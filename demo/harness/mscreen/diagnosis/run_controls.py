"""E16 remaining controls on T1 (frozen scorer): ties, hub statistic, true-negative confidence gap, A2 class-only, leave-demo-family-out. Usage: python run_controls.py <out_dir>"""
import json, sys, collections
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import prep, score
from run_dev import counterparts
from roles import load_port, phenotype
HERE = Path(__file__).resolve().parent; FZ = json.load(open(HERE / "FROZEN_SCORER.json")); W3 = (FZ["weights"]["a_failing_set"], FZ["weights"]["b_class"], FZ["weights"]["c_tic"])
def auc(pos, neg):
    pos = np.asarray(pos); neg = np.asarray(neg); return float(((pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()) / (len(pos) * len(neg)))
def evalset(qidx, SB, D, groups, truth, w, mask, tmax, wts, minev, pool_mask=None):
    ranks = []; tops = []
    for n, qi in enumerate(qidx):
        q = {k: SB[k][qi].copy() for k in ("K", "M", "T", "C")}; q["M"] = q["M"] | ~mask; a, b, c, nE, nK, _ = score.components(q, D, tmax); sc = np.where((nE >= minev) & (nK >= 1), wts[0] * a + wts[1] * b + wts[2] * c, 0).astype(np.float32); fs = score.aggregate(sc, groups, "max")
        if pool_mask is not None: fs = np.where(pool_mask, fs, -1)
        ranks.append(score.rank_of(fs, truth[n])); tops.append(fs)
    return np.array(ranks), np.array(tops)
def main():
    out = Path(sys.argv[1]); sp = json.load(open(HERE / "split.json")); A, phA, fa, ua = prep.load(); SA = prep.symptoms(A); B = load_port("managed-doom", prep.S / "md_phenotypes.sqlite"); phB = phenotype(B); fb = prep.functions(prep.S / "md_v2/manifest.json").set_index("fid"); SB = prep.symptoms(B)
    cp = counterparts(A, phA, fa, B, phB, fb, ua); test = set(sp["test_fids"]); dev = set(sp["dev_fids"]); cand = sorted(int(x) for x in ua); ci = {f: i for i, f in enumerate(cand)}; metaA = SA["meta"]; D = {k: SA[k] for k in ("K", "M", "T", "C")}; tmax = FZ["tmax"]
    groups = [np.where(metaA.fid.to_numpy() == f)[0] for f in cand]; metaB = SB["meta"]; nk = (SB["K"] & ~SB["M"]).sum(1); alld = np.ones(len(A.demos), bool)
    def queries(S):
        m = metaB.fid.map(lambda f: cp.get(int(f), -1) in S).to_numpy() & (nk >= 3); qi = np.where(m)[0]; qf = metaB.fid.iloc[qi].map(lambda f: cp[int(f)]).to_numpy(); mf = pd.Series(qf).value_counts(); return qi, np.array([ci[f] for f in qf]), qf, np.array([1.0 / mf[f] for f in qf])
    qi, truth, qf, w = queries(test); fns = sorted(set(qf)); md = ["# E16 controls on T1 (frozen scorer, test half)\n"]
    r, tops = evalset(qi, SB, D, groups, truth, w, alld, tmax, W3, FZ["min_eval"]); base5 = score.metrics(r, w)["top5"]
    # ties and hub
    ties = np.array([int((tops[n] == tops[n][truth[n]]).sum()) for n in range(len(qi))]); top5sets = [set(np.argsort(-tops[n], kind="stable")[:5]) for n in range(len(qi))]; cnt = collections.Counter(f for s in top5sets for f in s); hub = sum(c for _, c in cnt.most_common(5)) / (5 * len(qi))
    md += [f"**Ties:** median tie-set size at the truth's score {np.median(ties):.0f}, share of queries with ties > 1: {np.mean(ties > 1):.3f} (ranks are pessimistic).\n", f"**Hub statistic:** the five most often returned functions fill {hub:.3f} of all top-5 slots (uniform would be {5 * 5 / len(cand):.3f}); " + ", ".join(f"{fa.loc[cand[f], 'name']} ({c})" for f, c in cnt.most_common(5)) + ".\n"]
    # true negative: confidence gap, truth present vs removed
    top_present = np.array([tops[n].max() for n in range(len(qi))]); top_absent = []
    for n in range(len(qi)):
        t = truth[n]; q = {k: SB[k][qi[n]] for k in ("K", "M", "T", "C")}; a, b, c, nE, nK, _ = score.components(q, D, tmax); sc = np.where((nE >= FZ["min_eval"]) & (nK >= 1), W3[0] * a + W3[1] * b + W3[2] * c, 0).astype(np.float32); sc[groups[t]] = 0; top_absent.append(score.aggregate(sc, groups, "max").max())
    top_absent = np.array(top_absent); md += [f"**True negative (truth's lesions removed):** mean best score present {top_present.mean():.3f} vs absent {top_absent.mean():.3f}; AUC of the best score for telling present from absent {auc(top_present, top_absent):.3f} (0.5 = cannot tell). Wrong answers are therefore {'distinguishable' if auc(top_present, top_absent) > 0.7 else 'not reliably distinguishable'} from right ones by the score alone.\n"]
    # A2 class-only: top 20% of pool
    for name, S, pool in (("development half (pool 70, top 14)", dev, 14), ("test half (pool 140, top 28)", test, 28)):
        q2, t2, f2, w2 = queries(S); pm = None
        if S is dev: pm = np.array([f in dev for f in cand])
        rr, _ = evalset(q2, SB, D, groups, t2, w2, alld, tmax, (0, 1, 0), FZ["min_eval"], pm)
        if S is dev: rr = np.array([min(x, 10 ** 6) for x in rr])
        md.append(f"**A2 class-only scorer, {name}:** share with the truth in the top {pool}: {np.average(rr <= pool, weights=w2):.3f}")
    md.append("")
    # leave-demo-family-out (first letter of the demo name)
    fam = np.array([d[0] for d in A.demos]); rows = []
    for g in sorted(set(fam)):
        keep = fam != g; rr, _ = evalset(qi, SB, D, groups, truth, w, keep, tmax, W3, FZ["min_eval"]); rows.append(dict(left_out=g, demos_left_out=int((~keep).sum()), top5=score.metrics(rr, w)["top5"], top1=score.metrics(rr, w)["top1"]))
    for g in sorted(set(fam)):
        keep = fam == g
        if keep.sum() >= 10: rr, _ = evalset(qi, SB, D, groups, truth, w, keep, tmax, W3, FZ["min_eval"]); rows.append(dict(left_out=f"ONLY {g}", demos_left_out=int((~keep).sum()), top5=score.metrics(rr, w)["top5"], top1=score.metrics(rr, w)["top1"]))
    md += [f"**Demo-family sensitivity** (primary top-5 on all 77 demos {base5:.3f}):\n", pd.DataFrame(rows).round(3).to_markdown(index=False)]
    (out / "E16_CONTROLS.md").write_text("\n".join(md)); print("\n".join(md))
if __name__ == "__main__": main()
