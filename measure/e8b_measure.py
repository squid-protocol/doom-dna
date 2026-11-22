"""DOOM-E8b measurement: progenitor-anchored survival (Amendments 1 and 2; E8 and E7 code reused, never rewritten).

    python e8b_measure.py run [--only-validate] [--results DIR] [--stages a,b,...] [--no-text]

``--only-validate`` runs only what may be run before the registered analysis: (a) the reproduction check (the generalised
pipeline pointed at reference = linuxdoom must reproduce E8's surv_names / surv_struct_persnap_either /
surv_struct_pooled_either on a handful of E8 snapshots), (b) the decomposition of every progenitor against linuxdoom
(progenitor-versus-linuxdoom only; no port data), (c) decomposition self-consistency. ``run`` without it also produces
the port-versus-progenitor outputs and is launched by the parent only.

Outputs under R8B (default /srv/storage_16tb/projects/doom-e7-work/e8b/results):
  validation.csv, decomposition.csv, decomposition_summary.csv, decomp/<pin>.npz (R-function -> linuxdoom row map),
  snapshots_prog.csv, found/<tag>__<refkey>__<port>.npz, classA.csv, controls_prog.csv, ranking.csv,
  ranking_summary.csv, arbiter_prog.csv, errors.csv; caches under cache/ and fingerprints/ (resumable).

Definitions fixed where the specification was open
* decomposition classes: unchanged_inherited = twin (either direction, per-pair FDR 0.01) in linuxdoom; modified_inherited
  = no twin and (E7 stoplisted name key present in linuxdoom's keys, OR name-blind arbiter verdict exact/near/derived
  against ALL linuxdoom functions); novel = neither. Variant 'twin_only': everything not a twin is novel.
* subsets (snapshots_prog.csv): all, unchanged_inherited, modified_inherited, novel, common_denominator (= unchanged or
  modified, primary rule), novel_twin_only (novel under the twin_only variant). surv_* of a subset = found / subset size;
  blank when the subset is empty. shared_struct_persnap and shared_names are per (snapshot, reference) and repeat across
  that pair's subset rows.
* snapshot set per (port, reference): E8 calendar-plan rows, distinct sha, finished and fingerprintable scans, date
  strictly after the reference's filter date (1999-12-31 for boom-2.02 and mbf-2.03, else the pin's commit_date),
  eligible_snapshot >= 100. underpowered is therefore always 0 in snapshots_prog.csv (kept for schema parity). The pooled
  threshold is ONE per (port, reference, direction) over exactly that kept set.
* usable_rank (1-based by date, sha), is_first_usable, is_second_usable, in_first_three, and median3_<measure> (median of
  the first three usable snapshots' value for that subset, repeated on those three rows).
* age_years = (date - port origin date, the f=0 calendar row) / 365.25 as E8; age_prog_years = (date - filter date)/365.25.
* decoy family: names_pair is E8's with fam_all extended by EXT_FAMILY on every entry, and each progenitor label's family =
  {label} + EXT_FAMILY + declared families of the ports that use it (so the pool excludes the whole DOOM family).
* found/<tag>__<refkey>__<port>.npz: found_names, found_struct_persnap, found_struct_pooled over the reference's eligible
  functions (E7 table order); pair arrays pairs_r / pairs_p (reference eligible position, port-snapshot eligible position
  of accepted per-snapshot twins, both directions, deduplicated); for primary-role runs also ld_pairs_r / ld_pairs_p (the same
  against linuxdoom) so a bootstrap over the functions of P is possible; p_n_elig. E8's own linuxdoom found arrays stay in
  halflife/results/found/<tag>__R1.npz.
* class A: reference = parent snapshot at the fork commit; child snapshots = grid steps >= 1 plus the child's head (plan
  fraction 1) when it is not a grid step and is after the fork; contemporaneous values are copied from pairs_grid.csv
  (columns prefixed contemp_), not recomputed.
* controls: wrong progenitor per Amendment 1 E.9 on the port's primary snapshot set (subsets all and novel, plus the full
  list); the six primary progenitors against the unrelated controls' E8 calendar snapshots (non-empty scans; subset all).
* ranking: candidate = one snapshot per distinct repository, the latest strictly before the port's origin date, excluding
  the port and its declared descendants; the 8 progenitor scans are dated by their filter dates and belong to repository
  boom/mbf/smmu/edge/crispy-doom/chocolate-doom/winmbf/prboom-2.5.0; linuxdoom is listed (kind reference_context) but never
  ranked. The registered progenitor stands in for its repository's representative when it differs (flag reported).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
import time
import traceback
from datetime import date
from pathlib import Path

import numpy as np

E8M = "/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/measure"
E7M = "/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/measure"
SFS = "/srv/storage_16tb/projects/structural-fingerprint-scanner/src"
for _p in (E7M, SFS, E8M):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import e8_measure as M  # noqa: E402  (reuses fingerprinting, twin search, pooled thresholds, names/decoy, found arrays)
import e8_snap  # noqa: E402

A, N, E, T = M.A, M.N, M.E, M.T
FunctionTable = M.FunctionTable

REPO = Path(__file__).resolve().parents[1]
WORK = M.WORK
HL = M.HL
E8B_WORK = WORK / "e8b"
PROG_SNAPS = E8B_WORK / "snaps"
R8B = E8B_WORK / "results"
PINS_CSV = REPO / "manifest" / "e8b_pins.csv"
E8_MAN = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/manifest")
MIN_POWER = M.MIN_POWER

# ---------------------------------------------------------------- registered tables (Amendment 1 B, 2; E.9)

# port, primary progenitor pin, class, secondary (descriptive), descriptive-only
PRIMARY_MAP = [
    dict(port="prboom-plus", primary="boom-2.02", cls="B", secondary=["mbf-2.03"], descriptive=["prboom-2.5.0"]),
    dict(port="woof", primary="mbf-2.03", cls="B", secondary=["boom-2.02"], descriptive=["winmbf"]),
    dict(port="eternity", primary="smmu", cls="B", secondary=["mbf-2.03"], descriptive=[]),
    dict(port="edge-classic", primary="edge@2021-09-17", cls="C", secondary=["boom-2.02"], descriptive=[]),
    dict(port="inter-doom", primary="crispy-doom@2023-06-26", cls="C", secondary=[], descriptive=[]),
    dict(port="doomretro", primary="chocolate-doom@2013-12-10", cls="C", secondary=[], descriptive=[]),
]
PRIMARY_PINS = [m["primary"] for m in PRIMARY_MAP]
FILTER_DATE_OVERRIDE = {"boom-2.02": date(1999, 12, 31), "mbf-2.03": date(1999, 12, 31)}
CLASS_A = [("crispy-doom", "chocolate-doom"), ("dsda-doom", "prboom-plus"), ("nugget-doom", "woof"),
           ("kocoa-doom", "mochadoom")]
BOOM_LINE = ["prboom-plus", "woof", "eternity", "edge-classic"]
CHOCOLATE_LINE = ["inter-doom", "doomretro"]
WRONG = {**{p: "chocolate-doom@2013-12-10" for p in BOOM_LINE}, **{p: "boom-2.02" for p in CHOCOLATE_LINE}}
UNRELATED = ["curl", "libuv", "nginx", "helion", "rust-doom"]
# Amendment 1 G.14: added to the DOOM family set for the decoy vocabulary
EXT_FAMILY = frozenset({"boom", "mbf", "winmbf", "smmu", "prboom-2.5.0", "edge"})
SUBSETS = ["all", "unchanged_inherited", "modified_inherited", "novel", "common_denominator", "novel_twin_only"]
U, MOD, NOV = "unchanged_inherited", "modified_inherited", "novel"
VERDICTS_DERIVED = ("exact", "near", "derived")

SNAP_COLS = ["port", "role", "class", "ref", "ref_name", "subset", "plan_kind", "sha", "date", "age_years",
             "age_port_years", "second_usable", "first3_median_flag", "surv_names_ld", "surv_struct_persnap_either_ld",
             "surv_struct_pooled_either_ld", "surv_names_dedup", "surv_struct_persnap_either_dedup",
             "surv_names_ld_dedup", "surv_struct_persnap_either_ld_dedup", "n_subset", "n_ref_eligible", "eligible_snapshot", "dup_share", "lang_c", "lang_cpp",
             "lang_other", "underpowered", "usable_rank", "is_first_usable", "is_second_usable", "in_first_three",
             "surv_names", "surv_struct_persnap_either", "surv_struct_pooled_either", "median3_surv_names",
             "median3_surv_struct_persnap_either", "median3_surv_struct_pooled_either", "shared_struct_persnap",
             "shared_names", "names_certified", "tag"]
DECOMP_COLS = ["pin", "func_index", "name", "path", "loc", "class_primary", "class_twin_only", "twin", "name_key_match",
               "text_verdict", "ld_row"]
CLASSA_COLS = ["child", "parent", "step", "kind", "date", "child_sha", "parent_fork_sha", "same_language",
               "n_ref_eligible", "eligible_snapshot", "surv_struct_fork_persnap", "surv_names_fork", "shared_struct_persnap",
               "shared_names", "dup_share", "lang_c", "lang_cpp", "lang_other", "age_years"]
CONTROL_COLS = ["port", "kind", "ref_name", "subset", "plan_kind", "sha", "date", "n_subset", "n_ref_eligible",
                "eligible_snapshot", "underpowered", "after_ref_date", "surv_names", "surv_struct", "surv_struct_persnap_either",
                "surv_struct_pooled_either", "shared_struct_persnap", "shared_names", "names_certified", "tag"]
RANKW_COLS = ["port", "ref_name", "K", "one_over_K", "rank_struct", "rank_names", "registered_shared_struct",
              "registered_shared_names", "top1_struct", "top1_struct_value", "top1_names", "top1_names_value",
              "linuxdoom_shared_struct", "linuxdoom_shared_names", "ties_struct", "ties_names", "registered_is_repr"]
RANK_COLS = ["port", "metric", "port_tag", "port_date", "origin_date", "candidate_repo", "candidate_tag", "candidate_date",
             "candidate_kind", "candidate_eligible", "value", "rank", "K", "one_over_K", "is_registered", "registered_rank",
             "registered_is_repr"]
ARB_COLS = ["kind", "port", "ref_name", "which", "tag", "date", "eligible_ref", "exact", "near", "derived", "gone",
            "share_exact_near", "share_exact_near_derived"]


# ---------------------------------------------------------------- pure helpers (unit-tested)

def safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def repo_of(pin_name: str) -> str:
    """Repository a progenitor pin belongs to: boom-2.02 -> boom, mbf-2.03 -> mbf, edge@date -> edge, ..."""
    base = pin_name.split("@")[0]
    return {"boom-2.02": "boom", "mbf-2.03": "mbf"}.get(base, base)


def classify(twin, name_match, text_derived):
    """Decomposition classes (primary rule and twin_only variant) over one progenitor's eligible functions."""
    twin, nm, tx = (np.asarray(x, dtype=bool) for x in (twin, name_match, text_derived))
    primary = np.where(twin, U, np.where(nm | tx, MOD, NOV)).astype(object)
    twin_only = np.where(twin, U, NOV).astype(object)
    return primary, twin_only


def subset_masks(class_primary, class_twin_only) -> dict:
    cp, ct = np.asarray(class_primary, dtype=object), np.asarray(class_twin_only, dtype=object)
    return {"all": np.ones(len(cp), dtype=bool), U: cp == U, MOD: cp == MOD, NOV: cp == NOV,
            "common_denominator": (cp == U) | (cp == MOD), "novel_twin_only": ct == NOV}


def subset_survival(found, mask):
    """found[mask].sum() / mask.sum(); None for an empty subset."""
    mask = np.asarray(mask, dtype=bool)
    n = int(mask.sum())
    return None if n == 0 else float(np.asarray(found, dtype=bool)[mask].sum() / n)


def to_date(d) -> date:
    return d if isinstance(d, date) else date.fromisoformat(str(d)[:10])


def filter_date(pin_name: str, pin_rows: dict) -> date:
    if pin_name in FILTER_DATE_OVERRIDE:
        return FILTER_DATE_OVERRIDE[pin_name]
    return to_date(pin_rows[pin_name]["commit_date"])


def after_filter(snap_date, ref_date) -> bool:
    """Strictly after the progenitor's date."""
    return to_date(snap_date) > to_date(ref_date)


def usable(eligible: int, snap_date, ref_date, nonempty: bool = True) -> bool:
    return bool(nonempty and eligible >= MIN_POWER and after_filter(snap_date, ref_date))


def add_usable_flags(rows: list[dict], group=("port", "ref_name")) -> list[dict]:
    """usable_rank / is_first_usable / is_second_usable / in_first_three and median3_* columns, in place.
    Rows are expected to be the usable (kept) rows only; the rank is by (date, sha) over each group's distinct shas."""
    groups: dict = {}
    for r in rows:
        groups.setdefault(tuple(r[g] for g in group), []).append(r)
    for rs in groups.values():
        order = sorted({(str(r["date"]), r["sha"]) for r in rs})
        rank = {k: i + 1 for i, k in enumerate(order)}
        for r in rs:
            k = rank[(str(r["date"]), r["sha"])]
            r["usable_rank"] = k
            r["is_first_usable"] = int(k == 1)
            r["is_second_usable"] = int(k == 2)
            r["in_first_three"] = int(k <= 3)
            r["second_usable"] = r["is_second_usable"]      # names the analysis script reads
            r["first3_median_flag"] = r["in_first_three"]
        for col, src in (("median3_surv_names", "surv_names"),
                         ("median3_surv_struct_persnap_either", "surv_struct_persnap_either"),
                         ("median3_surv_struct_pooled_either", "surv_struct_pooled_either")):
            by_sub: dict = {}
            for r in rs:
                if r["usable_rank"] <= 3 and r.get(src) not in (None, ""):
                    by_sub.setdefault(r["subset"], []).append(float(r[src]))
            for r in rs:
                v = by_sub.get(r["subset"])
                r[col] = statistics.median(v) if (r["usable_rank"] <= 3 and v) else ""
    return rows


def descendants(basis_rows: list[dict], port: str) -> set:
    """Declared descendants of ``port`` in the lineage basis (rows excluded/dropped ignored)."""
    parent = {r["name"]: r["parent"] for r in basis_rows if r["basis"] not in ("excluded", "dropped")}

    def anc(x):
        out = []
        while x in parent:
            x = parent[x]
            out.append(x)
        return out

    return {c for c in parent if port in anc(c)}


def candidate_pool(cands: list[dict], origin, exclude_repos) -> list[dict]:
    """One snapshot per distinct repository: the latest with date strictly before ``origin``; ``exclude_repos`` dropped.
    Ties on date are broken by sha so the pick is deterministic."""
    origin = to_date(origin)
    best: dict = {}
    for c in cands:
        if c["repo"] in exclude_repos or not to_date(c["date"]) < origin:
            continue
        key = (to_date(c["date"]), c["sha"])
        if c["repo"] not in best or key > (to_date(best[c["repo"]]["date"]), best[c["repo"]]["sha"]):
            best[c["repo"]] = c
    return sorted(best.values(), key=lambda c: (c["repo"], c["sha"]))


def rank_of(values: dict, registered: str):
    """(rank, n_ties) of ``registered`` among {repo: value}: 1 + number of strictly greater values."""
    v = values[registered]
    greater = sum(1 for k, x in values.items() if k != registered and x > v)
    ties = sum(1 for k, x in values.items() if k != registered and x == v)
    return greater + 1, ties


def extend_family(fam_all: dict, ext=EXT_FAMILY, prog_ports: dict | None = None) -> dict:
    """Decoy-pool family sets: ``ext`` added to every family; each progenitor label (key of ``prog_ports``) gets
    {label} + ext + the families of the ports that use it. Returns a new dict."""
    out = {k: set(v) | set(ext) for k, v in fam_all.items()}
    for label, ports in (prog_ports or {}).items():
        s = {label} | set(ext)
        for p in ports:
            s |= set(fam_all.get(p, {p})) | {p}
        out[label] = s
    return out


def decompose(Rt: FunctionTable, Lt: FunctionTable, stop, verdicts=None, params=None):
    """Decomposition of R's eligible functions (loc >= 6) against L. ``verdicts`` = arbiter verdicts of R's eligible
    functions against all of L's functions (None: text channel off). Returns a dict of arrays over R's eligible order."""
    params = params or M.PARAMS
    em = M.elig_mask(Rt)
    n = int(em.sum())
    f = T.find_twins(Rt, Lt, params)
    b = T.find_twins(Lt, Rt, params)
    twin = M.twin_found_mask(Rt, f, b)
    pos = np.cumsum(em) - 1
    ld_row = np.full(n, -1, dtype=np.int64)
    ld_row[pos[b.t_index]] = b.q_index  # back direction first, forward overrides (query side is R)
    ld_row[pos[f.q_index]] = f.t_index
    lkeys = N.key_counts([str(x) for x in Lt.name[M.elig_mask(Lt)]], N.name_key, stop)
    keys = [N.name_key(str(x)) for x in Rt.name[em]]
    name_match = np.array([k is not None and k not in stop and k in lkeys for k in keys], dtype=bool)
    if verdicts is None:
        verdicts = ["" for _ in range(n)]
    verdicts = np.array(list(verdicts), dtype=object)
    assert len(verdicts) == n, (len(verdicts), n)
    text = np.array([v in VERDICTS_DERIVED for v in verdicts], dtype=bool)
    cp, ct = classify(twin, name_match, text)
    # linuxdoom-side common set: linuxdoom functions that twin an R function, or share an E7 name key with an R function
    # classified modified by name (text-only modified functions have no linuxdoom function recorded)
    lem = M.elig_mask(Lt)
    lpos = np.cumsum(lem) - 1
    ld_common = np.zeros(int(lem.sum()), dtype=bool)
    ld_common[lpos[ld_row[ld_row >= 0]]] = True
    mk = {k for k, c, nm in zip(keys, cp, name_match, strict=True) if c == MOD and nm and k is not None}
    ld_common |= np.array([N.name_key(str(x)) in mk for x in Lt.name[lem]], dtype=bool)
    return dict(ld_common=ld_common, twin=twin, name_match=name_match, text=text, verdict=verdicts, class_primary=cp, class_twin_only=ct,
                ld_row=ld_row, n=n)


def check_decomposition(d: dict) -> list[str]:
    """Self-consistency problems of one decomposition (empty list = consistent)."""
    bad = []
    cp, ct, tw = np.asarray(d["class_primary"], dtype=object), np.asarray(d["class_twin_only"], dtype=object), d["twin"]
    n = d["n"]
    if not (len(cp) == len(ct) == len(tw) == n):
        bad.append("length mismatch")
    if not np.isin(cp, [U, MOD, NOV]).all() or not np.isin(ct, [U, NOV]).all():
        bad.append("unknown class label")
    if ((cp == U) != tw).any() or ((ct == U) != tw).any():
        bad.append("unchanged_inherited differs from twin set")
    if ((cp == MOD) & (ct != NOV)).any():
        bad.append("modified under primary but not novel under twin_only")
    if ((cp == MOD) & ~(d["name_match"] | d["text"])).any() or ((cp == NOV) & (d["name_match"] | d["text"])).any():
        bad.append("modified/novel inconsistent with name/text evidence")
    if (cp == U).sum() + (cp == MOD).sum() + (cp == NOV).sum() != n:
        bad.append("classes do not partition")
    if ((d["ld_row"] >= 0) != tw).any():
        bad.append("ld_row set differs from twin set")
    return bad


# ---------------------------------------------------------------- context

class Ctx8b(M.Ctx):
    """E8's context plus: E8 fingerprint/search caches as read-only fallbacks, ref registry, extended decoy families."""

    def __init__(self, results: Path, ports_extra=()):
        super().__init__(results, ports_extra)
        self.e8_fp = HL / "results" / "fingerprints"
        self.e8_cache = HL / "results" / "cache"
        self.labels = {"R1": "linuxdoom", "R0": "nginx"}
        self.fam_all = extend_family(self.fam_all)

    def fingerprint(self, db, label, sub=""):
        if not sub:
            own = self.fp_dir / f"{E.N_safe(label)}.sfp.json"
            if not own.exists():
                old = self.e8_fp / f"{E.N_safe(label)}.sfp.json"
                if old.exists():
                    fp = M.Fingerprint.load(old)
                    if fp.spec_hash != self.spec:
                        raise RuntimeError(f"{label}: spec hash {fp.spec_hash} != {self.spec}")
                    return fp.functions
        return super().fingerprint(db, label, sub)

    def add_ref(self, label: str, key: str, table: FunctionTable, family_ports=()):
        self.tables[key] = table
        self.labels[key] = label
        self.fam_all[label] = extend_family(self.fam_all, EXT_FAMILY, {label: list(family_ports)})[label]


def get_searches(ctx: Ctx8b, tag: str, key: str, tab: FunctionTable, fresh: bool = False):
    """(fwd, back) twin searches of reference ``key`` against snapshot ``tag``: own cache; for linuxdoom (R1) E8's cache
    is a read-only fallback unless ``fresh``; else computed and cached."""
    R = ctx.tables[key]
    pf, pb = ctx.cache / "search" / f"{tag}__{key}__fwd.npz", ctx.cache / "search" / f"{tag}__{key}__back.npz"
    if pf.exists() and pb.exists():
        return M.load_search(pf, R, tab), M.load_search(pb, tab, R)
    if key == "R1" and not fresh:
        ef, eb = ctx.e8_cache / "search" / pf.name, ctx.e8_cache / "search" / pb.name
        if ef.exists() and eb.exists():
            return M.load_search(ef, R, tab), M.load_search(eb, tab, R)
    fwd, back = T.search(R, tab, M.PARAMS), T.search(tab, R, M.PARAMS)
    M.save_search(pf, fwd)
    M.save_search(pb, back)
    return fwd, back


def names_measures(ctx: Ctx8b, key: str, tag: str, port: str, tab: FunctionTable, cache_path: Path | None):
    if cache_path and cache_path.exists():
        return json.loads(cache_path.read_text())
    R, rl = ctx.tables[key], ctx.labels[key]
    f = ctx.names_pair(rl, R, rl, tag, tab, port)
    b = ctx.names_pair(tag, tab, port, rl, R, rl)
    nR = int(M.elig_mask(R).sum())
    out = dict(surv_names=f["matched"] / nR if nR else 0.0, names_certified=int(f["certified"]),
               shared_names=max(f["wilson_cert"], b["wilson_cert"]), pool_status=f["pool_status"])
    if cache_path:
        cache_path.write_text(json.dumps(out))
    return out


def twin_pairs(R: FunctionTable, tab: FunctionTable, fs, bs, thr=None):
    """Accepted twin pairs (reference eligible position, snapshot eligible position), both directions, deduplicated."""
    tf, tb = T.accept(fs, None if thr is None else thr[0]), T.accept(bs, None if thr is None else thr[1])
    pr, pp = np.cumsum(M.elig_mask(R)) - 1, np.cumsum(M.elig_mask(tab)) - 1
    r = np.concatenate([pr[tf.q_index], pr[tb.t_index]])
    p = np.concatenate([pp[tf.t_index], pp[tb.q_index]])
    if len(r) == 0:
        return r.astype(np.int64), p.astype(np.int64)
    u = np.unique(np.stack([r, p], axis=1), axis=0)
    return u[:, 0].astype(np.int64), u[:, 1].astype(np.int64)


def snap_meta(tab: FunctionTable):
    em = M.elig_mask(tab)
    c, cpp, oth = M.lang_shares(tab.language, tab.loc)
    return dict(eligible_snapshot=int(em.sum()), dup_share=round(M.dup_share(tab.key, tab.loc), 6),
                lang_c=round(c, 6), lang_cpp=round(cpp, 6), lang_other=round(oth, 6))


def measure_ref_port(ctx: Ctx8b, key: str, port: str, snaps: list[dict], tabs: dict, pool_tags=None, fresh=False,
                     with_ld=False, found_dir: Path | None = None, ld_key: str = "R1"):
    """Per-snapshot measures of reference ``key`` in each snapshot of ``port``. ``snaps``: dicts with tag. Pooled
    thresholds over ``pool_tags`` (default: all given snaps). Returns {tag: result}."""
    S = {s["tag"]: get_searches(ctx, s["tag"], key, tabs[s["tag"]], fresh) for s in snaps}
    pool = sorted(set(pool_tags) if pool_tags is not None else S)
    pool_S = {t: S[t] if t in S else get_searches(ctx, t, key, tabs[t]) for t in pool}
    pl = M.pooled_thresholds([pool_S[t][0] for t in pool], [pool_S[t][1] for t in pool], M.PARAMS.fdr) if pool else None
    R = ctx.tables[key]
    em = M.elig_mask
    out = {}
    for s in snaps:
        tg, tab = s["tag"], tabs[s["tag"]]
        fs, bs = S[tg]
        per = M.struct_measures(ctx, key, fs, bs)
        pp = M.struct_measures(ctx, key, fs, bs, pl) if (pl and tg in pool) else None
        nm = names_measures(ctx, key, tg, port, tab, ctx.cache / "names" / f"{tg}__{key}__{safe(port)}.json")
        fnames = M.name_found_mask(R.name[em(R)], tab.name[em(tab)], ctx.stop)
        res = dict(per=per, pp=pp, nm=nm, found_names=fnames, found_persnap=per["found"],
                   found_pooled=pp["found"] if pp else None, meta=snap_meta(tab))
        pr, pp_ = twin_pairs(R, tab, fs, bs)
        res["pairs"] = (pr, pp_)
        res["n_P_elig"] = int(em(tab).sum())
        if with_ld:
            fl, bl = get_searches(ctx, tg, ld_key, tab)
            res["ld_pairs"] = twin_pairs(ctx.tables[ld_key], tab, fl, bl)
        if found_dir is not None:
            arr = dict(found_names=fnames, found_struct_persnap=per["found"],
                       found_struct_pooled=pp["found"] if pp else np.zeros(per["nR"], dtype=bool),
                       pooled_available=np.array(bool(pp)), pairs_r=pr, pairs_p=pp_,
                       p_n_elig=np.array(int(em(tab).sum())))
            if with_ld:
                arr.update(ld_pairs_r=res["ld_pairs"][0], ld_pairs_p=res["ld_pairs"][1])
            found_dir.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(found_dir / f"{tg}__{key}__{safe(port)}.npz", **arr)
        out[tg] = res
    return out


def fnum(x):
    return "" if x is None else x


# ---------------------------------------------------------------- inputs

def read_csv(p):
    return list(csv.DictReader(open(p)))


def write(path: Path, cols, rows):
    M.write(path, cols, rows)


def load_pins() -> dict:
    return {r["name"]: r for r in read_csv(PINS_CSV)}


def pin_tag(r) -> str:
    return e8_snap.tag(r["sha"], r["scope_key"])


def pin_dir(r) -> Path:
    return PROG_SNAPS / pin_tag(r)


def prog_family_ports(pins) -> dict:
    """pin name -> ports that use it (primary, secondary, descriptive and wrong-progenitor roles)."""
    fp: dict = {n: set() for n in pins}
    for m in PRIMARY_MAP:
        for n in [m["primary"], *m["secondary"], *m["descriptive"]]:
            fp[n].add(m["port"])
    for port, w in WRONG.items():
        fp[w].add(port)
    for n in pins:
        repo = repo_of(n)
        fp[n].add(repo)
    return fp


def register_progenitors(ctx: Ctx8b, pins: dict):
    """Fingerprint and register every progenitor as reference key safe(pin). Returns {pin: dict(table, key, row)}."""
    fam = prog_family_ports(pins)
    out = {}
    for n, r in pins.items():
        d = pin_dir(r)
        if not M.finished(d):
            raise SystemExit(f"progenitor scan {n} not finished: {d}")
        tab = ctx.fingerprint(M.snap_db(d), n)
        key = safe(n)
        ctx.add_ref(n, key, tab, fam[n])
        out[n] = dict(table=tab, key=key, row=r, dir=d)
    return out


_LD = {}


def ld_all_funcs():
    """linuxdoom: every function (arbiter 'port' side) and the eligible list."""
    if "funcs" not in _LD:
        db = A.scan_db(WORK, E.ENGINE, "linuxdoom")
        sc = A.load_scan_data(db)
        _LD["funcs"] = A.build_funcs(sc, WORK / "repos" / "linuxdoom", db)
    return _LD["funcs"]


def eligible_funcs(snapdir: Path, table: FunctionTable):
    """Arbiter Func list of a scan's eligible functions, checked to align with the fingerprint's eligible rows."""
    db = M.snap_db(snapdir)
    sc = A.load_scan_data(db)
    elig = np.flatnonzero(A.eligible_mask(sc))
    funcs = A.build_funcs(sc, (snapdir / "_export").resolve(), db, elig)
    names = table.name[M.elig_mask(table)]
    if len(funcs) != len(names) or any(f.name != str(x) for f, x in zip(funcs, names, strict=True)):
        raise RuntimeError(f"arbiter/fingerprint eligible functions differ for {snapdir}")
    return funcs


def arbiter_rows(ctx: Ctx8b, cache_key: str, ref_funcs, port_funcs):
    p = ctx.cache / "text" / f"arb__{safe(cache_key)}.json"
    if p.exists():
        return json.loads(p.read_text())
    rows = A.run_port(ref_funcs, port_funcs)
    p.write_text(json.dumps(rows))
    return rows


# ---------------------------------------------------------------- decomposition

def run_decomposition(ctx: Ctx8b, progs: dict, results: Path, use_text=True):
    L = ctx.tables["R1"]
    summ, rows = [], []
    decomp = {}
    (results / "decomp").mkdir(exist_ok=True)
    for n, pr in progs.items():
        t = time.time()
        verdicts = None
        if use_text:
            rr = arbiter_rows(ctx, f"{n}__linuxdoom", eligible_funcs(pr["dir"], pr["table"]), ld_all_funcs())
            verdicts = [r["verdict"] for r in rr]
        d = decompose(pr["table"], L, ctx.stop, verdicts)
        bad = check_decomposition(d)
        if bad:
            raise RuntimeError(f"decomposition of {n} inconsistent: {bad}")
        decomp[n] = d
        tb = pr["table"]
        em = M.elig_mask(tb)
        names, paths, locs = tb.name[em], tb.path[em], tb.loc[em]
        for i in range(d["n"]):
            rows.append(dict(pin=n, func_index=i, name=names[i], path=paths[i], loc=int(locs[i]),
                             class_primary=d["class_primary"][i], class_twin_only=d["class_twin_only"][i],
                             twin=int(d["twin"][i]), name_key_match=int(d["name_match"][i]),
                             text_verdict=d["verdict"][i], ld_row=int(d["ld_row"][i])))
        np.savez_compressed(results / "decomp" / f"{safe(n)}.npz", ld_row=d["ld_row"], twin=d["twin"],
                            name_match=d["name_match"], text=d["text"], class_primary=d["class_primary"].astype(str),
                            class_twin_only=d["class_twin_only"].astype(str))
        cp, ct = d["class_primary"], d["class_twin_only"]
        n_el = d["n"]
        s = dict(pin=n, eligible=n_el, unchanged_inherited=int((cp == U).sum()), modified_inherited=int((cp == MOD).sum()),
                 novel=int((cp == NOV).sum()), twin_only_unchanged=int((ct == U).sum()), twin_only_novel=int((ct == NOV).sum()),
                 modified_by_name_only=int(((cp == MOD) & d["name_match"] & ~d["text"]).sum()),
                 modified_by_text_only=int(((cp == MOD) & ~d["name_match"] & d["text"]).sum()),
                 modified_by_both=int(((cp == MOD) & d["name_match"] & d["text"]).sum()), text_channel=int(use_text))
        for k in ("unchanged_inherited", "modified_inherited", "novel", "twin_only_novel"):
            s[f"share_{k}"] = round(s[k] / n_el, 4) if n_el else ""
        summ.append(s)
        print(f"  decomposition {n}: {n_el} eligible, U {s['unchanged_inherited']} M {s['modified_inherited']} "
              f"N {s['novel']} (twin_only novel {s['twin_only_novel']}), {time.time() - t:.0f}s", flush=True)
    write(results / "decomposition.csv", DECOMP_COLS, rows)
    write(results / "decomposition_summary.csv", list(summ[0]), summ)
    return decomp, summ


# ---------------------------------------------------------------- E8 reproduction (reference = linuxdoom)

VALIDATE_PORTS = ("chocolate-doom", "prboom-plus", "doomretro")


def e8_pool_tags(ctx: Ctx8b, rows, port):
    """E8's pooled-threshold set: distinct finished, fingerprintable calendar + commit-count snapshots of the port."""
    tags, tabs = [], {}
    for r in rows:
        if r["port"] != port or r["plan_kind"] not in ("calendar", "commitcount") or r["tag"] in tabs:
            continue
        d = HL / "snaps" / r["tag"]
        if not M.finished(d):
            continue
        try:
            tabs[r["tag"]] = ctx.fingerprint(M.snap_db(d), r["tag"])
        except Exception:  # noqa: BLE001
            continue
        if int(M.elig_mask(tabs[r["tag"]]).sum()) == 0:  # E8's search fails on an empty table: not in its pool
            tabs.pop(r["tag"])
            continue
        tags.append(r["tag"])
    return sorted(set(tags)), tabs


def validate_e8(ctx: Ctx8b, results: Path, per_port=2, tol=0.01, ports=VALIDATE_PORTS):
    """Reproduce E8's R1 values with the generalised pipeline (fresh searches for the checked snapshots)."""
    rows, _, _, _, _ = M.load_plan()
    for r in rows:
        r["tag"] = M.tag_of(r["sha"], r["scope_key"])
    e8 = {}
    for r in read_csv(HL / "results" / "snapshots.csv"):
        if r["ref"] == "R1":
            e8[(r["port"], r["sha"])] = r
    out = []
    for port in ports:
        pool, tabs = e8_pool_tags(ctx, rows, port)
        cal = {}
        for r in rows:
            if r["port"] == port and r["plan_kind"] == "calendar" and r["tag"] in tabs and (port, r["sha"]) in e8:
                cal.setdefault(r["sha"], r)
        if not cal:
            continue
        ordered = sorted(cal.values(), key=lambda r: (r["date"], r["sha"]))
        ordered = [r for r in ordered if int(M.elig_mask(tabs[r["tag"]]).sum()) >= 1]
        pick = list({r["sha"]: r for r in ordered[:1] + ordered[len(ordered) // 2: len(ordered) // 2 + max(per_port - 1, 0)]}.values())
        # fresh searches for the picked snapshots; the rest of the pool comes from E8's cache (same computation)
        snaps = [dict(tag=r["tag"], sha=r["sha"], date=r["date"]) for r in pick]
        res = measure_ref_port(ctx, "R1", port, snaps, tabs, pool_tags=pool, fresh=True)
        for r in pick:
            m = res[r["tag"]]
            ref_row = e8[(port, r["sha"])]
            nR = m["per"]["nR"]
            mine = dict(surv_names=m["nm"]["surv_names"], surv_struct_persnap_either=m["per"]["either"] / nR,
                        surv_struct_pooled_either=(m["pp"]["either"] / nR) if m["pp"] else "")
            row = dict(port=port, sha=r["sha"], date=r["date"], tag=r["tag"])
            ok = True
            for k, v in mine.items():
                e8v = ref_row[k]
                row[f"{k}_e8b"], row[f"{k}_e8"] = v, e8v
                if v == "" and e8v == "":
                    row[f"{k}_diff"] = 0.0
                elif v == "" or e8v == "":
                    row[f"{k}_diff"], ok = "mismatch", False
                else:
                    row[f"{k}_diff"] = abs(float(v) - float(e8v))
                    ok = ok and row[f"{k}_diff"] <= tol
            row["within_tol"] = int(ok)
            out.append(row)
    cols = list(out[0]) if out else ["port"]
    write(results / "validation.csv", cols, out)
    return out


# ---------------------------------------------------------------- snapshot sets

def port_snapshots(rows, port, kinds=("calendar",)):
    """Distinct-sha plan rows of a port for the given plan kinds, E8 tag (same scope as E8), in date order."""
    seen = {}
    for r in rows:
        if r["port"] == port and r["plan_kind"] in kinds:
            seen.setdefault(r["sha"], r)
    return sorted(seen.values(), key=lambda r: (r["date"], r["sha"]))


def load_snap_tables(ctx: Ctx8b, snaps, errors, label="snapshot"):
    """Fingerprint tables of finished scans; empty/failed scans are recorded and dropped."""
    tabs, ok = {}, []
    for r in snaps:
        d = HL / "snaps" / r["tag"]
        if r["tag"] in tabs:
            ok.append(r)
            continue
        if not M.finished(d):
            continue
        try:
            tabs[r["tag"]] = ctx.fingerprint(M.snap_db(d), r["tag"])
            ok.append(r)
        except Exception as e:  # noqa: BLE001
            errors.append(dict(tag=r["tag"], where=f"fingerprint ({label})", error=repr(e)[:300]))
    return tabs, ok


def make_rows(ctx, port, ref_name, kind_cols, snaps, res, cls, origin, ref_date, subsets=SUBSETS, ld_by_tag=None):
    """Expand per-snapshot results into subset rows."""
    out = []
    masks = subset_masks(cls["class_primary"], cls["class_twin_only"]) if cls else {"all": None}
    for s in snaps:
        m = res[s["tag"]]
        nR = m["per"]["nR"]
        for sub in subsets:
            if sub not in masks:
                continue
            mk = masks[sub] if masks[sub] is not None else np.ones(nR, dtype=bool)
            row = dict(kind_cols)
            row.update(port=port, ref_name=ref_name, subset=sub, plan_kind=s["plan_kind"], sha=s["sha"], date=s["date"],
                       age_port_years=round((to_date(s["date"]) - origin).days / 365.25, 4) if origin else "",
                       age_years=round((to_date(s["date"]) - ref_date).days / 365.25, 4),  # since the progenitor (analysis: >0)
                       n_subset=int(mk.sum()), n_ref_eligible=nR, underpowered=int(m["meta"]["eligible_snapshot"] < MIN_POWER),
                       surv_names=fnum(subset_survival(m["found_names"], mk)),
                       surv_struct_persnap_either=fnum(subset_survival(m["found_persnap"], mk)),
                       surv_struct_pooled_either=fnum(subset_survival(m["found_pooled"], mk)) if m["found_pooled"] is not None else "",
                       shared_struct_persnap=m["per"]["shared"], shared_names=m["nm"]["shared_names"],
                       names_certified=m["nm"]["names_certified"], tag=s["tag"], **m["meta"])
            ld = (ld_by_tag or {}).get(s["tag"])
            if ld is not None and sub in ("all", "common_denominator") and (sub == "all" or cls):
                lm = np.ones(len(ld["names"]), dtype=bool) if sub == "all" else cls["ld_common"]
                row["surv_names_ld"] = fnum(subset_survival(ld["names"], lm))
                row["surv_struct_persnap_either_ld"] = fnum(subset_survival(ld["persnap"], lm))
                row["surv_struct_pooled_either_ld"] = fnum(subset_survival(ld["pooled"], lm)) if ld["pooled"] is not None else ""
            row["surv_struct"] = row["surv_struct_persnap_either"]
            out.append(row)
    return out


def load_ld_arrays(tag, port):
    """E8's own linuxdoom found arrays for this snapshot (copied through, never recomputed)."""
    p = HL / "results" / "found" / f"{tag}__R1.npz"
    if not p.exists():
        return None
    with np.load(p) as z:
        pk = f"found_struct_pooled__{port}"
        return dict(names=z["found_names"], persnap=z["found_struct_persnap"], pooled=z[pk] if pk in z.files else None)


def dedup_table(tab: FunctionTable) -> FunctionTable:
    """One representative (first in table order) per exact-digest group among the eligible functions (loc >= 6);
    functions below the eligibility floor are kept untouched. Amendment 1 G.12."""
    em = M.elig_mask(tab)
    keep = np.ones(len(tab), dtype=bool)
    _, first = np.unique(tab.key[em], return_index=True)
    ei = np.flatnonzero(em)
    keep[ei] = False
    keep[ei[first]] = True
    return FunctionTable(repo=tab.repo, name=tab.name[keep], path=tab.path[keep], language=tab.language[keep], loc=tab.loc[keep],
              archetype=tab.archetype[keep], key=tab.key[keep], vectors=tab.vectors[keep], edges=None)


def dedup_survival(ctx, key, port, snaps, tabs):
    """{tag: (surv_names, surv_struct_persnap_either)} with both sides de-duplicated (reference registered as key__dd)."""
    kd = key + "__dd"
    if kd not in ctx.tables:
        lab = ctx.labels[key] + "__dd"
        ctx.add_ref(lab, kd, dedup_table(ctx.tables[key]), [])
        ctx.fam_all[lab] = set(ctx.fam_all.get(ctx.labels[key], {ctx.labels[key]})) | {lab}
    out = {}
    for s in snaps:
        tg = s["tag"] + "__dd"
        tab = dedup_table(tabs[s["tag"]])
        fs, bs = get_searches(ctx, tg, kd, tab)
        per = M.struct_measures(ctx, kd, fs, bs)
        nm = names_measures(ctx, kd, tg, port, tab, ctx.cache / "names" / f"{tg}__{kd}__{safe(port)}.json")
        nR = per["nR"]
        out[s["tag"]] = (nm["surv_names"], per["either"] / nR if nR else None)
    return out


def write_paired_novel(found_dir: Path, sha: str, ref_name: str, res: dict, cls: dict, n_ld: int, n_R: int):
    """Files read by e8b_analyze: found/<sha12>__<ref_name>__paired.npz (p_in_R, p_in_LD over the port snapshot's eligible
    functions, n_R_eligible, n_LD_eligible) and __novel.npz (found_names, found_struct_persnap over R's novel subset)."""
    found_dir.mkdir(parents=True, exist_ok=True)
    nP = int(res["n_P_elig"])
    pr, pl = np.zeros(nP, dtype=bool), np.zeros(nP, dtype=bool)
    pr[res["pairs"][1]] = True
    pl[res["ld_pairs"][1]] = True
    base = found_dir / f"{sha[:12]}__{ref_name}__"
    np.savez_compressed(f"{base}paired.npz", p_in_R=pr, p_in_LD=pl, n_R_eligible=np.array(n_R), n_LD_eligible=np.array(n_ld))
    nv = subset_masks(cls["class_primary"], cls["class_twin_only"])[NOV]
    np.savez_compressed(f"{base}novel.npz", found_names=res["found_names"][nv], found_struct_persnap=res["found_persnap"][nv])


def ranking_wide(summary: list[dict]) -> list[dict]:
    """One row per port (ranking.csv as e8b_analyze reads it) from the per-(port, metric) summary rows."""
    by: dict = {}
    for r in summary:
        by.setdefault(r["port"], {})[r["metric"]] = r
    out = []
    for port, d in by.items():
        st, nm = d.get("shared_struct"), d.get("shared_names")
        ref = st or nm
        out.append(dict(port=port, ref_name=ref["registered"], K=ref["K"], one_over_K=ref["one_over_K"],
                        rank_struct=st["registered_rank"] if st else "", rank_names=nm["registered_rank"] if nm else "",
                        registered_shared_struct=st["registered_value"] if st else "",
                        registered_shared_names=nm["registered_value"] if nm else "",
                        top1_struct=st["top1"] if st else "", top1_struct_value=st["top1_value"] if st else "",
                        top1_names=nm["top1"] if nm else "", top1_names_value=nm["top1_value"] if nm else "",
                        linuxdoom_shared_struct=st["linuxdoom_value"] if st else "",
                        linuxdoom_shared_names=nm["linuxdoom_value"] if nm else "",
                        ties_struct=st["ties"] if st else "", ties_names=nm["ties"] if nm else "",
                        registered_is_repr=ref["registered_is_repr"]))
    return out


# ---------------------------------------------------------------- stages

def ref_rows(ctx, key, ref_kind, ref_name, port, cls_letter, keep, tabs, cls, origin, fd, results, ld_key="R1",
             ld_loader=None):
    """All snapshots_prog.csv rows of one (port, reference): survival + subsets + linuxdoom columns; for primary refs also
    the dedup columns and the paired/novel found files the analysis reads."""
    ld_loader = ld_loader or load_ld_arrays
    primary = ref_kind == "primary"
    res = measure_ref_port(ctx, key, port, keep, tabs, found_dir=results / "found", with_ld=primary, ld_key=ld_key)
    ldt = {s["tag"]: ld_loader(s["tag"], port) for s in keep}
    ldt = {k: v for k, v in ldt.items() if v is not None}
    rr = make_rows(ctx, port, ref_name, {"role": "lineage", "class": cls_letter, "ref": ref_kind}, keep, res, cls, origin, fd,
                   ld_by_tag=ldt)
    if primary:
        n_ld = int(M.elig_mask(ctx.tables[ld_key]).sum())
        dd_r = dedup_survival(ctx, key, port, keep, tabs)
        dd_l = dedup_survival(ctx, ld_key, port, keep, tabs)
        for r in rr:
            if r["subset"] == "all":
                r["surv_names_dedup"], r["surv_struct_persnap_either_dedup"] = (fnum(x) for x in dd_r[r["tag"]])
                r["surv_names_ld_dedup"], r["surv_struct_persnap_either_ld_dedup"] = (fnum(x) for x in dd_l[r["tag"]])
        for s_ in keep:
            write_paired_novel(results / "found", s_["sha"], ref_name, res[s_["tag"]], cls, n_ld, res[s_["tag"]]["per"]["nR"])
    return rr


def stage_main(ctx, progs, decomp, rows, origin, results, errors, pins):
    """snapshots_prog.csv; also returns the usable snapshot set per port for the controls."""
    out_rows, port_sets = [], {}
    for m in PRIMARY_MAP:
        port = m["port"]
        snaps_all = port_snapshots(rows, port)
        tabs, snaps_ok = load_snap_tables(ctx, snaps_all, errors)
        refs = [(m["primary"], "primary")] + [(x, "secondary") for x in m["secondary"]] + \
               [(x, "descriptive") for x in m["descriptive"]]
        for ref_name, ref_kind in refs:
            fd = filter_date(ref_name, pins)
            keep = [s for s in snaps_ok if usable(int(M.elig_mask(tabs[s["tag"]]).sum()), s["date"], fd)]
            if ref_kind == "primary":
                port_sets[port] = (keep, tabs)
            if not keep:
                print(f"  {port} <- {ref_name}: no usable snapshot", flush=True)
                continue
            rr = ref_rows(ctx, progs[ref_name]["key"], ref_kind, ref_name, port, m["cls"], keep, tabs, decomp[ref_name],
                          origin.get(port), fd, results)
            add_usable_flags(rr, ("port", "ref_name"))
            out_rows.extend(rr)
            print(f"  {port} <- {ref_name} ({ref_kind}): {len(keep)} usable snapshots", flush=True)
    write(results / "snapshots_prog.csv", SNAP_COLS, out_rows)
    return port_sets


def stage_controls(ctx, progs, decomp, rows, origin, results, errors, pins, port_sets):
    out = []
    # wrong progenitors on the port's primary snapshot set
    for port, wrong in WRONG.items():
        if port not in port_sets:
            continue
        keep, tabs = port_sets[port]
        if not keep:
            continue
        fd = filter_date(wrong, pins)
        res = measure_ref_port(ctx, progs[wrong]["key"], port, keep, tabs, found_dir=None)
        rr = make_rows(ctx, port, wrong, {"role": "", "class": "", "ref": ""}, keep, res, decomp[wrong], origin.get(port), fd,
                       subsets=("all", NOV, "novel_twin_only"))
        for r in rr:
            r["kind"] = "wrong_progenitor"
            r["after_ref_date"] = int(after_filter(r["date"], fd))
        out.extend(rr)
    # primary progenitors against the unrelated controls
    for port in UNRELATED:
        snaps_all = port_snapshots(rows, port)
        tabs, ok = load_snap_tables(ctx, snaps_all, errors, "control")
        ok = [s for s in ok if int(M.elig_mask(tabs[s["tag"]]).sum()) >= 1]
        if not ok:
            continue
        for pin in PRIMARY_PINS:
            fd = filter_date(pin, pins)
            res = measure_ref_port(ctx, progs[pin]["key"], port, ok, tabs)
            rr = make_rows(ctx, port, pin, {}, ok, res, None, origin.get(port), fd, subsets=("all",))
            for r in rr:
                r["kind"] = "unrelated"
                r["after_ref_date"] = int(after_filter(r["date"], fd))
            out.extend(rr)
    write(results / "controls_prog.csv", CONTROL_COLS, out)
    return out


def stage_classA(ctx, rows, tasks, grid, portinfo, results, errors):
    truth = {r["child"]: r for r in read_csv(E8_MAN / "e8_fork_truth.csv")}
    pg = {(r["child"], r["parent"], r["step"]): r for r in read_csv(HL / "results" / "pairs_grid.csv")}
    out = []
    for child, parent in CLASS_A:
        ft = truth[child]
        fork_sha = ft["fork_sha"]
        g0 = next(g for g in grid if g["child"] == child and g["step"] == "0")
        t = tasks.get((parent, g0["parent_sha"]))
        sk = t["scope_key"] if t else portinfo.get(parent, {}).get("scope_key", "")
        ptag = M.tag_of(g0["parent_sha"], sk)
        if g0["parent_sha"] != fork_sha or not M.finished(HL / "snaps" / ptag):
            errors.append(dict(tag=ptag, where=f"classA {child}", error="parent@fork scan missing or sha mismatch"))
            continue
        ptab = ctx.fingerprint(M.snap_db(HL / "snaps" / ptag), ptag)
        key = safe(f"fork_{child}")
        ctx.add_ref(f"{parent}@fork", key, ptab, [parent])
        snaps = []
        for g in grid:
            if g["child"] == child and int(g["step"]) >= 1:
                t = tasks.get((child, g["child_sha"]))
                sk = t["scope_key"] if t else portinfo.get(child, {}).get("scope_key", "")
                snaps.append(dict(tag=M.tag_of(g["child_sha"], sk), sha=g["child_sha"], date=g["child_date"], step=g["step"],
                                  kind="grid", plan_kind="grid_child"))
        have = {s["sha"] for s in snaps}
        for r in rows:
            if r["port"] == child and r["fraction"] in ("1", "1.0") and r["sha"] not in have \
                    and to_date(r["date"]) > to_date(ft["fork_date"]):
                snaps.append(dict(tag=r["tag"], sha=r["sha"], date=r["date"], step="head", kind="head", plan_kind=r["plan_kind"]))
        tabs, ok = load_snap_tables(ctx, snaps, errors, f"classA {child}")
        ok = [s for s in ok if int(M.elig_mask(tabs[s["tag"]]).sum()) >= 1]
        if not ok:
            continue
        res = measure_ref_port(ctx, key, child, ok, tabs)
        origin_c = to_date(ft["fork_date"])
        for s in ok:
            m = res[s["tag"]]
            nR = m["per"]["nR"]
            row = dict(child=child, parent=parent, step=s["step"], kind=s["kind"], date=s["date"], child_sha=s["sha"],
                       parent_fork_sha=fork_sha, same_language=ft["same_language"], n_ref_eligible=nR,
                       surv_struct_fork_persnap=m["per"]["either"] / nR if nR else "", surv_names_fork=m["nm"]["surv_names"],
                       shared_struct_persnap=m["per"]["shared"], shared_names=m["nm"]["shared_names"],
                       age_years=round((to_date(s["date"]) - origin_c).days / 365.25, 4), **m["meta"])
            gp = pg.get((child, parent, str(s["step"])))
            for k, v in (gp or {}).items():
                if k not in ("child", "parent", "step"):
                    row[f"contemp_{k}"] = v
            out.append(row)
    cols = CLASSA_COLS + [f"contemp_{c}" for c in ["target_date", "child_sha", "parent_sha", "identical_sha", "elig_child",
                                                  "elig_parent", "surv_struct_c2p", "surv_struct_p2c", "shared_struct_max",
                                                  "shared_struct_min", "surv_names_c2p", "surv_names_p2c", "shared_names_max",
                                                  "shared_names_min", "names_pool_status"]]
    write(results / "classA.csv", cols, out)
    return out


def stage_ranking(ctx, progs, rows, origin, results, errors, pins, port_sets):
    basis = read_csv(Path(E.REPO) / "manifest" / "declared_lineage_basis.csv")
    cands = [dict(repo=r["port"], tag=r["tag"], sha=r["sha"], date=r["date"], kind="e8_snapshot", pin=None) for r in rows]
    for n, pr in progs.items():
        cands.append(dict(repo=repo_of(n), tag=pin_tag(pr["row"]), sha=pr["row"]["sha"], date=str(filter_date(n, pins)),
                          kind="progenitor", pin=n))
    tabs_cache = {}

    def tab_of(c):
        if c["tag"] not in tabs_cache:
            if c["pin"]:
                tabs_cache[c["tag"]] = progs[c["pin"]]["table"]
            else:
                d = HL / "snaps" / c["tag"]
                tabs_cache[c["tag"]] = None
                if M.finished(d):
                    try:
                        tabs_cache[c["tag"]] = ctx.fingerprint(M.snap_db(d), c["tag"])
                    except Exception:  # noqa: BLE001
                        pass
        return tabs_cache[c["tag"]]

    def valid(c):
        t = tab_of(c)
        return t is not None and int(M.elig_mask(t).sum()) >= 1

    out, summary = [], []
    for m in PRIMARY_MAP:
        port = m["port"]
        keep, tabs = port_sets.get(port, ([], {}))
        if not keep:
            continue
        p = keep[0]  # earliest usable snapshot under the primary reference
        ptab = tabs[p["tag"]]
        org = origin[port]
        excl = {port} | descendants(basis, port)
        early = [c for c in cands if c["repo"] not in excl and to_date(c["date"]) < org and c["tag"] != p["tag"]]
        # latest *scanned* (valid) snapshot per repository: drop empty/failed scans before picking
        full = candidate_pool([c for c in early if valid(c)], org, excl)
        reg_repo = repo_of(m["primary"])
        reg = next(c for c in cands if c["pin"] == m["primary"])
        rep = next((c for c in full if c["repo"] == reg_repo), None)
        was_repr = bool(rep and rep["tag"] == reg["tag"])
        pool = [c for c in full if c["repo"] != reg_repo] + [reg]
        for metric in ("shared_struct", "shared_names"):
            vals, det = {}, {}

            def score(c):
                if c["pin"]:
                    key = progs[c["pin"]]["key"]
                else:
                    key = f"cand_{safe(c['tag'])}"
                    ctx.add_ref(c["tag"], key, tab_of(c), [c["repo"]])
                if metric == "shared_struct":
                    fs, bs = get_searches(ctx, p["tag"], key, ptab)
                    return M.struct_measures(ctx, key, fs, bs)["shared"]
                return names_measures(ctx, key, p["tag"], port, ptab,
                                      ctx.cache / "names" / f"{p['tag']}__{key}__{safe(port)}.json")["shared_names"]

            for c in pool:
                vals[c["repo"]] = score(c)
                det[c["repo"]] = c
            rk, ties = rank_of(vals, reg_repo)
            K = len(vals)
            for repo, v in sorted(vals.items(), key=lambda kv: -kv[1]):
                c = det[repo]
                r2, _ = rank_of(vals, repo)
                out.append(dict(port=port, metric=metric, port_tag=p["tag"], port_date=p["date"], origin_date=org,
                                candidate_repo=repo, candidate_tag=c["tag"], candidate_date=c["date"], candidate_kind=c["kind"],
                                candidate_eligible=int(M.elig_mask(tab_of(c)).sum()), value=v, rank=r2, K=K,
                                one_over_K=round(1 / K, 6), is_registered=int(repo == reg_repo), registered_rank=rk,
                                registered_is_repr=int(was_repr)))
            # linuxdoom for context only: never ranked, never counted in K
            fs, bs = get_searches(ctx, p["tag"], "R1", ptab)
            lv = (M.struct_measures(ctx, "R1", fs, bs)["shared"] if metric == "shared_struct" else
                  names_measures(ctx, "R1", p["tag"], port, ptab, ctx.cache / "names" / f"{p['tag']}__R1__{safe(port)}.json")["shared_names"])
            out.append(dict(port=port, metric=metric, port_tag=p["tag"], port_date=p["date"], origin_date=org,
                            candidate_repo="linuxdoom", candidate_tag="", candidate_date="", candidate_kind="reference_context",
                            candidate_eligible=int(M.elig_mask(ctx.tables["R1"]).sum()), value=lv, rank="", K=K,
                            one_over_K=round(1 / K, 6), is_registered=0, registered_rank=rk, registered_is_repr=int(was_repr)))
            top = max(vals.items(), key=lambda kv: kv[1])
            summary.append(dict(port=port, metric=metric, registered=m["primary"], registered_rank=rk, ties=ties, K=K,
                                one_over_K=round(1 / K, 6), top1=top[0], top1_value=top[1], registered_value=vals[reg_repo],
                                linuxdoom_value=lv, registered_is_repr=int(was_repr)))
    write(results / "ranking_candidates.csv", RANK_COLS, out)
    write(results / "ranking.csv", RANKW_COLS, ranking_wide(summary))  # one row per port, as e8b_analyze reads it
    if summary:
        write(results / "ranking_summary.csv", list(summary[0]), summary)
    return out


def stage_arbiter(ctx, progs, results, port_sets, errors):
    out = []

    def add(kind, port, ref_name, which, tag, dt, ref_funcs, port_funcs):
        ck = f"{port}__linuxdoom" if kind == "prog_vs_linuxdoom" else f"{kind}__{port}__{ref_name}__{tag}"  # shares the decomposition cache
        rr = arbiter_rows(ctx, ck, ref_funcs, port_funcs)
        s = A.summarise(port, rr)
        out.append(dict(kind=kind, port=port, ref_name=ref_name, which=which, tag=tag, date=dt, eligible_ref=s["eligible"],
                        exact=s["exact"], near=s["near"], derived=s["derived"], gone=s["gone"],
                        share_exact_near=s["share_exact_near"], share_exact_near_derived=s["share_exact_near_derived"]))

    for n, pr in progs.items():
        add("prog_vs_linuxdoom", n, "linuxdoom", "-", pin_tag(pr["row"]), pr["row"]["commit_date"],
            eligible_funcs(pr["dir"], pr["table"]), ld_all_funcs())
    rows, *_ = M.load_plan()
    for r in rows:
        r["tag"] = M.tag_of(r["sha"], r["scope_key"])
    for m in PRIMARY_MAP:
        keep, tabs = port_sets.get(m["port"], ([], {}))
        if not keep:
            continue
        pr = progs[m["primary"]]
        rf = eligible_funcs(pr["dir"], pr["table"])
        head = next((r for r in port_snapshots(rows, m["port"]) if r["fraction"] in ("1", "1.0")), None)
        picks = [("earliest", keep[0])] + ([("head", head)] if head else [])
        for which, s in picks:
            d = HL / "snaps" / s["tag"]
            if not M.finished(d):
                continue
            try:
                db = M.snap_db(d)
                pf = A.build_funcs(A.load_scan_data(db), (d / "_export").resolve(), db)
            except Exception as e:  # noqa: BLE001
                errors.append(dict(tag=s["tag"], where="arbiter", error=repr(e)[:300]))
                continue
            add("port_vs_prog", m["port"], m["primary"], which, s["tag"], s["date"], rf, pf)
    write(results / "arbiter_prog.csv", ARB_COLS, out)
    return out


# ---------------------------------------------------------------- driver

def run(a):
    results = Path(a.results)
    results.mkdir(parents=True, exist_ok=True)
    rows, origin, tasks, grid, portinfo = M.load_plan()
    for r in rows:
        r["tag"] = M.tag_of(r["sha"], r["scope_key"])
    ports_all = sorted({r["port"] for r in rows} | {repo_of(n) for n in load_pins()})
    ctx = Ctx8b(results, ports_all)
    pins = load_pins()
    errors = []
    t0 = time.time()
    progs = register_progenitors(ctx, pins)
    print(f"progenitors registered: {len(progs)}", flush=True)

    print("E8 reproduction (reference = linuxdoom):", flush=True)
    val = validate_e8(ctx, results)
    for v in val:
        print("  ", v["port"], v["sha"][:8], {k: (round(v[k], 4) if isinstance(v[k], float) else v[k]) for k in v
                                              if k.endswith("_diff")}, "OK" if v["within_tol"] else "FAIL", flush=True)
    bad_val = [v for v in val if not v["within_tol"]]
    if not a.only_validate and (bad_val or not val):
        print("E8 reproduction failed or empty: refusing to produce port-versus-progenitor outputs", flush=True)
        return 1
    print("decomposition of the progenitors against linuxdoom:", flush=True)
    decomp, summ = run_decomposition(ctx, progs, results, use_text=not a.no_text)
    if a.only_validate:
        print(f"validate-only done: {len(val)} checks ({len(bad_val)} failing), {len(summ)} progenitors, "
              f"{time.time() - t0:.0f}s", flush=True)
        return 1 if (bad_val or not val) else 0
    stages = set(a.stages.split(",")) if a.stages else {"main", "controls", "classA", "arbiter", "ranking"}
    port_sets = stage_main(ctx, progs, decomp, rows, origin, results, errors, pins)
    if "controls" in stages:
        stage_controls(ctx, progs, decomp, rows, origin, results, errors, pins, port_sets)
    if "classA" in stages:
        stage_classA(ctx, rows, tasks, grid, portinfo, results, errors)
    if "arbiter" in stages and not a.no_text:
        stage_arbiter(ctx, progs, results, port_sets, errors)
    if "ranking" in stages:  # LAST: the only place real port-vs-candidate numbers are produced
        stage_ranking(ctx, progs, rows, origin, results, errors, pins, port_sets)
    if errors:
        write(results / "errors.csv", ["tag", "where", "error"], errors)
    print(f"run done, {len(errors)} errors, {time.time() - t0:.0f}s", flush=True)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", choices=["run"])
    ap.add_argument("--only-validate", action="store_true")
    ap.add_argument("--results", default=str(R8B))
    ap.add_argument("--stages", help="comma list of main,controls,classA,arbiter,ranking (default all)")
    ap.add_argument("--no-text", action="store_true", help="skip the name-blind text arbiter (decomposition text channel off)")
    a = ap.parse_args(argv)
    try:
        return run(a)
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
