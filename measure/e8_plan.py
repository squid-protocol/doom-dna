"""DOOM-E8 snapshot plan builder (Amendment 1 §B, §C, §D.17, §E). Outcome-blind: reads git history only.

Writes, into ``manifest/``: ``e8_plan.csv`` (calendar half-life plan), ``e8_plan_commitcount.csv`` (same fractions of
first-parent commits, 11 lineages), ``e8_grid_pairs.csv`` (semi-annual post-fork grid for the fork-date pairs),
``e8_rescan.csv`` (noise replicates) and ``e8_tasks.csv`` (every distinct scan to run).

    python e8_plan.py
"""

from __future__ import annotations

import bisect
import csv
import datetime
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POOL = Path("/srv/storage_16tb/projects/temporal-crucible-pool")
CONTROLS = Path("/srv/storage_16tb/projects/doom-e7-work/halflife/controls")
FRACTIONS = [1, 1 / 2, 1 / 4, 1 / 8, 1 / 16, 1 / 32, 0]
YEAR = 365.25 * 86400

LINEAGES = {  # name -> stratum (fixed in Amendment 1 B.2)
    "chocolate-doom": "history-preserving", "woof": "history-preserving", "prboom-plus": "history-preserving",
    "eternity": "history-preserving", "odamex": "history-preserving", "gzdoom": "history-preserving",
    "doomretro": "import", "srb2": "import", "fastdoom": "import", "edge-classic": "import", "inter-doom": "import",
}
CHILDREN = {"crispy-doom": "chocolate-doom", "nugget-doom": "woof", "dsda-doom": "prboom-plus"}  # post-fork segments
DESCRIPTIVE = {"managed-doom": "descriptive-cross-language", "helion": "control-rewrite", "rust-doom": "control-rewrite",
               "freedoom": "control-assets"}
EXTERNAL = {  # unrelated C/C++ control histories: name -> (clone path, E7 pinned SHA)
    "curl": (POOL / "curl", "01798a002debb5018d693f7fe6237968218eb808"),
    "nginx": (CONTROLS / "nginx", "2e8440bcdc438f0f1cd03da778a3843ddb3c86d9"),
    "libuv": (CONTROLS / "libuv", "f08538cca14f73e30c89625e473fea3f5f55e300"),
}
PAIRS = [  # child, parent, same_language  (ground truth = last shared first-parent commit)
    ("crispy-doom", "chocolate-doom", True), ("dsda-doom", "prboom-plus", True),
    ("nugget-doom", "woof", True), ("kocoa-doom", "mochadoom", False),
]
NOISE_PORTS = ("woof", "edge-classic")
C_FAMILY = set(LINEAGES) | set(CHILDREN)


def git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, errors="replace").stdout


def history(repo, head):
    """Oldest-first first-parent (sha, committer time), times forced non-decreasing (cumulative max)."""
    out = [l.split() for l in git(repo, "log", "--first-parent", "--format=%H %ct", head).splitlines() if l.strip()]
    out = [(s, int(t)) for s, t in out][::-1]
    cm, fixed = 0, []
    for s, t in out:
        cm = max(cm, t)
        fixed.append((s, cm))
    return fixed


def iso(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d")


def at_or_before(hist, t):
    ts = [x[1] for x in hist]
    return hist[max(bisect.bisect_right(ts, t) - 1, 0)]


def main():
    man = {r["name"]: r for r in csv.DictReader(open(REPO / "manifest" / "manifest.csv"))}
    scope = {r["name"]: r for r in csv.DictReader(open(REPO / "manifest" / "scope.csv"))}
    all_ports = {}
    for n in list(LINEAGES) + list(CHILDREN) + list(DESCRIPTIVE) + [p for _, p, _ in PAIRS] + [c for c, _, _ in PAIRS]:
        if n in man:
            all_ports[n] = (POOL / "doom-ports" / n, man[n]["sha"])
    for n, (path, sha) in EXTERNAL.items():
        all_ports[n] = (path, sha)
    role = {**{n: "lineage" for n in LINEAGES}, **{n: "child-post-fork" for n in CHILDREN}, **DESCRIPTIVE,
            **{n: "control-unrelated" for n in EXTERNAL}}
    hist, head_used = {}, {}
    for n, (repo, sha) in all_ports.items():
        has = bool(git(repo, "cat-file", "-t", sha).strip())
        head_used[n] = sha if has else "HEAD"
        hist[n] = history(repo, head_used[n])

    def scope_key(n):
        s = scope.get(n)
        return (s["keep"] + "|" + s["drop"]) if s else ""

    plan, plan_cc = [], []
    for n in all_ports:
        h = hist[n]
        if not h:
            continue
        o, hd = h[0][1], h[-1][1]
        base = dict(port=n, role=role.get(n, "pair-side"), stratum=LINEAGES.get(n, DESCRIPTIVE.get(n, role.get(n, ""))),
                    first_parent_commits=len(h), same_language=("yes" if n in C_FAMILY or n in EXTERNAL else "no"),
                    scope_key=scope_key(n), head_in_history=int(head_used[n] != "HEAD"))
        for f in FRACTIONS:
            s, t = at_or_before(h, o + f * (hd - o))
            plan.append({**base, "fraction": f, "sha": s, "date": iso(t)})
        if n in LINEAGES:
            for f in FRACTIONS:
                i = round(f * (len(h) - 1))
                plan_cc.append({**base, "fraction": f, "sha": h[i][0], "date": iso(h[i][1])})

    # fork pairs: ground truth = last shared first-parent commit; semi-annual grid after the fork
    grid, truth = [], []
    for c, p, same in PAIRS:
        hc, hp = hist[c], hist[p]
        setc = {s for s, _ in hc}
        shared = [(s, t) for s, t in hp if s in setc]
        fork_sha, fork_t = shared[-1]
        truth.append(dict(child=c, parent=p, same_language=("yes" if same else "no"), fork_sha=fork_sha, fork_date=iso(fork_t)))
        end = min(hc[-1][1], hp[-1][1])
        k = 0
        while fork_t + 0.5 * YEAR * k <= end:
            t = fork_t + 0.5 * YEAR * k
            sc, tc = at_or_before(hc, t)
            sp, tp = at_or_before(hp, t)
            grid.append(dict(child=c, parent=p, step=k, target_date=iso(t), child_sha=sc, child_date=iso(tc),
                             parent_sha=sp, parent_date=iso(tp), same_language=("yes" if same else "no")))
            k += 1

    # noise replicates: every planned commit of two ports is scanned twice more
    rescan = [dict(port=r["port"], sha=r["sha"], replicate=rep) for r in plan if r["port"] in NOISE_PORTS for rep in (1, 2)]

    # distinct scan tasks
    tasks = {}
    def add(port, sha, why):
        repo = all_ports[port][0]
        key = (str(repo), sha, scope_key(port))
        tasks.setdefault(key, dict(port=port, repo=str(repo), sha=sha, scope_key=scope_key(port), why=set()))["why"].add(why)
    for r in plan:
        add(r["port"], r["sha"], "calendar")
    for r in plan_cc:
        add(r["port"], r["sha"], "commitcount")
    for g in grid:
        add(g["child"], g["child_sha"], "grid")
        add(g["parent"], g["parent_sha"], "grid")
    out = REPO / "manifest"
    for name, rows in (("e8_plan.csv", plan), ("e8_plan_commitcount.csv", plan_cc), ("e8_grid_pairs.csv", grid),
                       ("e8_fork_truth.csv", truth), ("e8_rescan.csv", rescan)):
        with open(out / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    trows = [dict(port=t["port"], repo=t["repo"], sha=t["sha"], scope_key=t["scope_key"], why="+".join(sorted(t["why"]))) for t in tasks.values()]
    with open(out / "e8_tasks.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(trows[0]))
        w.writeheader()
        w.writerows(trows)
    print(f"plan rows {len(plan)}, commit-count rows {len(plan_cc)}, grid steps {len(grid)}, rescans {len(rescan)}, distinct scan tasks {len(trows)}")
    for t in truth:
        print(t)


if __name__ == "__main__":
    sys.exit(main())
