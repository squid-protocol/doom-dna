# `DOOM-E7` Amendment 1 (2026-11-22): reconciling two independent design reviews

Reviews: one Claude subagent and one Gemini (`gemini-4-neon-high`), run in parallel on the same brief (the draft file plus the scanner method doc, manifest and earlier preregistrations), neither seeing the other's output. Their raw reports are kept with the PR discussion. Where they agree it is marked **both**. Where code was checked directly by me it is marked **verified**.

This amendment **supersedes** the sections it names in [E7_THREE_TREES.md](E7_THREE_TREES.md). Anything not named there stays as written. **Registered 2026-11-22 14:47 EST** by the commit that adds `manifest/RUN_PINS.json` and `manifest/e7_new.csv`, before any E7 scan.

## A. Corrections to facts in the draft

1. **The text arbiter is name-gated (both, verified).** `measure/lineage.py` lines 208-214 look for `exact` and `near` matches only among functions with the same normalized name. A renamed function can only be scored "gone". So "names > text survival" (first half of H7.1) is true by construction, and sfs is penalized for finding renamed code. The earlier sfs precision/recall (93% / 65%, METHOD §12) and false-twin rates were measured against this same arbiter and are **superseded by E7**, not carried forward.
2. **The draft's "text verdicts do not depend on the engine" was wrong (Gemini, verified).** `lineage.py` takes function boundaries from the engine's scan database (`function_data.start_line`, `loc`). It must be rerun on the launch engine's scans.
3. **The sfs "family" rule has a root-sibling defect (Gemini, verified).** In `structural_fingerprint/lineage.py`, `cousin` excludes root ancestors but `sibling` does not, so all 19 programs whose declared parent is `linuxdoom` count as family of one another. The earlier "74% have a declared relative as nearest neighbour" is inflated and is superseded. `H7.5`'s 0.70 threshold, which came from it, is withdrawn.
4. **The multiset prose was inaccurate (Gemini).** `Σ min(n_Q, n_T)` lets a repeated key match as many times as both repos carry it. The sentence "a repeated name such as `main` cannot match twice" is struck. Generic-key handling (D3) is the real control.

## B. The arbiter (replaces §4 `M6`, `H7.1`)

- Build `measure/text_arbiter.py`: a **name-blind** text matcher. Candidates for each linuxdoom function are all functions in the port (not same-name only), shortlisted by MinHash over 4-token body shingles (own name masked, comments stripped), then scored by Jaccard. Verdicts: `exact`, `near` (at least 0.9), `derived` (at least 0.6). The overlap check is the verification rule already in `structural_fingerprint/ledger.py`; **only that rule is reused, not the function ledger** (the ledger follows one repo's history, mixes names and sfs twins in its stages, and would be circular as an arbiter).
- Run on the launch engine's scans, over exactly the eligible, scope-filtered function set both methods use. Report `M6` against `exact+near` and against `exact+near+derived`, and separately on the subset of functions whose name survives (where the old and new arbiters are comparable).
- `survival_struct` in `M6` uses **either-direction** twins (METHOD §9) so reference-side ratio-test collapse on ports with duplicated functions doesn't bias it.
- **H7.1 revised:** per port, `|err_struct| < |err_names|` against the name-blind arbiter, for at least 75% of the named same-language ports (list in D2), with the aggregate mean-absolute-error difference and a paired bootstrap over ports (2,000 draws) reported. The "names > text" clause is dropped as descriptive only.

## C. Declared tree and metrics (replaces §3 "Three trees", "Family", §4 `M1`-`M5`)

1. **Canonical treeification, fixed before scoring.**
   - `doo-cr` keeps its most specific parent (`puredoom`). `room4doom` is a from-scratch reimplementation whose two declared parents are compatibility/inspiration, not code lineage: it is **excluded from M1-M3** and kept as an M7 negative control. *(Assumption of mine about your data: say if you want it treated as a descendant.)*
   - `linuxdoom` and `doom3do` are scored as sampled ancestors (pendant leaves). A virtual root joins the unparented programs.
   - `doom3-bfg` gets the declared edge `doom3-bfg -> linuxdoom` (basis: inferred), since the scope rule keeps `doomclassic/`. `freedoom` (assets) is left out of tree scoring and reported separately.
2. **Edge basis column.** Add `manifest/declared_lineage_basis.csv` marking each declared edge `explicit` (README or history says so) or `inferred` (for example doomgeneric from copyright headers, committed before scanning). `M1`-`M3` are reported on all edges and on explicit edges only.
3. **Family rule.** `sibling` requires a shared **non-root** declared parent. `M1` is reported with and without root-only siblings. `M1` and `M2` are labelled **distance-matrix metrics**, not tree metrics. `M2` reports mean and median rank, ties averaged.
4. **Tree-to-tree metrics.** Replace symmetric clade RF against a polytomous declared tree with **resolved-clade recall and resolved-triplet compatibility** (the share of `T_declared`'s resolved clades and triplets that `T_names` and `T_struct` satisfy). Also report unrooted bipartition RF and quartet distance for the measured trees against each other.
5. **UPGMA kept** (continuity with METHOD §6). Add **Neighbor-Joining** (unrooted) and a rooted-at-linuxdoom variant as co-primary robustness checks. Nulls: the global leaf shuffle **plus** a within-language-stratified shuffle and a polytomy-preserving re-attachment. Bootstrap support by resampling functions is reported for each tree.
6. **Common scored set is primary (both).** `M1`-`M3` are reported (a) on the intersection of programs scored by both methods, and (b) with coverage (share of declared-parent ports clearing the floor) and full-set accuracy counting dropped declared-parent ports as misses.
7. `M4` excludes `quake`, `quake2`, `lua` (a same-studio pair and an outlier root).
8. **Distance.** Keep `shared = max over directions of the Wilson lower bound` as registered; add sensitivities with the **min** direction and a **pooled** survival. Vendored libraries (SDL, zlib, `textscreen`) are **retained** in the primary and dropped in a sensitivity, one policy for both methods.

## D. Name method (replaces §3 "Name key", N2, N3)

1. **Key.** Drop empty keys and keys under 3 characters after normalization. Drop `operator*` and destructors (`~`). Keep the delimiter rule, per-language, written into the key function's docstring.
2. **Same-language port list** is pinned in `manifest/e7_groups.csv` (C, C++, Objective-C ports with a declared lineage vs cross-language ports), committed before scanning.
3. **Generic names.** The primary name method gets a symmetric chance control (E below). The document-frequency cut **N3 is replaced** by an **external stoplist** derived from the GitGalaxy population corpus (keys present in at least 1% of non-DOOM repositories), written to `manifest/name_stoplist.txt` before scanning. If the population corpus can't be reached, derive it from the unrelated controls only, and say so. Raw names without the stoplist run as a sensitivity. Report per program the share of matched keys that are generic (key in at least 10 programs).
4. **N2** strips only the documented DOOM prefix set (`p_ r_ g_ d_ i_ v_ w_ z_ m_ s_ f_ hu_ st_ am_ wi_ net_ txt_ deh_`), and only when the remaining stem has at least 6 characters (as `measure/lineage.py` does).
5. **Eligibility.** The 6-line rule is imposed by structure, not by names. Add a **no-size-filter names variant**. A program with 0 eligible functions is listed as unscorable before the floor.

## E. Symmetric error control (replaces §3 "Survival"; both)

- Structure certifies at `fdr = 0.01` with a `+1` correction, so a pair with fewer than 100 candidates can certify nothing. Names had no equivalent. Now:
  - **Name decoy.** For each pair, replace Q's key multiset 200 times (seeded) with a same-size draw from the pooled vocabulary of the unrelated controls and the programs outside either side's declared family; a pair's name-survival is certified only if it exceeds the 99th percentile of the decoys (same `+1` rule).
  - **Minimum evidence for both methods:** a pair with `min(|Q|,|T|) < 100` eligible functions is reported **"underpowered"**, not "no detectable descent", under both methods, and does not count as a false-attachment test.
  - Every negative control intended to test false attachment has **at least 150** eligible functions.

## F. Hypotheses (replaces §4 `H7.1`-`H7.5`, §5)

- **Primary endpoints, Holm-corrected across the family:** `H7.1` (B above), `H7.4` (revised below), `H7.5a` (`M1` on the corrected family rule). Everything else is exploratory or descriptive.
- **H7.2:** Spearman of `shared_names` vs `shared_struct`, with a **cluster bootstrap over ports** (a port appears in many pairs). Descriptive.
- **H7.3:** among cross-language ports with a declared parent that `T_struct` leaves with no detectable descent, how many **attach to a declared family member** under names (not merely clear the floor). Names the exact ports; descriptive.
- **H7.4 revised:** attachments **to DOOM engine-ports** only (the `quake` to `quake2` pair is excluded). Controls are stratified: same-studio (`quake`, `quake2`) vs unrelated C/C++ (G2). Prediction: structure shows 0 false attachments to DOOM engine-ports among unrelated controls with at least 150 eligible functions; names shows at least 1.
- **H7.5a:** `M1` (corrected rule, common scored set) exceeds the 95th percentile of the within-language-stratified permutation null for each method. The earlier 0.70 is withdrawn. A fixed numeric threshold is added only if the null's values are looked up before the run.
- A **power statement** is added to the report: with about 30 scored ports, the smallest `M1` difference detectable between methods, from the paired bootstrap.
- **Wording ban:** the report may say a method "agrees with the declared lineage" and "agrees with name-blind text survival of linuxdoom code", **never** "tracks ancestry better".

## G. Corpus, controls, Phase B (replaces §2 table, §6)

1. **Honest labels.** Phase A is a **locked-protocol re-measurement on a new engine** of programs already scanned and seen (E5 scored). The thresholds were chosen with that data in view. Phase B1 (the 11) is a **frozen-map placement check, descriptive for the E5 five and for the six added controls**, which only test "nothing spurious attaches". **Confirmatory** claims come only from Phase B2 below.
2. **New programs, selected by metadata only and listed in `manifest/e7_new.csv` before cloning:**
   - 3 to 5 **unrelated large C/C++ negative controls** (at least 200 eligible functions, permissive licences), added to the **Phase A map**.
   - 3 to 5 **unseen positive held-outs** (genuine forks or hybrids not previously scanned), placed in **Phase B2**.
3. **H7.6 split.** *Sensitivity:* every B2 positive attaches to a declared-family program under each method (reported per program). *Specificity:* 0 false attachments among clear negatives with at least 150 functions. The report also gives the **always-null baseline** (a method that never attaches) next to each score, with exact intervals.
4. **H7.7 crisp:** names' correct-placement count on B1+B2 is at most structure's; it is falsified if names is higher. The "or the table shows" clause is struck.
5. **`iron-doom`** is an **unscored diagnostic for both methods** (outside both denominators). `doomarkable` stays a negative.
6. **Leave-one-out placement:** 8 mapped ports with a declared parent in the map (chosen by rule: the 8 with the most eligible functions) are removed, the map rebuilt, and each placed back. Nearest = declared parent or a declared relative is the positive.
7. Phase B is **pairwise nearest-neighbour** (argmax of `shared`), not tree insertion; the draft's "frozen map" wording is corrected.
8. **No Phase B code path runs on any withheld program before the Phase A manifest is committed.**

## H. Pins, scope, provenance (replaces §3 "Run pins", §7)

- A single `manifest/RUN_PINS.json` is committed **at registration**: GitGalaxy engine SHA, `reference_function_model.json` hash, `spec_hash`, and the SHAs of **all** programs (manifest, `quake`, `quake2`, `lua`, the 11, the new ones). The phrase "pinned scans from `followups/seed-and-extend`" is struck; **every program is rescanned**. The engine SHA and `spec_hash` are written into each Newick header.
- **Scope rules** are stated in full from `scope.csv` (keep and drop: `doom3-bfg` keeps `doomclassic/`; `dsda-doom` and `doomsday` have drops; `doomretro` has none). The sentence claiming Chocolate, Crispy, Inter and Doom Retro are "handled alike" is corrected.
- Ties in `M1`, `M2` and Phase B are broken by **averaging**, not alphabetically.
- `M8` gets a deterministic priority order: (1) generic-name collision if over half of matched keys are generic; (2) small-repo threshold if `min(|Q|,|T|) < 100`; (3) sideways transfer if at least 70% of matched functions are in one directory; (4) translation if the languages differ; (5) rename/reorganization otherwise. Each of the 20 pairs is coded by the rule, not by judgment.
- Add unit tests: self-to-self survival is 1.0 for both methods, and `survival_names <= 1` always.
- Report `M1`-`M7` separately for same-language and cross-language subsets.

## I. Disagreements and declined suggestions

- The Claude review proposed **leaving the name-gated arbiter in place** as a fallback with a caveat. Declined: both reviews call it a blocker, and the corrected arbiter is built instead (B).
- The Gemini review proposed an **8.2M-function external stoplist**. Adopted with a stated fallback (D3) because I haven't confirmed the population corpus is reachable from the run machine.
- The two reviews differ on `iron-doom`: Claude would keep it (pre-stating N2/N3 outcomes), Gemini would exclude it from both denominators. Adopted Gemini's: it is a diagnostic only.
- Unchanged from the draft: the questions; the per-metric report with no declared winner and "no difference detected" when an interval includes 0; shared Wilson/max/`1 - shared` formula; UPGMA as the primary tree; the Phase A manifest committed before Phase B; the disclosure paragraph; the sensitivity list; no third-party source committed.

## J. Effects on earlier claims (to be corrected in the article regardless of E7's outcome)

The "74% have a declared relative as nearest neighbour" (scanner example README), and the 93% precision / 65% recall of twins (name-gated arbiter), are not to be quoted as results. E7 replaces them.

## K. Registration record (2026-11-22 14:47 EST)

- **Engine** `704cb35f0` (GitGalaxy `origin/main`, 2026-11-22 14:38 EST), checked out detached at `gitgalaxy-worktrees/e7-engine`. **sfs** `main` at `bcd3cb7` (v0.1.0; supersedes the draft's `b1a9e92`, an ancestor).
- **Reference refresh not needed.** `tools/refresh_reference.py` re-run against the engine changed only provenance fields; `spec_hash` is unchanged (structure `f5d525ed16bc91db`, portable `82dfe97689dec61b`), so sfs `main` is used unmodified.
- **66 programs pinned** in `RUN_PINS.json`: 44 manifest ports, `lua`/`quake`/`quake2`, the 11 withheld, and 8 new (4 positives, 4 unrelated negatives; selection rule in `manifest/e7_new_selection.md`, fixed before cloning). The 11 withheld and the controls are pinned to default-branch HEAD at registration. Earlier E5-era SHAs for them were not recorded and are not used. The carddemo control is scoped to `COCRDLIC.cbl` and `COUSR00C.cbl`.
- **Still to be committed before the first scan** (per Amendment 1 D and C): `manifest/declared_lineage_basis.csv`, `manifest/e7_groups.csv`, `manifest/name_stoplist.txt`. If the population corpus isn't reachable for the stoplist, the fallback in D3 applies and is recorded when the file is committed. Any later change to a registered rule needs a dated amendment.
- **Known gap:** the scan scope used for the E5-era controls other than carddemo was not recorded; E7 scans each at its pinned SHA in full, apart from `scope.csv` rules.
