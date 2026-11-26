/* DOOM-E13 headless driver for PureDOOM (single-header engine). Our own code; the engine header is patched in a work copy only.
 * Same digest line format as e13_headless.c. */
#include <stdio.h>
#include <stdlib.h>
#define DOOM_IMPLEMENT_PRINT
#define DOOM_IMPLEMENT_MALLOC
#define DOOM_IMPLEMENT_FILE_IO
#define DOOM_IMPLEMENT_GETTIME
#define DOOM_IMPLEMENT_EXIT
#define DOOM_IMPLEMENT_GETENV
#define DOOM_IMPLEMENTATION
#include "PureDOOM.h"

static FILE *dig = NULL;
void e13_digest(void)
{
    player_t *p = &players[consoleplayer];
    if (!dig) { const char *f = getenv("E13_DIGEST"); dig = fopen(f ? f : "e13_digest.txt", "w"); if (!dig) return; setvbuf(dig, NULL, _IOFBF, 1 << 16); }
    if (!p->mo) return;
    fprintf(dig, "%d %d %d %d %d %d %d %u %d %d %d %d %d %d %d\n", gametic, leveltime, prndindex, rndindex,
            (int)p->mo->x, (int)p->mo->y, (int)p->mo->z, (unsigned)p->mo->angle, p->health, p->armorpoints,
            (int)p->readyweapon, p->ammo[0], p->ammo[1], p->ammo[2], p->ammo[3]);
}
static void close_digest(void) { if (dig) { fclose(dig); dig = NULL; } }

int main(int argc, char **argv)
{
    atexit(close_digest);
    doom_init(argc, argv, 0);
    for (;;) doom_force_update();
    return 0;
}
