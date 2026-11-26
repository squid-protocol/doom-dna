"""Synthetic-data basis for the E15 thresholds (no screen data). Simulates two ports whose functions share latent role groups; port B's phenotype of a function is its group centroid
plus measurement noise, and a fraction `swap` of functions plays a different role in B. Reports AMI of the two ports' recovered groups over name-agree pairs, and rank recovery of the partner.
Usage: python simulate_thresholds.py   (e11 venv python)"""
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import adjusted_mutual_info_score
rng = np.random.default_rng(20261127)
def sim(n_funcs=140, k=12, n_demos=42, swap=0.2, noise=0.15, pairs=80, reps=200):
    amis, top1, top5, chance = [], [], [], []
    for _ in range(reps):
        cent = rng.beta(0.6, 0.9, size=(k, n_demos))                       # group centroids: kill fraction per demo
        reach = rng.random((n_funcs, n_demos)) < rng.uniform(0.3, 0.9, size=(n_funcs, 1))   # which demos observe the function
        g = rng.integers(0, k, n_funcs)
        def pheno(groups):
            x = np.clip(cent[groups] + rng.normal(0, noise, (n_funcs, n_demos)), 0, 1); x[~reach] = np.nan; return x
        A = pheno(g); gB = np.where(rng.random(n_funcs) < swap, rng.integers(0, k, n_funcs), g); B = pheno(gB)
        def dist(X, Y=None):
            Y = X if Y is None else Y; D = np.zeros((len(X), len(Y)))
            for i in range(len(X)):
                m = ~np.isnan(X[i]) & ~np.isnan(Y)
                with np.errstate(invalid="ignore", divide="ignore"): d = np.nansum(np.abs(X[i] - Y) * m, axis=1) / m.sum(1)
                d[m.sum(1) < 5] = 1.0; D[i] = d
            return D
        def groups(X):
            D = dist(X); D = (D + D.T) / 2; np.fill_diagonal(D, 0); return fcluster(linkage(squareform(D, checks=False), "average"), k, "maxclust")
        ga, gb = groups(A), groups(B); idx = rng.choice(n_funcs, pairs, replace=False)
        amis.append(adjusted_mutual_info_score(ga[idx], gb[idx]))
        D = dist(A[idx], B); order = np.argsort(D, axis=1); rank = np.array([np.where(order[i] == idx[i])[0][0] for i in range(pairs)])
        top1.append((rank == 0).mean()); top5.append((rank < 5).mean()); chance.append(5 / n_funcs)
    return np.mean(amis), np.mean(top1), np.mean(top5), np.mean(chance)
print("swap noise | AMI  top1  top5  (chance top5)")
for swap in (0.0, 0.2, 0.45, 0.7):
    for noise in (0.15, 0.3):
        a, t1, t5, c = sim(swap=swap, noise=noise, reps=60); print(f"{swap:4.2f} {noise:4.2f} | {a:.2f} {t1:.2f} {t5:.2f} ({c:.2f})")
