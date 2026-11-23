"""Seed 0 of the replicated-shuffle search reproduces sfs find_twins (E7's single-shuffle result) exactly, on synthetic fingerprints."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "measure"))
from structural_fingerprint.twins import TwinParams, find_twins  # noqa: E402
from structural_fingerprint.fingerprint import FunctionTable  # noqa: E402
import e7_draws  # noqa: E402


def _table(repo, n, d, seed):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(n, d))
    return FunctionTable(repo=repo, name=np.array([f"f{i}" for i in range(n)]), path=np.array(["a.c"] * n), language=np.array(["c"] * n), loc=rng.integers(3, 60, n),
                         vectors=v.astype(np.float32), archetype=rng.integers(0, 3, n), key=rng.integers(0, 10**9, n).astype(np.uint64))


def test_seed0_matches_find_twins():
    q, t = _table("q", 400, 8, 1), _table("t", 420, 8, 2)
    t.vectors[:150] = q.vectors[:150] + np.random.default_rng(3).normal(scale=0.01, size=(150, 8))  # plant near twins
    t.loc[:150] = q.loc[:150]
    rows, dec, real = e7_draws.pair_draws(q, t, [0, 1, 2])
    ref = find_twins(q, t, TwinParams(min_loc=6))
    r0 = rows[0]
    assert r0["twins"] == len(ref.q_index) and abs(r0["threshold"] - ref.threshold) < 1e-9 and r0["decoy_hits"] == ref.decoy_hits
    assert rows[1]["seed"] == 1 and set(dec) == {0, 1, 2}
