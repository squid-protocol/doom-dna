# E14 (DRAFT 2026-11-26): do structurally matched functions play the same role? Break them the same way in several ports.

**Status: DRAFT, not registered.** Needs two independent design reviews (Claude subagent + Gemini, read-only, blind to results) reconciled in a dated section, then a commit, before any mutant is built. Proposed by the owner after E13 Part A (the localiser failed its registered primaries, `results/e13/E13_PART_A_RESULTS.md`).

## Question
Our matcher says function X in port P and function Y in port Q have the same structure (name-blind). Do they have the same *role*? Operational test: apply the **same one-token change** at the **same site** in both, run the same demos, and compare how the game breaks.

## Design (proposed)
1. **Function set.** Functions matched (E12 ladder, exact tier and the next tier, files in `doom-e7-work/gene-view`) between the reference port and **every** port in the panel, ranked by conservation (number of ports matching, then match score). Take the top 60 simulation functions (p_*, no I/O, no rendering) that call or are called by gameplay code.
2. **Panel.** Ports we can rebuild and run on our demos with the digest patch: chocolate-doom (reference), crispy-doom, prboom-plus, doomgeneric, sdl-doom, inter-doom, doom-ascii. (Non-C ports later, if the C result is interesting.)
3. **Sites.** In each conserved function, enumerate mutation sites (as in E13) in the reference; map each to the matched site in each port by operator and ordinal position within the function, **kept only where the two functions' site lists have the same operator sequence** (else the site is unmatched and is skipped; count reported).
4. **Signature of a break.** Detected or not (45 demos, E13 set); on detected: the set of failing demos, first diverging field and tic per demo, and the divergence class (position / health / RNG / world-hash only). Behaviour is deterministic, so the same engine behaviour gives the same signature.
5. **Agreement score** for a mutant pair: (a) same detected/not detected; (b) Jaccard similarity of failing-demo sets; (c) same first-field on the shared failing demos.
6. **Controls (the point of the design).** (i) *Within-port control:* the same mutation applied in the **same port but a different function of the same file** (same operator, same size decile). (ii) *Mismatched pair:* the matched mutation in port P versus a mutation in a **non-matched** function of port Q. (iii) *Non-conserved matched functions* (lowest conservation) as a dose-response check. If agreement for matched pairs is no higher than for controls, then matched structure does not imply same role at this resolution.

## Predictions (to be tightened at review)
* **S1:** detection agrees for >= 85% of matched pairs, against <= 65% for mismatched pairs.
* **S2:** mean Jaccard of failing demos is at least 0.3 higher for matched than mismatched pairs.
* **S3:** agreement rises with conservation (top third > bottom third).
* **S4 (what would surprise):** matched pairs agree no more than controls. Report either way.

## Limits to state
Same-language (C) ports share inherited code, so agreement partly reflects shared source, not independent convergence; the test needs the independent-lineage ports (doomgeneric from a different base, Mocha, Kocoa, gore) in a second phase. Mutation sites are matched syntactically; a one-token change can behave differently if surrounding code differs. Survivors (not detected) agree trivially; the score is reported with and without them.

## Cost / next step
Phase 1: build mutation support for the 6 other C ports (their build trees exist in `demo-study/build`), 60 functions x ~5 sites x 7 ports = ~2,100 builds; incremental relink makes each ~1 minute, run 8 wide = about 5 hours. No agent spend.
