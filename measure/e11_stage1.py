"""DOOM-E11 stage 1: are call-graph communities stable and meaningful? (venv with networkx)  Writes results/e11/ and scores the gate in E11_STAGE1_RESULTS.md."""
import json, sys, collections, itertools
from pathlib import Path
import numpy as np, networkx as nx
from networkx.algorithms import community as C
REPO = Path(__file__).resolve().parents[1]; G_DIR = Path("/srv/storage_16tb/projects/doom-e11-work/graphs"); OUT = REPO / "results" / "e11"; OUT.mkdir(parents=True, exist_ok=True)
TAX = json.load(open("/srv/storage_16tb/projects/structural-fingerprint-scanner/examples/doom/subsystems.json"))["basename_prefix"]
PORTS = ["chocolate-doom", "crispy-doom", "doomgeneric", "prboom-plus", "woof", "eternity", "odamex", "mochadoom", "gore", "puredoom"]
CTRL = ["nginx", "curl", "lua", "helion", "rust-doom"]
NSEED, NNULL, NPERM = 30, 20, 1000
rng = np.random.default_rng(20261123)

def ari(a, b):
    a = np.unique(a, return_inverse=True)[1]; b = np.unique(b, return_inverse=True)[1]
    ct = np.zeros((a.max() + 1, b.max() + 1)); np.add.at(ct, (a, b), 1)
    c2 = lambda x: x * (x - 1) / 2
    s = c2(ct).sum(); A = c2(ct.sum(1)).sum(); B = c2(ct.sum(0)).sum(); N = c2(len(a)); e = A * B / N
    return float((s - e) / ((A + B) / 2 - e)) if (A + B) / 2 != e else 1.0

def nmi(a, b):
    a = np.unique(a, return_inverse=True)[1]; b = np.unique(b, return_inverse=True)[1]
    ct = np.zeros((a.max() + 1, b.max() + 1)); np.add.at(ct, (a, b), 1); n = ct.sum(); p = ct / n
    pa, pb = p.sum(1), p.sum(0); nz = p > 0
    mi = (p[nz] * np.log(p[nz] / np.outer(pa, pb)[nz])).sum(); ha = -(pa[pa > 0] * np.log(pa[pa > 0])).sum(); hb = -(pb[pb > 0] * np.log(pb[pb > 0])).sum()
    return float(mi / ((ha + hb) / 2)) if ha + hb > 0 else 1.0

def load(n):
    d = np.load(G_DIR / f"{n}.npz", allow_pickle=False); E = d["edges"]
    G = nx.Graph(); G.add_edges_from((int(a), int(b)) for a, b in E if a != b)
    return G, d["path"], d["name"], len(d["loc"])

def louvain(G, gamma, seed):
    comms = C.louvain_communities(G, resolution=gamma, seed=seed); nodes = sorted(G.nodes()); idx = {v: i for i, v in enumerate(nodes)}
    lab = np.zeros(len(nodes), int)
    for k, c in enumerate(comms):
        for v in c: lab[idx[v]] = k
    return lab, comms, nodes

def hand(path):
    b = str(path).split("/")[-1].lower()
    for pfx, sub in TAX:
        if b.startswith(pfx): return sub
    return "other"

def topdir(path):
    p = str(path).strip("/").split("/"); return "/".join(p[:2]) if len(p) > 2 else (p[0] if len(p) > 1 else "")

def perm_null(truth, lab, fn):
    return np.array([fn(rng.permutation(truth), lab) for _ in range(NPERM)])

def analyse(name, gammas=(1.0,), extra=False):
    G, path, fname, nfunc = load(name); iso = nfunc - G.number_of_nodes(); res = []
    for gamma in gammas:
        labs, Qs = [], []
        for s in range(NSEED):
            lab, comms, nodes = louvain(G, gamma, s); labs.append(lab); Qs.append(C.modularity(G, comms, resolution=1.0))
        pair = [ari(a, b) for a, b in itertools.combinations(labs, 2)]
        sizes = collections.Counter(labs[0]); big = [v for v in sizes.values() if v >= 10]
        r = dict(program=name, gamma=gamma, functions=nfunc, clustered=G.number_of_nodes(), isolated=iso, groups=len(sizes), groups_ge10=len(big),
                 share_in_ge10=sum(big) / G.number_of_nodes(), largest=max(sizes.values()) / G.number_of_nodes(), stab_ari_median=float(np.median(pair)), stab_ari_min=float(np.min(pair)), modularity=float(np.mean(Qs)))
        if gamma == 1.0:
            nq = []
            for _ in range(NNULL):
                H = G.copy(); nx.double_edge_swap(H, nswap=5 * H.number_of_edges(), max_tries=100 * H.number_of_edges(), seed=int(rng.integers(1 << 30)))
                comms = C.louvain_communities(H, seed=0); nq.append(C.modularity(H, comms))
            r["modularity_null_mean"] = float(np.mean(nq)); r["modularity_z"] = float((np.mean(Qs) - np.mean(nq)) / max(np.std(nq), 1e-9))
            nodes = sorted(G.nodes()); P = [path[v] for v in nodes]
            truths = {"file": np.array(P)}
            td = np.array([topdir(x) for x in P])
            if len(set(td)) > 1 and "" not in set(td) or name != "linuxdoom" and len(set(td)) > 1: truths["dir"] = td
            if name == "linuxdoom": truths["hand_prefix"] = np.array([hand(x) for x in P])
            for k, tv in truths.items():
                nm = float(np.median([nmi(tv, l) for l in labs])); ar = float(np.median([ari(tv, l) for l in labs]))
                nn = perm_null(tv, labs[0], nmi); p = float((nn >= nm).mean())
                r.update({f"nmi_{k}": nm, f"ari_{k}": ar, f"nmi_{k}_null95": float(np.percentile(nn, 95)), f"nmi_{k}_p": p})
        res.append(r)
    return res

rows = []
for n in ["linuxdoom"] + PORTS + CTRL:
    rows += analyse(n, gammas=(0.5, 1.0, 2.0) if n in ("linuxdoom", "chocolate-doom") else (1.0,)); print(n, "done", flush=True)
import csv
allk = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("program", "gamma"), k))
with open(OUT / "stage1_table.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=allk); w.writeheader(); w.writerows(rows)
L = {r["program"]: r for r in rows if r["gamma"] == 1.0}; ld = L["linuxdoom"]
gate = {"(i) linuxdoom stability ARI median >= 0.70": ld["stab_ari_median"] >= 0.70, "(ii) >= 70% of functions in groups of >= 10": ld["share_in_ge10"] >= 0.70,
        "(iii) modularity z vs degree-preserving null >= 5": ld["modularity_z"] >= 5,
        "(iv) agreement with hand taxonomy: NMI above null (p<0.01) and ARI >= 0.30": ld.get("nmi_hand_prefix_p", 1) < 0.01 and ld.get("ari_hand_prefix", 0) >= 0.30,
        "(v) >= 8 of 10 ports with stability ARI median >= 0.60": sum(L[p]["stab_ari_median"] >= 0.60 for p in PORTS) >= 8}
fmt = lambda x, d=2: ("%.*f" % (d, x)) if isinstance(x, float) else str(x)
T = ["# DOOM-E11 stage 1 results: do call graphs yield stable, meaningful subsystems?", "", "Method and gate as in [the stage 1 note](../../preregistration/E11_SUBSYSTEMS_STAGE1.md). Louvain, 30 seeds, 20 degree-preserving nulls, 1,000 label permutations. Full table: `stage1_table.csv`.", "",
     "## Gate", "", "| criterion | value | pass |", "|---|---|---|"]
vals = {0: fmt(ld["stab_ari_median"]), 1: fmt(ld["share_in_ge10"]), 2: fmt(ld["modularity_z"], 1), 3: f"NMI {fmt(ld.get('nmi_hand_prefix', float('nan')))} (null95 {fmt(ld.get('nmi_hand_prefix_null95', float('nan')))}), ARI {fmt(ld.get('ari_hand_prefix', float('nan')))}", 4: f"{sum(L[p]['stab_ari_median'] >= 0.60 for p in PORTS)} of 10"}
for i, (k, v) in enumerate(gate.items()): T.append(f"| {k} | {vals[i]} | {'yes' if v else '**NO**'} |")
T += ["", f"**Gate: {'PASSED' if all(gate.values()) else 'NOT PASSED'}.**", "", "## Per program (resolution 1.0)", "", "| program | funcs (clustered) | groups | groups >= 10 | share in them | largest group | stability ARI median / min | modularity (null) z | NMI file (null95) | NMI dir | ARI hand |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for n in ["linuxdoom"] + PORTS + CTRL:
    r = L[n]; T.append(f"| {n} | {r['functions']} ({r['clustered']}) | {r['groups']} | {r['groups_ge10']} | {fmt(r['share_in_ge10'])} | {fmt(r['largest'])} | {fmt(r['stab_ari_median'])} / {fmt(r['stab_ari_min'])} | {fmt(r['modularity'], 3)} ({fmt(r['modularity_null_mean'], 3)}) z {fmt(r['modularity_z'], 0)} | {fmt(r.get('nmi_file', float('nan')))} ({fmt(r.get('nmi_file_null95', float('nan')))}) | {fmt(r.get('nmi_dir', float('nan')))} | {fmt(r.get('ari_hand_prefix', float('nan')))} |")
T += ["", "## Resolution sweep (is about 16 groups natural?)", "", "| program | resolution | groups | groups >= 10 | share in them | stability ARI median |", "|---|---|---|---|---|---|"]
for r in rows:
    if r["program"] in ("linuxdoom", "chocolate-doom"): T.append(f"| {r['program']} | {r['gamma']} | {r['groups']} | {r['groups_ge10']} | {fmt(r['share_in_ge10'])} | {fmt(r['stab_ari_median'])} |")
ctl = [L[p]["stab_ari_median"] for p in CTRL]; prt = [L[p]["stab_ari_median"] for p in PORTS]
sw = [r for r in rows if r["program"] == "linuxdoom"]
P = [("P1 linuxdoom stability ARI median in 0.50 to 0.80", 0.50 <= ld["stab_ari_median"] <= 0.80, fmt(ld["stab_ari_median"])),
     ("P2 modularity z above 5 for every program", all(r["modularity_z"] > 5 for r in L.values()), "min z " + fmt(min(r["modularity_z"] for r in L.values()), 1)),
     ("P3 at least 70% of linuxdoom's clustered functions in groups of 10+", ld["share_in_ge10"] >= 0.70, fmt(ld["share_in_ge10"])),
     ("P4 NMI above null for file and hand taxonomy, ARI hand below 0.30", ld.get("nmi_file_p", 1) < 0.05 and ld.get("nmi_hand_prefix_p", 1) < 0.05 and ld.get("ari_hand_prefix", 1) < 0.30, f"p_file {fmt(ld.get('nmi_file_p', float('nan')), 3)}, p_hand {fmt(ld.get('nmi_hand_prefix_p', float('nan')), 3)}, ARI hand {fmt(ld.get('ari_hand_prefix', float('nan')))}"),
     ("P5 controls as stable as ports (median stability within 0.10)", abs(np.median(ctl) - np.median(prt)) <= 0.10, f"controls {fmt(float(np.median(ctl)))}, ports {fmt(float(np.median(prt)))}"),
     ("P6 no resolution gives a stable (ARI >= 0.7) partition with 14 to 18 groups of 10+ (linuxdoom)", not any(r["stab_ari_median"] >= 0.7 and 14 <= r["groups_ge10"] <= 18 for r in sw), "; ".join(f"g={r['gamma']}: {r['groups_ge10']} groups, ARI {fmt(r['stab_ari_median'])}" for r in sw)),
     ("P7 gate not passed on (i) or (iv)", (not gate["(i) linuxdoom stability ARI median >= 0.70"]) or (not gate["(iv) agreement with hand taxonomy: NMI above null (p<0.01) and ARI >= 0.30"]), "")]
T += ["", "## Predictions", "", "| prediction | result | value |", "|---|---|---|"] + [f"| {a} | {'met' if ok else 'NOT met'} | {v} |" for a, ok, v in P]
(OUT / "E11_STAGE1_RESULTS.md").write_text("\n".join(T) + "\n"); print("\n".join(T))
