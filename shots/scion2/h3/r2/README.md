# H3 round 2: layered rigs, replacement heads and hands

Round 1 (one front rig, its own head and hands) is kept in `r1/`, together with its code,
outputs, sheet and move, for comparison. Round 2 follows `../BAKEOFF.md`. It keeps the
round-1 base (layered, mesh-skinned painting) and borrows replacement heads and hands
from H2's catalogue of whole paintings. It also adds a 3/4 rig and fixes the round-1
craft defects. This file describes what was done and what can't be done. It does not
grade.

## Masters (`specs.py`)

| view | master | family | used for |
|---|---|---|---|
| front | `poet.11/02-front-guide-stone` | 11 | refocus, 12/02, push-apart, palms-up, crouch, dance, head-back, the move |
| 3/4 right | `poet.10/q1-approach-bike` (walking; the bike is cut away) | 10 | falter, phone-palm |

Neither family is a target family. No profile rig was built: no target needs one once
the 3/4 rig exists, and `gaps.json` covers it. `poet.11/01-wall-rear-three-quarter-touch`
was examined as a 3/4 master and turned out to be a back view.

Layers, back to front:
- **Front rig:** legs (one mesh), torso, head, arm R, arm L.
- **3/4 rig:** far arm, seat with the far leg, near leg, torso, head, near arm. The far
  arm sits behind the jacket and the near arm and near leg in front.

The hidden areas are filled in from the master's own plain fabric:
- the jacket behind each arm, including the chest contour behind the far arm and the
  back contour behind the near arm;
- the trouser waist under the hem;
- the seat under the near thigh;
- the neck under the jaw.

Each layer is a triangle mesh whose vertices are softly weighted to the bone segments
(linear blend skinning). The jacket's shoulder caps partly follow the upper arms.

## Replacement heads and hands (`lib.py`, `lib/`)
Heads and hands are cut from whole suited paintings (H2's catalogue), and each is used
only when its family differs from the target's. `pose.py` asserts this for the master,
the head and every hand of every output.

**Heads** are cut along the collar line and sit into the rig's collar. The seat has no
edge line, and the head is rotated so its own collar lines up with the rig's.

| head | source | view and expression |
|---|---|---|
| `chinup` | 07/chin-up-open-arms | 3/4 right, looking up |
| `reathe` | 11/05-read-water-reathe-1 | front, head thrown back |
| `welcome` | 11/welcome-new-day | front, looking up, mouth slightly open |
| `q1` | 10/q1-approach-bike | 3/4 right, level |
| `setdown` | 06/set-down-03-the-coin | 3/4 right, looking down |

**Hands** are cut by skin colour inside a box and slide under the rig's cuff. A wrist
base and a finger direction orient each one along the rig's hand bone, and any hand can
be mirrored.

| hand | source | shape |
|---|---|---|
| `raisedR` / `raisedL` | 11/welcome-new-day | open, raised |
| `palmupR` / `palmupL` | 07/chin-up-open-arms | palm up |
| `stopR` | 08/07-push-flat | vertical stop palm; mirrored for the left hand |
| `reachL` | 08/07-push-flat | flat, reaching |
| `fist12R` / `fist12L` | 12/02 | fist |
| `fist08L` | 08/03 | fist |
| `fist14R` / `fist14L` | poet.14.muse-dance/cards-2 | fist |

Also available: `cuff`, an empty sleeve opening drawn as an ellipse, and `none`.

Drawings asked for that exist only in a target's own family are listed in
`gaps.json` → `library_gaps`:
- laughing (12);
- no glasses (13);
- hand at the temple or holding sunglasses (13);
- phone (09);
- cup (13);
- pocket and round empty cuff (04).

## Craft changes since round 1
- **No halo.** The painting's own soft brown edge is stripped from every piece when the
  rig is built. Each piece (layer, head or hand) then gets one crisp edge at output
  resolution: a 1.6 px dark-brown line and a 1 px tan hairline (in master px, scaled).
  It is drawn under the piece, so it shows only outside it. The edge depends on the type
  of boundary:
  - **The painting's own outline:** always edged.
  - **A cut** (for example an arm's inner side): edged only where it ends up on the
    silhouette.
  - **A seam meant to read as continuous cloth** (sleeve into shoulder, head into
    collar, thigh into seat): never edged.

  The round-1 tan bands and outer lip are gone.
- **No face warp.** The round-1 "yaw" slid the face texture and made it swim. It is
  removed: a head turn is now a head swap.
- **Every frame rendered once, straight from the master textures.** No frame is made
  from another frame. The video is encoded at crf 17 with `-tune animation`.
- **The move.** `move.py`'s docstring has the frame-by-frame timing.
  - **Steps:** the feet step one after the other with IK. The planted boot stays at a
    fixed world position, and the travelling boot lifts 20 px on an arc and lands.
  - **Weight:** the pelvis sinks in the anticipation and shifts toward the planted foot
    during each step.
  - **Settle:** the arms overshoot and settle (back-out easing).
  - **Breath:** the holds breathe (chest swells 0.8% on a 40-frame cycle).
  - **Swaps:** each hand and head swap lands on a held frame after a one-frame
    anticipation (the forearms cock down before the fists appear, and the fists pull
    in before they open). There are no dissolves.
  - **Height:** the fists reach overhead as in 12/02, because of a +12° upper-arm key and
    a forearm stretch limit of 1.25.

## Posing (`pose.py`, `keys.json`)
Bone angles come from the target's Pose Lab markers measured against the rig master's
own markers: an absolute rotation per bone, with a clamped squash along its axis.
`keys.json` holds the choices the markers can't make, set by eye per target:
- the view;
- the head and hands;
- the wrist turn;
- small bone corrections;
- for crops with unusable markers, a manual placement.

## Outputs
- `out/<id>.png`: 9 reproductions, each an RGBA figure on the target's own canvas.
  `out/sheet.jpg` shows painting | reproduction at the same height. `out/poses.json`
  records the sources used for each output.
- `out/move.mp4` (1600×900, 24 fps, 96 frames, H.264) and `out/move_strip.jpg` (every
  6th frame).
- `gaps.json`: 3 targets not attempted (kneel, lying, seated cup), each with why and a
  painting brief, plus the partial misses for each attempted target and the library
  gaps. `gaps/forced/` shows what the rigs produce when forced to try the 3 gap poses;
  these are evidence, not reproductions.

## What it can't do
- **Fold limbs into depth.** A thigh or shin pointing at the viewer (crouch, kneel, seat)
  can only squash 30% in the picture plane. Crouched knees go sideways.
- **Use a pose drawing that wasn't painted outside the target's family.** This covers
  laughing, glasses off, phone, cup, temple and pocket.
- **Make the far arm of the 3/4 rig read as attached.** Its shoulder is hidden behind
  the chest, so a raised far arm seems to start under the collar.
- **Seat the walking 3/4 master.** It can't sit: the inpainted waist opens into a smear.
- **Keep the jacket from going boxy when an arm is raised.** The jacket sides stay
  vertical and the arm rises out of the shoulder cap.
- **Match poet.12's style.** The thick tan outline and bigger head are not reproduced.
- **Turn the head between views.** A head turn is a drawing swap (a cut), never a turn.

## Run
```
python3 rig.py            # build rig/front and rig/q3r from the masters
python3 lib.py            # cut lib/ heads and hands
python3 pose.py           # out/ stills + sheet (skips gaps.json targets)
python3 move.py 2         # out/move.mp4 + out/move_strip.jpg (2x supersampled)
```
