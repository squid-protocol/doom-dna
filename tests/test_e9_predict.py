"""Synthetic tests for measure/e9_predict.py. Only synthetic tables, plus one E7 phase A reproduction (a known number)."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e9_predict", ROOT / "measure" / "e9_predict.py")
P = importlib.util.module_from_spec(spec)
sys.modules["e9_predict"] = P
spec.loader.exec_module(P)
from structural_fingerprint.fingerprint import FunctionTable  # noqa: E402
from structural_fingerprint.twins import TwinParams  # noqa: E402

GEOM = ((0, 1, 2), np.ones(3))


def table(repo, names, loc, vectors=None, keys=None, seed=0):
    n = len(names)
    rng = np.random.default_rng(seed)
    return FunctionTable(repo=repo, name=np.array(names, dtype=str), path=np.array(["x.c"] * n, dtype=str),
                         language=np.array(["c"] * n, dtype=str), loc=np.asarray(loc, dtype=np.int32),
                         archetype=np.zeros(n, dtype=np.int16),
                         key=np.asarray(keys if keys is not None else rng.integers(1, 2**62, n), dtype=np.uint64),
                         vectors=(vectors if vectors is not None else rng.normal(size=(n, 6))).astype(np.float32), edges=None)


def funcs_for(tabs, vertical=None):
    rows = []
    for prog, t in tabs.items():
        for i in range(len(t)):
            rows.append(dict(program=prog, func_id=f"{prog}#{i}", engine_row=i, vertical=int(i in (vertical or {}).get(prog, ())),
                             vertical_namekey=0, dup_rep=f"{prog}#{i}"))
    return P.Funcs(pd.DataFrame(rows))


def noise_pool(seed=5, n_prog=8, n=300, vocab=2000):
    rng = np.random.default_rng(seed)
    tabs = {}
    for k in range(n_prog):
        nm = [f"word{j}x" for j in rng.integers(0, vocab, n)]
        tabs[f"pool{k}"] = table(f"pool{k}", nm, np.full(n, 10), seed=k)
    return P.NamePool(tabs, frozenset()), tabs


# ------------------------------------------------------------------------------------------------ names
def test_names_unique_key_emission_and_stoplist():
    a = table("A", ["alpha_one", "beta_two", "dup_key", "dup_key", "stopword", "tiny", "p_gamma_long"], [10, 10, 10, 10, 10, 3, 10])
    b = table("B", ["AlphaOne", "beta_two", "dup_key", "other", "stopword", "tiny", "x"], [10, 10, 10, 10, 10, 10, 10])
    va, vb = P.make_view(a), P.make_view(b)
    got = P.names_unique_pairs(va, vb, P.N.name_key, frozenset({"stopword"}))
    keys = {k for *_, k in got}
    assert keys == {"alphaone", "betatwo"}            # dup_key has n_A = 2; stopword removed; tiny: loc 3 on A is ineligible
    assert all(i != 3 for i, _, _ in got)
    multi, omitted = P.names_multi_pairs(va, vb, P.N.name_key, frozenset({"stopword"}))
    assert sorted((x, y) for x, y, *_ in multi) == [(2, 2), (3, 2)] and omitted == 0
    assert all(m == 2 for *_, m in multi)


def test_names_n2_prefix_strip_emits_reprefixed():
    a = table("A", ["P_ChangeSector"], [10])
    b = table("B", ["ChangeSector"], [10])
    va, vb = P.make_view(a), P.make_view(b)
    assert P.names_unique_pairs(va, vb, P.N.name_key, frozenset()) == []
    got = P.names_unique_pairs(va, vb, P.N.name_key_n2, frozenset())
    assert [(x, y) for x, y, _ in got] == [(0, 0)]


def test_decoy_gate_certifies_shared_and_rejects_chance():
    pool, _ = noise_pool()
    rng = np.random.default_rng(11)
    shared = [f"shared_fn_{i}_q" for i in range(150)]
    own = lambda: [f"word{j}x" for j in rng.integers(0, 2000, 300)]
    ta = table("A", shared + own(), np.full(450, 10))
    tb = table("B", shared + own(), np.full(450, 10))
    g = pool.gate("A", "B", ta, tb)
    assert g["certified"] == 1 and g["decoy_ge"] <= 1
    tc = table("C", own(), np.full(300, 10))
    td = table("D", own(), np.full(300, 10))
    g2 = pool.gate("C", "D", tc, td)
    assert g2["certified"] == 0 and g2["matched"] > 0


# ------------------------------------------------------------------------------------------------ structure
def make_clone_world(n_copy=150, n_other=60, seed=1):
    rng = np.random.default_rng(seed)
    vec = rng.normal(size=(n_copy, 6)) * 3
    keys = rng.integers(1, 2**62, n_copy)
    ta = table("A", [f"copy_{i}" for i in range(n_copy)] + [f"a_only_{i}" for i in range(n_other)], np.r_[np.full(n_copy, 20), np.full(n_other, 8)],
               vectors=np.vstack([vec, rng.normal(size=(n_other, 6)) * 3]), keys=np.r_[keys, rng.integers(1, 2**62, n_other)])
    perm = rng.permutation(n_copy)
    tb = table("B", [f"copy_{i}" for i in perm] + [f"b_only_{i}" for i in range(n_other)], np.r_[np.full(n_copy, 20), np.full(n_other, 8)],
               vectors=np.vstack([vec[perm], rng.normal(size=(n_other, 6)) * 3]), keys=np.r_[keys[perm], rng.integers(1, 2**62, n_other)])
    return ta, tb, perm


def test_structure_union_and_post_hoc_vertical_filter():
    ta, tb, perm = make_clone_world()
    va, vb = P.make_view(ta), P.make_view(tb)
    pairs, diag = P.struct_union(va, vb, TwinParams(min_loc=6))
    truth = {(i, int(np.flatnonzero(perm == i)[0])) for i in range(150)}
    assert truth <= set(pairs)
    assert diag["k_union"] >= 150 and diag["twins_ab"] >= 150 and diag["twins_ba"] >= 150
    # union is no larger than the sum and no smaller than either direction
    assert max(diag["twins_ab"], diag["twins_ba"]) <= diag["k_union"] <= diag["twins_ab"] + diag["twins_ba"]
    pool, _ = noise_pool()
    tabs = {"A": ta, "B": tb}
    vert = {"A": {0, 1, 2}, "B": {int(np.flatnonzero(perm == 5)[0])}}
    funcs = funcs_for(tabs, vert)
    preds, diags = P.process_pair("A", "B", ta, tb, funcs, pool, TwinParams(min_loc=6), frozenset(), GEOM)
    prim = {(r[3], r[5]) for r in preds if r[0] == "structure" and r[1] == "primary"}
    assert (0, int(np.flatnonzero(perm == 0)[0])) not in prim and (1, int(np.flatnonzero(perm == 1)[0])) not in prim
    assert (5, int(np.flatnonzero(perm == 5)[0])) not in prim            # vertical on the B side
    assert (10, int(np.flatnonzero(perm == 10)[0])) in prim
    assert len(prim) == len({(a, b) for (a, b) in pairs if not (a in vert["A"] or b in vert["B"])})
    pre = {(r[3], r[5]) for r in preds if r[0] == "structure" and r[1] == "premasked"}
    assert (10, int(np.flatnonzero(perm == 10)[0])) in pre
    assert not any(a in vert["A"] or b in vert["B"] for a, b in pre)
    assert all(r[7] == 1 for r in preds if r[0] == "structure")


def test_dedup_variant_drops_non_representatives():
    ta, tb, perm = make_clone_world()
    tabs = {"A": ta, "B": tb}
    rows = []
    for prog, t in tabs.items():
        for i in range(len(t)):
            rows.append(dict(program=prog, func_id=f"{prog}#{i}", engine_row=i, vertical=0, vertical_namekey=0,
                             dup_rep=f"{prog}#0" if (prog == "A" and i in (3, 4)) else f"{prog}#{i}"))
    funcs = P.Funcs(pd.DataFrame(rows))
    pool, _ = noise_pool()
    preds, diags = P.process_pair("A", "B", ta, tb, funcs, pool, TwinParams(min_loc=6), frozenset(), GEOM)
    dd = {r[3] for r in preds if r[1] == "dedup" and r[0] == "structure"}
    pr = {r[3] for r in preds if r[1] == "primary" and r[0] == "structure"}
    assert 3 not in dd and 4 not in dd and 3 in pr and 4 in pr
    assert {d["variant"] for d in diags} == {"primary", "dedup"}


# ------------------------------------------------------------------------------------------------ R1 and geometry
def test_r1_without_replacement_and_deciles_with_fallback():
    rng = np.random.default_rng(3)
    loc_a = rng.integers(6, 100, 200)
    loc_b = rng.integers(6, 30, 200)       # B has nothing in A's upper deciles after pooling: forces fallback
    out = P.r1_pairs(np.arange(200), loc_a, np.arange(1000, 1200), loc_b, 40, seed=9)
    assert len(out) == 40
    assert len({a for a, _, _ in out}) == 40 and len({b for _, b, _ in out}) == 40     # without replacement on both sides
    assert out == P.r1_pairs(np.arange(200), loc_a, np.arange(1000, 1200), loc_b, 40, seed=9)   # seeded
    assert out != P.r1_pairs(np.arange(200), loc_a, np.arange(1000, 1200), loc_b, 40, seed=10)
    edges = P.loc_deciles(np.concatenate([loc_a, loc_b]))
    da = dict(zip(range(200), P.decile_of(edges, loc_a)))
    db = dict(zip(range(1000, 1200), P.decile_of(edges, loc_b)))
    same = sum(da[a] == db[b] for a, b, _ in out)
    assert same >= 1
    # when B has no function in the decile, the nearest decile is used (never a farther one while a nearer one has stock)
    a_hi = [(a, b) for a, b, _ in out if da[a] > max(db.values())]
    for a, b in a_hi:
        assert db[b] >= max(set(db.values())) - 3


def test_r1_budget_floor_and_exhaustion():
    out = P.r1_pairs(np.arange(3), np.array([10, 20, 30]), np.arange(3), np.array([10, 20, 30]), 5, 1)
    assert len(out) == 3                                      # cannot exceed the smaller side
    assert P.r1_pairs([], np.array([]), [1], np.array([10]), 5, 1) == []


def test_budget_rule_in_process_pair():
    ta, tb, perm = make_clone_world(n_copy=150, n_other=60)
    funcs = funcs_for({"A": ta, "B": tb})
    pool, _ = noise_pool()
    preds, diags = P.process_pair("A", "B", ta, tb, funcs, pool, TwinParams(min_loc=6), frozenset(), GEOM)
    d = [x for x in diags if x["variant"] == "primary"][0]
    assert d["budget"] == max(d["k_struct"], d["k_names"], 5)
    r1 = [r for r in preds if r[0] == "r1" and r[1] == "primary"]
    assert len(r1) == d["budget"]
    # floor of 5: two tiny, unrelated tables
    t1 = table("C", [f"qq_{i}" for i in range(40)], np.full(40, 10), seed=4)
    t2 = table("D", [f"zz_{i}" for i in range(40)], np.full(40, 10), seed=5)
    preds, diags = P.process_pair("C", "D", t1, t2, funcs_for({"C": t1, "D": t2}), pool, TwinParams(min_loc=6), frozenset(), GEOM)
    d = [x for x in diags if x["variant"] == "primary"][0]
    assert d["budget"] == max(d["k_struct"], d["k_names"], 5)
    assert d["budget"] >= 5
    assert len([r for r in preds if r[0] == "r1" and r[1] == "primary"]) == d["budget"]


def test_geometry_reciprocal_nearest_neighbours():
    xa = np.array([[0, 0, 0], [10, 10, 10], [20, 20, 20.0]])
    xb = np.array([[0.1, 0, 0], [10.4, 10, 10], [5, 5, 5], [40, 40, 40.0]])
    out = P.geometry_pairs(np.array([100, 101, 102]), xa, np.array([200, 201, 202, 203]), xb, 10)
    # a0<->b0 and a1<->b1 are reciprocal; a2's nearest is b3 (distance 34) while b3's nearest is a2: also reciprocal
    got = {(a, b) for a, b, _ in out}
    assert (100, 200) in got and (101, 201) in got
    assert (100, 202) not in got
    assert [d for *_, d in out] == sorted(d for *_, d in out)
    cut = P.geometry_pairs(np.array([100, 101, 102]), xa, np.array([200, 201, 202, 203]), xb, 1)
    assert cut == out[:1] and cut[0][:2] == (100, 200)
    assert P.geometry_pairs([], np.zeros((0, 3)), [1], np.zeros((1, 3)), 3) == []


# ------------------------------------------------------------------------------------------------ plumbing
def test_funcs_mapping_and_pair_lists(tmp_path):
    f = pd.DataFrame(dict(program=["A", "A", "A"], func_id=["a1", "a2", "a3"], engine_row=[0, 1, -1], vertical=["1", "0", "0"],
                          vertical_namekey=["0", "1", "0"], dup_rep=["a1", "a1", "a3"]))
    fu = P.Funcs(f)
    assert fu.fid("A", 0) == "a1" and fu.fid("A", 5) == "row:5" and fu.fid("SPIKE", 7) == "7"
    assert list(fu.flag(fu.vertical, "A", 3)) == [True, False, False]
    assert list(fu.flag(fu.vnk, "A", 3)) == [False, True, False]
    assert list(fu.flag(fu.nonrep, "A", 3)) == [False, True, False]
    pairs = pd.DataFrame(dict(prog_a=["b", "a", "c"], prog_b=["a", "b", "d"], eligible_primary=["1", "0", "0"]))
    assert P.eligible_port_pairs(pairs) == [("a", "b")]
    cp = P.control_pairs()
    assert ("nginx", "woof") in cp and all(len(x) == 2 for x in cp)
    assert not any(a in P.NEGATIVES and b in P.NEGATIVES for a, b in cp)
    (tmp_path / "spike_truth.csv").write_text("tier,module_size,donor,recipient_program,donor_func_id,recipient_func_name,recipient_engine_row\n"
                                              "a,150,curl,spike-a,f1,x,3\nc,150,curl,spike-c,f1,x,3\n")
    assert P.spike_pairs(tmp_path) == [("curl", "spike-a"), ("curl", "spike-c")]


# ------------------------------------------------------------------------------------------------ E7 reproduction (known number)
@pytest.mark.skipif(not (P.FP_A / "linuxdoom.sfp.npz").exists(), reason="E7 phase A fingerprints not available")
def test_reproduces_e7_linuxdoom_chocolate_counts():
    stop = P.load_stoplist()
    tq, tt = P.load_table("linuxdoom", [P.FP_A]), P.load_table("chocolate-doom", [P.FP_A])
    ne = pd.read_csv(P.E7_A / "pairs_names.csv")
    ns = pd.read_csv(P.E7_A / "pairs_struct.csv")
    en = ne[(ne.q == "linuxdoom") & (ne.t == "chocolate-doom")].iloc[0]
    es = ns[(ns.q == "linuxdoom") & (ns.t == "chocolate-doom")].iloc[0]
    assert P.names_matched_count(tq, tt, stop) == int(en.matched) == 572
    r = P.find_twins(tq, tt, TwinParams(min_loc=P.ELIG))
    assert r.accepted == int(es.twins) == 385
    pairs, diag = P.struct_union(P.make_view(tq), P.make_view(tt), TwinParams(min_loc=P.ELIG))
    assert diag["twins_ab"] == 385                        # the A -> B direction of the union is the E7 call
    assert diag["k_union"] >= 385
