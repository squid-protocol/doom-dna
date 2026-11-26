"""Build Mocha Doom (Java) with the E13 per-tic digest. Usage: python build_mochadoom.py <mochadoom_clone> <out_dir>
Copies src/ to out_dir (the clone is never modified), inserts one call after the leveltime increment, adds our e13.Digest class, compiles with javac."""
import re, shutil, subprocess, sys
from pathlib import Path
clone, out = Path(sys.argv[1]), Path(sys.argv[2]); H = Path(__file__).resolve().parent
if out.exists(): shutil.rmtree(out)
shutil.copytree(clone / "src", out / "src", ignore=shutil.ignore_patterns("*.class"))
p = out / "src/p/Actions/ActionsThinkers.java"; t = p.read_text()
m = re.search(r"\n([ \t]*)DOOM\(\)\.leveltime\+\+;[^\n]*\n", t); assert m, "anchor not found"
p.write_text(t[:m.end()] + f"{m.group(1)}e13.Digest.tick(DOOM(), getThinkerCap());\n" + t[m.end():])
(out / "src/e13").mkdir(); shutil.copy(H / "E13Digest.java", out / "src/e13/Digest.java")
r = subprocess.run(["javac", "-nowarn", "-cp", ".", "-d", str(out / "classes"), "mochadoom/Engine.java", "e13/Digest.java"], cwd=out / "src", capture_output=True, text=True)
print(r.stdout[-800:], r.stderr[-2500:]); sys.exit(r.returncode)
