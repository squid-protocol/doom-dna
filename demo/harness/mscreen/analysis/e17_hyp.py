"""E17 descriptive hypotheses H-B2 (families), H-B3 (flagged pairs), H-B4 (SFS confidence AUC), H-B5 (E16 frozen scorer) and the frozen SFS confidence score. See E17_DIVERGENT_PORT_SCREENS.md v2."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from e17_core import *
TIER = {"exact": 6, "twin": 5, "xtwin": 4, "seed": 3, "ext1": 2, "ext2": 1, "ext3": 0}
# ---------------------------------------------------------------- SFS confidence score (E15 step 2: logistic on tier and log size ratio), frozen as JSON
def sfs_features(tier, size_ratio):
    return np.column_stack([pd.Series(tier).map(TIER).astype(float).to_numpy(), np.log(np.clip(np.asarray(size_ratio, float), 1.0, None))])
def sfs_score(tier, size_ratio, coef):
    """frozen confidence: intercept + b_tier * tier rank + b_logsize * log(size ratio); higher = more confident"""
    X = sfs_features(tier, size_ratio); return coef["intercept"] + X @ np.array([coef["b_tier"], coef["b_logsize"]])
def fit_sfs(out_json):
    """Fit the E15 step-2 score once, on the two C-family screens already analysed in E15 (managed-doom and prboom-plus pairs pooled; truth = behaviourally confirmed as in sfs_update_experiment.py), and write the frozen coefficients"""
    import csv, sfs_calibration as Cal
    from roles import load_port
    from sklearn.linear_model import LogisticRegression
    S = Cal.S; fc, fm, fp = Cal.funcs(S / "choc_v2/manifest.json"), Cal.funcs(S / "md_v2/manifest.json"), Cal.funcs(S / "pb_v2/manifest.json")
    A = load_port("chocolate-doom", S / "choc_phenotypes.sqlite"); Bm = load_port("managed-doom", S / "md_phenotypes.sqlite"); Pb = load_port("prboom-plus", S / "pb_phenotypes.sqlite"); demos = A.demos
    e12 = list(csv.DictReader(open(Path(__file__).resolve().parents[2] / "e14/pilot_pairs.csv"))); aC = Cal.adj(next((Cal.SCANS / "chocolate-doom").glob("*master.db"))); aM = Cal.adj(next((Cal.SCANS / "managed-doom").glob("*master.db"))); aP = Cal.adj(next((Cal.SCANS / "prboom-plus").glob("*master.db")))
    dfs = []
    for PY, fy, col, tcol, adjY, exact in ((Bm, fm, "md_name", "md_tier", aM, False), (Pb, fp, "pb_name", "pb_tier", aP, True)):
        tab, info = Cal.calibrate(A, PY, fc.set_index("fid"), fy.set_index("fid"), e12, col, tcol, "x", demos, aC, adjY, exact_names=exact); dfs.append(info["diag"])
    d = pd.concat(dfs); X = sfs_features(d.tier, d.size_ratio); m = LogisticRegression().fit(X, d.both.astype(int))
    coef = dict(intercept=float(m.intercept_[0]), b_tier=float(m.coef_[0][0]), b_logsize=float(m.coef_[0][1]), n_pairs=int(len(d)), n_confirmed=int(d.both.sum()), source="E15 managed-doom + prboom-plus pairs (E15_SFS_UPDATE_STEP1 step 2 model, pooled)")
    Path(out_json).write_text(json.dumps(coef, indent=1)); return coef
# ---------------------------------------------------------------- H-B4
def hb4(e12, fM, fC, mats, pools, ctx_lines, coef, nq_thr, B=2000):
    """E12 pairs Mocha -> chocolate-doom with both functions usable (screened by unique exact names). Confirmation = D <= the 5th percentile of random cross-port D AND the clean call profile as close as the 5th percentile of
    random cross-port raw-L1 N0 (a divergent port never reproduces counts exactly, so 'same call-profile class' is read as 'inside the random 5th percentile'). AUC of the frozen SFS confidence overall and within tier group, function-clustered CI."""
    Dm, N0, rows, pool = mats["D"], mats["N0"], mats["rows"], pools
    cn = {n: f for f, n in zip(fC.fid, fC.name) if (fC.name == n).sum() == 1}; mn = {n: f for f, n in zip(fM.fid, fM.name) if (fM.name == n).sum() == 1}
    ri = {int(f): i for i, f in enumerate(rows)}; pi = {int(f): j for j, f in enumerate(pool)}; recs = []
    for r in e12.itertuples():
        c, m = cn.get(r.ref_name), mn.get(r.port_name)
        if c is None or m is None or int(m) not in ri or int(c) not in pi: continue
        i, j = ri[int(m)], pi[int(c)]; lm, lc = ctx_lines[0].get(int(m), 1), ctx_lines[1].get(int(c), 1); recs.append(dict(cfid=int(c), mfid=int(m), tier=r.tier, size_ratio=max(lm, lc) / max(1, min(lm, lc)), D=Dm[i, j], N0=N0[i, j]))
    d = pd.DataFrame(recs)
    if len(d) == 0: return dict(n=0, note="no usable E12 pairs"), d
    d["conf_both"] = (d.D <= nq_thr["D05"]) & (d.N0 <= nq_thr["N005"]); d["conf_D"] = d.D <= nq_thr["D05"]; d["score"] = sfs_score(d.tier, d.size_ratio, coef); d["tiercode"] = d.tier.map(TIER).astype(float)
    out = dict(n=int(len(d)), n_confirmed=int(d.conf_both.sum()), thresholds=nq_thr, power_ok=bool(len(d) >= 40)); groups = {"all": d.tier.notna(), "twin tiers (exact, twin, xtwin, seed)": d.tier.isin(TWIN), "extension tiers (ext1-3)": d.tier.str.startswith("ext")}
    for lab, mask in groups.items():
        g = d[mask]; res = dict(n=int(len(g)), confirmed=int(g.conf_both.sum()), power_ok=bool(len(g) >= 40))
        for nm, sc in (("sfs_score", g.score), ("tier_only", g.tiercode), ("size_only", -np.log(g.size_ratio.clip(lower=1.0)))):
            a = auc(sc, g.conf_both); lo, hi = cluster_auc_ci(sc.to_numpy(), g.conf_both.to_numpy(), g.cfid.to_numpy(), B=B) if a == a else (float("nan"),) * 2; res[nm] = dict(auc=a, lo=lo, hi=hi)
        res["auc_D_only_confirmation"] = auc(g.score, g.conf_D) if len(g) else float("nan"); out[lab] = res
    return out, d
# ---------------------------------------------------------------- H-B3
def hb3(pairs_df, Dm, rows, pool, thr25, seed=5, n_audit=40):
    """strict name-agree pairs whose D is at least the 25th percentile of random cross-port D (they look as unlike as an ordinary random pair): the list, and a seeded sample of up to 40 for the blind audit"""
    ri = {int(f): i for i, f in enumerate(rows)}; pi = {int(f): j for j, f in enumerate(pool)}; recs = []
    for r in pairs_df[pairs_df.strict].itertuples():
        if int(r.mfid) in ri and int(r.cfid) in pi: recs.append(dict(mocha=r.mname, chocolate=r.cname, tier=r.tier, D=float(Dm[ri[int(r.mfid)], pi[int(r.cfid)]])))
    d = pd.DataFrame(recs, columns=["mocha", "chocolate", "tier", "D"]); fl = d[d.D >= thr25].copy() if len(d) else d
    aud = fl.sample(min(n_audit, len(fl)), random_state=seed) if len(fl) else fl
    return dict(threshold=float(thr25), strict_usable=int(len(d)), flagged=int(len(fl)), share=float(len(fl) / len(d)) if len(d) else float("nan"), audit_n=int(len(aud))), fl.sort_values("D", ascending=False), aud
# ---------------------------------------------------------------- H-B2
def lesion_table_port(P):
    """per-lesion effect table (as lesion_classes.lesion_table, from an in-memory port): kill fraction, family-of-demo profile, class mix of kills, median log first tic"""
    from roles import CLASS_BITS, CLASSES
    FAMS = "scbvxpfg"; r = P.res[P.res.outcome.isin(["killed", "same"])]; d = pd.DataFrame(dict(lesion=r.lesion.to_numpy(), demo=r.demo.to_numpy(), k=(r.outcome == "killed").astype(int).to_numpy(), tic=r.tic.fillna(0).to_numpy(), mask=r["mask"].fillna(-1).astype(int).to_numpy()))
    d["fam"] = d.demo.str[0]; d["lt"] = np.log10(d.tic + 1); g = d.groupby("lesion"); T = pd.DataFrame({"n_exec": g.size(), "n_kill": g.k.sum()}); T["kill_frac"] = T.n_kill / T.n_exec
    fam = d.groupby(["lesion", "fam"]).k.mean().unstack().reindex(columns=list(FAMS)).fillna(0.0); fam.columns = [f"fam_{c}" for c in fam.columns]
    kk = d[d.k == 1]; cls = np.zeros((len(kk), len(CLASSES)))
    for c, name in enumerate(CLASSES):
        b = CLASS_BITS[name]; cls[:, c] = ((kk["mask"].to_numpy() & b) != 0) if name != "time" else (kk["mask"].to_numpy() <= 0) | ((kk["mask"].to_numpy() & b) != 0)
    C = pd.DataFrame(cls, index=kk.lesion.to_numpy(), columns=[f"cls_{c}" for c in CLASSES]).groupby(level=0).mean(); lt = kk.groupby("lesion").lt.median().rename("med_log_tic")
    meta = P.res.drop_duplicates("lesion").set_index("lesion")[["fid", "fn", "kind"]]; return meta.join(T, how="inner").join(fam).join(C).join(lt)
def hb2(M, C, pairs_df, null_reps=30, seed=6):
    """The E15 lesion-effect families are the k-means classes of chocolate-doom lesions (lesion_classes.classify, seed 0, reproducing E15). For each family, over the host functions that have a name-agree Mocha counterpart,
    the chocolate-doom family centroid versus the Mocha lesion-effect profile of those counterparts (RMS of z-scored differences, the E15 cross-port metric; 0.4 = the E15 cutoff), next to a shuffled-demo null for Mocha."""
    import lesion_classes as LC
    Tc = lesion_table_port(C); det, cols, k, sil = LC.classify(Tc); Tm = lesion_table_port(M); dm = Tm[(Tm.n_kill >= 1) & (Tm.n_exec >= 3)]
    cols = [c for c in cols if c in dm.columns]; both = pd.concat([det[cols], dm[cols]]); mu, sd = both.mean(), both.std().replace(0, 1)
    c2m = dict(zip(pairs_df.cfid, pairs_df.mfid)); out = []
    def profile_dist(table_det, hosts_m, centroid):
        g = table_det[table_det.fid.isin(hosts_m)]
        if len(g) < 5: return float("nan"), len(g)
        z = ((g[cols].mean() - centroid) / sd).fillna(0.0); return float(np.sqrt((z ** 2).mean())), len(g)
    rng = np.random.default_rng(seed); nulls = []
    for _ in range(null_reps):
        Ms = Port(M.name, M.lesions, M.res.assign(demo=rng.permutation(M.res.demo.to_numpy())), M.reach, M.demos); Ts = lesion_table_port(Ms); nulls.append(Ts[(Ts.n_kill >= 1) & (Ts.n_exec >= 3)])
    for c in sorted(det.cls.unique()):
        g = det[det.cls == c]; hosts_c = set(g.fid) & set(c2m); hosts_m = {c2m[h] for h in hosts_c}
        if len(hosts_c) == 0: out.append(dict(family=int(c), choc_lesions=len(g), matched_hosts=0, dist=float("nan"), null_mean=float("nan"), null_p05=float("nan"))); continue
        cen = det[(det.cls == c) & det.fid.isin(hosts_c)][cols].mean(); d, n = profile_dist(dm, hosts_m, cen); nd = np.array([profile_dist(t, hosts_m, cen)[0] for t in nulls])
        out.append(dict(family=int(c), choc_lesions=int(len(g)), matched_hosts=len(hosts_c), mocha_lesions=int(n), dist=d, within_0_4=bool(d <= 0.4) if d == d else None, null_mean=float(np.nanmean(nd)), null_p05=float(np.nanpercentile(nd, 5)) if np.isfinite(nd).any() else float("nan")))
    return dict(k=int(k), silhouette=float(sil), families=out, e15_expected_k=11)
# ---------------------------------------------------------------- H-B5
def hb5(M, C, fM_path, A_phC, fC, ua, split, outdir, seed=7):
    """E16 diagnosis, frozen scorer, chocolate-doom dictionary, Mocha lesions as queries (test-half targets, >= 3 killed demos), counterparts = name-agree without the identical-profile condition. Exploratory."""
    import run_test, prep as P
    def counterparts(A, phA, fa, B, phB, fb, ua_):
        kc = name_keys(fa.reset_index(), True); km = name_keys(fb.reset_index(), False); us = set(int(x) for x in ua_)
        return {km[k]: kc[k] for k in km if k in kc and kc[k] in us}
    run_test.counterparts = counterparts; run_test.load_port = lambda label, path: M      # run() loads the query port by path: hand it the in-memory Mocha port
    SA = P.symptoms(C); rows, res, a1, dropped = run_test.run("mochadoom", None, fM_path, C, A_phC, fC.set_index("fid"), ua, SA, run_test.FZ["tmax"], split, Path(outdir), np.random.default_rng(seed))
    return rows, res, a1, dropped
