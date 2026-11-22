"""DOOM-E8 snapshot runner: export each planned commit, apply scope pruning, count functions with ctags, scan.

Outcome-blind: computes no survival, shared or trend. Resumable (a finished task with rc.txt is skipped).

    python e8_snap.py tasks   [--workers 3]          # manifest/e8_tasks.csv  -> <work>/halflife/snaps
    python e8_snap.py rescan  [--workers 3]          # manifest/e8_rescan.csv -> <work>/halflife/snaps_rep{1,2}
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORK = Path("/srv/storage_16tb/projects/doom-e7-work/halflife")
ENGINE = Path("/srv/storage_16tb/projects/gitgalaxy-worktrees/e7-engine")
PY = "/srv/storage_16tb/projects/gitgalaxy/venvs/selfscan/bin/python"
HEAVY = ENGINE / "tests" / "tools" / "box" / "heavy-run.sh"
KINDS = {"function", "method", "procedure", "subroutine", "func", "member"}


def tag(sha: str, scope_key: str) -> str:
    return f"{sha[:12]}__{hashlib.sha1(scope_key.encode()).hexdigest()[:6]}"


def prune(root: Path, scope_key: str) -> list[str]:
    """scope.csv semantics as the E7 harness: drop listed directories that exist; (keep lists unused here)."""
    keep, _, drop = scope_key.partition("|")
    done = []
    for d in drop.split():
        p = root / d
        if p.exists():
            shutil.rmtree(p) if p.is_dir() else p.unlink()
            done.append(d)
    return done


def ctags_count(root: Path) -> int:
    r = subprocess.run(["ctags", "-R", "-x", "-f", "-", str(root)], capture_output=True, text=True, errors="replace")
    n = 0
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) > 1 and parts[1] in KINDS:
            n += 1
    return n


def run_task(t: dict, out_root: Path) -> dict:
    sha, scope_key, repo = t["sha"], t["scope_key"], t["repo"]
    out = out_root / tag(sha, scope_key)
    meta_p = out / "meta.json"
    if (out / "rc.txt").exists() and meta_p.exists():
        return json.loads(meta_p.read_text())
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    t0 = time.time()
    exp = out / "_export"
    exp.mkdir()
    ar = subprocess.run(f"git -C '{repo}' archive {sha} | tar -x -C '{exp}'", shell=True, capture_output=True, text=True)
    if ar.returncode:
        meta = dict(task=t, rc=-1, error=ar.stderr[:200])
        meta_p.write_text(json.dumps(meta))
        (out / "rc.txt").write_text("-1\n")
        return meta
    pruned = prune(exp, scope_key) if scope_key else []
    nfun = ctags_count(exp)
    env = dict(os.environ, PYTHONPATH=str(ENGINE), GITGALAXY_LICENSE_KEY=os.environ.get("GITGALAXY_LICENSE_KEY", "COMMUNITY_FREE_TIER"),
               GG_HEAVY_SLOTS=os.environ.get("GG_HEAVY_SLOTS", "3"))
    cmd = [PY, "-m", "gitgalaxy.galaxyscope", str(exp), "--output", str(out) + "/"]
    if HEAVY.exists():
        cmd = [str(HEAVY), *cmd]
    with open(out / "scan.log", "w") as log:
        rc = subprocess.run(cmd, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    # the export is kept: the name-blind text arbiter reads function bodies from it
    meta = dict(task=t, rc=rc, pruned=pruned, ctags_functions=nfun, seconds=round(time.time() - t0))
    meta_p.write_text(json.dumps(meta))
    (out / "rc.txt").write_text(f"{rc}\n")
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["tasks", "rescan"])
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    plan = {(r["port"], r["sha"]): r for r in csv.DictReader(open(REPO / "manifest" / "e8_tasks.csv"))}
    if a.mode == "tasks":
        jobs = [(t, WORK / "snaps") for t in plan.values()]
    else:
        tasks_by = {}
        for r in csv.DictReader(open(REPO / "manifest" / "e8_tasks.csv")):
            tasks_by.setdefault((r["port"], r["sha"]), r)
        jobs = []
        for r in csv.DictReader(open(REPO / "manifest" / "e8_rescan.csv")):
            t = tasks_by.get((r["port"], r["sha"]))
            if t:
                jobs.append((t, WORK / f"snaps_rep{r['replicate']}"))
    (WORK / "snaps").mkdir(parents=True, exist_ok=True)
    for _, root in jobs:
        root.mkdir(parents=True, exist_ok=True)
    done = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(run_task, t, root) for t, root in jobs]
        for f in futs:
            m = f.result()
            done += 1
            if done % 10 == 0 or done == len(futs):
                bad = m.get("rc") not in (0, None)
                print(f"{done}/{len(futs)} done, {time.time() - t0:.0f}s{'  (last rc ' + str(m.get('rc')) + ')' if bad else ''}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    sys.exit(main())
