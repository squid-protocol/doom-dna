"""Replication helper (NEW code): how far do the pair shares move between two runs? Usage: python pair_shift.py A_pairs_struct.csv B_pairs_struct.csv [LABEL]"""
import csv
import sys

import numpy as np


def sh(p):
    return {(r["q"], r["t"]): int(r["twins"]) / max(int(r["elig_q"]), 1) for r in csv.DictReader(open(p))}


a, b = sh(sys.argv[1]), sh(sys.argv[2])
d = np.array([b[k] - a[k] for k in a])
ad = np.abs(d)
print(f"{sys.argv[3] if len(sys.argv) > 3 else ''} {len(d)} ordered pairs: median |change| {np.median(ad):.4f}, 95th pct {np.percentile(ad, 95):.4f}, 99th {np.percentile(ad, 99):.4f}, "
      f"max {ad.max():.3f}; pairs with |change| >= 0.01: {int((ad >= .01).sum())}, >= 0.03: {int((ad >= .03).sum())}, >= 0.10: {int((ad >= .10).sum())}")
top = sorted(a, key=lambda k: -abs(b[k] - a[k]))[:8]
for k in top:
    print(f"   {k[0]} -> {k[1]}: {a[k]:.3f} -> {b[k]:.3f}")
