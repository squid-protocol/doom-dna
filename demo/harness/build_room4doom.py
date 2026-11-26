"""Build room4doom (Rust rewrite of DOOM) headless with the E13 per-tic digest.
Usage: python build_room4doom.py <room4doom_clone> <out_dir>   (E13_KEEP=1 keeps an existing out_dir so a failed build can be resumed)
Copies the clone (never modified), inserts a digest of the console player after the existing per-tic trace call in gamestate (our lines only),
builds game-exe with the software feature (its --headless mode runs without a window)."""
import os, shutil, subprocess, sys
from pathlib import Path
clone, out = Path(sys.argv[1]), Path(sys.argv[2])
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); CARGO = W / "tools/rust/bin/cargo"
CALL = '''            if let Some(mo) = self.players[self.consoleplayer].mobj() {
                let st = &self.players[self.consoleplayer].status;
                e13_write(&format!("{} {} {} 0 {} {} {} {} {} {} {} {} {} {} {}", level.level_time, level.level_time, math::get_prndindex(),
                    mo.x.raw(), mo.y.raw(), mo.z.raw(), mo.angle.to_bam(), st.health, st.armorpoints, st.readyweapon as i32,
                    st.ammo[0], st.ammo[1], st.ammo[2], st.ammo[3]));
            }
'''
TAIL = '''

/// DOOM-E13 digest writer (our code): one line per tic to $E13_DIGEST.
fn e13_write(line: &str) {
    use std::io::Write;
    static F: std::sync::OnceLock<std::sync::Mutex<std::fs::File>> = std::sync::OnceLock::new();
    let f = F.get_or_init(|| std::sync::Mutex::new(std::fs::File::create(std::env::var("E13_DIGEST").unwrap_or_else(|_| "e13_digest.txt".into())).unwrap()));
    let _ = writeln!(f.lock().unwrap(), "{}", line);
}
'''
ANCHOR = "            gameplay::demo_trace::trace_tic(level);\n"
if out.exists() and not os.environ.get("E13_KEEP"): shutil.rmtree(out)
if not out.exists():
    shutil.copytree(clone, out, ignore=shutil.ignore_patterns(".git", "target", "*.wad", "*.WAD", "*.png", "*.jpg"))
p = out / "gamestate/src/lib.rs"; t = p.read_text()
if "e13_write" not in t:
    assert t.count(ANCHOR) == 1, "anchor not found"
    p.write_text(t.replace(ANCHOR, ANCHOR + CALL) + TAIL)
env = dict(os.environ, PATH=f"{W}/tools/rust/bin:{W}/venv/bin:/usr/bin:/bin", CARGO_HOME=str(W / "tools/cargo_home"), CARGO_TARGET_DIR=str(W / "tools/room4doom_target"),
           CARGO_TERM_COLOR="never", PKG_CONFIG_PATH=f"{W}/prefix/lib/pkgconfig", LIBRARY_PATH=f"{W}/prefix/lib", LD_LIBRARY_PATH=f"{W}/prefix/lib")
r = subprocess.run([str(CARGO), "build", "--release", "-p", "room4doom", ], cwd=out, capture_output=True, text=True, env=env)
print(r.stdout[-1500:]); print(r.stderr[-4000:]); sys.exit(r.returncode)
