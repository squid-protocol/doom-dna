"""E15 exploratory report: H6 (E12 homology), PC4 (file recovery), N5 (lesion-kind control), group tables, hot and inert lists. Usage: python run_exploratory.py <out_dir>  (after the primary run)"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_e15 import context
from pipeline import analyze
from exploratory import *
E12 = Path(__file__).resolve().parents[1] / "../e14/pilot_pairs.csv"
def report(out, A, B, e12_csv, fmap):
    ctx = out["_ctx"]; md = ["# E15 exploratory analyses\\n"]; names = ("chocolate-doom", "managed-doom"); phs = (ctx["phA"], ctx["phB"]); Ps = (A, B)
    md.append("## Group tables (usable functions per group)\\n")
    for i in range(2):
        h = ctx["h"][i]; f = fmap[i]; fids = phs[i].fids[h["idx"]]; rows = []
        for c in np.unique(h["labels"]):
            ix = np.where(h["labels"] == c)[0]; rows.append((int(c), len(ix), ", ".join(f.loc[x, "name"] for x in fids[ix][:10]) + (" ..." if len(ix) > 10 else ""), h["stab"].get(c, float("nan"))))
        md += [f"### {names[i]} (k={h['k']}, usable {len(h['idx'])})\\n", "| group | size | stability | first functions |\\n|---|---|---|---|"] + [f"| {c} | {n} | {s:.2f} | {fs} |" for c, n, fs, s in rows] + [""]
        hot = ", ".join(f.loc[x, "name"] for x in phs[i].fids[phs[i].hot]); inert = int(phs[i].inert.sum()); md.append(f"Hot class ({int(phs[i].hot.sum())}): {hot}\\n\\nInert class: {inert} functions\\n")
        files = [f.loc[x, "file"] for x in fids]; md.append(f"PC4 (groups vs source files): {pc4_files(h['labels'], files)}\\n"); md.append(f"N5 (operator-kind control): {n5_kind(Ps[i], phs[i], h, h['k'])}\\n")
    res, aud = h6(ctx, e12_csv); md += ["## H6: E12 structural matches versus phenotype groups\\n", f"{res}\\n"]
    return "\\n".join(md), aud
def main():
    out_dir = Path(sys.argv[1]); out_dir.mkdir(parents=True, exist_ok=True); A, B, GA, GB, fc, fm = context(); out = analyze(A, B, GA, GB, fc, fm)
    text, aud = report(out, A, B, str(E12.resolve()), (fc.set_index("fid"), fm.set_index("fid"))); (out_dir / "E15_EXPLORATORY.md").write_text(text); aud.to_csv(out_dir / "E15_H6_audit_list.csv", index=False); print(text[:3000])
if __name__ == "__main__": main()
