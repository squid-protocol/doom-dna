"""DOOM-E10 development: 'either' rule = a pair is flagged if the plain scan OR the normalised scan certifies it. Suite recall, real T1 transfer recall, hard-negative FP."""
import glob, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import e10_norm as N, e10_dev as D
from e10_dev_eval import R, REPOS, plain_table, keymap
from concurrent.futures import ThreadPoolExecutor


def keyed(a, b, ka, kb):
    inv_a = {v: k for k, v in ka.items()}; inv_b = {v: k for k, v in kb.items()}
    return {(inv_a[i], inv_b[j]) for i, j in N.union(a, b) if i in inv_a and j in inv_b}


def main():
    prog = pd.read_csv(R + "dev_programs.csv").set_index("program")
    tr = pd.read_csv(R + "dev_truth.csv", dtype=str); tr = tr[(tr.eligible == "1") & (tr.kept == "1")]
    plain, norm = {}, {}
    for p, r in prog.iterrows():
        d = glob.glob(R + f"snaps/{r.commit[:12]}__*") or glob.glob(R + f"snaps/**/{r.commit[:12]}__*", recursive=True)
        plain[p] = plain_table(p, glob.glob(d[0] + "/*_galaxy_master.db")[0])
    for dn in ("curl", "libuv"):
        plain[dn] = D.fp(dn, "structure", "density")
    ports = ["linuxdoom", "chocolate-doom", "crispy-doom", "doom-ascii", "doom-wasm", "sdl-doom", "prboom-plus", "woof", "eternity", "odamex"]
    pairs = pd.read_csv(D.E9 + "truth/pairs.csv", dtype=str)
    p2p = pairs[(pairs.pair_class == "port-to-port") & (pairs.eligible_primary == "1") & (pairs.jaccard.astype(float) >= 0.9)]
    need = sorted(set(p2p.prog_a) | set(p2p.prog_b) | set(ports) | {"nginx", "leveldb"})
    items = [(p, r.dir) for p, r in prog.iterrows()] + [("curl", REPOS + "curl"), ("libuv", "/srv/storage_16tb/projects/doom-e7-work/halflife/controls/libuv")]
    items += [(p, REPOS + p) for p in need if os.path.isdir(REPOS + p)]
    with ThreadPoolExecutor(3) as ex:
        for p, t in ex.map(N.prep, items):
            norm[p] = t
    for p in need:
        db = f"{D.SC}{p}/{p}_galaxy_master.db"
        if os.path.exists(db):
            plain[p] = plain_table(p, db)
    rows = []
    for (var, donor, size), g in tr.groupby(["variant", "donor", "module_size"]):
        rp = f"chocolate-e10-{donor}-{var}"
        K = {}
        for nm, T in (("plain", plain), ("norm", norm)):
            ka, kb = keymap(T[donor]), keymap(T[rp]); K[nm] = (keyed(T[donor], T[rp], ka, kb))
        n = hp = hn = he = 0
        for o, df, rf in zip(g.orig_func, g.donor_file, g.recipient_file):
            k = ((o, df), (o, rf)); n += 1
            a, b = k in K["plain"], k in K["norm"]
            hp += a; hn += b; he += (a or b)
        rows.append(dict(variant=var, size=size, plain=hp / n, norm=hn / n, either=he / n, n=n))
    r = pd.DataFrame(rows); print(r.round(2).to_string(index=False), flush=True)
    fn = pd.read_csv(D.E9 + "truth/functions.csv", dtype=str, usecols=["program", "func_id", "name", "path"])
    fk = {(p, i): (n, pa) for p, i, n, pa in zip(fn.program, fn.func_id, fn.name, fn.path)}
    H = {"plain": 0, "norm": 0, "either": 0}; M = 0
    for (a, b), g in p2p.groupby(["prog_a", "prog_b"]):
        if any(a not in T or b not in T or len(T[a].loc) == 0 or len(T[b].loc) == 0 for T in (plain, norm)):
            continue
        K = {nm: keyed(T[a], T[b], keymap(T[a]), keymap(T[b])) for nm, T in (("plain", plain), ("norm", norm))}
        for fa, fb in zip(g.func_a, g.func_b):
            ka_, kb_ = fk.get((a, fa)), fk.get((b, fb))
            if ka_ is None or kb_ is None:
                continue
            M += 1; x, y = (ka_, kb_) in K["plain"], (ka_, kb_) in K["norm"]
            H["plain"] += x; H["norm"] += y; H["either"] += (x or y)
    print("real T1 transfers n=%d:" % M, {k: round(v / M, 3) for k, v in H.items()}, flush=True)
    fp = {"plain": 0, "norm": 0, "either": 0}; elig = 0
    for nn in ("nginx", "leveldb"):
        fl = {"plain": set(), "norm": set()}
        for pn in ports:
            if any(pn not in T or len(T[pn].loc) == 0 for T in (plain, norm)):
                continue
            for nm, T in (("plain", plain), ("norm", norm)):
                fl[nm] |= {i for i, _ in N.union(T[nn], T[pn])}
        ka, kn = {v: k for k, v in keymap(plain[nn]).items()}, {v: k for k, v in keymap(norm[nn]).items()}
        sp = {ka[i] for i in fl["plain"] if i in ka}; sn = {kn[i] for i in fl["norm"] if i in kn}
        fp["plain"] += len(sp); fp["norm"] += len(sn); fp["either"] += len(sp | sn); elig += int((plain[nn].loc >= 6).sum())
    print("hard-negative FP per 1000:", {k: round(1000 * v / elig, 1) for k, v in fp.items()}, flush=True)


if __name__ == "__main__":
    main()
