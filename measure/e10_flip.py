"""DOOM-E10 follow-up: how stable is the per-pair target-decoy threshold? Same scans, 30 different decoy seeds, linuxdoom -> port, for E7's scans and the normalised scans."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
from structural_fingerprint.fingerprint import build
from structural_fingerprint.reference import load_reference
from structural_fingerprint.scan_io import load_scan
from structural_fingerprint import twins as TW
from structural_fingerprint.twins import TwinParams
ref = load_reference("structure")
def tab(w, n): return build(load_scan(f"/srv/storage_16tb/projects/{w}/scans/704cb35f0/{n}/{n}_galaxy_master.db", ref.signal_columns, name=n), ref, min_loc=3).functions
PORTS = ["chocolate-doom", "crispy-doom", "inter-doom", "prboom-plus", "fastdoom", "woof", "dsda-doom", "srb2", "gzdoom", "odamex", "nginx", "libuv", "quake2"]
rows = []
for w, lab in (("doom-e7-work", "E7"), ("doom-e7n-work", "normalised")):
    L = tab(w, "linuxdoom")
    for t in PORTS:
        T = tab(w, t)
        for seed in range(30):
            r = TW.find_twins(L, T, TwinParams(min_loc=6, seed=seed))
            rows.append(dict(run=lab, port=t, seed=seed, threshold=r.threshold, accepted=len(r.q_index), eligible=r.eligible))
        print(lab, t, flush=True)
pd.DataFrame(rows).to_csv("/srv/storage_16tb/projects/doom-e7n-work/flip_seeds.csv", index=False)
