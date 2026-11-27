# E18 (DRAFT v1, 2026-11-27): DoomGraph v0, a cross-port meta layer, and what it can predict

**Status: DRAFT; two independent reviews and a dated reconciliation before any hold-out score is computed.** Schema: `doomgraph/SCHEMA.md`.

## Question
Can the layers we already hold for Doom's ports (structure, matches, lineage, call counts, lesion phenotypes) be merged into one graph of **ortholog groups** such that holding out one layer for one port and predicting it from the rest works well? The prediction accuracy is the measurable value of the graph; a database whose layers do not predict each other would be a catalogue, not a model.

## Build (deterministic, versioned)
* Instances from the scans; match edges from the E12 pair files, name-agree and E7 text-arbiter edges; **ortholog groups** by reference-anchored clustering (an instance joins the group of its best-scoring anchor in the reference engines when the evidence chain is consistent, with conflicts and many-to-many cases kept as flagged group members, never silently merged). The clustering rule and confidence thresholds are frozen by commit before any hold-out score is computed.
* Layers ingested as in the schema, with the E15 hot/inert masks verbatim. **Mocha and gore lesion outcomes are excluded** until E17's analysis is frozen and read.

## Hold-out tasks (each leave-one-port-out; the held-out port's own layer value is removed from the graph before prediction)
* **P1 (primary): phenotype from the neighbours.** For chocolate-doom, managed-doom and prboom-plus functions, predict the function's lesion-effect family profile and its hot/inert class from the **same ortholog group's phenotypes in the other screened ports** plus its call-graph neighbours. Score: agreement with the actual phenotype (the E15 distance D to the held-out truth; top-5 recovery of the function among group candidates; hot/inert accuracy and AUC). Baselines: group-size prior, name-only partner phenotype, the call-count profile nearest neighbour, and a random-group control.
* **P2: edge validity.** Predict whether a match edge is behaviourally confirmed from structural features, tier, neighbourhood agreement and group context (the SFS confidence score is the baseline to beat), scored by AUC within tier.
* **P3: link prediction.** Hide 10% of match edges between a port and its reference; recover them from the rest of the graph (group evidence and call-graph neighbourhood); score hit@1 and hit@5 against random and name-agree baselines.
* **P4 (descriptive): conservation.** Report per ortholog group: the number of ports present, divergence, lineage depth and behavioural conservation, and the share of groups with at least one behaviourally divergent instance.

## Thresholds (fixed now)
* **P1 passes** if the held-out family profile is within the E15 5th-percentile distance of the truth for at least **30 percentage points more** of the functions than the best baseline, with a cluster-bootstrap (clusters = ortholog groups) lower bound above 0 and at least **60** groups scored.
* **P2/P3** are reported against their baselines with intervals; no pass/fail beyond a stated lift of 0.05 AUC for P2.
* **Uninterpretable:** fewer than 60 scorable groups, group construction instability (membership changing by more than 10% under a different anchor), hold-out leakage found in an audit, or results carried by one subsystem.

## Controls
Shuffled group labels; hold-out of a different layer to confirm no label leakage; an anchor-swap (chocolate-doom vs linuxdoom); a leave-lineage-out version (hold out a whole fork family) because forks share code.

## Limits
One program; groups are built from the same match evidence the baselines use, so P3 is partly circular and is reported as such; faithful ports dominate the screened layers (E17 adds divergent ones later); behavioural truth exists only for screened ports.
