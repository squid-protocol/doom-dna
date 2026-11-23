"""DOOM-E11 stage 2, step 1: place every Phase A program's functions onto linuxdoom by structural twins (E7 Amendment 2 pooled K=25 cutoff, both directions),
strictly one-to-one on both sides; ambiguous matches dropped and counted. Run with the sfs venv. Writes <work>/placement/<program>.npz and placement_summary.csv."""
import csv, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/measure")
import e7_draws as D, e7_run as R
from structural_fingerprint import twins as TW
from concurrent.futures import ThreadPoolExecutor
OUT = Path("/srv/storage_16tb/projects/doom-e11-work/placement"); OUT.mkdir(parents=True, exist_ok=True)
W = Path("/srv/storage_16tb/projects/doom-e7-work"); K = 25
progs = R.load_programs(); names = [p["name"] for p in progs if p["role"] in R.MAP_ROLES]
fps, _ = R.fingerprints(names, W / "results" / "e7" / "phaseA" / "fingerprints"); T = {n: f.functions for n, f in zip(names, fps)}
L = T["linuxdoom"]

def twins(q, t):
    rows, decoys, real, s = D.pair_draws(q, t, list(range(K)))
    r = TW.accept(s, D.pooled_cutoff(real, decoys, 1.0)); return list(zip(map(int, r.q_index), map(int, r.t_index))), rows[0]["elig_q"]

def one(n):
    P = T[n]
    a, el_l = twins(L, P)            # (l, p)
    b, el_p = twins(P, L)            # (p, l)
    pairs = set(a) | {(l, p) for p, l in b}
    by_l, by_p = {}, {}
    for l, p in pairs:
        by_l.setdefault(l, set()).add(p); by_p.setdefault(p, set()).add(l)
    keep = [(l, p) for l, p in pairs if len(by_l[l]) == 1 and len(by_p[p]) == 1]
    amb_l = sum(1 for v in by_l.values() if len(v) > 1); amb_p = sum(1 for v in by_p.values() if len(v) > 1)
    arr = np.array(sorted(keep), dtype=np.int64).reshape(-1, 2)
    np.savez_compressed(OUT / f"{n}.npz", pairs_l=arr[:, 0], pairs_p=arr[:, 1])
    return dict(program=n, eligible_ref=el_l, eligible_port=el_p, union_pairs=len(pairs), placed=len(keep), ambiguous_ref=amb_l, ambiguous_port=amb_p)

todo = [n for n in names if n != "linuxdoom"]
rows = []
with ThreadPoolExecutor(3) as ex:
    for r in ex.map(one, todo):
        rows.append(r); print(r["program"], r["placed"], flush=True)
with open(OUT / "placement_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("done", len(rows))
