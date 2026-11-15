"""Score preregistered DOOM-E6 held-out partial-engine hybrids and id Tech 4 against linuxdoom."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from structural_fingerprint import blind as BL
from structural_fingerprint import features as F
from structural_fingerprint.fingerprint import build
from structural_fingerprint.lattice import keyword_lattice_distance, keyword_lattice_profile
from structural_fingerprint.reference import load_reference
from structural_fingerprint.scan_io import load_scan, resolve_scans


def _norm_name(s: str) -> str:
    return s.strip().lower().replace("-", "_")


def _same_name(a: str, b: str) -> bool:
    na, nb = _norm_name(a), _norm_name(b)
    if na == nb:
        return True
    if "_" in nb and na.split("_", 1)[-1] == nb.split("_", 1)[-1]:
        return len(na.split("_", 1)[-1]) >= 4
    return False


def _prefix(name: str) -> str:
    head = name.split("_", 1)[0].upper()
    return head if len(head) <= 3 and "_" in name else "other"


def main() -> int:
    ref = load_reference("portable")
    bp = BL.BlindParams()

    ld_db = resolve_scans([Path("/srv/storage_16tb/projects/gitgalaxy/doom-study/rescan-6c7c6c1bc/scans/6c7c6c1bc/linuxdoom")])[0]
    ref_scan = load_scan(ld_db, ref.signal_columns)
    ref_ft = build(ref_scan, ref, min_loc=3, keyword_mode="composition").functions
    rv = BL.blind_view(ref_ft)
    xr = BL.descriptors(rv, len(ref.archetype_names), bp.use_graph, bp.use_measures, None, bp.geometry_only)
    hr = BL.hop_matrix(rv, bp.hop_cap)
    ref_comp = F.raw_features(
        ref, ref_scan.loc, ref_scan.complexity, ref_scan.args, ref_scan.keyword_density, ref_scan.signals,
        keyword_mode="composition",
    )[rv.rows]
    r_norm = ref_comp / np.maximum(np.linalg.norm(ref_comp, axis=1, keepdims=True), 1e-9)
    ref_nbrs: dict[int, set[int]] = defaultdict(set)
    for u, v in rv.edges.tolist():
        if u != v:
            ref_nbrs[u].add(v)
            ref_nbrs[v].add(u)
    _, _, ref_kw = keyword_lattice_profile(ref_scan.signals, rv.rows)

    e6_root = Path("/tmp/doom-e6/scans")
    for name in ["heretic", "hexen", "doom64ex", "srb2", "dhewm3"]:
        p_db = resolve_scans([e6_root / name])[0]
        p_scan = load_scan(p_db, ref.signal_columns)
        p_ft = build(p_scan, ref, min_loc=3, keyword_mode="composition").functions
        pv = BL.blind_view(p_ft)
        if pv.n > 15000:
            print(f"{name:12s} | n={pv.n} (>15000, skipping dense FGW)")
            continue
        xp = BL.descriptors(pv, len(ref.archetype_names), bp.use_graph, bp.use_measures, None, bp.geometry_only)
        hp = BL.hop_matrix(pv, bp.hop_cap)

        m = BL._sqdist(xp, xr)
        m = m / (m.max() or 1.0)
        t = BL.fused_gw(m, hp, hr, bp.alpha, bp.epsilon, bp.outer)
        fgw_cost = float(np.sum(t * m))

        best_r = np.argmax(t, axis=1)
        best_p = np.argmax(t, axis=0)
        rbh = [(i, int(best_r[i]), float(t[i, best_r[i]])) for i in range(pv.n) if best_p[best_r[i]] == i]
        rbh.sort(key=lambda x: x[2], reverse=True)
        k_seed = max(1, int(len(rbh) * 0.15)) if rbh else 0
        seeds = rbh[:k_seed]

        p_comp = F.raw_features(
            ref, p_scan.loc, p_scan.complexity, p_scan.args, p_scan.keyword_density, p_scan.signals,
            keyword_mode="composition",
        )[pv.rows]
        delta = np.mean(p_comp[[i for i, _, _ in seeds]] - ref_comp[[j for _, j, _ in seeds]], axis=0) if seeds else np.zeros(p_comp.shape[1])
        p_sh = p_comp - delta
        p_sh_norm = p_sh / np.maximum(np.linalg.norm(p_sh, axis=1, keepdims=True), 1e-9)

        p_nbrs: dict[int, set[int]] = defaultdict(set)
        for u, v in pv.edges.tolist():
            if u != v:
                p_nbrs[u].add(v)
                p_nbrs[v].add(u)

        matched = {i: j for i, j, _ in seeds}
        used_r = set(matched.values())
        for _ in range(3):
            proposals: list[tuple[float, int, int]] = []
            for pu in range(pv.n):
                if pu in matched:
                    continue
                cand_votes: Counter[int] = Counter()
                for pn in p_nbrs.get(pu, ()):
                    if pn in matched:
                        for rc in ref_nbrs.get(matched[pn], ()):
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
                if pu not in matched and ru not in used_r:
                    matched[pu] = ru
                    used_r.add(ru)
                    added += 1
            if added == 0:
                break

        t1_hits = sum(1 for i, j, _ in seeds if _same_name(str(p_ft.name[pv.rows[i]]), str(ref_ft.name[rv.rows[j]])))
        se_hits_pairs = [
            (str(p_ft.name[pv.rows[i]]), str(ref_ft.name[rv.rows[j]]))
            for i, j in matched.items()
            if _same_name(str(p_ft.name[pv.rows[i]]), str(ref_ft.name[rv.rows[j]]))
        ]
        _, _, p_kw = keyword_lattice_profile(p_scan.signals, pv.rows)
        kw_jsd = keyword_lattice_distance(p_kw, ref_kw)

        pref_counts = Counter(_prefix(rn) for _, rn in se_hits_pairs)
        top_prefs = ", ".join(f"{k}:{v}" for k, v in pref_counts.most_common(6))
        print(
            f"{name:10s} | n={pv.n:5d} | FGW={fgw_cost:.3f} | kw_JSD={kw_jsd:.3f} | "
            f"T1={t1_hits:3d}/{len(seeds):<3d} ({t1_hits/max(1,len(seeds)):5.1%}) | "
            f"SE={len(se_hits_pairs):3d}/{len(matched):<3d} ({len(se_hits_pairs)/max(1,len(matched)):5.1%}) | "
            f"prefixes=[{top_prefs}]"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
