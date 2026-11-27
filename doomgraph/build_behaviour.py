#!/usr/bin/env python3
"""Build doomgraph_behaviour.sqlite (separate file): clean reach counts, E15 function phenotypes with hot/inert/usable flags verbatim from the E15 pipeline
(demo/harness/mscreen/analysis/roles.py and tests.usable) for chocolate-doom, managed-doom and prboom-plus, the demo table, and E13 demo conformance.
Reads the static database only to map screen functions to instance ids.  NOT ingested: Mocha or gore lesion outcomes (screen/jv_v2, go_v2, results/e17,
results/e16/cases), and no lesion-level rows (lesion text) for any port.

    nice -n 10 python3 doomgraph/build_behaviour.py [--static PATH] [--out PATH]"""
import argparse, collections, csv, datetime, hashlib, json, math, os, sqlite3, sys, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
ANALYSIS = C.REPO / "demo/harness/mscreen/analysis"
SCREEN = C.WORK / "demo-study/screen"
FORBIDDEN = ("jv_v2", "go_v2", "results/e17", "results/e16/cases", "mocha", "gore_v2")
STORES = (("choc", "chocolate-doom"), ("md", "managed-doom"), ("pb", "prboom-plus"))

_real_connect = sqlite3.connect
def _guard(database, *a, **k):
    s = str(database).lower()
    if any(w in s for w in FORBIDDEN): raise PermissionError(f"E17 is blind: refusing to open {database}")
    return _real_connect(database, *a, **k)
sqlite3.connect = _guard

def import_e15():
    """E15 loaders and the usable() mask, verbatim; tests.py imports scikit-learn only for an AMI helper this build does not use, so a stub stands in when scikit-learn is absent"""
    sys.path.insert(0, str(ANALYSIS))
    try:
        import sklearn.metrics  # noqa: F401
    except ImportError:
        m = types.ModuleType("sklearn"); mm = types.ModuleType("sklearn.metrics"); mm.adjusted_mutual_info_score = lambda *a, **k: float("nan"); m.metrics = mm
        sys.modules["sklearn"] = m; sys.modules["sklearn.metrics"] = mm
    import roles, tests
    return roles, tests

CONF_FILES = {   # E13 demo-conformance files -> (port, variant)
    "phase0_gore_vs_chocolate.csv": ("gore", "random300"), "phase0_mochadoom_vs_chocolate.csv": ("mochadoom", "random300"),
    "phase0_room4doom_vs_chocolate_random300.csv": ("room4doom", "random300"), "phase0_room4doom_vs_chocolate_quietstart150.csv": ("room4doom", "quietstart150"),
    "phase1_gore_chaos200.csv": ("gore", "chaos200"), "phase1_kocoa_chaos200_wide.csv": ("kocoa-doom", "chaos200"), "phase1_kocoa_sticky300_wide.csv": ("kocoa-doom", "sticky300"),
    "phase1_mochadoom_chaos200_wide.csv": ("mochadoom", "chaos200"), "phase1_mochadoom_sticky300_wide.csv": ("mochadoom", "sticky300"), "phase1_room4doom_chaos200.csv": ("room4doom", "chaos200"),
    "phase2_botdemos_gore_wide.csv": ("gore", "botdemos"), "phase2_botdemos_kocoa_wide.csv": ("kocoa-doom", "botdemos"), "phase2_botdemos_mochadoom_wide.csv": ("mochadoom", "botdemos"),
    "phase2_botdemos_room4doom.csv": ("room4doom", "botdemos"), "phase2_botdemos_room4doom_header1.csv": ("room4doom", "botdemos_header1"),
    "phase3_botdemos_doomascii_wide.csv": ("doom-ascii", "botdemos"), "phase3_botdemos_manageddoom_wide.csv": ("managed-doom", "botdemos"), "phase3_botdemos_puredoom.csv": ("puredoom", "botdemos"),
    "phase3_gen_asc.csv": ("doom-ascii", "generated"), "phase3_gen_md.csv": ("managed-doom", "generated"), "phase3_gen_pd.csv": ("puredoom", "generated"),
    "phase3_gen_c_asc.csv": ("doom-ascii", "generated_c"), "phase3_gen_c_md.csv": ("managed-doom", "generated_c"), "phase3_gen_c_pd.csv": ("puredoom", "generated_c"),
}
ENGINE = {"choc": "chocolate-doom", "dg": "doomgeneric", "crispy": "crispy-doom", "pboom": "prboom-plus", "sdl": "sdl-doom", "inter": "inter-doom"}

def conformance_rows(demo_dir, build_id):
    rows = []
    def ival(x):
        try: return int(float(x))
        except (TypeError, ValueError): return None
    for fn, (port, var) in sorted(CONF_FILES.items()):
        p = demo_dir / fn
        if not p.exists(): continue
        for r in csv.DictReader(open(p)):
            if "gore_tic" in r:       # phase0 gore: original and the fixed build
                for tag, pre in (("orig", "gore"), ("fix", "gorefix")):
                    t = ival(r[f"{pre}_tic"]); rows.append((port, r["demo"], f"{var}:{tag}", "diverged" if t is not None else "identical", t, r[f"{pre}_field"] or None, fn, build_id))
                continue
            for tag in ("strict", "gameplay"):
                if f"{tag}_tic" not in r: continue
                t = ival(r[f"{tag}_tic"]); rows.append((port, r["demo"], f"{var}:{tag}", "diverged" if t is not None else "identical", t, r[f"{tag}_field"] or None, fn, build_id))
    p = demo_dir / "phase0_random_demo_matrix.csv"
    for r in csv.DictReader(open(p)):
        rows.append((ENGINE[r["engine"]], r["demo"], "random300:matrix", r["status"], ival(r["tic"]), r["field"] or None, p.name, build_id))
    return rows

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--static", default=str(C.STATIC_DB)); ap.add_argument("--out", default=str(C.BEHAV_DB))
    a = ap.parse_args(); out = Path(a.out)
    if out.exists(): out.unlink()
    roles, tests = import_e15()
    import numpy as np
    build_id = "dg-v0-" + datetime.date.today().isoformat()
    S = _real_connect(f"file:{a.static}?mode=ro", uri=True)
    db = _real_connect(str(out)); db.executescript(C.BEHAV_DDL)
    e15 = C.git_info(); e15c = C.git_info()["code_commit"]
    import subprocess
    e15_commit = subprocess.run(["git", "-C", str(C.REPO), "log", "-1", "--format=%H", "--", "demo/harness/mscreen/analysis/roles.py", "demo/harness/mscreen/analysis/tests.py"], capture_output=True, text=True).stdout.strip()
    man = dict(e15); man.update(schema_version=C.SCHEMA_VERSION, build_id=build_id, built_at=datetime.datetime.now().isoformat(timespec="seconds"), e15_pipeline_commit=e15_commit,
        static_db_sha256=C.sha256_file(a.static), excluded="Mocha and gore lesion outcomes (E17 blind); no lesion-level rows for any port",
        usable_rule="tests.usable: eligible (>= 4 informative lesions) and not hot and not inert, verbatim", hot_frac=str(roles.HOT_FRAC), min_inf=str(roles.MIN_INF))
    sel = json.load(open(SCREEN / "demo_selection_2.json")); freedoom = set(sel["chosen"])
    all_demos = {}; availability = {}
    for store, port in STORES:
        dbp = SCREEN / f"{store}_phenotypes.sqlite"; man[f"store_sha256:{store}"] = C.sha256_file(dbp)
        P = roles.load_port(port, dbp); ph = roles.phenotype(P); us = tests.usable(ph)
        ids = {r[0]: r[1:] for r in S.execute("select i.inst_id, i.instance_key, i.name, i.file, i.line from instance i join port p using(port_id) where p.name=?", (port,))}
        idx = collections.defaultdict(list)
        for iid, (key, name, file, line) in ids.items(): idx[(os.path.splitext(os.path.basename(file))[0].lower(), name)].append((iid, line))
        st = _real_connect(f"file:{dbp}?mode=ro", uri=True)
        fmap = {}; unm = 0
        for fid, f, n, l in st.execute("select fid, file, name, line from functions"):
            c = idx.get((f.lower(), n), [])
            if len(c) > 1: c = [x for x in c if x[1] == l]
            if len(c) == 1: fmap[fid] = c[0][0]
            else: unm += 1
        man[f"screen_functions_unmapped:{port}"] = str(unm)
        for d in P.demos: all_demos.setdefault(d, set()).add(store)
        rows = []
        for k, fid in enumerate(ph.fids):
            iid = fmap.get(int(fid))
            if iid is None: continue
            cl = [None if math.isnan(x) else float(x) for x in ph.cls[k]]
            rows.append((port, iid, ids[iid][0], int(ph.hot[k]), int(ph.inert[k]), int(us[k]), int(ph.eligible[k]), int(ph.ninf[k]),
                         None if math.isnan(ph.tic[k]) else float(ph.tic[k]), *cl, e15_commit, f"{port}:{len(P.demos)}:{hashlib.sha1(','.join(P.demos).encode()).hexdigest()[:10]}", "e15_screen_store", build_id))
        db.executemany("insert into phenotype values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        pd_rows = []
        for k, fid in enumerate(ph.fids):
            iid = fmap.get(int(fid))
            if iid is None: continue
            for j, d in enumerate(P.demos):
                if not math.isnan(ph.F[k][j]): pd_rows.append((port, iid, d, float(ph.F[k][j])))
        db.executemany("insert into phenotype_demo values (?,?,?,?)", pd_rows)
        rr = []
        for fid, d, n, ft in zip(P.reach.fid, P.reach.demo, P.reach.entries, P.reach.first_tic):
            iid = fmap.get(int(fid))
            if iid is not None: rr.append((port, iid, ids[iid][0], d, int(n), None if ft is None or (isinstance(ft, float) and math.isnan(ft)) else int(ft), "e15_screen_store", build_id))
        db.executemany("insert into demo_reach values (?,?,?,?,?,?,?,?)", rr)
        availability[port] = dict(phenotype=len(rows), demo_reach=len({r[1] for r in rr}), phenotype_usable=sum(r[5] for r in rows), conformance=0)
        print(port, "phenotypes", len(rows), "usable", availability[port]["phenotype_usable"], "reach rows", len(rr), "unmapped screen fns", unm, flush=True)
    db.executemany("insert into demo values (?,?,?,?,?,?)", [(d, ",".join(sorted(s)), "freedoom2" if d in freedoom else "doom1_shareware", d[0], "e15_77", "demo_selection_2.json") for d, s in sorted(all_demos.items())])
    conf = conformance_rows(C.REPO / "demo", build_id)
    db.executemany("insert into conformance values (?,?,?,?,?,?,?,?)", conf)
    byp = collections.Counter(); 
    for r in conf: byp[r[0]] += 1
    for p, n in byp.items(): availability.setdefault(p, {})["conformance"] = len({r[1] for r in conf if r[0] == p})
    for p, d in availability.items():
        for l, n in d.items(): db.execute("insert into layer_availability values (?,?,?)", (p, l, n))
    db.executemany("insert into build_manifest values (?,?)", sorted(man.items()))
    db.commit()
    for (t,) in db.execute("select name from sqlite_master where type='table'").fetchall():
        for cid, col, typ, *_ in db.execute(f"pragma table_info({t})").fetchall():
            if "TEXT" in (typ or "").upper():
                lim = 4000 if (t == "build_manifest" and col == "value") else C.TEXT_LIMIT
                if db.execute(f'select count(*) from {t} where length("{col}")>?', (lim,)).fetchone()[0]: raise SystemExit(f"allowlist violation {t}.{col}")
    db.close(); print("built", out)

if __name__ == "__main__":
    main()
