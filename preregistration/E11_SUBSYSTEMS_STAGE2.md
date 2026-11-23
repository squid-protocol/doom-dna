# DOOM-E11 stage 2 (DRAFT, not registered): how much of `linuxdoom`'s call-graph architecture does each port keep?

**Status: DRAFT 2026-11-23. Becomes REGISTERED when two independent design reviews are reconciled in a dated section and this file is committed before any placement or measurement.** Stage 1 ([results](../results/e11/E11_STAGE1_RESULTS.md)) showed that Louvain finds stable, meaningful groups ("subsystems") in `linuxdoom`'s call graph (19 groups, 16 of 10 or more functions, ARI 0.78, NMI 0.52 with the hand taxonomy). Stage 2 asks whether ports keep that architecture, measured against chance, with placement that does not use names or file paths.

## Question and why it is harder than it looks
The old wiring chart placed functions by name and file path (so it was "not blind") and the scanner's own note says a placement made by aligning call graphs "imposes the reference's shape" and makes reimplementations look like DOOM. So placement has to come from something other than names, paths, or the call graph being measured.
**Placement used here:** structural twins (name-blind function fingerprints, E7 Amendment 2 pooled K = 25 cutoff, either direction, one-to-one) between the port and `linuxdoom`. A port function that is the twin of a `linuxdoom` function takes that function's group. Only twin-matched port functions are placed; coverage is reported and is a result.
**Honest limit stated up front:** for a same-language port, copied functions keep their calls, so preserved wiring among twin functions is partly the retention of copied code. Stage 2 therefore measures (a) how far the imported groups remain real communities of the port's own call graph, which a copy-and-extend port should satisfy, and (b) how the answer falls with coverage and across ports. It is a **calibration ceiling** for the translation case, not that case. Translations (Go, Scheme, Fortran, Java, Kotlin, C#, Dart) have no usable structural twins; placing them needs a mapping that is neither name-based nor call-graph-aligned, which does not exist in the pipeline and is **out of scope** here (to be stated as an open problem, not papered over).

## Design
* **Reference partition:** `linuxdoom` Louvain, resolution 1.0, **consensus over 100 seeds** (co-association matrix clustered at 0.5), reducing seed noise. Sensitivity: seed-0 partition; resolutions 0.5 and 2.0; the hand taxonomy (file-name prefix) as an alternative reference.
* **Programs:** same-language (C and C-family) DOOM ports with at least **100 placed functions and 150 calls among them** (listed after placement, before any metric); unrelated programs (`nginx`, `curl`, `lua`) and from-scratch rewrites, reported with their coverage (expected insufficient); `helion`, `rust-doom` cross-language, expected unplaced.
* **Placement:** twins port to `linuxdoom` in both directions, union, one-to-one (each `linuxdoom` function used once), E7 Amendment 2 pooled cutoff, K = 25; engine `704cb35f0`; fingerprints from the E7 phase A set. Reported per port: eligible functions, placed functions, coverage of `linuxdoom`.
* **Metrics, each on the placed functions and the port's own call graph among them:**
  * **M1 modularity gap:** modularity of the imported labelling on the port's induced graph, against the same labelling shuffled among the placed functions (1,000 shuffles; group sizes preserved); z score.
  * **M2 agreement with the port's own groups:** NMI between the imported labelling and the port's own Louvain partition (30 seeds, median), against a label-permutation null and against the **ceiling** (the port's own seed-to-seed stability on the same functions).
  * **M3 cross-wiring gap:** cosine between the off-diagonal group-to-group call matrix of the port's placed functions and `linuxdoom`'s matrix **restricted to the matched `linuxdoom` functions**, against the shuffled-label null; gap = real minus null mean.
  * **Edge retention (descriptive):** share of calls among matched `linuxdoom` functions that exist among their port twins.
* **Controls:** (i) the shuffled-label null for every metric; (ii) unrelated programs (reported, not scored, when coverage is insufficient); (iii) a **destroyed-structure control**: for each port, the imported labels with function-to-label assignment permuted within `linuxdoom`'s file (keeps file adjacency, breaks the subsystem mapping); (iv) the hand taxonomy as reference to see whether Louvain groups travel better.

## Predictions (before any placement)
* **P1:** for each same-language port with coverage of at least 0.30 of `linuxdoom` (expected: `chocolate-doom`, `crispy-doom`, `doomgeneric`, `sdl-doom`, `doom-ascii`, `doom-wasm`), M1 z is at least 5 and M2 NMI is above the permutation null's 95th percentile.
* **P2:** M2 reaches at least 50% of its ceiling for those ports.
* **P3:** M3 gap is positive for at least 5 of those 6.
* **P4:** the faithful, high-coverage ports score higher on M1 than the heavily restructured ports with coverage under 0.15 (`prboom-plus`, `woof`, `dsda-doom`, `eternity`), where placed functions are few; any port under the 100-function floor is listed as insufficient, not as zero.
* **P5:** the destroyed-structure control scores far lower than the true placement on M1 and M2 for every scored port (otherwise M1 and M2 do not measure subsystem structure).
* **P6:** unrelated programs and from-scratch rewrites have insufficient coverage; none is scored. If any has enough placed functions, its M1 z is below 5.
* **P7:** Louvain-derived labels give a higher M1 than the hand taxonomy for at least 4 of 6 faithful ports (they optimise modularity on the reference), reported without a claim that Louvain "is better".
Failed predictions are reported as failed. The headline is descriptive: which ports keep the subsystem structure, at what coverage, against chance.

## Limits
Same-language only (see above). Placement covers only twin-matched functions; port-unique code is invisible to the metric. Louvain depends on resolution; the sweep is reported. The reference and the metrics share the call graph of the reference program, which is why M2 uses the port's own graph and a ceiling, and why the destroyed-structure control is required. Third-party source is not committed.
