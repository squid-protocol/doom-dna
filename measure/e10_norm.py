"""DOOM-E10 development: canonicalisation before measuring. Strip comments and apply one pinned clang-format configuration to every C/C++ file of a source tree,
scan the normalised tree with the E7 engine, then compare with the DEFAULT sfs lens (no lens change). Evaluates the E9 spike-in tiers and a false-positive check."""
import glob, os, shutil, subprocess, sys, json
from concurrent.futures import ThreadPoolExecutor
import numpy as np, pandas as pd
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e9-horizontal/measure")
sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
import e9_spike as S9
from structural_fingerprint.fingerprint import build
from structural_fingerprint.reference import load_reference
from structural_fingerprint.scan_io import load_scan
from structural_fingerprint.twins import TwinParams, find_twins

W = "/srv/storage_16tb/projects/doom-e7-work/e10/norm2"
ENG = "/srv/storage_16tb/projects/gitgalaxy-worktrees/e7-engine"
PY = "/srv/storage_16tb/projects/gitgalaxy/venvs/selfscan/bin/python"
CF = "/srv/storage_16tb/projects/doom-e7-work/e9/venv/bin/clang-format"
CONF = "/srv/storage_16tb/projects/doom-dna-worktrees/e10-robust-lens/manifest/e10_canon_clang_format.yaml"
E9 = "/srv/storage_16tb/projects/doom-e7-work/e9/results/"
EXT = (".c", ".h", ".cc", ".cpp", ".hpp", ".cxx")
P = TwinParams(min_loc=6)
ref = load_reference("structure")


def normalise(src, dst):
    if os.path.exists(dst):
        return
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git"))
    for f in glob.glob(dst + "/**/*", recursive=True):
        if os.path.isfile(f) and f.endswith(EXT):
            try:
                t = open(f, errors="replace").read()
                t = S9.strip_comments(t)
                open(f, "w").write("\n".join(l for l in t.split("\n") if l.strip()) + "\n")
                subprocess.run([CF, "-i", f"--style=file:{CONF}", f], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=60)
            except Exception:
                pass


def scan(d, out):
    if glob.glob(out + "/*_galaxy_master.db"):
        return glob.glob(out + "/*_galaxy_master.db")[0]
    os.makedirs(out, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=ENG, GITGALAXY_LICENSE_KEY="COMMUNITY_FREE_TIER", GG_HEAVY_SLOTS="3")
    subprocess.run([f"{ENG}/tests/tools/box/heavy-run.sh", PY, "-m", "gitgalaxy.galaxyscope", d, "--output", out + "/"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return glob.glob(out + "/*_galaxy_master.db")[0]


def table(prog, db):
    return build(load_scan(db, ref.signal_columns, name=prog), ref, min_loc=3).functions


def prep(item):
    prog, src = item
    d = f"{W}/src/{prog}"
    normalise(src, d)
    return prog, table(prog, scan(d, f"{W}/scan/{prog}"))


def union(a, b):
    ab, ba = find_twins(a, b, P), find_twins(b, a, P)
    s = {(int(i), int(j)) for i, j in zip(ab.q_index, ab.t_index)}
    return s | {(int(j), int(i)) for i, j in zip(ba.q_index, ba.t_index)}


def main():
    st = pd.read_csv(E9 + "spike/spike_truth.csv", dtype=str)
    st = st[(st.eligible == "1") & (st.kept == "1") & st.recipient_engine_row.notna() & (st.recipient_engine_row != "")]
    progs = pd.read_csv(E9 + "spike/spike_programs.csv").set_index("program").dir
    items = [("curl", "/srv/storage_16tb/projects/doom-e7-work/repos/curl"), ("libuv", "/srv/storage_16tb/projects/doom-e7-work/halflife/controls/libuv")]
    items += [(p, progs[p]) for p in sorted(st.recipient_program.unique())]
    neg = [("nginx", "/srv/storage_16tb/projects/doom-e7-work/repos/nginx"), ("leveldb", "/srv/storage_16tb/projects/doom-e7-work/repos/leveldb")]
    doom = ["chocolate-doom", "crispy-doom", "doomgeneric", "doom-ascii", "doom-wasm", "sdl-doom", "prboom-plus", "woof", "eternity", "odamex", "linuxdoom"]
    items += neg + [(p, f"/srv/storage_16tb/projects/doom-e7-work/repos/{p}") for p in doom]
    tabs = {}
    with ThreadPoolExecutor(3) as ex:
        for p, t in ex.map(prep, items):
            tabs[p] = t
            print("prepared", p, len(t.loc), flush=True)
    # donor engine rows in the NORMALISED donor tables: match by (name, path suffix) via the E9 functions.csv names
    for donor in ("curl", "libuv"):
        pass
    res = []
    for (donor, tier, size), x in st.groupby(["donor", "tier", "module_size"]):
        rp = f"chocolate-spike-{donor}-{tier}"
        a, b = tabs[donor], tabs[rp]
        S = union(a, b)
        # map donor/recipient functions by name+path (names unchanged in normalised donor; recipient uses renamed_func)
        didx = {}
        for i, (n, pth) in enumerate(zip(a.name, a.path)):
            didx.setdefault((str(n), str(pth)), i)
        ridx = {}
        for i, (n, pth) in enumerate(zip(b.name, b.path)):
            ridx.setdefault((str(n), str(pth)), i)
        hits = n = 0
        for o, r_, df, rf in zip(x.orig_func, x.renamed_func, x.donor_file, x.recipient_file):
            i = didx.get((o, df)); j = ridx.get((r_, rf))
            if i is None or j is None:
                continue
            n += 1
            hits += (i, j) in S
        res.append(dict(donor=donor, tier=tier, size=size, recall=hits / max(n, 1), n=n))
    r = pd.DataFrame(res)
    print(r.pivot_table(index=["size", "tier"], values="recall").round(3).to_string())
    fp, elig = 0, 0
    for nn, _ in neg:
        flagged = set()
        for pn in doom:
            if pn in tabs and len(tabs[pn].loc) > 0:
                flagged |= {i for i, _ in union(tabs[nn], tabs[pn])}
        fp += len(flagged); elig += int((tabs[nn].loc >= 6).sum())
    print("hard-negative FP per 1000 (normalised, 11 DOOM ports):", round(1000 * fp / max(elig, 1), 1))
    r.to_csv("/srv/storage_16tb/projects/doom-e7-work/e10_norm_results.csv", index=False)


if __name__ == "__main__":
    main()
