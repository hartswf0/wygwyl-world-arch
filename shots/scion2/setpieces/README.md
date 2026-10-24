# WYGWYL set-piece registry (MERGE of four swarms)

`registry.json` has one record for each of the 2,227 parts on the 162 sheets whose id contains `.props.`, `.set.`, `.hero.` or `.fx.`. That is 2,075 cards plus the 152 catalogued `kind: ref` reference panels, which are kept and marked unusable. It merges:

| swarm | file | owns |
|---|---|---|
| hygiene | `hygiene.json` | grade, defects, duplicate_of, pixel cleanliness (measured and viewed) |
| semantics | `semantics.json` | name, category, scene (CLIP, label lexicon and kNN fusion; inferred) |
| space | `space.json` | plane, contact, view, tile, size_cm, scale_src (alpha measurements plus rules) |
| affordance | `affordance.json` | seat, surface, grip, aperture, lean, occluder and stand_on geometry in part pixels |

The merge code is in `merge/`, run in this order:
1. `tanstrip.py` measures tan heading strips.
2. `merge.py` writes `registry.json` and `conflicts.json`.
3. `letters.py` measures lettering and label boxes. It reads the registry, so run `merge.py` again afterwards.
4. `atlas.py` renders `atlas/*.jpg`.

All four steps take less than a minute on 1 core. No CLIP is re-run; everything is read from the swarm outputs. Nothing under `shots/kits/` is touched.

## Record fields

| field | meaning | decided by |
|---|---|---|
| `id`, `file`, `sheet`, `poems`, `label`, `kind` | from `shots/kits/cut/catalog.json`; `file` is relative to the repo root | catalog (measured) |
| `scene` | staged locations (`shots/stage/sets/*.json`) that use the part. The catalog's own scene is null for every set piece. | semantics |
| `name` | readable name. It is `"<category> (<sheet title>)"` when no label could be read (see `provenance.name.src`). | semantics; merge C4b |
| `category` | backdrop, ground, architecture, aperture, furniture-seat, furniture-surface, vehicle, handheld-prop, wearable, plant-nature, light-fx, text-graphic, character-fragment, other, reference-panel | semantics; merge rules C1–C5, P1 |
| `usable` | true only if no swarm or merge rule says "do not place" | AND of the swarms, then merge overturns (U2o, U4o, H1) |
| `unusable_reasons` | `[{by, rule, reason}]` | |
| `grade` | A clean, B usable with care, C do not place. Unusable parts are always C; `grade_hygiene` keeps the hygiene grade. | hygiene |
| `defects` | hygiene defects `{kind, severity, basis, evidence}`. `fix` holds hygiene's repair hints (for example "erode alpha 2px"). | hygiene |
| `duplicate_of` | id of the best copy when this part is a same-sheet variant or a cross-sheet copy | hygiene |
| `plane` | far_backdrop, mid_set, ground_plane, near_set, foreground_occluder or overlay_fx | space; merge P1–P3 |
| `contact` | `{type: stands, rests, lies_flat, inset, hangs, floats, full-frame, overlay, worn or attached, y_px, x0_px, x1_px, ...}` in part pixels | space |
| `view`, `view_conf` | front, 3/4, side, top, perspective, scene or flat. Mostly low confidence. | space |
| `tile` | `{left, right, repeat, seam, ...}`. `repeat` means it can be laid side by side. | space |
| `size_cm`, `scale_src`, `px` | world size `{h, w}` and where it came from (label_cm, registry, prior, sheet_median, frame or none) | space |
| `affordances` | `[{kind, confidence, geometry}]`, with geometry in the part's own webp pixels (x right, y down) | affordance; merge F3 caps |
| `affordances_dropped` | affordances removed because the part is unusable or the label is wrong (C4b) | |
| `flags` | size_doubt, label_doubt, plane_doubt, contact_doubt, affordance_doubt, hygiene_overturned | merge |
| `rank` | ordering score (inferred): grade, best copy, semantics confidence, fewer flags, has size | merge |
| `merge_rules` | ids of every merge rule that fired on this part (see `rules` in registry.json) | |
| `provenance` | per field: which swarm decided it, the basis (measured, viewed or inferred) and its evidence (label class, CLIP class, kNN vote, hygiene metrics, space rules trail, affordance evidence) | |

`conflicts.json` lists 475 cross-swarm disagreements as `{id, kind, a, b, resolution, rule, basis}`:

| kind | count |
|---|---|
| size (space's own size against the sheet scale) | 148 |
| usable | 97 |
| plane | 86 |
| size_vs_category | 62 |
| registry_q (semantics echoed the old registry C, hygiene re-measured) | 38 |
| category | 35 |
| affordance_vs_category | 9 |

## Counts (measured over all 2,227 parts, after the merge rules)

- **Usable:** 1,973, of which 1,684 are A and 289 are B. 1,689 of them are the best copy of their duplicate group.
- **Unusable:** 254: the 152 refs plus 102 cards.
- **Usable by category:**

| category | usable |
|---|---|
| architecture | 364 |
| light-fx | 310 |
| other | 226 |
| ground | 212 |
| aperture | 197 |
| handheld-prop | 190 |
| plant-nature | 146 |
| backdrop | 136 |
| vehicle | 60 |
| furniture-seat | 43 |
| wearable | 41 |
| text-graphic | 39 |
| furniture-surface | 9 |

- **Usable by plane:**

| plane | usable |
|---|---|
| mid_set | 674 |
| near_set | 624 |
| overlay_fx | 300 |
| ground_plane | 223 |
| far_backdrop | 140 |
| foreground_occluder | 12 |

- **Unusable reasons** (a part can have several):

| rule | parts |
|---|---|
| U1 hygiene/ref | 208 |
| U2 semantics skip | 41 |
| U3 character-fragment | 38 |
| U10 lettering | 22 |
| U9 tan heading strip | 7 |
| U8 unnamed lettering | 6 |
| U7 reference wording | 4 |
| U4 space | 2 |
| U11 captioned reference image | 2 |

- **Affordances on usable parts:**

| affordance | parts |
|---|---|
| lean | 112 |
| occluder | 104 |
| grip | 85 |
| stand_on | 80 |
| aperture | 73 |
| seat | 45 |
| surface | 29 |

- **Flags:**

| flag | parts |
|---|---|
| size_doubt | 212 |
| label_doubt | 117 |
| contact_doubt | 49 |
| plane_doubt | 35 |
| affordance_doubt | 9 |
| hygiene_overturned | 4 |

- **World size:** usable parts with a size_cm: 1,090. The rest are frame-sized backdrops, fx or unknown.

## Merge rules

The full text of each rule is in `registry.json` under `rules`.

- **Usability**
  - U1 hygiene C
  - U2 semantics skip
  - U3 character-fragment
  - U4 space placeable=false (only when it adds information)
  - U5 drop affordances of unusable parts
  - U6 ignore the echoed registry q
  - U7 reference wording
  - U8 unnamed lettering
  - U9 tan "(N CARDS)" heading strips (measured `merge/tanstrip.json`)
  - U10 black lettering or label boxes (measured `merge/letters.json`)
  - U11 captioned "ASSEMBLED REFERENCE" images
- **Overturns:**
  - U2o: a heading-like label on a clean object.
  - U4o: reference wording on a clean object.
  - H1: corner-clip only, on intact portals and temples.
- **Misfiles:**
  - C1: fx-sheet objects named pills or heart.
  - C2: "character fragments" that are a sofa arm, a marionette control, a glass panel or a "Poet" caption.
  - C3: strong grip label means handheld-prop.
  - C4: cup, saucer and coupe labels mean handheld-prop, and a facade label means architecture.
  - C4b: C4 is skipped when CLIP is at least 0.9 sure it is furniture. The tableware label belongs to a neighbouring card.
  - C5: the poet's-eye sheet is all character fragments.
- **Planes:**
  - P1: fx cards with code-only labels go back to overlay_fx. Plant cards become plant-nature/near_set and building strips become architecture/mid_set.
  - P2: props and furniture are never put on the backdrop or overlay planes.
  - P3: text-graphic plates on props/set sheets go to near_set.
- **Flags:**
  - F1: scale conflict
  - F2: size outside the category's range
  - F3: affordance not compatible with the category (confidence capped at 0.35)
  - F4: label/CLIP conflict plus label mismatch
  - F5: light-fx not on overlay_fx
  - F6: duplicate

### Changed after viewing the atlases

- **U8:** v1 killed the TIDE OFFICE plate, a blank number strip, a poster frame and a thread. It now needs an empty label.
- **U4 and U7:** reference wording on a part id or label had blocked a lantern, a gold rim, skyline terraces, hanging foliage, a pearl bracelet, a door frame and VU meter parts. These were clean pieces with a heading attached by mistake. Added U4o.
- **P1:**
  - v1 put every code-labelled fx card on overlay_fx, including tulips and BO1–3 tower strips. Plant and building exceptions added.
  - It also left the "(N CARDS)" heading strips usable. Added U9.
- **Lettering:**
  - "LIGHTS", "PARTS", "FRONT WHEEL RING", "WHEEL SPOKE INSERT" and an "8 wide light pool" label box were usable. Added U10, with the dark threshold lowered from 0.35 to 0.30 after a second look.
  - Two "ASSEMBLED REFERENCE" scene images were usable. Added U11.
- **C4 then C4b:** "7 ESPRESSO CUP (TABLE)" and "8 SAUCER" are actually bentwood chairs (viewed). Pews were briefly made handheld because of the word "glass", so "glass" was removed from C4.
- **C2:** the sofa arm, marionette crossbar, handprint glass and the "Poet" ground strip had been made unusable as body parts.
- **C5:** "LOWER LID" and the iris rings from the poet's-eye sheet had been filed as ground or light-fx.
- **H1:** viewed the shadowpool frames, the temple "4. COMPLETE" and the temple shadow. All are intact.
- **P3:** name plaques, the EXIT sign and the TIDE OFFICE plate had been on overlay_fx.
- **F3:** ground was allowed to carry aperture (floor openings) and aperture to carry stand_on (thresholds).

## How to query

```bash
cd shots/scion2/setpieces
python3 query.py find --category furniture-seat --affordance seat --min-grade A
python3 query.py find --affordance grip --poem 13 --plane near_set
python3 query.py find --category backdrop --plane far_backdrop --text night
python3 query.py find --scene bedroom --exclude-flags size_doubt,label_doubt --json
python3 query.py why 09.set.mother_living_room/right-sofa-arm-wide-enough-for-poet-to-sit-on
python3 query.py stats
```

```python
import sys; sys.path.insert(0, 'shots/scion2/setpieces'); import query
chairs = query.find(category='furniture-seat', affordance='seat', usable_only=True, min_grade='A')
seat = next(a for a in chairs[0]['affordances'] if a['kind'] == 'seat')['geometry']   # seat_y, x_range, back
k = query.scale_px(chairs[0], px_per_cm=3.0)    # resize factor so the chair renders at its size_cm
```

`find()` hides unusable parts and non-best duplicates by default. It sorts best first, and when an affordance is requested it also sorts by that affordance's confidence. For scene assembly:
- Use `plane` for the depth layer.
- Use `contact.y_px` as the floor line. For hangs it is the top row.
- Use `size_cm` with `scale_px` for scale.
- Use `affordances[*].geometry` for interaction points.
- Treat any part whose `flags` contain size_doubt or label_doubt as needing a person or a fallback.

## Atlases (audit)

- `atlas/cat_<category>.jpg`: every usable piece of that category, best first. A pink tile means the part carries a flag. Tile text: grade, plane, size and DUP; then name; then flags and affordances; then id.
- `atlas/unusable.jpg`: every unusable card with its rule, the swarm that blocked it, and the reason.
- `atlas/unusable_refs.jpg`: the 152 reference panels.
- `atlas/merge_rules.jpg`: every part whose category or plane a merge rule changed.

Viewed by the merge swarm: unusable (all of it, twice), merge_rules, furniture-seat, text-graphic, handheld-prop page 1, light-fx page 1, other page 1, vehicle page 1, the last page of architecture, and the last page of ground. **Not viewed:** aperture, backdrop, plant-nature, wearable, furniture-surface, and the middle pages of the large categories.

## Known gaps

- **Wrong labels:** semantics and space both trust labels that sometimes belong to a neighbouring card. Only the cases caught by label_doubt, F3, C4b or viewing are corrected. Example: a lantern labelled "SHORE" is still filed as ground.
- **Sizes:** sheet-median sizes are often wrong for part-of pieces, for example bike-view parts at 2–8 cm. 212 parts carry size_doubt, and 883 usable parts have no size_cm.
- **Fx sheets:** after P1, tulips 16/18/19 on `13.fx.orbit-harvest` and the stone weights on `08.fx.soul-weather` are still light-fx/overlay_fx.
- **Signs and words:**
  - NEW SINGLE (marquee lettering strip) and MORE SPACE FOR LAUGHTER (word card) stay unusable. Both are conservative calls and may be real signs.
  - Text-graphic plates have no size.
- **Fingerprint sheet:** the R1–R6 parts on `05.props.fingerprint` were not checked by eye.
- **Hygiene's own gaps** (no OCR, character_baked recall) carry through.
