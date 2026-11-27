# E16 (DRAFT 2026-11-27): diagnosing a bug from its symptom with the lesion dictionary

**Status: DRAFT.** Needs two independent design reviews (a Claude subagent and Gemini, read-only), a dated reconciliation, the development/frozen split below, and a commit before any test-set quantity is computed. Builds on E15 (the lesion screens of chocolate-doom, managed-doom and prboom-plus, 2026-11-26/27).

## Question
Every lesion in the E15 screen is a known, small bug with a recorded symptom (which of the 77 demos change, how early, which part of the game state diverges first). If a port misbehaves, can the **symptom** point to the **function** at fault by looking it up in the reference engine's lesion dictionary? This is the idea the E13 localiser tried with call graphs and RNG callers (23% within three hops, primary prediction failed).

## Definitions (frozen by the reviews)
* **Dictionary** = all chocolate-doom lesions (7,383; ids and results of E15), each with a symptom vector over the 77 demos: for each demo where the site executes, `killed` (first diverging tic, class set of the first diverging row: player, world, sector, keys, time; RNG bit excluded) or `same`; demos where the site never executes are unobserved. A function's dictionary entries are its lesions.
* **Symptom** of a test bug = the same vector measured for the test (a lesion of another engine, or a real divergence of a port against chocolate-doom's clean digests) on the demos where it was observed.
* **Scorer** (to be frozen on the development half): similarity between a symptom and a dictionary lesion on the co-observed demos (at least 5): weighted mean of (a) agreement of the killed/same pattern (Jaccard of the failing sets), (b) agreement of the first-diverging class set, (c) closeness of first-diverging tics (rank-based). **Function score** = the maximum similarity over the function's lesions (the Metallaxis-style max rule; a mean-of-top-3 variant is a registered sensitivity). Ties count against the scorer (pessimistic rank).
* **Baselines (registered):** (B1) random ranking; (B2) **spectrum-based fault localisation on clean call coverage** (Ochiai and Tarantula on the per-demo function-entered coverage of chocolate-doom: functions entered mostly in the failing demos rank first); (B3) the E13 localiser's result (23%, depth three, reported as context only: different quantity); (B4) rank by number of demos entering the function (a popularity prior).
* **Hot and inert classes** (E15 definitions) are excluded from the candidate list and from the test bugs, and listed.

## Protocol
1. **Development half.** The 140 usable chocolate-doom functions are split by a fixed hash of the function name into development and test halves. The scorer's weights and the aggregation rule are chosen on **leave-lesion-out diagnosis inside the development half only**. Nothing from the test half, managed-doom, prboom-plus, gore or Kocoa is used. The scorer and every threshold below are then **frozen and committed**.
2. **T1 (primary): cross-engine, managed-doom.** Test bugs = managed-doom lesions that change at least 3 demos, whose host function has a **chocolate-doom counterpart** (name agrees after prefix stripping, identical call profile on all 77 demos; counterpart not hot or inert). Truth = the counterpart. The dictionary contains **all** chocolate-doom lesions of **test-half functions only** for scoring? No: the candidate list is all usable chocolate-doom functions, the dictionary all their lesions; the managed-doom lesions are a different implementation, so no leakage. Unit of analysis: the host function (cluster bootstrap by function, 10,000 resamples), with up to 5 lesions sampled per function (seed fixed) so large functions do not dominate.
3. **T2: cross-engine, prboom-plus,** same rules (counterpart by identical text or name with identical call profile).
4. **T3 (upper bound, descriptive): within chocolate-doom** leave-lesion-out on the test half.
5. **Real cases (after T1-T3 are read):** **gore (Go)** and **Kocoa (Kotlin)** against chocolate-doom's clean digests on the shareware-base demos each port can run (clean digests for gore and Kocoa on these demos are regenerated and committed with this registration's pins). Gore: the cause is known (the loop index in `p_CrossSubsector`, E13); Kocoa: unknown (monster behaviour; `NewChaseDir`, the tables match C).

## Hypotheses and thresholds (to be fixed from the development half and stated before T1 is computed; the shape is fixed now)
* **A1 (primary):** on T1, **top-5 recovery >= max(0.40, B2's top-5 + 0.15)**, with the cluster-bootstrap lower bound above B2's. Chance is about 3%. If the development half suggests 0.40 is unreachable, the threshold is revised **before** T1 and recorded.
* **A1b:** the same on T2; the two engines are reported separately and pooled with a function-level bootstrap.
* **A2:** **family narrowing.** The class set and severity band of the symptom alone (without the demo pattern) keep the true function inside the top 15% of candidates in at least **70%** of T1 bugs.
* **A3 (gore):** `p_CrossSubsector` (and its immediate callees) ranks in the **top 10 of the usable candidates** for gore's divergence on the demos where gore diverges and chocolate-doom does not.
* **A4 (Kocoa):** the top 10 contains the monster-chase family (`NewChaseDir`, `A_Chase`, `P_Move`, `P_TryWalk`, `P_CheckMissileRange`); the test is **confirmed** only if a source change guided by the ranking removes the divergence on the demos tested (E13's rule: a root cause is claimed only by a fix that removes the divergence).
* **Decision rule for a null:** if the lower bound of A1's top-5 recovery is below B2's, the lesion dictionary is "not distinguishable from coverage-based localisation at this resolution".

## Controls and sanity checks
* **Shuffled dictionary** (function labels permuted): top-5 must fall to chance.
* **Self-diagnosis ceiling:** a lesion's own half-split symptom against its own function (E15 PC1f-like): the within-function reliability bounds any cross-engine score.
* **Sensitivity:** demo subsets (original 42 / shareware 58 / Freedoom); lesion classes (statement deletion only / operators and constants only); one lesion per function; the mean-of-top-3 aggregation.

## Limits
Lesions are one-token bugs; real translation bugs (a loop index, a table value) are different perturbations, so gore and Kocoa are the real-world checks and carry n = 2; managed-doom and prboom-plus are faithful translations, so cross-engine diagnosis may be easier than for a divergent port; the candidate list covers only the screened simulation functions (a bug in rendering, input or a table outside those files cannot be found); the dictionary needs the symptom measured on enough of the demos; thresholds in A1 were set after seeing E15 results in general (but no diagnosis quantity).
