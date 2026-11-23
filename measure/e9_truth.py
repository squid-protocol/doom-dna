#!/usr/bin/env python3
"""DOOM-E9 outcome-blind truth builder (Amendment 1 sections B and C; D.14 de-duplication).

Builds the ground truth for horizontal transfer between DOOM ports WITHOUT any predictor: no twin table, no name
table, no structure score is read or computed. Function boundaries come from ``ctags`` (independent of the engine),
candidates come from one global MinHash-LSH over all function bodies (never from names or paths), the truth is the
exact Jaccard of 4-token shingles (name-blind text arbiter of E7: comments stripped, own name masked).

    python e9_truth.py run [--only-validate] [--programs a,b] [--skip-t2] [--force] [--jobs N] [--out DIR]

Stages (all cached under ``<out>/cache``; ``--force`` rebuilds):
  1 inventory   ctags functions, tokens, shingles (plain + identifier-normalised), MinHash signatures
  2 dedup       identical normalised bodies collapsed per repository (``dup_rep``)
  3 search      one LSH index over the representatives of all programs + progenitors, exact Jaccard on candidates
  4 vertical    counterpart (Jaccard >= 0.6) in an in-corpus ancestor (plus the name-key sensitivity)
  5 eligible    c_family, different clades, no shared commit, neither function vertical; classification, events
  6 outputs     functions.csv pairs.csv events*.csv perm_null.npz hand_audit_sample.csv truth_size.csv
  7 T2          first appearance dates by fuzzy body lineage through git history (``--skip-t2`` to omit)

SCHEMA CHOICES fixed where the registration is open (also in the final report):
  * functions.csv lists ALL ctags functions (func_id stable by path then start_line); eligible = loc >= 6;
    ``dup_rep`` is the func_id of the representative of the identical-body class (itself for the representative),
    -1 for ineligible functions. pairs.csv is at REPRESENTATIVE level; expand through ``dup_rep``.
  * pairs.csv keeps every cross-repository pair with Jaccard >= 0.6 OR identifier-normalised Jaccard >= 0.9 between
    programs of DIFFERENT clades (same-clade pairs are never eligible and are not written; they are counted in
    stats.json). Ineligible pairs carry pair_class cross-language | shared-commit | vertical | co-clade.
  * eligible pairs (any Jaccard) carry pair_class external-library | port-to-port | co-borrowing | coincidence;
    T3 directed rows take precedence over the external-library list (``opl`` is in both files); T1 = eligible_primary
    with jaccard >= 0.9; the 0.6 and identifier-normalised sets are the co-primary sensitivities.
  * event key: ``donor|recipient|module_cluster``; port-to-port: donor = T3 donor, recipient = borrower, cluster =
    borrower directory; co-borrowing: donor = common T3 donor, recipient = ``A+B`` (sorted), cluster = module name;
    external-library and coincidence: donor empty, recipient = ``A+B`` (sorted), cluster = ``dirA|dirB``.
  * events.csv has two trailing extra columns (n_pairs, module); n_functions = max over the two sides of distinct
    functions in the event. events_06.csv and events_idnorm.csv are the sensitivity versions.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import functools
import hashlib
import json
import multiprocessing as mp
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest"
WORK = Path("/srv/storage_16tb/projects/doom-e7-work")
POOL = Path("/srv/storage_16tb/projects/temporal-crucible-pool")
W9_DEFAULT = WORK / "e9" / "results" / "truth"
E7_MEASURE = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/measure")
STOPLIST = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e7-three-trees/manifest/name_stoplist.txt")
SFS_SRC = "/srv/storage_16tb/projects/structural-fingerprint-scanner/src"
ENGINE = "704cb35f0"

MIN_LOC = 6
NEAR, DERIVED = 0.9, 0.6
PERMS = 128
SHINGLE = 4
BANDS, ROWS = 32, 4  # P(candidate | J=0.6) = 1-(1-0.6^4)^32 = 0.988; J>=0.7 > 0.9999
SEED = 20261122
PREFILTER = 0.40  # MinHash-estimate floor before exact Jaccard (about 4.5 sigma below 0.6)
LINEAGE_J = 0.8
CENSOR_DAYS = 14
BASELINE_N = 2000
N_PERM = 200
HASH_COMMENT = (".py", ".rb", ".sh", ".pl", ".r", ".jl", ".ex", ".exs", ".yml", ".yaml")
FUNC_KINDS = {"function", "method", "subroutine", "procedure", "constructor", "destructor"}
C_EXT = {".c", ".h", ".m"}
CPP_EXT = {".cc", ".cpp", ".cxx", ".c++", ".hpp", ".hh", ".hxx", ".inl", ".ipp", ".mm", ".cu", ".cp"}

FAMILY = {
    "chocolate-doom": "chocolate-family", "crispy-doom": "chocolate-family", "inter-doom": "chocolate-family",
    "prboom-plus": "prboom-plus-family", "dsda-doom": "prboom-plus-family",
    "woof": "woof-family", "nugget-doom": "woof-family",
}  # fmt: skip
BOOM_ANCESTORS = ["boom-2.02", "mbf-2.03", "winmbf", "prboom-2.5.0"]
EXTRA_ANCESTORS = {"eternity": ["smmu"], "edge-classic": ["edge@2021-09-17"]}
PARENT_ANCESTOR = {"crispy-doom": "chocolate-doom", "nugget-doom": "woof", "dsda-doom": "prboom-plus"}
PROGENITORS = ["boom-2.02", "mbf-2.03", "smmu", "edge@2021-09-17", "prboom-2.5.0", "winmbf"]
BIG_FIRST = ["gzdoom", "doom3-bfg", "doomsday", "odamex", "eternity", "srb2", "quake2", "doom-ios"]

KEYWORDS = frozenset(
    """auto break case char const continue default do double else enum extern float for goto if inline int long
    register restrict return short signed sizeof static struct switch typedef union unsigned void volatile while
    _Bool bool class namespace template typename public private protected virtual new delete this try catch throw
    using operator true false nullptr constexpr override final explicit mutable friend const_cast dynamic_cast
    static_cast reinterpret_cast and or not fn let mut impl pub func var def lambda self import from as in is elif
    except finally yield async await end then local function nil null val fun object interface extends implements
    package abstract synchronized throws instanceof elsif begin""".split()
)

TOKEN_RE = re.compile(r"[A-Za-z_]\w*|\d+|[^\s\w]")
IDTOKEN_RE = re.compile(r"\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'|[A-Za-z_]\w*|\d+(?:\.\d+)?|[^\s\w]")
IDENT_RE = re.compile(r"[A-Za-z_]\w*$")


def log(msg: str) -> None:
    print(f"e9_truth {time.strftime('%H:%M:%S')}: {msg}", flush=True)


# ----------------------------------------------------------------------------------------------- tokens, shingles
def strip_comments(text: str, path: str) -> str:
    if path.lower().endswith(HASH_COMMENT):
        return re.sub(r"#.*", "", text)
    return re.sub(r"//.*", "", re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL))


def tokenize_body(text: str, path: str, name: str) -> list[str]:
    """E7 tokens: comments stripped, the function's own name (and its last qualified part) masked ``@``."""
    text = strip_comments(text, path)
    last = re.split(r"::|\.", name)[-1]
    return ["@" if t == name or t == last else t for t in TOKEN_RE.findall(text)]


def idnorm_tokens(text: str, path: str) -> list[str]:
    """Identifier-normalised stream: every non-keyword identifier becomes ``ID``; literals and punctuation kept."""
    out = []
    for t in IDTOKEN_RE.findall(strip_comments(text, path)):
        out.append("ID" if IDENT_RE.match(t) and t not in KEYWORDS else t)
    return out


_tok_hash: dict[str, int] = {}


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


def body_hash(toks: list[str]) -> str:
    return hashlib.sha1("\x00".join(toks).encode()).hexdigest()[:16]


# ----------------------------------------------------------------------------------------------- MinHash and LSH
@functools.lru_cache(maxsize=1)
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
    """(n, PERMS) uint64 MinHash signatures; an empty shingle set gets an all-ones signature."""
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


def band_keys(sig: np.ndarray, band: int, rows: int = ROWS) -> np.ndarray:
    blk = sig[:, band * rows : (band + 1) * rows]
    k = np.zeros(len(sig), dtype=np.uint64)
    with np.errstate(over="ignore"):
        for c in range(rows):
            k = k * np.uint64(0x9E3779B97F4A7C15) + blk[:, c] + np.uint64(c + 1)
    return k


def lsh_pairs(sig: np.ndarray, keep_pair=None, bands: int = BANDS, rows: int = ROWS, cap: int = 5000):
    """Candidate pairs (i < j) whose signatures agree on all ``rows`` slots of at least one band.

    ``keep_pair(lo, hi) -> bool array`` filters before accumulation. Returns (lo, hi, n_oversize_groups)."""
    n = len(sig)
    out, big = [], 0
    for b in range(bands):
        k = band_keys(sig, b, rows)
        order = np.argsort(k, kind="stable")
        ks = k[order]
        brk = np.flatnonzero(ks[1:] != ks[:-1]) + 1
        st, en = np.r_[0, brk], np.r_[brk, n]
        sz = en - st
        two = st[sz == 2]
        ii, jj = [order[two]], [order[two + 1]]
        for s0, e0 in zip(st[sz > 2], en[sz > 2], strict=True):
            if e0 - s0 > cap:
                big += 1
                continue
            m = order[s0:e0]
            a, c = np.triu_indices(len(m), 1)
            ii.append(m[a])
            jj.append(m[c])
        i, j = np.concatenate(ii), np.concatenate(jj)
        lo, hi = np.minimum(i, j), np.maximum(i, j)
        if keep_pair is not None and len(lo):
            m = keep_pair(lo, hi)
            lo, hi = lo[m], hi[m]
        out.append(lo.astype(np.int64) * n + hi)
    codes = np.unique(np.concatenate(out)) if out else np.zeros(0, dtype=np.int64)
    return codes // max(n, 1), codes % max(n, 1), big


def est_jaccard(sig: np.ndarray, i: np.ndarray, j: np.ndarray, chunk: int = 40000) -> np.ndarray:
    out = np.empty(len(i), dtype=np.float32)
    for lo in range(0, len(i), chunk):
        out[lo : lo + chunk] = (sig[i[lo : lo + chunk]] == sig[j[lo : lo + chunk]]).mean(axis=1)
    return out


_G: dict = {}


def _jac_chunk(span):
    lo, hi = span
    i, j, sh, shi = _G["i"], _G["j"], _G["sh"], _G["shi"]
    a = np.empty(hi - lo, dtype=np.float32)
    b = np.empty(hi - lo, dtype=np.float32)
    for k in range(lo, hi):
        a[k - lo] = jaccard(sh[i[k]], sh[j[k]])
        b[k - lo] = jaccard(shi[i[k]], shi[j[k]])
    return a, b


def exact_pairs(i, j, sh, shi, jobs: int = 1):
    """Exact Jaccard (plain and identifier-normalised) of every pair, optionally on a forked pool."""
    n = len(i)
    if n == 0:
        return np.zeros(0, np.float32), np.zeros(0, np.float32)
    _G.update(i=i, j=j, sh=sh, shi=shi)
    spans = [(lo, min(n, lo + 20000)) for lo in range(0, n, 20000)]
    if jobs > 1 and len(spans) > 1:
        with mp.get_context("fork").Pool(jobs) as pool:
            res = pool.map(_jac_chunk, spans)
    else:
        res = [_jac_chunk(s) for s in spans]
    return np.concatenate([r[0] for r in res]), np.concatenate([r[1] for r in res])


# ----------------------------------------------------------------------------------------------- ctags inventory
def ctags_cmd(cpp_h: bool = False) -> list[str]:
    cmd = ["ctags", "--output-format=json", "--fields=+neKS", "--kinds-C=f", "--kinds-C++=f", "--sort=no",
           "--exclude=.git", "-o", "-"]  # fmt: skip
    if cpp_h:
        cmd += ["--map-C=-.h", "--map-C++=+.h"]
    return cmd


def parse_ctags(stdout: str) -> list[tuple[str, str, int, int]]:
    """[(path, name, start, end)] of function and method definitions, sorted by path then start line."""
    seen, out = set(), []
    for line in stdout.splitlines():
        if not line.startswith("{"):
            continue
        try:
            t = json.loads(line)
        except ValueError:
            continue
        if t.get("_type") != "tag" or t.get("kind") not in FUNC_KINDS or "end" not in t or "line" not in t:
            continue
        s, e = int(t["line"]), int(t["end"])
        if e < s:
            continue
        key = (t["path"], t["name"], s, e)
        if key not in seen:
            seen.add(key)
            out.append(key)
    out.sort(key=lambda r: (r[0], r[2], r[3], r[1]))
    return out


def ctags_dir(root: Path, cpp_h: bool = False) -> list[tuple[str, str, int, int]]:
    r = subprocess.run(ctags_cmd(cpp_h) + ["-R"], cwd=root, capture_output=True, text=True, errors="replace",
                       timeout=3600)  # fmt: skip
    return parse_ctags(r.stdout)


def ctags_files(paths: list[str], cwd: Path, cpp_h: bool = False) -> list[tuple[str, str, int, int]]:
    r = subprocess.run(ctags_cmd(cpp_h) + ["-L", "-"], cwd=cwd, input="\n".join(paths) + "\n", capture_output=True,
                       text=True, errors="replace", timeout=3600)  # fmt: skip
    return parse_ctags(r.stdout)


def read_lines(path: Path) -> list[str] | None:
    try:
        return path.read_bytes().decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
    except OSError:
        return None


@dataclass
class FuncRec:
    name: str
    path: str
    start: int
    end: int
    loc: int
    ext: str
    toks: list[str] | None = None
    idtoks: list[str] | None = None


def load_functions(root: Path, cpp_h: bool = False, all_tokens: bool = False) -> list[FuncRec]:
    """ctags functions of a tree with tokens for the eligible ones (loc >= 6; all of them if ``all_tokens``)."""
    out: list[FuncRec] = []
    cache: dict[str, list[str] | None] = {}
    for path, name, s, e in ctags_dir(root, cpp_h):
        if path not in cache:
            cache[path] = read_lines(root / path)
        lines = cache[path]
        rec = FuncRec(name, path, s, e, e - s + 1, os.path.splitext(path)[1].lower())
        if lines is not None and (all_tokens or rec.loc >= MIN_LOC):
            text = "\n".join(lines[s - 1 : e])
            rec.toks = tokenize_body(text, path, name)
            rec.idtoks = idnorm_tokens(text, path)
        out.append(rec)
    return out


def dedup_reps(hashes: list[str | None], eligible) -> np.ndarray:
    """func_id of the representative (lowest id) of each identical-body class; -1 where not eligible."""
    rep = np.full(len(hashes), -1, dtype=np.int64)
    first: dict[str, int] = {}
    for i, h in enumerate(hashes):
        if eligible[i] and h:
            rep[i] = first.setdefault(h, i)
    return rep


# ----------------------------------------------------------------------------------------------- manifests, rules
def read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def load_programs() -> dict[str, dict]:
    return {r["name"]: r for r in read_csv(MANIFEST / "e9_programs.csv")}


def clade_key(name: str, programs: dict[str, dict]) -> str:
    c = programs[name]["clade"]
    return f"own:{name}" if c == "own" else c


def ancestors_of(port: str, programs: dict[str, dict]) -> list[str]:
    anc = [] if port == "linuxdoom" else ["linuxdoom"]
    if programs[port]["clade"] == "boom-mbf":
        anc += BOOM_ANCESTORS
    anc += EXTRA_ANCESTORS.get(port, [])
    if port in PARENT_ANCESTOR:
        anc.append(PARENT_ANCESTOR[port])
    return list(dict.fromkeys(anc))


def pair_ineligible_reason(a: str, b: str, programs: dict[str, dict], shared: set) -> str:
    """'' if the PROGRAM pair is eligible; else cross-language | co-clade | shared-commit (vertical is per function)."""
    if programs[a]["language_group"] != "c_family" or programs[b]["language_group"] != "c_family":
        return "cross-language"
    if clade_key(a, programs) == clade_key(b, programs):
        return "co-clade"
    if frozenset((a, b)) in shared:
        return "shared-commit"
    return ""


def stratum_of(ext_a: str, ext_b: str) -> str:
    kind = lambda e: "c" if e in C_EXT else "cpp" if e in CPP_EXT else "other"  # noqa: E731
    return "-".join(sorted((kind(ext_a), kind(ext_b))))


def path_dir(path: str) -> str:
    d = os.path.dirname(path)
    return d if d else "."


class Rules:
    """External-library list (e9_external_libs.csv) and T3 file (e9_t3.csv): annotate functions, classify pairs."""

    def __init__(self, libs: list[dict], t3: list[dict]):
        self.libs = [(r["library"], [p.strip().lower() for p in r["directory_pattern"].split("|") if p.strip()])
                     for r in libs]  # fmt: skip
        self.t3 = t3
        self.by_donor: dict[str, list[dict]] = defaultdict(list)
        self.by_borrower: dict[str, list[dict]] = defaultdict(list)
        for r in t3:
            self.by_donor[r["donor"]].append(r)
            self.by_borrower[r["borrower"]].append(r)

    @classmethod
    def load(cls) -> Rules:
        return cls(read_csv(MANIFEST / "e9_external_libs.csv"), read_csv(MANIFEST / "e9_t3.csv"))

    def external_lib(self, path: str) -> str:
        comps = [c.lower() for c in path.replace("\\", "/").split("/")[:-1]]
        for lib, pats in self.libs:
            if any(fnmatch.fnmatchcase(c, p) for c in comps for p in pats):
                return lib
        return ""

    def roles(self, program: str, path: str) -> list[tuple[str, str, dict]]:
        """T3 roles of a function: [(module, 'donor'|'borrower', row)]."""
        low = path.replace("\\", "/").lower()
        comps = low.split("/")[:-1]
        out = []
        for r in self.by_donor.get(program, []):
            if r["module"].lower() in comps:
                out.append((r["module"], "donor", r))
        for r in self.by_borrower.get(program, []):
            bp = r["borrower_path"].lower().strip("/")
            if low.startswith(bp + "/"):
                out.append((r["module"], "borrower", r))
        return out

    def annotate(self, program: str, path: str) -> dict:
        roles = self.roles(program, path)
        return dict(dir=path_dir(path), lib=self.external_lib(path), roles=roles,
                    t3_module=roles[0][0] if roles else "")  # fmt: skip

    def classify(self, prog_a: str, ann_a: dict, prog_b: str, ann_b: dict) -> dict:
        """Class of an eligible pair (programs in sorted order a < b): donor, recipient, module_cluster, module."""
        pair = f"{prog_a}+{prog_b}"
        dirs = f"{ann_a['dir']}|{ann_b['dir']}"
        if any(role == "borrower" and r["type"].startswith("co-clade") for _, role, r in ann_a["roles"] + ann_b["roles"]):
            return dict(pair_class="co-clade", donor="", recipient=pair, module_cluster=dirs, module="")
        for ma, ra, rowa in ann_a["roles"]:
            for mb, rb, rowb in ann_b["roles"]:
                if ma != mb or not rowa["type"].startswith("port-to-port") or not rowb["type"].startswith("port-to-port"):
                    continue
                if ra == "donor" and rb == "borrower" and rowb["donor"] == prog_a and rowb["borrower"] == prog_b:
                    return dict(pair_class="port-to-port", donor=prog_a, recipient=prog_b, module_cluster=ann_b["dir"],
                                module=ma)  # fmt: skip
                if rb == "donor" and ra == "borrower" and rowa["donor"] == prog_b and rowa["borrower"] == prog_a:
                    return dict(pair_class="port-to-port", donor=prog_b, recipient=prog_a, module_cluster=ann_a["dir"],
                                module=ma)  # fmt: skip
                if ra == "borrower" and rb == "borrower" and rowa["donor"] == rowb["donor"]:
                    return dict(pair_class="co-borrowing", donor=rowa["donor"], recipient=pair, module_cluster=ma,
                                module=ma)  # fmt: skip
        lib = ann_a["lib"] or ann_b["lib"]
        if lib:
            return dict(pair_class="external-library", donor="", recipient=pair, module_cluster=dirs, module=lib)
        return dict(pair_class="coincidence", donor="", recipient=pair, module_cluster=dirs, module=dirs)


def event_id(donor: str, recipient: str, cluster: str) -> str:
    return f"{donor}|{recipient}|{cluster}"


def lineage_of(prog_a: str, prog_b: str) -> str:
    return "|".join(sorted((FAMILY.get(prog_a, prog_a), FAMILY.get(prog_b, prog_b))))


def censor_reason(first_ct: int, root_ct: int, added: int, total: int) -> str:
    """Left-censoring: within 14 days of the root commit, or a commit adding more than half the repository's files."""
    if first_ct - root_ct <= CENSOR_DAYS * 86400:
        return "root-14d"
    if total > 0 and added > 0.5 * total:
        return "squash-import"
    return ""


def vertical_from_pairs(ancestors: dict[str, list[str]], prog_i, fn_i, prog_j, fn_j, jac, names: list[str],
                        thresh: float = DERIVED) -> dict[tuple[str, int], tuple[str, float]]:  # fmt: skip
    """{(port, func_id): (best ancestor, jaccard)} from candidate pairs; a pair marks the side whose program has the
    other side's program among its ancestors."""
    out: dict[tuple[str, int], tuple[str, float]] = {}
    for pi, fi, pj, fj, jv in zip(prog_i, fn_i, prog_j, fn_j, jac, strict=True):
        if jv < thresh:
            continue
        for p, f, q in ((names[pi], int(fi), names[pj]), (names[pj], int(fj), names[pi])):
            if q in ancestors.get(p, ()):
                cur = out.get((p, f))
                if cur is None or jv > cur[1] or (jv == cur[1] and q < cur[0]):
                    out[(p, f)] = (q, float(jv))
    return out


# ----------------------------------------------------------------------------------------------- name key
try:
    sys.path.insert(0, str(E7_MEASURE))
    from e7_names import name_key  # type: ignore  # noqa: E402
except Exception:  # pragma: no cover - fallback with the identical rule
    _QUAL = re.compile(r"::|\.")

    def name_key(name):  # type: ignore
        if not name:
            return None
        last = _QUAL.split(name.strip())[-1]
        if last.startswith("~") or last.lower().startswith("operator"):
            return None
        key = re.sub(r"[^0-9a-z]", "", last.lower())
        return key if len(key) >= 3 else None


def load_stoplist() -> frozenset[str]:
    try:
        return frozenset(l.strip() for l in STOPLIST.read_text().splitlines() if l.strip() and not l.startswith("#"))
    except OSError:
        return frozenset()


# ----------------------------------------------------------------------------------------------- inventory stage
def program_root(name: str) -> tuple[Path, bool]:
    """(scoped source tree, cpp_h) of a program or progenitor."""
    progs = load_programs()
    if name in progs:
        return WORK / "repos" / name, progs[name]["primary_language"] in ("cpp", "c++")
    pins = {r["name"]: r for r in read_csv(MANIFEST / "e8b_pins.csv")}
    r = pins[name]
    tag = f"{r['sha'][:12]}__{hashlib.sha1(r['scope_key'].encode()).hexdigest()[:6]}"
    return WORK / "e8b" / "snaps" / tag / "_export", name.startswith("edge")


def inv_file(cache_dir: Path, name: str) -> Path:
    return cache_dir / f"inv_{name.replace('@', '_at_')}.npz"


def inventory(name: str, cache_dir: Path, force: bool = False) -> Path:
    """Build (or reuse) one program's inventory cache file."""
    out = inv_file(cache_dir, name)
    if out.is_file() and not force:
        return out
    root, cpp_h = program_root(name)
    t0 = time.time()
    funcs = load_functions(root, cpp_h)
    n = len(funcs)
    elig = np.array([f.toks is not None and len(f.toks) > 0 for f in funcs], dtype=bool)
    sh = [shingle_array(f.toks) if elig[i] else np.zeros(0, np.uint64) for i, f in enumerate(funcs)]
    shi = [shingle_array(f.idtoks) if elig[i] else np.zeros(0, np.uint64) for i, f in enumerate(funcs)]
    eidx = np.flatnonzero(elig)
    sig = signatures([sh[i] for i in eidx])
    sigi = signatures([shi[i] for i in eidx])
    off = np.r_[0, np.cumsum([len(s) for s in sh])]
    offi = np.r_[0, np.cumsum([len(s) for s in shi])]
    tmp = out.with_suffix(".tmp.npz")
    np.savez(tmp, name=np.array([f.name for f in funcs]), path=np.array([f.path for f in funcs]),
             start=np.array([f.start for f in funcs], dtype=np.int32), end=np.array([f.end for f in funcs], dtype=np.int32),
             ext=np.array([f.ext for f in funcs]), elig=elig,
             hash=np.array([body_hash(f.toks) if elig[i] else "" for i, f in enumerate(funcs)]),
             sh=np.concatenate(sh) if n else np.zeros(0, np.uint64), off=off,
             shi=np.concatenate(shi) if n else np.zeros(0, np.uint64), offi=offi, sig=sig, sigi=sigi)  # fmt: skip
    tmp.replace(out)
    log(f"inventory {name}: {n} functions, {int(elig.sum())} eligible ({time.time() - t0:.0f}s)")
    return out


@dataclass
class Inv:
    name: str
    func: list[str]
    path: list[str]
    start: np.ndarray
    end: np.ndarray
    ext: list[str]
    elig: np.ndarray
    hash: list[str]
    sh: list[np.ndarray]
    shi: list[np.ndarray]
    sig: np.ndarray  # rows aligned to eidx
    sigi: np.ndarray
    eidx: np.ndarray
    dup_rep: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))

    @property
    def n(self) -> int:
        return len(self.func)

    @property
    def loc(self) -> np.ndarray:
        return self.end - self.start + 1


def load_inv(name: str, file: Path) -> Inv:
    z = np.load(file)
    off, offi = z["off"], z["offi"]
    shall, shiall = z["sh"], z["shi"]
    sh = [shall[off[i] : off[i + 1]] for i in range(len(off) - 1)]
    shi = [shiall[offi[i] : offi[i + 1]] for i in range(len(offi) - 1)]
    elig = z["elig"]
    inv = Inv(name, list(z["name"]), list(z["path"]), z["start"], z["end"], list(z["ext"]), elig, list(z["hash"]), sh,
              shi, z["sig"], z["sigi"], np.flatnonzero(elig))  # fmt: skip
    inv.dup_rep = dedup_reps(inv.hash, elig)
    return inv


# ----------------------------------------------------------------------------------------------- histories
def git(gd: Path, *args: str, input: str | None = None, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(gd), *args], capture_output=True, text=True, errors="replace", input=input)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:3])} failed in {gd}: {r.stderr[:200]}")
    return r.stdout


def history_source(name: str, sha: str) -> tuple[Path | None, bool]:
    """(git dir holding the pinned SHA, is_shallow)."""
    cands = [POOL / "doom-ports" / name, WORK / "halflife" / "controls" / name, POOL / name, WORK / "repos" / name]
    for c in cands:
        if c.is_dir() and subprocess.run(["git", "-C", str(c), "cat-file", "-e", f"{sha}^{{commit}}"],
                                         capture_output=True).returncode == 0:  # fmt: skip
            shallow = git(c, "rev-parse", "--is-shallow-repository", check=False).strip() == "true"
            return c, shallow
    return None, False


def commit_set(gd: Path, sha: str) -> set[bytes]:
    return {bytes.fromhex(l) for l in git(gd, "rev-list", sha).split() if len(l) == 40}


def shared_commit_pairs(names: list[str], programs: dict[str, dict], cache: Path) -> tuple[set, dict]:
    """Program pairs whose histories (full ancestry of the pinned SHAs) share at least one commit."""
    f = cache / "shared_commits.csv"
    src = {n: history_source(n, programs[n]["sha"]) for n in names}
    if f.is_file():
        return {frozenset((r["a"], r["b"])) for r in read_csv(f)}, src
    sets = {n: commit_set(gd, programs[n]["sha"]) for n, (gd, _) in src.items() if gd is not None}
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if a in sets and b in sets and not sets[a].isdisjoint(sets[b]):
                rows.append(dict(a=a, b=b, n_shared=len(sets[a] & sets[b])))
    write_csv(f, rows, ["a", "b", "n_shared"])
    return {frozenset((r["a"], r["b"])) for r in rows}, src


# ----------------------------------------------------------------------------------------------- engine row
def engine_rows(name: str, inv: Inv) -> np.ndarray:
    """Row of each ctags function in the E7 fingerprint FunctionTable (-1 unmatched): same path and last name
    component, nearest start line (scan database function_data), then nearest loc; greedy one-to-one."""
    rows = np.full(inv.n, -1, dtype=np.int64)
    npz = WORK / "results" / "e7" / "phaseA" / "fingerprints" / f"{name}.sfp.npz"
    dbs = sorted((WORK / "scans" / ENGINE / name).glob("*_galaxy_master.db"))
    if not npz.is_file() or not dbs:
        return rows
    try:
        sys.path.insert(0, SFS_SRC)
        from structural_fingerprint import scan_io  # type: ignore
        import sqlite3

        z = np.load(npz)
        zname, zpath = z["name"], z["path"]
        scan = scan_io.load_scan(dbs[0], ())
        keep = np.flatnonzero(scan.loc >= 3)
        if len(keep) != len(zname) or not all(zname[i] == scan.func_name[j] for i, j in enumerate(keep[:200])):
            raise RuntimeError("scan and fingerprint tables are not aligned")
        con = sqlite3.connect(f"file:{dbs[0]}?mode=ro", uri=True)
        try:
            start = dict(con.execute("select id, coalesce(start_line, 0) from function_data"))
        finally:
            con.close()
    except Exception as exc:  # pragma: no cover - environment
        log(f"engine_row {name}: unavailable ({exc})")
        return rows
    last = lambda s: re.split(r"::|\.", s)[-1]  # noqa: E731
    table: dict[tuple[str, str], list[tuple[int, int, int]]] = defaultdict(list)
    for r, j in enumerate(keep):
        table[(str(zpath[r]), last(scan.func_name[j]))].append(
            (r, int(start.get(int(scan.func_id[j]), 0)), int(scan.loc[j])))
    cand = []
    for fid in range(inv.n):
        for r, s, l in table.get((inv.path[fid], last(inv.func[fid])), ()):
            cand.append((abs(s - int(inv.start[fid])), abs(l - int(inv.loc[fid])), fid, r))
    cand.sort()
    used_f, used_r = set(), set()
    for ds, _dl, fid, r in cand:
        if fid in used_f or r in used_r or ds > 200:
            continue
        rows[fid] = r
        used_f.add(fid)
        used_r.add(r)
    return rows


# ----------------------------------------------------------------------------------------------- T2 first appearance
def first_parent_root(gd: Path, sha: str) -> int:
    r = git(gd, "rev-list", "--first-parent", "--max-parents=0", sha).split()
    return min(int(git(gd, "show", "-s", "--format=%ct", c).strip()) for c in r)


def file_versions(gd: Path, sha: str, path: str) -> list[dict]:
    """First-parent history of ``path`` newest first, following renames and copies (-M -C)."""
    out = git(gd, "log", "--first-parent", "--follow", "-M", "-C", "--name-status", "--format=%x01%H\t%ct\t%at", sha,
              "--", path)  # fmt: skip
    versions, cur = [], path
    for block in out.split("\x01")[1:]:
        lines = block.strip("\n").split("\n")
        h, ct, at = lines[0].split("\t")
        status = [l.split("\t") for l in lines[1:] if l.strip()]
        here, deleted = cur, False
        for s in status:
            if s[0][0] in "RC":
                here, cur = s[-1], s[1]
            elif s[0][0] == "D":
                deleted = True
        if not deleted:
            versions.append(dict(commit=h, ct=int(ct), at=int(at), path=here))
    return versions


def cat_blobs(gd: Path, specs: list[str]) -> list[tuple[str, bytes] | None]:
    r = subprocess.run(["git", "-C", str(gd), "cat-file", "--batch"], input=("\n".join(specs) + "\n").encode(),
                       capture_output=True)  # fmt: skip
    buf, pos, out = r.stdout, 0, []
    for _ in specs:
        nl = buf.index(b"\n", pos)
        head = buf[pos:nl].decode(errors="replace").split()
        pos = nl + 1
        if len(head) < 3 or head[-1] == "missing":
            out.append(None)
            continue
        size = int(head[2])
        out.append((head[0], buf[pos : pos + size]))
        pos += size + 1
    return out


class BlobFuncs:
    """Functions of one file version (ctags) with lazily computed shingles."""

    def __init__(self, lines: list[str], path: str, funcs: list[tuple[str, int, int]]):
        self.lines, self.path, self.funcs = lines, path, funcs
        self._sh: dict[int, np.ndarray] = {}

    def shingles(self, k: int) -> np.ndarray:
        if k not in self._sh:
            name, s, e = self.funcs[k]
            self._sh[k] = shingle_array(tokenize_body("\n".join(self.lines[s - 1 : e]), self.path, name))
        return self._sh[k]


def trace_lineage(target_sh: np.ndarray, target_loc: int, blobs: list[BlobFuncs | None]) -> int:
    """Index (newest = 0) of the OLDEST consecutive file version holding a descendant of the target at
    Jaccard >= 0.8; each step compares with the previously matched body, so post-copy edits do not move the date."""
    cur, cur_loc, earliest = target_sh, target_loc, 0
    for v in range(1, len(blobs)):
        b = blobs[v]
        if b is None:
            break
        best, bk = 0.0, -1
        for k, (_, s, e) in enumerate(b.funcs):
            loc = e - s + 1
            if loc < 0.4 * cur_loc or loc > 2.5 * cur_loc:
                continue
            j = jaccard(cur, b.shingles(k))
            if j > best:
                best, bk = j, k
        if best >= LINEAGE_J:
            cur = b.shingles(bk)
            cur_loc = b.funcs[bk][2] - b.funcs[bk][1] + 1
            earliest = v
        else:
            break
    return earliest


def parse_blob_funcs(gd: Path, versions: list[dict], cpp_h: bool, cache: dict) -> list[BlobFuncs | None]:
    """Function lists of every version of one file (blob-sha cache; one ctags call for all new blobs)."""
    got = cat_blobs(gd, [f"{v['commit']}:{v['path']}" for v in versions])
    out: list[BlobFuncs | None] = [None] * len(versions)
    todo: list[tuple[int, str, bytes]] = []
    for i, g in enumerate(got):
        if g is None:
            continue
        sha, data = g
        if sha in cache:
            out[i] = cache[sha]
        elif not any(t[1] == sha for t in todo):
            todo.append((i, sha, data))
    if todo:
        with tempfile.TemporaryDirectory(prefix="e9t2_") as td:
            tdp = Path(td)
            names = []
            for k, (i, _sha, data) in enumerate(todo):
                nm = f"{k}{os.path.splitext(versions[i]['path'])[1].lower()}"
                (tdp / nm).write_bytes(data)
                names.append(nm)
            tags: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
            for path, name, s, e in ctags_files(names, tdp, cpp_h):
                tags[path].append((name, s, e))
            for k, (i, sha, data) in enumerate(todo):
                lines = data.decode("utf-8", "replace").replace("\r\n", "\n").split("\n")
                cache[sha] = BlobFuncs(lines, versions[i]["path"], tags.get(names[k], []))
    for i, g in enumerate(got):
        if g is not None:
            out[i] = cache[g[0]]
    return out


def commit_add_stats(gd: Path, commit: str, memo: dict) -> tuple[int, int]:
    """(files added by the commit relative to its first parent, files in the tree at the commit)."""
    if commit in memo:
        return memo[commit]
    total = len(git(gd, "ls-tree", "-r", "--name-only", commit).splitlines())
    parents = git(gd, "rev-list", "--parents", "-n", "1", commit).split()[1:]
    if parents:
        diff = git(gd, "diff-tree", "-r", "--no-commit-id", "--name-status", "--no-renames", parents[0], commit)
        added = len([l for l in diff.splitlines() if l.startswith("A")])
    else:
        added = total
    memo[commit] = (added, total)
    return memo[commit]


def iso_utc(ts: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


T2_COLS = ["program", "func_id", "first_commit", "first_date_committer", "first_date_author", "censored", "reason"]


def t2_for_file(task: dict) -> list[dict]:
    """First appearance of the target functions of ONE file (worker)."""
    gd, sha, path = Path(task["gd"]), task["sha"], task["path"]
    base = dict(program=task["program"])

    def fail(reason: str) -> list[dict]:
        return [dict(base, func_id=fid, first_commit="", first_date_committer="", first_date_author="", censored=1,
                     reason=reason) for fid, _, _ in task["targets"]]  # fmt: skip

    try:
        versions = file_versions(gd, sha, path)
    except Exception as exc:
        return fail(f"git-error:{str(exc)[:40]}")
    if not versions:
        return fail("no-history")
    blobs = parse_blob_funcs(gd, versions, task["cpp_h"], {})
    memo: dict = {}
    rows = []
    for fid, sh, loc in task["targets"]:
        v = versions[trace_lineage(sh, loc, blobs)]
        added, total = commit_add_stats(gd, v["commit"], memo)
        why = censor_reason(v["ct"], task["root_ct"], added, total)
        rows.append(dict(base, func_id=fid, first_commit=v["commit"], first_date_committer=iso_utc(v["ct"]),
                         first_date_author=iso_utc(v["at"]), censored=int(bool(why)), reason=why))  # fmt: skip
    return rows


# ----------------------------------------------------------------------------------------------- validation
def synthetic_lsh_recall(n_base: int = 1500, seed: int = 7) -> dict:
    """Miss rate of the LSH on synthetic near-copies with exact Jaccard in [0.6, 0.7), [0.7, 0.9) and >= 0.9."""
    rng = np.random.default_rng(seed)
    vocab = [f"t{i}" for i in range(400)]
    funcs = []
    for _ in range(n_base):
        base = [vocab[k] for k in rng.integers(0, 400, size=int(rng.integers(100, 240)))]
        funcs.append(base)
        for frac in (0.006, 0.02, 0.05, 0.057):
            c = list(base)
            for pos in rng.choice(len(c), size=max(1, int(frac * len(c))), replace=False):
                c[pos] = f"x{rng.integers(0, 10**6)}"
            funcs.append(c)
    sh = [shingle_array(f) for f in funcs]
    sig = signatures(sh)
    lo, hi, _ = lsh_pairs(sig)
    cand = set(zip(lo.tolist(), hi.tolist(), strict=True))
    bins = {"j06_07": [0, 0], "j07_09": [0, 0], "j09_up": [0, 0]}
    for g in range(n_base):
        b = g * 5
        for k in range(1, 5):
            j = jaccard(sh[b], sh[b + k])
            key = "j09_up" if j >= 0.9 else "j07_09" if j >= 0.7 else "j06_07" if j >= 0.6 else None
            if key:
                bins[key][0] += 1
                bins[key][1] += int((b, b + k) in cand)
    return {k: dict(n=v[0], found=v[1], miss_rate=(1 - v[1] / v[0]) if v[0] else float("nan")) for k, v in bins.items()}


def exact_best_matches(ref_sh: list[np.ndarray], port_sh: list[np.ndarray]) -> np.ndarray:
    """Exact best Jaccard of every ref set against all port sets via an inverted index (validation only)."""
    post: dict[int, list[int]] = defaultdict(list)
    for j, s in enumerate(port_sh):
        for h in s.tolist():
            post[h].append(j)
    sizes = np.array([len(s) for s in port_sh])
    best = np.zeros(len(ref_sh))
    for i, s in enumerate(ref_sh):
        if not len(s):
            continue
        cnt: Counter = Counter()
        for h in s.tolist():
            cnt.update(post.get(h, ()))
        for j, c in cnt.items():
            jv = c / (len(s) + sizes[j] - c)
            if jv > best[i]:
                best[i] = jv
    return best


def reproduce_arbiter(work: Path = WORK) -> dict:
    """linuxdoom eligible functions found in chocolate-doom, my own tokenisation: exact+near and +derived shares
    (E7 arbiter reference: about 0.43 and 0.66)."""
    ref = [f for f in load_functions(work / "repos" / "linuxdoom") if f.toks and f.loc >= MIN_LOC]
    port = [f for f in load_functions(work / "repos" / "chocolate-doom", all_tokens=True) if f.toks]
    sh_r = [shingle_array(f.toks) for f in ref]
    sh_p = [shingle_array(f.toks) for f in port]
    hashes = {body_hash(f.toks) for f in port}
    best = exact_best_matches(sh_r, sh_p)
    exact = np.array([body_hash(f.toks) in hashes for f in ref])
    n = len(ref)
    ex = int(exact.sum())
    near = int(((best >= NEAR) & ~exact).sum())
    der = int(((best >= DERIVED) & (best < NEAR) & ~exact).sum())
    # the LSH recall on the same real pair set
    allsig = np.concatenate([signatures(sh_r), signatures(sh_p)])
    lo, hi, _ = lsh_pairs(allsig, keep_pair=lambda a, b: (a < n) & (b >= n))
    lsh_best = np.zeros(n)
    for a, b in zip(lo.tolist(), hi.tolist(), strict=True):
        lsh_best[a] = max(lsh_best[a], jaccard(sh_r[a], sh_p[b - n]))
    missed = int(((best >= DERIVED) & (lsh_best < DERIVED) & ~exact).sum())
    return dict(eligible_linuxdoom=n, chocolate_functions=len(port), exact=ex, near=near, derived=der,
                share_exact_near=round((ex + near) / n, 4), share_exact_near_derived=round((ex + near + der) / n, 4),
                lsh_missed=missed, exact_found_ge_0_6=int(((best >= DERIVED) | exact).sum()),
                reference_exact_near=0.43, reference_exact_near_derived=0.66)  # fmt: skip


def validate(out: Path) -> dict:
    res: dict = {"synthetic_lsh": synthetic_lsh_recall()}
    log(f"synthetic LSH recall: {json.dumps(res['synthetic_lsh'])}")
    repro = reproduce_arbiter()
    res["reproduction"] = repro
    ok = abs(repro["share_exact_near"] - 0.43) <= 0.03 and abs(repro["share_exact_near_derived"] - 0.66) <= 0.03
    res["reproduction_within_0.03"] = bool(ok)
    log(f"reproduction: {json.dumps(repro)} within 0.03: {ok}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "validate.json").write_text(json.dumps(res, indent=1))
    return res


# ----------------------------------------------------------------------------------------------- main pipeline
def write_csv(path: Path, rows: list[dict], cols: list[str]) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def build_events(pairs: list[dict], level: str) -> list[dict]:
    """Events from eligible pairs at one truth level: 't1' (jaccard >= 0.9), 'j06', or 'idnorm' (idnorm >= 0.9)."""
    sel = {"t1": lambda p: p["jaccard"] >= NEAR, "j06": lambda p: p["jaccard"] >= DERIVED,
           "idnorm": lambda p: p["jaccard_idnorm"] >= NEAR}[level]  # fmt: skip
    ev: dict[str, dict] = {}
    for p in pairs:
        if not p["eligible_primary"] or not sel(p):
            continue
        e = ev.setdefault(p["event_id"], dict(event_id=p["event_id"], donor=p["donor"], recipient=p["recipient"],
                                              module_cluster=p["module_cluster"], pair_class=p["pair_class"],
                                              lineage_pair=lineage_of(p["prog_a"], p["prog_b"]), module=p["module"],
                                              _a=set(), _b=set(), n_pairs=0))  # fmt: skip
        e["_a"].add(p["func_a"])
        e["_b"].add(p["func_b"])
        e["n_pairs"] += 1
    out = []
    for e in ev.values():
        e["n_functions"] = max(len(e.pop("_a")), len(e.pop("_b")))
        out.append(e)
    return out


EVENT_COLS = ["event_id", "donor", "recipient", "module_cluster", "n_functions", "pair_class", "lineage_pair",
              "n_pairs", "module"]  # fmt: skip
PAIR_COLS = ["prog_a", "func_a", "prog_b", "func_b", "jaccard", "jaccard_idnorm", "pair_class", "eligible_primary",
             "stratum", "donor", "event_id"]  # fmt: skip
FUNC_COLS = ["program", "func_id", "name", "path", "start_line", "end_line", "loc", "language_ext", "body_hash",
             "dup_rep", "vertical", "vertical_ancestor", "vertical_namekey", "module_dir", "external_lib", "t3_module",
             "engine_row"]  # fmt: skip


def stack_reps(progs_all: list[str], invs: dict[str, Inv]):
    gp, gf, sig, sigi = [], [], [], []
    for pi, n in enumerate(progs_all):
        inv = invs[n]
        reps = np.flatnonzero(inv.elig & (inv.dup_rep == np.arange(inv.n)))
        rows = np.searchsorted(inv.eidx, reps)
        gp.append(np.full(len(reps), pi, dtype=np.int32))
        gf.append(reps)
        sig.append(inv.sig[rows])
        sigi.append(inv.sigi[rows])
    return np.concatenate(gp), np.concatenate(gf), np.concatenate(sig), np.concatenate(sigi)


def run(args) -> int:
    out = Path(args.out)
    cache = out / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    if args.only_validate:
        res = validate(out)
        return 0 if res["reproduction_within_0.03"] else 1
    programs = load_programs()
    ports = [p for p in programs if (not args.programs or p in args.programs.split(","))]
    port_set = set(ports)
    anc = {p: ancestors_of(p, programs) for p in programs}
    need = list(dict.fromkeys(ports + [a for p in ports for a in anc[p] if a in programs]))
    progs_all = need + [p for p in PROGENITORS if any(p in anc[x] for x in ports)]
    rules = Rules.load()
    stop = load_stoplist()
    jobs = args.jobs

    # ---- 1 inventory (parallel over programs)
    todo = [n for n in progs_all if args.force or not inv_file(cache, n).is_file()]
    if todo:
        todo.sort(key=lambda n: BIG_FIRST.index(n) if n in BIG_FIRST else 99)
        log(f"inventory of {len(todo)} programs on {jobs} workers")
        with mp.get_context("fork").Pool(min(jobs, len(todo))) as pool:
            pool.starmap(inventory, [(n, cache, args.force) for n in todo], chunksize=1)
    invs: dict[str, Inv] = {n: load_inv(n, inv_file(cache, n)) for n in progs_all}

    # ---- shared commits, history sources
    shared, src = shared_commit_pairs(list(programs), programs, cache)
    write_csv(out / "history_sources.csv", [dict(program=n, git_dir=str(g or ""), shallow=int(s),
                                                  pinned_sha=programs[n]["sha"]) for n, (g, s) in src.items()],
              ["program", "git_dir", "shallow", "pinned_sha"])  # fmt: skip

    # ---- 2/3 global reps and LSH
    gp, gf, sig, sigi = stack_reps(progs_all, invs)
    sh = [invs[progs_all[p]].sh[f] for p, f in zip(gp, gf, strict=True)]
    shi = [invs[progs_all[p]].shi[f] for p, f in zip(gp, gf, strict=True)]
    n_all = len(gp)
    log(f"global index: {n_all} representatives of {sum(int(i.elig.sum()) for i in invs.values())} eligible functions")

    P = len(progs_all)
    rel = np.zeros((P, P), dtype=bool)  # candidate pairs worth an exact Jaccard
    write_pair = np.zeros((P, P), dtype=bool)  # pairs that are written to pairs.csv
    for i, a in enumerate(progs_all):
        for j, b in enumerate(progs_all):
            if i == j:
                continue
            if a in programs and b in programs:
                diff = clade_key(a, programs) != clade_key(b, programs)
                rel[i, j] = diff or b in anc[a] or a in anc[b]
                write_pair[i, j] = diff and a in port_set and b in port_set
            elif (a in programs) != (b in programs):
                port, other = (a, b) if a in programs else (b, a)
                rel[i, j] = other in anc[port]
    t0 = time.time()
    keep = lambda lo, hi: rel[gp[lo], gp[hi]]  # noqa: E731
    lo1, hi1, big1 = lsh_pairs(sig, keep)
    lo2, hi2, big2 = lsh_pairs(sigi, keep)
    codes = np.unique(np.concatenate([lo1.astype(np.int64) * n_all + hi1, lo2.astype(np.int64) * n_all + hi2]))
    pi_, pj_ = codes // n_all, codes % n_all
    ok = (est_jaccard(sig, pi_, pj_) >= PREFILTER) | (est_jaccard(sigi, pi_, pj_) >= PREFILTER)
    pi_, pj_ = pi_[ok], pj_[ok]
    log(f"LSH: {len(codes)} candidates, {len(pi_)} after the {PREFILTER} estimate floor ({time.time() - t0:.0f}s);"
        f" oversize groups {big1 + big2}")
    j1, j2 = exact_pairs(pi_, pj_, sh, shi, jobs)
    kept = (j1 >= DERIVED) | (j2 >= NEAR)
    pi_, pj_, j1, j2 = pi_[kept], pj_[kept], j1[kept], j2[kept]
    log(f"exact Jaccard: {len(pi_)} pairs kept (plain >= 0.6 or idnorm >= 0.9)")

    # ---- 4 vertical
    vert = vertical_from_pairs(anc, gp[pi_], gf[pi_], gp[pj_], gf[pj_], j1, progs_all)
    anc_keys: dict[str, set[str]] = {}
    for n in {a for p in ports for a in anc[p]}:
        inv = invs[n]
        anc_keys[n] = {k for i in np.flatnonzero(inv.elig) if (k := name_key(inv.func[i])) and k not in stop}

    # ---- function annotations
    stats: dict = {"engine_match": {}}
    ann: dict[str, list[dict]] = {}
    func_rows: dict[str, list[dict]] = {}
    for n in ports:
        inv = invs[n]
        eng = engine_rows(n, inv)
        el = inv.elig
        stats["engine_match"][n] = dict(matched=int((eng >= 0).sum()), total=inv.n,
                                        rate=round(float((eng >= 0).mean()), 4) if inv.n else "",
                                        matched_eligible=int((eng[el] >= 0).sum()), eligible=int(el.sum()),
                                        rate_eligible=round(float((eng[el] >= 0).mean()), 4) if el.any() else "")  # fmt: skip
        ann[n], rows = [], []
        for f in range(inv.n):
            a = rules.annotate(n, inv.path[f])
            ann[n].append(a)
            rep = int(inv.dup_rep[f])
            v = vert.get((n, rep)) if rep >= 0 else None
            nk = name_key(inv.func[f]) if rep >= 0 else None
            vnk = int(v is not None or (nk is not None and nk not in stop and any(nk in anc_keys.get(x, ()) for x in anc[n])))
            rows.append(dict(program=n, func_id=f, name=inv.func[f], path=inv.path[f], start_line=int(inv.start[f]),
                             end_line=int(inv.end[f]), loc=int(inv.loc[f]), language_ext=inv.ext[f],
                             body_hash=inv.hash[f], dup_rep=rep, vertical=int(v is not None),
                             vertical_ancestor=v[0] if v else "", vertical_namekey=vnk, module_dir=a["dir"],
                             external_lib=a["lib"], t3_module=a["t3_module"], engine_row=int(eng[f])))  # fmt: skip
        func_rows[n] = rows
    write_csv(out / "functions.csv", [r for n in ports for r in func_rows[n]], FUNC_COLS)
    write_csv(out / "functions_progenitors.csv",
              [dict(program=n, func_id=f, name=invs[n].func[f], path=invs[n].path[f], start_line=int(invs[n].start[f]),
                    end_line=int(invs[n].end[f]), body_hash=invs[n].hash[f], dup_rep=int(invs[n].dup_rep[f]))
               for n in PROGENITORS if n in invs for f in range(invs[n].n)],
              ["program", "func_id", "name", "path", "start_line", "end_line", "body_hash", "dup_rep"])  # fmt: skip

    # ---- 5 pairs: eligibility, classification
    pairs: list[dict] = []
    skipped = 0
    for a_i, b_i, ja, jb in zip(pi_, pj_, j1, j2, strict=True):
        pa, pb = int(gp[a_i]), int(gp[b_i])
        if not write_pair[pa, pb]:
            skipped += 1
            continue
        A, B, fa, fb = progs_all[pa], progs_all[pb], int(gf[a_i]), int(gf[b_i])
        if A > B:
            A, B, fa, fb = B, A, fb, fa
        why = pair_ineligible_reason(A, B, programs, shared)
        if not why and ((A, fa) in vert or (B, fb) in vert):
            why = "vertical"
        cls = rules.classify(A, ann[A][fa], B, ann[B][fb])
        if not why and cls["pair_class"] == "co-clade":
            why = "co-clade"
        rec = dict(prog_a=A, func_a=fa, prog_b=B, func_b=fb, jaccard=round(float(ja), 4),
                   jaccard_idnorm=round(float(jb), 4), stratum=stratum_of(invs[A].ext[fa], invs[B].ext[fb]))  # fmt: skip
        if why:
            rec.update(pair_class=why, eligible_primary=0, donor="", event_id="", recipient="", module_cluster="",
                       module="")  # fmt: skip
        else:
            rec.update(pair_class=cls["pair_class"], eligible_primary=1, donor=cls["donor"],
                       event_id=event_id(cls["donor"], cls["recipient"], cls["module_cluster"]),
                       recipient=cls["recipient"], module_cluster=cls["module_cluster"], module=cls["module"])  # fmt: skip
        pairs.append(rec)
    pairs.sort(key=lambda p: (p["prog_a"], p["prog_b"], p["func_a"], p["func_b"]))
    write_csv(out / "pairs.csv", [{k: p[k] for k in PAIR_COLS} for p in pairs], PAIR_COLS)
    for level, fname in (("t1", "events.csv"), ("j06", "events_06.csv"), ("idnorm", "events_idnorm.csv")):
        write_csv(out / fname, build_events(pairs, level), EVENT_COLS)
    elig = [p for p in pairs if p["eligible_primary"]]
    log(f"pairs: {len(pairs)} written, {len(elig)} eligible, {sum(p['jaccard'] >= NEAR for p in elig)} eligible T1")

    perm_null(out, elig, invs, func_rows)
    hand_audit(out, elig, invs, args.seed)

    # ---- 7 T2
    t2_rows: list[dict] = []
    if not args.skip_t2:
        t2_rows = run_t2(out, elig, invs, programs, src, args, ports)
    truth_size(out, elig, invs, t2_rows, stats)
    stats.update(n_pairs_written=len(pairs), skipped_same_clade_candidates=skipped, lsh_oversize_groups=big1 + big2,
                 candidates=int(len(codes)), runtime_s=round(time.time() - t_start))  # fmt: skip
    (out / "stats.json").write_text(json.dumps(stats, indent=1))
    log(f"done in {time.time() - t_start:.0f}s")
    return 0


def perm_null(out: Path, elig: list[dict], invs: dict[str, Inv], func_rows) -> None:
    """200 seeded within-port redraws, matched on loc decile, of the same number of non-vertical eligible functions,
    for every eligible port pair with at least one matched function (indices only)."""
    byp: dict[tuple[str, str, str], dict[str, set]] = defaultdict(lambda: defaultdict(set))
    for p in elig:
        for lvl, ok in (("t1", p["jaccard"] >= NEAR), ("j06", p["jaccard"] >= DERIVED)):
            if ok:
                byp[(p["prog_a"], p["prog_b"], lvl)][p["prog_a"]].add(p["func_a"])
                byp[(p["prog_a"], p["prog_b"], lvl)][p["prog_b"]].add(p["func_b"])
    arrays, meta = {}, []
    deciles: dict[str, tuple] = {}
    for (A, B, lvl), sides in sorted(byp.items()):
        for prog in (A, B):
            if prog not in deciles:
                inv = invs[prog]
                reps = np.flatnonzero(inv.elig & (inv.dup_rep == np.arange(inv.n)))
                edges = np.quantile(inv.loc[reps], np.linspace(0.1, 0.9, 9))
                dec = np.searchsorted(edges, inv.loc, side="right")
                nonv = np.array([r for r in reps if not func_rows[prog][r]["vertical"]], dtype=np.int64)
                deciles[prog] = (dec, {d: nonv[dec[nonv] == d] for d in range(10)})
            dec, pool = deciles[prog]
            matched = np.array(sorted(sides[prog], key=lambda f: (dec[f], f)), dtype=np.int64)
            seed = int.from_bytes(hashlib.blake2b(f"{A}|{B}|{lvl}|{prog}".encode(), digest_size=4).digest(), "little")
            rng = np.random.default_rng([SEED, seed])
            need = Counter(int(dec[f]) for f in matched)
            draws = np.empty((N_PERM, len(matched)), dtype=np.uint32)
            for r in range(N_PERM):
                cols = []
                for d in sorted(need):
                    pl = pool[d]
                    if not len(pl):  # nearest non-empty decile
                        pl = pool[min((x for x in pool if len(pool[x])), key=lambda x: abs(x - d))]
                    cols.append(rng.choice(pl, size=need[d], replace=need[d] > len(pl)))
                draws[r] = np.concatenate(cols)
            key = f"{A}|{B}|{lvl}|{prog}"
            arrays[key + "|matched"] = matched.astype(np.uint32)
            arrays[key + "|draws"] = draws
            meta.append(key)
    np.savez_compressed(out / "perm_null.npz", keys=np.array(meta), n_draws=np.array(N_PERM), **arrays)
    log(f"perm_null.npz: {len(meta)} (pair, level, side) blocks")


def hand_audit(out: Path, elig: list[dict], invs: dict[str, Inv], seed: int) -> None:
    rng = np.random.default_rng(seed)
    arms = {"T1-confirmed": [p for p in elig if p["jaccard"] >= NEAR],
            "near-candidate-0.6-0.9": [p for p in elig if DERIVED <= p["jaccard"] < NEAR]}  # fmt: skip
    rows = []
    cols = ["arm", "prog_a", "func_a", "name_a", "path_a", "start_a", "end_a", "prog_b", "func_b", "name_b", "path_b",
            "start_b", "end_b", "jaccard", "jaccard_idnorm", "pair_class"]  # fmt: skip
    for arm, pool in arms.items():
        pick = rng.choice(len(pool), size=min(50, len(pool)), replace=False) if pool else []
        for k in sorted(int(x) for x in pick):
            p = pool[k]
            a, b = invs[p["prog_a"]], invs[p["prog_b"]]
            fa, fb = p["func_a"], p["func_b"]
            rows.append(dict(arm=arm, prog_a=p["prog_a"], func_a=fa, name_a=a.func[fa], path_a=a.path[fa],
                             start_a=int(a.start[fa]), end_a=int(a.end[fa]), prog_b=p["prog_b"], func_b=fb,
                             name_b=b.func[fb], path_b=b.path[fb], start_b=int(b.start[fb]), end_b=int(b.end[fb]),
                             jaccard=p["jaccard"], jaccard_idnorm=p["jaccard_idnorm"], pair_class=p["pair_class"]))  # fmt: skip
    write_csv(out / "hand_audit_sample.csv", rows, cols)


def run_t2(out: Path, elig: list[dict], invs, programs, src, args, ports) -> list[dict]:
    parts = out / "cache" / "t2_parts"
    parts.mkdir(exist_ok=True)
    rng = np.random.default_rng(args.seed)
    t1: dict[str, set] = defaultdict(set)
    matched_any: dict[str, set] = defaultdict(set)
    for p in elig:
        if p["jaccard"] >= NEAR or p["jaccard_idnorm"] >= NEAR:
            t1[p["prog_a"]].add(p["func_a"])
            t1[p["prog_b"]].add(p["func_b"])
        matched_any[p["prog_a"]].add(p["func_a"])
        matched_any[p["prog_b"]].add(p["func_b"])
    tasks, rows_all = [], []
    for n in ports:
        part = parts / f"{n}.csv"
        if part.is_file() and not args.force:
            rows_all += read_csv(part)
            continue
        gd, shallow = src[n]
        inv = invs[n]
        reps = np.flatnonzero(inv.elig & (inv.dup_rep == np.arange(inv.n)))
        base_pool = [int(f) for f in reps if f not in matched_any[n]]
        base = set(rng.choice(base_pool, size=min(args.baseline_n, len(base_pool)), replace=False).tolist()) if base_pool else set()
        targets = sorted(t1[n] | base)
        if not targets:
            write_csv(part, [], T2_COLS)
            continue
        if gd is None or shallow:
            rows = [dict(program=n, func_id=f, first_commit="", first_date_committer="", first_date_author="",
                         censored=1, reason="shallow-history" if gd else "no-history") for f in targets]  # fmt: skip
            write_csv(part, rows, T2_COLS)
            rows_all += rows
            continue
        sha = programs[n]["sha"]
        root_ct = first_parent_root(gd, sha)
        byfile = defaultdict(list)
        for f in targets:
            byfile[inv.path[f]].append((f, inv.sh[f], int(inv.end[f] - inv.start[f] + 1)))
        for path, tg in byfile.items():
            tasks.append(dict(program=n, gd=str(gd), sha=sha, path=path, targets=tg, root_ct=root_ct,
                              cpp_h=programs[n]["primary_language"] in ("cpp", "c++")))  # fmt: skip
    if tasks:
        log(f"T2: {len(tasks)} files on {args.jobs} workers")
        tasks.sort(key=lambda t: -len(t["targets"]))
        got: dict[str, list] = defaultdict(list)
        with mp.get_context("fork").Pool(args.jobs) as pool:
            for k, res in enumerate(pool.imap_unordered(t2_for_file, tasks, chunksize=1)):
                for r in res:
                    got[r["program"]].append(r)
                if k % 500 == 0:
                    log(f"T2 {k}/{len(tasks)} files")
        for n, rows in got.items():
            rows.sort(key=lambda r: r["func_id"])
            write_csv(parts / f"{n}.csv", rows, T2_COLS)
            rows_all += rows
    for r in rows_all:
        r["func_id"] = int(r["func_id"])
        r["censored"] = int(r["censored"])
    rows_all.sort(key=lambda r: (r["program"], r["func_id"]))
    write_csv(out / "t2.csv", rows_all, T2_COLS)
    return rows_all


def truth_size(out: Path, elig: list[dict], invs, t2_rows: list[dict], stats: dict) -> None:
    rows: list[dict] = []

    def add(metric, scope, value):
        rows.append(dict(metric=metric, scope=scope, value=value))

    dupn = {n: Counter(inv.dup_rep[inv.dup_rep >= 0].tolist()) for n, inv in invs.items()}

    def covered(sel):
        reps = set()
        for p in sel:
            reps.add((p["prog_a"], p["func_a"]))
            reps.add((p["prog_b"], p["func_b"]))
        return len(reps), sum(dupn[pr][f] for pr, f in reps)

    for cls in ["all", "port-to-port", "co-borrowing", "external-library", "coincidence"]:
        sub = [p for p in elig if cls == "all" or p["pair_class"] == cls]
        for lvl, sel, evl in (("t1_0.9", [p for p in sub if p["jaccard"] >= NEAR], "t1"),
                              ("j_0.6", [p for p in sub if p["jaccard"] >= DERIVED], "j06"),
                              ("idnorm_0.9", [p for p in sub if p["jaccard_idnorm"] >= NEAR], "idnorm")):  # fmt: skip
            ev = build_events(sub, evl)
            nf, nraw = covered(sel)
            add(f"eligible_pairs_{lvl}", cls, len(sel))
            add(f"functions_{lvl}", cls, nf)
            add(f"functions_raw_{lvl}", cls, nraw)
            add(f"events_{lvl}", cls, len(ev))
            add(f"distinct_modules_{lvl}", cls, len({e["module"] for e in ev}))
            add(f"independent_lineage_pairs_{lvl}", cls, len({e["lineage_pair"] for e in ev}))
            if ev:
                nfs = sorted(e["n_functions"] for e in ev)
                add(f"functions_per_event_median_{lvl}", cls, nfs[len(nfs) // 2])
                add(f"functions_per_event_min_{lvl}", cls, nfs[0])
                add(f"functions_per_event_max_{lvl}", cls, nfs[-1])
    ev_all = build_events(elig, "t1")
    add("power_gate_h91_descriptive", "all", int(len({e["lineage_pair"] for e in ev_all}) < 5 or
                                                 len({e["module"] for e in ev_all}) < 2))  # fmt: skip
    by: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in t2_rows:
        by[r["program"]][0] += 1
        by[r["program"]][1] += int(r["censored"] == 1 and r["reason"] in ("root-14d", "squash-import"))
    for n, (tot, cen) in sorted(by.items()):
        add("left_censored_share", n, round(cen / tot, 4) if tot else "")
        add("t2_functions", n, tot)
        add("t2_left_censored", n, cen)
    write_csv(out / "truth_size.csv", rows, ["metric", "scope", "value"])
    write_csv(out / "engine_match.csv", [dict(program=n, **v) for n, v in stats["engine_match"].items()],
              ["program", "matched", "total", "rate", "matched_eligible", "eligible", "rate_eligible"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("--only-validate", action="store_true", help="synthetic checks and the chocolate/linuxdoom reproduction")
    r.add_argument("--programs", default="", help="comma-separated subset of ports (default all 51)")
    r.add_argument("--skip-t2", action="store_true")
    r.add_argument("--force", action="store_true")
    r.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    r.add_argument("--out", default=str(W9_DEFAULT))
    r.add_argument("--seed", type=int, default=SEED)
    r.add_argument("--baseline-n", type=int, default=BASELINE_N)
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
