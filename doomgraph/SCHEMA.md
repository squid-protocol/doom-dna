# DoomGraph schema (v1, 2026-11-27: see E18 v2 section 'Schema v1' for the required additions, which govern)

**Two database files:** `doomgraph_static.sqlite` (instances, match edges, call edges, lineage edges, ortholog groups) and `doomgraph_behaviour.sqlite` (reach, lesions, phenotypes, conformance, folds). The group-building code never opens the behaviour file.

One SQLite file (`doomgraph.sqlite`) plus a build script; every row records its source file and commit so layers can be rebuilt. Layers are separate tables joined on **instance ids**; nothing is overwritten.

## Entities
* `port(port_id, name, language, lineage_parent, scan_path, commit_sha)`: about 36 ports plus the reference engines (linuxdoom, chocolate-doom, doomgeneric, prboom-plus, woof).
* `instance(inst_id, port_id, fid, name, file, line, size, lang_kind)`: one row per function instance, from the GitGalaxy/tree-sitter scans (`fid` = the scan's function index; the pair files index into it).
* `ortholog_group(group_id, anchor_inst, method, version)` and `membership(inst_id, group_id, confidence, evidence)`: groups built from the match edges (below) anchored on linuxdoom or chocolate-doom; every membership keeps its evidence chain, and group construction is deterministic and versioned.

## Edge layers
* `match_edge(a_inst, b_inst, tier, score, source)`: E12 matches from `gene-view/*.json` (`F0` exact fingerprint, `F1c` twin, `S` graph seed, `ext` extension tiers 1-3, with the gate result), plus name-agree edges (unique name after prefix stripping), plus E7 text-arbiter confirmations.
* `call_edge(caller_inst, callee_inst, kind)`: the scanner's static call graph (G1) and state-table dispatch edges (G2), as in E13.
* `lineage_edge(port, parent_port, evidence)`: E7/E8b progenitor and fork evidence.

## Behaviour layers (per instance)
* `demo_reach(inst_id, demo, entries, first_tic)`: clean call counts per demo (chocolate-doom, managed-doom, prboom-plus, Mocha, gore as available).
* `lesion(lesion_id, inst_id, line, kind, family)` and `lesion_result(lesion_id, demo, outcome, tic, class_bits)`: the E15 screens (and Mocha/gore only after their analyses are frozen and read).
* `phenotype(inst_id, hot, inert, usable, kill_fraction_by_family, median_log_tic, class_dist, nobs)`: the E15 function phenotype (D inputs), with the E15 hot/inert flags verbatim.
* `conformance(port, demo, status, first_tic, field)`: E13 demo conformance of each port against the reference.
* `diagnosis_dictionary(lesion_id, symptom_vector)`: E16's dictionary view (a view over `lesion_result`).

## Derived and annotation layers
* `behaviour_confirmed(edge)`: the E14/E15 definition (D at or below the 5th percentile of random cross-port pairs and identical call profile) wherever both ends have phenotypes.
* `subsystem(inst_id, subsystem)`: the 16 call-graph subsystems.
* `sfs_confidence(edge, score)`: the size-aware confidence score (frozen formula and commit recorded).

## Rules
No third-party source or WAD text is stored (hashes, names, line ranges, metrics only). The Mocha and gore lesion outcomes are **not** ingested until the E17 analysis has run and its results are committed. Every table has `source` and `build_id`.
