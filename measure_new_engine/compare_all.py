"""Replication helper (NEW code): per-program scan-database comparison across the engines used.

    python compare_all.py --out DIR

Pairs compared (A -> B): original E7 scan (704cb35f0) -> C0 (same engine, this harness): does the harness reproduce E7?;
C0 -> C1 (#8939 = 3c436c8c57): what the boolean-operator split changes; C1 -> NEW (beb46cfbc): what the other 119 commits
change; ORIG -> NEW: the whole difference. Writes compare_all.csv (one row per program and pair) and compare_all.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_scans import compare  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
B = Path("/srv/storage_16tb/projects/doom-e7-newengine-work")
SETS = {"orig": Path("/srv/storage_16tb/projects/doom-e7-work/scans/704cb35f0"), "c0": B / "c0/scans/704cb35f0",
        "c1": B / "c1/scans/3c436c8c5", "new": B / "new/scans/beb46cfbc"}
PAIRS = [("orig", "c0"), ("c0", "c1"), ("c1", "new"), ("orig", "new")]


def db(tag, name):
    return SETS[tag] / name / f"{name}_galaxy_master.db"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    names = [p["name"] for p in json.load(open(REPO / "manifest" / "RUN_PINS.json"))["programs"]]
    rows, full = [], {}
    for n in names:
        for x, y in PAIRS:
            if not (db(x, n).exists() and db(y, n).exists()):
                continue
            r = compare(db(x, n), db(y, n))
            full[f"{n}|{x}->{y}"] = r
            rows.append(dict(program=n, pair=f"{x}->{y}", n_a=r["n_a"], n_b=r["n_b"], aligned=r["aligned"], only_a=r["only_a"], only_b=r["only_b"],
                             funcs_vector_input_diff=r["functions_with_any_vector_input_diff"],
                             diff_loc=r["diff_loc"], diff_complexity=r["diff_complexity"], diff_args=r["diff_args"],
                             diff_keyword_density=r["diff_keyword_density"], diff_fan_in=r["diff_fan_in"], diff_fan_out=r["diff_fan_out"],
                             edges_a=r["edges_a"], edges_b=r["edges_b"], signal_cols="; ".join(f"{k}={v}" for k, v in r["diff_signal_columns"].items())))
    a.out.mkdir(parents=True, exist_ok=True)
    with open(a.out / "compare_all.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (a.out / "compare_all.json").write_text(json.dumps(full, indent=1))
    print(f"{len(rows)} comparisons")


if __name__ == "__main__":
    main()
