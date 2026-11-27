"""E17 core (preregistration/E17_DIVERGENT_PORT_SCREENS.md, v2 governs): distances, N0 variants, ranks, cluster bootstrap, pair tables, clean-digest demo matching.
Pure functions; nothing here opens a store unless a caller passes a Port. Reuses the E15 modules (roles.py, tests.py) and the E16 data layer (diagnosis/prep.py) unchanged."""
import difflib, math, os, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import rankdata
HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "diagnosis", HERE.parents[1]): sys.path.insert(0, str(p))
import roles
from roles import Port, phenotype, MIN_CO, MIN_INF, W_L1, W_TIC, W_CLS
from tests import usable, tmax
import prep
TWIN = {"exact", "twin", "xtwin", "seed"}          # the E15 'strong' tiers (STRONG in sfs_calibration.py); see E17_RESULTS deviations
TWIN_NARROW = {"exact", "twin", "xtwin"}
EPS = 1e-12
KEEP_WIDE = [1] + list(range(4, 19))               # compare_digests.KEEP with E13_WIDE: leveltime, x..ammo3, world and sector fingerprints, cards; the gameplay RNG index (2) excluded, as in make_clean_digests.py

# ---------------------------------------------------------------- names and pairs
def name_keys(f, is_c):
    """unique name keys (after C prefix stripping for the C port) -> fid; generic and short names excluded, as in E15"""
    keys = [prep.PREFIX.sub("", n) if is_c else n for n in f.name]; cnt = pd.Series(keys).value_counts()
    return {k: int(fid) for k, fid in zip(keys, f.fid) if cnt[k] == 1 and len(k) >= 4 and k.lower() not in prep.GENERIC}
def fclass(ph, fid):
    """usable / hot / inert / '<4' (fewer than 4 informative lesions, or no result at all); '<4' takes precedence as in the E15 eligibility rule"""
    w = np.where(ph.fids == fid)[0]
    if len(w) == 0: return "<4"
    i = w[0]
    if ph.ninf[i] < MIN_INF: return "<4"
    return "hot" if ph.hot[i] else ("inert" if ph.inert[i] else "usable")
CLASSES4 = ["usable", "hot", "inert", "<4"]
def make_pairs(fM, fC, phM, phC, e12, arb=None):
    """name-agree pairs (unique in both ports) with their E12 tier for that very pair and the text-arbiter flag; classes of both sides"""
    kc, km = name_keys(fC, True), name_keys(fM, False); cname = dict(zip(fC.fid, fC.name)); mname = dict(zip(fM.fid, fM.name)); tier = {}
    for r in (e12.itertuples() if e12 is not None and len(e12) else []): tier[(r.ref_name, r.port_name)] = r.tier
    arb = arb or set(); rows = []
    for k in sorted(set(kc) & set(km)):
        c, m = kc[k], km[k]; t = tier.get((cname[c], mname[m]), ""); a = (cname[c], mname[m]) in arb
        rows.append(dict(key=k, mfid=m, cfid=c, cname=cname[c], mname=mname[m], tier=t, arbiter=a, strict=bool(t in TWIN or a), strict_narrow=bool(t in TWIN_NARROW or a), strict_ext=bool(t != "" or a), cls_m=fclass(phM, m), cls_c=fclass(phC, c)))
    return pd.DataFrame(rows, columns=["key", "mfid", "cfid", "cname", "mname", "tier", "arbiter", "strict", "strict_narrow", "strict_ext", "cls_m", "cls_c"])
def transition(pairs):
    t = pd.crosstab(pairs.cls_m, pairs.cls_c).reindex(index=CLASSES4, columns=CLASSES4, fill_value=0); t.index.name = "Mocha \\ chocolate"; return t

# ---------------------------------------------------------------- phenotype distance and components
def pdist(phQ, qf, phP, pf, T):
    """(K co-observed demos, L1, tic, JS) for query fids x pool fids; fids with no phenotype row get K=0 (missing)"""
    qf, pf = np.asarray(qf), np.asarray(pf); n, m = len(qf), len(pf); K = np.zeros((n, m), int); L = np.ones((n, m)); Tt = np.ones((n, m)); J = np.zeros((n, m))
    qi = {int(f): i for i, f in enumerate(phQ.fids)}; pi = {int(f): i for i, f in enumerate(phP.fids)}
    rq = [i for i, f in enumerate(qf) if int(f) in qi]; rp = [j for j, f in enumerate(pf) if int(f) in pi]
    if not rq or not rp: return K, L, Tt, J
    A = phQ.sub(np.array([qi[int(qf[i])] for i in rq])); B = phP.sub(np.array([pi[int(pf[j])] for j in rp])); a, b = A.n, B.n
    k_ = np.zeros((a, b), int); l_ = np.ones((a, b)); t_ = np.ones((a, b)); j_ = np.zeros((a, b)); oa, ob = A.obs, B.obs; Fa, Fb = np.nan_to_num(A.F), np.nan_to_num(B.F)
    for i in range(a):
        co = oa[i][None, :] & ob; k = co.sum(1); k_[i] = k; l_[i] = (np.abs(Fa[i][None, :] - Fb) * co).sum(1) / np.maximum(k, 1)
        with np.errstate(invalid="ignore"):
            t_[i] = roles._nanrule(np.full(b, A.tic[i]), B.tic, np.abs(A.tic[i] - B.tic) / T)
            pa = np.broadcast_to(A.cls[i], B.cls.shape); js = np.nan_to_num(jensenshannon(np.nan_to_num(pa, nan=0.2), np.nan_to_num(B.cls, nan=0.2), base=2, axis=1))
            j_[i] = np.where(np.isnan(A.cls[i][0]) | np.isnan(B.cls[:, 0]), roles._nanrule(np.full(b, A.cls[i][0]), B.cls[:, 0], 0.0), js)
    ix = np.ix_(rq, rp); K[ix], L[ix], Tt[ix], J[ix] = k_, l_, t_, j_; return K, L, Tt, J
def combine(parts, which="D"):
    """E15 distance (0.6 kill fraction + 0.2 first tic + 0.2 class), or one component alone (ablation); fewer than 5 co-observed demos -> maximum distance 1 (missing-D imputation)"""
    K, L, Tt, J = parts; v = {"D": W_L1 * L + W_TIC * Tt + W_CLS * J, "kill": L, "tic": Tt, "class": J}[which]; return np.where(K >= MIN_CO, v, 1.0)

# ---------------------------------------------------------------- N0: clean entry-count profiles
def entries_matrix(P, fids, demos):
    di = {d: i for i, d in enumerate(demos)}; fi = {int(f): i for i, f in enumerate(fids)}; M = np.zeros((len(fids), len(demos))); r = P.reach
    for f, d, n in zip(r.fid, r.demo, r.entries):
        if int(f) in fi and d in di: M[fi[int(f)], di[d]] = n
    return M
def n0_dists(Lq, Lp, cols):
    """four N0 distances (lower = closer) on log1p counts over the demo columns: raw L1 (mean over demos), cosine and Spearman over co-observed demos (both entered; >= 3 needed, else the maximum 2), binary reach Jaccard"""
    a, b = Lq[:, cols], Lp[:, cols]; n, m = len(a), len(b); out = {}; oa, ob = a > 0, b > 0
    out["l1"] = np.abs(a[:, None, :] - b[None, :, :]).mean(2) if a.shape[1] else np.ones((n, m))
    inter = (oa[:, None, :] & ob[None, :, :]).sum(2); uni = (oa[:, None, :] | ob[None, :, :]).sum(2); out["jaccard"] = np.where(uni > 0, 1 - inter / np.maximum(uni, 1), 1.0)
    cos = np.full((n, m), 2.0); sp = np.full((n, m), 2.0)
    for i in range(n):
        co = oa[i][None, :] & ob; k = co.sum(1)
        for j in np.where(k >= 3)[0]:
            x, y = a[i][co[j]], b[j][co[j]]; den = np.linalg.norm(x) * np.linalg.norm(y); cos[i, j] = 1 - (x @ y) / den if den > 0 else 1.0
            sx, sy = rankdata(x), rankdata(y); sx, sy = sx - sx.mean(), sy - sy.mean(); d = math.sqrt((sx ** 2).sum() * (sy ** 2).sum()); sp[i, j] = 1 - (sx @ sy) / d if d > 0 else 1.0
    out["cosine"], out["spearman"] = cos, sp; return out
N0_KINDS = ["l1", "cosine", "spearman", "jaccard"]

# ---------------------------------------------------------------- ranks, metrics, bootstrap
def prank(S, tgt):
    """pessimistic rank: candidates at least as close as the partner, itself and ties included"""
    t = S[np.arange(len(tgt)), tgt][:, None]; return (S <= t + EPS).sum(1)
def tiesize(S, tgt):
    t = S[np.arange(len(tgt)), tgt][:, None]; return (np.abs(S - t) <= EPS).sum(1)
def combined_rank_mean(*mats): return sum(rankdata(m, axis=1) for m in mats) / len(mats)
def metrics(rk, ties=None):
    rk = np.asarray(rk, float); out = dict(n=int(len(rk)), top1=float((rk <= 1).mean()) if len(rk) else float("nan"), top3=float((rk <= 3).mean()) if len(rk) else float("nan"), top5=float((rk <= 5).mean()) if len(rk) else float("nan"), mrr=float((1 / rk).mean()) if len(rk) else float("nan"))
    if ties is not None and len(rk): out["mean_tie"] = float(np.mean(ties))
    return out
def cluster_boot(a, b, cl, B=10000, seed=1):
    """paired difference of means (a - b) with a cluster bootstrap over clusters (chocolate-doom functions); returns point, 2.5%, 97.5%"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) == 0: return float("nan"), float("nan"), float("nan")
    u, inv = np.unique(cl, return_inverse=True); nc = np.bincount(inv).astype(float); sd = np.bincount(inv, weights=a - b); rng = np.random.default_rng(seed); idx = rng.integers(0, len(u), (B, len(u)))
    d = sd[idx].sum(1) / nc[idx].sum(1); return float((a - b).mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
def cluster_ci(a, cl, B=10000, seed=2):
    a = np.asarray(a, float); u, inv = np.unique(cl, return_inverse=True); nc = np.bincount(inv).astype(float); sd = np.bincount(inv, weights=a); rng = np.random.default_rng(seed); idx = rng.integers(0, len(u), (B, len(u)))
    d = sd[idx].sum(1) / nc[idx].sum(1); return float(a.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
def auc(score, y):
    """Mann-Whitney AUC with ties counted half; nan when one class is empty"""
    score, y = np.asarray(score, float), np.asarray(y, bool)
    if y.all() or (~y).all() or len(y) == 0: return float("nan")
    r = rankdata(score); n1, n0 = y.sum(), (~y).sum(); return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
def cluster_auc_ci(score, y, cl, B=2000, seed=3):
    """function-clustered bootstrap interval of the AUC (resamples with one class only are skipped)"""
    score, y, cl = np.asarray(score, float), np.asarray(y, bool), np.asarray(cl); u = np.unique(cl); g = {c: np.where(cl == c)[0] for c in u}; rng = np.random.default_rng(seed); v = []
    for _ in range(B):
        ix = np.concatenate([g[c] for c in rng.choice(u, len(u))]); x = auc(score[ix], y[ix])
        if x == x: v.append(x)
    return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) > 20 else (float("nan"), float("nan"))

# ---------------------------------------------------------------- baselines
def name_similarity(qnames, pnames):
    """name-only baseline score matrix (lower = closer): 1 - difflib ratio on lower-cased names without the C prefix"""
    qs = [n.lower() for n in qnames]; ps = [prep.PREFIX.sub("", n).lower() for n in pnames]; M = np.ones((len(qs), len(ps)))
    for i, a in enumerate(qs):
        for j, b in enumerate(ps): M[i, j] = 1 - difflib.SequenceMatcher(None, a, b).ratio()
    return M
def e12_matrix(qfids, pfids, proposal):
    """E12 structural matcher as a ranker: the one-to-one partner it proposes scores 0, every other candidate ties at 1 (pessimistic ranks)"""
    pi = {int(f): j for j, f in enumerate(pfids)}; M = np.ones((len(qfids), len(pfids)))
    for i, f in enumerate(qfids):
        c = proposal.get(int(f));
        if c is not None and int(c) in pi: M[i, pi[int(c)]] = 0.0
    return M
def strata_codes(vals, q=3): return pd.qcut(pd.Series(vals).rank(method="first"), q, labels=False, duplicates="drop").to_numpy()
def shuffled_partner_ranks(S, tgt, strata, n_shuf=200, seed=4):
    """ranks of partners shuffled among pairs within strata (function size x reach of the chocolate partner); returns per-shuffle top-5 shares"""
    rng = np.random.default_rng(seed); out = []; groups = [np.where(strata == s)[0] for s in np.unique(strata)]
    for _ in range(n_shuf):
        t = tgt.copy()
        for g in groups: t[g] = tgt[rng.permutation(g)]
        out.append(float((prank(S, t) <= 5).mean()))
    return np.array(out)

# ---------------------------------------------------------------- clean digests: demos on which the two ports agree
def digest_agreement(mocha_dir, choc_dir, demos, min_len=200):
    """first divergence of the Mocha clean digest from the chocolate-doom one per demo (same rule as make_clean_digests.py: common columns, RNG index excluded, dead-angle ignored).
    Returns {demo: (identical?, first divergence tic or None, field)}"""
    import compare_digests as C
    out = {}
    for d in demos:
        a, b = C.load(Path(choc_dir) / f"{d}.txt"), C.load(Path(mocha_dir) / f"{d}.txt")
        if not a or not b: out[d] = (False, -1, "missing"); continue
        r = C.first_divergence(a, b, KEEP_WIDE, True); out[d] = (bool(r is None and len(b) > min_len), None if r is None else int(r[0]), "" if r is None else r[1])
    return out
