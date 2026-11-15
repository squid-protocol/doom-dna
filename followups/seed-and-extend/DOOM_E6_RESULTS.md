# `DOOM-E6` Results: Partial-Engine Hybrids & Genre Shifts

Preregistered in [preregistration/EXPERIMENTS.md](../../preregistration/EXPERIMENTS.md) (`1122023`) prior to cloning or scanning. Scored with [`score_e6.py`](score_e6.py) against `linuxdoom` (`777` funcs, `--lens portable`, `keyword_mode="composition"`, 3-hop Seed-and-Extend).

## Scorecard

| Target | Repo / Scope | Funcs | Preregistered Prediction | Observed vs. `linuxdoom` | Verdict |
|---|---|---:|---|---|---|
| **`heretic`** | `chocolate-doom/src/heretic` | 729 | **H6.4:** `>= 50%` T1 name precision | **T1 `52/67` (`77.6%`)**, SE `211/439` (`48.1%`), `kw_JSD=0.135`<br>Prefixes: `P:91, R:49, AM:14, G:12, EV:11, A:6` | **Confirmed** |
| **`hexen`** | `chocolate-doom/src/hexen` | 1,147 | **H6.4:** `>= 50%` T1 name precision | **T1 `39/67` (`58.2%`)**, SE `140/484` (`28.9%`), `kw_JSD=0.163`<br>Prefixes: `P:47, R:38, AM:17, G:12, T:5, A:5` | **Confirmed** |
| **`doom64ex`** | `svkaiser/Doom64EX` | 1,750 | **H6.3:** `>= 40%` T1 name precision | **T1 `33/79` (`41.8%`)**, SE `152/545` (`27.9%`), `kw_JSD=0.270`<br>Prefixes: `P:81, A:30, M:7, EV:7, R:6` | **Confirmed** |
| **`srb2`** | `STJr/SRB2` (3D Sonic platformer) | 6,805 | **H6.2:** `>= 25%` T1 name precision | **T1 `23/95` (`24.2%`)**, SE `53/656` (`8.1%`), `kw_JSD=0.205`<br>Prefixes: `AM:21, P:11, R:11, M:2, PIT:2` | **Borderline / Near-Confirmed** (`24.2%` vs `25%` threshold; `53` exact DOOM core hits inside a 6,805-func platformer) |
| **`dhewm3`** | `dhewm/dhewm3` (id Tech 4) | 20,173 | **H6.1:** `<= 2%` name precision | Skipped (`n=20,173 > 15,000` dense `n×n` FGW memory limit) | **Unscored (OOM guard)** |

## Key Takeaways

1. **Smooth evolutionary gradient across id Tech 1 expansions:** Precision steps down cleanly as each game adds more custom mechanics on top of `linuxdoom`: `heretic` (`77.6%` T1) → `hexen` (`58.2%` T1) → `doom64ex` (`41.8%` T1) → `srb2` (`24.2%` T1, `6,805` funcs).
2. **Core `P_*` / `R_*` / `AM_*` subsystems survive genre changes:** Even in `srb2` (a 9× larger 3D Sonic platformer), Seed-and-Extend blindly recovers **53 exact DOOM functions** concentrated in Automap (`AM:21`), Playsim (`P:11`), and Renderer (`R:11`).
3. **Dense FGW scaling limit:** `dhewm3` (`20,173` functions), like `doomsday` (`23,304`) and `gzdoom` (`18,434`), hits the `15,000`-function dense `n×n` FGW limit—highlighting sparse/Nystrom or module-level FGW as a natural engineering next step.
