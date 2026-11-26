
/* ======== DOOM-E13 goal-directed bot (our own code), appended to g_game.c in a private work copy ========
 * Finds reachable key items and manual doors (including key-locked ones), walks to them, opens doors with "use",
 * and records everything as an ordinary demo (via -record). Env: E13_BOT=1 enables, E13_BOT_TICS = length (default 9000). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "p_local.h"
#include "r_state.h"
#include "r_main.h"
#include "d_loop.h"
#include "m_fixed.h"

#define E13_CELL 32
static int e13_on = -1, e13_maxtics = 9000;
static int gw, gh, gminx, gminy, ncells, e13_level = -1, e13_tic0;
static unsigned char *c_ok, *c_req, *e_ok, *e_req;
static int *c_floor, *dist, *prevc, *queue, *doorreq, *door_lines, ndoor_lines;
static unsigned char *door_state_cache;
static int goal_type, goal_cx, goal_cy, goal_x, goal_y, goal_line, goal_age, use_tics, wander_until;
static int doors_opened, keys_got, last_px, last_py, stuck_since, idle_tics, e13_seed = 12345;
static int bad_line[1024], nbad_lines, bad_key_x[32], bad_key_y[32], nbad_keys, opened_line[1024], nopened;
static const int dxs[4] = { 1, 0, -1, 0 }, dys[4] = { 0, 1, 0, -1 };

static int e13_rand(void) { e13_seed = e13_seed * 1103515245 + 12345; return (e13_seed >> 16) & 0x7fff; }
static int held_mask(player_t *p) { int m = 0; if (p->cards[0] || p->cards[3]) m |= 1; if (p->cards[1] || p->cards[4]) m |= 2; if (p->cards[2] || p->cards[5]) m |= 4; return m; }
static int line_door_req(int sp) { switch (sp) { case 26: case 32: return 1; case 27: case 34: return 2; case 28: case 33: return 4; default: return 0; } }
static int is_manual_door(int sp) { return sp == 1 || sp == 26 || sp == 27 || sp == 28 || sp == 31 || sp == 32 || sp == 33 || sp == 34 || sp == 117 || sp == 118; }

static void e13_free(void) { free(c_ok); free(c_req); free(e_ok); free(e_req); free(c_floor); free(dist); free(prevc); free(queue); free(doorreq); free(door_lines); free(door_state_cache); c_ok = c_req = e_ok = e_req = NULL; c_floor = dist = prevc = queue = doorreq = door_lines = NULL; door_state_cache = NULL; }

static void e13_level_init(void)
{
    int i, minx = 1 << 30, maxx = -(1 << 30), miny = 1 << 30, maxy = -(1 << 30);
    e13_free();
    for (i = 0; i < numvertexes; i++) { int x = vertexes[i].x >> FRACBITS, y = vertexes[i].y >> FRACBITS; if (x < minx) minx = x; if (x > maxx) maxx = x; if (y < miny) miny = y; if (y > maxy) maxy = y; }
    gminx = minx - 64; gminy = miny - 64; gw = (maxx - gminx) / E13_CELL + 3; gh = (maxy - gminy) / E13_CELL + 3; ncells = gw * gh;
    c_ok = calloc(ncells, 1); c_req = calloc(ncells, 1); e_ok = calloc(ncells * 4, 1); e_req = calloc(ncells * 4, 1);
    c_floor = calloc(ncells, sizeof(int)); dist = calloc(ncells, sizeof(int)); prevc = calloc(ncells, sizeof(int)); queue = calloc(ncells, sizeof(int));
    doorreq = malloc(numsectors * sizeof(int)); door_lines = malloc(numlines * sizeof(int)); ndoor_lines = 0;
    for (i = 0; i < numsectors; i++) doorreq[i] = -1;
    for (i = 0; i < numlines; i++) {
        line_t *l = &lines[i];
        if (is_manual_door(l->special) && l->backsector) { doorreq[l->backsector - sectors] = line_door_req(l->special); door_lines[ndoor_lines++] = i; }
    }
    door_state_cache = calloc(numsectors, 1);
    memset(bad_line, 0, sizeof(bad_line)); nbad_lines = 0; nbad_keys = 0; nopened = 0; goal_type = 0; doors_opened = 0; keys_got = 0; idle_tics = 0; wander_until = 0; stuck_since = gametic;
    e13_level = levelstarttic; e13_tic0 = gametic;
    fprintf(stderr, "BOT level start: %d cells, %d door lines\n", ncells, ndoor_lines);
}

static int probe(fixed_t x, fixed_t y, int *floorz, int *req)
{
    mobj_t *mo = players[consoleplayer].mo; subsector_t *ss; int si, ok, saved = mo->flags;
    *req = 0;
    mo->flags &= ~MF_PICKUP;   /* P_CheckPosition would otherwise pick up every item it touches */
    ok = P_CheckPosition(mo, x, y);
    mo->flags = saved;
    if (ok) { *floorz = tmfloorz >> FRACBITS; return 1; }
    ss = R_PointInSubsector(x, y); si = ss->sector - sectors;
    if (doorreq[si] >= 0) { *floorz = ss->sector->floorheight >> FRACBITS; *req = doorreq[si]; return 1; }
    return 0;
}
static fixed_t cell_cx(int cx) { return (gminx + cx * E13_CELL + E13_CELL / 2) << FRACBITS; }
static fixed_t cell_cy(int cy) { return (gminy + cy * E13_CELL + E13_CELL / 2) << FRACBITS; }
static int cell_of(fixed_t x, fixed_t y, int *cx, int *cy) { *cx = ((x >> FRACBITS) - gminx) / E13_CELL; *cy = ((y >> FRACBITS) - gminy) / E13_CELL; return *cx >= 0 && *cy >= 0 && *cx < gw && *cy < gh; }

static int edge_ok(int c, int d, int *req)
{
    int cx = c % gw, cy = c / gw, nx = cx + dxs[d], ny = cy + dys[d], k, f0, f1, r, rr = 0;
    if (nx < 0 || ny < 0 || nx >= gw || ny >= gh) return 0;
    if (e_ok[c * 4 + d]) { *req = e_req[c * 4 + d]; return e_ok[c * 4 + d] == 1; }
    if (!probe(cell_cx(cx), cell_cy(cy), &f0, &r)) { e_ok[c * 4 + d] = 2; return 0; }
    rr |= r;
    for (k = 1; k <= 4; k++) {
        fixed_t x = cell_cx(cx) + (cell_cx(nx) - cell_cx(cx)) * k / 4, y = cell_cy(cy) + (cell_cy(ny) - cell_cy(cy)) * k / 4;
        if (!probe(x, y, &f1, &r) || f1 - f0 > 24) { e_ok[c * 4 + d] = 2; return 0; }
        rr |= r; f0 = f1;
    }
    e_ok[c * 4 + d] = 1; e_req[c * 4 + d] = rr; *req = rr; return 1;
}

static void bfs(int start, int held)
{
    int h = 0, t = 0, i;
    for (i = 0; i < ncells; i++) { dist[i] = -1; prevc[i] = -1; }
    dist[start] = 0; queue[t++] = start;
    while (h < t) {
        int c = queue[h++], d;
        for (d = 0; d < 4; d++) {
            int req, nx = c % gw + dxs[d], ny = c / gw + dys[d], n;
            if (nx < 0 || ny < 0 || nx >= gw || ny >= gh) continue;
            n = ny * gw + nx; if (dist[n] >= 0) continue;
            if (!edge_ok(c, d, &req) || (req & ~held)) continue;
            dist[n] = dist[c] + 1; prevc[n] = c; queue[t++] = n;
        }
    }
}

static int door_open(sector_t *s) { return s->ceilingheight - s->floorheight >= 40 * FRACUNIT; }

static void check_door_changes(void)
{
    int i, changed = 0;
    for (i = 0; i < numsectors; i++) if (doorreq[i] >= 0) { unsigned char o = door_open(&sectors[i]); if (o != door_state_cache[i]) { door_state_cache[i] = o; changed = 1; } }
    if (changed) { memset(c_ok, 0, ncells); memset(e_ok, 0, ncells * 4); }
}

static int is_bad_line(int li) { int i; for (i = 0; i < nbad_lines; i++) if (bad_line[i] == li) return 1; return 0; }
static int is_bad_key(int x, int y) { int i; for (i = 0; i < nbad_keys; i++) if (bad_key_x[i] == x && bad_key_y[i] == y) return 1; return 0; }

static void door_stand_point(int li, fixed_t *sx, fixed_t *sy, fixed_t *mx, fixed_t *my)
{
    line_t *l = &lines[li]; double dx = (l->v2->x - l->v1->x) / 65536.0, dy = (l->v2->y - l->v1->y) / 65536.0, len = sqrt(dx * dx + dy * dy);
    *mx = (l->v1->x + l->v2->x) / 2; *my = (l->v1->y + l->v2->y) / 2;
    *sx = *mx + (fixed_t)((dy / len) * 40 * 65536.0); *sy = *my + (fixed_t)((-dx / len) * 40 * 65536.0);
    if (P_PointOnLineSide(*sx, *sy, l) != 0) { *sx = *mx - (fixed_t)((dy / len) * 40 * 65536.0); *sy = *my - (fixed_t)((-dx / len) * 40 * 65536.0); }   /* use only works from the front side */
}

/* walks the route from the player to the goal cell; returns the index of the first closed door sector on it, or -1 */
static int first_closed_door(int goalcell, int start)
{
    int path[4096], n = 0, c = goalcell, i;
    while (c != start && c >= 0 && n < 4096) { path[n++] = c; c = prevc[c]; }
    for (i = n - 1; i >= 0; i--) {
        subsector_t *ss = R_PointInSubsector(cell_cx(path[i] % gw), cell_cy(path[i] / gw)); int si = ss->sector - sectors;
        if (doorreq[si] >= 0 && !door_open(ss->sector)) return si;
    }
    return -1;
}

/* the best usable line for a door sector: reachable stand point, not marked bad */
static int door_line_for_sector(int si, int held)
{
    int i, best = -1, bestd = 1 << 30;
    for (i = 0; i < ndoor_lines; i++) {
        int li = door_lines[i], cx, cy; fixed_t sx, sy, mx, my;
        if (lines[li].backsector - sectors != si || is_bad_line(li) || (line_door_req(lines[li].special) & ~held)) continue;
        door_stand_point(li, &sx, &sy, &mx, &my);
        if (!cell_of(sx, sy, &cx, &cy) || dist[cy * gw + cx] < 0) continue;
        if (dist[cy * gw + cx] < bestd) { bestd = dist[cy * gw + cx]; best = li; }
    }
    return best;
}

static void choose_goal(mobj_t *mo, int held)
{
    thinker_t *th; int best = -1, bestd = 1 << 30, i, pcx, pcy;
    goal_type = 0; goal_age = 0; use_tics = 0;
    cell_of(mo->x, mo->y, &pcx, &pcy);
    for (th = thinkercap.next; th != &thinkercap; th = th->next) {
        mobj_t *m; int cx, cy, col = 0, dn;
        if (th->function.acp1 != (actionf_p1)P_MobjThinker) continue;
        m = (mobj_t *)th; dn = m->info->doomednum;
        if (dn == 5 || dn == 40) col = 1; else if (dn == 6 || dn == 39) col = 2; else if (dn == 13 || dn == 38) col = 4; else continue;
        if (held & col) continue;
        if (!cell_of(m->x, m->y, &cx, &cy) || dist[cy * gw + cx] < 0 || is_bad_key(m->x >> FRACBITS, m->y >> FRACBITS)) continue;
        if (dist[cy * gw + cx] < bestd) { bestd = dist[cy * gw + cx]; best = 1; goal_type = 1; goal_x = m->x; goal_y = m->y; goal_cx = cx; goal_cy = cy; }
    }
    if (best == 1) {
        int start = pcy * gw + pcx, si = first_closed_door(goal_cy * gw + goal_cx, start);
        if (si >= 0) { int li = door_line_for_sector(si, held); if (li >= 0) { fixed_t sx, sy, mx, my; goal_type = 2; goal_line = li; door_stand_point(li, &sx, &sy, &mx, &my); goal_x = sx; goal_y = sy; cell_of(sx, sy, &goal_cx, &goal_cy); } }
        return;
    }
    for (i = 0; i < ndoor_lines; i++) {
        int li = door_lines[i], cx, cy; fixed_t sx, sy, mx, my; line_t *l = &lines[li];
        if (is_bad_line(li) || door_open(l->backsector) || (line_door_req(l->special) & ~held)) continue;
        door_stand_point(li, &sx, &sy, &mx, &my);
        if (!cell_of(sx, sy, &cx, &cy) || dist[cy * gw + cx] < 0) continue;
        if (dist[cy * gw + cx] < bestd) { bestd = dist[cy * gw + cx]; goal_type = 2; goal_line = li; goal_x = sx; goal_y = sy; goal_cx = cx; goal_cy = cy; }
    }
    if (goal_type == 2) {
        int start = pcy * gw + pcx, si = first_closed_door(goal_cy * gw + goal_cx, start);
        if (si >= 0 && si != lines[goal_line].backsector - sectors) { int li = door_line_for_sector(si, held); if (li >= 0) { fixed_t sx, sy, mx, my; goal_line = li; door_stand_point(li, &sx, &sy, &mx, &my); goal_x = sx; goal_y = sy; cell_of(sx, sy, &goal_cx, &goal_cy); } }
    }
}

static void steer(mobj_t *mo, ticcmd_t *cmd, fixed_t tx, fixed_t ty, int run)
{
    angle_t want = R_PointToAngle2(mo->x, mo->y, tx, ty); int diff = (int)(want - mo->angle), turn = diff >> 16;
    if (turn > 5000) turn = 5000; if (turn < -5000) turn = -5000;
    cmd->angleturn = (short)turn;
    cmd->forwardmove = (abs(diff) < (ANG45 / 2)) ? run : 0;
}

void E13_BotCmd(ticcmd_t *cmd)
{
    player_t *p = &players[consoleplayer]; mobj_t *mo = p->mo; int held, pcx, pcy, start, rel;
    if (e13_on < 0) { const char *e = getenv("E13_BOT"), *t = getenv("E13_BOT_TICS"); e13_on = (e && *e) ? 1 : 0; if (t) e13_maxtics = atoi(t); if (getenv("E13_BOT_SEED")) e13_seed = atoi(getenv("E13_BOT_SEED")); if (e13_on) singletics = true; }
    if (!e13_on || !mo || gamestate != GS_LEVEL) return;
    if (e13_level != levelstarttic) e13_level_init();
    rel = gametic - e13_tic0;
    memset(cmd, 0, sizeof(*cmd));
    if (rel >= e13_maxtics || idle_tics > 400 || p->health <= 0) { fprintf(stderr, "BOT done: tics=%d keys_mask=%d doors_opened=%d health=%d idle=%d\n", rel, held_mask(p), doors_opened, p->health, idle_tics); G_CheckDemoStatus(); return; }
    held = held_mask(p);
    if (held != keys_got) { fprintf(stderr, "BOT tic %d: keys held now %d\n", rel, held); keys_got = held; goal_type = 0; }
    check_door_changes();
    if (!cell_of(mo->x, mo->y, &pcx, &pcy)) return;
    start = pcy * gw + pcx;
    if (abs((mo->x >> FRACBITS) - last_px) + abs((mo->y >> FRACBITS) - last_py) > 6) { last_px = mo->x >> FRACBITS; last_py = mo->y >> FRACBITS; stuck_since = gametic; }
    bfs(start, held);
    if (goal_type == 0 || goal_age > 900 || (goal_type == 2 && door_open(lines[goal_line].backsector) && use_tics > 2)) {
        if (goal_type == 2 && door_open(lines[goal_line].backsector)) {
            int i, seen = 0; for (i = 0; i < nopened; i++) if (opened_line[i] == goal_line) seen = 1;
            if (!seen && nopened < 1024) { opened_line[nopened++] = goal_line; doors_opened++; fprintf(stderr, "BOT tic %d: door line %d (special %d) opened\n", rel, goal_line, lines[goal_line].special); }
        }
        if (goal_age > 900 && goal_type == 2 && nbad_lines < 1024) bad_line[nbad_lines++] = goal_line;
        if (goal_age > 900 && goal_type == 1 && nbad_keys < 32) { bad_key_x[nbad_keys] = goal_x >> FRACBITS; bad_key_y[nbad_keys++] = goal_y >> FRACBITS; }
        choose_goal(mo, held);
        if (goal_type == 2 && getenv("E13_BOT_DEBUG")) { line_t *l = &lines[goal_line]; fixed_t sx, sy, mx, my; door_stand_point(goal_line, &sx, &sy, &mx, &my); fprintf(stderr, "BOTLINE %d special %d v1 %d,%d v2 %d,%d mid %d,%d stand %d,%d side-of-player %d backsector floor %d ceil %d front floor %d ceil %d\n", goal_line, l->special, l->v1->x >> FRACBITS, l->v1->y >> FRACBITS, l->v2->x >> FRACBITS, l->v2->y >> FRACBITS, mx >> FRACBITS, my >> FRACBITS, sx >> FRACBITS, sy >> FRACBITS, P_PointOnLineSide(mo->x, mo->y, l), l->backsector->floorheight >> FRACBITS, l->backsector->ceilingheight >> FRACBITS, l->frontsector->floorheight >> FRACBITS, l->frontsector->ceilingheight >> FRACBITS); }
        if (goal_type) { idle_tics = 0; fprintf(stderr, "BOT tic %d: goal %s at cell %d,%d (dist %d)\n", rel, goal_type == 1 ? "KEY" : "DOOR", goal_cx, goal_cy, dist[goal_cy * gw + goal_cx]); }
    }
    if (goal_type == 0) {
        idle_tics++;
        if (gametic >= wander_until || dist[start] < 0) { int tries = 40, c; do { c = e13_rand() % ncells; } while (tries-- && dist[c] < 0); if (dist[c] >= 0) { goal_cx = c % gw; goal_cy = c / gw; wander_until = gametic + 140; } }
        goal_x = cell_cx(goal_cx); goal_y = cell_cy(goal_cy);
    }
    goal_age++;
    if (getenv("E13_BOT_DEBUG") && rel % 20 == 0) fprintf(stderr, "BOTDBG tic %d pos %d,%d ang %d goal type %d at %d,%d dist-to-goal %ld cell-dist %d use_tics %d doorceil %d usedown %d\n", rel, mo->x >> FRACBITS, mo->y >> FRACBITS, (int)(mo->angle >> 24), goal_type, goal_x >> FRACBITS, goal_y >> FRACBITS, (long)(((goal_x - mo->x) >> FRACBITS) * ((goal_x - mo->x) >> FRACBITS) + ((goal_y - mo->y) >> FRACBITS) * ((goal_y - mo->y) >> FRACBITS)), dist[goal_cy * gw + goal_cx], use_tics, goal_type == 2 ? (lines[goal_line].backsector->ceilingheight >> FRACBITS) : -1, (int)p->usedown);
    /* path following: walk back from the goal cell to find the next cell on the route */
    {
        int c = goal_cy * gw + goal_cx, steps = 0, next = -1, look = 2;
        if (dist[c] < 0) { goal_type = 0; return; }
        while (c != start && prevc[c] >= 0 && steps < 100000) { if (dist[c] <= look) next = c; c = prevc[c]; steps++; }
        if (dist[goal_cy * gw + goal_cx] <= 1 || next < 0) {
            long ddx = (goal_x - mo->x) >> FRACBITS, ddy = (goal_y - mo->y) >> FRACBITS;
            if (goal_type == 2 && ddx * ddx + ddy * ddy < 24 * 24) {
                fixed_t sx, sy, mx, my; angle_t want; int diff;
                door_stand_point(goal_line, &sx, &sy, &mx, &my); want = R_PointToAngle2(mo->x, mo->y, mx, my); diff = (int)(want - mo->angle);
                cmd->angleturn = (short)((diff >> 16) > 5000 ? 5000 : ((diff >> 16) < -5000 ? -5000 : (diff >> 16)));
                if (abs(diff) < ANG45 / 8) { sector_t *ds = lines[goal_line].backsector; /* pressing use on a MOVING door reverses it, so press only when it is fully closed, then wait */ if (ds->ceilingheight <= ds->floorheight && use_tics % 12 == 0) cmd->buttons |= BT_USE; use_tics++; }
            } else steer(mo, cmd, goal_x, goal_y, 50);
            return;
        }
        steer(mo, cmd, cell_cx(next % gw), cell_cy(next / gw), 50);
    }
    if (goal_type == 2 && use_tics > 0 && use_tics <= 140) stuck_since = gametic;
    if (goal_type == 2 && use_tics > 140) { if (nbad_lines < 1024) bad_line[nbad_lines++] = goal_line; goal_type = 0; fprintf(stderr, "BOT tic %d: door line %d did not open, marked bad\n", rel, goal_line); return; }
    if (gametic - stuck_since > 100) { stuck_since = gametic; if (goal_type == 2 && nbad_lines < 1024) bad_line[nbad_lines++] = goal_line; if (goal_type == 1 && nbad_keys < 32) { bad_key_x[nbad_keys] = goal_x >> FRACBITS; bad_key_y[nbad_keys++] = goal_y >> FRACBITS; } goal_type = 0; wander_until = 0; fprintf(stderr, "BOT tic %d: stuck, dropping goal\n", rel); }
}
int E13_BotActive(void) { if (e13_on < 0) { const char *e = getenv("E13_BOT"); return e && *e; } return e13_on; }
