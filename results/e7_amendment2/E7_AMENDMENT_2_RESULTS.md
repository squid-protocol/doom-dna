# DOOM-E7 Amendment 2 results (2026-11-23): pooled multi-decoy cutoff, K = 25

Rule as registered in [Amendment 2](../../preregistration/E7_AMENDMENT_2.md) and 2a (K = 25). 2,550 ordered Phase A pairs, 25 decoy shuffles each, same scans and engine as E7 (`704cb35f0`). E7's analysis code run unchanged on regenerated inputs (primary: pooled cutoff; conservative: `+K` kept). The names arm is untouched (identical numbers in all three reports). Status: exploratory; Phase B (withheld) not recomputed.

## Predictions
| | Prediction | Outcome |
|---|---|---|
| P-A1 (primary) | cutoff above zero in at least 90% of active pairs | **98.9%** (352 active pairs). Met. |
| P-A2 | stably high ports change by less than 0.03 | max change 0.013. Met. |
| P-A3 | previously low or unstable ports rise by at least 0.03 | 6 of 7. `prboom-plus` +0.096, `doom-ios` +0.119, `dsda-doom` +0.083, `fastdoom` +0.064, `woof` +0.061, `srb2` +0.045; **`inter-doom` fell 0.028** (E7's single draw, 0.168, was the high side of a coin flip; pooled 0.140). Not fully met. |
| P-A4 (controls) | unrelated controls at or below 0.10 against every program | max 0.028. Met. (`quake`/`quake2` 0.082 with each other, `lua`/`srb2` 0.118, reported separately.) |
| P-A5 (primary) | nearest-is-family on the fixed 25-program set changes by less than 0.10; H7.1 stays met | 0.619 to 0.619 (primary and conservative); H7.1 21 of 22 under both. Met. |
| P-A6 | detectable programs rise from 25 to at least 30 | 35 at the registered 2% floor. Met, **but see the floor table**. |
Convergence (K = 12 vs K = 25): 2.0% of active pairs differ by more than 2% of `elig_q` (bound 5%). Adequate.

## What the pooled rule changes
* The cutoff no longer collapses: stable-low ports sit at 6 to 12% shared with `linuxdoom` where E7 reported 1 to 2% (`woof` 0.070, `dsda-doom` 0.102, `prboom-plus` 0.121, `srb2` 0.064, `doom-ios` 0.145, `fastdoom` 0.215).
* Single-shuffle stability among the 352 active pairs: 156 stable-certified, 116 stable-uncertified, 80 unstable (23%): about a quarter of the active pairs were at the mercy of the shuffle in E7.
* Nearest-is-family on the fixed 25-program set is unchanged at 0.619. On the program set each rule detects: E7 0.619, primary 0.560 (35 programs, more programs scored), conservative 0.619.

## Detectability depends on the floor
Structurally detectable programs of 51:

| Floor (symmetrised Wilson lower bound) | E7 single shuffle | primary | conservative |
|---|---:|---:|---:|
| 0.02 (registered) | 25 | 35 | 25 |
| 0.03 | 25 | 30 | 23 |
| 0.05 | 22 | 23 | 20 |
| 0.08 | 20 | 20 | 18 |

Of the ten programs newly detectable at 0.02, six attach to a program in another language group (`agentic-cobol-doom-codex` to `mood` 0.048, `cssdoom` to `edge-classic` 0.057, `fps-cob` to `odamex` 0.083, `freedoom` to `srb2` 0.054, `gzdoom` to `agentic-cobol-doom-cc` 0.043, plus the from-scratch `helion` and `dartdoom` to each other). Background under the primary rule, across 1,216 cross-language pairs: median 0.000, 95th percentile 0.010, 99th percentile 0.025, maximum 0.083; 2% of them exceed 0.02, almost none exceed 0.05. The registered 2% floor therefore sits at the edge of the background, and the rise from 25 to 35 detectable is mostly weak signal between 0.02 and 0.05. At a floor of 0.05 the three rules agree (22, 23, 20).

## Other quantities (E7 / primary / conservative)
UPGMA structure-tree triplet compatibility 0.848 / 0.700 / 0.873 (the primary scored set is larger, so not like for like); H7.2 Spearman over C-family pairs above the floor 0.809 (n = 112) / 0.778 (n = 167) / 0.794 (n = 94).

## Reading
E7's structure results hold where the signal is strong: the ranking, the families, the controls, and H7.1. The single-shuffle cutoff understated weak-to-moderate sharing for ports such as `woof`, `dsda-doom`, `prboom-plus` and `doom-ios`, and misreported `inter-doom` and `fastdoom` by a coin flip. The pooled rule corrects that, at the cost of letting a few weak cross-language attachments cross a 2% floor.
