# Staged: poems 08-14

**40 of 40 scenes pass every hard check.** Passing means the measurements hold (feet, scale, contact, overlaps, word sync); it does not mean the scene is good. The weak points below are from reading contact sheets.

Poems 08 to 14 staged on lane C's sets, on the reading's clock. All numbers below are measured on the render by `lib/checks.js` (`node shots/suite/render.mjs <id>`) and stored in each `data/scenes/<id>.json`.

## How it was built

- **Windows on the reading:** `tools/stage2_windows.py` cuts each poem's reading into its scenes (word trigrams against the breakdown; hand-set starts for 09, 12, 14, where refrains or abridged lines fool the match). Windows tile the reading, so scenes play in **reading order**, which differs from the breakdown's numbering in 08 (08.2 is read first) and 12 (12.2 after 12.4). 14.1 has no words of its own and holds the pause between poems 13 and 14. The reading has "Even here is chilly in the morning" at the head of poem 11, so it sits in 11.1, not 10.6.
- **Blocking:** `tools/stage2_specs.py` (one record per scene), compiled by `tools/stage2_stage.py`. Feet are placed on the ground; no figure is scaled by hand.
- **POET** is played by his 30 painted replacement cards (`pose` beats on words, two stride cards), which answers the review note about segmented tracksuit limbs. **EX** uses back cards only. Angels and SHE use painted play cards because the stager does not draw skirt rigs. Everyone else is lane B jointed.
- **Joins:** panes cut into real surfaces of the plate (railing glass, street ad panels, shop window, chapel door, hanging sheet, hall windows), found by `lib/archive_grab.py`, labelled ARCHIVE as long as they show. Screen, wipe and citizen joins elsewhere.
- **Additions:** `lib/ext.js` (registry), `lib/stage2_extra.js` (actions pose, lean_back, nod, laugh, breathe; fx card, glow, smoke, pour, stars; join pane; held prop cards; cast.ghost; cast.play_key).

## Limits of this pass

- **Archive picks are weak in meaning.** Only 2,292 of the 15,149 clips are cached on this machine and no clip was downloaded, so many picks match by look, not subject (for example, "Moonwalk One" or "Friendship Seven" for skies; "Plant Solutions Video" for a family reunion). Titles are honest on screen, and each scene pack records the pick and its CLIP score. Re-picking by eye, or fetching the best clips, is the cheapest big improvement.
- **The `off_frame` check cannot see a head cut by the frame top** when the camera is not zoomed: the mask canvas clips the silhouette first. Head room was worked out from each set's camera height and checked by eye on contact sheets, not by this check.
- **`view_vs_travel` warnings** (warn-only) mostly come from POET's and FATHER's stride cards when they walk toward or away from the lens; no back stride card exists for either.
- **Cards do not show head beats.** On a card puppet, wince, nod and head moves change nothing visible; POET acts only through card swaps.
- **Set layers.** A plate plane has one depth, so planes can wrongly cover a figure. `set_layers` sends such planes behind the puppets per scene, which loses some true occlusion (the hall's planters).

## 08 · Newly Single

Reel: `renders/poem_08.mp4`

| scene | s | status | foot slide cm/f | contact % | scale % | bodies cm | card/travel warn f | joins (ARCHIVE) |
| :-- | --: | :-- | --: | --: | --: | --: | --: | :-- |
| 08.2 THE ESCAPE | 15.4 | PASS | 0 | – | 0.24 | 3.1 | 54 | pane wall_0 California Picture Book |
| 08.1 PULSING | 9.3 | PASS | 0 | – | 0.29 | 12.9 | 0 | pane wall_1 Apollo Soyuz |
| 08.3 IMAGINE MY BODY | 16.6 | PASS | 0 | – | 0.08 | 3 | 0 | pane wall_1 What's It to You? (Part I); citizen  Sports and Culture |
| 08.4 THE EQUATOR | 8.1 | PASS | 0 | – | 0.24 | – | 0 | wipe haze_1 Moonwalk One, ca. 1970 |
| 08.5 COOL ME DOWN | 20.1 | PASS | 0 | – | 0.21 | 60.3 | 0 | pane wall_0 Zuivel Friesche Coop. fabriek |
| 08.6 BACK TO MY BODY | 11.9 | PASS | 0 | – | 0.29 | 21.7 | 0 | pane wall_1 Steel Mill |
| 08.7 MOUNTAINS IN THE DISTANCE | 9.9 | PASS | 0 | – | 0.11 | 68.1 | 0 | pane wall_0 Cabeza Prieta National Wildlife Refuge Desert Wilderness; pane wall_0 Moonwalk One, ca. 1970 |

- **08.2** Weak: The soul reads as a second POET, not as something leaving him; he does not rise. Would help: A vellum soul card with a lift-off pose; a head-down body card. Staging notes: The soul is POET's own painted cards drawn as vellum (cast.ghost 0.55), as the dossier asks ("the same cards in vellum"). The reading puts this scene first in poem 08 (the breakdown lists it second); scenes are cut and reeled in reading order.
- **08.1** Weak: A glass walkway, not a club: three dancer cards are a thin "crowded floor". The pane is small. Would help: A rooftop-club plate with an empty floor; 6-8 more dancer cards; a back view of the jacket dancer. Staging notes: Restaged on lane C's rooftop set (a glass walkway above the city, no generated crowd in the plate): the crowd is three painted dancer cards. Dancers dance in their painted dance cards (replacement), swaying on 124 bpm bars and wandering in zones by goal.
- **08.3** Weak: "Strangers collide" is two cards walking together; the spark is only a strobe flash. Would help: Paired dancer cards at the moment of contact.
- **08.4** Weak: Good read (the sun wipe works). The soul is small and only poses. Would help: A heat-haze card over the plain. Staging notes: Only the soul is here (vellum POET cards); the body stays on the rooftop.
- **08.5** Weak: Angels pour from their own card basins to the side; the water on his head comes from a hanging basin, so two pours do not line up. Would help: An angel pour card aimed at the centre; a wet POET card (the dossier asks for one); the equator plate for this scene. Staging notes: The breakdown has the pour on the equator plain; lane C put 08.5 on the rooftop, so the angels pour on the walkway. The ice basin (08.props.basins) hangs over his head as a set card; the water is a code stream.
- **08.6** Weak: The return is a fade, not a merge; smoke is a code blur. Would help: A real smoke plate layer; a lean-back POET card (card 10 stands in).
- **08.7** Weak: The street is a parked car and ad panels; no mountains except in the panel. Would help: A street plate with mountains beyond it, as the line asks. Staging notes: EX is played only by his back cards (face never seen); he walks away up the street.

## 09 · Yet, Heard

Reel: `renders/poem_09.mp4`

| scene | s | status | foot slide cm/f | contact % | scale % | bodies cm | card/travel warn f | joins (ARCHIVE) |
| :-- | --: | :-- | --: | --: | --: | --: | --: | :-- |
| 09.1 THE SHARED MOON | 35.1 | PASS | 0 | – | 0.13 | 73.9 | 0 | pane door_1 Space Flight: Application of Orbital Mechanics; citizen  [Amateur films: Ivan Besse collection: Britton, South Dakota 1938-39] (Part VI) |
| 09.2 TEARS, AN ABYSS | 35.4 | PASS | 0 | – | 0.46 | 177.9 | 13 | pane wall_0 Arranging a Buffet Supper; pane wall_0 Apollo 12: Pinpoint for Science |
| 09.3 HIS FOOTSTEPS, RETRACED | 27.9 | PASS | 0 | – | 0.46 | 22.6 | 39 | pane wall_0 Friendship Seven; pane wall_0 No Time for Ugliness (Part I) |
| 09.4 EAST, AT THE HARBOR | 11.4 | PASS | 0 | – | 0.21 | 13.7 | 164 | screen water_0 Gouda |

- **09.1** Weak: 35 s on one set with a single static crowd; long holds between poses. Would help: A cut to a second angle, or a moon card for this arcade; EX packing card in this set. Staging notes: EX keeps his back to us (cards 00/01 and his back walk); he looks at the moon with POET, then walks off.
- **09.2** Weak: 35 s, and MOTHER is a tiny jointed figure across a street instead of in her own room; no phone in either hand. Would help: A mother_living_room plate (the dossier marks it needed) split-screen in a pane; a POET-on-the-phone card. Staging notes: EX packs the suitcase in his crouched back card ("you help me gather my things"), then stands with his back to us. MOTHER is lane B's jointed mother in her cardigan, far across the street in a lamp glow: the other end of the line (the breakdown's living room needs its own set). The phone booth is the painted 09.props.phonebooth card standing on the street at its real height (235 cm).
- **09.3** Weak: FATHER has one walk card, three-quarter front. The two overlap on screen at the end of the walk (depth is clear on the ground: no body overlap). Would help: FATHER back/profile walk cards; a sunrise harbour plate. Staging notes: FATHER is the painted father_elder walk card (the only FATHER card), summoned with an appear; POET walks with him by goal (walk_with).
- **09.4** Weak: Very small in frame, and FATHER walks away in a card that faces us (view_vs_travel warns). The plate has no quay near the camera. Would help: A FATHER back-walk card; lane C's harbour plate with a walkable quay in the foreground. Staging notes: Restaged on lane C's harbour canal (stands on water): father and son walk the far bank away from us, east, small in the frame. The FATHER walk card is three-quarter front; walking away it reads sideways (no back card exists) - his back walk card is the asset to paint.

## 10 · Magic Ride

Reel: `renders/poem_10.mp4`

| scene | s | status | foot slide cm/f | contact % | scale % | bodies cm | card/travel warn f | joins (ARCHIVE) |
| :-- | --: | :-- | --: | --: | --: | --: | --: | :-- |
| 10.1 HOP ON | 20.7 | PASS | 0 | – | 0.37 | – | 0 | wipe haze_0 Friendship Seven |
| 10.2 HEADS TWIST | 26.9 | PASS | 0 | – | 1.47 | 296.9 | 0 | wipe haze_1 Small Town Back Street - Morning (Wide Screen) |
| 10.3 MOON SETTLES | 13.7 | PASS | 0 | – | 0.09 | – | 0 | wipe wall_1 Friendship Seven; pane wall_0 Space Shuttle: A Remarkable Flying Machine |
| 10.4 NIGHT REPLACED | 15.1 | PASS | 0 | – | 0.15 | – | 16 | wipe haze_0 Bosque del Apache National Wildlife Refuge |
| 10.5 BLISSFUL, INNOCENT | 12.0 | PASS | 0 | – | 0.04 | – | 0 | wipe haze_0 Morning Fog - Time Lapse (Wide Screen 16:9); citizen  Kinderen naar buiten |
| 10.6 CHILLY MORNING | 8.5 | PASS | 0 | – | 0.98 | 29.7 | 0 | wipe haze_0 Powers Music School Presents: Musical Story Hour 02/28/09 |

- **10.1** Weak: The road is far from a 5.3 m camera: figures 135 px, plate soft at 2x push. The bike card and card 23's bike do not match in position at "hop on". Would help: A closer sidewalk plate; POET rub/mount replacement cards with the bike separate. Staging notes: The set's scale puts the road far from a 5.3 m camera (figures 135 px); the camera is pushed in 2x, the figures are not resized. The motorcycle is the painted 11.props.parked-motorcycle card at its real height (110 cm); POET's card 23 "Mounting the Motorcycle" takes over at "hop on".
- **10.2** Weak: Card 23 is POET walking beside the bike, so he never actually rides: it slides with a hop for 27 s, wheels still. The crowd is tiny and the sky wipe barely shows. Would help: A jointed rider on the bike-kit parts (10.props.bike-*, already cut) and spinning wheel cards; a street plate with buildings. Staging notes: He rides on his painted card 23 (the motorcycle in it), pinned as his walk card, so the ride is a cut-out slide with the card's hop. The crowd turns to him by goal (face POET), Thistle-Gulch style: no authored turns.
- **10.3** Weak: Very large in frame (a 1 m camera and the only floor at the bottom); his feet read as standing on the far buildings. Would help: A road-out-of-town plate with a farther floor. Staging notes: The rooftop is the only floor in view and the camera is 1 m up, so he stands close and big (a back three-quarter medium).
- **10.4** Weak: No road in the plate: he stands on a dark slope on a flat ground plane, feet do not follow the slope. Would help: A mountain-road plate with a measured camera (scale here is assumed).
- **10.5** Weak: Almost static: four poses in 12 s. Citizen disc floats in the forest. Would help: A walking-on loop for the road; a nest or dawn card.
- **10.6** Weak: He walks beside the bike here too (card 23), though the line is "riding"; the bike crowds the two extras. Would help: The jointed rider asked for in 10.2. Staging notes: The breakdown closes 10.6 on "Even here, it's chilly in the morning"; the reading speaks that line at the head of poem 11, so it lives in 11.1.

## 11 · New Day

Reel: `renders/poem_11.mp4`

| scene | s | status | foot slide cm/f | contact % | scale % | bodies cm | card/travel warn f | joins (ARCHIVE) |
| :-- | --: | :-- | --: | --: | --: | --: | --: | :-- |
| 11.1 MORNING FOG | 13.3 | PASS | 0 | – | 0.04 | – | 0 | pane wall_2 The National Wildlife Refuges of Alaska |
| 11.2 FIRST COURSES | 21.8 | PASS | 0 | – | 0.02 | – | 0 | pane wall_1 Sound And The Story; citizen  Let's Go To The Movies |
| 11.3 COLUMNS AND BEAMS | 13.4 | PASS | 0 | – | 0.07 | – | 0 | pane wall_1 Fastax-tion; wipe water_0 Inside the Fed |
| 11.4 THE INFINITY POOL | 12.6 | PASS | 0 | – | 0 | – | 0 | screen water_0 WHY SPACE |
| 11.5 WALKING ON WATER | 21.6 | PASS | 0 | – | 0.38 | – | 0 | pane wall_2 [Amateur film: Medicus collection: New York World's Fair, 1939-40] (Reel 6) (Part I) |
| 11.6 A NEW DAY | 19.1 | PASS | 0 | – | 0.02 | – | 0 | pane wall_1 RCA Presentation: Television, An |

- **11.1** Weak: Quiet by design; pane in the chapel door is tiny. Would help: A real fog plate layer.
- **11.2** Weak: Plate has no shore: he stands on a code deck strip; the deck reads as a band. Would help: A shore foreground card painted for this plate; a flame prop for "diminishing flame". Staging notes: The plate is mirror water to the frame edge; POET stands on a painted shore card (a code deck), sized by the set's scale at its line.
- **11.3** Weak: "Rebuild" has no building in it: only a pointing pose. The clip in the colonnade is tiny. Would help: Temple courses and columns already cut (11.props.temple.arrival.*) as stacking cards.
- **11.4** Weak: The camera looks down at the pool: only a kneeling figure fits, cropped close to the top-left. Would help: A journal in his hands; an eye-level pool plate. Staging notes: The camera looks down on the pool (horizon at y 80): a standing 184 cm figure fits only far away, so he is staged kneeling (cards 28, 29).
- **11.5** Weak: Reads well, but he walks on wet sand rather than water. Card 17 has hands above the head, so its alpha-based size makes the body a few % small. Would help: A water-walk plate; body-based sizing for arms-up cards.
- **11.6** Weak: Same deck strip; five poses, no movement in 19 s. Would help: A slow walk along the shore; more people from the poem's "together".

## 12 · Reunion

Reel: `renders/poem_12.mp4`

| scene | s | status | foot slide cm/f | contact % | scale % | bodies cm | card/travel warn f | joins (ARCHIVE) |
| :-- | --: | :-- | --: | --: | --: | --: | --: | :-- |
| 12.1 HUGS WITH NO REASON | 12.6 | PASS | 0 | 0.023 | 0.67 | 32.7 | 0 | pane pane_0 Plant Solutions Video - Long |
| 12.3 ELDERS, NOW PAST | 7.2 | PASS | 0 | – | 0.14 | 64.6 | 0 | pane pane_0 JFK EXHIBIT 3: RECONSTRUCTION FILM |
| 12.4 BURNING HOURGLASSES | 13.0 | PASS | 0 | – | 0.17 | 130.7 | 0 | pane pane_0 Morning Fog - Time Lapse (Wide Screen 16:9) |
| 12.2 LESS TIME, MORE SPACE | 23.7 | PASS | 0 | 0.02 | 1.53 | -35.2 | 161 | pane pane_0 Amateur Film: West 1940 |
| 12.5 WINDS PART | 9.4 | PASS | 0 | – | 1.61 | 14.8 | 27 | pane wall_4 B0Y SCOUTS--CAMP BRADY, ca. 1937 |

- **12.1** Weak: The hug is one arm from a jointed brother onto a card that cannot hug back; figures are small behind the plants (a 56 cm camera). Would help: A paired hug card; a hall plate with a higher camera. Staging notes: The hall's camera is low (56 cm): everyone stands far, beyond the planters, so their whole figures fit (y <= 609).
- **12.3** Weak: Short and clear; the vellum elders are generic extras with no faces of their own. Would help: Painted elder heads (lane B flags sixteen extras sharing one head). Staging notes: The elders of memory are lane B's elder_memory puppets drawn as vellum (cast.ghost); they fade at "rooms".
- **12.4** Weak: Hourglass props are small at this depth, and POET holds an orb rather than an hourglass. Would help: A POET card holding the hourglass. Staging notes: The burning hourglass is the painted 12.props.last-hourglass card (p23) held in each jointed hand as a prop card.
- **12.2** Weak: 23 s; the walk deeper is the only event. Set is not a place for "football". Would help: Group laughter cards; replacement mouths driven on the jointed friends. Staging notes: Reading order: "This is brotherhood ... all too familiar" is read here, after 12.4; the reel follows the reading.
- **12.5** Weak: No ball: the "football" is a lunge pose. They stand on the bottom step line, and the breakdown's parting is not staged. Would help: A ball prop card; a kick pair.

## 13 · How to Win My Heart

Reel: `renders/poem_13.mp4`

| scene | s | status | foot slide cm/f | contact % | scale % | bodies cm | card/travel warn f | joins (ARCHIVE) |
| :-- | --: | :-- | --: | --: | --: | --: | --: | :-- |
| 13.1 SMALL TABLES | 7.3 | PASS | 0 | – | 0 | 74.5 | 0 | pane wall_2 Wonderful World (Part III) |
| 13.2 COUNTED ORBITS | 16.3 | PASS | 0 | 0.029 | 0.41 | 8 | 47 | pane wall_0 VOYAGER II-Rendezvous With Saturn |
| 13.3 BURNED STORIES | 36.1 | PASS | 0 | – | 0.51 | 7.6 | 0 | pane wall_4 Ripley's Believe it or Not Museum - Gatlinburg, Tennessee; citizen  Berlin: Symphony of a Great City |
| 13.4 HARVESTED POWER | 13.2 | PASS | 0 | – | 0.3 | – | 0 | wipe haze_0 Golden Harvest...Fifty Years of Calpak Progress |
| 13.5 REFOCUS | 14.8 | PASS | 0 | – | 0.32 | 74.5 | 0 | pane wall_2 Out of This World |
| 13.6 WON'T LEAVE | 13.5 | PASS | 0 | – | 0.05 | – | 0 | pane wall_2 Moonwalk One, ca. 1970 |

- **13.1** Weak: A café made of cards on tidal flats under a storm: lane C marks this set "needs a plate". Table and POET do not share a real seat. Would help: The harbour café plate the dossier asks for. Staging notes: Lane C has no café plate (status "needs a plate"): the café is built on the tidal flats with the painted 13.props.cafe tables and chairs at their real heights.
- **13.2** Weak: Couples hold and sway but do not orbit; the jointed arms are thin at this size. Would help: A slow-dance pair card; an orbit goal (circle a shared point). Staging notes: Each couple holds by two reaches (hand to the partner's shoulder) and sways together; their overlap is an exempt touch beat.
- **13.3** Weak: 36 s on one quay, standing in a row; the fire is small and low beside a 700 px POET; the elders' purple suits are not robes. Would help: Three plates (pews, café at dusk, the fire), as the breakdown has; a burning-letters fire card; a kneeling elder group. Staging notes: The breakdown spans three sets (church pews, café at dusk, the quay fire); lane C gives 13.3 the quay, so the younger self and the elders stand on the quay as memory.
- **13.4** Weak: The field is pale canola, not scarlet poppies; figure stands over the flowers with no occlusion. Would help: A poppy plate, or poppy cards in a near plane. Staging notes: The plate's field is pale canola, not scarlet poppies: the poppies arrive as found film (asset wanted: a poppy-field plate or a poppy card).
- **13.5** Weak: SHE is a small front-only card with no window and no wave: the moment the poem turns on is the weakest beat. Would help: A distant-window set card (13.props.distant-window exists) with SHE in it; a working skirt rig or a wave card. Staging notes: SHE is the painted woman card (front stand only: lane B's skirt rig does not draw in the stager, so she has no wave), far across the flats; the couple sits at the second café table.
- **13.6** Weak: Same café; the smile is a raised hand, because there are no driven face cards. Would help: Face plug-ins (lane A has mouths and eyes) on the POET cards.

## 14 · Hot Minute

Reel: `renders/poem_14.mp4`

| scene | s | status | foot slide cm/f | contact % | scale % | bodies cm | card/travel warn f | joins (ARCHIVE) |
| :-- | --: | :-- | --: | --: | --: | --: | --: | :-- |
| 14.1 EVERYTHING I BUILT | 8.9 | PASS | 0 | – | 0.02 | – | 0 | pane wall_1 LOS ANGELES, ca. 1917 |
| 14.2 FROM THE GROUND UP | 23.2 | PASS | 0 | – | 0.02 | – | 0 | pane wall_1 Who's Out There? |
| 14.3 NO WALLS | 8.6 | PASS | 0 | – | 0.06 | – | 0 | wipe haze_0 Sports and Culture |
| 14.4 THE REEL | 20.9 | PASS | 0 | – | 1.19 | 287.9 | 0 | screen screen_0 Control Your Emotions; screen screen_1 Watershed wildfire |
| 14.5 TWO ENTWINED MUSES | 12.7 | PASS | 0 | – | 0.03 | 39.5 | 0 | wipe haze_0 Foundation Foods |
| 14.6 I CHOOSE THE DOOR | 11.6 | PASS | 0 | – | 0.23 | 30 | 0 | pane haze_0 Under Western Stars |

- **14.1** Weak: The words the breakdown gives are not in the reading, so this is a held wide over the pause; the haze is a code blur. Would help: Dissolve sheets from the plate's own layers (fall off plane by plane). Staging notes: No words: the reading pauses between poems 13 and 14 here, and the scene holds that pause (beats on seconds, not words).
- **14.2** Weak: 23 s of poses on the deck strip; the "from the ground up" dissolve is not built. Would help: The same dissolve; POET dissolving card.
- **14.3** Weak: Fine and plain; the found clip is a strong image over a figure that is much smaller. Would help: None needed.
- **14.4** Weak: Good TV joins; POET is small at the edge, b-roll extras are barely visible inside the screen. Would help: A real reel: the motif montage (window, tambourine, field, stars) the breakdown lists, as a clip list. Staging notes: Two b-roll extras walk inside the screen's street (tiny, at the plate's own scale); POET watches from the dark in front of it.
- **14.5** Weak: "Entwined" is two cards side by side, swaying on a whole-card rotation. Would help: A paired dance card of POET with his muse. Staging notes: The muse is POET's own cards in vellum (cast.ghost 0.6): two entwined muses, one man.
- **14.6** Weak: Reading gives 4 s of words; the rest is the walk. Guests stand outside the door because the opening is opaque, not in the party. Would help: A vintage party plate through the door; a door-opening animation (14.props.door has the states). Staging notes: The door is the painted 14.props.door card (p13, open, cream light) at 210 cm; the party is seen through it as found film, the guests as vellum.
