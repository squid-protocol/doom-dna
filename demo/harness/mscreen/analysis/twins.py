import sys, re, csv
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot/demo/harness/mscreen/analysis")
import numpy as np, pandas as pd
from run_e15 import context
from roles import *; from tests import usable, tmax, reach_pheno, l1
PREFIX = re.compile(r"^(EV_|P_|A_|T_|PIT_|PTR_)")
A, B, GA, GB, fc, fm = context(); fa, fb = fc.set_index("fid"), fm.set_index("fid"); demos = A.demos
phA, phB = phenotype(A), phenotype(B); ia, ib = np.where(usable(phA))[0], np.where(usable(phB))[0]; sa, sb = phA.sub(ia), phB.sub(ib); T = tmax(phA, phB)
D = dist(sa, sb, T); N0 = l1(reach_pheno(A, sa.fids, demos), reach_pheno(B, sb.fids, demos))
na = [fa.loc[f, "name"] for f in sa.fids]; nb = [fb.loc[f, "name"] for f in sb.fids]; filea = [fa.loc[f, "file"] for f in sa.fids]; fileb = [fb.loc[f, "file"] for f in sb.fids]
ka = [PREFIX.sub("", n) for n in na]
e12 = {}
for x in csv.DictReader(open("/srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot/demo/harness/e14/pilot_pairs.csv")): e12.setdefault(x["ref_name"], []).append((x["md_name"], x["md_tier"]))
namepair = {(i, j) for i in range(len(na)) for j in range(len(nb)) if ka[i] == nb[j] and len(ka[i]) >= 4}
dn = np.array([D[i, j] for i, j in namepair]); q = np.quantile(dn, 0.75); print(f"usable functions {len(na)} (C) / {len(nb)} (C#); name-agree pairs {len(namepair)}; break-pattern distance of name-agree pairs: median {np.median(dn):.3f}, 75th pct {q:.3f}")
# 1) functional twins: identical call profile, similar break pattern, different names, not matched by E12
tw = []
for i in range(len(na)):
    cand = [j for j in range(len(nb)) if N0[i, j] < 1e-9 and ka[i] != nb[j]]
    if not cand or len(cand) > 4: continue
    for j in cand:
        if D[i, j] <= q:
            e = e12.get(na[i], []); tw.append((na[i], filea[i], nb[j], fileb[j], round(float(D[i, j]), 3), len(cand), "yes: " + ", ".join(f"{m} ({t})" for m, t in e[:2]) if e else "no E12 match", any(m == nb[j] for m, t in e)))
print(f"\n== functional twins (identical call profile in all 77 demos, break pattern as close as a true partner, names differ): {len(tw)} candidate pairs")
tw.sort(key=lambda r: r[4])
print(f"   of which E12 also matched them: {sum(1 for r in tw if r[7])}; not matched by E12: {sum(1 for r in tw if not r[7])}")
for r in tw[:30]: print(f"   {r[0]:28s} ({r[1]:9s}) ~ {r[2]:24s} ({r[3]:16s}) dist {r[4]:.3f} cands {r[5]}  E12: {r[6]}{'  [matched]' if r[7] else ''}")
# 2) name AND structure agree (E12 pair with equal names) but role (profile or break pattern) differs
print("\n== matched by name and by E12 structure, but roles differ (profile rank > 5 or break-pattern distance above the 75th percentile of true partners)")
bad = []
for i in range(len(na)):
    for m, t in e12.get(na[i], []):
        if m in nb and ka[i] == m:
            j = nb.index(m); rk = int((N0[i] <= N0[i, j]).sum()); rkd = int((D[i] <= D[i, j]).sum())
            if rk > 5 or D[i, j] > q: bad.append((na[i], m, t, round(float(N0[i, j]), 3), rk, round(float(D[i, j]), 3), rkd))
print(f"   {len(bad)} pairs")
for r in sorted(bad, key=lambda r: -r[5]): print(f"   {r[0]:28s} ~ {r[1]:22s} tier {r[2]:6s} call-profile dist {r[3]:.3f} (rank {r[4]}), break-pattern dist {r[5]:.3f} (rank {r[6]})")
