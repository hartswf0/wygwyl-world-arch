# library2: the regularized parts library

Each card in `shots/skinlab/library.json` is checked here before any assembler uses it. A card is cleaned so that it
holds exactly one part, then classified and given a sub-skeleton with its connection pivot. Last, it is re-rendered
onto a fixed grid with **rotation and uniform scale only**. Nothing is warped or repainted. An assembler can then
attach a part at its pivot, rotate it about a known axis, and trust its view and facing.

Build order: POET (all costumes), then EX, then the others by screen time (`../cast_plan.json`).
Status: poet heads are done. Hands, feet, limbs/torso/pelvis, the head builder and the QA stage (`qa/`) are in progress.

## Layout
- `index.json`: one record per source card per part type (`parts[key]`, with key = `<char>/<part>/<card-slug>`).
- `<char>/<part>/<card-slug>.png`: the canonical RGBA image.
- `sheets/<char>_<part>_NN.jpg`: review sheets. `sheets/<char>_<part>_rejected_NN.jpg`: cards that were rejected
  or re-filed, each with its reason.
- `fixes.json`: manual corrections keyed by source card id. Fields: `part` (re-file), `reject`, `view`, `facing`,
  `state`, `rot`, `scale`, keypoints in CARD pixels, and `flags`. These fields override the automatic values and
  are marked `source: fixes.json` in the index.
- `tools/`: the code (`common.py`, `brass.py`, `index.py`, `heads.py`, ...). Run
  `python3 shots/scion2/library2/tools/heads.py poet`.

## The grid
- The scale is `CANON_PPC` = **10 px per cm** for every character and every part. A head 24 cm tall is 240 px.
- Card to canonical: `canonical = M · [x, y, 1]`, where `M = transform.matrix_card_to_canonical` (2×3). `M` is a
  similarity: `rotation_deg_ccw` is counter-clockwise on screen, and `scale` is uniform.

| part | canvas | pivot on canvas | primary axis (pivot→tip) on canvas |
|---|---|---|---|
| head | 512×512 | neck (256,448) | neck→crown points **up** |
| hand | 384×384 | wrist (192,72) | wrist→knuckles points **down** |
| foot | 512×384 | ankle (256,96) | sole horizontal, sole down; toe direction = facing |
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
- `neck_cut_short`, `pale_skin_off_palette`, `filed_threequarter_drawn_as_profile`, `backing_plate`,
  `other_costume_*`.

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

Head scale: crown→chin = character height / 7.75 (24 cm for the poet at 186 cm). Heads cut from the same sheet
share one scale, the median of the members whose chin is measurable. This keeps the painter's relative sizes, and it
covers back views, whose chin is hidden. `transform.scale_source` says which rule was used.

## How an assembler uses a part
1. Pick by `character`, `part`, `classes.view/facing/state`, and `status == "ok"`. Skip flags you cannot accept.
2. Load `image`. Its pivot is at `GRID[part].pivot` on the canvas.
3. Put the canvas pivot on the neighbour's matching pivot (e.g. the torso's `neck`).
4. Rotate about the pivot by the bone angle measured from the primary axis, and scale by `target_ppc / 10`.
