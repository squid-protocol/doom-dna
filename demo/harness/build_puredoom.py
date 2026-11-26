"""Build PureDOOM headless with the E13 per-tic digest. Usage: python build_puredoom.py <puredoom_clone_dir> <out_dir>
Copies PureDOOM.h to out_dir, inserts one call after the leveltime increment, compiles with our driver."""
import re, shutil, subprocess, sys
from pathlib import Path
src, out = Path(sys.argv[1]), Path(sys.argv[2]); HERE = Path(__file__).resolve().parent
out.mkdir(parents=True, exist_ok=True)
t = (src / "PureDOOM.h").read_text()
m = re.search(r"\n(\s*)leveltime\+\+;[^\n]*\n", t); assert m, "anchor not found"
t = t[:m.end()] + f"{m.group(1)}{{ extern void e13_digest(void); e13_digest(); }}\n" + t[m.end():]
(out / "PureDOOM.h").write_text(t); shutil.copy(HERE / "e13_pure_main.c", out / "e13_pure_main.c")
r = subprocess.run(["gcc", "-O2", "-w", "-o", str(out / "engine"), str(out / "e13_pure_main.c"), "-lm"], capture_output=True, text=True, cwd=out)
print(r.stdout[-800:], r.stderr[-2000:]); sys.exit(r.returncode)
