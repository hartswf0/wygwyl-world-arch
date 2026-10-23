# Test 7: blind recognition 20/30, mean critic 0/30

Round 11 added:
- the chest emblem, fists and pocket hands per painting, and two-handed holds;
- legs from one source;
- profile sunglasses built from the master head;
- straight arms where painted;
- head roll held to the painting.

Two fresh judges (see `MEAN_CRITIC.md`).

## Judge 1: blind recognition (h01–h30)

| | T1 | T2 | T3 | T4 | T5 | T6 | **T7** | pass |
|---|---|---|---|---|---|---|---|---|
| Top-1 of 30 | 7 | 10 | 14 | 13 | 15 | 19 | **20** | 25 |
| Fair 20 | 6 | 7 | 11 | 11 | 11 | 14 | **15** | 16 |
| High-confidence right | – | – | 6/7 | 2/2 | 4/4 | 6/6 | **13/14** | all |

- No pose was lost against test 6.
- Gained: sweep-forearms. It is recognised for the first time, thanks to the chest emblem; it had been called a ceiling.
- The one wrong high-confidence pick was falter-at-shoulder-contact-2, read as 68.
- **Judge 1 does not pass yet.**

## Judge 2: the mean critic (m01–m30, painting | puppet side by side)

**0 of 30 accepted.** Recognition and acceptance are different bars: a puppet can be matched to its painting and still not pass as a finished film. Example: `mean7_example_m01.jpg` (poet.12/02, recognised at high confidence in every test, failed here).

Defect categories, by the number of sheets each kills:

| # | defect | sheets |
|---|---|---|
| 1 | Head wrong in view, roll or gaze: looks up or down, turned away, profile against 3/4, back of head against face | ~19 |
| 2 | Knees break into separate thigh and shin cards with a width step | ~20 |
| 3 | A separate pelvis band or crotch card between jacket and trousers, which the painting doesn't have | ~18 |
| 4 | Boots tiny, splayed outward, rotated, or at mismatched scales | ~18 |
| 5 | The key gesture missing: pocket, phone pressed to the ear, hand at the temple, pointing finger, head on hand, upturned or cupped palms, open cuffs | ~17 |
| 6 | Proportions: torso cropped short, boxy and sleeveless; upper-arm cards oversized; fat limbs | ≥12 |
| 7 | The pose replaced: stance closed up, crouch turned into a sprawl, the wrong view (frontal against a profile stride), an invented pose | ~10 |
| 8 | A floating hand or prop | ~8 |
| 9 | Blurred or jagged cards | ~4 |

Ceilings the critic suggested, to be confirmed next round:
- part-14 (m13): almost all motorcycle;
- cafe-sit (m18): a tight crop;
- poet.05/1 (m15): a narrow strip;
- brace-04-unclench (m30): a two-panel before/after.

## What this means
Rounds 3–11 optimised for recognition, and recognition rose from 7 to 20. The mean critic shows that the drawing system itself is still a paper doll, not the painted man. Every sheet fails on the same structural defects: the pelvis band, knee breaks, boots, torso proportions and head views. These are fixed once, in the contract and the renderer, not pose by pose. Round 12 attacks those first, worst first, judged side by side against the paintings.
