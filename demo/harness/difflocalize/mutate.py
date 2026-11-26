"""Mutation machinery for validating the localiser: apply one small change to one function of the (patched, traced) reference engine and relink it.
Operators: relational (< <= > >=), == and !=, + and -, && and ||, integer constant + 1. The mutated function is known from the scanner's database."""
import os, random, re, shutil, subprocess, sys
from pathlib import Path
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); NINJA = W / "venv/bin/ninja"
BASE = W / "build/choc-mut-base"; BUILD = BASE / "build"; SRCDIR = BASE / "src/src/doom"
FILES = ["p_enemy", "p_map", "p_maputl", "p_sight", "p_mobj", "p_user", "p_pspr", "p_inter", "p_doors", "p_floor", "p_ceilng", "p_spec", "p_switch", "p_plats", "p_lights", "p_telept"]
_cmds = None
def commands():
    global _cmds
    if _cmds is None:
        lines = subprocess.check_output([str(NINJA), "-C", str(BUILD), "-t", "commands", "chocolate-doom"], text=True).splitlines()
        comp = {}
        for l in lines:
            m = re.search(r" -c (\S+/src/doom/(\w+)\.c)$", l)
            if m: comp[m.group(2)] = l
        _cmds = (comp, lines[-1])
    return _cmds

SITE_RES = [
    (re.compile(r"(?<![<>=!+\-*/&|^%\w])()(<=|>=|<|>)(?![<>=])()"), {"<": "<=", "<=": "<", ">": ">=", ">=": ">"}, "relational"),
    (re.compile(r"()(==|!=)()"), {"==": "!=", "!=": "=="}, "equality"),
    (re.compile(r"(?<=[\w)\]])\s*()(\+|-)(?![+\-=>])\s*(?=[\w(])()"), {"+": "-", "-": "+"}, "arithmetic"),
    (re.compile(r"()(&&|\|\|)()"), {"&&": "||", "||": "&&"}, "logical"),
    (re.compile(r"()(<<|>>)()"), {"<<": ">>", ">>": "<<"}, "shift"),
]
CONST_RE = re.compile(r"(?<![\w.\"'#])(\d+)(?![\w.\"'])")

def mask(text):
    """same-length copy with comments and string/char literals blanked, so offsets stay valid"""
    out = []; i = 0; n = len(text); st = "code"
    while i < n:
        c = text[i]; d = text[i:i + 2]
        if st == "code":
            if d == "/*": st = "block"; out.append("  "); i += 2; continue
            if d == "//": st = "line"; out.append("  "); i += 2; continue
            if c == '"': st = "str"; out.append(" "); i += 1; continue
            if c == "'": st = "chr"; out.append(" "); i += 1; continue
            out.append(c); i += 1
        elif st == "block":
            if d == "*/": st = "code"; out.append("  "); i += 2; continue
            out.append("\n" if c == "\n" else " "); i += 1
        elif st == "line":
            if c == "\n": st = "code"; out.append("\n")
            else: out.append(" ")
            i += 1
        else:
            q = '"' if st == "str" else "'"
            if c == "\\": out.append("  "); i += 2; continue
            if c == q: st = "code"
            out.append(" "); i += 1
    return "".join(out)

def sites(text):
    """mutation sites inside function bodies only (file-scope initializers and typedefs are excluded)"""
    m = mask(text); out = []; depth = 0; func_depths = []; header = ""
    for ln, line in enumerate(m.split("\n"), 1):
        s = line.strip()
        if s.startswith("#"): continue
        # track function bodies: a '{' at depth 0 opens a function if the text since the last ';' or '}' looks like a definition
        for ci, ch in enumerate(line):
            if ch == "{":
                if depth == 0:
                    h = header.strip(); is_func = "(" in h and ")" in h and "=" not in h and not re.match(r"^(typedef|struct|enum|union)\b", h)
                    func_depths.append(is_func)
                depth += 1; header = ""
            elif ch == "}":
                depth -= 1
                if depth == 0: header = ""; func_depths = []
            elif ch == ";" and depth == 0: header = ""
            elif depth == 0: header += ch
        if depth == 0 and not (func_depths and func_depths[-1]): header += "\n"
        inside = depth >= 1 and func_depths and func_depths[0]
        if not inside or not s or re.match(r"^(case\b|default\b)", s) or "I_Error" in s: continue
        for rx, table, kind in SITE_RES:
            for mm in rx.finditer(line): out.append((ln, mm.start(2), mm.end(2), mm.group(2), table[mm.group(2)], kind))
        for mm in CONST_RE.finditer(line):
            v = int(mm.group(1))
            if 2 <= v < 100000 and "[" not in line[max(0, mm.start() - 1):mm.start()]: out.append((ln, mm.start(1), mm.end(1), mm.group(1), str(v + 1), "constant"))
    return out

def apply(text, site):
    i, a, b, old, new, kind = site; lines = text.split("\n"); l = lines[i - 1]
    assert l[a:b] == old, (l, a, b, old)
    lines[i - 1] = l[:a] + new + l[b:]; return "\n".join(lines)

def build_mutant(file_stem, mutated_text, tag):
    """compile the mutated copy of one source file and relink; returns the binary path or None if it does not build"""
    comp, link = commands(); cmd = comp[file_stem]
    tmpsrc = SRCDIR / f"_mut_{tag}.c"; tmpsrc.write_text(mutated_text)
    outdir = W / "mut" / tag; outdir.mkdir(parents=True, exist_ok=True); obj = outdir / "m.o"; binp = outdir / "chocolate-doom"
    c = re.sub(r"-MD -MT \S+ -MF \S+", "", cmd); c = re.sub(r" -o \S+\.o ", f" -o {obj} ", c); c = re.sub(r" -c \S+$", f" -c {tmpsrc}", c)
    r = subprocess.run(c, shell=True, cwd=BUILD, capture_output=True, text=True); tmpsrc.unlink(missing_ok=True)
    if r.returncode: return None
    marker = " src/CMakeFiles/chocolate-doom.dir/i_main.c.o "; assert marker in link
    l = link.replace(marker, marker + f" {obj} ", 1)  # the doom sources live in a static library; an object listed first takes precedence over its archive member
    l = re.sub(r"-Wl,--dependency-file=\S+", "", l); l = l.replace(" -o src/chocolate-doom ", f" -o {binp} ")
    r = subprocess.run(l, shell=True, cwd=BUILD, capture_output=True, text=True)
    return binp if r.returncode == 0 and binp.exists() else None
