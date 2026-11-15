"""Build real 16-track call-graph DNA gene-map data for the interactive visualizer.

1. Discovers communities directly from ``linuxdoom``'s call graph (zero filename rules)
   using greedy modularity + merging tiny connected components into their strongest
   neighbor community, yielding 15 call-graph communities + 1 Novel/Horizontal track.
2. Runs Seed-and-Extend (zero names/paths) from ``linuxdoom`` onto each selected port
   to assign Red (``linuxdoom``) gene bands across the 15 call-graph tracks.
3. For functions not matched to ``linuxdoom``, checks reciprocal structural twins
   (``BL.descriptors``) against secondary donors (``chocolate-doom``, ``prboom-plus``,
   ``doomgeneric``, ``woof``) to highlight horizontal/branch transfers (Blue, Amber,
   Violet, Teal).
4. Writes ``article/dna_tracks_data.json`` with real per-function gene bands.
"""

from __future__ import annotations

import gc
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist


def discover_communities(n: int, edges: np.ndarray, locs: np.ndarray, k_keep: int = 15) -> tuple[np.ndarray, list[list[int]]]:
    """Greedy modularity clustering on undirected call graph, merging tiny groups."""
    adj = [defaultdict(int) for _ in range(n)]
    deg = np.zeros(n, dtype=np.float64)
    for u, v in edges.tolist():
        if u != v:
            adj[u][v] += 1
            adj[v][u] += 1
            deg[u] += 1
            deg[v] += 1
    m2 = max(1.0, float(np.sum(deg)))

    comm = list(range(n))
    tot_deg = deg.copy()
    for _ in range(20):
        moved = 0
        for i in range(n):
            if deg[i] == 0:
                continue
            ci = comm[i]
            cw = defaultdict(float)
            for j, w in adj[i].items():
                cw[comm[j]] += w
            tot_deg[ci] -= deg[i]
            best_c, best_gain = ci, 0.0
            for c, k_in in cw.items():
                gain = k_in - deg[i] * tot_deg[c] / m2
                if gain > best_gain + 1e-12:
                    best_gain = gain
                    best_c = c
            tot_deg[best_c] += deg[i]
            if best_c != ci:
                comm[i] = best_c
                moved += 1
        if moved == 0:
            break

    groups = defaultdict(list)
    for i, c in enumerate(comm):
        groups[c].append(i)

    # Sort communities by total LOC; keep top k_keep - 1 and fold remainder into last community
    ordered = sorted(groups.values(), key=lambda g: -sum(int(locs[i]) for i in g))
    kept = ordered[: k_keep - 1]
    rest = [i for g in ordered[k_keep - 1 :] for i in g]
    if rest:
        kept.append(rest)

    node_to_comm = np.zeros(n, dtype=np.int64)
    for cid, g in enumerate(kept):
        for i in g:
            node_to_comm[i] = cid
    return node_to_comm, kept


def main() -> int:
    from structural_fingerprint import blind as BL
    from structural_fingerprint import features as F
    from structural_fingerprint.fingerprint import build
    from structural_fingerprint.reference import load_reference
    from structural_fingerprint.scan_io import load_scan, resolve_scans

    scans_main = Path("/srv/storage_16tb/projects/gitgalaxy/doom-study/rescan-6c7c6c1bc/scans/6c7c6c1bc")
    scans_e5 = Path("/tmp/doom-e5/scans")
    scans_e6 = Path("/tmp/doom-e6/scans")
    out_json = Path(__file__).resolve().parents[2] / "article" / "dna_tracks_data.json"

    ref = load_reference("portable")
    bp = BL.BlindParams()

    def load_port(name: str, db_path: Path, max_n: int = 10000):
        sc = load_scan(db_path, ref.signal_columns)
        ft = build(sc, ref, min_loc=3, keyword_mode="composition").functions
        bv = BL.blind_view(ft)
        if max_n and len(bv.rows) > max_n:
            return {"name": name, "n": len(bv.rows), "skipped": True}
        xd = BL.descriptors(bv, len(ref.archetype_names), bp.use_graph, bp.use_measures, None, bp.geometry_only)
        hm = BL.hop_matrix(bv, bp.hop_cap)
        comp_all = F.raw_features(
            ref, sc.loc, sc.complexity, sc.args, sc.keyword_density, sc.signals,
            keyword_mode="composition",
        )
        comp = comp_all[bv.rows]
        cnorm = comp / np.maximum(np.linalg.norm(comp, axis=1, keepdims=True), 1e-9)
        nbrs = defaultdict(set)
        for u, v in bv.edges.tolist():
            if u != v:
                nbrs[u].add(v); nbrs[v].add(u)
        names = [str(ft.name[r]) for r in bv.rows]
        locs = np.array([int(ft.loc[r]) for r in bv.rows], dtype=np.int64)
        langs = sorted(set(str(ft.language[r]) for r in bv.rows))
        edges = bv.edges
        if name == "chocolate-doom":
            excluded = ("src/heretic/", "src/hexen/", "src/strife/", "src/setup/")
            keep = [i for i, r in enumerate(bv.rows) if not str(ft.path[r]).startswith(excluded)]
            old_to_new = {old: new for new, old in enumerate(keep)}
            xd = xd[keep]
            hm = hm[np.ix_(keep, keep)]
            comp = comp[keep]
            cnorm = cnorm[keep]
            names = [names[i] for i in keep]
            locs = locs[keep]
            edges = np.array(
                [[old_to_new[u], old_to_new[v]] for u, v in edges.tolist() if u in old_to_new and v in old_to_new],
                dtype=edges.dtype,
            ) if len(edges) else edges
            nbrs = defaultdict(set)
            for u, v in edges.tolist():
                if u != v:
                    nbrs[u].add(v); nbrs[v].add(u)
            n_out = len(keep)
        else:
            n_out = len(bv.rows)
        return {
            "name": name, "n": n_out, "xd": xd, "hm": hm, "comp": comp,
            "cnorm": cnorm, "nbrs": nbrs, "edges": edges, "names": names,
            "locs": locs, "langs": langs, "tree": cKDTree(xd),
        }

    ld = load_port("linuxdoom", resolve_scans([scans_main / "linuxdoom"])[0])
    ld_comm, ld_groups = discover_communities(ld["n"], ld["edges"], ld["locs"], k_keep=16)

    # Label each discovered community by its top-2 hub functions
    deg_ld = np.zeros(ld["n"], dtype=np.int64)
    for u, v in ld["edges"].tolist():
        if u != v:
            deg_ld[u] += 1; deg_ld[v] += 1

    track_labels = []
    for cid, g in enumerate(ld_groups):
        if cid == len(ld_groups) - 1 and len(g) > 100:
            track_labels.append("C16: Leaf / Misc Core")
        else:
            hubs = [ld["names"][i] for i in sorted(g, key=lambda i: (-deg_ld[i], -ld["locs"][i]))[:2]]
            track_labels.append(f"C{cid+1:02d}: " + " / ".join(hubs))

    print("Discovered 16 call-graph tracks:")
    for idx, lbl in enumerate(track_labels):
        print(f"  {idx+1:02d}. {lbl}")

    # Secondary donors (masked against linuxdoom)
    donors_spec = [
        ("chocolate-doom", resolve_scans([scans_main / "chocolate-doom"])[0]),
        ("prboom-plus", resolve_scans([scans_main / "prboom-plus"])[0]),
        ("doomgeneric", resolve_scans([scans_main / "doomgeneric"])[0]),
        ("woof", resolve_scans([scans_main / "woof"])[0]),
    ]
    heretic_db = scans_e6 / "heretic" / "heretic_galaxy_master.db"
    if heretic_db.is_file():
        donors_spec.append(("heretic", heretic_db))
    donors = {}
    for dname, ddb in donors_spec:
        D = load_port(dname, ddb)
        dists, _ = ld["tree"].query(D["xd"], k=1)
        nov = np.flatnonzero(dists > 0.35)
        donors[dname] = {
            "xd": D["xd"][nov], "tree": cKDTree(D["xd"][nov]),
            "locs": D["locs"][nov], "names": [D["names"][i] for i in nov],
        }

    DOOM_PORT_DONORS = ("chocolate-doom", "prboom-plus", "doomgeneric", "woof")
    PORT_YEAR = {
        "linuxdoom": 1993,
        "heretic": 1994,
        "hexen": 1995,
        "srb2": 1998,
        "zdoom": 1998,
        "prboom": 1999,
        "eternity": 2001,
        "chocolate-doom": 2005,
        "gzdoom": 2005,
        "prboom-plus": 2006,
        "odamex": 2006,
        "doom64ex": 2008,
        "crispy-doom": 2014,
        "doomgeneric": 2016,
        "woof": 2019,
        "dsda-doom": 2020,
    }

    def eligible_donors(tname, ctrl_names):
        if tname in ctrl_names or tname in {"linuxdoom", "heretic", "doom64ex", "srb2"}:
            return set()
        tyear = PORT_YEAR.get(tname, 2022)
        if tname == "hexen":
            return {"heretic"} if PORT_YEAR["heretic"] < tyear else set()
        return {d for d in DOOM_PORT_DONORS if d != tname and PORT_YEAR[d] < tyear}

    scans_ctrl = Path("/srv/storage_16tb/projects/gitgalaxy/doom-study/controls/scans")
    ctrl_names = set()
    targets = [("linuxdoom", resolve_scans([scans_main / "linuxdoom"])[0])]
    for p in sorted(scans_main.iterdir()):
        if not p.is_dir() or p.name == "linuxdoom":
            continue
        try:
            db = resolve_scans([p])[0]
            targets.append((p.name, db))
        except Exception:
            pass
    for p in sorted(scans_ctrl.iterdir()):
        if p.is_dir():
            try:
                targets.append((p.name, resolve_scans([p])[0]))
                ctrl_names.add(p.name)
            except Exception:
                pass
    for name in ["cydoomgeneric", "iron-doom", "doomarkable", "DOOM-style-Game", "doome"]:
        db = scans_e5 / f"{name}_galaxy_master_master.db"
        if db.is_file():
            targets.append((name, db))
    seen_targets = {t[0] for t in targets}
    for name in ["heretic", "hexen", "doom64ex", "srb2"]:
        if name in seen_targets:
            continue
        db = scans_e6 / name / f"{name}_galaxy_master.db"
        if db.is_file():
            targets.append((name, db))

    out_ports = {}
    for tname, tdb in targets:
        P = load_port(tname, tdb, max_n=10000)
        if P.get("skipped") or P["n"] > 10000:
            print(f"Skipping {tname} (n={P['n']} > 10000)", flush=True)
            del P
            gc.collect()
            continue
        # Map P -> linuxdoom via Seed-and-Extend
        if tname == "linuxdoom":
            matched_ld = {i: i for i in range(P["n"])}
        else:
            cost = cdist(P["xd"], ld["xd"], metric="euclidean")
            cost /= (np.median(cost) + 1e-12)
            T = BL.fused_gw(cost, P["hm"], ld["hm"], alpha=0.5, eps=0.05, outer=40)
            best_r = np.argmax(T, axis=1)
            best_q = np.argmax(T, axis=0)
            seeds = [(qi, int(best_r[qi]), float(T[qi, best_r[qi]]))
                     for qi in range(P["n"]) if best_q[best_r[qi]] == qi]
            seeds.sort(key=lambda x: -x[2])
            k_seed = max(3, int(round(0.15 * len(seeds))))
            top_seeds = seeds[:k_seed]
            del cost, T
            def valid_ld_pair(qi: int, rc: int) -> bool:
                la, lb = int(P["locs"][qi]), int(ld["locs"][rc])
                return (
                    np.linalg.norm(P["xd"][qi] - ld["xd"][rc]) <= 0.65
                    and min(la, lb) >= 5
                    and min(la, lb) / max(la, lb) >= 0.40
                )

            delta = np.median(P["comp"][[s[0] for s in top_seeds]] - ld["comp"][[s[1] for s in top_seeds]], axis=0)
            matched_ld = {qi: ri for qi, ri, _ in seeds if valid_ld_pair(qi, ri)}
            used_r = set(matched_ld.values())
            r_snorm = (ld["comp"] + delta) / np.maximum(np.linalg.norm(ld["comp"] + delta, axis=1, keepdims=True), 1e-9)
            for _ in range(3):
                cand = []
                for qi in range(P["n"]):
                    if qi in matched_ld:
                        continue
                    qn = [u for u in P["nbrs"][qi] if u in matched_ld]
                    if not qn:
                        continue
                    rc_cnt = defaultdict(int)
                    for u in qn:
                        for rc in ld["nbrs"][matched_ld[u]]:
                            if rc not in used_r:
                                rc_cnt[rc] += 1
                    for rc, cnt in rc_cnt.items():
                        cand.append((float(np.dot(P["cnorm"][qi], r_snorm[rc])) + 0.1 * cnt, qi, rc))
                cand.sort(key=lambda x: -x[0])
                for _, qi, rc in cand:
                    if qi in matched_ld or rc in used_r:
                        continue
                    if valid_ld_pair(qi, rc):
                        matched_ld[qi] = rc
                        used_r.add(rc)
            matched_ld = {qi: rc for qi, rc in matched_ld.items() if valid_ld_pair(qi, rc)}

        # Assign secondary donors for unmatched functions
        donor_match = {}
        allowed_donors = eligible_donors(tname, ctrl_names)
        unmatched = [qi for qi in range(P["n"]) if qi not in matched_ld]
        if unmatched and allowed_donors:
            P_unm_xd = P["xd"][unmatched]
            P_unm_tree = cKDTree(P_unm_xd)
            for dname, D in donors.items():
                if dname not in allowed_donors:
                    continue
                da, ia = D["tree"].query(P_unm_xd, k=1, distance_upper_bound=0.25)
                db, ib = P_unm_tree.query(D["xd"], k=1, distance_upper_bound=0.25)
                for u_idx, qi in enumerate(unmatched):
                    if qi in donor_match:
                        continue
                    ri = int(ia[u_idx])
                    if ri < len(D["xd"]) and np.isfinite(da[u_idx]) and int(ib[ri]) == u_idx:
                        la, lb = P["locs"][qi], D["locs"][ri]
                        if la >= 5 and lb >= 5 and abs(la - lb) / max(la, lb) <= 0.30:
                            donor_match[qi] = (dname, D["names"][ri])

        # Assign every function to one of the 16 call-graph communities:
        # 1) Direct linuxdoom Seed-and-Extend match -> its linuxdoom community
        # 2) Unmatched -> propagate community from call-graph neighbors (3 rounds)
        # 3) Still disconnected -> nearest linuxdoom descriptor community
        func_comm = {}
        for qi, ri in matched_ld.items():
            func_comm[qi] = int(ld_comm[ri])

        for _ in range(4):
            updates = {}
            for qi in range(P["n"]):
                if qi in func_comm:
                    continue
                nbr_comms = [func_comm[u] for u in P["nbrs"][qi] if u in func_comm]
                if nbr_comms:
                    counts = defaultdict(int)
                    for c in nbr_comms:
                        counts[c] += 1
                    updates[qi] = max(counts.items(), key=lambda x: x[1])[0]
            if not updates:
                break
            func_comm.update(updates)

        still_unassigned = [qi for qi in range(P["n"]) if qi not in func_comm]
        if still_unassigned:
            _, nearest_ld = ld["tree"].query(P["xd"][still_unassigned], k=1)
            for qi, ldi in zip(still_unassigned, nearest_ld.tolist(), strict=True):
                func_comm[qi] = int(ld_comm[ldi])

        # Build 16 tracks: each track has list of [func_name, loc, donor_or_null, ref_name_or_null]
        tracks = [[] for _ in range(len(track_labels))]
        for qi in range(P["n"]):
            fn = P["names"][qi]
            loc = int(P["locs"][qi])
            cid = func_comm[qi]
            if qi in matched_ld:
                ri = matched_ld[qi]
                tracks[cid].append([fn, loc, "linuxdoom", ld["names"][ri]])
            elif qi in donor_match:
                dname, d_fn = donor_match[qi]
                tracks[cid].append([fn, loc, dname, d_fn])
            else:
                tracks[cid].append([fn, loc, None, None])

        out_ports[tname] = {
            "meta": f"{'/'.join(P['langs'])} • {P['n']:,} funcs • {int(np.sum(P['locs'])):,} LOC",
            "tracks": tracks,
        }
        print(f"Exported {tname:16s}: linuxdoom={len(matched_ld):4d}, donor={len(donor_match):3d}, novel={P['n']-len(matched_ld)-len(donor_match):4d}", flush=True)
        del P
        gc.collect()

    payload = {"subsystems": track_labels, "ports": out_ports}
    out_json.write_text(json.dumps(payload), encoding="utf-8")
    print(f"Wrote {out_json} ({out_json.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
