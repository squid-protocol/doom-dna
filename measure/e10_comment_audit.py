"""DOOM-E10 comment-sensitivity audit (development): strip all comments, and rewrite all comment text, in linuxdoom and lua; scan; per-signal change rates."""
import glob, os, re, shutil, subprocess, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner-worktrees/robust-lens/src")
from structural_fingerprint.reference import load_reference
from structural_fingerprint.scan_io import load_scan
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e10-robust-lens/measure")
W = "/srv/storage_16tb/projects/doom-e7-work/e10/audit_c"
ENG = "/srv/storage_16tb/projects/gitgalaxy-worktrees/e7-engine"
PY = "/srv/storage_16tb/projects/gitgalaxy/venvs/selfscan/bin/python"
SRC = {"linuxdoom": "/srv/storage_16tb/projects/doom-e7-work/repos/linuxdoom", "lua": "/srv/storage_16tb/projects/doom-e7-work/repos/lua"}
ref = load_reference("structure")
TOK = re.compile(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(/\*.*?\*/|//[^\n]*)', re.S)


def transform(text, mode):
    def f(m):
        if m.group(1):
            return m.group(1)
        c = m.group(2)
        if mode == "strip":
            return "\n" * c.count("\n") if c.startswith("/*") else ""
        return "/* edited */" if c.startswith("/*") else "// edited"
    return TOK.sub(f, text)


def scan(d, out):
    os.makedirs(out, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=ENG, GITGALAXY_LICENSE_KEY="COMMUNITY_FREE_TIER", GG_HEAVY_SLOTS="3")
    subprocess.run([f"{ENG}/tests/tools/box/heavy-run.sh", PY, "-m", "gitgalaxy.galaxyscope", d, "--output", out + "/"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return glob.glob(out + "/*_galaxy_master.db")[0]


def sig(db, name):
    s = load_scan(db, ref.signal_columns, name=name)
    d = {}
    for i, n in enumerate(s.func_name):
        d.setdefault(n, []).append(i)
    return s, {n: v[0] for n, v in d.items() if len(v) == 1}


rows = []
for prog, src in SRC.items():
    shutil.rmtree(f"{W}/{prog}", ignore_errors=True)
    base = f"{W}/{prog}/orig"
    shutil.copytree(src, base, ignore=shutil.ignore_patterns(".git"))
    b, bi = sig(scan(base, f"{W}/{prog}/orig_scan"), prog)
    for mode in ("strip", "rewrite"):
        d = f"{W}/{prog}/{mode}"
        shutil.copytree(base, d)
        for f in glob.glob(d + "/**/*", recursive=True):
            if f.endswith((".c", ".h")):
                t = open(f, errors="replace").read()
                open(f, "w").write(transform(t, mode))
        s, si = sig(scan(d, f"{W}/{prog}/{mode}_scan"), prog)
        com = [n for n in bi if n in si]
        A = b.signals[[bi[n] for n in com]]; C = s.signals[[si[n] for n in com]]
        for j, c in enumerate(ref.signal_columns):
            rows.append(dict(program=prog, variant=mode, signal=c, n=len(com), changed=float((A[:, j] != C[:, j]).mean())))
        for nm, x, y in (("complexity", b.complexity[[bi[n] for n in com]], s.complexity[[si[n] for n in com]]), ("args", b.args[[bi[n] for n in com]], s.args[[si[n] for n in com]]),
                         ("loc", b.loc[[bi[n] for n in com]], s.loc[[si[n] for n in com]])):
            rows.append(dict(program=prog, variant=mode, signal=nm, n=len(com), changed=float((x != y).mean())))
        print(prog, mode, len(com), flush=True)
a = pd.DataFrame(rows)
a.to_csv("/srv/storage_16tb/projects/doom-e7-work/e10/comment_audit.csv", index=False)
print(a.groupby("signal").changed.max().sort_values(ascending=False).head(10).round(3).to_string())
