# DOOM-E8c: does a denser snapshot grid and the pooled cutoff improve fork-date recovery? (exploratory)

**Status: exploratory, written 2026-11-23 before any new snapshot is scanned or scored. Not registered with two design reviews; the owner asked for an exploration.** Follow-up to DOOM-E8 H8.3(b) (draft PR #3) and E7 Amendment 2 (draft PR #2). The idea is the owner's; it was generated after seeing E8's results, including which pairs failed.

## Question
E8 estimated the date a child port forked from its parent by fitting a hinge to `shared(child@t, parent@t)` over a **semi-annual** grid (5 points for `dsda-doom`/`prboom-plus`, 10 for `nugget-doom`/`woof`, 25 for `crispy-doom`/`chocolate-doom`) and extrapolating back to `S = 1`. Errors in years (structure, max): `dsda-doom` -0.05, `nugget-doom` -0.75, `crispy-doom` -28.8; names did as well or better for `nugget-doom` (-0.05). Two things could improve this: **more points** (a monthly grid right after the fork, where the decline starts), and the **pooled multi-decoy cutoff** (E7 Amendment 2: K = 25) in place of E8's cutoff. Which one matters?

## Design
* Pairs: the three same-language pairs with git ground truth (`manifest/e8_fork_truth.csv` in E8): `crispy-doom`/`chocolate-doom` (2013-12-09), `dsda-doom`/`prboom-plus` (2020-11-09), `nugget-doom`/`woof` (2021-08-31). `kocoa-doom`/`mochadoom` (cross-language, no usable points in E8) is not repeated.
* **Dense grid:** monthly for the 36 months after the fork, quarterly after that to the head; child and parent each at the last first-parent commit at or before the date; identical-SHA rows excluded. SHAs are resolved and written to `manifest/e8c_grid.csv` and committed **before any scan**.
* Same engine (`704cb35f0`), same scope rules, scanner as E7 Amendment 2 (checkout `b1a9e92`).
* **Four arms,** so the two effects are separable:
  * **A** E8 as registered (read from E8's `h83b_pairs.csv`, not recomputed);
  * **B** E8's own semi-annual points rescored with the pooled K = 25 rule (cutoff effect alone);
  * **C** dense grid, pooled K = 25 rule (both changes);
  * **D** dense grid, single shuffle per pair (E7/E8-style cutoff; density effect alone).
* Per snapshot pair: structure `shared` = max over the two directions of the Wilson lower bound of twins / eligible (loc at least 6), and the min; names `shared` = the same on the share of eligible functions whose E7 name key (stoplist) is found in the other snapshot (no decoy certification, unlike E8; arm B shows whether that matters).
* Estimator unchanged: E8's `hinge_fit` and its placebos (time-shift and permutation), imported from `e8_analyze.py`. Added: a point bootstrap (1,000 resamples) for an interval on the estimate.

## Predictions (before any scan)
* **P1:** in arm C, `dsda-doom` and `nugget-doom` structure (max) estimates are within **0.5 years** of the git truth (E8: -0.05 and -0.75).
* **P2:** `crispy-doom` stays poor (error more than 5 years early) in every arm, because its post-fork decline is slow and the exponential hinge extrapolates far; more points do not fix a model misfit.
* **P3:** the bootstrap interval on the estimate is narrower in arm C than in arm B for `dsda-doom` and `nugget-doom`.
* **P4:** names are at least as accurate as structure for `nugget-doom` in arm C (E8: names -0.05, structure -0.75).
* **P5:** the observed absolute error is below the placebo median for every pair and method that has a fit.
* **P6 (what separates the effects):** arm D differs from arm C by less than 0.25 years in the estimate for `dsda-doom` and `nugget-doom` (the cutoff rule matters little once the grid is dense); arm B differs from arm A by less than 0.25 years (E8's pooled-per-port cutoff was already steady).
A failed prediction is reported as failed.

## Limits
* Three pairs; this is a feasibility exploration, not validation. The result applies to forks with shared git history.
* The hinge model assumes `S = 1` at the fork and exponential decline; merges from a living parent re-converge a child (visible in E8's `pairs_grid`), which the model cannot represent.
* A child that adds code lowers `shared(max)` only slowly; `shared(min)` is reported for that reason.
* Third-party source is not committed; only the manifest, scripts, measurements and hashes.
