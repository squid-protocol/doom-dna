"""Compare per-tic digests of two engines on the same demo.
Compared fields: leveltime, prndindex (gameplay RNG), x, y, z, angle, health, armor, weapon, ammo0..3.
NOT compared: gametic (engines count it differently) and rndindex (cosmetic RNG: status-bar face, sound).
Usage: python compare_digests.py [--no-prnd] [--ignore-dead-angle] <runs_dir> <label_a> <label_b> demo1 [demo2 ...]
Prints per demo: identical|diverges at tic N (field), tics in each digest."""
import sys
from pathlib import Path
NAMES = ["gametic", "leveltime", "prndindex", "rndindex", "x", "y", "z", "angle", "health", "armor", "weapon", "ammo0", "ammo1", "ammo2", "ammo3", "nmobjs", "mobjhash", "sectorhash", "cards"]
KEEP = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
import os
if os.environ.get("E13_WIDE"): KEEP = KEEP + [15, 16, 17, 18]  # world fingerprint columns (monsters/objects and sectors), when both digests have them
def load(f):
    if not Path(f).exists(): return None
    rows = [l.split() for l in open(f) if len(l.split()) in (15, 18, 19)]  # a crashed engine can leave a partial last line
    # some engines emit one stray row before the level starts (leveltime does not increase between rows 0 and 1): drop it
    if len(rows) > 1 and int(rows[1][1]) <= int(rows[0][1]): rows = rows[1:]
    return rows
def first_divergence(a, b, keep=KEEP, ignore_dead_angle=False):
    n = min(len(a), len(b))
    for i in range(n):
        for k in keep:
            if k >= len(a[i]) or k >= len(b[i]): continue
            if a[i][k] != b[i][k]:
                if ignore_dead_angle and NAMES[k] == "angle" and int(a[i][8]) <= 0: continue  # post hoc rule: the death camera is cosmetic; committed as a flag
                return i, NAMES[k]
    return (n, "length") if len(a) != len(b) else None
if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    NOPRND = "--no-prnd" in sys.argv
    IDA = "--ignore-dead-angle" in sys.argv  # boom-family engines do not keep the compatibility RNG index in every mode
    keep = [k for k in KEEP if not (NOPRND and k == 2)]
    d, la, lb = Path(args[0]), args[1], args[2]
    for demo in args[3:]:
        a, b = load(d / f"{la}_{demo}.txt"), load(d / f"{lb}_{demo}.txt")
        if a is None or b is None: print(f"{la} vs {lb} {demo}: missing digest"); continue
        r = first_divergence(a, b, keep, IDA)
        print(f"{la} vs {lb} {demo}: " + ("identical (%d tics)" % len(a) if r is None else f"diverges at tic {r[0]} ({r[1]}); lengths {len(a)}/{len(b)}"))
