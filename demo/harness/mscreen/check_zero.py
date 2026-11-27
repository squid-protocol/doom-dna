"""Zero-lesion check for a schemata build: with no lesion active, every demo must finish with verdict 'end <rows>' equal to the clean reference.
Usage: python check_zero.py <engine c|md> <screen_dir> <clean_dir>"""
import os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"; eng, screen, clean = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
names = sorted({p.stem for p in (E14 / "wads").glob("*.WAD")} | {p.parent.name for p in (E14 / "wads").glob("*/freedoom2.wad")})
def wadpath(d): return (E14 / "wads" / f"{d}.WAD") if (E14 / "wads" / f"{d}.WAD").exists() else (E14 / "wads" / d / "freedoom2.wad")
def one(n):
    home = tempfile.mkdtemp(prefix="zc_", dir=str(E14)); vf = Path(home) / "v.txt"
    env = dict(os.environ, HOME=home, LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", DOTNET_ROOT=str(W / "tools/dotnet"), DOTNET_NOLOGO="1", E13_REF=str(clean / f"{n}.txt"), E13_VERDICT=str(vf), E13_NODIGEST="1", DOOMWADDIR=str(W / "wads"))
    cmd = [str(W / "tools/dotnet/dotnet"), str(screen / "bin/e13-managed-doom.dll"), "-iwad", str(wadpath(n)), "-timedemo", "demo1", "-nosound", "-nomusic"] if eng == "md" else [str(screen / ("prboom-plus" if eng == "pb" else "chocolate-doom")), "-iwad", str(wadpath(n)), "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic", "-nogui"]
    try: subprocess.run(cmd, cwd=home, env=env, timeout=120, capture_output=True)
    except subprocess.TimeoutExpired: pass
    v = vf.read_text().split() if vf.exists() else ["none"]; shutil.rmtree(home, ignore_errors=True)
    rows = sum(1 for l in open(clean / f"{n}.txt") if len(l.split()) == 19)
    return v[0] == "end" and int(v[1]) == rows, v, rows
with ThreadPoolExecutor(6) as ex: res = list(ex.map(one, names))
bad = [(n, r[1], r[2]) for n, r in zip(names, res) if not r[0]]
print(f"zero-lesion check ({eng}): {len(names) - len(bad)}/{len(names)} demos identical to the clean reference", bad[:4])
