"""E15 PC2 (identity ceiling): near-clone port (prboom-plus) versus chocolate-doom. For functions whose text is identical (and, as sensitivity, near-identical) between the two, is the chocolate-doom counterpart
the top-1 nearest neighbour of the prboom-plus function's break pattern? Usage: python pc2.py <out_dir>   (env E15_PB_DB, E15_CHOC_DB override the stores)"""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from roles import *; from tests import usable, tmax, ranks
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); S = W / "screen"
def main():
    out_dir = Path(sys.argv[1]); out_dir.mkdir(parents=True, exist_ok=True)
    A = load_port("chocolate-doom", os.environ.get("E15_CHOC_DB", str(S / "choc_phenotypes.sqlite"))); P = load_port("prboom-plus", os.environ.get("E15_PB_DB", str(S / "pb_phenotypes.sqlite")))
    fa = {f["fid"]: f["name"] for f in json.load(open(os.environ.get("E15_CHOC_MAN", str(S / "choc_v2/manifest.json"))))["functions"]}; fp = {f["fid"]: f["name"] for f in json.load(open(S / "pb_v2/manifest.json"))["functions"]}
    ident = json.load(open(S / "pb_identical_functions.json")); phA, phP = phenotype(A), phenotype(P); ia, ip = np.where(usable(phA))[0], np.where(usable(phP))[0]; sa, sp = phA.sub(ia), phP.sub(ip); T = tmax(phA, phP)
    namesA = {fa[f]: j for j, f in enumerate(sa.fids)}; namesP = {fp[f]: j for j, f in enumerate(sp.fids)}; D = dist(sp, sa, T); md = ["# E15 PC2: identity ceiling (prboom-plus vs chocolate-doom)\n", f"usable functions: chocolate-doom {len(ia)}, prboom-plus {len(ip)}\n"]
    for label, names in (("identical text", ident["identical"]), ("near-identical text (>= 0.9 token similarity)", ident["near_identical"])):
        pairs = [(namesP[n], namesA[n], n) for n in names if n in namesP and n in namesA]
        if not pairs: md.append(f"## {label}\nno usable pairs\n"); continue
        rk = ranks(D[[p[0] for p in pairs]], np.array([p[1] for p in pairs])); t1 = float((rk == 1).mean()); t5 = float((rk <= 5).mean())
        md += [f"## {label}: {len(pairs)} functions", f"top-1 {t1:.2f}, top-5 {t5:.2f} (chance top-1 {1 / len(ia):.3f}); registered PC2 threshold top-1 >= 0.90 on the identical-text set: **{'PASSED' if label == 'identical text' and t1 >= 0.9 else ('FAILED' if label == 'identical text' else 'sensitivity')}**\n", "| function | rank of the chocolate-doom counterpart |\n|---|---|"] + [f"| {n} | {int(r)} |" for (_, _, n), r in zip(pairs, rk)] + [""]
    (out_dir / "E15_PC2.md").write_text("\n".join(md)); print("\n".join(md)[:1500])
if __name__ == "__main__": main()
