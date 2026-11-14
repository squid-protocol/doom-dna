import ast
import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def test_followup_scripts_parse():
    for p in sorted((ROOT / "followups").glob("*/measure.py")):
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))


def test_collapse_short_wrappers():
    path = ROOT / "followups" / "oop-function-collapse" / "measure.py"
    spec = importlib.util.spec_from_file_location("doom_e1_measure", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # 0 (loc 20) -> 1 (loc 2 wrapper) -> 2 (loc 15) -> 3 (loc 3 leaf, no callees: must stay)
    edges = np.array([[0, 1], [1, 2], [2, 3]], dtype=np.int32)
    loc = np.array([20, 2, 15, 3], dtype=np.int32)
    new_edges, keep = mod.collapse_short_wrappers(edges, loc, max_loc=5)

    assert keep.tolist() == [True, False, True, True]
    assert new_edges.tolist() == [[0, 2], [2, 3]]
