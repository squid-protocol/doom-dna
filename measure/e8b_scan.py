"""DOOM-E8b: pin and scan the progenitors (outcome-blind; Amendment 1 §H). Builds manifest/e8b_pins.csv and scans each pinned commit
with the E7 engine through the E8 runner (export kept, scope pruning as E7/E8).

    python e8b_scan.py
"""
import csv
import datetime
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/measure")
import e8_snap  # noqa: E402  (E8's runner, reused unchanged)

REPO = Path(__file__).resolve().parents[1]
B = Path("/srv/storage_16tb/projects/doom-e7-work/e8b/progenitors")
P = Path("/srv/storage_16tb/projects/temporal-crucible-pool/doom-ports")
OUT = Path("/srv/storage_16tb/projects/doom-e7-work/e8b/snaps")


def git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, errors="replace").stdout.strip()


def full(repo, ref):
    return git(repo, "rev-parse", ref)


def date(repo, sha):
    return datetime.datetime.fromtimestamp(int(git(repo, "log", "-1", "--format=%ct", sha)), datetime.timezone.utc).strftime("%Y-%m-%d")


scope = {r["name"]: r for r in csv.DictReader(open(REPO / "manifest" / "scope.csv"))}
sk = lambda n: (scope[n]["keep"] + "|" + scope[n]["drop"]) if n in scope else ""  # noqa: E731
PINS = [  # name, repo, sha, role, release-date rule
    ("boom-2.02", B / "boom", full(B / "boom", "HEAD"), "primary: prboom-plus (secondary: edge-classic)", "source headers 1999; filter date 1999-12-31"),
    ("mbf-2.03", B / "mbf", full(B / "mbf", "HEAD"), "primary: woof; secondary: eternity", "source headers 1999; filter date 1999-12-31"),
    ("smmu", B / "smmu", full(B / "smmu", "173934b11e86"), "primary: eternity", "last commit 2001-02-25"),
    ("edge@2021-09-17", B / "edge", full(B / "edge", "d7adfc6a5320"), "primary: edge-classic (class C)", "last first-parent commit at or before 2021-10-16"),
    ("crispy-doom@2023-06-26", P / "crispy-doom", "595ecb2e5ee8f03162c24e9a73b369b1fb0450c8", "primary: inter-doom (class C)", "last commit at or before 2023-07-06"),
    ("chocolate-doom@2013-12-10", P / "chocolate-doom", "b9690ac0bbe2b5af137aeb09261aac4478f3fbf8", "primary: doomretro (class C, inferred)", "last commit at or before 2013-12-21"),
    ("winmbf", B / "winmbf", full(B / "winmbf", "HEAD"), "descriptive: woof's own early history (all 32 commits are inside the woof clone)", "2008-06-17 to 2016-08-20"),
    ("prboom-2.5.0", B / "prboom-2.5.0", full(B / "prboom-2.5.0", "HEAD"), "descriptive sibling only (NEWS tags changes taken from PrBoom+)", "release mirror"),
]
rows = []
for name, repo, sha, role, rd in PINS:
    port = name.split("@")[0]
    scope_port = port if port in scope else ""
    rows.append(dict(name=name, repo=str(repo), sha=sha, commit_date=date(repo, sha), scope_key=sk(scope_port), role=role, dating=rd))
with open(REPO / "manifest" / "e8b_pins.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
OUT.mkdir(parents=True, exist_ok=True)
for r in rows:
    m = e8_snap.run_task(dict(port=r["name"], repo=r["repo"], sha=r["sha"], scope_key=r["scope_key"]), OUT)
    print(r["name"], "rc", m.get("rc"), "ctags", m.get("ctags_functions"), "pruned", m.get("pruned"), f"{m.get('seconds')}s", flush=True)
print("done")
