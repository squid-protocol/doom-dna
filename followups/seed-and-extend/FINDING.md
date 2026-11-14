# Seed-and-Extend Finding: Unsupervised Cross-Language 1-to-1 Function Alignment

* **Engine scans:** `6c7c6c1bc` (`--lens portable`, `keyword_mode="composition"`, `--seed-frac 0.15 --hops 3`)
* **Command:** `followups/seed-and-extend/measure.py`
* **Zero names or file paths are read** during seeding, `delta` calibration, or 3-hop extension. Names and subsystems are used *only* post-hoc to score precision.

## Results

| Port | Language | Tier-1 Seeds | Tier-1 `sub` | Tier-1 `name` | Seed+Extend (3 hops) | S+E `sub` | S+E `name` |
|---|---|---:|---:|---:|---:|---:|---:|
| `chocolate-doom` | C | 103 | `93.2%` | `95/103` (**92.2%**) | 666 | `79.6%` | `433/666` (**65.0%**) |
| `gore` | Go | 80 | `1.2%` *(flat dir)* | `74/80` (**92.5%**) | 561 | `0.2%` *(flat dir)* | `426/561` (**75.9%**) |
| `dartdoom` | Dart | 64 | **`82.8%`** | `5/64` (7.8%) | 398 | **`62.8%`** | `32/398` (8.0%) |
| `doom-scheme` | Scheme | 54 | **`59.3%`** | `4/54` (7.4%) | 402 | **`58.7%`** | `16/402` (4.0%) |
| `mochadoom` | Java | 64 | `20.3%` | `10/64` (**15.6%**) | 490 | `33.5%` | `79/490` (**16.1%**) |
| `room4doom` *(scratch)* | Rust | 71 | `5.6%` | `0/71` (0.0%) | 549 | `9.7%` | `0/549` (0.0%) |

## Why This Matters

* **From `0` twins to `426` 1-to-1 Go ↔ C matches:** Isolated single-function matching (`followups/cross-lang-twins`) found **0** twins in `gore`. Unsupervised FGW seeding + `delta` translation-shift calibration + 3-hop call-graph extension recovered **74/80 (92.5%)** exact Go ↔ C function pairs in Tier-1 and **426/561 (75.9%)** across the whole codebase—without reading a single identifier.
* **Works even when names are gone:** `dartdoom` (`82.8%` Tier-1, `62.8%` overall) and `doom-scheme` (`59.3%` Tier-1, `58.7%` overall) align to the right `linuxdoom` subsystems even where functions were renamed.
* **Negative control stays at 0%:** From-scratch `room4doom` gets `0/549` (`0.0%`) name matches and `9.7%` subsystem agreement.
