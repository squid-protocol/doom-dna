"""E15 registered sensitivity analyses (amendments A1, A2): the primary pipeline re-run on filtered views. Usage: python run_sensitivity.py <out_dir>   (after the screens finish and the primary run)
Views: original 42 demos; shareware-base 58 demos; Freedoom demos only; original lesions only (ids < 10000); per-lesion-class phenotypes (statement deletion; condition negation; operators and constants)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_e15 import context
from pipeline import analyze, verdicts
KINDS_SDL = ["sdl"]; KINDS_NEG = ["negate"]; KINDS_OPS = ["relational", "equality", "arithmetic", "logical", "constant", "const_zero", "const_dec", "const_toggle", "arith2", "bitwise", "not", "incdec"]
VIEWS = [("original 42 demos", dict(fam="scb")), ("shareware-base 58 demos", dict(fam="scbvxp")), ("Freedoom demos only", dict(fam="fg")), ("original lesions only", dict(ids="old")),
         ("statement-deletion lesions only", dict(kinds=KINDS_SDL)), ("condition-negation lesions only", dict(kinds=KINDS_NEG)), ("operator and constant lesions only", dict(kinds=KINDS_OPS))]
def main():
    out_dir = Path(sys.argv[1]); out_dir.mkdir(parents=True, exist_ok=True); A, B, GA, GB, fc, fm = context(); md = ["# E15 sensitivity analyses\n"]
    for label, v in VIEWS:
        kw = {}
        if "fam" in v: kw["demos"] = [d for d in A.demos if d[0] in v["fam"]]
        if "kinds" in v: kw["kinds"] = v["kinds"]
        if v.get("ids") == "old": kw["lesion_ids"] = set(A.res[A.res.lesion < 10000].lesion) | set(B.res[B.res.lesion < 10000].lesion)
        a, b = A.subset(**kw), B.subset(**kw)
        if a.demos != b.demos or not a.demos: md.append(f"## {label}\nnot run: no common demos\n"); continue
        try: res = verdicts(analyze(a, b, GA, GB, fc, fm, B_perm=2000))
        except Exception as e: md.append(f"## {label}\nnot run: {type(e).__name__}: {e}\n"); continue
        md += [f"## {label} ({len(a.demos)} demos)\n", "| prediction | observed | result |\n|---|---|---|"] + [f"| {p} | {o} | {r} |" for p, o, r in res] + [""]
    (out_dir / "E15_SENSITIVITY.md").write_text("\n".join(md)); print("\n".join(md)[:3000])
if __name__ == "__main__": main()
