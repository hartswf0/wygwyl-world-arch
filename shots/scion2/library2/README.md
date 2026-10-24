# library2: the regularized parts library

Each card in `shots/skinlab/library.json` is checked here before any assembler uses it. A card is cleaned so that it
holds exactly one part, then classified and given a sub-skeleton with its connection pivot. Last, it is re-rendered
onto a fixed grid with **rotation and uniform scale only**. Nothing is warped or repainted. An assembler can then
attach a part at its pivot, rotate it about a known axis, and trust its view and facing.

Build order: POET (all costumes), then EX, then the others by screen time (`../cast_plan.json`).
Status:
- **Card by card (reviewed):** the POET (both costumes) and the EX. Every slot is done: head, torso, pelvis,
  upper_arm, forearm, hand, thigh, shin and foot.
- **Head builder:** composed heads (`tools/headbuilder.py`).
- **Automatic only:** the next characters by screen time (party_guest, poet_soul, brother_1, friend_1, friend_2,
  vintage_man, vintage_woman, mother). They are flagged `auto_only`: nobody has looked at their keypoints card by
  card.
- **QA gate:** `qa/` (README there) is the gate an assembler must respect.
- **Proportion canon:** `canon.json`, per character/costume, from the Pose Lab markers on the painted figures.
  Each part carries `canon_deviation` in index.json.

## Layout
- `index.json`: one record per source card per part type (`parts[key]`, with key = `<char>/<part>/<card-slug>`).
- `<char>/<part>/<card-slug>.png`: the canonical RGBA image.
- `sheets/<char>_<part>_NN.jpg`: review sheets. `sheets/<char>_<part>_rejected_NN.jpg`: cards that were rejected
  or re-filed, each with its reason.
- `fixes.json`: manual corrections keyed by source card id. Fields: `part` (re-file), `reject`, `view`, `facing`,
  `state`, `rot`, `scale`, keypoints in CARD pixels, and `flags`. These fields override the automatic values and
  are marked `source: fixes.json` in the index.
- `tools/`: the code.
  - `common.py` holds the grid, cleaning, transforms and sheets.
  - `brass.py` detects the brads.
  - `index.py` writes the records.
  - The per-part builders are `heads.py`, `hands.py`, `feet.py` and `segments.py` (torso, pelvis and limbs).
  - The other tools are `headbuilder.py`, `canon.py`, `cliptext.py` (CLIP zero-shot on the cached embeddings) and
    `build_all.py <chars...>`.
  - To rebuild a character, run `python3 shots/scion2/library2/tools/build_all.py poet`, then `canon.py`.
- `canon.json`: proportion canon (segment lengths and joint widths in cm, with median and IQR) per
  character/costume.
- `qa/`: gates, `seam.py` (the joint fitness), `pairs.py` (pairwise joint sweeps) and `pairs.json` (the
  compatibility matrix).

## Defringe
Every canonical image is defringed: each semi-transparent edge pixel takes the colour of the nearest solid pixel,
so the light card-background fringe cannot show as a white halo over a dark partner. Alpha and solid pixels are
unchanged (`defringed: true` in index.json).

## Native sets
`source_set` in index.json gives the source sheet, the costume, his left/right (`side_in_set`) and `sheet_mates`,
the other parts cut on the same sheet, grouped by part type. The kit's tabs were sized for their sheet-mates, so
these are the native pairs.

## The grid
- The scale is `CANON_PPC` = **10 px per cm** for every character and every part. A head 24 cm tall is 240 px.
- Card to canonical: `canonical = M · [x, y, 1]`, where `M = transform.matrix_card_to_canonical` (2×3). `M` is a
  similarity: `rotation_deg_ccw` is counter-clockwise on screen, and `scale` is uniform.

| part | canvas | pivot on canvas | primary axis (pivot→tip) on canvas |
|---|---|---|---|
| head | 512×512 | neck (256,448) | neck→crown points **up** |
| hand | 384×384 | wrist (192,72) | wrist→knuckles points **down** |
| foot | 768×512 | ankle (384,112) | sole horizontal, sole down; toe direction = facing |
| upper_arm / forearm | 256×512 | shoulder / elbow (128,64) | points down |
| thigh / shin | 320×640 | hip / knee (160,80) | points down |
| torso | 768×768 | waist (384,640) | waist→neck points up |
| pelvis | 640×512 | waist (320,128) | waist→hip-mid points down |

Grid lines on the sheets are every 5 cm (50 px). They are aligned to the pivot, which is drawn as a red cross.

## Classification fields (each `{value, conf, source}`)
- `view`: front, three-quarter, side, three-quarter-back, back (feet and hands also: top).
- `facing`: screen-left or screen-right is the way the nose or toe points on screen; `camera` / `away` for front
  and back.
- `side`: for limbs, his left or right.
- `state`
  - heads: painted_face, blank_face_plate (hair, beard and ears painted, no eyes or mouth), partial_face_plate,
    back_of_head, bare_backing_plate.
  - hands: open, fist, grip, pinch, point, cupped, palm-up, palm-down, holding-X.
  - feet: boot, shoe, sneaker, sole_visible.
- The sources are, in order of trust:
  1. `fixes.json` (this agent looked at the card);
  2. `labels.json` (agent-vision);
  3. the library view (filed from the sheet caption);
  4. pixel tests;
  5. CLIP.
- `pixel_tests` keeps the raw numbers.

## Flags
- `cleaned`: components or regions were cut away (`removed_components` lists each with its bbox).
- `caption_removed`: printed caption text was cut off.
- `painted` / `blank` / `back`: the face state.
- `low_res`: the card's long side is under 180 px.
- `chin_estimated_from_ear_line`: back views, where the chin cannot be seen. It is placed at crown + (ear-line − crown)/0.54.
- `chin_estimated_from_outline`: back views without a hand-set chin. The chin is taken where the neck widens; on
  such a sheet the heads share the median scale.
- `auto_only`: a character that was not looked at card by card.
- `composed`: a head-builder composite. `no_nose_card` means the kit has no nose card.
- `prop`: a hand holding a painted prop. `pale_skin_off_palette` / `off_palette_white`: another costume or palette.
- `low_res`: the card's long side is under 180 px. `no_wrist_brad` / `no_ankle_brad` / `*_pivot_estimated`: the
  pivot is not on a detected brad.
- `name_says_right_image_is_left`, `name_palm_back_unreliable`: the card's name contradicts the image; the image
  wins.
- `neck_cut_short`, `pale_skin_off_palette`, `filed_threequarter_drawn_as_profile`, `backing_plate`,
  `other_costume_*`.

## Other sub-skeletons (keypoints in `keypoints.canonical` / `keypoints.card`)
- **hand:**
  - `pivot`: the wrist brad;
  - `palm_centre`;
  - `knuckle_l`, `knuckle_r` (the knuckle line);
  - `tip_0..4`: fingertips, ordered by x;
  - `thumb_tip`: the tip at the largest angle from the axis, when over 35°.
  - Classes:
    - `palm_normal` (palm / back facing the camera);
    - `side` (his left/right; from the name or by eye, else derived from the thumb side and palm_normal);
    - `state`;
    - `grip_for` (the prop the grip was painted for, when the prop is not on the card).
- **foot:**
  - `pivot`: the ankle brad;
  - `toe`, `heel`;
  - `sole_heel`, `sole_toe`: the sole line.
  - The facing is the screen direction of the toe.
- **torso:**
  - `pivot`: the waist brad;
  - `neck`: the neck brad, or the top of the collar;
  - `shoulder_l`, `shoulder_r`: screen-left/right sockets (or `shoulder` for a side view);
  - widths at the waist, mid and neck, plus the shoulder span.
- **pelvis:**
  - `pivot`: the waist;
  - `hip_l`, `hip_r`, `hip_mid`;
  - `brads_in_a_row` flags waist strips.
- **limbs:**
  - `pivot`: the proximal joint (shoulder, elbow, hip or knee);
  - the distal joint, named in GRID `tip_name`;
  - `widths_px` at both ends and mid;
  - `extra_brads_mid_segment` flags two segments on one card.
- **Scales:**
  - Hands and feet use one scale per cut sheet, the median library px_per_cm. The library's px_per_cm is a
    per-card fit of A–B to a fixed length, so using it card by card would stretch fists to the length of open
    hands.
  - Torso and limbs use the kit's median brad-to-brad length for that character.
  - Heads use crown→chin = height/8.

## Head builder (`tools/headbuilder.py`)
1. Blank front and profile plates are combined with feature cards (eyes, brows, mouths). The layout comes from
   each plate's keypoints:
   - the eye pair sits on the eye line;
   - the brows sit at eye − 0.085·H;
   - the lips sit at eye + 0.55·(chin − eye).
2. Plate widths are fractions of H, measured where a head and its features were cut on the same sheet.
3. The feature pixels are only scaled and placed. Each feature card is trimmed to its painted feature with a
   feathered alpha edge, so the plate outline does not show, and its brass eyelets are cut out. Only alpha changes.
   The profile composites are rougher than the front ones (patches near the eye).
4. The records are part `head`, with:
   - the flag `composed`;
   - `classes.expression`;
   - `composed_from` (the plate and the feature card ids).
5. They share the plate's pivot and transform.
6. Sheets: `sheets/<char>_head_composed_NN.jpg`.

## Head sub-skeleton (keypoints, canonical and card px)
- `pivot`: the neck connection. This is the brass eyelet or brad on the neck tab (found by the colour and
  roundness detector in `tools/brass.py`); otherwise the library A point.
- `crown`: the top of the hair.
- `chin`: the bottom of the chin or beard. On a side view it is the front of the chin.
- `eye_line`: the centre of the eye line. On profiles it is at the eye.
- `ear_l` / `ear_r`: the outer edge of the screen-left / screen-right ear, on front and back views.
- `ear`: the visible ear, on profile and three-quarter views.
- `nose`: the nose tip on profiles.
- `face_dir`: `yaw_deg` (0 front, ±45 three-quarter, ±90 profile, ±135 three-quarter back, 180 back; + = towards
  screen-right). `vec3` = (x screen-right, y down, z toward camera).
- `widths_px`: the neck width at the pivot, the minimum neck width, and the chin-row width. A torso's neck opening
  should match these.

Head scale: crown→chin = character height / 8 (the Vitruvian canon of the contract; 23.3 cm for the poet at
186 cm). Heads cut from the same sheet
share one scale, the median of the members whose chin is measurable. This keeps the painter's relative sizes, and it
covers back views, whose chin is hidden. `transform.scale_source` says which rule was used.

## How an assembler uses a part
1. Pick by `character`, `part`, `classes.view/facing/state`, and `status == "ok"`. Skip flags you cannot accept.
2. Load `image`. Its pivot is at `GRID[part].pivot` on the canvas.
3. Put the canvas pivot on the neighbour's matching pivot (e.g. the torso's `neck`).
4. Rotate about the pivot by the bone angle measured from the primary axis, and scale by `target_ppc / 10`.
