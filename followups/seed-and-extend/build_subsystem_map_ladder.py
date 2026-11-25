"""Rebuild the call-graph subsystem map's ancestry colouring on the E12 evidence tiers.

Stage 1 (``--stage jobs``): for each port and each reference it may descend from (``linuxdoom`` plus the older
DOOM ports of the lineage rule below), run the E12 matcher (fingerprint twins, graph seeds, extension; no names)
and store the matches in a work directory, one resumable file per (port, reference).
Stage 2 (``--stage assemble``): colour every function of every port by the strongest evidence of ancestry
(red = ``linuxdoom``, other colours = a later ancestor the function does NOT trace to ``linuxdoom`` through),
place it on one of ``linuxdoom``'s 16 call-graph subsystems, and write ``article/subsystem_map_data.json``.

Evidence tiers, strongest first: exact, twin, xtwin (fingerprints), seed, ext1, ext2, ext3 (graph).
Seeds and extension are used only where the pair passes E12's coherence gate (it fails on unrelated programs and on
the most diverged ports), so a failed gate leaves that port's graph-only evidence out instead of showing noise.
A function traces to the reference with the strongest tier; ties go to ``linuxdoom``, then to the donor order below.
A donor only counts for functions the donor itself does not trace to ``linuxdoom`` (code the donor added),
and only on fingerprint evidence (exact, twin): its added-code set is small, so graph matches reach it by chance.

The subsystem placement reads call edges, so the figure shows where a port's functions fall among DOOM's
subsystems; it is not an independent measure of preserved architecture (see DOOM-E11).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "measure"))
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/measure")
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
import numpy as np  # noqa: E402

import e12_ladder as L  # noqa: E402
import e7_draws as D  # noqa: E402
from structural_fingerprint import blind as BL  # noqa: E402
from structural_fingerprint.twins import TwinParams  # noqa: E402

WORK = Path("/srv/storage_16tb/projects/doom-e7-work/gene-view")
OUT = REPO / "article" / "subsystem_map_data.json"
TIERS = ["exact", "twin", "xtwin", "seed", "ext1", "ext2", "ext3"]
RANK = {t: i for i, t in enumerate(TIERS)}
DONORS = ("chocolate-doom", "prboom-plus", "doomgeneric", "woof")
PORT_YEAR = {"linuxdoom": 1993, "srb2": 1998, "prboom": 1999, "eternity": 2001, "chocolate-doom": 2005, "prboom-plus": 2006,
             "odamex": 2006, "crispy-doom": 2014, "doomgeneric": 2016, "woof": 2019, "dsda-doom": 2020}
CONTROLS = {"lua", "quake", "quake2"}
WANTED = ["chocolate-doom", "crispy-doom", "doomgeneric", "doomretro", "prboom-plus", "dsda-doom", "woof", "eternity", "odamex", "srb2",
          "room4doom", "gore", "managed-doom", "mochadoom", "rust-doom", "doom-wasm", "fastdoom", "puredoom", "doom-ios", "doom-ascii",
          "helion", "edge-classic", "nugget-doom", "inter-doom", "sdl-doom", "doom3do", "sqldoom", "doomf77", "doom-scheme", "doo-cr",
          "kocoa-doom", "fsharp-doom", "cssdoom", "doom-fx", "fps-cob", "agentic-cobol-doom-cc", "agentic-cobol-doom-codex", "mood",
          "freedoom", "dartdoom", "lua", "quake", "quake2"]
CHOC_EXCLUDED = ("src/heretic/", "src/hexen/", "src/strife/", "src/setup/")
MAX_N = 10000


def eligible_donors(port: str) -> list[str]:
    if port in CONTROLS or port in {"linuxdoom", "srb2"}:
        return []
    year = PORT_YEAR.get(port, 2022)
    return [d for d in DONORS if d != port and PORT_YEAR[d] < year]


def jobs_list(only: list[str] | None = None) -> list[tuple[str, str]]:
    out = []
    for p in WANTED:
        if only and p not in only:
            continue
        if not (L.SC / p).is_dir():
            continue
        out.append((p, "linuxdoom"))
        out += [(p, d) for d in eligible_donors(p)]
    return out


# ---------------------------------------------------------------- stage 1
def fingerprint_pairs(port: str, ref: str, preset: str) -> list[tuple[int, int, float]]:
    """Registered twin setting (FDR 0.01, ratio 0.8, pooled K=25), both directions, strictly one-to-one."""
    tp, _, _ = L.tables(port, preset)
    tl, _, _ = L.tables(ref, preset)
    par = TwinParams(min_loc=L.MIN_LOC, ratio=0.8, fdr=0.01)
    res = {}
    for tag, q, t in (("pl", tp, tl), ("lp", tl, tp)):
        _, dec, real, s = D.pair_draws(q, t, list(range(25)), par)
        res[tag] = (dec, real, s)
    cands = []
    dec, real, s = res["pl"]
    r = L.TW.accept(s, L.pooled_cutoff_fdr(real, dec, 0.01))
    d_all = np.where(r.exact, 0.0, r.distance)
    cands += [(float(d), int(a), int(b)) for a, b, d in zip(r.q_index, r.t_index, d_all)]
    dec, real, s = res["lp"]
    r = L.TW.accept(s, L.pooled_cutoff_fdr(real, dec, 0.01))
    d_all = np.where(r.exact, 0.0, r.distance)
    cands += [(float(d), int(b), int(a)) for a, b, d in zip(r.q_index, r.t_index, d_all)]
    return [(i, j, 1.0 - d) for i, j, d in L.one_to_one(cands)]


def pair_job(args: tuple[str, str]) -> str:
    port, ref = args
    f = WORK / f"{port}__{ref}.json"
    if f.exists():
        return f"{port} vs {ref}: cached"
    t0 = time.time()
    tp, _, _ = L.tables(port, "P")
    if BL.blind_view(tp).n > MAX_N:
        f.write_text(json.dumps({"port": port, "ref": ref, "skipped": "too large"}))
        return f"{port} vs {ref}: skipped (too large)"
    gr, gate = L.graph_rungs(port, np.random.default_rng(0), ref_name=ref)
    nseed = len(gr["S"])
    h1, h2, h3 = gate["E3c_hop_ends"]
    ext = []
    for k, (a, b, s) in enumerate(gr["E3c"][nseed:], start=nseed):
        ext.append([a, b, round(float(s), 4), 1 if k < h1 else (2 if k < h2 else 3)])
    out = {"port": port, "ref": ref,
           "F0": [[a, b, round(s, 4)] for a, b, s in fingerprint_pairs(port, ref, "F0")],
           "F1c": [[a, b, round(s, 4)] for a, b, s in fingerprint_pairs(port, ref, "F1c")],
           "S": [[a, b, round(float(s), 4)] for a, b, s in gr["S"]], "ext": ext,
           "gate": {"passes": bool(gate["passes"]), "strong_fgw": round(gate["strong_fgw"], 3), "mean_sup": round(gate["mean_sup"], 3)}}
    f.write_text(json.dumps(out, separators=(",", ":")))
    return f"{port} vs {ref}: {len(out['F0'])} F0, {len(out['F1c'])} F1c, {nseed} seeds, {len(ext)} ext, gate {gate['passes']} ({time.time() - t0:.0f}s)"


def run_jobs(only: list[str] | None, workers: int, smallest_first: bool = False) -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    todo = jobs_list(only)
    # biggest ports first so the long jobs do not end up last
    def size(j: tuple[str, str]) -> int:
        try:
            return int(L.tables(j[0], "P")[0].loc.shape[0])
        except Exception:
            return 0
    todo.sort(key=lambda j: size(j) if smallest_first else -size(j))
    print(f"{len(todo)} (port, reference) jobs, {workers} workers", flush=True)
    with ProcessPoolExecutor(workers) as ex:
        for line in ex.map(pair_job, todo):
            print(line, flush=True)


# ---------------------------------------------------------------- stage 2
def load_discover():
    spec = importlib.util.spec_from_file_location("bsm", Path(__file__).with_name("build_subsystem_map.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ref_matches(port: str, ref: str, tp, tl):
    """port table row -> (ref table row, tier, score), strictly one-to-one across tiers, E12 universe (>= 6 lines)."""
    f = WORK / f"{port}__{ref}.json"
    if not f.exists():
        return None, None
    d = json.loads(f.read_text())
    if "skipped" in d:
        return None, None
    ok = lambda a, b: tp.loc[a] >= L.MIN_LOC and tl.loc[b] >= L.MIN_LOC  # noqa: E731
    cand = {t: [] for t in TIERS}
    for a, b, s in d["F0"]:
        if ok(a, b):
            cand["exact" if s >= 0.999999 else "twin"].append((a, b, s))
    for a, b, s in d["F1c"]:
        if ok(a, b):
            cand["xtwin"].append((a, b, s))
    gate = d["gate"]
    if gate["passes"]:
        cand["seed"] = [(a, b, s) for a, b, s in d["S"] if ok(a, b)]
        for a, b, s, h in d["ext"]:
            if ok(a, b):
                cand[f"ext{h}"].append((a, b, s))
    used_a, used_b, out = set(), set(), {}
    for t in TIERS:
        for a, b, s in cand[t]:
            if a in used_a or b in used_b:
                continue
            used_a.add(a)
            used_b.add(b)
            out[a] = (b, t, s)
    return out, gate


def assemble(out_path: Path = OUT) -> None:
    from scipy.spatial import cKDTree
    bsm = load_discover()
    bp = BL.BlindParams()
    tl, ref_obj, _ = L.tables("linuxdoom", "P")
    rv = BL.blind_view(tl)
    na = len(ref_obj.archetype_names)
    xd_ld = BL.descriptors(rv, na, bp.use_graph, bp.use_measures, None, bp.geometry_only)
    locs_ld = np.array([int(tl.loc[r]) for r in rv.rows], dtype=np.int64)
    ld_comm, ld_groups, comm_info = bsm.discover_communities(rv.n, rv.edges, locs_ld, xd_ld)
    old = json.load(open(OUT))["subsystems"]
    deg = np.zeros(rv.n, dtype=np.int64)
    for u, v in rv.edges.tolist():
        if u != v:
            deg[u] += 1
            deg[v] += 1
    names_ld = [str(tl.name[r]) for r in rv.rows]
    labels = []
    for cid, g in enumerate(ld_groups):
        hubs = [names_ld[i] for i in sorted(g, key=lambda i: (-deg[i], -locs_ld[i]))[:2]]
        labels.append(f"S{cid + 1:02d}: " + bsm.SUBSYSTEM_NAMES.get(" / ".join(hubs), " / ".join(hubs)))
    assert labels == old, f"subsystem labels changed:\n{labels}\nvs\n{old}"
    row2comm = {int(r): int(c) for r, c in zip(rv.rows, ld_comm)}
    tree_ld = cKDTree(xd_ld)

    def excluded_rows(name: str, t) -> set[int]:
        if name != "chocolate-doom":
            return set()
        return {r for r in range(len(t.path)) if str(t.path[r]).startswith(CHOC_EXCLUDED)}

    # linuxdoom-traceable rows of each donor (for "code the donor added")
    red = {}
    for d in DONORS:
        td, _, _ = L.tables(d, "P")
        m, _ = ref_matches(d, "linuxdoom", td, tl)
        red[d] = set(m) if m else set()
    ports_out = {}
    for port in ["linuxdoom"] + WANTED:
        if not (L.SC / port).is_dir():
            continue
        tp, _, _ = L.tables(port, "P")
        pv = BL.blind_view(tp)
        if pv.n > MAX_N:
            print("skip", port, pv.n)
            continue
        if port == "linuxdoom":
            tracks = [[] for _ in labels]
            for i, r in enumerate(pv.rows):
                tracks[int(ld_comm[i])].append([str(tp.name[r]), int(tp.loc[r]), "linuxdoom", str(tp.name[r]), "self"])
            ports_out[port] = {"meta": f"{'/'.join(sorted(set(str(tp.language[r]) for r in pv.rows)))} • {pv.n:,} funcs • {int(sum(int(tp.loc[r]) for r in pv.rows)):,} LOC", "tracks": tracks, "gates": {}}
            continue
        excl = excluded_rows(port, tp)
        rows = [int(r) for r in pv.rows if int(r) not in excl]
        view_of = {int(r): i for i, r in enumerate(pv.rows)}
        m_ld, gate_ld = ref_matches(port, "linuxdoom", tp, tl)
        if m_ld is None:
            print("no linuxdoom job for", port)
            continue
        gates = {"linuxdoom": gate_ld}
        cand = defaultdict(list)  # row -> [(rank, pref, ref, ref_name, tier)]
        for r, (b, t, s) in m_ld.items():
            cand[r].append((RANK[t], 0, "linuxdoom", str(tl.name[b]), t, b))
        for k, d in enumerate(eligible_donors(port)):
            td, _, _ = L.tables(d, "P")
            m, gate_d = ref_matches(port, d, tp, td)
            if m is None:
                continue
            gates[d] = gate_d
            ex_d = excluded_rows(d, td)
            for r, (b, t, s) in m.items():
                if b in red[d] or b in ex_d:
                    continue
                if t not in ("exact", "twin"):
                    continue  # donors: fingerprint evidence only; their novel-function sets are small, so seeds and extension match them by chance
                cand[r].append((RANK[t], 1 + k, d, str(td.name[b]), t, b))
        best = {}
        for r in rows:
            if cand.get(r):
                best[r] = min(cand[r], key=lambda x: (x[0], x[1]))
        # subsystem placement: direct linuxdoom match, then neighbour votes, then nearest descriptor
        func_comm = {}
        for r in rows:
            b = best.get(r)
            if b and b[2] == "linuxdoom":
                func_comm[view_of[r]] = row2comm[b[5]]
        nbrs = defaultdict(set)
        for u, v in pv.edges.tolist():
            if u != v:
                nbrs[u].add(v)
                nbrs[v].add(u)
        for _ in range(4):
            upd = {}
            for qi in range(pv.n):
                if qi in func_comm:
                    continue
                votes = defaultdict(int)
                for u in nbrs[qi]:
                    if u in func_comm:
                        votes[func_comm[u]] += 1
                if votes:
                    upd[qi] = max(votes.items(), key=lambda x: x[1])[0]
            if not upd:
                break
            func_comm.update(upd)
        left = [qi for qi in range(pv.n) if qi not in func_comm]
        if left:
            xd_p = BL.descriptors(pv, na, bp.use_graph, bp.use_measures, None, bp.geometry_only)
            _, nearest = tree_ld.query(xd_p[left], k=1)
            for qi, ldi in zip(left, nearest.tolist(), strict=True):
                func_comm[qi] = int(ld_comm[ldi])
        tracks = [[] for _ in labels]
        n_by = defaultdict(int)
        for r in rows:
            b = best.get(r)
            ent = [str(tp.name[r]), int(tp.loc[r]), b[2] if b else None, b[3] if b else None, b[4] if b else None]
            tracks[func_comm[view_of[r]]].append(ent)
            n_by[ent[2] or "none"] += 1
        langs = "/".join(sorted(set(str(tp.language[r]) for r in rows)))
        ports_out[port] = {"meta": f"{langs} • {len(rows):,} funcs • {int(sum(int(tp.loc[r]) for r in rows)):,} LOC", "tracks": tracks, "gates": gates}
        print(f"{port:26s} rows={len(rows):5d} " + " ".join(f"{k}={v}" for k, v in sorted(n_by.items())) + f"  gate(linuxdoom)={gate_ld['passes']}", flush=True)
    payload = {"subsystems": labels, "ports": ports_out,
               "provenance": {"engine": "704cb35f0", "subsystems": comm_info, "names": "read from each subsystem's files and hub functions",
                              "placement": "E12 ladder: fingerprint twins, then graph seeds, then extension (seeds and extension only where the coherence gate passes); subsystem placement reads call-graph edges",
                              "tiers": TIERS, "donors": list(DONORS), "donor_rule": "older DOOM ports only; only for functions the donor itself does not trace to linuxdoom; exact or twin fingerprint evidence only",
                              "min_lines": L.MIN_LOC, "chocolate_doom_excludes": list(CHOC_EXCLUDED)}}
    out_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out_path} ({out_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["jobs", "assemble", "all"], default="all")
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--smallest-first", action="store_true", help="work from the small pairs up (a second pool beside a biggest-first one)")
    a = ap.parse_args()
    only = [x for x in a.only.split(",") if x] or None
    if a.stage in ("jobs", "all"):
        run_jobs(only, a.workers, a.smallest_first)
    if a.stage in ("assemble", "all"):
        assemble(Path(a.out))
