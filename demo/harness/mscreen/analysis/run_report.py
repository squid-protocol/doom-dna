"""E15 results page from the real data (same seeds and permutation count as the registered run). Usage: python run_report.py <out.html>"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_e15 import context
from pipeline import analyze
from report_html import build
def main():
    A, B, GA, GB, fc, fm = context(); out = analyze(A, B, GA, GB, fc, fm, B_perm=int(os.environ.get("E15_BPERM", "10000")))
    build(out, GA, GB, (fc.set_index("fid"), fm.set_index("fid")), sys.argv[1], title="Do function roles form call-graph neighbourhoods that recur across ports? (E15 results)"); print("wrote", sys.argv[1])
if __name__ == "__main__": main()
