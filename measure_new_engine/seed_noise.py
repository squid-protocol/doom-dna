"""Replication helper (NEW code): how much does E7's single-shuffle structure result move when only the decoy draw changes?

    python seed_noise.py ORIG_draws_long.csv NEW_draws_long.csv

Per run: for each decoy seed s (0 = E7's own draw), (a) number of programs detectable at the 2% floor (symmetrised Wilson lower bound
of twins / elig_q, as e7_analyze does) and (b) number of ordered pairs whose share differs from seed 0's by at least 0.03.
Then the same for the engine change: seed-0 original vs seed-0 new.
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
from structural_fingerprint.lineage import wilson_lower as wl  # noqa: E402


def load(p):
    d = pd.read_csv(p)
    d["share"] = d.twins / d.elig_q.clip(lower=1)
    d["w"] = wl(d.twins.to_numpy(), d.elig_q.clip(lower=1).to_numpy())
    return d


def detectable(d, s):
    x = d[d.seed == s]
    names = sorted(set(x.q) | set(x.t))
    ix = {n: i for i, n in enumerate(names)}
    m = np.zeros((len(names), len(names)))
    for q, t, w in zip(x.q, x.t, x.w):
        m[ix[q], ix[t]] = w
    m = np.maximum(m, m.T)
    return {n for n in names if m[ix[n]].max() >= 0.02}


o, n = load(sys.argv[1]), load(sys.argv[2])
for lab, d in (("original engine", o), ("new engine", n)):
    seeds = sorted(d.seed.unique())
    det = [len(detectable(d, s)) for s in seeds]
    base = d[d.seed == 0].set_index(["q", "t"]).share
    moved = [int(((d[d.seed == s].set_index(["q", "t"]).share - base).abs() >= 0.03).sum()) for s in seeds[1:]]
    print(f"{lab}: detectable programs at 2% across {len(seeds)} single decoy draws: min {min(det)}, median {int(np.median(det))}, max {max(det)}; seed 0 = {det[0]}")
    print(f"{lab}: ordered pairs whose share differs from seed 0 by >= 0.03 when only the draw changes: mean {np.mean(moved):.1f}, range {min(moved)} to {max(moved)}")
b0o, b0n = o[o.seed == 0].set_index(["q", "t"]).share, n[n.seed == 0].set_index(["q", "t"]).share
print(f"engine change, seed 0 vs seed 0: pairs with |change| >= 0.03: {int(((b0n - b0o).abs() >= 0.03).sum())}")
dd = sorted(detectable(o, 0) ^ detectable(n, 0))
print("programs crossing the floor at seed 0:", dd)
# how often does each crossing program cross when only the seed changes (original engine)?
for p in dd:
    inn = [p in detectable(o, s) for s in sorted(o.seed.unique())]
    print(f"  {p}: detectable in {sum(inn)} of {len(inn)} decoy draws on the original engine")
