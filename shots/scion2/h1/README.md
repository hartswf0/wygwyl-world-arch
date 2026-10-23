# SCION 2 / H1: pose graph + mesh warp (deform the nearest painting)

Builder H1. Inputs: the paintings (`shots/kits/cut/poet.*.main-poses/*.webp`), the Pose Lab
markers (`targets[].markers` in `shots/rig/poses_v2/poet__red_black_sunglasses.json`; the
solves, cards and puppet fields in that file are not read), and `shots/scion2/test_set.json`.
No code or data from the card-puppet run.

## What is here

| path | what |
|---|---|
| `h1core.py` | source curation, bones, view features, capped re-posing (`fit`), pose distance and ranking |
| `h1warp.py` | part masks, hidden-torso fill, joint-continuous skin weights, triangle mesh warp |
| `h1render.py` | one render: nearest painting -> layered warp toward the target markers |
| `h1run.py` | `python3 h1run.py kill` / `all`: the reproductions and the side-by-side sheets |
| `h1move.py` | the 4 s move |
| `h1gaps.py` | writes `gaps.json` from `out/runs.json` |
| `kill/` | kill experiment: 3 poses, `sheet.jpg` = painting / H1 / the same source with the cap lifted (diagnostic only) |
| `out/<id>.png` | 12 reproductions, RGBA, figure only, scaled to the target painting's figure height |
| `out/sheet.jpg` | painting / H1 for all 12, same height; "NOT REACHED (cap)" printed where the pose is not reached |
| `out/runs.json` | per pose: source painting, mirror, rotation applied per part, rotation wanted beyond the cap, torso-fill donor |
| `out/move.mp4`, `out/move_strip.jpg`, `out/move_log.json` | the move, every 6th frame, which painting each frame comes from |
| `gaps.json` | poses not reached, what is missing, and a brief for the painting that would close each gap |

## Method

1. **Sources.** 29 whole paintings in the red/black suit, not cut at the sheet edge and without a
   held prop (the list and the reasons for every exclusion are in `h1core.py`). One more
   (`13/03-letter-fire-crouch`) is used with its envelope colour-keyed out. Benches were also tried
   and dropped: keying the bench out cuts him along the bench edge.
2. **Pose distance (leave-one-family-out).** For a target, every source of another `poet.NN`
   sheet is tried as painted and mirrored (and with L/R marker labels of arms or legs swapped,
   penalised, for mislabelled markers). Each candidate is re-posed toward the target (step 3) and
   scored by: marker error after re-posing (in torso lengths), the amount of rotation used,
   rotation wanted beyond the cap, view difference (signed shoulder and hip width, face direction),
   foreshortening difference per limb, crossed-legs mismatch, and the painted chest emblem
   (sheet 04 paints a glowing emblem the other sheets don't).
3. **Re-posing with caps.** Every part keeps its painted length (one global scale). Each part
   (torso, head, upper arm, forearm+hand, thigh, shin) turns toward the target direction by at
   most **30°** in the picture plane, the head by at most **20°**. Boots ride rigid with the shin
   (the toe markers are silhouette guesses). Crossed legs in the source ride with the torso.
4. **Part masks.** Each figure pixel is owned by the nearest bone capsule (radius measured from the
   painting's own thickness). A limb owns only what lies past its root joint; the shoulder slope,
   collar and the jacket hem down to the crotch stay with the torso; the head owns only what is
   above the neck and away from the shoulder rivets.
5. **Layers.** Legs (behind), body (torso + head), arms (in front), each warped as its own
   triangle mesh, so an arm in front of the chest moves without dragging the chest.
6. **Skinning.** Each vertex follows its own part rigidly, except near a joint, where the two parts
   that meet share a smoothed ownership map tapered by distance to the joint. Because the weights
   come from one smooth map, both sides of a cut between two layers move the same way at the
   joint: the arm bends into the shoulder instead of tearing from it.
7. **Hidden regions.** Torso pixels the painter covered with an arm are filled from another
   painting of him (another family than the target's, arms clear of the torso, nearest view),
   registered by shoulders/hips/neck/groin with a similarity transform and tone-matched; the
   shoulder joint itself is not filled (no second rivet). Limb roots are also drawn under
   everything, carried by the torso, to close the wedge a turning limb opens; that underlay is
   clipped to the closed silhouette so it never sticks out.
8. **Edges.** The painted light cut-out rim is dropped where a moved part carries it inside the
   figure; a cut between parts that ends up against the background gets a soft dark edge.
9. **Scale.** The result is cropped and scaled so the figure is as tall as the target painting's.

**The move** (`h1move.py`): the two keys are placed at the same body size (neck-to-ankle span).
Each frame's target is interpolated in bone-angle space with eased holds on the keys. The frame
is the nearest painting in the pose graph (all clean paintings, keys included) warped toward that
target with the same caps. The painting changes when another is clearly nearer or when the current
one would need more than the cap and another needs less. At the keys the method returns the
paintings themselves (zero rotation). A 3-frame dissolve at painting changes was tried: it shows
two men at once, so the changes are cuts.

## What it can't do (by construction)

- **Reach a pose no painting is near.** With a 30° cap the result is only as close as the nearest
  painting of another family. Of the 12 test poses, 4 are within the cap (or within 15° beyond it
  on forearms): arms up (from 11 welcome-new-day), push-apart (from 05 ask-the-universe), palms up
  (from 11 02-front-guide-stone), side stride (from 07 o06-point-at); 08 head-thrown-back is
  within the cap on the arms but the head is not thrown back. The other 7 are not reached: the
  front stand (a hand at the head: forearm 120-165° away), hand at ear, crouch, kneel, seated
  profile, lying and bent-knee dance. No other family has a crouch, kneel, seated profile or lying
  painting usable as a source. These are rendered at the cap (so the output is a different pose)
  and logged in `gaps.json` with briefs.
- **Change hands, face or expression.** Markers carry no hand shape: the fists target gets open
  waving hands, the push target gets palms up, the laughing face stays the source's face.
- **Change foreshortening or view.** A painted three-quarter limb stays three-quarter; a profile
  can't be made from a front painting.
- **Invent hidden limb drawing.** Only the torso has a hidden-region fill. When legs painted close
  together are spread, the inner thighs and crotch open a V whose edges were never drawn.
- **Keep one drawing across a move between different paintings.** The sheets differ in costume
  (04's chest emblem), outline (12's thick tan sticker border), head size and expression; when the
  move changes painting the drawing changes in one frame.

## Failure list (what I saw, comparing each output with its painting at the same height)

- Kill experiment: none of the 3 poses is reached. Front stand comes out as a standing man with
  open arms instead of a hand at the head; crouch comes out as a standing knee-bend with pushing
  palms; seated profile comes out as a leaning walking man (from 04 walk-hollow). The
  uncapped diagnostic shows what the cap prevents: folded forearms and shredded, detached
  shins.
- `out/`: 7 of 12 in the wrong pose (see above); lying is a standing man at a lying painting's
  height. Where the pose is reached the figure reads as his painting (the warp is small), with
  these visible defects: small jagged slivers at the inner thigh / crotch when legs are spread
  (palms-up, push-apart, arms-up); a short notch at the back of a bent knee; occasional thin red
  stripe fragments at the forearm where the elbow bends; on the kneel and hand-at-ear outputs
  a small light sliver near the hip / knee.
- Move (`out/move_log.json`): palms-up painting warped for frames 0-~25, a cut to 11
  welcome-new-day for 2-3 frames, a cut to the 12/02 painting, held, then the reverse. At each
  cut the drawing changes: the chest emblem disappears, the head size and the outline thickness
  change, open hands become fists. Before the first cut the warped palms-up drawing shows torn
  dark flaps under the left armpit and a jagged V at the crotch as the legs open.
