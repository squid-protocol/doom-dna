package e13

import java.io.BufferedWriter
import java.io.FileWriter

/** DOOM-E13 per-tic digest for Kocoa Doom (Kotlin; our own code). Same 18-column line format as the other engines:
 *  gametic leveltime prndindex rndindex x y z angle health armor readyweapon ammo0..3 nmobjs mobjhash sectorhash. File: $E13_DIGEST. */
object Digest {
    private var out: BufferedWriter? = null
    private var pending = 0

    private fun fnv(h: Long, v: Int): Long {
        var hh = h
        for (i in 0 until 4) {
            hh = hh xor ((v ushr (8 * i)) and 0xff).toLong()
            hh *= 0x100000001b3L
        }
        return hh
    }

    @JvmStatic
    fun tick(d: doom.DoomMain<*, *>, cap: doom.thinker_t) {
        val pl = d.players[d.consoleplayer]
        val mo = pl.mo ?: return
        var w = out
        if (w == null) {
            val f = System.getenv("E13_DIGEST") ?: "e13_digest.txt"
            w = BufferedWriter(FileWriter(f), 1 shl 16)
            out = w
            Runtime.getRuntime().addShutdownHook(Thread { try { w.flush(); w.close() } catch (e: Exception) { } })
        }
        var msum = 0L
        var nm = 0
        var t = cap.next
        while (t != null && t !== cap) {
            if (t is p.mobj_t && t !== mo && t.thinkerFunction !== p.RemoveState.REMOVE) {
                var h = -0x340d631b7bdddcdbL  // 0xcbf29ce484222325 as a signed long
                h = fnv(h, t.type!!.ordinal); h = fnv(h, t._x); h = fnv(h, t._y); h = fnv(h, t._z); h = fnv(h, t.angle.toInt())
                h = fnv(h, t.momx); h = fnv(h, t.momy); h = fnv(h, t.momz); h = fnv(h, t.health)
                msum += h; nm++
            }
            t = t.next
        }
        var sh = -0x340d631b7bdddcdbL
        for (i in 0 until d.levelLoader.numsectors) {
            val sc = d.levelLoader.sectors[i]
            sh = fnv(sh, sc.floorheight); sh = fnv(sh, sc.ceilingheight); sh = fnv(sh, sc.special.toInt())
        }
        w.write("${d.gametic} ${d.leveltime} ${d.random.index} 0 ${mo._x} ${mo._y} ${mo._z} ${mo.angle and 0xffffffffL} ${pl.health[0]} ${pl.armorpoints[0]} ${pl.readyweapon.ordinal} " +
            "${pl.ammo[0]} ${pl.ammo[1]} ${pl.ammo[2]} ${pl.ammo[3]} $nm ${java.lang.Long.toUnsignedString(msum)} ${java.lang.Long.toUnsignedString(sh)}\n")
        if (++pending >= 64) { w.flush(); pending = 0 }
    }
}
