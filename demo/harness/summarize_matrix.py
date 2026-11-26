"""Write a per-demo table (first strict divergence and first gameplay divergence vs the reference) for one engine.
Usage: python summarize_matrix.py <run_dir> <label> <out_csv> [ref_label=choc] [--wide] [--no-prnd]   (gameplay = angle ignored while the reference player is dead)"""
import csv, glob, os, sys
from pathlib import Path
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if "--wide" in sys.argv: os.environ["E13_WIDE"] = "1"
NOPRND = "--no-prnd" in sys.argv  # engines whose gameplay-RNG index is not comparable (not masked to 0..255, or private)
sys.path.insert(0, str(Path(__file__).resolve().parent)); import compare_digests as C
if NOPRND: C.KEEP = [k for k in C.KEEP if k != 2]
run, label, out = Path(args[0]), args[1], args[2]; ref = args[3] if len(args) > 3 else "choc"
rows = []
for f in sorted(glob.glob(str(run / f"{label}_g*.txt"))):
    d = Path(f).stem[len(label) + 1:]; a, r = C.load(f), C.load(run / f"{ref}_{d}.txt"); hdr = (run.parent / f"{d}.lmp").read_bytes()[:4]
    strict = game = None
    for i in range(min(len(a), len(r))):
        for k in C.KEEP:
            if k >= len(a[i]) or k >= len(r[i]): continue
            if a[i][k] != r[i][k]:
                if strict is None: strict = (i, C.NAMES[k])
                if C.NAMES[k] == "angle" and int(r[i][8]) <= 0: continue
                if game is None: game = (i, C.NAMES[k])
    rows.append(dict(demo=d, map=hdr[3], skill=hdr[1], strict_tic="" if not strict else strict[0], strict_field="" if not strict else strict[1], gameplay_tic="" if not game else game[0], gameplay_field="" if not game else game[1]))
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(f"{label}: {len(rows)} demos, {sum(1 for r in rows if r['gameplay_tic'] == '')} gameplay-identical, {sum(1 for r in rows if r['strict_tic'] == '')} strictly identical")
