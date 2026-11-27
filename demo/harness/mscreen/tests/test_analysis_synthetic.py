"""Validation of the E15 analysis pipeline on synthetic screens (no real data). Run: python -m pytest demo/harness/mscreen/tests -q   (e11 venv python, a few minutes)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import synth
from pipeline import analyze, verdicts
def results(out): return {p.split()[0] + (" " + p.split()[1] if p.startswith("H2") else ""): r for p, o, r in verdicts(out)}
def test_planted_structure_is_recovered():
    v = results(synth.run(planted=True, swap=0.2, B_perm=1000))
    assert v["PC1g"].startswith("PASSED") and v["PC1f"].startswith("PASSED")
    assert v["H1a"].startswith("PASSED") and v["H3"].startswith("PASSED") and v["H4"].startswith("PASSED")
    assert all(r.startswith("PASSED") for k, r in v.items() if k.startswith("H2"))
def test_no_structure_fails_the_gate_and_labels_exploratory():
    v = results(synth.run(planted=False, B_perm=1000))
    assert v["H1a"].startswith("FAILED") and all("exploratory" in r for k, r in v.items() if k.startswith("H2") or k == "H3")
def test_destroyed_roles_lower_recurrence():
    hi = synth.run(planted=True, swap=0.0, B_perm=500)["h3"]["ami"]; lo = synth.run(planted=True, swap=0.8, B_perm=500)["h3"]["ami"]
    assert hi > lo + 0.3
def test_subset_views_run():
    A, B, GA, GB, fa, fb = synth.build(planted=True)
    dm = [d for d in A.demos if d[0] in "sc"]; a, b = A.subset(demos=dm), B.subset(demos=dm)
    assert a.demos == b.demos and len(a.demos) == 30
    out = analyze(a, b, GA, GB, fa, fb, B_perm=300); assert out["pairs"] > 60
def test_exploratory_runs_on_synthetic():
    import csv, tempfile, numpy as np
    from run_exploratory import report
    A, B, GA, GB, fa, fb = synth.build(planted=True, swap=0.2); out = analyze(A, B, GA, GB, fa, fb, B_perm=300)
    rng = np.random.default_rng(1); f = tempfile.mktemp(suffix=".csv")
    with open(f, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["ref_name", "md_name", "md_tier"])
        for i in range(28, 150): w.writerow([f"P_func{i}x", f"func{i}x", rng.choice(["exact", "twin", "ext1", "ext2"])])
    text, aud = report(out, A, B, f, (fa.set_index("fid"), fb.set_index("fid")))
    assert "PC4" in text and "H6" in text and "aligned" in text
def test_report_page_is_well_formed():
    import re, tempfile, xml.dom.minidom
    from report_html import build
    A, B, GA, GB, fa, fb = synth.build(planted=True, swap=0.2); out = analyze(A, B, GA, GB, fa, fb, B_perm=300)
    path = tempfile.mktemp(suffix=".html"); doc = build(out, GA, GB, (fa.set_index("fid"), fb.set_index("fid")), path)
    svgs = re.findall(r"<svg.*?</svg>", doc, re.S); assert len(svgs) >= 5
    for sv in svgs: xml.dom.minidom.parseString(sv)       # each chart is well-formed XML
    assert "PASSED" in doc and "<title>Function roles screen</title>" in doc
if __name__ == "__main__":   # runs without pytest
    import time
    for name, fn in sorted((k, v) for k, v in dict(globals()).items() if k.startswith("test_")):
        t0 = time.time(); fn(); print(f"PASS {name} ({time.time() - t0:.0f}s)", flush=True)
