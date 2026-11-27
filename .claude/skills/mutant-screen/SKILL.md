---
name: mutant-screen
description: Screen a program's functions with one-token lesions (mutant schemata, one build per port) against a deterministic replay assay, store phenotypes, and compare functions across implementations by what breaks. Use when asked to build, run, validate or analyse a mutant screen / role screen (E15), add a port or lesion class, or extend the demo suite.
---
# Mutant screen

Read `docs/notes/MUTANT_SCREEN_RUNBOOK.md` first (steps, lessons) and `preregistration/E15_ROLE_SCREEN.md` (hypotheses, amendments, blind rule).

Workflow: build the lesion binary (`demo/harness/mscreen/build_c.py` or `build_cs.py`) -> validate (`check_zero.py`, `validate_*.py`) -> choose demos (`select_demos.py`) -> run (`runner.py`, resumable) -> guard (`baselines.py`) -> analyse (`analysis/run_e15.py`, `run_sensitivity.py`, `run_exploratory.py`, `report_html.py`).

Rules: never query lesion outcomes before the analysis code is committed; validate every new lesion class against classical rebuilds; new lesion ids go above 10,000 and never renumber old ones; kill processes by PID (never `pkill -f` in the Bash tool); the box is shared, so respect the runner's load limit and do not touch other sessions' processes.
