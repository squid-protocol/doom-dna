# Mutant screen runbook (how to screen a port; lessons from E15)

**Goal.** Lesion every function of a port, replay a shared demo suite, record each lesion's phenotype, and compare phenotypes across ports (`preregistration/E15_ROLE_SCREEN.md`). Code: `demo/harness/mscreen/`.

## Steps for one port
1. **Engine with digest + runtime.** The port must emit the 19-column per-tic digest (see E13) and accept `E13_MUT`, `E13_REF`, `E13_VERDICT`, `E13_PROFILE`, `E13_NODIGEST` (runtime in `e13_screen.{c,h}`, `E13Mut.cs`; early abort in `patch_abort.py`). A new language needs a tree-sitter config in `schemata.py` (function, binary-expression, literal node types, probe text).
2. **Build the lesion binary** (`build_c.py`, `build_cs.py`): one build, every lesion a runtime switch; ill-typed lesions are dropped by a compile-error loop that attributes errors to the innermost lesion. C# needs extra rules (definite assignment, reachability).
3. **Validate** (never skip): `check_zero.py` (no lesion active: every demo replays the clean digest exactly); `validate_c.py` / `validate_cs.py` / `validate_v2.py` (lesion via switch equals the same lesion rebuilt classically).
4. **Demos.** `gen_demos.py` (sticky, chaos, game-mode variants, `doom2` for Freedoom), `select_demos.py` (greedy by new executed lesion sites; both ports must replay identically). Freedoom demos live in `wads/<demo>/freedoom2.wad` because Managed Doom reads the game from the file name.
5. **Run** `runner.py <screen_dir> <store.sqlite> [--engine md] [--clean DIR] --workers N`; resumable; a lesion runs only on demos that execute its site; hangs are recorded fast (6x the clean time) and re-run once with `--rerun-hangs`; `--refresh-profile` adds new sites or demos to an existing store.
6. **Guard.** `baselines.py snapshot` before, `baselines.py verify` after (checksums of clean digests and demos plus a no-lesion replay of every demo on both engines).
7. **Analyse** (`analysis/`): `run_e15.py` (registered primary), `run_sensitivity.py`, `run_exploratory.py`, `report_html.py`; validated on synthetic screens (`tests/test_analysis_synthetic.py`, `python tests/test_analysis_synthetic.py`).

## Lessons (each cost time)
* **No `preexec_fn` with threads** (deadlock): use `nice` in the command.
* **Infinite-loop lesions exhaust workers**: scale the timeout to the clean run time; re-run hangs separately; commit progress as jobs complete (not in submission order).
* **Function-entry reach is not site reach**: per-site counters distinguish "never executed" from "executed and harmless".
* **Record the mask of every mismatching column** (the RNG column masks which state class broke).
* **Index lesions are undefined behaviour** (out-of-bounds on arrays): excluded. Shift lesions are build-dependent: excluded from the primary analysis.
* **A statement-deletion switch can break C# definite assignment**; negating `while (true)` breaks reachability analysis: both are handled by the compile loop.
* **Other sessions load the box** (the runner pauses above its load limit): check `loaded.sh`-style load tests before blaming the runner.
* **Blind rule.** Do not query lesion outcomes before the analysis code is registered; completeness counts (rows present, hangs) are fine.
