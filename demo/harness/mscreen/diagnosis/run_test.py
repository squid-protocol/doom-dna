"""E16 held-out test (T1 managed-doom, T2 prboom-plus). Uses FROZEN_SCORER.json only. Usage: python run_test.py <out_dir>"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import prep, score
from run_dev import counterparts, FAMILY
from roles import load_port, phenotype
HERE = Path(__file__).resolve().parent; FZ = json.load(open(HERE / "FROZEN_SCORER.json")); W3 = (FZ["weights"]["a_failing_set"], FZ["weights"]["b_class"], FZ["weights"]["c_tic"])
def boot(per_fn_a, per_fn_b, n=10000, seed=1):
    rng = np.random.default_rng(seed); a = np.asarray(per_fn_a); b = np.asarray(per_fn_b); m = len(a); idx = rng.integers(0, m, (n, m)); d = (a[idx] - b[idx]).mean(1); return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
def run(label, path, man, A, phA, fa, ua, SA, tmax, sp, out, rng):
    B = load_port(label, path); phB = phenotype(B); fb = prep.functions(man).set_index("fid"); assert A.demos == B.demos; SB = prep.symptoms(B); cp = counterparts(A, phA, fa, B, phB, fb, ua)
    test = set(sp["test_fids"]); cand = sorted(int(x) for x in ua); ci = {f: i for i, f in enumerate(cand)}; metaA = SA["meta"]; dk = metaA.kind.to_numpy(); df = np.array([FAMILY.get(k, k) for k in dk])
    groups = [np.where(metaA.fid.to_numpy() == f)[0] for f in cand]; nles = np.array([len(g) for g in groups]); D = {k: SA[k] for k in ("K", "M", "T", "C")}
    metaB = SB["meta"]; nk = (SB["K"] & ~SB["M"]).sum(1); all_c = metaB.fid.map(lambda f: int(f) in cp).to_numpy(); in_test = metaB.fid.map(lambda f: cp.get(int(f), -1) in test).to_numpy()
    qidx = np.where(in_test & (nk >= 3))[0]; dropped = int((in_test & (nk < 3)).sum()); qfun = metaB.fid.iloc[qidx].map(lambda f: cp[int(f)]).to_numpy(); truth = np.array([ci[f] for f in qfun]); mf = pd.Series(qfun).value_counts(); fns = sorted(mf.index)
    print(f"{label}: {len(fns)} test-half counterpart functions, {len(qidx)} queries ({dropped} dropped by the >=3-demo filter)", flush=True)
    covA = prep.reach_matrix(A, cand) > 0; RA = prep.reach_matrix(A, cand); fam = np.array([d[0] for d in A.demos]); fams = sorted(set(fam)); qk = metaB.kind.to_numpy()[qidx]; qf = np.array([FAMILY.get(k, k) for k in qk])
    famprof = np.array([[D["K"][g][:, fam == f_].mean() for f_ in fams] for g in groups]); perm = rng.permutation(len(cand)); R = {}
    names = ["dictionary", "dictionary_C", "ochiai", "tarantula", "metallaxis", "size", "calls", "family", "shuffled", "true_negative"]; R = {k: [] for k in names}
    for n, qi in enumerate(qidx):
        q = {k: SB[k][qi] for k in ("K", "M", "T", "C")}; E = ~q["M"]; F = q["K"] & E; P = ~q["K"] & E; t = truth[n]; a, b, c, nE, nK, _ = score.components(q, D, tmax); valid = (nE >= FZ["min_eval"]) & (nK >= 1)
        sc = np.where(valid, W3[0] * a + W3[1] * b + W3[2] * c, 0).astype(np.float32); fs = score.aggregate(sc, groups, FZ["agg"]); R["dictionary"].append(score.rank_of(fs, t))
        scC = np.where(valid & (df != qf[n]), W3[0] * a + W3[1] * b + W3[2] * c, 0).astype(np.float32); R["dictionary_C"].append(score.rank_of(score.aggregate(scC, groups, FZ["agg"]), t))
        R["ochiai"].append(score.rank_of(score.ochiai(covA, F, P), t)); R["tarantula"].append(score.rank_of(score.tarantula(covA, F, P), t)); R["calls"].append(score.rank_of(score.calls(RA, F, P), t)); R["size"].append(score.rank_of(nles.astype(float), t))
        KL = D["K"] & E[None, :]; met = (KL & F[None, :]).sum(1) / np.sqrt(max(F.sum(), 1) * np.maximum(KL.sum(1), 1)); R["metallaxis"].append(score.rank_of(score.aggregate(met.astype(np.float32), groups, "max"), t))
        qv = np.array([F[fam == f_].mean() for f_ in fams]); R["family"].append(score.rank_of(-np.abs(famprof - qv[None, :]).sum(1), t)); R["shuffled"].append(score.rank_of(fs[perm], t))
    w = np.array([1.0 / mf[f] for f in qfun]); pool = len(cand); rows = [dict(method="random (chance)", n=len(qidx), top1=1 / pool, top3=3 / pool, top5=5 / pool, top10=10 / pool, mrr=float(np.mean(1 / np.arange(1, pool + 1))))]
    for k in names:
        if k == "true_negative": continue
        rows.append(dict(method=k, **score.metrics(R[k], w)))
    # paired cluster bootstrap on top-5 per function
    pf = {k: np.array([np.mean([R[k][i] <= 5 for i in np.where(qfun == f)[0]]) for f in fns]) for k in names if k != "true_negative"}; res = {}
    for k in ("ochiai", "metallaxis", "family", "size", "calls", "dictionary_C", "shuffled"):
        d = pf["dictionary"] - pf[k]; lo, hi = boot(pf["dictionary"], pf[k]); res[k] = dict(delta=float(d.mean()), lo=lo, hi=hi)
    top5 = float(pf["dictionary"].mean())
    a1 = dict(top5=top5, ochiai_top5=float(pf["ochiai"].mean()), lift=res["ochiai"]["delta"], ci=(res["ochiai"]["lo"], res["ochiai"]["hi"]), n_functions=len(fns), power_ok=len(fns) >= 30)
    a1["pass"] = bool(a1["power_ok"] and a1["ci"][0] > 0 and a1["lift"] >= 0.15 and top5 >= max(0.25, a1["ochiai_top5"] + 0.15))
    # tie sets and hub statistic for the primary scorer
    pd.DataFrame(dict(lesion=metaB.lid.iloc[qidx].to_numpy(), host=metaB.fn.iloc[qidx].to_numpy(), truth_fid=qfun, rank_dictionary=R["dictionary"], rank_dictionary_C=R["dictionary_C"], rank_ochiai=R["ochiai"], rank_metallaxis=R["metallaxis"])).to_csv(out / f"{label}_ranks.csv", index=False)
    return rows, res, a1, dropped
def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); sp = json.load(open(HERE / "split.json")); A, phA, fa, ua = prep.load(); SA = prep.symptoms(A); rng = np.random.default_rng(7); md = ["# E16 held-out test (frozen scorer: " + json.dumps(FZ["weights"]) + f", {FZ['agg']}, min {FZ['min_eval']} demos)\n"]; summ = {}
    for label, p, man in (("managed-doom", prep.S / "md_phenotypes.sqlite", prep.S / "md_v2/manifest.json"), ("prboom-plus", prep.S / "pb_phenotypes.sqlite", prep.S / "pb_v2/manifest.json")):
        rows, res, a1, dropped = run(label, p, man, A, phA, fa, ua, SA, FZ["tmax"], sp, out, rng)
        md += [f"## {'T1' if label == 'managed-doom' else 'T2'}: {label} ({a1['n_functions']} test-half counterpart functions; {dropped} queries dropped by the >=3-demo filter; pool 140)\n", pd.DataFrame(rows).round(3).to_markdown(index=False), "", "Paired cluster bootstrap (functions, 10,000) of top-5, dictionary minus comparator:\n", pd.DataFrame(res).T.round(3).to_markdown(), "", f"**A1 check:** top-5 {a1['top5']:.3f}, Ochiai {a1['ochiai_top5']:.3f}, lift {a1['lift']:.3f}, 95% CI ({a1['ci'][0]:.3f}, {a1['ci'][1]:.3f}), functions {a1['n_functions']} (power gate >= 30: {a1['power_ok']}) -> **{'PASS' if a1['pass'] else 'FAIL'}**\n"]; summ[label] = a1
    md.append("Notes: `dictionary_C` removes the query's operator family; `shuffled` permutes function labels as units (chance control). The true-negative control and the hub statistic are computed separately. T2 includes functions with identical text (not separated): an upper bound.\n"); (out / "E16_TEST.md").write_text("\n".join(md)); json.dump(summ, open(out / "E16_TEST.json", "w"), indent=1, default=str); print("\n".join(md))
if __name__ == "__main__": main()
