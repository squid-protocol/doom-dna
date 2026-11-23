"""DOOM-E10 format-sensitivity audit (development, no copy truth involved): re-format two C code bases (linuxdoom, lua) with six clang-format
styles, scan each with the E7 engine, and measure per signal how often a function's raw count changes. Layout-sensitive signals are those that change
in more than 5% of functions under any style."""
import glob, os, shutil, subprocess, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner-worktrees/robust-lens/src")
from structural_fingerprint.reference import load_reference
from structural_fingerprint.scan_io import load_scan

W = "/srv/storage_16tb/projects/doom-e7-work/e10/audit"
CF = "/srv/storage_16tb/projects/doom-e7-work/e9/venv/bin/clang-format"
ENG = "/srv/storage_16tb/projects/gitgalaxy-worktrees/e7-engine"
PY = "/srv/storage_16tb/projects/gitgalaxy/venvs/selfscan/bin/python"
STYLES = ["LLVM", "Google", "Mozilla", "GNU", "WebKit", "Chromium", "{BasedOnStyle: LLVM, BreakBeforeBraces: Allman, IndentWidth: 4}"]
SRC = {"linuxdoom": "/srv/storage_16tb/projects/doom-e7-work/repos/linuxdoom", "lua": "/srv/storage_16tb/projects/doom-e7-work/repos/lua"}
ref = load_reference("structure")


def scan(d, out):
    os.makedirs(out, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=ENG, GITGALAXY_LICENSE_KEY="COMMUNITY_FREE_TIER", GG_HEAVY_SLOTS="3")
    subprocess.run([f"{ENG}/tests/tools/box/heavy-run.sh", PY, "-m", "gitgalaxy.galaxyscope", d, "--output", out + "/"], env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return glob.glob(out + "/*_galaxy_master.db")[0]


def sig(db, name):
    s = load_scan(db, ref.signal_columns, name=name)
    d = {}
    for i, n in enumerate(s.func_name):
        d.setdefault(n, []).append(i)
    return s, {n: v[0] for n, v in d.items() if len(v) == 1}


rows = []
for prog, src in SRC.items():
    base_dir = f"{W}/{prog}/orig"
    shutil.rmtree(f"{W}/{prog}", ignore_errors=True)
    shutil.copytree(src, base_dir, ignore=shutil.ignore_patterns(".git"))
    b, bi = sig(scan(base_dir, f"{W}/{prog}/orig_scan"), prog)
    for k, style in enumerate(STYLES):
        d = f"{W}/{prog}/s{k}"
        shutil.copytree(base_dir, d)
        files = [f for f in glob.glob(d + "/**/*", recursive=True) if f.endswith((".c", ".h"))]
        for f in files:
            subprocess.run([CF, "-i", f"--style={style}", f], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        s, si = sig(scan(d, f"{W}/{prog}/s{k}_scan"), prog)
        com = [n for n in bi if n in si]
        A = b.signals[[bi[n] for n in com]]; C = s.signals[[si[n] for n in com]]
        for j, c in enumerate(ref.signal_columns):
            rows.append(dict(program=prog, style=style[:20], signal=c, n=len(com), changed=float((A[:, j] != C[:, j]).mean()), mean_abs=float(np.abs(A[:, j] - C[:, j]).mean()),
                             mean_count=float(A[:, j].mean())))
        for nm, x, y in (("complexity", b.complexity[[bi[n] for n in com]], s.complexity[[si[n] for n in com]]), ("args", b.args[[bi[n] for n in com]], s.args[[si[n] for n in com]]),
                         ("loc", b.loc[[bi[n] for n in com]], s.loc[[si[n] for n in com]])):
            rows.append(dict(program=prog, style=style[:20], signal=nm, n=len(com), changed=float((x != y).mean()), mean_abs=float(np.abs(x - y).mean()), mean_count=float(np.mean(x))))
        print(prog, style[:20], len(com), flush=True)
pd.DataFrame(rows).to_csv("/srv/storage_16tb/projects/doom-e7-work/e10/format_audit.csv", index=False)
a = pd.DataFrame(rows)
w = a.groupby("signal").changed.max().sort_values(ascending=False)
print(w.head(14).round(3).to_string())
