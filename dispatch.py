"""JeL Q-Site: explicit QUBO and NumPy QAOA statevector simulator."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parent


def build_problem(config, demand_kwh):
    block = config['block_kwh']
    if not isinstance(block, (int, float)) or block <= 0:
        raise ValueError('block_kwh must be positive')
    if demand_kwh < 0 or not np.isclose(demand_kwh / block, round(demand_kwh / block)):
        raise ValueError('Demand must be a nonnegative integer number of energy blocks')
    weights, costs, owners = [], [], []
    for i, source in enumerate(config['sources']):
        if source['cost_per_block_inr'] < 0 or not source['weights']:
            raise ValueError('Nonnegative costs and nonempty encodings required')
        for w in source['weights']:
            if not isinstance(w, int) or w <= 0:
                raise ValueError('Encoding weights must be positive integers')
            weights.append(w)
            costs.append(w * source['cost_per_block_inr'])
            owners.append(i)
    n = len(weights)
    if not 1 <= n <= 16:
        raise ValueError('Local simulator supports 1 to 16 qubits')
    w, c = np.array(weights), np.array(costs, dtype=float)
    demand = round(demand_kwh / block)
    # All costs are nonnegative. Any feasible cost <= sum(c); any
    # infeasible allocation has integer mismatch >= 1. Hence this penalty
    # makes every feasible optimum better than every infeasible state.
    penalty = float(c.sum() + 1)
    q = np.diag(c + penalty * (w*w - 2*demand*w))
    for i in range(n):
        for j in range(i+1, n):
            q[i, j] = 2 * penalty * w[i] * w[j]
    bits = ((np.arange(2**n)[:, None] >> np.arange(n)) & 1)
    supply = bits @ w
    cost = bits @ c
    energies = np.einsum('bi,ij,bj->b', bits, q, bits) + penalty*demand*demand
    return dict(n=n, w=w, c=c, owners=owners, bits=bits, supply=supply,
                cost=cost, demand=demand, feasible=supply == demand,
                q=q, constant=penalty*demand*demand, penalty=penalty,
                energies=energies)


def qaoa_state(params, energies, n):
    """|+> initial state; exp(-i gamma C), then exp(-i beta sum X).

    Index bit i corresponds to decision variable i (little endian).
    Diagonal C is the exact QUBO including its constant; global phase is harmless.
    """
    state = np.full(2**n, 1 / np.sqrt(2**n), dtype=complex)
    for gamma, beta in np.asarray(params).reshape(-1, 2):
        state *= np.exp(-1j * gamma * energies)
        for qubit in range(n):
            view = state.reshape(-1, 2, 2**qubit)
            a, b = view[:, 0, :].copy(), view[:, 1, :].copy()
            view[:, 0, :] = np.cos(beta)*a - 1j*np.sin(beta)*b
            view[:, 1, :] = np.cos(beta)*b - 1j*np.sin(beta)*a
    return state


def solve_qaoa(problem, seed=42, depth=3, starts=3, maxiter=180, shots=4096):
    if min(depth, starts, maxiter, shots) < 1:
        raise ValueError('depth, starts, maxiter and shots must be positive')
    rng = np.random.default_rng(seed)
    # Scale by a single positive constant; retain the original argmin.
    scale = float(np.max(np.abs(problem['energies']))) or 1.0
    energies = problem['energies'] / scale
    history, runs = [], []
    def objective(params):
        probs = np.abs(qaoa_state(params, energies, problem['n']))**2
        value = float(probs @ energies)
        history.append(value * scale)
        return value
    start = time.perf_counter()
    for _ in range(starts):
        fit = minimize(objective, rng.uniform(0, 2*np.pi, 2*depth),
                       method='COBYLA', options={'maxiter': maxiter, 'rhobeg': 1.0})
        runs.append(fit)
    best = min(runs, key=lambda fit: fit.fun)
    probs = np.abs(qaoa_state(best.x, energies, problem['n']))**2
    probs /= probs.sum()
    counts = rng.multinomial(shots, probs)
    observed = np.flatnonzero(counts)
    feasible_observed = observed[problem['feasible'][observed]]
    # No exact solution is injected into the quantum result.
    selected = (int(min(feasible_observed, key=lambda i: problem['cost'][i]))
                if len(feasible_observed) else None)
    return dict(selected=selected, mode=int(np.argmax(counts)), counts=counts,
                probabilities=probs, history=history, parameters=best.x.tolist(),
                evaluations=len(history), runtime_seconds=time.perf_counter()-start,
                optimizer_success=bool(best.success), optimizer_message=str(best.message),
                feasible_probability=float(probs[problem['feasible']].sum()))


def allocation(index, problem, config):
    if index is None:
        return None
    bits = problem['bits'][index]
    return dict(state_index=int(index), bitstring=format(index, f"0{problem['n']}b"),
                cost_inr=float(problem['cost'][index]),
                supply_kwh=float(problem['supply'][index]*config['block_kwh']),
                feasible=bool(problem['feasible'][index]),
                sources_kwh={s['name']: int(sum(bits[j]*problem['w'][j]
                    for j, owner in enumerate(problem['owners']) if owner == i)*config['block_kwh'])
                    for i, s in enumerate(config['sources'])})


def greedy_index(problem, config):
    # Economic merit order, valid for the default contiguous block encodings.
    remaining = problem['demand']
    chosen = np.zeros(problem['n'], dtype=int)
    for owner in sorted(range(len(config['sources'])),
                        key=lambda i: config['sources'][i]['cost_per_block_inr']):
        indices = [j for j, o in enumerate(problem['owners']) if o == owner]
        options = []
        for mask in range(2**len(indices)):
            value = sum(problem['w'][j] for k, j in enumerate(indices) if mask >> k & 1)
            if value <= remaining:
                options.append((value, mask))
        value, mask = max(options)
        remaining -= value
        for k, j in enumerate(indices):
            chosen[j] = mask >> k & 1
    return int(sum(int(b) << j for j, b in enumerate(chosen)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'scenarios.json')
    parser.add_argument('--output', type=Path, default=ROOT/'results')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--depth', type=int, default=3)
    parser.add_argument('--starts', type=int, default=3)
    parser.add_argument('--maxiter', type=int, default=180)
    parser.add_argument('--shots', type=int, default=4096)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for scenario in config['scenarios']:
        p = build_problem(config, scenario['demand_kwh'])
        feasible = np.flatnonzero(p['feasible'])
        t = time.perf_counter()
        exact = int(min(feasible, key=lambda i: p['cost'][i])) if len(feasible) else None
        classical_seconds = time.perf_counter()-t
        row = dict(name=scenario['name'], demand_kwh=scenario['demand_kwh'],
                   qubits=p['n'], capacity_kwh=int(p['w'].sum()*config['block_kwh']),
                   exact=allocation(exact, p, config),
                   greedy=allocation(greedy_index(p, config), p, config),
                   exact_runtime_seconds=classical_seconds)
        if exact is None:
            row.update(status='infeasible', reason='No encoded allocation meets demand; QAOA skipped',
                       shortfall_kwh=max(0, scenario['demand_kwh']-row['capacity_kwh']))
        else:
            q = solve_qaoa(p, args.seed, args.depth, args.starts, args.maxiter, args.shots)
            optima = p['feasible'] & np.isclose(p['cost'], p['cost'][exact])
            row.update(status='solved' if q['selected'] is not None else 'no_feasible_sample',
                       qaoa=allocation(q['selected'], p, config),
                       modal_sample=allocation(q['mode'], p, config),
                       optimality_gap_inr=None if q['selected'] is None else float(p['cost'][q['selected']]-p['cost'][exact]),
                       optimal_probability=float(q['probabilities'][optima].sum()),
                       uniform_optimal_probability=float(optima.mean()),
                       feasible_probability=q['feasible_probability'],
                       feasible_shots=int(q['counts'][p['feasible']].sum()),
                       counts={format(i, f"0{p['n']}b"): int(c) for i,c in enumerate(q['counts']) if c},
                       history=q['history'], parameters=q['parameters'],
                       qaoa_runtime_seconds=q['runtime_seconds'], evaluations=q['evaluations'],
                       optimizer_success=q['optimizer_success'], optimizer_message=q['optimizer_message'])
        (args.output/f"qubo_{len(results)+1}.json").write_text(json.dumps(dict(
            matrix=p['q'].tolist(), constant=p['constant'], penalty=p['penalty'],
            weights=p['w'].tolist(), costs=p['c'].tolist(), owners=p['owners']), indent=2))
        results.append(row)
        print(f"{row['name']}: {row['status']}; exact={row['exact']}; QAOA={row.get('qaoa')}")
    report = dict(team='JeL', project='Q-Site Energy Dispatch', backend='NumPy exact statevector QAOA simulation; no hardware',
                  config=config, settings=vars(args) | {'config':str(args.config), 'output':str(args.output)},
                  versions=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
                  config_sha256=hashlib.sha256(args.config.read_bytes()).hexdigest(), scenarios=results)
    (args.output/'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    with (args.output/'summary.csv').open('w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['scenario','demand_kwh','status','exact_cost_inr','qaoa_cost_inr','gap_inr','optimal_probability','uniform_optimal_probability'])
        for r in results:
            writer.writerow([r['name'],r['demand_kwh'],r['status'],(r['exact'] or {}).get('cost_inr'),
                             (r.get('qaoa') or {}).get('cost_inr'),r.get('optimality_gap_inr'),
                             r.get('optimal_probability'),r.get('uniform_optimal_probability')])
    from visuals import render
    render(report, args.output)


if __name__ == '__main__':
    main()
