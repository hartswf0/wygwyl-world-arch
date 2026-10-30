# Parts audit (lane A): every sheet, every cut, one registry

Written 2026-10-30 by `shots/suite/tools/*.py`. All numbers below come from `data/sheets.json`,
`data/parts.json`, `data/parts_summary.json` and `review/parts_measure.json`; rerun the tools to refresh them.

```
python3 shots/suite/tools/kit_registry.py         # kit.py layouts for all 10 v2 builds -> data/kit_layouts.json
python3 shots/suite/tools/sheets.py               # sheet inventory                     -> data/sheets.json
python3 shots/suite/tools/cut_all.py   <work>     # cut every painted part sheet (release cutter, flattened ground)
python3 shots/suite/tools/clip_tag.py  <work>     # zero-shot tags for cards the layout cannot name
python3 shots/suite/tools/build_parts.py <work>   # name, pivot, sockets, scale       -> data/parts.json, parts_summary.json, parts/cut/
python3 shots/suite/tools/measure_parts.py        # pivot and scale checks on the cards -> review/parts_measure.json, parts_contact.jpg
```

## 1. Sheets

| group | where | sheets | state | holds parts | cut before | cut now |
|---|---|---:|---|---:|---:|---:|
| kit3 v2 templates | `arena/parts/kit3/v2/templates` | 95 | empty layout (85 cells sheets + 10 cut charts) | – | – | – |
| kit3 v2 packs | `arena/parts/kit3/v2/packs` | 287 | **259 empty layouts** (panel A unpainted), 28 composited by `generate_v2_kits.py` (14 poem prop packs, 14 poem set packs) | 273 | – | – |
| kit3 v2 renders | `arena/parts/kit3/v2/rendered` | 17 | painted | 17 | 17 (`v2/cut`, generic names, no pivots/scale) | 17 |
| poem kits | `kits/packs/poem_NN/0X_*` | 365 unique (by content; 668 files with repeats across poems) | painted | 268 (character 144, actions 59, props 65); 97 sets/fx are not puppet parts | 153 of the 268 had a `release_v2/cuts` dir, but only 1,714 of the 6,234 cards that `release_catalog.json` lists are on disk | 268 |
| tracksuit sources | `kits/packs/poet_tracksuit_v1/0{2,3}_*` | 7 | painted | 7 | 31 parts by the kit author | 7 |
| weave man | `weave/cast/man/sheets` | 18 | painted | 18 | yes: `weave/cast/man/{parts,library}` (cast.json, library_manifest.json) | no (registered as cut) |
| Bolas dummy | `arena/cast/dummy/_sheet_bola.jpg` | 1 | drawn in code | 1 | yes: `arena/cast/dummy/*.png` | no |

- **Painted sheets that hold puppet parts: 311** (268 poem kit + 17 v2 renders + 7 tracksuit + 18 weave + 1 dummy).
  **Cut in this pass: 292** (all poem kit, v2 render and tracksuit sheets), into 4,491 working cards after dropping
  232 text/caption cards and 572 assembled "reference proof" figures the release cutter marks below a divider.
- **Empty layouts are not parts.** All 259 character packs in `kit3/v2/packs` are unpainted panel-A layouts, so their
  cells count as *missing* unless a poem-kit painting or a composite fills them (section 4).
- **Pivots/sockets on the sheet:** every layout has brad crosses (A green, B red, torso sockets blue) placed by kit.py;
  on the painted sheets the brads are painted brass: 2,320 of the 4,491 new cards carry at least one readable brad.
- The old Body Lab (`arena/parts/body_lab/body_lab_unified.json`) points 2,717 of its 3,997 entries at
  `release_v2/cuts` files that are not in the repo; every one of those sheets is cut again here.

## 2. How a card is named, pivoted and scaled

- **Cutting** reuses `arena/parts/kit3/cut_release_kits.py::cut_single_sheet` (alpha from card vs ground, connected
  components, holes, reference-row split). The v2 renders and weave sheets sit on vignetted off-white paper, so the
  ground is flattened first (`tools/cutter.py`); colours are restored inside each card. 997 cards reuse the existing
  `release_v2/cuts` file (same bbox and size); 3,494 are new WebP files in `shots/suite/parts/cut/` (≈33 MB).
- **Names** (`label_method`): `layout` (612 cards) where the sheet's kit layout and the cut agree: hands 24, heads 5/10,
  feet 6, face 27 (plate + 8 eyes + 6 brows + 12 mouths), replacements 6, hipcore 5, and body sheets filled slot by
  kind (torso, two hands, two feet by CLIP; limb segments in the layout's own reading sequence upper arm, forearm,
  [upper arm, forearm,] thigh, shin, ...); each layout naming had to agree with CLIP on ≥60% of cards (all 30 did,
  median 100%). `prompt` (128) where the sheet's prompt numbers its cards and the count matches. `clip` (3,742 painted
  cards) otherwise: coarse kind only, limb segments stay `limb` / `unassigned`, with two shape corrections (a long
  capsule with a brad at each end is a limb, not a foot; a "face feature" taller than 22% of the sheet is a head).
- **Pivots** are the brass brads read off each card (`tools/cutter.py::brads`: brass hue 19–34, round once eyelet
  holes are filled, inside the card). 2,445 painted parts pivot on a read brad, 337 on kit.py's limb rule (A half a
  card-width in from the end) where no brad was readable, 67 on sockets placed by hand earlier (registered.json,
  weave cast.json, man_hands/hands.json); the rest are constructed and say so in `pivot_source`.
- **Sockets:** limbs A/B; torso neck, shoulder_L/R, waist, hip_L/R (actor L is viewer right in front view); pelvis
  waist + hips; hands wrist, palm, grip, tip; feet ankle, heel, toe (on the sole line); heads/face plates neck, crown,
  eyes, mouth, chin (kit.py head ratios 0.356 / 0.585 / 0.70 of crown→neck); props grip; whole-body cards hip.
- **Scale** (px per cm): per sheet, the median over cards whose span can be trusted against the character's skeleton
  (kit.py `humanoid(height_cm)`): hands wrist→tip, heads crown→neck, and – only when the layout or prompt named them –
  limb brad spans, torso neck→waist and flat profile feet heel→toe. 117 of the 292 cut sheets have such cards;
  **2,404 of 5,408 painted parts have a measured scale**. The layout's own px/cm is *not* used as a fallback: the
  painters did not keep it (measured sheet px/cm is a median 39% above the layout's px/cm × sheet width / 2048, n=35).
  Composited v2 parts use the template px/cm they were pasted at (6 body, 11 hands/feet, 12 heads, 14 face).
  Each trusted card also carries `scale.own_px_per_cm` and `scale.vs_skeleton_pct`.
- `height_cm_real` is the part file's own height in cm (file px ÷ px/cm); `char_height_cm` is the character's.

## 3. The registry

`data/parts.json`: **9,108 parts** — 5,408 painted, 3,519 composited (`kit3/v2/parts`, recoloured/pasted from other
paintings by `generate_v2_kits.py`, not painted for that character), 181 coded (arena/parts/lib, Bolas dummies, weave
proc.*). 5,715 have a scale.

| category | all | painted |
|---|---:|---:|
| hands | 1,989 | 775 |
| feet / shoes | 761 | 464 |
| heads (+ face plates) | 661 | 399 |
| eyes · mouths · brows · noses · glasses | 1,310 | 730 |
| limbs (upper arm, forearm, thigh, shin, unassigned limb) | 2,030 | 1,179 |
| torsos · hips · wings | 738 | 559 |
| whole-body replacement cards | 499 | 339 |
| props | 1,120 | 963 |

Parts by part: hand 1,989 · prop 1,120 · limb (unassigned) 1,005 · foot 761 · head 635 · mouth 512 · replacement 499 ·
eye 411 · torso 356 · pelvis 308 · brow 285 · forearm 263 · upper arm 261 · shin 259 · thigh 242 · wing 74 · nose 54 ·
glasses 27 · face plate 26 · accessory 21.

Sources registered without re-cutting (provenance kept per part): `kit3/v2/parts` 3,519 · weave man 268 ·
tracksuit 31-part set + profile faces 81 · body_lab crops 344 · arena/parts/lib 84 · arena/parts/cut 49 · Bolas
dummy 120 · weave woman (p07) 11 · play/data.json whole-figure draws 141. Not registered: 350 `kit3/v2/parts` set
plates (S#_P# stage layers: lane C's) and the `kit3/v2/cut` and `kits/packs/poem_NN/cut` cuts, which are superseded
duplicates of sheets cut here.

## 4. What is missing (painted parts vs the v2 kit cells)

Cells come from v2.py: principal characters get body ×4 views, heads, face front/profile, hands, feet,
replacements (141 cells); EX gets back/three-quarter-back only (58); extras get body front/back/profile, heads, hands (62).

| character | cells | missing painted | missing even counting composites | what is missing (painted) |
|---|---:|---:|---:|---|
| POET | 141 | 8 | 0 | three-quarter limb segments (that sheet's limbs could not be split) |
| EX | 58 | 0 | 0 | – |
| YOUNG POET | 141 | 65 | 0 | 24 hand shapes, face front (plate, 8 eyes, 5 brows, 11 mouths), 16 limb segments |
| GHOST CHILD | 141 | 123 | 0 | nearly everything: only the action/compact-core sheets are painted |
| THE WOMAN | 141 | 122 | 0 | nearly everything except her p07 weave parts and the mother/window sheets |
| PARENTS | 62 | 57 | 0 | the kit sheets (bodies, 24 hands, 5 heads); only role sheets exist |
| ANCESTORS | 62 | 57 | 0 | same |
| ATLANTIS | 62 | 52 | 0 | same (heads exist) |
| PARTY · CLUB · DJ | 62 | 0 | 0 | – |
| ANGELS | 62 | 57 | 5 | same; 5 cells have no composite either |
| FAMILY | 62 | 0 | 0 | – |
| BOLA / SHIM / DOT | 141 | 138 / 141 / 130 | 1 / 1 / 1 | the painted Bolas kit (only v2 renders of Bola/Dot body front exist) |

The full cell lists are in `data/parts_summary.json → missing.<character>.missing_painted_cells`.

## 5. Measured (on the card files)

**Pivot vs brad mark.** Over all 1,989 painted cards that pivot on a read brad, the release cutter's own brad detector
(a different colour rule) finds a brad a median **1.4 px** from the registry pivot; 70% within 3 px, 80% within 15 px
(median 1.1 px for those). In a visual check of 16 cases over 15 px, 14 were the other detector missing the pivot
brad and matching skin, kraft or another brad; 2 were bad cards. The 10 random cards in the contact sheet: 2.5, 194.2
(other detector missed the top brad), 1.4, 0.4, 43.1 (sneaker: the other detector fired on the kraft tab), 4.5, 0.4,
2.0, 0.4, 0.7 px. kit.py's limb rule (A half a card-width in) lands a median 25.7 px from the painted brad (n=128):
painters put the eyelet nearer the end than the layout did, so read brads beat the rule.

**Scale vs the character's height.** Each trusted card's span, converted with its sheet's px/cm computed *without
it*, against the skeleton length from height_cm: median **7.8%** error (n=700; p90 30.7%). By part: heads 1.8%,
hands 6.8%, thighs 20.7%, feet 22.4%, torsos 24.0%, shins 24.6%, upper arms 25.4%, forearms 27.4%. The limb errors are
the paintings, not the reader: on the body sheets painted arm segments run +13% (upper arm) / +21% (forearm) long and
legs −19% (thigh) / −22% (shin), torsos −24%, against the skeleton — arms and legs were painted almost the same length.
A rig that pins these cards must rescale per part (`scale.own_px_per_cm`), not per sheet. The 10 random cards:
hand +11.5%, forearm +50.9% (family profile), shin +27.2% (woman v2 profile: a fused leg named shin), hand +9.8%,
head +8.0%, head +0.6%, head −16.1%, hand −9.1%, head +7.7%, thigh −24.9%.

Contact sheet: `review/parts_contact.jpg` (top: pivots, sockets and the independent detector's rings; bottom: the 10
scale cards drawn on one cm grid).

## 6. Known weak spots

- 3,742 painted cards are named by CLIP only (coarse kind, `view` from the sheet name or `unknown`); 1,005 limb
  segments are `limb`/`unassigned`. Sample errors seen: a fused thigh+shin named shin, couples' figures named pelvis,
  a few captions that survive the text filter.
- 3,004 painted parts have no scale (their sheet has no trusted span). The Body Lab draws them 40 cm on the long side
  with a dashed edge rather than guessing.
- The 31-part tracksuit set was rendered one component per canvas, so each card is scaled by its own span; hands,
  boots and the head of that set have no brad span and stay unscaled.

## 7. Privacy

Nothing here reads or derives from the private shoot paths. Two things to flag, untouched and not spread:
`arena/parts/kit3/refs/man_tracksuit_{front,threequarter}.png` and `man_collage.webp` are photo-real images of a man
pasted into panel B of the v2 packs (their provenance is not recorded in the repo; `weave/cast/man/README.md` says the
user's reference photos are *not* in the repo); and `kits/packs/poet_gemini_raw/` holds 44 photo-real Gemini renders of
the poet. Neither was cut, copied or registered.
