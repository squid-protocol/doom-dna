# Lesion-level phenotype classes (Brenner-style), exploratory

## chocolate-doom

5549 lesions with at least one clean run; 3576 change the game on at least one demo (and ran on >= 3) and are classified; 1208 ran on >= 3 demos and never changed anything (silent class); 765 ran on fewer than 3 demos. Best k = 11 (silhouette 0.34).

| class | lesions | what breaks first | kill share | severity (log tic) | lesion kinds | functions with the most lesions in the class |
|---|---|---|---|---|---|---|
| 0 | 74 | time 0.97 world 0.08 player 0.06 | 0.79 | 2.46 | sdl 27%, negate 23%, incdec 9% | P_RemoveMobj(10), P_NewChaseDir(6), P_AddActivePlat(5), P_DivlineSide(3), P_CrossBSPNode(3), P_RespawnSpecials(3) |
| 1 | 308 | world 0.92 player 0.07 sector 0.00 | 0.72 | 2.69 | sdl 21%, negate 15%, constant 8% | P_BulletSlope(32), P_RespawnSpecials(21), P_NightmareRespawn(16), P_CrossSubsector(13), P_CheckSight(13), P_SpawnMissile(13) |
| 2 | 908 | world 0.91 player 0.08 sector 0.01 | 0.95 | 2.07 | sdl 28%, negate 20%, arithmetic 10% | P_NewChaseDir(67), A_Chase(65), P_PathTraverse(64), PTR_ShootTraverse(55), P_CrossSubsector(35), PIT_AddThingIntercepts(34) |
| 3 | 384 | world 0.85 player 0.18 sector 0.01 | 0.22 | 2.93 | sdl 18%, relational 15%, const_dec 9% | P_TeleportMove(22), P_XYMovement(16), P_BulletSlope(13), P_RespawnSpecials(11), P_DeathThink(11), P_KillMobj(11) |
| 4 | 612 | player 0.68 world 0.34 sector 0.01 | 0.98 | 1.32 | sdl 28%, negate 24%, arithmetic 10% | P_XYMovement(59), P_SlideMove(56), P_PathTraverse(38), P_CheckPosition(37), P_SpawnMapThing(36), PIT_CheckThing(25) |
| 5 | 221 | player 0.91 world 0.24 sector 0.00 | 0.8 | 2.94 | sdl 21%, negate 14%, constant 10% | A_VileAttack(34), P_TouchSpecialThing(23), P_DamageMobj(19), P_PlayerInSpecialSector(18), P_CheckAmmo(17), P_PlayerThink(16) |
| 6 | 236 | sector 0.99 world 0.10 player 0.07 | 0.92 | 2.51 | sdl 39%, negate 25%, const_toggle 8% | T_MovePlane(21), T_PlatRaise(21), EV_DoFloor(20), EV_DoPlat(18), T_VerticalDoor(17), EV_VerticalDoor(16) |
| 7 | 403 | world 0.92 player 0.12 sector 0.00 | 0.97 | 2.71 | sdl 36%, negate 14%, not 7% | A_Tracer(55), EV_Teleport(39), P_ZMovement(25), P_SpawnPlayerMissile(21), A_Fire(20), A_SkullAttack(19) |
| 8 | 8 | keys 1.00 player 0.00 world 0.00 | 1.0 | 1.28 | negate 38%, const_toggle 25%, sdl 25% | P_SpawnPlayer(4), P_GiveCard(3), P_TouchSpecialThing(1) |
| 9 | 111 | sector 0.97 world 0.11 player 0.07 | 0.36 | 2.93 | sdl 42%, const_toggle 14%, negate 13% | EV_VerticalDoor(15), T_MovePlane(14), EV_DoFloor(14), P_CrossSpecialLine(8), P_UnsetThingPosition(6), PTR_UseTraverse(5) |
| 10 | 311 | player 0.83 world 0.32 sector 0.00 | 0.93 | 2.58 | sdl 24%, negate 17%, const_dec 7% | P_DamageMobj(43), P_TouchSpecialThing(21), PIT_RadiusAttack(18), P_PlayerThink(18), A_WeaponReady(16), A_SargAttack(15) |

**Back-working to functions:** 117 functions have >= 8 classified lesions. Clustering functions by the mix of lesion classes they contain gives 11 function communities. Against the article's 16 call-graph subsystems (117 of these functions are on the map): ARI 0.01, AMI 0.12; by dominant class: ARI 0.01.

Subsystem by function community (counts):

| subsystem                  |   1 |   2 |   3 |   4 |   5 |   6 |   7 |   8 |   9 |   10 |   11 |
|:---------------------------|----:|----:|----:|----:|----:|----:|----:|----:|----:|-----:|-----:|
| S01: Monsters & Mayhem     |   5 |   1 |  13 |   6 |  18 |  12 |   3 |  25 |   5 |    3 |    1 |
| S03: Doors, Lifts & Lights |   9 |   0 |   1 |   0 |   1 |   0 |   0 |   0 |   0 |    0 |    0 |
| S04: Lines & Sightlines    |   1 |   0 |   0 |   0 |   6 |   0 |   0 |   7 |   0 |    0 |    0 |

## managed-doom

5012 lesions with at least one clean run; 2988 change the game on at least one demo (and ran on >= 3) and are classified; 1364 ran on >= 3 demos and never changed anything (silent class); 660 ran on fewer than 3 demos. Best k = 13 (silhouette 0.34).

| class | lesions | what breaks first | kill share | severity (log tic) | lesion kinds | functions with the most lesions in the class |
|---|---|---|---|---|---|---|
| 0 | 283 | player 0.80 world 0.32 sector 0.00 | 0.93 | 2.55 | sdl 22%, negate 18%, equality 8% | DamageMobj(43), TouchSpecialThing(16), WeaponReady(16), Run(15), DoRadiusAttack(15), SargAttack(12) |
| 1 | 307 | world 0.95 player 0.07 sector 0.00 | 0.96 | 2.68 | sdl 29%, negate 16%, arith2 9% | Tracer(53), Teleport(23), ZMovement(22), SkullAttack(18), FireShotgun2(17), Fire(16) |
| 2 | 503 | player 0.69 world 0.34 sector 0.01 | 0.97 | 1.18 | negate 26%, sdl 24%, equality 10% | XYMovement(53), SlideMove(43), SpawnMapThing(37), Run(33), InterceptVector(27), CheckPosition(26) |
| 3 | 90 | player 0.94 world 0.25 sector 0.00 | 0.2 | 3.03 | relational 14%, equality 13%, logical 12% | PlayerThink(13), CheckAmmo(12), TouchSpecialThing(11), SlideTraverse(7), GivePower(6), AddLineIntercepts(6) |
| 4 | 272 | world 0.93 player 0.06 sector 0.01 | 0.23 | 3.01 | sdl 19%, relational 12%, const_dec 10% | XYMovement(14), TeleportMove(14), RespawnSpecials(12), CheckMissileRange(10), DeathThink(10), KillMobj(10) |
| 5 | 746 | world 0.92 player 0.07 sector 0.00 | 0.94 | 2.16 | negate 23%, sdl 21%, arithmetic 11% | NewChaseDir(75), Chase(60), ShootTraverse(54), CheckMissileRange(31), AimLineAttack(28), SpawnBlood(28) |
| 6 | 8 | keys 1.00 player 0.00 world 0.00 | 0.98 | 0.96 | negate 38%, sdl 38%, equality 12% | SpawnPlayer(5), GiveCard(2), TouchSpecialThing(1) |
| 7 | 142 | sector 1.00 player 0.09 world 0.09 | 0.66 | 2.84 | sdl 35%, negate 19%, equality 15% | DoFloor(30), DoLocalDoor(16), Run(14), DoDoor(10), FindNextHighestFloor(10), MovePlane(9) |
| 8 | 138 | sector 0.98 world 0.11 player 0.05 | 0.94 | 2.5 | sdl 34%, negate 32%, equality 11% | Run(34), DoPlatform(19), MovePlane(16), DoLocalDoor(10), SpawnSpecials(7), UseSpecialLine(6) |
| 9 | 9 | time 1.00 world 0.77 player 0.77 | 0.97 | 1.95 | sdl 33%, const_toggle 22%, negate 22% | DeathThink(5), Update(2), PlayerThink(1), World(1) |
| 10 | 242 | world 0.86 player 0.12 sector 0.01 | 0.67 | 2.74 | negate 17%, sdl 16%, equality 11% | BulletSlope(20), DamageMobj(18), Saw(16), RespawnSpecials(12), CrossSubsector(11), TryMove(10) |
| 11 | 179 | player 0.90 world 0.29 time 0.00 | 0.89 | 2.92 | sdl 21%, negate 15%, constant 11% | VileAttack(31), PlayerInSpecialSector(22), TouchSpecialThing(14), CheckAmmo(14), Teleport(11), BruisAttack(10) |
| 12 | 69 | world 0.62 player 0.37 sector 0.02 | 0.92 | 1.95 | equality 88%, constant 4%, negate 3% | SpawnMapThing(8), CheckThing(8), Chase(5), DamageMobj(5), CheckLine(4), XYMovement(4) |

**Back-working to functions:** 105 functions have >= 8 classified lesions. Clustering functions by the mix of lesion classes they contain gives 13 function communities. Against the article's 16 call-graph subsystems (105 of these functions are on the map): ARI 0.05, AMI 0.07; by dominant class: ARI 0.05.

Subsystem by function community (counts):

| subsystem                    |   1 |   2 |   3 |   4 |   5 |   6 |   7 |   8 |   9 |   10 |   11 |   12 |   13 |
|:-----------------------------|----:|----:|----:|----:|----:|----:|----:|----:|----:|-----:|-----:|-----:|-----:|
| S01: Monsters & Mayhem       |   5 |   1 |   0 |   1 |   1 |   1 |   2 |   1 |   1 |    5 |    1 |    1 |   13 |
| S02: The Engine Room         |   1 |   0 |   0 |   0 |   0 |   1 |   4 |   0 |   0 |    4 |    0 |    5 |    4 |
| S03: Doors, Lifts & Lights   |   0 |   0 |   5 |   3 |   1 |   0 |   0 |   0 |   0 |    1 |    0 |    0 |    0 |
| S04: Lines & Sightlines      |   0 |   1 |   1 |   0 |   0 |   0 |   0 |   0 |   0 |    3 |    0 |    1 |    4 |
| S05: Soundstage & Scoreboard |   0 |   1 |   0 |   0 |   0 |   0 |   0 |   0 |   0 |    1 |    0 |    0 |    0 |
| S06: The 2D Painter          |   0 |   0 |   1 |   0 |   0 |   0 |   0 |   0 |   0 |    0 |    0 |    0 |    1 |
| S07: The Archivist           |   2 |   0 |   1 |   0 |   0 |   1 |   2 |   0 |   0 |    3 |    0 |    2 |    3 |
| S09: The 3D Eye              |   4 |   1 |   0 |   0 |   0 |   0 |   0 |   0 |   1 |    1 |    0 |    2 |    2 |
| S10: The Sound Daemon        |   0 |   0 |   0 |   0 |   0 |   0 |   0 |   0 |   0 |    1 |    0 |    0 |    0 |
| S14: The Automap Pen         |   0 |   1 |   0 |   0 |   0 |   0 |   0 |   0 |   0 |    0 |    0 |    0 |    1 |
| S15: Status Bar & Palette    |   0 |   0 |   0 |   0 |   0 |   0 |   0 |   0 |   0 |    1 |    0 |    0 |    0 |

## Do the lesion classes recur across ports?

Chocolate-doom class matched to its closest managed-doom class (one-to-one, by centroid distance; lower is closer, 0.5 is already close):

| chocolate class | managed class | distance | chocolate: main state, kill share | managed: main state, kill share |
|---|---|---|---|---|
| 0 | 9 | 0.86 | time, 0.79 | time, 0.97 |
| 1 | 10 | 0.19 | world, 0.72 | world, 0.67 |
| 2 | 5 | 0.05 | world, 0.95 | world, 0.94 |
| 3 | 4 | 0.11 | world, 0.22 | world, 0.23 |
| 4 | 2 | 0.05 | player, 0.98 | player, 0.97 |
| 5 | 11 | 0.19 | player, 0.8 | player, 0.89 |
| 6 | 8 | 0.26 | sector, 0.92 | sector, 0.94 |
| 7 | 1 | 0.05 | world, 0.97 | world, 0.96 |
| 8 | 6 | 0.29 | keys, 1.0 | keys, 0.98 |
| 9 | 7 | 0.40 | sector, 0.36 | sector, 0.66 |
| 10 | 0 | 0.06 | player, 0.93 | player, 0.93 |