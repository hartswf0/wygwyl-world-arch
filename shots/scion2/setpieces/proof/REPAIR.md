# Stage proof repair (v2)

This records what I changed after the blind critic's review of the v1 proof. Each critic failure gets its root cause, the fix, and whether the matching repair condition now holds. Every claim is tagged **measured** (a number from `proof/<scene>.json` under `checks.repair`, or from `proof/repair_audit.json`), **viewed** (I looked at the render), or **inferred** (a chosen constant or a rule of thumb).

The critic has **not** re-judged v2. Nothing below says what the critic thinks of it.

- **v1 files:** `proof/<scene>_v1.{jpg,json,mp4,_layers.jpg,_strip.jpg}`, plus `summary_v1.json`. The v1 code is at `repair/stage_v1.py`.
- **v2 files:** `proof/<scene>.*`, rendered by `python3 stage.py`. Each still is frame 96. Each scene is 120 frames at 24 fps, 1280x720.
- **Audit sheets:**
  - `proof/repair_compare.jpg`: v1 and v2 stills side by side.
  - `proof/repair_hard_cases.jpg`: the p01 entrance frames in v1 and v2, the p09 stand-to-sit frames, and the p07 bartender pose swaps.
  - Produced by `python3 repair/audit.py`.
- **New code:** `stage.py` (edited), `repair/border.py`, `repair/palette.py`, `repair/actors.py`, `repair/audit.py` and `repair/contact.py`. The registry and `shots/kits/` are unchanged. Every fix is a rule in the stage; no part ids are hand-picked.

## The common root cause: no camera

The critic's "largest gap" is real. v1 drew everything at one scale, as a flat toy theatre. The floor was a strip in front elevation, mirror-tiled across the frame. Because nothing had a camera:

- a nearer actor could be smaller than a farther one;
- the floor could not agree with a painted wall corner;
- a counter could not have a top surface;
- an opening could not have depth.

**v2 adds one pinhole camera (inferred constants):**
- Eye height is 150 cm, so the horizon is at y=230 (360 px above the back line at 2.4 px/cm).
- The horizontal field of view is 60 degrees, so F=1108 px and the back line is Z0=462 cm from the camera.
- Everything standing on depth line y is scaled by `persp(y) = (y-230)/360`. Real size is kept at the back line.

**What draws through that camera:**
- The floor is one card mapped onto the floor plane by a homography.
- The counter top is a plane.
- Opening reveals are wall-thickness quads that run back toward the vanishing point.
- The vanishing point is taken from a painted wall corner when the wall has one (measured). Otherwise it is the frame centre.

The checks divide every rendered size by `persp`. The scale ratios against real-world expectations stay at 0.95 to 1.01 (measured, `checks.scale`).

## p01_doorway

| # | Critic failure | Root cause | Fix | Condition now |
|---|---|---|---|---|
| 1 | A forearm floats in the doorway (f18-26) | The walk drawing `walk-the-room` throws one palm forward. It reaches 0.445 of body height ahead of the torso (measured). With the body behind the wall, only the arm showed. | **Stage rule `entrance_walk`:** entrances use the walk drawing with the least lead. That is `03-walk-profile-colonnade`, with a lead of 0.304 (measured). **New check `partial_visibility`:** a frame fails when the torso is hidden and no visible part reaches the floor. | **Holds.** 0 failing frames of 37 partly-hidden frames (measured, every 2nd frame sampled). Viewed in `repair_hard_cases.jpg`: in v2 a boot and leg step in first, then the body; in v1 at f18-20 there is an arm alone. The first version of this check flagged legs that the woman's dress split into pieces, so I relaxed it to "torso hidden and nothing grounded" (viewed). |
| 2 | The man stands on sky; the door niche is a blue cloud fill | The hall flat `07-hall-4-corridor-frame-4` has its own transparent far opening, and nothing closed it. The floor stopped at the back line, so the backdrop showed under his feet. | **Stage rule:** an opening in a flat behind the back line must close with an opaque part from the same sheet (`closes`: no openings of its own, taller than wide). This found `01.hero.severn/08-hall-door-far-door-slider`, fitted to the measured hole. The floor plane now runs back to the hall's base line (`ground(y_top=...)`). | **Holds** (viewed): a red far door fills the opening, and his boots stand on the board floor 7.7 px in front of the threshold (measured). **Trade-off** (viewed): the far door fills nearly the whole opening, so it reads more as a closed door than as a corridor. |
| 3 | The window is a frame hung on the wall; no sill or depth; the same blue fill as p09 | No wall thickness existed. The backdrop was chosen by text='night' in each poem independently, and the 01 and 09 skies are near twins (palette distance 6.6, measured). | **`Stage.reveals`:** each measured opening gets the faces of a 25 cm wall (inferred) that the camera can see: lintel, sill and the jamb away from the vanishing point, shaded from the wall's own ring colour. **`choose_backdrop`:** a backdrop must be at least 12 palette units from every fill chosen earlier in the run (inferred threshold), and no thin bands. | **Holds.** The window reveal is 26.3 px and the door reveal 9.6 px, against the 8 px minimum (measured). The fill is now `01.set.city_fall_void/black-blue-backing`, and the 01 cloud sky was rejected as too close to p09's (measured). Viewed: the jamb and lintel faces show. |
| 4 | Scale reads backwards: the nearer woman is shorter | There was one scale for all depths. | The camera: actors are scaled by `persp` of their feet line. The woman stands at d=0.7, which is `persp` 1.24. | **Holds.** The nearer actor is at least 1.144x the farther in nominal height and 1.078x in painted height, over 120 pairs of frames (measured, `depth_ladder`). |
| 5 | Sunglasses during the walk, a bare face at the wave | Nothing kept accessories consistent between beats. `07-hello` is "glasses off". | **`StageActor._resolve`:** CLIP scores the head crop for glasses (`repair/actors.py`, cached). Every beat must fall on the same side of 0.02 as the first beat. That cut-off sits in the measured gap: -0.007 for `07-hello`, at least 0.042 for every other poet drawing. A mismatch is swapped for a matching drawing in the same posture, preferring a greeting (`palms-up`), then the nearest pose. | **Holds.** The wave became `ask-the-universe-2`, glasses score 0.065 (measured). Viewed: sunglasses in every frame. **Trade-off:** it is no longer a wave; it is an open-arms greeting. My first choice, the `open-up` family, picked `welcome-new-day`, whose arms crossed the jamb (viewed), so I dropped that family. |

## p07_bar

| # | Critic failure | Root cause | Fix | Condition now |
|---|---|---|---|---|
| 6 | The floor is a tiled diamond plate: seams every 220 px, repeated red rivet lights, a flat elevation | `Stage.ground` mirror-tiled a small card (`07.hero.shaft/part-12`, 138 px interior) across the floor band. The only "floor" in poem 07 was chosen by text. | **Floor plane:** one card, no tiling, by homography. **`choose_floor`:** candidates are usable ground cards from any poem that a person can stand on. A card is rejected when it carries an outdoor or edge name, has an interior under 300 px wide, or has an autocorrelation peak above 0.6. The winner has the lowest palette distance to the bottom 30% of the wall, with a bonus for the same sheet or poem. The cage floor was rejected at 138 px wide. Chosen: `06.hero.teahouse/06-floor-stone-apron`, palette distance 7.4. | **Holds.** Floor layer: highest autocorrelation peak 0.144 (measured; shifts 20 to 640 px, high-passed). Still floor band: v1 0.429 at exactly 220 px (the tile period), v2 0.096 (measured). One card, so no repeated rivets (viewed). **Caveat:** the 0.6 cut-off would not have caught v1's tiling (0.43). The fix removes tiling itself rather than relying on the threshold. |
| 7 | No room behind the bar; the bartender is framed in the window | The counter stood at d=0.55, right against the wall. The man's x was hand-set where an opening was behind him. | **`solid_spans`:** the man stands in the widest run of solid wall at upper-body height (measured: x 753-1045). Depths come from the camera: the man is 37 cm from the wall, then a 20 cm body gap (inferred), then a 45 cm counter (inferred). That puts the counter front at Z=360 cm, d=0.815. | **Partly holds.** At most 5.1% of his visible pixels fall over an opening, against 100% framed in v1 (measured). **The 40 px floor or back-bar band does not hold.** With the eye at 150 cm and a 105 cm counter, the floor behind the counter is hidden by geometry. The registry has no back-bar piece: searches for shelf, cabinet, sideboard, dresser and rack found none usable (measured). The visible counter-top plane is 15.9 px deep (measured). |
| 8 | The right "window" is door-height; the horizons disagree | Opening detection counted the wall's uneven bottom edge as hole. The middle opening was mis-measured, and v1 filled it as a window. | **`floor_cut`:** holes are counted only above the wall's median bottom minus 2% of its height. Openings reaching that line are doors. The bar wall now measures two door-height openings and one window (sill 87.9 cm, measured). One backdrop sits behind all of them. | **Partly holds.** The openings are classified by measurement, and the counter is not centred on an opening. The wall really does have door-height openings; I did not hunt for a different wall. Horizon (viewed): one sky image is visible through all openings. |
| 9 | A white halo appears only in the gesture pose | `dance-threequarter` has a 4 px sticker halo; `main-poses` has none (measured, `actors.halo`). | **`StageActor._resolve`:** if an actor's drawings in a sheet disagree on the halo (one at 0, another at 2 px or more), near-white edge pixels within that width are stripped from all of them. | **Holds** for the halo: 4 px stripped from the man (measured), and viewed in `repair_hard_cases.jpg` row 4. **Not fixed:** a size jump in the same swap. The height guard shrinks `main-poses` (228.7 cm by markers) to 177 cm, so the dance pose looks about 1.3x bigger (viewed). See gaps. |
| 10 | Bottles stand on the front lip of an edge-on top | The front panel was the only surface. Props rested on its top edge. | **`Stage.counter_top`:** the same sheet's `countertop` card is mapped as a horizontal plane between the front's painted top edge and 45 cm behind it, toward the vanishing point. **`on_plane`:** bottles rest 20 cm back, at that depth's perspective scale. | **Holds.** The bottles sit 0.5 px from their rest line, inside the plane's x range (measured). Viewed: a top surface band shows, with the bottles set back on it. |

## p09_parlour

| # | Critic failure | Root cause | Fix | Condition now |
|---|---|---|---|---|
| 11 | Dollhouse armchair (critic measured about 160 px against a 430 px man) | I could not reproduce the 160 px. v1 rendered the chair at 228 px, which is 95 cm. The chair's registry size of 95 cm is within the real-world range, and the drawing's own seat height is 49.5 cm, which matches the sitter's 46.9 cm seat-to-feet (measured). The man swamps it because he stood 0.25 nearer to the camera than the chair, under a model with no camera. | The camera, so actor and chair compare at the same depth. I kept the chair at 95 cm: raising it to the critic's band midpoint would put the seat at about 55 cm, above the painting's leg length. | **Holds.** Chair back over standing actor is 0.518, inside 0.50-0.65 (measured, depth-normalised). Head above the back is 0.307 of actor height (limit 0.35). Hips are 0.1 px from the seat line (limit 15). Boots are 7.2 px from the chair base line (limit 40). |
| 12 | The sit is a pop cut; a boot is planted in front of the side table | There was no transition. The table was placed at a hand-picked x. | **`StageActor` tween:** 4 dissolve in-between frames. The last standing layer slides toward the seat and fades out while the seated painting fades in. No lowering drawing exists: every non-sit poet drawing has a hip ratio of 0.48 or more (measured). **Table placement:** a probe render of the seated beat measures how far right the figure reaches; the table goes 18 px clear of that. The side-table expectation was lowered to 50-62-70 cm (inferred). | **Holds** by count: 4 in-between frames, against the minimum of 3 (measured). It is a dissolve, not a drawn lowering (viewed: a double image at f57-58). The table now clears the feet (viewed), with table over actor at 0.336, inside 0.30-0.40 (measured). |
| 13 | A neon striped floor under a period room; floor and wall perspective disagree | The floor query took the first 'floor' result (a cinema lobby), and the floor had no perspective. | **`choose_floor`:** chosen `12.set.temple_backroom/01-floor-bare-board-strip-interior`, palette distance 8.2 to the wall bottom. The neon lobby floor's palette distance to this wall was 37.6 (measured). **`measure_vp`:** the wall's painted left corner is fitted with a line (57 px run, residual 0.59 px), which crosses the horizon at x=1039. The floor homography uses that same vanishing point. A fit with residual above 3 px is rejected: the bar wall's door-notched bottom gave a 118 px residual, and I first used it before adding this rule (measured). | **Holds** (measured and viewed): warm boards under the green wall, one vanishing point for the corner and the floor. Floor autocorrelation peak 0.557, below 0.6; this is board grain at 30 px (measured). |
| 14 | The window is a flat swatch with a torn or deckle inner edge | The wall cut-out's opening edge is ragged paint, and the backdrop showed right up against it. | **`clean_flat`:** each opening becomes a clean rectangle (the rows and columns that are at least 50% hole). Ragged transparent bits are inpainted from the wall; ragged paint inside is cleared. Then the reveal (fix 3) is drawn behind it. | **Holds** for the edge and the depth: the reveal is 35.8 px, and the rectangle is clean by construction (viewed). The fill is still `09.set.atlantis_club_sidewalk/01-night-sky-teal-grey`, now unique to this scene. Whether it reads as a "view" is a judgement I leave open. |
| 15 | Rope or cardboard trim at the frame edges and the wall/floor seam | Cut-outs keep the sheet's painted card border. | **`border.border_width` (measured per part):** the largest 2 px ring colour jump within 3-18 px of the outside edge. It is trimmed from flats and from rectangular cards that fill at least 90% of their box: 9 px on the p09 wall, 5-11 px elsewhere. Shaped cut-outs are not trimmed. On a floor card, the first 10% of rows are dropped (inferred share), because the p01 board floor's broken far edge showed as notches at the seam (viewed). | **Holds** (viewed). The image-gradient energy in the 15 px edge bands of the p09 still fell from 4.4x and 2.6x the frame mean (v1) to 0.38x and 0.28x (measured). The higher right-band values in p07 (1.51) and p01 (1.41) are room content, a door frame and a window frame (viewed). |

## Checks that still hold after the repair (measured)

| | p07_bar | p09_parlour | p01_doorway |
|---|---|---|---|
| Occlusion rules / violations | 10 / 0 | 9 / 0 | 10 / 0 |
| Wrong-order tests caught | 5 of 5 | 2 of 2 | 2 of 2 |
| Worst contact error | 2.1 px | 1.0 px | 2.0 px (the hall flat stands 11.5 px off its line behind the wall, by design) |
| Actor feet off their line (max) | 0.75 px | 0.91 px | 1.0 px |
| Swap jumps | 0 cm | 22 cm into the sit (as v1, now dissolved) | 0 cm |

## Rule changes after viewing my own renders

These are separate from the critic's list. Each came from looking at a render.

1. **Door openings were inpainted grey.** Viewed: the first `clean_flat` run filled the bar wall's middle door with grey. Root cause: the wall's uneven bottom joined the door hole, so the row test failed. Fixed by `floor_cut`.
2. **A false vanishing point.** Measured: residual 118 px, VP at x=1195 on the bar wall. Fits with residual above 3 px are now rejected.
3. **A gap under the counter top.** Viewed: the counter-top plane started at the affordance's `surface_y`, leaving a gap where the bartender's cuffs showed. It now starts at the front's measured painted top edge.
4. **The counter fell off the frame.** Measured: the first depth plan put the counter at d=1.07, beyond the front edge. Changed to man d=0.25, gap 20 cm, depth 45 cm. The counter is also shifted to stay inside the frame.
5. **Glasses test too strict.** Measured: a tolerance of 0.035 between beats swapped `arrive-01`, which has glasses. It is now a binary cut-off at 0.02.
6. **Floor card far edge.** Viewed: the board floor's ragged far edge showed at the p01 seam, so the first 10% of rows are dropped.
7. **Floating-limb check.** Viewed: legs split by a nearer actor's dress were counted as floating, so the check was relaxed as described in fix 1.

## Gaps (not fixed, or only by an inferred rule)

- **No back-bar.** The 40 px floor or back-bar band behind the counter is not met. The geometry hides the floor, and the registry has no back-bar piece.
- **Bartender size jump.** The height guard rescales `main-poses` from 229 to 177 cm, but `dance-threequarter` is drawn at its marker scale. Their head-to-chin markers (15.5 and 15.0 cm before the guard) suggest the guard may be wrong for this drawing. Head markers are too inconsistent across the library to use as the reference (measured).
- **The sit in-betweens are a dissolve.** The library has no lowering drawing.
- **The wave is now an open-arms greeting.** The only waving drawing has the glasses off.
- **Inferred constants.** The camera (eye 150 cm, 60 degree field), wall thickness 25 cm, counter depth 45 cm, the actor body gap of 20 cm, the reveal shading and the contact shadows are all inferred. The reveals and shadows are generated, not taken from the sheets.
- **Floor cards are textures stretched onto the plane.** One card is stretched non-uniformly; there is no real-size tiling.
- **Sampling.** The occlusion and visibility checks ran on every 2nd frame plus the still, not on every frame. The floor periodicity metric is a high-passed autocorrelation peak, my reading of the critic's test.
- **One run, fixed order.** Backdrop uniqueness is enforced within one `run()` (bar, then parlour, then hall). Rendering one scene alone (`python3 stage.py hall`) has no earlier fills to avoid and can pick a different sky.
- **Scope.** The recipes are still written by hand for these three poems.
