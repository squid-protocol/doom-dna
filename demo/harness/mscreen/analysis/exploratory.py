"""E15 exploratory analyses (H5/H6 and controls PC4, N5), run on the context of the primary analysis. Pure functions over `out["_ctx"]`.
H6a: do E12 structural matches (by tier) fall in corresponding phenotype groups? H6b: where does the phenotype matcher rank the E12 partner? Also the disagreement list for the registered audit of 40 pairs."""
import csv, numpy as np, pandas as pd
from pathlib import Path
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score
from roles import *; from tests import usable, tmax, ranks
STRONG = {"exact", "twin", "xtwin", "seed"}
def align_groups(la, lb):
    """one-to-one correspondence of groups between ports by maximal overlap on name-agree pairs (Hungarian)"""
    ca, cb = np.unique(la), np.unique(lb); M = np.array([[((la == a) & (lb == b)).sum() for b in cb] for a in ca]); r, c = linear_sum_assignment(-M)
    return {ca[i]: cb[j] for i, j in zip(r, c)}
def pc4_files(labels, files, B=2000, seed=7):
    """PC4: do phenotype groups recover the source-file structure? adjusted Rand index against file labels and a permutation p"""
    rng = np.random.default_rng(seed); f = pd.factorize(np.asarray(files))[0]; obs = adjusted_rand_score(labels, f); null = [adjusted_rand_score(rng.permutation(labels), f) for _ in range(B)]
    return dict(ari=float(obs), null_mean=float(np.mean(null)), p=float((1 + sum(x >= obs for x in null)) / (1 + B)))
def n5_kind(P, ph, hh, k, kinds=None):
    """N5: do the groups just reflect the operator mix? cluster functions by their per-lesion-kind kill fraction only and compare with the phenotype groups"""
    from scipy.cluster.hierarchy import fcluster, linkage
    r = P.res[P.res.outcome.isin(["killed", "same"])].copy(); r["k"] = (r.outcome == "killed").astype(float); fids = ph.fids[hh["idx"]]
    T = r.groupby(["fid", "kind"]).k.mean().unstack().reindex(fids).fillna(0.0).to_numpy(); Z = linkage(T, "average"); lab = fcluster(Z, k, "maxclust")
    return dict(ari_with_groups=float(adjusted_rand_score(hh["labels"], lab)), kinds=int(T.shape[1]))
def h6(ctx, e12_csv, B=5000, seed=8):
    """E12 homology: tier concordance (aligned group share), rank of the structural partner under the phenotype distance, and the disagreement list"""
    phA, phB, h, fmap, pairs = ctx["phA"], ctx["phB"], ctx["h"], ctx["fmap"], ctx["pairs"]; fa, fb = fmap
    ia, ib = h[0]["idx"], h[1]["idx"]; la = h[0]["labels"][[p[0] for p in pairs]]; lb = h[1]["labels"][[p[1] for p in pairs]]; amap = align_groups(la, lb)
    namesA = {fa.loc[phA.fids[i], "name"]: j for j, i in enumerate(ia)}; namesB = {fb.loc[phB.fids[i], "name"]: j for j, i in enumerate(ib)}
    rows = list(csv.DictReader(open(e12_csv))); rng = np.random.default_rng(seed); T = tmax(phA, phB); sa, sb = phA.sub(ia), phB.sub(ib); D = dist(sa, sb, T); out = []
    for x in rows:
        a, b = namesA.get(x["ref_name"]), namesB.get(x["md_name"])
        if a is None or b is None: continue
        rk = 1 + (D[a] < D[a, b]).sum(); same = amap.get(h[0]["labels"][a]) == h[1]["labels"][b]; out.append(dict(ref=x["ref_name"], md=x["md_name"], tier=x["md_tier"], strong=x["md_tier"] in STRONG, aligned=bool(same), rank=int(rk), dist=float(D[a, b])))
    df = pd.DataFrame(out)
    if df.empty: return dict(pairs=0), df
    res = dict(pairs=len(df))
    for nm, g in (("strong tiers", df[df.strong]), ("extension tiers", df[~df.strong])):
        res[nm] = dict(n=len(g), aligned=float(g.aligned.mean()) if len(g) else float("nan"), top5=float((g["rank"] <= 5).mean()) if len(g) else float("nan"), median_rank=float(g["rank"].median()) if len(g) else float("nan"))
    la_all = h[0]["labels"]; lb_all = h[1]["labels"]; amap_all = align_groups(la, lb)
    nulls = []; names_a = df.ref.map(namesA).to_numpy(); names_b = df.md.map(namesB).to_numpy()
    for _ in range(B):
        sh = rng.permutation(names_b); nulls.append(np.mean([amap_all.get(la_all[a]) == lb_all[b] for a, b in zip(names_a, sh)]))
    res["random pairs aligned"] = float(np.mean(nulls)); res["all pairs aligned"] = float(df.aligned.mean())
    aud = pd.concat([df[(df.aligned == False) & (df["rank"] > 20)].sample(min(20, int(((df.aligned == False) & (df["rank"] > 20)).sum())), random_state=1) if ((df.aligned == False) & (df["rank"] > 20)).any() else df.iloc[:0],
                     df[(df.aligned) & (df["rank"] <= 3)].sample(min(20, int(((df.aligned) & (df["rank"] <= 3)).sum())), random_state=1) if ((df.aligned) & (df["rank"] <= 3)).any() else df.iloc[:0]])
    return res, aud
