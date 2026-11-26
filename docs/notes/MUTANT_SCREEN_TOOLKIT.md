# Mutant screen toolkit (plan, 2026-11-26)

**Idea (owner):** define a function by its *role*, the phenotype it shows when broken, not by its name or structure; then ask how functions that play the same role diverged across ports. It is a forward-genetics mutant screen: saturate every function with small lesions, record the phenotype in a standard assay (deterministic demo replay), call "orthologs" by phenotype, then study how sequence (structure), name and size drifted while the phenotype held.

| Genetics | Here |
|---|---|
| gene | function |
| mutagenesis | one-token lesions (operator, comparison, constant, shift) at every site |
| assay | deterministic demo replay, per-tic digest of player + world fingerprint, compared with the same port unmutated |
| phenotype | which demos fail, at which tic, in which field (player / monster / sector / keys / RNG) |
| ortholog by phenotype | functions in two ports whose lesion phenotypes match |
| complementation (stretch) | swap a function between near-clone ports and see if the game still replays |
| epistasis (stretch) | double lesions in two functions |

## Layers and what exists
| Layer | Job | Status |
|---|---|---|
| L0 instrumentation | per-tic digest (all engines), RNG trace by caller, reach probe | done for C family, C#, Java, Kotlin, Go; Rust/puredoom player-only |
| L1 **schemata mutagenesis** | one build per port; every lesion is a runtime switch (env var), no rebuild per mutant | **building now (C first)**; C#, Java, Kotlin, Rust, Go emitters follow; tree-sitter parses all six |
| L2 phenotype runner | runs (mutant, demo) jobs, **aborts at first divergence**, resumable, resource-governed, results in one table | to build |
| L3 demo suite + coverage | demos reaching every simulation function, measured by the reach probe; greedy set cover | 42 demos reach ~140/230 simulation functions; needs targeted demos |
| L4 phenotype store | table of (port, function, site, op) x (demo -> outcome, tic, field) | to build |
| L5 analysis | phenotype similarity, ortholog calling, calibration against names, confusion matrix against the structural matcher, divergence studies | pilot analysis exists (E14) |
| Skill / CLI | `mscreen` CLI and a project skill so a new port can be screened by anyone | after L1-L2 work |

## Why schemata
E14 used one rebuild per mutant (about 1 minute); a full screen of one port is ~2,000 mutants x 42 demos. With schemata a port needs one build; with early abort a killed mutant costs the demo prefix up to the first divergence. Estimated cost of a full screen: about 2 hours per C port, instead of 30+.

## Validation (before any scientific use)
Schemata must reproduce rebuilt mutants: draw 25 mutants, build each classically (edit the same source bytes), run the same demos, and require identical outcomes (kill set, first tic, field) to the schemata run. Unbuildable or ill-typed sites are dropped by a compile-error loop and tabulated.

## Milestones
1. C schemata for chocolate-doom, validated (now). 2. Runner with early abort + store. 3. Dynamic profile (per-function entry counts and first tic) from the same build. 4. C# managed-doom, prboom-plus, then the other C ports. 5. Java/Kotlin/Go/Rust. 6. Targeted demos to reach more functions. 7. Registration of the role-matching study with two independent reviews, then the screen of all runnable ports.

## Limits (to repeat in every report)
Simulation functions only (rendering, menu and sound do not appear in headless demos); equivalent mutants are indistinguishable from unreached code without coverage; DOOM 1 shareware content only; one-token lesions are not realistic translation errors; a function split in two by a port is a one-to-many role.
