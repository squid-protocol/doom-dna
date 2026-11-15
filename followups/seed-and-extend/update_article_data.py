"""Enrich article/data.json with Seed-and-Extend results, DOOM-E5 targets, 6 new controls, and horizontal transfers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "article" / "data.json"
RESULTS_CSV = Path(__file__).resolve().parent / "results_all.csv"


def main() -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    # 1. Load Seed-and-Extend results from results_all.csv
    se_by_port = {}
    with RESULTS_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            se_by_port[row["port"]] = {
                "t1_n": int(row["t1_n"]),
                "t1_hits": int(row["t1_name_hits"]),
                "t1_prec": float(row["t1_name_prec"]),
                "se_n": int(row["se_n"]),
                "se_hits": int(row["se_name_hits"]),
                "se_prec": float(row["se_name_prec"]),
            }

    existing = {p["name"]: p for p in data["ports"]}
    for name, p in existing.items():
        if name in se_by_port:
            p["seed_extend"] = se_by_port[name]

    # Helper to construct clean compatible entries for newly added targets/controls
    def make_entry(
        name: str,
        language: str,
        cls: str,
        fidelity: str,
        lic: str,
        functions: int,
        lineage: str,
        se: dict,
        fgw_cost: float,
        shared: float,
        blurb: str,
        upstream: str = "",
    ) -> dict:
        return {
            "name": name,
            "language": language,
            "languages": "",
            "class": cls,
            "fidelity": fidelity,
            "license": lic,
            "lineage": lineage,
            "upstream": upstream,
            "functions": functions,
            "wiring": None,
            "cross_wiring": None,
            "cross_null": None,
            "gap": None,
            "calls_kept": None,
            "shape_distance": None,
            "assigned_by": {},
            "stations": {},
            "lines": [],
            "survival": None,
            "parent": None,
            "shared_with_linuxdoom": shared,
            "nearest": [],
            "crosscheck": None,
            "blind": None,
            "twins": None,
            "seed_extend": se,
            "fgw_cost": fgw_cost,
            "facts": {"github": {"description": blurb}},
        }

    # 2. DOOM-E5 held-out targets (DOOM_E5_RESULTS.md)
    e5_entries = [
        make_entry(
            "cydoomgeneric",
            "c",
            "fork",
            "held-out E5 fork",
            "GPL-2.0",
            1109,
            "doomgeneric (C + Python bindings)",
            {"t1_n": 92, "t1_hits": 91, "t1_prec": 0.9891, "se_n": 620, "se_hits": 287, "se_prec": 0.4629, "best_anchor": "doomgeneric", "best_t1_prec": 1.0, "best_fgw_cost": 0.313},
            0.541,
            0.559,
            "DOOM-E5 held-out target: Cython/Python wrapper vendoring doomgeneric (100.0% T1 vs doomgeneric, FGW=0.313).",
        ),
        make_entry(
            "iron-doom",
            "rust",
            "rewrite",
            "held-out E5 ECS rewrite",
            "GPL-3.0",
            319,
            "chocolate-doom (rewritten in Bevy ECS)",
            {"t1_n": 24, "t1_hits": 0, "t1_prec": 0.0, "se_n": 147, "se_hits": 0, "se_prec": 0.0},
            0.734,
            0.0,
            "DOOM-E5 falsification: ported from Chocolate Doom into Bevy ECS; decoupling into ECS systems erases call-graph DNA (0.0%).",
        ),
        make_entry(
            "doomarkable",
            "rust",
            "notdoom",
            "held-out E5 external wrapper",
            "GPL-2.0",
            41,
            "wraps external doomgeneric-rs crate",
            {"t1_n": 6, "t1_hits": 0, "t1_prec": 0.0, "se_n": 37, "se_hits": 0, "se_prec": 0.0},
            0.747,
            0.0,
            "DOOM-E5 falsification: 41-function Rust platform wrapper calling external doomgeneric-rs crate (engine not vendored).",
        ),
        make_entry(
            "DOOM-style-Game",
            "python",
            "rewrite",
            "held-out E5 raycaster",
            "MIT",
            66,
            "from-scratch Python raycaster",
            {"t1_n": 9, "t1_hits": 0, "t1_prec": 0.0, "se_n": 39, "se_hits": 0, "se_prec": 0.0},
            0.705,
            0.0,
            "DOOM-E5 held-out control: from-scratch Python raycaster (0.0% vs linuxdoom).",
        ),
        make_entry(
            "doome",
            "rust",
            "rewrite",
            "held-out E5 Rust engine",
            "MIT",
            651,
            "from-scratch MIT Rust engine",
            {"t1_n": 28, "t1_hits": 0, "t1_prec": 0.0, "se_n": 322, "se_hits": 0, "se_prec": 0.0},
            0.756,
            0.0,
            "DOOM-E5 held-out control: from-scratch MIT Rust DOOM-style engine (0.0% vs linuxdoom).",
        ),
    ]

    # 3. 6 additional permissive controls (CONTROLS_CROSSPAIRS.md)
    ctrl_entries = [
        make_entry(
            "carddemo-cobol-ctrl",
            "cobol",
            "notdoom",
            "permissive COBOL control",
            "Apache-2.0",
            55,
            "aws-mainframe-modernization-carddemo",
            {"t1_n": 20, "t1_hits": 1, "t1_prec": 0.05, "se_n": 16, "se_hits": 1, "se_prec": 0.0625},
            0.772,
            0.0,
            "Permissive non-game COBOL control (COCRDLIC + COUSR00C); sits higher in FGW cost (0.748-0.772) than COBOL raycasters (0.670-0.706).",
        ),
        make_entry(
            "c-raycasting",
            "c",
            "notdoom",
            "permissive C raycaster control",
            "MIT",
            23,
            "KjetilIN/raycasting",
            {"t1_n": 23, "t1_hits": 0, "t1_prec": 0.0, "se_n": 19, "se_hits": 1, "se_prec": 0.0526},
            0.781,
            0.0,
            "Permissive C SDL2 raycaster control (0/23 T1 hits vs linuxdoom).",
        ),
        make_entry(
            "c-raycasting2",
            "c",
            "notdoom",
            "permissive C raycaster control",
            "MIT",
            21,
            "Kinyarasam/Raycasting-C",
            {"t1_n": 21, "t1_hits": 0, "t1_prec": 0.0, "se_n": 14, "se_hits": 1, "se_prec": 0.0714},
            0.769,
            0.0,
            "Permissive C SDL2 raycaster control (0/21 T1 hits vs linuxdoom).",
        ),
        make_entry(
            "goom3d",
            "go",
            "notdoom",
            "permissive Go raycaster control",
            "MIT",
            76,
            "garstas/goom3d",
            {"t1_n": 64, "t1_hits": 0, "t1_prec": 0.0, "se_n": 46, "se_hits": 0, "se_prec": 0.0},
            0.721,
            0.0,
            "Permissive Go Wolfenstein-style raycaster control: 0 hits against Go port gore (0.721 FGW).",
        ),
        make_entry(
            "bubbletea",
            "go",
            "notdoom",
            "permissive Go TUI control",
            "MIT",
            675,
            "charmbracelet/bubbletea",
            {"t1_n": 206, "t1_hits": 1, "t1_prec": 0.0049, "se_n": 302, "se_hits": 0, "se_prec": 0.0},
            0.736,
            0.0,
            "Permissive Go TUI framework control: 0 hits after 3-hop SE against both gore and linuxdoom.",
        ),
        make_entry(
            "macroquad",
            "rust",
            "notdoom",
            "permissive Rust engine control",
            "Apache-2.0",
            960,
            "not-fl3/macroquad",
            {"t1_n": 269, "t1_hits": 0, "t1_prec": 0.0, "se_n": 367, "se_hits": 0, "se_prec": 0.0},
            0.731,
            0.0,
            "Permissive Rust game engine control: 0 hits vs linuxdoom (0.731 FGW); rust-doom sits closer to macroquad (0.681) than linuxdoom (0.802).",
        ),
    ]

    for entry in e5_entries + ctrl_entries:
        if entry["name"] in existing:
            existing[entry["name"]].update(entry)
        else:
            data["ports"].append(entry)
            existing[entry["name"]] = entry

    # 4. Update family tree with DOOM-E5 lineages
    data["family"]["cydoomgeneric"] = {"parent": "doomgeneric", "kind": "fork"}
    data["family"]["iron-doom"] = {"parent": "chocolate-doom", "kind": "rewrite"}
    data["family"]["doomarkable"] = {"parent": "doomgeneric", "kind": "rewrite"}

    # 5. Add verified horizontal transfer pairs (HORIZONTAL_BORROWING.md)
    data["horizontal_transfers"] = [
        {"a": "eternity", "b": "chocolate-doom", "twins": "210 T1", "exact": "182 SE", "module": "textscreen", "finding": "Horizontal borrow onto SMMU/MBF branch"},
        {"a": "odamex", "b": "chocolate-doom", "twins": "178 T1", "exact": "136 SE", "module": "textscreen", "finding": "Horizontal borrow onto ZDoom branch"},
        {"a": "doom-wasm", "b": "woof", "twins": "67", "exact": "53", "module": "textscreen", "finding": "Horizontal borrow onto MBF/WinMBF branch"},
        {"a": "chocolate-doom", "b": "dsda-doom", "twins": "39", "exact": "29", "module": "src/hexen", "finding": "Hexen subsystem copied into PrBoom+ branch"},
        {"a": "dsda-doom", "b": "woof", "twins": "47", "exact": "37", "module": "prboom2/src <-> src", "finding": "Shared MBF21 action pointers"},
        {"a": "chocolate-doom", "b": "woof", "twins": "19", "exact": "13", "module": "man", "finding": "Shared docgen tooling"},
        {"a": "doom-ios", "b": "prboom-plus", "twins": "272", "exact": "257", "module": "code/prboom", "finding": "Hidden PrBoom ancestry (declared linuxdoom)"},
        {"a": "doomgeneric", "b": "sdl-doom", "twins": "528", "exact": "521", "module": "doomgeneric <-> src", "finding": "Shared Chocolate-derived minimal SDL base"},
    ]

    DATA_PATH.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"Updated {DATA_PATH}: {len(data['ports'])} total entries ({sum(1 for p in data['ports'] if 'seed_extend' in p)} with Seed-and-Extend)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
