"""Build the schemata binary of prboom-plus (the same 16 simulation files): one binary, every lesion a runtime switch (PC2 near-clone control of E15).
Usage: python build_c_pb.py <out_dir>   (screen-venv python). Writes <out_dir>/prboom-plus, manifest.json (sites, functions, dropped)."""
import json, re, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H)); sys.path.insert(0, str(H.parent / "difflocalize"))
import schemata
schemata.GUARD_MISPARSE = True
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); BUILD = W / "build/prboom-plus/build"; SRC = W / "build/prboom-plus/src/prboom2/src"
FILES = "p_enemy p_map p_maputl p_sight p_mobj p_user p_pspr p_inter p_doors p_floor p_ceilng p_spec p_switch p_plats p_lights p_telept".split()
cmds = subprocess.run([str(W / "venv/bin/ninja"), "-t", "commands", "prboom-plus"], cwd=BUILD, capture_output=True, text=True).stdout.strip().split("\n"); link = cmds[-1]; comp = {}
for c in cmds[:-1]:
    m = re.search(r" -o src/CMakeFiles/prboom-plus\.dir/(\w+)\.c\.o ", c)
    if m: comp[m.group(1)] = c
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
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
for stem in FILES:
    src = (SRC / f"{stem}.c").read_bytes(); drop = set(); tmp = SRC / f"_scr_{stem}.c"; obj = out / f"{stem}.o"
    for attempt in range(12):
        text, rows, fns, nid, nfn, nid2 = schemata.instrument(src, "c", idb, fnb, frozenset(drop), id2b); tmp.write_text(text, encoding="latin-1")
        r = subprocess.run(compile_cmd(stem, tmp, obj), shell=True, cwd=BUILD, capture_output=True, text=True)
        if r.returncode == 0: break
        newly = set()
        for m in re.finditer(r"_scr_\w+\.c:(\d+):(\d+): error", r.stderr): newly |= attribute(text, int(m.group(1)), int(m.group(2)))
        if not newly: tmp.unlink(missing_ok=True); raise SystemExit(f"{stem}: compile error not attributable to a lesion:\n{(r.stderr or r.stdout)[-1500:]}")
        drop |= newly
    else: raise SystemExit(f"{stem}: compile loop did not converge")
    tmp.unlink(missing_ok=True)
    for row in rows:
        row["file"] = stem
        if row["id"] in drop: dropped.append(dict(id=row["id"], file=stem, fn=row["fn"], line=row["line"], op=row["op"], kind=row["kind"]))
    for f in fns: f["file"] = stem
    rows_all += [x for x in rows if x["id"] not in drop]; fns_all += fns; idb, fnb, id2b = nid, nfn, nid2; objs.append(obj); print(stem, len(rows) - len(drop), "sites kept,", len(drop), "dropped,", len(fns), "functions", flush=True)
scr = out / "e13_screen.o"; c = re.sub(r"-MD -MT \S+ -MF \S+", "", comp[FILES[0]]); c = re.sub(r" -o \S+\.o ", f" -o {scr} ", c); c = re.sub(r" -c \S+$", f" -c {H / 'e13_screen.c'}", c)
r = subprocess.run(c, shell=True, cwd=BUILD, capture_output=True, text=True); assert r.returncode == 0, r.stderr[-500:]
binp = out / "prboom-plus"; l = link
for stem, obj in zip(FILES, objs): assert f"src/CMakeFiles/prboom-plus.dir/{stem}.c.o" in l; l = l.replace(f"src/CMakeFiles/prboom-plus.dir/{stem}.c.o", str(obj))
l = re.sub(r"-Wl,--dependency-file=\S+", "", l); l = l.replace(" -o prboom-plus ", f" -o {binp} ", 1); l = l.replace("-O3 -DNDEBUG ", f"-O3 -DNDEBUG {scr} ", 1)
r = subprocess.run(l, shell=True, cwd=BUILD, capture_output=True, text=True); assert r.returncode == 0 and binp.exists(), r.stderr[-1200:]
json.dump(dict(sites=rows_all, functions=fns_all, dropped=dropped), open(out / "manifest.json", "w"))
print("built", binp, "|", len(rows_all), "lesions in", len(fns_all), "functions;", len(dropped), "dropped")
