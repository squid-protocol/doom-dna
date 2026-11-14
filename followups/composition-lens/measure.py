"""DOOM-E2: Compare cross-language alignment across density, smoothed_density, and composition modes.

Usage:
    python followups/composition-lens/measure.py --scans DIR --out DIR
"""

from __future__ import annotations

import argparse
from pathlib import Path

MODES = ("density", "smoothed_density", "composition")


def main() -> int:
    ap = argparse.ArgumentParser(description="DOOM-E2: compare keyword modes on portable lens")
    ap.add_argument("--scans", required=True, help="Directory of GitGalaxy scan databases")
    ap.add_argument("--out", required=True, help="Output directory")
    args = ap.parse_args()

    from structural_fingerprint import cli as sfs_cli

    out = Path(args.out)
    manifest_dir = Path(__file__).resolve().parents[2] / "manifest"
    for mode in MODES:
        mode_out = out / mode
        rc = sfs_cli.main([
            "subway",
            args.scans,
            "--reference", "linuxdoom",
            "--taxonomy", str(manifest_dir / "subsystems.json"),
            "--declared-lineage", str(manifest_dir / "declared_lineage.csv"),
            "--lens", "portable",
            "--keyword-mode", mode,
            "-o", str(mode_out),
        ])
        if rc != 0:
            return rc
    print(f"wrote DOOM-E2 comparison across {MODES} to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
