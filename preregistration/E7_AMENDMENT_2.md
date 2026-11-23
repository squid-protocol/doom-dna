# `DOOM-E7` Amendment 2 (2026-11-23): pooled multi-decoy cutoff for the structure arm

**Status: RECONCILED; becomes REGISTERED by the commit that adds this file in this form, before any full replicated run.** Supersedes only the structure-arm cutoff rule and the sections it names in [E7_THREE_TREES.md](E7_THREE_TREES.md) and [Amendment 1](E7_AMENDMENT_1.md); the rest stands. The E7 numbers as registered stay on record as "single shuffle".

## A. The problem (found after E7, in DOOM-E10 part 2)

The structure arm certifies a function twin when its distance is below a per-pair cutoff set by target-decoy competition (sfs `twins.py`): the target's functions are shuffled within engine archetype into a decoy, and the cutoff is the largest distance at which `(decoy hits + 1) / real candidates` stays at or below 1%. **E7 drew that decoy once per pair.** The `+1` is the single-decoy finite-sample correction, so a pair needs about 100 candidate twins before anything is certified; near that margin the answer depends on whether one random draw has zero early decoy hits, and the cutoff flips between a working value (about 0.06) and zero.

Evidence (E10 part 2, `flip_seeds.csv`, 30 shuffles on E7's scans): `chocolate-doom`, `crispy-doom` never collapse; `woof`, `dsda-doom`, `srb2`, `gzdoom`, `odamex` and the unrelated controls collapse in 30 of 30; `inter-doom` (20 of 30), `prboom-plus` after normalisation (14 of 30) and `fastdoom` (4 of 30) depend on the draw. The names arm was given 200 Monte Carlo draws for its pair-level chance test; this is not the same kind of quantity (see §F), but the structure arm had no replication at all.

## B. The rule (replaces the single-shuffle structure matrices)

1. For every ordered Phase A pair, the real twin search is computed once; **K = 100** decoy shuffles are drawn (seeds 0..99; seed 0 is E7's original shuffle). Implementation: `measure/e7_draws.py`; seed 0 is tested to reproduce `find_twins` exactly.
2. **Primary cutoff (pooled multi-decoy TDC):** with `n_t(d)` the real distinctive reciprocal candidates at or below `d` and `n_d,k(d)` the decoy hits of shuffle `k`, `FDR_K(d) = (1 + sum_k n_d,k(d)) / (K * n_t(d))`; the cutoff is the largest `d` whose monotone (q-value) estimate is at or below 0.01, as in sfs. This reduces to E7's rule for K = 1. Exact-clone bypass (loc at least 12, unique key) is unchanged. The twin set at that cutoff is one deterministic table per ordered pair.
3. **Conservative sensitivity (S1):** the same pooled counts with the full `+1` kept on the mean count, `FDR(d) = (mean_k n_d,k(d) + 1) / n_t(d)`. This keeps E7's "about 100 candidates" gate.
4. **As registered (S2):** E7's single-shuffle table, unchanged. **(S3):** the mean over the 100 single-shuffle shares (descriptive; it carries no FDR claim).
5. **Downstream artefacts are regenerated, not patched.** For each of the primary and S1 rules, a separate work directory is built with: `pairs_struct.csv` (E7's columns, from the twin set at that cutoff, `wilson` = the Wilson lower bound of (twins, elig_q) as in E7), `linuxdoom_twin_presence.npz` (which M6 and H7.1 read), the E7 names tables (unchanged), the text arbiter output (layout-independent, reused), and E7's phase A fingerprints. **`e7_analyze.py` is then run unchanged on each directory**, so every quantity it prints is recomputed, including M1 to M8, H7.1 to H7.3, H7.4 and H7.5a. The 2% detectability floor is applied exactly as E7 applies it (to the symmetric Wilson lower bound).
6. Directions: both ordered directions are computed per pair; E7's symmetrisation (`max` over the two directions) is applied to the Wilson bounds after the cutoff, as E7 did.
7. **Diagnostics for the supplemental figure (not used in any test):** per ordered pair, the single-shuffle certified fraction `c` (share of the 100 shuffles with cutoff above zero), the 10th, 50th and 90th percentile single-shuffle share, and `c` classes (`stable-certified` at `c >= 0.9`, `stable-uncertified` at `c <= 0.1`, otherwise `unstable`). A pair with `c = 0` can still show an exact-clone floor, so a stable-uncertified pair is **below what the rule can certify**, not absent.

## C. Convergence and robustness (pre-stated)

* **Convergence:** cutoffs at K = 50 (seeds 0..49) and K = 100 are compared per pair; the median absolute difference and the share of pairs whose twin count differs by more than 2% of `elig_q` are reported. K = 100 is judged adequate if that share is at most 5% of active pairs.
* **A conclusion is called robust** only if it holds under both the primary rule and S1. A conclusion that holds only under the primary rule is reported as "depends on the multi-decoy correction".
* Tree stability: UPGMA and NJ trees from the primary, S1, S2 and S3 matrices are compared (Robinson-Foulds and quartet distance) and shown.

## D. Predictions (written before any full replicated run)

Disclosure: this amendment was written **after** seeing E7 and E10 part 2, including the 30-shuffle `linuxdoom`-to-port table and a development run of K = 100 pooled and conservative cutoffs on 13 `linuxdoom`-to-port pairs (`inter-doom`, `prboom-plus`, `fastdoom`, `woof`, `dsda-doom`, `srb2`, `gzdoom`, `odamex`, `nginx`, `libuv`, `quake2`, `chocolate-doom`, `crispy-doom`). Predictions about those rows are partly known; the confirmatory content is the other pairs and the derived quantities. This is exploratory in status and the primary endpoints are Holm-corrected as P-A1 and P-A5 only.

* **P-A1 (primary):** under the primary rule the cutoff is above zero for at least 90% of active ordered pairs (share at least 0.02 under either S1 or the primary), against E7's single-shuffle collapse.
* **P-A2:** the stably high pairs (`chocolate-doom`, `crispy-doom`, `doom-wasm`, `sdl-doom`, `doom-ascii`, `doomgeneric` against `linuxdoom`) change by less than 0.03 from E7.
* **P-A3:** the previously low or unstable ports (`woof`, `dsda-doom`, `srb2`, `prboom-plus`, `doom-ios`, `inter-doom`, `fastdoom`) rise by at least 0.03 under the primary rule relative to E7's single shuffle (known for the `linuxdoom` row from development data).
* **P-A4 (controls):** the unrelated C and C++ controls (`nginx`, `leveldb`, `curl`, `libuv`) stay at or below 0.10 against every DOOM port; the same-studio `quake` and `quake2` and `lua` (attached to `srb2` in E7) are reported separately.
* **P-A5 (primary):** on the fixed set of the 25 programs that E7 called structurally detectable, structure's nearest-is-family rate (E7 0.619) changes by less than 0.10 under the primary rule, and H7.1 (structure closer to the text arbiter in at least 75% of same-language ports) remains met.
* **P-A6:** the number of structurally detectable programs (2% floor) rises from 25 to at least 30 under the primary rule.
All metrics are also reported on the fixed 25-program set as well as the program set each rule detects, so changes in the scored set are not confused with changes in the data. A failed prediction is reported as failed.

## E. Supplemental figure (specified now)

Figure S-A, built by script from the raw table, no manual editing: (a) for each port (rows, ordered by primary share with `linuxdoom`), the distribution of the single-shuffle share across the 100 shuffles, with E7's single value, the S1 value and the primary value marked, the 2% floor drawn; (b) the certified fraction `c` per port; (c) a second `linuxdoom`-to-port panel for one direct parent-child pair as a stable reference.

## F. Limits

* The pooled rule is a standard multi-decoy generalisation, not a new method; K independent decoys of the same target are correlated through the shared target, so the multi-decoy `1/K` correction is the usual approximation. S1 is the conservative bound.
* The 1% FDR claim belongs to the cutoff rules (primary and S1); S3 (mean share) and the percentile diagnostics are descriptive and carry no FDR claim.
* The names arm uses a 200-draw Monte Carlo pair-level p-value on an external vocabulary and keeps no function when uncertified; structure certifies function by function and keeps exact clones. The two are comparable in "replicated-null effort", not identical. A secondary check reruns the names chance control with a second seed and reports how many certified pairs change.
* Singleton archetype strata are never shuffled (`_decoy`), and shuffling within archetype is unchanged by this amendment.
* Only Phase A is recomputed. Phase B (withheld) stays under E7's registered single-shuffle rule and is therefore not directly comparable until a later amendment applies the same rule to it.
* The scanner commit actually used by E7 and by this amendment is `b1a9e92`; E7's `RUN_PINS.json` names `bcd3cb7`, which differs only in `cli.py`, `lattice.py` and `port_evidence.py`, not in the matching code. This is recorded here and not edited in the pins.
* Normalised scans (E10 part 2) are not re-estimated here; the rule can be rerun on them as a stated sensitivity.

## G. Reviews and reconciliation (two independent design reviews, Claude subagent and Gemini `gemini-4-neon-high`)

Both reviews rejected the median of 100 single shuffles as the summary: the quantity is bimodal at the cutoff cliff, the median jumps at `c = 0.5`, can deterministically collapse a pair that a single shuffle would certify 45% of the time (Gemini's Poisson example), and carries no FDR meaning. **Adopted:** pooled multi-decoy TDC as primary (Gemini), the conservative `+1`-kept variant (Claude's averaged-decoy suggestion) as S1, the mean share as descriptive S3. Tested on development data before registration: pooled-100 cutoffs came out between 0.03 and 0.065 for every port with enough candidates and unrelated controls stayed low; S1 reproduces E7's collapsed values.
Also adopted (both): the claim that `e7_analyze.py` runs unchanged was wrong in three ways (M6 and H7.1 read `linuxdoom_twin_presence.npz`, the file name and `wilson` column are read, H7.4 and H7.5a omitted); fixed in §B.5. Predictions P-A2 to P-A4 as first drafted were circular or already contradicted by the 30-shuffle data and are replaced (§D). Class thresholds now serve only diagnostics, with the exact-clone floor stated (§B.7). The names-arm symmetry sentence is reworded (§A, §F). Disclosure of seen data, fixed-program-set reporting, convergence check, tree stability, the pin discrepancy and the Phase B limit are added.
Declined: promoting E8's per-port pooled cutoff to co-primary (it pools across different pairs and is a different estimand); it remains a descriptive extra. Claude's suggestion of the 10th-percentile share as the lower bound is not needed once the Wilson bound is taken at a fixed cutoff.

## H. Amendment 2a (2026-11-23, before any full replicated result was read): K = 25

The owner cut the run time. A full K = 100 run was started and **stopped after 200 of 2,550 pairs, with nothing read** (outputs are written only at the end; none existed). Replacing K = 100 by **K = 25** (seeds 0..24; seed 0 is still E7's draw).

Basis, measured on development data only (`linuxdoom` against `inter-doom`, `prboom-plus`, `fastdoom`, `woof`, `dsda-doom`, `srb2`, `crispy-doom`; 300 random K-subsets of 100 shuffles per K): the spread (SD) of a port's share under the pooled rule falls as about `0.025 / sqrt(K)`: K = 1 0.025 (up to 0.058), K = 5 0.012, K = 10 0.008, K = 25 0.004, K = 50 about 0.002 (an underestimate, because K-subsets of 100 overlap). At K = 25 the noise is about 4% of a share of 0.10, below the noise from which programs were sampled.

Changes to §B and §C only: K = 25 replaces K = 100 everywhere; the convergence check compares K = 12 (seeds 0..11) with K = 25 instead of K = 50 with K = 100, with the same adequacy bound (twin count differing by more than 2% of `elig_q` in at most 5% of active pairs). The `+1` of the conservative variant (S1) becomes `+K` with K = 25. §D predictions, §E figure and everything else stand. The figure's per-pair distribution is over 25 single shuffles. Declared: the K = 100 development numbers quoted in §G came from the same seven-to-thirteen dev pairs and are unaffected.
