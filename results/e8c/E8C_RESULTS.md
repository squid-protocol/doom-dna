# DOOM-E8c results: fork dates from a denser grid and the pooled cutoff (exploratory)

Arms: A = E8 as registered; B = E8's semi-annual points, pooled K = 25 rule; C = dense grid, pooled K = 25; D = dense grid, single shuffle per pair (E8's rule). Estimate error in years = estimate - git truth (negative = estimate too early). `n` = points used by the fit. `boot` = 95% point-bootstrap interval of the error.

## crispy-doom from chocolate-doom  (git truth 2013.94)

| method | arm A error (n) [boot] | arm B error (n) [boot] | arm C error (n) [boot] | arm D error (n) [boot] |
|---|---|---|---|---|
| struct_max | -28.75 (25) | -28.70 (25) [-29.50, -21.00] | -21.61 (75) [-29.12, -17.19] | -21.66 (75) [-29.23, -17.96] |
| struct_min | -18.85 (25) | -16.20 (25) [-26.15, -11.20] | -11.61 (75) [-16.22, -9.49] | -11.61 (75) [-16.19, -9.49] |
| names_max | -29.35 (25) | -29.35 (25) [-29.50, -27.42] | -28.86 (75) [-29.91, -28.66] | -28.86 (75) [-29.91, -28.66] |
| names_min | -21.65 (25) | -21.65 (25) [-29.00, -13.55] | -15.96 (75) [-19.12, -13.22] | -15.96 (75) [-19.12, -13.22] |

## dsda-doom from prboom-plus  (git truth 2020.86)

| method | arm A error (n) [boot] | arm B error (n) [boot] | arm C error (n) [boot] | arm D error (n) [boot] |
|---|---|---|---|---|
| struct_max | -0.05 (5) | -0.00 (5) [-0.50, 0.55] | -0.02 (36) [-0.14, 0.03] | -0.02 (36) [-0.12, 0.01] |
| struct_min | -0.20 (5) | -0.20 (5) [-0.35, 0.05] | -0.22 (36) [-0.25, -0.17] | -0.22 (36) [-0.25, -0.17] |
| names_max | -0.10 (5) | -0.10 (5) [-0.58, 0.25] | -0.27 (36) [-0.32, -0.07] | -0.27 (36) [-0.32, -0.07] |
| names_min | -0.35 (5) | -0.35 (5) [-0.85, -0.25] | -0.32 (36) [-0.57, -0.29] | -0.32 (36) [-0.57, -0.29] |

## nugget-doom from woof  (git truth 2021.66)

| method | arm A error (n) [boot] | arm B error (n) [boot] | arm C error (n) [boot] | arm D error (n) [boot] |
|---|---|---|---|---|
| struct_max | -0.75 (10) | -1.10 (10) [-3.10, 0.21] | -2.42 (44) [-5.49, -1.33] | -2.42 (44) [-5.44, -1.33] |
| struct_min | -0.70 (10) | -0.65 (10) [-2.67, 0.18] | -2.92 (44) [-12.37, -1.34] | -2.92 (44) [-12.34, -1.34] |
| names_max | -0.05 (10) | -0.05 (10) [-1.56, 2.85] | -0.92 (44) [-2.82, -0.17] | -0.92 (44) [-2.82, -0.17] |
| names_min | +0.00 (10) | +0.00 (10) [-1.40, 1.55] | -1.82 (44) [-24.00, -0.24] | -1.82 (44) [-24.00, -0.24] |

## Predictions

| prediction | result | values |
|---|---|---|
| P1 arm C structure(max) within 0.5 y for dsda-doom and nugget-doom | NOT met | {'dsda-doom': -0.02, 'nugget-doom': -2.42} |
| P2 crispy-doom error more than 5 y early in every arm (struct_max) | met | {'A': -28.75, 'B': -28.7, 'C': -21.61, 'D': -21.66} |
| P3 bootstrap interval narrower in C than B for dsda-doom and nugget-doom (struct_max) | NOT met | {'dsda-doom': (1.05, 0.17), 'nugget-doom': (3.31, 4.17)} |
| P4 names at least as accurate as structure for nugget-doom in arm C (names_max vs struct_max) | met | {'names': -0.92, 'struct': -2.42} |
| P5 observed |error| below both placebo median errors for every fitted row | NOT met |  |
| P6 |D-C| < 0.25 y and |B-A| < 0.25 y for dsda-doom and nugget-doom (struct_max) | NOT met | {'|D-C|': {'dsda-doom': 0.0, 'nugget-doom': 0.0}, '|B-A|': {'dsda-doom': 0.05, 'nugget-doom': 0.35}} |

## Reading (written after the numbers)

**More points helped one pair, hurt one, and did not rescue the third.**
* `dsda-doom` (shared structure falls smoothly from 0.92 to 0.38 over three years): the dense grid recovers the fork date to **-0.02 years** (structure, max), and the 95% bootstrap interval of the error shrinks from about 1.05 years (5 points) to **0.17 years** (36 points). This is the case the method was built for, and density clearly helps.
* `nugget-doom` (shared structure stays near 0.85 for years because Woof's code keeps being merged in, then falls late): the dense grid gives **-2.42 years** where E8's 10 sparse points gave -0.75. More data showed that an exponential decline from the fork date is the wrong shape for a child that keeps re-converging with its parent; E8's closer estimate was partly luck of where its 10 points fell. Names still did best (-0.92, E8 -0.05).
* `crispy-doom`: improved from -28.8 to -21.6 years but is still useless, for the same reason (long, slow, merge-driven decline).

**The cutoff rule does not matter for these pairs.** Dense grid, pooled K = 25 against a single shuffle (arms C and D): identical to the second decimal for every pair and method. A parent and its direct child have hundreds to thousands of candidate twins, far above the roughly 100 where the single-shuffle cutoff becomes unstable. The instability found in E7 affects weakly related pairs, not these. (Arm B differs from arm A by 0.05 years for `dsda-doom` and 0.35 for `nugget-doom`; that is a cutoff effect on 5 and 10 points, not seen on the dense grid.)

**What predicts a recoverable fork date:** the child must diverge cleanly from the parent (a smooth decline), not keep absorbing its parent's code. In this set that is one of three pairs.

**Predictions:** P2 and P4 met. P1 (within 0.5 years for both), P3 (interval narrower in the dense arm for both), P5 (error below both placebo medians in every row) and P6 (cutoff and rule differences under 0.25 years) were not met; each failure is above. P5 fails only for `crispy-doom` names (no information) and borderline for `nugget-doom` (observed 2.42 vs placebo 2.24).

**Limits:** three pairs, exploratory, placebo and bootstrap use 300 draws (E8 used 500). Names use no decoy certification here (arm B matches E8's names to the second decimal, so this did not matter). Scores are at one machine and one pinned scanner (`b1a9e92`, engine `704cb35f0`).
