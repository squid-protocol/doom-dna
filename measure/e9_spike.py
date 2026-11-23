"""DOOM-E9 spike-in builder (manifest/e9_spike_recipe.md; Amendment 1 section E.16).

Outcome-blind: builds, scans and fingerprints constructed spike-ins and verifies the BUILD only (ctags function counts,
exact renaming map, scan statuses). It runs NO predictor (no twin search, no name matching, no near-copy search)
between a donor and a spiked recipient.

    python e9_spike.py build [--workers 3] [--no-scan]   # all tiers and both sizes, scans, fingerprints, truth csv
    python e9_spike.py check                             # verify what is on disk, print + write spike_check.json

Layout (scratch, outside every repository): ``W = doom-e7-work/e9/spike`` ; results ``S9 = doom-e7-work/e9/results/spike``.

Definitions fixed where the recipe was open
* Donor files: only ``*.c`` files directly in ``lib/`` (curl) and ``src/unix/`` (libuv), alphabetical, read from the donor
  repository AT ITS E7 PIN (``git show <pin>:<path>``). Eligible = ctags function definition with line span >= 6
  (end line - start line + 1; universal ctags kind ``f`` = definitions only, not prototypes). Files are added until the
  cumulative eligible count reaches the target (150 / 50); the file that crosses the target is included.
* Rename key: a definition name defined in ONE donor file is renamed globally to ``s9_<8 hex of sha1(seed+name)>``; a name
  defined in several donor files is renamed per file (hash of ``seed+name@relpath``) and only inside that file. Several
  definitions of one name in one file (#if variants) share one new name. Call sites = identifier tokens outside string
  and character literals, not preceded by ``.`` or ``->`` (struct members untouched); comments are renamed too.
* Tier b50 = the first floor(n/2) rename keys by sha1(seed+"b50:"+key) order; b100 = all.
* Tier c = b100, comments removed (stripping leaves strings intact), pinned clang-format.
* Tier d = c + ``(void)0;`` as first statement of every function body (then re-formatted) + reordering of function
  definitions inside each file (a seeded permutation of the extents among the extent slots; only top-level, non-overlapping
  extents that are not inside any #if are moved).
* Tier e = the 30% partial module on the VERBATIM-named code (tier a text): per file a contiguous block of functions
  (start by seeded hash), block sizes by largest remainder to hit round(0.3 N) overall; a removed function stays as a
  prototype if its name is still used by remaining text, else is deleted; files with no kept function are dropped.
* truth rows are all definitions of the donor modules (not only eligible ones); ``eligible`` and ``span`` are extra columns.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SEED = 20261122
REPO = Path(__file__).resolve().parents[1]
CLANG_FORMAT = "/srv/storage_16tb/projects/doom-e7-work/e9/venv/bin/clang-format"
CLANG_VERSION = "18.1.8"
CF_CONFIG = REPO / "manifest" / "e9_clang_format.yaml"
CTAGS = "/usr/bin/ctags"
E7 = Path("/srv/storage_16tb/projects/doom-e7-work")
W = E7 / "e9" / "spike"
S9 = E7 / "e9" / "results" / "spike"
RECIPIENT = E7 / "repos" / "chocolate-doom"
E7_FP = E7 / "results" / "e7" / "phaseA" / "fingerprints"
E8_MEASURE = "/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/measure"
SFS = "/srv/storage_16tb/projects/structural-fingerprint-scanner/src"
MIN_LOC_FP = 3
ELIGIBLE_LOC = 6

# curl: the pool checkout is at another commit; doom-e7-work/repos/curl holds the E7 pin (read via git show <pin>:path)
DONORS = {
    "curl": dict(repo=E7 / "repos" / "curl", pin="01798a002debb5018d693f7fe6237968218eb808", subdir="lib",
                 target=150, size="large"),
    "libuv": dict(repo=E7 / "halflife" / "controls" / "libuv", pin="f08538cca14f73e30c89625e473fea3f5f55e300",
                  subdir="src/unix", target=50, size="small"),
}
TIERS = ["a", "b50", "b100", "c", "d", "e"]
TRUTH_COLS = ["tier", "module_size", "donor", "orig_func", "renamed_func", "donor_file", "recipient_file", "kept",
              "recipient_engine_row", "eligible", "span"]
BASELINE = "chocolate-spike-base"


# The engine honours the recipient's own .gitignore (chocolate-doom ignores 'lib'): spike/curl/lib/ is silently skipped by
# the scan (verified: zero spike rows). curl's donor directory lib/ is therefore placed at spike/curl/libsrc/.
RECIPIENT_SUBDIR = {"curl": ("lib", "libsrc")}


def recipient_rel(donor: str, rel: str) -> str:
    a, b = RECIPIENT_SUBDIR.get(donor, (None, None))
    if a and rel.startswith(a + "/"):
        rel = b + rel[len(a):]
    return f"spike/{donor}/{rel}"


def copy_tier(donor: str, tier: str, root: Path) -> None:
    for p in sorted((W / "tiers" / donor / tier).rglob("*.c")):
        rel = str(p.relative_to(W / "tiers" / donor / tier))
        dst = root / recipient_rel(donor, rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)


def program_name(donor: str, tier: str) -> str:
    return f"chocolate-spike-{donor}-{tier}"


# ------------------------------------------------------------------ lexing

_TOK = re.compile(
    r'(?P<bc>/\*.*?\*/)|(?P<lc>//(?:\\\n|[^\n])*)|(?P<str>"(?:\\.|[^"\\\n])*")|(?P<chr>\'(?:\\.|[^\'\\\n])*\')'
    r'|(?P<id>[A-Za-z_][A-Za-z_0-9]*)|(?P<num>\.?[0-9](?:[eEpP][+-]|[A-Za-z_0-9.])*)',
    re.S,
)
_WORD = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


def tokens(text: str):
    """Yield (kind, start, end): bc, lc, str, chr, id, num. Everything else is skipped."""
    for m in _TOK.finditer(text):
        yield m.lastgroup, m.start(), m.end()


def strip_comments(text: str) -> str:
    """Remove comments, leave string and character literals intact. A block comment becomes one space (tokens never
    fuse), a line comment is removed up to (not including) its newline; trailing blanks left behind are trimmed."""
    out, last, touched = [], 0, False
    for kind, s, e in tokens(text):
        if kind in ("bc", "lc"):
            out.append(text[last:s])
            out.append(" " if kind == "bc" else "")
            last = e
            touched = True
    out.append(text[last:])
    res = "".join(out)
    return re.sub(r"[ \t]+\n", "\n", res) if touched else res


def mask(text: str) -> str:
    """Same-length copy with comments and literal contents blanked (newlines kept): for structural scans."""
    out = list(text)
    for kind, s, e in tokens(text):
        if kind in ("bc", "lc", "str", "chr"):
            for i in range(s, e):
                if out[i] != "\n":
                    out[i] = " "
    return "".join(out)


# ------------------------------------------------------------------ ctags


def ctags_funcs_text(text: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.c"
        p.write_text(text)
        return ctags_funcs(p)


def ctags_funcs(path: Path) -> list[dict]:
    r = subprocess.run([CTAGS, "--output-format=json", "--fields=+ne", "--kinds-C=f", "--language-force=C",
                        "-f", "-", str(path)], capture_output=True, text=True, errors="replace")
    out = []
    for line in r.stdout.splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("_type") == "tag" and d.get("kind") == "function":
            out.append(dict(name=d["name"], line=int(d["line"]), end=int(d.get("end", d["line"]))))
    out.sort(key=lambda d: (d["line"], d["name"]))
    return out


# ------------------------------------------------------------------ renaming


def new_name(key: str) -> str:
    return "s9_" + hashlib.sha1((str(SEED) + key).encode()).hexdigest()[:8]


def _is_member(text: str, s: int) -> bool:
    pre = text[max(0, s - 40):s].rstrip()
    return (pre.endswith(".") and not pre.endswith("..")) or pre.endswith("->")


def rename_text(text: str, mapping: dict[str, str]) -> str:
    """Word-boundary replacement (whole identifier tokens, so no substring damage) in code and comments; never inside
    string/char literals and never for a struct member access (``.name`` / ``->name``)."""
    if not mapping:
        return text
    out, last = [], 0
    for kind, s, e in tokens(text):
        if kind == "id":
            nn = mapping.get(text[s:e])
            if nn is not None and not _is_member(text, s):
                out += [text[last:s], nn]
                last = e
        elif kind in ("bc", "lc"):
            seg = text[s:e]
            new = _WORD.sub(lambda m: mapping.get(m.group(0), m.group(0)), seg)
            if new != seg:
                out += [text[last:s], new]
                last = e
    out.append(text[last:])
    return "".join(out)


def build_rename_plan(defs: dict[str, list[dict]]) -> dict:
    """defs: relpath -> function dicts. key = name (defined in exactly one file) or name@relpath (several files)."""
    files_of: dict[str, set] = {}
    for rel, fs in defs.items():
        for f in fs:
            files_of.setdefault(f["name"], set()).add(rel)
    keymap: dict[str, str] = {}
    seen: dict[str, str] = {}
    for rel in sorted(defs):
        for f in defs[rel]:
            key = f["name"] if len(files_of[f["name"]]) == 1 else f"{f['name']}@{rel}"
            if key in keymap:
                continue
            nn, k = new_name(key), 0
            while nn in seen:  # 8-hex collision between two keys: probe deterministically
                k += 1
                nn = new_name(f"{key}#{k}")
            seen[nn] = key
            keymap[key] = nn
    return dict(files_of=files_of, keymap=keymap)


def def_key(name: str, rel: str, plan: dict) -> str:
    return name if len(plan["files_of"][name]) == 1 else f"{name}@{rel}"


def subset_keys(keys, tag: str, frac: float) -> set[str]:
    order = sorted(keys, key=lambda k: hashlib.sha1(f"{SEED}:{tag}:{k}".encode()).hexdigest())
    return set(order[: int(len(order) * frac)])


def apply_rename(files: dict[str, str], plan: dict, chosen: set[str]) -> dict[str, str]:
    """Global keys apply in every file, per-file keys (name@rel) only in their own file."""
    glob = {k: v for k, v in plan["keymap"].items() if k in chosen and "@" not in k}
    out = {}
    for rel, text in files.items():
        local = {k.split("@")[0]: v for k, v in plan["keymap"].items() if k in chosen and k.endswith("@" + rel)}
        out[rel] = rename_text(text, {**glob, **local})
    return out


# ------------------------------------------------------------------ formatter


def check_formatter() -> str:
    r = subprocess.run([CLANG_FORMAT, "--version"], capture_output=True, text=True)
    if CLANG_VERSION not in r.stdout:
        raise RuntimeError(f"pinned clang-format {CLANG_VERSION} required, got {r.stdout.strip()!r}")
    return r.stdout.strip()


def clang_format(text: str, config: Path = CF_CONFIG) -> str:
    r = subprocess.run([CLANG_FORMAT, f"--style=file:{config}", "--assume-filename=x.c"], input=text,
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("clang-format failed: " + r.stderr[:300])
    return r.stdout


# ------------------------------------------------------------------ function extents

_TYPE_LINE = re.compile(r"^[A-Za-z_][A-Za-z_0-9\s\*]*$")


def func_start_line(mlines: list[str], name_line: int) -> int:
    """0-based first line of a definition whose name is on 1-based ``name_line``: walk up over return-type lines."""
    i = name_line - 1
    while i > 0:
        prev = mlines[i - 1].strip()
        if not prev or not _TYPE_LINE.match(prev) or prev in ("else", "do"):
            break
        i -= 1
    return i


def pp_depth(mlines: list[str]) -> list[int]:
    """depth[i] = #if nesting before line i; depth[len] after the last line."""
    depth, res = 0, []
    for ln in mlines:
        res.append(depth)
        m = re.match(r"\s*#\s*(\w+)", ln)
        if m:
            if m.group(1) in ("if", "ifdef", "ifndef"):
                depth += 1
            elif m.group(1) == "endif":
                depth = max(0, depth - 1)
    res.append(depth)
    return res


def extents(text: str) -> list[dict]:
    """Function definitions with 0-based inclusive line extents [s, e]; ``movable`` = top level, outside any #if,
    not overlapping another extent."""
    lines = text.split("\n")
    mlines = mask(text).split("\n")
    depth = pp_depth(mlines)
    res = []
    for f in ctags_funcs_text(text):
        s = func_start_line(mlines, f["line"])
        e = min(f["end"] - 1, len(lines) - 1)
        res.append(dict(name=f["name"], line=f["line"], s=s, e=e, movable=(depth[s] == 0 and depth[e + 1] == 0 and e >= s)))
    res.sort(key=lambda d: (d["s"], d["e"]))
    for i in range(1, len(res)):
        if res[i]["s"] <= res[i - 1]["e"]:
            res[i]["movable"] = res[i - 1]["movable"] = False
    return res


def body_open_offsets(text: str, funcs: list[dict]) -> list[int]:
    """Offset just after the opening ``{`` of each function body (found in masked text), or -1."""
    m = mask(text)
    starts = [0]
    for ln in m.split("\n"):
        starts.append(starts[-1] + len(ln) + 1)
    res = []
    for f in funcs:
        off = starts[f["line"] - 1]
        mm = re.search(r"\b" + re.escape(f["name"]) + r"\b", m[off: off + 4000])
        j = m.find("(", off + mm.end()) if mm else -1
        if j < 0:
            res.append(-1)
            continue
        d = 0
        while j < len(m):
            d += (m[j] == "(") - (m[j] == ")")
            if d == 0:
                break
            j += 1
        k = j
        while k < len(m) and m[k] not in "{;":
            k += 1
        res.append(k + 1 if k < len(m) and m[k] == "{" else -1)
    return res


def insert_void0(text: str) -> str:
    """Insert ``(void)0;`` as the first statement of every function body."""
    offs = body_open_offsets(text, ctags_funcs_text(text))
    for o in sorted({o for o in offs if o >= 0}, reverse=True):
        text = text[:o] + "\n(void)0;" + text[o:]
    return text


def reorder_functions(text: str, rel: str = "") -> str:
    """Permute the movable function extents among the movable slots by a seeded hash order (gaps stay in place)."""
    lines = text.split("\n")
    ex = [d for d in extents(text) if d["movable"]]
    if len(ex) < 2:
        return text
    chunks = [lines[d["s"]: d["e"] + 1] for d in ex]
    order = sorted(range(len(ex)), key=lambda i: hashlib.sha1(f"{SEED}:d:{rel}:{ex[i]['name']}:{i}".encode()).hexdigest())
    res, last = [], 0
    for slot, src in zip(ex, order):
        res.extend(lines[last: slot["s"]])
        res.extend(chunks[src])
        last = slot["e"] + 1
    res.extend(lines[last:])
    return "\n".join(res)


def partial_module(files: dict[str, str], frac: float = 0.3) -> tuple[dict[str, str], set]:
    """Tier e. Returns (new files, kept set of (rel, name, line-in-input)). Contiguous blocks per file."""
    info = {rel: extents(text) for rel, text in files.items()}
    n_tot = sum(len(v) for v in info.values())
    quota = {rel: frac * len(v) for rel, v in info.items()}
    k = {rel: int(q) for rel, q in quota.items()}
    rest = round(frac * n_tot) - sum(k.values())
    for rel in sorted(quota, key=lambda r: (-(quota[r] - int(quota[r])), hashlib.sha1(f"{SEED}:e:{r}".encode()).hexdigest())):
        if rest <= 0:
            break
        if k[rel] < len(info[rel]):
            k[rel] += 1
            rest -= 1
    new, kept = {}, set()
    for rel, text in files.items():
        ex, kk = info[rel], k[rel]
        if kk == 0:
            continue
        off = int(hashlib.sha1(f"{SEED}:e:off:{rel}".encode()).hexdigest(), 16) % (len(ex) - kk + 1)
        keep_idx = set(range(off, off + kk))
        lines = text.split("\n")
        removed = {d["s"]: d for i, d in enumerate(ex) if i not in keep_idx}
        gone = set()
        for d in removed.values():
            gone.update(range(d["s"], d["e"] + 1))
        remaining = "\n".join(ln for j, ln in enumerate(lines) if j not in gone)
        used = {remaining[s:e] for kind, s, e in tokens(mask(remaining)) if kind == "id"}
        out, j = [], 0
        while j < len(lines):
            d = removed.get(j)
            if d is None:
                if j not in gone:
                    out.append(lines[j])
                j += 1
                continue
            if d["name"] in used:  # keep a declaration so remaining call sites stay valid
                head = "\n".join(lines[d["s"]: d["e"] + 1])
                b = mask(head).find("{")
                out.append(head[:b].rstrip() + ";" if b > 0 else head)
            j = d["e"] + 1
        new[rel] = "\n".join(out)
        kept.update((rel, ex[i]["name"], ex[i]["line"]) for i in keep_idx)
    return new, kept


# ------------------------------------------------------------------ donor selection


def git_show(repo: Path, pin: str, path: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "show", f"{pin}:{path}"], capture_output=True,
                          check=True).stdout.decode("utf-8", errors="replace")


def git_list_c(repo: Path, pin: str, subdir: str) -> list[str]:
    r = subprocess.run(["git", "-C", str(repo), "ls-tree", "--name-only", f"{pin}:{subdir}"], capture_output=True,
                       text=True, check=True)
    return sorted(f"{subdir}/{n}" for n in r.stdout.split("\n") if n.endswith(".c"))


def select_module(donor: str) -> dict:
    d = DONORS[donor]
    files, defs, texts, n_elig = [], {}, {}, 0
    for rel in git_list_c(d["repo"], d["pin"], d["subdir"]):
        text = git_show(d["repo"], d["pin"], rel)
        fs = ctags_funcs_text(text)
        for f in fs:
            f["span"] = f["end"] - f["line"] + 1
            f["eligible"] = int(f["span"] >= ELIGIBLE_LOC)
        files.append(rel)
        defs[rel], texts[rel] = fs, text
        n_elig += sum(f["eligible"] for f in fs)
        if n_elig >= d["target"]:
            break
    return dict(donor=donor, files=files, defs=defs, texts=texts, n_eligible=n_elig,
                n_functions=sum(len(v) for v in defs.values()))


# ------------------------------------------------------------------ tiers


def make_tiers(mod: dict) -> dict:
    """tier -> dict(files=relpath->text[, kept=set]); plus _plan, _b50. Deterministic."""
    plan = build_rename_plan(mod["defs"])
    keys = sorted(plan["keymap"])
    orig = mod["texts"]
    b50 = subset_keys(keys, "b50", 0.5)
    t = {"a": dict(files=dict(orig))}
    t["b50"] = dict(files=apply_rename(orig, plan, b50))
    t["b100"] = dict(files=apply_rename(orig, plan, set(keys)))
    c = {rel: clang_format(strip_comments(tx)) for rel, tx in t["b100"]["files"].items()}
    t["c"] = dict(files=c)
    t["d"] = dict(files={rel: reorder_functions(clang_format(insert_void0(tx)), rel) for rel, tx in c.items()})
    e_files, kept = partial_module(orig)
    t["e"] = dict(files=e_files, kept=kept)
    t["_plan"], t["_b50"] = plan, b50
    return t


def truth_rows(mod: dict, tiers: dict) -> list[dict]:
    plan, b50 = tiers["_plan"], tiers["_b50"]
    d = DONORS[mod["donor"]]
    rows = []
    for tier in TIERS:
        for rel in mod["files"]:
            for f in sorted(mod["defs"][rel], key=lambda x: (x["line"], x["name"])):
                key = def_key(f["name"], rel, plan)
                new = plan["keymap"][key]
                if tier in ("a", "e"):
                    rn = f["name"]
                elif tier == "b50":
                    rn = new if key in b50 else f["name"]
                else:
                    rn = new
                kept = int((rel, f["name"], f["line"]) in tiers["e"]["kept"]) if tier == "e" else 1
                rows.append(dict(tier=tier, module_size=d["size"], donor=mod["donor"], orig_func=f["name"],
                                 renamed_func=rn, donor_file=rel, recipient_file=recipient_rel(mod["donor"], rel),
                                 kept=kept, recipient_engine_row="", eligible=f["eligible"], span=f["span"]))
    return rows


def write_tier_files(donor: str, tiers: dict) -> None:
    for tier in TIERS:
        root = W / "tiers" / donor / tier
        if root.exists():
            shutil.rmtree(root)
        for rel, text in tiers[tier]["files"].items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)


# ------------------------------------------------------------------ recipients and scans

GIT_ENV = dict(GIT_AUTHOR_NAME="e9", GIT_AUTHOR_EMAIL="e9@example.invalid", GIT_COMMITTER_NAME="e9",
               GIT_COMMITTER_EMAIL="e9@example.invalid", GIT_AUTHOR_DATE="2026-11-22T00:00:00+00:00",
               GIT_COMMITTER_DATE="2026-11-22T00:00:00+00:00")


def assemble(donor: str | None, tier: str | None) -> tuple[str, Path, str]:
    """Scratch recipient = chocolate-doom export (copy, no .git) + spike/<donor>/ files, committed in its own scratch
    repo (so the E8 runner's ``git archive`` step is used unchanged). Returns (program, dir, commit)."""
    prog = BASELINE if donor is None else program_name(donor, tier)
    root = W / "recipients" / prog
    if root.exists() and not (root / ".git").exists():
        shutil.rmtree(root)
    if donor is not None and (root / "spike").exists():  # always refresh the donor files from the tier output
        shutil.rmtree(root / "spike")
        copy_tier(donor, tier, root)
    if not (root / ".git").exists():
        shutil.copytree(RECIPIENT, root, ignore=shutil.ignore_patterns(".git"))
        if donor is not None:
            copy_tier(donor, tier, root)
        env = {**os.environ, **GIT_ENV}
        cmds = [["init", "-q"], ["add", "-A"]] + ([["add", "-A", "-f", "spike"]] if donor else []) + [["commit", "-q", "-m", prog]]
        for cmd in cmds:  # -f: the recipient's .gitignore lists 'lib', which would hide spike/curl/lib
            subprocess.run(["git", "-C", str(root), *cmd], check=True, env=env, capture_output=True)
    else:
        env = {**os.environ, **GIT_ENV}
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True, env=env, capture_output=True)
        if donor:
            subprocess.run(["git", "-C", str(root), "add", "-A", "-f", "spike"], check=True, env=env, capture_output=True)
        if subprocess.run(["git", "-C", str(root), "diff", "--cached", "--quiet"], env=env).returncode:
            subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", prog + " (refresh)"], check=True, env=env,
                           capture_output=True)
    sha = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True,
                         check=True).stdout.strip()
    return prog, root, sha


def scan_all(programs: list[tuple[str, Path, str]], workers: int) -> dict:
    sys.path.insert(0, E8_MEASURE)
    import e8_snap
    from concurrent.futures import ThreadPoolExecutor
    out_root = S9 / "snaps"
    out_root.mkdir(parents=True, exist_ok=True)
    jobs = [dict(sha=sha, scope_key=prog, repo=str(root), port=prog) for prog, root, sha in programs]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        metas = list(ex.map(lambda t: e8_snap.run_task(t, out_root), jobs))
    res = {}
    for (prog, _, sha), m in zip(programs, metas):
        res[prog] = dict(tag=e8_snap.tag(sha, prog), rc=m.get("rc"), ctags_functions=m.get("ctags_functions"),
                         seconds=m.get("seconds"), sha=sha)
    (S9 / "scan_status.json").write_text(json.dumps(res, indent=1, sort_keys=True))
    return res


def fingerprint_all(scans: dict) -> dict:
    sys.path.insert(0, SFS)
    import glob
    from structural_fingerprint.fingerprint import Fingerprint, build, safe_name
    from structural_fingerprint.reference import load_reference
    from structural_fingerprint.scan_io import load_scan
    ref = load_reference("structure")
    fpd = S9 / "fingerprints"
    fpd.mkdir(parents=True, exist_ok=True)
    tabs = {}
    for prog, m in scans.items():
        p = fpd / f"{safe_name(prog)}.sfp.json"
        if not p.exists():
            dbs = sorted(glob.glob(str(S9 / "snaps" / m["tag"] / "*_galaxy_master.db"))) if m["rc"] == 0 else []
            if not dbs:
                continue
            build(load_scan(Path(dbs[0]), ref.signal_columns, name=prog), ref, min_loc=MIN_LOC_FP).save(fpd)
        tabs[prog] = Fingerprint.load(p)
    for donor in DONORS:  # donor programs = the E7 fingerprints (curl, libuv exist there), copied unchanged
        for ext in (".sfp.json", ".sfp.npz"):
            src, dst = E7_FP / f"{donor}{ext}", fpd / f"{donor}{ext}"
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
    return tabs


def attach_engine_rows(rows: list[dict], tabs: dict) -> dict:
    """recipient_engine_row = row index in the spiked program's FunctionTable by (path, name); duplicate (path, name)
    pairs are matched in truth (file) order."""
    index = {}
    for prog, fp in tabs.items():
        d: dict = {}
        for i, (p, n) in enumerate(zip(fp.functions.path.tolist(), fp.functions.name.tolist())):
            d.setdefault((p, n), []).append(i)
        index[prog] = d
    used: dict = {}
    for r in rows:
        prog = program_name(r["donor"], r["tier"])
        r["recipient_engine_row"] = ""
        if prog not in index or not int(r["kept"]):
            continue
        key = (prog, r["recipient_file"], r["renamed_func"])
        lst = index[prog].get(key[1:], [])
        n = used.get(key, 0)
        if n < len(lst):
            r["recipient_engine_row"] = lst[n]
        used[key] = n + 1
    stats = {}
    for prog in index:
        sub = [r for r in rows if program_name(r["donor"], r["tier"]) == prog and int(r["kept"])]
        stats[prog] = dict(kept_rows=len(sub), matched=sum(r["recipient_engine_row"] != "" for r in sub))
    return stats


def write_truth(rows: list[dict]) -> Path:
    S9.mkdir(parents=True, exist_ok=True)
    p = S9 / "spike_truth.csv"
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=TRUTH_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return p


# ------------------------------------------------------------------ build / check


def build_all(workers: int, scan: bool) -> None:
    ver = check_formatter()
    print("formatter:", ver, flush=True)
    S9.mkdir(parents=True, exist_ok=True)
    W.mkdir(parents=True, exist_ok=True)
    rows, sel = [], {}
    for donor in DONORS:
        mod = select_module(donor)
        tiers = make_tiers(mod)
        write_tier_files(donor, tiers)
        rows += truth_rows(mod, tiers)
        sel[donor] = dict(pin=DONORS[donor]["pin"], repo=str(DONORS[donor]["repo"]), files=mod["files"],
                          n_functions=mod["n_functions"], n_eligible=mod["n_eligible"])
        print(donor, "files", len(mod["files"]), "functions", mod["n_functions"], "eligible", mod["n_eligible"], flush=True)
    (S9 / "spike_donor_files.json").write_text(json.dumps(
        dict(seed=SEED, clang_format=ver, config_sha1=hashlib.sha1(CF_CONFIG.read_bytes()).hexdigest(), donors=sel),
        indent=1))
    write_truth(rows)
    programs = [assemble(None, None)] + [assemble(d, t) for d in DONORS for t in TIERS]
    (S9 / "spike_programs.csv").write_text("program,dir,commit\n" + "".join(f"{p},{r},{s}\n" for p, r, s in programs))
    if not scan:
        return
    scans = scan_all(programs, workers)
    for p, m in scans.items():
        print("scan", p, "rc", m["rc"], "ctags", m["ctags_functions"], "s", m["seconds"], flush=True)
    tabs = fingerprint_all(scans)
    stats = attach_engine_rows(rows, tabs)
    write_truth(rows)
    (S9 / "engine_row_match.json").write_text(json.dumps(stats, indent=1, sort_keys=True))
    print("fingerprints:", len(tabs), "programs; engine-row matches:", json.dumps(stats), flush=True)


def definition_count(text: str, name: str) -> int:
    return sum(1 for f in ctags_funcs_text(text) if f["name"] == name)


def old_name_in_code(text: str, name: str) -> bool:
    """True if ``name`` still occurs as an identifier in code (outside comments, strings, member accesses)."""
    m = mask(text)
    return any(m[s:e] == name and not _is_member(m, s) for kind, s, e in tokens(m) if kind == "id")


def check_all() -> dict:
    rep: dict = {"formatter": check_formatter()}
    donors = json.loads((S9 / "spike_donor_files.json").read_text())["donors"]
    truth = list(csv.DictReader(open(S9 / "spike_truth.csv")))
    for donor, info in donors.items():
        rep[donor] = {}
        n_orig = sum(len(ctags_funcs_text(git_show(DONORS[donor]["repo"], info["pin"], rel))) for rel in info["files"])
        for tier in TIERS:
            root = W / "tiers" / donor / tier
            files = {str(p.relative_to(root)): p.read_text() for p in root.rglob("*.c")}
            n = sum(len(ctags_funcs_text(tx)) for tx in files.values())
            rows = [r for r in truth if r["donor"] == donor and r["tier"] == tier]
            ren = [r for r in rows if r["renamed_func"] != r["orig_func"] and r["kept"] == "1"]
            grouped: dict = {}
            for r in ren:
                grouped.setdefault((r["donor_file"], r["renamed_func"]), []).append(r)
            bad = sum(definition_count(files[rel], nn) != len(rs) for (rel, nn), rs in grouped.items())
            multi = sum(len(rs) > 1 for rs in grouped.values())
            leaked = sum(old_name_in_code(files[r["donor_file"]], r["orig_func"]) for r in ren)
            by_orig = {(r["donor_file"], r["orig_func"]) for r in ren}
            injective = len({(r["donor_file"], r["renamed_func"]) for r in ren}) == len(by_orig) or multi > 0
            rep[donor][tier] = dict(
                ctags_functions=n, original_functions=n_orig, expected=sum(r["kept"] == "1" for r in rows),
                count_ok=(n == sum(r["kept"] == "1" for r in rows)), renamed_definitions=len(ren),
                renamed_names_with_several_defs_same_file=multi, definition_count_mismatch=bad,
                orig_name_left_in_code=leaked, files=len(files), mapping_injective_per_file=injective)
    sc = S9 / "scan_status.json"
    if sc.exists():
        rep["scans"] = {p: dict(rc=m["rc"], ctags_functions=m["ctags_functions"]) for p, m in json.loads(sc.read_text()).items()}
    em = S9 / "engine_row_match.json"
    if em.exists():
        rep["engine_row_match"] = json.loads(em.read_text())
    rep["loc_changed_tier_c_vs_b100"] = loc_changed(truth)
    (S9 / "spike_check.json").write_text(json.dumps(rep, indent=1, sort_keys=True))
    print(json.dumps(rep, indent=1, sort_keys=True))
    return rep


def loc_changed(truth: list[dict]) -> dict:
    """Functions whose engine loc differs between tier b100 and tier c (same functions, matched via the truth rows)."""
    sys.path.insert(0, SFS)
    from structural_fingerprint.fingerprint import Fingerprint, safe_name
    out = {}
    for donor in DONORS:
        try:
            tb, tc = (Fingerprint.load(S9 / "fingerprints" / f"{safe_name(program_name(donor, t))}.sfp.json").functions
                      for t in ("b100", "c"))
        except Exception:
            continue
        rb, rc = ({(r["donor_file"], r["orig_func"], i): r["recipient_engine_row"] for i, r in enumerate(truth)
                   if r["donor"] == donor and r["tier"] == t and r["recipient_engine_row"] != ""} for t in ("b100", "c"))
        rb = {k[:2]: v for k, v in rb.items()}
        rc = {k[:2]: v for k, v in rc.items()}
        both = sorted(set(rb) & set(rc))
        out[donor] = dict(compared=len(both),
                          changed=sum(int(tb.loc[int(rb[k])]) != int(tc.loc[int(rc[k])]) for k in both))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build", "check"])
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--no-scan", action="store_true")
    a = ap.parse_args(argv)
    build_all(a.workers, not a.no_scan) if a.mode == "build" else check_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
