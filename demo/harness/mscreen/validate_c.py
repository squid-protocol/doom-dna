"""Validate the schemata build: (1) with no lesion active every demo replays identically to the clean engine; (2) N random lesions run via the switch equal the same lesions rebuilt classically.
Usage: python validate_c.py <screen_dir> [N=30] [seed=1]   (screen-venv python)"""
import json, os, random, shutil, subprocess, sys, tempfile
os.environ["E13_WIDE"] = "1"
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); sys.path.insert(0, str(H.parent)); sys.path.insert(0, str(H.parent / "difflocalize"))
import compare_digests as C, mutate
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"
KEEP = C.KEEP
screen = Path(sys.argv[1]); N = int(sys.argv[2]) if len(sys.argv) > 2 else 30; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
names = sorted(p.stem for p in (E14 / "wads").glob("*.WAD"))
def run(binary, demo, digest, mut=None, profile=None):
    home = tempfile.mkdtemp(prefix="msv_", dir=str(E14)); env = dict(os.environ, HOME=home, XDG_DATA_HOME=home, XDG_CONFIG_HOME=home, LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", E13_DIGEST=str(digest))
    if mut is not None: env["E13_MUT"] = str(mut)
    if profile: env["E13_PROFILE"] = str(profile)
    try: rc = subprocess.run([str(binary), "-iwad", str(E14 / "wads" / f"{demo}.WAD"), "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic", "-nogui"], cwd=home, env=env, timeout=90, capture_output=True).returncode
    except subprocess.TimeoutExpired: rc = -9
    shutil.rmtree(home, ignore_errors=True); return rc
clean = {n: C.load(E14 / "clean/ch" / f"{n}.txt") for n in names}
def outcome(n, d, rc):
    b = C.load(d)
    if rc == -9 or (rc != 0 and not b): return ("crash",)
    r = C.first_divergence(clean[n], b or [], KEEP, True); return ("same",) if r is None else ("killed", r[0], r[1])
tmp = E14 / "msv"; tmp.mkdir(exist_ok=True); sb = screen / "chocolate-doom"; man = json.load(open(screen / "manifest.json"))
with ThreadPoolExecutor(8) as ex: z = list(ex.map(lambda n: outcome(n, tmp / f"z_{n}.txt", run(sb, n, tmp / f"z_{n}.txt")), names))
bad = [(n, o) for n, o in zip(names, z) if o != ("same",)]; print(f"(1) no lesion active: {len(names) - len(bad)}/{len(names)} demos identical to the clean engine", bad[:3], flush=True)
# profile output sanity
run(sb, names[0], tmp / "p.txt", profile=tmp / "prof.txt"); prof = [l.split() for l in open(tmp / "prof.txt")]; print("profile lines:", len(prof), "functions entered in", names[0])
rng = random.Random(seed); sites = man["sites"]; pick = rng.sample(sites, N); fails = 0
for k, s in enumerate(pick):
    with ThreadPoolExecutor(8) as ex: a = list(ex.map(lambda n: outcome(n, tmp / f"a_{n}.txt", run(sb, n, tmp / f"a_{n}.txt", mut=s["id"])), names))
    src = (mutate.SRCDIR / f"{s['file']}.c").read_bytes(); old, new = s["op"].encode(), s["new"].encode(); assert src[s["byte"]:s["byte"] + len(old)] == old
    text = (src[:s["byte"]] + new + src[s["byte"] + len(old):]).decode("latin-1"); binp = mutate.build_mutant(s["file"], text, f"v{k}")
    if not binp: print(f"lesion {s['id']} {s['fn']} {s['op']}->{s['new']}: classical rebuild failed to build (schemata accepted it)"); fails += 1; continue
    with ThreadPoolExecutor(8) as ex: b = list(ex.map(lambda n: outcome(n, tmp / f"b_{n}.txt", run(binp, n, tmp / f"b_{n}.txt")), names))
    shutil.rmtree(W / "mut" / f"v{k}", ignore_errors=True); diff = [(n, x, y) for n, x, y in zip(names, a, b) if x != y]
    print(f"lesion {s['id']:5d} {s['fn']:26s} {s['op']:>3s}->{s['new']:<3s} killed {sum(x[0]=='killed' for x in a):2d}/42 via switch, {sum(x[0]=='killed' for x in b):2d}/42 rebuilt: {'IDENTICAL' if not diff else 'DIFFERENT ' + str(diff[:2])}", flush=True); fails += bool(diff)
print(f"(2) {N - fails}/{N} lesions identical between the switch and a classical rebuild")
