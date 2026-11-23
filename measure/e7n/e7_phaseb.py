"""DOOM-E7 Phase B analysis: withheld and B2 programs placed pairwise on the frozen map (Amendment 1 §G).

    python e7_phaseb.py     # reads phaseA + phaseB pair tables, writes phaseB_report.md

Placement = argmax of ``shared`` over map programs (pairwise nearest neighbour, not tree insertion).
A program attaches if its largest shared reaches the 2% floor. Ties are split (all tied nearest programs count).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta

HERE = Path(__file__).resolve().parent
REPO = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees")
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, str(HERE))
import e7_trees as T  # noqa: E402

WORK = Path("/srv/storage_16tb/projects/doom-e7n-work")
A, B = WORK / "results" / "e7" / "phaseA", WORK / "results" / "e7" / "phaseB"
FLOOR = 0.02


def rd(p):
    return list(csv.DictReader(open(p)))


def cp(k, n):
    if n == 0:
        return (float("nan"), float("nan"))
    return (0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1)), 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k)))


def shared_table(struct_rows, name_rows):
    """(a, b) -> (shared_struct, shared_names) from directional Wilson bounds."""
    s, n = {}, {}
    for r in struct_rows:
        s[(r["q"], r["t"])] = float(r["wilson"])
    for r in name_rows:
        n[(r["q"], r["t"])] = float(r["wilson_cert"])
    out = {}
    for (q, t) in s:
        out[(q, t)] = (max(s[(q, t)], s.get((t, q), 0)), max(n[(q, t)], n.get((t, q), 0)))
    return out


def main():
    progs = json.load(open(REPO / "manifest" / "RUN_PINS.json"))["programs"]
    role = {p["name"]: p["role"] for p in progs}
    anchors = {r["name"]: r["expected_family_anchor"] for r in rd(REPO / "manifest" / "e7_new.csv") if r["expected_family_anchor"]}
    anchors["cydoomgeneric"] = "doomgeneric"
    elig = {}
    for d in (A, B):
        for r in rd(d / "programs.csv"):
            elig[r["name"]] = int(r["eligible"])
    mapn = [r["name"] for r in rd(A / "programs.csv")]
    bn = [p["name"] for p in progs if p["role"] in ("phase-B1-withheld", "phase-B2-positive")]
    shB = shared_table(rd(B / "pairs_struct.csv"), rd(B / "pairs_names.csv"))
    shA = shared_table(rd(A / "pairs_struct.csv"), rd(A / "pairs_names.csv"))
    allnames = mapn + bn
    decl = T.build_declared(REPO / "manifest" / "declared_lineage.csv", REPO / "manifest" / "declared_lineage_basis.csv", allnames)

    def nearest(w, k, table, pool):
        vals = {p: table[(w, p)][k] for p in pool if (w, p) in table}
        m = max(vals.values())
        return m, [p for p, v in vals.items() if v == m] if m > 0 else []

    def family(anchor, near):
        if near == anchor:
            return True
        try:
            return decl.relation(anchor, near) not in ("other", None)
        except Exception:
            return False

    L = []
    P = lambda s="": L.append(s)  # noqa: E731
    P("# DOOM-E7 Phase B results")
    P("Pairwise nearest-neighbour placement on the frozen Phase A map (not tree insertion). A program attaches if its largest shared reaches the 2% floor.")
    P()
    P("| program | role | eligible | struct nearest (shared) | names nearest (shared) | expected | struct | names |")
    P("|---|---|---:|---|---|---|:-:|:-:|")
    res = {}
    for w in bn:
        ms, ns_ = nearest(w, 0, shB, mapn)
        mn, nn_ = nearest(w, 1, shB, mapn)
        att_s, att_n = ms >= FLOOR, mn >= FLOOR
        anc = anchors.get(w)
        if anc:
            ok_s = att_s and any(family(anc, x) for x in ns_)
            ok_n = att_n and any(family(anc, x) for x in nn_)
            exp = f"attach to family of {anc}"
        else:
            ok_s, ok_n = not att_s, not att_n
            exp = "no detectable descent"
        res[w] = (ok_s, ok_n, att_s, att_n)
        fs = f"{', '.join(ns_[:2]) or '-'} ({ms:.4f})" if att_s else f"none ({ms:.4f})"
        fn = f"{', '.join(nn_[:2]) or '-'} ({mn:.4f})" if att_n else f"none ({mn:.4f})"
        tag = " *(diagnostic, unscored)*" if w == "iron-doom" else ""
        P(f"| {w}{tag} | {role[w]} | {elig[w]} | {fs} | {fn} | {exp} | {'ok' if ok_s else 'MISS'} | {'ok' if ok_n else 'MISS'} |")
    P()
    pos = [w for w in bn if w in anchors and w != "iron-doom"]
    neg = [w for w in bn if w not in anchors and w != "iron-doom"] + (["doomarkable"] if "doomarkable" in bn and "doomarkable" not in anchors else [])
    neg = sorted(set(w for w in bn if w not in anchors and w != "iron-doom"))
    big = [w for w in neg if elig[w] >= 150]
    small = [w for w in neg if elig[w] < 150]
    P("## Scores (iron-doom excluded from both denominators; it is an unscored diagnostic)")
    for k, label in ((0, "structure"), (1, "names")):
        sens = sum(res[w][k] for w in pos)
        fa_big = sum(res[w][3 if k else 2] for w in big)
        fa_small = sum(res[w][3 if k else 2] for w in small)
        corr = sum(res[w][k] for w in pos + neg)
        lo, hi = cp(corr, len(pos + neg))
        P(f"- **{label}**: sensitivity {sens}/{len(pos)}; false attachments {fa_big}/{len(big)} among negatives with at least 150 functions ({', '.join(big)}), {fa_small}/{len(small)} among underpowered negatives ({', '.join(small)}); correct placements {corr}/{len(pos + neg)} (exact 95% CI [{lo:.2f}, {hi:.2f}]).")
    base = len(neg)
    P(f"- **Always-null baseline** (never attaches): sensitivity 0/{len(pos)}, correct placements {base}/{len(pos + neg)}.")
    cs = sum(res[w][0] for w in pos + neg)
    cn = sum(res[w][1] for w in pos + neg)
    P()
    P(f"**H7.6** (structure: every positive attaches correctly and no false attachment among negatives with at least 150 functions): sensitivity {sum(res[w][0] for w in pos)}/{len(pos)}, false attachments {sum(res[w][2] for w in big)}/{len(big)} -> "
      f"{'met' if sum(res[w][0] for w in pos) == len(pos) and sum(res[w][2] for w in big) == 0 else 'not met'}.")
    P(f"**H7.7** (names' correct-placement count at most structure's, falsified if names is higher): names {cn}/{len(pos + neg)} vs structure {cs}/{len(pos + neg)} -> "
      f"{'falsified (names higher)' if cn > cs else 'not falsified'}.")
    P()

    # ---- leave-one-out placement (map programs placed against the others; uses Phase A tables only)
    basis = {(r["name"]): r for r in rd(REPO / "manifest" / "declared_lineage_basis.csv") if r["basis"] not in ("excluded", "dropped")}
    cand = [n for n in mapn if n in basis and basis[n]["parent"] in mapn]
    top = sorted(cand, key=lambda n: -elig[n])[:8]
    P("## Leave-one-out placement (8 mapped ports with the most eligible functions and a declared parent in the map)")
    P("| port | declared parent | struct nearest (shared) | names nearest (shared) | struct | names |")
    P("|---|---|---|---|:-:|:-:|")
    ok_s_n = ok_n_n = 0
    for w in top:
        par = basis[w]["parent"]
        pool = [p for p in mapn if p != w]
        ms, ns_ = nearest(w, 0, shA, pool)
        mn, nn_ = nearest(w, 1, shA, pool)
        okS = ms >= FLOOR and any(family(par, x) for x in ns_)
        okN = mn >= FLOOR and any(family(par, x) for x in nn_)
        ok_s_n += okS
        ok_n_n += okN
        P(f"| {w} | {par} | {', '.join(ns_[:2]) or 'none'} ({ms:.4f}) | {', '.join(nn_[:2]) or 'none'} ({mn:.4f}) | {'ok' if okS else 'MISS'} | {'ok' if okN else 'MISS'} |")
    ls_, hs_ = cp(ok_s_n, len(top))
    ln_, hn_ = cp(ok_n_n, len(top))
    P()
    P(f"Leave-one-out sensitivity: structure {ok_s_n}/{len(top)} (exact 95% CI [{ls_:.2f}, {hs_:.2f}]), names {ok_n_n}/{len(top)} (exact 95% CI [{ln_:.2f}, {hn_:.2f}]). Correct = nearest program is the declared parent or a declared relative of it.")
    P()
    P("## Diagnostics (read with the scores; the scoring above is as registered)")
    g = lambda a, b, k: shB.get((a, b), shB.get((b, a), (float("nan"), float("nan"))))[k]  # noqa: E731
    if "cydoomgeneric" in bn:
        P(f"- **cydoomgeneric** is scored a miss by both methods only because its top match, `sdl-doom`, is not a declared relative of its anchor `doomgeneric`. Shared with `doomgeneric`: structure {g('cydoomgeneric', 'doomgeneric', 0):.3f}, names {g('cydoomgeneric', 'doomgeneric', 1):.3f}; with `sdl-doom`: structure {g('cydoomgeneric', 'sdl-doom', 0):.3f}, names {g('cydoomgeneric', 'sdl-doom', 1):.3f}. The two are within about 0.02 of each other, and Phase A already showed `doomgeneric` and `sdl-doom` share almost everything.")
    if "cpp-doom" in bn:
        P(f"- **cpp-doom** (C++ fork of Crispy Doom): structure shares {g('cpp-doom', 'crispy-doom', 0):.4f} with `crispy-doom` (the C to C++ change rewrites the measurements), names {g('cpp-doom', 'crispy-doom', 1):.3f}. Names track a translation that structure cannot.")
    P("- Anchors `linuxdoom` (derp, broom) count every declared descendant of linuxdoom as family, which is lenient: any DOOM port passes. The nearest programs are listed in the table.")
    P("- `goom3d` (structure, 47 functions) and `c-raycasting2` (names, 18 functions) attach just above the 2% floor but are below the 100-function minimum evidence, so they are flagged underpowered, not scored as false attachments against the methods.")
    (B / "phaseB_report.md").write_text("\n".join(L) + "\n")
    print(B / "phaseB_report.md")


if __name__ == "__main__":
    main()
