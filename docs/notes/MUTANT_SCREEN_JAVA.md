# Mutant screen: Mocha Doom (Java) engine (2026-11-27)

Same pattern as the C# managed-doom build (`MUTANT_SCREEN_RUNBOOK.md`). Engine only: no lesion outcome was read; the screen has not been run. Files in `demo/harness/mscreen/`:
`schemata_java.py` (Java grammar config, registers `java` into `schemata.LANGS`, `schemata.py` untouched), `build_java.py`, `E13Mut.java` (runtime, package `e13`), `validate_java.py`, `jv_common.py` (demo/lump/Xvfb/run helper), `runner_java.py` (runner.py with `run()` swapped for a Mocha launcher).

## Build (`build_java.py <out>`, screen-venv python)
Mocha source is copied from `demo-study/build/mochadoom/src` (it already carries the per-tic digest hook); the copy gets three of our patches: `e13/Digest.java` calls `E13Mut.check(long[19])` and honours `E13_NODIGEST`; `Engine.main`'s `catch (Exception)` calls `E13Mut.crash()`; `e13/E13Mut.java` is added. `bin/base` = all uninstrumented classes, `bin/inst` = instrumented files; classpath `bin/inst:bin/base`.
Instrumented: every file under `p/Actions/**` (incl. `ActiveStates` monsters/weapons/attacks), `p/Specials.java`, `p/UnifiedGameMap.java`, `p/ActionFunctions.java`, `p/MapUtils.java` (40 files). Constructors, field initialisers and static blocks are not functions; lambdas/anonymous classes belong to the enclosing method.
Java specifics: array index, array dimension, switch labels and annotations never lesioned; long (`5L`), hex, octal, `1_000` literals not lesioned; `++/--` in statement or for-update position is emitted as `x += (On(id) ? -1 : 1)` (a ternary is not a Java statement; same effect as the classical `++`->`--` edit).
Compile loop (javac `-XDrawDiagnostics`, columns with tabs expanded to 8): `prob.found.req` etc. drop the innermost lesion at the error and the literal-constant lesions on the error line (a literal stops being a compile-time constant: `byte b = 5`); `var.might.not.have.been.initialized` drops the deleted plain assignments `name = ...` in that method; unreachable/missing-return drop that method's condition negations (never needed). 39 iterations, about 1 minute.

Result: **258 functions, 5,934 lesions kept, 599 dropped** (527 statement deletions, 51 const_toggle, 7 each constant/const_zero/const_dec). Kept per kind: sdl 1577, negate 836, const_toggle 451, equality 397, constant 381, const_zero 381, const_dec 381, arithmetic 358, relational 304, arith2 211, not 161, logical 156, bitwise 152, incdec 113, shift 75 (shift excluded from the primary analysis). Ids: original < 10000, v2 classes from 10000, as for C/C#.

## Demos Mocha can run: all 77
Mocha cannot load the e14 WADs (DEMO1 lump appended after the directory: `NegativeArraySizeException` in `loadPatchNames` for Freedoom; shareware also unreliable). Recipe: IWAD plus an external lump in the working directory, `java -cp ... mochadoom.Engine -iwad DOOM1.WAD -timedemo <demo> -nodraw -nosound -nomusic` with `<demo>.lmp` = the DEMO1 lump of the e14 WAD (`validate_java.py clean` extracts them to `screen/jv_v2/lmp/`). Freedoom demos use the **original** `freedoom2.wad` (SHA-256 a8772e08...) as `-iwad`, not the e14 copy. Mocha needs an X display even with `-nodraw`: a shared Xvfb (never per-job `xvfb-run`: killing the wrapper on a timeout orphans the JVM).

## Validation (numbers)
1. Zero-lesion replay (E13_MUT unset): **77/77** demos, instrumented per-tic digest byte-identical to the clean Mocha digest and verdict `end <rows>`.
2. Classical rebuild equivalence: **20/20** (15 kinds, one each, plus 5 random; lesions executed on >= 1 demo; seed 1; compared on the executing demos plus 6 non-executing: outcome class, first diverging tic and mismatch mask all equal).
3. Clean digests `screen/jv_v2/clean/<demo>.txt` for 77/77 demos; repeat run byte-identical **77/77**. Mocha is not identical to chocolate-doom on every demo (49/77 on the common columns; the differences are in Freedoom and some chaos demos), which is why lesions are compared with Mocha's own clean digest.
4. Profile: `F fid count first` / `S id count` produced on 77/77 demos; 216 of 258 functions entered by >= 1 demo, 4,554 of 5,934 lesion sites executed by >= 1 demo; no unknown ids. Never entered: brain/boss spawner, sliding doors, locked-door helpers, strobe/light helpers, crusher stop etc.

## Runtime notes
`E13_MUT`, `E13_REF`, `E13_VERDICT`, `E13_PROFILE`, `E13_NODIGEST` as for C#. An uncaught exception (e.g. integer division by zero) writes no verdict, so the runner records `crash`; `I_Error` writes `end <rows>` (an early end, like the C engines). **The crash path was designed but not exercised** (exercising it needs lesion outcomes; the first screen run will show it). Early abort uses `Runtime.halt`.
Timing (box shared, load about 3-4 of 12 cores): clean run 0.63 s, instrumented 0.86 s, profile run 0.97 s, lesion job about 1.3 s wall at 3 workers (JVM startup ~0.4 s; each JVM uses ~1.7 CPU-s because of JIT threads). Recommended: `--workers 3` (nice 10 is applied; runner pauses above load 10).

## Launch
```
cd demo/harness/mscreen; S=/srv/storage_16tb/projects/doom-e7-work/demo-study/screen/jv_v2
/srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python runner_java.py $S $S/jv_phenotypes.sqlite --clean $S/clean --workers 3
```
(resumable; `--rerun-hangs`, `--refresh-profile`, `--functions` as in runner.py.)
