import sys, re, csv, json
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot/demo/harness/mscreen/analysis")
import numpy as np, pandas as pd
from run_e15 import context
from roles import *; from tests import usable, tmax, reach_pheno, l1
from graphs import g1_edges, norm
from pathlib import Path
SCANS = Path("/srv/storage_16tb/projects/doom-e7-work/scans/704cb35f0")
PREFIX = re.compile(r"^(EV_|P_|A_|T_|PIT_|PTR_)")
A, B, GA, GB, fc, fm = context(); fa, fb = fc.set_index("fid"), fm.set_index("fid"); demos = A.demos
phA, phB = phenotype(A), phenotype(B); ia, ib = np.where(usable(phA))[0], np.where(usable(phB))[0]; sa, sb = phA.sub(ia), phB.sub(ib); T = tmax(phA, phB)
D = dist(sa, sb, T); N0 = l1(reach_pheno(A, sa.fids, demos), reach_pheno(B, sb.fids, demos))
na = [fa.loc[f, "name"] for f in sa.fids]; nb = [fb.loc[f, "name"] for f in sb.fids]; ka = [PREFIX.sub("", n) for n in na]
fman = {x["fid"]: x for x in json.load(open("/srv/storage_16tb/projects/doom-e7-work/demo-study/screen/choc_v2/manifest.json"))["functions"]}; gman = {x["fid"]: x for x in json.load(open("/srv/storage_16tb/projects/doom-e7-work/demo-study/screen/md_v2/manifest.json"))["functions"]}
sza = [fman[f]["end_line"] - fman[f]["line"] + 1 for f in sa.fids]; szb = [gman[f]["end_line"] - gman[f]["line"] + 1 for f in sb.fids]
e12 = {}
for x in csv.DictReader(open("/srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot/demo/harness/e14/pilot_pairs.csv")): e12.setdefault(x["ref_name"], {})[x["md_name"]] = x["md_tier"]
# call-graph neighbours (undirected, G1) in each port, by normalised name
def adj(path):
    A_ = {}
    for a, b in g1_edges(path): A_.setdefault(a, set()).add(b); A_.setdefault(b, set()).add(a)
    return A_
adjA = adj(next((SCANS / "chocolate-doom").glob("*master.db"))); adjB = adj(next((SCANS / "managed-doom").glob("*master.db")))
anchors = {}   # name-agree anchors: chocolate normalised name -> managed normalised name
for i in range(len(na)):
    for j in range(len(nb)):
        if ka[i] == nb[j] and len(ka[i]) >= 4: anchors[norm(na[i])] = norm(nb[j])
def nbr_corr(i, j):
    """share of the chocolate function's call-graph neighbours (that are anchored) whose partners are neighbours of the managed function"""
    nA = adjA.get(norm(na[i]), set()); nBset = adjB.get(norm(nb[j]), set()); anc = [anchors[x] for x in nA if x in anchors]
    return (sum(1 for y in anc if y in nBset) / len(anc), len(anc)) if len(anc) >= 2 else (np.nan, len(anc))
Dm = D.copy(); Dm[Dm >= 0.999] = np.inf
bestB = Dm.argmin(1); bestA = Dm.argmin(0); dn = np.array([D[i, j] for i in range(len(na)) for j in range(len(nb)) if ka[i] == nb[j] and len(ka[i]) >= 4]); med, q75 = np.median(dn), np.quantile(dn, 0.75)
rows = []
for i in range(len(na)):
    j = bestB[i]
    if np.isfinite(Dm[i, j]) and bestA[j] == i:
        nm = (ka[i] == nb[j] and len(ka[i]) >= 4); st = nb[j] in e12.get(na[i], {}); nc, nn = nbr_corr(i, j)
        rows.append(dict(c_fn=na[i], c_file=fa.loc[sa.fids[i], "file"], m_fn=nb[j], m_file=fb.loc[sb.fids[j], "file"], d=float(D[i, j]), call_same=bool(N0[i, j] < 1e-9), name_agree=nm, e12=st, c_lines=sza[i], m_lines=szb[j],
                         size_ratio=round(max(sza[i], szb[j]) / max(1, min(sza[i], szb[j])), 1), nbr_agree=nc, n_anchored_nbrs=nn, e12_alt=", ".join(f"{m}({t})" for m, t in list(e12.get(na[i], {}).items())[:2])))
R = pd.DataFrame(rows); R["cat"] = np.select([R.name_agree & R.e12, R.name_agree & ~R.e12, ~R.name_agree & R.e12], ["name + E12", "name only", "E12 only"], "neither (functional twin)")
print(f"usable functions: chocolate {len(na)}, managed {len(nb)}; name-agree partner distance: median {med:.3f}, 75th pct {q75:.3f}")
print(f"mutual-nearest break-pattern pairs: {len(R)} = {len(R)/len(na):.0%} of chocolate usable functions, {len(R)/len(nb):.0%} of managed usable")
for lab, th in (("any distance", 9), (f"close (<= 75th pct of name-agree pairs, {q75:.3f})", q75), (f"very close (<= median {med:.3f})", med)):
    S = R[R.d <= th]; vc = S.cat.value_counts(); print(f"\n[{lab}] {len(S)} pairs: " + "; ".join(f"{k} {v} ({v/len(S):.0%})" for k, v in vc.items()))
tw = R[(R.cat == "neither (functional twin)") & (R.d <= q75)].sort_values("d"); print(f"\nFunctional twins (mutual nearest, close, neither name nor E12): {len(tw)} = {len(tw)/len(na):.0%} of chocolate usable, {len(tw)/len(R):.0%} of mutual-nearest pairs")
print("  identical call profile:", int(tw.call_same.sum()), "of", len(tw), "| size ratio median", float(tw.size_ratio.median()), "vs name-agree pairs", float(R[R.name_agree].size_ratio.median()), "| call-graph neighbour agreement median", round(float(tw.nbr_agree.median(skipna=True)), 2), "(n with enough anchored neighbours:", int(tw.nbr_agree.notna().sum()), ") vs name-agree pairs", round(float(R[R.name_agree].nbr_agree.median(skipna=True)), 2))
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 40)
print(tw[["c_fn", "c_file", "m_fn", "m_file", "d", "call_same", "c_lines", "m_lines", "nbr_agree", "e12_alt"]].to_string(index=False))
R.to_csv("/srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot/results/e15/E15_MUTUAL_NEAREST_PAIRS.csv", index=False)
