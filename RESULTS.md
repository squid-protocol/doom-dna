# DOOM's DNA: Consolidated Results & Open Questions

All measurements below come from pinned GitGalaxy engine `6c7c6c1bc` across the **44 licensed ports** in `manifest/manifest.csv` plus 3 unrelated C controls (WinQuake, Quake II, Lua).

## 1. Established Conclusions

* **Within-language structural twins (`sfs twins`):**
  * **93% precision**, **65% recall** across 27,778 function-by-port pairs against source-text diffs (`measure/lineage.py`).
  * Rank correlation of port twin survival vs. source-text survival: **Spearman ρ = 0.83** (`n = 43`; **0.84** in `article/teardown-of-doom.md`).
  * Unrelated C controls: `0%–0.6%` (`0–8` twins vs. `403` for `chocolate-doom`); `Quake ↔ Quake II` shares `12.7%`.
* **Horizontal library sharing (lateral transfer):**
  * `eternity` and `odamex` match `doom-wasm` through ~200 `textscreen` UI library twins (`TXT_ButtonDrawer`, etc.) absent from `linuxdoom`.
* **Cross-subsystem wiring above chance (`sfs subway --reference linuxdoom`):**
  * `doom-scheme` (`+0.51`) and `gore` (`+0.50`) match `chocolate-doom` (`+0.51`) in cross-subsystem wiring above a degree-preserving shuffled null.
  * `dartdoom` retains `+0.19`; `doomf77` (`+0.05`), `mochadoom` (`+0.01`), `kocoa-doom` (`-0.08`), `managed-doom` (`-0.15`), and from-scratch engines (`-0.08` to `+0.06`) sit near or below chance.
* **Blind placement (`results/blind_placement.md`):**
  * With names and paths hidden: `gore` 60% (`κ = 0.50` vs. 20% chance; 99% on top-quartile confidence), `dartdoom` 48% (`κ = 0.31`), `doom-scheme` 46% (`κ = 0.26`).
  * Rewiring `gore`'s call graph while keeping degree drops accuracy from 60% to 39%.

## 2. Known Limitations & Open Questions

1. **Tiny-function OOP distortion:** 34% of `mochadoom` (Java) and 43% of `kocoa-doom` (Kotlin) functions are `<= 3` LOC (vs. `< 2%` in C), distorting unsmoothed `hits/loc` density. Tracked in `preregistration/EXPERIMENTS.md` (`DOOM-E1`) and standardized in `docs/KEYWORD_MODES.md`.
2. **Blind wiring circularity:** Computing wiring *after* blind placement imposes `linuxdoom`'s shape on unrelated engines (`0.33–0.64`); only blind-placement *agreement* with name/path placement is valid evidence.
3. **Cross-language function twins:** Current `portable` density still clusters by language family rather than ancestry (`DOOM-E2`).
4. **Directory taxonomy coverage:** Default `manifest/subsystems.json` maps by file name/directory, inflating `other %` on reorganized ports (`DOOM-E3`).
5. **Graph-shape distance:** Raw graph-shape distance (`0.30–3.25` for DOOM vs. `1.04–2.30` for controls) does not separate lineage (`DOOM-E4`).
