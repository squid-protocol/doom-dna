# Cross-Pair Permutations & Expanded Permissive Controls

Follow-up to [FINDING.md](FINDING.md) testing:
1. **66 pairwise Seed-and-Extend permutations** (`alpha=0.5`, `eps=0.05`, 3-hop extension) across 12 repos: the novel / from-scratch / agentic COBOL DOOM cohort (`agentic-cobol-doom-cc`, `agentic-cobol-doom-codex`, `fps-cob`, `fsharp-doom`, `doomf77`, `cssdoom`, `sqldoom`, `rust-doom`), three DOOM anchors (`linuxdoom`, `doomgeneric`, `gore`), and `quake`.
2. **6 additional permissive-license controls** addressing language, engine-architecture, and graph-size confounds:
   - **Non-game COBOL (`carddemo-cobol-ctrl`)**: `COCRDLIC.cbl` + `COUSR00C.cbl` from `aws-mainframe-modernization-carddemo` (Apache-2.0, `n=55`, `edges=50`)
   - **C raycasters**: `KjetilIN/raycasting` (`c-raycasting`, MIT, `n=23`, `edges=22`) and `Kinyarasam/Raycasting-C` (`c-raycasting2`, MIT, `n=21`, `edges=17`)
   - **Go controls**: `garstas/goom3d` (Go Wolfenstein-style raycaster, MIT, `n=76`, `edges=67`) and `charmbracelet/bubbletea` (Go TUI framework, MIT, `n=675`, `edges=1,028`)
   - **Rust control**: `not-fl3/macroquad` (Rust game engine, Apache-2.0, `n=960`, `edges=2,015`)

---

## 1. Novel / From-Scratch / COBOL Cross-Pair Summary

| Category | Pair | Tier-1 Seeds (Name Hits) | After 3-Hop SE (Name Hits) | FGW Cost |
|---|---|---:|---:|---:|
| **True DOOM ports** | `linuxdoom` ↔ `doomgeneric` | 604 (**498**) | 611 (**362**) | **0.567** |
| | `gore` ↔ `doomgeneric` | 588 (**458**) | 725 (**432**) | **0.639** |
| | `linuxdoom` ↔ `gore` | 434 (**269**) | 508 (**229**) | **0.663** |
| **COBOL ↔ COBOL raycasters** | `agentic-cobol-doom-cc` ↔ `fps-cob` | 26 (1) | 27 (0) | **0.670** |
| | `agentic-cobol-doom-cc` ↔ `agentic-cobol-doom-codex` | 31 (0) | 19 (0) | **0.694** |
| | `fps-cob` ↔ `agentic-cobol-doom-codex` | 37 (0) | 41 (0) | **0.706** |
| **Novel ↔ `linuxdoom`** | `agentic-cobol-doom-cc` ↔ `linuxdoom` | 38 (0) | 40 (0) | 0.800 |
| | `agentic-cobol-doom-codex` ↔ `linuxdoom` | 94 (1: `main`) | 110 (1: `main`) | 0.754 |
| | `fps-cob` ↔ `linuxdoom` | 45 (0) | 49 (0) | 0.749 |
| | `rust-doom` ↔ `linuxdoom` | 150 (0) | 160 (0) | 0.802 |
| | `sqldoom` ↔ `linuxdoom` | 209 (2) | 191 (0) | 0.726 |
| | `doomf77` ↔ `linuxdoom` | 117 (0) | 120 (1) | 0.743 |
| | `fsharp-doom` ↔ `linuxdoom` | 34 (0) | 8 (0) | 0.891 |
| **Control** | `linuxdoom` ↔ `quake` | 395 (4) | 532 (3) | 0.710 |

* Every novel/from-scratch repo scores **0–1** accidental name hits against `linuxdoom`, `doomgeneric`, `gore`, `quake`, **and against every other novel repo**.
* The three COBOL raycasters (`agentic-cobol-doom-cc`, `agentic-cobol-doom-codex`, `fps-cob`) cluster at lower FGW transport cost (**`0.670–0.706`**) and align analogous raycaster roles without names (`MAIN-PARA ↔ MAIN ↔ main-section`, `READ-KEY ↔ POLL-INPUT`, `PUT-PIXEL ↔ set_color`, `DRAW-WORLD-WALL-SLICE ↔ draw_line`).

---

## 2. Expanded Permissive Controls

| Control Pair | Tier-1 Seeds (Hits) | After 3-Hop SE (Hits) | FGW Cost | Finding |
|---|---:|---:|---:|---|
| `agentic-cobol-doom-cc` ↔ `carddemo-cobol-ctrl` | 20 (1) | 16 (1) | **0.772** | Business COBOL of matching size (`n=55`) sits much higher than COBOL raycasters (`0.670–0.706`). |
| `fps-cob` ↔ `carddemo-cobol-ctrl` | 23 (0) | 32 (0) | **0.748** | Confirms COBOL raycaster clustering is architectural, not just COBOL syntax or small `n`. |
| `carddemo-cobol-ctrl` ↔ `agentic-cobol-doom-codex` | 29 (0) | 38 (0) | **0.763** | Zero cross-domain match. |
| `c-raycasting` / `c-raycasting2` ↔ `linuxdoom` | 23 (0) / 21 (0) | 19 (1) / 14 (1) | 0.781 / 0.769 | Small C SDL2 raycasters show 0–1 incidental hits vs. BSP `linuxdoom`. |
| `goom3d` (Go raycaster) ↔ `gore` | 64 (0) | 46 (0) | 0.721 | Same-language Go raycaster gets **0** hits against `gore` (vs. `gore ↔ linuxdoom` **229/508**, `0.663`). |
| `bubbletea` (Go) ↔ `gore` | 206 (1) | 302 (0) | 0.717 | Large Go codebase gets **0** hits against `gore` (`0.736` vs. `linuxdoom`). |
| `macroquad` (Rust) ↔ `linuxdoom` | 269 (0) | 367 (0) | 0.731 | Large Rust game engine gets **0** hits against `linuxdoom` (`1` vs. `gore`). |
| `rust-doom` ↔ `macroquad` | 223 (9) | 237 (1) | **0.681** | `rust-doom` sits closer to a Rust game engine (`0.681`) and `quake` (`0.668`) than to `linuxdoom` (`0.802`). |
