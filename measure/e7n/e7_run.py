"""DOOM-E7 core run: fingerprints, structure twins, name matching with a chance control (Amendment 1 §D, §E, §G).

    python e7_run.py --phase A [--only a,b,c] [--workers N]     # map programs only (never loads a withheld scan)
    python e7_run.py --phase B [--workers N]                    # withheld + B2 programs vs the frozen map

Outputs go to ``<work>/results/e7/phase<A|B>/`` (long CSVs, one row per ordered pair) and, for phase A, a
SHA-256 manifest to commit before phase B runs. Phase B never recomputes or alters a phase A table.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import sys
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees")
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, str(HERE))

import e7_names as N  # noqa: E402
from structural_fingerprint.fingerprint import Fingerprint, build  # noqa: E402
from structural_fingerprint.lineage import wilson_lower as wl_np  # noqa: E402
from structural_fingerprint.reference import load_reference  # noqa: E402
from structural_fingerprint.scan_io import load_scan  # noqa: E402
from structural_fingerprint.twins import TwinParams, find_twins  # noqa: E402

WORK = Path("/srv/storage_16tb/projects/doom-e7n-work")
ENGINE = "704cb35f0"
MIN_LOC_FP = 3  # fingerprint floor (sfs default); twin/name eligibility is loc >= 6
ELIGIBLE_LOC = 6
DRAWS = 200
MIN_POWER = 100
GENERIC_DF = 10
MAP_ROLES = ("map", "map-negative-unrelated", "map-negative-same-studio")
B_ROLES = ("phase-B1-withheld", "phase-B2-positive")


def load_programs():
    pins = json.load(open(REPO / "manifest" / "RUN_PINS.json"))
    return pins["programs"]


def declared_families(names):
    """F(X) = {X} + declared ancestors + descendants + non-root siblings + cousins (Amendment 1 §C.3, §E)."""
    basis = {(r["name"], r["parent"]): r["basis"] for r in csv.DictReader(open(REPO / "manifest" / "declared_lineage_basis.csv"))}
    parent = {c: p for (c, p), b in basis.items() if b not in ("excluded", "dropped")}
    roots = {p for p in parent.values() if p not in parent}

    def anc(x):
        out = []
        while x in parent:
            x = parent[x]
            out.append(x)
        return out

    fam = {}
    for x in names:
        a = set(anc(x))
        d = {c for c in parent if x in anc(c)}
        sib = {c for c, p in parent.items() if p == parent.get(x) and p not in roots and c != x}
        non_root_anc = a - roots
        cous = {c for c in parent if non_root_anc and (set(anc(c)) - roots) & non_root_anc}
        fam[x] = ({x} | a | d | sib | cous) & set(names)
    return fam


def scan_db(name):
    d = WORK / "scans" / ENGINE / name
    if not (d / "rc.txt").exists() or (d / "rc.txt").read_text().strip() != "0":
        raise SystemExit(f"e7_run: scan of {name} not finished or failed ({d})")
    return d / f"{name}_galaxy_master.db"


def fingerprints(names, outdir):
    ref = load_reference("structure")
    fps = []
    for n in names:
        p = outdir / f"{N_safe(n)}.sfp.json"
        if p.exists():
            fps.append(Fingerprint.load(p))
            continue
        fp = build(load_scan(scan_db(n), ref.signal_columns, name=n), ref, min_loc=MIN_LOC_FP)
        fp.save(outdir)
        fps.append(fp)
    hashes = {fp.spec_hash for fp in fps}
    if len(hashes) != 1:
        raise SystemExit(f"e7_run: mixed spec hashes {hashes}")
    return fps, hashes.pop()


def N_safe(n):
    from structural_fingerprint.fingerprint import safe_name
    return safe_name(n)


def program_keys(table, stoplist):
    """Eligible (loc >= 6) names -> key counters for the three name variants."""
    keep = table.loc >= ELIGIBLE_LOC
    names = [str(x) for x in table.name[keep]]
    return {
        "primary": N.key_counts(names, N.name_key, stoplist),
        "nostop": N.key_counts(names, N.name_key),
        "n2": N.key_counts(names, N.name_key_n2, stoplist),
        "n": int(keep.sum()),
    }


def build_vocab(per_prog):
    vocab = {}
    for d in per_prog.values():
        for k in d["primary"]:
            vocab.setdefault(k, len(vocab))
    return vocab


def dense(counter, vocab):
    v = np.zeros(len(vocab), dtype=np.int32)
    for k, c in counter.items():
        i = vocab.get(k)
        if i is not None:
            v[i] = c
    return v


def stable_seed(q, t):
    return zlib.crc32(f"{q}|{t}".encode()) & 0xFFFFFFFF


def run_names_pair(qn, tn, per, dense_all, total, fam, vocab_n, df_generic, vocab):
    """Names result for ordered pair (Q -> T): matched, decoy test, Wilson bounds, generic share."""
    q, t = per[qn], per[tn]
    nq, nt = q["n"], t["n"]
    cq, ct = q["primary"], t["primary"]
    m = N.matched(cq, ct)
    out = dict(q=qn, t=tn, elig_q=nq, elig_t=nt, matched=m, surv=(min(1.0, m / nq) if nq else 0.0))
    # generic share of matched keys
    gen = sum(min(n, ct[k]) for k, n in cq.items() if k in ct and k in df_generic)
    out["generic_share"] = (gen / m) if m else 0.0
    out["nostop_matched"] = N.matched(q["nostop"], t["nostop"])
    out["n2_matched"] = N.matched(q["n2"], t["n2"])
    # decoy: replace Q's key multiset by same-size draws from the pool outside both declared families
    tot_q = sum(cq.values())
    ge = None
    if m > 0 and tot_q > 0 and ct:
        excl = fam.get(qn, {qn}) | fam.get(tn, {tn}) | {qn, tn}
        pool = total.astype(np.int64).copy()
        for p in excl:
            if p in dense_all:
                pool -= dense_all[p]
        cdf = np.cumsum(pool)
        if cdf[-1] > 0:
            rng = np.random.default_rng(stable_seed(qn, tn))
            u = rng.random((DRAWS, tot_q)) * cdf[-1]
            idx = np.searchsorted(cdf, u, side="right")
            idx = np.minimum(idx, len(cdf) - 1)
            ids_t = np.array([vocab[k] for k in ct], dtype=np.int64)
            cnt_t = np.array([ct[k] for k in ct], dtype=np.int64)
            pos = np.full(len(vocab), -1, dtype=np.int64)
            pos[ids_t] = np.arange(len(ids_t))
            pp = pos[idx]  # (DRAWS, tot_q)
            rows = np.repeat(np.arange(DRAWS), tot_q).reshape(DRAWS, tot_q)
            ok = pp >= 0
            flat = rows[ok] * len(ids_t) + pp[ok]
            hist = np.bincount(flat, minlength=DRAWS * len(ids_t)).reshape(DRAWS, len(ids_t))
            dm = np.minimum(hist, cnt_t[None, :]).sum(axis=1)
            ge = int((dm >= m).sum())
        else:
            ge = 0
    out["decoy_ge"] = -1 if ge is None else ge
    out["certified"] = int(ge is not None and ge <= 1)  # (ge + 1) / (DRAWS + 1) <= 0.01
    k_cert = m if out["certified"] else 0
    out["wilson_raw"] = float(N.wilson_lower(m, nq))
    out["wilson_cert"] = float(N.wilson_lower(k_cert, nq))
    out["underpowered"] = int(min(nq, nt) < MIN_POWER)
    return out


def struct_pair(i, j, tables, params, L):
    r = find_twins(tables[i], tables[j], params)
    s = r.stats
    row = dict(q=tables[i].repo, t=tables[j].repo, elig_q=int(s["eligible"]), twins=int(s["twins"]),
               exact=int(s["exact_clones"]), surv=float(s["survival"]),
               name_agreement=("" if s["name_agreement"] is None else float(s["name_agreement"])))
    row["wilson"] = float(wl_np(np.array([row["twins"]]), np.array([max(row["elig_q"], 1)]))[0]) if row["elig_q"] else 0.0
    return row, r


def write_csv(path, rows):
    cols = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["A", "B"], required=True)
    ap.add_argument("--only")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    progs = load_programs()
    role = {p["name"]: p["role"] for p in progs}
    map_names = [p["name"] for p in progs if p["role"] in MAP_ROLES]
    b_names = [p["name"] for p in progs if p["role"] in B_ROLES]
    out = WORK / "results" / "e7" / (f"phase{a.phase}" if not a.only else "smoke")
    (out / "fingerprints").mkdir(parents=True, exist_ok=True)
    stop = frozenset(l.strip() for l in open(REPO / "manifest" / "name_stoplist.txt") if l.strip() and not l.startswith("#"))
    params = TwinParams(min_loc=ELIGIBLE_LOC)
    t0 = time.time()

    if a.phase == "B" and a.only:
        raise SystemExit("e7_run: --only is for phase A smoke runs")
    if a.phase == "A":
        names = [n for n in map_names if not a.only or n in a.only.split(",")]
        if a.only and set(a.only.split(",")) - set(names):
            raise SystemExit("e7_run: --only names must be phase A programs")
        fps, spec = fingerprints(names, out / "fingerprints")
        tables = [fp.functions for fp in fps]
        per = {n: program_keys(t, stop) for n, t in zip(names, tables)}
        df = collections.Counter(k for d in per.values() for k in d["primary"])
        df_generic = {k for k, c in df.items() if c >= GENERIC_DF}
        json.dump(sorted(df_generic), open(out / "generic_keys.json", "w"))
        pairs_idx = [(i, j) for i in range(len(names)) for j in range(len(names)) if i != j]
        left_names, right_names = names, names
    else:
        a_dir = WORK / "results" / "e7" / "phaseA"
        if not (a_dir / "MANIFEST.sha256").exists():
            raise SystemExit("e7_run: phase A manifest missing; phase B must not run before it is committed")
        names_a = [n for n in map_names if (a_dir / "fingerprints" / f"{N_safe(n)}.sfp.json").exists()]
        fps_a, spec = fingerprints(names_a, a_dir / "fingerprints")
        fps_b, spec_b = fingerprints(b_names, out / "fingerprints")
        assert spec == spec_b
        names = names_a + b_names
        tables = [fp.functions for fp in fps_a + fps_b]
        per = {n: program_keys(t, stop) for n, t in zip(names, tables)}
        df_generic = set(json.load(open(a_dir / "generic_keys.json")))  # defined on the map only
        ia = range(len(names_a))
        ib = range(len(names_a), len(names))
        pairs_idx = [(i, j) for i in ib for j in ia] + [(j, i) for i in ib for j in ia]
        left_names, right_names = names, names

    vocab = build_vocab(per)
    dense_all = {n: dense(per[n]["primary"], vocab) for n in names}
    total = np.sum(list(dense_all.values()), axis=0) if dense_all else np.zeros(0)
    fam = declared_families(names)
    print(f"phase {a.phase}: {len(names)} programs, {len(pairs_idx)} ordered pairs, spec {spec}, "
          f"eligible total {sum(p['n'] for p in per.values())}", flush=True)

    def work_pair(ij):
        i, j = ij
        srow, r = struct_pair(i, j, tables, params, "linuxdoom")
        nrow = run_names_pair(names[i], names[j], per, dense_all, total, fam, len(vocab), df_generic, vocab)
        keep = None
        if "linuxdoom" in (names[i], names[j]):
            keep = (names[i], names[j], r.q_index.copy(), r.t_index.copy())
        return srow, nrow, keep

    srows, nrows, presence = [], [], {}
    done = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for srow, nrow, keep in ex.map(work_pair, pairs_idx):
            srows.append(srow)
            nrows.append(nrow)
            if keep:
                presence[f"{keep[0]}|{keep[1]}|q"] = keep[2]
                presence[f"{keep[0]}|{keep[1]}|t"] = keep[3]
            done += 1
            if done % 200 == 0 or done == len(pairs_idx):
                print(f"  {done}/{len(pairs_idx)} pairs, {time.time() - t0:.0f}s", flush=True)
    write_csv(out / "pairs_struct.csv", srows)
    write_csv(out / "pairs_names.csv", nrows)
    if "linuxdoom" in names:
        L = tables[names.index("linuxdoom")]
        np.savez_compressed(out / "linuxdoom_twin_presence.npz", ref_name=L.name, ref_path=L.path, ref_loc=L.loc, **presence)
    write_csv(out / "programs.csv", [dict(name=n, role=role[n], eligible=per[n]["n"], rows_fp=len(t))
                                      for n, t in zip(names, tables)])
    meta = dict(phase=a.phase, engine=ENGINE, spec_hash=spec, draws=DRAWS, min_loc=ELIGIBLE_LOC, params="ratio 0.8, fdr 0.01",
                programs=names, seconds=round(time.time() - t0))
    json.dump(meta, open(out / "run_meta.json", "w"), indent=1)
    if a.phase == "A" and not a.only:
        files = sorted(p for p in out.glob("*") if p.is_file() and p.name != "MANIFEST.sha256")
        files += sorted((out / "fingerprints").glob("*"))
        code = [HERE / "e7_run.py", HERE / "e7_names.py", REPO / "manifest" / "RUN_PINS.json",
                REPO / "manifest" / "name_stoplist.txt", REPO / "manifest" / "declared_lineage_basis.csv"]
        with open(out / "MANIFEST.sha256", "w") as f:
            for p in files + code:
                f.write(f"{sha(p)}  {p.name if p.parent == out else p.relative_to(out) if str(p).startswith(str(out)) else p}\n")
    print("done", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
