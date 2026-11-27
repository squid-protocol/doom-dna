# E16 held-out test (frozen scorer: {"a_failing_set": 0.5, "b_class": 0.0, "c_tic": 0.5}, max, min 10 demos)

## T1: managed-doom (43 test-half counterpart functions; 472 queries dropped by the >=3-demo filter; pool 140)

| method          |   n |   top1 |   top3 |   top5 |   top10 |   mrr |
|:----------------|----:|-------:|-------:|-------:|--------:|------:|
| random (chance) | 855 |  0.007 |  0.021 |  0.036 |   0.071 | 0.039 |
| dictionary      | 855 |  0.766 |  0.95  |  0.969 |   0.996 | 0.859 |
| dictionary_C    | 855 |  0.587 |  0.823 |  0.854 |   0.896 | 0.711 |
| ochiai          | 855 |  0.246 |  0.343 |  0.358 |   0.413 | 0.322 |
| tarantula       | 855 |  0.064 |  0.106 |  0.195 |   0.292 | 0.129 |
| metallaxis      | 855 |  0.555 |  0.736 |  0.755 |   0.81  | 0.659 |
| size            | 855 |  0     |  0     |  0     |   0     | 0.024 |
| calls           | 855 |  0.046 |  0.07  |  0.109 |   0.221 | 0.107 |
| family          | 855 |  0.202 |  0.289 |  0.373 |   0.463 | 0.295 |
| shuffled        | 855 |  0.007 |  0.038 |  0.058 |   0.089 | 0.05  |

Paired cluster bootstrap (functions, 10,000) of top-5, dictionary minus comparator:

|              |   delta |    lo |    hi |
|:-------------|--------:|------:|------:|
| ochiai       |   0.612 | 0.478 | 0.739 |
| metallaxis   |   0.215 | 0.136 | 0.299 |
| family       |   0.596 | 0.469 | 0.717 |
| size         |   0.969 | 0.937 | 0.993 |
| calls        |   0.86  | 0.775 | 0.934 |
| dictionary_C |   0.115 | 0.061 | 0.181 |
| shuffled     |   0.911 | 0.842 | 0.968 |

**A1 check:** top-5 0.969, Ochiai 0.358, lift 0.612, 95% CI (0.478, 0.739), functions 43 (power gate >= 30: True) -> **PASS**

## T2: prboom-plus (1 test-half counterpart functions; 3 queries dropped by the >=3-demo filter; pool 140)

| method          |   n |   top1 |   top3 |   top5 |   top10 |   mrr |
|:----------------|----:|-------:|-------:|-------:|--------:|------:|
| random (chance) |   5 |  0.007 |  0.021 |  0.036 |   0.071 | 0.039 |
| dictionary      |   5 |  0     |  0     |  0.8   |   0.8   | 0.203 |
| dictionary_C    |   5 |  0     |  0.2   |  0.8   |   0.8   | 0.22  |
| ochiai          |   5 |  0     |  0     |  0     |   0     | 0.023 |
| tarantula       |   5 |  0     |  0     |  0     |   0     | 0.012 |
| metallaxis      |   5 |  0.8   |  0.8   |  0.8   |   0.8   | 0.804 |
| size            |   5 |  0     |  0     |  0     |   0     | 0.007 |
| calls           |   5 |  0     |  0     |  0     |   0     | 0.045 |
| family          |   5 |  0     |  0.8   |  0.8   |   0.8   | 0.402 |
| shuffled        |   5 |  0     |  0     |  0.8   |   0.8   | 0.203 |

Paired cluster bootstrap (functions, 10,000) of top-5, dictionary minus comparator:

|              |   delta |   lo |   hi |
|:-------------|--------:|-----:|-----:|
| ochiai       |     0.8 |  0.8 |  0.8 |
| metallaxis   |     0   |  0   |  0   |
| family       |     0   |  0   |  0   |
| size         |     0.8 |  0.8 |  0.8 |
| calls        |     0.8 |  0.8 |  0.8 |
| dictionary_C |     0   |  0   |  0   |
| shuffled     |     0   |  0   |  0   |

**A1 check:** top-5 0.800, Ochiai 0.000, lift 0.800, 95% CI (0.800, 0.800), functions 1 (power gate >= 30: False) -> **FAIL**

Notes: `dictionary_C` removes the query's operator family; `shuffled` permutes function labels as units (chance control). The true-negative control and the hub statistic are computed separately. T2 includes functions with identical text (not separated): an upper bound.
