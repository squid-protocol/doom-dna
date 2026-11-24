| Quantity | ORIGINAL (704cb35f0) | NEW ENGINE (beb46cfbc) | change | real by the pre-stated rule |
|---|---:|---:|---|---|
| Programs with detectable descent at the 2% floor (struct), of 51 | 25 | 27 | changed | REAL (crossed: doomretro, gzdoom) |
| Programs with detectable descent at the 2% floor (names), of 51 | 41 | 41 |  | no (crossed: none) |
| Nearest-is-family, corrected rule, struct, common set (orig 25) | 0.619 | 0.565 | changed | no (orig exact CI 0.38 to 0.82 on 13/21) |
| Nearest-is-family, corrected, struct, own detectable set | 0.619 | 0.565 | changed | no (orig exact CI 0.38 to 0.82 on 13/21) |
| Nearest-is-family, corrected, names, common set | 0.714 | 0.652 | changed | no (orig exact CI 0.29 to 0.96 on 5/7) |
| Nearest-is-family, corrected, names, own detectable set | 0.600 | 0.600 |  | no (orig exact CI 0.15 to 0.95 on 3/5) |
| Nearest-is-family, old root-sibling rule (inflated), struct, common | 0.762 | 0.696 | changed | moved |
| Nearest-is-family, old root-sibling rule (inflated), names, common | 0.714 | 0.696 | changed | no |
| Declared parent rank, mean, struct, common | 8.570 | 9.200 | changed | moved |
| Declared parent rank, median, struct, common | 3.800 | 4.500 | changed | moved (>= 0.5 rank) |
| Declared parent rank, median, names, common | 2.000 | 2.000 |  | no |
| Resolved-triplet compatibility with declared tree, UPGMA struct | 0.848 | 0.763 | changed | moved |
| Resolved-triplet compatibility with declared tree, UPGMA names | 0.869 | 0.849 | changed | no |
| Clade recall (declared clades recovered), UPGMA struct | 0.200 | 0.200 |  | no |
| Names tree vs structure tree, UPGMA quartet distance | 0.177 | 0.180 | changed | no |
| Names tree vs structure tree, UPGMA normalised RF | 0.579 | 0.667 | changed | moved |
| Programs detectable under both (M4 set) | 22 | 24 | changed | set size follows detectability |
| Spearman shared-names vs shared-structure, all 1,275 pairs | 0.401 | 0.413 | changed | no |
| H7.2: Spearman, C-family pairs above floor under both | 0.809 (n=112, [0.596, 0.930]) | 0.862 (n=111, [0.742, 0.941]) | changed | no (inside original interval) (verdict: interval includes values below 0.80 in both) |
| H7.1: ports where structure is closer to text survival (exact+near), of 22 | 21/22 | 21/22 |  | no (orig exact CI 0.77 to 1.00) |
| H7.1 on exact+near+derived | 19/22 | 19/22 |  | no (orig exact CI 0.65 to 0.97) |
| Spearman vs name-blind text survival, structure | 0.865 [0.611, 0.975] | 0.86 [0.608, 0.970] | changed | no (inside original interval) |
| Spearman vs name-blind text survival, names | 0.928 [0.775, 0.977] | 0.928 [0.775, 0.977] |  | no (inside original interval) |
| H7.4: false attachments among large unrelated controls, structure | 1 | 1 |  | no |
| H7.4: false attachments among large unrelated controls, names | 1 | 1 |  | no |
| H7.3: cross-language ports struct leaves undetected that attach to a declared family under names | 2/6 | 2/6 |  | see scorecard |
| Phase B positives attached to a family member (structure), of 5 | 3/5 | 3/5 |  | no |
| Phase B false attachments, negatives >= 150 functions (structure), of 3 | 0/3 | 0/3 |  | no |
| Phase B correct placements, 14 scored (structure) | 11/14 [0.49, 0.95] | 12/14 [0.57, 0.98] | changed | no (inside original CI) |
| Phase B positives attached to a family member (names), of 5 | 4/5 | 4/5 |  | no |
| Phase B false attachments, negatives >= 150 functions (names), of 3 | 0/3 | 0/3 |  | no |
| Phase B correct placements, 14 scored (names) | 12/14 [0.57, 0.98] | 12/14 [0.57, 0.98] |  | no (inside original CI) |
| Phase B leave-one-out, 8 mapped ports (structure) | 6/8 [0.35, 0.97] | 6/8 | changed | no (inside original CI) |
| Phase B leave-one-out, 8 mapped ports (names) | 7/8 | 7/8 |  | no |
| Scorecard H7.6 | not met. | not met. |  | no |
| Scorecard H7.7 | falsified (names higher). | not falsified. | changed | REAL (verdict flipped) |

Phase B programs whose placement changed (struct nearest | names nearest | struct verdict | names verdict):

- `iron-doom`: ('none (0.0046)', 'none (0.0142)', 'ok', 'ok')  ->  ('none (0.0045)', 'none (0.0142)', 'ok', 'ok')
- `doome`: ('none (0.0041)', 'none (0.0004)', 'ok', 'ok')  ->  ('none (0.0041)', 'none (0.0000)', 'ok', 'ok')
- `c-raycasting`: ('none (0.0085)', 'none (0.0038)', 'ok', 'ok')  ->  ('none (0.0085)', 'none (0.0085)', 'ok', 'ok')
- `goom3d`: ('curl (0.0219)', 'none (0.0038)', 'MISS', 'ok')  ->  ('none (0.0117)', 'none (0.0038)', 'ok', 'ok')
- `derp`: ('linuxdoom (0.7092)', 'linuxdoom (0.8863)', 'ok', 'ok')  ->  ('linuxdoom (0.7273)', 'linuxdoom (0.8863)', 'ok', 'ok')
- `d2k`: ('prboom-plus (0.5577)', 'prboom-plus (0.7977)', 'ok', 'ok')  ->  ('prboom-plus (0.5346)', 'prboom-plus (0.7977)', 'ok', 'ok')
- `cpp-doom`: ('none (0.0108)', 'crispy-doom (0.8982)', 'MISS', 'ok')  ->  ('none (0.0097)', 'crispy-doom (0.8982)', 'MISS', 'ok')
- `broom`: ('doom-wasm (0.4622)', 'sdl-doom (0.7798)', 'ok', 'ok')  ->  ('doom-wasm (0.4483)', 'sdl-doom (0.7798)', 'ok', 'ok')

| Amendment 2 quantity (K = 25) | ORIGINAL | NEW ENGINE | change | real |
|---|---:|---:|---|---|
| Programs detectable at floor 0.02, E7 single shuffle | 25 | 27 | changed | REAL |
| Programs detectable at floor 0.02, primary rule | 35 | 35 |  | REAL |
| Programs detectable at floor 0.02, conservative rule | 25 | 23 | changed | REAL |
| Programs detectable at floor 0.03, E7 single shuffle | 25 | 24 | changed | moved |
| Programs detectable at floor 0.03, primary rule | 30 | 30 |  | no |
| Programs detectable at floor 0.03, conservative rule | 23 | 23 |  | no |
| Programs detectable at floor 0.05, E7 single shuffle | 22 | 22 |  | no |
| Programs detectable at floor 0.05, primary rule | 23 | 23 |  | no |
| Programs detectable at floor 0.05, conservative rule | 20 | 20 |  | no |
| Programs detectable at floor 0.08, E7 single shuffle | 20 | 20 |  | no |
| Programs detectable at floor 0.08, primary rule | 20 | 20 |  | no |
| Programs detectable at floor 0.08, conservative rule | 18 | 18 |  | no |
| programs crossing the 2% floor, single | | | gained: doomretro, gzdoom; lost: none | |
| programs crossing the 2% floor, primary | | | gained: agentic-cobol-doom-cc; lost: freedoom | |
| programs crossing the 2% floor, conservative | | | gained: none; lost: doomsday, edge-classic | |
| Nearest-is-family on E7's fixed 25-program set, single | 0.619 | 0.619 |  | no (orig exact CI 0.38 to 0.82) |
| Nearest-is-family on E7's fixed 25-program set, primary | 0.619 | 0.619 |  | no (orig exact CI 0.38 to 0.82) |
| Nearest-is-family on E7's fixed 25-program set, conservative | 0.619 | 0.571 | changed | no (orig exact CI 0.38 to 0.82) |
| Nearest-is-family on each rule's own detectable set, primary | 0.560 | 0.560 |  | no |
| Nearest-is-family on each rule's own detectable set, conservative | 0.619 | 0.600 | changed | no |
| P-A1: share of active pairs with cutoff above zero (primary) | 0.989 of 352 | 0.991 of 334 | changed | no |
| Stability classes among active pairs (stable-certified / stable-uncertified / unstable) | 156/116/80 | 149/104/81 | changed | descriptive |
| Convergence K=12 vs K=25 (share of active pairs differing by > 2% of elig_q; bound 5%) | 0.020 | 0.042 | changed | no |
| P-A4: largest share of an unrelated control with any program (primary), bound 0.10 | 0.028 | 0.030 | changed | no |
| Cross-language background (primary): 95th / 99th percentile / max, share above 0.02 | 0.010 / 0.025 / 0.083, 0.020 | 0.010 / 0.022 / 0.085, 0.016 | changed | descriptive |

Ports whose share with `linuxdoom` under the primary rule moved by at least 0.03 (`material` by the pre-stated rule):

- none
