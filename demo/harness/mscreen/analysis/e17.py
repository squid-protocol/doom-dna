"""E17 analysis (Mocha Doom lesion screen), exactly the v2 section of preregistration/E17_DIVERGENT_PORT_SCREENS.md. Mocha is the sole confirmatory port; queries run Mocha -> chocolate-doom over the 140 usable chocolate-doom candidates.
Usage (e11 venv python, niced):
  nice -n 10 python analysis/e17.py <mocha_store.sqlite> <mocha_manifest.json> <mocha_clean_dir> <out_dir> [--B 10000] [--pairs csv] [--arbiter csv] [--sfs json] [--skip hb2,hb5]
Writes <out_dir>/E17_RESULTS.md and E17_RESULTS.json (+ flagged / unrankable / demo-agreement CSVs). Nothing here is run on a real store by the tests: they use synthetic stores only."""
import argparse, json, sys, types
from pathlib import Path
import numpy as np, pandas as pd
from e17_core import *
import e17_hyp as H
from tests import pc1
RAND_N = 20000
class Ctx:
    """everything the analysis needs, so tests can hand in synthetic stores: M (Mocha port), C (chocolate-doom), MD (managed-doom or None), fM/fC/fMD (fid, name, file, lines), pool (usable chocolate fids), e12 (ref_name, port_name, tier), arb (set of (choc name, mocha name)),
    match_demos (demos where Mocha replays chocolate-doom identically), digest (per-demo agreement table), sfs (frozen coefficients), hb5 (dict of split/manifest path/ua, or None)"""
    def __init__(self, **kw): self.__dict__.update(dict(MD=None, fMD=None, e12=None, arb=None, digest=None, sfs=None, hb5=None, match_demos=None)); self.__dict__.update(kw)

def cl_report(ev_rows): return pd.DataFrame(ev_rows)
def eval_set(sel_df, S, rowidx, colidx, pool_reach, pool_lines, n0names, B, n_shuf, chance):
    """ranks, metrics and the registered comparisons for one truth set. S = dict method -> (n_rows x pool) score matrices (lower = closer); sel_df rows give the query row and partner column."""
    n = len(sel_df)
    if n == 0: return dict(n=0)
    ri = np.array([rowidx[int(f)] for f in sel_df.mfid]); tj = np.array([colidx[int(f)] for f in sel_df.cfid]); cl = sel_df.cfid.to_numpy(); R, TS, MT = {}, {}, {}
    for k, Mx in S.items(): R[k] = prank(Mx[ri], tj); TS[k] = tiesize(Mx[ri], tj); MT[k] = metrics(R[k], TS[k])
    best = max(n0names, key=lambda k: (MT[k]["top5"], MT[k]["mrr"])); comb = combined_rank_mean(S["D"][ri], S[best][ri]); R["combined"] = prank(comb, tj); TS["combined"] = tiesize(comb, tj); MT["combined"] = metrics(R["combined"], TS["combined"])
    ind = {k: (v <= 5).astype(float) for k, v in R.items()}; lift = cluster_boot(ind["D"], ind[best], cl, B, 11); lift_c = cluster_boot(ind["combined"], ind[best], cl, B, 12); d5 = cluster_ci(ind["D"], cl, B, 13)
    missed = (R[best] > 5) | (TS[best] > 1); lm = float(ind["D"][missed].mean()) if missed.any() else float("nan")
    st = strata_codes(pool_lines[tj]) * 3 + strata_codes(pool_reach[tj]) if n >= 9 else np.zeros(n, int); sh = {}
    for nm, k in (("D", "D"), (best, best)): v = shuffled_partner_ranks(S[k][ri], tj, st, n_shuf, 14); sh[nm] = dict(mean=float(v.mean()), lo=float(np.percentile(v, 2.5)), hi=float(np.percentile(v, 97.5)))
    return dict(n=int(n), clusters=int(len(np.unique(cl))), metrics=MT, best_n0=best, chance_top5=chance, d_top5_ci=d5, lift=lift, lift_combined_vs_n0=lift_c, d_top5_on_n0_tied_or_missed=lm, n_n0_tied_or_missed=int(missed.sum()), shuffled=sh, ri=ri, tj=tj, ind=ind, ranks=R)
def verdict(ev, thr, gates, flags, min_pairs=40):
    if ev.get("n", 0) == 0: return "INCONCLUSIVE for power (no usable pairs)"
    if flags: return "UNINTERPRETABLE (" + "; ".join(flags) + ")"
    if ev["n"] < min_pairs: return f"INCONCLUSIVE for power ({ev['n']} usable pairs < {min_pairs})"
    pt, lo, hi = ev["lift"]; d5 = ev["metrics"]["D"]["top5"]
    if pt >= 0.10 and lo > 0 and d5 >= thr: return "PASS"
    if -0.05 <= lo and hi <= 0.05: return "NOT DISTINGUISHABLE at this resolution (lift interval within +-0.05)"
    return "NOT PASSED (inconclusive: lift interval not within +-0.05; " + ("N0 better, interval below 0" if hi < 0 else "pass rule not met") + ")"
def analyze(ctx, B=10000, n_shuf=200, hb2_null=30, skip=(), outdir=None):
    M, C = ctx.M, ctx.C; demos = [d for d in M.demos if d in set(C.demos)]; M, C = M.subset(demos=demos), C.subset(demos=demos)
    phM, phC = phenotype(M), phenotype(C); pool = np.array(sorted(int(x) for x in ctx.pool)); T = tmax(phM, phC); uq = np.array(sorted(int(x) for x in phM.fids[usable(phM)])); nd = len(demos); out = dict(demos=nd)
    pairs = make_pairs(ctx.fM, ctx.fC, phM, phC, ctx.e12, ctx.arb); poolset = set(int(x) for x in pool); uqset = set(int(x) for x in uq)
    pairs["rankable"] = [(int(m) in uqset) and (int(c) in poolset) for m, c in zip(pairs.mfid, pairs.cfid)]
    out["n_usable"] = dict(mocha=len(uq), chocolate_pool=len(pool)); out["pairs"] = dict(name_agree=int(len(pairs)), strict=int(pairs.strict.sum()), strict_narrow=int(pairs.strict_narrow.sum()), strict_ext=int(pairs.strict_ext.sum()), rankable_loose=int(pairs.rankable.sum()),
        rankable_strict=int((pairs.rankable & pairs.strict).sum()), rankable_strict_narrow=int((pairs.rankable & pairs.strict_narrow).sum()), rankable_strict_ext=int((pairs.rankable & pairs.strict_ext).sum()))
    out["transition"] = transition(pairs).to_dict(); unrank = pairs[~pairs.rankable][["mname", "cname", "tier", "strict", "cls_m", "cls_c"]]
    # --- distances
    parts = pdist(phM, uq, phC, pool, T); Dm = {w: combine(parts, w) for w in ("D", "kill", "tic", "class")}; Kc = parts[0]
    di = np.arange(nd); mdm = [i for i, d in enumerate(demos) if ctx.match_demos and d in set(ctx.match_demos)]
    Lq, Lp = np.log1p(entries_matrix(M, uq, demos)), np.log1p(entries_matrix(C, pool, demos)); n0 = {}; a = n0_dists(Lq, Lp, di)
    for k in N0_KINDS: n0[f"N0_{k}_all"] = a[k]
    if len(mdm) >= 5:
        b = n0_dists(Lq, Lp, np.array(mdm))
        for k in N0_KINDS: n0[f"N0_{k}_match"] = b[k]
    out["match_demos"] = dict(n=len(mdm), demos=[demos[i] for i in mdm])
    S = {"D": Dm["D"], "D_kill": Dm["kill"], "D_tic": Dm["tic"], "D_class": Dm["class"], **n0}
    S["name_only"] = name_similarity(list(ctx.fM.set_index("fid").loc[uq, "name"]), list(ctx.fC.set_index("fid").loc[pool, "name"]))
    prop = {}
    if ctx.e12 is not None and len(ctx.e12):
        cn = {n: f for f, n in zip(ctx.fC.fid, ctx.fC.name) if (ctx.fC.name == n).sum() == 1}; mn = {n: f for f, n in zip(ctx.fM.fid, ctx.fM.name) if (ctx.fM.name == n).sum() == 1}
        for r in ctx.e12.itertuples():
            if r.ref_name in cn and r.port_name in mn: prop[int(mn[r.port_name])] = int(cn[r.ref_name])
    S["e12_structural"] = e12_matrix(uq, pool, prop); rowidx = {int(f): i for i, f in enumerate(uq)}; colidx = {int(f): j for j, f in enumerate(pool)}
    rc = C.reach.groupby("fid").demo.nunique(); pool_reach = np.array([rc.get(int(f), 0) for f in pool]); fl = ctx.fC.set_index("fid").lines; pool_lines = np.array([float(fl.get(int(f), 1)) for f in pool]); chance = 5 / len(pool); n0names = list(n0)
    # --- missing-D
    ri_all = pairs[pairs.rankable]; mi = np.array([Kc[rowidx[int(m)], colidx[int(c)]] < MIN_CO for m, c in zip(ri_all.mfid, ri_all.cfid)]) if len(ri_all) else np.array([], bool)
    out["missing_D"] = dict(matrix_rate=float((Kc < MIN_CO).mean()), loose_pair_rate=float(mi.mean()) if len(mi) else float("nan"))
    sets = {"strict": pairs.rankable & pairs.strict, "loose": pairs.rankable, "strict_ext (sensitivity)": pairs.rankable & pairs.strict_ext, "strict_narrow (sensitivity)": pairs.rankable & pairs.strict_narrow}; ev = {}
    for nm, mask in sets.items(): ev[nm] = eval_set(pairs[mask], S, rowidx, colidx, pool_reach, pool_lines, n0names, B, n_shuf, chance)
    # --- gates
    pcM = pc1(M); gates = dict(pc1f_top1=pcM["top1"], pc1f_top5=pcM["top5"], pc1f_n=pcM["n"], pc1g_ami=pcM["group_ami"], pc1f_pass=bool(pcM["top1"] >= 0.20 and pcM["top5"] >= 0.50), pc1g_pass=bool(pcM["group_ami"] >= 0.40)); out["gates"] = gates
    thr = max(3 * chance, 0.5 * pcM["top5"]); out["d_top5_threshold"] = thr; res = M.res; tot = len(res); bad = res.outcome.isin(["crash", "hang"]); crash_only = res.groupby("lesion").outcome.apply(lambda s: bool((s == "crash").all())).sum() if tot else 0
    out["crash_hang"] = dict(share=float(bad.mean()) if tot else 0.0, crash_rows=int((res.outcome == "crash").sum()), hang_rows=int((res.outcome == "hang").sum()), crash_only_lesions=int(crash_only), rows=int(tot))
    # --- hub and tie dominance (all query rows)
    top5 = np.argsort(S["D"], axis=1)[:, :5]; cnt = np.bincount(top5.ravel(), minlength=len(pool)); hub = float(cnt.max() / max(1, len(uq))); evs = ev["strict"]
    tie_share = float(np.mean(tiesize(S["D"][evs["ri"]], evs["tj"]) >= 5)) if evs.get("n") else 0.0; out["hub_tie"] = dict(hub_max_share_of_queries=hub, tie_ge5_share=tie_share)
    # --- leave-one-family-out (D top-5 and lift on the strict set)
    lofo = []
    if evs.get("n"):
        fams = sorted({d[0] for d in demos})
        for f in fams:
            ds = [d for d in demos if d[0] != f]; Ms, Cs = M.subset(demos=ds), C.subset(demos=ds); pM, pC = phenotype(Ms), phenotype(Cs); Dd = combine(pdist(pM, uq, pC, pool, T)); keep = [i for i, d in enumerate(demos) if d[0] != f]
            Nb = n0_dists(Lq, Lp, np.array(keep))[evs["best_n0"].split("_")[1]] if evs["best_n0"].endswith("_all") else None
            rD = prank(Dd[evs["ri"]], evs["tj"]); d5f = float((rD <= 5).mean()); row = dict(dropped=f, D_top5=d5f)
            if Nb is not None: row["best_N0_top5"] = float((prank(Nb[evs["ri"]], evs["tj"]) <= 5).mean()); row["lift"] = d5f - row["best_N0_top5"]
            lofo.append(row)
    out["lofo"] = lofo
    # --- flags
    flags = []
    if not gates["pc1f_pass"]: flags.append(f"PC1f failed (top-1 {gates['pc1f_top1']:.2f}, top-5 {gates['pc1f_top5']:.2f})")
    if not gates["pc1g_pass"]: flags.append(f"PC1g failed (AMI {gates['pc1g_ami']:.2f})")
    if out["missing_D"]["loose_pair_rate"] == out["missing_D"]["loose_pair_rate"] and out["missing_D"]["loose_pair_rate"] > 0.40: flags.append(f"missing-D rate {out['missing_D']['loose_pair_rate']:.0%} > 40%")
    if out["crash_hang"]["share"] > 0.15: flags.append(f"crash+hang {out['crash_hang']['share']:.0%} > 15%")
    if hub > 0.25: flags.append(f"hub dominance (one candidate in the top-5 of {hub:.0%} of queries)")
    if tie_share > 0.20: flags.append(f"tie dominance ({tie_share:.0%} of strict pairs tie with >= 5 candidates)")
    if lofo and evs["metrics"]["D"]["top5"] >= thr and any(r["D_top5"] < min(thr, 0.5 * evs["metrics"]["D"]["top5"]) for r in lofo): flags.append("result carried by one demo family (D top-5 falls below the threshold and by more than half when that family is dropped)")
    out["flags"] = flags; out["thresholds_note"] = "hub 25% and tie 20% are analysis-time operationalisations of 'hub or tie dominance' (the registration gives no number)"
    out["verdict"] = {k: verdict(v, thr, gates, flags if k == "strict" else []) for k, v in ev.items()}
    out["verdict"]["strict"] = verdict(evs, thr, gates, flags)
    out["H-B1"] = {k: {kk: vv for kk, vv in v.items() if kk not in ("ri", "tj", "ind", "ranks")} for k, v in ev.items()}
    # --- difference in differences versus managed-doom on the same chocolate functions
    out["did"] = did(ctx, ev, pairs, S, rowidx, colidx, uq, pool, phC, T, demos, B) if ctx.MD is not None else dict(note="no managed-doom store given")
    # --- H-B3 / H-B4
    thr_rand = rand_thresholds(Dm["D"], n0["N0_l1_all"]); out["random_cross_port"] = thr_rand
    out["H-B3"], flagged, audit = H.hb3(pairs, Dm["D"], uq, pool, thr_rand["D25"])
    coef = ctx.sfs or dict(intercept=0.0, b_tier=1.0, b_logsize=-1.0, note="NO frozen SFS file given: fallback tier minus log size")
    lines_m = ctx.fM.set_index("fid").lines.to_dict(); lines_c = ctx.fC.set_index("fid").lines.to_dict()
    out["H-B4"], hb4d = H.hb4(ctx.e12 if ctx.e12 is not None else pd.DataFrame(columns=["ref_name", "port_name", "tier"]), ctx.fM, ctx.fC, dict(D=Dm["D"], N0=n0["N0_l1_all"], rows=uq), pool, (lines_m, lines_c), coef, dict(D05=thr_rand["D05"], N005=thr_rand["N0_l1_05"]), B=min(B, 2000))
    out["H-B4"]["sfs_coef"] = coef
    # --- H-B2 / H-B5
    if "hb2" not in skip: out["H-B2"] = H.hb2(M, C, pairs, hb2_null)
    if "hb5" not in skip and ctx.hb5 is not None and (ctx.hb5.get("split")):
        rows, rs, a1, dropped = H.hb5(M, C, ctx.hb5["manifest"], phC, ctx.fC, ctx.hb5["ua"], ctx.hb5["split"], Path(outdir or "."))
        out["H-B5"] = dict(rows=rows, bootstrap=rs, a1=a1, dropped=int(dropped))
    out["_pairs"], out["_unrank"], out["_flagged"], out["_audit"] = pairs, unrank, flagged, audit
    return out
def rand_thresholds(D, N0, seed=8):
    """5th and 25th percentile of random cross-port D (missing-D pairs excluded) and the 5th percentile of random cross-port raw-L1 N0"""
    rng = np.random.default_rng(seed); i = rng.integers(0, D.shape[0], RAND_N); j = rng.integers(0, D.shape[1], RAND_N); d = D[i, j]; d = d[d < 1.0 - 1e-12]; n = N0[i, j]
    return dict(D05=float(np.quantile(d, 0.05)) if len(d) else 0.0, D25=float(np.quantile(d, 0.25)) if len(d) else 0.0, N0_l1_05=float(np.quantile(n, 0.05)), n_random=int(len(d)))
def did(ctx, ev, pairs, S, rowidx, colidx, uq, pool, phC, T, demos, B):
    """gap = D top-5 minus the best N0 top-5 on the same chocolate functions; DiD = Mocha gap minus managed-doom gap (managed-doom pairs = name-agree, E15 convention). Cluster bootstrap over chocolate-doom functions."""
    MD = ctx.MD.subset(demos=[d for d in ctx.MD.demos if d in set(demos)]); phD = phenotype(MD); ud = np.array(sorted(int(x) for x in phD.fids[usable(phD)]))
    kc, kd = name_keys(ctx.fC, True), name_keys(ctx.fMD, False); cpairs = [(kd[k], kc[k]) for k in kd if k in kc and kd[k] in set(ud) and kc[k] in set(int(x) for x in pool)]
    if not cpairs: return dict(note="no managed-doom name-agree pairs")
    Dd = combine(pdist(phD, ud, phC, pool, T)); Ld, Lp = np.log1p(entries_matrix(MD, ud, demos)), np.log1p(entries_matrix(ctx.C.subset(demos=demos), pool, demos)); nd_ = n0_dists(Ld, Lp, np.arange(len(demos)))
    rr = {int(f): i for i, f in enumerate(ud)}; ri = np.array([rr[m] for m, c in cpairs]); tj = np.array([colidx[c] for m, c in cpairs]); cf = np.array([c for m, c in cpairs]); rD = prank(Dd[ri], tj) <= 5
    bn = {k: (prank(nd_[k][ri], tj) <= 5).mean() for k in N0_KINDS}; bk = max(bn, key=bn.get); rN = prank(nd_[bk][ri], tj) <= 5; gap_md = {int(c): float(a) - float(b) for c, a, b in zip(cf, rD, rN)}; res = {}
    res["managed_doom"] = dict(n=len(cpairs), D_top5=float(rD.mean()), best_n0=f"N0_{bk}_all", n0_top5=float(rN.mean()), gap=float(rD.mean() - rN.mean()))
    for nm in ("strict", "loose"):
        e = ev[nm]
        if e.get("n", 0) == 0: continue
        gm = {}; cfm = pairs[pairs.rankable & (pairs.strict if nm == "strict" else True)].cfid.to_numpy()
        for c, a, b in zip(cfm, e["ind"]["D"], e["ind"][e["best_n0"]]): gm[int(c)] = float(a) - float(b)
        common = sorted(set(gm) & set(gap_md))
        if len(common) < 3: res[nm] = dict(n=len(common)); continue
        a = np.array([gm[c] for c in common]); b = np.array([gap_md[c] for c in common]); pt, lo, hi = cluster_boot(a, b, np.array(common), B, 15); res[nm] = dict(n=len(common), mocha_gap=float(a.mean()), md_gap=float(b.mean()), did=pt, lo=lo, hi=hi)
    return res
# ------------------------------------------------------------------ report
def f3(x): return "nan" if x is None or x != x else f"{x:.3f}"
def md_report(out):
    L = ["# E17 results: Mocha Doom lesion screen (v2 analysis, strict blind pipeline)\n"]; v = out["verdict"]["strict"]; L += [f"**H-B1 verdict (strict truth set, primary): {v}**\n"]
    p = out["pairs"]; L += [f"Demos {out['demos']}; usable Mocha functions {out['n_usable']['mocha']}; chocolate-doom pool {out['n_usable']['chocolate_pool']} (E15 masks). Name-agree pairs {p['name_agree']}: strict {p['strict']} (narrow twin-only {p['strict_narrow']}, any E12 tier {p['strict_ext']}); usable on both sides (rankable): loose {p['rankable_loose']}, strict {p['rankable_strict']}.",
        f"Missing-D (< 5 co-observed demos): {out['missing_D']['matrix_rate']:.1%} of all query x candidate cells, {f3(out['missing_D']['loose_pair_rate'])} of rankable name-agree pairs. Demos where Mocha replays chocolate-doom identically: {out['match_demos']['n']}.\n"]
    g = out["gates"]; L += ["## Gates and uninterpretable outcomes", f"PC1f (Mocha, within-function split-half): top-1 {g['pc1f_top1']:.2f}, top-5 {g['pc1f_top5']:.2f} (n={g['pc1f_n']}): {'pass' if g['pc1f_pass'] else 'FAIL'}; PC1g AMI {g['pc1g_ami']:.2f}: {'pass' if g['pc1g_pass'] else 'FAIL'}. Crash+hang share {out['crash_hang']['share']:.1%} ({out['crash_hang']['crash_rows']} crash rows, {out['crash_hang']['hang_rows']} hang rows, {out['crash_hang']['crash_only_lesions']} crash-only lesions). Hub max share {out['hub_tie']['hub_max_share_of_queries']:.0%}, tie>=5 share {out['hub_tie']['tie_ge5_share']:.0%}.",
        "Flags: " + ("; ".join(out["flags"]) if out["flags"] else "none") + f". D top-5 pass threshold max(3 x chance, 0.5 x PC1f top-5) = {out['d_top5_threshold']:.3f}.\n"]
    for k, e in out["H-B1"].items():
        L += [f"## H-B1, {k} truth set: {out['verdict'][k]}\n"]
        if e.get("n", 0) == 0: L += ["no usable pairs\n"]; continue
        rows = [dict(method=m, **{kk: round(vv, 3) for kk, vv in mt.items()}) for m, mt in e["metrics"].items()]; L += [f"pairs {e['n']} (clusters {e['clusters']}); chance top-5 {e['chance_top5']:.3f}; best N0 variant (by top-5): {e['best_n0']}.\n", pd.DataFrame(rows).to_markdown(index=False), ""]
        pt, lo, hi = e["lift"]; ptc, loc, hic = e["lift_combined_vs_n0"]; L += [f"D top-5 {e['d_top5_ci'][0]:.3f} (95% cluster CI {e['d_top5_ci'][1]:.3f} to {e['d_top5_ci'][2]:.3f}). **Lift D minus best N0 (top-5): {pt:+.3f}, 95% cluster-bootstrap interval {lo:+.3f} to {hi:+.3f}.** Counts plus lesions (combined) minus best N0: {ptc:+.3f} ({loc:+.3f} to {hic:+.3f}). D top-5 on N0-tied-or-missed pairs: {f3(e['d_top5_on_n0_tied_or_missed'])} (n={e['n_n0_tied_or_missed']}).",
              "Shuffled partners within strata of function size x reach (top-5, mean and 95% range of 200 shuffles): " + "; ".join(f"{m} {s['mean']:.3f} ({s['lo']:.3f} to {s['hi']:.3f})" for m, s in e["shuffled"].items()) + "\n"]
    L += ["## Unrankable name-agree pairs: 4x4 transition matrix (rows Mocha, columns chocolate-doom)\n", pd.DataFrame(out["transition"]).T.to_markdown() if False else pd.DataFrame(out["transition"]).to_markdown(), f"\n{len(out['_unrank'])} unrankable pairs are listed in `unrankable_pairs.csv` (counted, not misses).\n"]
    L += ["## Leave-one-demo-family-out (strict set)\n", pd.DataFrame(out["lofo"]).round(3).to_markdown(index=False) if out["lofo"] else "n/a", ""]
    d = out["did"]; L += ["## Difference in differences versus managed-doom (same chocolate-doom functions)\n", json.dumps(d, default=str, indent=1) + "\n"]
    L += ["## H-B2 families (descriptive: no pass/fail count)\n"]; h2 = out.get("H-B2")
    if h2: L += [f"chocolate-doom lesion classes reproduced: k = {h2['k']} (E15: {h2['e15_expected_k']}).\n", pd.DataFrame(h2["families"]).round(3).to_markdown(index=False) + "\n"]
    else: L += ["skipped\n"]
    h3 = out["H-B3"]; L += ["## H-B3 flagged pairs (audit list in `hb3_flagged.csv`, blind audit sample in `hb3_audit_sample.csv`)\n", f"threshold D >= {h3['threshold']:.3f} (25th percentile of random cross-port D): {h3['flagged']} of {h3['strict_usable']} usable strict pairs flagged ({f3(h3['share'])}); audit sample {h3['audit_n']}.\n"]
    h4 = out["H-B4"]; L += ["## H-B4 SFS confidence (AUC within tier, function-clustered CI; descriptive)\n", json.dumps(h4, default=str, indent=1) + "\n"]
    if "H-B5" in out: h5 = out["H-B5"]; L += ["## H-B5 E16 frozen scorer, Mocha lesions on chocolate-doom (exploratory)\n", pd.DataFrame(h5["rows"]).round(3).to_markdown(index=False), "", json.dumps(dict(bootstrap=h5["bootstrap"], a1=h5["a1"], dropped=h5["dropped"]), default=str, indent=1) + "\n"]
    L += ["## Deviations from the registration, forced by the data layout\n"] + [f"* {x}" for x in DEVIATIONS]; return "\n".join(L)
DEVIATIONS = [
    "'Twin tier' for the strict set = the E15 strong tiers (exact, twin, xtwin, seed); a narrow variant (exact, twin, xtwin only) and a variant with any E12 tier are reported as sensitivities. The text arbiter has no Mocha/chocolate-doom source, so confirmation comes from the optional --arbiter CSV (none by default).",
    "Mocha-matching demos (variant b): a demo counts when the two clean digests are identical on the common columns (RNG index excluded, dead-angle ignored) over the full length. The store holds only whole-demo entry counts, so counts cannot be truncated at a first-divergence tic; demos that diverge are excluded, not truncated (the first-divergence tics are in `demo_agreement.csv`).",
    "Eligibility of a function ('<4' class) uses the E15 rule, at least 4 informative lesions, not 4 observed demos.",
    "Best N0 variant is chosen on the truth set being evaluated (top-5, then MRR), which favours N0 and is conservative for the lift; the managed-doom gap uses its own best all-demo variant.",
    "Cosine and Spearman need >= 3 co-observed demos (else the maximum distance 2). Ties always count against the matcher (pessimistic ranks).",
    "'Same call-profile class' in H-B4 = raw-L1 N0 within the 5th percentile of random cross-port N0 (a divergent port cannot reproduce counts exactly); D-only confirmation AUC is reported beside it. SFS confidence = E15 step-2 logistic (tier, log size ratio) refit on managed-doom + prboom-plus pairs and frozen in `sfs_frozen.json` (E15's step 2 fitted one port and tested on the other).",
    "H-B2 families are reproduced by re-running lesion_classes.classify on the chocolate-doom store (seed 0), not read from a stored file; the shuffled-demo null permutes demo labels across Mocha result rows (30 shuffles).",
    "E12 structural matcher as a ranker: its one-to-one proposal ranks 1 when right, otherwise ties with all candidates. Name-only baseline = difflib similarity of names (name agreement defines truth, so this baseline is circular by construction; reported for completeness).",
    "Hub (25%) and tie (20%) dominance thresholds and the 'carried by one family' rule (D top-5 below the pass threshold and below half its full value when one family is dropped) are my operationalisations; the registration gives no numbers."]
def load_ctx(a):
    from roles import load_port
    S = prep.S; M = load_port("mochadoom", a.store)
    if a.choc_db: C = load_port("chocolate-doom", a.choc_db); pool = usable_fids(C)
    else: C, _, _, pool = prep.load()      # E15 masks, as the registration asks
    man = lambda p: pd.DataFrame([dict(fid=f["fid"], name=f["name"], file=f["file"], lines=f["end_line"] - f["line"] + 1) for f in json.load(open(p))["functions"]])
    fM, fC = man(a.manifest), man(a.choc_man or S / "choc_v2/manifest.json")
    MD = load_port("managed-doom", a.md_db or S / "md_phenotypes.sqlite") if not a.no_md else None; fMD = man(a.md_man or S / "md_v2/manifest.json") if MD is not None else None
    e12 = pd.read_csv(a.pairs) if Path(a.pairs).exists() else None; arb = set(map(tuple, pd.read_csv(a.arbiter)[["ref_name", "port_name"]].values)) if a.arbiter else None
    dem = sorted(set(M.demos) & set(C.demos)); dig = digest_agreement(a.clean_dir, a.choc_clean, dem); match = [d for d, v in dig.items() if v[0]]
    sfs = json.load(open(a.sfs)) if Path(a.sfs).exists() else None; sp = json.load(open(HERE.parent / "diagnosis/split.json"))
    return Ctx(M=M, C=C, MD=MD, fM=fM, fC=fC, fMD=fMD, pool=pool, e12=e12, arb=arb, match_demos=match, digest=dig, sfs=sfs, hb5=dict(split=sp, manifest=a.manifest, ua=pool))
def usable_fids(P): ph = phenotype(P); return ph.fids[usable(ph)]
def write(out, outdir):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True); (outdir / "E17_RESULTS.md").write_text(md_report(out))
    js = {k: v for k, v in out.items() if not k.startswith("_")}; (outdir / "E17_RESULTS.json").write_text(json.dumps(js, default=str, indent=1)); out["_unrank"].to_csv(outdir / "unrankable_pairs.csv", index=False)
    out["_pairs"].to_csv(outdir / "name_agree_pairs.csv", index=False); out["_flagged"].to_csv(outdir / "hb3_flagged.csv", index=False); out["_audit"].to_csv(outdir / "hb3_audit_sample.csv", index=False)
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("store"); ap.add_argument("manifest"); ap.add_argument("clean_dir"); ap.add_argument("out_dir")
    ap.add_argument("--B", type=int, default=10000); ap.add_argument("--pairs", default=str(HERE.parents[2] / "results/e17/mocha_choc_e12_pairs.csv")); ap.add_argument("--arbiter"); ap.add_argument("--sfs", default=str(HERE.parents[2] / "results/e17/sfs_frozen.json"))
    ap.add_argument("--choc-clean", default=str(prep.W / "e14/clean/ch")); ap.add_argument("--choc-db"); ap.add_argument("--choc-man"); ap.add_argument("--md-db"); ap.add_argument("--md-man"); ap.add_argument("--no-md", action="store_true"); ap.add_argument("--skip", default="")
    a = ap.parse_args(argv); ctx = load_ctx(a); out = analyze(ctx, B=a.B, skip=set(a.skip.split(",")), outdir=a.out_dir); write(out, a.out_dir)
    pd.DataFrame([dict(demo=d, identical=v[0], first_div_tic=v[1], field=v[2]) for d, v in ctx.digest.items()]).to_csv(Path(a.out_dir) / "demo_agreement.csv", index=False); print(md_report(out)[:3000])
if __name__ == "__main__": main()
