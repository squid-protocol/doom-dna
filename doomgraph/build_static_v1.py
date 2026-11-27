#!/usr/bin/env python3
"""Build DoomGraph v1 (E18 amendment A1): copy the v0 static database (all v0 rows stay intact) to doomgraph_static_v1.sqlite and add the multi-anchor
consensus runs as new build scopes 'v1' (five joint anchors) and the two pre-fixed anchor-swap runs.  Static evidence only (match edges, call edges,
lineage already stored in the v0 static file); never opens the behaviour database, phenotypes, reach or Mocha/gore data.

    nice -n 10 python3 doomgraph/build_static_v1.py [--src PATH] [--out PATH]   (requires build_static.py output first; see doomgraph/README.md)"""
import argparse, collections, datetime, json, shutil, sqlite3, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
from groups_v1 import build_groups_v1
import audit as AU
import build_static as BS      # installs the sqlite3 open-guard (behaviour / phenotype / screen / jv_v2 / go_v2 refused)

def add_run(db, scope, anchors, insts, edges, calls, parent, build_id, gid_start):
    res = build_groups_v1(insts, edges, calls, parent, anchors, C.CONTROL_PORTS)
    gmap = {g: gid_start + k + 1 for k, g in enumerate(res["anchors"])}
    mem_rows = []; cnt = collections.defaultdict(lambda: [0, set()])
    for x, rows in sorted(res["members"].items()):
        for r in rows:
            mem_rows.append((x, gmap[r["group"]], scope, r["rank"], r["role"], r["confidence"], r["evidence"], build_id))
            if r["rank"] == 1: cnt[r["group"]][0] += 1; cnt[r["group"]][1].add(insts[x]["port"])
    db.executemany("insert into ortholog_group values (?,?,?,?,?,?,?,?)",
                   [(gmap[g], scope, g, "consensus_v1:" + "+".join(anchors), C.GROUP_VERSION_V1, cnt[g][0], len(cnt[g][1]), build_id) for g in res["anchors"]])
    db.executemany("insert into membership values (?,?,?,?,?,?,?,?)", mem_rows)
    db.executemany("insert into ungrouped values (?,?,?,?)", [(x, scope, why, build_id) for x, why in sorted(res["ungrouped"].items())])
    print(scope, "groups", len(res["anchors"]), "grouped", len(res["members"]), "ungrouped", len(res["ungrouped"]), flush=True)
    return gid_start + len(res["anchors"])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--src", default=str(C.STATIC_DB)); ap.add_argument("--out", default=str(C.STATIC_V1_DB))
    a = ap.parse_args(); t0 = time.time(); out = Path(a.out)
    if out.exists(): out.unlink()
    shutil.copyfile(a.src, out)
    db = sqlite3.connect(str(out))
    build_id = "dg-v1-" + datetime.date.today().isoformat()
    insts, edges, calls, parent = AU.load_inputs(db)
    gid = db.execute("select coalesce(max(group_id),0) from ortholog_group").fetchone()[0]
    runs = [("v1", C.V1_ANCHORS)] + list(C.V1_SWAPS.items())
    for scope, anchors in runs: gid = add_run(db, scope, anchors, insts, edges, calls, parent, build_id, gid)
    man = dict(C.git_info()); man.update(v1_build_id=build_id, v1_group_version=C.GROUP_VERSION_V1, v1_anchors=",".join(C.V1_ANCHORS),
        v1_swap_runs=json.dumps(C.V1_SWAPS), v1_source_static=Path(a.src).name, v1_source_static_sha256=C.sha256_file(a.src),
        v1_constants=json.dumps(dict(tier_w=C.TIER_W, name_w=C.NAME_W, arb_w=C.ARB_W, arb_bonus=C.ARB_BONUS, min_join=C.MIN_JOIN, conflict_margin=C.CONFLICT_MARGIN, hop2=C.HOP2_FACTOR)),
        v1_seeds="none (deterministic; no random draws)", v1_opened_databases=json.dumps(sorted({Path(p.split("?")[0]).name for p in BS.OPENED})))
    for k, v in man.items():
        db.execute("insert or replace into build_manifest values (?,?)", (k if k.startswith("v1_") else "v1_" + k, v))
    db.commit(); BS.check_allowlist(db); db.close()
    print(f"built {out} in {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
