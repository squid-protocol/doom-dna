"""DoomGraph group construction: a PURE function over in-memory static evidence (instances, match edges, call edges, lineage).
It never opens a database or a file, and it is given no phenotype, reach or behaviour data (E18 v2 static-only build boundary;
tests/test_doomgraph.py checks this module's source and its inputs).

Rule (frozen by commit before any hold-out score):
  * one group per anchor-port instance (anchor = linuxdoom; chocolate-doom for the stability run); the anchor instance is its own first member;
  * every other non-control instance collects candidate groups from four evidence channels:
      D  direct E12 tier edge to an anchor instance (weights TIER_W; S/ext only when the pair passed its gate; both ends >= 6 lines),
      N  direct name-agree edge (unique name after prefix stripping in both ports; weight NAME_W),
      H  2-hop chain x - y - anchor through one other port (weight = HOP2_FACTOR * the weaker edge; no path longer than 2 hops),
      A  text-arbiter confirmation of an anchor candidate (adds ARB_BONUS, never creates a candidate alone);
  * score = best of D/N/H (+ ARB_BONUS if confirmed); join the best group when score >= MIN_JOIN;
    tie-breakers in fixed order: more channels, lineage-consistent path, more call-graph support (pass-1 labels of call neighbours), lower anchor inst_id;
  * roles (one per membership row, precedence conflict > split > merge > member): conflict = the runner-up group scores within CONFLICT_MARGIN of the best (comparable evidence for different groups; weaker dissent stays as an alternative row); split = one instance matches several anchors (tied D, or arbiter confirms several); merge = several instances
    of one port in one group.  Alternatives are kept as extra membership rows (rank >= 2), never silently merged.
"""
from collections import defaultdict
from common import (TIER_W, NAME_W, ARB_W, ARB_BONUS, HOP2_FACTOR, MIN_JOIN, CONFLICT_MARGIN, MAX_CAND_ROWS, MIN_LOC_EDGE, jdump)

def lineage_chain(port, parent):
    out, p, seen = [], port, set()
    while p in parent and p not in seen:
        seen.add(p); p = parent[p]; out.append(p)
    return out

def build_groups(instances, edges, calls, parent, anchor_port, control_ports, scope="full"):
    """instances: {inst_id: dict(port, size)}; edges: iterable of dict(a, b, tier, gate, source, verdict) (tier in F0,F1c,S,ext1-3,NAME,TXT; source e12|name|e7_arbiter);
    calls: iterable of (caller, callee); parent: {port: declared parent port}.
    Returns dict(members={inst: [row,...]}, ungrouped={inst: reason}, anchors=[inst ids])."""
    port = {i: d["port"] for i, d in instances.items()}
    size = {i: d.get("size") or 0 for i, d in instances.items()}
    ctrl = set(control_ports)
    adj = defaultdict(list)        # x -> [(y, channel, weight, tier)]
    arb = defaultdict(dict)        # x(port side) -> {anchor inst: verdict}
    for e in sorted(edges, key=lambda e: (e["a"], e["b"], e["tier"], e["source"])):
        a, b = e["a"], e["b"]
        if port[a] in ctrl or port[b] in ctrl: continue
        t = e["tier"]
        if e["source"] == "e7_arbiter":
            if port[a] == anchor_port and port[b] != anchor_port: arb[b][a] = e["verdict"]
            elif port[b] == anchor_port and port[a] != anchor_port: arb[a][b] = e["verdict"]
            continue
        if e["source"] == "name":
            w, ch = NAME_W, "N"
        else:
            if t not in TIER_W: continue
            if t in ("S", "ext1", "ext2", "ext3") and not e.get("gate"): continue
            if size[a] < MIN_LOC_EDGE or size[b] < MIN_LOC_EDGE: continue
            w, ch = TIER_W[t], "D"
        adj[a].append((b, ch, w, t)); adj[b].append((a, ch, w, t))
    anchors = sorted(i for i in instances if port[i] == anchor_port)
    anchor_set = set(anchors)
    # call neighbours inside one port, undirected
    nb = defaultdict(set)
    for c, d in calls:
        if c in port and d in port and port[c] == port[d] and c != d:
            nb[c].add(d); nb[d].add(c)
    chain = {}
    def lin(p):
        if p not in chain: chain[p] = set(lineage_chain(p, parent)) | {p}
        return chain[p]
    cand = {}
    for x in sorted(instances):
        if port[x] == anchor_port or port[x] in ctrl: continue
        c = defaultdict(dict)      # group(anchor inst) -> {channel: (weight, tier, hop, via)}
        px = port[x]
        for y, ch, w, t in adj.get(x, ()):
            if y in anchor_set:
                k = (w, t, 1, "")
                if ch not in c[y] or k[0] > c[y][ch][0]: c[y][ch] = k
            elif port[y] != px:
                for a, ch2, w2, t2 in adj.get(y, ()):
                    if a in anchor_set and port[y] != anchor_port:
                        w3 = HOP2_FACTOR * min(w, w2)
                        if "H" not in c[a] or w3 > c[a]["H"][0] or (w3 == c[a]["H"][0] and port[y] < c[a]["H"][3]):
                            c[a]["H"] = (w3, t if w <= w2 else t2, 2, port[y])
        for a, v in arb.get(x, {}).items():
            if v in ARB_W and (a in c):       # confirmation only: needs another channel's support
                c[a]["A"] = (ARB_W[v], v, 1, "")
        if c: cand[x] = c
    def keyof(x, a, cs):
        ch = cs[a]
        base = max((ch[k][0] for k in ("D", "N", "H") if k in ch), default=0.0)
        score = base + (ARB_BONUS if ("A" in ch and base > 0) else 0.0)
        nch = sum(1 for k in ("D", "N", "H", "A") if k in ch)
        paths = {ch[k][3] for k in ("H",) if k in ch}
        lok = 1 if ("D" in ch or "N" in ch or any(p in lin(port[x]) for p in paths)) else 0
        return score, nch, lok
    # pass 1: unique-argmax labels
    label = {}
    ranked = {}
    for x, cs in cand.items():
        r = sorted(cs, key=lambda a: (-keyof(x, a, cs)[0], -keyof(x, a, cs)[1], -keyof(x, a, cs)[2], a))
        ranked[x] = r
        if keyof(x, r[0], cs)[0] >= MIN_JOIN and (len(r) == 1 or keyof(x, r[0], cs) != keyof(x, r[1], cs)): label[x] = r[0]
    anb = defaultdict(set)
    for c_, d_ in calls:
        if c_ in anchor_set and d_ in anchor_set: anb[c_].add(d_); anb[d_].add(c_)
    def csupport(x, a):
        return sum(1 for n in nb.get(x, ()) if label.get(n) is not None and (label[n] == a or label[n] in anb[a]))
    members = defaultdict(list); ungrouped = {}
    for x in sorted(instances):
        if port[x] in ctrl or x in anchor_set: continue
        if x not in cand: ungrouped[x] = "no_candidate"; continue
        cs = cand[x]
        order = sorted(cs, key=lambda a: (-keyof(x, a, cs)[0], -keyof(x, a, cs)[1], -keyof(x, a, cs)[2], -csupport(x, a), a))
        k0 = keyof(x, order[0], cs)
        if k0[0] < MIN_JOIN: ungrouped[x] = "below_threshold"; continue
        # channel disagreement and splits
        tops = {}
        for chn in ("D", "N", "H"):
            ws = {a: cs[a][chn][0] for a in cs if chn in cs[a]}
            if ws:
                m = max(ws.values()); tops[chn] = {a for a, w in ws.items() if w == m}
        topgroups = set().union(*tops.values()) if tops else set()
        conflict = False     # comparable evidence for a different group (a weaker dissent is resolved by weight and kept as an alternative row)
        if len(order) > 1:
            k1 = keyof(x, order[1], cs)
            if k1[0] >= CONFLICT_MARGIN * k0[0] and k1[0] >= MIN_JOIN: conflict = True
        split_groups = set(tops.get("D", set())) | {a for a in cs if "A" in cs[a]}
        split = len(split_groups) > 1
        role = "conflict" if conflict else ("split" if split else "member")
        keep = [order[0]] + [a for a in order[1:] if (a in topgroups or a in split_groups) and keyof(x, a, cs)[0] >= MIN_JOIN]
        keep = keep[:MAX_CAND_ROWS]
        for rk, a in enumerate(keep, 1):
            ch = cs[a]; sc, nch, lok = keyof(x, a, cs)
            bestch = max((k for k in ("D", "N", "H") if k in ch), key=lambda k: (ch[k][0], k == "D", k == "N"), default="A")
            tinfo = ch[bestch]
            ev = {"ch": bestch, "chs": "".join(k for k in ("D", "N", "H", "A") if k in ch), "t": tinfo[1], "hop": tinfo[2], "via": tinfo[3],
                  "s": round(sc, 1), "lin": lok, "cs": csupport(x, a), "arb": ch["A"][1] if "A" in ch else ""}
            members[x].append(dict(group=a, rank=rk, role=role, confidence=round(min(1.0, sc / 100.0), 3), evidence=jdump(ev)))
    # merges: several rank-1 instances of one port in one group
    cnt = defaultdict(lambda: defaultdict(list))
    for x, rows in members.items():
        cnt[rows[0]["group"]][port[x]].append(x)
    for g, byport in cnt.items():
        for p, xs in byport.items():
            if len(xs) > 1:
                for x in xs:
                    for r in members[x]:
                        if r["group"] == g and r["role"] == "member": r["role"] = "merge"
    return dict(members=dict(members), ungrouped=ungrouped, anchors=anchors)
