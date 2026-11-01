# JeL — real IBM hardware run

Run these commands in a terminal in this project folder, or in qBraid Lab after uploading the folder. qBraid serves as the Python host; IBM Runtime submits directly to your IBM account.

```text
python -m pip install -r requirements-ibm.txt
python -m unittest -v
python ibm_hardware.py
```

The last command validates the Qiskit circuit against an independent statevector implementation without using hardware quota. It must print PASS before submission.

In a private qBraid notebook cell, save credentials using hidden prompts:

```python
from getpass import getpass
from qiskit_ibm_runtime import QiskitRuntimeService
QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform",
    token=getpass("IBM API key: "),
    instance=getpass("Open Plan instance CRN: "),
    overwrite=True,
    set_as_default=True,
)
```

Get the API key and the Open Plan instance CRN from your IBM Quantum Platform account. Check the instance's remaining quota there. Do not paste secrets into chat or commit them. Credentials are stored privately by the IBM client in that execution environment.

Submit one scenario using job mode:

```text
python ibm_hardware.py --submit --scenario 0
```

The script selects an accessible operational real processor, transpiles the ten-qubit QAOA circuit for that processor, and submits 4,096 shots with a 60-second QPU execution limit. This limit is not a guarantee of successful completion or total remaining account quota. Queue waiting can take substantially longer. Local angle optimization avoids repeated optimizer jobs on the free plan. This is locally trained QAOA executed on real hardware, not optimization trained entirely on a QPU.

The job ID is printed immediately and saved under `results/ibm/`. If the terminal disconnects, retrieve that same job rather than resubmitting:

```text
python ibm_hardware.py --job-id YOUR_JOB_ID
```

Keep the corresponding manifest JSON. Retrieval uses its original scenario, ensuring measurements are decoded against the correct inputs. The result JSON preserves actual hardware counts, backend, job ID, exact comparison, best feasible sample, modal sample, feasible shots and optimal shots. Show the IBM dashboard job alongside this JSON as hardware evidence. The prepared ISA circuit is saved as QPY.

Only after inspecting the first result and remaining quota, optionally submit the surge:

```text
python ibm_hardware.py --submit --scenario 1
```

Noise can reduce quality; an optimal result cannot be promised. A completed hardware job and measured feasibility/optimality are separate claims. If no feasible sample is measured, the report records null rather than substituting a classical answer.

IBM Open Plan currently provides up to 10 minutes of QPU time per rolling 28 days and supports job/batch mode, not sessions. Sources: https://quantum.cloud.ibm.com/docs/en/guides/max-execution-time and https://quantum.cloud.ibm.com/docs/en/guides/run-jobs-session.

Hardware submission requires your saved credentials and available account quota. Until an actual job completes, simulator results are not hardware evidence.
