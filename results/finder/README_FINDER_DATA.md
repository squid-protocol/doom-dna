# Function-finder data (2026-11-25)

One file per program (`<program>.json`) plus `index.json`. 35 programs: 19 same-language ports, the development port (`chocolate-doom`), 6 translations, 6 controls, 3 held-out controls. Reference side is always `linuxdoom`.

**Per-program file:** `port`, `group` (SL same-language, DEV, T translation, K/H controls), `eligible` (functions of at least 6 lines), `gate` (coherence check: `passes`, `strong_fgw`, `mean_sup`), `tier_counts`, `pairs`.
**Each pair** = `[port_name, port_path, port_loc, ref_name, ref_path, ref_loc, tier, score, also_found_by, truth]`.
* **tier** (strictly one-to-one across tiers, best tier wins): `exact` (identical structural fingerprint, E7 setting), `twin` (fingerprint twin), `xtwin` (cross-language fingerprint preset), `seed` (reciprocal graph seeds, top 15%), `ext1`/`ext2`/`ext3` (extension by hop, calibrated: the published method).
* **also_found_by**: other tiers that matched the same pair.
* **truth** (a check, never used to choose a pair): same-language = `near` (text-similarity at least 0.9), `derived` (0.6 to 0.9), `none` (not listed: not proof of a wrong match), `unmapped`; translations = `name-match` / `no-name-match` (function-name agreement, a lower bound that misses renamed ports); controls = `control`.

**index.json:** per-program summaries and `tier_truth_by_group`, the pooled tier-by-truth table the page uses to say how far to trust each tier.

**Not in the data:** the fingerprint sweep settings other than the registered one; pairs for programs above 10,000 functions; anything about subsystems or architecture.
Source: `measure/finder_export.py` (reuses `measure/e12_ladder.py`; one output field, `E3c_hop_ends`, was added after the E12 run and changes no result).
