/* mutant-screen runtime (our code). E13_MUT=<id> activates one lesion; E13_PROFILE=<file> dumps "function_id entries first_tic" at exit. */
#include <stdio.h>
#include <stdlib.h>
int e13_mut_id = -1;
unsigned e13_site[16384];
unsigned e13_fcount[16384];
int e13_first[16384];
static void e13_dump(void)
{
    const char *f = getenv("E13_PROFILE"); FILE *o; int i;
    if (!f || !(o = fopen(f, "w"))) return;
    for (i = 0; i < 16384; i++) if (e13_fcount[i]) fprintf(o, "F %d %u %d\n", i, e13_fcount[i], e13_first[i] - 1);
    for (i = 0; i < 16384; i++) if (e13_site[i]) fprintf(o, "S %d %u\n", i, e13_site[i]);
    fclose(o);
}
__attribute__((constructor)) static void e13_init(void)
{
    const char *m = getenv("E13_MUT"); if (m) e13_mut_id = atoi(m);
    if (getenv("E13_PROFILE")) atexit(e13_dump);
}
