"""E15 C-family replication: the registered pipeline with prboom-plus in place of managed-doom (near-clone, same language). Usage: python run_cfamily.py <out_dir>"""
import json, os, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from roles import *; from graphs import *; from pipeline import *
S = W / "screen"; SCANS = W.parent / "scans/704cb35f0"
def funcs(man): return pd.DataFrame([dict(fid=f["fid"], name=f["name"], file=f["file"]) for f in man["functions"]])
def main():
    out_dir = Path(sys.argv[1]); out_dir.mkdir(parents=True, exist_ok=True)
    mc, mp = json.load(open(S / "choc_v2/manifest.json")), json.load(open(S / "pb_v2/manifest.json")); fc, fp = funcs(mc), funcs(mp)
    A = load_port("chocolate-doom", os.environ.get("E15_CHOC_DB", str(S / "choc_phenotypes.sqlite"))); B = load_port("prboom-plus", os.environ.get("E15_PB_DB", str(S / "pb_phenotypes.sqlite")))
    ea = g1_edges(next((SCANS / "chocolate-doom").glob("*master.db"))) | g2_chocolate(); eb = g1_edges(next((SCANS / "prboom-plus").glob("*master.db"))) | g2_chocolate()
    out = analyze(A, B, Graph(fc.fid, fc.name, ea), Graph(fp.fid, fp.name, eb), fc, fp, B_perm=int(os.environ.get("E15_BPERM", "10000")), b_is_c=True); v = verdicts(out)
    md = ["# E15 C-family replication (chocolate-doom vs prboom-plus)\n", f"usable functions {out['n_eligible']}; hot {out['hot']}; inert {out['inert']}; name-agree pairs {out['pairs']}\n", "| prediction | observed | result |\n|---|---|---|"] + [f"| {p} | {o} | {r} |" for p, o, r in v]
    (out_dir / "E15_CFAMILY.md").write_text("\n".join(md)); print("\n".join(md)[:2500])
if __name__ == "__main__": main()
