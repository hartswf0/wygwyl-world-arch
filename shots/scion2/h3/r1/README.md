# H3: one painting made into a layered rig

SCION 2, hypothesis H3 (Live2D / Spine style). One front painting of the poet is cut
into overlapping layers. Each layer's hidden area is filled in, and the layers are bent
by soft mesh skinning toward each target painting's Pose Lab markers. This file
describes the method. It does not grade the results.

## Master
`poet.11.main-poses/02-front-guide-stone`: front view, standing, arms held away from
the body with the palms up, sunglasses on, red and black tracksuit, 414 px tall.
Family poet.11 is not a target family, so leave-one-family-out holds for all 12
targets. No profile or 3/4 rig was built; `gaps.json` explains why.

## Parts (`rig/layer_*.png`, built by `rig.py`)
Back to front:

| layer | content | bones (soft weights) | hidden area completed |
|---|---|---|---|
| legs | both trouser legs, the waist and crotch, and both boots, as one mesh | pelvis (bound down to the crotch apex), thigh, shin and foot for each leg | trouser waist under the jacket hem, inpainted from the master's plain trouser fabric |
| torso | jacket with hem, collar and shoulder caps | chest above, pelvis at the hem, with a smooth blend between them; each shoulder cap is up to 60% weighted to its upper arm, so a raised arm lifts it | jacket side under each upper arm and the neck under the jaw (inpainted from the master's own fabric and skin; piping, brass and edge pixels are excluded as sources) |
| head | face and hair above the collar | head | none |
| armR, armL | sleeve, forearm and hand, one mesh per arm | chest (at the collar), upper arm, forearm and hand | none; the top of the sleeve fades into the torso's shoulder cap |
| brads | the painting's own shoulder, elbow, hip and knee brads | ride their joints rigidly and are never rotated, so the highlights keep the painting's light | none |

**Skinning.** Each mesh is a triangle grid over its layer's alpha, with a 2 px step.
Each vertex is weighted to the layer's bones by a softmax of its distance to each bone
segment. Joints therefore bend across a band of cloth instead of hinging at a cut, and
a bone can also squash along its axis to show foreshortening.

**Rendering.** The deformed mesh is rasterized into a per-pixel lookup into the
master's texture (upsampled 3x, bilinear), so every pixel comes from the painting.
Where a fold overlaps itself, the distal part draws over the proximal part. A
later fragment replaces earlier cloth only where its own texel is painted. A margin
triangle that is stretched past 1.8x its painted size is dropped, so the paper edge
is not smeared across the gap when the legs spread.

**Paper edge.** Each layer stores its cut edges, meaning the places where it ends
inside the painted figure. When a cut edge ends up on the silhouette with nothing
behind it, it gets the painting's tan paper edge. When it lies over the jacket, an arm
gets a thin dark contour, as the painting draws a sleeve over cloth.

**Borrowed drawings.** The two raised fists in `poet.14.muse-dance/cards-2` are swapped
in for the hands on 12/02 and 08/03 and in the move. They are rigid attachments on
the hand bone, tucked into the cuff.

## Posing (`pose.py`, `keys.json`)
- **Scale:** the median of the torso, legs, shoulders and arms length ratios between
  the target's markers and the master's.
- **Bone angles:** each bone turns by the absolute rotation that takes the master's
  marker-to-marker direction to the target's.
- **Bone lengths:** each bone squashes along its axis by the length ratio, clamped
  (0.62 to 1.15 for arms, 0.7 to 1.12 for legs).
- **Chest lean:** clamped to ±35°. Beyond that, the whole figure turns.
- **Animator keys:** `keys.json` holds keys the markers cannot give, set by eye for
  each target. They cover:
  - wrist rotation;
  - head tilt;
  - face "yaw", which slides the features inside the fixed head outline by up to
    10 px;
  - hand swaps: `fist`, or `none` for the empty cuffs.

## The move (`move.py`)
96 frames at 1600×900, 24 fps, all rendered from the rig. The end poses are the rig's
own reproductions of the two paintings, not cross-fades. Bone angles are eased. The
legs are solved by two-bone IK so the boots stay on one floor, the travelling foot
lifts on a small arc, and the pelvis dips through the change. The hands change from
open palm to borrowed fist by a one-frame replacement swap (a dissolve ghosted both drawings) while the forearms are moving
fastest. Outputs: `out/move.mp4` and `out/move_strip.jpg` (every 6th frame).

## Outputs
- `kill/`: the kill experiment (push-apart, palms-up, bent-knee dance) and its sheet,
  as first rendered. The rig was refined afterwards: crotch binding, shoulder caps,
  stretched-margin culling, wrist keys.
- `out/<id>.png`: RGBA figures on the target painting's canvas for 8 of the 12 targets.
  `out/sheet.jpg` shows each as painting | rig at the same height.
- `gaps.json`: the 4 targets the front rig cannot attempt (3/4 hand at ear, seated
  3/4 with cup, kneel, lying), with painting briefs, and the partial misses in the
  8 it did attempt. `gaps/forced/` shows what the rig produces when forced to try the
  4 gap targets; these are evidence, not reproductions.

## What it can't do
- **Turn.** The chest, hips, boots and face stay frontal. Yaw slides the features about
  a quarter turn at most. Head pitch (looking up, head thrown back) is impossible.
- **Fold into depth.** A thigh or shin pointing at or away from the viewer (crouch,
  kneel, seat) can only squash 30% in the picture plane. A crouch then spreads its
  knees sideways.
- **Show what the master doesn't have:**
  - the poet.04 chest emblem;
  - an open laughing mouth;
  - sunglasses off;
  - props;
  - the round open sleeve ends of the empty-cuffs painting (the rig's cuffs are flat
    cuts).
- **Fold the elbow fully.** Bends past about 140° crumple the inner sleeve. The brad
  covers the centre of the fold but not its inner edge.
- **Raise an arm without the torso going boxy.** With the arm up, the jacket's sides
  stay vertical and the arm grows out of the top of a shoulder pad. The jacket does
  not ride up.
- **Make every hand drawing.** Only the master's two open palms (rotated by wrist
  keys) and the two borrowed fists exist. A relaxed hanging hand or a hand holding
  something is an open palm turned.
- **Keep inpainted areas sharp.** These areas (jacket side, trouser waist) read as
  softer, smudgier fabric than the painting where they are uncovered: the torso's side
  under a raised arm, and the waist when the pelvis tilts against the chest.

## Run
```
python3 rig.py            # build rig/ from the master
python3 pose.py kill      # kill/ sheet
python3 pose.py all       # out/ stills + sheet
python3 pose.py forced    # gaps/forced/ evidence
python3 move.py 2         # out/move.mp4, out/move_strip.jpg (2x supersampled)
```
