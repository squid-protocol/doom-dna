"""DOOM-E8 measurement: survival of a fixed reference in each half-life snapshot (E7 rules reused unchanged).

Computes NO trend, tau, fit, age-vs-survival or other inferential statistic: that belongs to the analysis script.

    python e8_measure.py run [--limit N] [--ports a,b] [--no-text] [--no-noise]
    python e8_measure.py status

Reads finished scans (``rc.txt == 0``) under ``<work>/halflife/snaps``; replicate scans under ``snaps_rep{1,2}``.
Writes under ``<work>/halflife/results``: snapshots.csv, found/*.npz, pairs_grid.csv, noise.csv, precondition.csv,
precondition_summary.csv, fingerprints/ (cache), cache/ (search, names and text-arbiter caches), errors.csv.

Incremental: a fingerprint, a twin search (per snapshot and reference), a names result and a text-arbiter result are each
cached on first computation and reused on every rerun; pooled thresholds and all output tables are rebuilt from the caches
(they depend on the set of finished snapshots).

Definitions fixed where the contract was open
* ``tag`` = sha[:12] + '__' + sha1(scope_key)[:6] (as e8_snap.py). One row per plan row (so tied fractions that collapse to
  one commit give identical rows; the analysis de-duplicates by sha).
* eligible = loc >= 6 (E7). n_ref_eligible = eligible functions of the reference (R1 linuxdoom: 689).
* language shares over eligible snapshot functions, from the fingerprint ``language`` column (engine strings, lower case):
  lang_c = 'c'; lang_cpp = 'cpp'; lang_other = everything else (objective-c, assembly, python, ...).
* dup_share = share of eligible functions whose exact measurement digest (``key``) occurs at least twice among the
  snapshot's eligible functions.
* age_years = (date - date of that port's f=0 row in e8_plan.csv) / 365.25 days.
* surv_names = E7 matched (stoplist) / n_ref_eligible, reference -> snapshot; surv_names_nostop without the stoplist;
  names_certified = E7 decoy test, direction reference -> snapshot; shared_names = max over both directions of the
  decoy-certified Wilson bound. Not zeroed when uncertified: the flag is reported beside it.
* structure: reference functions linked to a twin in the snapshot in EITHER direction (reference->snapshot hit, or
  snapshot->reference hit whose twin is that function), over n_ref_eligible; fwd = reference->snapshot only.
  persnap = per-snapshot FDR 0.01 threshold in each direction; pooled = ONE threshold per (port, reference, direction)
  over all distinct finished snapshots of that port in the calendar and commit-count plans (grid snapshots reuse their
  port's pooled threshold; blank when the port has none).
* shared_struct_* = max over directions of the Wilson bound of twins/eligible (E7 ``struct_pair`` rule).
* text_en / text_end: name-blind arbiter shares exact+near and exact+near+derived (reference = linuxdoom, 689 functions),
  filled for plan role ``lineage`` with ref R1 only.
* found/<tag>__R1.npz: found_names, found_struct_persnap, found_struct_pooled (primary port) plus
  found_struct_pooled__<port> for every port using that tag (the pooled threshold is port-specific), over the reference's
  eligible functions in E7 table row order. found_names: for each name key the first min(count_ref, count_snap) reference
  functions (row order) carrying it, so the sum equals the E7 matched count.
"""

from __future__ import annotations

import argparse
import collections
import csv
import glob
import hashlib
import json
import sys
import time
import traceback
from datetime import date
from pathlib import Path

import numpy as np

E7 = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/measure")
SFS = "/srv/storage_16tb/projects/structural-fingerprint-scanner/src"
for p in (str(E7), SFS):
    if p not in sys.path:
        sys.path.insert(0, p)

import e7_arbiter as A  # noqa: E402
import e7_names as N  # noqa: E402
import e7_run as E  # noqa: E402
from structural_fingerprint import twins as T  # noqa: E402
from structural_fingerprint.fingerprint import Fingerprint, FunctionTable, build  # noqa: E402
from structural_fingerprint.reference import load_reference  # noqa: E402
from structural_fingerprint.scan_io import load_scan  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
WORK = Path("/srv/storage_16tb/projects/doom-e7-work")
HL = WORK / "halflife"
E7_FP = WORK / "results" / "e7" / "phaseA" / "fingerprints"
E7_MANIFEST = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/manifest")
PARAMS = T.TwinParams(min_loc=E.ELIGIBLE_LOC)
MIN_POWER = E.MIN_POWER
REFS = {"R1": "linuxdoom", "R0": "nginx"}

SNAP_COLS = ["port", "role", "stratum", "plan_kind", "fraction", "sha", "date", "age_years", "ref", "n_ref_eligible",
             "eligible_snapshot", "dup_share", "lang_c", "lang_cpp", "lang_other", "ctags_functions", "pruned",
             "underpowered", "surv_names", "surv_names_nostop", "names_certified", "shared_names",
             "surv_struct_persnap_either", "surv_struct_persnap_fwd", "surv_struct_pooled_either",
             "shared_struct_persnap", "shared_struct_pooled", "text_en", "text_end"]
SELF_COLS = ["port", "sha0", "sha", "age_years", "n_s0_eligible", "surv_names_self",
             "surv_struct_self_persnap_either"]
GRID_COLS = ["child", "parent", "step", "target_date", "child_sha", "parent_sha", "identical_sha", "elig_child",
             "elig_parent", "surv_struct_c2p", "surv_struct_p2c", "shared_struct_max", "shared_struct_min",
             "surv_names_c2p", "surv_names_p2c", "shared_names_max", "shared_names_min", "names_pool_status"]


# ---------------------------------------------------------------- pure helpers (unit-tested)

def tag_of(sha: str, scope_key: str) -> str:
    return f"{sha[:12]}__{hashlib.sha1(scope_key.encode()).hexdigest()[:6]}"


def dup_share(key: np.ndarray, loc: np.ndarray, min_loc: int = E.ELIGIBLE_LOC) -> float:
    """Share of eligible functions (loc >= min_loc) whose exact-digest group has two or more eligible members."""
    k = np.asarray(key)[np.asarray(loc) >= min_loc]
    if len(k) == 0:
        return 0.0
    _, inv, cnt = np.unique(k, return_inverse=True, return_counts=True)
    return float((cnt[inv] >= 2).sum() / len(k))


def lang_shares(language: np.ndarray, loc: np.ndarray, min_loc: int = E.ELIGIBLE_LOC) -> tuple[float, float, float]:
    """(c, cpp, other) shares of eligible functions; engine language strings 'c' and 'cpp', everything else other."""
    lg = np.asarray(language)[np.asarray(loc) >= min_loc]
    n = len(lg)
    if n == 0:
        return 0.0, 0.0, 0.0
    c = float((lg == "c").sum() / n)
    cpp = float((lg == "cpp").sum() / n)
    return c, cpp, 1.0 - c - cpp


def elig_mask(table: FunctionTable) -> np.ndarray:
    return table.loc >= E.ELIGIBLE_LOC


def name_found_mask(ref_names, snap_names, stoplist) -> np.ndarray:
    """Per reference function (eligible rows given): True for the first min(count_ref, count_snap) functions of each
    stoplist-filtered name key, so that the sum equals the E7 matched count."""
    cs = N.key_counts([str(x) for x in snap_names], N.name_key, stoplist)
    used: collections.Counter = collections.Counter()
    out = np.zeros(len(ref_names), dtype=bool)
    for i, nm in enumerate(ref_names):
        k = N.name_key(str(nm))
        if k is None or k in stoplist:
            continue
        if used[k] < cs.get(k, 0):
            out[i] = True
            used[k] += 1
    return out


def twin_found_mask(ref_table: FunctionTable, fwd: T.TwinResult, back: T.TwinResult | None) -> np.ndarray:
    """Bool over the reference's eligible functions: has a twin (fwd: ref is query; back: ref is target)."""
    em = elig_mask(ref_table)
    pos = np.cumsum(em) - 1
    out = np.zeros(int(em.sum()), dtype=bool)
    out[pos[fwd.q_index]] = True
    if back is not None:
        out[pos[back.t_index]] = True
    return out


def pooled_thresholds(fwd_searches, back_searches, fdr: float):
    """One threshold per direction over all the searches of one (port, reference) (METHOD.md section 10)."""
    return T.pooled_threshold(list(fwd_searches), fdr)[0], T.pooled_threshold(list(back_searches), fdr)[0]


def self_survival(t0: FunctionTable, t: FunctionTable, stop, cache_path: Path | None = None):
    """Survival of t0's eligible functions in t: (names one-to-one with stoplist, twins in either direction at
    per-snapshot fdr 0.01), both divided by t0's eligible count. Registered estimand surv(s0 -> s), Amendment 1 D.16."""
    if cache_path is not None and cache_path.exists():
        return tuple(json.loads(cache_path.read_text()))
    em = elig_mask(t0)
    n0 = int(em.sum())
    if n0 == 0:
        return 0.0, 0.0
    cq = N.key_counts([str(x) for x in t0.name[em]], N.name_key, stop)
    ct = N.key_counts([str(x) for x in t.name[elig_mask(t)]], N.name_key, stop)
    names = min(1.0, N.matched(cq, ct) / n0)
    f = T.find_twins(t0, t, PARAMS)
    b = T.find_twins(t, t0, PARAMS)
    struct = int(twin_found_mask(t0, f, b).sum()) / n0
    if cache_path is not None:
        cache_path.write_text(json.dumps([names, struct]))
    return names, struct


def wilson(k: int, n: int) -> float:
    return float(E.wl_np(np.array([k]), np.array([max(n, 1)]))[0]) if n else 0.0


# ---------------------------------------------------------------- caches

def save_search(path: Path, s: T.TwinSearch):
    np.savez_compressed(path, qm=s.qm, tm=s.tm, d1=s.d1, i1=s.i1, t_pass=s.t_pass, e1=s.e1, e_pass=s.e_pass,
                        exact=s.exact, exact_t=s.exact_t)


def load_search(path: Path, q: FunctionTable, t: FunctionTable) -> T.TwinSearch:
    with np.load(path) as z:
        return T.TwinSearch(q, t, PARAMS, z["qm"], z["tm"], z["d1"], z["i1"], z["t_pass"], z["e1"], z["e_pass"],
                            z["exact"], z["exact_t"])


def snap_db(d: Path) -> Path | None:
    g = sorted(glob.glob(str(d / "*_galaxy_master.db")))
    return Path(g[0]) if g else None


def finished(d: Path) -> bool:
    rc = d / "rc.txt"
    return rc.exists() and rc.read_text().strip() == "0" and snap_db(d) is not None


# ---------------------------------------------------------------- context

class Ctx:
    def __init__(self, results: Path, ports_extra=()):
        self.results = results
        self.fp_dir = results / "fingerprints"
        self.cache = results / "cache"
        for d in (self.fp_dir, self.cache / "search", self.cache / "names", self.cache / "text", results / "found"):
            d.mkdir(parents=True, exist_ok=True)
        self.ref_model = load_reference("structure")
        self.tables = {}
        for r, nm in REFS.items():
            fp = Fingerprint.load(E_FP_path(nm))
            self.tables[r] = fp.functions
            self.spec = fp.spec_hash
        self.stop = frozenset(l.strip() for l in open(E7_MANIFEST / "name_stoplist.txt")
                              if l.strip() and not l.startswith("#"))
        progs = E.load_programs()
        self.map_names = [p["name"] for p in progs if p["role"] in E.MAP_ROLES and (E_FP_path(p["name"])).exists()]
        self.per = {}
        for n in self.map_names:
            self.per[n] = E.program_keys(Fingerprint.load(E_FP_path(n)).functions, self.stop)
        self.base_vocab = E.build_vocab(self.per)
        self.base_dense = {n: E.dense(self.per[n]["primary"], self.base_vocab) for n in self.map_names}
        self.base_total = np.sum(list(self.base_dense.values()), axis=0)
        self.df_generic = set(json.load(open(WORK / "results" / "e7" / "phaseA" / "generic_keys.json")))
        self.fam_all = E.declared_families(sorted(set(self.map_names) | set(ports_extra)))
        self._ref_funcs = None

    # --- fingerprints
    def fingerprint(self, db: Path, label: str, sub: str = "") -> FunctionTable:
        d = self.fp_dir / sub if sub else self.fp_dir
        p = d / f"{E.N_safe(label)}.sfp.json"
        if p.exists():
            fp = Fingerprint.load(p)
        else:
            fp = build(load_scan(db, self.ref_model.signal_columns, name=label), self.ref_model, min_loc=E.MIN_LOC_FP)
            fp.save(d)
        if fp.spec_hash != self.spec:
            raise RuntimeError(f"{label}: spec hash {fp.spec_hash} != {self.spec}")
        return fp.functions

    # --- names
    def names_pair(self, ql, qt, qport, tl, tt, tport):
        """E7 names result for ordered pair (q -> t); labels are program names (reference names or tags)."""
        extra = {}
        for lab, tab in ((ql, qt), (tl, tt)):
            if lab not in self.per:
                extra[lab] = E.program_keys(tab, self.stop)
        per = {**self.per, **extra}
        vocab = dict(self.base_vocab)
        for d in extra.values():
            for k in d["primary"]:
                vocab.setdefault(k, len(vocab))
        pad = len(vocab) - len(self.base_vocab)
        total = np.concatenate([self.base_total, np.zeros(pad, dtype=self.base_total.dtype)]) if pad else self.base_total
        dense_all = {n: (np.concatenate([v, np.zeros(pad, dtype=v.dtype)]) if pad else v)
                     for n, v in self.base_dense.items()}
        fam = dict(self.fam_all)
        for lab, port in ((ql, qport), (tl, tport)):
            if lab not in fam:
                fam[lab] = set(self.fam_all.get(port, {port})) | {port}
        res = E.run_names_pair(ql, tl, per, dense_all, total, fam, len(vocab), self.df_generic, vocab)
        excl = fam.get(ql, {ql}) | fam.get(tl, {tl}) | {ql, tl}
        pool = int(total.astype(np.int64).sum() - sum(int(dense_all[p].sum()) for p in excl if p in dense_all))
        res["pool_keys"] = pool
        res["pool_status"] = "ok" if (pool > 0 and res["matched"] > 0) else ("empty_pool" if pool <= 0 else "no_matches")
        return res

    # --- text arbiter
    def ref_funcs(self):
        if self._ref_funcs is None:
            db = A.scan_db(WORK, E.ENGINE, "linuxdoom")
            sc = A.load_scan_data(db)
            elig = np.flatnonzero(A.eligible_mask(sc))
            self._ref_funcs = A.build_funcs(sc, WORK / "repos" / "linuxdoom", db, elig)
            assert len(self._ref_funcs) == int(elig_mask(self.tables["R1"]).sum()), "arbiter reference differs from R1"
        return self._ref_funcs


def E_FP_path(name: str) -> Path:
    return E7_FP / f"{E.N_safe(name)}.sfp.json"


# ---------------------------------------------------------------- per (snapshot, ref) core

def get_searches(ctx: Ctx, tag: str, ref: str, tab: FunctionTable, cache=True):
    R = ctx.tables[ref]
    pf = ctx.cache / "search" / f"{tag}__{ref}__fwd.npz"
    pb = ctx.cache / "search" / f"{tag}__{ref}__back.npz"
    if cache and pf.exists() and pb.exists():
        return load_search(pf, R, tab), load_search(pb, tab, R)
    fwd = T.search(R, tab, PARAMS)
    back = T.search(tab, R, PARAMS)
    if cache:
        save_search(pf, fwd)
        save_search(pb, back)
    return fwd, back


def struct_measures(ctx: Ctx, ref: str, fwd_s, back_s, thr=None):
    """Twin results at per-snapshot thresholds (thr None) or given (fwd, back) thresholds; counts and found mask."""
    R = ctx.tables[ref]
    tf = T.accept(fwd_s, None if thr is None else thr[0])
    tb = T.accept(back_s, None if thr is None else thr[1])
    nR = int(elig_mask(R).sum())
    nS = tb.eligible
    found = twin_found_mask(R, tf, tb)
    found_fwd = twin_found_mask(R, tf, None)
    return dict(fwd=len(tf.q_index), back=len(tb.q_index), nR=nR, nS=nS, found=found,
                either=int(found.sum()), fwd_only=int(found_fwd.sum()),
                shared=max(wilson(len(tf.q_index), nR), wilson(len(tb.q_index), nS)),
                shared_min=min(wilson(len(tf.q_index), nR), wilson(len(tb.q_index), nS)))


def names_measures(ctx: Ctx, ref: str, tag: str, port: str, tab: FunctionTable, cache_path: Path | None):
    if cache_path and cache_path.exists():
        return json.loads(cache_path.read_text())
    R = ctx.tables[ref]
    rl = REFS[ref]
    f = ctx.names_pair(rl, R, rl, tag, tab, port)
    b = ctx.names_pair(tag, tab, port, rl, R, rl)
    nR = int(elig_mask(R).sum())
    out = dict(surv_names=f["matched"] / nR if nR else 0.0, surv_names_nostop=f["nostop_matched"] / nR if nR else 0.0,
               names_certified=int(f["certified"]), shared_names=max(f["wilson_cert"], b["wilson_cert"]),
               pool_status=f["pool_status"])
    if cache_path:
        cache_path.write_text(json.dumps(out))
    return out


def text_measures(ctx: Ctx, tag: str, snapdir: Path):
    p = ctx.cache / "text" / f"{tag}.json"
    if p.exists():
        return json.loads(p.read_text())
    db = snap_db(snapdir)
    ps = A.load_scan_data(db)
    funcs = A.build_funcs(ps, (snapdir / "_export").resolve(), db)
    rows = A.run_port(ctx.ref_funcs(), funcs)
    s = A.summarise(tag, rows)
    out = dict(text_en=s["share_exact_near"], text_end=s["share_exact_near_derived"])
    p.write_text(json.dumps(out))
    return out


# ---------------------------------------------------------------- plan reading

def read_csv(p):
    return list(csv.DictReader(open(p)))


def parse_date(s):
    return date.fromisoformat(s[:10])


def load_plan():
    man = REPO / "manifest"
    rows = []
    origin = {}
    for kind, f in (("calendar", "e8_plan.csv"), ("commitcount", "e8_plan_commitcount.csv")):
        for r in read_csv(man / f):
            r = dict(r, plan_kind=kind)
            rows.append(r)
            if kind == "calendar" and r["fraction"] in ("0", "0.0"):
                origin[r["port"]] = parse_date(r["date"])
    portinfo = {}
    for r in rows:
        portinfo.setdefault(r["port"], r)
    tasks = {(r["port"], r["sha"]): r for r in read_csv(man / "e8_tasks.csv")}
    grid = read_csv(man / "e8_grid_pairs.csv")
    for g in grid:
        for side, kind in (("child", "grid_child"), ("parent", "grid_parent")):
            port, sha = g[side], g[f"{side}_sha"]
            t = tasks.get((port, sha))
            sk = t["scope_key"] if t else portinfo.get(port, {}).get("scope_key", "")
            pi = portinfo.get(port, {})
            rows.append(dict(port=port, role=pi.get("role", ""), stratum=pi.get("stratum", ""), plan_kind=kind,
                             fraction="", sha=sha, date=g[f"{side}_date"], scope_key=sk))
    return rows, origin, tasks, grid, portinfo


# ---------------------------------------------------------------- driver

def run(a):
    results = Path(a.results)
    snaps = Path(a.work) / "halflife" / "snaps"
    rows, origin, tasks, grid, portinfo = load_plan()
    ports_all = sorted({r["port"] for r in rows})
    ctx = Ctx(results, ports_all)
    lineage_ports = {r["port"] for r in rows if r["role"] == "lineage"}
    errors = []
    failed = {}
    timing = []
    only = set(a.ports.split(",")) if a.ports else None

    for r in rows:
        r["tag"] = tag_of(r["sha"], r["scope_key"])
        r["dir"] = snaps / r["tag"]
        r["ok"] = finished(r["dir"])
    pending = sum(1 for r in rows if not r["ok"])
    sel = [r for r in rows if r["ok"] and (not only or r["port"] in only)]
    tags = {}
    for r in sel:
        tags.setdefault(r["tag"], r)
    if a.limit:
        keep = set(list(tags)[: a.limit])
        sel = [r for r in sel if r["tag"] in keep]
        tags = {t: v for t, v in tags.items() if t in keep}
    print(f"plan rows {len(rows)}, finished {len(rows) - pending}, selected {len(sel)} rows / {len(tags)} tags", flush=True)

    # fingerprints + searches per (tag, ref)
    tab, S = {}, {}
    refs_for = lambda port: ["R1"] + ([] if port == "nginx" else ["R0"])  # noqa: E731
    t_start = time.time()
    for i, (tg, r) in enumerate(tags.items()):
        t0 = time.time()
        try:
            tab[tg] = ctx.fingerprint(snap_db(r["dir"]), tg)
            need = {"R1"} | ({"R0"} if any(x["port"] != "nginx" for x in sel if x["tag"] == tg) else set())
            for ref in sorted(need):
                S[(tg, ref)] = get_searches(ctx, tg, ref, tab[tg])
        except Exception as e:  # noqa: BLE001
            errors.append(dict(tag=tg, where="fingerprint/search", error=repr(e)[:300]))
            traceback.print_exc()
            tab.pop(tg, None)
            failed[tg] = r
        timing.append(time.time() - t0)
        if (i + 1) % 10 == 0:
            print(f"  fingerprint+search {i + 1}/{len(tags)}, {time.time() - t_start:.0f}s", flush=True)
    sel = [r for r in sel if r["tag"] in tab]

    # pooled thresholds per (port, ref): distinct finished calendar+commitcount tags of the port
    pool_tags = collections.defaultdict(set)
    for r in rows:
        if r["plan_kind"] in ("calendar", "commitcount") and r["ok"] and r["tag"] in tab:
            pool_tags[r["port"]].add(r["tag"])
    pooled = {}
    for port, tgs in pool_tags.items():
        if only and port not in only:
            continue
        for ref in refs_for(port):
            tl = sorted(tgs)
            pooled[(port, ref)] = pooled_thresholds([S[(t, ref)][0] for t in tl], [S[(t, ref)][1] for t in tl], PARAMS.fdr)

    # snapshot rows
    out_rows, found_store, pre = [], collections.defaultdict(dict), {}
    for r in sel:
        tg, port = r["tag"], r["port"]
        tb = tab[tg]
        meta = json.loads((r["dir"] / "meta.json").read_text())
        em = elig_mask(tb)
        n_el = int(em.sum())
        pre.setdefault(tg, dict(ports=set(), sha=r["sha"], ctags_functions=meta.get("ctags_functions", ""), eligible_snapshot=n_el))
        pre[tg]["ports"].add(port)
        c, cpp, oth = lang_shares(tb.language, tb.loc)
        dsh = dup_share(tb.key, tb.loc)
        org = origin.get(port)
        age = round((parse_date(r["date"]) - org).days / 365.25, 4) if org else ""
        text = {}
        if not a.no_text and r["role"] == "lineage" and port in lineage_ports:
            try:
                text = text_measures(ctx, tg, r["dir"])
            except Exception as e:  # noqa: BLE001
                errors.append(dict(tag=tg, where="text", error=repr(e)[:300]))
        for ref in refs_for(port):
            nm = names_measures(ctx, ref, tg, port, tb, ctx.cache / "names" / f"{tg}__{ref}__{E.N_safe(port)}.json")
            fs, bs = S[(tg, ref)]
            per = struct_measures(ctx, ref, fs, bs)
            pl = pooled.get((port, ref))
            pp = struct_measures(ctx, ref, fs, bs, pl) if pl else None
            nR = per["nR"]
            row = dict(port=port, role=r["role"], stratum=r["stratum"], plan_kind=r["plan_kind"], fraction=r["fraction"],
                       sha=r["sha"], date=r["date"], age_years=age, ref=ref, n_ref_eligible=nR, eligible_snapshot=n_el,
                       dup_share=round(dsh, 6), lang_c=round(c, 6), lang_cpp=round(cpp, 6), lang_other=round(oth, 6),
                       ctags_functions=meta.get("ctags_functions", ""), pruned=";".join(meta.get("pruned", [])),
                       underpowered=int(n_el < MIN_POWER), surv_names=nm["surv_names"],
                       surv_names_nostop=nm["surv_names_nostop"], names_certified=nm["names_certified"],
                       shared_names=nm["shared_names"], surv_struct_persnap_either=per["either"] / nR,
                       surv_struct_persnap_fwd=per["fwd_only"] / nR,
                       surv_struct_pooled_either=(pp["either"] / nR) if pp else "", shared_struct_persnap=per["shared"],
                       shared_struct_pooled=pp["shared"] if pp else "", text_en=text.get("text_en", ""),
                       text_end=text.get("text_end", ""))
            if ref == "R1":
                st = found_store[tg]
                st.setdefault("names", name_found_mask(ctx.tables["R1"].name[elig_mask(ctx.tables["R1"])], tb.name[em],
                                                       ctx.stop))
                st["persnap"] = per["found"]
                st.setdefault("pooled", {})[port] = pp["found"] if pp else np.zeros(nR, dtype=bool)
                st.setdefault("pooled_has", {})[port] = pp is not None
                st.setdefault("roles", {})[port] = r["role"]
            out_rows.append(row)
    for tg, st in found_store.items():
        ports = sorted(st["pooled"])
        primary = next((p for p in ports if st["roles"][p] == "lineage"), ports[0])
        extra = {f"found_struct_pooled__{p}": st["pooled"][p] for p in ports}
        np.savez_compressed(results / "found" / f"{tg}__R1.npz", found_names=st["names"],
                            found_struct_persnap=st["persnap"], found_struct_pooled=st["pooled"][primary],
                            pooled_port=np.array(primary), ports=np.array(ports), **extra)
    write(results / "snapshots.csv", SNAP_COLS, out_rows)

    # precondition (a scan that cannot be fingerprinted, e.g. an early commit with no functions, counts as 0 eligible)
    for tg, r in failed.items():
        meta = json.loads((r["dir"] / "meta.json").read_text())
        pre.setdefault(tg, dict(ports=set(), sha=r["sha"], ctags_functions=meta.get("ctags_functions", ""), eligible_snapshot=0))
        pre[tg]["ports"].update(x["port"] for x in rows if x["tag"] == tg)
    prow = []
    for tg, d in pre.items():
        prow.append(dict(tag=tg, ports=";".join(sorted(d["ports"])), sha=d["sha"], ctags_functions=d["ctags_functions"],
                         eligible_snapshot=d["eligible_snapshot"], usable=int(d["eligible_snapshot"] >= MIN_POWER)))
    write(results / "precondition.csv", ["tag", "ports", "sha", "ctags_functions", "eligible_snapshot", "usable"], prow)
    summ = []
    for port in ports_all:
        cal = {r["sha"] for r in rows if r["port"] == port and r["plan_kind"] == "calendar"}
        allp = {r["sha"] for r in rows if r["port"] == port}
        fin_c = {r["sha"] for r in rows if r["port"] == port and r["plan_kind"] == "calendar" and r["tag"] in pre}
        fin_a = {r["sha"] for r in rows if r["port"] == port and r["tag"] in pre}
        use = lambda shas: sum(1 for r in {(x["sha"]): x for x in rows if x["port"] == port and x["sha"] in shas}.values()  # noqa: E731
                               if r["tag"] in pre and pre[r["tag"]]["eligible_snapshot"] >= MIN_POWER)
        summ.append(dict(port=port, planned_distinct_calendar=len(cal), planned_distinct_all=len(allp),
                         scanned_calendar=len(fin_c), scanned_all=len(fin_a), usable_distinct_calendar=use(fin_c),
                         usable_distinct_all=use(fin_a)))
    write(results / "precondition_summary.csv", list(summ[0]), summ)

    # self-origin survival (Amendment 1 D.16)
    (ctx.cache / "self").mkdir(exist_ok=True)
    so = []
    for port in sorted(lineage_ports):
        if only and port not in only:
            continue
        seen = {}
        for r in rows:
            if (r["port"] == port and r["plan_kind"] == "calendar" and r["tag"] in tab
                    and int(elig_mask(tab[r["tag"]]).sum()) >= MIN_POWER):
                seen.setdefault(r["sha"], r)
        if not seen:
            continue
        ordered = sorted(seen.values(), key=lambda r: (parse_date(r["date"]), r["sha"]))
        r0 = ordered[0]
        t0 = tab[r0["tag"]]
        n0 = int(elig_mask(t0).sum())
        for r in ordered:
            nm_, st_ = self_survival(t0, tab[r["tag"]], ctx.stop, ctx.cache / "self" / f"{r0['tag']}__{r['tag']}.json")
            org = origin.get(port)
            so.append(dict(port=port, sha0=r0["sha"], sha=r["sha"],
                           age_years=round((parse_date(r["date"]) - org).days / 365.25, 4) if org else "",
                           n_s0_eligible=n0, surv_names_self=nm_, surv_struct_self_persnap_either=st_))
    write(results / "self_origin.csv", SELF_COLS, so)

    # grid pairs
    grows = []
    if not only:
        for g in grid:
            rowp = grid_row(ctx, g, tasks, portinfo, snaps, errors)
            if rowp:
                grows.append(rowp)
    write(results / "pairs_grid.csv", GRID_COLS, grows)

    # noise
    if not a.no_noise and not only:
        write(results / "noise.csv", NOISE_COLS, noise_rows(ctx, a, tasks, tab, S))
    if errors:
        write(results / "errors.csv", ["tag", "where", "error"], errors)
    el = time.time() - t_start
    n = max(len(tags), 1)
    print(f"done: {len(tags)} snapshots, {len(out_rows)} snapshot rows, {len(grows)} grid pairs, {len(errors)} errors; "
          f"{el:.0f}s total, {el / n:.1f}s per snapshot (fingerprint+searches, uncached part)", flush=True)


def write(path: Path, cols, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def grid_row(ctx: Ctx, g, tasks, portinfo, snaps: Path, errors):
    sides = {}
    for side in ("child", "parent"):
        port, sha = g[side], g[f"{side}_sha"]
        t = tasks.get((port, sha))
        sk = t["scope_key"] if t else portinfo.get(port, {}).get("scope_key", "")
        tg = tag_of(sha, sk)
        d = snaps / tg
        if not finished(d):
            return None
        try:
            sides[side] = (port, tg, ctx.fingerprint(snap_db(d), tg))
        except Exception as e:  # noqa: BLE001
            errors.append(dict(tag=tg, where="grid", error=repr(e)[:300]))
            return None
    (cp, ct, ctab), (pp, pt, ptab) = sides["child"], sides["parent"]
    # distinct labels even when the two sides are the same commit (same tag): suffix by side
    cl, pl = ct + "_c", pt + "_p"
    ctab = FunctionTable(**{**ctab.__dict__, "repo": cl})
    ptab = FunctionTable(**{**ptab.__dict__, "repo": pl})
    c2p = T.find_twins(ctab, ptab, PARAMS)
    p2c = T.find_twins(ptab, ctab, PARAMS)
    nc, np_ = c2p.eligible, p2c.eligible
    w1, w2 = wilson(len(c2p.q_index), nc), wilson(len(p2c.q_index), np_)
    nf = ctx.names_pair(cl, ctab, cp, pl, ptab, pp)
    nb = ctx.names_pair(pl, ptab, pp, cl, ctab, cp)
    status = nf["pool_status"] if nf["pool_status"] == nb["pool_status"] else f"{nf['pool_status']}/{nb['pool_status']}"
    return dict(child=g["child"], parent=g["parent"], step=g["step"], target_date=g["target_date"],
                child_sha=g["child_sha"], parent_sha=g["parent_sha"], identical_sha=int(g["child_sha"] == g["parent_sha"]),
                elig_child=nc, elig_parent=np_, surv_struct_c2p=len(c2p.q_index) / nc if nc else 0.0,
                surv_struct_p2c=len(p2c.q_index) / np_ if np_ else 0.0, shared_struct_max=max(w1, w2),
                shared_struct_min=min(w1, w2), surv_names_c2p=(nf["matched"] / nc if nc else 0.0),
                surv_names_p2c=(nb["matched"] / np_ if np_ else 0.0),
                shared_names_max=max(nf["wilson_cert"], nb["wilson_cert"]),
                shared_names_min=min(nf["wilson_cert"], nb["wilson_cert"]), names_pool_status=status)


NOISE_COLS = ["port", "sha", "tag", "surv_names_orig", "surv_names_rep1", "surv_names_rep2", "struct_either_orig",
              "struct_either_rep1", "struct_either_rep2", "absdiff_names_rep1", "absdiff_names_rep2",
              "absdiff_struct_rep1", "absdiff_struct_rep2"]


def noise_rows(ctx: Ctx, a, tasks, tab, S):
    snaps = Path(a.work) / "halflife"
    seen, out = {}, []
    for r in read_csv(REPO / "manifest" / "e8_rescan.csv"):
        seen.setdefault((r["port"], r["sha"]), set()).add(r["replicate"])
    for (port, sha), reps in sorted(seen.items()):
        t = tasks.get((port, sha))
        if not t:
            continue
        tg = tag_of(sha, t["scope_key"])
        if tg not in tab:
            continue
        vals = {}
        for name, T_, (fs, bs) in (("orig", tab[tg], S[(tg, "R1")]),):
            nm = names_measures(ctx, "R1", tg, port, T_, ctx.cache / "names" / f"{tg}__R1__{E.N_safe(port)}.json")
            m0 = struct_measures(ctx, "R1", fs, bs)
            vals[name] = (nm["surv_names"], m0["either"] / m0["nR"])
        for rep in ("1", "2"):
            d = snaps / f"snaps_rep{rep}" / tg
            if rep in reps and finished(d):
                tb = ctx.fingerprint(snap_db(d), tg, sub=f"rep{rep}")
                fs, bs = T.search(ctx.tables["R1"], tb, PARAMS), T.search(tb, ctx.tables["R1"], PARAMS)
                nm = names_measures(ctx, "R1", tg, port, tb, None)
                m = struct_measures(ctx, "R1", fs, bs)
                vals[rep] = (nm["surv_names"], m["either"] / m["nR"])
        row = dict(port=port, sha=sha, tag=tg, surv_names_orig=vals["orig"][0], struct_either_orig=vals["orig"][1])
        for rep in ("1", "2"):
            if rep in vals:
                row[f"surv_names_rep{rep}"], row[f"struct_either_rep{rep}"] = vals[rep]
                row[f"absdiff_names_rep{rep}"] = abs(vals[rep][0] - vals["orig"][0])
                row[f"absdiff_struct_rep{rep}"] = abs(vals[rep][1] - vals["orig"][1])
        out.append(row)
    return out


def status(a):
    rows, *_ = load_plan()
    snaps = Path(a.work) / "halflife" / "snaps"
    ok = {r["tag"] for r in ({**r, "tag": tag_of(r["sha"], r["scope_key"])} for r in rows)
          if finished(snaps / r["tag"])}
    tot = {tag_of(r["sha"], r["scope_key"]) for r in rows}
    print(f"{len(ok)}/{len(tot)} distinct snapshot scans finished")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", choices=["run", "status"])
    ap.add_argument("--work", default=str(WORK))
    ap.add_argument("--results", default=str(HL / "results"))
    ap.add_argument("--limit", type=int, default=0, help="process only the first N finished snapshots")
    ap.add_argument("--ports", help="comma-separated ports only (skips grid and noise)")
    ap.add_argument("--no-text", action="store_true")
    ap.add_argument("--no-noise", action="store_true")
    a = ap.parse_args(argv)
    (status if a.mode == "status" else run)(a)


if __name__ == "__main__":
    main()
