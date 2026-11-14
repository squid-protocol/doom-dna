import ast
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_and_lineage_consistent():
    manifest_path = ROOT / "manifest" / "manifest.csv"
    lineage_path = ROOT / "manifest" / "declared_lineage.csv"
    assert manifest_path.exists()
    assert lineage_path.exists()

    with manifest_path.open(newline="", encoding="utf-8") as f:
        ports = {row["name"] for row in csv.DictReader(f)}
    assert len(ports) >= 44
    assert "linuxdoom" in ports

    with lineage_path.open(newline="", encoding="utf-8") as f:
        lineage_rows = list(csv.DictReader(f))
    assert len(lineage_rows) > 0
    for row in lineage_rows:
        assert row["name"] in ports, f"declared_lineage port {row['name']} missing from manifest.csv"
        if row["parent"]:
            assert row["parent"] in ports, f"declared_lineage parent {row['parent']} missing from manifest.csv"


def test_json_artifacts_valid():
    for rel in ("manifest/subsystems.json", "article/data.json", "results/blind_placement.json"):
        path = ROOT / rel
        assert path.exists(), f"missing {rel}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, (dict, list))


def test_measure_scripts_compile():
    measure_dir = ROOT / "measure"
    scripts = sorted(measure_dir.glob("*.py"))
    assert len(scripts) > 0
    for script in scripts:
        ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
