"""Add an in-engine early-abort comparison to the E13 digest of a chocolate-family p_tick.c (our code; idempotent).
With E13_REF=<clean digest file> the engine compares each tic's digest row with the reference row (columns: leveltime, gameplay RNG index, x y z angle health armor weapon ammo0-3,
nmobjs, mobjhash, sectorhash, keys; the angle is skipped while the reference player is dead) and, at the first mismatch, writes "div <row> <column>" to E13_VERDICT and exits.
At normal exit it writes "end <rows>". Usage: python patch_abort.py <p_tick.c>"""
import sys
from pathlib import Path
p = Path(sys.argv[1]); t = p.read_text(encoding="latin-1")
if "E13_REF" in t: print("already patched"); sys.exit(0)
a = t.index('    fprintf(e13_dig, "%d %d %d %d %d %d %d %u')
b = t.index("}", t.index("cmask);", a))
new = r'''    {
        unsigned long long v[19] = { (unsigned long long)gametic, (unsigned long long)leveltime, (unsigned long long)E13_PRND, (unsigned long long)E13_RND, (unsigned long long)(int)p->mo->x, (unsigned long long)(int)p->mo->y, (unsigned long long)(int)p->mo->z,
            (unsigned long long)(unsigned)p->mo->angle, (unsigned long long)p->health, (unsigned long long)E13_ARMOR, (unsigned long long)(int)p->readyweapon, (unsigned long long)p->ammo[0], (unsigned long long)p->ammo[1], (unsigned long long)p->ammo[2], (unsigned long long)p->ammo[3],
            (unsigned long long)nm, msum, sh, (unsigned long long)cmask };
        static int e13_rows = 0; static unsigned long long *e13_ref = NULL; static int e13_nref = -1; static const char *e13_verd = NULL;
        if (e13_nref < 0) {
            const char *rf = getenv("E13_REF"); e13_verd = getenv("E13_VERDICT"); e13_nref = 0;
            if (rf) { FILE *r = fopen(rf, "r"); if (r) { char line[512]; int cap = 0; while (fgets(line, sizeof line, r)) {
                unsigned long long x[19]; int k = sscanf(line, "%llu %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu", x, x+1, x+2, x+3, x+4, x+5, x+6, x+7, x+8, x+9, x+10, x+11, x+12, x+13, x+14, x+15, x+16, x+17, x+18);
                if (k != 19) continue; if (e13_nref == cap) { cap = cap ? cap * 2 : 4096; e13_ref = realloc(e13_ref, cap * 19 * sizeof(unsigned long long)); }
                { int j; for (j = 0; j < 19; j++) e13_ref[e13_nref * 19 + j] = x[j]; } e13_nref++; } fclose(r); } }
        }
        if (e13_nref > 0 && e13_rows < e13_nref) {
            static const int cols[] = { 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 }; unsigned long long *rr = e13_ref + e13_rows * 19; int j;
            for (j = 0; j < 17; j++) { int c = cols[j];
                if (c == 7 && (long long)(int)rr[8] <= 0) continue;
                if (v[c] != rr[c]) { if (e13_verd) { FILE *o = fopen(e13_verd, "w"); if (o) { fprintf(o, "div %d %d\n", e13_rows, c); fclose(o); } } fflush(NULL); _exit(0); } }
        }
        e13_rows++;
        if (e13_verd && e13_nref >= 0) { static int reg = 0; if (!reg) { reg = 1; atexit(e13_verdict_end); } e13_rows_out = e13_rows; }
        if (e13_dig) fprintf(e13_dig, "%d %d %d %d %d %d %d %u %d %d %d %d %d %d %d %d %llu %llu %d\n", gametic, leveltime, E13_PRND, E13_RND,
            (int)p->mo->x, (int)p->mo->y, (int)p->mo->z, (unsigned)p->mo->angle, p->health, E13_ARMOR,
            (int)p->readyweapon, p->ammo[0], p->ammo[1], p->ammo[2], p->ammo[3], nm, msum, sh, cmask);
    }
'''
t = t[:a] + new + t[b:]
t = t.replace("static FILE *e13_dig = NULL;", "#include <unistd.h>\nstatic int e13_rows_out = 0;\nstatic void e13_verdict_end(void) { const char *vf = getenv(\"E13_VERDICT\"); FILE *o; if (!vf) return; o = fopen(vf, \"w\"); if (o) { fprintf(o, \"end %d\\n\", e13_rows_out); fclose(o); } }\nstatic FILE *e13_dig = NULL;", 1)
t = t.replace('if (!e13_dig) { const char *f = getenv("E13_DIGEST"); e13_dig = fopen(f ? f : "e13_digest.txt", "w"); if (!e13_dig) return; setvbuf(e13_dig, NULL, _IOLBF, 1 << 12); atexit(e13_close); }',
              'if (!e13_dig && !getenv("E13_NODIGEST")) { const char *f = getenv("E13_DIGEST"); e13_dig = fopen(f ? f : "e13_digest.txt", "w"); if (!e13_dig) return; setvbuf(e13_dig, NULL, _IOLBF, 1 << 12); atexit(e13_close); }', 1)
p.write_text(t, encoding="latin-1"); print("patched")
