"""Evidence for the Phase 2 rubric, computed from actual inputs and counts."""
import hashlib
import io
import json
import unittest

import numpy as np
from rich import box
from rich.table import Table
from rich.rule import Rule
from dispatch import ROOT, build_problem, qaoa_state


def audit_counts(row, problem):
    counts=row['counts']
    if any(len(b)!=problem['n'] or set(b)-{'0','1'} or not isinstance(c,int) or c<=0 for b,c in counts.items()):
        raise ValueError('Malformed bitstring or count')
    if sum(counts.values())!=row['shots']:
        raise ValueError('Shot totals disagree')
    optimum=float(problem['cost'][problem['feasible']].min())
    feasible=optimal=0
    for bits,count in counts.items():
        i=int(bits,2)
        if problem['feasible'][i]:
            feasible+=count
            if np.isclose(problem['cost'][i],optimum):
                optimal+=count
    selected=row['best_feasible_sample']
    if selected:
        index=selected['state_index']
        if not problem['feasible'][index] or counts.get(format(index,f"0{problem['n']}b"),0)==0:
            raise ValueError('Selected solution is not a valid measured sample')
        if not np.isclose(selected['cost_inr'],problem['cost'][index]):
            raise ValueError('Selected cost does not match input model')
    return dict(feasible_shots=feasible,optimal_shots=optimal,shots=row['shots'])


def render_phase2(console, rows, cached=False):
    from qiskit.quantum_info import Statevector
    from ibm_hardware import circuit_for
    console.print(Rule('PHASE 2 / Prototype evidence',style='cyan'))
    console.print('[bold]This is an evidence checklist, not a predicted judging score.[/]')
    console.print('Mode: '+('Saved measurement replay; checks below run now.' if cached else 'Fresh simulation and live checks.'))
    console.print('Scope: working one-hour allocation. Reserve, outage and recovery features remain planned.\n')
    width=min(console.width,120)
    def facts(title, entries):
        console.print('\n[bold cyan]'+title+'[/]')
        t=Table(box=box.MINIMAL,show_edge=False,padding=(0,2),width=width)
        narrow=width<105
        columns=[('Evidence',20),('Result and explanation',max(20,width-30))] if narrow else [('Evidence',24),('Result',width-66),('Meaning',28)]
        for heading,w in columns:
            t.add_column(heading,width=w,min_width=w,max_width=w)
        t.add_row(*(['']*len(columns)))
        for label,result,meaning in entries:
            t.add_row(label,f'{result}\n[dim]{meaning}[/]' if narrow else str(result),*([] if narrow else [str(meaning)]))
        t.add_row(*(['']*len(columns)));console.print(t)
    facts('1. MVP functionality and completion / 25%',[
        ('Inputs','Five sources; costs and demand in scenarios.json','Synthetic one-hour examples'),
        ('End-to-end path','Read inputs, solve, validate, display and save','Working allocation pipeline'),
        ('Capacity handling','Source output cannot exceed its encoded limit','Checked against input model'),
        ('Shortage case','160 kWh required; 150 kWh available','Rejects an impossible request'),
        ('Not delivered yet','Interactive inputs; reserve/outage/recovery','Do not present as complete')])
    evidence=[]
    hash_now=hashlib.sha256((ROOT/'scenarios.json').read_bytes()).hexdigest()
    for row in rows:
        if row['status']=='infeasible':continue
        cfg=row.get('config')
        if not cfg:raise ValueError('Results lack input evidence. Run python dashboard.py --phase2 without --cached.')
        p=build_problem(cfg,row['scenario']['demand_kwh'])
        audit=audit_counts(row,p)
        scale=float(np.max(np.abs(p['energies']))) or 1
        qc=circuit_for(p,row['parameters'])
        equivalent=Statevector.from_instruction(qc).equiv(Statevector(qaoa_state(row['parameters'],p['energies']/scale,p['n'])))
        if not equivalent:raise AssertionError('Qiskit verification failed')
        name=row['scenario']['name']
        facts('2. Quantum component / 25% / '+name,[
            ('Actual quantum role',f"{p['n']} simulated qubits; Qiskit circuit sampling",'Runs locally, no QPU'),
            ('Model','QUBO = cost + P (supply - demand)^2','Binary choices with penalties'),
            ('Circuit verification','PASS: equivalent independent statevectors','Live check, even in replay'),
            ('Training',f"3 QAOA layers; {len(row['parameters'])} angles; 3 starts",'NumPy simulation + COBYLA'),
            ('Measured valid shots',f"{audit['feasible_shots']} / {audit['shots']} ({audit['feasible_shots']/audit['shots']:.1%})",'Demand exactly met'),
            ('Measured optimal shots',f"{audit['optimal_shots']} / {audit['shots']} ({audit['optimal_shots']/audit['shots']:.2%})",'Exact minimum cost measured'),
            ('Most frequent sample',f"{row['modal_sample']['supply_kwh']:.0f} kWh; valid = {row['modal_sample']['feasible']}",'Separate from best sample'),
            ('Optimizer converged',row['optimizer_success'],'Budget exhaustion is visible')])
        facts('Classical comparison / '+name,[
            ('Exact cost',f"INR {row['exact']['cost_inr']:.0f}",'Exhaustive encoded search'),
            ('Classical merit order',f"INR {row['greedy']['cost_inr']:.0f}",'Cheapest sources first'),
            ('Best quantum sample',f"INR {row['best_feasible_sample']['cost_inr']:.0f}" if row['best_feasible_sample'] else 'None','Only measured valid samples'),
            ('Cost gap',str(row['optimality_gap_inr'])+' INR','Zero means matching cost'),
            ('Exact / greedy time',f"{row['exact_seconds']*1000:.3f} / {row['greedy_seconds']*1000:.3f} ms",'Shared construction excluded'),
            ('Quantum workflow time',f"{row['qaoa_seconds']*1000:.3f} ms",'Training + check + sampling')])
        console.print('[dim]Single-run timings on this machine. Quantum speedup is not established; merit order already solves this linear model.[/]')
        evidence.append(dict(scenario=name,counts_audit=audit,circuit_equivalent=equivalent,
                             inputs_match_current_file=row.get('config_sha256')==hash_now,
                             measurement_generated_utc=row.get('generated_utc','Not recorded in older results')))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_dispatch')
    test_result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    facts('3. Technical implementation / 20%',[
        ('Core tests run now',f"{test_result.testsRun} run; {len(test_result.failures)} failures; {len(test_result.errors)} errors",'Actual execution, not a label'),
        ('Measurement audit','PASS for displayed feasible scenarios','Bitstrings, totals, selected cost'),
        ('Input fingerprint','MATCH' if all(e['inputs_match_current_file'] for e in evidence) else 'STALE OR NOT RECORDED','Fresh run recommended if stale'),
        ('Evidence saved','results/phase2_evidence.json','Checks and timing provenance'),
        ('Reproducibility','Seed 42; settings and counts in JSON','One seed, not repeated trials')])
    facts('4. Innovation and real-world impact / 15%',[
        ('Current contribution','Explained allocation + quantum validation','An educational prototype'),
        ('Proposed distinction','Price of reserve + verified recovery options','Requires implementation'),
        ('Intended users','Community facilities; campus energy teams','No live site validation yet'),
        ('Society / SDGs','Affordable energy (7); resilient infrastructure (9)','Relevance, not measured impact'),
        ('Existing tools','REopt already supports energy/resilience planning','No superiority claim')])
    facts('5. Demo and presentation / 15%',[
        ('Demonstrate','80 kWh normal; 120 kWh surge; 160 kWh shortage','Explain sources, cost, balance'),
        ('Explain quantum','Train angles; simulate circuit; check samples','Never claim all samples optimal'),
        ('Compare honestly','Cost gap, valid-shot rate and measured times','Matching cost is not speedup'),
        ('Next completion gate','Implement reserve/outage/recovery tests','Needed to fulfill the new idea')])
    (ROOT/'results'/'phase2_evidence.json').write_text(json.dumps(dict(
        scope='One-hour allocation; extended resilience features planned',cached_measurements=cached,
        scenarios=evidence,tests_run=test_result.testsRun,tests_passed=test_result.wasSuccessful()),indent=2))
    if not test_result.wasSuccessful():raise AssertionError('Core tests failed; inspect before demo')
