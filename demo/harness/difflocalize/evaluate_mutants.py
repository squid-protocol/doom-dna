"""Validate the localiser with injected bugs (registered design: preregistration/E13_DEMO_CONFORMANCE.md, Part A).
Usage: python evaluate_mutants.py <n_attempts> <out_csv> [seed=20261201]
For each sampled mutant of the reference engine: build, run the 45 detection demos, classify (does not build / survived / crash-hang / killed), and for killed mutants run the
localiser on three choices of failing demo (earliest, a seeded random one, the median) and record everything needed for the registered analyses (see analyze_mutation_eval.py)."""
import csv, os, random, shutil, subprocess, sys, tempfile
os.environ["E13_WIDE"] = "1"   # compare the world fingerprint and keys columns too (registered)
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import locate, mutate, compare_digests as C
W = mutate.W; DEMODIR = W / "mut_demos"; BASEBIN = mutate.BUILD / "src/chocolate-doom"
DB = next((W / "../scans/704cb35f0/chocolate-doom").resolve().glob("*master.db")); GRAPH = locate.CallGraph(DB)
UNIVERSE = {n for n, (p, l) in GRAPH.where.items() if any(p.endswith(f"src/doom/{s}.c") for s in mutate.FILES)}
CAP_PER_FUNCTION = 2; NREWIRED = 20

def setup():
    DEMODIR.mkdir(exist_ok=True); shutil.copy(W / "run/DOOM1.WAD", DEMODIR / "DOOM1.WAD"); names = []
    for i in range(20): shutil.copy(W / f"gen/g{i:04d}.lmp", DEMODIR / f"s{i:04d}.lmp"); names.append(f"s{i:04d}")
    for i in range(10): shutil.copy(W / f"gen_c/g{i:04d}.lmp", DEMODIR / f"c{i:04d}.lmp"); names.append(f"c{i:04d}")
    bots = sorted((W / "gen_bot").glob("g*.lmp"))[:12]
    for i, f in enumerate(bots): shutil.copy(f, DEMODIR / f"b{i:04d}.lmp"); names.append(f"b{i:04d}")
    return names + ["demo1", "demo2", "demo3"]

def run(binary, demo, digest, trace=None, timeout=40):
    """returns (returncode, timed_out)"""
    home = tempfile.mkdtemp(prefix="e13h_", dir=str(W / "mut"))
    env = dict(os.environ, HOME=home, XDG_DATA_HOME=home, XDG_CONFIG_HOME=home, LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", E13_DIGEST=str(digest))
    if trace: env["E13_TRACE"] = str(trace)
    rc, to = 0, False
    try: rc = subprocess.run([str(binary), "-iwad", str(DEMODIR / "DOOM1.WAD"), "-timedemo", demo, "-nodraw", "-nosound", "-nomusic", "-nogui"], cwd=DEMODIR, env=env, timeout=timeout, capture_output=True).returncode
    except subprocess.TimeoutExpired: to = True
    shutil.rmtree(home, ignore_errors=True); return rc, to

def closure_row(prefix, sus, tn, total_u):
    out = {f"{prefix}_truth_depth": sus.get(tn, "") if tn else "", f"{prefix}_total": len(sus)}
    for d in range(0, 7): out[f"{prefix}_size_{d}"] = sum(1 for v in sus.values() if v <= d)
    return out

def main():
    n, out = int(sys.argv[1]), sys.argv[2]; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20261201
    (W / "mut").mkdir(exist_ok=True); demos = setup(); refdir = W / "mut/ref"; refdir.mkdir(exist_ok=True)
    with ThreadPoolExecutor(8) as ex: refrc = list(ex.map(lambda d: run(BASEBIN, d, refdir / f"{d}.txt"), demos))
    # check: tracing must not change behaviour
    for d in demos[:3] + demos[-3:]:
        run(BASEBIN, d, refdir / f"{d}.traced.txt", refdir / f"{d}.trace.txt")
        assert C.load(refdir / f"{d}.txt") == C.load(refdir / f"{d}.traced.txt"), f"tracing changed the digest on {d}"
    rng = random.Random(seed); pool = []
    for stem in mutate.FILES:
        text = (mutate.SRCDIR / f"{stem}.c").read_text()
        for s in mutate.sites(text):
            tf = GRAPH.function_at(f"src/doom/{stem}.c", s[0]); pool.append((stem, s, tf))
    rng.shuffle(pool); per_fn = {}; chosen = []
    for stem, s, tf in pool:
        if per_fn.get(tf, 0) >= CAP_PER_FUNCTION: continue
        per_fn[tf] = per_fn.get(tf, 0) + 1; chosen.append((stem, s, tf))
        if len(chosen) >= n: break
    rewired = [GRAPH.rewired(random.Random(seed + 1 + i)) for i in range(NREWIRED)]
    keys = None; fh = open(out, "w", newline=""); w = None
    for k, (stem, site, tf) in enumerate(chosen):
        text = (mutate.SRCDIR / f"{stem}.c").read_text(); tag = f"m{k:03d}"; tn = locate.norm(tf) if tf else None
        rec = dict(mutant=tag, file=stem, line=site[0], kind=site[5], change=f"{site[3]} -> {site[4]}", truth=tf or "", truth_in_universe=int(tn in UNIVERSE), truth_calls_prandom=int(bool(tn) and "prandom" in GRAPH.callees.get(tn, ())))
        binp = mutate.build_mutant(stem, mutate.apply(text, site), tag)
        if not binp: rec["status"] = "does not build"
        else:
            mdir = W / "mut" / tag
            with ThreadPoolExecutor(8) as ex: mrc = list(ex.map(lambda d: run(binp, d, mdir / f"{d}.txt"), demos))
            fails = []; crashes = 0
            for d, (rc, to) in zip(demos, mrc):
                if to or rc < 0: crashes += 1; continue
                a, b = C.load(refdir / f"{d}.txt"), C.load(mdir / f"{d}.txt")
                if not a: continue
                r = C.first_divergence(a, b or [], C.KEEP)
                if r: fails.append((r[0], d, r[1]))
            rec.update(demos_diverging=len(fails), demos_crashed=crashes)
            if not fails: rec["status"] = "crash/hang" if crashes else "survived"
            else:
                rec["status"] = "killed"; fails.sort()
                picks = {"earliest": fails[0], "random": fails[random.Random(seed * 7 + k).randrange(len(fails))], "median": fails[len(fails) // 2]}
                for which, (tic, d, fld) in picks.items():
                    rt, mt = mdir / f"{d}.rtrace.txt", mdir / f"{d}.mtrace.txt"
                    run(BASEBIN, d, mdir / f"{d}.rref.txt", rt); run(binp, d, mdir / f"{d}.rmut.txt", mt)
                    loc = locate.localise(mdir / f"{d}.rref.txt", mdir / f"{d}.rmut.txt", rt, mt, GRAPH)
                    pre = "" if which == "earliest" else f"{which}_"
                    A, B = loc.get("suspects", {}), loc.get("suspects_b", {}); syms = loc.get("symptoms", [])
                    rec.update({f"{pre}demo": d, f"{pre}first_tic": loc["first_tic"], f"{pre}field": loc["field"], f"{pre}basis": loc.get("basis", ""), f"{pre}symptoms": " ".join(syms)})
                    rec.update(closure_row(f"{pre}A", A, tn, len(UNIVERSE))); rec.update(closure_row(f"{pre}B", B, tn, len(UNIVERSE)))
                    if which == "earliest":
                        reach = GRAPH.reach_any(syms) if syms else {}; rec["reachable_any"] = int(bool(tn) and tn in reach)
                        fam = [x for x in locate.FIELD_FAMILY.get(loc["field"], []) if x in GRAPH.names]; ff = GRAPH.closure(fam, 3) if fam else {}
                        rec.update({"ff_hit_3": int(bool(tn) and tn in ff), "ff_size_3": len(ff)})
                        hits = 0; sizes = 0
                        for g in rewired:
                            c = g.closure(syms, 3) if syms else {}; hits += int(bool(tn) and tn in c); sizes += len(c)
                        rec.update({"rewired_hit_3": hits / NREWIRED, "rewired_size_3": sizes / NREWIRED})
            shutil.rmtree(mdir, ignore_errors=True)
        if w is None or any(kk not in keys for kk in rec):
            keys = sorted(set(keys or []) | set(rec), key=lambda kk: (kk not in ("mutant", "file", "line", "kind", "change", "truth", "status"), kk))
        rows_written = rec; 
        print(tag, rec["status"], tf, "|", rec.get("A_truth_depth", ""), flush=True)
        # rewrite the CSV each time with the full header (small file), so a crash loses nothing
        all_rows = getattr(main, "rows", []); all_rows.append(rec); main.rows = all_rows
        fh.seek(0); fh.truncate(); w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(all_rows); fh.flush()
    print("wrote", out, len(getattr(main, "rows", [])), "mutants")

if __name__ == "__main__": main()
