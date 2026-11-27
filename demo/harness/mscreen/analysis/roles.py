"""E15 analysis core: function phenotypes from a screen store, the registered distance, hot/inert classes, clustering with the gap statistic and bootstrap stability.
Everything here follows preregistration/E15_ROLE_SCREEN.md. Nothing reads a database unless a function is called with its path."""
import collections, math, random, sqlite3
import numpy as np, pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import jensenshannon, squareform
CLASSES = ["player", "world", "sector", "keys", "time"]
CLASS_BITS = {"player": sum(1 << c for c in range(4, 15)), "world": (1 << 15) | (1 << 16), "sector": 1 << 17, "keys": 1 << 18, "time": 1 << 1}   # the RNG bit (2) is never a class
W_L1, W_TIC, W_CLS = 0.6, 0.2, 0.2
MIN_CO = 5; MIN_INF = 4; HOT_FRAC = 0.9

class Port:
    """a screen store: lesions, results (observed lesion x demo pairs), clean per-function entry counts"""
    def __init__(self, name, lesions, results, reach, demos):
        self.name, self.lesions, self.res, self.reach, self.demos = name, lesions, results, reach, list(demos)
def _subset(self, demos=None, kinds=None, lesion_ids=None, suffix=""):
    """a filtered view of a port (demo subset, lesion kinds, lesion ids), used for the registered sensitivity analyses"""
    res, reach, dm = self.res, self.reach, self.demos
    if demos is not None: ds = set(demos); res = res[res.demo.isin(ds)]; reach = reach[reach.demo.isin(ds)]; dm = [d for d in self.demos if d in ds]
    if kinds is not None: res = res[res.kind.isin(kinds)]
    if lesion_ids is not None: res = res[res.lesion.isin(lesion_ids)]
    return Port(self.name + suffix, self.lesions, res, reach, dm)
Port.subset = _subset
def load_port(name, db_path, exclude_shift=True):
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    les = pd.read_sql("select * from lesions", db); res = pd.read_sql("select * from results", db); reach = pd.read_sql("select * from reach", db); demos = sorted(pd.read_sql("select distinct demo from sitereach", db).demo)
    res = res.merge(les[["id", "fid", "file", "fn", "kind"]], left_on="lesion", right_on="id").drop(columns="id")
    if exclude_shift: res = res[res.kind != "shift"]
    return Port(name, les, res, reach, demos)

class Pheno:
    def __init__(self, fids, F, tic, cls, ninf):
        self.fids, self.F, self.tic, self.cls, self.ninf = fids, F, tic, cls, ninf
        obs = ~np.isnan(F); self.obs = obs
        with np.errstate(invalid="ignore"):
            self.hot = np.array([(obs[i].sum() > 0) and (np.nanmean(F[i][obs[i]] >= HOT_FRAC) >= HOT_FRAC) for i in range(len(fids))])
            self.inert = np.array([obs[i].sum() > 0 and np.nansum(F[i]) == 0 for i in range(len(fids))])
        self.eligible = (ninf >= MIN_INF)
    def sub(self, idx): return Pheno(self.fids[idx], self.F[idx], self.tic[idx], self.cls[idx], self.ninf[idx])
    @property
    def n(self): return len(self.fids)

def phenotype(P, keep=None):
    r = P.res[P.res.outcome.isin(["killed", "same"])]
    if keep is not None: r = r[r.lesion.isin(keep)]
    di = {d: i for i, d in enumerate(P.demos)}; fids = np.array(sorted(r.fid.unique())); fi = {f: i for i, f in enumerate(fids)}; n, nd = len(fids), len(P.demos)
    S = np.zeros((n, nd)); C = np.zeros((n, nd))
    for (f, d), g in r.groupby(["fid", "demo"]): S[fi[f], di[d]] = (g.outcome == "killed").sum(); C[fi[f], di[d]] = len(g)
    F = np.where(C > 0, S / np.maximum(C, 1), np.nan)
    k = r[r.outcome == "killed"].copy(); tic = np.full(n, np.nan); cls = np.full((n, len(CLASSES)), np.nan)
    k["ltic"] = np.log10(k.tic.fillna(0) + 1)
    for f, g in k.groupby("fid"):
        tic[fi[f]] = g.ltic.median(); v = np.zeros(len(CLASSES))
        for m in g["mask"]:
            m = int(m); bits = [c for c, b in zip(CLASSES, [CLASS_BITS[c] for c in CLASSES]) if (m & b)] if m > 0 else ["time"]   # mask -1: the run ended early or late
            for c in bits: v[CLASSES.index(c)] += 1
        cls[fi[f]] = v / v.sum() if v.sum() else np.nan
    ninf = np.array([r[r.fid == f].lesion.nunique() for f in fids])
    return Pheno(fids, F, tic, cls, ninf)

def _nanrule(a, b, val):
    """terms with missing values: both missing -> 0, one missing -> 1"""
    out = np.where(np.isnan(a) & np.isnan(b), 0.0, np.where(np.isnan(a) | np.isnan(b), 1.0, val)); return out
def dist(A, B, Tmax):
    n, m = A.n, B.n; D = np.ones((n, m)); oa, ob = A.obs, B.obs; Fa, Fb = np.nan_to_num(A.F), np.nan_to_num(B.F)
    for i in range(n):
        co = oa[i][None, :] & ob; k = co.sum(1)
        l1 = (np.abs(Fa[i][None, :] - Fb) * co).sum(1) / np.maximum(k, 1)
        with np.errstate(invalid="ignore"):
            t = _nanrule(np.full(m, A.tic[i]), B.tic, np.abs(A.tic[i] - B.tic) / Tmax)
            pa = np.broadcast_to(A.cls[i], B.cls.shape); js = np.nan_to_num(jensenshannon(np.nan_to_num(pa, nan=0.2), np.nan_to_num(B.cls, nan=0.2), base=2, axis=1))
            js = np.where(np.isnan(A.cls[i][0]) | np.isnan(B.cls[:, 0]), _nanrule(np.full(m, A.cls[i][0]), B.cls[:, 0], 0.0), js)
        D[i] = np.where(k >= MIN_CO, W_L1 * l1 + W_TIC * t + W_CLS * js, 1.0)
    return D
def sym_dist(A, Tmax):
    D = dist(A, A, Tmax); D = (D + D.T) / 2; np.fill_diagonal(D, 0.0); return D

def wk(D, labels):
    tot = 0.0
    for c in np.unique(labels):
        ix = np.where(labels == c)[0]
        if len(ix) > 1: tot += D[np.ix_(ix, ix)].sum() / (2 * len(ix))
    return tot
def cut(D, kmax):
    Z = linkage(squareform(D, checks=False), "average"); return Z, {k: fcluster(Z, k, "maxclust") for k in range(2, kmax + 1)}
def null_pheno(ph, rng, mode="gauss"):
    """null datasets for the gap test. 'gauss' (primary, SigClust-style): rows drawn from a multivariate normal with the observed per-demo means and covariance (a continuum with the same correlations, no clusters),
    observed-demo mask kept, values clipped to [0,1]. 'perm' (secondary, any structure): kill fractions permuted within each demo column among the functions observing that demo.
    In both, tic and class rows are permuted jointly among functions."""
    F = ph.F.copy(); obs = ph.obs; n, nd = F.shape
    if mode == "perm":
        for d in range(nd):
            ix = np.where(obs[:, d])[0]
            if len(ix) > 1: F[ix, d] = F[rng.permutation(ix), d]
    else:
        mu = np.nanmean(F, axis=0); X = np.where(obs, F, mu[None, :]); cov = np.cov(X, rowvar=False) + 1e-6 * np.eye(nd)
        Z = rng.multivariate_normal(mu, cov, size=n, method="cholesky" if False else "svd"); F = np.where(obs, np.clip(Z, 0, 1), np.nan)
    p = rng.permutation(n); return Pheno(ph.fids, F, ph.tic[p], ph.cls[p], ph.ninf)

def gap_choose(ph, Tmax, kmax, B=200, seed=1, mode="gauss"):
    """k = the k with the largest gap; p = share of null datasets whose own largest leave-one-out gap is at least as large (accounts for choosing k)"""
    rng = np.random.default_rng(seed); D = sym_dist(ph, Tmax); Z, labs = cut(D, kmax); ks = sorted(labs)
    Wobs = np.array([wk(D, labs[k]) for k in ks]); Wn = []
    for _ in range(B):
        nd = null_pheno(ph, rng, mode); Dn = sym_dist(nd, Tmax); _, ln = cut(Dn, kmax); Wn.append([wk(Dn, ln[k]) for k in ks])
    lw = np.log(np.maximum(np.array(Wn), 1e-12)); gap = lw.mean(0) - np.log(np.maximum(Wobs, 1e-12)); mx = float(gap.max()); i = int(np.argmax(gap)); choose = ks[i]
    tot = lw.sum(0); null_max = np.array([((tot - lw[b]) / (B - 1) - lw[b]).max() for b in range(B)])
    p = (1 + (null_max >= mx).sum()) / (1 + B)
    return dict(k=choose, labels=labs[choose], D=D, gap=gap, ks=ks, p=float(p), gap_at_k=mx)
def family(d): return d[0]
def jacc(a, b): return len(a & b) / max(1, len(a | b))
def stability(ph, Tmax, k, labels, demos, B=60, seed=2):
    """mean best-match Jaccard per cluster over bootstraps of demos (stratified by demo family) and of functions (80% subsamples)"""
    rng = np.random.default_rng(seed); n = ph.n; res = collections.defaultdict(list); fam = np.array([family(d) for d in demos])
    for b in range(B):
        if b % 2 == 0:
            idx = np.concatenate([rng.choice(np.where(fam == f)[0], (fam == f).sum(), replace=True) for f in np.unique(fam)])
            bp = Pheno(ph.fids, ph.F[:, idx], ph.tic, ph.cls, ph.ninf); fx = np.arange(n)
        else:
            fx = np.sort(rng.choice(n, int(0.8 * n), replace=False)); bp = ph.sub(fx)
        bl = fcluster(linkage(squareform(sym_dist(bp, Tmax), checks=False), "average"), k, "maxclust")
        for c in np.unique(labels):
            a = set(np.where(labels == c)[0]) & set(fx); best = max((jacc(a, set(fx[np.where(bl == q)[0]])) for q in np.unique(bl)), default=0); res[c].append(best)
    return {c: float(np.mean(v)) for c, v in res.items()}
