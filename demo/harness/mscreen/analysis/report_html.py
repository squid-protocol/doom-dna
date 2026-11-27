"""E15 results page: one self-contained HTML file (inline SVG, light/dark via CSS variables). build(out, GA, GB, fmap, path) -> writes the page."""
import html, numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform
from roles import *; from tests import usable, tmax, ranks, reach_pheno, l1
from pipeline import verdicts
from exploratory import align_groups
import figures_svg as F
CSS = """:root{color-scheme:light;--surface-1:#fff;--surface-2:#f2f4f7;--text-1:#191919;--text-2:#666;--grid:#e3e6ea;--axis:#9aa0a8;--series-1:#257de0;--series-2:#f47230;--series-3:#00b894;--ok:#0a7a2f;--bad:#b3261e;--mid:#8a5a00}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme=light])){color-scheme:dark;--surface-1:#191919;--surface-2:#262626;--text-1:#efefef;--text-2:#9c9c9c;--grid:#333;--axis:#6b6b6b;--series-1:#338ced;--series-2:#e76624;--series-3:#00a888;--ok:#4cc27a;--bad:#ff8a80;--mid:#e0b04a}}
:root[data-theme=dark]{color-scheme:dark;--surface-1:#191919;--surface-2:#262626;--text-1:#efefef;--text-2:#9c9c9c;--grid:#333;--axis:#6b6b6b;--series-1:#338ced;--series-2:#e76624;--series-3:#00a888;--ok:#4cc27a;--bad:#ff8a80;--mid:#e0b04a}
body{margin:0;background:var(--surface-1);color:var(--text-1);font:15px/1.5 system-ui,sans-serif}main{max-width:960px;margin:0 auto;padding:24px 16px 64px}h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:32px 0 8px}p.sub{color:var(--text-2);margin:0 0 16px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--grid);vertical-align:top}th{color:var(--text-2);font-weight:600}
.chip{display:inline-block;padding:1px 8px;border-radius:10px;font-weight:600;font-size:12px;border:1px solid currentColor;white-space:nowrap}.ok{color:var(--ok)}.bad{color:var(--bad)}.mid{color:var(--mid)}
svg.viz{width:100%;height:auto;max-width:900px;display:block;margin:8px 0}svg .t1{font:600 13px system-ui;fill:var(--text-1)}svg .t2{font:11px system-ui;fill:var(--text-2)}svg .t3{font:10px system-ui;fill:var(--text-1)}svg .t3.w{fill:#fff}
figure{margin:16px 0}figcaption{color:var(--text-2);font-size:13px}"""
def chip(r):
    k = "ok" if r.startswith("PASSED") else ("bad" if r.startswith("FAILED") or r.startswith("not") else "mid"); sym = {"ok": "&#10003;", "bad": "&#10007;", "mid": "?"}[k]
    return f'<span class="chip {k}">{sym} {html.escape(r)}</span>'
def order(h):
    D = h["D"]; leaf = leaves_list(linkage(squareform(D, checks=False), "average")); pos = {v: i for i, v in enumerate(leaf)}; return sorted(range(len(D)), key=lambda i: (h["labels"][i], pos[i]))
def build(out, GA, GB, fmap, path, title="Do function roles form call-graph neighbourhoods that recur across ports?"):
    ctx = out["_ctx"]; v = verdicts(out); fa, fb = fmap; demos = ctx["demos"]; parts = [f"<h1>{html.escape(title)}</h1><p class=sub>E15 mutant screen: chocolate-doom (C) and managed-doom (C#), registered analysis</p>"]
    parts.append("<h2>Registered predictions</h2><table><tr><th>prediction</th><th>observed</th><th>result</th></tr>" + "".join(f"<tr><td>{html.escape(p)}</td><td>{html.escape(o)}</td><td>{chip(r)}</td></tr>" for p, o, r in v) + "</table>")
    for i, nm in enumerate(("chocolate-doom", "managed-doom")):
        ph, h, f = (ctx["phA"], ctx["phB"])[i], ctx["h"][i], (fa, fb)[i]; od = order(h); fids = ph.fids[h["idx"]][od]; idx = h["idx"][od]
        parts.append(f"<h2>Break patterns of {nm} functions</h2><figure>" + F.heatmap(ph.F[idx], [f.loc[x, "name"] for x in fids], demos, [int(h["labels"][j]) for j in od], f"{nm}: fraction of each function's lesions that break each demo (k={h['k']} groups, {len(od)} functions)") + "<figcaption>Hover a cell for the function, demo and value. Groups are numbered on the left; hatched cells were not observed (the demo never executes that function's lesion sites).</figcaption></figure>")
    pairs = ctx["pairs"]
    if len(pairs) >= 4:
        la = ctx["h"][0]["labels"][[p[0] for p in pairs]]; lb = ctx["h"][1]["labels"][[p[1] for p in pairs]]; ca, cb = np.unique(la), np.unique(lb); M = np.array([[((la == a) & (lb == b)).sum() for b in cb] for a in ca])
        parts.append("<h2>Do the groups recur across ports?</h2><figure>" + F.matrix(M, [str(x) for x in ca], [str(x) for x in cb], "Group correspondence over name-agree functions") + "<figcaption>A tight diagonal-like structure (one dominant column per row) means the same role groups appear in both ports.</figcaption></figure>")
        phA, phB = ctx["phA"], ctx["phB"]; ia, ib = np.where(usable(phA))[0], np.where(usable(phB))[0]; sa, sb = phA.sub(ia), phB.sub(ib); T = tmax(phA, phB); pa = np.array([p[0] for p in pairs]); pb = np.array([p[1] for p in pairs])
        rk = ranks(dist(sa.sub(pa), sb, T), pb); N0 = ranks(l1(reach_pheno(ctx["A"], sa.fids[pa], demos), reach_pheno(ctx["B"], sb.fids, demos)), pb); mx = len(ib); xs = list(range(1, mx + 1))
        cdf = lambda r: [float((r <= x).mean()) for x in xs]
        parts.append("<h2>Does a function's break pattern find its partner?</h2><figure>" + F.lines([("break pattern", xs, cdf(rk)), ("clean run counts only", xs, cdf(N0)), ("chance", xs, [x / mx for x in xs])], mx, "Share of name-agree partners found within the top N candidates", "candidates considered (rank)", "share of partners found") + "<figcaption>The break-pattern matcher has to beat the clean-entry-count baseline and chance to count as evidence.</figcaption></figure>")
    for i, (nm, G) in enumerate((("chocolate-doom", GA), ("managed-doom", GB))):
        ph, h, f = (ctx["phA"], ctx["phB"])[i], ctx["h"][i], (fa, fb)[i]; fids = ph.fids[h["idx"]]; Dg, _ = G.sub(fids); files = np.array([f.loc[x, "file"] for x in fids]); cf = files[:, None] != files[None, :]; rng = np.random.default_rng(1); rows = []
        for c in np.unique(h["labels"]):
            ix = np.where(h["labels"] == c)[0]
            if len(ix) < 5: continue
            m = cf[np.ix_(ix, ix)]; obs = (Dg[np.ix_(ix, ix)] * m).sum() / max(1, m.sum()); nulls = []
            for _ in range(200):
                s = rng.choice(len(fids), len(ix), replace=False); mm = cf[np.ix_(s, s)]; nulls.append((Dg[np.ix_(s, s)] * mm).sum() / max(1, mm.sum()))
            rows.append((str(c), float(obs), float(np.mean(nulls))))
        if rows: parts.append(f"<h2>Call-graph neighbourhoods in {nm}</h2><figure>" + F.bars(rows, f"{nm}: mean call distance between functions of a group (different files only)") + "<figcaption>Shorter than the random-group bar means the group's functions sit closer together in the call graph.</figcaption></figure>")
    doc = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Function roles screen</title><style>{CSS}</style></head><body><main>{"".join(parts)}</main></body></html>'
    open(path, "w").write(doc); return doc
