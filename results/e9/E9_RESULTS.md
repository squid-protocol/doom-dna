# DOOM-E9 results: finding horizontally transferred code, structure against names

Registered 2026-11-22 20:03 EST (commit `33e8bf6`); truth-set size recorded 20:09 (`320973f`); predictions frozen and hashed 20:18 (`4b2e18b`); hand-audit rubric fixed before any rating. Engine `704cb35f0`, sfs `bcd3cb7`. Full report: [phase_report.md](analysis/phase_report.md). 51 programs, 221 eligible port pairs, 239 transfer events, 99 independent lineage pairs (the power gate is met, so the main comparison is inferential). **Wording scope (Amendment 1):** this measures agreement with an independent text and git criterion on same-language near-verbatim copies, and robustness on constructed spike-ins. It does not show that structure finds transfers better than names in general.

## The answer in plain terms

**Structure is more precise than names at what it reports, names are cleaner on unrelated code, and neither is robust to everything. Renaming alone does not hide a copy from structure; reformatting and small edits do.**

| Question | Structure | Names |
|---|---:|---:|
| **Precision** against the co-primary truth (text, documentation, hand audit) | **0.39** | 0.19 |
| Precision against the text criterion alone | 0.24 | 0.11 |
| Recall of near-copy pairs (text criterion) | 0.26 | 0.29 |
| False positives on **unrelated C code** (`nginx`, `leveldb`), per 1,000 functions | 14.4 (60 functions) | **0** |
| False positives on **from-scratch rewrites** (`helion`, `room4doom`, `rust-doom`), per 1,000 | **32** | 59 |
| Random pairing / geometry-only baselines, precision | 0.000 / 0.018 | |

* **P1 (primary): structure's precision is higher, difference +0.20 (95% interval 0.12 to 0.27; de-duplicated version +0.18).** Both are low in absolute terms: most predicted pairs are not near-verbatim copies. It is **fragile to the vertical mask**: if names are masked by their own name keys (a registered sensitivity), names reach 0.52 and structure 0.44 on the same truth, so the winner depends on how "already inherited from linuxdoom" is defined. The headline mask is the predictor-independent text arbiter.
* **P2 (primary): structure's false-positive bound on unrelated code is not lower.** Structure flagged 60 of 4,153 functions (upper 95% bound 17.9 per 1,000); names, under the same pair-level certification, flagged none. Both are far below a chance floor of 67 per 1,000. Structure is the cleaner of the two only on from-scratch rewrites that reuse DOOM's vocabulary.
* **Documented transfers (Chocolate's `textscreen` and `opl`):** names recover 95% to 100% of the verbatim copies; structure recovers 80% to 93%. Where the names are the same, names are the easier tool.

## The renaming test the owner asked for (spike-ins, exact by construction)

Code from `curl` (162 functions) and `libuv` (106) was inserted into a scratch Chocolate Doom and disguised in tiers. Recall of the inserted functions:

| Disguise | Structure (large / small module) | Names (large / small) |
|---|---|---|
| Verbatim | 0.95 / 0.96 | 0.96 / 0.39 |
| 50% of functions renamed | 0.95 / 0.96 | 0.51 / 0.15 |
| **100% of functions renamed** | **0.95 / 0.96** | **0.00 / 0.00** |
| 100% renamed + comments stripped + reformatted | 0.49 / 0.64 | 0.00 / 0.00 |
| the above + a statement added to every function | 0.43 / **0.00** | 0.00 / 0.00 |
| 30% of the module only | 0.90 / 0.86 | 0.94 / 0.41 |

* **Hiding a copy by renaming functions defeats names completely and does not touch structure** (0.95 against 0.00). That is the owner's claim, now measured.
* **The registered bar was not met:** structure recall under renaming plus comment-stripping plus reformatting is 0.49 and 0.64 against the 0.80 required. Reformatting (it changes line counts, which many of the structural measurements divide by) and adding even one statement per function break the match, and the small module collapses to zero.

## Time evidence (supporting, not proof)

* **Transferred modules arrive as a unit.** The functions of a confirmed transfer appear in the borrower within 14 days of each other in 23% to 67% of cases, against 2% to 11% in permuted baselines (excess +0.48, interval 0.41 to 0.57). Native subsystems also cluster, so this shows "arrived together", not "arrived from elsewhere".
* **Donor first, at the module level:** Chocolate's `textscreen` directory was added 2005-10-02, before Eternity (2006), Odamex (2014) and Woof (2021). At the function level, the order excess over a random baseline is +0.16 (interval -0.003 to 0.34, not above baseline), and 20 functions are dated "recipient first". Those 20 are artifacts of following each function's current form back through history (the donor's later edits move its function-level date), not evidence of reverse copying.

## Hand audit

Two model raters (a Claude subagent and Gemini) labelled 100 blinded pairs; agreement 86% (Cohen's kappa 0.74). Of the 50 pairs the text criterion confirmed, none was audited as independent code; of the 50 predicted pairs it did not confirm, 33 were audited as independent. This supports the text criterion as a truth set. Model raters are a weaker substitute for humans, and the first rater finished the 100 labels in about half a minute, so these labels should be read with that in mind.

## Truth set and caveats

* 7,102 eligible near-copy pairs (Jaccard 0.9) in 239 events and 124 modules; **documented port-to-port transfers are only 7 events from 2 modules (`textscreen`, `opl`)**, all from Chocolate. 3,134 pairs are vendored external libraries (zlib, libpng, miniz and others) and 2,862 are "coincidence" (near-identical code between ports with no documented source), so most of the truth is not transfer between ports.
* Engine mapping: recall covers functions that map to an engine row; C++ ports (Eternity, Odamex, Woof, SRB2) map only 60% to 77% of their functions.
* The spike-in schema needed a small adapter between two helper scripts (`e9_spike_adapt.py`) and the analysis needed one bug fix (blank engine rows); both were fixed before the final analysis and committed.
* All of this is on one corpus (DOOM-family C code).
