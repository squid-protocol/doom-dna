# E15 C-family replication (chocolate-doom vs prboom-plus)

usable functions (140, 160); hot (26, 24); inert (23, 23); name-agree pairs 125

| prediction | observed | result |
|---|---|---|
| PC1f function-level reliability gate for H4 (top-1 >= 0.20 and top-5 >= 0.50, each port) | A top1 0.53 top5 0.69 (n=118); B top1 0.48 top5 0.68 (n=130) | PASSED |
| PC1g group-level reliability gate for H1a-H3 (AMI of split-half groupings >= 0.40, each port) | A 0.73, B 0.95 | PASSED |
| H1a discrete grouping exists (max-gap p<0.01 against a Gaussian null with the observed covariance, and >=60% of functions in stable groups, both ports) | A k=18 p=0.005 (any-structure p=0.010) stable 1.00; B k=26 p=0.294 (any-structure p=0.010) stable 0.69 | FAILED (H2-H4 exploratory) |
| H2 neighbourhoods, chocolate-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.45 hops (obs 4.04 vs null 4.49), p=0.0001; clean-count groups 0.22 (break-pattern groups tighter) | FAILED [exploratory: H1a failed] |
| H2 neighbourhoods, managed-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.14 hops (obs 4.35 vs null 4.49), p=0.0001; clean-count groups 0.24 (not tighter than clean-count groups) | FAILED [exploratory: H1a failed] |
| H3 recurrence (AMI >= 0.30, p<0.0167, >= 60 pairs; clean-count baseline reported) | AMI 0.64 (null 0.09; clean-count groups 0.83) over 125 pairs, p=0.0001 | PASSED [exploratory: H1a failed] |
| H4 recovers name-agree partners beyond reach (a function-level result: not gated by H1a) | top-5 0.78 (threshold 0.34; chance 0.03, N0 1.00, ceiling 0.68), top-1 0.64 (N0 0.88), p=0.0001, pairs 125, pool 160 | PASSED |