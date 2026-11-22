"""Tests for measure/e8_measure.py (run with the selfscan venv python: ``python -m pytest tests/test_e8_measure.py``)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "measure"))

import e8_measure as M  # noqa: E402
from structural_fingerprint import twins as T  # noqa: E402
from structural_fingerprint.fingerprint import FunctionTable  # noqa: E402

E7_SCAN = Path("/srv/storage_16tb/projects/doom-e7-work/scans/704cb35f0/chocolate-doom")
E7_RES = M.WORK / "results" / "e7" / "phaseA"


def table(repo, vectors, archetype=None, loc=None, key=None, names=None, language=None):
    n = len(vectors)
    return FunctionTable(
        repo=repo, name=np.array(names if names is not None else [f"f{i}" for i in range(n)]),
        path=np.array(["x.c"] * n), language=np.array(language if language is not None else ["c"] * n),
        loc=np.array(loc if loc is not None else [20] * n, dtype=np.int32),
        archetype=np.array(archetype if archetype is not None else [0] * n, dtype=np.int16),
        key=np.array(key if key is not None else np.arange(n, dtype=np.uint64), dtype=np.uint64),
        vectors=np.asarray(vectors, dtype=np.float32), edges=None)


def test_tag_matches_runner():
    sys.path.insert(0, str(HERE.parent / "measure"))
    import e8_snap
    for sha, sk in (("895f581c5d91497bdda0516612da803fe5843e28", "|src/heretic src/hexen src/strife"), ("a" * 40, "")):
        assert M.tag_of(sha, sk) == e8_snap.tag(sha, sk)
    assert M.tag_of("a" * 40, "").endswith("__da39a3")


def test_dup_share_synthetic():
    key = np.array([1, 1, 2, 3, 3, 3, 4, 9, 9], dtype=np.uint64)
    loc = np.array([10, 10, 10, 10, 10, 10, 10, 3, 3])  # the two loc-3 duplicates are not eligible
    assert M.dup_share(key, loc) == pytest.approx(5 / 7)  # keys 1,1,3,3,3 are in groups; 2 and 4 are not
    assert M.dup_share(np.arange(5, dtype=np.uint64), np.full(5, 8)) == 0.0
    assert M.dup_share(np.zeros(4, dtype=np.uint64), np.full(4, 8)) == 1.0
    assert M.dup_share(np.zeros(0, dtype=np.uint64), np.zeros(0)) == 0.0
    # a duplicate group needs two ELIGIBLE members: one eligible + one below the floor is not a group
    assert M.dup_share(np.array([5, 5], dtype=np.uint64), np.array([10, 4])) == 0.0


def test_lang_shares():
    lg = np.array(["c", "c", "cpp", "python", "c"])
    loc = np.array([10, 10, 10, 10, 2])
    c, cpp, oth = M.lang_shares(lg, loc)
    assert (c, cpp, oth) == pytest.approx((0.5, 0.25, 0.25))


def test_name_found_mask_matches_e7_count():
    stop = frozenset({"main"})
    ref = ["P_Foo", "P_Foo", "G_Bar", "main", "xy", "A_Baz"]
    snap = ["p_foo", "x_bar", "x_bar", "main", "A_Baz", "A_BAZ"]
    got = M.name_found_mask(ref, snap, stop)
    # keys: pfoo(2 ref, 1 snap) -> 1 found; gbar vs xbar differ; main stoplisted; xy too short; abaz -> 1
    assert got.tolist() == [True, False, False, False, False, True]
    cr, cs = M.N.key_counts(ref, M.N.name_key, stop), M.N.key_counts(snap, M.N.name_key, stop)
    assert got.sum() == M.N.matched(cr, cs)


def synthetic(seed=1, n=400, dim=8):
    rng = np.random.default_rng(seed)
    arch = rng.integers(0, 3, size=n)
    vec = rng.normal(size=(n, dim))
    R = table("R", vec, archetype=arch, key=np.arange(n, dtype=np.uint64))
    big = table("big", vec + rng.normal(scale=0.01, size=vec.shape), archetype=arch,
                key=np.arange(n, dtype=np.uint64) + 10_000)
    sub = rng.choice(n, 30, replace=False)
    small = table("small", vec[sub] + rng.normal(scale=0.01, size=(30, dim)), archetype=arch[sub],
                  key=np.arange(30, dtype=np.uint64) + 20_000)
    noise = table("noise", rng.normal(size=(n, dim)), archetype=rng.integers(0, 3, size=n),
                  key=np.arange(n, dtype=np.uint64) + 30_000)
    return R, big, small, noise


def test_pooled_threshold_helper_synthetic():
    R, big, small, noise = synthetic()
    P = M.PARAMS
    fwd = [T.search(R, t, P) for t in (big, small, noise)]
    back = [T.search(t, R, P) for t in (big, small, noise)]
    tf, tb = M.pooled_thresholds(fwd, back, P.fdr)
    assert tf == T.pooled_threshold(fwd, P.fdr)[0] and tb == T.pooled_threshold(back, P.fdr)[0]
    assert tf > 0 and tb > 0
    # a pool of one search is that search's own per-snapshot threshold
    own = T.accept(fwd[0]).threshold
    assert M.pooled_thresholds(fwd[:1], back[:1], P.fdr)[0] == pytest.approx(own)
    # power: the 30-function snapshot cannot certify anything alone (needs 1/fdr candidates), but can under the pool
    alone = T.accept(fwd[1])
    pooled = T.accept(fwd[1], tf)
    assert alone.threshold == 0.0 and len(pooled.q_index) > len(alone.q_index)
    assert len(pooled.q_index) >= 25
    # nothing from the unrelated snapshot is certified by the pooled yardstick beyond a small chance share
    assert len(T.accept(fwd[2], tf).q_index) < 0.05 * len(R)
    assert M.pooled_thresholds([], [], P.fdr) == (0.0, 0.0)


def test_twin_found_mask_positions():
    R, big, _, _ = synthetic()
    R.loc[:5] = 3  # ineligible reference rows (loc < 6) are dropped from the mask axis
    f = T.find_twins(R, big, M.PARAMS)
    b = T.find_twins(big, R, M.PARAMS)
    m = M.twin_found_mask(R, f, b)
    assert len(m) == int((R.loc >= 6).sum())
    assert m.sum() == len(set(f.q_index.tolist()) | set(b.t_index.tolist()))
    assert M.twin_found_mask(R, f, None).sum() == len(f.q_index)


@pytest.mark.skipif(not (E7_SCAN / "rc.txt").exists() or not (E7_RES / "pairs_names.csv").exists(),
                    reason="E7 chocolate-doom scan or E7 phase A tables absent")
def test_e7_validation_chocolate_doom(tmp_path):
    """The pipeline restricted to the E7-pinned chocolate-doom scan reproduces E7: names 0.830, structure 0.565."""
    ctx = M.Ctx(tmp_path, ["chocolate-doom"])
    db = M.snap_db(E7_SCAN)
    tab = ctx.fingerprint(db, "chocolate-doom")  # same program name as E7 (it seeds the decoy shuffles)
    fs, bs = M.get_searches(ctx, "chocolate-doom", "R1", tab, cache=False)
    per = M.struct_measures(ctx, "R1", fs, bs)
    nm = M.names_measures(ctx, "R1", "chocolate-doom", "chocolate-doom", tab, None)
    e7n = next(r for r in csv.DictReader(open(E7_RES / "pairs_names.csv")) if (r["q"], r["t"]) == ("linuxdoom", "chocolate-doom"))
    e7s = next(r for r in csv.DictReader(open(E7_RES / "pairs_struct.csv")) if (r["q"], r["t"]) == ("linuxdoom", "chocolate-doom"))
    assert per["nR"] == int(e7n["elig_q"]) == 689
    assert abs(nm["surv_names"] - 0.830) < 0.01
    assert abs(nm["surv_names"] - float(e7n["surv"])) < 1e-9
    assert abs(nm["names_certified"] - int(e7n["certified"])) == 0
    assert abs(per["either"] / per["nR"] - 0.565) < 0.01
    assert per["fwd"] == int(e7s["twins"])
    # found masks are consistent with the counts
    R = ctx.tables["R1"]
    em = R.loc >= 6
    fnd = M.name_found_mask(R.name[em], tab.name[tab.loc >= 6], ctx.stop)
    assert int(fnd.sum()) == int(e7n["matched"])
    assert int(per["found"].sum()) == per["either"]


def test_self_survival_self_vs_self_is_one():
    R, big, _, _ = synthetic()
    names = [f"fn_{i}_name" for i in range(len(R.loc))]
    R.name = np.array(names)
    n, s = M.self_survival(R, R, frozenset())
    assert n == 1.0 and s == 1.0
    # against an unrelated table both survivals are low
    _, _, _, noise = synthetic()
    noise.name = np.array([f"other_{i}_zz" for i in range(len(noise.loc))])
    n2, s2 = M.self_survival(R, noise, frozenset())
    assert n2 == 0.0 and s2 < 0.1
