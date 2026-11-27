# E16 real cases: symptom vectors for gore (Go) and Kocoa (Kotlin)

Data only: no ranking and no localisation. Files: `gore_symptom.csv`, `kocoa_symptom.csv` (columns `demo, outcome, tic, classes, tics_port, tics_ref`), produced by `demo/harness/mscreen/diagnosis/run_cases.py` (`run <port>`, then `repeat <port>`).

## Method
* 77 demos = the names in `e14/clean/ch/`. Each port ran headless, 2 jobs, `nice -n 10`, paused when the 1-minute load average exceeded 6, one process group per run (killed by group only after completion or timeout). Timeouts: gore 60 s, Kocoa (JVM) 90 s; no Kocoa run needed more than ~1 s.
* Buggy builds only: `build/gore` and `build/kocoa/classes` (not `gore-fixed`).
* gore: `-iwad DEMOIWAD.WAD -timedemo demo1` in a scratch cwd (symlink to the per-demo e14 WAD). gore prints the timedemo line and then never exits, so the runner treats that line as completion and stops the process 3 s later. Digests were complete (row count equal to the reference on every non-killed-by-length demo).
* Kocoa: the per-demo e14 WAD copies make Kocoa's WAD reader throw (demo lump appended after the directory), so it runs the stock shareware `DOOM1.WAD` plus the demo as an external `demo1.lmp` extracted from the e14 WAD (the Mocha-style loader). For the Freedoom demos the base is that demo's `freedoom2.wad`.
* Columns compared (both ports emit the 19-column format incl. the wide world fingerprint): leveltime (1), x y z angle (4-7), health armor weapon (8-10), ammo0-3 (11-14), nmobjs, mobjhash, sectorhash (15-17), keys (18). Excluded: gametic, the gameplay RNG index (2, so the symptom is RNG-free for both ports; Kocoa's is not comparable anyway) and the cosmetic RNG index (3). Angle skipped while the reference player is dead (`--ignore-dead-angle`).
* `tic` = 0-based index of the first diverging row (same convention as compare_digests.py). `classes` = E15 class names (order player, world, sector, keys, time) from the mismatching columns of that row via `roles.CLASS_BITS`. If no row mismatches but the row counts differ: `killed` at tic = the shorter length with class `time` (E15's mask -1 rule). Stray pre-level rows are dropped as in compare_digests.py.
* `crash` / `hang` / `missing` rows have empty tic and classes (to be treated as missing by the scorer). Partial first-divergence info for them is in `<data root>/e16cases/<port>_detail.csv` (not committed).

## Results (77 demos)
| port | killed | same | crash | hang | missing |
|---|---|---|---|---|---|
| gore | 69 | 5 | 1 | 2 | 0 |
| Kocoa | 46 | 12 | 0 | 0 | 19 |

* gore `same`: b0000, b0006, b0007, b0008, b0009 (bot demos, no monsters). Crash: v0084 (Go nil-pointer panic, rc 2). Hangs: f0074 and g0018 (Freedoom; digest stopped at 76 and 528 rows, process did not finish in 60 s).
* Kocoa `same`: all 12 bot demos b0000-b0011 (consistent with the documented 47/47 on no-monster bot demos). Missing: all 19 Freedoom demos (f*, g*): Kocoa throws in texture init on freedoom2.wad (`InitTextures` exception), so no digest exists.
* Surprising: on the three x demos (x0014, x0043, x0056) Kocoa diverges at tic 0 in many columns including keys and nmobjs (e.g. 309 vs 362 objects, keys 0 vs 63): its external-demo path appears to start a different state than the reference for those demos, so these are start-state failures, not play-time symptoms. gore diverges on them at tics 9, 8 and 47. Treat the Kocoa x demos as suspect when scoring.
* Kocoa's lesion-free symptom is dominated by the world class (monster state), as in the earlier phase-1 notes.

## Determinism
Five random killed/same demos per port (seed 16) run twice; digests byte-identical: gore s0005 s0019 v0000 g0063 s0012; Kocoa p0010 s0006 c0006 s0002 c0002. 10 of 10 identical.

## Reproduce
`python3 -I run_cases.py run gore|kocoa`, then `repeat gore|kocoa`. Digests go to `/srv/storage_16tb/projects/doom-e7-work/demo-study/e16cases/` (not committed).
