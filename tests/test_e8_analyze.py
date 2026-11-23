"""Synthetic tests for measure/e8_analyze.py. No real results are read: everything is generated in a temp dir."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e8_analyze", ROOT / "measure" / "e8_analyze.py")
E = importlib.util.module_from_spec(spec)
sys.modules["e8_analyze"] = E
spec.loader.exec_module(E)

AGES = [0.7, 1.5, 3.0, 6.0, 12.0, 20.0]
FRACS = [0.03125, 0.0625, 0.125, 0.25, 0.5, 1.0]
B = 300


def sha(port, k):
    return f"{(sum(map(ord, port)) * 1000 + k):012x}" + "0" * 28


def make_results(tmp, struct_lambda=0.15, flat_struct=False, seed=1, n_funcs=300, drop_to=None):
    """Write snapshots.csv + found/*.npz for 11 lineages (+3 children, controls)."""
    rng = np.random.default_rng(seed)
    rows = []
    (tmp / "found").mkdir(parents=True, exist_ok=True)
    plan_rows = []
    ports = E.LINEAGES + E.CHILDREN + ["helion"]
    for pi, port in enumerate(ports):
        role = "lineage" if port in E.LINEAGES else ("child-post-fork" if port in E.CHILDREN else "control-rewrite")
        stratum = "history-preserving" if port in E.HISTORY else "import"
        lam = struct_lambda * (0.8 + 0.4 * rng.random())
        for k, (a, f) in enumerate(zip(AGES, FRACS)):
            sh = sha(port, k)
            ps = 0.5 if flat_struct else np.exp(-lam * (a - AGES[0]))
            ps = 0.01 if role == "control-rewrite" else ps
            arr_s = rng.random(n_funcs) < ps
            arr_n = rng.random(n_funcs) < 0.5
            arr_p = rng.random(n_funcs) < ps
            tg = E.tag(sh, "")
            np.savez(tmp / "found" / f"{tg}__R1.npz", found_names=arr_n, found_struct_persnap=arr_s, found_struct_pooled=arr_p)
            rows.append(dict(port=port, role=role, stratum=stratum, plan_kind="calendar", fraction=f, sha=sh, date="2000-01-01",
                             age_years=a, ref="R1", n_ref_eligible=n_funcs, eligible_snapshot=200 + 100 * k, dup_share=0.1,
                             lang_c=1.0, lang_cpp=0.0, lang_other=0.0, ctags_functions=300, pruned="", underpowered=0,
                             surv_names=arr_n.mean(), surv_names_nostop=arr_n.mean(), names_certified=0, shared_names=0.0 if role == "control-rewrite" else 0.3,
                             surv_struct_persnap_either=arr_s.mean(), surv_struct_persnap_fwd=arr_s.mean(),
                             surv_struct_pooled_either=arr_p.mean(), shared_struct_persnap=0.0 if role == "control-rewrite" else 0.3,
                             shared_struct_pooled=0.0 if role == "control-rewrite" else 0.3, text_en=0, text_end=0))
            plan_rows.append(dict(port=port, scope_key="", sha=sh))
    snap = pd.DataFrame(rows)
    snap.to_csv(tmp / "snapshots.csv", index=False)
    return snap


def write_plans(tmp, snap):
    pd.DataFrame(dict(port=snap.port, scope_key="", sha=snap.sha)).to_csv(tmp / "plan.csv", index=False)


def make_pairs(tmp, fork=2013.94, lam=0.35, noise=0.01, seed=3):
    rng = np.random.default_rng(seed)
    rows = []
    for step in range(0, 15):
        t = fork + 0.5 * step
        s = 1.0 if step == 0 else float(np.clip(np.exp(-lam * (t - fork)) + rng.normal(0, noise), 0, 1))
        d = pd.Timestamp(year=int(t), month=1, day=1) + pd.Timedelta(days=int((t - int(t)) * 365.25))
        rows.append(dict(child="crispy-doom", parent="chocolate-doom", step=step, target_date=d.date().isoformat(), child_sha="a", parent_sha="a" if step == 0 else "b",
                         identical_sha=int(step == 0), elig_child=500, elig_parent=500, surv_struct_c2p=s, surv_struct_p2c=s,
                         shared_struct_max=s, shared_struct_min=s * 0.9, surv_names_c2p=s, surv_names_p2c=s, shared_names_max=s, shared_names_min=s))
    pd.DataFrame(rows).to_csv(tmp / "pairs_grid.csv", index=False)
    pd.DataFrame(dict(child=["crispy-doom"], parent=["chocolate-doom"], same_language=["yes"], fork_sha=["x"], fork_date=["2013-12-09"])).to_csv(tmp / "truth.csv", index=False)
    return pd.read_csv(tmp / "pairs_grid.csv")


def prepared(snap, ports=E.LINEAGES):
    return E.prepare_sample(snap, {}, "calendar", "R1", ports)


def test_holm_values():
    np.testing.assert_allclose(E.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    np.testing.assert_allclose(E.holm([0.5, 0.001, 0.2]), [0.5, 0.003, 0.4])
    assert E.holm([0.9, 0.9, 0.9]).max() == 1.0


def test_sign_test_power_statement():
    assert E.sign_test_threshold(11, 0.0125) == 10
    assert E.sign_test_threshold(11, 0.05) == 9


def test_decaying_structure_flat_names_passes(tmp_path):
    snap = make_results(tmp_path)
    ctx = E.Ctx(tmp_path, B=B, seed=5)
    ds, dn, ep = E.analyse(prepared(snap), ctx)
    assert ep["n_lineages"] == 11
    assert ep["P1"] and ep["P2"] and ep["P3"], ep
    assert ep["tau_crit"] and ep["delta_crit"]
    assert ep["med_tau_struct"] <= -0.6
    assert ep["names_ci_lo"] > -0.10 and ep["names_ci_hi"] < 0.10


def test_flat_structure_fails_p1(tmp_path):
    snap = make_results(tmp_path, flat_struct=True, seed=2)
    ctx = E.Ctx(tmp_path, B=B, seed=5)
    _, _, ep = E.analyse(prepared(snap), ctx)
    assert not ep["P1"]
    assert not ep["tau_crit"] and not ep["delta_crit"]


def test_children_underpowered_and_not_scored(tmp_path):
    snap = make_results(tmp_path)
    # make one lineage have only 3 usable snapshots via underpowered flag; and one underpowered row elsewhere
    m = (snap.port == "srb2") & (snap.age_years <= 3.0)
    snap.loc[m, "underpowered"] = 1                     # leaves 3 usable (6, 12, 20)
    m2 = (snap.port == "woof") & (snap.age_years == 0.7)
    snap.loc[m2, "underpowered"] = 1                    # 5 usable
    df = prepared(snap)
    assert set(df.port) <= set(E.LINEAGES)
    assert not set(df.port) & set(E.CHILDREN)
    ds, _ = E.per_lineage(df, *E.METHODS["struct"], E.Ctx(tmp_path, B=50))
    r = ds.set_index("port")
    assert r.loc["srb2", "n_usable"] == 3 and not r.loc["srb2", "scored"]
    assert r.loc["woof", "n_usable"] == 5 and r.loc["woof", "scored"]
    # earliest usable snapshot of woof is the 1.5-year one, not the underpowered 0.7
    assert r.loc["woof", "age_earliest"] == 1.5
    assert pd.isna(r.loc["srb2", "tau"])


def test_sha_dedup(tmp_path):
    snap = make_results(tmp_path)
    dup = snap[(snap.port == "woof") & (snap.fraction == 1.0)].copy()
    dup["fraction"] = 0.5
    snap2 = pd.concat([snap, dup], ignore_index=True)
    df = prepared(snap2)
    assert (df.port == "woof").sum() == 6
    assert not df.duplicated(["port", "sha"]).any()


def test_plan_file_membership_used_when_plan_kind_differs(tmp_path):
    snap = make_results(tmp_path)
    snap["plan_kind"] = "grid_child"
    plans = {"calendar": set(zip(snap.port, snap.sha))}
    assert len(E.prepare_sample(snap, plans, "calendar", "R1", E.LINEAGES)) == 66
    assert len(E.prepare_sample(snap, {}, "calendar", "R1", E.LINEAGES)) == 0


def test_hinge_recovers_fork(tmp_path):
    p = make_pairs(tmp_path)
    truth = pd.read_csv(tmp_path / "truth.csv")
    res, _ = E.h83b(p, truth, n_placebo=30, seed=1)
    row = res[res.method == "struct_max"].iloc[0]
    assert abs(row.error_years) <= 0.5, row
    assert row.same_language == "yes"
    assert row.n_points == 14                       # identical-SHA row excluded
    assert abs(row.error_years) < abs(row.baseline_error_years)
    # direct estimator check, noiseless
    t = np.arange(2014.0, 2020.0, 0.5)
    est, lam, _ = E.hinge_fit(t, np.exp(-0.4 * (t - 2013.5)))
    assert abs(est - 2013.5) <= 0.1 and abs(lam - 0.4) < 0.1


def make_self_origin(df, mcol="surv_struct_pooled_either", lam=0.15, seed=0):
    """Synthetic self_origin.csv: exp decay from s0 with S=1 at s0."""
    rng = np.random.default_rng(seed)
    rows = []
    for port, g in df.groupby("port"):
        u = g[g.underpowered != 1].sort_values("age_years")
        s0 = u.iloc[0]
        for _, r in u.iloc[1:].iterrows():
            v = float(np.exp(-lam * (r.age_years - s0.age_years)) * (0.9 + 0.2 * rng.random()))
            rows.append(dict(port=port, sha0=s0.sha, sha=r.sha, age_years=r.age_years, n_s0_eligible=200,
                             surv_names_self=min(v, 1.0), surv_struct_self_persnap_either=min(v, 1.0)))
    return pd.DataFrame(rows)


def test_h83a_censors_floor_ports_and_age_zero(tmp_path):
    snap = make_results(tmp_path)
    df = prepared(snap)
    so = make_self_origin(df)
    hd = df[(df.port == "fastdoom") & (df.age_years == 20.0)].sha.iloc[0]
    so.loc[(so.port == "fastdoom") & (so.sha == hd), "surv_struct_self_persnap_either"] = 0.01
    hd2 = df[(df.port == "doomretro") & (df.age_years == 20.0)].sha.iloc[0]
    so.loc[(so.port == "doomretro") & (so.sha == hd2), "surv_struct_self_persnap_either"] = 1.0
    so.to_csv(tmp_path / "self_origin.csv", index=False)
    so = pd.read_csv(tmp_path / "self_origin.csv")
    r = E.h83a(df, "surv_struct_pooled_either", so, E.SELF_COLS["struct"], n_perm=50, seed=1)
    t = r["table"].set_index("port")
    assert t.loc["fastdoom", "status"].startswith("censored") and np.isnan(t.loc["fastdoom", "a_hat"])
    assert t.loc["doomretro", "a_hat"] == 0.0
    assert r["n_censored"] == 1
    assert r["summary"]["n_estimated"] == 10
    # true age is the span head - s0, and the head value is the self-origin row of the head sha
    assert t.loc["woof", "true_age"] == pytest.approx(20.0 - 0.7)
    hw = df[(df.port == "woof") & (df.age_years == 20.0)].sha.iloc[0]
    assert t.loc["woof", "S_self"] == pytest.approx(so[(so.port == "woof") & (so.sha == hw)].surv_struct_self_persnap_either.iloc[0])
    assert 0.05 < t.loc["woof", "lambda_loo_median"] < 0.4


def test_h83a_missing_self_rows_unestimable(tmp_path):
    snap = make_results(tmp_path)
    df = prepared(snap)
    r = E.h83a(df, "surv_struct_pooled_either", None, E.SELF_COLS["struct"], n_perm=10, seed=1)
    assert r["n_estimated"] == 0 and r["table"].status.str.startswith("unestimable").all()


def test_permutation_null_kills_spearman_of_head_date_structure():
    rng = np.random.default_rng(0)
    ages = np.arange(1, 12, dtype=float)
    a_hat = ages * 1.3 + 0.2                         # monotone in age
    rho, p = E.perm_spearman(a_hat, ages, 2000, seed=4)
    assert rho == pytest.approx(1.0) and p < 0.001
    shuffled = rng.permutation(ages)                 # ages shuffled across lineages
    while stats_rho(a_hat, shuffled) > 0.5:
        shuffled = rng.permutation(ages)
    rho2, p2 = E.perm_spearman(a_hat, shuffled, 2000, seed=4)
    assert p2 > 0.05


def stats_rho(x, y):
    from scipy import stats
    return stats.spearmanr(x, y).statistic


def test_partial_spearman_removes_size_effect():
    n = 12
    z = np.arange(n, dtype=float)
    a = z + 0.0
    s = -z + np.random.default_rng(1).normal(0, 0.1, n)      # fully explained by z
    r, _ = E.partial_spearman(a, s, z)
    assert abs(r) < 0.9
    r_plain, _ = E.kendall(a, s)
    assert r_plain < -0.9


def test_functional_form_recovers_lambda(tmp_path):
    snap = make_results(tmp_path, struct_lambda=0.2, n_funcs=800)
    df = prepared(snap)
    ff = E.functional_form(df, E.Ctx(tmp_path, B=30), fit_draws=5)
    s = ff[ff.method == "struct"]
    assert 0.1 < s.lambda_m1.median() < 0.3
    assert (s.burst_yearly.dropna() >= 0).all() and s.lambda_m1_lo.notna().all()


def test_end_to_end_report(tmp_path):
    snap = make_results(tmp_path)
    make_pairs(tmp_path)
    make_self_origin(prepared(snap)).to_csv(tmp_path / "self_origin.csv", index=False)
    plan = tmp_path / "plan"
    plan.mkdir()
    pd.DataFrame(dict(port=snap.port, scope_key="", sha=snap.sha)).to_csv(plan / "e8_plan.csv", index=False)
    pd.DataFrame(dict(port=snap.port, scope_key="", sha=snap.sha, fraction=snap.fraction)).iloc[:0].to_csv(plan / "e8_plan_commitcount.csv", index=False)
    pd.read_csv(tmp_path / "truth.csv").to_csv(plan / "e8_fork_truth.csv", index=False)
    pd.DataFrame(dict(sha=["a", "b"], abs_diff=[0.0, 0.004])).to_csv(tmp_path / "noise.csv", index=False)
    pd.DataFrame(dict(port=E.LINEAGES, n_usable=6)).to_csv(tmp_path / "precondition_summary.csv", index=False)
    E.main(["--results", str(tmp_path), "--plan-dir", str(plan), "--boot", "100", "--perm", "100", "--fit-draws", "5", "--placebo", "10"])
    rep = (tmp_path / "analysis" / "phase_report.md").read_text()
    assert "Registered predictions scored" in rep and "P1" in rep
    for f in ["per_lineage.csv", "primary_endpoints.csv", "sensitivities.csv", "strata.csv", "functional_form.csv", "h83b_pairs.csv", "controls.csv"]:
        assert (tmp_path / "analysis" / f).exists(), f
    ns = pd.read_csv(tmp_path / "analysis" / "noise_summary.csv")
    assert ns[ns.column == "abs_diff"].max_abs.iloc[0] == pytest.approx(0.004)
    pe = pd.read_csv(tmp_path / "analysis" / "primary_endpoints.csv")
    assert (pe.result == "met").all()
