"""E14: which linuxdoom functions are matched (name-blind, E12 ladder) in every panel port? Output: conserved.csv
Run: e11 venv python, from anywhere."""
import sys, json, csv
from pathlib import Path
SE = "/srv/storage_16tb/projects/doom-dna-worktrees/gene-view/followups/seed-and-extend"
sys.path.insert(0, SE)
import build_subsystem_map_ladder as B
L = B.L
PANEL = ["chocolate-doom", "crispy-doom", "prboom-plus", "doomgeneric", "sdl-doom", "inter-doom", "doom-ascii"]
REF = "linuxdoom"
tl = L.tables(REF, "P")[0]
print("columns:", [c for c in dir(tl) if not c.startswith("_")][:40])
per = {}
for p in PANEL:
    tp = L.tables(p, "P")[0]; m, gate = B.ref_matches(p, REF, tp, tl)
    per[p] = (tp, m); print(p, "matched", len(m or {}))
import collections
cnt = collections.defaultdict(dict)
for p, (tp, m) in per.items():
    for a, (b, tier, s) in (m or {}).items(): cnt[b][p] = (a, tier, s)
out = []
for b, d in cnt.items():
    out.append((len(d), min(("exact", "twin", "xtwin", "seed", "ext1", "ext2", "ext3").index(t[1]) for t in d.values()), b, d))
out.sort(key=lambda x: (-x[0], x[1]))
with open("conserved_raw.json", "w") as f:
    json.dump([[n, w, int(b), {p: [int(a), t, float(s)] for p, (a, t, s) in d.items()}] for n, w, b, d in out], f)
print("functions matched in all", len(PANEL), ":", sum(1 for x in out if x[0] == len(PANEL)), " >=5:", sum(1 for x in out if x[0] >= 5))
names = {p: per[p][0] for p in PANEL}
with open("conserved.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ref_name", "ref_path", "ref_loc", "n_ports", "worst_tier"] + [x for p in PANEL for x in (p + ":name", p + ":path", p + ":tier")])
    for n, wt, b, d in out:
        row = [tl.name[b], tl.path[b], tl.loc[b], n, wt]
        for p in PANEL:
            if p in d: a, t, s = d[p]; row += [names[p].name[a], names[p].path[a], t]
            else: row += ["", "", ""]
        w.writerow(row)
