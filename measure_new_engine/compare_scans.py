"""Replication helper (NEW code): compare two scan databases of the same program on what the structure arm reads.

    python compare_scans.py A_DB B_DB [--json]

Functions are aligned on (file path, function name, occurrence number within that pair), so database row ids do not
matter. Reports counts of functions in each, how many align, and how many aligned functions differ in loc, complexity,
args, keyword_density, fan_in, fan_out and in each reference signal column; plus the number of call edges (descriptive only).
"""
from __future__ import annotations

import argparse
import collections
import json
import sys

import numpy as np

sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
from structural_fingerprint.reference import load_reference  # noqa: E402
from structural_fingerprint.scan_io import load_scan  # noqa: E402

SCALARS = ("loc", "complexity", "args", "keyword_density", "fan_in", "fan_out")


def keyed(scan):
    seen = collections.Counter()
    out = {}
    paths = scan.func_path
    for i, (p, n) in enumerate(zip(paths, scan.func_name)):
        k = (p, n, seen[(p, n)])
        seen[(p, n)] += 1
        out[k] = i
    return out


def compare(a_db, b_db):
    ref = load_reference("structure")
    A = load_scan(a_db, ref.signal_columns, name="a")
    B = load_scan(b_db, ref.signal_columns, name="b")
    ka, kb = keyed(A), keyed(B)
    common = sorted(set(ka) & set(kb))
    ia = np.array([ka[k] for k in common], dtype=int)
    ib = np.array([kb[k] for k in common], dtype=int)
    r = dict(n_a=A.n_functions, n_b=B.n_functions, aligned=len(common), only_a=len(set(ka) - set(kb)), only_b=len(set(kb) - set(ka)),
             edges_a=int(len(A.call_edges)), edges_b=int(len(B.call_edges)), missing_a=list(A.missing_signals), missing_b=list(B.missing_signals))
    for s in SCALARS:
        x, y = getattr(A, s)[ia], getattr(B, s)[ib]
        r[f"diff_{s}"] = int((~np.isclose(x, y, rtol=0, atol=1e-9)).sum())
    sig_diff = {}
    for j, c in enumerate(ref.signal_columns):
        d = int((A.signals[ia, j] != B.signals[ib, j]).sum())
        if d:
            sig_diff[c] = d
    r["diff_signal_columns"] = sig_diff
    anysig = (A.signals[ia] != B.signals[ib]).any(1) if len(ia) else np.zeros(0, bool)
    anyscalar = np.zeros(len(ia), bool)
    for s in SCALARS[:4]:
        anyscalar |= ~np.isclose(getattr(A, s)[ia], getattr(B, s)[ib], rtol=0, atol=1e-9)
    r["functions_with_any_vector_input_diff"] = int((anysig | anyscalar).sum())
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("a"), ap.add_argument("b")
    a = ap.parse_args()
    print(json.dumps(compare(a.a, a.b), indent=1))
