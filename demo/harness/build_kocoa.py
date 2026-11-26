"""Build Kocoa Doom (Kotlin Mocha) with the E13 per-tic digest. Usage: python build_kocoa.py <kocoa_clone> <out_dir>
Copies src/ (the clone is never modified), inserts one call after the leveltime increment, adds our Kotlin digest, compiles everything with the private kotlinc."""
import os, re, shutil, subprocess, sys
from pathlib import Path
clone, out = Path(sys.argv[1]), Path(sys.argv[2]); H = Path(__file__).resolve().parent
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); KC = W / "tools/kotlinc/bin/kotlinc"
if out.exists(): shutil.rmtree(out)
shutil.copytree(clone / "src", out / "src", ignore=shutil.ignore_patterns("*.class"))
p = out / "src/p/Actions/ActionsThinkers.kt"; t = p.read_text()
m = re.search(r"\n([ \t]*)DOOM\(\)\.leveltime\+\+[^\n]*\n", t); assert m, "anchor not found"
p.write_text(t[:m.end()] + f"{m.group(1)}e13.Digest.tick(DOOM(), getThinkerCap())\n" + t[m.end():])
(out / "src/e13").mkdir(); shutil.copy(H / "kocoa/Digest.kt", out / "src/e13/Digest.kt")
env = dict(os.environ, JAVA_OPTS="-Xmx4g -Xss8m")
r = subprocess.run([str(KC), "-nowarn", "-jvm-target", "17", "-language-version", "1.6", "-api-version", "1.6", "-d", str(out / "classes"), str(out / "src")], capture_output=True, text=True, env=env)
print(r.stdout[-1500:]); print(r.stderr[-3500:]); sys.exit(r.returncode)
