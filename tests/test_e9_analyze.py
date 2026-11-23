"""Synthetic tests for measure/e9_analyze.py. Everything is generated in a temp dir; no real results are read."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e9_analyze", ROOT / "measure" / "e9_analyze.py")
A = importlib.util.module_from_spec(spec)
sys.modules["e9_analyze"] = A
spec.loader.exec_module(A)

CHOC = "chocolate-doom"
RECIP = ["eternity", "odamex", "woof", "prboom-plus", "gzdoom", "edge-classic"]
NEGS = ["nginx", "leveldb", "helion"]
NF = 80


def fid(prog, i):
    return f"{prog}:{i}"


def iso(base, days):
    return (pd.Timestamp(base, tz="UTC") + pd.Timedelta(days=int(days))).isoformat()


def make_world(tmp: Path, spike_c_small_hits=17, with_audit=False, seed=7):
    """Truth files + predictions + spike files for a small world. Returns the dict of paths."""
    rng = np.random.default_rng(seed)
    t9, p9, s9 = tmp / "truth", tmp / "pred", tmp / "spike"
    for d in (t9, p9, s9):
        d.mkdir(parents=True, exist_ok=True)
    progs = [CHOC] + RECIP + NEGS
    frows, trows = [], []
    for prog in progs:
        for i in range(NF):
            mod, t3, bh, name = "src", "", f"{prog}-{i}", f"{prog}_g{i}"
            if i < 10:
                mod, t3, bh, name = "textscreen", "textscreen", f"bh_ts{i}", f"ts_fn{i}"
            elif i < 15 and prog in (CHOC, "eternity", "odamex"):
                mod, t3, bh, name = "opl", "opl", f"bh_opl{i}", f"opl_fn{i}"
            if prog == "woof" and i in (8, 9):
                name = f"renamed_{i}_zz"
            if prog in (CHOC, "odamex") and i == 7:
                name = "dup_name"
            if prog == "odamex" and i == 70:
                name = "dup_name"
            frows.append(dict(program=prog, func_id=fid(prog, i), name=name, path=f"{mod}/f{i}.c", start_line=1, end_line=20, loc=20,
                              language_ext=".c", body_hash=bh, dup_rep=fid(prog, i), vertical=0, vertical_ancestor="", vertical_namekey=0,
                              module_dir=mod, external_lib="", t3_module=t3, engine_row=i))
            # dates
            if prog == CHOC:
                d = iso("2010-03-01", i) if i < 10 else (iso("2011-01-01", i) if i < 15 else iso("2004-01-01", rng.integers(0, 5000)))
            elif i < 10 and prog in RECIP:
                d = iso("2009-01-01", 0) if prog == "gzdoom" else iso("2012-06-01", i % 5)
            elif i < 15 and prog in ("eternity", "odamex"):
                d = iso("2013-01-01", i % 3)
            else:
                d = iso("2008-01-01", rng.integers(0, 4400))
            cens = int(prog == CHOC and i == 79)
            trows.append(dict(program=prog, func_id=fid(prog, i), first_commit="abc", first_date_committer=d, first_date_author=d,
                              censored=cens, reason="root" if cens else ""))
    pd.DataFrame(frows).to_csv(t9 / "functions.csv", index=False)
    pd.DataFrame(trows).to_csv(t9 / "t2.csv", index=False)
    prow, erow = [], []
    for r in RECIP:
        ids = [("textscreen", range(10))] + ([("opl", range(10, 15))] if r in ("eternity", "odamex") else [])
        for mod, rng_ in ids:
            eid = f"E-{mod}-{r}"
            erow.append(dict(event_id=eid, donor=CHOC, recipient=r, module_cluster=mod, n_functions=len(rng_), pair_class="port-to-port",
                             lineage_pair=A.lineage_pair(CHOC, r)))
            for i in rng_:
                prow.append(dict(prog_a=CHOC, func_a=fid(CHOC, i), prog_b=r, func_b=fid(r, i), jaccard=0.95, jaccard_idnorm=0.96,
                                 pair_class="port-to-port", eligible_primary=1, stratum="c-c", donor=CHOC, event_id=eid))
        prow.append(dict(prog_a=CHOC, func_a=fid(CHOC, 20), prog_b=r, func_b=fid(r, 20), jaccard=0.3, jaccard_idnorm=0.3,
                         pair_class="coincidence", eligible_primary=1, stratum="c-c", donor="", event_id=""))
    pd.DataFrame(prow).to_csv(t9 / "pairs.csv", index=False)
    pd.DataFrame(erow).to_csv(t9 / "events.csv", index=False)
    np.savez(t9 / "perm_null.npz", x=np.zeros(3))

    def pr(pred, var, a, i, b, j, cert):
        return dict(predictor=pred, variant=var, prog_a=a, func_a=fid(a, i), prog_b=b, func_b=fid(b, j), score_or_dist=0.0, certified=cert)

    preds = []
    for r in RECIP:
        ts = [(i, i) for i in range(10)] + ([(i, i) for i in range(10, 15)] if r in ("eternity", "odamex") else [])
        fp = [(30, 31), (31, 30)] + ([(40 + k, 40 + k) for k in range(6)] if r == "eternity" else [])
        for var in ("primary", "dedup"):
            for i, j in ts + fp:
                preds.append(pr("structure", var, CHOC, i, r, j, 1))
        names_tp = [(i, i) for i in range(6)] + ([(i, i) for i in range(10, 13)] if r in ("eternity", "odamex") else [])
        names_fp = [(50 + k, 51 + k) for k in range(6)]
        for var in ("unique_key", "dedup"):
            for i, j in names_tp + names_fp:
                preds.append(pr("names", var, CHOC, i, r, j, 1))
            for k in range(3):
                preds.append(pr("names", var, CHOC, 60 + k, r, 61 + k, 0))
        for var in ("primary", "dedup"):
            for k in range(8):
                preds.append(pr("r1", var, CHOC, 65 + k, r, 66 + k, 0))
    pd.DataFrame(preds).to_csv(p9 / "predictions.csv", index=False)
    ctrl = []
    for var, sv, nv in (("primary", "primary", "unique_key"), ("dedup", "dedup", "dedup")):
        for k in range(2):
            ctrl.append(pr("structure", sv, "nginx", k, "woof", k, 1))
        for k in range(6):
            ctrl.append(pr("names", nv, "nginx" if k < 5 else "leveldb", k, "woof", k, 1))
        for k in range(4):
            ctrl.append(pr("structure", sv, "helion", k, "woof", k, 1))
    pd.DataFrame(ctrl).to_csv(p9 / "predictions_controls.csv", index=False)
    # spike
    srows, sp = [], []
    hits = {("a", "150"): (20, 20), ("a", "50"): (20, 20), ("b50", "150"): (20, 10), ("b50", "50"): (20, 10), ("b100", "150"): (20, 0),
            ("b100", "50"): (20, 0), ("c", "150"): (20, 0), ("c", "50"): (spike_c_small_hits, 0), ("d", "150"): (12, 0),
            ("d", "50"): (12, 0), ("e", "150"): (6, 6), ("e", "50"): (3, 3)}
    for (tier, size), (hs, hn) in hits.items():
        n = 20 if tier != "e" else (6 if size == "150" else 3)
        prog = f"spike-{tier}-{size}"
        for i in range(n):
            srows.append(dict(tier=tier, module_size=size, donor="curl", recipient_program=prog, donor_func_id=f"curl:{i}",
                              recipient_func_name=f"s9_{i}", recipient_engine_row=1000 + i))
        if tier == "c" or tier == "a":
            n_s = hs
        else:
            n_s = min(hs, n)
        for i in range(min(n_s, n)):
            sp.append(dict(predictor="structure", variant="primary", prog_a="curl", func_a=f"curl:{i}", prog_b=prog, func_b=str(1000 + i),
                           score_or_dist=0.1, certified=1))
        for i in range(min(hn, n)):
            sp.append(dict(predictor="names", variant="unique_key", prog_a="curl", func_a=f"curl:{i}", prog_b=prog, func_b=str(1000 + i),
                           score_or_dist=0.0, certified=1))
    pd.DataFrame(srows).to_csv(s9 / "spike_truth.csv", index=False)
    pd.DataFrame(sp).to_csv(p9 / "predictions_spike.csv", index=False)
    if with_audit:
        pd.DataFrame([dict(pair_id=f"{CHOC}|{fid(CHOC, 30)}|eternity|{fid('eternity', 31)}", rater1="1", rater2="1", label="1")]).to_csv(
            t9 / "hand_audit_ratings.csv", index=False)
    return dict(t9=t9, p9=p9, s9=s9)


# ------------------------------------------------------------------------------------------------ statistics
def test_clopper_pearson_bounds():
    assert A.cp_upper(0, 1000) == pytest.approx(1 - 0.05 ** (1 / 1000), rel=1e-9)
    assert A.cp_upper(5, 5) == 1.0 and np.isnan(A.cp_upper(0, 0))
    lo, hi = A.cp_interval(8, 10)
    assert lo == pytest.approx(stats.beta.ppf(0.025, 8, 3)) and hi == pytest.approx(stats.beta.ppf(0.975, 9, 2))
    assert A.cp_interval(0, 10)[0] == 0.0 and A.cp_interval(10, 10)[1] == 1.0
    r = A.fp_rate(2, 160)
    assert r["rate_per_1000"] == pytest.approx(12.5) and r["upper95_per_1000"] == pytest.approx(1000 * A.cp_upper(2, 160))
    assert A.fp_rate(0, 160)["upper95_per_1000"] < 20


def test_holm_on_two_endpoints():
    assert np.allclose(A.holm([0.01, 0.04]), [0.02, 0.04])
    assert np.allclose(A.holm([0.04, 0.01]), [0.04, 0.02])
    assert np.allclose(A.holm([0.03, 0.03]), [0.06, 0.06])
    assert np.allclose(A.holm([0.5, float("nan")]), [1.0, 1.0])


def test_micro_average_is_pooled_not_mean_of_means():
    tab = pd.DataFrame(dict(cluster=["x", "y"], tp_s=[9, 1], n_s=[10, 10], tp_n=[1, 9], n_n=[10, 90]))
    r = A.cluster_boot_diff(tab, 200, 1)
    assert r["prec_s"] == pytest.approx(10 / 20) and r["prec_n"] == pytest.approx(10 / 100)
    assert r["diff"] == pytest.approx(0.5 - 0.1)


def test_cluster_bootstrap_interval_and_determinism():
    clusters = [f"c{i}" for i in range(8)]
    pos = pd.DataFrame(dict(cluster=clusters, tp_s=[9] * 8, n_s=[10] * 8, tp_n=[5] * 8, n_n=[10] * 8))
    r = A.cluster_boot_diff(pos, 500, 3)
    assert r["diff"] == pytest.approx(0.4) and r["lo"] == pytest.approx(0.4) and r["p_one_sided"] < 0.01
    assert r == A.cluster_boot_diff(pos, 500, 3)
    mixed = pd.DataFrame(dict(cluster=clusters, tp_s=[9, 1, 9, 1, 9, 1, 9, 1], n_s=[10] * 8, tp_n=[1, 9, 1, 9, 1, 9, 1, 9], n_n=[10] * 8))
    m = A.cluster_boot_diff(mixed, 500, 3)
    assert m["diff"] == pytest.approx(0.0) and m["lo"] < 0 < m["hi"] and m["p_one_sided"] > 0.1
    assert np.isnan(A.cluster_boot_diff(pos.iloc[0:0], 10, 1)["diff"])


def test_power_gate():
    ev = lambda pairs, mods: pd.DataFrame(dict(donor=[p[0] for p in pairs], recipient=[p[1] for p in pairs], module_cluster=mods))
    few = ev([("chocolate-doom", r) for r in ["eternity", "odamex", "woof", "nugget-doom"]], ["textscreen"] * 4)
    g = A.power_gate(few)
    assert g["descriptive"] and g["n_lineage_pairs"] == 3 and g["n_modules"] == 1       # woof and nugget-doom are one lineage
    assert A.power_gate(ev([("chocolate-doom", r) for r in RECIP], ["textscreen"] * 6))["descriptive"]       # one module only
    ok = A.power_gate(ev([("chocolate-doom", r) for r in RECIP], ["textscreen"] * 5 + ["opl"]))
    assert not ok["descriptive"] and ok["n_lineage_pairs"] == 6
    assert A.power_gate(pd.DataFrame())["descriptive"]


def test_spike_recall_arithmetic_and_check():
    st = pd.DataFrame(dict(tier=["c"] * 10, module_size=["150"] * 10, donor=["curl"] * 10, recipient_program=["sp"] * 10,
                           donor_func_id=[f"d{i}" for i in range(10)], recipient_func_name=["x"] * 10, recipient_engine_row=[str(i) for i in range(10)]))
    pred = pd.DataFrame([dict(predictor="structure", variant="primary", prog_a="curl", func_a=f"d{i}", prog_b="sp", func_b=str(i),
                              score_or_dist=0, certified=1) for i in range(8)] +
                        [dict(predictor="structure", variant="primary", prog_a="curl", func_a="d9", prog_b="sp", func_b="3", score_or_dist=0, certified=1)])
    rec = A.spike_recall(st, pred, "structure", "primary")
    r = rec.iloc[0]
    assert (r.hits, r.n, r.recall) == (8, 10, 0.8)                         # the wrong-partner pair for d9 is not a hit
    assert (r.ci_lo, r.ci_hi) == pytest.approx(A.cp_interval(8, 10))
    st2 = pd.concat([st, st.assign(module_size="50")])
    pred2 = pd.concat([pred, pred.assign(prog_b="sp")])
    rec2 = pd.concat([A.spike_recall(st, pred, "structure", "primary"), A.spike_recall(st.assign(module_size="50"), pred, "structure", "primary")])
    assert A.spike_check(rec2)["met"]
    rec3 = rec2.copy()
    rec3.loc[rec3.index[-1], "recall"] = 0.79
    assert not A.spike_check(rec3)["met"]
    assert not A.spike_check(rec2.iloc[:1])["met"]                         # needs both sizes


# ------------------------------------------------------------------------------------------------ scoring on the synthetic world
@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("w")
    paths = make_world(tmp)
    T = A.Truth(paths["t9"])
    preds = A.read_predictions(paths["p9"])
    return dict(paths=paths, T=T, preds=preds, scored=A.score_predictions(preds["eligible"], T))


def test_precision_recall_and_truth_flags(world):
    T, sc = world["T"], world["scored"]
    s = A.get_set(sc, "structure", "primary", "all")
    assert len(s) == 88 and int(s.tp9.sum()) == 70
    n_c = A.get_set(sc, "names", "unique_key", "cert")
    assert len(n_c) == 78 and int(n_c.tp9.sum()) == 42 and len(A.get_set(sc, "names", "unique_key", "all")) == 78 + 18
    classes = A.truth_classes(T)
    assert len(classes) == 70
    m = A.set_metrics(s, classes, A.covered_classes(s, T))
    assert m["recall"] == 1.0 and m["precision"] == pytest.approx(70 / 88)
    mn = A.set_metrics(n_c, classes, A.covered_classes(n_c, T))
    assert mn["covered"] == 42 and mn["recall"] == pytest.approx(42 / 70)
    # T3: pairs inside one T3 module count under the co-primary truth even below the jaccard cut
    assert int(s.t3.sum()) == 70 and int(s.copri.sum()) == 70


def test_p1_event_clustered_and_leave_one_module_out(world):
    sc = world["scored"]
    p1 = A.p1_block(sc, 400, 5, "copri")
    r = p1.iloc[0]
    assert r.prec_s == pytest.approx(70 / 88) and r.prec_n == pytest.approx(42 / 78) and r["diff"] == pytest.approx(70 / 88 - 42 / 78)
    assert r.n_clusters == 6 and r.lo > 0 and r.p_one_sided < 0.01
    assert set(p1.variant) == {"primary", "dedup"}
    lo = A.p1_block(sc, 400, 5, "copri", exclude_module="textscreen").iloc[0]
    assert lo.n_pred_struct < r.n_pred_struct and lo.n_pred_names < r.n_pred_names
    assert lo.excluded_module == "textscreen"
    # opl-only precision for structure: 15 tp predictions + FPs (30/31 and eternity 40..45) remain
    assert lo.n_pred_struct == 88 - 60 and lo.prec_s == pytest.approx(10 / 28)


def test_hand_audit_overrides_co_primary(tmp_path):
    paths = make_world(tmp_path, with_audit=True)
    T = A.Truth(paths["t9"])
    sc = A.score_predictions(A.read_predictions(paths["p9"])["eligible"], T)
    s = A.get_set(sc, "structure", "primary", "all")
    assert int((s.audit == 1).sum()) == 1 and int(s.copri.sum()) == 71   # the audited non-T1 pair is now a co-primary positive
    assert A.Truth(paths["t9"]).audit is not None


def test_negatives_and_p2(world):
    ctrl = A.score_predictions(world["preds"]["controls"], world["T"])
    neg, flagged = A.negatives_table(ctrl, world["T"])
    h = neg[(neg.stratum == "hard") & (neg.predictor == "structure") & (neg.variant == "primary")].iloc[0]
    assert (h.fp, h.n_eligible) == (2, 160) and h.upper95_per_1000 == pytest.approx(1000 * A.cp_upper(2, 160))
    hn = neg[(neg.stratum == "hard") & (neg.predictor == "names") & (neg.variant == "unique_key") & (neg.flavour == "cert")].iloc[0]
    assert hn.fp == 6
    soft = neg[(neg.stratum == "soft") & (neg.predictor == "structure") & (neg.variant == "primary")].iloc[0]
    assert soft.fp == 4 and soft.n_eligible == NF
    p2 = A.p2_block(neg, flagged)
    r = p2[p2.variant == "primary"].iloc[0]
    # structure flags nginx 0-1; names flags nginx 0-4 and leveldb 0: the overlap is nginx 0-1, so 0 vs 4 discordant functions
    assert (r.struct_only, r.names_only) == (0, 4) and r.p_one_sided == pytest.approx(stats.binom.cdf(0, 4, 0.5))
    assert r.upper_struct < r.upper_names


def test_spike_in_world(world):
    st = pd.read_csv(world["paths"]["s9"] / "spike_truth.csv", dtype=str)
    pred = world["preds"]["spike"]
    rec = pd.concat([A.spike_recall(st, pred, p, v, fl) for p, v, fl, _ in A.iter_sets(pred)])
    c = rec[(rec.predictor == "structure") & (rec.tier == "c")].set_index("module_size")
    assert (c.loc["150", "hits"], c.loc["50", "hits"]) == (20, 17)
    assert A.spike_check(rec)["met"]
    nm = rec[(rec.predictor == "names") & (rec.variant == "unique_key") & (rec.flavour == "all") & (rec.tier == "b100")]
    assert (nm.recall == 0).all()                                            # names recall under 100% renaming is zero


def test_order_excess_with_baseline_and_falsification(world):
    tab, summ, fals = A.order_excess(world["T"], 300, 1)
    assert set(tab.recipient) == set(RECIP) and summ["n_functions"] == 70
    assert summ["share"] == pytest.approx(60 / 70)
    assert 0.5 < summ["baseline"] < 0.9 and summ["excess"] == pytest.approx(summ["share"] - summ["baseline"])
    assert len(fals) == 10 and set(fals.recipient) == {"gzdoom"}              # gzdoom dated before the donor
    cens = tab.n_censored_excluded.sum()
    assert cens == 0
    # the exact baseline equals brute force on a small example
    d, r = np.array([1, 5, 9]), np.array([2, 6, 10, 0])
    brute = np.mean([x <= y for x in d for y in r])
    assert A.baseline_donor_first(d, r) == pytest.approx(brute)


def test_import_cluster_with_permutation_baselines(world):
    tab, summ = A.import_cluster(world["T"], world["scored"], 200, 2)
    c = tab[tab.set == "confirmed"]
    assert len(c) == 8 and (c.share == 1.0).all()                            # transferred functions land within days of one another
    assert summ["permuted"] < 0.5 and summ["excess"] > 0.5 and summ["lo"] > 0.3
    assert summ["native_dir"] < 1.0
    assert summ["n_unconfirmed"] >= 1 and summ["unconfirmed"] < 0.5          # unconfirmed predictions are spread over years
    again = A.import_cluster(world["T"], world["scored"], 200, 2)[1]
    assert again == summ


def test_module_clustering_share(world):
    T = world["T"]
    r = A.module_cluster_share("eternity", [fid("eternity", i) for i in range(10)], T)
    assert r["share"] == 1.0 and not r["call_graph_used"]
    scattered = [fid("eternity", i) for i in (20, 21, 22)]
    assert A.module_cluster_share("eternity", scattered, T)["share"] == 0.0
    # call-graph component of >= 5 matched functions rescues functions spread over directories
    f = T.functions
    fn = {k: dict(v) for k, v in T.fn.items()}
    for i in range(30, 36):
        fn[("eternity", fid("eternity", i))]["module_dir"] = f"dir{i}"
    T2 = A.Truth.__new__(A.Truth)
    T2.fn = fn
    ids = [fid("eternity", i) for i in range(30, 36)]
    edges = np.array([[30, 31], [31, 32], [32, 33], [33, 34], [40, 41]])
    r2 = A.module_cluster_share("eternity", ids, T2, lambda p: edges)
    assert r2["call_graph_used"] and r2["comp_share"] == pytest.approx(5 / 6) and r2["dir_share"] == 0.0


def test_h95_reason_codes(world):
    sc = world["scored"][world["scored"].mapped]
    classes = A.truth_classes(world["T"])
    miss = A.miss_table(world["T"], sc, classes)
    st = miss[(miss.predictor == "structure")]
    assert len(st) == 0
    nm = miss[(miss.predictor == "names") & (miss.flavour == "cert")]
    assert len(nm) == 70 - 42
    reasons = set(nm.reason)
    assert {"renamed_key_differs", "key_not_unique", "no_match_unexplained"} <= reasons
    woof = nm[(nm.prog_b == "woof") & nm.func_b.isin([fid("woof", 8), fid("woof", 9)])]
    assert set(woof.reason) == {"renamed_key_differs"}
    odamex7 = nm[(nm.prog_b == "odamex") & (nm.func_b == fid("odamex", 7))]
    assert set(odamex7.reason) == {"key_not_unique"}


# ------------------------------------------------------------------------------------------------ end to end
def test_end_to_end_report(tmp_path):
    paths = make_world(tmp_path)
    r = A.run_analysis(paths["t9"], paths["p9"], paths["s9"], None, B=200, seed=1, fp_dir=None)
    rep = (paths["p9"] / "analysis" / "phase_report.md").read_text()
    assert rep.index("## Registered checks scored") < rep.index("## Estimator choices") < rep.index("## 1. Truth and sample")
    for k in ("P1", "P2", "Spike-in: structure recall", "Order excess", "Import-cluster excess", "Power gate", "Falsification"):
        assert k in rep
    assert "hand_audit_ratings.csv absent" in rep
    assert r["gate"]["descriptive"] is False and r["spike_check"]["met"]
    assert set(r["holm"]) == {"P1", "P2"} and all(0 <= v <= 1 for v in r["holm"].values())
    assert r["holm"]["P1"] < 0.05
    for f in ("p1.csv", "p2.csv", "precision_recall.csv", "spike_recall.csv", "order_excess.csv", "import_cluster.csv", "h95_misses.csv",
              "registered_checks.csv", "negative_controls.csv", "leave_one_module_out.csv", "falsification_list.csv"):
        assert (paths["p9"] / "analysis" / f).exists(), f
    # determinism
    first = (paths["p9"] / "analysis" / "p1.csv").read_text()
    A.run_analysis(paths["t9"], paths["p9"], paths["s9"], None, B=200, seed=1, fp_dir=None)
    assert (paths["p9"] / "analysis" / "p1.csv").read_text() == first


def test_end_to_end_power_gate_makes_p1_descriptive_and_missing_inputs_are_skipped(tmp_path):
    paths = make_world(tmp_path)
    ev = pd.read_csv(paths["t9"] / "events.csv")
    ev[ev.recipient.isin(["eternity", "odamex"]) & (ev.module_cluster == "textscreen")].to_csv(paths["t9"] / "events.csv", index=False)
    (paths["p9"] / "predictions_controls.csv").unlink()
    (paths["p9"] / "predictions_spike.csv").unlink()
    r = A.run_analysis(paths["t9"], paths["p9"], paths["s9"], None, B=100, seed=1, fp_dir=None)
    rep = (paths["p9"] / "analysis" / "phase_report.md").read_text()
    assert r["gate"]["descriptive"] and "DESCRIPTIVE" in rep and "descriptive (power gate)" in rep
    assert set(r["holm"]) <= {"P2"} and "P1" not in r["holm"]
    assert "P2 skipped" in rep and "spike-in check skipped" in rep
