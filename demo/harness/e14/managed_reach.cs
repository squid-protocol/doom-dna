// E14 reach probe: prints one line to stderr the first time a mutated function is entered (our code).
public static class E13Reach
{
    static bool seen;
    public static void Hit() { if (!seen) { seen = true; System.Console.Error.WriteLine("E13REACH"); } }
}
