# Cross-Language Function Twins (`followups/cross-lang-twins`)

* **Engine scans:** `6c7c6c1bc` (`--lens portable`, `TwinParams(min_loc=6, ratio=0.85, fdr=0.05)`)
* **Command:** `followups/cross-lang-twins/measure.py`

## Results

| Port | Language | Mode | Twins (`eligible`) | `same_sub` | `same_name` |
|---|---|---|---:|---:|---:|
| `chocolate-doom` | C | `baseline(dens,raw)` | `420 (4,490)` | `91.4%` | `90.5%` |
| `chocolate-doom` | C | `e3(comp,rank_norm)` | `272 (4,490)` | `77.2%` | `69.1%` |
| `gore` | Go | `baseline(dens,raw)` | `0 (812)` | `n/a` | `n/a` |
| `gore` | Go | `e3(comp,rank_norm)` | `0 (812)` | `n/a` | `n/a` |
| `dartdoom` | Dart | `baseline(dens,raw)` | `1 (576)` | `0.0%` | `0.0%` |
| `dartdoom` | Dart | `e3(comp,rank_norm)` | `0 (576)` | `n/a` | `n/a` |
| `doom-scheme` | Scheme | `baseline(dens,raw)` | `0 (585)` | `n/a` | `n/a` |
| `doom-scheme` | Scheme | `e3(comp,rank_norm)` | `0 (585)` | `n/a` | `n/a` |
| `mochadoom` | Java | `baseline(dens,raw)` | `44 (1,751)` | `68.2%` | `86.4%` |
| `mochadoom` | Java | `e3(comp,rank_norm)` | `29 (1,751)` | `75.9%` | **`96.6%`** |
| `room4doom` *(scratch)* | Rust | `baseline` / `e3` | `1` / `0` | `0.0%` / `n/a` | `0.0%` / `n/a` |

## Interpretation

* **Why `gore`, `dartdoom`, and `doom-scheme` still yield `0` twins:** Even after removing language offsets with within-repo rank normalization and `composition`, a translated function does not sit close enough to a single `linuxdoom` function in isolation to beat a shuffled-feature decoy (`fdr=0.05`) and Lowe's ratio test (`0.85`). Cross-language alignment lives in the **call-graph neighborhood** (`blind.py`'s FGW: `62.2%` on `gore`), not in isolated single-function keyword vectors.
* **Precision vs. recall trade-off:** On `mochadoom` (where some functions were ported 1-to-1), `composition + rank_norm` raised name-agreement precision from `86.4%` to **`96.6%`** (`29` twins). Within the same language (`chocolate-doom`), raw `density` remains far superior (`420` twins at `90.5%` vs. `272` at `69.1%`).
