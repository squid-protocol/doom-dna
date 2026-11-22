"""DOOM-E8b precondition table (Amendment 1 §H): pinned SHAs, eligible functions, duplicate share, language shares, scope drops and
scan status for every progenitor scan. Outcome-blind: no survival, no shared, no comparison with any port.

    python e8b_precondition.py
"""
import collections
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, "/srv/storage_16tb/projects/structural-fingerprint-scanner/src")
sys.path.insert(0, "/srv/storage_16tb/projects/doom-dna-worktrees/e8-half-life/measure")
from structural_fingerprint.fingerprint import build  # noqa: E402
from structural_fingerprint.reference import load_reference  # noqa: E402
from structural_fingerprint.scan_io import load_scan  # noqa: E402
import e8_snap  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SNAPS = Path("/srv/storage_16tb/projects/doom-e7-work/e8b/snaps")
ref = load_reference("structure")
rows = []
for r in csv.DictReader(open(REPO / "manifest" / "e8b_pins.csv")):
    d = SNAPS / e8_snap.tag(r["sha"], r["scope_key"])
    meta = json.loads((d / "meta.json").read_text()) if (d / "meta.json").exists() else {}
    row = dict(name=r["name"], sha=r["sha"], commit_date=r["commit_date"], role=r["role"], scan_rc=meta.get("rc", ""),
               ctags_functions=meta.get("ctags_functions", ""), pruned=" ".join(meta.get("pruned", [])), eligible="", dup_share="",
               lang_c="", lang_cpp="", lang_other="", status="")
    db = next(iter(d.glob("*_galaxy_master.db")), None)
    if db is None or meta.get("rc") != 0:
        row["status"] = "no scan"
    else:
        fp = build(load_scan(db, ref.signal_columns, name=r["name"]), ref, min_loc=3)
        t = fp.functions
        keep = t.loc >= 6
        n = int(keep.sum())
        row["eligible"] = n
        if n:
            c = collections.Counter(t.key[keep].tolist())
            row["dup_share"] = round(sum(v for v in c.values() if v > 1) / n, 3)
            lang = collections.Counter(str(x) for x in t.language[keep])
            row["lang_c"] = round(lang.get("c", 0) / n, 3)
            row["lang_cpp"] = round(lang.get("cpp", 0) / n, 3)
            row["lang_other"] = round(1 - row["lang_c"] - row["lang_cpp"], 3)
        row["status"] = "usable" if n >= 100 else "underpowered"
    rows.append(row)
out = REPO / "manifest" / "e8b_precondition.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
for r in rows:
    print({k: r[k] for k in ("name", "commit_date", "scan_rc", "eligible", "dup_share", "lang_c", "lang_cpp", "status")})
