"""Run JeL Q-Site QAOA circuits with Qiskit's local statevector simulator."""
import json
import time
import hashlib
from datetime import datetime, timezone
import qiskit
import numpy as np
from qiskit.quantum_info import Statevector
from qiskit.primitives import StatevectorSampler
from dispatch import ROOT, build_problem, solve_qaoa, qaoa_state, allocation, greedy_index
from ibm_hardware import circuit_for


def main():
    config = json.loads((ROOT/'scenarios.json').read_text())
    rows = []
    for scenario in config['scenarios']:
        started = time.perf_counter()
        p = build_problem(config,scenario['demand_kwh'])
        build_seconds = time.perf_counter()-started
        feasible = np.flatnonzero(p['feasible'])
        row = dict(scenario=scenario,backend='Qiskit StatevectorSampler (local)',team='JeL',
                   config=config, config_sha256=hashlib.sha256((ROOT/'scenarios.json').read_bytes()).hexdigest(),
                   generated_utc=datetime.now(timezone.utc).isoformat(),
                   qiskit_version=qiskit.__version__,seed=42)
        if not len(feasible):
            row['status'] = 'infeasible'
            rows.append(row)
            continue
        started = time.perf_counter()
        exact = int(min(feasible,key=lambda i:p['cost'][i]))
        exact_seconds = time.perf_counter()-started
        started = time.perf_counter()
        greedy = greedy_index(p,config)
        greedy_seconds = time.perf_counter()-started
        started = time.perf_counter()
        trained = solve_qaoa(p)
        qc = circuit_for(p,trained['parameters'])
        scale = float(np.max(np.abs(p['energies']))) or 1
        if not Statevector.from_instruction(qc).equiv(Statevector(qaoa_state(trained['parameters'],p['energies']/scale,p['n']))):
            raise AssertionError('Qiskit circuit verification failed')
        qc.measure_all()
        circuit_depth=qc.depth()
        circuit_operations=dict(qc.count_ops())
        counts = StatevectorSampler(seed=42).run([qc],shots=4096).result()[0].data.meas.get_counts()
        measured = [int(b,2) for b in counts if p['feasible'][int(b,2)]]
        best = min(measured,key=lambda i:p['cost'][i]) if measured else None
        quantum_seconds = time.perf_counter()-started
        row.update(status='solved' if best is not None else 'no_feasible_sample',
                   qubits=p['n'],shots=sum(counts.values()),counts=counts,
                   parameters=trained['parameters'],
                   circuit_depth=circuit_depth,circuit_operations=circuit_operations,
                   layers=3,starts=3,max_evaluations_per_start=180,
                   config=config, history=trained['history'],
                   optimizer_success=trained['optimizer_success'],
                   optimizer_message=trained['optimizer_message'],
                   build_seconds=build_seconds, exact_seconds=exact_seconds,
                   greedy_seconds=greedy_seconds, qaoa_seconds=quantum_seconds,
                   greedy=allocation(greedy,p,config),
                   training='Local NumPy statevector QAOA with COBYLA; verified equivalent Qiskit circuit',
                   best_feasible_sample=allocation(best,p,config),exact=allocation(exact,p,config),
                   modal_sample=allocation(int(max(counts,key=counts.get),2),p,config),
                   feasible_shots=sum(c for b,c in counts.items() if p['feasible'][int(b,2)]),
                   optimality_gap_inr=None if best is None else float(p['cost'][best]-p['cost'][exact]))
        print(scenario['name'],row['best_feasible_sample'])
        rows.append(row)
    output = ROOT/'results'/'qiskit_local.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(rows,indent=2))
    print('Saved',output)


if __name__ == '__main__':
    main()
