"""Baseline integrity guard. `snapshot` records checksums of every clean reference digest and demo WAD (run it BEFORE the screens finish); `verify` re-checks them and replays every demo with no lesion active
on both engines (the clean digests must be reproduced exactly). Reads no lesion outcome. Usage: python baselines.py snapshot|verify"""
import hashlib, json, os, subprocess, sys, shutil, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"; SNAP = W / "screen/baselines.json"
def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def files():
    out = {}
    for d in ("ch", "md"):
        for p in sorted((E14 / "clean" / d).glob("*.txt")): out[str(p.relative_to(E14))] = p
    for p in sorted((E14 / "wads").glob("*.WAD")): out[str(p.relative_to(E14))] = p
    for p in sorted((E14 / "wads").glob("*/freedoom2.wad")): out[str(p.relative_to(E14))] = p
    return out
def demos(): return sorted({p.stem for p in (E14 / "wads").glob("*.WAD")} | {p.parent.name for p in (E14 / "wads").glob("*/freedoom2.wad")})
def wadpath(d): return (E14 / "wads" / f"{d}.WAD") if (E14 / "wads" / f"{d}.WAD").exists() else (E14 / "wads" / d / "freedoom2.wad")
def replay(port, d):
    home = tempfile.mkdtemp(prefix="bl_", dir=str(E14)); vf = Path(home) / "v.txt"; clean = E14 / "clean" / port
    env = dict(os.environ, HOME=home, LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", DOTNET_ROOT=str(W / "tools/dotnet"), DOTNET_NOLOGO="1", E13_REF=str(clean / f"{d}.txt"), E13_VERDICT=str(vf), E13_NODIGEST="1")
    cmd = [str(W / "tools/dotnet/dotnet"), str(W / "screen/md_v2/bin/e13-managed-doom.dll"), "-iwad", str(wadpath(d)), "-timedemo", "demo1", "-nosound", "-nomusic"] if port == "md" else [str(W / "screen/choc_v2/chocolate-doom"), "-iwad", str(wadpath(d)), "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic", "-nogui"]
    subprocess.run(["timeout", "300"] + cmd, cwd=home, env=env, capture_output=True); v = vf.read_text().split() if vf.exists() else ["none"]; shutil.rmtree(home, ignore_errors=True)
    rows = sum(1 for l in open(clean / f"{d}.txt") if len(l.split()) == 19); return v[0] == "end" and int(v[1]) == rows
if __name__ == "__main__":
    if sys.argv[1] == "snapshot":
        with ThreadPoolExecutor(4) as ex: sums = dict(zip(files(), ex.map(md5, files().values())))
        json.dump(sums, open(SNAP, "w"), indent=0); print("snapshot of", len(sums), "files written")
    else:
        snap = json.load(open(SNAP)); cur = files(); bad = [k for k in snap if k not in cur or md5(cur[k]) != snap[k]]; new = [k for k in cur if k not in snap]
        print(f"checksums: {len(snap) - len(bad)}/{len(snap)} unchanged; changed or missing: {bad[:5]}; files not in the snapshot: {len(new)}")
        for port in ("ch", "md"):
            with ThreadPoolExecutor(6) as ex: res = list(ex.map(lambda d: replay(port, d), demos()))
            print(f"zero-lesion replay {port}: {sum(res)}/{len(res)} demos reproduce the clean digest exactly", [d for d, r in zip(demos(), res) if not r][:5])
