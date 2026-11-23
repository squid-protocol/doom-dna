# DOOM-E11 stage 2 results: how much of `linuxdoom`'s subsystem architecture do ports keep?

Registered design: [stage 2](../../preregistration/E11_SUBSYSTEMS_STAGE2.md). Placement by one-to-one structural twins (E7 Amendment 2 pooled K = 25). Reference: iterative consensus Louvain. Full table: `stage2_table.csv`.

## Primary ports (resolution 1.0)

| port | placed (coverage) | edge retention | gained-edge fidelity real [95% CI] vs null 95th | AMI imported vs own groups (ceiling) | label-perm 95th / file-perm 99th | AMI file-label / hand taxonomy | M1 Q (fraction of pure copy) | M3 cos (copy exp), gap |
|---|---|---|---|---|---|---|---|---|
| chocolate-doom | 367 (0.50) | 0.93 | n/a [n/a, n/a] vs n/a | 0.69 (0.80) | 0.02 / 0.34 | 0.42 / 0.46 | 0.62 (1.00) | n/a (n/a), n/a |
| crispy-doom | 245 | insufficient | | | | | | |
| doomgeneric | 387 (0.53) | 0.98 | n/a [n/a, n/a] vs n/a | 0.84 (0.90) | 0.02 / 0.38 | 0.48 / 0.50 | 0.64 (0.99) | n/a (n/a), n/a |
| sdl-doom | 386 (0.52) | 0.98 | n/a [n/a, n/a] vs n/a | 0.86 (0.89) | 0.02 / 0.39 | 0.49 / 0.51 | 0.64 (0.99) | n/a (n/a), n/a |
| doom-ascii | 377 (0.51) | 0.98 | n/a [n/a, n/a] vs n/a | 0.86 (0.88) | 0.02 / 0.39 | 0.49 / 0.49 | 0.63 (0.99) | n/a (n/a), n/a |
| doom-wasm | 362 (0.49) | 0.93 | n/a [n/a, n/a] vs n/a | 0.70 (0.84) | 0.02 / 0.35 | 0.44 / 0.49 | 0.62 (1.01) | n/a (n/a), n/a |

## Secondary and other programs (resolution 1.0)

| program | group | eligible | placed | calls among placed | status | edge retention | AMI imported vs own (file-perm 99th) |
|---|---|---|---|---|---|---|---|
| nugget-doom | control/other | 3419 | 47 | 3 | insufficient | n/a | n/a (n/a) |
| doom3-bfg | control/other | 836 | 42 | 9 | insufficient | n/a | n/a (n/a) |
| quake2 | control/other | 3505 | 39 | 0 | insufficient | n/a | n/a (n/a) |
| quake | control/other | 4336 | 30 | 2 | insufficient | n/a | n/a (n/a) |
| doom3do | control/other | 428 | 21 | 5 | insufficient | n/a | n/a (n/a) |
| helion | control/other | 6424 | 16 | 0 | insufficient | n/a | n/a (n/a) |
| doomsday | control/other | 13392 | 11 | 0 | insufficient | n/a | n/a (n/a) |
| doomretro | control/other | 1921 | 10 | 1 | insufficient | n/a | n/a (n/a) |
| gzdoom | control/other | 12864 | 10 | 1 | insufficient | n/a | n/a (n/a) |
| libuv | control/other | 2745 | 9 | 0 | insufficient | n/a | n/a (n/a) |
| curl | control/other | 6912 | 6 | 0 | insufficient | n/a | n/a (n/a) |
| dartdoom | control/other | 576 | 4 | 0 | insufficient | n/a | n/a (n/a) |
| room4doom | control/other | 3488 | 3 | 0 | insufficient | n/a | n/a (n/a) |
| doo-cr | control/other | 646 | 2 | 0 | insufficient | n/a | n/a (n/a) |
| managed-doom | control/other | 947 | 2 | 0 | insufficient | n/a | n/a (n/a) |
| agentic-cobol-doom-cc | control/other | 47 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| agentic-cobol-doom-codex | control/other | 124 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| cssdoom | control/other | 176 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| doom-fx | control/other | 1468 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| doom-scheme | control/other | 585 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| doomf77 | control/other | 144 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| edge-classic | control/other | 4036 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| fps-cob | control/other | 48 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| freedoom | control/other | 111 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| fsharp-doom | control/other | 39 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| gore | control/other | 812 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| kocoa-doom | control/other | 1646 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| leveldb | control/other | 853 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| lua | control/other | 1207 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| nginx | control/other | 3344 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| rust-doom | control/other | 301 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| sqldoom | control/other | 389 | 0 | 0 | insufficient | n/a | n/a (n/a) |
| mood | secondary | 1694 | 627 | 710 | scored | 0.52 | 0.67 (0.25) |
| puredoom | secondary | 1261 | 359 | 223 | insufficient | n/a | n/a (n/a) |
| fastdoom | secondary | 1923 | 158 | 71 | insufficient | n/a | n/a (n/a) |
| inter-doom | secondary | 2509 | 104 | 82 | insufficient | n/a | n/a (n/a) |
| doom-ios | secondary | 1488 | 99 | 34 | insufficient | n/a | n/a (n/a) |
| prboom-plus | secondary | 2044 | 85 | 15 | insufficient | n/a | n/a (n/a) |
| dsda-doom | secondary | 3470 | 77 | 6 | insufficient | n/a | n/a (n/a) |
| woof | secondary | 3172 | 53 | 8 | insufficient | n/a | n/a (n/a) |
| srb2 | secondary | 5818 | 42 | 0 | insufficient | n/a | n/a (n/a) |
| mochadoom | secondary | 1751 | 29 | 25 | insufficient | n/a | n/a (n/a) |
| odamex | secondary | 5541 | 1 | 0 | insufficient | n/a | n/a (n/a) |
| eternity | secondary | 5236 | 0 | 0 | insufficient | n/a | n/a (n/a) |

## Pure-copy curve (random samples of linuxdoom's own graph)

| placed fraction | edges among placed | modularity of the reference labels |
|---|---|---|
| 0.1 | 16 | 0.589 |
| 0.2 | 61 | 0.681 |
| 0.3 | 138 | 0.680 |
| 0.4 | 258 | 0.684 |
| 0.5 | 390 | 0.691 |
| 0.6 | 586 | 0.688 |

## Predictions

| prediction | result | value |
|---|---|---|
| P1 edge retention at least 0.50 for each primary port | NOT met | 5 of 6 |
| P2 AMI above label-permutation 95th for all six, above file-level 99th for at least five | NOT met | 5 of 6; 5 of 6 |
| P3 M1 at least 0.8 of pure-copy expectation for at least four | met | 5 of 6 |
| P4 gained-edge fidelity above matched null for at least four | NOT met | 0 of 6 |
| P5 file-label AMI within 0.05 of subsystem AMI for at least three | not true | 0 of 6 |
| P6 no unrelated or from-scratch program is scored | met | none scored |
| P7 P2 holds at all three resolutions for at least five | met | 5 of 6 |
| P8 coverage ranks as E7 Amendment 2 pooled shares (Spearman at least 0.8) | met | rho 0.95 (n 50) |

## Reading (written after the numbers)

**What the registered rules produced.** Five of the six primary ports were scored; `crispy-doom` (245 placed functions, 249 calls among them) fell under the registered floor of 300 calls and is listed as insufficient, not as a failure. P1 and P2 therefore read "5 of 6" because of that one unscored port: **all five scored ports meet both** (edge retention 0.93 to 0.98; AMI far above the label-permutation 95th percentile of 0.02 and the file-level 99th percentile of 0.34 to 0.39). The two other "not met" rows are not failures of the ports: **P4 could not be tested** (a port adds 1 to 4 calls among the placed functions beyond `linuxdoom`'s, fewer than the 30 needed), and M3 had enough cross-group calls only at the finest resolution (100 to 115 at gamma 2.0; 38 to 59 at 0.5 and 1.0).

**What it says.**
* For same-language ports that copy a large share of `linuxdoom`, **`linuxdoom`'s call-graph groups remain communities of the port's whole call graph**: agreement with the port's own groups is 0.69 to 0.86 (AMI at gamma 1.0) against the port's own stability ceiling of 0.80 to 0.90, i.e. about 83% to 98% of the ceiling.
* **The groups explain the ports better than file layout or the hand taxonomy do** (file-label AMI 0.42 to 0.49; hand taxonomy 0.46 to 0.51; discovered groups 0.69 to 0.86), so the discovered subsystems add information beyond which file a function sits in. This was the prediction I flagged as the likely uncomfortable one (P5); it did not happen.
* **The placed core is essentially a pure copy.** M1 is 0.99 to 1.01 of the pure-copy expectation and edge retention 0.93 to 0.98. A copy keeps its structure, so this is the calibration ceiling, as the design said, and the test of whether ports extend the architecture (gained-edge fidelity) is untestable because ports add almost no calls among the copied functions.
* `mood` (more modified; edge retention 0.52) is scored and keeps the groups well (AMI 0.67, file-level 99th 0.25) but sits at 0.73 of its own ceiling.

**What it does not say.** Every program that is not a close copy is unscored: the modified ports (`prboom-plus`, `woof`, `dsda-doom`, `inter-doom`, `fastdoom`) place 53 to 158 functions with 6 to 82 calls among them, and every translation, from-scratch rewrite and unrelated program places 0 to 47 functions with 0 to 9 calls (P6 met). **The translation case, which is the interesting one, is not measured here**; the design said so in advance and §F lists the two routes that could be tried next.

**Limits.** Placement covers about half of `linuxdoom`'s clustered functions even for the closest ports, so the call graph among placed functions is sparse (about 510 to 570 calls). Results at gamma 0.5 are weaker (AMI 0.45 to 0.91): the coarser the groups, the less they match a port's own finer structure. P8 (coverage ranks as the pooled shares do) met, rho 0.95.
