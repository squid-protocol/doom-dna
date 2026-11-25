# DOOM-E12: why match, then extend? What the method ladder shows

Run 2026-11-25 (US Eastern). Design registered before any scoring (commit 4a5b9b1, `preregistration/E12_METHOD_LADDER.md`); table `results/e12/e12_table.csv` (32,231 rows, 35 programs); generated tables `results/e12/E12_RESULTS.md`; blind audit `results/e12/audit/`. This report is hand-written from those files.

## The answer in four lines
1. **Within one language, fingerprints alone beat the extension.** At the same number of emitted pairs, plain fingerprint twins are more precise and recover more functions than the seed-and-extend method. Prediction P1b (extension adds recall) **failed**.
2. **Across languages the picture reverses, but only for some languages.** Fingerprints find nothing for Go, Scheme and Dart; seeds plus extension match 91% (Go), 43% (Scheme) and 59% to 75% (Dart) of the pairs at 250. Neither method finds the C# ports. For the Java port (mochadoom) fingerprints work (72% to 90% precision on 29 to 46 pairs) and the graph methods fail (4%).
3. **The call graph carries real signal, and the extension depends on it.** Shuffling the call graph (keeping each function's number of calls) drops call-graph-only matching from 0.37 to 0.01 precision and extension from 0.45 to 0.11. The seeds hold up better (0.50 to 0.32), so they lean partly on the per-function measurements.
4. **Extension emits pairs whether or not there is anything to find.** On every control program it fills its quota (100 of 100). The coherence gate is what stops it, and the gate rejected all five controls but also three genuinely diverged same-language ports.

## Prediction scorecard (scored exactly as registered; `chocolate-doom` not counted)
| | Prediction | Result |
|---|---|---|
| P1a | F0 (fingerprints, E7 setting) precision >= 0.90 on >= 15 of 19 same-language programs | **FAILED**: 1 of 19 (median 0.41). See caveat A. |
| P1b | E3c recall exceeds F0's by >= 0.05 at N=250 with precision >= 0.75 on >= 10 of 19 | **FAILED**: 0 of 19; median change **-0.13** (fingerprints recover more). |
| P2 | Fingerprints emit < 5% of functions on gore, doom-scheme, dartdoom; E3c reaches >= 0.50 on gore | **PASSED** (known beforehand): 0% to 0.7%; gore 0.91. |
| P3 | Call graph alone is >= 0.30 less precise than fused at N=100 on >= 14 of 19 | **FAILED**: 0 of 19; median gap only 0.05. |
| P4 | Calibration adds < 0.05 on >= 5 of 6 translations | **PASSED**, vacuously: calibrated and uncalibrated extension are almost identical. |
| P5 | Precision falls <= 0.15 from 1 to 3 hops at N=250 on >= 14 of 19 | **PASSED, but uninformative**: E1, E2, E3 are identical in their first 250 pairs. They differ only past 250 (recall at 500: 0.46 for 1 hop, 0.60 for 3). |
| P6 | Extension emits >= 90 on every hard control at N=100; the gate rejects all 5 controls and accepts >= 17 of 19 | **FAILED**: seeds emit only 27 to 73, and rust-doom 1-hop emits 71; the gate rejected 5 of 5 controls but accepted only **16 of 19** (rejected eternity, odamex, edge-classic). |
| P7 | Rung ordering the same under two truths (Kendall tau >= 0.8) | **FAILED**: tau = 0.48. |
New ones (P1b, P3, P5, P6 gate half, P7): four of five failed or were vacuous. The ones that restated known results (P2, P4) passed.

## Where each rung stands (mean over the 8 same-language programs with a large truth, N=250, precision / recall) — post hoc, see caveat B
| rung | precision / recall |
|---|---|
| F0 fingerprints | **0.83 / 0.63** |
| F1c fingerprints + cross-language steps | 0.83 / 0.57 |
| G0 measurements only | 0.45 / 0.31 |
| G1 call graph only | 0.51 / 0.36 |
| G2 fused | 0.62 / 0.48 |
| S seeds (about 90 pairs) | 0.65 / 0.19 |
| E3c seeds + 3 hops + calibration | 0.60 / 0.48 |
Reading it: each added ingredient helps the *graph* family (measurements only, then graph only, then fused, then seeds as a precise subset), but none reaches what fingerprints achieve inside a language. The extension adds no precision or recall over the fused list at N=250; its value is reaching further down the list at 500 and beyond, with falling precision.

## Fingerprint thresholds (descriptive sweep, all 19 programs, full lists)
Loosening the cutoff from FDR 0.001 to 0.10 adds about 12% more true pairs (2,288 to 2,564) and more than triples the unconfirmed ones (567 to 1,782). The tightest settings are the most precise; the registered setting (0.01, ratio 0.8) sits in the middle. The ratio test matters little. This is a descriptive grid, no setting was selected from it.

## Translations (blind audit)
Forty emitted pairs per translation were drawn at random from E3c at N=250 and rated by an independent model reader that saw only the two functions' code (no method labels, no answer key). Function names are visible inside code, so this checks the name key but is not name-free.
| program | name-key precision at 250 | rater: same or similar (sample of 40) | key-true pairs rated ok | key-false pairs rated ok |
|---|---|---|---|---|
| gore (Go) | 0.91 | 37 of 40 | 37 of 37 | 0 of 3 |
| doom-scheme | 0.43 | 17 of 40 | 16 of 16 | 1 of 24 |
| dartdoom | 0.59 | 30 of 40 | 26 of 26 | 4 of 14 |
| mochadoom (Java) | 0.04 | 7 of 40 | 1 of 1 | 6 of 39 |
The name key is a **safe lower bound**: every pair it counts was confirmed (80 of 80). It undercounts ports that renamed functions: dartdoom's true rate is about 0.75 not 0.65, mochadoom's about 0.18 not 0.03. The audit sample is small; the rater is a model, not a person.

## What this says about the three-step method
* **Step 1 (fingerprints) is the right first tool inside a language and for Java**, where it is both precise and fast. It is blind to Go, Scheme, Dart, C#.
* **Step 2 (reciprocal graph-and-measurement seeds) is the right tool across languages** where the call-graph shape survives (Go, Scheme, Dart): 0.52 to 0.96 precision on 40 to 70 pairs.
* **Step 3 (extension) buys reach, not accuracy**: more pairs per program, at falling precision, and only with the real call graph. It needs the coherence gate to avoid emitting pairs on unrelated programs.
* Neither covers the C# ports (kocoa-doom, managed-doom: about 0). Whatever transfers there is not captured by either route.

## Caveats and departures from the registration
**A. Precision is a lower bound.** The registration said unlabelled pairs are never counted false. The text-truth table lists only pairs above Jaccard 0.6, so a pair that is a true homolog below that is indistinguishable from a wrong one, and the code counts it as false. That affects every same-language precision here, hardest on the 11 programs whose truth lists fewer than 100 functions (`doomretro` 2, `eternity` 3, `odamex` 9, `srb2` 9, `woof` 21, `nugget-doom` 26, `dsda-doom` 26, and so on). P1a and P1b are therefore close to uninformative for those programs and I registered them anyway; the reviewers had warned the truth was thin for woof and prboom-plus, and I added more diverged ports without raising that.
**B. The 8-program subset is post hoc** (programs with a text truth of at least 100 functions: doomgeneric, sdl-doom, doom-ascii, doom-wasm, puredoom, mood, crispy-doom, inter-doom). It was chosen after seeing the table because the other eleven cannot support a precision statement. The registered scorecard above is on all 19.
**C. Smaller departures:** seeds were scored on the top 15% fixed by the published rule; the audit was a single model rater, not several; the rewiring null used 10 draws on programs of at most 3,000 functions (the real-graph comparison is restricted to the same programs); dartdoom's summary line disagreed with its own 40 ratings by one pair and the per-pair ratings were used; the sweep shows the registered N=250 view flat because truncation hides the cutoff, so the sweep above uses full lists.
**D. Development port:** chocolate-doom is excluded from every count; its F0 reaches 0.86 / 0.72 at N=250, G2 0.58 / 0.49, S 0.65 / 0.21.
**E. Gate:** the gate accepted managed-doom (mean support 2.22) although its pairs score about 0.003; it is a coherence check, not a correctness check.
**F. Scope:** programs over 10,000 functions (gzdoom, doomsday, doom3-bfg) are not covered; no architecture or wiring claim is made.

## What is left
Nothing in the registration is unfinished. Open questions this raises: whether a combined method (fingerprints first, graph seeds for what fingerprints miss) beats either route; whether the C# ports can be matched at all; and why the gate fails the three most diverged C++ ports.
