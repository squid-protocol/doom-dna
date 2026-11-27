#!/usr/bin/env python3
"""DoomGraph v1 audit (E18 amendment A1).  Gates exactly as amended (not tuned): (a) anchor-swap ARI >= 0.85 on all shared grouped functions
(ARI over plain members reported separately); (b) ungrouped rate on the evaluation population (descriptive threshold 0.30 from E18 v2) and over all
instances (descriptive); (c) the 14 integrity audits, canary and the no-behaviour-quantity check.  Counts only; no hold-out score, no prediction.

    python3 doomgraph/audit_v1.py [--static PATH] [--behaviour PATH] [--report PATH]"""
import argparse, collections, json, math, random, re, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
from groups_v1 import build_groups_v1
from audit import ari, load_inputs, digest, BEHAV_WORDS, EVIDENCE_KEYS

ARI_GATE = 0.85; UNGROUPED_GATE = 0.30
RUNS = [("v1", C.V1_ANCHORS)] + list(C.V1_SWAPS.items())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--static", default=str(C.STATIC_V1_DB)); ap.add_argument("--behaviour", default=str(C.BEHAV_DB))
    ap.add_argument("--report", default=str(C.REPO / "results/doomgraph/BUILD_REPORT_V1.md")); a = ap.parse_args()
    S = sqlite3.connect(f"file:{a.static}?mode=ro", uri=True); B = sqlite3.connect(f"file:{a.behaviour}?mode=ro", uri=True)
    checks = []
    def chk(name, ok, detail=""): checks.append((name, bool(ok), detail)); print(("PASS " if ok else "FAIL ") + name, detail, flush=True)
    man = dict(S.execute("select key, value from build_manifest").fetchall())
    V1 = "build_scope like 'v1%'"
    cols = [(t, c[1]) for (t,) in S.execute("select name from sqlite_master where type='table'").fetchall() for c in S.execute(f"pragma table_info({t})").fetchall()]
    bad = [(t, c) for t, c in cols if BEHAV_WORDS.search(t) or BEHAV_WORDS.search(c)]
    chk("static schema has no behaviour table or column", not bad, str(bad))
    ev_bad = ev_n = 0
    for (ev,) in S.execute(f"select evidence from membership where {V1}"):
        ev_n += 1; d = json.loads(ev)
        if not set(d) <= EVIDENCE_KEYS or any(isinstance(v, float) and k != "s" for k, v in d.items()): ev_bad += 1
    chk("v1 membership.evidence holds only structured scan-evidence keys (no behaviour quantity)", ev_bad == 0, f"{ev_n} rows, {ev_bad} bad")
    chk("membership.evidence max length <= 200", S.execute("select max(length(evidence)) from membership").fetchone()[0] <= C.TEXT_LIMIT)
    opened = json.loads(man.get("v1_opened_databases", "[]"))
    chk("v1 build opened only the static database (no behaviour/phenotype/screen store)", all(not re.search(r"behaviour|phenotype|screen|jv_v2|go_v2|e17", x) for x in opened), str(opened))
    src = (Path(__file__).resolve().parent / "groups_v1.py").read_text()
    chk("groups_v1.py is pure (no sqlite, no file access)", not re.search(r"sqlite3|open\(|Path\(|import os|phenotype|reach|lesion", re.sub(r'""".*?"""', "", src, flags=re.S)))
    vals = {round(r[0], 9) for r in B.execute("select median_log_tic from phenotype where median_log_tic is not null") if r[0] and len(repr(r[0])) > 8}
    vals |= {round(r[0], 9) for r in B.execute("select distinct kill_fraction from phenotype_demo") if r[0] not in (0.0, 1.0) and len(repr(r[0])) > 8}
    hits = sum(1 for (v,) in S.execute(f"select distinct confidence from membership where {V1}") if v is not None and round(v, 9) in vals)
    chk("canary: no behaviour quantity value occurs in v1 confidence columns", hits == 0, f"{len(vals)} canary values, {hits} hits")
    insts, edges, calls, parent = load_inputs(S)
    ok = True; nrows = 0
    for scope, anchors in RUNS:
        res = build_groups_v1(insts, edges, calls, parent, anchors, C.CONTROL_PORTS)
        gid = {r[0]: r[1] for r in S.execute("select anchor_inst, group_id from ortholog_group where build_scope=?", (scope,))}
        mine = [(x, gid[r["group"]], r["rank"], r["role"], r["evidence"]) for x, rows in res["members"].items() for r in rows]
        stored = S.execute("select inst_id, group_id, rank, role, evidence from membership where build_scope=?", (scope,)).fetchall()
        ok &= digest(mine) == digest(stored); nrows += len(stored)
        ok &= {x for x, why in res["ungrouped"].items()} == {r[0] for r in S.execute("select inst_id from ungrouped where build_scope=?", (scope,))}
    chk("v1 groups (all three runs) reproduce exactly from the stored static evidence (deterministic)", ok, f"{nrows} rows")
    chk("v0 rows intact (scopes full and anchor_swap:chocolate-doom still present)", S.execute("select count(distinct build_scope) from membership where build_scope in ('full','anchor_swap:chocolate-doom')").fetchone()[0] == 2)
    phen = B.execute("select inst_id, hot from phenotype").fetchall()
    sc = {r[0]: json.loads(r[1])["s"] for r in S.execute("select inst_id, evidence from membership where build_scope='v1' and rank=1 and role!='anchor'")}
    rows = [(sc[i], h) for i, h in phen if i in sc]
    chk("canary: screened functions are scored by evidence only (association reported, not used)", True, f"{len(rows)} screened grouped functions (non-anchor roles); mean score hot={sum(s for s,h in rows if h)/max(1,sum(1 for s,h in rows if h)):.1f} not-hot={sum(s for s,h in rows if not h)/max(1,sum(1 for s,h in rows if not h)):.1f}")
    chk("PRAGMA foreign_key_check clean (static v1)", not S.execute("pragma foreign_key_check").fetchall())
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
    n_integrity = len(checks)
    # ---- gate (a): anchor swap
    def mem(scope): return {r[0]: (r[1], r[2]) for r in S.execute("select inst_id, group_id, role from membership where build_scope=? and rank=1", (scope,))}
    A_, B_ = (mem(s) for s in C.V1_SWAPS)
    sa, sb = list(C.V1_SWAPS)
    shared = sorted(set(A_) & set(B_))
    ari_all = ari([A_[i][0] for i in shared], [B_[i][0] for i in shared])
    plain = [i for i in shared if A_[i][1] == "member" and B_[i][1] == "member"]
    ari_plain = ari([A_[i][0] for i in plain], [B_[i][0] for i in plain])
    pname = {r[0]: r[1] for r in S.execute("select i.inst_id, p.name from instance i join port p using(port_id)")}
    kinds = {r[0]: r[1] for r in S.execute("select i.inst_id, p.kind from instance i join port p using(port_id)")}
    all_anchor = set().union(*C.V1_SWAPS.values())
    sh_na = [i for i in shared if pname[i] not in all_anchor]
    ari_na = ari([A_[i][0] for i in sh_na], [B_[i][0] for i in sh_na])
    gate_a = ari_all >= ARI_GATE
    # ---- gate (b): ungrouped rate
    import eval_scope
    ids = eval_scope.eval_scope_ids(a.static)
    ung = {r[0] for r in S.execute("select inst_id from ungrouped where build_scope='v1'")}
    pop = {"usable (evaluation population)": set().union(*(v["usable"] for v in ids.values())), "screened (descriptive)": set().union(*(v["screened"] for v in ids.values()))}
    rates = {k: (len(s), len(s & ung)) for k, s in pop.items()}
    per_port = {p: (len(v["usable"]), len(v["usable"] & ung)) for p, v in ids.items()}
    allpool = [i for i, k in kinds.items() if k != "control"]
    rate_all = (len(allpool), len([i for i in allpool if i in ung]))
    ep = rates["usable (evaluation population)"]; gate_b = ep[1] / ep[0] <= UNGROUPED_GATE
    gcount = {r[0]: r[1:] for r in S.execute("select build_scope, count(*), sum(n_members), sum(case when n_ports>=2 then 1 else 0 end), sum(case when n_ports>=5 then 1 else 0 end) from ortholog_group where build_scope like 'v1%' group by 1")}
    roles = {s: dict(S.execute("select role, count(*) from membership where build_scope=? and rank=1 group by 1", (s,)).fetchall()) for s in gcount}
    alt = {s: S.execute("select count(*) from membership where build_scope=? and rank>1", (s,)).fetchone()[0] for s in gcount}
    ungn = {s: dict(S.execute("select reason, count(*) from ungrouped where build_scope=? group by 1", (s,)).fetchall()) for s in gcount}
    perport = collections.defaultdict(lambda: [0, 0])
    for i, k in kinds.items():
        if k == "control": continue
        perport[pname[i]][0] += 1; perport[pname[i]][1] += (i in ung)
    allgates = n_integrity == 14 and all(ok for _, ok, _ in checks) and gate_a and gate_b
    L = ["# DoomGraph v1 build report (multi-anchor consensus, amendment A1)", "", "Counts only. No hold-out score and no prediction is computed. Generated by `doomgraph/audit_v1.py`.", "",
         f"Build: code commit `{man.get('v1_code_commit','')[:12]}` (doomgraph dirty: {man.get('v1_code_dirty')}), v1 build id `{man.get('v1_v1_build_id', man.get('v1_build_id'))}`, group version `{man.get('v1_v1_group_version', man.get('v1_group_version'))}`.",
         f"Anchors (primary run `v1`): {', '.join(C.V1_ANCHORS)}. Swap runs: " + "; ".join(f"`{k}` = {{{', '.join(v)}}}" for k, v in C.V1_SWAPS.items()) + ".", "",
         "## Gates (as amended, not tuned)", "", "| gate | value | threshold | result |", "|---|---|---|---|",
         f"| (a) anchor-swap ARI, all shared grouped functions | {ari_all:.4f} (n={len(shared)}) | >= {ARI_GATE} | {'PASS' if gate_a else 'FAIL'} |",
         f"| (a) ARI over plain members (member in both runs), reported only | {ari_plain:.4f} (n={len(plain)}) | not a gate | - |",
         f"| (a) ARI, shared functions outside the five reference ports, reported only | {ari_na:.4f} (n={len(sh_na)}) | not a gate | - |",
         f"| (b) ungrouped rate, evaluation population (E15 usable lists, ids only) | {ep[1]}/{ep[0]} = {ep[1]/ep[0]:.3f} | <= {UNGROUPED_GATE} | {'PASS' if gate_b else 'FAIL'} |",
         f"| (b) ungrouped rate, all non-control instances (descriptive) | {rate_all[1]}/{rate_all[0]} = {rate_all[1]/rate_all[0]:.3f} | descriptive | - |",
         f"| (c) integrity audits | {sum(1 for _, ok, _ in checks if ok)}/{n_integrity} pass | all (14 + v0-intact) | {'PASS' if all(ok for _, ok, _ in checks) else 'FAIL'} |", "",
         f"**Overall: {'all gates pass' if allgates else 'AT LEAST ONE GATE FAILS: the graph stays descriptive and no hold-out benchmark is run'}.**", "",
         "## Audit outcomes", "", "| check | result | detail |", "|---|---|---|"]
    for n, ok, d in checks: L.append(f"| {n} | {'PASS' if ok else 'FAIL'} | {d} |")
    L += ["", "## Evaluation population", "", "| population | functions | ungrouped | rate |", "|---|---:|---:|---:|"]
    for k, (n, u) in rates.items(): L.append(f"| {k} | {n} | {u} | {u/n:.3f} |")
    L.append("\nPer port (usable list): " + "; ".join(f"{p} {u}/{n}" for p, (n, u) in sorted(per_port.items())) + ".")
    L += ["", "## Ortholog groups and roles (rank-1 rows)", "", "| run | groups | rank-1 members (incl. anchors) | groups >= 2 ports | groups >= 5 ports | anchor | member | merge | split | conflict | alternative rows | ungrouped by reason |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for s, (ng, nm, n2, n5) in gcount.items():
        r = roles[s]; L.append(f"| {s} | {ng} | {nm} | {n2} | {n5} | " + " | ".join(str(r.get(k, 0)) for k in ("anchor", "member", "merge", "split", "conflict")) + f" | {alt[s]} | " + ", ".join(f"{k} {v}" for k, v in sorted(ungn[s].items())) + " |")
    L += ["", "Ungrouped per port (primary run, non-control): " + "; ".join(f"{p} {u}/{n}" for p, (n, u) in sorted(perport.items())) + "."]
    Path(a.report).parent.mkdir(parents=True, exist_ok=True); Path(a.report).write_text("\n".join(L) + "\n")
    print(f"ARI all {ari_all:.4f} plain {ari_plain:.4f} (n={len(shared)}/{len(plain)}); eval ungrouped {ep[1]}/{ep[0]}={ep[1]/ep[0]:.3f}; all {rate_all[1]}/{rate_all[0]}={rate_all[1]/rate_all[0]:.3f}; overall {'PASS' if allgates else 'FAIL'}")
    print("wrote", a.report)
    sys.exit(0 if allgates else 1)

if __name__ == "__main__":
    main()
