"""Replication helper: scan the 66 E7 programs with one pinned engine checkout (NEW code for the new-engine replication).

    python scan_programs.py --engine /path/to/engine-worktree --work WORKDIR [--only a,b] [--src DIR]

For every program in manifest/RUN_PINS.json: copy the pinned, scoped source tree from the original E7 clone (read only;
``.git`` and ``.gitgalaxy`` are left out), make a fresh scratch git repo and ``git add -f -A`` (otherwise .gitignore hides
sources and the counts are wrong), then scan it in git mode through heavy-run.sh with PYTHONPATH set to the engine
worktree (the preset PYTHONPATH points at main and would run the wrong tree). Outputs, in the layout e7_run.py reads:
WORKDIR/scans/<engine short sha>/<name>/ (rc.txt, scan.log, *_galaxy_master.db). Finished scans are skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HEAVY = "/srv/storage_16tb/projects/gitgalaxy-worktrees/e7-engine-current/tests/tools/box/heavy-run.sh"
SRC = Path("/srv/storage_16tb/projects/doom-e7-work/repos")  # frozen original clones: read only


def make_scratch_repo(src: Path, dest: Path) -> None:
    """Copy ``src`` without .git/.gitgalaxy into ``dest`` and commit every file, ignored ones included."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, symlinks=True, ignore=shutil.ignore_patterns(".git", ".gitgalaxy"))
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    for args in (["init", "-q"], ["add", "-f", "-A"],
                 ["-c", "user.name=e7", "-c", "user.email=e7@example.invalid", "commit", "-q", "--allow-empty", "-m", "scratch"]):
        r = subprocess.run(["git", "-C", str(dest), *args], capture_output=True, text=True, env=env)
        if r.returncode:
            raise SystemExit(f"git {args[0]} failed in {dest}: {r.stderr[:300]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--only", default="")
    ap.add_argument("--src", type=Path, default=SRC)
    a = ap.parse_args()
    sha = subprocess.run(["git", "-C", str(a.engine), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    short = sha[:9]
    print(f"engine {a.engine} = {sha}", flush=True)
    env0 = dict(os.environ, PYTHONPATH=str(a.engine), PYTHONDONTWRITEBYTECODE="1")
    loaded = subprocess.run([sys.executable, "-c", "import gitgalaxy;print(gitgalaxy.__file__)"], capture_output=True,
                            text=True, env=env0, cwd="/tmp").stdout.strip()
    print(f"gitgalaxy imported from {loaded}", flush=True)
    if not loaded.startswith(str(a.engine)):
        raise SystemExit("scan_programs: the engine that would run is not the pinned worktree; stopping")
    progs = json.load(open(REPO / "manifest" / "RUN_PINS.json"))["programs"]
    names = [p["name"] for p in progs if not a.only or p["name"] in a.only.split(",")]
    for n in names:
        out = a.work / "scans" / short / n
        if (out / "rc.txt").exists() and (out / "rc.txt").read_text().strip() == "0":
            continue
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)
        repo = a.work / "repos" / n
        make_scratch_repo(a.src / n, repo)
        env = dict(os.environ, PYTHONPATH=str(a.engine), PYTHONDONTWRITEBYTECODE="1",
                   GITGALAXY_LICENSE_KEY="COMMUNITY_FREE_TIER")
        cmd = [HEAVY, sys.executable, "-m", "gitgalaxy.galaxyscope", str(repo), "--output", str(out) + "/"]
        with open(out / "scan.log", "w") as log:
            rc = subprocess.run(cmd, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        (out / "rc.txt").write_text(f"{rc}\n")
        (out / "engine_sha.txt").write_text(sha + "\n")
        print(f"{n}: rc={rc}", flush=True)
        shutil.rmtree(repo, ignore_errors=True)  # the scan database is the product; the scratch copy is not kept
    print("scans done", flush=True)


if __name__ == "__main__":
    main()
