"""Build the call-graph subsystem map data for the interactive figure.

1. Finds subsystems directly from ``linuxdoom``'s call graph (no filename rules) by Louvain
   community detection with iterative consensus (Lancichinetti and Fortunato 2012: 100 runs,
   co-association threshold 0.5, resolution 1.0). Groups of fewer than 10 functions are merged
   into the neighbouring group they call most; functions with no stable group (isolated or
   unstable) join the group of their nearest labelled function by measurement. The number of
   subsystems is whatever the graph gives (16 at the default), not a cap.
2. Runs Seed-and-Extend (zero names/paths; the extension follows call-graph neighbours) from
   ``linuxdoom`` onto each port to place its functions on those subsystems.
3. For functions not matched to ``linuxdoom``, checks reciprocal structural twins
   (``BL.descriptors``) against secondary donors (``chocolate-doom``, ``prboom-plus``,
   ``doomgeneric``, ``woof``) to mark likely branch transfers.
4. Writes ``article/subsystem_map_data.json`` with the per-function placement.

The placement reads call edges, so the figure shows *where each port's functions fall among
``linuxdoom``'s subsystems*; it is not an independent measurement of how much architecture a
port preserves (see DOOM-E11).
"""

from __future__ import annotations

import gc
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import networkx as nx
from networkx.algorithms import community as nxc
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist


def discover_communities(n: int, edges: np.ndarray, locs: np.ndarray, desc: np.ndarray, gamma: float = 1.0,
                         nrun: int = 100, tau: float = 0.5, min_group: int = 10):
    """Louvain subsystems with iterative consensus. Returns (node_to_group, groups, info)."""
    G = nx.Graph()
    G.add_nodes_from(range(n))
    G.add_edges_from((int(u), int(v)) for u, v in edges.tolist() if u != v)
    nodes = [v for v in range(n) if G.degree(v) > 0]
    idx = {v: i for i, v in enumerate(nodes)}
    H0 = G.subgraph(nodes)

    def labels(graph, seed, weight=None):
        lab = np.zeros(len(nodes), dtype=np.int64)
        for k, c in enumerate(nxc.louvain_communities(graph, resolution=gamma if weight is None else 1.0, seed=seed, weight=weight)):
            for v in c:
                lab[idx[v]] = k
        return lab

    parts = [labels(H0, s) for s in range(nrun)]
    m = len(nodes)
    for _ in range(8):
        D = np.zeros((m, m), dtype=np.float32)
        for p in parts:
            D += (p[:, None] == p[None, :])
        D /= len(parts)
        D[D < tau] = 0
        np.fill_diagonal(D, 0)
        r, c = np.nonzero(np.triu(D))
        if len(r) == 0:
            break
        H = nx.Graph()
        H.add_nodes_from(nodes)
        H.add_weighted_edges_from((nodes[a], nodes[b], float(D[a, b])) for a, b in zip(r.tolist(), c.tolist()))
        new = [labels(H, s, weight="weight") for s in range(nrun)]
        agree = all(len(set(zip(new[0].tolist(), q.tolist()))) == len(set(new[0].tolist())) == len(set(q.tolist())) for q in new[1:5])
        parts = new
        if agree:
            break
    lab = parts[0].copy()
    unstable = np.asarray((D > 0).sum(1) == 0)
    full = -np.ones(n, dtype=np.int64)
    for v in nodes:
        if not unstable[idx[v]]:
            full[v] = lab[idx[v]]
    # merge groups smaller than min_group into the group they call most
    sizes = np.bincount(full[full >= 0]) if (full >= 0).any() else np.array([0])
    small = {g for g in range(len(sizes)) if 0 < sizes[g] < min_group}
    for g in sorted(small):
        members = np.flatnonzero(full == g)
        votes = defaultdict(int)
        for v in members.tolist():
            for u in G.neighbors(v):
                if full[u] >= 0 and full[u] not in small:
                    votes[int(full[u])] += 1
        if votes:
            full[members] = max(votes.items(), key=lambda x: x[1])[0]
    # unlabelled (isolated or unstable): nearest labelled function by measurement
    lab_idx = np.flatnonzero(full >= 0)
    rest = np.flatnonzero(full < 0)
    if len(rest) and len(lab_idx):
        _, nn = cKDTree(desc[lab_idx]).query(desc[rest], k=1)
        full[rest] = full[lab_idx[nn]]
    # order by total LOC, largest first; relabel 0..K-1
    gids = [g for g in np.unique(full) if g >= 0]
    order = sorted(gids, key=lambda g: -int(locs[full == g].sum()))
    remap = {g: i for i, g in enumerate(order)}
    node_to_group = np.array([remap[int(g)] for g in full], dtype=np.int64)
    groups = [np.flatnonzero(node_to_group == i).tolist() for i in range(len(order))]
    info = {"method": "Louvain with iterative consensus", "resolution": gamma, "runs": nrun, "threshold": tau,
            "min_group_functions": min_group, "groups": len(groups), "functions": int(n),
            "functions_without_calls": int(n - len(nodes)), "unstable_functions": int(unstable.sum()),
            "group_sizes": [len(g) for g in groups]}
    return node_to_group, groups, info


def main() -> int:
    sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
    from structural_fingerprint import blind as BL
    from structural_fingerprint import features as F
    from structural_fingerprint.fingerprint import build
    from structural_fingerprint.reference import load_reference
    from structural_fingerprint.scan_io import load_scan, resolve_scans

    scans_main = Path("/srv/storage_16tb/projects/doom-e7-work/scans/704cb35f0")  # engine 704cb35f0, the DOOM-E7 scans
    out_json = Path(__file__).resolve().parents[2] / "article" / "subsystem_map_data.json"

    ref = load_reference("portable")
    bp = BL.BlindParams()
    keep_feat_cols = [
        i for i, n in enumerate(ref.feature_names)
        if n not in ("log_complexity", "func_internal_density")
    ]

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
        )[:, keep_feat_cols]
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
    ld_comm, ld_groups, comm_info = discover_communities(ld["n"], ld["edges"], ld["locs"], ld["xd"])

    # Label each discovered community by its top-2 hub functions
    deg_ld = np.zeros(ld["n"], dtype=np.int64)
    for u, v in ld["edges"].tolist():
        if u != v:
            deg_ld[u] += 1; deg_ld[v] += 1

    track_labels = []
    for cid, g in enumerate(ld_groups):
        hubs = [ld["names"][i] for i in sorted(g, key=lambda i: (-deg_ld[i], -ld["locs"][i]))[:2]]
        track_labels.append(f"S{cid + 1:02d}: " + " / ".join(hubs))

    print(f"Found {len(track_labels)} call-graph subsystems (sizes {comm_info['group_sizes']}):")
    for idx, lbl in enumerate(track_labels):
        print(f"  {idx + 1:02d}. {lbl}")

    # Secondary donors (masked against linuxdoom)
    donors_spec = [
        ("chocolate-doom", resolve_scans([scans_main / "chocolate-doom"])[0]),
        ("prboom-plus", resolve_scans([scans_main / "prboom-plus"])[0]),
        ("doomgeneric", resolve_scans([scans_main / "doomgeneric"])[0]),
        ("woof", resolve_scans([scans_main / "woof"])[0]),
    ]
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
        if tname in ctrl_names or tname in {"linuxdoom", "srb2"}:
            return set()
        tyear = PORT_YEAR.get(tname, 2022)
        return {d for d in DOOM_PORT_DONORS if d != tname and PORT_YEAR[d] < tyear}

    # Targets: the programs of the previously published figure, scanned at engine 704cb35f0 (heretic, hexen
    # and doom64ex came from an older partial-engine experiment whose scans no longer exist and are dropped).
    wanted = ["chocolate-doom", "crispy-doom", "doomgeneric", "doomretro", "prboom-plus", "dsda-doom", "woof", "eternity", "odamex", "srb2",
              "room4doom", "gore", "managed-doom", "mochadoom", "rust-doom", "doom-wasm", "fastdoom", "puredoom", "doom-ios", "doom-ascii",
              "helion", "edge-classic", "nugget-doom", "inter-doom", "sdl-doom", "doom3do", "sqldoom", "doomf77", "doom-scheme", "doo-cr",
              "kocoa-doom", "fsharp-doom", "cssdoom", "doom-fx", "fps-cob", "agentic-cobol-doom-cc", "agentic-cobol-doom-codex", "mood",
              "freedoom", "dartdoom", "lua", "quake", "quake2"]
    ctrl_names = {"lua", "quake", "quake2"}
    targets = [("linuxdoom", resolve_scans([scans_main / "linuxdoom"])[0])]
    for name in wanted:
        d = scans_main / name
        if d.is_dir():
            try:
                targets.append((name, resolve_scans([d])[0]))
            except Exception as e:  # noqa: BLE001
                print(f"Skipping {name}: {e}", flush=True)

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
            del cost
            def valid_ld_pair(qi: int, rc: int) -> bool:
                la, lb = int(P["locs"][qi]), int(ld["locs"][rc])
                return (
                    np.linalg.norm(P["xd"][qi] - ld["xd"][rc]) <= 0.45
                    and min(la, lb) >= 5
                    and min(la, lb) / max(la, lb) >= 0.45
                )

            delta = np.median(P["comp"][[s[0] for s in top_seeds]] - ld["comp"][[s[1] for s in top_seeds]], axis=0)
            r_snorm = (ld["comp"] + delta) / np.maximum(np.linalg.norm(ld["comp"] + delta, axis=1, keepdims=True), 1e-9)

            def valid_cal_pair(qi: int, rc: int) -> bool:
                la, lb = int(P["locs"][qi]), int(ld["locs"][rc])
                return (
                    float(np.dot(P["cnorm"][qi], r_snorm[rc])) >= 0.70
                    and min(la, lb) >= 5
                    and min(la, lb) / max(la, lb) >= 0.20
                )

            matched_ld = {qi: ri for qi, ri, _ in top_seeds}
            used_r = set(matched_ld.values())
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
                    matched_ld[qi] = rc
                    used_r.add(rc)

            # Check whether Seed-and-Extend found a coherent call-graph backbone
            # (separates true DOOM ports/translations from unrelated controls without raw xd bias).
            sup = [
                sum(1 for u in P["nbrs"][qi] if u in matched_ld and matched_ld[u] in ld["nbrs"][rc])
                for qi, rc in matched_ld.items()
            ]
            tr = [float(T[qi, rc] / (T[qi].max() + 1e-12)) for qi, rc in matched_ld.items()]
            strong_fgw = sum(1 for x in tr if x >= 0.5) / max(1, len(tr))
            mean_sup = float(np.mean(sup)) if sup else 0.0
            del T

            if strong_fgw >= 0.20 and mean_sup >= 2.10:
                # Include all reciprocal FGW seeds that pass the calibrated gate too
                for qi, ri, _ in seeds:
                    if qi not in matched_ld and ri not in used_r and valid_cal_pair(qi, ri):
                        matched_ld[qi] = ri
                        used_r.add(ri)
                matched_ld = {qi: rc for qi, rc in matched_ld.items() if valid_cal_pair(qi, rc)}
            else:
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

    payload = {"subsystems": track_labels, "ports": out_ports, "provenance": {"engine": "704cb35f0", "subsystems": comm_info, "placement": "Seed-and-Extend (reads call-graph neighbours); donors by structural twins"}}
    out_json.write_text(json.dumps(payload), encoding="utf-8")
    print(f"Wrote {out_json} ({out_json.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
