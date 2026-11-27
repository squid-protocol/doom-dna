"""DoomGraph v1 group construction (E18 amendment A1): multi-anchor consensus.  A PURE function over in-memory static evidence
(no database, no file, no phenotype/reach/behaviour data; same boundary as groups.py).

Rule (frozen by commit before the v1 build is looked at; weights/thresholds are the v0 constants, not retuned):
  1. Anchor clustering.  The anchor ports (default: the five reference engines) are joint anchors.  Between anchor instances of different
     ports the pair score is the best of the direct E12 tier weight / name-agree weight (+ ARB_BONUS when the text arbiter confirms it).
     For each anchor instance u and each other anchor port q, the best partner is the unique argmax; a link u-v is an AGREEING link when
     each is the other's unique best in its port and the score >= MIN_JOIN.  Agreeing links are united strongest first (ties: lower ids);
     a union that would put two instances of one port into one group is refused, and both ends take role 'conflict'.  A member whose
     strongest edge to a different group is within CONFLICT_MARGIN of its in-group score also takes 'conflict' (alternative row kept).
     Group id = lowest instance id of the cluster (role 'anchor'); the other members are 'member' or 'conflict'.
  2. Non-anchor instances collect candidate groups from channels D (direct E12 edge to a group member), N (name-agree), H (2-hop through one
     other-port instance to a group member; no path longer than 2 hops), A (text-arbiter confirmation of a supported candidate, never alone).
     score = best of D/N/H (+ ARB_BONUS if confirmed); join the best group when score >= MIN_JOIN.  Tie-breakers in fixed order: score, more
     channels, lineage-consistent path, more supporting anchor ports (direct evidence), call-graph support (pass-1 labels), lower group id.
  3. Roles (precedence conflict > split > merge > member): conflict = runner-up within CONFLICT_MARGIN of the best; split = tied direct
     evidence for several groups or several arbiter confirmations; merge = several instances of one port in one group.
  4. A group with no member from another port (a lone anchor instance nobody joined) is not a group: its instance is listed ungrouped
     ('anchor_singleton'); instances without any anchor evidence are ungrouped ('no_candidate' / 'below_threshold').
No random draws; deterministic port/instance order."""
from collections import defaultdict
from common import (TIER_W, NAME_W, ARB_W, ARB_BONUS, HOP2_FACTOR, MIN_JOIN, CONFLICT_MARGIN, MAX_CAND_ROWS, MIN_LOC_EDGE, jdump)
from groups import lineage_chain
RESOLVE_CONFLICTS_UNGROUPED = True   # attempt 2 (see BUILD_REPORT_V1.md): a non-anchor conflict does not join a group

def build_groups_v1(instances, edges, calls, parent, anchor_ports, control_ports):
    """same inputs as groups.build_groups with anchor_ports a collection.
    Returns dict(members={inst: [row,...]} incl. anchor-port instances, ungrouped={inst: reason}, anchors=[group ids])."""
    port = {i: d["port"] for i, d in instances.items()}
    size = {i: d.get("size") or 0 for i, d in instances.items()}
    ctrl = set(control_ports); aports = set(anchor_ports)
    adj = defaultdict(list)           # x -> [(y, ch, weight, tier)]
    arb = {}                          # (lo, hi) -> verdict
    for e in sorted(edges, key=lambda e: (e["a"], e["b"], e["tier"], e["source"])):
        a, b = e["a"], e["b"]
        if port[a] in ctrl or port[b] in ctrl or port[a] == port[b]: continue
        t = e["tier"]
        if e["source"] == "e7_arbiter":
            if e["verdict"] in ARB_W: arb[(min(a, b), max(a, b))] = e["verdict"]
            continue
        if e["source"] == "name": w, ch = NAME_W, "N"
        else:
            if t not in TIER_W: continue
            if t in ("S", "ext1", "ext2", "ext3") and not e.get("gate"): continue
            if size[a] < MIN_LOC_EDGE or size[b] < MIN_LOC_EDGE: continue
            w, ch = TIER_W[t], "D"
        adj[a].append((b, ch, w, t)); adj[b].append((a, ch, w, t))
    anchors = sorted(i for i in instances if port[i] in aports and port[i] not in ctrl)
    aset = set(anchors)
    # ---- 1. anchor clustering
    def pair(u, v):
        best = None
        for y, ch, w, t in adj.get(u, ()):
            if y == v and (best is None or w > best[0]): best = (w, ch, t)
        if best is None: return None
        bonus = ARB_BONUS if (min(u, v), max(u, v)) in arb else 0
        return (best[0] + bonus, best[1], best[2])
    ps = {}                                   # (u, v) -> (score, ch, tier), both directions
    for u in anchors:
        for y, ch, w, t in adj.get(u, ()):
            if y in aset and (u, y) not in ps:
                p = pair(u, y)
                ps[(u, y)] = p; ps[(y, u)] = p
    bestp = {}                                # (u, port q) -> unique-best partner or None (tie)
    for u in anchors:
        byq = defaultdict(list)
        for y, ch, w, t in adj.get(u, ()):
            if y in aset: byq[port[y]].append(y)
        for q, ys in byq.items():
            sc = {y: ps[(u, y)][0] for y in set(ys)}
            m = max(sc.values()); top = sorted(y for y, s in sc.items() if s == m)
            bestp[(u, q)] = top[0] if len(top) == 1 else None
    links = sorted(((ps[(u, v)][0], u, v) for (u, q), v in bestp.items()
                    if v is not None and u < v and bestp.get((v, port[u])) == u and ps[(u, v)][0] >= MIN_JOIN), key=lambda t: (-t[0], t[1], t[2]))
    root = {i: i for i in anchors}; ports_of = {i: {port[i]} for i in anchors}; clash = set()
    def find(x):
        while root[x] != x: root[x] = root[root[x]]; x = root[x]
        return x
    for s, u, v in links:
        ru, rv = find(u), find(v)
        if ru == rv: continue
        if ports_of[ru] & ports_of[rv]: clash |= {u, v}; continue
        if rv < ru: ru, rv = rv, ru
        root[rv] = ru; ports_of[ru] |= ports_of[rv]
    clusters = defaultdict(list)
    for i in anchors: clusters[find(i)].append(i)
    gid_of = {}; rep_of = {}
    for r, ms in clusters.items():
        g = min(ms)
        for i in ms: gid_of[i] = g
        rep_of[g] = ms
    members = defaultdict(list); ungrouped = {}; conflict_rows = defaultdict(list)
    keep_groups = set()
    for g, ms in sorted(rep_of.items()):
        if len(ms) < 2: continue              # lone anchor: not a group yet (may still gain members below)
        for u in ms:
            if u == g:
                members[u] = [dict(group=g, rank=1, role="anchor", confidence=1.0, evidence=jdump({"ch": "anchor"}))]; continue
            inn = [(ps[(u, v)][0], v) for v in ms if v != u and (u, v) in ps]
            s0, v0 = max(inn) if inn else (0, None)
            out = [(ps[(u, y)][0], y) for y, ch, w, t in adj.get(u, ()) if y in aset and gid_of[y] != g and len(rep_of[gid_of[y]]) >= 2 and (u, y) in ps]
            s1, y1 = max(out) if out else (0, None)
            conflict = (u in clash) or (s1 >= MIN_JOIN and s1 >= CONFLICT_MARGIN * max(s0, 1))
            tinfo = ps[(u, v0)] if v0 is not None else (0, "D", "")
            ev = {"ch": tinfo[1], "chs": tinfo[1], "t": tinfo[2], "hop": 1, "via": "", "s": round(s0, 1), "lin": 1, "cs": 0, "arb": ""}
            rows = [dict(group=g, rank=1, role="conflict" if conflict else "member", confidence=round(min(1.0, s0 / 100.0), 3), evidence=jdump(ev))]
            if conflict and y1 is not None and gid_of[y1] != g:
                ev2 = dict(ev); ev2["s"] = round(s1, 1); ev2["t"] = ps[(u, y1)][2]; ev2["ch"] = ev2["chs"] = ps[(u, y1)][1]
                rows.append(dict(group=gid_of[y1], rank=2, role="conflict", confidence=round(min(1.0, s1 / 100.0), 3), evidence=jdump(ev2)))
            members[u] = rows
    def agroup(a):
        return gid_of[a]
    # ---- 2. candidate groups for non-anchor instances
    chain = {}
    def lin(p):
        if p not in chain: chain[p] = set(lineage_chain(p, parent)) | {p}
        return chain[p]
    nb = defaultdict(set)
    for c, d in calls:
        if c in port and d in port and port[c] == port[d] and c != d: nb[c].add(d); nb[d].add(c)
    cand = {}
    for x in sorted(instances):
        if x in aset or port[x] in ctrl: continue
        c = defaultdict(dict); sup = defaultdict(dict)   # sup[g][anchor port] = best direct weight
        for y, ch, w, t in adj.get(x, ()):
            if y in aset:
                g = agroup(y); k = (w, t, 1, "")
                if ch not in c[g] or k[0] > c[g][ch][0]: c[g][ch] = k
                sup[g][port[y]] = max(sup[g].get(port[y], 0), w)
            else:
                for a, ch2, w2, t2 in adj.get(y, ()):
                    if a in aset and port[a] != port[x] and port[y] != port[x]:
                        g = agroup(a); w3 = HOP2_FACTOR * min(w, w2)
                        if "H" not in c[g] or w3 > c[g]["H"][0] or (w3 == c[g]["H"][0] and port[y] < c[g]["H"][3]):
                            c[g]["H"] = (w3, t if w <= w2 else t2, 2, port[y])
        for y, ch, w, t in adj.get(x, ()):
            if y in aset and (min(x, y), max(x, y)) in arb and agroup(y) in c:
                v = arb[(min(x, y), max(x, y))]
                if "A" not in c[agroup(y)] or ARB_W[v] > c[agroup(y)]["A"][0]: c[agroup(y)]["A"] = (ARB_W[v], v, 1, "")
        if c: cand[x] = (c, sup)
    # arbiter edges exist only for pairs with a match edge in adj? no: arbiter pairs are separate edges; add them as confirmation-only
    for (a, b), v in sorted(arb.items()):
        for x, y in ((a, b), (b, a)):
            if y in aset and x in cand:
                g = agroup(y)
                if g in cand[x][0] and "A" not in cand[x][0][g]: cand[x][0][g]["A"] = (ARB_W[v], v, 1, "")
    def keyof(x, g):
        ch = cand[x][0][g]
        base = max((ch[k][0] for k in ("D", "N", "H") if k in ch), default=0.0)
        score = base + (ARB_BONUS if ("A" in ch and base > 0) else 0.0)
        nch = sum(1 for k in ("D", "N", "H", "A") if k in ch)
        paths = {ch[k][3] for k in ("H",) if k in ch}
        lok = 1 if ("D" in ch or "N" in ch or any(p in lin(port[x]) for p in paths)) else 0
        return score, nch, lok, len(cand[x][1].get(g, ()))
    def agg(x, g):     # attempt 3: consensus weight = sum over the supporting anchor ports of their best direct weight
        return sum(cand[x][1].get(g, {}).values())
    label = {}
    for x, (cs, sup) in cand.items():
        r = sorted(cs, key=lambda g: (-agg(x, g),) + tuple(-v for v in keyof(x, g)) + (g,))
        if keyof(x, r[0])[0] >= MIN_JOIN and (len(r) == 1 or keyof(x, r[0]) != keyof(x, r[1])): label[x] = r[0]
    gadj = defaultdict(set)
    for c_, d_ in calls:
        if c_ in aset and d_ in aset and gid_of[c_] != gid_of[d_]: gadj[gid_of[c_]].add(gid_of[d_]); gadj[gid_of[d_]].add(gid_of[c_])
    def csupport(x, g):
        return sum(1 for n in nb.get(x, ()) if label.get(n) is not None and (label[n] == g or label[n] in gadj[g]))
    for x in sorted(instances):
        if x in aset or port[x] in ctrl: continue
        if x not in cand: ungrouped[x] = "no_candidate"; continue
        cs, sup = cand[x]
        order = sorted(cs, key=lambda g: (-agg(x, g),) + tuple(-v for v in keyof(x, g)) + (-csupport(x, g), g))
        k0 = keyof(x, order[0])
        if k0[0] < MIN_JOIN: ungrouped[x] = "below_threshold"; continue
        tops = {}
        for chn in ("D", "N", "H"):
            ws = {g: cs[g][chn][0] for g in cs if chn in cs[g]}
            if ws:
                m = max(ws.values()); tops[chn] = {g for g, w in ws.items() if w == m}
        topgroups = set().union(*tops.values()) if tops else set()
        conflict = False
        if len(order) > 1:
            k1 = keyof(x, order[1])
            if k1[0] >= CONFLICT_MARGIN * k0[0] and k1[0] >= MIN_JOIN: conflict = True
        split_groups = set(tops.get("D", set())) | {g for g in cs if "A" in cs[g]}
        role = "conflict" if conflict else ("split" if len(split_groups) > 1 else "member")
        keep = ([order[0]] + [g for g in order[1:] if (g in topgroups or g in split_groups) and keyof(x, g)[0] >= MIN_JOIN])[:MAX_CAND_ROWS]
        if conflict and RESOLVE_CONFLICTS_UNGROUPED:
            ungrouped[x] = "conflict"
        for rk, g in enumerate(keep, 1):
            ch = cs[g]; sc, nch, lok, ns = keyof(x, g)
            bestch = max((k for k in ("D", "N", "H") if k in ch), key=lambda k: (ch[k][0], k == "D", k == "N"), default="A")
            ti = ch[bestch]
            ev = {"ch": bestch, "chs": "".join(k for k in ("D", "N", "H", "A") if k in ch), "t": ti[1], "hop": ti[2], "via": ti[3],
                  "s": round(sc, 1), "lin": lok, "cs": csupport(x, g), "arb": ch["A"][1] if "A" in ch else ""}
            (conflict_rows[x] if x in ungrouped else members[x]).append(dict(group=g, rank=rk + (1 if x in ungrouped else 0), role=role, confidence=round(min(1.0, sc / 100.0), 3), evidence=jdump(ev)))
    # groups that gained members from other ports become real groups; lone anchors are ungrouped
    for g, ms in sorted(rep_of.items()):
        gained = any(port[x] != port[g] for x, rows in members.items() if rows[0]["group"] == g and x not in aset)
        if len(ms) >= 2 or gained:
            keep_groups.add(g)
            if g not in members:   # representative of a group that only gained non-anchor members
                members[g] = [dict(group=g, rank=1, role="anchor", confidence=1.0, evidence=jdump({"ch": "anchor"}))]
        else:
            ungrouped[g] = "anchor_singleton"
    # non-anchor members pointing at a never-kept group cannot happen (they make it kept); drop rows of ungrouped anchors
    for u in list(members):
        if u in ungrouped: members.pop(u)
    for x, rows in conflict_rows.items():      # unresolved conflicts: no rank-1 group; the candidate groups stay as explicit alternative rows (rank >= 2)
        members[x] = [r for r in rows if r["group"] in keep_groups]
        if not members[x]: del members[x]
    for u in members: members[u] = [r for r in members[u] if r["rank"] == 1 or r["group"] in keep_groups]
    # merges: several rank-1 instances of one port in one group
    cnt = defaultdict(lambda: defaultdict(list))
    for x, rows in members.items():
        if x not in ungrouped: cnt[rows[0]["group"]][port[x]].append(x)
    for g, byport in cnt.items():
        for p, xs in byport.items():
            if len(xs) > 1:
                for x in xs:
                    for r in members[x]:
                        if r["group"] == g and r["role"] == "member": r["role"] = "merge"
    return dict(members=dict(members), ungrouped=ungrouped, anchors=sorted(keep_groups))
