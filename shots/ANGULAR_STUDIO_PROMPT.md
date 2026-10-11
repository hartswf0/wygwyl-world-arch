# MULTIPLANE ANIMATION STUDIO — WYGWYL WORLD ARCH EDITION
## Angular drawing first. Data joins second. Revised 10 Oct 2026.

This prompt is for a drawing agent. Its centre of gravity is **how every frame is drawn**: what a shape is,
where its edges go, how light moves through colour, how a body is built from a few planes, and how those
planes stay attached to the thing they describe while it moves. Repository data (Part E) tells you *what* to
draw and *when*; Parts A–D tell you *how it must look and behave*.

The reference drawing is `shots/out/bdc7d6ec-1d4e-4f99-ad7e-9917394c542a_2/program/frame0.png`
(Cortex Commons: children running left under a satellite dish). Open it before drawing anything. Everything
below is a description of what that picture already does.

---

## PART A — WHAT THE PICTURE IS MADE OF

### A1. The primitive is a lit surface, not a line
A drawing is a stack of **filled regions**. Each region is one of five things:
1. a **silhouette** (the outer mass of a body/object/landform),
2. a **lit plane** (the part facing the light),
3. a **shadow plane** (turned away, or in cast shadow),
4. a **reflected/bounced patch** (light returning from the ground, a coloured projection, water),
5. an **atmosphere field** (sky, haze, a light pool: wide, smooth, gradient-filled).

If a region is none of these, delete it. No region exists "for texture" or "for detail".

### A2. Edges are designed, not generated
- Edges are **straight segments joined at decisive angles**. A contour is typically 6–30 vertices for a whole
  figure, not hundreds. Think cut paper / chisel facets, not a traced photo.
- **Vary segment length on purpose.** A long quiet edge (a wall, a dish rim, a thigh) sits next to a short
  busy run (a hand, hair, foliage, rubble). The contrast between quiet and busy edges is the style.
- Corners are **clipped** (a cut across a corner) rather than rounded. A rounded form is expressed by
  gradient *inside* the region, not by a curved boundary.
- Add **notches and spurs** (small bites and thin projections) where something is torn, loose, or in
  motion: coat hem, fingers, toes, grass line, debris. Not everywhere.
- Silhouette angularity scales with distance: **near = more vertices and sharper notches; far = fewer,
  longer, quieter edges that nearly merge with atmosphere.**
- **No outline strokes around characters.** Separation comes from adjacent colour/value only. A thin dark
  rim may sit *inside* a silhouette edge where a lit body passes in front of a dark mass (a figure's lit
  shoulder against the dish). Structural strokes are reserved for things that must read as lines: stair
  edges, rails, wires, antenna spars.
- No pencil grain, hatching, noise, film grain, bevel, gloss, drop shadow filters, or blur on shape edges.

### A3. Colour is organised by light, then by object
Before drawing, write down for the shot: **key light** (colour, direction), **ambient field** (colour of the
shadows and sky), **darkest connected mass**, **brightest region**, and **any coloured projection**.

- Every object's local colour is **bent toward the light it sits in.** In the Cortex frame: cool blue-grey
  environment, warm terracotta/ochre figures, one magenta/violet projected pool on the ground.
- A body is **2–5 values of one hue family** (e.g. terracotta: base, lit, deep shadow, rim). Not a rainbow of
  facets. A second hue appears only for *reflected light* or *a projection*.
- **Gradients live inside regions** and describe form or atmosphere: head dark at crown → lighter at face;
  sky dark at top → pale at horizon; torso warm at lit side → deep at shadow side. Boundaries stay hard.
- **Atmospheric perspective:** with distance, saturation drops, value contrast shrinks, hues drift to the
  ambient field colour. The farthest plane should almost be the sky colour.
- **Strongest contrast goes where the story is.** Lightest light against darkest dark at the performer's
  head/hands/feet. Everything else compresses toward mid-values.
- Cast shadows and light pools are **single large shapes** that cross the ground and bodies coherently.
  They are not scattered per-polygon.

### A4. Hierarchy of attention (what gets detail)
Rank every area: **1 hero contact/gesture → 2 hero silhouette → 3 secondary figures → 4 key set pieces
(the dish) → 5 mid-ground → 6 far ground and sky.** Spend vertices and internal regions in that order.
Rank 6 is nearly flat. A region is allowed to be quiet; the viewer's eye needs somewhere to rest.

### A5. Selective edge loss
Where information is not needed, let edges disappear: a shadowed arm merges into the torso, a far runner
dissolves into haze, two dark masses fuse into one. Restore a separating sliver **only** where the action
needs it (a planted heel, a reaching hand, the head turning).

---

## PART B — BUILDING A FIGURE FROM PLANES

### B1. Construct under, finish over
Underneath: line of action; head / ribcage / pelvis masses; the supporting leg; where weight points.
On top (what the viewer sees): one **silhouette**, then **2–5 internal planes**:

| Plane | Purpose | Typical shape |
|---|---|---|
| Hair/head cap | gives head direction | a clipped cap, darker than the face |
| Face | only facing/turn, almost never features | one value, one notch for nose/brow if needed |
| Torso lit side | shows light direction | a long wedge down the lit flank |
| Torso shadow | shows turn/twist | a darker wedge, often continuous with the arm |
| Limb undersides | separate limbs from torso | narrow dark wedge on the lower edge |
| Joint notches | knees, elbows, ankles | small dark bites, 1–3 per limb |
| Cloth | dress/coat hem | long angular flap with 1–2 spurs |
| Hands/feet | contact and direction | blocklike, 3–6 vertices |

The 12-vertex head, wedge torso, and notched knee in the reference are the target level of description.

### B2. Weight and silhouette
The silhouette alone must tell the action. Squint test: fill it black; can you still see *run vs walk vs
stop*? Keep **negative space** between the limbs that matter; avoid tangents where an arm edge kisses the
torso edge. Planted foot flat on a ground-attached shape; trailing parts (cloth, hand) lag.

### B3. Facial economy
Faces are head angle plus at most one cut (nose/brow plane) or one shadow region. Expression is carried by
head tilt, shoulder line, and weight. No eyes/mouth unless the shot is close enough to need them.

### B4. Set pieces and environment
A large object (dish, building) is **one dark mass** with 1–3 lit planes and a clipped, notched rim; its
support structure can be a separate, lighter, less detailed mass. Foliage: one dark canopy + 1–2 lighter
clusters, broken edge. Ground: **large faceted fields** separated by value, with the light pool as one
bold shape; avoid fine floor tessellation, since it competes with the performers.

### B5. Repetition is an error
Do not tile the same facet size across unrelated surfaces. Do not give every shape the same edge
character. If two adjacent regions have equal size, equal angle and equal value, merge or redesign one.

---

## PART C — THE DRAWING THROUGH TIME

### C1. Region identity is the continuity rule
Every internal region is **owned**: by a body part, garment, object, light field, or cast shadow. Give it a
persistent ID (`runner2.torso_shadow`, `dish.lit_rim`, `ground.projection`). Across drawings:
- **Resting regions keep their shape.** Re-draw a boundary only because of pose, perspective, occlusion,
  or illumination change.
- Regions **move with their owner** (a sleeve shadow turns with the sleeve).
- A region may **split, merge, appear or vanish** only when a body turn/occlusion causes it, and this is
  a deliberate new drawing, not an interpolation artifact.
- Forbidden: contours that crawl, patches that migrate across a body, limbs that flicker out, per-frame
  random vertex jitter.

### C2. Key, breakdown, in-between
- **Keys** change *intention or support* (contact, compression, push-off, flight, opposite contact,
  recovery). They must read distinctly as silhouettes.
- **Breakdowns** show *how* the body travels: which mass leads, which lags, the path of hips and head.
  Hips rise while toes stay loaded; cloth hangs behind. Not the midpoint.
- **In-betweens** are the only drawings allowed to be (assisted) interpolation, and only between
  drawings whose regions correspond 1:1. Where a turn changes visible anatomy, **draw a new key.**
- Draw on **twos** (one drawing, two frames) at 24 fps as the default; ones for impact and fast contact;
  holds for decisions. Choose per-element; the camera and the light run on their own tracks.

### C3. Light changes are drawing events
A change of light (entering the orange stairwell; the projection pool crossing a runner) is **one coherent
colour shift across body + ground + wall together**, driven by a large mask crossing the scene. Not
per-polygon flicker. Warm light adds a bright rim plane on the lit side of each body and re-bends their
shadow colours.

### C4. Camera is separate from performance
Multiplane camera moves layers by parallax; performers get their own contact poses and travel. Actors
keep moving through camera holds. Never use camera movement to hide an unanimated performer.

### C5. Replace, don't layer, moving figures
If a figure becomes animated, **delete its static depiction** from the background and **paint behind it**
(the newly exposed ground/wall) in the same angular language. Keep its contact shadow and reflection with
the new drawing.

---

## PART D — CHECKS (run them on pictures, not on JSON)

For the first frame, each key extreme, mid-shot, and last frame:
1. **Silhouette squint:** blacken everything; is the action, and each performer, readable?
2. **Value squint:** blur heavily; does the focal point still hold the highest contrast?
3. **Edge audit:** vary long/short? clipped corners? any accidental outline, hatching, or noise?
4. **Colour audit:** one key light; bodies 2–5 values per hue; projection isolated; far = atmosphere.
5. **Region audit:** IDs stable, no crawling, no swapped ownership, no static duplicates.
6. **Contact audit:** feet attached while planted, hands attached while holding, continuous travel.
7. **Occlusion/paint-behind** at first, middle, last camera positions; no holes.
8. **Playback:** watch the whole shot at its frame rate. A passing still is not a passing film.

Repair order: **silhouette → ownership → light → edge character → detail**. If a later edit is worse,
restore the best checkpoint. Do not chase a numeric score by adding detail; the diagnostics
(`dE`, SSIM, CLIP, prompt rank) measure resemblance to the photo, not quality of the cartoon.

---

## PART E — DATA, BRIEFLY (what to read, what it's good for)

Repository `hartswf0/wygwyl-world-arch`; resolve and record a commit SHA. Join by **full shot ID**
(`<job_uuid>_<variant>`), never by alias. Paths relative to the repo; `<sid>` = `shots/out/<sid>`.

| Question | Read |
|---|---|
| What is visibly there? Camera/size/district | source PNG, `<sid>/shot.json` (estimates are estimates) |
| The existing angular drawing | `<sid>/program/frame0.png`, `scene.json` **together with** `cartoon.html` (gradients + structural lines are only in the HTML), `compare.jpg` |
| Depth sheets, roles, parallax, camera | `<sid>/multiplane/multiplane.json`, `planes.npz`, `arrays.npz` |
| Authored intent, keys, exposures | `shots/director_notes.json[<sid>]` |
| Visual problems already judged | `shots/judge_notes.json`, `<sid>/program/perceive.json`, `<sid>/cartoon/signals.json` |
| Timing of the existing film | `<sid>/film/xsheet.json` (120 f @ 24 fps for Cortex) |
| Sequence order/overlaps | `shots/film/reels.js`, `poems.json`, `riverbed_*.json` |

Rules that prevent the usual mistakes:
- **Role ≠ sheet ≠ region ≠ performer.** P0–P6 are semantic roles; `multiplane.sheets` are individually
  placed, ordered far→near (Cortex has 19); `scene.json` shape IDs are colour regions (87), not actors;
  performers are what you identify by inspection. `planes.npz.L` holds role numbers, not sheet indices.
- **Preserve compound paths, holes, and beyond-frame geometry** when importing vectors (negative
  coordinates are paint-behind/overscan). Verify the import against `frame0.png`.
- **Declare units.** `camera.amplitude`: truck/tilt = source pixels; push = scale fraction. Program JSON
  normalises truck by W (50.96 px / 1456 = 0.035). Source image coords: x right, y down.
  Camera direction and artwork displacement are opposite: say both.
- **One clock per output.** Analysis runtime ≠ duration. Program preview (96 f) ≠ film x-sheet (120 f) ≠
  reel placement ≠ poem source window. `duration_frames = 0` means "no authored exposures", not "0 frames".
- **High-res `S*.png` sheets are absent at the inspected revision**; low-res WebP in `shots/world/` are
  present. Preview from those; redraw/reconstruct for finals. Check for missing files before assuming.
- **What performs depends on the scene**: people → run/walk drawings; water → reflection/ripple regions;
  an empty room → light and camera; an authored absent subject (Cenotaph child) → draw it as new work.
  Source action wins over generic motion suggestions (Cortex runs; the auto-suggestion says walk).
- **Tag provenance:** `observed` · `estimated` · `authored_existing` · `proposed` · `rendered_verified`.
  Only call something `rendered_verified` after inspecting the actual output.

---

## PART F — OUTPUT

First return: resolved shot identity, one-paragraph source readback (what is *drawn*: silhouettes, light,
palette), selected clock, one-sentence dramatic action. Then: registration → performer separation →
**key drawings (silhouette first)** → breakdowns → exposure sheet → depth-aware compositing → camera →
playback → corrections. Report only files actually produced, with stage and completion status.

### Assignment
```
REPOSITORY:       {{hartswf0/wygwyl-world-arch}}
REVISION:         {{COMMIT_OR_CURRENT_HEAD}}
SHOT / SEQUENCE:  {{FULL_SHOT_ID_OR_MANIFEST_QUALIFIED_SELECTION}}
MODE:             {{animate_existing | extend_existing | new_shot_in_district | conform_sequence}}
DIRECTION:        {{USER_DIRECTION_OR_SOURCE_GROUNDED_PROPOSAL}}
TIMING SOURCE:    {{XSHEET | REEL | CUT | NEW_DURATION}}
DELIVERABLE:      {{STAGE_REQUESTED}}
```

### Worked case — Cortex Commons (`bdc7d6ec-1d4e-4f99-ad7e-9917394c542a_2`, 1456×816, district commons)
Drawn content (observed): cool blue sky and distant land; one huge dark satellite dish on a lighter
support, upper right; six–seven running children left of centre in terracotta/ochre/maroon with a lit rim
on their lit flank; a single magenta-violet projection pool on a mauve ground; foreground rubble as dark
long-edged masses. Preserve the low viewpoint and the dish as a fixed object (not a vehicle).
Camera (proposed): truck right, 50.96 source px × sheet parallax, artwork displaces left; frames 0–11
establish, 12–107 traverse, 108–119 settle, of 120 at 24 fps. Test one runner's contact → compression →
push-off → flight → opposite contact → recovery before animating the group. Replace the static runners
you animate and paint behind them. The projection pool is a light event: move/shift it as one mask.
