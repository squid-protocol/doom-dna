"""DOOM-E8c step 4: fork-date estimates by arm (A E8 as registered, B semi-annual + pooled K=25, C dense + pooled K=25, D dense + single shuffle),
E8's own hinge_fit and placebos (imported unchanged), a point bootstrap, and the registered predictions scored. Writes results/e8c/."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/measure")
import e8_analyze as A
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
E8R = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life")
OUT = REPO / "results" / "e8c"; OUT.mkdir(parents=True, exist_ok=True)
NPLAC, NBOOT = 300, 300
pairs = pd.read_csv("/srv/storage_16tb/projects/doom-e8c-work/results/pairs_dense.csv")
truth = pd.read_csv(E8R / "manifest" / "e8_fork_truth.csv")
cols = {"B": ("semi", ""), "C": ("dense", ""), "D": ("dense", "_single")}
res = {}
a = pd.read_csv(E8R / "results" / "e8" / "analysis" / "h83b_pairs.csv"); res["A"] = a[a.same_language == "yes"].copy()
for arm, (grid, suf) in cols.items():
    d = pairs[pairs.grid == grid].copy()
    d["shared_struct_max"] = d["shared_struct_max" + suf]; d["shared_struct_min"] = d["shared_struct_min" + suf]
    t, _ = A.h83b(d, truth, NPLAC, 20261123)
    res[arm] = t[t.same_language == "yes"].copy()
    # point bootstrap interval on the estimate
    lo, hi = [], []
    for r in res[arm].itertuples():
        g = d[(d.child == r.child) & (d.parent == r.parent) & (d.identical_sha == 0)].dropna(subset=[A.PAIR_METHODS[r.method]])
        tt = np.array([A.to_year(x) for x in g.target_date]); ss = g[A.PAIR_METHODS[r.method]].values.astype(float)
        rng = np.random.default_rng(1); est = []
        for _ in range(NBOOT):
            i = rng.integers(0, len(tt), len(tt)); est.append(A.hinge_fit(tt[i], ss[i])[0])
        est = np.array(est, float); est = est[np.isfinite(est)]
        lo.append(np.percentile(est, 2.5) - r.truth if len(est) else np.nan); hi.append(np.percentile(est, 97.5) - r.truth if len(est) else np.nan)
    res[arm]["boot_lo_err"] = lo; res[arm]["boot_hi_err"] = hi
for k, v in res.items():
    v.insert(0, "arm", k)
allr = pd.concat(res.values(), ignore_index=True); allr.to_csv(OUT / "fork_estimates_by_arm.csv", index=False)
L = ["# DOOM-E8c results: fork dates from a denser grid and the pooled cutoff (exploratory)", "",
     "Arms: A = E8 as registered; B = E8's semi-annual points, pooled K = 25 rule; C = dense grid, pooled K = 25; D = dense grid, single shuffle per pair (E8's rule). Estimate error in years = estimate - git truth (negative = estimate too early). `n` = points used by the fit. `boot` = 95% point-bootstrap interval of the error.", ""]
for pair in sorted(set(zip(allr.child, allr.parent))):
    L.append(f"## {pair[0]} from {pair[1]}  (git truth {allr[(allr.child == pair[0])].truth.iloc[0]:.2f})")
    L += ["", "| method | " + " | ".join(f"arm {k} error (n) [boot]" for k in "ABCD") + " |", "|---|" + "---|" * 4]
    for m in ("struct_max", "struct_min", "names_max", "names_min"):
        cells = []
        for k in "ABCD":
            r = allr[(allr.arm == k) & (allr.child == pair[0]) & (allr.method == m)]
            if len(r) == 0 or not np.isfinite(r.error_years.iloc[0]): cells.append("n/a"); continue
            r = r.iloc[0]; b = f" [{r.boot_lo_err:.2f}, {r.boot_hi_err:.2f}]" if "boot_lo_err" in r and np.isfinite(r.get("boot_lo_err", np.nan)) else ""
            cells.append(f"{r.error_years:+.2f} ({int(r.n_points)}){b}")
        L.append(f"| {m} | " + " | ".join(cells) + " |")
    L.append("")
def g(arm, child, m):
    r = allr[(allr.arm == arm) & (allr.child == child) & (allr.method == m)]
    return r.iloc[0] if len(r) else None
def err(arm, child, m):
    r = g(arm, child, m); return float(r.error_years) if r is not None and np.isfinite(r.error_years) else float("nan")
def width(arm, child, m):
    r = g(arm, child, m); return float(r.boot_hi_err - r.boot_lo_err) if r is not None and arm != "A" and np.isfinite(r.boot_hi_err) else float("nan")
P = []
P.append(("P1 arm C structure(max) within 0.5 y for dsda-doom and nugget-doom", all(abs(err("C", c, "struct_max")) <= 0.5 for c in ("dsda-doom", "nugget-doom")), {c: round(err("C", c, "struct_max"), 2) for c in ("dsda-doom", "nugget-doom")}))
P.append(("P2 crispy-doom error more than 5 y early in every arm (struct_max)", all(err(k, "crispy-doom", "struct_max") < -5 for k in "ABCD"), {k: round(err(k, "crispy-doom", "struct_max"), 2) for k in "ABCD"}))
P.append(("P3 bootstrap interval narrower in C than B for dsda-doom and nugget-doom (struct_max)", all(width("C", c, "struct_max") < width("B", c, "struct_max") for c in ("dsda-doom", "nugget-doom")), {c: (round(width("B", c, "struct_max"), 2), round(width("C", c, "struct_max"), 2)) for c in ("dsda-doom", "nugget-doom")}))
P.append(("P4 names at least as accurate as structure for nugget-doom in arm C (names_max vs struct_max)", abs(err("C", "nugget-doom", "names_max")) <= abs(err("C", "nugget-doom", "struct_max")), {"names": round(err("C", "nugget-doom", "names_max"), 2), "struct": round(err("C", "nugget-doom", "struct_max"), 2)}))
okp = all((r.placebo_permute_median_abs_err > abs(r.error_years)) and (r.placebo_shift_median_abs_err > abs(r.error_years)) for r in allr.itertuples() if np.isfinite(r.error_years) and np.isfinite(getattr(r, "placebo_permute_median_abs_err", np.nan)))
P.append(("P5 observed |error| below both placebo median errors for every fitted row", okp, ""))
dD = {c: round(abs(err("D", c, "struct_max") - err("C", c, "struct_max")), 2) for c in ("dsda-doom", "nugget-doom")}
dB = {c: round(abs(err("B", c, "struct_max") - err("A", c, "struct_max")), 2) for c in ("dsda-doom", "nugget-doom")}
P.append(("P6 |D-C| < 0.25 y and |B-A| < 0.25 y for dsda-doom and nugget-doom (struct_max)", all(v < 0.25 for v in list(dD.values()) + list(dB.values())), {"|D-C|": dD, "|B-A|": dB}))
L += ["## Predictions", "", "| prediction | result | values |", "|---|---|---|"] + [f"| {a} | {'met' if ok else 'NOT met'} | {v} |" for a, ok, v in P]
(OUT / "E8C_RESULTS.md").write_text("\n".join(L) + "\n"); print("\n".join(L))
