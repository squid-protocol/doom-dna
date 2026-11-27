"""E16 real cases: per-demo symptom vectors for gore (Go) and Kocoa (Kotlin) against chocolate-doom's clean digests.
Usage: python run_cases.py run <gore|kocoa> [--repeat N] ; python run_cases.py csv <gore|kocoa>
Runs the port headless on every demo of e14/clean/ch (2 jobs, nice 10, paused when the 1-minute load average is > 6), keeps the digests under
<W>/e16cases/<port>/, then compares each to the clean digest. Compared columns: leveltime, x y z angle, health armor weapon, ammo0-3, nmobjs, mobjhash,
sectorhash, keys (NOT gametic, NOT the gameplay RNG index, NOT the cosmetic RNG index); the angle is skipped while the reference player is dead.
Mask = every mismatching column of the first diverging row (bit = column index); class set from roles.CLASS_BITS (E15 order player, world, sector, keys, time).
A run that ends with a different row count and no earlier mismatch is 'killed' at tic min(rows) with the time class (E15's mask -1 rule)."""
import csv, os, random, signal, struct, subprocess, sys, time, shutil, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from roles import CLASSES, CLASS_BITS
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"; CLEAN = E14 / "clean/ch"; OUT = W / "e16cases"
REPO = Path(__file__).resolve().parents[4]; RES = REPO / "results/e16/cases"
KEEP = [1] + list(range(4, 19))          # leveltime, x..ammo3, nmobjs, mobjhash, sectorhash, keys
DEAD_ANGLE = 7; HEALTH = 8
TIMEOUT = {"gore": 60, "kocoa": 90}
def load(f):
    f = Path(f)
    if not f.exists(): return None
    rows = [l.split() for l in open(f) if len(l.split()) == 19]       # a killed engine can leave a partial last line
    if len(rows) > 1 and int(rows[1][1]) <= int(rows[0][1]): rows = rows[1:]   # stray pre-level row
    return rows
def first_div(ref, port):
    n = min(len(ref), len(port))
    for i in range(n):
        mask = 0
        for k in KEEP:
            if ref[i][k] != port[i][k]:
                if k == DEAD_ANGLE and int(ref[i][HEALTH]) <= 0: continue
                mask |= 1 << k
        if mask: return i, mask
    return None
def classes_of(mask):
    if mask > 0: return [c for c in CLASSES if mask & CLASS_BITS[c]]
    return ["time"]
def wad_of(demo):
    p = E14 / "wads" / f"{demo}.WAD"
    return p if p.exists() else E14 / "wads" / demo / "freedoom2.wad"
def demo1_lump(wad):
    d = open(wad, "rb").read(); _, n, o = struct.unpack("<4sii", d[:12])
    for i in range(n):
        p, s, nm = struct.unpack("<ii8s", d[o + 16 * i:o + 16 * i + 16])
        if nm.rstrip(b"\0") == b"DEMO1": return d[p:p + s]
def load_ok():
    while float(open("/proc/loadavg").read().split()[0]) > 6: time.sleep(20)
def launch(port, demo, outdir):
    wad = wad_of(demo); digest = outdir / f"{demo}.txt"; log = outdir / f"{demo}.log"
    if digest.exists(): digest.unlink()
    work = Path(f"{outdir}/work_{demo}"); shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    env = dict(os.environ, HOME=str(work), XDG_DATA_HOME=str(work), XDG_CONFIG_HOME=str(work), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", E13_DIGEST=str(digest))
    if port == "gore":
        os.symlink(wad, work / "DEMOIWAD.WAD")
        cmd = [str(W / "build/gore/engine"), "-iwad", "DEMOIWAD.WAD", "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic"]
    else:   # Kocoa cannot read the per-demo IWAD copies (demo lump appended after the directory): stock base game + the demo as an external lump
        base = wad if wad.name == "freedoom2.wad" else W / "run_kocoa/DOOM1.WAD"
        os.symlink(base, work / base.name); (work / "demo1.lmp").write_bytes(demo1_lump(wad))
        cmd = ["xvfb-run", "-a", "java", "-Xmx2g", "-Xss8m", "-cp", f"{W}/build/kocoa/classes:{W}/tools/kotlinc/lib/kotlin-stdlib.jar", "mochadoom.Engine",
               "-iwad", base.name, "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic"]
    load_ok()
    with open(log, "w") as lg:
        pr = subprocess.Popen(["nice", "-n", "10"] + cmd, cwd=work, env=env, stdout=lg, stderr=subprocess.STDOUT, start_new_session=True)
    t0 = time.time(); done = None; rc = None
    while True:
        rc = pr.poll()
        if rc is not None: break
        if done is None and b"timed " in open(log, "rb").read() and b"gametics in" in open(log, "rb").read(): done = time.time()
        if done and time.time() - done > 3: break          # gore prints the timedemo line and then never exits
        if time.time() - t0 > TIMEOUT[port]: break
        time.sleep(0.25)
    timed_out = rc is None and done is None
    if rc is None:
        for sig in (signal.SIGTERM, signal.SIGKILL):          # our own process group only
            try: os.killpg(pr.pid, sig)
            except ProcessLookupError: break
            time.sleep(1.5)
        pr.wait()
    completed = b"gametics in" in open(log, "rb").read()
    shutil.rmtree(work, ignore_errors=True)
    return completed, timed_out, rc, time.time() - t0
def classify(port, demo, outdir, completed, timed_out, rc):
    ref = load(CLEAN / f"{demo}.txt"); p = load(outdir / f"{demo}.txt"); nref = len(ref) if ref else 0
    if not p: return dict(demo=demo, outcome="missing" if not timed_out else "hang", tic="", classes="", tics_port=0, tics_ref=nref), "no rows"
    row = dict(demo=demo, tic="", classes="", tics_port=len(p), tics_ref=nref)
    d = first_div(ref, p)
    partial = f"first_div={d[0]},{'+'.join(classes_of(d[1]))}" if d else "no_div_in_common_rows"
    if not completed: row["outcome"] = "hang" if timed_out else "crash"; return row, f"rc={rc} {partial}"
    if d: row.update(outcome="killed", tic=d[0], classes="+".join(classes_of(d[1])))
    elif len(p) != len(ref): row.update(outcome="killed", tic=min(len(p), len(ref)), classes="time")
    else: row["outcome"] = "same"
    return row, f"rc={rc}"
def demos(): return sorted(p.stem for p in CLEAN.glob("*.txt"))
def run_all(port, subset=None, tag=""):
    outdir = OUT / (port + tag); outdir.mkdir(parents=True, exist_ok=True); rows = {}; det = {}
    def one(d):
        c, to, rc, secs = launch(port, d, outdir); r, note = classify(port, d, outdir, c, to, rc); r["_secs"] = round(secs, 1); return d, r, note
    with ThreadPoolExecutor(2) as ex:
        for d, r, note in ex.map(one, subset or demos()):
            rows[d] = r; det[d] = note; print(d, r["outcome"], r["tic"], r["classes"], note, r["_secs"], flush=True)
    return rows, det
def main():
    mode, port = sys.argv[1], sys.argv[2]; RES.mkdir(parents=True, exist_ok=True)
    if mode == "run":
        rows, det = run_all(port)
        with open(RES / f"{port}_symptom.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["demo", "outcome", "tic", "classes", "tics_port", "tics_ref"])
            for d in sorted(rows): r = rows[d]; w.writerow([r["demo"], r["outcome"], r["tic"], r["classes"], r["tics_port"], r["tics_ref"]])
        with open(OUT / f"{port}_detail.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["demo", "note", "secs"])
            for d in sorted(rows): w.writerow([d, det[d], rows[d]["_secs"]])
    elif mode == "repeat":   # determinism: 5 random demos run twice, digests must be byte-identical
        ok = [l.split(",")[0] for l in open(RES / f"{port}_symptom.csv").read().splitlines()[1:] if l.split(",")[1] in ("killed", "same")]
        pick = random.Random(16).sample(ok, 5); run_all(port, pick, tag="_repeat")
        for d in pick:
            a, b = OUT / port / f"{d}.txt", OUT / f"{port}_repeat" / f"{d}.txt"
            print("DETERMINISM", port, d, "identical" if a.read_bytes() == b.read_bytes() else "DIFFERENT")
main()
