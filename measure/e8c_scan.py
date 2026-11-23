"""DOOM-E8c step 2: scan every commit of the dense grid (and of E8's semi-annual grid for arm B) with E8's scanner wrapper. Reuses E8's scan of a commit when it exists
(symlink), otherwise scans it. Nothing is measured here."""
import csv, os, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/measure")
import e8_snap as S
REPO = Path(__file__).resolve().parents[1]
E8M = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/manifest")
OLD = Path("/srv/storage_16tb/projects/doom-e7-work/halflife/snaps")
NEW = Path("/srv/storage_16tb/projects/doom-e8c-work/snaps")
POOL = "/srv/storage_16tb/projects/temporal-crucible-pool/doom-ports/"

scope = {}
for r in csv.DictReader(open(E8M / "e8_tasks.csv")):
    scope.setdefault(r["port"], r["scope_key"])
tasks = {}
for fn in (REPO / "manifest" / "e8c_grid.csv", E8M / "e8_grid_pairs.csv"):
    for r in csv.DictReader(open(fn)):
        if r["child"] not in ("crispy-doom", "dsda-doom", "nugget-doom"):
            continue
        for port, sha in ((r["child"], r["child_sha"]), (r["parent"], r["parent_sha"])):
            tasks[(port, sha)] = dict(port=port, repo=POOL + port, sha=sha, scope_key=scope.get(port, ""))
NEW.mkdir(parents=True, exist_ok=True)
todo = []
for t in tasks.values():
    tag = S.tag(t["sha"], t["scope_key"])
    old = OLD / tag
    if (old / "rc.txt").exists() and (old / "meta.json").exists() and not (NEW / tag).exists():
        os.symlink(old, NEW / tag)
    elif not (NEW / tag).exists():
        todo.append(t)
print(f"{len(tasks)} distinct (port, commit): {len(tasks) - len(todo)} reused from E8, {len(todo)} to scan", flush=True)
done = 0
with ThreadPoolExecutor(3) as ex:
    for m in ex.map(lambda t: S.run_task(t, NEW), todo):
        done += 1
        if done % 10 == 0 or done == len(todo):
            print(f"{done}/{len(todo)} scanned", flush=True)
print("done", flush=True)
