# Translation Vector & Seed-and-Extend (`followups/translation-shift`)

* **Engine scans:** `6c7c6c1bc` (name-paired functions `>= 6` LOC vs. `linuxdoom`)
* **Command:** `followups/translation-shift/measure.py`

## 1. Systematic Translation Shifts (C → Target Language)

| Port | Paired funcs | Strongest correlations (`r`) | Systematic shifts (`mean(port - C)`) |
|---|---:|---|---|
| `gore` (Go) | 510 | `log_args` `0.996`, `log_complexity` `0.935`, `log_loc` `0.908`, `struct_branch` `0.853` | `log_loc` `-0.339`, `struct_func_start` `+0.276`, `struct_branch` `+0.302` |
| `dartdoom` (Dart) | 26 | `log_args` `0.840`, `keyword_density` `0.794`, `func_internal_density` `0.747` | `bitwise_ops` `+0.554`, `struct_args` `-0.677` |
| `doom-scheme` (Scheme) | 52 | `def_cleanup` `0.888`, `log_complexity` `0.711`, `arch_io` `0.705`, `log_loc` `0.697` | `log_loc` `-0.865`, `log_complexity` `-0.493`, `arch_io` `+0.267` |
| `mochadoom` (Java) | 155 | `state_flux` `0.883`, `bitwise_ops` `0.844`, `state_bailout_hits` `0.767` | `state_flux` `-0.149`, `bitwise_ops` `-0.149`, `log_loc` `-0.090` |

## 2. 1-to-1 Exact Function Recall: Global vs. Mean-Shifted vs. Tier-2 Anchor Propagation

| Port | Global cosine | Mean-shifted cosine | Tier-2 (1-hop from top-20% anchors) |
|---|---:|---:|---:|
| `gore` | `10.8%` | `17.8%` | **`59.9%` (`124/207`)** |
| `dartdoom` | `0.0%` | `11.5%` | `n/a (0/0)` |
| `doom-scheme` | `7.7%` | `3.8%` | **`50.0%` (`3/6`)** |
| `mochadoom` | `27.1%` | `14.2%` | **`65.0%` (`13/20`)** |

*Caveat:* The Tier-1 seed set in this diagnostic used the top-20% highest-similarity pairs with their true `linuxdoom` targets as anchors; a production matcher must seed Tier-1 from unsupervised high-confidence FGW / unique landmark matches and iterate outward.
