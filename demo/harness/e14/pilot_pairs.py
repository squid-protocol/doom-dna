"""E14 phase 0: matched functions chocolate-doom -> prboom-plus and managed-doom (E12 ladder; F0 then F1c, one-to-one). Writes pilot_pairs.csv"""
import sys, csv
SE = "/srv/storage_16tb/projects/doom-dna-worktrees/gene-view/followups/seed-and-extend"; sys.path.insert(0, SE)
import build_subsystem_map_ladder as B
L = B.L; REF = "chocolate-doom"; tl = L.tables(REF, "P")[0]; res = {}
for p in ("prboom-plus", "managed-doom"):
    tp = L.tables(p, "P")[0]
    # ref_matches maps port row -> ref row for ref==REF
    m, gate = B.ref_matches(p, REF, tp, tl); res[p] = (tp, m); print(p, "matched", len(m or {}), "gate", gate and gate.get("passes"))
inv = {p: {b: (a, t, s) for a, (b, t, s) in (m or {}).items()} for p, (tp, m) in res.items()}
with open("pilot_pairs.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ref_name", "ref_path", "ref_loc", "pb_name", "pb_path", "pb_tier", "pb_score", "md_name", "md_path", "md_tier", "md_score"])
    for b in sorted(set(inv["prboom-plus"]) & set(inv["managed-doom"])):
        pa, pt, ps = inv["prboom-plus"][b]; ma, mt, ms = inv["managed-doom"][b]; tpb = res["prboom-plus"][0]; tmd = res["managed-doom"][0]
        w.writerow([tl.name[b], tl.path[b], tl.loc[b], tpb.name[pa], tpb.path[pa], pt, round(ps, 3), tmd.name[ma], tmd.path[ma], mt, round(ms, 3)])
print("in both:", len(set(inv["prboom-plus"]) & set(inv["managed-doom"])))
