# DOOM-E8b results: does measuring each port against its closest progenitor explain what E8 saw?

Registered 2026-11-22 18:51 EST (commit `7d44a1a`); measurement outputs frozen and hashed at 18:55 EST (`b22d0f6`) before the analysis was run. Engine `704cb35f0`, sfs `bcd3cb7`. Full tables: [phase_report.md](analysis/phase_report.md). **A post hoc follow-up on the same ports and scans as E8, not independent confirmation.** `odamex`, `gzdoom` and `srb2` have no obtainable progenitor and stay unexplained.

## The answer in plain terms

**Yes, mostly: for five of six ports the right progenitor explains far more of the early code than linuxdoom does. The registered headline is met, but it is thin and fragile, and one port and the controls did not behave.**

| Port | Progenitor | Survival of progenitor at earliest snapshot | Survival of linuxdoom | Advantage (95% interval) |
|---|---|---:|---:|---|
| `woof` | MBF 2.03 | 0.78 | 0.18 | **+0.59** (0.56 to 0.63) |
| `prboom-plus` | Boom 2.02 | 0.68 | 0.21 | **+0.47** (0.42 to 0.52) |
| `edge-classic` | EDGE (2021-09) | 0.36 | 0.00 | **+0.36** (0.35 to 0.37) |
| `inter-doom` | Crispy Doom (2023-06) | 0.63 | 0.29 | **+0.35** (0.31 to 0.39) |
| `eternity` | SMMU | 0.31 | 0.03 | **+0.28** (0.26 to 0.31) |
| `doomretro` | Chocolate Doom (2013-12) | 0.11 | 0.16 | **-0.04** (-0.07 to -0.02) |

* **Registered rule:** at least 5 of 6 ports pass (advantage at least +0.05 with the paired interval above 0) and a one-sided Wilcoxon p below 0.05. **Met: 5 of 6, p = 0.031.**
* **It is fragile, and the reasons matter:**
  * Drop any one of the five passing ports and the rule fails (4 of 5 is not enough). It rests on exactly five passes.
  * `edge-classic` is C++ and linuxdoom is C, so structure cannot see linuxdoom in it at all (survival 0.000). Its pass is **partly language blindness, not ancestry**. Under the registered pure-C sensitivity it drops out and the rule is **not met** (4 of 5, p = 0.062).
  * `inter-doom` passes at its first snapshot but not at its second (-0.12).
* **The carry-over gate is met (6 of 6):** the progenitor's own novel code (code not in linuxdoom) survives above the 2% floor in every port, so the advantage is not just inherited linuxdoom code.
* **The progenitor map holds up where it can be tested:** the registered progenitor ranks first among candidates for `woof`, `edge-classic`, `inter-doom` and `doomretro`, and second for `eternity` (its 2006 code is closer to MBF 2.03, 0.34, than to SMMU, 0.25). For `prboom-plus` only three candidates existed in 2000, so "top 3" is true by construction there.

## What did not work

* **`doomretro` is the exception.** Chocolate Doom explains less of it than linuxdoom does, and Boom 2.02 explains slightly more (0.14 against 0.11). Its progenitor link was the weakest ("inferred"), and Doom Retro looks heavily rewritten from its first commit.
* **The controls were not met (H8b.4).** Differential specificity failed for `doomretro` (above). The wrong progenitor's own novel code should have stayed below 2% but reached 3.0% (`prboom-plus`), 4.0% (`eternity`) and 2.7% (`doomretro`). The 2% floor is too tight against the chance-level structural matching of small novel subsets of about 3 to 4%. The six new progenitors stay below 0.6% against every unrelated control.
* **Not all the decay predictions held.** With the progenitor as reference, structure survival falls with age in most ports, but several conclusions flip once repository growth is controlled (the same fragility as E8).

## The cleanest result: forks measured from the fork point

For the four git-shared forks (descriptive only), measured from the parent's code **at the fork commit**, structure survival falls much faster than name survival in all three same-language pairs:

| Child | Years | Structure | Names |
|---|---:|---|---|
| `crispy-doom` from `chocolate-doom` | 12.7 | 0.81 to 0.52 | 0.93 to 0.87 |
| `dsda-doom` from `prboom-plus` | 5.9 | 0.84 to 0.35 | 0.93 to 0.65 |
| `nugget-doom` from `woof` | 4.6 | 0.77 to 0.30 | 0.91 to 0.65 |

This is the original hypothesis (names change less than structure over time) holding when the comparator is the right one. `kocoa-doom` (Java to Kotlin) shows structure collapsing to 0.00 at the head while names stay at 0.56.

## What this means for the story

* **E8's flat-and-low curves were largely a comparator problem for the lineages we could test**: the Boom/MBF/SMMU/EDGE and Crispy lines start high against their progenitor and low against linuxdoom.
* **It does not explain `gzdoom`, `odamex` or `srb2`** (no progenitor found), and `doomretro` stays unexplained.
* **Caveats to state:** a post hoc follow-up; a headline that hinges on exactly five of six passes and one language-confounded port; progenitor survival is measured with Boom and MBF being only about 850 to 935 functions, so shares are larger for small progenitors (the common-denominator version agrees except for `doomretro`, 0.03).
