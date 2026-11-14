# DOOM's DNA (`doom-dna`)

A standalone, reproducible study of **44 DOOM ports** across ~20 programming languages, measured by structural geometry and call-graph wiring without reading identifiers or comments.

> **Separation of concerns:** [gitgalaxy](https://github.com/squid-protocol/gitgalaxy) (`tests/doom_rosetta/`) owns the engine CI regression gate. This repository owns the **scientific study**: manifests, keyword-interpretation standards, preregistered follow-up experiments, measurement scripts, results, and the interactive article.

## Repository Layout

| Directory | Purpose |
|---|---|
| `manifest/` | Pinned 44-port corpus (`manifest.csv`, `scope.csv`), `declared_lineage.csv`, `subsystems.json`, `timeline_events.csv` |
| `docs/` | Canonical measurement contracts, starting with [docs/KEYWORD_MODES.md](docs/KEYWORD_MODES.md) |
| `preregistration/` | Registered hypotheses for open questions (`DOOM-E1`..`DOOM-E4`) |
| `measure/` | Study-side measurement, lineage, fidelity, and report-generation scripts |
| `results/` | Generated evidence artifacts (`blind_placement.*`) and [RESULTS.md](RESULTS.md) |
| `followups/` | Exploratory & registered follow-up experiments (`oop-function-collapse/`, `composition-lens/`) |
| `article/` | Interactive HTML article (`index.html`, `data.json`, media) and text edition (`teardown-of-doom.md`) |
| `tests/` | Structural integrity & schema checks (`pytest`) |

## Headline Conclusions

1. **Name-blind twins work within a language:** `sfs twins` achieves **93% precision** (65% recall) against source-text function diffs (Spearman ρ = 0.83–0.84 across 43–44 programs), while unrelated C controls (Quake, Quake II, Lua) sit at 0–0.6%.
2. **Unsupervised Seed-and-Extend recovers 1-to-1 DOOM DNA across translations:** Using `composition` mode, FGW reciprocal-best-hit seeding, `delta` translation-offset calibration, and 3-hop call-graph extension (zero names or paths read), we recover **95.3%** (`687/721`) of `mood` (C+COBOL), **89.0%** (`590/663`) of `puredoom` (single-header C), **84.9%** (`547/644`) of `doomgeneric`, **75.9%** (`426/561`) of `gore` (**Go**, even with flat directory layout), and **65.0%** (`433/666`) of `chocolate-doom`, while unrelated C controls (`lua` 0.0%, `quake` 0.6%, `quake2` 0.6%) and from-scratch reimplementations (`room4doom`, `rust-doom`, `helion` all **0.0%**) sit at noise ([FINDING.md](followups/seed-and-extend/FINDING.md)).
3. **Cross-pair permutations & expanded language/architecture controls confirm zero false DNA:** Across **66** pairwise permutations of novel/from-scratch/COBOL repos (`agentic-cobol-doom-cc`, `agentic-cobol-doom-codex`, `fps-cob`, `fsharp-doom`, `doomf77`, `cssdoom`, `sqldoom`, `rust-doom`) and **6** new permissive controls (`carddemo-cobol-ctrl`, `c-raycasting`, `c-raycasting2`, `goom3d`, `bubbletea`, `macroquad`), every non-DOOM pair scores **0–1** SE name hits. Meanwhile, the three COBOL raycasters cluster in FGW cost (**`0.670–0.706`** vs. **`0.748–0.775`** against same-size business COBOL `carddemo-cobol-ctrl`) and align analogous raycaster roles without names ([CONTROLS_CROSSPAIRS.md](followups/seed-and-extend/CONTROLS_CROSSPAIRS.md)).
4. **Horizontal borrowing is visible without names:** `eternity` and `odamex` match `doom-wasm` via ~200 `textscreen` library twins absent from `linuxdoom`.
5. **Architecture survives some translations above chance:** `doom-scheme` (+0.51) and `gore` (+0.50) preserve `linuxdoom`'s cross-subsystem call wiring on par with `chocolate-doom` (+0.51), and blind placement hits 60% (`κ = 0.50`) on Go vs. 20% chance.
6. **Raw wiring and graph-shape distance mislead without nulls:** Raw wiring flatters every port (`0.72–0.95`), and raw graph-shape distance does not separate DOOM ports (`0.30–3.25`) from unrelated controls (`1.04–2.30`).

## Open Questions

See [preregistration/EXPERIMENTS.md](preregistration/EXPERIMENTS.md) for the registered experiments addressing tiny OOP function splitting (`mochadoom`, `kocoa-doom`, `managed-doom`), cross-language composition matching, and subsystem `other %` coverage gates.

## Licensing & Attribution

Measurements only: no third-party source code or WAD/game data is committed. Every port in `manifest/manifest.csv` carries an explicit OSI or CC0 license. "DOOM" is used descriptively; this project is not affiliated with or endorsed by id Software, ZeniMax Media, or Microsoft.
