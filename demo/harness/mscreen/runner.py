"""Phenotype runner: run lesions of a schemata build over the demo suite and store outcomes in SQLite (resumable, load-governed).
Usage: python runner.py <screen_dir> <store.sqlite> [--workers 8] [--functions A,B,...] [--limit N] [--wads DIR] [--clean DIR]
Needs the early-abort digest (patch_abort.py). A lesion is run only on demos whose clean profile enters its function (a lesion cannot affect a demo that never executes it)."""
import argparse, json, os, shutil, sqlite3, subprocess, sys, tempfile, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"
ap = argparse.ArgumentParser(); ap.add_argument("screen"); ap.add_argument("store"); ap.add_argument("--workers", type=int, default=8); ap.add_argument("--functions"); ap.add_argument("--limit", type=int)
ap.add_argument("--wads", default=str(E14 / "wads")); ap.add_argument("--clean", default=str(E14 / "clean/ch")); ap.add_argument("--engine", default="c"); ap.add_argument("--rerun-hangs", action="store_true"); ap.add_argument("--refresh-profile", action="store_true"); ap.add_argument("--maxload", type=float, default=10.0); ap.add_argument("--timeout", type=int, default=150)
a = ap.parse_args(); screen = Path(a.screen); binary = screen / ("bin/e13-managed-doom.dll" if a.engine == "md" else "chocolate-doom"); man = json.load(open(screen / "manifest.json")); wads = Path(a.wads); clean = Path(a.clean)
names = sorted({p.stem for p in wads.glob("*.WAD")} | {p.parent.name for p in wads.glob("*/freedoom2.wad")});   # a demo is either wads/<name>.WAD (shareware base) or wads/<name>/freedoom2.wad (Freedoom base; Managed Doom reads the game from the file name)
def wadpath(d): return (wads / f"{d}.WAD") if (wads / f"{d}.WAD").exists() else (wads / d / "freedoom2.wad")
db = sqlite3.connect(a.store, check_same_thread=False); lock = threading.Lock()
db.executescript("""create table if not exists results(lesion integer, demo text, outcome text, tic integer, mask integer, rc integer, tries integer, primary key(lesion, demo));
create table if not exists clean_time(demo text primary key, secs real);
create table if not exists sitereach(demo text, lesion integer, count integer, primary key(demo, lesion));
create table if not exists reach(demo text, fid integer, entries integer, first_tic integer, primary key(demo, fid));
create table if not exists lesions(id integer primary key, file text, fn text, fid integer, line integer, kind text, op text, new text);
create table if not exists functions(fid integer primary key, file text, name text, line integer, size integer);""")
db.executemany("insert or ignore into lesions values(?,?,?,?,?,?,?,?)", [(s["id"], s["file"], s["fn"], s["fid"], s["line"], s["kind"], s["op"], s["new"]) for s in man["sites"]])
db.executemany("insert or ignore into functions values(?,?,?,?,?)", [(f["fid"], f["file"], f["name"], f["line"], f["size"]) for f in man["functions"]]); db.commit()
def env_for(home, extra):
    return dict(os.environ, HOME=home, XDG_DATA_HOME=home, XDG_CONFIG_HOME=home, LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", **extra)
def run(demo, extra, timeout=None):
    home = tempfile.mkdtemp(prefix="mscr_", dir=str(E14)); t0 = time.time()
    cmd = ["nice", "-n", "10"] + ([str(W / "tools/dotnet/dotnet"), str(binary), "-iwad", str(wadpath(demo)), "-timedemo", "demo1", "-nosound", "-nomusic"] if a.engine == "md" else [str(binary), "-iwad", str(wadpath(demo)), "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic", "-nogui"])
    extra = dict(extra, DOTNET_ROOT=str(W / "tools/dotnet"), DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1") if a.engine == "md" else extra
    try: rc = subprocess.run(cmd, cwd=home, env=env_for(home, extra), timeout=timeout or a.timeout, capture_output=True).returncode
    except subprocess.TimeoutExpired: rc = -9
    return home, rc
def refrows(demo): return sum(1 for l in open(clean / f"{demo}.txt") if len(l.split()) == 19)
# clean profiles (which functions each demo enters)
have = set() if a.refresh_profile else {r[0] for r in db.execute("select distinct demo from reach")}   # --refresh-profile: new lesion sites / new demos (insert or ignore keeps old rows)
for d in names:
    if d in have: continue
    home, rc = run(d, dict(E13_PROFILE=str(Path(tempfile.gettempdir()) / f"prof_{d}.txt"), E13_NODIGEST="1")); p = Path(tempfile.gettempdir()) / f"prof_{d}.txt"
    lines = [l.split() for l in open(p)]; p.unlink(); shutil.rmtree(home, ignore_errors=True)
    db.executemany("insert or ignore into reach values(?,?,?,?)", [(d, int(x[1]), int(x[2]), int(x[3])) for x in lines if x[0] == "F"])
    db.executemany("insert or ignore into sitereach values(?,?,?)", [(d, int(x[1]), int(x[2])) for x in lines if x[0] == "S"]); db.commit()
have_t = {r[0] for r in db.execute("select demo from clean_time")}
for d in names:
    if d in have_t: continue
    t0 = time.time(); home, rc = run(d, dict(E13_NODIGEST="1")); shutil.rmtree(home, ignore_errors=True); db.execute("insert or replace into clean_time values(?,?)", (d, time.time() - t0)); db.commit()
ctime = {d: s_ for d, s_ in db.execute("select demo, secs from clean_time")}
def tmo(d): return int(min(a.timeout, max(15, 6 * ctime.get(d, 10))))   # a lesion that makes the game loop forever is detected after 6x the clean run time
executed = {}
for d, les in db.execute("select demo, lesion from sitereach"): executed.setdefault(d, set()).add(les)
lesions = [s for s in man["sites"] if (not a.functions or s["fn"] in a.functions.split(","))]
if a.limit: lesions = lesions[:a.limit]
done = {(l, d) for l, d in db.execute("select lesion, demo from results")}
hangs = {(l, d) for l, d in db.execute("select lesion, demo from results where outcome='hang' and tries=1")} if a.rerun_hangs else set()
jobs = [(s["id"], d) for s in lesions for d in names if s["id"] in executed.get(d, ()) and ((s["id"], d) in hangs if a.rerun_hangs else (s["id"], d) not in done)]  # a lesion can only matter on demos that execute its site
print(f"{len(lesions)} lesions, {len(names)} demos, {len(jobs)} jobs to run ({len(done)} already stored)", flush=True)
def job(j):
    les, d = j
    while float(open("/proc/loadavg").read().split()[0]) > a.maxload: time.sleep(20)
    out, tic, mask, rc, tries = "crash", None, None, 0, 0
    for tries in ((2,) if a.rerun_hangs else (1,)):
        vf = Path(tempfile.gettempdir()) / f"verd_{les}_{d}_{os.getpid()}.txt"; vf.unlink(missing_ok=True)
        home, rc = run(d, dict(E13_MUT=str(les), E13_REF=str(clean / f"{d}.txt"), E13_VERDICT=str(vf), E13_NODIGEST="1"), timeout=(a.timeout if a.rerun_hangs else tmo(d))); shutil.rmtree(home, ignore_errors=True)
        out, tic, mask = "crash", None, None
        if rc == -9: out = "hang"; break          # re-run once with the full timeout in a separate pass (--rerun-hangs)
        if vf.exists():
            w = vf.read_text().split(); vf.unlink()
            if w[0] == "div": out, tic, mask = "killed", int(w[1]), int(w[2])
            elif w[0] == "end": out = "same" if int(w[1]) == refrows(d) else "killed"; tic = None if out == "same" else min(int(w[1]), refrows(d)); mask = None if out == "same" else -1   # -1: the run ended early or late (length)
        break
    with lock: db.execute("insert or replace into results values(?,?,?,?,?,?,?)", (les, d, out, tic, mask, rc, tries))
    return out
t0 = time.time(); n = 0
from concurrent.futures import as_completed
with ThreadPoolExecutor(a.workers) as ex:
    for fut in as_completed([ex.submit(job, j) for j in jobs]):
        n += 1
        if n % 200 == 0:
            with lock: db.commit()
            print(f"{n}/{len(jobs)} jobs, {time.time() - t0:.0f}s", flush=True)
db.commit(); print("done", n, "jobs in", round(time.time() - t0), "s")
