"""DOOM-E12 method ladder. Registered design: preregistration/E12_METHOD_LADDER.md. Venv with networkx/pandas/scikit-learn; sfs on the path.
Per program: ranked one-to-one pair lists for each rung against linuxdoom, truth mapping, metrics at matched N, controls, rewiring null, gate.
Usage: python e12_ladder.py [--smoke]   (writes results/e12/)"""
import csv, glob, json, sys, time, collections
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src"); sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/measure")
from structural_fingerprint import blind as BL, features as F, twins as TW
from structural_fingerprint.fingerprint import build
from structural_fingerprint.reference import load_reference
from structural_fingerprint.scan_io import load_scan, resolve_scans
from structural_fingerprint.twins import TwinParams
from scipy.stats import rankdata
import e7_draws as D, e7_names as N
REPO = Path(__file__).resolve().parents[1]; OUT = REPO / "results" / "e12"; OUT.mkdir(parents=True, exist_ok=True)
SC = Path("/srv/storage_16tb/projects/doom-e7-work/scans/704cb35f0"); T9 = Path("/srv/storage_16tb/projects/doom-e7-work/e9/results/truth")
STOP = frozenset(l.strip() for l in open("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/manifest/name_stoplist.txt") if l.strip() and not l.startswith("#"))
SL = ["doomgeneric", "sdl-doom", "doom-ascii", "doom-wasm", "puredoom", "mood", "fastdoom", "doom-ios", "prboom-plus", "woof", "crispy-doom", "inter-doom", "doomretro", "nugget-doom", "dsda-doom", "eternity", "odamex", "edge-classic", "srb2"]
DEV = ["chocolate-doom"]; TR = ["gore", "doom-scheme", "dartdoom", "mochadoom", "managed-doom", "kocoa-doom"]
CTRL = ["lua", "nginx", "room4doom", "rust-doom", "quake", "quake2"]; HELD = ["leveldb", "curl", "libuv"]
GROUP = {**{p: "SL" for p in SL}, **{p: "DEV" for p in DEV}, **{p: "T" for p in TR}, **{p: "K" for p in CTRL}, **{p: "H" for p in HELD}}
NS = (50, 100, 250, 500); SEED_FRAC, HOPS = 0.15, 3; MIN_LOC = 6; REWIRE_MAX = 3000; NREWIRE = 10
FDRS, RATIOS = (0.001, 0.01, 0.05, 0.10), (0.7, 0.8, 0.9, 1.0)
bp = BL.BlindParams()

def pooled_cutoff_fdr(real, decoys, fdr):
    if len(real) == 0: return 0.0
    K = len(decoys); ts = np.sort(real); n_t = np.arange(1, len(ts) + 1)
    nd = np.sum([np.searchsorted(np.sort(d), ts, side="right") for d in decoys], axis=0)
    est = (nd + 1) / (K * n_t); q = np.minimum.accumulate(est[::-1])[::-1]; ok = np.flatnonzero(q <= fdr)
    return float(ts[ok[-1]]) if len(ok) else 0.0

def one_to_one(cands):
    """cands: (score, i, j) with LOWER score = better. Greedy by score; ties by (i, j). Returns ordered list (i, j, score)."""
    out, ui, uj = [], set(), set()
    for s, i, j in sorted(cands, key=lambda x: (x[0], x[1], x[2])):
        if i in ui or j in uj: continue
        ui.add(i); uj.add(j); out.append((i, j, s))
    return out

_REF = {}
def tables(name, preset):
    key = (name, preset)
    if key not in _REF:
        lens, mode, rank = {"F0": ("structure", "density", False), "F1a": ("portable", "density", False), "F1b": ("portable", "composition", False), "F1c": ("portable", "composition", True), "P": ("portable", "composition", False)}[preset]
        ref = load_reference(lens); sc = load_scan(resolve_scans([SC / name])[0], ref.signal_columns, name=name)
        t = build(sc, ref, min_loc=3, keyword_mode=mode).functions
        if rank:
            v = np.column_stack([(rankdata(t.vectors[:, c]) - 0.5) / len(t.vectors) for c in range(t.vectors.shape[1])]).astype(t.vectors.dtype); t.vectors = v
        _REF[key] = (t, ref, sc)
    return _REF[key]

def fingerprint_rungs(name, uni_ok):
    """F0, F1a, F1b, F1c: twins both directions, pooled K=25, sweep over (fdr, ratio); returns {(rung, fdr, ratio): ordered list of (port_row, ref_row, dist)}"""
    out = {}
    for preset in ("F0", "F1a", "F1b", "F1c"):
        tp, _, _ = tables(name, preset); tl, _, _ = tables("linuxdoom", preset)
        for ratio in RATIOS:
            par = TwinParams(min_loc=MIN_LOC, ratio=ratio, fdr=0.01)
            res = {}
            for tag, q, t in (("pl", tp, tl), ("lp", tl, tp)):
                rows, dec, real, s = D.pair_draws(q, t, list(range(25)), par); res[tag] = (dec, real, s)
            for fdr in FDRS:
                cands = []
                dec, real, s = res["pl"]; r = TW.accept(s, pooled_cutoff_fdr(real, dec, fdr))
                d_all = np.where(r.exact, 0.0, r.distance)
                cands += [(float(d), int(a), int(b)) for a, b, d in zip(r.q_index, r.t_index, d_all)]
                dec, real, s = res["lp"]; r = TW.accept(s, pooled_cutoff_fdr(real, dec, fdr)); d_all = np.where(r.exact, 0.0, r.distance)
                cands += [(float(d), int(b), int(a)) for a, b, d in zip(r.q_index, r.t_index, d_all)]
                out[(preset, fdr, ratio)] = [(i, j, 1.0 - d) for i, j, d in one_to_one(cands)]
    return out

def graph_rungs(name, rng, rewire=False, ref_name="linuxdoom"):
    """G0, G1, G2, S, E1, E2, E3, E3c: returns ({rung: ordered list of (port_row, ref_row, score)}, gate stats). Uses blind views of the portable composition tables."""
    tp, ref, sc = tables(name, "P"); tl, _, scl = tables(ref_name, "P"); pv = BL.blind_view(tp); rv = BL.blind_view(tl)
    if rewire: pv = BL.rewired(pv, rng)
    na = len(ref.archetype_names); hp = BL.hop_matrix(pv, bp.hop_cap); hr = BL.hop_matrix(rv, bp.hop_cap)
    keep = [i for i, n in enumerate(ref.feature_names) if n not in ("log_complexity", "func_internal_density")]
    def comp(scan, view): return F.raw_features(ref, scan.loc, scan.complexity, scan.args, scan.keyword_density, scan.signals, keyword_mode="composition")[:, keep][view.rows]
    pc, rc = comp(sc, pv), comp(scl, rv); rn = rc / np.maximum(np.linalg.norm(rc, axis=1, keepdims=True), 1e-9)
    def rbh_list(use_graph, use_meas, alpha):
        xp = BL.descriptors(pv, na, use_graph, use_meas, None, bp.geometry_only); xr = BL.descriptors(rv, na, use_graph, use_meas, None, bp.geometry_only)
        m = BL._sqdist(xp, xr); m = m / (m.max() or 1.0); t = BL.fused_gw(m, hp, hr, alpha, bp.epsilon, bp.outer)
        br, bq = np.argmax(t, axis=1), np.argmax(t, axis=0)
        lst = sorted(((i, int(br[i]), float(t[i, br[i]])) for i in range(pv.n) if bq[br[i]] == i), key=lambda x: (-x[2], x[0]))
        return lst, t
    g0, _ = rbh_list(False, True, 0.0); g1, _ = rbh_list(True, False, bp.alpha); g2, t = rbh_list(True, True, bp.alpha)
    k = max(1, int(len(g2) * SEED_FRAC)); seeds = g2[:k]
    pn = collections.defaultdict(set)
    for u, v in pv.edges.tolist(): pn[u].add(v); pn[v].add(u)
    rnb = collections.defaultdict(set)
    for u, v in rv.edges.tolist(): rnb[u].add(v); rnb[v].add(u)
    def extend(calibrate):
        anchor = {i: j for i, j, _ in seeds}; used = set(anchor.values()); order = [(i, j, s) for i, j, s in seeds]; lists = {}
        delta = np.mean(pc[[i for i, _, _ in seeds]] - rc[[j for _, j, _ in seeds]], axis=0) if (calibrate and seeds) else np.zeros(pc.shape[1])
        psh = pc - delta; psn = psh / np.maximum(np.linalg.norm(psh, axis=1, keepdims=True), 1e-9)
        for h in range(1, HOPS + 1):
            props = []
            for pu in range(pv.n):
                if pu in anchor: continue
                votes = collections.Counter()
                for q in pn.get(pu, ()):
                    if q in anchor:
                        for c in rnb.get(anchor[q], ()):
                            if c not in used: votes[c] += 1
                if not votes: continue
                cands = np.array(list(votes.keys())); v = np.array([votes[c] for c in cands], float); cos = rn[cands] @ psn[pu]
                sco = v * (1.0 + np.maximum(cos, 0.0)) + 0.25 * t[pu, cands] / (t[pu].max() or 1.0); b = int(np.argmax(sco)); props.append((float(sco[b]), pu, int(cands[b])))
            props.sort(reverse=True)
            for s_, pu, ru in props:
                if pu not in anchor and ru not in used: anchor[pu] = ru; used.add(ru); order.append((pu, ru, s_))
            lists[h] = list(order)
        return lists, anchor
    unc, _ = extend(False); cal, anchor = extend(True)
    sup = [sum(1 for u in pn[qi] if u in anchor and anchor[u] in rnb[rc_]) for qi, rc_ in anchor.items()]
    tr = [float(t[qi, rc_] / (t[qi].max() + 1e-12)) for qi, rc_ in anchor.items()]
    gate = dict(strong_fgw=float(np.mean([x >= 0.5 for x in tr])) if tr else 0.0, mean_sup=float(np.mean(sup)) if sup else 0.0)
    gate["passes"] = bool(gate["strong_fgw"] >= 0.20 and gate["mean_sup"] >= 2.10)
    gate["E3c_hop_ends"] = [len(cal[h]) for h in (1, 2, 3)]  # added after the E12 run (finder / subsystem map); changes no result
    toRow = lambda lst: [(int(pv.rows[i]), int(rv.rows[j]), s) for i, j, s in lst]
    return {"G0": toRow(g0), "G1": toRow(g1), "G2": toRow(g2), "S": toRow(seeds), "E1": toRow(unc[1]), "E2": toRow(unc[2]), "E3": toRow(unc[3]), "E3c": toRow(cal[3])}, gate

# ------------------------------------------------------------------ truth
_TRUTH = {}
def truth():
    if not _TRUTH:
        fn = pd.read_csv(T9 / "functions.csv", dtype=str); pr = pd.read_csv(T9 / "pairs.csv", dtype=str)
        fn = fn[fn.engine_row.notna() & (fn.engine_row != "")]; fn["row"] = fn.engine_row.astype(float).astype(int)
        _TRUTH["fn"] = fn; ldf = fn[fn.program == "linuxdoom"]; _TRUTH["ld_hash"] = dict(zip(ldf.row, ldf.body_hash))
        pr = pr[((pr.prog_a == "linuxdoom") | (pr.prog_b == "linuxdoom"))].copy(); pr["jaccard"] = pr.jaccard.astype(float); pr["jid"] = pr.jaccard_idnorm.astype(float)
        a = pr.prog_a == "linuxdoom"; pr["port"] = np.where(a, pr.prog_b, pr.prog_a); pr["pf"] = np.where(a, pr.func_b, pr.func_a); pr["rf"] = np.where(a, pr.func_a, pr.func_b)
        h = {(r.program, r.func_id): r.body_hash for r in fn.itertuples()}; pr["ph"] = [h.get((p, f)) for p, f in zip(pr.port, pr.pf)]; pr["rh"] = [h.get(("linuxdoom", f)) for f in pr.rf]; pr = pr.dropna(subset=["ph", "rh"])
        _TRUTH["pairs"] = pr
    return _TRUTH

def truth_sets(name):
    T = truth(); p = T["pairs"][T["pairs"].port == name]; fn = T["fn"][T["fn"].program == name]
    sets = {"j09": set(zip(p.ph[p.jaccard >= 0.9], p.rh[p.jaccard >= 0.9])), "j06": set(zip(p.ph[p.jaccard >= 0.6], p.rh[p.jaccard >= 0.6])), "id09": set(zip(p.ph[p.jid >= 0.9], p.rh[p.jid >= 0.9]))}
    maxj = p.groupby("ph").jaccard.max().to_dict()
    return sets, dict(zip(fn.row, fn.body_hash)), maxj, fn

def score_list(lst, name, tp, tl, kind):
    """Returns dict with counts for the list (already in the loc>=6 universe)."""
    if kind == "SL":
        sets, ph_of, maxj, fn = truth_sets(name); ld_h = truth()["ld_hash"]; res = {}
        for tag, S in sets.items():
            true = false = unl = 0
            for pr_, rr_, _ in lst:
                hp_, hr_ = ph_of.get(pr_), ld_h.get(rr_)
                if hp_ is None or hr_ is None: unl += 1
                elif (hp_, hr_) in S: true += 1
                else: false += 1
            res[tag] = (true, false, unl)
        return res
    if kind in ("T", "DEVT"):
        true = false = 0
        for pr_, rr_, _ in lst:
            a, b = N.name_key(str(tp.name[pr_])), N.name_key(str(tl.name[rr_]))
            if a and b and a == b and a not in STOP: true += 1
            else: false += 1
        return {"name": (true, false, 0)}
    return {"all_false": (0, len(lst), 0)}

def recall_fn(lst, name, tag="j09"):
    sets, ph_of, maxj, fn = truth_sets(name); ld_h = truth()["ld_hash"]; S = sets[tag]
    partners = collections.defaultdict(set)
    for a, b in S: partners[a].add(b)
    rec_hashes = set(); got = set()
    for pr_, rr_, _ in lst:
        hp_, hr_ = ph_of.get(pr_), ld_h.get(rr_)
        if hp_ is not None and hr_ is not None and (hp_, hr_) in S: got.add(hp_)
    n_with = len(partners); return (len(got) / n_with if n_with else float("nan")), n_with, len(got)

def run_program(args):
    name, smoke = args; t0 = time.time(); rng = np.random.default_rng(abs(hash(name)) % (2 ** 32)); kind = GROUP[name]; rows = []; lists = {}
    tp, _, _ = tables(name, "P"); tl, _, _ = tables("linuxdoom", "P"); nelig = int(((tp.loc >= MIN_LOC)).sum())
    uni = lambda lst: [(a, b, s) for a, b, s in lst if tp.loc[a] >= MIN_LOC and tl.loc[b] >= MIN_LOC]
    fr = fingerprint_rungs(name, None) if not smoke else {}
    gr, gate = graph_rungs(name, rng)
    allr = {}
    for (preset, fdr, ratio), lst in fr.items(): allr[f"{preset}|{fdr}|{ratio}"] = lst
    for r, lst in gr.items(): allr[r] = lst
    for key, lst in allr.items():
        full = uni(lst); dropped = len(lst) - len(full)
        for N_ in list(NS) + ["full"]:
            sub = full if N_ == "full" else full[:N_]
            if not sub and N_ != "full": continue
            sc = score_list(sub, name, tp, tl, "SL" if kind in ("SL",) else ("DEVT" if kind == "T" else ("SL" if kind == "DEV" else "K")))
            for tag, (tr_, fa_, un_) in sc.items():
                row = dict(program=name, group=kind, rung=key, N=N_, truth=tag, emitted=len(sub), dropped_endpoints=dropped, true=tr_, false=fa_, unlabelled=un_, precision=(tr_ / (tr_ + fa_)) if (tr_ + fa_) else float("nan"), lower_bound=tr_ / max(len(sub), 1), eligible=nelig, per1000=1000 * len(sub) / max(nelig, 1))
                if kind in ("SL", "DEV") and tag == "j09" or (kind in ("SL", "DEV") and tag in ("j06", "id09")):
                    r_, nwith, got = recall_fn(sub, name, tag); row.update(recall=r_, truth_functions=nwith, recovered=got)
                rows.append(row)
    rows.append(dict(program=name, group=kind, rung="GATE", N="full", strong_fgw=gate["strong_fgw"], mean_sup=gate["mean_sup"], passes=gate["passes"], eligible=nelig))
    # rewiring null
    if tp.loc.shape[0] <= REWIRE_MAX and not smoke:
        for d in range(NREWIRE):
            gr2, _ = graph_rungs(name, np.random.default_rng(1000 + d), rewire=True)
            for r, lst in gr2.items():
                full = uni(lst)
                for N_ in (100, 250):
                    sub = full[:N_]; sc = score_list(sub, name, tp, tl, "SL" if kind in ("SL", "DEV") else ("DEVT" if kind == "T" else "K"))
                    for tag, (tr_, fa_, un_) in sc.items():
                        rows.append(dict(program=name, group=kind, rung="REWIRED|" + r, N=N_, truth=tag, draw=d, emitted=len(sub), true=tr_, false=fa_, unlabelled=un_, precision=(tr_ / (tr_ + fa_)) if (tr_ + fa_) else float("nan")))
    lists = {k: v for k, v in allr.items() if k in ("E3c", "G2", "S")}
    json.dump({k: [(int(a), int(b), float(s)) for a, b, s in v] for k, v in lists.items()}, open(OUT / f"lists_{name}.json", "w"))
    print(name, "done", f"{time.time() - t0:.0f}s", flush=True); return rows

def main(smoke=False):
    names = (DEV + SL + TR + CTRL + HELD) if not smoke else ["doomgeneric", "gore", "lua"]
    t0 = time.time(); rows = []
    with ProcessPoolExecutor(1 if smoke else 2) as ex:  # owner 11-25: 2 cores after the smoke test (pin with taskset, OMP/OPENBLAS threads=1)
        for r in ex.map(run_program, [(n, smoke) for n in names]): rows += r
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("program", "group", "rung", "N", "truth"), k))
    with open(OUT / ("e12_table_smoke.csv" if smoke else "e12_table.csv"), "w", newline="") as f: w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    print("done", len(rows), "rows", f"{time.time() - t0:.0f}s", flush=True)

if __name__ == "__main__":
    main(smoke="--smoke" in sys.argv)
