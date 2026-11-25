# DOOM-E11 stage 4 results: wiring against chance on the discovered subsystems

Registered design: [stage 4](../../preregistration/E11_SUBSYSTEMS_STAGE4.md). Placement by twin, name and file path (not blind). Full table: `stage4_table.csv`; recovery: `stage4_recovery.csv`.

## References and placement rules (read before any gap)

| arm | reference diagonal share | wiring floor | held-out recovery (80/20) | coverage of held-out | stem and prefix reproduce labels |
|---|---|---|---|---|---|
| D | 0.84 | 0.63 | 0.67 | 1.00 | 0.71 |
| H1 | 0.54 | 0.46 | 0.96 | 1.00 | 1.00 |

## Arm D (discovered subsystems, resolution 1.0), all placements

Cross-wiring against chance. 'File null' is the size-stratified profile swap (undefined with fewer than 30 placed files or one file over 25%). Standardised gap = (real - null mean) / null SD.

| program | grp | placed (cov) | twin/name/path | files | cross calls | cross [95% CI] | function null mean (97.5th) | file null mean (97.5th) | z function | z file | above file/function 97.5th | non-twin: above function 97.5th |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chocolate-doom | C | 1310 (0.53) | 370/281/659 | 97 | 599 | 0.74 [0.68, 0.77] | 0.65 (0.70) | 0.63 (0.72) | 3.3 | 2.0 | **yes** (file) | not scored |
| crispy-doom | C | 1640 (0.58) | 248/412/980 | 112 | 1109 | 0.71 [0.67, 0.73] | 0.63 (0.68) | 0.62 (0.71) | 2.9 | 1.7 | no (file) | no |
| doomgeneric | C | 1061 (0.89) | 389/247/425 | 74 | 399 | not scored: low-count (descriptive) | | | | | | | |
| sdl-doom | C | 1034 (0.96) | 388/247/399 | 72 | 402 | not scored: low-count (descriptive) | | | | | | | |
| doom-ascii | C | 970 (0.95) | 379/257/334 | 72 | 387 | not scored: low-count (descriptive) | | | | | | | |
| doom-wasm | C | 1215 (0.60) | 365/277/573 | 91 | 555 | 0.77 [0.72, 0.80] | 0.66 (0.71) | 0.64 (0.73) | 4.1 | 2.7 | **yes** (file) | not scored |
| mood | M | 1494 (0.80) | 627/761/106 | 125 | 546 | 0.99 [0.95, 0.98] | 0.66 (0.71) | 0.65 (0.73) | 13.7 | 8.2 | **yes** (file) | not scored |
| prboom-plus | M | 1608 (0.66) | 88/566/954 | 101 | 978 | 0.72 [0.67, 0.74] | 0.66 (0.70) | 0.61 (0.72) | 2.4 | 2.0 | no (file) | **yes** |
| woof | M | 2482 (0.66) | 54/536/1892 | 145 | 2351 | 0.56 [0.53, 0.58] | 0.59 (0.64) | 0.55 (0.64) | -1.7 | 0.2 | no (file) | no |
| dsda-doom | M | 2458 (0.55) | 80/544/1834 | 92 | 1767 | 0.62 [0.57, 0.65] | 0.64 (0.69) | 0.50 (0.62) | -1.2 | 1.8 | no (file) | no |
| inter-doom | M | 1696 (0.55) | 105/479/1112 | 111 | 863 | 0.81 [0.77, 0.83] | 0.65 (0.69) | 0.64 (0.73) | 7.1 | 3.0 | **yes** (file) | **yes** |
| fastdoom | M | 1078 (0.51) | 162/439/477 | 93 | 534 | 0.64 [0.58, 0.67] | 0.60 (0.66) | 0.57 (0.71) | 1.2 | 1.0 | no (file) | not scored |
| doom-ios | M | 1067 (0.60) | 103/493/471 | 75 | 579 | 0.70 [0.63, 0.73] | 0.67 (0.73) | 0.62 (0.73) | 0.9 | 1.4 | no (file) | not scored |
| eternity | M | 3693 (0.56) | 0/544/3149 | 227 | 2567 | 0.59 [0.56, 0.61] | 0.66 (0.69) | 0.65 (0.73) | -4.7 | -1.5 | no (file) | no |
| odamex | M | 4345 (0.56) | 1/617/3727 | 224 | 3432 | 0.61 [0.58, 0.62] | 0.55 (0.58) | 0.54 (0.63) | 3.6 | 1.5 | no (file) | **yes** |
| srb2 | M | 4099 (0.60) | 47/464/3588 | 136 | 4183 | 0.74 [0.71, 0.76] | 0.63 (0.67) | 0.50 (0.60) | 5.5 | 4.5 | **yes** (file) | **yes** |
| puredoom | M | 1364 (0.88) | 361/945/58 | 58 | 500 | 0.98 [0.93, 0.97] | 0.66 (0.70) | n/a (n/a) | 13.0 | n/a | **yes** (function (weaker)) | not scored |
| nugget-doom | M | 2830 (0.68) | 48/541/2241 | 145 | 2867 | 0.62 [0.60, 0.65] | 0.60 (0.65) | 0.57 (0.66) | 0.9 | 1.1 | no (file) | no |
| doomretro | M | 1801 (0.81) | 10/505/1286 | 80 | 2130 | 0.75 [0.72, 0.77] | 0.63 (0.68) | 0.59 (0.71) | 5.1 | 2.6 | **yes** (file) | **yes** |
| gzdoom | M | 5521 (0.30) | 12/406/5103 | 318 | 2353 | 0.47 [0.45, 0.49] | 0.49 (0.52) | 0.50 (0.57) | -2.2 | -0.7 | no (file) | no |
| doomsday | M | 1658 (0.08) | 14/408/1236 | 157 | 783 | 0.45 [0.42, 0.48] | 0.40 (0.44) | 0.41 (0.48) | 2.5 | 1.2 | no (file) | **yes** |
| edge-classic | M | 1942 (0.38) | 2/139/1801 | 107 | 1470 | 0.57 [0.55, 0.59] | 0.55 (0.62) | 0.48 (0.62) | 0.7 | 1.3 | no (file) | no |
| doom3do | M | 223 (0.44) | 22/201/0 | 44 | 51 | not scored: not scored (placed 223, cross calls 51, populated 10) | | | | | | | |
| doom3-bfg | M | 804 (0.80) | 42/628/134 | 64 | 318 | not scored: low-count (descriptive) | | | | | | | |
| gore | T | 599 (0.60) | 0/599/0 | 7 | 169 | not scored: low-count (descriptive) | | | | | | | |
| doom-scheme | T | 621 (0.78) | 0/452/169 | 64 | 174 | not scored: low-count (descriptive) | | | | | | | |
| dartdoom | T | 527 (0.73) | 4/392/131 | 43 | 169 | not scored: low-count (descriptive) | | | | | | | |
| managed-doom | T | 341 (0.27) | 3/338/0 | 53 | 32 | not scored: not scored (placed 341, cross calls 32, populated 9) | | | | | | | |
| mochadoom | T | 877 (0.29) | 44/732/101 | 148 | 103 | not scored: low-count (descriptive) | | | | | | | |
| kocoa-doom | T | 792 (0.27) | 0/730/62 | 144 | 90 | not scored: not scored (placed 792, cross calls 90, populated 14) | | | | | | | |
| doomf77 | T | 146 (1.00) | 0/4/142 | 13 | 135 | not scored: low-count (descriptive) | | | | | | | |
| doo-cr | T | 1303 (0.88) | 5/1204/94 | 25 | 15 | not scored: not scored (placed 1303, cross calls 15, populated 13) | | | | | | | |
| helion | R | 163 (0.02) | 16/132/15 | 53 | 2 | not scored: not scored (placed 163, cross calls 2, populated 10) | | | | | | | |
| rust-doom | R | 14 (0.02) | 0/4/10 | 5 | 0 | not scored: not scored (placed 14, cross calls 0, populated 1) | | | | | | | |
| room4doom | R | 296 (0.06) | 3/264/29 | 62 | 37 | not scored: not scored (placed 296, cross calls 37, populated 10) | | | | | | | |
| cssdoom | R | 4 (0.02) | 0/4/0 | 3 | 0 | not scored: not scored (placed 4, cross calls 0, populated 1) | | | | | | | |
| fsharp-doom | R | 7 (0.15) | 0/7/0 | 1 | 0 | not scored: not scored (placed 7, cross calls 0, populated 1) | | | | | | | |
| doom-fx | R | no call graph or no scan | | | | | | | |
| sqldoom | R | 10 (0.02) | 0/10/0 | 9 | 0 | not scored: not scored (placed 10, cross calls 0, populated 1) | | | | | | | |
| agentic-cobol-doom-cc | K | 1 (0.02) | 0/1/0 | 1 | 0 | not scored: not scored (placed 1, cross calls 0, populated 0) | | | | | | | |
| agentic-cobol-doom-codex | K | 1 (0.01) | 0/1/0 | 1 | 0 | not scored: not scored (placed 1, cross calls 0, populated 0) | | | | | | | |
| fps-cob | K | 2 (0.04) | 0/2/0 | 1 | 0 | not scored: not scored (placed 2, cross calls 0, populated 0) | | | | | | | |
| c-raycasting | K | 2 (0.09) | 0/2/0 | 1 | 0 | not scored: not scored (placed 2, cross calls 0, populated 0) | | | | | | | |
| c-raycasting2 | K | 1 (0.05) | 0/1/0 | 1 | 0 | not scored: not scored (placed 1, cross calls 0, populated 0) | | | | | | | |
| goom3d | K | 3 (0.04) | 0/3/0 | 3 | 0 | not scored: not scored (placed 3, cross calls 0, populated 0) | | | | | | | |
| nginx | U | 5 (0.00) | 1/4/0 | 3 | 0 | not scored: not scored (placed 5, cross calls 0, populated 1) | | | | | | | |
| curl | U | 60 (0.01) | 6/52/2 | 50 | 0 | not scored: not scored (placed 60, cross calls 0, populated 4) | | | | | | | |
| lua | U | 5 (0.00) | 0/5/0 | 4 | 0 | not scored: not scored (placed 5, cross calls 0, populated 0) | | | | | | | |
| leveldb | U | 11 (0.01) | 0/2/9 | 3 | 0 | not scored: not scored (placed 11, cross calls 0, populated 1) | | | | | | | |
| libuv | U | 113 (0.03) | 13/29/71 | 39 | 9 | not scored: not scored (placed 113, cross calls 9, populated 6) | | | | | | | |
| bubbletea | U | 0 (0.00) | 0/0/0 | 0 | 0 | not scored: not scored (placed 0, cross calls 0, populated 0) | | | | | | | |
| macroquad | U | 6 (0.01) | 0/6/0 | 6 | 0 | not scored: not scored (placed 6, cross calls 0, populated 0) | | | | | | | |
| carddemo-cobol-ctrl | U | 0 (0.00) | 0/0/0 | 0 | 0 | not scored: not scored (placed 0, cross calls 0, populated 0) | | | | | | | |
| quake | X | 1575 (0.29) | 35/137/1403 | 170 | 96 | not scored: not scored (placed 1575, cross calls 96, populated 10) | | | | | | | |
| quake2 | X | 2583 (0.49) | 50/71/2462 | 146 | 552 | 0.17 [0.16, 0.18] | 0.35 (0.39) | 0.29 (0.37) | -10.5 | -3.2 | no (file) | no |
| freedoom | X | 1 (0.01) | 0/1/0 | 1 | 0 | not scored: not scored (placed 1, cross calls 0, populated 0) | | | | | | | |

## Low-count programs (100 to 499 cross calls; descriptive only, not used by any prediction)

| program | grp | placed (cov) | cross calls | cross | function null mean (97.5th) | z function | file null (97.5th) |
|---|---|---|---|---|---|---|---|
| doomgeneric | C | 1061 (0.89) | 399 | 0.89 | 0.62 (0.68) | 9.5 | 0.60 (0.70) |
| sdl-doom | C | 1034 (0.96) | 402 | 0.90 | 0.63 (0.68) | 9.4 | 0.60 (0.70) |
| doom-ascii | C | 970 (0.95) | 387 | 0.92 | 0.64 (0.70) | 9.4 | 0.61 (0.71) |
| doom3-bfg | M | 804 (0.80) | 318 | 0.97 | 0.64 (0.70) | 10.0 | 0.61 (0.72) |
| gore | T | 599 (0.60) | 169 | 0.82 | 0.62 (0.69) | 5.2 | n/a (n/a) |
| doom-scheme | T | 621 (0.78) | 174 | 0.71 | 0.63 (0.70) | 2.2 | 0.59 (0.71) |
| dartdoom | T | 527 (0.73) | 169 | 0.51 | 0.63 (0.70) | -3.4 | 0.48 (0.60) |
| mochadoom | T | 877 (0.29) | 103 | 0.63 | 0.66 (0.73) | -1.0 | 0.60 (0.70) |
| doomf77 | T | 146 (1.00) | 135 | 0.31 | 0.55 (0.65) | -4.3 | n/a (n/a) |

## Arm comparison (cross-wiring standardised gap against the function shuffle, resolution 1.0 for D)

| program | D | H1 (hand, derived rules) | H3 (hand rules, no overrides) | H2 (hand taxonomy as shipped) |
|---|---|---|---|---|
| chocolate-doom | 3.3 | 12.0 | 14.3 | 15.1 |
| crispy-doom | 2.9 | 10.0 | 13.7 | 13.0 |
| doomgeneric | not scored | 11.5 | 11.7 | 11.8 |
| sdl-doom | not scored | 10.8 | 10.6 | 10.5 |
| doom-ascii | not scored | 9.1 | 8.8 | 9.0 |
| doom-wasm | 4.1 | 10.6 | 17.6 | 17.2 |
| mood | 13.7 | 11.0 | 12.1 | 11.8 |
| prboom-plus | 2.4 | 7.8 | 6.7 | 7.2 |
| woof | -1.7 | 11.0 | 11.1 | 10.7 |
| dsda-doom | -1.2 | 7.6 | 7.6 | 7.8 |
| inter-doom | 7.1 | 14.5 | 13.3 | 13.7 |
| fastdoom | 1.2 | 4.8 | 3.9 | 3.8 |
| doom-ios | 0.9 | 7.4 | 6.9 | 6.5 |
| eternity | -4.7 | 9.1 | 10.4 | 11.0 |
| odamex | 3.6 | 7.2 | 5.5 | 5.6 |
| srb2 | 5.5 | 8.5 | 8.4 | 8.8 |
| puredoom | 13.0 | 10.7 | 11.1 | 11.2 |
| nugget-doom | 0.9 | 10.5 | 12.2 | 11.8 |
| doomretro | 5.1 | 7.0 | 6.9 | 6.9 |
| gzdoom | -2.2 | -0.3 | 2.4 | 7.7 |
| doomsday | 2.5 | 12.6 | -2.8 | -2.6 |
| edge-classic | 0.7 | 3.6 | 5.0 | 4.9 |
| doom3-bfg | not scored | 9.3 | 9.5 | 9.6 |
| gore | not scored | 8.3 | 8.6 | 8.1 |
| managed-doom | not scored | not scored | -4.1 | -4.3 |
| mochadoom | not scored | not scored | 2.6 | 1.1 |
| kocoa-doom | not scored | not scored | not scored | -0.5 |
| helion | not scored | not scored | -3.0 | -2.7 |
| room4doom | not scored | not scored | 1.1 | -1.6 |
| quake2 | -10.5 | -3.6 | -6.1 | -6.1 |

## Predictions

| prediction | result | value |
|---|---|---|
| P1 pipeline sanity: scored close copies above every defined null | NOT met | 2 of 3 scored: ['chocolate-doom', 'doom-wasm'] |
| P2 gore and doom-scheme above function and file nulls and on non-twin placements | NOT met or untestable | {'gore': None, 'doom-scheme': None} |
| P3 at most one scored U or R program above the file null | met | 0 of 0 scored: [] |
| P4 none of the four zeros scored above the file null (falsifier) | not falsified | above: {'mochadoom': None, 'kocoa-doom': None, 'managed-doom': None, 'doomf77': None}; sufficiency gates passed: {'mochadoom': False, 'kocoa-doom': False, 'managed-doom': False, 'doomf77': False} |
| P5 D vs H3 rank agreement at least 0.8 (all; within M and T) | NOT met | rho 0.46 (n 20); M and T rho 0.29 (n 16) |
| P6 at least four scored M programs above the file null on non-twin placements | met | 4 of 12: ['prboom-plus', 'inter-doom', 'srb2', 'doomretro'] |
| P7 rank agreement across resolutions at least 0.8 and scored status of C, T, U unchanged | NOT met | rho 0.5 vs 1.0 0.52 (n 13); 2.0 vs 1.0 0.42 (n 20); status unchanged: False |

## Group effect sizes (A12 on the standardised gap against the function shuffle, arm D, all placements)

| pair | A12 | n | n |
|---|---|---|---|
| C against M | 0.65 | 3 | 16 |
| M against T | n/a | 16 | 0 |
| T against U | n/a | 0 | 0 |
| T against R | n/a | 0 | 0 |

## Reading (written after the numbers)

**The discovered subsystems are a weak yardstick for wiring against chance; the hand-written ones still work.** On the same programs, scans, engine and exclusion rule, the close and modified C-family programs (23 to 24 with nulls) have a **median standardised gap of 3.3** under the discovered subsystems (52% at 3 or more; 65% above the function-shuffle 97.5th percentile), against **9.3, 9.2 and 9.3** under the hand-written ones (arms H1, H3, H2; 92% to 96% at 3 or more). The ranking of programs by gap agrees only weakly between the arms (Spearman 0.46 over 20 programs, 0.29 within M and T; P5 not met).

**Why, from the measurements (not a claim about the subsystems being unreal).**
* **Name and path rules place the discovered subsystems poorly.** Held-out recovery on `linuxdoom` itself is 0.67 for the discovered subsystems against 0.96 for the hand-written ones, and the file-stem and prefix rules reproduce the Louvain labels only 71% of the time (100% for the hand-written ones, which are defined by file prefixes). Communities of the call graph cut across files, so file-based placement cannot follow them.
* **The discovered reference leaves little cross-subsystem structure to match.** Its diagonal share is 0.84 (hand-written: 0.54) and its wiring floor 0.63 (0.46); the null means for ports sit at 0.40 to 0.67 and the real cross-wiring at 0.45 to 0.99, so most of the headroom is already used by chance.

**Predictions (registered floor of 500 cross-subsystem calls).** P1 not met (2 of 3 scored close copies above every null: `chocolate-doom`, `doom-wasm`; `crispy-doom` not; `doomgeneric`, `sdl-doom` and `doom-ascii` fell just under the floor at 387 to 402 cross calls and are strongly above in the descriptive tier, z 9.4 to 9.5). P2 untestable (`gore` 169 and `doom-scheme` 174 cross calls: descriptive tier only; `gore` z 5.2 and `doom-scheme` z 2.2 against the function shuffle, file null undefined for `gore`). P3 met only vacuously (no unrelated or from-scratch program is scored; they place 0% to 3% of their functions and have at most 9 cross calls, so they cannot be tested this way). P4 not falsified, but every zero is **unreadable**: none of `mochadoom`, `kocoa-doom`, `managed-doom`, `doomf77` is scored and none passes the sufficiency gates. P5 not met. P6 met at the threshold (4 of 12 scored modified ports above the file null on non-twin placements: `prboom-plus`, `inter-doom`, `srb2`, `doomretro`; the other 8 are not). P7 not met (resolution rank agreement 0.52 and 0.42; scored status changes).

**What the hand-written arms show (same engine, stricter exclusion of the fallback class).** They repeat the old note: Go, Scheme and Dart translations are positive (`gore` 8.6, `doom-scheme` 7.6, `dartdoom` 8.3 against the function shuffle, arm H3), the C#, Kotlin, Java and Fortran translations are around zero or negative (`managed-doom` -4.1, `kocoa-doom` -1.3, `mochadoom` 2.6, `doomf77` 0.6), rewrites are near zero or negative (`helion` -3.0, `room4doom` 1.1) and `quake2` is clearly negative (-6.1). A zero for the Java, Kotlin, C# and Fortran ports remains unreadable (lost or failed placement; the gates fail).

**Consequence for the article.** Keep the hand-written subsystems for the wiring-against-chance chart. The discovered subsystems are real structure of DOOM's call graph (stages 1 and 2) and a good description of it, but name and path placement cannot use them as a yardstick for other programs. Both nulls keep the call graph and cannot say whether the calls kept the design; and a positive gap still mixes survival of copied code, names and layout with wiring (the non-twin subset reduces this for close copies but is mostly under the floor).
