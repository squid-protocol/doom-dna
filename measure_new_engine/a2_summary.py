"""Replication helper (NEW code): recompute the summary quantities quoted in results/e7_amendment2/E7_AMENDMENT_2_RESULTS.md.

    python a2_summary.py --single DIR_phaseA --a2 A2_DIR [--fixed-from FROZEN_PHASEA_DIR] [--json OUT]

--single : the single-shuffle phase A directory (pairs_struct.csv, run_meta.json) of the run being summarised.
--a2     : the Amendment 2 output directory (pair_diagnostics.csv, primary/, conservative/).
--fixed-from : the frozen ORIGINAL phase A directory; its pairs_struct.csv defines the fixed set of programs the original
           E7 called structurally detectable (so the same 25 programs are scored in both runs).
Definitions are the ones the Amendment 2 results used (verified by running this on the original data, see the
results file): 'active' pair = share twins/elig_q at least 0.02 under the primary or the conservative rule;
stability classes from the single-shuffle certified fraction c (>= 0.9, <= 0.1, else unstable); convergence = share of
active pairs whose twin count at K = 12 and K = 25 differ by more than 2% of elig_q; detectable at floor f = a program whose
largest symmetrised Wilson lower bound with any other program is at least f.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
import e7_trees as T  # noqa: E402

REPO = HERE.parent
FLOORS = (0.02, 0.03, 0.05, 0.08)


def rd(p):
    return list(csv.DictReader(open(p)))


def wilson_matrix(rows, names):
    idx = {n: i for i, n in enumerate(names)}
    m = np.zeros((len(names), len(names)))
    for r in rows:
        m[idx[r["q"]], idx[r["t"]]] = float(r["wilson"])
    m = np.maximum(m, m.T)
    np.fill_diagonal(m, 0.0)
    return m


def shares(rows, names):
    idx = {n: i for i, n in enumerate(names)}
    m = np.zeros((len(names), len(names)))
    for r in rows:
        m[idx[r["q"]], idx[r["t"]]] = int(r["twins"]) / max(int(r["elig_q"]), 1)
    return m


def detectable(wm, names, floor):
    return {n for i, n in enumerate(names) if wm[i].max() >= floor}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--single", required=True, type=Path)
    ap.add_argument("--a2", required=True, type=Path)
    ap.add_argument("--fixed-from", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    names = json.load(open(a.single / "run_meta.json"))["programs"]
    idx = {n: i for i, n in enumerate(names)}
    single = rd(a.single / "pairs_struct.csv")
    prim = rd(a.a2 / "primary/results/e7/phaseA/pairs_struct.csv")
    cons = rd(a.a2 / "conservative/results/e7/phaseA/pairs_struct.csv")
    dg = rd(a.a2 / "pair_diagnostics.csv")
    out = {}
    W = {"single": wilson_matrix(single, names), "primary": wilson_matrix(prim, names), "conservative": wilson_matrix(cons, names)}
    out["detectable_by_floor"] = {f"{f:.2f}": {k: len(detectable(w, names, f)) for k, w in W.items()} for f in FLOORS}
    out["detectable_programs_0.02"] = {k: sorted(detectable(w, names, 0.02)) for k, w in W.items()}
    # active pairs
    sp, sc = shares(prim, names), shares(cons, names)
    act = [(r["q"], r["t"]) for r in dg if sp[idx[r["q"]], idx[r["t"]]] >= 0.02 or sc[idx[r["q"]], idx[r["t"]]] >= 0.02]
    dgi = {(r["q"], r["t"]): r for r in dg}
    out["active_pairs"] = len(act)
    out["P_A1_cutoff_above_zero"] = float(np.mean([float(dgi[k]["thr_primary"]) > 0 for k in act])) if act else float("nan")
    cls = {"stable-certified": 0, "stable-uncertified": 0, "unstable": 0}
    for k in act:
        c = float(dgi[k]["c_certified"])
        cls["stable-certified" if c >= 0.9 else "stable-uncertified" if c <= 0.1 else "unstable"] += 1
    out["stability_classes_active"] = cls
    out["convergence_share_active_pairs_k12_vs_k25_differ_gt_2pct"] = float(np.mean(
        [abs(int(dgi[k]["twins_primary"]) - int(dgi[k]["twins_k12"])) > 0.02 * int(dgi[k]["elig_q"]) for k in act])) if act else float("nan")
    # linuxdoom row: single vs primary vs conservative share per port (P-A2, P-A3)
    ss = shares(single, names)
    li = idx["linuxdoom"]
    out["linuxdoom_to_port_share"] = {n: {"single": float(ss[li, i]), "primary": float(sp[li, i]), "conservative": float(sc[li, i])}
                                      for n, i in idx.items() if n != "linuxdoom"}
    # controls (P-A4)
    ctrl = [n for n in ("nginx", "leveldb", "curl", "libuv") if n in idx]
    others = [i for n, i in idx.items() if n not in ctrl]
    pm = np.maximum(sp, sp.T)
    out["P_A4_max_share_unrelated_controls_primary"] = float(max(pm[idx[c], others].max() for c in ctrl))
    # cross-language background (primary)
    grp = {r["name"]: r["language_group"] for r in rd(REPO / "manifest" / "e7_groups.csv")}
    wr = {(r["q"], r["t"]): float(r["wilson"]) for r in prim}  # ordered pairs, unsymmetrised Wilson lower bound
    vals = [v for (q, t), v in wr.items() if grp[q] != grp[t]]
    out["cross_language_pairs_primary"] = {"n": len(vals), "median": float(np.median(vals)), "p95": float(np.percentile(vals, 95)),
                                           "p99": float(np.percentile(vals, 99)), "max": float(max(vals)),
                                           "share_above_0.02": float(np.mean(np.array(vals) > 0.02))}
    # fixed set nearest-is-family (E7's own detectable programs)
    if a.fixed_from:
        fnames = json.load(open(a.fixed_from / "run_meta.json"))["programs"]
        fw = wilson_matrix(rd(a.fixed_from / "pairs_struct.csv"), fnames)
        fixed = detectable(fw, fnames, 0.02)
        out["fixed_set_n"] = len(fixed)
        out["fixed_set"] = sorted(fixed)
        lin, bas = REPO / "manifest" / "declared_lineage.csv", REPO / "manifest" / "declared_lineage_basis.csv"
        decl = T.build_declared(lin, bas, names)
        for k, w in W.items():
            dist = 1.0 - np.maximum(w, np.eye(len(names)))
            skip = {n for n in names if n not in fixed}
            out.setdefault("nearest_is_family_fixed_set", {})[k] = float(T.nearest_is_family(dist, names, decl, include_root_siblings=False, skip=skip)[1])
            own = detectable(w, names, 0.02)
            skip2 = {n for n in names if n not in own}
            out.setdefault("nearest_is_family_own_detectable", {})[k] = float(T.nearest_is_family(dist, names, decl, include_root_siblings=False, skip=skip2)[1])
    txt = json.dumps(out, indent=1)
    print(txt)
    if a.json:
        a.json.write_text(txt + "\n")


if __name__ == "__main__":
    main()
