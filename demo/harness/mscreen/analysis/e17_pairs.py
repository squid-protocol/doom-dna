"""E17 helper: E12 structural matches Mocha Doom -> chocolate-doom (one-to-one across tiers), as a CSV (same logic as demo/harness/e14/pilot_pairs.py).
Reads only the E12 gene-view match files and scanner tables, never a screen store. Usage: python e17_pairs.py <out.csv>  (e11 venv python)"""
import csv, sys
SE = "/srv/storage_16tb/projects/doom-dna-worktrees/gene-view/followups/seed-and-extend"
def main(out, port="mochadoom", ref="chocolate-doom"):
    sys.path.insert(0, SE); import build_subsystem_map_ladder as B
    L = B.L; tl = L.tables(ref, "P")[0]; tp = L.tables(port, "P")[0]; m, gate = B.ref_matches(port, ref, tp, tl)
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["ref_name", "ref_path", "ref_loc", "port_name", "port_path", "port_loc", "tier", "score"])
        for a, (b, t, s) in sorted((m or {}).items(), key=lambda kv: kv[1][0]): w.writerow([tl.name[b], tl.path[b], tl.loc[b], tp.name[a], tp.path[a], tp.loc[a], t, round(s, 4)])
    print(port, "matched", len(m or {}), "gate", gate and gate.get("passes"))
if __name__ == "__main__": main(sys.argv[1])
