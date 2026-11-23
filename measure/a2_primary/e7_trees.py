"""DOOM-E7 tree library: declared tree, Newick trees, tree and distance-matrix metrics, nulls.

Pure Python + numpy (scipy only through the scanner's ``upgma``). No scan access.
Implements Amendment 1 sections C, F, I of the DOOM-E7 preregistration.

Conventions
-----------
* A ``Tree`` is a rooted tree over named leaves. Unrooted (NJ) trees are stored with a
  trifurcating root; use ``root_at(tree, leaf)`` before any rooted metric (clades, triplets).
* ``DeclaredTree`` is a ``Tree`` built from the declared lineage. Every program is a leaf;
  a program with declared children is a *sampled ancestor*: an internal node plus a pendant
  leaf of the same name. Programs with no usable parent hang off the virtual root
  ``__root__``.
* "Root-like" programs (``DeclaredTree.roots``) are the top-level ancestors: programs whose
  parent is the virtual root and that either have children or appear as a parent in the raw
  declared graph (linuxdoom, doom3do). Amendment 1 C.3: a shared root-like parent does not
  make two programs siblings, and a root-like ancestor does not make them cousins.
"""
from __future__ import annotations

import csv
import itertools
import re
import sys
from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np

sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
from structural_fingerprint.lineage import upgma as _sfs_upgma  # noqa: E402

ROOT = "__root__"
ALWAYS_EXCLUDED = frozenset({"freedoom"})  # assets project: left out of tree scoring (Amendment 1 C.1)
DROP_ALWAYS = {"excluded", "dropped"}
DROP_EXPLICIT_ONLY = {"inferred", "collapsed"}


# --------------------------------------------------------------------------- Tree

class Tree:
    """Rooted tree. ``children``: node -> list of child nodes; ``names``: leaf node -> name."""

    def __init__(self, children: dict, root, names: dict):
        self.children = {k: list(v) for k, v in children.items()}
        self.root = root
        self.names = dict(names)
        self.parent = {}
        for p, cs in self.children.items():
            for c in cs:
                self.parent[c] = p
        self.leaves = sorted(self.names.values())
        if len(set(self.leaves)) != len(self.leaves):
            raise ValueError("duplicate leaf names")
        self._leafsets = None
        self._depth = None
        self.length = {}  # node -> branch length to parent (when known)

    # -- structure
    def _post(self):
        order, stack = [], [self.root]
        while stack:
            n = stack.pop()
            order.append(n)
            stack.extend(self.children.get(n, ()))
        return order[::-1]  # children before parents

    def leafsets(self) -> dict:
        if self._leafsets is None:
            ls = {}
            for n in self._post():
                if n in self.names:
                    ls[n] = frozenset([self.names[n]])
                else:
                    ls[n] = frozenset().union(*(ls[c] for c in self.children.get(n, ())))
            self._leafsets = ls
        return self._leafsets

    def depths(self) -> dict:
        if self._depth is None:
            d = {self.root: 0}
            stack = [self.root]
            while stack:
                n = stack.pop()
                for c in self.children.get(n, ()):
                    d[c] = d[n] + 1
                    stack.append(c)
            self._depth = d
        return self._depth

    def _check_leaves(self, leaves):
        L = sorted(leaves)
        missing = set(L) - set(self.leaves)
        if missing:
            raise ValueError(f"leaves not in tree: {sorted(missing)[:5]}")
        return L

    def lca_depth(self, L: list[str]):
        """(D, dep): D[i,j] = topological depth of lca(L[i], L[j]); dep[i] = depth of leaf i."""
        pos = {n: i for i, n in enumerate(L)}
        ls, dp = self.leafsets(), self.depths()
        D = np.zeros((len(L), len(L)), dtype=np.int64)
        dep = np.zeros(len(L), dtype=np.int64)
        for node in sorted(ls, key=lambda x: dp[x]):  # shallow first, deeper overwrite
            idx = [pos[x] for x in ls[node] if x in pos]
            if not idx:
                continue
            if node in self.names:
                dep[idx[0]] = dp[node]
            if len(idx) > 1:
                D[np.ix_(idx, idx)] = dp[node]
        for i in range(len(L)):
            D[i, i] = dep[i]
        return D, dep

    # -- rooted clades and triplets
    def clades(self, leaves: Iterable[str] | None = None) -> set:
        """Set of frozensets (rooted clades of internal non-root nodes), size >= 2, excluding the
        full leaf set. With ``leaves``, clades are intersected with it first (pruning)."""
        L = set(self.leaves if leaves is None else self._check_leaves(leaves))
        out = set()
        for n, s in self.leafsets().items():
            if n == self.root or n in self.names:
                continue
            s = s & L
            if 2 <= len(s) < len(L):
                out.add(frozenset(s))
        return out

    def triplets(self, leaves: Iterable[str] | None = None) -> set:
        """Resolved rooted triplets as tuples (a, b, c), a < b, meaning ab|c."""
        L = self.leaves if leaves is None else self._check_leaves(leaves)
        combos, st = _triple_states(self, L)
        out = set()
        for (i, j, k), s in zip(combos, st):
            if s == 1:
                out.add((L[i], L[j], L[k]))
            elif s == 2:
                out.add((L[i], L[k], L[j]))
            elif s == 3:
                out.add((L[j], L[k], L[i]))
        return out

    # -- unrooted
    def bipartitions(self, leaves: Iterable[str] | None = None) -> set:
        """Non-trivial splits (both sides >= 2 leaves) as frozensets, canonically the side
        not containing the smallest leaf name."""
        L = set(self.leaves if leaves is None else self._check_leaves(leaves))
        if len(L) < 4:
            return set()
        ref = min(L)
        out = set()
        for n, s in self.leafsets().items():
            if n == self.root:
                continue
            s = frozenset(s & L)
            if len(s) < 2 or len(L) - len(s) < 2:
                continue
            if ref in s:
                s = frozenset(L - s)
            out.add(s)
        return out

    def topo_dist(self, L: list[str]) -> np.ndarray:
        """Edge-count path distance among leaves L (a degree-2 root is not counted as a node)."""
        D, dep = self.lca_depth(L)
        dist = dep[:, None] + dep[None, :] - 2 * D
        np.fill_diagonal(dist, 0)
        if len(self.children.get(self.root, ())) == 2:
            cross = (D == 0)
            np.fill_diagonal(cross, False)
            dist = dist - cross.astype(np.int64)
        return dist


def _combos(n: int, r: int) -> np.ndarray:
    if n < r:
        return np.zeros((0, r), dtype=np.int64)
    flat = np.fromiter(itertools.chain.from_iterable(itertools.combinations(range(n), r)),
                       dtype=np.int64)
    return flat.reshape(-1, r)


def _triple_states(tree: Tree, L: list[str]):
    """combos (m,3) of indices into L and states: 0 unresolved, 1 ij|k, 2 ik|j, 3 jk|i."""
    combos = _combos(len(L), 3)
    if len(combos) == 0:
        return combos, np.zeros(0, dtype=np.int8)
    D, _ = tree.lca_depth(L)
    i, j, k = combos[:, 0], combos[:, 1], combos[:, 2]
    dij, dik, djk = D[i, j], D[i, k], D[j, k]
    st = np.zeros(len(combos), dtype=np.int8)
    st[(dij > dik) & (dij > djk)] = 1
    st[(dik > dij) & (dik > djk)] = 2
    st[(djk > dij) & (djk > dik)] = 3
    return combos, st


def _quartet_states(tree: Tree, L: list[str]):
    """combos (m,4) and states: 0 star, 1 ij|kl, 2 ik|jl, 3 il|jk (unrooted four-point rule)."""
    combos = _combos(len(L), 4)
    if len(combos) == 0:
        return combos, np.zeros(0, dtype=np.int8)
    d = tree.topo_dist(L)
    i, j, k, l = combos.T
    s = np.stack([d[i, j] + d[k, l], d[i, k] + d[j, l], d[i, l] + d[j, k]])
    st = (np.argmin(s, axis=0) + 1).astype(np.int8)
    st[(s[0] == s[1]) & (s[1] == s[2])] = 0
    return combos, st


# --------------------------------------------------------------------------- Newick

def _quote(name: str) -> str:
    if any(c in name for c in " ():;,'[]"):
        return "'" + name.replace("'", "''") + "'"
    return name


def upgma_newick(distance, names: list[str]) -> str:
    """UPGMA (average linkage) Newick string via the scanner's ``upgma`` (rooted, ultrametric)."""
    return _sfs_upgma(np.asarray(distance, dtype=float), list(names))[0]


def nj_newick(distance, names: list[str]) -> str:
    """Neighbor-Joining (Saitou-Nei) Newick, unrooted (trifurcating top). Ties: first minimum."""
    names = list(names)
    n = len(names)
    d = np.asarray(distance, dtype=float)
    d = (d + d.T) / 2
    if n == 1:
        return f"{_quote(names[0])};"
    if n == 2:
        h = d[0, 1] / 2
        return f"({_quote(names[0])}:{h:.6f},{_quote(names[1])}:{h:.6f});"
    labels = [_quote(x) for x in names]
    D = d.copy()
    np.fill_diagonal(D, 0.0)
    while len(labels) > 3:
        m = len(labels)
        r = D.sum(axis=1)
        Q = (m - 2) * D - r[:, None] - r[None, :]
        np.fill_diagonal(Q, np.inf)
        i, j = np.unravel_index(np.argmin(Q), Q.shape)
        if i > j:
            i, j = j, i
        li = 0.5 * D[i, j] + (r[i] - r[j]) / (2 * (m - 2))
        lj = D[i, j] - li
        node = f"({labels[i]}:{li:.6f},{labels[j]}:{lj:.6f})"
        du = 0.5 * (D[i] + D[j] - D[i, j])
        keep = [x for x in range(m) if x not in (i, j)]
        newD = np.zeros((len(keep) + 1, len(keep) + 1))
        newD[:-1, :-1] = D[np.ix_(keep, keep)]
        newD[-1, :-1] = newD[:-1, -1] = du[keep]
        labels = [labels[x] for x in keep] + [node]
        D = newD
    a, b, c = 0, 1, 2
    la = 0.5 * (D[a, b] + D[a, c] - D[b, c])
    lb = 0.5 * (D[a, b] + D[b, c] - D[a, c])
    lc = 0.5 * (D[a, c] + D[b, c] - D[a, b])
    return f"({labels[a]}:{la:.6f},{labels[b]}:{lb:.6f},{labels[c]}:{lc:.6f});"


_NUM = re.compile(r"[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?")


def parse_newick(s: str) -> Tree:
    """Parse a Newick string (quoted names, branch lengths, [comments]; internal labels ignored)."""
    s = re.sub(r"\[[^\]]*\]", "", s).strip()
    if not s.endswith(";"):
        raise ValueError("Newick must end with ';'")
    s = s[:-1]
    pos = 0
    counter = itertools.count()
    children, names, length = {}, {}, {}

    def ws():
        nonlocal pos
        while pos < len(s) and s[pos].isspace():
            pos += 1

    def label():
        nonlocal pos
        ws()
        if pos < len(s) and s[pos] == "'":
            pos += 1
            out = []
            while True:
                if pos >= len(s):
                    raise ValueError("unterminated quote")
                if s[pos] == "'":
                    if pos + 1 < len(s) and s[pos + 1] == "'":
                        out.append("'")
                        pos += 2
                        continue
                    pos += 1
                    break
                out.append(s[pos])
                pos += 1
            return "".join(out)
        st = pos
        while pos < len(s) and s[pos] not in "(),:;":
            pos += 1
        return s[st:pos].strip()

    def blen():
        nonlocal pos
        ws()
        if pos < len(s) and s[pos] == ":":
            pos += 1
            ws()
            m = _NUM.match(s, pos)
            if not m:
                raise ValueError("bad branch length")
            pos = m.end()
            return float(m.group(0))
        return None

    def node():
        nonlocal pos
        ws()
        nid = next(counter)
        if pos < len(s) and s[pos] == "(":
            pos += 1
            kids = []
            while True:
                kids.append(node())
                ws()
                if s[pos] == ",":
                    pos += 1
                    continue
                if s[pos] == ")":
                    pos += 1
                    break
                raise ValueError(f"unexpected {s[pos]!r} at {pos}")
            children[nid] = kids
            label()  # internal label ignored
        else:
            nm = label()
            if not nm:
                raise ValueError("unnamed leaf")
            names[nid] = nm
        bl = blen()
        if bl is not None:
            length[nid] = bl
        return nid

    root = node()
    ws()
    if pos != len(s):
        raise ValueError("trailing characters after tree")
    if root in names:  # single leaf
        children[root] = []
    t = Tree(children, root, names)
    t.length = length
    return t


def root_at(tree: Tree, leaf: str) -> Tree:
    """Re-root at a leaf (outgroup rooting): the new root has two children, the leaf and the
    rest of the tree. A degree-2 old root is contracted first. Topology only."""
    node_of = {v: k for k, v in tree.names.items()}
    if leaf not in node_of:
        raise ValueError(f"unknown leaf {leaf!r}")
    adj = {}
    for p, cs in tree.children.items():
        for c in cs:
            adj.setdefault(p, []).append(c)
            adj.setdefault(c, []).append(p)
    if len(tree.children.get(tree.root, ())) == 2:
        a, b = tree.children[tree.root]
        adj[a].remove(tree.root)
        adj[b].remove(tree.root)
        adj[a].append(b)
        adj[b].append(a)
        del adj[tree.root]
    start = node_of[leaf]
    if len(adj.get(start, ())) != 1:
        raise ValueError("leaf must have a single neighbour")
    new_root = ("newroot",)
    children = {new_root: [start]}
    x = adj[start][0]
    children[new_root].append(x)
    stack = [(x, start)]
    while stack:
        n, par = stack.pop()
        kids = [c for c in adj.get(n, ()) if c != par]
        if kids:
            children[n] = kids
            stack.extend((c, n) for c in kids)
    return Tree(children, new_root, tree.names)


# --------------------------------------------------------------------------- tree-vs-tree

def _common(a: Tree, b: Tree, leaves) -> list[str]:
    L = sorted(leaves)
    for t in (a, b):
        t._check_leaves(L)
    return L


def resolved_clade_recall(declared: Tree, tree: Tree, leaves) -> float:
    """Share of the declared tree's resolved clades (restricted to ``leaves``; size >= 2, not
    the full set, de-duplicated) that are also clades of ``tree``. nan if there are none."""
    L = _common(declared, tree, leaves)
    dec = declared.clades(L)
    if not dec:
        return float("nan")
    return len(dec & tree.clades(L)) / len(dec)


def resolved_triplet_compat(declared: Tree, tree: Tree, leaves) -> float:
    """Share of the declared tree's resolved rooted triplets (on ``leaves``) that ``tree`` also
    resolves the same way (ab|c). Unresolved-in-tree counts as not satisfied. nan if none."""
    L = _common(declared, tree, leaves)
    _, sd = _triple_states(declared, L)
    _, st = _triple_states(tree, L)
    res = sd != 0
    if not res.any():
        return float("nan")
    return float((sd[res] == st[res]).mean())


def rf_unrooted(tree_a: Tree, tree_b: Tree, leaves) -> float:
    """Normalised unrooted Robinson-Foulds on non-trivial bipartitions restricted to ``leaves``:
    |A symdiff B| / (|A| + |B|); 0 if both are empty."""
    L = _common(tree_a, tree_b, leaves)
    A, B = tree_a.bipartitions(L), tree_b.bipartitions(L)
    if not A and not B:
        return 0.0
    return len(A ^ B) / (len(A) + len(B))


def triplet_distance(tree_a: Tree, tree_b: Tree, leaves) -> float:
    """Rooted triplet distance on ``leaves``: among leaf triples resolved in at least one tree,
    the share where the two trees do not give the same resolution. 0 if none are resolved."""
    L = _common(tree_a, tree_b, leaves)
    _, sa = _triple_states(tree_a, L)
    _, sb = _triple_states(tree_b, L)
    either = (sa != 0) | (sb != 0)
    if not either.any():
        return 0.0
    return float((sa[either] != sb[either]).mean())


def quartet_distance(tree_a: Tree, tree_b: Tree, leaves) -> float:
    """Unrooted quartet distance on ``leaves`` (exact, vectorised four-point rule): among
    4-subsets resolved in at least one tree, the share with different topologies (a star
    in one and resolved in the other counts as different). Roots are ignored."""
    L = _common(tree_a, tree_b, leaves)
    _, sa = _quartet_states(tree_a, L)
    _, sb = _quartet_states(tree_b, L)
    either = (sa != 0) | (sb != 0)
    if not either.any():
        return 0.0
    return float((sa[either] != sb[either]).mean())


# --------------------------------------------------------------------------- declared tree

class DeclaredTree(Tree):
    """Declared lineage tree with every program a leaf (see module docstring).

    Extra attributes: ``declared_parent`` (program -> parent program or ``__root__``),
    ``roots`` (top-level ancestors, root-like), ``excluded`` (programs left out),
    ``explicit_only``.
    """

    def __init__(self, members, declared_parent, roots, excluded, explicit_only=False):
        members = list(members)
        has_children = {p for c, p in declared_parent.items() if p != ROOT}
        top = ("root",)
        children = {top: []}
        names = {}
        for m in sorted(members):
            names[("l", m)] = m
        for m in sorted(has_children):
            children[("n", m)] = [("l", m)]
        for m in sorted(members):
            par = declared_parent[m]
            pnode = top if par == ROOT else ("n", par)
            # an ancestor's internal node hangs off its own parent; its pendant leaf is already inside it
            if m in has_children:
                children[pnode].append(("n", m))
            else:
                children[pnode].append(("l", m))
        super().__init__(children, top, names)
        self.declared_parent = dict(declared_parent)
        self.roots = tuple(sorted(roots))
        self.excluded = frozenset(excluded)
        self.explicit_only = explicit_only
        self._children_of = {}
        for c, p in declared_parent.items():
            self._children_of.setdefault(p, set()).add(c)

    @property
    def parent_map(self) -> dict:
        return self.declared_parent

    def ancestors(self, x: str) -> set:
        out, p = set(), self.declared_parent.get(x, ROOT)
        while p != ROOT:
            out.add(p)
            p = self.declared_parent[p]
        return out

    def descendants(self, x: str) -> set:
        out, stack = set(), [x]
        while stack:
            for c in self._children_of.get(stack.pop(), ()):
                out.add(c)
                stack.append(c)
        return out

    def relation(self, x: str, y: str, include_root_siblings: bool = False) -> str:
        """'ancestor' (y is x's ancestor), 'descendant', 'sibling', 'cousin' or 'other'.
        Default: sibling needs a shared non-root parent, cousin a shared non-root ancestor
        (virtual root and top-level ancestors are root-like). With include_root_siblings a
        shared virtual root or top-level parent also makes siblings (the old inflated rule)."""
        if x == y:
            return "self"
        if y in self.ancestors(x):
            return "ancestor"
        if y in self.descendants(x):
            return "descendant"
        rootlike = set(self.roots) | {ROOT}
        px, py = self.declared_parent.get(x, ROOT), self.declared_parent.get(y, ROOT)
        if px == py and (px not in rootlike or include_root_siblings):
            return "sibling"
        if (self.ancestors(x) & self.ancestors(y)) - rootlike:
            return "cousin"
        return "other"


def _read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def build_declared(lineage_csv, basis_csv, programs, *, explicit_only: bool = False) -> DeclaredTree:
    """Build the registered declared tree (Amendment 1 C.1-C.2).

    Edges = declared_lineage.csv rows plus any extra rows of the basis csv (the registered
    doom3-bfg -> linuxdoom edge lives only there), minus rows whose basis is ``excluded`` or
    ``dropped``; with ``explicit_only`` also minus ``inferred`` and ``collapsed``. A lineage
    row with no basis row raises ValueError. A program left with no usable parent (including
    one whose parent is not in ``programs`` or is excluded) hangs off ``__root__``. Programs
    whose every edge is ``excluded`` (room4doom) and ``ALWAYS_EXCLUDED`` (freedoom) are absent.
    Programs not mentioned anywhere are leaves under ``__root__``.
    """
    basis = {}
    for r in _read_csv(basis_csv):
        basis[(r["name"], r["parent"])] = r["basis"].strip()
    raw = [(r["name"], r["parent"]) for r in _read_csv(lineage_csv)]
    for key in basis:
        if key not in raw:
            raw.append(key)
    drop = set(DROP_ALWAYS) | (DROP_EXPLICIT_ONLY if explicit_only else set())
    kept, raw_children, excluded_basis = {}, set(), set()
    for c, p in raw:
        if (c, p) not in basis:
            raise ValueError(f"edge {c}->{p} has no row in the basis csv")
        b = basis[(c, p)]
        raw_children.add(c)
        if b == "excluded":
            excluded_basis.add(c)
        if b in drop:
            continue
        if c in kept:
            raise ValueError(f"{c} has two usable parents: {kept[c]}, {p}")
        kept[c] = p
    excluded = set(ALWAYS_EXCLUDED) | {c for c in excluded_basis if c not in kept}
    members = [p for p in programs if p not in excluded]
    mset = set(members)
    dparent = {}
    for m in members:
        p = kept.get(m)
        dparent[m] = p if (p in mset and p != m) else ROOT
    for m in members:  # cycle check
        seen, x = {m}, dparent[m]
        while x != ROOT:
            if x in seen:
                raise ValueError(f"cycle in declared lineage at {x}")
            seen.add(x)
            x = dparent[x]
    raw_parents = {p for _, p in raw}
    has_children = {p for p in dparent.values() if p != ROOT}
    roots = {m for m in members if dparent[m] == ROOT and (m in has_children or m in raw_parents)}
    return DeclaredTree(members, dparent, roots, excluded, explicit_only)


# --------------------------------------------------------------------------- distance-matrix metrics

def _tied_min(row: np.ndarray, i: int, tol: float = 1e-12) -> list[int]:
    cand = [j for j in range(len(row)) if j != i]
    m = min(row[j] for j in cand)
    return [j for j in cand if row[j] <= m + tol]


def nearest_is_family(distance, names, declared: DeclaredTree, *, include_root_siblings=False,
                      skip=()):
    """M1 (a distance-matrix metric, not a tree metric). Returns ``(rows, rate)``.

    Scored programs: in ``declared``, not in ``skip``, and having a declared ancestor or
    descendant (as in the scanner's evaluate_lineage). ``skip`` programs are not scored but
    stay candidate neighbours. The nearest neighbour is the minimum-distance other program;
    ties are split: ``weight`` = share of tied nearest neighbours that are family (ancestor,
    descendant, sibling or cousin, see ``DeclaredTree.relation``). ``rate`` = mean weight
    (nan if no program is scored). Each row: name, nearest (list), relations (list), weight.
    """
    names = list(names)
    d = np.asarray(distance, dtype=float)
    skip = set(skip)
    inlist = set(declared.leaves)
    rows = []
    for i, n in enumerate(names):
        if n in skip or n not in inlist:
            continue
        if not (declared.ancestors(n) or declared.descendants(n)):
            continue
        tied = _tied_min(d[i], i)
        rels = []
        for j in tied:
            m = names[j]
            if m in inlist:
                rels.append(declared.relation(n, m, include_root_siblings))
            else:  # not a declared-tree program
                rels.append("sibling" if (include_root_siblings and declared.declared_parent.get(n) == ROOT)
                            else "other")
        w = float(np.mean([r != "other" for r in rels]))
        rows.append({"name": n, "nearest": [names[j] for j in tied], "relations": rels, "weight": w})
    rate = float(np.mean([r["weight"] for r in rows])) if rows else float("nan")
    return rows, rate


def parent_rank(distance, names, declared: DeclaredTree, *, skip=()):
    """M2 (distance-matrix metric). Returns ``(rows, mean_rank, median_rank)``.

    For each non-skipped program whose declared parent (a program, not the virtual root) is in
    ``names``: rank of that parent among the other programs ordered by distance, not counting
    the program's own declared descendants. Ties are averaged: rank = 1 + (#strictly closer)
    + (#other tied)/2. Rows: name, parent, rank, rank1 (rank == 1). The share at rank 1 is
    the mean of ``rank1`` over rows."""
    names = list(names)
    idx = {n: i for i, n in enumerate(names)}
    d = np.asarray(distance, dtype=float)
    skip = set(skip)
    rows = []
    for n in names:
        if n in skip or n not in declared.declared_parent:
            continue
        p = declared.declared_parent[n]
        if p == ROOT or p not in idx:
            continue
        i = idx[n]
        desc = declared.descendants(n)
        others = [j for j, m in enumerate(names) if j != i and m not in desc]
        dp = d[i, idx[p]]
        less = sum(1 for j in others if d[i, j] < dp - 1e-12)
        eq = sum(1 for j in others if abs(d[i, j] - dp) <= 1e-12 and j != idx[p])
        rank = 1 + less + eq / 2
        rows.append({"name": n, "parent": p, "rank": rank, "rank1": rank == 1})
    if not rows:
        return rows, float("nan"), float("nan")
    r = np.array([x["rank"] for x in rows])
    return rows, float(r.mean()), float(np.median(r))


# --------------------------------------------------------------------------- nulls

@dataclass
class NullResult:
    """``null``: array of metric values under the null; ``gap``: observed minus mean(null).
    Iterating yields ``(null, gap)``. Also: observed, p_upper (share of null >= observed,
    with +1 smoothing), p95 (95th percentile of the null)."""
    null: np.ndarray
    gap: float
    observed: float
    p_upper: float
    p95: float

    def __iter__(self):
        yield self.null
        yield self.gap


def permutation_null(metric_fn: Callable[[list], float], names, *, groups: dict | None = None,
                     n: int = 1000, seed: int = 0) -> NullResult:
    """Label-permutation null. ``metric_fn(labels)`` receives a list the same length as
    ``names``: ``labels[i]`` is the name now assigned to the i-th row/leaf of the measured
    object (the matrix or tree stays fixed, labels move). Observed = ``metric_fn(list(names))``.

    ``groups=None``: global shuffle of all labels. ``groups`` = dict name -> group (e.g. the
    ``language_group`` column of e7_groups.csv): labels are shuffled only among rows of the same
    group (names missing from ``groups`` form their own group). Seeded (numpy default_rng).
    NaN metric values are dropped from the null."""
    names = list(names)
    rng = np.random.default_rng(seed)
    if groups is None:
        blocks = [list(range(len(names)))]
    else:
        by = {}
        for i, nm in enumerate(names):
            by.setdefault(groups.get(nm, "__none__"), []).append(i)
        blocks = list(by.values())
    obs = float(metric_fn(list(names)))
    vals = []
    for _ in range(n):
        lab = list(names)
        for b in blocks:
            perm = rng.permutation(len(b))
            for src, dst in zip(perm, b):
                lab[dst] = names[b[src]]
        vals.append(float(metric_fn(lab)))
    null = np.array(vals, dtype=float)
    null = null[~np.isnan(null)]
    gap = obs - float(null.mean()) if len(null) else float("nan")
    p = (1 + int((null >= obs).sum())) / (1 + len(null))
    p95 = float(np.percentile(null, 95)) if len(null) else float("nan")
    return NullResult(null, gap, obs, p, p95)


def polytomy_preserving_null(declared: Tree, n: int, seed: int = 0) -> list[Tree]:
    """Null declared trees that keep the declared tree's polytomy structure.

    Algorithm: take the declared tree's skeleton, i.e. every internal node with its exact
    number of leaf slots and its nesting of internal nodes (so the multiset of child counts,
    the polytomy sizes and the depth profile are unchanged, and the sampled-ancestor pendant
    leaf slot of every ancestor stays), detach all leaves, then re-attach the leaf names to the
    leaf slots in a uniformly random order (seeded). Each draw is a ``Tree`` with the same
    leaf set. Note a sampled ancestor's name may land anywhere: the pairing between an
    ancestor node and its pendant leaf is deliberately broken, since that is part of what the
    null randomises. Returns a list of ``n`` Trees."""
    rng = np.random.default_rng(seed)
    slots = sorted(declared.names)
    labels = [declared.names[s] for s in slots]
    out = []
    for _ in range(n):
        perm = rng.permutation(len(labels))
        names = {s: labels[p] for s, p in zip(slots, perm)}
        out.append(Tree(declared.children, declared.root, names))
    return out


# --------------------------------------------------------------------------- floor

def detectable(shared, names, floor: float = 0.02) -> list[str]:
    """Names whose largest ``shared`` with any other program is >= ``floor``; the rest have
    'no detectable descent'. ``shared`` is a square matrix aligned with ``names``."""
    s = np.array(shared, dtype=float)
    np.fill_diagonal(s, -np.inf)
    mx = s.max(axis=1) if s.shape[0] > 1 else np.array([-np.inf])
    return [n for n, m in zip(names, mx) if m >= floor]
