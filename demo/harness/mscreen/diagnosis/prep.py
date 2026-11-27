"""E16 data layer: dense symptom vectors for lesions (killed / same / missing per demo, log first tic, class set), usable-function lists (E15 masks, verbatim), the file-blocked development/test split,
and the counterpart map from managed-doom functions to chocolate-doom functions. Reads only stores through the E15 loaders."""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from roles import load_port, phenotype, CLASSES, CLASS_BITS
from tests import usable, reach_pheno, l1
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); S = W / "screen"; PREFIX = re.compile(r"^(EV_|P_|A_|T_|PIT_|PTR_)"); GENERIC = {"add", "remove", "get", "set", "update", "run", "start", "stop", "init", "clear", "reset", "check", "free", "alloc"}
def class_bits(mask):
    m = int(mask) if mask == mask and mask is not None else -1
    if m > 0: return sum(1 << j for j, c in enumerate(CLASSES) if (m & CLASS_BITS[c]))   # RNG-only first rows give an empty class set
    return 1 << CLASSES.index("time")
def symptoms(port):
    """arrays over (lesion, demo): K killed, M missing (crash/hang), T log10(first tic + 1), C class-set bits; unexecuted sites are 'same' (a real bug would show no symptom there)"""
    res = port.res; demos = port.demos; di = {d: i for i, d in enumerate(demos)}; lids = np.array(sorted(res.lesion.unique())); li = {l: i for i, l in enumerate(lids)}; n, nd = len(lids), len(demos)
    K = np.zeros((n, nd), bool); M = np.zeros((n, nd), bool); T = np.zeros((n, nd), np.float32); C = np.zeros((n, nd), np.uint8)
    r = res[res.outcome.isin(["killed", "same", "crash", "hang"])]; ii = r.lesion.map(li).to_numpy(); jj = r.demo.map(di).to_numpy(); out = r.outcome.to_numpy()
    kill = out == "killed"; K[ii[kill], jj[kill]] = True; bad = (out == "crash") | (out == "hang"); M[ii[bad], jj[bad]] = True
    kr = r[kill]; T[ii[kill], jj[kill]] = np.log10(kr.tic.fillna(0).to_numpy() + 1); C[ii[kill], jj[kill]] = [class_bits(m) for m in kr["mask"].to_numpy()]
    meta = res.drop_duplicates("lesion").set_index("lesion").loc[lids][["fid", "file", "fn", "kind"]].reset_index().rename(columns={"lesion": "lid"}); return dict(K=K, M=M, T=T, C=C, meta=meta, demos=demos)
def reach_matrix(port, fids):
    """clean call coverage: functions x demos (entries)"""
    di = {d: i for i, d in enumerate(port.demos)}; fi = {f: i for i, f in enumerate(fids)}; R = np.zeros((len(fids), len(port.demos)))
    for f, d, n in zip(port.reach.fid, port.reach.demo, port.reach.entries):
        if f in fi and d in di: R[fi[f], di[d]] = n
    return R
def functions(man): return pd.DataFrame([dict(fid=f["fid"], name=f["name"], file=f["file"]) for f in json.load(open(man))["functions"]])
def split_files(usable_funcs):
    """whole files to the development or the test half, alternating by the number of usable functions (largest first); fixed and committed before any scoring"""
    cnt = usable_funcs.groupby("file").size().sort_values(ascending=False, kind="stable"); dev, test = [], []; sd = st = 0
    for f, n in cnt.items():
        if sd <= st: dev.append(f); sd += n
        else: test.append(f); st += n
    return sorted(dev), sorted(test)
def load():
    A = load_port("chocolate-doom", S / "choc_phenotypes.sqlite"); phA = phenotype(A); fa = functions(S / "choc_v2/manifest.json").set_index("fid"); ua = phA.fids[usable(phA)]
    return A, phA, fa, ua
