"""Validate the C# schemata build: N random lesions run via the switch vs the same lesion rebuilt classically (byte edit of the original source), on all demos, early-abort verdicts.
Usage: python validate_cs.py <screen_dir> <clean_dir> [N=20] [seed=1]"""
import json, os, random, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
H = Path(__file__).resolve().parent; W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"
screen, clean = Path(sys.argv[1]), Path(sys.argv[2]); N = int(sys.argv[3]) if len(sys.argv) > 3 else 20; seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
names = sorted(p.stem for p in (E14 / "wads").glob("*.WAD")); man = json.load(open(screen / "manifest.json"))
env0 = dict(os.environ, DOTNET_CLI_HOME=str(W / "tools/dotnet_home"), DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_ROOT=str(W / "tools/dotnet"))
tree = screen.parent / "md_classic"; 
if tree.exists(): shutil.rmtree(tree)
tree.mkdir(); shutil.copytree(W / "build/managed-doom/src", tree / "src"); shutil.copy(W / "build/managed-doom/E13.csproj", tree / "E13.csproj"); shutil.copy(H.parent / "managed/E13Digest.cs", tree / "src/E13Digest.cs"); shutil.copy(H / "E13Mut.cs", tree / "src/E13Mut.cs")
def run(dll, n, mut):
    home = tempfile.mkdtemp(prefix="vcs_", dir=str(E14)); vf = Path(home) / "v.txt"
    env = dict(env0, HOME=home, E13_REF=str(clean / f"{n}.txt"), E13_VERDICT=str(vf), E13_NODIGEST="1")
    if mut is not None: env["E13_MUT"] = str(mut)
    try: rc = subprocess.run([str(W / "tools/dotnet/dotnet"), str(dll), "-iwad", str(E14 / "wads" / f"{n}.WAD"), "-timedemo", "demo1", "-nosound", "-nomusic"], cwd=home, env=env, timeout=120, capture_output=True).returncode
    except subprocess.TimeoutExpired: rc = -9
    v = vf.read_text().split() if vf.exists() else ["none"]; shutil.rmtree(home, ignore_errors=True)
    rows = sum(1 for l in open(clean / f"{n}.txt") if len(l.split()) == 19)
    if rc == -9: return ("hang",)
    if v[0] == "div": return ("killed", int(v[1]), int(v[2]))
    if v[0] == "end": return ("same",) if int(v[1]) == rows else ("killed", min(int(v[1]), rows), -1)
    return ("crash",)
rng = random.Random(seed); pick = rng.sample(man["sites"], N); bad = 0
for k, s in enumerate(pick):
    f = tree / "src/Doom/World" / f"{s['file']}.cs"; src = (W / "build/managed-doom/src/Doom/World" / f"{s['file']}.cs").read_bytes(); o, nw = s["op"].encode(), s["new"].encode(); assert src[s["byte"]:s["byte"] + len(o)] == o
    f.write_bytes(src[:s["byte"]] + nw + src[s["byte"] + len(o):]); out = tree / f"bin{k}"
    r = subprocess.run([str(W / "tools/dotnet/dotnet"), "build", "-c", "Release", "-o", str(out), "-nologo"], cwd=tree, capture_output=True, text=True, env=env0); f.write_bytes(src)
    if r.returncode: print(f"lesion {s['id']} {s['fn']} {s['op']}->{s['new']}: classical rebuild does not compile (schemata accepted it)", flush=True); bad += 1; continue
    with ThreadPoolExecutor(6) as ex: a = list(ex.map(lambda n: run(screen / "bin/e13-managed-doom.dll", n, s["id"]), names)); b = list(ex.map(lambda n: run(out / "e13-managed-doom.dll", n, None), names))
    diff = [(n, x, y) for n, x, y in zip(names, a, b) if x != y]; shutil.rmtree(out, ignore_errors=True)
    print(f"lesion {s['id']:5d} {s['fn']:24s} {s['op']:>3s}->{s['new']:<3s} killed {sum(x[0]=='killed' for x in a):2d}/42 switch, {sum(x[0]=='killed' for x in b):2d}/42 rebuilt: {'IDENTICAL' if not diff else 'DIFFERENT ' + str(diff[:2])}", flush=True); bad += bool(diff)
print(f"{N - bad}/{N} lesions identical between the switch and a classical rebuild")
