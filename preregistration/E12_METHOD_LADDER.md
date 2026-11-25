# DOOM-E12 (DRAFT, not registered): why match, then extend? A method ladder for function matching against `linuxdoom`

**Status: DRAFT 2026-11-25. Becomes REGISTERED when two independent design reviews are reconciled in a dated section and this file is committed before any matching or scoring.** Engine `704cb35f0`, scanner `b1a9e92`.

## Why this experiment
The Seed-and-Extend method (fingerprints, then reciprocal matching of precise seeds, then extension along the call graph) came from a chain of follow-ups in `followups/`: name-blind fingerprint twins work within a language (`chocolate-doom` 420 twins at 90.5% name agreement) and find **nothing across languages** (0 twins for Go, Scheme, Dart); fixing the language offset (composition lens, rank normalisation, calibrating the shift) gave small gains (Go placement 60.3 to 62.2%, 1-to-1 recall 10.8 to 17.8%); seeding anchors and following call-graph neighbours one hop gave large gains on a favourable anchor set (Go 59.9%, Java 65%); the production method then recovered 67 to 95% in same-language ports and 76.6% of Go, with unrelated programs at 0 to 0.8%. **What was never done is the whole ladder on one footing:** the same ports, the same one-to-one matching, the same scoring, rung by rung, with a fingerprint threshold sweep and a call-graph-only baseline, graded against truth that no rung uses. This experiment does that, so the three-step design is justified (or not) by one table.

## Question
For function matching against `linuxdoom`, what does each ingredient add, and where does each rung stop working: **fingerprints alone**, **plus cross-language normalisation**, **plus offset calibration**, **call-graph shape alone**, **seeds**, **seeds plus extension**?

## Design
* **Rungs** (every rung outputs a strict one-to-one set of pairs, port function to `linuxdoom` function, ranked by confidence):
  * **L0 fingerprints alone:** E7's structure-lens twins, pooled K = 25 cutoff (E7 Amendment 2), either direction, with a **threshold sweep**: FDR in {0.001, 0.01, 0.05, 0.10} and ratio in {0.7, 0.8, 0.9, off}. The headline row is E7's registered setting (0.01, 0.8), fixed before any result; the grid is descriptive.
  * **L1 cross-language fingerprints:** portable lens, composition keyword mode, within-repository rank normalisation, same sweep.
  * **L2 offset calibration:** L1 with the language offset (median composition difference over the L1 twins as anchors) subtracted from the port, re-matched.
  * **L3 call-graph shape alone:** descriptors are the nine call-graph roles only (no measurement features), optimal-transport coupling, reciprocal best hits.
  * **L4 seeds:** fused Gromov-Wasserstein (descriptors plus call-graph hop distances, no names), reciprocal best hits, the top 15% by coupling mass (the published Tier-1 rule).
  * **L5 seeds plus calibration gate:** all reciprocal FGW hits kept only where the calibrated composition cosine is at least 0.70 and the size ratio at least 0.20 (the published gate), no graph extension.
  * **L6 seeds plus extension:** the published method, extension of 1, 2 and 3 hops (separate rows), seeds and offset as in L4 and L5.
  The matcher code is the published `followups/seed-and-extend/measure.py` and the figure builder's gates, ported to the current engine; no hyperparameter is tuned.
* **Programs:** same-language (SL): `chocolate-doom`, `doomgeneric`, `sdl-doom`, `doom-ascii`, `doom-wasm`, `puredoom`, `mood`, `fastdoom`, `doom-ios`, `prboom-plus`, `woof`. Translations (T): `gore`, `doom-scheme`, `dartdoom`, `mochadoom`, `managed-doom`, `kocoa-doom`. Controls (K): `lua`, `quake`, `quake2`, `room4doom`, `rust-doom`, `nginx`. Programs above 10,000 functions are omitted (dense `n x n` hop matrices). `chocolate-doom` is the **development** port (only it may be used to look at behaviour before predictions are scored; no setting is chosen from it).
* **Truth, none of it used by any rung:** for SL programs the **name-blind text arbiter** pairs from E9 (`truth/pairs.csv`, pairs against `linuxdoom`: 4-token shingles with the function's own name masked, Jaccard at least 0.9 = near copy, at least 0.6 = derived), mapped to engine rows; for T programs, where text truth does not exist, **normalised function-name agreement** (the E7 name key), a noisy key reported separately and never pooled with the text truth; for K programs every pair is false by construction.
* **Metrics, per rung and program:** pairs emitted; precision (against the text truth for SL, the name key for T); recall (SL only: share of truth near-copy pairs recovered) and the recall at the precision of 0.9 where reached; for K programs the **false pairs per 1,000 functions**; the same on a **permutation floor** (the `linuxdoom` side shuffled, so name hits and text hits expected by chance are reported); bootstrap 95% intervals over functions. Rung-to-rung differences are reported as paired differences on the same functions.
* **No gate by default:** the method's coherence gate (the figure builder's `strong_fgw` and `mean_sup`) is **reported as a separate descriptive row** (L7), with its post hoc thresholds flagged, because the published numbers show the extension step emits about 500 pairs for every program, controls included.

## Predictions (before any matching)
* **P1 (primary, within language):** on the SL programs, L0 at the E7 setting has precision at least 0.90 (against the text truth), and L6 (3 hops) raises recall over L0 by at least 0.15 on at least 6 of the 11 programs while keeping precision at least 0.75.
* **P2 (primary, across languages):** on `gore`, `doom-scheme` and `dartdoom`, L0 and L1 recover fewer than 5% of functions (name key); `gore` under L6 recovers at least 40%.
* **P3 (primary, graph alone is not enough):** L3 (call-graph shape alone) has precision at least 0.30 below L4 (seeds) on at least 8 of the 11 SL programs.
* **P4:** offset calibration alone (L2 minus L1) adds under 10 percentage points of recovered functions on every T program.
* **P5:** extension helps and costs: recall rises monotonically with hops 1 to 3 on SL programs, with precision falling by at most 0.15 absolute from 1 to 3 hops.
* **P6 (primary, controls):** L0 to L3 emit at most 1 false pair per 1,000 functions on the K programs; L4 to L6 are reported as they are (expected high: the extension emits pairs regardless).
* **P7:** the headline ordering of rungs (L0 low across languages, L6 highest recovered functions, L3 least precise) is the same under the E7 text truth and under the name key for the SL programs.
A failed prediction is reported as failed.

## Limits
Translation truth is the function-name key, which is noisy in both directions and cannot grade a port that renamed everything; results for translations are therefore a lower bound on correct matches and are never mixed with the text truth. The study is on one family of programs. The published method's gate thresholds were set after the fact. Third-party source is not committed.
