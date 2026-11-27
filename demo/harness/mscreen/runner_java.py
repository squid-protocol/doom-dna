"""Phenotype runner for the Mocha Doom (Java) schemata build: runner.py (unchanged; same store schema, resumable, hang handling, load governor) with its `run()` replaced by a Mocha launcher
(shared Xvfb, IWAD + external <demo>.lmp, classpath bin/inst:bin/base). Usage: python runner_java.py <screen_dir> <store.sqlite> --clean <screen_dir>/clean [--workers 3] [runner.py options]
Default --wads is e14/wads (only the demo names are taken from it; the lump files are jv_v2/lmp/<demo>.lmp, made by `validate_java.py clean`)."""
import re, sys
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); import jv_common as J
src = (H / "runner.py").read_text()
a = src.index("def run(demo, extra, timeout=None):"); b = src.index("def refrows(demo)")
new = '''def run(demo, extra, timeout=None):
    cp = str(screen / "bin/inst") + ":" + str(screen / "bin/base"); home, rc, _ = J.run_mocha(cp, demo, dict(extra), timeout=timeout or a.timeout, keep_home=True, tmp=J.E14)
    return home, rc
'''
src = src[:a] + new + src[b:]
src = src.replace('binary = screen / ("bin/e13-managed-doom.dll" if a.engine == "md" else ("prboom-plus" if a.engine == "pb" else "chocolate-doom"))', 'binary = None', 1)
assert "J.run_mocha" in src and "binary = None" in src
sys.argv[0] = str(H / "runner.py"); exec(compile(src, str(H / "runner.py"), "exec"), {"__name__": "__main__", "__file__": str(H / "runner.py"), "J": J})
