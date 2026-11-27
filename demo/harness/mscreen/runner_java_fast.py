"""Faster-launch variant of runner_java.py: identical runner (same store schema, resumable, hang rule, load governor, outcome reading); ONLY the java command line changes.
Differences: classpath = jars of bin/inst + bin/base (screen/jv_v2/fast/{inst,base}.jar, built with `jar --create --no-manifest -C bin/<x> .`; required because AppCDS cannot archive from directories),
an AppCDS dynamic archive (screen/jv_v2/fast/mocha_inst.jsa, built with -XX:ArchiveClassesAtExit on one run), C1-only JIT, one compiler thread, no perf-data mmap.
If bin/inst or bin/base is ever rebuilt, rebuild the jars and the archive (see docs/notes/MUTANT_SCREEN_JAVA_FAST.md). If the archive is missing/mismatched the JVM silently falls back to normal class loading (-Xshare:auto).
Usage: identical to runner_java.py."""
import sys
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); import jv_common as J
FAST = J.S / "fast"
J.JVM = ["-XX:+UseSerialGC", "-Xmx768m", "-Xss4m", f"-XX:SharedArchiveFile={FAST / 'mocha_inst.jsa'}", "-Xshare:auto", "-XX:TieredStopAtLevel=1", "-XX:CICompilerCount=1", "-XX:-UsePerfData"]
src = (H / "runner.py").read_text()
a = src.index("def run(demo, extra, timeout=None):"); b = src.index("def refrows(demo)")
new = '''def run(demo, extra, timeout=None):
    cp = str(J.S / "fast/inst.jar") + ":" + str(J.S / "fast/base.jar"); home, rc, _ = J.run_mocha(cp, demo, dict(extra), timeout=timeout or a.timeout, keep_home=True, tmp=J.E14)
    return home, rc
'''
src = src[:a] + new + src[b:]
src = src.replace('binary = screen / ("bin/e13-managed-doom.dll" if a.engine == "md" else ("prboom-plus" if a.engine == "pb" else "chocolate-doom"))', 'binary = None', 1)
assert "J.run_mocha" in src and "binary = None" in src
sys.argv[0] = str(H / "runner.py"); exec(compile(src, str(H / "runner.py"), "exec"), {"__name__": "__main__", "__file__": str(H / "runner.py"), "J": J})
