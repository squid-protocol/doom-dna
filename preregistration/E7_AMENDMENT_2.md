# `DOOM-E7` Amendment 2 (2026-11-23): replicated decoy shuffles for the structure arm

**Status: DRAFT.** Becomes REGISTERED when two independent design reviews are reconciled in a section below and this file is committed before any replicated-shuffle computation. Supersedes only the sections it names in [E7_THREE_TREES.md](E7_THREE_TREES.md) and [Amendment 1](E7_AMENDMENT_1.md); the rest stands. The E7 numbers as registered stay on record, labelled "single shuffle".

## A. The problem (found after E7, in DOOM-E10 part 2)

The structure arm decides whether a twin is real from a distance cutoff set per program pair by target-decoy competition (sfs `twins.py`): the target program's functions are shuffled within engine archetype into a decoy, the cutoff is the largest distance at which decoy matches stay within 1% of real matches (with a `+1` correction, so a pair needs at least 100 candidate twins before anything is certified). **E7 draws that shuffle once per pair** (seed from the two program names). The names arm, in contrast, draws **200** decoys for its chance control (`DRAWS = 200` in `e7_run.py`). The two arms are therefore not sampled equally.

Evidence that one draw is too few (DOOM-E10 part 2, `results/e10/flip_seeds.csv`): the same E7 scans, 30 different shuffles, `linuxdoom` against each port:

* `chocolate-doom` and `crispy-doom`: the cutoff never collapses; shares vary by about 0.04.
* `woof`, `dsda-doom`, `srb2`, `gzdoom`, `odamex` and the unrelated controls: the cutoff collapses to zero in 30 of 30 shuffles (stably uncertifiable, not noise).
* `inter-doom` (20 of 30 collapsed; share 0.080 or 0.171) and `fastdoom` (4 of 30; 0.028 to 0.251): the answer depends on the shuffle. E7's single draw is one outcome of a coin flip.

## B. Replicated-shuffle rule (replaces the single-shuffle structure matrices)

1. For every ordered program pair in Phase A, run the structure twin search with **K = 100** decoy shuffles, seeds `0..99` (seed 0 is E7's original draw). The real search is computed once per pair; only the decoy changes.
2. Per pair record: the **median share** (twins / eligible query functions) over the 100 shuffles; the 10th and 90th percentiles; the **certified fraction** `c` (shuffles in which the cutoff is above zero); the median cutoff.
3. **Pair class** (fixed now): `stable-certified` if `c >= 0.9`; `stable-uncertified` if `c <= 0.1`; `borderline` otherwise.
4. **The value used in matrices, trees and every metric** (`pairs_struct.csv`, same columns as E7) is the **median share**. A new file `pairs_struct_median.csv` is written in E7's format and `e7_analyze.py` is run on it **unchanged**, so every E7 quantity (M1 to M8, H7.1 to H7.3) is recomputed. Phase B (withheld) is not part of this amendment.
5. The 2% detectability floor is applied to the median. The detectable-descent count is reported with and without borderline pairs.
6. Names arm: unchanged (already 200 draws).

## C. Predictions (before any replicated run)

* **P-A1:** at least 85% of active pairs (share at least 0.02 in either E7 or the median) are not borderline.
* **P-A2:** among stable pairs, the 10th to 90th percentile range is within 0.03 of the median.
* **P-A3:** 3 to 8 `linuxdoom` pairs have an E7 single-draw value that differs from the median by more than 0.05 (expected: `inter-doom`, `fastdoom`, and a few more).
* **P-A4:** `woof`, `dsda-doom`, `srb2`, `gzdoom`, `odamex` stay below the 2% floor at the median; the unrelated controls stay below the floor.
* **P-A5:** structure's nearest-is-family rate (E7 0.619) changes by less than 0.05; H7.1 (structure closer to the text arbiter in at least 75% of same-language ports) remains met.
A failed prediction is reported as failed.

## D. Supplemental figure (specified now)

Figure S-A: for each port (rows, ordered by median share), the distribution of `linuxdoom`-to-port share across the 100 shuffles (strip or violin), E7's single-draw value marked, the 2% floor drawn, points coloured by pair class. Second panel: the certified fraction `c` per port. Produced by a script from the raw table; no manual editing.

## E. Secondary, descriptive

* E8-style pooled per-port cutoff (`pooled_threshold` over the port's pairs) next to the median, to show whether pooling gives the same answer.
* The same replication on the DOOM-E10 normalised scans, to show the formatting result does not depend on the draw.

## F. Limits

* Replication removes **sampling noise from the shuffle**. It does not change the rule's conservatism: stably uncertifiable pairs stay uncertified, and the `+1` rule still needs about 100 candidates. Those pairs are reported as "below what the rule can certify", never as zero.
* The shuffle design (within archetype, one target function population) is unchanged.
* K = 100 gives a 95% interval on `c` of at most +-0.10 and was chosen for that, and for a cost of about four hours on this machine, not tuned on outcomes.
* The median is a summary; for borderline pairs both the median and the range are reported, and no conclusion should rest on a borderline pair alone.
