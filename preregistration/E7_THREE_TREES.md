# `DOOM-E7`: Three Trees (declared, names, structure) and a Withheld Validation

**Status: REGISTERED 2026-11-22 14:47 EST (this commit), before any E7 scan. [Amendment 1](E7_AMENDMENT_1.md) reconciles two independent design reviews and supersedes the sections it names; read it with this file. Pins: [manifest/RUN_PINS.json](../manifest/RUN_PINS.json). New programs: [manifest/e7_new.csv](../manifest/e7_new.csv).** It registered when two independent design reviews were reconciled in a dated amendment and this file was committed before any scan or scoring run. Thresholds marked `[LOCK]` are my proposals and are open to the reviews. After registration, nothing in §3 to §6 changes without a dated amendment.

**This experiment fixes the numbers the rewritten article quotes.** It supersedes the lineage, twin-survival and descent numbers from engine `6c7c6c1bc` and from the older engine `9f213ab83` examples in the scanner repo. Earlier results stay as history.

## 1. Questions

1. Can function **names** recover the ports' ancestry independently of what the ports declare?
2. Can the name-blind scanner (`sfs`) do the same, and is it better or worse than names?
3. How do the three trees (declared, names, structure) differ, where do they agree, and where the two measured methods disagree, why?
4. Do the two measured methods behave as expected on a **withheld** set of programs that never entered the map?

## 2. Corpus

| Set | Members | Role |
|---|---|---|
| **Map set** | The 44 ports in `manifest/manifest.csv` (pinned SHAs), plus 3 unrelated C negative controls: `quake`, `quake2`, `lua` (the pinned scans from `followups/seed-and-extend`) | Build the three trees |
| **Withheld set (11)** | E5 held-outs: `cydoomgeneric`, `iron-doom`, `doomarkable`, `DOOM-style-Game`, `doome`. Added permissive controls: `carddemo-cobol-ctrl`, `c-raycasting`, `c-raycasting2`, `goom3d`, `bubbletea`, `macroquad` | Placed on the frozen map in Phase B only |

These are the 55 programs of `article/data.json`: 44 + 11. The 3 unrelated C controls were scanned separately and sit outside both sets. They go in the map set because the question asks for negative controls on the maps.

**Disclosure.** All 58 programs were already scanned at engine `6c7c6c1bc`, and E5 was scored. "Withheld" here means *never used to build the map or fix any rule or threshold in this experiment*, not "never seen". The 5 E5 programs also have earlier preregistered predictions (E5). The 6 extra controls have no earlier prediction, so §6 registers one for each.

## 3. Pinned definitions (one set, used by both methods)

**Run pins (recorded in `results/e7/RUN_MANIFEST.json` before the first scan):** `structural-fingerprint-scanner` commit `b1a9e92` (v0.1.0); GitGalaxy engine commit = `origin/main` at launch (SHA written down before scanning); manifest SHAs as pinned. The vendored sfs reference model was extracted from engine `9f213ab83`, so run `tools/refresh_reference.py` against the launch engine first. Every fingerprint must carry the same `spec_hash`, or the run stops. All 58 programs are rescanned on that engine. No scan from an earlier engine enters any E7 number.

**Eligible function.** A scanned function of at least `min_loc = 6` lines (the twin default), synthetic `__global_context__` slices dropped, in the repo's scoped code (the `scope.csv` drops apply). Sensitivity: `min_loc = 3`.

**Name key (names method).** Case-folded; all non-alphanumerics removed; for a qualified name only its last component (`Foo::bar`, `Foo.bar` give `bar`). So `P_SpawnMobj`, `p_spawn_mobj` and `pSpawnMobj` share a key. No path, signature or module is used.
- Variant N2: also strip a leading module prefix of 1 to 4 letters followed by `_` (`P_`, `R_`, `TXT_`) before normalizing.
- Variant N3: drop any key present in 25% or more of the 58 programs (`main`, `init`, `usage`...) `[LOCK]`.

**Survival, one definition per method, same shape.** For an ordered pair (Q, T), over eligible functions:
- `survival_names(Q→T) = Σ_k min(n_Q(k), n_T(k)) / |eligible Q|`: one-to-one by key, so a repeated name such as `main` cannot match twice.
- `survival_struct(Q→T)` = the share of eligible Q functions linked to a certified twin in T, per `docs/METHOD.md` §5: reciprocal best hit, ratio test 0.8, target-decoy at `fdr = 0.01`, one-to-one; lens `structure`. Sensitivity: `fdr = 0.05`, lens `portable`.

**Shared (pair), identical formula for both methods.** `shared = max over the two directions of the Wilson 95% lower bound of survival` (METHOD §5). **Distance** `= 1 − shared`. **Tree** = UPGMA (average linkage), Newick, as METHOD §6. **Floor** = 2%: a program whose largest shared with every other program is under 0.02 has *no detectable descent* under that method; it is listed, drawn at the root, and left out of that tree's scoring (as METHOD §6).

**Three trees.** `T_declared` from `manifest/declared_lineage.csv` (topology only; 29 declared parents, 15 programs without a declared parent), `T_names`, `T_struct` (sfs descent tree). The sfs profile tree is reported as a fourth, unscored context.

**Family.** As METHOD §6: a declared ancestor, descendant, sibling, or cousin (shared declared ancestor other than the root).

## 4. Phase A: build and compare the three trees (map set, 47 programs)

Computed in this order, all from the one scan set: names matrix, structure matrix, three trees, comparison tables, then a SHA-256 manifest of every table and Newick. **That manifest is committed before Phase B starts.**

**Metrics, applied identically to `T_names` and `T_struct`:**
- `M1`: nearest-is-family rate over scored programs.
- `M2`: declared parent's rank among the other programs (not counting its own declared descendants); median and share at rank 1.
- `M3`: normalized clade (Robinson–Foulds) distance and triplet distance to `T_declared`, on the programs scored in the tree and having a declared parent. Reported with the permutation null (1,000 seeded leaf-label shuffles) and the gap.
- `M4`: agreement between the two measured trees: clade and triplet distance `T_names` vs `T_struct` on the programs scored in both, with the same null.
- `M5`: pair-level agreement: Spearman of `shared_names` vs `shared_struct` over all pairs; and the 2×2 table of pairs above/below the floor under each method.
- `M6` (**arbiter**): independent source-text survival of linuxdoom functions per port (`lineage.py`, `survival_functions.csv`, exact or near) at the manifest SHAs. Spearman of `survival_names(linuxdoom→port)` and of `survival_struct(linuxdoom→port)` against it; mean absolute error against the text survival of each; paired bootstrap (2,000 draws) of the difference, 95% interval. Text verdicts do not depend on the engine and are reused.
- `M7`: negative controls: for each of `quake`, `quake2`, `lua` (and the map set's reimplementations and raycasters), the largest `shared` with any DOOM engine-port under each method, and whether it clears the floor.
- `M8` (descriptive): the 20 pairs with the largest `|shared_names − shared_struct|`, each classified from its twin and name lists as sideways transfer, translation, rename or reorganization, generic-name collision, or small-repo threshold. The rubric is fixed here; no extra categories after seeing the pairs.

### Hypotheses (Phase A) `[LOCK]`

| # | Prediction | Basis |
|---|---|---|
| H7.1 | Names **overstate** inheritance: for same-language ports, `survival_names(linuxdoom→port) > text survival` for at least 75% of ports, and `survival_struct` is closer to text survival (lower mean absolute error) in at least 75%. | Article: Chocolate keeps 86% of names, 33% of code |
| H7.2 | Where both detect descent, the two **rank** ports alike: Spearman of `shared_names` vs `shared_struct` at least 0.80 over same-language pairs above the floor. | Earlier twin vs text 0.83 |
| H7.3 | Names reach where structure cannot: among cross-language ports that `T_struct` leaves with no detectable descent but that have a declared parent, at least a third clear the floor under names. Unsure; the earlier R-series found translations "not usable" by name. | Gore keeps many names |
| H7.4 | Names **false-attach** more than structure: `quake` or `quake2` clears the floor against a DOOM engine-port under names (id-style names, generic names) and not under structure; structure shows 0 control attachments. | Controls 0 to 0.6% under structure |
| H7.5 | Both trees recover declared family: `M1` at least 0.70 for each. `M4` clade distance is below the 5th percentile of its permutation null. | Earlier descent 74% |

H7.1 and H7.4 are the "which is better" tests: against independent text survival, and against negatives. H7.3 is where names can win. Each is reported whichever way it falls.

## 5. Name vs structure: the verdict rule

No single winner is declared in advance. The report states per metric (`M1`, `M2`, `M3`, `M6`, `M7`) which method is better and by how much with its interval, and then one sentence on complementarity (what each finds that the other misses, from `M8`). If the interval of a difference includes 0, the report says "no difference detected".

## 6. Phase B: withheld validation (11 programs)

Run only after the Phase A manifest is committed. The map is **frozen**: no UPGMA rerun, no threshold change. For each withheld program W and each method, compute `shared(W, p)` for every map program p; W's *nearest* = argmax; W *attaches* if max is at or above the floor, else *no detectable descent*. Each outcome is scored against the expectation below, written before any Phase B computation.

| W | Expected under both methods | Why |
|---|---|---|
| `cydoomgeneric` | Attaches; nearest = `doomgeneric` | Vendors doomgeneric (E5: 100% Tier-1) |
| `iron-doom` | `[LOCK]` Names: may attach to `chocolate-doom` (normalization bridges snake_case) or not. Structure: no detectable descent | Bevy ECS rewrite (E5: 0.0%) |
| `doomarkable` | No detectable descent | 41-function wrapper around an external crate |
| `DOOM-style-Game`, `doome` | No detectable descent | From-scratch |
| `carddemo-cobol-ctrl`, `c-raycasting`, `c-raycasting2`, `goom3d`, `bubbletea`, `macroquad` | No detectable descent | Non-DOOM controls |

**Scoring.** Per method: outcomes matching expectation out of 11; false attachments (expected none, attached); and for `cydoomgeneric` whether the nearest is `doomgeneric`. `H7.6`: structure meets expectation on at least 10 of 11 and has 0 false attachments. `H7.7`: names meet expectation on at most as many as structure, or the table shows which programs names get wrong and why (generic names). The `iron-doom` row has no directional prediction for names; it is reported and nothing hangs on it.

## 7. Sensitivity (reported, not decisive)

`min_loc = 3`; N2 and N3 name variants; `fdr = 0.05`; lens `portable`; floor 1% and 5%; Chocolate, Crispy, Inter and Doom Retro are handled alike (the `scope.csv` drops apply). A conclusion that flips under a sensitivity is labelled fragile in the report.

## 8. Outputs

Registration: this file. Data (small tables, Newick, manifests, hashes): `results/e7/`. Raw scans and fingerprints stay on disk outside the repo with their hashes in `RUN_MANIFEST.json`. Code to be added before the run, in `measure/`: names matrix and survival, tree comparison (RF, triplet, null), the arbiter, the Phase B placer, each with a test. No third-party source code or WAD data is committed.

## 9. Known limits

- The universe is only the 44 + 3 map programs; the descent tree is cohort-relative.
- Names are cheap to copy and to change; text survival is a third reference only for linuxdoom-to-port pairs, not pairwise.
- The declared lineage is what each project says about itself, and where the parent is outside the corpus the nearest corpus ancestor is used.
- The 11 programs are withheld from construction, not from knowledge.
- Dense FGW is not used here, so `doomsday`, `gzdoom` and `doom3-bfg` are in the twin and name analyses, unlike Seed-and-Extend.
