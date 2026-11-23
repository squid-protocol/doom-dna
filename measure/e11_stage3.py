"""DOOM-E11 stage 3 (registered design: preregistration/E11_SUBSYSTEMS_STAGE3.md). Arm F placement (geometry-only descriptors, no call edge read), calibration on linuxdoom
by cross-validation, reference-swap specificity of excess homogeneity, file control. Venv with networkx + scikit-learn; sfs on the path.
Writes results/e11/stage3_*.csv and E11_STAGE3_RESULTS.md."""
import csv, glob, json, collections, sys, time
from pathlib import Path
import numpy as np, networkx as nx
from networkx.algorithms import community as C
from sklearn.metrics import cohen_kappa_score
from sklearn.cluster import KMeans
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src"); sys.path.insert(0, str(Path(__file__).resolve().parent))
from structural_fingerprint.fingerprint import Fingerprint
from structural_fingerprint import blind as B
import e11_stage2 as S2
REPO = Path(__file__).resolve().parents[1]; OUT = REPO / "results" / "e11"; OUT.mkdir(parents=True, exist_ok=True)
FPDIRS = "/srv/storage_16tb/projects/doom-e7-work/results/e7/phase[AB]/fingerprints"
GROUPS = {"C": ["chocolate-doom", "crispy-doom", "doomgeneric", "sdl-doom", "doom-ascii", "doom-wasm"],
          "M": ["mood", "prboom-plus", "woof", "dsda-doom", "inter-doom", "fastdoom", "doom-ios", "eternity", "odamex", "srb2", "puredoom", "nugget-doom", "doomretro", "gzdoom", "doomsday", "edge-classic", "doom3do", "doom3-bfg"],
          "T": ["gore", "doom-scheme", "dartdoom", "managed-doom", "mochadoom", "kocoa-doom", "doomf77", "doo-cr"],
          "R": ["helion", "rust-doom", "room4doom", "cssdoom", "fsharp-doom", "doom-fx", "sqldoom"],
          "K": ["agentic-cobol-doom-cc", "agentic-cobol-doom-codex", "fps-cob", "c-raycasting", "c-raycasting2", "goom3d"],
          "U": ["nginx", "curl", "lua", "leveldb", "libuv", "bubbletea", "macroquad", "carddemo-cobol-ctrl"], "X": ["quake", "quake2", "freedoom"]}
GROUP_OF = {p: g for g, ps in GROUPS.items() for p in ps}; ORDINAL = {"C": 3, "M": 2, "T": 1, "R": 0, "U": 0, "K": 0}
ALT_REF_PROGS = ["nginx", "curl", "lua", "leveldb", "libuv", "bubbletea", "macroquad"]
K_NN, ABST_PCT, NPERM, NSEEDS, NBOOT = 15, 95, 50, 5, 200
GAM = (0.5, 1.0, 2.0); rng = np.random.default_rng(20261123)
_FP = {}
def fp(name):
    if name not in _FP:
        p = glob.glob(f"{FPDIRS}/{name}.sfp.json")
        _FP[name] = Fingerprint.load(Path(p[0])).functions if p else None
    return _FP[name]
_VIEW = {}
def view(name):
    if name not in _VIEW:
        t = fp(name); v = B.blind_view(t); d = B.descriptors(v, 1, use_graph=False, use_measures=True, geometry_only=True)
        G = nx.Graph(); G.add_edges_from((int(a), int(b)) for a, b in v.edges)  # view indices
        _VIEW[name] = dict(t=t, v=v, desc=d, G=G, paths=np.asarray(t.path)[v.rows].astype(str))
    return _VIEW[name]

def sqd(a, b): return (a ** 2).sum(1)[:, None] + (b ** 2).sum(1)[None, :] - 2 * a @ b.T
def abstain_threshold(xr):
    d = sqd(xr, xr); np.fill_diagonal(d, np.inf); return float(np.percentile(d.min(1), ABST_PCT))
def place(xq, xr, yr, thr, decision="lift"):
    d = sqd(xq, xr); k = min(K_NN, len(xr)); nn = np.argpartition(d, k - 1, axis=1)[:, :k]; s = int(yr.max()) + 1
    votes = np.eye(s)[yr][nn].sum(1) / k; prior = np.bincount(yr, minlength=s) / len(yr)
    score = votes / np.where(prior > 0, prior, np.inf) if decision == "lift" else votes
    lab = score.argmax(1); lab[d.min(1) > thr] = -1; return lab
def hom(lab, comm):
    _, lab = np.unique(lab, return_inverse=True); _, comm = np.unique(comm, return_inverse=True); K, Cn = lab.max() + 1, comm.max() + 1
    ct = np.bincount(comm * K + lab, minlength=Cn * K).reshape(Cn, K).astype(float); n = ct.sum(); pl = ct.sum(0) / n; Hl = -(pl[pl > 0] * np.log(pl[pl > 0])).sum()
    if Hl == 0: return float("nan")
    p = ct / ct.sum(1, keepdims=True); Hc = -np.where(p > 0, p * np.log(np.where(p > 0, p, 1)), 0).sum(1); return float(1 - (ct.sum(1) / n * Hc).sum() / Hl)
def excess(lab, comm, nperm=NPERM):
    h = hom(lab, comm); null = np.mean([hom(rng.permutation(lab), comm) for _ in range(nperm)]); return h - null, h, null

# ---------------------------------------------------------------- reference partitions
_OREF = {}
def other_reference(name):
    if name not in _OREF:
        V = view(name); t = V["t"]; G = nx.Graph(); G.add_edges_from((int(a), int(b)) for a, b in t.edges if a != b)
        best, bg = None, None
        for g in (0.25, 0.5, 1.0, 2.0, 4.0):
            nodes, lab = S2.lab_array(G, g, 0); sz = np.bincount(lab); n10 = int((sz >= 10).sum())
            if best is None or abs(n10 - 16) < best: best, bg = abs(n10 - 16), g
        nodes, lab, raw, how = S2.consensus(G, bg); row2lab = {v: int(l) for v, l in zip(nodes, lab) if l >= 0}
        idx = [i for i, r in enumerate(V["v"].rows) if int(r) in row2lab]; y = np.array([row2lab[int(V["v"].rows[i])] for i in idx])
        _OREF[name] = dict(idx=np.array(idx), y=y, gamma=bg, how=how, groups=int(len(np.unique(y))), n10=int((np.bincount(y) >= 10).sum()))
    return _OREF[name]
def doom_reference(gamma):
    R = S2.reference(gamma); V = view("linuxdoom"); labs = R["labs"]
    idx = [i for i, r in enumerate(V["v"].rows) if int(r) in labs]; y = np.array([labs[int(V["v"].rows[i])] for i in idx]); return np.array(idx), y, R
def reference_set(gamma):
    """list of (name, kind, xr, yr, threshold). DOOM first; then 20 random partitions with the DOOM size profile, 3 graph-blind 16-means, other programs' partitions."""
    V = view("linuxdoom"); idx, y, _ = doom_reference(gamma); xr = V["desc"][idx]; thr = abstain_threshold(xr); refs = [("DOOM", "doom", xr, y, thr)]
    for r in range(20): refs.append((f"random{r}", "random", xr, rng.permutation(y), thr))
    for s in range(3):
        km = KMeans(n_clusters=16, n_init=1, random_state=s).fit(V["desc"][V["desc"].sum(1) >= 0]); refs.append((f"kmeans{s}", "kmeans", V["desc"], km.labels_, abstain_threshold(V["desc"])))
    for o in ALT_REF_PROGS:
        if fp(o) is None: continue
        O = other_reference(o); xo = view(o)["desc"][O["idx"]]; refs.append((f"prog:{o}", "program", xo, O["y"], abstain_threshold(xo)))
    return refs

# ---------------------------------------------------------------- calibration on linuxdoom (10-fold)
def calibrate(gamma):
    V = view("linuxdoom"); idx, y, _ = doom_reference(gamma); x = V["desc"][idx]; n = len(idx); folds = np.array_split(rng.permutation(n), 10); out = []
    for dec in ("lift", "argmax"):
        ks, ba, acc, nul = [], [], [], []
        for f in folds:
            tr = np.setdiff1d(np.arange(n), f); thr = abstain_threshold(x[tr]); pred = place(x[f], x[tr], y[tr], thr, dec); ok = pred >= 0
            if ok.sum() < 20: continue
            yt, yp = y[f][ok], pred[ok]; ks.append(cohen_kappa_score(yt, yp)); acc.append(float((yt == yp).mean()))
            cls = [c for c in np.unique(yt) if (yt == c).sum() >= 5]; ba.append(float(np.mean([(yp[yt == c] == c).mean() for c in cls])) if cls else float("nan"))
            nul.append(np.percentile([cohen_kappa_score(rng.permutation(yt), yp) for _ in range(100)], 95))
        out.append(dict(gamma=gamma, decision=dec, kappa_median=float(np.median(ks)), kappa_lo=float(np.percentile(ks, 2.5)), kappa_hi=float(np.percentile(ks, 97.5)), shuffle95=float(np.median(nul)), acc=float(np.mean(acc)), balanced=float(np.nanmean(ba)), coverage=float(np.mean([1 - 0])), folds=len(ks)))
    return out

# ---------------------------------------------------------------- one program
def communities(G, gamma_p, nodes_n):
    out = []
    for s in range(NSEEDS):
        lab = -np.ones(nodes_n, int)
        for k, c in enumerate(C.louvain_communities(G, resolution=gamma_p, seed=s)):
            for v in c: lab[v] = k
        sz = np.bincount(lab[lab >= 0]) if (lab >= 0).any() else np.array([0]); big = np.isin(lab, np.where(sz >= 10)[0]) & (lab >= 0); lab[~big] = -1; out.append(lab)
    return out

def score_program(name, refsets, comm_cache, decisions=("lift", "argmax")):
    V = view(name); n = V["v"].n; rows = []
    if n < 300: return [dict(program=name, group=GROUP_OF.get(name, "?"), functions=n, status="too small (under 300 functions)")]
    for gp in GAM:
        if (name, gp) not in comm_cache: comm_cache[(name, gp)] = communities(V["G"], gp, n)
        comms = comm_cache[(name, gp)]
        if int(np.mean([len(set(c[c >= 0])) for c in comms])) < 10:
            rows.append(dict(program=name, group=GROUP_OF.get(name, "?"), functions=n, gamma_port=gp, status="under 10 communities of 10+ functions")); continue
        for gr, refs in refsets.items():
            for dec in decisions:
                X = {}
                for rname, kind, xr, yr, thr in refs:
                    if rname == f"prog:{name}": continue
                    lab = place(V["desc"], xr, yr, thr, dec); vals = []
                    for c in comms:
                        m = (lab >= 0) & (c >= 0)
                        if m.sum() < 50 or len(np.unique(lab[m])) < 2: continue
                        vals.append(excess(lab[m], c[m])[0])
                    X[rname] = (float(np.mean(vals)) if vals else float("nan"), float((lab >= 0).mean()))
                xd = X["DOOM"][0]; alt = np.array([v[0] for k, v in X.items() if k != "DOOM" and np.isfinite(v[0])])
                if not np.isfinite(xd) or len(alt) < 10: rows.append(dict(program=name, group=GROUP_OF.get(name, "?"), functions=n, gamma_ref=gr, gamma_port=gp, decision=dec, status="insufficient alternatives")); continue
                rows.append(dict(program=name, group=GROUP_OF.get(name, "?"), functions=n, status="scored", gamma_ref=gr, gamma_port=gp, decision=dec, coverage=X["DOOM"][1], X_doom=xd, X_alt_median=float(np.median(alt)), X_alt_p95=float(np.percentile(alt, 95)),
                                 diff=xd - float(np.median(alt)), pct=float((alt <= xd).mean()), specific=int((alt <= xd).mean() >= 0.95), n_alt=len(alt),
                                 X_kmeans=float(np.mean([v[0] for k, v in X.items() if k.startswith("kmeans")])), X_random_mean=float(np.mean([v[0] for k, v in X.items() if k.startswith("random")])),
                                 X_programs=float(np.mean([v[0] for k, v in X.items() if k.startswith("prog:") and np.isfinite(v[0])])) if any(k.startswith("prog:") for k in X) else float("nan")))
        # file control (label = contiguous path blocks, K classes)
    return rows

def file_control(name, gamma_p, comm_cache, K):
    V = view(name); order = np.argsort(V["paths"], kind="stable"); lab = np.zeros(V["v"].n, int); lab[order] = np.minimum(np.arange(V["v"].n) * K // V["v"].n, K - 1); vals = []
    for c in comm_cache[(name, gamma_p)]:
        m = c >= 0
        if m.sum() >= 50: vals.append(excess(lab[m], c[m])[0])
    return float(np.mean(vals)) if vals else float("nan")

def main():
    t0 = time.time(); cal = []
    for g in GAM: cal += calibrate(g)
    print("calibration done", f"{time.time() - t0:.0f}s", flush=True)
    refsets = {g: reference_set(g) for g in GAM}; print("references built", len(refsets[1.0]), f"{time.time() - t0:.0f}s", flush=True)
    names = [p for g in ("C", "M", "T", "R", "K", "U", "X") for p in GROUPS[g]]; names = [n for n in names if fp(n) is not None]
    rows, comm_cache = [], {}
    for n in names:
        rows += score_program(n, refsets, comm_cache); print(n, "done", f"{time.time() - t0:.0f}s", flush=True)
    for r in rows:
        if r.get("status") == "scored" and r["decision"] == "lift" and r["gamma_ref"] == 1.0:
            K = int(len(np.unique(doom_reference(1.0)[1]))); r["X_file"] = file_control(r["program"], r["gamma_port"], comm_cache, K)
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("program", "group", "functions", "status"), k))
    with open(OUT / "stage3_table.csv", "w", newline="") as f: w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    with open(OUT / "stage3_calibration.csv", "w", newline="") as f: w = csv.DictWriter(f, fieldnames=list(cal[0].keys())); w.writeheader(); w.writerows(cal)
    report(rows, cal, {o: dict(gamma=v["gamma"], groups=v["groups"], n10=v["n10"], how=v["how"]) for o, v in _OREF.items()})

def report(rows, cal, orefs):
    f = lambda x, d=2: ("%.*f" % (d, x)) if isinstance(x, float) and np.isfinite(x) else "n/a"
    prim = {r["program"]: r for r in rows if r.get("status") == "scored" and r["decision"] == "lift" and r["gamma_ref"] == 1.0 and r["gamma_port"] == 1.0}
    c1 = [c for c in cal if c["decision"] == "lift" and c["gamma"] == 1.0][0]; gate = c1["kappa_median"] >= 0.20 and c1["kappa_lo"] > c1["shuffle95"]
    T = ["# DOOM-E11 stage 3 results: is `linuxdoom`'s partition specifically predictive of other programs' communities, from measurements alone?", "", "Registered design: [stage 3](../../preregistration/E11_SUBSYSTEMS_STAGE3.md). Arm F placement (no call edge read), excess homogeneity over communities of 10+ functions, about 30 alternative references. Full table: `stage3_table.csv`.", "",
         "## Calibration (10-fold on `linuxdoom`'s own functions, abstaining at the 95th percentile of nearest distance)", "", "| reference resolution | decision | kappa median [95% over folds] | shuffle 95th | accuracy | balanced accuracy |", "|---|---|---|---|---|---|"]
    for c in cal: T.append(f"| {c['gamma']} | {c['decision']} | {f(c['kappa_median'])} [{f(c['kappa_lo'])}, {f(c['kappa_hi'])}] | {f(c['shuffle95'])} | {f(c['acc'])} | {f(c['balanced'])} |")
    T += ["", f"**Gate (lift, resolution 1.0: median kappa at least 0.20 with lower bound above the shuffle 95th): {'PASSED' if gate else 'NOT PASSED'}.**", "", "## Specificity at the primary setting (reference resolution 1.0, port resolution 1.0, `lift`)", "", "Percentile = share of the ~30 alternative references whose excess homogeneity is at or below DOOM's; DOOM-specific = percentile at least 0.95.", "",
          "| program | group | functions | coverage | X DOOM | X alt median (95th) | difference | percentile | DOOM-specific | X file control |", "|---|---|---|---|---|---|---|---|---|---|"]
    for g in ("C", "M", "T", "R", "K", "U", "X"):
        for p in GROUPS[g]:
            r = prim.get(p)
            if r: T.append(f"| {p} | {g} | {r['functions']} | {f(r['coverage'])} | {f(r['X_doom'], 3)} | {f(r['X_alt_median'], 3)} ({f(r['X_alt_p95'], 3)}) | {f(r['diff'], 3)} | {f(r['pct'])} | {'**yes**' if r['specific'] else 'no'} | {f(r.get('X_file', float('nan')), 3)} |")
            else:
                any_r = [x for x in rows if x["program"] == p]
                if any_r: T.append(f"| {p} | {g} | {any_r[0].get('functions', '')} | | | | | | not scored: {any_r[0].get('status')} | |")
    spec = lambda ps: [p for p in ps if p in prim and prim[p]["specific"]]
    sc = lambda ps: [p for p in ps if p in prim]
    P2 = spec(GROUPS["C"]); P3 = spec(GROUPS["U"]); P5 = spec(["prboom-plus", "woof", "dsda-doom", "inter-doom", "fastdoom"]); trans = [p for p in GROUPS["T"] if p != "gore" and p in prim]; tspec = spec(trans)
    from scipy.stats import spearmanr
    xs = [prim[p]["pct"] for p in prim if GROUP_OF.get(p) in ORDINAL]; ys = [ORDINAL[GROUP_OF[p]] for p in prim if GROUP_OF.get(p) in ORDINAL]; rho = spearmanr(xs, ys).statistic if len(xs) > 3 else float("nan")
    frac = lambda g: (len(spec(GROUPS[g])), len(sc(GROUPS[g])))
    robust = lambda p: all(any(r["program"] == p and r.get("status") == "scored" and r["decision"] == "lift" and r["gamma_ref"] == 1.0 and r["gamma_port"] == gp and r["specific"] for r in rows) for gp in GAM) and any(r["program"] == p and r.get("status") == "scored" and r["decision"] == "argmax" and r["gamma_ref"] == 1.0 and r["gamma_port"] == 1.0 and r["specific"] for r in rows)
    p8 = [p for p in GROUPS["C"] if robust(p)]
    T += ["", "## Predictions", "", "| prediction | result | value |", "|---|---|---|",
          f"| P1 gate | {'met' if gate else 'NOT met'} | kappa {f(c1['kappa_median'])} [{f(c1['kappa_lo'])}] vs shuffle 95th {f(c1['shuffle95'])} |", f"| P2 at least five of six C ports DOOM-specific | {'met' if len(P2) >= 5 else 'NOT met'} | {len(P2)} of {len(sc(GROUPS['C']))} scored: {P2} |",
          f"| P3 at most one scored U program DOOM-specific | {'met' if len(P3) <= 1 else 'NOT met'} | {len(P3)} of {len(sc(GROUPS['U']))} scored: {P3} |", f"| P4 `gore` DOOM-specific; at most three of the other scored translations | {'met' if 'gore' in prim and prim['gore']['specific'] and len(tspec) <= 3 else 'NOT met'} | gore {'yes' if 'gore' in prim and prim['gore']['specific'] else 'no/unscored'}; others {len(tspec)} of {len(trans)}: {tspec} |",
          f"| P5 at least four of five modified ports DOOM-specific | {'met' if len(P5) >= 4 else 'NOT met'} | {len(P5)} of {len(sc(['prboom-plus', 'woof', 'dsda-doom', 'inter-doom', 'fastdoom']))} scored: {P5} |", f"| P6 Spearman(percentile, group rank) at least 0.5 | {'met' if rho >= 0.5 else 'NOT met'} | rho {f(float(rho))} (n {len(xs)}) |",
          f"| P7 R and K not DOOM-specific more often than U | {'met' if (frac('R')[0] / max(frac('R')[1], 1) <= frac('U')[0] / max(frac('U')[1], 1) + 1e-9 and frac('K')[0] / max(frac('K')[1], 1) <= frac('U')[0] / max(frac('U')[1], 1) + 1e-9) else 'NOT met'} | R {frac('R')}, K {frac('K')}, U {frac('U')} |",
          f"| P8 P2 robust to port resolution and to `argmax` for at least five of six | {'met' if len(p8) >= 5 else 'NOT met'} | {len(p8)} of 6: {p8} |", "", "## Other-program references used", "", "| program | resolution chosen | groups | groups of 10+ | method |", "|---|---|---|---|---|"] + [f"| {o} | {v['gamma']} | {v['groups']} | {v['n10']} | {v['how']} |" for o, v in orefs.items()]
    (OUT / "E11_STAGE3_RESULTS.md").write_text("\n".join(T) + "\n"); print("\n".join(T))

if __name__ == "__main__":
    main()
