"""Phenotype runner for the gore (Go) schemata build: same store, same outcomes and same rules as runner.py (which hardcodes the three other launch recipes), gore's launch recipe.
Usage: python runner_go.py <screen_dir> <store.sqlite> [--workers 3] [--functions A,B,...] [--limit N] [--wads DIR] [--clean DIR] [--rerun-hangs] [--refresh-profile] [--maxload 10] [--timeout 150]
Every lesion is compared with gore's OWN clean digest (--clean, default screen/go_v2/clean/<demo>.txt), not chocolate-doom's. Demos on which the unmodified engine crashes or hangs (clean/status.json) are skipped.
A lesion is run only on demos whose clean site profile executed its site. Outcomes: killed (first diverging tic, mask of mismatching columns), same, crash (an uncaught Go panic: index out of range,
nil dereference, integer division by zero ...), hang (no end within 6x the clean time, floor 15 s; re-run once with --rerun-hangs and the full timeout)."""
import argparse, collections, json, os, shutil, sqlite3, sys, tempfile, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H))
import validate_go as V
ap = argparse.ArgumentParser(); ap.add_argument("screen"); ap.add_argument("store"); ap.add_argument("--workers", type=int, default=3); ap.add_argument("--functions"); ap.add_argument("--limit", type=int)
ap.add_argument("--wads", default=str(V.E14 / "wads")); ap.add_argument("--clean", default=str(V.S / "clean")); ap.add_argument("--rerun-hangs", action="store_true"); ap.add_argument("--refresh-profile", action="store_true")
ap.add_argument("--maxload", type=float, default=10.0); ap.add_argument("--timeout", type=int, default=150)
a = ap.parse_args(); screen = Path(a.screen); binary = screen / "bin/engine"; man = json.load(open(screen / "manifest.json")); wads = Path(a.wads); clean = Path(a.clean)
status = json.load(open(clean / "status.json")); names = sorted(d for d in V.demos(wads) if status.get(d, {}).get("status") == "ok")
db = sqlite3.connect(a.store, check_same_thread=False); lock = threading.Lock()
db.executescript("""create table if not exists results(lesion integer, demo text, outcome text, tic integer, mask integer, rc integer, tries integer, primary key(lesion, demo));
create table if not exists clean_time(demo text primary key, secs real);
create table if not exists sitereach(demo text, lesion integer, count integer, primary key(demo, lesion));
create table if not exists reach(demo text, fid integer, entries integer, first_tic integer, primary key(demo, fid));
create table if not exists lesions(id integer primary key, file text, fn text, fid integer, line integer, kind text, op text, new text);
create table if not exists functions(fid integer primary key, file text, name text, line integer, size integer);""")
db.executemany("insert or ignore into lesions values(?,?,?,?,?,?,?,?)", [(s["id"], s["file"], s["fn"], s["fid"], s["line"], s["kind"], s["op"], s["new"]) for s in man["sites"]])
db.executemany("insert or ignore into functions values(?,?,?,?,?)", [(f["fid"], f["file"], f["name"], f["line"], f["size"]) for f in man["functions"]]); db.commit()
def gate():
    while float(open("/proc/loadavg").read().split()[0]) > a.maxload: time.sleep(20)
have = set() if a.refresh_profile else {r[0] for r in db.execute("select distinct demo from reach")}
for d in names:
    if d in have: continue
    gate(); pf = V.TMP / f"prof_{d}.txt"; V.TMP.mkdir(parents=True, exist_ok=True); pf.unlink(missing_ok=True)
    V.run_gore(binary, d, dict(E13_PROFILE=str(pf), E13_NODIGEST="1"), wads=wads, after_line=0.5); lines = [l.split() for l in open(pf)]; pf.unlink()
    db.executemany("insert or ignore into reach values(?,?,?,?)", [(d, int(x[1]), int(x[2]), int(x[3])) for x in lines if x[0] == "F"])
    db.executemany("insert or ignore into sitereach values(?,?,?)", [(d, int(x[1]), int(x[2])) for x in lines if x[0] == "S"]); db.commit()
have_t = {r[0] for r in db.execute("select demo from clean_time")}
for d in names:
    if d in have_t: continue
    gate(); secs = V.run_gore(binary, d, dict(E13_NODIGEST="1"), wads=wads, after_line=0.5)[3]; db.execute("insert or replace into clean_time values(?,?)", (d, secs)); db.commit()
ctime = dict(db.execute("select demo, secs from clean_time"))
def tmo(d): return int(min(a.timeout, max(15, 6 * ctime.get(d, 10))))
executed = {}
for d, les in db.execute("select demo, lesion from sitereach"): executed.setdefault(d, set()).add(les)
lesions = [s for s in man["sites"] if (not a.functions or s["fn"] in a.functions.split(","))]
if a.limit: lesions = lesions[:a.limit]
done = {(l, d) for l, d in db.execute("select lesion, demo from results")}; hangs = set()
if a.rerun_hangs:   # only isolated hangs: a lesion that hangs on >= half of the demos that execute it is a deterministic infinite loop
    allh = collections.Counter(l for l, in db.execute("select lesion from results where outcome='hang'")); ex_n = collections.Counter()
    for l, d in db.execute("select lesion, demo from sitereach"): ex_n[l] += 1
    hangs = {(l, d) for l, d in db.execute("select lesion, demo from results where outcome='hang' and tries=1") if allh[l] <= 1 or allh[l] / max(1, ex_n[l]) < 0.5}
jobs = [(s["id"], d) for s in lesions for d in names if s["id"] in executed.get(d, ()) and ((s["id"], d) in hangs if a.rerun_hangs else (s["id"], d) not in done)]
print(f"{len(lesions)} lesions, {len(names)} demos ({len(status) - len(names)} excluded: unmodified gore crashes or hangs), {len(jobs)} jobs to run ({len(done)} already stored)", flush=True)
def job(j):
    les, d = j; gate(); tries = 2 if a.rerun_hangs else 1
    out = V.classify(binary, d, {"E13_MUT": str(les)}, a.timeout if a.rerun_hangs else tmo(d), wads=wads, clean=clean)
    o, tic, mask = (out + (None, None))[0], (out[1] if len(out) > 1 else None), (out[2] if len(out) > 2 else None)
    with lock: db.execute("insert or replace into results values(?,?,?,?,?,?,?)", (les, d, o, tic, mask, 0, tries))
    return o
t0 = time.time(); n = 0
with ThreadPoolExecutor(a.workers) as ex:
    for fut in as_completed([ex.submit(job, j) for j in jobs]):
        n += 1
        if n % 200 == 0:
            with lock: db.commit()
            print(f"{n}/{len(jobs)} jobs, {time.time() - t0:.0f}s", flush=True)
db.commit(); print("done", n, "jobs in", round(time.time() - t0), "s")
