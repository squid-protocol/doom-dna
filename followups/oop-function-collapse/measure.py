"""DOOM-E1: Collapse short wrapper functions (loc <= max_loc) in a call graph before subway analysis.

Usage:
    python followups/oop-function-collapse/measure.py --scans DIR --out DIR [--max-loc 5]
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np


def collapse_short_wrappers(
    edges: np.ndarray,
    loc: np.ndarray,
    max_loc: int = 5,
) -> tuple[np.ndarray, np.ndarray]:
    """Contract short wrapper nodes (loc <= max_loc) that have both callers and callees.

    Every path ``caller -> wrapper -> callee`` becomes ``caller -> callee`` (without self-loops),
    and the wrapper node is marked inactive in the returned boolean ``keep`` mask.
    """
    n = len(loc)
    keep = np.ones(n, dtype=bool)
    if n == 0 or len(edges) == 0:
        return edges.copy(), keep

    out_adj: dict[int, set[int]] = defaultdict(set)
    in_adj: dict[int, set[int]] = defaultdict(set)
    for u, v in edges.tolist():
        if u != v:
            out_adj[u].add(v)
            in_adj[v].add(u)

    for w in range(n):
        if loc[w] > max_loc:
            continue
        callers = list(in_adj.get(w, ()))
        callees = list(out_adj.get(w, ()))
        if not callers or not callees:
            continue
        keep[w] = False
        for c in callers:
            out_adj[c].discard(w)
            for t in callees:
                if c != t:
                    out_adj[c].add(t)
                    in_adj[t].add(c)
        for t in callees:
            in_adj[t].discard(w)
        out_adj.pop(w, None)
        in_adj.pop(w, None)

    new_edges = sorted((u, v) for u, targets in out_adj.items() if keep[u] for v in targets if keep[v])
    arr = np.asarray(new_edges, dtype=np.int32) if new_edges else np.zeros((0, 2), dtype=np.int32)
    return arr, keep


def main() -> int:
    ap = argparse.ArgumentParser(description="DOOM-E1: compare subway wiring before/after short-wrapper collapse")
    ap.add_argument("--scans", required=True, help="Directory of GitGalaxy scan databases")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--max-loc", type=int, default=5, help="Collapse wrappers with loc <= max_loc (default 5)")
    args = ap.parse_args()

    from structural_fingerprint import subway as SW
    from structural_fingerprint.fingerprint import FunctionTable, build
    from structural_fingerprint.reference import load_reference
    from structural_fingerprint.scan_io import load_scan, resolve_scans
    from structural_fingerprint.twins import TwinParams

    ref = load_reference("structure")
    tax = SW.Taxonomy.load(Path(__file__).resolve().parents[2] / "manifest" / "subsystems.json")
    raw_tables: list[FunctionTable] = []
    collapsed_tables: list[FunctionTable] = []
    for db in resolve_scans([Path(args.scans)]):
        fp = build(load_scan(db, ref.signal_columns), ref, min_loc=1, keyword_mode="smoothed_density")
        ft = fp.functions
        assert ft is not None
        raw_tables.append(ft)
        new_edges, keep = collapse_short_wrappers(ft.edges if ft.edges is not None else np.zeros((0, 2), dtype=np.int32), ft.loc, args.max_loc)
        remap = -np.ones(len(ft), dtype=np.int32)
        remap[np.flatnonzero(keep)] = np.arange(int(keep.sum()), dtype=np.int32)
        remapped_edges = remap[new_edges] if len(new_edges) else new_edges
        collapsed_tables.append(
            FunctionTable(
                repo=ft.repo,
                name=ft.name[keep],
                path=ft.path[keep],
                language=ft.language[keep],
                loc=ft.loc[keep],
                archetype=ft.archetype[keep],
                key=ft.key[keep],
                vectors=ft.vectors[keep],
                edges=remapped_edges,
            )
        )

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    params = TwinParams()
    raw_maps, _, _ = SW.build_maps(raw_tables, "linuxdoom", tax, params)
    col_maps, _, _ = SW.build_maps(collapsed_tables, "linuxdoom", tax, params)
    SW.write_outputs(out / "raw", raw_maps, tax, "linuxdoom")
    SW.write_outputs(out / "collapsed", col_maps, tax, "linuxdoom")
    print(f"wrote DOOM-E1 raw vs collapsed subway outputs to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
