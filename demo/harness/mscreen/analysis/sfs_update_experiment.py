"""SFS update experiment, step 1 (cross-validated on behaviour): learn a size gate on one port pair, test on the other (and the reverse), compared with the unchanged matcher.
Truth = behaviourally confirmed ('both': break pattern closer than 95% of random pairs AND identical call profile). Usage: python sfs_update_experiment.py <out_dir>"""
import csv, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sfs_calibration as C
from roles import load_port
S = C.S
def evaluate(df, rule, gold):
    kept = df[rule(df)]; tp = int(kept.both.sum()); prec = tp / max(1, len(kept)); rec = tp / max(1, gold); f1 = 2 * prec * rec / max(1e-9, prec + rec); return dict(kept=len(kept), correct=tp, precision=prec, recall=rec, f1=f1)
def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    fc, fm, fp = C.funcs(S / "choc_v2/manifest.json"), C.funcs(S / "md_v2/manifest.json"), C.funcs(S / "pb_v2/manifest.json"); demos = None
    A = load_port("chocolate-doom", S / "choc_phenotypes.sqlite"); Bm = load_port("managed-doom", S / "md_phenotypes.sqlite"); Pb = load_port("prboom-plus", S / "pb_phenotypes.sqlite"); demos = A.demos
    e12 = list(csv.DictReader(open(Path(__file__).resolve().parents[2] / "e14/pilot_pairs.csv"))); aC = C.adj(next((C.SCANS / "chocolate-doom").glob("*master.db"))); aM = C.adj(next((C.SCANS / "managed-doom").glob("*master.db"))); aP = C.adj(next((C.SCANS / "prboom-plus").glob("*master.db")))
    ports = {}
    for lab, PY, fy, col, tcol, adjY, exact in (("managed-doom", Bm, fm, "md_name", "md_tier", aM, False), ("prboom-plus", Pb, fp, "pb_name", "pb_tier", aP, True)):
        tab, info = C.calibrate(A, PY, fc.set_index("fid").assign(lines=fc.set_index("fid").lines), fy.set_index("fid").assign(lines=fy.set_index("fid").lines), e12, col, tcol, lab, demos, aC, adjY, exact_names=exact); ports[lab] = (info["diag"], info["gold"])
    grid = [1.1, 1.25, 1.5, 2.0, 3.0, 1e9]; md = ["# SFS update experiment, step 1: a size gate learned on one port, tested on the other\n", "Truth: behaviourally confirmed pairs (break pattern and call profile). Unchanged matcher = every E12 pair; updated matcher = pairs whose size ratio (larger / smaller function, in lines) is at most the learned gate. The gate is chosen to maximise F1 on the training port and applied unchanged to the test port.\n"]
    names = list(ports)
    for tr, te in ((names[0], names[1]), (names[1], names[0])):
        dtr, gtr = ports[tr]; dte, gte = ports[te]
        scores = {g: evaluate(dtr, lambda d, g=g: d.size_ratio <= g, gtr)["f1"] for g in grid}; best = max(scores, key=scores.get)
        base = evaluate(dte, lambda d: d.size_ratio <= 1e9, gte); upd = evaluate(dte, lambda d: d.size_ratio <= best, gte)
        rng = np.random.default_rng(1); boots = []
        for _ in range(2000):
            s = dte.iloc[rng.integers(0, len(dte), len(dte))]; boots.append(evaluate(s, lambda d: d.size_ratio <= best, gte)["precision"] - evaluate(s, lambda d: d.size_ratio <= 1e9, gte)["precision"])
        lo, hi = np.percentile(boots, [2.5, 97.5]); strong = evaluate(dte, lambda d: d.tier.isin(C.STRONG), gte)
        md += [f"## Learn on {tr}, test on {te}\n", f"Gate chosen on {tr}: size ratio <= {best if best < 1e8 else 'none'} (F1 by gate on the training port: " + ", ".join(f"{g if g < 1e8 else 'none'}: {v:.2f}" for g, v in scores.items()) + ")\n",
               pd.DataFrame([dict(matcher="unchanged SFS (all E12 pairs)", **base), dict(matcher=f"SFS with the size gate (<= {best})", **upd), dict(matcher="SFS strong tiers only", **strong)]).round(2).to_markdown(index=False), f"\nPrecision gain from the gate on the test port: {upd['precision'] - base['precision']:+.2f} (bootstrap 95% interval {lo:+.2f} to {hi:+.2f}); recall change {upd['recall'] - base['recall']:+.2f}.\n"]
    # step 2: a calibrated confidence score instead of a hard gate; fit on one port, evaluate ranking quality (AUC) on the other
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    TIER = {"exact": 6, "twin": 5, "xtwin": 4, "seed": 3, "ext1": 2, "ext2": 1, "ext3": 0}
    def feats(d, which):
        X = pd.DataFrame({"tier": d.tier.map(TIER).astype(float), "logsize": np.log(d.size_ratio.clip(lower=1.0))})
        return X[which]
    md += ["## Step 2: a calibrated confidence score instead of a hard gate\n", "Ranking quality (AUC of the score for behaviourally confirmed versus not) on the held-out port; the score is a logistic model fitted on the other port. The baseline is the matcher's own tier order.\n"]
    rows = []
    for tr, te in ((names[0], names[1]), (names[1], names[0])):
        dtr, dte = ports[tr][0], ports[te][0]
        for lab, which in (("tier order only (unchanged SFS)", ["tier"]), ("size ratio only", ["logsize"]), ("tier + size ratio (calibrated score)", ["tier", "logsize"])):
            if lab.startswith("tier order"): sc = dte.tier.map(TIER).astype(float)
            elif lab.startswith("size ratio only"): sc = -np.log(dte.size_ratio.clip(lower=1.0))
            else: m = LogisticRegression().fit(feats(dtr, which), dtr.both); sc = pd.Series(m.decision_function(feats(dte, which)), index=dte.index)
            auc = roc_auc_score(dte.both, sc); rng = np.random.default_rng(2); bs = []
            for _ in range(1000):
                k = rng.integers(0, len(dte), len(dte)); 
                if dte.both.iloc[k].nunique() > 1: bs.append(roc_auc_score(dte.both.iloc[k], sc.iloc[k]))
            rows.append(dict(fitted_on=tr, tested_on=te, score=lab, AUC=round(auc, 2), ci=f"{np.percentile(bs, 2.5):.2f} to {np.percentile(bs, 97.5):.2f}"))
    md += [pd.DataFrame(rows).to_markdown(index=False), ""]
    (out / "E15_SFS_UPDATE_STEP1.md").write_text("\n".join(md)); print("\n".join(md))
if __name__ == "__main__": main()
