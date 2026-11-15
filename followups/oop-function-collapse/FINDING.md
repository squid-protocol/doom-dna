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

Collapsing `loc <= 5` pass-through wrappers (`caller -> wrapper -> callee`) removed ~136–179 nodes in Java/Kotlin, **but moved `over_null` by at most `+0.020` (no larger than the from-scratch Rust control `room4doom`)**. Short wrapper methods in the call graph are therefore **not** what hid DOOM's subsystem wiring in `mochadoom`, `kocoa-doom`, and `managed-doom` under the old `smoothed_density` subway metric.

---

## Refined DOOM-E1 (Seed-and-Extend, `composition` mode + `delta` calibration)

* **Command:** `followups/oop-function-collapse/measure_seed_extend.py --max-loc 5`
* **Question:** When measured with unsupervised **Seed-and-Extend** (`composition` mode + `delta` calibration) instead of `smoothed_density` subway `over_null`, does collapsing `loc <= 5` OOP wrappers improve 1-to-1 function recovery?

| Port | Language | Functions (`raw -> collapsed`) | Tier-1 `name` (`raw -> col`) | Seed+Extend `name` (`raw -> col`) | Delta |
|---|---|---:|---:|---:|---:|
| `mochadoom` | Java | `3,037 -> 2,858` | `10/64 (15.6%) -> 10/62 (16.1%)` | `79/490 (16.1%) -> 87/466 (18.7%)` | **`+2.6%` (`+8` hits)** |
| `managed-doom` | C# | `1,285 -> 1,255` | `7/53 (13.2%) -> 8/52 (15.4%)` | `59/421 (14.0%) -> 82/435 (18.9%)` | **`+4.9%` (`+23` hits)** |
| `kocoa-doom` | Kotlin | `2,902 -> 2,766` | `3/57 (5.3%) -> 3/54 (5.6%)` | `18/405 (4.4%) -> 12/349 (3.4%)` | `-1.0%` |
| `chocolate-doom` *(ctrl)* | C | `5,129 -> 4,995` | `95/103 (92.2%) -> 92/102 (90.2%)` | `433/666 (65.0%) -> 409/638 (64.1%)` | `-0.9%` |
| `gore` *(ctrl)* | Go | `996 -> 943` | `74/80 (92.5%) -> 71/77 (92.2%)` | `426/561 (75.9%) -> 426/561 (75.9%)` | `0.0%` |
| `room4doom` *(scratch)* | Rust | `4,582 -> 4,435` | `0/71 (0.0%) -> 0/67 (0.0%)` | `0/549 (0.0%) -> 0/487 (0.0%)` | `0.0%` |

### Refined Interpretation
* **Partial rescue in Java & C#:** Collapsing `loc <= 5` pass-through wrappers measurably helps Seed-and-Extend 1-hop propagation in **`managed-doom`** (`59 -> 82` exact hits, **+39% more recovered functions**, `14.0% -> 18.9%`) and **`mochadoom`** (`79 -> 87` exact hits, `16.1% -> 18.7%`), while leaving `gore` (`75.9%`) and `room4doom` (`0.0%`) unchanged.
* **Why:** Short OOP getters/wrappers act as 1-hop "bridges" that block Seed-and-Extend's 1-hop neighbor matching in Java/C#; contracting `caller -> wrapper -> callee` reconnects the underlying DOOM call edges without inflating false positives on scratch rewrites.
