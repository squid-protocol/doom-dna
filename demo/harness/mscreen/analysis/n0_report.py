"""E15 exploratory (A4 item 5): dynamic call-count profiles as an ortholog matcher. Uses ONLY clean-run coverage (how often each function runs on each demo), no lesion outcome.
Matches chocolate-doom functions to managed-doom functions by the distance between their log call-count profiles; scores it against the name-agree partners and against the E12 structural matches. Usage: python n0_report.py <out_dir>"""
import csv, re, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); S = W / "screen"; PREFIX = re.compile(r"^(EV_|P_|A_|T_|PIT_|PTR_)"); GENERIC = {"add", "remove", "get", "set", "update", "run", "start", "stop", "init", "clear", "reset", "check", "free", "alloc"}
def load(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True); f = pd.read_sql("select fid, file, name from functions", c); r = pd.read_sql("select demo, fid, entries from reach", c); demos = sorted(r.demo.unique()); return f, r, demos
def profiles(f, r, demos, min_demos=3):
    di = {d: i for i, d in enumerate(demos)}; M = np.zeros((len(f), len(demos))); fi = {x: i for i, x in enumerate(f.fid)}
    for fid, d, n in zip(r.fid, r.demo, r.entries):
        if fid in fi and d in di: M[fi[fid], di[d]] = np.log1p(n)
    keep = (M > 0).sum(1) >= min_demos; return M, keep
def ranks(D, partner): return np.array([int((D[i] <= D[i, partner[i]]).sum()) for i in range(len(partner))])
def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); fa, ra, da = load(S / "choc_phenotypes.sqlite"); fb, rb, db = load(S / "md_phenotypes.sqlite"); assert da == db, "port stores must share the demo set"
    Ma, ka = profiles(fa, ra, da); Mb, kb = profiles(fb, rb, db); ia, ib = np.where(ka)[0], np.where(kb)[0]; na = fa.name.to_numpy()[ia]; nb = fb.name.to_numpy()[ib]
    D = np.abs(Ma[ia][:, None, :] - Mb[ib][None, :, :]).mean(2)
    ka_ = pd.Series([PREFIX.sub("", n) for n in na]); kb_ = pd.Series(nb); ua, ub = ka_.value_counts(), kb_.value_counts()
    ai = {k: i for i, k in enumerate(ka_) if ua[k] == 1 and len(k) >= 4 and k.lower() not in GENERIC}; bi = {k: j for j, k in enumerate(kb_) if ub[k] == 1}
    pairs = [(ai[k], bi[k], k) for k in sorted(set(ai) & set(bi))]; md = ["# Dynamic call-count profiles as an ortholog matcher (no lesion outcomes)\n", f"functions entered by >= 3 demos: chocolate-doom {len(ia)}, managed-doom {len(ib)}; demos {len(da)}; name-agree pairs {len(pairs)}\n"]
    rk = ranks(D[[p[0] for p in pairs]], np.array([p[1] for p in pairs])); zero = (D[[p[0] for p in pairs], [p[1] for p in pairs]] < 1e-9).mean()
    md.append(f"**Name-agree partners:** top-1 {np.mean(rk == 1):.2f}, top-5 {np.mean(rk <= 5):.2f}, median rank {int(np.median(rk))}; chance top-1 {1 / len(ib):.3f}. {zero:.0%} of partner pairs have an identical profile (distance 0; ties count against the matcher).\n")
    miss = [(pairs[i][2], int(rk[i])) for i in np.argsort(-rk)[:15] if rk[i] > 5]
    if miss: md += ["Name-agree pairs with the worst profile rank (profile does not isolate the partner):\n", "| function | rank of its name partner |\n|---|---|"] + [f"| {n} | {r} |" for n, r in miss] + [""]
    # E12 structural matches
    rows = list(csv.DictReader(open(Path(__file__).resolve().parents[2] / "e14/pilot_pairs.csv"))); an = {n: i for i, n in enumerate(na)}; bn = {n: j for j, n in enumerate(nb)}; res = []
    for x in rows:
        a, b = an.get(x["ref_name"]), bn.get(x["md_name"])
        if a is None or b is None: continue
        agree_k = PREFIX.sub("", x["ref_name"]); nameagree = agree_k == x["md_name"]; r = int((D[a] <= D[a, b]).sum()); alt = bi.get(agree_k)
        res.append(dict(ref=x["ref_name"], md=x["md_name"], tier=x["md_tier"], name_agree=nameagree, rank=r, dist=float(D[a, b]), name_partner=(kb_[alt] if alt is not None else ""), name_partner_dist=float(D[a, alt]) if alt is not None else np.nan))
    df = pd.DataFrame(res); md.append(f"## E12 structural matches ({len(df)} chocolate-doom to managed-doom pairs with both functions entered)\n")
    strong = {"exact", "twin", "xtwin", "seed"}; df["strong"] = df.tier.isin(strong)
    md += ["| group | pairs | profile top-1 | top-5 | median rank |\n|---|---|---|---|---|"] + [f"| {nm} | {len(g)} | {(g['rank'] == 1).mean():.2f} | {(g['rank'] <= 5).mean():.2f} | {int(g['rank'].median())} |" for nm, g in (("strong tiers (exact, twin, xtwin, seed)", df[df.strong]), ("extension tiers (ext1-3)", df[~df.strong]), ("matcher agrees with the name", df[df.name_agree]), ("matcher disagrees with the name", df[~df.name_agree])) if len(g)]
    dis = df[(~df.name_agree) & df.name_partner.ne("")]
    if len(dis): md += [f"\n**Where the structural matcher and the name disagree ({len(dis)} pairs with a same-named function in managed-doom):** the call-count profile is closer to the NAME partner for {(dis.name_partner_dist < dis.dist).mean():.0%} of them and closer to the structural matcher's choice for {(dis.name_partner_dist > dis.dist).mean():.0%} (ties {(dis.name_partner_dist == dis.dist).mean():.0%}).\n"]
    df.to_csv(out / "E15_N0_e12_pairs.csv", index=False); (out / "E15_N0_REPORT.md").write_text("\n".join(md)); print("\n".join(md)[:3500])
if __name__ == "__main__": main()
