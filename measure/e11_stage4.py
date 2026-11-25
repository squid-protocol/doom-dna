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
NDRAW, MIN_PLACED, MIN_CROSS, MIN_POP, MIN_FILES, MIN_NAME = 1000, 100, 100, 8, 15, 6
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
    if len(uf) < MIN_FILES: return None
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

def run_program(args):
    name, arms, ndraw = args; rng = np.random.default_rng(abs(hash(name)) % (2 ** 32)); t = table(name); rows = []
    if t is None or t.edges is None or not len(t.edges): return [dict(program=name, group=GROUP_OF.get(name, "?"), status="no call graph")]
    isc = code(t); files = np.array([str(p) for p in t.path]); tw = WORK / "placement" / f"{name}.npz"
    pairs = list(zip(np.load(tw)["pairs_l"].tolist(), np.load(tw)["pairs_p"].tolist())) if tw.exists() else []
    for arm in arms:
        ref, ref_labels, s, rule, names, fb, ref_m = arm["ref"], arm["ref_labels"], arm["s"], arm["rule"], arm["names"], arm["fb"], arm["ref_m"]
        labels, src = place(t, ref, ref_labels, pairs, rule, names, fb); placed = labels >= 0; npl = int(placed.sum())
        m = SW._calls(labels, t.edges, s); cross_calls = int(SW._off_diagonal(m).sum()); pop = int((np.bincount(labels[placed], minlength=s) >= 3).sum()) if npl else 0
        row = dict(program=name, group=GROUP_OF.get(name, "?"), arm=arm["name"], gamma=arm["gamma"], functions=int(isc.sum()), placed=npl, coverage=npl / max(int(isc.sum()), 1),
                   src_twin=int((src == "twin").sum()), src_name=int((src == "name").sum()), src_path=int((src == "path").sum()), cross_calls=cross_calls, populated=pop,
                   files=int(len(np.unique(files[placed]))) if npl else 0, calls_per_function=len(t.edges) / max(int(isc.sum()), 1))
        w, c = cos_pair(m, ref_m); row.update(wiring=w, cross=c, floor=SW.wiring_floor(ref_m)); wl, cl = cos_pair(m, ref_m, log=True); row.update(wiring_log=wl, cross_log=cl)
        # placement quality
        npn, npp = name_only(t, names), path_only(t, rule, fb)
        tw_idx = np.flatnonzero(src == "twin"); both = np.flatnonzero((npn >= 0) & (npp >= 0))
        both_np = (npn[tw_idx] >= 0) | (npp[tw_idx] >= 0)
        try: row["kappa_name_path_vs_twin"] = float(cohen_kappa_score(labels[tw_idx][both_np], np.where(npn[tw_idx] >= 0, npn[tw_idx], npp[tw_idx])[both_np])) if both_np.sum() > 20 else float("nan")
        except Exception: row["kappa_name_path_vs_twin"] = float("nan")
        row["n_name_and_path"] = int(len(both)); row["kappa_name_vs_path"] = float(cohen_kappa_score(npn[both], npp[both])) if len(both) > 20 and len(set(npn[both])) > 1 else float("nan")
        scored = npl >= MIN_PLACED and cross_calls >= MIN_CROSS and pop >= MIN_POP
        row["status"] = "scored" if scored else "not scored (placed %d, cross calls %d, populated %d)" % (npl, cross_calls, pop)
        if scored:
            nl = nulls(labels, t.edges, files, ref_m, s, rng, ndraw)
            for kind, arr in nl.items():
                if len(arr) == 0: row[f"null_{kind}_n"] = 0; continue
                cr = arr[:, 1]; cr = cr[np.isfinite(cr)]
                row.update({f"null_{kind}_n": len(cr), f"null_{kind}_mean": float(cr.mean()), f"null_{kind}_lo": float(np.percentile(cr, 2.5)), f"null_{kind}_hi": float(np.percentile(cr, 97.5)),
                            f"gap_{kind}": c - float(cr.mean()), f"pct_{kind}": float((cr <= c).mean())})
        rows.append(row)
    return rows

def build_arms(gamma_list=(1.0,)):
    import e11_stage2 as S2
    ref = table("linuxdoom"); tax = SW.Taxonomy.load(TAXFILE); arms = []
    hand = np.where(code(ref), [tax.classify(str(x), ref.repo) for x in ref.path], -1).astype(np.int64); fbh = tax.index[tax.fallback]; hand_ref = np.where(hand == fbh, -1, hand)
    for g in gamma_list:
        labs = S2.reference(g)["labs"]; rl = np.full(len(ref), -1, np.int64)
        for r, l in labs.items(): rl[int(r)] = int(l)
        s = int(rl.max()) + 1; rule = DerivedRules(ref, rl); arms.append(dict(name="D", gamma=g, ref=ref, ref_labels=rl, s=s, rule=rule, names=name_index(ref, rl), fb=None, ref_m=SW._calls(rl, ref.edges, s)))
    s = len(tax.subsystems); rule_h1 = DerivedRules(ref, hand_ref); hm = SW._calls(hand_ref, ref.edges, s); nh = name_index(ref, hand_ref)
    arms.append(dict(name="H1", gamma=None, ref=ref, ref_labels=hand_ref, s=s, rule=rule_h1, names=nh, fb=fbh, ref_m=hm))
    arms.append(dict(name="H2", gamma=None, ref=ref, ref_labels=hand_ref, s=s, rule=tax, names=nh, fb=fbh, ref_m=hm))
    return arms

def main(smoke=False):
    arms = build_arms((1.0, 0.5, 2.0)); names = [p for g in ("C", "M", "T", "R", "K", "U", "X") for p in GROUPS[g] if table(p) is not None]
    if smoke: names, nd = ["chocolate-doom", "gore", "lua"], 20
    else: nd = NDRAW
    t0 = time.time(); rows = []
    with ProcessPoolExecutor(3) as ex:
        for res in ex.map(run_program, [(n, arms, nd) for n in names]):
            rows += res; print(res[0]["program"], "done", f"{time.time() - t0:.0f}s", flush=True)
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("program", "group", "arm", "gamma", "status"), k))
    with open(OUT / ("stage4_table_smoke.csv" if smoke else "stage4_table.csv"), "w", newline="") as f: w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    return rows

if __name__ == "__main__":
    main(smoke="--smoke" in sys.argv)
