"""Shared helpers for the Mocha Doom (Java) mutant screen: demo list, demo-lump extraction, a shared Xvfb, and the one function that runs Mocha on a demo.
Why this is not the same as the C / C# engines: Mocha cannot load a WAD whose DEMO1 lump was appended after the directory (the e14/wads/<demo>.WAD files), so every demo is replayed as
IWAD + external `<demo>.lmp` found in the working directory (`-timedemo <demo>`): shareware demos use DOOM1.WAD, Freedoom demos the original freedoom2.wad (SHA-256 a8772e08...).
Mocha needs an X display (AWT) even with -nodraw; one Xvfb is shared by all workers (never one xvfb-run per job: killing the wrapper on a timeout would orphan the JVM)."""
import atexit, os, threading, shutil, struct, subprocess, tempfile, time
from pathlib import Path
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); E14 = W / "e14"; S = W / "screen/jv_v2"
DOOM1 = W / "run_mocha/DOOM1.WAD"; FREEDOOM = W / "wads_ext/freedoom_0.13.0/freedoom-0.13.0/freedoom2.wad"
CLEAN_CP = str(W / "build/mochadoom/classes")   # the plain Mocha build with the per-tic digest (the clean reference engine)
JVM = ["-XX:+UseSerialGC", "-Xmx768m", "-Xss4m"]
def demo_names(wads=E14 / "wads"):
    return sorted({p.stem for p in wads.glob("*.WAD")} | {p.parent.name for p in wads.glob("*/freedoom2.wad")})
def demo_wad(d, wads=E14 / "wads"):   # the e14 copy that carries the DEMO1 lump
    return wads / f"{d}.WAD" if (wads / f"{d}.WAD").exists() else wads / d / "freedoom2.wad"
def is_freedoom(d): return not (E14 / "wads" / f"{d}.WAD").exists()
def lmp_path(d): return S / "lmp" / f"{d}.lmp"
def extract_lmp(d):
    """write S/lmp/<d>.lmp = the DEMO1 lump of the e14 WAD"""
    data = demo_wad(d).read_bytes(); ident, n, ofs = struct.unpack("<4sii", data[:12])
    for i in range(n):
        e = ofs + 16 * i
        if data[e + 8:e + 16].rstrip(b"\0") == b"DEMO1":
            p, s = struct.unpack("<ii", data[e:e + 8]); lmp_path(d).parent.mkdir(parents=True, exist_ok=True); lmp_path(d).write_bytes(data[p:p + s]); return s
    raise SystemExit(f"no DEMO1 lump in {demo_wad(d)}")
_xvfb = None; _xlock = threading.Lock()
def display():
    """DISPLAY of the shared Xvfb (E13_DISPLAY if the launcher already has one, else start one and stop it at exit, by PID)"""
    global _xvfb
    if os.environ.get("E13_DISPLAY"): return os.environ["E13_DISPLAY"]
    with _xlock:
      if _xvfb is None:
        r, w = os.pipe(); p = subprocess.Popen(["Xvfb", "-displayfd", str(w), "-screen", "0", "640x480x24", "-nolisten", "tcp"], pass_fds=(w,), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); os.close(w)
        num = os.read(r, 16).decode().strip(); os.close(r); assert num, "Xvfb did not start"; _xvfb = (p, ":" + num)
        atexit.register(lambda: (_xvfb[0].terminate(), _xvfb[0].wait()))
    return _xvfb[1]
def run_mocha(cp, demo, extra, timeout=150, keep_home=False, tmp=None):
    """Run Mocha on one demo. Returns (home_dir, returncode, seconds); rc -9 = timeout (the JVM is killed by PID). extra = E13_* environment."""
    home = tempfile.mkdtemp(prefix="jv_", dir=str(tmp or E14)); h = Path(home)
    os.symlink(FREEDOOM if is_freedoom(demo) else DOOM1, h / ("freedoom2.wad" if is_freedoom(demo) else "DOOM1.WAD")); os.symlink(lmp_path(demo), h / f"{demo}.lmp")
    iwad = "freedoom2.wad" if is_freedoom(demo) else "DOOM1.WAD"
    cmd = ["nice", "-n", "10", "java"] + JVM + ["-cp", cp, "mochadoom.Engine", "-iwad", iwad, "-timedemo", demo, "-nodraw", "-nosound", "-nomusic"]
    env = dict(os.environ, HOME=home, DISPLAY=display(), **extra); t0 = time.time()
    p = subprocess.Popen(cmd, cwd=home, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try: rc = p.wait(timeout=timeout)
    except subprocess.TimeoutExpired: p.kill(); p.wait(); rc = -9
    if not keep_home: shutil.rmtree(home, ignore_errors=True)
    return home, rc, time.time() - t0
def verdict_outcome(vf, nrows, rc):
    """same / killed(tic, mask) / hang / crash exactly as runner.py reads the verdict file"""
    if rc == -9: return ("hang",)
    v = Path(vf).read_text().split() if Path(vf).exists() else ["none"]
    if v[0] == "div": return ("killed", int(v[1]), int(v[2]))
    if v[0] == "end": return ("same",) if int(v[1]) == nrows else ("killed", min(int(v[1]), nrows), -1)
    return ("crash",)
def nrows(clean_file): return sum(1 for l in open(clean_file) if len(l.split()) == 19)
