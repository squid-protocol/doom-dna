"""DOOM-E11 stage 1, step 1: export each program's call graph from the E7 phase A fingerprints (run with the sfs venv)."""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
from structural_fingerprint.fingerprint import Fingerprint
SRC = Path("/srv/storage_16tb/projects/doom-e7-work/results/e7/phaseA/fingerprints"); OUT = Path("/srv/storage_16tb/projects/doom-e11-work/graphs"); OUT.mkdir(parents=True, exist_ok=True)
import json
PROGS = [p["name"] for p in json.load(open("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/manifest/RUN_PINS.json"))["programs"] if p["role"] in ("map", "map-negative-unrelated", "map-negative-same-studio")]  # all Phase A programs (stage 1 used a subset)
for n in PROGS:
    f = Fingerprint.load(next(SRC.glob(f"{n}.sfp.json")) if (SRC / f"{n}.sfp.json").exists() else next(SRC.glob(f"*{n}*.sfp.json")))
    t = f.functions
    if t.edges is None:
        print(n, "no edges", flush=True); continue
    np.savez_compressed(OUT / f"{n}.npz", edges=np.asarray(t.edges, dtype=np.int32), path=np.asarray(t.path).astype(str), name=np.asarray(t.name).astype(str), loc=np.asarray(t.loc))
    print(n, len(t.loc), len(t.edges), flush=True)
