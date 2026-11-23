# DOOM-E11 stage 1: does a program's call graph yield stable, meaningful subsystems? (go/no-go gate)

**Status: written 2026-11-23 before any clustering was run. Exploratory gate; not registered with two design reviews.** Prompted by an examination of the article's "16-track gene map" (Claim 6, Visual 3): its `discover_communities` keeps the 15 largest communities of a one-pass local-moving heuristic and folds the rest into a 16th bucket, so the number 16 is a cap, not a finding. In `linuxdoom`, 554 of 777 functions (71%) sit in that last bucket, and re-ordering the functions changes the groups (adjusted Rand agreement about 0.5). Their agreement with the hand-written 16-subsystem taxonomy is about zero. Stage 1 asks, with a proper method, whether call-graph-found subsystems are real.

## Method
* Data: the E7 phase A fingerprints (engine `704cb35f0`): distinct resolved calls as an undirected, unweighted graph; isolated functions are excluded from clustering and reported.
* Programs: `linuxdoom` (primary); ten ports (`chocolate-doom`, `crispy-doom`, `doomgeneric`, `prboom-plus`, `woof`, `eternity`, `odamex`, `mochadoom`, `gore`, `puredoom`); controls: unrelated (`nginx`, `curl`, `lua`) and from-scratch (`helion`, `rust-doom`).
* Clustering: Louvain (networkx 3.7), the number of groups left to the data. Resolution 1.0 is primary; 0.5 and 2.0 are a sweep to ask whether about 16 groups is natural at any resolution.
* **Stability:** 30 seeds per program; median and minimum pairwise adjusted Rand index (ARI).
* **Not an artefact of degree:** best modularity against 20 degree-preserving rewirings of the same graph (z score).
* **Coverage:** number of groups with at least 10 functions and the share of clustered functions inside them.
* **Meaning:** agreement (normalised mutual information, NMI, and ARI) between the groups and (G1) source file membership, (G2) for `linuxdoom` the hand taxonomy by file-name prefix (`examples/doom/subsystems.json`), (G3) top-level directory where one exists; each against a label-permutation null (1,000 shuffles).

## Gate (pass only if all hold)
On `linuxdoom` at resolution 1.0: (i) median seed-to-seed ARI at least **0.70**; (ii) at least **70%** of clustered functions in groups of at least 10 functions; (iii) modularity above the degree-preserving null by z at least **5**; (iv) agreement with the hand taxonomy: NMI above its permutation null (p below 0.01) and ARI at least **0.30**. And on at least **8 of the 10 ports**: median ARI at least **0.60**. A fail names the criteria that failed.

## Predictions (before any run)
* **P1:** `linuxdoom` seed-to-seed ARI median is between 0.50 and 0.80 (the gate's criterion (i) is borderline or failed).
* **P2:** modularity is far above the degree-preserving null (z above 5) for every program, controls included: any sparse graph has community structure; this alone does not make the groups subsystems.
* **P3:** with Louvain at least 70% of `linuxdoom`'s clustered functions are in groups of 10 or more (unlike the script's 29% outside the catch-all).
* **P4:** NMI with file membership and with the hand taxonomy is above the permutation null, while ARI with the hand taxonomy stays below 0.30.
* **P5:** the controls cluster as stably as the DOOM ports (stability is a property of graph size and sparsity, not of DOOM's design).
* **P6:** no resolution in the sweep yields a stable (ARI at least 0.7) partition with 14 to 18 groups of 10 or more functions.
* **P7 (overall):** the gate is **not** passed on criterion (i) or (iv).
A failed prediction is reported as failed. A fail of the gate is a result, not an error.

## Limits
`linuxdoom` has 779 functions and 1,605 calls (43 isolated), a small graph; resolution limits of modularity apply. Louvain is one family of method; Leiden or stochastic block models are not tried in stage 1. Ground truths are imperfect proxies for "subsystem". Third-party source is not committed.
