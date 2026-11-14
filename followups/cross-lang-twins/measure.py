"""DOOM-E3 (Cross-Language Twins): Within-repo rank-normalized function-to-function twins.

Tests whether rank-normalizing each feature column within its own repository enables
direct ``twins.py`` function matching across languages (C <-> Go, Dart, Scheme).
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import numpy as np


def rank_normalize_columns(vectors: np.ndarray) -> np.ndarray:
    """Rank-normalize each feature column within a single repository to [0, 1].

    Constant columns map to 0.5 so they contribute zero variance.
    """
    n, d = vectors.shape
    if n <= 1 or d == 0:
        return np.full((n, d), 0.5, dtype=np.float32)
    out = np.empty((n, d), dtype=np.float32)
    for j in range(d):
        col = vectors[:, j]
        if np.all(col == col[0]):
            out[:, j] = 0.5
            continue
        order = np.argsort(col, kind="mergesort")
        ranks = np.empty(n, dtype=np.float64)
        ranks[order] = np.arange(n, dtype=np.float64)
        out[:, j] = (ranks / (n - 1)).astype(np.float32)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Test cross-language function twins with within-repo rank normalization")
    ap.add_argument("--scans", required=True)
    ap.add_argument("--ports", default="chocolate-doom,gore,dartdoom,doom-scheme,mochadoom,room4doom")
    args = ap.parse_args()

    from structural_fingerprint.fingerprint import build
    from structural_fingerprint.reference import load_reference
    from structural_fingerprint.scan_io import load_scan, resolve_scans
    from structural_fingerprint.subway import Taxonomy
    from structural_fingerprint.twins import TwinParams, find_twins

    root = Path(args.scans)
    tax = Taxonomy.load(Path(__file__).resolve().parents[2] / "manifest" / "subsystems.json")
    ref = load_reference("portable")
    params = TwinParams(min_loc=6, ratio=0.85, fdr=0.05)

    def load_ft(name: str, mode: str, rank_norm: bool):
        db = resolve_scans([root / name])[0]
        ft = build(load_scan(db, ref.signal_columns), ref, min_loc=3, keyword_mode=mode).functions
        assert ft is not None
        if rank_norm:
            ft = replace(ft, vectors=rank_normalize_columns(ft.vectors))
        return ft

    ref_raw = load_ft("linuxdoom", "density", False)
    ref_comp_norm = load_ft("linuxdoom", "composition", True)

    for port in args.ports.split(","):
        for label, r_ft, mode, rn in [
            ("baseline(dens,raw)", ref_raw, "density", False),
            ("e3(comp,rank_norm)", ref_comp_norm, "composition", True),
        ]:
            p_ft = load_ft(port, mode, rn)
            res = find_twins(p_ft, r_ft, params)
            same_sub = 0
            same_name = 0
            for qi, ti in zip(res.q_index, res.t_index, strict=True):
                if tax.classify(str(p_ft.path[qi]), port) == tax.classify(str(r_ft.path[ti]), "linuxdoom"):
                    same_sub += 1
                pn = str(p_ft.name[qi]).strip().lower()
                rn_str = str(r_ft.name[ti]).strip().lower()
                if pn == rn_str or (pn.split("_", 1)[-1] == rn_str.split("_", 1)[-1] and "_" in rn_str):
                    same_name += 1
            n = res.accepted
            sub_pct = f"{same_sub / n:.1%}" if n else "n/a"
            name_pct = f"{same_name / n:.1%}" if n else "n/a"
            print(f"{port:15s} | {label:20s} | twins={n:4d} (eligible={res.eligible:4d}, thr={res.threshold:.3f}) | same_sub={sub_pct:>5} | same_name={name_pct:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
