"""Tests for measure/e7_trees.py on small synthetic trees (plus a real-csv sanity check)."""
import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "measure"))
import e7_trees as T  # noqa: E402

PROGRAMS = ["R", "A", "B", "C", "D", "E", "X", "Y", "W", "Z", "FX"]
# R root; A,D under R; B,C under A; E under D; W root (second top-level) with child Z;
# X, Y, unparented. FX is excluded (freedoom-like, via basis 'excluded').
LINEAGE = [("A", "R"), ("D", "R"), ("B", "A"), ("C", "A"), ("E", "D"), ("Z", "W"),
           ("FX", "R"), ("C", "Q")]
BASIS = [("A", "R", "explicit"), ("D", "R", "explicit"), ("B", "A", "explicit"),
         ("C", "A", "inferred"), ("E", "D", "collapsed"), ("Z", "W", "explicit"),
         ("FX", "R", "excluded"), ("C", "Q", "dropped")]


@pytest.fixture()
def declared(tmp_path):
    return _build(tmp_path)


def _build(tmp_path, explicit_only=False, programs=PROGRAMS):
    lin, bas = tmp_path / "lin.csv", tmp_path / "bas.csv"
    lin.write_text("name,parent\n" + "".join(f"{c},{p}\n" for c, p in LINEAGE))
    bas.write_text("name,parent,basis,reason,manifest_lineage_text\n"
                   + "".join(f"{c},{p},{b},r,t\n" for c, p, b in BASIS))
    return T.build_declared(lin, bas, programs, explicit_only=explicit_only)


def test_declared_structure(declared):
    d = declared
    assert "FX" not in d.leaves and "Q" not in d.leaves
    assert sorted(d.leaves) == sorted(set(PROGRAMS) - {"FX"})
    assert d.declared_parent["C"] == "A"           # dropped edge Q ignored
    assert d.declared_parent["X"] == T.ROOT
    assert d.ancestors("B") == {"A", "R"}
    assert d.descendants("R") == {"A", "B", "C", "D", "E"}
    assert d.roots == ("R", "W")
    assert d.clades() == {frozenset("RABCDE"), frozenset("ABC"), frozenset("DE"), frozenset("WZ")}


def test_sampled_ancestor_pendant_leaf(declared):
    # R is both an internal node and a pendant leaf: clade RABCDE contains leaf R
    assert "R" in declared.names.values()
    assert ("n", "R") in declared.children
    assert ("l", "R") in declared.children[("n", "R")]


def test_declared_triplets(declared):
    t = declared.triplets()
    assert ("B", "C", "D") in t
    # sampled ancestor A with children B, C is a polytomy: BC|A is NOT declared
    assert ("B", "C", "A") not in t and not any(set(x) == {"A", "B", "C"} for x in t)
    assert ("D", "E", "A") in t
    assert ("A", "B", "D") in t          # AB|D: A is an ancestor-side of B, D on other branch
    assert ("A", "D", "X") in t
    assert ("B", "C", "X") in t
    # polytomy under R is unresolved wrt R: R,A,D: A and D hang off R's node with R's leaf
    assert not any(set(x) == {"R", "A", "D"} for x in t)
    assert not any(set(x) == {"X", "Y", "A"} for x in t)   # root polytomy


def test_explicit_only(tmp_path):
    d = _build(tmp_path, explicit_only=True)
    assert d.declared_parent["C"] == T.ROOT      # inferred dropped
    assert d.declared_parent["E"] == T.ROOT      # collapsed dropped
    assert d.declared_parent["B"] == "A"
    assert frozenset("ABC") not in d.clades()
    assert frozenset("AB") in d.clades()
    assert "D" in d.leaves                        # D still has child? no: E dropped -> plain leaf under R
    assert frozenset("DE") not in d.clades()


def test_missing_basis_row_raises(tmp_path):
    lin, bas = tmp_path / "l.csv", tmp_path / "b.csv"
    lin.write_text("name,parent\nA,R\n")
    bas.write_text("name,parent,basis\n")
    with pytest.raises(ValueError):
        T.build_declared(lin, bas, ["A", "R"])


def test_extra_basis_edge_used(tmp_path):
    lin, bas = tmp_path / "l.csv", tmp_path / "b.csv"
    lin.write_text("name,parent\nA,R\n")
    bas.write_text("name,parent,basis\nA,R,explicit\nBF,R,inferred\n")
    assert T.build_declared(lin, bas, ["A", "R", "BF"]).declared_parent["BF"] == "R"
    assert T.build_declared(lin, bas, ["A", "R", "BF"], explicit_only=True).declared_parent["BF"] == T.ROOT


# ---- Newick / NJ

MATCH = "(((B,C,A),(D,E),R),(W,Z),X,Y);"
MATCH_BIN = "(((((B,C),A),(D,E)),R),((W,Z),(X,Y)));"
MISMATCH = "(((B,D),(A,E)),((C,R),(W,X)),(Z,Y));"
L10 = sorted(set(PROGRAMS) - {"FX"})


def test_parse_newick_basic():
    t = T.parse_newick("('a b':1.5,(c:0.1,d:2e-1):0.3,e);")
    assert t.leaves == ["a b", "c", "d", "e"]
    assert t.clades() == {frozenset("cd")}
    assert T.parse_newick("((a,b),(c,d));").bipartitions() == {frozenset("ab")} or \
        T.parse_newick("((a,b),(c,d));").bipartitions() == {frozenset("cd")}


def test_clade_recall_and_triplets(declared):
    for nw, rec in [(MATCH, 1.0), (MATCH_BIN, 1.0)]:
        t = T.parse_newick(nw)
        assert T.resolved_clade_recall(declared, t, L10) == 1.0
        assert T.resolved_triplet_compat(declared, t, L10) == 1.0
    m = T.parse_newick(MISMATCH)
    assert T.resolved_clade_recall(declared, m, L10) < 0.5
    assert 0.0 <= T.resolved_triplet_compat(declared, m, L10) < 0.6


def test_recall_restricted_leaves(declared):
    t = T.parse_newick("((B,C),(D,E),(W,Z),A);")
    sub = ["A", "B", "C", "D", "E"]
    # declared restricted: ABC, DE and RABCDE -> ABCDE equals full set (dropped)
    assert T.resolved_clade_recall(declared, t, sub) == 0.5   # DE yes, ABC no
    t2 = T.parse_newick("(((B,C),A),(D,E),(W,Z));")
    assert T.resolved_clade_recall(declared, t2, sub) == 1.0


def test_unresolved_tree_triplets_not_satisfied(declared):
    star = T.parse_newick("(" + ",".join(L10) + ");")
    assert T.resolved_triplet_compat(declared, star, L10) == 0.0
    assert T.resolved_clade_recall(declared, star, L10) == 0.0


def test_tree_metrics_identity_and_symmetry():
    a = T.parse_newick("(((a,b),c),((d,e),(f,g)));")
    b = T.parse_newick("(((a,c),b),((d,f),(e,g)));")
    L = list("abcdefg")
    assert T.rf_unrooted(a, a, L) == 0
    assert T.quartet_distance(a, a, L) == 0
    assert T.triplet_distance(a, a, L) == 0
    for f in (T.rf_unrooted, T.quartet_distance, T.triplet_distance):
        assert f(a, b, L) == pytest.approx(f(b, a, L))
        assert 0 < f(a, b, L) <= 1


def test_quartet_known_value():
    a = T.parse_newick("((a,b),(c,d));")
    b = T.parse_newick("((a,c),(b,d));")
    assert T.quartet_distance(a, b, list("abcd")) == 1.0
    assert T.quartet_distance(a, T.parse_newick("(a,b,c,d);"), list("abcd")) == 1.0
    # rooting does not matter for quartets
    c = T.parse_newick("(a,(b,(c,d)));")
    assert T.quartet_distance(a, c, list("abcd")) == 0.0


def test_rf_unrooted_ignores_root_placement():
    a = T.parse_newick("(((a,b),c),(d,e));")
    b = T.parse_newick("((a,b),(c,(d,e)));")
    assert T.rf_unrooted(a, b, list("abcde")) == 0


def test_quartet_fifty_leaves_fast():
    import time
    rng = np.random.default_rng(1)
    names = [f"l{i}" for i in range(50)]
    m = rng.random((50, 50))
    m = m + m.T
    np.fill_diagonal(m, 0)
    a = T.parse_newick(T.upgma_newick(m, names))
    m2 = rng.random((50, 50))
    m2 = m2 + m2.T
    np.fill_diagonal(m2, 0)
    b = T.parse_newick(T.nj_newick(m2, names))
    t0 = time.time()
    q = T.quartet_distance(a, b, names)
    assert time.time() - t0 < 20
    assert 0.5 < q <= 1.0
    assert T.quartet_distance(a, a, names) == 0


def _path_dists(tree):
    names = tree.leaves
    pos = {n: k for k, n in enumerate(tree.names)}
    # lengths along root paths
    def up(n):
        out, acc = {}, 0.0
        while True:
            out[n] = acc
            if n == tree.root:
                break
            acc += tree.length.get(n, 0.0)
            n = tree.parent[n]
        return out
    nodes = {v: k for k, v in tree.names.items()}
    ups = {nm: up(nodes[nm]) for nm in names}
    d = np.zeros((len(names), len(names)))
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            common = [n for n in ups[a] if n in ups[b]]
            m = min(ups[a][n] + ups[b][n] for n in common)
            d[i, j] = m
    return names, d


def test_nj_recovers_additive_tree():
    truth = T.parse_newick("(((A:1,B:2):3,(C:4,D:1):1):2,E:2,(F:1.5,G:0.5):2.5);")
    names, d = _path_dists(truth)
    nj = T.parse_newick(T.nj_newick(d, names))
    assert T.rf_unrooted(truth, nj, names) == 0
    names2, d2 = _path_dists(nj)
    order = [names2.index(n) for n in names]
    assert np.allclose(d2[np.ix_(order, order)], d, atol=1e-4)


def test_nj_small_cases():
    assert T.parse_newick(T.nj_newick(np.zeros((1, 1)), ["a"])).leaves == ["a"]
    assert T.parse_newick(T.nj_newick(np.array([[0, 2.0], [2, 0]]), ["a", "b"])).leaves == ["a", "b"]
    t = T.parse_newick(T.nj_newick(np.array([[0, 1, 2.0], [1, 0, 3], [2, 3, 0]]), list("abc")))
    assert len(t.leaves) == 3


def test_root_at_leaf_gives_rooted_clades():
    nj = T.parse_newick("((a:1,b:1):1,c:1,(d:1,e:1):1);")
    r = T.root_at(nj, "c")
    cl = r.clades()
    assert frozenset("ab") in cl and frozenset("de") in cl
    assert sorted(r.leaves) == list("abcde")
    assert T.rf_unrooted(nj, r, list("abcde")) == 0
    with pytest.raises(ValueError):
        T.root_at(nj, "zzz")


def test_root_at_degree2_root():
    t = T.parse_newick("(((a,b),c),(d,e));")
    r = T.root_at(t, "a")
    assert frozenset("de") in r.clades()
    assert T.rf_unrooted(t, r, list("abcde")) == 0


def test_nj_rooted_at_linuxdoom_recovers_declared_clades(declared):
    # additive distances from the declared topology itself (every edge length 1, pendant leaves)
    tree = declared
    L = tree.leaves
    D, dep = tree.lca_depth(L)
    d = (dep[:, None] + dep[None, :] - 2 * D).astype(float)
    np.fill_diagonal(d, 0)
    nj = T.root_at(T.parse_newick(T.nj_newick(d, L)), "R")
    assert nj.leaves == L


# ---- distance-matrix metrics

def _mat(names, pairs, default=1.0):
    n = len(names)
    m = np.full((n, n), default)
    for (a, b), v in pairs.items():
        i, j = names.index(a), names.index(b)
        m[i, j] = m[j, i] = v
    np.fill_diagonal(m, 0)
    return m


def test_root_siblings_not_family_by_default(declared):
    names = ["R", "A", "B", "C", "D", "E", "X", "Y", "W", "Z"]
    # A's only close neighbour is D: they share parent R (top-level = root-like)
    m = _mat(names, {("A", "D"): 0.1})
    rows, rate = T.nearest_is_family(m, names, declared)
    ra = next(r for r in rows if r["name"] == "A")
    assert ra["nearest"] == ["D"] and ra["weight"] == 0.0
    rows2, rate2 = T.nearest_is_family(m, names, declared, include_root_siblings=True)
    ra2 = next(r for r in rows2 if r["name"] == "A")
    assert ra2["weight"] == 1.0 and ra2["relations"] == ["sibling"]
    # R and W only share the virtual root
    assert declared.relation("R", "W") == "other"
    assert declared.relation("R", "W", include_root_siblings=True) == "sibling"
    # unparented X,Y share only the virtual root
    assert declared.relation("X", "Y") == "other"
    assert declared.relation("X", "Y", include_root_siblings=True) == "sibling"
    assert rate2 > rate


def test_family_relations(declared):
    assert declared.relation("B", "C") == "sibling"       # shared non-root parent A
    assert declared.relation("B", "E") == "other"         # only common ancestor R is root-like
    assert declared.relation("B", "A") == "ancestor"
    assert declared.relation("A", "B") == "descendant"
    assert declared.relation("B", "R") == "ancestor"
    # cousin: shared non-root ancestor
    d_children = declared
    assert d_children.relation("B", "C") == "sibling"


def test_cousin(tmp_path):
    lin, bas = tmp_path / "l.csv", tmp_path / "b.csv"
    rows = [("a", "r"), ("b", "r"), ("c", "a"), ("d", "b"), ("e", "c"), ("f", "a"), ("g", "f")]
    lin.write_text("name,parent\n" + "".join(f"{c},{p}\n" for c, p in rows))
    bas.write_text("name,parent,basis\n" + "".join(f"{c},{p},explicit\n" for c, p in rows))
    d = T.build_declared(lin, bas, list("rabcdefg"))
    assert d.relation("e", "g") == "cousin"   # common ancestor a (non-root)
    assert d.relation("e", "d") == "other"    # only common ancestor r is root-like
    assert d.relation("c", "f") == "sibling"


def test_nearest_tie_averaging(declared):
    names = ["R", "A", "B", "C", "D", "E", "X", "Y", "W", "Z"]
    # A is equidistant to B (descendant, family) and D (other): weight 0.5
    m = _mat(names, {("A", "B"): 0.2, ("A", "D"): 0.2})
    rows, _ = T.nearest_is_family(m, names, declared)
    ra = next(r for r in rows if r["name"] == "A")
    assert sorted(ra["nearest"]) == ["B", "D"]
    assert ra["weight"] == 0.5


def test_nearest_skip_and_rate(declared):
    names = ["R", "A", "B", "C", "D", "E", "X", "Y", "W", "Z"]
    m = _mat(names, {("A", "B"): 0.1, ("B", "A"): 0.1, ("C", "B"): 0.1, ("D", "E"): 0.1,
                     ("R", "A"): 0.1, ("E", "D"): 0.1, ("W", "Z"): 0.1})
    rows, rate = T.nearest_is_family(m, names, declared)
    scored = {r["name"] for r in rows}
    assert "X" not in scored and "Y" not in scored      # no declared relatives
    assert rate == 1.0
    rows2, rate2 = T.nearest_is_family(m, names, declared, skip=["A"])
    assert "A" not in {r["name"] for r in rows2}


def test_parent_rank_with_descendant_exclusion_and_ties(declared):
    names = ["R", "A", "B", "C", "D", "E", "X", "Y", "W", "Z"]
    # For A (parent R): its own children B, C are closest but excluded; then X, then R.
    m = _mat(names, {("A", "B"): 0.01, ("A", "C"): 0.02, ("A", "X"): 0.3, ("A", "R"): 0.5},
             default=0.9)
    rows, mean, med = T.parent_rank(m, names, declared)
    ra = next(r for r in rows if r["name"] == "A")
    assert ra["rank"] == 2
    # tie: B (parent A) equidistant to A and C -> A shares rank with C (rank 1.5)
    m2 = _mat(names, {("B", "A"): 0.2, ("B", "C"): 0.2}, default=0.9)
    rows2, _, _ = T.parent_rank(m2, names, declared)
    assert next(r for r in rows2 if r["name"] == "B")["rank"] == 1.5
    assert mean == pytest.approx(np.mean([r["rank"] for r in rows]))
    assert med == pytest.approx(np.median([r["rank"] for r in rows]))


def test_parent_rank_skips_root_parent(declared):
    names = ["R", "A", "X"]
    m = _mat(names, {})
    rows, _, _ = T.parent_rank(m, names, declared)
    assert {r["name"] for r in rows} == {"A"}


# ---- nulls

def test_permutation_null_global_and_grouped(declared):
    names = ["R", "A", "B", "C", "D", "E", "X", "Y", "W", "Z"]
    m = _mat(names, {("A", "B"): 0.1, ("C", "B"): 0.1, ("D", "E"): 0.1, ("R", "A"): 0.1,
                     ("W", "Z"): 0.1})

    def metric(labels):
        order = [labels.index(n) for n in names]
        mm = m[np.ix_(order, order)]
        return T.nearest_is_family(mm, names, declared)[1]

    r = T.permutation_null(metric, names, n=200, seed=3)
    null, gap = r
    assert len(null) == 200 and gap == pytest.approx(r.observed - null.mean())
    assert gap > 0
    assert T.permutation_null(metric, names, n=50, seed=3).null.tolist() == \
        T.permutation_null(metric, names, n=50, seed=3).null.tolist()
    groups = {n: ("g1" if n in "RABCD" else "g2") for n in names}
    seen = []

    def spy(labels):
        seen.append(list(labels))
        return 0.0

    T.permutation_null(spy, names, groups=groups, n=20, seed=1)
    for lab in seen[1:]:
        assert sorted(lab[:5]) == sorted(names[:5]) and sorted(lab[5:]) == sorted(names[5:])


def test_polytomy_preserving_null(declared):
    trees = T.polytomy_preserving_null(declared, 20, seed=5)
    assert len(trees) == 20
    sizes = sorted(len(c) for c in declared.children.values())
    for t in trees:
        assert t.leaves == declared.leaves
        assert sorted(len(c) for c in t.children.values()) == sizes
    assert any(t.clades() != declared.clades() for t in trees)
    again = T.polytomy_preserving_null(declared, 20, seed=5)
    assert [t.clades() for t in trees] == [t.clades() for t in again]
    # null recall of declared clades is well below 1
    rec = [T.resolved_clade_recall(declared, t, declared.leaves) for t in trees]
    assert np.mean(rec) < 0.5


def test_detectable():
    s = np.array([[1, 0.5, 0.0], [0.5, 1, 0.01], [0.0, 0.01, 1]])
    assert T.detectable(s, ["a", "b", "c"]) == ["a", "b"]
    assert T.detectable(s, ["a", "b", "c"], floor=0.005) == ["a", "b", "c"]


# ---- real manifest sanity (only if present)

REAL = ROOT_DIR / "manifest"


@pytest.mark.skipif(not (REAL / "declared_lineage.csv").exists(), reason="manifest not present")
def test_real_declared():
    import csv
    progs = [r["name"] for r in csv.DictReader(open(REAL / "e7_groups.csv"))]
    d = T.build_declared(REAL / "declared_lineage.csv", REAL / "declared_lineage_basis.csv", progs)
    assert "room4doom" not in d.leaves and "freedoom" not in d.leaves
    assert d.declared_parent["doo-cr"] == "puredoom"
    assert d.declared_parent["doom3-bfg"] == "linuxdoom"
    assert d.declared_parent["doomgeneric"] == "chocolate-doom"
    assert set(d.roots) == {"linuxdoom", "doom3do"}
    assert len(d.leaves) == len(progs) - 2
    e = T.build_declared(REAL / "declared_lineage.csv", REAL / "declared_lineage_basis.csv", progs,
                         explicit_only=True)
    assert e.declared_parent["doomgeneric"] == T.ROOT
    assert e.declared_parent["doom3-bfg"] == T.ROOT
    assert e.clades() != d.clades()


# ---- NJ on exactly additive distances from a polytomous declared tree with a sampled ancestor

def _declared_additive():
    R = T.ROOT
    parent = {"anc": R, "x": R, "y": R, "z": R,
              "a": "anc", "b": "anc", "c": "anc", "m": "anc",
              "m1": "m", "m2": "m", "m3": "m"}
    members = list(parent)
    decl = T.DeclaredTree(members, parent, roots=["anc"], excluded=[])
    par = decl.parent_map

    def chain(u):
        c = [u]
        while c[-1] in par:
            c.append(par[c[-1]])
        return c

    def dist(u, v):
        cu, cv = chain(u), chain(v)
        s = set(cv)
        for i, w in enumerate(cu):
            if w in s:
                return i + cv.index(w)

    names = sorted(members)
    d = np.array([[dist(u, v) if u != v else 0 for v in names] for u in names], float)
    return decl, names, d


def test_nj_additive_declared_rooted_at_outgroup_gives_full_compat():
    decl, names, d = _declared_additive()
    nj = T.parse_newick(T.nj_newick(d, names))
    # every declared split is recovered by NJ on an exact tree metric
    assert decl.bipartitions(names) <= nj.bipartitions(names)
    # rooted at an unrelated top-level leaf (not a sampled ancestor) the rooted metrics are exact
    tr = T.root_at(nj, "x")
    ls = [n for n in names if n != "x"]
    assert T.resolved_triplet_compat(decl, tr, ls) == 1.0
    assert T.resolved_clade_recall(decl, tr, ls) == 1.0


def test_nj_additive_rooting_at_sampled_ancestor_is_undetermined():
    # a sampled ancestor sits ON the tree (zero pendant edge): rooting there makes its parent side
    # a polytomy with its descendants, so NJ cannot separate 'descendants' from 'unrelated'.
    decl, names, d = _declared_additive()
    nj = T.parse_newick(T.nj_newick(d, names))
    tr = T.root_at(nj, "anc")
    ls = [n for n in names if n != "anc"]
    assert T.resolved_triplet_compat(decl, tr, ls) < 1.0
