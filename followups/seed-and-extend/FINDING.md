# Seed-and-Extend Finding: Full 41-Port + 3-Control Sweep

* **Engine scans:** `6c7c6c1bc` (`--lens portable`, `keyword_mode="composition"`, `NO_COMPLEXITY`, `--seed-frac 0.15 --hops 3 --max-funcs 15000`)
* **Command:** `followups/seed-and-extend/measure.py --all --extra-scans .../controls/scans --out-csv results_all.csv`
* **Full table:** [results_all.csv](results_all.csv) (`doomsday` 23,304 and `gzdoom` 18,434 skipped due to dense `n×n` FGW memory limit).
* **Zero names or file paths are read** during seeding, `delta` calibration, or 3-hop extension.

## Summary: Controls vs. Ports

### 1. Unrelated Controls & From-Scratch Reimplementations (~0%)
| Repo | Type | Functions | Tier-1 `name` | Seed+Extend `name` | Seed+Extend `sub` |
|---|---|---:|---:|---:|---:|
| `lua` | Unrelated C | 1,666 | `0/70` (`0.0%`) | `0/492` (**`0.0%`**) | `2.6%` |
| `quake` | Unrelated C | 2,594 | `2/66` (`3.0%`) | `4/533` (**`0.8%`**) | `3.4%` |
| `quake2` | Unrelated C | 5,289 | `2/57` (`3.5%`) | `3/494` (**`0.6%`**) | `5.7%` |
| `room4doom` | Rust scratch | 4,582 | `0/71` (`0.0%`) | `0/548` (**`0.0%`**) | `9.5%` |
| `rust-doom` | Rust scratch | 582 | `0/31` (`0.0%`) | `0/208` (**`0.0%`**) | `7.2%` |
| `helion` | C# scratch | 8,386 | `0/83` (`0.0%`) | `0/589` (**`0.0%`**) | `6.6%` |
| `freedoom` | Assets | 106 | `0/15` (`0.0%`) | `0/61` (**`0.0%`**) | `0.0%` |

### 2. Selected DOOM Ports & Cross-Language Translations
| Repo | Language | Functions | Tier-1 `name` | Seed+Extend `name` | Seed+Extend `sub` |
|---|---|---:|---:|---:|---:|
| `mood` | C + COBOL | 1,859 | `110/110` (**`100.0%`**) | `691/725` (**`95.3%`**) | `99.3%` |
| `puredoom` | C (single header) | 1,546 | `98/98` (**`100.0%`**) | `596/663` (**`89.9%`**) | `15.1%` *(single file)* |
| `doomgeneric` | C | 1,192 | `97/97` (**`100.0%`**) | `550/642` (**`85.7%`**) | `92.2%` |
| `sdl-doom` | C | 1,079 | `99/99` (**`100.0%`**) | `545/653` (**`83.5%`**) | `90.5%` |
| `doom-ascii` | C | 1,019 | `98/98` (**`100.0%`**) | `527/639` (**`82.5%`**) | `91.2%` |
| `doom-wasm` | C | 2,035 | `95/96` (**`99.0%`**) | `518/642` (**`80.7%`**) | `90.0%` |
| `gore` | **Go** | 996 | `74/80` (**`92.5%`**) | `430/561` (**`76.6%`**) | `0.2%` *(flat dir)* |
| `chocolate-doom` | C | 5,129 | `95/103` (**`92.2%`**) | `443/664` (**`66.7%`**) | `80.6%` |
| `fastdoom` | C | 2,114 | `57/72` (`79.2%`) | `301/547` (**`55.0%`**) | `70.0%` |
| `doom-ios` | Obj-C / C | 1,768 | `59/84` (`70.2%`) | `279/572` (**`48.8%`**) | `70.1%` |
| `doom3-bfg` | C++ (DOOM Classic) | 13,859 | `46/89` (`51.7%`) | `265/671` (**`39.5%`**) | `52.9%` |
| `mochadoom` | **Java** | 3,037 | `10/64` (`15.6%`) | `86/483` (**`17.8%`**) | `33.5%` |
| `managed-doom` | **C#** | 1,285 | `7/53` (`13.2%`) | `66/412` (**`16.0%`**) | `40.8%` |
| `dartdoom` | **Dart** | 723 | `5/64` (`7.8%`) | `34/394` (`8.6%`) | **`65.2%`** |
| `doom-scheme` | **Scheme** | 798 | `4/54` (`7.4%`) | `19/398` (`4.8%`) | **`59.8%`** |

## Key Takeaway
* **Clean separation:** Every unrelated C codebase (`lua` `0.0%`, `quake` `0.8%`, `quake2` `0.6%`) and every from-scratch reimplementation (`room4doom`, `rust-doom`, `helion` all `0.0%`) sits at **0–0.8%**.
* **Even single-header / flat-directory ports are recovered:** `puredoom` (`89.9%`) and `gore` (`76.6%`) had near-zero directory-taxonomy scores (`15.1%` and `0.2%`) because they don't use DOOM's folder layout—yet Seed-and-Extend recovers **596** and **430** exact 1-to-1 functions respectively.
