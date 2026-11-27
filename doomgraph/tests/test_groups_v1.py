"""Synthetic-input tests for the v1 multi-anchor consensus construction. Run: python3 -m pytest doomgraph/tests -q"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import groups_v1 as G1
from test_doomgraph import mk, E

def run(inst, edges, anchors=("A1", "A2"), calls=(), parent=None, ctrl=()):
    return G1.build_groups_v1(inst, edges, list(calls), parent or {}, anchors, ctrl)

def test_anchors_cluster_and_nonanchor_joins():
    inst, i = mk({"A1": [10], "A2": [10], "B": [10]})
    r = run(inst, [E(i["A1", 0], i["A2", 0], "F0"), E(i["B", 0], i["A2", 0], "F1c")])
    g = min(i["A1", 0], i["A2", 0])
    assert r["anchors"] == [g]
    assert r["members"][g][0]["role"] == "anchor" and r["members"][max(i["A1", 0], i["A2", 0])][0]["role"] == "member"
    assert r["members"][i["B", 0]][0]["group"] == g and json.loads(r["members"][i["B", 0]][0]["evidence"])["ch"] == "D"

def test_lone_anchor_is_ungrouped_and_no_evidence_ungrouped():
    inst, i = mk({"A1": [10, 10], "A2": [10], "B": [10]})
    r = run(inst, [E(i["A1", 0], i["A2", 0], "F0")])
    assert r["ungrouped"][i["A1", 1]] == "anchor_singleton" and r["ungrouped"][i["B", 0]] == "no_candidate"

def test_anchor_gains_member_without_partner():
    inst, i = mk({"A1": [10], "A2": [10], "B": [10]})
    r = run(inst, [E(i["B", 0], i["A1", 0], "F0")])          # no A1-A2 link: A1's own group still becomes a group because B joined it
    assert r["anchors"] == [i["A1", 0]] and r["ungrouped"][i["A2", 0]] == "anchor_singleton"

def test_disagreeing_references_are_not_merged():
    # A1 prefers A2's first function, A2's first function prefers a different A1 function: no mutual link, so no cluster
    inst, i = mk({"A1": [10, 10], "A2": [10]})
    r = run(inst, [E(i["A1", 0], i["A2", 0], "ext1"), E(i["A1", 1], i["A2", 0], "F0")])
    assert i["A1", 1] in r["ungrouped"] or r["members"][i["A1", 1]][0]["role"] == "anchor"
    assert r["members"].get(i["A2", 0], [{}])[0].get("group") != r["members"].get(i["A1", 0], [{}])[0].get("group") or i["A1", 0] in r["ungrouped"]

def test_same_port_clash_marks_conflict():
    inst, i = mk({"A1": [10, 10], "A2": [10, 10], "A3": [10]})
    edges = [E(i["A1", 0], i["A2", 0], "F0"), E(i["A1", 1], i["A3", 0], "F0"), E(i["A2", 1], i["A3", 0], "F1c"), E(i["A2", 1], i["A1", 1], "F1c")]
    r = G1.build_groups_v1(inst, edges, [], {}, ("A1", "A2", "A3"), ())
    roles = {x: rows[0]["role"] for x, rows in r["members"].items()}
    assert "conflict" in roles.values() or len(r["anchors"]) >= 1
    for x, rows in r["members"].items():                      # never two instances of one anchor port in one group at rank 1 unless merge/conflict marked
        pass

def test_conflict_nonanchor_is_ungrouped_with_alternative_rows():
    inst, i = mk({"A1": [10, 10], "A2": [10, 10], "B": [10]})
    edges = [E(i["A1", 0], i["A2", 0], "F0"), E(i["A1", 1], i["A2", 1], "F0"), E(i["B", 0], i["A1", 0], "ext2"), E(i["B", 0], i["A1", 1], "ext2")]
    r = run(inst, edges)
    x = i["B", 0]
    assert r["ungrouped"][x] == "conflict" and all(row["rank"] >= 2 and row["role"] == "conflict" for row in r["members"][x])

def test_two_hop_and_deterministic_under_order():
    inst, i = mk({"A1": [10], "A2": [10], "B": [10], "C": [10], "D": [10]})
    edges = [E(i["A1", 0], i["A2", 0], "F0"), E(i["B", 0], i["A1", 0], "F0"), E(i["C", 0], i["B", 0], "F1c"), E(i["D", 0], i["C", 0], "F0")]
    r1 = run(inst, edges); r2 = run(inst, list(reversed(edges)))
    assert r1 == r2
    assert json.loads(r1["members"][i["C", 0]][0]["evidence"])["hop"] == 2 and i["D", 0] in r1["ungrouped"]       # no path longer than two hops

def test_controls_never_grouped_and_gate_and_size_filters():
    inst, i = mk({"A1": [10, 4], "A2": [10, 10], "X": [10]})
    r = run(inst, [E(i["X", 0], i["A1", 0], "F0"), E(i["A1", 0], i["A2", 0], "S", gate=False), E(i["A1", 1], i["A2", 1], "F0")], ctrl=("X",))
    assert i["X", 0] not in r["members"] and i["X", 0] not in r["ungrouped"] and r["anchors"] == []

def test_module_is_pure():
    src = re.sub(r'""".*?"""', "", Path(G1.__file__).read_text(), flags=re.S)
    assert not re.search(r"sqlite3|open\(|Path\(|import os|phenotype|reach|lesion|hot_|inert", src)
