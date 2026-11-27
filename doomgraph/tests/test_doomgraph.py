"""Tests on small synthetic inputs (no scans, no stores). Run: python3 -m pytest doomgraph/tests -q"""
import csv, json, re, sqlite3, sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common as C
import groups as G
import audit as AU
import build_static as BS
import build_behaviour as BB

def mk(ports):
    """ports: {port: [size,...]} -> (instances, id map)"""
    inst, ids, n = {}, {}, 0
    for p, sizes in ports.items():
        for k, sz in enumerate(sizes):
            n += 1; inst[n] = dict(port=p, size=sz); ids[(p, k)] = n
    return inst, ids

def E(a, b, tier, source="e12", gate=True, verdict=None):
    return dict(a=min(a, b), b=max(a, b), tier=tier, source=source, gate=gate, verdict=verdict)

def run(inst, edges, calls=(), parent=None, anchor="A", ctrl=()):
    return G.build_groups(inst, edges, list(calls), parent or {}, anchor, ctrl)

def test_direct_name_and_hop2_join():
    inst, i = mk({"A": [10, 10, 10], "B": [10, 10], "C": [10], "D": [10]})
    edges = [E(i["B", 0], i["A", 0], "F0"), E(i["C", 0], i["A", 1], "NAME", "name"), E(i["D", 0], i["B", 1], "F1c"), E(i["B", 1], i["A", 2], "F0")]
    r = run(inst, edges)
    m = {x: rows[0] for x, rows in r["members"].items()}
    assert m[i["B", 0]]["group"] == i["A", 0] and json.loads(m[i["B", 0]]["evidence"])["ch"] == "D"
    assert m[i["C", 0]]["group"] == i["A", 1] and json.loads(m[i["C", 0]]["evidence"])["ch"] == "N"
    assert m[i["D", 0]]["group"] == i["A", 2] and json.loads(m[i["D", 0]]["evidence"])["hop"] == 2
    assert r["anchors"] == sorted(i["A", k] for k in range(3))

def test_gate_and_small_functions_excluded():
    inst, i = mk({"A": [10, 4], "B": [10, 10]})
    edges = [E(i["B", 0], i["A", 0], "S", gate=False), E(i["B", 1], i["A", 1], "F0")]   # failed gate for S; anchor end under 6 lines
    r = run(inst, edges)
    assert r["members"] == {} and set(r["ungrouped"]) == {i["B", 0], i["B", 1]}

def test_no_path_longer_than_two_hops():
    inst, i = mk({"A": [10], "B": [10], "C": [10], "D": [10]})
    edges = [E(i["B", 0], i["A", 0], "F0"), E(i["C", 0], i["B", 0], "F0"), E(i["D", 0], i["C", 0], "F0")]
    r = run(inst, edges)
    assert i["C", 0] in r["members"] and i["D", 0] not in r["members"] and r["ungrouped"][i["D", 0]] == "no_candidate"

def test_controls_and_anchor_never_grouped():
    inst, i = mk({"A": [10], "X": [10], "B": [10]})
    r = run(inst, [E(i["X", 0], i["A", 0], "F0"), E(i["B", 0], i["A", 0], "F0")], ctrl=("X",))
    assert i["X", 0] not in r["members"] and i["X", 0] not in r["ungrouped"] and i["B", 0] in r["members"]

def test_merge_role_and_conflict_role():
    inst, i = mk({"A": [10, 10], "B": [10, 10, 10]})
    edges = [E(i["B", 0], i["A", 0], "F0"), E(i["B", 1], i["A", 0], "ext1"),      # merge: two B functions in one group
             E(i["B", 2], i["A", 0], "S"), E(i["B", 2], i["A", 1], "NAME", "name")]  # 60 vs 25 -> weaker dissent: no conflict, alternative row kept
    r = run(inst, edges)
    assert {r["members"][i["B", 0]][0]["role"], r["members"][i["B", 1]][0]["role"]} == {"merge"}
    assert r["members"][i["B", 2]][0]["role"] == "merge" and len(r["members"][i["B", 2]]) == 2
    inst, i = mk({"A": [10, 10], "B": [10, 10]})
    r = run(inst, [E(i["B", 0], i["A", 0], "ext1"), E(i["B", 0], i["A", 1], "NAME", "name")])   # 40 vs 25: 25 < 0.8*40 -> member
    assert r["members"][i["B", 0]][0]["role"] == "member"
    r = run(inst, [E(i["B", 0], i["A", 0], "ext2"), E(i["B", 0], i["A", 1], "NAME", "name")])   # 30 vs 25: comparable -> conflict, both rows kept
    assert [x["role"] for x in r["members"][i["B", 0]]] == ["conflict", "conflict"]

def test_split_by_arbiter_and_confirmation_only():
    inst, i = mk({"A": [10, 10], "B": [10, 10]})
    edges = [E(i["B", 0], i["A", 0], "F0"), E(i["B", 0], i["A", 1], "TXT", "e7_arbiter", verdict="near"), E(i["B", 1], i["A", 1], "TXT", "e7_arbiter", verdict="exact")]
    r = run(inst, edges)
    assert i["B", 1] not in r["members"]                         # arbiter alone never creates membership
    rows = r["members"][i["B", 0]]
    assert rows[0]["group"] == i["A", 0] and json.loads(rows[0]["evidence"])["chs"] == "D"

def test_deterministic_under_input_order_and_tiebreak_by_calls():
    inst, i = mk({"A": [10, 10, 10, 10], "B": [10, 10, 10]})
    # B0 ties between A0 and A1 (same tier); B1 and B2 pin down the neighbourhood: B0 calls B1 which sits in A2, A2 calls A1
    edges = [E(i["B", 0], i["A", 0], "ext1"), E(i["B", 0], i["A", 1], "ext1"), E(i["B", 1], i["A", 2], "F0")]
    calls = [(i["B", 0], i["B", 1]), (i["A", 2], i["A", 1])]
    r1 = run(inst, edges, calls)
    r2 = run(inst, list(reversed(edges)), list(reversed(calls)))
    assert r1 == r2
    assert r1["members"][i["B", 0]][0]["group"] == i["A", 1]       # call support breaks the tie
    r3 = run(inst, edges, [])
    assert r3["members"][i["B", 0]][0]["group"] == i["A", 0]       # no support -> lower anchor id

def test_lineage_tiebreak_prefers_lineage_consistent_path():
    inst, i = mk({"A": [10, 10], "B": [10], "C": [10], "D": [10]})
    edges = [E(i["D", 0], i["B", 0], "F0"), E(i["B", 0], i["A", 0], "F0"), E(i["D", 0], i["C", 0], "F0"), E(i["C", 0], i["A", 1], "F0")]
    r = run(inst, edges, parent={"D": "C"})
    assert r["members"][i["D", 0]][0]["group"] == i["A", 1]

def test_group_inputs_carry_no_behaviour_and_module_is_pure():
    src = Path(G.__file__).read_text()
    assert not re.search(r"sqlite3|open\(|Path\(|import os|phenotype|reach|lesion|hot_|inert", re.sub(r'""".*?"""', "", src, flags=re.S))
    inst, i = mk({"A": [10], "B": [10]})
    assert set(inst[1]) == {"port", "size"}

def test_ari():
    assert AU.ari([1, 1, 2, 2], [5, 5, 7, 7]) == pytest.approx(1.0)
    assert AU.ari([1, 1, 2, 2], [1, 2, 1, 2]) < 0.1

def test_strip_name_rule():
    assert C.strip_name("P_Move") == "Move" and C.strip_name("A_Chase") == "Chase" and C.strip_name("PIT_CheckLine") == "CheckLine" and C.strip_name("R_Draw") == "R_Draw"

def static_db(tmp_path):
    db = sqlite3.connect(tmp_path / "s.sqlite"); db.executescript(C.STATIC_DDL)
    db.execute("insert into port values (1,'p','c','port','704cb35f0/p','abc','704cb35f0','00','11',2,2,'scan','b')")
    return db

def test_schema_keys_and_constraints(tmp_path):
    db = static_db(tmp_path)
    for k in (1, 2): db.execute("insert into instance values (?,1,?,?, 'n', 'f.c', 1, 10, 0, 0, 'c', 'scan', 'b')", (k, k, f"key{k}"))
    db.execute("insert into match_edge(a_inst,b_inst,tier,score,source,build_id) values (1,2,'F0',1.0,'e12','b')")
    with pytest.raises(sqlite3.IntegrityError): db.execute("insert into match_edge(a_inst,b_inst,tier,score,source,build_id) values (2,1,'F0',1.0,'e12','b')")      # canonical order
    with pytest.raises(sqlite3.IntegrityError): db.execute("insert into match_edge(a_inst,b_inst,tier,score,source,build_id) values (1,2,'F0',1.0,'e12','b')")      # unique
    db.execute("insert into ortholog_group values (1,'full',1,'m','g1',1,1,'b')")
    with pytest.raises(sqlite3.IntegrityError): db.execute("insert into membership values (2,1,'full',1,'bogus',1.0,'{}','b')")
    db.execute("pragma foreign_keys=on")
    assert db.execute("select count(*) from sqlite_master where name in ('build_manifest','holdout_fold','layer_availability')").fetchone()[0] >= 2
    assert {c[1] for c in db.execute("pragma table_info(instance)")} >= {"inst_id", "fid", "instance_key"}
    assert {c[1] for c in db.execute("pragma table_info(match_edge)")} >= {"edge_id", "gate_passed"}
    assert {c[1] for c in db.execute("pragma table_info(membership)")} >= {"role", "build_scope"}

def test_allowlist_rejects_long_text_and_newlines(tmp_path):
    db = static_db(tmp_path)
    BS.check_allowlist(db)
    db.execute("insert into instance values (1,1,1,'k','n','f.c',1,10,0,0,'c','scan','b')"); BS.check_allowlist(db)
    db.execute("update instance set name=?", ("x" * 201,))
    with pytest.raises(SystemExit): BS.check_allowlist(db)
    db.execute("update instance set name='a\nb'")
    with pytest.raises(SystemExit): BS.check_allowlist(db)
    db.execute("update instance set name='ok'"); db.execute("insert into ortholog_group values (1,'full',1,'m','g1',1,1,'b')")
    db.execute("insert into membership values (1,1,'full',1,'anchor',1.0,?, 'b')", ("{" + '"s":"' + "y" * 300 + '"}',))
    with pytest.raises(SystemExit): BS.check_allowlist(db)

def test_boundary_guards(tmp_path):
    with pytest.raises(PermissionError): sqlite3.connect(str(tmp_path / "doomgraph_behaviour.sqlite"))      # static build may not open behaviour/phenotype stores (BS guard is installed on import)
    with pytest.raises(PermissionError): BB._guard("/x/screen/jv_v2/store.sqlite")                               # behaviour build may not open E17 stores
    with pytest.raises(PermissionError): BB._guard("/x/results/e17/anything.sqlite")

def test_conformance_rows_from_synthetic_csv(tmp_path):
    (tmp_path / "phase1_gore_chaos200.csv").write_text("demo,map,skill,strict_tic,strict_field,gameplay_tic,gameplay_field\ng0000,6,2,6,prndindex,6,prndindex\ng0001,4,4,,,,\n")
    (tmp_path / "phase0_random_demo_matrix.csv").write_text("demo,skill,map,engine,status,tic,field,tics,ref_tics\ng0000,1,2,choc,identical,,,4000,4000\n")
    rows = BB.conformance_rows(tmp_path, "b")
    d = {(r[0], r[1], r[2]): r for r in rows}
    assert d[("gore", "g0000", "chaos200:strict")][3:6] == ("diverged", 6, "prndindex")
    assert d[("gore", "g0001", "chaos200:gameplay")][3] == "identical"
    assert d[("chocolate-doom", "g0000", "random300:matrix")][3] == "identical"

def test_audit_loads_group_inputs_from_static_db(tmp_path):
    db = static_db(tmp_path)
    db.execute("insert into lineage_edge(port,parent,parent_kind,basis,source,build_id) values ('p','linuxdoom','port','explicit','x','b')")
    db.execute("insert into lineage_edge(port,parent,parent_kind,basis,source,build_id) values ('q','linuxdoom','port','dropped','x','b')")
    insts, edges, calls, parent = AU.load_inputs(db)
    assert parent == {"p": "linuxdoom"} and insts == {} and edges == [] and calls == []
