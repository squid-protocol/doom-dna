# DoomGraph v0 (E18)

Registered spec: `preregistration/E18_DOOMGRAPH.md` (section "v2" governs) and `doomgraph/SCHEMA.md` (v1 header). This directory holds the build code; the databases are large and stay on disk, **not in git**:

* `/srv/storage_16tb/projects/doom-e7-work/doomgraph/doomgraph_static.sqlite`: instances, match edges (E12 pair files, name-agree, E7 text arbiter), call edges (G1, G2), lineage edges, subsystem placement, ortholog groups.
* `/srv/storage_16tb/projects/doom-e7-work/doomgraph/doomgraph_behaviour.sqlite`: demo table, clean reach counts, E15 phenotypes (hot/inert/usable verbatim), E13 conformance, empty `behaviour_confirmed`, `sfs_confidence` and `holdout_fold`. Never attached to the group-building code.

## Rebuild (about 10 s for the static file, about 1 min for the behaviour file; run at low priority)

```
cd /srv/storage_16tb/projects/doom-dna-worktrees/e13-demo-pilot
nice -n 10 python3 doomgraph/build_static.py        # scans + gene-view pair files + E7/E8b/subsystem-map worktrees -> doomgraph_static.sqlite
nice -n 10 python3 doomgraph/build_behaviour.py     # E15 stores + E13 csvs (reads only instance ids from the static file) -> doomgraph_behaviour.sqlite
python3 doomgraph/audit.py                          # writes results/doomgraph/BUILD_REPORT.md (counts only); exit code 1 on any audit failure
python3 -m pytest doomgraph/tests -q                # synthetic-input tests
```

Python 3.12 with numpy, scipy and pandas (scikit-learn is not required; `build_behaviour.py` stubs the unused AMI import of `tests.py`). `build_manifest` records the code commit, pair-file sha256 (180 files), scan sha256 and commit per port, source commits (E7, E8b, subsystem map, gene-view, scanner), the name-stripping rule, weights, thresholds and seeds (group construction has no random draws). Commit the code before building so the recorded commit is the one that built the files.

## Files

* `common.py`: paths, frozen weights and thresholds, DDL for both files.
* `groups.py`: the pure group-building function (no file or database access; it receives only instances, match edges, call edges and declared lineage). Rule in its docstring.
* `build_static.py`: static build. A guard on `sqlite3.connect` refuses behaviour, phenotype and E17 paths; the databases it opened are logged in `build_manifest.opened_databases`.
* `build_behaviour.py`: behaviour build. Its guard refuses `jv_v2`, `go_v2`, `results/e17`, `results/e16/cases` (E17 is blind).
* `audit.py`: boundary, canary, determinism, allowlist, anchor-swap ARI, ungrouped rate, counts per port and layer.
* `tests/test_doomgraph.py`: synthetic tests.

## Conventions and choices to know

* **Instance** = a row of the E12 function table: scan functions of at least 3 lines, synthetic buckets dropped, in scan order. `fid` is that row index (the pair files index into it); verified by name agreement of exact-fingerprint pairs (83 percent of F0 pairs agree by name; twins with a renamed function are expected to differ). `instance_key` = sha1 prefix of (port, file, name, argument count); not unique when a file holds overloads, `UNIQUE(port_id, fid)` is the key.
* **Match edges** are stored once, canonically (`a_inst < b_inst`), per (tier, source). Tiers: `F0`, `F1c`, `S`, `ext1..3` (E12), `NAME` (unique name after stripping the `prep.py` prefixes and excluding its generic names, in both ports, for pairs among the reference engines), `TXT` (E7 text arbiter; verdict, similarity and a row hash only). `gate_passed` is the pair file's coherence gate; the group builder uses `S` and `ext` only when it passed and any tier only when both ends have at least 6 lines (the E12 universe).
* **Call edges**: G1 = scanner resolved calls (`fcall_data`, kinds `call` and `reference`); G2 = state-table dispatch edges (dispatcher to action function) for chocolate-doom, prboom-plus (same names) and managed-doom, taken from `graphs.py`.
* **Groups**: one per linuxdoom instance (anchor). Runs: `full` (anchor linuxdoom, primary) and `anchor_swap:chocolate-doom`. Controls (lua, quake, quake2, nginx, curl, leveldb, libuv) keep instances and are never grouped.
* **Roles**: `anchor`, `member`, `merge`, `split`, `conflict` (one per membership row; alternatives are extra rows with `rank >= 2`). Conflict, split and merge are to be excluded from P1 scoring.
* **Subsystems** are the placements in `subsystem_map_data.json` (16 subsystems), matched to instances by (port, name, size); unmatched or ambiguous entries are left out.
* **Behaviour**: screen functions are joined to instances by (file stem, name), then line; 2 managed-doom overloads are left out (counted in the manifest). Lesion-level rows are not ingested for any port.

## v1 (E18 amendment A1): multi-anchor consensus (descriptive only if a gate fails; see results/doomgraph/BUILD_REPORT_V1.md)

```
nice -n 10 python3 doomgraph/build_static_v1.py     # copies doomgraph_static.sqlite -> doomgraph_static_v1.sqlite (v0 rows intact) and adds build scopes v1, v1_swap:ldgw, v1_swap:cpw
python3 doomgraph/audit_v1.py                       # gates (a) anchor-swap ARI, (b) ungrouped rate on the E15 usable lists (ids only), (c) integrity audits; writes BUILD_REPORT_V1.md (exit 1 if any gate fails)
python3 -m pytest doomgraph/tests -q
```
`groups_v1.py` is the pure construction (joint anchors = the five reference engines; anchors cluster by mutual best matches; non-anchors join the group with the best-weighted consistent evidence); `eval_scope.py` is used only by the audit.
