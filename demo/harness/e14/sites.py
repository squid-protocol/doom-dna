"""E14 generic mutation-site finder for C and C# (function spans, ordered sites, token-window alignment between ports)."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "difflocalize")); import mutate
CTRL = {"if", "for", "while", "switch", "foreach", "using", "lock", "catch", "fixed", "else", "do", "return", "sizeof", "when"}
KEYW = {"if", "else", "while", "for", "return", "break", "continue", "case", "switch", "null", "NULL", "true", "false", "new", "do", "goto"}

def functions(text):
    """{name: (body_start, body_end)} of top-level function bodies (also methods inside classes); first definition wins"""
    m = mutate.mask(text); out = {}; stack = []; header_start = 0; i = 0; n = len(m)
    while i < n:
        c = m[i]
        if c == "{":
            h = m[header_start:i].strip(); is_func = False; name = None
            if not any(k == "func" for k, _ in stack) and h.endswith(")") or (h and re.search(r"\)\s*(:\s*base\([^)]*\))?\s*$", h) and not any(k == "func" for k, _ in stack)):
                hh = re.sub(r"\s+", " ", h); mm = re.search(r"([A-Za-z_]\w*)\s*\([^()]*(?:\([^()]*\)[^()]*)*\)\s*(?::\s*base\([^)]*\))?\s*$", hh)
                if mm and mm.group(1) not in CTRL: is_func = True; name = mm.group(1)
            stack.append(("func" if is_func else "blk", (name, i)))
            header_start = i + 1
        elif c == "}":
            if stack:
                k, (name, st) = stack.pop()
                if k == "func" and name not in out: out[name] = (st + 1, i)
            header_start = i + 1
        elif c == ";" and not any(k == "func" for k, _ in stack): header_start = i + 1
        elif c == ";" : pass
        i += 1
    return out

def _tokens(m):
    m = m.replace("->", ".")
    return re.findall(r"[A-Za-z_]\w*|\d+|<<|>>|<=|>=|==|!=|&&|\|\||[-+*/<>=!&|(){}\[\];,.?:%^~]", m)

def norm_tok(t):
    if t in KEYW or not (t[0].isalpha() or t[0] == "_"): return "N" if t.isdigit() else t
    return "I"

def sites(text, span, csharp=False):
    """ordered mutation sites inside text[span]: dicts with abs start/end, old, new, kind, window"""
    m = mutate.mask(text); b0, b1 = span; out = []; body = m[b0:b1]
    for rx, table, kind in mutate.SITE_RES:
        for mm in rx.finditer(body):
            s, e = mm.start(2) + b0, mm.end(2) + b0; old = mm.group(2)
            if csharp and old in ("<", ">") and not (m[s - 1] == " " and m[e] == " "): continue
            out.append(dict(start=s, end=e, old=old, new=table[old], kind=kind))
    for mm in mutate.CONST_RE.finditer(body):
        v = int(mm.group(1)); s, e = mm.start(1) + b0, mm.end(1) + b0
        if 2 <= v < 100000 and m[s - 1:s] != "[": out.append(dict(start=s, end=e, old=mm.group(1), new=str(v + 1), kind="constant"))
    out.sort(key=lambda d: d["start"])
    for d in out:
        pre = _tokens(m[max(b0, d["start"] - 60):d["start"]])[-3:]; post = _tokens(m[d["end"]:min(b1, d["end"] + 60)])[:3]
        d["window"] = [norm_tok(t) for t in pre] + ["@"] + [norm_tok(t) for t in post]; d["pos"] = (d["start"] - b0) / max(1, b1 - b0)
    return out

def win_sim(a, b):
    ia, ib = a.index("@"), b.index("@"); sc = 0; tot = 0
    for k in (-3, -2, -1, 1, 2, 3):
        x = a[ia + k] if 0 <= ia + k < len(a) else None; y = b[ib + k] if 0 <= ib + k < len(b) else None
        tot += 1; sc += (x == y and x is not None)
    return sc / tot

def align(ref, tgt, min_score=0.5):
    """one-to-one alignment: same operator kind and old token; score = window similarity - 0.5*|relative position difference|"""
    pairs = []
    for i, r in enumerate(ref):
        for j, t in enumerate(tgt):
            if r["kind"] != t["kind"] or r["old"] != t["old"]: continue
            pairs.append((win_sim(r["window"], t["window"]) - 0.5 * abs(r["pos"] - t["pos"]), i, j))
    pairs.sort(reverse=True); ui, uj, out = set(), set(), {}
    for s, i, j in pairs:
        if s < min_score or i in ui or j in uj: continue
        ui.add(i); uj.add(j); out[i] = (j, round(s, 3))
    return out

def apply(text, d):
    assert text[d["start"]:d["end"]] == d["old"], (text[d["start"]:d["end"]], d["old"])
    return text[:d["start"]] + d["new"] + text[d["end"]:]

if __name__ == "__main__":
    W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study/build")
    tests = [("src/doom/p_enemy.c", "A_Chase", "prboom2/src/p_enemy.c", "A_Chase", "ManagedDoom/src/Doom/World/MonsterBehavior.cs", "Chase")]
    ref = (mutate.BASE / "src" / tests[0][0]).read_text(); pb = (W / "prboom-plus/src" / tests[0][2]).read_text(); md = (W / "managed-doom/src" / tests[0][4].replace("ManagedDoom/src/", "")).read_text()
    fr, fp, fm = functions(ref), functions(pb), functions(md); print(len(fr), len(fp), len(fm), "A_Chase" in fr, "A_Chase" in fp, "Chase" in fm)
    sr, sp, sm = sites(ref, fr["A_Chase"]), sites(pb, fp["A_Chase"]), sites(md, fm["Chase"], True); print("sites", len(sr), len(sp), len(sm))
    a = align(sr, sp); b = align(sr, sm); print("aligned to prboom", len(a), "to managed", len(b))
    for i in range(min(6, len(sr))): print(sr[i]["old"], sr[i]["kind"], sr[i]["window"], "->pb", a.get(i), "->md", b.get(i))
