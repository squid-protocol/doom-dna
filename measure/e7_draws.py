"""DOOM-E7 Amendment 2: replicated decoy shuffles for the structure arm.

    python e7_draws.py --work /srv/.../doom-e7-work [--k 100] [--workers 3] [--only a,b]

For every ordered Phase A program pair, the real twin search is computed ONCE; only the decoy shuffle changes (seeds 0..K-1, seed 0 = E7's original draw).
Per pair and seed it records the cutoff, the twin count and the decoy-hit count, and it stores the decoy nearest distances so other summaries can be formed
offline. Output: <work>/results/e7/draws/draws_long.csv (one row per pair and seed) and draws_decoys.npz. Seed 0 reproduces E7's single-shuffle table exactly
(checked by tests/test_e7_draws.py). Nothing here reads a verdict; it only reuses E7's fingerprints.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, str(HERE))
from structural_fingerprint import twins as TW  # noqa: E402
from structural_fingerprint.twins import TwinParams  # noqa: E402

ELIGIBLE_LOC = 6


def pair_draws(query, target, seeds, params=None):
    """Real search once; decoy per seed. Returns (rows, decoy_arrays)."""
    p = params or TwinParams(min_loc=ELIGIBLE_LOC)
    qm = np.flatnonzero(query.loc >= p.min_loc)
    tm = np.flatnonzero(target.loc >= p.min_loc)
    scale = np.sqrt(query.vectors.shape[1]) if query.vectors.size else 1.0
    qv, tv = query.vectors[qm], target.vectors[tm]
    d1, d2, i1 = TW._top2(qv, tv, p.block)
    d1, d2 = d1 / scale, d2 / scale
    _, _, back = TW._top2(tv, qv, p.block)
    reciprocal = (i1 >= 0) & (back[np.maximum(i1, 0)] == np.arange(len(qm)))
    t_pass = reciprocal & TW._distinct(d1, d2, p.ratio) & np.isfinite(d1)
    t_keys, q_keys = target.key[tm], query.key[qm]
    tu, tc = np.unique(t_keys, return_counts=True)
    qu, qc = np.unique(q_keys, return_counts=True)
    uniq = np.intersect1d(tu[tc == 1], qu[qc == 1])
    exact = np.isin(q_keys, uniq) & (query.loc[qm] >= 2 * p.min_loc)
    ex_idx = np.flatnonzero(exact)
    rows, dec = [], {}
    for seed in seeds:
        decoy = TW._decoy(tv, target.archetype[tm], f"{query.repo}\0{target.repo}\0{seed}")
        e1, e2, ei = TW._top2(qv, decoy, p.block)
        e1, e2 = e1 / scale, e2 / scale
        _, _, eback = TW._top2(decoy, qv, p.block)
        e_recip = (ei >= 0) & (eback[np.maximum(ei, 0)] == np.arange(len(qm)))
        e_pass = e_recip & TW._distinct(e1, e2, p.ratio) & np.isfinite(e1)
        thr, est = TW._fdr_threshold(d1[t_pass], e1[e_pass], p.fdr)
        ok = np.flatnonzero(t_pass & (d1 <= thr))
        twins = len(np.union1d(ok, ex_idx))
        rows.append(dict(q=query.repo, t=target.repo, seed=seed, elig_q=len(qm), elig_t=len(tm), threshold=thr, est_fdr=est, twins=twins,
                         exact=len(ex_idx), candidates=int(t_pass.sum()), decoy_distinct=int(e_pass.sum()),
                         decoy_hits=int((e_pass & (e1 <= thr)).sum())))
        dec[seed] = e1[e_pass].astype(np.float32)
    return rows, dec, d1[t_pass].astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="/srv/storage_16tb/projects/doom-e7-work")
    ap.add_argument("--k", type=int, default=100)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    import e7_run as R
    work = Path(a.work)
    out = work / "results" / "e7" / "draws"
    out.mkdir(parents=True, exist_ok=True)
    progs = R.load_programs()
    names = [p["name"] for p in progs if p["role"] in R.MAP_ROLES]
    if a.only:
        names = [n for n in names if n in a.only.split(",")]
    fps, spec = R.fingerprints(names, work / "results" / "e7" / "phaseA" / "fingerprints")
    tables = {n: fp.functions for n, fp in zip(names, fps)}
    seeds = list(range(a.k))
    pairs = [(i, j) for i in names for j in names if i != j]
    done = set()
    long_p = out / "draws_long.csv"
    if long_p.exists():
        with open(long_p) as f:
            done = {(r["q"], r["t"]) for r in csv.DictReader(f)}
    todo = [p for p in pairs if p not in done]
    print(f"{len(pairs)} ordered pairs, {len(todo)} to do, K={a.k}, spec {spec}", flush=True)
    t0 = time.time()
    first = not long_p.exists()
    with open(long_p, "a", newline="") as f, ThreadPoolExecutor(a.workers) as ex:
        w = None
        for n, (rows, dec, real) in enumerate(ex.map(lambda p: pair_draws(tables[p[0]], tables[p[1]], seeds), todo), 1):
            if w is None:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                if first:
                    w.writeheader()
            w.writerows(rows)
            f.flush()
            np.savez_compressed(out / f"dec_{rows[0]['q']}__{rows[0]['t']}.npz", real=real, **{f"s{s}": v for s, v in dec.items()})
            if n % 100 == 0:
                print(f"{n}/{len(todo)} pairs, {time.time() - t0:.0f}s", flush=True)
    print("done", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
