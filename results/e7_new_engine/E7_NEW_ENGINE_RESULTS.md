# DOOM-E7 repeated on the current engine: results

Replication of DOOM-E7 (protocol, Amendment 1, Amendment 2 and 2a) with **one change, the GitGalaxy engine**. Registered before any scan in [E7_REPLICATION_NEW_ENGINE.md](../../preregistration/E7_REPLICATION_NEW_ENGINE.md) (commit `3e0b2e5`). Everything ran on 2026-11-24, 8:05 AM to 9:23 AM US Eastern. Raw data and fingerprints: `/srv/storage_16tb/projects/doom-e7-newengine-work` (`new/` = new engine, `c0/` = original engine through this harness, `c1/` = engine at #8939, `new_a2/` = Amendment 2 run).

## The short answer

**Did the E7 results change?** Yes in a few places, no in the places that carry the conclusions, and the changes are not caused by the call-graph and import-graph work.

* **Call-graph and import-graph quality cannot move E7.** The structure arm builds its measurements from per-function size, complexity, argument count, keyword density and 31 per-function signal counts. It loads the call edges and fan-in/fan-out but only copies them into descriptive fields of the fingerprint file; none of them enters a distance, a cutoff, a name key or a metric. The import graph is not read at all. This is shown from the code (below) and by experiment: in 11 of the 16 map programs whose call-graph output changed between the commit just after the pin and today, the twin vectors are byte-for-byte identical.
* **What did change the scans is a signal change, #8939** (it moved boolean operators out of `branch` into a new `short_circuit` signal). It changes the inputs of the twin vectors for 43,326 of 198,874 functions (21.8%) in 62 of the 66 programs. A second, smaller set of rule fixes (the stacked batch #9111) changes 610 more functions (0.3%).
* **The E7 numbers as registered (one decoy shuffle per pair) moved a little**: structurally detectable programs 25 to 27 (`doomretro` and `gzdoom` cross the 2% floor), nearest-is-family 0.619 to 0.565 on the programs each run detects (unchanged, 0.619, on E7's own 25), tree triplet compatibility 0.848 to 0.763. **But a re-roll of the random decoy on the unchanged original scans moves the result by as much**: across 25 decoy draws on the original engine the detectable count ranges 25 to 28 (median 27), and `doomretro` and `gzdoom` are detectable in 17 and 19 of the 25 draws. E7's registered 25 was a low draw. So these changes are real by my pre-stated rule (a program crossed the floor) but cannot be told apart from the decoy noise Amendment 2 was written to remove.
* **The stable numbers (Amendment 2, pooled decoys, K = 25) barely moved.** Detectable programs at the 2% floor 35 and 35 (one program in, one out, both weak edge cases); nearest-is-family on E7's fixed 25 programs 0.619 and 0.619; H7.1 21 of 22 and 21 of 22; of 2,550 ordered pairs only 3 moved by 0.03 or more (under the single shuffle 28 did). No port's share with `linuxdoom` moved by 0.03 (largest 0.010).
* **Scorecard**: one verdict flipped in the registered Phase B scorecard (H7.7, "names' placements not above structure's": falsified 12 vs 11 before, not falsified 12 vs 12 now), because the 47-function program `goom3d` no longer attaches to `curl` (0.0219 to 0.0117) at the single-shuffle cutoff. H7.1 to H7.6 and H7.5a keep their verdicts. In the Amendment 2 scorecard, P-A3 (previously low ports rise by 0.03 or more) goes from 6 of 7 to 7 of 7, because `inter-doom`'s single-shuffle value fell from 0.168 to 0.081 while its pooled value stayed at 0.140 / 0.145: E7's original `inter-doom` figure was the high side of a coin flip and the new one is the low side.

## Engines

| | Original | This replication |
|---|---|---|
| Commit | `704cb35f075660a637b61331554d8ff0bf206036`, 2026-11-22 2:38 PM EST | `beb46cfbc65391bd210dda4175045c78b1e96047` (origin/main when I started), 2026-11-24 7:50 AM EST |
| Commits between | | 120 |

The first of the 120 is #8939 itself (`3c436c8c57`, 2:42 PM EST on the 22nd, four minutes after the pin, parent = the pin), so the effect of #8939 can be isolated exactly.

**Call-graph and import-graph work (8 commits):** #8921 (call-graph Level 1 fixes for PowerShell, Haskell, Shell, Solidity; Level 2 for C++/Kotlin), #9046 (import resolution Erlang, OCaml, Nim), #9060 (Perl and PHP call-graph fixes), #9063 (Level 1 benchmark widened to 30 languages), #9070 (import resolution Tcl, Fortran), #9143 (C++ and Kotlin Level 2), #9161 (Level 2 across Kotlin, C, Rust, C++, TypeScript, JavaScript). Plus three README or evidence-sheet commits (#9062, #9142, #9144).

**Signal and rule work (changes what a scan counts):** #8939 (`short_circuit` split; 45 language rules; decision density now reads `branch + short_circuit`); #9111 (one re-bless for nine stacked engine fixes #9053 to #9067: Perl literal shielding, Ada, Dart, Groovy, Haskell, Objective-C, PowerShell, Scheme, Swift rules, plus changes in `core/detector.py` and `core/prism.py`); #9064 (Elixir), #9065 (R), #9066 (Nim), #9130 (Erlang). About 19 further commits only reword rule comments or "zero-trust" wording and change no behaviour.

**Everything else (about 85 commits):** COBOL/CICS/JCL forge, det mutation ledgers, CardDemo jobs, CI and box tooling, docs. None of these code paths run when a DOOM port is scanned (checked by the scan comparison below: the only differences in the scan databases are the ones listed there).

Reference model: `tools/refresh_reference.py` was run against both engines into side files (`results/e7_new_engine/reference_refresh_*.json`), not adopted. Only the provenance fields differ from the vendored model; `spec_hash` is **`f5d525ed16bc91db` (structure) and `82dfe97689dec61b` (portable), unchanged**. So the engine's archetype and scaling model was not retrained; #8939 changed what the scan counts for `branch` but the reference scaler, fitted before the split, was not refitted. I used the vendored model as registered; every fingerprint carries spec_hash `f5d525ed16bc91db`.

## What the structure arm reads (worked out from the code before any scan)

From the scan database: per function `loc`, `complexity`, `args`, `keyword_density` and 31 signal counts (the reference model's `signal_sources`, among them `branch`, `structural_boundaries`, `func_start`, `safety`, `io`, `api`, `bitwise_ops`), plus function name and file path. `scan_io.load_scan` also reads `func_fan_in`, `func_fan_out` and the call edges (`fcall_data`); `fingerprint.build` uses them only for `geometry.sketch` (fan-in/out quantiles) and `callgraph` (shape summary) in the descriptive part of the fingerprint file. The twin vector (`features.raw_features`, `standardize`, `embed`), the structural key, the engine-archetype strata used for decoys (computed by the reference model's own nearest-centroid rule, not read from the scan), the cutoffs and every E7 metric use none of them. The names arm and the text arbiter read function names, paths and line ranges. So only changes in which functions are found and what they count can matter, and the first is rare (12 functions in 2 programs differ: 4 in `iron-doom` from #8939, 8 in `odamex` from the later commits).

## Controls and how the change is attributed

All comparisons are per function on exactly the columns above (`measure_new_engine/compare_scans.py`, `compare_all.py`; `results/e7_new_engine/attribution/compare_all.csv`).

| Step | Functions with changed twin-vector inputs | Function sets | Call-graph outputs |
|---|---|---|---|
| **C0** original engine, this harness vs the original E7 scans (66 programs) | **0 of 198,874** | identical | 1 edge differs in `helion` (19,696 vs 19,697: a call-graph nondeterminism, never read) |
| C0 to **C1** (#8939 alone): the boolean-operator split | **43,326 of 198,874 (21.8%)**, 62 of 66 programs; 13 signal columns, mainly `struct_branch`; complexity changes in C# (`managed-doom` 145, `helion` 1,429), `edge-classic`, `lua`, `d2k`, `odamex` | 4 new functions (`iron-doom`) | 2 programs differ in edges, 10 functions in fan-in/out |
| C1 to **NEW** (the other 119 commits) | **610 of 198,878 (0.3%)**, 14 programs (`curl` 292, `dartdoom` 188, `odamex` 24, `gzdoom` 24, 8 C programs with a handful of `bitwise_ops` changes) | 8 new functions (`odamex`) | **22 programs differ in call edges, 4,684 functions in fan-in/out** |

* The harness reproduces E7: the original engine, rescanned by my scripts, gives function tables identical to the original on all 66 programs and byte-identical Phase A pair tables (`cmp` on `pairs_struct.csv`, `pairs_names.csv`, `linuxdoom_twin_presence.npz`). Every difference below is therefore the engine, not the harness. (Determinism of the engine itself: two fresh scans of `linuxdoom` and `c-raycasting` on the new engine were identical; this check was done after the main run, not before it as the brief asked, but the 66-program C0 match covers it.)
* The call-graph work shows up exactly where it should, in call edges and fan-in/out (22 programs, 4,684 functions), and nowhere that a twin vector reads. `attribution_check.py`: of the 16 map programs where call-graph outputs differ between C1 and NEW, the twin vectors and structural keys are byte-identical in 11; in the other five (`eternity`, `odamex`, `gzdoom`, `doom-scheme`, `curl`) they differ only for the 13, 24, 24, 5 and 292 functions whose signal counts changed.
* The 610 later signal changes: I bisected one of them (a handful of `bitwise_ops` counts in `chocolate-doom`) over the 45 commits that touch `gitgalaxy/`: the first commit that changes it is #9111 (the stacked rule fixes; last good #9064). I did not find which of the nine fixes does it or why a C program is touched, and I did not bisect the larger `curl` and `dartdoom` changes (`curl` has Perl, shell and other-language files; `dartdoom` is Dart).
* **What #8939 alone does to the E7 results**: the Phase A single-shuffle run on the C1 scans reproduces the new-engine run almost entirely (27 detectable, the same three programs change, 29 pairs moved by 0.03 or more vs 28, H7.2 0.863 vs 0.862, nearest-is-family 0.565, UPGMA triplet 0.779 vs 0.763, Phase B H7.7 flip the same). So the change in the registered results appears between C0 and C1 and is attributed to the signal split; the other 119 commits add only small differences (for example the triplet score 0.779 to 0.763).
* **Why a modest data change gives visible changes in the single-shuffle numbers** (added after seeing the results, descriptive; `seed_noise.py`): re-drawing only the decoy shuffle on the **unchanged original scans** moves on average 31 ordered pairs by 0.03 or more (range 24 to 39; the engine change moved 28), and moves the detectable count between 25 and 28. The single-decoy cutoff sits on a cliff (Amendment 2 section A), and any small change to the data pushes some pairs over it. The registered single-shuffle numbers are therefore sensitive to small perturbations in general, whatever their source.

## Side by side: the registered E7 numbers

"Real by the pre-stated rule" is the rule written in the registration note: outside the original's own interval, or a program crossing the 2% floor, or a flipped verdict; quantities with no interval count as "moved" at a change of 0.05 (0.5 for a median rank). A "real" mark is not an attribution; see the previous section for that.

| Quantity | ORIGINAL (704cb35f0) | NEW ENGINE (beb46cfbc) | change | real by the pre-stated rule |
|---|---:|---:|---|---|
| Programs with detectable descent at the 2% floor (struct), of 51 | 25 | 27 | changed | REAL (crossed: doomretro, gzdoom) |
| Programs with detectable descent at the 2% floor (names), of 51 | 41 | 41 |  | no (crossed: none) |
| Nearest-is-family, corrected rule, struct, common set (orig 25) | 0.619 | 0.565 | changed | no (orig exact CI 0.38 to 0.82 on 13/21) |
| Nearest-is-family, corrected, struct, own detectable set | 0.619 | 0.565 | changed | no (orig exact CI 0.38 to 0.82 on 13/21) |
| Nearest-is-family, corrected, names, common set | 0.714 | 0.652 | changed | no (orig exact CI 0.29 to 0.96 on 5/7) |
| Nearest-is-family, corrected, names, own detectable set | 0.600 | 0.600 |  | no (orig exact CI 0.15 to 0.95 on 3/5) |
| Nearest-is-family, old root-sibling rule (inflated), struct, common | 0.762 | 0.696 | changed | moved |
| Nearest-is-family, old root-sibling rule (inflated), names, common | 0.714 | 0.696 | changed | no |
| Declared parent rank, mean, struct, common | 8.570 | 9.200 | changed | moved |
| Declared parent rank, median, struct, common | 3.800 | 4.500 | changed | moved (>= 0.5 rank) |
| Declared parent rank, median, names, common | 2.000 | 2.000 |  | no |
| Resolved-triplet compatibility with declared tree, UPGMA struct | 0.848 | 0.763 | changed | moved |
| Resolved-triplet compatibility with declared tree, UPGMA names | 0.869 | 0.849 | changed | no |
| Clade recall (declared clades recovered), UPGMA struct | 0.200 | 0.200 |  | no |
| Names tree vs structure tree, UPGMA quartet distance | 0.177 | 0.180 | changed | no |
| Names tree vs structure tree, UPGMA normalised RF | 0.579 | 0.667 | changed | moved |
| Programs detectable under both (M4 set) | 22 | 24 | changed | set size follows detectability |
| Spearman shared-names vs shared-structure, all 1,275 pairs | 0.401 | 0.413 | changed | no |
| H7.2: Spearman, C-family pairs above floor under both | 0.809 (n=112, [0.596, 0.930]) | 0.862 (n=111, [0.742, 0.941]) | changed | no (inside original interval) (verdict: interval includes values below 0.80 in both) |
| H7.1: ports where structure is closer to text survival (exact+near), of 22 | 21/22 | 21/22 |  | no (orig exact CI 0.77 to 1.00) |
| H7.1 on exact+near+derived | 19/22 | 19/22 |  | no (orig exact CI 0.65 to 0.97) |
| Spearman vs name-blind text survival, structure | 0.865 [0.611, 0.975] | 0.86 [0.608, 0.970] | changed | no (inside original interval) |
| Spearman vs name-blind text survival, names | 0.928 [0.775, 0.977] | 0.928 [0.775, 0.977] |  | no (inside original interval) |
| H7.4: false attachments among large unrelated controls, structure | 1 | 1 |  | no |
| H7.4: false attachments among large unrelated controls, names | 1 | 1 |  | no |
| H7.3: cross-language ports struct leaves undetected that attach to a declared family under names | 2/6 | 2/6 |  | see scorecard |
| Phase B positives attached to a family member (structure), of 5 | 3/5 | 3/5 |  | no |
| Phase B false attachments, negatives >= 150 functions (structure), of 3 | 0/3 | 0/3 |  | no |
| Phase B correct placements, 14 scored (structure) | 11/14 [0.49, 0.95] | 12/14 [0.57, 0.98] | changed | no (inside original CI) |
| Phase B positives attached to a family member (names), of 5 | 4/5 | 4/5 |  | no |
| Phase B false attachments, negatives >= 150 functions (names), of 3 | 0/3 | 0/3 |  | no |
| Phase B correct placements, 14 scored (names) | 12/14 [0.57, 0.98] | 12/14 [0.57, 0.98] |  | no (inside original CI) |
| Phase B leave-one-out, 8 mapped ports (structure) | 6/8 [0.35, 0.97] | 6/8 | changed | no (inside original CI) |
| Phase B leave-one-out, 8 mapped ports (names) | 7/8 | 7/8 |  | no |
| Scorecard H7.6 | not met. | not met. |  | no |
| Scorecard H7.7 | falsified (names higher). | not falsified. | changed | REAL (verdict flipped) |


Phase B programs whose placement changed (struct nearest | names nearest | struct verdict | names verdict):

- `iron-doom`: none (0.0046) | none (0.0142) | ok | ok  ->  none (0.0045) | none (0.0142) | ok | ok
- `doome`: none (0.0041) | none (0.0004) | ok | ok  ->  none (0.0041) | none (0.0000) | ok | ok
- `c-raycasting`: none (0.0085) | none (0.0038) | ok | ok  ->  none (0.0085) | none (0.0085) | ok | ok
- `goom3d`: curl (0.0219) | none (0.0038) | MISS | ok  ->  none (0.0117) | none (0.0038) | ok | ok
- `derp`: linuxdoom (0.7092) | linuxdoom (0.8863) | ok | ok  ->  linuxdoom (0.7273) | linuxdoom (0.8863) | ok | ok
- `d2k`: prboom-plus (0.5577) | prboom-plus (0.7977) | ok | ok  ->  prboom-plus (0.5346) | prboom-plus (0.7977) | ok | ok
- `cpp-doom`: none (0.0108) | crispy-doom (0.8982) | MISS | ok  ->  none (0.0097) | crispy-doom (0.8982) | MISS | ok
- `broom`: doom-wasm (0.4622) | sdl-doom (0.7798) | ok | ok  ->  doom-wasm (0.4483) | sdl-doom (0.7798) | ok | ok

## Side by side: Amendment 2 (pooled decoys, K = 25) and the 2% floor

Fixed set = the 25 programs E7 called structurally detectable. P-A1 uses "active pair = share of at least 0.02 under the primary or the conservative rule", the definition that reproduces the original 352 pairs.

| Amendment 2 quantity (K = 25) | ORIGINAL | NEW ENGINE | change | real |
|---|---:|---:|---|---|
| Programs detectable at floor 0.02, E7 single shuffle | 25 | 27 | changed | REAL |
| Programs detectable at floor 0.02, primary rule | 35 | 35 |  | REAL |
| Programs detectable at floor 0.02, conservative rule | 25 | 23 | changed | REAL |
| Programs detectable at floor 0.03, E7 single shuffle | 25 | 24 | changed | moved |
| Programs detectable at floor 0.03, primary rule | 30 | 30 |  | no |
| Programs detectable at floor 0.03, conservative rule | 23 | 23 |  | no |
| Programs detectable at floor 0.05, E7 single shuffle | 22 | 22 |  | no |
| Programs detectable at floor 0.05, primary rule | 23 | 23 |  | no |
| Programs detectable at floor 0.05, conservative rule | 20 | 20 |  | no |
| Programs detectable at floor 0.08, E7 single shuffle | 20 | 20 |  | no |
| Programs detectable at floor 0.08, primary rule | 20 | 20 |  | no |
| Programs detectable at floor 0.08, conservative rule | 18 | 18 |  | no |
| programs crossing the 2% floor, single | | | gained: doomretro, gzdoom; lost: none | |
| programs crossing the 2% floor, primary | | | gained: agentic-cobol-doom-cc; lost: freedoom | |
| programs crossing the 2% floor, conservative | | | gained: none; lost: doomsday, edge-classic | |
| Nearest-is-family on E7's fixed 25-program set, single | 0.619 | 0.619 |  | no (orig exact CI 0.38 to 0.82) |
| Nearest-is-family on E7's fixed 25-program set, primary | 0.619 | 0.619 |  | no (orig exact CI 0.38 to 0.82) |
| Nearest-is-family on E7's fixed 25-program set, conservative | 0.619 | 0.571 | changed | no (orig exact CI 0.38 to 0.82) |
| Nearest-is-family on each rule's own detectable set, primary | 0.560 | 0.560 |  | no |
| Nearest-is-family on each rule's own detectable set, conservative | 0.619 | 0.600 | changed | no |
| P-A1: share of active pairs with cutoff above zero (primary) | 0.989 of 352 | 0.991 of 334 | changed | no |
| Stability classes among active pairs (stable-certified / stable-uncertified / unstable) | 156/116/80 | 149/104/81 | changed | descriptive |
| Convergence K=12 vs K=25 (share of active pairs differing by > 2% of elig_q; bound 5%) | 0.020 | 0.042 | changed | no |
| P-A4: largest share of an unrelated control with any program (primary), bound 0.10 | 0.028 | 0.030 | changed | no |
| Cross-language background (primary): 95th / 99th percentile / max, share above 0.02 | 0.010 / 0.025 / 0.083, 0.020 | 0.010 / 0.022 / 0.085, 0.016 | changed | descriptive |

Ports whose share with `linuxdoom` under the primary rule moved by at least 0.03 (`material` by the pre-stated rule):

- none

## Programs whose detectability, nearest relative or placement changed

**Phase A, E7's registered single-shuffle rule** (`attribution/program_changes_phaseA_single_shuffle.md`; the #8939-only run gives the identical list):

| program | detectable | nearest relative, old | best share, old | nearest relative, new | best share, new |
|---|---|---|---:|---|---:|
| `doomretro` | no to yes | none | 0.0051 | `woof` | 0.0439 |
| `gzdoom` | no to yes | none | 0.0185 | `odamex` | 0.0204 |
| `edge-classic` | yes to yes | `eternity` | 0.0477 | `doomsday` | 0.0256 |

The names arm: **no program changed** detectability or nearest relative. Of 2,550 ordered name pairs only the 50 involving `odamex` differ (5,541 to 5,545 eligible functions: a function-extraction change), the rest are identical.

**Amendment 2 pooled rule (K = 25)** (`attribution/program_changes_amendment2_primary.md`): `freedoom` goes from detectable to not (`srb2` 0.0250 to 0.0194, 111 functions); `agentic-cobol-doom-cc` from not to detectable (`gzdoom` 0.0336; the program has 47 functions); nearest relative changes for `doomretro` (`woof` 0.0350 to `inter-doom` 0.0271), `gzdoom` (`edge-classic` 0.0222 to `agentic-cobol-doom-cc` 0.0336), `doom3-bfg` (`linuxdoom` 0.0467 to `eternity` 0.0446) and `doomsday` (`eternity` 0.0323 to `doom3-bfg` 0.0343). All are cross-language or near-floor programs. Under the conservative rule `doomsday` and `edge-classic` drop below the floor. No program that carries a conclusion (the ports with shares above 0.05) changed.

**Phase B (registered single-shuffle rule):** `goom3d` MISS to ok (attaches to `curl` at 0.0219, now 0.0117; 47 functions, below the 100-function minimum-evidence line); leave-one-out `gzdoom` MISS to ok and `edge-classic` ok to MISS (net 6 of 8 both times); the four positives `derp`, `d2k`, `broom`, `cpp-doom` keep their placements and verdicts (structure shares move by 0.014 to 0.023). `cpp-doom` is still placed under names only.

## Registered expectations against the outcome

| Expectation (written before the scans) | Outcome |
|---|---|
| Detectable programs (structure) 25 plus or minus 2 | 27: inside, at the edge |
| Nearest-is-family (common set) within 0.05 of 0.62 | 0.565 on each run's own set: **outside** (0.054 off); 0.619 on E7's fixed 25 |
| H7.1 20 to 22 of 22 | 21: as expected |
| Spearman vs text survival 0.87 plus or minus 0.04 | 0.860: as expected |
| Triplet compatibility 0.848 plus or minus 0.03 | 0.763: **outside** |
| Names columns identical except where extraction changed | as expected (only `odamex`) |
| Phase B the same | **partly wrong**: H7.7 flipped; `goom3d`, `gzdoom`, `edge-classic` changed |
| Amendment 2: fixed-set 0.619 plus or minus 0.05, H7.1 21 of 22, detectable 35 plus or minus 3 | all as expected |
| No scorecard verdict flips | **wrong**: H7.7 (Phase B) and P-A3 (Amendment 2) flipped |

## What I could not separate

* The Amendment 2 differences are small (2 programs swap at the floor, 3 pairs move by 0.03 or more). I ran the K = 25 draws only on the new engine (55 minutes of heavy slot), not at #8939, so I cannot say how much of that is #8939 and how much the other 119 commits. The Phase A single-shuffle comparison says #8939 does nearly all of it.
* Which of the nine fixes in #9111 changes C function signals, and why.
* The Phase B flip of H7.7 rests on one 47-function program crossing a cliff; I did not repeat Phase B with several decoy seeds (Amendment 2 left Phase B on the single shuffle), so I cannot say whether `goom3d` would also flip on the original engine with another seed. `doomretro` and `gzdoom` in Phase A do (17 and 19 of 25 draws).
* Whether the shift would be larger with a reference scaler refitted after #8939. The reference model was not retrained (spec_hash unchanged), so the scaled `branch` feature now sits slightly lower for functions with boolean operators; that is the registered pipeline's behaviour and I did not change it.

## What this does not show

It does not show that structure tracks ancestry better, or worse, than names. It shows that E7's measurements, taken on 66 specific programs with one scanner, are not sensitive to the call-graph and import-graph work, are sensitive in their registered single-shuffle form to small perturbations of any kind, and are stable in their pooled (Amendment 2) form against a signal change that touched a fifth of all functions. It does not test other languages' call-graph quality, other programs, or an engine that changes the slicer or the reference model. The comparison is one run per engine; the names arm and text arbiter are deterministic, the structure arm is deterministic given the decoy seeds. The "real" marks follow my pre-stated rule, which is generous to calling a change real for small counts. The added analyses (control scans, #8939-only run, bisect, decoy-draw noise) were designed after seeing the first results; they are descriptive and carry no registered threshold.

## Deviations from the original procedure (all checked not to matter by the C0 control)

* The original scanned the pinned clones in place; I copied each clone's scoped working tree (without `.git` and `.gitgalaxy`) into a fresh scratch git repo with `git add -f -A` and scanned that (the brief's rule). The C0 control shows the function tables are identical on all 66.
* `e7_run.py --workers 3` instead of the default 6 (box etiquette); results identical (C0).
* The sfs checkout is the one the original used (`b1a9e92`, differs from the pin file's `bcd3cb7` only in files outside the matching code, as Amendment 2 section F records).
* The text arbiter was rerun on the new scans (it reads function line ranges from the scan database), from source trees rebuilt from the frozen clones.
* Script changes: `measure_new_engine/` holds copies of `measure/e7_*.py`. The only edits: work directory and engine short SHA now come from environment variables `E7_WORK` and `E7_ENGINE` (`e7_run.py`, `e7_analyze.py`, `e7_phaseb.py`); `e7_draws.py` requires `--work` and `--out`; `e7_supp_table.py` reads `E7_A2` and `E7_SUPP_OUT`. Analysis logic is byte-identical (`diff measure/e7_analyze.py measure_new_engine/e7_analyze.py`). New files: `scan_programs.py`, `compare_scans.py`, `compare_all.py`, `a2_summary.py` (reproduces the quantities quoted in `E7_AMENDMENT_2_RESULTS.md` on the original data: 352 active pairs, 98.9%, 156/116/80, 2.0%, floor table, 1,216 cross-language pairs), `side_by_side.py`, `program_changes.py`, `pair_shift.py`, `seed_noise.py`, `attribution_check.py`, `run_pipeline.sh`; tests in `tests/test_new_engine_helpers.py`.
* Order of operations was the original's: all 66 scans, Phase A and arbiter and analysis (committed, `bb4ce31`), then Phase B (`544f5e6`), then the Amendment 2 draws.

## Repeat it

```
export PATH=/srv/storage_16tb/projects/gitgalaxy/venvs/selfscan/bin:$PATH
W=/srv/storage_16tb/projects/doom-e7-newengine-work; M=measure_new_engine
python $M/scan_programs.py --engine <engine worktree at beb46cfbc65391bd210dda4175045c78b1e96047> --work $W/new
bash $M/run_pipeline.sh new beb46cfbc A      # Phase A, arbiter, analysis
bash $M/run_pipeline.sh new beb46cfbc B      # Phase B
bash $M/run_pipeline.sh new beb46cfbc A2     # pooled K = 25 draws, both analyses, summary, supplement
```
Controls: same with `--engine` at `704cb35f0` (`c0`) and `3c436c8c57` (`c1`), then `python $M/compare_all.py --out $W/compare`. Command log: `results/e7_new_engine/logs/*_commands.txt`; scan logs and pipeline logs in the same folder; per-program fingerprints in `$W/new/results/e7/phaseA/fingerprints` and `.../phaseB/fingerprints`.
