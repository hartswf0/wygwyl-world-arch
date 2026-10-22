# Animation library: notes on the retarget

Acting Arena acts re-solved onto the poem-kit cut-out characters.

- `retarget.py`: the solver. Run `python3 shots/stage/anim/retarget.py` to rebuild every clip and `index.json`, or `retarget.py <character> ACT-001 ACT-003` for a few clips.
- `rigs.py`: one rig spec per character. It lists the cards and resolves each card's pivot and socket points from the cutter's brads plus the alpha channel. `python3 rigs.py <character>` prints the resolved points.
- `render.py`: a Pillow renderer used for checking (`--strip clip.json f f f --out x.png`).
- `index.html`: the viewer. It shows a line-up at true relative scale on one floor, plus a tile per clip with its checks.
- `clips/<character>/<ACT-id>.json`: same display-list format as `shots/arena/clips` (`images`, `frames[].draw[]` with `{t:'img', id, m}`, `beats`, `clock`, `technical`). Two additions:
  - `shade` on far-limb ops in profile.
  - `dbg.gap/drift/miss` per frame.
- **Image paths are relative to the clip file.** `../../../../` from `clips/<character>/` is `shots/`, and `image_root` says so. Most paths point straight into `shots/kits/cut/` and `shots/kits/packs/`. Eight cut parts still carried their sheet's panel-frame lines. For those, `rigs.py` writes a copy with only the largest opaque island to `shots/stage/anim/parts/`. `cut/` itself is never modified.
- `frames/`: verification PNG strips rendered from the final clips.

## How a clip is solved

1. **Source.** The input is the Bolas Crash Lab 3D joint bank (`shots/arena/bolas/bank/T1NN.json`, cm, floor y=0). This is the same motion the `ACT-NNN__*.json` arena clips were compiled from. Starting from 3D, not from the 2D frames, is what lets each body keep its own proportions.
2. **3D retarget.**
   - The source is scaled by `r = target hip height / 95 cm (Bola)` about the camera's ground point. A planted source foot therefore stays planted.
   - Bone directions come from the source. Bone lengths come from the character (`props` in `rigs.py`, as fractions of height, so the total is exactly `height_cm`).
   - Each leg is two-bone IK from the hip to the foot card's ankle **brad**. That brad sits wherever the boot card puts it, often 11–19 cm up the shaft, so the shin is `knee height - brad height`.
   - The pelvis drops, smoothed, wherever a leg cannot reach.
3. **Projection.** The act's own camera yaw and elevation are used, but at one fixed scale for every clip (`K = 4.038 px/cm`). Clips are therefore comparable in size.
4. **Card chain (2D).**
   - The torso card (waist brad to neck brad) is the root.
   - The head hangs on the torso's neck brad, the arms on its shoulder brads, and the hip bridge on its waist brad.
   - The legs are 2D IK from the bridge's hip brads to the ankle target.
   - Every card is scaled from **cm, never from its sheet's pixel size**: segment length in cm × K / card brad-to-brad px. This is what stops heads, hands and feet ballooning when sheets were drawn at different resolutions.
   - Limbs and feet may shorten along their axis for foreshortening, clamped at 0.45–0.5. Heads and hands are rigid.
   - If the brads a leg must join are farther apart than the foreshortened cards reach, the cards first get their length back (up to their real length). Beyond that they stretch by at most 4%. Past that, the foot follows the leg, so a brad never opens. Any slip that causes is counted as drift.
5. **Contact pass.**
   - While the source heel or ball is down, the drawn contact point is pinned in screen space. That is the card's heel while the heel carries the load and the card's ball (77% along the sole) once it moves to the ball.
   - When the load moves from heel to ball, the pin is handed over with the ankle kept continuous.
   - When the foot swaps card (flat, heel-up or toe-up states, or a mirror flip), the contact point is kept where it is and the leg absorbs the ankle shift. The sole therefore does not pop.
6. **Checks** are measured on the drawn cards, not on the skeleton:
   - `brad_gap`: the distance between the two brads that should coincide, at every joint.
   - `planted_drift`: the movement of the same contact point between consecutive frames, counted only when that point was down on both frames.
   - `height_cm`: drawn sole to head-card top, median of the first 12 frames.
   - `source_slide`: the Bolas foot's own slide on the same frames, for comparison.

Tolerances are the arena's: drift 0.6 cm/frame, brad gap 2.0 cm.

## Result (31 clips)

| | ACT-001 walk | ACT-003 crouch | ACT-008 stand after fall | ACT-017 dance | ACT-024 wait | more |
|---|---|---|---|---|---|---|
| poet_tracksuit (180) | **pass** 0.09 | fail 2.29 | **pass** 0.14 * | **pass** 0.09 | fail 0.81 | 002 fail 0.70, 007 **pass**, 013 fail 1.88, 019 **pass**, 023 **pass** |
| poet_tshirt (180) | **pass** 0.52 | fail 2.29 | **pass** 0.16 * | fail 1.29 | fail 1.13 | |
| young_poet (122) | **pass** 0.43 | fail 1.34 | **pass** 0.11 * | fail 1.07 | fail 1.04 | |
| woman (165) | **pass** 0.57 | fail 2.18 | | fail 1.36 | fail 1.10 | |
| ex (183, back only) | **pass** 0.08 | fail 2.34 | | | fail 0.83 | |
| party_guest (178) | **pass** 0.59 | | | fail 1.46 | fail 1.22 | 019 fail 1.42 |

Values are the worst planted drift in cm/frame. The brad gap is 0.00 cm in all 31 clips. `*` marks a pass with the floor frames flagged (see "What still fails" below). Every fail is planted drift above 0.6 cm/frame, and it is a handful of frames, not a slide. For example, the crouch fails on 2 frames (59 and 75) in every character, at the moment the load moves from heel to ball. The per-frame values are in `frames[].dbg.drift`.

## Per character

### POET, black/red tracksuit (poems 04–14)
- **Cards:**
  - Profile body: `poet.red_black_sunglasses.body.profile`.
  - Front body: `.body.front` with the pack's `19/20_boot_front`.
  - Back body: `.hipcore/2-3` torso, `.hipcore/5-rear-seat` and `.body.back` limbs.
  - Heads: `.heads` (5 views).
  - Profile feet: the `.feet` flat, heel-up and toe-up state cards.
  - Sunglasses: the pack's `31_sunglasses_front` for the front, `master/front-2` for 3/4, and `master/sunglasses-right` for profile, scaled to the head card.
  - Hip bridge: `.hipcore/4-hip-bridge`. It is always drawn under the thighs, and in profile it is squashed edge-on and hidden.
  - No shorts or pelvis cover is ever drawn in front view.
- **Proportion problems and fixes:**
  - The profile torso card has only neck and waist brads. The shoulder is a hint at (0.42, 0.16).
  - The cutter's `pivot` for the torso is a false brad on the top edge, so the neck uses the grommet at (0.58, 0.077).
  - A 13.5 cm bridge left a dark gap of bridge between the jacket hem and the thighs. The tracksuit uses `bridge = 0.035 H`, so the hem meets the thigh tops.
  - Feet were 35% oversized until the foot length was measured to the toe tip instead of the lowest toe pixel. They are now 26 cm for a 180 cm man.
  - The Chelsea boot's ankle brad is 11 cm up the shaft. The shin card ends there.
- **Height:** drawn 172–176 for a 180 target. Bola stands with bent knees, and the walk is "carrying a full cup", head down.

### POET, black t-shirt (poems 01–03)
- **The kit has no side-view body:** `poet.black_tshirt.compact-core` is front/back only. Side-on frames use the front torso and front limbs with the profile shoes and the tracksuit's heads (same man, no sunglasses). That is a "front torso walking sideways" construction, and every clip says so in `problems`.
- The front hip bridge's hip brads are 27.6 cm apart. Side-on, they splayed the legs and forced a 10 cm pelvis drop and deep knees. Side-on, the bridge is now squashed to its projected width (minimum 45%, so the waistband still covers the gap under the t-shirt).
- The thigh cards are wide (2:1), so he reads stockier than the tracksuit version. That is the kit's art, not something the retarget can fix.

### YOUNG POET, child clothes (122 cm)
- **Proportions:** child props `hip 0.48, head 0.225` (big head, short legs), so `r = 0.62`. Strides and arm swing scale with him.
- **No usable hip bridge:** `young_poet.child_clothes.hipcore` was cut as one whole sheet. The bridge is virtual: the hips follow the skeleton under the torso, and the shorts on the thigh cards cover the joint.
- **Tall sneaker tab:** the tab puts the ankle brad 11.6 cm up on a 32 cm knee height. The shin card is therefore only 20.7 cm. The knee still reads, but the lower leg rotates as one piece with the sock.
- **Wrong state-card facing:** the heel-up state card `poet-child` was detected as facing left, because its toe hangs below the tab. Its facing is forced in the spec.

### WOMAN, red floral dress (poem 13)
- **Head facing:** `woman.13.heads-hands/4-head-right-profile` shows her *right* cheek, so she faces screen-left. With the facing assumed right, she walked looking at the sky. It is now `faces: -1`, and the 3/4 head likewise.
- **Bodice:** the profile bodice's two top brads are neck (top-right) and shoulder (top-left, over the armhole). The arms hang there, which reads slightly behind the bust.
- **Skirt:** the skirt panel (kit garment, waist to knee) hangs from the waist brad toward the mid-point of the knees. It is squashed to 62% in profile and widens with the leg spread. It covers the thighs, so only the shins and shoes move below it.

### EX, back views only (face never seen)
- **Turning him away:** the whole act is turned about the vertical axis so his mean heading is 150° (away from camera, a little to the right). Back cards are forced on every frame.
  - The first implementation turned him the wrong way, so he faced the camera at 31° in back cards. It now searches the rotation numerically.
- **Facing frames are counted:** frames where the source still turns toward camera are listed as a problem (ACT-024: 90 frames), but only back heads are ever drawn.
- **Bridge brads:** the bridge brad selection picked the waist brad twice on `ex.ex_jacket.hipcore/4-hip-bridge`. The bridge became a giant tilted card beside the torso. Brad selection is now waist = top-centre and hips = the outermost of the rest.
- **Seat:** the rear seat cover is drawn over the thigh tops, as the kit intends. Combined with the pocketed jean thighs, it gives a heavy seat. That is the kit's art.
- **Back shoes:** the back shoe card has no heel-toe axis. It is scaled so its ankle-brad height equals the 3D brad height, which stops it floating. Its contact is the projected 3D heel or ball kept relative to that brad.

### PARTY GUEST (poem 07 party, 178 cm)
- **Bridge:** the profile kit's pelvis connector is very wide (40 cm between the hip brads). Side-on it is squashed and hidden. Facing camera it shows as a waistband under the jacket.
- **Facing camera:** the kit is profile only. Dancing toward camera uses the front head on a profile body, with profile legs splayed.

## What still fails (honestly)

- **Planted drift on 18 of 31 clips (worst 2.34 cm/frame).** It is concentrated in 1–5 frames per clip:
  - The crouch, frames 59 and 75 in every character: the load moving heel to ball while the foot also rotates.
  - Dances and waits: the foot pivots on the spot. A rigid profile card cannot show that yaw, and it flips mirror while planted.
  - Fixing it would need a blended two-point pin (heel and ball weighted) or a pivoting-foot replacement card.
- **Lying on the floor (ACT-008, 34 frames).** The standing cards are rotated onto the floor and read as a jumble. The kit's `replacements.back_lying / side_lying / kneeling / sitting / deep_crouch` sheets are not used yet. Each clip lists its floor frames.
- **Two-person acts (ACT-002, 013, 017, 019, 023).** Only the lead actor is retargeted. The partner and the props (cup, box) are not drawn.
- **Hand shapes.** Hand shapes are not switched: relaxed or open cards only. The source grip and pinch, and the arm's contact with props, are lost because arms are FK with the target's lengths.
- **The t-shirt POET has no side view (kit gap).** Side-on he is a front torso with profile shoes and head.
- **Drawn height is 3–6% under target.** Bola's stance has bent knees and a head tilt, and the retarget keeps both. A "stand tall" option would need a source-pose correction.
- **Wide hips facing camera.** On the profile-only rigs (young_poet, woman, party_guest), facing-camera frames still use profile limbs with the hips from the squashed bridge, which reads as a slightly wide-legged stance.
- **Profile limb cards for both legs.** Profile kits ship only one (L) thigh, shin and arm. The far limb is the same card, darkened (`shade: 0.35`).
