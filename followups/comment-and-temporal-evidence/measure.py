"""3-Layer Port Evidence Sweep: Pure Structure, Comments-Only RBH, and Multi-Modal (FGW+Ext)."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from structural_fingerprint import blind as BL
from structural_fingerprint.fingerprint import build
from structural_fingerprint.port_evidence import (
    _DROP_COMPLEXITY,
    _comment_rbh,
    _count_name_ok,
    _jaccard_matrix,
    _prepare_side,
    _seed_and_extend,
)
from structural_fingerprint.reference import load_reference
from structural_fingerprint.scan_io import load_scan, resolve_scans


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate Structure, Comments-Only, and Multi-Modal alignment")
    ap.add_argument("--scans", required=True, help="Directory of port scan subdirectories")
    ap.add_argument("--repos", required=True, help="Directory of port git checkouts")
    ap.add_argument("--extra-scans", action="append", default=[], help="Control scan directories")
    ap.add_argument("--extra-repos", action="append", default=[], help="Control repo directories")
    ap.add_argument("--max-funcs", type=int, default=15000)
    ap.add_argument("--out-csv", default=str(Path(__file__).with_name("results_all.csv")))
    args = ap.parse_args()

    scans_root = Path(args.scans)
    repos_root = Path(args.repos)
    ref = load_reference("portable")
    bp = BL.BlindParams()
    keep_cols = [i for i, n in enumerate(ref.feature_names) if n not in _DROP_COMPLEXITY]

    ld_db = resolve_scans([scans_root / "linuxdoom"])[0]
    origin = _prepare_side(ld_db, ref, bp, keep_cols, 3, repos_root / "linuxdoom", None)

    targets: list[tuple[str, str, Path, Path]] = []
    for d in sorted(scans_root.iterdir()):
        if d.is_dir() and d.name != "linuxdoom":
            targets.append(("port", d.name, d, repos_root / d.name))
    for es, er in zip(args.extra_scans, args.extra_repos, strict=True):
        es_p, er_p = Path(es), Path(er)
        for d in sorted(es_p.iterdir()):
            if d.is_dir():
                targets.append(("ctrl", d.name, d, er_p / d.name))

    rows_out: list[dict[str, object]] = []
    for kind, name, sdir, rdir in targets:
        dbs = resolve_scans([sdir])
        if not dbs:
            continue
        scan = load_scan(dbs[0], ref.signal_columns)
        ft = build(scan, ref, min_loc=3, keyword_mode="composition").functions
        assert ft is not None
        view = BL.blind_view(ft)
        if view.n < 10 or view.n > args.max_funcs:
            print(f"{kind:4s} {name:25s} | {view.n:5d} | skipped")
            continue

        side = _prepare_side(dbs[0], ref, bp, keep_cols, 3, rdir if rdir.exists() else None, None)
        j_mat = _jaccard_matrix(side.toks, origin.toks)

        m_struct, _, _ = _seed_and_extend(side, origin, bp)
        m_multi, _, _ = _seed_and_extend(side, origin, bp, j_mat=j_mat, fgw_comment_w=0.25, ext_comment_w=1.0)
        m_cmt = _comment_rbh(j_mat, side.toks, origin.toks)

        s_ok = _count_name_ok(m_struct, side, origin)
        m_ok = _count_name_ok(m_multi, side, origin)
        c_ok = _count_name_ok(m_cmt, side, origin)
        n_cmt = sum(1 for t in side.toks if len(t) >= 3)

        print(
            f"{kind:4s} {name:25s} | n={side.view.n:5d} | "
            f"struct={s_ok}/{len(m_struct)} | cmt_rbh={c_ok}/{len(m_cmt)} | multi={m_ok}/{len(m_multi)}"
        )
        rows_out.append({
            "type": kind,
            "port": name,
            "n": side.view.n,
            "n_cmt3": n_cmt,
            "struct_ok": s_ok,
            "struct_n": len(m_struct),
            "struct_pct": round(100.0 * s_ok / max(1, len(m_struct)), 2),
            "cmt_ok": c_ok,
            "cmt_n": len(m_cmt),
            "cmt_pct": round(100.0 * c_ok / max(1, len(m_cmt)), 2),
            "multi_ok": m_ok,
            "multi_n": len(m_multi),
            "multi_pct": round(100.0 * m_ok / max(1, len(m_multi)), 2),
        })

    out_path = Path(args.out_csv)
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
