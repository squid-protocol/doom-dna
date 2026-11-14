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
2. **Horizontal borrowing is visible without names:** `eternity` and `odamex` match `doom-wasm` via ~200 `textscreen` library twins absent from `linuxdoom`.
3. **Architecture survives some translations above chance:** `doom-scheme` (+0.51) and `gore` (+0.50) preserve `linuxdoom`'s cross-subsystem call wiring on par with `chocolate-doom` (+0.51), and blind placement hits 60% (`κ = 0.50`) on Go vs. 20% chance.
4. **Raw wiring and graph-shape distance mislead without nulls:** Raw wiring flatters every port (`0.72–0.95`), and raw graph-shape distance does not separate DOOM ports (`0.30–3.25`) from unrelated controls (`1.04–2.30`).

## Open Questions

See [preregistration/EXPERIMENTS.md](preregistration/EXPERIMENTS.md) for the registered experiments addressing tiny OOP function splitting (`mochadoom`, `kocoa-doom`, `managed-doom`), cross-language composition matching, and subsystem `other %` coverage gates.

## Licensing & Attribution

Measurements only: no third-party source code or WAD/game data is committed. Every port in `manifest/manifest.csv` carries an explicit OSI or CC0 license. "DOOM" is used descriptively; this project is not affiliated with or endorsed by id Software, ZeniMax Media, or Microsoft.
