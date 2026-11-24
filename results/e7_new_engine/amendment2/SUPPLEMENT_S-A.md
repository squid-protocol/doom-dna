# Supplement S-A: how much one decoy shuffle can move a result (DOOM-E7 Amendment 2)

Built by `measure/e7_supp_table.py` from `draws_long.csv` and `pair_diagnostics.csv` (2,550 ordered pairs, 25 shuffles each; seed 0 is E7's draw). Share = twins / eligible functions of the query. `c` = fraction of the 25 single shuffles in which the cutoff was above zero (a single shuffle certifies nothing below it). In the bar: `-` spans the min to max of the single shuffles, `|` the median, `E` E7's value, `P` the primary pooled value.

How to read it: where the dashes are short and E and P coincide (`chocolate-doom`, `crispy-doom`) a single shuffle was enough. Where the dashes are long or E and P are far apart (`inter-doom`, `fastdoom`, `prboom-plus`) E7's one draw was one of two or more possible answers. Pairs with `c` near 0 and short dashes (`woof`, `srb2`, `gzdoom`) are not noisy; the single-shuffle rule simply cannot certify them, and the pooled rule can.

## `linuxdoom` against each port (all 50)

| port | E7 (seed 0) | conservative | primary (pooled) | 25 single shuffles: min / p10 / median / p90 / max | c | class | 0 ... 0.6 |
|---|---:|---:|---:|---|---:|---|---|
| `doomgeneric` | 0.573 | 0.575 | 0.579 | 0.556 / 0.560 / 0.575 / 0.583 / 0.585 | 1.00 | stable-certified | `                                    -eP ` |
| `sdl-doom` | 0.578 | 0.573 | 0.578 | 0.556 / 0.565 / 0.573 / 0.582 / 0.583 | 1.00 | stable-certified | `                                    -|p ` |
| `doom-ascii` | 0.566 | 0.559 | 0.565 | 0.537 / 0.545 / 0.559 / 0.566 / 0.569 | 1.00 | stable-certified | `                                   -|p  ` |
| `chocolate-doom` | 0.524 | 0.533 | 0.540 | 0.521 / 0.523 / 0.528 / 0.545 / 0.560 | 1.00 | stable-certified | `                                  eP-   ` |
| `doom-wasm` | 0.528 | 0.531 | 0.537 | 0.514 / 0.520 / 0.531 / 0.540 / 0.546 | 1.00 | stable-certified | `                                 -EP    ` |
| `crispy-doom` | 0.344 | 0.354 | 0.366 | 0.338 / 0.344 / 0.354 / 0.366 / 0.370 | 1.00 | stable-certified | `                      E|P               ` |
| `fastdoom` | 0.173 | 0.028 | 0.215 | 0.028 / 0.028 / 0.202 / 0.223 / 0.239 | 0.80 | UNSTABLE | `  ---------E-|P--                       ` |
| `inter-doom` | 0.081 | 0.081 | 0.145 | 0.081 / 0.081 / 0.081 / 0.171 / 0.174 | 0.36 | UNSTABLE | `     e---P--                            ` |
| `doom-ios` | 0.026 | 0.026 | 0.144 | 0.026 / 0.026 / 0.026 / 0.154 / 0.176 | 0.24 | UNSTABLE | `  e------P--                            ` |
| `prboom-plus` | 0.025 | 0.025 | 0.119 | 0.025 / 0.025 / 0.025 / 0.097 / 0.152 | 0.12 | UNSTABLE | `  e-----P--                             ` |
| `dsda-doom` | 0.017 | 0.017 | 0.099 | 0.017 / 0.017 / 0.017 / 0.017 / 0.017 | 0.00 | stable-uncertified | ` e    P                                 ` |
| `mood` | 0.071 | 0.071 | 0.077 | 0.071 / 0.071 / 0.071 / 0.071 / 0.071 | 0.00 | stable-uncertified | `     p                                  ` |
| `mochadoom` | 0.057 | 0.057 | 0.067 | 0.057 / 0.057 / 0.057 / 0.057 / 0.057 | 0.00 | stable-uncertified | `    p                                   ` |
| `woof` | 0.009 | 0.009 | 0.064 | 0.009 / 0.009 / 0.009 / 0.009 / 0.009 | 0.00 | stable-uncertified | ` e  P                                   ` |
| `nugget-doom` | 0.009 | 0.009 | 0.064 | 0.009 / 0.009 / 0.009 / 0.009 / 0.009 | 0.00 | stable-uncertified | ` e  P                                   ` |
| `srb2` | 0.019 | 0.019 | 0.061 | 0.019 / 0.019 / 0.019 / 0.019 / 0.019 | 0.00 | stable-uncertified | ` e  P                                   ` |
| `doom3-bfg` | 0.000 | 0.000 | 0.052 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `e  P                                    ` |
| `quake2` | 0.010 | 0.010 | 0.038 | 0.010 / 0.010 / 0.010 / 0.010 / 0.010 | 0.00 | stable-uncertified | ` eP                                     ` |
| `doom3do` | 0.007 | 0.007 | 0.020 | 0.007 / 0.007 / 0.007 / 0.007 / 0.007 | 0.00 | stable-uncertified | `eP                                      ` |
| `helion` | 0.007 | 0.007 | 0.015 | 0.007 / 0.007 / 0.007 / 0.007 / 0.007 | 0.00 | stable-uncertified | `eP                                      ` |
| `quake` | 0.004 | 0.004 | 0.015 | 0.004 / 0.004 / 0.004 / 0.004 / 0.004 | 0.00 | stable-uncertified | `eP                                      ` |
| `doomsday` | 0.006 | 0.006 | 0.015 | 0.006 / 0.006 / 0.006 / 0.006 / 0.006 | 0.00 | stable-uncertified | `eP                                      ` |
| `libuv` | 0.006 | 0.006 | 0.015 | 0.006 / 0.006 / 0.006 / 0.006 / 0.006 | 0.00 | stable-uncertified | `eP                                      ` |
| `nginx` | 0.001 | 0.001 | 0.012 | 0.001 / 0.001 / 0.001 / 0.001 / 0.001 | 0.00 | stable-uncertified | `eP                                      ` |
| `gzdoom` | 0.003 | 0.003 | 0.012 | 0.003 / 0.003 / 0.003 / 0.003 / 0.003 | 0.00 | stable-uncertified | `eP                                      ` |
| `doo-cr` | 0.000 | 0.000 | 0.010 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `eP                                      ` |
| `doomretro` | 0.004 | 0.004 | 0.007 | 0.004 / 0.004 / 0.004 / 0.004 / 0.004 | 0.00 | stable-uncertified | `p                                       ` |
| `room4doom` | 0.004 | 0.004 | 0.006 | 0.004 / 0.004 / 0.004 / 0.004 / 0.004 | 0.00 | stable-uncertified | `p                                       ` |
| `managed-doom` | 0.000 | 0.000 | 0.006 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `curl` | 0.003 | 0.003 | 0.003 | 0.003 / 0.003 / 0.003 / 0.003 / 0.003 | 0.00 | stable-uncertified | `p                                       ` |
| `dartdoom` | 0.003 | 0.003 | 0.003 | 0.003 / 0.003 / 0.003 / 0.003 / 0.003 | 0.00 | stable-uncertified | `p                                       ` |
| `puredoom` | 0.001 | 0.001 | 0.001 | 0.001 / 0.001 / 0.001 / 0.001 / 0.001 | 0.00 | stable-uncertified | `p                                       ` |
| `odamex` | 0.001 | 0.001 | 0.001 | 0.001 / 0.001 / 0.001 / 0.001 / 0.001 | 0.00 | stable-uncertified | `p                                       ` |
| `rust-doom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `cssdoom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `gore` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `doom-fx` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `fps-cob` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `kocoa-doom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `fsharp-doom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `eternity` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `edge-classic` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `freedoom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `doomf77` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `sqldoom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `leveldb` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `agentic-cobol-doom-cc` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `lua` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `doom-scheme` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `agentic-cobol-doom-codex` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |

## Reference: `chocolate-doom` against its descendants

| port | E7 (seed 0) | conservative | primary (pooled) | 25 single shuffles: min / p10 / median / p90 / max | c | class | 0 ... 0.6 |
|---|---:|---:|---:|---|---:|---|---|
| `crispy-doom` | 0.789 | 0.789 | 0.790 | 0.789 / 0.789 / 0.790 / 0.792 / 0.794 | 1.00 | stable-certified | `                                       p` |
| `doom-wasm` | 0.680 | 0.683 | 0.684 | 0.677 / 0.680 / 0.684 / 0.685 / 0.685 | 1.00 | stable-certified | `                                       p` |
| `inter-doom` | 0.526 | 0.525 | 0.525 | 0.519 / 0.521 / 0.525 / 0.528 / 0.529 | 1.00 | stable-certified | `                                  p     ` |
| `sdl-doom` | 0.312 | 0.312 | 0.313 | 0.306 / 0.310 / 0.312 / 0.313 / 0.315 | 1.00 | stable-certified | `                    p                   ` |
| `doomgeneric` | 0.310 | 0.311 | 0.311 | 0.302 / 0.306 / 0.311 / 0.312 / 0.314 | 1.00 | stable-certified | `                    p                   ` |
| `doom-ascii` | 0.279 | 0.277 | 0.280 | 0.273 / 0.274 / 0.279 / 0.282 / 0.285 | 1.00 | stable-certified | `                  p-                    ` |

## All pairs

Active pairs (share at least 0.02 under the primary or conservative rule): 334. Single-shuffle class: stable-certified 149, stable-uncertified 104, unstable 81.
Most unstable pairs: `linuxdoom`>`fastdoom` (c 0.80, 0.028-0.223), `linuxdoom`>`doom-ios` (c 0.24, 0.026-0.154), `doom-ascii`>`fastdoom` (c 0.48, 0.016-0.138), `sdl-doom`>`fastdoom` (c 0.76, 0.019-0.138), `doomgeneric`>`fastdoom` (c 0.76, 0.017-0.132), `doom-ascii`>`doom-ios` (c 0.60, 0.017-0.128), `sdl-doom`>`doom-ios` (c 0.56, 0.018-0.126), `doomgeneric`>`doom-ios` (c 0.56, 0.017-0.117).
