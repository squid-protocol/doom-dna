"""Validate the expansion lesions (ids >= 10000): N per lesion kind, switch run vs classical rebuild of the same byte edit, early-abort verdicts on all demos.
Usage: python validate_v2.py <c|md> <screen_dir> <clean_dir> [per_kind=2] [seed=1]"""
import json, os, random, shutil, subprocess, sys, tempfile, collections
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); sys.path.insert(0, str(H.parent / "difflocalize"))
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"
eng, screen, clean = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]); per = int(sys.argv[4]) if len(sys.argv) > 4 else 2; seed = int(sys.argv[5]) if len(sys.argv) > 5 else 1
names = sorted({p.stem for p in (E14 / "wads").glob("*.WAD")} | {p.parent.name for p in (E14 / "wads").glob("*/freedoom2.wad")});
def wadpath(d): return (E14 / "wads" / f"{d}.WAD") if (E14 / "wads" / f"{d}.WAD").exists() else (E14 / "wads" / d / "freedoom2.wad")
man = json.load(open(screen / "manifest.json")); env0 = dict(os.environ, DOTNET_CLI_HOME=str(W / "tools/dotnet_home"), DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_ROOT=str(W / "tools/dotnet"))
def run(binary, n, mut):
    home = tempfile.mkdtemp(prefix="vv_", dir=str(E14)); vf = Path(home) / "v.txt"
    env = dict(env0, HOME=home, LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", E13_REF=str(clean / f"{n}.txt"), E13_VERDICT=str(vf), E13_NODIGEST="1", DOOMWADDIR=str(W / "wads"))
    if mut is not None: env["E13_MUT"] = str(mut)
    cmd = [str(W / "tools/dotnet/dotnet"), str(binary), "-iwad", str(wadpath(n)), "-timedemo", "demo1", "-nosound", "-nomusic"] if eng == "md" else [str(binary), "-iwad", str(wadpath(n)), "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic", "-nogui"]
    try: rc = subprocess.run(["timeout", "40"] + cmd, cwd=home, env=env, capture_output=True).returncode
    except Exception: rc = -9
    v = vf.read_text().split() if vf.exists() else ["none"]; shutil.rmtree(home, ignore_errors=True); rows = sum(1 for l in open(clean / f"{n}.txt") if len(l.split()) == 19)
    if rc == 124: return ("hang",)
    if v[0] == "div": return ("killed", int(v[1]), int(v[2]))
    if v[0] == "end": return ("same",) if int(v[1]) == rows else ("killed", min(int(v[1]), rows), -1)
    return ("crash",)
rng = random.Random(seed); OLD = os.environ.get("V2_OLD"); new = [s for s in man["sites"] if (s["id"] < 10000 if OLD else s["id"] >= 10000)]; by = collections.defaultdict(list)
for s in new:
    if "edit" not in s: s["edit"] = [s["byte"], s["byte"] + len(s["op"]), s["new"]]   # original lesion classes: replace the operator or constant token
for s in new: by[s["kind"]].append(s)
pick = [s for k in sorted(by) for s in rng.sample(by[k], min(per, len(by[k])))]; bad = 0; skipped = 0
if eng == "md":
    tree = screen.parent / "md_classic_v2"
    if tree.exists(): shutil.rmtree(tree)
    tree.mkdir(); shutil.copytree(W / "build/managed-doom/src", tree / "src"); shutil.copy(W / "build/managed-doom/E13.csproj", tree / "E13.csproj"); shutil.copy(H.parent / "managed/E13Digest.cs", tree / "src/E13Digest.cs"); shutil.copy(H / "E13Mut.cs", tree / "src/E13Mut.cs")
elif eng == "pb":
    import re as _re
    PBB = W / "build/prboom-plus/build"; PBS = W / "build/prboom-plus/src/prboom2/src"; _cmds = subprocess.run([str(W / "venv/bin/ninja"), "-t", "commands", "prboom-plus"], cwd=PBB, capture_output=True, text=True).stdout.strip().split("\n"); _link = _cmds[-1]; _comp = {}
    for _c in _cmds[:-1]:
        _m = _re.search(r" -o src/CMakeFiles/prboom-plus\.dir/(\w+)\.c\.o ", _c)
        if _m: _comp[_m.group(1)] = _c
    def pb_classic(stem, text, tag):
        tmp = PBS / f"_cls_{tag}.c"; tmp.write_text(text, encoding="latin-1"); d = W / "mut" / tag; d.mkdir(parents=True, exist_ok=True); obj = d / "m.o"; binp = d / "prboom-plus"
        c = _re.sub(r"-MD -MT \S+ -MF \S+", "", _comp[stem]); c = _re.sub(r" -o \S+\.o ", f" -o {obj} ", c); c = _re.sub(r" -c \S+$", f" -c {tmp}", c)
        r = subprocess.run(c, shell=True, cwd=PBB, capture_output=True, text=True); tmp.unlink(missing_ok=True)
        if r.returncode: return None
        l = _link.replace(f"src/CMakeFiles/prboom-plus.dir/{stem}.c.o", str(obj)); l = _re.sub(r"-Wl,--dependency-file=\S+", "", l).replace(" -o prboom-plus ", f" -o {binp} ", 1)
        r = subprocess.run(l, shell=True, cwd=PBB, capture_output=True, text=True); return binp if r.returncode == 0 and binp.exists() else None
else:
    import mutate
for k, s in enumerate(pick):
    st, en, rep = s["edit"]
    if eng == "md":
        f = tree / "src/Doom/World" / f"{s['file']}.cs"; src = (W / "build/managed-doom/src/Doom/World" / f"{s['file']}.cs").read_bytes(); f.write_bytes(src[:st] + rep.encode("latin-1") + src[en:]); out = tree / f"bin{k}"
        r = subprocess.run([str(W / "tools/dotnet/dotnet"), "build", "-c", "Release", "-o", str(out), "-nologo"], cwd=tree, capture_output=True, text=True, env=env0); f.write_bytes(src); binp = out / "e13-managed-doom.dll" if r.returncode == 0 else None
    elif eng == "pb":
        src = (PBS / f"{s['file']}.c").read_bytes(); binp = pb_classic(s["file"], (src[:st] + rep.encode("latin-1") + src[en:]).decode("latin-1"), f"vv{k}")
    else:
        src = (mutate.SRCDIR / f"{s['file']}.c").read_bytes(); binp = mutate.build_mutant(s["file"], (src[:st] + rep.encode("latin-1") + src[en:]).decode("latin-1"), f"vv{k}")
    if not binp: print(f"lesion {s['id']} {s['kind']:12s} {s['fn']}: classical rebuild does not compile (switch accepted it)", flush=True); skipped += 1; continue
    with ThreadPoolExecutor(6) as ex: a = list(ex.map(lambda n: run(screen / ("bin/e13-managed-doom.dll" if eng == "md" else ("prboom-plus" if eng == "pb" else "chocolate-doom")), n, s["id"]), names)); b = list(ex.map(lambda n: run(binp, n, None), names))
    diff = [(n, x, y) for n, x, y in zip(names, a, b) if x != y]; shutil.rmtree(W / "mut" / f"vv{k}", ignore_errors=True)
    if eng == "md": shutil.rmtree(tree / f"bin{k}", ignore_errors=True)
    print(f"lesion {s['id']:5d} {s['kind']:12s} {s['fn'][:24]:24s} killed {sum(x[0]=='killed' for x in a):2d}/42 switch, {sum(x[0]=='killed' for x in b):2d}/42 rebuilt: {'IDENTICAL' if not diff else 'DIFFERENT ' + str(diff[:2])}", flush=True); bad += bool(diff)
print(f"{len(pick) - bad - skipped}/{len(pick) - skipped} lesions identical between the switch and a classical rebuild ({skipped} not comparable)")
