# E14 pilot results (non-confirmatory; Phase 0)

102 mutants built or attempted; seed 20261127; 42 demos (20 sticky, 10 chaos, 12 bot); scored against each port's own clean run on the common columns (world fingerprint included, no RNG index).

## Build, coverage and survival by port and role

| port:role | attempted | built | reached by >=1 demo | killed (>=1 demo) | killed among reached | crash/hang |
|---|---|---|---|---|---|---|
| ch | 36 | 33 | 27 | 13 | 13/27 | 0 |
| pb:match | 31 | 28 | 21 | 9 | 9/21 | 0 |
| md:match | 24 | 0 | 0 | 0 | 0/0 | 0 |
| md:name | 11 | 0 | 0 | 0 | 0/0 | 0 |

## Aligned site pairs

Reference-port sites chosen: 33; with a prboom-plus match: 28; with a managed-doom matcher target: 0.

## Agreement with chocolate-doom (matched and control pairs)

Pairs are (chocolate mutant, target mutant) with both functions reached by at least one common demo. `kill pairs` = at least one of the two killed; the Jaccard is of the failing-demo sets on demos reaching both.

| comparison | pairs reached | kill pairs | both survive | mean Jaccard (kill pairs) | tic agree (+-1) | first-field agree |
|---|---|---|---|---|---|---|
| pb:match (matched) | 21 | 11 | 10 | 0.82 | 1.00 | 1.00 |
| pb:match (control: other function, same operator) | 111 | 57 | 54 | 0.10 | 0.00 | 0.09 |
| pb:name (matched) | 0 | 0 | 0 | nan | nan | nan |
| pb:name (control: other function, same operator) | 0 | 0 | 0 | nan | nan | nan |
| md:match (matched) | 0 | 0 | 0 | nan | nan | nan |
| md:match (control: other function, same operator) | 0 | 0 | 0 | nan | nan | nan |
| md:name (matched) | 0 | 0 | 0 | nan | nan | nan |
| md:name (control: other function, same operator) | 0 | 0 | 0 | nan | nan | nan |

## Where the matcher and the function names disagree (same reference function, two candidate targets)

| ref function | port | matcher target | name target | Jaccard vs matcher | Jaccard vs name | winner |
|---|---|---|---|---|---|---|

## Variance for power (kill pairs, Jaccard, per reference function)

* pb:match: 7 functions with kill pairs; mean of function means 0.86; sd between functions 0.35
* md:match: no kill pairs

## Detail: every aligned site (reached / killed demos out of 42)

| ref | site | kind | ch | pb:match | pb:name | md:match | md:name |
|---|---|---|---|---|---|---|---|
| A_Chase | 8 | arithmetic | 26/26 |  |  |  |  |
| A_Chase | 13 | relational | 26/26 | 26/26 |  |  |  |
| A_Chase | 16 | equality | 26/22 | 26/22 |  |  |  |
| A_SpawnFly | 0 | constant | 0/0 | 0/0 |  |  |  |
| A_SpawnFly | 2 | constant | 0/0 | 0/0 |  |  |  |
| A_SpawnFly | 7 | constant | 0/0 | 0/0 |  |  |  |
| EV_DoDoor | 0 | relational | 1/0 | 0/0 |  |  |  |
| EV_DoDoor | 2 | constant | 1/0 |  |  |  |  |
| EV_DoDoor | 6 | equality | 1/0 |  |  |  |  |
| EV_DoFloor | 8 | equality | 7/0 | 7/0 |  |  |  |
| EV_DoFloor | 14 | arithmetic | 7/0 | 7/0 |  |  |  |
| EV_DoFloor | 22 | relational | 7/0 |  |  |  |  |
| PIT_VileCheck | 0 | equality | 0/0 | 0/0 |  |  |  |
| PIT_VileCheck | 10 | shift | 0/0 | 0/0 |  |  |  |
| PIT_VileCheck | 11 | constant | 0/0 | 0/0 |  |  |  |
| P_KillMobj | 1 | shift | 23/23 | 23/23 |  |  |  |
| P_KillMobj | 2 | constant | 23/0 | 23/0 |  |  |  |
| P_KillMobj | 9 | relational | 23/0 | 23/0 |  |  |  |
| P_LineOpening | 1 | relational | 42/0 | 42/0 |  |  |  |
| P_LineOpening | 2 | relational | 42/0 | 42/0 |  |  |  |
| P_LineOpening | 3 | arithmetic | 42/29 | 42/29 |  |  |  |
| P_PlayerInSpecialSector | 7 | logical | 12/1 | 12/0 |  |  |  |
| P_PlayerInSpecialSector | 8 | relational | 12/0 | 12/0 |  |  |  |
| P_PlayerInSpecialSector | 10 | constant | 12/1 | 12/0 |  |  |  |
| P_SpawnBlood | 1 | constant | 23/23 |  |  |  |  |
| P_SpawnBlood | 7 | logical | 23/23 | 23/23 |  |  |  |
| P_SpawnBlood | 10 | relational | 23/0 | 23/0 |  |  |  |
| P_SpawnPuff | 2 | constant | 30/30 | 30/30 |  |  |  |
| P_SpawnPuff | 3 | relational | 30/0 | 30/0 |  |  |  |
| P_SpawnPuff | 4 | equality | 30/30 | 30/30 |  |  |  |
| P_UseSpecialLine | 19 | constant | 33/0 | 33/0 |  |  |  |
| T_MovePlane | 4 | equality | 30/15 | 30/15 |  |  |  |
| T_MovePlane | 6 | relational | 30/1 | 30/1 |  |  |  |

Did not build: 41 (Counter({'md:match': 24, 'md:name': 11, 'ch': 3, 'pb:match': 3}))