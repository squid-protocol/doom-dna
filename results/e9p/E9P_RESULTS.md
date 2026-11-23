# DOOM-E9p results (2026-11-23): E9's structure arm rerun with the pooled multi-decoy cutoff

Rules as in [the E9p note](../../preregistration/E9P_POOLED_CUTOFF.md) (predictions written before any pooled prediction). Only the twin-search cutoff changed (pooled K = 25, E7 Amendment 2); the truth set, names arm, baselines, spike-ins and analysis code are E9's. Full pooled report: `phase_report_pooled.md`; tables `*_pooled.csv`. Exploratory rerun.

## Headline
**The pooled cutoff certifies many more pairs and almost none of the extra ones are real.** The share of port pairs with a nonzero cutoff in both directions rises from **20% to 79%**, but true near-copies found barely change (1,826 to 1,831 of the predicted pairs), predicted pairs rise from 7,691 to 10,121, and **false positives on unrelated C code rise 4.6 times** (60 to 273 functions; 14.4 to 65.7 per 1,000). Precision falls (co-primary truth 0.39 to 0.30; text criterion 0.24 to 0.18). Recall of near-copy classes is unchanged (0.260 to 0.261). The names arm reproduces exactly.

| Quantity (structure, primary) | E9 as run | pooled K = 25 |
|---|---:|---:|
| Port pairs with a nonzero cutoff in both directions | 20% | 79% |
| Predicted pairs / confirmed | 7,691 / 1,826 | 10,121 / 1,831 |
| Precision, co-primary truth (names 0.19 in both) | 0.39 (difference +0.20, interval 0.12 to 0.26) | 0.30 (+0.11, 0.05 to 0.16) |
| Precision, text criterion | 0.24 | 0.18 |
| Recall of near-copy classes | 0.260 | 0.261 |
| False positives, unrelated C code (nginx, leveldb) | 60 (14.4 per 1,000) | 273 (65.7 per 1,000) |
| False positives, from-scratch rewrites | 203 (32.0) | 412 (65.0) |
| Documented transfers (textscreen, opl, music) | 0.81, 0.71, 0.84 | 0.81, 0.71, 0.84 |
| Spike-in, 100% renamed (large / small) | 0.95 / 0.96 | 0.95 / 0.96 |
| Spike-in, renamed + stripped + reformatted | 0.49 / 0.64 | 0.53 / 0.60 |
| Spike-in, plus a statement per function | 0.43 / 0.00 | 0.33 / 0.34 |
| Spike-in, 30% of the module | 0.90 / 0.86 | 0.98 / 0.93 |

## Predictions
| | Prediction | Outcome |
|---|---|---|
| P-a | nonzero cutoff in both directions rises from 30% to at least 60% | **met** (baseline was 20%, now 79%) |
| P-b | renamed + stripped + reformatted rises by at least 0.10 in both modules | **not met** (+0.04 large, -0.04 small) |
| P-c | 100% renaming stays within 0.05 of 0.95 / 0.96 | **met** (0.95 / 0.96) |
| P-d | statement per function: large rises by at least 0.10; small stays below 0.20 | **not met** (large fell 0.43 to 0.33; small rose 0.00 to 0.34) |
| P-e | false positives on unrelated C code rise by less than a factor of 3 | **not met** (4.6 times) |
| P-f | near-copy recall rises by at least 0.05; text precision changes by less than 0.10 | **not met** (recall +0.001; precision change -0.056 is within the bound) |
| P-g | names arm reproduces exactly | **met** |
| P-h | documented transfers do not fall | **met** (unchanged) |

## Reading
The pooled rule answers a different question than E9 asks. For **estimating how much two programs share** (E7), a cutoff that is steady and not artificially conservative reduces understatement. For **flagging individual transferred functions with false-positive control** (E9), after the vertical mask the candidate pool is small and mostly unrelated code, and a cutoff that is more permissive (the multi-decoy finite-sample correction shrinks with K) lets in unrelated functions at four to five times the old rate while adding almost no true transfers. E9's registered headline stands as run; this rerun is a sensitivity analysis showing that the conservative single-shuffle behaviour was the safer choice for detection. The takeaway for E7 Amendment 2: choose the cutoff by the question (estimating share: pooled, with the conservative variant alongside; detecting transfers: conservative).
