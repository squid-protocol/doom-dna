"""DOOM-E10 simple-edit obfuscation suite builder (development suite).

Outcome-blind: builds the variants, inserts them into scratch copies of the recipient exactly as E9 did, scans them with
the E7 engine and verifies the BUILD only (ctags counts, edit counts, scan return codes). It runs NO twin search, name
matching, near-copy search or fingerprint comparison between a donor and a recipient.

    python e10_suite.py build --suite dev [--workers 3] [--no-scan]

Names are left unchanged (the case is a copier who keeps the code and edits it a little). Edits are applied definition by
definition using the ctags extents / body-open offsets of the E9 builder. New suites are added to the SUITES table.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

E9_MEASURE = "/srv/storage_16tb/projects/doom-dna-worktrees/e9-horizontal/measure"
if E9_MEASURE not in sys.path:
    sys.path.insert(0, E9_MEASURE)
import e9_spike as e9  # noqa: E402

E7 = Path("/srv/storage_16tb/projects/doom-e7-work")
E9_CF = Path("/srv/storage_16tb/projects/doom-dna-worktrees/e9-horizontal/manifest/e9_clang_format.yaml")

VARIANTS = ["E_comment", "E_blank", "E_kw", "E_stmt", "E_decl", "E_format", "E_combo1", "E_combo2", "E_verbatim"]

# Suite table: add another suite here (donors, recipient, formatter config, variants, work dir) without touching the code.
SUITES = {
    "dev": dict(
        work=E7 / "e10" / "dev",
        recipient=E7 / "repos" / "chocolate-doom",
        clang_config=E9_CF,
        variants=VARIANTS,
        prefix="chocolate-e10",
        donors={
            "curl": dict(repo=E7 / "repos" / "curl", pin="01798a002debb5018d693f7fe6237968218eb808", subdir="lib",
                         target=150, size="large"),
            "libuv": dict(repo=E7 / "halflife" / "controls" / "libuv", pin="f08538cca14f73e30c89625e473fea3f5f55e300",
                          subdir="src/unix", target=50, size="small"),
        },
    ),
}

TRUTH_COLS = ["variant", "module_size", "donor", "orig_func", "renamed_func", "donor_file", "recipient_file", "kept",
              "eligible", "span"]
EDITED = "edited"


# ------------------------------------------------------------------ edits (text -> (text, count))


def edit_comment(text: str) -> tuple[str, int]:
    """Rewrite the text of every comment to 'edited', keeping delimiters; strings and chars untouched."""
    out, last, n = [], 0, 0
    for kind, s, e in e9.tokens(text):
        if kind == "bc":
            out += [text[last:s], f"/* {EDITED} */"]
        elif kind == "lc":
            out += [text[last:s], f"// {EDITED}"]
        else:
            continue
        last, n = e, n + 1
    out.append(text[last:])
    return "".join(out), n


def _body_opens(text: str) -> list[int]:
    return sorted({o for o in e9.body_open_offsets(text, e9.ctags_funcs_text(text)) if o >= 0})


def insert_first(text: str, snippet: str) -> tuple[str, int]:
    """Insert ``snippet`` on its own line right after the opening brace of every function body."""
    offs = _body_opens(text)
    for o in reversed(offs):
        text = text[:o] + "\n" + snippet + text[o:]
    return text, len(offs)


def edit_kw(text: str) -> tuple[str, int]:
    return insert_first(text, "if (0) { }")


def edit_stmt(text: str) -> tuple[str, int]:
    return insert_first(text, "(void)0;")


def edit_decl(text: str) -> tuple[str, int]:
    return insert_first(text, "int e10_unused;")


def edit_blank(text: str) -> tuple[str, int]:
    """One blank line after every line ending with ';' (comments ignored) inside function bodies. Count = definitions
    that received at least one blank line."""
    funcs = e9.ctags_funcs_text(text)
    offs = e9.body_open_offsets(text, funcs)
    masked = e9.mask(text)
    mlines = masked.split("\n")
    starts = [0]
    for ln in mlines:
        starts.append(starts[-1] + len(ln) + 1)
    ex = {(d["name"], d["line"]): d for d in e9.extents(text)}
    marked: set[int] = set()
    n_def = 0
    for f, o in zip(funcs, offs):
        if o < 0:
            continue
        d = ex.get((f["name"], f["line"]))
        if d is None:
            continue
        first = text.count("\n", 0, o)
        hit = False
        for i in range(first, d["e"] + 1):
            m = mlines[i].rstrip()
            if not m.endswith(";") or m.lstrip().startswith("#") or starts[i] + len(m) <= o:
                continue
            marked.add(i)
            hit = True
        n_def += hit
    lines = text.split("\n")
    res = []
    for i, ln in enumerate(lines):
        res.append(ln)
        if i in marked:
            res.append("")
    return "\n".join(res), n_def


def make_format(config: Path):
    def edit_format(text: str) -> tuple[str, int]:
        return e9.clang_format(text, config), 1
    return edit_format


def apply_variant(variant: str, text: str, config: Path = E9_CF) -> tuple[str, dict]:
    """Apply a variant to one file. Returns (text, counts)."""
    fmt = make_format(config)
    steps = {
        "E_comment": [("comments", edit_comment)], "E_blank": [("blank_defs", edit_blank)],
        "E_kw": [("defs_edited", edit_kw)], "E_stmt": [("defs_edited", edit_stmt)],
        "E_decl": [("defs_edited", edit_decl)], "E_format": [("formatted", fmt)], "E_verbatim": [],
        "E_combo1": [("comments", edit_comment), ("blank_defs", edit_blank), ("formatted", fmt)],
        "E_combo2": [("comments", edit_comment), ("blank_defs", edit_blank), ("formatted", fmt),
                     ("defs_edited", edit_kw)],
    }[variant]
    counts: dict = {}
    for key, fn in steps:
        text, c = fn(text)
        counts[key] = counts.get(key, 0) + c
    return text, counts


# ------------------------------------------------------------------ build


def configure(suite: dict) -> Path:
    """Point the E9 builder at this suite (recipient, work dir, donors, program naming)."""
    work = suite["work"]
    e9.RECIPIENT = suite["recipient"]
    e9.W = work / "spike"
    e9.DONORS.update(suite["donors"])
    e9.program_name = lambda donor, variant: f"{suite['prefix']}-{donor}-{variant}"
    return work


def build(suite_name: str, workers: int = 3, scan: bool = True) -> None:
    suite = SUITES[suite_name]
    work = configure(suite)
    res = work / "results"
    res.mkdir(parents=True, exist_ok=True)
    ver = e9.check_formatter()
    print("formatter:", ver, flush=True)
    cfg = suite["clang_config"]
    rows, checks, programs = [], {}, []
    for donor in suite["donors"]:
        mod = e9.select_module(donor)
        d = suite["donors"][donor]
        print(donor, "files", len(mod["files"]), "functions", mod["n_functions"], "eligible", mod["n_eligible"], flush=True)
        base = mod["n_functions"]
        for v in suite["variants"]:
            root = e9.W / "tiers" / donor / v
            if root.exists():
                shutil.rmtree(root)
            tot: dict = {}
            n_fn = 0
            for rel in mod["files"]:
                new, c = apply_variant(v, mod["texts"][rel], cfg)
                for k, x in c.items():
                    tot[k] = tot.get(k, 0) + x
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(new)
                n_fn += len(e9.ctags_funcs_text(new))
            chk = dict(ctags_functions=n_fn, verbatim_functions=base, count_ok=(n_fn == base), files=len(mod["files"]))
            if v in ("E_comment", "E_combo1", "E_combo2"):
                chk["comments_rewritten"] = tot.get("comments", 0)
            for k in ("blank_defs", "defs_edited"):
                if k in tot:
                    chk["definitions_edited" if k == "defs_edited" else "definitions_with_blank_lines"] = tot[k]
            if v in ("E_blank", "E_combo1", "E_combo2"):
                chk["definitions_with_blank_lines"] = tot.get("blank_defs", 0)
            checks.setdefault(v, {})[donor] = chk
            for rel in mod["files"]:
                for f in sorted(mod["defs"][rel], key=lambda x: (x["line"], x["name"])):
                    rows.append(dict(variant=v, module_size=d["size"], donor=donor, orig_func=f["name"],
                                     renamed_func=f["name"], donor_file=rel,
                                     recipient_file=e9.recipient_rel(donor, rel), kept=1, eligible=f["eligible"],
                                     span=f["span"]))
            programs.append(e9.assemble(donor, v))
            print(" ", v, json.dumps(chk), flush=True)
    with open(res / "dev_truth.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=TRUTH_COLS)
        w.writeheader()
        w.writerows(rows)
    (res / "build_checks.json").write_text(json.dumps(checks, indent=1, sort_keys=True))
    status = {}
    if scan:
        sys.path.insert(0, e9.E8_MEASURE)
        import e8_snap
        from concurrent.futures import ThreadPoolExecutor
        out_root = res / "snaps"
        out_root.mkdir(parents=True, exist_ok=True)
        jobs = [dict(sha=sha, scope_key=prog, repo=str(root), port=prog) for prog, root, sha in programs]
        with ThreadPoolExecutor(max_workers=workers) as ex:
            metas = list(ex.map(lambda t: e8_snap.run_task(t, out_root), jobs))
        for (prog, _, sha), m in zip(programs, metas):
            status[prog] = dict(tag=e8_snap.tag(sha, prog), rc=m.get("rc"), ctags_functions=m.get("ctags_functions"),
                                seconds=m.get("seconds"), sha=sha)
            print("scan", prog, "rc", m.get("rc"), flush=True)
        (res / "scan_status.json").write_text(json.dumps(status, indent=1, sort_keys=True))
    with open(res / "dev_programs.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["program", "dir", "commit", "scan_tag"])
        for prog, root, sha in programs:
            w.writerow([prog, root, sha, status.get(prog, {}).get("tag", "")])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build"])
    ap.add_argument("--suite", default="dev", choices=sorted(SUITES))
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--no-scan", action="store_true")
    a = ap.parse_args(argv)
    build(a.suite, a.workers, not a.no_scan)
    return 0


if __name__ == "__main__":
    sys.exit(main())
