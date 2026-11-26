package e13;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;

/** DOOM-E13 per-tic digest for Mocha Doom (our own code). Same line format as the C engines:
 *  gametic leveltime prndindex rndindex x y z angle health armor readyweapon ammo0..3.  File: $E13_DIGEST. */
public final class Digest {
    private static BufferedWriter out;
    private static int pending = 0;

    public static void tick(doom.DoomMain<?, ?> d) {
        try {
            if (out == null) {
                String f = System.getenv("E13_DIGEST");
                out = new BufferedWriter(new FileWriter(f != null ? f : "e13_digest.txt"), 1 << 16);
                Runtime.getRuntime().addShutdownHook(new Thread(() -> { try { out.flush(); out.close(); } catch (IOException e) { } }));
            }
            doom.player_t p = d.players[d.consoleplayer];
            if (p == null || p.mo == null) return;
            out.write(d.gametic + " " + d.leveltime + " " + d.random.getIndex() + " 0 " + p.mo.x + " " + p.mo.y + " " + p.mo.z + " "
                    + (p.mo.angle & 0xffffffffL) + " " + p.health[0] + " " + p.armorpoints[0] + " " + p.readyweapon.ordinal() + " "
                    + p.ammo[0] + " " + p.ammo[1] + " " + p.ammo[2] + " " + p.ammo[3] + "\n");
            if (++pending >= 64) { out.flush(); pending = 0; }
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}
