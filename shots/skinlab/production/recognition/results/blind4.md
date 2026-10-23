# Blind recognition test 4: round 8 (head canon and clamp, seat cloth, sleeves, clean harvest, props, hand states)

**Setup.** The same 30 poses as tests 1–3, under a new shuffle (e01–e30). A fresh critic matched them blind against the same 108 paintings and opened nothing outside the blind folder.

**Result:**

| Subset | Test 1 | Test 2 | Test 3 | **Test 4** |
|---|---|---|---|---|
| Top-1, all 30 | 7 | 10 | 14 | **13** |
| Top-2, all 30 | 9 | 11 | 14 | **18** |
| Top-1, test 2's fair 20 | 6 | 7 | 11 | **11** |
| Top-1, renders the critic did not mark prop-led | – | – | 10/22 | **9/21** |
| High-confidence picks right | – | – | 6/7 | 2/2 |

**Honest read.** Round 8 did not move recognition: 13 against 14 is flat, within noise. The renders are cleaner, with clean legs, painted-size heads and no hip gaps, and the critic's second pick is now right 5 more times, so more misses are near misses. But the same number of first picks are right.

**Gained:** pluck-the-daisy (the flower is in the hand) and phone-palm (the hand at the ear). These were both targeted fixes.

**Lost** (`blind4_lost_vs_blind3.jpg` shows test 3 | test 4):
- **refocus:** in test 3 the head tilted toward the raised hand. Round 8's head-roll clamp straightened it, and the critic now reads it as a wave. **A global clamp erased an identifying feature of the painting.**
- **coil-to-mount:** the same cause. The upright head no longer matches the painting's lowered crouch.
- **falter-at-shoulder-contact-2:** the trouser top and clean legs changed its silhouette. It now reads as hand-on-chest (68).
- **part-2:** the chair was removed as "not in the painting", but the painting does show a chair at its cut edge. The cup sits at the knee, not at the mouth. Now the seated figure floats.

**Lesson (a process failure, not just a render one).** Each builder judged its fixes on the poses it was told about. The changes were global (the head clamp, the trouser top, prop removal), and they cost poses that already worked. From now on, every round must pass a **regression gate** before it counts:
- re-render all 30;
- set every previously recognised pose next to its last recognised render and its painting;
- reject any change that loses a recognised pose's identifying feature.

Global clamps must yield to the painting's own markers: per-painting `headLeanDeg`, and per-painting props as painted.

**Failure causes now (the critic's words):**
1. Far limbs and hands drawn over the torso or face hide the gesture (e08, e10, e12, e23, e30).
2. Leg chains in kneels and crouches: knees bend backwards or crumple, and boot scale is mismatched (e08, e16, e22, e24, e27, e28).
3. Seated and riding poses have no seat volume and no seat card; the figure floats or sits through props, and bike matches depend on the bike (e03, e07, e12, e21, e26).
4. A profile head on a frontal torso, residual head roll, and width steps at the shoulders and hips (e14, e16, e18, e30, e02, e05, e19).
5. The generic standing palms-out family (28/52/85/86/101) loses the weight shift, foot spread and hand shape that tell its members apart.
