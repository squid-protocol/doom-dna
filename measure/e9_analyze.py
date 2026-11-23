#!/usr/bin/env python
"""DOOM-E9 analysis (Amendment 1 sections B, C, E, F). Reads truth (T9), predictions (P9) and spike-in results (S9),
writes P9/analysis/phase_report.md and CSV tables.

    python e9_analyze.py --truth T9 --pred P9 --spike S9 [--boot 2000] [--seed N] [--fp-dir DIR]

Deterministic given --seed. Estimators the Amendment left open are marked "FIXED:" in comments and repeated in the
report's "Estimator choices" block. Nothing here computes predictions or truth.
"""
from __future__ import annotations

import argparse
import math
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
E7_MEASURE = "/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/measure"
if E7_MEASURE not in sys.path:
    sys.path.insert(0, E7_MEASURE)
import e7_names as N  # noqa: E402

WORK = Path("/srv/storage_16tb/projects/doom-e7-work")
T9 = WORK / "e9" / "results" / "truth"
P9 = WORK / "e9" / "results" / "pred"
S9 = WORK / "e9" / "results" / "spike"
FP_A = WORK / "results" / "e7" / "phaseA" / "fingerprints"
STOPLIST = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/manifest/name_stoplist.txt")

HARD, SOFT, DESC = ("nginx", "leveldb"), ("helion", "room4doom", "rust-doom"), ("quake", "quake2", "lua")
STRATA = {"hard": HARD, "soft": SOFT, "descriptive": DESC}
FAMILY = {"chocolate-doom": "chocolate", "crispy-doom": "chocolate", "inter-doom": "chocolate",
          "prboom-plus": "prboom", "dsda-doom": "prboom", "woof": "woof", "nugget-doom": "woof"}
TRUE_VALUES = {"1", "true", "yes", "y", "t", "1.0", "copy", "transfer", "match"}
ELIG = 6
MIN_LINEAGE_PAIRS, MIN_MODULES = 5, 2
MIN_GROUP = 5          # FIXED: smallest group of dated functions for the import-cluster and clustering statistics
WINDOW_DAYS = 14
N_PERM = 200
SPIKE_TIERS = ["a", "b50", "b100", "c", "d", "e"]
SPIKE_FLOOR = 0.80
PRIMARY_STRUCT, PRIMARY_NAMES = ("structure", "primary"), ("names", "unique_key")
DAY_NS = 86_400 * 10**9


def seed_of(*parts) -> int:
    return zlib.crc32("|".join(str(p) for p in parts).encode()) & 0x7FFFFFFF


def truthy(x) -> bool:
    return not (x is None or (isinstance(x, float) and np.isnan(x))) and str(x).strip().lower() in TRUE_VALUES


def fam(p: str) -> str:
    return FAMILY.get(p, p)


def lineage_pair(a: str, b: str) -> str:
    return "|".join(sorted((fam(a), fam(b))))


def pk(pa, fa, pb, fb):
    a, b = (str(pa), str(fa)), (str(pb), str(fb))
    return (a, b) if a <= b else (b, a)


# ----------------------------------------------------------------------------- small statistics
def holm(p) -> np.ndarray:
    p = np.where(np.isnan(np.asarray(p, float)), 1.0, np.asarray(p, float))
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(np.argsort(p)):
        run = max(run, (m - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def cp_upper(k: int, n: int, alpha: float = 0.05) -> float:
    """One-sided exact (Clopper-Pearson) upper bound at level 1 - alpha."""
    if n <= 0:
        return float("nan")
    return 1.0 if k >= n else float(stats.beta.ppf(1 - alpha, k + 1, n - k))


def cp_interval(k: int, n: int, alpha: float = 0.05):
    """Two-sided exact interval."""
    if n <= 0:
        return float("nan"), float("nan")
    lo = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k >= n else float(stats.beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def fp_rate(k: int, n: int) -> dict:
    """False-positive rate per 1,000 eligible functions with the exact one-sided 95% upper bound."""
    return dict(fp=int(k), n_eligible=int(n), rate_per_1000=(1000.0 * k / n if n else float("nan")),
                upper95_per_1000=1000.0 * cp_upper(k, n) if n else float("nan"))


def cluster_boot_diff(tab: pd.DataFrame, B: int, seed: int) -> dict:
    """Paired cluster bootstrap of micro-averaged precision (set s minus set n). ``tab``: one row per cluster with
    tp_s, n_s, tp_n, n_n. A draw resamples clusters with replacement and recomputes pooled precision of each set."""
    out = dict(n_clusters=len(tab), prec_s=float("nan"), prec_n=float("nan"), diff=float("nan"), lo=float("nan"),
               hi=float("nan"), p_one_sided=float("nan"), n_valid=0)
    if not len(tab):
        return out
    tp_s, n_s, tp_n, n_n = (tab[c].to_numpy(float) for c in ("tp_s", "n_s", "tp_n", "n_n"))
    if n_s.sum() > 0:
        out["prec_s"] = tp_s.sum() / n_s.sum()
    if n_n.sum() > 0:
        out["prec_n"] = tp_n.sum() / n_n.sum()
    out["diff"] = out["prec_s"] - out["prec_n"]
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(tab), size=(B, len(tab)))
    ns, nn = n_s[idx].sum(1), n_n[idx].sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        d = np.where((ns > 0) & (nn > 0), tp_s[idx].sum(1) / ns - tp_n[idx].sum(1) / nn, np.nan)
    ok = ~np.isnan(d)
    out["n_valid"] = int(ok.sum())
    if ok.any():
        out["lo"], out["hi"] = (float(x) for x in np.percentile(d[ok], [2.5, 97.5]))
        out["p_one_sided"] = float(((d[ok] <= 0).sum() + 1) / (ok.sum() + 1))  # H0 diff <= 0
    return out


def power_gate(events: pd.DataFrame) -> dict:
    """Amendment F.18: fewer than 5 independent lineage pairs or fewer than 2 distinct modules => descriptive."""
    if events is None or not len(events):
        return dict(n_events=0, n_lineage_pairs=0, n_modules=0, descriptive=True, reason="no events")
    lp = {lineage_pair(d, r) for d, r in zip(events.donor, events.recipient)}
    mods = {str(m) for m in events.module_cluster}
    why = []
    if len(lp) < MIN_LINEAGE_PAIRS:
        why.append(f"{len(lp)} independent lineage pairs (< {MIN_LINEAGE_PAIRS})")
    if len(mods) < MIN_MODULES:
        why.append(f"{len(mods)} distinct modules (< {MIN_MODULES})")
    return dict(n_events=len(events), n_lineage_pairs=len(lp), n_modules=len(mods), descriptive=bool(why),
                reason="; ".join(why) if why else "gate met")


# ----------------------------------------------------------------------------- loading
def _read(path: Path, **kw):
    return pd.read_csv(path, dtype=kw.pop("dtype", str), keep_default_na=False, **kw) if Path(path).exists() else None


class Truth:
    def __init__(self, t9: Path):
        t9 = Path(t9)
        f = _read(t9 / "functions.csv")
        for c in ("loc", "engine_row"):
            f[c] = pd.to_numeric(f[c], errors="coerce").fillna(-1).astype(int)
        self.functions = f
        self.fn = {}
        for r in f.itertuples(index=False):
            d = r._asdict()
            self.fn[(d["program"], str(d["func_id"]))] = d
        p = _read(t9 / "pairs.csv")
        for c in ("jaccard", "jaccard_idnorm"):
            p[c] = pd.to_numeric(p[c], errors="coerce").fillna(0.0)
        p["elig"] = p["eligible_primary"].map(truthy)
        self.pairs = p
        self.pd: dict = {}
        for r in p.itertuples(index=False):
            k = pk(r.prog_a, r.func_a, r.prog_b, r.func_b)
            old = self.pd.get(k)
            if old is None or r.jaccard > old["jac"]:
                self.pd[k] = dict(jac=r.jaccard, jid=r.jaccard_idnorm, cls=r.pair_class, elig=bool(r.elig),
                                  stratum=r.stratum, event=r.event_id, donor=r.donor)
        self.stratum_of = {}
        for a, b, s in zip(p.prog_a, p.prog_b, p.stratum):
            if s:
                self.stratum_of.setdefault(tuple(sorted((a, b))), s)
        self.elig_pairs = {tuple(sorted((a, b))) for a, b, e in zip(p.prog_a, p.prog_b, p.elig) if e}
        ev = _read(t9 / "events.csv")
        self.events = ev if ev is not None else pd.DataFrame(columns=["event_id", "donor", "recipient", "module_cluster",
                                                                      "n_functions", "pair_class", "lineage_pair"])
        self.event_module = dict(zip(self.events.event_id, self.events.module_cluster))
        t2 = _read(t9 / "t2.csv")
        self.t2 = t2 if t2 is not None else pd.DataFrame(columns=["program", "func_id", "first_date_committer",
                                                                  "first_date_author", "censored"])
        self.audit = self._load_audit(t9)
        self.perm_keys = []
        pn = t9 / "perm_null.npz"
        if pn.exists():
            with np.load(pn, allow_pickle=False) as z:
                self.perm_keys = list(z.files)

    def _load_audit(self, t9: Path):
        rat = _read(t9 / "hand_audit_ratings.csv")
        if rat is None:
            return None
        smp = _read(t9 / "hand_audit_sample.csv")
        pid = {}
        if smp is not None and {"pair_id", "prog_a", "func_a", "prog_b", "func_b"} <= set(smp.columns):
            pid = {r.pair_id: pk(r.prog_a, r.func_a, r.prog_b, r.func_b) for r in smp.itertuples(index=False)}
        lab = {}
        for r in rat.itertuples(index=False):
            k = pid.get(r.pair_id)
            if k is None and str(r.pair_id).count("|") == 3:
                a = str(r.pair_id).split("|")
                k = pk(a[0], a[1], a[2], a[3])
            if k is not None and str(r.label).strip():
                lab[k] = int(truthy(r.label))
        return lab

    def dates(self, which: str = "committer") -> dict:
        col = "first_date_committer" if which == "committer" else "first_date_author"
        d = pd.to_datetime(self.t2[col], utc=True, errors="coerce")
        out = {}
        for prog, fid, dt, cen in zip(self.t2.program, self.t2.func_id, d, self.t2.censored):
            if pd.isna(dt) or truthy(cen):
                continue
            out[(prog, str(fid))] = int(dt.value)
        return out

    def body(self, prog, fid):
        r = self.fn.get((prog, str(fid)))
        return r["body_hash"] if r else None


def read_predictions(pred_dir: Path):
    pred_dir = Path(pred_dir)
    out = {}
    for key, name in (("eligible", "predictions.csv"), ("controls", "predictions_controls.csv"), ("spike", "predictions_spike.csv")):
        p = pred_dir / name
        if p.exists():
            df = pd.read_csv(p, dtype={"prog_a": str, "func_a": str, "prog_b": str, "func_b": str, "predictor": str, "variant": str},
                             keep_default_na=False)
            df["certified"] = pd.to_numeric(df["certified"], errors="coerce").fillna(0).astype(int)
            df["score_or_dist"] = pd.to_numeric(df["score_or_dist"], errors="coerce")
            out[key] = df
    return out


# ----------------------------------------------------------------------------- scoring predictions
def score_predictions(pred: pd.DataFrame, T: Truth) -> pd.DataFrame:
    df = pred.copy().reset_index(drop=True)
    keys = [pk(a, fa, b, fb) for a, fa, b, fb in zip(df.prog_a, df.func_a, df.prog_b, df.func_b)]
    info = [T.pd.get(k) for k in keys]
    df["key"] = keys
    df["in_truth"] = [i is not None and i["elig"] for i in info]
    df["jac"] = [i["jac"] if i and i["elig"] else 0.0 for i in info]
    df["jid"] = [i["jid"] if i and i["elig"] else 0.0 for i in info]
    df["cls"] = [i["cls"] if i else "" for i in info]
    df["event"] = [i["event"] if i else "" for i in info]
    df["tp9"] = df.jac >= 0.9
    df["tp6"] = df.jac >= 0.6
    df["tpid"] = df.jid >= 0.9

    def t3(r):
        a, b = T.fn.get((r.prog_a, r.func_a)), T.fn.get((r.prog_b, r.func_b))
        return bool(a and b and a["t3_module"] and a["t3_module"] == b["t3_module"])

    df["t3"] = [t3(r) for r in df.itertuples(index=False)]
    aud = T.audit or {}
    df["audit"] = [aud.get(k, -1) for k in keys]
    # co-primary truth: the hand-audit label where the pair was audited, otherwise T1 (>= 0.9) or a T3 module pair
    df["copri"] = np.where(df.audit >= 0, df.audit == 1, df.tp9 | df.t3)
    df["lineage"] = [lineage_pair(a, b) for a, b in zip(df.prog_a, df.prog_b)]
    df["stratum"] = [T.stratum_of.get(tuple(sorted((a, b))), "") for a, b in zip(df.prog_a, df.prog_b)]
    df["mapped"] = ~(df.func_a.str.startswith("row:") | df.func_b.str.startswith("row:"))

    def module(r):
        if r.event and r.event in T.event_module:
            return str(T.event_module[r.event])
        for p, f in ((r.prog_a, r.func_a), (r.prog_b, r.func_b)):
            rec = T.fn.get((p, f))
            if rec and rec["t3_module"]:
                return str(rec["t3_module"])
        return ""

    df["module"] = [module(r) for r in df.itertuples(index=False)]
    return df


def iter_sets(df: pd.DataFrame):
    """(predictor, variant, flavour, frame): names also get a pair-level certified flavour."""
    for (p, v), g in df.groupby(["predictor", "variant"], sort=True):
        yield p, v, "all", g
        if p == "names":
            yield p, v, "cert", g[g.certified == 1]


def truth_classes(T: Truth, col="jaccard", thr=0.9) -> dict:
    """Normalised-body equivalence classes of the eligible truth pairs: class key -> dict(event, cls, rows)."""
    p = T.pairs
    sel = p[p.elig & (p[col] >= thr)]
    out = {}
    for r in sel.itertuples(index=False):
        ha, hb = T.body(r.prog_a, r.func_a), T.body(r.prog_b, r.func_b)
        if ha is None or hb is None:
            continue
        a, b = (r.prog_a, ha), (r.prog_b, hb)
        k = (a, b) if a <= b else (b, a)
        d = out.setdefault(k, dict(event=r.event_id, cls=r.pair_class, stratum=r.stratum, rows=[]))
        d["rows"].append((r.prog_a, str(r.func_a), r.prog_b, str(r.func_b)))
    return out


def covered_classes(df: pd.DataFrame, T: Truth) -> set:
    out = set()
    for pa, fa, pb, fb in zip(df.prog_a, df.func_a, df.prog_b, df.func_b):
        ha, hb = T.body(pa, fa), T.body(pb, fb)
        if ha is None or hb is None:
            continue
        a, b = (pa, ha), (pb, hb)
        out.add((a, b) if a <= b else (b, a))
    return out


def set_metrics(df: pd.DataFrame, classes: dict, cov: set, tpcol: str = "tp9") -> dict:
    n = len(df)
    tp = int(df[tpcol].sum())
    cc = len(classes)
    got = sum(1 for k in classes if k in cov)
    return dict(n_pred=n, tp=tp, precision=(tp / n if n else float("nan")), n_classes=cc, covered=got,
                recall=(got / cc if cc else float("nan")))


# ----------------------------------------------------------------------------- P1
def cluster_table(ds: pd.DataFrame, dn: pd.DataFrame, tpcol: str) -> pd.DataFrame:
    keys = sorted(set(ds.lineage) | set(dn.lineage))
    gs, gn = ds.groupby("lineage"), dn.groupby("lineage")
    rows = []
    for k in keys:
        a = gs.get_group(k) if k in gs.groups else ds.iloc[0:0]
        b = gn.get_group(k) if k in gn.groups else dn.iloc[0:0]
        rows.append(dict(cluster=k, tp_s=int(a[tpcol].sum()), n_s=len(a), tp_n=int(b[tpcol].sum()), n_n=len(b)))
    return pd.DataFrame(rows, columns=["cluster", "tp_s", "n_s", "tp_n", "n_n"])


def get_set(df: pd.DataFrame, predictor: str, variant: str, flavour: str) -> pd.DataFrame:
    g = df[(df.predictor == predictor) & (df.variant == variant)]
    return g[g.certified == 1] if flavour == "cert" else g


def p1_block(df: pd.DataFrame, B: int, seed: int, tpcol: str = "copri", exclude_module: str | None = None,
             variants=(("primary", "unique_key"), ("dedup", "dedup")), names_flavour="cert") -> pd.DataFrame:
    rows = []
    for sv, nv in variants:
        s, n = get_set(df, "structure", sv, "all"), get_set(df, "names", nv, names_flavour)
        s, n = s[s.mapped], n[n.mapped]
        if exclude_module:
            s, n = s[s.module != exclude_module], n[n.module != exclude_module]
        r = cluster_boot_diff(cluster_table(s, n, tpcol), B, seed_of(seed, "P1", sv, nv, tpcol, exclude_module))
        r.update(variant=sv, names_variant=nv, names_flavour=names_flavour, truth=tpcol, n_pred_struct=len(s), n_pred_names=len(n),
                 excluded_module=exclude_module or "")
        rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- negative controls (P2)
def eligible_counts(T: Truth, variant: str) -> dict:
    f = T.functions
    f = f[f["loc"] >= ELIG]
    if variant == "dedup":
        rep = [(str(d).strip() in ("", "-1", "nan")) or str(d) == str(i) for d, i in zip(f.dup_rep, f.func_id)]
        f = f[np.array(rep, bool)]
    return f.groupby("program").size().to_dict()


def negatives_table(ctrl: pd.DataFrame, T: Truth):
    """False-positive rate per 1,000 eligible functions per stratum, predictor, variant. A negative-program
    function is a false positive for a predictor if any emitted pair containing it is not T1-confirmed."""
    rows, flagged = [], {}
    for p, v, fl, g in iter_sets(ctrl):
        ec = eligible_counts(T, "dedup" if v == "dedup" else "primary")
        for stratum, progs in STRATA.items():
            fset, conf, nraw = set(), set(), 0
            for r in g.itertuples(index=False):
                for prog, fid in ((r.prog_a, r.func_a), (r.prog_b, r.func_b)):
                    if prog in progs:
                        nraw += 1
                        (conf if r.tp9 else fset).add((prog, fid))
            n_el = sum(ec.get(x, 0) for x in progs)
            row = dict(stratum=stratum, predictor=p, variant=v, flavour=fl, programs=",".join(progs), n_raw_pairs=nraw,
                       n_confirmed_functions=len(conf), **fp_rate(len(fset), n_el))
            rows.append(row)
            flagged[(stratum, p, v, fl)] = fset
    return pd.DataFrame(rows), flagged


def p2_block(neg: pd.DataFrame, flagged: dict) -> pd.DataFrame:
    rows = []
    for sv, nv in (("primary", "unique_key"), ("dedup", "dedup")):
        s = neg[(neg.stratum == "hard") & (neg.predictor == "structure") & (neg.variant == sv) & (neg.flavour == "all")]
        n = neg[(neg.stratum == "hard") & (neg.predictor == "names") & (neg.variant == nv) & (neg.flavour == "cert")]
        if not len(s) or not len(n):
            continue
        fs, fn_ = flagged[("hard", "structure", sv, "all")], flagged[("hard", "names", nv, "cert")]
        so, no = len(fs - fn_), len(fn_ - fs)
        # FIXED: paired exact (McNemar) one-sided p over the hard-negative functions flagged by exactly one predictor;
        # H1: structure flags fewer. No discordant function => p = 1.
        p = float(stats.binom.cdf(so, so + no, 0.5)) if so + no else 1.0
        rows.append(dict(variant=sv, names_variant=nv, fp_struct=int(s.fp.iloc[0]), upper_struct=float(s.upper95_per_1000.iloc[0]),
                         fp_names=int(n.fp.iloc[0]), upper_names=float(n.upper95_per_1000.iloc[0]),
                         n_eligible=int(s.n_eligible.iloc[0]), struct_only=so, names_only=no, p_one_sided=p))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- spike-in
def spike_recall(spike_truth: pd.DataFrame, pred: pd.DataFrame, predictor: str, variant: str, flavour: str = "all") -> pd.DataFrame:
    g = get_set(pred, predictor, variant, flavour)
    hit = {pk(a, fa, b, fb) for a, fa, b, fb in zip(g.prog_a, g.func_a, g.prog_b, g.func_b)}
    st = spike_truth.copy()
    # only kept, eligible functions that map to an engine row on the recipient side count (blank rows are removed or sub-6-line functions)
    ok = st.recipient_engine_row.notna() & (st.recipient_engine_row.astype(str).str.strip() != "")
    if "kept" in st:
        ok &= st.kept.astype(str) == "1"
    if "eligible" in st:
        ok &= st.eligible.astype(str) == "1"
    st = st[ok].copy()
    st["hit"] = [pk(d, df_, r, str(int(float(row)))) in hit for d, df_, r, row in
                 zip(st.donor, st.donor_func_id, st.recipient_program, st.recipient_engine_row)]
    rows = []
    for (tier, size), x in st.groupby(["tier", "module_size"], sort=False):
        k, n = int(x.hit.sum()), len(x)
        lo, hi = cp_interval(k, n)
        rows.append(dict(predictor=predictor, variant=variant, flavour=flavour, tier=tier, module_size=size, hits=k, n=n,
                         recall=k / n if n else float("nan"), ci_lo=lo, ci_hi=hi))
    return pd.DataFrame(rows)


def spike_check(rec: pd.DataFrame) -> dict:
    """Registered check: structure recall >= 0.80 under tier (c) at BOTH sizes."""
    x = rec[(rec.predictor == "structure") & (rec.variant == "primary") & (rec.tier == "c")]
    sizes = sorted(x.module_size.unique(), key=str)
    if len(sizes) < 2:
        return dict(met=False, sizes=len(sizes), detail="fewer than two module sizes under tier (c)")
    ok = bool((x.recall >= SPIKE_FLOOR).all())
    return dict(met=ok, sizes=len(sizes), detail="; ".join(f"size {r.module_size}: {r.recall:.3f} [{r.ci_lo:.3f}, {r.ci_hi:.3f}] ({r.hits}/{r.n})" for r in x.itertuples()))


# ----------------------------------------------------------------------------- time checks
def baseline_donor_first(donor_dates: np.ndarray, rec_dates: np.ndarray) -> float:
    """Exact share of (donor, borrower) function pairs with donor date <= borrower date."""
    if not len(donor_dates) or not len(rec_dates):
        return float("nan")
    d = np.sort(donor_dates)
    return float(np.searchsorted(d, rec_dates, side="right").sum() / (len(d) * len(rec_dates)))


def order_excess(T: Truth, B: int, seed: int, which: str = "committer"):
    """Order (T3-directed port-to-port events only): donor-first share minus the same pair's baseline of
    non-transferred functions, censored functions excluded. Returns (per-pair table, summary, falsification list)."""
    dates = T.dates(which)
    ev = T.events[T.events.pair_class == "port-to-port"]
    p = T.pairs[T.pairs.elig & (T.pairs.jaccard >= 0.9)]
    rows, fals = [], []
    for (D, Rr), e in ev.groupby(["donor", "recipient"], sort=True):
        ids = set(e.event_id)
        pe = p[p.event_id.isin(ids)]
        n = first = cens = 0
        for r in pe.itertuples(index=False):
            a, b = (r.prog_a, str(r.func_a)), (r.prog_b, str(r.func_b))
            fd, fr = (a, b) if r.prog_a == D else (b, a)
            if fd[0] != D or fr[0] != Rr:
                continue
            if fd not in dates or fr not in dates:
                cens += 1
                continue
            n += 1
            first += dates[fd] <= dates[fr]
            if dates[fr] < dates[fd]:
                fals.append(dict(donor=D, recipient=Rr, donor_func=fd[1], recipient_func=fr[1], event_id=r.event_id,
                                 donor_date=pd.Timestamp(dates[fd], tz="UTC").isoformat(),
                                 recipient_date=pd.Timestamp(dates[fr], tz="UTC").isoformat()))
        matched = {(r.prog_a, str(r.func_a)) for r in p.itertuples(index=False) if {r.prog_a, r.prog_b} == {D, Rr}} | \
                  {(r.prog_b, str(r.func_b)) for r in p.itertuples(index=False) if {r.prog_a, r.prog_b} == {D, Rr}}
        dd = np.array([v for (pg, f), v in dates.items() if pg == D and (pg, f) not in matched], dtype=np.int64)
        rd = np.array([v for (pg, f), v in dates.items() if pg == Rr and (pg, f) not in matched], dtype=np.int64)
        base = baseline_donor_first(dd, rd)
        rows.append(dict(donor=D, recipient=Rr, lineage=lineage_pair(D, Rr), n_dated=n, n_censored_excluded=cens, donor_first=int(first),
                         share=(first / n if n else float("nan")), baseline=base,
                         excess=(first / n - base if n and not np.isnan(base) else float("nan")), n_baseline_donor=len(dd), n_baseline_recipient=len(rd)))
    tab = pd.DataFrame(rows, columns=["donor", "recipient", "lineage", "n_dated", "n_censored_excluded", "donor_first", "share",
                                      "baseline", "excess", "n_baseline_donor", "n_baseline_recipient"])
    use = tab[(tab.n_dated > 0) & tab.baseline.notna()]
    summ = dict(n_pairs=len(use), n_functions=int(use.n_dated.sum()), share=float("nan"), baseline=float("nan"), excess=float("nan"),
                lo=float("nan"), hi=float("nan"))
    if len(use):
        def stat(u):
            w = u.n_dated.to_numpy(float)
            return (u.donor_first.sum() / w.sum()), (w * u.baseline.to_numpy(float)).sum() / w.sum()
        s, b = stat(use)
        summ.update(share=float(s), baseline=float(b), excess=float(s - b))
        groups = {k: g for k, g in use.groupby("lineage")}
        keys = sorted(groups)
        rng = np.random.default_rng(seed_of(seed, "order", which))
        ex = []
        for _ in range(B):
            pick = rng.integers(0, len(keys), len(keys))
            u = pd.concat([groups[keys[i]] for i in pick])
            s_, b_ = stat(u)
            ex.append(s_ - b_)
        summ["lo"], summ["hi"] = (float(x) for x in np.percentile(ex, [2.5, 97.5]))
    return tab, summ, pd.DataFrame(fals, columns=["donor", "recipient", "donor_func", "recipient_func", "event_id", "donor_date", "recipient_date"])


def share_within(ns: np.ndarray, days: int = WINDOW_DAYS) -> float:
    if len(ns) < 2:
        return float("nan")
    return float((np.abs(ns - np.median(ns)) <= days * DAY_NS).mean())


def import_cluster(T: Truth, scored_struct: pd.DataFrame, B: int, seed: int, which: str = "committer"):
    """Share of a module's matched functions within 14 days of the median date, computed identically for T1-confirmed
    groups, unconfirmed groups and within-borrower permuted baselines (plus a same-directory native control)."""
    dates = T.dates(which)
    by_prog: dict = {}
    by_dir: dict = {}
    for (prog, fid), v in dates.items():
        by_prog.setdefault(prog, []).append(v)
        rec = T.fn.get((prog, fid))
        by_dir.setdefault((prog, rec["module_dir"] if rec else ""), []).append(v)
    by_prog = {k: np.array(v, dtype=np.int64) for k, v in by_prog.items()}
    by_dir = {k: np.array(v, dtype=np.int64) for k, v in by_dir.items()}
    p = T.pairs[T.pairs.elig & (T.pairs.jaccard >= 0.9)]
    rows = []
    for e in T.events.itertuples(index=False):
        pe = p[p.event_id == e.event_id]
        fs = {(r.prog_a, str(r.func_a)) if r.prog_a == e.recipient else (r.prog_b, str(r.func_b)) for r in pe.itertuples(index=False)
              if e.recipient in (r.prog_a, r.prog_b)}
        d = np.array([dates[x] for x in fs if x in dates], dtype=np.int64)
        if len(d) < MIN_GROUP:
            continue
        rows.append(dict(set="confirmed", group=e.event_id, borrower=e.recipient, lineage=lineage_pair(e.donor, e.recipient), n=len(d),
                         share=share_within(d), _d=d))
    s = scored_struct[(scored_struct.predictor == "structure") & (scored_struct.variant == "primary") & ~scored_struct.tp9]
    grp: dict = {}
    for r in s.itertuples(index=False):
        for side, (pg, f, other) in enumerate(((r.prog_a, r.func_a, r.prog_b), (r.prog_b, r.func_b, r.prog_a))):
            rec = T.fn.get((pg, f))
            grp.setdefault((pg, other, rec["module_dir"] if rec else ""), set()).add((pg, f))
    for (pg, other, md_), fs in sorted(grp.items()):
        d = np.array([dates[x] for x in fs if x in dates], dtype=np.int64)
        if len(d) >= MIN_GROUP:
            rows.append(dict(set="unconfirmed", group=f"{pg}~{other}:{md_}", borrower=pg, lineage=lineage_pair(pg, other), n=len(d),
                             share=share_within(d), _d=d))
    conf = [r for r in rows if r["set"] == "confirmed"]
    for r in conf:
        rng = np.random.default_rng(seed_of(seed, "perm", r["group"], which))
        pool = by_prog.get(r["borrower"], np.array([], dtype=np.int64))
        if len(pool) >= r["n"]:
            r_perm = np.nanmean([share_within(rng.choice(pool, r["n"], replace=False)) for _ in range(N_PERM)])
        else:
            r_perm = float("nan")
        dirs = [v for (pg, _), v in by_dir.items() if pg == r["borrower"] and len(v) >= r["n"]]
        if dirs:
            r_nat = np.nanmean([share_within(rng.choice(dirs[int(rng.integers(len(dirs)))], r["n"], replace=False)) for _ in range(N_PERM)])
        else:
            r_nat = float("nan")
        r["perm_share"], r["native_dir_share"] = float(r_perm), float(r_nat)
    tab = pd.DataFrame([{k: v for k, v in r.items() if k != "_d"} for r in rows])
    summ = dict(n_confirmed=len(conf), n_unconfirmed=sum(r["set"] == "unconfirmed" for r in rows))
    if conf:
        c = tab[tab.set == "confirmed"]
        summ.update(confirmed=float(c.share.mean()), permuted=float(c.perm_share.mean()), native_dir=float(c.native_dir_share.mean()),
                    excess=float((c.share - c.perm_share).mean()))
        diffs = c.assign(diff=c.share - c.perm_share).dropna(subset=["diff"])
        g = {k: x["diff"].to_numpy() for k, x in diffs.groupby("lineage")}
        keys = sorted(g)
        if keys:
            rng = np.random.default_rng(seed_of(seed, "import-ci", which))
            boots = [np.concatenate([g[keys[i]] for i in rng.integers(0, len(keys), len(keys))]).mean() for _ in range(B)]
            summ["lo"], summ["hi"] = (float(x) for x in np.percentile(boots, [2.5, 97.5]))
    if summ["n_unconfirmed"]:
        summ["unconfirmed"] = float(tab[tab.set == "unconfirmed"].share.mean())
    return tab, summ


# ----------------------------------------------------------------------------- module clustering
def module_cluster_share(prog: str, fids, T: Truth, edges_of=None) -> dict:
    """Share of the matched borrower functions that share a directory with >= 5 matched functions, or lie in a weakly
    connected component of >= 5 matched functions in the call graph induced on the matched set. FIXED as stated."""
    fids = sorted(set(fids))
    recs = [T.fn.get((prog, f)) for f in fids]
    dirs: dict = {}
    for r in recs:
        dirs.setdefault(r["module_dir"] if r else None, 0)
        dirs[r["module_dir"] if r else None] += 1
    in_dir = np.array([bool(r) and dirs[r["module_dir"]] >= MIN_GROUP for r in recs])
    in_comp = np.zeros(len(fids), dtype=bool)
    have_graph = False
    edges = edges_of(prog) if edges_of else None
    if edges is not None and len(edges):
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        rows = [r["engine_row"] if r else -1 for r in recs]
        pos = {r: i for i, r in enumerate(rows) if r >= 0}
        sel = [(pos[a], pos[b]) for a, b in np.asarray(edges).tolist() if a in pos and b in pos]
        m = len(fids)
        if sel:
            a, b = zip(*sel)
            g = coo_matrix((np.ones(len(sel)), (a, b)), shape=(m, m))
            _, lab = connected_components(g, directed=False)
            sizes = np.bincount(lab, minlength=lab.max() + 1)
            in_comp = (sizes[lab] >= MIN_GROUP) & np.array([x >= 0 for x in rows])
        have_graph = True
    return dict(n=len(fids), share=float((in_dir | in_comp).mean()) if fids else float("nan"), dir_share=float(in_dir.mean()) if fids else float("nan"),
                comp_share=float(in_comp.mean()) if fids else float("nan"), call_graph_used=have_graph)


def clustering_table(T: Truth, scored: pd.DataFrame, edges_of=None) -> pd.DataFrame:
    rows = []
    p = T.pairs[T.pairs.elig & (T.pairs.jaccard >= 0.9)]
    for e in T.events.itertuples(index=False):
        pe = p[p.event_id == e.event_id]
        fs = [(r.func_a if r.prog_a == e.recipient else r.func_b) for r in pe.itertuples(index=False) if e.recipient in (r.prog_a, r.prog_b)]
        if fs:
            rows.append(dict(set="confirmed", group=e.event_id, borrower=e.recipient, **module_cluster_share(e.recipient, fs, T, edges_of)))
    s = scored[(scored.predictor == "structure") & (scored.variant == "primary") & ~scored.tp9]
    for (a, b), g in s.groupby(["prog_a", "prog_b"]):
        for prog, col in ((a, "func_a"), (b, "func_b")):
            fs = list(g[col])
            if len(fs) >= MIN_GROUP:
                rows.append(dict(set="unconfirmed", group=f"{a}~{b}", borrower=prog, **module_cluster_share(prog, fs, T, edges_of)))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- H9.5
def load_stoplist() -> frozenset:
    if STOPLIST.exists():
        return frozenset(l.strip() for l in open(STOPLIST) if l.strip() and not l.startswith("#"))
    return frozenset()


def miss_table(T: Truth, scored: pd.DataFrame, classes: dict) -> pd.DataFrame:
    stop = load_stoplist()
    f = T.functions
    el = f[f["loc"] >= ELIG]
    kc, k2c = {}, {}
    for prog, nm in zip(el.program, el.name):
        k = N.name_key(nm)
        if k is not None and k not in stop:
            kc[(prog, k)] = kc.get((prog, k), 0) + 1
        k2 = N.name_key_n2(nm)
        if k2 is not None and k2 not in stop:
            k2c[(prog, k2)] = k2c.get((prog, k2), 0) + 1
    bh = f.groupby(["program", "body_hash"]).size().to_dict()
    rows = []
    sets = [("structure", "primary", "all"), ("names", "unique_key", "all"), ("names", "unique_key", "cert"),
            ("geometry", "primary", "all"), ("r1", "primary", "all")]
    raw_names = get_set(scored, "names", "unique_key", "all")
    raw_cov = covered_classes(raw_names, T)
    for pred, var, fl in sets:
        g = get_set(scored, pred, var, fl)
        cov = covered_classes(g, T)
        partners = set()
        for r in g.itertuples(index=False):
            partners.add((r.prog_a, r.func_a))
            partners.add((r.prog_b, r.func_b))
        for k, d in sorted(classes.items(), key=lambda kv: str(kv[0])):
            if k in cov:
                continue
            pa, fa, pb, fb = d["rows"][0]
            ra, rb = T.fn[(pa, fa)], T.fn[(pb, fb)]
            if pred == "names" and fl == "cert" and k in raw_cov:
                why = "uncertified_pair"
            elif ra["engine_row"] < 0 or rb["engine_row"] < 0:
                why = "unmapped_engine_row"
            elif ra["loc"] < ELIG or rb["loc"] < ELIG:
                why = "below_min_loc"
            elif pred == "structure" and (bh.get((pa, ra["body_hash"]), 0) > 1 or bh.get((pb, rb["body_hash"]), 0) > 1):
                why = "duplicated_body_blocks_reciprocal_hit"
            elif pred == "names":
                ka, kb = N.name_key(ra["name"]), N.name_key(rb["name"])
                if ka is None or kb is None or ka in stop or kb in stop:
                    why = "key_unusable_or_stoplisted"
                elif ka != kb:
                    n2a, n2b = N.name_key_n2(ra["name"]), N.name_key_n2(rb["name"])
                    why = "reprefixed_matches_only_under_n2" if n2a is not None and n2a == n2b else "renamed_key_differs"
                elif kc.get((pa, ka), 0) != 1 or kc.get((pb, kb), 0) != 1:
                    why = "key_not_unique"
                elif (pa, fa) in partners or (pb, fb) in partners:
                    why = "other_partner_emitted"
                else:
                    why = "no_match_unexplained"
            elif pred in ("geometry", "r1"):
                why = "other_partner_emitted" if ((pa, fa) in partners or (pb, fb) in partners) else "not_selected"
            elif (pa, fa) in partners or (pb, fb) in partners:
                why = "other_partner_emitted"
            else:
                why = "no_reciprocal_distinct_twin_under_fdr"
            rows.append(dict(predictor=pred, variant=var, flavour=fl, prog_a=pa, func_a=fa, prog_b=pb, func_b=fb,
                             event_id=d["event"], pair_class=d["cls"], reason=why))
    return pd.DataFrame(rows, columns=["predictor", "variant", "flavour", "prog_a", "func_a", "prog_b", "func_b", "event_id", "pair_class", "reason"])


# ----------------------------------------------------------------------------- report helpers
def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    if isinstance(x, (float, np.floating)):
        return f"{x:.{nd}f}"
    return str(x)


def md(df) -> str:
    if df is None or not len(df):
        return "_(none)_\n"
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in df.itertuples(index=False):
        out.append("| " + " | ".join(fmt(v) for v in r) + " |")
    return "\n".join(out) + "\n"


def edges_loader(fp_dir: Path | None):
    if fp_dir is None or not Path(fp_dir).exists():
        return None
    cache = {}

    def load(prog):
        if prog not in cache:
            try:
                from structural_fingerprint.fingerprint import FunctionTable, safe_name
                cache[prog] = FunctionTable.load(Path(fp_dir) / f"{safe_name(prog)}.sfp.npz").edges
            except Exception:
                cache[prog] = None
        return cache[prog]
    return load


ESTIMATORS = [
    "Unit and clusters: a prediction belongs to the lineage pair of its two programs (Chocolate/Crispy/Inter = one lineage, PrBoom+/dsda-doom, Woof/Nugget; every other program its own). Events are nested in lineage pairs; the bootstrap resamples lineage pairs (2,000 draws, seeded), paired across the two predictors.",
    "Precision is pooled (micro-averaged) over all scored predictions on eligible port pairs; predictions with an unmapped engine row (func_id 'row:N') are excluded from precision and counted per predictor.",
    "A prediction is a T1 true positive iff the pair is in pairs.csv with eligible_primary = 1 and jaccard >= 0.9 (sensitivities: >= 0.6, and jaccard_idnorm >= 0.9). Recall counts normalised-body equivalence classes (program, body_hash) of the truth pairs, covered by any predicted pair of the same two classes (multikey sets are therefore scored by class).",
    "Co-primary truth for P1 = hand-audit label where the pair was audited (hand_audit_ratings.csv), otherwise T1 (>= 0.9) or both functions in the same non-empty t3_module. The T1-only version is reported beside it.",
    "P1 compares structure (primary, full repositories filtered post hoc) with names unique-key restricted to pair-level certified pairs (symmetric error control); the de-duplicated variants are co-primary: P1 is 'structure higher' only if the interval lies above 0 in BOTH, and its p-value is the larger of the two bootstrap tails. Raw names, premasked and other variants are sensitivities.",
    "Names certified = the pair passes the E7 decoy gate in either direction (200 seeded draws, 99th percentile); the gate is evaluated on the same repositories (or de-duplicated views) the predictor used.",
    "P2: a negative-program function is a false positive for a predictor if it appears in any emitted pair that is not T1-confirmed; denominator = eligible (loc >= 6) functions of the stratum's programs (representatives only for the de-duplicated variant); upper bound = one-sided 95% Clopper-Pearson per 1,000. The p-value for Holm is a paired exact (McNemar) one-sided test over hard-negative functions flagged by exactly one predictor, the larger of the primary and de-duplicated p-values.",
    "Holm is applied to the P1 and P2 p-values only (to P2 alone if the power gate makes P1 descriptive).",
    "Spike-in recall = hit truth functions / truth functions per (tier, size), exact two-sided 95% Clopper-Pearson interval; a hit is a predicted pair (donor function, recipient engine row) in either orientation. The registered check is a point estimate >= 0.80 at both sizes under tier (c).",
    "Order excess: donor-first means donor first-appearance <= borrower first-appearance (committer date), over T1-confirmed function pairs of port-to-port events with fixed donor and borrower; baseline = exact share over all uncensored functions of the same two programs not in any T1 pair of that pair; excess = pooled observed share minus the pair-count-weighted baseline; interval by bootstrap over lineage pairs. Author date is a sensitivity.",
    "Import cluster: groups need >= 5 dated functions; confirmed groups = the borrower functions of one event; unconfirmed groups = non-T1-confirmed structure predictions grouped by (pair, side, directory), both sides taken; permuted baseline = 200 seeded within-borrower random subsets of the same size (mean per group); native control = same-size subsets drawn from one random directory of the borrower. perm_null.npz contents are listed but the baseline is recomputed here from t2.csv.",
    "Module clustering: a matched borrower function counts as clustered if its directory holds >= 5 matched functions of the group, or it lies in a weakly connected component of >= 5 in the call graph induced on the group (edges from the fingerprint tables; directory-only if they are unavailable).",
    "Leave-one-module-out: predictions and truth classes whose module (events.csv module_cluster, or t3_module of either function) is the named module are removed; textscreen is the registered exclusion; all other modules are in a descriptive table.",
    "Duplicate representative: a row is a duplicate iff dup_rep is non-empty and differs from its own func_id.",
]


# ----------------------------------------------------------------------------- main analysis
def run_analysis(truth: Path, pred_dir: Path, spike: Path | None, out: Path | None = None, B: int = 2000, seed: int = 20261122,
                 fp_dir: Path | None = None) -> dict:
    T = Truth(truth)
    preds = read_predictions(pred_dir)
    out = Path(out) if out else Path(pred_dir) / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    notes, tables, sec = [], {}, []

    def save(name, df):
        tables[name] = df
        if df is not None and len(df):
            df.to_csv(out / f"{name}.csv", index=False)

    # ---- sample ---------------------------------------------------------------------------------------
    gate = power_gate(T.events)
    ev = T.events.copy()
    if len(ev):
        ev["lineage"] = [lineage_pair(d, r) for d, r in zip(ev.donor, ev.recipient)]
    save("events", ev)
    elig_pairs = T.pairs[T.pairs.elig]
    n_t1 = int((elig_pairs.jaccard >= 0.9).sum())
    classes = truth_classes(T)
    cls_by_event = {}
    for d in classes.values():
        cls_by_event[d["event"]] = cls_by_event.get(d["event"], 0) + 1
    save("truth_size", pd.DataFrame([dict(events=gate["n_events"], lineage_pairs=gate["n_lineage_pairs"], modules=gate["n_modules"],
                                          t1_function_pairs=n_t1, t1_body_classes=len(classes),
                                          eligible_port_pairs=len(T.elig_pairs))]))
    sec.append(("1. Truth and sample", f"Events {gate['n_events']}, independent lineage pairs {gate['n_lineage_pairs']}, distinct modules "
                f"{gate['n_modules']}; T1 function pairs at Jaccard >= 0.9: {n_t1} in {len(classes)} normalised-body classes; eligible port pairs "
                f"{len(T.elig_pairs)}. Power gate: **{gate['reason']}** -> H9.1 is {'DESCRIPTIVE' if gate['descriptive'] else 'inferential'}.\n\n"
                + "Events (functions per event):\n\n" + md(ev if len(ev) else None)))

    scored = None
    if "eligible" in preds:
        e = preds["eligible"]
        e = e[[tuple(sorted((a, b))) in T.elig_pairs for a, b in zip(e.prog_a, e.prog_b)]]
        scored = score_predictions(e, T)
    else:
        notes.append("predictions.csv (eligible pairs) not found: P1 and the recall tables are skipped.")

    p1_primary = p1_all = None
    pred_counts = pm = pd.DataFrame()
    lomo_df = pd.DataFrame()
    unmapped = pd.DataFrame()
    miss = pd.DataFrame()
    if scored is not None:
        unmapped = scored.groupby(["predictor", "variant"]).agg(n_pred=("mapped", "size"), n_unmapped=("mapped", lambda x: int((~x).sum()))).reset_index()
        save("prediction_counts", unmapped)
        sc = scored[scored.mapped]
        cl06, clid = truth_classes(T, "jaccard", 0.6), truth_classes(T, "jaccard_idnorm", 0.9)
        rows = []
        for p, v, fl, g in iter_sets(sc):
            cov = covered_classes(g, T)
            m9 = set_metrics(g, classes, cov, "tp9")
            m6 = set_metrics(g, cl06, cov, "tp6")
            mi = set_metrics(g, clid, cov, "tpid")
            mc = set_metrics(g, classes, cov, "copri")
            rows.append(dict(predictor=p, variant=v, flavour=fl, **m9, precision_t3audit=mc["precision"], precision_06=m6["precision"],
                             recall_06=m6["recall"], precision_idnorm=mi["precision"], recall_idnorm=mi["recall"]))
        pm = pd.DataFrame(rows)
        save("precision_recall", pm)
        # per-class and per-stratum breakdown of the primary sets
        brk = []
        for p, v, fl, g in iter_sets(sc):
            if v not in ("primary", "unique_key", "dedup"):
                continue
            cov = covered_classes(g, T)
            for cname in ("port-to-port", "co-borrowing", "external-library", "coincidence"):
                sub = {k: d for k, d in classes.items() if d["cls"] == cname}
                brk.append(dict(predictor=p, variant=v, flavour=fl, by="pair_class", level=cname, n_pred_tp=int(((g.cls == cname) & g.tp9).sum()),
                                n_classes=len(sub), covered=sum(1 for k in sub if k in cov),
                                recall=(sum(1 for k in sub if k in cov) / len(sub) if sub else float("nan"))))
            for sname in ("c-c", "c-cpp"):
                sub = {k: d for k, d in classes.items() if d["stratum"] == sname}
                gg = g[g.stratum == sname]
                brk.append(dict(predictor=p, variant=v, flavour=fl, by="stratum", level=sname, n_pred_tp=int(gg.tp9.sum()),
                                n_classes=len(sub), covered=sum(1 for k in sub if k in cov),
                                recall=(sum(1 for k in sub if k in cov) / len(sub) if sub else float("nan"))))
        save("breakdown", pd.DataFrame(brk))
        # events: per-event recall of the primary sets
        evr = []
        for p, v, fl, g in iter_sets(sc):
            if (p, v) not in (PRIMARY_STRUCT, PRIMARY_NAMES, ("structure", "dedup"), ("names", "dedup")):
                continue
            cov = covered_classes(g, T)
            for eid, n_c in sorted(cls_by_event.items()):
                got = sum(1 for k, d in classes.items() if d["event"] == eid and k in cov)
                evr.append(dict(predictor=p, variant=v, flavour=fl, event_id=eid, classes=n_c, covered=got, recall=got / n_c))
        save("event_recall", pd.DataFrame(evr))
        # ---- P1 ------------------------------------------------------------------------------------------
        a = p1_block(sc, B, seed, "copri")
        b = p1_block(sc, B, seed, "tp9")
        c = p1_block(sc, B, seed, "copri", names_flavour="all")
        lom = p1_block(sc, B, seed, "copri", exclude_module="textscreen")
        for df_, lab in ((a, "co-primary truth, names certified"), (b, "T1 only, names certified"), (c, "co-primary truth, names raw"),
                         (lom, "leave textscreen out, co-primary truth, names certified")):
            df_.insert(0, "spec", lab)
        p1_all = pd.concat([a, b, c, lom], ignore_index=True)
        save("p1", p1_all)
        p1_primary = a
        mods = sorted({m for m in sc.module if m} | {str(m) for m in T.events.module_cluster})
        rows = []
        for m in mods:
            r = p1_block(sc, max(200, B // 10), seed, "copri", exclude_module=m).iloc[0:1]
            rows.append(dict(left_out=m, diff=float(r["diff"].iloc[0]), lo=float(r["lo"].iloc[0]), hi=float(r["hi"].iloc[0]),
                             n_struct=int(r.n_pred_struct.iloc[0]), n_names=int(r.n_pred_names.iloc[0])))
        lomo_df = pd.DataFrame(rows)
        save("leave_one_module_out", lomo_df)
        # ---- H9.5 ----------------------------------------------------------------------------------------
        miss = miss_table(T, sc, classes)
        save("h95_misses", miss)
        if len(miss):
            save("h95_summary", miss.groupby(["predictor", "variant", "flavour", "reason"]).size().rename("n_missed").reset_index())
        # ---- calibration diagnostics --------------------------------------------------------------------
        dg = Path(pred_dir) / "pairs_diag.csv"
        if dg.exists():
            diag = pd.read_csv(dg)
            keep = [c_ for c_ in ("prog_a", "prog_b", "variant", "k_struct", "k_names", "budget", "twins_ab", "twins_ba", "decoy_hits_ab",
                                  "decoy_hits_ba", "thr_ab", "thr_ba", "names_certified", "decoy_ge_ab", "decoy_ge_ba") if c_ in diag]
            save("calibration_diag", diag[keep])
    sec.append(("2. Predictor outputs", "Predictions per predictor and variant (scored on eligible port pairs; unmapped = engine row without a func_id):\n\n" + md(unmapped)))
    sec.append(("3. Precision and recall (T1; sensitivities at Jaccard 0.6 and identifier-normalised; co-primary column adds T3 and the hand audit)",
                md(pm) + ("\nHand audit: " + (f"{len(T.audit)} audited pairs used." if T.audit else "hand_audit_ratings.csv absent: skipped (T1 + T3 only).") + "\n")))
    if T.audit is None:
        notes.append("hand_audit_ratings.csv absent: the co-primary truth is T1 + T3 only.")

    # ---- P1 summary
    p1_p, p1_desc = float("nan"), gate["descriptive"]
    if p1_primary is not None and len(p1_primary):
        s_hi = bool((p1_primary.lo > 0).all()) and len(p1_primary) == 2
        p1_p = float(p1_primary.p_one_sided.max())
        sec.append(("4. P1: structure minus names, micro-averaged precision (event-clustered 95% bootstrap over lineage pairs)",
                    ("**Power gate not met: reported descriptively, no inferential claim.**\n\n" if p1_desc else "") +
                    md(p1_all) + f"\nStructure higher (interval above 0 in both co-primary variants): **{s_hi}**.\n\nLeave-one-module-out (all modules):\n\n" + md(lomo_df)))
    else:
        s_hi = False
        sec.append(("4. P1", "No eligible predictions available."))

    # ---- negatives
    neg = flagged = None
    p2 = pd.DataFrame()
    p2_p = float("nan")
    if "controls" in preds:
        cs = score_predictions(preds["controls"], T)
        neg, flagged = negatives_table(cs, T)
        save("negative_controls", neg)
        p2 = p2_block(neg, flagged)
        save("p2", p2)
        if len(p2):
            p2_p = float(p2.p_one_sided.max())
        sec.append(("5. Negative controls and P2 (false positives per 1,000 eligible functions, exact one-sided 95% upper bound)",
                    "Hard negatives (nginx, leveldb) carry P2; soft negatives (helion, room4doom, rust-doom) are reported separately; quake, quake2, lua are descriptive "
                    "(lua also appears in srb2 as a known vendoring positive: confirmed pairs are listed in n_confirmed_functions).\n\n" + md(p2) + "\n" + md(neg)))
    else:
        notes.append("predictions_controls.csv not found: P2 skipped.")
        sec.append(("5. Negative controls and P2", "predictions_controls.csv not found: skipped."))

    # ---- Holm
    ps, labels = [], []
    if not p1_desc and not np.isnan(p1_p):
        ps.append(p1_p)
        labels.append("P1")
    if not np.isnan(p2_p):
        ps.append(p2_p)
        labels.append("P2")
    adj = dict(zip(labels, holm(ps))) if ps else {}

    # ---- spike
    spike_res = pd.DataFrame()
    chk = dict(met=False, sizes=0, detail="spike-in results not found")
    st_path = Path(spike) / "spike_truth.csv" if spike else None
    if "spike" in preds and st_path is not None and st_path.exists():
        stt = pd.read_csv(st_path, dtype=str)
        parts = [spike_recall(stt, preds["spike"], p, v, fl) for p, v, fl, _ in iter_sets(preds["spike"])]
        spike_res = pd.concat([x for x in parts if len(x)], ignore_index=True) if any(len(x) for x in parts) else pd.DataFrame()
        save("spike_recall", spike_res)
        chk = spike_check(spike_res) if len(spike_res) else chk
        sec.append(("6. Spike-in recall by disguise tier and size (deterministic checks; names versus structure under renaming is DESCRIPTIVE)",
                    f"Registered check, structure recall >= {SPIKE_FLOOR:.2f} under tier (c) at both sizes: **{'met' if chk['met'] else 'not met'}** ({chk['detail']}).\n\n"
                    + md(spike_res)))
    else:
        notes.append("spike results not found: spike-in check skipped.")
        sec.append(("6. Spike-in recall", "Spike-in predictions or spike_truth.csv not found: skipped."))

    # ---- time
    o_tab, o_sum, fals = order_excess(T, B, seed)
    save("order_excess", o_tab)
    save("falsification_list", fals)
    oa_tab, oa_sum, _ = order_excess(T, max(200, B // 10), seed, "author")
    ic_tab, ic_sum = import_cluster(T, scored if scored is not None else pd.DataFrame(columns=["predictor", "variant", "tp9"]), B, seed)
    save("import_cluster", ic_tab)
    ic_a, ic_asum = import_cluster(T, scored if scored is not None else pd.DataFrame(columns=["predictor", "variant", "tp9"]), max(200, B // 10), seed, "author")
    sec.append(("7. Time checks (supporting evidence, a falsifier not a validator)",
                f"Order excess (committer date): donor-first share {fmt(o_sum['share'])}, same-pair baseline {fmt(o_sum['baseline'])}, excess **{fmt(o_sum['excess'])}** "
                f"[{fmt(o_sum['lo'])}, {fmt(o_sum['hi'])}] over {o_sum['n_functions']} dated function pairs in {o_sum['n_pairs']} port pairs "
                f"(author-date sensitivity: {fmt(oa_sum['excess'])}).\n\n" + md(o_tab) +
                f"\nImport cluster (share within {WINDOW_DAYS} days of the median): confirmed {fmt(ic_sum.get('confirmed'))}, unconfirmed {fmt(ic_sum.get('unconfirmed'))}, "
                f"within-borrower permuted {fmt(ic_sum.get('permuted'))}, native same-directory control {fmt(ic_sum.get('native_dir'))}; excess over permuted "
                f"**{fmt(ic_sum.get('excess'))}** [{fmt(ic_sum.get('lo'))}, {fmt(ic_sum.get('hi'))}] (author-date sensitivity {fmt(ic_asum.get('excess'))}). "
                f"perm_null.npz keys: {', '.join(T.perm_keys) or 'none'}.\n\n" + md(ic_tab) +
                f"\nFalsification list (recipient dated strictly before donor): {len(fals)} function pairs.\n\n" + md(fals)))

    # ---- clustering
    cl = clustering_table(T, scored if scored is not None else pd.DataFrame(columns=["predictor", "variant", "tp9", "prog_a", "prog_b"]),
                          edges_loader(fp_dir))
    save("module_clustering", cl)
    if len(cl):
        s_ = cl.groupby("set").agg(groups=("share", "size"), mean_share=("share", "mean"), mean_dir=("dir_share", "mean"), mean_comp=("comp_share", "mean")).reset_index()
    else:
        s_ = pd.DataFrame()
    sec.append(("8. Module clustering (post hoc, never used for matching)", md(s_) + "\n" + md(cl)))

    # ---- H9.5
    hs = tables.get("h95_summary")
    sec.append(("9. H9.5: what each predictor misses (every miss listed in h95_misses.csv with a reason code)", md(hs)))
    cd = tables.get("calibration_diag")
    sec.append(("10. Calibration diagnostics (sfs decoy hits are NOT a predictor)", md(cd.head(40) if cd is not None else None) +
                "\n(first 40 rows; full table in calibration_diag.csv)\n"))

    # ---- registered checks block
    reg = []
    if p1_primary is not None and len(p1_primary):
        for r in p1_primary.itertuples(index=False):
            reg.append(("P1 (" + r.variant + ")", f"diff {fmt(r.diff)} [{fmt(r.lo)}, {fmt(r.hi)}], structure {fmt(r.prec_s)} vs names {fmt(r.prec_n)}",
                        "descriptive (power gate)" if p1_desc else ("structure higher" if r.lo > 0 else "interval includes 0 or below")))
        reg.append(("P1 Holm-adjusted p", fmt(adj.get("P1", float("nan")), 4), "not applicable (descriptive)" if p1_desc else ("< 0.05" if adj.get("P1", 1) < 0.05 else ">= 0.05")))
    else:
        reg.append(("P1", "n/a", "no eligible predictions"))
    if len(p2):
        for r in p2.itertuples(index=False):
            reg.append(("P2 (" + r.variant + ")", f"hard-negative upper 95% per 1,000: structure {fmt(r.upper_struct)} (FP {r.fp_struct}) vs names certified {fmt(r.upper_names)} (FP {r.fp_names}); n {r.n_eligible}",
                        "structure bound lower" if r.upper_struct < r.upper_names else "structure bound not lower"))
        reg.append(("P2 Holm-adjusted p", fmt(adj.get("P2", float("nan")), 4), "< 0.05" if adj.get("P2", 1) < 0.05 else ">= 0.05"))
    else:
        reg.append(("P2", "n/a", "no control predictions"))
    reg.append(("Spike-in: structure recall >= 0.80 under tier (c), both sizes", chk["detail"], "met" if chk["met"] else "not met"))
    reg.append(("Order excess above baseline (deterministic check)", f"{fmt(o_sum['excess'])} [{fmt(o_sum['lo'])}, {fmt(o_sum['hi'])}]",
                "above baseline" if (o_sum["excess"] > 0 and o_sum["lo"] > 0) else "not above baseline"))
    reg.append(("Import-cluster excess over permuted baseline (deterministic check)", f"{fmt(ic_sum.get('excess'))} [{fmt(ic_sum.get('lo'))}, {fmt(ic_sum.get('hi'))}]",
                "above baseline" if (ic_sum.get("excess", float("nan")) > 0 and ic_sum.get("lo", -1) > 0) else "not above baseline"))
    reg.append(("Falsification: recipient dated strictly before donor", str(len(fals)), "listed"))
    reg.append(("Power gate", gate["reason"], "H9.1 descriptive" if gate["descriptive"] else "H9.1 inferential"))
    regdf = pd.DataFrame(reg, columns=["check", "value", "result"])
    save("registered_checks", regdf)

    notes_txt = "\n".join(f"- {n}" for n in notes) or "- none"
    body = ["# DOOM-E9 phase report\n", "## Registered checks scored\n", md(regdf), "\nHolm applies to P1 and P2 only; the spike-in, Order and import-cluster rows are deterministic checks and are not Holm-corrected. "
            "H9.5 is descriptive. The earlier fixed pass/fail thresholds are withdrawn (Amendment 1, item 20).\n",
            "## Estimator choices\n", "\n".join(f"- {e}" for e in ESTIMATORS) + f"\n\nBootstrap draws {B}, seed {seed}.\n\nInput notes:\n{notes_txt}\n"]
    for i, (title, text) in enumerate(sec, 0):
        body.append(f"## {title}\n\n{text}\n")
    (out / "phase_report.md").write_text("\n".join(body))
    return dict(tables=tables, gate=gate, p1_p=p1_p, p2_p=p2_p, holm=adj, spike_check=chk, order=o_sum, import_cluster=ic_sum, out=out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", default=str(T9))
    ap.add_argument("--pred", default=str(P9))
    ap.add_argument("--spike", default=str(S9))
    ap.add_argument("--fp-dir", default=str(FP_A))
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261122)
    a = ap.parse_args(argv)
    r = run_analysis(Path(a.truth), Path(a.pred), Path(a.spike), None, a.boot, a.seed, Path(a.fp_dir))
    print("wrote", r["out"] / "phase_report.md")


if __name__ == "__main__":
    main()
