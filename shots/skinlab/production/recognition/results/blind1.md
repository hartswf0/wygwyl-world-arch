# Blind recognition test 1: baseline (stub renderer, before the per-view mechanics)

**Setup:**
- 30 puppet renders, randomly sampled from the 76 eligible poet poses. Excluded: the 11 paintings of the ex, the 8 cut-off references, and the T-shirt costume.
- Each render was matched against all 108 shuffled paintings by a fresh critic, who could not see the key.
- Renders came from Builder A's harness through a stub over PuppetCore.solve/drawCard: rigid cards pinned at brads, no view-specific mechanics.

**Result:**

| Measure | Correct |
|---|---|
| Top-1 (named painting) | 7 / 30 (23%) |
| Top-2 (either candidate) | 9 / 30 (30%) |
| Chance | ~1% |

- **Recognised:** arms overhead (q2-star-overhead), goalpost arms (12/02), squat with raised forearms (04-4-empty-cuffs), palms raised (04-6-rise-flex), V-arms (welcome-new-day), kneel/seated (04-2-heart-seated), arm stretched out (in-wind), falter-at-shoulder-contact, lying (q3-restless-lying-2, as second choice). They were recognised by a distinctive arm silhouette, almost all in front view.

**Failure causes (the critic's own words, summarised), each routed to an owner:**
1. **Head cropped or buried** in ~12 of 30. A framing bug in the harness → builder A.
2. **Missing props and set pieces** (bike, cup, chair, mic): seated poses float. → harness: draw the painting's prop silhouette or the kit's prop card (builder A).
3. **The body falls apart into cards:** gaps at the waist and hip, X-crossed legs, breaks at the knee. → renderer mechanics (builder B).
4. **Bowed/diamond legs** on every front-standing pose, so the poses can't be told apart. → front-view leg mechanics (builder B).
5. **Foreshortening and scale:** limbs toward the camera drawn as flat ovals, oversized boots and shins in close-ups, far arm across the chest, wrist past 90°. → harvested foreshortened cards (builder A) plus per-view rules (builder B).

**Next blind test:** the same 30 poses after the fixes, with a fresh critic and a new shuffle.
