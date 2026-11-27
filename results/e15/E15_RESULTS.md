# E15 results (registered analysis)

usable functions (eligible, not hot, not inert): chocolate-doom 140, managed-doom 136; hot class (26, 34); inert class (23, 67); name-agree pairs 101

| prediction | observed | result |
|---|---|---|
| PC1f function-level reliability gate for H4 (top-1 >= 0.20 and top-5 >= 0.50, each port) | A top1 0.53 top5 0.69 (n=118); B top1 0.43 top5 0.70 (n=105) | PASSED |
| PC1g group-level reliability gate for H1a-H3 (AMI of split-half groupings >= 0.40, each port) | A 0.73, B 0.44 | PASSED |
| H1a discrete grouping exists (max-gap p<0.01 against a Gaussian null with the observed covariance, and >=60% of functions in stable groups, both ports) | A k=18 p=0.005 (any-structure p=0.010) stable 1.00; B k=15 p=0.104 (any-structure p=0.010) stable 0.83 | FAILED (H2-H4 exploratory) |
| H2 neighbourhoods, chocolate-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.45 hops (obs 4.04 vs null 4.49), p=0.0001; clean-count groups 0.22 (break-pattern groups tighter) | FAILED [exploratory: H1a failed] |
| H2 neighbourhoods, managed-doom (>= 0.5 hops, p<0.0167; clean-count baseline reported) | 0.16 hops (obs 3.73 vs null 3.88), p=0.0001; clean-count groups 0.16 (not tighter than clean-count groups) | FAILED [exploratory: H1a failed] |
| H3 recurrence (AMI >= 0.30, p<0.0167, >= 60 pairs; clean-count baseline reported) | AMI 0.83 (null 0.08; clean-count groups 0.83) over 101 pairs, p=0.0001 | PASSED [exploratory: H1a failed] |
| H4 recovers name-agree partners beyond reach (a function-level result: not gated by H1a) | top-5 0.90 (threshold 0.35; chance 0.04, N0 0.97, ceiling 0.70), top-1 0.84 (N0 0.94), p=0.0001, pairs 101, pool 136 | PASSED |