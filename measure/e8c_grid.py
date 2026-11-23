"""DOOM-E8c step 1: resolve the dense grid (monthly for 36 months after the fork, quarterly after, to the head) to commits. Writes manifest/e8c_grid.csv.
No scan is run and nothing is measured here."""
import csv, subprocess, datetime as dt
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
POOL = Path("/srv/storage_16tb/projects/temporal-crucible-pool/doom-ports")
E8 = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/manifest")
SAME = ("crispy-doom", "dsda-doom", "nugget-doom")

def add_months(d, m):
    y, mo = divmod(d.month - 1 + m, 12); y += d.year
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mo])
    return dt.date(y, mo + 1, day)

def last_commit(repo, date):
    out = subprocess.run(["git", "-C", str(repo), "rev-list", "-1", "--first-parent", f"--before={date.isoformat()} 23:59:59", "HEAD"], capture_output=True, text=True).stdout.strip()
    if not out:
        return "", ""
    d = subprocess.run(["git", "-C", str(repo), "show", "-s", "--format=%cI", out], capture_output=True, text=True).stdout.strip()[:10]
    return out, d

def head_date(repo):
    return dt.date.fromisoformat(subprocess.run(["git", "-C", str(repo), "show", "-s", "--format=%cI", "HEAD"], capture_output=True, text=True).stdout.strip()[:10])

truth = {r["child"]: r for r in csv.DictReader(open(E8 / "e8_fork_truth.csv"))}
rows = []
for child in SAME:
    t = truth[child]; parent = t["parent"]; fork = dt.date.fromisoformat(t["fork_date"])
    end = min(head_date(POOL / child), head_date(POOL / parent))
    dates = [add_months(fork, m) for m in range(1, 37)]
    m = 39
    while add_months(fork, m) <= end:
        dates.append(add_months(fork, m)); m += 3
    seen = set()
    for step, d in enumerate(dates, 1):
        cs, cd = last_commit(POOL / child, d); ps, pd_ = last_commit(POOL / parent, d)
        if not cs or not ps or (cs, ps) in seen:
            continue
        seen.add((cs, ps))
        rows.append(dict(child=child, parent=parent, step=step, target_date=d.isoformat(), child_sha=cs, child_date=cd, parent_sha=ps, parent_date=pd_,
                         identical_sha=int(cs == ps), grid="dense"))
with open(REPO / "manifest" / "e8c_grid.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for c in SAME:
    print(c, sum(1 for r in rows if r["child"] == c), "grid points,", len({r['child_sha'] for r in rows if r['child'] == c} | {r['parent_sha'] for r in rows if r['child'] == c}), "distinct commits")
