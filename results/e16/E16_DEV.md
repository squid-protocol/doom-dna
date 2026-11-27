# E16 development task (development-half functions only; no test-half, no prboom-plus, no gore or Kocoa data)

dictionary 2960 lesions in 70 functions; 1316 managed-doom query lesions from 55 chocolate-doom counterpart functions (equal weight per function); pool 70.

## A. exact twin lesion in the dictionary (transplant upper bound)

| method                                                      |    n |   top1 |   top3 |   top5 |   top10 |   mrr |
|:------------------------------------------------------------|-----:|-------:|-------:|-------:|--------:|------:|
| random (chance)                                             | 1316 |  0.014 |  0.043 |  0.071 |   0.143 | 0.069 |
| B2 Ochiai coverage                                          | 1316 |  0.31  |  0.488 |  0.523 |   0.576 | 0.422 |
| B2 Tarantula coverage                                       | 1316 |  0.09  |  0.292 |  0.341 |   0.355 | 0.215 |
| B3 Metallaxis-style kill-only                               | 1316 |  0.498 |  0.735 |  0.837 |   0.881 | 0.642 |
| B4 size prior                                               | 1316 |  0.018 |  0.055 |  0.073 |   0.164 | 0.074 |
| B5 call-count contrast                                      | 1316 |  0.08  |  0.173 |  0.307 |   0.458 | 0.191 |
| B7 demo-family-only                                         | 1316 |  0.188 |  0.343 |  0.423 |   0.527 | 0.309 |
| E16 scorer (best: max, min 10 demos, weights 0.5/0.25/0.25) | 1316 |  0.805 |  0.995 |  0.998 |   1     | 0.895 |

Top configurations:

| agg   |   min_eval |   wa |   wb |   wc |    n |   top1 |   top3 |   top5 |   top10 |   mrr |
|:------|-----------:|-----:|-----:|-----:|-----:|-------:|-------:|-------:|--------:|------:|
| max   |         10 | 0.5  | 0.25 | 0.25 | 1316 |  0.805 |  0.995 |  0.998 |   1     | 0.895 |
| max   |          5 | 0.5  | 0.25 | 0.25 | 1316 |  0.802 |  0.995 |  0.998 |   1     | 0.893 |
| max   |         10 | 0.25 | 0.25 | 0.5  | 1316 |  0.808 |  0.996 |  0.998 |   0.998 | 0.897 |
| max   |          5 | 0.25 | 0.25 | 0.5  | 1316 |  0.805 |  0.996 |  0.998 |   0.998 | 0.895 |

## B. lesions of the query's kind removed from the dictionary

| method                                                      |    n |   top1 |   top3 |   top5 |   top10 |   mrr |
|:------------------------------------------------------------|-----:|-------:|-------:|-------:|--------:|------:|
| random (chance)                                             | 1316 |  0.014 |  0.043 |  0.071 |   0.143 | 0.069 |
| B2 Ochiai coverage                                          | 1316 |  0.31  |  0.488 |  0.523 |   0.576 | 0.422 |
| B2 Tarantula coverage                                       | 1316 |  0.09  |  0.292 |  0.341 |   0.355 | 0.215 |
| B3 Metallaxis-style kill-only                               | 1316 |  0.413 |  0.623 |  0.753 |   0.801 | 0.556 |
| B4 size prior                                               | 1316 |  0.018 |  0.055 |  0.073 |   0.164 | 0.074 |
| B5 call-count contrast                                      | 1316 |  0.08  |  0.173 |  0.307 |   0.458 | 0.191 |
| B7 demo-family-only                                         | 1316 |  0.153 |  0.328 |  0.39  |   0.504 | 0.28  |
| E16 scorer (best: max, min 10 demos, weights 0.25/0.25/0.5) | 1316 |  0.657 |  0.868 |  0.886 |   0.903 | 0.764 |

Top configurations:

| agg   |   min_eval |   wa |   wb |   wc |    n |   top1 |   top3 |   top5 |   top10 |   mrr |
|:------|-----------:|-----:|-----:|-----:|-----:|-------:|-------:|-------:|--------:|------:|
| max   |         10 | 0.25 | 0.25 |  0.5 | 1316 |  0.657 |  0.868 |  0.886 |   0.903 | 0.764 |
| max   |         10 | 0.5  | 0    |  0.5 | 1316 |  0.607 |  0.85  |  0.886 |   0.907 | 0.734 |
| max   |          5 | 0.25 | 0.25 |  0.5 | 1316 |  0.657 |  0.865 |  0.886 |   0.903 | 0.763 |
| max   |          5 | 0.5  | 0    |  0.5 | 1316 |  0.581 |  0.85  |  0.885 |   0.907 | 0.721 |

## C. lesions of the query's family removed (operator / constant / unary / control flow): the realistic condition

| method                                                    |    n |   top1 |   top3 |   top5 |   top10 |   mrr |
|:----------------------------------------------------------|-----:|-------:|-------:|-------:|--------:|------:|
| random (chance)                                           | 1316 |  0.014 |  0.043 |  0.071 |   0.143 | 0.069 |
| B2 Ochiai coverage                                        | 1316 |  0.31  |  0.488 |  0.523 |   0.576 | 0.422 |
| B2 Tarantula coverage                                     | 1316 |  0.09  |  0.292 |  0.341 |   0.355 | 0.215 |
| B3 Metallaxis-style kill-only                             | 1316 |  0.409 |  0.657 |  0.734 |   0.784 | 0.552 |
| B4 size prior                                             | 1316 |  0.018 |  0.055 |  0.073 |   0.164 | 0.074 |
| B5 call-count contrast                                    | 1316 |  0.08  |  0.173 |  0.307 |   0.458 | 0.191 |
| B7 demo-family-only                                       | 1316 |  0.17  |  0.331 |  0.388 |   0.466 | 0.287 |
| E16 scorer (best: max, min 10 demos, weights 0.5/0.0/0.5) | 1316 |  0.605 |  0.833 |  0.875 |   0.898 | 0.728 |

Top configurations:

| agg   |   min_eval |   wa |   wb |   wc |    n |   top1 |   top3 |   top5 |   top10 |   mrr |
|:------|-----------:|-----:|-----:|-----:|-----:|-------:|-------:|-------:|--------:|------:|
| max   |         10 | 0.5  |    0 | 0.5  | 1316 |  0.605 |  0.833 |  0.875 |   0.898 | 0.728 |
| max   |         10 | 0.25 |    0 | 0.75 | 1316 |  0.614 |  0.841 |  0.874 |   0.892 | 0.735 |
| max   |          5 | 0.5  |    0 | 0.5  | 1316 |  0.579 |  0.833 |  0.873 |   0.898 | 0.715 |
| max   |          3 | 0.25 |    0 | 0.75 | 1316 |  0.58  |  0.841 |  0.873 |   0.893 | 0.717 |

**Viability gate on the realistic condition C** (scorer top-5 >= B2 Ochiai top-5 + 0.10): scorer 0.875 vs 0.523 + 0.10 -> **VIABLE**. Best baseline in condition C: 0.734.
