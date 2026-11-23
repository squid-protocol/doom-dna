# DOOM-E11 stage 3 results: is `linuxdoom`'s partition specifically predictive of other programs' communities, from measurements alone?

Registered design: [stage 3](../../preregistration/E11_SUBSYSTEMS_STAGE3.md). Arm F placement (no call edge read), excess homogeneity over communities of 10+ functions, about 30 alternative references. Full table: `stage3_table.csv`.

## Calibration (10-fold on `linuxdoom`'s own functions, abstaining at the 95th percentile of nearest distance)

| reference resolution | decision | kappa median [95% over folds] | shuffle 95th | accuracy | balanced accuracy |
|---|---|---|---|---|---|
| 0.5 | lift | 0.08 [0.03, 0.15] | 0.05 | 0.16 | 0.13 |
| 0.5 | argmax | 0.18 [0.10, 0.24] | 0.09 | 0.37 | 0.34 |
| 1.0 | lift | 0.08 [0.05, 0.13] | 0.05 | 0.12 | 0.12 |
| 1.0 | argmax | 0.19 [0.09, 0.23] | 0.07 | 0.30 | 0.32 |
| 2.0 | lift | 0.09 [-0.00, 0.13] | 0.03 | 0.11 | 0.08 |
| 2.0 | argmax | 0.10 [0.03, 0.22] | 0.05 | 0.16 | 0.20 |

**Gate (lift, resolution 1.0: median kappa at least 0.20 with lower bound above the shuffle 95th): NOT PASSED.**

## Specificity at the primary setting (reference resolution 1.0, port resolution 1.0, `lift`)

Percentile = share of the ~30 alternative references whose excess homogeneity is at or below DOOM's; DOOM-specific = percentile at least 0.95.

| program | group | functions | coverage | X DOOM | X alt median (95th) | difference | percentile | DOOM-specific | X file control |
|---|---|---|---|---|---|---|---|---|---|
| chocolate-doom | C | 2477 | 0.89 | 0.031 | 0.022 (0.054) | 0.009 | 0.80 | no | 0.427 |
| crispy-doom | C | 2823 | 0.89 | 0.025 | 0.024 (0.059) | 0.000 | 0.57 | no | 0.433 |
| doomgeneric | C | 1192 | 0.94 | 0.066 | 0.033 (0.076) | 0.033 | 0.90 | no | 0.331 |
| sdl-doom | C | 1079 | 0.93 | 0.064 | 0.028 (0.073) | 0.036 | 0.90 | no | 0.336 |
| doom-ascii | C | 1019 | 0.93 | 0.062 | 0.028 (0.071) | 0.034 | 0.90 | no | 0.319 |
| doom-wasm | C | 2035 | 0.90 | 0.034 | 0.023 (0.060) | 0.011 | 0.77 | no | 0.445 |
| mood | M | 1860 | 0.98 | 0.073 | 0.022 (0.069) | 0.051 | 0.93 | no | 0.510 |
| prboom-plus | M | 2430 | 0.92 | 0.041 | 0.026 (0.061) | 0.015 | 0.83 | no | 0.387 |
| woof | M | 3788 | 0.90 | 0.039 | 0.026 (0.072) | 0.013 | 0.77 | no | 0.371 |
| dsda-doom | M | 4497 | 0.90 | 0.041 | 0.027 (0.062) | 0.014 | 0.73 | no | 0.320 |
| inter-doom | M | 3060 | 0.91 | 0.070 | 0.058 (0.093) | 0.011 | 0.70 | no | 0.451 |
| fastdoom | M | 2114 | 0.84 | 0.056 | 0.041 (0.095) | 0.015 | 0.80 | no | 0.452 |
| doom-ios | M | 1768 | 0.90 | 0.060 | 0.047 (0.100) | 0.014 | 0.83 | no | 0.433 |
| eternity | M | 6641 | 0.77 | 0.035 | 0.025 (0.055) | 0.010 | 0.73 | no | 0.318 |
| odamex | M | 7759 | 0.81 | 0.044 | 0.034 (0.067) | 0.010 | 0.73 | no | 0.352 |
| srb2 | M | 6805 | 0.84 | 0.058 | 0.036 (0.095) | 0.022 | 0.87 | no | 0.359 |
| puredoom | M | 1546 | 0.95 | 0.055 | 0.018 (0.061) | 0.037 | 0.90 | no | 0.317 |
| nugget-doom | M | 4173 | 0.91 | 0.042 | 0.025 (0.071) | 0.017 | 0.77 | no | 0.345 |
| doomretro | M | 2233 | 0.79 | 0.040 | 0.035 (0.074) | 0.005 | 0.67 | no | 0.296 |
| gzdoom | M | 18434 | 0.68 | 0.042 | 0.039 (0.083) | 0.003 | 0.60 | no | 0.323 |
| doomsday | M | 22101 | 0.63 | 0.031 | 0.023 (0.046) | 0.008 | 0.73 | no | 0.300 |
| edge-classic | M | 5152 | 0.86 | 0.045 | 0.034 (0.070) | 0.011 | 0.73 | no | 0.387 |
| doom3do | M | 511 | 0.89 | 0.052 | 0.025 (0.066) | 0.027 | 0.90 | no | 0.248 |
| doom3-bfg | M | 1011 | 0.94 | 0.057 | 0.030 (0.063) | 0.027 | 0.90 | no | 0.363 |
| gore | T | 996 | 0.90 | 0.051 | 0.027 (0.056) | 0.025 | 0.90 | no | 0.081 |
| doom-scheme | T | 798 | 0.76 | 0.040 | 0.034 (0.072) | 0.006 | 0.73 | no | 0.336 |
| dartdoom | T | 723 | 0.88 | 0.033 | 0.025 (0.048) | 0.008 | 0.77 | no | 0.386 |
| managed-doom | T | 1285 | 0.87 | 0.115 | 0.103 (0.147) | 0.012 | 0.73 | no | 0.370 |
| mochadoom | T | 3037 | 0.70 | 0.085 | 0.071 (0.127) | 0.015 | 0.73 | no | 0.426 |
| kocoa-doom | T | 2902 | 0.67 | 0.072 | 0.057 (0.101) | 0.015 | 0.77 | no | 0.430 |
| doomf77 | T | 146 | | | | | | not scored: too small (under 300 functions) | |
| doo-cr | T | 1488 | | | | | | not scored: under 10 communities of 10+ functions | |
| helion | R | 8386 | 0.63 | 0.062 | 0.049 (0.087) | 0.013 | 0.70 | no | 0.371 |
| rust-doom | R | 582 | 0.59 | 0.082 | 0.072 (0.121) | 0.010 | 0.67 | no | 0.311 |
| room4doom | R | 4729 | 0.44 | 0.039 | 0.028 (0.052) | 0.011 | 0.90 | no | 0.398 |
| cssdoom | R | 217 | | | | | | not scored: too small (under 300 functions) | |
| fsharp-doom | R | 47 | | | | | | not scored: too small (under 300 functions) | |
| doom-fx | R | 1865 | | | | | | not scored: under 10 communities of 10+ functions | |
| sqldoom | R | 475 | 0.85 | 0.042 | 0.038 (0.091) | 0.004 | 0.60 | no | 0.555 |
| agentic-cobol-doom-cc | K | 45 | | | | | | not scored: too small (under 300 functions) | |
| agentic-cobol-doom-codex | K | 153 | | | | | | not scored: too small (under 300 functions) | |
| fps-cob | K | 51 | | | | | | not scored: too small (under 300 functions) | |
| c-raycasting | K | 23 | | | | | | not scored: too small (under 300 functions) | |
| c-raycasting2 | K | 21 | | | | | | not scored: too small (under 300 functions) | |
| goom3d | K | 76 | | | | | | not scored: too small (under 300 functions) | |
| nginx | U | 3419 | 0.79 | 0.029 | 0.021 (0.044) | 0.009 | 0.72 | no | 0.202 |
| curl | U | 7412 | 0.87 | 0.046 | 0.033 (0.084) | 0.013 | 0.79 | no | 0.327 |
| lua | U | 1666 | 0.84 | 0.039 | 0.027 (0.057) | 0.012 | 0.90 | no | 0.310 |
| leveldb | U | 1278 | 0.38 | 0.038 | 0.025 (0.040) | 0.013 | 0.90 | no | 0.343 |
| libuv | U | 3682 | 0.33 | 0.053 | 0.032 (0.067) | 0.021 | 0.79 | no | 0.323 |
| bubbletea | U | 720 | | | | | | not scored: under 10 communities of 10+ functions | |
| macroquad | U | 960 | 0.54 | 0.084 | 0.047 (0.099) | 0.038 | 0.90 | no | 0.250 |
| carddemo-cobol-ctrl | U | 55 | | | | | | not scored: too small (under 300 functions) | |
| quake | X | 5351 | 0.84 | 0.031 | 0.024 (0.048) | 0.008 | 0.73 | no | 0.389 |
| quake2 | X | 5289 | 0.42 | 0.061 | 0.034 (0.086) | 0.027 | 0.87 | no | 0.481 |
| freedoom | X | 106 | | | | | | not scored: too small (under 300 functions) | |

## Predictions

| prediction | result | value |
|---|---|---|
| P1 gate | NOT met | kappa 0.08 [0.05] vs shuffle 95th 0.05 |
| P2 at least five of six C ports DOOM-specific | NOT met | 0 of 6 scored: [] |
| P3 at most one scored U program DOOM-specific | met | 0 of 6 scored: [] |
| P4 `gore` DOOM-specific; at most three of the other scored translations | NOT met | gore no/unscored; others 0 of 5: [] |
| P5 at least four of five modified ports DOOM-specific | NOT met | 0 of 5 scored: [] |
| P6 Spearman(percentile, group rank) at least 0.5 | NOT met | rho 0.14 (n 40) |
| P7 R and K not DOOM-specific more often than U | met | R (0, 4), K (0, 0), U (0, 6) |
| P8 P2 robust to port resolution and to `argmax` for at least five of six | NOT met | 0 of 6: [] |

## Other-program references used

| program | resolution chosen | groups | groups of 10+ | method |
|---|---|---|---|---|
| nginx | 1.0 | 28 | 17 | consensus |
| curl | 0.5 | 73 | 16 | best-of-30 |
| lua | 1.0 | 51 | 12 | consensus |
| leveldb | 1.0 | 30 | 18 | consensus |
| libuv | 1.0 | 77 | 18 | consensus |
| bubbletea | 2.0 | 29 | 16 | consensus |
| macroquad | 2.0 | 40 | 20 | consensus |

## Reading (written after the numbers)

**The gate failed and no program, including the close copies, was DOOM-specific.** Arm F (placement from measurements alone) predicts `linuxdoom`'s own subsystems only slightly better than chance (kappa 0.08, balanced accuracy 0.12; `argmax` 0.19 and 0.32), below the 0.20 gate at every resolution. Per the registration this means arm F carries too little to support any port-level claim. The specificity table agrees: **0 of 6 close copies, 0 of 5 modified ports, `gore` and the other translations are all below the 95th percentile**, and DOOM's partition ranks only at the 57th to 93rd percentile among the ~30 alternatives, including for programs known (stage 2) to keep DOOM's subsystems.

**The important point is sensitivity, not ancestry.** The close copies are the positive controls, and this method does not detect them. So for the translations and rewrites a null means "this method cannot see", not "the architecture is gone". P3 and P7 are met only because nothing is specific (0 of 6 unrelated programs, and R and K likewise); they are not evidence of discrimination. P1, P2, P4, P5, P6 (Spearman 0.14) and P8 are not met.

**What the table does show.** A function's source file explains a program's own call-graph communities far better than its DOOM-subsystem label does: excess homogeneity from file layout alone is 0.20 to 0.56 (`X file control`) against 0.03 to 0.12 for the measurement-based labels. DOOM's partition scores a little above the median alternative in almost every program (differences 0.00 to 0.05), unrelated programs included, a mild generic effect that is not DOOM-specific. Programs under 300 functions (`doomf77`, the toy raycasters, `cssdoom`, `fsharp-doom`, `freedoom`, `carddemo-cobol-ctrl`) were not scored; `doo-cr`, `doom-fx` and `bubbletea` have fewer than 10 communities of 10 or more functions at port resolution 1.0.

**Consequence.** This circularity-free route is not viable as designed: measurements alone do not carry the subsystem signal across programs (the earlier sfs study found the same, measures-only balanced accuracy 0.10 to 0.26). What does work is twin placement for close copies (stage 2). Anything that reaches further (Seed-and-Extend's call-graph extension) reads the call graph, so measuring architecture on its output is circular. Whether architecture survives translation therefore remains **unmeasured**, with two untested routes in the stage 3 note (data and constants; validated name-and-path placement with a file-level null).
