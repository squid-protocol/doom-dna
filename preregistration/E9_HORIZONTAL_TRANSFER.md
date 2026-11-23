# `DOOM-E9`: Horizontal transfer between ports: structure vs names vs random, validated against source text and git history

**Status: DRAFT, not registered. [Amendment 1](E9_AMENDMENT_1.md) (2026-11-22) reconciles two independent design reviews and supersedes the sections it names; read it with this file.** Registers when two independent design reviews are reconciled in a dated amendment and this file is committed before any E9 computation. Thresholds marked `[LOCK]` are proposals. Reuses `DOOM-E7`'s engine, sfs, name key, stoplist, twin machinery and Phase A map; runs after `DOOM-E8`'s scan pipeline is done (E8 and E9 do not share scans).

## 1. Why

The earlier horizontal-transfer result (`followups/seed-and-extend/HORIZONTAL_BORROWING.md`: Chocolate Doom's `textscreen` library in `eternity`, `odamex`, `doom-wasm`, `woof`) used an older engine and a hand-tuned method: fixed distance thresholds (`linuxdoom_thresh 0.35`, `twin_thresh 0.25`), pairs on declared-different branches only, and **names used afterwards to grade and to cluster** (a hit was "the names agree", a module was found by directory). It had no negative controls, no independent ground truth, and no time check. This experiment repeats it with the calibrated E7 machinery, an **independent** ground truth (source text and git history), controls, and the two baselines the owner asked for: names, and random.

## 2. Definitions

* **Vertical inheritance** of a function in port `P`: it has a certified structural twin in `linuxdoom` (E7 rule) or its name key matches one of `linuxdoom`'s.
* **Horizontal candidate** between ports `A` and `B`: a function pair `(a, b)` (eligible, loc at least 6) where **neither** `a` nor `b` is vertically inherited, and `A` and `B` have **no declared common non-root ancestor and no shared git commit** (so shared history, as Chocolate/Crispy, is excluded). Which pairs of ports are eligible is fixed by `declared_lineage_basis.csv` and the shared-commit inventory before any result.
* **Predictors** (each emits a set of candidate pairs per port pair):
  * **Names:** equal E7 name key (primary: with the E7 stoplist), one-to-one by key, not vertically inherited.
  * **Structure:** E7 reciprocal-best-hit twins at `fdr 0.01` between `A` and `B`, not vertically inherited, under the E7 `structure` lens, per-pair threshold.
  * **Random (two nulls):** (R1) for each port pair, the same *number* of function pairs as the structure predictor emits, drawn uniformly from eligible functions of `A` and `B` matched on loc decile; (R2) the sfs target-decoy hits (decoy-matched pairs, which are random by construction) read as the empirical false-hit rate. Seeded.
* **Ground truth, independent of both predictors:**
  * **T1 text copy:** the pair's bodies are near-identical by the **name-blind** text arbiter (4-token shingles, own name masked, comments stripped, Jaccard at least 0.9; `measure/e7_arbiter.py` rule, with candidates over all functions, not same-name). T1 is the primary truth.
  * **T2 provenance and time:** from the full git histories (`temporal-crucible-pool/doom-ports`), the first-appearance date of each function body (normalised-body digest) in its own repository's first-parent history. A copy `A -> B` requires `B`'s first appearance at or after `A`'s.
  * **T3 documented:** vendored or documented libraries (directory listings, READMEs, licence headers), e.g. `textscreen` (Chocolate), `blua` in `srb2` (Lua), recorded in a file **before** scoring.

## 3. Controls

* **Negative controls (no transfer is possible by construction):** pairs involving the from-scratch rewrites (`helion`, `rust-doom`, `room4doom`, `fsharp-doom`), the COBOL raycasters, and the unrelated C/C++ programs (`nginx`, `leveldb`, `curl`, `libuv`, `quake`, `quake2`; the same-studio pair excluded), crossed with DOOM ports; and cross-language pairs. Any predicted transfer here that T1 does not confirm is a false positive.
* **Positive control by construction (spike-in):** copy a module (about 50 functions, for example `textscreen`, and a Lua module) from a donor into a recipient repository that does not have it, with **graded disguise**: (a) verbatim; (b) functions renamed (all, 50%); (c) renamed plus comments stripped plus reformatted. Truth is known exactly. This also tests the "hide the copy by renaming" claim the owner raised.
* **Shuffled-label control:** the full analysis with port labels permuted across pairs, to give the chance level of the module-clustering and time checks.

## 4. Measurements

For each predictor and each eligible port pair: candidate pairs, **precision** and **recall** against T1 (recall measured over the T1 truth set), module clustering (directory plus call-graph connectivity, **after** matching, never used for matching), **false-positive count on the negative controls**, **spike-in recall by disguise level**, and for T1-confirmed transfers:
* **Order** (T2): share of transfers with donor first (borrower's first appearance at or after the donor's).
* **Import cluster** (T2): in the borrower, the transferred functions of one module appear within a short window (a vendoring commit); dispersion of first-appearance dates (share within 14 days of the median), compared with the same statistic for predicted pairs **not** confirmed by T1 and for shuffled-label pairs.
Counts, not just rates, are reported. The size of the T1 truth set is computed first (it needs neither predictor) and **recorded before predictors are scored**; if fewer than **30** T1 transfers exist in total, the experiment is declared underpowered for H9.2 and reported descriptively.

## 5. Hypotheses `[LOCK]`

* **H9.1 (precision):** against T1, the structure predictor's precision is at least 0.80 and exceeds the names predictor's precision, with the difference's paired bootstrap interval (over port pairs) above 0. Basis: E7 showed generic-name collisions inflate name matches.
* **H9.2 (recall on name-preserving transfers):** on verbatim T1 transfers, names recall is at least structure's recall (names keep names). Predicted *not* to hold on the renamed spike-ins: **structure recall at 50% and 100% renaming is at least 0.8 and at least twice the names recall**, which falls to its chance level.
* **H9.3 (negative controls):** structure has **0** false positives across the negative-control pairs; names has at least 1; the random predictor R1 has a false-positive count far above both (reported with its seed interval).
* **H9.4 (time validation):** among T1-confirmed transfers, at least **80%** have donor-first order, and the import-cluster statistic is higher for T1-confirmed than for unconfirmed or shuffled pairs (paired comparison, one-sided).
* **H9.5 (what structure finds that names miss):** there exist T1-confirmed transfers found by structure and not by names (renamed or re-prefixed), and the reverse (found by names and not structure, for example duplicated or translated code); both counts are reported, and each missed case is listed with its reason.
Primary endpoints, Holm-corrected: H9.1, H9.3, and the spike-in recall at 100% renaming. The rest are descriptive.

## 6. Limits and disclosure

* **Prior knowledge:** the `textscreen` transfers and the E7 Phase A tables are known; the direction of H9.1 to H9.3 is expected. The informative parts are the magnitudes, the precision comparison, the spike-in recall curve and the time checks. No E9 computation has been done.
* The older engine's results are not reused; the old thresholds are dropped.
* T1 uses text similarity, so a transfer that was **rewritten** (not copied) is invisible to T1 and counts as a miss for any predictor; T1 is therefore a floor on true transfers, and precision measured against T1 is a lower bound.
* A time order shows direction and clustering, not that a copy occurred; it is supporting evidence, reported next to T1, never replacing it.
* Duplicated functions inside a repo (E7: 99% of `puredoom`) defeat one-to-one matching; the primary analysis keeps duplicates as E7 does, with a de-duplicated sensitivity at equal standing.
* Shared-history families (Chocolate/Crispy/Inter, PrBoom+/dsda-doom, Woof/Nugget) are excluded as pairs and treated as one lineage when counting independent transfers.
* No third-party source is committed; spike-in recipients are scratch copies outside the repository.

## 7. Order of work

1. Reviews and amendment; fix the eligible-pair list, the T3 file, the negative-control list and the spike-in recipe; commit code and tests.
2. Compute the T1 truth set and T2 first-appearance data; record the truth-set size; commit.
3. Run the predictors (names, structure, R1, R2) and the controls; commit the output manifest.
4. Analysis and report.
