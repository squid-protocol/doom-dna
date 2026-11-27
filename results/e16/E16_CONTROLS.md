# E16 controls on T1 (frozen scorer, test half)

**Ties:** median tie-set size at the truth's score 1, share of queries with ties > 1: 0.196 (ranks are pessimistic).

**Hub statistic:** the five most often returned functions fill 0.194 of all top-5 slots (spreading evenly over all 140 candidates would give 0.036, over the 43 true functions 0.116; the printed 0.179 in the first run was a labelling error); PIT_AddThingIntercepts (262), P_CrossSpecialLine (148), P_DamageMobj (147), PTR_ShootTraverse (139), P_PlayerThink (133).

**True negative (truth's lesions removed):** mean best score present 0.989 vs absent 0.927; AUC of the best score for telling present from absent 0.850 (0.5 = cannot tell). Wrong answers are therefore distinguishable from right ones by the score alone.

**A2 class-only scorer, development half (pool 70, top 14):** share with the truth in the top 14: 0.201
**A2 class-only scorer, test half (pool 140, top 28):** share with the truth in the top 28: 0.437

**Demo-family sensitivity** (primary top-5 on all 77 demos 0.969):

| left_out   |   demos_left_out |   top5 |   top1 |
|:-----------|-----------------:|-------:|-------:|
| b          |               12 |  0.962 |  0.791 |
| c          |               10 |  0.967 |  0.758 |
| f          |               12 |  0.966 |  0.735 |
| g          |                7 |  0.967 |  0.728 |
| p          |                2 |  0.969 |  0.764 |
| s          |               20 |  0.961 |  0.762 |
| v          |               11 |  0.962 |  0.709 |
| x          |                3 |  0.969 |  0.762 |
| ONLY b     |               65 |  0.244 |  0.058 |
| ONLY c     |               67 |  0.593 |  0.29  |
| ONLY f     |               65 |  0.861 |  0.644 |
| ONLY s     |               57 |  0.679 |  0.465 |
| ONLY v     |               66 |  0.818 |  0.512 |