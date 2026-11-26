package e13;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;

/** DOOM-E13 per-tic digest for Mocha Doom (our own code). Same line format as the C engines:
 *  gametic leveltime prndindex rndindex x y z angle health armor readyweapon ammo0..3.  File: $E13_DIGEST. */
public final class Digest {
    private static BufferedWriter out;
    private static int pending = 0;

    private static long fnv(long h, int v) { for (int i = 0; i < 4; i++) { h ^= (v >>> (8 * i)) & 0xff; h *= 0x100000001b3L; } return h; }

    public static void tick(doom.DoomMain<?, ?> d, doom.thinker_t cap) {
        try {
            if (out == null) {
                String f = System.getenv("E13_DIGEST");
                out = new BufferedWriter(new FileWriter(f != null ? f : "e13_digest.txt"), 1 << 16);
                Runtime.getRuntime().addShutdownHook(new Thread(() -> { try { out.flush(); out.close(); } catch (IOException e) { } }));
            }
            doom.player_t pl = d.players[d.consoleplayer];
            if (pl == null || pl.mo == null) return;
            long msum = 0; int nm = 0;
            for (doom.thinker_t t = cap.next; t != cap; t = t.next) {
                if (t instanceof p.mobj_t && t != pl.mo && t.thinkerFunction != p.RemoveState.REMOVE) {
                    p.mobj_t m = (p.mobj_t) t; long h = 0xcbf29ce484222325L;
                    h = fnv(h, m.type.ordinal()); h = fnv(h, m.x); h = fnv(h, m.y); h = fnv(h, m.z); h = fnv(h, (int) m.angle);
                    h = fnv(h, m.momx); h = fnv(h, m.momy); h = fnv(h, m.momz); h = fnv(h, m.health);
                    msum += h; nm++;
                }
            }
            long sh = 0xcbf29ce484222325L;
            for (int i = 0; i < d.levelLoader.numsectors; i++) { rr.sector_t sc = d.levelLoader.sectors[i]; sh = fnv(sh, sc.floorheight); sh = fnv(sh, sc.ceilingheight); sh = fnv(sh, sc.special); }
            int cm = 0; for (int i = 0; i < 6; i++) if (pl.cards[i]) cm |= 1 << i;
            out.write(d.gametic + " " + d.leveltime + " " + d.random.getIndex() + " 0 " + pl.mo.x + " " + pl.mo.y + " " + pl.mo.z + " "
                    + (pl.mo.angle & 0xffffffffL) + " " + pl.health[0] + " " + pl.armorpoints[0] + " " + pl.readyweapon.ordinal() + " "
                    + pl.ammo[0] + " " + pl.ammo[1] + " " + pl.ammo[2] + " " + pl.ammo[3] + " " + nm + " " + Long.toUnsignedString(msum) + " " + Long.toUnsignedString(sh) + " " + cm + "\n");
            if (++pending >= 64) { out.flush(); pending = 0; }
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}
