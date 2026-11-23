# `DOOM-E8b` Amendment 1 (2026-11-22): reconciling two independent design reviews and the progenitor search

Reviews: a Claude subagent and Gemini (`gemini-4-neon-high`), same brief, neither seeing the other's output. **both** = both reviews raised it. This amendment supersedes the sections of [E8B_PROGENITOR.md](E8B_PROGENITOR.md) it names; the rest stands. Status is still DRAFT until the pre-measurement steps in §H are done and the pins are committed before any survival is computed.

## A. Narrowed claim (both)

1. **Title and §1 are narrowed.** E8b tests whether **anchoring to the closest obtainable progenitor** raises initial survival and gives cleaner structural decay in the **Chocolate lineage and the Boom, MBF, SMMU and EDGE lineages**. It does **not** test, and cannot explain, E8's flat-and-low `gzdoom`, `odamex` and `srb2`: their progenitors (old ZDoom, CSDoom, Doom Legacy) were searched for and not found (`manifest/e8b_progenitor_search.md`). Those three remain **unexplained**. C to C++ migrations (late `eternity`, `edge-classic` against a C progenitor) test language blindness, not comparator mismatch.
2. **Prior knowledge, specific (both).** The E8 numbers that motivated the idea: the low flat `gzdoom`, `odamex`, `edge-classic` and `srb2` curves, and the contrast of Chocolate (0.88 to 0.55) with them. E8's `pairs_grid.csv` (class A post-fork) and E7's head matrices (head-level class C proximity) were **seen**. Genuinely unseen: survival against the new progenitors (Boom, MBF, WinMBF, SMMU, PrBoom 2.5.0, EDGE at the fork date) and the two date-matched parents. E8 snapshots and scoring are reused, so E8b results are **not independent of E8**.

## B. Progenitor map: one primary per port, with a rule (replaces §2 table; both)

**Inclusion rule (operational, fixed before cloning):** a progenitor is a public repository of the documented ancestor release or revision, whose source carries a confirmed GPL licence (header or `COPYING`), chosen from the port's declared lineage text before any measurement.

| Port | Primary progenitor | Pin | Class | Secondary (descriptive) |
|---|---|---|---|---|
| `prboom-plus` | **Boom 2.02** (`doom-cross-port-collab/boom`) | release date 1998-10-22 (to confirm from the repo's docs) | B | PrBoom 2.5.0 (`froggey/prboom-2.5.0`) for snapshots dated after its release; MBF 2.03 |
| `woof` | **WinMBF** (`team-eternity/WinMBF`) at the last commit before `woof`'s first commit (2008-06-17); **if git ancestry shows shared history it becomes class A with that fork commit** | decided after cloning, before measurement | B or A | MBF 2.03, Boom 2.02 (the chain is reported) |
| `eternity` | **SMMU** (`fragglet/smmu`, GPL-2.0, 2000-05 to 2001-02) at its last commit | before `eternity`'s first commit (2006-02-07) | B | MBF 2.03 |
| `edge-classic` | **EDGE** (`3dfxdev/EDGE`, GPLv2) at the last commit at or before `edge-classic`'s first commit (2021-10-16) | pinned after cloning | C (same language, C++) | Boom 2.02 |
| `inter-doom` | **`crispy-doom`** at the last commit at or before 2023-07-06 | one new scan | C | `chocolate-doom` |
| `doomretro` | **`chocolate-doom`** at the last commit at or before 2013-12-21 | one new scan | C, inferred | none |
| `crispy-doom`, `dsda-doom`, `nugget-doom`, `kocoa-doom` | parent at the git fork commit | `e8_fork_truth.csv` | **A, calibration stratum** | |
| `chocolate-doom`, `fastdoom` | `linuxdoom` itself | | excluded from H8b.1 by identity; reported | |
| `odamex`, `gzdoom`, `srb2` | none found | | untestable, unexplained | |

Release dates are pinned from each repository's own documents before computation (a GitHub commit date is a modern import date and is **not** used as an age). Within-port Kendall `tau-b` is shift-invariant, so the date matters only for filtering (a progenitor is used only for snapshots dated after it) and for H8b.3.

## C. Time and class A (both; replaces §3 snapshot rule)

3. **Class A is measured only post-fork.** Their calendar snapshots before the fork are the parent's own commits and are excluded (comparing a snapshot to a reference years in its future caps survival and forces `A < 0`). Class A uses the E8 semi-annual grid (`e8_grid_pairs.csv`), excluding `step 0`, plus the 2026 head where the grid ended early. The class A stratum is a **calibration and post-fork decay check, not part of the primary test**. Fork-anchored survival (frozen parent at the fork commit) is contrasted with contemporaneous `shared(P@t, R@t)` (two-sided, with upstream merges), because living parents are merged into children (visible in `pairs_grid.csv`).
4. **Class B and C comparison snapshots.** A snapshot counts only if it is dated after the progenitor, has at least 100 eligible functions and a non-empty scan. `A` is reported at the earliest usable snapshot, at the second, and as the median of the first three, to expose single-point artefacts (`f = 0` crashes in `prboom-plus` and `doomretro`; the `inter-doom` jump).

## D. Measures and the primary test (replaces §3 measures, §4 H8b.1; both)

5. **Three-way decomposition of each progenitor `R` against `linuxdoom`:** (i) **unchanged inherited** (certified twin in `linuxdoom`), (ii) **modified inherited** (no twin, but the same E7 name key or the name-blind text arbiter's `derived` verdict against `linuxdoom`), (iii) **progenitor-novel** (neither). `S_R^novel(t)` is the survival of group (iii) alone. The "advantage must remain positive for the added subset" clause is **struck** (Boom-novel code is absent from `linuxdoom`, so that comparison is undefined). The **carry-over gate** is: `S_R^novel(earliest usable) >= 0.02` with a 95% bootstrap interval above 0, and above the wrong-progenitor novel survival (item 9).
6. **Equal footing for the two arms.** `S_R` and `S_linuxdoom` are computed with the same twin-score procedure at the same FDR (0.01), thresholds calibrated separately per reference and reported; and `A` is also computed on a **common-denominator subset** (functions present in both `R` and `linuxdoom`). `A` is bootstrapped **paired over the functions of `P`**, and the per-snapshot check is reported.
7. **Primary test (replaces "70% + sign test").** The primary sample is the **independent, same-language, non-shared-history** ports: `prboom-plus`, `eternity` (its early C snapshots), `woof` (if class B), `edge-classic`, `inter-doom`, `doomretro`. A port **passes** if `A_struct(earliest usable) >= +0.05` with the paired 95% bootstrap interval strictly above 0. The headline claim "anchoring to the progenitor explains more of the port than `linuxdoom`" is **supported** if **at least 5 of 6** (or all, if fewer than 6 qualify) pass **and** a one-sided Wilcoxon signed-rank test on `A` gives p below 0.05 (with n = 6 the smallest possible p is 0.016; with n = 5, 0.031). Below the minimum n of 5 the result is **inconclusive**, not negative. A negative result on the testable ports means **"wrong comparator not supported"**, stated as such. The earlier 70% bar and the unbounded sign test are withdrawn. `kocoa-doom` (cross-language) and any snapshot with `lang_c < 0.90` against a C progenitor are **excluded from the structural test and reported separately alongside names**.
8. **`A_names` and `S_R,names^novel`** are reported descriptively beside structure for every port.

## E. Controls (replaces H8b.4; both)

9. **Differential specificity:** with wrong progenitors **pinned before cloning** (`chocolate-doom` at 2013-12-09 for Boom-line ports; Boom 2.02 for Chocolate-line ports), `S_R_right(t) > S_R_wrong(t)` on total survival; and on the **progenitor-novel** subset of the *wrong* progenitor, survival stays below the 2% floor (this removes shared `linuxdoom` ancestry, which is why total survival against a wrong progenitor is **not** predicted to stay below the floor). `nginx` stays as a pure null; **the new progenitors are also run against the unrelated controls** (`curl`, `libuv`, `nginx`, `helion`, `rust-doom`) and must stay below 2% under structure.

## F. H8b.2 and H8b.3 (replaces H8b.2, H8b.3; both)

10. **H8b.2 (descriptive, secondary):** decay with the progenitor as reference, judged on the **partial correlation with `log(eligible functions)`**, with the explicit expectation that the E8 result (trend vanishing under that control) may recur and is reported as fragile. The name decay is reported on the same footing so "structure vs names" is comparable with E8.
11. **H8b.3 (exploratory, one fixed snapshot per candidate):** for each port, the candidate pool is **one snapshot per distinct repository** (the latest scanned snapshot strictly before the port's origin or fork date, excluding the port and its declared descendants), with the date filter applied from the pinned release dates (so `WinMBF` of 2008 is not a candidate for `prboom-plus` of 2000). `shared_struct` (per-snapshot threshold) and `shared_names` are ranked separately. The exact rank is reported with the pool size `K` and the random-ranking baseline (`1/K` for rank 1); the "top 3 in 70%" rule is withdrawn. If the registered progenitor is not in the top 3, H8b.1 is reported but not read as supporting the map.

## G. Confounds (both; replaces §5 handling)

12. **De-duplication:** function-level exact-digest de-duplication on both sides is a sensitivity (E8's snapshot-dropping at `dup_share > 0.25` is not enough: `prboom-plus`'s earliest usable snapshot has `dup_share` 0.345, `edge-classic` 0.32 to 0.33). **Pure-C filter** redefined for E8b as `lang_c >= 0.90` **relative to the C progenitor** (not the port's head), so `eternity`'s 2006 to 2008 C segment is analysed cleanly (E8's filter dropped all of it because the head is C++). **Name-blind text arbiter** (`measure/e7_arbiter.py`) is run on the earliest usable snapshot and the head for every class B and C port against its progenitor, and for each progenitor against `linuxdoom`, to separate real retention from growth-driven crowding. The growth control (partial correlation with `log(eligible)`) is applied to every trend and noted for `A(t)`, where growth partly cancels because both arms use the same snapshots (checked).
13. **Threshold policy:** per-snapshot FDR 0.01 is primary for H8b.1 (a single-snapshot cross-reference comparison); pooled per port is primary for H8b.2 trends; both reported.
14. **Name decoy pool:** `boom`, `mbf`, `winmbf`, `smmu`, `prboom-2.5.0` and `edge` are added to the DOOM family set when building the decoy vocabulary for E8b (otherwise all DOOM ports stay in the pool and the decoy bar rises artificially).

## H. Pre-measurement steps (before the map is locked and E8b is registered)

* **Licences confirmed (2026-11-22, by API, before any clone):** Boom 2.02 and MBF 2.03 (GPL notice in `d_main.c` and `docs/copying`); WinMBF (GPL notice in `Source/d_main.c`); EDGE (GPLv2 stated in `AUTHORS.md`, `docs/licenses` present); SMMU and PrBoom 2.5.0 (`COPYING`). No source is committed; only measurements and hashes.
* Clone the progenitors **outside** the repository; resolve the open pins (WinMBF ancestry vs `woof`; the EDGE and Chocolate and Crispy commits at the origin dates; the SMMU last commit; release dates from the repositories' own documents); scan them with the E7 engine (`704cb35f0`) plus the two date-matched parents (`crispy-doom`, `chocolate-doom`).
* Commit a **precondition table** (pinned SHAs, eligible functions, `dup_share`, `lang_c`, scope drops, scan status) **before** locking the final map and registering. Registration then follows the E8 pattern (pins, scripts, manifest hashes committed before any survival is computed).

## I. Declined or adjusted

* Both reviews asked that `woof` have a single primary: adopted (WinMBF, with the ancestry check that may move it to class A).
* The Claude review suggested a mixed-effects model over all usable snapshots; adopted only as a descriptive sensitivity, since 6 ports do not support random effects reliably.
* Gemini suggested excluding `edge-classic` as C++ against a C progenitor; resolved instead by changing its progenitor to EDGE (same language), which the search made possible.
* Unchanged: the post hoc framing, adding progenitors to the corpus, E7 and E8 pins, the evidence classes, the chain reporting, fixed-release progenitors, the nginx null, and the staged commit discipline.
