"""E14 confirmatory analysis exactly as registered (preregistration/E14_SAME_BREAK_SAME_ROLE.md section E). Usage: python analyze_confirm.py <jsonl> <out.md>"""
import collections, json, math, random, statistics, sys
from pathlib import Path
rows = [json.loads(l) for l in open(sys.argv[1])]; ok = [r for r in rows if r["status"] == "ok"]; out = []; P = out.append
by = collections.defaultdict(dict)
for r in ok: by[(r["ref"], r["site"])][r["role"]] = r
strat = {r["ref"]: r["stratum"] for r in rows}
def fail(r, demos): return {d for d in demos if r["demos"][d]["outcome"] == "killed"}
def reach(r): return {d for d, v in r["demos"].items() if v["reach"]}
def pair(a, b, only=None):
    both = reach(a) & reach(b)
    if only: both = {d for d in both if d.startswith(only)}
    if not both: return None
    fa, fb = fail(a, both), fail(b, both)
    if not fa and not fb: return dict(kind="survive")
    sh = fa & fb; u = fa | fb
    return dict(kind="kill", jac=len(sh) / len(u), tic=(sum(abs(a["demos"][d]["tic"] - b["demos"][d]["tic"]) <= 1 for d in sh) / len(sh)) if sh else None,
                field=(sum(a["demos"][d]["field"] == b["demos"][d]["field"] for d in sh) / len(sh)) if sh else None)
def boot(vals, B=10000, seed=1):
    rng = random.Random(seed); n = len(vals)
    if n == 0: return (float("nan"),) * 2
    ms = sorted(statistics.mean(rng.choice(vals) for _ in range(n)) for _ in range(B)); return ms[int(0.025 * B)], ms[int(0.975 * B)]
def fmean(d): return {k: statistics.mean(v) for k, v in d.items() if v}
def matched(role, only=None, st=None):
    d = collections.defaultdict(list)
    for (rf, si), v in by.items():
        if st and strat.get(rf) != st: continue
        if "ch" in v and role in v:
            p = pair(v["ch"], v[role], only)
            if p and p["kind"] == "kill": d[rf].append(p["jac"])
    return fmean(d)
def permutation(st, only=None):
    d = collections.defaultdict(list)
    for (rf, si), v in by.items():
        if strat.get(rf) != st or "ch" not in v: continue
        for (rf2, si2), v2 in by.items():
            if rf2 != rf and "md:match" in v2 and v2["md:match"]["kind"] == v["ch"]["kind"]:
                p = pair(v["ch"], v2["md:match"], only)
                if p and p["kind"] == "kill": d[rf].append(p["jac"])
    return fmean(d)
def samefile(st, port="md", only=None):
    d = collections.defaultdict(list)
    for (rf, si), v in by.items():
        if strat.get(rf) != st: continue
        if "ch" in v and f"{port}:ctl" in v:
            p = pair(v["ch"], v[f"{port}:ctl"], only)
            if p and p["kind"] == "kill": d[rf].append(p["jac"])
    return fmean(d)
def diff(a, b):
    ks = sorted(set(a) & set(b)); v = [a[k] - b[k] for k in ks]; return len(ks), (statistics.mean(v) if v else float("nan")), boot(v), v
P("# E14 confirmatory results (registered analysis)\n"); P(f"{len(rows)} mutants attempted, {len(ok)} built; functions: agree {len({r['ref'] for r in rows if r['stratum']=='agree'})}, disagree {len({r['ref'] for r in rows if r['stratum']=='disagree'})}.\n")
P("## Build, reach, kill, crash by role\n"); P("| role | attempted | built | reached | killed (>=1) | crash/hang |\n|---|---|---|---|---|---|")
for role in ("ch", "pb:match", "pb:ctl", "md:match", "md:name", "md:ctl"):
    a = [r for r in rows if r["role"] == role]; b = [r for r in a if r["status"] == "ok"]
    if a: P(f"| {role} | {len(a)} | {len(b)} | {sum(r['reached'] > 0 for r in b)} | {sum(r['killed'] > 0 for r in b)} | {sum(r['crash'] > 0 for r in b)} |")
P("\n## Registered predictions\n"); res = []
m = matched("md:match", st="agree"); c = permutation("agree"); n, dd, ci, _ = diff(m, c)
s1 = n >= 10 and dd >= 0.40 and ci[0] > 0.25; power = n >= 10
res.append(("S1 (primary)", "agree, managed-doom: matched - permutation control >= 0.40, 95% lower bound > 0.25, >= 10 functions", f"{n} functions; diff {dd:+.2f} (95% {ci[0]:+.2f} to {ci[1]:+.2f}); matched mean {statistics.mean(m.values()) if m else float('nan'):.2f}; control mean {statistics.mean(c.values()) if c else float('nan'):.2f}", "PASSED" if s1 else ("INCONCLUSIVE (power)" if not power else "FAILED")))
sf = samefile("agree"); n2, d2, ci2, _ = diff(m, sf); res.append(("S2", "matched - same-file control >= 0.30", f"{n2} functions; {d2:+.2f} (95% {ci2[0]:+.2f} to {ci2[1]:+.2f})", "PASSED" if n2 and d2 >= 0.30 else "FAILED"))
ma, md_ = matched("md:match", st="agree"), matched("md:match", st="disagree"); ok3 = len(ma) >= 6 and len(md_) >= 6
if ma and md_:
    va, vd = list(ma.values()), list(md_.values()); d3 = statistics.mean(va) - statistics.mean(vd); rng = random.Random(2); bs = sorted(statistics.mean(rng.choice(va) for _ in va) - statistics.mean(rng.choice(vd) for _ in vd) for _ in range(10000))
    res.append(("S3", "agree - disagree matched Jaccard >= 0.30 (>= 6 functions each)", f"agree {len(va)} fn mean {statistics.mean(va):.2f}; disagree {len(vd)} fn mean {statistics.mean(vd):.2f}; diff {d3:+.2f} (95% {bs[250]:+.2f} to {bs[9750]:+.2f})", ("PASSED" if d3 >= 0.30 else "FAILED") if ok3 else "INCONCLUSIVE (n<6 per stratum)"))
else: res.append(("S3", "agree - disagree", "no kill pairs in one stratum", "INCONCLUSIVE"))
res.append(("S4", "role-blind only if the matched - control interval lies inside +-0.15", f"interval {ci[0]:+.2f} to {ci[1]:+.2f}", ("ROLE-BLIND" if (ci[0] > -0.15 and ci[1] < 0.15) else ("INCONCLUSIVE" if ci[0] < 0.40 else "not role-blind")) if power else "INCONCLUSIVE (power)"))
tics, flds = [], []
for (rf, si), v in by.items():
    if strat.get(rf) == "agree" and "ch" in v and "md:match" in v:
        p = pair(v["ch"], v["md:match"])
        if p and p["kind"] == "kill" and p["tic"] is not None: tics.append(p["tic"]); flds.append(p["field"])
res.append(("S5", "tic (+-1) and first-field agreement >= 0.80 (agree, managed-doom)", f"{len(tics)} kill pairs; tic {statistics.mean(tics) if tics else float('nan'):.2f}; field {statistics.mean(flds) if flds else float('nan'):.2f}", "PASSED" if tics and statistics.mean(tics) >= 0.8 and statistics.mean(flds) >= 0.8 else "FAILED"))
w = [0, 0, 0]
for (rf, si), v in by.items():
    if strat.get(rf) == "disagree" and "ch" in v and "md:match" in v and "md:name" in v:
        a, b = pair(v["ch"], v["md:match"]), pair(v["ch"], v["md:name"]); ja = a["jac"] if a and a["kind"] == "kill" else None; jb = b["jac"] if b and b["kind"] == "kill" else None
        if ja is None and jb is None: continue
        w[0 if (jb or 0) > (ja or 0) else (1 if (ja or 0) > (jb or 0) else 2)] += 1
nn = w[0] + w[1]; pv = (2 * sum(math.comb(nn, i) for i in range(0, min(w[0], w[1]) + 1)) / 2 ** nn) if nn else 1.0
res.append(("S6", "name-oracle target closer to the reference break than the matcher target (sign test)", f"name closer {w[0]}, matcher closer {w[1]}, ties {w[2]}; two-sided p {min(1.0, pv):.3f}", "PASSED" if w[0] > w[1] else "FAILED"))
pb = matched("pb:match", st="agree"); res.append(("S7", "prboom-plus agree stratum matched Jaccard >= 0.70", f"{len(pb)} functions; mean {statistics.mean(pb.values()) if pb else float('nan'):.2f}", "PASSED" if pb and statistics.mean(pb.values()) >= 0.70 else "FAILED"))
P("| prediction | registered | observed | result |\n|---|---|---|---|")
for r in res: P("| " + " | ".join(r) + " |")
P("\n## Sensitivity and descriptive\n")
for label, only in (("all 42 demos", None), ("bot demos only", "b"), ("sticky only", "s"), ("chaos only", "c")):
    mm, cc = matched("md:match", only, "agree"), permutation("agree", only); n_, d_, ci_, _ = diff(mm, cc); P(f"* agree stratum, managed-doom, {label}: {n_} functions with kill pairs; matched - control {d_:+.2f} (95% {ci_[0]:+.2f} to {ci_[1]:+.2f})")
P(f"* per stratum, managed-doom matched: agree {len(ma)} functions, disagree {len(md_)} functions with kill pairs; prboom-plus matched: agree {len(pb)}, disagree {len(matched('pb:match', st='disagree'))}")
P("* strict (not dead-angle-ignoring) comparison: not stored by this run's outcome records; not computed (deviation from the registered list).\n")
P("## Per function (matched Jaccard, managed-doom and prboom-plus; kill pairs only)\n"); P("| function | stratum | md matched | pb matched |\n|---|---|---|---|")
mdall, pball = matched("md:match"), matched("pb:match")
for rf in sorted(strat): P(f"| {rf} | {strat[rf]} | {mdall.get(rf, float('nan')):.2f} | {pball.get(rf, float('nan')):.2f} |")
Path(sys.argv[2]).write_text("\n".join(out))
