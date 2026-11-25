"""DOOM-E11 stage 4: wiring against chance on the discovered subsystems (non-blind placement by twin, name, path). Registered design:
preregistration/E11_SUBSYSTEMS_STAGE4.md. Venv with networkx + scikit-learn; sfs on the path. Writes results/e11/stage4_*.csv."""
import csv, glob, json, re, sys, time, collections
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src"); sys.path.insert(0, str(Path(__file__).resolve().parent))
from structural_fingerprint.fingerprint import Fingerprint
from structural_fingerprint import subway as SW
from sklearn.metrics import cohen_kappa_score
REPO = Path(__file__).resolve().parents[1]; OUT = REPO / "results" / "e11"; OUT.mkdir(parents=True, exist_ok=True)
WORK = Path("/srv/storage_16tb/projects/doom-e11-work")
FP = "/srv/storage_16tb/projects/doom-e7-work/results/e7/phase[AB]/fingerprints"
TAXFILE = "/srv/storage_16tb/projects/structural-fingerprint-scanner/examples/doom/subsystems.json"
GROUPS = {"C": ["chocolate-doom", "crispy-doom", "doomgeneric", "sdl-doom", "doom-ascii", "doom-wasm"],
          "M": ["mood", "prboom-plus", "woof", "dsda-doom", "inter-doom", "fastdoom", "doom-ios", "eternity", "odamex", "srb2", "puredoom", "nugget-doom", "doomretro", "gzdoom", "doomsday", "edge-classic", "doom3do", "doom3-bfg"],
          "T": ["gore", "doom-scheme", "dartdoom", "managed-doom", "mochadoom", "kocoa-doom", "doomf77", "doo-cr"],
          "R": ["helion", "rust-doom", "room4doom", "cssdoom", "fsharp-doom", "doom-fx", "sqldoom"],
          "K": ["agentic-cobol-doom-cc", "agentic-cobol-doom-codex", "fps-cob", "c-raycasting", "c-raycasting2", "goom3d"],
          "U": ["nginx", "curl", "lua", "leveldb", "libuv", "bubbletea", "macroquad", "carddemo-cobol-ctrl"], "X": ["quake", "quake2", "freedoom"]}
GROUP_OF = {p: g for g, ps in GROUPS.items() for p in ps}
NDRAW, MIN_PLACED, MIN_CROSS, MIN_POP, MIN_FILES, MAX_FILE_SHARE, MIN_NAME, NBOOT = 1000, 100, 500, 8, 30, 0.25, 6, 200
_FPC = {}
def table(name):
    if name not in _FPC:
        p = glob.glob(f"{FP}/{name}.sfp.json"); _FPC[name] = Fingerprint.load(Path(p[0])).functions if p else None
    return _FPC[name]
def code(t): return SW._code_mask(t)
def base(path): return str(path).rsplit("/", 1)[-1].lower()
def stem(path): b = base(path); return b.rsplit(".", 1)[0] if "." in b else b
def prefix(path):
    m = re.match(r"^([a-z]+_)", base(path)); return m.group(1) if m else None

class DerivedRules:
    """File stems and module prefixes of the reference, each taking the majority subsystem of its functions (longest first)."""
    def __init__(self, ref, ref_labels):
        st, px = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
        for p, l in zip(ref.path, ref_labels):
            if l < 0: continue
            st[stem(p)][int(l)] += 1
            if prefix(p): px[prefix(p)][int(l)] += 1
        self.stems = sorted(((s, c.most_common(1)[0][0]) for s, c in st.items()), key=lambda x: -len(x[0]))
        self.prefixes = sorted(((s, c.most_common(1)[0][0]) for s, c in px.items()), key=lambda x: -len(x[0]))
    def classify(self, path, repo=None):
        b = base(path)
        for s, l in self.stems:
            if b.startswith(s): return l
        for s, l in self.prefixes:
            if b.startswith(s): return l
        return -1

def name_index(ref, ref_labels):
    """normalised name (and the name without a module prefix) -> subsystem, dropping any name that maps to more than one subsystem
    or is shorter than MIN_NAME characters (the scanner's setdefault silently let the first win)."""
    seen = collections.defaultdict(set)
    for n, l in zip(ref.name, ref_labels):
        if l < 0: continue
        for key in {SW._norm(n)} | ({SW._norm(str(n).split("_", 1)[1])} if "_" in str(n) else set()):
            if len(key) >= MIN_NAME: seen[key].add(int(l))
    return {k: next(iter(v)) for k, v in seen.items() if len(v) == 1}

def place(t, ref, ref_labels, twin_pairs, path_rule, names, fallback_label=None):
    """labels per table row (-1 unplaced) and source per row ('twin','name','path',''). Fallback or unknown path -> unplaced."""
    n = len(t); labels = np.full(n, -1, np.int64); src = np.array([""] * n, dtype=object); isc = code(t)
    for l, p in twin_pairs:
        if isc[p] and ref_labels[l] >= 0: labels[p] = ref_labels[l]; src[p] = "twin"
    for i in np.flatnonzero(isc & (labels < 0)):
        nm = str(t.name[i]); hit = names.get(SW._norm(nm))
        if hit is None and "_" in nm: hit = names.get(SW._norm(nm.split("_", 1)[1]))
        if hit is not None: labels[i] = hit; src[i] = "name"; continue
        lab = path_rule.classify(str(t.path[i]), t.repo)
        if lab is not None and lab >= 0 and lab != fallback_label: labels[i] = lab; src[i] = "path"
    return labels, src

def name_only(t, names):
    out = np.full(len(t), -1, np.int64)
    for i in np.flatnonzero(code(t)):
        nm = str(t.name[i]); h = names.get(SW._norm(nm))
        if h is None and "_" in nm: h = names.get(SW._norm(nm.split("_", 1)[1]))
        if h is not None: out[i] = h
    return out
def path_only(t, rule, fallback_label=None):
    out = np.full(len(t), -1, np.int64)
    for i in np.flatnonzero(code(t)):
        l = rule.classify(str(t.path[i]), t.repo)
        if l is not None and l >= 0 and l != fallback_label: out[i] = l
    return out

def cos_pair(m, ref_m, log=False):
    a, b = (np.log1p(m), np.log1p(ref_m)) if log else (m.astype(float), ref_m.astype(float))
    return SW._cosine(a, b), SW._cosine(SW._off_diagonal(a), SW._off_diagonal(b))

def file_shuffle(labels, files, rng):
    placed = np.flatnonzero(labels >= 0); uf, inv = np.unique(files[placed], return_inverse=True); sizes = np.bincount(inv)
    if len(uf) < MIN_FILES or sizes.max() / sizes.sum() > MAX_FILE_SHARE: return None
    lists = [labels[placed][inv == k] for k in range(len(uf))]; strata = np.floor(np.log2(np.maximum(sizes, 1))).astype(int); donor = np.arange(len(uf)); new = labels.copy()
    for s in np.unique(strata):
        idx = np.flatnonzero(strata == s); donor[idx] = rng.permutation(idx)
    for k in range(len(uf)): new[placed[inv == k]] = rng.permutation(np.resize(lists[donor[k]], sizes[k]))
    return new

def nulls(labels, edges, files, ref_m, s, rng, ndraw=NDRAW):
    placed = np.flatnonzero(labels >= 0); res = {"function": [], "file": [], "rename": []}
    for _ in range(ndraw):
        sh = labels.copy(); sh[placed] = rng.permutation(labels[placed]); res["function"].append(cos_pair(SW._calls(sh, edges, s), ref_m))
        fs = file_shuffle(labels, files, rng)
        if fs is not None: res["file"].append(cos_pair(SW._calls(fs, edges, s), ref_m))
        pm = rng.permutation(s); rn = labels.copy(); rn[placed] = pm[labels[placed]]; res["rename"].append(cos_pair(SW._calls(rn, edges, s), ref_m))
    return {k: np.array(v) for k, v in res.items()}

def evaluate(t, labels, src, arm, files, isc, rng, ndraw, tag, names_idx, rule, fb, full_diag=True):
    s, ref_m = arm["s"], arm["ref_m"]; placed = labels >= 0; npl = int(placed.sum())
    m = SW._calls(labels, t.edges, s); cross_calls = int(SW._off_diagonal(m).sum()); pop = int((np.bincount(labels[placed], minlength=s) >= 3).sum()) if npl else 0
    row = dict(program=t.repo, group=GROUP_OF.get(t.repo, "?"), arm=arm["name"], gamma=arm["gamma"], subset=tag, functions=int(isc.sum()), placed=npl, coverage=npl / max(int(isc.sum()), 1),
               src_twin=int((src == "twin").sum()), src_name=int((src == "name").sum()), src_path=int((src == "path").sum()), cross_calls=cross_calls, populated=pop,
               files=int(len(np.unique(files[placed]))) if npl else 0, max_file_share=float(np.bincount(np.unique(files[placed], return_inverse=True)[1]).max() / npl) if npl else float("nan"),
               calls_per_function=len(t.edges) / max(int(isc.sum()), 1), ref_diagonal_share=arm["diag"], ref_floor=arm["floor"])
    w, c = cos_pair(m, ref_m); row.update(wiring=w, cross=c); wl, cl = cos_pair(m, ref_m, log=True); row.update(wiring_log=wl, cross_log=cl)
    scored = npl >= MIN_PLACED and cross_calls >= MIN_CROSS and pop >= MIN_POP
    low = (not scored) and npl >= MIN_PLACED and cross_calls >= 100 and pop >= MIN_POP   # descriptive tier: 100 to 499 cross calls
    row["status"] = "scored" if scored else ("low-count (descriptive)" if low else "not scored (placed %d, cross calls %d, populated %d)" % (npl, cross_calls, pop))
    if scored or low:
        bs = []
        for _ in range(NBOOT):
            e = t.edges[rng.integers(0, len(t.edges), len(t.edges))]; bs.append(cos_pair(SW._calls(labels, e, s), ref_m)[1])
        bs = np.array(bs); row["cross_ci_lo"], row["cross_ci_hi"] = float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))
        nl = nulls(labels, t.edges, files, ref_m, s, rng, ndraw)
        for kind, arr in nl.items():
            if len(arr) == 0: row[f"null_{kind}_n"] = 0; continue
            cr = arr[:, 1]; cr = cr[np.isfinite(cr)]; sd = float(cr.std()) if len(cr) > 1 else float("nan")
            row.update({f"null_{kind}_n": len(cr), f"null_{kind}_mean": float(cr.mean()), f"null_{kind}_sd": sd, f"null_{kind}_lo": float(np.percentile(cr, 2.5)), f"null_{kind}_hi": float(np.percentile(cr, 97.5)),
                        f"gap_{kind}": c - float(cr.mean()), f"z_{kind}": (c - float(cr.mean())) / sd if sd and sd > 0 else float("nan"), f"pct_{kind}": float((cr <= c).mean()),
                        f"mdg_{kind}": float(np.percentile(cr, 97.5) - cr.mean())})
    return row

def run_program(args):
    name, arms, ndraw = args; rng = np.random.default_rng(abs(hash(name)) % (2 ** 32)); t = table(name); rows = []
    if t is None or t.edges is None or not len(t.edges): return [dict(program=name, group=GROUP_OF.get(name, "?"), status="no call graph")]
    isc = code(t); files = np.array([str(p) for p in t.path]); tw = WORK / "placement" / f"{name}.npz"
    pairs = list(zip(np.load(tw)["pairs_l"].tolist(), np.load(tw)["pairs_p"].tolist())) if tw.exists() else []
    for arm in arms:
        labels, src = place(t, arm["ref"], arm["ref_labels"], pairs, arm["rule"], arm["names"], arm["fb"])
        row = evaluate(t, labels, src, arm, files, isc, rng, ndraw, "all", arm["names"], arm["rule"], arm["fb"])
        # placement quality (same arm)
        npn, npp = name_only(t, arm["names"]), path_only(t, arm["rule"], arm["fb"])
        tw_idx = np.flatnonzero(src == "twin"); both = np.flatnonzero((npn >= 0) & (npp >= 0)); np_any = (npn[tw_idx] >= 0) | (npp[tw_idx] >= 0)
        try: row["kappa_namepath_vs_twin"] = float(cohen_kappa_score(labels[tw_idx][np_any], np.where(npn[tw_idx] >= 0, npn[tw_idx], npp[tw_idx])[np_any])) if np_any.sum() > 20 else float("nan")
        except Exception: row["kappa_namepath_vs_twin"] = float("nan")
        row["n_name_and_path"] = int(len(both)); row["kappa_name_vs_path"] = float(cohen_kappa_score(npn[both], npp[both])) if len(both) > 20 and len(set(npn[both])) > 1 else float("nan")
        rows.append(row)
        if arm["name"] == "D" and arm["gamma"] == 1.0:   # circularity control: by placement source
            for tag, keep in (("non_twin", src != "twin"), ("twin_only", src == "twin")):
                lab2 = np.where(keep, labels, -1); src2 = np.where(keep, src, "")
                rows.append(evaluate(t, lab2, src2, arm, files, isc, rng, ndraw, tag, arm["names"], arm["rule"], arm["fb"]))
    return rows

def diag_floor(m):
    tot = float(m.sum()); return (float(np.trace(m)) / tot if tot else float("nan")), SW.wiring_floor(m)

def build_arms(gamma_list=(1.0, 0.5, 2.0)):
    import e11_stage2 as S2
    ref = table("linuxdoom"); tax = SW.Taxonomy.load(TAXFILE); arms = []
    hand = np.where(code(ref), [tax.classify(str(x), ref.repo) for x in ref.path], -1).astype(np.int64); fbh = tax.index[tax.fallback]; hand_ref = np.where(hand == fbh, -1, hand)
    for g in gamma_list:
        labs = S2.reference(g)["labs"]; rl = np.full(len(ref), -1, np.int64)
        for r, l in labs.items(): rl[int(r)] = int(l)
        s = int(rl.max()) + 1; rm = SW._calls(rl, ref.edges, s); d, f = diag_floor(rm)
        arms.append(dict(name="D", gamma=g, ref=ref, ref_labels=rl, s=s, rule=DerivedRules(ref, rl), names=name_index(ref, rl), fb=None, ref_m=rm, diag=d, floor=f))
    s = len(tax.subsystems); hm = SW._calls(hand_ref, ref.edges, s); d, f = diag_floor(hm); nh = name_index(ref, hand_ref)
    tax3 = SW.Taxonomy(name="hand without per-port overrides", subsystems=list(tax.subsystems), basename_prefix=list(tax.basename_prefix), path_keyword=list(tax.path_keyword), fallback=tax.fallback, overrides={})
    for nm, rule in (("H1", DerivedRules(ref, hand_ref)), ("H3", tax3), ("H2", tax)):
        arms.append(dict(name=nm, gamma=None, ref=ref, ref_labels=hand_ref, s=s, rule=rule, names=nh, fb=fbh, ref_m=hm, diag=d, floor=f))
    return arms

def recovery(arms):
    """Held-out recovery on linuxdoom: five random 20% holdouts placed by name then path rules derived from the other 80%."""
    ref = table("linuxdoom"); out = []; rng = np.random.default_rng(7)
    for arm in arms:
        if arm["name"] not in ("D", "H1") or arm["gamma"] not in (None, 1.0): continue
        lab = arm["ref_labels"]; idx = np.flatnonzero(lab >= 0); accs, covs = [], []
        for _ in range(5):
            hold = rng.choice(idx, size=len(idx) // 5, replace=False); tr = lab.copy(); tr[hold] = -1
            rule = DerivedRules(ref, tr); names = name_index(ref, tr); ok = pl = 0
            for i in hold:
                nm = str(ref.name[i]); h = names.get(SW._norm(nm))
                if h is None and "_" in nm: h = names.get(SW._norm(nm.split("_", 1)[1]))
                if h is None:
                    h = rule.classify(str(ref.path[i]), ref.repo); h = None if h is None or h < 0 else h
                if h is not None: pl += 1; ok += int(h == lab[i])
            accs.append(ok / max(pl, 1)); covs.append(pl / len(hold))
        rule = DerivedRules(ref, lab); allp = [(rule.classify(str(ref.path[i]), ref.repo) == lab[i]) for i in idx]
        out.append(dict(arm=arm["name"], holdout_accuracy=float(np.mean(accs)), holdout_coverage=float(np.mean(covs)), stem_prefix_reproduces_labels=float(np.mean(allp)), reference_diagonal_share=arm["diag"], reference_floor=arm["floor"]))
    return out

def a12(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if not len(x) or not len(y): return float("nan")
    return float(((x[:, None] > y[None, :]).sum() + 0.5 * (x[:, None] == y[None, :]).sum()) / (len(x) * len(y)))

def report(rows, rec):
    import pandas as pd
    from scipy.stats import spearmanr
    df = pd.DataFrame(rows); sc = df[df.status == "scored"]
    f = lambda x, d=2: ("%.*f" % (d, x)) if isinstance(x, float) and np.isfinite(x) else "n/a"
    D = sc[(sc.arm == "D") & (sc.gamma == 1.0)]; Da = D[D.subset == "all"].set_index("program"); Dn = D[D.subset == "non_twin"].set_index("program")
    def above(r, strict=True):  # (above, which null)
        if r.get("null_file_n", 0) and r["null_file_n"] > 0 and np.isfinite(r.get("null_file_hi", np.nan)): return r["cross"] > r["null_file_hi"], "file"
        return r["cross"] > r["null_function_hi"], "function (weaker)"
    T = ["# DOOM-E11 stage 4 results: wiring against chance on the discovered subsystems", "", "Registered design: [stage 4](../../preregistration/E11_SUBSYSTEMS_STAGE4.md). Placement by twin, name and file path (not blind). Full table: `stage4_table.csv`; recovery: `stage4_recovery.csv`.", "",
         "## References and placement rules (read before any gap)", "", "| arm | reference diagonal share | wiring floor | held-out recovery (80/20) | coverage of held-out | stem and prefix reproduce labels |", "|---|---|---|---|---|---|"]
    for r in rec: T.append(f"| {r['arm']} | {f(r['reference_diagonal_share'])} | {f(r['reference_floor'])} | {f(r['holdout_accuracy'])} | {f(r['holdout_coverage'])} | {f(r['stem_prefix_reproduces_labels'])} |")
    T += ["", "## Arm D (discovered subsystems, resolution 1.0), all placements", "", "Cross-wiring against chance. 'File null' is the size-stratified profile swap (undefined with fewer than 30 placed files or one file over 25%). Standardised gap = (real - null mean) / null SD.", "",
          "| program | grp | placed (cov) | twin/name/path | files | cross calls | cross [95% CI] | function null mean (97.5th) | file null mean (97.5th) | z function | z file | above file/function 97.5th | non-twin: above function 97.5th |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in "CMTRKUX":
        for p in GROUPS[g]:
            r = Da.loc[p] if p in Da.index else None
            if r is None:
                x = df[(df.program == p) & (df.arm == "D") & (df.gamma == 1.0) & (df.subset == "all")]
                T.append(f"| {p} | {g} | " + (f"{int(x.iloc[0]['placed'])} ({f(x.iloc[0]['coverage'])}) | {int(x.iloc[0]['src_twin'])}/{int(x.iloc[0]['src_name'])}/{int(x.iloc[0]['src_path'])} | {int(x.iloc[0]['files'])} | {int(x.iloc[0]['cross_calls'])} | not scored: {x.iloc[0]['status']} |" if len(x) else "no call graph or no scan |") + " | | | | | | |"); continue
            ab, which = above(r); nt = Dn.loc[p] if p in Dn.index else None
            T.append(f"| {p} | {g} | {int(r['placed'])} ({f(r['coverage'])}) | {int(r['src_twin'])}/{int(r['src_name'])}/{int(r['src_path'])} | {int(r['files'])} | {int(r['cross_calls'])} | {f(r['cross'])} [{f(r['cross_ci_lo'])}, {f(r['cross_ci_hi'])}] | {f(r['null_function_mean'])} ({f(r['null_function_hi'])}) | "
                     f"{f(r.get('null_file_mean', float('nan')))} ({f(r.get('null_file_hi', float('nan')))}) | {f(r['z_function'], 1)} | {f(r.get('z_file', float('nan')), 1)} | {'**yes**' if ab else 'no'} ({which}) | "
                     + (("**yes**" if nt['cross'] > nt['null_function_hi'] else "no") if nt is not None else "not scored") + " |")
    low = df[(df.status == "low-count (descriptive)") & (df.arm == "D") & (df.gamma == 1.0) & (df.subset == "all")]
    T += ["", "## Low-count programs (100 to 499 cross calls; descriptive only, not used by any prediction)", "", "| program | grp | placed (cov) | cross calls | cross | function null mean (97.5th) | z function | file null (97.5th) |", "|---|---|---|---|---|---|---|---|"]
    for _, r in low.iterrows(): T.append(f"| {r['program']} | {r['group']} | {int(r['placed'])} ({f(r['coverage'])}) | {int(r['cross_calls'])} | {f(r['cross'])} | {f(r['null_function_mean'])} ({f(r['null_function_hi'])}) | {f(r['z_function'], 1)} | {f(r.get('null_file_mean', float('nan')))} ({f(r.get('null_file_hi', float('nan')))}) |")
    # arm comparison
    T += ["", "## Arm comparison (cross-wiring standardised gap against the function shuffle, resolution 1.0 for D)", "", "| program | D | H1 (hand, derived rules) | H3 (hand rules, no overrides) | H2 (hand taxonomy as shipped) |", "|---|---|---|---|---|"]
    arms = {a: sc[(sc.arm == a) & (sc.subset == "all") & ((sc.gamma == 1.0) | sc.gamma.isna())].set_index("program") for a in ("D", "H1", "H3", "H2")}
    for g in "CMTRUX":
        for p in GROUPS[g]:
            if any(p in arms[a].index for a in arms): T.append(f"| {p} | " + " | ".join((f(arms[a].loc[p, "z_function"], 1) if p in arms[a].index else "not scored") for a in ("D", "H1", "H3", "H2")) + " |")
    # predictions
    C = [p for p in GROUPS["C"] if p in Da.index]; p1 = [p for p in C if above(Da.loc[p])[0]]
    p2 = {}
    for p in ("gore", "doom-scheme"):
        if p in Da.index and p in Dn.index: p2[p] = bool(Da.loc[p, "cross"] > Da.loc[p, "null_function_hi"] and above(Da.loc[p])[0] and Dn.loc[p, "cross"] > Dn.loc[p, "null_function_hi"])
        else: p2[p] = None
    ctrl = [p for p in GROUPS["U"] + GROUPS["R"] if p in Da.index]; p3 = [p for p in ctrl if above(Da.loc[p])[0]]
    four = ["mochadoom", "kocoa-doom", "managed-doom", "doomf77"]; p4 = {p: (above(Da.loc[p])[0] if p in Da.index else None) for p in four}
    gates = {}
    for p in four:
        x = df[(df.program == p) & (df.arm == "D") & (df.gamma == 1.0) & (df.subset == "all")]
        gates[p] = None if not len(x) else bool(x.iloc[0]["coverage"] >= 0.5 and x.iloc[0]["populated"] >= 10 and x.iloc[0]["n_name_and_path"] >= 50)
    both = [p for p in arms["D"].index if p in arms["H3"].index]; mt = [p for p in both if GROUP_OF.get(p) in ("M", "T")]
    r5 = spearmanr([arms["D"].loc[p, "z_function"] for p in both], [arms["H3"].loc[p, "z_function"] for p in both]).statistic if len(both) > 3 else float("nan")
    r5b = spearmanr([arms["D"].loc[p, "z_function"] for p in mt], [arms["H3"].loc[p, "z_function"] for p in mt]).statistic if len(mt) > 3 else float("nan")
    Mnt = [p for p in GROUPS["M"] if p in Dn.index]; p6 = [p for p in Mnt if Dn.loc[p, "cross"] > Dn.loc[p, "null_file_hi" if Dn.loc[p].get("null_file_n", 0) > 0 and np.isfinite(Dn.loc[p].get("null_file_hi", np.nan)) else "null_function_hi"]]
    g_ = {gm: sc[(sc.arm == "D") & (sc.gamma == gm) & (sc.subset == "all")].set_index("program") for gm in (0.5, 1.0, 2.0)}
    def rho(a, b):
        ix = [p for p in g_[a].index if p in g_[b].index]; return (spearmanr([g_[a].loc[p, "z_function"] for p in ix], [g_[b].loc[p, "z_function"] for p in ix]).statistic if len(ix) > 3 else float("nan")), len(ix)
    r05, n05 = rho(0.5, 1.0); r2, n2 = rho(2.0, 1.0)
    status = lambda gm: {p: p in g_[gm].index for g in "CTU" for p in GROUPS[g]}; same = status(0.5) == status(1.0) == status(2.0)
    T += ["", "## Predictions", "", "| prediction | result | value |", "|---|---|---|",
          f"| P1 pipeline sanity: scored close copies above every defined null | {'met' if C and len(p1) == len(C) else 'NOT met'} | {len(p1)} of {len(C)} scored: {p1} |",
          f"| P2 gore and doom-scheme above function and file nulls and on non-twin placements | {'met' if all(v for v in p2.values() if v is not None) and any(v for v in p2.values()) else 'NOT met or untestable'} | {p2} |",
          f"| P3 at most one scored U or R program above the file null | {'met' if len(p3) <= 1 else 'NOT met'} | {len(p3)} of {len(ctrl)} scored: {p3} |",
          f"| P4 none of the four zeros scored above the file null (falsifier) | {'not falsified' if not any(v for v in p4.values() if v is not None) else 'FALSIFIED'} | above: {p4}; sufficiency gates passed: {gates} |",
          f"| P5 D vs H3 rank agreement at least 0.8 (all; within M and T) | {'met' if r5 >= 0.8 and r5b >= 0.8 else 'NOT met'} | rho {f(float(r5))} (n {len(both)}); M and T rho {f(float(r5b))} (n {len(mt)}) |",
          f"| P6 at least four scored M programs above the file null on non-twin placements | {'met' if len(p6) >= 4 else 'NOT met'} | {len(p6)} of {len(Mnt)}: {p6} |",
          f"| P7 rank agreement across resolutions at least 0.8 and scored status of C, T, U unchanged | {'met' if r05 >= 0.8 and r2 >= 0.8 and same else 'NOT met'} | rho 0.5 vs 1.0 {f(float(r05))} (n {n05}); 2.0 vs 1.0 {f(float(r2))} (n {n2}); status unchanged: {same} |"]
    # group effect sizes
    T += ["", "## Group effect sizes (A12 on the standardised gap against the function shuffle, arm D, all placements)", "", "| pair | A12 | n | n |", "|---|---|---|---|"]
    z = {g: [Da.loc[p, "z_function"] for p in GROUPS[g] if p in Da.index] for g in "CMTRUX"}
    for a_, b_ in (("C", "M"), ("M", "T"), ("T", "U"), ("T", "R")): T.append(f"| {a_} against {b_} | {f(a12(z[a_], z[b_]))} | {len(z[a_])} | {len(z[b_])} |")
    (OUT / "E11_STAGE4_RESULTS.md").write_text("\n".join(T) + "\n"); print("\n".join(T))

def main(smoke=False):
    arms = build_arms(); names = [p for g in ("C", "M", "T", "R", "K", "U", "X") for p in GROUPS[g] if table(p) is not None]
    rec = recovery(arms)
    if smoke: names, nd = ["chocolate-doom", "gore", "lua"], 20
    else: nd = NDRAW
    t0 = time.time(); rows = []
    with ProcessPoolExecutor(3) as ex:
        for res in ex.map(run_program, [(n, arms, nd) for n in names]):
            rows += res; print(res[0]["program"], "done", f"{time.time() - t0:.0f}s", flush=True)
    suf = "_smoke" if smoke else ""
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("program", "group", "arm", "gamma", "subset", "status"), k))
    with open(OUT / f"stage4_table{suf}.csv", "w", newline="") as f: w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    with open(OUT / f"stage4_recovery{suf}.csv", "w", newline="") as f: w = csv.DictWriter(f, fieldnames=list(rec[0].keys())); w.writeheader(); w.writerows(rec)
    if not smoke: report(rows, rec)
    return rows

if __name__ == "__main__":
    main(smoke="--smoke" in sys.argv)
