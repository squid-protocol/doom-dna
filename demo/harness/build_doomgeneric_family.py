"""Build a doomgeneric-family engine (doomgeneric, doom-ascii-like trees) headless with the E13 per-tic digest.
Copies the pinned clone to a work directory (the clone is never modified), inserts one call after the playsim tic, compiles.
Usage: python build_doomgeneric_family.py <src_dir_with_c_files> <out_dir>   (src_dir is e.g. repos/doomgeneric/doomgeneric)"""
import re, shutil, subprocess, sys
from pathlib import Path
src, out = Path(sys.argv[1]), Path(sys.argv[2])
HERE = Path(__file__).resolve().parent
if out.exists(): shutil.rmtree(out)
shutil.copytree(src, out)
# 1. one inserted call, after the per-tic game time advance (anchor: the leveltime increment in P_Ticker)
p = out / "p_tick.c"; t = p.read_text()
anchor = re.search(r"\n(\s*)leveltime\+\+;[^\n]*\n", t)
assert anchor, "anchor 'leveltime++;' not found in p_tick.c"
t = t[:anchor.end()] + f"{anchor.group(1)}{{ extern void E13_Digest(void); E13_Digest(); }}\n" + t[anchor.end():]
p.write_text(t)
# 2. sources: the Makefile's object list minus the platform file, plus ours
mk = (src / "Makefile").read_text()
objs = re.search(r"SRC_DOOM\s*=\s*(.*)", mk).group(1).split()
objs = [o[:-2] + ".c" for o in objs if o not in ("doomgeneric_xlib.o", "doomgeneric_sdl.o")]
shutil.copy(HERE / "e13_headless.c", out / "e13_headless.c")
cmd = ["gcc", "-O2", "-w", "-DNORMALUNIX", "-DLINUX", "-D_DEFAULT_SOURCE", "-fcommon", "-o", str(out / "engine")] + [str(out / o) for o in objs] + [str(out / "e13_headless.c"), "-lm"]
print(" ".join(cmd[:8]), "... (%d files)" % len(objs))
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stdout[-1500:], r.stderr[-2500:])
sys.exit(r.returncode)
