# E15 exploratory analyses

## Group tables (usable functions per group)

### chocolate-doom (k=18, usable 140)

| group | size | stability | first functions |
|---|---|---|---|
| 1 | 18 | 0.70 | PIT_VileCheck, A_VileChase, A_Scream, PIT_StompThing, P_TeleportMove, P_ThingHeightClip, P_ChangeSector, P_UnsetThingPosition, P_RemoveMobj, P_RespawnSpecials ... |
| 2 | 9 | 0.64 | P_BlockThingsIterator, P_SpawnPlayer, getNextSector, P_FindMinSurroundingLight, P_SpawnSpecials, T_FireFlicker, P_SpawnFireFlicker, P_SpawnStrobeFlash, P_SpawnGlowingLight |
| 3 | 2 | 0.65 | PIT_ChangeSector, P_GivePower |
| 4 | 17 | 0.77 | PTR_UseTraverse, P_UseLines, T_VerticalDoor, EV_DoDoor, EV_VerticalDoor, T_MovePlane, EV_DoFloor, P_FindLowestFloorSurrounding, P_FindHighestFloorSurrounding, P_FindLowestCeilingSurrounding ... |
| 5 | 81 | 0.91 | P_RecursiveSound, P_NoiseAlert, P_CheckMeleeRange, P_CheckMissileRange, P_Move, P_NewChaseDir, P_LookForPlayers, A_Look, A_Chase, A_FaceTarget ... |
| 6 | 1 | 0.62 | P_SpawnPlayerMissile |
| 7 | 1 | 0.83 | A_PainShootSkull |
| 8 | 1 | 0.64 | A_Saw |
| 9 | 1 | 0.87 | A_FirePlasma |
| 10 | 1 | 0.69 | A_FireShotgun2 |
| 11 | 1 | 0.87 | A_FireCGun |
| 12 | 1 | 0.90 | P_GiveCard |
| 13 | 1 | 0.87 | EV_DoLockedDoor |
| 14 | 1 | 0.92 | T_MoveCeiling |
| 15 | 1 | 0.88 | EV_DoCeiling |
| 16 | 1 | 0.79 | P_FindNextHighestFloor |
| 17 | 1 | 0.90 | EV_DoDonut |
| 18 | 1 | 0.90 | P_StartButton |

Hot class (26): P_TryWalk, A_PosAttack, A_SPosAttack, A_CPosAttack, A_BspiAttack, A_TroopAttack, A_HeadAttack, A_CyberAttack, A_SkelMissile, A_SkelFist, A_VileAttack, A_FatAttack1, A_FatAttack2, A_FatAttack3, A_PainAttack, A_Explode, P_LineAttack, P_AproxDistance, P_MakeDivline, P_SubstNullMobj, P_Thrust, A_Lower, A_FireMissile, A_FireBFG, T_LightFlash, P_SpawnLightFlash

Inert class: 23 functions

PC4 (groups vs source files): {'ari': 0.0792161378731432, 'null_mean': 3.5552186012042074e-05, 'p': 0.0004997501249375312}

N5 (operator-kind control): {'ari_with_groups': -0.09654782380801426, 'kinds': 14}

### managed-doom (k=15, usable 136)

| group | size | stability | first functions |
|---|---|---|---|
| 1 | 21 | 0.60 | AddPoint, Run, SpawnStrobeFlash, SpawnGlowingLight, ShootSpecialLine, VileCheck, VileChase, CalcHeight, DeathThink, SetupPlayerSprites ... |
| 2 | 3 | 0.79 | Run, FindMinSurroundingLight, GetNextSector |
| 3 | 2 | 0.54 | GivePower, CrushThing |
| 4 | 16 | 0.74 | UseTraverse, UseLines, UseSpecialLine, CrossSpecialLine, Run, MovePlane, GetNextSector, FindLowestFloorSurrounding, FindHighestFloorSurrounding, FindLowestCeilingSurrounding ... |
| 5 | 84 | 0.87 | AimTraverse, ShootTraverse, AimLineAttack, LineAttack, SpawnPuff, SpawnBlood, GiveAmmo, GiveWeapon, GiveHealth, GiveArmor ... |
| 6 | 1 | 0.87 | Run |
| 7 | 1 | 0.85 | PainShootSkull |
| 8 | 1 | 0.88 | DoLockedDoor |
| 9 | 1 | 0.75 | FindNextHighestFloor |
| 10 | 1 | 0.92 | DoCeiling |
| 11 | 1 | 0.87 | DoDonut |
| 12 | 1 | 0.69 | Saw |
| 13 | 1 | 0.77 | FireCGun |
| 14 | 1 | 0.60 | FireShotgun2 |
| 15 | 1 | 0.80 | FirePlasma |

Hot class (34): MakeFrom, Make, Run, SpawnLightFlash, TryWalk, PosAttack, SPosAttack, CPosAttack, TroopAttack, SargAttack, HeadAttack, FatAttack1, FatAttack2, FatAttack3, BspiAttack, CyberAttack, Explode, VileAttack, SkelMissile, SkelFist, PainAttack, InterceptVector, Thrust, FindSectorFromLineTag, HitSlideLine, StairStep, Add, Remove, MoveNext, FireMissile, FireBFG, SecretExitLevel, GetNewValidCount, SubstNullMobj

Inert class: 67 functions

PC4 (groups vs source files): {'ari': 0.044550661794469426, 'null_mean': 5.278497086108143e-05, 'p': 0.0014992503748125937}

N5 (operator-kind control): {'ari_with_groups': -0.12369605833847262, 'kinds': 14}

## H6: E12 structural matches versus phenotype groups

{'pairs': 61, 'strong tiers': {'n': 10, 'aligned': 1.0, 'top5': 0.8, 'median_rank': 1.0}, 'extension tiers': {'n': 51, 'aligned': 0.7058823529411765, 'top5': 0.5490196078431373, 'median_rank': 1.0}, 'random pairs aligned': 0.3780131147540984, 'all pairs aligned': 0.7540983606557377}
