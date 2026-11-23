"""DOOM-E10 development evaluation: plain vs normalised (strip comments + pinned clang-format) pipeline, default sfs lens both ways.
(1) simple-edit suite (9 variants x 2 donors, names unchanged) recall by variant; (2) recall of E9 documented port-to-port T1 transfers; (3) hard-negative FP."""
import glob, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import e10_norm as N
import e10_dev as D
from structural_fingerprint.fingerprint import build
from structural_fingerprint.scan_io import load_scan
from concurrent.futures import ThreadPoolExecutor

R = "/srv/storage_16tb/projects/doom-e7-work/e10/dev/results/"
REPOS = "/srv/storage_16tb/projects/doom-e7-work/repos/"


def plain_table(prog, db):
    return build(load_scan(db, N.ref.signal_columns, name=prog), N.ref, min_loc=3).functions


def keymap(t):
    m = {}
    for i, (n, p) in enumerate(zip(t.name, t.path)):
        m.setdefault((str(n), str(p)), []).append(i)
    return {k: v[0] for k, v in m.items() if len(v) == 1}


def main():
    prog = pd.read_csv(R + "dev_programs.csv").set_index("program")
    tr = pd.read_csv(R + "dev_truth.csv", dtype=str)
    tr = tr[(tr.eligible == "1") & (tr.kept == "1")]
    # plain tables
    plain = {}
    for p, r in prog.iterrows():
        d = glob.glob(R + f"snaps/{r.commit[:12]}__*") or glob.glob(R + f"snaps/**/{r.commit[:12]}__*", recursive=True)
        plain[p] = plain_table(p, glob.glob(d[0] + "/*_galaxy_master.db")[0])
    for dn, d in (("curl", "curl"), ("libuv", "libuv")):
        plain[dn] = D.fp(dn, "structure", "density")
    # normalised tables (donors and recipients)
    items = [(p, r.dir) for p, r in prog.iterrows()]
    items += [("curl", REPOS + "curl"), ("libuv", "/srv/storage_16tb/projects/doom-e7-work/halflife/controls/libuv")]
    norm = {}
    with ThreadPoolExecutor(3) as ex:
        for p, t in ex.map(N.prep, items):
            norm[p] = t
    rows = []
    for name, T in (("plain", plain), ("normalised", norm)):
        for (var, donor, size), g in tr.groupby(["variant", "donor", "module_size"]):
            a, b = T[donor], T[f"chocolate-e10-{donor}-{var}"]
            S = N.union(a, b)
            ka, kb = keymap(a), keymap(b)
            h = n = 0
            for o, df, rf in zip(g.orig_func, g.donor_file, g.recipient_file):
                i, j = ka.get((o, df)), kb.get((o, rf))
                if i is None or j is None:
                    continue
                n += 1; h += (i, j) in S
            rows.append(dict(pipeline=name, variant=var, size=size, recall=h / max(n, 1), n=n))
    r = pd.DataFrame(rows)
    r.to_csv("/srv/storage_16tb/projects/doom-e7-work/e10_dev_eval_suite.csv", index=False)
    print(r.pivot_table(index=["size", "variant"], columns="pipeline", values="recall").round(2).to_string(), flush=True)
    # real transfers
    pairs = pd.read_csv(D.E9 + "truth/pairs.csv", dtype=str)
    p2p = pairs[(pairs.pair_class == "port-to-port") & (pairs.eligible_primary == "1") & (pairs.jaccard.astype(float) >= 0.9)]
    fn = pd.read_csv(D.E9 + "truth/functions.csv", dtype=str, usecols=["program", "func_id", "name", "path"])
    fk = {(p, i): (n, pa) for p, i, n, pa in zip(fn.program, fn.func_id, fn.name, fn.path)}
    need = sorted(set(p2p.prog_a) | set(p2p.prog_b))
    plainp, normp = {}, {}
    items2 = []
    for p in need:
        if p in norm or not os.path.isdir(REPOS + p):
            continue
        items2.append((p, REPOS + p))
    with ThreadPoolExecutor(3) as ex:
        for p, t in ex.map(N.prep, items2):
            norm[p] = t
    for p in need:
        db = f"{D.SC}{p}/{p}_galaxy_master.db"
        if os.path.exists(db):
            plain[p] = plain_table(p, db)
    out = []
    for name, T in (("plain", plain), ("normalised", norm)):
        H = M = 0
        for (a, b), g in p2p.groupby(["prog_a", "prog_b"]):
            if a not in T or b not in T or len(T[a].loc) == 0 or len(T[b].loc) == 0:
                continue
            S = N.union(T[a], T[b]); ka, kb = keymap(T[a]), keymap(T[b])
            for fa, fb in zip(g.func_a, g.func_b):
                i, j = ka.get(fk.get((a, fa))), kb.get(fk.get((b, fb)))
                if i is None or j is None:
                    continue
                M += 1; H += (i, j) in S
        out.append((name, H, M, H / max(M, 1)))
    print("real documented transfers (T1, jaccard>=0.9):", out, flush=True)


if __name__ == "__main__":
    main()
