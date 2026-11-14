"""Detect horizontal code transfers across declared DOOM lineage branches.

Algorithm (name-blind during matching):
1. Load each port's FunctionTable in ``composition`` mode and compute ``BL.descriptors``
   (structural geometry + 1-hop call-graph neighborhood descriptors).
2. Mask out vertical ``linuxdoom`` inheritance: any function with a tight structural
   match in ``linuxdoom`` (``dist <= linuxdoom_thresh``) is excluded from horizontal search.
3. Across all pairs of ports on *different* non-``linuxdoom`` branches (per
   ``manifest/declared_lineage.csv``), find reciprocal best-hit structural twins
   (``dist <= twin_thresh`` and comparable LOC).
4. Cluster matched pairs by directory/module and call-graph connectivity (post-hoc
   name/path inspection only) to surface multi-function horizontally borrowed libraries
   and subsystems.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


def _load_lineage(path: Path) -> dict[str, set[str]]:
    """Return map: port -> set of all declared ancestors (excluding linuxdoom)."""
    parents: dict[str, set[str]] = defaultdict(set)
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            parents[row["name"]].add(row["parent"])

    ancestors: dict[str, set[str]] = {}
    for node in list(parents.keys()):
        seen: set[str] = set()
        stack = list(parents[node])
        while stack:
            p = stack.pop()
            if p == "linuxdoom" or p in seen:
                continue
            seen.add(p)
            stack.extend(parents.get(p, ()))
        ancestors[node] = seen
    return ancestors


def _same_branch(a: str, b: str, anc: dict[str, set[str]]) -> bool:
    if a == b:
        return True
    aa = anc.get(a, set()) | {a}
    ab = anc.get(b, set()) | {b}
    return bool(aa & ab)


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect horizontal transfers across DOOM ports")
    ap.add_argument("--scans", required=True)
    ap.add_argument("--max-funcs", type=int, default=25000)
    ap.add_argument("--linuxdoom-thresh", type=float, default=0.35)
    ap.add_argument("--twin-thresh", type=float, default=0.25)
    ap.add_argument("--min-cluster", type=int, default=8)
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    from structural_fingerprint import blind as BL
    from structural_fingerprint.fingerprint import build
    from structural_fingerprint.reference import load_reference
    from structural_fingerprint.scan_io import load_scan, resolve_scans

    manifest_dir = Path(__file__).resolve().parents[2] / "manifest"
    anc = _load_lineage(manifest_dir / "declared_lineage.csv")

    ref = load_reference("portable")
    bp = BL.BlindParams()
    scans_root = Path(args.scans)

    # Load linuxdoom first
    ld_db = resolve_scans([scans_root / "linuxdoom"])[0]
    ld_sc = load_scan(ld_db, ref.signal_columns)
    ld_ft = build(ld_sc, ref, min_loc=3, keyword_mode="composition").functions
    ld_bv = BL.blind_view(ld_ft)
    ld_xd = BL.descriptors(ld_bv, len(ref.archetype_names), bp.use_graph, bp.use_measures, None, bp.geometry_only)
    ld_tree = cKDTree(ld_xd)

    ports = {}
    for p in sorted(scans_root.iterdir()):
        if not p.is_dir() or p.name == "linuxdoom":
            continue
        try:
            db = resolve_scans([p])[0]
            sc = load_scan(db, ref.signal_columns)
            ft = build(sc, ref, min_loc=3, keyword_mode="composition").functions
        except Exception:
            continue
        if ft is None or len(ft) > args.max_funcs or len(ft) < 30:
            continue
        bv = BL.blind_view(ft)
        xd = BL.descriptors(bv, len(ref.archetype_names), bp.use_graph, bp.use_measures, None, bp.geometry_only)

        # Mask out vertical linuxdoom matches
        dists, _ = ld_tree.query(xd, k=1)
        novel_idx = np.flatnonzero(dists > args.linuxdoom_thresh)
        if len(novel_idx) < args.min_cluster:
            continue

        xd_nov = xd[novel_idx]
        locs_nov = np.array([int(ft.loc[bv.rows[i]]) for i in novel_idx])
        names_nov = [str(ft.name[bv.rows[i]]) for i in novel_idx]
        dirs_nov = [str(Path(str(ft.path[bv.rows[i]])).parent) for i in novel_idx]
        ports[p.name] = {
            "xd": xd_nov,
            "tree": cKDTree(xd_nov),
            "locs": locs_nov,
            "names": names_nov,
            "dirs": dirs_nov,
        }

    print(f"Loaded {len(ports)} ports (non-linuxdoom functions masked at thresh={args.linuxdoom_thresh}).")

    findings = []
    names_list = sorted(ports.keys())
    for i, pa in enumerate(names_list):
        A = ports[pa]
        for pb in names_list[i + 1 :]:
            if _same_branch(pa, pb, anc):
                continue
            B = ports[pb]
            # Reciprocal nearest neighbors in descriptor space
            da, ia = B["tree"].query(A["xd"], k=1, distance_upper_bound=args.twin_thresh)
            db, ib = A["tree"].query(B["xd"], k=1, distance_upper_bound=args.twin_thresh)

            twins = []
            for qi in range(len(A["xd"])):
                ri = int(ia[qi])
                if ri >= len(B["xd"]) or not np.isfinite(da[qi]):
                    continue
                if int(ib[ri]) == qi:
                    la, lb = A["locs"][qi], B["locs"][ri]
                    if la >= 5 and lb >= 5 and abs(la - lb) / max(la, lb) <= 0.30:
                        twins.append((qi, ri))

            if len(twins) < args.min_cluster:
                continue

            # Post-hoc: group by (dir_a, dir_b) to identify borrowed modules/libraries
            dir_pairs = Counter((A["dirs"][qi], B["dirs"][ri]) for qi, ri in twins)
            exact_name = sum(
                1 for qi, ri in twins
                if A["names"][qi].strip().lower() == B["names"][ri].strip().lower()
            )
            top_dir, top_cnt = dir_pairs.most_common(1)[0]
            if top_cnt < args.min_cluster and exact_name < args.min_cluster:
                continue
            sample_names = [
                A["names"][qi]
                for qi, ri in twins
                if (A["dirs"][qi], B["dirs"][ri]) == top_dir
                and A["names"][qi].strip().lower() == B["names"][ri].strip().lower()
            ][:5]
            findings.append((exact_name, len(twins), pa, pb, top_dir[0], top_dir[1], top_cnt, sample_names))

    findings.sort(key=lambda x: (-x[0], -x[1]))
    print(f"\n=== TOP CROSS-BRANCH HORIZONTAL CLUSTERS (showing up to {args.top}) ===")
    print(f"{'Port A':16s} | {'Port B':16s} | {'Twins':>5s} | {'Exact':>5s} | {'Top Shared Module Pair (count)':50s} | Samples")
    print("-" * 140)
    for exact, tot, pa, pb, da, db_, cnt, samp in findings[: args.top]:
        mod = f"{da} <-> {db_} ({cnt})"
        print(f"{pa:16s} | {pb:16s} | {tot:5d} | {exact:5d} | {mod:50s} | {', '.join(samp)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
