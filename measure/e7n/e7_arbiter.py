#!/usr/bin/env python3
"""DOOM-E7 name-blind text arbiter (Amendment 1 section B).

For every eligible function of the reference port ``linuxdoom`` decide how much of its code survives in another
port, WITHOUT using a function name or a file path to find candidates:

* tokens: comments stripped, the function's own name masked as ``@`` (the rule in structural_fingerprint/ledger.py),
  4-token shingles, Jaccard similarity;
* candidates: top-K (20) functions among ALL functions of the port by MinHash signature (128 permutations, numpy,
  fixed seed), then exact Jaccard on the shortlist; a normalised-body-hash lookup over the whole port is also
  tried, so an identical body is never missed by the shortlist;
* verdicts: ``exact`` (identical normalised body or sim == 1.0), ``near`` (>= 0.9), ``derived`` (>= 0.6), else ``gone``.

Eligible reference function = ``scan_io.load_scan`` function (synthetic slices such as ``__global_context__``
already dropped) with ``loc >= 6``: exactly the set ``structural_fingerprint.fingerprint.build(min_loc=6)`` keeps.

    python e7_arbiter.py --work /srv/storage_16tb/projects/doom-e7-work --engine 704cb35f0 --ports a,b|all --out DIR

Writes ``arbiter_<port>.csv`` per port and ``arbiter_summary.csv``. Ports without ``rc.txt`` in their scan dir
(scan unfinished) are skipped with a message.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import time
from collections import namedtuple
from pathlib import Path

import numpy as np

sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from e7_names import name_key  # noqa: E402
from structural_fingerprint import scan_io  # noqa: E402

REFERENCE = "linuxdoom"
MIN_LOC = 6
NEAR, DERIVED = 0.9, 0.6
K = 20
PERMS = 128
SHINGLE = 4
SEED = 20261122
TOKEN_RE = re.compile(r"[A-Za-z_]\w*|\d+|[^\s\w]")
HASH_COMMENT = (".py", ".rb", ".sh", ".pl", ".r", ".jl", ".ex", ".exs", ".yml", ".yaml")
M64 = np.uint64(0xFFFFFFFFFFFFFFFF)

Func = namedtuple("Func", "file name start toks")
_tok_hash: dict[str, int] = {}


def tokenize_body(text: str, path: str, name: str) -> list[str]:
    """Tokens of one function's text: comments stripped, its own name (and its last qualified part) masked ``@``."""
    if path.lower().endswith(HASH_COMMENT):
        text = re.sub(r"#.*", "", text)
    else:
        text = re.sub(r"//.*", "", re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL))
    last = re.split(r"::|\.", name)[-1]
    return ["@" if t == name or t == last else t for t in TOKEN_RE.findall(text)]


def _th(t: str) -> int:
    h = _tok_hash.get(t)
    if h is None:
        h = _tok_hash[t] = int.from_bytes(hashlib.blake2b(t.encode(), digest_size=8).digest(), "little")
    return h


def shingle_array(toks: list[str]) -> np.ndarray:
    """Sorted unique uint64 hashes of the 4-token shingles (a body shorter than 4 tokens is one shingle)."""
    if not toks:
        return np.zeros(0, dtype=np.uint64)
    h = np.fromiter((_th(t) for t in toks), dtype=np.uint64, count=len(toks))
    n = max(1, len(h) - SHINGLE + 1)
    if len(h) < SHINGLE:
        h = np.concatenate([h, np.zeros(SHINGLE - len(h), dtype=np.uint64)])
    acc = np.zeros(n, dtype=np.uint64)
    with np.errstate(over="ignore"):
        for j in range(SHINGLE):
            acc = acc * np.uint64(0x9E3779B97F4A7C15) + h[j : j + n] + np.uint64(j + 1)
    return np.unique(acc)


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    if not len(a) or not len(b):
        return 0.0
    inter = len(np.intersect1d(a, b, assume_unique=True))
    return inter / (len(a) + len(b) - inter)


def _perms() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    a = rng.integers(1, 2**63, size=PERMS, dtype=np.uint64) * np.uint64(2) + np.uint64(1)
    b = rng.integers(0, 2**63, size=PERMS, dtype=np.uint64)
    return a, b


def _mix(x: np.ndarray) -> np.ndarray:
    with np.errstate(over="ignore"):
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        return x ^ (x >> np.uint64(31))


def signatures(sh: list[np.ndarray]) -> np.ndarray:
    """(n, PERMS) uint64 MinHash signatures; an empty shingle set gets an all-ones signature that never matches."""
    a, b = _perms()
    sig = np.full((len(sh), PERMS), np.iinfo(np.uint64).max, dtype=np.uint64)
    with np.errstate(over="ignore"):
        for i, s in enumerate(sh):
            if len(s):
                m = _mix(s)
                for lo in range(0, len(m), 4096):
                    v = m[lo : lo + 4096, None] * a[None, :] + b[None, :]
                    sig[i] = np.minimum(sig[i], v.min(axis=0)) if lo else v.min(axis=0)
    return sig


def shortlist(sig_ref: np.ndarray, sig_port: np.ndarray, k: int = K, chunk: int = 128) -> np.ndarray:
    """(R, min(k,P)) indices of the port functions whose signatures agree in most slots (ties: lower index)."""
    r, p = len(sig_ref), len(sig_port)
    kk = min(k, p)
    out = np.zeros((r, kk), dtype=np.int64)
    if kk == 0:
        return out
    for lo in range(0, r, chunk):
        blk = sig_ref[lo : lo + chunk]
        cnt = np.zeros((len(blk), p), dtype=np.int32)
        for i in range(PERMS):
            cnt += blk[:, i, None] == sig_port[None, :, i]
        # lexicographic: higher count first, then lower index
        key = cnt.astype(np.int64) * (p + 1) + (p - np.arange(p))[None, :]
        part = np.argpartition(-key, kk - 1, axis=1)[:, :kk]
        ordv = np.take_along_axis(key, part, axis=1)
        out[lo : lo + chunk] = np.take_along_axis(part, np.argsort(-ordv, axis=1), axis=1)
    return out


def verdict_of(sim: float, exact: bool) -> str:
    if exact or sim >= 1.0:
        return "exact"
    if sim >= NEAR:
        return "near"
    if sim >= DERIVED:
        return "derived"
    return "gone"


def match(ref: list[Func], port: list[Func], k: int = K) -> list[dict]:
    """Name-blind best match of every ``ref`` function among all ``port`` functions: [{verdict, sim, j}] (j = port
    index, -1 for none). Names and paths are never consulted."""
    sh_r = [shingle_array(f.toks) for f in ref]
    sh_p = [shingle_array(f.toks) for f in port]
    body_p: dict[bytes, int] = {}
    for j, f in enumerate(port):
        if f.toks:
            body_p.setdefault(hashlib.sha1("\x00".join(f.toks).encode()).digest(), j)
    if ref and port:
        short = shortlist(signatures(sh_r), signatures(sh_p), k)
    else:
        short = np.zeros((len(ref), 0), dtype=np.int64)
    out = []
    for i, f in enumerate(ref):
        if not f.toks or not len(sh_r[i]):
            out.append(dict(verdict="gone", sim=0.0, j=-1))
            continue
        hit = body_p.get(hashlib.sha1("\x00".join(f.toks).encode()).digest())
        if hit is not None:
            out.append(dict(verdict="exact", sim=1.0, j=hit))
            continue
        best, bj = 0.0, -1
        for j in short[i]:
            s = jaccard(sh_r[i], sh_p[int(j)])
            if s > best:
                best, bj = s, int(j)
        out.append(dict(verdict=verdict_of(best, False), sim=best, j=bj if best > 0 else -1))
    return out


def _rel(path: str, repo: Path) -> str:
    path = path.replace("\\", "/")
    prefix = str(repo).replace("\\", "/").rstrip("/") + "/"
    return path[len(prefix) :] if path.startswith(prefix) else path


def scan_db(work: Path, engine: str, port: str) -> Path | None:
    d = work / "scans" / engine / port
    if not (d / "rc.txt").is_file():
        return None
    dbs = sorted(d.glob(f"*{scan_io.DB_SUFFIX}"))
    return dbs[0] if dbs else None


def load_scan_data(db: Path):
    return scan_io.load_scan(db, ())


def eligible_mask(scan) -> np.ndarray:
    """The set sfs fingerprints at min_loc 6 (load_scan already dropped the synthetic slices)."""
    return scan.loc >= MIN_LOC


def read_lines(repo: Path, rel: str, cache: dict) -> list[str] | None:
    if rel not in cache:
        try:
            cache[rel] = (repo / rel).read_bytes().decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
        except OSError:
            cache[rel] = None
    return cache[rel]


def build_funcs(scan, repo: Path, db: Path, idx=None) -> list[Func]:
    """Functions of a scan (all, or the ``idx`` subset) with body tokens sliced from the clone (start_line, loc)."""
    import sqlite3

    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        start = dict(con.execute("select id, coalesce(start_line, 0) from function_data"))
    finally:
        con.close()
    cache: dict = {}
    paths = scan.func_path
    out = []
    for i in range(scan.n_functions) if idx is None else idx:
        rel = _rel(paths[i], repo)
        s = int(start.get(int(scan.func_id[i]), 0))
        lines = read_lines(repo, rel, cache)
        toks: list[str] = []
        if lines is not None and s >= 1:
            toks = tokenize_body("\n".join(lines[s - 1 : s - 1 + max(int(scan.loc[i]), 1)]), rel, scan.func_name[i])
        out.append(Func(rel, scan.func_name[i], s, toks))
    return out


COLS = ["ref_file", "ref_func", "ref_start_line", "verdict", "sim", "port_file", "port_func", "name_survives"]


def run_port(ref_funcs: list[Func], port_funcs: list[Func]) -> list[dict]:
    keys = {name_key(f.name) for f in port_funcs} - {None}
    res = match(ref_funcs, port_funcs)
    rows = []
    for f, r in zip(ref_funcs, res, strict=True):
        p = port_funcs[r["j"]] if r["j"] >= 0 and r["verdict"] != "gone" else None
        nk = name_key(f.name)
        rows.append(dict(ref_file=f.file, ref_func=f.name, ref_start_line=f.start, verdict=r["verdict"],
                         sim=round(r["sim"], 4), port_file=p.file if p else "", port_func=p.name if p else "",
                         name_survives=int(nk is not None and nk in keys)))  # fmt: skip
    return rows


def summarise(port: str, rows: list[dict]) -> dict:
    def shares(sub):
        n = len(sub)
        c = {v: sum(r["verdict"] == v for r in sub) for v in ("exact", "near", "derived", "gone")}
        en = (c["exact"] + c["near"]) / n if n else float("nan")
        end = (c["exact"] + c["near"] + c["derived"]) / n if n else float("nan")
        return c, en, end

    c, en, end = shares(rows)
    sub = [r for r in rows if r["name_survives"]]
    _, sen, send = shares(sub)
    return dict(port=port, eligible=len(rows), exact=c["exact"], near=c["near"], derived=c["derived"],
                gone=c["gone"], share_exact_near=round(en, 4), share_exact_near_derived=round(end, 4),
                name_survivors=len(sub), share_exact_near_ns=round(sen, 4),
                share_exact_near_derived_ns=round(send, 4))  # fmt: skip


def write_csv(path: Path, rows: list[dict], cols: list[str] | None = None) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols or list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--engine", required=True)
    ap.add_argument("--ports", required=True, help="comma-separated ports, or 'all' (every port with a finished scan)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    work = a.work.resolve()
    ref_db = scan_db(work, a.engine, REFERENCE)
    if ref_db is None:
        raise SystemExit(f"e7_arbiter: no finished scan of {REFERENCE} under {work}/scans/{a.engine}")
    if a.ports == "all":
        ports = sorted(p.name for p in (work / "scans" / a.engine).iterdir() if p.is_dir() and p.name != REFERENCE)
    else:
        ports = [p for p in a.ports.split(",") if p and p != REFERENCE]
    a.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    scan = load_scan_data(ref_db)
    elig = np.flatnonzero(eligible_mask(scan))
    ref_funcs = build_funcs(scan, work / "repos" / REFERENCE, ref_db, elig)
    print(f"e7_arbiter: {REFERENCE}: {len(ref_funcs)} eligible functions (loc >= {MIN_LOC})")
    summary = []
    for port in ports:
        db = scan_db(work, a.engine, port)
        if db is None:
            print(f"e7_arbiter: SKIP {port}: no finished scan (no rc.txt) under {work}/scans/{a.engine}/{port}")
            continue
        repo = work / "repos" / port
        if not repo.is_dir():
            print(f"e7_arbiter: SKIP {port}: no clone at {repo}")
            continue
        t1 = time.time()
        ps = load_scan_data(db)
        port_funcs = build_funcs(ps, repo, db)
        rows = run_port(ref_funcs, port_funcs)
        write_csv(a.out / f"arbiter_{port}.csv", rows, COLS)
        summary.append(summarise(port, rows))
        s = summary[-1]
        print(f"e7_arbiter: {port}: {len(port_funcs)} functions, exact+near {s['share_exact_near']}, "
              f"+derived {s['share_exact_near_derived']} ({time.time() - t1:.1f}s)")  # fmt: skip
    if summary:
        write_csv(a.out / "arbiter_summary.csv", summary)
    print(f"e7_arbiter: wrote {a.out} in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
