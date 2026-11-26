# E14 confirmatory results (registered analysis)

379 mutants attempted, 373 built; functions: agree 15, disagree 15.

## Build, reach, kill, crash by role

| role | attempted | built | reached | killed (>=1) | crash/hang |
|---|---|---|---|---|---|
| ch | 88 | 87 | 85 | 51 | 3 |
| pb:match | 48 | 47 | 44 | 25 | 0 |
| pb:ctl | 87 | 86 | 65 | 24 | 2 |
| md:match | 45 | 44 | 41 | 22 | 6 |
| md:name | 23 | 23 | 23 | 15 | 0 |
| md:ctl | 88 | 86 | 58 | 31 | 3 |

## Registered predictions

| prediction | registered | observed | result |
|---|---|---|---|
| S1 (primary) | agree, managed-doom: matched - permutation control >= 0.40, 95% lower bound > 0.25, >= 10 functions | 12 functions; diff +0.61 (95% +0.44 to +0.73); matched mean 0.87; control mean 0.23 | PASSED |
| S2 | matched - same-file control >= 0.30 | 10 functions; +0.69 (95% +0.47 to +0.88) | PASSED |
| S3 | agree - disagree | no kill pairs in one stratum | INCONCLUSIVE |
| S4 | role-blind only if the matched - control interval lies inside +-0.15 | interval +0.44 to +0.73 | not role-blind |
| S5 | tic (+-1) and first-field agreement >= 0.80 (agree, managed-doom) | 21 kill pairs; tic 0.86; field 0.99 | PASSED |
| S6 | name-oracle target closer to the reference break than the matcher target (sign test) | name closer 1, matcher closer 0, ties 0; two-sided p 1.000 | PASSED |
| S7 | prboom-plus agree stratum matched Jaccard >= 0.70 | 4 functions; mean 0.88 | PASSED |

## Sensitivity and descriptive

* agree stratum, managed-doom, all 42 demos: 12 functions with kill pairs; matched - control +0.61 (95% +0.44 to +0.73)
* agree stratum, managed-doom, bot demos only: 8 functions with kill pairs; matched - control +0.58 (95% +0.25 to +0.82)
* agree stratum, managed-doom, sticky only: 12 functions with kill pairs; matched - control +0.58 (95% +0.42 to +0.72)
* agree stratum, managed-doom, chaos only: 12 functions with kill pairs; matched - control +0.52 (95% +0.32 to +0.69)
* per stratum, managed-doom matched: agree 12 functions, disagree 0 functions with kill pairs; prboom-plus matched: agree 4, disagree 8
* strict (not dead-angle-ignoring) comparison: not stored by this run's outcome records; not computed (deviation from the registered list).

## Per function (matched Jaccard, managed-doom and prboom-plus; kill pairs only)

| function | stratum | md matched | pb matched |
|---|---|---|---|
| A_Look | disagree | nan | nan |
| A_PosAttack | disagree | nan | 1.00 |
| A_Punch | disagree | nan | 1.00 |
| A_SPosAttack | disagree | nan | nan |
| EV_VerticalDoor | disagree | nan | nan |
| PIT_AddLineIntercepts | agree | 1.00 | 1.00 |
| PIT_ChangeSector | disagree | nan | nan |
| PIT_CheckLine | agree | 1.00 | nan |
| PIT_CheckThing | agree | 1.00 | 1.00 |
| PTR_ShootTraverse | agree | nan | 0.88 |
| P_AimLineAttack | disagree | nan | 1.00 |
| P_CheckMeleeRange | disagree | nan | 0.94 |
| P_CheckMissileRange | agree | nan | nan |
| P_CheckMissileSpawn | agree | 0.62 | 0.62 |
| P_DeathThink | disagree | nan | nan |
| P_FindSectorFromLineTag | agree | 0.44 | nan |
| P_InterceptVector | disagree | nan | nan |
| P_LookForPlayers | agree | 1.00 | nan |
| P_Move | agree | 1.00 | nan |
| P_PathTraverse | disagree | nan | 0.44 |
| P_SetThingPosition | disagree | nan | nan |
| P_SlideMove | disagree | nan | 0.96 |
| P_SpawnLightFlash | agree | 1.00 | nan |
| P_SpawnMapThing | agree | 0.50 | nan |
| P_SpawnMissile | disagree | nan | 1.00 |
| P_SpawnMobj | agree | 1.00 | nan |
| P_SpawnStrobeFlash | agree | nan | nan |
| P_TryMove | agree | 1.00 | nan |
| P_UseLines | disagree | nan | 0.56 |
| P_ZMovement | agree | 0.87 | nan |
## Post hoc notes (not registered; added after reading the table above)
* **The disagree stratum was not testable with this design.** Of 42 reference sites in the disagree stratum, only 3 had an aligned managed-doom mutant at the matcher's target (agree stratum: 41 of 45), because the matcher's target functions have different code, so the site alignment (operator plus surrounding tokens) finds almost nothing to pair. S3 is therefore inconclusive by the registered rule, and S6 (1 vs 0) is not meaningful although the registered "more often than not" rule technically passes.
* The agree stratum is defined by name agreement, so a positive result there says: where the matcher's pick and the function name agree, the code behaves alike across a faithful translation. It does not show the matcher is right where it disagrees with the names.
* Crash/hang: managed-doom matched mutants 6 of 44; excluded from the Jaccard.
* Not run: strict (non dead-angle-ignoring) comparison.
