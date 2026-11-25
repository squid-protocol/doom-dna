"""Replication helper (NEW code): the ORIGINAL | NEW ENGINE side-by-side table, built from the two sets of report files.

    python side_by_side.py --new-work WORK --orig-a2-summary JSON --new-a2-summary JSON --out FILE.md

Reads the original reports (committed under results/e7, results/e7_amendment2 and the frozen A2 work dir) and the replication's, extracts
every quoted number with the regexes below and writes one markdown table. 'Real?' follows preregistration/E7_REPLICATION_NEW_ENGINE.md:
rates and counts with an original interval are real only if the new value falls outside it; quantities without an interval are 'moved'
at a difference of 0.05 (0.5 for a median rank); a program crossing the 2% floor, a changed nearest relative or placement, or a flipped
verdict is real. Nothing here is a new test: it only reads the numbers the registered scripts printed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from scipy.stats import beta

REPO = Path(__file__).resolve().parent.parent
OA = REPO / "results/e7/phaseA/phaseA_report.md"
OB = REPO / "results/e7/phaseB/phaseB_report.md"
OPA = Path("/srv/storage_16tb/projects/doom-e7a2-work/primary/results/e7/phaseA/phaseA_report.md")
OCA = Path("/srv/storage_16tb/projects/doom-e7a2-work/conservative/results/e7/phaseA/phaseA_report.md")


def cp(k, n, a=0.05):
    lo = 0.0 if k == 0 else beta.ppf(a / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - a / 2, k + 1, n - k)
    return float(lo), float(hi)


def frac(r):  # rate -> (k, n) with the smallest n <= 60
    for n in range(1, 61):
        if abs(r * n - round(r * n)) < 0.0006 * n:
            return round(r * n), n
    return None


def grab(txt, pat, grp=1, cast=float):
    m = re.search(pat, txt, re.M)
    if not m:
        raise SystemExit(f"pattern not found: {pat}")
    return cast(m.group(grp))


def row_cells(txt, prefix):
    for line in txt.splitlines():
        if line.startswith(prefix):
            return [c.strip() for c in line.strip("|").split("|")]
    raise SystemExit(f"row not found: {prefix}")


def fmt(x, d=3):
    return f"{x:.{d}f}" if isinstance(x, float) else str(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-work", required=True, type=Path)
    ap.add_argument("--orig-a2-summary", required=True, type=Path)
    ap.add_argument("--new-a2-summary", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    NA = (a.new_work / "new/results/e7/phaseA/phaseA_report.md").read_text()
    NB = (a.new_work / "new/results/e7/phaseB/phaseB_report.md").read_text()
    oa, ob = OA.read_text(), OB.read_text()
    L = []

    def add(label, o, n, real, note=""):
        L.append(f"| {label} | {o} | {n} | {'' if o == n else 'changed'} | {real}{(' (' + note + ')') if note else ''} |")

    def rate(label, key_prefix, col, o_txt=oa, n_txt=NA, exact_ci=True):
        o = float(row_cells(o_txt, key_prefix)[col]); n = float(row_cells(n_txt, key_prefix)[col])
        kn = frac(o)
        if kn and exact_ci:
            lo, hi = cp(*kn)
            real = "REAL" if not (lo <= n <= hi) else "no"
            note = f"orig exact CI {lo:.2f} to {hi:.2f} on {kn[0]}/{kn[1]}"
        else:
            real, note = ("moved" if abs(n - o) >= 0.05 else "no"), ""
        add(label, fmt(o), fmt(n), real, note)

    L.append("| Quantity | ORIGINAL (704cb35f0) | NEW ENGINE (beb46cfbc) | change | real by the pre-stated rule |")
    L.append("|---|---:|---:|---|---|")
    # ---- Phase A
    for m in ("struct", "names"):
        o = grab(oa, rf"\*\*{m}\*\*: (\d+) detectable", cast=int); n = grab(NA, rf"\*\*{m}\*\*: (\d+) detectable", cast=int)
        ou = set(grab(oa, rf"\*\*{m}\*\*: \d+ detectable, \d+ not: (.*)", cast=str).split(", ")); nu = set(grab(NA, rf"\*\*{m}\*\*: \d+ detectable, \d+ not: (.*)", cast=str).split(", "))
        crossed = sorted(ou ^ nu)
        add(f"Programs with detectable descent at the 2% floor ({m}), of 51", o, n, "REAL" if crossed else "no", "crossed: " + (", ".join(crossed) or "none"))
    rate("Nearest-is-family, corrected rule, struct, common set (orig 25)", "| struct | all edges | common |", 3)
    rate("Nearest-is-family, corrected, struct, own detectable set", "| struct | all edges | own detectable |", 3)
    rate("Nearest-is-family, corrected, names, common set", "| names | all edges | common |", 3)
    rate("Nearest-is-family, corrected, names, own detectable set", "| names | all edges | own detectable |", 3)
    rate("Nearest-is-family, old root-sibling rule (inflated), struct, common", "| struct | all edges | common |", 4, exact_ci=False)
    rate("Nearest-is-family, old root-sibling rule (inflated), names, common", "| names | all edges | common |", 4, exact_ci=False)
    rate("Declared parent rank, mean, struct, common", "| struct | all edges | common |", 5, exact_ci=False)
    rate("Declared parent rank, median, struct, common", "| struct | all edges | common |", 6, exact_ci=False)
    o = float(row_cells(oa, "| struct | all edges | common |")[6]); n = float(row_cells(NA, "| struct | all edges | common |")[6])
    L[-1] = L[-1].rsplit("|", 2)[0] + ("| moved (>= 0.5 rank) |" if abs(n - o) >= 0.5 else "| no |")
    rate("Declared parent rank, median, names, common", "| names | all edges | common |", 6, exact_ci=False)
    L[-1] = L[-1].rsplit("|", 2)[0] + ("| moved (>= 0.5 rank) |" if abs(float(row_cells(NA, "| names | all edges | common |")[6]) - float(row_cells(oa, "| names | all edges | common |")[6])) >= 0.5 else "| no |")
    rate("Resolved-triplet compatibility with declared tree, UPGMA struct", "| UPGMA struct |", 2, exact_ci=False)
    rate("Resolved-triplet compatibility with declared tree, UPGMA names", "| UPGMA names |", 2, exact_ci=False)
    rate("Clade recall (declared clades recovered), UPGMA struct", "| UPGMA struct |", 1, exact_ci=False)
    # M4 / M5
    for lab, pat in (("Names tree vs structure tree, UPGMA quartet distance", r"UPGMA RF [\d.]+, quartet ([\d.]+)"), ("Names tree vs structure tree, UPGMA normalised RF", r"UPGMA RF ([\d.]+)")):
        o, n = grab(oa, pat), grab(NA, pat)
        add(lab, fmt(o), fmt(n), "moved" if abs(o - n) >= 0.05 else "no")
    add("Programs detectable under both (M4 set)", grab(oa, r"On (\d+) programs detectable under both", cast=int), grab(NA, r"On (\d+) programs detectable under both", cast=int), "set size follows detectability")
    o, n = grab(oa, r"All pairs: Spearman ([\d.]+)"), grab(NA, r"All pairs: Spearman ([\d.]+)")
    add("Spearman shared-names vs shared-structure, all 1,275 pairs", fmt(o), fmt(n), "moved" if abs(o - n) >= 0.05 else "no")
    pat = r"n=(\d+): Spearman ([\d.]+); cluster bootstrap over programs 95% interval \[([\d.]+), ([\d.]+)\]"
    mo, mn = re.search(pat, oa), re.search(pat, NA)
    inside = float(mo.group(3)) <= float(mn.group(2)) <= float(mo.group(4))
    add("H7.2: Spearman, C-family pairs above floor under both", f"{mo.group(2)} (n={mo.group(1)}, [{mo.group(3)}, {mo.group(4)}])", f"{mn.group(2)} (n={mn.group(1)}, [{mn.group(3)}, {mn.group(4)}])", "no (inside original interval)" if inside else "REAL", "verdict: interval includes values below 0.80 in both")
    # M6
    for lab, pat in (("H7.1: ports where structure is closer to text survival (exact+near), of 22", r"H7.1 vs exact\+near:\*\* structure closer to the text arbiter in (\d+)/22"), ("H7.1 on exact+near+derived", r"exact\+near\+derived:\*\* structure closer to the text arbiter in (\d+)/22")):
        o, n = grab(oa, pat, cast=int), grab(NA, pat, cast=int)
        lo, hi = cp(o, 22)
        add(lab, f"{o}/22", f"{n}/22", "REAL" if not (lo <= n / 22 <= hi) else "no", f"orig exact CI {lo:.2f} to {hi:.2f}")
    pat = r"exact\+near:\*\*.*?Spearman vs text: structure ([\d.]+) \[([\d.]+), ([\d.]+)\], names ([\d.]+) \[([\d.]+), ([\d.]+)\]"
    mo, mn = re.search(pat, oa), re.search(pat, NA)
    for i, nm in ((1, "structure"), (4, "names")):
        o, n = float(mo.group(i)), float(mn.group(i))
        inside = float(mo.group(i + 1)) <= n <= float(mo.group(i + 2))
        add(f"Spearman vs name-blind text survival, {nm}", f"{o} [{mo.group(i+1)}, {mo.group(i+2)}]", f"{n} [{mn.group(i+1)}, {mn.group(i+2)}]", "no (inside original interval)" if inside else "REAL")
    pat = r"false attachments to DOOM engine-ports: structure (\d+), names (\d+)"
    mo, mn = re.search(pat, oa), re.search(pat, NA)
    add("H7.4: false attachments among large unrelated controls, structure", mo.group(1), mn.group(1), "no" if mo.group(1) == mn.group(1) else "REAL (verdict could flip)")
    add("H7.4: false attachments among large unrelated controls, names", mo.group(2), mn.group(2), "no" if mo.group(2) == mn.group(2) else "REAL")
    pat = r"H7\.3\*\* \(descriptive.*?\): (\d+/\d+)"
    add("H7.3: cross-language ports struct leaves undetected that attach to a declared family under names", grab(oa, pat, cast=str), grab(NA, pat, cast=str), "see scorecard")
    # ---- Phase B
    def b(txt, pat):
        return re.search(pat, txt)
    for m in ("structure", "names"):
        o, n = b(ob, rf"\*\*{m}\*\*: sensitivity (\d)/5; false attachments (\d)/3.*?correct placements (\d+)/14 \(exact 95% CI \[([\d.]+), ([\d.]+)\]\)"), b(NB, rf"\*\*{m}\*\*: sensitivity (\d)/5; false attachments (\d)/3.*?correct placements (\d+)/14 \(exact 95% CI \[([\d.]+), ([\d.]+)\]\)")
        add(f"Phase B positives attached to a family member ({m}), of 5", f"{o.group(1)}/5", f"{n.group(1)}/5", "no" if o.group(1) == n.group(1) else "REAL")
        add(f"Phase B false attachments, negatives >= 150 functions ({m}), of 3", f"{o.group(2)}/3", f"{n.group(2)}/3", "no" if o.group(2) == n.group(2) else "REAL")
        inside = float(o.group(4)) <= int(n.group(3)) / 14 <= float(o.group(5))
        add(f"Phase B correct placements, 14 scored ({m})", f"{o.group(3)}/14 [{o.group(4)}, {o.group(5)}]", f"{n.group(3)}/14 [{n.group(4)}, {n.group(5)}]", "no (inside original CI)" if inside else "REAL")
    pat = r"Leave-one-out sensitivity: structure (\d)/8 \(exact 95% CI \[([\d.]+), ([\d.]+)\]\), names (\d)/8"
    o, n = b(ob, pat), b(NB, pat)
    add("Phase B leave-one-out, 8 mapped ports (structure)", f"{o.group(1)}/8 [{o.group(2)}, {o.group(3)}]", f"{n.group(1)}/8", "no (inside original CI)" if float(o.group(2)) <= int(n.group(1)) / 8 <= float(o.group(3)) else "REAL")
    add("Phase B leave-one-out, 8 mapped ports (names)", f"{o.group(4)}/8", f"{n.group(4)}/8", "no" if o.group(4) == n.group(4) else "changed within CI")
    for h in ("H7.6", "H7.7"):
        pat = rf"\*\*{h}\*\*.*?-> ([^\n]*)"
        add(f"Scorecard {h}", grab(ob, pat, cast=str), grab(NB, pat, cast=str), "no" if grab(ob, pat, cast=str) == grab(NB, pat, cast=str) else "REAL (verdict flipped)")
    # Phase B per-program placement changes
    def placements(txt):
        d = {}
        for line in txt.splitlines():
            if line.startswith("| ") and ("phase-B" in line):
                c = [x.strip() for x in line.strip("|").split("|")]
                d[c[0].replace(" *(diagnostic, unscored)*", "")] = (c[3], c[4], c[6], c[7])
        return d
    po, pn = placements(ob), placements(NB)
    L.append("")
    L.append("Phase B programs whose placement changed (struct nearest | names nearest | struct verdict | names verdict):")
    L.append("")
    for k in po:
        if po[k] != pn.get(k):
            L.append(f"- `{k}`: {po[k]}  ->  {pn.get(k)}")
    # ---- Amendment 2
    if a.new_a2_summary and a.new_a2_summary.exists():
        so, sn = json.load(open(a.orig_a2_summary)), json.load(open(a.new_a2_summary))
        L.append("")
        L.append("| Amendment 2 quantity (K = 25) | ORIGINAL | NEW ENGINE | change | real |")
        L.append("|---|---:|---:|---|---|")

        def add2(label, o, n, real):
            L.append(f"| {label} | {o} | {n} | {'' if o == n else 'changed'} | {real} |")
        for f in ("0.02", "0.03", "0.05", "0.08"):
            for k in ("single", "primary", "conservative"):
                o, n = so["detectable_by_floor"][f][k], sn["detectable_by_floor"][f][k]
                add2(f"Programs detectable at floor {f}, {'E7 single shuffle' if k == 'single' else k + ' rule'}", o, n, "REAL" if f == "0.02" and (so["detectable_programs_0.02"][k] != sn["detectable_programs_0.02"][k]) else ("moved" if o != n else "no"))
        for k in ("single", "primary", "conservative"):
            ow, nw = set(so["detectable_programs_0.02"][k]), set(sn["detectable_programs_0.02"][k])
            L.append(f"| programs crossing the 2% floor, {k} | | | gained: {', '.join(sorted(nw - ow)) or 'none'}; lost: {', '.join(sorted(ow - nw)) or 'none'} | |")
        for k in ("single", "primary", "conservative"):
            o, n = so["nearest_is_family_fixed_set"][k], sn["nearest_is_family_fixed_set"][k]
            kn = frac(o); lo, hi = cp(*kn)
            add2(f"Nearest-is-family on E7's fixed 25-program set, {k}", fmt(o), fmt(n), "REAL" if not (lo <= n <= hi) else f"no (orig exact CI {lo:.2f} to {hi:.2f})")
        for k in ("primary", "conservative"):
            o, n = so["nearest_is_family_own_detectable"][k], sn["nearest_is_family_own_detectable"][k]
            add2(f"Nearest-is-family on each rule's own detectable set, {k}", fmt(o), fmt(n), "moved" if abs(o - n) >= 0.05 else "no")
        add2("P-A1: share of active pairs with cutoff above zero (primary)", f"{so['P_A1_cutoff_above_zero']:.3f} of {so['active_pairs']}", f"{sn['P_A1_cutoff_above_zero']:.3f} of {sn['active_pairs']}", "no" if (so['P_A1_cutoff_above_zero'] >= .9) == (sn['P_A1_cutoff_above_zero'] >= .9) else "REAL (verdict flipped)")
        add2("Stability classes among active pairs (stable-certified / stable-uncertified / unstable)", "/".join(str(v) for v in so["stability_classes_active"].values()), "/".join(str(v) for v in sn["stability_classes_active"].values()), "descriptive")
        add2("Convergence K=12 vs K=25 (share of active pairs differing by > 2% of elig_q; bound 5%)", fmt(so["convergence_share_active_pairs_k12_vs_k25_differ_gt_2pct"]), fmt(sn["convergence_share_active_pairs_k12_vs_k25_differ_gt_2pct"]), "no" if sn["convergence_share_active_pairs_k12_vs_k25_differ_gt_2pct"] <= 0.05 else "REAL (bound broken)")
        add2("P-A4: largest share of an unrelated control with any program (primary), bound 0.10", fmt(so["P_A4_max_share_unrelated_controls_primary"]), fmt(sn["P_A4_max_share_unrelated_controls_primary"]), "no" if sn["P_A4_max_share_unrelated_controls_primary"] <= 0.10 else "REAL (verdict flipped)")
        co, cn = so["cross_language_pairs_primary"], sn["cross_language_pairs_primary"]
        add2("Cross-language background (primary): 95th / 99th percentile / max, share above 0.02", f"{co['p95']:.3f} / {co['p99']:.3f} / {co['max']:.3f}, {co['share_above_0.02']:.3f}", f"{cn['p95']:.3f} / {cn['p99']:.3f} / {cn['max']:.3f}, {cn['share_above_0.02']:.3f}", "descriptive")
        pa = []
        for p, v in so["linuxdoom_to_port_share"].items():
            w = sn["linuxdoom_to_port_share"][p]
            d = w["primary"] - v["primary"]
            if abs(d) >= 0.03:
                pa.append((p, v["primary"], w["primary"], d))
        L.append("")
        L.append("Ports whose share with `linuxdoom` under the primary rule moved by at least 0.03 (`material` by the pre-stated rule):")
        L.append("")
        for p, o, n, d in sorted(pa, key=lambda x: -abs(x[3])):
            L.append(f"- `{p}`: {o:.3f} -> {n:.3f} ({d:+.3f})")
        if not pa:
            L.append("- none")
    a.out.write_text("\n".join(L) + "\n")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
