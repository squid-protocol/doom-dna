"""Build the schemata build of gore (Go translation of doomgeneric): every lesion in the simulation functions is a runtime switch (E13_MUT=<id>); entry counters and early abort included.
Usage: python build_go.py <out_dir>   (screen-venv python).  Default out_dir = screen/go_v2.  Writes
  <out_dir>/base/   the work copy of build/gore with our two small patches (digest rows -> e13Check, timedemo end -> e13Finish) and e13mut.go; the classical-rebuild base (original sources untouched)
  <out_dir>/tree/   the same with doom.go instrumented
  <out_dir>/bin/engine, <out_dir>/manifest.json (sites, functions, dropped with reasons), <out_dir>/facts.json (go/types facts)."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H))
import schemata, schemata_go
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); GO = W / "tools/go/bin/go"; SRC = W / "build/gore"
GOENV = {"PATH": "/usr/bin:/bin", "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=mod", "GOPATH": str(W / "tools/gopath"), "GOCACHE": str(W / "tools/gocache"), "GOPROXY": "off", "CGO_ENABLED": "0"}

def split_args(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([{": depth += 1
        elif ch in ")]}": depth -= 1
        if ch == "," and depth == 0: out.append(cur.strip()); cur = ""
        else: cur += ch
    out.append(cur.strip()); return out

def make_base(base):
    """Work copy of build/gore (never modified) + the screen patches. Returns the patched doom.go bytes."""
    if base.exists(): shutil.rmtree(base)
    (base / "cmd/e13").mkdir(parents=True)
    for f in ("doom.go", "go.mod", "go.sum", "e13digest.go"): shutil.copy(SRC / f, base / f)
    shutil.copy(SRC / "cmd/e13/main.go", base / "cmd/e13/main.go"); shutil.copy(H / "e13mut.go", base / "e13mut.go")
    d = (base / "e13digest.go").read_text()
    assert d.count("if e13file == nil {") == 1; d = d.replace("if e13file == nil {", "if e13file == nil && !e13NoDigest {")
    m = re.search(r'fmt\.Fprintf\(e13file, ("(?:[^"\\]|\\.)*"), (.*?)\)\n\}', d, re.S); assert m, "digest Fprintf not found"
    args = split_args(m.group(2)); assert len(args) == 18 and m.group(1).count("%d") == 18 and " 0 " in m.group(1), (len(args), m.group(1))
    vals = ["e13U(%s)" % a for a in args[:3]] + ["0"] + ["e13U(%s)" % a for a in args[3:]]
    new = "if !e13NoDigest {\n\t\t" + m.group(0)[:-2] + "\n\t}\n\te13Check([19]uint64{" + ", ".join(vals) + "})\n}"
    (base / "e13digest.go").write_text(d[:m.start()] + new + d[m.end():])
    t = (base / "doom.go").read_text(); a = 'i_Error("timed %d gametics'; assert t.count(a) == 1
    (base / "doom.go").write_text(t.replace(a, "e13Finish()\n\t\t" + a)); return (base / "doom.go").read_bytes()

def gobuild(d, out):
    return subprocess.run([str(GO), "build", "-gcflags=-e", "-o", str(out), "./cmd/e13"], cwd=d, capture_output=True, text=True, env=dict(GOENV, HOME=str(d)))

def spans(text):
    """[(start, end, id)] of every /*S<id>*/ ... /*E<id>*/ schema (a duplicated operand gives the id twice)."""
    out = []; st = []
    for m in re.finditer(r"/\*([SE])(\d+)\*/", text):
        if m.group(1) == "S": st.append((m.start(), int(m.group(2))))
        else:
            s0, i = st.pop(); assert i == int(m.group(2)); out.append((s0, m.end(), i))
    return out

def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else W / "screen/go_v2"); out.mkdir(parents=True, exist_ok=True); base = out / "base"; tree = out / "tree"
    orig = make_base(base)
    tools = out / "tools"; tools.mkdir(exist_ok=True)   # the go/types helper (gotypes/), built with the private Go toolchain
    for f in ("main.go", "go.mod"): shutil.copy(H / "gotypes" / f, tools / f)
    r = subprocess.run([str(GO), "build", "-o", "e13types", "."], cwd=tools, capture_output=True, text=True, env=dict(GOENV, HOME=str(tools)))
    if r.returncode: raise SystemExit("building e13types failed:\n" + r.stderr[-800:])
    r = subprocess.run([str(out / "tools/e13types"), str(base), "doom.go"], capture_output=True, text=True)
    if r.returncode: raise SystemExit("e13types failed " + r.stderr[-800:])
    facts = json.loads(r.stdout); (out / "facts.json").write_text(r.stdout); print("go/types facts:", {k: len(v) if hasattr(v, "__len__") else v for k, v in facts.items()}, r.stderr[:300])
    names = schemata_go.simulation_functions(orig); schemata_go.configure(facts, names); print(len(names), "simulation functions selected")
    if tree.exists(): shutil.rmtree(tree)
    shutil.copytree(base, tree)
    drop = set(); fx = tree / "doom.go"
    def gen():
        t, rows, fns, nid, nfn, nid2 = schemata.instrument(orig, "go", 0, 0, frozenset(drop), 10000); fx.write_bytes(t.encode("latin-1")); return t, rows, fns, nid, nfn, nid2
    text, rows, fns, nid, nfn, nid2 = gen()
    print("generated:", len(rows), "lesion rows,", len(fns), "functions,", len(text) // 1000, "KB")
    reasons = {}
    for it in range(40):
        r = gobuild(tree, out / "bin/engine")
        if r.returncode == 0: break
        errs = re.findall(r"^(?:\./)?doom\.go:(\d+):(\d+): (.*)$", r.stderr, re.M); other = [l for l in r.stderr.splitlines() if re.match(r"^(?!(?:\./)?doom\.go)\S+\.go:\d+", l)]
        if other: raise SystemExit("error outside doom.go:\n" + "\n".join(other[:5]))
        if not errs: raise SystemExit("build failed without a position:\n" + r.stderr[-1500:])
        lines = text.split("\n"); starts = [0]
        for l in lines: starts.append(starts[-1] + len(l) + 1)
        sp = spans(text); new = set()
        for ln, col, msg in errs:
            off = starts[int(ln) - 1] + int(col) - 1
            inside = [(e - s0, i) for s0, e, i in sp if s0 <= off < e]
            if inside: new.add(min(inside)[1]); continue
            m = re.search(r"declared and not used: (\w+)", msg)
            k = text.rfind("e13Enter(", 0, off); k2 = text.find("e13Enter(", off); hi = k2 if k2 >= 0 else len(text)
            if m and k >= 0:   # a deleted statement made a variable unused: drop the deletions in this function that mention it
                pat = re.compile(r"\b" + m.group(1) + r"\b")
                for s0, e, i in sp:
                    if k <= s0 < hi and text[s0:s0 + 22].startswith("/*S") and "{ if !e13On(" in text[s0:s0 + 40] and pat.search(text[s0:e]): new.add(i)
            elif "missing return" in msg and k >= 0:   # a deleted/negated statement broke terminating-statement analysis: drop the sdl and negations of this function
                for s0, e, i in sp:
                    if k <= s0 < hi and ("{ if !e13On(" in text[s0:s0 + 40] or "!= e13On(" in text[e - 30:e]): new.add(i)
            if not new: raise SystemExit("compile error not attributable to a lesion: %s:%s %s" % (ln, col, msg))
        for i in new: reasons[i] = "compile"
        drop |= new; text, rows, fns, nid, nfn, nid2 = gen(); print(f"iteration {it}: {len(errs)} errors, dropped {len(drop)} lesions so far", flush=True)
    else: raise SystemExit("compile loop did not converge")
    sites, dropped = [], []
    for row in rows:
        row["file"] = "doom"; row.pop("edit", None) if False else None
        why = row.get("pre_drop") or ("compile" if row["id"] in drop else None)
        (dropped if why else sites).append(dict(row, reason=why) if why else row)
    for f in fns: f["file"] = "doom"
    json.dump(dict(sites=sites, functions=fns, dropped=[dict(id=d["id"], file=d["file"], fn=d["fn"], op=d["op"], kind=d["kind"], reason=d["reason"]) for d in dropped]), open(out / "manifest.json", "w"))
    import collections
    print("built", out / "bin/engine", "|", len(sites), "lesions in", len(fns), "functions;", len(dropped), "dropped", dict(collections.Counter(d["reason"] for d in dropped)))
    print("lesions per kind:", dict(sorted(collections.Counter(s["kind"] for s in sites).items())))
main()
