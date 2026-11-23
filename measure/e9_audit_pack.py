"""Build blinded hand-audit packets (rubric: preregistration/E9_AUDIT_RUBRIC.md). 50 T1-confirmed pairs (from the truth sample) and 50
predicted pairs that T1 did not confirm (drawn from the predictors' eligible-pair output, seed 20261122). Raters see only code text,
extensions and line counts. The key (packet id -> arm, programs, functions) stays outside the packets."""
import random
import sys
from pathlib import Path
import pandas as pd

T9 = Path("/srv/storage_16tb/projects/doom-e7-work/e9/results/truth")
P9 = Path("/srv/storage_16tb/projects/doom-e7-work/e9/results/pred")
REPOS = Path("/srv/storage_16tb/projects/doom-e7-work/repos")
OUT = Path("/srv/storage_16tb/projects/doom-e7-work/e9/audit")
SEED = 20261122
MAXLINES = 80
rng = random.Random(SEED)
OUT.mkdir(parents=True, exist_ok=True)

fn = pd.read_csv(T9 / "functions.csv", dtype=str, usecols=["program", "func_id", "path", "start_line", "end_line", "loc", "language_ext"])
fidx = {(p, i): (pa, int(s), int(e)) for p, i, pa, s, e in zip(fn.program, fn.func_id, fn.path, fn.start_line, fn.end_line)}
pairs = pd.read_csv(T9 / "pairs.csv", dtype=str)
pairs["jaccard"] = pairs.jaccard.astype(float)
conf = pairs[(pairs.eligible_primary == "1") & (pairs.jaccard >= 0.9)]
confkey = {tuple(sorted(((a, fa), (b, fb)))) for a, fa, b, fb in zip(conf.prog_a, conf.func_a, conf.prog_b, conf.func_b)}


def body(prog, fid):
    if (prog, fid) not in fidx:
        return None
    path, s, e = fidx[(prog, fid)]
    f = REPOS / prog / path
    if not f.exists():
        return None
    lines = f.read_text(errors="replace").splitlines()[s - 1:e]
    note = ""
    if len(lines) > MAXLINES:
        note = f"\n/* ... {len(lines) - MAXLINES} more lines omitted ... */"
        lines = lines[:MAXLINES]
    return "\n".join(lines) + note, len(lines), Path(path).suffix


# arm 1: T1-confirmed pairs
arm1 = [r for r in conf.itertuples()]
rng.shuffle(arm1)
a1 = []
for r in arm1:
    if body(r.prog_a, r.func_a) and body(r.prog_b, r.func_b):
        a1.append((r.prog_a, r.func_a, r.prog_b, r.func_b, "T1-confirmed", float(r.jaccard)))
    if len(a1) == 50:
        break
# arm 2: predicted pairs not T1-confirmed
pred = pd.read_csv(P9 / "predictions.csv", dtype=str, usecols=["predictor", "variant", "prog_a", "func_a", "prog_b", "func_b"])
pred = pred[((pred.predictor == "structure") & (pred.variant == "primary")) | ((pred.predictor == "names") & (pred.variant == "unique_key"))]
pred = pred[~pred.func_a.str.startswith("row:") & ~pred.func_b.str.startswith("row:")]
cand = [(r.prog_a, r.func_a, r.prog_b, r.func_b, r.predictor) for r in pred.itertuples()
        if tuple(sorted(((r.prog_a, r.func_a), (r.prog_b, r.func_b)))) not in confkey]
rng.shuffle(cand)
a2 = []
for pa, fa, pb, fb, pr in cand:
    if body(pa, fa) and body(pb, fb):
        a2.append((pa, fa, pb, fb, "predicted-unconfirmed:" + pr, float("nan")))
    if len(a2) == 50:
        break
allp = a1 + a2
rng.shuffle(allp)
key, packets = [], []
for i, (pa, fa, pb, fb, arm, j) in enumerate(allp):
    pid = f"P{i + 1:03d}"
    A, la, ea = body(pa, fa)
    B, lb, eb = body(pb, fb)
    if rng.random() < 0.5:  # blind the order
        A, la, ea, B, lb, eb, pa, fa, pb, fb = B, lb, eb, A, la, ea, pb, fb, pa, fa
    key.append(dict(packet=pid, arm=arm, prog_a=pa, func_a=fa, prog_b=pb, func_b=fb, jaccard=j))
    packets.append(f"## {pid}\n\n### Function A ({ea}, {la} lines)\n```c\n{A}\n```\n\n### Function B ({eb}, {lb} lines)\n```c\n{B}\n```\n")
pd.DataFrame(key).to_csv(OUT / "key_DO_NOT_SHARE.csv", index=False)
for b in range(0, len(packets), 25):
    (OUT / f"packets_{b // 25 + 1}.md").write_text("# Audit packets\n\nFor each packet answer with one label: COPY, INDEPENDENT or TRIVIAL (see the rubric).\n\n" + "\n".join(packets[b:b + 25]))
print(len(a1), "T1-confirmed;", len(a2), "predicted-unconfirmed;", len(packets), "packets in", OUT)
