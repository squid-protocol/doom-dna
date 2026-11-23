"""Seed 0 of the replicated search reproduces sfs find_twins; the pooled cutoff reduces to E7's rule for K = 1; accept at a cutoff matches find_twins."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "measure"))
from structural_fingerprint import twins as TW  # noqa: E402
from structural_fingerprint.fingerprint import FunctionTable  # noqa: E402
from structural_fingerprint.twins import TwinParams, find_twins  # noqa: E402
import e7_draws  # noqa: E402


def _table(repo, n, d, seed):
    rng = np.random.default_rng(seed)
    return FunctionTable(repo=repo, name=np.array([f"f{i}" for i in range(n)]), path=np.array(["a.c"] * n), language=np.array(["c"] * n),
                         loc=rng.integers(3, 60, n), vectors=rng.normal(size=(n, d)).astype(np.float32), archetype=rng.integers(0, 3, n),
                         key=rng.integers(0, 10**9, n).astype(np.uint64))


def _pair():
    q, t = _table("q", 400, 8, 1), _table("t", 420, 8, 2)
    t.vectors[:150] = q.vectors[:150] + np.random.default_rng(3).normal(scale=0.01, size=(150, 8)).astype(np.float32)
    t.loc[:150] = q.loc[:150]
    return q, t


def test_seed0_matches_find_twins():
    q, t = _pair()
    rows, decoys, real, s = e7_draws.pair_draws(q, t, [0, 1, 2])
    ref = find_twins(q, t, TwinParams(min_loc=6))
    assert rows[0]["twins"] == len(ref.q_index) and abs(rows[0]["threshold"] - ref.threshold) < 1e-9 and rows[0]["decoy_hits"] == ref.decoy_hits


def test_pooled_cutoff_k1_equals_e7_rule():
    q, t = _pair()
    rows, decoys, real, s = e7_draws.pair_draws(q, t, [0])
    assert abs(e7_draws.pooled_cutoff(real, decoys, 1.0) - rows[0]["threshold"]) < 1e-12


def test_accept_at_cutoff_matches_find_twins():
    q, t = _pair()
    rows, decoys, real, s = e7_draws.pair_draws(q, t, [0])
    r1 = TW.accept(s, rows[0]["threshold"])
    ref = find_twins(q, t, TwinParams(min_loc=6))
    assert len(r1.q_index) == len(ref.q_index) and set(r1.q_index) == set(ref.q_index) and set(r1.t_index) == set(ref.t_index)


def test_conservative_not_above_primary():
    q, t = _pair()
    rows, decoys, real, s = e7_draws.pair_draws(q, t, list(range(20)))
    assert e7_draws.pooled_cutoff(real, decoys, 20.0) <= e7_draws.pooled_cutoff(real, decoys, 1.0) + 1e-12
