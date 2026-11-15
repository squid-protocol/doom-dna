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

## `DOOM-E5`: Held-Out Cross-Language Port vs. From-Scratch Predictions (Preregistered Prior to Cloning)
* **Question:** Can unsupervised Seed-and-Extend + `horizontal_transfers.py` accurately predict whether newly sampled permissive DOOM repositories are true `linuxdoom` source ports (even across Rust/Python) vs. from-scratch engines, and identify their exact parent port without reading identifiers?
* **Held-Out Targets (selected by GitHub metadata/license only, not yet cloned or scanned):**
  1. `Henrique194/iron-doom` (GPL-3.0, Rust — described as a Doom source port written in Rust)
  2. `wojciech-graj/cydoomgeneric` (GPL-2.0, C/Python — Python bindings for `doomgeneric`)
  3. `LinusCDE/doomarkable` (GPL-2.0, C/C++ — DOOM on reMarkable)
  4. `StanislavPetrovV/DOOM-style-Game` (MIT, Python — Pygame DOOM-style raycaster)
  5. `Patryk27/doome` (MIT, Rust — *"Doom + Cliché = Doomé"*)
* **Predictions:**
  * **H5.1 (`iron-doom`):** True Rust port of DOOM's call graph — Seed-and-Extend against `linuxdoom` recovers **`>= 25%` 1-to-1 name precision** (vs. `0.0%` for from-scratch `rust-doom` and `macroquad`).
  * **H5.2 (`cydoomgeneric`):** Wraps `doomgeneric` — recovers **`>= 70%` against `linuxdoom`** and **`>= 80%` against `doomgeneric`**, with `horizontal_transfers.py` identifying `doomgeneric` (not `linuxdoom` directly) as its closest parent.
  * **H5.3 (`doomarkable`):** GPL-2.0 port — recovers **`>= 50%` against `linuxdoom`** and reveals its exact upstream parent (`doomgeneric`, `chocolate-doom`, or `prboom-plus`).
  * **H5.4 (`DOOM-style-Game`):** From-scratch Python raycaster — scores **`<= 2%` name precision** against `linuxdoom` (`0–1` accidental hits).
  * **H5.5 (`doome`):** MIT-licensed (non-GPL) Rust project — predicted to be a from-scratch / inspired engine (**`<= 2%` name precision** against `linuxdoom`).

## `DOOM-E6`: Partial-Engine Hybrids, Genre Shifts & Studio Rewrites (Preregistered Prior to Cloning/Scanning)
* **Question:** When a different game or engine takes *parts* of DOOM (`id Tech 1`) and expands or rewrites them—across genres (`SRB2`), console/RPG expansions (`Doom64EX`, Heretic/Hexen), or studio-internal engine rewrites (`dhewm3`, pure id Tech 4 without DOOM Classic)—can Seed-and-Extend localize the surviving DOOM core vs. newly written subsystems, and separate id Tech 1 hybrids from id Tech 4?
* **Held-Out Targets:**
  1. `dhewm/dhewm3` (GPL-3.0, C++ — Doom 3 / id Tech 4 engine without DOOM Classic)
  2. `STJr/SRB2` (GPL-2.0, C — Sonic Robo Blast 2, 3D platformer built on Doom Legacy)
  3. `svkaiser/Doom64EX` (GPL-2.0, C — DOOM 64 engine built on DOOM / id Tech 1)
  4. Heretic / Hexen (`chocolate-doom/src/heretic` & `src/hexen` or `hheretic`, GPL-2.0, C)
* **Predictions:**
  * **H6.1 (`dhewm3`):** Pure id Tech 4 rewrite without DOOM Classic scores **`<= 2%` 1-to-1 name precision** against `linuxdoom` (contrasting with `doom3-bfg` at `38.1%`).
  * **H6.2 (`SRB2`):** Despite being a 3D Sonic platformer, Seed-and-Extend against `linuxdoom` recovers **`>= 25%` 1-to-1 name precision**, concentrated in core `z_zone` / `w_wad` / `r_bsp` / `p_map` routines.
  * **H6.3 (`Doom64EX`):** Recovers **`>= 40%` 1-to-1 name precision** against `linuxdoom`, with core engine retention and N64 rendering/scripting divergence.
  * **H6.4 (Heretic / Hexen):** Recovers **`>= 50%` 1-to-1 name precision** against `linuxdoom`, with higher retention in `z_zone` / `w_wad` / `r_bsp` than in `p_enemy` / `g_game`.
