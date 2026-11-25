"""Export per-port function matches for the interactive function finder.
Tiers (priority order, strict one-to-one across tiers): exact (fingerprint clone), twin (fingerprint twin, E7 setting), xtwin (cross-language fingerprint F1c, registered setting),
seed (top 15% reciprocal graph seeds), ext1/ext2/ext3 (extension by hop, calibrated = the published method). Each pair lists which other tiers found the same pair.
Truth annotation (never used to choose pairs): same-language = text-similarity band from the E9 arbiter (near>=0.9, derived 0.6-0.9, none = not listed, unmapped); translations = function-name agreement; controls = control.
Usage: python finder_export.py [--only a,b]   (writes results/finder/)"""
import sys, json, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import numpy as np, e12_ladder as L
OUT = Path(__file__).resolve().parents[1] / "results" / "finder"; OUT.mkdir(parents=True, exist_ok=True)
PRIO = ["exact", "twin", "xtwin", "seed", "ext1", "ext2", "ext3"]

def export_one(name):
    t0 = time.time(); kind = L.GROUP[name]
    tp, _, _ = L.tables(name, "P"); tl, _, _ = L.tables("linuxdoom", "P")
    ok = lambda a, b: tp.loc[a] >= L.MIN_LOC and tl.loc[b] >= L.MIN_LOC
    fr = L.fingerprint_rungs(name, None); gr, gate = L.graph_rungs(name, np.random.default_rng(0))
    cand = {}  # tier -> list of (a, b, score)
    f0 = [(a, b, s) for a, b, s in fr[("F0", 0.01, 0.8)] if ok(a, b)]; cand["exact"] = [x for x in f0 if x[2] >= 0.999999]; cand["twin"] = [x for x in f0 if x[2] < 0.999999]
    cand["xtwin"] = [(a, b, s) for a, b, s in fr[("F1c", 0.01, 0.8)] if ok(a, b)]
    s_list = [(a, b, s) for a, b, s in gr["S"] if ok(a, b)]; cand["seed"] = s_list
    e3c = gr["E3c"]; h1, h2, h3 = gate["E3c_hop_ends"]; nseed = len(gr["S"])
    cand["ext1"] = [x for x in e3c[nseed:h1] if ok(x[0], x[1])]; cand["ext2"] = [x for x in e3c[h1:h2] if ok(x[0], x[1])]; cand["ext3"] = [x for x in e3c[h2:h3] if ok(x[0], x[1])]
    found = {}
    for tier in PRIO:
        for a, b, s in cand[tier]: found.setdefault((a, b), set()).add(tier)
    used_a, used_b, rows = set(), set(), []
    for tier in PRIO:
        for a, b, s in cand[tier]:
            if a in used_a or b in used_b: continue
            used_a.add(a); used_b.add(b); rows.append((a, b, tier, float(s)))
    if kind in ("SL", "DEV"):
        sets, ph_of, _, _ = L.truth_sets(name); ld_h = L.truth()["ld_hash"]
        def truth(a, b):
            hp, hr = ph_of.get(a), ld_h.get(b)
            if hp is None or hr is None: return "unmapped"
            return "near" if (hp, hr) in sets["j09"] else ("derived" if (hp, hr) in sets["j06"] else "none")
    elif kind == "T":
        def truth(a, b):
            x, y = L.N.name_key(str(tp.name[a])), L.N.name_key(str(tl.name[b])); return "name-match" if (x and x == y and x not in L.STOP) else "no-name-match"
    else:
        def truth(a, b): return "control"
    pairs = [[str(tp.name[a]), str(tp.path[a]), int(tp.loc[a]), str(tl.name[b]), str(tl.path[b]), int(tl.loc[b]), tier, round(s, 4), sorted(found[(a, b)] - {tier}, key=PRIO.index), truth(a, b)] for a, b, tier, s in rows]
    counts = {t: sum(1 for r in pairs if r[6] == t) for t in PRIO}
    res = dict(port=name, group=kind, eligible=int((tp.loc >= L.MIN_LOC).sum()), gate=dict(passes=gate["passes"], strong_fgw=round(gate["strong_fgw"], 3), mean_sup=round(gate["mean_sup"], 3)), tier_counts=counts, pairs=pairs)
    json.dump(res, open(OUT / f"{name}.json", "w"), separators=(",", ":")); print(name, len(pairs), counts, f"{time.time() - t0:.0f}s", flush=True); return name

def main():
    only = None
    if "--only" in sys.argv: only = sys.argv[sys.argv.index("--only") + 1].split(",")
    names = only or (L.DEV + L.SL + L.TR + L.CTRL + L.HELD)
    with ProcessPoolExecutor(min(6, len(names))) as ex: list(ex.map(export_one, names))
    if only: return
    idx, pooled = [], {}
    for n in names:
        d = json.load(open(OUT / f"{n}.json")); idx.append(dict(port=n, group=d["group"], eligible=d["eligible"], gate=d["gate"], tier_counts=d["tier_counts"], matched=len(d["pairs"])))
        for r in d["pairs"]:
            k = (d["group"], r[6], r[9]); pooled[k] = pooled.get(k, 0) + 1
    tab = {}
    for (g, tier, tr), c in pooled.items(): tab.setdefault(g, {}).setdefault(tier, {})[tr] = c
    json.dump(dict(ports=idx, tier_truth_by_group=tab, tiers=PRIO, note="Truth columns are checks, never used to choose pairs. See README_FINDER_DATA.md. SL/DEV: near/derived/none/unmapped = text-similarity band (none means not listed, not proven wrong). T: name agreement (lower bound). Controls: every pair is unrelated."), open(OUT / "index.json", "w"), separators=(",", ":"))
    print("index written", len(idx))
if __name__ == "__main__": main()
