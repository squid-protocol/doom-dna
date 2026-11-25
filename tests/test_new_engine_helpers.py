"""Tests for the replication helpers (measure_new_engine/scan_programs.py, compare_scans.py)."""
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "measure_new_engine"))
import compare_scans  # noqa: E402
import scan_programs  # noqa: E402
from structural_fingerprint.reference import load_reference  # noqa: E402


def test_scratch_repo_tracks_ignored_files_and_drops_old_git(tmp_path):
    src = tmp_path / "src"
    (src / "sub").mkdir(parents=True)
    (src / ".gitignore").write_text("*.c\n")
    (src / "sub" / "a.c").write_text("int main(){return 0;}\n")
    (src / ".git").mkdir()
    (src / ".git" / "junk").write_text("x")
    (src / ".gitgalaxy").mkdir()
    (src / ".gitgalaxy" / "cache.db").write_text("x")
    dest = tmp_path / "dest"
    scan_programs.make_scratch_repo(src, dest)
    tracked = subprocess.run(["git", "-C", str(dest), "ls-files"], capture_output=True, text=True).stdout.split()
    assert "sub/a.c" in tracked  # git add -f -A keeps the ignored source
    assert not any(t.startswith(".gitgalaxy") for t in tracked)
    assert not (dest / ".git" / "junk").exists()


def _db(path, rows):
    ref = load_reference("structure")
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE file_data (id INTEGER, file_path TEXT, file_name TEXT, language TEXT, coding_loc INT)")
    cols = ", ".join(f"{s} INT" for s in ref.signal_columns)
    c.execute(f"CREATE TABLE function_data (id INTEGER, file_id INT, func_name TEXT, loc INT, complexity INT, args INT, {cols})")
    c.execute("INSERT INTO file_data VALUES (1, 'a.c', 'a.c', 'c', 100)")
    for i, (name, loc, sig) in enumerate(rows, 1):
        vals = ", ".join(str(sig if s == ref.signal_columns[0] else 0) for s in ref.signal_columns)
        c.execute(f"INSERT INTO function_data VALUES ({i}, 1, '{name}', {loc}, 3, 1, {vals})")
    c.commit()
    c.close()
    return ref.signal_columns[0]


def test_compare_counts_changed_signal_only(tmp_path):
    first = _db(tmp_path / "a.db", [("f", 10, 4), ("g", 8, 1)])
    _db(tmp_path / "b.db", [("g", 8, 1), ("f", 10, 2)])  # rows in another order, f's first signal falls
    r = compare_scans.compare(tmp_path / "a.db", tmp_path / "b.db")
    assert r["aligned"] == 2 and r["only_a"] == 0 and r["only_b"] == 0
    assert r["diff_signal_columns"] == {first: 1}
    assert r["diff_loc"] == 0 and r["functions_with_any_vector_input_diff"] == 1
