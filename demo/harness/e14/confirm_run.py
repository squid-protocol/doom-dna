"""E14 confirmatory run (registered design: preregistration/E14_SAME_BREAK_SAME_ROLE.md). Usage: python confirm_run.py <out.jsonl> [sites_per_function=3] (e11 venv python)
Reads sample.json (frozen before this run). Per reference function: up to 3 aligned sites; mutants in chocolate-doom (reference), prboom-plus (matcher target), managed-doom (matcher target and, where the names disagree, the name-oracle target),
plus a same-file control (a different function in the target's file, same operator) for each target port."""
import json, os, random, shutil, subprocess, sys
os.environ["E13_WIDE"] = "1"
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); sys.path.insert(0, str(H.parent)); sys.path.insert(0, str(H.parent / "difflocalize"))
out_path = Path(sys.argv[1]); per_fn = int(sys.argv[2]) if len(sys.argv) > 2 else 3; sys.argv = sys.argv[:1]
import sites as S, mutate, compare_digests as C, pilot_run as P
SEED = 20261129
def main():
    sample = json.load(open(H / "sample.json")); names = P.demos(); rng = random.Random(SEED); fh = open(out_path, "a")
    subprocess.run([str(P.NINJA), "-C", str(P.B / "prboom-plus/build"), "prboom-plus"], check=True, capture_output=True)
    shutil.copy(P.B / "prboom-plus/build/prboom-plus", P.OUT / "bin/prboom-plus.clean")
    bins = {"ch": mutate.BUILD / "src/chocolate-doom", "pb": P.OUT / "bin/prboom-plus.clean", "md": P.W / "build/managed-doom/bin"}; clean = {}
    for port in bins:
        cd = P.OUT / "clean" / port; cd.mkdir(parents=True, exist_ok=True)
        with P.ThreadPoolExecutor(8) as ex: rr = list(ex.map(lambda n: (n, P.run(port, bins[port], n, cd / f"{n}.txt")), names))
        clean[port] = {n: (cd / f"{n}.txt", r) for n, r in rr}
    for port in ("pb", "md"):
        ok = sum(bool(C.load(clean["ch"][n][0]) and C.load(clean[port][n][0]) and C.first_divergence(C.load(clean["ch"][n][0]), C.load(clean[port][n][0]), P.KEEPC, True) is None) for n in names)
        assert ok == len(names), f"{port} baseline {ok}/{len(names)}"; print(f"baseline {port} {ok}/{len(names)}", flush=True)
    todo = [(st, d) for st in ("agree", "disagree") for d in sample[st]]
    if os.environ.get("E14_TODO"): todo = todo[:int(os.environ["E14_TODO"])]
    for stratum, d in todo:
        cn = d["ref"]; ref_t = (mutate.SRCDIR / f"{d['ref_file']}.c").read_text(encoding="latin-1"); ref_f = S.functions(ref_t)
        tg = {}  # role -> (port, file, text, funcs, funcname)
        pb_t = (P.PB_SRC / f"{d['pb_file']}.c").read_text(encoding="latin-1"); pb_f = S.functions(pb_t); tg["pb:match"] = ("pb", d["pb_file"], pb_t, pb_f, d["pb"])
        md_t = (P.MD_SRC / f"{d['md_file']}.cs").read_text(encoding="latin-1"); md_f = S.functions(md_t); tg["md:match"] = ("md", d["md_file"], md_t, md_f, d["md"])
        if d["md_oracle"] and d["md_oracle"] != d["md"]:
            ot = (P.MD_SRC / f"{d['md_oracle_file']}.cs").read_text(encoding="latin-1"); tg["md:name"] = ("md", d["md_oracle_file"], ot, S.functions(ot), d["md_oracle"])
        rs = S.sites(ref_t, ref_f[cn]); al = {}
        for k, (port, f, t, fs, nm) in tg.items(): al[k] = S.align(rs, S.sites(t, fs[nm], port == "md"), 0.5) if nm in fs else {}
        cand = [i for i in range(len(rs)) if any(i in a for a in al.values())]; by_kind = {}
        for i in cand: by_kind.setdefault(rs[i]["kind"], []).append(i)
        pick = []; kinds = list(by_kind); rng.shuffle(kinds)
        while len(pick) < min(per_fn, len(cand)):
            for k in kinds:
                if by_kind[k] and len(pick) < per_fn: pick.append(by_kind[k].pop(rng.randrange(len(by_kind[k]))))
        for si in pick:
            site = rs[si]; jobs = [("ch", "ch", cn, d["ref_file"], ref_t, ref_f[cn], site, "ref")]
            for k, (port, f, t, fs, nm) in tg.items():
                if si in al[k]: jobs.append((k, port, nm, f, t, fs[nm], S.sites(t, fs[nm], port == "md")[al[k][si][0]], al[k][si][1]))
            for k in ("pb:match", "md:match"):   # same-file control: another function of the matcher target's file, same operator kind
                port, f, t, fs, nm = tg[k]; opts = []
                for g, span in fs.items():
                    if g == nm: continue
                    for ts in S.sites(t, span, port == "md"):
                        if ts["kind"] == site["kind"]: opts.append((g, span, ts))
                if opts: g, span, ts = rng.choice(opts); jobs.append((k.split(":")[0] + ":ctl", port, g, f, t, span, ts, "same-file"))
            for role, port, fname, f, t, span, tsite, score in jobs:
                probe = P.PROBE_CS if port == "md" else P.PROBE_C
                mt = S.apply(t, tsite); mt = mt[:span[0]] + probe + mt[span[0]:]
                tag = f"{cn}_{si}_{role.replace(':', '')}"; rec = dict(ref=cn, stratum=stratum, site=si, role=role, port=port, function=fname, file=f, kind=site["kind"], change=f'{tsite["old"]}->{tsite["new"]}', align=score, seed=SEED)
                binary = P.build(port, f, mt, tag)
                if binary is None: rec["status"] = "does not build"
                else:
                    per = P.evaluate(port, binary, clean[port], names, tag); rec["status"] = "ok"; rec["demos"] = per
                    rec["reached"] = sum(v["reach"] for v in per.values()); rec["killed"] = sum(v["outcome"] == "killed" for v in per.values()); rec["crash"] = sum(v["outcome"] == "crash" for v in per.values())
                    shutil.rmtree(P.OUT / "bin" / tag, ignore_errors=True); shutil.rmtree(P.W / "mut" / tag, ignore_errors=True)
                fh.write(json.dumps(rec) + "\n"); fh.flush(); print(tag, rec["status"], rec.get("reached"), rec.get("killed"), rec.get("crash"), flush=True)
if __name__ == "__main__": main()
