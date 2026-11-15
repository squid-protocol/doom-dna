"""DOOM-E1 (Refined): Collapse short wrapper functions (loc <= max_loc) before Seed-and-Extend.

Tests whether collapsing OOP pass-through wrappers (``caller -> wrapper -> callee``
with ``loc <= max_loc``) improves unsupervised Seed-and-Extend recovery
(``composition`` mode + ``delta`` calibration) on Java/Kotlin/C# ports vs controls.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from measure import collapse_short_wrappers


def _norm_name(s: str) -> str:
    return s.strip().lower().replace("-", "_")


def _same_name(a: str, b: str) -> bool:
    na, nb = _norm_name(a), _norm_name(b)
    if na == nb:
        return True
    if "_" in nb and na.split("_", 1)[-1] == nb.split("_", 1)[-1]:
        return len(na.split("_", 1)[-1]) >= 4
    return False


def run_seed_extend(p_ft, p_comp_keep, ref_ft, rv, xr, hr, ref_comp, r_norm, ref_nbrs, tax, port: str, len_archetypes: int, bp, seed_frac: float = 0.15, hops: int = 3):
    from structural_fingerprint import blind as BL

    pv = BL.blind_view(p_ft)
    xp = BL.descriptors(pv, len_archetypes, bp.use_graph, bp.use_measures, None, bp.geometry_only)
    hp = BL.hop_matrix(pv, bp.hop_cap)

    m = BL._sqdist(xp, xr)
    m = m / (m.max() or 1.0)
    t = BL.fused_gw(m, hp, hr, bp.alpha, bp.epsilon, bp.outer)

    best_r = np.argmax(t, axis=1)
    best_p = np.argmax(t, axis=0)
    rbh = [(i, int(best_r[i]), float(t[i, best_r[i]])) for i in range(pv.n) if best_p[best_r[i]] == i]
    rbh.sort(key=lambda x: x[2], reverse=True)
    k_seed = max(1, int(len(rbh) * seed_frac)) if rbh else 0
    seeds = rbh[:k_seed]

    anchor_p_to_r: dict[int, int] = {i: j for i, j, _ in seeds}
    used_r: set[int] = set(anchor_p_to_r.values())

    p_comp = p_comp_keep[pv.rows]
    if seeds:
        pi_s = np.array([i for i, _, _ in seeds], dtype=np.int64)
        ri_s = np.array([j for _, j, _ in seeds], dtype=np.int64)
        delta = np.mean(p_comp[pi_s] - ref_comp[ri_s], axis=0)
    else:
        delta = np.zeros(p_comp.shape[1])
    p_sh = p_comp - delta
    p_sh_norm = p_sh / np.maximum(np.linalg.norm(p_sh, axis=1, keepdims=True), 1e-9)

    p_nbrs: dict[int, set[int]] = defaultdict(set)
    for u, v in pv.edges.tolist():
        p_nbrs[u].add(v)
        p_nbrs[v].add(u)

    for _ in range(hops):
        proposals: list[tuple[float, int, int]] = []
        for pu in range(pv.n):
            if pu in anchor_p_to_r:
                continue
            cand_votes: Counter[int] = Counter()
            for pn in p_nbrs.get(pu, ()):
                if pn in anchor_p_to_r:
                    for rc in ref_nbrs.get(anchor_p_to_r[pn], ()):
                        if rc not in used_r:
                            cand_votes[rc] += 1
            if not cand_votes:
                continue
            cands = np.array(list(cand_votes.keys()), dtype=np.int64)
            votes = np.array([cand_votes[c] for c in cands], dtype=np.float64)
            cos = r_norm[cands] @ p_sh_norm[pu]
            scores = votes * (1.0 + np.maximum(cos, 0.0)) + 0.25 * t[pu, cands] / (t[pu].max() or 1.0)
            best_idx = int(np.argmax(scores))
            proposals.append((float(scores[best_idx]), pu, int(cands[best_idx])))
        if not proposals:
            break
        proposals.sort(reverse=True)
        added = 0
        for _, pu, ru in proposals:
            if pu not in anchor_p_to_r and ru not in used_r:
                anchor_p_to_r[pu] = ru
                used_r.add(ru)
                added += 1
        if added == 0:
            break

    def score_pairs(pairs: list[tuple[int, int]]) -> tuple[int, float, int, float]:
        if not pairs:
            return 0, 0.0, 0, 0.0
        sub_ok = 0
        name_ok = 0
        for pu, ru in pairs:
            pr, rr = pv.rows[pu], rv.rows[ru]
            if tax.classify(str(p_ft.path[pr]), port) == tax.classify(str(ref_ft.path[rr]), "linuxdoom"):
                sub_ok += 1
            if _same_name(str(p_ft.name[pr]), str(ref_ft.name[rr])):
                name_ok += 1
        return len(pairs), sub_ok / len(pairs), name_ok, name_ok / len(pairs)

    n1, sub1, nok1, nm1 = score_pairs([(i, j) for i, j, _ in seeds])
    na, suba, noka, nma = score_pairs(list(anchor_p_to_r.items()))
    return pv.n, (n1, sub1, nok1, nm1), (na, suba, noka, nma)


def main() -> int:
    ap = argparse.ArgumentParser(description="DOOM-E1 (Refined): Seed-and-Extend before vs after wrapper collapse")
    ap.add_argument("--scans", default="/srv/storage_16tb/projects/gitgalaxy/doom-study/rescan-6c7c6c1bc/scans/6c7c6c1bc")
    ap.add_argument("--ports", default="mochadoom,kocoa-doom,managed-doom,chocolate-doom,gore,room4doom")
    ap.add_argument("--max-loc", type=int, default=5)
    args = ap.parse_args()

    from structural_fingerprint import blind as BL
    from structural_fingerprint import features as F
    from structural_fingerprint.fingerprint import FunctionTable, build
    from structural_fingerprint.reference import load_reference
    from structural_fingerprint.scan_io import load_scan, resolve_scans
    from structural_fingerprint.subway import Taxonomy

    root = Path(args.scans)
    tax = Taxonomy.load(Path(__file__).resolve().parents[2] / "manifest" / "subsystems.json")
    ref = load_reference("portable")
    bp = BL.BlindParams()

    ref_db = resolve_scans([root / "linuxdoom"])[0]
    ref_scan = load_scan(ref_db, ref.signal_columns)
    ref_ft = build(ref_scan, ref, min_loc=3, keyword_mode="composition").functions
    assert ref_ft is not None
    rv = BL.blind_view(ref_ft)
    xr = BL.descriptors(rv, len(ref.archetype_names), bp.use_graph, bp.use_measures, None, bp.geometry_only)
    hr = BL.hop_matrix(rv, bp.hop_cap)
    ref_comp_all = F.raw_features(
        ref, ref_scan.loc, ref_scan.complexity, ref_scan.args, ref_scan.keyword_density, ref_scan.signals,
        keyword_mode="composition",
    )
    ref_comp = ref_comp_all[rv.rows]
    r_norm = ref_comp / np.maximum(np.linalg.norm(ref_comp, axis=1, keepdims=True), 1e-9)
    ref_nbrs: dict[int, set[int]] = defaultdict(set)
    for u, v in rv.edges.tolist():
        ref_nbrs[u].add(v)
        ref_nbrs[v].add(u)

    for port in args.ports.split(","):
        dbs = resolve_scans([root / port])
        if not dbs:
            continue
        p_scan = load_scan(dbs[0], ref.signal_columns)
        # Raw (min_loc=3, matching standard Seed-and-Extend)
        ft_raw = build(p_scan, ref, min_loc=3, keyword_mode="composition").functions
        assert ft_raw is not None
        comp_all = F.raw_features(
            ref, p_scan.loc, p_scan.complexity, p_scan.args, p_scan.keyword_density, p_scan.signals,
            keyword_mode="composition",
        )
        n_raw, t1_raw, se_raw = run_seed_extend(
            ft_raw, comp_all, ref_ft, rv, xr, hr, ref_comp, r_norm, ref_nbrs, tax, port, len(ref.archetype_names), bp
        )

        # Collapsed: build at min_loc=1 so loc <= max_loc wrappers exist, collapse them, then filter min_loc=3
        ft_full = build(p_scan, ref, min_loc=1, keyword_mode="composition").functions
        assert ft_full is not None
        new_edges, keep = collapse_short_wrappers(
            ft_full.edges if ft_full.edges is not None else np.zeros((0, 2), dtype=np.int32),
            ft_full.loc,
            args.max_loc,
        )
        keep_3 = keep & (ft_full.loc >= 3)
        remap = -np.ones(len(ft_full), dtype=np.int32)
        remap[np.flatnonzero(keep_3)] = np.arange(int(keep_3.sum()), dtype=np.int32)
        if len(new_edges):
            valid_e = keep_3[new_edges[:, 0]] & keep_3[new_edges[:, 1]]
            remapped_edges = remap[new_edges[valid_e]]
        else:
            remapped_edges = new_edges
        ft_col = FunctionTable(
            repo=ft_full.repo,
            name=ft_full.name[keep_3],
            path=ft_full.path[keep_3],
            language=ft_full.language[keep_3],
            loc=ft_full.loc[keep_3],
            archetype=ft_full.archetype[keep_3],
            key=ft_full.key[keep_3],
            vectors=ft_full.vectors[keep_3],
            edges=remapped_edges,
        )
        n_col, t1_col, se_col = run_seed_extend(
            ft_col, comp_all[keep_3], ref_ft, rv, xr, hr, ref_comp, r_norm, ref_nbrs, tax, port, len(ref.archetype_names), bp
        )
        print(
            f"{port:16s} | n: {n_raw:4d} -> {n_col:4d} | "
            f"T1 name: {t1_raw[2]:2d}/{t1_raw[0]:<2d} ({t1_raw[3]:5.1%}) -> {t1_col[2]:2d}/{t1_col[0]:<2d} ({t1_col[3]:5.1%}) | "
            f"S+E name: {se_raw[2]:3d}/{se_raw[0]:<3d} ({se_raw[3]:5.1%}) -> {se_col[2]:3d}/{se_col[0]:<3d} ({se_col[3]:5.1%}) | "
            f"S+E sub: {se_raw[1]:5.1%} -> {se_col[1]:5.1%}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
