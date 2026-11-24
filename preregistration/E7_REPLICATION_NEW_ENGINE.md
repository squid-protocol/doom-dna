# DOOM-E7 replication on the current engine (registered before any scan)

Registered 2026-11-24 (US Eastern), on branch `e7-new-engine`, committed before any scan of this replication. This is a replication of E7 (protocol, Amendment 1, Amendment 2 and 2a) with **one change: the GitGalaxy engine**. It needs no two-design-review process because the design is not changed. If the design has to change, I stop and report.

## Pins

| | Original E7 | This replication |
|---|---|---|
| Engine (`squid-protocol/gitgalaxy`) | `704cb35f075660a637b61331554d8ff0bf206036` (2026-11-22 14:38 EST) | `beb46cfbc65391bd210dda4175045c78b1e96047` (origin/main at start, commit date 2026-11-24 07:50 EST), detached worktree `/srv/storage_16tb/projects/gitgalaxy-worktrees/e7-engine-current` |
| Commits between | | 120 |
| sfs scanner | checkout at `b1a9e92` (pin file says `bcd3cb7`; same matching code, see Amendment 2 section F) | same checkout, unchanged |
| Reference model | `spec_hash f5d525ed16bc91db`, vendored file unchanged | same vendored file. `tools/refresh_reference.py` is run against the new engine into a side file and **not adopted** |
| 66 programs | `manifest/RUN_PINS.json` | same SHAs, same scope drops (`manifest/scope.csv`); sources are copied from the original clones' working trees, `.git` and `.gitgalaxy` left out, into fresh scratch git repos with `git add -f -A` |

## Frozen

Every hypothesis, metric, the 2% floor, the name rules and stoplist, the text arbiter, Amendment 2's pooled multi-decoy rule with K = 25 (seeds 0..24), the S1 conservative variant, the analysis scripts. Scripts are copied to `measure_new_engine/` with only two kinds of change: the work-directory path and the engine short SHA (listed exactly in the results file). Same order of operations: scan all 66, Phase A (51 programs), arbiter, Phase A analysis, Phase B (15 withheld) against the frozen map, then the Amendment 2 pooled cutoff on Phase A.

## What the structure arm reads (worked out from `structural_fingerprint/scan_io.py`, `fingerprint.py`, `features.py`, `twins.py`)

From the engine's scan database (`function_data`, `file_data`): per function `loc`, `complexity`, `args`, `keyword_density`, and the 31 per-function signal counts named in the reference model (among them `branch`, `structural_boundaries`, `args`, `func_start`, `safety`, `io`, `api`, ...), plus the function name and file path (for the structural key, the names arm and the arbiter) and which files and functions the engine extracts at all. The twin vector is built only from these through the vendored reference model; the decoy strata use the reference model's own nearest-centroid archetype, not the label stored in the scan.

It also loads the call edges (`fcall_data`), `func_fan_in` and `func_fan_out`, but uses them **only for descriptive fields of the fingerprint file** (a geometry sketch and a call-graph shape summary). They never enter a twin vector, a distance, a cutoff, a name key or any E7 metric. The import graph is not read at all. **So call-graph and import-graph quality cannot move any E7 headline number except by changing which functions or signals the scan contains.**

What can move it: (a) the #8939 split of boolean operators out of `branch` into `short_circuit` (the `branch` column falls for every function with `&&`, `||`, `and`, `or`; `short_circuit` is not a reference column, so it is dropped; the reference scaler was fitted before the split and is not retrained; C# also gains `&&`/`||` in `complexity`); (b) other rule or slicer changes to specific languages in 120 commits (Elixir #9064, R #9065, Nim #9066, Erlang #9130, Perl/PHP #9060, Shell/PowerShell/Solidity #8921 and others; the engine's DOOM-rosetta golden moved for four ports: odamex, edge-classic, managed-doom, helion).

## Expectations (written before any scan)

1. **Same or nearly same** for the C and C++ ports that carry most of the numbers, because both sides of every pair are scanned by the same engine, so the `branch` shift moves both together; only distances near a cutoff and exact-clone keys can flip. Expected: detectable programs (structure) 25 plus or minus 2; nearest-is-family (common set) within 0.05 of 0.62; H7.1 (21 of 22) stays met, 20 to 22; Spearman vs text survival 0.87 plus or minus 0.04; triplet compatibility 0.848 plus or minus 0.03; the names columns unchanged for programs whose function extraction did not change (exactly equal; any difference is an extraction change, not a structure change).
2. **Changed** for the languages the engine changed: C# (managed-doom, helion, and any other C# program), Lua, PowerShell, and programs in the other touched languages. Expected to differ in per-program share, not in conclusions.
3. Phase B: positives 3 of 5 attach under structure, 0 false attachments among large negatives, 11 of 14 correct placements, 6 of 8 leave-one-out. Expected the same.
4. Amendment 2 (K = 25): nearest-is-family on the fixed 25-program set 0.619 plus or minus 0.05; H7.1 21 of 22; detectable at the 2% floor under the primary rule 35 plus or minus 3. Stated non-prediction: the pooled rule is deterministic given the scan, so any difference is data, not chance.
5. Scorecard H7.1 to H7.7: no verdict flips.

## Rule for calling a change real

A difference is **real** only if at least one of: (i) a rate or count moves outside the original's own interval (exact or bootstrap 95% CI where the original reports one); (ii) a program crosses the 2% floor in either direction, or its nearest relative or its Phase B placement changes; (iii) a scorecard prediction flips its verdict. For quantities that have no interval in the original (medians, tree scores, Spearman), a change of at least 0.05 (0.5 rank for the median parent rank) is called **moved** and not real. Per-program shared-structure shares: a change of at least 0.03 is **material** (the threshold Amendment 2 used for its stable-pair prediction). Anything smaller is noise-level and reported as unchanged.

## Attribution design (proportionate, not a bisection)

Two controls beyond the main run, all on the same 66 programs: **(C0)** the original engine `704cb35f0` run through this same harness, to show the harness reproduces the original function tables (if it does not, that is a finding and the comparison is limited to the harness); **(C1)** engine `3c436c8c57` (#8939 itself, the first commit after the pin, whose parent is the pin), which isolates the boolean-operator split from the other 119 commits. Phase A pair tables (Amendment 1 single-shuffle rule, a cheap 4-minute step) are produced for C0, C1 and the new engine, and the scan databases are compared column by column on the columns the structure arm reads. A change that appears between C0 and C1 is attributed to the signal split; a change that appears between C1 and the new engine is attributed to the other 119 commits, and then to call-graph work only if the function-table columns that differ are ones call-graph code can touch (it cannot touch any column read by a twin vector). The full Amendment 2 K = 25 run is done once, on the new engine.
