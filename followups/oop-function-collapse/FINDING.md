# DOOM-E1 Finding: Tiny-Function Wrapper Collapse (`loc <= 5`)

* **Engine scans:** `6c7c6c1bc` (44 DOOM ports, `keyword_mode="smoothed_density"`, `min_loc=1`)
* **Command:** `followups/oop-function-collapse/measure.py --max-loc 5`

## Verdict: **Refuted** (`over_null` did not rise by `>= +0.10` on Java/Kotlin/C#)

| Port | Language | Functions (`raw -> collapsed`) | Cross-wiring (`raw -> collapsed`) | `over_null` (`raw -> collapsed`) | Delta |
|---|---|---:|---:|---:|---:|
| `mochadoom` | Java | `3,781 -> 3,602` | `0.375 -> 0.391` | `+0.010 -> +0.027` | `+0.017` |
| `kocoa-doom` | Kotlin | `3,565 -> 3,429` | `0.273 -> 0.266` | `-0.083 -> -0.089` | `-0.006` |
| `managed-doom` | C# | `1,300 -> 1,270` | `0.095 -> 0.103` | `-0.161 -> -0.142` | `+0.020` |
| `chocolate-doom` *(control)* | C | `5,169 -> 5,035` | `0.827 -> 0.828` | `+0.518 -> +0.521` | `+0.003` |
| `gore` *(control)* | Go | `1,025 -> 972` | `0.644 -> 0.639` | `+0.499 -> +0.490` | `-0.009` |
| `room4doom` *(scratch)* | Rust | `4,684 -> 4,537` | `0.086 -> 0.107` | `+0.007 -> +0.027` | `+0.020` |

## Interpretation

Collapsing `loc <= 5` pass-through wrappers (`caller -> wrapper -> callee`) removed ~136–179 nodes in Java/Kotlin, **but moved `over_null` by at most `+0.020` (no larger than the from-scratch Rust control `room4doom`)**. Short wrapper methods in the call graph are therefore **not** what hid DOOM's subsystem wiring in `mochadoom`, `kocoa-doom`, and `managed-doom`. The remaining explanations are genuine architectural reorganization into OOP classes/interfaces and/or directory-taxonomy mismatch (`DOOM-E3`).
