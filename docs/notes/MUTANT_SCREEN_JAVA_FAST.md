# Faster JVM launch for the Mocha (Java) mutant screen (2026-11-27)

`demo/harness/mscreen/runner_java_fast.py` is `runner_java.py` with only the java command line changed (same store schema, resumable, same 6x-clean-time hang rule, same outcome reading). Nothing was applied to the running screen.

## Flags
Old: `-XX:+UseSerialGC -Xmx768m -Xss4m -cp bin/inst:bin/base`.
New: the same three flags plus `-XX:SharedArchiveFile=screen/jv_v2/fast/mocha_inst.jsa -Xshare:auto -XX:TieredStopAtLevel=1 -XX:CICompilerCount=1 -XX:-UsePerfData`, classpath `screen/jv_v2/fast/inst.jar:screen/jv_v2/fast/base.jar`.
- The jars are `jar --create --no-manifest -C bin/inst .` / `-C bin/base .` (AppCDS refuses directories on the classpath); the archive is a dynamic AppCDS archive made with `-XX:ArchiveClassesAtExit` from one ordinary lesion run. Rebuild all three if bin/inst or bin/base is ever rebuilt. A missing or mismatched archive falls back silently to normal loading.
- JDK 21.0.13 (so `-XX:+AutoCreateSharedArchive` was also possible; not used, a fixed archive is simpler to reason about).
- Most of the saving is `TieredStopAtLevel=1` (no C2 compiler threads for a ~0.5 s run); the archive adds a few percent more CPU and about 0.1 s of wall.

## Measurements (9 stored jobs: 3 killed, 3 same, 3 crash; nice 10, box load ~12, 2 repeats each)
| | CPU s/job (user+sys of the java process) | wall s/job |
|---|---|---|
| current | 1.27 to 1.54 | 0.57 to 1.24 |
| new | 0.57 | 0.49 |
Single-flag runs (CPU/job, same set): TieredStopAtLevel=1 alone 0.72, archive alone 1.11, -UsePerfData alone about the baseline, archive+C1+no perf data 0.60, plus CICompilerCount=1 0.57. About 2.5x less CPU per job. `-Xverify:none` and `-XX:-BytecodeVerificationRemote` gave no gain (the latter is a diagnostic flag and refuses to start without UnlockDiagnosticVMOptions; not used).

## Equivalence check
300 jobs from the store, seed 13, stratified 100 killed / 100 same / 100 crash: re-run with the new settings; outcome, first diverging tic and mismatch mask compared to the stored values (crash = no verdict, same as the runner): **300/300 identical, 0 mismatches**. Plus a full runner-path check on a scratch copy of the store (never the live one): all 77 demos of one lesion re-run through `runner_java_fast.py` with 2 workers, 77/77 identical in outcome, tic and mask.
No `hang` rows exist in the store, so no hang case could be re-run. Hang rule: timeout = min(150, max(15, 6 x clean time)); clean times are about 0.46 s, so the floor of 15 s applies. A normal job takes about 0.5 s with the new flags (C1-only is slower only in long steady-state runs, which these are not), so the rule keeps a wide margin; faster launch does not make a normal job look like a hang, and an infinite loop still times out at the same wall time.

## Caveat seen during testing
Several of my own test runs failed for a moment with `Can't connect to X11 window server using ':3'` (every job returning rc 1, recorded as `crash`): another process on this shared box appears to collide with the freshly started Xvfb display number. The same commands succeeded minutes later. After a restart, check that the first stored rows are not all `crash` (see below).

## Restart procedure (do not run while unsure; the runner is resumable, results commit every 200 jobs, the uncommitted tail is simply re-run)
```
OLD=$(cat /home/joe/.claude/jobs/2d0f7fb1/tmp/jv_screen.pid)
ps -eo pid,args | grep '[X]vfb'        # note the Xvfb PID that belongs to the runner (child of $OLD: pgrep -P $OLD)
kill $OLD; wait for it to exit (python flushes the store at exit); kill <Xvfb PID>
cd /srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot/demo/harness/mscreen
S=/srv/storage_16tb/projects/doom-e7-work/demo-study/screen/jv_v2
nohup /srv/storage_16tb/projects/doom-e7-work/screen-venv/bin/python runner_java_fast.py $S $S/jv_phenotypes.sqlite --clean $S/clean --workers 11 --maxload 14 > <log> 2>&1 &
echo $! > /home/joe/.claude/jobs/2d0f7fb1/tmp/jv_screen.pid
```
Afterwards (after a few hundred jobs) verify `select outcome,count(*) from results order by rowid desc limit 200 group by 1` is not dominated by `crash` (the old mix is roughly 49% killed / 36% same / 15% crash); if it is, stop and restart (fresh Xvfb display). With CPU per job down about 2.5x, workers 11 / maxload 14 can stay; the load governor will let the runner go faster per slot, so consider raising workers only if the box has headroom.
