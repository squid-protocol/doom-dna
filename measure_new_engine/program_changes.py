"""Replication helper (NEW code): per-program detectability, nearest relative and share, original vs new engine.

    python program_changes.py --orig PHASE_A_DIR --new PHASE_A_DIR [--arm struct|names] [--label TEXT] --out FILE.md

Uses the symmetrised Wilson lower bound exactly as e7_analyze.py does (struct: pairs_struct.csv column wilson; names: pairs_names.csv
column wilson_cert), floor 0.02. A program is listed when its detectability or its nearest program changes, or its best share moves by >= 0.03.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

FLOOR = 0.02


def load(d, arm):
    names = json.load(open(d / "run_meta.json"))["programs"]
    idx = {n: i for i, n in enumerate(names)}
    f, col = ("pairs_struct.csv", "wilson") if arm == "struct" else ("pairs_names.csv", "wilson_cert")
    m = np.zeros((len(names), len(names)))
    for r in csv.DictReader(open(d / f)):
        m[idx[r["q"]], idx[r["t"]]] = float(r[col])
    m = np.maximum(m, m.T)
    np.fill_diagonal(m, 0)
    return names, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig", type=Path, required=True)
    ap.add_argument("--new", type=Path, required=True)
    ap.add_argument("--arm", default="struct")
    ap.add_argument("--label", default="")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    no, mo = load(a.orig, a.arm)
    nn, mn = load(a.new, a.arm)
    assert no == nn
    lines = [f"| program | detectable (orig -> new) | nearest (orig) | best share (orig) | nearest (new) | best share (new) |", "|---|---|---|---:|---|---:|"]
    cnt = 0
    for i, n in enumerate(no):
        jo, jn = int(mo[i].argmax()), int(mn[i].argmax())
        so, sn = mo[i, jo], mn[i, jn]
        do, dn = so >= FLOOR, sn >= FLOOR
        nearo = no[jo] if do else "none"
        nearn = no[jn] if dn else "none"
        # a tie at the top is not a change of nearest: compare by value of the new best partner in the old matrix
        changed_near = (nearo != nearn) and not (do and dn and abs(mo[i, jn] - so) < 1e-12)
        if do != dn or changed_near or abs(sn - so) >= 0.03:
            cnt += 1
            lines.append(f"| {n} | {'yes' if do else 'no'} -> {'yes' if dn else 'no'} | {nearo} | {so:.4f} | {nearn} | {sn:.4f} |")
    a.out.write_text(f"{a.label} ({a.arm}, floor {FLOOR}): {cnt} of {len(no)} programs listed\n\n" + "\n".join(lines) + "\n")
    print(cnt, "listed")


if __name__ == "__main__":
    main()
