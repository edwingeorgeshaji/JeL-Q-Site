"""JeL: validate QAOA locally, optionally submit one IBM hardware job."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from dispatch import ROOT, build_problem, solve_qaoa, qaoa_state, allocation


def circuit_for(p, params):
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(p['n'])
    qc.h(range(p['n']))
    scale = float(np.max(np.abs(p['energies']))) or 1
    q = p['q']/scale
    # x=(1-Z)/2: linear Z and pairwise ZZ coefficients.
    h = -np.diag(q)/2
    for i in range(p['n']):
        for j in range(i+1, p['n']):
            h[i] -= q[i,j]/4
            h[j] -= q[i,j]/4
    for gamma,beta in np.array(params).reshape(-1,2):
        for i in range(p['n']):
            qc.rz(2*gamma*h[i], i)
        for i in range(p['n']):
            for j in range(i+1,p['n']):
                if q[i,j]:
                    qc.rzz(gamma*q[i,j]/2, i,j)
        qc.rx(2*beta, range(p['n']))
    return qc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--submit', action='store_true')
    parser.add_argument('--job-id', help='Retrieve an existing job without resubmission')
    parser.add_argument('--backend')
    parser.add_argument('--scenario', type=int, default=0)
    args = parser.parse_args()
    from qiskit.quantum_info import Statevector
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    config = json.loads((ROOT/'scenarios.json').read_text())
    scenario = config['scenarios'][args.scenario]
    p = build_problem(config, scenario['demand_kwh'])
    if not p['feasible'].any():
        raise ValueError('Scenario has no feasible allocation')
    q = solve_qaoa(p)
    qc = circuit_for(p,q['parameters'])
    actual = Statevector.from_instruction(qc)
    scale = float(np.max(np.abs(p['energies']))) or 1
    expected = Statevector(qaoa_state(q['parameters'],p['energies']/scale,p['n']))
    if not actual.equiv(expected):
        raise AssertionError('Qiskit circuit differs from independently simulated QAOA')
    print('PASS: Qiskit circuit equals NumPy statevector up to global phase')
    if not (args.submit or args.job_id):
        print('Validation only; no IBM quota used. Add --submit for hardware.')
        return
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    service = QiskitRuntimeService()  # Credentials saved privately in this environment.
    output = ROOT/'results'/'ibm'
    output.mkdir(parents=True,exist_ok=True)
    if args.job_id:
        job = service.job(args.job_id)
        manifest = json.loads((output/f'{args.job_id}_manifest.json').read_text())
        config = manifest['config']
        p = build_problem(config,manifest['scenario']['demand_kwh'])
    else:
        backend = service.backend(args.backend) if args.backend else service.least_busy(operational=True,simulator=False,min_num_qubits=p['n'])
        if backend.configuration().simulator:
            raise ValueError('Real processor required')
        qc.measure_all()
        isa = generate_preset_pass_manager(backend=backend,optimization_level=3,seed_transpiler=42).run(qc)
        manifest = dict(team='JeL',project='Q-Site Energy Dispatch',config=config,
                        scenario=scenario,parameters=q['parameters'],backend=backend.name,
                        isa_depth=isa.depth(),operations=dict(isa.count_ops()),shots=4096,
                        method='Locally optimized QAOA; final circuit measured on IBM hardware',
                        submitted_utc=datetime.now(timezone.utc).isoformat())
        from qiskit import qpy
        with (output/'prepared_circuit.qpy').open('wb') as f:
            qpy.dump(isa,f)
        job = SamplerV2(mode=backend,options={'max_execution_time':60}).run([isa],shots=4096)
        manifest['job_id'] = job.job_id()
        (output/f'{job.job_id()}_manifest.json').write_text(json.dumps(manifest,indent=2))
        print('Submitted',job.job_id(),'on',backend.name,flush=True)
    result = job.result()
    counts = result[0].data.meas.get_counts()
    feasible = [int(b,2) for b in counts if p['feasible'][int(b,2)]]
    best = min(feasible,key=lambda i:p['cost'][i]) if feasible else None
    exact = int(min(np.flatnonzero(p['feasible']),key=lambda i:p['cost'][i]))
    report = dict(manifest=manifest,status=str(job.status()),counts=counts,
                  best_feasible_sample=allocation(best,p,config),exact=allocation(exact,p,config),
                  feasible_shots=sum(c for b,c in counts.items() if p['feasible'][int(b,2)]),
                  optimal_shots=sum(c for b,c in counts.items() if p['feasible'][int(b,2)] and np.isclose(p['cost'][int(b,2)],p['cost'][exact])),
                  modal_sample=allocation(int(max(counts,key=counts.get),2),p,config))
    path = output/f'{job.job_id()}_result.json'
    path.write_text(json.dumps(report,indent=2))
    print('Hardware evidence saved:',path)


if __name__ == '__main__':
    main()
