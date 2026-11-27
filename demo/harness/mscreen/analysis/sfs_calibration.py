"""Calibrating the structural matcher (SFS/E12) against independent behavioural measures: the lesion break pattern (D) and the clean call-count profile (N0), compared with names.
'Behaviourally confirmed' thresholds come from the data's own noise (distance between two random halves of the SAME function), not from names or structure.
Usage: python sfs_calibration.py <out_dir>"""
import csv, re, sys, os
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from roles import *; from tests import usable, tmax, reach_pheno, l1
from graphs import g1_edges, norm
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); S = W / "screen"; SCANS = W.parent / "scans/704cb35f0"; PREFIX = re.compile(r"^(EV_|P_|A_|T_|PIT_|PTR_)")
STRONG = {"exact", "twin", "xtwin", "seed"}
def funcs(man): import json; return pd.DataFrame([dict(fid=f["fid"], name=f["name"], file=f["file"], lines=f["end_line"] - f["line"] + 1) for f in json.load(open(man))["functions"]])
def self_distance(P, T, seed=6):
    """distances between two random halves of the same function's lesions (the noise floor of the break pattern)"""
    rng = np.random.default_rng(seed); les = P.res[P.res.outcome.isin(["killed", "same"])].groupby("fid").lesion.unique(); A_, B_, fids = [], [], []
    for f, ls in les.items():
        if len(ls) >= 8: ls = rng.permutation(ls); h = len(ls) // 2; A_ += list(ls[:h]); B_ += list(ls[h:]); fids.append(f)
    pa, pb = phenotype(P, keep=set(A_)), phenotype(P, keep=set(B_)); use = [f for f in fids if f in set(pa.fids) and f in set(pb.fids)]
    ia = np.array([np.where(pa.fids == f)[0][0] for f in use]); ib = np.array([np.where(pb.fids == f)[0][0] for f in use]); ok = ~pa.hot[ia] & ~pa.inert[ia] & ~pb.hot[ib] & ~pb.inert[ib]; ia, ib = ia[ok], ib[ok]
    Dd = dist(pa.sub(ia), pb.sub(ib), T); return np.diag(Dd)
def calibrate(PX, PY, fx, fy, e12, namecol, tiercol, label, demos, adjX, adjY, exact_names=False):
    phX, phY = phenotype(PX), phenotype(PY); ix, iy = np.where(usable(phX))[0], np.where(usable(phY))[0]; sx, sy = phX.sub(ix), phY.sub(iy); T = tmax(phX, phY)
    D = dist(sx, sy, T); N0 = l1(reach_pheno(PX, sx.fids, demos), reach_pheno(PY, sy.fids, demos)); nx = [fx.loc[f, "name"] for f in sx.fids]; ny = [fy.loc[f, "name"] for f in sy.fids]; kx = list(nx) if exact_names else [PREFIX.sub("", n) for n in nx]   # C to C ports keep their names; C to C# strips the C prefixes
    sd = self_distance(PX, T); t_noise = float(np.quantile(sd, 0.90)); rngc = np.random.default_rng(3); rnd = D[rngc.integers(0, len(nx), 20000), rngc.integers(0, len(ny), 20000)]; t_self = float(np.quantile(rnd, 0.05))   # threshold = the 5th percentile of random cross-port pairs (data-driven, name-free); the within-function noise floor is reported beside it
    ex = {n: i for i, n in enumerate(nx)}; ey = {n: j for j, n in enumerate(ny)}
    pairs = []
    for r in e12:
        i, j = ex.get(r["ref_name"]), ey.get(r[namecol])
        if i is not None and j is not None: pairs.append((i, j, r[tiercol], r["ref_name"], r[namecol]))
    namepairs = [(i, j) for i in range(len(nx)) for j in range(len(ny)) if kx[i] == ny[j] and len(kx[i]) >= 4]
    Dm = D.copy(); Dm[Dm >= 0.999] = np.inf; bestY = Dm.argmin(1); bestX = Dm.argmin(0)
    def row(name, prs):
        prs = list(prs)
        if not prs: return dict(group=name, n=0)
        d = np.array([D[i, j] for i, j in prs]); q = np.array([N0[i, j] for i, j in prs]); rbh = np.array([bool(np.isfinite(Dm[i, j]) and bestY[i] == j and bestX[j] == i) for i, j in prs])
        return dict(group=name, n=len(prs), phenotype_confirmed=float((d <= t_self).mean()), call_profile_identical=float((q < 1e-9).mean()), both=float(((d <= t_self) & (q < 1e-9)).mean()), mutual_nearest=float(rbh.mean()), median_distance=float(np.median(d)), contradicted=float((d > np.median(rnd)).mean()))
    rows = [row("name-agree pairs", namepairs)]
    for nm, tiers in (("SFS strong tiers (exact, twin, xtwin, seed)", STRONG), ("SFS ext1", {"ext1"}), ("SFS ext2", {"ext2"}), ("SFS ext3", {"ext3"})): rows.append(row(nm, [(i, j) for i, j, t, a, b in pairs if t in tiers]))
    rows.append(row("SFS all tiers", [(i, j) for i, j, t, a, b in pairs])); rows.append(row("SFS pairs that agree with the name", [(i, j) for i, j, t, a, b in pairs if kx[i] == ny[j]])); rows.append(row("SFS pairs that disagree with the name", [(i, j) for i, j, t, a, b in pairs if kx[i] != ny[j]]))
    rng = np.random.default_rng(1); rows.append(row("random pairs (chance)", [(int(rng.integers(len(nx))), int(rng.integers(len(ny)))) for _ in range(2000)]))
    # recall: behaviourally confirmed pairs (mutual nearest, indistinguishable from self, identical call profile) recovered by each matcher
    gold = {(i, int(bestY[i])) for i in range(len(nx)) if np.isfinite(Dm[i, bestY[i]]) and bestX[bestY[i]] == i and D[i, bestY[i]] <= t_self and N0[i, bestY[i]] < 1e-9}
    sfs = {(i, j) for i, j, t, a, b in pairs}; strong = {(i, j) for i, j, t, a, b in pairs if t in STRONG}; nm = set(namepairs)
    rec = {k: len(gold & v) / max(1, len(gold)) for k, v in (("names", nm), ("SFS (all tiers)", sfs), ("SFS strong tiers", strong), ("names or SFS", nm | sfs))}
    # the SFS pairs fall within the evaluable set only where both functions have a phenotype; report how many of the gold pairs SFS even proposes a partner for
    # diagnostics for the unconfirmed SFS pairs: size ratio and call-graph neighbour agreement (anchors = SFS strong pairs, name-free)
    anchors = {norm(a): norm(b) for i, j, t, a, b in pairs if t in STRONG}
    def nbr(a, b):
        nA, nB = adjX.get(norm(a), set()), adjY.get(norm(b), set()); anc = [anchors[x] for x in nA if x in anchors]
        return sum(1 for y in anc if y in nB) / len(anc) if len(anc) >= 2 else np.nan
    lx = dict(zip(fx.name, fx.lines)); ly = dict(zip(fy.name, fy.lines))
    def sr(a, b): u, v = lx.get(a, 1), ly.get(b, 1); return max(u, v) / max(1, min(u, v))
    diag = pd.DataFrame([dict(tier=t, confirmed=bool(D[i, j] <= t_self), size_ratio=sr(a, b), nbr=nbr(a, b)) for i, j, t, a, b in pairs])
    e12by = {}
    for r in e12: e12by.setdefault(r["ref_name"], set()).add(r[namecol])
    bd = {"SFS right": 0, "SFS proposed a different function": 0, "SFS proposed nothing": 0}
    for i, j in gold:
        prop = e12by.get(nx[i]); 
        if not prop: bd["SFS proposed nothing"] += 1
        elif ny[j] in prop: bd["SFS right"] += 1
        else: bd["SFS proposed a different function"] += 1
    bd2 = {"SFS right": 0, "SFS proposed a different function": 0, "SFS proposed nothing": 0}
    for i, j in gold:
        if kx[i] == ny[j]: continue
        prop = e12by.get(nx[i])
        if not prop: bd2["SFS proposed nothing"] += 1
        elif ny[j] in prop: bd2["SFS right"] += 1
        else: bd2["SFS proposed a different function"] += 1
    nb_ = {"name right": sum(1 for i, j in gold if kx[i] == ny[j]), "name wrong or absent": sum(1 for i, j in gold if kx[i] != ny[j])}
    sizes = pd.DataFrame([dict(sr=sr(a, b), ok=bool(D[i, j] <= t_self and N0[i, j] < 1e-9)) for i, j, t, a, b in pairs]); sizes["bin"] = pd.cut(sizes.sr, [0, 1.25, 2, 1e9], labels=["size ratio <= 1.25", "1.25 to 2", "> 2"])
    sb = sizes.groupby("bin", observed=True).ok.agg(["size", "mean"]).rename(columns={"size": "SFS pairs", "mean": "behaviourally confirmed"}).reset_index()
    return pd.DataFrame(rows), dict(gold_breakdown=bd, renamed_breakdown=bd2, name_breakdown=nb_, size_bins=sb, t_self=t_self, t_noise=t_noise, n_usable=(len(nx), len(ny)), gold=len(gold), recall=rec, diag=diag)
def adj(path):
    A_ = {}
    for a, b in g1_edges(path): A_.setdefault(a, set()).add(b); A_.setdefault(b, set()).add(a)
    return A_
def auc(pos, neg):
    pos, neg = [x for x in pos if x == x], [x for x in neg if x == x]
    if not pos or not neg: return float("nan")
    return float(np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in neg]))
def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    fc, fm, fp = funcs(S / "choc_v2/manifest.json"), funcs(S / "md_v2/manifest.json"), funcs(S / "pb_v2/manifest.json"); fc_, fm_, fp_ = fc.set_index("fid"), fm.set_index("fid"), fp.set_index("fid")
    A = load_port("chocolate-doom", S / "choc_phenotypes.sqlite"); Bm = load_port("managed-doom", S / "md_phenotypes.sqlite"); Pb = load_port("prboom-plus", S / "pb_phenotypes.sqlite"); demos = A.demos
    e12 = list(csv.DictReader(open(Path(__file__).resolve().parents[2] / "e14/pilot_pairs.csv"))); aC = adj(next((SCANS / "chocolate-doom").glob("*master.db"))); aM = adj(next((SCANS / "managed-doom").glob("*master.db"))); aP = adj(next((SCANS / "prboom-plus").glob("*master.db")))
    md = ["# Calibrating the structural matcher (SFS/E12) against behaviour\n", "Behavioural measures (independent of names and of structure): the lesion break pattern (distance D between functions) and the clean call-count profile. 'Phenotype confirmed' = D no larger than the 5th percentile of random cross-port function pairs (chance level 5%), so the threshold comes from the data, not from names. 'both' = phenotype confirmed and call profile identical. 'Call profile identical' = the two functions run exactly the same number of times on all 77 demos. 'Contradicted' = D above the median of random pairs.\n"]
    for lab, PY, fy_, col, tcol, adjY in (("chocolate-doom -> managed-doom (independent lineage)", Bm, fm_, "md_name", "md_tier", aM), ("chocolate-doom -> prboom-plus (near-clone)", Pb, fp_, "pb_name", "pb_tier", aP)):
        exact = "prboom" in lab
        tab, info = calibrate(A, PY, fc_.reset_index().set_index("fid").assign(lines=fc.set_index("fid").lines), fy_.assign(lines=(fm if "managed" in lab else fp).set_index("fid").lines), e12, col, tcol, lab, demos, aC, adjY, exact_names=exact)
        md += [f"## {lab}\n", f"usable functions {info['n_usable']}; behavioural threshold D <= {info['t_self']:.3f} (the 5th percentile of random cross-port pairs; the within-function split-half noise floor is {info['t_noise']:.3f}, too lax to separate pairs from chance); behaviourally confirmed mutual-nearest pairs (the gold set): {info['gold']}\n", tab.round(2).to_markdown(index=False), "",
               "Share of the gold pairs each matcher recovers: " + ", ".join(f"{k} {v:.0%}" for k, v in info["recall"].items()) + "\n"]
        md.append("What SFS did on the behaviourally confirmed pairs: " + ", ".join(f"{k} {v}" for k, v in info["gold_breakdown"].items()) + f" (of {info['gold']}). Names: " + ", ".join(f"{k} {v}" for k, v in info["name_breakdown"].items()) + ".\n")
        md.append("On the confirmed pairs that names miss (renames, " + str(sum(info['renamed_breakdown'].values())) + "): " + ", ".join(f"{k} {v}" for k, v in info["renamed_breakdown"].items()) + ".\n")
        md += ["SFS precision by size ratio (larger / smaller function, in lines):\n", info["size_bins"].round(2).to_markdown(index=False), ""]
        dg = info["diag"]; md.append(f"Failure diagnostics on the {len(dg)} SFS pairs with data: confirmed {int(dg.confirmed.sum())}, unconfirmed {int((~dg.confirmed).sum())}. AUC of 'smaller size ratio' for confirmed vs unconfirmed: {auc(-dg[dg.confirmed].size_ratio, -dg[~dg.confirmed].size_ratio):.2f}; AUC of 'call-graph neighbour agreement' (anchors = SFS strong pairs only): {auc(dg[dg.confirmed].nbr, dg[~dg.confirmed].nbr):.2f} (n with enough anchored neighbours: {int(dg.nbr.notna().sum())}).\n")
    (out / "E15_SFS_CALIBRATION.md").write_text("\n".join(md)); print("\n".join(md)[:7000])
if __name__ == "__main__": main()
