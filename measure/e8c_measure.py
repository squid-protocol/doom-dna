"""DOOM-E8c step 3: score every snapshot pair of the dense grid and of E8's semi-annual grid.

Per pair: structure `shared` under (i) the pooled multi-decoy cutoff, K = 25 (E7 Amendment 2) and (ii) a single shuffle per pair (E8's rule: find_twins with the
per-pair cutoff); names `shared` as the Wilson lower bound of the E7 stoplist name-key match, both directions (no decoy certification). Writes
<work>/results/pairs_dense.csv. Resumable (cache of finished pairs). Reads no estimate; the hinge fit is in e8c_analyze.py."""
import csv, glob, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/measure")
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/measure")
import e7_draws as D, e7_names as N, e8_snap as S
from structural_fingerprint import twins as TW
from structural_fingerprint.fingerprint import FunctionTable, build
from structural_fingerprint.lineage import wilson_lower as wl_np
from structural_fingerprint.reference import load_reference
from structural_fingerprint.scan_io import load_scan

REPO = Path(__file__).resolve().parents[1]
E8M = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/manifest")
E7M = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/manifest")
SNAPS = Path("/srv/storage_16tb/projects/doom-e8c-work/snaps")
OUT = Path("/srv/storage_16tb/projects/doom-e8c-work/results"); OUT.mkdir(parents=True, exist_ok=True)
K = 25
ref = load_reference("structure")
STOP = frozenset(l.strip() for l in open(E7M / "name_stoplist.txt") if l.strip() and not l.startswith("#"))
scope = {}
for r in csv.DictReader(open(E8M / "e8_tasks.csv")):
    scope.setdefault(r["port"], r["scope_key"])
_fp = {}
def table(port, sha, label):
    tag = S.tag(sha, scope.get(port, ""))
    key = (tag, label)
    if key not in _fp:
        db = glob.glob(str(SNAPS / tag / "*_galaxy_master.db"))
        if not db:
            return None
        t = build(load_scan(db[0], ref.signal_columns, name=port), ref, min_loc=3).functions
        _fp[key] = FunctionTable(**{**t.__dict__, "repo": label})
    return _fp[key]

def wil(k, n):
    return float(wl_np(np.array([k]), np.array([max(n, 1)]))[0]) if n else 0.0

def names_found(a, b):
    ka = a.name[a.loc >= 6]; kb = b.name[b.loc >= 6]
    cs = N.key_counts([str(x) for x in kb], N.name_key, STOP)
    used = {}; m = 0
    for nm in ka:
        k = N.name_key(str(nm))
        if k is None or k in STOP:
            continue
        if used.get(k, 0) < cs.get(k, 0):
            m += 1; used[k] = used.get(k, 0) + 1
    return m, len(ka)

def direction(q, t):
    rows, decoys, real, s = D.pair_draws(q, t, list(range(K)))
    thr = D.pooled_cutoff(real, decoys, 1.0)
    tw_p = len(TW.accept(s, thr).q_index); tw_1 = rows[0]["twins"]; el = rows[0]["elig_q"]
    return dict(el=el, tw_pooled=tw_p, tw_single=tw_1, thr_pooled=thr, thr_single=rows[0]["threshold"],
                c_cert=float(np.mean([r["threshold"] > 0 for r in rows])))

def do_pair(g):
    ct = table(g["child"], g["child_sha"], g["child_sha"][:10] + "_c"); pt = table(g["parent"], g["parent_sha"], g["parent_sha"][:10] + "_p")
    if ct is None or pt is None:
        return None
    a, b = direction(ct, pt), direction(pt, ct)
    nm1, n1 = names_found(ct, pt); nm2, n2 = names_found(pt, ct)
    w = lambda x, y, k: (wil(x[k], x["el"]), wil(y[k], y["el"]))
    wp, ws = w(a, b, "tw_pooled"), w(a, b, "tw_single"); wn = (wil(nm1, n1), wil(nm2, n2))
    return dict(child=g["child"], parent=g["parent"], step=g["step"], target_date=g["target_date"], child_sha=g["child_sha"], parent_sha=g["parent_sha"],
                identical_sha=int(g["child_sha"] == g["parent_sha"]), grid=g["grid"], elig_child=a["el"], elig_parent=b["el"],
                surv_c2p_pooled=a["tw_pooled"] / max(a["el"], 1), surv_p2c_pooled=b["tw_pooled"] / max(b["el"], 1),
                surv_c2p_single=a["tw_single"] / max(a["el"], 1), surv_p2c_single=b["tw_single"] / max(b["el"], 1),
                shared_struct_max=max(wp), shared_struct_min=min(wp), shared_struct_max_single=max(ws), shared_struct_min_single=min(ws),
                shared_names_max=max(wn), shared_names_min=min(wn), thr_c2p=a["thr_pooled"], thr_p2c=b["thr_pooled"],
                c_cert_c2p=a["c_cert"], c_cert_p2c=b["c_cert"])

def main():
    grid = [dict(r, grid="dense") for r in csv.DictReader(open(REPO / "manifest" / "e8c_grid.csv"))]
    semi = [dict(r, grid="semi") for r in csv.DictReader(open(E8M / "e8_grid_pairs.csv")) if r["child"] in ("crispy-doom", "dsda-doom", "nugget-doom")]
    jobs = [g for g in grid + semi]
    t0 = time.time(); rows = []
    with ThreadPoolExecutor(3) as ex:
        for n, r in enumerate(ex.map(do_pair, jobs), 1):
            if r:
                rows.append(r)
            if n % 10 == 0:
                print(f"{n}/{len(jobs)} pairs, {time.time() - t0:.0f}s", flush=True)
    with open(OUT / "pairs_dense.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("done", len(rows), "of", len(jobs), "pairs,", round(time.time() - t0), "s", flush=True)

if __name__ == "__main__":
    main()
