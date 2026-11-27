"""Write clean per-tic digests of a lesion-free build for every demo (E14/clean/<tag>/<demo>.txt) and report which demos replay identically to chocolate-doom on the common columns.
Usage: python make_clean_digests.py <pb|c|md> <screen_dir> <tag>"""
import os, shutil, subprocess, sys, tempfile
os.environ["E13_WIDE"] = "1"
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H.parent)); import compare_digests as C
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"; eng, screen, tag = sys.argv[1], Path(sys.argv[2]), sys.argv[3]; out = E14 / "clean" / tag; out.mkdir(parents=True, exist_ok=True)
names = sorted({p.stem for p in (E14 / "wads").glob("*.WAD")} | {p.parent.name for p in (E14 / "wads").glob("*/freedoom2.wad")})
def wadpath(d): return (E14 / "wads" / f"{d}.WAD") if (E14 / "wads" / f"{d}.WAD").exists() else (E14 / "wads" / d / "freedoom2.wad")
def one(d):
    home = tempfile.mkdtemp(prefix="cd_", dir=str(E14)); env = dict(os.environ, HOME=home, LD_LIBRARY_PATH=str(W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", DOOMWADDIR=str(W / "wads"), E13_DIGEST=str(out / f"{d}.txt"))
    cmd = [str(screen / "prboom-plus" if eng == "pb" else screen / "chocolate-doom"), "-iwad", str(wadpath(d)), "-timedemo", "demo1", "-nodraw", "-nosound", "-nomusic", "-nogui"]
    subprocess.run(["timeout", "300"] + cmd, cwd=home, env=env, capture_output=True); shutil.rmtree(home, ignore_errors=True)
    a, b = C.load(E14 / "clean/ch" / f"{d}.txt"), C.load(out / f"{d}.txt"); KEEPC = [k for k in C.KEEP if k != 2]
    return d, bool(a and b and len(b) > 200 and C.first_divergence(a, b, KEEPC, True) is None), len(b or [])
with ThreadPoolExecutor(4) as ex: res = list(ex.map(one, names))
ok = [d for d, i, n in res if i]; bad = [(d, n) for d, i, n in res if not i]; print(f"{tag}: {len(ok)}/{len(res)} demos replay identically to chocolate-doom (common columns, RNG index excluded)"); print("not identical:", bad[:20])
(E14 / f"identical_{tag}.txt").write_text("\n".join(ok))
