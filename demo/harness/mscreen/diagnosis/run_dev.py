"""E16 development task: tune the scorer on managed-doom lesions whose chocolate-doom counterpart lies in the DEVELOPMENT half, against a development-half dictionary and candidate list. Test-half functions are not used.
Usage: python run_dev.py <out_dir>"""
import itertools, json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import prep, score
from roles import load_port, phenotype
from tests import usable
HERE = Path(__file__).resolve().parent
def counterparts(A, phA, fa, B, phB, fb, ua):
    """managed-doom function id -> chocolate-doom function id (usable): same name after prefix stripping (unique in both ports) and an identical call-count profile on every demo"""
    ra, rb = prep.reach_matrix(A, list(phA.fids)), prep.reach_matrix(B, list(phB.fids)); na = [fa.loc[f, "name"] for f in phA.fids]; nb = [fb.loc[f, "name"] for f in phB.fids]; ka = [prep.PREFIX.sub("", n) for n in na]
    ca = pd.Series(ka).value_counts(); cb = pd.Series(nb).value_counts(); ia = {k: i for i, k in enumerate(ka) if ca[k] == 1 and len(k) >= 4 and k.lower() not in prep.GENERIC}; usable_set = set(int(x) for x in ua); out = {}
    for j, n in enumerate(nb):
        if cb[n] == 1 and n in ia:
            i = ia[n]
            if int(phA.fids[i]) in usable_set and np.array_equal(ra[i], rb[j]): out[int(phB.fids[j])] = int(phA.fids[i])
    return out
FAMILY = {"relational": "operator", "equality": "operator", "arithmetic": "operator", "arith2": "operator", "logical": "operator", "bitwise": "operator", "shift": "operator", "constant": "constant", "const_zero": "constant", "const_dec": "constant", "const_toggle": "constant", "not": "unary", "incdec": "unary", "negate": "control", "sdl": "control"}
def run_condition(cond, comp, D, dm, groups, cand, truth, w, qidx, SB, metaB, covA, RA, fam, fams, nles, tmax):
    """cond: 'none' (the exact twin lesion is in the dictionary), 'kind' (lesions of the query's kind are removed), 'family' (lesions of the query's family are removed)"""
    dk = dm.kind.to_numpy(); df = np.array([FAMILY.get(k, k) for k in dk]); qk = metaB.kind.to_numpy()[qidx]; qf = np.array([FAMILY.get(k, k) for k in qk]); base = {k: [] for k in ("ochiai", "tarantula", "metallaxis", "size", "calls", "family")}
    famprof_cache = {}
    def famprof(excl):
        if excl not in famprof_cache:
            keep = (df != excl) if cond == "family" else ((dk != excl) if cond == "kind" else np.ones(len(dk), bool))
            famprof_cache[excl] = np.array([[D["K"][g[keep[g]]][:, fam == f_].mean() if keep[g].any() else 0.0 for f_ in fams] for g in groups])
        return famprof_cache[excl]
    for n, qi in enumerate(qidx):
        q = {k: SB[k][qi] for k in ("K", "M", "T", "C")}; E = ~q["M"]; F = q["K"] & E; P = ~q["K"] & E; t = truth[n]
        ok = np.ones(len(dk), bool) if cond == "none" else ((df != qf[n]) if cond == "family" else (dk != qk[n]))
        base["ochiai"].append(score.rank_of(score.ochiai(covA, F, P), t)); base["tarantula"].append(score.rank_of(score.tarantula(covA, F, P), t)); base["calls"].append(score.rank_of(score.calls(RA, F, P), t)); base["size"].append(score.rank_of(nles.astype(float), t))
        kq = F.sum(); KLq = (D["K"] & E[None, :]); met = np.where(ok, (KLq & F[None, :]).sum(1) / np.sqrt(max(kq, 1) * np.maximum(KLq.sum(1), 1)), 0.0); base["metallaxis"].append(score.rank_of(score.aggregate(met.astype(np.float32), groups, "max"), t))
        qfv = np.array([(F[fam == f_]).mean() if (fam == f_).any() else 0.0 for f_ in fams]); fp = famprof(qf[n] if cond == "family" else qk[n]); base["family"].append(score.rank_of(-np.abs(fp - qfv[None, :]).sum(1), t))
    pool = len(cand); rnd = dict(n=len(qidx), top1=1 / pool, top3=3 / pool, top5=5 / pool, top10=10 / pool, mrr=np.mean(1 / np.arange(1, pool + 1)))
    rows = [dict(method="random (chance)", **rnd)] + [dict(method=nm, **score.metrics(base[k], w)) for nm, k in (("B2 Ochiai coverage", "ochiai"), ("B2 Tarantula coverage", "tarantula"), ("B3 Metallaxis-style kill-only", "metallaxis"), ("B4 size prior", "size"), ("B5 call-count contrast", "calls"), ("B7 demo-family-only", "family"))]
    simplex = [(i / 4, j / 4, (4 - i - j) / 4) for i in range(5) for j in range(5 - i)]; grid = []
    for how in ("max", "top3", "maxnorm"):
        for mn in (3, 5, 10):
            for wa, wb, wc in simplex:
                ranks = []
                for n, (a, b, c, nE, nK) in enumerate(comp):
                    ok = np.ones(len(dk), bool) if cond == "none" else ((df != qf[n]) if cond == "family" else (dk != qk[n])); valid = (nE >= mn) & (nK >= 1) & ok; sc = np.where(valid, wa * a + wb * b + wc * c, 0.0).astype(np.float32); ranks.append(score.rank_of(score.aggregate(sc, groups, how), truth[n]))
                grid.append(dict(agg=how, min_eval=mn, wa=wa, wb=wb, wc=wc, **score.metrics(ranks, w)))
    return rows, pd.DataFrame(grid).sort_values(["top5", "mrr"], ascending=False)
def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); sp = json.load(open(HERE / "split.json")); dev = set(sp["dev_fids"])
    A, phA, fa, ua = prep.load(); B = load_port("managed-doom", prep.S / "md_phenotypes.sqlite"); phB = phenotype(B); fb = prep.functions(prep.S / "md_v2/manifest.json").set_index("fid"); assert A.demos == B.demos
    SA, SB = prep.symptoms(A), prep.symptoms(B); cp = counterparts(A, phA, fa, B, phB, fb, ua); tmax = float(max(SA["T"].max(), SB["T"].max()))
    # development dictionary: lesions of development-half usable functions only; candidate pool = the same functions
    metaA = SA["meta"]; keep = metaA.fid.isin(dev).to_numpy(); D = {k: SA[k][keep] for k in ("K", "M", "T", "C")}; dm = metaA[keep].reset_index(drop=True); cand = sorted(dev); ci = {f: i for i, f in enumerate(cand)}
    groups = [np.where(dm.fid.to_numpy() == f)[0] for f in cand]; nles = np.array([len(g) for g in groups])
    metaB = SB["meta"]; qmask = metaB.fid.map(lambda f: cp.get(int(f), -1) in dev).to_numpy() & (SB["K"] & ~SB["M"]).sum(1).__ge__(3); qidx = np.where(qmask)[0]
    qfun = metaB.fid.iloc[qidx].map(lambda f: cp[int(f)]).to_numpy(); mf = pd.Series(qfun).value_counts(); w = np.array([1.0 / mf[f] for f in qfun])
    print(f"development task: dictionary {len(dm)} lesions in {len(cand)} functions; {len(qidx)} query lesions from {len(mf)} counterpart functions; pool {len(cand)} (chance top-5 {5 / len(cand):.3f})", flush=True)
    covA = prep.reach_matrix(A, cand) > 0; RA = prep.reach_matrix(A, cand); fam = np.array([d[0] for d in A.demos]); fams = sorted(set(fam))
    comp = []; truth = np.array([ci[f] for f in qfun]); covA = prep.reach_matrix(A, cand) > 0; RA = prep.reach_matrix(A, cand); fam = np.array([d[0] for d in A.demos]); fams = sorted(set(fam))
    for qi in qidx:
        q = {k: SB[k][qi] for k in ("K", "M", "T", "C")}; a, b, c, nE, nK, inter = score.components(q, D, tmax); comp.append((a, b, c, nE, nK))
    md = ["# E16 development task (development-half functions only; no test-half, no prboom-plus, no gore or Kocoa data)\n", f"dictionary {len(dm)} lesions in {len(cand)} functions; {len(qidx)} managed-doom query lesions from {len(mf)} chocolate-doom counterpart functions (equal weight per function); pool {len(cand)}.\n"]; cfg = {}
    for cond, label in (("none", "A. exact twin lesion in the dictionary (transplant upper bound)"), ("kind", "B. lesions of the query's kind removed from the dictionary"), ("family", "C. lesions of the query's family removed (operator / constant / unary / control flow): the realistic condition")):
        rows, G = run_condition(cond, comp, D, dm, groups, cand, truth, w, qidx, SB, metaB, covA, RA, fam, fams, nles, tmax); b0 = G.iloc[0]; G.to_csv(out / f"dev_grid_{cond}.csv", index=False)
        ochi5 = [r for r in rows if r["method"] == "B2 Ochiai coverage"][0]["top5"]; rows.append(dict(method=f"E16 scorer (best: {b0['agg']}, min {int(b0.min_eval)} demos, weights {b0.wa}/{b0.wb}/{b0.wc})", **{k: float(b0[k]) for k in ("n", "top1", "top3", "top5", "top10", "mrr")}))
        md += [f"## {label}\n", pd.DataFrame(rows).round(3).to_markdown(index=False), "", f"Top configurations:\n", G.head(4).round(3).to_markdown(index=False), ""]
        cfg[cond] = dict(agg=b0["agg"], min_eval=int(b0.min_eval), wa=float(b0.wa), wb=float(b0.wb), wc=float(b0.wc), dev_top5=float(b0.top5), b2_top5=float(ochi5), best_baseline_top5=float(max(r["top5"] for r in rows if r["method"] not in ("random (chance)",) and not r["method"].startswith("E16"))))
    fam_cfg = cfg["family"]; viable = fam_cfg["dev_top5"] >= fam_cfg["b2_top5"] + 0.10; md.append(f"**Viability gate on the realistic condition C** (scorer top-5 >= B2 Ochiai top-5 + 0.10): scorer {fam_cfg['dev_top5']:.3f} vs {fam_cfg['b2_top5']:.3f} + 0.10 -> **{'VIABLE' if viable else 'NOT VIABLE (study stops with a null)'}**. Best baseline in condition C: {fam_cfg['best_baseline_top5']:.3f}.\n")
    json.dump(dict(tmax=tmax, viable=bool(viable), conditions=cfg), open(out / "dev_config.json", "w"), indent=1)
    (out / "E16_DEV.md").write_text("\n".join(md)); print("\n".join(md))
if __name__ == "__main__": main()
