"""Build an SDL2-based DOOM engine (chocolate-doom family) headless with the E13 per-tic digest.
Usage: python build_sdl_engine.py <clone_dir> <out_dir> [extra cmake args...]
Copies the clone to out_dir/src (the clone is never modified), inserts one call after the leveltime increment in p_tick.c and appends our
digest function to that file, then configures and builds with the private SDL2 prefix. Our inserted code only; no third-party source is stored."""
import re, shutil, subprocess, sys
from pathlib import Path
import os
clone, out = Path(sys.argv[1]), Path(sys.argv[2]); extra = sys.argv[3:]
PRND = os.environ.get("E13_PRND", "prndindex"); RND = os.environ.get("E13_RND", "rndindex"); ARMOR = os.environ.get("E13_ARMOR", "p->armorpoints")
PRE = os.environ.get("E13_PRE", "extern int prndindex, rndindex;")  # declarations the RNG names need (boom family: #include \"m_random.h\")
SUB = os.environ.get("E13_SUBDIR", "")  # CMake root inside the clone (boom family: prboom2)
TARGET = os.environ.get("E13_TARGET")  # ninja target to build (the engine executable)
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study")
src = out / "src"
if out.exists(): shutil.rmtree(out)
out.mkdir(parents=True); shutil.copytree(clone, src, ignore=shutil.ignore_patterns(".git", "*.wad", "*.WAD"))
cands = [p for p in src.rglob("p_tick.c") if "leveltime++" in p.read_text(errors="replace")]
assert len(cands) == 1, cands
# the study clones omit the other games' directories; give CMake empty stand-in libraries so it can configure (only the doom target is built)
sdir = cands[0].parent.parent
for name in ("heretic", "hexen", "strife", "setup"):
    d = sdir / name
    if not d.exists() and (sdir / "CMakeLists.txt").exists() and name in (sdir / "CMakeLists.txt").read_text():
        d.mkdir(); (d / "stub.c").write_text("void D_DoomMain(void) {}\nvoid SetupMain(void) {}\n")
        (d / "CMakeLists.txt").write_text(f"add_library({name} STATIC stub.c)\n")
p = cands[0]; t = p.read_text(errors="replace")
m = re.search(r"\n([ \t]*)leveltime\+\+;[^\n]*\n", t); assert m
t = t[:m.end()] + f"{m.group(1)}E13_Digest();\n" + t[m.end():]
# forward declaration right after the first #include line, definition appended at the end of the file
inc = re.search(r"\n#include[^\n]*\n", t)
t = t[:inc.end()] + "void E13_Digest(void);\n" + t[inc.end():]
t += PRE + "\n#define E13_PRND (" + PRND + ")\n#define E13_RND (" + RND + ")\n#define E13_ARMOR (" + ARMOR + ")\n"
t += r'''

/* ---- DOOM-E13 per-tic digest (our code) ---- */
#include <stdio.h>
#include <stdlib.h>
extern int gametic;
static unsigned long long e13_fnv(unsigned long long h, int v) { unsigned int u = (unsigned int)v; int i; for (i = 0; i < 4; i++) { h ^= (u >> (8 * i)) & 0xff; h *= 0x100000001b3ULL; } return h; }
static FILE *e13_dig = NULL;
static void e13_close(void) { if (e13_dig) { fclose(e13_dig); e13_dig = NULL; } }
void E13_Digest(void)
{
    player_t *p = &players[consoleplayer];
    if (!e13_dig) { const char *f = getenv("E13_DIGEST"); e13_dig = fopen(f ? f : "e13_digest.txt", "w"); if (!e13_dig) return; setvbuf(e13_dig, NULL, _IOLBF, 1 << 12); atexit(e13_close); }
    if (!p->mo) return;
    unsigned long long msum = 0, sh = 0xcbf29ce484222325ULL; int nm = 0, i, cmask = 0;
    for (i = 0; i < 6; i++) if (p->cards[i]) cmask |= 1 << i;
    for (thinker_t *th = thinkercap.next; th != &thinkercap; th = th->next)
        if (th->function.acp1 == (actionf_p1)P_MobjThinker && (mobj_t *)th != p->mo) {
            mobj_t *m = (mobj_t *)th; unsigned long long h = 0xcbf29ce484222325ULL;
            h = e13_fnv(h, (int)m->type); h = e13_fnv(h, (int)m->x); h = e13_fnv(h, (int)m->y); h = e13_fnv(h, (int)m->z); h = e13_fnv(h, (int)m->angle);
            h = e13_fnv(h, (int)m->momx); h = e13_fnv(h, (int)m->momy); h = e13_fnv(h, (int)m->momz); h = e13_fnv(h, (int)m->health);
            msum += h; nm++;
        }
    for (i = 0; i < numsectors; i++) { sh = e13_fnv(sh, (int)sectors[i].floorheight); sh = e13_fnv(sh, (int)sectors[i].ceilingheight); sh = e13_fnv(sh, (int)sectors[i].special); }
    fprintf(e13_dig, "%d %d %d %d %d %d %d %u %d %d %d %d %d %d %d %d %llu %llu %d\n", gametic, leveltime, E13_PRND, E13_RND,
            (int)p->mo->x, (int)p->mo->y, (int)p->mo->z, (unsigned)p->mo->angle, p->health, E13_ARMOR,
            (int)p->readyweapon, p->ammo[0], p->ammo[1], p->ammo[2], p->ammo[3], nm, msum, sh, cmask);
}
'''
p.write_text(t)

# optional: trace every gameplay-RNG call with the calling function's name (E13_TRACE=1); the trace file is chosen by $E13_TRACE at run time
if os.environ.get("E13_TRACE_BUILD"):
    mh = next(src.rglob("m_random.h")); mc = next(src.rglob("m_random.c"))
    h = mh.read_text(); h = re.sub(r"int\s+P_Random\s*\(\s*void\s*\)\s*;", "int P_Random (void);\nint E13_PRandom(const char *fn);\n#ifndef E13_NO_MACRO\n#define P_Random() E13_PRandom(__func__)\n#endif", h, count=1); mh.write_text(h)
    c = mc.read_text(); c = "#define E13_NO_MACRO\n" + c + r'''
#include <stdio.h>
#include <stdlib.h>
extern int gametic;
static FILE *e13_tr = NULL;
int E13_PRandom(const char *fn)
{
    int v = P_Random();
    if (!e13_tr) { const char *f = getenv("E13_TRACE"); if (!f) return v; e13_tr = fopen(f, "w"); if (!e13_tr) return v; setvbuf(e13_tr, NULL, _IOLBF, 1 << 12); }
    fprintf(e13_tr, "%d %s %d\n", gametic, fn, prndindex);
    return v;
}
'''
    mc.write_text(c)

if os.environ.get("E13_TRACE_BUILD") and os.environ.get("E13_TRACE_SIGHT"):
    ps = next(src.rglob("p_sight.c")); t = ps.read_text()
    t2 = re.sub(r"boolean\s+P_CheckSight\s*\(\s*mobj_t\s*\*\s*t1\s*,\s*mobj_t\s*\*\s*t2\s*\)", "static boolean P_CheckSight_orig(mobj_t *t1, mobj_t *t2)", t, count=1)
    assert t2 != t, "P_CheckSight definition not found"
    t2 += r'''
#include <stdio.h>
#include <stdlib.h>
extern int gametic;
static FILE *e13_sight = NULL;
boolean P_CheckSight(mobj_t *t1, mobj_t *t2)
{
    boolean r = P_CheckSight_orig(t1, t2);
    if (!e13_sight) { const char *f = getenv("E13_SIGHT"); if (!f) return r; e13_sight = fopen(f, "w"); if (!e13_sight) return r; setvbuf(e13_sight, NULL, _IOLBF, 1 << 12); }
    fprintf(e13_sight, "%d %d %d %d %d %d %d %d\n", gametic, (int)t1->type, (int)t1->x, (int)t1->y, (int)t2->x, (int)t2->y, (int)t2->type, (int)r);
    return r;
}
'''
    ps.write_text(t2)

# optional: the goal-directed bot (E13_BOT_BUILD=1): appended to g_game.c, hooked after the ticcmd copy so it also feeds -record
if os.environ.get("E13_BOT_BUILD"):
    gg = next(src.rglob("g_game.c")); g = gg.read_text()
    hook = "memcpy(cmd, &netcmds[i], sizeof(ticcmd_t));\n"
    assert g.count(hook) == 1, "ticcmd copy anchor not found"
    g = g.replace(hook, hook + "\t    if (i == consoleplayer && E13_BotActive()) E13_BotCmd(cmd);\n")
    gt = re.search(r"\nvoid\s+G_Ticker\s*\(\s*void\s*\)", g); assert gt, "G_Ticker not found"
    g = g[:gt.start()] + "\nvoid E13_BotCmd(ticcmd_t *cmd);\nint E13_BotActive(void);\n" + g[gt.start():]
    g += (Path(__file__).resolve().parent / "bot/e13_bot.c.inc").read_text()
    gg.write_text(g)
env = {"PATH": f"{W}/venv/bin:/usr/bin:/bin", "HOME": str(out)}
bd = out / "build"
cfg = [str(W / "venv/bin/cmake"), "-S", str(src / SUB), "-B", str(bd), "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_PREFIX_PATH={W}/prefix", "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"] + extra
r = subprocess.run(cfg, capture_output=True, text=True, env=env); print(r.stdout[-600:], r.stderr[-1800:])
if r.returncode: sys.exit(r.returncode)
r = subprocess.run([str(W / "venv/bin/ninja"), "-C", str(bd), "-j8"] + ([TARGET] if TARGET else []), capture_output=True, text=True, env=env); print(r.stdout[-1200:], r.stderr[-2500:]); sys.exit(r.returncode)
