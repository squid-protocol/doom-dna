# DOOM-E2 Finding: `composition` vs. `density` on Cross-Language Blind Placement

* **Engine scans:** `6c7c6c1bc` (`--lens portable`, `--draws 200 --rewire-draws 1`)
* **Command:** `python -m structural_fingerprint.blind ... --ports gore,dartdoom,doom-scheme,mochadoom --keyword-mode {density,composition}`

## Results

| Port | Language | `density` acc (null) | `composition` acc (null) | `acc` delta | `composition` wiring (full / off) |
|---|---|---:|---:|---:|---|
| `gore` | Go | `0.603 (0.204)` | **`0.622 (0.198)`** | **`+0.019` (`+0.025` over null)** | `0.962 / 0.771` *(was `0.956 / 0.712`)* |
| `dartdoom` | Dart | `0.475 (0.238)` | `0.475 (0.238)` | `0.000` | `0.940 / 0.637` *(was `0.950 / 0.735`)* |
| `doom-scheme` | Scheme | `0.456 (0.260)` | `0.454 (0.261)` | `-0.002` | `0.933 / 0.598` *(was `0.933 / 0.626`)* |
| `mochadoom` | Java | `0.205 (0.165)` | `0.202 (0.160)` | `-0.003` | `0.919 / 0.527` *(was `0.919 / 0.515`)* |

## Interpretation

* **Within `blind.py`:** Switching from per-100-LOC `density` to `composition` (`hits_i / sum(hits)`) lifted `gore` (Go) blind placement accuracy from **60.3% to 62.2%** (`+2.5 pts` over null) while holding `dartdoom` and `doom-scheme` steady.
* **Why the gain is modest:** `blind.py` already rank-normalizes every feature column within each repository, which removes much of the language-verbosity offset before `composition` runs.
* **Next:** To test direct **function-to-function** cross-language keyword matching without subsystem buckets, add within-repo rank-normalization or cosine-on-composition to `twins.py`.
