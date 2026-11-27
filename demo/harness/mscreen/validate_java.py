"""Validate the Java (Mocha Doom) schemata build. Subcommands (screen-venv python; all runs use nice and at most --jobs parallel JVMs, default 3):
  clean   <screen_dir>                     Mocha's own clean digests -> <screen_dir>/clean/<demo>.txt, a repeat run (determinism), and agreement with the chocolate-doom clean digests (information only)
  zero    <screen_dir>                     zero-lesion replay: E13_MUT unset, the instrumented build's per-tic digest file equals the clean digest, and the in-engine verdict is 'end <rows>'
  classic <screen_dir> [N=20] [seed=1]     N lesions (all 15 kinds, executed on >= 1 demo) run via the switch and via a classical rebuild of the same edit: verdicts must agree demo by demo
  profile <screen_dir>                     E13_PROFILE on every demo: function entry counts and site counters
Usage: python validate_java.py <cmd> <screen_dir> [args] [--jobs 3]"""
import json, os, random, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); sys.path.insert(0, str(H.parent))
import jv_common as J
a = [x for x in sys.argv[1:] if not x.startswith("--")]; jobs = int(next((x.split("=")[1] for x in sys.argv if x.startswith("--jobs=")), 3))
cmd, screen = a[0], Path(a[1]); clean = screen / "clean"; names = J.demo_names(); INST = f"{screen}/bin/inst:{screen}/bin/base"
def pool(fn, items):
    with ThreadPoolExecutor(jobs) as ex: return list(ex.map(fn, items))
def load(p): return [l.split() for l in open(p) if len(l.split()) == 19]
def digest_run(cp, d, out, extra=None):
    home, rc, secs = J.run_mocha(cp, d, dict(E13_DIGEST=str(out), **(extra or {})), keep_home=False); return rc, secs
if cmd == "clean":
    for d in names: J.extract_lmp(d)   # <demo>.lmp = the DEMO1 lump of the e14 WAD (Mocha loads IWAD + external lump)
    (screen / "clean").mkdir(exist_ok=True); (screen / "clean_repeat").mkdir(exist_ok=True); import compare_digests as C
    def one(d):
        r1 = digest_run(J.CLEAN_CP, d, clean / f"{d}.txt"); r2 = digest_run(J.CLEAN_CP, d, screen / "clean_repeat" / f"{d}.txt"); return d, r1, r2
    res = pool(one, names); det = 0; ok = []; bad = []; ch = 0; chbad = []
    for d, r1, r2 in res:
        f1, f2 = clean / f"{d}.txt", screen / "clean_repeat" / f"{d}.txt"
        if f1.exists() and f2.exists() and f1.read_bytes() == f2.read_bytes() and f1.stat().st_size > 0: det += 1
        rows = J.nrows(f1) if f1.exists() else 0
        (ok if rows > 200 else bad).append((d, rows, r1[0]))
        c = C.load(J.E14 / "clean/ch" / f"{d}.txt"); m = C.load(f1) if f1.exists() else None
        if c and m:
            r = C.first_divergence(c, m, [k for k in [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]], True)
            if r is None: ch += 1
            else: chbad.append((d, r))
    print(f"clean digests written for {len(ok)}/{len(names)} demos; repeat run byte-identical on {det}/{len(names)}; identical to chocolate-doom on all common columns (dead-angle ignored): {ch}/{len(names)}")
    print("no/short digest:", bad[:10]); print("differs from chocolate (first 10):", chbad[:10]); print("mean wall s per clean run:", round(sum(r[1][1] for r in res) / len(res), 2))
elif cmd == "zero":
    (screen / "zero").mkdir(exist_ok=True)
    def one(d):
        f = screen / "zero" / f"{d}.txt"; vf = screen / "zero" / f"{d}.verdict"; vf.unlink(missing_ok=True)
        home, rc, secs = J.run_mocha(INST, d, dict(E13_DIGEST=str(f), E13_REF=str(clean / f"{d}.txt"), E13_VERDICT=str(vf)))
        same = f.exists() and f.read_bytes() == (clean / f"{d}.txt").read_bytes(); v = vf.read_text().split() if vf.exists() else ["none"]
        return d, same, v, J.nrows(clean / f"{d}.txt"), secs
    res = pool(one, names); okn = [d for d, s, v, n, _ in res if s and v == ["end", str(n)]]
    print(f"zero-lesion replay: {len(okn)}/{len(names)} demos: instrumented digest byte-identical to the clean digest and verdict 'end <rows>'")
    print("not identical:", [(d, s, v, n) for d, s, v, n, _ in res if d not in okn][:10]); print("mean wall s per instrumented run:", round(sum(r[4] for r in res) / len(res), 2))
elif cmd == "profile":
    man = json.load(open(screen / "manifest.json")); (screen / "prof").mkdir(exist_ok=True)
    def one(d):
        pf = screen / "prof" / f"{d}.txt"; home, rc, secs = J.run_mocha(INST, d, dict(E13_PROFILE=str(pf), E13_NODIGEST="1")); return d, rc, secs
    res = pool(one, names); fe = {}; se = {}; nonempty = 0
    for d, rc, secs in res:
        pf = screen / "prof" / f"{d}.txt"
        if not pf.exists(): continue
        nonempty += 1
        for l in open(pf):
            w = l.split()
            if w[0] == "F": fe.setdefault(int(w[1]), {})[d] = (int(w[2]), int(w[3]))
            else: se.setdefault(int(w[1]), set()).add(d)
    fids = {f["fid"] for f in man["functions"]}; sites = {s["id"] for s in man["sites"]}
    print(f"profile files for {nonempty}/{len(names)} demos; functions in manifest {len(fids)}, entered by >= 1 demo {len(fids & set(fe))}, unknown fids in profiles {len(set(fe) - fids)}; "
          f"lesion sites in manifest {len(sites)}, executed by >= 1 demo {len(sites & set(se))}, unknown site ids {len(set(se) - sites)}")
    print("functions never entered (first 40):", sorted(f["name"] for f in man["functions"] if f["fid"] not in fe)[:40])
    json.dump({"entered": {k: len(v) for k, v in fe.items()}, "sites": {k: sorted(v) for k, v in se.items()}}, open(screen / "profile_summary.json", "w"))
    print("mean wall s per profiled run:", round(sum(r[2] for r in res) / len(res), 2))
elif cmd == "classic":
    N = int(a[2]) if len(a) > 2 else 20; seed = int(a[3]) if len(a) > 3 else 1; man = json.load(open(screen / "manifest.json")); prof = json.load(open(screen / "profile_summary.json"))
    cand = [s for s in man["sites"] if str(s["id"]) in prof["sites"]]; rng = random.Random(seed); bykind = {}
    for s in cand: bykind.setdefault(s["kind"], []).append(s)
    pick = [rng.choice(v) for k, v in sorted(bykind.items())]   # one per kind (15), the rest uniformly random among lesions executed on >= 1 demo
    while len(pick) < N:
        s = rng.choice(cand)
        if s not in pick: pick.append(s)
    pick = pick[:N]; src0 = J.W / "build/mochadoom/src"; res_all = []; bad = 0; work = screen / "classic"; shutil.rmtree(work, ignore_errors=True); work.mkdir()
    def run(cp, d, mut, tag):
        vf = work / f"{tag}_{d}.verdict"; vf.unlink(missing_ok=True); ex = dict(E13_REF=str(clean / f"{d}.txt"), E13_VERDICT=str(vf), E13_NODIGEST="1")
        if mut is not None: ex["E13_MUT"] = str(mut)
        home, rc, secs = J.run_mocha(cp, d, ex, timeout=60); return J.verdict_outcome(vf, J.nrows(clean / f"{d}.txt"), rc)
    for k, s in enumerate(pick):
        rel = f"p/{s['path']}.java"; orig = (src0 / rel).read_bytes(); st, en, new = s["edit"] if "edit" in s else (s["byte"], s["byte"] + len(s["op"]), s["new"])
        if "edit" not in s: assert orig[st:en] == s["op"].encode(), (s["id"], orig[st:en], s["op"])
        patched = orig[:st] + new.encode("latin-1") + orig[en:]; cdir = work / f"c{k}"; (cdir / "src" / Path(rel).parent).mkdir(parents=True); (cdir / "cls").mkdir(); (cdir / "src" / rel).write_bytes(patched)
        r = subprocess.run(["javac", "-nowarn", "-encoding", "ISO-8859-1", "-cp", f"{screen}/bin/base", "-d", str(cdir / "cls"), str(cdir / "src" / rel)], capture_output=True, text=True)
        if r.returncode: print(f"lesion {s['id']} {s['fn']} {s['op']}->{s['new']}: classical rebuild does not compile:", r.stderr[:300], flush=True); bad += 1; continue
        ex_d = [d for d in names if d in {x for x in prof["sites"][str(s["id"])]}]   # the demos that execute the site, plus up to 6 that do not (they must agree trivially)
        others = [d for d in names if d not in ex_d][:6]; ds = ex_d + others
        sw = pool(lambda d: run(INST, d, s["id"], "sw"), ds); cl = pool(lambda d: run(f"{cdir / 'cls'}:{screen}/bin/base", d, None, "cl"), ds)
        diff = [(d, x, y) for d, x, y in zip(ds, sw, cl) if x != y]; ks = sum(x[0] == "killed" for x in sw); kc = sum(x[0] == "killed" for x in cl)
        res_all.append((s["id"], not diff)); bad += bool(diff)
        print(f"lesion {s['id']:5d} {s['kind']:12s} {s['fn'][:24]:24s} {s['op'][:6]:>6s}->{s['new'][:6]:<6s} on {len(ds):2d} demos: killed {ks:2d} switch, {kc:2d} rebuilt, first-tic+mask compared: {'IDENTICAL' if not diff else 'DIFFERENT ' + str(diff[:2])}", flush=True)
        shutil.rmtree(cdir, ignore_errors=True)
    print(f"{N - bad}/{N} lesions identical between the switch and a classical rebuild")
