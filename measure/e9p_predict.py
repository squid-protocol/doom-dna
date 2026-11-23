#!/usr/bin/env python
"""DOOM-E9p: run E9's predictor unchanged except that the twin search uses the pooled multi-decoy cutoff (K = 25, E7 Amendment 2).
Usage identical to e9_predict.py (e.g. `run --pairs eligible --out <dir>`). Only `find_twins` without an explicit threshold is replaced."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/measure")
import e7_draws as D  # noqa: E402
import e9_predict as P  # noqa: E402
from structural_fingerprint import twins as TW  # noqa: E402

K = 25
_orig = P.find_twins

def find_twins_pooled(query, target, params=None, threshold=None):
    if threshold is not None:
        return _orig(query, target, params, threshold)
    p = params or TW.TwinParams(min_loc=D.ELIGIBLE_LOC)
    rows, decoys, real, s = D.pair_draws(query, target, list(range(K)), p)
    return TW.accept(s, D.pooled_cutoff(real, decoys, 1.0))

P.find_twins = find_twins_pooled

if __name__ == "__main__":
    P.main()
