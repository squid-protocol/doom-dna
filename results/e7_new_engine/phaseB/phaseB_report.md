# DOOM-E7 Phase B results
Pairwise nearest-neighbour placement on the frozen Phase A map (not tree insertion). A program attaches if its largest shared reaches the 2% floor.

| program | role | eligible | struct nearest (shared) | names nearest (shared) | expected | struct | names |
|---|---|---:|---|---|---|:-:|:-:|
| cydoomgeneric | phase-B1-withheld | 971 | sdl-doom (0.9060) | sdl-doom (0.9641) | attach to family of doomgeneric | MISS | MISS |
| iron-doom *(diagnostic, unscored)* | phase-B1-withheld | 227 | none (0.0045) | none (0.0142) | no detectable descent | ok | ok |
| doomarkable | phase-B1-withheld | 30 | none (0.0002) | none (0.0003) | no detectable descent | ok | ok |
| DOOM-style-Game | phase-B1-withheld | 39 | none (0.0142) | none (0.0045) | no detectable descent | ok | ok |
| doome | phase-B1-withheld | 380 | none (0.0041) | none (0.0000) | no detectable descent | ok | ok |
| carddemo-cobol-ctrl | phase-B1-withheld | 37 | none (0.0048) | none (0.0038) | no detectable descent | ok | ok |
| c-raycasting | phase-B1-withheld | 21 | none (0.0085) | none (0.0085) | no detectable descent | ok | ok |
| c-raycasting2 | phase-B1-withheld | 18 | none (0.0099) | agentic-cobol-doom-cc (0.0310) | no detectable descent | ok | MISS |
| goom3d | phase-B1-withheld | 47 | none (0.0117) | none (0.0038) | no detectable descent | ok | ok |
| bubbletea | phase-B1-withheld | 509 | none (0.0011) | none (0.0000) | no detectable descent | ok | ok |
| macroquad | phase-B1-withheld | 614 | none (0.0089) | none (0.0006) | no detectable descent | ok | ok |
| derp | phase-B2-positive | 5325 | linuxdoom (0.7273) | linuxdoom (0.8863) | attach to family of linuxdoom | ok | ok |
| d2k | phase-B2-positive | 3573 | prboom-plus (0.5346) | prboom-plus (0.7977) | attach to family of prboom-plus | ok | ok |
| cpp-doom | phase-B2-positive | 2094 | none (0.0097) | crispy-doom (0.8982) | attach to family of crispy-doom | MISS | ok |
| broom | phase-B2-positive | 2276 | doom-wasm (0.4483) | sdl-doom (0.7798) | attach to family of linuxdoom | ok | ok |

## Scores (iron-doom excluded from both denominators; it is an unscored diagnostic)
- **structure**: sensitivity 3/5; false attachments 0/3 among negatives with at least 150 functions (bubbletea, doome, macroquad), 0/6 among underpowered negatives (DOOM-style-Game, c-raycasting, c-raycasting2, carddemo-cobol-ctrl, doomarkable, goom3d); correct placements 12/14 (exact 95% CI [0.57, 0.98]).
- **names**: sensitivity 4/5; false attachments 0/3 among negatives with at least 150 functions (bubbletea, doome, macroquad), 1/6 among underpowered negatives (DOOM-style-Game, c-raycasting, c-raycasting2, carddemo-cobol-ctrl, doomarkable, goom3d); correct placements 12/14 (exact 95% CI [0.57, 0.98]).
- **Always-null baseline** (never attaches): sensitivity 0/5, correct placements 9/14.

**H7.6** (structure: every positive attaches correctly and no false attachment among negatives with at least 150 functions): sensitivity 3/5, false attachments 0/3 -> not met.
**H7.7** (names' correct-placement count at most structure's, falsified if names is higher): names 12/14 vs structure 12/14 -> not falsified.

## Leave-one-out placement (8 mapped ports with the most eligible functions and a declared parent in the map)
| port | declared parent | struct nearest (shared) | names nearest (shared) | struct | names |
|---|---|---|---|:-:|:-:|
| gzdoom | linuxdoom | odamex (0.0204) | dartdoom (0.2461) | ok | ok |
| srb2 | linuxdoom | lua (0.0984) | linuxdoom (0.3646) | MISS | ok |
| odamex | linuxdoom | doom-wasm (0.0888) | doo-cr (0.5499) | ok | ok |
| eternity | linuxdoom | doom-wasm (0.0982) | linuxdoom (0.5594) | ok | ok |
| edge-classic | linuxdoom | doomsday (0.0256) | doom3do (0.0594) | MISS | MISS |
| dsda-doom | prboom-plus | prboom-plus (0.3044) | linuxdoom (0.6390) | ok | ok |
| nugget-doom | woof | woof (0.7478) | woof (0.7183) | ok | ok |
| woof | linuxdoom | nugget-doom (0.7478) | nugget-doom (0.7183) | ok | ok |

Leave-one-out sensitivity: structure 6/8 (exact 95% CI [0.35, 0.97]), names 7/8 (exact 95% CI [0.47, 1.00]). Correct = nearest program is the declared parent or a declared relative of it.

## Diagnostics (read with the scores; the scoring above is as registered)
- **cydoomgeneric** is scored a miss by both methods only because its top match, `sdl-doom`, is not a declared relative of its anchor `doomgeneric`. Shared with `doomgeneric`: structure 0.890, names 0.949; with `sdl-doom`: structure 0.906, names 0.964. The two are within about 0.02 of each other, and Phase A already showed `doomgeneric` and `sdl-doom` share almost everything.
- **cpp-doom** (C++ fork of Crispy Doom): structure shares 0.0003 with `crispy-doom` (the C to C++ change rewrites the measurements), names 0.898. Names track a translation that structure cannot.
- Anchors `linuxdoom` (derp, broom) count every declared descendant of linuxdoom as family, which is lenient: any DOOM port passes. The nearest programs are listed in the table.
- `goom3d` (structure, 47 functions) and `c-raycasting2` (names, 18 functions) attach just above the 2% floor but are below the 100-function minimum evidence, so they are flagged underpowered, not scored as false attachments against the methods.
