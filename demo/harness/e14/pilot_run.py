"""E14 phase 0 (non-confirmatory pilot): same one-token mutation at aligned sites in chocolate-doom, prboom-plus and managed-doom; each mutant scored against its own clean port.
Usage: python pilot_run.py <out.jsonl> [seed=20261127] [sites_per_function=3]   (run with the e11 venv python; E13_WIDE is set here)"""
import json, os, random, shutil, subprocess, sys, tempfile, threading
os.environ["E13_WIDE"] = "1"
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); sys.path.insert(0, str(H.parent)); sys.path.insert(0, str(H.parent / "difflocalize"))
import sites as S, mutate, compare_digests as C
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); B = W / "build"; OUT = W / "e14"; OUT.mkdir(exist_ok=True)
NINJA = W / "venv/bin/ninja"; DOTNET = W / "tools/dotnet/dotnet"
KEEPC = [k for k in C.KEEP if k != 2]   # common columns: no gameplay RNG index (prboom-plus lacks it)
PB_SRC = B / "prboom-plus/src/prboom2/src"; MD_SRC = B / "managed-doom/src/Doom/World"; CH_SRC = mutate.BASE / "src/src/doom"
PROBE_C = ' { static int e13r; extern long write(int,const void*,unsigned long); if(!e13r){e13r=1;write(2,"E13REACH\\n",9);} } '
PROBE_CS = " E13Reach.Hit(); "
# pilot functions: (choc file, choc function, prboom file, prboom matcher function, managed file, managed matcher function, managed name-oracle function)
PILOT = [("p_enemy", "A_Chase", "p_enemy", "A_Chase", "MonsterBehavior", "Chase", "Chase"),
         ("p_floor", "T_MovePlane", "p_floor", "T_MovePlane", "SectorAction", "MovePlane", "MovePlane"),
         ("p_mobj", "P_SpawnBlood", "p_mobj", "P_SpawnBlood", "Hitscan", "SpawnBlood", "SpawnBlood"),
         ("p_mobj", "P_SpawnPuff", "p_mobj", "P_SpawnPuff", "Hitscan", "SpawnPuff", "SpawnPuff"),
         ("p_maputl", "P_LineOpening", "p_maputl", "P_LineOpening", "MapCollision", "LineOpening", "LineOpening"),
         ("p_switch", "P_UseSpecialLine", "p_switch", "P_UseSpecialLine", "MapInteraction", "UseSpecialLine", "UseSpecialLine"),
         ("p_enemy", "PIT_VileCheck", "p_enemy", "PIT_VileCheck", "MonsterBehavior", "VileCheck", "VileCheck"),
         ("p_spec", "P_PlayerInSpecialSector", "p_spec", "P_PlayerInSpecialSector", "PlayerBehavior", "PlayerInSpecialSector", "PlayerInSpecialSector"),
         ("p_doors", "EV_DoDoor", "p_floor", "EV_DoElevator", "SectorAction", "DoFloor", "DoDoor"),
         ("p_floor", "EV_DoFloor", "p_floor", "EV_DoFloor", "SectorAction", "DoDoor", "DoFloor"),
         ("p_enemy", "A_SpawnFly", "p_enemy", "A_SpawnFly", "SectorAction", "CrushThing", "SpawnFly"),
         ("p_inter", "P_KillMobj", "p_inter", "P_KillMobj", "WeaponBehavior", "BFGSpray", "KillMobj")]

if os.environ.get("E14_LIMIT"): PILOT = PILOT[:int(os.environ["E14_LIMIT"])]

def demos():
    d = OUT / "wads"; d.mkdir(exist_ok=True); names = []
    srcs = [(f"s{i:04d}", W / f"gen/g{i:04d}.lmp") for i in range(20)] + [(f"c{i:04d}", W / f"gen_c/g{i:04d}.lmp") for i in range(10)] + [(f"b{i:04d}", f) for i, f in enumerate(sorted((W / "gen_bot").glob("g*.lmp"))[:12])]
    for n, f in srcs:
        if not (d / f"{n}.WAD").exists(): subprocess.run([sys.executable, str(H.parent / "make_demo_iwad.py"), str(W / "run/DOOM1.WAD"), str(f), str(d / f"{n}.WAD")], check=True)
        names.append(n)
    return names

def cmd(port, binary, wad):
    if port == "md": return [str(DOTNET), str(binary / "e13-managed-doom.dll"), "-iwad", str(wad), "-timedemo", "demo1", "-nosound", "-nomusic"]
    return [str(binary), "-iwad", str(wad), "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic", "-nogui"]

def run(port, binary, demo, digest):
    home = tempfile.mkdtemp(prefix="e14h_", dir=str(OUT)); env = dict(os.environ, HOME=home, XDG_DATA_HOME=home, XDG_CONFIG_HOME=home, LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy",
        E13_DIGEST=str(digest), DOOMWADDIR=str(W / "wads"), DOTNET_ROOT=str(W / "tools/dotnet"), DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1")
    try:
        r = subprocess.run(cmd(port, binary, OUT / "wads" / f"{demo}.WAD"), cwd=home, env=env, timeout=90, capture_output=True); rc, to, err = r.returncode, False, r.stderr
    except subprocess.TimeoutExpired: rc, to, err = -9, True, b""
    shutil.rmtree(home, ignore_errors=True); return rc, to, b"E13REACH" in err

LOCK = threading.Lock()
def build(port, file, text, tag):
    """returns the mutant binary (or directory for managed) or None"""
    if port == "ch": return mutate.build_mutant(file, text, tag)
    out = OUT / "bin" / tag; out.mkdir(parents=True, exist_ok=True)
    if port == "pb":
        f = PB_SRC / f"{file}.c"; orig = f.read_text(); f.write_text(text)
        try:
            r = subprocess.run([str(NINJA), "-C", str(B / "prboom-plus/build"), "prboom-plus"], capture_output=True, text=True)
            ok = r.returncode == 0
        finally: f.write_text(orig)
        if not ok: return None
        shutil.copy(B / "prboom-plus/build/prboom-plus", out / "prboom-plus"); return out / "prboom-plus"
    f = MD_SRC / f"{file}.cs"; orig = f.read_text(); f.write_text(text)
    try:
        env = dict(os.environ, DOTNET_CLI_HOME=str(W / "tools/dotnet_home"), DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_ROOT=str(W / "tools/dotnet"))
        r = subprocess.run([str(DOTNET), "build", "-c", "Release", "-o", str(out)], cwd=B / "managed-doom", capture_output=True, text=True, env=env); ok = r.returncode == 0
    finally: f.write_text(orig)
    return out if ok else None

def evaluate(port, binary, clean, names, tag):
    d = OUT / "res" / tag; d.mkdir(parents=True, exist_ok=True); per = {}
    with ThreadPoolExecutor(8) as ex: runs = list(ex.map(lambda n: run(port, binary, n, d / f"{n}.txt"), names))
    for n, (rc, to, reach) in zip(names, runs):
        a, b = C.load(clean[n][0]), C.load(d / f"{n}.txt")
        if to or (rc != 0 and not b): per[n] = dict(reach=reach, outcome="crash"); continue
        r = C.first_divergence(a, b or [], KEEPC, True)
        per[n] = dict(reach=reach, outcome="killed" if r else "same", tic=r[0] if r else None, field=r[1] if r else None, rc=rc)
    shutil.rmtree(d, ignore_errors=True); return per

def main():
    out_path, seed, per_fn = Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 20261127, int(sys.argv[3]) if len(sys.argv) > 3 else 3
    names = demos(); (OUT / "bin").mkdir(exist_ok=True); (OUT / "res").mkdir(exist_ok=True); rng = random.Random(seed)
    # clean runs of each port (self-reference); also gives the baseline replay check against chocolate
    bins = {"ch": mutate.BUILD / "src/chocolate-doom", "pb": None, "md": W / "build/managed-doom/bin"}
    subprocess.run([str(NINJA), "-C", str(B / "prboom-plus/build"), "prboom-plus"], check=True, capture_output=True)  # the build dir may hold a leftover mutant binary: rebuild from the restored source first
    shutil.copy(B / "prboom-plus/build/prboom-plus", OUT / "bin/prboom-plus.clean"); bins["pb"] = OUT / "bin/prboom-plus.clean"
    clean = {}
    for port in bins:
        cd = OUT / "clean" / port; cd.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(8) as ex: rr = list(ex.map(lambda n: (n, run(port, bins[port], n, cd / f"{n}.txt")), names))
        clean[port] = {n: (cd / f"{n}.txt", r) for n, r in rr}
    base = {}
    for port in ("pb", "md"):
        ok = 0
        for n in names:
            a, b = C.load(clean["ch"][n][0]), C.load(clean[port][n][0])
            ok += bool(a and b and C.first_divergence(a, b, KEEPC, True) is None)
        assert ok == len(names), f"{port} clean baseline is not identical to chocolate ({ok}/{len(names)}): refusing to continue"
        base[port] = ok; print(f"baseline replay vs chocolate, common columns, gameplay-identical: {port} {ok}/{len(names)}", flush=True)
    cl = {p: clean[p] for p in clean}
    fh = open(out_path, "a")
    for (cf, cn, pf, pn, mf, mn, mo) in PILOT:
        ref_t = (CH_SRC / f"{cf}.c").read_text(); ref_f = S.functions(ref_t)
        pb_t = (PB_SRC / f"{pf}.c").read_text(); pb_f = S.functions(pb_t)
        md_t = (MD_SRC / f"{mf}.cs").read_text(); md_f = S.functions(md_t)
        # name-oracle function in prboom-plus is the same C name (in any file of the same name); managed oracle given in the table (file: same as matcher's unless found elsewhere)
        targets = {"pb:match": ("pb", pf, pb_t, pb_f.get(pn), pn)}
        if pn != cn:
            for f2 in sorted(PB_SRC.glob("*.c")):
                t2 = f2.read_text(errors="replace"); fn2 = S.functions(t2)
                if cn in fn2: targets["pb:name"] = ("pb", f2.stem, t2, fn2[cn], cn); break
        targets["md:match"] = ("md", mf, md_t, md_f.get(mn), mn)
        if mo != mn:
            for f2 in sorted((MD_SRC).glob("*.cs")):
                t2 = f2.read_text(); fn2 = S.functions(t2)
                if mo in fn2: targets["md:name"] = ("md", f2.stem, t2, fn2[mo], mo); break
        if cn not in ref_f: print("missing ref function", cn); continue
        rs = S.sites(ref_t, ref_f[cn]); al = {}
        for k, (port, f, t, span, nm) in targets.items(): al[k] = S.align(rs, S.sites(t, span, port == "md"), 0.5) if span else {}
        cand = [i for i in range(len(rs)) if any(i in a for a in al.values())]
        if not cand: print(cn, "no aligned sites"); continue
        by_kind = {}
        for i in cand: by_kind.setdefault(rs[i]["kind"], []).append(i)
        pick = []; kinds = list(by_kind); rng.shuffle(kinds)
        while len(pick) < min(per_fn, len(cand)):
            for k in kinds:
                if by_kind[k] and len(pick) < per_fn: pick.append(by_kind[k].pop(rng.randrange(len(by_kind[k]))))
        for si in pick:
            site = rs[si]
            jobs = [("ch", cn, "ch", cf, ref_t, ref_f[cn], site, "ref")]
            for k, (port, f, t, span, nm) in targets.items():
                if si in al[k]:
                    tsite = S.sites(t, span, port == "md")[al[k][si][0]]; jobs.append((k, nm, port, f, t, span, tsite, al[k][si][1]))
            for role, fname, port, f, t, span, tsite, score in jobs:
                probe = PROBE_CS if port == "md" else PROBE_C
                mt = S.apply(t, tsite); mt = mt[:span[0]] + probe + mt[span[0]:]   # span start lies before the site, so the offsets stay valid
                tag = f"{cn}_{si}_{role.replace(':', '')}"; rec = dict(ref=cn, site=si, role=role, port=port, function=fname, file=f, kind=site["kind"], change=f'{tsite["old"]}->{tsite["new"]}', align=score, seed=seed)
                binary = build(port, f, mt, tag)
                if binary is None: rec["status"] = "does not build"
                else:
                    per = evaluate(port, binary, cl[port], names, tag); rec["status"] = "ok"; rec["demos"] = per
                    rec["reached"] = sum(v["reach"] for v in per.values()); rec["killed"] = sum(v["outcome"] == "killed" for v in per.values()); rec["crash"] = sum(v["outcome"] == "crash" for v in per.values())
                    shutil.rmtree(OUT / "bin" / tag, ignore_errors=True); shutil.rmtree(W / "mut" / tag, ignore_errors=True)
                fh.write(json.dumps(rec) + "\n"); fh.flush(); print(tag, rec["status"], rec.get("reached"), rec.get("killed"), rec.get("crash"), flush=True)
    print("baseline", base)
if __name__ == "__main__": main()
