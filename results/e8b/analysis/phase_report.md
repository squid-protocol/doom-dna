# DOOM-E8b phase report

Post hoc follow-up to E8 on largely the same ports and scans: not independent confirmation.

## Registered predictions scored

- H8b.1 (headline: progenitor beats linuxdoom, >= 5 of 6 ports and Wilcoxon p < 0.05): **fragile (primary: met)**
- H8b.1 carry-over gate (novel survival >= 0.02, interval > 0, above wrong progenitor): **met**
- H8b.2 (structure decay vs age, partial on log eligible; descriptive): **fragile**
- H8b.3 (registered progenitor in top 3 of the candidate ranking): **met**
- H8b.4 (controls: differential specificity, wrong-progenitor novel < 0.02, unrelated < 0.02): **not met**
- Class A calibration stratum: descriptive, not scored.

## Estimator choices

1. Bootstrap: 2000 draws (--B), seeded per (seed, port, sha, reference), always over FUNCTIONS never over time points; percentile 95% interval.
2. A (primary) = surv_struct_persnap_either (reference R, subset all) minus the linuxdoom value for the same snapshot (surv_struct_persnap_either_ld); per-snapshot FDR 0.01 thresholds (Amendment 1 G.13).
3. PAIRED bootstrap of A: resample the port snapshot's ELIGIBLE FUNCTIONS with replacement (one index vector shared by both arms) from found/<tag>__<ref_name>__paired.npz arrays p_in_R and p_in_LD; A* = sum(p_in_R[idx])/n_R_eligible - sum(p_in_LD[idx])/n_LD_eligible, with n_R_eligible, n_LD_eligible the stored reference-function counts. Interval = 2.5/97.5 percentiles of A*. A PASS needs A >= +0.05 and interval lower bound > 0.
4. found-file tag = first 12 characters of the snapshot sha: found/<sha12>__<ref_name>__<subset>.npz (also paired, novel).
5. Usable snapshot = dated after the progenitor (age_years > 0), eligible_snapshot >= 100, underpowered != 1, finite structural survival; earliest/second/third by date.
6. lang_c < 0.90 snapshots are excluded from the structural test against a C progenitor (not applied to edge-classic, whose progenitor EDGE is C++); excluded snapshots are listed with A_names.
7. Headline: n qualifying ports < 5 -> INCONCLUSIVE; else SUPPORTED iff n_pass >= 5 (all if n < 6) AND one-sided Wilcoxon signed-rank (H1: A > 0) p < 0.05; otherwise 'wrong comparator not supported'.
8. Leave-one-port-out: the same decision rule re-run on each (n-1)-port subset.
9. Carry-over gate per port: S_R^novel(earliest usable) >= 0.02, function-level bootstrap lower bound > 0, and above the wrong-progenitor novel survival (nearest control date); a missing novel row or missing wrong-progenitor value counts as not passing. Prediction scored 'met' iff every qualifying port passes.
10. Variants without function-level paired arrays (pooled, median-of-three, common-denominator) use the point rule A >= 0.05 only; the pooled variant uses surv_struct_pooled_either_ld if supplied, else the per-snapshot linuxdoom value (mixed).
11. H8b.2: Kendall tau-b and partial Spearman (control log(eligible_snapshot)) of POOLED-threshold survival vs age_years, snapshots after the progenitor, n >= 4; 'decay' = negative with p < 0.05; fragile iff raw and partial conclusions differ. Scored met iff median tau and median partial tau (structure, all) are both negative; fragile if their signs differ or any port is fragile in the structure/all trend; inconclusive with fewer than 3 testable ports.
12. H8b.3: top-3 gate uses rank_struct; baseline = 1/K for rank 1 and min(3,K)/K for top 3. Scored met iff every ranked port has the registered progenitor in the top 3.
13. Controls: differential specificity S_R_right > S_R_wrong (total, nearest control date); wrong-progenitor novel < 0.02; every new progenitor vs every unrelated control < 0.02.
14. Sensitivities flip a conclusion (status differs from the primary status) -> marked fragile in the scored block.

## 1. H8b.1 primary test: A at the earliest usable snapshot

| port | date | n_usable | S_R | S_LD | A | lo | hi | passed | A_names | lang_c | dup_share | qualifies |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| prboom-plus | 2000-11-29 | 6 | 0.679 | 0.213 | 0.465 | 0.417 | 0.516 | yes | 0.132 | 0.976 | 0.345 | yes |
| woof | 2008-06-17 | 6 | 0.779 | 0.184 | 0.594 | 0.560 | 0.629 | yes | 0.056 | 1.000 | 0.065 | yes |
| eternity | 2006-02-07 | 4 | 0.305 | 0.025 | 0.280 | 0.256 | 0.305 | yes | -0.145 | 0.977 | 0.123 | yes |
| edge-classic | 2021-12-12 | 6 | 0.360 | 0.000 | 0.360 | 0.353 | 0.367 | yes | 0.198 | 0.010 | 0.173 | yes |
| inter-doom | 2023-07-06 | 7 | 0.634 | 0.286 | 0.348 | 0.309 | 0.390 | yes | 0.032 | 0.999 | 0.088 | yes |
| doomretro | 2014-05-16 | 6 | 0.114 | 0.158 | -0.044 | -0.067 | -0.021 | no | -0.382 | 1.000 | 0.086 | yes |

Qualifying ports: 6; passing: 5; one-sided Wilcoxon p = 0.0312.

**Headline status: SUPPORTED**

Power note: with n = 6 the smallest attainable one-sided Wilcoxon signed-rank p is 1/64 = 0.0156; with n = 5 it is 1/32 = 0.0312. Here n = 6 (minimum attainable p = 0.0156).

### 1a. Leave-one-port-out

| dropped | n_qualifying | n_pass | wilcoxon_p | status |
|---|---|---|---|---|
| prboom-plus | 5 | 4 | 0.062 | wrong comparator not supported |
| woof | 5 | 4 | 0.062 | wrong comparator not supported |
| eternity | 5 | 4 | 0.062 | wrong comparator not supported |
| edge-classic | 5 | 4 | 0.062 | wrong comparator not supported |
| inter-doom | 5 | 4 | 0.062 | wrong comparator not supported |
| doomretro | 5 | 5 | 0.031 | SUPPORTED |

### 1b. A at second usable snapshot

| port | date | A | lo | hi | passed |
|---|---|---|---|---|---|
| prboom-plus | 2001-07-22 | 0.275 | 0.239 | 0.310 | yes |
| woof | 2008-06-18 | 0.552 | 0.518 | 0.586 | yes |
| eternity | 2006-09-30 | 0.259 | 0.234 | 0.283 | yes |
| edge-classic | 2022-02-06 | 0.361 | 0.350 | 0.372 | yes |
| inter-doom | 2023-08-12 | -0.124 | -0.189 | -0.056 | no |
| doomretro | 2014-10-09 | 0.081 | 0.067 | 0.094 | yes |

### 1c. A as median of first three usable snapshots

| port | A | passed |
|---|---|---|
| prboom-plus | 0.309 | yes |
| woof | 0.594 | yes |
| eternity | 0.259 | yes |
| edge-classic | 0.360 | yes |
| inter-doom | -0.124 | no |
| doomretro | 0.071 | yes |

### 1d. Common-denominator A

| port | date | A | passed |
|---|---|---|---|
| prboom-plus | 2000-11-29 | 0.426 | yes |
| woof | 2008-06-17 | 0.685 | yes |
| eternity | 2006-02-07 | 0.470 | yes |
| edge-classic | 2021-12-12 | 0.692 | yes |
| inter-doom | 2023-07-06 | 0.240 | yes |
| doomretro | 2014-05-16 | 0.029 | no |

### 1e. Snapshots excluded by lang_c < 0.90 (structural test; names shown beside)

| port | sha | date | lang_c | A_struct_not_tested | A_names |
|---|---|---|---|---|---|
| eternity | 2326701a20cab6d05cfdaf4d4d3c307d0dc65f8f | 2011-04-08 | 0.087 | 0.031 | -0.132 |
| eternity | 95f46b3425938c12eec6493e5b46e594c68b29ee | 2016-03-12 | 0.045 | 0.003 | -0.173 |
| eternity | 339dfa50df9189d203dba9c703b20546b4008002 | 2026-10-04 | 0.051 | 0.003 | -0.177 |

## 2. Carry-over gate

| port | sha | S_novel | lo | hi | S_wrong_novel | floor_ok | ci_ok | above_wrong | passed | n_novel_note |
|---|---|---|---|---|---|---|---|---|---|---|
| prboom-plus | 5c2f54d04ae82f4b2d5013a0ac09b3ba69a62498 | 0.679 | 0.625 | 0.733 | 0.030 | yes | yes | yes | yes |  |
| woof | 9ab0817c7caf13a77e11c00720983eab57f3666f | 0.572 | 0.520 | 0.622 | 0.009 | yes | yes | yes | yes |  |
| eternity | a22e63c62afdcb8aba4bab709f8cd826b263586f | 0.227 | 0.204 | 0.250 | 0.040 | yes | yes | yes | yes |  |
| edge-classic | a255d0f3752b19d9237aa49629ec1be25ac93747 | 0.353 | 0.342 | 0.364 | 0.002 | yes | yes | yes | yes |  |
| inter-doom | b845695b07094cb35688450de27aa56e99f48467 | 0.651 | 0.629 | 0.672 | 0.003 | yes | yes | yes | yes |  |
| doomretro | 4010f4ffaa4a91cb55f62c6308f6eafdbea9ae86 | 0.071 | 0.057 | 0.085 | 0.027 | yes | yes | yes | yes |  |

Share of ports passing: 1.000 (6 of 6).

## 3. H8b.2 decay vs age (descriptive)

| port | subset | measure | n | tau | p | partial | partial_p | fragile |
|---|---|---|---|---|---|---|---|---|
| prboom-plus | all | structure | 6 | -1.000 | 0.003 | -1.000 | 0.000 | no |
| prboom-plus | all | names | 6 | -0.828 | 0.022 | -0.866 | 0.058 | yes |
| prboom-plus | novel | structure | 6 | -0.966 | 0.007 | -0.978 | 0.004 | no |
| prboom-plus | novel | names | 6 | -0.931 | 0.011 | -0.954 | 0.012 | no |
| woof | all | structure | 6 | -0.966 | 0.007 | -0.876 | 0.052 | yes |
| woof | all | names | 6 | -0.775 | 0.042 | -0.000 | 1.000 | yes |
| woof | novel | structure | 6 | -0.894 | 0.016 | -0.799 | 0.105 | yes |
| woof | novel | names | 6 | -0.577 | 0.143 | 0.000 | 1.000 | no |
| eternity | all | structure | 4 | -1.000 | 0.083 | 0.000 | 1.000 | no |
| eternity | all | names | 4 | -0.913 | 0.071 | 0.000 | 1.000 | no |
| eternity | novel | structure | 4 | -1.000 | 0.083 | 0.000 | 1.000 | no |
| eternity | novel | names | 4 | -0.667 | 0.333 | 0.000 | 1.000 | no |
| edge-classic | all | structure | 6 | -0.867 | 0.017 | -0.984 | 0.002 | no |
| edge-classic | all | names | 6 | -1.000 | 0.003 | -1.000 | 0.000 | no |
| edge-classic | novel | structure | 6 | -0.867 | 0.017 | -0.984 | 0.002 | no |
| edge-classic | novel | names | 6 | -1.000 | 0.003 | -1.000 | 0.000 | no |
| inter-doom | all | structure | 7 | -0.488 | 0.129 | -0.889 | 0.018 | yes |
| inter-doom | all | names | 7 | -0.488 | 0.129 | -0.889 | 0.018 | yes |
| inter-doom | novel | structure | 7 | -0.390 | 0.224 | -0.467 | 0.351 | no |
| inter-doom | novel | names | 7 | -0.195 | 0.543 | -0.428 | 0.398 | no |
| doomretro | all | structure | 6 | -1.000 | 0.003 | 0.000 | 1.000 | yes |
| doomretro | all | names | 6 | -0.867 | 0.017 | 0.000 | 1.000 | yes |
| doomretro | novel | structure | 6 | -0.867 | 0.017 | 0.000 | 1.000 | yes |
| doomretro | novel | names | 6 | -0.600 | 0.136 | 0.000 | 1.000 | no |

Names minus structure (tau and partial):

| port | subset | tau_names_minus_struct | partial_names_minus_struct |
|---|---|---|---|
| prboom-plus | all | 0.172 | 0.134 |
| prboom-plus | novel | 0.035 | 0.024 |
| woof | all | 0.191 | 0.876 |
| woof | novel | 0.317 | 0.799 |
| eternity | all | 0.087 | 0.000 |
| eternity | novel | 0.333 | 0.000 |
| edge-classic | all | -0.133 | -0.016 |
| edge-classic | novel | -0.133 | -0.016 |
| inter-doom | all | 0.000 | 0.000 |
| inter-doom | novel | 0.195 | 0.039 |
| doomretro | all | 0.133 | 0.000 |
| doomretro | novel | 0.267 | 0.000 |

## 4. H8b.3 ranking

| port | ref_name | K | one_over_K | rank_struct | rank_names | registered_shared_struct | registered_shared_names | top1_struct | top1_struct_value | top1_names | top1_names_value | linuxdoom_shared_struct | linuxdoom_shared_names | ties_struct | ties_names | registered_is_repr | baseline_rank1 | baseline_top3 | in_top3_struct | in_top3_names | read_as_supporting |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| prboom-plus | boom-2.02 | 3 | 0.333 | 2 | 1 | 0.389 | 0.938 | mbf | 0.447 | boom | 0.938 | 0.062 | 0.793 | 0 | 0 | 1 | 0.333 | 1.000 | yes | yes | yes |
| woof | mbf-2.03 | 13 | 0.077 | 1 | 1 | 0.856 | 0.950 | mbf | 0.856 | mbf | 0.950 | 0.146 | 0.764 | 0 | 0 | 1 | 0.077 | 0.231 | yes | yes | yes |
| eternity | smmu | 9 | 0.111 | 2 | 7 | 0.250 | 0.549 | mbf | 0.338 | mbf | 0.762 | 0.010 | 0.682 | 0 | 0 | 1 | 0.111 | 0.333 | yes | no | yes |
| edge-classic | edge@2021-09-17 | 26 | 0.038 | 1 | 1 | 0.697 | 0.816 | edge | 0.697 | edge | 0.816 | 0.000 | 0.169 | 0 | 0 | 1 | 0.038 | 0.115 | yes | yes | yes |
| inter-doom | crispy-doom@2023-06-26 | 27 | 0.037 | 1 | 1 | 0.706 | 0.879 | crispy-doom | 0.706 | crispy-doom | 0.879 | 0.252 | 0.706 | 0 | 0 | 1 | 0.037 | 0.111 | yes | yes | yes |
| doomretro | chocolate-doom@2013-12-10 | 16 | 0.062 | 1 | 1 | 0.173 | 0.746 | chocolate-doom | 0.173 | crispy-doom | 0.746 | 0.130 | 0.703 | 0 | 1 | 1 | 0.062 | 0.188 | yes | yes | yes |

Gate: the registered progenitor is in the top 3 (structure) for every ported ranked; H8b.1 may be read as supporting the map.

## 5. Controls

### 5a. Differential specificity (S_R_right > S_R_wrong, total)

| port | S_right | S_wrong | passed |
|---|---|---|---|
| prboom-plus | 0.679 | 0.108 | yes |
| woof | 0.779 | 0.066 | yes |
| eternity | 0.305 | 0.068 | yes |
| edge-classic | 0.360 | 0.001 | yes |
| inter-doom | 0.634 | 0.027 | yes |
| doomretro | 0.114 | 0.137 | no |

### 5b. Wrong-progenitor novel subset below 0.02

| port | S_wrong_novel | passed |
|---|---|---|
| prboom-plus | 0.030 | no |
| woof | 0.009 | yes |
| eternity | 0.040 | no |
| edge-classic | 0.002 | yes |
| inter-doom | 0.003 | yes |
| doomretro | 0.027 | no |

### 5c. New progenitors vs unrelated controls below 0.02

| ref_name | n_controls | max_S | passed |
|---|---|---|---|
| boom-2.02 | 33 | 0.006 | yes |
| chocolate-doom@2013-12-10 | 33 | 0.006 | yes |
| crispy-doom@2023-06-26 | 33 | 0.005 | yes |
| edge@2021-09-17 | 33 | 0.001 | yes |
| mbf-2.03 | 33 | 0.004 | yes |
| smmu | 33 | 0.005 | yes |

## 6. Class A calibration stratum (descriptive only)

| child | n_steps | surv_struct_fork_persnap | surv_names_fork | shared_struct_persnap | shared_names |
|---|---|---|---|---|---|
| crispy-doom | 26 | 0.600 | 0.881 | 0.569 | 0.866 |
| dsda-doom | 6 | 0.598 | 0.784 | 0.562 | 0.766 |
| kocoa-doom | 6 | 0.668 | 0.675 | 0.652 | 0.659 |
| nugget-doom | 11 | 0.506 | 0.793 | 0.458 | 0.771 |

| child | parent | step | kind | date | child_sha | parent_fork_sha | same_language | n_ref_eligible | eligible_snapshot | surv_struct_fork_persnap | surv_names_fork | shared_struct_persnap | shared_names | dup_share | lang_c | lang_cpp | lang_other | age_years | contemp_target_date | contemp_child_sha | contemp_parent_sha | contemp_identical_sha | contemp_elig_child | contemp_elig_parent | contemp_surv_struct_c2p | contemp_surv_struct_p2c | contemp_shared_struct_max | contemp_shared_struct_min | contemp_surv_names_c2p | contemp_surv_names_p2c | contemp_shared_names_max | contemp_shared_names_min | contemp_names_pool_status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| crispy-doom | chocolate-doom | 1 | grid | 2014-06-08 | 1ca201965ff190aaf358249a0d299ed245169ee9 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2003 | 0.812 | 0.934 | 0.792 | 0.922 | 0.085 | 0.962 | 0.000 | 0.037 | 0.496 | 2014-06-09 | 1ca201965ff190aaf358249a0d299ed245169ee9 | b83132a4962787aabf2e07ae90d37d6d87b001b3 | 0.000 | 2003.000 | 1982.000 | 0.872 | 0.883 | 0.869 | 0.857 | 0.928 | 0.937 | 0.926 | 0.915 | ok |
| crispy-doom | chocolate-doom | 2 | grid | 2014-12-08 | 3ef48415d193caba6400151f47cb2d992cd210bb | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2050 | 0.785 | 0.931 | 0.761 | 0.919 | 0.090 | 0.963 | 0.000 | 0.037 | 0.997 | 2014-12-09 | 3ef48415d193caba6400151f47cb2d992cd210bb | f6e092005e6fd291fef0b9d7cf37ce6c4a5e1da2 | 0.000 | 2050.000 | 1972.000 | 0.824 | 0.854 | 0.838 | 0.807 | 0.901 | 0.937 | 0.925 | 0.887 | ok |
| crispy-doom | chocolate-doom | 3 | grid | 2015-06-09 | 404e098c8475ce0ee28917b4a79d64d2707968f9 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2078 | 0.760 | 0.928 | 0.728 | 0.916 | 0.088 | 0.963 | 0.000 | 0.036 | 1.498 | 2015-06-10 | 404e098c8475ce0ee28917b4a79d64d2707968f9 | 970a54d1cf2a980fd3bb5412d2e0cfc9ae8898ec | 0.000 | 2078.000 | 1969.000 | 0.799 | 0.845 | 0.828 | 0.782 | 0.888 | 0.938 | 0.926 | 0.874 | ok |
| crispy-doom | chocolate-doom | 4 | grid | 2015-11-30 | e8a640cde3defd80872d2f3f63537b30af505ec0 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2098 | 0.737 | 0.926 | 0.709 | 0.913 | 0.087 | 0.963 | 0.000 | 0.037 | 1.974 | 2015-12-09 | e8a640cde3defd80872d2f3f63537b30af505ec0 | 123eeafba7561bf44e8b66927386a6a5dd11b549 | 0.000 | 2098.000 | 1981.000 | 0.790 | 0.833 | 0.816 | 0.772 | 0.883 | 0.935 | 0.924 | 0.869 | ok |
| crispy-doom | chocolate-doom | 5 | grid | 2016-06-08 | 5d9737c3e2c56a27f9bf1847f986d12123acf91f | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2105 | 0.705 | 0.912 | 0.677 | 0.899 | 0.089 | 0.963 | 0.000 | 0.037 | 2.497 | 2016-06-09 | 5d9737c3e2c56a27f9bf1847f986d12123acf91f | ad113dcdd09405e81214e0f477dc44d49f6bcac8 | 0.000 | 2105.000 | 1971.000 | 0.754 | 0.804 | 0.786 | 0.735 | 0.869 | 0.928 | 0.916 | 0.854 | ok |
| crispy-doom | chocolate-doom | 6 | grid | 2016-11-29 | 16f5cca5c4806a7d29ae79bc6a361ba119f8587a | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2133 | 0.695 | 0.911 | 0.669 | 0.898 | 0.091 | 0.963 | 0.000 | 0.036 | 2.973 | 2016-12-08 | 16f5cca5c4806a7d29ae79bc6a361ba119f8587a | 805c6718912fb2532341f36d8f0b4b5092a35d00 | 0.000 | 2133.000 | 1976.000 | 0.740 | 0.799 | 0.781 | 0.721 | 0.861 | 0.929 | 0.917 | 0.845 | ok |
| crispy-doom | chocolate-doom | 7 | grid | 2017-06-08 | 0e4d2decf983a8b2b5d41fe237b50b99aa028b16 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2160 | 0.690 | 0.910 | 0.657 | 0.897 | 0.090 | 0.964 | 0.000 | 0.036 | 3.496 | 2017-06-09 | 0e4d2decf983a8b2b5d41fe237b50b99aa028b16 | 1843d641566a080f2751348e0ca9a54694e1f348 | 0.000 | 2160.000 | 1991.000 | 0.714 | 0.776 | 0.758 | 0.694 | 0.848 | 0.920 | 0.907 | 0.832 | ok |
| crispy-doom | chocolate-doom | 8 | grid | 2017-12-05 | a8fd660d4046efe5d57db64ac0815799ac28c393 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2182 | 0.624 | 0.871 | 0.593 | 0.855 | 0.090 | 0.962 | 0.000 | 0.037 | 3.989 | 2017-12-09 | a8fd660d4046efe5d57db64ac0815799ac28c393 | 95bd2d4483435285113a55281a8d713688ef2a1b | 0.000 | 2182.000 | 2035.000 | 0.764 | 0.819 | 0.802 | 0.745 | 0.882 | 0.946 | 0.935 | 0.868 | ok |
| crispy-doom | chocolate-doom | 9 | grid | 2018-06-04 | f429375c3dea29a9278e73830ca1871c17ae192b | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2192 | 0.592 | 0.868 | 0.558 | 0.853 | 0.085 | 0.963 | 0.000 | 0.037 | 4.485 | 2018-06-09 | f429375c3dea29a9278e73830ca1871c17ae192b | 622340e47976299e6107997d92197b351258d8c5 | 0.000 | 2192.000 | 2021.000 | 0.755 | 0.817 | 0.799 | 0.736 | 0.872 | 0.946 | 0.935 | 0.857 | ok |
| crispy-doom | chocolate-doom | 10 | grid | 2018-12-09 | 82189afa55770b1202394420cd12a969041a3b40 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2240 | 0.568 | 0.868 | 0.539 | 0.852 | 0.088 | 0.962 | 0.000 | 0.038 | 4.999 | 2018-12-09 | 82189afa55770b1202394420cd12a969041a3b40 | 1b98fb58714e590638c35fc7df9e1e587b4ed3d3 | 0.000 | 2240.000 | 2053.000 | 0.747 | 0.816 | 0.799 | 0.728 | 0.867 | 0.946 | 0.936 | 0.853 | ok |
| crispy-doom | chocolate-doom | 11 | grid | 2019-06-08 | 6a23c24d7e3501861c20959af5921206e04c2245 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2270 | 0.550 | 0.867 | 0.522 | 0.851 | 0.087 | 0.962 | 0.000 | 0.038 | 5.495 | 2019-06-10 | 6a23c24d7e3501861c20959af5921206e04c2245 | 1857858144fc14ed5b370bb9a86653606c647ae6 | 0.000 | 2270.000 | 2076.000 | 0.737 | 0.804 | 0.786 | 0.719 | 0.863 | 0.944 | 0.933 | 0.849 | ok |
| crispy-doom | chocolate-doom | 12 | grid | 2019-12-09 | 79c9d66be08124e80be76c3a639b270bf384ad8a | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2287 | 0.553 | 0.867 | 0.526 | 0.851 | 0.087 | 0.962 | 0.000 | 0.038 | 5.999 | 2019-12-09 | 79c9d66be08124e80be76c3a639b270bf384ad8a | a713167fcf34253837deacda5de2b3de4b30ca1b | 0.000 | 2287.000 | 2080.000 | 0.739 | 0.812 | 0.795 | 0.721 | 0.861 | 0.947 | 0.937 | 0.847 | ok |
| crispy-doom | chocolate-doom | 13 | grid | 2020-05-26 | 1434047b18c4b0ac8673c858ee1748a5d298088f | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2296 | 0.546 | 0.867 | 0.511 | 0.851 | 0.086 | 0.962 | 0.000 | 0.038 | 6.461 | 2020-06-09 | 1434047b18c4b0ac8673c858ee1748a5d298088f | 5bf73c4864fedb6b97b27bf302435a1168ba8f4c | 0.000 | 2296.000 | 2080.000 | 0.734 | 0.807 | 0.790 | 0.716 | 0.858 | 0.947 | 0.936 | 0.843 | ok |
| crispy-doom | chocolate-doom | 14 | grid | 2020-12-07 | d864adb3b99d6db70cac8b5d7358206da08fae11 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2300 | 0.555 | 0.867 | 0.527 | 0.851 | 0.085 | 0.962 | 0.000 | 0.038 | 6.995 | 2020-12-08 | d864adb3b99d6db70cac8b5d7358206da08fae11 | 0b76cbbe94a8a4b7562e3f95dfc00c1110b707a4 | 0.000 | 2300.000 | 2081.000 | 0.733 | 0.807 | 0.789 | 0.714 | 0.857 | 0.947 | 0.936 | 0.842 | ok |
| crispy-doom | chocolate-doom | 15 | grid | 2021-05-29 | 3ee72e2dd807cfd97880c3bfeeaa42af403db246 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2304 | 0.550 | 0.867 | 0.514 | 0.851 | 0.084 | 0.962 | 0.000 | 0.038 | 7.469 | 2021-06-09 | 3ee72e2dd807cfd97880c3bfeeaa42af403db246 | c3e9173772e07ee21f3cea39fd6e3935ed95a02c | 0.000 | 2304.000 | 2082.000 | 0.734 | 0.809 | 0.791 | 0.715 | 0.855 | 0.947 | 0.936 | 0.841 | ok |
| crispy-doom | chocolate-doom | 16 | grid | 2021-11-29 | 66ecb5efb79dde48dda78a47546a4b084e7a6aa0 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2285 | 0.550 | 0.867 | 0.522 | 0.851 | 0.081 | 0.962 | 0.000 | 0.038 | 7.973 | 2021-12-09 | 66ecb5efb79dde48dda78a47546a4b084e7a6aa0 | f8ee575d83b1824ef752a1f4ade4171e43af68ea | 0.000 | 2285.000 | 2058.000 | 0.726 | 0.805 | 0.787 | 0.707 | 0.854 | 0.948 | 0.938 | 0.839 | ok |
| crispy-doom | chocolate-doom | 17 | grid | 2022-06-08 | 5d26df80c8fd204d39fd1b407f25c6ed35382fd3 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2304 | 0.538 | 0.866 | 0.511 | 0.850 | 0.082 | 0.962 | 0.000 | 0.038 | 8.496 | 2022-06-09 | 5d26df80c8fd204d39fd1b407f25c6ed35382fd3 | 6e2d5f924cb23eb3ad2984ce85bdbae702117d0d | 0.000 | 2304.000 | 2066.000 | 0.724 | 0.806 | 0.789 | 0.705 | 0.850 | 0.948 | 0.937 | 0.835 | ok |
| crispy-doom | chocolate-doom | 18 | grid | 2022-11-23 | 6a6d6c88086a03d71527707fcdfd447a008d297b | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2314 | 0.545 | 0.866 | 0.508 | 0.850 | 0.085 | 0.962 | 0.000 | 0.038 | 8.956 | 2022-12-09 | 6a6d6c88086a03d71527707fcdfd447a008d297b | 88f5ae5be28d3c472c6d4e060304b877d52ec139 | 0.000 | 2314.000 | 2070.000 | 0.720 | 0.802 | 0.785 | 0.702 | 0.848 | 0.948 | 0.937 | 0.833 | ok |
| crispy-doom | chocolate-doom | 19 | grid | 2023-06-07 | 0fd23c29a98413d5e47e9f3f8b1f97187be35b14 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2368 | 0.538 | 0.866 | 0.507 | 0.850 | 0.089 | 0.962 | 0.000 | 0.038 | 9.492 | 2023-06-10 | 0fd23c29a98413d5e47e9f3f8b1f97187be35b14 | e96d2c2c1bf33b3367cf40d234563d7c5465b614 | 0.000 | 2368.000 | 2113.000 | 0.714 | 0.797 | 0.779 | 0.695 | 0.846 | 0.948 | 0.938 | 0.831 | ok |
| crispy-doom | chocolate-doom | 20 | grid | 2023-12-03 | e41ec278a48631b617a11c721a94fea5cd612ec0 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2405 | 0.533 | 0.866 | 0.502 | 0.850 | 0.091 | 0.962 | 0.000 | 0.038 | 9.982 | 2023-12-09 | e41ec278a48631b617a11c721a94fea5cd612ec0 | e9c202bd4df494634509e6023ad426b93df3871b | 0.000 | 2405.000 | 2146.000 | 0.709 | 0.793 | 0.775 | 0.691 | 0.847 | 0.949 | 0.939 | 0.832 | ok |
| crispy-doom | chocolate-doom | 21 | grid | 2024-04-24 | 3a7e9fcfbf82763f7f2aa9550c6fd2e97251eedf | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2412 | 0.531 | 0.866 | 0.496 | 0.850 | 0.091 | 0.962 | 0.000 | 0.038 | 10.374 | 2024-06-09 | 3a7e9fcfbf82763f7f2aa9550c6fd2e97251eedf | 2ea764fed6a266e291cf37375f52bc92260f686c | 0.000 | 2412.000 | 2149.000 | 0.709 | 0.790 | 0.772 | 0.690 | 0.845 | 0.949 | 0.939 | 0.830 | ok |
| crispy-doom | chocolate-doom | 22 | grid | 2024-11-23 | bd87fce1d57c99ee5cae73a2636cf781d36e39ba | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2424 | 0.540 | 0.865 | 0.509 | 0.849 | 0.091 | 0.962 | 0.000 | 0.038 | 10.957 | 2024-12-08 | bd87fce1d57c99ee5cae73a2636cf781d36e39ba | bb9bb2324852db731d81ee8c1f16a9b0b0fc31df | 0.000 | 2424.000 | 2150.000 | 0.704 | 0.791 | 0.773 | 0.686 | 0.841 | 0.948 | 0.938 | 0.826 | ok |
| crispy-doom | chocolate-doom | 23 | grid | 2025-06-04 | afb11aeda721e4c158c6eae632d9058071487b91 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2427 | 0.519 | 0.865 | 0.485 | 0.849 | 0.091 | 0.962 | 0.000 | 0.038 | 11.485 | 2025-06-09 | afb11aeda721e4c158c6eae632d9058071487b91 | 0b3cb528c3f53c61d7a4ebe13a7d522570b98d83 | 0.000 | 2427.000 | 2150.000 | 0.705 | 0.795 | 0.778 | 0.687 | 0.839 | 0.947 | 0.937 | 0.824 | ok |
| crispy-doom | chocolate-doom | 24 | grid | 2025-12-02 | bf19c669553ad5142fed4181a6ee3bdc4a1d2a06 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2428 | 0.536 | 0.865 | 0.506 | 0.849 | 0.091 | 0.962 | 0.000 | 0.038 | 11.981 | 2025-12-09 | bf19c669553ad5142fed4181a6ee3bdc4a1d2a06 | 47ec8a606c7e903b8e79204e85d6cabf394eefec | 0.000 | 2428.000 | 2150.000 | 0.702 | 0.792 | 0.774 | 0.683 | 0.839 | 0.947 | 0.937 | 0.824 | ok |
| crispy-doom | chocolate-doom | 25 | grid | 2026-06-08 | 643fff4297ac7880c5cb261561caeedf6cbe2a46 | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2436 | 0.520 | 0.865 | 0.488 | 0.849 | 0.092 | 0.962 | 0.000 | 0.038 | 12.496 | 2026-06-09 | 643fff4297ac7880c5cb261561caeedf6cbe2a46 | 353cf5001dfd5777c13327010fa58acb57b913b2 | 0.000 | 2436.000 | 2151.000 | 0.698 | 0.791 | 0.774 | 0.679 | 0.837 | 0.947 | 0.937 | 0.821 | ok |
| crispy-doom | chocolate-doom | head | head | 2026-09-09 | 39f4d9362acf2e7f8164edbd4f6d5176399ebffb | e2f1ba09c6a801242d6641dd08784d721a749589 | yes | 1908 | 2444 | 0.524 | 0.865 | 0.490 | 0.849 | 0.092 | 0.962 | 0.000 | 0.038 | 12.750 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| dsda-doom | prboom-plus | 1 | grid | 2021-05-10 | 4a2aed3f684db17585e256e6cd16328bd8bc6768 | 676d818c5bbc1d45f0a191def0d7629ed73a84cb | yes | 1947 | 2286 | 0.836 | 0.926 | 0.814 | 0.913 | 0.064 | 0.957 | 0.014 | 0.029 | 0.498 | 2021-05-11 | 4a2aed3f684db17585e256e6cd16328bd8bc6768 | 635be4806561ff3fcf46ad948e60e813dda8905c | 0.000 | 2286.000 | 2016.000 | 0.717 | 0.814 | 0.796 | 0.699 | 0.792 | 0.898 | 0.884 | 0.775 | ok |
| dsda-doom | prboom-plus | 2 | grid | 2021-11-08 | f0e9b6714c2f7970889fa157a57d67b2baeeda7e | 676d818c5bbc1d45f0a191def0d7629ed73a84cb | yes | 1947 | 2729 | 0.768 | 0.890 | 0.742 | 0.875 | 0.080 | 0.965 | 0.012 | 0.023 | 0.997 | 2021-11-09 | f0e9b6714c2f7970889fa157a57d67b2baeeda7e | e08f129f557cae6e529d8f9ff151750a2345a16a | 0.000 | 2729.000 | 2030.000 | 0.560 | 0.748 | 0.729 | 0.541 | 0.646 | 0.869 | 0.854 | 0.628 | ok |
| dsda-doom | prboom-plus | 3 | grid | 2022-05-10 | 706c39150664ebbb112a6a55fd4f6d0cdd54e038 | 676d818c5bbc1d45f0a191def0d7629ed73a84cb | yes | 1947 | 2822 | 0.688 | 0.821 | 0.639 | 0.804 | 0.096 | 0.986 | 0.011 | 0.002 | 1.498 | 2022-05-11 | 706c39150664ebbb112a6a55fd4f6d0cdd54e038 | b21bdbc198f382bb5a938b287eab696a5328567a | 0.000 | 2822.000 | 2037.000 | 0.477 | 0.653 | 0.632 | 0.459 | 0.578 | 0.800 | 0.782 | 0.559 | ok |
| dsda-doom | prboom-plus | 4 | grid | 2022-11-09 | 7bfb8fc3dae7e29d928944aec6b9763d63fc5a0e | 676d818c5bbc1d45f0a191def0d7629ed73a84cb | yes | 1947 | 2896 | 0.509 | 0.740 | 0.471 | 0.720 | 0.107 | 0.987 | 0.011 | 0.002 | 1.999 | 2022-11-09 | 7bfb8fc3dae7e29d928944aec6b9763d63fc5a0e | 495fd599b11283617bbc6ef966e7dbd709fc61c5 | 0.000 | 2896.000 | 2039.000 | 0.353 | 0.496 | 0.474 | 0.336 | 0.509 | 0.723 | 0.703 | 0.491 | ok |
| dsda-doom | prboom-plus | 5 | grid | 2023-05-09 | 4c0035d4a5a4a28f0a7a7bac7dd53906e05d07f4 | 676d818c5bbc1d45f0a191def0d7629ed73a84cb | yes | 1947 | 3129 | 0.442 | 0.680 | 0.390 | 0.659 | 0.133 | 0.985 | 0.013 | 0.002 | 2.494 | 2023-05-11 | 4c0035d4a5a4a28f0a7a7bac7dd53906e05d07f4 | 8be14f401de006bdeb1a1f8f6b50171c04bb4889 | 0.000 | 3129.000 | 2044.000 | 0.272 | 0.404 | 0.383 | 0.257 | 0.437 | 0.668 | 0.648 | 0.419 | ok |
| dsda-doom | prboom-plus | head | head | 2026-10-03 | 432d808d9e8492101df8ee1449cba759f8a62ea5 | 676d818c5bbc1d45f0a191def0d7629ed73a84cb | yes | 1947 | 3470 | 0.347 | 0.647 | 0.313 | 0.626 | 0.135 | 0.968 | 0.029 | 0.003 | 5.897 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| nugget-doom | woof | 1 | grid | 2022-02-26 | b1d62a78ac1ca20733a1130787489b9c3f789f52 | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 1748 | 0.772 | 0.912 | 0.742 | 0.896 | 0.089 | 0.993 | 0.000 | 0.007 | 0.490 | 2022-03-02 | b1d62a78ac1ca20733a1130787489b9c3f789f52 | 8acd6de68df6ff1a636c736bdc186ca75b79813e | 0.000 | 1748.000 | 1728.000 | 0.876 | 0.888 | 0.873 | 0.860 | 0.961 | 0.972 | 0.963 | 0.950 | ok |
| nugget-doom | woof | 2 | grid | 2022-08-15 | de1588b894601f2c0fa54259a4c89cc9e78a7f7d | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 1981 | 0.675 | 0.895 | 0.641 | 0.877 | 0.086 | 0.975 | 0.000 | 0.025 | 0.956 | 2022-08-31 | de1588b894601f2c0fa54259a4c89cc9e78a7f7d | d51fdc9fb2b01c65730b42940390e67bb163784c | 0.000 | 1981.000 | 1961.000 | 0.876 | 0.886 | 0.871 | 0.861 | 0.955 | 0.965 | 0.956 | 0.945 | ok |
| nugget-doom | woof | 3 | grid | 2023-03-01 | 7e2de76303138d571204e18f31c916e2c73a72ae | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 2049 | 0.651 | 0.892 | 0.613 | 0.874 | 0.088 | 0.976 | 0.000 | 0.024 | 1.498 | 2023-03-02 | 7e2de76303138d571204e18f31c916e2c73a72ae | 5401a036227437ce8877f070ca78b671905b54bf | 0.000 | 2049.000 | 2052.000 | 0.848 | 0.847 | 0.832 | 0.831 | 0.941 | 0.940 | 0.930 | 0.929 | ok |
| nugget-doom | woof | 4 | grid | 2023-08-31 | afc7d20011abaf77e220cc3970fa67bac09f25eb | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 2156 | 0.577 | 0.869 | 0.538 | 0.850 | 0.091 | 0.974 | 0.000 | 0.026 | 1.999 | 2023-09-01 | afc7d20011abaf77e220cc3970fa67bac09f25eb | 445ab3e20879179c4e78980ceda60fdacd42edb1 | 0.000 | 2156.000 | 2165.000 | 0.825 | 0.823 | 0.809 | 0.806 | 0.932 | 0.928 | 0.920 | 0.916 | ok |
| nugget-doom | woof | 5 | grid | 2024-03-01 | 175d2421640797469a3fe3ffe9d5c6f99cada36a | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 2396 | 0.512 | 0.835 | 0.464 | 0.814 | 0.096 | 0.972 | 0.001 | 0.027 | 2.500 | 2024-03-01 | 175d2421640797469a3fe3ffe9d5c6f99cada36a | 9aa4ddd7f89d550de874f3fdd9c2347d803f3fac | 0.000 | 2396.000 | 2330.000 | 0.828 | 0.849 | 0.834 | 0.812 | 0.925 | 0.951 | 0.942 | 0.914 | ok |
| nugget-doom | woof | 6 | grid | 2024-08-29 | a4cc694f360a0d4fc0cd20c601bf866ab5241b79 | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 2461 | 0.476 | 0.783 | 0.418 | 0.760 | 0.091 | 0.973 | 0.001 | 0.026 | 2.995 | 2024-08-31 | a4cc694f360a0d4fc0cd20c601bf866ab5241b79 | cbf2e289b8fbcb887a5479b8740ec557d3b5a167 | 0.000 | 2461.000 | 2523.000 | 0.766 | 0.753 | 0.749 | 0.736 | 0.888 | 0.866 | 0.875 | 0.853 | ok |
| nugget-doom | woof | 7 | grid | 2025-02-28 | 5a25069dff904df436009055ac87c15d86c9be54 | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 2834 | 0.406 | 0.723 | 0.361 | 0.699 | 0.093 | 0.975 | 0.001 | 0.024 | 3.496 | 2025-03-01 | 5a25069dff904df436009055ac87c15d86c9be54 | 0df430ad7807aaf634735101b8b3cce24a6449a5 | 0.000 | 2834.000 | 2709.000 | 0.796 | 0.837 | 0.822 | 0.781 | 0.902 | 0.944 | 0.935 | 0.891 | ok |
| nugget-doom | woof | 8 | grid | 2025-08-19 | 950c5cbc42050d142cd12f4ea3319ab6ba6e1ac8 | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 2856 | 0.393 | 0.723 | 0.346 | 0.699 | 0.096 | 0.975 | 0.001 | 0.024 | 3.967 | 2025-08-31 | 950c5cbc42050d142cd12f4ea3319ab6ba6e1ac8 | 0676f2ca942c14fe07de542fc84ac8d1fb21dbc1 | 0.000 | 2856.000 | 2840.000 | 0.718 | 0.733 | 0.717 | 0.702 | 0.876 | 0.881 | 0.868 | 0.863 | ok |
| nugget-doom | woof | 9 | grid | 2026-03-01 | 4c8f23d62655dda2f7aa95a23bc665b6727ff334 | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 2897 | 0.419 | 0.720 | 0.329 | 0.696 | 0.094 | 0.976 | 0.001 | 0.023 | 4.498 | 2026-03-02 | 4c8f23d62655dda2f7aa95a23bc665b6727ff334 | fe1d6fceebedc14fea22a8c929723b57c31cf109 | 0.000 | 2897.000 | 3089.000 | 0.660 | 0.621 | 0.643 | 0.603 | 0.833 | 0.781 | 0.819 | 0.766 | ok |
| nugget-doom | woof | 10 | grid | 2026-08-21 | 5ca2e6b954a37b936440770789e3fd7678a295e2 | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 2996 | 0.385 | 0.719 | 0.337 | 0.694 | 0.102 | 0.977 | 0.001 | 0.023 | 4.972 | 2026-08-31 | 5ca2e6b954a37b936440770789e3fd7678a295e2 | 6cb2c098e7ea81f3bfe5f0c5bc259cab378f30db | 0.000 | 2996.000 | 3137.000 | 0.617 | 0.592 | 0.600 | 0.575 | 0.798 | 0.763 | 0.784 | 0.747 | ok |
| nugget-doom | woof | head | head | 2026-10-18 | 42efefeb3c2a2e79ff4aa3563e0d140a5bde63ff | 2edac4d48f734586350e8d8a97d9c746f4c7a62f | yes | 1320 | 3419 | 0.300 | 0.653 | 0.254 | 0.627 | 0.114 | 0.981 | 0.000 | 0.019 | 5.131 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |
| kocoa-doom | mochadoom | 1 | grid | 2019-07-20 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | no | 1751 | 1751 | 0.801 | 0.698 | 0.782 | 0.677 | 0.199 | 0.021 | 0.000 | 0.979 | 0.000 | 2020-01-19 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | 1.000 | 1751.000 | 1751.000 | 0.801 | 0.801 | 0.782 | 0.782 | 0.698 | 0.698 | 0.677 | 0.677 | ok |
| kocoa-doom | mochadoom | 2 | grid | 2019-07-20 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | no | 1751 | 1751 | 0.801 | 0.698 | 0.782 | 0.677 | 0.199 | 0.021 | 0.000 | 0.979 | 0.000 | 2020-07-19 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | 1.000 | 1751.000 | 1751.000 | 0.801 | 0.801 | 0.782 | 0.782 | 0.698 | 0.698 | 0.677 | 0.677 | ok |
| kocoa-doom | mochadoom | 3 | grid | 2019-07-20 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | no | 1751 | 1751 | 0.801 | 0.698 | 0.782 | 0.677 | 0.199 | 0.021 | 0.000 | 0.979 | 0.000 | 2021-01-18 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | 1.000 | 1751.000 | 1751.000 | 0.801 | 0.801 | 0.782 | 0.782 | 0.698 | 0.698 | 0.677 | 0.677 | ok |
| kocoa-doom | mochadoom | 4 | grid | 2019-07-20 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | no | 1751 | 1751 | 0.801 | 0.698 | 0.782 | 0.677 | 0.199 | 0.021 | 0.000 | 0.979 | 0.000 | 2021-07-20 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | 1.000 | 1751.000 | 1751.000 | 0.801 | 0.801 | 0.782 | 0.782 | 0.698 | 0.698 | 0.677 | 0.677 | ok |
| kocoa-doom | mochadoom | 5 | grid | 2019-07-20 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | no | 1751 | 1751 | 0.801 | 0.698 | 0.782 | 0.677 | 0.199 | 0.021 | 0.000 | 0.979 | 0.000 | 2022-01-18 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | 1.000 | 1751.000 | 1751.000 | 0.801 | 0.801 | 0.782 | 0.782 | 0.698 | 0.698 | 0.677 | 0.677 | ok |
| kocoa-doom | mochadoom | head | head | 2022-06-04 | 72d5113cd569f72bf7e8617904951175c4358f1e | a1c6b24747ed21d3912608c9f6dc712dc57ce9c9 | no | 1751 | 1646 | 0.002 | 0.559 | 0.001 | 0.570 | 0.217 | 0.000 | 0.000 | 1.000 | 2.875 | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA | NA |

## 7. Sensitivities (status flip = fragile)

| variant | n_qualifying | n_pass | wilcoxon_p | status | flips |
|---|---|---|---|---|---|
| de-duplicated (dup_share <= 0.25) | 6 | 5 | 0.031 | SUPPORTED | no |
| pooled threshold (R pooled vs linuxdoom per-snapshot unless a pooled LD column exists) | 6 | 5 | 0.031 | SUPPORTED | no |
| pure-C (lang_c >= 0.90, all ports) | 5 | 4 | 0.062 | wrong comparator not supported | yes |
| second usable snapshot | 6 | 5 | 0.047 | SUPPORTED | no |
| median of first three usable | 6 | 5 | 0.047 | SUPPORTED | no |
| common-denominator A (point rule only) | 6 | 5 | 0.016 | SUPPORTED | no |
| function-level dedup columns | 6 | 5 | 0.031 | SUPPORTED | no |

### de-duplicated (dup_share <= 0.25)

| port | date | A | lo | hi | passed | qualifies |
|---|---|---|---|---|---|---|
| prboom-plus | 2001-07-22 | 0.275 | 0.239 | 0.310 | yes | yes |
| woof | 2008-06-17 | 0.594 | 0.560 | 0.629 | yes | yes |
| eternity | 2006-02-07 | 0.280 | 0.256 | 0.305 | yes | yes |
| edge-classic | 2021-12-12 | 0.360 | 0.353 | 0.367 | yes | yes |
| inter-doom | 2023-07-06 | 0.348 | 0.309 | 0.390 | yes | yes |
| doomretro | 2014-05-16 | -0.044 | -0.067 | -0.021 | no | yes |

### pooled threshold (R pooled vs linuxdoom per-snapshot unless a pooled LD column exists)

| port | date | A | lo | hi | passed | qualifies |
|---|---|---|---|---|---|---|
| prboom-plus | 2000-11-29 | 0.451 | NA | NA | yes | yes |
| woof | 2008-06-17 | 0.557 | NA | NA | yes | yes |
| eternity | 2006-02-07 | 0.179 | NA | NA | yes | yes |
| edge-classic | 2021-12-12 | 0.359 | NA | NA | yes | yes |
| inter-doom | 2023-07-06 | 0.322 | NA | NA | yes | yes |
| doomretro | 2014-05-16 | -0.027 | NA | NA | no | yes |

### pure-C (lang_c >= 0.90, all ports)

| port | date | A | lo | hi | passed | qualifies |
|---|---|---|---|---|---|---|
| prboom-plus | 2000-11-29 | 0.465 | 0.417 | 0.516 | yes | yes |
| woof | 2008-06-17 | 0.594 | 0.560 | 0.629 | yes | yes |
| eternity | 2006-02-07 | 0.280 | 0.256 | 0.305 | yes | yes |
| edge-classic |  | NA | NA | NA | no | no |
| inter-doom | 2023-07-06 | 0.348 | 0.309 | 0.390 | yes | yes |
| doomretro | 2014-05-16 | -0.044 | -0.067 | -0.021 | no | yes |

### second usable snapshot

| port | date | A | lo | hi | passed | qualifies |
|---|---|---|---|---|---|---|
| prboom-plus | 2001-07-22 | 0.275 | 0.239 | 0.310 | yes | yes |
| woof | 2008-06-18 | 0.552 | 0.518 | 0.586 | yes | yes |
| eternity | 2006-09-30 | 0.259 | 0.234 | 0.283 | yes | yes |
| edge-classic | 2022-02-06 | 0.361 | 0.350 | 0.372 | yes | yes |
| inter-doom | 2023-08-12 | -0.124 | -0.189 | -0.056 | no | yes |
| doomretro | 2014-10-09 | 0.081 | 0.067 | 0.094 | yes | yes |

### median of first three usable

| port | date | A | lo | hi | passed | qualifies |
|---|---|---|---|---|---|---|
| prboom-plus | 2000-11-29 | 0.309 | NA | NA | yes | yes |
| woof | 2008-06-17 | 0.594 | NA | NA | yes | yes |
| eternity | 2006-02-07 | 0.259 | NA | NA | yes | yes |
| edge-classic | 2021-12-12 | 0.360 | NA | NA | yes | yes |
| inter-doom | 2023-07-06 | -0.124 | NA | NA | no | yes |
| doomretro | 2014-05-16 | 0.071 | NA | NA | yes | yes |

### common-denominator A (point rule only)

| port | date | A | lo | hi | passed | qualifies |
|---|---|---|---|---|---|---|
| prboom-plus | 2000-11-29 | 0.426 | NA | NA | yes | yes |
| woof | 2008-06-17 | 0.685 | NA | NA | yes | yes |
| eternity | 2006-02-07 | 0.470 | NA | NA | yes | yes |
| edge-classic | 2021-12-12 | 0.692 | NA | NA | yes | yes |
| inter-doom | 2023-07-06 | 0.240 | NA | NA | yes | yes |
| doomretro | 2014-05-16 | 0.029 | NA | NA | no | yes |

### function-level dedup columns

| port | date | A | lo | hi | passed | qualifies |
|---|---|---|---|---|---|---|
| prboom-plus | 2001-07-22 | 0.336 | 0.239 | 0.310 | yes | yes |
| woof | 2008-06-17 | 0.664 | 0.560 | 0.629 | yes | yes |
| eternity | 2006-02-07 | 0.349 | 0.256 | 0.305 | yes | yes |
| edge-classic | 2021-12-12 | 0.454 | 0.353 | 0.367 | yes | yes |
| inter-doom | 2023-07-06 | 0.410 | 0.309 | 0.390 | yes | yes |
| doomretro | 2014-05-16 | -0.073 | -0.067 | -0.021 | no | yes |

Function-level dedup columns were supplied by the measurement script and are used above.

## 8. Supplementary inputs

### Decomposition

| pin | eligible | unchanged_inherited | modified_inherited | novel | twin_only_unchanged | twin_only_novel | modified_by_name_only | modified_by_text_only | modified_by_both | text_channel | share_unchanged_inherited | share_modified_inherited | share_novel | share_twin_only_novel |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| boom-2.02 | 856 | 212 | 348 | 296 | 212 | 644 | 182 | 1 | 165 | 1 | 0.248 | 0.406 | 0.346 | 0.752 |
| mbf-2.03 | 935 | 147 | 407 | 381 | 147 | 788 | 249 | 0 | 158 | 1 | 0.157 | 0.435 | 0.407 | 0.843 |
| smmu | 1749 | 16 | 493 | 1240 | 16 | 1733 | 282 | 6 | 205 | 1 | 0.009 | 0.282 | 0.709 | 0.991 |
| edge@2021-09-17 | 6805 | 1 | 155 | 6649 | 1 | 6804 | 147 | 3 | 5 | 1 | 0.000 | 0.023 | 0.977 | 1.000 |
| crispy-doom@2023-06-26 | 2372 | 254 | 352 | 1766 | 254 | 2118 | 231 | 6 | 115 | 1 | 0.107 | 0.148 | 0.745 | 0.893 |
| chocolate-doom@2013-12-10 | 1908 | 405 | 193 | 1310 | 405 | 1503 | 101 | 4 | 88 | 1 | 0.212 | 0.101 | 0.687 | 0.788 |
| winmbf | 863 | 146 | 413 | 304 | 146 | 717 | 258 | 2 | 153 | 1 | 0.169 | 0.479 | 0.352 | 0.831 |
| prboom-2.5.0 | 1244 | 21 | 513 | 710 | 21 | 1223 | 322 | 4 | 187 | 1 | 0.017 | 0.412 | 0.571 | 0.983 |

### Name-blind arbiter

| kind | port | ref_name | which | tag | date | eligible_ref | exact | near | derived | gone | share_exact_near | share_exact_near_derived |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| prog_vs_linuxdoom | boom-2.02 | linuxdoom | - | 2a11d37040be__da39a3 | 2025-01-08 | 856 | 146 | 35 | 182 | 493 | 0.211 | 0.424 |
| prog_vs_linuxdoom | mbf-2.03 | linuxdoom | - | 8f705abd36ed__da39a3 | 2025-01-08 | 935 | 92 | 40 | 147 | 656 | 0.141 | 0.298 |
| prog_vs_linuxdoom | smmu | linuxdoom | - | 173934b11e86__da39a3 | 2001-02-25 | 1749 | 50 | 37 | 136 | 1526 | 0.050 | 0.128 |
| prog_vs_linuxdoom | edge@2021-09-17 | linuxdoom | - | d7adfc6a5320__da39a3 | 2021-09-17 | 6805 | 2 | 0 | 6 | 6797 | 0.000 | 0.001 |
| prog_vs_linuxdoom | crispy-doom@2023-06-26 | linuxdoom | - | 595ecb2e5ee8__b0a9d0 | 2023-06-26 | 2372 | 134 | 33 | 176 | 2029 | 0.070 | 0.145 |
| prog_vs_linuxdoom | chocolate-doom@2013-12-10 | linuxdoom | - | b9690ac0bbe2__b0a9d0 | 2013-12-10 | 1908 | 288 | 68 | 124 | 1428 | 0.187 | 0.252 |
| prog_vs_linuxdoom | winmbf | linuxdoom | - | 3af60d718b1f__da39a3 | 2016-08-20 | 863 | 87 | 43 | 142 | 591 | 0.151 | 0.315 |
| prog_vs_linuxdoom | prboom-2.5.0 | linuxdoom | - | da3313ffaeb9__da39a3 | 2026-08-07 | 1244 | 54 | 26 | 128 | 1036 | 0.064 | 0.167 |
| port_vs_prog | prboom-plus | boom-2.02 | earliest | 5c2f54d04ae8__da39a3 | 2000-11-29 | 856 | 441 | 108 | 196 | 111 | 0.641 | 0.870 |
| port_vs_prog | prboom-plus | boom-2.02 | head | 969515162c5a__da39a3 | 2023-06-20 | 856 | 109 | 65 | 214 | 468 | 0.203 | 0.453 |
| port_vs_prog | woof | mbf-2.03 | earliest | 9ab0817c7caf__da39a3 | 2008-06-17 | 935 | 719 | 44 | 23 | 149 | 0.816 | 0.841 |
| port_vs_prog | woof | mbf-2.03 | head | 9d11c343c7fc__da39a3 | 2026-10-05 | 935 | 72 | 55 | 202 | 606 | 0.136 | 0.352 |
| port_vs_prog | eternity | smmu | earliest | a22e63c62afd__da39a3 | 2006-02-07 | 1749 | 310 | 98 | 398 | 943 | 0.233 | 0.461 |
| port_vs_prog | eternity | smmu | head | 339dfa50df91__da39a3 | 2026-10-04 | 1749 | 10 | 6 | 95 | 1638 | 0.009 | 0.064 |
| port_vs_prog | edge-classic | edge@2021-09-17 | earliest | a255d0f3752b__da39a3 | 2021-12-12 | 6805 | 2748 | 169 | 417 | 3471 | 0.429 | 0.490 |
| port_vs_prog | edge-classic | edge@2021-09-17 | head | 50b901f2f9b3__da39a3 | 2026-10-14 | 6805 | 12 | 4 | 372 | 6417 | 0.002 | 0.057 |
| port_vs_prog | inter-doom | crispy-doom@2023-06-26 | earliest | b845695b0709__cb0772 | 2023-07-06 | 2372 | 1459 | 90 | 240 | 583 | 0.653 | 0.754 |
| port_vs_prog | inter-doom | crispy-doom@2023-06-26 | head | e3018d269c1b__cb0772 | 2026-10-16 | 2372 | 1077 | 189 | 304 | 802 | 0.534 | 0.662 |
| port_vs_prog | doomretro | chocolate-doom@2013-12-10 | earliest | 4010f4ffaa4a__da39a3 | 2014-05-16 | 1908 | 123 | 46 | 217 | 1522 | 0.089 | 0.202 |
| port_vs_prog | doomretro | chocolate-doom@2013-12-10 | head | 71f94d210c5a__da39a3 | 2026-10-05 | 1908 | 6 | 1 | 26 | 1875 | 0.004 | 0.017 |

### Precondition

| name | sha | commit_date | role | scan_rc | ctags_functions | pruned | eligible | dup_share | lang_c | lang_cpp | lang_other | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| boom-2.02 | 2a11d37040be9ac40a61f4c7b7f4541bef2411bf | 2025-01-08 | primary: prboom-plus (secondary: edge-classic) | 0 | 2175 | NA | 856 | 0.083 | 0.946 | 0.027 | 0.027 | usable |
| mbf-2.03 | 8f705abd36ed2edc3ba64abb855f05a12dd71bc9 | 2025-01-08 | primary: woof; secondary: eternity | 0 | 2266 | NA | 935 | 0.105 | 0.919 | 0.025 | 0.056 | usable |
| smmu | 173934b11e861c4379b6941145b7260fee317b24 | 2001-02-25 | primary: eternity | 0 | 3274 | NA | 1749 | 0.176 | 0.886 | 0.013 | 0.101 | usable |
| edge@2021-09-17 | d7adfc6a5320211502bb26b5f3b4aa571c913be3 | 2021-09-17 | primary: edge-classic (class C) | 0 | 18134 | NA | 6805 | 0.236 | 0.119 | 0.873 | 0.008 | usable |
| crispy-doom@2023-06-26 | 595ecb2e5ee8f03162c24e9a73b369b1fb0450c8 | 2023-06-26 | primary: inter-doom (class C) | 0 | 4075 | src/heretic src/hexen src/strife | 2372 | 0.090 | 0.962 | 0.000 | 0.038 | usable |
| chocolate-doom@2013-12-10 | b9690ac0bbe2b5af137aeb09261aac4478f3fbf8 | 2013-12-10 | primary: doomretro (class C, inferred) | 0 | 3326 | src/heretic src/hexen src/strife | 1908 | 0.087 | 0.961 | 0.001 | 0.038 | usable |
| winmbf | 3af60d718b1fe272769ee9eeb768b88e29a6cd7e | 2016-08-20 | descriptive: woof's own early history (all 32 commits are inside the woof clone) | 0 | 1826 | NA | 863 | 0.076 | 1.000 | 0.000 | 0.000 | usable |
| prboom-2.5.0 | da3313ffaeb94dff71778108f209aa3b75eada72 | 2026-08-07 | descriptive sibling only (NEWS tags changes taken from PrBoom+) | 0 | 2464 | NA | 1244 | 0.123 | 0.859 | 0.004 | 0.137 | usable |

