// Mutant-screen runtime for Mocha Doom (Java; our own code, same contract as E13Mut.cs / e13_screen.c):
//   E13_MUT=<id>      activates one lesion (a lesion site is `e13.E13Mut.On(id) ? mutated : original`)
//   E13_REF=<file>    clean per-tic digest of the same engine; the run exits at the first tic whose digest row differs (columns 1,2,4..18; the angle is skipped while the reference player is dead)
//   E13_VERDICT=<f>   "div <row> <bitmask of every mismatching column>" at the first mismatch, "end <rows>" at exit (also after an I_Error, like the C engines);
//                     nothing is written when the run dies from an uncaught exception, which the runner records as a crash
//   E13_PROFILE=<f>   at exit: "F <fid> <entries> <first tic>" per function, "S <id> <count>" per lesion site
//   E13_NODIGEST=1    do not write the per-tic digest file
package e13;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;

public final class E13Mut {
    public static final int Id;
    public static int Tic;
    private static final int N = 1 << 17;
    private static final long[] counts = new long[N];
    private static final int[] first = new int[N];
    private static final long[] site = new long[N];
    private static long[][] refRows;
    private static int rows;
    private static String verdict;
    private static volatile boolean crashed;
    private static final int[] COLS = { 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 };

    static {
        int v = -1;
        try { String s = System.getenv("E13_MUT"); if (s != null) v = Integer.parseInt(s.trim()); } catch (NumberFormatException e) { }
        Id = v;
        init();
        Runtime.getRuntime().addShutdownHook(new Thread(E13Mut::finish));
        Thread.setDefaultUncaughtExceptionHandler((t, e) -> { e.printStackTrace(); crash(); System.exit(1); });
    }

    public static boolean On(int id) { site[id]++; return Id == id; }

    public static int Enter(int fid) { counts[fid]++; if (first[fid] == 0) first[fid] = Tic + 1; return 0; }

    /** Called by the patched Mocha entry point when an exception ends the run (a lesion crash). */
    public static void crash() { crashed = true; }

    public static boolean nodigest() { return System.getenv("E13_NODIGEST") != null; }

    private static void init() {
        verdict = System.getenv("E13_VERDICT");
        String rf = System.getenv("E13_REF");
        if (rf != null && new File(rf).exists()) {
            ArrayList<long[]> list = new ArrayList<>();
            try (BufferedReader r = new BufferedReader(new FileReader(rf), 1 << 16)) {
                String line;
                while ((line = r.readLine()) != null) {
                    String[] p = line.trim().split("\\s+");
                    if (p.length != 19) continue;
                    long[] a = new long[19];
                    for (int i = 0; i < 19; i++) a[i] = p[i].startsWith("-") ? Long.parseLong(p[i]) : Long.parseUnsignedLong(p[i]);
                    list.add(a);
                }
            } catch (IOException e) { throw new RuntimeException(e); }
            refRows = list.toArray(new long[0][]);
        }
    }

    /** One call per tic with the 19 digest values (signed ints sign-extended, unsigned values as raw 64 bits); exits at the first mismatch with the reference. */
    public static void check(long[] val) {
        Tic = (int) val[0];
        if (refRows != null && rows < refRows.length) {
            long[] rr = refRows[rows];
            long mask = 0;
            for (int c : COLS) {
                if (c == 7 && (int) rr[8] <= 0) continue;
                if (val[c] != rr[c]) mask |= 1L << c;
            }
            if (mask != 0) {
                if (verdict != null) write(verdict, "div " + rows + " " + mask + "\n");
                Runtime.getRuntime().halt(0);
            }
        }
        rows++;
    }

    private static void write(String f, String s) {
        try (FileWriter w = new FileWriter(f)) { w.write(s); } catch (IOException e) { }
    }

    private static void finish() {
        String pf = System.getenv("E13_PROFILE");
        if (pf != null) {
            try (PrintWriter o = new PrintWriter(new FileWriter(pf))) {
                for (int i = 0; i < N; i++) if (counts[i] != 0) o.println("F " + i + " " + counts[i] + " " + (first[i] - 1));
                for (int i = 0; i < N; i++) if (site[i] != 0) o.println("S " + i + " " + site[i]);
            } catch (IOException e) { }
        }
        if (verdict != null && !crashed && !new File(verdict).exists()) write(verdict, "end " + rows + "\n");
    }
}
