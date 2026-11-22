# `DOOM-E8b`: Progenitor-anchored survival: does an appropriate comparator explain the ports that did not behave as expected in E8?

**Status: DRAFT, not registered. [Amendment 1](E8B_AMENDMENT_1.md) (2026-11-22) reconciles two independent design reviews and the progenitor search and supersedes the sections it names; read it with this file.** Registers when two independent design reviews are reconciled in a dated amendment and this file is committed before any E8b computation or new clone. Thresholds marked `[LOCK]` are proposals. Follow-up to `DOOM-E8` (draft PR #3, results in `results/e8/E8_RESULTS.md` there); reuses E8's scans, scripts, engine (`704cb35f0`), sfs (`bcd3cb7`) and E7's name key, stoplist and twin rules unchanged.

## 1. Why, and what kind of experiment this is

`DOOM-E8` measured how much of **linuxdoom** survives in each port over its history. Names also decayed, structure decayed clearly only in lineages that start close to linuxdoom (Chocolate 0.88 to 0.55), and lineages from other code lines (gzdoom, odamex, edge-classic, srb2) stayed flat and low. The owner's reading is that linuxdoom is the wrong comparator for ports that descend from an intermediate (Boom, MBF, ZDoom, a fork). This experiment tests that reading by measuring each port against its **appropriate progenitor**.

**It tests a hypothesis generated after seeing the E8 results**, on largely the same ports and the same scans. It is a follow-up that explains E8, not independent confirmation of the original hypotheses. The write-up must say so.

## 2. What "appropriate progenitor" can mean here (facts from the corpus)

Only four child/parent pairs share git history, which gives an exact fork point: `crispy-doom` from `chocolate-doom` (2013-12-09), `dsda-doom` from `prboom-plus` (2020-11-09), `nugget-doom` from `woof` (2021-08-31), `kocoa-doom` from `mochadoom` (2019-07-20; cross-language). Every other port's real progenitor is either **outside the corpus** (Boom 2.02, MBF 2.03, ZDoom, SMMU, EDGE, Doom Legacy) or has no shared git history (`inter-doom` from Crispy, `doomretro` from Chocolate). Choosing a different corpus comparator cannot fix those; **the progenitors have to be added to the corpus.**

**Progenitor map (fixed here, before any computation, from each port's declared lineage text):**

| Port | Progenitor | Basis | Evidence class |
|---|---|---|---|
| `crispy-doom` | `chocolate-doom` at the fork commit | git shared history | A |
| `dsda-doom` | `prboom-plus` at the fork commit | git shared history | A |
| `nugget-doom` | `woof` at the fork commit | git shared history | A |
| `kocoa-doom` | `mochadoom` at the fork commit | git shared history (Java to Kotlin) | A, cross-language |
| `prboom-plus` | **Boom 2.02** (new) | "PrBoom, Boom, linuxdoom" | B |
| `woof` | **WinMBF** (new) and **MBF 2.03** (new) | "WinMBF, MBF, Boom" | B |
| `eternity` | **MBF 2.03** (new) | "SMMU, MBF" | B |
| `edge-classic` | **Boom 2.02** (new) | "EDGE (Boom-derived)" | B, weak |
| `inter-doom` | `crispy-doom` at the date of its first commit | "Crispy Doom" | C |
| `doomretro` | `chocolate-doom` at the date of its first commit | "inferred: crispy README calls it his fork" | C, inferred |
| `odamex`, `gzdoom` | none available (ZDoom 1.22 not obtainable); `srb2` (Doom Legacy) likewise | | untestable, reported only |

New corpus programs, selected by documented lineage and checked by GitHub metadata only, before cloning: `doom-cross-port-collab/boom` (Boom 2.02), `doom-cross-port-collab/mbf` (MBF 2.03), `team-eternity/WinMBF` (32 commits). **Licensing to be confirmed before cloning:** GitHub shows no licence field for any of them (as it also does for `coelckers/prboom-plus`, already in the corpus, whose licence the manifest takes from `COPYING`); the source files carry the original GPL headers, to be checked. If a licence cannot be confirmed, the owner decides whether to include it (measurements only, no source committed).

## 3. Measurements

For each tested port `P` and its progenitor `R` (a **fixed snapshot**: the fork commit, the origin-date commit, or the release):
* **Progenitor-anchored survival** `S_R(t)`: for each of `P`'s existing E8 snapshots (calendar plan, de-duplicated, at least 100 eligible functions), the share of `R`'s eligible functions (loc at least 6) found in the snapshot, by **structure** (either-direction twins, pooled threshold per port as E8) and by **names** (E7 key, stoplist, decoy test, one-to-one). Same rules as E8; no new scans except the progenitors (3 releases) and two date-matched parents (`crispy-doom` and `chocolate-doom` at the origin dates of `inter-doom` and `doomretro`): **5 new scans**.
* **Progenitor-added code:** `R`'s functions split into those **inherited from linuxdoom** (certified twin or name match in the E7 `linuxdoom` fingerprint) and those **added by the progenitor** (Boom's own functions, for example). `S_R^added(t)` isolates the progenitor's own contribution, so a port that only carries linuxdoom code is not credited to Boom.
* **Comparison with E8:** for the same snapshots, `S_linuxdoom(t)` from E8; the **advantage** `A(t) = S_R(t) - S_linuxdoom(t)`.
* **Wrong-progenitor controls:** each tested port against a progenitor from a different line (a Boom-line port against Chocolate; a Chocolate-line port against Boom), and against `nginx` (E8 placebo reference). Their survival should be low and show no trend.
* **Sibling and contemporaneous check (descriptive):** `shared(P@t, R_current@t)` where the progenitor's own history exists (the four class A pairs, from E8's `pairs_grid.csv`).

## 4. Hypotheses `[LOCK]` (all directional, motivated by E8)

* **H8b.1 (the comparator explains the anomalies; primary):** for the ports with a class A or B progenitor, structure `S_R(earliest usable)` exceeds `S_linuxdoom(earliest usable)` in at least **70%** of ports, tested by an exact one-sided sign test (with the number of ports reported), with function-level bootstrap intervals for each port's advantage. Where `S_R^added` is computed, the advantage must remain positive for the progenitor-added subset, or the result is labelled "carried over from linuxdoom".
* **H8b.2 (the original hypothesis, re-tested; descriptive):** with the progenitor as reference, structure survival falls with age since the progenitor's date (Kendall `tau-b` at most -0.6 in a majority of class A and B ports) and the fall in names is smaller than the fall in structure; reported per port, with the E8 caveat that names also decayed.
* **H8b.3 (the progenitor map is right; exploratory):** among all scanned snapshots dated at or before a port's origin (plus the three new releases), the registered progenitor ranks first (or in the top 3) by `shared` at the port's earliest snapshot in at least 70% of the tested ports.
* **H8b.4 (controls):** wrong-progenitor and `nginx` survival stay below the 2% floor with no trend; if a wrong progenitor shows a high survival, that is reported as shared ancestry (for example Boom and Chocolate both descend from linuxdoom), not discarded.
Primary endpoint: **H8b.1**. Everything else is descriptive.

## 5. Limits and disclosure

* **Post hoc motivation (above).** The progenitor map was written after E8 results were seen; it follows each port's declared lineage text and the git-shared history, not the E8 numbers, and is fixed before computation. No E8b number has been computed.
* **Few pairs.** Class A has four pairs (three same-language); class B has four ports and two to three progenitors; the testable set is about 8 to 10 ports and the sign test's power is limited (10 ports need 9 in the predicted direction for p below 0.05).
* **Boom and MBF are single releases** (2 to 4 commits), so progenitor-anchored survival is measured against a fixed release, not against a moving parent; PrBoom's own history before 2000 is not available.
* **Intermediate steps.** Boom to MBF to WinMBF to Woof is a chain; the nearest progenitor in the map is used, and the chain is reported (a port can be closer to Boom than to MBF).
* **Inherited-versus-added split** relies on E7 twin and name matches against `linuxdoom`; Boom's modified-but-not-certified functions land in "added" (a bias in favour of H8b.1), so the split is reported with both rules (certified twin only; certified twin or name match).
* Duplicated functions (E7: `puredoom` 99%, `mood` 78%) and C to C++ migration (E8) can still distort both methods; the E8 sensitivities (de-duplicated, pure-C, per-snapshot threshold, partial correlation with `log(eligible)`) are repeated.
* Repository growth entangles structure survival with age (E8): the partial correlation with `log(eligible)` is part of every trend result.
* No third-party source is committed; clones and scans stay outside the repository, hashed in the run manifest.

## 6. Order of work

1. Reviews and amendment; confirm the three progenitor licences; commit the progenitor map, scripts and tests.
2. Clone the three progenitors at pinned SHAs and scan them, plus the two date-matched parent commits (5 scans); commit the pins before any survival is computed.
3. Measure `S_R(t)`, `S_R^added(t)` and the controls over the existing E8 snapshots; commit the manifest; analysis and report.
