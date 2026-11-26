"""E14 pilot analysis (non-confirmatory): coverage, survivors, alignment, and agreement of matched pairs versus controls. Usage: python analyze_pilot.py <jsonl> <out.md>"""
import json, sys, itertools, collections, statistics
from pathlib import Path
rows = [json.loads(l) for l in open(sys.argv[1])]; out = []; P = out.append
ok = [r for r in rows if r["status"] == "ok"]
P("# E14 pilot results (non-confirmatory; Phase 0)\n"); P(f"{len(rows)} mutants built or attempted; seed {rows[0]['seed']}; 42 demos (20 sticky, 10 chaos, 12 bot); scored against each port's own clean run on the common columns (world fingerprint included, no RNG index).\n")
P("## Build, coverage and survival by port and role\n")
P("| port:role | attempted | built | reached by >=1 demo | killed (>=1 demo) | killed among reached | crash/hang |\n|---|---|---|---|---|---|---|")
for key in ("ch", "pb:match", "pb:name", "md:match", "md:name"):
    a = [r for r in rows if r["role"] == key]
    if not a: continue
    b = [r for r in a if r["status"] == "ok"]; rch = [r for r in b if r["reached"] > 0]; kl = [r for r in b if r["killed"] > 0]; klr = [r for r in rch if r["killed"] > 0]; cr = [r for r in b if r["crash"] > 0]
    P(f"| {key} | {len(a)} | {len(b)} | {len(rch)} | {len(kl)} | {len(klr)}/{len(rch)} | {len(cr)} |")
by = collections.defaultdict(dict)
for r in ok: by[(r["ref"], r["site"])][r["role"]] = r
def fail(r): return {d for d, v in r["demos"].items() if v["outcome"] == "killed"}
def reach(r): return {d for d, v in r["demos"].items() if v["reach"]}
def pair(a, b):
    """both reached on shared demos; Jaccard over failing sets restricted to demos reaching both; tic and field agreement on shared failing demos"""
    both = reach(a) & reach(b)
    if not both: return None
    fa, fb = fail(a) & both, fail(b) & both
    if not fa and not fb: return dict(kind="survive", jac=None, n=len(both))
    u = fa | fb; sh = fa & fb
    ta = sum(abs(a["demos"][d]["tic"] - b["demos"][d]["tic"]) <= 1 for d in sh); fa_ = sum(a["demos"][d]["field"] == b["demos"][d]["field"] for d in sh)
    return dict(kind="kill", jac=len(sh) / len(u), n=len(both), tic=ta / len(sh) if sh else None, field=fa_ / len(sh) if sh else None)
P("\n## Aligned site pairs\n"); P(f"Reference-port sites chosen: {len(by)}; with a prboom-plus match: {sum('pb:match' in v for v in by.values())}; with a managed-doom matcher target: {sum('md:match' in v for v in by.values())}.\n")
def stats(pairs):
    k = [p for p in pairs if p and p["kind"] == "kill"]; s = [p for p in pairs if p and p["kind"] == "survive"]
    jac = [p["jac"] for p in k]; tic = [p["tic"] for p in k if p["tic"] is not None]; fld = [p["field"] for p in k if p["field"] is not None]
    return len(pairs), len(k), len(s), (statistics.mean(jac) if jac else float("nan")), (statistics.mean(tic) if tic else float("nan")), (statistics.mean(fld) if fld else float("nan"))
P("## Agreement with chocolate-doom (matched and control pairs)\n"); P("Pairs are (chocolate mutant, target mutant) with both functions reached by at least one common demo. `kill pairs` = at least one of the two killed; the Jaccard is of the failing-demo sets on demos reaching both.\n")
P("| comparison | pairs reached | kill pairs | both survive | mean Jaccard (kill pairs) | tic agree (+-1) | first-field agree |\n|---|---|---|---|---|---|---|")
ctl = {}
for key in ("pb:match", "pb:name", "md:match", "md:name"):
    prs = [pair(v["ch"], v[key]) for v in by.values() if "ch" in v and key in v]; prs = [p for p in prs if p]
    n, k, s, j, t, f = stats(prs); P(f"| {key} (matched) | {n} | {k} | {s} | {j:.2f} | {t:.2f} | {f:.2f} |")
    # control: chocolate mutant paired with the same port's mutant of a DIFFERENT reference function, same operator kind
    cp = []
    for (rf, si), v in by.items():
        for (rf2, si2), v2 in by.items():
            if rf2 != rf and key in v2 and "ch" in v and v["ch"]["kind"] == v2[key]["kind"]: cp.append(pair(v["ch"], v2[key]))
    cp = [p for p in cp if p]; n, k, s, j, t, f = stats(cp); P(f"| {key} (control: other function, same operator) | {n} | {k} | {s} | {j:.2f} | {t:.2f} | {f:.2f} |"); ctl[key] = cp
P("\n## Where the matcher and the function names disagree (same reference function, two candidate targets)\n")
P("| ref function | port | matcher target | name target | Jaccard vs matcher | Jaccard vs name | winner |\n|---|---|---|---|---|---|---|")
for port in ("pb", "md"):
    for (rf, si), v in sorted(by.items()):
        if "ch" in v and f"{port}:match" in v and f"{port}:name" in v:
            a = pair(v["ch"], v[f"{port}:match"]); b = pair(v["ch"], v[f"{port}:name"]); ja = a["jac"] if a and a["kind"] == "kill" else None; jb = b["jac"] if b and b["kind"] == "kill" else None
            w = "tie/none" if ja is None and jb is None else ("name" if (jb or 0) > (ja or 0) else ("matcher" if (ja or 0) > (jb or 0) else "tie"))
            P(f"| {rf} site {si} | {port} | {v[f'{port}:match']['function']} | {v[f'{port}:name']['function']} | {'-' if ja is None else f'{ja:.2f}'} | {'-' if jb is None else f'{jb:.2f}'} | {w} |")
P("\n## Variance for power (kill pairs, Jaccard, per reference function)\n")
for key in ("pb:match", "md:match"):
    perf = collections.defaultdict(list)
    for (rf, si), v in by.items():
        if "ch" in v and key in v:
            p = pair(v["ch"], v[key])
            if p and p["kind"] == "kill": perf[rf].append(p["jac"])
    m = [statistics.mean(x) for x in perf.values()]
    P(f"* {key}: {len(m)} functions with kill pairs; mean of function means {statistics.mean(m):.2f}; sd between functions {statistics.pstdev(m) if len(m) > 1 else float('nan'):.2f}" if m else f"* {key}: no kill pairs")
P("\n## Detail: every aligned site (reached / killed demos out of 42)\n"); P("| ref | site | kind | ch | pb:match | pb:name | md:match | md:name |\n|---|---|---|---|---|---|---|---|")
for (rf, si), v in sorted(by.items()):
    cell = lambda k: f"{v[k]['reached']}/{v[k]['killed']}" if k in v else ""
    P(f"| {rf} | {si} | {v['ch']['kind'] if 'ch' in v else ''} | {cell('ch')} | {cell('pb:match')} | {cell('pb:name')} | {cell('md:match')} | {cell('md:name')} |")
nb = [r for r in rows if r["status"] != "ok"]; P(f"\nDid not build: {len(nb)} ({collections.Counter(r['role'] for r in nb)})")
Path(sys.argv[2]).write_text("\n".join(out))
