"""Replication helper (NEW code): do call-graph-only changes reach the structure arm's twin vectors?

    python attribution_check.py   (reads the C1 = #8939 and NEW phase A fingerprints and compare_all.csv)

For each of the 51 map programs: did the call-graph outputs (call edges or per-function fan-in/fan-out) differ between the #8939 scan and the new scan, and are the
fingerprint's twin vectors and structural keys byte-identical between the two?
"""
import csv
import os

import numpy as np

W = "/srv/storage_16tb/projects/doom-e7-newengine-work/"
rows = [r for r in csv.DictReader(open(W + "compare/compare_all.csv")) if r["pair"] == "c1->new"]
res = []
for r in rows:
    n = r["program"]
    fa, fb = W + f"c1/results/e7/phaseA/fingerprints/{n}.sfp.npz", W + f"new/results/e7/phaseA/fingerprints/{n}.sfp.npz"
    if not (os.path.exists(fa) and os.path.exists(fb)):
        continue
    a, b = np.load(fa, allow_pickle=True), np.load(fb, allow_pickle=True)
    same = a["vectors"].shape == b["vectors"].shape and np.array_equal(a["vectors"], b["vectors"]) and np.array_equal(a["key"], b["key"])
    graph = r["edges_a"] != r["edges_b"] or int(r["diff_fan_in"]) or int(r["diff_fan_out"])
    res.append((n, same, bool(graph), int(r["funcs_vector_input_diff"])))
g = [x for x in res if x[2]]
print(f"map programs compared: {len(res)}")
print(f"programs whose call-graph outputs (edges or fan-in/out) differ between #8939 and the new engine: {len(g)}")
print(f"  of those, twin vectors and keys byte-identical: {sum(1 for x in g if x[1])}; not identical (program, functions whose vector inputs changed): {[(x[0], x[3]) for x in g if not x[1]]}")
print(f"programs with byte-identical twin vectors and keys, all: {sum(x[1] for x in res)} of {len(res)}")
