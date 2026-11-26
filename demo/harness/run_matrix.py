"""Run every engine on every demo in a directory and compare each engine's per-tic digest against the reference engine.
Usage: python run_matrix.py <demo_dir> <out_csv> [--engines a,b,c]
Engines and their quirks live in ENGINES below. Writes one row per (demo, engine): status, first divergence tic, field, tics played."""
import csv, os, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import compare_digests as C
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); H = Path(__file__).resolve().parent
B = W / "build"
ENGINES = {  # label: (binary, compare without the gameplay RNG column?, extra env)
    "choc": (B / "chocolate-doom/build/src/chocolate-doom", False, {}),
    "dg": (B / "doomgeneric/engine", False, {}),
    "crispy": (B / "crispy-doom/build/src/crispy-doom", False, {}),
    "pboom": (B / "prboom-plus/build/prboom-plus", True, {"DOOMWADDIR": str(W / "wads")}),
    "sdl": (B / "sdl-doom/build/sdl2-doom", False, {}),
    "inter": (B / "inter-doom/build/src/inter-doom", True, {}),
    "pd": (B / "puredoom/engine", False, {}),
}
REF = "choc"
def run_one(args):
    run, label, demo = args
    binary, _, env = ENGINES[label]
    e = dict(os.environ, E13_RUN=str(run), E13_TIMEOUT="60", **env)
    subprocess.run([str(H / "run_demo.sh"), str(binary), label, demo, *([] if label != "pd" else [])], env=e, capture_output=True)
def main():
    demo_dir, out_csv = Path(sys.argv[1]), Path(sys.argv[2])
    labels = list(ENGINES)
    if "--engines" in sys.argv: labels = sys.argv[sys.argv.index("--engines") + 1].split(",")
    run = demo_dir / "_run"; run.mkdir(exist_ok=True)
    for f in ("DOOM1.WAD", "doom1.wad"): shutil.copy(W / "run/DOOM1.WAD", run / f) if not (run / f).exists() else None
    demos = sorted(p.stem for p in demo_dir.glob("*.lmp"))
    for d in demos: shutil.copy(demo_dir / f"{d}.lmp", run / f"{d}.lmp")
    jobs = [(run, l, d) for d in demos for l in labels]
    with ThreadPoolExecutor(6) as ex: list(ex.map(run_one, jobs))
    rows = []
    for d in demos:
        ref = C.load(run / f"{REF}_{d}.txt")
        hdr = (demo_dir / f"{d}.lmp").read_bytes()[:4]
        for l in labels:
            a = C.load(run / f"{l}_{d}.txt")
            if a is None or ref is None: rows.append(dict(demo=d, skill=hdr[1], map=hdr[3], engine=l, status="no digest", tic="", field="", tics=0, ref_tics=len(ref or []))); continue
            keep = [k for k in C.KEEP if not (ENGINES[l][1] and k == 2)]
            r = C.first_divergence(ref, a, keep)
            rows.append(dict(demo=d, skill=hdr[1], map=hdr[3], engine=l, status="identical" if r is None else "diverges", tic="" if r is None else r[0], field="" if r is None else r[1], tics=len(a), ref_tics=len(ref)))
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} rows -> {out_csv}")
if __name__ == "__main__": main()
