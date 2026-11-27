"""E16 real cases: score gore and Kocoa symptom vectors with the FROZEN scorer and baselines. Usage: python score_cases.py <out_dir>"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import prep, score
from roles import CLASSES
HERE = Path(__file__).resolve().parent; FZ = json.load(open(HERE / "FROZEN_SCORER.json")); W3 = (FZ["weights"]["a_failing_set"], FZ["weights"]["b_class"], FZ["weights"]["c_tic"]); ROOT = HERE.parents[3]
def vec(csv, demos, drop=()):
    d = pd.read_csv(csv).set_index("demo"); n = len(demos); q = dict(K=np.zeros(n, bool), M=np.zeros(n, bool), T=np.zeros(n, np.float32), C=np.zeros(n, np.uint8))
    for i, dm in enumerate(demos):
        r = d.loc[dm] if dm in d.index else None
        if r is None or r.outcome in ("crash", "hang", "missing") or dm in drop: q["M"][i] = True; continue
        if r.outcome == "killed":
            q["K"][i] = True; q["T"][i] = np.log10(float(r.tic) + 1); cl = str(r.classes).split("+") if isinstance(r.classes, str) else []; q["C"][i] = sum(1 << CLASSES.index(c) for c in cl if c in CLASSES) or (1 << CLASSES.index("time"))
    return q
def main():
    out = Path(sys.argv[1]); A, phA, fa, ua = prep.load(); SA = prep.symptoms(A); cand = sorted(int(x) for x in ua); metaA = SA["meta"]; D = {k: SA[k] for k in ("K", "M", "T", "C")}; groups = [np.where(metaA.fid.to_numpy() == f)[0] for f in cand]
    covA = prep.reach_matrix(A, cand) > 0; RA = prep.reach_matrix(A, cand); fam = np.array([d[0] for d in A.demos]); fams = sorted(set(fam)); famprof = np.array([[D["K"][g][:, fam == f_].mean() for f_ in fams] for g in groups]); nm = [fa.loc[f, "name"] for f in cand]; allnames = {fa.loc[f, "name"]: f for f in fa.index}
    kd = pd.read_csv(ROOT / "results/e16/cases/kocoa_symptom.csv"); early = tuple(kd[(kd.outcome == "killed") & (kd.tic <= 1)].demo)
    md = ["# E16 real cases (frozen scorer; candidates = 140 usable chocolate-doom functions)\n"]
    for label, csv, drop, targets in (("gore", "gore_symptom.csv", (), ["P_CrossSubsector"]), ("Kocoa", "kocoa_symptom.csv", (), ["P_NewChaseDir", "A_Chase", "P_Move", "P_TryWalk", "P_CheckMissileRange"]), ("Kocoa (3 start-state demos x0014/x0043/x0056 set aside)", "kocoa_symptom.csv", ("x0014", "x0043", "x0056"), ["P_NewChaseDir", "A_Chase", "P_Move", "P_TryWalk", "P_CheckMissileRange"]), ("Kocoa SENSITIVITY (post hoc, after seeing the first run): every demo diverging at tic 0 or 1 set aside as a start-state artifact of the external-demo path", "kocoa_symptom.csv", early, ["P_NewChaseDir", "A_Chase", "P_Move", "P_TryWalk", "P_CheckMissileRange"])):
        q = vec(ROOT / "results/e16/cases" / csv, A.demos, drop); E = ~q["M"]; F = q["K"] & E; P = ~q["K"] & E; a, b, c, nE, nK, _ = score.components(q, D, FZ["tmax"]); sc = np.where((nE >= FZ["min_eval"]) & (nK >= 1), W3[0] * a + W3[1] * b + W3[2] * c, 0).astype(np.float32); fs = score.aggregate(sc, groups, FZ["agg"])
        KL = D["K"] & E[None, :]; met = score.aggregate(((KL & F[None, :]).sum(1) / np.sqrt(max(F.sum(), 1) * np.maximum(KL.sum(1), 1))).astype(np.float32), groups, "max"); och = score.ochiai(covA, F, P); qv = np.array([F[fam == f_].mean() for f_ in fams]); fm = -np.abs(famprof - qv[None, :]).sum(1)
        md += [f"## {label}: evaluated demos {int(E.sum())}, killed {int(F.sum())}, same {int(P.sum())}; median first-tic of kills {np.median(np.expm1(q['T'][F])):.0f}\n", f"Best similarity {fs.max():.3f}; ties at the top {int((fs == fs.max()).sum())}.\n"]
        top = np.argsort(-fs, kind="stable")[:12]; md += ["Top 12 (dictionary scorer): " + ", ".join(f"{nm[i]} ({fs[i]:.3f})" for i in top) + "\n", "Top 8 Ochiai: " + ", ".join(nm[i] for i in np.argsort(-och, kind="stable")[:8]) + "\n", "Top 8 Metallaxis-style: " + ", ".join(nm[i] for i in np.argsort(-met, kind="stable")[:8]) + "\n"]
        rows = []
        for t in targets:
            if t in nm: i = nm.index(t); rows.append(dict(target=t, usable=True, rank_dictionary=score.rank_of(fs, i), rank_ochiai=score.rank_of(och, i), rank_metallaxis=score.rank_of(met, i), rank_family=score.rank_of(fm, i)))
            else: rows.append(dict(target=t, usable=False, note="not in the 140 usable candidates (hot, inert, outside screened files or named differently): scored as a miss"))
        md += [pd.DataFrame(rows).to_markdown(index=False), ""]
    (out / "E16_CASES.md").write_text("\n".join(md)); print("\n".join(md))
if __name__ == "__main__": main()
