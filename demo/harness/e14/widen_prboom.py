"""E14: give the study's prboom-plus build the same world fingerprint digest as the other C engines (the original build is player-only, 15 columns).
Replaces the body of E13_Digest in prboom2/src/p_tick.c of the private build tree (our code only). Usage: python widen_prboom.py <p_tick.c>"""
import re, sys
from pathlib import Path
p = Path(sys.argv[1]); t = p.read_text()
i = t.index("static FILE *e13_dig = NULL;")
new = r'''static unsigned long long e13_fnv(unsigned long long h, int v) { unsigned int u = (unsigned int)v; int i; for (i = 0; i < 4; i++) { h ^= (u >> (8 * i)) & 0xff; h *= 0x100000001b3ULL; } return h; }
static FILE *e13_dig = NULL;
static void e13_close(void) { if (e13_dig) { fclose(e13_dig); e13_dig = NULL; } }
void E13_Digest(void)
{
    player_t *p = &players[consoleplayer];
    if (!e13_dig) { const char *f = getenv("E13_DIGEST"); e13_dig = fopen(f ? f : "e13_digest.txt", "w"); if (!e13_dig) return; setvbuf(e13_dig, NULL, _IOFBF, 1 << 16); atexit(e13_close); }
    if (!p->mo) return;
    unsigned long long msum = 0, sh = 0xcbf29ce484222325ULL; int nm = 0, i, cmask = 0;
    for (i = 0; i < 6; i++) if (p->cards[i]) cmask |= 1 << i;
    for (thinker_t *th = thinkercap.next; th != &thinkercap; th = th->next)
        if (th->function == P_MobjThinker && (mobj_t *)th != p->mo) {
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
p.write_text(t[:i] + new)
