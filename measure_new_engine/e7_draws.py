"""DOOM-E7 Amendment 2: replicated decoy shuffles and pooled multi-decoy cutoff for the structure arm.

    python e7_draws.py --work /srv/.../doom-e7-work --out /srv/.../doom-e7a2-work [--k 100] [--workers 3] [--only a,b]

Per ordered Phase A pair: the real twin search once; K decoy shuffles (seeds 0..K-1, seed 0 = E7's draw). Outputs under <out>:
  draws_long.csv                      one row per pair and seed (cutoff, twins, decoy hits)
  primary/results/e7/phaseA/          pairs_struct.csv + linuxdoom_twin_presence.npz at the pooled multi-decoy cutoff  (Amendment 2 B.2)
  conservative/results/e7/phaseA/     same at the pooled counts with the full +1 kept                                  (B.3)
Other files e7_analyze.py reads are linked from E7's phase A directory. Nothing here reads a verdict.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, str(HERE))
from structural_fingerprint import twins as TW  # noqa: E402
from structural_fingerprint.lineage import wilson_lower as wl_np  # noqa: E402
from structural_fingerprint.twins import TwinParams  # noqa: E402

ELIGIBLE_LOC = 6


def real_state(query, target, p):
    """Everything the real twin search computes (no decoy), as a TwinSearch with a dummy decoy, plus the arrays the cutoffs need."""
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
    first_pos = {int(k): int(i) for i, k in enumerate(t_keys)}
    exact = np.isin(q_keys, uniq) & (query.loc[qm] >= 2 * p.min_loc)
    exact_t = np.array([first_pos[int(k)] for k in q_keys[exact]], dtype=np.int64)
    s = TW.TwinSearch(query, target, p, qm, tm, d1, i1, t_pass, np.full(len(qm), np.inf), np.zeros(len(qm), bool), exact, exact_t)
    return s, qv, tv, scale


def decoy_hits(s, qv, tv, scale, seed):
    p = s.params
    decoy = TW._decoy(tv, s.target.archetype[s.tm], f"{s.query.repo}\0{s.target.repo}\0{seed}")
    e1, e2, ei = TW._top2(qv, decoy, p.block)
    e1, e2 = e1 / scale, e2 / scale
    _, _, eback = TW._top2(decoy, qv, p.block)
    e_recip = (ei >= 0) & (eback[np.maximum(ei, 0)] == np.arange(len(s.qm)))
    e_pass = e_recip & TW._distinct(e1, e2, p.ratio) & np.isfinite(e1)
    return e1, e_pass


def pooled_cutoff(real, decoys, plus):
    """Largest distance whose monotone q-value (nd_total + plus) / (K * n_t) is <= 0.01.  plus = 1: pooled multi-decoy TDC (B.2);
    plus = K: the full single-decoy +1 kept on the mean count (B.3, conservative)."""
    if len(real) == 0:
        return 0.0
    K = len(decoys)
    ts = np.sort(real)
    n_t = np.arange(1, len(ts) + 1)
    nd = np.sum([np.searchsorted(np.sort(d), ts, side="right") for d in decoys], axis=0)
    est = (nd + plus) / (K * n_t)
    q = np.minimum.accumulate(est[::-1])[::-1]
    ok = np.flatnonzero(q <= 0.01)
    return float(ts[ok[-1]]) if len(ok) else 0.0


def pair_draws(query, target, seeds, params=None):
    p = params or TwinParams(min_loc=ELIGIBLE_LOC)
    s, qv, tv, scale = real_state(query, target, p)
    real = s.d1[s.t_pass]
    ex_idx = np.flatnonzero(s.exact)
    rows, decoys = [], []
    for seed in seeds:
        e1, e_pass = decoy_hits(s, qv, tv, scale, seed)
        thr, est = TW._fdr_threshold(real, e1[e_pass], p.fdr)
        twins = len(np.union1d(np.flatnonzero(s.t_pass & (s.d1 <= thr)), ex_idx))
        rows.append(dict(q=query.repo, t=target.repo, seed=seed, elig_q=len(s.qm), elig_t=len(s.tm), threshold=thr, est_fdr=est, twins=twins,
                         exact=len(ex_idx), candidates=int(s.t_pass.sum()), decoy_distinct=int(e_pass.sum()),
                         decoy_hits=int((e_pass & (e1 <= thr)).sum())))
        decoys.append(e1[e_pass])
    return rows, decoys, real, s


def srow(r):
    st = r.stats
    row = dict(q=r.query, t=r.target, elig_q=int(st["eligible"]), twins=int(st["twins"]), exact=int(st["exact_clones"]), surv=float(st["survival"]),
               name_agreement=("" if st["name_agreement"] is None else float(st["name_agreement"])))
    row["wilson"] = float(wl_np(np.array([row["twins"]]), np.array([max(row["elig_q"], 1)]))[0]) if row["elig_q"] else 0.0
    return row


def one_pair(args):
    query, target, seeds = args
    rows, decoys, real, s = pair_draws(query, target, seeds)
    thr_p = pooled_cutoff(real, decoys, 1.0)
    thr_c = pooled_cutoff(real, decoys, float(len(decoys)))
    thr_12 = pooled_cutoff(real, decoys[:12], 1.0)
    rp, rc, r12 = TW.accept(s, thr_p), TW.accept(s, thr_c), TW.accept(s, thr_12)
    sh = np.array([r["twins"] for r in rows]) / max(rows[0]["elig_q"], 1)
    diag = dict(q=query.repo, t=target.repo, elig_q=rows[0]["elig_q"], candidates=rows[0]["candidates"], thr_primary=thr_p, thr_conservative=thr_c,
                thr_k12=thr_12, twins_primary=len(rp.q_index), twins_conservative=len(rc.q_index), twins_k12=len(r12.q_index),
                c_certified=float(np.mean([r["threshold"] > 0 for r in rows])), share_p10=float(np.percentile(sh, 10)),
                share_p50=float(np.percentile(sh, 50)), share_p90=float(np.percentile(sh, 90)), share_mean=float(sh.mean()), share_seed0=float(sh[0]))
    keep = (rp.q_index.copy(), rp.t_index.copy(), rc.q_index.copy(), rc.t_index.copy())
    return rows, srow(rp), srow(rc), diag, keep


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k", type=int, default=25)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    import e7_run as R
    work, out = Path(a.work), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    progs = R.load_programs()
    names = [p["name"] for p in progs if p["role"] in R.MAP_ROLES]
    if a.only:
        names = [n for n in names if n in a.only.split(",")]
    fps, spec = R.fingerprints(names, work / "results" / "e7" / "phaseA" / "fingerprints")
    tables = {n: fp.functions for n, fp in zip(names, fps)}
    seeds = list(range(a.k))
    pairs = [(i, j) for i in names for j in names if i != j]
    print(f"{len(pairs)} ordered pairs, K={a.k}, spec {spec}", flush=True)
    t0 = time.time()
    long_rows, prim, cons, diag, pres = [], [], [], [], {}
    with ThreadPoolExecutor(a.workers) as ex:
        for n, (i, j, res) in enumerate(((i, j, r) for (i, j), r in zip(pairs, ex.map(one_pair, [(tables[i], tables[j], seeds) for i, j in pairs]))), 1):
            rows, rp, rc, dg, keep = res
            long_rows += rows; prim.append(rp); cons.append(rc); diag.append(dg)
            if "linuxdoom" in (i, j):
                for tag, (qi, ti) in (("primary", keep[:2]), ("conservative", keep[2:])):
                    pres.setdefault(tag, {})[f"{i}|{j}|q"] = qi
                    pres[tag][f"{i}|{j}|t"] = ti
            if n % 100 == 0:
                print(f"{n}/{len(pairs)} pairs, {time.time() - t0:.0f}s", flush=True)
    write_csv(out / "draws_long.csv", long_rows)
    write_csv(out / "pair_diagnostics.csv", diag)
    src = work / "results" / "e7" / "phaseA"
    for tag, srows in (("primary", prim), ("conservative", cons)):
        d = out / tag / "results" / "e7" / "phaseA"
        d.mkdir(parents=True, exist_ok=True)
        write_csv(d / "pairs_struct.csv", srows)
        if "linuxdoom" in names:
            L = tables["linuxdoom"]
            np.savez_compressed(d / "linuxdoom_twin_presence.npz", ref_name=L.name, ref_path=L.path, ref_loc=L.loc, **pres[tag])
        for f in os.listdir(src):
            if f in ("pairs_struct.csv", "linuxdoom_twin_presence.npz") or (d / f).exists():
                continue
            if f.endswith((".nwk", ".md", "phaseA_matrices.npz", "MANIFEST.sha256")):
                continue  # outputs of the analysis; regenerated
            os.symlink(src / f, d / f)
    print("done", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
