"""Synthetic screens with planted role groups: validates the analysis pipeline without touching any real screen database.
planted=True: 12 groups; port B keeps roles except `swap` of functions; planted=False: no group structure (null). Usage: python synth.py <planted|null> [swap=0.2]"""
import sys, sqlite3, tempfile, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from roles import *; from graphs import Graph, norm; from pipeline import *
def make_port(name, rng, groups, cent, hot_ids, inert_ids, fids, file_of, idio, nd=42, demos=None):
    demos = demos or [f"{'s' if i < 20 else ('c' if i < 30 else 'b')}{i:04d}" for i in range(nd)]
    les, res, reach, sr = [], [], [], []; lid = 0
    for f in fids:
        nl = int(rng.integers(10, 25)); fam = rng.random(nd) < rng.uniform(0.4, 0.95)
        for d, ok in zip(demos, fam):
            if ok: reach.append((d, f, int(rng.integers(5, 5000)), int(rng.integers(0, 200))))
        for _ in range(nl):
            les.append((lid, file_of[f], f"fn{f}", f, 10, "relational", "<", "<=")); lid += 1
            for j, (d, ok) in enumerate(zip(demos, fam)):
                if not ok or rng.random() > 0.85: continue
                p = 0.97 if f in hot_ids else (0.0 if f in inert_ids else float(np.clip(cent[groups[f]][j] + idio[f][j], 0, 1)))
                killed = rng.random() < p; g = groups[f]
                mask = int(sum(1 << c for c in ([4, 5] if g % 3 == 0 else ([15, 16] if g % 3 == 1 else [17])))) | 4
                res.append((lid - 1, d, "killed" if killed else "same", int(np.exp(rng.normal(3 + 0.2 * (g % 5), 0.5))) if killed else None, mask if killed else None, 0, 1, f, file_of[f], f"fn{f}", "relational"))
                sr.append((d, lid - 1, 1))
    L = pd.DataFrame(les, columns=["id", "file", "fn", "fid", "line", "kind", "op", "new"]); R = pd.DataFrame(res, columns=["lesion", "demo", "outcome", "tic", "mask", "rc", "tries", "fid", "file", "fn", "kind"])
    RC = pd.DataFrame(reach, columns=["demo", "fid", "entries", "first_tic"]); return Port(name, L, R, RC, demos)
def build(planted=True, swap=0.2, n=150, k=12, seed=11):
    rng = np.random.default_rng(seed); fids = list(range(n)); hot = set(fids[:8]); inert = set(fids[8:28]); real = fids[28:]
    cent = rng.beta(0.4, 0.5, size=(k, 42)) if planted else np.tile(rng.beta(0.4, 0.5, size=(1, 42)), (k, 1)); idio = {f: rng.normal(0, 0.2, 42) for f in fids}
    gA = {f: int(rng.integers(0, k)) for f in fids}; gB = {f: (int(rng.integers(0, k)) if rng.random() < swap else gA[f]) for f in fids}
    if not planted: gA = {f: int(rng.integers(0, k)) for f in fids}; gB = gA
    file_of = {f: f"file{(gA[f] // 2) if rng.random() < 0.5 else int(rng.integers(0, 8))}" for f in fids}
    A = make_port("A", rng, gA, cent, hot, inert, fids, file_of, idio); B = make_port("B", rng, gB, cent, hot, inert, fids, file_of, idio)
    names = {f: (f"P_func{f}" if True else "") for f in fids}; fa = pd.DataFrame(dict(fid=fids, name=[f"P_func{f}x" for f in fids], file=[file_of[f] for f in fids])); fb = pd.DataFrame(dict(fid=fids, name=[f"func{f}x" for f in fids], file=[file_of[f] for f in fids]))
    def edges(groups):
        e = set()
        for a in fids:
            for b in fids:
                if a < b and rng.random() < (0.45 if groups[a] == groups[b] else 0.008): e.add((norm(f"P_func{a}x"), norm(f"P_func{b}x"))); e.add((norm(f"func{a}x"), norm(f"func{b}x")))
        return e
    E = edges(gA if planted else {f: 0 for f in fids}); GA = Graph(fids, fa.name, E); GB = Graph(fids, fb.name, E)
    return A, B, GA, GB, fa, fb
def run(planted=True, swap=0.2, n=150, k=12, seed=11, B_perm=2000):
    A, B, GA, GB, fa, fb = build(planted, swap, n, k, seed)
    return analyze(A, B, GA, GB, fa, fb, B_perm=B_perm)
if __name__ == "__main__":
    planted = sys.argv[1] == "planted"; swap = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2
    out = run(planted, swap)
    print("eligible usable:", out["n_eligible"], "hot:", out["hot"], "inert:", out["inert"], "name-agree pairs:", out["pairs"])
    for p, o, r in verdicts(out): print(f"- {p}: {o} -> {r}")
