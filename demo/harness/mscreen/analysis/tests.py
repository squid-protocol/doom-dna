"""E15 hypothesis tests and controls (H1a, H2, H3, H4, PC1, N0), following the registration. Pure functions over Pheno/Graph objects."""
import math, numpy as np, pandas as pd
from sklearn.metrics import adjusted_mutual_info_score
from roles import *
def usable(ph): return ph.eligible & ~ph.hot & ~ph.inert
def tmax(*phs): return max(1e-9, max(np.nanmax(p.tic) for p in phs if np.isfinite(p.tic).any()))
def h1a(ph, demos, kmax=None):
    idx = np.where(usable(ph))[0]; sub = ph.sub(idx); T = tmax(ph); kmax = kmax or max(3, min(40, len(idx) // 4))
    g = gap_choose(sub, T, kmax, mode="gauss"); stab = stability(sub, T, g["k"], g["labels"], demos); gp = gap_choose(sub, T, kmax, mode="perm", B=100)
    share = np.mean([stab[c] >= 0.6 for c in g["labels"]]) if len(idx) else 0.0
    return dict(idx=idx, k=g["k"], labels=g["labels"], p=g["p"], p_perm=gp["p"], k_perm=gp["k"], share_stable=float(share), stab=stab, D=g["D"], n=len(idx), gap_at_k=g["gap_at_k"])
def strata(vals, q=3):
    r = pd.Series(vals).rank(method="first"); return pd.qcut(r, q, labels=False).to_numpy()
def h2(labels, fids, graph, files, reach_count, B=10000, seed=3, min_size=5):
    """size-weighted mean cross-file pairwise G3 distance within groups vs permutation of labels within (reach, degree) strata; returns hops reduction and p"""
    Dg, deg = graph.sub(fids); cf = (np.array(files)[:, None] != np.array(files)[None, :]); labs = np.asarray(labels); rng = np.random.default_rng(seed)
    st = strata(reach_count) * 3 + strata(deg)
    def stat(l):
        num = den = 0.0
        for c in np.unique(l):
            ix = np.where(l == c)[0]
            if len(ix) < min_size: continue
            m = cf[np.ix_(ix, ix)]; k = m.sum()
            if k == 0: continue
            num += len(ix) * (Dg[np.ix_(ix, ix)] * m).sum() / k; den += len(ix)
        return -num / den if den else np.nan
    obs = stat(labs); null = []
    groups = [np.where(st == s)[0] for s in np.unique(st)]
    for _ in range(B):
        l = labs.copy()
        for g in groups: l[g] = labs[rng.permutation(g)]
        null.append(stat(l))
    null = np.array(null); null = null[np.isfinite(null)]
    return dict(hops=float(obs - null.mean()) if np.isfinite(obs) else float("nan"), p=float((1 + (null >= obs).sum()) / (1 + len(null))), obs_mean=-obs, null_mean=-float(null.mean()))
def h3(la, lb, strata_b, B=10000, seed=4):
    """AMI between the two ports' group assignments over name-agree pairs; permutation of port-B labels within reach strata"""
    rng = np.random.default_rng(seed); obs = adjusted_mutual_info_score(la, lb); groups = [np.where(strata_b == s)[0] for s in np.unique(strata_b)]; null = []
    for _ in range(B):
        l = lb.copy()
        for g in groups: l[g] = lb[rng.permutation(g)]
        null.append(adjusted_mutual_info_score(la, l))
    null = np.array(null); return dict(ami=float(obs), p=float((1 + (null >= obs).sum()) / (1 + B)), null_mean=float(null.mean()), pairs=len(la))
def ranks(D, partner):
    """1-based rank of the partner column for each row of D; ties count against the matcher (pessimistic): rank = number of candidates at least as close as the partner"""
    return np.array([int((D[i] <= D[i, partner[i]]).sum()) for i in range(len(partner))])
def reach_pheno(P, fids, demos):
    """N0: clean entry-count profile (log1p entries per demo) as the 'phenotype'"""
    r = P.reach; di = {d: i for i, d in enumerate(demos)}; fi = {f: i for i, f in enumerate(fids)}; M = np.zeros((len(fids), len(demos)))
    for f, d, n in zip(r.fid, r.demo, r.entries):
        if f in fi and d in di: M[fi[f], di[d]] = math.log1p(n)
    return M
def l1(M, N): return np.abs(M[:, None, :] - N[None, :, :]).mean(2)
def h4(phA, phB, PA, PB, demos, pairs, ceiling_top5, B=10000, seed=5):
    """pairs: list of (index into usable(phA), index into usable(phB)); recovery vs chance, N0 and the within-function ceiling"""
    ia, ib = np.where(usable(phA))[0], np.where(usable(phB))[0]; sa, sb = phA.sub(ia), phB.sub(ib); T = tmax(phA, phB)
    pa = np.array([p[0] for p in pairs]); pb = np.array([p[1] for p in pairs]); D = dist(sa.sub(pa), sb, T); rk = ranks(D, pb)
    N0 = l1(reach_pheno(PA, sa.fids[pa], demos), reach_pheno(PB, sb.fids, demos)); r0 = ranks(N0, pb)
    t1, t5 = (rk == 1), (rk <= 5); n1, n5 = (r0 == 1), (r0 <= 5); chance = 5 / len(ib); rng = np.random.default_rng(seed); ok = 0; n = len(pairs)
    for _ in range(B):
        s = rng.integers(0, n, n); T5, N5, T1, N1 = t5[s].mean(), n5[s].mean(), t1[s].mean(), n1[s].mean()
        ok += (T5 >= max(3 * chance, 0.5 * ceiling_top5))          # amendment A4: N0 is reported, not a pass criterion
    return dict(top1=float(t1.mean()), top5=float(t5.mean()), n0_top1=float(n1.mean()), n0_top5=float(n5.mean()), chance_top5=float(chance), ceiling_top5=float(ceiling_top5), p=float((1 + (B - ok)) / (1 + B)), pairs=n, pool=len(ib), group_rank_median=float(np.median(rk)))
def pc1(P, seed=6):
    """split-half reliability: each function's lesions split at random into halves; the half-phenotype's rank of its own other half among all functions"""
    rng = np.random.default_rng(seed); les = P.res[P.res.outcome.isin(["killed", "same"])].groupby("fid").lesion.unique(); A, Bk = [], []; fids = []
    for f, ls in les.items():
        if len(ls) >= 8: ls = rng.permutation(ls); h = len(ls) // 2; A += list(ls[:h]); Bk += list(ls[h:]); fids.append(f)
    pa, pb = phenotype(P, keep=set(A)), phenotype(P, keep=set(Bk)); use = [f for f in fids if f in set(pa.fids) and f in set(pb.fids)]
    ia = np.array([np.where(pa.fids == f)[0][0] for f in use]); ib = np.array([np.where(pb.fids == f)[0][0] for f in use])
    ok = ~pa.hot[ia] & ~pa.inert[ia] & ~pb.hot[ib] & ~pb.inert[ib]; ia, ib = ia[ok], ib[ok]; T = tmax(pa, pb); D = dist(pa.sub(ia), pb.sub(ib), T); rk = ranks(D, np.arange(len(ia)))
    # group-level reliability: cluster the half-A and half-B phenotypes of the same functions separately; AMI of the two assignments
    sa, sb = pa.sub(ia), pb.sub(ib); k = max(3, min(15, len(ia) // 8))
    la = fcluster(linkage(squareform(sym_dist(sa, T), checks=False), "average"), k, "maxclust"); lb = fcluster(linkage(squareform(sym_dist(sb, T), checks=False), "average"), k, "maxclust")
    return dict(top1=float((rk == 1).mean()), top5=float((rk <= 5).mean()), n=len(ia), chance_top1=1 / max(1, len(ia)), group_ami=float(adjusted_mutual_info_score(la, lb)))
