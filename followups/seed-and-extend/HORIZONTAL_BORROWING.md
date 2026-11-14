# Horizontal Borrowing Highlight: `textscreen` in `eternity` and `odamex`

In the original study ([teardown-of-doom.md](../../article/teardown-of-doom.md)), `eternity` (SMMU/MBF branch) and `odamex` (ZDoom branch) matched `chocolate-doom` / `doom-wasm` far more closely than `linuxdoom` because both horizontally borrowed Chocolate Doom's `textscreen` on-screen text UI library — a subsystem completely absent from `linuxdoom`.

Running unsupervised **Seed-and-Extend** (`alpha=0.5`, `eps=0.05`, 3-hop extension, zero names or file paths read) makes that horizontal gene transfer jump straight out of the raw call-graph coupling:

## Pairwise `textscreen` Recovery

| Pair | Tier-1 FGW Name Hits | `textscreen` Hits (Share of T1) | After 3-Hop SE Name Hits | `textscreen` Hits (SE) |
|---|---:|---:|---:|---:|
| **`eternity` ↔ `chocolate-doom`** | 276 | **210 (76.1%)** | 220 | **182** |
| **`eternity` ↔ `doom-wasm`** | 271 | **220 (81.2%)** | 217 | **187** |
| **`odamex` ↔ `chocolate-doom`** | 212 | **178 (84.0%)** | 152 | **136** |
| **`eternity` ↔ `odamex`** | 228 | **190 (83.3%)** | 186 | **166** |
| *Baseline:* `eternity` ↔ `linuxdoom` | 12 | 0 | 50 | 0 |
| *Baseline:* `odamex` ↔ `linuxdoom` | 6 | 0 | 39 | 0 |

## Concrete Recovered Examples (Blind to Names & Paths)

* **`eternity` ↔ `chocolate-doom`:**
  * Tier-1 FGW seeds: `TXT_NewCallbackTable` (`11L` ↔ `11L`), `convert_image` (`32L` ↔ `32L`), `FreeCallbackData` (`7L` ↔ `7L`), `TXT_PushClipArea` (`32L` ↔ `32L`), `TXT_UnrefCallbackTable` (`19L` ↔ `19L`).
  * Hop-1 call-graph extensions: `CalcRowColSizes` (`76L`, via `CalculateWidgetDimensions`), `TXT_DrawWindowFrame` (`59L`, via `TXT_BGColor`), `TXT_LabelDrawer` (`63L`, via `TXT_BGColor`), `TXT_DrawSeparator` (`44L`, via `TXT_GotoXY`), `TXT_InputBoxDrawer` (`58L`, via `TXT_BGColor`).
* **`odamex` ↔ `chocolate-doom`:**
  * Tier-1 FGW seeds: `TXT_NewCallbackTable`, `TXT_PushClipArea`, `TXT_UnrefCallbackTable`, `TXT_SignalConnect` (`23L` ↔ `23L`), `ExecReadOutput` (`85L` ↔ `90L`).
  * Hop-1 call-graph extensions: `TXT_InitTable` (via `TXT_AddWidget`), `CalcRowColSizes` (via `TXT_PageTable`), `TXT_TableDrawer` (via `TXT_DrawWidget`), `TXT_StringCopy` (via `TXT_SpinControlKeyPress`).
* **`eternity` ↔ `odamex` (cross-branch horizontal match):**
  * Two separate DOOM branches (SMMU/MBF vs. ZDoom) share **190** Tier-1 `textscreen` hits (`TXT_SpinControlDrawer`, `TXT_DrawWindowFrame`, `DrawHelpIndicator`, `TXT_DrawVertScrollbar` via `TXT_ScrollPaneDrawer`).
