"""Build the schemata build of Managed Doom (C#): every lesion in the Doom/World files is a runtime switch (E13_MUT=<id>); entry counters and early abort included.
Usage: python build_cs.py <out_dir>   (screen-venv python). Writes <out_dir>/e13-managed-doom.dll (+ deps) and manifest.json."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H))
import schemata
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); DOTNET = W / "tools/dotnet/dotnet"
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); tree = out / "tree"
if tree.exists(): shutil.rmtree(tree)
(tree).mkdir(); shutil.copytree(W / "build/managed-doom/src", tree / "src"); shutil.copy(W / "build/managed-doom/E13.csproj", tree / "E13.csproj")
shutil.copy(H.parent / "managed/E13Digest.cs", tree / "src/E13Digest.cs"); shutil.copy(H / "E13Mut.cs", tree / "src/E13Mut.cs")
files = sorted((tree / "src/Doom/World").glob("*.cs")); orig = {f: f.read_bytes() for f in files}; drops = {f: set() for f in files}; base = {}; idb = fnb = 0; info = {}
env = dict(os.environ, DOTNET_CLI_HOME=str(W / "tools/dotnet_home"), DOTNET_NOLOGO="1", DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_ROOT=str(W / "tools/dotnet"))
def spans(text):
    res = []
    for m in re.finditer(r"\(E13Mut\.On\((\d+)\) \?", text):
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
        res.append((i, j, int(m.group(1))))
    return res
texts = {}
def gen(f):
    t, rows, fns, nid, nfn = schemata.instrument(orig[f], "csharp", base[f][0], base[f][1], frozenset(drops[f])); f.write_text(t, encoding="latin-1"); texts[f] = t; info[f] = (rows, fns)
for f in files:   # first pass assigns fixed id ranges
    base[f] = (idb, fnb); t, rows, fns, nid, nfn = schemata.instrument(orig[f], "csharp", idb, fnb); idb, fnb = nid, nfn; info[f] = (rows, fns); texts[f] = t; f.write_text(t, encoding="latin-1")
for it in range(25):
    r = subprocess.run([str(DOTNET), "build", "-c", "Release", "-o", str(out / "bin"), "-nologo"], cwd=tree, capture_output=True, text=True, env=env)
    if r.returncode == 0: break
    errs = set(re.findall(r"^(.*?\.cs)\((\d+),(\d+)\): error", r.stdout, re.M)); changed = set()
    for path, ln, col in errs:
        f = Path(path)
        if f not in texts: raise SystemExit("error outside the instrumented files:\n" + r.stdout[-1500:])
        lines = texts[f].split("\n"); off = sum(len(x) + 1 for x in lines[int(ln) - 1 - 0:0]) 
        off = sum(len(x) + 1 for x in lines[:int(ln) - 1]) + int(col) - 1
        inside = [(e - s0, i) for s0, e, i in spans(texts[f]) if s0 <= off <= e]
        if inside: drops[f].add(min(inside)[1]); changed.add(f)
        # a literal that stops being a compile-time constant breaks implicit conversions (e.g. Angle / 2): also drop the constant lesions on the error line
        lstart = sum(len(x) + 1 for x in lines[:int(ln) - 1]); lend = lstart + len(lines[int(ln) - 1])
        for m in re.finditer(r"\(E13Mut\.On\((\d+)\) \? \((\d+)\) : \((\d+)\)\)", texts[f]):
            if lstart <= m.start() <= lend and int(m.group(1)) not in drops[f]: drops[f].add(int(m.group(1))); changed.add(f)
    if not changed: raise SystemExit("compile error not attributable to a lesion:\n" + r.stdout[-1800:])
    for f in changed: gen(f)
    print(f"iteration {it}: dropped {sum(len(v) for v in drops.values())} lesions so far", flush=True)
else: raise SystemExit("compile loop did not converge")
rows_all, fns_all, dropped = [], [], []
for f in files:
    rows, fns = info[f]
    for row in rows:
        row["file"] = f.stem
        (dropped if row["id"] in drops[f] else rows_all).append(row)
    for fn in fns: fn["file"] = f.stem; fns_all.append(fn)
json.dump(dict(sites=rows_all, functions=fns_all, dropped=[dict(id=d["id"], file=d["file"], fn=d["fn"], op=d["op"], kind=d["kind"]) for d in dropped]), open(out / "manifest.json", "w"))
print("built", out / "bin/e13-managed-doom.dll", "|", len(rows_all), "lesions in", len(fns_all), "functions;", len(dropped), "dropped")
