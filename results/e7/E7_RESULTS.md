# DOOM-E7 results: names vs structure for tracing ancestry, with negative controls and a withheld set

Registered 2026-11-22 14:47 EST ([protocol](../../preregistration/E7_THREE_TREES.md), [Amendment 1](../../preregistration/E7_AMENDMENT_1.md)). Phase A (51 map programs) was frozen and pushed at 15:13 EST (commit `7439016`) before any withheld program was loaded. Engine `704cb35f0`, sfs `bcd3cb7`, `spec_hash f5d525ed16bc91db`. Full tables: [phaseA_report.md](phaseA/phaseA_report.md), [phaseB_report.md](phaseB/phaseB_report.md). **These numbers replace the earlier lineage, twin-survival and descent figures** (the 74% nearest-is-family, 93%/65% twin precision/recall).

All of the numbers below were produced by the registered rules. Where I found a defect in a registered rule, it is listed in "Defects and post-hoc items" and **not** corrected in the numbers.

## The four questions

**1. Can function names recover ancestry independent of what ports declare?** Yes, broadly. On the 25 programs both methods detect, the corrected nearest-is-family rate under names is **0.71** (structure **0.62**), against a within-language shuffle null of about **0.24**. Names detect descent for 41 of 51 programs; structure for 25.

**2. Is the name-blind scanner better or worse than names?** It depends on what is asked, and the answer is split.
- **Level of shared code (calibration): structure is better.** Against the name-blind text arbiter, structure is closer in **21 of 22** same-language ports (95%, exact 95% CI 0.77 to 1.00). Names overstate: Doom Retro keeps 63% of linuxdoom's names but 0.3% of its code by text; Crispy Doom 83% of names, 23% of code.
- **Rank order of ports: names are as good or slightly better.** Spearman against text survival: names 0.93 (95% CI 0.78 to 0.98), structure 0.87 (0.61 to 0.98).
- **Translations: names win where structure fails.** `cpp-doom` (C++ fork of Crispy Doom) shares 0.0003 structure with `crispy-doom` but 0.898 by names. `gore` (Go) has no structural descent but its nearest by names is `doomgeneric` (0.77).
- **False attachment: structure is cleaner.** From-scratch rewrites share DOOM's function vocabulary: names attach `room4doom` (0.15), `fsharp-doom` (0.11), `fps-cob` (0.09) and `helion` (0.06) to DOOM ports. Structure attaches none of them.

**3. How do the three trees differ, and do the two measured methods agree?**
- The declared tree is almost a star: 7 resolved clades (19 programs hang directly off `linuxdoom`). Against it, both measured trees satisfy about **85% of resolved triplets** (structure 0.848, names 0.869; shuffle null 95th percentile about 0.52) but recover only **1 of 5 declared clades**. Both are far above chance on ordering and weak on the deep clades.
- The two measured trees agree substantially: normalised bipartition distance **0.58**, quartet distance **0.18** on the 22 programs detectable under both; the distance is below the 5th percentile of the null.
- Pair level: Spearman between shared-names and shared-structure is **0.40** over all 1,275 pairs, **0.81** (cluster-bootstrap 95% interval 0.60 to 0.93) over C-family pairs above the floor under both. Names find 379 pairs that structure does not; structure finds 5 that names do not.

**4. Do the withheld programs place as expected?** Mostly, with two instructive exceptions. See Phase B below.

## Phase A numbers you can cite

| Quantity | Structure | Names |
|---|---:|---:|
| Programs with detectable descent (2% floor), of 51 | 25 | 41 |
| Nearest-is-family, corrected rule, common 25 | 0.62 | 0.71 |
| Nearest-is-family, old root-sibling rule (inflated) | 0.76 | 0.71 |
| Declared parent rank, median (all edges, common) | 3.8 | 2.0 |
| Resolved-triplet compatibility with declared tree (UPGMA) | 0.848 | 0.869 |
| Ports where method is closer to text survival (of 22) | 21 | 1 |
| Spearman vs name-blind text survival | 0.87 | 0.93 |

**The corrected family rule matters.** Under the old rule that counted two ports sharing only the `linuxdoom` root as siblings, structure's nearest-is-family was 0.76, close to the 74% quoted earlier. Under the corrected rule it is 0.62.

**Negative controls.** The unrelated C/C++ controls (`nginx`, `leveldb`, `curl`, `libuv`) attach to nothing under either method. `quake` and `quake2` attach under structure at 0.020 and 0.024, just above the floor (to `fastdoom` and `doom-ios`), and under names at 0.015 and 0.000 (both below the floor). `lua` attaches to `srb2` (structure 0.093, names 0.203) because **SRB2 vendors Lua** (`src/blua/`): that is real shared code, not a false positive.

## Phase B: the 15 programs placed on the frozen map

Pairwise nearest neighbour, iron-doom excluded as a diagnostic, floor 2%.

| | Structure | Names |
|---|---:|---:|
| Positives attached to a declared-family member (5) | 3 | 4 |
| False attachments, negatives with at least 150 functions (3) | 0 | 0 |
| Correct placements, 14 scored (exact 95% CI) | 11 (0.49 to 0.95) | 12 (0.57 to 0.98) |
| Always-never-attach baseline | 9 of 14 | 9 of 14 |
| Leave-one-out, 8 mapped ports (exact 95% CI) | 6 (0.35 to 0.97) | 7 (0.47 to 1.00) |

- `derp`, `d2k`, `broom` place correctly under both. `cpp-doom` places under names only (structure cannot see through C to C++).
- `cydoomgeneric` is scored a miss by both methods **only** because its top match, `sdl-doom`, is not a declared relative of `doomgeneric`. It shares 0.890 (structure) and 0.949 (names) with `doomgeneric`, within 0.02 of `sdl-doom`.
- `iron-doom`, `doomarkable`, `doome`, `DOOM-style-Game` and the non-DOOM controls attach to nothing, matching the E5 result. `goom3d` (structure) and `c-raycasting2` (names) attach just above the floor but have under 100 functions.

## Scorecard against the registered predictions

| | Prediction | Result |
|---|---|---|
| H7.1 | Structure closer to the name-blind text arbiter in at least 75% of ports | **Met**: 21 of 22 |
| H7.2 | Spearman of shared-names vs shared-structure at least 0.80 (descriptive) | Point estimate 0.81, interval 0.60 to 0.93 (**interval includes values below 0.80**) |
| H7.3 | At least a third of structure-undetected cross-language ports attach to a declared family member under names | **Met, borderline**: 2 of 6 |
| H7.4 | Structure shows 0 false attachments among large unrelated controls; names at least 1 | **Not met as registered**: structure 1, names 1; the one case is `lua` to `srb2`, a real vendored copy |
| H7.5a | M1 above the within-language null's 95th percentile | **Met** for both (0.62 and 0.71 vs 0.24) |
| H7.6 | Structure places every positive and has no false attachment among large negatives | **Not met**: 3 of 5 positives |
| H7.7 | Names' correct-placement count not above structure's | **Falsified**: 12 vs 11 (names higher, within the wide interval) |

## Defects and post-hoc items (not applied to the numbers above)

1. **M8 "generic key" rule is defective.** A key present in at least 10 of the 51 map programs is called generic, but 33 of the 51 are DOOM ports, so DOOM's own vocabulary is called generic and rule 1 fires on every DOOM pair. The M8 table is not usable.
2. **No de-duplication of eligible functions.** 99% of `puredoom`'s eligible functions and 78% of `mood`'s are exact duplicates inside the repo; structure's one-to-one matching finds almost nothing between them (`puredoom` and `mood` share 0.0001 structure but 0.91 by names, and the name figure counts duplicate copies by multiplicity). Both methods are affected, in different directions.
3. **Vendored code is kept** (registered), so `lua` in `srb2` counts as an attachment.
4. **Rooted NJ at linuxdoom is not determined by the data** (linuxdoom is itself a sampled ancestor); the rooted NJ rows are reported and not interpreted. Post hoc, NJ was also run on the detectable programs only.
5. **The declared tree is nearly a star** (7 resolved clades), so clade and triplet scores say little about deep structure.
6. **Anchor leniency**: placing a program with anchor `linuxdoom` counts any DOOM descendant as correct.
7. **Name-blind arbiter** found more surviving code than the old name-gated one (Chocolate Doom exact+near 0.43 vs about 0.33 to 0.35), as the design review predicted.

A dated Amendment 2 is needed before any of items 1 to 3 changes a number. Until then the figures above are as registered.

## What this changes for the article

- Replace the 74% and the 93%/65% with the figures above.
- Say that **names and structure measure different things**: names track a port's vocabulary and its function names across rewrites; structure tracks code. Names overstate code inheritance but follow translations; structure is better calibrated but blind to translations and to heavily duplicated repos.
- Do not claim "structure tracks ancestry better". The registered wording is "agrees with the declared lineage" and "agrees with name-blind text survival of linuxdoom code".
- The case for the name-blind tool is the **negative controls and the calibration**, not a lineage-recovery advantage: names attach DOOM's vocabulary to unrelated rewrites, structure does not.

Provenance: `RUN_PINS.json`, `phaseA/MANIFEST.sha256` (174 files, committed before Phase B), `phaseB/MANIFEST.sha256`.
