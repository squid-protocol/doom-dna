# `DOOM-E9` Amendment 2 (2026-11-22): registration record

**Registered 2026-11-22 20:03 EST by the commit that adds this file, before any E9 truth set or predictor was computed on the corpus.** Design: [E9_HORIZONTAL_TRANSFER.md](E9_HORIZONTAL_TRANSFER.md) and [Amendment 1](E9_AMENDMENT_1.md) (two independent reviews reconciled). Engine `704cb35f0`, sfs `bcd3cb7`, `spec_hash f5d525ed16bc91db`; E7's name key, stoplist and twin rules unchanged; the E8b progenitors are used as ancestors.

## Committed before computation

* Inputs: `manifest/e9_programs.csv` (clades, language groups, pins), `e9_t3.csv`, `e9_external_libs.csv`, `e9_spike_recipe.md`, `e9_clang_format.yaml` (`clang-format 18.1.8` from a separate virtual environment), the E7 pins and the E8b progenitor pins.
* Scripts with 61 passing tests: `measure/e9_truth.py` (near-copy truth, vertical mask, classification, first-appearance dates), `e9_predict.py` (names, structure, chance floor, trivial-geometry baseline), `e9_analyze.py`, `e9_spike.py`.
* **The spike-ins were built and scanned before registration** (outcome-blind: no predictor was run between a donor and a spiked recipient). Donors: `curl` (9 files of `lib/`, 162 eligible functions) and `libuv` (6 files of `src/unix/`, 106 eligible); recipient: scoped `chocolate-doom`; tiers a, b50, b100, c, d, e; the build checks and the exact renaming map are in `results/e9/pre/`.

## What the scripts do that the design left open (disclosed, fixed here)

* **Spike-in placement:** Chocolate's `.gitignore` excludes `lib`, so `curl`'s `lib/` is placed at `spike/curl/libsrc/`. Tier (e) is built on the verbatim-named text. The 20 libuv functions unmatched under tier (c) are 3 to 4 lines long and below the 6-line eligibility floor.
* **Truth builder:** one 128-permutation MinHash-LSH (32 bands of 4) over all 51 programs and the 6 progenitors; candidates never use names or paths; exact Jaccard on every candidate; pairs at representative level (de-duplicated); a T3 directed row takes precedence over the external-library list (`opl` is in both).
* **Engine mapping limit:** truth is computed on `ctags` functions and predictors run on the engine's function table; the match rate is 99% for C ports (chocolate-doom 99.8%) but **60% to 77% for C++ ports** (`woof`, `eternity`, `odamex`, `srb2`). **Recall is computed over truth functions that map to an engine row on both sides** and the match rates are reported per program, so C++ ports contribute fewer scored functions; this is a limitation, not a rule change.
* **Shallow histories:** `room4doom`, `lua`, `quake`, `quake2`, `leveldb` and `curl` have only shallow clones, so their first-appearance dates are marked censored (`shallow-history`); they are negative controls and donor sources, not time-test subjects.
* **Predictors:** structure is the union of both twin directions run on full repositories and filtered post hoc (the pre-masked order is a sensitivity); names use unique-key one-to-one pairs with the E7 decoy gate; R1 is the chance floor with budget `max(k_struct, k_names)` (floor 5); the trivial-geometry baseline is reciprocal nearest neighbours on loc, complexity and arguments. P1 counts as "structure higher" only if both the raw and the de-duplicated variants have an interval above 0.
* **Hand audit:** the two raters will be **model raters** (a Claude subagent and Gemini) working from a rubric fixed before the audit, which is a weaker substitute for human raters and is reported as such. The audit file is not yet created; P1 is reported without it until it exists.
* **Validation, all on known numbers:** the predictors reproduce E7's linuxdoom to chocolate-doom counts exactly (572 name matches, 385 twins, 233 exact clones); the truth builder's own tokenisation reproduces the arbiter shares for linuxdoom in chocolate-doom (0.434 exact+near, 0.663 with derived; E7 about 0.43 and 0.66); the LSH missed none of 455 pairs above Jaccard 0.6 on linuxdoom against chocolate-doom.

## Order from here

1. Run `e9_truth.py run` (outcome-blind). **Record the truth-set size (`truth_size.csv`: events, distinct modules, lineage pairs, functions) in a commit before any predictor is scored.**
2. Run the predictors (`eligible`, `controls`, `spike`), commit the output manifest hashes.
3. Run the model-rater hand audit on the sample; then `e9_analyze.py`.
Any later change to a registered rule needs a dated amendment.
