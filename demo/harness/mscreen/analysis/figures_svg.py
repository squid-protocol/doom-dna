"""E15 figures as inline SVG (no dependencies): phenotype heatmap, rank-recovery curves, group-correspondence matrix, neighbourhood bars. Colours are CSS variables (light/dark in the report page);
sequential single-hue scale for magnitude, the first three validated categorical slots for series, numbered brackets (not colours) for groups."""
import html
import numpy as np
RAMP = ["#e8f1fc", "#b6d3f5", "#6aa6ea", "#257de0", "#124d94"]
def _hex(c): return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
def ramp(v):
    v = min(max(v, 0.0), 1.0) * (len(RAMP) - 1); i = min(int(v), len(RAMP) - 2); t = v - i; a, b = _hex(RAMP[i]), _hex(RAMP[i + 1])
    return "#%02x%02x%02x" % tuple(round(a[k] + (b[k] - a[k]) * t) for k in range(3))
def esc(s): return html.escape(str(s), quote=True)
def heatmap(F, rows, cols, labels, title, cw=7, rh=5):
    """F: functions x demos kill fractions (NaN = not observed); rows/cols: names; labels: group id per row (rows already ordered by cluster). Numbered brackets mark the groups."""
    n, m = F.shape; left, top = 74, 34; W, H = left + m * cw + 12, top + n * rh + 24; o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}" class="viz">', f'<text x="0" y="14" class="t1">{esc(title)}</text>']
    o.append('<defs><pattern id="na" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="4" height="4" fill="var(--surface-2)"/><line x1="0" y1="0" x2="0" y2="4" stroke="var(--grid)" stroke-width="1"/></pattern></defs>')
    for i in range(n):
        for j in range(m):
            v = F[i, j]; fill = "url(#na)" if np.isnan(v) else ramp(v); tip = f"{rows[i]} | {cols[j]}: " + ("not observed" if np.isnan(v) else f"{v:.2f} of lesions break it")
            o.append(f'<rect x="{left + j * cw}" y="{top + i * rh}" width="{cw - 1}" height="{rh - 1}" fill="{fill}"><title>{esc(tip)}</title></rect>')
    start = 0
    for i in range(1, n + 1):
        if i == n or labels[i] != labels[start]:
            y0, y1 = top + start * rh, top + i * rh
            o.append(f'<line x1="{left - 8}" x2="{left - 8}" y1="{y0 + 1}" y2="{y1 - 2}" stroke="var(--axis)" stroke-width="1"/><text x="{left - 12}" y="{(y0 + y1) / 2 + 3}" text-anchor="end" class="t2">{labels[start]}</text>'); start = i
    prev = None
    for j, c in enumerate(cols):
        if c[0] != prev: o.append(f'<text x="{left + j * cw}" y="{top - 6}" class="t2">{esc(c[0])}</text>'); prev = c[0]
    o.append(f'<text x="0" y="{H - 6}" class="t2">rows grouped by phenotype group (numbers on the left); columns are demos by family; darker = more of the function\'s lesions break the demo</text></svg>'); return "".join(o)
def lines(series, xmax, title, xlabel, ylabel):
    """series: list of (name, xs, ys); up to three series in categorical slots 1-3, direct labels at the right end plus a legend"""
    W, H, L, B, T, R = 520, 300, 54, 44, 34, 110; cols = ["var(--series-1)", "var(--series-2)", "var(--series-3)"]
    sx = lambda x: L + (W - L - R) * x / xmax; sy = lambda y: H - B - (H - B - T) * y
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}" class="viz"><text x="0" y="14" class="t1">{esc(title)}</text>']
    for g in (0, .25, .5, .75, 1): o.append(f'<line x1="{L}" x2="{W - R}" y1="{sy(g)}" y2="{sy(g)}" stroke="var(--grid)"/><text x="{L - 6}" y="{sy(g) + 3}" text-anchor="end" class="t2">{g:.2f}</text>')
    o.append(f'<line x1="{L}" x2="{W - R}" y1="{sy(0)}" y2="{sy(0)}" stroke="var(--axis)"/>')
    for k in (1, xmax // 4, xmax // 2, xmax): o.append(f'<text x="{sx(k)}" y="{H - B + 14}" text-anchor="middle" class="t2">{k}</text>')
    for (name, xs, ys), c in zip(series, cols):
        pts = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(xs, ys)); o.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2"><title>{esc(name)}</title></polyline><text x="{W - R + 6}" y="{sy(ys[-1]) + 3}" class="t2">{esc(name)}</text>')
    o.append(f'<text x="{(L + W - R) / 2}" y="{H - 8}" text-anchor="middle" class="t2">{esc(xlabel)}</text><text x="12" y="{(T + H - B) / 2}" transform="rotate(-90 12 {(T + H - B) / 2})" text-anchor="middle" class="t2">{esc(ylabel)}</text></svg>'); return "".join(o)
def matrix(M, rl, cl, title):
    """group correspondence counts (rows: port A groups, columns: port B groups)"""
    n, m = M.shape; c = 26; L, T = 44, 40; W, H = L + m * c + 8, T + n * c + 22; mx = max(1, M.max()); o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}" class="viz"><text x="0" y="14" class="t1">{esc(title)}</text>']
    for i in range(n):
        o.append(f'<text x="{L - 6}" y="{T + i * c + 17}" text-anchor="end" class="t2">{esc(rl[i])}</text>')
        for j in range(m):
            v = M[i, j]; o.append(f'<rect x="{L + j * c}" y="{T + i * c}" width="{c - 2}" height="{c - 2}" fill="{ramp(v / mx)}"><title>{esc(f"A group {rl[i]} / B group {cl[j]}: {int(v)} functions")}</title></rect>' + (f'<text x="{L + j * c + c / 2 - 1}" y="{T + i * c + 16}" text-anchor="middle" class="t3{" w" if v / mx > .55 else ""}">{int(v)}</text>' if v else ""))
    for j in range(m): o.append(f'<text x="{L + j * c + c / 2 - 1}" y="{T - 5}" text-anchor="middle" class="t2">{esc(cl[j])}</text>')
    o.append(f'<text x="0" y="{H - 5}" class="t2">name-agree functions: chocolate-doom group (rows) by managed-doom group (columns)</text></svg>'); return "".join(o)
def bars(pairs, title):
    """paired horizontal bars (group: observed vs null mean call-graph distance)"""
    n = len(pairs); W, rh, L = 520, 16, 56; H = 40 + n * rh + 22; mx = max(1e-9, max(max(a, b) for _, a, b in pairs)); sx = lambda v: L + (W - L - 20) * v / mx
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}" class="viz"><text x="0" y="14" class="t1">{esc(title)}</text>']
    for i, (g, a, b) in enumerate(pairs):
        y = 30 + i * rh; o.append(f'<text x="{L - 6}" y="{y + 9}" text-anchor="end" class="t2">group {esc(g)}</text><rect x="{L}" y="{y}" width="{sx(a) - L:.1f}" height="5" rx="2" fill="var(--series-1)"><title>{esc(f"group {g}: observed {a:.2f} hops")}</title></rect><rect x="{L}" y="{y + 7}" width="{sx(b) - L:.1f}" height="5" rx="2" fill="var(--series-2)"><title>{esc(f"group {g}: random-group mean {b:.2f} hops")}</title></rect>')
    o.append(f'<rect x="{W - 190}" y="6" width="9" height="9" rx="2" fill="var(--series-1)"/><text x="{W - 176}" y="14" class="t2">observed</text><rect x="{W - 110}" y="6" width="9" height="9" rx="2" fill="var(--series-2)"/><text x="{W - 96}" y="14" class="t2">random groups</text></svg>'); return "".join(o)
