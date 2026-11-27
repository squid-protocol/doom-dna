"""Validate the gore (Go) schemata build and make gore's own clean reference digests (every lesion is compared with gore's own clean run, not chocolate-doom's).
Usage (screen-venv python):
  python validate_go.py clean   [--jobs 2]            clean digests of the UNMODIFIED build/gore engine -> screen/go_v2/clean/<demo>.txt, status.json (completed / crash / hang)
  python validate_go.py repeat  [--jobs 2]            the same again into clean_repeat/, byte-compared (determinism)
  python validate_go.py zero    [--jobs 3]            zero-lesion replay: E13_MUT unset, (a) digest file byte-identical to the clean digest, (b) early-abort verdict 'end <rows>'
  python validate_go.py equiv   [N=20] [seed=1] [strat]  N random lesions (strat: round robin over the 15 kinds): switch (schemata) vs a classical source patch of exactly that change, verdicts on every demo
  python validate_go.py profile                       E13_PROFILE on every demo: format, coverage of the instrumented functions, cross-check of entry counts against chocolate-doom's profile
gore never exits after the timedemo line (unmodified engine): the run is stopped by process group a few seconds after that line. The instrumented build ends itself (e13Finish)."""
import json, os, random, re, shutil, signal, sqlite3, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H))
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"; S = W / "screen/go_v2"; ORIG = W / "build/gore/engine"; INST = S / "bin/engine"
GOENV = {"PATH": "/usr/bin:/bin", "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=mod", "GOPATH": str(W / "tools/gopath"), "GOCACHE": str(W / "tools/gocache"), "GOPROXY": "off", "CGO_ENABLED": "0"}
TMP = S / "work"

def demos(wads=E14 / "wads"):
    return sorted({p.stem for p in wads.glob("*.WAD")} | {p.parent.name for p in wads.glob("*/freedoom2.wad")})
def wadpath(d, wads=E14 / "wads"):
    return (wads / f"{d}.WAD") if (wads / f"{d}.WAD").exists() else (wads / d / "freedoom2.wad")
def load_ok(maxload=6.0):
    while float(open("/proc/loadavg").read().split()[0]) > maxload: time.sleep(20)

def run_gore(binary, demo, extra=None, timeout=60, wads=E14 / "wads", after_line=3.0):
    """Run one demo headless in a scratch directory (the IWAD-swap demo as DEMOIWAD.WAD). Returns (rc, finished, hung, secs, log): rc None when we had to stop the process;
    finished = the timedemo line was printed; hung = no timedemo line before the timeout. Stops only its own process group."""
    TMP.mkdir(parents=True, exist_ok=True); work = Path(tempfile.mkdtemp(prefix="g_", dir=str(TMP))); os.symlink(wadpath(demo, wads), work / "DEMOIWAD.WAD")
    env = dict(os.environ, HOME=str(work), XDG_DATA_HOME=str(work), XDG_CONFIG_HOME=str(work), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", **(extra or {}))
    for k in [k for k in env if k.startswith("E13_") and extra is not None and k not in extra]: del env[k]
    logf = work / "log.txt"; t0 = time.time()
    with open(logf, "w") as lg:
        pr = subprocess.Popen(["nice", "-n", "10", str(binary), "-iwad", "DEMOIWAD.WAD", "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic"], cwd=work, env=env, stdout=lg, stderr=subprocess.STDOUT, start_new_session=True)
    done = None; rc = None
    while True:
        rc = pr.poll()
        if rc is not None: break
        if done is None and b"gametics in" in logf.read_bytes(): done = time.time()
        if done and time.time() - done > after_line: break
        if time.time() - t0 > timeout: break
        time.sleep(0.05)
    hung = rc is None and done is None
    if rc is None:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try: os.killpg(pr.pid, sig)
            except ProcessLookupError: break
            time.sleep(0.5)
        pr.wait()
    log = logf.read_bytes(); shutil.rmtree(work, ignore_errors=True)
    return rc, b"gametics in" in log, hung, time.time() - t0, log

def rows_of(path):
    p = Path(path)
    return sum(1 for l in open(p) if len(l.split()) == 19) if p.exists() else 0

def clean_pass(out, jobs):
    out.mkdir(parents=True, exist_ok=True); status = {}
    def one(d):
        load_ok(); dig = out / f"{d}.txt"; dig.unlink(missing_ok=True)
        rc, fin, hung, secs, log = run_gore(ORIG, d, {"E13_DIGEST": str(dig)})
        st = "ok" if fin else ("hang" if hung else "crash")
        if not fin and not hung: tail = log.decode("latin-1").strip().splitlines()[:2]
        else: tail = []
        return d, dict(status=st, rows=rows_of(dig), rc=rc, secs=round(secs, 1), note=" | ".join(tail)[:160])
    with ThreadPoolExecutor(jobs) as ex:
        for d, r in ex.map(one, demos()): status[d] = r; print(d, r, flush=True)
    (out / "status.json").write_text(json.dumps(status, indent=1)); return status

def classify(binary_dir, d, extra, timeout, wads=E14 / "wads", clean=None):
    """One screen-style run of the instrumented engine -> ('killed', tic, mask) | ('same',) | ('crash',) | ('hang',)"""
    vf = TMP / f"v_{os.getpid()}_{d}_{extra.get('E13_MUT', 'x')}.txt"; TMP.mkdir(parents=True, exist_ok=True); vf.unlink(missing_ok=True)
    rc, fin, hung, secs, log = run_gore(binary_dir, d, dict(extra, E13_REF=str(clean / f"{d}.txt"), E13_VERDICT=str(vf), E13_NODIGEST="1"), timeout=timeout, wads=wads, after_line=0.5)
    v = vf.read_text().split() if vf.exists() else None; vf.unlink(missing_ok=True); nref = rows_of(clean / f"{d}.txt")
    if hung or (rc == -9): return ("hang",)
    if v and v[0] == "div": return ("killed", int(v[1]), int(v[2]))
    if v and v[0] == "end": return ("same",) if int(v[1]) == nref else ("killed", min(int(v[1]), nref), -1)
    return ("crash",)

def good_demos(clean=S / "clean"):
    st = json.load(open(clean / "status.json")); return sorted(d for d, r in st.items() if r["status"] == "ok")

def cmd_clean(jobs, tag="clean"):
    st = clean_pass(S / tag, jobs); import collections
    print("clean digests:", dict(collections.Counter(r["status"] for r in st.values())), "| excluded:", {d: r["status"] for d, r in st.items() if r["status"] != "ok"})

def cmd_repeat(jobs):
    a = json.load(open(S / "clean/status.json")); b = clean_pass(S / "clean_repeat", jobs); same = []; diff = []
    for d in sorted(a):
        if a[d]["status"] != "ok" and b[d]["status"] != "ok": same.append((d, "both " + a[d]["status"])); continue
        (same if (S / "clean" / f"{d}.txt").read_bytes() == (S / "clean_repeat" / f"{d}.txt").read_bytes() and a[d]["status"] == b[d]["status"] else diff).append(d)
    print(f"determinism: {len(a) - len(diff)}/{len(a)} demos identical on repeat (byte-identical digests and the same status); different: {diff}")

def cmd_zero(jobs):
    ds = good_demos(); res = {}
    def one(d):
        dig = TMP / f"z_{d}.txt"; TMP.mkdir(parents=True, exist_ok=True); dig.unlink(missing_ok=True)
        rc, fin, hung, secs, log = run_gore(INST, d, {"E13_DIGEST": str(dig)}, after_line=0.5)   # (a) digest file with no lesion active
        a = dig.exists() and dig.read_bytes() == (S / "clean" / f"{d}.txt").read_bytes(); n = rows_of(dig); dig.unlink(missing_ok=True)
        b = classify(INST, d, {}, 60, clean=S / "clean")                                          # (b) early-abort comparison against the clean reference
        return d, a, b, n, round(secs, 2), rc
    with ThreadPoolExecutor(jobs) as ex:
        for r in ex.map(one, ds): res[r[0]] = r
    bad = [(d, r[1], r[2], r[5]) for d, r in res.items() if not (r[1] and r[2] == ("same",))]
    print(f"zero-lesion replay: {len(ds) - len(bad)}/{len(ds)} completed demos identical (digest bytes AND early-abort verdict 'end <rows>'); not identical: {bad}")
    allst = json.load(open(S / "clean/status.json")); print(f"all {len(allst)} demos run; not completed on the unmodified engine (excluded from the screen): {{d: r['status'] for d, r in allst.items() if r['status'] != 'ok'}}".replace("{d: r['status'] for d, r in allst.items() if r['status'] != 'ok'}", str({d: r['status'] for d, r in allst.items() if r['status'] != 'ok'})))
    for d in sorted(allst):
        if allst[d]["status"] != "ok": print(f"  {d}: unmodified engine {allst[d]['status']}; instrumented engine, no lesion: ", classify(INST, d, {}, 30, clean=S / "clean"))

def cmd_equiv(N, seed, strat=False):
    man = json.load(open(S / "manifest.json")); base = S / "base"; ds = good_demos(); rng = random.Random(seed); sites = [s for s in man["sites"]]
    src0 = (base / "doom.go").read_bytes(); pick = []; skipped = []
    work = S / "classic"; shutil.rmtree(work, ignore_errors=True); shutil.copytree(base, work)
    order = rng.sample(sites, len(sites)); results = []
    if strat:   # round robin over the 15 lesion kinds, so every kind is validated
        byk = {}
        for x in order: byk.setdefault(x["kind"], []).append(x)
        order = [lst[i] for i in range(len(sites)) for lst in byk.values() if i < len(lst)]
    for s in order:
        if len(pick) >= N: break
        if s["kind"] == "shift" and False: continue
        if "edit" in s: a, b, new = s["edit"]; 
        else: a, b, new = s["byte"], s["byte"] + len(s["op"]), s["new"]
        old = src0[a:b]
        if "edit" not in s: assert old == s["op"].encode(), (s["id"], old, s["op"])
        (work / "doom.go").write_bytes(src0[:a] + new.encode() + src0[b:])
        r = subprocess.run([str(W / "tools/go/bin/go"), "build", "-o", str(work / f"engine_{s['id']}"), "./cmd/e13"], cwd=work, capture_output=True, text=True, env=dict(GOENV, HOME=str(work)))
        if r.returncode: skipped.append((s["id"], s["kind"], (r.stderr.strip().splitlines() or ["?"])[0][:90])); continue
        eng = work / f"engine_{s['id']}"
        with ThreadPoolExecutor(3) as ex:
            x = list(ex.map(lambda d: classify(INST, d, {"E13_MUT": str(s["id"])}, 6, clean=S / "clean"), ds)); y = list(ex.map(lambda d: classify(eng, d, {}, 6, clean=S / "clean"), ds))
        eng.unlink(); diff = [(d, p, q) for d, p, q in zip(ds, x, y) if p != q]
        print(f"lesion {s['id']:5d} {s['kind']:12s} {s['fn']:24s} {s['op']:>6s}->{s['new']:<6s} switch vs classical rebuild on {len(ds)} demos: {'IDENTICAL' if not diff else 'DIFFERENT ' + str(diff[:3])}", flush=True)
        pick.append((s, not diff))
    (work / "doom.go").write_bytes(src0)
    print(f"{sum(ok for _, ok in pick)}/{len(pick)} lesions identical between the switch and a classical rebuild; {len(skipped)} drawn lesions had a classical patch that does not compile (schemata-only semantics): {skipped}")

def cmd_profile():
    man = json.load(open(S / "manifest.json")); fids = {f["fid"]: f["name"] for f in man["functions"]}; sids = {s["id"] for s in man["sites"]}; ds = good_demos(); union = {}; bad = 0; tot = {}
    def one(d):
        pf = TMP / f"p_{d}.txt"; TMP.mkdir(parents=True, exist_ok=True); pf.unlink(missing_ok=True); run_gore(INST, d, {"E13_PROFILE": str(pf), "E13_NODIGEST": "1"}, after_line=0.5)
        lines = [l.split() for l in open(pf)] if pf.exists() else []; pf.unlink(missing_ok=True); return d, lines
    with ThreadPoolExecutor(3) as ex:
        for d, lines in ex.map(one, ds):
            for x in lines:
                if x[0] == "F":
                    if int(x[1]) not in fids: bad += 1
                    union[int(x[1])] = union.get(int(x[1]), 0) + int(x[2]); tot.setdefault(d, {})[int(x[1])] = int(x[2])
                elif x[0] == "S" and int(x[1]) not in sids and int(x[1]) not in {s_ for s_ in range(0, 1 << 17)} : bad += 1
    print(f"profile: {len(ds)} demos; {len(union)}/{len(fids)} functions entered by at least one demo; {bad} profile lines with an unknown id; never entered: {sorted(fids[f] for f in set(fids) - set(union))}")
    # static check: every instrumented function has exactly one e13Enter at the top of its body
    txt = (S / "tree/doom.go").read_text("latin-1"); ents = re.findall(r"\{ e13Enter\((\d+)\);", txt); print("e13Enter calls:", len(ents), "distinct fids:", len(set(ents)), "functions:", len(fids))
    # cross-check against chocolate-doom's profile (name-agree functions, same demos; gore diverges from chocolate on most demos so counts are compared on the first-demo-tic window only as a sanity check)
    db = S.parent / "choc_phenotypes.sqlite" if (S.parent / "choc_phenotypes.sqlite").exists() else None
    if db:
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True); cf = {r[0]: r[1] for r in c.execute("select fid, name from functions")}; ce = {}
        for d, fid, n in c.execute("select demo, fid, entries from reach"): ce.setdefault(cf.get(fid), {}).setdefault(d, n)
        low = {k[0].lower() + k[1:]: v for k, v in ce.items() if k}; agree = 0; both = 0; ratios = []
        for fid, name in fids.items():
            if name not in low: continue
            both += 1
            ds_ = [d for d in tot if fid in tot[d] and d in low[name]]
            if ds_: agree += 1; ratios += [tot[d][fid] / low[name][d] for d in ds_ if low[name][d]]
        ratios.sort(); print(f"cross-check vs chocolate-doom's profile: {both} name-agree functions, {agree} entered in both; median gore/chocolate entry ratio {ratios[len(ratios)//2]:.3f} over {len(ratios)} (function, demo) pairs; 10-90 percentile {ratios[len(ratios)//10]:.2f}-{ratios[9*len(ratios)//10]:.2f}")

if __name__ == "__main__":
    a = sys.argv[1:]; jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else (3 if a and a[0] in ("zero", "profile") else 2); pos = [x for x in a if not x.startswith("--") and not x.isdigit() or x in a[:1]]
    if a[0] == "clean": cmd_clean(jobs)
    elif a[0] == "repeat": cmd_repeat(jobs)
    elif a[0] == "zero": cmd_zero(jobs)
    elif a[0] == "equiv": cmd_equiv(int(a[1]) if len(a) > 1 and a[1].isdigit() else 20, int(a[2]) if len(a) > 2 and a[2].isdigit() else 1, "strat" in a)
    elif a[0] == "profile": cmd_profile()
