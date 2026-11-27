"""Lesion-level phenotype classes (Brenner-style): classify every lesion by WHAT it breaks (the state that diverges first, how severe, in which kinds of demos), then work backward to the functions involved,
build a function network from shared classes, and compare with the E15 function groups and with the 16 call-graph subsystems of the article's subsystem map. Exploratory (post hoc, requested by the owner after the registered run).
Usage: python lesion_classes.py <out_dir>"""
import json, re, sys, collections
from pathlib import Path
import numpy as np, pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score, silhouette_score
sys.path.insert(0, str(Path(__file__).resolve().parent))
from roles import CLASS_BITS, CLASSES
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); S = W / "screen"
FAMS = "scbvxpfg"
def lesion_table(port_db):
    import sqlite3
    c = sqlite3.connect(f"file:{port_db}?mode=ro", uri=True); r = pd.read_sql("select lesion, demo, outcome, tic, mask from results", c); les = pd.read_sql("select id, kind, fn, fid, file from lesions", c)
    d = r[r.outcome.isin(["killed", "same"])].copy(); d["k"] = (d.outcome == "killed").astype(int); d["fam"] = d.demo.str[0]; d["lt"] = np.log10(d.tic.fillna(0) + 1)
    g = d.groupby("lesion"); T = pd.DataFrame({"n_exec": g.size(), "n_kill": g.k.sum()}); T["kill_frac"] = T.n_kill / T.n_exec
    fam = d.groupby(["lesion", "fam"]).k.mean().unstack().reindex(columns=list(FAMS)).fillna(0.0); fam.columns = [f"fam_{c}" for c in fam.columns]
    kk = d[d.k == 1]; cls = np.zeros((len(kk), len(CLASSES)))
    for i, m in enumerate(kk["mask"].fillna(-1).astype(int)):
        bits = [j for j, c in enumerate(CLASSES) if (m & CLASS_BITS[c])] if m > 0 else [CLASSES.index("time")]
        for j in bits: cls[i, j] = 1
    C = pd.DataFrame(cls, index=kk.lesion.to_numpy(), columns=[f"cls_{c}" for c in CLASSES]).groupby(level=0).mean(); lt = kk.groupby("lesion").lt.median().rename("med_log_tic")
    bad = r[r.outcome.isin(["crash", "hang"])].groupby("lesion").size().rename("n_bad")
    T = T.join(fam).join(C).join(lt).join(bad).fillna({"n_bad": 0}); T = les.set_index("id").join(T, how="inner"); return T
def classify(T, kmin=4, kmax=14, seed=0):
    det = T[(T.n_kill >= 1) & (T.n_exec >= 3)].copy(); cols = [c for c in det.columns if c.startswith(("cls_", "fam_"))] + ["kill_frac", "med_log_tic"]
    X = det[cols].fillna(0.0).to_numpy(float); X = (X - X.mean(0)) / np.where(X.std(0) > 1e-9, X.std(0), 1); best = None
    rng = np.random.default_rng(seed); sub = rng.choice(len(X), min(2500, len(X)), replace=False)
    for k in range(kmin, kmax + 1):
        km = KMeans(k, n_init=5, random_state=seed).fit(X); sc = silhouette_score(X[sub], km.labels_[sub])
        if best is None or sc > best[0]: best = (sc, k, km.labels_)
    det["cls"] = best[2]; return det, cols, best[1], best[0]
def describe(det, cols, name):
    out = []
    for c in sorted(det.cls.unique()):
        g = det[det.cls == c]; st = {k[4:]: g[k].mean() for k in g.columns if k.startswith("cls_")}; fm = {k[4:]: g[k].mean() for k in g.columns if k.startswith("fam_")}
        top = g.fn.value_counts().head(6); share = (top / g.fn.map(det.fn.value_counts()).reindex(top.index).to_numpy() if False else None)
        out.append(dict(cls=int(c), n=len(g), main_state=max(st, key=st.get), state=" ".join(f"{k} {v:.2f}" for k, v in sorted(st.items(), key=lambda kv: -kv[1])[:3]), kill=round(g.kill_frac.mean(), 2), logtic=round(g.med_log_tic.mean(), 2),
                        kinds=", ".join(f"{k} {v:.0%}" for k, v in g.kind.value_counts(normalize=True).head(3).items()), functions=", ".join(f"{k}({v})" for k, v in top.items())))
    return pd.DataFrame(out)
def subsystems(port):
    d = json.load(open(W.parent / "../projects/doom-dna-worktrees/gene-view/article/subsystem_map_data.json")) if False else json.load(open("/srv/storage_16tb/projects/doom-dna-worktrees/gene-view/article/subsystem_map_data.json"))
    p = d["ports"].get(port); names = d["subsystems"]
    if not p: return {}, names
    m = {}
    for i, track in enumerate(p["tracks"]):
        for e in track: m.setdefault(e[0], i)
    return m, names
def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); md = ["# Lesion-level phenotype classes (Brenner-style), exploratory\n"]; res = {}
    for port, db in (("chocolate-doom", "choc"), ("managed-doom", "md")):
        T = lesion_table(S / f"{db}_phenotypes.sqlite"); det, cols, k, sil = classify(T); res[port] = (T, det, cols)
        silent = int(((T.n_kill == 0) & (T.n_exec >= 3)).sum()); few = int((T.n_exec < 3).sum())
        md += [f"## {port}\n", f"{len(T)} lesions with at least one clean run; {len(det)} change the game on at least one demo (and ran on >= 3) and are classified; {silent} ran on >= 3 demos and never changed anything (silent class); {few} ran on fewer than 3 demos. Best k = {k} (silhouette {sil:.2f}).\n"]
        D = describe(det, cols, port); md += ["| class | lesions | what breaks first | kill share | severity (log tic) | lesion kinds | functions with the most lesions in the class |\n|---|---|---|---|---|---|---|"] + [f"| {r.cls} | {r.n} | {r.state} | {r.kill} | {r.logtic} | {r.kinds} | {r.functions} |" for r in D.itertuples()] + [""]
        # back-work: function x class distribution, function communities
        nf = det.groupby("fn").size(); keep = nf[nf >= 8].index; M = pd.crosstab(det[det.fn.isin(keep)].fn, det[det.fn.isin(keep)].cls); P = M.div(M.sum(1), axis=0)
        Z = linkage(P.to_numpy(), "average", metric="cosine"); comm = fcluster(Z, k, "maxclust"); fc = pd.Series(comm, index=P.index)
        smap, snames = subsystems(port); inter = [f for f in P.index if f in smap]
        if inter:
            lab_s = [smap[f] for f in inter]; lab_c = [fc[f] for f in inter]; lab_dom = [int(P.loc[f].idxmax()) for f in inter]
            md += [f"**Back-working to functions:** {len(P)} functions have >= 8 classified lesions. Clustering functions by the mix of lesion classes they contain gives {k} function communities. Against the article's 16 call-graph subsystems ({len(inter)} of these functions are on the map): ARI {adjusted_rand_score(lab_s, lab_c):.2f}, AMI {adjusted_mutual_info_score(lab_s, lab_c):.2f}; by dominant class: ARI {adjusted_rand_score(lab_s, lab_dom):.2f}.\n"]
            ct = pd.crosstab(pd.Series([snames[smap[f]] for f in inter], name="subsystem"), pd.Series([fc[f] for f in inter], name="community")); md += ["Subsystem by function community (counts):\n", ct.to_markdown(), ""]
        res[port] = (T, det, cols, fc, P, smap)
    # cross-port: match lesion classes by centroid (state mix, kill share, severity, family profile)
    cA, cB = res["chocolate-doom"][1], res["managed-doom"][1]; cols = [c for c in res["chocolate-doom"][2] if c in cB.columns]
    A = cA.groupby("cls")[cols].mean(); B = cB.groupby("cls")[cols].mean(); mu = pd.concat([cA[cols], cB[cols]]).mean(); sd = pd.concat([cA[cols], cB[cols]]).std().replace(0, 1); An = ((A - mu) / sd).fillna(0).to_numpy(); Bn = ((B - mu) / sd).fillna(0).to_numpy()
    Dm = np.sqrt(((An[:, None, :] - Bn[None, :, :]) ** 2).mean(2)); r, c = linear_sum_assignment(Dm)
    md += ["## Do the lesion classes recur across ports?\n", "Chocolate-doom class matched to its closest managed-doom class (one-to-one, by centroid distance; lower is closer, 0.5 is already close):\n", "| chocolate class | managed class | distance | chocolate: main state, kill share | managed: main state, kill share |\n|---|---|---|---|---|"]
    Da, Db = describe(cA, cols, "a").set_index("cls"), describe(cB, cols, "b").set_index("cls")
    for i, j in zip(r, c): md.append(f"| {A.index[i]} | {B.index[j]} | {Dm[i, j]:.2f} | {Da.loc[A.index[i]].main_state}, {Da.loc[A.index[i]].kill} | {Db.loc[B.index[j]].main_state}, {Db.loc[B.index[j]].kill} |")
    (out / "E15_LESION_CLASSES.md").write_text("\n".join(md)); print("\n".join(md)[:6000])
if __name__ == "__main__": main()
