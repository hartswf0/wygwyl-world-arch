# H2: replacement animation (choose, hold, cut; no deformation)

**Representation.** The paintings themselves, used as replacement drawings. A painting is never warped. It is only placed: uniform scale and translation, plus a mirror where the costume allows. The 12 test poses below use no mirror; the ranker's best was never a mirror except for "lying", which is a gap anyway.

## Files
- `kill/` holds the kill experiment: `sheet.jpg` (target | pick, same scale), three RGBA reproductions, `picks.json`, and `NOTES.md` (what I saw).
- `out/<test id with / as __>.png` are the 12 reproductions (RGBA figure, transparent background, at the target painting's body scale). `out/sheet.jpg` shows painting | reproduction for all 12, labelled with source painting, distance and status. `out/picks.json` holds the pick, the distance terms, the scale and offset, and the runners-up.
- `out/move.mp4` (4 s, 24 fps, 1600x900, H.264) and `out/move_strip.jpg` (every 6th frame). `out/move.json` has the timing, the per-drawing placement and the source of each frame.
- `gaps.json` holds the painting briefs; `gaps/*_ref.png` are their references (a stick figure over the faded target painting, or for the move a stick figure interpolated between the two neighbouring paintings).
- `coverage.md`, `coverage.jpg` and `coverage.json` are the coverage map of all 130 paintings.
- `tools/` contains `catalog_src.py` (my hand reading of all 130 paintings), `h2.py` (distance, placement, sheets), `stills.py`, `move.py`, `gaps.py` and `coverage.py`.

Run order: `python3 tools/stills.py kill && python3 tools/stills.py all && python3 tools/move.py && python3 tools/gaps.py && python3 tools/coverage.py`

## Method
1. **Library.** I looked at all 130 paintings and tagged each (`tools/catalog_src.py`). Only whole figures of the suited poet are eligible (50). Cut, fragment, empty, labelled, multi-figure and ex paintings are excluded, and so is the t-shirt costume (a costume change would break "one man").
2. **Leave-one-family-out.** For a target from `poet.NN`, no painting from `poet.NN` is a candidate.
3. **Distance D** (lower is closer), the sum of:
   - **pose**: screen-space marker error after the best translation and a uniform scale held within ±10% of the body-scale ratio, so a crouch can't be "fitted" by shrinking a stand. Wrists, head and ankles weigh most, and each term is weighted by marker confidence. On top of that, the mean screen-angle difference of the limb bones (it separates arms-out from arms-down). Arm and leg pairing is free (min over swaps), so the comparison is about what is on screen, not about L/R labels. Body unit = the 2nd-longest bone estimate (foreshortening only shortens).
   - **silhouette**: 0.6 x (1 − IoU) of the two alpha masks under that placement.
   - **view**: facing on screen (front, 3/4, profile, back, and which way), from my tags. Front vs back costs most.
   - **posture class**: 0 if the same, 0.1 within upright postures, 0.8 across (standing vs crouch vs sit vs lie), because posture reads first.
   - **hands, gaze, props, costume variant (poet.04 disc), mirror**: small penalties from the tags. Each prop that the target lacks costs 0.15.
4. **Status**: D ≤ 0.55 covered, ≤ 1.10 approximate, above that a gap. I set these thresholds by looking at the picks, not by fitting them.
5. **Placement in the stills**: the fitted scale and offset put the pick in the target painting's frame, so painting | pick are at the same body scale with the feet on one line.
6. **The move**: palms up (04/04-6) → fists up (12/02) → back. In between only other paintings: 05/ask-the-universe-2, 11/welcome-new-day and 11/02-front-guide-stone. I chose them by pairwise pose distance and then by eye, for an arc: dip, throw, hit; release, drop, settle. Timing, all cuts, in frames: palms 14 | dip 6 | open V 6 | fists hit at f26, held 30 | open V 6 | arms low 10 | palms 24. Each drawing is scaled so the head-to-ankle height is equal, the midpoint between the ankles sits on one screen x, and the lowest boot pixel sits on one floor line. A fixed soft contact shadow sits under the feet.
   - Version 1 had two 2-frame dissolves. At full size they read as a translucent double man with four arms and two offset heads, so version 2 is all cuts (the dissolve code is kept).

## Results (description, not a grade)
`out/sheet.jpg`. Every frame is a real painting, so there are no seams, no stretching and no swimming. What fails is the choice of drawing:

| test | pick | D | status |
|---|---|---|---|
| front stand 13/06 | 11/05-read-water-reathe-1 | 0.75 | approximate: holds a book; target has a hand at the temple, glasses off |
| arms up fists 12/02 | 11/welcome-new-day | 0.60 | approximate: open V, open hands, not fists |
| push-apart 07 | 05/ask-the-universe-2 | 0.74 | approximate: arms low with palms up, not pushing out at shoulder height |
| palms up 04/04-6 | 11/02-front-guide-stone | 0.48 | covered: arms a bit lower, gaze forward, no chest disc |
| hand at ear 09/phone-palm | 13/06-refocus | 1.09 | approximate: hand at the temple but frontal, no phone |
| crouch 04/04-4 | 13/03-letter-fire-crouch | 1.55 | gap: 3/4 crouch reaching with a letter |
| kneel 04/04-2 | 13/04-harvest-reach | 1.37 | gap: kneeling forward with flowers |
| seated profile cup 13/part-2 | 11/pool-edge-seated | 1.17 | gap: 3/4, stone block, book |
| lying 05/q3-2 | 04/04-4-sweep-forearms (mirrored) | 2.67 | gap: nothing lies outside poet.05; the pick is a crouch |
| bent-knee dance 08/03 | 04/04-6-rise-flex-reflect | 1.03 | approximate: straight legs, palms up |
| side stride 09/falter | 12/01 | 0.59 | approximate: low lunge, both arms spread |
| head back 08/05 | 07/chin-up-open-arms | 0.51 | covered: chin up, but the head is not thrown back as far |

**The move, as I saw it:** the cuts land on poses, and the dip before the throw reads as anticipation. The pops are between families, not between poses. poet.04 has a chest disc that appears at the start and end and is absent in between. poet.12 has a thick tan outline and a bigger, laughing head that pops in at the hit. Stance width jumps (feet 1.0 → 1.3 → 1.75 torso-widths), and the boots can't stay planted because no two paintings share a stance. Between 05/ask and 11/welcome the arms jump from low to a high V in one cut. Each drawing is upscaled about 1.6x and is softer than the source.

## What it can't do
- **Reach an unpainted pose.** Every miss is a brief in `gaps.json`, never a warp.
- **Keep feet planted across drawings** whose stances differ, or keep scale identical when families paint the man at different proportions. Body-scale normalisation keeps him the same height, but heads and outline weight still change.
- **Remove baked-in props** (book, block, letter, flowers, bike). They come with the drawing.
- **Use painted variants within a family under leave-one-family-out.** In production the poet.04 crouch or poet.05 lying are already painted; the test removes them on purpose.
- **Rely on the markers alone.** On crouches, cut figures and kneels they are often wrong (crossed legs, missing wrists). The silhouette term and my tags carry those cases, and every pick was checked by eye against its painting.
