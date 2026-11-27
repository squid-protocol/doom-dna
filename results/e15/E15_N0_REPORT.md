# Dynamic call-count profiles as an ortholog matcher (no lesion outcomes)

functions entered by >= 3 demos: chocolate-doom 182, managed-doom 256; demos 77; name-agree pairs 145

**Name-agree partners:** top-1 0.86, top-5 0.96, median rank 1; chance top-1 0.004. 98% of partner pairs have an identical profile (distance 0; ties count against the matcher).

Name-agree pairs with the worst profile rank (profile does not isolate the partner):

| function | rank of its name partner |
|---|---|
| LightFlash | 103 |
| StrobeFlash | 66 |
| SpawnSpecials | 37 |
| CalcHeight | 11 |
| PlayerThink | 11 |
| RespawnSpecials | 11 |

## E12 structural matches (82 chocolate-doom to managed-doom pairs with both functions entered)

| group | pairs | profile top-1 | top-5 | median rank |
|---|---|---|---|---|
| strong tiers (exact, twin, xtwin, seed) | 11 | 0.82 | 0.82 | 1 |
| extension tiers (ext1-3) | 71 | 0.32 | 0.38 | 26 |
| matcher agrees with the name | 32 | 0.91 | 1.00 | 1 |
| matcher disagrees with the name | 50 | 0.06 | 0.08 | 108 |

**Where the structural matcher and the name disagree (40 pairs with a same-named function in managed-doom):** the call-count profile is closer to the NAME partner for 98% of them and closer to the structural matcher's choice for 2% (ties 0%).
