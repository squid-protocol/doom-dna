#!/usr/bin/env python
"""DOOM-E8 analysis (Amendment 1 sections B, C, D). Reads the outputs of e8_measure.py, writes
<results>/analysis/phase_report.md and CSV tables.

    python e8_analyze.py --results R --plan-dir manifest

Everything is deterministic given --seed. Resampling is ALWAYS over reference functions (the found-arrays),
never over time points. Estimators that the Amendment left open are marked "FIXED:" in comments and are
repeated in the report's "Estimator choices" block.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import least_squares

# ----------------------------------------------------------------------------- constants (Amendment 1 B)
LINEAGES = ["chocolate-doom", "woof", "prboom-plus", "doomretro", "eternity", "odamex", "gzdoom", "srb2",
            "fastdoom", "edge-classic", "inter-doom"]
CHILDREN = ["crispy-doom", "nugget-doom", "dsda-doom"]
HISTORY = ["chocolate-doom", "woof", "prboom-plus", "eternity", "odamex", "gzdoom"]
IMPORT = ["doomretro", "srb2", "fastdoom", "edge-classic", "inter-doom"]
BOOM = ["gzdoom", "edge-classic", "odamex", "eternity"]
CONTROL_ROLES = ["control-rewrite", "control-assets", "control-unrelated", "descriptive-cross-language"]
FLOOR = 0.02
MIN_SNAPSHOTS = 4
MIN_LINEAGES = 8
EQUIV = 0.10
ALPHA = 0.05

METHODS = {  # name -> (csv column, found-array key)
    "struct": ("surv_struct_pooled_either", "found_struct_pooled"),
    "struct_persnap": ("surv_struct_persnap_either", "found_struct_persnap"),
    "names": ("surv_names", "found_names"),
}
PAIR_METHODS = {"struct_max": "shared_struct_max", "struct_min": "shared_struct_min",
                "names_max": "shared_names_max", "names_min": "shared_names_min"}


def seed_of(*parts) -> int:
    return zlib.crc32("|".join(str(p) for p in parts).encode()) & 0x7FFFFFFF


def tag(sha: str, scope_key: str) -> str:
    """Same as measure/e8_snap.py tag()."""
    return f"{sha[:12]}__{hashlib.sha1(scope_key.encode()).hexdigest()[:6]}"


def found_path(results: Path, sha: str, scope_key: str, ref: str = "R1") -> Path:
    return Path(results) / "found" / f"{tag(sha, scope_key)}__{ref}.npz"


# ----------------------------------------------------------------------------- small statistics
def holm(p) -> np.ndarray:
    """Holm step-down adjusted p-values (NaN treated as 1)."""
    p = np.where(np.isnan(np.asarray(p, float)), 1.0, np.asarray(p, float))
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def kendall(a, s):
    """Kendall tau-b, two-sided. FIXED: a constant series (tau undefined) gives tau=0, p=1."""
    a, s = np.asarray(a, float), np.asarray(s, float)
    if len(a) < 3 or np.ptp(a) == 0 or np.ptp(s) == 0:
        return 0.0, 1.0
    r = stats.kendalltau(a, s, variant="b", method="auto")
    return float(r.statistic), float(r.pvalue)


def partial_spearman(a, s, z):
    """FIXED: partial Spearman = Pearson correlation of the rank-residuals of age and survival after
    regressing each (linearly) on the rank of the control z; p from a t distribution with n-3 df."""
    a, s, z = (stats.rankdata(np.asarray(v, float)) for v in (a, s, z))
    n = len(a)
    if n < 4 or np.ptp(a) == 0 or np.ptp(s) == 0:
        return 0.0, 1.0

    def resid(y):
        if np.ptp(z) == 0:
            return y - y.mean()
        X = np.column_stack([np.ones(n), z])
        return y - X @ np.linalg.lstsq(X, y, rcond=None)[0]

    ra, rs = resid(a), resid(s)
    if np.ptp(ra) < 1e-12 or np.ptp(rs) < 1e-12:
        return 0.0, 1.0
    r = float(np.clip(np.corrcoef(ra, rs)[0, 1], -1, 1))
    if abs(r) >= 1:
        return r, 0.0
    t = r * math.sqrt((n - 3) / (1 - r * r))
    return r, float(2 * stats.t.sf(abs(t), n - 3))


def wilcoxon(x, y=None, alternative="less"):
    try:
        x = np.asarray(x, float)
        if y is not None:
            r = stats.wilcoxon(x, np.asarray(y, float), alternative=alternative)
        else:
            r = stats.wilcoxon(x, alternative=alternative)
        return float(r.pvalue)
    except ValueError:
        return float("nan")


def sign_test_threshold(n: int, alpha: float) -> int | None:
    """Smallest k (of n) so that the one-sided exact sign test P(X >= k | p=.5) < alpha."""
    for k in range(n + 1):
        if stats.binom.sf(k - 1, n, 0.5) < alpha:
            return k
    return None


def perm_spearman(x, y, n_perm, seed):
    """Spearman rho(x, y) and a one-sided permutation p (shuffle y across units): P(rho_perm >= rho_obs)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return float("nan"), float("nan")
    rho = float(stats.spearmanr(x, y).statistic)
    rng = np.random.default_rng(seed)
    rx = stats.rankdata(x)
    ry = stats.rankdata(y)
    cnt = 0
    for _ in range(n_perm):
        pr = rng.permutation(ry)
        r = np.corrcoef(rx, pr)[0, 1]
        cnt += r >= rho - 1e-12
    return rho, (cnt + 1) / (n_perm + 1)


# ----------------------------------------------------------------------------- loading
def read_csv(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if Path(path).exists() else None


def load_inputs(results: Path, plan_dir: Path) -> dict:
    results, plan_dir = Path(results), Path(plan_dir)
    d = {"snap": pd.read_csv(results / "snapshots.csv")}
    for k, f in [("pairs", "pairs_grid.csv"), ("noise", "noise.csv"), ("self", "self_origin.csv"), ("precond", "precondition_summary.csv")]:
        d[k] = read_csv(results / f)
    d["truth"] = read_csv(plan_dir / "e8_fork_truth.csv")
    plans = {}
    scope = {}
    for kind, f in [("calendar", "e8_plan.csv"), ("commitcount", "e8_plan_commitcount.csv")]:
        p = read_csv(plan_dir / f)
        if p is not None:
            plans[kind] = set(zip(p.port, p.sha))
            for r in p.itertuples():
                scope[(r.port, r.sha)] = "" if pd.isna(r.scope_key) else str(r.scope_key)
    d["plans"], d["scope"] = plans, scope
    snap = d["snap"]
    snap["scope_key"] = [d["scope"].get((p, s), "") for p, s in zip(snap.port, snap.sha)]
    return d


class Ctx:
    """Holds results path, bootstrap settings and a cache of function-level bootstrap draws."""

    def __init__(self, results, B=2000, seed=20261122):
        self.results, self.B, self.seed = Path(results), int(B), int(seed)
        self.cache = {}

    def snap_boot(self, row, fkey):
        """B bootstrap draws of one snapshot's survival (resampling the reference functions); None if no file."""
        key = (row["sha"], row["scope_key"], fkey)
        if key in self.cache:
            return self.cache[key]
        out = None
        fp = found_path(self.results, row["sha"], row["scope_key"])
        if fp.exists():
            try:
                with np.load(fp) as z:
                    arr = np.asarray(z[fkey], dtype=float)
                if len(arr):
                    rng = np.random.default_rng(seed_of(self.seed, tag(row["sha"], row["scope_key"]), fkey))
                    idx = rng.integers(0, len(arr), size=(self.B, len(arr)))
                    out = arr[idx].mean(axis=1)
            except (KeyError, ValueError, OSError):
                out = None
        self.cache[key] = out
        return out


# ----------------------------------------------------------------------------- sample construction
def prepare_sample(snap, plans, kind="calendar", ref="R1", ports=None):
    """Rows of one plan kind and reference, restricted to ports, de-duplicated by SHA within port (C.4)."""
    df = snap[snap.ref == ref].copy()
    if "scope_key" not in df:
        df["scope_key"] = ""
    inplan = np.array([(p, s) in plans.get(kind, set()) for p, s in zip(df.port, df.sha)], bool)
    df = df[(df.plan_kind == kind) | inplan]
    if ports is not None:
        df = df[df.port.isin(ports)]
    df = df.sort_values(["port", "age_years", "fraction"]).drop_duplicates(["port", "sha"], keep="first")
    return df.reset_index(drop=True)


def per_lineage(df, mcol, fkey, ctx, tau_kind="kendall"):
    """Per-lineage tau, delta (earliest usable - head) and function-level bootstrap of delta."""
    rows, boots = [], {}
    for port, g in df.groupby("port", sort=True):
        u = g[g.underpowered != 1].sort_values("age_years")
        n = len(u)
        rec = dict(port=port, stratum=g.stratum.iloc[0], n_distinct=len(g), n_underpowered=int((g.underpowered == 1).sum()),
                   n_usable=n, scored=n >= MIN_SNAPSHOTS)
        if rec["scored"]:
            a, s = u.age_years.values, u[mcol].values
            if tau_kind == "partial":
                tau, p = partial_spearman(a, s, np.log(u.eligible_snapshot.values.astype(float)))
            else:
                tau, p = kendall(a, s)
            e, h = u.iloc[0], u.iloc[-1]
            rec.update(tau=tau, p=p, delta=float(e[mcol] - h[mcol]), s_earliest=float(e[mcol]), s_head=float(h[mcol]),
                       age_earliest=float(e.age_years), age_head=float(h.age_years))
            be, bh = ctx.snap_boot(e, fkey), ctx.snap_boot(h, fkey)
            if be is not None and bh is not None:
                db = be - bh
                boots[port] = db
                rec["delta_lo"], rec["delta_hi"] = (float(x) for x in np.percentile(db, [2.5, 97.5]))
        rows.append(rec)
    cols = ["port", "stratum", "n_distinct", "n_underpowered", "n_usable", "scored", "tau", "p", "delta", "s_earliest",
            "s_head", "age_earliest", "age_head", "delta_lo", "delta_hi"]
    out = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
    return out, boots


def endpoints(ds, dn, bn, ports=None):
    """P1, P2, P3 (Holm over exactly three) and the separately reported effect-size criteria."""
    a = ds[ds.scored.astype(bool)].set_index("port")
    b = dn[dn.scored.astype(bool)].set_index("port")
    common = [p for p in a.index if p in b.index and (ports is None or p in ports)]
    n = len(common)
    res = dict(n_lineages=n, lineages=",".join(common))
    nan = float("nan")
    if n < 2:
        res.update(p1=nan, p2=nan, p3=nan, p1_holm=nan, p2_holm=nan, p3_holm=nan, P1=False, P2=False, P3=False,
                   med_tau_struct=nan, med_tau_names=nan, med_delta_struct=nan, med_delta_names=nan,
                   names_ci_lo=nan, names_ci_hi=nan, tau_crit=False, delta_crit=False, n_tau_neg=0, delta_share=nan,
                   sign_p=nan, n_boot=0)
        return res
    ts, tn = a.loc[common, "tau"].values, b.loc[common, "tau"].values
    p1 = wilcoxon(ts, None, "less")          # H0 median tau >= 0
    p2 = wilcoxon(ts, tn, "less")            # H1 tau_struct < tau_names
    arrs = [bn[p] for p in common if p in bn]
    lo = hi = nan
    p3 = nan
    if arrs:
        med = np.median(np.vstack(arrs), axis=0)
        lo, hi = (float(x) for x in np.percentile(med, [2.5, 97.5]))
        B = len(med)
        # FIXED: bootstrap TOST-style p for the Holm family = max of the two one-sided tail fractions
        p3 = max(((med <= -EQUIV).sum() + 1) / (B + 1), ((med >= EQUIV).sum() + 1) / (B + 1))
    ph = holm([p1, p2, p3])
    ci_in = bool(arrs) and lo > -EQUIV and hi < EQUIV
    dsv = a.loc[common, "delta"].values
    neg = int((ts < 0).sum())
    res.update(p1=p1, p2=p2, p3=p3, p1_holm=ph[0], p2_holm=ph[1], p3_holm=ph[2],
               P1=bool(ph[0] < ALPHA), P2=bool(ph[1] < ALPHA),
               # FIXED: P3 passes iff the registered 95% interval criterion holds AND its Holm-adjusted p < alpha
               P3=bool(ci_in and ph[2] < ALPHA),
               names_ci_lo=lo, names_ci_hi=hi, names_ci_inside=ci_in, n_boot=len(arrs),
               med_tau_struct=float(np.median(ts)), med_tau_names=float(np.median(tn)),
               med_delta_struct=float(np.median(dsv)), med_delta_names=float(np.median(b.loc[common, "delta"].values)),
               tau_crit=bool(np.median(ts) <= -0.6), n_tau_neg=neg,
               delta_share=float(np.mean(dsv >= 0.10)), delta_crit=bool(np.mean(dsv >= 0.10) >= 0.70),
               sign_p=float(stats.binom.sf(neg - 1, n, 0.5)))
    return res


def conclusion(ep):
    return (bool(ep["P1"]), bool(ep["P2"]), bool(ep["P3"]), bool(ep["tau_crit"]), bool(ep["delta_crit"]))


CONC_NAMES = ["P1", "P2", "P3", "median_tau_struct<=-0.6", "delta_struct>=0.10 in >=70%"]


def analyse(df, ctx, struct="struct", tau_kind="kendall", ports=None):
    scol, skey = METHODS[struct]
    ncol, nkey = METHODS["names"]
    ds, _ = per_lineage(df, scol, skey, ctx, tau_kind)
    dn, bn = per_lineage(df, ncol, nkey, ctx, tau_kind)
    ep = endpoints(ds, dn, bn, ports)
    return ds, dn, ep


# ----------------------------------------------------------------------------- sensitivities
def _set(x):
    if pd.isna(x):
        return frozenset()
    return frozenset(t for t in str(x).replace(";", " ").replace(",", " ").replace("|", " ").split() if t)


def head_row(g):
    return g.sort_values("age_years").iloc[-1]


def filt_dedup(df, snap_all=None):
    return df[df.dup_share <= 0.25]


def filt_pure_c(df, full=None):
    keep = []
    for port, g in df.groupby("port"):
        h = head_row(g)
        ok = ((g.lang_c >= 0.9) & ((g.lang_c - h.lang_c).abs() < 0.10) & ((g.lang_cpp - h.lang_cpp).abs() < 0.10)
              & ((g.lang_other - h.lang_other).abs() < 0.10))
        keep.append(g[ok])
    return pd.concat(keep) if keep else df.iloc[0:0]


def filt_pruned(df, full=None):
    keep = []
    for port, g in df.groupby("port"):
        hs = _set(head_row(g).pruned)
        keep.append(g[[(_set(x) == hs) for x in g.pruned]])
    return pd.concat(keep) if keep else df.iloc[0:0]


# ----------------------------------------------------------------------------- functional form
def fit_exp(a, s, model):
    """Constrained NLS. FIXED: model 1 S0*exp(-lam a), 0<S0<=1 (lower bound 1e-6), lam in [0,50];
    model 2 Sinf+(S0-Sinf)exp(-lam a), Sinf in [0,1], S0 in [1e-6,1], lam in [0,50]; multi-start, best SSE."""
    a, s = np.asarray(a, float), np.asarray(s, float)
    best = None
    if model == 1:
        starts = [(S0, lam) for S0 in (1.0, max(min(s.max(), 1.0), 1e-3)) for lam in (0.01, 0.1, 0.5, 2.0)]
        lo, hi = [1e-6, 0.0], [1.0, 50.0]
        f = lambda x: x[0] * np.exp(-x[1] * a) - s
    else:
        starts = [(S0, lam, si) for S0 in (1.0, max(min(s.max(), 1.0), 1e-3)) for lam in (0.05, 0.3, 1.5)
                  for si in (0.0, float(np.clip(s.min(), 0, 1)))]
        lo, hi = [1e-6, 0.0, 0.0], [1.0, 50.0, 1.0]
        f = lambda x: x[2] + (x[0] - x[2]) * np.exp(-x[1] * a) - s
    for x0 in starts:
        x0 = np.clip(x0, np.array(lo) + 1e-9, np.array(hi) - 1e-9)
        try:
            r = least_squares(f, x0, bounds=(lo, hi))
        except ValueError:
            continue
        if best is None or r.cost < best.cost:
            best = r
    if best is None:
        return dict(S0=np.nan, lam=np.nan, Sinf=np.nan, sse=np.nan)
    x = best.x
    return dict(S0=float(x[0]), lam=float(x[1]), Sinf=float(x[2]) if model == 2 else 0.0, sse=float(2 * best.cost))


def burst(a, s):
    """Rate-normalised burst: max_k (loss rate on interval k) / (total loss / total time). FIXED: loss = -(dS)."""
    a, s = np.asarray(a, float), np.asarray(s, float)
    o = np.argsort(a)
    a, s = a[o], s[o]
    if len(a) < 3:
        return float("nan")
    rng_s, rng_t = s[0] - s[-1], a[-1] - a[0]
    if rng_s <= 1e-9 or rng_t <= 0:
        return float("nan")
    rates = -np.diff(s) / np.diff(a)
    return float(np.max(rates) / (rng_s / rng_t))


def burst_yearly(a, s):
    """FIXED: linear interpolation onto an even 1-year grid starting at the earliest age (grid points <= head age)."""
    a, s = np.asarray(a, float), np.asarray(s, float)
    o = np.argsort(a)
    a, s = a[o], s[o]
    if len(a) < 3:
        return float("nan")
    grid = np.arange(a[0], a[-1] + 1e-9, 1.0)
    if len(grid) < 3:
        return float("nan")
    return burst(grid, np.interp(grid, a, s))


def functional_form(df, ctx, fit_draws):
    rows = []
    for method in ("struct", "names"):
        col, key = METHODS[method]
        for port, g in df.groupby("port", sort=True):
            u = g[g.underpowered != 1].sort_values("age_years")
            if len(u) < MIN_SNAPSHOTS:
                continue
            a, s = u.age_years.values, u[col].values
            f1, f2 = fit_exp(a, s, 1), fit_exp(a, s, 2)
            rec = dict(port=port, method=method, n=len(u), S0_m1=f1["S0"], lambda_m1=f1["lam"], sse_m1=f1["sse"],
                       halflife_m1=(math.log(2) / f1["lam"]) if f1["lam"] > 1e-9 else float("inf"),
                       S0_m2=f2["S0"], Sinf_m2=f2["Sinf"], lambda_m2=f2["lam"], sse_m2=f2["sse"],
                       burst_halflife_grid=burst(a, s), burst_yearly=burst_yearly(a, s))
            boots = [ctx.snap_boot(r, key) for _, r in u.iterrows()]
            if all(b is not None for b in boots) and fit_draws > 0:
                M = np.column_stack(boots)[:fit_draws]
                l1 = np.array([fit_exp(a, row, 1)["lam"] for row in M])
                l2 = np.array([fit_exp(a, row, 2)["lam"] for row in M]) if len(u) >= 4 else np.array([np.nan])
                rec.update(lambda_m1_lo=np.percentile(l1, 2.5), lambda_m1_hi=np.percentile(l1, 97.5),
                           lambda_m2_lo=np.nanpercentile(l2, 2.5), lambda_m2_hi=np.nanpercentile(l2, 97.5),
                           n_boot_fits=len(M))
            rows.append(rec)
    return pd.DataFrame(rows)


def heterogeneity(ff):
    rows = []
    for method, g in ff.groupby("method"):
        lam = g.lambda_m1.values
        pos = lam[lam > 1e-9]
        rows.append(dict(method=method, n=len(lam), median_lambda=np.median(lam), q25=np.percentile(lam, 25),
                         q75=np.percentile(lam, 75), min=lam.min(), max=lam.max(),
                         cv=(lam.std(ddof=1) / lam.mean()) if len(lam) > 1 and lam.mean() > 0 else np.nan,
                         max_over_min_positive=(pos.max() / pos.min()) if len(pos) > 1 else np.nan))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- H8.3(a)
def fit_lambda_s0_one(a, s):
    """lambda of S = exp(-lambda * (a - a0)) (S0 = 1 by construction); FIXED: bounded multi-start least squares."""
    t = np.asarray(a, float) - a[0]
    s = np.asarray(s, float)
    best, bl = np.inf, 0.0
    for x0 in (0.01, 0.1, 0.5, 2.0):
        r = least_squares(lambda x: np.exp(-x[0] * t) - s, [x0], bounds=([0.0], [50.0]))
        if r.cost < best:
            best, bl = r.cost, float(r.x[0])
    return bl


SELF_COLS = {"struct": "surv_struct_self_persnap_either", "names": "surv_names_self"}


def h83a(df, mcol, self_df, self_col, n_perm, seed):
    """Exploratory age-from-head with the registered estimand: self-origin survival surv(s0 -> head) read from
    self_origin.csv (row of the port whose sha equals the head snapshot's sha; S = 1 at s0 by construction).
    Time zero is s0, so the estimated and true 'age' are the span age(head) - age(s0). The self-origin curve of
    a lineage is s0 (S=1) plus the self_origin rows for its later usable snapshots."""
    lines = {}
    for port, g in df.groupby("port", sort=True):
        u = g[g.underpowered != 1].sort_values("age_years")
        if len(u) < MIN_SNAPSHOTS:
            continue
        sha0, shah = u.sha.iloc[0], u.sha.iloc[-1]
        sr = self_df[(self_df.port == port) & (self_df.sha0 == sha0)] if self_df is not None and len(self_df) else pd.DataFrame()
        sm = dict(zip(sr.sha, sr[self_col])) if len(sr) else {}
        sm[sha0] = 1.0
        keep = [i for i, x in enumerate(u.sha) if x in sm and pd.notna(sm[x])]
        a = u.age_years.values[keep]
        sv = np.array([sm[u.sha.iloc[i]] for i in keep], float)
        has_head = shah in sm and pd.notna(sm[shah])
        lines[port] = dict(a=a, s=sv, S_head=float(u[mcol].iloc[-1]), S_self=float(sm[shah]) if has_head else np.nan,
                           span=float(u.age_years.iloc[-1] - u.age_years.iloc[0]), age_head=float(u.age_years.iloc[-1]),
                           age_s0=float(u.age_years.iloc[0]))
    ports = list(lines)
    lam = {p: fit_lambda_s0_one(lines[p]["a"], lines[p]["s"]) if len(lines[p]["a"]) >= 2 else np.nan for p in ports}
    rows = []
    for p in ports:
        L = lines[p]
        others = [q for q in ports if q != p]
        lam_med = float(np.nanmedian([lam[q] for q in others])) if others else np.nan
        rec = dict(port=p, true_age=L["span"], S_head=L["S_head"], S_self=L["S_self"],
                   lambda_loo_median=lam_med, loo_median_age=float(np.median([lines[q]["span"] for q in others])) if others else np.nan)
        if np.isnan(L["S_self"]):
            rec.update(status="unestimable (no self-origin row for head)", a_hat=np.nan)
        elif L["S_self"] <= FLOOR:
            rec.update(status="censored (unestimable: at or below floor)", a_hat=np.nan)
        elif L["S_self"] >= 1:
            rec.update(status="estimated", a_hat=0.0)
        elif lam_med > 1e-9:
            rec.update(status="estimated", a_hat=float(-math.log(rec["S_self"]) / lam_med))
        else:
            rec.update(status="unestimable (lambda 0)", a_hat=np.nan)
        # rank-regression baseline, leave-one-out: ranks of S_head among the others -> age by quantile mapping
        if len(others) >= 3:
            sh = np.array([lines[q]["S_head"] for q in others])
            ag = np.array([lines[q]["span"] for q in others])
            rs = stats.rankdata(sh)
            ra = stats.rankdata(ag)
            slope, icpt = np.polyfit(rs, ra, 1)
            r_star = (sh < L["S_head"]).sum() + 0.5 * (sh == L["S_head"]).sum() + 0.5
            ra_hat = float(np.clip(icpt + slope * r_star, 1, len(others)))
            rec["rank_reg_age"] = float(np.interp(ra_hat, np.arange(1, len(others) + 1), np.sort(ag)))
        else:
            rec["rank_reg_age"] = np.nan
        rows.append(rec)
    t = pd.DataFrame(rows)
    out = dict(table=t, n_lineages=len(t))
    est = t[t.status == "estimated"].dropna(subset=["a_hat", "rank_reg_age", "loo_median_age"])
    out["n_estimated"] = len(est)
    out["n_censored"] = int(t.status.str.startswith("censored").sum()) if len(t) else 0
    nan = float("nan")
    summ = dict(method=mcol, n_lineages=len(t), n_estimated=len(est), n_censored=out["n_censored"])
    if len(est) >= 3:
        a = est.true_age.values
        ape = lambda v: np.abs(v - a) / a
        e_m, e_b1, e_b2 = ape(est.a_hat.values), ape(est.loo_median_age.values), ape(est.rank_reg_age.values)
        summ.update(mdape_model=float(np.median(e_m)), mdape_loo_median=float(np.median(e_b1)),
                    mdape_rank_reg=float(np.median(e_b2)),
                    p_model_vs_loo_median=wilcoxon(np.abs(est.a_hat.values - a), np.abs(est.loo_median_age.values - a), "less"),
                    p_model_vs_rank_reg=wilcoxon(np.abs(est.a_hat.values - a), np.abs(est.rank_reg_age.values - a), "less"))
        rho, pp = perm_spearman(est.a_hat.values, a, n_perm, seed)
        summ.update(spearman=rho, spearman_perm_p=pp)
        beats = (summ["mdape_model"] < summ["mdape_loo_median"] and summ["mdape_model"] < summ["mdape_rank_reg"]
                 and summ["p_model_vs_loo_median"] < ALPHA and summ["p_model_vs_rank_reg"] < ALPHA)
        summ["model_adds_information"] = bool(beats and pp < ALPHA)
    else:
        summ.update(mdape_model=nan, mdape_loo_median=nan, mdape_rank_reg=nan, p_model_vs_loo_median=nan,
                    p_model_vs_rank_reg=nan, spearman=nan, spearman_perm_p=nan, model_adds_information=False)
    out["summary"] = summ
    return out


# ----------------------------------------------------------------------------- H8.3(b)
T_STEP = 0.05
LAM_GRID = np.logspace(-4, 1.7, 120)


def hinge_fit(t, s):
    """Hinge (broken-stick) on post-fork points. Model S(t) = 1 for t <= t*, exp(-lam (t - t*)) for t > t*.
    FIXED estimator: least squares in S over a grid t* in [t_min - 30 y, t_max] (step 0.05 y) x lam in
    [1e-4, 50] (120 log-spaced values); the fork estimate is t*, i.e. the time at which the fitted post-fork
    curve back-extrapolates to S = 1. Returns (t_star, lam, sse) or NaNs if fewer than 3 points or no decline."""
    t, s = np.asarray(t, float), np.asarray(s, float)
    if len(t) < 3 or np.all(s >= 0.999):
        return float("nan"), float("nan"), float("nan")
    ts = np.arange(t.min() - 30.0, t.max() + 1e-9, T_STEP)
    dt = t[None, :] - ts[:, None]                                     # (T, n)
    pred = np.where(dt[:, None, :] <= 0, 1.0, np.exp(-LAM_GRID[None, :, None] * np.clip(dt[:, None, :], 0, None)))
    sse = ((pred - s[None, None, :]) ** 2).sum(axis=2)               # (T, L)
    # tie-break: among equal minima take the largest t* (smallest extrapolation) -> argmin on reversed order
    flat = sse[::-1].reshape(-1)
    k = int(np.argmin(flat))
    ti, li = divmod(k, sse.shape[1])
    ti = len(ts) - 1 - ti
    return float(ts[ti]), float(LAM_GRID[li]), float(sse[ti, li])


def to_year(d):
    d = pd.to_datetime(d)
    return float(d.year + (d.dayofyear - 1) / 365.25)


def h83b(pairs, truth, n_placebo, seed):
    if pairs is None or truth is None or len(pairs) == 0:
        return pd.DataFrame(), pd.DataFrame()
    pairs = pairs.copy()
    pairs["t"] = [to_year(x) for x in pairs.target_date]
    tr = {(r.child, r.parent): r for r in truth.itertuples()}
    rows, plac = [], []
    for (child, parent), g in pairs.groupby(["child", "parent"], sort=True):
        r = tr.get((child, parent))
        truth_t = to_year(r.fork_date) if r is not None else float("nan")
        same = r.same_language if r is not None else "unknown"
        t_all = g.t.values
        mid = (t_all.min() + t_all.max()) / 2
        gp = g[~g.identical_sha.astype(bool)]
        for mname, col in PAIR_METHODS.items():
            if col not in gp:
                continue
            gg = gp.dropna(subset=[col])
            t, s = gg.t.values, gg[col].values.astype(float)
            est, lam, sse = hinge_fit(t, s)
            rec = dict(child=child, parent=parent, same_language=same, method=mname, n_points=len(gg),
                       truth=truth_t, estimate=est, lambda_=lam, error_years=est - truth_t if r is not None else np.nan,
                       baseline_midpoint=mid, baseline_error_years=mid - truth_t if r is not None else np.nan)
            rng = np.random.default_rng(seed_of(seed, child, parent, mname))
            if len(gg) >= 3 and np.isfinite(est):
                W = (t_all.max() - t_all.min()) / 2
                shift = [hinge_fit(t + rng.uniform(-W, W), s)[0] for _ in range(n_placebo)]
                shift_err = np.array(shift) - (truth_t if r is not None else t.min())
                perm = [hinge_fit(t, rng.permutation(s))[0] for _ in range(n_placebo)]
                perm_err = np.array(perm) - (truth_t if r is not None else t.min())
                obs = abs(rec["error_years"]) if r is not None else abs(est - t.min())
                rec.update(placebo_shift_median_abs_err=float(np.nanmedian(np.abs(shift_err))),
                           placebo_permute_median_abs_err=float(np.nanmedian(np.abs(perm_err))),
                           placebo_permute_frac_le_obs=float(np.nanmean(np.abs(perm_err) <= obs)),
                           placebo_shift_frac_le_obs=float(np.nanmean(np.abs(shift_err) <= obs)),
                           has_truth=r is not None)
            rows.append(rec)
    t = pd.DataFrame(rows)
    return t, plac


# ----------------------------------------------------------------------------- controls, noise, preconditions
def controls_table(snap, plans):
    rows = []
    for role in CONTROL_ROLES:
        sub = snap[(snap.role == role) & (snap.ref == "R1")]
        for port, g in sub.groupby("port", sort=True):
            g = g.sort_values(["age_years", "fraction"]).drop_duplicates("sha")
            u = g[g.underpowered != 1]
            rec = dict(port=port, role=role, n_distinct=len(g), n_usable=len(u),
                       max_shared_struct=float(u.shared_struct_pooled.max()) if len(u) else np.nan,
                       max_shared_names=float(u.shared_names.max()) if len(u) else np.nan,
                       max_surv_struct=float(u.surv_struct_pooled_either.max()) if len(u) else np.nan,
                       max_surv_names=float(u.surv_names.max()) if len(u) else np.nan)
            rec["shared_struct_reaches_floor"] = bool(len(u) and (u.shared_struct_pooled >= FLOOR).any())
            rec["shared_names_reaches_floor"] = bool(len(u) and (u.shared_names >= FLOOR).any())
            if len(u) >= MIN_SNAPSHOTS:
                rec["tau_struct"], rec["p_struct"] = kendall(u.age_years, u.surv_struct_pooled_either)
                rec["tau_names"], rec["p_names"] = kendall(u.age_years, u.surv_names)
            rows.append(rec)
    return pd.DataFrame(rows)


def controls_snapshots(snap):
    sub = snap[snap.role.isin(CONTROL_ROLES) & (snap.ref == "R1") & (snap.underpowered != 1)]
    return sub.sort_values(["port", "age_years"]).drop_duplicates(["port", "sha"])[
        ["port", "role", "fraction", "age_years", "eligible_snapshot", "surv_struct_pooled_either", "surv_names",
         "shared_struct_pooled", "shared_names"]]


def placebo_r0(snap, plans):
    df = prepare_sample(snap, plans, "calendar", "R0", LINEAGES)
    rows = []
    for port, g in df.groupby("port", sort=True):
        u = g[g.underpowered != 1].sort_values("age_years")
        if len(u) < MIN_SNAPSHOTS:
            rows.append(dict(port=port, n_usable=len(u), scored=False))
            continue
        ts, ps = kendall(u.age_years, u.surv_struct_pooled_either)
        tn, pn = kendall(u.age_years, u.surv_names)
        rows.append(dict(port=port, n_usable=len(u), scored=True, tau_struct_R0=ts, p_struct=ps, tau_names_R0=tn, p_names=pn))
    return pd.DataFrame(rows)


def noise_summary(noise):
    if noise is None or len(noise) == 0:
        return pd.DataFrame()
    rows = []
    for c in noise.columns:
        if pd.api.types.is_numeric_dtype(noise[c]):
            v = noise[c].abs().dropna()
            if len(v):
                rows.append(dict(column=c, n=len(v), max_abs=float(v.max()), median_abs=float(v.median())))
    return pd.DataFrame(rows)


def import_alt_age(df):
    """B.2 for import ports: tau against age since the first snapshot whose structure survival is >= floor."""
    rows = []
    for port in IMPORT:
        g = df[(df.port == port) & (df.underpowered != 1)].sort_values("age_years")
        h = g[g.surv_struct_pooled_either >= FLOOR]
        if len(h) == 0:
            rows.append(dict(port=port, first_appearance_age=np.nan, n=0))
            continue
        a0 = float(h.age_years.iloc[0])
        h = h[h.age_years >= a0]
        tau, p = kendall(h.age_years - a0, h.surv_struct_pooled_either) if len(h) >= 3 else (np.nan, np.nan)
        rows.append(dict(port=port, first_appearance_age=a0, n=len(h), tau_since_first_appearance=tau, p=p))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- report helpers
def fmt(x, nd=3):
    if isinstance(x, (bool, np.bool_)):
        return "yes" if x else "no"
    if isinstance(x, (int, np.integer)):
        return str(x)
    if isinstance(x, (float, np.floating)):
        if np.isnan(x):
            return ""
        if np.isinf(x):
            return "inf"
        return f"{x:.{nd}f}"
    return "" if x is None else str(x)


def md(df, nd=3):
    if df is None or len(df) == 0:
        return "_(none)_\n"
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(fmt(r[c], nd) for c in cols) + " |")
    return "\n".join(out) + "\n"


def ep_row(label, ep):
    keep = ["n_lineages", "med_tau_struct", "med_tau_names", "med_delta_struct", "med_delta_names", "names_ci_lo",
            "names_ci_hi", "p1", "p2", "p3", "p1_holm", "p2_holm", "p3_holm", "P1", "P2", "P3", "tau_crit", "n_tau_neg",
            "delta_share", "delta_crit"]
    r = {"analysis": label}
    r.update({k: ep.get(k) for k in keep})
    return r


# ----------------------------------------------------------------------------- main analysis
def run(results, plan_dir, B=2000, seed=20261122, n_perm=5000, fit_draws=500, n_placebo=500):
    results = Path(results)
    out = results / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    D = load_inputs(results, plan_dir)
    snap, plans = D["snap"], D["plans"]
    ctx = Ctx(results, B, seed)
    tables = {}
    sec = []  # report sections (title, text)

    def save(name, df):
        tables[name] = df
        if df is not None and len(df):
            df.to_csv(out / f"{name}.csv", index=False)

    # ---- 1. sample ----------------------------------------------------------------------------------
    prim = prepare_sample(snap, plans, "calendar", "R1", LINEAGES)
    present_children = sorted(set(snap.port) & set(CHILDREN))
    ds, dn, ep = analyse(prim, ctx)
    save("lineage_struct", ds)
    save("lineage_names", dn)
    dsp, _, _ = analyse(prim, ctx, "struct_persnap")
    sample = ds[["port", "stratum", "n_distinct", "n_underpowered", "n_usable", "scored"]].copy()
    missing = [p for p in LINEAGES if p not in set(sample.port)]
    for p in missing:
        sample.loc[len(sample)] = dict(port=p, stratum="", n_distinct=0, n_underpowered=0, n_usable=0, scored=False)
    sample["status"] = np.where(sample.scored, "scored", "listed, not scored (fewer than 4 usable distinct snapshots)")
    save("sample", sample)
    n_qual = int(sample.scored.sum())
    testable = n_qual >= MIN_LINEAGES
    pre = D["precond"]
    sec.append(("1. Sample", f"Independent lineages: {len(LINEAGES)} (primary sample). Child ports excluded from the primary sample "
                f"(post-fork segments only): {', '.join(CHILDREN)}; present in the results file: {', '.join(present_children) or 'none'}.\n\n"
                f"Snapshots are de-duplicated by SHA within a port; snapshots with fewer than 100 eligible functions "
                f"(underpowered) are excluded from trend tests; age = years since the first commit; reference R1 only.\n\n"
                f"Lineages with at least 4 usable distinct snapshots: **{n_qual}** of {len(LINEAGES)}. "
                f"Whole experiment testable (at least {MIN_LINEAGES} lineages qualify): **{'yes' if testable else 'NO, H8.2 untestable'}**.\n\n"
                + md(sample) + "\nPrecondition summary as provided:\n\n" + md(pre)))

    # ---- 2. per-lineage ---------------------------------------------------------------------------
    pl = ds.merge(dn, on="port", suffixes=("_struct", "_names"))[
        ["port", "stratum_struct", "n_usable_struct", "scored_struct", "tau_struct", "p_struct", "delta_struct", "delta_lo_struct",
         "delta_hi_struct", "tau_names", "p_names", "delta_names", "delta_lo_names", "delta_hi_names"]] if len(ds) else pd.DataFrame()
    pl = pl.rename(columns={"stratum_struct": "stratum", "n_usable_struct": "n_usable", "scored_struct": "scored"}) if len(pl) else pl
    if len(pl) and len(dsp):
        pl = pl.merge(dsp[["port", "tau", "p", "delta"]].rename(columns={"tau": "tau_struct_persnap", "p": "p_struct_persnap",
                                                                          "delta": "delta_struct_persnap"}), on="port", how="left")
    save("per_lineage", pl)
    sec.append(("2. Per-lineage trends (Kendall tau-b, age vs survival; Delta = surv(earliest usable) - surv(head))",
                "Per-lineage p-values are not used as evidence (Amendment 1, item 13). Delta intervals are 95% function-level bootstrap "
                f"({B} draws). A constant series is reported as tau 0.\n\n" + md(pl)))

    # ---- 3. primary endpoints ----------------------------------------------------------------------
    n = ep["n_lineages"]
    thr = pd.DataFrame([dict(n_lineages=m, sign_k_for_p_lt_0_0125=sign_test_threshold(m, 0.0125),
                             sign_k_for_p_lt_0_05=sign_test_threshold(m, 0.05)) for m in sorted({n, 11, 8} if n else {11, 8})])
    prim_tab = pd.DataFrame([
        dict(endpoint="P1 structure trend (one-sided Wilcoxon on tau, H1 median tau < 0)", raw_p=ep["p1"], holm_p=ep["p1_holm"], result="met" if ep["P1"] else "not met"),
        dict(endpoint="P2 tau_struct < tau_names (paired Wilcoxon)", raw_p=ep["p2"], holm_p=ep["p2_holm"], result="met" if ep["P2"] else "not met"),
        dict(endpoint="P3 names flat (95% bootstrap interval of median Delta_names inside +-0.10; bootstrap tail p)", raw_p=ep["p3"], holm_p=ep["p3_holm"],
             result="met" if ep["P3"] else "not met")])
    save("primary_endpoints", prim_tab)
    eff = pd.DataFrame([
        dict(criterion="median structure tau <= -0.6", value=ep["med_tau_struct"], result="met" if ep["tau_crit"] else "not met"),
        dict(criterion="structure Delta >= +0.10 in >= 70% of scored lineages", value=ep["delta_share"], result="met" if ep["delta_crit"] else "not met"),
        dict(criterion="(secondary) lineages with tau_struct < 0; exact one-sided sign-test p", value=ep["n_tau_neg"], result=fmt(ep["sign_p"], 4))])
    save("effect_size_criteria", eff)
    sec.append(("3. Primary endpoints (Holm across P1, P2, P3; alpha 0.05)",
                f"n lineages = {n}. Median Delta_names = {fmt(ep['med_delta_names'])} with 95% bootstrap interval "
                f"[{fmt(ep['names_ci_lo'])}, {fmt(ep['names_ci_hi'])}]; median Delta_struct = {fmt(ep['med_delta_struct'])}; "
                f"median tau struct = {fmt(ep['med_tau_struct'])}, names = {fmt(ep['med_tau_names'])}.\n\n" + md(prim_tab) +
                "\nEffect-size criteria (reported separately, not inferential):\n\n" + md(eff) +
                "\nPower statement (registered): exact one-sided sign test thresholds (smallest number of lineages in the predicted "
                "direction with p below the level):\n\n" + md(thr)))

    # ---- 4. strata ------------------------------------------------------------------------------------
    srows = [ep_row("pooled (11 lineages)", ep)]
    for lab, ports in [("history-preserving", HISTORY), ("import / fresh start", IMPORT), ("Boom/MBF/ZDoom line (gzdoom, edge-classic, odamex, eternity)", BOOM)]:
        srows.append(ep_row(lab, endpoints(ds, dn, _boots_of(dn, ctx, prim, "names"), ports)))
    strata = pd.DataFrame(srows)
    save("strata", strata)
    sec.append(("4. Strata (same endpoints; descriptive for small n)", md(strata)))
    save("import_alt_age", import_alt_age(prim))
    sec.append(("4b. Import ports: survival against age since first appearance of linuxdoom code", md(tables["import_alt_age"])))

    # ---- 5. sensitivities ---------------------------------------------------------------------------
    sens = {}
    cc = prepare_sample(snap, plans, "commitcount", "R1", LINEAGES)
    sens["commit-count plan"] = analyse(cc, ctx)[2]
    sens["de-duplicated (dup_share <= 0.25)"] = analyse(filt_dedup(prim), ctx)[2]
    sens["pure-C (lang_c >= 0.9, no shift >= 10 pp from head)"] = analyse(filt_pure_c(prim), ctx)[2]
    sens["per-snapshot thresholds (structure)"] = analyse(prim, ctx, "struct_persnap")[2]
    sens["partial correlation controlling log(eligible_snapshot)"] = analyse(prim, ctx, "struct", "partial")[2]
    sens["exclude snapshots with pruned set differing from head"] = analyse(filt_pruned(prim), ctx)[2]
    base = conclusion(ep)
    srows, frag = [], {}
    for lab, e in sens.items():
        c = conclusion(e)
        flips = [CONC_NAMES[i] for i in range(5) if c[i] != base[i]]
        for f in flips:
            frag.setdefault(f, []).append(lab)
        r = ep_row(lab, e)
        r["flips_vs_primary"] = "; ".join(flips) if flips else ""
        r["fragile"] = bool(flips)
        srows.append(r)
    sens_tab = pd.DataFrame(srows)
    save("sensitivities", sens_tab)
    sec.append(("5. Sensitivities (each row repeats the primary analysis under one change; a flipped conclusion is marked fragile)", md(sens_tab)))

    # ---- 6. functional form --------------------------------------------------------------------------
    ff = functional_form(prim, ctx, fit_draws)
    save("functional_form", ff)
    het = heterogeneity(ff) if len(ff) else pd.DataFrame()
    save("lambda_heterogeneity", het)
    sec.append(("6. Functional form (descriptive; constrained NLS; bootstrap intervals from function-level resampling)",
                f"Model 1 S0*exp(-lambda*age), model 2 Sinf+(S0-Sinf)*exp(-lambda*age). Burst = max interval loss rate / mean loss rate, on the half-life "
                f"snapshots and on a yearly interpolated grid. Bootstrap fits use the first {fit_draws} draws.\n\n" + md(ff) + "\nHeterogeneity of lambda (model 1):\n\n" + md(het)))

    # ---- 7. H8.3(a) -------------------------------------------------------------------------------------
    a_tabs, a_sum = [], []
    for m in ("struct", "names"):
        r = h83a(prim, METHODS[m][0], D.get("self"), SELF_COLS[m], n_perm, seed_of(seed, "h83a", m))
        t = r["table"].copy()
        t.insert(0, "method", m)
        a_tabs.append(t)
        s = dict(r["summary"])
        s["method"] = m
        a_sum.append(s)
    a_tab, a_s = pd.concat(a_tabs) if a_tabs else pd.DataFrame(), pd.DataFrame(a_sum)
    save("h83a_ages", a_tab)
    save("h83a_summary", a_s)
    sec.append(("7. H8.3(a) exploratory: age from head survival",
                "Self-origin survival surv(s0 -> head) is read from self_origin.csv (S=1 at s0); "
                "time zero is s0, so true age = age(head) - age(s0). Censored: self-origin head survival at or below 0.02. "
                f"Spearman permutation null: {n_perm} shuffles of ages, seeded. 'Adds information' = beats both baselines "
                "(lower MdAPE and paired Wilcoxon p<0.05 each) and permutation p<0.05.\n\n" + md(a_s) + "\n" + md(a_tab)))

    # ---- 8. H8.3(b) --------------------------------------------------------------------------------------
    hb, _ = h83b(D["pairs"], D["truth"], n_placebo, seed)
    save("h83b_pairs", hb)
    sec.append(("8. H8.3(b) exploratory: fork date from post-fork decline (no pass/fail rule)",
                "Estimator: hinge fit on post-fork points (identical-SHA rows excluded); the fork estimate is the time at which the fitted post-fork "
                "curve back-extrapolates to S=1. error_years = estimate - git truth. Baseline = midpoint of the grid span. Placebos: time axis shifted by a random "
                "offset (uniform within half the span) and survival values permuted over time, each refit; columns give the median absolute error under the placebo "
                "and the fraction of placebo errors no larger than the observed one. Pairs not in the truth file (unrelated pairs) are scored against the first grid date, no truth.\n\n"
                "Same-language pairs:\n\n" + md(hb[hb.same_language == "yes"] if len(hb) else hb) +
                "\nCross-language pairs (kocoa-doom / mochadoom):\n\n" + md(hb[hb.same_language != "yes"] if len(hb) else hb)))

    # ---- 9. controls ---------------------------------------------------------------------------------------
    ct = controls_table(snap, plans)
    save("controls", ct)
    save("controls_snapshots", controls_snapshots(snap))
    r0 = placebo_r0(snap, plans)
    save("placebo_r0", r0)
    sec.append(("9. Controls", "Survival vs R1 at every usable snapshot; floor = 0.02 on `shared`.\n\n" + md(ct) + "\nSnapshot detail: see controls_snapshots.csv.\n\n"
                "Placebo reference R0 (unrelated old C project): a trend of survival against R0 with age is a pipeline artefact.\n\n" + md(r0)))

    # ---- 10. noise -----------------------------------------------------------------------------------------
    ns = noise_summary(D["noise"])
    save("noise_summary", ns)
    sec.append(("10. Measurement noise (absolute differences between replicate scans)", md(ns)))

    # ---- registered predictions -------------------------------------------------------------------------------
    preds = []

    def status(met, key):
        if key in frag:
            return "fragile"
        return "met" if met else "not met"

    preds.append(("Precondition: at least 8 lineages with at least 4 usable snapshots", f"{n_qual} lineages", "met" if testable else "not met"))
    preds.append(("P1 structure trend: median tau < 0 (Holm)", f"raw p {fmt(ep['p1'], 4)}, Holm p {fmt(ep['p1_holm'], 4)}", status(ep["P1"], "P1")))
    preds.append(("P2 tau_struct < tau_names (Holm)", f"raw p {fmt(ep['p2'], 4)}, Holm p {fmt(ep['p2_holm'], 4)}", status(ep["P2"], "P2")))
    preds.append(("P3 names flat: 95% interval of median Delta_names inside +-0.10 (Holm)",
                  f"interval [{fmt(ep['names_ci_lo'])}, {fmt(ep['names_ci_hi'])}], Holm p {fmt(ep['p3_holm'], 4)}", status(ep["P3"], "P3")))
    preds.append(("Effect size: median structure tau <= -0.6", f"median tau {fmt(ep['med_tau_struct'])}", status(ep["tau_crit"], CONC_NAMES[3])))
    preds.append(("Effect size: structure Delta >= +0.10 in >= 70% of scored lineages", f"{fmt(ep['delta_share'])} of lineages", status(ep["delta_crit"], CONC_NAMES[4])))
    if len(ct):
        for role, pred in [("control-rewrite", "structure below floor at every usable snapshot (helion, rust-doom)")]:
            sub = ct[ct.role == role]
            met = bool(len(sub) and not sub.shared_struct_reaches_floor.any())
            preds.append((f"Controls {role}: {pred}", f"max shared_struct {fmt(sub.max_shared_struct.max() if len(sub) else np.nan)}", "met" if met else "not met"))
    preds.append(("H8.3(a) model adds information over both baselines (exploratory)",
                  "; ".join(f"{r.method}: {fmt(r.mdape_model)} vs {fmt(r.mdape_loo_median)}/{fmt(r.mdape_rank_reg)}" for r in a_s.itertuples()) if len(a_s) else "",
                  "met" if len(a_s) and bool(a_s.model_adds_information.any()) else "not met"))
    preds.append(("H8.3(b) fork date recovery (exploratory, no pass/fail rule)", "see section 8 (errors in years)", "not scored (no criterion)"))
    pred_tab = pd.DataFrame(preds, columns=["prediction", "result", "status"])
    save("registered_predictions", pred_tab)
    fr = "\n".join(f"- {k}: flips under {', '.join(v)}" for k, v in frag.items()) or "- none"
    block = md(pred_tab) + "\nFragile (flips under a sensitivity):\n\n" + fr + "\n"

    est = ("- Kendall tau-b via scipy (`auto`: exact when no ties, else asymptotic); a constant series gives tau 0, p 1.\n"
           "- Wilcoxon signed-rank via scipy (exact when no ties/zeros; zero differences dropped).\n"
           "- Bootstrap: resample reference functions of each snapshot (found-arrays), B draws, seeded per snapshot; Delta bootstrap = earliest minus head draws; "
           "median-Delta interval = 2.5/97.5 percentiles of the per-draw median over lineages.\n"
           "- P3 Holm p: max of the two one-sided bootstrap tail fractions at -0.10 / +0.10 (with +1 smoothing); P3 met = interval inside AND Holm p < 0.05.\n"
           "- Partial correlation: partial Spearman on ranks (linear residuals on rank of log(eligible_snapshot)).\n"
           "- Plan membership by plan_kind column or by (port, sha) in the plan file; f=0 snapshots are kept when usable and otherwise listed as underpowered.\n"
           "- Pure-C: lang_c >= 0.9 and |lang_c, lang_cpp, lang_other - head| < 0.10 each. Pruned filter: pruned token set equal to head's.\n"
           "- Head = latest usable snapshot; earliest = earliest usable.\n"
           "- H8.3(a): self-origin survival surv(s0 -> head) read from self_origin.csv; lambda from S0=1 fits of the other lineages' self-origin curves over all usable snapshots (median); "
           "rank-regression baseline maps the leave-one-out rank of the R1 head survival to an age by quantile interpolation.\n"
           "- H8.3(b): see section 8.\n")
    head = ("# DOOM-E8 phase report\n\nGenerated by measure/e8_analyze.py (seed %d, bootstrap draws %d). Plain tables; no interpretation beyond met / not met / fragile.\n\n" % (seed, B))
    text = head + "## Registered predictions scored\n\n" + block + "\n## Estimator choices (where the Amendment left room)\n\n" + est + "\n"
    for t, body in sec:
        text += f"## {t}\n\n{body}\n"
    (out / "phase_report.md").write_text(text, encoding="utf-8")
    return tables, text


def _boots_of(dn, ctx, prim, which):
    """Re-derive the names Delta bootstrap draws (cached, cheap) for the stratum subsets."""
    _, boots = per_lineage(prim, METHODS["names"][0], METHODS["names"][1], ctx)
    return boots


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", required=True)
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--seed", type=int, default=20261122)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--perm", type=int, default=5000)
    ap.add_argument("--fit-draws", type=int, default=500)
    ap.add_argument("--placebo", type=int, default=500)
    a = ap.parse_args(argv)
    run(a.results, a.plan_dir, a.boot, a.seed, a.perm, a.fit_draws, a.placebo)
    print(f"wrote {Path(a.results) / 'analysis' / 'phase_report.md'}")


if __name__ == "__main__":
    main()
