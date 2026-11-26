"""Strict and 'gameplay' comparison of a translation's per-tic digests against the reference engine over a demo set.
strict: every field. gameplay: the view angle is ignored on tics where the reference player is dead (health <= 0), because death-camera turning is cosmetic.
Usage: python analyze_translation.py <run_dir> <label> [ref_label=choc] [--no-prnd]"""
import collections, glob, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import compare_digests as C
run, label = Path(sys.argv[1]), sys.argv[2]
ref_label = next((a for a in sys.argv[3:] if not a.startswith("--")), "choc"); noprnd = "--no-prnd" in sys.argv
keep = [k for k in C.KEEP if not (noprnd and k == 2)]
rows = []; names = C.NAMES
for f in sorted(glob.glob(str(run / f"{label}_*.txt"))):
    demo = Path(f).stem[len(label) + 1:]
    a, r = C.load(f), C.load(run / f"{ref_label}_{demo}.txt")
    if not a or not r: rows.append((demo, "missing", None, None, 0)); continue
    n = min(len(a), len(r)); strict = None; game = None; deadonly = True
    for i in range(n):
        for k in keep:
            if a[i][k] != r[i][k]:
                if strict is None: strict = (i, names[k])
                dead = int(r[i][8]) <= 0
                if names[k] == "angle" and dead: continue
                if game is None: game = (i, names[k])
                deadonly = False
    rows.append((demo, "ok", strict, game, (len(a), len(r))))
ok = [r for r in rows if r[1] == "ok"]
print(f"{label} vs {ref_label}: {len(ok)} demos compared ({len(rows) - len(ok)} missing)")
print("  strictly identical on every field:", sum(1 for r in ok if r[2] is None))
print("  identical on gameplay (angle ignored while dead):", sum(1 for r in ok if r[3] is None))
print("  length mismatches:", sum(1 for r in ok if r[4][0] != r[4][1]))
fl = collections.Counter(r[2][1] for r in ok if r[2]); print("  strict divergence first field:", dict(fl))
fg = [(r[0], r[3]) for r in ok if r[3]]; print("  gameplay divergences:", fg[:10], "..." if len(fg) > 10 else "")
