# DOOM-E9 phase report

## Registered checks scored

| check | value | result |
|---|---|---|
| P1 (primary) | diff 0.198 [0.119, 0.265], structure 0.390 vs names 0.192 | structure higher |
| P1 (dedup) | diff 0.176 [0.100, 0.243], structure 0.368 vs names 0.192 | structure higher |
| P1 Holm-adjusted p | 0.0010 | < 0.05 |
| P2 (primary) | hard-negative upper 95% per 1,000: structure 17.881 (FP 60) vs names certified 0.721 (FP 0); n 4153 | structure bound not lower |
| P2 (dedup) | hard-negative upper 95% per 1,000: structure 18.068 (FP 60) vs names certified 0.729 (FP 0); n 4110 | structure bound not lower |
| P2 Holm-adjusted p | 1.0000 | >= 0.05 |
| Spike-in: structure recall >= 0.80 under tier (c), both sizes | size large: 0.494 [0.414, 0.573] (80/162); size small: 0.638 [0.539, 0.730] (67/105) | not met |
| Order excess above baseline (deterministic check) | 0.157 [-0.003, 0.343] | not above baseline |
| Import-cluster excess over permuted baseline (deterministic check) | 0.479 [0.410, 0.569] | above baseline |
| Falsification: recipient dated strictly before donor | 20 | listed |
| Power gate | gate met | H9.1 inferential |


Holm applies to P1 and P2 only; the spike-in, Order and import-cluster rows are deterministic checks and are not Holm-corrected. H9.5 is descriptive. The earlier fixed pass/fail thresholds are withdrawn (Amendment 1, item 20).

## Estimator choices

- Unit and clusters: a prediction belongs to the lineage pair of its two programs (Chocolate/Crispy/Inter = one lineage, PrBoom+/dsda-doom, Woof/Nugget; every other program its own). Events are nested in lineage pairs; the bootstrap resamples lineage pairs (2,000 draws, seeded), paired across the two predictors.
- Precision is pooled (micro-averaged) over all scored predictions on eligible port pairs; predictions with an unmapped engine row (func_id 'row:N') are excluded from precision and counted per predictor.
- A prediction is a T1 true positive iff the pair is in pairs.csv with eligible_primary = 1 and jaccard >= 0.9 (sensitivities: >= 0.6, and jaccard_idnorm >= 0.9). Recall counts normalised-body equivalence classes (program, body_hash) of the truth pairs, covered by any predicted pair of the same two classes (multikey sets are therefore scored by class).
- Co-primary truth for P1 = hand-audit label where the pair was audited (hand_audit_ratings.csv), otherwise T1 (>= 0.9) or both functions in the same non-empty t3_module. The T1-only version is reported beside it.
- P1 compares structure (primary, full repositories filtered post hoc) with names unique-key restricted to pair-level certified pairs (symmetric error control); the de-duplicated variants are co-primary: P1 is 'structure higher' only if the interval lies above 0 in BOTH, and its p-value is the larger of the two bootstrap tails. Raw names, premasked and other variants are sensitivities.
- Names certified = the pair passes the E7 decoy gate in either direction (200 seeded draws, 99th percentile); the gate is evaluated on the same repositories (or de-duplicated views) the predictor used.
- P2: a negative-program function is a false positive for a predictor if it appears in any emitted pair that is not T1-confirmed; denominator = eligible (loc >= 6) functions of the stratum's programs (representatives only for the de-duplicated variant); upper bound = one-sided 95% Clopper-Pearson per 1,000. The p-value for Holm is a paired exact (McNemar) one-sided test over hard-negative functions flagged by exactly one predictor, the larger of the primary and de-duplicated p-values.
- Holm is applied to the P1 and P2 p-values only (to P2 alone if the power gate makes P1 descriptive).
- Spike-in recall = hit truth functions / truth functions per (tier, size), exact two-sided 95% Clopper-Pearson interval; a hit is a predicted pair (donor function, recipient engine row) in either orientation. The registered check is a point estimate >= 0.80 at both sizes under tier (c).
- Order excess: donor-first means donor first-appearance <= borrower first-appearance (committer date), over T1-confirmed function pairs of port-to-port events with fixed donor and borrower; baseline = exact share over all uncensored functions of the same two programs not in any T1 pair of that pair; excess = pooled observed share minus the pair-count-weighted baseline; interval by bootstrap over lineage pairs. Author date is a sensitivity.
- Import cluster: groups need >= 5 dated functions; confirmed groups = the borrower functions of one event; unconfirmed groups = non-T1-confirmed structure predictions grouped by (pair, side, directory), both sides taken; permuted baseline = 200 seeded within-borrower random subsets of the same size (mean per group); native control = same-size subsets drawn from one random directory of the borrower. perm_null.npz contents are listed but the baseline is recomputed here from t2.csv.
- Module clustering: a matched borrower function counts as clustered if its directory holds >= 5 matched functions of the group, or it lies in a weakly connected component of >= 5 in the call graph induced on the group (edges from the fingerprint tables; directory-only if they are unavailable).
- Leave-one-module-out: predictions and truth classes whose module (events.csv module_cluster, or t3_module of either function) is the named module are removed; textscreen is the registered exclusion; all other modules are in a descriptive table.
- Duplicate representative: a row is a duplicate iff dup_rep is non-empty and differs from its own func_id.

Bootstrap draws 2000, seed 20261122.

Input notes:
- none

## 1. Truth and sample

Events 239, independent lineage pairs 99, distinct modules 170; T1 function pairs at Jaccard >= 0.9: 7102 in 7102 normalised-body classes; eligible port pairs 221. Power gate: **gate met** -> H9.1 is inferential.

Events (functions per event):

| event_id | donor | recipient | module_cluster | n_functions | pair_class | lineage_pair | n_pairs | module | lineage |
|---|---|---|---|---|---|---|---|---|---|
| |chocolate-doom+doom3-bfg|src|doomclassic/doom |  | chocolate-doom+doom3-bfg | src|doomclassic/doom | 1 | coincidence | chocolate-family|doom3-bfg | 1 | src|doomclassic/doom | |chocolate-doom+doom3-bfg |
| |chocolate-doom+dsda-doom|opl|prboom2/src/MUSIC |  | chocolate-doom+dsda-doom | opl|prboom2/src/MUSIC | 42 | external-library | chocolate-family|prboom-plus-family | 42 | opl | |chocolate-doom+dsda-doom |
| |chocolate-doom+dsda-doom|src|prboom2/src/MUSIC |  | chocolate-doom+dsda-doom | src|prboom2/src/MUSIC | 17 | coincidence | chocolate-family|prboom-plus-family | 17 | src|prboom2/src/MUSIC | |chocolate-doom+dsda-doom |
| |chocolate-doom+dsda-doom|src|prboom2/src |  | chocolate-doom+dsda-doom | src|prboom2/src | 2 | coincidence | chocolate-family|prboom-plus-family | 2 | src|prboom2/src | |chocolate-doom+dsda-doom |
| chocolate-doom|dsda-doom|prboom2/src/textscreen | chocolate-doom | dsda-doom | prboom2/src/textscreen | 4 | port-to-port | chocolate-family|prboom-plus-family | 4 | textscreen | chocolate|prboom |
| |chocolate-doom+eternity|src|source |  | chocolate-doom+eternity | src|source | 1 | coincidence | chocolate-family|eternity | 1 | src|source | |chocolate-doom+eternity |
| |chocolate-doom+eternity|src|source/Win32 |  | chocolate-doom+eternity | src|source/Win32 | 6 | coincidence | chocolate-family|eternity | 6 | src|source/Win32 | |chocolate-doom+eternity |
| |chocolate-doom+eternity|src|source/textscreen |  | chocolate-doom+eternity | src|source/textscreen | 1 | coincidence | chocolate-family|eternity | 1 | src|source/textscreen | |chocolate-doom+eternity |
| chocolate-doom|eternity|source/textscreen | chocolate-doom | eternity | source/textscreen | 224 | port-to-port | chocolate-family|eternity | 224 | textscreen | chocolate|eternity |
| |chocolate-doom+fastdoom|src/doom|FASTDOOM |  | chocolate-doom+fastdoom | src/doom|FASTDOOM | 2 | coincidence | chocolate-family|fastdoom | 2 | src/doom|FASTDOOM | |chocolate-doom+fastdoom |
| |chocolate-doom+fastdoom|src|FASTDOOM |  | chocolate-doom+fastdoom | src|FASTDOOM | 1 | coincidence | chocolate-family|fastdoom | 1 | src|FASTDOOM | |chocolate-doom+fastdoom |
| |chocolate-doom+gzdoom|opl|libraries/ZMusic/thirdparty/adlmidi/chips/nuked |  | chocolate-doom+gzdoom | opl|libraries/ZMusic/thirdparty/adlmidi/chips/nuked | 17 | external-library | chocolate-family|gzdoom | 17 | opl | |chocolate-doom+gzdoom |
| |chocolate-doom+nugget-doom|src|src |  | chocolate-doom+nugget-doom | src|src | 58 | coincidence | chocolate-family|woof-family | 58 | src|src | |chocolate-doom+nugget-doom |
| |chocolate-doom+odamex|src|common |  | chocolate-doom+odamex | src|common | 2 | coincidence | chocolate-family|odamex | 2 | src|common | |chocolate-doom+odamex |
| |chocolate-doom+odamex|src|libraries/textscreen |  | chocolate-doom+odamex | src|libraries/textscreen | 2 | coincidence | chocolate-family|odamex | 2 | src|libraries/textscreen | |chocolate-doom+odamex |
| |chocolate-doom+odamex|src|client/sdl |  | chocolate-doom+odamex | src|client/sdl | 1 | external-library | chocolate-family|odamex | 1 | SDL | |chocolate-doom+odamex |
| |chocolate-doom+odamex|src|libraries/textscreen/examples |  | chocolate-doom+odamex | src|libraries/textscreen/examples | 1 | coincidence | chocolate-family|odamex | 1 | src|libraries/textscreen/examples | |chocolate-doom+odamex |
| chocolate-doom|odamex|libraries/textscreen/examples | chocolate-doom | odamex | libraries/textscreen/examples | 15 | port-to-port | chocolate-family|odamex | 15 | textscreen | chocolate|odamex |
| chocolate-doom|odamex|libraries/textscreen | chocolate-doom | odamex | libraries/textscreen | 193 | port-to-port | chocolate-family|odamex | 193 | textscreen | chocolate|odamex |
| |chocolate-doom+prboom-plus|opl|prboom2/src/MUSIC |  | chocolate-doom+prboom-plus | opl|prboom2/src/MUSIC | 4 | external-library | chocolate-family|prboom-plus-family | 4 | opl | |chocolate-doom+prboom-plus |
| |chocolate-doom+prboom-plus|pcsound|prboom2/src/PCSOUND |  | chocolate-doom+prboom-plus | pcsound|prboom2/src/PCSOUND | 2 | coincidence | chocolate-family|prboom-plus-family | 2 | pcsound|prboom2/src/PCSOUND | |chocolate-doom+prboom-plus |
| |chocolate-doom+prboom-plus|src/doom|prboom2/src |  | chocolate-doom+prboom-plus | src/doom|prboom2/src | 10 | coincidence | chocolate-family|prboom-plus-family | 10 | src/doom|prboom2/src | |chocolate-doom+prboom-plus |
| |chocolate-doom+prboom-plus|src|prboom2/src |  | chocolate-doom+prboom-plus | src|prboom2/src | 21 | coincidence | chocolate-family|prboom-plus-family | 21 | src|prboom2/src | |chocolate-doom+prboom-plus |
| |chocolate-doom+prboom-plus|src|prboom2/src/MUSIC |  | chocolate-doom+prboom-plus | src|prboom2/src/MUSIC | 5 | coincidence | chocolate-family|prboom-plus-family | 5 | src|prboom2/src/MUSIC | |chocolate-doom+prboom-plus |
| chocolate-doom|prboom-plus|prboom2/src/TEXTSCREEN | chocolate-doom | prboom-plus | prboom2/src/TEXTSCREEN | 8 | port-to-port | chocolate-family|prboom-plus-family | 8 | textscreen | chocolate|prboom |
| |chocolate-doom+woof|man|man |  | chocolate-doom+woof | man|man | 8 | coincidence | chocolate-family|woof-family | 8 | man|man | |chocolate-doom+woof |
| chocolate-doom|woof|opl | chocolate-doom | woof | opl | 53 | port-to-port | chocolate-family|woof-family | 53 | opl | chocolate|woof |
| |chocolate-doom+woof|src|src |  | chocolate-doom+woof | src|src | 75 | coincidence | chocolate-family|woof-family | 75 | src|src | |chocolate-doom+woof |
| |chocolate-doom+woof|src/doom|src |  | chocolate-doom+woof | src/doom|src | 19 | coincidence | chocolate-family|woof-family | 19 | src/doom|src | |chocolate-doom+woof |
| |chocolate-doom+woof|src|textscreen |  | chocolate-doom+woof | src|textscreen | 1 | coincidence | chocolate-family|woof-family | 1 | src|textscreen | |chocolate-doom+woof |
| |chocolate-doom+woof|src/setup|setup |  | chocolate-doom+woof | src/setup|setup | 28 | coincidence | chocolate-family|woof-family | 28 | src/setup|setup | |chocolate-doom+woof |
| |chocolate-doom+woof|src|third-party/sha1 |  | chocolate-doom+woof | src|third-party/sha1 | 4 | coincidence | chocolate-family|woof-family | 4 | src|third-party/sha1 | |chocolate-doom+woof |
| chocolate-doom|woof|textscreen | chocolate-doom | woof | textscreen | 214 | port-to-port | chocolate-family|woof-family | 214 | textscreen | chocolate|woof |
| |crispy-doom+dsda-doom|src/doom|prboom2/src |  | crispy-doom+dsda-doom | src/doom|prboom2/src | 1 | coincidence | chocolate-family|prboom-plus-family | 1 | src/doom|prboom2/src | |crispy-doom+dsda-doom |
| |crispy-doom+prboom-plus|src/doom|prboom2/src |  | crispy-doom+prboom-plus | src/doom|prboom2/src | 2 | coincidence | chocolate-family|prboom-plus-family | 2 | src/doom|prboom2/src | |crispy-doom+prboom-plus |
| |crispy-doom+woof|src|src |  | crispy-doom+woof | src|src | 4 | coincidence | chocolate-family|woof-family | 4 | src|src | |crispy-doom+woof |
| |crispy-doom+woof|src/doom|src |  | crispy-doom+woof | src/doom|src | 7 | coincidence | chocolate-family|woof-family | 7 | src/doom|src | |crispy-doom+woof |
| |doom-ascii+doom3-bfg|src|doomclassic/doom |  | doom-ascii+doom3-bfg | src|doomclassic/doom | 1 | coincidence | doom-ascii|doom3-bfg | 1 | src|doomclassic/doom | |doom-ascii+doom3-bfg |
| |doom-ascii+dsda-doom|src|prboom2/src |  | doom-ascii+dsda-doom | src|prboom2/src | 2 | coincidence | doom-ascii|prboom-plus-family | 2 | src|prboom2/src | |doom-ascii+dsda-doom |
| |doom-ascii+eternity|src|source |  | doom-ascii+eternity | src|source | 1 | coincidence | doom-ascii|eternity | 1 | src|source | |doom-ascii+eternity |
| |doom-ascii+fastdoom|src|FASTDOOM |  | doom-ascii+fastdoom | src|FASTDOOM | 1 | coincidence | doom-ascii|fastdoom | 1 | src|FASTDOOM | |doom-ascii+fastdoom |
| |doom-ascii+nugget-doom|src|src |  | doom-ascii+nugget-doom | src|src | 1 | coincidence | doom-ascii|woof-family | 1 | src|src | |doom-ascii+nugget-doom |
| |doom-ascii+odamex|src|common |  | doom-ascii+odamex | src|common | 2 | coincidence | doom-ascii|odamex | 2 | src|common | |doom-ascii+odamex |
| |doom-ascii+odamex|src|libraries/textscreen |  | doom-ascii+odamex | src|libraries/textscreen | 1 | coincidence | doom-ascii|odamex | 1 | src|libraries/textscreen | |doom-ascii+odamex |
| |doom-ascii+prboom-plus|src|prboom2/src |  | doom-ascii+prboom-plus | src|prboom2/src | 12 | coincidence | doom-ascii|prboom-plus-family | 12 | src|prboom2/src | |doom-ascii+prboom-plus |
| |doom-ascii+woof|src|src |  | doom-ascii+woof | src|src | 18 | coincidence | doom-ascii|woof-family | 18 | src|src | |doom-ascii+woof |
| |doom-ascii+woof|src|third-party/sha1 |  | doom-ascii+woof | src|third-party/sha1 | 4 | coincidence | doom-ascii|woof-family | 4 | src|third-party/sha1 | |doom-ascii+woof |
| |doom-wasm+doom3-bfg|src|doomclassic/doom |  | doom-wasm+doom3-bfg | src|doomclassic/doom | 1 | coincidence | doom-wasm|doom3-bfg | 1 | src|doomclassic/doom | |doom-wasm+doom3-bfg |
| |doom-wasm+dsda-doom|opl|prboom2/src/MUSIC |  | doom-wasm+dsda-doom | opl|prboom2/src/MUSIC | 1 | external-library | doom-wasm|prboom-plus-family | 1 | opl | |doom-wasm+dsda-doom |
| |doom-wasm+dsda-doom|src|prboom2/src/MUSIC |  | doom-wasm+dsda-doom | src|prboom2/src/MUSIC | 17 | coincidence | doom-wasm|prboom-plus-family | 17 | src|prboom2/src/MUSIC | |doom-wasm+dsda-doom |
| |doom-wasm+dsda-doom|src|prboom2/src |  | doom-wasm+dsda-doom | src|prboom2/src | 2 | coincidence | doom-wasm|prboom-plus-family | 2 | src|prboom2/src | |doom-wasm+dsda-doom |
| |doom-wasm+eternity|src|source |  | doom-wasm+eternity | src|source | 1 | coincidence | doom-wasm|eternity | 1 | src|source | |doom-wasm+eternity |
| |doom-wasm+eternity|src|source/textscreen |  | doom-wasm+eternity | src|source/textscreen | 1 | coincidence | doom-wasm|eternity | 1 | src|source/textscreen | |doom-wasm+eternity |
| |doom-wasm+fastdoom|src/doom|FASTDOOM |  | doom-wasm+fastdoom | src/doom|FASTDOOM | 2 | coincidence | doom-wasm|fastdoom | 2 | src/doom|FASTDOOM | |doom-wasm+fastdoom |
| |doom-wasm+fastdoom|src|FASTDOOM |  | doom-wasm+fastdoom | src|FASTDOOM | 1 | coincidence | doom-wasm|fastdoom | 1 | src|FASTDOOM | |doom-wasm+fastdoom |
| |doom-wasm+gzdoom|opl|libraries/ZMusic/thirdparty/adlmidi/chips/nuked |  | doom-wasm+gzdoom | opl|libraries/ZMusic/thirdparty/adlmidi/chips/nuked | 11 | external-library | doom-wasm|gzdoom | 11 | opl | |doom-wasm+gzdoom |
| |doom-wasm+nugget-doom|src|src |  | doom-wasm+nugget-doom | src|src | 45 | coincidence | doom-wasm|woof-family | 45 | src|src | |doom-wasm+nugget-doom |
| |doom-wasm+odamex|src|common |  | doom-wasm+odamex | src|common | 2 | coincidence | doom-wasm|odamex | 2 | src|common | |doom-wasm+odamex |
| |doom-wasm+odamex|src|libraries/textscreen |  | doom-wasm+odamex | src|libraries/textscreen | 2 | coincidence | doom-wasm|odamex | 2 | src|libraries/textscreen | |doom-wasm+odamex |
| |doom-wasm+odamex|src|libraries/textscreen/examples |  | doom-wasm+odamex | src|libraries/textscreen/examples | 1 | coincidence | doom-wasm|odamex | 1 | src|libraries/textscreen/examples | |doom-wasm+odamex |
| |doom-wasm+prboom-plus|opl|prboom2/src/MUSIC |  | doom-wasm+prboom-plus | opl|prboom2/src/MUSIC | 4 | external-library | doom-wasm|prboom-plus-family | 4 | opl | |doom-wasm+prboom-plus |
| |doom-wasm+prboom-plus|pcsound|prboom2/src/PCSOUND |  | doom-wasm+prboom-plus | pcsound|prboom2/src/PCSOUND | 3 | coincidence | doom-wasm|prboom-plus-family | 3 | pcsound|prboom2/src/PCSOUND | |doom-wasm+prboom-plus |
| |doom-wasm+prboom-plus|src/doom|prboom2/src |  | doom-wasm+prboom-plus | src/doom|prboom2/src | 10 | coincidence | doom-wasm|prboom-plus-family | 10 | src/doom|prboom2/src | |doom-wasm+prboom-plus |
| |doom-wasm+prboom-plus|src|prboom2/src |  | doom-wasm+prboom-plus | src|prboom2/src | 21 | coincidence | doom-wasm|prboom-plus-family | 21 | src|prboom2/src | |doom-wasm+prboom-plus |
| |doom-wasm+prboom-plus|src|prboom2/src/MUSIC |  | doom-wasm+prboom-plus | src|prboom2/src/MUSIC | 5 | coincidence | doom-wasm|prboom-plus-family | 5 | src|prboom2/src/MUSIC | |doom-wasm+prboom-plus |
| |doom-wasm+woof|opl|opl |  | doom-wasm+woof | opl|opl | 12 | external-library | doom-wasm|woof-family | 12 | opl | |doom-wasm+woof |
| |doom-wasm+woof|src|src |  | doom-wasm+woof | src|src | 69 | coincidence | doom-wasm|woof-family | 69 | src|src | |doom-wasm+woof |
| |doom-wasm+woof|src/doom|src |  | doom-wasm+woof | src/doom|src | 18 | coincidence | doom-wasm|woof-family | 18 | src/doom|src | |doom-wasm+woof |
| |doom-wasm+woof|src|textscreen |  | doom-wasm+woof | src|textscreen | 1 | coincidence | doom-wasm|woof-family | 1 | src|textscreen | |doom-wasm+woof |
| |doom-wasm+woof|src|third-party/sha1 |  | doom-wasm+woof | src|third-party/sha1 | 4 | coincidence | doom-wasm|woof-family | 4 | src|third-party/sha1 | |doom-wasm+woof |
| |doom3-bfg+doomgeneric|doomclassic/doom|doomgeneric |  | doom3-bfg+doomgeneric | doomclassic/doom|doomgeneric | 1 | coincidence | doom3-bfg|doomgeneric | 1 | doomclassic/doom|doomgeneric | |doom3-bfg+doomgeneric |
| |doom3-bfg+eternity|doomclassic/doom|source |  | doom3-bfg+eternity | doomclassic/doom|source | 1 | coincidence | doom3-bfg|eternity | 1 | doomclassic/doom|source | |doom3-bfg+eternity |
| |doom3-bfg+gzdoom|doomclassic/timidity|libraries/ZMusic/thirdparty/timidityplus |  | doom3-bfg+gzdoom | doomclassic/timidity|libraries/ZMusic/thirdparty/timidityplus | 1 | coincidence | doom3-bfg|gzdoom | 1 | doomclassic/timidity|libraries/ZMusic/thirdparty/timidityplus | |doom3-bfg+gzdoom |
| |doom3-bfg+inter-doom|doomclassic/doom|src |  | doom3-bfg+inter-doom | doomclassic/doom|src | 1 | coincidence | chocolate-family|doom3-bfg | 1 | doomclassic/doom|src | |doom3-bfg+inter-doom |
| |doom3-bfg+sdl-doom|doomclassic/doom|src |  | doom3-bfg+sdl-doom | doomclassic/doom|src | 1 | coincidence | doom3-bfg|sdl-doom | 1 | doomclassic/doom|src | |doom3-bfg+sdl-doom |
| |doomgeneric+dsda-doom|doomgeneric|prboom2/src |  | doomgeneric+dsda-doom | doomgeneric|prboom2/src | 2 | coincidence | doomgeneric|prboom-plus-family | 2 | doomgeneric|prboom2/src | |doomgeneric+dsda-doom |
| |doomgeneric+eternity|doomgeneric|source |  | doomgeneric+eternity | doomgeneric|source | 1 | coincidence | doomgeneric|eternity | 1 | doomgeneric|source | |doomgeneric+eternity |
| |doomgeneric+fastdoom|doomgeneric|FASTDOOM |  | doomgeneric+fastdoom | doomgeneric|FASTDOOM | 3 | coincidence | doomgeneric|fastdoom | 3 | doomgeneric|FASTDOOM | |doomgeneric+fastdoom |
| |doomgeneric+nugget-doom|doomgeneric|src |  | doomgeneric+nugget-doom | doomgeneric|src | 1 | coincidence | doomgeneric|woof-family | 1 | doomgeneric|src | |doomgeneric+nugget-doom |
| |doomgeneric+odamex|doomgeneric|common |  | doomgeneric+odamex | doomgeneric|common | 2 | coincidence | doomgeneric|odamex | 2 | doomgeneric|common | |doomgeneric+odamex |
| |doomgeneric+odamex|doomgeneric|libraries/textscreen |  | doomgeneric+odamex | doomgeneric|libraries/textscreen | 1 | coincidence | doomgeneric|odamex | 1 | doomgeneric|libraries/textscreen | |doomgeneric+odamex |
| |doomgeneric+prboom-plus|doomgeneric|prboom2/src |  | doomgeneric+prboom-plus | doomgeneric|prboom2/src | 21 | coincidence | doomgeneric|prboom-plus-family | 21 | doomgeneric|prboom2/src | |doomgeneric+prboom-plus |
| |doomgeneric+woof|doomgeneric|src |  | doomgeneric+woof | doomgeneric|src | 30 | coincidence | doomgeneric|woof-family | 30 | doomgeneric|src | |doomgeneric+woof |
| |doomgeneric+woof|doomgeneric|third-party/sha1 |  | doomgeneric+woof | doomgeneric|third-party/sha1 | 4 | coincidence | doomgeneric|woof-family | 4 | doomgeneric|third-party/sha1 | |doomgeneric+woof |
| |doomretro+edge-classic|SDL2-2.32.10/include|libraries/sdl2/mingw/include/SDL2 |  | doomretro+edge-classic | SDL2-2.32.10/include|libraries/sdl2/mingw/include/SDL2 | 5 | external-library | doomretro|edge-classic | 5 | SDL | |doomretro+edge-classic |
| |doomretro+edge-classic|src/miniz|libraries/miniz |  | doomretro+edge-classic | src/miniz|libraries/miniz | 132 | external-library | doomretro|edge-classic | 132 | miniz | |doomretro+edge-classic |
| |doomretro+gzdoom|src/miniz|libraries/ZMusic/thirdparty/miniz |  | doomretro+gzdoom | src/miniz|libraries/ZMusic/thirdparty/miniz | 137 | external-library | doomretro|gzdoom | 137 | miniz | |doomretro+gzdoom |
| |doomretro+gzdoom|xcode/SDL2_image.framework/Versions/A/Frameworks/webp.framework/Headers/webp|libraries/webp/include/webp |  | doomretro+gzdoom | xcode/SDL2_image.framework/Versions/A/Frameworks/webp.framework/Headers/webp|libraries/webp/include/webp | 3 | external-library | doomretro|gzdoom | 3 | SDL | |doomretro+gzdoom |
| |doomretro+odamex|src|common |  | doomretro+odamex | src|common | 1 | coincidence | doomretro|odamex | 1 | src|common | |doomretro+odamex |
| |doomretro+prboom-plus|src|prboom2/src/MUSIC |  | doomretro+prboom-plus | src|prboom2/src/MUSIC | 1 | coincidence | doomretro|prboom-plus-family | 1 | src|prboom2/src/MUSIC | |doomretro+prboom-plus |
| |doomretro+srb2|SDL2-2.32.10/include|libs/SDL2/i686-w64-mingw32/include/SDL2 |  | doomretro+srb2 | SDL2-2.32.10/include|libs/SDL2/i686-w64-mingw32/include/SDL2 | 9 | external-library | doomretro|srb2 | 9 | SDL | |doomretro+srb2 |
| |doomretro+woof|src|src |  | doomretro+woof | src|src | 1 | coincidence | doomretro|woof-family | 1 | src|src | |doomretro+woof |
| |doomretro+woof|src/miniz|third-party/miniz |  | doomretro+woof | src/miniz|third-party/miniz | 139 | external-library | doomretro|woof-family | 139 | miniz | |doomretro+woof |
| |doomretro+woof|src/nano_bsp|src |  | doomretro+woof | src/nano_bsp|src | 5 | coincidence | doomretro|woof-family | 5 | src/nano_bsp|src | |doomretro+woof |
| |doomretro+woof|src/yyjson|third-party/yyjson |  | doomretro+woof | src/yyjson|third-party/yyjson | 327 | coincidence | doomretro|woof-family | 329 | src/yyjson|third-party/yyjson | |doomretro+woof |
| |doomsday+edge-classic|doomsday/external/fluidsynth/src/rvoice|libraries/fluidlite/src |  | doomsday+edge-classic | doomsday/external/fluidsynth/src/rvoice|libraries/fluidlite/src | 14 | coincidence | doomsday|edge-classic | 16 | doomsday/external/fluidsynth/src/rvoice|libraries/fluidlite/src | |doomsday+edge-classic |
| |doomsday+edge-classic|doomsday/external/fluidsynth/src/sfloader|libraries/fluidlite/src |  | doomsday+edge-classic | doomsday/external/fluidsynth/src/sfloader|libraries/fluidlite/src | 43 | coincidence | doomsday|edge-classic | 43 | doomsday/external/fluidsynth/src/sfloader|libraries/fluidlite/src | |doomsday+edge-classic |
| |doomsday+edge-classic|doomsday/external/fluidsynth/src/synth|libraries/fluidlite/src |  | doomsday+edge-classic | doomsday/external/fluidsynth/src/synth|libraries/fluidlite/src | 27 | coincidence | doomsday|edge-classic | 27 | doomsday/external/fluidsynth/src/synth|libraries/fluidlite/src | |doomsday+edge-classic |
| |doomsday+edge-classic|doomsday/external/fluidsynth/src/utils|libraries/fluidlite/src |  | doomsday+edge-classic | doomsday/external/fluidsynth/src/utils|libraries/fluidlite/src | 31 | coincidence | doomsday|edge-classic | 31 | doomsday/external/fluidsynth/src/utils|libraries/fluidlite/src | |doomsday+edge-classic |
| |doomsday+edge-classic|doomsday/external/stb|libraries/stb |  | doomsday+edge-classic | doomsday/external/stb|libraries/stb | 7 | coincidence | doomsday|edge-classic | 7 | doomsday/external/stb|libraries/stb | |doomsday+edge-classic |
| |doomsday+edge-classic|doomsday/libs/gui/src/text|libraries/stb |  | doomsday+edge-classic | doomsday/libs/gui/src/text|libraries/stb | 87 | coincidence | doomsday|edge-classic | 87 | doomsday/libs/gui/src/text|libraries/stb | |doomsday+edge-classic |
| |doomsday+eternity|doomsday/external/json/include/nlohmann/detail/conversions|source/nlohmann |  | doomsday+eternity | doomsday/external/json/include/nlohmann/detail/conversions|source/nlohmann | 2 | coincidence | doomsday|eternity | 2 | doomsday/external/json/include/nlohmann/detail/conversions|source/nlohmann | |doomsday+eternity |
| |doomsday+eternity|doomsday/external/json/include/nlohmann/detail/input|source/nlohmann |  | doomsday+eternity | doomsday/external/json/include/nlohmann/detail/input|source/nlohmann | 2 | coincidence | doomsday|eternity | 2 | doomsday/external/json/include/nlohmann/detail/input|source/nlohmann | |doomsday+eternity |
| |doomsday+eternity|doomsday/external/json/include/nlohmann/detail/iterators|source/nlohmann |  | doomsday+eternity | doomsday/external/json/include/nlohmann/detail/iterators|source/nlohmann | 5 | coincidence | doomsday|eternity | 5 | doomsday/external/json/include/nlohmann/detail/iterators|source/nlohmann | |doomsday+eternity |
| |doomsday+eternity|doomsday/external/json/include/nlohmann|source/nlohmann |  | doomsday+eternity | doomsday/external/json/include/nlohmann|source/nlohmann | 9 | coincidence | doomsday|eternity | 9 | doomsday/external/json/include/nlohmann|source/nlohmann | |doomsday+eternity |
| |doomsday+gzdoom|doomsday/external/fluidsynth/src/drivers|libraries/ZMusic/thirdparty/fluidsynth/src/drivers |  | doomsday+gzdoom | doomsday/external/fluidsynth/src/drivers|libraries/ZMusic/thirdparty/fluidsynth/src/drivers | 5 | coincidence | doomsday|gzdoom | 5 | doomsday/external/fluidsynth/src/drivers|libraries/ZMusic/thirdparty/fluidsynth/src/drivers | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/fluidsynth/src/midi|libraries/ZMusic/thirdparty/fluidsynth/src/midi |  | doomsday+gzdoom | doomsday/external/fluidsynth/src/midi|libraries/ZMusic/thirdparty/fluidsynth/src/midi | 29 | coincidence | doomsday|gzdoom | 29 | doomsday/external/fluidsynth/src/midi|libraries/ZMusic/thirdparty/fluidsynth/src/midi | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/fluidsynth/src/rvoice|libraries/ZMusic/thirdparty/fluidsynth/src/rvoice |  | doomsday+gzdoom | doomsday/external/fluidsynth/src/rvoice|libraries/ZMusic/thirdparty/fluidsynth/src/rvoice | 3 | coincidence | doomsday|gzdoom | 3 | doomsday/external/fluidsynth/src/rvoice|libraries/ZMusic/thirdparty/fluidsynth/src/rvoice | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/fluidsynth/src/sfloader|libraries/ZMusic/thirdparty/fluidsynth/src/sfloader |  | doomsday+gzdoom | doomsday/external/fluidsynth/src/sfloader|libraries/ZMusic/thirdparty/fluidsynth/src/sfloader | 2 | coincidence | doomsday|gzdoom | 2 | doomsday/external/fluidsynth/src/sfloader|libraries/ZMusic/thirdparty/fluidsynth/src/sfloader | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/fluidsynth/src/synth|libraries/ZMusic/thirdparty/fluidsynth/src/synth |  | doomsday+gzdoom | doomsday/external/fluidsynth/src/synth|libraries/ZMusic/thirdparty/fluidsynth/src/synth | 39 | coincidence | doomsday|gzdoom | 39 | doomsday/external/fluidsynth/src/synth|libraries/ZMusic/thirdparty/fluidsynth/src/synth | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/fluidsynth/src/utils|libraries/ZMusic/thirdparty/fluidsynth/src/utils |  | doomsday+gzdoom | doomsday/external/fluidsynth/src/utils|libraries/ZMusic/thirdparty/fluidsynth/src/utils | 26 | coincidence | doomsday|gzdoom | 26 | doomsday/external/fluidsynth/src/utils|libraries/ZMusic/thirdparty/fluidsynth/src/utils | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/json/include/nlohmann/detail/conversions|libraries/cppdap/third_party/json/include/nlohmann/detail/conversions |  | doomsday+gzdoom | doomsday/external/json/include/nlohmann/detail/conversions|libraries/cppdap/third_party/json/include/nlohmann/detail/conversions | 25 | coincidence | doomsday|gzdoom | 27 | doomsday/external/json/include/nlohmann/detail/conversions|libraries/cppdap/third_party/json/include/nlohmann/detail/conversions | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/json/include/nlohmann/detail|libraries/cppdap/third_party/json/include/nlohmann/detail |  | doomsday+gzdoom | doomsday/external/json/include/nlohmann/detail|libraries/cppdap/third_party/json/include/nlohmann/detail | 12 | coincidence | doomsday|gzdoom | 12 | doomsday/external/json/include/nlohmann/detail|libraries/cppdap/third_party/json/include/nlohmann/detail | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/json/include/nlohmann/detail/input|libraries/cppdap/third_party/json/include/nlohmann/detail/input |  | doomsday+gzdoom | doomsday/external/json/include/nlohmann/detail/input|libraries/cppdap/third_party/json/include/nlohmann/detail/input | 13 | coincidence | doomsday|gzdoom | 13 | doomsday/external/json/include/nlohmann/detail/input|libraries/cppdap/third_party/json/include/nlohmann/detail/input | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/json/include/nlohmann/detail/iterators|libraries/cppdap/third_party/json/include/nlohmann/detail/iterators |  | doomsday+gzdoom | doomsday/external/json/include/nlohmann/detail/iterators|libraries/cppdap/third_party/json/include/nlohmann/detail/iterators | 21 | coincidence | doomsday|gzdoom | 21 | doomsday/external/json/include/nlohmann/detail/iterators|libraries/cppdap/third_party/json/include/nlohmann/detail/iterators | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/json/include/nlohmann/detail/output|libraries/cppdap/third_party/json/include/nlohmann/detail/output |  | doomsday+gzdoom | doomsday/external/json/include/nlohmann/detail/output|libraries/cppdap/third_party/json/include/nlohmann/detail/output | 5 | coincidence | doomsday|gzdoom | 5 | doomsday/external/json/include/nlohmann/detail/output|libraries/cppdap/third_party/json/include/nlohmann/detail/output | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/json/include/nlohmann|libraries/cppdap/third_party/json/include/nlohmann |  | doomsday+gzdoom | doomsday/external/json/include/nlohmann|libraries/cppdap/third_party/json/include/nlohmann | 55 | coincidence | doomsday|gzdoom | 71 | doomsday/external/json/include/nlohmann|libraries/cppdap/third_party/json/include/nlohmann | |doomsday+gzdoom |
| |doomsday+gzdoom|doomsday/external/stb|src/common/thirdparty/stb |  | doomsday+gzdoom | doomsday/external/stb|src/common/thirdparty/stb | 151 | coincidence | doomsday|gzdoom | 151 | doomsday/external/stb|src/common/thirdparty/stb | |doomsday+gzdoom |
| |doomsday+inter-doom|doomsday/external/stb|lib/stb_image_write |  | doomsday+inter-doom | doomsday/external/stb|lib/stb_image_write | 25 | coincidence | chocolate-family|doomsday | 25 | doomsday/external/stb|lib/stb_image_write | |doomsday+inter-doom |
| |dsda-doom+gzdoom|prboom2/src/MUSIC|libraries/ZMusic/thirdparty/adlmidi/chips/nuked |  | dsda-doom+gzdoom | prboom2/src/MUSIC|libraries/ZMusic/thirdparty/adlmidi/chips/nuked | 17 | coincidence | gzdoom|prboom-plus-family | 17 | prboom2/src/MUSIC|libraries/ZMusic/thirdparty/adlmidi/chips/nuked | |dsda-doom+gzdoom |
| |dsda-doom+gzdoom|prboom2/src/dsda|src/gamedata |  | dsda-doom+gzdoom | prboom2/src/dsda|src/gamedata | 1 | coincidence | gzdoom|prboom-plus-family | 1 | prboom2/src/dsda|src/gamedata | |dsda-doom+gzdoom |
| |dsda-doom+inter-doom|prboom2/src/MUSIC|lib/opl |  | dsda-doom+inter-doom | prboom2/src/MUSIC|lib/opl | 42 | external-library | chocolate-family|prboom-plus-family | 42 | opl | |dsda-doom+inter-doom |
| |dsda-doom+inter-doom|prboom2/src/MUSIC|src |  | dsda-doom+inter-doom | prboom2/src/MUSIC|src | 16 | coincidence | chocolate-family|prboom-plus-family | 16 | prboom2/src/MUSIC|src | |dsda-doom+inter-doom |
| |dsda-doom+inter-doom|prboom2/src|src |  | dsda-doom+inter-doom | prboom2/src|src | 2 | coincidence | chocolate-family|prboom-plus-family | 2 | prboom2/src|src | |dsda-doom+inter-doom |
| |dsda-doom+odamex|prboom2/src|common |  | dsda-doom+odamex | prboom2/src|common | 4 | coincidence | odamex|prboom-plus-family | 4 | prboom2/src|common | |dsda-doom+odamex |
| chocolate-doom|dsda-doom+odamex|textscreen | chocolate-doom | dsda-doom+odamex | textscreen | 1 | co-borrowing | odamex|prboom-plus-family | 1 | textscreen | chocolate|dsda-doom+odamex |
| |dsda-doom+sdl-doom|prboom2/src|src |  | dsda-doom+sdl-doom | prboom2/src|src | 2 | coincidence | prboom-plus-family|sdl-doom | 2 | prboom2/src|src | |dsda-doom+sdl-doom |
| |edge-classic+gzdoom|libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/synth |  | edge-classic+gzdoom | libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/synth | 5 | coincidence | edge-classic|gzdoom | 5 | libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/synth | |edge-classic+gzdoom |
| |edge-classic+gzdoom|libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/utils |  | edge-classic+gzdoom | libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/utils | 12 | coincidence | edge-classic|gzdoom | 12 | libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/utils | |edge-classic+gzdoom |
| |edge-classic+gzdoom|libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/sfloader |  | edge-classic+gzdoom | libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/sfloader | 2 | coincidence | edge-classic|gzdoom | 2 | libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/sfloader | |edge-classic+gzdoom |
| |edge-classic+gzdoom|libraries/minivorbis|libraries/ZMusic/thirdparty/dumb/src/helpers |  | edge-classic+gzdoom | libraries/minivorbis|libraries/ZMusic/thirdparty/dumb/src/helpers | 2 | coincidence | edge-classic|gzdoom | 2 | libraries/minivorbis|libraries/ZMusic/thirdparty/dumb/src/helpers | |edge-classic+gzdoom |
| |edge-classic+gzdoom|libraries/miniz|libraries/ZMusic/thirdparty/miniz |  | edge-classic+gzdoom | libraries/miniz|libraries/ZMusic/thirdparty/miniz | 133 | external-library | edge-classic|gzdoom | 133 | miniz | |edge-classic+gzdoom |
| |edge-classic+gzdoom|libraries/opalmidi|libraries/ZMusic/thirdparty/adlmidi/chips/opal/old |  | edge-classic+gzdoom | libraries/opalmidi|libraries/ZMusic/thirdparty/adlmidi/chips/opal/old | 18 | coincidence | edge-classic|gzdoom | 18 | libraries/opalmidi|libraries/ZMusic/thirdparty/adlmidi/chips/opal/old | |edge-classic+gzdoom |
| |edge-classic+gzdoom|libraries/stb|src/common/thirdparty/stb |  | edge-classic+gzdoom | libraries/stb|src/common/thirdparty/stb | 18 | coincidence | edge-classic|gzdoom | 18 | libraries/stb|src/common/thirdparty/stb | |edge-classic+gzdoom |
| |edge-classic+inter-doom|libraries/miniz|lib/miniz |  | edge-classic+inter-doom | libraries/miniz|lib/miniz | 132 | external-library | chocolate-family|edge-classic | 132 | miniz | |edge-classic+inter-doom |
| |edge-classic+inter-doom|libraries/sdl2/mingw/include/SDL2|lib/win32/SDL2-2.32.10/include |  | edge-classic+inter-doom | libraries/sdl2/mingw/include/SDL2|lib/win32/SDL2-2.32.10/include | 5 | external-library | chocolate-family|edge-classic | 5 | SDL | |edge-classic+inter-doom |
| |edge-classic+lua|libraries/lua|. |  | edge-classic+lua | libraries/lua|. | 516 | external-library | edge-classic|lua | 516 | lua | |edge-classic+lua |
| |edge-classic+lua|source_files/edge/script/compat|. |  | edge-classic+lua | source_files/edge/script/compat|. | 1 | coincidence | edge-classic|lua | 1 | source_files/edge/script/compat|. | |edge-classic+lua |
| |edge-classic+srb2|libraries/lua|src/blua |  | edge-classic+srb2 | libraries/lua|src/blua | 39 | external-library | edge-classic|srb2 | 39 | lua | |edge-classic+srb2 |
| |edge-classic+srb2|libraries/sdl2/mingw/include/SDL2|libs/SDL2/i686-w64-mingw32/include/SDL2 |  | edge-classic+srb2 | libraries/sdl2/mingw/include/SDL2|libs/SDL2/i686-w64-mingw32/include/SDL2 | 5 | external-library | edge-classic|srb2 | 5 | SDL | |edge-classic+srb2 |
| |eternity+gzdoom|snes_spc|libraries/ZMusic/thirdparty/game-music-emu/gme |  | eternity+gzdoom | snes_spc|libraries/ZMusic/thirdparty/game-music-emu/gme | 29 | coincidence | eternity|gzdoom | 31 | snes_spc|libraries/ZMusic/thirdparty/game-music-emu/gme | |eternity+gzdoom |
| |eternity+gzdoom|source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/conversions |  | eternity+gzdoom | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/conversions | 8 | coincidence | eternity|gzdoom | 8 | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/conversions | |eternity+gzdoom |
| |eternity+gzdoom|source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/iterators |  | eternity+gzdoom | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/iterators | 6 | coincidence | eternity|gzdoom | 6 | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/iterators | |eternity+gzdoom |
| |eternity+gzdoom|source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/input |  | eternity+gzdoom | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/input | 3 | coincidence | eternity|gzdoom | 3 | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/input | |eternity+gzdoom |
| |eternity+gzdoom|source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail |  | eternity+gzdoom | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail | 2 | coincidence | eternity|gzdoom | 2 | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail | |eternity+gzdoom |
| |eternity+gzdoom|source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/output |  | eternity+gzdoom | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/output | 5 | coincidence | eternity|gzdoom | 5 | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/output | |eternity+gzdoom |
| |eternity+gzdoom|source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann |  | eternity+gzdoom | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann | 12 | coincidence | eternity|gzdoom | 12 | source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann | |eternity+gzdoom |
| |eternity+inter-doom|libpng/arm|lib/spng |  | eternity+inter-doom | libpng/arm|lib/spng | 1 | external-library | chocolate-family|eternity | 1 | libpng | |eternity+inter-doom |
| |eternity+inter-doom|source/Win32|src |  | eternity+inter-doom | source/Win32|src | 6 | coincidence | chocolate-family|eternity | 6 | source/Win32|src | |eternity+inter-doom |
| |eternity+inter-doom|source|src |  | eternity+inter-doom | source|src | 1 | coincidence | chocolate-family|eternity | 1 | source|src | |eternity+inter-doom |
| |eternity+odamex|source/Win32|client/sdl |  | eternity+odamex | source/Win32|client/sdl | 1 | external-library | eternity|odamex | 1 | SDL | |eternity+odamex |
| |eternity+odamex|source|common |  | eternity+odamex | source|common | 6 | coincidence | eternity|odamex | 6 | source|common | |eternity+odamex |
| chocolate-doom|eternity+odamex|textscreen | chocolate-doom | eternity+odamex | textscreen | 218 | co-borrowing | eternity|odamex | 218 | textscreen | chocolate|eternity+odamex |
| |eternity+sdl-doom|source|src |  | eternity+sdl-doom | source|src | 1 | coincidence | eternity|sdl-doom | 1 | source|src | |eternity+sdl-doom |
| |eternity+srb2|libpng|libs/libpng-src |  | eternity+srb2 | libpng|libs/libpng-src | 425 | external-library | eternity|srb2 | 435 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/arm|libs/libpng-src/arm |  | eternity+srb2 | libpng/arm|libs/libpng-src/arm | 11 | external-library | eternity|srb2 | 11 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/contrib/arm-neon|libs/libpng-src/contrib/arm-neon |  | eternity+srb2 | libpng/contrib/arm-neon|libs/libpng-src/contrib/arm-neon | 4 | external-library | eternity|srb2 | 4 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/contrib/examples|libs/libpng-src/contrib/examples |  | eternity+srb2 | libpng/contrib/examples|libs/libpng-src/contrib/examples | 12 | external-library | eternity|srb2 | 12 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/contrib/gregbook|libs/libpng-src/contrib/gregbook |  | eternity+srb2 | libpng/contrib/gregbook|libs/libpng-src/contrib/gregbook | 41 | external-library | eternity|srb2 | 41 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/contrib/libtests|libs/libpng-src/contrib/libtests |  | eternity+srb2 | libpng/contrib/libtests|libs/libpng-src/contrib/libtests | 420 | external-library | eternity|srb2 | 462 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/contrib/oss-fuzz|libs/libpng-src/contrib/oss-fuzz |  | eternity+srb2 | libpng/contrib/oss-fuzz|libs/libpng-src/contrib/oss-fuzz | 3 | external-library | eternity|srb2 | 3 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/contrib/pngminus|libs/libpng-src/contrib/pngminus |  | eternity+srb2 | libpng/contrib/pngminus|libs/libpng-src/contrib/pngminus | 9 | external-library | eternity|srb2 | 9 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/contrib/powerpc-vsx|libs/libpng-src/contrib/powerpc-vsx |  | eternity+srb2 | libpng/contrib/powerpc-vsx|libs/libpng-src/contrib/powerpc-vsx | 2 | external-library | eternity|srb2 | 2 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/contrib/tools|libs/libpng-src/contrib/tools |  | eternity+srb2 | libpng/contrib/tools|libs/libpng-src/contrib/tools | 144 | external-library | eternity|srb2 | 146 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/contrib/visupng|libs/libpng-src/contrib/visupng |  | eternity+srb2 | libpng/contrib/visupng|libs/libpng-src/contrib/visupng | 11 | external-library | eternity|srb2 | 11 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/intel|libs/libpng-src/intel |  | eternity+srb2 | libpng/intel|libs/libpng-src/intel | 9 | external-library | eternity|srb2 | 9 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/mips|libs/libpng-src/mips |  | eternity+srb2 | libpng/mips|libs/libpng-src/mips | 8 | external-library | eternity|srb2 | 8 | libpng | |eternity+srb2 |
| |eternity+srb2|libpng/powerpc|libs/libpng-src/powerpc |  | eternity+srb2 | libpng/powerpc|libs/libpng-src/powerpc | 8 | external-library | eternity|srb2 | 8 | libpng | |eternity+srb2 |
| |eternity+srb2|snes_spc|libs/gme/gme |  | eternity+srb2 | snes_spc|libs/gme/gme | 34 | coincidence | eternity|srb2 | 36 | snes_spc|libs/gme/gme | |eternity+srb2 |
| |eternity+srb2|zlib|libs/zlib |  | eternity+srb2 | zlib|libs/zlib | 33 | external-library | eternity|srb2 | 33 | zlib | |eternity+srb2 |
| |eternity+srb2|zlib|libs/zlib/test |  | eternity+srb2 | zlib|libs/zlib/test | 1 | external-library | eternity|srb2 | 1 | zlib | |eternity+srb2 |
| |fastdoom+inter-doom|FASTDOOM|src |  | fastdoom+inter-doom | FASTDOOM|src | 1 | coincidence | chocolate-family|fastdoom | 1 | FASTDOOM|src | |fastdoom+inter-doom |
| |fastdoom+prboom-plus|FASTDOOM|prboom2/src |  | fastdoom+prboom-plus | FASTDOOM|prboom2/src | 1 | coincidence | fastdoom|prboom-plus-family | 1 | FASTDOOM|prboom2/src | |fastdoom+prboom-plus |
| |fastdoom+sdl-doom|FASTDOOM|src |  | fastdoom+sdl-doom | FASTDOOM|src | 3 | coincidence | fastdoom|sdl-doom | 3 | FASTDOOM|src | |fastdoom+sdl-doom |
| |fastdoom+woof|FASTDOOM|src |  | fastdoom+woof | FASTDOOM|src | 1 | coincidence | fastdoom|woof-family | 1 | FASTDOOM|src | |fastdoom+woof |
| |gzdoom+inter-doom|libraries/ZMusic/thirdparty/adlmidi/chips/nuked|lib/opl |  | gzdoom+inter-doom | libraries/ZMusic/thirdparty/adlmidi/chips/nuked|lib/opl | 17 | external-library | chocolate-family|gzdoom | 17 | opl | |gzdoom+inter-doom |
| |gzdoom+inter-doom|libraries/ZMusic/thirdparty/miniz|lib/miniz |  | gzdoom+inter-doom | libraries/ZMusic/thirdparty/miniz|lib/miniz | 137 | external-library | chocolate-family|gzdoom | 137 | miniz | |gzdoom+inter-doom |
| |gzdoom+inter-doom|src/common/thirdparty/stb|lib/stb_image_write |  | gzdoom+inter-doom | src/common/thirdparty/stb|lib/stb_image_write | 1 | coincidence | chocolate-family|gzdoom | 1 | src/common/thirdparty/stb|lib/stb_image_write | |gzdoom+inter-doom |
| |gzdoom+prboom-plus|cmake|prboom2/cmake |  | gzdoom+prboom-plus | cmake|prboom2/cmake | 1 | coincidence | gzdoom|prboom-plus-family | 1 | cmake|prboom2/cmake | |gzdoom+prboom-plus |
| |gzdoom+prboom-plus|libraries/ZMusic/thirdparty/adlmidi/chips/dosbox|prboom2/src/MUSIC |  | gzdoom+prboom-plus | libraries/ZMusic/thirdparty/adlmidi/chips/dosbox|prboom2/src/MUSIC | 4 | coincidence | gzdoom|prboom-plus-family | 4 | libraries/ZMusic/thirdparty/adlmidi/chips/dosbox|prboom2/src/MUSIC | |gzdoom+prboom-plus |
| |gzdoom+srb2|libraries/ZMusic/thirdparty/game-music-emu/gme|libs/gme/gme |  | gzdoom+srb2 | libraries/ZMusic/thirdparty/game-music-emu/gme|libs/gme/gme | 423 | coincidence | gzdoom|srb2 | 429 | libraries/ZMusic/thirdparty/game-music-emu/gme|libs/gme/gme | |gzdoom+srb2 |
| |gzdoom+woof|libraries/ZMusic/thirdparty/adlmidi/chips/nuked|opl |  | gzdoom+woof | libraries/ZMusic/thirdparty/adlmidi/chips/nuked|opl | 17 | external-library | gzdoom|woof-family | 17 | opl | |gzdoom+woof |
| |gzdoom+woof|libraries/ZMusic/thirdparty/miniz|third-party/miniz |  | gzdoom+woof | libraries/ZMusic/thirdparty/miniz|third-party/miniz | 137 | external-library | gzdoom|woof-family | 137 | miniz | |gzdoom+woof |
| |inter-doom+nugget-doom|lib/netlib|netlib |  | inter-doom+nugget-doom | lib/netlib|netlib | 12 | coincidence | chocolate-family|woof-family | 12 | lib/netlib|netlib | |inter-doom+nugget-doom |
| |inter-doom+nugget-doom|src|src |  | inter-doom+nugget-doom | src|src | 61 | coincidence | chocolate-family|woof-family | 61 | src|src | |inter-doom+nugget-doom |
| |inter-doom+odamex|src|common |  | inter-doom+odamex | src|common | 2 | coincidence | chocolate-family|odamex | 2 | src|common | |inter-doom+odamex |
| |inter-doom+odamex|src|client/sdl |  | inter-doom+odamex | src|client/sdl | 1 | external-library | chocolate-family|odamex | 1 | SDL | |inter-doom+odamex |
| |inter-doom+prboom-plus|lib/opl|prboom2/src/MUSIC |  | inter-doom+prboom-plus | lib/opl|prboom2/src/MUSIC | 4 | external-library | chocolate-family|prboom-plus-family | 4 | opl | |inter-doom+prboom-plus |
| |inter-doom+prboom-plus|src/doom|prboom2/src |  | inter-doom+prboom-plus | src/doom|prboom2/src | 10 | coincidence | chocolate-family|prboom-plus-family | 10 | src/doom|prboom2/src | |inter-doom+prboom-plus |
| |inter-doom+prboom-plus|src|prboom2/src |  | inter-doom+prboom-plus | src|prboom2/src | 20 | coincidence | chocolate-family|prboom-plus-family | 20 | src|prboom2/src | |inter-doom+prboom-plus |
| |inter-doom+prboom-plus|src|prboom2/src/MUSIC |  | inter-doom+prboom-plus | src|prboom2/src/MUSIC | 5 | coincidence | chocolate-family|prboom-plus-family | 5 | src|prboom2/src/MUSIC | |inter-doom+prboom-plus |
| |inter-doom+srb2|lib/spng|libs/libpng-src/arm |  | inter-doom+srb2 | lib/spng|libs/libpng-src/arm | 1 | external-library | chocolate-family|srb2 | 1 | libpng | |inter-doom+srb2 |
| |inter-doom+srb2|lib/win32/SDL2-2.32.10/include|libs/SDL2/i686-w64-mingw32/include/SDL2 |  | inter-doom+srb2 | lib/win32/SDL2-2.32.10/include|libs/SDL2/i686-w64-mingw32/include/SDL2 | 9 | external-library | chocolate-family|srb2 | 9 | SDL | |inter-doom+srb2 |
| |inter-doom+woof|lib/miniz|third-party/miniz |  | inter-doom+woof | lib/miniz|third-party/miniz | 139 | external-library | chocolate-family|woof-family | 139 | miniz | |inter-doom+woof |
| |inter-doom+woof|lib/opl|opl |  | inter-doom+woof | lib/opl|opl | 53 | external-library | chocolate-family|woof-family | 53 | opl | |inter-doom+woof |
| |inter-doom+woof|lib/spng|third-party/spng |  | inter-doom+woof | lib/spng|third-party/spng | 161 | coincidence | chocolate-family|woof-family | 161 | lib/spng|third-party/spng | |inter-doom+woof |
| |inter-doom+woof|src|src |  | inter-doom+woof | src|src | 75 | coincidence | chocolate-family|woof-family | 75 | src|src | |inter-doom+woof |
| |inter-doom+woof|src/doom|src |  | inter-doom+woof | src/doom|src | 16 | coincidence | chocolate-family|woof-family | 16 | src/doom|src | |inter-doom+woof |
| |inter-doom+woof|src/netgame|setup |  | inter-doom+woof | src/netgame|setup | 28 | coincidence | chocolate-family|woof-family | 28 | src/netgame|setup | |inter-doom+woof |
| |inter-doom+woof|src|third-party/sha1 |  | inter-doom+woof | src|third-party/sha1 | 4 | coincidence | chocolate-family|woof-family | 4 | src|third-party/sha1 | |inter-doom+woof |
| |lua+srb2|.|src/blua |  | lua+srb2 | .|src/blua | 32 | external-library | lua|srb2 | 32 | lua | |lua+srb2 |
| |nugget-doom+sdl-doom|src|src |  | nugget-doom+sdl-doom | src|src | 1 | coincidence | sdl-doom|woof-family | 1 | src|src | |nugget-doom+sdl-doom |
| |odamex+prboom-plus|common|prboom2/src |  | odamex+prboom-plus | common|prboom2/src | 1 | coincidence | odamex|prboom-plus-family | 1 | common|prboom2/src | |odamex+prboom-plus |
| chocolate-doom|odamex+prboom-plus|textscreen | chocolate-doom | odamex+prboom-plus | textscreen | 10 | co-borrowing | odamex|prboom-plus-family | 10 | textscreen | chocolate|odamex+prboom-plus |
| |odamex+quake|common|QW/client |  | odamex+quake | common|QW/client | 1 | coincidence | odamex|quake | 1 | common|QW/client | |odamex+quake |
| |odamex+quake|master|QW/client |  | odamex+quake | master|QW/client | 1 | coincidence | odamex|quake | 1 | master|QW/client | |odamex+quake |
| |odamex+quake2|common|linux |  | odamex+quake2 | common|linux | 1 | coincidence | odamex|quake2 | 1 | common|linux | |odamex+quake2 |
| |odamex+sdl-doom|common|src |  | odamex+sdl-doom | common|src | 2 | coincidence | odamex|sdl-doom | 2 | common|src | |odamex+sdl-doom |
| |odamex+sdl-doom|libraries/textscreen|src |  | odamex+sdl-doom | libraries/textscreen|src | 1 | coincidence | odamex|sdl-doom | 1 | libraries/textscreen|src | |odamex+sdl-doom |
| |odamex+woof|common|src |  | odamex+woof | common|src | 2 | coincidence | odamex|woof-family | 2 | common|src | |odamex+woof |
| chocolate-doom|odamex+woof|textscreen | chocolate-doom | odamex+woof | textscreen | 166 | co-borrowing | odamex|woof-family | 166 | textscreen | chocolate|odamex+woof |
| |odamex+woof|libraries/textscreen|src |  | odamex+woof | libraries/textscreen|src | 1 | coincidence | odamex|woof-family | 1 | libraries/textscreen|src | |odamex+woof |
| |prboom-plus+sdl-doom|prboom2/src|src |  | prboom-plus+sdl-doom | prboom2/src|src | 21 | coincidence | prboom-plus-family|sdl-doom | 21 | prboom2/src|src | |prboom-plus+sdl-doom |
| |prboom-plus+srb2|prboom2/src/WIN|src |  | prboom-plus+srb2 | prboom2/src/WIN|src | 1 | coincidence | prboom-plus-family|srb2 | 1 | prboom2/src/WIN|src | |prboom-plus+srb2 |
| |prboom-plus+srb2|prboom2/src|src/hardware |  | prboom-plus+srb2 | prboom2/src|src/hardware | 9 | coincidence | prboom-plus-family|srb2 | 9 | prboom2/src|src/hardware | |prboom-plus+srb2 |
| |quake+quake2|QW/client|linux |  | quake+quake2 | QW/client|linux | 9 | coincidence | quake|quake2 | 9 | QW/client|linux | |quake+quake2 |
| |quake+quake2|QW/client|win32 |  | quake+quake2 | QW/client|win32 | 3 | coincidence | quake|quake2 | 3 | QW/client|win32 | |quake+quake2 |
| |quake+quake2|QW/client|client |  | quake+quake2 | QW/client|client | 12 | coincidence | quake|quake2 | 12 | QW/client|client | |quake+quake2 |
| |quake+quake2|QW/client|qcommon |  | quake+quake2 | QW/client|qcommon | 17 | coincidence | quake|quake2 | 17 | QW/client|qcommon | |quake+quake2 |
| |quake+quake2|QW/client|server |  | quake+quake2 | QW/client|server | 1 | coincidence | quake|quake2 | 1 | QW/client|server | |quake+quake2 |
| |quake+quake2|QW/client|ctf |  | quake+quake2 | QW/client|ctf | 24 | coincidence | quake|quake2 | 24 | QW/client|ctf | |quake+quake2 |
| |quake+quake2|QW/client|ref_soft |  | quake+quake2 | QW/client|ref_soft | 38 | coincidence | quake|quake2 | 38 | QW/client|ref_soft | |quake+quake2 |
| |quake+quake2|QW/client|ref_gl |  | quake+quake2 | QW/client|ref_gl | 10 | coincidence | quake|quake2 | 10 | QW/client|ref_gl | |quake+quake2 |
| |quake+quake2|QW/client|irix |  | quake+quake2 | QW/client|irix | 3 | coincidence | quake|quake2 | 3 | QW/client|irix | |quake+quake2 |
| |quake+quake2|QW/server|ref_gl |  | quake+quake2 | QW/server|ref_gl | 1 | coincidence | quake|quake2 | 1 | QW/server|ref_gl | |quake+quake2 |
| |quake+quake2|QW/server|game |  | quake+quake2 | QW/server|game | 1 | coincidence | quake|quake2 | 1 | QW/server|game | |quake+quake2 |
| |quake+quake2|QW/server|server |  | quake+quake2 | QW/server|server | 3 | coincidence | quake|quake2 | 3 | QW/server|server | |quake+quake2 |
| |quake+quake2|WinQuake|qcommon |  | quake+quake2 | WinQuake|qcommon | 2 | coincidence | quake|quake2 | 2 | WinQuake|qcommon | |quake+quake2 |
| |quake+quake2|WinQuake|win32 |  | quake+quake2 | WinQuake|win32 | 6 | coincidence | quake|quake2 | 6 | WinQuake|win32 | |quake+quake2 |
| |quake+quake2|WinQuake|ref_gl |  | quake+quake2 | WinQuake|ref_gl | 2 | coincidence | quake|quake2 | 2 | WinQuake|ref_gl | |quake+quake2 |
| |quake+quake2|WinQuake|ctf |  | quake+quake2 | WinQuake|ctf | 1 | coincidence | quake|quake2 | 1 | WinQuake|ctf | |quake+quake2 |
| |quake+quake2|WinQuake|client |  | quake+quake2 | WinQuake|client | 1 | coincidence | quake|quake2 | 1 | WinQuake|client | |quake+quake2 |
| |quake+quake2|WinQuake|irix |  | quake+quake2 | WinQuake|irix | 1 | coincidence | quake|quake2 | 1 | WinQuake|irix | |quake+quake2 |
| |quake+quake2|WinQuake|linux |  | quake+quake2 | WinQuake|linux | 2 | coincidence | quake|quake2 | 2 | WinQuake|linux | |quake+quake2 |
| |quake+srb2|QW/client|src |  | quake+srb2 | QW/client|src | 1 | coincidence | quake|srb2 | 1 | QW/client|src | |quake+srb2 |
| |quake2+srb2|ctf|src |  | quake2+srb2 | ctf|src | 1 | coincidence | quake2|srb2 | 1 | ctf|src | |quake2+srb2 |
| |sdl-doom+woof|src|src |  | sdl-doom+woof | src|src | 30 | coincidence | sdl-doom|woof-family | 30 | src|src | |sdl-doom+woof |
| |sdl-doom+woof|src|third-party/sha1 |  | sdl-doom+woof | src|third-party/sha1 | 4 | coincidence | sdl-doom|woof-family | 4 | src|third-party/sha1 | |sdl-doom+woof |
| |srb2+woof|libs/libpng-src/arm|third-party/spng |  | srb2+woof | libs/libpng-src/arm|third-party/spng | 1 | external-library | srb2|woof-family | 1 | libpng | |srb2+woof |


## 2. Predictor outputs

Predictions per predictor and variant (scored on eligible port pairs; unmapped = engine row without a func_id):

| predictor | variant | n_pred | n_unmapped |
|---|---|---|---|
| geometry | dedup | 23292 | 2600 |
| geometry | primary | 22683 | 2694 |
| names | dedup | 21483 | 992 |
| names | multikey | 8785 | 3180 |
| names | n2 | 20334 | 1176 |
| names | unique_key | 21038 | 972 |
| names | unique_key_vnk | 7864 | 551 |
| r1 | dedup | 23348 | 3440 |
| r1 | primary | 22739 | 3139 |
| structure | dedup | 9304 | 1023 |
| structure | premasked | 8004 | 962 |
| structure | primary | 8616 | 925 |
| structure | primary_vnk | 7680 | 873 |


## 3. Precision and recall (T1; sensitivities at Jaccard 0.6 and identifier-normalised; co-primary column adds T3 and the hand audit)

| predictor | variant | flavour | n_pred | tp | precision | n_classes | covered | recall | precision_t3audit | precision_06 | recall_06 | precision_idnorm | recall_idnorm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| geometry | dedup | all | 20692 | 389 | 0.019 | 7102 | 389 | 0.055 | 0.031 | 0.028 | 0.047 | 0.026 | 0.048 |
| geometry | primary | all | 19989 | 360 | 0.018 | 7102 | 378 | 0.053 | 0.031 | 0.027 | 0.046 | 0.026 | 0.048 |
| names | dedup | all | 20491 | 2142 | 0.105 | 7102 | 2142 | 0.302 | 0.185 | 0.161 | 0.270 | 0.122 | 0.221 |
| names | dedup | cert | 19724 | 2141 | 0.109 | 7102 | 2141 | 0.301 | 0.192 | 0.167 | 0.269 | 0.127 | 0.221 |
| names | multikey | all | 5605 | 136 | 0.024 | 7102 | 137 | 0.019 | 0.056 | 0.064 | 0.029 | 0.034 | 0.017 |
| names | multikey | cert | 4500 | 133 | 0.030 | 7102 | 134 | 0.019 | 0.069 | 0.078 | 0.029 | 0.042 | 0.017 |
| names | n2 | all | 19158 | 1923 | 0.100 | 7102 | 1929 | 0.272 | 0.174 | 0.155 | 0.244 | 0.117 | 0.199 |
| names | n2 | cert | 18236 | 1923 | 0.105 | 7102 | 1929 | 0.272 | 0.183 | 0.163 | 0.244 | 0.123 | 0.199 |
| names | unique_key | all | 20066 | 2074 | 0.103 | 7102 | 2083 | 0.293 | 0.186 | 0.158 | 0.261 | 0.120 | 0.214 |
| names | unique_key | cert | 19411 | 2074 | 0.107 | 7102 | 2083 | 0.293 | 0.192 | 0.163 | 0.261 | 0.124 | 0.214 |
| names | unique_key_vnk | all | 7313 | 2021 | 0.276 | 7102 | 2030 | 0.286 | 0.501 | 0.416 | 0.251 | 0.319 | 0.207 |
| names | unique_key_vnk | cert | 7103 | 2021 | 0.285 | 7102 | 2030 | 0.286 | 0.516 | 0.428 | 0.250 | 0.328 | 0.207 |
| r1 | dedup | all | 19908 | 3 | 0.000 | 7102 | 3 | 0.000 | 0.003 | 0.000 | 0.000 | 0.000 | 0.001 |
| r1 | primary | all | 19600 | 1 | 0.000 | 7102 | 1 | 0.000 | 0.003 | 0.000 | 0.000 | 0.000 | 0.000 |
| structure | dedup | all | 8281 | 1883 | 0.227 | 7102 | 1883 | 0.265 | 0.368 | 0.294 | 0.200 | 0.291 | 0.213 |
| structure | premasked | all | 7042 | 1783 | 0.253 | 7102 | 1818 | 0.256 | 0.419 | 0.327 | 0.194 | 0.327 | 0.208 |
| structure | primary | all | 7691 | 1826 | 0.237 | 7102 | 1849 | 0.260 | 0.390 | 0.306 | 0.197 | 0.306 | 0.211 |
| structure | primary_vnk | all | 6807 | 1791 | 0.263 | 7102 | 1814 | 0.255 | 0.435 | 0.339 | 0.193 | 0.338 | 0.206 |

Hand audit: 100 audited pairs used.


## 4. P1: structure minus names, micro-averaged precision (event-clustered 95% bootstrap over lineage pairs)

| spec | n_clusters | prec_s | prec_n | diff | lo | hi | p_one_sided | n_valid | variant | names_variant | names_flavour | truth | n_pred_struct | n_pred_names | excluded_module |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| co-primary truth, names certified | 155 | 0.390 | 0.192 | 0.198 | 0.119 | 0.265 | 0.000 | 2000 | primary | unique_key | cert | copri | 7691 | 19411 |  |
| co-primary truth, names certified | 155 | 0.368 | 0.192 | 0.176 | 0.100 | 0.243 | 0.000 | 2000 | dedup | dedup | cert | copri | 8281 | 19724 |  |
| T1 only, names certified | 155 | 0.237 | 0.107 | 0.131 | 0.069 | 0.177 | 0.000 | 2000 | primary | unique_key | cert | tp9 | 7691 | 19411 |  |
| T1 only, names certified | 155 | 0.227 | 0.109 | 0.119 | 0.060 | 0.163 | 0.000 | 2000 | dedup | dedup | cert | tp9 | 8281 | 19724 |  |
| co-primary truth, names raw | 163 | 0.390 | 0.186 | 0.204 | 0.123 | 0.267 | 0.000 | 2000 | primary | unique_key | all | copri | 7691 | 20066 |  |
| co-primary truth, names raw | 163 | 0.368 | 0.185 | 0.183 | 0.104 | 0.252 | 0.000 | 2000 | dedup | dedup | all | copri | 8281 | 20491 |  |
| leave textscreen out, co-primary truth, names certified | 153 | 0.230 | 0.091 | 0.139 | 0.067 | 0.200 | 0.000 | 2000 | primary | unique_key | cert | copri | 5819 | 17236 | textscreen |
| leave textscreen out, co-primary truth, names certified | 153 | 0.217 | 0.093 | 0.124 | 0.058 | 0.183 | 0.000 | 2000 | dedup | dedup | cert | copri | 6411 | 17565 | textscreen |

Structure higher (interval above 0 in both co-primary variants): **True**.

Leave-one-module-out (all modules):

| left_out | diff | lo | hi | n_struct | n_names |
|---|---|---|---|---|---|
| .|src/blua | 0.198 | 0.123 | 0.260 | 7633 | 19334 |
| FASTDOOM|prboom2/src | 0.198 | 0.126 | 0.286 | 7689 | 19405 |
| FASTDOOM|src | 0.198 | 0.121 | 0.267 | 7681 | 19390 |
| QW/client|client | 0.198 | 0.125 | 0.262 | 7684 | 19408 |
| QW/client|ctf | 0.198 | 0.118 | 0.267 | 7690 | 19411 |
| QW/client|irix | 0.198 | 0.128 | 0.263 | 7691 | 19411 |
| QW/client|linux | 0.198 | 0.116 | 0.274 | 7684 | 19410 |
| QW/client|qcommon | 0.197 | 0.112 | 0.254 | 7670 | 19399 |
| QW/client|ref_gl | 0.197 | 0.127 | 0.253 | 7685 | 19411 |
| QW/client|ref_soft | 0.197 | 0.124 | 0.250 | 7672 | 19411 |
| QW/client|server | 0.198 | 0.128 | 0.253 | 7690 | 19411 |
| QW/client|src | 0.198 | 0.118 | 0.264 | 7691 | 19411 |
| QW/client|win32 | 0.198 | 0.138 | 0.274 | 7685 | 19411 |
| QW/server|game | 0.198 | 0.118 | 0.265 | 7691 | 19410 |
| QW/server|ref_gl | 0.198 | 0.108 | 0.268 | 7691 | 19411 |
| QW/server|server | 0.198 | 0.109 | 0.261 | 7690 | 19406 |
| SDL2-2.32.10/include|libraries/sdl2/mingw/include/SDL2 | 0.198 | 0.132 | 0.253 | 7691 | 19411 |
| SDL2-2.32.10/include|libs/SDL2/i686-w64-mingw32/include/SDL2 | 0.198 | 0.112 | 0.258 | 7691 | 19411 |
| WinQuake|client | 0.198 | 0.098 | 0.271 | 7690 | 19410 |
| WinQuake|ctf | 0.198 | 0.128 | 0.259 | 7691 | 19411 |
| WinQuake|irix | 0.198 | 0.128 | 0.269 | 7691 | 19411 |
| WinQuake|linux | 0.198 | 0.126 | 0.271 | 7691 | 19411 |
| WinQuake|qcommon | 0.198 | 0.133 | 0.251 | 7689 | 19411 |
| WinQuake|ref_gl | 0.198 | 0.117 | 0.261 | 7690 | 19411 |
| WinQuake|win32 | 0.197 | 0.114 | 0.266 | 7685 | 19406 |
| cmake|prboom2/cmake | 0.198 | 0.114 | 0.269 | 7691 | 19411 |
| common|QW/client | 0.198 | 0.110 | 0.262 | 7691 | 19411 |
| common|linux | 0.198 | 0.112 | 0.259 | 7691 | 19411 |
| common|prboom2/src | 0.198 | 0.106 | 0.253 | 7691 | 19405 |
| common|src | 0.198 | 0.140 | 0.271 | 7691 | 19385 |
| ctf|src | 0.198 | 0.120 | 0.271 | 7691 | 19411 |
| doomclassic/doom|doomgeneric | 0.198 | 0.122 | 0.263 | 7691 | 19411 |
| doomclassic/doom|source | 0.198 | 0.134 | 0.262 | 7691 | 19411 |
| doomclassic/doom|src | 0.198 | 0.118 | 0.273 | 7691 | 19411 |
| doomclassic/timidity|libraries/ZMusic/thirdparty/timidityplus | 0.198 | 0.112 | 0.261 | 7691 | 19411 |
| doomgeneric|FASTDOOM | 0.198 | 0.118 | 0.255 | 7687 | 19401 |
| doomgeneric|common | 0.198 | 0.117 | 0.264 | 7691 | 19404 |
| doomgeneric|libraries/textscreen | 0.198 | 0.118 | 0.265 | 7691 | 19411 |
| doomgeneric|prboom2/src | 0.197 | 0.123 | 0.267 | 7670 | 19381 |
| doomgeneric|source | 0.198 | 0.129 | 0.249 | 7691 | 19411 |
| doomgeneric|src | 0.198 | 0.133 | 0.257 | 7660 | 19350 |
| doomgeneric|third-party/sha1 | 0.198 | 0.127 | 0.270 | 7691 | 19411 |
| doomsday/external/fluidsynth/src/drivers|libraries/ZMusic/thirdparty/fluidsynth/src/drivers | 0.198 | 0.125 | 0.257 | 7691 | 19411 |
| doomsday/external/fluidsynth/src/midi|libraries/ZMusic/thirdparty/fluidsynth/src/midi | 0.198 | 0.115 | 0.278 | 7691 | 19411 |
| doomsday/external/fluidsynth/src/rvoice|libraries/ZMusic/thirdparty/fluidsynth/src/rvoice | 0.198 | 0.113 | 0.259 | 7691 | 19411 |
| doomsday/external/fluidsynth/src/rvoice|libraries/fluidlite/src | 0.198 | 0.103 | 0.261 | 7691 | 19411 |
| doomsday/external/fluidsynth/src/sfloader|libraries/ZMusic/thirdparty/fluidsynth/src/sfloader | 0.198 | 0.109 | 0.261 | 7691 | 19411 |
| doomsday/external/fluidsynth/src/sfloader|libraries/fluidlite/src | 0.198 | 0.115 | 0.260 | 7691 | 19411 |
| doomsday/external/fluidsynth/src/synth|libraries/ZMusic/thirdparty/fluidsynth/src/synth | 0.198 | 0.129 | 0.262 | 7691 | 19411 |
| doomsday/external/fluidsynth/src/synth|libraries/fluidlite/src | 0.198 | 0.125 | 0.265 | 7691 | 19411 |
| doomsday/external/fluidsynth/src/utils|libraries/ZMusic/thirdparty/fluidsynth/src/utils | 0.198 | 0.116 | 0.271 | 7691 | 19411 |
| doomsday/external/fluidsynth/src/utils|libraries/fluidlite/src | 0.198 | 0.124 | 0.269 | 7691 | 19411 |
| doomsday/external/json/include/nlohmann/detail/conversions|libraries/cppdap/third_party/json/include/nlohmann/detail/conversions | 0.198 | 0.131 | 0.267 | 7691 | 19411 |
| doomsday/external/json/include/nlohmann/detail/conversions|source/nlohmann | 0.198 | 0.121 | 0.271 | 7691 | 19411 |
| doomsday/external/json/include/nlohmann/detail/input|libraries/cppdap/third_party/json/include/nlohmann/detail/input | 0.198 | 0.114 | 0.264 | 7691 | 19411 |
| doomsday/external/json/include/nlohmann/detail/input|source/nlohmann | 0.198 | 0.119 | 0.271 | 7691 | 19411 |
| doomsday/external/json/include/nlohmann/detail/iterators|libraries/cppdap/third_party/json/include/nlohmann/detail/iterators | 0.198 | 0.123 | 0.273 | 7691 | 19411 |
| doomsday/external/json/include/nlohmann/detail/iterators|source/nlohmann | 0.198 | 0.122 | 0.263 | 7691 | 19411 |
| doomsday/external/json/include/nlohmann/detail/output|libraries/cppdap/third_party/json/include/nlohmann/detail/output | 0.198 | 0.123 | 0.259 | 7691 | 19411 |
| doomsday/external/json/include/nlohmann/detail|libraries/cppdap/third_party/json/include/nlohmann/detail | 0.198 | 0.128 | 0.258 | 7691 | 19411 |
| doomsday/external/json/include/nlohmann|libraries/cppdap/third_party/json/include/nlohmann | 0.198 | 0.118 | 0.265 | 7691 | 19411 |
| doomsday/external/json/include/nlohmann|source/nlohmann | 0.198 | 0.121 | 0.263 | 7691 | 19411 |
| doomsday/external/stb|lib/stb_image_write | 0.199 | 0.128 | 0.262 | 7691 | 19373 |
| doomsday/external/stb|libraries/stb | 0.198 | 0.136 | 0.259 | 7691 | 19411 |
| doomsday/external/stb|src/common/thirdparty/stb | 0.198 | 0.125 | 0.277 | 7691 | 19411 |
| doomsday/libs/gui/src/text|libraries/stb | 0.198 | 0.120 | 0.265 | 7691 | 19411 |
| lib/miniz|third-party/miniz | 0.198 | 0.114 | 0.262 | 7691 | 19411 |
| lib/netlib|netlib | 0.197 | 0.127 | 0.269 | 7680 | 19399 |
| lib/opl|opl | 0.196 | 0.118 | 0.267 | 7645 | 19354 |
| lib/opl|prboom2/src/MUSIC | 0.198 | 0.125 | 0.256 | 7685 | 19403 |
| lib/spng|libs/libpng-src/arm | 0.198 | 0.134 | 0.257 | 7691 | 19411 |
| lib/spng|third-party/spng | 0.198 | 0.123 | 0.265 | 7691 | 19411 |
| lib/win32/SDL2-2.32.10/include|libs/SDL2/i686-w64-mingw32/include/SDL2 | 0.198 | 0.123 | 0.258 | 7691 | 19411 |
| libpng/arm|lib/spng | 0.198 | 0.122 | 0.266 | 7691 | 19411 |
| libpng/arm|libs/libpng-src/arm | 0.198 | 0.124 | 0.276 | 7691 | 19411 |
| libpng/contrib/arm-neon|libs/libpng-src/contrib/arm-neon | 0.198 | 0.141 | 0.268 | 7691 | 19411 |
| libpng/contrib/examples|libs/libpng-src/contrib/examples | 0.198 | 0.124 | 0.267 | 7691 | 19411 |
| libpng/contrib/gregbook|libs/libpng-src/contrib/gregbook | 0.198 | 0.127 | 0.279 | 7691 | 19411 |
| libpng/contrib/libtests|libs/libpng-src/contrib/libtests | 0.198 | 0.122 | 0.265 | 7691 | 19411 |
| libpng/contrib/oss-fuzz|libs/libpng-src/contrib/oss-fuzz | 0.198 | 0.128 | 0.271 | 7691 | 19411 |
| libpng/contrib/pngminus|libs/libpng-src/contrib/pngminus | 0.198 | 0.120 | 0.262 | 7691 | 19411 |
| libpng/contrib/powerpc-vsx|libs/libpng-src/contrib/powerpc-vsx | 0.198 | 0.124 | 0.266 | 7691 | 19411 |
| libpng/contrib/tools|libs/libpng-src/contrib/tools | 0.198 | 0.118 | 0.275 | 7691 | 19411 |
| libpng/contrib/visupng|libs/libpng-src/contrib/visupng | 0.198 | 0.137 | 0.266 | 7691 | 19411 |
| libpng/intel|libs/libpng-src/intel | 0.198 | 0.140 | 0.267 | 7691 | 19411 |
| libpng/mips|libs/libpng-src/mips | 0.198 | 0.107 | 0.264 | 7691 | 19411 |
| libpng/powerpc|libs/libpng-src/powerpc | 0.198 | 0.128 | 0.270 | 7691 | 19411 |
| libpng|libs/libpng-src | 0.198 | 0.133 | 0.269 | 7691 | 19411 |
| libraries/ZMusic/thirdparty/adlmidi/chips/dosbox|prboom2/src/MUSIC | 0.198 | 0.122 | 0.270 | 7691 | 19411 |
| libraries/ZMusic/thirdparty/adlmidi/chips/nuked|lib/opl | 0.198 | 0.124 | 0.260 | 7691 | 19411 |
| libraries/ZMusic/thirdparty/adlmidi/chips/nuked|opl | 0.198 | 0.131 | 0.264 | 7691 | 19411 |
| libraries/ZMusic/thirdparty/game-music-emu/gme|libs/gme/gme | 0.198 | 0.135 | 0.268 | 7691 | 19411 |
| libraries/ZMusic/thirdparty/miniz|lib/miniz | 0.198 | 0.131 | 0.265 | 7691 | 19411 |
| libraries/ZMusic/thirdparty/miniz|third-party/miniz | 0.198 | 0.129 | 0.269 | 7691 | 19411 |
| libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/sfloader | 0.198 | 0.109 | 0.269 | 7691 | 19411 |
| libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/synth | 0.198 | 0.129 | 0.256 | 7691 | 19411 |
| libraries/fluidlite/src|libraries/ZMusic/thirdparty/fluidsynth/src/utils | 0.198 | 0.104 | 0.265 | 7691 | 19411 |
| libraries/lua|. | 0.198 | 0.123 | 0.271 | 7691 | 19411 |
| libraries/lua|src/blua | 0.198 | 0.122 | 0.250 | 7691 | 19411 |
| libraries/minivorbis|libraries/ZMusic/thirdparty/dumb/src/helpers | 0.198 | 0.106 | 0.266 | 7691 | 19411 |
| libraries/miniz|lib/miniz | 0.198 | 0.131 | 0.260 | 7691 | 19411 |
| libraries/miniz|libraries/ZMusic/thirdparty/miniz | 0.198 | 0.112 | 0.255 | 7691 | 19411 |
| libraries/opalmidi|libraries/ZMusic/thirdparty/adlmidi/chips/opal/old | 0.198 | 0.132 | 0.253 | 7691 | 19411 |
| libraries/sdl2/mingw/include/SDL2|lib/win32/SDL2-2.32.10/include | 0.198 | 0.122 | 0.256 | 7691 | 19411 |
| libraries/sdl2/mingw/include/SDL2|libs/SDL2/i686-w64-mingw32/include/SDL2 | 0.198 | 0.114 | 0.255 | 7691 | 19411 |
| libraries/stb|src/common/thirdparty/stb | 0.198 | 0.103 | 0.270 | 7691 | 19411 |
| libraries/textscreen | 0.193 | 0.114 | 0.262 | 7524 | 19188 |
| libraries/textscreen/examples | 0.197 | 0.133 | 0.256 | 7677 | 19402 |
| libraries/textscreen|src | 0.198 | 0.121 | 0.260 | 7691 | 19411 |
| libs/libpng-src/arm|third-party/spng | 0.198 | 0.125 | 0.274 | 7691 | 19411 |
| man|man | 0.197 | 0.118 | 0.264 | 7682 | 19406 |
| master|QW/client | 0.198 | 0.122 | 0.265 | 7691 | 19411 |
| opl | 0.198 | 0.126 | 0.263 | 7621 | 19329 |
| opl|libraries/ZMusic/thirdparty/adlmidi/chips/nuked | 0.198 | 0.129 | 0.270 | 7691 | 19411 |
| opl|opl | 0.198 | 0.115 | 0.261 | 7676 | 19384 |
| opl|prboom2/src/MUSIC | 0.196 | 0.126 | 0.265 | 7633 | 19341 |
| pcsound|prboom2/src/PCSOUND | 0.198 | 0.108 | 0.274 | 7684 | 19401 |
| prboom2/src/MUSIC|lib/opl | 0.196 | 0.109 | 0.269 | 7653 | 19369 |
| prboom2/src/MUSIC|libraries/ZMusic/thirdparty/adlmidi/chips/nuked | 0.198 | 0.124 | 0.257 | 7691 | 19411 |
| prboom2/src/MUSIC|src | 0.197 | 0.123 | 0.284 | 7678 | 19387 |
| prboom2/src/TEXTSCREEN | 0.198 | 0.115 | 0.265 | 7683 | 19399 |
| prboom2/src/WIN|src | 0.198 | 0.116 | 0.264 | 7690 | 19411 |
| prboom2/src/dsda|src/gamedata | 0.198 | 0.118 | 0.250 | 7691 | 19410 |
| prboom2/src/textscreen | 0.198 | 0.130 | 0.265 | 7687 | 19405 |
| prboom2/src|common | 0.198 | 0.127 | 0.262 | 7691 | 19383 |
| prboom2/src|src | 0.197 | 0.118 | 0.257 | 7668 | 19379 |
| prboom2/src|src/hardware | 0.197 | 0.131 | 0.262 | 7683 | 19401 |
| snes_spc|libraries/ZMusic/thirdparty/game-music-emu/gme | 0.198 | 0.115 | 0.257 | 7691 | 19411 |
| snes_spc|libs/gme/gme | 0.198 | 0.111 | 0.259 | 7691 | 19411 |
| source/Win32|client/sdl | 0.198 | 0.120 | 0.253 | 7689 | 19409 |
| source/Win32|src | 0.198 | 0.116 | 0.259 | 7690 | 19387 |
| source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann | 0.198 | 0.102 | 0.262 | 7691 | 19411 |
| source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail | 0.198 | 0.124 | 0.265 | 7691 | 19411 |
| source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/conversions | 0.198 | 0.135 | 0.262 | 7691 | 19411 |
| source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/input | 0.198 | 0.119 | 0.268 | 7691 | 19411 |
| source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/iterators | 0.198 | 0.118 | 0.263 | 7691 | 19411 |
| source/nlohmann|libraries/cppdap/third_party/json/include/nlohmann/detail/output | 0.198 | 0.128 | 0.261 | 7691 | 19411 |
| source/textscreen | 0.192 | 0.119 | 0.258 | 7498 | 19168 |
| source_files/edge/script/compat|. | 0.198 | 0.124 | 0.271 | 7691 | 19411 |
| source|common | 0.198 | 0.123 | 0.264 | 7689 | 19400 |
| source|src | 0.198 | 0.112 | 0.276 | 7691 | 19411 |
| src/common/thirdparty/stb|lib/stb_image_write | 0.198 | 0.122 | 0.269 | 7691 | 19411 |
| src/doom|FASTDOOM | 0.198 | 0.130 | 0.269 | 7691 | 19403 |
| src/doom|prboom2/src | 0.197 | 0.115 | 0.268 | 7653 | 19368 |
| src/doom|src | 0.198 | 0.134 | 0.282 | 7633 | 19309 |
| src/miniz|libraries/ZMusic/thirdparty/miniz | 0.198 | 0.126 | 0.270 | 7691 | 19411 |
| src/miniz|libraries/miniz | 0.198 | 0.118 | 0.275 | 7691 | 19411 |
| src/miniz|third-party/miniz | 0.198 | 0.121 | 0.266 | 7691 | 19411 |
| src/nano_bsp|src | 0.198 | 0.105 | 0.263 | 7691 | 19393 |
| src/netgame|setup | 0.197 | 0.128 | 0.275 | 7657 | 19378 |
| src/setup|setup | 0.197 | 0.122 | 0.272 | 7656 | 19377 |
| src/yyjson|third-party/yyjson | 0.198 | 0.113 | 0.268 | 7691 | 19411 |
| src|FASTDOOM | 0.198 | 0.126 | 0.268 | 7684 | 19395 |
| src|client/sdl | 0.198 | 0.123 | 0.275 | 7691 | 19405 |
| src|common | 0.198 | 0.122 | 0.270 | 7691 | 19376 |
| src|doomclassic/doom | 0.198 | 0.126 | 0.263 | 7691 | 19411 |
| src|libraries/textscreen | 0.198 | 0.102 | 0.264 | 7691 | 19411 |
| src|libraries/textscreen/examples | 0.198 | 0.120 | 0.275 | 7691 | 19411 |
| src|prboom2/src | 0.195 | 0.121 | 0.256 | 7603 | 19292 |
| src|prboom2/src/MUSIC | 0.197 | 0.128 | 0.253 | 7637 | 19316 |
| src|source | 0.198 | 0.130 | 0.262 | 7691 | 19411 |
| src|source/Win32 | 0.198 | 0.117 | 0.278 | 7690 | 19387 |
| src|source/textscreen | 0.198 | 0.118 | 0.254 | 7689 | 19411 |
| src|src | 0.205 | 0.112 | 0.287 | 6927 | 18661 |
| src|textscreen | 0.198 | 0.130 | 0.263 | 7691 | 19411 |
| src|third-party/sha1 | 0.198 | 0.124 | 0.257 | 7691 | 19411 |
| textscreen | 0.139 | 0.069 | 0.203 | 5819 | 17236 |
| xcode/SDL2_image.framework/Versions/A/Frameworks/webp.framework/Headers/webp|libraries/webp/include/webp | 0.198 | 0.114 | 0.262 | 7691 | 19411 |
| zlib|libs/zlib | 0.198 | 0.131 | 0.267 | 7691 | 19411 |
| zlib|libs/zlib/test | 0.198 | 0.126 | 0.272 | 7691 | 19411 |


## 5. Negative controls and P2 (false positives per 1,000 eligible functions, exact one-sided 95% upper bound)

Hard negatives (nginx, leveldb) carry P2; soft negatives (helion, room4doom, rust-doom) are reported separately; quake, quake2, lua are descriptive (lua also appears in srb2 as a known vendoring positive: confirmed pairs are listed in n_confirmed_functions).

| variant | names_variant | fp_struct | upper_struct | fp_names | upper_names | n_eligible | struct_only | names_only | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|
| primary | unique_key | 60 | 17.881 | 0 | 0.721 | 4153 | 60 | 0 | 1.000 |
| dedup | dedup | 60 | 18.068 | 0 | 0.729 | 4110 | 60 | 0 | 1.000 |

| stratum | predictor | variant | flavour | programs | n_raw_pairs | n_confirmed_functions | fp | n_eligible | rate_per_1000 | upper95_per_1000 |
|---|---|---|---|---|---|---|---|---|---|---|
| hard | geometry | dedup | all | nginx,leveldb | 296 | 0 | 201 | 4110 | 48.905 | 54.803 |
| soft | geometry | dedup | all | helion,room4doom,rust-doom | 1792 | 0 | 1048 | 6221 | 168.462 | 176.462 |
| descriptive | geometry | dedup | all | quake,quake2,lua | 1017 | 3 | 785 | 5714 | 137.382 | 145.097 |
| hard | geometry | primary | all | nginx,leveldb | 296 | 0 | 190 | 4153 | 45.750 | 51.446 |
| soft | geometry | primary | all | helion,room4doom,rust-doom | 1771 | 0 | 1018 | 6338 | 160.618 | 168.399 |
| descriptive | geometry | primary | all | quake,quake2,lua | 878 | 2 | 707 | 7254 | 97.463 | 103.381 |
| hard | names | dedup | all | nginx,leveldb | 0 | 0 | 0 | 4110 | 0.000 | 0.729 |
| soft | names | dedup | all | helion,room4doom,rust-doom | 1640 | 0 | 443 | 6221 | 71.210 | 76.805 |
| descriptive | names | dedup | all | quake,quake2,lua | 500 | 27 | 361 | 5714 | 63.178 | 68.727 |
| hard | names | dedup | cert | nginx,leveldb | 0 | 0 | 0 | 4110 | 0.000 | 0.729 |
| soft | names | dedup | cert | helion,room4doom,rust-doom | 1020 | 0 | 346 | 6221 | 55.618 | 60.635 |
| descriptive | names | dedup | cert | quake,quake2,lua | 270 | 26 | 244 | 5714 | 42.702 | 47.366 |
| hard | names | multikey | all | nginx,leveldb | 3 | 0 | 3 | 4153 | 0.722 | 1.866 |
| soft | names | multikey | all | helion,room4doom,rust-doom | 796 | 0 | 285 | 6338 | 44.967 | 49.485 |
| descriptive | names | multikey | all | quake,quake2,lua | 918 | 3 | 324 | 7254 | 44.665 | 48.861 |
| hard | names | multikey | cert | nginx,leveldb | 0 | 0 | 0 | 4153 | 0.000 | 0.721 |
| soft | names | multikey | cert | helion,room4doom,rust-doom | 381 | 0 | 170 | 6338 | 26.822 | 30.405 |
| descriptive | names | multikey | cert | quake,quake2,lua | 4 | 0 | 4 | 7254 | 0.551 | 1.261 |
| hard | names | n2 | all | nginx,leveldb | 1 | 0 | 1 | 4153 | 0.241 | 1.142 |
| soft | names | n2 | all | helion,room4doom,rust-doom | 2653 | 0 | 515 | 6338 | 81.256 | 87.124 |
| descriptive | names | n2 | all | quake,quake2,lua | 439 | 26 | 318 | 7254 | 43.838 | 47.999 |
| hard | names | n2 | cert | nginx,leveldb | 0 | 0 | 0 | 4153 | 0.000 | 0.721 |
| soft | names | n2 | cert | helion,room4doom,rust-doom | 1786 | 0 | 441 | 6338 | 69.580 | 75.064 |
| descriptive | names | n2 | cert | quake,quake2,lua | 269 | 26 | 243 | 7254 | 33.499 | 37.185 |
| hard | names | unique_key | all | nginx,leveldb | 0 | 0 | 0 | 4153 | 0.000 | 0.721 |
| soft | names | unique_key | all | helion,room4doom,rust-doom | 1617 | 0 | 443 | 6338 | 69.896 | 75.391 |
| descriptive | names | unique_key | all | quake,quake2,lua | 409 | 26 | 312 | 7254 | 43.011 | 47.136 |
| hard | names | unique_key | cert | nginx,leveldb | 0 | 0 | 0 | 4153 | 0.000 | 0.721 |
| soft | names | unique_key | cert | helion,room4doom,rust-doom | 1145 | 0 | 375 | 6338 | 59.167 | 64.273 |
| descriptive | names | unique_key | cert | quake,quake2,lua | 270 | 26 | 244 | 7254 | 33.637 | 37.329 |
| hard | names | unique_key_vnk | all | nginx,leveldb | 0 | 0 | 0 | 4153 | 0.000 | 0.721 |
| soft | names | unique_key_vnk | all | helion,room4doom,rust-doom | 740 | 0 | 385 | 6338 | 60.745 | 65.910 |
| descriptive | names | unique_key_vnk | all | quake,quake2,lua | 333 | 26 | 299 | 7254 | 41.219 | 45.266 |
| hard | names | unique_key_vnk | cert | nginx,leveldb | 0 | 0 | 0 | 4153 | 0.000 | 0.721 |
| soft | names | unique_key_vnk | cert | helion,room4doom,rust-doom | 591 | 0 | 317 | 6338 | 50.016 | 54.754 |
| descriptive | names | unique_key_vnk | cert | quake,quake2,lua | 270 | 26 | 244 | 7254 | 33.637 | 37.329 |
| hard | r1 | dedup | all | nginx,leveldb | 296 | 0 | 274 | 4110 | 66.667 | 73.420 |
| soft | r1 | dedup | all | helion,room4doom,rust-doom | 1792 | 0 | 1615 | 6221 | 259.605 | 268.910 |
| descriptive | r1 | dedup | all | quake,quake2,lua | 1017 | 0 | 957 | 5714 | 167.483 | 175.821 |
| hard | r1 | primary | all | nginx,leveldb | 296 | 0 | 279 | 4153 | 67.180 | 73.919 |
| soft | r1 | primary | all | helion,room4doom,rust-doom | 1771 | 0 | 1595 | 6338 | 251.657 | 260.785 |
| descriptive | r1 | primary | all | quake,quake2,lua | 878 | 0 | 829 | 7254 | 114.282 | 120.610 |
| hard | structure | dedup | all | nginx,leveldb | 100 | 0 | 60 | 4110 | 14.599 | 18.068 |
| soft | structure | dedup | all | helion,room4doom,rust-doom | 286 | 0 | 203 | 6221 | 32.631 | 36.583 |
| descriptive | structure | dedup | all | quake,quake2,lua | 658 | 27 | 430 | 5714 | 75.254 | 81.244 |
| hard | structure | premasked | all | nginx,leveldb | 101 | 0 | 60 | 4153 | 14.447 | 17.881 |
| soft | structure | premasked | all | helion,room4doom,rust-doom | 293 | 0 | 204 | 6338 | 32.187 | 36.076 |
| descriptive | structure | premasked | all | quake,quake2,lua | 466 | 26 | 273 | 7254 | 37.634 | 41.519 |
| hard | structure | primary | all | nginx,leveldb | 100 | 0 | 60 | 4153 | 14.447 | 17.881 |
| soft | structure | primary | all | helion,room4doom,rust-doom | 286 | 0 | 203 | 6338 | 32.029 | 35.909 |
| descriptive | structure | primary | all | quake,quake2,lua | 550 | 26 | 369 | 7254 | 50.868 | 55.317 |
| hard | structure | primary_vnk | all | nginx,leveldb | 98 | 0 | 59 | 4153 | 14.207 | 17.616 |
| soft | structure | primary_vnk | all | helion,room4doom,rust-doom | 263 | 0 | 189 | 6338 | 29.820 | 33.578 |
| descriptive | structure | primary_vnk | all | quake,quake2,lua | 478 | 26 | 329 | 7254 | 45.354 | 49.579 |


## 6. Spike-in recall by disguise tier and size (deterministic checks; names versus structure under renaming is DESCRIPTIVE)

Registered check, structure recall >= 0.80 under tier (c) at both sizes: **not met** (size large: 0.494 [0.414, 0.573] (80/162); size small: 0.638 [0.539, 0.730] (67/105)).

| predictor | variant | flavour | tier | module_size | hits | n | recall | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|---|---|
| geometry | dedup | all | a | large | 62 | 162 | 0.383 | 0.308 | 0.462 |
| geometry | dedup | all | b50 | large | 62 | 162 | 0.383 | 0.308 | 0.462 |
| geometry | dedup | all | b100 | large | 62 | 162 | 0.383 | 0.308 | 0.462 |
| geometry | dedup | all | c | large | 10 | 162 | 0.062 | 0.030 | 0.111 |
| geometry | dedup | all | d | large | 11 | 162 | 0.068 | 0.034 | 0.118 |
| geometry | dedup | all | e | large | 0 | 52 | 0.000 | 0.000 | 0.068 |
| geometry | dedup | all | a | small | 42 | 105 | 0.400 | 0.306 | 0.500 |
| geometry | dedup | all | b50 | small | 42 | 105 | 0.400 | 0.306 | 0.500 |
| geometry | dedup | all | b100 | small | 42 | 105 | 0.400 | 0.306 | 0.500 |
| geometry | dedup | all | c | small | 3 | 105 | 0.029 | 0.006 | 0.081 |
| geometry | dedup | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| geometry | dedup | all | e | small | 2 | 29 | 0.069 | 0.008 | 0.228 |
| geometry | primary | all | a | large | 64 | 162 | 0.395 | 0.319 | 0.475 |
| geometry | primary | all | b50 | large | 64 | 162 | 0.395 | 0.319 | 0.475 |
| geometry | primary | all | b100 | large | 64 | 162 | 0.395 | 0.319 | 0.475 |
| geometry | primary | all | c | large | 10 | 162 | 0.062 | 0.030 | 0.111 |
| geometry | primary | all | d | large | 12 | 162 | 0.074 | 0.039 | 0.126 |
| geometry | primary | all | e | large | 0 | 52 | 0.000 | 0.000 | 0.068 |
| geometry | primary | all | a | small | 40 | 105 | 0.381 | 0.288 | 0.481 |
| geometry | primary | all | b50 | small | 40 | 105 | 0.381 | 0.288 | 0.481 |
| geometry | primary | all | b100 | small | 40 | 105 | 0.381 | 0.288 | 0.481 |
| geometry | primary | all | c | small | 4 | 105 | 0.038 | 0.010 | 0.095 |
| geometry | primary | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| geometry | primary | all | e | small | 2 | 29 | 0.069 | 0.008 | 0.228 |
| names | dedup | all | a | large | 156 | 162 | 0.963 | 0.921 | 0.986 |
| names | dedup | all | b50 | large | 83 | 162 | 0.512 | 0.433 | 0.592 |
| names | dedup | all | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | dedup | all | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | dedup | all | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | dedup | all | e | large | 49 | 52 | 0.942 | 0.841 | 0.988 |
| names | dedup | all | a | small | 41 | 105 | 0.390 | 0.297 | 0.491 |
| names | dedup | all | b50 | small | 16 | 105 | 0.152 | 0.090 | 0.236 |
| names | dedup | all | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | dedup | all | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | dedup | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | dedup | all | e | small | 12 | 29 | 0.414 | 0.235 | 0.611 |
| names | dedup | cert | a | large | 156 | 162 | 0.963 | 0.921 | 0.986 |
| names | dedup | cert | b50 | large | 83 | 162 | 0.512 | 0.433 | 0.592 |
| names | dedup | cert | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | dedup | cert | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | dedup | cert | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | dedup | cert | e | large | 49 | 52 | 0.942 | 0.841 | 0.988 |
| names | dedup | cert | a | small | 41 | 105 | 0.390 | 0.297 | 0.491 |
| names | dedup | cert | b50 | small | 16 | 105 | 0.152 | 0.090 | 0.236 |
| names | dedup | cert | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | dedup | cert | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | dedup | cert | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | dedup | cert | e | small | 12 | 29 | 0.414 | 0.235 | 0.611 |
| names | multikey | all | a | large | 5 | 162 | 0.031 | 0.010 | 0.071 |
| names | multikey | all | b50 | large | 3 | 162 | 0.019 | 0.004 | 0.053 |
| names | multikey | all | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | multikey | all | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | multikey | all | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | multikey | all | e | large | 2 | 52 | 0.038 | 0.005 | 0.132 |
| names | multikey | all | a | small | 63 | 105 | 0.600 | 0.500 | 0.694 |
| names | multikey | all | b50 | small | 36 | 105 | 0.343 | 0.253 | 0.442 |
| names | multikey | all | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | multikey | all | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | multikey | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | multikey | all | e | small | 17 | 29 | 0.586 | 0.389 | 0.765 |
| names | multikey | cert | a | large | 5 | 162 | 0.031 | 0.010 | 0.071 |
| names | multikey | cert | b50 | large | 3 | 162 | 0.019 | 0.004 | 0.053 |
| names | multikey | cert | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | multikey | cert | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | multikey | cert | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | multikey | cert | e | large | 2 | 52 | 0.038 | 0.005 | 0.132 |
| names | multikey | cert | a | small | 63 | 105 | 0.600 | 0.500 | 0.694 |
| names | multikey | cert | b50 | small | 36 | 105 | 0.343 | 0.253 | 0.442 |
| names | multikey | cert | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | multikey | cert | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | multikey | cert | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | multikey | cert | e | small | 17 | 29 | 0.586 | 0.389 | 0.765 |
| names | n2 | all | a | large | 156 | 162 | 0.963 | 0.921 | 0.986 |
| names | n2 | all | b50 | large | 83 | 162 | 0.512 | 0.433 | 0.592 |
| names | n2 | all | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | n2 | all | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | n2 | all | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | n2 | all | e | large | 49 | 52 | 0.942 | 0.841 | 0.988 |
| names | n2 | all | a | small | 41 | 105 | 0.390 | 0.297 | 0.491 |
| names | n2 | all | b50 | small | 16 | 105 | 0.152 | 0.090 | 0.236 |
| names | n2 | all | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | n2 | all | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | n2 | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | n2 | all | e | small | 12 | 29 | 0.414 | 0.235 | 0.611 |
| names | n2 | cert | a | large | 156 | 162 | 0.963 | 0.921 | 0.986 |
| names | n2 | cert | b50 | large | 83 | 162 | 0.512 | 0.433 | 0.592 |
| names | n2 | cert | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | n2 | cert | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | n2 | cert | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | n2 | cert | e | large | 49 | 52 | 0.942 | 0.841 | 0.988 |
| names | n2 | cert | a | small | 41 | 105 | 0.390 | 0.297 | 0.491 |
| names | n2 | cert | b50 | small | 16 | 105 | 0.152 | 0.090 | 0.236 |
| names | n2 | cert | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | n2 | cert | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | n2 | cert | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | n2 | cert | e | small | 12 | 29 | 0.414 | 0.235 | 0.611 |
| names | unique_key | all | a | large | 156 | 162 | 0.963 | 0.921 | 0.986 |
| names | unique_key | all | b50 | large | 83 | 162 | 0.512 | 0.433 | 0.592 |
| names | unique_key | all | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key | all | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key | all | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key | all | e | large | 49 | 52 | 0.942 | 0.841 | 0.988 |
| names | unique_key | all | a | small | 41 | 105 | 0.390 | 0.297 | 0.491 |
| names | unique_key | all | b50 | small | 16 | 105 | 0.152 | 0.090 | 0.236 |
| names | unique_key | all | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key | all | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key | all | e | small | 12 | 29 | 0.414 | 0.235 | 0.611 |
| names | unique_key | cert | a | large | 156 | 162 | 0.963 | 0.921 | 0.986 |
| names | unique_key | cert | b50 | large | 83 | 162 | 0.512 | 0.433 | 0.592 |
| names | unique_key | cert | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key | cert | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key | cert | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key | cert | e | large | 49 | 52 | 0.942 | 0.841 | 0.988 |
| names | unique_key | cert | a | small | 41 | 105 | 0.390 | 0.297 | 0.491 |
| names | unique_key | cert | b50 | small | 16 | 105 | 0.152 | 0.090 | 0.236 |
| names | unique_key | cert | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key | cert | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key | cert | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key | cert | e | small | 12 | 29 | 0.414 | 0.235 | 0.611 |
| names | unique_key_vnk | all | a | large | 156 | 162 | 0.963 | 0.921 | 0.986 |
| names | unique_key_vnk | all | b50 | large | 83 | 162 | 0.512 | 0.433 | 0.592 |
| names | unique_key_vnk | all | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key_vnk | all | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key_vnk | all | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key_vnk | all | e | large | 49 | 52 | 0.942 | 0.841 | 0.988 |
| names | unique_key_vnk | all | a | small | 41 | 105 | 0.390 | 0.297 | 0.491 |
| names | unique_key_vnk | all | b50 | small | 16 | 105 | 0.152 | 0.090 | 0.236 |
| names | unique_key_vnk | all | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key_vnk | all | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key_vnk | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key_vnk | all | e | small | 12 | 29 | 0.414 | 0.235 | 0.611 |
| names | unique_key_vnk | cert | a | large | 156 | 162 | 0.963 | 0.921 | 0.986 |
| names | unique_key_vnk | cert | b50 | large | 83 | 162 | 0.512 | 0.433 | 0.592 |
| names | unique_key_vnk | cert | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key_vnk | cert | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key_vnk | cert | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| names | unique_key_vnk | cert | e | large | 49 | 52 | 0.942 | 0.841 | 0.988 |
| names | unique_key_vnk | cert | a | small | 41 | 105 | 0.390 | 0.297 | 0.491 |
| names | unique_key_vnk | cert | b50 | small | 16 | 105 | 0.152 | 0.090 | 0.236 |
| names | unique_key_vnk | cert | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key_vnk | cert | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key_vnk | cert | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| names | unique_key_vnk | cert | e | small | 12 | 29 | 0.414 | 0.235 | 0.611 |
| r1 | dedup | all | a | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| r1 | dedup | all | b50 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| r1 | dedup | all | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| r1 | dedup | all | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| r1 | dedup | all | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| r1 | dedup | all | e | large | 0 | 52 | 0.000 | 0.000 | 0.068 |
| r1 | dedup | all | a | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| r1 | dedup | all | b50 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| r1 | dedup | all | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| r1 | dedup | all | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| r1 | dedup | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| r1 | dedup | all | e | small | 0 | 29 | 0.000 | 0.000 | 0.119 |
| r1 | primary | all | a | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| r1 | primary | all | b50 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| r1 | primary | all | b100 | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| r1 | primary | all | c | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| r1 | primary | all | d | large | 0 | 162 | 0.000 | 0.000 | 0.023 |
| r1 | primary | all | e | large | 0 | 52 | 0.000 | 0.000 | 0.068 |
| r1 | primary | all | a | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| r1 | primary | all | b50 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| r1 | primary | all | b100 | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| r1 | primary | all | c | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| r1 | primary | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| r1 | primary | all | e | small | 0 | 29 | 0.000 | 0.000 | 0.119 |
| structure | dedup | all | a | large | 153 | 162 | 0.944 | 0.897 | 0.974 |
| structure | dedup | all | b50 | large | 153 | 162 | 0.944 | 0.897 | 0.974 |
| structure | dedup | all | b100 | large | 153 | 162 | 0.944 | 0.897 | 0.974 |
| structure | dedup | all | c | large | 72 | 162 | 0.444 | 0.366 | 0.524 |
| structure | dedup | all | d | large | 70 | 162 | 0.432 | 0.355 | 0.512 |
| structure | dedup | all | e | large | 48 | 52 | 0.923 | 0.815 | 0.979 |
| structure | dedup | all | a | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | dedup | all | b50 | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | dedup | all | b100 | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | dedup | all | c | small | 66 | 105 | 0.629 | 0.529 | 0.721 |
| structure | dedup | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| structure | dedup | all | e | small | 25 | 29 | 0.862 | 0.683 | 0.961 |
| structure | premasked | all | a | large | 154 | 162 | 0.951 | 0.905 | 0.978 |
| structure | premasked | all | b50 | large | 154 | 162 | 0.951 | 0.905 | 0.978 |
| structure | premasked | all | b100 | large | 154 | 162 | 0.951 | 0.905 | 0.978 |
| structure | premasked | all | c | large | 80 | 162 | 0.494 | 0.414 | 0.573 |
| structure | premasked | all | d | large | 70 | 162 | 0.432 | 0.355 | 0.512 |
| structure | premasked | all | e | large | 47 | 52 | 0.904 | 0.790 | 0.968 |
| structure | premasked | all | a | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | premasked | all | b50 | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | premasked | all | b100 | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | premasked | all | c | small | 67 | 105 | 0.638 | 0.539 | 0.730 |
| structure | premasked | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| structure | premasked | all | e | small | 25 | 29 | 0.862 | 0.683 | 0.961 |
| structure | primary | all | a | large | 154 | 162 | 0.951 | 0.905 | 0.978 |
| structure | primary | all | b50 | large | 154 | 162 | 0.951 | 0.905 | 0.978 |
| structure | primary | all | b100 | large | 154 | 162 | 0.951 | 0.905 | 0.978 |
| structure | primary | all | c | large | 80 | 162 | 0.494 | 0.414 | 0.573 |
| structure | primary | all | d | large | 70 | 162 | 0.432 | 0.355 | 0.512 |
| structure | primary | all | e | large | 47 | 52 | 0.904 | 0.790 | 0.968 |
| structure | primary | all | a | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | primary | all | b50 | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | primary | all | b100 | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | primary | all | c | small | 67 | 105 | 0.638 | 0.539 | 0.730 |
| structure | primary | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| structure | primary | all | e | small | 25 | 29 | 0.862 | 0.683 | 0.961 |
| structure | primary_vnk | all | a | large | 154 | 162 | 0.951 | 0.905 | 0.978 |
| structure | primary_vnk | all | b50 | large | 154 | 162 | 0.951 | 0.905 | 0.978 |
| structure | primary_vnk | all | b100 | large | 154 | 162 | 0.951 | 0.905 | 0.978 |
| structure | primary_vnk | all | c | large | 80 | 162 | 0.494 | 0.414 | 0.573 |
| structure | primary_vnk | all | d | large | 70 | 162 | 0.432 | 0.355 | 0.512 |
| structure | primary_vnk | all | e | large | 47 | 52 | 0.904 | 0.790 | 0.968 |
| structure | primary_vnk | all | a | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | primary_vnk | all | b50 | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | primary_vnk | all | b100 | small | 101 | 105 | 0.962 | 0.905 | 0.990 |
| structure | primary_vnk | all | c | small | 67 | 105 | 0.638 | 0.539 | 0.730 |
| structure | primary_vnk | all | d | small | 0 | 105 | 0.000 | 0.000 | 0.035 |
| structure | primary_vnk | all | e | small | 25 | 29 | 0.862 | 0.683 | 0.961 |


## 7. Time checks (supporting evidence, a falsifier not a validator)

Order excess (committer date): donor-first share 0.972, same-pair baseline 0.815, excess **0.157** [-0.003, 0.343] over 711 dated function pairs in 5 port pairs (author-date sensitivity: 0.157).

| donor | recipient | lineage | n_dated | n_censored_excluded | donor_first | share | baseline | excess | n_baseline_donor | n_baseline_recipient |
|---|---|---|---|---|---|---|---|---|---|---|
| chocolate-doom | dsda-doom | chocolate|prboom | 4 | 0 | 4 | 1.000 | 0.787 | 0.213 | 1496 | 2055 |
| chocolate-doom | eternity | chocolate|eternity | 224 | 0 | 223 | 0.996 | 0.658 | 0.337 | 1329 | 2098 |
| chocolate-doom | odamex | chocolate|odamex | 208 | 0 | 202 | 0.971 | 0.794 | 0.178 | 1349 | 2024 |
| chocolate-doom | prboom-plus | chocolate|prboom | 8 | 0 | 7 | 0.875 | 0.307 | 0.568 | 1511 | 1874 |
| chocolate-doom | woof | chocolate|woof | 267 | 0 | 255 | 0.955 | 0.978 | -0.023 | 1159 | 2653 |

Import cluster (share within 14 days of the median): confirmed 0.544, unconfirmed 0.280, within-borrower permuted 0.065, native same-directory control 0.421; excess over permuted **0.479** [0.410, 0.569] (author-date sensitivity 0.478). perm_null.npz keys: keys, n_draws, chocolate-doom|doom3-bfg|j06|chocolate-doom|matched, chocolate-doom|doom3-bfg|j06|chocolate-doom|draws, chocolate-doom|doom3-bfg|j06|doom3-bfg|matched, chocolate-doom|doom3-bfg|j06|doom3-bfg|draws, chocolate-doom|doom3-bfg|t1|chocolate-doom|matched, chocolate-doom|doom3-bfg|t1|chocolate-doom|draws, chocolate-doom|doom3-bfg|t1|doom3-bfg|matched, chocolate-doom|doom3-bfg|t1|doom3-bfg|draws, chocolate-doom|dsda-doom|j06|chocolate-doom|matched, chocolate-doom|dsda-doom|j06|chocolate-doom|draws, chocolate-doom|dsda-doom|j06|dsda-doom|matched, chocolate-doom|dsda-doom|j06|dsda-doom|draws, chocolate-doom|dsda-doom|t1|chocolate-doom|matched, chocolate-doom|dsda-doom|t1|chocolate-doom|draws, chocolate-doom|dsda-doom|t1|dsda-doom|matched, chocolate-doom|dsda-doom|t1|dsda-doom|draws, chocolate-doom|eternity|j06|chocolate-doom|matched, chocolate-doom|eternity|j06|chocolate-doom|draws, chocolate-doom|eternity|j06|eternity|matched, chocolate-doom|eternity|j06|eternity|draws, chocolate-doom|eternity|t1|chocolate-doom|matched, chocolate-doom|eternity|t1|chocolate-doom|draws, chocolate-doom|eternity|t1|eternity|matched, chocolate-doom|eternity|t1|eternity|draws, chocolate-doom|fastdoom|j06|chocolate-doom|matched, chocolate-doom|fastdoom|j06|chocolate-doom|draws, chocolate-doom|fastdoom|j06|fastdoom|matched, chocolate-doom|fastdoom|j06|fastdoom|draws, chocolate-doom|fastdoom|t1|chocolate-doom|matched, chocolate-doom|fastdoom|t1|chocolate-doom|draws, chocolate-doom|fastdoom|t1|fastdoom|matched, chocolate-doom|fastdoom|t1|fastdoom|draws, chocolate-doom|gzdoom|j06|chocolate-doom|matched, chocolate-doom|gzdoom|j06|chocolate-doom|draws, chocolate-doom|gzdoom|j06|gzdoom|matched, chocolate-doom|gzdoom|j06|gzdoom|draws, chocolate-doom|gzdoom|t1|chocolate-doom|matched, chocolate-doom|gzdoom|t1|chocolate-doom|draws, chocolate-doom|gzdoom|t1|gzdoom|matched, chocolate-doom|gzdoom|t1|gzdoom|draws, chocolate-doom|nugget-doom|j06|chocolate-doom|matched, chocolate-doom|nugget-doom|j06|chocolate-doom|draws, chocolate-doom|nugget-doom|j06|nugget-doom|matched, chocolate-doom|nugget-doom|j06|nugget-doom|draws, chocolate-doom|nugget-doom|t1|chocolate-doom|matched, chocolate-doom|nugget-doom|t1|chocolate-doom|draws, chocolate-doom|nugget-doom|t1|nugget-doom|matched, chocolate-doom|nugget-doom|t1|nugget-doom|draws, chocolate-doom|odamex|j06|chocolate-doom|matched, chocolate-doom|odamex|j06|chocolate-doom|draws, chocolate-doom|odamex|j06|odamex|matched, chocolate-doom|odamex|j06|odamex|draws, chocolate-doom|odamex|t1|chocolate-doom|matched, chocolate-doom|odamex|t1|chocolate-doom|draws, chocolate-doom|odamex|t1|odamex|matched, chocolate-doom|odamex|t1|odamex|draws, chocolate-doom|prboom-plus|j06|chocolate-doom|matched, chocolate-doom|prboom-plus|j06|chocolate-doom|draws, chocolate-doom|prboom-plus|j06|prboom-plus|matched, chocolate-doom|prboom-plus|j06|prboom-plus|draws, chocolate-doom|prboom-plus|t1|chocolate-doom|matched, chocolate-doom|prboom-plus|t1|chocolate-doom|draws, chocolate-doom|prboom-plus|t1|prboom-plus|matched, chocolate-doom|prboom-plus|t1|prboom-plus|draws, chocolate-doom|woof|j06|chocolate-doom|matched, chocolate-doom|woof|j06|chocolate-doom|draws, chocolate-doom|woof|j06|woof|matched, chocolate-doom|woof|j06|woof|draws, chocolate-doom|woof|t1|chocolate-doom|matched, chocolate-doom|woof|t1|chocolate-doom|draws, chocolate-doom|woof|t1|woof|matched, chocolate-doom|woof|t1|woof|draws, crispy-doom|dsda-doom|j06|crispy-doom|matched, crispy-doom|dsda-doom|j06|crispy-doom|draws, crispy-doom|dsda-doom|j06|dsda-doom|matched, crispy-doom|dsda-doom|j06|dsda-doom|draws, crispy-doom|dsda-doom|t1|crispy-doom|matched, crispy-doom|dsda-doom|t1|crispy-doom|draws, crispy-doom|dsda-doom|t1|dsda-doom|matched, crispy-doom|dsda-doom|t1|dsda-doom|draws, crispy-doom|gzdoom|j06|crispy-doom|matched, crispy-doom|gzdoom|j06|crispy-doom|draws, crispy-doom|gzdoom|j06|gzdoom|matched, crispy-doom|gzdoom|j06|gzdoom|draws, crispy-doom|nugget-doom|j06|crispy-doom|matched, crispy-doom|nugget-doom|j06|crispy-doom|draws, crispy-doom|nugget-doom|j06|nugget-doom|matched, crispy-doom|nugget-doom|j06|nugget-doom|draws, crispy-doom|prboom-plus|j06|crispy-doom|matched, crispy-doom|prboom-plus|j06|crispy-doom|draws, crispy-doom|prboom-plus|j06|prboom-plus|matched, crispy-doom|prboom-plus|j06|prboom-plus|draws, crispy-doom|prboom-plus|t1|crispy-doom|matched, crispy-doom|prboom-plus|t1|crispy-doom|draws, crispy-doom|prboom-plus|t1|prboom-plus|matched, crispy-doom|prboom-plus|t1|prboom-plus|draws, crispy-doom|woof|j06|crispy-doom|matched, crispy-doom|woof|j06|crispy-doom|draws, crispy-doom|woof|j06|woof|matched, crispy-doom|woof|j06|woof|draws, crispy-doom|woof|t1|crispy-doom|matched, crispy-doom|woof|t1|crispy-doom|draws, crispy-doom|woof|t1|woof|matched, crispy-doom|woof|t1|woof|draws, doom-ascii|doom3-bfg|j06|doom-ascii|matched, doom-ascii|doom3-bfg|j06|doom-ascii|draws, doom-ascii|doom3-bfg|j06|doom3-bfg|matched, doom-ascii|doom3-bfg|j06|doom3-bfg|draws, doom-ascii|doom3-bfg|t1|doom-ascii|matched, doom-ascii|doom3-bfg|t1|doom-ascii|draws, doom-ascii|doom3-bfg|t1|doom3-bfg|matched, doom-ascii|doom3-bfg|t1|doom3-bfg|draws, doom-ascii|dsda-doom|j06|doom-ascii|matched, doom-ascii|dsda-doom|j06|doom-ascii|draws, doom-ascii|dsda-doom|j06|dsda-doom|matched, doom-ascii|dsda-doom|j06|dsda-doom|draws, doom-ascii|dsda-doom|t1|doom-ascii|matched, doom-ascii|dsda-doom|t1|doom-ascii|draws, doom-ascii|dsda-doom|t1|dsda-doom|matched, doom-ascii|dsda-doom|t1|dsda-doom|draws, doom-ascii|eternity|j06|doom-ascii|matched, doom-ascii|eternity|j06|doom-ascii|draws, doom-ascii|eternity|j06|eternity|matched, doom-ascii|eternity|j06|eternity|draws, doom-ascii|eternity|t1|doom-ascii|matched, doom-ascii|eternity|t1|doom-ascii|draws, doom-ascii|eternity|t1|eternity|matched, doom-ascii|eternity|t1|eternity|draws, doom-ascii|fastdoom|j06|doom-ascii|matched, doom-ascii|fastdoom|j06|doom-ascii|draws, doom-ascii|fastdoom|j06|fastdoom|matched, doom-ascii|fastdoom|j06|fastdoom|draws, doom-ascii|fastdoom|t1|doom-ascii|matched, doom-ascii|fastdoom|t1|doom-ascii|draws, doom-ascii|fastdoom|t1|fastdoom|matched, doom-ascii|fastdoom|t1|fastdoom|draws, doom-ascii|nugget-doom|j06|doom-ascii|matched, doom-ascii|nugget-doom|j06|doom-ascii|draws, doom-ascii|nugget-doom|j06|nugget-doom|matched, doom-ascii|nugget-doom|j06|nugget-doom|draws, doom-ascii|nugget-doom|t1|doom-ascii|matched, doom-ascii|nugget-doom|t1|doom-ascii|draws, doom-ascii|nugget-doom|t1|nugget-doom|matched, doom-ascii|nugget-doom|t1|nugget-doom|draws, doom-ascii|odamex|j06|doom-ascii|matched, doom-ascii|odamex|j06|doom-ascii|draws, doom-ascii|odamex|j06|odamex|matched, doom-ascii|odamex|j06|odamex|draws, doom-ascii|odamex|t1|doom-ascii|matched, doom-ascii|odamex|t1|doom-ascii|draws, doom-ascii|odamex|t1|odamex|matched, doom-ascii|odamex|t1|odamex|draws, doom-ascii|prboom-plus|j06|doom-ascii|matched, doom-ascii|prboom-plus|j06|doom-ascii|draws, doom-ascii|prboom-plus|j06|prboom-plus|matched, doom-ascii|prboom-plus|j06|prboom-plus|draws, doom-ascii|prboom-plus|t1|doom-ascii|matched, doom-ascii|prboom-plus|t1|doom-ascii|draws, doom-ascii|prboom-plus|t1|prboom-plus|matched, doom-ascii|prboom-plus|t1|prboom-plus|draws, doom-ascii|woof|j06|doom-ascii|matched, doom-ascii|woof|j06|doom-ascii|draws, doom-ascii|woof|j06|woof|matched, doom-ascii|woof|j06|woof|draws, doom-ascii|woof|t1|doom-ascii|matched, doom-ascii|woof|t1|doom-ascii|draws, doom-ascii|woof|t1|woof|matched, doom-ascii|woof|t1|woof|draws, doom-ios|quake|j06|doom-ios|matched, doom-ios|quake|j06|doom-ios|draws, doom-ios|quake|j06|quake|matched, doom-ios|quake|j06|quake|draws, doom-ios|quake2|j06|doom-ios|matched, doom-ios|quake2|j06|doom-ios|draws, doom-ios|quake2|j06|quake2|matched, doom-ios|quake2|j06|quake2|draws, doom-wasm|doom3-bfg|j06|doom-wasm|matched, doom-wasm|doom3-bfg|j06|doom-wasm|draws, doom-wasm|doom3-bfg|j06|doom3-bfg|matched, doom-wasm|doom3-bfg|j06|doom3-bfg|draws, doom-wasm|doom3-bfg|t1|doom-wasm|matched, doom-wasm|doom3-bfg|t1|doom-wasm|draws, doom-wasm|doom3-bfg|t1|doom3-bfg|matched, doom-wasm|doom3-bfg|t1|doom3-bfg|draws, doom-wasm|dsda-doom|j06|doom-wasm|matched, doom-wasm|dsda-doom|j06|doom-wasm|draws, doom-wasm|dsda-doom|j06|dsda-doom|matched, doom-wasm|dsda-doom|j06|dsda-doom|draws, doom-wasm|dsda-doom|t1|doom-wasm|matched, doom-wasm|dsda-doom|t1|doom-wasm|draws, doom-wasm|dsda-doom|t1|dsda-doom|matched, doom-wasm|dsda-doom|t1|dsda-doom|draws, doom-wasm|eternity|j06|doom-wasm|matched, doom-wasm|eternity|j06|doom-wasm|draws, doom-wasm|eternity|j06|eternity|matched, doom-wasm|eternity|j06|eternity|draws, doom-wasm|eternity|t1|doom-wasm|matched, doom-wasm|eternity|t1|doom-wasm|draws, doom-wasm|eternity|t1|eternity|matched, doom-wasm|eternity|t1|eternity|draws, doom-wasm|fastdoom|j06|doom-wasm|matched, doom-wasm|fastdoom|j06|doom-wasm|draws, doom-wasm|fastdoom|j06|fastdoom|matched, doom-wasm|fastdoom|j06|fastdoom|draws, doom-wasm|fastdoom|t1|doom-wasm|matched, doom-wasm|fastdoom|t1|doom-wasm|draws, doom-wasm|fastdoom|t1|fastdoom|matched, doom-wasm|fastdoom|t1|fastdoom|draws, doom-wasm|gzdoom|j06|doom-wasm|matched, doom-wasm|gzdoom|j06|doom-wasm|draws, doom-wasm|gzdoom|j06|gzdoom|matched, doom-wasm|gzdoom|j06|gzdoom|draws, doom-wasm|gzdoom|t1|doom-wasm|matched, doom-wasm|gzdoom|t1|doom-wasm|draws, doom-wasm|gzdoom|t1|gzdoom|matched, doom-wasm|gzdoom|t1|gzdoom|draws, doom-wasm|nugget-doom|j06|doom-wasm|matched, doom-wasm|nugget-doom|j06|doom-wasm|draws, doom-wasm|nugget-doom|j06|nugget-doom|matched, doom-wasm|nugget-doom|j06|nugget-doom|draws, doom-wasm|nugget-doom|t1|doom-wasm|matched, doom-wasm|nugget-doom|t1|doom-wasm|draws, doom-wasm|nugget-doom|t1|nugget-doom|matched, doom-wasm|nugget-doom|t1|nugget-doom|draws, doom-wasm|odamex|j06|doom-wasm|matched, doom-wasm|odamex|j06|doom-wasm|draws, doom-wasm|odamex|j06|odamex|matched, doom-wasm|odamex|j06|odamex|draws, doom-wasm|odamex|t1|doom-wasm|matched, doom-wasm|odamex|t1|doom-wasm|draws, doom-wasm|odamex|t1|odamex|matched, doom-wasm|odamex|t1|odamex|draws, doom-wasm|prboom-plus|j06|doom-wasm|matched, doom-wasm|prboom-plus|j06|doom-wasm|draws, doom-wasm|prboom-plus|j06|prboom-plus|matched, doom-wasm|prboom-plus|j06|prboom-plus|draws, doom-wasm|prboom-plus|t1|doom-wasm|matched, doom-wasm|prboom-plus|t1|doom-wasm|draws, doom-wasm|prboom-plus|t1|prboom-plus|matched, doom-wasm|prboom-plus|t1|prboom-plus|draws, doom-wasm|woof|j06|doom-wasm|matched, doom-wasm|woof|j06|doom-wasm|draws, doom-wasm|woof|j06|woof|matched, doom-wasm|woof|j06|woof|draws, doom-wasm|woof|t1|doom-wasm|matched, doom-wasm|woof|t1|doom-wasm|draws, doom-wasm|woof|t1|woof|matched, doom-wasm|woof|t1|woof|draws, doom3-bfg|doomgeneric|j06|doom3-bfg|matched, doom3-bfg|doomgeneric|j06|doom3-bfg|draws, doom3-bfg|doomgeneric|j06|doomgeneric|matched, doom3-bfg|doomgeneric|j06|doomgeneric|draws, doom3-bfg|doomgeneric|t1|doom3-bfg|matched, doom3-bfg|doomgeneric|t1|doom3-bfg|draws, doom3-bfg|doomgeneric|t1|doomgeneric|matched, doom3-bfg|doomgeneric|t1|doomgeneric|draws, doom3-bfg|edge-classic|j06|doom3-bfg|matched, doom3-bfg|edge-classic|j06|doom3-bfg|draws, doom3-bfg|edge-classic|j06|edge-classic|matched, doom3-bfg|edge-classic|j06|edge-classic|draws, doom3-bfg|eternity|j06|doom3-bfg|matched, doom3-bfg|eternity|j06|doom3-bfg|draws, doom3-bfg|eternity|j06|eternity|matched, doom3-bfg|eternity|j06|eternity|draws, doom3-bfg|eternity|t1|doom3-bfg|matched, doom3-bfg|eternity|t1|doom3-bfg|draws, doom3-bfg|eternity|t1|eternity|matched, doom3-bfg|eternity|t1|eternity|draws, doom3-bfg|gzdoom|j06|doom3-bfg|matched, doom3-bfg|gzdoom|j06|doom3-bfg|draws, doom3-bfg|gzdoom|j06|gzdoom|matched, doom3-bfg|gzdoom|j06|gzdoom|draws, doom3-bfg|gzdoom|t1|doom3-bfg|matched, doom3-bfg|gzdoom|t1|doom3-bfg|draws, doom3-bfg|gzdoom|t1|gzdoom|matched, doom3-bfg|gzdoom|t1|gzdoom|draws, doom3-bfg|inter-doom|j06|doom3-bfg|matched, doom3-bfg|inter-doom|j06|doom3-bfg|draws, doom3-bfg|inter-doom|j06|inter-doom|matched, doom3-bfg|inter-doom|j06|inter-doom|draws, doom3-bfg|inter-doom|t1|doom3-bfg|matched, doom3-bfg|inter-doom|t1|doom3-bfg|draws, doom3-bfg|inter-doom|t1|inter-doom|matched, doom3-bfg|inter-doom|t1|inter-doom|draws, doom3-bfg|prboom-plus|j06|doom3-bfg|matched, doom3-bfg|prboom-plus|j06|doom3-bfg|draws, doom3-bfg|prboom-plus|j06|prboom-plus|matched, doom3-bfg|prboom-plus|j06|prboom-plus|draws, doom3-bfg|sdl-doom|j06|doom3-bfg|matched, doom3-bfg|sdl-doom|j06|doom3-bfg|draws, doom3-bfg|sdl-doom|j06|sdl-doom|matched, doom3-bfg|sdl-doom|j06|sdl-doom|draws, doom3-bfg|sdl-doom|t1|doom3-bfg|matched, doom3-bfg|sdl-doom|t1|doom3-bfg|draws, doom3-bfg|sdl-doom|t1|sdl-doom|matched, doom3-bfg|sdl-doom|t1|sdl-doom|draws, doomgeneric|dsda-doom|j06|doomgeneric|matched, doomgeneric|dsda-doom|j06|doomgeneric|draws, doomgeneric|dsda-doom|j06|dsda-doom|matched, doomgeneric|dsda-doom|j06|dsda-doom|draws, doomgeneric|dsda-doom|t1|doomgeneric|matched, doomgeneric|dsda-doom|t1|doomgeneric|draws, doomgeneric|dsda-doom|t1|dsda-doom|matched, doomgeneric|dsda-doom|t1|dsda-doom|draws, doomgeneric|eternity|j06|doomgeneric|matched, doomgeneric|eternity|j06|doomgeneric|draws, doomgeneric|eternity|j06|eternity|matched, doomgeneric|eternity|j06|eternity|draws, doomgeneric|eternity|t1|doomgeneric|matched, doomgeneric|eternity|t1|doomgeneric|draws, doomgeneric|eternity|t1|eternity|matched, doomgeneric|eternity|t1|eternity|draws, doomgeneric|fastdoom|j06|doomgeneric|matched, doomgeneric|fastdoom|j06|doomgeneric|draws, doomgeneric|fastdoom|j06|fastdoom|matched, doomgeneric|fastdoom|j06|fastdoom|draws, doomgeneric|fastdoom|t1|doomgeneric|matched, doomgeneric|fastdoom|t1|doomgeneric|draws, doomgeneric|fastdoom|t1|fastdoom|matched, doomgeneric|fastdoom|t1|fastdoom|draws, doomgeneric|nugget-doom|j06|doomgeneric|matched, doomgeneric|nugget-doom|j06|doomgeneric|draws, doomgeneric|nugget-doom|j06|nugget-doom|matched, doomgeneric|nugget-doom|j06|nugget-doom|draws, doomgeneric|nugget-doom|t1|doomgeneric|matched, doomgeneric|nugget-doom|t1|doomgeneric|draws, doomgeneric|nugget-doom|t1|nugget-doom|matched, doomgeneric|nugget-doom|t1|nugget-doom|draws, doomgeneric|odamex|j06|doomgeneric|matched, doomgeneric|odamex|j06|doomgeneric|draws, doomgeneric|odamex|j06|odamex|matched, doomgeneric|odamex|j06|odamex|draws, doomgeneric|odamex|t1|doomgeneric|matched, doomgeneric|odamex|t1|doomgeneric|draws, doomgeneric|odamex|t1|odamex|matched, doomgeneric|odamex|t1|odamex|draws, doomgeneric|prboom-plus|j06|doomgeneric|matched, doomgeneric|prboom-plus|j06|doomgeneric|draws, doomgeneric|prboom-plus|j06|prboom-plus|matched, doomgeneric|prboom-plus|j06|prboom-plus|draws, doomgeneric|prboom-plus|t1|doomgeneric|matched, doomgeneric|prboom-plus|t1|doomgeneric|draws, doomgeneric|prboom-plus|t1|prboom-plus|matched, doomgeneric|prboom-plus|t1|prboom-plus|draws, doomgeneric|srb2|j06|doomgeneric|matched, doomgeneric|srb2|j06|doomgeneric|draws, doomgeneric|srb2|j06|srb2|matched, doomgeneric|srb2|j06|srb2|draws, doomgeneric|woof|j06|doomgeneric|matched, doomgeneric|woof|j06|doomgeneric|draws, doomgeneric|woof|j06|woof|matched, doomgeneric|woof|j06|woof|draws, doomgeneric|woof|t1|doomgeneric|matched, doomgeneric|woof|t1|doomgeneric|draws, doomgeneric|woof|t1|woof|matched, doomgeneric|woof|t1|woof|draws, doomretro|doomsday|j06|doomretro|matched, doomretro|doomsday|j06|doomretro|draws, doomretro|doomsday|j06|doomsday|matched, doomretro|doomsday|j06|doomsday|draws, doomretro|dsda-doom|j06|doomretro|matched, doomretro|dsda-doom|j06|doomretro|draws, doomretro|dsda-doom|j06|dsda-doom|matched, doomretro|dsda-doom|j06|dsda-doom|draws, doomretro|edge-classic|j06|doomretro|matched, doomretro|edge-classic|j06|doomretro|draws, doomretro|edge-classic|j06|edge-classic|matched, doomretro|edge-classic|j06|edge-classic|draws, doomretro|edge-classic|t1|doomretro|matched, doomretro|edge-classic|t1|doomretro|draws, doomretro|edge-classic|t1|edge-classic|matched, doomretro|edge-classic|t1|edge-classic|draws, doomretro|eternity|j06|doomretro|matched, doomretro|eternity|j06|doomretro|draws, doomretro|eternity|j06|eternity|matched, doomretro|eternity|j06|eternity|draws, doomretro|fastdoom|j06|doomretro|matched, doomretro|fastdoom|j06|doomretro|draws, doomretro|fastdoom|j06|fastdoom|matched, doomretro|fastdoom|j06|fastdoom|draws, doomretro|gzdoom|j06|doomretro|matched, doomretro|gzdoom|j06|doomretro|draws, doomretro|gzdoom|j06|gzdoom|matched, doomretro|gzdoom|j06|gzdoom|draws, doomretro|gzdoom|t1|doomretro|matched, doomretro|gzdoom|t1|doomretro|draws, doomretro|gzdoom|t1|gzdoom|matched, doomretro|gzdoom|t1|gzdoom|draws, doomretro|odamex|j06|doomretro|matched, doomretro|odamex|j06|doomretro|draws, doomretro|odamex|j06|odamex|matched, doomretro|odamex|j06|odamex|draws, doomretro|odamex|t1|doomretro|matched, doomretro|odamex|t1|doomretro|draws, doomretro|odamex|t1|odamex|matched, doomretro|odamex|t1|odamex|draws, doomretro|prboom-plus|j06|doomretro|matched, doomretro|prboom-plus|j06|doomretro|draws, doomretro|prboom-plus|j06|prboom-plus|matched, doomretro|prboom-plus|j06|prboom-plus|draws, doomretro|prboom-plus|t1|doomretro|matched, doomretro|prboom-plus|t1|doomretro|draws, doomretro|prboom-plus|t1|prboom-plus|matched, doomretro|prboom-plus|t1|prboom-plus|draws, doomretro|srb2|j06|doomretro|matched, doomretro|srb2|j06|doomretro|draws, doomretro|srb2|j06|srb2|matched, doomretro|srb2|j06|srb2|draws, doomretro|srb2|t1|doomretro|matched, doomretro|srb2|t1|doomretro|draws, doomretro|srb2|t1|srb2|matched, doomretro|srb2|t1|srb2|draws, doomretro|woof|j06|doomretro|matched, doomretro|woof|j06|doomretro|draws, doomretro|woof|j06|woof|matched, doomretro|woof|j06|woof|draws, doomretro|woof|t1|doomretro|matched, doomretro|woof|t1|doomretro|draws, doomretro|woof|t1|woof|matched, doomretro|woof|t1|woof|draws, doomsday|edge-classic|j06|doomsday|matched, doomsday|edge-classic|j06|doomsday|draws, doomsday|edge-classic|j06|edge-classic|matched, doomsday|edge-classic|j06|edge-classic|draws, doomsday|edge-classic|t1|doomsday|matched, doomsday|edge-classic|t1|doomsday|draws, doomsday|edge-classic|t1|edge-classic|matched, doomsday|edge-classic|t1|edge-classic|draws, doomsday|eternity|j06|doomsday|matched, doomsday|eternity|j06|doomsday|draws, doomsday|eternity|j06|eternity|matched, doomsday|eternity|j06|eternity|draws, doomsday|eternity|t1|doomsday|matched, doomsday|eternity|t1|doomsday|draws, doomsday|eternity|t1|eternity|matched, doomsday|eternity|t1|eternity|draws, doomsday|gzdoom|j06|doomsday|matched, doomsday|gzdoom|j06|doomsday|draws, doomsday|gzdoom|j06|gzdoom|matched, doomsday|gzdoom|j06|gzdoom|draws, doomsday|gzdoom|t1|doomsday|matched, doomsday|gzdoom|t1|doomsday|draws, doomsday|gzdoom|t1|gzdoom|matched, doomsday|gzdoom|t1|gzdoom|draws, doomsday|inter-doom|j06|doomsday|matched, doomsday|inter-doom|j06|doomsday|draws, doomsday|inter-doom|j06|inter-doom|matched, doomsday|inter-doom|j06|inter-doom|draws, doomsday|inter-doom|t1|doomsday|matched, doomsday|inter-doom|t1|doomsday|draws, doomsday|inter-doom|t1|inter-doom|matched, doomsday|inter-doom|t1|inter-doom|draws, doomsday|woof|j06|doomsday|matched, doomsday|woof|j06|doomsday|draws, doomsday|woof|j06|woof|matched, doomsday|woof|j06|woof|draws, dsda-doom|gzdoom|j06|dsda-doom|matched, dsda-doom|gzdoom|j06|dsda-doom|draws, dsda-doom|gzdoom|j06|gzdoom|matched, dsda-doom|gzdoom|j06|gzdoom|draws, dsda-doom|gzdoom|t1|dsda-doom|matched, dsda-doom|gzdoom|t1|dsda-doom|draws, dsda-doom|gzdoom|t1|gzdoom|matched, dsda-doom|gzdoom|t1|gzdoom|draws, dsda-doom|inter-doom|j06|dsda-doom|matched, dsda-doom|inter-doom|j06|dsda-doom|draws, dsda-doom|inter-doom|j06|inter-doom|matched, dsda-doom|inter-doom|j06|inter-doom|draws, dsda-doom|inter-doom|t1|dsda-doom|matched, dsda-doom|inter-doom|t1|dsda-doom|draws, dsda-doom|inter-doom|t1|inter-doom|matched, dsda-doom|inter-doom|t1|inter-doom|draws, dsda-doom|odamex|j06|dsda-doom|matched, dsda-doom|odamex|j06|dsda-doom|draws, dsda-doom|odamex|j06|odamex|matched, dsda-doom|odamex|j06|odamex|draws, dsda-doom|odamex|t1|dsda-doom|matched, dsda-doom|odamex|t1|dsda-doom|draws, dsda-doom|odamex|t1|odamex|matched, dsda-doom|odamex|t1|odamex|draws, dsda-doom|sdl-doom|j06|dsda-doom|matched, dsda-doom|sdl-doom|j06|dsda-doom|draws, dsda-doom|sdl-doom|j06|sdl-doom|matched, dsda-doom|sdl-doom|j06|sdl-doom|draws, dsda-doom|sdl-doom|t1|dsda-doom|matched, dsda-doom|sdl-doom|t1|dsda-doom|draws, dsda-doom|sdl-doom|t1|sdl-doom|matched, dsda-doom|sdl-doom|t1|sdl-doom|draws, edge-classic|gzdoom|j06|edge-classic|matched, edge-classic|gzdoom|j06|edge-classic|draws, edge-classic|gzdoom|j06|gzdoom|matched, edge-classic|gzdoom|j06|gzdoom|draws, edge-classic|gzdoom|t1|edge-classic|matched, edge-classic|gzdoom|t1|edge-classic|draws, edge-classic|gzdoom|t1|gzdoom|matched, edge-classic|gzdoom|t1|gzdoom|draws, edge-classic|inter-doom|j06|edge-classic|matched, edge-classic|inter-doom|j06|edge-classic|draws, edge-classic|inter-doom|j06|inter-doom|matched, edge-classic|inter-doom|j06|inter-doom|draws, edge-classic|inter-doom|t1|edge-classic|matched, edge-classic|inter-doom|t1|edge-classic|draws, edge-classic|inter-doom|t1|inter-doom|matched, edge-classic|inter-doom|t1|inter-doom|draws, edge-classic|lua|j06|edge-classic|matched, edge-classic|lua|j06|edge-classic|draws, edge-classic|lua|j06|lua|matched, edge-classic|lua|j06|lua|draws, edge-classic|lua|t1|edge-classic|matched, edge-classic|lua|t1|edge-classic|draws, edge-classic|lua|t1|lua|matched, edge-classic|lua|t1|lua|draws, edge-classic|srb2|j06|edge-classic|matched, edge-classic|srb2|j06|edge-classic|draws, edge-classic|srb2|j06|srb2|matched, edge-classic|srb2|j06|srb2|draws, edge-classic|srb2|t1|edge-classic|matched, edge-classic|srb2|t1|edge-classic|draws, edge-classic|srb2|t1|srb2|matched, edge-classic|srb2|t1|srb2|draws, eternity|gzdoom|j06|eternity|matched, eternity|gzdoom|j06|eternity|draws, eternity|gzdoom|j06|gzdoom|matched, eternity|gzdoom|j06|gzdoom|draws, eternity|gzdoom|t1|eternity|matched, eternity|gzdoom|t1|eternity|draws, eternity|gzdoom|t1|gzdoom|matched, eternity|gzdoom|t1|gzdoom|draws, eternity|inter-doom|j06|eternity|matched, eternity|inter-doom|j06|eternity|draws, eternity|inter-doom|j06|inter-doom|matched, eternity|inter-doom|j06|inter-doom|draws, eternity|inter-doom|t1|eternity|matched, eternity|inter-doom|t1|eternity|draws, eternity|inter-doom|t1|inter-doom|matched, eternity|inter-doom|t1|inter-doom|draws, eternity|odamex|j06|eternity|matched, eternity|odamex|j06|eternity|draws, eternity|odamex|j06|odamex|matched, eternity|odamex|j06|odamex|draws, eternity|odamex|t1|eternity|matched, eternity|odamex|t1|eternity|draws, eternity|odamex|t1|odamex|matched, eternity|odamex|t1|odamex|draws, eternity|sdl-doom|j06|eternity|matched, eternity|sdl-doom|j06|eternity|draws, eternity|sdl-doom|j06|sdl-doom|matched, eternity|sdl-doom|j06|sdl-doom|draws, eternity|sdl-doom|t1|eternity|matched, eternity|sdl-doom|t1|eternity|draws, eternity|sdl-doom|t1|sdl-doom|matched, eternity|sdl-doom|t1|sdl-doom|draws, eternity|srb2|j06|eternity|matched, eternity|srb2|j06|eternity|draws, eternity|srb2|j06|srb2|matched, eternity|srb2|j06|srb2|draws, eternity|srb2|t1|eternity|matched, eternity|srb2|t1|eternity|draws, eternity|srb2|t1|srb2|matched, eternity|srb2|t1|srb2|draws, fastdoom|gzdoom|j06|fastdoom|matched, fastdoom|gzdoom|j06|fastdoom|draws, fastdoom|gzdoom|j06|gzdoom|matched, fastdoom|gzdoom|j06|gzdoom|draws, fastdoom|inter-doom|j06|fastdoom|matched, fastdoom|inter-doom|j06|fastdoom|draws, fastdoom|inter-doom|j06|inter-doom|matched, fastdoom|inter-doom|j06|inter-doom|draws, fastdoom|inter-doom|t1|fastdoom|matched, fastdoom|inter-doom|t1|fastdoom|draws, fastdoom|inter-doom|t1|inter-doom|matched, fastdoom|inter-doom|t1|inter-doom|draws, fastdoom|odamex|j06|fastdoom|matched, fastdoom|odamex|j06|fastdoom|draws, fastdoom|odamex|j06|odamex|matched, fastdoom|odamex|j06|odamex|draws, fastdoom|prboom-plus|j06|fastdoom|matched, fastdoom|prboom-plus|j06|fastdoom|draws, fastdoom|prboom-plus|j06|prboom-plus|matched, fastdoom|prboom-plus|j06|prboom-plus|draws, fastdoom|prboom-plus|t1|fastdoom|matched, fastdoom|prboom-plus|t1|fastdoom|draws, fastdoom|prboom-plus|t1|prboom-plus|matched, fastdoom|prboom-plus|t1|prboom-plus|draws, fastdoom|sdl-doom|j06|fastdoom|matched, fastdoom|sdl-doom|j06|fastdoom|draws, fastdoom|sdl-doom|j06|sdl-doom|matched, fastdoom|sdl-doom|j06|sdl-doom|draws, fastdoom|sdl-doom|t1|fastdoom|matched, fastdoom|sdl-doom|t1|fastdoom|draws, fastdoom|sdl-doom|t1|sdl-doom|matched, fastdoom|sdl-doom|t1|sdl-doom|draws, fastdoom|woof|j06|fastdoom|matched, fastdoom|woof|j06|fastdoom|draws, fastdoom|woof|j06|woof|matched, fastdoom|woof|j06|woof|draws, fastdoom|woof|t1|fastdoom|matched, fastdoom|woof|t1|fastdoom|draws, fastdoom|woof|t1|woof|matched, fastdoom|woof|t1|woof|draws, gzdoom|inter-doom|j06|gzdoom|matched, gzdoom|inter-doom|j06|gzdoom|draws, gzdoom|inter-doom|j06|inter-doom|matched, gzdoom|inter-doom|j06|inter-doom|draws, gzdoom|inter-doom|t1|gzdoom|matched, gzdoom|inter-doom|t1|gzdoom|draws, gzdoom|inter-doom|t1|inter-doom|matched, gzdoom|inter-doom|t1|inter-doom|draws, gzdoom|prboom-plus|j06|gzdoom|matched, gzdoom|prboom-plus|j06|gzdoom|draws, gzdoom|prboom-plus|j06|prboom-plus|matched, gzdoom|prboom-plus|j06|prboom-plus|draws, gzdoom|prboom-plus|t1|gzdoom|matched, gzdoom|prboom-plus|t1|gzdoom|draws, gzdoom|prboom-plus|t1|prboom-plus|matched, gzdoom|prboom-plus|t1|prboom-plus|draws, gzdoom|quake2|j06|gzdoom|matched, gzdoom|quake2|j06|gzdoom|draws, gzdoom|quake2|j06|quake2|matched, gzdoom|quake2|j06|quake2|draws, gzdoom|srb2|j06|gzdoom|matched, gzdoom|srb2|j06|gzdoom|draws, gzdoom|srb2|j06|srb2|matched, gzdoom|srb2|j06|srb2|draws, gzdoom|srb2|t1|gzdoom|matched, gzdoom|srb2|t1|gzdoom|draws, gzdoom|srb2|t1|srb2|matched, gzdoom|srb2|t1|srb2|draws, gzdoom|woof|j06|gzdoom|matched, gzdoom|woof|j06|gzdoom|draws, gzdoom|woof|j06|woof|matched, gzdoom|woof|j06|woof|draws, gzdoom|woof|t1|gzdoom|matched, gzdoom|woof|t1|gzdoom|draws, gzdoom|woof|t1|woof|matched, gzdoom|woof|t1|woof|draws, inter-doom|nugget-doom|j06|inter-doom|matched, inter-doom|nugget-doom|j06|inter-doom|draws, inter-doom|nugget-doom|j06|nugget-doom|matched, inter-doom|nugget-doom|j06|nugget-doom|draws, inter-doom|nugget-doom|t1|inter-doom|matched, inter-doom|nugget-doom|t1|inter-doom|draws, inter-doom|nugget-doom|t1|nugget-doom|matched, inter-doom|nugget-doom|t1|nugget-doom|draws, inter-doom|odamex|j06|inter-doom|matched, inter-doom|odamex|j06|inter-doom|draws, inter-doom|odamex|j06|odamex|matched, inter-doom|odamex|j06|odamex|draws, inter-doom|odamex|t1|inter-doom|matched, inter-doom|odamex|t1|inter-doom|draws, inter-doom|odamex|t1|odamex|matched, inter-doom|odamex|t1|odamex|draws, inter-doom|prboom-plus|j06|inter-doom|matched, inter-doom|prboom-plus|j06|inter-doom|draws, inter-doom|prboom-plus|j06|prboom-plus|matched, inter-doom|prboom-plus|j06|prboom-plus|draws, inter-doom|prboom-plus|t1|inter-doom|matched, inter-doom|prboom-plus|t1|inter-doom|draws, inter-doom|prboom-plus|t1|prboom-plus|matched, inter-doom|prboom-plus|t1|prboom-plus|draws, inter-doom|srb2|j06|inter-doom|matched, inter-doom|srb2|j06|inter-doom|draws, inter-doom|srb2|j06|srb2|matched, inter-doom|srb2|j06|srb2|draws, inter-doom|srb2|t1|inter-doom|matched, inter-doom|srb2|t1|inter-doom|draws, inter-doom|srb2|t1|srb2|matched, inter-doom|srb2|t1|srb2|draws, inter-doom|woof|j06|inter-doom|matched, inter-doom|woof|j06|inter-doom|draws, inter-doom|woof|j06|woof|matched, inter-doom|woof|j06|woof|draws, inter-doom|woof|t1|inter-doom|matched, inter-doom|woof|t1|inter-doom|draws, inter-doom|woof|t1|woof|matched, inter-doom|woof|t1|woof|draws, lua|srb2|j06|lua|matched, lua|srb2|j06|lua|draws, lua|srb2|j06|srb2|matched, lua|srb2|j06|srb2|draws, lua|srb2|t1|lua|matched, lua|srb2|t1|lua|draws, lua|srb2|t1|srb2|matched, lua|srb2|t1|srb2|draws, nugget-doom|sdl-doom|j06|nugget-doom|matched, nugget-doom|sdl-doom|j06|nugget-doom|draws, nugget-doom|sdl-doom|j06|sdl-doom|matched, nugget-doom|sdl-doom|j06|sdl-doom|draws, nugget-doom|sdl-doom|t1|nugget-doom|matched, nugget-doom|sdl-doom|t1|nugget-doom|draws, nugget-doom|sdl-doom|t1|sdl-doom|matched, nugget-doom|sdl-doom|t1|sdl-doom|draws, odamex|prboom-plus|j06|odamex|matched, odamex|prboom-plus|j06|odamex|draws, odamex|prboom-plus|j06|prboom-plus|matched, odamex|prboom-plus|j06|prboom-plus|draws, odamex|prboom-plus|t1|odamex|matched, odamex|prboom-plus|t1|odamex|draws, odamex|prboom-plus|t1|prboom-plus|matched, odamex|prboom-plus|t1|prboom-plus|draws, odamex|quake|j06|odamex|matched, odamex|quake|j06|odamex|draws, odamex|quake|j06|quake|matched, odamex|quake|j06|quake|draws, odamex|quake|t1|odamex|matched, odamex|quake|t1|odamex|draws, odamex|quake|t1|quake|matched, odamex|quake|t1|quake|draws, odamex|quake2|j06|odamex|matched, odamex|quake2|j06|odamex|draws, odamex|quake2|j06|quake2|matched, odamex|quake2|j06|quake2|draws, odamex|quake2|t1|odamex|matched, odamex|quake2|t1|odamex|draws, odamex|quake2|t1|quake2|matched, odamex|quake2|t1|quake2|draws, odamex|sdl-doom|j06|odamex|matched, odamex|sdl-doom|j06|odamex|draws, odamex|sdl-doom|j06|sdl-doom|matched, odamex|sdl-doom|j06|sdl-doom|draws, odamex|sdl-doom|t1|odamex|matched, odamex|sdl-doom|t1|odamex|draws, odamex|sdl-doom|t1|sdl-doom|matched, odamex|sdl-doom|t1|sdl-doom|draws, odamex|srb2|j06|odamex|matched, odamex|srb2|j06|odamex|draws, odamex|srb2|j06|srb2|matched, odamex|srb2|j06|srb2|draws, odamex|woof|j06|odamex|matched, odamex|woof|j06|odamex|draws, odamex|woof|j06|woof|matched, odamex|woof|j06|woof|draws, odamex|woof|t1|odamex|matched, odamex|woof|t1|odamex|draws, odamex|woof|t1|woof|matched, odamex|woof|t1|woof|draws, prboom-plus|sdl-doom|j06|prboom-plus|matched, prboom-plus|sdl-doom|j06|prboom-plus|draws, prboom-plus|sdl-doom|j06|sdl-doom|matched, prboom-plus|sdl-doom|j06|sdl-doom|draws, prboom-plus|sdl-doom|t1|prboom-plus|matched, prboom-plus|sdl-doom|t1|prboom-plus|draws, prboom-plus|sdl-doom|t1|sdl-doom|matched, prboom-plus|sdl-doom|t1|sdl-doom|draws, prboom-plus|srb2|j06|prboom-plus|matched, prboom-plus|srb2|j06|prboom-plus|draws, prboom-plus|srb2|j06|srb2|matched, prboom-plus|srb2|j06|srb2|draws, prboom-plus|srb2|t1|prboom-plus|matched, prboom-plus|srb2|t1|prboom-plus|draws, prboom-plus|srb2|t1|srb2|matched, prboom-plus|srb2|t1|srb2|draws, puredoom|quake2|j06|puredoom|matched, puredoom|quake2|j06|puredoom|draws, puredoom|quake2|j06|quake2|matched, puredoom|quake2|j06|quake2|draws, quake|quake2|j06|quake|matched, quake|quake2|j06|quake|draws, quake|quake2|j06|quake2|matched, quake|quake2|j06|quake2|draws, quake|quake2|t1|quake|matched, quake|quake2|t1|quake|draws, quake|quake2|t1|quake2|matched, quake|quake2|t1|quake2|draws, quake|srb2|j06|quake|matched, quake|srb2|j06|quake|draws, quake|srb2|j06|srb2|matched, quake|srb2|j06|srb2|draws, quake|srb2|t1|quake|matched, quake|srb2|t1|quake|draws, quake|srb2|t1|srb2|matched, quake|srb2|t1|srb2|draws, quake2|srb2|j06|quake2|matched, quake2|srb2|j06|quake2|draws, quake2|srb2|j06|srb2|matched, quake2|srb2|j06|srb2|draws, quake2|srb2|t1|quake2|matched, quake2|srb2|t1|quake2|draws, quake2|srb2|t1|srb2|matched, quake2|srb2|t1|srb2|draws, sdl-doom|woof|j06|sdl-doom|matched, sdl-doom|woof|j06|sdl-doom|draws, sdl-doom|woof|j06|woof|matched, sdl-doom|woof|j06|woof|draws, sdl-doom|woof|t1|sdl-doom|matched, sdl-doom|woof|t1|sdl-doom|draws, sdl-doom|woof|t1|woof|matched, sdl-doom|woof|t1|woof|draws, srb2|woof|j06|srb2|matched, srb2|woof|j06|srb2|draws, srb2|woof|j06|woof|matched, srb2|woof|j06|woof|draws, srb2|woof|t1|srb2|matched, srb2|woof|t1|srb2|draws, srb2|woof|t1|woof|matched, srb2|woof|t1|woof|draws.

| set | group | borrower | lineage | n | share | perm_share | native_dir_share |
|---|---|---|---|---|---|---|---|
| confirmed | chocolate-doom|eternity|source/textscreen | eternity | chocolate|eternity | 224 | 0.598 | 0.046 | 0.482 |
| confirmed | chocolate-doom|odamex|libraries/textscreen/examples | odamex | chocolate|odamex | 15 | 0.667 | 0.105 | 0.390 |
| confirmed | chocolate-doom|odamex|libraries/textscreen | odamex | chocolate|odamex | 193 | 0.233 | 0.022 | 0.101 |
| confirmed | chocolate-doom|prboom-plus|prboom2/src/TEXTSCREEN | prboom-plus | chocolate|prboom | 8 | 0.625 | 0.040 | 0.519 |
| confirmed | chocolate-doom|woof|opl | woof | chocolate|woof | 53 | 0.547 | 0.086 | 0.662 |
| confirmed | chocolate-doom|woof|textscreen | woof | chocolate|woof | 214 | 0.593 | 0.089 | 0.375 |
| unconfirmed | chocolate-doom~dsda-doom:src | chocolate-doom | chocolate|prboom | 27 | 0.185 | n/a | n/a |
| unconfirmed | chocolate-doom~dsda-doom:src/doom | chocolate-doom | chocolate|prboom | 10 | 0.000 | n/a | n/a |
| unconfirmed | chocolate-doom~fastdoom:src | chocolate-doom | chocolate|fastdoom | 15 | 0.067 | n/a | n/a |
| unconfirmed | chocolate-doom~linuxdoom:src | chocolate-doom | chocolate|linuxdoom | 9 | 0.111 | n/a | n/a |
| unconfirmed | chocolate-doom~linuxdoom:src/doom | chocolate-doom | chocolate|linuxdoom | 10 | 0.000 | n/a | n/a |
| unconfirmed | chocolate-doom~nugget-doom:man | chocolate-doom | chocolate|woof | 7 | 1.000 | n/a | n/a |
| unconfirmed | chocolate-doom~nugget-doom:src | chocolate-doom | chocolate|woof | 16 | 0.000 | n/a | n/a |
| unconfirmed | chocolate-doom~odamex:textscreen | chocolate-doom | chocolate|odamex | 13 | 0.154 | n/a | n/a |
| unconfirmed | chocolate-doom~prboom-plus:src | chocolate-doom | chocolate|prboom | 32 | 0.000 | n/a | n/a |
| unconfirmed | chocolate-doom~prboom-plus:src/doom | chocolate-doom | chocolate|prboom | 5 | 0.200 | n/a | n/a |
| unconfirmed | chocolate-doom~woof:man | chocolate-doom | chocolate|woof | 7 | 1.000 | n/a | n/a |
| unconfirmed | chocolate-doom~woof:src | chocolate-doom | chocolate|woof | 182 | 0.044 | n/a | n/a |
| unconfirmed | chocolate-doom~woof:src/doom | chocolate-doom | chocolate|woof | 17 | 0.059 | n/a | n/a |
| unconfirmed | chocolate-doom~woof:src/setup | chocolate-doom | chocolate|woof | 10 | 0.200 | n/a | n/a |
| unconfirmed | chocolate-doom~woof:textscreen | chocolate-doom | chocolate|woof | 13 | 0.077 | n/a | n/a |
| unconfirmed | crispy-doom~dsda-doom:src/doom | crispy-doom | chocolate|prboom | 6 | 0.000 | n/a | n/a |
| unconfirmed | crispy-doom~fastdoom:src/doom | crispy-doom | chocolate|fastdoom | 11 | 0.091 | n/a | n/a |
| unconfirmed | crispy-doom~linuxdoom:src/doom | crispy-doom | chocolate|linuxdoom | 7 | 0.143 | n/a | n/a |
| unconfirmed | crispy-doom~prboom-plus:src/doom | crispy-doom | chocolate|prboom | 11 | 0.091 | n/a | n/a |
| unconfirmed | crispy-doom~woof:src/doom | crispy-doom | chocolate|woof | 17 | 0.059 | n/a | n/a |
| unconfirmed | doomgeneric~fastdoom:doomgeneric | doomgeneric | doomgeneric|fastdoom | 19 | 0.842 | n/a | n/a |
| unconfirmed | doomgeneric~nugget-doom:doomgeneric | doomgeneric | doomgeneric|woof | 5 | 0.600 | n/a | n/a |
| unconfirmed | doomgeneric~prboom-plus:doomgeneric | doomgeneric | doomgeneric|prboom | 17 | 0.824 | n/a | n/a |
| unconfirmed | doomgeneric~srb2:doomgeneric | doomgeneric | doomgeneric|srb2 | 44 | 0.932 | n/a | n/a |
| unconfirmed | doomgeneric~woof:doomgeneric | doomgeneric | doomgeneric|woof | 45 | 0.956 | n/a | n/a |
| unconfirmed | doomretro~curl:src | doomretro | curl|doomretro | 6 | 0.000 | n/a | n/a |
| unconfirmed | doomretro~doom3do:src | doomretro | doom3do|doomretro | 5 | 0.200 | n/a | n/a |
| unconfirmed | doomretro~dsda-doom:src | doomretro | doomretro|prboom | 11 | 0.091 | n/a | n/a |
| unconfirmed | doomretro~linuxdoom:src | doomretro | doomretro|linuxdoom | 5 | 0.200 | n/a | n/a |
| unconfirmed | doomretro~quake:src | doomretro | doomretro|quake | 9 | 0.111 | n/a | n/a |
| unconfirmed | doomretro~quake2:src | doomretro | doomretro|quake2 | 5 | 0.200 | n/a | n/a |
| unconfirmed | doomretro~srb2:src | doomretro | doomretro|srb2 | 13 | 0.077 | n/a | n/a |
| unconfirmed | doomretro~woof:src | doomretro | doomretro|woof | 9 | 0.111 | n/a | n/a |
| unconfirmed | dsda-doom~chocolate-doom:prboom2/src | dsda-doom | chocolate|prboom | 19 | 0.053 | n/a | n/a |
| unconfirmed | dsda-doom~chocolate-doom:prboom2/src/dsda | dsda-doom | chocolate|prboom | 7 | 0.143 | n/a | n/a |
| unconfirmed | dsda-doom~doom-ascii:prboom2/src | dsda-doom | doom-ascii|prboom | 10 | 0.000 | n/a | n/a |
| unconfirmed | dsda-doom~doom-ascii:prboom2/src/dsda | dsda-doom | doom-ascii|prboom | 7 | 0.143 | n/a | n/a |
| unconfirmed | dsda-doom~doom-wasm:prboom2/src | dsda-doom | doom-wasm|prboom | 16 | 0.000 | n/a | n/a |
| unconfirmed | dsda-doom~doom-wasm:prboom2/src/MUSIC | dsda-doom | doom-wasm|prboom | 7 | 0.571 | n/a | n/a |
| unconfirmed | dsda-doom~doom-wasm:prboom2/src/dsda | dsda-doom | doom-wasm|prboom | 7 | 0.143 | n/a | n/a |
| unconfirmed | dsda-doom~doom-wasm:prboom2/src/textscreen | dsda-doom | doom-wasm|prboom | 5 | 1.000 | n/a | n/a |
| unconfirmed | dsda-doom~fastdoom:prboom2/src | dsda-doom | fastdoom|prboom | 19 | 0.053 | n/a | n/a |
| unconfirmed | dsda-doom~fastdoom:prboom2/src/dsda | dsda-doom | fastdoom|prboom | 15 | 0.067 | n/a | n/a |
| unconfirmed | dsda-doom~inter-doom:prboom2/src | dsda-doom | chocolate|prboom | 33 | 0.061 | n/a | n/a |
| unconfirmed | dsda-doom~inter-doom:prboom2/src/dsda | dsda-doom | chocolate|prboom | 12 | 0.000 | n/a | n/a |
| unconfirmed | dsda-doom~inter-doom:prboom2/src/textscreen | dsda-doom | chocolate|prboom | 5 | 1.000 | n/a | n/a |
| unconfirmed | dsda-doom~linuxdoom:prboom2/src | dsda-doom | linuxdoom|prboom | 5 | 0.400 | n/a | n/a |
| unconfirmed | dsda-doom~quake:prboom2/src | dsda-doom | prboom|quake | 8 | 0.000 | n/a | n/a |
| unconfirmed | dsda-doom~quake:prboom2/src/dsda | dsda-doom | prboom|quake | 6 | 0.000 | n/a | n/a |
| unconfirmed | dsda-doom~quake2:prboom2/src | dsda-doom | prboom|quake2 | 8 | 0.000 | n/a | n/a |
| unconfirmed | dsda-doom~srb2:prboom2/src | dsda-doom | prboom|srb2 | 47 | 0.064 | n/a | n/a |
| unconfirmed | dsda-doom~srb2:prboom2/src/MUSIC | dsda-doom | prboom|srb2 | 10 | 0.700 | n/a | n/a |
| unconfirmed | dsda-doom~srb2:prboom2/src/dsda | dsda-doom | prboom|srb2 | 25 | 0.040 | n/a | n/a |
| unconfirmed | edge-classic~doomsday:source_files/ddf | edge-classic | doomsday|edge-classic | 9 | 0.111 | n/a | n/a |
| unconfirmed | edge-classic~doomsday:source_files/dehacked | edge-classic | doomsday|edge-classic | 6 | 0.500 | n/a | n/a |
| unconfirmed | edge-classic~doomsday:source_files/edge | edge-classic | doomsday|edge-classic | 33 | 0.242 | n/a | n/a |
| unconfirmed | edge-classic~gzdoom:source_files/ddf | edge-classic | edge-classic|gzdoom | 7 | 0.714 | n/a | n/a |
| unconfirmed | edge-classic~gzdoom:source_files/edge | edge-classic | edge-classic|gzdoom | 46 | 0.565 | n/a | n/a |
| unconfirmed | edge-classic~gzdoom:source_files/edge/render/sokol | edge-classic | edge-classic|gzdoom | 10 | 0.700 | n/a | n/a |
| unconfirmed | edge-classic~gzdoom:source_files/edge/script/compat | edge-classic | edge-classic|gzdoom | 5 | 0.800 | n/a | n/a |
| unconfirmed | edge-classic~odamex:source_files/edge | edge-classic | edge-classic|odamex | 17 | 0.059 | n/a | n/a |
| unconfirmed | eternity~chocolate-doom:source/textscreen | eternity | chocolate|eternity | 8 | 0.750 | n/a | n/a |
| unconfirmed | eternity~doom-wasm:source/textscreen | eternity | doom-wasm|eternity | 192 | 0.646 | n/a | n/a |
| unconfirmed | eternity~doomsday:source | eternity | doomsday|eternity | 64 | 0.031 | n/a | n/a |
| unconfirmed | eternity~doomsday:source/textscreen | eternity | doomsday|eternity | 5 | 0.600 | n/a | n/a |
| unconfirmed | eternity~gzdoom:source | eternity | eternity|gzdoom | 58 | 0.000 | n/a | n/a |
| unconfirmed | eternity~inter-doom:source/textscreen | eternity | chocolate|eternity | 187 | 0.658 | n/a | n/a |
| unconfirmed | eternity~odamex:source | eternity | eternity|odamex | 72 | 0.083 | n/a | n/a |
| unconfirmed | eternity~odamex:source/textscreen | eternity | eternity|odamex | 10 | 0.800 | n/a | n/a |
| unconfirmed | fastdoom~chocolate-doom:FASTDOOM | fastdoom | chocolate|fastdoom | 25 | 0.040 | n/a | n/a |
| unconfirmed | fastdoom~crispy-doom:FASTDOOM | fastdoom | chocolate|fastdoom | 16 | 0.000 | n/a | n/a |
| unconfirmed | fastdoom~doom-ascii:FASTDOOM | fastdoom | doom-ascii|fastdoom | 14 | 0.000 | n/a | n/a |
| unconfirmed | fastdoom~doom-wasm:FASTDOOM | fastdoom | doom-wasm|fastdoom | 36 | 0.000 | n/a | n/a |
| unconfirmed | fastdoom~doom3do:FASTDOOM | fastdoom | doom3do|fastdoom | 5 | 0.200 | n/a | n/a |
| unconfirmed | fastdoom~doomgeneric:FASTDOOM | fastdoom | doomgeneric|fastdoom | 16 | 0.000 | n/a | n/a |
| unconfirmed | fastdoom~doomsday:FASTDOOM | fastdoom | doomsday|fastdoom | 6 | 0.000 | n/a | n/a |
| unconfirmed | fastdoom~dsda-doom:FASTDOOM | fastdoom | fastdoom|prboom | 50 | 0.000 | n/a | n/a |
| unconfirmed | fastdoom~dsda-doom:FDSETUP | fastdoom | fastdoom|prboom | 5 | 0.600 | n/a | n/a |
| unconfirmed | fastdoom~gzdoom:FASTDOOM | fastdoom | fastdoom|gzdoom | 7 | 0.143 | n/a | n/a |
| unconfirmed | fastdoom~inter-doom:FASTDOOM | fastdoom | chocolate|fastdoom | 16 | 0.000 | n/a | n/a |
| unconfirmed | fastdoom~linuxdoom:FASTDOOM | fastdoom | fastdoom|linuxdoom | 31 | 0.161 | n/a | n/a |
| unconfirmed | fastdoom~puredoom:FASTDOOM | fastdoom | fastdoom|puredoom | 8 | 0.000 | n/a | n/a |
| unconfirmed | fastdoom~quake:FASTDOOM | fastdoom | fastdoom|quake | 82 | 0.049 | n/a | n/a |
| unconfirmed | fastdoom~quake2:FASTDOOM | fastdoom | fastdoom|quake2 | 6 | 0.333 | n/a | n/a |
| unconfirmed | fastdoom~sdl-doom:FASTDOOM | fastdoom | fastdoom|sdl-doom | 15 | 0.067 | n/a | n/a |
| unconfirmed | fastdoom~srb2:FASTDOOM | fastdoom | fastdoom|srb2 | 12 | 0.000 | n/a | n/a |
| unconfirmed | fastdoom~woof:FASTDOOM | fastdoom | fastdoom|woof | 12 | 0.000 | n/a | n/a |
| unconfirmed | gzdoom~eternity:src/playsim | gzdoom | eternity|gzdoom | 7 | 0.429 | n/a | n/a |
| unconfirmed | inter-doom~dsda-doom:src | inter-doom | chocolate|prboom | 9 | 0.222 | n/a | n/a |
| unconfirmed | inter-doom~dsda-doom:src/doom | inter-doom | chocolate|prboom | 24 | 0.208 | n/a | n/a |
| unconfirmed | inter-doom~linuxdoom:src/doom | inter-doom | chocolate|linuxdoom | 7 | 0.429 | n/a | n/a |
| unconfirmed | inter-doom~nugget-doom:src/doom | inter-doom | chocolate|woof | 8 | 0.000 | n/a | n/a |
| unconfirmed | inter-doom~prboom-plus:src | inter-doom | chocolate|prboom | 7 | 0.143 | n/a | n/a |
| unconfirmed | inter-doom~prboom-plus:src/doom | inter-doom | chocolate|prboom | 7 | 0.143 | n/a | n/a |
| unconfirmed | inter-doom~srb2:src | inter-doom | chocolate|srb2 | 9 | 0.556 | n/a | n/a |
| unconfirmed | inter-doom~srb2:src/doom | inter-doom | chocolate|srb2 | 15 | 0.200 | n/a | n/a |
| unconfirmed | inter-doom~woof:lib/textscreen | inter-doom | chocolate|woof | 6 | 0.833 | n/a | n/a |
| unconfirmed | inter-doom~woof:src | inter-doom | chocolate|woof | 22 | 0.455 | n/a | n/a |
| unconfirmed | inter-doom~woof:src/doom | inter-doom | chocolate|woof | 29 | 0.414 | n/a | n/a |
| unconfirmed | nugget-doom~chocolate-doom:src | nugget-doom | chocolate|woof | 15 | 0.067 | n/a | n/a |
| unconfirmed | nugget-doom~doom-wasm:src | nugget-doom | doom-wasm|woof | 13 | 0.077 | n/a | n/a |
| unconfirmed | nugget-doom~inter-doom:src | nugget-doom | chocolate|woof | 17 | 0.118 | n/a | n/a |
| unconfirmed | odamex~chocolate-doom:libraries/textscreen | odamex | chocolate|odamex | 11 | 0.545 | n/a | n/a |
| unconfirmed | odamex~doom-wasm:libraries/textscreen | odamex | doom-wasm|odamex | 164 | 0.268 | n/a | n/a |
| unconfirmed | odamex~doom-wasm:libraries/textscreen/examples | odamex | doom-wasm|odamex | 14 | 0.714 | n/a | n/a |
| unconfirmed | odamex~doomsday:client/src | odamex | doomsday|odamex | 17 | 0.118 | n/a | n/a |
| unconfirmed | odamex~doomsday:common | odamex | doomsday|odamex | 33 | 0.030 | n/a | n/a |
| unconfirmed | odamex~edge-classic:client/src | odamex | edge-classic|odamex | 11 | 0.182 | n/a | n/a |
| unconfirmed | odamex~edge-classic:common | odamex | edge-classic|odamex | 22 | 0.000 | n/a | n/a |
| unconfirmed | odamex~eternity:client/sdl | odamex | eternity|odamex | 8 | 0.750 | n/a | n/a |
| unconfirmed | odamex~eternity:client/src | odamex | eternity|odamex | 19 | 0.053 | n/a | n/a |
| unconfirmed | odamex~eternity:common | odamex | eternity|odamex | 31 | 0.032 | n/a | n/a |
| unconfirmed | odamex~eternity:libraries/textscreen | odamex | eternity|odamex | 9 | 0.667 | n/a | n/a |
| unconfirmed | odamex~eternity:server/src | odamex | eternity|odamex | 5 | 0.200 | n/a | n/a |
| unconfirmed | odamex~inter-doom:libraries/textscreen | odamex | chocolate|odamex | 162 | 0.272 | n/a | n/a |
| unconfirmed | odamex~woof:libraries/textscreen | odamex | odamex|woof | 12 | 0.583 | n/a | n/a |
| unconfirmed | prboom-plus~chocolate-doom:prboom2/src | prboom-plus | chocolate|prboom | 19 | 0.105 | n/a | n/a |
| unconfirmed | prboom-plus~chocolate-doom:prboom2/src/MUSIC | prboom-plus | chocolate|prboom | 19 | 0.684 | n/a | n/a |
| unconfirmed | prboom-plus~chocolate-doom:prboom2/src/TEXTSCREEN | prboom-plus | chocolate|prboom | 5 | 0.800 | n/a | n/a |
| unconfirmed | prboom-plus~crispy-doom:prboom2/src | prboom-plus | chocolate|prboom | 15 | 0.067 | n/a | n/a |
| unconfirmed | prboom-plus~doom-wasm:prboom2/src | prboom-plus | doom-wasm|prboom | 12 | 0.000 | n/a | n/a |
| unconfirmed | prboom-plus~doom-wasm:prboom2/src/MUSIC | prboom-plus | doom-wasm|prboom | 12 | 0.667 | n/a | n/a |
| unconfirmed | prboom-plus~doom-wasm:prboom2/src/TEXTSCREEN | prboom-plus | doom-wasm|prboom | 12 | 0.667 | n/a | n/a |
| unconfirmed | prboom-plus~doomgeneric:prboom2/src | prboom-plus | doomgeneric|prboom | 7 | 0.143 | n/a | n/a |
| unconfirmed | prboom-plus~doomsday:prboom2/src | prboom-plus | doomsday|prboom | 10 | 0.000 | n/a | n/a |
| unconfirmed | prboom-plus~inter-doom:prboom2/src | prboom-plus | chocolate|prboom | 26 | 0.000 | n/a | n/a |
| unconfirmed | prboom-plus~inter-doom:prboom2/src/MUSIC | prboom-plus | chocolate|prboom | 12 | 0.583 | n/a | n/a |
| unconfirmed | prboom-plus~inter-doom:prboom2/src/TEXTSCREEN | prboom-plus | chocolate|prboom | 9 | 0.667 | n/a | n/a |
| unconfirmed | prboom-plus~quake:prboom2/src | prboom-plus | prboom|quake | 5 | 0.200 | n/a | n/a |
| unconfirmed | prboom-plus~sdl-doom:prboom2/src | prboom-plus | prboom|sdl-doom | 7 | 0.143 | n/a | n/a |
| unconfirmed | prboom-plus~sdl-doom:prboom2/src/MUSIC | prboom-plus | prboom|sdl-doom | 7 | 0.857 | n/a | n/a |
| unconfirmed | prboom-plus~srb2:prboom2/src | prboom-plus | prboom|srb2 | 35 | 0.057 | n/a | n/a |
| unconfirmed | prboom-plus~srb2:prboom2/src/MUSIC | prboom-plus | prboom|srb2 | 9 | 0.778 | n/a | n/a |
| unconfirmed | prboom-plus~srb2:prboom2/src/SDL | prboom-plus | prboom|srb2 | 5 | 0.200 | n/a | n/a |
| unconfirmed | sdl-doom~fastdoom:src | sdl-doom | fastdoom|sdl-doom | 17 | 0.765 | n/a | n/a |
| unconfirmed | sdl-doom~linuxdoom:src | sdl-doom | linuxdoom|sdl-doom | 18 | 1.000 | n/a | n/a |
| unconfirmed | sdl-doom~prboom-plus:src | sdl-doom | prboom|sdl-doom | 20 | 0.650 | n/a | n/a |
| unconfirmed | sdl-doom~woof:src | sdl-doom | sdl-doom|woof | 41 | 0.732 | n/a | n/a |
| unconfirmed | srb2~doom-wasm:src | srb2 | doom-wasm|srb2 | 23 | 0.043 | n/a | n/a |
| unconfirmed | srb2~doomgeneric:src | srb2 | doomgeneric|srb2 | 10 | 0.200 | n/a | n/a |
| unconfirmed | srb2~dsda-doom:src | srb2 | prboom|srb2 | 14 | 0.143 | n/a | n/a |
| unconfirmed | srb2~dsda-doom:src/hardware | srb2 | prboom|srb2 | 7 | 0.429 | n/a | n/a |
| unconfirmed | srb2~inter-doom:src | srb2 | chocolate|srb2 | 16 | 0.125 | n/a | n/a |
| unconfirmed | srb2~prboom-plus:src | srb2 | prboom|srb2 | 11 | 0.091 | n/a | n/a |
| unconfirmed | srb2~woof:src | srb2 | srb2|woof | 27 | 0.037 | n/a | n/a |
| unconfirmed | woof~chocolate-doom:src | woof | chocolate|woof | 194 | 0.526 | n/a | n/a |
| unconfirmed | woof~chocolate-doom:textscreen | woof | chocolate|woof | 6 | 0.500 | n/a | n/a |
| unconfirmed | woof~crispy-doom:src | woof | chocolate|woof | 16 | 0.000 | n/a | n/a |
| unconfirmed | woof~doom-ascii:src | woof | doom-ascii|woof | 29 | 0.034 | n/a | n/a |
| unconfirmed | woof~doom-wasm:opl | woof | doom-wasm|woof | 8 | 0.000 | n/a | n/a |
| unconfirmed | woof~doom-wasm:src | woof | doom-wasm|woof | 139 | 0.043 | n/a | n/a |
| unconfirmed | woof~doom-wasm:textscreen | woof | doom-wasm|woof | 198 | 0.576 | n/a | n/a |
| unconfirmed | woof~doom3do:src | woof | doom3do|woof | 5 | 0.200 | n/a | n/a |
| unconfirmed | woof~doomgeneric:src | woof | doomgeneric|woof | 36 | 0.056 | n/a | n/a |
| unconfirmed | woof~doomsday:src | woof | doomsday|woof | 7 | 0.143 | n/a | n/a |
| unconfirmed | woof~fastdoom:src | woof | fastdoom|woof | 10 | 0.300 | n/a | n/a |
| unconfirmed | woof~inter-doom:setup | woof | chocolate|woof | 5 | 1.000 | n/a | n/a |
| unconfirmed | woof~inter-doom:src | woof | chocolate|woof | 207 | 0.010 | n/a | n/a |
| unconfirmed | woof~inter-doom:textscreen | woof | chocolate|woof | 189 | 0.566 | n/a | n/a |
| unconfirmed | woof~linuxdoom:src | woof | linuxdoom|woof | 6 | 0.000 | n/a | n/a |
| unconfirmed | woof~odamex:src | woof | odamex|woof | 6 | 0.000 | n/a | n/a |
| unconfirmed | woof~odamex:textscreen | woof | odamex|woof | 11 | 0.545 | n/a | n/a |
| unconfirmed | woof~quake2:src | woof | quake2|woof | 10 | 0.000 | n/a | n/a |
| unconfirmed | woof~sdl-doom:src | woof | sdl-doom|woof | 35 | 0.057 | n/a | n/a |
| unconfirmed | woof~srb2:src | woof | srb2|woof | 112 | 0.018 | n/a | n/a |
| unconfirmed | woof~srb2:textscreen | woof | srb2|woof | 17 | 0.529 | n/a | n/a |

Falsification list (recipient dated strictly before donor): 20 function pairs.

| donor | recipient | donor_func | recipient_func | event_id | donor_date | recipient_date |
|---|---|---|---|---|---|---|
| chocolate-doom | eternity | 2242 | 8914 | chocolate-doom|eternity|source/textscreen | 2009-03-12T22:20:07+00:00 | 2009-03-06T18:26:27+00:00 |
| chocolate-doom | odamex | 2184 | 8315 | chocolate-doom|odamex|libraries/textscreen | 2010-01-26T00:59:02+00:00 | 2010-01-06T09:16:03+00:00 |
| chocolate-doom | odamex | 2243 | 8372 | chocolate-doom|odamex|libraries/textscreen | 2010-01-26T00:59:02+00:00 | 2010-01-06T09:16:03+00:00 |
| chocolate-doom | odamex | 2244 | 8373 | chocolate-doom|odamex|libraries/textscreen | 2010-01-26T00:59:02+00:00 | 2010-01-06T09:16:03+00:00 |
| chocolate-doom | odamex | 2245 | 8374 | chocolate-doom|odamex|libraries/textscreen | 2010-01-26T00:59:02+00:00 | 2010-01-06T09:16:03+00:00 |
| chocolate-doom | odamex | 2258 | 8387 | chocolate-doom|odamex|libraries/textscreen | 2010-01-26T00:59:02+00:00 | 2010-01-06T09:16:03+00:00 |
| chocolate-doom | odamex | 2342 | 8470 | chocolate-doom|odamex|libraries/textscreen | 2010-01-26T00:59:02+00:00 | 2010-01-06T09:16:03+00:00 |
| chocolate-doom | prboom-plus | 2258 | 465 | chocolate-doom|prboom-plus|prboom2/src/TEXTSCREEN | 2010-01-26T00:59:02+00:00 | 2009-12-25T19:32:18+00:00 |
| chocolate-doom | woof | 56 | 38 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-07-12T04:43:46+00:00 |
| chocolate-doom | woof | 62 | 44 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-06-18T13:14:56+00:00 |
| chocolate-doom | woof | 63 | 45 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-06-18T13:14:56+00:00 |
| chocolate-doom | woof | 71 | 53 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-06-18T13:14:56+00:00 |
| chocolate-doom | woof | 76 | 58 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-06-18T13:14:56+00:00 |
| chocolate-doom | woof | 77 | 59 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-07-12T04:43:46+00:00 |
| chocolate-doom | woof | 78 | 60 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-07-12T04:43:46+00:00 |
| chocolate-doom | woof | 86 | 68 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-06-18T13:14:56+00:00 |
| chocolate-doom | woof | 89 | 71 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-07-12T04:43:46+00:00 |
| chocolate-doom | woof | 90 | 72 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-07-12T04:43:46+00:00 |
| chocolate-doom | woof | 91 | 73 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-07-12T04:43:46+00:00 |
| chocolate-doom | woof | 92 | 74 | chocolate-doom|woof|opl | 2026-08-24T10:34:59+00:00 | 2026-06-18T13:14:56+00:00 |


## 8. Module clustering (post hoc, never used for matching)

| set | groups | mean_share | mean_dir | mean_comp |
|---|---|---|---|---|
| confirmed | 7 | 0.857 | 0.857 | 0.000 |
| unconfirmed | 286 | 0.567 | 0.567 | 0.000 |

| set | group | borrower | n | share | dir_share | comp_share | call_graph_used |
|---|---|---|---|---|---|---|---|
| confirmed | chocolate-doom|dsda-doom|prboom2/src/textscreen | dsda-doom | 4 | 0.000 | 0.000 | 0.000 | False |
| confirmed | chocolate-doom|eternity|source/textscreen | eternity | 224 | 1.000 | 1.000 | 0.000 | False |
| confirmed | chocolate-doom|odamex|libraries/textscreen/examples | odamex | 15 | 1.000 | 1.000 | 0.000 | False |
| confirmed | chocolate-doom|odamex|libraries/textscreen | odamex | 193 | 1.000 | 1.000 | 0.000 | False |
| confirmed | chocolate-doom|prboom-plus|prboom2/src/TEXTSCREEN | prboom-plus | 8 | 1.000 | 1.000 | 0.000 | False |
| confirmed | chocolate-doom|woof|opl | woof | 53 | 1.000 | 1.000 | 0.000 | False |
| confirmed | chocolate-doom|woof|textscreen | woof | 214 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | chocolate-doom~doom3do | chocolate-doom | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | chocolate-doom~doom3do | doom3do | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | chocolate-doom~dsda-doom | chocolate-doom | 55 | 0.727 | 0.727 | 0.000 | False |
| unconfirmed | chocolate-doom~dsda-doom | dsda-doom | 55 | 0.873 | 0.873 | 0.000 | False |
| unconfirmed | chocolate-doom~eternity | chocolate-doom | 19 | 0.316 | 0.316 | 0.000 | False |
| unconfirmed | chocolate-doom~eternity | eternity | 19 | 0.579 | 0.579 | 0.000 | False |
| unconfirmed | chocolate-doom~fastdoom | chocolate-doom | 28 | 0.679 | 0.679 | 0.000 | False |
| unconfirmed | chocolate-doom~fastdoom | fastdoom | 28 | 0.964 | 0.964 | 0.000 | False |
| unconfirmed | chocolate-doom~linuxdoom | chocolate-doom | 31 | 0.742 | 0.742 | 0.000 | False |
| unconfirmed | chocolate-doom~linuxdoom | linuxdoom | 31 | 0.839 | 0.839 | 0.000 | False |
| unconfirmed | chocolate-doom~nugget-doom | chocolate-doom | 42 | 0.571 | 0.571 | 0.000 | False |
| unconfirmed | chocolate-doom~nugget-doom | nugget-doom | 42 | 0.500 | 0.500 | 0.000 | False |
| unconfirmed | chocolate-doom~odamex | chocolate-doom | 18 | 0.722 | 0.722 | 0.000 | False |
| unconfirmed | chocolate-doom~odamex | odamex | 18 | 0.833 | 0.833 | 0.000 | False |
| unconfirmed | chocolate-doom~prboom-plus | chocolate-doom | 57 | 0.895 | 0.895 | 0.000 | False |
| unconfirmed | chocolate-doom~prboom-plus | prboom-plus | 57 | 0.930 | 0.930 | 0.000 | False |
| unconfirmed | chocolate-doom~quake | chocolate-doom | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | chocolate-doom~quake | quake | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | chocolate-doom~quake2 | chocolate-doom | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | chocolate-doom~quake2 | quake2 | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | chocolate-doom~srb2 | chocolate-doom | 13 | 0.385 | 0.385 | 0.000 | False |
| unconfirmed | chocolate-doom~srb2 | srb2 | 13 | 0.769 | 0.769 | 0.000 | False |
| unconfirmed | chocolate-doom~woof | chocolate-doom | 287 | 0.930 | 0.930 | 0.000 | False |
| unconfirmed | chocolate-doom~woof | woof | 287 | 0.916 | 0.916 | 0.000 | False |
| unconfirmed | crispy-doom~dsda-doom | crispy-doom | 9 | 0.778 | 0.778 | 0.000 | False |
| unconfirmed | crispy-doom~dsda-doom | dsda-doom | 9 | 0.667 | 0.667 | 0.000 | False |
| unconfirmed | crispy-doom~fastdoom | crispy-doom | 20 | 0.750 | 0.750 | 0.000 | False |
| unconfirmed | crispy-doom~fastdoom | fastdoom | 20 | 0.850 | 0.850 | 0.000 | False |
| unconfirmed | crispy-doom~linuxdoom | crispy-doom | 7 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | crispy-doom~linuxdoom | linuxdoom | 7 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | crispy-doom~nugget-doom | crispy-doom | 20 | 0.250 | 0.250 | 0.000 | False |
| unconfirmed | crispy-doom~nugget-doom | nugget-doom | 20 | 0.300 | 0.300 | 0.000 | False |
| unconfirmed | crispy-doom~prboom-plus | crispy-doom | 17 | 0.706 | 0.706 | 0.000 | False |
| unconfirmed | crispy-doom~prboom-plus | prboom-plus | 17 | 0.882 | 0.882 | 0.000 | False |
| unconfirmed | crispy-doom~quake | crispy-doom | 5 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | crispy-doom~quake | quake | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | crispy-doom~woof | crispy-doom | 43 | 0.581 | 0.581 | 0.000 | False |
| unconfirmed | crispy-doom~woof | woof | 43 | 0.674 | 0.674 | 0.000 | False |
| unconfirmed | curl~doomretro | curl | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~doomretro | doomretro | 7 | 0.857 | 0.857 | 0.000 | False |
| unconfirmed | curl~doomsday | curl | 10 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~doomsday | doomsday | 10 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~dsda-doom | curl | 12 | 0.500 | 0.500 | 0.000 | False |
| unconfirmed | curl~dsda-doom | dsda-doom | 12 | 0.417 | 0.417 | 0.000 | False |
| unconfirmed | curl~gzdoom | curl | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~gzdoom | gzdoom | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~inter-doom | curl | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~inter-doom | inter-doom | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~libuv | curl | 11 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~libuv | libuv | 11 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~prboom-plus | curl | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~prboom-plus | prboom-plus | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~quake | curl | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~quake | quake | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~quake2 | curl | 10 | 0.600 | 0.600 | 0.000 | False |
| unconfirmed | curl~quake2 | quake2 | 10 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | curl~srb2 | curl | 12 | 0.500 | 0.500 | 0.000 | False |
| unconfirmed | curl~srb2 | srb2 | 12 | 0.500 | 0.500 | 0.000 | False |
| unconfirmed | doom-ascii~dsda-doom | doom-ascii | 24 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doom-ascii~dsda-doom | dsda-doom | 24 | 0.917 | 0.917 | 0.000 | False |
| unconfirmed | doom-ascii~fastdoom | doom-ascii | 15 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doom-ascii~fastdoom | fastdoom | 15 | 0.933 | 0.933 | 0.000 | False |
| unconfirmed | doom-ascii~linuxdoom | doom-ascii | 19 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doom-ascii~linuxdoom | linuxdoom | 19 | 0.842 | 0.842 | 0.000 | False |
| unconfirmed | doom-ascii~prboom-plus | doom-ascii | 11 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doom-ascii~prboom-plus | prboom-plus | 11 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom-ascii~woof | doom-ascii | 44 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doom-ascii~woof | woof | 44 | 0.886 | 0.886 | 0.000 | False |
| unconfirmed | doom-ios~doomsday | doom-ios | 8 | 0.625 | 0.625 | 0.000 | False |
| unconfirmed | doom-ios~doomsday | doomsday | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom-ios~quake2 | doom-ios | 27 | 0.889 | 0.889 | 0.000 | False |
| unconfirmed | doom-ios~quake2 | quake2 | 27 | 0.630 | 0.630 | 0.000 | False |
| unconfirmed | doom-wasm~dsda-doom | doom-wasm | 51 | 0.922 | 0.922 | 0.000 | False |
| unconfirmed | doom-wasm~dsda-doom | dsda-doom | 51 | 0.922 | 0.922 | 0.000 | False |
| unconfirmed | doom-wasm~eternity | doom-wasm | 196 | 0.985 | 0.985 | 0.000 | False |
| unconfirmed | doom-wasm~eternity | eternity | 196 | 0.990 | 0.990 | 0.000 | False |
| unconfirmed | doom-wasm~fastdoom | doom-wasm | 40 | 0.950 | 0.950 | 0.000 | False |
| unconfirmed | doom-wasm~fastdoom | fastdoom | 40 | 0.950 | 0.950 | 0.000 | False |
| unconfirmed | doom-wasm~linuxdoom | doom-wasm | 22 | 0.773 | 0.773 | 0.000 | False |
| unconfirmed | doom-wasm~linuxdoom | linuxdoom | 22 | 0.773 | 0.773 | 0.000 | False |
| unconfirmed | doom-wasm~nugget-doom | doom-wasm | 20 | 0.750 | 0.750 | 0.000 | False |
| unconfirmed | doom-wasm~nugget-doom | nugget-doom | 20 | 0.950 | 0.950 | 0.000 | False |
| unconfirmed | doom-wasm~odamex | doom-wasm | 183 | 0.989 | 0.989 | 0.000 | False |
| unconfirmed | doom-wasm~odamex | odamex | 183 | 0.989 | 0.989 | 0.000 | False |
| unconfirmed | doom-wasm~prboom-plus | doom-wasm | 47 | 0.872 | 0.872 | 0.000 | False |
| unconfirmed | doom-wasm~prboom-plus | prboom-plus | 47 | 0.894 | 0.894 | 0.000 | False |
| unconfirmed | doom-wasm~srb2 | doom-wasm | 88 | 0.932 | 0.932 | 0.000 | False |
| unconfirmed | doom-wasm~srb2 | srb2 | 88 | 0.898 | 0.898 | 0.000 | False |
| unconfirmed | doom-wasm~woof | doom-wasm | 387 | 0.987 | 0.987 | 0.000 | False |
| unconfirmed | doom-wasm~woof | woof | 387 | 0.995 | 0.995 | 0.000 | False |
| unconfirmed | doom3-bfg~doomsday | doom3-bfg | 10 | 0.700 | 0.700 | 0.000 | False |
| unconfirmed | doom3-bfg~doomsday | doomsday | 10 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3-bfg~eternity | doom3-bfg | 9 | 0.556 | 0.556 | 0.000 | False |
| unconfirmed | doom3-bfg~eternity | eternity | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3-bfg~gzdoom | doom3-bfg | 8 | 0.875 | 0.875 | 0.000 | False |
| unconfirmed | doom3-bfg~gzdoom | gzdoom | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3-bfg~odamex | doom3-bfg | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3-bfg~odamex | odamex | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3do~doomretro | doom3do | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3do~doomretro | doomretro | 5 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doom3do~dsda-doom | doom3do | 5 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doom3do~dsda-doom | dsda-doom | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3do~fastdoom | doom3do | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3do~fastdoom | fastdoom | 6 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doom3do~prboom-plus | doom3do | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3do~prboom-plus | prboom-plus | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3do~quake | doom3do | 9 | 0.667 | 0.667 | 0.000 | False |
| unconfirmed | doom3do~quake | quake | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3do~quake2 | doom3do | 6 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doom3do~quake2 | quake2 | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3do~woof | doom3do | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doom3do~woof | woof | 5 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomgeneric~fastdoom | doomgeneric | 20 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomgeneric~fastdoom | fastdoom | 20 | 0.950 | 0.950 | 0.000 | False |
| unconfirmed | doomgeneric~nugget-doom | doomgeneric | 5 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomgeneric~nugget-doom | nugget-doom | 5 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomgeneric~prboom-plus | doomgeneric | 17 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomgeneric~prboom-plus | prboom-plus | 17 | 0.765 | 0.765 | 0.000 | False |
| unconfirmed | doomgeneric~srb2 | doomgeneric | 45 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomgeneric~srb2 | srb2 | 45 | 0.844 | 0.844 | 0.000 | False |
| unconfirmed | doomgeneric~woof | doomgeneric | 47 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomgeneric~woof | woof | 47 | 0.936 | 0.936 | 0.000 | False |
| unconfirmed | doomretro~doomsday | doomretro | 6 | 0.833 | 0.833 | 0.000 | False |
| unconfirmed | doomretro~doomsday | doomsday | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomretro~dsda-doom | doomretro | 12 | 0.917 | 0.917 | 0.000 | False |
| unconfirmed | doomretro~dsda-doom | dsda-doom | 12 | 0.833 | 0.833 | 0.000 | False |
| unconfirmed | doomretro~linuxdoom | doomretro | 6 | 0.833 | 0.833 | 0.000 | False |
| unconfirmed | doomretro~linuxdoom | linuxdoom | 6 | 0.833 | 0.833 | 0.000 | False |
| unconfirmed | doomretro~quake | doomretro | 10 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomretro~quake | quake | 10 | 0.500 | 0.500 | 0.000 | False |
| unconfirmed | doomretro~quake2 | doomretro | 5 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomretro~quake2 | quake2 | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomretro~srb2 | doomretro | 14 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomretro~srb2 | srb2 | 14 | 0.571 | 0.571 | 0.000 | False |
| unconfirmed | doomretro~woof | doomretro | 10 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | doomretro~woof | woof | 10 | 0.900 | 0.900 | 0.000 | False |
| unconfirmed | doomsday~dsda-doom | doomsday | 11 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~dsda-doom | dsda-doom | 11 | 0.727 | 0.727 | 0.000 | False |
| unconfirmed | doomsday~edge-classic | doomsday | 188 | 0.245 | 0.245 | 0.000 | False |
| unconfirmed | doomsday~edge-classic | edge-classic | 188 | 0.936 | 0.936 | 0.000 | False |
| unconfirmed | doomsday~eternity | doomsday | 272 | 0.371 | 0.371 | 0.000 | False |
| unconfirmed | doomsday~eternity | eternity | 272 | 0.901 | 0.901 | 0.000 | False |
| unconfirmed | doomsday~fastdoom | doomsday | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~fastdoom | fastdoom | 8 | 0.750 | 0.750 | 0.000 | False |
| unconfirmed | doomsday~gzdoom | doomsday | 289 | 0.356 | 0.356 | 0.000 | False |
| unconfirmed | doomsday~gzdoom | gzdoom | 289 | 0.478 | 0.478 | 0.000 | False |
| unconfirmed | doomsday~inter-doom | doomsday | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~inter-doom | inter-doom | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~libuv | doomsday | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~libuv | libuv | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~linuxdoom | doomsday | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~linuxdoom | linuxdoom | 7 | 0.857 | 0.857 | 0.000 | False |
| unconfirmed | doomsday~odamex | doomsday | 186 | 0.226 | 0.226 | 0.000 | False |
| unconfirmed | doomsday~odamex | odamex | 186 | 0.796 | 0.796 | 0.000 | False |
| unconfirmed | doomsday~prboom-plus | doomsday | 13 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~prboom-plus | prboom-plus | 13 | 0.769 | 0.769 | 0.000 | False |
| unconfirmed | doomsday~quake | doomsday | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~quake | quake | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~srb2 | doomsday | 23 | 0.217 | 0.217 | 0.000 | False |
| unconfirmed | doomsday~srb2 | srb2 | 23 | 0.348 | 0.348 | 0.000 | False |
| unconfirmed | doomsday~woof | doomsday | 12 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | doomsday~woof | woof | 12 | 0.750 | 0.750 | 0.000 | False |
| unconfirmed | dsda-doom~fastdoom | dsda-doom | 56 | 0.929 | 0.929 | 0.000 | False |
| unconfirmed | dsda-doom~fastdoom | fastdoom | 56 | 0.982 | 0.982 | 0.000 | False |
| unconfirmed | dsda-doom~gzdoom | dsda-doom | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | dsda-doom~gzdoom | gzdoom | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | dsda-doom~inter-doom | dsda-doom | 94 | 0.904 | 0.904 | 0.000 | False |
| unconfirmed | dsda-doom~inter-doom | inter-doom | 94 | 0.926 | 0.926 | 0.000 | False |
| unconfirmed | dsda-doom~linuxdoom | dsda-doom | 11 | 0.818 | 0.818 | 0.000 | False |
| unconfirmed | dsda-doom~linuxdoom | linuxdoom | 11 | 0.818 | 0.818 | 0.000 | False |
| unconfirmed | dsda-doom~odamex | dsda-doom | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | dsda-doom~odamex | odamex | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | dsda-doom~quake | dsda-doom | 20 | 0.950 | 0.950 | 0.000 | False |
| unconfirmed | dsda-doom~quake | quake | 20 | 0.900 | 0.900 | 0.000 | False |
| unconfirmed | dsda-doom~quake2 | dsda-doom | 22 | 0.909 | 0.909 | 0.000 | False |
| unconfirmed | dsda-doom~quake2 | quake2 | 22 | 0.773 | 0.773 | 0.000 | False |
| unconfirmed | dsda-doom~srb2 | dsda-doom | 132 | 0.947 | 0.947 | 0.000 | False |
| unconfirmed | dsda-doom~srb2 | srb2 | 132 | 0.962 | 0.962 | 0.000 | False |
| unconfirmed | edge-classic~gzdoom | edge-classic | 225 | 0.956 | 0.956 | 0.000 | False |
| unconfirmed | edge-classic~gzdoom | gzdoom | 225 | 0.502 | 0.502 | 0.000 | False |
| unconfirmed | edge-classic~odamex | edge-classic | 106 | 0.906 | 0.906 | 0.000 | False |
| unconfirmed | edge-classic~odamex | odamex | 106 | 0.821 | 0.821 | 0.000 | False |
| unconfirmed | edge-classic~srb2 | edge-classic | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | edge-classic~srb2 | srb2 | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | eternity~gzdoom | eternity | 264 | 0.913 | 0.913 | 0.000 | False |
| unconfirmed | eternity~gzdoom | gzdoom | 264 | 0.564 | 0.564 | 0.000 | False |
| unconfirmed | eternity~inter-doom | eternity | 196 | 0.964 | 0.964 | 0.000 | False |
| unconfirmed | eternity~inter-doom | inter-doom | 196 | 0.949 | 0.949 | 0.000 | False |
| unconfirmed | eternity~odamex | eternity | 269 | 0.926 | 0.926 | 0.000 | False |
| unconfirmed | eternity~odamex | odamex | 269 | 0.874 | 0.874 | 0.000 | False |
| unconfirmed | fastdoom~gzdoom | fastdoom | 8 | 0.875 | 0.875 | 0.000 | False |
| unconfirmed | fastdoom~gzdoom | gzdoom | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | fastdoom~inter-doom | fastdoom | 19 | 0.947 | 0.947 | 0.000 | False |
| unconfirmed | fastdoom~inter-doom | inter-doom | 19 | 0.842 | 0.842 | 0.000 | False |
| unconfirmed | fastdoom~linuxdoom | fastdoom | 31 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | fastdoom~linuxdoom | linuxdoom | 31 | 0.903 | 0.903 | 0.000 | False |
| unconfirmed | fastdoom~prboom-plus | fastdoom | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | fastdoom~prboom-plus | prboom-plus | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | fastdoom~puredoom | fastdoom | 8 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | fastdoom~puredoom | puredoom | 8 | 0.625 | 0.625 | 0.000 | False |
| unconfirmed | fastdoom~quake | fastdoom | 87 | 0.943 | 0.943 | 0.000 | False |
| unconfirmed | fastdoom~quake | quake | 87 | 0.966 | 0.966 | 0.000 | False |
| unconfirmed | fastdoom~quake2 | fastdoom | 8 | 0.875 | 0.875 | 0.000 | False |
| unconfirmed | fastdoom~quake2 | quake2 | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | fastdoom~sdl-doom | fastdoom | 18 | 0.944 | 0.944 | 0.000 | False |
| unconfirmed | fastdoom~sdl-doom | sdl-doom | 18 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | fastdoom~srb2 | fastdoom | 13 | 0.923 | 0.923 | 0.000 | False |
| unconfirmed | fastdoom~srb2 | srb2 | 13 | 0.538 | 0.538 | 0.000 | False |
| unconfirmed | fastdoom~woof | fastdoom | 14 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | fastdoom~woof | woof | 14 | 0.929 | 0.929 | 0.000 | False |
| unconfirmed | gzdoom~leveldb | gzdoom | 20 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~leveldb | leveldb | 20 | 0.600 | 0.600 | 0.000 | False |
| unconfirmed | gzdoom~libuv | gzdoom | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~libuv | libuv | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~linuxdoom | gzdoom | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~linuxdoom | linuxdoom | 5 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | gzdoom~prboom-plus | gzdoom | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~prboom-plus | prboom-plus | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~quake2 | gzdoom | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~quake2 | quake2 | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~srb2 | gzdoom | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~srb2 | srb2 | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~woof | gzdoom | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | gzdoom~woof | woof | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | inter-doom~linuxdoom | inter-doom | 37 | 0.973 | 0.973 | 0.000 | False |
| unconfirmed | inter-doom~linuxdoom | linuxdoom | 37 | 0.919 | 0.919 | 0.000 | False |
| unconfirmed | inter-doom~nugget-doom | inter-doom | 30 | 0.867 | 0.867 | 0.000 | False |
| unconfirmed | inter-doom~nugget-doom | nugget-doom | 30 | 0.867 | 0.867 | 0.000 | False |
| unconfirmed | inter-doom~odamex | inter-doom | 172 | 0.953 | 0.953 | 0.000 | False |
| unconfirmed | inter-doom~odamex | odamex | 172 | 0.965 | 0.965 | 0.000 | False |
| unconfirmed | inter-doom~prboom-plus | inter-doom | 61 | 0.902 | 0.902 | 0.000 | False |
| unconfirmed | inter-doom~prboom-plus | prboom-plus | 61 | 0.967 | 0.967 | 0.000 | False |
| unconfirmed | inter-doom~puredoom | inter-doom | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | inter-doom~puredoom | puredoom | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | inter-doom~quake2 | inter-doom | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | inter-doom~quake2 | quake2 | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | inter-doom~srb2 | inter-doom | 88 | 0.920 | 0.920 | 0.000 | False |
| unconfirmed | inter-doom~srb2 | srb2 | 88 | 0.886 | 0.886 | 0.000 | False |
| unconfirmed | inter-doom~woof | inter-doom | 468 | 0.987 | 0.987 | 0.000 | False |
| unconfirmed | inter-doom~woof | woof | 468 | 0.989 | 0.989 | 0.000 | False |
| unconfirmed | libuv~prboom-plus | libuv | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | libuv~prboom-plus | prboom-plus | 5 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | libuv~quake | libuv | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | libuv~quake | quake | 7 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | libuv~srb2 | libuv | 9 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | libuv~srb2 | srb2 | 9 | 0.556 | 0.556 | 0.000 | False |
| unconfirmed | linuxdoom~puredoom | linuxdoom | 9 | 0.889 | 0.889 | 0.000 | False |
| unconfirmed | linuxdoom~puredoom | puredoom | 9 | 0.556 | 0.556 | 0.000 | False |
| unconfirmed | linuxdoom~quake | linuxdoom | 8 | 0.750 | 0.750 | 0.000 | False |
| unconfirmed | linuxdoom~quake | quake | 8 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | linuxdoom~quake2 | linuxdoom | 10 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | linuxdoom~quake2 | quake2 | 10 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | linuxdoom~sdl-doom | linuxdoom | 19 | 0.842 | 0.842 | 0.000 | False |
| unconfirmed | linuxdoom~sdl-doom | sdl-doom | 19 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | linuxdoom~srb2 | linuxdoom | 13 | 0.846 | 0.846 | 0.000 | False |
| unconfirmed | linuxdoom~srb2 | srb2 | 13 | 0.769 | 0.769 | 0.000 | False |
| unconfirmed | linuxdoom~woof | linuxdoom | 7 | 0.857 | 0.857 | 0.000 | False |
| unconfirmed | linuxdoom~woof | woof | 7 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | lua~srb2 | lua | 106 | 0.981 | 0.981 | 0.000 | False |
| unconfirmed | lua~srb2 | srb2 | 106 | 0.953 | 0.953 | 0.000 | False |
| unconfirmed | nugget-doom~quake2 | nugget-doom | 6 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | nugget-doom~quake2 | quake2 | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | odamex~quake2 | odamex | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | odamex~quake2 | quake2 | 6 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | odamex~srb2 | odamex | 14 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | odamex~srb2 | srb2 | 14 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | odamex~woof | odamex | 20 | 0.800 | 0.800 | 0.000 | False |
| unconfirmed | odamex~woof | woof | 20 | 0.850 | 0.850 | 0.000 | False |
| unconfirmed | prboom-plus~quake | prboom-plus | 9 | 0.556 | 0.556 | 0.000 | False |
| unconfirmed | prboom-plus~quake | quake | 9 | 0.556 | 0.556 | 0.000 | False |
| unconfirmed | prboom-plus~sdl-doom | prboom-plus | 20 | 0.750 | 0.750 | 0.000 | False |
| unconfirmed | prboom-plus~sdl-doom | sdl-doom | 20 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | prboom-plus~srb2 | prboom-plus | 54 | 0.963 | 0.963 | 0.000 | False |
| unconfirmed | prboom-plus~srb2 | srb2 | 54 | 0.796 | 0.796 | 0.000 | False |
| unconfirmed | quake~quake2 | quake | 277 | 0.473 | 0.473 | 0.000 | False |
| unconfirmed | quake~quake2 | quake2 | 277 | 0.462 | 0.462 | 0.000 | False |
| unconfirmed | quake~srb2 | quake | 14 | 0.500 | 0.500 | 0.000 | False |
| unconfirmed | quake~srb2 | srb2 | 14 | 0.929 | 0.929 | 0.000 | False |
| unconfirmed | quake2~srb2 | quake2 | 14 | 0.357 | 0.357 | 0.000 | False |
| unconfirmed | quake2~srb2 | srb2 | 14 | 0.500 | 0.500 | 0.000 | False |
| unconfirmed | quake2~woof | quake2 | 12 | 0.000 | 0.000 | 0.000 | False |
| unconfirmed | quake2~woof | woof | 12 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | sdl-doom~woof | sdl-doom | 43 | 1.000 | 1.000 | 0.000 | False |
| unconfirmed | sdl-doom~woof | woof | 43 | 0.953 | 0.953 | 0.000 | False |
| unconfirmed | srb2~woof | srb2 | 167 | 0.904 | 0.904 | 0.000 | False |
| unconfirmed | srb2~woof | woof | 167 | 0.952 | 0.952 | 0.000 | False |


## 9. H9.5: what each predictor misses (every miss listed in h95_misses.csv with a reason code)

| predictor | variant | flavour | reason | n_missed |
|---|---|---|---|---|
| geometry | primary | all | not_selected | 957 |
| geometry | primary | all | other_partner_emitted | 1070 |
| geometry | primary | all | unmapped_engine_row | 4697 |
| names | unique_key | all | key_not_unique | 135 |
| names | unique_key | all | key_unusable_or_stoplisted | 101 |
| names | unique_key | all | no_match_unexplained | 1 |
| names | unique_key | all | renamed_key_differs | 69 |
| names | unique_key | all | reprefixed_matches_only_under_n2 | 16 |
| names | unique_key | all | unmapped_engine_row | 4697 |
| names | unique_key | cert | key_not_unique | 135 |
| names | unique_key | cert | key_unusable_or_stoplisted | 101 |
| names | unique_key | cert | no_match_unexplained | 1 |
| names | unique_key | cert | renamed_key_differs | 69 |
| names | unique_key | cert | reprefixed_matches_only_under_n2 | 16 |
| names | unique_key | cert | unmapped_engine_row | 4697 |
| r1 | primary | all | not_selected | 346 |
| r1 | primary | all | other_partner_emitted | 2058 |
| r1 | primary | all | unmapped_engine_row | 4697 |
| structure | primary | all | duplicated_body_blocks_reciprocal_hit | 81 |
| structure | primary | all | no_reciprocal_distinct_twin_under_fdr | 245 |
| structure | primary | all | other_partner_emitted | 230 |
| structure | primary | all | unmapped_engine_row | 4697 |


## 10. Calibration diagnostics (sfs decoy hits are NOT a predictor)

| prog_a | prog_b | variant | k_struct | k_names | budget | twins_ab | twins_ba | decoy_hits_ab | decoy_hits_ba | thr_ab | thr_ba | names_certified | decoy_ge_ab | decoy_ge_ba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chocolate-doom | doom3-bfg | primary | 0 | 91 | 91 | 0 | 0 | 0 | 0 | 0.000 | 0.000 | 1 | 0 | 0 |
| chocolate-doom | doom3-bfg | dedup | 0 | 89 | 89 | 0 | 0 | 0 | 0 | 0.000 | 0.000 | 1 | 0 | 0 |
| chocolate-doom | doom3do | primary | 5 | 11 | 11 | 7 | 5 | 0 | 0 | 0.000 | 0.000 | 1 | 0 | 0 |
| chocolate-doom | doom3do | dedup | 4 | 11 | 11 | 7 | 6 | 0 | 0 | 0.000 | 0.000 | 1 | 0 | 0 |
| chocolate-doom | dsda-doom | primary | 113 | 168 | 168 | 214 | 223 | 1 | 1 | 0.046 | 0.046 | 1 | 0 | 0 |
| chocolate-doom | dsda-doom | dedup | 119 | 168 | 168 | 189 | 237 | 0 | 1 | 0.035 | 0.053 | 1 | 0 | 0 |
| chocolate-doom | edge-classic | primary | 2 | 0 | 5 | 1 | 2 | 0 | 0 | 0.000 | 0.000 | 0 | 182 | 200 |
| chocolate-doom | edge-classic | dedup | 2 | 0 | 5 | 1 | 3 | 0 | 0 | 0.000 | 0.000 | 0 | 187 | 200 |
| chocolate-doom | eternity | primary | 208 | 400 | 400 | 209 | 196 | 1 | 0 | 0.077 | 0.064 | 1 | 0 | 0 |
| chocolate-doom | eternity | dedup | 212 | 396 | 396 | 214 | 204 | 1 | 1 | 0.086 | 0.076 | 1 | 0 | 0 |
| chocolate-doom | fastdoom | primary | 29 | 72 | 72 | 101 | 29 | 0 | 0 | 0.040 | 0.000 | 1 | 0 | 0 |
| chocolate-doom | fastdoom | dedup | 39 | 73 | 73 | 129 | 102 | 0 | 0 | 0.048 | 0.039 | 1 | 0 | 0 |
| chocolate-doom | gzdoom | primary | 2 | 37 | 37 | 3 | 4 | 0 | 0 | 0.000 | 0.000 | 1 | 0 | 200 |
| chocolate-doom | gzdoom | dedup | 1 | 37 | 37 | 2 | 4 | 0 | 0 | 0.000 | 0.000 | 1 | 0 | 200 |
| chocolate-doom | linuxdoom | primary | 31 | 116 | 116 | 370 | 385 | 2 | 2 | 0.058 | 0.077 | 1 | 0 | 0 |
| chocolate-doom | linuxdoom | dedup | 24 | 115 | 115 | 365 | 373 | 1 | 2 | 0.053 | 0.061 | 1 | 0 | 0 |
| chocolate-doom | nugget-doom | primary | 93 | 98 | 98 | 658 | 676 | 5 | 4 | 0.060 | 0.062 | 1 | 0 | 0 |
| chocolate-doom | nugget-doom | dedup | 96 | 99 | 99 | 669 | 687 | 5 | 5 | 0.064 | 0.065 | 1 | 0 | 0 |
| chocolate-doom | odamex | primary | 186 | 337 | 337 | 186 | 178 | 0 | 0 | 0.049 | 0.014 | 1 | 0 | 0 |
| chocolate-doom | odamex | dedup | 187 | 334 | 334 | 181 | 185 | 0 | 0 | 0.027 | 0.049 | 1 | 0 | 0 |
| chocolate-doom | prboom-plus | primary | 104 | 194 | 194 | 190 | 184 | 0 | 0 | 0.053 | 0.055 | 1 | 0 | 0 |
| chocolate-doom | prboom-plus | dedup | 101 | 193 | 193 | 190 | 161 | 0 | 0 | 0.053 | 0.043 | 1 | 0 | 0 |
| chocolate-doom | quake | primary | 9 | 0 | 9 | 7 | 11 | 0 | 0 | 0.000 | 0.000 | 0 | 200 | 200 |
| chocolate-doom | quake | dedup | 9 | 2 | 9 | 12 | 13 | 0 | 0 | 0.000 | 0.000 | 0 | 200 | 200 |
| chocolate-doom | quake2 | primary | 6 | 3 | 6 | 10 | 10 | 0 | 0 | 0.000 | 0.000 | 0 | 200 | 200 |
| chocolate-doom | quake2 | dedup | 6 | 2 | 6 | 10 | 10 | 0 | 0 | 0.000 | 0.000 | 0 | 200 | 200 |
| chocolate-doom | srb2 | primary | 13 | 56 | 56 | 18 | 17 | 0 | 0 | 0.000 | 0.000 | 1 | 0 | 200 |
| chocolate-doom | srb2 | dedup | 12 | 55 | 55 | 18 | 18 | 0 | 0 | 0.000 | 0.000 | 1 | 0 | 200 |
| chocolate-doom | woof | primary | 632 | 640 | 640 | 663 | 685 | 4 | 5 | 0.063 | 0.064 | 1 | 0 | 0 |
| chocolate-doom | woof | dedup | 625 | 635 | 635 | 657 | 674 | 5 | 5 | 0.059 | 0.060 | 1 | 0 | 0 |
| crispy-doom | dsda-doom | primary | 10 | 71 | 71 | 166 | 194 | 0 | 0 | 0.031 | 0.038 | 1 | 0 | 0 |
| crispy-doom | dsda-doom | dedup | 23 | 71 | 71 | 222 | 249 | 1 | 1 | 0.049 | 0.055 | 1 | 0 | 0 |
| crispy-doom | fastdoom | primary | 20 | 72 | 72 | 121 | 135 | 0 | 0 | 0.051 | 0.056 | 1 | 0 | 0 |
| crispy-doom | fastdoom | dedup | 9 | 72 | 72 | 26 | 107 | 0 | 0 | 0.000 | 0.044 | 1 | 0 | 0 |
| crispy-doom | gzdoom | primary | 2 | 37 | 37 | 3 | 5 | 0 | 0 | 0.000 | 0.000 | 1 | 0 | 200 |
| crispy-doom | gzdoom | dedup | 2 | 37 | 37 | 2 | 5 | 0 | 0 | 0.000 | 0.000 | 1 | 0 | 200 |
| crispy-doom | linuxdoom | primary | 7 | 130 | 130 | 245 | 244 | 1 | 1 | 0.054 | 0.052 | 1 | 0 | 0 |
| crispy-doom | linuxdoom | dedup | 7 | 130 | 130 | 243 | 257 | 1 | 1 | 0.053 | 0.068 | 1 | 0 | 0 |
| crispy-doom | nugget-doom | primary | 20 | 54 | 54 | 677 | 671 | 5 | 5 | 0.061 | 0.056 | 1 | 0 | 0 |
| crispy-doom | nugget-doom | dedup | 22 | 55 | 55 | 718 | 702 | 6 | 6 | 0.075 | 0.066 | 1 | 0 | 0 |

(first 40 rows; full table in calibration_diag.csv)

