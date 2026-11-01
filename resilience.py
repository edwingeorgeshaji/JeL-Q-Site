"""Two-hour reserve/outage experiment with Qiskit QAOA and exact baselines."""
import copy
import json
import time
from datetime import datetime, timezone

import numpy as np
from scipy.optimize import minimize
from qiskit.quantum_info import Statevector
from qiskit.primitives import StatevectorSampler
from dispatch import ROOT, build_problem, allocation, qaoa_state
from ibm_hardware import circuit_for

DEFAULT=dict(demand=80, critical=30, battery=30, power=30, reserve=30,
             outage_solar=0,outage_wind=0,outage_diesel=0)


def validate(inputs):
    if set(inputs)!=set(DEFAULT):
        raise ValueError('Input fields do not match the model')
    for key,value in inputs.items():
        if type(value) is not int or value<0 or value%10:
            raise ValueError(f'{key}: use nonnegative multiples of 10 kWh')
    if inputs['reserve']>inputs['battery']:
        raise ValueError('Reserve cannot exceed starting battery energy')
    if inputs['power']>30 or any(inputs[k]>30 for k in ['outage_solar','outage_wind','outage_diesel']):
        raise ValueError('Source power/availability cannot exceed 30 kWh per hour')
    if inputs['battery']>300 or inputs['demand']>200 or inputs['critical']>200:
        raise ValueError('Demo bounds: battery <=300, demands <=200 kWh')


def encoding(blocks):
    return {0:[],1:[1],2:[1,1],3:[1,2]}[blocks]


def problem(inputs, reserve):
    cfg=json.loads((ROOT/'scenarios.json').read_text())
    capacity=min(inputs['power'],inputs['battery']-reserve)
    # No variable for an unavailable battery, preserving the source name in outputs.
    cfg['sources'][2]['weights']=encoding(capacity//10) or [1]
    if capacity==0:
        cfg['sources'].pop(2)
    return cfg,build_problem(cfg,inputs['demand'])


def exact_plan(inputs,reserve):
    cfg,p=problem(inputs,reserve)
    started=time.perf_counter()
    feasible=np.flatnonzero(p['feasible'])
    best=int(min(feasible,key=lambda i:p['cost'][i])) if len(feasible) else None
    return cfg,p,allocation(best,p,cfg),time.perf_counter()-started


def outage(inputs,plan):
    if plan is None:
        return None
    used=plan['sources_kwh'].get('Battery',0)
    remaining=inputs['battery']-used
    battery_available=min(remaining,inputs['power'])
    available=inputs['outage_solar']+inputs['outage_wind']+inputs['outage_diesel']+battery_available
    # Essential demand prioritized; oversupply curtailed; dispatch by cost.
    need=inputs['critical']; supplied={}
    for name,cap in [('Solar',inputs['outage_solar']),('Wind',inputs['outage_wind']),('Battery',battery_available),('Diesel',inputs['outage_diesel'])]:
        take=min(need,cap); supplied[name]=take; need-=take
    costs={'Solar':8,'Wind':12,'Battery':25,'Diesel':75}
    return dict(remaining_before=remaining,remaining_after=remaining-supplied['Battery'],
                sources_kwh=supplied,served=inputs['critical']-need,shortfall=need,
                available=available,cost_inr=sum(v/10*costs[k] for k,v in supplied.items()))


def recovery(inputs,reserve,limit=100):
    attempts=[]
    for added in range(0,limit+1,10):
        changed=copy.deepcopy(inputs);changed['battery']+=added
        _,_,plan,_=exact_plan(changed,reserve)
        result=outage(changed,plan)
        ok=bool(result is not None and result['shortfall']==0)
        attempts.append(dict(added_kwh=added,success=ok))
        if ok:
            return dict(added_kwh=added,attempts=attempts,plan=plan,outage=result)
    return dict(added_kwh=None,attempts=attempts,reason='No tested extra-energy increment fixes the shortage; power/availability limits may bind.')


def quantum(cfg,p,seed=42,iterations=80):
    start=time.perf_counter();rng=np.random.default_rng(seed)
    scale=float(np.max(np.abs(p['energies']))) or 1
    history=[]
    def objective(params):
        state=Statevector.from_instruction(circuit_for(p,params))
        score=float(state.probabilities()@p['energies'])/scale
        history.append(score*scale);return score
    fits=[minimize(objective,rng.uniform(0,2*np.pi,4),method='COBYLA',options={'maxiter':iterations}) for _ in range(2)]
    fit=min(fits,key=lambda f:f.fun)
    qc=circuit_for(p,fit.x)
    if not Statevector.from_instruction(qc).equiv(Statevector(qaoa_state(fit.x,p['energies']/scale,p['n']))):
        raise AssertionError('Independent circuit verification failed')
    qc.measure_all()
    counts=StatevectorSampler(seed=seed).run([qc],shots=2048).result()[0].data.meas.get_counts()
    observed=[int(b,2) for b in counts if p['feasible'][int(b,2)]]
    best=min(observed,key=lambda i:p['cost'][i]) if observed else None
    optimum=float(p['cost'][p['feasible']].min())
    good=sum(c for b,c in counts.items() if p['feasible'][int(b,2)])
    optimal=sum(c for b,c in counts.items() if p['feasible'][int(b,2)] and np.isclose(p['cost'][int(b,2)],optimum))
    return dict(seed=seed,counts=counts,shots=2048,feasible_shots=good,optimal_shots=optimal,
                plan=allocation(best,p,cfg),gap=None if best is None else float(p['cost'][best]-optimum),
                seconds=time.perf_counter()-start,qubits=p['n'],layers=2,starts=2,
                evaluations=len(history),history=history,parameters=fit.x.tolist(),
                optimizer_success=bool(fit.success),optimizer_message=str(fit.message),
                verified=True,depth=qc.depth(),backend='Qiskit Statevector, local',
                training='Every objective evaluation uses a Qiskit circuit statevector')


def run(inputs=None,seeds=(42,43,44)):
    inputs=copy.deepcopy(DEFAULT if inputs is None else inputs);validate(inputs)
    results=[]
    for name,reserve in [('Lowest Cost',0),('Emergency Ready',inputs['reserve'])]:
        cfg,p,plan,seconds=exact_plan(inputs,reserve)
        row=dict(name=name,reserve=reserve,config=cfg,exact=plan,exact_seconds=seconds,
                 outage=outage(inputs,plan),recovery=recovery(inputs,reserve))
        row['trials']=[quantum(cfg,p,seed) for seed in seeds] if plan else []
        for trial in row['trials']:
            trial['outage']=outage(inputs,trial['plan'])
        results.append(row)
    report=dict(schema=1,generated_utc=datetime.now(timezone.utc).isoformat(),inputs=inputs,
                seeds=list(seeds),plans=results,assumptions='Two independent one-hour supply intervals except battery carry-over. No charging, network physics or forecasts. Synthetic INR costs. Recovery changes starting usable battery energy only, up to +100 kWh; power fixed.')
    path=ROOT/'results'/'resilience.json';path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report,indent=2));return report
