# Skin Lab state (diagnose.py)

Recomputed from library.json; agents propose experiments against these numbers.

| part | cards | view only guessed | label vs CLIP conflicts | length spread in one character (median, worst) | vs Vitruvian (median) |
|---|---|---|---|---|---|
| head | 233 | 42 | 0 | 1.05 (7.48 friend_1) | 1.19 |
| torso | 214 | 51 | 0 | 1.0 (1.09 poet) | 0.97 |
| pelvis | 101 | 67 | 0 | 1.32 (7.36 ex) | 0.98 |
| upper_arm | 200 | 159 | 0 | 1.0 (1.05 poet) | 0.99 |
| forearm | 190 | 150 | 0 | 1.02 (1.05 poet) | 0.97 |
| hand | 604 | 510 | 0 | 1.0 (1.06 poet) | 1.12 |
| thigh | 193 | 148 | 0 | 1.05 (1.05 vintage_woman) | 1.0 |
| shin | 177 | 136 | 0 | 1.05 (1.05 father_elder) | 1.01 |
| foot | 229 | 94 | 0 | 1.41 (6.54 poet) | 1.19 |

Misfiled (CLIP, unsettled): 26 — {'hand->eye': 7, 'hand->mouth': 3, 'hand->foot': 3, 'thigh->pelvis': 2, 'forearm->hand': 2, 'shin->hand': 2, 'hand->brow': 1, 'hand->head': 1, 'upper_arm->hand': 1, 'thigh->hand': 1, 'head->foot': 1, 'eye->head': 1}
Pelvis: 101 hip bridges; characters with none: ancestors, father_elder, couple_2_a, child_traveler, atlantis_crowd, citizen_1, couple_2_b, elder_man, elder_1, gatekeeper, friend_2, ancestor_robe, brother_1, couple_1_b, couple_3_b; not 3 brads: 32; views {'front': 19, 'side': 8, 'back': 7, None: 67}
Feet: 229; views {'side': 125, None: 94, 'back': 2, 'front': 8}; facing unsettled 229; sole vs canon 1.19
Faces: 87 front heads, painted unsettled 87; features {'brow': 87, 'mouth': 72, 'eye': 85, 'nose': 7}; heads with no feature kit: atlantis_crowd, citizen_1, couple_1_a, couple_2_b, dj_cyber, father_02, gatekeeper, traveler_1
Settled by a person: 0 of 2392

## Coverage gaps (forced kitbash), worst first

- **ancestors** (30 cards): no torso, pelvis, upper_arm, forearm, thigh, shin, foot at all; views unknown for hand; missing views —
- **atlantis_crowd** (25 cards): no torso, pelvis, upper_arm, forearm, thigh, shin, foot at all; views unknown for hand; missing views —
- **ancestor_robe** (16 cards): no head, pelvis, forearm, hand at all; views unknown for upper_arm, thigh, shin; missing views torso:side, foot:front, foot:back
- **couple_3_b** (16 cards): no head, pelvis, hand at all; views unknown for upper_arm, thigh; missing views forearm:side, forearm:front, shin:side, shin:front, foot:front, foot:back
- **ex** (200 cards): no — at all; views unknown for —; missing views head:side, head:front, torso:side, torso:front, pelvis:side, pelvis:front, upper_arm:side, upper_arm:front, forearm:side, forearm:front
- **ancestor_elder** (12 cards): no head, forearm, hand, shin at all; views unknown for pelvis, upper_arm, thigh; missing views foot:front, foot:back
- **party_guest** (49 cards): no — at all; views unknown for —; missing views pelvis:side, pelvis:back, upper_arm:front, upper_arm:back, forearm:front, forearm:back, hand:back, thigh:front, thigh:back, shin:front
- **couple_2_b** (20 cards): no pelvis, hand at all; views unknown for upper_arm, thigh; missing views torso:back, forearm:side, forearm:front, shin:side, shin:back, foot:front, foot:back
- **brother_1** (16 cards): no head, pelvis, hand at all; views unknown for upper_arm, forearm, thigh; missing views shin:side, shin:front, foot:front, foot:back
- **couple_1_b** (16 cards): no head, pelvis, hand at all; views unknown for upper_arm, forearm, shin; missing views thigh:side, thigh:back, foot:front, foot:back
- **friend_2** (17 cards): no head, pelvis, hand at all; views unknown for upper_arm, forearm, thigh; missing views shin:side, foot:front, foot:back
- **dj_cyber** (49 cards): no — at all; views unknown for pelvis; missing views upper_arm:front, upper_arm:back, forearm:front, forearm:back, hand:back, thigh:front, thigh:back, shin:front, shin:back, foot:front
