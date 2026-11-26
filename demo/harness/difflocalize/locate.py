"""DOOM-E13 differential localisation (tier 1): from two engines' deterministic runs, find where behaviour first diverges and which functions to suspect.
Inputs per engine: a per-tic digest and a gameplay-RNG caller trace ("gametic caller prndindex" per call; see E13_TRACE_BUILD).
Steps: (1) first diverging tic and field; (2) first tic whose RNG-caller sequence differs, and the callers present in only one engine (the symptom functions);
(3) suspects = the symptom functions plus their static callee closure (from the scanner's call graph) up to a depth; (4) a fixed field-to-function-family prior when there is no RNG difference."""
import collections, json, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); import compare_digests as C

def norm(name): return name.lower().replace("_", "")

def load_trace(path):
    d = collections.defaultdict(list)
    try:
        for l in open(path):
            p = l.split()
            if len(p) == 3: d[int(p[0])].append(norm(p[1]))
    except FileNotFoundError: pass
    return d

def rng_first_diff(ref_trace, subj_trace):
    """first gametic whose caller list differs -> (gametic, ref_only, subj_only, ref_calls, subj_calls) or None"""
    for t in sorted(set(ref_trace) | set(subj_trace)):
        a, b = ref_trace.get(t, []), subj_trace.get(t, [])
        if a != b:
            ca, cb = collections.Counter(a), collections.Counter(b)
            ref_only = [k for k in (ca - cb)]; subj_only = [k for k in (cb - ca)]
            if not ref_only and not subj_only:  # same multiset, different order: report the first position that differs
                i = next(i for i in range(min(len(a), len(b))) if a[i] != b[i]); ref_only, subj_only = [a[i]], [b[i]]
            return t, ref_only, subj_only, a, b
    return None

class CallGraph:
    """static call graph from a scanner database (function_data.calls_out_to), names normalised"""
    def __init__(self, db_path):
        c = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.callees = collections.defaultdict(set); self.callers = collections.defaultdict(set); self.names = {}; self.where = {}
        for name, calls, path, line in c.execute("select f.func_name, f.calls_out_to, fi.file_path, f.start_line from function_data f join file_data fi on fi.id=f.file_id"):
            n = norm(name); self.names[n] = name; self.where.setdefault(n, (path, line))
            try:
                for x in json.loads(calls or "[]"): self.callees[n].add(norm(x))
            except Exception: pass
        for f, gs in list(self.callees.items()):
            for g in gs: self.callers[g].add(f)
        self.total = len(self.names)
    def closure(self, starts, depth):
        """{function: shortest depth} reachable from starts within depth (starts at 0), only functions defined in the scan"""
        seen = {s: 0 for s in starts if s in self.names}; frontier = list(seen)
        for d in range(1, depth + 1):
            nxt = []
            for f in frontier:
                for g in self.callees.get(f, ()):
                    if g in self.names and g not in seen: seen[g] = d; nxt.append(g)
            frontier = nxt
        return seen
    def closure_with_callers(self, starts, depth, up=2):
        """variant B: also seed with the callers of the symptom functions (up to `up` levels), then take the callee closure of all seeds"""
        seeds = {s: 0 for s in starts if s in self.names}; frontier = list(seeds)
        for u in range(1, up + 1):
            nxt = []
            for f in frontier:
                for g in self.callers.get(f, ()):
                    if g in self.names and g not in seeds: seeds[g] = u; nxt.append(g)
            frontier = nxt
        out = {}
        for s0, u in seeds.items():
            for g, d in self.closure([s0], depth).items():
                if g not in out or d + u < out[g]: out[g] = d + u
        return out
    def function_at(self, path_suffix, line):
        best = None
        for n, (p, l) in self.where.items():
            if p.endswith(path_suffix) and l <= line and (best is None or l > self.where[best][1]): best = n
        return best

# fixed prior (not tuned on any result): which function family a first-diverging digest field points at
FIELD_FAMILY = {
    "x": ["pxymovement", "ptrymove", "pcheckposition", "pslidemove", "pplayerthink", "pmovement", "pcrossspecialline", "puselines"],
    "y": ["pxymovement", "ptrymove", "pcheckposition", "pslidemove", "pplayerthink", "pmovement", "pcrossspecialline", "puselines"],
    "z": ["pzmovement", "pcheckposition", "pplayerthink", "pmobjthinker"],
    "angle": ["pplayerthink", "pmovement", "pdeaththink", "pcalcheight"],
    "health": ["pdamagemobj", "ptouchspecialthing", "pplayerthink", "pinflictdamage", "psectordamage"],
    "armor": ["pdamagemobj", "ptouchspecialthing", "pgivearmor"],
    "weapon": ["pfireweapon", "pbringupweapon", "pplayerthink", "pmovepsprites", "pchangeweapon", "pcheckammo"],
    "ammo0": ["pfireweapon", "pgiveammo", "ptouchspecialthing", "pcheckammo", "adecreaseammo", "afirepistol"],
    "mobjhash": ["pmobjthinker", "pxymovement", "pdamagemobj", "ptrywalk", "pnewchasedir"],
    "nmobjs": ["pspawnmobj", "pspawnmapthing", "premovemobj", "pkillmobj"],
    "sectorhash": ["tvertical door", "tmoveplane", "pspawnspecials", "pupdatespecials", "evdodoor", "pusespecialline", "tvdoor", "tmovefloor", "tmoveceiling"],
    "cards": ["ptouchspecialthing", "pgivecard"],
    "prndindex": [],
}

def localise(ref_digest, subj_digest, ref_trace_path, subj_trace_path, graph, depth=6, no_prnd=False):
    a, b = C.load(ref_digest), C.load(subj_digest)
    keep = [k for k in C.KEEP if not (no_prnd and k == 2)]
    div = C.first_divergence(a, b, keep) if a and b else None
    out = {"diverges": div is not None, "first_tic": div[0] if div else None, "field": div[1] if div else None}
    if not div: return out
    r = rng_first_diff(load_trace(ref_trace_path), load_trace(subj_trace_path))
    out["rng_diff"] = None
    symptoms = []
    if r:
        t, ro, so, ra, sb = r
        out["rng_diff"] = {"gametic": t, "ref_only": ro, "subject_only": so, "ref_calls": ra[:12], "subject_calls": sb[:12]}
        symptoms = [x for x in dict.fromkeys(ro + so)]
    out["symptoms"] = symptoms
    if symptoms:
        out["suspects"] = graph.closure(symptoms, depth); out["suspects_b"] = graph.closure_with_callers(symptoms, depth)
        out["basis"] = "rng-caller diff"
    else:
        fam = [x for x in FIELD_FAMILY.get(div[1], []) if x in graph.names]
        out["suspects"] = graph.closure(fam, depth) if fam else {}; out["suspects_b"] = graph.closure_with_callers(fam, depth) if fam else {}
        out["basis"] = "field prior" if fam else "none"
    return out
