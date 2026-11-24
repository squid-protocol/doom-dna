"""Supplement S-A (text form): how much each port's share with linuxdoom varied across the 25 single decoy shuffles, with E7's value, the conservative and
the primary (pooled) value. Built from draws_long.csv and pair_diagnostics.csv; no manual editing. Output: results/e7_amendment2/SUPPLEMENT_S-A.md"""
import os
import numpy as np, pandas as pd
A = os.environ["E7_A2"].rstrip("/") + "/"
OUT = os.environ["E7_SUPP_OUT"]
dl = pd.read_csv(A + "draws_long.csv"); dg = pd.read_csv(A + "pair_diagnostics.csv")
dl["share"] = dl.twins / dl.elig_q
dg["sp"] = dg.twins_primary / dg.elig_q; dg["sc"] = dg.twins_conservative / dg.elig_q
W = 40; SCALE = 0.6
def bar(lo, med, hi, e7, prim):
    cells = [" "] * W
    pos = lambda v: min(W - 1, int(round(v / SCALE * (W - 1))))
    for i in range(pos(lo), pos(hi) + 1): cells[i] = "-"
    cells[pos(med)] = "|"; cells[pos(e7)] = "E" if cells[pos(e7)] != "|" else "e"; cells[pos(prim)] = "P" if cells[pos(prim)] not in "Ee" else "p"
    return "".join(cells)
def table(q, ports, title):
    rows = []
    for t in ports:
        s = dl[(dl.q == q) & (dl.t == t)].share; g = dg[(dg.q == q) & (dg.t == t)].iloc[0]
        c = g.c_certified; cl = "stable-certified" if c >= 0.9 else "stable-uncertified" if c <= 0.1 else "UNSTABLE"
        rows.append((g.sp, f"| `{t}` | {s.iloc[0]:.3f} | {g.sc:.3f} | {g.sp:.3f} | {s.min():.3f} / {s.quantile(.1):.3f} / {s.median():.3f} / {s.quantile(.9):.3f} / {s.max():.3f} | {c:.2f} | {cl} | `{bar(s.min(), s.median(), s.max(), s.iloc[0], g.sp)}` |"))
    rows.sort(key=lambda r: -r[0])
    return [f"## {title}", "", "| port | E7 (seed 0) | conservative | primary (pooled) | 25 single shuffles: min / p10 / median / p90 / max | c | class | 0 ... 0.6 |", "|---|---:|---:|---:|---|---:|---|---|"] + [r[1] for r in rows] + [""]
ports = sorted(set(dg[dg.q == "linuxdoom"].t), key=lambda t: -dg[(dg.q == "linuxdoom") & (dg.t == t)].sp.iloc[0])
L = ["# Supplement S-A: how much one decoy shuffle can move a result (DOOM-E7 Amendment 2)", "",
     "Built by `measure/e7_supp_table.py` from `draws_long.csv` and `pair_diagnostics.csv` (2,550 ordered pairs, 25 shuffles each; seed 0 is E7's draw). Share = twins / eligible functions of the query. "
     "`c` = fraction of the 25 single shuffles in which the cutoff was above zero (a single shuffle certifies nothing below it). In the bar: `-` spans the min to max of the single shuffles, `|` the median, `E` E7's value, `P` the primary pooled value.", "",
     "How to read it: where the dashes are short and E and P coincide (`chocolate-doom`, `crispy-doom`) a single shuffle was enough. Where the dashes are long or E and P are far apart (`inter-doom`, `fastdoom`, `prboom-plus`) E7's one draw was one of two or more possible answers. Pairs with `c` near 0 and short dashes (`woof`, `srb2`, `gzdoom`) are not noisy; the single-shuffle rule simply cannot certify them, and the pooled rule can.", ""]
L += table("linuxdoom", ports, "`linuxdoom` against each port (all 50)")
L += table("chocolate-doom", ["crispy-doom", "doom-wasm", "doom-ascii", "doomgeneric", "sdl-doom", "inter-doom"], "Reference: `chocolate-doom` against its descendants")
x = dg.assign(cls=pd.cut(dg.c_certified, [-.01, .1, .9, 1.0], labels=["stable-uncertified", "unstable", "stable-certified"]))
act = x[(x.sp >= .02) | (x.sc >= .02)]
L += ["## All pairs", "", f"Active pairs (share at least 0.02 under the primary or conservative rule): {len(act)}. Single-shuffle class: " + ", ".join(f"{k} {v}" for k, v in act.cls.value_counts().items()) + ".",
      "Most unstable pairs: " + ", ".join(f"`{r.q}`>`{r.t}` (c {r.c_certified:.2f}, {r.share_p10:.3f}-{r.share_p90:.3f})" for r in act[act.cls == "unstable"].assign(w=lambda d: d.share_p90 - d.share_p10).sort_values("w", ascending=False).head(8).itertuples()) + "."]
open(OUT, "w").write("\n".join(L) + "\n")
print("wrote", OUT, len(L), "lines")
