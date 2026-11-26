"""Generate random self-play demos (vanilla 1.9 .lmp format, version 109) for differential testing of DOOM engines.
Each demo: one player, chosen episode/map/skill, a seeded random policy of persistent actions (run/walk/strafe/turn/fire/use/weapon switch).
The inputs are ours, so no third-party demo content is involved. Usage: python gen_demos.py <out_dir> <count> [seed] [tics] [quiet_start_tics] [sticky|chaos]   (quiet start: buttons off for the first N tics; chaos: per-tic full-range random bytes)"""
import random, struct, sys
from pathlib import Path
out, n = Path(sys.argv[1]), int(sys.argv[2]); seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0; tics = int(sys.argv[4]) if len(sys.argv) > 4 else 4000
quiet = int(sys.argv[5]) if len(sys.argv) > 5 else 0
mode = sys.argv[6] if len(sys.argv) > 6 else "sticky"
variants = len(sys.argv) > 7 and sys.argv[7] == "variants"  # random game-mode flags in the header: skill 1-5 (5 = nightmare), respawning monsters, fast monsters, deathmatch rules (reaches code the default demos never run)  # sticky (default) or chaos: fresh random full-range bytes every tic, buttons 0..0x7F (no special/pause bit)
out.mkdir(parents=True, exist_ok=True)
rng = random.Random(seed)
def chaos(rng, tics):
    for t in range(tics):
        yield rng.randint(-127, 127), rng.randint(-128, 127), rng.randint(0, 255), rng.randint(0, 0x7F)  # forward -128 is the demo-end marker, so it is excluded

def policy(rng, tics):
    fwd = side = turn = btn = 0; left = 0; weapon = 0
    for t in range(tics):
        if left <= 0:
            left = rng.randint(8, 60)
            fwd = rng.choice([50, 50, 50, 25, 25, 0, -25, -50]); side = rng.choice([0, 0, 0, 40, -40, 24, -24])
            turn = rng.choice([0, 0, 2, -2, 5, -5, 7, -7, 10, -10]); fire = rng.random() < 0.5; use = rng.random() < 0.15
            weapon = rng.choice([0, 0, 0, 1, 2, 3, 4, 5, 6, 7])  # 0 = keep
            btn = (1 if fire else 0) | (2 if use else 0)
            if weapon: btn |= 4 | ((weapon - 1) << 3)
        yield fwd, side, turn, btn
        left -= 1
        if btn & 4: btn &= 0x03  # a weapon change lasts one tic; fire/use persist
for i in range(n):
    r = random.Random(rng.random())
    skill = r.choice([1, 2, 3, 4]); ep = 1; mp = r.randint(1, 9); dm = rp = fs = 0
    if variants: skill = r.choice([1, 2, 3, 4, 5, 5]); rp = int(r.random() < 0.4); fs = int(r.random() < 0.4); dm = r.choice([0, 0, 1, 2])
    hdr = bytes([109, skill, ep, mp, dm, rp, fs, 0, 0, 1, 0, 0, 0])
    body = b"".join(struct.pack("bbBB", f, s, t & 0xff, 0 if k < quiet else b) for k, (f, s, t, b) in enumerate((chaos if mode == "chaos" else policy)(r, tics)))
    (out / f"g{i:04d}.lmp").write_bytes(hdr + body + b"\x80")
print(f"wrote {n} demos to {out}")
