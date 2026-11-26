# DOOM demo studies: plan and Phase 0 pilot (2026-11-25; not registered)

**Idea.** DOOM records inputs as demos (`.lmp`) that replay tic by tic. A faithful port stays in sync; a divergent one desyncs. That is a behavioural ground truth to set against our structural measures (fingerprints, call graph, the finder tiers).

## Studies
1. **Structure to sync:** does the retained structure of the playsim subsystems predict sync with a vanilla-compatible engine, and where does the first desync fall?
2. **Performance:** `-timedemo` speed and per-function profile joined to the matched pairs (performance inheritance).
3. **Behavioural truth for matching:** per-function call counts under the same demo, as a name-free, text-free truth for translations (replaces E12's weakest truth).
4. **Swap tests:** replace a matched function by its counterpart and replay: does sync survive? (the real accuracy of each tier).

## Phase 0 gate (why a pilot comes first)
If every close port syncs perfectly there is nothing for study 1 to explain, and the registered effort should go to studies 2 and 3. So Phase 0 measures how much sync varies across ports before anything is registered.

## Harness (this branch, `demo/harness/`)
* `e13_headless.c`: headless platform layer for doomgeneric-family engines; writes one digest line per game tic: `gametic leveltime prndindex rndindex x y z angle health armor weapon ammo0..3`. A fake clock keeps timing deterministic; the demo runs under `-timedemo -nodraw -nosound -nomusic -nogui`.
* `build_doomgeneric_family.py`: copies a pinned clone to a work directory (the clone is never modified), inserts one call after the per-tic game-time increment, compiles. `e13_pure_main.c` + `build_puredoom.py` do the same for PureDOOM.
* Third-party source is never committed: only our driver and the patcher (which inserts one line at a short anchor). Builds and digests live outside the repo (`doom-e7-work/demo-study/`).
* Compare on `leveltime, prndindex, x, y, z, angle, health, armor, weapon, ammo`. **Do not compare `rndindex`**: it is the cosmetic RNG (status-bar face, sound) and differs between engines for harmless reasons.

## Phase 0 results (2026-11-25; pilot, not registered)
**Engines built headless with the digest (owner approved installing missing dependencies):** `chocolate-doom` (reference), `doomgeneric`, `crispy-doom`, `prboom-plus`, `sdl-doom`, `inter-doom` (all C, SDL2 dummy video/audio or the doomgeneric headless layer) and `puredoom`. Shareware `DOOM1.WAD` (md5 `f0cefca49926d00903cf57551d901abe`).
* **The harness checks out:** two independent builds of the chocolate family and `doomgeneric` give byte-identical digests; repeat runs are identical.
* **Shareware demos 1 to 3 (5,026 / 3,836 / 2,134 tics):** six engines are identical to the reference on every compared field at every tic. `puredoom` (linuxdoom 1.10 based) matches for 346 tics on demo 1 and then diverges (weapon field first); it cannot load external demo files, so demos 2 and 3 were not played. Plausible cause (not established): the released 1.10 source differs in behaviour from the shipped 1.9 executable.
* **Random self-play demos:** `demo/harness/gen_demos.py` writes vanilla-format demos from a seeded random policy (run, strafe, turn, fire, use, weapon switch; our own inputs, no third-party content). 300 demos, 4,000 tics each, all maps E1M1 to E1M9, skills 1 to 4: **1,800 of 1,800 runs identical across the six engines** (`demo/phase0_random_demo_matrix.csv`). The player moved and fired in every demo and died in 187, so the demos exercise combat and death, not just walking.
* **Boom-family caveat:** `prboom-plus` and `inter-doom` do not keep the gameplay RNG index in every mode (or keep it private), so they are compared on the game state without that column.

## First translation: Mocha Doom (Java), same demos, same reference
Built with `javac` from a patched copy (`demo/harness/build_mochadoom.py`, our `E13Digest.java`); runs under a virtual display.
* **Shareware demos 1 to 3:** identical to the reference on every field at every tic except the **view angle for 3, 9 and 25 tics while the player is dead** (the death-camera turns toward the attacker by a different step; it lands on the same angle). Position, health, armor, weapon, ammo and the gameplay RNG index match throughout.
* **300 random self-play demos** (`demo/phase0_mochadoom_vs_chocolate.csv`): strictly identical on every field in 130; identical on gameplay (angle ignored while dead) in **291**; **9 real gameplay desyncs** (3%). In each, the gameplay RNG index drifts by one call (once two, once 23) at some tic and the player's position diverges 2 to 122 tics later (one demo shows only the RNG drift). They are not spread evenly: 5 of 29 demos on E1M5 (17%) against 4 of 271 on the other maps (1.5%); small numbers.
* So a Java translation of a C program is behaviourally identical on the player's trajectory in 97% of random play, and identical on the shareware demos apart from a cosmetic camera. Not yet known: which Java function consumes a different number of random numbers (a call-by-call RNG trace on one of the nine demos would show it).
* Deliberately a post hoc rule: "ignore the angle while the reference player is dead" was set after seeing the first demo; the strict numbers are reported alongside.

## What this means for the studies
* **Study 1 as first framed has little to explain among established C ports:** sync does not vary among them on shareware or random demos. The outcome variance sits elsewhere (non-vanilla-exact engines like `puredoom`, translations, ports in non-compatible modes), so study 1 should be re-scoped there, with translations as the main case.
* **Performance (study 2) and the call-count oracle (study 3) do not depend on sync variance.** Speed certainly varies; per-function call counts are language-independent, and demos are now a cheap, reproducible driver for both.
* **Not yet built:** `dsda-doom` (needs OpenGL), `woof` and `nugget-doom` (need SDL3 3.4+ and OpenAL), and the other translations (`gore` Go, `managed-doom` C#, `doom-scheme`, `dartdoom`, `kocoa-doom`).
## Blockers and next steps
* Done: SDL2 2.30.9, SDL2_net 2.2.0 and SDL2_mixer 2.8.0 built from official release sources into a private prefix (`doom-e7-work/demo-study/prefix`), cmake and ninja in a private venv.
* Next: find where Mocha Doom's RNG use differs (call-by-call trace), then the other translations; then register the re-scoped study 1 or study 3 with two independent design reviews, as before.
