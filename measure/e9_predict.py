#!/usr/bin/env python
"""DOOM-E9 predictors (Amendment 1 sections D, E, F). Emits candidate function pairs; scores nothing.

    python e9_predict.py run --pairs eligible|controls|spike [--only-validate] [--truth T9] [--out P9]

* ``eligible``: every port pair with at least one ``eligible_primary`` row in truth/pairs.csv.
* ``controls``: each negative-control program (hard, soft, descriptive) crossed with every c_family DOOM port.
* ``spike``: (donor, spiked recipient) pairs listed in <spike>/spike_truth.csv; any two fingerprints work.
* ``--only-validate``: reproduces E7's phase A numbers for linuxdoom -> chocolate-doom (names matched count,
  structure twin count, decoy gate) and exits. Reads only E7 phase A tables and fingerprints.

Predictors and variants (column ``variant`` of predictions.csv):
  structure : primary (full repositories, twins in either direction, union, filtered post hoc by the vertical
              mask), premasked (vertical rows removed before the search), dedup (identical bodies collapsed
              first; co-primary), primary_vnk (post-hoc mask also drops vertical_namekey rows).
  names     : unique_key (n_A(k) = n_B(k) = 1; raw set, ``certified`` = pair-level E7 decoy gate passed),
              dedup (co-primary), multikey (any multiplicity, scored later by body-equivalence class), n2
              (DOOM prefix strip), unique_key_vnk.
  r1        : chance floor, budget max(k_struct, k_names, 5), drawn without replacement within pooled loc
              deciles (empty deciles fall back to the nearest).
  geometry  : reciprocal nearest neighbours on (loc, complexity, args) alone, same budget rule.

Estimators the Amendment left open are marked FIXED in comments. R2 (decoys) is not a predictor; decoy hit counts
are written to pairs_diag.csv as a calibration diagnostic only.
"""
from __future__ import annotations

import argparse
import csv
import sys
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
E9 = HERE.parent
SFS_SRC = "/srv/storage_16tb/projects/structural-fingerprint-scanner/src"
E7_MEASURE = "/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/measure"
for _p in (SFS_SRC, E7_MEASURE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import e7_names as N  # noqa: E402
import e7_run as R  # noqa: E402
from structural_fingerprint.fingerprint import FunctionTable, safe_name  # noqa: E402
from structural_fingerprint.twins import TwinParams, find_twins  # noqa: E402

WORK = Path("/srv/storage_16tb/projects/doom-e7-work")
T9 = WORK / "e9" / "results" / "truth"
P9 = WORK / "e9" / "results" / "pred"
S9 = WORK / "e9" / "results" / "spike"
FP_A = WORK / "results" / "e7" / "phaseA" / "fingerprints"
FP_S = S9 / "fingerprints"
E7_A = WORK / "results" / "e7" / "phaseA"
STOPLIST = Path(R.REPO) / "manifest" / "name_stoplist.txt"

ELIG = R.ELIGIBLE_LOC  # 6
FLOOR_K = 5
MULTI_CAP = 100  # FIXED: multikey emission omits keys whose n_A * n_B exceeds this (counted in the diagnostics)
HARD = ("nginx", "leveldb")
SOFT = ("helion", "room4doom", "rust-doom")
DESC = ("quake", "quake2", "lua")
NEGATIVES = HARD + SOFT + DESC
PRED_COLS = ["predictor", "variant", "prog_a", "func_a", "prog_b", "func_b", "score_or_dist", "certified"]
TRUE_VALUES = {"1", "true", "yes", "y", "t", "1.0"}


def truthy(x) -> bool:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return False
    return str(x).strip().lower() in TRUE_VALUES


def stable_seed(*parts) -> int:
    return zlib.crc32("|".join(str(p) for p in parts).encode()) & 0xFFFFFFFF


# ----------------------------------------------------------------------------------------------- tables, views
@dataclass
class View:
    """A FunctionTable restricted to ``rows`` (indices into the original table)."""
    table: FunctionTable
    rows: np.ndarray

    def __len__(self):
        return len(self.rows)


def make_view(t: FunctionTable, keep: np.ndarray | None = None) -> View:
    rows = np.arange(len(t)) if keep is None else np.flatnonzero(keep)
    if keep is None:
        return View(t, rows)
    sub = FunctionTable(repo=t.repo, name=t.name[rows], path=t.path[rows], language=t.language[rows], loc=t.loc[rows],
                        archetype=t.archetype[rows], key=t.key[rows], vectors=t.vectors[rows], edges=None)
    return View(sub, rows)


def load_table(name: str, dirs) -> FunctionTable:
    for d in dirs:
        p = Path(d) / f"{safe_name(name)}.sfp.npz"
        if p.exists():
            return FunctionTable.load(p)
    raise FileNotFoundError(f"no fingerprint table for {name} in {[str(d) for d in dirs]}")


class Funcs:
    """functions.csv lookups: engine_row <-> func_id, vertical flags, duplicate representatives."""

    def __init__(self, df: pd.DataFrame | None):
        self.rowmap: dict[str, dict[int, str]] = {}
        self.vertical: dict[str, set[int]] = {}
        self.vnk: dict[str, set[int]] = {}
        self.nonrep: dict[str, set[int]] = {}
        if df is None or not len(df):
            return
        df = df.copy()
        df["engine_row"] = pd.to_numeric(df["engine_row"], errors="coerce").fillna(-1).astype(int)
        for prog, g in df.groupby("program", sort=False):
            g = g[g.engine_row >= 0]
            self.rowmap[prog] = {int(r): str(f) for r, f in zip(g.engine_row, g.func_id)}
            self.vertical[prog] = {int(r) for r, v in zip(g.engine_row, g.vertical) if truthy(v)}
            vn = g["vertical_namekey"] if "vertical_namekey" in g else [0] * len(g)
            self.vnk[prog] = {int(r) for r, v in zip(g.engine_row, vn) if truthy(v)}
            # FIXED: a row is a duplicate (non-representative) iff dup_rep is set and differs from its own func_id.
            dr = g["dup_rep"] if "dup_rep" in g else [""] * len(g)
            self.nonrep[prog] = {int(r) for r, f, d in zip(g.engine_row, g.func_id, dr)
                                 if not (pd.isna(d) or str(d).strip() in ("", "-1", "nan")) and str(d) != str(f)}

    def fid(self, prog: str, row: int) -> str:
        m = self.rowmap.get(prog)
        if m is None:  # programs absent from functions.csv (spike recipients): the engine row is the id
            return str(int(row))
        return m.get(int(row), f"row:{int(row)}")

    def flag(self, store: dict, prog: str, n: int) -> np.ndarray:
        a = np.zeros(n, dtype=bool)
        for r in store.get(prog, ()):
            if r < n:
                a[r] = True
        return a


# ----------------------------------------------------------------------------------------------- structure
def struct_union(va: View, vb: View, params: TwinParams):
    """E7 twins in both directions, union. Returns ({(row_a, row_b): distance}, diagnostics). Rows are original."""
    r_ab = find_twins(va.table, vb.table, params)
    r_ba = find_twins(vb.table, va.table, params)
    pairs: dict[tuple[int, int], float] = {}
    for q, t, d in zip(r_ab.q_index, r_ab.t_index, r_ab.distance):
        k = (int(va.rows[q]), int(vb.rows[t]))
        pairs[k] = min(float(d), pairs.get(k, np.inf))
    for q, t, d in zip(r_ba.q_index, r_ba.t_index, r_ba.distance):
        k = (int(va.rows[t]), int(vb.rows[q]))
        pairs[k] = min(float(d), pairs.get(k, np.inf))
    diag = dict(twins_ab=r_ab.accepted, twins_ba=r_ba.accepted, exact_ab=int(r_ab.exact.sum()), exact_ba=int(r_ba.exact.sum()),
                thr_ab=float(r_ab.threshold), thr_ba=float(r_ba.threshold),
                decoy_hits_ab=int(r_ab.decoy_hits), decoy_hits_ba=int(r_ba.decoy_hits), k_union=len(pairs))
    return pairs, diag


# ----------------------------------------------------------------------------------------------- names
def key_table(v: View, keyfn, stoplist) -> dict[str, list[int]]:
    """key -> original rows of the eligible (loc >= 6) functions in the view (stoplist applied, as E7)."""
    d: dict[str, list[int]] = {}
    for i in np.flatnonzero(v.table.loc >= ELIG):
        k = keyfn(str(v.table.name[i]))
        if k is not None and k not in stoplist:
            d.setdefault(k, []).append(int(v.rows[i]))
    return d


def names_unique_pairs(va: View, vb: View, keyfn, stoplist) -> list[tuple[int, int, str]]:
    ka, kb = key_table(va, keyfn, stoplist), key_table(vb, keyfn, stoplist)
    return sorted((ka[k][0], kb[k][0], k) for k in ka if len(ka[k]) == 1 and len(kb.get(k, ())) == 1)


def names_multi_pairs(va: View, vb: View, keyfn, stoplist):
    """Keys present on both sides with multiplicity somewhere (n_A > 1 or n_B > 1). All cross pairs per key.
    Returns (pairs, n_keys_omitted_over_cap)."""
    ka, kb = key_table(va, keyfn, stoplist), key_table(vb, keyfn, stoplist)
    out, omitted = [], 0
    for k in sorted(ka):
        if k in kb and (len(ka[k]) > 1 or len(kb[k]) > 1):
            if len(ka[k]) * len(kb[k]) > MULTI_CAP:
                omitted += 1
                continue
            m = len(ka[k]) * len(kb[k])
            out.extend((a, b, k, m) for a in ka[k] for b in kb[k])
    return out, omitted


def names_matched_count(ta: FunctionTable, tb: FunctionTable, stoplist) -> int:
    """E7's name-survival matched count (sum over keys of min(n_A, n_B)); reuses E7's key code."""
    return N.matched(R.program_keys(ta, stoplist)["primary"], R.program_keys(tb, stoplist)["primary"])


class NamePool:
    """The E7 decoy pool and gate: 200 seeded draws, certified iff at most one draw reaches the matched count
    (the 99th percentile rule)."""

    def __init__(self, tables: dict[str, FunctionTable], stoplist, df_generic=frozenset(), fam=None):
        self.stop = stoplist
        self.df_generic = set(df_generic)
        self.per = {n: R.program_keys(t, stoplist) for n, t in tables.items()}
        self.vocab = R.build_vocab(self.per)
        self.dense_all = {n: R.dense(self.per[n]["primary"], self.vocab) for n in tables}
        self.total = np.sum(list(self.dense_all.values()), axis=0) if self.dense_all else np.zeros(len(self.vocab), dtype=np.int32)
        self.fam = fam if fam is not None else {}

    def gate(self, qn: str, tn: str, tq: FunctionTable, tt: FunctionTable) -> dict:
        per = {qn: R.program_keys(tq, self.stop), tn: R.program_keys(tt, self.stop)}
        vocab = dict(self.vocab)
        for p in per.values():
            for k in p["primary"]:
                vocab.setdefault(k, len(vocab))
        return R.run_names_pair(qn, tn, per, self.dense_all, self.total, self.fam, len(vocab), self.df_generic, vocab)


# ----------------------------------------------------------------------------------------------- R1 and geometry
def loc_deciles(loc_pooled: np.ndarray) -> np.ndarray:
    return np.quantile(loc_pooled, np.linspace(0, 1, 11)[1:-1]) if len(loc_pooled) else np.zeros(9)


def decile_of(edges: np.ndarray, loc: np.ndarray) -> np.ndarray:
    return np.searchsorted(edges, loc, side="right")


def r1_pairs(rows_a, loc_a, rows_b, loc_b, budget: int, seed: int):
    """Chance floor. FIXED: deciles are pooled over the pair's eligible functions on both sides; A functions are
    drawn without replacement uniformly; each is matched to an unused B function of the same decile, falling back
    to the nearest decile (lower first on ties) that still has unused B functions."""
    rows_a, rows_b = np.asarray(rows_a), np.asarray(rows_b)
    k = int(min(budget, len(rows_a), len(rows_b)))
    if k <= 0:
        return []
    rng = np.random.default_rng(seed)
    edges = loc_deciles(np.concatenate([loc_a, loc_b]))
    da, db = decile_of(edges, np.asarray(loc_a)), decile_of(edges, np.asarray(loc_b))
    pools = {d: list(np.flatnonzero(db == d)) for d in range(10)}
    out = []
    for i in rng.permutation(len(rows_a))[:k]:
        d0 = int(da[i])
        for off in range(10):
            cands = [d for d in (d0 - off, d0 + off) if 0 <= d <= 9 and pools[d]]
            if cands:
                d = cands[0]
                break
        else:
            break
        pl = pools[d]
        j = pl.pop(int(rng.integers(len(pl))))
        out.append((int(rows_a[i]), int(rows_b[j]), float(abs(int(loc_a[i]) - int(loc_b[j])))))
    return out


def geom_spec():
    """Column indices and lens weights of (log_loc, log_complexity, log_args) in the fingerprint vectors."""
    from structural_fingerprint.reference import load_reference
    ref = load_reference("structure")
    idx = [ref.feature_names.index(n) for n in ("log_loc", "log_complexity", "log_args")]
    w = np.asarray(ref.weights)[idx]
    return idx, np.where(w > 0, w, 1.0)


def geometry_pairs(rows_a, xa, rows_b, xb, budget: int):
    """Trivial-geometry baseline: reciprocal nearest neighbours on three standardised columns; the ``budget``
    closest reciprocal pairs (ties by row order)."""
    from scipy.spatial import cKDTree
    rows_a, rows_b = np.asarray(rows_a), np.asarray(rows_b)
    if len(rows_a) == 0 or len(rows_b) == 0 or budget <= 0:
        return []
    ta, tb = cKDTree(xb), cKDTree(xa)
    d_ab, i_ab = ta.query(xa, k=1)
    _, i_ba = tb.query(xb, k=1)
    out = [(int(rows_a[i]), int(rows_b[j]), float(d)) for i, (j, d) in enumerate(zip(i_ab, d_ab)) if i_ba[j] == i]
    out.sort(key=lambda t: (t[2], t[0], t[1]))
    return out[:budget]


# ----------------------------------------------------------------------------------------------- one port pair
def process_pair(A: str, B: str, ta: FunctionTable, tb: FunctionTable, funcs: Funcs, pool: NamePool,
                 params: TwinParams, stoplist, geom=None):
    """All predictors and variants for one unordered port pair. Returns (prediction tuples, diagnostics rows).
    Prediction tuples: (predictor, variant, prog_a, row_a, prog_b, row_b, score, certified)."""
    if A > B:
        A, B, ta, tb = B, A, tb, ta
    vert_a, vert_b = funcs.flag(funcs.vertical, A, len(ta)), funcs.flag(funcs.vertical, B, len(tb))
    vnk_a, vnk_b = funcs.flag(funcs.vnk, A, len(ta)), funcs.flag(funcs.vnk, B, len(tb))
    nr_a, nr_b = funcs.flag(funcs.nonrep, A, len(ta)), funcs.flag(funcs.nonrep, B, len(tb))
    if geom is None:
        geom = geom_spec()
    gcols, gw = geom
    preds, diags = [], []

    def emit(pred, variant, pairs, cert=0):
        for a, b, s, *c in pairs:
            preds.append((pred, variant, A, a, B, b, s, int(c[0]) if c else cert))

    for dd in ("primary", "dedup"):
        va = make_view(ta, None if dd == "primary" else ~nr_a)
        vb = make_view(tb, None if dd == "primary" else ~nr_b)
        lab = "primary" if dd == "primary" else "dedup"
        # ---- structure: full repositories, union, post-hoc vertical filter (primary)
        sp, sd = struct_union(va, vb, params)
        keep = [(a, b, d) for (a, b), d in sorted(sp.items()) if not vert_a[a] and not vert_b[b]]
        emit("structure", lab, [(a, b, d, 1) for a, b, d in keep])
        k_struct = len(keep)
        if dd == "primary":
            emit("structure", "primary_vnk", [(a, b, d, 1) for a, b, d in keep if not vnk_a[a] and not vnk_b[b]])
            vpa, vpb = make_view(ta, ~vert_a), make_view(tb, ~vert_b)
            pm, pd_ = struct_union(vpa, vpb, params)
            emit("structure", "premasked", [(a, b, d, 1) for (a, b), d in sorted(pm.items())])
            sd["k_premasked"] = len(pm)
            sd["twins_premasked_ab"], sd["twins_premasked_ba"] = pd_["twins_ab"], pd_["twins_ba"]
        # ---- names: unique key, raw set with the pair-level gate in ``certified``
        g1, g2 = pool.gate(A, B, va.table, vb.table), pool.gate(B, A, vb.table, va.table)
        cert = int(g1["certified"] or g2["certified"])  # FIXED: certified iff either direction passes the gate
        up = names_unique_pairs(va, vb, N.name_key, stoplist)
        upf = [(a, b, 0.0, cert) for a, b, _ in up if not vert_a[a] and not vert_b[b]]
        emit("names", "unique_key" if dd == "primary" else "dedup", upf)
        k_names = len(upf)
        if dd == "primary":
            emit("names", "unique_key_vnk", [(a, b, 0.0, cert) for a, b, _ in up if not (vert_a[a] or vnk_a[a] or vert_b[b] or vnk_b[b])])
            n2 = names_unique_pairs(va, vb, N.name_key_n2, stoplist)
            emit("names", "n2", [(a, b, 0.0, cert) for a, b, _ in n2 if not vert_a[a] and not vert_b[b]])
            mp, omitted = names_multi_pairs(va, vb, N.name_key, stoplist)
            emit("names", "multikey", [(a, b, float(m), cert) for a, b, _, m in mp if not vert_a[a] and not vert_b[b]])
            sd["multikey_keys_omitted"] = omitted
        # ---- chance floor and trivial geometry: same budget rule, non-vertical eligible functions
        budget = max(k_struct, k_names, FLOOR_K)
        ea = np.flatnonzero((va.table.loc >= ELIG) & ~vert_a[va.rows])
        eb = np.flatnonzero((vb.table.loc >= ELIG) & ~vert_b[vb.rows])
        emit("r1", lab, r1_pairs(va.rows[ea], va.table.loc[ea], vb.rows[eb], vb.table.loc[eb], budget, stable_seed(A, B, "R1", dd)), 0)
        xa = va.table.vectors[ea][:, gcols] / gw
        xb = vb.table.vectors[eb][:, gcols] / gw
        emit("geometry", lab, geometry_pairs(va.rows[ea], xa, vb.rows[eb], xb, budget), 0)
        diags.append(dict(prog_a=A, prog_b=B, variant=lab, elig_a=int(len(ea)), elig_b=int(len(eb)), k_struct=k_struct,
                          k_names=k_names, budget=budget, names_matched_ab=g1["matched"], decoy_ge_ab=g1["decoy_ge"],
                          decoy_ge_ba=g2["decoy_ge"], names_certified=cert, **sd))
    return preds, diags


# ----------------------------------------------------------------------------------------------- run modes
def read_pairs_csv(truth: Path) -> pd.DataFrame:
    return pd.read_csv(truth / "pairs.csv", dtype=str)


def eligible_port_pairs(pairs: pd.DataFrame):
    m = pairs[pairs.eligible_primary.map(truthy)]
    return sorted({tuple(sorted((a, b))) for a, b in zip(m.prog_a, m.prog_b)})


def control_pairs():
    progs = pd.read_csv(E9 / "manifest" / "e9_programs.csv")
    ports = sorted(progs[(progs.role == "map") & (progs.language_group == "c_family")].name)
    ports = [p for p in ports if p not in NEGATIVES]
    return sorted({tuple(sorted((n, p))) for n in NEGATIVES for p in ports})


def spike_pairs(spike: Path):
    st = pd.read_csv(spike / "spike_truth.csv", dtype=str)
    return sorted({tuple(sorted((d, r))) for d, r in zip(st.donor, st.recipient_program)})


def build_pool(stoplist):
    progs = [p for p in R.load_programs() if p["role"] in R.MAP_ROLES]
    names = [p["name"] for p in progs if (FP_A / f"{safe_name(p['name'])}.sfp.npz").exists()]
    tables = {n: load_table(n, [FP_A]) for n in names}
    generic = set()
    gp = E7_A / "generic_keys.json"
    if gp.exists():
        import json
        generic = set(json.load(open(gp)))
    return NamePool(tables, stoplist, generic, R.declared_families(names)), tables


def load_stoplist() -> frozenset:
    return frozenset(l.strip() for l in open(STOPLIST) if l.strip() and not l.startswith("#"))


def validate(stoplist) -> int:
    """Reproduce E7 phase A for linuxdoom -> chocolate-doom from the E7 tables (a known number)."""
    q, t = "linuxdoom", "chocolate-doom"
    tq, tt = load_table(q, [FP_A]), load_table(t, [FP_A])
    pool, _ = build_pool(stoplist)
    m = names_matched_count(tq, tt, stoplist)
    g = pool.gate(q, t, tq, tt)
    r = find_twins(tq, tt, TwinParams(min_loc=ELIG))
    ne = pd.read_csv(E7_A / "pairs_names.csv")
    ns = pd.read_csv(E7_A / "pairs_struct.csv")
    en = ne[(ne.q == q) & (ne.t == t)].iloc[0]
    es = ns[(ns.q == q) & (ns.t == t)].iloc[0]
    rows = [("names matched", m, int(en.matched)), ("names decoy_ge", g["decoy_ge"], int(en.decoy_ge)),
            ("names certified", g["certified"], int(en.certified)), ("structure twins", r.accepted, int(es.twins)),
            ("structure exact clones", int(r.exact.sum()), int(es.exact))]
    ok = True
    for lab, mine, e7 in rows:
        flag = "OK" if mine == e7 else "MISMATCH"
        ok &= mine == e7
        print(f"validate {q} -> {t}: {lab}: mine {mine}  E7 {e7}  {flag}")
    return 0 if ok else 1


def run(args) -> int:
    stop = load_stoplist()
    if args.only_validate:
        return validate(stop)
    truth, out = Path(args.truth), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fdf = truth / "functions.csv"
    funcs = Funcs(pd.read_csv(fdf, dtype={"program": str, "func_id": str, "dup_rep": str}) if fdf.exists() else None)
    if args.pairs == "eligible":
        plist, dirs, name = eligible_port_pairs(read_pairs_csv(truth)), [FP_A], "predictions.csv"
    elif args.pairs == "controls":
        plist, dirs, name = control_pairs(), [FP_A], "predictions_controls.csv"
    else:
        plist, dirs, name = spike_pairs(Path(args.spike)), [Path(args.spike) / "fingerprints", FP_A], "predictions_spike.csv"
    pool, tables = build_pool(stop)
    geom = geom_spec()
    params = TwinParams(min_loc=ELIG)

    def job(pr):
        a, b = pr
        try:
            ta = tables.get(a) or load_table(a, dirs)
            tb = tables.get(b) or load_table(b, dirs)
        except FileNotFoundError as e:
            return None, [dict(prog_a=a, prog_b=b, variant="skipped", note=str(e))]
        return process_pair(a, b, ta, tb, funcs, pool, params, stop, geom)

    n = 0
    with open(out / name, "w", newline="") as f, ThreadPoolExecutor(max_workers=args.workers) as ex:
        w = csv.writer(f)
        w.writerow(PRED_COLS)
        diag_all = []
        for preds, diags in ex.map(job, plist):
            diag_all.extend(diags)
            for pred, var, pa, ra, pb, rb, s, c in preds or []:
                w.writerow([pred, var, pa, funcs.fid(pa, ra), pb, funcs.fid(pb, rb), f"{s:.6g}", c])
                n += 1
    pd.DataFrame(diag_all).to_csv(out / name.replace("predictions", "pairs_diag"), index=False)
    print(f"wrote {n} predictions for {len(plist)} port pairs to {out / name}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--pairs", choices=["eligible", "spike", "controls"], required=True)
    r.add_argument("--only-validate", action="store_true")
    r.add_argument("--truth", default=str(T9))
    r.add_argument("--out", default=str(P9))
    r.add_argument("--spike", default=str(S9))
    r.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
