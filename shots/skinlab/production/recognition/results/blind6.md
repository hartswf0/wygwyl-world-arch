# Blind recognition test 6: round 10 (crisp joints and edges, chains from adjusted joints, one scale per figure, held props, crop floor)

**Setup.** The same 30 poses as tests 1–5, under a new shuffle (g01–g30). A fresh critic matched them blind against the same 108 paintings and opened nothing outside the blind folder. Sheet: `poet/blind6_results.jpg` (green = recognised; each tile is painting | puppet | joint atlas).

**Result:**

| Subset | T1 | T2 | T3 | T4 | T5 | **T6** |
|---|---|---|---|---|---|---|
| Top-1, all 30 | 7 | 10 | 14 | 13 | 15 | **19** |
| Top-2, all 30 | 9 | 11 | 14 | 18 | 18 | **23** |
| Top-1, test 2's fair 20 | 6 | 7 | 11 | 11 | 11 | **14** |
| Top-1, renders not marked prop-led | – | – | 10/22 | 9/21 | 7/20 | **11/20** |
| High-confidence picks right | – | – | 6/7 | 2/2 | 4/4 | **6/6** |

**Honest read.**
- This is the first break of the plateau. The fair 20 rose from 11 to 14 after three flat tests, and no previously recognised pose was lost: the gate held.
- New: left-then-right-1, rise-flex-reflect (regained), walk-to-the-gate-2, and gentle-slow-bent-knee-dance (regained).
- **Caveat:** 4 of the 19 were picked at low confidence: walk-to-the-gate-2, left-then-right-1, cafe-sit and the slow dance. Some low-confidence right picks are lucky guesses, so treat the gain as about +2 to +4, not +4 for sure.
- Of the 30 poses, 20 have been recognised at least once in tests 3–6 (21 counting falter-at-shoulder-contact from an earlier test). An earlier count of 22 was my error.

**What changed in round 10:**
- The knee disc and built hip piece were removed.
- Harvested cards have binary edges, with no feather and no upscaling beyond 1.5×.
- Harvested chains are chosen after every joint move, so arm cards reach their hands.
- Boot and limb scale are matched within 10%.
- The orb is held between the hands, and riders straddle the bike.
- Crops keep at least 60% of the figure.

**Still missed (11):**
- part-14 and pockets: the bike crop leaves almost no figure.
- falter-at-shoulder-contact-2 and brace-04-unclench: read as near neighbours (73/68, 48).
- hands-these-poses, chest-lean and ask-the-universe-2: the open-palm family.
- poet.05/1: cropped kneel.
- sag-on-tired: back view in the suit, while the painting shows a bomber.
- sweep-forearms: still unreadable.
- falter-at-shoulder-contact: no diagonal in any painting.

**Failure causes now (the critic's words):**
1. **The open-palm family looks alike.** What tells them apart is missing: the **chest orb** emblem on the jacket in 85 and 98, the head tilted up (76, 80), arms fully straight (15, 87), and fists instead of palms (11).
2. **Side-cropped strips are ambiguous.** The figure in the painting is as generic as in the render. This is a ceiling.
3. **Props carry several matches,** while the figure differs: arms bent where the painting has them straight, one hand where it has two, legs straight where it has a lunge.
4. **Inconsistent cards.** A single leg card is swapped to a different texture or width, with oversized knee rivets and seam steps (g07, g19, g23, g30). Profile and three-quarter heads have no sunglasses and a different realistic face.
5. **Joint and roll errors:** head roll too far (daisy, slow dance, sweep-forearms), folded legs with wrong-way knees, wrists near 90°, detached hands (sag-on-tired, sweep-forearms).
