# E16 real cases (frozen scorer; candidates = 140 usable chocolate-doom functions)

## gore: evaluated demos 74, killed 69, same 5; median first-tic of kills 2

Best similarity 0.905; ties at the top 1.

Top 12 (dictionary scorer): P_CheckPosition (0.905), P_TraverseIntercepts (0.903), P_DivlineSide (0.882), P_CrossSubsector (0.880), P_BlockLinesIterator (0.879), P_SpawnMapThing (0.879), P_PointOnDivlineSide (0.877), P_SpawnMobj (0.876), PIT_AddLineIntercepts (0.874), P_PathTraverse (0.873), P_PlayerThink (0.873), A_WeaponReady (0.872)

Top 8 Ochiai: PIT_CheckLine, PIT_CheckThing, P_CheckPosition, P_TryMove, P_HitSlideLine, PTR_SlideTraverse, P_SlideMove, P_UseLines

Top 8 Metallaxis-style: P_PointOnDivlineSide, PIT_AddLineIntercepts, P_PathTraverse, PIT_CheckLine, PIT_CheckThing, P_CheckPosition, P_TryMove, P_HitSlideLine

| target           | usable   |   rank_dictionary |   rank_ochiai |   rank_metallaxis |   rank_family |
|:-----------------|:---------|------------------:|--------------:|------------------:|--------------:|
| P_CrossSubsector | True     |                 4 |            64 |                51 |            28 |

## Kocoa: evaluated demos 58, killed 46, same 12; median first-tic of kills 3

Best similarity 1.000; ties at the top 1.

Top 12 (dictionary scorer): P_CrossSubsector (1.000), P_MobjThinker (0.980), P_SpawnMapThing (0.956), P_SpawnMobj (0.930), P_CheckAmmo (0.930), P_FireWeapon (0.930), A_WeaponReady (0.930), P_BringUpWeapon (0.930), P_PathTraverse (0.929), PTR_ShootTraverse (0.929), P_SpawnPuff (0.929), P_SpawnPlayer (0.928)

Top 8 Ochiai: P_RecursiveSound, P_NoiseAlert, P_LookForPlayers, A_Look, PTR_AimTraverse, PTR_ShootTraverse, P_AimLineAttack, PIT_AddThingIntercepts

Top 8 Metallaxis-style: P_LookForPlayers, PTR_AimTraverse, PTR_ShootTraverse, P_AimLineAttack, P_PointOnDivlineSide, PIT_AddThingIntercepts, P_PathTraverse, P_DivlineSide

| target              | usable   |   rank_dictionary |   rank_ochiai |   rank_metallaxis |   rank_family | note                                                                                                         |
|:--------------------|:---------|------------------:|--------------:|------------------:|--------------:|:-------------------------------------------------------------------------------------------------------------|
| P_NewChaseDir       | True     |                36 |            25 |                40 |             6 | nan                                                                                                          |
| A_Chase             | True     |                35 |            25 |                40 |            13 | nan                                                                                                          |
| P_Move              | True     |                33 |            25 |                40 |            37 | nan                                                                                                          |
| P_TryWalk           | False    |               nan |           nan |               nan |           nan | not in the 140 usable candidates (hot, inert, outside screened files or named differently): scored as a miss |
| P_CheckMissileRange | True     |                50 |            26 |                44 |            46 | nan                                                                                                          |

## Kocoa (3 start-state demos x0014/x0043/x0056 set aside): evaluated demos 55, killed 43, same 12; median first-tic of kills 3

Best similarity 1.000; ties at the top 1.

Top 12 (dictionary scorer): P_CrossSubsector (1.000), P_MobjThinker (0.980), P_SpawnMapThing (0.943), P_CheckAmmo (0.939), P_FireWeapon (0.939), A_WeaponReady (0.939), P_BringUpWeapon (0.939), P_SpawnMobj (0.938), P_PathTraverse (0.936), PTR_ShootTraverse (0.936), P_SpawnPlayer (0.936), P_PlayerThink (0.936)

Top 8 Ochiai: P_RecursiveSound, P_NoiseAlert, P_LookForPlayers, A_Look, PTR_AimTraverse, PTR_ShootTraverse, P_AimLineAttack, PIT_AddThingIntercepts

Top 8 Metallaxis-style: P_LookForPlayers, PTR_AimTraverse, PTR_ShootTraverse, P_AimLineAttack, P_PointOnDivlineSide, PIT_AddThingIntercepts, P_PathTraverse, P_DivlineSide

| target              | usable   |   rank_dictionary |   rank_ochiai |   rank_metallaxis |   rank_family | note                                                                                                         |
|:--------------------|:---------|------------------:|--------------:|------------------:|--------------:|:-------------------------------------------------------------------------------------------------------------|
| P_NewChaseDir       | True     |                37 |            25 |                40 |             9 | nan                                                                                                          |
| A_Chase             | True     |                36 |            25 |                40 |            17 | nan                                                                                                          |
| P_Move              | True     |                34 |            25 |                40 |            30 | nan                                                                                                          |
| P_TryWalk           | False    |               nan |           nan |               nan |           nan | not in the 140 usable candidates (hot, inert, outside screened files or named differently): scored as a miss |
| P_CheckMissileRange | True     |                53 |            26 |                45 |            61 | nan                                                                                                          |

## Kocoa SENSITIVITY (post hoc, after seeing the first run): every demo diverging at tic 0 or 1 set aside as a start-state artifact of the external-demo path: evaluated demos 46, killed 34, same 12; median first-tic of kills 3

Best similarity 0.990; ties at the top 1.

Top 12 (dictionary scorer): P_MobjThinker (0.990), P_SpawnMobj (0.976), P_PathTraverse (0.976), P_SpawnPuff (0.976), PTR_ShootTraverse (0.976), P_CheckAmmo (0.975), P_FireWeapon (0.975), A_WeaponReady (0.975), P_BringUpWeapon (0.975), P_AimLineAttack (0.974), P_LookForPlayers (0.972), P_SpawnPlayer (0.968)

Top 8 Ochiai: P_RecursiveSound, P_NoiseAlert, P_LookForPlayers, A_Look, PTR_AimTraverse, PTR_ShootTraverse, P_AimLineAttack, PIT_AddThingIntercepts

Top 8 Metallaxis-style: P_LookForPlayers, PTR_AimTraverse, PTR_ShootTraverse, P_AimLineAttack, P_PointOnDivlineSide, PIT_AddThingIntercepts, P_PathTraverse, P_DivlineSide

| target              | usable   |   rank_dictionary |   rank_ochiai |   rank_metallaxis |   rank_family | note                                                                                                         |
|:--------------------|:---------|------------------:|--------------:|------------------:|--------------:|:-------------------------------------------------------------------------------------------------------------|
| P_NewChaseDir       | True     |                41 |            25 |                41 |           115 | nan                                                                                                          |
| A_Chase             | True     |                41 |            25 |                41 |            90 | nan                                                                                                          |
| P_Move              | True     |                37 |            25 |                41 |            87 | nan                                                                                                          |
| P_TryWalk           | False    |               nan |           nan |               nan |           nan | not in the 140 usable candidates (hot, inert, outside screened files or named differently): scored as a miss |
| P_CheckMissileRange | True     |                50 |            26 |                44 |            70 | nan                                                                                                          |
