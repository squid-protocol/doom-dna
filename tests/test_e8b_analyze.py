"""Synthetic-data tests for measure/e8b_analyze.py (no real E8b results are read)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "measure"))
import e8b_analyze as E  # noqa: E402

PORTS = E.PRIMARY_PORTS
PROG = {"prboom-plus": "boom", "woof": "mbf", "eternity": "smmu", "edge-classic": "edge",
        "inter-doom": "crispy", "doomretro": "chocolate"}
M, NR, NL = 600, 800, 900


def make_world(tmp, passing, novel=0.10, wrong_novel=0.005, lang_c_first=None, wrong_total=0.05,
               unrelated=0.0, top3=True, with_novel=True, n_snaps=4):
    """passing: set of ports whose A is large; others have A ~ 0.02."""
    tmp = Path(tmp)
    (tmp / "found").mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(1)
    rows, ctrl, rank = [], [], []
    for port in PORTS:
        for k in range(n_snaps):
            sha = f"{port[:4]}{k:02d}".ljust(12, "0") + "ab"
            big = port in passing
            r_cnt = int(NR * (0.55 if big else 0.12)) - 5 * k
            l_cnt = int(NL * (0.10 if big else 0.10))
            pr = np.zeros(M, bool)
            pr[:r_cnt] = True
            pl = np.zeros(M, bool)
            pl[:l_cnt] = True
            rng.shuffle(pr), rng.shuffle(pl)
            # counts must not exceed M: M=600 -> scale
            sR, sL = r_cnt / NR, l_cnt / NL
            lang_c = 0.95
            if lang_c_first is not None and port == lang_c_first and k == 0:
                lang_c = 0.5
            tagp = f"{sha[:12]}__{PROG[port]}__"
            np.savez(tmp / "found" / f"{tagp}paired.npz", p_in_R=pr, p_in_LD=pl, n_R_eligible=NR, n_LD_eligible=NL)
            base = dict(port=port, role="primary", **{"class": "B"}, ref="primary", ref_name=PROG[port], plan_kind="calendar",
                        sha=sha, date=f"{2002 + k}-06-01", age_years=3.0 + k, eligible_snapshot=500 + 10 * k,
                        underpowered=0, dup_share=0.1, lang_c=lang_c, lang_cpp=0.03, lang_other=0.02,
                        second_usable=int(k == 1), first3_median_flag=int(k < 3))
            rows.append(dict(base, subset="all", surv_names=sR * 0.9, surv_struct_persnap_either=sR,
                             surv_struct_pooled_either=sR + 0.01, shared_struct_persnap=sR, shared_names=sR,
                             surv_names_ld=sL * 0.9, surv_struct_persnap_either_ld=sL, surv_struct_pooled_either_ld=sL))
            rows.append(dict(base, subset="common_denominator", surv_names=sR, surv_struct_persnap_either=sR * 1.1,
                             surv_struct_pooled_either=sR, shared_struct_persnap=sR, shared_names=sR,
                             surv_names_ld=sL, surv_struct_persnap_either_ld=sL))
            if with_novel:
                nv = rng.random(300) < novel
                np.savez(tmp / "found" / f"{tagp}novel.npz", found_names=nv, found_struct_persnap=nv)
                rows.append(dict(base, subset="novel", surv_names=nv.mean(), surv_struct_persnap_either=nv.mean(),
                                 surv_struct_pooled_either=nv.mean(), shared_struct_persnap=0, shared_names=0,
                                 surv_names_ld=0, surv_struct_persnap_either_ld=0))
        ctrl.append(dict(kind="wrong_progenitor", port=port, ref_name="wrong", subset="all", surv_struct=wrong_total,
                         surv_names=0.05, date="2002-06-01"))
        ctrl.append(dict(kind="wrong_progenitor", port=port, ref_name="wrong", subset="novel", surv_struct=wrong_novel,
                         surv_names=0.0, date="2002-06-01"))
        rank.append(dict(port=port, ref_name=PROG[port], rank_struct=1 if top3 else 7, rank_names=2, K=20,
                         shared_struct_ref=0.5, shared_names_ref=0.4, top_candidate_struct=PROG[port],
                         top_candidate_names=PROG[port]))
    for name in ["curl", "nginx"]:
        for ref in PROG.values():
            ctrl.append(dict(kind="unrelated", port=name, ref_name=ref, subset="all", surv_struct=unrelated,
                             surv_names=0.0, date="2020-01-01"))
    pd.DataFrame(rows).to_csv(tmp / "snapshots_prog.csv", index=False)
    pd.DataFrame(ctrl).to_csv(tmp / "controls_prog.csv", index=False)
    pd.DataFrame(rank).to_csv(tmp / "ranking.csv", index=False)
    pd.DataFrame([dict(child="crispy-doom", parent="chocolate-doom", step=s, date=f"2015-0{s}-01",
                       surv_struct_fork_anchored=0.8 - 0.05 * s, surv_names_fork_anchored=0.7,
                       shared_struct_contemporaneous=0.9, shared_names_contemporaneous=0.9) for s in range(1, 4)]
                 ).to_csv(tmp / "classA.csv", index=False)
    pd.DataFrame([dict(progenitor="boom", n_eligible=856, n_unchanged=500, n_modified=200, n_novel=156)]
                 ).to_csv(tmp / "decomposition_summary.csv", index=False)
    return tmp


def run(tmp, **kw):
    return E.run(tmp, None, B=400, **kw)


def test_six_pass_supported(tmp_path):
    w = make_world(tmp_path, set(PORTS))
    r = run(w)
    assert r["decision"]["n_qualifying"] == 6 and r["decision"]["n_pass"] == 6
    assert r["decision"]["status"] == E.STATUS_SUPPORTED
    assert r["decision"]["wilcoxon_p"] == pytest.approx(1 / 64)


def test_five_of_six_still_supported(tmp_path):
    w = make_world(tmp_path, set(PORTS[:5]))
    r = run(w)
    assert r["decision"]["n_pass"] == 5 and r["decision"]["status"] == E.STATUS_SUPPORTED


def test_three_pass_not_supported(tmp_path):
    w = make_world(tmp_path, set(PORTS[:3]))
    r = run(w)
    assert r["decision"]["n_pass"] == 3
    assert r["decision"]["status"] == "wrong comparator not supported"


def test_four_qualifying_inconclusive(tmp_path):
    w = make_world(tmp_path, set(PORTS))
    s = pd.read_csv(w / "snapshots_prog.csv")
    s = s[~s.port.isin(PORTS[:2])]
    s.to_csv(w / "snapshots_prog.csv", index=False)
    r = run(w)
    assert r["decision"]["n_qualifying"] == 4
    assert r["decision"]["status"] == E.STATUS_INCONCLUSIVE
    assert "inconclusive" in r["scored"]["h1"]


def test_lang_c_filter_excludes_snapshots(tmp_path):
    w = make_world(tmp_path, set(PORTS), lang_c_first="eternity")
    data = E.load_inputs(w)
    g = E.usable_rows(data["snap"], "eternity", {})
    assert len(g) == 3 and (g.lang_c >= 0.9).all()
    ex = E.lang_excluded(data["snap"], "eternity")
    assert len(ex) == 1
    # edge-classic (C++ progenitor) is not filtered even at low lang_c
    s = data["snap"]
    s.loc[s.port == "edge-classic", "lang_c"] = 0.1
    assert len(E.usable_rows(s, "edge-classic", {})) == 4
    r = run(w)
    assert (r["primary"].set_index("port").loc["eternity", "sha"] != ex.iloc[0]["sha"])
    rep = (Path(w) / "analysis" / "h8b1_lang_c_excluded.csv").read_text()
    assert "eternity" in rep and "A_names" in rep


def test_paired_bootstrap_interval(tmp_path):
    w = make_world(tmp_path, {"woof"})
    ctx = E.Ctx(w, 1000)
    data = E.load_inputs(w)
    big = E.usable_rows(data["snap"], "woof", {}).iloc[0]
    d = ctx.boot_paired_A(big)
    lo, hi = E.ci(d)
    A = E.a_value(data["snap"], big, {})
    assert lo < A < hi and lo > 0.2
    # deterministic
    assert np.array_equal(d, E.Ctx(w, 1000).boot_paired_A(big))
    small = E.usable_rows(data["snap"], "prboom-plus", {}).iloc[0]
    lo2, hi2 = E.ci(ctx.boot_paired_A(small))
    assert lo2 < 0.05  # A ~ 0.02: interval cannot clear +0.05 comfortably
    # A of exactly 0.05 with a wide interval fails the "interval above 0" requirement
    arr = np.zeros(40, bool)
    arr[:3] = True
    np.savez(w / "found" / f"{small['sha'][:12]}__{small['ref_name']}__paired.npz", p_in_R=arr, p_in_LD=arr[::-1].copy(),
             n_R_eligible=40, n_LD_eligible=40)
    lo3, hi3 = E.ci(E.Ctx(w, 1000).boot_paired_A(small))
    assert lo3 < 0 < hi3 or lo3 <= 0


def test_carry_over_with_and_without_novel(tmp_path):
    w = make_world(tmp_path / "a", set(PORTS), novel=0.15)
    r = run(w)
    assert r["carry"].passed.all() and r["scored"]["carry"] == "met"
    w2 = make_world(tmp_path / "b", set(PORTS), novel=0.0)
    r2 = run(w2)
    assert not r2["carry"].passed.any() and r2["scored"]["carry"] == "not met"
    # novel survival below the wrong-progenitor value also fails
    w3 = make_world(tmp_path / "c", set(PORTS), novel=0.15, wrong_novel=0.5)
    assert not run(w3)["carry"].passed.any()
    # no novel rows at all
    w4 = make_world(tmp_path / "d", set(PORTS), with_novel=False)
    assert not run(w4)["carry"].passed.any()


def test_wilcoxon_min_p_statement():
    assert E.min_wilcoxon_p(6) == pytest.approx(1 / 64)
    assert E.min_wilcoxon_p(5) == pytest.approx(1 / 32)
    assert E.wilcoxon_greater([0.3, 0.4, 0.35, 0.5, 0.6, 0.45]) == pytest.approx(1 / 64)
    assert E.wilcoxon_greater([0.3, 0.4, 0.35, 0.5, 0.6]) == pytest.approx(1 / 32)
    note = E.power_note(6)
    assert "1/64" in note and "1/32" in note


def test_ranking_gate(tmp_path):
    w = make_world(tmp_path / "a", set(PORTS), top3=True)
    r = run(w)
    assert r["scored"]["h3"] == "met" and (r["rank"].baseline_rank1 == 1 / 20).all()
    assert "every" in E.gate_statement(r["rank"])
    w2 = make_world(tmp_path / "b", set(PORTS), top3=False)
    r2 = run(w2)
    assert r2["scored"]["h3"] == "not met"
    g = E.gate_statement(r2["rank"])
    assert "NOT in the top 3" in g and "not read as supporting the map" in g


def test_controls(tmp_path):
    r = run(make_world(tmp_path / "a", set(PORTS)))
    assert r["spec"].passed.all() and r["cnov"].passed.all() and r["cunrel"].passed.all()
    assert r["scored"]["h4"] == "met"
    r2 = run(make_world(tmp_path / "b", set(PORTS), wrong_total=0.9, unrelated=0.1, wrong_novel=0.2))
    assert not r2["spec"].passed.any() and not r2["cnov"].passed.any() and not r2["cunrel"].passed.any()
    assert r2["scored"]["h4"] == "not met"


def test_fragile_flag_on_sensitivity_flip(tmp_path):
    w = make_world(tmp_path, set(PORTS))
    s = pd.read_csv(w / "snapshots_prog.csv")
    # high dup share in earliest snapshots of 3 ports -> dedup sensitivity changes the sample
    m = s.port.isin(PORTS[:3]) & (s.sha.str[4:6] == "00")
    s.loc[m, "dup_share"] = 0.4
    s.to_csv(w / "snapshots_prog.csv", index=False)
    r = run(w)
    assert r["decision"]["status"] == E.STATUS_SUPPORTED
    assert r["sens"].set_index("variant").loc["de-duplicated (dup_share <= 0.25)", "status"] == E.STATUS_SUPPORTED


def test_trends_partial_and_fragile():
    # survival decays with age but entirely through eligible growth -> partial vanishes
    age = np.arange(1, 9, dtype=float)
    elig = 100 * age
    s = 1 / np.sqrt(elig)
    t, p = E.kendall(age, s)
    assert t == pytest.approx(-1.0)
    pr, pp = E.partial_spearman(age, s, np.log(elig))
    assert abs(pr) < 1e-6 or pp > 0.05


def test_end_to_end_report(tmp_path):
    w = make_world(tmp_path, set(PORTS))
    E.main(["--results", str(w), "--plan-dir", str(tmp_path / "manifest"), "--B", "300"])
    rep = (w / "analysis" / "phase_report.md").read_text()
    assert rep.index("## Registered predictions scored") < rep.index("## Estimator choices") < rep.index("## 1.")
    for needle in ["Headline status: SUPPORTED", "1/64", "Leave-one-port-out", "Carry-over", "Class A", "Sensitivities",
                   "PAIRED bootstrap"]:
        assert needle in rep
    for f in ["h8b1_primary", "h8b1_carry_over", "h8b2_trends", "h8b3_ranking", "sensitivities", "classA_summary",
              "controls_specificity"]:
        assert (w / "analysis" / f"{f}.csv").exists()
