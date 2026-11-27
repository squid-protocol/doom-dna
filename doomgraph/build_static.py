#!/usr/bin/env python3
"""Build doomgraph_static.sqlite: instances, match edges (E12 pair files, name-agree, E7 text arbiter), call edges (G1, G2), lineage edges,
subsystem placement, ortholog groups.  Static evidence only: this process never opens the behaviour database or any phenotype/reach store
(a guard on sqlite3.connect refuses such paths).

    nice -n 10 python3 doomgraph/build_static.py [--out PATH] [--ports a,b,...]   (rebuild: see doomgraph/README.md)"""
import argparse, collections, csv, datetime, glob, json, re, sqlite3, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
from groups import build_groups

_real_connect = sqlite3.connect
OPENED = []
def _guarded_connect(database, *a, **k):
    s = str(database); OPENED.append(s)
    if any(w in s for w in ("behaviour", "phenotype", "/screen/", "jv_v2", "go_v2")):
        raise PermissionError(f"static build must not open {s}")
    return _real_connect(database, *a, **k)
sqlite3.connect = _guarded_connect

def scan_db(name):
    return C.SCAN_ROOT / name / f"{name}_galaxy_master.db"

def load_instances(name):
    """rows of the E12 function table (fid space): scan functions (synthetic buckets dropped) with >= 3 lines, in scan order"""
    synth = {"__global_context__", "__module__", "__file_scope__"}
    c = sqlite3.connect(f"file:{scan_db(name)}?mode=ro", uri=True)
    files = {r[0]: (r[1] or "", str(r[2] or "unknown").lower()) for r in c.execute("select id, coalesce(file_path, file_name, ''), language from file_data order by id")}
    rows = []
    for r in c.execute("select id, file_id, coalesce(func_name,''), coalesce(loc,0), start_line, coalesce(args,0), coalesce(complexity,0) from function_data order by id"):
        if r[2] in synth or r[1] not in files: continue
        rows.append(r)
    commit = (c.execute("select commit_hash from repo_data limit 1").fetchone() or [None])[0]
    scanned = len(rows)
    rows = [r for r in rows if r[3] >= C.MIN_LOC_SCAN]
    dbid2fid = {r[0]: i for i, r in enumerate(rows)}
    calls = []
    for s, d, k in c.execute("select src_func_id, dst_func_id, coalesce(kind,'call') from fcall_data where src_func_id is not null and dst_func_id is not null"):
        if s in dbid2fid and d in dbid2fid and s != d: calls.append((dbid2fid[s], dbid2fid[d], k))
    c.close()
    inst = [dict(fid=i, name=r[2], file=files[r[1]][0], line=r[4], size=r[3], args=r[5], cx=r[6], lang=files[r[1]][1]) for i, r in enumerate(rows)]
    return inst, calls, commit, scanned

def pair_files(only=None):
    out = []
    for f in sorted(C.GENE_VIEW.glob("*__*.json")):
        d = json.loads(f.read_text())
        if "skipped" in d: continue
        if only and d["port"] not in only and d["ref"] not in only: continue
        out.append((f, d))
    return out

def arbiter_rows(port):
    f = C.WT / "e7-three-trees/results/e7/phaseA/arbiter" / f"arbiter_{port}.csv"
    if not f.exists(): return f, []
    return f, list(csv.DictReader(open(f)))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(C.STATIC_DB)); ap.add_argument("--ports", default="")
    a = ap.parse_args(); only = set(filter(None, a.ports.split(",")))
    t0 = time.time(); out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists(): out.unlink()
    build_id = "dg-v0-" + datetime.date.today().isoformat()
    pfs = pair_files(only or None)
    ports = sorted({d["port"] for _, d in pfs} | {d["ref"] for _, d in pfs} | {C.ANCHOR})
    db = _real_connect(str(out)); db.executescript(C.STATIC_DDL)
    man = {}
    man.update(C.git_info()); man.update(schema_version=C.SCHEMA_VERSION, group_version=C.GROUP_VERSION, build_id=build_id,
        built_at=datetime.datetime.now().isoformat(timespec="seconds"), scan_engine=C.SCAN_ROOT.name, anchor=C.ANCHOR, swap_anchor=C.SWAP_ANCHOR,
        name_prefix_rule=C.PREFIX.pattern, name_generic_excluded=",".join(sorted(C.GENERIC)), min_loc_scan=str(C.MIN_LOC_SCAN), min_loc_edge=str(C.MIN_LOC_EDGE),
        tier_weights=json.dumps(C.TIER_W), name_weight=str(C.NAME_W), arbiter_weights=json.dumps(C.ARB_W), arbiter_bonus=str(C.ARB_BONUS), hop2_factor=str(C.HOP2_FACTOR),
        min_join=str(C.MIN_JOIN), conflict_margin=str(C.CONFLICT_MARGIN), control_ports=",".join(C.CONTROL_PORTS), seeds="none (group construction is deterministic; no random draws)",
        sfs_commit=C.git_info("/srv/storage_16tb/projects/structural-fingerprint-scanner")["code_commit"])
    for n, p in (("e7_commit", "e7-three-trees"), ("e8b_commit", "e8b-progenitor"), ("subsystem_map_commit", "subsystem-map"), ("gene_view_commit", "gene-view")):
        man[n] = C.git_info(C.WT / p)["code_commit"]
    # ---- instances
    inst_rows, key2inst, byport, calls_by_port = [], {}, {}, {}
    iid = 0; portrows = []
    for pname in ports:
        inst, calls, commit, scanned = load_instances(pname)
        langs = collections.Counter(i["lang"] for i in inst); lang = langs.most_common(1)[0][0] if langs else None
        dig = C.sha1_short(json.dumps([[i["name"], i["file"], i["size"], i["line"]] for i in inst]))
        sha = C.sha256_file(scan_db(pname)); man[f"scan_sha256:{pname}"] = sha
        kind = "anchor" if pname == C.ANCHOR else ("control" if pname in C.CONTROL_PORTS else ("reference" if pname in C.REF_ENGINES else "port"))
        portrows.append((len(portrows) + 1, pname, lang, kind, f"{C.SCAN_ROOT.name}/{pname}", commit, C.SCAN_ROOT.name, sha, dig, scanned, len(inst), "scan", build_id))
        pid = len(portrows); ids = []
        for i in inst:
            iid += 1; ids.append(iid)
            sig = f"{i['args']}"
            key = C.sha1_short(f"{pname}|{i['file']}|{i['name']}|{sig}")
            inst_rows.append((iid, pid, i["fid"], key, i["name"], i["file"], i["line"], i["size"], i["args"], i["cx"], i["lang"], "scan", build_id))
        byport[pname] = dict(ids=ids, inst=inst, pid=pid)
        calls_by_port[pname] = calls
        print(f"{pname}: {len(inst)} instances ({scanned} scanned)", flush=True)
    db.executemany("insert into port values (?,?,?,?,?,?,?,?,?,?,?,?,?)", portrows)
    db.executemany("insert into instance values (?,?,?,?,?,?,?,?,?,?,?,?,?)", inst_rows)
    fid2inst = lambda p, f: byport[p]["ids"][f]
    # ---- E12 match edges
    medges = {}; nbad = 0
    for f, d in pfs:
        P, R = d["port"], d["ref"]; gate = int(bool(d["gate"]["passes"])); man[f"pairfile_sha256:{f.name}"] = C.sha256_file(f)
        lists = [("F0", d["F0"]), ("F1c", d["F1c"]), ("S", d["S"]), ("ext", d["ext"])]
        for tier, ents in lists:
            for e in ents:
                x, y, s = e[0], e[1], e[2]
                t = tier if tier != "ext" else f"ext{e[3]}"
                if x >= len(byport[P]["ids"]) or y >= len(byport[R]["ids"]): nbad += 1; continue
                ia, ib = fid2inst(P, x), fid2inst(R, y); a_, b_ = (ia, ib) if ia < ib else (ib, ia)
                medges[(a_, b_, t, "e12")] = (s, f.stem, gate, None, C.sha1_short(f"{f.stem}|{x}|{y}|{t}|{s}"))
    man["pair_entries_out_of_range"] = str(nbad)
    # ---- name-agree edges (unique stripped name in both ports; refs only, as the E12 pair files)
    def uniq_names(p):
        cnt = collections.Counter(C.strip_name(i["name"]) for i in byport[p]["inst"])
        return {C.strip_name(i["name"]): fid2inst(p, i["fid"]) for i in byport[p]["inst"]
                if cnt[C.strip_name(i["name"])] == 1 and C.strip_name(i["name"]) and C.strip_name(i["name"]).lower() not in C.GENERIC}
    un = {p: uniq_names(p) for p in ports if p not in C.CONTROL_PORTS}
    done = set()
    for p in sorted(un):
        for r in C.REF_ENGINES:
            if r == p or r not in un: continue
            k = tuple(sorted((p, r)))
            if k in done: continue
            done.add(k)
            for nm, ia in un[p].items():
                ib = un[r].get(nm)
                if ib is not None:
                    a_, b_ = (ia, ib) if ia < ib else (ib, ia)
                    medges[(a_, b_, "NAME", "name")] = (1.0, f"{k[0]}__{k[1]}", None, None, C.sha1_short(f"{k}|{nm}"))
    # ---- E7 text arbiter (verdict, similarity and a row hash only; no rationale, no snippets)
    ld = byport[C.ANCHOR]["inst"]; ldkey = {(i["file"], i["name"], i["line"]): fid2inst(C.ANCHOR, i["fid"]) for i in ld}
    arb_hash = []; narb = narb_ok = narb_amb = narb_noref = 0
    for p in ports:
        if p == C.ANCHOR: continue
        f, rows = arbiter_rows(p)
        if not rows: continue
        arb_hash.append(C.sha256_file(f)); man[f"arbiter_sha256:{p}"] = arb_hash[-1]
        pk = collections.defaultdict(list)
        for i in byport[p]["inst"]: pk[(i["file"], i["name"])].append(fid2inst(p, i["fid"]))
        for r in rows:
            if r["verdict"] not in C.ARB_W: continue
            narb += 1
            ra = ldkey.get((r["ref_file"], r["ref_func"], int(r["ref_start_line"]) if r["ref_start_line"] else None))
            if ra is None: narb_noref += 1; continue
            cands = pk.get((r["port_file"], r["port_func"]), [])
            if len(cands) != 1: narb_amb += 1; continue
            narb_ok += 1; ia, ib = ra, cands[0]; a_, b_ = (ia, ib) if ia < ib else (ib, ia)
            medges[(a_, b_, "TXT", "e7_arbiter")] = (float(r["sim"]), f.stem, None, r["verdict"], C.sha1_short("|".join([r["verdict"], r["sim"], str(ra), str(cands[0])])))
    man.update(arbiter_rows_confirming=str(narb), arbiter_edges=str(narb_ok), arbiter_ref_unmapped=str(narb_noref), arbiter_port_ambiguous_or_missing=str(narb_amb))
    db.executemany("insert into match_edge(a_inst,b_inst,tier,score,source,pair_file,gate_passed,verdict,evidence_hash,build_id) values (?,?,?,?,?,?,?,?,?,?)",
        [(k[0], k[1], k[2], v[0], k[3], v[1], v[2], v[3], v[4], build_id) for k, v in sorted(medges.items())])
    # ---- call edges: G1 (scanner resolved calls) and G2 (state-table dispatch)
    cedges = {}
    for p in ports:
        for s, d, k in calls_by_port[p]: cedges[(fid2inst(p, s), fid2inst(p, d), "call" if k == "call" else "reference", "g1")] = 1
    sys.path.insert(0, str(C.REPO / "demo/harness/mscreen/analysis"))
    import graphs as GR
    norm = GR.norm
    g2 = {"chocolate-doom": GR.g2_chocolate(), "prboom-plus": GR.g2_chocolate(), "managed-doom": GR.g2_managed()}
    g2skip = 0
    for p, es in g2.items():
        if p not in byport: continue
        nm = collections.defaultdict(list)
        for i in byport[p]["inst"]: nm[norm(i["name"])].append(i)
        def pick(n):
            c = nm.get(n, [])
            if len(c) > 1: c = [i for i in c if "/doom/" in "/" + i["file"].lower() and "/info/" not in i["file"].lower()] or c   # C: src/doom; C#: implementation, not the Info wrapper
            return fid2inst(p, c[0]["fid"]) if len(c) == 1 else None
        for act, disp in sorted(es):
            x, y = pick(act), pick(disp)
            if x is None or y is None: g2skip += 1; continue
            cedges[(y, x, "dispatch", "g2")] = 1          # dispatcher -> action function
    man["g2_edges_unmapped"] = str(g2skip)
    db.executemany("insert into call_edge(caller_inst,callee_inst,kind,source,build_id) values (?,?,?,?,?)", [(k[0], k[1], k[2], k[3], build_id) for k in sorted(cedges)])
    # ---- lineage edges
    lin_rows = []; parent = {}
    e7 = C.WT / "e7-three-trees/manifest/declared_lineage_basis.csv"
    for r in csv.DictReader(open(e7)):
        lin_rows.append((r["name"], r["parent"], "port", r["basis"], None, None, None, None, "e7_declared_lineage_basis", man["e7_commit"], build_id))
        if r["basis"] in ("explicit", "inferred", "collapsed") and r["name"] not in parent: parent[r["name"]] = r["parent"]
    rank = {(r["port"], r["ref_name"]): r for r in csv.DictReader(open(C.WT / "e8b-progenitor/results/e8b/analysis/h8b3_ranking.csv"))}
    for r in csv.DictReader(open(C.WT / "e8b-progenitor/manifest/e8b_pins.csv")):
        role = r["role"]
        found = [(m.group(1), m.group(2)) for m in re.finditer(r"(primary|secondary): ([\w-]+)", role)]
        if not found and role.startswith("descriptive"): found = [("descriptive", "")]
        for kind, who in found:
            rk = rank.get((who, r["name"]), {})
            lin_rows.append((who or "", r["name"], "external_progenitor", "e8b_pin", kind, float(rk["registered_shared_struct"]) if rk else None,
                             float(rk["registered_shared_names"]) if rk else None, int(rk["rank_struct"]) if rk else None, "e8b_pins", man["e8b_commit"], build_id))
    db.executemany("insert into lineage_edge(port,parent,parent_kind,basis,role,shared_struct,shared_names,rank_struct,source,source_commit,build_id) values (?,?,?,?,?,?,?,?,?,?,?)", lin_rows)
    # ---- subsystem placement (the 16 call-graph subsystems; map placement only, verbatim)
    sm = json.loads((C.WT / "subsystem-map/article/subsystem_map_data.json").read_text()); nsub = collections.Counter(); sub_rows = {}
    for p, pd in sm["ports"].items():
        if p not in byport: continue
        idx = collections.defaultdict(list)
        for i in byport[p]["inst"]: idx[(i["name"], i["size"])].append(i["fid"])
        for sidx, track in enumerate(pd["tracks"], 1):
            for name, loc, _rp, _rn in track:
                c = idx.get((name, loc), [])
                if len(c) == 1: sub_rows[fid2inst(p, c[0])] = (sidx, "map_ref" if _rp else "map_own"); nsub[p] += 1
    db.executemany("insert into subsystem values (?,?,?,?,?)", [(i, v[0], v[1], "subsystem_map_data.json", build_id) for i, v in sorted(sub_rows.items())])
    man["subsystem_map_n_subsystems"] = str(len(sm["subsystems"]))
    # ---- groups: primary (anchor linuxdoom) and the stability run (anchor chocolate-doom)
    pid2name = {r[0]: r[1] for r in portrows}
    insts = {r[0]: dict(port=pid2name[r[1]], size=r[7]) for r in inst_rows}
    edges = [dict(a=k[0], b=k[1], tier=k[2], source=k[3], gate=bool(v[2]), verdict=v[3]) for k, v in medges.items()]
    calls = [(k[0], k[1]) for k in cedges if k[3] == "g1" or k[3] == "g2"]
    gid = 0
    for anchor, scope in ((C.ANCHOR, "full"), (C.SWAP_ANCHOR, f"anchor_swap:{C.SWAP_ANCHOR}")):
        if anchor not in byport: continue
        res = build_groups(insts, edges, calls, parent, anchor, C.CONTROL_PORTS, scope)
        gmap = {}
        for a_ in res["anchors"]:
            gid += 1; gmap[a_] = gid
        mem_rows = []; cnt = collections.defaultdict(lambda: [0, set()])
        for a_ in res["anchors"]:
            mem_rows.append((a_, gmap[a_], scope, 1, "anchor", 1.0, C.jdump({"ch": "anchor"}), build_id)); cnt[a_][0] += 1; cnt[a_][1].add(insts[a_]["port"])
        for x, rows in sorted(res["members"].items()):
            for r in rows:
                mem_rows.append((x, gmap[r["group"]], scope, r["rank"], r["role"], r["confidence"], r["evidence"], build_id))
                if r["rank"] == 1: cnt[r["group"]][0] += 1; cnt[r["group"]][1].add(insts[x]["port"])
        db.executemany("insert into ortholog_group values (?,?,?,?,?,?,?,?)", [(gmap[a_], scope, a_, "anchored_v1", C.GROUP_VERSION, cnt[a_][0], len(cnt[a_][1]), build_id) for a_ in res["anchors"]])
        db.executemany("insert into membership values (?,?,?,?,?,?,?,?)", mem_rows)
        db.executemany("insert into ungrouped values (?,?,?,?)", [(x, scope, why, build_id) for x, why in sorted(res["ungrouped"].items())])
        print(scope, "groups", len(res["anchors"]), "members", len(res["members"]), "ungrouped", len(res["ungrouped"]), flush=True)
    # ---- layer availability
    q = lambda s: dict(db.execute(s).fetchall())
    avail = {
        "structure": q("select p.name, count(*) from instance i join port p using(port_id) group by 1"),
        "match_e12": q("select p.name, count(distinct i.inst_id) from instance i join port p using(port_id) join match_edge m on m.source='e12' and (m.a_inst=i.inst_id or m.b_inst=i.inst_id) group by 1"),
        "name_agree": q("select p.name, count(distinct i.inst_id) from instance i join port p using(port_id) join match_edge m on m.source='name' and (m.a_inst=i.inst_id or m.b_inst=i.inst_id) group by 1"),
        "text_arbiter": q("select p.name, count(distinct i.inst_id) from instance i join port p using(port_id) join match_edge m on m.source='e7_arbiter' and (m.a_inst=i.inst_id or m.b_inst=i.inst_id) group by 1"),
        "call_g1": q("select p.name, count(distinct i.inst_id) from instance i join port p using(port_id) join call_edge c on c.source='g1' and (c.caller_inst=i.inst_id or c.callee_inst=i.inst_id) group by 1"),
        "call_g2": q("select p.name, count(distinct i.inst_id) from instance i join port p using(port_id) join call_edge c on c.source='g2' and (c.caller_inst=i.inst_id or c.callee_inst=i.inst_id) group by 1"),
        "subsystem": q("select p.name, count(*) from subsystem s join instance i using(inst_id) join port p using(port_id) group by 1"),
        "group_member": q("select p.name, count(distinct i.inst_id) from membership m join instance i using(inst_id) join port p using(port_id) where m.build_scope='full' and m.rank=1 group by 1"),
    }
    linp = {r[0] for r in lin_rows}
    avail["lineage"] = {p: byport[p]["inst"].__len__() for p in ports if p in linp}
    db.executemany("insert into layer_availability values (?,?,?)", [(p, l, d.get(p, 0)) for l, d in avail.items() for p in ports])
    scan_n = sum(1 for p in OPENED if "/scans/" in p)
    man["opened_databases"] = json.dumps({"scan_dbs": scan_n, "other": sorted({Path(p.split("?")[0]).name for p in OPENED if "/scans/" not in p})})
    db.executemany("insert into build_manifest values (?,?)", sorted(man.items()))
    db.commit()
    check_allowlist(db)
    db.close()
    print(f"built {out} in {time.time()-t0:.0f}s", flush=True)

def check_allowlist(db):
    """ingest allowlist: no text column may hold a value longer than TEXT_LIMIT or containing a newline (no source text, no snippets, no rationales)"""
    bad = []
    for (t,) in db.execute("select name from sqlite_master where type='table'").fetchall():
        for cid, col, typ, *_ in db.execute(f"pragma table_info({t})").fetchall():
            if "TEXT" not in (typ or "").upper(): continue
            if t == "build_manifest" and col == "value": lim = 4000   # manifest values: paths, hashes, thresholds (lists of ports can be long)
            else: lim = C.TEXT_LIMIT
            n = db.execute(f'select count(*) from {t} where length("{col}") > ? or "{col}" like \'%\n%\'', (lim,)).fetchone()[0]
            if n: bad.append((t, col, n))
    if bad: raise SystemExit(f"allowlist violation: {bad}")

if __name__ == "__main__":
    main()
