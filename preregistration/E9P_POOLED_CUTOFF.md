# DOOM-E9p: E9's structure arm rerun with the pooled multi-decoy cutoff (exploratory rerun)

**Status: written 2026-11-23 before any pooled prediction was produced. Not registered with two design reviews; a rerun of one arm of E9 (draft PR #5) under E7 Amendment 2's cutoff rule, at the owner's request.**

## Why
E9 scored every port pair with the single-shuffle per-pair cutoff. E9's own saved diagnostics show the cutoff collapsed to zero in at least one direction for **353 of 442 port pairs (80%; 309 in both directions)**, in all 400 negative-control pairs, and in 12 of 24 spike-in pairs. At a cutoff of zero only exact clones count, so for most pairs E9's "structure" predictor was an exact-clone detector. E7 Amendment 2 replaced the single shuffle by a pooled multi-decoy cutoff (K = 25). Does E9 change?

## What changes and what does not
* Changed: the structure predictor's twin search uses the pooled K = 25 cutoff (`e7_draws.pooled_cutoff`, `+1` pooled) in both directions; everything downstream of the twin search is E9's code unchanged (vertical mask, union, premasked and de-duplicated variants).
* Unchanged: the truth set (T1 text copy, T2 history, T3 documented), the names predictor, the random and geometry baselines, the spike-in recipients, the analysis code, the seeds. The names arm's numbers must reproduce exactly.
* Hand audit: E9's model-rater audit covers E9's predicted pairs. Pairs newly predicted under the pooled rule are **not audited** and are reported as such; precision is scored against the text criterion (T1) and documentation (T3), with the audited co-primary figure reported only on pairs both runs predict.

## Baselines to compare against (E9 as registered)
Precision vs the co-primary truth 0.39 (text alone 0.24); recall of near-copy pairs 0.26; false positives on unrelated C code (`nginx`, `leveldb`) 60 functions (14.4 per 1,000); on from-scratch rewrites 32 per 1,000; spike-in recall (large / small module): verbatim 0.95 / 0.96, 100% renamed 0.95 / 0.96, renamed + stripped + reformatted 0.49 / 0.64, plus a statement per function 0.43 / 0.00, 30% of module 0.90 / 0.86; documented `textscreen` and `opl` transfers recovered 80% to 93%.

## Predictions (before any pooled prediction)
* **P-a:** port pairs with a nonzero cutoff in both directions rise from 30% to at least 60%.
* **P-b:** spike-in recall for renamed + stripped + reformatted rises by at least 0.10 in both modules (to at least 0.59 / 0.74).
* **P-c:** spike-in recall for 100% renaming alone stays within 0.05 of 0.95 / 0.96.
* **P-d:** spike-in recall with a statement added per function rises by at least 0.10 for the large module; the small module stays below 0.20 (short functions).
* **P-e:** false positives on unrelated C code rise but by less than a factor of 3 (at most 180 functions, 43 per 1,000).
* **P-f:** recall of text near-copy pairs rises by at least 0.05; precision against the text criterion (0.24) changes by less than 0.10 either way.
* **P-g:** the names arm reproduces E9's numbers exactly.
* **P-h:** documented transfers (`textscreen`, `opl`): structure recovery does not fall below E9's 80% to 93%.
A failed prediction is reported as failed.

## Limits
Written after seeing E9's results and the cutoff-collapse counts. One arm rerun on the same truth set; the false-positive and precision results are the ones most likely to move against the pooled rule, and are reported as they come out. Third-party source is not committed.
