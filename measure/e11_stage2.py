"""DOOM-E11 stage 2 metrics (networkx + scikit-learn venv). Registered design: preregistration/E11_SUBSYSTEMS_STAGE2.md.
Reads <work>/graphs/*.npz (directed calls) and <work>/placement/*.npz (one-to-one twin pairs). Writes results/e11/stage2_*.csv and E11_STAGE2_RESULTS.md."""
import csv, json, itertools, collections, sys, time
from pathlib import Path
import numpy as np, networkx as nx
from networkx.algorithms import community as C
from sklearn.metrics import adjusted_mutual_info_score as AMI, homogeneity_completeness_v_measure as HCV
REPO = Path(__file__).resolve().parents[1]; WORK = Path("/srv/storage_16tb/projects/doom-e11-work"); OUT = REPO / "results" / "e11"; OUT.mkdir(parents=True, exist_ok=True)
TAX = json.load(open("/srv/storage_16tb/projects/structural-fingerprint-scanner/examples/doom/subsystems.json"))["basename_prefix"]
PRIMARY = ["chocolate-doom", "crispy-doom", "doomgeneric", "sdl-doom", "doom-ascii", "doom-wasm"]
SECONDARY = ["fastdoom", "inter-doom", "doom-ios", "prboom-plus", "dsda-doom", "woof", "srb2", "mood", "puredoom", "mochadoom", "eternity", "odamex"]
GAMMAS = (0.5, 1.0, 2.0); NSEED = 30; NCONS = 100; NPERM = 1000; NBOOT = 1000; NCOPY = 200; MAXN_CONS = 3500
rng = np.random.default_rng(20261123)

def load(n):
    d = np.load(WORK / "graphs" / f"{n}.npz", allow_pickle=False); E = d["edges"]
    DE = {(int(a), int(b)) for a, b in E if a != b}; G = nx.Graph(); G.add_edges_from(DE)
    return dict(G=G, DE=DE, path=d["path"], nfunc=len(d["loc"]))

def lab_array(G, gamma, seed, weight=None):
    nodes = sorted(G.nodes()); idx = {v: i for i, v in enumerate(nodes)}; lab = np.zeros(len(nodes), int)
    for k, c in enumerate(C.louvain_communities(G, resolution=gamma, seed=seed, weight=weight)):
        for v in c: lab[idx[v]] = k
    return nodes, lab

def consensus(G, gamma, nrun=NCONS, tau=0.5, maxit=8):
    """Iterative consensus (Lancichinetti and Fortunato 2012). Returns nodes, labels (-1 = unstable), the first NSEED raw partitions."""
    nodes, _ = lab_array(G, gamma, 0); n = len(nodes)
    parts = [lab_array(G, gamma, s)[1] for s in range(nrun)]; raw = parts[:NSEED]
    if n > MAXN_CONS:  # too large for a dense co-association matrix: best modularity of the raw partitions
        qs = [C.modularity(G, [set(np.array(nodes)[p == k]) for k in np.unique(p)], resolution=1.0) for p in raw]
        return nodes, raw[int(np.argmax(qs))], raw, "best-of-30"
    for _ in range(maxit):
        D = np.zeros((n, n), np.float32)
        for p in parts: D += (p[:, None] == p[None, :])
        D /= len(parts); D[D < tau] = 0; np.fill_diagonal(D, 0)
        r, c = np.nonzero(np.triu(D))
        if len(r) == 0: break
        H = nx.Graph(); H.add_nodes_from(range(n)); H.add_weighted_edges_from(zip(r.tolist(), c.tolist(), D[r, c].tolist()))
        new = []
        for s in range(nrun):
            lab = np.zeros(n, int)
            for k, cm in enumerate(C.louvain_communities(H, weight="weight", seed=s)):
                for v in cm: lab[v] = k
            new.append(lab)
        same = all(AMI(new[0], q) > 0.999 for q in new[1:5]); parts = new
        if same: break
    final = parts[0].copy(); unstable = np.asarray((D > 0).sum(1) == 0); final[unstable] = -1
    return nodes, final, raw, "consensus"

def hand(path):
    b = str(path).split("/")[-1].lower()
    for pfx, sub in TAX:
        if b.startswith(pfx): return sub
    return "other"

def file_majority(files, lab):
    fm = {}
    for f in set(files):
        ls = [l for ff, l in zip(files, lab) if ff == f]; fm[f] = collections.Counter(ls).most_common(1)[0][0]
    return fm

def strat_shuffle(lab, deg, k=5):
    q = np.unique(np.quantile(deg, np.linspace(0, 1, k + 1)[1:-1])); bins = np.digitize(deg, q); out = lab.copy()
    for b in np.unique(bins):
        i = np.where(bins == b)[0]; out[i] = lab[rng.permutation(i)]
    return out

def cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b); return float(a @ b / (na * nb)) if na > 0 and nb > 0 else float("nan")

def xmatrix(edges, labs, groups):
    gi = {g: i for i, g in enumerate(groups)}; M = np.zeros((len(groups), len(groups)))
    for a, b in edges:
        if labs[a] != labs[b]: M[gi[labs[a]], gi[labs[b]]] += 1
    return M

def offdiag(M): return M[~np.eye(len(M), dtype=bool)]

def qmod(G, labs):
    nodes = list(G.nodes()); parts = collections.defaultdict(set)
    for v in nodes: parts[labs[v]].add(v)
    return C.modularity(G, list(parts.values())) if G.number_of_edges() else float("nan")

REF = {}; PORT_CACHE = {}
def reference(gamma):
    if gamma not in REF:
        L = load("linuxdoom"); nodes, lab, _, how = consensus(L["G"], gamma); REF[gamma] = dict(L=L, labs={v: int(l) for v, l in zip(nodes, lab) if l >= 0}, n_unstable=int((lab < 0).sum()), n_nodes=len(nodes), how=how)
    return REF[gamma]

def evaluate(prog, gamma, pl, P, full):
    R = reference(gamma); L = R["L"]; refl = R["labs"]; pairs = [(int(l), int(p)) for l, p in zip(pl["pairs_l"], pl["pairs_p"]) if int(l) in refl and int(p) in P["G"]]
    l2p = dict(pairs); p2l = {p: l for l, p in pairs}; placed = sorted(p2l)
    Eport = [(a, b) for a, b in P["DE"] if a in p2l and b in p2l]
    row = dict(program=prog, gamma=gamma, ref_nodes=R["n_nodes"], ref_unstable=R["n_unstable"], placed=len(placed), coverage=len(placed) / max(len(refl), 1), port_calls_among_placed=len(Eport))
    if len(placed) < 100 or len(Eport) < 300:
        row["status"] = "insufficient"; return row
    row["status"] = "scored"; imp = {p: refl[p2l[p]] for p in placed}
    # E1 edge retention and gained edges
    Lm = [(a, b) for a, b in L["DE"] if a in l2p and b in l2p]; ret = [(l2p[a], l2p[b]) in P["DE"] for a, b in Lm]
    row["E1_retention"] = float(np.mean(ret)) if ret else float("nan"); row["E1_n_ref_edges"] = len(Lm)
    gained = [(a, b) for a, b in Eport if (p2l[a], p2l[b]) not in L["DE"]]; row["gained_edges"] = len(gained)
    if len(gained) >= 30:
        fid = np.array([imp[a] == imp[b] for a, b in gained], float); row["E1g_real"] = float(fid.mean())
        bs = [fid[rng.integers(0, len(fid), len(fid))].mean() for _ in range(NBOOT)]; row["E1g_lo"], row["E1g_hi"] = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
        deg = np.array([P["G"].degree(p) for p in placed]); lab0 = np.array([imp[p] for p in placed]); ix = {p: i for i, p in enumerate(placed)}; nul = []
        for _ in range(300):
            s = strat_shuffle(lab0, deg); nul.append(np.mean([s[ix[a]] == s[ix[b]] for a, b in gained]))
        row["E1g_null_mean"], row["E1g_null95"] = float(np.mean(nul)), float(np.percentile(nul, 95))
    # M2 against the port's own (full-graph) consensus partition, restricted to placed functions
    cn, cl, raw, how = PORT_CACHE[(prog, gamma)]; cix = {v: i for i, v in enumerate(cn)}; keep = [p for p in placed if cl[cix[p]] >= 0]
    row["port_partition"] = how; row["M2_n"] = len(keep)
    if len(keep) >= 50:
        pc = [int(cl[cix[p]]) for p in keep]; li = [imp[p] for p in keep]
        row["M2_AMI"] = float(AMI(li, pc)); h, c, _ = HCV(li, pc); row["M2_homog"], row["M2_compl"] = float(h), float(c)
        row["M2_ceiling"] = float(np.median([AMI([int(r_[cix[p]]) for p in keep], pc) for r_ in raw]))
        row["M2_perm95"] = float(np.percentile([AMI(rng.permutation(li), pc) for _ in range(NPERM)], 95))
        lfiles = [str(L["path"][p2l[p]]) for p in keep]; fm = file_majority([str(L["path"][l]) for l in refl], [refl[l] for l in refl]); files = sorted(fm); fg = np.array([fm[f] for f in files]); fnull = []
        for _ in range(NPERM):
            pg = dict(zip(files, rng.permutation(fg))); fnull.append(AMI([pg[f] for f in lfiles], pc))
        row["M2_filepermute99"] = float(np.percentile(fnull, 99))
        row["M2_AMI_filelabel"] = float(AMI(lfiles, pc)); row["M2_AMI_hand"] = float(AMI([hand(str(L["path"][p2l[p]])) for p in keep], pc))
    # M1 (descriptive) as a fraction of the pure-copy expectation
    Gi = P["G"].subgraph(placed); row["M1_Q"] = float(qmod(Gi, imp)) if Gi.number_of_edges() else float("nan")
    LG = nx.Graph(); LG.add_nodes_from(l2p); LG.add_edges_from(Lm); copyq, copycos = [], []; labsL = {l: refl[l] for l in l2p}; groups = sorted(set(labsL.values())); nodesL = list(l2p)
    Mref = offdiag(xmatrix(Lm, labsL, groups)); rate = row["E1_retention"] if np.isfinite(row["E1_retention"]) else 1.0; target = Gi.number_of_edges()
    for _ in range(NCOPY if len(nodesL) < 1500 else 60):
        H = nx.Graph(); H.add_nodes_from(nodesL); H.add_edges_from([e for e in LG.edges() if rng.random() < rate])
        while H.number_of_edges() < target:
            a, b = rng.integers(0, len(nodesL), 2)
            if a != b: H.add_edge(nodesL[a], nodesL[b])
        copyq.append(qmod(H, labsL)); copycos.append(cosine(offdiag(xmatrix(list(H.edges()), labsL, groups)), Mref))
    row["M1_copyexp"] = float(np.mean(copyq)); row["M1_ratio"] = row["M1_Q"] / row["M1_copyexp"] if row["M1_copyexp"] else float("nan")
    # M3 (descriptive; own floor of 100 directed cross-group calls)
    Mp = xmatrix([(p2l[a], p2l[b]) for a, b in Eport], refl, groups); row["M3_cross_calls"] = int(Mp.sum())
    if Mp.sum() >= 100:
        Mp_ = offdiag(Mp); row["M3_cos"] = cosine(Mp_, Mref); row["M3_copyexp"] = float(np.nanmean(copycos))
        deg = np.array([P["G"].degree(p) for p in placed]); lab0 = np.array([imp[p] for p in placed]); ix = {p: i for i, p in enumerate(placed)}; nul = []
        for _ in range(300):
            s = strat_shuffle(lab0, deg); nul.append(cosine(offdiag(xmatrix([(ix[a], ix[b]) for a, b in Eport], s, groups)), Mref))
        row["M3_null_mean"] = float(np.nanmean(nul)); row["M3_gap"] = row["M3_cos"] - row["M3_null_mean"]
    return row

def main():
    place = {p.stem: np.load(p) for p in (WORK / "placement").glob("*.npz")}
    summ = {r["program"]: r for r in csv.DictReader(open(WORK / "placement" / "placement_summary.csv"))}
    rows, t0 = [], time.time()
    scored_set = PRIMARY + SECONDARY
    progs = sorted(place, key=lambda n: (n not in PRIMARY, n not in SECONDARY, n))
    for n in progs:
        P = load(n); gams = GAMMAS if n in PRIMARY else (1.0,)
        for g in gams:
            R = reference(g); placed = [(int(l), int(p)) for l, p in zip(place[n]["pairs_l"], place[n]["pairs_p"]) if int(l) in R["labs"] and int(p) in P["G"]]
            enough = len(placed) >= 100
            if enough and (n, g) not in PORT_CACHE: PORT_CACHE[(n, g)] = consensus(P["G"], g)
            r = evaluate(n, g, place[n], P, None) if (enough or True) else None
            r["group"] = "primary" if n in PRIMARY else "secondary" if n in SECONDARY else "control/other"; r["eligible_port"] = summ[n]["eligible_port"]; r["ambiguous_ref"] = summ[n]["ambiguous_ref"]; r["ambiguous_port"] = summ[n]["ambiguous_port"]
            rows.append(r); print(n, g, r["status"], r["placed"], f"{time.time() - t0:.0f}s", flush=True)
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("program", "gamma", "group", "status"), k))
    with open(OUT / "stage2_table.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    # pure-copy curve (power at the floors): random samples of linuxdoom's own graph
    R = reference(1.0); L = R["L"]; refl = R["labs"]; nodes = sorted(refl); curve = []
    for fr in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
        qs, ne = [], []
        for _ in range(30):
            s = [v for v in nodes if rng.random() < fr]; Hs = L["G"].subgraph(s); ne.append(Hs.number_of_edges()); qs.append(qmod(Hs, refl))
        curve.append((fr, int(np.mean(ne)), float(np.nanmean(qs))))
    json.dump(curve, open(OUT / "stage2_copy_curve.json", "w"))
    report(rows, curve)

def report(rows, curve):
    g1 = {r["program"]: r for r in rows if r["gamma"] == 1.0}; f = lambda x, d=2: ("%.*f" % (d, x)) if isinstance(x, float) and np.isfinite(x) else "n/a"
    T = ["# DOOM-E11 stage 2 results: how much of `linuxdoom`'s subsystem architecture do ports keep?", "", "Registered design: [stage 2](../../preregistration/E11_SUBSYSTEMS_STAGE2.md). Placement by one-to-one structural twins (E7 Amendment 2 pooled K = 25). Reference: iterative consensus Louvain. Full table: `stage2_table.csv`.", "",
         "## Primary ports (resolution 1.0)", "", "| port | placed (coverage) | edge retention | gained-edge fidelity real [95% CI] vs null 95th | AMI imported vs own groups (ceiling) | label-perm 95th / file-perm 99th | AMI file-label / hand taxonomy | M1 Q (fraction of pure copy) | M3 cos (copy exp), gap |", "|---|---|---|---|---|---|---|---|---|"]
    for n in PRIMARY:
        r = g1[n]
        if r["status"] != "scored": T.append(f"| {n} | {r['placed']} | insufficient | | | | | | |"); continue
        T.append(f"| {n} | {r['placed']} ({f(r['coverage'])}) | {f(r.get('E1_retention'))} | {f(r.get('E1g_real'))} [{f(r.get('E1g_lo'))}, {f(r.get('E1g_hi'))}] vs {f(r.get('E1g_null95'))} | {f(r.get('M2_AMI'))} ({f(r.get('M2_ceiling'))}) | {f(r.get('M2_perm95'))} / {f(r.get('M2_filepermute99'))} | {f(r.get('M2_AMI_filelabel'))} / {f(r.get('M2_AMI_hand'))} | {f(r.get('M1_Q'))} ({f(r.get('M1_ratio'))}) | {f(r.get('M3_cos'))} ({f(r.get('M3_copyexp'))}), {f(r.get('M3_gap'))} |")
    T += ["", "## Secondary and other programs (resolution 1.0)", "", "| program | group | eligible | placed | calls among placed | status | edge retention | AMI imported vs own (file-perm 99th) |", "|---|---|---|---|---|---|---|---|"]
    for r in sorted(g1.values(), key=lambda r: (r["group"], -r["placed"])):
        if r["program"] in PRIMARY: continue
        T.append(f"| {r['program']} | {r['group']} | {r['eligible_port']} | {r['placed']} | {r['port_calls_among_placed']} | {r['status']} | {f(r.get('E1_retention'))} | {f(r.get('M2_AMI'))} ({f(r.get('M2_filepermute99'))}) |")
    T += ["", "## Pure-copy curve (random samples of linuxdoom's own graph)", "", "| placed fraction | edges among placed | modularity of the reference labels |", "|---|---|---|"] + [f"| {a} | {b} | {f(c, 3)} |" for a, b, c in curve]
    P6 = [r["program"] for r in g1.values() if r["group"] == "control/other" and r["status"] == "scored"]
    pr = {r["program"]: [rr for rr in rows if rr["program"] == r["program"]] for r in rows}
    ok = lambda r: r["status"] == "scored" and "M2_AMI" in r
    p1 = sum(1 for n in PRIMARY if g1[n]["status"] == "scored" and g1[n].get("E1_retention", 0) >= 0.5)
    p2a = sum(1 for n in PRIMARY if ok(g1[n]) and g1[n]["M2_AMI"] > g1[n]["M2_perm95"]); p2b = sum(1 for n in PRIMARY if ok(g1[n]) and g1[n]["M2_AMI"] > g1[n]["M2_filepermute99"])
    p3 = sum(1 for n in PRIMARY if g1[n].get("M1_ratio", 0) >= 0.8); p4 = sum(1 for n in PRIMARY if "E1g_real" in g1[n] and g1[n]["E1g_real"] > g1[n]["E1g_null95"])
    p5 = sum(1 for n in PRIMARY if ok(g1[n]) and abs(g1[n]["M2_AMI"] - g1[n]["M2_AMI_filelabel"]) <= 0.05)
    p7 = sum(1 for n in PRIMARY if all(ok(r) and r["M2_AMI"] > r["M2_perm95"] and r["M2_AMI"] > r["M2_filepermute99"] for r in pr[n] if r["status"] == "scored") and sum(1 for r in pr[n] if r["status"] == "scored") == 3)
    from scipy.stats import spearmanr
    e7 = {(r["q"], r["t"]): r for r in csv.DictReader(open("/srv/storage_16tb/projects/doom-e7a2-work/pair_diagnostics.csv"))}; xs, ys = [], []
    for r in g1.values():
        d = e7.get(("linuxdoom", r["program"]))
        if d: xs.append(r["coverage"]); ys.append(float(d["twins_primary"]) / float(d["elig_q"]))
    rho = spearmanr(xs, ys).statistic
    T += ["", "## Predictions", "", "| prediction | result | value |", "|---|---|---|",
          f"| P1 edge retention at least 0.50 for each primary port | {'met' if p1 == 6 else 'NOT met'} | {p1} of 6 |", f"| P2 AMI above label-permutation 95th for all six, above file-level 99th for at least five | {'met' if p2a == 6 and p2b >= 5 else 'NOT met'} | {p2a} of 6; {p2b} of 6 |",
          f"| P3 M1 at least 0.8 of pure-copy expectation for at least four | {'met' if p3 >= 4 else 'NOT met'} | {p3} of 6 |", f"| P4 gained-edge fidelity above matched null for at least four | {'met' if p4 >= 4 else 'NOT met'} | {p4} of 6 |",
          f"| P5 file-label AMI within 0.05 of subsystem AMI for at least three | {'true (groups add little beyond files)' if p5 >= 3 else 'not true'} | {p5} of 6 |", f"| P6 no unrelated or from-scratch program is scored | {'met' if not P6 else 'NOT met'} | {P6 or 'none scored'} |",
          f"| P7 P2 holds at all three resolutions for at least five | {'met' if p7 >= 5 else 'NOT met'} | {p7} of 6 |", f"| P8 coverage ranks as E7 Amendment 2 pooled shares (Spearman at least 0.8) | {'met' if rho >= 0.8 else 'NOT met'} | rho {f(float(rho))} (n {len(xs)}) |"]
    (OUT / "E11_STAGE2_RESULTS.md").write_text("\n".join(T) + "\n"); print("\n".join(T))

if __name__ == "__main__":
    main()
