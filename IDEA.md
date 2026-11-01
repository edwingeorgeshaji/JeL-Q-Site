# Q-Site: energy reserve and recovery planner

Q-Site helps a community facility manager compare the lowest current-hour electricity cost with an emergency-ready plan, test a specified grid outage, and understand the smallest tested extra-energy intervention that restores essential service.

## Phase 1 scope

The bounded hackathon proposal covers five sources, one normal hour followed by one outage hour, battery energy carry-over without charging, a user-selected reserve, essential demand and recovery search in 10 kWh increments. Flexible task scheduling and multi-day forecasting are stretch goals.

Phase 2 implementation now includes interactive preset/custom inputs, fixed-reserve normal dispatch, outage evaluation with battery carry-over and power limits, and verified recovery search. Qiskit evaluates every training circuit; three-seed trials compare measured results with exact classical plans. Run `python dashboard.py` or `python dashboard.py --demo`. Earlier PDF/slides record the proposal state; see README for the current implementation and model boundaries.

## Rubric coverage

| Criterion | Weight | Concrete evidence planned |
|---|---:|---|
| Problem and SDG relevance | 20% | Shelter manager's cost/reserve decision; SDG 7.1 affordability/reliability, 7.2 renewable allocation, 9.1 resilient infrastructure; cost, essential kWh served and shortfall. |
| Innovation | 25% | Compare two plans, trigger the same outage, verify the smallest successful recovery increment among tested options. No first-ever claim. |
| Feasibility | 20% | Offline simulation, at most 10 qubits; proposed 24-hour build schedule and fallback in PDF pages 17-18. Actual remaining time needs confirmation. |
| Quantum planning | 25% | Fixed-reserve dispatch QUBO; bounded encoding; local angle training and verified Qiskit sampling; exact and merit-order comparisons; five declared seeds. |
| Presentation clarity | Unspecified | Plain labels, aligned charts and 90-second user journey. Remaining 10% inferred, not confirmed. |

Quantum scope: QAOA solves a fixed-reserve dispatch subproblem. Classical code handles reserve choices, outage evaluation and recovery search. Identical constraints and inputs apply to classical baselines. No speedup is claimed; unsuccessful or infeasible samples remain visible.

Project metrics are experimental measures, not official SDG indicators or proof of social impact. REopt already addresses energy planning and resilience; Q-Site's proposed distinction is a focused, explainable interaction and a transparent quantum experiment.

Official SDG references: https://www.un.org/sustainabledevelopment/energy/ and https://sdgs.un.org/goals/goal9.
