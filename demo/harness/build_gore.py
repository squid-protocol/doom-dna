"""Build gore (Go translation of doomgeneric) headless with the E13 per-tic digest.
Usage: python build_gore.py <gore_clone> <out_dir>. Copies the clone (never modified), inserts one call after the leveltime increment,
adds our digest file and a headless driver, relaxes go.mod's go directive for the local toolchain, builds with the private Go."""
import re, shutil, subprocess, sys
from pathlib import Path
clone, out = Path(sys.argv[1]), Path(sys.argv[2]); H = Path(__file__).resolve().parent
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); GO = W / "tools/go/bin/go"
if out.exists(): shutil.rmtree(out)
shutil.copytree(clone, out, ignore=shutil.ignore_patterns(".git", "example", "static", "testdata", "*.png", "*.wad", "*.WAD"))
t = (out / "doom.go").read_text()
m = re.search(r"\n(\t)// for par times\n\tleveltime\+\+\n", t); assert m, "anchor not found"
(out / "doom.go").write_text(t[:m.end()] + "\te13Digest()\n" + t[m.end():])
import os
if os.environ.get("E13_FIX_CROSSSUBSECTOR"):  # causal test: the translation indexes segs[sub.Ffirstline] inside a loop over i (C: seg++); use the loop variable
    t = (out / "doom.go").read_text()
    a = t.index("func p_CrossSubsector("); b = t.index("seg := &segs[sub.Ffirstline]", a)
    (out / "doom.go").write_text(t[:b] + "seg := &segs[i]" + t[b + len("seg := &segs[sub.Ffirstline]"):])
if os.environ.get("E13_TRACE_BUILD"):
    t = (out / "doom.go").read_text()
    old = "func p_Random() int32 {\n\tprndindex = (prndindex + 1) & 0xff\n"
    assert old in t; (out / "doom.go").write_text(t.replace(old, old + "\te13Trace()\n", 1))
if os.environ.get("E13_TRACE_BUILD") and os.environ.get("E13_TRACE_SIGHT"):
    t = (out / "doom.go").read_text()
    assert "func p_CheckSight(t1 *mobj_t, t2 *mobj_t) boolean {" in t
    (out / "doom.go").write_text(t.replace("func p_CheckSight(t1 *mobj_t, t2 *mobj_t) boolean {", "func p_CheckSight_orig(t1 *mobj_t, t2 *mobj_t) boolean {", 1))
    (out / "e13sight.go").write_text(open(H / "gore/e13sight.go").read())
shutil.copy(H / "gore/e13digest.go", out / "e13digest.go")
(out / "cmd/e13").mkdir(parents=True); shutil.copy(H / "gore/main.go", out / "cmd/e13/main.go")
g = (out / "go.mod").read_text(); (out / "go.mod").write_text(re.sub(r"(?m)^go [0-9.]+$", "go 1.23", g))
env = {"PATH": "/usr/bin:/bin", "HOME": str(out), "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=mod", "GOPATH": str(W / "tools/gopath"), "GOCACHE": str(W / "tools/gocache"), "GOPROXY": "off", "CGO_ENABLED": "0"}
r = subprocess.run([str(GO), "build", "-o", str(out / "engine"), "./cmd/e13"], cwd=out, capture_output=True, text=True, env=env)
print(r.stdout[-800:], r.stderr[-2500:]); sys.exit(r.returncode)
