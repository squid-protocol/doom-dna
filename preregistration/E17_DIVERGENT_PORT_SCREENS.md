# E17 (DRAFT v1, 2026-11-27): full lesion screens of divergent ports (Mocha Doom, gore) and what they add

**Status: DRAFT; needs two independent reviews, a dated reconciliation and a commit before any screen outcome is read.** Builds on E15 (screens of chocolate-doom, managed-doom, prboom-plus: faithful ports) and E16 (symptom diagnosis). The two engines were built and validated without reading outcomes (Mocha: zero-lesion replay 77/77, classical-rebuild equivalence 20/20, clean digests deterministic; gore: pending).

## Why
E15 found that for faithful translations, clean call-count profiles identify partner functions as well as or better than lesion phenotypes (N0), so lesions' added value was not shown. The question that remains is whether phenotypes add information where the ports are **not** faithful. Mocha (Java; matches chocolate-doom's digests on only 49 of 77 demos) and gore (Go; diverges on 69 of 77) are such ports. Each lesion is compared with the port's **own clean digest** (self-differential), so divergence from chocolate-doom does not enter the lesion outcome.

## Design
* Same lesion kinds, ids, exclusions (shift and index lesions out of the primary analysis), hot and inert classes, demos (the 77), runner and analysis pipeline as E15, unchanged; per-port frozen definitions in E15 apply. Screens are run one port at a time under the shared-box rules (max 3 workers, niced).
* **Partner definition (frozen before outcomes):** function pairs between each new port and chocolate-doom by (i) the E12 structural matches (twin tiers and extension tiers) and (ii) name agreement after prefix stripping. A pair is **name-agree** if (ii) holds and the name is unique in both ports. Call-count identity across ports is no longer required.
* **Clean baselines for every pair:** call-count profile distance computed from each port's own clean entry counts on the 77 demos (N0, as in A4), and the E7 text arbiter where available.

## Hypotheses (primary unless marked)
* **H-B1 (primary): lesions add information where call counts cannot decide.** On name-agree pairs of each new port with chocolate-doom, partner recovery by the lesion phenotype distance (E15 D) is **at least 0.10 higher in top-5 (paired cluster bootstrap over functions, lower bound > 0)** than recovery by the call-count profile distance, in the pooled Mocha and gore pairs; E15's faithful-port gap (N0 at least as good as lesions) is the contrast. Reported separately for each port; the pooled test is the primary.
* **H-B2: lesion-effect families recur.** At least 8 of the 11 E15 lesion-effect families have a profile in each new port within 0.4 (E15 metric) of the chocolate-doom family profile.
* **H-B3 (descriptive, with audit):** name-agree pairs whose phenotype distance exceeds the E15 5th-percentile threshold of random cross-port pairs are listed and audited by two reviewers; the share confirmed as real role differences (not noise, not hot-or-inert artefacts) is reported.
* **H-B4: SFS confidence.** The size-aware confidence score from the SFS calibration keeps **AUC >= 0.75** for predicting behavioural confirmation (D at or below the 5th percentile and the same call-profile class) on the new ports' structural twin and extension pairs.
* **H-B5 (E16 follow-up, descriptive):** diagnosis with the chocolate-doom dictionary of Mocha lesions at the family-removed condition: top-5 against the baselines, in the more divergent port (the transplant upper bound is E16's T1).
* **Controls:** shuffled partners (chance), within-function split-half ceiling (PC1f), the E15 gates PC1g (cross-port reproducibility of hot and inert classes), and a ceiling from identical-text pairs where they exist.
* **Pre-declared null:** if H-B1 fails, phenotype distance is not distinguishable from call counts even for unfaithful ports at this resolution, and the lesion programme's value is reduced to the calibration data and families.

## Limits
Two divergent ports are two points; Mocha is itself the source of Kocoa; gore diverges on most monster demos, so its screen measures lesion effects on code that already fails monster behaviour (reported by demo family); Kocoa (Kotlin, fully divergent but unscreenable without a Kotlin engine and Freedoom loading) is deferred.
