# JeL — Q-Site Energy Dispatch

Quantum Hack Day – Kochi · QuantumX and TinkerHub Foundation

**Selected track: Challenge 03, Quantum Simulation for Energy Systems.**

Q-Site answers a practical dispatch question: how should a small microgrid allocate solar, wind, stored energy, grid imports, and diesel to meet an AI-driven electricity load at minimum operating cost?

The project now implements the **Phase 2 energy reserve and recovery prototype** for community facilities. It compares lowest-cost and emergency-ready plans, tests a specified outage, and searches verified recovery options. The earlier PDF and slides describe the prior proposal state; use the implementation instructions below for the current software.

## Phase 2: run the full prototype

```powershell
python dashboard.py
```

Choose the shelter preset or custom inputs, then an outage preset. Custom entries cover normal demand, essential outage demand, starting battery energy, output power, reserve and outage availability. Enter nonnegative multiples of 10, within the displayed bounds. Prices and normal-hour nonbattery capacities remain the synthetic values in `scenarios.json`.

For a fresh automatic demonstration: `python dashboard.py --demo`. For a saved replay: `python dashboard.py --cached`. For a faster single-seed run: `python dashboard.py --demo --trials 1`. Default trials use seeds 42, 43 and 44. `python dashboard.py --legacy` retains the original one-hour UI. The existing `--details` and `--scale` views continue to display the legacy experiment.

The default battery-only outage preset compares INR 110 versus INR 170 normal-hour dispatch. Exact plans serve 10/30 versus 30/30 kWh of essential outage energy. The additional INR 60 is the normal-hour price of the chosen reserve, not a total-life cost or hardware purchase. Recovery searches +0 to +100 kWh of starting usable battery energy in 10 kWh steps, keeping power fixed: the cheapest plan needs +20 kWh in the default example. Smaller tested increments fail. It does not compare all possible infrastructure interventions.

Each quantum trial trains two-layer QAOA through Qiskit Statevector at every objective evaluation, using classical COBYLA, two starts and 80 evaluations per start, then takes 2,048 Qiskit measurements. It independently verifies the circuit against the NumPy implementation. Best measured feasible cost, feasibility rate, optimal-shot rate, runtime and convergence status are preserved; an exact answer is never injected into samples. Optimizers may exhaust their budget. The classical exact plans and seed-42 measured plans have separately labeled outage coverage. No quantum speedup is established.

`results/resilience.json` contains complete inputs, per-seed counts and parameters, optimizer evidence, actual measured plans and verified recovery attempts. `results/phase2_dashboard.txt` stores terminal output. Tests: `python -m unittest -v` (12 tests in the current project).

Model boundary: two one-hour intervals, continuous essential load within the outage hour, no charging, battery carry-over and per-hour power limits, grid unavailable throughout the outage. Renewable and generator availability are user inputs, not forecasts. No grid physics, automatic equipment control or physical-site validation. Recovery and outage evaluation are classical; QAOA solves each fixed-reserve normal-hour dispatch subproblem. See `resilience.py` and `resilience_ui.py`.

## Run

### Terminal dashboard (recommended)

For Phase 2 judging evidence, run `python dashboard.py --phase2`. This keeps the simple graphs and adds sections for the five rubric categories (25%, 25%, 20%, 15%, 15%). It computes measurement quality from raw counts, verifies the Qiskit circuit, executes the four core tests, checks whether saved inputs match the current configuration, and shows classical/quantum costs and timings. `python dashboard.py --cached --phase2` replays saved measurements but runs the checks again. Evidence is saved to `results/phase2_evidence.json`; it is not a predicted judging score. Reserve/outage/recovery remain explicitly planned.

```powershell
python -m pip install -r requirements-qiskit.txt
python dashboard.py
```

Maximize the terminal for wider tables. Windows Terminal supports the colored charts and Unicode graph characters. The dashboard reruns QAOA and Qiskit sampling, then displays resource bars, exact and merit-order classical comparisons, measured feasibility, top bitstrings and the optimizer energy trace. It records a text copy in `results/dashboard.txt`.

Use `python dashboard.py --cached` to display saved results quickly, or `python dashboard.py --scenario 1` to focus on the surge. The scale laboratory measures classical merit-order dispatch for 5, 50, 500 and 5,000 synthetic sources, using seven repeats. `results/scaling.json` stores the timings and machine description. Quantum simulation is measured only at five sources; larger statevector memory figures are explicitly theoretical estimates. For this independent linear-cost model, classical merit order is already exact. No large-scale quantum speedup is claimed.

The primary demonstration now runs locally using Qiskit. IBM hardware is optional and no credentials are needed:

```powershell
python -m pip install -r requirements-qiskit.txt
python qiskit_local.py
```

Read `results/qiskit_local.json` for actual Qiskit measurement counts and the exact comparison. Angles are trained with the local NumPy statevector implementation; the equivalent Qiskit circuit is independently verified and then sampled using Qiskit StatevectorSampler. This is a local quantum simulation. Existing IBM jobs can be cancelled in the IBM dashboard if they are no longer needed.

Python 3.11+ recommended. From this directory:

```powershell
python -m pip install -r requirements.txt
python -m unittest -v
python dispatch.py
Invoke-Item results/dispatch.svg
```

No cloud accounts, credentials, paid services, or quantum hardware required. Dependencies were already installed for the recorded run. NumPy implements the quantum statevector directly; this version does not require Qiskit. This is quantum circuit simulation on a classical computer.

## Running in qBraid

For the current project, open qBraid Lab, create a Python notebook or terminal, upload this folder, and run the same commands above. A qBraid account may be needed to access Lab, but **no IBM Quantum API key is needed**: this code runs its statevector simulation locally inside the Python environment.

There are three different cases:

1. **Local or qBraid Lab simulation:** no IBM key. Run `python dispatch.py`; this is the recommended demo path.
2. **A qBraid-hosted simulator job submitted through qBraid Runtime:** use a qBraid API key if the selected qBraid service asks for one. This is a qBraid credential, not an IBM credential; simulator access and credits depend on the qBraid workspace.
3. **A real IBM Quantum processor:** requires IBM credentials (IBM API token, and for IBM Cloud the matching CRN/instance). The current `dispatch.py` does not submit to IBM hardware; it is intentionally self-contained and hardware-independent. An IBM backend adapter would need to be added for a hardware run.

Do not paste IBM or qBraid secrets into `scenarios.json`, notebooks, screenshots, Git, or the project files. qBraid's current documentation describes qBraid API keys for qBraid Runtime and separate IBM credentials for IBM backends: https://docs.qbraid.com/v2/sdk/user-guide/providers/getting-started and https://docs.qbraid.com/v2/sdk/user-guide/providers/ibm.

To rerun with another initialization:

```powershell
python dispatch.py --seed 7 --output results/seed7
```

Edit `scenarios.json` to change demand, energy prices or source encodings. Each source's weights specify the energy blocks represented by its bits; `[1, 2]` encodes 0–3 blocks. The default five sources use ten qubits. Demand must be an integer number of blocks. Keep total qubits at 16 or below for this local simulator.

## Fresh results

Default configuration: synthetic one-hour dispatch, 10 kWh blocks, 30 kWh available from each resource. Costs are illustrative INR per block, not observed tariffs.

| Scenario | Demand | Exact cost | QAOA best feasible measured cost | Status |
|---|---:|---:|---:|---|
| Daytime | 80 kWh | INR 110 | INR 110 | Feasible |
| AI load surge | 120 kWh | INR 300 | INR 300 | Feasible |
| Capacity shortfall | 160 kWh | — | — | Infeasible: 150 kWh available |

Daytime uses solar 30, wind 30, battery 20 kWh. The AI surge uses solar 30, wind 30, battery 30, grid imports 30 kWh. See `results/results.json` for optimizer diagnostics, most frequent sampled allocations, complete measurement counts, runtimes, exact optimal-state probabilities and uniform-sampling probabilities. `results/summary.csv` supports quick comparison.

In this run, optimal-state probability was 0.252% for Daytime and 0.835% for AI load surge, compared with 0.098% under uniform sampling. Both optimizers reached their evaluation limit without reporting convergence. The most frequent sampled states violated demand in both scenarios. The feasible results above therefore depend on explicitly documented classical filtering and rescoring of the measured samples; they do not demonstrate reliable direct quantum dispatch.

## Mathematical formulation

For bit j, let w_j be its energy in blocks and c_j its operating cost. Let d be demand in blocks. Minimize

```text
E(x) = sum_j c_j x_j + P (sum_j w_j x_j - d)^2
x_j in {0,1}
P = sum_j c_j + 1
```

Every source capacity is enforced by its finite encoding. Demand is an exact equality: oversupply receives the same mismatch penalty as shortage. Since costs are nonnegative and mismatch is an integer, P exceeds every possible dispatch cost. Whenever a feasible encoded state exists, the global penalized optimum is feasible.

The exported upper triangular QUBO has Q_jj = c_j + P(w_j² - 2dw_j), Q_ij = 2Pw_iw_j for i<j, and constant Pd². Each `results/qubo_N.json` preserves these coefficients and the variable-to-source mapping. All 1,024 states are checked against the physical objective by the tests.

QAOA starts at |+>^n, alternates exp(-i gamma C) and exp(-i beta sum X) for p=3 layers, and uses classical COBYLA to tune six angles. The cost operator is scaled by one positive constant for optimization. Three seeded starts each allow 180 function evaluations. The final optimized state is sampled 4,096 times. No exact answer is supplied to the optimizer or injected into the sample set. Bit i is variable i; printed bitstrings put variable 0 on the right.

The implementation follows the alternating cost/mixer construction in [Farhi, Goldstone and Gutmann, A Quantum Approximate Optimization Algorithm](https://arxiv.org/abs/1411.4028). Tests compare the simulator against an independently constructed dense matrix exponential on two qubits.

## Classical comparisons and interpretation

Exhaustive enumeration provides the exact encoded optimum. Economic merit order supplies a simple classical dispatch baseline; it is already optimal for these default linear costs and contiguous encodings. For arbitrary noncontiguous custom encodings, greedy may miss feasible allocations.

The reported quantum allocation is the lowest-cost feasible state among the measured samples. It is **not necessarily the most frequent state**. Selecting the best of 4,096 samples from a 1,024-state space can find the optimum even with weak quantum concentration. Compare `optimal_probability` with `uniform_optimal_probability`; matching the exact optimum alone is not evidence of quantum advantage. The optimizer's success flag and message are preserved even if its evaluation budget is exhausted. Expected penalized energy and dispatch cost are distinct quantities.

Runtime of the exact solver covers minimization over the precomputed feasible states. QAOA runtime covers parameter optimization and final sampling. Both exclude shared problem construction; this is not a scaling benchmark.

The project is designed for Challenge 03 and focuses on a transparent, runnable demonstration of quantum-assisted energy planning. It prioritizes challenge fit and a strong visual demonstration; it cannot guarantee judging outcomes.

## Presentation sequence

1. Explain the AI-load surge and the five constrained resources.
2. Open `results/dispatch.svg`: show resource contributions, demand and costs.
3. Run `python dispatch.py` live and compare the measured quantum result to exact and greedy dispatch.
4. Explain ten binary decisions, the mismatch penalty, the cost/mixer layers and classical angle tuning.
5. Show `results/convergence.svg` and probability metrics, then the 160 kWh infeasibility case.

## Scope

Single synthetic one-hour interval; battery begins with 30 kWh usable stored energy and its cost represents a simplified discharge cost. No charging, inter-hour state of charge, losses, AC power flow, network constraints, carbon optimization, forecast uncertainty, generator startup costs, ramping, or hardware noise are modeled. Renewable availability is a scenario input, not a forecast. All five default resources have 30 kWh capacity to keep encoding simple. This small linear dispatch problem is easy classically; this project demonstrates a transparent quantum-assisted formulation, not a speedup or production energy planner.

## Files

- `dispatch.py`: model, exhaustive and greedy baselines, QAOA simulator and CLI.
- `scenarios.json`: explicit synthetic inputs.
- `visuals.py`: standalone SVG charts, generated from the fresh results.
- `test_dispatch.py`: objective, unitary simulation, capacity and sampling checks.
- `results/`: generated JSON, CSV and SVG artifacts, including reproducibility settings and dependency versions.
