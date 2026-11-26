// Mutant-screen runtime for Managed Doom (our code): lesion switch, per-function entry counters, in-engine early abort against a clean reference digest.
using System;
using System.IO;
using System.Linq;

public static class E13Mut
{
    public static readonly int Id = int.TryParse(Environment.GetEnvironmentVariable("E13_MUT"), out var v) ? v : -1;
    public static int Tic;
    static readonly uint[] counts = new uint[16384];
    static readonly int[] first = new int[16384];
    static readonly uint[] site = new uint[16384];
    static ulong[][] refRows;
    static int rows;
    static string verdict;
    static bool init;

    public static bool On(int id) { site[id]++; return Id == id; }
    public static int Enter(int fid) { counts[fid]++; if (first[fid] == 0) first[fid] = Tic + 1; return 0; }

    static void Init()
    {
        init = true; verdict = Environment.GetEnvironmentVariable("E13_VERDICT");
        var rf = Environment.GetEnvironmentVariable("E13_REF");
        if (rf != null && File.Exists(rf))
        {
            var list = new System.Collections.Generic.List<ulong[]>();
            foreach (var line in File.ReadLines(rf)) { var p = line.Split(' ', StringSplitOptions.RemoveEmptyEntries); if (p.Length != 19) continue; list.Add(p.Select(x => x.StartsWith("-") ? unchecked((ulong)long.Parse(x)) : ulong.Parse(x)).ToArray()); }
            refRows = list.ToArray();
        }
        AppDomain.CurrentDomain.ProcessExit += (s, e) => Finish();
    }

    static readonly int[] cols = { 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 };

    // called once per tic with the 19 digest values; exits at the first mismatch with the reference
    public static void Check(ulong[] val)
    {
        if (!init) Init();
        if (refRows != null && rows < refRows.Length)
        {
            var rr = refRows[rows];
            long mask = 0;
            foreach (var c in cols)
            {
                if (c == 7 && (long)unchecked((int)rr[8]) <= 0) continue;
                if (val[c] != rr[c]) mask |= 1L << c;
            }
            if (mask != 0) { if (verdict != null) File.WriteAllText(verdict, $"div {rows} {mask}\n"); Environment.Exit(0); }
        }
        rows++;
    }

    static void Finish()
    {
        var pf = Environment.GetEnvironmentVariable("E13_PROFILE");
        if (pf != null)
        {
            using (var o = new StreamWriter(pf))
            {
                for (int i = 0; i < counts.Length; i++) if (counts[i] != 0) o.WriteLine($"F {i} {counts[i]} {first[i] - 1}");
                for (int i = 0; i < site.Length; i++) if (site[i] != 0) o.WriteLine($"S {i} {site[i]}");
            }
        }
        if (verdict != null && !File.Exists(verdict)) File.WriteAllText(verdict, $"end {rows}\n");
    }
}
