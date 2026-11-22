# `DOOM-E8b` progenitor search log (2026-11-22, metadata only; nothing cloned or scanned)

Purpose: for each port whose real progenitor is outside the corpus, record what was searched and what was found, so "untestable" is a documented outcome and not an assertion. Sources: GitHub repository metadata and file listings through the API.

| Needed progenitor | For | Tried | Outcome |
|---|---|---|---|
| Boom 2.02 | `prboom-plus` (primary), `edge-classic` (secondary) | `doom-cross-port-collab/boom` | Found: 4 commits, "The Doom source port, Boom 2.02"; no licence field and no root `COPYING` (to verify, see licence note) |
| MBF 2.03 | `woof` (secondary), `eternity` (secondary) | `doom-cross-port-collab/mbf` | Found: 2 commits; same licence note |
| WinMBF | `woof` (primary) | `team-eternity/WinMBF`, `doomtech/winmbf` | Found: 32 commits (2016); no licence field; pin to the commit Woof's history starts from (to establish) |
| SMMU | `eternity` (primary) | `fragglet/smmu` | **Found**: GPL-2.0, `COPYING` present, "historical repository of the SMMU source, reconstructed from the releases", commits 2000-05 to 2001-02 on the first page, archived 2013 |
| PrBoom 2.5.0 | `prboom-plus` (secondary, snapshots after its date) | `froggey/prboom-2.5.0` | Found: GPL-2.0, `COPYING` present, one commit, "Mirror of prboom-2.5.0 release" (a release mirror; the release postdates the earliest prboom-plus snapshots, so it can only serve later ones) |
| EDGE at the date edge-classic forked | `edge-classic` (class C) | `3dfxdev/EDGE` | Found: C++ history 2021-03 to 2025-11 (so the 2021-10 commit is a contemporaneous parent, not an old ancestor); no licence field, `COPYING` not seen in the root listing (to verify) |
| Old ZDoom (1.22 and early 2.x) | `odamex`, `gzdoom` | `ZDoom/zdoom`, `coelckers/zdoom` (is GZDoom), `drfrag666/gzdoom`, searches "zdoom 1.22", "zdoom source code old version" | **Not found**: no old ZDoom repository; `gzdoom`'s own early history is a descendant, not a progenitor |
| CSDoom 0.62 | `odamex` | `odamex/odamex-0.x`, search "csdoom" | **Not found** (`ronen9rex-prog/CSdoom` is an empty 1 KB repository) |
| Doom Legacy | `srb2` | `doomlegacy/doomlegacy`, `legacy-team/doomlegacy`, search "doom legacy 1.4" | **Not found** |
| PrBoom 2.x CVS history | `prboom-plus` | `prboom/prboom`, `kraflab/prboom` | Not found as a repository (the early prboom-plus history itself is imported CVS) |

**Untestable after search: `odamex`, `gzdoom`, `srb2`.** The E8 anomalies for these three are not explained by this experiment and are reported as unexplained.

**Licence note.** GitHub shows no licence field for Boom, MBF, WinMBF or EDGE (also true of `coelckers/prboom-plus`, already in the corpus, whose licence the manifest takes from `COPYING`). SMMU and PrBoom 2.5.0 carry `COPYING`. Before any clone: check the source headers and docs of Boom, MBF, WinMBF and EDGE; default if unconfirmed: measurements and hashes only, no source committed, and the owner decides inclusion.
