"""Validate the localiser with injected bugs. For N random mutants of the reference engine's simulation code:
build the mutant, find the demo where it diverges earliest from the reference, run the localiser, and score it against the known mutated function.
Usage: python evaluate_mutants.py <n_mutants> <out_csv> [seed]"""
import csv, os, random, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import locate, mutate, compare_digests as C
W = mutate.W; DEMODIR = W / "mut_demos"; BASEBIN = mutate.BUILD / "src/chocolate-doom"
DB = next((W / "../scans/704cb35f0/chocolate-doom").resolve().glob("*master.db")); GRAPH = locate.CallGraph(DB)

def setup():
    DEMODIR.mkdir(exist_ok=True); shutil.copy(W / "run/DOOM1.WAD", DEMODIR / "DOOM1.WAD"); names = []
    for i in range(20): shutil.copy(W / f"gen/g{i:04d}.lmp", DEMODIR / f"s{i:04d}.lmp"); names.append(f"s{i:04d}")
    for i in range(10): shutil.copy(W / f"gen_c/g{i:04d}.lmp", DEMODIR / f"c{i:04d}.lmp"); names.append(f"c{i:04d}")
    return names + ["demo1", "demo2", "demo3"]

def run(binary, demo, digest, trace=None, timeout=40):
    home = tempfile.mkdtemp(prefix="e13h_", dir=str(W / "mut"))
    env = dict(os.environ, HOME=home, XDG_DATA_HOME=home, XDG_CONFIG_HOME=home, LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", E13_DIGEST=str(digest))
    if trace: env["E13_TRACE"] = str(trace)
    try: subprocess.run([str(binary), "-iwad", str(DEMODIR / "DOOM1.WAD"), "-timedemo", demo, "-nodraw", "-nosound", "-nomusic", "-nogui"], cwd=DEMODIR, env=env, timeout=timeout, capture_output=True)
    except subprocess.TimeoutExpired: pass
    shutil.rmtree(home, ignore_errors=True)

def main():
    n, out = int(sys.argv[1]), sys.argv[2]; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20261126
    (W / "mut").mkdir(exist_ok=True); demos = setup(); refdir = W / "mut/ref"; refdir.mkdir(exist_ok=True)
    with ThreadPoolExecutor(8) as ex: list(ex.map(lambda d: run(BASEBIN, d, refdir / f"{d}.txt"), demos))
    rng = random.Random(seed); pool = []
    for stem in mutate.FILES:
        for s in mutate.sites((mutate.SRCDIR / f"{stem}.c").read_text()): pool.append((stem, s))
    rows = []
    for k in range(n):
        stem, site = rng.choice(pool); text = (mutate.SRCDIR / f"{stem}.c").read_text(); tag = f"m{k:03d}"
        truth = GRAPH.function_at(f"src/doom/{stem}.c", site[0]); rec = dict(mutant=tag, file=stem, line=site[0], kind=site[5], change=f"{site[3]} -> {site[4]}", truth=truth or "")
        binp = mutate.build_mutant(stem, mutate.apply(text, site), tag)
        if not binp: rec.update(status="does not build"); rows.append(rec); print(tag, rec["status"], flush=True); continue
        mdir = W / "mut" / tag
        with ThreadPoolExecutor(8) as ex: list(ex.map(lambda d: run(binp, d, mdir / f"{d}.txt"), demos))
        best = None
        for d in demos:
            a, b = C.load(refdir / f"{d}.txt"), C.load(mdir / f"{d}.txt")
            if not a: continue
            r = C.first_divergence(a, b or [], C.KEEP)
            if r and (best is None or r[0] < best[1]): best = (d, r[0], r[1])
        if not best: rec.update(status="survived"); rows.append(rec); print(tag, rec["status"], truth, flush=True); shutil.rmtree(mdir, ignore_errors=True); continue
        d = best[0]; rt, mt = mdir / f"{d}.rtrace.txt", mdir / f"{d}.mtrace.txt"
        run(BASEBIN, d, mdir / f"{d}.rref.txt", rt); run(binp, d, mdir / f"{d}.rmut.txt", mt)
        loc = locate.localise(mdir / f"{d}.rref.txt", mdir / f"{d}.rmut.txt", rt, mt, GRAPH)
        sus = loc.get("suspects", {}); susb = loc.get("suspects_b", {}); tn = locate.norm(truth) if truth else None
        rec.update(status="killed", demo=d, first_tic=loc["first_tic"], field=loc["field"], basis=loc.get("basis", ""), symptoms=" ".join(loc.get("symptoms", [])[:8]),
                   truth_depth=(sus.get(tn) if tn else None) if sus.get(tn) is not None else "", suspects_total=len(sus))
        rec["truth_depth_b"] = susb.get(tn, "") if tn else ""; rec["suspects_total_b"] = len(susb)
        for dd in range(0, 7): rec[f"closure_{dd}"] = sum(1 for v in sus.values() if v <= dd)
        rows.append(rec); print(tag, "killed", truth, "| basis", rec["basis"], "| truth depth", rec["truth_depth"], "| closure sizes", [rec[f"closure_{x}"] for x in (0, 2, 4, 6)], flush=True)
        shutil.rmtree(mdir, ignore_errors=True)
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("mutant", "file", "line", "kind", "change", "truth", "status"), k))
    with open(out, "w", newline="") as f: w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    print("wrote", out, len(rows), "mutants")

if __name__ == "__main__": main()
