# Methods paper: notes (2026-11-25, not a draft of the paper)

**Working claim.** A name-blind, cross-language function matcher, evaluated on a family of DOOM ports with known lineage, is best described as a **two-route design with a gate**, not one method: fingerprints inside a language, call-graph seeds across languages, extension for reach. The evidence is a registered ladder (E12) at matched volume, graded against truth that no rung uses, with controls.

## 1. Architecture to describe
1. **Instrument.** Per-function measurements (37 features) and a call graph from the GitGalaxy engine (pinned at `704cb35f0` for the studies); no names, comments or text enter any matcher.
2. **Route A, fingerprint twins** (scanner `twins.py`): reciprocal best hit, ratio test, exact-clone bypass (loc >= 12), minimum 6 lines, target-decoy false-discovery control with the pooled multi-decoy cutoff (E7 Amendment 2, K = 25). Works inside a language and for Java.
3. **Route B, seeds** (`blind.py`, `seed-and-extend/measure.py`): fused Gromov-Wasserstein coupling over descriptors plus hop distances, reciprocal best hits, top 15% as seeds. Works across languages where call-graph shape survives (Go, Scheme, Dart).
4. **Route C, extension:** 3 rounds of neighbour voting from seeds, with an optional composition offset calibrated on the seeds. Buys reach, not accuracy; fills its quota on unrelated code.
5. **Gate** (coherence: strong-FGW share and mean neighbour support): the only thing that stops C from emitting on controls; descriptive thresholds, set after the fact.
6. **Truth apparatus** (none used by any matcher): name-blind text arbiter (E9: 4-token shingles with the function's own name masked; Jaccard 0.9 / 0.6; duplicate classes), normalised name key (a safe lower bound; confirmed 80 of 80 by blind raters, undercounts renamed ports), blind rater audit, unrelated-program controls, degree-preserving call-graph rewiring null.
7. **Analysis layer, not part of the matcher:** call-graph community discovery on `linuxdoom` (Louvain consensus, 16 groups) and the chance-adjusted wiring comparison. Report as a method with its limits (below), not as evidence of preserved architecture.

## 2. Evaluation design to describe (the part that is unusual)
* **Registration before scoring**, two independent design reviews (Claude + Gemini) reconciled in a dated amendment, results scored exactly as registered, failed predictions reported as failed. Studies E7 to E12 and amendments in `preregistration/`.
* **Matched volume.** Rungs emit very different numbers of pairs; compare at N = 50/100/250/500 and on full lists.
* **Controls at three levels:** decoy shuffles (inside the cutoff), unrelated programs (false pairs per 1,000), rewired graphs (what degrees and measurements alone produce).
* **Circularity discipline:** any step that uses call-graph edges, names or paths cannot also be the independent evidence for the same claim; state which pairs of methods are independent.

## 3. Results to carry (from E12; numbers in `results/e12/E12_REPORT.md`)
* Within a language, fingerprints beat extension at equal volume (8 well-covered programs, N = 250: 0.83 / 0.63 vs 0.60 / 0.48, precision / recall).
* Across languages: seeds and extension reach 0.91 (Go), 0.43 (Scheme), 0.59 to 0.75 (Dart) where fingerprints find nothing; fingerprints work for the Java port and the graph does not; no route works for the C# ports.
* The real call graph matters: rewiring drops graph-only matching 0.37 to 0.01 and extension 0.45 to 0.11; seeds 0.50 to 0.32.
* Calibration alone adds nothing; extension hops differ only beyond 250 pairs.

## 4. Negative and null results worth a section (they protect the claim)
* **Formatting is not the cause** of what moved (E10): normalising source did not change results.
* **Subsystem placement by measurement alone carries no subsystem signal** (E11 stage 3); names and paths recover discovered subsystems poorly (stage 4) so hand-written subsystems stay the better yardstick for the wiring chart.
* **Pooled cutoff** fixes share estimation but costs detection (E9p): choose the cutoff by the question.
* **Robust lens** (scanner branch `robust-lens`): no gain.

## 5. Limits to state plainly
Precision is a lower bound (unlisted homologs count as unmatched); thin text truth for 11 of 19 same-language programs; gate thresholds fit after the fact on the development port; programs above 10,000 functions not covered; single model rater for the audit; architecture preservation under translation is unmeasured.

## 6. Open items before a paper
Combined method (A then B) vs either alone, scored at matched volume; why the gate rejects the three most diverged C++ ports; whether the C# ports are matchable at all; a second independent rater set; a gate chosen on held-out programs.
