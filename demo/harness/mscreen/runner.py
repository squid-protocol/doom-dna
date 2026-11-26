"""Phenotype runner: run lesions of a schemata build over the demo suite and store outcomes in SQLite (resumable, load-governed).
Usage: python runner.py <screen_dir> <store.sqlite> [--workers 8] [--functions A,B,...] [--limit N] [--wads DIR] [--clean DIR]
Needs the early-abort digest (patch_abort.py). A lesion is run only on demos whose clean profile enters its function (a lesion cannot affect a demo that never executes it)."""
import argparse, json, os, shutil, sqlite3, subprocess, sys, tempfile, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"
ap = argparse.ArgumentParser(); ap.add_argument("screen"); ap.add_argument("store"); ap.add_argument("--workers", type=int, default=8); ap.add_argument("--functions"); ap.add_argument("--limit", type=int)
ap.add_argument("--wads", default=str(E14 / "wads")); ap.add_argument("--clean", default=str(E14 / "clean/ch")); ap.add_argument("--engine", default="c"); ap.add_argument("--maxload", type=float, default=10.0); ap.add_argument("--timeout", type=int, default=90)
a = ap.parse_args(); screen = Path(a.screen); binary = screen / ("bin/e13-managed-doom.dll" if a.engine == "md" else "chocolate-doom"); man = json.load(open(screen / "manifest.json")); wads = Path(a.wads); clean = Path(a.clean)
names = sorted(p.stem for p in wads.glob("*.WAD")); db = sqlite3.connect(a.store, check_same_thread=False); lock = threading.Lock()
db.executescript("""create table if not exists results(lesion integer, demo text, outcome text, tic integer, col integer, rc integer, primary key(lesion, demo));
create table if not exists reach(demo text, fid integer, entries integer, first_tic integer, primary key(demo, fid));
create table if not exists lesions(id integer primary key, file text, fn text, line integer, kind text, op text, new text);
create table if not exists functions(fid integer primary key, file text, name text, line integer, size integer);""")
db.executemany("insert or ignore into lesions values(?,?,?,?,?,?,?)", [(s["id"], s["file"], s["fn"], s["line"], s["kind"], s["op"], s["new"]) for s in man["sites"]])
db.executemany("insert or ignore into functions values(?,?,?,?,?)", [(f["fid"], f["file"], f["name"], f["line"], f["size"]) for f in man["functions"]]); db.commit()
def env_for(home, extra):
    return dict(os.environ, HOME=home, XDG_DATA_HOME=home, XDG_CONFIG_HOME=home, LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", **extra)
def run(demo, extra):
    home = tempfile.mkdtemp(prefix="mscr_", dir=str(E14)); t0 = time.time()
    cmd = ["nice", "-n", "10"] + ([str(W / "tools/dotnet/dotnet"), str(binary), "-iwad", str(wads / f"{demo}.WAD"), "-timedemo", "demo1", "-nosound", "-nomusic"] if a.engine == "md" else [str(binary), "-iwad", str(wads / f"{demo}.WAD"), "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic", "-nogui"])
    extra = dict(extra, DOTNET_ROOT=str(W / "tools/dotnet"), DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1") if a.engine == "md" else extra
    try: rc = subprocess.run(cmd, cwd=home, env=env_for(home, extra), timeout=a.timeout, capture_output=True).returncode
    except subprocess.TimeoutExpired: rc = -9
    return home, rc
def refrows(demo): return sum(1 for l in open(clean / f"{demo}.txt") if len(l.split()) == 19)
# clean profiles (which functions each demo enters)
have = {r[0] for r in db.execute("select distinct demo from reach")}
for d in names:
    if d in have: continue
    home, rc = run(d, dict(E13_PROFILE=str(Path(tempfile.gettempdir()) / f"prof_{d}.txt"), E13_NODIGEST="1")); p = Path(tempfile.gettempdir()) / f"prof_{d}.txt"
    rows = [tuple(map(int, l.split())) for l in open(p)]; p.unlink(); shutil.rmtree(home, ignore_errors=True)
    db.executemany("insert or ignore into reach values(?,?,?,?)", [(d, fid, n, ft) for fid, n, ft in rows]); db.commit()
fid_of = {}
for f in man["functions"]: fid_of[(f["file"], f["name"])] = f["fid"]
entered = {}
for d, fid in db.execute("select demo, fid from reach"): entered.setdefault(d, set()).add(fid)
lesions = [s for s in man["sites"] if (not a.functions or s["fn"] in a.functions.split(","))]
if a.limit: lesions = lesions[:a.limit]
done = {(l, d) for l, d in db.execute("select lesion, demo from results")}
jobs = [(s["id"], d) for s in lesions for d in names if fid_of.get((s["file"], s["fn"])) in entered.get(d, ()) and (s["id"], d) not in done]
print(f"{len(lesions)} lesions, {len(names)} demos, {len(jobs)} jobs to run ({len(done)} already stored)", flush=True)
def job(j):
    les, d = j
    while float(open("/proc/loadavg").read().split()[0]) > a.maxload: time.sleep(20)
    vf = Path(tempfile.gettempdir()) / f"verd_{les}_{d}_{os.getpid()}.txt"; vf.unlink(missing_ok=True)
    home, rc = run(d, dict(E13_MUT=str(les), E13_REF=str(clean / f"{d}.txt"), E13_VERDICT=str(vf), E13_NODIGEST="1")); shutil.rmtree(home, ignore_errors=True)
    out, tic, col = "crash", None, None
    if rc == -9: out = "hang"
    elif vf.exists():
        w = vf.read_text().split(); vf.unlink()
        if w[0] == "div": out, tic, col = "killed", int(w[1]), int(w[2])
        elif w[0] == "end": out = "same" if int(w[1]) == refrows(d) else "killed"; tic = None if out == "same" else min(int(w[1]), refrows(d)); col = None if out == "same" else -1
    elif rc == 0: out = "crash"
    with lock: db.execute("insert or replace into results values(?,?,?,?,?,?)", (les, d, out, tic, col, rc))
    return out
t0 = time.time(); n = 0
with ThreadPoolExecutor(a.workers) as ex:
    for out in ex.map(job, jobs):
        n += 1
        if n % 500 == 0:
            with lock: db.commit()
            print(f"{n}/{len(jobs)} jobs, {time.time() - t0:.0f}s", flush=True)
db.commit(); print("done", n, "jobs in", round(time.time() - t0), "s")
