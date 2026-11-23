"""DOOM-E10 DEVELOPMENT sweep (exploratory; uses the E9 spike-ins, which were already seen). Compares sfs lens and keyword-mode configurations
on: recall of disguised copies by tier, false positives on hard negatives (nginx, leveldb), and recall of real documented transfers (E9 truth).
The configuration chosen here is frozen before the held-out suite is built."""
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd

sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner-worktrees/robust-lens/src")
from structural_fingerprint.fingerprint import build  # noqa: E402
from structural_fingerprint.reference import load_reference  # noqa: E402
from structural_fingerprint.scan_io import load_scan  # noqa: E402
from structural_fingerprint.twins import TwinParams, find_twins  # noqa: E402

E9 = "/srv/storage_16tb/projects/doom-e7-work/e9/results/"
SC = "/srv/storage_16tb/projects/doom-e7-work/scans/704cb35f0/"
SPK = E9 + "spike/snaps/"
CONFIGS = [("robust", "density"), ("robust", "smoothed_density")]
NEG = ["nginx", "leveldb"]
P = TwinParams(min_loc=6)


def scan_db(prog):
    import glob
    if prog.startswith("chocolate-spike"):
        import json
        pins = pd.read_csv(E9 + "spike/spike_programs.csv")
        sha = pins[pins.program == prog].commit.iloc[0]
        # snaps are tagged sha12__scopehash; the spike programs were scanned with the scratch repo commit
        for d in glob.glob(SPK + f"{sha[:12]}__*"):
            return glob.glob(d + "/*_galaxy_master.db")[0]
        raise FileNotFoundError(prog)
    return f"{SC}{prog}/{prog}_galaxy_master.db"


def fp(prog, lens, mode):
    ref = load_reference(lens)
    return build(load_scan(scan_db(prog), ref.signal_columns, name=prog), ref, min_loc=3, keyword_mode=mode).functions


def union_pairs(a, b):
    ab = find_twins(a, b, P)
    ba = find_twins(b, a, P)
    s = {(int(i), int(j)) for i, j in zip(ab.q_index, ab.t_index)}
    s |= {(int(j), int(i)) for i, j in zip(ba.q_index, ba.t_index)}
    return s


def main():
    st = pd.read_csv(E9 + "spike/spike_truth.csv", dtype=str)
    st = st[(st.eligible == "1") & (st.kept == "1") & st.recipient_engine_row.notna() & (st.recipient_engine_row != "")]
    fn = pd.read_csv(E9 + "truth/functions.csv", dtype=str, usecols=["program", "func_id", "engine_row", "loc"])
    row = {(p, i): int(float(r)) for p, i, r in zip(fn.program, fn.func_id, fn.engine_row) if r not in ("", "nan") and not pd.isna(r)}
    pairs = pd.read_csv(E9 + "truth/pairs.csv", dtype=str)
    p2p = pairs[(pairs.pair_class == "port-to-port") & (pairs.eligible_primary == "1") & (pairs.jaccard.astype(float) >= 0.9)]
    ports = pd.read_csv("/srv/storage_16tb/projects/doom-dna-worktrees/e9-horizontal/manifest/e9_programs.csv")
    cfam = [n for n, l, r in zip(ports.name, ports.language_group, ports.role) if l == "c_family" and r == "map" and n not in NEG]
    out = []
    for lens, mode in CONFIGS:
        t0 = time.time()
        tabs = {}
        need = ["curl", "libuv"] + NEG + cfam + sorted(st.recipient_program.unique())
        def f(p):
            try:
                return p, fp(p, lens, mode)
            except Exception as e:
                return p, None
        with ThreadPoolExecutor(6) as ex:
            for p, t in ex.map(f, need):
                tabs[p] = t
        res = dict(lens=lens, mode=mode)
        # (1) disguised-copy recall by tier (donor <-> spiked recipient, either direction)
        for (donor, tier, size), x in st.groupby(["donor", "tier", "module_size"]):
            rp = f"chocolate-spike-{donor}-{tier}"
            if tabs.get(rp) is None or tabs.get(donor) is None:
                continue
            S = union_pairs(tabs[donor], tabs[rp])
            hits = 0
            for did, rrow in zip(x.donor_func_id, x.recipient_engine_row):
                d = row.get((donor, did))
                hits += (d is not None and (d, int(float(rrow))) in S)
            res[f"{size}:{tier}"] = hits / len(x)
        # (2) false positives on hard negatives per 1,000 eligible functions
        fp_funcs, elig = 0, 0
        for n in NEG:
            if tabs.get(n) is None:
                continue
            flagged = set()
            for pn in cfam:
                if tabs.get(pn) is None:
                    continue
                flagged |= {i for i, _ in union_pairs(tabs[n], tabs[pn])}
            fp_funcs += len(flagged)
            elig += int((tabs[n].loc >= 6).sum())
        res["fp_per_1000_hard"] = 1000 * fp_funcs / max(elig, 1)
        # (3) recall of real documented transfers (E9 port-to-port T1 pairs) by recipient
        rec = {}
        for (a, b), g in p2p.groupby(["prog_a", "prog_b"]):
            if tabs.get(a) is None or tabs.get(b) is None:
                continue
            S = union_pairs(tabs[a], tabs[b])
            h = n = 0
            for fa, fb in zip(g.func_a, g.func_b):
                ra, rb = row.get((a, fa)), row.get((b, fb))
                if ra is None or rb is None:
                    continue
                n += 1
                h += (ra, rb) in S
            rec[(a, b)] = (h, n)
        H = sum(h for h, n in rec.values()); N = sum(n for h, n in rec.values())
        res["real_transfer_recall"] = H / max(N, 1)
        res["real_n"] = N
        res["seconds"] = round(time.time() - t0)
        out.append(res)
        print(res, flush=True)
    pd.DataFrame(out).to_csv("/srv/storage_16tb/projects/doom-e7-work/e10_dev_sweep_v3.csv", index=False)


if __name__ == "__main__":
    main()
