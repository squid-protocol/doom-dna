"""Unsupervised Seed-and-Extend Cross-Language Function Alignment.

1. Seed (Tier-1): Compute FGW coupling matrix ``T`` between port and reference
   (descriptors + hop-distance call graph, zero names) and extract reciprocal best hits.
2. Calibrate: Estimate the repo-to-repo translation vector ``delta`` in composition space
   from Tier-1 seeds.
3. Extend (Tier-2+): Iteratively propagate outward along 1-hop call-graph neighbors,
   matching port functions to reference candidates reachable from anchored neighbors.
4. Score (post-hoc only): Check 1-to-1 name-agreement precision and subsystem agreement.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def _norm_name(s: str) -> str:
    return s.strip().lower().replace("-", "_")


def _same_name(a: str, b: str) -> bool:
    na, nb = _norm_name(a), _norm_name(b)
    if na == nb:
        return True
    if "_" in nb and na.split("_", 1)[-1] == nb.split("_", 1)[-1]:
        return len(na.split("_", 1)[-1]) >= 4
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Unsupervised Seed-and-Extend cross-language function alignment")
    ap.add_argument("--scans", required=True)
    ap.add_argument("--extra-scans", action="append", default=[], help="Additional scan directories (e.g. controls)")
    ap.add_argument("--ports", default="chocolate-doom,gore,dartdoom,doom-scheme,mochadoom,room4doom")
    ap.add_argument("--all", action="store_true", help="Run on all scan subdirectories except linuxdoom")
    ap.add_argument("--seed-frac", type=float, default=0.15, help="Top fraction of FGW reciprocal best hits as Tier-1 seeds")
    ap.add_argument("--hops", type=int, default=3, help="Number of 1-hop extension rounds")
    ap.add_argument("--max-funcs", type=int, default=15000, help="Skip ports above this size to avoid O(n^2) FGW OOM")
    ap.add_argument("--out-csv", help="Optional CSV output path")
    args = ap.parse_args()

    from structural_fingerprint import blind as BL
    from structural_fingerprint import features as F
    from structural_fingerprint.fingerprint import build
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

    targets: list[tuple[str, Path]] = []
    if args.all:
        for d in sorted(root.iterdir()):
            if d.is_dir() and d.name != "linuxdoom":
                targets.append((d.name, d))
    else:
        for p in args.ports.split(","):
            targets.append((p, root / p))
    for extra in args.extra_scans:
        ep = Path(extra)
        for d in sorted(ep.iterdir()):
            if d.is_dir():
                targets.append((d.name, d))

    rows_out: list[dict[str, object]] = []
    for port, p_dir in targets:
        dbs = resolve_scans([p_dir])
        if not dbs:
            continue
        p_scan = load_scan(dbs[0], ref.signal_columns)
        p_ft = build(p_scan, ref, min_loc=3, keyword_mode="composition").functions
        assert p_ft is not None
        pv = BL.blind_view(p_ft)
        if pv.n < 10 or pv.n > args.max_funcs:
            print(f"{port:24s} | skipped (n={pv.n})")
            continue
        xp = BL.descriptors(pv, len(ref.archetype_names), bp.use_graph, bp.use_measures, None, bp.geometry_only)
        hp = BL.hop_matrix(pv, bp.hop_cap)

        m = BL._sqdist(xp, xr)
        m = m / (m.max() or 1.0)
        t = BL.fused_gw(m, hp, hr, bp.alpha, bp.epsilon, bp.outer)

        best_r = np.argmax(t, axis=1)
        best_p = np.argmax(t, axis=0)
        rbh = [(i, int(best_r[i]), float(t[i, best_r[i]])) for i in range(pv.n) if best_p[best_r[i]] == i]
        rbh.sort(key=lambda x: x[2], reverse=True)
        k_seed = max(1, int(len(rbh) * args.seed_frac)) if rbh else 0
        seeds = rbh[:k_seed]

        anchor_p_to_r: dict[int, int] = {i: j for i, j, _ in seeds}
        used_r: set[int] = set(anchor_p_to_r.values())

        p_comp_all = F.raw_features(
            ref, p_scan.loc, p_scan.complexity, p_scan.args, p_scan.keyword_density, p_scan.signals,
            keyword_mode="composition",
        )
        p_comp = p_comp_all[pv.rows]
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

        for _ in range(args.hops):
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

        t1_pairs = [(i, j) for i, j, _ in seeds]
        all_pairs = list(anchor_p_to_r.items())
        n1, sub1, nok1, nm1 = score_pairs(t1_pairs)
        na, suba, noka, nma = score_pairs(all_pairs)
        print(f"{port:24s} | n={pv.n:5d} | T1 ({n1:3d}): sub={sub1:5.1%} name={nok1:3d}/{n1:<3d} ({nm1:5.1%}) | S+E ({na:3d}): sub={suba:5.1%} name={noka:3d}/{na:<3d} ({nma:5.1%})")
        rows_out.append({
            "port": port, "n_funcs": pv.n,
            "t1_n": n1, "t1_sub": round(sub1, 4), "t1_name_hits": nok1, "t1_name_prec": round(nm1, 4),
            "se_n": na, "se_sub": round(suba, 4), "se_name_hits": noka, "se_name_prec": round(nma, 4),
        })

    if args.out_csv and rows_out:
        out_p = Path(args.out_csv)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with out_p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
            w.writeheader()
            w.writerows(rows_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
