"""Build the schemata build of Mocha Doom (Java): every lesion in the simulation files is a runtime switch (E13_MUT=<id>); entry counters, site counters and early abort included.
Usage: python build_java.py <out_dir>   (screen-venv python). Writes <out_dir>/bin/base (all uninstrumented classes + e13.E13Mut + e13.Digest) and <out_dir>/bin/inst (the instrumented
classes; classpath = bin/inst:bin/base) and <out_dir>/manifest.json (same layout as build_cs.py). The Mocha source in demo-study/build/mochadoom is copied, never modified.
Instrumented files: every .java under p/Actions (the P_* action code: monsters, weapons, doors, floors, ceilings, plats, lights, movement, sight, spawns, teleport, use/shoot events),
p/Specials.java, p/UnifiedGameMap.java, p/ActionFunctions.java, p/MapUtils.java."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H))
import schemata, schemata_java
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study")
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); tree = out / "tree"
if tree.exists(): shutil.rmtree(tree)
for d in ("bin",):
    if (out / d).exists(): shutil.rmtree(out / d)
tree.mkdir(); shutil.copytree(W / "build/mochadoom/src", tree / "src", ignore=shutil.ignore_patterns("*.class"))
src = tree / "src"; BASE, INST = out / "bin/base", out / "bin/inst"; BASE.mkdir(parents=True); INST.mkdir(parents=True)
# --- runtime + digest hook (our code; the Mocha files only get the three patches below) ---
shutil.copy(H / "E13Mut.java", src / "e13/E13Mut.java")
dg = (H.parent / "E13Digest.java").read_text()
dg = dg.replace("if (out == null) {", "if (out == null && !E13Mut.nodigest()) {", 1)
a = dg.index("out.write(d.gametic"); b = dg.index("if (++pending >= 64) { out.flush(); pending = 0; }") + len("if (++pending >= 64) { out.flush(); pending = 0; }")
write_stmt = dg[a:b]
val = ("long[] val = { d.gametic, d.leveltime, d.random.getIndex(), 0, pl.mo.x, pl.mo.y, pl.mo.z, (pl.mo.angle & 0xffffffffL), pl.health[0], pl.armorpoints[0], pl.readyweapon.ordinal(), "
       "pl.ammo[0], pl.ammo[1], pl.ammo[2], pl.ammo[3], nm, msum, sh, cm };\n            E13Mut.check(val);\n            if (out != null) { " + write_stmt + " }")
dg = dg[:a] + val + dg[b:]
assert dg.count("E13Mut") == 2, dg.count("E13Mut")
(src / "e13/Digest.java").write_text(dg)
eng = src / "mochadoom/Engine.java"; t = eng.read_text()
m = re.search(r"(catch\s*\(\s*Exception e\s*\)\s*\{\s*e\.printStackTrace\(\);)(\s*System\.exit\(1\);)", t); assert m, "Engine.main catch not found"
eng.write_text(t[:m.end(1)] + "\n            e13.E13Mut.crash();" + t[m.end(1):])
R = subprocess.run(["javac", "-nowarn", "-cp", ".", "-d", str(BASE), "mochadoom/Engine.java", "e13/Digest.java", "e13/E13Mut.java"], cwd=src, capture_output=True, text=True)
if R.returncode: raise SystemExit("base compile failed:\n" + R.stderr[-3000:])
# --- instrument ---
files = sorted(set((src / "p/Actions").rglob("*.java")) | {src / "p" / n for n in ("Specials.java", "UnifiedGameMap.java", "ActionFunctions.java", "MapUtils.java")})
orig = {f: f.read_bytes() for f in files}; drops = {f: set() for f in files}; why = {}; base = {}; idb = fnb = 0; id2b = 10000; info = {}; texts = {}
def gen(f):
    t, rows, fns, nid, nfn, nid2 = schemata.instrument(orig[f], "java", base[f][0], base[f][1], frozenset(drops[f]), base[f][2]); f.write_text(t, encoding="latin-1"); texts[f] = t; info[f] = (rows, fns)
for f in files:   # first pass assigns fixed id ranges (a drop never renumbers)
    base[f] = (idb, fnb, id2b); t, rows, fns, nid, nfn, nid2 = schemata.instrument(orig[f], "java", idb, fnb, frozenset(), id2b); idb, fnb, id2b = nid, nfn, nid2; info[f] = (rows, fns); texts[f] = t; f.write_text(t, encoding="latin-1")
assert idb < 10000 and id2b < (1 << 17), (idb, id2b)
def spans(text):
    """(start, end, id) of every lesion expression `(e13.E13Mut.On(id) ? ...)` and every deleted statement `{ if (!e13.E13Mut.On(id)) { ... } }`; comments, strings and chars are skipped."""
    res = []; pats = [(re.compile(r"\(e13\.E13Mut\.On\((\d+)\) \?"), "(", ")"), (re.compile(r"\{ if \(!e13\.E13Mut\.On\((\d+)\)\) \{"), "{", "}")]
    for rx, op, cl in pats:
        for m in rx.finditer(text):
            i = m.start(); depth = 0; j = i; n = len(text)
            while j < n:
                ch = text[j]
                if ch == "/" and text[j + 1:j + 2] == "/": j = text.find("\n", j); j = n if j < 0 else j
                elif ch == "/" and text[j + 1:j + 2] == "*": j = text.find("*/", j + 2) + 1
                elif ch in "\"'":
                    q = ch; j += 1
                    while j < n and text[j] != q: j += 2 if text[j] == "\\" else 1
                elif ch == op: depth += 1
                elif ch == cl:
                    depth -= 1
                    if depth == 0: break
                j += 1
            res.append((i, j, int(m.group(1))))
    return res
def offset(text, ln, col):   # javac raw diagnostics: 1-based line, 1-based column with tabs expanded to multiples of 8
    lines = text.split("\n"); base_off = sum(len(x) + 1 for x in lines[:ln - 1]); c = 0
    for k, ch in enumerate(lines[ln - 1]):
        if c + 1 >= col: return base_off + k
        c = (c // 8 * 8 + 8) if ch == "\t" else c + 1
    return base_off + len(lines[ln - 1])
def method_region(T, off):
    k = T.rfind("e13.E13Mut.Enter(", 0, off); k2 = T.find("e13.E13Mut.Enter(", off)
    return (k if k >= 0 else 0), (k2 if k2 >= 0 else len(T))
byname = {f.name: f for f in files}; assert len(byname) == len(files), 'duplicate file names: javac raw diagnostics print the base name only'
stats = {"flow_method": 0, "line_const": 0, "span": 0, "assign_sdl": 0, "escalated": 0}; seen = {}
pending = list(files)
for it in range(60):
    for f in pending: gen(f)
    pending = []
    r = subprocess.run(["javac", "-nowarn", "-XDrawDiagnostics", "-Xmaxerrs", "100000", "-encoding", "ISO-8859-1", "-cp", str(BASE), "-d", str(INST)] + [str(f.relative_to(src)) for f in files], cwd=src, capture_output=True, text=True)
    if r.returncode == 0: break
    errs = re.findall(r"^(\S+\.java):(\d+):(\d+): compiler\.err\.([\w.]+):?\s*(.*)$", r.stdout + r.stderr, re.M); changed = set()
    if os.environ.get("JV_VERBOSE"): import collections; print(collections.Counter(e[3] for e in errs), flush=True)
    if not errs: raise SystemExit("javac failed without attributable errors:\n" + (r.stdout + r.stderr)[-2500:])
    done_now = set()
    for path, ln, col, key, rest in errs:
        if (path, ln, key, rest) in done_now: continue   # the same error at several columns of one line counts once per iteration
        done_now.add((path, ln, key, rest))
        f = byname.get(Path(path).name)
        if f is None: raise SystemExit(f"error outside the instrumented files: {path}:{ln}:{col} {key} {rest}\n" + (r.stdout + r.stderr)[-1500:])
        T = texts[f]; off = offset(T, int(ln), int(col)); sp = spans(T); n0 = len(drops[f]); tag = (f, int(ln), key); seen[tag] = seen.get(tag, 0) + 1; lo, hi = method_region(T, off)
        inside = [(e - s0, i) for s0, e, i in sp if s0 <= off <= e and i not in drops[f]]
        flow = key.startswith("var.") or key in ("unreachable.stmt", "missing.ret.stmt", "initializer.must.be.able.to.complete.normally", "cant.assign.val.to.var")   # flow errors sit at the use, not at the lesion
        if inside and not flow and seen[tag] == 1: drops[f].add(min(inside)[1]); stats["span"] += 1
        if key in ("unreachable.stmt", "missing.ret.stmt", "initializer.must.be.able.to.complete.normally") or (not inside and not flow and seen[tag] == 1):   # reachability / missing return: the condition negations of this method
            for s0, e, i in sp:
                if lo <= s0 <= hi and T[s0:s0 + 40].startswith("(e13.E13Mut.On(") and re.match(r"\(e13\.E13Mut\.On\(\d+\) \? !\(", T[s0:s0 + 60]): drops[f].add(i)
            stats["flow_method"] += 1
        if key in ("var.might.not.have.been.initialized", "var.might.already.be.assigned", "cant.assign.val.to.var", "var.not.initialized.in.default.constructor"):   # a deleted assignment broke definite assignment
            nm = re.search(r"([A-Za-z_]\w*)", rest)
            if nm:
                name = nm.group(1); pat = re.compile(r"\{ if \(!e13\.E13Mut\.On\(\d+\)\) \{\s*" + re.escape(name) + r"\s*=(?!=)")   # only a plain assignment to the variable can have established its definite assignment
                for s0, e, i in sp:
                    if lo <= s0 <= hi and pat.match(T, s0): drops[f].add(i); stats["assign_sdl"] += 1
        if key in ("prob.found.req", "incomparable.types", "illegal.start.of.expr", "not.stmt", "limit.code", "operator.cant.be.applied", "operator.cant.be.applied.1"):   # a literal that stops being a compile-time constant breaks implicit narrowing: drop the constant lesions on the error line
            ls = T.rfind("\n", 0, off) + 1; le = T.find("\n", off); le = len(T) if le < 0 else le
            for m in re.finditer(r"\(e13\.E13Mut\.On\((\d+)\) \? \(?-?(\d+)\)? : \(?(\d+)\)?\)", T[ls:le]): drops[f].add(int(m.group(1))); stats["line_const"] += 1
        if seen[tag] >= 3 and len(drops[f]) == n0:   # escalate: every lesion on the error line, then every lesion of the method
            tgt = [(s0, e, i) for s0, e, i in sp if (T.rfind("\n", 0, s0) + 1) <= (T.rfind("\n", 0, off) + 1) <= e and i not in drops[f]] if seen[tag] == 3 else [(s0, e, i) for s0, e, i in sp if lo <= s0 <= hi and i not in drops[f]]
            for s0, e, i in tgt: drops[f].add(i)
            stats["escalated"] += 1
        if os.environ.get('JV_VERBOSE') == '2': print(' ', path, ln, key, rest, '| dropped', len(drops[f]) - n0, flush=True)
        if len(drops[f]) != n0: changed.add(f)
    if not changed: raise SystemExit("compile error not attributable to a lesion:\n" + (r.stdout + r.stderr)[-2000:])
    pending = list(changed)
    print(f"iteration {it}: {len(errs)} errors, dropped {sum(len(v) for v in drops.values())} lesions so far", flush=True)
else: raise SystemExit("compile loop did not converge")
rows_all, fns_all, dropped = [], [], []
for f in files:
    rows, fns = info[f]; rel = str(f.relative_to(src / "p"))[:-5]
    for row in rows: row["file"] = f.stem; row["path"] = rel; (dropped if row["id"] in drops[f] else rows_all).append(row)
    for fn in fns: fn["file"] = f.stem; fn["path"] = rel; fns_all.append(fn)
json.dump(dict(sites=rows_all, functions=fns_all, dropped=[dict(id=d["id"], file=d["file"], fn=d["fn"], op=d["op"], kind=d["kind"]) for d in dropped], stats=stats), open(out / "manifest.json", "w"))
print("built", out / "bin", "|", len(rows_all), "lesions in", len(fns_all), "functions;", len(dropped), "dropped;", stats)
