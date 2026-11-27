"""Functions whose source text is identical (comments and whitespace ignored) between chocolate-doom and prboom-plus, by name, in the 16 screened simulation files. Writes screen/pb_identical_functions.json.
Usage: python identical_functions.py   (screen-venv python)"""
import difflib, json, re, sys
from pathlib import Path
import tree_sitter_language_pack as tsp
W = Path("/srv/storage_16tb/projects/doom-e7-work/demo-study"); FILES = "p_enemy p_map p_maputl p_sight p_mobj p_user p_pspr p_inter p_doors p_floor p_ceilng p_spec p_switch p_plats p_lights p_telept".split()
P = tsp.get_parser("c")
def funcs(path):
    src = path.read_bytes(); t = P.parse(src); out = {}
    def walk(n):
        if n.type == "function_definition":
            d = n.child_by_field_name("declarator")
            while d is not None and d.type != "identifier":
                nd = d.child_by_field_name("declarator"); d = nd if nd is not None else (d.children[0] if d.children else None)
            if d is not None and d.type == "identifier":
                toks = []
                def leaves(x):
                    if x.type == "comment": return
                    if not x.children: toks.append(x.text.decode("latin-1")); return
                    for c in x.children: leaves(c)
                leaves(n); out.setdefault(d.text.decode(), " ".join(toks))
            return
        for c in n.children: walk(c)
    walk(t.root_node); return out
ident, differ, only, near = {}, [], [], []
for stem in FILES:
    a = funcs(W / "build/choc-mut-base/src/src/doom" / f"{stem}.c"); b = funcs(W / "build/prboom-plus/src/prboom2/src" / f"{stem}.c")
    for n in sorted(set(a) & set(b)):
        if a[n] == b[n]: ident[n] = stem
        else:
            differ.append(n); ta, tb = a[n].split(), b[n].split()
            if abs(len(ta) - len(tb)) <= 0.2 * max(len(ta), len(tb)) and difflib.SequenceMatcher(None, ta, tb, autojunk=False).ratio() >= 0.9: near.append(n)
    only += [n for n in b if n not in a]
print(f"same name in both: {len(ident) + len(differ)}; identical text: {len(ident)}; near-identical (>= 0.9 token similarity): {len(near)}; same name but different text: {len(differ)}; prboom-only functions: {len(only)}")
json.dump(dict(identical=sorted(ident), near_identical=sorted(near), different=sorted(differ), pb_only=sorted(only)), open(W / "screen/pb_identical_functions.json", "w"), indent=0)
