# `DOOM-E8b` Amendment 3 (2026-11-22): registration record

**Registered 2026-11-22 18:51 EST by the commit that adds this file, before any E8b port-versus-progenitor measurement.** Design: [E8B_PROGENITOR.md](E8B_PROGENITOR.md), [Amendment 1](E8B_AMENDMENT_1.md) (two reviews reconciled), [Amendment 2](E8B_AMENDMENT_2.md) (pins resolved from the clones). Engine `704cb35f0`, sfs `bcd3cb7`, `spec_hash f5d525ed16bc91db`, the E7 name key, stoplist and twin rules, unchanged.

## Committed before measurement

* Pins and precondition table: `manifest/e8b_pins.csv`, `manifest/e8b_precondition.csv`, search log `manifest/e8b_progenitor_search.md`.
* Scripts with tests (36 passing): `measure/e8b_scan.py`, `e8b_precondition.py`, `e8b_measure.py`, `e8b_analyze.py`.
* Outcome-neutral results already computed (progenitors against linuxdoom only, no port data): `results/e8b/pre/decomposition_summary.csv` (unchanged inherited / modified inherited / novel counts for the 8 progenitors, both rule variants) and `results/e8b/pre/validation.csv` (the generalised pipeline reproduces E8's linuxdoom numbers with zero difference on six snapshots).

## What the scripts do that the design left open (disclosed, fixed here)

* **Paired advantage.** The analysis bootstraps A over the **port snapshot's functions** (`p_in_R`, `p_in_LD`); the point value of A uses survival counted over the **reference's** functions. They agree in expectation but not exactly (a port function twinned to two reference functions counts once). The pass rule uses the point A with the paired interval.
* **Common-denominator set** = linuxdoom functions that twin a progenitor function, plus those sharing an E7 name key with a progenitor function classed modified by name; text-only modified functions have no linuxdoom function and are not in it.
* `age_years` in the measurement output is days since the **progenitor filter date** (Boom and MBF: 1999-12-31); the port-origin age is `age_port_years`.
* **Function-level de-duplication** sensitivity is implemented (one representative per exact-digest group on both sides) for subset `all` of the primary references; the `dup_share` at most 0.25 variant is also reported.
* PrBoom 2.5.0 (a release mirror dated 2026) leaves no usable snapshot under the date rule; it is a descriptive sibling and may produce no rows.
* The decomposition's `unchanged inherited` counts for SMMU (16 of 1,749) and EDGE (1 of 6,805) are low, which is what the E7 twin rule returns for heavily rewritten or C++ code; the carry-over gate uses the progenitor-novel subset, and both rule variants are reported.

## Order from here

Run `e8b_measure.py run` (stages: main, controls, classA, arbiter, ranking), commit the output manifest hashes, then run `e8b_analyze.py`; both are fixed above. Any later change to a rule needs a dated amendment.
