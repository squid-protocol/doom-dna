# `DOOM-E8` Amendment 2 (2026-11-22): registration record, pins and one procedural rule

Registers `DOOM-E8` (with [Amendment 1](E8_AMENDMENT_1.md)) at the commit that adds this file and the plan files below, **before any E8 scan**.

## Pins

* Engine `704cb35f0` (GitGalaxy `origin/main` of 2026-11-22, detached worktree `gitgalaxy-worktrees/e7-engine`), sfs `main` at `bcd3cb7`, `spec_hash` structure `f5d525ed16bc91db`. Same as `DOOM-E7`; E7 code (`measure/e7_names.py`, `e7_run.py`, `e7_arbiter.py` on draft PR #2) is reused unchanged.
* Reference `R1 = linuxdoom` at the E7 pin `a77dfb96...`; placebo reference `R0 = nginx` at its E7 pin `2e8440bc...`.
* Histories: existing full clones under `temporal-crucible-pool/doom-ports` and `temporal-crucible-pool/curl`; full clones of `nginx` and `libuv` fetched 2026-11-22 into `doom-e7-work/halflife/controls`.

## Plan files (committed with this amendment; built by `measure/e8_plan.py`, outcome-blind)

* `manifest/e8_plan.csv`: 161 calendar half-life rows (11 lineages, 3 child ports, 4 descriptive or rewrite controls, 3 unrelated C controls, plus fork-pair parents), with `stratum`, `first_parent_commits`, `same_language`, `scope_key`.
* `manifest/e8_plan_commitcount.csv`: 77 rows (11 lineages, fractions of first-parent commit count).
* `manifest/e8_grid_pairs.csv`: 49 semi-annual post-fork steps for four child/parent pairs; `manifest/e8_fork_truth.csv`: ground-truth fork commits (crispy-doom/chocolate-doom 2013-12-09; dsda-doom/prboom-plus 2020-11-09; nugget-doom/woof 2021-08-31; kocoa-doom/mochadoom 2019-07-20).
* `manifest/e8_rescan.csv`: 28 noise replicates (all planned commits of `woof` and `edge-classic`, scanned twice more).
* `manifest/e8_tasks.csv`: **296 distinct scan tasks** (repo, commit, scope key) covering all of the above; 324 scans including the replicates.

## Procedural rule (a dated relaxation of Amendment 1 §E)

Amendment 1 asked for the analysis scripts to be committed before the first scan. Scanning and fingerprinting are **outcome-blind** (they compute no survival and no trend). So: the snapshot runner, the measurement scripts and the analysis scripts are committed **after the scans finish and before any scan output is read for survival, shared or trend**; the output manifest hash is committed before any figure. The pre-scan **precondition table** (distinct snapshots and eligible-function counts per planned commit, from `ctags` on each export) is produced by the runner and committed with the measurement scripts; it is not an outcome.

## Known limits recorded at registration

Several fractions collapse to the same commit for short histories (the plan keeps the duplicates, the analysis de-duplicates); `room4doom` is not in this plan; `curl` and `nginx` in their pinned heads may not be in the clone's first-parent history (flagged `head_in_history`).
