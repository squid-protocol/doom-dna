# DOOM-E10 part 2 results: E7 structural arm repeated on normalised source (2026-11-23)

Rules as in [the part 2 registration](../../preregistration/E10_PART2_E7_REPEAT.md) (predictions committed before any normalised scan was read). Full normalised Phase A report: `e7n_phaseA_report.md`. E7 analysis code unchanged; scans in git mode as E7. Phase B (withheld set) not yet run.

## Headline
Normalising before scanning barely moves the E7 picture. Shared structure with `linuxdoom` changed by less than 0.05 in 46 of 50 programs. The flat, low ports stay flat and low: gzdoom 0.006 to 0.006, odamex 0.001 to 0.002, edge-classic 0.000 to 0.000, srb2 0.019 to 0.015, woof 0.009 to 0.023, dsda-doom 0.019 to 0.032, eternity 0.000 to 0.000. Formatting is therefore **not** the main reason those ports show little structure.

Moves: prboom-plus 0.025 to 0.169 (+0.144), fastdoom 0.151 to 0.238 (+0.087), doom-ios 0.026 to 0.084 (+0.058); inter-doom 0.168 to 0.077 (-0.092), crispy-doom 0.354 to 0.324 (-0.030).

## Predictions
| | Prediction | Outcome |
|---|---|---|
| P1 | detectable structural descent does not fall, rises by at least 3 (E7: 25) | 28 of 51. Met (+3). Part of the rise is a coverage change (doom3-bfg parsed 1,058 to 16,379 functions). |
| P2 | same-language ports rise or stay equal in at least 70% | Judged on shared structure with `linuxdoom` only (not on each port's declared relatives; not computed): mostly equal, 3 rose, 1 fell by more than 0.05. |
| P3 | translations unchanged | gore 0.000 to 0.000. Met. (cpp-doom is Phase B, not run.) |
| P4 | unrelated controls stay below floor | nginx, leveldb, curl, libuv at or below 0.003; quake 0.004 to 0.009. Met. |
| P5 | Spearman vs text survival does not fall by more than 0.05 | structure 0.865 to 0.878; names 0.928 to 0.922. Met. |
| P6 | nearest-is-family within 0.05 | structure 0.619 to 0.542 (-0.077), names 0.600 to 0.733 (+0.133). **Not met**, but the programs scored differ (25 vs 28 structurally detectable; 41 vs 40 for names), so this is not a like-for-like change. |

Other: resolved-triplet compatibility with the declared tree, structure 0.848 to 0.771, names 0.869 to 0.852. The names arm is not invariant under normalisation (different parse, different function sets), so names moved too.

## Honest limits
* Detectability changes mix real signal with changed function coverage (doom3-bfg, doom-ios), so counts of "detectable" ports should be read with that in mind.
* The scan mode matters: a first run without git mode made doomgeneric drop to 0 functions (a `.gitignore` effect, not normalisation). It was caught by a function-count check and rerun in E7's git mode. My earlier spike-in comparisons used the no-git mode for the normalised side and need rechecking.
* Normalisation only helps ports whose code is copied and reformatted. It cannot recover rewritten code, which is what most flat ports appear to be.

## Follow-up (2026-11-23): what actually moved, and why

**By relationship** (pairs with at least 0.02 shared structure in either run; change = normalised minus E7; "up/down/flat" at +-0.02):

| Relationship | Pairs | Mean change | Up | Down | Flat |
|---|---:|---:|---:|---:|---:|
| Declared parent and child | 30 | +0.012 | 6 | 3 | 21 |
| Further declared ancestor | 14 | -0.001 | 1 | 2 | 11 |
| Same lineage (shared non-root ancestor) | 18 | -0.008 | 1 | 3 | 14 |
| Only `linuxdoom` / unrelated | 191 | +0.005 | 36 | 12 | 143 |

Between a port and its direct parent, normalisation changes nothing (for example `chocolate-doom` to `crispy-doom` 0.790 to 0.776; `inter-doom` to `crispy-doom` 0.492 to 0.475).

**The large moves are a threshold effect, not formatting.** E7 sets a threshold per pair from decoy matches (target-decoy, FDR 0.01). That threshold is unstable: for `linuxdoom` to `inter-doom` it went 0.065 (E7) to 0.000 (normalised); for `linuxdoom` to `prboom-plus` it went 0.000 (E7) to 0.061 (normalised). At a threshold fixed at 0.065 in both runs, shared structure with `linuxdoom` is almost unchanged by normalisation:

| Port | Own threshold E7 / normalised | Fixed 0.065 E7 / normalised |
|---|---|---|
| inter-doom | 0.168 / 0.077 | 0.167 / 0.164 |
| prboom-plus | 0.025 / 0.169 | 0.157 / 0.175 |
| doom-ios | 0.026 / 0.084 | 0.164 / 0.190 |
| woof | 0.009 / 0.023 | 0.126 / 0.120 |
| dsda-doom | 0.019 / 0.032 | 0.151 / 0.146 |
| srb2 | 0.019 / 0.015 | 0.100 / 0.109 |

**Consequence for E7 (and probably E8):** E7's low values for `woof`, `dsda-doom`, `prboom-plus`, `doom-ios` and `srb2` were understated because the per-pair threshold collapsed to 0 for those pairs. At a fixed 0.065 they sit at 0.10 to 0.16, above the background of the unrelated controls at the same threshold (`nginx` 0.023, `curl` 0.023, `libuv` 0.039, `helion` 0.030, `quake2` 0.074). The fixed threshold is not FDR-controlled, so this is evidence that the registered rule is unstable, not a corrected number.

Eligibility (6 lines) and the exact-clone zone (12 lines) are layout dependent (`linuxdoom` 689 to 651 eligible; 69 functions leave the 12-line zone) but explain only about 10% of lost twins in `inter-doom`.
