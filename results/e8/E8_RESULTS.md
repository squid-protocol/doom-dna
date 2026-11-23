# DOOM-E8 results: how name sharing and structure sharing with linuxdoom change over a port's history

Registered 2026-11-22 16:17 EST ([protocol](../../preregistration/E8_HALF_LIFE.md), [Amendment 1](../../preregistration/E8_AMENDMENT_1.md), [Amendment 2](../../preregistration/E8_AMENDMENT_2.md)). Scripts committed 16:30 EST and measurement outputs committed 16:50 EST (commit `c80dd06`), both before the analysis was run. Engine `704cb35f0`, sfs `bcd3cb7`. 281 distinct snapshot scans, 11 independent lineages, all numbers below from the registered analysis ([phase_report.md](analysis/phase_report.md)).

## The answer in plain terms

**The owner's hypotheses were: names stay constant over a port's history, structure rises toward the origin, and a copying date can be read off the decay. The data do not support them as stated.**

1. **Names are not flat. They decay too, about as much as structure.** The median fall in linuxdoom-name survival from a port's earliest usable snapshot to its head is **0.11** (95% interval 0.08 to 0.14), against 0.09 for structure. The names-flat test was **not met**, and structure's trend was no steeper than names' (paired test p 0.84).
2. **Structure's decay is real in some lineages and absent in others.** In 8 of 11 lineages structure survival falls with age, and the median rank correlation is -0.71 (the effect-size bar of -0.6 is met). But the registered significance test did not survive correction (raw p 0.04, corrected 0.12), and only 5 of 11 lineages lose at least 0.10. The strongest cases are close copies: **Chocolate Doom 0.88 to 0.55** (names 0.90 to 0.83), fastdoom 0.51 lower, doomretro 0.11. Lineages whose code line is Boom, MBF or ZDoom (gzdoom, odamex, edge-classic) start low and stay flat.
3. **The structure trend is entangled with repository growth.** Controlling for the snapshot's function count, the structure trend disappears (median rank correlation becomes 0). Repositories grow from hundreds to thousands of functions, and more candidate functions crowd the one-to-one matching. This conclusion is flagged **fragile**.
4. **A date cannot be read off the head snapshot.** Age estimated from self-origin survival did not beat naive baselines (median error 56% for structure, 23% for names, against 32% for a constant guess); no method was significantly better, and two ports were at the floor and unestimable.
5. **Fork dates from post-fork divergence: 2 of 3 same-language pairs recovered, structure no better than names.** For `dsda-doom` from `prboom-plus` (git truth 2020-11-09) the error was 0.05 to 0.35 years; for `nugget-doom` from `woof` (2021-08-31) 0.00 to 0.75 years, names being closest. Both beat the midpoint baseline and the placebos. `crispy-doom` from `chocolate-doom` failed badly (estimates 19 to 29 years early: the post-fork decline is too slow to fit), and `kocoa-doom`/`mochadoom` had no usable points. Three pairs is a feasibility check, not a validation.
6. **Controls behave.** From-scratch rewrites and unrelated C programs stay below the floor under structure at every age. Names attach `helion` and `managed-doom` (as in E7). Replicate scans of two ports gave **identical results** (difference 0.000), so the engine is deterministic and none of the above is scan noise.

## What this means for the story

* The evidence supports "structure and names both lose linuxdoom's code over time, at different rates in different lineages, and structure is a faithful gauge for close copies". It does **not** support "names stay constant while structure decays" or a copying clock.
* The most defensible time-based result is the fork-date check, and only where a child's clone shares git history with its parent.
* Because the registered measures are survival of **linuxdoom's** functions, a lineage whose code line is not linuxdoom (Boom, ZDoom) shows a flat low curve by construction.

## Caveats found in the data

* 11 early commits scanned to zero functions and are listed, not scored; `freedoom` has 1 usable snapshot.
* Names survival counts duplicates by multiplicity and structure matches one-to-one (E7 defects, unfixed); the de-duplicated sensitivity did not change the conclusions.
* The structure trend against the **placebo reference** (an unrelated C project) was not significant in 10 of 11 lineages; `srb2` showed a trend (rank correlation 0.90), likely real vendored libraries.
* Trend tests on near-zero control curves (helion, libuv) are not meaningful.
