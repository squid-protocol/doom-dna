# DOOM-E9 truth-set size, recorded before any predictor was scored (2026-11-22)

Computed by `measure/e9_truth.py` (registered 20:03 EST, commit `33e8bf6`), outcome-blind, in 314 s. The full tables are hashed in `MANIFEST.sha256`; the small ones are copied here. No predictor has been run.

| | Eligible pairs (Jaccard at least 0.9) | Events | Distinct modules | Independent lineage pairs |
|---|---:|---:|---:|---:|
| **All classes** | 7,102 | 239 | 124 | 67 |
| Port-to-port (documented, T3) | 711 | 7 | 2 (`textscreen`, `opl`) | **4** |
| Co-borrowing (two borrowers of one donor) | 395 | 4 | 1 | 3 |
| External library | 3,134 | 51 | 6 | 22 |
| Coincidence (near-copy, undocumented) | 2,862 | 177 | 117 | 57 |

Sensitivity truth sets: Jaccard at least 0.6 gives 12,202 eligible pairs, 372 events, 196 modules, 81 lineage pairs; the identifier-normalised 0.9 set gives 11,329 pairs, 801 events, 514 modules, 164 lineage pairs.

**Port-to-port events (all from `chocolate-doom`):** `textscreen` into `eternity` (224 functions), `woof` (214), `odamex` (193 plus 15 in examples), `prboom-plus` (8, partial), `dsda-doom` (4, partial), and `opl` into `woof` (53).

**Registered power gate (Amendment 1 F.18):** fewer than 5 independent lineage pairs or fewer than 2 modules makes P1 descriptive. The **port-to-port stratum has 4 lineage pairs, so P1 restricted to documented port-to-port transfers is descriptive**; P1 over all truth classes (67 lineage pairs) passes the gate and is reported with the classes separated. The large **coincidence** class (2,862 pairs, 117 modules) is near-identical code between cross-clade ports that no documentation or external-library rule explains (short wrappers, tables, undocumented vendored code); it is reported as its own class and is not claimed as transfer.

Left-censored first-appearance shares are high for some repositories (for example `chocolate-doom` 20%, `crispy-doom` 12%; the COBOL raycasters and `doom-wasm` are fully censored), so time checks apply to the dated subset only.
