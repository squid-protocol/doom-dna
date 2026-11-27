# E15 sensitivity analyses

## original 42 demos (42 demos)

| prediction | observed | result |
|---|---|---|
| PC1f function-level reliability gate for H4 (top-1 >= 0.20 and top-5 >= 0.50, each port) | A top1 0.56 top5 0.81 (n=90); B top1 0.45 top5 0.74 (n=80) | PASSED |
| PC1g group-level reliability gate for H1a-H3 (AMI of split-half groupings >= 0.40, each port) | A 0.53, B 0.49 | PASSED |
| H1a discrete grouping exists (max-gap p<0.01 against a Gaussian null with the observed covariance, and >=60% of functions in stable groups, both ports) | A k=7 p=0.010 (any-structure p=0.010) stable 0.85; B k=5 p=0.005 (any-structure p=0.010) stable 1.00 | PASSED |
| H2 neighbourhoods, chocolate-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.25 hops (obs 4.16 vs null 4.41), p=0.0005; clean-count groups 0.29 (not tighter than clean-count groups) | FAILED |
| H2 neighbourhoods, managed-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.17 hops (obs 3.84 vs null 4.00), p=0.0005; clean-count groups 0.15 (break-pattern groups tighter) | FAILED |
| H3 recurrence (AMI >= 0.30, p<0.0167, >= 60 pairs; clean-count baseline reported) | AMI 0.68 (null 0.01; clean-count groups 0.69) over 77 pairs, p=0.0005 | PASSED |
| H4 recovers name-agree partners beyond reach (a function-level result: not gated by H1a) | top-5 0.94 (threshold 0.37; chance 0.05, N0 0.96, ceiling 0.74), top-1 0.81 (N0 0.91), p=0.0005, pairs 77, pool 108 | PASSED |

## shareware-base 58 demos (58 demos)

| prediction | observed | result |
|---|---|---|
| PC1f function-level reliability gate for H4 (top-1 >= 0.20 and top-5 >= 0.50, each port) | A top1 0.53 top5 0.73 (n=99); B top1 0.46 top5 0.72 (n=96) | PASSED |
| PC1g group-level reliability gate for H1a-H3 (AMI of split-half groupings >= 0.40, each port) | A 1.00, B 0.77 | PASSED |
| H1a discrete grouping exists (max-gap p<0.01 against a Gaussian null with the observed covariance, and >=60% of functions in stable groups, both ports) | A k=17 p=0.005 (any-structure p=0.010) stable 0.88; B k=14 p=0.104 (any-structure p=0.010) stable 0.99 | FAILED (H2-H4 exploratory) |
| H2 neighbourhoods, chocolate-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.30 hops (obs 4.13 vs null 4.43), p=0.0005; clean-count groups 0.40 (not tighter than clean-count groups) | FAILED [exploratory: H1a failed] |
| H2 neighbourhoods, managed-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.20 hops (obs 3.79 vs null 3.99), p=0.0005; clean-count groups 0.15 (break-pattern groups tighter) | FAILED [exploratory: H1a failed] |
| H3 recurrence (AMI >= 0.30, p<0.0167, >= 60 pairs; clean-count baseline reported) | AMI 0.77 (null 0.10; clean-count groups 0.83) over 86 pairs, p=0.0005 | PASSED [exploratory: H1a failed] |
| H4 recovers name-agree partners beyond reach (a function-level result: not gated by H1a) | top-5 0.86 (threshold 0.36; chance 0.04, N0 0.97, ceiling 0.72), top-1 0.81 (N0 0.93), p=0.0005, pairs 86, pool 120 | PASSED |

## Freedoom demos only (19 demos)

| prediction | observed | result |
|---|---|---|
| PC1f function-level reliability gate for H4 (top-1 >= 0.20 and top-5 >= 0.50, each port) | A top1 0.47 top5 0.67 (n=107); B top1 0.42 top5 0.71 (n=99) | PASSED |
| PC1g group-level reliability gate for H1a-H3 (AMI of split-half groupings >= 0.40, each port) | A 0.00, B 0.00 | FAILED (group claims uninterpretable) |
| H1a discrete grouping exists (max-gap p<0.01 against a Gaussian null with the observed covariance, and >=60% of functions in stable groups, both ports) | A k=22 p=0.015 (any-structure p=0.010) stable 0.71; B k=22 p=0.030 (any-structure p=0.010) stable 0.70 | FAILED (H2-H4 exploratory) |
| H2 neighbourhoods, chocolate-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.54 hops (obs 3.86 vs null 4.40), p=0.0005; clean-count groups 0.26 (break-pattern groups tighter) | PASSED [exploratory: H1a failed] |
| H2 neighbourhoods, managed-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.21 hops (obs 3.69 vs null 3.90), p=0.0005; clean-count groups -0.01 (break-pattern groups tighter) | FAILED [exploratory: H1a failed] |
| H3 recurrence (AMI >= 0.30, p<0.0167, >= 60 pairs; clean-count baseline reported) | AMI 0.67 (null 0.13; clean-count groups 0.96) over 99 pairs, p=0.0005 | PASSED [exploratory: H1a failed] |
| H4 recovers name-agree partners beyond reach (a function-level result: not gated by H1a) | top-5 0.89 (threshold 0.35; chance 0.04, N0 0.97, ceiling 0.71), top-1 0.83 (N0 0.94), p=0.0005, pairs 99, pool 132 | PASSED |

## original lesions only (77 demos)

| prediction | observed | result |
|---|---|---|
| PC1f function-level reliability gate for H4 (top-1 >= 0.20 and top-5 >= 0.50, each port) | A top1 0.32 top5 0.59 (n=59); B top1 0.36 top5 0.73 (n=55) | PASSED |
| PC1g group-level reliability gate for H1a-H3 (AMI of split-half groupings >= 0.40, each port) | A 0.61, B 1.00 | PASSED |
| H1a discrete grouping exists (max-gap p<0.01 against a Gaussian null with the observed covariance, and >=60% of functions in stable groups, both ports) | A k=13 p=1.000 (any-structure p=0.010) stable 0.99; B k=19 p=1.000 (any-structure p=0.010) stable 0.98 | FAILED (H2-H4 exploratory) |
| H2 neighbourhoods, chocolate-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.25 hops (obs 3.88 vs null 4.13), p=0.0005; clean-count groups 0.15 (break-pattern groups tighter) | FAILED [exploratory: H1a failed] |
| H2 neighbourhoods, managed-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.03 hops (obs 3.48 vs null 3.51), p=0.3863; clean-count groups 0.07 (not tighter than clean-count groups) | FAILED [exploratory: H1a failed] |
| H3 recurrence (AMI >= 0.30, p<0.0167, >= 60 pairs; clean-count baseline reported) | AMI 0.56 (null 0.08; clean-count groups 0.88) over 64 pairs, p=0.0005 | PASSED [exploratory: H1a failed] |
| H4 recovers name-agree partners beyond reach (a function-level result: not gated by H1a) | top-5 0.88 (threshold 0.36; chance 0.06, N0 1.00, ceiling 0.73), top-1 0.78 (N0 0.94), p=0.0005, pairs 64, pool 83 | PASSED |

## statement-deletion lesions only (77 demos)

| prediction | observed | result |
|---|---|---|
| PC1f function-level reliability gate for H4 (top-1 >= 0.20 and top-5 >= 0.50, each port) | A top1 0.33 top5 0.51 (n=55); B top1 0.38 top5 0.68 (n=34) | PASSED |
| PC1g group-level reliability gate for H1a-H3 (AMI of split-half groupings >= 0.40, each port) | A 0.33, B 0.39 | FAILED (group claims uninterpretable) |
| H1a discrete grouping exists (max-gap p<0.01 against a Gaussian null with the observed covariance, and >=60% of functions in stable groups, both ports) | A k=16 p=0.090 (any-structure p=0.010) stable 0.73; B k=14 p=0.398 (any-structure p=0.010) stable 0.71 | FAILED (H2-H4 exploratory) |
| H2 neighbourhoods, chocolate-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.59 hops (obs 3.70 vs null 4.28), p=0.0005; clean-count groups -0.05 (break-pattern groups tighter) | PASSED [exploratory: H1a failed] |
| H2 neighbourhoods, managed-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.15 hops (obs 3.47 vs null 3.63), p=0.0010; clean-count groups -0.09 (break-pattern groups tighter) | FAILED [exploratory: H1a failed] |
| H3 recurrence (AMI >= 0.30, p<0.0167, >= 60 pairs; clean-count baseline reported) | AMI 0.75 (null 0.03; clean-count groups 0.76) over 71 pairs, p=0.0005 | PASSED [exploratory: H1a failed] |
| H4 recovers name-agree partners beyond reach (a function-level result: not gated by H1a) | top-5 0.85 (threshold 0.34; chance 0.05, N0 1.00, ceiling 0.68), top-1 0.72 (N0 0.93), p=0.0005, pairs 71, pool 91 | PASSED |

## condition-negation lesions only (77 demos)

| prediction | observed | result |
|---|---|---|
| PC1f function-level reliability gate for H4 (top-1 >= 0.20 and top-5 >= 0.50, each port) | A top1 0.30 top5 0.57 (n=23); B top1 0.36 top5 0.68 (n=22) | PASSED |
| PC1g group-level reliability gate for H1a-H3 (AMI of split-half groupings >= 0.40, each port) | A 0.34, B 0.43 | FAILED (group claims uninterpretable) |
| H1a discrete grouping exists (max-gap p<0.01 against a Gaussian null with the observed covariance, and >=60% of functions in stable groups, both ports) | A k=7 p=0.846 (any-structure p=0.010) stable 0.98; B k=11 p=0.990 (any-structure p=0.010) stable 1.00 | FAILED (H2-H4 exploratory) |
| H2 neighbourhoods, chocolate-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.12 hops (obs 4.57 vs null 4.69), p=0.0335; clean-count groups 0.14 (not tighter than clean-count groups) | INCONCLUSIVE (power) |
| H2 neighbourhoods, managed-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.26 hops (obs 3.20 vs null 3.45), p=0.0210; clean-count groups -0.00 (break-pattern groups tighter) | INCONCLUSIVE (power) |
| H3 recurrence (AMI >= 0.30, p<0.0167, >= 60 pairs; clean-count baseline reported) | AMI 0.32 (null 0.03; clean-count groups 0.89) over 37 pairs, p=0.0005 | INCONCLUSIVE (power) |
| H4 recovers name-agree partners beyond reach (a function-level result: not gated by H1a) | top-5 0.97 (threshold 0.34; chance 0.10, N0 1.00, ceiling 0.68), top-1 0.95 (N0 0.92), p=0.0005, pairs 37, pool 48 | INCONCLUSIVE (power) |

## operator and constant lesions only (77 demos)

| prediction | observed | result |
|---|---|---|
| PC1f function-level reliability gate for H4 (top-1 >= 0.20 and top-5 >= 0.50, each port) | A top1 0.46 top5 0.65 (n=91); B top1 0.49 top5 0.76 (n=78) | PASSED |
| PC1g group-level reliability gate for H1a-H3 (AMI of split-half groupings >= 0.40, each port) | A 0.51, B 0.00 | FAILED (group claims uninterpretable) |
| H1a discrete grouping exists (max-gap p<0.01 against a Gaussian null with the observed covariance, and >=60% of functions in stable groups, both ports) | A k=13 p=0.488 (any-structure p=0.010) stable 0.74; B k=25 p=0.905 (any-structure p=0.010) stable 0.95 | FAILED (H2-H4 exploratory) |
| H2 neighbourhoods, chocolate-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.46 hops (obs 3.84 vs null 4.30), p=0.0005; clean-count groups 0.13 (break-pattern groups tighter) | FAILED [exploratory: H1a failed] |
| H2 neighbourhoods, managed-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.17 hops (obs 3.53 vs null 3.70), p=0.0565; clean-count groups 0.04 (break-pattern groups tighter) | FAILED [exploratory: H1a failed] |
| H3 recurrence (AMI >= 0.30, p<0.0167, >= 60 pairs; clean-count baseline reported) | AMI 0.36 (null 0.04; clean-count groups 0.71) over 81 pairs, p=0.0005 | PASSED [exploratory: H1a failed] |
| H4 recovers name-agree partners beyond reach (a function-level result: not gated by H1a) | top-5 0.90 (threshold 0.38; chance 0.05, N0 1.00, ceiling 0.76), top-1 0.83 (N0 0.94), p=0.0005, pairs 81, pool 101 | PASSED |
