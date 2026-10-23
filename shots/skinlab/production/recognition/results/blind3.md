# Blind recognition test 3: renderer fixes, re-solved poses, kit props, one-source limbs

**Setup.**
- The same 30 poses as tests 1 and 2, under a new shuffle and new names (d01–d30).
- A fresh critic matched them blind against the same 108 paintings and opened nothing but the blind folder.
- **Changes since test 2:**
  - **Builder B's renderPose fixes:**
    - the seat sits on the hip line;
    - knee width is matched;
    - arms are drawn under the torso unless they are well in front;
    - the torso is clamped to the pelvis;
    - the head follows the body's view;
    - the head matrix and pelvis height are fixed.
  - **Re-solved poses (`poses_v2`):** 88 of 90 were re-solved with the puppet in the loop.
  - **Builder A's harvested cards:**
    - each limb chain is cut whole from one painting, with no mixed chains;
    - kit prop cards (chair, bike, orb, hourglass) replace the silhouettes cut from the target painting.
- The props are kit cards placed where the painting's prop is. That is still a small positional hint, so renders the critic marked prop-led are scored separately.

**Result** (top-1 = the critic's first pick is the right painting; top-2 adds its second pick, which added no further hits this time):

| Subset | Test 1 | Test 2 | **Test 3** |
|---|---|---|---|
| All 30 | 7 | 10 | **14** |
| Test 2's fair 20 (no set piece in test 2) | 6 | 7 | **11** |
| The 22 the critic did not mark prop-led | – | – | **10** |
| The 8 prop-led or partly prop-led | – | – | 4 |
| The critic's "high confidence" picks | – | – | 6 of 7 right |

**Honest read.**
- This is the first gain clearly beyond noise: on the like-for-like 20, test 3 got 11 against 6 and 7 before.
- Confidence is calibrated: when the critic says "high", it is right 6 of 7 times.
- Still, 16 of 30 poses are not recognised.
- No second pick was ever right, so a miss is a real miss, not a near miss.

**Newly recognised:** heart-seated (the seat fix, d29), q2-star-overhead (orb, d09), the hourglass pose (d24), refocus (d15), in-wind on the bike (d30). Those named in test 2 are mostly held: lying, rise-flex-reflect, falter-2, empty-cuffs, slow dance, push-apart, welcome-new-day, coil-to-mount.

**Lost:** phone-palm (d12). It was a high-confidence match in test 2. Now it reads as a hand-on-chest half-figure, with a broken hip seam and a gap between the thigh and the torso.

**Still failing:**
- cafe-sit (d28): the chair is present, but the near arm crosses the body like a plank.
- sweep-forearms (d06): no seat, flat torso.
- the bike pocket and part-14 poses (d07, d20): the figure is crushed into the bike.
- daisy (d05): the flower prop is missing.
- the standing variants (d04, d13, d16, d23, d26).

**Failure causes now (the critic's words), each with its owner:**
1. **Seated and kneeling poses still have no seat or buttocks volume.** The shins fold into a stub, and the knees bend the wrong way in a kneel (d06, d22, d27, d28, d29). Chairs that appear in no painting pull the match onto the prop. → seat mass and sitting/kneeling mechanics in renderPose (B); only props that the paintings actually show (A).
2. **Legs still break into cards,** with jagged torn edges, holes and width steps at the knee and hip (d03, d08, d13, d16, d17, d23). The harvested cut edges are ragged. → clean harvested cut edges by feathering or trimming to the trouser outline, and close the gaps at the hip and knee (A); add an overlap or sleeve at the joint (B).
3. **Heads rolled up to 90° or oversized** (d01, d05, d07, d10, d24, d22). This is the loudest wrong signal. → clamp head roll to the painting's range and check the headScale (B).
4. **A missing or burying prop:** daisy without the flower (d05), the figure crushed into the bike (d07), the orb over the face (d09). → small held props (flower, book, phone handset); the bike placed by its seat and bars, not by the painting's bounding box (A).
5. **Near-identical gestures across paintings** (hand on chest, open palms, walking profile). This is a ceiling that only a distinctive limb angle, hand state (fist vs palm, hands in pockets) or prop can lift. → hand states per painting: fists, pockets (A/B).
