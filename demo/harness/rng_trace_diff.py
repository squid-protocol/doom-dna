"""Find where two engines first differ in gameplay-RNG use. Both traces are "gametic caller prndindex" lines (see E13_TRACE_BUILD).
Usage: python rng_trace_diff.py <trace_a> <trace_b>   Prints the first gametic whose caller list differs and the largest per-caller surpluses."""
import collections, sys
def load(f):
    d = collections.defaultdict(list)
    for l in open(f):
        t, fn, idx = l.split(); d[int(t)].append(fn.lower().replace("_", ""))
    return d
a, b = load(sys.argv[1]), load(sys.argv[2])
for t in sorted(set(a) | set(b)):
    if a.get(t, []) != b.get(t, []):
        print("first differing gametic:", t); print(" A:", a.get(t, [])[:14]); print(" B:", b.get(t, [])[:14]); break
else:
    print("RNG call sequences identical for", len(a), "tics")
ca = collections.Counter(x for v in a.values() for x in v); cb = collections.Counter(x for v in b.values() for x in v)
d = sorted(((k, cb[k] - ca[k], ca[k], cb[k]) for k in set(ca) | set(cb) if ca[k] != cb[k]), key=lambda x: -abs(x[1]))[:6]
print("largest per-caller differences (caller, B-A, A, B):"); [print("  ", x) for x in d]
