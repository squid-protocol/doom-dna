"""E14 confirmatory sample draw (seed 20261128): reference functions reached by >=5 demos, matched to both prboom-plus and managed-doom by the E12 ladder, with >=3 mutation sites, not in the pilot.
Strata by whether the matcher's managed-doom target carries the same name as the reference function ("agree") or a different name although a same-named function exists in managed-doom ("disagree"; the matcher's tier does not track this, e.g. P_NewChaseDir -> PlayerThink at tier xtwin). 15 per stratum. Writes sample.json."""
import csv, json, random, re, sys
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); sys.path.insert(0, str(H.parent / "difflocalize"))
import sites as S, mutate
sys.argv = sys.argv[:1]
import pilot_run as P
reach = json.load(open(H / "reach.json")); pairs = list(csv.DictReader(open(H / "pilot_pairs.csv"))); pilot = {x[1] for x in P.PILOT}
md_funcs = {}
for f in sorted(P.MD_SRC.glob("*.cs")):
    for n in S.functions(f.read_text()): md_funcs.setdefault(n, f.stem)
def oracle(name):
    n = re.sub(r"^(EV_|P_|A_|T_|PIT_|PTR_)", "", name)
    return (n, md_funcs[n]) if n in md_funcs else None
cands = {"agree": [], "disagree": []}
for x in pairs:
    rp = x["ref_path"].replace("\\", "/")
    m = re.match(r"src/doom/(p_\w+)\.c$", rp)
    if not m or m.group(1) not in mutate.FILES or x["ref_name"] in pilot or len(reach.get(x["ref_name"], [])) < 5: continue
    if not x["pb_path"].endswith(".c") or not x["md_path"].endswith(".cs"): continue
    t = (mutate.SRCDIR / f"{m.group(1)}.c").read_text(); fs = S.functions(t)
    if x["ref_name"] not in fs or len(S.sites(t, fs[x["ref_name"]])) < 3: continue
    pbf = Path(x["pb_path"]).stem; mdf = Path(x["md_path"]).stem
    if not (P.PB_SRC / f"{pbf}.c").exists() or not (P.MD_SRC / f"{mdf}.cs").exists(): continue
    o = oracle(x["ref_name"])
    if not o: continue
    stratum = "agree" if x["md_name"] == o[0] else "disagree"
    cands[stratum].append(dict(ref=x["ref_name"], ref_file=m.group(1), ref_reach=len(reach[x["ref_name"]]), pb=x["pb_name"], pb_file=pbf, pb_tier=x["pb_tier"], md=x["md_name"], md_file=mdf, md_tier=x["md_tier"], md_oracle=o[0] if o else None, md_oracle_file=o[1] if o else None))
rng = random.Random(20261128); out = {}
for k, v in cands.items(): print(k, "candidates", len(v)); rng.shuffle(v); out[k] = sorted(v[:15], key=lambda d: d["ref"])
json.dump(out, open(H / "sample.json", "w"), indent=1)
for k in out: print(k, [d["ref"] + ("" if d["md"] == d["ref"].split("_", 1)[-1] else f'->{d["md"]}') for d in out[k]])
