# Multi-Layer Port Evidence: Structure + Comments + Ledger + Isotonic Decay

## Summary

Combining three orthogonal signals—**pure structural Seed-and-Extend** (`NO_COMPLEXITY`), **function-level comment/docstring alignment**, and **temporal `ledger` birth-ID tracking**—recovers substantially more conserved functions across OOP and heavily refactored DOOM ports while keeping negative controls (`lua`, `quake`, `quake2`) and clean-room rewrites (`helion`) at `0.0%–0.8%`.

## 1. Cross-Port Sweep (`results_all.csv`, `min_loc=3`, vs. `linuxdoom` `n=777`)

Notable jumps from **Pure Structure (`S+E`)** to **Multi-Modal (`FGW+Ext`)**:

| Port | `n` | Pure Structure (`S+E`) | Comments-Only (`RBH J≥0.25`) | Multi-Modal (`FGW+Ext`) |
|---|---:|---:|---:|---:|
| `mood` | 1859 | 691/725 (95.3%) | 222/224 (99.1%) | **704/724 (97.2%)** |
| `puredoom` | 1546 | 596/663 (89.9%) | 429/430 (99.8%) | **639/668 (95.7%)** |
| `doomgeneric` | 1192 | 550/642 (85.7%) | 386/399 (96.7%) | **587/652 (90.0%)** |
| `gore` | 996 | 430/561 (76.6%) | 355/368 (96.5%) | **552/619 (89.2%)** |
| `doom3-bfg` | 13859 | 265/671 (39.5%) | 413/421 (98.1%) | **561/640 (87.7%)** |
| `chocolate-doom` | 5129 | 443/664 (66.7%) | 386/401 (96.3%) | **510/669 (76.2%)** |
| `crispy-doom` | 5870 | 369/663 (55.7%) | 362/386 (93.8%) | **486/660 (73.6%)** |
| `mochadoom` | 3037 | 86/483 (17.8%) | 333/362 (92.0%) | **389/544 (71.5%)** |
| `managed-doom` | 1285 | 66/412 (16.0%) | 123/162 (75.9%) | **198/366 (54.1%)** |
| `kocoa-doom` | 2902 | 17/408 (4.2%) | 166/177 (93.8%) | **233/434 (53.7%)** |
| `eternity` | 6641 | 38/644 (5.9%) | 148/208 (71.2%) | **270/621 (43.5%)** |
| `odamex` | 7759 | 37/664 (5.6%) | 200/256 (78.1%) | **268/634 (42.3%)** |
| `helion` (clean-room) | 8386 | 0/589 (0.0%) | 0/10 (0.0%) | **0/575 (0.0%)** |
| `lua` (control) | 1666 | 0/492 (0.0%) | 0/7 (0.0%) | **0/525 (0.0%)** |
| `quake` (control) | 2594 | 4/533 (0.8%) | 0/2 (0.0%) | **4/527 (0.8%)** |
| `quake2` (control) | 5289 | 3/494 (0.6%) | 0/2 (0.0%) | **2/488 (0.4%)** |

Full 44-row output is in [`results_all.csv`](results_all.csv).

## 2. Multi-Snapshot Ledger + Isotonic Decay (`structural_fingerprint.port_evidence`)

- **`gore` (5 snapshots over 17 months: `day5 bdb1e8a` → `day14 ac1c714` → `mo5 3590aa5` → `mo17a 877e2a4` → `HEAD c2b1989`):**
  - Pure structure raw: `0.802 → 0.763 → 0.766 → 0.736 → 0.738`
  - PAVA isotonic fit: `0.802 → 0.765 → 0.765 → 0.737 → 0.737` (`drop=+0.066`, `verdict=one_time_port`)
  - Temporal projection at `HEAD`: `direct=433/587`, `projected=257/307`, `confirmed=217/219 (99.1%)`, `union=457/629`
- **`mochadoom` (2 snapshots over 11 years: `2015 cf8eaeb` → `2026 c0af132`):**
  - Pure structure raw: `0.199 → 0.150` (`drop=+0.049`, `verdict=one_time_port`)
  - Temporal projection at `HEAD`: `direct=79/527`, `projected=99/516`, `union=117/853`
- **`lua` (3-commit negative control: `108e0bdc` → `3f4f2801` → `c42d820b`):**
  - Pure structure raw: `0.002 → 0.002 → 0.000` (`verdict=unrelated_or_clean_room`, `confirmed=0/122`, `cmt_rbh=0/7`)
