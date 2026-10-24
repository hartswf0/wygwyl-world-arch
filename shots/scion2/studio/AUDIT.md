# Audit: why we keep choosing odd pieces, checked against the animation swarms

This audit is source-checked against the 54 swarm prompts in `SCION_Swarm_Operator.html` and against our own measurements. Every claim below is labelled:
- **measured**: from our numbers;
- **viewed**: I looked at the renders;
- **critic**: from an independent critic;
- **inferred**: my reading.

## The finding in one line
Every method we built fills a gap in the drawings with the nearest wrong thing. The swarms agree that when a pose isn't in the drawing, you swap to a drawing that has it. When no drawing has it, you commission one. You never bend or assemble one to fit.

The swarms that say this include:
- Pose2Pose;
- Dynamic Pose Selection;
- the Multiview Turn Lab;
- Cartoon Saloon, Harmony and Moho;
- the repair rules of ARAP and MLS.

## Assumptions, where they live, and what the swarms say

| # | Assumption we made | Where | Swarm that contradicts it | Evidence | Action |
|---|---|---|---|---|---|
| A1 | One master painting per view can be bent into every pose | `rigkit` (H3 rigs), `studio` proof01 | ARAP repair ("add explicit cuts or draw swaps"); Moho ("swap or redraw rather than scaling anatomy"); Cartoon Saloon ("replace important drawings"); Multiview Turn Lab | **Viewed:** the gown crumples when the woman walks; the poet's walk is bent from a painting of him approaching a motorbike. **Measured:** proof01's checks all pass anyway. | Bend only within a drawing's own neighbourhood (small secondary moves); change pose by swapping drawings |
| A2 | Parts from different sheets can be assembled into new bodies | `library2`, the joint lab (8 rounds) | Cartoon Saloon ("rigs do not betray construction"); Max Ernst (seams deliberate or concealed); Gilliam (paper boundaries intentional) | **Critic:** at best 5 of 12 joints passed (round 8), and no full body was ever made | Stopped. Keep library2's QA checks for checking drawings, not for building bodies |
| A3 | An actor is whoever has a rig | proof01 casting | Pose2Pose ("if no drawing captures a vital moment, request new artwork") | **Measured:** the vintage man and woman have 8 paintings each, 5–6 of them dance poses, yet were cast to walk, grasp and fall | Cast by coverage (below), not by which rigs exist |
| A4 | The cutout is the figure | the poet's library | GrabCut and SAM swarms (separate the subject from its accessories); Provenance Graph | **Measured:** 38 of the poet's 90 paintings carry props or scenery in the cutout (a table, a motorbike, a stone pillar, a door frame). The selector chose a table-lean for a walk. | `select.library` now drops cutouts with props unless the scene asks for that prop. Recut the props as separate layers. |
| A5 | Proxy scores mean quality | `seam.py`, critic v1, our checks | Doctrine items 9 and 14 ("do not replace perceptual criticism with numerical proxy scores") | **Measured:** seam.py agreed with the critic on 8% of judged joints. **Critic:** v1 failed 3 of 4 unaltered paintings. | Use the style-anchored critic with hidden painting controls. Geometry checks only cover what geometry can measure. |
| A6 | The floor is a line | proof01 | Multiplane and Occlusion swarms | **Measured:** in a 3/4 drawing the far foot sits 12–30 px higher; treating the floor as a line made planted feet slide 4–28 cm | Fixed: each foot stands at its own depth |
| A7 | Smooth is better | rigkit easing, joint lab | Gilliam ("visual logic over smoothness"), Reiniger, South Park (limited animation as style) | **Inferred:** rounds were spent hiding swaps that the style would show | Swaps on held frames, animated on twos or threes, are the grammar |
| A8 | Generate the motion first, then find drawings for it | proof02 | Exposure sheets (Harmony); Dynamic Pose Selection ("minimum-duration holds") | **Measured:** a target taken from the bent rig left 108 of 132 frames with no clean drawing; the target itself was crouched and off-model | Write the performance in terms of the drawings that exist (the exposure sheet) |
| A9 | Every character's drawings are labelled | catalogs | Provenance; SAM ("refuse to infer invisible parts") | **Measured:** angel, citizen, dj, traveler and both ancestors have no view labels, so none of their paintings can be selected | Label views. Until then these characters are blocked. |

## The simple method the swarms converge on: exposure-sheet animation from whole paintings
Code is in `studio/exposure.py`; the proof is in `studio/proof03.py`.

1. **Vocabulary.** Each actor's clean paintings: one costume, a full figure, no scenery in the cutout. Each is tagged by view (front, 3/4, profile, 3/4-back, back) and posture.
2. **Sheet.** A list of beats. Each beat names a painting by id or by view (optionally mirrored), a hold in frames, an optional travel distance, and whether it lands with a settle.
3. **Placement.** One size per actor (from the marked legs and torso). The lowest painted pixel sits on the floor. The body centre carries over from the previous beat unless the beat travels, so a swap never jumps.
4. **Turns are rings of views.** A spin runs 3/4, profile, 3/4-back, back, then the far side mirrored. The ring is resolved from each actor's own drawings. A missing view holds the previous drawing, so every actor's spin has identical beats.
5. **Gaps are commissions.** A beat no clean drawing covers is reported as a drawing to make. It is never filled with the nearest wrong one.

### What proof 03 shows (measured)
| | frames | floor error | jump at a swap | drawings | size spread |
|---|---|---|---|---|---|
| spin, casting A (man / woman) | 85 / 85 | 1.0 / 0.5 px | 0.0 cm | 7 / 7 | 9.3% / 6.1% |
| spin, casting B (roles swapped) | 85 / 85 | 0.5 / 1.0 px | 0.0 cm | 7 / 7 | |
| the poet's five beats | 116 | 1.0 px | 0.0 cm | 5 | 5.7% |

Recast: identical beats on identical frames in both castings (**measured**). Every frame is an intact painting; no pixel of any drawing is bent (**structural**).

### Critic (blind A/B against proof01's bent rigs; full text in `proof03/critic.md`)
**The exposure sheet is stronger: 5.5/10 against 3.5/10.**
- **Exposure sheet:** every frame stays on-model, and the spin reads as a full 360° turn.
- **Bent rigs:**
  - the gown turns into a garbled drawing for about 3 seconds;
  - a foreign hook-shaped piece hangs on the man in the pinstripe suit;
  - the walk is a crouched shuffle.

The exposure sheet's largest gap:
1. **The walk** is one frozen stride sliding across the floor, because only one clean walk drawing exists.
2. **Beat changes** are one-frame pops.

The repair condition: the leading boot alternates at least every 0.5 s, planted boots stay within ±3 px, and each beat change has at least 2 in-between frames with nothing broken.

**Next steps:**
- **Walk:** commission the 3/4 walk cycle, which is the real fix. As a stopgap, test a bend limited to each drawing's own neighbourhood (at most 15°, toward the next drawing's pose) for 2-frame in-betweens. Judge that stopgap by the same blind critic.

## Coverage and commissions
`studio/coverage.json` lists each character's clean drawings by view and posture. The gaps that block the poems:

- **Poet (track suit):** 21 clean drawings, but:
  - one clean 3/4 walk drawing, where a walk needs at least two contacts and two passings;
  - no clean neutral 3/4 stand;
  - no back views in this costume.

  **Commission:** a 3/4 walk cycle (4 drawings), a neutral 3/4 stand, a back stand and a back 3/4.
- **Vintage man and woman:** complete dance turnarounds (profile, 3/4, 3/4-back, back), but:
  - no walk, sit or front dance;
  - the man's only front drawing is a stiff stand cut from a different card.

  **Commission:** a front dance pose each and a 3/4 walk pair each.
- **The ex:** 15 clean drawings, all back or 3/4-back, which is consistent with the design rule that the ex is only ever seen from behind. This is not a gap.
- **Blocked until views are labelled:** angel, citizen, dj, traveler, both ancestors.
