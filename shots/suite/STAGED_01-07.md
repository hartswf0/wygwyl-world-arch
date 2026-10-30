# Staged scenes, poems 01–07 (stage lane 1)

40 scenes, 10.9 minutes of reading, 40 pass every hard check measured on the render. 5 scenes have no puppet (the breakdown puts no body in them), so their checks have nothing to measure; say so rather than read those passes as evidence.

Every scene is built by `tools/stage_01_07.py` (compact spec) + `tools/stage_build.py` (windows, audio, walkable, archive strips, word anchors) and rendered by `node shots/suite/render.mjs <id>`.
Scene windows tile each poem's reading end to end (`tools/stage_windows.py`), so a poem's reel plays its reading through. Figure size always comes from lane C's horizon + px/cm: nothing is hand-scaled.

What the numbers do not say: `occlusion` is 0 by construction where lane C gives no footprint (it has none), so it only counts feet inside a footprint the scene authored; `off_frame` under-reads when no camera zoom is active (the mask is clipped to the frame); `scale_vs_set` skips air and sit frames, so a floating scene reports "no standing frames".

Reels: `renders/poem_NN.mp4` (`tools/stage_reels.py`).

New modules: `lib/set_patch.js` (scene-side walkable, marks, surface depths, plane re-seating), `lib/actions_extra.js` (drop, rise, float, tumble), `lib/fx_extra.js` (props that ride hands and fly; sweep, flash, rain, footprints, blinds, cracks, glow, iris, cobweb, stars, scatter, reticle), `lib/hands_extra.js` + `data/hand_cards.json` (replacement hand shapes).
Shared-file edits, all small: `index.html` (imports; applySetPatch after loadSet; applyExtras after compileScene; comp/set/cam on window.SUITE), `lib/adapters.js` (every lane-B character gets parts; pelvis/bridge cards; replacement hands), `lib/draw.js` (FX_EXTRA hook; lane-B pelvis card sized by its own px/cm), `lib/solver.js` (a held gesture is kept inside the arm), `lib/checks.js` (a vanished body re-plants where it reappears, so foot slide is not read across a vanish), `render.mjs` (protocolTimeout 30 min: long crowd scenes outlast the 3 min default).

## Scenes

| scene | movement | s | cast | beats / joins | status |
|---|---|---|---|---|---|
| 01.1 | THE SEARCH | 8.4 | POET, EX | 6 / 1 | PASS |
| 01.2 | MORE HAZE | 5.4 | POET, EX | 4 / 2 | PASS |
| 01.3 | THE FALL | 34.3 | POET, EX | 14 / 4 | PASS |
| 01.4 | AS DARK AS BLACK | 41.3 | POET, EX, GUEST_1, GUEST_2, GUEST_3 | 22 / 3 | PASS |
| 02.1 | SILENT SCREAM | 20.8 | POET, EX | 16 / 2 | PASS |
| 02.2 | THE MIRROR | 10.9 | POET | 8 / 1 | PASS |
| 02.3 | WE GO THROUGH | 14.8 | POET | 8 / 2 | PASS |
| 02.4 | THE GHOST WAS SEVEN | 16.9 | YOUNG_POET, GHOST_CHILD | 9 / 2 | PASS |
| 02.5 | BLINDS UP | 12.2 | YOUNG_POET | 6 / 2 | PASS |
| 02.6 | THROUGH THE WINDOW | 7.8 | YOUNG_POET, GHOST_CHILD | 7 / 1 | PASS |
| 03.1 | ODE TO FOREVER | 12.3 | — | 0 / 3 | PASS (no puppet: checks have no body to measure) |
| 03.2 | STILL WHOLE | 2.8 | — | 0 / 1 | PASS (no puppet: checks have no body to measure) |
| 03.3 | COBWEBS | 13.5 | — | 0 / 2 | PASS (no puppet: checks have no body to measure) |
| 03.4 | UNTIL NOTHING REMAINS | 20.9 | — | 0 / 3 | PASS (no puppet: checks have no body to measure) |
| 03.5 | TWO SETS OF FOOTSTEPS | 7.0 | POET, EX | 3 / 2 | PASS |
| 03.6 | SHATTERED | 6.7 | — | 0 / 1 | PASS (no puppet: checks have no body to measure) |
| 04.1 | WASHED ASHORE | 15.2 | POET | 7 / 2 | PASS |
| 04.2 | FOLDED WHISPERS | 31.5 | POET | 11 / 2 | PASS |
| 04.3 | MUSTARD SEEDS | 10.3 | POET | 4 / 2 | PASS |
| 04.4 | THEY TURN TO FACE ME | 16.6 | POET | 8 / 2 | PASS |
| 04.5 | DEEPEST DARKNESS | 9.3 | POET | 5 / 1 | PASS |
| 04.6 | I PUT THEM BACK ON | 49.5 | POET | 24 / 4 | PASS |
| 05.1 | NAME MY OWN STARS | 9.6 | POET, ANCESTOR_1, ANCESTOR_2, ANCESTOR_3, ANCESTOR_4, ANCESTOR_5, ANCESTOR_6 | 10 / 2 | PASS |
| 05.2 | SOUTHERN PINE | 19.3 | POET | 7 / 4 | PASS |
| 05.3 | A NEW UNIVERSE | 13.5 | POET, ANCESTOR_1, ANCESTOR_2, ANCESTOR_4, ANCESTOR_7, ANCESTOR_8 | 9 / 2 | PASS |
| 05.4 | BEWARE OF ME | 32.3 | POET, ANCESTOR_1, ANCESTOR_5, ANCESTOR_6, ANCESTOR_9 | 12 / 3 | PASS |
| 05.5 | THE GATES OPEN | 9.4 | POET, ANCESTOR_1, ANCESTOR_2 | 8 / 2 | PASS |
| 06.1 | THE COMETS | 28.2 | POET, ELDER_1, CROWD_1, CROWD_2 | 6 / 3 | PASS |
| 06.2 | THE WATERLINE FALLS | 11.8 | POET, CROWD_1, CROWD_3 | 8 / 2 | PASS |
| 06.3 | ADMISSION | 29.8 | GATEKEEPER_1, POET, CROWD_2, CROWD_3, CROWD_4, CROWD_5, CROWD_6 | 15 / 3 | PASS |
| 06.4 | NARROW STREETS | 13.8 | POET, CROWD_7, CROWD_8, MUSICIAN_1 | 7 / 3 | PASS |
| 06.5 | CROSSHAIRS TO CONTINUUMS | 10.5 | POET, CROWD_3, CROWD_7 | 6 / 2 | PASS |
| 06.6 | WELCOMING ALL | 8.1 | POET, CROWD_1, CROWD_3, CROWD_7, ELDER_1, GUEST_1 | 18 / 1 | PASS |
| 07.1 | CHIN NESTED | 8.7 | POET, DJ, GUEST_1, GUEST_2 | 7 / 1 | PASS |
| 07.2 | VINEYARD GHOSTS | 13.8 | POET, EX, GUEST_3, GUEST_4 | 7 / 1 | PASS |
| 07.3 | THOUSAND LIGHT YEARS | 19.4 | POET, DJ, GUEST_1, GUEST_5 | 6 / 2 | PASS |
| 07.4 | DIVERGING RINGS | 16.8 | POET, GUEST_2, GUEST_6 | 6 / 2 | PASS |
| 07.5 | ELEVEN PETALS | 10.4 | POET, GUEST_3, GUEST_4 | 5 / 2 | PASS |
| 07.6 | THREE ROADS | 10.2 | POET, DJ | 5 / 3 | PASS |
| 07.7 | CHIN HIGH | 21.4 | POET, DJ, GUEST_1, GUEST_5 | 11 / 2 | PASS |

## Per scene

### 01.1 · THE SEARCH (8.4 s, suite 28.81–37.24)
- **Status:** PASS. Set: bedroom_highrise (lane C 01.1).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 0.13 % · occlusion 0 f · bodies 254 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on screen_3 @ world,: [San Francisco General Strike] (Part II) (1934).
- **Weak:** POET and EX read well; the "TV" is a dark framed picture carrying archive; reading gesture is one held page.
- **Would help:** CRT card with an open screen; head cards for "sad, reading".

### 01.2 · MORE HAZE (5.4 s, suite 37.24–42.62)
- **Status:** PASS. Set: bedroom_highrise (lane C 01.2).
- **Checks:** foot slide 0 cm/f · reach 0.82 · contact 0.007 % · scale 1.23 % · occlusion 0 f · bodies 179.5 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on pane_2 @ hallways,: Alice In Wonderland (1915); touch on pane_0 @ fire: Under Western Stars (None).
- **Weak:** EX is now outside the glass on a code-drawn landing; his retreat is small because the landing is shallow; the window never truly "slides away".
- **Would help:** A bedroom plate with a real fire escape (lane C flags it); true dolly-zoom planes.

### 01.3 · THE FALL (34.3 s, suite 42.62–76.91)
- **Status:** PASS. Set: city_fall_void (lane C 01.3).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 0 % · occlusion 0 f · bodies 538.4 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on haze_2 @ maze: Berlin: Symphony of a Great City (None); screen on wall_0 @ forest: Foggy Mountain Morning (Wide Screen) (2007); citizen on stage @ having: Beginning to Date (1953); screen on haze_2 @ failed: Alcohol and the Human Body (1949).
- **Weak:** A 34 s fall on one aerial plate: bodies float, drop and roll, no streaking floors; the jointed tee tumbles stiff. Scale check has no standing frames (air).
- **Would help:** POET falling/tumbling replacement bodies; a city-streak layer; escape-screen bezels.

### 01.4 · AS DARK AS BLACK (41.3 s, suite 76.91–118.22)
- **Status:** PASS. Set: vintage_party (lane C 01.4).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 1.85 % · occlusion 0 f · bodies 484.8 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on pane_1 @ spectrum: His Royal Highness - Rare Australian Trailer (1932); screen on screen_2 @ photographs,: Colaci Home Movies: Family 1952-1956 (Part I) (1952); screen on pane_0 @ With: Under Western Stars (None).
- **Weak:** "Needs a plate": a chapel with a giant drum stands in for the ballroom; figures only ~210 px, so the camera is zoomed 1.65-1.9x onto a floor strip. No hole in the floor.
- **Would help:** A figure-free ballroom plate with parquet; floor-hole card; grey-painted party dancers.

### 02.1 · SILENT SCREAM (20.8 s, suite 126.64–147.44)
- **Status:** PASS. Set: black_void (lane C 02.1).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 0 % · occlusion 0 f · bodies 737.4 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** wipe on haze_0 @ walls: San Francisco Earthquake Aftermath, Part 1 (1906); citizen on stage @ solitude: Coney Island - Boardwalk Crowd (Standard 4:3) (1940).
- **Weak:** Works as a void; arms-up scream is one held pose; rings are small code cards. Scale check has no standing frames (float).
- **Would help:** Scream head card; ring prop cards.

### 02.2 · THE MIRROR (10.9 s, suite 147.44–158.32)
- **Status:** PASS. Set: bedroom_night (lane C 02.2).
- **Checks:** foot slide 0 cm/f · reach 0.614 · contact 0.032 % · scale 0.47 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** touch on pane_0 @ midnight.: Speech: Platform Posture and Appearance (1949).
- **Weak:** The window stands in for the mirror (no mirror surface in this plate); he sits on the bed edge rather than tossing in bed.
- **Would help:** A bedroom plate with a mirror; lying/tossing replacement bodies.

### 02.3 · WE GO THROUGH (14.8 s, suite 158.32–173.09)
- **Status:** PASS. Set: black_void (lane C 02.3).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 0.37 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** wipe on haze_0 @ road: Dusk to Dawn (1971); screen on haze_0 @ dilated: Eyes and Their Care (An Introduction), The (1941).
- **Weak:** The pupil push-through is an iris to black, not an eye; POET just stands in the void with two wipes.
- **Would help:** An eye-macro plate and a real pupil dissolve.

### 02.4 · THE GHOST WAS SEVEN (16.9 s, suite 173.09–189.94)
- **Status:** PASS. Set: living_room_1990s (lane C 02.4).
- **Checks:** foot slide 0 cm/f · reach 0.983 · contact 0.017 % · scale 0.29 % · occlusion 0 f · bodies 10.9 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on pane_1 @ parents: Family Life (1949); screen on pane_0 @ winter: Winter in Den haag / IJs in Den Haag (1922).
- **Weak:** Lane C uses the high-rise bedroom as the 1990s living room; no car, no door-post height marks; both children wear a borrowed head.
- **Would help:** A 1990s living-room plate, the driveway view, painted child and ghost heads.

### 02.5 · BLINDS UP (12.2 s, suite 189.94–202.18)
- **Status:** PASS. Set: living_room_1990s (lane C 02.5).
- **Checks:** foot slide 0 cm/f · reach 0.766 · contact 0.018 % · scale 0.35 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on pane_1 @ see: Dusk to Dawn (1971); screen on pane_1 @ whispering: Have I Told You Lately That I Love You? (1958).
- **Weak:** Blind slats are code-drawn; the amber hazard light is a sweep; the boy barely moves.
- **Would help:** Blind/curtain card rig; the driveway plate through the window.

### 02.6 · THROUGH THE WINDOW (7.8 s, suite 202.18–209.99)
- **Status:** PASS. Set: living_room_1990s (lane C 02.6).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact 0.011 % · scale 0.7 % · occlusion 0 f · bodies 27.5 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on pane_0 @ old: Destruction: Fun or Dumb? (None).
- **Weak:** Reads well: hand-off, wind-up, throw, cracks, black. Cracks are code lines, tambourine is a code card; the wind-up is one held arm.
- **Would help:** Tambourine prop card; a pane-shatter card set.

### 03.1 · ODE TO FOREVER (12.3 s, suite 218.97–231.28)
- **Status:** PASS (no puppet: checks have no body to measure). Set: chapel_interior (lane C 03.1).
- **Checks:** foot slide 0 cm/f · reach 0 · contact — % · scale 0 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on screen_2 @ tambourine: Sound Waves And Their Sources (1933); screen on pane_0 @ choir: Something to Sing About (1937); screen on pane_1 @ prayer: De graal pinksterzegen (1932).
- **Weak:** No puppet (breakdown): the tambourine crosses a chapel dominated by the plate's giant drum. Checks have nothing to measure.
- **Would help:** A figure-free chapel without the drum: choir stands, prayer lines.

### 03.2 · STILL WHOLE (2.8 s, suite 231.28–234.10)
- **Status:** PASS (no puppet: checks have no body to measure). Set: chapel_interior (lane C 03.2).
- **Checks:** foot slide 0 cm/f · reach 0 · contact — % · scale 0 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on pane_1 @ abandoned: Aqua Frolics (None).
- **Weak:** 2.8 s: tambourine enters and hangs; the time-lapse is a light sweep only.
- **Would help:** Rose-window pass-through card; baptism-pool plate.

### 03.3 · COBWEBS (13.5 s, suite 234.10–247.63)
- **Status:** PASS (no puppet: checks have no body to measure). Set: chapel_interior (lane C 03.3).
- **Checks:** foot slide 0 cm/f · reach 0 · contact — % · scale 0 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on screen_2 @ cobwebs,: Spider Engineers (1956); screen on pane_0 @ gift: Pathe News Christmas with Their Cameramen and Crews 'Round the World (1950).
- **Weak:** Decay is code cobwebs + darkening on one state of the chapel; the gift boxes are only archive.
- **Would help:** Three time-lapse states of the chapel; gift-box cards.

### 03.4 · UNTIL NOTHING REMAINS (20.9 s, suite 247.63–268.56)
- **Status:** PASS (no puppet: checks have no body to measure). Set: chapel_storm (lane C 03.4).
- **Checks:** foot slide 0 cm/f · reach 0 · contact — % · scale 0 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on haze_1 @ thunders,: Lightning (1950); screen on wall_0 @ broken: Shock Troops of Disaster: The Story of the New England Hurricane (1938); screen on wall_0 @ breads: Rain Off Barn Roof (Wide Screen) (2007).
- **Weak:** Storm reads (flashes, rain, archive), but no gift/bread/string inserts; no puppet to measure.
- **Would help:** Broken-gift, bread, marionette-string prop cards.

### 03.5 · TWO SETS OF FOOTSTEPS (7.0 s, suite 268.56–275.60)
- **Status:** PASS. Set: remnants_shore (lane C 03.5).
- **Checks:** foot slide 0 cm/f · reach 0 · contact — % · scale 0.06 % · occlusion 0 f · bodies 27.8 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on water_0 @ blankets: Gulliver's Travels (1939); screen on water_0 @ footsteps,: Robinson Crusoe C (1927).
- **Weak:** Good: two backs walking away; the footprints are small code marks and not read from the soles.
- **Would help:** Footprint cards; a chapel-remnants plate (this plate's chapel is whole).

### 03.6 · SHATTERED (6.7 s, suite 275.60–282.29)
- **Status:** PASS (no puppet: checks have no body to measure). Set: remnants_shore (lane C 03.6).
- **Checks:** foot slide 0 cm/f · reach 0 · contact — % · scale 0 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on water_0 @ shattered: Explosives - Tool for Progress (1970).
- **Weak:** The shatter is code shards fading out; pieces do not remain for 04.
- **Would help:** Tambourine pieces card set that stays on the shore.

### 04.1 · WASHED ASHORE (15.2 s, suite 290.52–305.69)
- **Status:** PASS. Set: shore_night (lane C 04.1).
- **Checks:** foot slide 0 cm/f · reach 0.822 · contact — % · scale 2.36 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on water_1 @ ashes: Watershed wildfire (1958); screen on water_1 @ lift: Wonder of Water (1958).
- **Weak:** Low camera (53 cm): POET must keep to a far shore strip; hands at the hips stand in for pockets; ravens are code silhouettes.
- **Would help:** Hands-in-pockets torso/arm cards; raven cards; the hollow-chest card (04.1c).

### 04.2 · FOLDED WHISPERS (31.5 s, suite 305.69–337.22)
- **Status:** PASS. Set: shore_night (lane C 04.2).
- **Checks:** foot slide 0 cm/f · reach 0.822 · contact — % · scale 0.86 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on water_1 @ waves: Safe In Port (None); screen on water_1 @ sad: Living Stereo (1958).
- **Weak:** Reads well; kneel is a deep squat; the heart is small and code-drawn; 31 s on one set is long for one gesture line.
- **Would help:** Heart prop card with a beat cycle; kneeling replacement body.

### 04.3 · MUSTARD SEEDS (10.3 s, suite 337.22–347.52)
- **Status:** PASS. Set: night_garden_field (lane C 04.3).
- **Checks:** foot slide 0 cm/f · reach 0.822 · contact — % · scale 0.22 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on haze_0 @ puzzle: Master Hands (None); screen on haze_0 @ mustard: Victory Gardens (None).
- **Weak:** Back-view walk into the field works; the puzzle pieces are only archive; no incline trail set.
- **Would help:** Puzzle-piece cards; an incline-trail plate.

### 04.4 · THEY TURN TO FACE ME (16.6 s, suite 347.52–364.14)
- **Status:** PASS. Set: night_garden_field (lane C 04.4).
- **Checks:** foot slide 0 cm/f · reach 0.822 · contact — % · scale 2.04 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on haze_0 @ golden: Spring Comes to a Pond (1952); screen on haze_0 @ memories: They Grow Up So Fast (1956).
- **Weak:** The plants do not actually turn; a glow stands in.
- **Would help:** Plant/flower cards that turn their faces; weed cards.

### 04.5 · DEEPEST DARKNESS (9.3 s, suite 364.14–373.42)
- **Status:** PASS. Set: field_dark (lane C 04.5).
- **Checks:** foot slide 0 cm/f · reach 0.822 · contact — % · scale 0.27 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on haze_0 @ clouds: Cloud Hides Moon (Standard 4:3) (2007).
- **Weak:** Very dark by design; the hands on the ground are placeholder code cards.
- **Would help:** Hand-on-ground cards; empty-sleeve arm cards (04.5c).

### 04.6 · I PUT THEM BACK ON (49.5 s, suite 373.42–422.91)
- **Status:** PASS. Set: field_dark (lane C 04.6).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact 0.028 % · scale 1.1 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on haze_0 @ Hands: Master Hands (Part IV) (1936); screen on haze_0 @ world: Mirror of America (1963); screen on haze_0 @ alright.: Vivid Sunrise 2 (2007); screen on haze_0 @ tree: Night Tree (2006).
- **Weak:** 50 s on one set; the hands-back-on beat is a reach plus a code card riding up; the puppet shows his own hands throughout.
- **Would help:** Handless forearm cards and hand-seating cards; a second field plate for the long reflection.

### 05.1 · NAME MY OWN STARS (9.6 s, suite 433.01–442.62)
- **Status:** PASS. Set: night_field_parade (lane C 05.1).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact 0.015 % · scale 0.5 % · occlusion 0 f · bodies 1.1 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on haze_0 @ inherit: Fighter for Freedom: The Frederick Douglass Story (1984); screen on haze_0 @ galaxies: Heavenly Bodies (None).
- **Weak:** The parade reads, ancestors walk in and face POET; names on stars (05.1c) not staged; star is a code card.
- **Would help:** Star prop cards and a name-typing fx; lantern cards.

### 05.2 · SOUTHERN PINE (19.3 s, suite 442.62–461.90)
- **Status:** PASS. Set: humid_basement (lane C 05.2).
- **Checks:** foot slide 0 cm/f · reach 0 · contact — % · scale 1.96 % · occlusion 0 f · bodies — cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_2 @ shared: Inner City, The (1958); screen on wall_1 @ wood: Trees to Tribunes (1937); screen on wall_2 @ mattress: Sleep for Health (1950); screen on wall_4 @ dream: Sun Emerges (2006).
- **Weak:** "Needs a plate": a flooded underpass stands in for the basement; he sits, cannot lie; the mattress is a code slab.
- **Would help:** A basement-bedroom plate with joists; lying replacement body; mattress card.

### 05.3 · A NEW UNIVERSE (13.5 s, suite 461.90–475.41)
- **Status:** PASS. Set: night_field_parade (lane C 05.3).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact 0.027 % · scale 0.41 % · occlusion 0 f · bodies 14.5 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on haze_0 @ universe,: Four in the Cosmos (1969); screen on haze_0 @ miracles: VOYAGER II-Rendezvous With Saturn (1986).
- **Weak:** Works; the universe is a code orb; blessings on nodes are not staged.
- **Would help:** Universe sphere card; web-of-light fx.

### 05.4 · BEWARE OF ME (32.3 s, suite 475.41–507.69)
- **Status:** PASS. Set: night_field_parade (lane C 05.4).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact 0.041 % · scale 0.77 % · occlusion 0 f · bodies -12.6 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on haze_0 @ history: Kentucky Pioneers (1941); screen on haze_0 @ blood: Labor of Thy Hands (None); screen on haze_0 @ baritone: Sound And The Story (1956).
- **Weak:** The chain of hands on shoulders works and is measured, but stays static for 32 s; the insert on the palm (05.4a) is not staged.
- **Would help:** Palm-insert plate; fingerprint/vein light card; a second blocking for the middle.

### 05.5 · THE GATES OPEN (9.4 s, suite 507.69–517.08)
- **Status:** PASS. Set: winged_marble_gate (lane C 05.5).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 0.24 % · occlusion 0 f · bodies 21.2 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** wipe on door_1 @ 2.2: A Poem in Marble, A Place on the Map: Byron R. White U.S. Courthouse, Denver, CO (2007); screen on pane_0 @ 4: World's Fair Night Aerials (None).
- **Weak:** "Needs a plate": a neon alley with a red door stands in for the winged marble gate; no words in this window.
- **Would help:** A winged marble gate plate (the dossier names it; lane C has none).

### 06.1 · THE COMETS (28.2 s, suite 517.08–545.28)
- **Status:** PASS. Set: causeway_road (lane C 06.1).
- **Checks:** foot slide 0 cm/f · reach 0 · contact — % · scale 0.3 % · occlusion 0 f · bodies 31.3 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on haze_5 @ hymns: Back of the Mike (1938); screen on wall_1 @ yellow: American Road, The (Part III) (None); screen on haze_5 @ comets: Excursion to the Moon (1908).
- **Weak:** The plate has no causeway: travellers walk on water; comet and soul-light are code cards.
- **Would help:** A causeway plate; comet card; yellow-brick road.

### 06.2 · THE WATERLINE FALLS (11.8 s, suite 545.28–557.07)
- **Status:** PASS. Set: atlantis_waterfront (lane C 06.2).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 0.27 % · occlusion 0 f · bodies 116.2 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_1 @ Atlantis.: World of Tomorrow, The (Part I) (None); screen on water_0 @ pack: Zuyderzee works (1930).
- **Weak:** The waterline does not actually fall (one plate); only the people move.
- **Would help:** Two plates (flooded / risen) or a waterline wipe plate.

### 06.3 · ADMISSION (29.8 s, suite 557.07–586.91)
- **Status:** PASS. Set: atlantis_gate (lane C 06.3).
- **Checks:** foot slide 0 cm/f · reach 0.902 · contact 0.021 % · scale 0.43 % · occlusion 0 f · bodies 0.9 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on door_1 @ currency: Banks And Credits (1948); wipe on door_1 @ safe.: Gift of Green (1946); screen on pane_0 @ candlelight: Coffee House Rendezvous (Part I) (1969).
- **Weak:** Queue and coin hand-offs work; the booth is implied, the door doubles as gate; crowd is shared-head citizens.
- **Would help:** Booth card; lantern-window faces; painted citizen heads.

### 06.4 · NARROW STREETS (13.8 s, suite 586.91–600.66)
- **Status:** PASS. Set: narrow_streets (lane C 06.4).
- **Checks:** foot slide 0 cm/f · reach 0.817 · contact — % · scale 1.19 % · occlusion 0 f · bodies 3.8 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on door_0 @ shadows: Third Avenue El (None); screen on door_0 @ joyful: Coney Island At Night (Standard 4:3) (1940); screen on door_0 @ clouds: Moon And Cloud 3 (Wide Screen 16:9) (2007).
- **Weak:** Walk and rainbow sweeps read; door panes are mostly hidden by the plate's dark foreground.
- **Would help:** A real musician card; a narrow-street plate with a clear wall for the archive.

### 06.5 · CROSSHAIRS TO CONTINUUMS (10.5 s, suite 600.66–611.20)
- **Status:** PASS. Set: atlantis_plaza (lane C 06.5).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 2.32 % · occlusion 0 f · bodies 455.8 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_1 @ crosshairs: Space Navigation (1967); screen on water_0 @ serendipity.: Sun Peeks Outs From Behind Clouds (2007).
- **Weak:** The reticle is a code overlay; lane C has no plaza plate, the waterfront stands in.
- **Would help:** A plaza plate; a real scope-reticle card.

### 06.6 · WELCOMING ALL (8.1 s, suite 611.20–619.27)
- **Status:** PASS. Set: atlantis_plaza (lane C 06.6).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 1.66 % · occlusion 0 f · bodies 89.5 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_1 @ city: World's Fair Night Aerials (None).
- **Weak:** The final arms-up reads; the plate is the waterfront again; wandering to the house (06.6c-d) not staged.
- **Would help:** A plaza plate and a house-exterior set.

### 07.1 · CHIN NESTED (8.7 s, suite 627.31–636.05)
- **Status:** PASS. Set: house_party (lane C 07.1).
- **Checks:** foot slide 0 cm/f · reach 0.816 · contact — % · scale 0.63 % · occlusion 0 f · bodies 10.6 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_0 @ turn: [Chevrolet Sales Convention Musical] (1954).
- **Weak:** DJ drops in small and far; no booth or decks in the plate.
- **Would help:** A DJ booth card with decks; a bar card for POET.

### 07.2 · VINEYARD GHOSTS (13.8 s, suite 636.05–649.83)
- **Status:** PASS. Set: house_party (lane C 07.2).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 0.27 % · occlusion 0 f · bodies 55.5 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_0 @ ghosts: Golden Harvest...Fifty Years of Calpak Progress (1950).
- **Weak:** Ghost EX reads as a translucent back; the vineyard is archive on the wall; guests only lean by a held hand.
- **Would help:** A couch card; vineyard plate for the projection.

### 07.3 · THOUSAND LIGHT YEARS (19.4 s, suite 649.83–669.20)
- **Status:** PASS. Set: house_party (lane C 07.3).
- **Checks:** foot slide 0 cm/f · reach 0.653 · contact 0 % · scale 2.42 % · occlusion 0 f · bodies 43.1 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_0 @ stars: Moonwalk One, ca. 1970 (1970); screen on wall_0 @ thousand: Who's Out There? (1975).
- **Weak:** POET's walk and the parting crowd work (keep_distance); only two guests means no "packed" room.
- **Would help:** More party guests / a crowd layer; ceiling LED stars plate.

### 07.4 · DIVERGING RINGS (16.8 s, suite 669.20–686.04)
- **Status:** PASS. Set: house_party (lane C 07.4).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 0.47 % · occlusion 0 f · bodies 159.6 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_0 @ shared: Transportation: Bus, Truck, and Taxi (1946); screen on wall_0 @ u: Show 'Em the Road (Part II) (1954).
- **Weak:** Rings on the wall read; hands-apart gesture is two held arms.
- **Would help:** Wedding-band cards; truck cards.

### 07.5 · ELEVEN PETALS (10.4 s, suite 686.04–696.43)
- **Status:** PASS. Set: house_party (lane C 07.5).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 1.75 % · occlusion 0 f · bodies 124.1 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_0 @ daisy: Spring Comes to a Pond (1952); screen on wall_0 @ future: They Grow Up So Fast (1956).
- **Weak:** No daisy head is drawn: petals only; a lighter is only a glow.
- **Would help:** Daisy prop card with separate petals; lighter card.

### 07.6 · THREE ROADS (10.2 s, suite 696.43–706.60)
- **Status:** PASS. Set: house_party (lane C 07.6).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 0.47 % · occlusion 0 f · bodies 511.6 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_0a @ rain: Rain On Budded Tree (2007); screen on wall_0b @ fog: Low-Lying Fog (Wide Screen) (2007); screen on wall_0c @ lights: Small Town Intersection With Stoplight - Early Morning (Wide Screen) (2007).
- **Weak:** Three panels on the wall work; pointing is a held arm (the point hand card is not selected by this gesture).
- **Would help:** A pointing arm pose; a stronger DJ headphone card.

### 07.7 · CHIN HIGH (21.4 s, suite 706.60–727.95)
- **Status:** PASS. Set: house_party (lane C 07.7).
- **Checks:** foot slide 0 cm/f · reach 0.97 · contact — % · scale 0.47 % · occlusion 0 f · bodies 159.6 cm · ground 0 f · off-frame 0 f · word sync 0 off.
- **Joins:** screen on wall_0 @ open: Walk In - Coming Soon - Theater Audience (None); screen on wall_0 @ volume: Coney Island At Night (Standard 4:3) (1940).
- **Weak:** Erupting room is three figures; strobe sells it more than the crowd.
- **Would help:** A crowd layer of hands; phone/lighter cards.
