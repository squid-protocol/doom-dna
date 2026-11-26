/* DOOM-E13 headless platform layer for doomgeneric-family engines. Our own code; no third-party source.
 * Writes one digest line per game tic (after the playsim) so two engines playing the same demo can be compared tic by tic.
 * Digest line: gametic leveltime prndindex rndindex x y z angle health armor readyweapon ammo0 ammo1 ammo2 ammo3 nmobjs-free-field(0)
 * The file is chosen by $E13_DIGEST. A fake clock makes timing deterministic (the demo is played with -timedemo, one tic per loop). */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "doomgeneric.h"
#include "doomstat.h"
#include "d_player.h"
#include "p_mobj.h"
#include "m_random.h"
#include "p_local.h"

extern int prndindex, rndindex;
extern int leveltime;
static FILE *dig = NULL;
static uint32_t fake_ms = 0;

void DG_Init(void) {}
void DG_DrawFrame(void) {}
void DG_SleepMs(uint32_t ms) { fake_ms += ms; }
uint32_t DG_GetTicksMs(void) { return fake_ms += 1; }
int DG_GetKey(int *pressed, unsigned char *key) { (void)pressed; (void)key; return 0; }
void DG_SetWindowTitle(const char *title) { (void)title; }

void E13_Digest(void)
{
    player_t *p = &players[consoleplayer];
    if (!dig) { const char *f = getenv("E13_DIGEST"); dig = fopen(f ? f : "e13_digest.txt", "w"); if (!dig) return; setvbuf(dig, NULL, _IOFBF, 1 << 16); }
    if (!p->mo) return;
    fprintf(dig, "%d %d %d %d %d %d %d %u %d %d %d %d %d %d %d\n", gametic, leveltime, prndindex, rndindex,
            (int)p->mo->x, (int)p->mo->y, (int)p->mo->z, (unsigned)p->mo->angle, p->health, p->armorpoints,
            (int)p->readyweapon, p->ammo[0], p->ammo[1], p->ammo[2], p->ammo[3]);
}
void E13_DigestClose(void) { if (dig) { fclose(dig); dig = NULL; } }

int main(int argc, char **argv)
{
    atexit(E13_DigestClose);
    doomgeneric_Create(argc, argv);
    for (;;) doomgeneric_Tick();
    return 0;
}
