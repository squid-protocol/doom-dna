# `DOOM-E8b` Amendment 2 (2026-11-22): pin resolutions from cloning (outcome-blind)

Records what the clones showed and the resulting changes to the progenitor map of [Amendment 1 §B](E8B_AMENDMENT_1.md). Nothing here uses any survival or similarity number; the only measurements taken are repository facts (commit ancestry, dates, licences) and the precondition table (`manifest/e8b_precondition.csv`). Status is still DRAFT: registration follows once the measurement scripts are committed.

## Findings from the clones

1. **`woof` contains WinMBF's whole history.** All 32 commits of `team-eternity/WinMBF` are inside the `woof` clone, and WinMBF's first commit (2008-06-17) is `woof`'s first commit. WinMBF is therefore `woof`'s own early history, not a separate progenitor. The registered rule would make `woof` class A with fork commit = WinMBF's last commit (2016-08-20), leaving only post-2016 snapshots measurable. **Resolution (dated before any measurement):** the progenitor of `woof`'s history is **MBF 2.03** (class B, a separate repository with no shared commits), because WinMBF is itself an MBF port; WinMBF is measured **descriptively** (the `woof` snapshots before 2016-08-20 are WinMBF commits, which makes that comparison mechanical, so it is a sanity check only). `nugget-doom` from `woof` stays class A.
2. **PrBoom 2.5.0 contains PrBoom+ code.** Its `NEWS` tags changes taken from PrBoom+ (`[prb+]`), so it cannot be an ancestor of `prboom-plus`. **Resolution:** removed as a secondary progenitor; kept as a **descriptive sibling** comparator only. `prboom-plus`'s primary stays **Boom 2.02**.
3. **`edge-classic` shares no commits with `3dfxdev/EDGE`** (0 of 4,956), so it is class C as registered. EDGE has a real history from 2000-03-23, so the contemporaneous parent is well defined.
4. **Release dates.** GitHub commit dates for Boom, MBF and PrBoom 2.5.0 are import dates (2025 and 2026) and are not used. Boom's and MBF's source headers carry "Copyright (C) 1999"; the documents state "BOOM v2.02". The release dates are pinned as **no later than 1999-12-31** (used only to filter that a progenitor predates a snapshot; all earliest usable snapshots of the ports it serves are in 2000 or later); no more precise date is claimed. SMMU's last commit is 2001-02-25.

## Pins (committed in `manifest/e8b_pins.csv`; scans in `doom-e7-work/e8b/snaps`, engine `704cb35f0`)

| Progenitor | Commit | Date | Role |
|---|---|---|---|
| Boom 2.02 | `2a11d37040be` | 1999 or earlier (headers) | primary: `prboom-plus`; secondary: `edge-classic` |
| MBF 2.03 | `8f705abd36ed` | 1999 or earlier | primary: `woof`; secondary: `eternity` |
| SMMU | `173934b11e86` | 2001-02-25 | primary: `eternity` |
| EDGE | `d7adfc6a5320` | 2021-09-17 (last first-parent commit at or before 2021-10-16) | primary: `edge-classic` (class C) |
| `crispy-doom` | `595ecb2e5ee8` | 2023-06-26 | primary: `inter-doom` (class C) |
| `chocolate-doom` | `b9690ac0bbe2` | 2013-12-10 | primary: `doomretro` (class C, inferred) |
| WinMBF | `3af60d718b1f` | 2016-08-20 | descriptive |
| PrBoom 2.5.0 | `da3313ffaeb9` | (release mirror) | descriptive sibling |

## Resulting primary sample

Independent, same-language, non-shared-history ports: **`prboom-plus` (Boom), `woof` (MBF), `eternity` (SMMU; early C snapshots), `edge-classic` (EDGE, both C++), `inter-doom` (Crispy), `doomretro` (Chocolate)**: six, as Amendment 1 §D.7 anticipated, so the rule "at least 5 of 6 plus a one-sided Wilcoxon p below 0.05" stands. Class A (`crispy-doom`, `dsda-doom`, `nugget-doom`, `kocoa-doom`) stays the post-fork calibration stratum. `odamex`, `gzdoom` and `srb2` remain untestable and unexplained; `chocolate-doom` and `fastdoom` remain excluded by identity.

## Precondition table (all eight scans clean, return code 0)

Eligible functions (loc at least 6): Boom 856, MBF 935, SMMU 1,749, EDGE 6,805, Crispy@2023 2,372, Chocolate@2013 1,908, WinMBF 863, PrBoom 2.5.0 1,244. Duplicate share 0.08 to 0.18 except EDGE 0.24 (the largest and mixed C/C++ at 87% C++). Language: Boom, MBF, SMMU, Crispy, Chocolate, WinMBF at least 0.89 C; EDGE 0.87 C++; PrBoom 2.5.0 0.86 C. Scope drops applied to `crispy-doom` and `chocolate-doom` (Heretic, Hexen, Strife). The 0.24 EDGE duplicate share is under the 0.25 sensitivity cut and is reported.

## Still to do before registration

Write and commit the measurement and analysis scripts with tests; then register by commit (this amendment, the pins, the precondition table, the scripts), then measure.
