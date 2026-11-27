"""Validation of the E17 analysis (analysis/e17.py) on SYNTHETIC stores with planted structure; no real screen database (in particular no Mocha store) is touched.
Scenarios: perfect information (the Mocha function behaves exactly like its chocolate-doom partner, clean counts uncorrelated), partial (same role group only), none (independent), and a faithful port (identical clean counts) where N0 must win.
Run: nice -n 10 python demo/harness/mscreen/tests/test_e17_synthetic.py   (e11 venv python; pytest not needed)."""
import json, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import e17, e17_core as K
from e17_core import Port
KINDS = ["relational", "constant", "negate", "sdl", "not", "arithmetic"]; B_TEST = 1000
def demo_names(): return [f"{f}{i:04d}" for f, n in (("s", 15), ("c", 10), ("b", 8), ("v", 7)) for i in range(n)]
def build_port(name, rng, fids, p, mask, counts, demos, grp, hot, inert):
    les, res, reach = [], [], []; lid = 0
    for f in fids:
        for j, d in enumerate(demos):
            if mask[f, j]: reach.append((d, f, int(counts[f, j]), int(rng.integers(0, 200))))
        for _ in range(int(rng.integers(10, 25))):
            kind = KINDS[int(rng.integers(len(KINDS)))]; les.append((lid, f"file{grp[f] % 8}", f"fn{f}", f, 10, kind, "<", "<=")); lid += 1
            for j, d in enumerate(demos):
                if not mask[f, j] or rng.random() > 0.85: continue
                q = 0.97 if f in hot else (0.0 if f in inert else float(p[f, j])); killed = rng.random() < q; g = grp[f]
                m = (sum(1 << c for c in ([4, 5] if g % 3 == 0 else ([15, 16] if g % 3 == 1 else [17]))) | 4) if killed else None
                res.append((lid - 1, d, "killed" if killed else "same", int(np.exp(rng.normal(3 + 0.2 * (g % 5), 0.5))) if killed else None, m, 0, 1, f, f"file{grp[f] % 8}", f"fn{f}", kind))
    L = pd.DataFrame(les, columns=["id", "file", "fn", "fid", "line", "kind", "op", "new"]); R = pd.DataFrame(res, columns=["lesion", "demo", "outcome", "tic", "mask", "rc", "tries", "fid", "file", "fn", "kind"]); RC = pd.DataFrame(reach, columns=["demo", "fid", "entries", "first_tic"]); return Port(name, L, R, RC, demos)
def make_ctx(scenario, seed=21, n=170, k=20, strict_share=0.6, with_md=False, outdir=None):
    rng = np.random.default_rng(seed); demos = demo_names(); nd = len(demos); fids = list(range(n)); hot = set(fids[:6]); inert = set(fids[6:16])
    cent = rng.beta(0.4, 0.5, size=(k, nd)); gC = {f: int(rng.integers(0, k)) for f in fids}; idC = rng.normal(0, 0.2, (n, nd)); fam = rng.random((n, nd)) < rng.uniform(0.4, 0.95, (n, 1))
    pC = np.clip(np.array([cent[gC[f]] for f in fids]) + idC, 0, 1)
    if scenario == "perfect": gM, pM = dict(gC), pC.copy()
    elif scenario in ("partial", "faithful"): gM = dict(gC); pM = np.clip(np.array([cent[gM[f]] for f in fids]) + rng.normal(0, 0.2, (n, nd)), 0, 1)
    else: gM = {f: int(rng.integers(0, k)) for f in fids}; pM = np.clip(np.array([cent[gM[f]] for f in fids]) + rng.normal(0, 0.2, (n, nd)), 0, 1)
    cntC = rng.integers(5, 5000, (n, nd)); cntM = cntC.copy() if scenario == "faithful" else rng.integers(5, 5000, (n, nd))      # a diverged port's clean counts are unrelated to chocolate-doom's
    famM = fam if scenario == "faithful" else rng.random((n, nd)) < rng.uniform(0.4, 0.95, (n, 1))      # a diverged port reaches functions on its own pattern of demos
    C = build_port("chocolate-doom", rng, fids, pC, fam, cntC, demos, gC, hot, inert); M = build_port("mochadoom", rng, fids, pM, famM, cntM, demos, gM, hot, inert)
    lines = rng.integers(10, 200, n); fC = pd.DataFrame(dict(fid=fids, name=[f"P_func{f}x" for f in fids], file=[f"file{gC[f] % 8}" for f in fids], lines=lines)); fM = pd.DataFrame(dict(fid=fids, name=[f"func{f}x" for f in fids], file=[f"file{gM[f] % 8}" for f in fids], lines=(lines * rng.uniform(0.8, 1.5, n)).astype(int)))
    tiers = np.where(rng.random(n) < strict_share, "twin", np.where(rng.random(n) < 0.6, "ext1", ""))
    e12 = pd.DataFrame([dict(ref_name=f"P_func{f}x", port_name=f"func{f}x", tier=t) for f, t in zip(fids, tiers) if t] + [dict(ref_name=f"P_func{(f + 7) % n}x", port_name=f"func{f}x", tier="ext1") for f, t in zip(fids, tiers) if not t])   # plus wrong structural proposals (H-B4 negatives)
    ph = K.phenotype(C); pool = ph.fids[K.usable(ph)]; match = demos if scenario == "faithful" else demos[:25]
    MD = None; fMD = None
    if with_md:
        MD = build_port("managed-doom", rng, fids, np.clip(pC + rng.normal(0, 0.1, (n, nd)), 0, 1), fam, cntC, demos, gC, hot, inert); fMD = fM.copy()
    sfs = dict(intercept=0.0, b_tier=0.3, b_logsize=-1.0); hb5 = None
    if outdir is not None:
        man = Path(outdir) / "manifest.json"; man.write_text(json.dumps(dict(functions=[dict(fid=int(f), name=nm, file=fl) for f, nm, fl in zip(fM.fid, fM.name, fM.file)]))); tf = sorted(int(x) for x in rng.permutation(pool)[: len(pool) // 2]); hb5 = dict(split=dict(test_fids=tf), manifest=str(man), ua=pool)
    return e17.Ctx(M=M, C=C, MD=MD, fM=fM, fC=fC, fMD=fMD, pool=pool, e12=e12, match_demos=match, sfs=sfs, hb5=hb5)
_cache = {}
def run(scenario, **kw):
    key = (scenario, tuple(sorted(kw.items())))
    if key not in _cache: _cache[key] = e17.analyze(make_ctx(scenario, **kw), B=B_TEST, n_shuf=40, hb2_null=3, skip=("hb2", "hb5"))
    return _cache[key]
def top5(o, m="D", s="strict"): return o["H-B1"][s]["metrics"][m]["top5"]
def test_distance_parity_with_e15():
    ctx = make_ctx("perfect", n=60); import roles
    ph = K.phenotype(ctx.C); T = K.tmax(ph); idx = np.where(K.usable(ph))[0][:20]; a = ph.sub(idx); Dm = roles.dist(a, a, T); Dn = K.combine(K.pdist(ph, a.fids, ph, a.fids, T)); assert np.allclose(Dm, Dn)
def test_perfect_information_is_recovered():
    o = run("perfect"); e = o["H-B1"]["strict"]; assert e["n"] >= 40 and o["verdict"]["strict"] == "PASS", o["verdict"]
    assert top5(o) > 0.5 and top5(o) > top5(o, e["best_n0"]) + 0.3 and e["lift"][1] > 0           # N0 is uninformative on a diverged port; D finds the partner
    assert o["H-B3"]["share"] < 0.2                                                                # almost no true partner looks like a random pair
    assert top5(o, "e12_structural") <= 1.0 and top5(o, "D_kill") > 0.3                              # the ablation carries signal
def test_partial_is_between_perfect_and_none():
    p, q, n = run("perfect"), run("partial"), run("none")
    assert top5(p) > top5(q) >= top5(n) - 0.02 and top5(q) > 0.05 and top5(n) < 0.20
def test_no_information_is_not_a_pass():
    o = run("none"); e = o["H-B1"]["strict"]; assert not o["verdict"]["strict"].startswith("PASS")
    assert abs(top5(o) - e["chance_top5"]) < 0.12 and e["d_top5_ci"][1] <= 0.25 and o["H-B3"]["share"] > 0.5      # D at chance; most pairs look like random pairs
def test_faithful_port_n0_wins():
    o = run("faithful"); e = o["H-B1"]["strict"]; best = e["best_n0"]; assert top5(o, best) > top5(o) + 0.2 and e["lift"][2] < 0 and "N0 better" in o["verdict"]["strict"]
    assert top5(o, "N0_l1_all") > 0.9 and e["lift_combined_vs_n0"][0] > -0.15                                  # raw counts identify partners; adding D costs little
def test_unrankable_and_transition_matrix():
    o = run("perfect"); t = pd.DataFrame(o["transition"]); assert t.loc["hot", "hot"] >= 3 and t.loc["inert", "inert"] >= 5      # the planted hot and inert functions
    assert len(o["_unrank"]) > 0 and not o["_unrank"].cls_m.eq("usable").all() and o["pairs"]["rankable_loose"] + len(o["_unrank"]) == o["pairs"]["name_agree"]
def test_power_gate_and_null_wording():
    o = e17.analyze(make_ctx("perfect", strict_share=0.15), B=B_TEST, n_shuf=20, skip=("hb2", "hb5")); assert o["H-B1"]["strict"]["n"] < 40 and o["verdict"]["strict"].startswith("INCONCLUSIVE for power")
    ev = dict(n=60, lift=(0.01, -0.03, 0.04), metrics=dict(D=dict(top5=0.5)))
    assert e17.verdict(ev, 0.1, {}, []).startswith("NOT DISTINGUISHABLE") and e17.verdict(dict(ev, lift=(0.0, -0.2, 0.2)), 0.1, {}, []).startswith("NOT PASSED") and e17.verdict(ev, 0.1, {}, ["PC1f failed"]).startswith("UNINTERPRETABLE")
def test_difference_in_differences_runs():
    o = e17.analyze(make_ctx("perfect", with_md=True), B=B_TEST, n_shuf=20, skip=("hb2", "hb5")); d = o["did"]; assert d["managed_doom"]["n"] > 20 and "did" in d["strict"] and d["strict"]["lo"] <= d["strict"]["did"] <= d["strict"]["hi"]
def test_digest_agreement_and_truncation_rule():
    d = Path(tempfile.mkdtemp()); (d / "a").mkdir(); (d / "b").mkdir()
    def row(i, x): return " ".join(str(v) for v in [i, i + 1, 133, 0, x, 5, 0, 7, 100, 0, 1, 50, 0, 0, 0, 85, 11, 22, 0])
    for demo, dv in (("s0000", None), ("s0001", 50)):
        for sub in "ab": (d / sub / f"{demo}.txt").write_text("\n".join(row(i, 7 if (sub == "a" or dv is None or i < dv) else 8) for i in range(300)))
    r = K.digest_agreement(d / "b", d / "a", ["s0000", "s0001", "s0002"]); assert r["s0000"][0] and not r["s0001"][0] and r["s0001"][1] == 50 and r["s0002"][2] == "missing"
def test_full_run_with_descriptive_hypotheses():
    out = Path(tempfile.mkdtemp()); ctx = make_ctx("perfect", outdir=out); o = e17.analyze(ctx, B=B_TEST, n_shuf=20, hb2_null=3, outdir=out); e17.write(o, out)
    h2 = o["H-B2"]; assert h2["families"] and any(f.get("within_0_4") for f in h2["families"]) and (out / "E17_RESULTS.md").exists()          # identical profiles fall inside 0.4
    h4 = o["H-B4"]; assert h4["n"] >= 40 and h4["all"]["auc_D_only_confirmation"] > 0.7     # true twin pairs are confirmed on D, wrong extension proposals are not: the frozen score ranks them apart (D+N0 confirmation is empty here: counts are unrelated)
    h5 = o["H-B5"]; r = {x["method"]: x for x in h5["rows"]}; assert r["dictionary_C"]["top5"] > r["random (chance)"]["top5"] if "dictionary_C" in r else r["dictionary"]["top5"] > r["random (chance)"]["top5"]
    json.loads((out / "E17_RESULTS.json").read_text()); assert "H-B1" in (out / "E17_RESULTS.md").read_text()
if __name__ == "__main__":
    import time
    for name, fn in sorted((k, v) for k, v in dict(globals()).items() if k.startswith("test_")):
        t0 = time.time(); fn(); print(f"PASS {name} ({time.time() - t0:.0f}s)", flush=True)
