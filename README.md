# JeL Q-Site

A Python terminal application for exploring microgrid energy planning using Qiskit quantum simulation and classical optimisation.

## What it helps with

- Compare electricity costs across solar, wind, batteries, grid imports, and diesel.
- Explore the trade-off between lower operating costs and keeping battery reserves.
- Simulate power outages and estimate additional battery energy needed for essential services.

Runs locally with synthetic scenarios. No quantum hardware or API keys are required.

## How to run

Use Python 3.11 or newer.

```bash
git clone https://github.com/edwingeorgeshaji/JeL-Q-Site.git
cd JeL-Q-Site
python -m pip install -r requirements-qiskit.txt
python dashboard.py
```

Choose a preset or enter your own energy requirements, then select an outage scenario.

For an automatic demo:

```bash
python dashboard.py --demo
```

To replay saved results:

```bash
python dashboard.py --cached
```
