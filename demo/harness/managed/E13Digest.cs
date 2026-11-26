// DOOM-E13 per-tic digest for Managed Doom (C#; our own code). Same 19-column line format as the other engines:
// gametic leveltime prndindex rndindex x y z angle health armor readyweapon ammo0..3 nmobjs mobjhash sectorhash cards. File: $E13_DIGEST.
using System;
using System.IO;
using System.Text;

namespace ManagedDoom
{
    public static class E13Digest
    {
        private static StreamWriter w;

        private static ulong Fnv(ulong h, int v)
        {
            uint u = (uint)v;
            for (int i = 0; i < 4; i++) { h ^= (u >> (8 * i)) & 0xff; h *= 0x100000001b3UL; }
            return h;
        }

        public static void Close() { w?.Flush(); w?.Dispose(); w = null; }

        public static void Tick(World world)
        {
            var p = world.ConsolePlayer;
            var mo = p.Mobj;
            if (mo == null) return;
            if (w == null && Environment.GetEnvironmentVariable("E13_NODIGEST") == null) { var f = Environment.GetEnvironmentVariable("E13_DIGEST") ?? "e13_digest.txt"; w = new StreamWriter(f, false, new UTF8Encoding(false), 1 << 16); }
            ulong msum = 0; int nm = 0;
            foreach (var t in world.Thinkers)
            {
                if (t is Mobj m && m != mo && t.ThinkerState != ThinkerState.Removed)
                {
                    ulong h = 0xcbf29ce484222325UL;
                    h = Fnv(h, (int)m.Type); h = Fnv(h, m.X.Data); h = Fnv(h, m.Y.Data); h = Fnv(h, m.Z.Data); h = Fnv(h, (int)m.Angle.Data);
                    h = Fnv(h, m.MomX.Data); h = Fnv(h, m.MomY.Data); h = Fnv(h, m.MomZ.Data); h = Fnv(h, m.Health);
                    msum += h; nm++;
                }
            }
            ulong sh = 0xcbf29ce484222325UL;
            foreach (var s in world.Map.Sectors) { sh = Fnv(sh, s.FloorHeight.Data); sh = Fnv(sh, s.CeilingHeight.Data); sh = Fnv(sh, (int)s.Special); }
            int cm = 0; for (int i = 0; i < 6; i++) if (p.Cards[i]) cm |= 1 << i;
            E13Mut.Tic = world.GameTic;
            ulong U(int x) { return unchecked((ulong)(long)x); }
            var val = new ulong[] { U(world.GameTic), U(world.LevelTime), U(world.Random.Index), 0, U(mo.X.Data), U(mo.Y.Data), U(mo.Z.Data), (ulong)(uint)mo.Angle.Data, U(p.Health), U(p.ArmorPoints), U((int)p.ReadyWeapon), U(p.Ammo[0]), U(p.Ammo[1]), U(p.Ammo[2]), U(p.Ammo[3]), U(nm), msum, sh, U(cm) };
            E13Mut.Check(val);
            if (w != null) w.WriteLine($"{world.GameTic} {world.LevelTime} {world.Random.Index} 0 {mo.X.Data} {mo.Y.Data} {mo.Z.Data} {mo.Angle.Data} {p.Health} {p.ArmorPoints} {(int)p.ReadyWeapon} {p.Ammo[0]} {p.Ammo[1]} {p.Ammo[2]} {p.Ammo[3]} {nm} {msum} {sh} {cm}");
        }
    }

    public static class E13Program
    {
        public static void Main(string[] a)
        {
            var args = new CommandLineArgs(a);
            var config = new Config();
            var content = new GameContent(args);
            var doom = new Doom(args, config, content, null, null, null, null);
            AppDomain.CurrentDomain.ProcessExit += (s, e) => E13Digest.Close();
            while (doom.Update() != UpdateResult.Completed) { }
            E13Digest.Close();
        }
    }
}
