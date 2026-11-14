# Standardizing Structural Keyword Interpretation

GitGalaxy extracts raw keyword-family hit counts per function (`hits_i`) alongside `loc`, `complexity`, and `args`. In earlier DOOM analyses, mixing raw counts, unsmoothed densities, and presence caused distortion—most visibly on Java (`mochadoom`, 34% of functions `<= 3` LOC) and Kotlin (`kocoa-doom`, 43% `<= 3` LOC) vs. C (`< 2%` `<= 3` LOC).

All DOOM study scripts and `structural-fingerprint-scanner` (`sfs`) analyses must explicitly name which of the **four standardized modes** they use:

## 1. Presence (`presence`)
* **Formula:** `1.0 if hits_i > 0 else 0.0`
* **Invariant to:** Formatting, line-splitting, and repetition within a function.
* **Use for:** Tiny functions (`loc <= 5`), capability checklists, and cross-language presence profiles.
* **Do not use for:** Comparing large functions (saturates to all-1s).

## 2. Raw Counts (`counts`)
* **Formula:** `log1p(hits_i)`
* **Invariant to:** Line-splitting (multiline vs. one-liner).
* **Use for:** Repo-level and subsystem-level totals / surface mass.
* **Do not use for:** Function-to-function matching across different sizes (collapses to `LOC`).

## 3. Smoothed Density (`smoothed_density`) vs. Legacy Density (`density`)
* **Legacy formula (`density`):** `log1p(min(hits_i / max(loc, 1) * 100, cap_i))`
  * *Known flaw:* On a 2-line getter with 1 `return` or `if`, `hits / loc * 100 = 50`, slamming into `cap_i` and inflating noise on OOP wrappers.
* **Standardized formula (`smoothed_density`):** `log1p(min(hits_i / (loc + k) * 100, cap_i))` with `k = 5.0`
* **Use for:** Within-language function twin matching (`sfs twins`), ideally paired with `--min-loc 10` for high-precision matching.

## 4. Composition / Share (`composition`)
* **Formula:** `hits_i / max(sum_j(hits_j), 1.0)`
* **Invariant to:** Both line-splitting verbosity *and* language-level boilerplate density.
* **Use for:** Cross-language comparisons (*"what mix of branching, state, memory, and I/O does this unit perform?"*).
* **Do not use for:** Zero-signal getters (`sum_j(hits_j) == 0`), which must be flagged as `empty_signature` rather than treated as `0.0`.
