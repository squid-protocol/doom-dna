# Preregistered Follow-Up Experiments (`doom-dna`)

These experiments close the open questions documented in `RESULTS.md` and `article/teardown-of-doom.md`.

## `DOOM-E1`: Tiny-Function Collapse for OOP Translations
* **Question:** Did `mochadoom` (Java), `kocoa-doom` (Kotlin), and `managed-doom` (C#) actually lose `linuxdoom`'s subsystem wiring, or did decomposing code into `<= 3`-line methods (34–43% vs. `< 2%` in C) hide the wiring and blow up unsmoothed `hits / loc` density?
* **Intervention:** Inline/collapse single-caller or `loc <= 5` leaf/wrapper functions in the call graph prior to `sfs subway` and `blind_placement`.
* **Prediction:** Cross-wiring over null (`over_null`) and blind-placement `κ` increase by `>= +0.10` on `mochadoom` and `kocoa-doom` when collapsed, without inflating unrelated controls (`room4doom`, `helion`, `Lua`).

## `DOOM-E2`: Composition + 1-Hop Neighborhood for Cross-Language Alignment
* **Question:** Can cross-language function matching (`linuxdoom` ↔ `gore`, `dartdoom`, `doom-scheme`) move above language-family clustering?
* **Intervention:** Replace `density` with `composition` (`hits_i / sum(hits)`) combined with 1-hop call-graph degree/fan-out features (`docs/KEYWORD_MODES.md` §4).
* **Prediction:** Within-subsystem nearest-neighbor agreement across C ↔ Go and C ↔ Scheme improves over `portable` density (`> 0.60` on `gore`).

## `DOOM-E3`: Explicit `other %` Coverage Gate in `subway`
* **Question:** How much of low `over_null` scores comes from directory-based `subsystems.json` dumping renamed files into `other %`?
* **Rule:** Any port with `other % > 20%` under default `subsystems.json` must be flagged `low_taxonomy_coverage` and excluded from "lost wiring" claims unless a per-port taxonomy override is supplied.

## `DOOM-E4`: Graph-Shape Distance Null Calibration
* **Question:** Why did raw `graph-shape distance` overlap between DOOM ports (`0.30–3.25`) and unrelated controls (`1.04–2.30`)?
* **Intervention:** Evaluate size-matched random-rewiring nulls (degree-preserving Maslov-Sneppen swaps) rather than raw Euclidean distance over global graph summary stats.
