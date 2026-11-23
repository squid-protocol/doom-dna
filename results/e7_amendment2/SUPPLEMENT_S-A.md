# Supplement S-A: how much one decoy shuffle can move a result (DOOM-E7 Amendment 2)

Built by `measure/e7_supp_table.py` from `draws_long.csv` and `pair_diagnostics.csv` (2,550 ordered pairs, 25 shuffles each; seed 0 is E7's draw). Share = twins / eligible functions of the query. `c` = fraction of the 25 single shuffles in which the cutoff was above zero (a single shuffle certifies nothing below it). In the bar: `-` spans the min to max of the single shuffles, `|` the median, `E` E7's value, `P` the primary pooled value.

How to read it: where the dashes are short and E and P coincide (`chocolate-doom`, `crispy-doom`) a single shuffle was enough. Where the dashes are long or E and P are far apart (`inter-doom`, `fastdoom`, `prboom-plus`) E7's one draw was one of two or more possible answers. Pairs with `c` near 0 and short dashes (`woof`, `srb2`, `gzdoom`) are not noisy; the single-shuffle rule simply cannot certify them, and the pooled rule can.

## `linuxdoom` against each port (all 50)

| port | E7 (seed 0) | conservative | primary (pooled) | 25 single shuffles: min / p10 / median / p90 / max | c | class | 0 ... 0.6 |
|---|---:|---:|---:|---|---:|---|---|
| `doomgeneric` | 0.573 | 0.575 | 0.579 | 0.554 / 0.559 / 0.573 / 0.582 / 0.583 | 1.00 | stable-certified | `                                    -eP ` |
| `sdl-doom` | 0.578 | 0.573 | 0.578 | 0.554 / 0.562 / 0.573 / 0.582 / 0.582 | 1.00 | stable-certified | `                                    -|p ` |
| `doom-ascii` | 0.563 | 0.563 | 0.565 | 0.537 / 0.545 / 0.560 / 0.566 / 0.569 | 1.00 | stable-certified | `                                   -|p  ` |
| `chocolate-doom` | 0.559 | 0.538 | 0.547 | 0.521 / 0.527 / 0.536 / 0.548 / 0.559 | 1.00 | stable-certified | `                                  -|p   ` |
| `doom-wasm` | 0.538 | 0.536 | 0.540 | 0.517 / 0.525 / 0.531 / 0.542 / 0.547 | 1.00 | stable-certified | `                                  -p-   ` |
| `crispy-doom` | 0.354 | 0.356 | 0.367 | 0.340 / 0.349 / 0.356 / 0.367 / 0.373 | 1.00 | stable-certified | `                      -eP               ` |
| `fastdoom` | 0.151 | 0.180 | 0.215 | 0.028 / 0.077 / 0.196 / 0.227 / 0.251 | 0.88 | UNSTABLE | `  --------E--|P--                       ` |
| `doom-ios` | 0.026 | 0.026 | 0.145 | 0.026 / 0.026 / 0.026 / 0.161 / 0.183 | 0.36 | UNSTABLE | `  e------P---                           ` |
| `inter-doom` | 0.168 | 0.080 | 0.141 | 0.080 / 0.080 / 0.080 / 0.154 / 0.171 | 0.28 | UNSTABLE | `     |---P-E                            ` |
| `prboom-plus` | 0.025 | 0.025 | 0.120 | 0.025 / 0.025 / 0.025 / 0.025 / 0.025 | 0.00 | stable-uncertified | `  e     P                               ` |
| `dsda-doom` | 0.019 | 0.019 | 0.102 | 0.019 / 0.019 / 0.019 / 0.019 / 0.019 | 0.00 | stable-uncertified | ` e     P                                ` |
| `mood` | 0.071 | 0.071 | 0.077 | 0.071 / 0.071 / 0.071 / 0.071 / 0.071 | 0.00 | stable-uncertified | `     p                                  ` |
| `woof` | 0.009 | 0.009 | 0.070 | 0.009 / 0.009 / 0.009 / 0.009 / 0.009 | 0.00 | stable-uncertified | ` e   P                                  ` |
| `mochadoom` | 0.057 | 0.057 | 0.067 | 0.057 / 0.057 / 0.057 / 0.057 / 0.057 | 0.00 | stable-uncertified | `    p                                   ` |
| `srb2` | 0.019 | 0.019 | 0.064 | 0.019 / 0.019 / 0.019 / 0.019 / 0.019 | 0.00 | stable-uncertified | ` e  P                                   ` |
| `doom3-bfg` | 0.000 | 0.000 | 0.062 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `e   P                                   ` |
| `nugget-doom` | 0.009 | 0.009 | 0.061 | 0.009 / 0.009 / 0.009 / 0.009 / 0.009 | 0.00 | stable-uncertified | ` e  P                                   ` |
| `quake2` | 0.012 | 0.012 | 0.048 | 0.012 / 0.012 / 0.012 / 0.012 / 0.012 | 0.00 | stable-uncertified | ` e P                                    ` |
| `doom3do` | 0.007 | 0.007 | 0.029 | 0.007 / 0.007 / 0.007 / 0.007 / 0.007 | 0.00 | stable-uncertified | `e P                                     ` |
| `libuv` | 0.007 | 0.007 | 0.016 | 0.007 / 0.007 / 0.007 / 0.007 / 0.007 | 0.00 | stable-uncertified | `eP                                      ` |
| `gzdoom` | 0.006 | 0.006 | 0.015 | 0.006 / 0.006 / 0.006 / 0.006 / 0.006 | 0.00 | stable-uncertified | `eP                                      ` |
| `helion` | 0.006 | 0.006 | 0.015 | 0.006 / 0.006 / 0.006 / 0.006 / 0.006 | 0.00 | stable-uncertified | `eP                                      ` |
| `doomsday` | 0.006 | 0.006 | 0.013 | 0.006 / 0.006 / 0.006 / 0.006 / 0.006 | 0.00 | stable-uncertified | `eP                                      ` |
| `quake` | 0.004 | 0.004 | 0.010 | 0.004 / 0.004 / 0.004 / 0.004 / 0.004 | 0.00 | stable-uncertified | `eP                                      ` |
| `doomretro` | 0.004 | 0.004 | 0.010 | 0.004 / 0.004 / 0.004 / 0.004 / 0.004 | 0.00 | stable-uncertified | `eP                                      ` |
| `curl` | 0.003 | 0.003 | 0.009 | 0.003 / 0.003 / 0.003 / 0.003 / 0.003 | 0.00 | stable-uncertified | `eP                                      ` |
| `doo-cr` | 0.000 | 0.000 | 0.007 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `managed-doom` | 0.001 | 0.001 | 0.006 | 0.001 / 0.001 / 0.001 / 0.001 / 0.001 | 0.00 | stable-uncertified | `p                                       ` |
| `dartdoom` | 0.003 | 0.003 | 0.006 | 0.003 / 0.003 / 0.003 / 0.003 / 0.003 | 0.00 | stable-uncertified | `p                                       ` |
| `room4doom` | 0.004 | 0.004 | 0.004 | 0.004 / 0.004 / 0.004 / 0.004 / 0.004 | 0.00 | stable-uncertified | `p                                       ` |
| `odamex` | 0.001 | 0.001 | 0.001 | 0.001 / 0.001 / 0.001 / 0.001 / 0.001 | 0.00 | stable-uncertified | `p                                       ` |
| `puredoom` | 0.001 | 0.001 | 0.001 | 0.001 / 0.001 / 0.001 / 0.001 / 0.001 | 0.00 | stable-uncertified | `p                                       ` |
| `nginx` | 0.001 | 0.001 | 0.001 | 0.001 / 0.001 / 0.001 / 0.001 / 0.001 | 0.00 | stable-uncertified | `p                                       ` |
| `rust-doom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `edge-classic` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `leveldb` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `doomf77` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `agentic-cobol-doom-codex` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `agentic-cobol-doom-cc` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `sqldoom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `eternity` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `gore` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `kocoa-doom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `fps-cob` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `doom-fx` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `freedoom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `lua` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `cssdoom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `doom-scheme` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |
| `fsharp-doom` | 0.000 | 0.000 | 0.000 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.00 | stable-uncertified | `p                                       ` |

## Reference: `chocolate-doom` against its descendants

| port | E7 (seed 0) | conservative | primary (pooled) | 25 single shuffles: min / p10 / median / p90 / max | c | class | 0 ... 0.6 |
|---|---:|---:|---:|---|---:|---|---|
| `crispy-doom` | 0.790 | 0.790 | 0.791 | 0.789 / 0.789 / 0.790 / 0.793 / 0.795 | 1.00 | stable-certified | `                                       p` |
| `doom-wasm` | 0.686 | 0.681 | 0.683 | 0.678 / 0.680 / 0.682 / 0.684 / 0.686 | 1.00 | stable-certified | `                                       p` |
| `inter-doom` | 0.525 | 0.524 | 0.525 | 0.519 / 0.523 / 0.525 / 0.527 / 0.529 | 1.00 | stable-certified | `                                  p     ` |
| `sdl-doom` | 0.312 | 0.311 | 0.312 | 0.308 / 0.309 / 0.311 / 0.313 / 0.316 | 1.00 | stable-certified | `                    p-                  ` |
| `doomgeneric` | 0.310 | 0.310 | 0.310 | 0.305 / 0.307 / 0.310 / 0.311 / 0.314 | 1.00 | stable-certified | `                    p                   ` |
| `doom-ascii` | 0.279 | 0.277 | 0.280 | 0.273 / 0.274 / 0.279 / 0.282 / 0.285 | 1.00 | stable-certified | `                  p-                    ` |

## All pairs

Active pairs (share at least 0.02 under the primary or conservative rule): 352. Single-shuffle class: stable-certified 156, stable-uncertified 116, unstable 80.
Most unstable pairs: `linuxdoom`>`fastdoom` (c 0.88, 0.077-0.227), `linuxdoom`>`doom-ios` (c 0.36, 0.026-0.161), `doom-ascii`>`doom-ios` (c 0.64, 0.016-0.137), `sdl-doom`>`fastdoom` (c 0.76, 0.019-0.138), `sdl-doom`>`doom-ios` (c 0.60, 0.017-0.135), `doomgeneric`>`fastdoom` (c 0.76, 0.017-0.125), `doom-ascii`>`prboom-plus` (c 0.40, 0.026-0.129), `sdl-doom`>`prboom-plus` (c 0.76, 0.040-0.143).
