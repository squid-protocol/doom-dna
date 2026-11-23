# DOOM-E11 stage 1 results: do call graphs yield stable, meaningful subsystems?

Method and gate as in [the stage 1 note](../../preregistration/E11_SUBSYSTEMS_STAGE1.md). Louvain, 30 seeds, 20 degree-preserving nulls, 1,000 label permutations. Full table: `stage1_table.csv`.

## Gate

| criterion | value | pass |
|---|---|---|
| (i) linuxdoom stability ARI median >= 0.70 | 0.78 | yes |
| (ii) >= 70% of functions in groups of >= 10 | 0.98 | yes |
| (iii) modularity z vs degree-preserving null >= 5 | 62.4 | yes |
| (iv) agreement with hand taxonomy: NMI above null (p<0.01) and ARI >= 0.30 | NMI 0.52 (null95 0.08), ARI 0.35 | yes |
| (v) >= 8 of 10 ports with stability ARI median >= 0.60 | 9 of 10 | yes |

**Gate: PASSED.**

## Per program (resolution 1.0)

| program | funcs (clustered) | groups | groups >= 10 | share in them | largest group | stability ARI median / min | modularity (null) z | NMI file (null95) | NMI dir | ARI hand |
|---|---|---|---|---|---|---|---|---|---|---|
| linuxdoom | 779 (736) | 19 | 16 | 0.98 | 0.21 | 0.78 / 0.60 | 0.697 (0.479) z 62 | 0.59 (0.19) | 0.25 | 0.35 |
| chocolate-doom | 2503 (2284) | 57 | 23 | 0.94 | 0.14 | 0.74 / 0.61 | 0.776 (0.472) z 122 | 0.60 (0.21) | 0.48 | nan |
| crispy-doom | 2852 (2569) | 59 | 26 | 0.95 | 0.10 | 0.76 / 0.58 | 0.756 (0.454) z 170 | 0.60 (0.21) | 0.46 | nan |
| doomgeneric | 1192 (1061) | 44 | 17 | 0.91 | 0.14 | 0.76 / 0.63 | 0.729 (0.510) z 69 | 0.61 (0.23) | nan | nan |
| prboom-plus | 2439 (2174) | 42 | 23 | 0.96 | 0.14 | 0.66 / 0.55 | 0.752 (0.506) z 102 | 0.59 (0.18) | 0.05 | nan |
| woof | 3805 (3619) | 58 | 27 | 0.97 | 0.16 | 0.69 / 0.52 | 0.762 (0.440) z 219 | 0.57 (0.17) | 0.26 | nan |
| eternity | 6642 (6125) | 71 | 25 | 0.98 | 0.13 | 0.62 / 0.48 | 0.741 (0.457) z 154 | 0.54 (0.14) | 0.28 | nan |
| odamex | 7886 (6729) | 89 | 34 | 0.97 | 0.10 | 0.53 / 0.39 | 0.719 (0.427) z 193 | 0.56 (0.16) | 0.40 | nan |
| mochadoom | 3037 (2405) | 82 | 32 | 0.94 | 0.09 | 0.76 / 0.65 | 0.821 (0.581) z 116 | 0.62 (0.29) | 0.53 | nan |
| gore | 1011 (893) | 28 | 16 | 0.96 | 0.17 | 0.77 / 0.60 | 0.709 (0.485) z 59 | 0.17 (0.05) | 0.12 | nan |
| puredoom | 1551 (1423) | 22 | 15 | 0.98 | 0.19 | 0.85 / 0.73 | 0.726 (0.423) z 112 | 0.51 (0.11) | 0.44 | nan |
| nginx | 3439 (2959) | 26 | 16 | 0.99 | 0.19 | 0.62 / 0.49 | 0.578 (0.375) z 153 | 0.42 (0.15) | 0.21 | nan |
| curl | 7732 (6699) | 83 | 21 | 0.97 | 0.14 | 0.65 / 0.55 | 0.679 (0.336) z 230 | 0.48 (0.18) | 0.49 | nan |
| lua | 1679 (1410) | 50 | 13 | 0.92 | 0.16 | 0.58 / 0.47 | 0.646 (0.412) z 100 | 0.61 (0.14) | 0.23 | nan |
| helion | 8396 (7369) | 137 | 34 | 0.96 | 0.16 | 0.71 / 0.49 | 0.793 (0.521) z 220 | 0.56 (0.24) | 0.42 | nan |
| rust-doom | 583 (479) | 20 | 13 | 0.95 | 0.12 | 0.70 / 0.53 | 0.714 (0.567) z 29 | 0.54 (0.22) | 0.39 | nan |

## Resolution sweep (is about 16 groups natural?)

| program | resolution | groups | groups >= 10 | share in them | stability ARI median |
|---|---|---|---|---|---|
| linuxdoom | 0.5 | 12 | 11 | 1.00 | 0.86 |
| linuxdoom | 1.0 | 19 | 16 | 0.98 | 0.78 |
| linuxdoom | 2.0 | 28 | 24 | 0.96 | 0.74 |
| chocolate-doom | 0.5 | 49 | 17 | 0.95 | 0.71 |
| chocolate-doom | 1.0 | 57 | 23 | 0.94 | 0.74 |
| chocolate-doom | 2.0 | 68 | 34 | 0.94 | 0.81 |

## Predictions

| prediction | result | value |
|---|---|---|
| P1 linuxdoom stability ARI median in 0.50 to 0.80 | met | 0.78 |
| P2 modularity z above 5 for every program | met | min z 28.8 |
| P3 at least 70% of linuxdoom's clustered functions in groups of 10+ | met | 0.98 |
| P4 NMI above null for file and hand taxonomy, ARI hand below 0.30 | NOT met | p_file 0.000, p_hand 0.000, ARI hand 0.35 |
| P5 controls as stable as ports (median stability within 0.10) | met | controls 0.65, ports 0.75 |
| P6 no resolution gives a stable (ARI >= 0.7) partition with 14 to 18 groups of 10+ (linuxdoom) | NOT met | g=0.5: 11 groups, ARI 0.86; g=1.0: 16 groups, ARI 0.78; g=2.0: 24 groups, ARI 0.74 |
| P7 gate not passed on (i) or (iv) | NOT met |  |

## Reading (written after the numbers)

**The gate passed, and my pessimistic predictions were wrong (P4, P6, P7 not met).** The earlier probe of the article's script (groups agreeing only about 0.5 across orderings, about zero agreement with the hand taxonomy, 71% of functions in a catch-all) described the script's one-pass clustering, not the call graph. A standard method (Louvain) on the same graph gives **19 groups for `linuxdoom`, 16 of them with 10 or more functions, holding 98% of the clustered functions**, stable across seeds (ARI median 0.78), far above a degree-preserving null (z 62), and **agreeing with the hand-written taxonomy** (NMI 0.52 against a permutation 95th percentile of 0.08; ARI 0.35).

**What this does and does not show.**
* About 16 groups is a natural resolution for `linuxdoom` at the default setting, but the count depends on resolution (11 groups at 0.5, 16 at 1.0, 24 at 2.0, among groups of 10 or more). "Exactly 16" is a setting, not a law; "roughly 11 to 24 depending on resolution, 16 at the default" is the honest statement. Larger ports give more groups (13 to 34 of 10 or more).
* Stability is a property of any call graph, not of DOOM: unrelated programs and from-scratch rewrites cluster almost as stably (controls 0.65, ports 0.75; `nginx` 0.62, `curl` 0.65, `lua` 0.58, `helion` 0.71). Agreement with source files is likewise high everywhere (NMI 0.42 to 0.62 except `gore`). So call-graph communities reflect how any program is organised. Whether a *port* preserves *DOOM's* architecture is a separate question (stage 2).
* Stability falls with graph size: `odamex` (7,886 functions) 0.53 fails the 0.60 bar; the other nine ports pass.
* The article's own figure used a different, weaker clustering and should be regenerated with a standard method before it is described as discovered subsystems.
