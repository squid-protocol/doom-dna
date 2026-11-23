"""DOOM-E10 part 2 (E7 repeat): rescan all 66 E7 programs at their pinned commits with the SAME scope pruning and engine as E7, after the canonical
normalisation (strip comments, drop blank lines, pinned clang-format) of every C-family source file. Programs without C-family files keep E7's scan (symlink).
No outcome is read here."""
import csv, glob, json, os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e9-horizontal/measure")
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/measure")
import e9_spike as S9
import e8_snap as S8

E7 = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees")
OLD = Path("/srv/storage_16tb/projects/doom-e7-work")
NEW = Path("/srv/storage_16tb/projects/doom-e7n-work")
ENG = "704cb35f0"
CF = "/srv/storage_16tb/projects/doom-e7-work/e9/venv/bin/clang-format"
CONF = "/srv/storage_16tb/projects/doom-dna-worktrees/e10-robust-lens/manifest/e10_canon_clang_format.yaml"
EXT = (".c", ".h", ".cc", ".cpp", ".hpp", ".cxx", ".hh", ".C", ".H")


def scope_key(name, rows):
    r = rows.get(name)
    return f"{r['keep']}|{r['drop']}" if r else ""


def one(args):
    p, rows = args
    name, sha = p["name"], p["sha"]
    out = NEW / "scans" / ENG / name
    if (out / f"{name}_galaxy_master.db").exists():
        return name, "cached", 0
    repo = OLD / "repos" / name
    exp = NEW / "work" / name
    shutil.rmtree(exp, ignore_errors=True); exp.mkdir(parents=True)
    ar = subprocess.run(f"git -C '{repo}' archive {sha} | tar -x -C '{exp}'", shell=True, capture_output=True, text=True)
    if ar.returncode:
        return name, "export-failed " + ar.stderr[:100], 0
    S8.prune(exp, scope_key(name, rows))
    cfiles = [f for f in glob.glob(str(exp) + "/**/*", recursive=True) if os.path.isfile(f) and f.endswith(EXT)]
    if not cfiles:
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() or out.is_symlink():
            out.unlink() if out.is_symlink() else shutil.rmtree(out)
        os.symlink(OLD / "scans" / ENG / name, out)
        shutil.rmtree(exp, ignore_errors=True)
        return name, "reused (no C-family files)", 0
    for f in cfiles:
        try:
            t = S9.strip_comments(open(f, errors="replace").read())
            open(f, "w").write("\n".join(l for l in t.split("\n") if l.strip()) + "\n")
            subprocess.run([CF, "-i", f"--style=file:{CONF}", f], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=120)
        except Exception:
            pass
    # scan in git mode exactly as E7 did (E7 scanned a checkout): a scratch repo with every exported (= tracked) file force-added, so .gitignore cannot hide sources
    g = ["git", "-C", str(exp), "-c", "user.name=e10", "-c", "user.email=e10@example.invalid"]
    subprocess.run(g + ["init", "-q"], check=False); subprocess.run(g + ["add", "-f", "-A"], capture_output=True, check=False)
    subprocess.run(g + ["commit", "-q", "-m", "normalised export"], capture_output=True, check=False)
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(S8.ENGINE), GITGALAXY_LICENSE_KEY="COMMUNITY_FREE_TIER", GG_HEAVY_SLOTS="3")
    cmd = [str(S8.HEAVY), S8.PY, "-m", "gitgalaxy.galaxyscope", str(exp), "--output", str(out) + "/"]
    t0 = time.time()
    with open(out / "scan.log", "w") as log:
        rc = subprocess.run(cmd, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    shutil.rmtree(exp, ignore_errors=True)
    return name, f"rc={rc} files={len(cfiles)}", round(time.time() - t0)


def main():
    pins = json.load(open(E7 / "manifest" / "RUN_PINS.json"))["programs"]
    rows = {r["name"]: r for r in csv.DictReader(open(E7 / "manifest" / "scope.csv"))}
    with ThreadPoolExecutor(3) as ex:
        for name, status, secs in ex.map(one, [(p, rows) for p in pins]):
            print(name, status, secs, flush=True)


if __name__ == "__main__":
    main()
