# Cast plan — layered rig for every character

Built 2026-10-23 from the poem plans (`stage/plans/NN.json` shot text), scene times (`stage/timeline/NN.json`), the cut catalog, `bodylab/body.json`, the Pose Lab files in `rig/poses/` and a visual check of every whole-figure card. Machine-readable version: `shots/scion2/cast_plan.json`.

## Totals

- **41 characters** across 14 poems (38 already have Rig Builder data in `shots/rig/data/`).
- **243 single whole-figure paintings**, 213 not clipped. All 243 now have markers: the 7 existing Pose Lab files plus 31 new files written in this pass (114 cards).
- **33 multi-figure cards** (couples, hugs, pairs, dissolve strips). These need splitting before they can be rigged.
- **No whole figure at all:** `friend_2/poem12`, `gatekeeper/atlantis`, `elders/memory`, `family_misc/poem10`, `fellow_mason/poem11`. Of these, friend_2 and the gatekeeper need puppets built from parts. The others are silhouettes or head-turn cards and need no rig.

### Corrections found on the way

- `solve.py` keys a card by the sheet it sits on. As a result, **12 EX paintings** on `poet.0x.main-poses` were solved with the POET rig, inside `poet__black_tshirt.json` and `poet__red_black_sunglasses.json`. `ex__ex_jacket.json` now holds them under the EX.
- `young_ghost.02.main-poses` is aliased to `young_poet/child_clothes`, but the boy on it wears **plaid winter pajamas** (`young_poet/pajamas_winter`), and two of its cards are the **ghost child**. Two more cards show both of them together.
- `poet_soul.08.main-poses/06-return` and `part-9` are clipped halves of the **poet**, not the soul.
- 30 cards are clipped: the cutter split the figure with a straight vertical line, which shows up most on the poet 05/07/08/09/10/13 sheets. They keep their markers but cannot serve as masters.
- `08.cast.club.main-poses` (12 dancers) and `party.vintage_party.*` (16 single dancers) had no markers. solve.py keys them as `club/shared` and `vintage_party/vintage`, which have no rig. They are now split into club_dress, club_shirt, club_jacket, vintage_man and vintage_woman.

## Recommended production order (most screen time first)

| # | character | screen time (s) | poems | whole paintings (usable) | markers | master front / 3-4 / profile / back | missing views |
|---|---|---|---|---|---|---|---|
| 1 | **Poet (red/black tracksuit, sunglasses)** `poet/red_black_sunglasses` | 1000.9 | 04 05 06 07 08 09 10 11 12 13 14 | 93 (68) | 93 | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` |  |
| 2 | **The EX (olive bomber jacket, jeans, white sneakers)** `ex/ex_jacket` | 247.2 | 01 02 03 07 08 09 | 19 (17) | 19 | back: `back-view-neutral-stand-with-vape-pen-01`; 3/4 back: `proofs`; profile: `ex-zips`; seated: `part`; falling: `03-fall-back-04` | front |
| 3 | **Poet (black t-shirt, jeans)** `poet/black_tshirt` | 144.0 | 01 02 03 | 17 (17) | 17 | front: `read-the`; 3/4: `poet-follows-the`; profile: `run-threequarter`; back: `two-backs-out-of-step-1`; seated: `sit-up-awake-2`; lying: `sit-up-awake`; falling: `noet` | kneeling |
| 4 | **Party guest (black jacket, white tee)** `party_guest/guest` | 100.5 | 06 07 | 7 (6) | 7 | front: `04-lighter-up-2`; 3/4: `02-mouth-words-we-love`; profile: `03-mouth-words-we-not`; back: `walk-into`; seated: `01-couch-lean-hand-to-chest` |  |
| 5 | **Poet's soul (pale-blue acetate poet, ring head)** `poet_soul/soul` | 61.0 | 08 | 6 (6) | 6 | front: `part-10`; 3/4: `stand-front`; seated: `05-ledge-sit-2`; kneeling: `part-4` | back, profile |
| 6 | **Brother 1 (grey hoodie, jeans)** `brother_1/poem12` | 57.6 | 12 | 2 (2) | 2 | front: `welcome`; 3/4 back: `back` | profile, back |
| 7 | **Friend 1 (navy jacket, khakis)** `friend_1/poem12` | 57.6 | 12 | 2 (2) | 2 | front: `part-25` | 3/4, profile, back |
| 8 | **Friend 2** `friend_2/poem12` | 57.6 | 12 | 0 (0) | 0 | — |  |
| 9 | **Vintage party man (pinstripe suit)** `vintage_man/suit` | 53.8 | 01 14 | 8 (8) | 8 | front: `main-poses`; 3/4: `dance-threequarter`; profile: `dance-profile`; back: `dance-back`; 3/4 back: `dance-threequarter-back` |  |
| 10 | **Vintage party woman (ivory gown)** `vintage_woman/gown` | 53.8 | 01 14 | 8 (8) | 8 | front: `party-vintage-party-2`; 3/4: `dance-threequarter-2`; profile: `dance-profile-2`; back: `dance-back-2`; 3/4 back: `dance-threequarter-back-party-vintage-party-main` |  |
| 11 | **Mother (afro, cardigan, green floral dress)** `mother/poem09` | 49.8 | 02 09 | 3 (3) | 3 | seated: `part-5`; profile: `part-2` | front, 3/4, back |
| 12 | **Ancestor (indigo robe with gold, copper shoulder plates)** `ancestor_robe/indigo_gold` | 48.9 | 05 | 5 (5) | 5 | front: `ida-reference-only` | 3/4, profile, back |
| 13 | **Atlantis citizen (cream wrap suit with coral trim)** `citizen_1/atlantis` | 43.7 | 06 | 7 (7) | 7 | front: `reference-only-4`; back: `citizen-1-twelve-crowd-instances`; seated: `part` |  |
| 14 | **Atlantis traveler (blue-grey greatcoat, boots)** `traveler_1/atlantis` | 39.7 | 06 | 11 (10) | 11 | front: `reference-only-2`; back: `traveler-1` | 3/4, profile |
| 15 | **Ancestor elder (white/silver robe, staff, turban) - AMOS** `ancestor_elder/white_silver` | 37.1 | 05 | 1 (1) | 1 | front: `amos-reference-only` |  |
| 16 | **DJ (cyber tracksuit, cap, headphones)** `dj_cyber/cyber` | 36.2 | 07 | 6 (6) | 6 | front: `06-stand-front`; 3/4: `03-listen-lift-earcup`; back: `05-dance-back`; crouch: `01-crouch-land` | profile |
| 17 | **Young poet, age 6 (plaid winter pajamas)** `young_poet/pajamas_winter` | 36.1 | 02 | 4 (4) | 4 | profile: `02-ghost-assembles-2`; back: `04-side-hug`; 3/4: `06-wind-up-ghost-thins-2` | front |
| 18 | **Father, elder (grey overcoat, flat cap, cane)** `father_elder/poem09` | 32.7 | 09 | 1 (1) | 1 | 3/4: `walk-east` | back, front, profile |
| 19 | **Atlantis child traveler (tan coat, teal scarf)** `child_traveler/atlantis` | 29.8 | 06 | 3 (3) | 3 | front: `27-stand-look-up`; 3/4: `28-walk-reach-up`; back: `child-traveler` |  |
| 20 | **Club dancer, woman (black sequin dress)** `club_dress/club` | 29.0 | 07 08 09 | 4 (4) | 4 | front: `fast-dance-collision-reach-1`; 3/4: `fast-dance-collision-reach-2` | back, profile |
| 21 | **Club dancer, man (floral shirt open)** `club_shirt/club` | 29.0 | 07 08 09 | 4 (4) | 4 | front: `fast-dance`; 3/4: `close-the-gap-2` | back, profile |
| 22 | **Club dancer, man (leather jacket)** `club_jacket/club` | 29.0 | 07 08 09 | 4 (4) | 4 | front: `fast-dance-collision-reach-1-2`; 3/4: `fast-dance-collision-reach-2-2` | back, profile |
| 23 | **Atlantis elder (patchwork coat and scarf)** `elder_1/atlantis` | 20.4 | 06 | 1 (1) | 1 | back: `elder-1` |  |
| 24 | **Angel (white robe, wings)** `angel/robe` | 20.1 | 08 | 6 (6) | 6 | front: `1-front-arms-lowered-wings-folded`; profile: `float-2-profile-knees-wings-half-open-bent`; back: `3-back-view-wings-open`; 3/4: `5-angel-right-tipping-basin-inward-left` |  |
| 25 | **Watchers on the avenue (heads turning)** `family_misc/poem10` | 17.2 | 10 | 0 (0) | 0 | — |  |
| 26 | **Father (poem 02, quilted jacket, plaid scarf)** `father_02/poem02` | 15.1 | 02 | 2 (2) | 2 | seated: `father-driver-profile` | front, back, profile |
| 27 | **Woman in red (afro, red dress)** `woman/poem13` | 14.8 | 13 | 1 (1) | 1 | front: `stand-small-scale-front-hand-lifted` |  |
| 28 | **Café couple 1A (man, cream shirt, jeans, sandals)** `couple_1_a/poem13` | 14.6 | 13 | 3 (2) | 3 | seated: `1a-1-b-day` | front, back, profile |
| 29 | **Café couple 1B (woman, floral sundress, braided updo)** `couple_1_b/poem13` | 14.6 | 13 | 1 (1) | 1 | seated: `seated-lean` | front, back, profile |
| 30 | **Café couple 2A (young man, light-blue shirt, white trousers)** `couple_2_a/poem13` | 14.6 | 13 | 1 (1) | 1 | seated: `2a-2b-day` | front, back, profile |
| 31 | **Café couple 2B (young woman, light-blue dress)** `couple_2_b/poem13` | 14.6 | 13 | 1 (1) | 1 | seated: `seated-lean-2` | front, back, profile |
| 32 | **Café couple 3A (older bald man, cream shirt, jeans)** `couple_3_a/poem13` | 14.6 | 13 | 1 (1) | 1 | seated: `3-a-3-b-day` | front, back, profile |
| 33 | **Café couple 3B (woman, white dress, blue sash)** `couple_3_b/poem13` | 14.6 | 13 | 1 (1) | 1 | seated: `seated-lean-3` | front, back, profile |
| 34 | **Young poet (striped tee, denim shorts)** `young_poet/child_clothes` | 14.2 | 13 | 3 (3) | 3 | 3/4: `strict-rail-lean` | front, back, profile |
| 35 | **Elder man (black/gold robe, pearls)** `elder_man/poem13` | 14.2 | 13 | 1 (1) | 1 | kneeling: `r2-kneel-bowed-threequarter-eyes-closed` | front, seated |
| 36 | **Elder woman (black/gold robe, pearls, rosary)** `elder_woman/poem13` | 14.2 | 13 | 2 (2) | 2 | kneeling: `part-18` | seated |
| 37 | **Atlantis gatekeeper** `gatekeeper/atlantis` | 14.1 | 06 | 0 (0) | 0 | — |  |
| 38 | **Man in street clothes (denim jacket, jeans) - identity unsure** `family/street_clothes` | 12.5 | 10 11 14 | 2 (2) | 2 | front: `laugh-standing-head-back`; seated: `grief-seated-head-in-cupped-hands` |  |
| 39 | **Ghost child, age 7 (pale nightgown)** `ghost_child/ghost_nightclothes` | 11.6 | 02 | 2 (2) | 2 | profile: `02-ghost-assembles-1` | front, back, 3/4 |
| 40 | **Memory elders (flat backlit silhouettes)** `elders/memory` | 7.2 | 12 | 0 (0) | 0 | front: `3a-arm-down` |  |
| 41 | **Fellow mason (optional)** `fellow_mason/poem11` | 0 | 11 | 0 (0) | 0 | — |  |

Notes on the order:

- The **poet (tracksuit)** carries about 1000 s across 11 poems. Its two h3 masters, FRONT `poet.11/02-front-guide-stone` and Q3R `poet.10/q1-approach-bike`, are in place. Next to add: a back master (`poet.14.exit/1-stand`), a profile master (`poet.11/03-walk-profile-colonnade`), a seated master (`hipcore/seated`) and a kneeling master (`poet.04/04-2-kneel-hollow`).
- The **EX** is second at 247 s, all back views. Use the back master (`ex.ex_jacket.master/back-view-neutral…`) and the 3/4-back master (`ex.ex_jacket.hipcore/proofs`).
- The **poet in the black t-shirt** follows, for poems 01-03.
- **Crowd puppets** come next and are reused many times: the party guest (06-07), the vintage couples (01, 14), the club dancers (08-09) and the Atlantis travellers and citizens (06). Each has one painted body with head variants.
- **Small parts** come last: the six café couples, the elders, the woman in the window and the parents in the car. They are on screen for a few seconds, small and mostly seated, so a single seated or kneeling master per character is enough.

## Poem by poem

### 01 — Out of Life (88.38 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (black t-shirt, jeans) `poet/black_tshirt` | 76.0 — 01.0, 01.3, 01.4, 01.5 | 8 (8) | front: `read-the`; 3/4: `poet-follows-the`; profile: `run-threequarter`; back: `two-backs-out-of-step-1`; seated: `sit-up-awake-2`; lying: `sit-up-awake`; falling: `noet` | no neutral front at rest (read-the holds a page); no kneeling |
| The EX (olive bomber jacket, jeans, white sneakers) `ex/ex_jacket` | 75.1 — 01.0, 01.1, 01.2, 01.3, 01.4 | 7 (7) | back: `back-view-neutral-stand-with-vape-pen-01`; 3/4 back: `proofs`; profile: `ex-zips`; seated: `part`; falling: `03-fall-back-04` | front and true profile are absent on purpose (back-only design); 01.2 tipping backward over the rail: 03-fall-back-04 is close |
| Vintage party man (pinstripe suit) `vintage_man/suit` | 41.2 — 01.4, 01.5 | 7 (7) | front: `main-poses`; 3/4: `dance-threequarter`; profile: `dance-profile`; back: `dance-back`; 3/4 back: `dance-threequarter-back` | couple holds are only on 2-figure cards (waltz instances, paired choreography) |
| Vintage party woman (ivory gown) `vintage_woman/gown` | 41.2 — 01.4, 01.5 | 6 (6) | front: `party-vintage-party-2`; 3/4: `dance-threequarter-2`; profile: `dance-profile-2`; back: `dance-back-2`; 3/4 back: `dance-threequarter-back-party-vintage-party-main` | no neutral standing front; legs hidden by the gown in every pose (markers approximate) |

Gaps for this poem: 01.0 poet 3/4 back with page: none (read-the is front); 01.4 EX back between dancers: use back-view-neutral; 01.2 EX tipping over the rail backward: 03-fall-back-04 is the nearest.

### 02 — Flashing Lights (81.58 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (black t-shirt, jeans) `poet/black_tshirt` | 45.5 — 02.0, 02.1 (partly inferred) | 5 (5) | front: `read-the`; 3/4: `poet-follows-the`; profile: `run-threequarter`; back: `two-backs-out-of-step-1`; seated: `sit-up-awake-2`; lying: `sit-up-awake`; falling: `noet` | no neutral front at rest (read-the holds a page); no kneeling |
| Young poet, age 6 (plaid winter pajamas) `young_poet/pajamas_winter` | 36.1 — 02.2, 02.3, 02.4, 02.5 | 4 (4) | profile: `02-ghost-assembles-2`; back: `04-side-hug`; 3/4: `06-wind-up-ghost-thins-2` | no front (02.4 reverse: the child's face card in headlight wash -> needs a front head at least; young_poet.child_clothes heads are a different costume); 02.2 black silhouette from behind can use the back card |
| The EX (olive bomber jacket, jeans, white sneakers) `ex/ex_jacket` | 19.9 — 02.0 | 8 (8) | back: `back-view-neutral-stand-with-vape-pen-01`; 3/4 back: `proofs`; profile: `ex-zips`; seated: `part`; falling: `03-fall-back-04` | front and true profile are absent on purpose (back-only design); 01.2 tipping backward over the rail: 03-fall-back-04 is close |
| Mother (afro, cardigan, green floral dress) `mother/poem09` | 15.1 — 02.4 | 2 (2) | seated: `part-5`; profile: `part-2` | no standing pose (not needed by the plans); 09.3 hang-up "pulled off on a replacement fade" only needs the seated card |
| Father (poem 02, quilted jacket, plaid scarf) `father_02/poem02` | 15.1 — 02.4 | 2 (2) | seated: `father-driver-profile` | none needed beyond the seated driver profile (seen small in the car window) |
| Ghost child, age 7 (pale nightgown) `ghost_child/ghost_nightclothes` | 11.6 — 02.3 | 2 (2) | profile: `02-ghost-assembles-1` | no front/3/4 (02.3 two-shot hug: only the 2-figure card 04-side-hug-2); fade-out states: 06-wind-up-ghost-thins-1 (dissolving) only |

Gaps for this poem: 02.4 child front face in headlight wash: no pajama-boy front; 02.4 parents: seated profiles exist (car-argument) - fine; 02.3 ghost hug: only the 2-figure card.

### 03 — How to break off an engagement (62.52 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (black t-shirt, jeans) `poet/black_tshirt` | 22.5 — 03.4 (partly inferred) | 4 (4) | front: `read-the`; 3/4: `poet-follows-the`; profile: `run-threequarter`; back: `two-backs-out-of-step-1`; seated: `sit-up-awake-2`; lying: `sit-up-awake`; falling: `noet` | no neutral front at rest (read-the holds a page); no kneeling |
| The EX (olive bomber jacket, jeans, white sneakers) `ex/ex_jacket` | 22.5 — 03.4 (partly inferred) | 9 (9) | back: `back-view-neutral-stand-with-vape-pen-01`; 3/4 back: `proofs`; profile: `ex-zips`; seated: `part`; falling: `03-fall-back-04` | front and true profile are absent on purpose (back-only design); 01.2 tipping backward over the rail: 03-fall-back-04 is close |

Scenes with no character: 03.0, 03.1, 03.2, 03.3, 03.5.

Gaps for this poem: no plan shot shows people (footprints only); poet.03 walking backs are available if the footprints get walkers.

### 04 — Nevermore (130.95 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 124.1 — 04.0, 04.2, 04.3, 04.4, 04.5, 04.6 | 15 (15) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |

Scenes with no character: 04.1.

Gaps for this poem: 04.5 sweeping forearms / finding hands: covered (04-4-sweep-forearms, 04-5 left-then-right; one of them clipped).

### 05 — Bloodlines (74.07 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 74.1 — 05.0, 05.1, 05.2, 05.3, 05.4, 05.5 | 15 (15) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |
| Ancestor (indigo robe with gold, copper shoulder plates) `ancestor_robe/indigo_gold` | 48.9 — 05.0, 05.1, 05.3, 05.4 (partly inferred) | 5 (5) | front: `ida-reference-only` | 05.1 ancestors "pan past" in profile walking: no profile/walk painting; 05.1/05.4 passing the star orb: only the 2-figure card amos-ida-otis-ruth-mae ("MAE GIVES FIRST") |
| Ancestor elder (white/silver robe, staff, turban) - AMOS `ancestor_elder/white_silver` | 37.1 — 05.1, 05.3 | 1 (1) | front: `amos-reference-only` | only a front reference figure |

Gaps for this poem: 05.1 poet profile walk: poet.05 06-walk-to-the-gate cards are clipped/C-grade -> use poet profile master; 05.1 ancestors walking in profile: none.

### 06 — Resurrecting Atlantis (100.48 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 100.5 — 06.0, 06.1, 06.2, 06.3, 06.4, 06.5, 06.6 | 12 (12) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |
| Atlantis citizen (cream wrap suit with coral trim) `citizen_1/atlantis` | 43.7 — 06.2, 06.4, 06.5 | 7 (7) | front: `reference-only-4`; back: `citizen-1-twelve-crowd-instances`; seated: `part` | no 3/4 or profile |
| Atlantis traveler (blue-grey greatcoat, boots) `traveler_1/atlantis` | 39.7 — 06.0, 06.2, 06.4 | 11 (11) | front: `reference-only-2`; back: `traveler-1` | 06.0 "file of traveller silhouettes" walking in: no walk/profile painting; fronts are labelled reference-only (assembled, not cut parts) |
| Atlantis child traveler (tan coat, teal scarf) `child_traveler/atlantis` | 29.8 — 06.3, 06.5 (partly inferred) | 3 (3) | front: `27-stand-look-up`; 3/4: `28-walk-reach-up`; back: `child-traveler` | 06.3 crouching to draw symbols in the sand: none (source-actions has a 5-instance run cycle card) |
| Atlantis elder (patchwork coat and scarf) `elder_1/atlantis` | 20.4 — 06.4 (partly inferred) | 1 (1) | back: `elder-1` | only one pose (back, arms up) |
| Party guest (black jacket, white tee) `party_guest/guest` | 17.9 — 06.6 | 0 (0) | front: `04-lighter-up-2`; 3/4: `02-mouth-words-we-love`; profile: `03-mouth-words-we-not`; back: `walk-into`; seated: `01-couch-lean-hand-to-chest` | no neutral standing front; only one guest identity (crowd variety from heads sheet party.party_guest.heads) |
| Atlantis gatekeeper `gatekeeper/atlantis` | 14.1 — 06.0 (partly inferred) | 0 (0) | — | no whole-figure painting (atlantis.06.source-actions/gatekeeper-traveler-1 is cut wrongly: it shows the guitar citizen) -> assemble from atlantis.06.gatekeeper.body + gatekeeper-elder.heads |

Gaps for this poem: 06.0 travellers walking: none (only fronts at rest and backs arms-up); 06.3 children crouching drawing: none; 06.0 gatekeeper: no whole figure.

### 07 — DJ Turn Me Up (98.76 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 96.1 — 07.1, 07.2, 07.3, 07.4, 07.5, 07.6 | 15 (15) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |
| Party guest (black jacket, white tee) `party_guest/guest` | 82.6 — 07.0, 07.1, 07.2, 07.4, 07.6 | 7 (7) | front: `04-lighter-up-2`; 3/4: `02-mouth-words-we-love`; profile: `03-mouth-words-we-not`; back: `walk-into`; seated: `01-couch-lean-hand-to-chest` | no neutral standing front; only one guest identity (crowd variety from heads sheet party.party_guest.heads) |
| DJ (cyber tracksuit, cap, headphones) `dj_cyber/cyber` | 36.2 — 07.0, 07.6 (partly inferred) | 6 (6) | front: `06-stand-front`; 3/4: `03-listen-lift-earcup`; back: `05-dance-back`; crouch: `01-crouch-land` | no profile (booth seen from the room) |
| The EX (olive bomber jacket, jeans, white sneakers) `ex/ex_jacket` | 20.9 — 07.2 | 7 (7) | back: `back-view-neutral-stand-with-vape-pen-01`; 3/4 back: `proofs`; profile: `ex-zips`; seated: `part`; falling: `03-fall-back-04` | front and true profile are absent on purpose (back-only design); 01.2 tipping backward over the rail: 03-fall-back-04 is close |

Gaps for this poem: 07.2 ghost backs: poet.07 "2" (EX ghost) + poet back cards; poet ghost back not painted.

### 08 — Newly Single (91.53 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 83.5 — 08.0, 08.1, 08.3, 08.4, 08.5 | 16 (16) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |
| Poet's soul (pale-blue acetate poet, ring head) `poet_soul/soul` | 61.0 — 08.0, 08.1, 08.2, 08.4 | 6 (6) | front: `part-10`; 3/4: `stand-front`; seated: `05-ledge-sit-2`; kneeling: `part-4` | no back or profile (08.0 crane up with the soul is seen from below/behind); floating/peeling-up pose (08.0) has no painting |
| Angel (white robe, wings) `angel/robe` | 20.1 — 08.3 | 6 (6) | front: `1-front-arms-lowered-wings-folded`; profile: `float-2-profile-knees-wings-half-open-bent`; back: `3-back-view-wings-open`; 3/4: `5-angel-right-tipping-basin-inward-left` | none for 08.3 (all three tilts painted: 4-, 5-, 6-tipping-basin) |
| Club dancer, woman (black sequin dress) `club_dress/club` | 16.6 — 08.1 | 4 (4) | front: `fast-dance-collision-reach-1`; 3/4: `fast-dance-collision-reach-2` | all four poses are dance actions: no neutral standing, no back (09.0 crowd strips at the club sidewalk want backs) |
| Club dancer, man (floral shirt open) `club_shirt/club` | 16.6 — 08.1 | 4 (4) | front: `fast-dance`; 3/4: `close-the-gap-2` | all four poses are dance actions: no neutral standing, no back (09.0 crowd strips at the club sidewalk want backs) |
| Club dancer, man (leather jacket) `club_jacket/club` | 16.6 — 08.1 | 4 (4) | front: `fast-dance-collision-reach-1-2`; 3/4: `fast-dance-collision-reach-2-2` | all four poses are dance actions: no neutral standing, no back (09.0 crowd strips at the club sidewalk want backs) |

Gaps for this poem: 08.0 soul peeling up / floating: none; 08.5 poet over-shoulder reaching to mountains: back + reach not painted.

### 09 — Yet, Heard (108.82 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| The EX (olive bomber jacket, jeans, white sneakers) `ex/ex_jacket` | 108.8 — 09.0, 09.1, 09.2, 09.3, 09.4, 09.5 | 11 (11) | back: `back-view-neutral-stand-with-vape-pen-01`; 3/4 back: `proofs`; profile: `ex-zips`; seated: `part`; falling: `03-fall-back-04` | front and true profile are absent on purpose (back-only design); 01.2 tipping backward over the rail: 03-fall-back-04 is close |
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 108.8 — 09.0, 09.1, 09.2, 09.3, 09.4, 09.5 | 15 (15) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |
| Mother (afro, cardigan, green floral dress) `mother/poem09` | 34.7 — 09.3 | 1 (1) | seated: `part-5`; profile: `part-2` | no standing pose (not needed by the plans); 09.3 hang-up "pulled off on a replacement fade" only needs the seated card |
| Father, elder (grey overcoat, flat cap, cane) `father_elder/poem09` | 32.7 — 09.4 | 1 (1) | 3/4: `walk-east` | 09.4 is "wide from behind: two backs walking away" -> needs a BACK view of the father (none) ; 2-figure card father-elder-poet-steady-shoulder-falter exists |
| Club dancer, woman (black sequin dress) `club_dress/club` | 12.4 — 09.0 (partly inferred) | 4 (4) | front: `fast-dance-collision-reach-1`; 3/4: `fast-dance-collision-reach-2` | all four poses are dance actions: no neutral standing, no back (09.0 crowd strips at the club sidewalk want backs) |
| Club dancer, man (floral shirt open) `club_shirt/club` | 12.4 — 09.0 (partly inferred) | 4 (4) | front: `fast-dance`; 3/4: `close-the-gap-2` | all four poses are dance actions: no neutral standing, no back (09.0 crowd strips at the club sidewalk want backs) |
| Club dancer, man (leather jacket) `club_jacket/club` | 12.4 — 09.0 (partly inferred) | 4 (4) | front: `fast-dance-collision-reach-1-2`; 3/4: `fast-dance-collision-reach-2-2` | all four poses are dance actions: no neutral standing, no back (09.0 crowd strips at the club sidewalk want backs) |

Gaps for this poem: 09.4 father and son walking away (backs): father back view missing; 09.3 poet in booth with handset: phone cards are clipped (phone-palm, hang-up-2, on-glass).

### 10 — Magic Ride (96.14 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 96.1 — 10.0, 10.1, 10.2, 10.3, 10.4, 10.5 | 18 (18) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |
| Watchers on the avenue (heads turning) `family_misc/poem10` | 17.2 — 10.3 | 0 (0) | — | head-turn cards only (family.10.watcher-head-turns): no body rig needed |

Gaps for this poem: most ride cards are clipped; whole: q1-approach-bike, 03-coil-to-mount, q5-left-hand-in, in-wind.

### 11 — New Day (101.27 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 96.3 — 11.0, 11.2, 11.3, 11.4, 11.5 | 13 (13) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |

Scenes with no character: 11.1.

Gaps for this poem: 11.0 rider on the bike arriving: reuse poem 10 ride cards.

### 12 — Reunion (64.81 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Brother 1 (grey hoodie, jeans) `brother_1/poem12` | 57.6 — 12.0, 12.1, 12.3, 12.4, 12.5, 12.6 | 2 (2) | front: `welcome`; 3/4 back: `back` | 12.5 profile chain with wrists interlocked: no profile painting; hugs only as poet+brother 2-figure cards (family.12.hug-restage) |
| Friend 1 (navy jacket, khakis) `friend_1/poem12` | 57.6 — 12.0, 12.1, 12.3, 12.4, 12.5, 12.6 | 2 (2) | front: `part-25` | no profile for the brotherhood chain; small paintings (~190 px) |
| Friend 2 `friend_2/poem12` | 57.6 — 12.0, 12.1, 12.3, 12.4, 12.5, 12.6 | 0 (0) | — | no whole-figure painting at all: body sheet family.12.friend_2.body + heads only -> assemble from parts |
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 51.3 — 12.0, 12.1, 12.3, 12.5, 12.6 (partly inferred) | 10 (10) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |
| Memory elders (flat backlit silhouettes) `elders/memory` | 7.2 — 12.2 (partly inferred) | 0 (0) | front: `3a-arm-down` | flat silhouette cards with one arm state each: animate by replacement, no rig needed |

Gaps for this poem: friend_2 has no whole figure; 12.5 brotherhood chain (profile, wrists interlocked): no profile poses for brother/friends; 12.6 football: none.

### 13 — How to Win My Heart (100.73 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 100.7 — 13.0, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6 | 15 (15) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |
| Woman in red (afro, red dress) `woman/poem13` | 14.8 — 13.5 | 1 (1) | front: `stand-small-scale-front-hand-lifted` | only one pose; enough for a window card |
| Café couple 1A (man, cream shirt, jeans, sandals) `couple_1_a/poem13` | 14.6 — 13.1 | 3 (3) | seated: `1a-1-b-day` | standing/walking only on 2-figure cards (harbor walk two by two, dusk turn) |
| Café couple 1B (woman, floral sundress, braided updo) `couple_1_b/poem13` | 14.6 — 13.1 | 1 (1) | seated: `seated-lean` | standing/walking only on 2-figure cards (harbor walk two by two, dusk turn) |
| Café couple 2A (young man, light-blue shirt, white trousers) `couple_2_a/poem13` | 14.6 — 13.1 | 1 (1) | seated: `2a-2b-day` | standing/walking only on 2-figure cards (harbor walk two by two, dusk turn) |
| Café couple 2B (young woman, light-blue dress) `couple_2_b/poem13` | 14.6 — 13.1 | 1 (1) | seated: `seated-lean-2` | standing/walking only on 2-figure cards (harbor walk two by two, dusk turn) |
| Café couple 3A (older bald man, cream shirt, jeans) `couple_3_a/poem13` | 14.6 — 13.1 | 1 (1) | seated: `3-a-3-b-day` | standing/walking only on 2-figure cards (harbor walk two by two, dusk turn) |
| Café couple 3B (woman, white dress, blue sash) `couple_3_b/poem13` | 14.6 — 13.1 | 1 (1) | seated: `seated-lean-3` | standing/walking only on 2-figure cards (harbor walk two by two, dusk turn) |
| Young poet (striped tee, denim shorts) `young_poet/child_clothes` | 14.2 — 13.2 | 3 (3) | 3/4: `strict-rail-lean` | only rail-lean poses exist; 13.2 needs only a small face at the café glass -> young_poet.child_clothes heads/face sheets suffice; no standing neutral whole figure (body sheets front/back/profile/threequarter are parts only) |
| Elder man (black/gold robe, pearls) `elder_man/poem13` | 14.2 — 13.2 | 1 (1) | kneeling: `r2-kneel-bowed-threequarter-eyes-closed` | 13.2 puts the elders seated "in the second pew": no seated painting; kneel cards + 2-figure prayer steps only |
| Elder woman (black/gold robe, pearls, rosary) `elder_woman/poem13` | 14.2 — 13.2 | 2 (2) | kneeling: `part-18` | no seated painting |

Gaps for this poem: 13.2 elders seated in pews: only kneeling; 13.6 poet walking from behind: poet back master.

### 14 — Hot Minute (69.36 s)

| character | on screen (s), scenes | paintings from this poem (with markers) | master candidates | gaps |
|---|---|---|---|---|
| Poet (red/black tracksuit, sunglasses) `poet/red_black_sunglasses` | 69.4 — 14.0, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6 | 9 (9) | front: `02-front-guide-stone`; 3/4: `q1-approach-bike`; profile: `03-walk-profile-colonnade`; back: `1-stand`; seated: `seated`; kneeling: `04-2-kneel-hollow`; lying: `q3-restless-lying-1` | no clean 3/4 FRONT standing neutral (q1-approach-bike is mid-walk with bike); no pure profile standing at rest |
| Vintage party man (pinstripe suit) `vintage_man/suit` | 12.6 — 14.5, 14.6 | 8 (8) | front: `main-poses`; 3/4: `dance-threequarter`; profile: `dance-profile`; back: `dance-back`; 3/4 back: `dance-threequarter-back` | couple holds are only on 2-figure cards (waltz instances, paired choreography) |
| Vintage party woman (ivory gown) `vintage_woman/gown` | 12.6 — 14.5, 14.6 | 8 (8) | front: `party-vintage-party-2`; 3/4: `dance-threequarter-2`; profile: `dance-profile-2`; back: `dance-back-2`; 3/4 back: `dance-threequarter-back-party-vintage-party-main` | no neutral standing front; legs hidden by the gown in every pose (markers approximate) |
| Man in street clothes (denim jacket, jeans) - identity unsure `family/street_clothes` | 12.5 — 14.2 (partly inferred) | 2 (2) | front: `laugh-standing-head-back`; seated: `grief-seated-head-in-cupped-hands` | who this is is not stated; body sheets front/back/profile exist as parts |

Gaps for this poem: 14.1 poet floating/rotating in the black: none; 14.5 muse dance: only 2-figure cards (poet.14.muse-dance); 14.2 B-roll man: identity unsure.

## Evidence

Every scene-to-character link in `cast_plan.json` (`poems.NN.cast.<char>.scenes[].evidence`) quotes the plan shot text. Links marked **inferred** come from the cut sheets or the poem lines instead:

- 02.1: poet (toss/mirror poses).
- 03.4: poet and EX (the "two backs out of step" sheet behind the footprints).
- 05.0: ancestors (the lantern staffs).
- 06.0: gatekeeper.
- 06.4: Atlantis elder.
- 06.5: families.
- 07.6: DJ.
- 09.0: club crowd.
- 12.0 and 12.1: poet.
- 12.2: memory elders.
- 14.2: the street-clothes man.

**Unsure identities.**

- `family/street_clothes`: a man in a denim jacket. He could be the poet out of costume or a B-roll stranger; nothing in the repo says.
- `poet.14.reserve/26-27`: a white/grey tracksuit poet, probably the 14.3 "graytones" state.
- The couple a/b pairing is taken from the card names (1a, 1-b, etc.).

## Marker files written in this pass (`shots/rig/poses/`, new files only)

- **How they were made.** The repo's own tool did the work: `markers.html`, `movenet-run.js` with the vendored model `movenet.js` (MoveNet Lightning, offline), and `PoseCore.prefillMarkers`. It ran headless in Chromium (CPU backend) on a scratch target list built with `solve.prepare` (bbox and brass brads).
- **How they were checked.** Every overlay was checked by eye. Each target carries `marker_source`, `confidence` (0.25 / 0.55 / 0.8) and `review {grade, note}`.
- **Manual fixes.** Five rejected reads were re-marked by hand (`marker_source: "manual"`, with `"manual-hidden"` for occluded joints): the two elder women and the elder man kneeling, the ghost child in profile, and the grief-seated man.
- **Dropped markers.** Two clipped cards had their leg markers removed.
- **No solves yet.** The files hold targets and markers only. To get keyframes, run `solve.py` for these keys after its target list maps the cards to them; it currently skips or mis-keys them.

- `ancestor_elder__white_silver.json` — 1 cards (1 medium)
- `ancestor_robe__indigo_gold.json` — 5 cards (5 medium)
- `brother_1__poem12.json` — 2 cards (1 medium, 1 good)
- `child_traveler__atlantis.json` — 3 cards (1 medium, 2 good)
- `citizen_1__atlantis.json` — 7 cards (5 good, 2 medium)
- `club_dress__club.json` — 4 cards (4 good)
- `club_jacket__club.json` — 4 cards (4 good)
- `club_shirt__club.json` — 4 cards (4 good)
- `couple_1_a__poem13.json` — 3 cards (2 good, 1 poor)
- `couple_1_b__poem13.json` — 1 cards (1 medium)
- `couple_2_a__poem13.json` — 1 cards (1 good)
- `couple_2_b__poem13.json` — 1 cards (1 medium)
- `couple_3_a__poem13.json` — 1 cards (1 good)
- `couple_3_b__poem13.json` — 1 cards (1 medium)
- `elder_1__atlantis.json` — 1 cards (1 good)
- `elder_man__poem13.json` — 1 cards (1 manual)
- `elder_woman__poem13.json` — 2 cards (2 manual)
- `ex__ex_jacket.json` — 16 cards (14 good, 2 medium)
- `family__street_clothes.json` — 2 cards (1 good, 1 manual)
- `father_02__poem02.json` — 2 cards (2 medium)
- `father_elder__poem09.json` — 1 cards (1 good)
- `friend_1__poem12.json` — 2 cards (2 good)
- `ghost_child__ghost_nightclothes.json` — 2 cards (1 manual, 1 poor)
- `mother__poem09.json` — 3 cards (3 medium)
- `poet__black_tshirt.supplement.json` — 2 cards (2 good)
- `poet__red_black_sunglasses.supplement.json` — 10 cards (6 good, 3 medium, 1 poor)
- `traveler_1__atlantis.json` — 11 cards (10 good, 1 poor)
- `vintage_man__suit.json` — 8 cards (7 good, 1 medium)
- `vintage_woman__gown.json` — 8 cards (8 medium)
- `woman__poem13.json` — 1 cards (1 good)
- `young_poet__pajamas_winter.json` — 4 cards (2 good, 2 medium)
