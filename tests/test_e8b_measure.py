"""Tests for measure/e8b_measure.py: synthetic tables for the logic, E8 reproduction against linuxdoom (skipped if the
E8 data is absent). No port-versus-progenitor comparison is run anywhere in this file."""

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "measure"))
import e8b_measure as X  # noqa: E402

M = X.M
FT = X.FunctionTable
HAVE_E8 = (X.HL / "results" / "snapshots.csv").exists() and (X.WORK / "results" / "e7" / "phaseA" / "fingerprints").exists()


def table(repo, names, vecs, keys, loc=20):
    n = len(names)
    return FT(repo=repo, name=np.array(names), path=np.array([f"src/{i}.c" for i in range(n)]),
              language=np.array(["c"] * n), loc=np.full(n, loc), archetype=np.zeros(n, dtype=int),
              key=np.array(keys, dtype=np.uint64), vectors=np.asarray(vecs, dtype=np.float32))


@pytest.fixture(scope="module")
def synth():
    rng = np.random.default_rng(7)
    d = 6
    Lv = rng.normal(size=(40, d)) * 3
    Lnames = [f"ldfunction{chr(97 + i // 26)}{chr(97 + i % 26)}" for i in range(40)]
    L = table("L", Lnames, Lv, np.arange(1, 41) * 7919)
    Rv = np.vstack([Lv[:10], rng.normal(size=(5, d)) * 3 + 50, rng.normal(size=(5, d)) * 3 - 50,
                    rng.normal(size=(10, d)) * 3 + 100])
    Rn = ([f"renamedclone{i}" for i in range(10)] + Lnames[10:15] + [f"textderived{i}" for i in range(5)]
          + [f"novelfunction{i}" for i in range(10)])
    Rk = list(np.arange(1, 11) * 7919) + list(10_000 + np.arange(20))
    R = table("R", Rn, Rv, Rk)
    verdicts = ["gone"] * 15 + ["derived"] * 5 + ["gone"] * 10
    return R, L, verdicts


# ---------------------------------------------------------------- decomposition

def test_classify_priority_and_variants():
    twin = [1, 1, 0, 0, 0, 0]
    name = [1, 0, 1, 0, 1, 0]
    text = [0, 0, 0, 1, 1, 0]
    p, t = X.classify(twin, name, text)
    assert list(p) == [X.U, X.U, X.MOD, X.MOD, X.MOD, X.NOV]
    assert list(t) == [X.U, X.U, X.NOV, X.NOV, X.NOV, X.NOV]


def test_decompose_four_classes_on_synthetic_tables(synth):
    R, L, verdicts = synth
    d = X.decompose(R, L, frozenset(), verdicts)
    assert X.check_decomposition(d) == []
    cp = list(d["class_primary"])
    assert cp[:10] == [X.U] * 10                      # certified twins (renamed copies)
    assert cp[10:15] == [X.MOD] * 5                   # same name key only
    assert cp[15:20] == [X.MOD] * 5                   # text arbiter derived only
    assert cp[20:] == [X.NOV] * 10                    # neither
    assert d["name_match"][10:15].all() and not d["name_match"][15:].any()
    assert d["text"][15:20].all() and not d["text"][:15].any()
    # twin_only variant: everything that is not a twin is novel
    assert list(d["class_twin_only"][:10]) == [X.U] * 10 and set(d["class_twin_only"][10:]) == {X.NOV}
    # mapping: twin i maps to linuxdoom row i
    assert list(d["ld_row"][:10]) == list(range(10)) and (d["ld_row"][10:] == -1).all()


def test_decompose_stoplist_blocks_name_channel(synth):
    R, L, verdicts = synth
    stop = frozenset(N for N in (X.N.name_key(n) for n in L.name[10:15]))
    d = X.decompose(R, L, stop, verdicts)
    assert list(d["class_primary"][10:15]) == [X.NOV] * 5


def test_decompose_without_text_channel(synth):
    R, L, _ = synth
    d = X.decompose(R, L, frozenset(), None)
    assert list(d["class_primary"][15:20]) == [X.NOV] * 5 and list(d["class_primary"][10:15]) == [X.MOD] * 5


def test_check_decomposition_detects_inconsistency(synth):
    R, L, verdicts = synth
    d = X.decompose(R, L, frozenset(), verdicts)
    d["class_primary"] = d["class_primary"].copy()
    d["class_primary"][0] = X.NOV
    assert X.check_decomposition(d)


# ---------------------------------------------------------------- subsets and survival arithmetic

def test_subset_masks_and_survival():
    cp = np.array([X.U, X.U, X.MOD, X.NOV, X.NOV, X.NOV], dtype=object)
    ct = np.array([X.U, X.U, X.NOV, X.NOV, X.NOV, X.NOV], dtype=object)
    m = X.subset_masks(cp, ct)
    assert {k: int(v.sum()) for k, v in m.items()} == {"all": 6, X.U: 2, X.MOD: 1, X.NOV: 3, "common_denominator": 3,
                                                        "novel_twin_only": 4}
    found = np.array([1, 0, 1, 1, 0, 0], dtype=bool)
    assert X.subset_survival(found, m["all"]) == pytest.approx(3 / 6)
    assert X.subset_survival(found, m[X.U]) == pytest.approx(1 / 2)
    assert X.subset_survival(found, m["common_denominator"]) == pytest.approx(2 / 3)
    assert X.subset_survival(found, m[X.NOV]) == pytest.approx(1 / 3)
    assert X.subset_survival(found, np.zeros(6, dtype=bool)) is None
    # the three classes partition: weighted subset survivals recombine to the total
    tot = sum(X.subset_survival(found, m[k]) * m[k].sum() for k in (X.U, X.MOD, X.NOV) if m[k].any())
    assert tot == pytest.approx(found.sum())


# ---------------------------------------------------------------- date filter and usable flags

def test_post_progenitor_filter_strict_and_boom_override():
    pins = {"boom-2.02": {"commit_date": "2025-01-08"}, "smmu": {"commit_date": "2001-02-25"}}
    assert X.filter_date("boom-2.02", pins) == date(1999, 12, 31)       # not the 2025 import date
    assert X.filter_date("mbf-2.03", {}) == date(1999, 12, 31)
    assert X.filter_date("smmu", pins) == date(2001, 2, 25)
    assert X.after_filter("2001-02-26", date(2001, 2, 25))
    assert not X.after_filter("2001-02-25", date(2001, 2, 25))          # strictly after
    assert not X.after_filter("2000-01-01", date(2001, 2, 25))
    assert X.usable(100, "2002-01-01", date(2001, 2, 25))
    assert not X.usable(99, "2002-01-01", date(2001, 2, 25))
    assert not X.usable(500, "2001-02-25", date(2001, 2, 25))
    assert not X.usable(0, "2005-01-01", date(2001, 2, 25), nonempty=False)


def test_second_usable_and_median_of_first_three():
    vals = {"2003-01-01": 0.9, "2002-01-01": 0.1, "2004-01-01": 0.5, "2005-01-01": 0.3}
    rows = []
    for dt, v in vals.items():
        for sub in ("all", "novel"):
            rows.append(dict(port="p", ref_name="r", sha=dt, date=dt, subset=sub, surv_names=v / 2,
                             surv_struct_persnap_either=v, surv_struct_pooled_either=""))
    X.add_usable_flags(rows)
    allr = {r["date"]: r for r in rows if r["subset"] == "all"}
    assert allr["2002-01-01"]["usable_rank"] == 1 and allr["2002-01-01"]["is_first_usable"] == 1
    assert allr["2003-01-01"]["is_second_usable"] == 1 and allr["2004-01-01"]["is_second_usable"] == 0
    assert [allr[d]["in_first_three"] for d in sorted(allr)] == [1, 1, 1, 0]
    # median of the first three usable (0.1, 0.9, 0.5) = 0.5, repeated on those rows, blank on the 4th
    assert allr["2002-01-01"]["median3_surv_struct_persnap_either"] == pytest.approx(0.5)
    assert allr["2004-01-01"]["median3_surv_struct_persnap_either"] == pytest.approx(0.5)
    assert allr["2005-01-01"]["median3_surv_struct_persnap_either"] == ""
    assert allr["2002-01-01"]["median3_surv_struct_pooled_either"] == ""


# ---------------------------------------------------------------- candidate pool

def test_candidate_pool_one_per_repo_strictly_before_origin_excluding_self_and_descendants():
    c = lambda repo, dt, sha: dict(repo=repo, date=dt, sha=sha, tag=sha)  # noqa: E731
    cands = [c("a", "2000-01-01", "a1"), c("a", "2001-06-01", "a2"), c("a", "2002-01-01", "a3"),   # a3 on origin: out
             c("b", "2001-12-31", "b1"), c("b", "2001-12-31", "b0"),                                   # tie -> larger sha
             c("self", "1999-01-01", "s1"), c("kid", "1999-01-01", "k1"), c("late", "2003-01-01", "l1")]
    pool = X.candidate_pool(cands, date(2002, 1, 1), {"self", "kid"})
    assert [(p["repo"], p["sha"]) for p in pool] == [("a", "a2"), ("b", "b1")]


def test_descendants_from_lineage_basis():
    basis = [dict(name="kid", parent="self", basis="explicit"), dict(name="grandkid", parent="kid", basis="explicit"),
             dict(name="other", parent="root", basis="explicit"), dict(name="ex", parent="self", basis="excluded")]
    assert X.descendants(basis, "self") == {"kid", "grandkid"}


def test_rank_of():
    vals = {"x": 0.5, "y": 0.9, "z": 0.5, "w": 0.1}
    assert X.rank_of(vals, "y") == (1, 0)
    assert X.rank_of(vals, "x") == (2, 1)
    assert X.rank_of(vals, "w") == (4, 0)


# ---------------------------------------------------------------- decoy family extension

def test_family_extension_for_decoy_pool():
    fam = {"prboom-plus": {"prboom-plus", "linuxdoom", "dsda-doom"}, "linuxdoom": {"linuxdoom", "prboom-plus"}}
    out = X.extend_family(fam, X.EXT_FAMILY, {"boom-2.02": ["prboom-plus"]})
    for k in ("boom", "mbf", "winmbf", "smmu", "prboom-2.5.0", "edge"):
        assert k in out["prboom-plus"] and k in out["linuxdoom"]
    assert {"boom-2.02", "linuxdoom", "dsda-doom", "prboom-plus"} <= out["boom-2.02"]   # progenitor = DOOM family member
    assert X.EXT_FAMILY <= out["boom-2.02"]
    assert "boom" not in fam["prboom-plus"]                                              # input not mutated


def test_registered_maps_match_amendment_2():
    m = {r["port"]: (r["primary"], r["cls"]) for r in X.PRIMARY_MAP}
    assert m == {"prboom-plus": ("boom-2.02", "B"), "woof": ("mbf-2.03", "B"), "eternity": ("smmu", "B"),
                 "edge-classic": ("edge@2021-09-17", "C"), "inter-doom": ("crispy-doom@2023-06-26", "C"),
                 "doomretro": ("chocolate-doom@2013-12-10", "C")}
    pins = X.load_pins()
    assert all(r["primary"] in pins for r in X.PRIMARY_MAP) and len(pins) == 8
    assert X.WRONG["prboom-plus"] == "chocolate-doom@2013-12-10" and X.WRONG["doomretro"] == "boom-2.02"
    assert X.repo_of("boom-2.02") == "boom" and X.repo_of("edge@2021-09-17") == "edge"


# ---------------------------------------------------------------- pipeline on synthetic tables (real E7 context)

@pytest.mark.skipif(not HAVE_E8, reason="E7/E8 data absent")
def test_measure_ref_port_synthetic_and_make_rows(tmp_path, synth):
    R, L, verdicts = synth
    ctx = X.Ctx8b(tmp_path, ["synthport"])
    ctx.add_ref("synthprog", "synthprog", R, [])
    d = X.decompose(R, L, ctx.stop, verdicts)
    rng = np.random.default_rng(3)
    # snapshot A: contains the 10 clones and the 5 same-name functions of R; snapshot B: only 4 clones
    A_ = table("tagA", [f"x{i}" for i in range(10)] + list(R.name[10:15]) + [f"other{i}" for i in range(30)],
               np.vstack([R.vectors[:10], rng.normal(size=(5, 6)) * 3 + 200, rng.normal(size=(30, 6)) * 3 - 200]),
               list(R.key[:10]) + list(900_000 + np.arange(35)))
    B_ = table("tagB", [f"y{i}" for i in range(4)] + [f"other{i}" for i in range(40)],
               np.vstack([R.vectors[:4], rng.normal(size=(40, 6)) * 3 - 300]), list(R.key[:4]) + list(800_000 + np.arange(40)))
    tabs = {"tagA": A_, "tagB": B_}
    snaps = [dict(tag="tagA", sha="a", date="2005-01-01", plan_kind="calendar"),
             dict(tag="tagB", sha="b", date="2006-01-01", plan_kind="calendar")]
    res = X.measure_ref_port(ctx, "synthprog", "synthport", snaps, tabs, found_dir=tmp_path / "found")
    a = res["tagA"]
    assert a["found_persnap"][:10].all() and not a["found_persnap"][20:].any()
    assert int(a["found_names"].sum()) == 5 and not a["found_names"][:10].any()
    assert res["tagB"]["found_persnap"].sum() == 4
    assert (tmp_path / "found" / "tagA__synthprog__synthport.npz").exists()
    with np.load(tmp_path / "found" / "tagA__synthprog__synthport.npz") as z:
        assert set(z["pairs_r"]) >= set(range(10)) and len(z["pairs_r"]) == len(z["pairs_p"])
        assert (z["found_struct_persnap"] == a["found_persnap"]).all()
    rows = X.make_rows(ctx, "synthport", "synthprog", {"role": "lineage", "class": "B", "ref": "primary"}, snaps, res, d,
                       date(2000, 1, 1), date(1999, 12, 31))
    by = {(r["sha"], r["subset"]): r for r in rows}
    assert by[("a", "all")]["surv_struct_persnap_either"] == pytest.approx(a["found_persnap"].sum() / 30)
    assert by[("a", X.U)]["surv_struct_persnap_either"] == pytest.approx(1.0)
    assert by[("a", X.NOV)]["surv_struct_persnap_either"] == pytest.approx(0.0)
    assert by[("a", X.MOD)]["surv_names"] == pytest.approx(5 / 10)
    assert by[("a", "common_denominator")]["n_subset"] == 20
    assert by[("b", X.U)]["surv_struct_persnap_either"] == pytest.approx(0.4)
    assert by[("a", "all")]["surv_struct_pooled_either"] != ""      # pooled over the two given snapshots
    assert by[("a", "all")]["age_years"] == pytest.approx((date(2005, 1, 1) - date(1999, 12, 31)).days / 365.25, abs=1e-3)


# ---------------------------------------------------------------- E8 reproduction (reference = linuxdoom)

@pytest.mark.skipif(not HAVE_E8, reason="E7/E8 data absent")
def test_reproduces_e8_values_against_linuxdoom(tmp_path):
    ctx = X.Ctx8b(tmp_path, ["chocolate-doom"])
    out = X.validate_e8(ctx, tmp_path, per_port=1, tol=0.01, ports=("chocolate-doom",))
    assert out, "no snapshot checked"
    for r in out:
        assert r["within_tol"] == 1, r
        for k in ("surv_names", "surv_struct_persnap_either", "surv_struct_pooled_either"):
            assert r[f"{k}_diff"] <= 0.01


# ---------------------------------------------------------------- dedup sensitivity

def test_dedup_table_keeps_one_per_digest_group_among_eligible():
    keys = [5, 5, 5, 7, 9, 9, 11]
    loc = [20, 20, 20, 20, 20, 20, 3]          # last row below the eligibility floor: untouched
    t = table("d", [f"n{i}" for i in range(7)], np.arange(14).reshape(7, 2), keys)
    t = X.FunctionTable(**{**t.__dict__, "loc": np.array(loc)})
    d = X.dedup_table(t)
    assert list(d.name) == ["n0", "n3", "n4", "n6"] and X.M.elig_mask(d).sum() == 3
    assert X.dedup_table(d).name.tolist() == d.name.tolist()          # idempotent


# ---------------------------------------------------------------- end to end: own writers -> e8b_analyze

def _world(rng, n_ld=150):
    d = 6
    Lv = rng.normal(size=(n_ld, d)) * 3
    L = table("L", [f"ldfn{i:04d}" for i in range(n_ld)], Lv, np.arange(1, n_ld + 1) * 7919)
    Rv = np.vstack([Lv[:60], rng.normal(size=(20, d)) * 3 + 50, rng.normal(size=(70, d)) * 3 + 100])
    Rn = [f"rclone{i:04d}" for i in range(60)] + [f"ldfn{i:04d}" for i in range(60, 80)] + [f"rnovel{i:04d}" for i in range(70)]
    R = table("R", Rn, Rv, list(np.arange(1, 61) * 7919) + list(50_000 + np.arange(90)))
    return L, R


def _snap_tab(rng, R, tag, n_clone, n=130):
    d = R.vectors.shape[1]
    base = 1_000_000 * (abs(hash(tag)) % 97 + 1)
    return table(tag, [f"{tag}c{i}" for i in range(n_clone)] + [f"{tag}x{i}" for i in range(n - n_clone)],
                 np.vstack([R.vectors[:n_clone], rng.normal(size=(n - n_clone, d)) * 3 - 300]),
                 list(R.key[:n_clone]) + list(base + np.arange(n - n_clone)))


@pytest.mark.skipif(not HAVE_E8, reason="E7/E8 data absent")
def test_end_to_end_writers_feed_the_analysis_script(tmp_path):
    import e8b_analyze as AN
    rng = np.random.default_rng(11)
    L, R = _world(rng)
    ctx = X.Ctx8b(tmp_path, ["prboom-plus", "woof"])
    ctx.add_ref("boom-2.02", "boom-2.02", R, [])
    W = _snap_tab(rng, R, "wrongref", 5, n=150)
    ctx.add_ref("chocolate-doom@2013-12-10", "chocwrong", W, [])
    wcls = X.decompose(W, L, ctx.stop, None)
    ctx.add_ref("synthld", "synthld", L, [])
    cls = X.decompose(R, L, ctx.stop, None)
    assert X.check_decomposition(cls) == []
    out_rows, ctrl, classa = [], [], []
    ds = {"prboom-plus": ("2000-06-01", "2002-06-01", "2004-06-01", "2006-06-01"),
          "woof": ("2009-06-01", "2011-06-01", "2013-06-01", "2015-06-01")}
    for port, dates in ds.items():
        snaps, tabs = [], {}
        for i, dt in enumerate(dates):
            tg = f"{port[:3]}{i}tag"
            tabs[tg] = _snap_tab(rng, R, tg, 40 - 8 * i)
            snaps.append(dict(tag=tg, sha=f"{port[:3]}{i}" + "ab" * 10, date=dt, plan_kind="calendar"))
        ldt = {}

        def loader(tag, port_, _ldt=ldt):
            return _ldt.get(tag)

        # linuxdoom arrays via the same measurement code, reference = synthetic L
        rl = X.measure_ref_port(ctx, "synthld", port, snaps, tabs)
        for tg, m in rl.items():
            ldt[tg] = dict(names=m["found_names"], persnap=m["found_persnap"], pooled=m["found_pooled"])
        rr = X.ref_rows(ctx, "boom-2.02", "primary", "boom-2.02", port, "B", snaps, tabs, cls, date(2000, 1, 1),
                        date(1999, 12, 31), tmp_path, ld_key="synthld", ld_loader=loader)
        X.add_usable_flags(rr)
        out_rows += rr
        res = X.measure_ref_port(ctx, "chocwrong", port, snaps, tabs)
        for r in X.make_rows(ctx, port, "chocolate-doom@2013-12-10", {}, snaps, res, wcls, date(2000, 1, 1), date(2013, 12, 10),
                             subsets=("all", X.NOV)):
            r["kind"] = "wrong_progenitor"
            ctrl.append(r)
        ctrl.append(dict(kind="unrelated", port="curl", ref_name="boom-2.02", subset="all", surv_struct=0.001, date="2010-01-01"))
    X.write(tmp_path / "snapshots_prog.csv", X.SNAP_COLS, out_rows)
    X.write(tmp_path / "controls_prog.csv", X.CONTROL_COLS, ctrl)
    summ = [dict(port="prboom-plus", metric=m, registered="boom-2.02", registered_rank=1, ties=0, K=9, one_over_K=round(1 / 9, 6),
                 top1="boom", top1_value=0.5, registered_value=0.5, linuxdoom_value=0.4, registered_is_repr=1)
            for m in ("shared_struct", "shared_names")]
    X.write(tmp_path / "ranking.csv", X.RANKW_COLS, X.ranking_wide(summ))
    X.write(tmp_path / "classA.csv", X.CLASSA_COLS, [dict(child="crispy-doom", parent="chocolate-doom", step=1,
                                                        surv_struct_fork_persnap=0.8, surv_names_fork=0.9, shared_struct_persnap=0.7,
                                                        shared_names=0.8)])
    X.write(tmp_path / "arbiter_prog.csv", X.ARB_COLS, [dict(kind="prog_vs_linuxdoom", port="boom-2.02", ref_name="linuxdoom")])
    X.write(tmp_path / "decomposition_summary.csv", ["pin", "eligible"], [dict(pin="boom-2.02", eligible=150)])

    p = AN.pd.read_csv(tmp_path / "snapshots_prog.csv")
    for c in ("second_usable", "first3_median_flag", "surv_struct_persnap_either_ld", "surv_names_ld",
              "surv_struct_pooled_either_ld", "surv_struct_persnap_either_dedup", "surv_struct_persnap_either_ld_dedup"):
        assert c in p and p[c].notna().any(), c
    sha = p[(p.port == "prboom-plus") & (p.subset == "all")].sha.iloc[0][:12]
    assert (tmp_path / "found" / f"{sha}__boom-2.02__paired.npz").exists()
    assert (tmp_path / "found" / f"{sha}__boom-2.02__novel.npz").exists()
    AN.main(["--results", str(tmp_path), "--plan-dir", str(tmp_path), "--B", "40"])
    assert (tmp_path / "analysis" / "phase_report.md").exists()
    prim = AN.pd.read_csv(tmp_path / "analysis" / "h8b1_primary.csv")
    row = prim[prim.port == "prboom-plus"].iloc[0]
    assert bool(row.qualifies) and np.isfinite(row.lo)          # the paired bootstrap file was found and read
    assert (tmp_path / "analysis" / "h8b1_carry_over.csv").exists()


def test_descriptive_pair_with_no_usable_snapshot_is_not_a_crash():
    # prboom-2.5.0 carries a 2026 filter date: every snapshot is before it
    pins = X.load_pins()
    fd = X.filter_date("prboom-2.5.0", pins)
    assert not any(X.usable(500, d, fd) for d in ("2000-03-09", "2023-06-20"))
    assert X.add_usable_flags([]) == []
