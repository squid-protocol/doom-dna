"""E16 scorer and baselines (registered in preregistration/E16_SYMPTOM_DIAGNOSIS.md v2). Pure functions over the dense symptom arrays from prep.py."""
import itertools, numpy as np
POP = np.array([bin(i).count("1") for i in range(32)], np.float32)
def components(q, Dct, tmax):
    """per dictionary lesion: (a) failing-set Jaccard, (b) class-set agreement on mutually killed demos, (c) tic closeness on mutually killed demos, plus evaluated-demo counts and kill counts"""
    E = ~q["M"][None, :] & ~Dct["M"]; nE = E.sum(1); Kq = q["K"][None, :] & E; KL = Dct["K"] & E
    inter = (Kq & KL).sum(1); union = (Kq | KL).sum(1); a = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
    B = Kq & KL; nB = B.sum(1); pa = q["C"][None, :]; pb = Dct["C"]; andc = POP[pa & pb]; orc = POP[pa | pb]; jac = np.where(orc > 0, andc / np.maximum(orc, 1), 1.0)   # two empty class sets agree
    b = np.where(nB > 0, (jac * B).sum(1) / np.maximum(nB, 1), 0.0); tc = 1.0 - np.minimum(1.0, np.abs(q["T"][None, :] - Dct["T"]) / tmax); c = np.where(nB > 0, (tc * B).sum(1) / np.maximum(nB, 1), 0.0)
    return a.astype(np.float32), b.astype(np.float32), c.astype(np.float32), nE, KL.sum(1), inter
def aggregate(les_score, groups, how):
    """groups: list of index arrays (lesions of each function, in candidate order); returns the function scores"""
    out = np.zeros(len(groups), np.float32)
    for i, g in enumerate(groups):
        v = les_score[g]
        if len(v) == 0: continue
        if how == "max": out[i] = v.max()
        elif how == "top3": out[i] = np.sort(v)[-3:].mean()
        elif how == "maxnorm": out[i] = v.max() / np.sqrt(len(v))
    return out
def rank_of(scores, truth_idx):
    """pessimistic rank: the number of candidates scoring at least as high as the truth (itself included)"""
    return int((scores >= scores[truth_idx]).sum())
def ochiai(cov, F, P):
    ef = (cov & F[None, :]).sum(1); ep = (cov & P[None, :]).sum(1); den = np.sqrt(max(F.sum(), 1) * (ef + ep)); return np.where(den > 0, ef / np.maximum(den, 1e-9), 0.0)
def tarantula(cov, F, P):
    ef = (cov & F[None, :]).sum(1) / max(F.sum(), 1); ep = (cov & P[None, :]).sum(1) / max(P.sum(), 1) if P.sum() else np.zeros(len(cov)); den = ef + ep; return np.where(den > 0, ef / np.maximum(den, 1e-9), 0.0)
def calls(R, F, P):
    L = np.log1p(R); return L[:, F].mean(1) - (L[:, P].mean(1) if P.sum() else 0.0)
def metrics(ranks, weights=None):
    r = np.asarray(ranks, float); w = np.ones(len(r)) if weights is None else np.asarray(weights, float); w = w / w.sum()
    return dict(n=len(r), top1=float((w * (r <= 1)).sum()), top3=float((w * (r <= 3)).sum()), top5=float((w * (r <= 5)).sum()), top10=float((w * (r <= 10)).sum()), mrr=float((w / r).sum()))
