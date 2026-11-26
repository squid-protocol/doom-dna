# E15 (DRAFT 2026-11-26): a mutant screen defines function roles; do roles form call-graph neighbourhoods that recur across ports?

**Status: DRAFT.** Must be reviewed twice (a Claude subagent and Gemini, read-only, blind to results), reconciled in a dated section, informed by the literature review (`docs/notes/LIT_REVIEW_MUTANT_SCREEN.md`, running), and committed before any result of the screen is read. **Disclosure:** the screens of chocolate-doom (1,843 lesions) and managed-doom (2,087 lesions) were started before this registration; their result databases have **not** been read or queried beyond job counts. Tooling validation (`mscreen/`: zero-lesion replay identical on all 42 demos; lesion switch identical to classical rebuild in 67/70 C and 20/20 C# samples; the three C differences are build-dependent break tics, not kill sets) used no phenotype analysis.

## Background and idea
Forward-genetics logic: lesion every function in small ways, assay with deterministic demo replay, and define a function's **role** by the **phenotype** of breaking it. The 42 demos are a **shared coordinate system** across ports, so lesion phenotypes from different engines can be compared directly, without first matching functions by name or structure.

## Owner's prediction (the headline)
**The screen reveals a modest number of groups of lesions (phenotype classes); each group's host functions form tight neighbourhoods in the call graph (not merely the same source file); and the same groups recur across ports and translations.**

## Definitions
* **Lesion phenotype (pi):** for each of the 42 demos: unreached (the function is never entered; exactly no effect), same, or killed with the first diverging tic and the first diverging state class (player, monster/world, sector, keys, RNG). Crash/hang is a separate outcome. Comparisons use the common columns, strict and dead-angle-ignoring both stored (dead-angle-ignoring primary).
* **Lesion similarity:** Jaccard of the failing-demo sets restricted to demos reaching both host functions, with first-class agreement as a secondary term; the 0/0 case (both survive) is excluded from clustering ("silent lesions" are reported and **never** counted as agreement).
* **Function phenotype:** the vector over demos of the fraction of the function's non-silent lesions that kill it, plus its state-class distribution and its reach profile (entries per demo from the clean profile).
* **Groups:** lesion clusters from average-linkage hierarchical clustering on 1 - similarity, cut by the gap statistic against the registered null below, stability by bootstrap resampling of demos (Jaccard stability >= 0.7 to count as a stable group).
* **Neighbourhood:** static call graph from the scanner database (confident edges, undirected, distance capped at 6), **and** a dynamic co-entry graph (functions entered in the same demos at similar rates) reported separately.

## Hypotheses and predictions (thresholds to be tightened at review)
* **H1 (structure of phenotype space).** Lesion phenotypes are not a continuum: a stable grouping exists with k between **6 and 25** groups for chocolate-doom (basis: DOOM's simulation has roughly a dozen subsystems: monster chase/attack/look, projectile/missile, movement and collision, blockmap/geometry, sight, door/floor/ceiling/platform/light specials, teleport, weapons/player, damage/interaction, spawn). The gap statistic exceeds its null at the chosen k, and >= 70% of lesions fall in stable groups.
* **H2 (neighbourhoods).** Hosts of a group are close in the call graph: for groups with >= 5 host functions, mean pairwise call distance is lower than for matched random function sets (matched on size and reach count) in >= 60% of groups at FDR 0.05, **and** still lower than for random sets drawn from the same source files in >= 40% of groups (so the effect is not only file locality). Reported: conductance/modularity of each group in the call graph against degree-preserving rewired graphs.
* **H3 (recurrence across ports).** Phenotype classes recur: for managed-doom (C#), >= 70% of chocolate groups have a mutual-best-match group whose centroid similarity exceeds the null (centroids compared in demo space; null by permuting demo labels), and among function pairs that agree by name (the E14 agree stratum extended to all reached functions) the normalised mutual information of group memberships across the two ports is >= **0.5** against a label-shuffled null.
* **H4 (role matching recovers known orthologs).** Nearest phenotype neighbour across ports recovers the name-agree partner for >= **50%** of reached functions (chance < 5%); the E12 structural matcher's strong tiers (exact/twin/seed) agree with phenotype matches more often than its extension tiers (ext1-3), and the confusion matrix between structural and phenotype matches is reported (exploratory: where they disagree, who is right is decided by a registered audit of 40 random disagreements by reading both functions).
* **H5 (conserved role, diverged structure; exploratory).** Among phenotype-matched pairs, structural fingerprint distance and size ratio are only weakly related to phenotype distance (|Spearman| < 0.3); the pairs with the largest structural divergence and still-matching phenotype are listed with names.

## Positive controls (must pass or the screen is declared uninterpretable)
* **PC1 reliability:** split each function's lesions into random halves; the phenotype of one half matches the other half of the same function as top-1 among all functions for >= **70%** of reached functions with >= 6 lesions (chocolate and managed-doom separately).
* **PC2 identity ceiling:** near-clone ports (prboom-plus, crispy-doom) screened with the same pipeline: functions with identical text in chocolate recover as top-1 phenotype neighbours for >= **90%**.
* **PC3 known orthologs:** the 12 managed-doom name-agree functions from the E14 confirmatory data match their chocolate partner as top-1 for >= **70%**.
* **PC4 file recovery:** phenotype groups recover source-file structure (adjusted Rand index against files above the permutation null), establishing that the groups carry architectural information at all.
* **PC5 determinism:** the zero-lesion replay and a repeated 200-lesion sample reproduce exactly.

## Negative controls
N1 degree-preserving rewired call graph; N2 random function sets matched on size and reach; N3 permuted demo labels; N4 a decoy matcher (random one-to-one inside the same file) for H4; N5 the 15 name-disagree functions: where the matcher paired different-named functions, phenotype similarity is expected to be low (reported, not predicted strongly).

## Analysis rules
Unit of analysis is the function (cluster bootstrap over functions, 10,000 resamples); lesions inside a function are dependent. One primary per hypothesis (H2: share of groups beating the matched null; H3: NMI; H4: top-1 recovery); Holm over the five primaries; everything else descriptive. Equivalent mutants and silent lesions are tabulated per function and per file; functions with < 4 non-silent lesions are excluded from role matching and listed. Build-dependent lesions (shift and bounds lesions) are reported with and without. All analysis code is committed before any query of the result databases.

## Limits
Simulation functions only (rendering, menu, sound are not exercised by headless demos); demos reach part of each function; one-token lesions; shared inherited code in the C family (so the independent claim rests on managed-doom, and later Mocha/Kocoa/gore); functions split or merged by a port have one-to-many roles; the static call graph misses function-pointer calls (thinkers), which can understate H2 (a dynamic co-entry graph is reported in parallel).
