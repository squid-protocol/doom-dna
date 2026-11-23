#!/usr/bin/env python
"""DOOM-E8b analysis (Amendment 1 sections D to G, Amendment 2). Reads the outputs of e8b_measure.py and writes
<results>/analysis/phase_report.md plus CSV tables.

    python e8b_analyze.py --results R8b --plan-dir manifest

Deterministic given --seed. Bootstrap resampling is ALWAYS over functions, never over time points.
Estimator choices the amendments left open are marked "FIXED:" and repeated in the report's
"Estimator choices" block.
"""
from __future__ import annotations

import argparse
import math
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# ----------------------------------------------------------------------------- constants
PRIMARY_PORTS = ["prboom-plus", "woof", "eternity", "edge-classic", "inter-doom", "doomretro"]
# FIXED: ports whose progenitor is NOT a C code base (EDGE is 87% C++): the lang_c >= 0.90 structural filter
# applies only against a C progenitor (Amendment 1 D.7), so it is not applied to these.
CPP_PROGENITOR_PORTS = {"edge-classic"}
MIN_ELIGIBLE = 100
A_MIN = 0.05
LANG_C_MIN = 0.90
DUP_MAX = 0.25
FLOOR = 0.02
MIN_PORTS = 5
ALPHA = 0.05
B_DEFAULT = 2000
STRUCT = "surv_struct_persnap_either"
STRUCT_LD = "surv_struct_persnap_either_ld"
POOLED = "surv_struct_pooled_either"
POOLED_LD = "surv_struct_pooled_either_ld"
NAMES = "surv_names"
NAMES_LD = "surv_names_ld"

STATUS_SUPPORTED = "SUPPORTED"
STATUS_INCONCLUSIVE = "INCONCLUSIVE"
STATUS_NOT = "wrong comparator not supported"


def seed_of(*parts) -> int:
    return zlib.crc32("|".join(str(p) for p in parts).encode()) & 0x7FFFFFFF


# ----------------------------------------------------------------------------- small statistics (from e8_analyze)
def kendall(a, s):
    """Kendall tau-b, two-sided. FIXED: a constant series gives tau=0, p=1."""
    a, s = np.asarray(a, float), np.asarray(s, float)
    if len(a) < 3 or np.ptp(a) == 0 or np.ptp(s) == 0:
        return 0.0, 1.0
    r = stats.kendalltau(a, s, variant="b", method="auto")
    return float(r.statistic), float(r.pvalue)


def partial_spearman(a, s, z):
    """FIXED: Pearson correlation of rank-residuals of age and survival after linear regression on rank(z);
    t-test with n-3 df."""
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


def holm(p) -> np.ndarray:
    p = np.where(np.isnan(np.asarray(p, float)), 1.0, np.asarray(p, float))
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def wilcoxon_greater(x) -> float:
    """One-sided signed-rank test, H1: median > 0."""
    try:
        return float(stats.wilcoxon(np.asarray(x, float), alternative="greater").pvalue)
    except ValueError:
        return float("nan")


def min_wilcoxon_p(n: int) -> float:
    """Smallest attainable one-sided exact signed-rank p for n pairs without ties/zeros: 1/2^n."""
    return 0.5 ** n


def power_note(n: int) -> str:
    return (f"Power note: with n = 6 the smallest attainable one-sided Wilcoxon signed-rank p is 1/64 = "
            f"{min_wilcoxon_p(6):.4f}; with n = 5 it is 1/32 = {min_wilcoxon_p(5):.4f}. Here n = {n}"
            + (f" (minimum attainable p = {min_wilcoxon_p(n):.4f})." if n > 0 else "."))


# ----------------------------------------------------------------------------- loading
def read_csv(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if Path(path).exists() else None


def load_inputs(results: Path, plan_dir: Path | None = None) -> dict:
    results = Path(results)
    d = {"snap": pd.read_csv(results / "snapshots_prog.csv")}
    for k, f in [("classA", "classA.csv"), ("controls", "controls_prog.csv"), ("ranking", "ranking.csv"),
                 ("arbiter", "arbiter_prog.csv"), ("decomp", "decomposition_summary.csv"),
                 ("precond", "e8b_precondition.csv")]:
        d[k] = read_csv(results / f)
        if d[k] is None and plan_dir is not None and k == "precond":
            d[k] = read_csv(Path(plan_dir) / f)
    snap = d["snap"]
    snap["date"] = pd.to_datetime(snap["date"], errors="coerce")
    if d["controls"] is not None and "date" in d["controls"]:
        d["controls"]["date"] = pd.to_datetime(d["controls"]["date"], errors="coerce")
    return d


def find_found(results: Path, sha: str, ref_name: str, subset: str) -> Path | None:
    """FIXED: tag = first 12 hex of the snapshot sha; file found/<tag>__<ref_name>__<subset>.npz (an optional
    '<port>__' prefix is tolerated by globbing)."""
    base = Path(results) / "found"
    exact = base / f"{str(sha)[:12]}__{ref_name}__{subset}.npz"
    if exact.exists():
        return exact
    hits = sorted(base.glob(f"*{str(sha)[:12]}*__{ref_name}__{subset}.npz")) if base.exists() else []
    return hits[0] if hits else None


class Ctx:
    def __init__(self, results, B=B_DEFAULT, seed=20261122):
        self.results, self.B, self.seed = Path(results), int(B), int(seed)
        self.cache = {}

    def _rng(self, *parts):
        return np.random.default_rng(seed_of(self.seed, *parts))

    def boot_mean(self, row, subset, key="found_struct_persnap"):
        """Function-level bootstrap draws of a reference-function survival (resample reference functions)."""
        ck = ("mean", row["sha"], row["ref_name"], subset, key)
        if ck in self.cache:
            return self.cache[ck]
        out = None
        fp = find_found(self.results, row["sha"], row["ref_name"], subset)
        if fp is not None:
            try:
                with np.load(fp) as z:
                    arr = np.asarray(z[key], dtype=float)
                if len(arr):
                    rng = self._rng(row["port"], row["sha"], row["ref_name"], subset, key)
                    out = np.empty(self.B)
                    step = max(1, 4_000_000 // len(arr))
                    for i in range(0, self.B, step):
                        j = min(self.B, i + step)
                        idx = rng.integers(0, len(arr), size=(j - i, len(arr)))
                        out[i:j] = arr[idx].mean(axis=1)
            except (KeyError, ValueError, OSError):
                out = None
        self.cache[ck] = out
        return out

    def boot_paired_A(self, row):
        """PAIRED function-level bootstrap of A for one port snapshot.

        FIXED construction: found/<tag>__<ref_name>__paired.npz holds boolean arrays p_in_R and p_in_LD over the
        ELIGIBLE FUNCTIONS OF THE PORT SNAPSHOT (p_in_R[i] = port function i is matched to the progenitor R,
        p_in_LD[i] = matched to linuxdoom) and scalars n_R_eligible, n_LD_eligible (number of eligible reference
        functions in R and in linuxdoom). Each draw resamples the port's eligible functions with replacement
        (same index vector for both arms, which is the pairing) and computes
            A* = sum(p_in_R[idx]) / n_R_eligible - sum(p_in_LD[idx]) / n_LD_eligible.
        The interval is the 2.5/97.5 percentile of A*."""
        ck = ("paired", row["sha"], row["ref_name"])
        if ck in self.cache:
            return self.cache[ck]
        out = None
        fp = find_found(self.results, row["sha"], row["ref_name"], "paired")
        if fp is not None:
            try:
                with np.load(fp) as z:
                    pr = np.asarray(z["p_in_R"], dtype=float)
                    pl = np.asarray(z["p_in_LD"], dtype=float)
                    nr = float(z["n_R_eligible"])
                    nl = float(z["n_LD_eligible"])
                m = len(pr)
                if m and len(pl) == m and nr > 0 and nl > 0:
                    rng = self._rng(row["port"], row["sha"], row["ref_name"], "paired")
                    out = np.empty(self.B)
                    step = max(1, 4_000_000 // m)
                    for i in range(0, self.B, step):
                        j = min(self.B, i + step)
                        idx = rng.integers(0, m, size=(j - i, m))
                        out[i:j] = pr[idx].sum(axis=1) / nr - pl[idx].sum(axis=1) / nl
            except (KeyError, ValueError, OSError):
                out = None
        self.cache[ck] = out
        return out


def ci(draws):
    if draws is None:
        return float("nan"), float("nan")
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return float(lo), float(hi)


# ----------------------------------------------------------------------------- primary sample
def is_usable(df):
    """FIXED: usable = after the progenitor (age_years > 0), eligible_snapshot >= 100, not underpowered,
    non-empty (finite structural survival)."""
    ok = (df.age_years > 0) & (df.eligible_snapshot >= MIN_ELIGIBLE) & df[STRUCT].notna()
    if "underpowered" in df:
        ok &= df.underpowered.fillna(0) != 1
    return ok


def port_all_rows(snap, port):
    g = snap[(snap.port == port) & (snap.ref == "primary") & (snap.subset == "all")]
    return g.sort_values("date").drop_duplicates("sha")


def usable_rows(snap, port, variant):
    g = port_all_rows(snap, port)
    g = g[is_usable(g)]
    if variant.get("lang_c_filter", True):
        if port not in CPP_PROGENITOR_PORTS:
            g = g[g.lang_c >= LANG_C_MIN]
    if variant.get("pure_c"):
        g = g[g.lang_c >= LANG_C_MIN]
    if variant.get("dedup"):
        g = g[g.dup_share <= DUP_MAX]
        dcol = variant.get("dedup_col")
        if dcol and dcol in g:
            g = g[g[dcol].notna()]
    return g


def lang_excluded(snap, port):
    """Snapshots otherwise usable but excluded from the structural test by lang_c < 0.90 against a C progenitor."""
    if port in CPP_PROGENITOR_PORTS:
        return port_all_rows(snap, port).iloc[0:0]
    g = port_all_rows(snap, port)
    g = g[is_usable(g)]
    return g[g.lang_c < LANG_C_MIN]


def cols_for(variant, snap):
    kind = variant.get("A", "persnap")
    if kind == "pooled":
        return POOLED, POOLED_LD if POOLED_LD in snap else STRUCT_LD
    if kind == "dedup_fn":
        return variant["r_col"], variant["ld_col"]
    return STRUCT, STRUCT_LD


def a_value(snap, row, variant):
    """A for one snapshot row under a variant (R minus linuxdoom, E8 value for the same snapshot)."""
    if variant.get("A") == "common":
        c = snap[(snap.port == row["port"]) & (snap.sha == row["sha"]) & (snap.ref == "primary")
                 & (snap.subset == "common_denominator")]
        if not len(c):
            return float("nan")
        c = c.iloc[0]
        return float(c[STRUCT] - c[STRUCT_LD])
    rc, lc = cols_for(variant, snap)
    return float(row[rc] - row[lc])


def evaluate(data, ctx, variant, ports=PRIMARY_PORTS):
    """Per-port A table for a variant. which: 'earliest' | 'second' | 'median3'."""
    snap = data["snap"]
    which = variant.get("which", "earliest")
    rows = []
    for port in ports:
        g = usable_rows(snap, port, variant)
        rec = dict(port=port, n_usable=len(g), qualifies=False, A=np.nan, lo=np.nan, hi=np.nan, passed=False,
                   sha="", date="", A_names=np.nan, S_R=np.nan, S_LD=np.nan, lang_c=np.nan, dup_share=np.nan)
        need = {"earliest": 1, "second": 2, "median3": 1}[which]
        if len(g) >= need:
            row = g.iloc[0] if which in ("earliest", "median3") else g.iloc[1]
            rc, lc = cols_for(variant, snap)
            if which == "median3":
                As = [a_value(snap, r, variant) for _, r in g.iloc[:3].iterrows()]
                A = float(np.nanmedian(As)) if not np.all(np.isnan(As)) else np.nan
            else:
                A = a_value(snap, row, variant)
            rec.update(qualifies=bool(np.isfinite(A)), A=A, sha=row["sha"], date=str(row["date"])[:10],
                       S_R=float(row[rc]) if variant.get("A") != "common" else np.nan,
                       S_LD=float(row[lc]) if variant.get("A") != "common" else np.nan,
                       lang_c=float(row["lang_c"]), dup_share=float(row["dup_share"]),
                       A_names=float(row[NAMES] - row[NAMES_LD]) if NAMES_LD in row and pd.notna(row[NAMES_LD]) else np.nan)
            can_ci = variant.get("A", "persnap") in ("persnap", "dedup_fn") and which != "median3" \
                and variant.get("A") != "pooled"
            if can_ci:
                rec["lo"], rec["hi"] = ci(ctx.boot_paired_A(row))
            if rec["qualifies"]:
                if can_ci:
                    rec["passed"] = bool(A >= A_MIN and np.isfinite(rec["lo"]) and rec["lo"] > 0)
                else:
                    # FIXED: no function-level paired arrays for this variant -> point rule A >= 0.05 only.
                    rec["passed"] = bool(A >= A_MIN)
        rows.append(rec)
    return pd.DataFrame(rows)


def decide(tab):
    """Headline rule from a per-port A table."""
    q = tab[tab.qualifies]
    n = len(q)
    npass = int(q.passed.sum())
    p = wilcoxon_greater(q.A.values) if n >= 2 else float("nan")
    if n < MIN_PORTS:
        status = STATUS_INCONCLUSIVE
    else:
        need = 5 if n >= 6 else n
        status = STATUS_SUPPORTED if (npass >= need and np.isfinite(p) and p < ALPHA) else STATUS_NOT
    return dict(n_qualifying=n, n_pass=npass, wilcoxon_p=p, min_p=min_wilcoxon_p(n) if n else float("nan"),
                status=status)


def leave_one_out(tab):
    rows = []
    q = tab[tab.qualifies]
    for port in q.port:
        r = q[q.port != port]
        d = decide(r.assign(qualifies=True))
        rows.append(dict(dropped=port, n_qualifying=d["n_qualifying"], n_pass=d["n_pass"],
                         wilcoxon_p=d["wilcoxon_p"], status=d["status"]))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- carry-over gate
def nearest_control(ctrl, kind, port, subsets, date):
    if ctrl is None:
        return None
    c = ctrl[(ctrl.kind == kind) & (ctrl[_cname(ctrl)] == port) & (ctrl.subset.isin(subsets))]
    if not len(c):
        return None
    if pd.notna(date) and c.date.notna().any():
        c = c.assign(_d=(c.date - date).abs()).sort_values("_d")
    return c.iloc[0]


def _cname(ctrl):
    return "port" if "port" in ctrl else "control"


def carry_over(data, ctx, tab):
    snap, ctrl = data["snap"], data["controls"]
    rows = []
    for _, t in tab[tab.qualifies].iterrows():
        port = t["port"]
        base = snap[(snap.port == port) & (snap.sha == t["sha"]) & (snap.ref == "primary")]
        nv = base[base.subset == "novel"]
        rec = dict(port=port, sha=t["sha"], S_novel=np.nan, lo=np.nan, hi=np.nan, S_wrong_novel=np.nan,
                   floor_ok=False, ci_ok=False, above_wrong=False, passed=False, n_novel_note="")
        if len(nv):
            r = nv.iloc[0]
            s = float(r[STRUCT]) if pd.notna(r[STRUCT]) else np.nan
            rec["S_novel"] = s
            rec["lo"], rec["hi"] = ci(ctx.boot_mean(r, "novel"))
            rec["floor_ok"] = bool(np.isfinite(s) and s >= FLOOR)
            rec["ci_ok"] = bool(np.isfinite(rec["lo"]) and rec["lo"] > 0)
            w = nearest_control(ctrl, "wrong_progenitor", port, ["novel"], pd.Timestamp(t["date"]))
            if w is not None and pd.notna(w["surv_struct"]):
                rec["S_wrong_novel"] = float(w["surv_struct"])
                rec["above_wrong"] = bool(np.isfinite(s) and s > rec["S_wrong_novel"])
            else:
                rec["n_novel_note"] = "no wrong-progenitor novel value (treated as not passing)"
        else:
            rec["n_novel_note"] = "no novel subset row (treated as not passing)"
        rec["passed"] = bool(rec["floor_ok"] and rec["ci_ok"] and rec["above_wrong"])
        rows.append(rec)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- H8b.2
def trend_tables(data):
    snap = data["snap"]
    rows = []
    for port in PRIMARY_PORTS:
        for subset in ["all", "novel"]:
            g = snap[(snap.port == port) & (snap.ref == "primary") & (snap.subset == subset)]
            g = g[(g.age_years > 0) & (g.eligible_snapshot >= MIN_ELIGIBLE)]
            if "underpowered" in g:
                g = g[g.underpowered.fillna(0) != 1]
            if port not in CPP_PROGENITOR_PORTS:
                g = g[g.lang_c >= LANG_C_MIN]
            g = g.sort_values("age_years").drop_duplicates("sha")
            for meas, col in [("structure", POOLED), ("names", NAMES)]:
                # FIXED: pooled-per-port threshold is primary for trends (Amendment 1 G.13)
                gg = g[g[col].notna()]
                n = len(gg)
                rec = dict(port=port, subset=subset, measure=meas, n=n, tau=np.nan, p=np.nan, partial=np.nan,
                           partial_p=np.nan, fragile=False)
                if n >= 4:
                    a, s = gg.age_years.values, gg[col].values
                    rec["tau"], rec["p"] = kendall(a, s)
                    rec["partial"], rec["partial_p"] = partial_spearman(a, s, np.log(gg.eligible_snapshot.values.astype(float)))
                    # FIXED: conclusion = 'decay' iff negative and p < 0.05; fragile iff raw and partial conclusions differ
                    c1 = rec["tau"] < 0 and rec["p"] < ALPHA
                    c2 = rec["partial"] < 0 and rec["partial_p"] < ALPHA
                    rec["fragile"] = bool(c1 != c2)
                rows.append(rec)
    t = pd.DataFrame(rows)
    contrast = []
    for port in PRIMARY_PORTS:
        for subset in ["all", "novel"]:
            s = t[(t.port == port) & (t.subset == subset) & (t.measure == "structure")]
            n = t[(t.port == port) & (t.subset == subset) & (t.measure == "names")]
            if len(s) and len(n) and s.iloc[0].n >= 4 and n.iloc[0].n >= 4:
                contrast.append(dict(port=port, subset=subset, tau_names_minus_struct=n.iloc[0].tau - s.iloc[0].tau,
                                     partial_names_minus_struct=n.iloc[0].partial - s.iloc[0].partial))
    return t, pd.DataFrame(contrast)


# ----------------------------------------------------------------------------- H8b.3
def ranking_table(data):
    r = data["ranking"]
    if r is None or not len(r):
        return None
    snap = data["snap"]
    prim = snap[(snap.ref == "primary")].groupby("port").ref_name.first().to_dict()
    r = r.copy()
    if "ref_name" in r:
        r = r[[prim.get(p) is None or rn == prim.get(p) for p, rn in zip(r.port, r.ref_name)]]
    r["baseline_rank1"] = 1.0 / r.K
    r["baseline_top3"] = np.minimum(3, r.K) / r.K
    # FIXED: the top-3 gate is evaluated on structural rank (rank_struct); the names rank is reported beside it.
    r["in_top3_struct"] = r.rank_struct <= 3
    r["in_top3_names"] = r.rank_names <= 3
    r["read_as_supporting"] = r.in_top3_struct
    return r


def gate_statement(rt):
    if rt is None:
        return "No ranking.csv."
    bad = rt[~rt.in_top3_struct]
    if not len(bad):
        return "Gate: the registered progenitor is in the top 3 (structure) for every ported ranked; H8b.1 may be read as supporting the map."
    return ("Gate: the registered progenitor is NOT in the top 3 (structure) for " + ", ".join(bad.port)
            + "; H8b.1's result for those ports is reported but not read as supporting the map.")


# ----------------------------------------------------------------------------- controls
def controls_tables(data, tab):
    ctrl, snap = data["controls"], data["snap"]
    spec, novel, unrel = [], [], []
    if ctrl is None:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    cn = _cname(ctrl)
    for _, t in tab[tab.qualifies].iterrows():
        port = t["port"]
        w = nearest_control(ctrl, "wrong_progenitor", port, ["all", "total"], pd.Timestamp(t["date"]))
        sr = t["S_R"]
        if w is not None and pd.notna(w["surv_struct"]):
            spec.append(dict(port=port, S_right=sr, S_wrong=float(w["surv_struct"]), passed=bool(sr > w["surv_struct"])))
        else:
            spec.append(dict(port=port, S_right=sr, S_wrong=np.nan, passed=False))
        wn = nearest_control(ctrl, "wrong_progenitor", port, ["novel"], pd.Timestamp(t["date"]))
        if wn is not None and pd.notna(wn["surv_struct"]):
            novel.append(dict(port=port, S_wrong_novel=float(wn["surv_struct"]), passed=bool(wn["surv_struct"] < FLOOR)))
        else:
            novel.append(dict(port=port, S_wrong_novel=np.nan, passed=False))
    u = ctrl[ctrl.kind == "unrelated"]
    for ref, g in u.groupby("ref_name"):
        mx = float(g.surv_struct.max())
        unrel.append(dict(ref_name=ref, n_controls=len(g), max_S=mx, passed=bool(mx < FLOOR)))
    return pd.DataFrame(spec), pd.DataFrame(novel), pd.DataFrame(unrel)


# ----------------------------------------------------------------------------- class A
def class_a_table(data):
    c = data["classA"]
    if c is None or not len(c):
        return None, None
    cols = [x for x in c.columns if x.startswith(("surv_", "shared_"))]
    summ = c.groupby("child")[cols].mean().reset_index()
    summ.insert(1, "n_steps", c.groupby("child").size().values)
    return c, summ


# ----------------------------------------------------------------------------- sensitivities
def sensitivities(data, ctx, base_status):
    snap = data["snap"]
    variants = [
        ("de-duplicated (dup_share <= 0.25)", dict(dedup=True)),
        ("pooled threshold (R pooled vs linuxdoom per-snapshot unless a pooled LD column exists)", dict(A="pooled")),
        ("pure-C (lang_c >= 0.90, all ports)", dict(pure_c=True)),
        ("second usable snapshot", dict(which="second")),
        ("median of first three usable", dict(which="median3")),
        ("common-denominator A (point rule only)", dict(A="common")),
    ]
    for dcol_r, dcol_l in [("surv_struct_persnap_either_dedup", "surv_struct_persnap_either_ld_dedup")]:
        if dcol_r in snap and dcol_l in snap:
            variants.append(("function-level dedup columns", dict(A="dedup_fn", r_col=dcol_r, ld_col=dcol_l,
                                                                 dedup=True, dedup_col=dcol_r)))
    out, tabs = [], {}
    for name, v in variants:
        t = evaluate(data, ctx, v)
        d = decide(t)
        d.update(variant=name, flips=bool(d["status"] != base_status))
        out.append(d)
        tabs[name] = t
    return pd.DataFrame(out), tabs


# ----------------------------------------------------------------------------- report helpers
def fmt(x, nd=3):
    if isinstance(x, (float, np.floating)):
        return "NA" if not np.isfinite(x) else f"{x:.{nd}f}"
    if isinstance(x, (bool, np.bool_)):
        return "yes" if x else "no"
    return str(x)


def md_table(df, cols=None):
    if df is None or not len(df):
        return "_(none)_\n"
    cols = cols or list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(fmt(r[c]) for c in cols) + " |")
    return "\n".join(lines) + "\n"


ESTIMATOR_CHOICES = [
    "Bootstrap: 2000 draws (--B), seeded per (seed, port, sha, reference), always over FUNCTIONS never over time points; percentile 95% interval.",
    "A (primary) = surv_struct_persnap_either (reference R, subset all) minus the linuxdoom value for the same snapshot "
    "(surv_struct_persnap_either_ld); per-snapshot FDR 0.01 thresholds (Amendment 1 G.13).",
    "PAIRED bootstrap of A: resample the port snapshot's ELIGIBLE FUNCTIONS with replacement (one index vector shared by both arms) "
    "from found/<tag>__<ref_name>__paired.npz arrays p_in_R and p_in_LD; A* = sum(p_in_R[idx])/n_R_eligible - sum(p_in_LD[idx])/n_LD_eligible, "
    "with n_R_eligible, n_LD_eligible the stored reference-function counts. Interval = 2.5/97.5 percentiles of A*. A PASS needs A >= +0.05 and interval lower bound > 0.",
    "found-file tag = first 12 characters of the snapshot sha: found/<sha12>__<ref_name>__<subset>.npz (also paired, novel).",
    "Usable snapshot = dated after the progenitor (age_years > 0), eligible_snapshot >= 100, underpowered != 1, finite structural survival; earliest/second/third by date.",
    "lang_c < 0.90 snapshots are excluded from the structural test against a C progenitor (not applied to edge-classic, whose progenitor EDGE is C++); excluded snapshots are listed with A_names.",
    "Headline: n qualifying ports < 5 -> INCONCLUSIVE; else SUPPORTED iff n_pass >= 5 (all if n < 6) AND one-sided Wilcoxon signed-rank (H1: A > 0) p < 0.05; otherwise 'wrong comparator not supported'.",
    "Leave-one-port-out: the same decision rule re-run on each (n-1)-port subset.",
    "Carry-over gate per port: S_R^novel(earliest usable) >= 0.02, function-level bootstrap lower bound > 0, and above the wrong-progenitor novel survival "
    "(nearest control date); a missing novel row or missing wrong-progenitor value counts as not passing. Prediction scored 'met' iff every qualifying port passes.",
    "Variants without function-level paired arrays (pooled, median-of-three, common-denominator) use the point rule A >= 0.05 only; the pooled variant uses surv_struct_pooled_either_ld if supplied, else the per-snapshot linuxdoom value (mixed).",
    "H8b.2: Kendall tau-b and partial Spearman (control log(eligible_snapshot)) of POOLED-threshold survival vs age_years, snapshots after the progenitor, n >= 4; "
    "'decay' = negative with p < 0.05; fragile iff raw and partial conclusions differ. Scored met iff median tau and median partial tau (structure, all) are both negative; "
    "fragile if their signs differ or any port is fragile in the structure/all trend; inconclusive with fewer than 3 testable ports.",
    "H8b.3: top-3 gate uses rank_struct; baseline = 1/K for rank 1 and min(3,K)/K for top 3. Scored met iff every ranked port has the registered progenitor in the top 3.",
    "Controls: differential specificity S_R_right > S_R_wrong (total, nearest control date); wrong-progenitor novel < 0.02; every new progenitor vs every unrelated control < 0.02.",
    "Sensitivities flip a conclusion (status differs from the primary status) -> marked fragile in the scored block.",
]


# ----------------------------------------------------------------------------- main analysis
def run(results, plan_dir=None, B=B_DEFAULT, seed=20261122):
    results = Path(results)
    out = results / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    data = load_inputs(results, plan_dir)
    ctx = Ctx(results, B, seed)
    snap = data["snap"]

    base_v = {}
    tab = evaluate(data, ctx, base_v)
    dec = decide(tab)
    loo = leave_one_out(tab)
    tab2 = evaluate(data, ctx, dict(which="second"))
    tab3 = evaluate(data, ctx, dict(which="median3"))
    tabc = evaluate(data, ctx, dict(A="common"))
    excl_rows = []
    for port in PRIMARY_PORTS:
        for _, r in lang_excluded(snap, port).iterrows():
            excl_rows.append(dict(port=port, sha=r["sha"], date=str(r["date"])[:10], lang_c=r["lang_c"],
                                  A_struct_not_tested=r[STRUCT] - r[STRUCT_LD],
                                  A_names=(r[NAMES] - r[NAMES_LD]) if NAMES_LD in r else np.nan))
    excl = pd.DataFrame(excl_rows)
    co = carry_over(data, ctx, tab)
    trend, contrast = trend_tables(data)
    rank = ranking_table(data)
    spec, cnov, cunrel = controls_tables(data, tab)
    cls_a, cls_a_sum = class_a_table(data)
    sens, sens_tabs = sensitivities(data, ctx, dec["status"])

    # ---- scoring
    def flips():
        return bool(len(sens) and sens.flips.any())

    h1 = {STATUS_SUPPORTED: "met", STATUS_INCONCLUSIVE: "inconclusive", STATUS_NOT: "not met"}[dec["status"]]
    h1_label = f"fragile (primary: {h1})" if flips() else h1
    if len(co):
        h_co = "met" if bool(co.passed.all()) else "not met"
    else:
        h_co = "inconclusive"
    if (trend.n >= 4).sum() and len(trend[(trend.subset == "all") & (trend.measure == "structure") & (trend.n >= 4)]) >= 3:
        ts = trend[(trend.subset == "all") & (trend.measure == "structure") & (trend.n >= 4)]
        mt, mp = float(ts.tau.median()), float(ts.partial.median())
        if (mt < 0) != (mp < 0) or ts.fragile.any():
            h2 = "fragile"
        elif mt < 0 and mp < 0:
            h2 = "met"
        else:
            h2 = "not met"
    else:
        h2 = "inconclusive"
    if rank is None or not len(rank):
        h3 = "inconclusive"
    else:
        h3 = "met" if bool(rank.in_top3_struct.all()) else "not met"
    cres = []
    for d in (spec, cnov, cunrel):
        if len(d):
            cres.append(bool(d.passed.all()))
    h4 = "inconclusive" if not cres else ("met" if all(cres) else "not met")

    # ---- tables
    def save(name, df):
        if df is not None and len(df):
            df.to_csv(out / f"{name}.csv", index=False)

    save("h8b1_primary", tab)
    save("h8b1_second_usable", tab2)
    save("h8b1_median_first3", tab3)
    save("h8b1_common_denominator", tabc)
    save("h8b1_leave_one_out", loo)
    save("h8b1_lang_c_excluded", excl)
    save("h8b1_carry_over", co)
    save("h8b2_trends", trend)
    save("h8b2_contrast", contrast)
    save("h8b3_ranking", rank)
    save("controls_specificity", spec)
    save("controls_wrong_novel", cnov)
    save("controls_unrelated", cunrel)
    save("classA_pairs", cls_a)
    save("classA_summary", cls_a_sum)
    save("sensitivities", sens)
    for name, t in sens_tabs.items():
        save("sens_" + "".join(c if c.isalnum() else "_" for c in name)[:40].strip("_"), t)
    for k, f in [("decomp", "decomposition_summary"), ("arbiter", "arbiter_prog"), ("precond", "precondition")]:
        save(f, data[k])

    qn = tab[tab.qualifies]
    L = []
    L += ["# DOOM-E8b phase report", "",
          "Post hoc follow-up to E8 on largely the same ports and scans: not independent confirmation.", "",
          "## Registered predictions scored", "",
          f"- H8b.1 (headline: progenitor beats linuxdoom, >= 5 of 6 ports and Wilcoxon p < 0.05): **{h1_label}**",
          f"- H8b.1 carry-over gate (novel survival >= 0.02, interval > 0, above wrong progenitor): **{h_co}**",
          f"- H8b.2 (structure decay vs age, partial on log eligible; descriptive): **{h2}**",
          f"- H8b.3 (registered progenitor in top 3 of the candidate ranking): **{h3}**",
          f"- H8b.4 (controls: differential specificity, wrong-progenitor novel < 0.02, unrelated < 0.02): **{h4}**",
          "- Class A calibration stratum: descriptive, not scored.", "",
          "## Estimator choices", ""]
    L += [f"{i}. {t}" for i, t in enumerate(ESTIMATOR_CHOICES, 1)]
    L += ["", "## 1. H8b.1 primary test: A at the earliest usable snapshot", "",
          md_table(tab, ["port", "date", "n_usable", "S_R", "S_LD", "A", "lo", "hi", "passed", "A_names", "lang_c", "dup_share", "qualifies"]),
          f"Qualifying ports: {dec['n_qualifying']}; passing: {dec['n_pass']}; one-sided Wilcoxon p = {fmt(dec['wilcoxon_p'], 4)}.",
          "", f"**Headline status: {dec['status']}**", "", power_note(dec["n_qualifying"]), "",
          "### 1a. Leave-one-port-out", "", md_table(loo),
          "### 1b. A at second usable snapshot", "", md_table(tab2, ["port", "date", "A", "lo", "hi", "passed"]),
          "### 1c. A as median of first three usable snapshots", "", md_table(tab3, ["port", "A", "passed"]),
          "### 1d. Common-denominator A", "", md_table(tabc, ["port", "date", "A", "passed"]),
          "### 1e. Snapshots excluded by lang_c < 0.90 (structural test; names shown beside)", "", md_table(excl),
          "## 2. Carry-over gate", "", md_table(co),
          f"Share of ports passing: {fmt(float(co.passed.mean()) if len(co) else float('nan'))}"
          f" ({int(co.passed.sum()) if len(co) else 0} of {len(co)}).", "",
          "## 3. H8b.2 decay vs age (descriptive)", "", md_table(trend),
          "Names minus structure (tau and partial):", "", md_table(contrast),
          "## 4. H8b.3 ranking", "", md_table(rank), gate_statement(rank), "",
          "## 5. Controls", "", "### 5a. Differential specificity (S_R_right > S_R_wrong, total)", "", md_table(spec),
          "### 5b. Wrong-progenitor novel subset below 0.02", "", md_table(cnov),
          "### 5c. New progenitors vs unrelated controls below 0.02", "", md_table(cunrel),
          "## 6. Class A calibration stratum (descriptive only)", "", md_table(cls_a_sum), md_table(cls_a),
          "## 7. Sensitivities (status flip = fragile)", "", md_table(sens, ["variant", "n_qualifying", "n_pass", "wilcoxon_p", "status", "flips"])]
    for name, t in sens_tabs.items():
        L += [f"### {name}", "", md_table(t, ["port", "date", "A", "lo", "hi", "passed", "qualifies"])]
    if any(c.endswith("_dedup") for c in snap.columns):
        L += ["Function-level dedup columns were supplied by the measurement script and are used above.", ""]
    else:
        L += ["No function-level dedup column was supplied; the de-duplicated sensitivity uses snapshot-level dup_share <= 0.25 only.", ""]
    L += ["## 8. Supplementary inputs", "", "### Decomposition", "", md_table(data["decomp"]),
          "### Name-blind arbiter", "", md_table(data["arbiter"]), "### Precondition", "", md_table(data["precond"])]
    (out / "phase_report.md").write_text("\n".join(L) + "\n")
    return dict(decision=dec, primary=tab, loo=loo, carry=co, trend=trend, rank=rank, spec=spec, cnov=cnov,
                cunrel=cunrel, sens=sens, scored=dict(h1=h1_label, carry=h_co, h2=h2, h3=h3, h4=h4), out=out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", required=True)
    ap.add_argument("--plan-dir", default="manifest")
    ap.add_argument("--seed", type=int, default=20261122)
    ap.add_argument("--B", type=int, default=B_DEFAULT)
    a = ap.parse_args(argv)
    r = run(a.results, a.plan_dir, a.B, a.seed)
    print(f"H8b.1: {r['decision']['status']} ({r['decision']['n_pass']}/{r['decision']['n_qualifying']} pass); report {r['out'] / 'phase_report.md'}")


if __name__ == "__main__":
    main()
