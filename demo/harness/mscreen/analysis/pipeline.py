"""E15 pipeline: run the registered analyses on two ports (A = chocolate-doom, B = managed-doom) and return a results dict + markdown."""
import re, numpy as np, pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from roles import *
from tests import *
PREFIX = re.compile(r"^(EV_|P_|A_|T_|PIT_|PTR_)"); GENERIC = {"add", "remove", "get", "set", "update", "run", "start", "stop", "init", "clear", "reset", "check", "free", "alloc"}
def agree_key(name, port_is_c):
    n = PREFIX.sub("", name) if port_is_c else name; return n
def reach_count(P, fids):
    c = P.reach.groupby("fid").demo.nunique(); return np.array([c.get(f, 0) for f in fids])
def n0_groups(P, ph, idx, demos, k):
    M = reach_pheno(P, ph.fids[idx], demos); D = np.abs(M[:, None, :] - M[None, :, :]).mean(2)
    return fcluster(linkage(squareform((D + D.T) / 2, checks=False), "average"), k, "maxclust")
def analyze(A, B, GA, GB, funcsA, funcsB, B_perm=10000):
    """funcsX: DataFrame(fid, name, file)"""
    out = {}; demos = A.demos; assert A.demos == B.demos
    phA, phB = phenotype(A), phenotype(B); out["n_eligible"] = (int(usable(phA).sum()), int(usable(phB).sum()))
    out["hot"] = (int(phA.hot.sum()), int(phB.hot.sum())); out["inert"] = (int(phA.inert.sum()), int(phB.inert.sum()))
    out["pc1"] = (pc1(A), pc1(B)); h = (h1a(phA, demos), h1a(phB, demos)); out["h1a"] = tuple({k: v for k, v in x.items() if k not in ("labels", "D", "stab", "idx")} for x in h)
    fmap = (funcsA.set_index("fid"), funcsB.set_index("fid")); res2 = []
    for P, ph, G, hh, f in ((A, phA, GA, h[0], fmap[0]), (B, phB, GB, h[1], fmap[1])):
        fids = ph.fids[hh["idx"]]; files = [f.loc[x, "file"] for x in fids]; rc = reach_count(P, fids)
        r = h2(hh["labels"], fids, G, files, rc, B=B_perm); g0 = n0_groups(P, ph, hh["idx"], demos, hh["k"]); r0 = h2(g0, fids, G, files, rc, B=min(B_perm, 2000)); r["n0_hops"] = r0["hops"]; res2.append(r)
    out["h2"] = tuple(res2)
    # name-agree pairs among usable functions with unique names
    def keyed(ph, hh, f, is_c):
        d = {}; cnt = collections.Counter(agree_key(f.loc[x, "name"], is_c) for x in ph.fids)
        for j, i in enumerate(hh["idx"]):
            k = agree_key(f.loc[ph.fids[i], "name"], is_c)
            if cnt[k] == 1 and len(k) >= 4 and k.lower() not in GENERIC: d[k] = j
        return d
    ka, kb = keyed(phA, h[0], fmap[0], True), keyed(phB, h[1], fmap[1], False); common = sorted(set(ka) & set(kb)); pairs = [(ka[k], kb[k]) for k in common]; out["pairs"] = len(pairs)
    la = h[0]["labels"][[p[0] for p in pairs]]; lb = h[1]["labels"][[p[1] for p in pairs]]
    out["_ctx"] = dict(phA=phA, phB=phB, h=h, fmap=fmap, pairs=pairs, ka=ka, kb=kb, A=A, B=B, demos=demos)
    if len(pairs) >= 4:
        sb = strata(reach_count(B, phB.fids[h[1]["idx"]][[p[1] for p in pairs]])); r3 = h3(la, lb, sb, B=B_perm)
        ga0 = n0_groups(A, phA, h[0]["idx"], demos, h[0]["k"]); gb0 = n0_groups(B, phB, h[1]["idx"], demos, h[1]["k"])
        r3["n0_ami"] = float(adjusted_mutual_info_score(ga0[[p[0] for p in pairs]], gb0[[p[1] for p in pairs]])); out["h3"] = r3
        # h4 pair indices are relative to usable(ph) order == h1a idx order
        out["h4"] = h4(phA, phB, A, B, demos, pairs, out["pc1"][1]["top5"], B=B_perm)
    return out
def verdicts(out):
    """apply the registered thresholds; returns a list of (prediction, observed, result). If H1a fails, H2-H4 results are labelled exploratory."""
    v = []; n_ok = min(out["n_eligible"]) >= 60; pc = out["pc1"]
    v.append(("PC1f function-level reliability gate for H4 (top-1 >= 0.20 and top-5 >= 0.50, each port)", f"A top1 {pc[0]['top1']:.2f} top5 {pc[0]['top5']:.2f} (n={pc[0]['n']}); B top1 {pc[1]['top1']:.2f} top5 {pc[1]['top5']:.2f} (n={pc[1]['n']})", "PASSED" if min(pc[0]['top1'], pc[1]['top1']) >= 0.20 and min(pc[0]['top5'], pc[1]['top5']) >= 0.50 else "FAILED (H4 uninterpretable)"))
    v.append(("PC1g group-level reliability gate for H1a-H3 (AMI of split-half groupings >= 0.40, each port)", f"A {pc[0]['group_ami']:.2f}, B {pc[1]['group_ami']:.2f}", "PASSED" if min(pc[0]['group_ami'], pc[1]['group_ami']) >= 0.40 else "FAILED (group claims uninterpretable)"))
    h1 = out["h1a"]; gate = all(x["p"] < 0.01 and x["share_stable"] >= 0.6 for x in h1)
    v.append(("H1a discrete grouping exists (max-gap p<0.01 against a Gaussian null with the observed covariance, and >=60% of functions in stable groups, both ports)", f"A k={h1[0]['k']} p={h1[0]['p']:.3f} (any-structure p={h1[0]['p_perm']:.3f}) stable {h1[0]['share_stable']:.2f}; B k={h1[1]['k']} p={h1[1]['p']:.3f} (any-structure p={h1[1]['p_perm']:.3f}) stable {h1[1]['share_stable']:.2f}", "PASSED" if gate else "FAILED (H2-H4 exploratory)"))
    tag = "" if gate else " [exploratory: H1a failed]"
    for i, nm in enumerate(("chocolate-doom", "managed-doom")):
        r = out["h2"][i]; ok = r["hops"] >= 0.5 and r["p"] < 0.0167
        v.append((f"H2 neighbourhoods, {nm} (>= 0.5 hops, p<0.0167; clean-count baseline reported)", f"{r['hops']:.2f} hops (obs {r['obs_mean']:.2f} vs null {r['null_mean']:.2f}), p={r['p']:.4f}; clean-count groups {r['n0_hops']:.2f} ({'break-pattern groups tighter' if r['hops'] > r['n0_hops'] else 'not tighter than clean-count groups'})", ("PASSED" if ok else "FAILED") + tag if n_ok else "INCONCLUSIVE (power)"))
    if "h3" in out:
        r = out["h3"]; ok = r["ami"] >= 0.30 and r["p"] < 0.0167
        v.append(("H3 recurrence (AMI >= 0.30, p<0.0167, >= 60 pairs; clean-count baseline reported)", f"AMI {r['ami']:.2f} (null {r['null_mean']:.2f}; clean-count groups {r['n0_ami']:.2f}) over {r['pairs']} pairs, p={r['p']:.4f}", ("PASSED" if ok else "FAILED") + tag if r["pairs"] >= 60 else "INCONCLUSIVE (power)"))
        r = out["h4"]; thr5 = max(3 * r["chance_top5"], 0.5 * r["ceiling_top5"]); ok = r["top5"] >= thr5 and r["p"] < 0.0167
        v.append(("H4 recovers name-agree partners beyond reach (a function-level result: not gated by H1a)", f"top-5 {r['top5']:.2f} (threshold {thr5:.2f}; chance {r['chance_top5']:.2f}, N0 {r['n0_top5']:.2f}, ceiling {r['ceiling_top5']:.2f}), top-1 {r['top1']:.2f} (N0 {r['n0_top1']:.2f}), p={r['p']:.4f}, pairs {r['pairs']}, pool {r['pool']}", ("PASSED" if ok else "FAILED") if r["pairs"] >= 60 else "INCONCLUSIVE (power)"))
    return v
