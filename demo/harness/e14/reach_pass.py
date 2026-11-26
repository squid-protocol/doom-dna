"""E14 reach pass: one chocolate-doom build with a once-per-run probe in every function of the 16 simulation files; run the 42 demos;
write reach.json {function: [demos that entered it]}. Usage: python reach_pass.py (e11 venv python)"""
import json, os, re, subprocess, sys, shutil
os.environ["E13_WIDE"] = "1"
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); sys.path.insert(0, str(H.parent)); sys.path.insert(0, str(H.parent / "difflocalize"))
import sites as S, mutate, pilot_run as P
sys.argv = sys.argv[:1]
objs = []; comp, link = mutate.commands(); outdir = mutate.W / "mut" / "reach"; outdir.mkdir(parents=True, exist_ok=True)
for stem in mutate.FILES:
    t = (mutate.SRCDIR / f"{stem}.c").read_text(); fs = S.functions(t); ins = []
    for name, (b0, b1) in fs.items():
        probe = ' { static int e13r; extern long write(int,const void*,unsigned long); if(!e13r){e13r=1;write(2,"E13R %s\\n",%d);} } ' % (name, len(name) + 6)
        ins.append((b0, probe))
    for b0, probe in sorted(ins, reverse=True): t = t[:b0] + probe + t[b0:]
    tmp = mutate.SRCDIR / f"_mut_reach_{stem}.c"; tmp.write_text(t); obj = outdir / f"{stem}.o"
    c = re.sub(r"-MD -MT \S+ -MF \S+", "", comp[stem]); c = re.sub(r" -o \S+\.o ", f" -o {obj} ", c); c = re.sub(r" -c \S+$", f" -c {tmp}", c)
    r = subprocess.run(c, shell=True, cwd=mutate.BUILD, capture_output=True, text=True); tmp.unlink(missing_ok=True)
    assert r.returncode == 0, (stem, r.stderr[-400:]); objs.append(obj)
marker = " src/CMakeFiles/chocolate-doom.dir/i_main.c.o "; binp = outdir / "chocolate-doom"
l = link.replace(marker, marker + " " + " ".join(map(str, objs)) + " ", 1); l = re.sub(r"-Wl,--dependency-file=\S+", "", l); l = l.replace(" -o src/chocolate-doom ", f" -o {binp} ")
r = subprocess.run(l, shell=True, cwd=mutate.BUILD, capture_output=True, text=True); assert r.returncode == 0, r.stderr[-400:]
names = P.demos(); reach = {}
def one(n):
    home = P.tempfile.mkdtemp(prefix="e14h_", dir=str(P.OUT)); env = dict(os.environ, HOME=home, XDG_DATA_HOME=home, XDG_CONFIG_HOME=home, LD_LIBRARY_PATH=str(P.W / "prefix/lib"), SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", E13_DIGEST=str(Path(home) / "d.txt"))
    r = subprocess.run(P.cmd("ch", binp, P.OUT / "wads" / f"{n}.WAD"), cwd=home, env=env, timeout=90, capture_output=True); shutil.rmtree(home, ignore_errors=True)
    return n, sorted(set(re.findall(rb"E13R (\w+)", r.stderr)))
with P.ThreadPoolExecutor(8) as ex:
    for n, fs in ex.map(one, names):
        for f in fs: reach.setdefault(f.decode(), []).append(n)
json.dump(reach, open(H / "reach.json", "w"), indent=0, sort_keys=True)
print(len(reach), "functions reached by at least one demo; >=5 demos:", sum(len(v) >= 5 for v in reach.values()))
