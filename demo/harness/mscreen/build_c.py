"""Build the schemata binary of chocolate-doom (16 simulation files): one binary, every lesion a runtime switch.
Usage: python build_c.py <out_dir>   (screen-venv python). Writes <out_dir>/chocolate-doom, manifest.json (sites, functions, dropped)."""
import json, re, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); sys.path.insert(0, str(H.parent / "difflocalize"))
import schemata, mutate
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); comp, link = mutate.commands(); SRC = mutate.SRCDIR
def compile_cmd(stem, srcfile, obj):
    c = re.sub(r"-MD -MT \S+ -MF \S+", "", comp[stem]); c = re.sub(r" -o \S+\.o ", f" -o {obj} ", c); c = re.sub(r" -c \S+$", f" -include {H / 'e13_screen.h'} -c {srcfile}", c); return c
def spans(text):
    """[(start, end, id)] of every '(E13_ON(id) ? ... )' schema, by balanced parentheses (quotes skipped)"""
    out = []
    for m in re.finditer(r"\(E13_ON\((\d+)\) \?", text):
        i = m.start(); depth = 0; q = None; j = i
        while j < len(text):
            ch = text[j]
            if q:
                if ch == "\\": j += 1
                elif ch == q: q = None
            elif ch in "\"'": q = ch
            elif ch == "(": depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0: break
            j += 1
        out.append((i, j, int(m.group(1))))
    for m in re.finditer(r"\{ if \(!E13_ON\((\d+)\)\) \{", text):
        i = m.start(); depth = 0; q = None; j = i
        while j < len(text):
            ch = text[j]
            if q:
                if ch == "\\": j += 1
                elif ch == q: q = None
            elif ch in "\"'": q = ch
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        out.append((i, j, int(m.group(1))))
    return out
def attribute(text, line, col):
    lines = text.split("\n"); off = sum(len(x) + 1 for x in lines[:line - 1]) + col - 1
    inside = [(e - s0, i) for s0, e, i in spans(text) if s0 <= off <= e]
    return {min(inside)[1]} if inside else set()
rows_all, fns_all, dropped, objs = [], [], [], []; idb = fnb = 0; id2b = 10000
for stem in mutate.FILES:
    src = (SRC / f"{stem}.c").read_bytes(); drop = set(); tmp = SRC / f"_scr_{stem}.c"; obj = out / f"{stem}.o"
    for attempt in range(12):
        text, rows, fns, nid, nfn, nid2 = schemata.instrument(src, "c", idb, fnb, frozenset(drop), id2b); tmp.write_text(text, encoding="latin-1")
        r = subprocess.run(compile_cmd(stem, tmp, obj), shell=True, cwd=mutate.BUILD, capture_output=True, text=True)
        if r.returncode == 0: break
        newly = set()
        for m in re.finditer(r"_scr_\w+\.c:(\d+):(\d+): error", r.stderr): newly |= attribute(text, int(m.group(1)), int(m.group(2)))
        if not newly: tmp.unlink(missing_ok=True); raise SystemExit(f"{stem}: compile error not attributable to a lesion:\n{r.stderr[-800:]}")
        drop |= newly
    else: raise SystemExit(f"{stem}: compile loop did not converge")
    tmp.unlink(missing_ok=True)
    for row in rows:
        row["file"] = stem
        if row["id"] in drop: dropped.append(dict(id=row["id"], file=stem, fn=row["fn"], line=row["line"], op=row["op"], kind=row["kind"]))
    for f in fns: f["file"] = stem
    rows_all += [x for x in rows if x["id"] not in drop]; fns_all += fns; idb, fnb, id2b = nid, nfn, nid2; objs.append(obj); print(stem, len(rows) - len(drop), "sites kept,", len(drop), "dropped,", len(fns), "functions", flush=True)
scr = out / "e13_screen.o"; c = re.sub(r"-MD -MT \S+ -MF \S+", "", comp[mutate.FILES[0]]); c = re.sub(r" -o \S+\.o ", f" -o {scr} ", c); c = re.sub(r" -c \S+$", f" -c {H / 'e13_screen.c'}", c)
r = subprocess.run(c, shell=True, cwd=mutate.BUILD, capture_output=True, text=True); assert r.returncode == 0, r.stderr[-500:]
marker = " src/CMakeFiles/chocolate-doom.dir/i_main.c.o "; binp = out / "chocolate-doom"
l = link.replace(marker, marker + " " + " ".join(map(str, objs + [scr])) + " ", 1); l = re.sub(r"-Wl,--dependency-file=\S+", "", l); l = l.replace(" -o src/chocolate-doom ", f" -o {binp} ")
r = subprocess.run(l, shell=True, cwd=mutate.BUILD, capture_output=True, text=True); assert r.returncode == 0 and binp.exists(), r.stderr[-800:]
json.dump(dict(sites=rows_all, functions=fns_all, dropped=dropped), open(out / "manifest.json", "w"))
print("built", binp, "|", len(rows_all), "lesions in", len(fns_all), "functions;", len(dropped), "dropped")
