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

## Phase 0 results so far (pilot; two engines, shareware `DOOM1.WAD`, md5 `f0cefca49926d00903cf57551d901abe`)
* `doomgeneric` (chocolate-derived): plays DEMO1, DEMO2, DEMO3 to completion (5,026 / 3,836 / 2,134 tics); two runs of each are byte-identical, so the digest is deterministic.
* `puredoom` (linuxdoom 1.10 based): plays DEMO1 identically to `doomgeneric` for the first **346 tics**, then diverges (gameplay RNG, then position), and its later level restarts match nothing, which fits a desynced game. It could not open demos 2 and 3 as external files, so only DEMO1 is measured for it.
* **Not yet a finding.** Two engines, one demo, no cause established (a likely candidate is the known behaviour differences between the 1.9 executable and the released 1.10 source, which would make this a version difference, not a port defect). It shows that sync does vary among near-identical code, which is what the gate asked.

## Blockers and next steps
* SDL-based ports (`chocolate-doom`, `crispy-doom`, `woof`, ...) need SDL2 development files, which this machine lacks; the SDL2 inside the `doomretro` clone is a prebuilt Windows package, not source. Getting a Linux SDL2 needs a download (official SDL release source, or a Python wheel); **owner decision**.
* Without SDL: `linuxdoom` (stub video/sound), `doom-ascii`, and the Java translation `mochadoom` (Maven, `~/.m2` is present).
* After the variance is known: register study 1 (or 3) with two independent design reviews, as before.
