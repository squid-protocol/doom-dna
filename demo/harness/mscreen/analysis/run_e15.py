"""E15 real-data run (registered analysis). Run ONLY after both screens have finished and the registration commit exists.
Usage: python run_e15.py <out_dir>   (e11 venv python). Reads screen/choc_phenotypes.sqlite and screen/md_phenotypes.sqlite read-only."""
import json, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from roles import *; from graphs import *; from pipeline import *
import os
S = W / "screen"; SCANS = W.parent / "scans/704cb35f0"
CHOC_DB = os.environ.get("E15_CHOC_DB", str(S / "choc_phenotypes.sqlite")); MD_DB = os.environ.get("E15_MD_DB", str(S / "md_phenotypes.sqlite")); CHOC_MAN = os.environ.get("E15_CHOC_MAN", str(S / "choc_v2/manifest.json")); MD_MAN = os.environ.get("E15_MD_MAN", str(S / "md_v2/manifest.json"))
def funcs(man): return pd.DataFrame([dict(fid=f["fid"], name=f["name"], file=f["file"]) for f in man["functions"]])
def context():
    mc, mm = json.load(open(CHOC_MAN)), json.load(open(MD_MAN)); fc, fm = funcs(mc), funcs(mm)
    A = load_port("chocolate-doom", CHOC_DB); B = load_port("managed-doom", MD_DB)
    ea = g1_edges(next((SCANS / "chocolate-doom").glob("*master.db"))) | g2_chocolate(); eb = g1_edges(next((SCANS / "managed-doom").glob("*master.db"))) | g2_managed()
    GA, GB = Graph(fc.fid, fc.name, ea), Graph(fm.fid, fm.name, eb)
    return A, B, GA, GB, fc, fm
def main():
    out_dir = Path(sys.argv[1]); out_dir.mkdir(parents=True, exist_ok=True)
    A, B, GA, GB, fc, fm = context(); out = analyze(A, B, GA, GB, fc, fm, B_perm=int(os.environ.get("E15_BPERM", "10000"))); v = verdicts(out)
    md = ["# E15 results (registered analysis)\n", f"usable functions (eligible, not hot, not inert): chocolate-doom {out['n_eligible'][0]}, managed-doom {out['n_eligible'][1]}; hot class {out['hot']}; inert class {out['inert']}; name-agree pairs {out['pairs']}\n", "| prediction | observed | result |\n|---|---|---|"] + [f"| {p} | {o} | {r} |" for p, o, r in v]
    (out_dir / "E15_RESULTS.md").write_text("\n".join(md)); json.dump({k: v for k, v in out.items() if k != "_ctx"}, open(out_dir / "E15_RESULTS.json", "w"), default=str, indent=1); print("\n".join(md))
if __name__ == "__main__": main()
