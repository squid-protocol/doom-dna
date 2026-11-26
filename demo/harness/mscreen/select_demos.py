"""Choose extra demos by site-level coverage (both ports, expanded screen builds). Candidates must replay identically on chocolate-doom and managed-doom (common columns).
Usage: python select_demos.py <max_new=40> <min_gain=5>   (screen-venv python; reads screen/choc_v2 and screen/md_v2). Writes the chosen demos into the screen demo pool (E14/wads, clean/ch, clean/md) and a report."""
import os, shutil, subprocess, sys, tempfile, json
os.environ["E13_WIDE"] = "1"
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H.parent)); import compare_digests as C
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"; CAND = E14 / "cand"; CAND.mkdir(exist_ok=True)
MAXNEW, MING = int(sys.argv[1]), int(sys.argv[2]); SCH, SMD = W / "screen/choc_v2/chocolate-doom", W / "screen/md_v2/bin/e13-managed-doom.dll"
env0 = dict(os.environ, DOTNET_ROOT=str(W / "tools/dotnet"), DOTNET_NOLOGO="1", LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
base = sorted(p.stem for p in (E14 / "wads").glob("*.WAD"))
cands = []   # (name, lmp path or None if already in E14/wads)
for fam, d in (("v", W / "gen_v/sv"), ("x", W / "gen_v/cv"), ("p", W / "gen_v/sp")):
    for f in sorted(d.glob("g*.lmp")): cands.append((f"{fam}{f.stem[1:]}", f))
for i, f in enumerate(sorted((W / "gen_bot").glob("g*.lmp"))):
    if i >= 12: cands.append((f"b{i:04d}", f))
def wad(name, lmp):
    p = (E14 / "wads" / f"{name}.WAD") if lmp is None else (CAND / f"{name}.WAD")
    if lmp is not None and not p.exists(): subprocess.run([sys.executable, str(H.parent / "make_demo_iwad.py"), str(W / "run/DOOM1.WAD"), str(lmp), str(p)], check=True)
    return p
def prof(port, name, lmp):
    home = tempfile.mkdtemp(prefix="sd_", dir=str(E14)); d = CAND / name; d.mkdir(exist_ok=True); dig, pf = d / f"{port}.txt", d / f"{port}.prof"
    env = dict(env0, HOME=home, E13_DIGEST=str(dig), E13_PROFILE=str(pf))
    cmd = [str(SMD) if port == "md" else str(SCH)]
    cmd = [str(W / "tools/dotnet/dotnet"), str(SMD), "-iwad", str(wad(name, lmp)), "-timedemo", "demo1", "-nosound", "-nomusic"] if port == "md" else [str(SCH), "-iwad", str(wad(name, lmp)), "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic", "-nogui"]
    try: subprocess.run(["timeout", "120"] + cmd, cwd=home, env=env, capture_output=True)
    except Exception: pass
    shutil.rmtree(home, ignore_errors=True)
    sites = {int(l.split()[1]) for l in open(pf) if l.startswith("S")} if pf.exists() else set(); fns = {int(l.split()[1]) for l in open(pf) if l.startswith("F")} if pf.exists() else set()
    return sites, fns
def work(item):
    name, lmp = item; a = prof("ch", name, lmp); b = prof("md", name, lmp); x, y = C.load(CAND / name / "ch.txt"), C.load(CAND / name / "md.txt")
    ident = bool(x and y and len(x) > 200 and C.first_divergence(x, y, C.KEEP, True) is None); return name, a, b, ident
allitems = [(n, None) for n in base] + cands
with ThreadPoolExecutor(8) as ex: res = list(ex.map(work, allitems))
cov = {r[0]: r for r in res}; cs, cf = set(), set(); ms, mf = set(), set()
for n in base: cs |= cov[n][1][0]; cf |= cov[n][1][1]; ms |= cov[n][2][0]; mf |= cov[n][2][1]
print(f"base ({len(base)} demos): chocolate sites {len(cs)}, functions {len(cf)}; managed sites {len(ms)}, functions {len(mf)}")
ok = [r for r in res if r[0] not in base and r[3]]; print(f"candidates: {len(cands)}; identical on both engines: {len(ok)}")
chosen = []
while len(chosen) < MAXNEW:
    best = max(ok, key=lambda r: len(r[1][0] - cs) + len(r[2][0] - ms), default=None)
    if best is None or len(best[1][0] - cs) + len(best[2][0] - ms) < MING: break
    chosen.append(best[0]); cs |= best[1][0]; cf |= best[1][1]; ms |= best[2][0]; mf |= best[2][1]; ok.remove(best)
print(f"chosen {len(chosen)} demos; after: chocolate sites {len(cs)}, functions {len(cf)}; managed sites {len(ms)}, functions {len(mf)}")
lm = dict(cands)
for n in chosen:
    shutil.copy(CAND / f"{n}.WAD", E14 / "wads" / f"{n}.WAD"); shutil.copy(CAND / n / "ch.txt", E14 / "clean/ch" / f"{n}.txt"); shutil.copy(CAND / n / "md.txt", E14 / "clean/md" / f"{n}.txt")
json.dump(dict(chosen=chosen, base=base), open(W / "screen/demo_selection.json", "w"), indent=1); print(chosen)
