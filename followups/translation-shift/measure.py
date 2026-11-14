"""Compare paired (linuxdoom, port) functions to measure:
1. Systematic feature shifts (the 'translation vector' between C and Go/Dart/Scheme/Java).
2. Seed-and-extend (Tier-1 anchor -> Tier-2 1-hop neighbor) cross-language matching.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np


def _norm_name(s: str) -> str:
    return s.strip().lower().replace("-", "_")


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure translation shifts and Tier-1 -> Tier-2 anchor propagation")
    ap.add_argument("--scans", required=True)
    ap.add_argument("--ports", default="gore,dartdoom,doom-scheme,mochadoom")
    args = ap.parse_args()

    from structural_fingerprint import features as F
    from structural_fingerprint.reference import load_reference
    from structural_fingerprint.scan_io import load_scan, resolve_scans

    root = Path(args.scans)
    ref = load_reference("portable")
    ref_scan = load_scan(resolve_scans([root / "linuxdoom"])[0], ref.signal_columns)
    ref_raw = F.raw_features(
        ref, ref_scan.loc, ref_scan.complexity, ref_scan.args, ref_scan.keyword_density, ref_scan.signals,
        keyword_mode="density",
    )
    ref_comp = F.raw_features(
        ref, ref_scan.loc, ref_scan.complexity, ref_scan.args, ref_scan.keyword_density, ref_scan.signals,
        keyword_mode="composition",
    )
    ref_by_name: dict[str, int] = {}
    for i, name in enumerate(ref_scan.func_name):
        if ref_scan.loc[i] >= 6:
            k = _norm_name(name)
            if k not in ref_by_name:
                ref_by_name[k] = i

    # Build linuxdoom 1-hop undirected neighbor sets
    ref_nbrs: dict[int, set[int]] = defaultdict(set)
    for u, v in ref_scan.call_edges.tolist():
        ref_nbrs[u].add(v)
        ref_nbrs[v].add(u)

    for port in args.ports.split(","):
        pscan = load_scan(resolve_scans([root / port])[0], ref.signal_columns)
        p_raw = F.raw_features(
            ref, pscan.loc, pscan.complexity, pscan.args, pscan.keyword_density, pscan.signals,
            keyword_mode="density",
        )
        p_comp = F.raw_features(
            ref, pscan.loc, pscan.complexity, pscan.args, pscan.keyword_density, pscan.signals,
            keyword_mode="composition",
        )

        pairs: list[tuple[int, int]] = []
        for i, name in enumerate(pscan.func_name):
            if pscan.loc[i] < 6:
                continue
            k = _norm_name(name)
            j = ref_by_name.get(k)
            if j is None and "_" in k:
                j = ref_by_name.get(k.split("_", 1)[1])
            if j is not None:
                pairs.append((i, j))

        pi = np.array([a for a, _ in pairs], dtype=np.int64)
        ri = np.array([b for _, b in pairs], dtype=np.int64)
        print(f"\n=== {port} ({len(pairs)} name-paired functions >= 6 LOC) ===")

        # 1. Feature correlation & systematic shift
        corrs = []
        for col_idx, fname in enumerate(ref.feature_names):
            x = p_raw[pi, col_idx]
            y = ref_raw[ri, col_idx]
            if np.std(x) > 1e-9 and np.std(y) > 1e-9:
                r = float(np.corrcoef(x, y)[0, 1])
                shift = float(np.mean(x - y))
                corrs.append((r, shift, fname))
        corrs.sort(reverse=True)
        print("  Top correlated features (density):")
        for r, sh, fn in corrs[:6]:
            print(f"    {fn:30s} r={r:+.3f}  mean_shift={sh:+.3f}")

        # 2. Tier-1 -> Tier-2 Anchor Propagation test:
        # Use top 15% largest/most-correlated pairs as Tier-1 anchors (oracle-free proxy: top 15% by loc*complexity)
        # Wait: let's test BOTH:
        #   (a) Global nearest-neighbor in centered composition space (subtracting mean translation shift!)
        #   (b) Tier-2 local matching restricted to 1-hop neighbors of Tier-1 anchors!
        p_norm = p_comp / np.maximum(np.linalg.norm(p_comp, axis=1, keepdims=True), 1e-9)
        r_norm = ref_comp / np.maximum(np.linalg.norm(ref_comp, axis=1, keepdims=True), 1e-9)

        # Global cosine nearest neighbor among paired functions vs all ref functions >= 6 LOC
        ref_elig = np.flatnonzero(ref_scan.loc >= 6)
        r_elig_norm = r_norm[ref_elig]
        sims = p_norm[pi] @ r_elig_norm.T
        top1_global = ref_elig[np.argmax(sims, axis=1)]
        global_acc = float(np.mean(top1_global == ri))

        # Mean-shifted (whitened translation vector) global accuracy
        delta = np.mean(p_comp[pi] - ref_comp[ri], axis=0)
        p_shifted = p_comp - delta
        p_sh_norm = p_shifted / np.maximum(np.linalg.norm(p_shifted, axis=1, keepdims=True), 1e-9)
        sims_sh = p_sh_norm[pi] @ r_elig_norm.T
        top1_shifted = ref_elig[np.argmax(sims_sh, axis=1)]
        shifted_acc = float(np.mean(top1_shifted == ri))

        # Tier-1 (top 20% by cosine similarity) -> Tier-2 (1-hop call-graph neighbors of Tier-1)
        p_nbrs: dict[int, set[int]] = defaultdict(set)
        for u, v in pscan.call_edges.tolist():
            p_nbrs[u].add(v)
            p_nbrs[v].add(u)

        # Simulate Tier-1 anchors: top 20% of correct/confident matches (or top 20% by similarity)
        best_sim = np.max(sims_sh, axis=1)
        k_anchors = max(5, len(pairs) // 5)
        anchor_idx = np.argsort(best_sim)[-k_anchors:]
        anchor_map = {int(pi[idx]): int(ri[idx]) for idx in anchor_idx}  # true Tier-1 anchors

        tier2_hits = 0
        tier2_total = 0
        for idx in range(len(pairs)):
            pu, ru = int(pi[idx]), int(ri[idx])
            if pu in anchor_map:
                continue
            cand_refs: set[int] = set()
            for pn in p_nbrs.get(pu, ()):
                if pn in anchor_map:
                    cand_refs.update(ref_nbrs.get(anchor_map[pn], ()))
            cand_refs = {c for c in cand_refs if ref_scan.loc[c] >= 6}
            if not cand_refs:
                continue
            cands = np.array(sorted(cand_refs), dtype=np.int64)
            best_c = cands[int(np.argmax(r_norm[cands] @ p_sh_norm[pu]))]
            tier2_total += 1
            if best_c == ru:
                tier2_hits += 1

        t2_pct = f"{tier2_hits / tier2_total:.1%}" if tier2_total else "n/a"
        print(f"  1-to-1 exact-function recall: global={global_acc:.1%} | mean-shifted={shifted_acc:.1%} | Tier-2 (1-hop from top-20% anchors)={t2_pct} ({tier2_hits}/{tier2_total})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
