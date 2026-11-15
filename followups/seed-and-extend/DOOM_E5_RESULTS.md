# `DOOM-E5` Results: Held-Out Cross-Language Predictions

Preregistered in [preregistration/EXPERIMENTS.md](../../preregistration/EXPERIMENTS.md) (`cbf526c`) **prior to cloning or scanning** any of the 5 held-out repositories.

## Scorecard

| Target | License / Lang | Functions | Preregistered Prediction | Observed (`linuxdoom` / Best Anchor) | Verdict |
|---|---|---:|---|---|---|
| **`cydoomgeneric`** | GPL-2.0 (`c`, `python`) | 1,109 | **H5.2:** `>= 70%` vs `linuxdoom`, `>= 80%` vs `doomgeneric`, parent = `doomgeneric` | `linuxdoom`: **T1 `91/92` (`98.9%`)**, SE `287/620` (`46.3%`), `FGW_cost=0.541`<br>`doomgeneric`: **T1 `156/156` (`100.0%`)**, SE `432/858` (`50.3%`), **`FGW_cost=0.313`**<br>`chocolate-doom`: T1 `139/140` (`99.3%`), SE `577/926` (`62.3%`), `FGW_cost=0.578` | **Confirmed** (`FGW_cost=0.313` pinpoints `doomgeneric` as parent) |
| **`DOOM-style-Game`** | MIT (`python`) | 66 | **H5.4:** `<= 2%` vs `linuxdoom` (from-scratch raycaster) | `linuxdoom`: T1 `0/9` (**`0.0%`**), SE `0/39` (**`0.0%`**), `FGW_cost=0.705` | **Confirmed** |
| **`doome`** | MIT (`rust`) | 651 | **H5.5:** `<= 2%` vs `linuxdoom` (MIT non-GPL Rust engine) | `linuxdoom`: T1 `0/28` (**`0.0%`**), SE `0/322` (**`0.0%`**), `FGW_cost=0.756` | **Confirmed** |
| **`iron-doom`** | GPL-3.0 (`rust`) | 319 | **H5.1:** `>= 25%` vs `linuxdoom` (Rust source port) | `linuxdoom`: T1 `0/24` (**`0.0%`**), SE `0/147` (**`0.0%`**), `FGW_cost=0.734` | **Falsified** *(see below)* |
| **`doomarkable`** | GPL-2.0 (`rust`) | 41 | **H5.3:** `>= 50%` vs `linuxdoom` (assumed C/C++ port) | `linuxdoom`: T1 `0/6` (**`0.0%`**), SE `0/37` (**`0.0%`**), `FGW_cost=0.747` | **Falsified** *(see below)* |

## What the Two Falsifications Taught Us

1. **`iron-doom` (`H5.1`):** Although `iron-doom` states it is *"built on the Chocolate Doom codebase"*, its architecture section reveals it **rewrote the engine into Bevy ECS** (`crates_plugins.rs` + Bevy systems).
   * **Insight:** Paradigm-preserving translations (`C → Go` in `gore`, `75.9%`) preserve DOOM's call-graph DNA; **paradigm-shifting ECS rewrites (`C → Bevy ECS`)** replace the imperative call graph with decoupled ECS systems and drop to `0.0%`, indistinguishable from a from-scratch engine.
2. **`doomarkable` (`H5.3`):** The repo is only a **41-function Rust platform wrapper** (`blue_noise_dither.rs`, `evdev_keyboard.rs`, `main.rs`) calling `doomgeneric-rs` as an external crate—the C DOOM engine is not vendored in the repository (unlike `cydoomgeneric`, which vendors `doomgeneric`'s C sources and hits `100.0%` Tier-1 / `FGW_cost=0.313`).
