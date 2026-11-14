# Seed-and-Extend Finding: Full 41-Port + 3-Control Sweep

* **Engine scans:** `6c7c6c1bc` (`--lens portable`, `keyword_mode="composition"`, `--seed-frac 0.15 --hops 3 --max-funcs 15000`)
* **Command:** `followups/seed-and-extend/measure.py --all --extra-scans .../controls/scans --out-csv results_all.csv`
* **Full table:** [results_all.csv](results_all.csv) (`doomsday` 23,304 and `gzdoom` 18,434 skipped due to dense `n×n` FGW memory limit).
* **Zero names or file paths are read** during seeding, `delta` calibration, or 3-hop extension.

## Summary: Controls vs. Ports

### 1. Unrelated Controls & From-Scratch Reimplementations (~0%)
| Repo | Type | Functions | Tier-1 `name` | Seed+Extend `name` | Seed+Extend `sub` |
|---|---|---:|---:|---:|---:|
| `lua` | Unrelated C | 1,666 | `0/70` (`0.0%`) | `0/493` (**`0.0%`**) | `2.4%` |
| `quake` | Unrelated C | 2,594 | `2/66` (`3.0%`) | `3/529` (**`0.6%`**) | `4.3%` |
| `quake2` | Unrelated C | 5,289 | `2/57` (`3.5%`) | `3/489` (**`0.6%`**) | `5.3%` |
| `room4doom` | Rust scratch | 4,582 | `0/71` (`0.0%`) | `0/549` (**`0.0%`**) | `9.7%` |
| `rust-doom` | Rust scratch | 582 | `0/31` (`0.0%`) | `0/196` (**`0.0%`**) | `7.1%` |
| `helion` | C# scratch | 8,386 | `0/83` (`0.0%`) | `0/579` (**`0.0%`**) | `8.5%` |
| `freedoom` | Assets | 106 | `0/15` (`0.0%`) | `0/60` (**`0.0%`**) | `0.0%` |

### 2. Selected DOOM Ports & Cross-Language Translations
| Repo | Language | Functions | Tier-1 `name` | Seed+Extend `name` | Seed+Extend `sub` |
|---|---|---:|---:|---:|---:|
| `mood` | C + COBOL | 1,859 | `110/110` (**`100.0%`**) | `687/721` (**`95.3%`**) | `99.2%` |
| `puredoom` | C (single header) | 1,546 | `98/98` (**`100.0%`**) | `590/663` (**`89.0%`**) | `14.8%` *(single file)* |
| `doomgeneric` | C | 1,192 | `97/97` (**`100.0%`**) | `547/644` (**`84.9%`**) | `91.1%` |
| `sdl-doom` | C | 1,079 | `99/99` (**`100.0%`**) | `535/650` (**`82.3%`**) | `90.5%` |
| `doom-ascii` | C | 1,019 | `98/98` (**`100.0%`**) | `517/640` (**`80.8%`**) | `90.6%` |
| `doom-wasm` | C | 2,035 | `95/96` (**`99.0%`**) | `505/641` (**`78.8%`**) | `88.1%` |
| `gore` | **Go** | 996 | `74/80` (**`92.5%`**) | `426/561` (**`75.9%`**) | `0.2%` *(flat dir)* |
| `chocolate-doom` | C | 5,129 | `95/103` (**`92.2%`**) | `433/666` (**`65.0%`**) | `79.6%` |
| `fastdoom` | C | 2,114 | `57/72` (`79.2%`) | `294/538` (**`54.6%`**) | `71.0%` |
| `doom-ios` | Obj-C / C | 1,768 | `59/84` (`70.2%`) | `267/568` (**`47.0%`**) | `68.5%` |
| `doom3-bfg` | C++ (DOOM Classic) | 13,859 | `46/89` (`51.7%`) | `259/679` (**`38.1%`**) | `51.8%` |
| `mochadoom` | **Java** | 3,037 | `10/64` (`15.6%`) | `79/490` (**`16.1%`**) | `33.5%` |
| `managed-doom` | **C#** | 1,285 | `7/53` (`13.2%`) | `59/421` (**`14.0%`**) | `38.5%` |
| `dartdoom` | **Dart** | 723 | `5/64` (`7.8%`) | `32/398` (`8.0%`) | **`62.8%`** |
| `doom-scheme` | **Scheme** | 798 | `4/54` (`7.4%`) | `16/402` (`4.0%`) | **`58.7%`** |

## Key Takeaway
* **Clean separation:** Every unrelated C codebase (`lua` `0.0%`, `quake` `0.6%`, `quake2` `0.6%`) and every from-scratch reimplementation (`room4doom`, `rust-doom`, `helion` all `0.0%`) sits at **0–0.6%**.
* **Even single-header / flat-directory ports are recovered:** `puredoom` (`89.0%`) and `gore` (`75.9%`) had near-zero directory-taxonomy scores (`14.8%` and `0.2%`) because they don't use DOOM's folder layout—yet Seed-and-Extend recovers **590** and **426** exact 1-to-1 functions respectively.
