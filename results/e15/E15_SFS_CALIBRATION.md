# Calibrating the structural matcher (SFS/E12) against behaviour

Behavioural measures (independent of names and of structure): the lesion break pattern (distance D between functions) and the clean call-count profile. 'Phenotype confirmed' = D no larger than the 5th percentile of random cross-port function pairs (chance level 5%), so the threshold comes from the data, not from names. 'both' = phenotype confirmed and call profile identical. 'Call profile identical' = the two functions run exactly the same number of times on all 77 demos. 'Contradicted' = D above the median of random pairs.

## chocolate-doom -> managed-doom (independent lineage)

usable functions (140, 136); behavioural threshold D <= 0.143 (the 5th percentile of random cross-port pairs; the within-function split-half noise floor is 0.384, too lax to separate pairs from chance); behaviourally confirmed mutual-nearest pairs (the gold set): 93

| group                                       |    n |   phenotype_confirmed |   call_profile_identical |   both |   mutual_nearest |   median_distance |   contradicted |
|:--------------------------------------------|-----:|----------------------:|-------------------------:|-------:|-----------------:|------------------:|---------------:|
| name-agree pairs                            |  105 |                  0.9  |                     0.98 |   0.89 |             0.79 |              0.04 |           0.08 |
| SFS strong tiers (exact, twin, xtwin, seed) |   10 |                  0.8  |                     0.8  |   0.8  |             0.6  |              0.05 |           0.1  |
| SFS ext1                                    |   23 |                  0.48 |                     0.57 |   0.48 |             0.35 |              0.2  |           0.35 |
| SFS ext2                                    |   19 |                  0.47 |                     0.53 |   0.47 |             0.47 |              0.27 |           0.47 |
| SFS ext3                                    |    9 |                  0.33 |                     0.33 |   0.33 |             0.33 |              0.26 |           0.33 |
| SFS all tiers                               |   61 |                  0.51 |                     0.56 |   0.51 |             0.43 |              0.12 |           0.34 |
| SFS pairs that agree with the name          |   31 |                  0.94 |                     1    |   0.94 |             0.84 |              0.03 |           0.06 |
| SFS pairs that disagree with the name       |   30 |                  0.07 |                     0.1  |   0.07 |             0    |              0.42 |           0.63 |
| random pairs (chance)                       | 2000 |                  0.05 |                     0.01 |   0.01 |             0.01 |              0.4  |           0.52 |

Share of the gold pairs each matcher recovers: names 89%, SFS (all tiers) 28%, SFS strong tiers 6%, names or SFS 89%

What SFS did on the behaviourally confirmed pairs: SFS right 29, SFS proposed a different function 35, SFS proposed nothing 29 (of 93). Names: name right 83, name wrong or absent 10.

On the confirmed pairs that names miss (renames, 10): SFS right 3, SFS proposed a different function 2, SFS proposed nothing 5.

SFS precision by size ratio (larger / smaller function, in lines):

| bin                |   SFS pairs |   behaviourally confirmed |
|:-------------------|------------:|--------------------------:|
| size ratio <= 1.25 |          35 |                      0.8  |
| 1.25 to 2          |          16 |                      0.19 |
| > 2                |          10 |                      0    |

Failure diagnostics on the 61 SFS pairs with data: confirmed 31, unconfirmed 30. AUC of 'smaller size ratio' for confirmed vs unconfirmed: 0.87; AUC of 'call-graph neighbour agreement' (anchors = SFS strong pairs only): 0.43 (n with enough anchored neighbours: 9).

## chocolate-doom -> prboom-plus (near-clone)

usable functions (140, 160); behavioural threshold D <= 0.158 (the 5th percentile of random cross-port pairs; the within-function split-half noise floor is 0.384, too lax to separate pairs from chance); behaviourally confirmed mutual-nearest pairs (the gold set): 72

| group                                       |    n |   phenotype_confirmed |   call_profile_identical |   both |   mutual_nearest |   median_distance |   contradicted |
|:--------------------------------------------|-----:|----------------------:|-------------------------:|-------:|-----------------:|------------------:|---------------:|
| name-agree pairs                            |  132 |                  0.78 |                     0.95 |   0.74 |             0.58 |              0.08 |           0.09 |
| SFS strong tiers (exact, twin, xtwin, seed) |   37 |                  0.7  |                     0.89 |   0.68 |             0.62 |              0.05 |           0.11 |
| SFS ext1                                    |   28 |                  0.68 |                     0.82 |   0.61 |             0.39 |              0.12 |           0.18 |
| SFS ext2                                    |    9 |                  0.67 |                     0.44 |   0.33 |             0.44 |              0.11 |           0.11 |
| SFS ext3                                    |    1 |                  0    |                     0    |   0    |             0    |              0.3  |           0    |
| SFS all tiers                               |   75 |                  0.68 |                     0.8  |   0.6  |             0.51 |              0.09 |           0.13 |
| SFS pairs that agree with the name          |   65 |                  0.75 |                     0.92 |   0.69 |             0.58 |              0.07 |           0.11 |
| SFS pairs that disagree with the name       |   10 |                  0.2  |                     0    |   0    |             0    |              0.28 |           0.3  |
| random pairs (chance)                       | 2000 |                  0.05 |                     0    |   0    |             0    |              0.4  |           0.49 |

Share of the gold pairs each matcher recovers: names 100%, SFS (all tiers) 49%, SFS strong tiers 31%, names or SFS 100%

What SFS did on the behaviourally confirmed pairs: SFS right 35, SFS proposed a different function 17, SFS proposed nothing 20 (of 72). Names: name right 72, name wrong or absent 0.

On the confirmed pairs that names miss (renames, 0): SFS right 0, SFS proposed a different function 0, SFS proposed nothing 0.

SFS precision by size ratio (larger / smaller function, in lines):

| bin                |   SFS pairs |   behaviourally confirmed |
|:-------------------|------------:|--------------------------:|
| size ratio <= 1.25 |          39 |                      0.69 |
| 1.25 to 2          |          26 |                      0.58 |
| > 2                |          10 |                      0.3  |

Failure diagnostics on the 75 SFS pairs with data: confirmed 51, unconfirmed 24. AUC of 'smaller size ratio' for confirmed vs unconfirmed: 0.72; AUC of 'call-graph neighbour agreement' (anchors = SFS strong pairs only): 0.78 (n with enough anchored neighbours: 22).
