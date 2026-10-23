# Blind recognition test 5: round 9 (painting-decided head, far limbs under, sunglasses heads, props as painted, crops, regression gate)

**Setup.** The same 30 poses as tests 1–4, under a new shuffle (f01–f30). A fresh critic matched them blind against the same 108 paintings and opened nothing outside the blind folder.

**Result:**

| Subset | T1 | T2 | T3 | T4 | **T5** |
|---|---|---|---|---|---|
| Top-1, all 30 | 7 | 10 | 14 | 13 | **15** |
| Top-2, all 30 | 9 | 11 | 14 | 18 | **18** |
| Top-1, test 2's fair 20 | 6 | 7 | 11 | 11 | **11** |
| Top-1, renders not marked prop-led | – | – | 10/22 | 9/21 | **7/20** |
| High-confidence picks right | – | – | 6/7 | 2/2 | **4/4** |

**Honest read.**
- 15/30 is the best so far, but it is within noise of 14 and 13.
- The regression gate worked as intended. Against test 4, it gained 4 poses (coil-to-mount, refocus, part-2, cafe-sit) and lost 2 (rise-flex-reflect, gentle-slow-bent-knee-dance, which came second).
- **The figure-only score is stuck.** The fair 20 has scored 11 for three tests running. The gains come from poses where a prop or crop helps: part-2's chair and cup, the cafe-sit chair, the bike.
- 18 of the 30 poses have been recognised at least once across tests 3–5. No single render set gets all 18.

**Round 9's own bug.** On refocus, the hand-to-head rule moved the wrist, but the harvested arm cards had been chosen for the unmoved arm, so the cards stop about 15 cm short. Refocus was still recognised (medium confidence), but floating hands are now the critic's cause #2 across many poses.

**Failure causes now (the critic's words):**
1. **Blurred joints.** Shoulders, hips and knees show as blurred blobs or width steps, so bent poses read as stiff tubes (f04, f07, f19, f26). This is new: the round 8–9 knee discs, sleeves, feathering and inpainting smear the joints.
2. **Floating hands.** Arm cards don't reach their hands, or the hands land on the torso or crotch (f03, f04, f05, f26, f29).
3. **Scale.** The two boots in one render differ in size, a near-limb card is far too large, and head roll is overdone (f03, f14, f17, f08, f19, f22).
4. **Crops leave too little figure** to match against (f05, f11, f13, f20, f28).
5. **Props carry the match:** the orb isn't held, a card fragment covers the hourglass, the rider's legs are jumbled (f08, f10, f24).
