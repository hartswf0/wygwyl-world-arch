# Cut fixes (fix_cut.py)

Post-pass over the cutter output. No part was renamed or moved; ids and file paths are unchanged.
Each changed part keeps its cutter values under `orig`; the first version of every re-cut image is in `cut/_orig/`.

Before (cutter first pass): 365 sheets, 5042 parts, 12 sheets with no parts, 781 parts with an empty or
garbled label (no 3-letter word and not a code like W06), 0 parts marked as references.
The 12 empty sheets were then cut box by box by cutter.py (rescue): +220 parts.

Totals now: {"sheets": 365, "parts": 5731, "working": 5407, "refs": 324, "unlabeled": 345, "empty_sheets": 0, "added_by_fix": 469, "recut_by_fix": 197}

Kinds of fix (a part may have several):
- `split`: a card that was a ruled box holding several cards -> kind `ref` (ref_reason "section box"), its contents added as new parts (`added: true`, `split_from`).
- `recut`: a framed cell holding one figure -> the same file re-cut to the figure (frame, printed label and paper dropped).
- `unclip`: a rectangular bite the cutter took out of a card (a word box removed before finding cards) filled back in.
- `grabcut`: tried on every pale card; the flood edge already sits on stronger contrast than GrabCut finds, so none are accepted.
- `label`: label re-read/re-assigned (old value under `orig.label`).
- `ref`: kind set to `ref` (`ref_reason` says why); planners should skip these.

## Per sheet

### 01.fx.haze-words
- label: 01.fx.haze-words/part-10: '' -> 'w04' (was empty/garbled)
- label: 01.fx.haze-words/w07-2: 'W07' -> 'W15' (old text not on the sheet; label 6px-cost away)

### 01.hero.catwalk
- label: 01.hero.catwalk/platform-end-platform-end: 'PLATFORM.END platform end' -> 'PLATFORM.END end platform (side elevation)' (re-read, more complete)

### 01.hero.severn
- label: 01.hero.severn/07-hall-4-corridor-frame-4: '07 HALL.4 corridor frame 4' -> '07 HALL.4 corridor frame 4 (smallest opening)' (closer label (cost 12 vs 1000000000); old text is 05-hall-2-corridor-frame-2's)

### 01.hero.severnescape
- label: 01.hero.severnescape/left-lightwell-wall: 'left lightwell wall' -> 'WALL.L L left lightwell wall' (re-read, more complete)
- label: 01.hero.severnescape/right-lightwell-wall: 'right lightwell wall' -> 'WALL.R right lightwell wall' (re-read, more complete)
- label: 01.hero.severnescape/part-4: '' -> 'TREAD.O1' (was empty/garbled)
- label: 01.hero.severnescape/part-8: '' -> 'TREAD.O3' (was empty/garbled)
- label: 01.hero.severnescape/planter-o3-planter-o4: 'PLANTER.O3 PLANTER.O4' -> 'TREAD.04' (closer label (cost 1 vs 266); old text is planter-o3's)
- label: 01.hero.severnescape/planter-o5-planter-o6: 'PLANTER.O5 PLANTER.O6' -> 'TREAD' (closer label (cost 11 vs 263); old text is planter-o5's)
- label: 01.hero.severnescape/and-distant-catwalk: 'and distant catwalk' -> 'PLANTER.O6' (closer label (cost 33 vs 65))

### 01.props.chandeliers
- label: 01.props.chandeliers/part-1: '' -> 'CHAIN H1' (was empty/garbled)
- label: 01.props.chandeliers/candle: 'CANDLE' -> 'ARM Al' (closer label (cost 15 vs 23); old text is flame's)
- label: 01.props.chandeliers/candle-2: 'CANDLE' -> 'ARM A2' (closer label (cost 12 vs 1000000000); old text is flame's)
- label: 01.props.chandeliers/candle-3: 'CANDLE' -> 'ARM A3' (closer label (cost 9 vs 1000000000); old text is flame's)
- label: 01.props.chandeliers/candle-c4: 'CANDLE C4' -> 'ARM A4' (closer label (cost 14 vs 1000000000); old text is flame-l2's)
- label: 01.props.chandeliers/candle-4: 'CANDLE' -> 'ARM' (closer label (cost 37 vs 1000000000); old text is flame's)
- label: 01.props.chandeliers/flame-l2: 'FLAME L2' -> 'CANDLE c2' (closer label (cost 13 vs 23); old text is crystal-2's)
- label: 01.props.chandeliers/flame-l3: 'FLAME L3' -> 'CANDLE c3' (closer label (cost 13 vs 23); old text is crystal-3's)
- label: 01.props.chandeliers/flame-ls: 'FLAME LS' -> 'CANDLE c5' (closer label (cost 13 vs 25); old text is crystal-4's)
- label: 01.props.chandeliers/lame-l6: 'LAME L6' -> 'CANDLE C6' (closer label (cost 13 vs 25); old text is crystal-5's)
- label: 01.props.chandeliers/crystal: 'CRYSTAL' -> 'FLAME Li' (closer label (cost 14 vs 1000000000); old text is crystal-8's)
- label: 01.props.chandeliers/crystal-2: 'CRYSTAL' -> 'FLAME L2' (closer label (cost 14 vs 1000000000); old text is crystal-8's)
- label: 01.props.chandeliers/crystal-4: 'CRYSTAL' -> 'FLAME L5' (closer label (cost 16 vs 1000000000); old text is crystal-8's)
- label: 01.props.chandeliers/crystal-5: 'CRYSTAL' -> 'FLAME L6' (closer label (cost 15 vs 1000000000); old text is crystal-8's)
- label: 01.props.chandeliers/crystal-6: 'CRYSTAL' -> 'CRYSTAL P1' (closer label (cost 13 vs 1000000000); old text is crystal-8's)
- label: 01.props.chandeliers/crystal-7: 'CRYSTAL' -> 'CRYSTAL P2' (closer label (cost 14 vs 1000000000); old text is crystal-8's)
- label: 01.props.chandeliers/part-24: '' -> 'CRYSTAL' (was empty/garbled)
- label: 01.props.chandeliers/crystal-10: 'CRYSTAL' -> 'CRYSTAL P6' (closer label (cost 14 vs 1000000000); old text is crystal-8's)

### 01.props.handheld
- label: 01.props.handheld/poem-paper: 'POEM PAPER' -> 'POEM PAPER FLAT' (re-read, more complete)
- label: 01.props.handheld/poem-paper-2: 'POEM PAPER' -> 'POEM PAPER CRUMPLED' (closer label (cost 42 vs 1000000000); old text is poem-paper's)
- label: 01.props.handheld/folded-paper: 'FOLDED PAPER' -> 'FOLDED PAPER EDGE (PLAIN)' (re-read, more complete)

### 01.props.room
- label: 01.props.room/television-frame: 'TELEVISION FRAME' -> 'BOX 1' (closer label (cost 26 vs 103); old text is television-pedestal-stand's)
- label: 01.props.room/television-pedestal: 'TELEVISION PEDESTAL' -> 'BOX 3' (closer label (cost 25 vs 141); old text is television-pedestal-stand-2's)
- label: 01.props.room/open: 'OPEN' -> 'DRESSER OPEN' (re-read, more complete)
- label: 01.props.room/tv-with-screen-feed: 'TV WITH SCREEN (FEED)' -> '(PARTY) TV WITH SCREEN (FEED)' (re-read, more complete)
- ref: 01.props.room/part-1: label fragment (printed words)
- ref: 01.props.room/only-assembled: label says 'assembled'
- ref: 01.props.room/dresser-closed: under the band heading 'REFERENCE ONLY'
- ref: 01.props.room/open: under the band heading 'REFERENCE ONLY'
- ref: 01.props.room/part-16: under the band heading 'REFERENCE ONLY'
- ref: 01.props.room/tv-with-screen-pills: under the band heading 'REFERENCE ONLY'
- ref: 01.props.room/tv-with-screen-party: under the band heading 'REFERENCE ONLY'
- ref: 01.props.room/tv-with-screen-feed: under the band heading 'REFERENCE ONLY'
- ref: 01.props.room/tv-with-screen-static: under the band heading 'REFERENCE ONLY'
- ref: 01.props.room/tv-with-screen-black-01-props-room: under the band heading 'REFERENCE ONLY'

### 01.props.trapdoor
- label: 01.props.trapdoor/tabs-2: 'TABS (2)' -> 'HINGE TABS (2)' (re-read, more complete)
- label: 01.props.trapdoor/void-backing-card: 'VOID BACKING CARD' -> 'VOID BACKING CARD BLACK' (re-read, more complete)
- ref: 01.props.trapdoor/backing: label fragment (printed words)

### 01.set.city_fall_void
- label: 01.set.city_fall_void/black-blue-backing: 'black-blue backing' -> 'VOID.61 black-blue backing' (re-read, more complete)
- label: 01.set.city_fall_void/facade-strip-a: 'facade strip A' -> 'TOWER facade strip A' (closer label (cost 6 vs 1000000000); old text is facade-strip-e's)
- label: 01.set.city_fall_void/facade-strip-c: 'facade strip C' -> 'TOWER.03 facade strip C' (closer label (cost 4 vs 1000000000); old text is facade-strip-e's)
- label: 01.set.city_fall_void/facade-strip-d: 'facade strip D' -> 'TOWER a4 facade strip' (closer label (cost 4 vs 1000000000); old text is facade-strip-e's)
- ref: 01.set.city_fall_void/part-3: label fragment (printed words)
- ref: 01.set.city_fall_void/part-5: label fragment (printed words)
- ref: 01.set.city_fall_void/part-6: label fragment (printed words)

### 02.fx.lights-iris
- label: 02.fx.lights-iris/sweep-light: 'SWEEP LIGHT' -> 'LIGHT SWEEP WHITE' (old text not on the sheet; label 30px-cost away)
- label: 02.fx.lights-iris/light: 'LIGHT' -> 'LIGHT SWEEP AMBER' (closer label (cost 25 vs 303); old text is part-4's)
- label: 02.fx.lights-iris/part-4: '' -> 'LIGHT SWEEP' (was empty/garbled)
- label: 02.fx.lights-iris/amber-light-sweep-red: 'AMBER LIGHT SWEEP RED' -> 'RIGHT CAVE (WALL CARD)' (closer label (cost 2 vs 72); old text is part-4's)
- label: 02.fx.lights-iris/part-11: '' -> 'IRIS' (was empty/garbled)

### 02.hero.childhouse
- split: 02.hero.childhouse/glass-03-09 (209x132) -> 2 parts
- label: 02.hero.childhouse/part-3: '' -> '03 CORNICE' (was empty/garbled)
- label: 02.hero.childhouse/10-shard: '10 SHARD' -> 'GLASS.03' (closer label (cost 40 vs 1000000000))
- label: 02.hero.childhouse/part: '' -> 'GLASS.03' (was empty/garbled)
- label: 02.hero.childhouse/part-2: '' -> 'GLASS.03' (was empty/garbled)
- ref: 02.hero.childhouse/glass-03-09: section box: its 2 contents are cut as separate parts
- added: 02.hero.childhouse/part
- added: 02.hero.childhouse/part-2

### 02.hero.drowned-light
- label: 02.hero.drowned-light/2-arch-glow-shape-deep-teal-soft-vertical-glow: '2 ARCH GLOW SHAPE deep teal, soft vertical glow' -> '(LONG) cold teal light, water surface shafts' (closer label (cost 94 vs 114))
- label: 02.hero.drowned-light/warm-amber-lights-keep-all-separate: 'warm amber lights, keep all separate' -> 'FLOOR LAMP DOTS (7) amber lights, various sizes keep all separate' (re-read, more complete)
- label: 02.hero.drowned-light/light: 'light' -> 'CARDS (2) long black, shape light keep separate' (closer label (cost 45 vs 1000000000))
- label: 02.hero.drowned-light/5-optional-glass-panel-clear-acetate-distressed-: '5 OPTIONAL GLASS PANEL clear acetate, distressed handprints' -> 'OPTIONAL GLASS clear acetate, distressed handprints living hands or people' (re-read, more complete)
- label: 02.hero.drowned-light/reference-only-possible-arrangement-not-attached: 'REFERENCE ONLY possible arrangement (not attached)' -> 'REFERENCE ONLY one possible arrangement (not attached)' (re-read, more complete)
- ref: 02.hero.drowned-light/reference-only-possible-arrangement-not-attached: label says 'REFERENCE'

### 02.props.blinds-height
- label: 02.props.blinds-height/n2-n3-n4-ns-n6-six-seven-n7: 'N2 N3 N4 NS N6 (SIX) (SEVEN) N7' -> 'HEIGHT POST (seven notches)' (old text not on the sheet; label 18px-cost away)
- label: 02.props.blinds-height/part-9: '' -> 'N3' (was empty/garbled)
- label: 02.props.blinds-height/part-16: '' -> 'N4' (was empty/garbled)
- label: 02.props.blinds-height/part-20: '' -> 'N5' (was empty/garbled)
- label: 02.props.blinds-height/part-21: '' -> 'N6' (was empty/garbled)
- label: 02.props.blinds-height/part-22: '' -> 'TOP RAIL' (was empty/garbled)
- label: 02.props.blinds-height/part-23: '' -> 'PULL CORD' (was empty/garbled)
- ref: 02.props.blinds-height/only-assembled-states-not-working: label says 'assembled'

### 02.props.car
- label: 02.props.car/car: 'CAR' -> 'CAR BODY (SIDE)' (re-read, more complete)
- label: 02.props.car/glass-insert: 'GLASS INSERT' -> 'REAR WINDOW GLASS INSERT' (closer label (cost 8 vs 24); old text is side-window-glass-insert's)
- label: 02.props.car/headlight-left: 'HEADLIGHT (left' -> 'HEADLIGHT INSERTS (left right)' (re-read, more complete)
- label: 02.props.car/inserts-right: 'INSERTS right)' -> 'HEADLIGHT INSERTS (left right)' (re-read, more complete)
- label: 02.props.car/hazard-light-left: 'HAZARD LIGHT (left' -> 'HAZARD LIGHT INSERTS (left right)' (re-read, more complete)
- label: 02.props.car/inserts-right-2: 'INSERTS right)' -> 'HAZARD LIGHT INSERTS (left right)' (closer label (cost 34 vs 1000000000); old text is headlight-left's)
- label: 02.props.car/tide-white-enamel: 'TIDE (white enamel)' -> 'TIDE OFFICE NOTICE PLATE (white enamel)' (re-read, more complete)
- label: 02.props.car/overlay-slightly-brighter: 'OVERLAY (slightly brighter)' -> 'HEADLIT PLATE OVERLAY (slightly brighter)' (re-read, more complete)

### 02.props.mirror-phone-rings
- label: 02.props.mirror-phone-rings/mirror-pane-grey: 'MIRROR PANE grey)' -> 'PANE (pale grey)' (closer label (cost 9 vs 1000000000); old text is mirror-frame-front's)
- label: 02.props.mirror-phone-rings/screen: 'SCREEN' -> 'SCREEN (dark)' (re-read, more complete)
- label: 02.props.mirror-phone-rings/pulse-inward: 'PULSE INWARD' -> 'PULSE INWARD 2' (closer label (cost 35 vs 1000000000); old text is pulse-inward-1's)
- ref: 02.props.mirror-phone-rings/parts: label fragment (printed words)
- ref: 02.props.mirror-phone-rings/glow: label fragment (printed words)

### 02.props.poet-eye-aperture
- split: 02.props.poet-eye-aperture/separate-separate-white-separate (1633x242) -> 5 parts
- label: 02.props.poet-eye-aperture/small: '(SMALL)' -> 'IRIS (SMALL)' (re-read, more complete)
- label: 02.props.poet-eye-aperture/medium: '(MEDIUM)' -> 'IRIS Rl RING (MEDIUM)' (closer label (cost 1 vs 1000000000); old text is part-2's)
- label: 02.props.poet-eye-aperture/separate: '(separate)' -> '(skin plate, no brow)' (closer label (cost 44 vs 1000000000); old text is separate-2's)
- label: 02.props.poet-eye-aperture/plate-brow-no: 'plate, brow) no' -> '(skin plate, no brow)' (re-read, more complete)
- label: 02.props.poet-eye-aperture/road-abstract-reference-for-meaning: 'ROAD (abstract (reference for meaning,' -> 'ROAD (abstract line only) (reference for meaning, not on iris)' (re-read, more complete)
- label: 02.props.poet-eye-aperture/part: '' -> '(large pupil)' (was empty/garbled)
- label: 02.props.poet-eye-aperture/part-2: '' -> '(medium pupil)' (was empty/garbled)
- ref: 02.props.poet-eye-aperture/separate-separate-white-separate: section box: its 5 contents are cut as separate parts
- added: 02.props.poet-eye-aperture/small-pupil
- added: 02.props.poet-eye-aperture/road-abstract-reference-for-meaning
- added: 02.props.poet-eye-aperture/line-only-meaning-iris-not-on
- added: 02.props.poet-eye-aperture/part
- added: 02.props.poet-eye-aperture/part-2

### 02.props.tambourine
- label: 02.props.tambourine/part-3: '' -> 'J1' (was empty/garbled)
- label: 02.props.tambourine/part-4: '' -> 'J2' (was empty/garbled)
- label: 02.props.tambourine/part-5: '' -> 'J3' (was empty/garbled)
- label: 02.props.tambourine/part-6: '' -> 'J4' (was empty/garbled)
- label: 02.props.tambourine/replacement-disc-with-circular-smear: 'replacement disc with circular smear' -> 'RIM (OPEN) wooden rim with 8 8 jingle slots' (closer label (cost 36 vs 1000000000))

### 02.props.window
- split: 02.props.window/g01-g10-g11 (1498x217) -> 3 parts
- label: 02.props.window/window: 'WINDOW' -> 'CURTAIN LEFT' (closer label (cost 13 vs 362); old text is window-sill-2's)
- label: 02.props.window/suse-pane: 'suse PANE' -> 'GLASS PANE (CLEAR)' (old text not on the sheet; label 27px-cost away)
- label: 02.props.window/curtain-rod: 'CURTAIN ROD' -> 'GLASS PANE (CRACKED)' (closer label (cost 24 vs 66); old text is curtain-rod-2's)
- label: 02.props.window/part-10: '' -> 'G02' (was empty/garbled)
- label: 02.props.window/part-11: '' -> 'G03' (was empty/garbled)
- label: 02.props.window/part-12: '' -> 'G04' (was empty/garbled)
- label: 02.props.window/part-13: '' -> 'G05' (was empty/garbled)
- label: 02.props.window/part-14: '' -> 'G06' (was empty/garbled)
- label: 02.props.window/part-15: '' -> 'G07' (was empty/garbled)
- label: 02.props.window/part-16: '' -> 'G08' (was empty/garbled)
- label: 02.props.window/part-17: '' -> 'G09' (was empty/garbled)
- ref: 02.props.window/g01-g10-g11: section box: its 3 contents are cut as separate parts
- added: 02.props.window/intact
- added: 02.props.window/empty
- added: 02.props.window/struck

### 02.set.bedroom_night
- label: 02.set.bedroom_night/wall-bedroom-backwall-plain: 'WALL bedroom backwall (plain)' -> '01 WALL bedroom backwall (plain)' (re-read, more complete)
- label: 02.set.bedroom_night/mirror-glass-blank: 'mirror glass (blank)' -> '03 MIRROR.GLASS mirror glass (blank)' (re-read, more complete)
- ref: 02.set.bedroom_night/glass-blank: label fragment (printed words)

### 02.set.black_void
- label: 02.set.black_void/reuse14-set-black-void-inward-rings-light-sweeps: 'reuse14.set.black_void. Inward rings, light sweeps and actors:' -> 'Black backing: reuse14.set.black_void. Inward rings, light sweeps and actors: separate. FLOOR: none.' (re-read, more complete)

### 02.set.driveway_road_night
- label: 02.set.driveway_road_night/part-2: '' -> '02-HILL hill silhouette' (was empty/garbled)
- label: 02.set.driveway_road_night/part-3: '' -> '02-ROAD road' (was empty/garbled)
- label: 02.set.driveway_road_night/part-4: '' -> '02-DRIVEWAY driveway edge' (was empty/garbled)
- label: 02.set.driveway_road_night/hazards-and-dome-light-separate-props-fx-02-set-: 'hazards and dome light: separate props/FX. 02.set.driveway_road_night' -> '02-TARMAC wet tarmac with streaks' (closer label (cost 48 vs 205))

### 02.set.eye_macro.road
- label: 02.set.eye_macro.road/dash-loop-centre-line: 'DASH.LOOP centre-line' -> 'DASH.LOOP centre-line dashes (loop)' (re-read, more complete)
- ref: 02.set.eye_macro.road/part-2: label fragment (printed words)
- ref: 02.set.eye_macro.road/part-3: label fragment (printed words)
- ref: 02.set.eye_macro.road/part-5: label fragment (printed words)
- ref: 02.set.eye_macro.road/winding-2: label fragment (printed words)

### 02.set.overseer_skyline
- label: 02.set.overseer_skyline/01-gradient: '01 gradient,' -> 'deep navy gradient, no moon, no buildings' (old text not on the sheet; label 14px-cost away)
- label: 02.set.overseer_skyline/left-slab-tower: 'left slab tower' -> '02 TOWER.L left slab tower' (re-read, more complete)
- label: 02.set.overseer_skyline/03-right-slab-tower: '03 right slab tower' -> '03 TOWER.R right slab tower' (re-read, more complete)
- label: 02.set.overseer_skyline/05-right-pipework: '05 right pipework' -> '05 PIPE.R right pipework' (re-read, more complete)
- label: 02.set.overseer_skyline/left-pipework: 'left pipework' -> '04 PIPE.L left pipework' (re-read, more complete)
- label: 02.set.overseer_skyline/06: '06-' -> '02 TOWER.L left slab tower' (was empty/garbled)
- ref: 02.set.overseer_skyline/skyline-separate: label fragment (printed words)

### 03.fx.storm-light
- label: 03.fx.storm-light/2-morning-bright: '2. MORNING BRIGHT' -> '1 1. DAWN 2. MORNING 3. OVERCAST 4. NIGHT WARM' (old text not on the sheet; label 14px-cost away)
- label: 03.fx.storm-light/2-medium: '2. MEDIUM' -> 'RAIN (3 cards)' (old text not on the sheet; label 33px-cost away)
- label: 03.fx.storm-light/3-heavy: '3. HEAVY' -> 'MEDIUM 3. HEAVY' (re-read, more complete)
- label: 03.fx.storm-light/1-left-branch-2: '1. LEFT BRANCH 2.' -> '1. LEFT BRANCH CENTER BRANCH' (re-read, more complete)

### 03.hero.chapel
- label: 03.hero.chapel/front-front-facade-with-arched-doorway: 'FRONT front facade with arched doorway' -> '03-01 FRONT front facade with arched doorway and' (re-read, more complete)
- label: 03.hero.chapel/roof-l-left-roof-plane-slate: 'ROOF.L left roof plane (slate)' -> '03-02 ROOF.L left roof plane (slate)' (re-read, more complete)
- label: 03.hero.chapel/roof-r-right-roof-plane-slate: 'ROOF.R right roof plane (slate)' -> '03-03 ROOF.R right roof plane (slate)' (re-read, more complete)
- label: 03.hero.chapel/03-04-tower-base-square-bell-tower-shaft: '03-04 TOWER.BASE square bell-tower shaft' -> '03-04 TOWER.BASE square bell-tower shaft with belfry opening' (re-read, more complete)
- label: 03.hero.chapel/03-05-tower-cap-bell-tower-roof-top: '03-05 TOWER.CAP bell-tower roof top' -> '03-05 TOWER.CAP bell-tower roof top (slate)' (re-read, more complete)
- label: 03.hero.chapel/left-side-wall-with-three-lancet: 'left side wall with three lancet' -> '03-06 SIDE.L left side wall with three lancet openings' (re-read, more complete)
- label: 03.hero.chapel/side-r-right-side-wall-with-three-lancet-opening: 'SIDE.R right side wall with three lancet openings' -> '03-07 SIDE.R right side wall with three lancet openings' (re-read, more complete)
- label: 03.hero.chapel/03-08-choir-1-choir-left: '03-08 CHOIR.1 choir (left)' -> '03-08 CHOIR.1 choir stand/step (left)' (re-read, more complete)
- label: 03.hero.chapel/interior-end-wall-with-rose-window-companions-an: 'interior end wall with rose window companions. and' -> '03-14 WEST.WALL interior end wall with' (old text not on the sheet; label 29px-cost away)
- label: 03.hero.chapel/1-floor-floor-with-baptism-pool-aperture-nave-st: '1 FLOOR floor with baptism-pool aperture nave stone' -> '03-11 FLOOR nave stone floor with baptism-pool aperture' (re-read, more complete)
- label: 03.hero.chapel/03-12-pool-bottom-baptism-pool-bottom: '03-12 POOL.BOTTOM baptism-pool bottom' -> '03-12 POOL.BOTTOM 03-13 POOL.RIM baptism-pool bottom (dry stone)' (re-read, more complete)

### 03.hero.chapel.decay
- label: 03.hero.chapel.decay/roof-l-left-roof-plane-slate: 'ROOF.L left roof plane (slate)' -> '03-02 ROOF.L left roof plane (slate)' (re-read, more complete)
- label: 03.hero.chapel.decay/03-03-right-plane-roof-slate: '03-03 right plane roof (slate)' -> '03-03 ROOF.R right roof plane (slate)' (re-read, more complete)
- label: 03.hero.chapel.decay/bell-tower-shaft-square-with-belfry-opening: 'bell-tower shaft square with belfry opening' -> '03-04 TOWER.BASE square bell-tower shaft with belfry opening' (re-read, more complete)
- label: 03.hero.chapel.decay/03-05-tower-cap-bell-tower-roof-top: '03-05 TOWER.CAP bell-tower roof top' -> '03-05 TOWER.CAP bell-tower roof top (slate)' (re-read, more complete)
- label: 03.hero.chapel.decay/03-06-left-side-wall-with-three-lancet: '03-06 left side wall with three lancet' -> '03-06 SIDE.L left side wall with three lancet openings' (re-read, more complete)
- label: 03.hero.chapel.decay/side-r-right-side-with-three-lancet-openings: 'SIDE.R right side with three lancet openings' -> '03-07 SIDE.R right side wall with three lancet openings' (re-read, more complete)
- label: 03.hero.chapel.decay/choir-stand-step-left: 'choir stand/step (left)' -> '03-08 CHOIR.1 choir stand/step (left)' (re-read, more complete)
- label: 03.hero.chapel.decay/03-09-choir-stand-step-centre: '03-09 choir stand/step (centre)' -> '03-09 CHOIR.2 choir stand/step (centre)' (re-read, more complete)
- label: 03.hero.chapel.decay/stone-floor-with-baptism-pool-aperture-nave: 'stone floor with baptism-pool aperture nave' -> '1 FLOOR nave stone floor with baptism-pool aperture' (re-read, more complete)
- label: 03.hero.chapel.decay/pool-bottom-baptism-pool-bottom-dry-stone: 'POOL.BOTTOM baptism-pool bottom (dry stone)' -> '03-12 POOL.BOTTOM baptism-pool bottom (dry stone)' (re-read, more complete)
- label: 03.hero.chapel.decay/baptism-pool-rim-stone: 'baptism-pool rim (stone)' -> '03-13 POOL.RIM baptism-pool rim (stone)' (re-read, more complete)

### 03.hero.chapel.interior-states
- label: 03.hero.chapel.interior-states/l-2-aged-three-lancet-wall: 'L.2 aged three-lancet wall' -> 'WALL.2 aged three-lancet wall (damp, cracks, moss)' (re-read, more complete)
- label: 03.hero.chapel.interior-states/glass-2a-left-lancet-pane: 'GLASS.2A left lancet pane' -> 'GLASS.2A left lancet pane (cracked, missing glass) (cracked, missing glass) (cracked, missing glass)' (closer label (cost 74 vs 1000000000); old text is glass-2b-lancet-pane-centre's)
- label: 03.hero.chapel.interior-states/right-lancet-cracked-missing: 'right lancet (cracked, missing' -> 'GLASS.2C right lancet pane' (old text not on the sheet; label 26px-cost away)
- label: 03.hero.chapel.interior-states/aged-near-pew-back-worn-splintering: 'aged near pew-back (worn, splintering)' -> 'PEWBACK.2 aged near pew-back (worn, splintering)' (re-read, more complete)
- label: 03.hero.chapel.interior-states/glass-3b-lancet-centre-remnant: 'GLASS.3B lancet centre remnant' -> 'GLASS.3A left lancet (broken, missing glass) (broken, missing glass) (broken, missing glass)' (closer label (cost 35 vs 48); old text is glass-3c-right-lancet's)
- label: 03.hero.chapel.interior-states/pewback-3-pew-back-ruined-near-remnant: 'PEWBACK.3 pew-back ruined near remnant' -> 'PEWBACK.3 ruined pew-back remnant (broken, splintered)' (old text not on the sheet; label 19px-cost away)
- label: 03.hero.chapel.interior-states/glass-3c-right-lancet: 'GLASS.3C right lancet' -> 'GLASS.3B centre lancet remnant right lancet' (closer label (cost 56 vs 401); old text is right-lancet-cracked-missing's)
- ref: 03.hero.chapel.interior-states/part-2: label fragment (printed words)
- ref: 03.hero.chapel.interior-states/moss: label fragment (printed words)

### 03.hero.chapel.ruin
- label: 03.hero.chapel.ruin/03-01-front-arch-doorway-ruined-facade-with-part: '03-01 FRONT arch-doorway ruined facade with partial and window' -> '03-01 FRONT ruined facade with arch-doorway and partial rose window' (re-read, more complete)
- label: 03.hero.chapel.ruin/03-04-tower-base-belfry-roofless-ruined-shaft: '03-04 TOWER.BASE belfry (roofless) ruined shaft' -> '03-04 TOWER.BASE 03-05 TOWER.C ruined belfry shaft (roofless) ruined cap (slate)' (re-read, more complete)
- label: 03.hero.chapel.ruin/03-12-pool-bottom-ruined-pool-bottom-dry-stone: '03-12 POOL.BOTTOM ruined pool bottom (dry stone)' -> '03-12 POOL.BOTTOM ruined pool bottom (dry stone) ruined pool rim (stone)' (re-read, more complete)
- label: 03.hero.chapel.ruin/pool-rim-stone-rim: 'POOL.RIM (stone) rim' -> '03-13 POOL.RIM' (old text not on the sheet; label 39px-cost away)

### 03.props.cobwebs
- label: 03.props.cobwebs/a: 'Aé' -> '6. HALF' (was empty/garbled)
- label: 03.props.cobwebs/part-9: '' -> 'AS' (was empty/garbled)
- label: 03.props.cobwebs/6-ci: '6 Ci' -> 'C1' (was empty/garbled)
- label: 03.props.cobwebs/part-22: '' -> 'Cé' (was empty/garbled)

### 03.props.rose-window
- label: 03.props.rose-window/frame-12-petal-openings: 'FRAME 12 PETAL OPENINGS' -> '12 PETAL OPENINGS CENTRAL OPENING' (re-read, more complete)
- label: 03.props.rose-window/e1-shore-remnant-1-curved-rim-arc: 'E1 SHORE REMNANT 1 CURVED RIM ARC' -> 'El SHORE REMNANT 1 RIM ARC' (closer label (cost 0 vs 724); old text is e3-shore-remnant-3-curved-rim-arc's)
- ref: 03.props.rose-window/to-break: label fragment (printed words)
- ref: 03.props.rose-window/to-break-2: label fragment (printed words)

### 03.props.strings-footprints
- label: 03.props.strings-footprints/thread: '(thread)' -> 'TI (thread)' (closer label (cost 22 vs 1000000000); old text is thread-2's)
- label: 03.props.strings-footprints/thread-2: '(thread)' -> 'T2 (thread)' (re-read, more complete)
- label: 03.props.strings-footprints/thread-3: '(thread)' -> 'T3 (thread)' (closer label (cost 17 vs 1000000000); old text is thread-2's)
- label: 03.props.strings-footprints/thread-4: '(thread)' -> 'T4 (thread)' (closer label (cost 12 vs 1000000000); old text is thread-2's)
- label: 03.props.strings-footprints/thread-5: '(thread)' -> 'T5 (thread)' (closer label (cost 13 vs 1000000000); old text is thread-2's)
- label: 03.props.strings-footprints/poet-foot-pad: 'POET FOOT PAD' -> 'POET FOOT PAD (stamp)' (re-read, more complete)
- label: 03.props.strings-footprints/ex-foot-pad: 'EX FOOT PAD' -> 'EX FOOT PAD (stamp)' (re-read, more complete)

### 03.props.tambourine-broken
- label: 03.props.tambourine-broken/whole-tambourine-tumble-blur: 'WHOLE TAMBOURINE (TUMBLE BLUR)' -> 'WHOLE TAMBOURINE (TUMBLE BLUR) replacement disc' (re-read, more complete)

### 03.set.chapel_side_doors
- label: 03.set.chapel_side_doors/left-door-leaf-hinge-edge: 'left door leaf (hinge edge)' -> 'DOOR.L left door leaf (hinge at outer edge)' (re-read, more complete)
- label: 03.set.chapel_side_doors/right-door-leaf-hinge-edge: 'right door leaf (hinge edge)' -> 'DOOR.R right door leaf (hinge at outer edge)' (re-read, more complete)
- label: 03.set.chapel_side_doors/stone-doorstep-wet-dark-light-supplied-separatel: 'stone doorstep (wet, dark) light supplied separately. boxes and their 03.set.chapel_side_doors' -> 'STEP stone doorstep (wet, dark)' (old text not on the sheet; label 9px-cost away)

### 03.set.chapel_storm
- label: 03.set.chapel_storm/03-floodwater: '03 floodwater' -> 'Chapel spire, walls and roof:03.hero.chapel state sheets. Lightning, rain, blanket/objects: separate FX/props.' (closer label (cost 76 vs 189))
- ref: 03.set.chapel_storm/02: label fragment (printed words)

### 04.fx.moon-reach
- label: 04.fx.moon-reach/part-7: '' -> 'CLUSTER' (was empty/garbled)
- label: 04.fx.moon-reach/7-reach2-medium: '[7] REACH2 medium' -> 'REACH1 SMALL' (old text not on the sheet; label 27px-cost away)
- label: 04.fx.moon-reach/part-12: '' -> 'REACH3 WIDE' (was empty/garbled)
- ref: 04.fx.moon-reach/2-full: label fragment (printed words)
- ref: 04.fx.moon-reach/composite-reference: label says 'COMPOSITE'

### 04.hero.viaduct
- label: 04.hero.viaduct/01-d-gothic-railway-archband-with-4-pointed-arch: '01 D gothic railway archband with 4 pointed arches (one broken) grey stone span' -> '01 ARCH.BAND rust-dark grey stone gothic railway archband with 4 pointed arches (one span broken)' (re-read, more complete)
- label: 04.hero.viaduct/arch-repeat-complete-pointed: 'ARCH.REPEAT complete pointed' -> '02 ARCH.REPEAT complete pointed gothic arch frame ARCH.NEAR larger' (re-read, more complete)
- label: 04.hero.viaduct/left-ceramic-edge: 'left ceramic edge' -> '04 PATCH.L' (closer label (cost 21 vs 1000000000))
- label: 04.hero.viaduct/patch-r-right-edge-ceramic: 'PATCH.R right edge ceramic' -> 'PATCH.R right ceramic edge plate' (re-read, more complete)

### 04.props.faith-blooms
- label: 04.props.faith-blooms/part-13: '' -> 'ST3' (was empty/garbled)

### 04.props.heart
- label: 04.props.heart/blue-point: 'BLUE POINT' -> 'BLUE POINT # Saa7ff' (re-read, more complete)
- label: 04.props.heart/acetate-support: 'ACETATE SUPPORT' -> 'ACETATE SUPPORT STEM' (re-read, more complete)
- label: 04.props.heart/overlay: 'OVERLAY' -> 'ASH-FLECK OVERLAY' (re-read, more complete)
- ref: 04.props.heart/slightly: label fragment (printed words)

### 04.props.poet-jointed-hands
- label: 04.props.poet-jointed-hands/poem-04: 'POEM 04' -> '3 PARTS (PALM FINGERS THUMB)' (old text not on the sheet; label 23px-cost away)
- label: 04.props.poet-jointed-hands/nevermore-black: 'NEVERMORE BLACK' -> '3 PARTS (PALM FINGERS THUMB)' (old text not on the sheet; label 23px-cost away)
- label: 04.props.poet-jointed-hands/male-poet: 'MALE POET' -> '3 PARTS (PALM FINGERS THUMB)' (old text not on the sheet; label 22px-cost away)
- label: 04.props.poet-jointed-hands/assembly: 'ASSEMBLY' -> '3 PARTS (PALM FINGERS THUMB)' (old text not on the sheet; label 24px-cost away)
- label: 04.props.poet-jointed-hands/pivot-finger-hinge: 'PIVOT FINGER HINGE)' -> '3 PARTS (PALM FINGERS THUMB)' (closer label (cost 19 vs 1000000000); old text is right-palm-pivot's)
- label: 04.props.poet-jointed-hands/right-palm-pivot: 'RIGHT PALM PIVOT' -> 'RIGHT (WRIST PIVOT FINGER HINGE)' (old text not on the sheet; label 12px-cost away)
- label: 04.props.poet-jointed-hands/palm-pivot: 'PALM PIVOT' -> '3 PARTS (PALM FINGERS THUMB)' (closer label (cost 23 vs 1000000000); old text is down's)
- label: 04.props.poet-jointed-hands/right-pivot: 'RIGHT PIVOT' -> '3 PARTS (PALM FINGERS THUMB)' (closer label (cost 25 vs 314); old text is right-thumb's)
- label: 04.props.poet-jointed-hands/left-finger-fan: 'LEFT FINGER FAN' -> 'RIGHT' (closer label (cost 19 vs 778); old text is left-finger-fan-four-fingers's)
- label: 04.props.poet-jointed-hands/left: 'LEFT' -> 'LEFT THUMB' (closer label (cost 12 vs 1148); old text is left-thumb's)
- label: 04.props.poet-jointed-hands/hand-poses-all-parts-joined-small-sleeve-socket-: 'HAND POSES (ALL PARTS JOINED) SMALL SLEEVE SOCKET SHOWN' -> 'ASSEMBLED REFERENCE ONLY' (old text not on the sheet; label 22px-cost away)
- label: 04.props.poet-jointed-hands/down: 'DOWN' -> 'PALM DOWN' (re-read, more complete)
- ref: 04.props.poet-jointed-hands/hand-poses-all-parts-joined-small-sleeve-socket-: label says 'ASSEMBLED'
- ref: 04.props.poet-jointed-hands/down: under the band heading 'ASSEMBLED REFERENCE ONLY'
- ref: 04.props.poet-jointed-hands/flexed: under the band heading 'ASSEMBLED REFERENCE ONLY'
- ref: 04.props.poet-jointed-hands/open: under the band heading 'ASSEMBLED REFERENCE ONLY'
- ref: 04.props.poet-jointed-hands/wrist-seated-with-sleeve-socket: under the band heading 'ASSEMBLED REFERENCE ONLY'

### 04.props.word-shore
- label: 04.props.word-shore/reference-only: 'REFERENCE ONLY' -> 'SHORE' (closer label (cost 31 vs 45))
- label: 04.props.word-shore/2-gel-panes: '(2) GEL PANES' -> '(2 FRAMES)' (closer label (cost 33 vs 120); old text is gel-panes-2's)
- label: 04.props.word-shore/part-29: '' -> '4' (was empty/garbled)
- label: 04.props.word-shore/part-30: '' -> 'te' (was empty/garbled)

### 04.set.night_garden_field
- label: 04.set.night_garden_field/left-weeds-grass: 'left weeds/grass' -> 'WEED.L left weeds/grass framing strip' (re-read, more complete)
- label: 04.set.night_garden_field/weed-r-right-strip: 'WEED.R right strip' -> 'WEED.R right weeds/grass framing strip' (re-read, more complete)
- label: 04.set.night_garden_field/soil-soil-floor-with: 'SOIL soil floor with' -> 'SOIL planted soil floor with scattered seeds' (re-read, more complete)

### 04.set.shore_night
- label: 04.set.shore_night/3-04-wave-3-wavefront: '3 04.WAVE.3 wavefront' -> 'WAVE.3 04.WAVE.3 wavefront (inner)' (re-read, more complete)
- label: 04.set.shore_night/stump-2-04-stump-2-charred-stump: 'STUMP.2 04.STUMP.2 charred stump' -> 'STUMP. 1 04.STUMP.1 charred stump STUMP. 2 04.STUMP.2 charred stump TREE. 1 O4.TREE.1 still tree' (re-read, more complete)
- label: 04.set.shore_night/ash-light-04-ash-light-ash-sand-light: 'ASH.LIGHT 04.ASH.LIGHT ash sand (light)' -> 'ASH. LIGHT 04.ASH.LIGHT ash sand (light) Ravens, trail prints, broken ring and heart supplied separately; steps reuse11.hero.steps.' (closer label (cost 28 vs 761); old text is ash-dark-ash-sand-dark-04-set-shore-night's)

### 05.hero.perimeter
- label: 05.hero.perimeter/top-rail-right: 'top rail (right)' -> 'RAIL.R top rail (right)' (re-read, more complete)
- label: 05.hero.perimeter/floor-wet-floor-no: 'FLOOR wet floor (no' -> 'MESH.R_ wire mesh panel (right)' (closer label (cost 116 vs 202))

### 05.props.fingerprint
- label: 05.props.fingerprint/reference-only-assembly-examples: 'REFERENCE ONLY (ASSEMBLY EXAMPLES)' -> '1. PALM BASE (FRONT BLANK RIDGES)' (closer label (cost 21 vs 33))
- label: 05.props.fingerprint/r4: 'R4' -> 'R1' (closer label (cost 27 vs 54); old text is r4-2's)
- label: 05.props.fingerprint/r5: 'R5' -> 'R2' (closer label (cost 25 vs 30); old text is r5-2's)
- label: 05.props.fingerprint/x3-2: '(x3)' -> 'D1' (old text not on the sheet; label 36px-cost away)

### 05.props.galaxy-universe
- label: 05.props.galaxy-universe/b2-expansion-ring: 'B2 EXPANSION RING' -> 'B2 EXPANSION RING SMALL' (re-read, more complete)
- label: 05.props.galaxy-universe/thin-hammered-ring-reference-only: 'thin hammered ring REFERENCE ONLY' -> 'Ai - GALAXY DISC four spiral arms + central bulge' (closer label (cost 41 vs 1000000000))
- label: 05.props.galaxy-universe/axle-support-card-with-hole: 'AXLE SUPPORT card with hole' -> 'A3 AXLE SUPPORT TAB card with hole' (re-read, more complete)
- ref: 05.props.galaxy-universe/disc: label fragment (printed words)

### 05.props.staff-mattress-emblem
- label: 05.props.staff-mattress-emblem/shaft-carved-ebony: 'SHAFT carved ebony' -> 'STAFF SHAFT carved ebony' (re-read, more complete)
- label: 05.props.staff-mattress-emblem/brass-empty-aperture: 'brass, empty aperture' -> 'TOP CAGE brass, empty aperture' (re-read, more complete)
- label: 05.props.staff-mattress-emblem/view-thin-rigid-tufted-stained: 'VIEW thin, rigid, tufted, stained' -> 'TOP VIEW thin, rigid, tufted, stained' (re-read, more complete)
- label: 05.props.staff-mattress-emblem/pale-stone-fits-recess: 'pale stone, fits recess' -> 'PAVING CARD rectangular stone floor with shallow emblem recess' (closer label (cost 19 vs 1000000000))
- label: 05.props.staff-mattress-emblem/acetate-water-droplets-a: 'ACETATE water droplets A' -> '(DAMP water droplets A' (closer label (cost 9 vs 60); old text is damp-droplets-b-water's)
- label: 05.props.staff-mattress-emblem/damp-droplets-b-water: '(DAMP droplets B water' -> '1) ACETATE (DAMP water droplets' (closer label (cost 24 vs 1000000000); old text is acetate-water-droplets-a's)
- label: 05.props.staff-mattress-emblem/amber-narrow: 'amber, narrow' -> 'LIGHT amber, narrow' (re-read, more complete)

### 05.props.star-names
- label: 05.props.star-names/mae-heir-orb: 'MAE HEIR ORB' -> 'SUPPORT STEM MAE HEIR ORB (#FFC94A)' (re-read, more complete)
- label: 05.props.star-names/ida: 'IDA' -> 'NAME02 IDA' (re-read, more complete)
- label: 05.props.star-names/otis: 'OTIS' -> 'NAM OTIS' (re-read, more complete)
- label: 05.props.star-names/mae: 'MAE' -> 'NAMEO5 MAE' (re-read, more complete)
- label: 05.props.star-names/cora: 'CORA' -> 'NAMEO7 CORA' (re-read, more complete)
- label: 05.props.star-names/june: 'JUNE' -> 'NAME09 JUNE' (re-read, more complete)

### 05.set.humid_basement
- label: 05.set.humid_basement/05-wall-of-two-of-grey-with-empty-window-well-ap: '05.WALL of two of grey with empty window-well aperture' -> 'long low wall of two courses of damp grey cinderblock with empty window-well aperture' (re-read, more complete)
- label: 05.set.humid_basement/05-plate-joist: '05.PLATE joist' -> '05.PLATE perforated metal joist plate' (closer label (cost 14 vs 1000000000))

### 05.set.winged_marble_gate
- label: 05.set.winged_marble_gate/rib-r-right-wing-ribs-right-open: 'RIB.R right wing (ribs) right open' -> 'THRESHOLD threshold (no doors)' (old text not on the sheet; label 28px-cost away)

### 06.fx.comet
- label: 06.fx.comet/part-2: '' -> 'c02' (was empty/garbled)
- label: 06.fx.comet/part-3: '' -> 'C03' (was empty/garbled)
- label: 06.fx.comet/co1-2: 'co1' -> 'C08' (closer label (cost 12 vs 1000000000); old text is co9's)
- label: 06.fx.comet/head-reuse-head-o5star: 'HEAD (reuse head) O5star' -> 'HEAD ORB (reuse O5star head)' (re-read, more complete)
- label: 06.fx.comet/part-17: '' -> 'DOME BEACON' (was empty/garbled)

### 06.fx.water-rainbow-clouds
- label: 06.fx.water-rainbow-clouds/reference-only: 'REFERENCE ONLY' -> 'REFERENCE ONLY ASSEMBLY LAYOUT' (re-read, more complete)
- label: 06.fx.water-rainbow-clouds/only-assembly: 'ONLY ASSEMBLY' -> 'REFERENCE ONLY ASSEMBLY LAYOUT' (re-read, more complete)
- ref: 06.fx.water-rainbow-clouds/reference-only: label says 'REFERENCE'
- ref: 06.fx.water-rainbow-clouds/only-assembly: label says 'REFERENCE'

### 06.hero.forum
- label: 06.hero.forum/back: 'BACK' -> 'LIP.3 inner rim ring' (closer label (cost 40 vs 136); old text is back-oval-light-backing's)

### 06.hero.house
- label: 06.hero.house/hanging-cable-web: 'hanging cable web' -> 'corrugated panel' (closer label (cost 34 vs 1000000000))
- ref: 06.hero.house/the: label fragment (printed words)
- ref: 06.hero.house/the-house: label fragment (printed words)
- ref: 06.hero.house/separate-parts: label fragment (printed words)

### 06.hero.teahouse
- label: 06.hero.teahouse/front-front-stall-facade: '-FRONT front (stall facade)' -> '06.FRONT front (stall facade)' (re-read, more complete)
- label: 06.hero.teahouse/interior-back-wall: 'interior back wall' -> '06.INTERIOR.BACK interior back wall' (re-read, more complete)

### 06.props.coin-booth
- label: 06.props.coin-booth/wet-ivory-marble-card-with-brass-details: 'wet ivory marble card with brass details' -> 'BOOTH FRONT FRAME wet ivory marble card with brass details' (re-read, more complete)
- label: 06.props.coin-booth/coin-face-thick-translucent-coin-thick: 'COIN FACE thick translucent coin thick' -> 'COIN FACE thick translucent coin pale blue with' (re-read, more complete)
- label: 06.props.coin-booth/coin-edge-with-cardboard: 'COIN EDGE with cardboard' -> 'COIN EDGE thick with cardboard core, translucent' (re-read, more complete)
- label: 06.props.coin-booth/coin-glow-replacement-pale-blue-coin-with: 'COIN GLOW (REPLACEMENT) pale blue coin with' -> 'COIN GLOW (REPLACEMENT) same coin with pale blue ink inside edge (for glow)' (re-read, more complete)
- label: 06.props.coin-booth/rim-card-pink-slim-card-teal: 'RIM CARD (pink slim card teal)' -> 'NEON RIM CARD slim card (pink teal)' (old text not on the sheet; label 1px-cost away)
- label: 06.props.coin-booth/lantern-window-amber-warm: 'LANTERN WINDOW amber warm' -> 'LANTERN WINDOW PANES (x2) warm amber glass card' (re-read, more complete)
- label: 06.props.coin-booth/panes-x2-glass-card: 'PANES (x2) glass card' -> 'LANTERN WINDOW PANES (x2) warm amber glass card' (old text not on the sheet; label 31px-cost away)
- label: 06.props.coin-booth/amp-window-card-trims: 'amp WINDOW card trims' -> 'LAMP' (old text not on the sheet; label 23px-cost away)
- label: 06.props.coin-booth/panes-glass: 'PANES glass' -> 'LANTERN WINDOW PANES (x2) warm amber glass card' (closer label (cost 31 vs 1000000000))
- label: 06.props.coin-booth/pieces-x4-needed-as: 'PIECES (x4) needed) as' -> 'TRIM PIECES (x4) card trims (use needed)' (old text not on the sheet; label 31px-cost away)
- label: 06.props.coin-booth/window-trim-use-as: 'WINDOW TRIM (use as' -> 'TRIM PIECES (x4) card trims (use needed)' (old text not on the sheet; label 13px-cost away)
- ref: 06.props.coin-booth/part-2: label fragment (printed words)
- ref: 06.props.coin-booth/part-3: label fragment (printed words)

### 06.props.lantern-candle-guitar
- label: 06.props.lantern-candle-guitar/separate: '(SEPARATE)' -> 'HANDLE (SEPARATE)' (closer label (cost 1 vs 1000000000); old text is post-separate's)
- label: 06.props.lantern-candle-guitar/candle-body: 'CANDLE BODY' -> 'CANDLE (PILLAR)' (closer label (cost 16 vs 111))
- label: 06.props.lantern-candle-guitar/guitar-body-neck-single-card: 'GUITAR (BODY NECK SINGLE CARD)' -> 'GUITAR SINGLE CARD) (MUSICAL PROP)' (re-read, more complete)
- label: 06.props.lantern-candle-guitar/flame-b-small: 'FLAME B SMALL' -> 'FLAME (SMALL REPLACEMENT)' (closer label (cost 12 vs 67); old text is flame-a-standard's)

### 06.set.atlantis_gate
- label: 06.set.atlantis_gate/portal-06-a-portal: 'PORTAL 06.A.portal' -> 'PORTAL 06.A.portal monumental gate frame' (re-read, more complete)
- label: 06.set.atlantis_gate/floor-06-a-floor: 'FLOOR 06.A.floor' -> 'FLOOR 06.A.floor polished marble forecourt (pool aperture)' (re-read, more complete)
- label: 06.set.atlantis_gate/06-a-pool-rim: '06.A.pool.rim' -> 'POOL.RIM 06.A.pool.rim marble pool rim' (re-read, more complete)
- label: 06.set.atlantis_gate/booth-platform-06-a-booth-platform: 'BOOTH.PLATFORM 06.A.booth.platform' -> 'BOOTH.PLATFORM 06.A.booth.platform marble plinth' (re-read, more complete)

### 06.set.atlantis_plaza
- label: 06.set.atlantis_plaza/facade-l-left-plaza-building-front: 'FACADE.L left plaza building front' -> 'FACADE.L left plaza building front GLAZING.L' (re-read, more complete)
- label: 06.set.atlantis_plaza/facade-c-plaza-building-front-centre: 'FACADE.C plaza building front centre' -> 'FACADE.C centre plaza building front GLAZING.C 7 panes' (closer label (cost 4 vs 1000000000); old text is facade-r-right-plaza-building-front's)
- label: 06.set.atlantis_plaza/facade-r-right-plaza-building-front: 'FACADE.R right plaza building front' -> 'FACADE.R right plaza building front GLAZING.R' (re-read, more complete)
- label: 06.set.atlantis_plaza/8: '—8' -> 'LO3' (was empty/garbled)
- label: 06.set.atlantis_plaza/los: 'LOS' -> 'panes' (closer label (cost 17 vs 1000000000); old text is lo1's)
- label: 06.set.atlantis_plaza/lo7: 'LO7' -> 'LO6 LO7 LO8' (closer label (cost 8 vs 1000000000); old text is lo1's)
- label: 06.set.atlantis_plaza/ro1-ro2-r03: 'RO1 RO2 R03' -> 'RO1 RO2 RO3 R04' (re-read, more complete)
- label: 06.set.atlantis_plaza/facade-r-building: 'FACADE.R building' -> 'FACADE.R right plaza building front GLAZING.R' (old text not on the sheet; label 18px-cost away)
- label: 06.set.atlantis_plaza/part-19: '' -> 'RO7' (was empty/garbled)

### 06.set.atlantis_waterfront
- label: 06.set.atlantis_waterfront/strip: 'strip' -> '06.WATER water plane' (closer label (cost 77 vs 241); old text is 06-terrace-r's)
- label: 06.set.atlantis_waterfront/06-terrace-r: '06.TERRACE.R' -> '06.WATERLINE water-edge strip' (closer label (cost 46 vs 1000000000); old text is 06-vine-l-left-vines's)
- label: 06.set.atlantis_waterfront/06-vine-l-left-vines: '06.VINE.L left vines' -> '06.TERRACE.L left terrace' (closer label (cost 111 vs 140); old text is 06-set-atlantis-waterfront's)
- label: 06.set.atlantis_waterfront/06-vine-r-right-vines: '06.VINE.R right vines' -> '06.TERRACE.R right terrace' (closer label (cost 79 vs 129))
- label: 06.set.atlantis_waterfront/behind-movable-waterline-fx-remain-independent-d: 'behind movable waterline. FX remain independent; derive reflection from final city assembly.' -> 'Assemble CITY01-16 behind movable waterline. Vine and water-motion FX remain independent; derive reflection from final city assembly.' (re-read, more complete)

### 06.set.atlantis_waterfront.skyline
- label: 06.set.atlantis_waterfront.skyline/reflected-skyline-are-separate-exact-assembly: 'reflected skyline are separate. Exact assembly' -> 'CITY.13 SLAB TOWER' (closer label (cost 14 vs 1000000000))

### 06.set.causeway_road
- label: 06.set.causeway_road/06-set-causeway-road-dome-and-two-spire-tips-cit: '06.set.causeway_road Dome and two spire tips: CITY01-03 from skyline sheet behind waterline. Comets, lantern' -> '06.ROAD.NEAR near-end paving (foreground extension)' (closer label (cost 101 vs 175))
- ref: 06.set.causeway_road/yellow-brick: label fragment (printed words)

### 06.set.crystal_tree_hall
- label: 06.set.crystal_tree_hall/crystal-canopy-left-1-front-largest: 'crystal canopy left 1 (front largest)' -> 'CANOPY.L1 crystal canopy left (front / largest)' (re-read, more complete)

### 06.set.narrow_streets
- label: 06.set.narrow_streets/right-door-leaf: 'right door leaf' -> 'DOOR.R right door leaf' (re-read, more complete)

### 07.fx.party-haze
- label: 07.fx.party-haze/drifting-haze-band-a: 'DRIFTING HAZE BAND A' -> 'HO1 DRIFTING HAZE BAND A' (re-read, more complete)
- label: 07.fx.party-haze/projections-and-glow-animation-instructions-are: 'projections and glow animation instructions are' -> 'HO3 DRIFTING HAZE AND C' (old text not on the sheet; label 40px-cost away)
- label: 07.fx.party-haze/ao2-amber-wash-card-b: 'AO2 AMBER WASH CARD B' -> 'Ho2 DRIFTING HAZE BAND' (closer label (cost 47 vs 1000000000); old text is amber-wash-card-a's)
- label: 07.fx.party-haze/g02: 'G02' -> 'GO2' (closer label (cost 9 vs 1000000000); old text is g01's)
- label: 07.fx.party-haze/go7: 'GO7' -> 'G07' (closer label (cost 3 vs 1000000000); old text is g02's)
- ref: 07.fx.party-haze/reference: label says 'REFERENCE'

### 07.hero.house
- label: 07.hero.house/part-3: '' -> 'Assembled view for reference only. Do not cut. Individual parts above.' (was empty/garbled)
- label: 07.hero.house/rusted-container-wall-with-picture-slot-empty: 'rusted container wall with picture slot (empty)' -> 'ON WALL PANEL' (closer label (cost 23 vs 31); old text is star-hole-sliding-tabs-cover's)
- label: 07.hero.house/star-hole-sliding-tabs-cover: 'STAR HOLE sliding tabs cover' -> 'A4 PROJECTION rusted container wall with picture slot (empty)' (old text not on the sheet; label 23px-cost away)

### 07.hero.house.furniture
- label: 07.hero.house.furniture/couch-r: 'COUCH (R)' -> 'PLINTH (R)' (closer label (cost 24 vs 164); old text is couch-back-r's)

### 07.hero.shaft
- recut: 07.hero.shaft/5-frame-5-6-frame-6: framed panel [11, 50, 420, 391] -> figure [27, 81, 373, 347]
- recut: 07.hero.shaft/7-frame-7-8-frame-8: framed panel [438, 53, 391, 385] -> figure [466, 108, 334, 318]
- recut: 07.hero.shaft/side-l: framed panel [836, 80, 370, 361] -> figure [870, 145, 299, 279]
- recut: 07.hero.shaft/sider-cage-floor: framed panel [1211, 81, 314, 360] -> figure [1248, 161, 244, 243]
- recut: 07.hero.shaft/l-doorr: framed panel [11, 451, 216, 253] -> figure [34, 505, 171, 170]
- recut: 07.hero.shaft/part-8: framed panel [618, 450, 155, 254] -> figure [641, 552, 108, 110]
- recut: 07.hero.shaft/sider-cage-floor-2: framed panel [1031, 450, 125, 254] -> figure [1053, 488, 83, 200]
- recut: 07.hero.shaft/cage-floor: framed panel [1161, 450, 125, 254] -> figure [1179, 488, 83, 200]
- recut: 07.hero.shaft/part-12: framed panel [1293, 451, 232, 253] -> figure [1311, 496, 196, 188]
- recut: 07.hero.shaft/doorr-2: framed panel [11, 713, 179, 271] -> figure [59, 748, 84, 224]
- recut: 07.hero.shaft/part-14: framed panel [195, 713, 172, 271] -> figure [238, 746, 84, 225]
- label: 07.hero.shaft/5-frame-5-6-frame-6: '5 FRAME 5 6 FRAME 6' -> 'FRAME 1' (printed in its panel)
- label: 07.hero.shaft/7-frame-7-8-frame-8: '7 FRAME 7 8 FRAME 8' -> '2 FRAME 2' (printed in its panel)
- label: 07.hero.shaft/side-l: 'SIDE L' -> '3 FRAME 3' (printed in its panel)
- label: 07.hero.shaft/l-doorr: 'L DOORR' -> '5 FRAME 5' (printed in its panel)
- label: 07.hero.shaft/sider-cage-floor-2: 'SIDER CAGE FLOOR' -> 'CAGE SIDE L' (printed in its panel)
- label: 07.hero.shaft/cage-floor: 'CAGE FLOOR' -> 'CAGE SIDER' (printed in its panel)
- label: 07.hero.shaft/part-12: '' -> 'CAGE FLOOR' (printed in its panel)
- label: 07.hero.shaft/doorr-2: 'DOORR' -> 'DOORL' (printed in its panel)
- label: 07.hero.shaft/part-14: '' -> 'DOORR' (printed in its panel)
- label: 07.hero.shaft/doorr: 'DOORR' -> 'DOOR R (SLIDING)' (old text not on the sheet; label 34px-cost away)
- label: 07.hero.shaft/lamp-repeatable-2: 'LAMP (REPEATABLE)' -> 'LANDING' (closer label (cost 67 vs 89); old text is part-16's)
- label: 07.hero.shaft/part-16: '' -> 'LAMP (REPEATABLE)' (was empty/garbled)
- label: 07.hero.shaft/part-17: '' -> 'VIOLET OPENING (BACKER)' (was empty/garbled)
- label: 07.hero.shaft/part-18: '' -> 'ASSEMBLED' (was empty/garbled)
- ref: 07.hero.shaft/part-18: label says 'ASSEMBLED'

### 07.props.bar-handheld
- split: 07.props.bar-handheld/lighter-body-flame-card-phone-front-body-phone-b (1507x270) -> 4 parts
- label: 07.props.bar-handheld/cyan-underlight-strip: 'CYAN UNDERLIGHT STRIP' -> 'piece)' (closer label (cost 47 vs 1000000000))
- label: 07.props.bar-handheld/magenta-underlight-strip-alternate: 'MAGENTA UNDERLIGHT STRIP (alternate)' -> 'CYAN ea' (old text not on the sheet; label 31px-cost away)
- label: 07.props.bar-handheld/lighter-body-unlit: 'LIGHTER BODY (unlit)' -> 'LIGHTER BODY FLAME CARD (unlit)' (re-read, more complete)
- label: 07.props.bar-handheld/flame-card-separate: 'FLAME CARD (separate)' -> 'DARK (separate) (empty screen recess) INSERT' (closer label (cost 58 vs 1000000000); old text is phone-back-separate's)
- label: 07.props.bar-handheld/cream-screen: 'CREAM SCREEN' -> 'CREAM SCREEN INSERT' (re-read, more complete)
- label: 07.props.bar-handheld/lighter-lit-prop-only: 'LIGHTER (LIT) PROP-ONLY' -> 'LIGHTER (LIT) PROP-ONLY PROOF' (re-read, more complete)
- label: 07.props.bar-handheld/bar-assembly-magenta: 'BAR ASSEMBLY (MAGENTA' -> 'BAR ASSEMBLY (MAGENTA UNDERLIGHT)' (re-read, more complete)
- label: 07.props.bar-handheld/bar-assembly-cyan-underlight: 'BAR ASSEMBLY (CYAN UNDERLIGHT)' -> 'REFERENCE ONLY (assembled for clarity do not glue)' (closer label (cost 25 vs 1000000000))
- label: 07.props.bar-handheld/part: '' -> 'PHONE (LIT) PROP-ONLY PROOF' (was empty/garbled)
- ref: 07.props.bar-handheld/lighter-body-flame-card-phone-front-body-phone-b: section box: its 4 contents are cut as separate parts
- ref: 07.props.bar-handheld/lighter-lit-prop-only: label says 'PROOF'
- ref: 07.props.bar-handheld/bar-assembly-magenta: under the band heading 'REFERENCE ONLY (assembled for clarity do'
- ref: 07.props.bar-handheld/bar-assembly-cyan-underlight: label says 'REFERENCE'
- ref: 07.props.bar-handheld/part: label says 'PROOF'
- added: 07.props.bar-handheld/lighter-lit-prop-only
- added: 07.props.bar-handheld/bar-assembly-magenta
- added: 07.props.bar-handheld/bar-assembly-cyan-underlight
- added: 07.props.bar-handheld/part

### 07.props.dj-decks
- label: 07.props.dj-decks/track: 'TRACK' -> 'CROSSFADER TRACK' (closer label (cost 5 vs 1000000000))

### 07.props.mic-daisy-rings
- label: 07.props.mic-daisy-rings/al-microphone: 'Al MICROPHONE' -> 'Al MICROPHONE (handheld)' (re-read, more complete)
- label: 07.props.mic-daisy-rings/a2-standpole: 'A2 STANDPOLE' -> 'A2 STANDPOLE (chrome)' (re-read, more complete)
- label: 07.props.mic-daisy-rings/part-7: '' -> 'P04' (was empty/garbled)
- label: 07.props.mic-daisy-rings/b2-stem: 'B2 STEM' -> 'STEM (with leaves) (replacement)' (closer label (cost 45 vs 1000000000); old text is b3-bare-stem's)
- label: 07.props.mic-daisy-rings/pivoting-clip-stand-clip: 'PIVOTING CLIP (stand clip)' -> 'A4 PIVOTING CLIP (stand clip)' (re-read, more complete)
- label: 07.props.mic-daisy-rings/eleven: 'ELEVEN' -> 'ELEVEN PETALS (6 5)' (re-read, more complete)
- label: 07.props.mic-daisy-rings/b1-yellow: 'B1 YELLOW' -> 'B1 YELLOW CENTRE DISC' (re-read, more complete)
- label: 07.props.mic-daisy-rings/round-base-stand: 'ROUND BASE (stand)' -> 'A3 ROUND BASE (stand)' (re-read, more complete)

### 07.props.projection
- label: 07.props.projection/part-1: '' -> 'PROJECTION (painted brick)' (was empty/garbled)
- label: 07.props.projection/part-2: '' -> 'TEXTURE OVERLAY' (was empty/garbled)
- label: 07.props.projection/trucked: 'TRUCKED' -> 'HOUSE' (old text not on the sheet; label 23px-cost away)
- ref: 07.props.projection/reference-only-assembled-with-vineyard: label says 'REFERENCE'

### 07.props.speakers-vu
- label: 07.props.speakers-vu/panel-perforated: 'PANEL (perforated)' -> 'LEFT SPEAKER BOX' (closer label (cost 19 vs 169); old text is left-tracing-paper-ghost-for-silhouettes-add's)
- label: 07.props.speakers-vu/tracing-paper-backing-silhouettes-add: 'TRACING PAPER BACKING silhouettes add' -> 'RIGHT SPEAKER BOX' (closer label (cost 20 vs 1000000000); old text is frame-vu-meter-cream-with's)
- label: 07.props.speakers-vu/left-tracing-paper-ghost-for-silhouettes-add: 'LEFT TRACING PAPER ghost (for silhouettes add' -> 'LEFT GRILLE PANEL (perforated)' (closer label (cost 16 vs 27); old text is frame-vu-meter-cream-with's)
- label: 07.props.speakers-vu/large-cone: 'LARGE CONE' -> 'SMALL CONE (normal)' (closer label (cost 11 vs 1000000000); old text is right's)
- label: 07.props.speakers-vu/panel-perforated-2: 'PANEL (perforated)' -> 'RIGHT GRILLE PANEL (perforated)' (closer label (cost 16 vs 1000000000); old text is left-tracing-paper-ghost-for-silhouettes-add's)
- label: 07.props.speakers-vu/add-later: 'add later)' -> 'LARGE CONE (normal)' (old text not on the sheet; label 11px-cost away)
- label: 07.props.speakers-vu/right: 'RIGHT' -> 'LARGE CONE' (closer label (cost 33 vs 1000000000); old text is tracing-paper-backing-silhouettes-add's)
- label: 07.props.speakers-vu/frame-vu-meter-cream-with: 'FRAME VU METER (cream with' -> 'LEFT TRACING PAPER BACKING (for ghost silhouettes add later)' (old text not on the sheet; label 11px-cost away)
- label: 07.props.speakers-vu/meter-needle-vu-meter-pivot-red-with-brad-warm: 'METER NEEDLE VU METER pivot) red with brad (warm' -> 'RIGHT TRACING PAPER BACKING (for ghost silhouettes add later)' (closer label (cost 10 vs 54); old text is thin-red-with-brad-pivot's)
- label: 07.props.speakers-vu/reference-only-assembled-examples: 'REFERENCE ONLY (assembled examples)' -> 'VU METER OUTER FRAME' (closer label (cost 8 vs 50))
- label: 07.props.speakers-vu/reference-only: 'REFERENCE ONLY' -> 'VU METER BACKING (warm vellum)' (closer label (cost 16 vs 1000000000))
- label: 07.props.speakers-vu/thin-red-with-brad-pivot: '(thin red with brad pivot)' -> 'VU METER NEEDLE (thin red with brad pivot)' (re-read, more complete)

### 07.set.projection_three_roads
- label: 07.set.projection_three_roads/panel-frame-1-left: 'PANEL FRAME 1 (LEFT)' -> '(LEFT ROAD)' (old text not on the sheet; label 19px-cost away)
- label: 07.set.projection_three_roads/diagonal-streaks: '(DIAGONAL STREAKS)' -> 'RAIN OVERLAY (DIAGONAL STREAKS)' (re-read, more complete)

### 07.set.projection_vineyard
- label: 07.set.projection_vineyard/4-f: '4 (f' -> 'A3- SUN (separate card)' (was empty/garbled)
- label: 07.set.projection_vineyard/a7: 'A7-' -> 'A5 ROW 4' (was empty/garbled)
- label: 07.set.projection_vineyard/a8-row-1-di: 'A8 ROW 1 di' -> '1 (closest' (closer label (cost 96 vs 1088); old text is a7's)
- label: 07.set.projection_vineyard/a11-planted-ground-front-layer: 'A11 PLANTED GROUND (front layer)' -> 'NEAR VINE LEFT' (closer label (cost 40 vs 78))
- label: 07.set.projection_vineyard/part-11: '' -> 'A10 NEAR VINE RIGHT' (was empty/garbled)

### 08.cast.angel.body
- label: 08.cast.angel.body/bodice-three-quarter: 'BODICE THREE-QUARTER' -> 'TORSO BODICE THREE-QUARTER' (re-read, more complete)
- label: 08.cast.angel.body/torso: 'TORSO' -> 'ald' (closer label (cost 44 vs 1000000000); old text is torso-bodice-front's)
- label: 08.cast.angel.body/hip-bridge-profile-3-holes: 'HIP BRIDGE PROFILE (3 HOLES)' -> 'TORSO BODICE PROFILE' (closer label (cost 31 vs 1000000000))
- label: 08.cast.angel.body/seat-cover-front: 'SEAT COVER FRONT' -> 'HIP BRIDGE FRONT (3 HOLES)' (closer label (cost 27 vs 1000000000))
- label: 08.cast.angel.body/thigh-left: 'THIGH LEFT' -> 'THIGH LEFT (hip-knee) (hip-knee) (knee-ankle) (knee-ankle)' (closer label (cost 57 vs 1000000000); old text is shin-left's)
- label: 08.cast.angel.body/left-profile: 'LEFT PROFILE' -> 'FOOT LEFT PROFILE' (re-read, more complete)

### 08.cast.angel.faces-hands
- label: 08.cast.angel.faces-hands/l-open: 'L OPEN' -> 'EYEL L OPEN' (closer label (cost 11 vs 1000000000); old text is open's)

### 08.cast.angel.main-poses
- label: 08.cast.angel.main-poses/6-angel-above-tilted-down-tipping-basin: '6. ANGEL ABOVE TILTED DOWN TIPPING BASIN' -> '3. BACK VIEW WINGS OPEN' (old text not on the sheet; label 29px-cost away)

### 08.cast.angel.wings
- label: 08.cast.angel.wings/fully-open: 'FULLY-OPEN' -> 'LEFT FULLY-OPEN' (closer label (cost 6 vs 1000000000))
- label: 08.cast.angel.wings/fully-open-2: 'FULLY-OPEN' -> 'RIGHT FULLY-OPEN' (closer label (cost 6 vs 311))
- label: 08.cast.angel.wings/e: 'e' -> 'RIGHT DOWNSTROKE' (was empty/garbled)

### 08.cast.club.main-poses
- unclip: 08.cast.club.main-poses/fast-dance-collision-reach-1: +93 px
- unclip: 08.cast.club.main-poses/street-fan: +285 px
- unclip: 08.cast.club.main-poses/collision-reach: +239 px
- unclip: 08.cast.club.main-poses/street-fan-2: +45 px
- unclip: 08.cast.club.main-poses/fast-dance-collision-reach-2-2: +489 px

### 08.cast.club_dress.body
- label: 08.cast.club_dress.body/front: 'FRONT' -> 'TORSO (FRONT)' (closer label (cost 0 vs 1000000000); old text is foot-r's)
- label: 08.cast.club_dress.body/torso: 'TORSO' -> 'TORSO (TH E-QUARTER)' (closer label (cost 6 vs 248); old text is front's)
- label: 08.cast.club_dress.body/profile: '(PROFILE)' -> 'TORSO (PR OFILE)' (closer label (cost 2 vs 1000000000); old text is foot-profile-r's)
- label: 08.cast.club_dress.body/bridge-three-quarter: 'BRIDGE (THREE-QUARTER)' -> 'TORSO (TH E-QUARTER)' (closer label (cost 21 vs 1000000000))
- label: 08.cast.club_dress.body/hip-profile: 'HIP (PROFILE)' -> 'HIP BRIDGE' (closer label (cost 12 vs 1000000000); old text is foot-profile-r's)
- label: 08.cast.club_dress.body/seat-front: 'SEAT (FRONT)' -> 'SEAT COVER (FRONT)' (re-read, more complete)
- label: 08.cast.club_dress.body/seat-cover: 'SEAT COVER' -> 'SEAT COVER (THREE-QUARTER)' (closer label (cost 1 vs 485); old text is seat-back's)
- label: 08.cast.club_dress.body/seat-ofile: 'SEAT OFILE)' -> 'SEAT COVER (PROFILE)' (re-read, more complete)
- label: 08.cast.club_dress.body/segments-single: 'SEGMENTS (single' -> 'SKIRT PANEL (FRONT)' (closer label (cost 15 vs 96))
- label: 08.cast.club_dress.body/skirt: 'SKIRT' -> 'SKIRT PANEL (PROFILE)' (closer label (cost 17 vs 1000000000); old text is skirt-2's)
- label: 08.cast.club_dress.body/thigh: 'THIGH' -> 'THIGH L' (closer label (cost 14 vs 1000000000); old text is part-18's)
- label: 08.cast.club_dress.body/part-18: '' -> 'THIGH' (was empty/garbled)
- label: 08.cast.club_dress.body/foot: 'FOOT' -> 'FOOT (FRONT) L' (closer label (cost 15 vs 221); old text is foot-r's)
- label: 08.cast.club_dress.body/foot-r: 'FOOT R' -> 'FOOT (FRONT)' (re-read, more complete)

### 08.cast.club_dress.faces-hands
- label: 08.cast.club_dress.faces-hands/eyes: 'EYES' -> 'FRONT' (closer label (cost 2 vs 92))
- label: 08.cast.club_dress.faces-hands/eyebrows: 'EYEBROWS)' -> 'THREE- UARTER' (closer label (cost 2 vs 1000000000))
- label: 08.cast.club_dress.faces-hands/part-4: '' -> 'BACK' (was empty/garbled)
- label: 08.cast.club_dress.faces-hands/l-side: 'L SIDE' -> 'MOUTHS (INDIVIDUAL CARDS)' (closer label (cost 102 vs 1000000000); old text is glance-r's)
- label: 08.cast.club_dress.faces-hands/cards: 'CARDS)' -> 'OPEN' (closer label (cost 9 vs 1000000000); old text is open-r's)
- label: 08.cast.club_dress.faces-hands/part-12: '' -> 'SPE' (was empty/garbled)
- label: 08.cast.club_dress.faces-hands/individual: '(INDIVIDUAL' -> 'SMILE' (closer label (cost 13 vs 40); old text is l-side's)
- label: 08.cast.club_dress.faces-hands/hands: 'HANDS' -> 'OPEN PALM' (old text not on the sheet; label 14px-cost away)
- label: 08.cast.club_dress.faces-hands/part-25: '' -> 'POINT' (was empty/garbled)
- label: 08.cast.club_dress.faces-hands/cupped: 'CUPPED' -> 'CUPPED GRIP' (re-read, more complete)
- label: 08.cast.club_dress.faces-hands/grip: 'GRIP' -> 'CUPPED GRIP' (re-read, more complete)

### 08.cast.club_jacket.body
- label: 08.cast.club_jacket.body/torso: 'torso' -> 'torso profile' (closer label (cost 5 vs 1000000000); old text is torso-2's)
- label: 08.cast.club_jacket.body/torso-2: 'torso' -> 'torso back' (re-read, more complete)
- label: 08.cast.club_jacket.body/hip-back-1-waist-2-thigh: 'hip back (1 waist 2 thigh)' -> 'hip bridge back (1 waist 2 thigh)' (re-read, more complete)
- label: 08.cast.club_jacket.body/cover-back: 'cover back' -> 'seat cover back' (re-read, more complete)

### 08.cast.club_jacket.faces-hands
- label: 08.cast.club_jacket.faces-hands/eyes-and-right: 'EYES AND RIGHT' -> 'FRONT' (old text not on the sheet; label 9px-cost away)
- label: 08.cast.club_jacket.faces-hands/separate-pieces: 'SEPARATE PIECES)' -> 'THREE-QUARTER' (old text not on the sheet; label 11px-cost away)
- label: 08.cast.club_jacket.faces-hands/part-3: '' -> 'PROFILE' (was empty/garbled)
- label: 08.cast.club_jacket.faces-hands/r-2: 'R' -> 'CLOSED' (was empty/garbled)
- label: 08.cast.club_jacket.faces-hands/l-side: 'L SIDE' -> 'L SIDE GLANCE' (re-read, more complete)
- label: 08.cast.club_jacket.faces-hands/r-3: 'R' -> 'L SIDE GLANCE' (was empty/garbled)
- label: 08.cast.club_jacket.faces-hands/l-3: 'L' -> 'OPEN' (was empty/garbled)
- label: 08.cast.club_jacket.faces-hands/r-4: 'R' -> 'NEUTRAL' (was empty/garbled)
- label: 08.cast.club_jacket.faces-hands/open-palm: 'OPEN PALM' -> 'NEUTRAL' (closer label (cost 94 vs 496); old text is l-3's)

### 08.cast.club_shirt.body
- label: 08.cast.club_shirt.body/o-fr: 'O (FR' -> 'TORSO (FRONT)' (was empty/garbled)
- label: 08.cast.club_shirt.body/profile: 'PROFILE' -> 'TORSO' (closer label (cost 12 vs 1000000000); old text is shoe-r-profile's)
- label: 08.cast.club_shirt.body/hip-bridge: 'HIP BRIDGE' -> 'HIP BRIDGE (THREE-QUARTER)' (closer label (cost 6 vs 509))
- label: 08.cast.club_shirt.body/bridge-profile: 'BRIDGE (PROFILE)' -> 'HIP BRIDGE (PROFILE)' (re-read, more complete)
- label: 08.cast.club_shirt.body/bridge-back: 'BRIDGE (BACK)' -> 'TORSO (BACK)' (closer label (cost 19 vs 1000000000))
- label: 08.cast.club_shirt.body/cover-front: 'COVER (FRONT)' -> 'SEAT COVER (FRONT)' (re-read, more complete)
- label: 08.cast.club_shirt.body/three-quarter-2: '(THREE-QUARTER)' -> 'SEAT COVER (THREE-QUARTER)' (closer label (cost 8 vs 216); old text is three-quarter's)
- label: 08.cast.club_shirt.body/seat-profile: 'SEAT (PROFILE)' -> 'SEAT COVER (PROFILE)' (closer label (cost 2 vs 1000000000); old text is shoe-r-profile's)
- label: 08.cast.club_shirt.body/upper-outer-l: 'UPPER (OUTER) L' -> 'UPPER ARM L (OUTER)' (closer label (cost 11 vs 1000000000); old text is arm-outer-r's)
- label: 08.cast.club_shirt.body/arm-outer-r: 'ARM (OUTER) R' -> 'UPPER ARM (OUTER)' (closer label (cost 12 vs 1000000000); old text is forearm-outer-l's)
- label: 08.cast.club_shirt.body/r-outer: 'R (OUTER)' -> 'SHIN (OUTER)' (re-read, more complete)
- label: 08.cast.club_shirt.body/l-front: 'L (FRONT)' -> 'SHOE L (FRONT)' (re-read, more complete)

### 08.cast.club_shirt.faces-hands
- split: 08.cast.club_shirt.faces-hands/hands-individual-pieces-sleeves-props-no-no (1012x382) -> 13 parts
- split: 08.cast.club_shirt.faces-hands/neck-chain-individual-piece-assembled-reference (1012x278) -> 9 parts
- label: 08.cast.club_shirt.faces-hands/blank-face: '(BLANK FACE)' -> 'PROFILE (BLANK FACE)' (closer label (cost 14 vs 1000000000); old text is front-blank-face's)
- label: 08.cast.club_shirt.faces-hands/blank: '(BLANK)' -> 'BACK (BLANK)' (re-read, more complete)
- label: 08.cast.club_shirt.faces-hands/eyer-d: 'EYER =D' -> 'EYE (OPEN)' (closer label (cost 4 vs 228); old text is eye-r-side's)
- label: 08.cast.club_shirt.faces-hands/neutral: '(NEUTRAL)' -> 'MOUTHS (individual pieces)' (closer label (cost 43 vs 1000000000); old text is brow-r-neutral's)
- label: 08.cast.club_shirt.faces-hands/l-side: 'L (SIDE)' -> 'EYE L (SIDE)' (re-read, more complete)
- label: 08.cast.club_shirt.faces-hands/cupped-grip-r: 'CUPPED GRIP R' -> 'a CUPPED CUPPED GRIP' (re-read, more complete)
- ref: 08.cast.club_shirt.faces-hands/hands-individual-pieces-sleeves-props-no-no: section box: its 13 contents are cut as separate parts
- ref: 08.cast.club_shirt.faces-hands/neck-chain-individual-piece-assembled-reference: section box: its 9 contents are cut as separate parts
- added: 08.cast.club_shirt.faces-hands/eye-l-open
- added: 08.cast.club_shirt.faces-hands/eyer-d
- added: 08.cast.club_shirt.faces-hands/neutral
- added: 08.cast.club_shirt.faces-hands/mouth-smile
- added: 08.cast.club_shirt.faces-hands/brow-r-neutral
- added: 08.cast.club_shirt.faces-hands/brow-l-neutral
- added: 08.cast.club_shirt.faces-hands/l-closed-eye
- added: 08.cast.club_shirt.faces-hands/brow-r-raised
- added: 08.cast.club_shirt.faces-hands/brow-l-raised
- added: 08.cast.club_shirt.faces-hands/th-open
- added: 08.cast.club_shirt.faces-hands/mout-speak
- added: 08.cast.club_shirt.faces-hands/l-side
- added: 08.cast.club_shirt.faces-hands/eye-r-side
- added: 08.cast.club_shirt.faces-hands/wave-r
- added: 08.cast.club_shirt.faces-hands/wave-l
- added: 08.cast.club_shirt.faces-hands/open-palm-fist-r-l
- added: 08.cast.club_shirt.faces-hands/point-l
- added: 08.cast.club_shirt.faces-hands/palm-open-l
- added: 08.cast.club_shirt.faces-hands/cupped-grip-r
- added: 08.cast.club_shirt.faces-hands/cupped-grip-l
- added: 08.cast.club_shirt.faces-hands/point-r
- added: 08.cast.club_shirt.faces-hands/fist-r

### 08.fx.soul-weather
- label: 08.fx.soul-weather/part-1: '' -> 'BACKLIGHT' (was empty/garbled)
- label: 08.fx.soul-weather/d36f46: '#d36f46' -> 'HEAD SPARK' (was empty/garbled)
- label: 08.fx.soul-weather/curls-3: 'CURLS (3)' -> 'HT OVAL' (closer label (cost 36 vs 70); old text is part-14's)
- label: 08.fx.soul-weather/part-14: '' -> 'CURLS (3)' (was empty/garbled)
- ref: 08.fx.soul-weather/part-1: label fragment (printed words)

### 08.hero.marquee
- label: 08.hero.marquee/marquee-lettering-strip: 'MARQUEE LETTERING STRIP' -> '(SEPARATE)' (old text not on the sheet; label 32px-cost away)
- label: 08.hero.marquee/poster-panel-2: 'POSTER PANEL 2' -> 'MARQUEE' (closer label (cost 45 vs 1000000000); old text is poster-panel-4's)
- label: 08.hero.marquee/poster-panel-3: 'POSTER PANEL 3' -> '(SEPARATE)' (closer label (cost 43 vs 1000000000); old text is poster-panel-4's)

### 08.hero.marquee.interior
- label: 08.hero.marquee.interior/separate: 'SEPARATE' -> 'LOBBY RIGHT WALL (PINK)' (closer label (cost 21 vs 1000000000); old text is corridor-middle-wall-deep-red's)
- label: 08.hero.marquee.interior/cyan: '(CYAN)' -> 'EMPTY)' (closer label (cost 55 vs 409); old text is bench-a-cyan's)
- label: 08.hero.marquee.interior/auditorium-rear-wall: 'AUDITORIUM REAR WALL' -> '3. AUDITORIUM (all pieces separate)' (closer label (cost 10 vs 156); old text is exit-sign-red-2's)
- label: 08.hero.marquee.interior/exit-sign-red-2: 'EXIT SIGN (RED)' -> 'AUDITORIUM REAR WALL (OPENING EMPTY)' (closer label (cost 20 vs 1000000000); old text is exit-sign-red's)
- ref: 08.hero.marquee.interior/auditorium-floor-assembled-reference: label says 'ASSEMBLED'

### 08.props.basins
- label: 08.props.basins/wi: 'wi' -> 'B1' (was empty/garbled)
- label: 08.props.basins/b2-2: 'B2' -> 'W2' (closer label (cost 9 vs 19); old text is b2's)
- label: 08.props.basins/b3-2: 'B3' -> 'W3' (closer label (cost 9 vs 19); old text is b3's)
- label: 08.props.basins/13: '13' -> 'I3' (old text not on the sheet; label 5px-cost away)
- label: 08.props.basins/16-2: '16' -> 'P3C' (closer label (cost 11 vs 25); old text is 16's)

### 08.props.moons-laundry
- label: 08.props.moons-laundry/4: '$4' -> 'S4' (was empty/garbled)
- label: 08.props.moons-laundry/6: '$6' -> 'S6' (was empty/garbled)
- label: 08.props.moons-laundry/hang: 'HANG' -> 'LAUNDRY LINES (2x)' (closer label (cost 59 vs 1494))
- label: 08.props.moons-laundry/snap: 'SNAP' -> 'HANG' (closer label (cost 22 vs 653))
- label: 08.props.moons-laundry/hang-3: 'HANG' -> 'TEAL (2' (closer label (cost 28 vs 1000000000))
- label: 08.props.moons-laundry/4x: '(4x)' -> 'C2' (closer label (cost 6 vs 1000000000); old text is 4's)
- label: 08.props.moons-laundry/part-22: '' -> 'C3' (was empty/garbled)
- label: 08.props.moons-laundry/assembled-laundry-line: 'ASSEMBLED LAUNDRY LINE' -> 'Lit' (closer label (cost 71 vs 149); old text is hang's)
- label: 08.props.moons-laundry/mi: 'Mi' -> 'LAUNDRY LINE ASSEMBLED (REFERENCE ONLY)' (was empty/garbled)
- label: 08.props.moons-laundry/mi-2: 'Mi' -> 'M1' (was empty/garbled)
- label: 08.props.moons-laundry/part-29: '' -> 'M2' (was empty/garbled)
- ref: 08.props.moons-laundry/laundry-line-assembled-reference-only: label says 'ASSEMBLED'
- ref: 08.props.moons-laundry/mi: label says 'ASSEMBLED'
- ref: 08.props.moons-laundry/mi-2: under the band heading 'LAUNDRY LINE ASSEMBLED (REFERENCE ONLY)'
- ref: 08.props.moons-laundry/m2: under the band heading 'LAUNDRY LINE ASSEMBLED (REFERENCE ONLY)'
- ref: 08.props.moons-laundry/m3: under the band heading 'LAUNDRY LINE ASSEMBLED (REFERENCE ONLY)'
- ref: 08.props.moons-laundry/part-29: under the band heading 'LAUNDRY LINE ASSEMBLED (REFERENCE ONLY)'
- ref: 08.props.moons-laundry/08-props-moons-laundry: under the band heading 'LAUNDRY LINE ASSEMBLED (REFERENCE ONLY)'

### 08.set.atlantis_aerial
- label: 08.set.atlantis_aerial/06-cloud-veil-top: '06 CLOUD VEIL TOP' -> 'CLOUD WISP C' (closer label (cost 57 vs 283))
- ref: 08.set.atlantis_aerial/assembled-reference: label says 'ASSEMBLED'

### 08.set.equator_plain
- label: 08.set.equator_plain/independent: 'independent;' -> 'EQUATOR TICKS (x6)' (closer label (cost 26 vs 40); old text is assembled's)
- label: 08.set.equator_plain/assembled: 'assembled' -> 'All working parts independent; assembled proof reference only.' (old text not on the sheet; label 26px-cost away)
- label: 08.set.equator_plain/assembled-2: 'assembled' -> 'EQUATOR TICKS (x6)' (old text not on the sheet; label 16px-cost away)
- label: 08.set.equator_plain/proof-is: 'proof is' -> 'EQUATOR TICKS (x6)' (old text not on the sheet; label 31px-cost away)
- ref: 08.set.equator_plain/reference: label says 'reference'

### 08.set.rooftop_club
- label: 08.set.rooftop_club/part-3: '' -> 'A' (was empty/garbled)
- label: 08.set.rooftop_club/part-4: '' -> 'STROBE TOWER A' (was empty/garbled)
- label: 08.set.rooftop_club/ledge: 'LEDGE' -> 'DISC-SPIRE SKYLINE' (closer label (cost 101 vs 115))
- label: 08.set.rooftop_club/part-9: '' -> 'STROBE TOWER A' (was empty/garbled)
- label: 08.set.rooftop_club/tile-floor: 'TILE FLOOR' -> 'RAILING' (closer label (cost 45 vs 210))
- ref: 08.set.rooftop_club/part-11: label fragment (printed words)

### 09.fx.call-abyss
- recut: 09.fx.call-abyss/r2: framed panel [1183, 427, 155, 104] -> figure [1185, 438, 151, 91]
- recut: 09.fx.call-abyss/r3: framed panel [1347, 423, 176, 107] -> figure [1358, 436, 154, 86]
- label: 09.fx.call-abyss/harbor-abyss-black-the: 'HARBOR ABYSS black the' -> 'INK' (closer label (cost 34 vs 60); old text is t1-t2-3-exhaze-dissolve-off-tissue-haze-that-dri's)
- label: 09.fx.call-abyss/c1-a: 'C1-A' -> 'CALL 1 CREST UP (TOWARD MOON) rises in an arc toward the moon' (was empty/garbled)
- label: 09.fx.call-abyss/c2-a-cream: 'C2-A CREAM' -> 'CALL 2 SAG DOWN (TOWARD WATER) dips downward toward the water' (closer label (cost 20 vs 30))
- label: 09.fx.call-abyss/tears-5-five-tiny-teardrops-ride-the-cord-and-pe: 'TEARS (5) five tiny teardrops ride the cord and peel off different at' -> 'aes' (closer label (cost 24 vs 44))
- label: 09.fx.call-abyss/water-ripples-3: 'WATER RIPPLES (3)' -> 'INK' (closer label (cost 33 vs 68))
- label: 09.fx.call-abyss/t1-t2-3-exhaze-dissolve-off-tissue-haze-that-dri: 'T1 T2 (3) EXHAZE DISSOLVE off tissue haze that drifts grey' -> 'HARBOR ABYSS a black hole in the water; no ring' (closer label (cost 42 vs 60))
- label: 09.fx.call-abyss/ri: 'Ri' -> 'R1' (was empty/garbled)

### 09.hero.canopy
- label: 09.hero.canopy/part-7: '' -> '4' (was empty/garbled)
- label: 09.hero.canopy/part-13: '' -> '3 (1 pc)' (was empty/garbled)
- label: 09.hero.canopy/part-15: '' -> '(1 pc)' (was empty/garbled)

### 09.props.moon-sun
- label: 09.props.moon-sun/cream-disc-with-three-soft-grey-maria-and-fine-g: 'cream disc with three soft grey maria and fine grey rim' -> 'MOON (FULL) cream disc with three soft grey maria and fine grey rim' (re-read, more complete)
- label: 09.props.moon-sun/moon-low-horizon-smaller-replacement-disc-look: 'MOON (LOW HORIZON) smaller replacement disc look' -> 'MOON (LOW HORIZON) smaller replacement disc same look' (re-read, more complete)
- label: 09.props.moon-sun/sun-half-up-larger-half-disc-replacement: 'SUN (HALF-UP) larger half disc replacement' -> 'HARBOR SUN (HALF-UP) larger half disc replacement' (re-read, more complete)
- label: 09.props.moon-sun/reflection-road-left-branch: 'REFLECTION ROAD LEFT BRANCH' -> 'REFLECTION ROAD LEFT BRANCH vertical card' (re-read, more complete)
- label: 09.props.moon-sun/road-straight: 'ROAD STRAIGHT' -> 'REFLECTION ROAD STRAIGHT vertical card' (re-read, more complete)
- label: 09.props.moon-sun/reflection-road-right-branch: 'REFLECTION ROAD RIGHT BRANCH' -> 'REFLECTION ROAD RIGHT BRANCH vertical card' (re-read, more complete)
- label: 09.props.moon-sun/harbor-lamp-separate-vertical: 'HARBOR LAMP separate vertical' -> 'HARBOR LAMP REFLECTIONS four separate vertical streak cards amber' (re-read, more complete)
- label: 09.props.moon-sun/reflections-streak-cards: 'REFLECTIONS streak cards' -> 'HARBOR LAMP REFLECTIONS four separate vertical streak cards amber' (closer label (cost 26 vs 1157); old text is road-straight's)

### 09.props.phonebooth
- label: 09.props.phonebooth/steel-mullion: '(STEEL MULLION)' -> 'FRONT OPEN FRAME (STEEL MULLION)' (re-read, more complete)
- label: 09.props.phonebooth/hinge-holes: '(HINGE HOLES)' -> 'DOOR LEFT (HINGE HOLES)' (re-read, more complete)
- label: 09.props.phonebooth/door-hinge-holes: 'DOOR (HINGE HOLES)' -> 'DOOR RIGHT (HINGE HOLES)' (closer label (cost 3 vs 167); old text is hinge-holes's)
- label: 09.props.phonebooth/glass-insert-right-clear: 'GLASS INSERT RIGHT (CLEAR)' -> 'DOOR GLASS INSERT RIGHT (CLEAR)' (re-read, more complete)
- label: 09.props.phonebooth/cream-yellow: '(CREAM YELLOW)' -> 'CEILING LIGHT ON (CREAM YELLOW)' (re-read, more complete)
- label: 09.props.phonebooth/light-off-grey: 'LIGHT OFF (GREY)' -> 'CEILING LIGHT OFF (GREY)' (re-read, more complete)
- label: 09.props.phonebooth/steel-grey: '(STEEL GREY)' -> 'DOOTH FLOOR (STEEL GREY)' (re-read, more complete)
- label: 09.props.phonebooth/pavement-grey: 'PAVEMENT (GREY)' -> 'PAVEMENT LIGHT WEDGE (GREY)' (re-read, more complete)
- label: 09.props.phonebooth/curb-grey: 'CURB (GREY)' -> 'CURB WEDGE (GREY)' (re-read, more complete)

### 09.props.phones-chair
- label: 09.props.phones-chair/part-2: '' -> 'ARMOURED STEEL COILED CORD' (was empty/garbled)
- label: 09.props.phones-chair/receiver: 'RECEIVER' -> 'RECEIVER (CREAM)' (re-read, more complete)
- label: 09.props.phones-chair/coiled-cord: 'COILED CORD' -> 'COILED CORD (CREAM)' (re-read, more complete)
- label: 09.props.phones-chair/front-arm-overlay: 'FRONT ARM OVERLAY' -> 'FRONT ARM OVERLAY (ONE, LEFT/RIGHT)' (re-read, more complete)

### 09.props.suitcases-notice
- label: 09.props.suitcases-notice/open-ard: 'OPEN ARD' -> 'OPEN CARD' (closer label (cost 20 vs 911); old text is case's)
- label: 09.props.suitcases-notice/case: 'CASE' -> 'OPEN CARD' (old text not on the sheet; label 1px-cost away)
- label: 09.props.suitcases-notice/part-7: '' -> 'HANDLE TAB' (was empty/garbled)
- label: 09.props.suitcases-notice/chalk-overlay-with-chalk-overlay: 'CHALK OVERLAY (WITH CHALK OVERLAY' -> 'BOARD CARD' (closer label (cost 12 vs 273); old text is chalk-overlay-1-with-time's)
- ref: 09.props.suitcases-notice/right-1-assembled: label says 'ASSEMBLED'

### 09.set.atlantis_club_sidewalk
- label: 09.set.atlantis_club_sidewalk/03-b: '03 B' -> 'POWER STRIP A' (was empty/garbled)
- label: 09.set.atlantis_club_sidewalk/06-shopfront-c: '06 SHOPFRONT C' -> 'STRIP' (closer label (cost 67 vs 351); old text is 05-shopfront-b's)

### 09.set.atlantis_harbor_street
- label: 09.set.atlantis_harbor_street/part-3: '' -> 'SKY 2 middle band' (was empty/garbled)
- label: 09.set.atlantis_harbor_street/part-4: '' -> 'SKY 3 lower band' (was empty/garbled)
- label: 09.set.atlantis_harbor_street/a: 'A' -> 'STRIP (left section)' (was empty/garbled)
- label: 09.set.atlantis_harbor_street/town-lamp: 'TOWN LAMP' -> 'JIB' (old text not on the sheet; label 22px-cost away)
- ref: 09.set.atlantis_harbor_street/assembled-proof-is-reference-only: label says 'Assembled'

### 09.set.harbor_path_east
- label: 09.set.harbor_path_east/part-3: '' -> 'SKY 2 grey-violet' (was empty/garbled)
- label: 09.set.harbor_path_east/part-4: '' -> 'SKY 3 dusty rose' (was empty/garbled)
- label: 09.set.harbor_path_east/part-5: '' -> 'SKY 4 pale gold' (was empty/garbled)
- label: 09.set.harbor_path_east/part-6: '' -> 'SKY apricot (near horizon)' (was empty/garbled)
- label: 09.set.harbor_path_east/left-top: 'LEFT top' -> 'with perspective (look east)' (old text not on the sheet; label 38px-cost away)
- label: 09.set.harbor_path_east/part-8: '' -> 'PATH EDGE LEFT low stone wall top' (was empty/garbled)
- label: 09.set.harbor_path_east/part-10: '' -> 'WORN FOOTPRINTS (x4)' (was empty/garbled)
- label: 09.set.harbor_path_east/reflection-white-gold-reflection-strip-separate-: 'REFLECTION white-gold reflection strip (separate insert) water' -> 'SUN-ROAD REFLECTION white-gold water reflection strip (separate insert)' (re-read, more complete)

### 09.set.mother_living_room
- label: 09.set.mother_living_room/with-corner: '(with corner)' -> 'LEFT' (closer label (cost 23 vs 1604))

### 10.fx.ride-light
- label: 10.fx.ride-light/left-sunrise: 'LEFT SUNRISE' -> 'LEFT SUNRISE RIGHT SUNRISE' (closer label (cost 46 vs 1000000000); old text is left-neon's)
- label: 10.fx.ride-light/right-sunrise: 'RIGHT SUNRISE' -> 'LEFT SUNRISE RIGHT SUNRISE' (closer label (cost 43 vs 1000000000); old text is right-neon's)
- label: 10.fx.ride-light/separate-parallax-pulse-and-timing-dawn-replacem: 'separate parallax pulse and timing, dawn replacement need animation' -> 'Use separate Poet sunglasses; pulse timing, parallax and dawn replacement need animation.' (re-read, more complete)

### 10.hero.shadowpool
- label: 10.hero.shadowpool/mid-frame: '(MID FRAME' -> 'FRAME 1 di' (old text not on the sheet; label 2px-cost away)
- label: 10.hero.shadowpool/4-far: '4 (FAR)' -> 'FRAME 4 (FAR)' (re-read, more complete)
- label: 10.hero.shadowpool/part-5: '' -> 'REFLECTION 1' (was empty/garbled)
- label: 10.hero.shadowpool/frame-mid-1-2: 'FRAME (MID 1)' -> 'REFLECTION' (closer label (cost 13 vs 39); old text is frame-mid-1's)

### 10.props.bike-ride-views
- label: 10.props.bike-ride-views/4-top-view-insert-fuel-panel-top-close-up-view: '4. TOP VIEW INSERT FUEL PANEL (TOP CLOSE-UP) VIEW' -> 'SADDLE PANEL (BACK VIEW)' (old text not on the sheet; label 35px-cost away)
- label: 10.props.bike-ride-views/fuel-panel-top-close-up-view: 'FUEL PANEL (TOP CLOSE-UP) VIEW' -> '4. TOP VIEW INSERT' (old text not on the sheet; label 33px-cost away)
- label: 10.props.bike-ride-views/chassis-engine: 'CHASSIS ENGINE' -> 'CHASSIS (FRONT VIEW)' (old text not on the sheet; label 12px-cost away)
- label: 10.props.bike-ride-views/3-4-back-view: '(3/4 BACK VIEW)' -> 'FUEL TANK PANEL (3/4' (closer label (cost 5 vs 1000000000); old text is saddle-panel-2's)
- label: 10.props.bike-ride-views/chassis-engine-view: 'CHASSIS ENGINE VIEW)' -> 'CHASSIS (BACK VIEW)' (closer label (cost 23 vs 1000000000); old text is chassis-engine's)
- label: 10.props.bike-ride-views/saddle-panel: 'SADDLE PANEL' -> 'SADDLE PANEL (FRONT VIEW)' (closer label (cost 10 vs 1000000000); old text is 4-top-view-insert-fuel-panel-top-close-up-view's)
- label: 10.props.bike-ride-views/front-view: '(FRONT VIEW)' -> 'WHEEL' (closer label (cost 9 vs 1000000000); old text is fuel-tank-view's)
- label: 10.props.bike-ride-views/front-wheel: 'FRONT WHEEL' -> 'FRONT WHEEL REAR SPOKE' (closer label (cost 22 vs 1000000000); old text is fuel-tank-view's)
- label: 10.props.bike-ride-views/rear-front-view: 'REAR (FRONT VIEW)' -> 'FRONT WHEEL REAR SPOKE' (closer label (cost 26 vs 180); old text is fuel-tank-view's)
- label: 10.props.bike-ride-views/front-wheel-2: 'FRONT WHEEL' -> 'EL VIEW) 3/4' (closer label (cost 28 vs 1000000000); old text is fuel-tank-view's)
- label: 10.props.bike-ride-views/3-4-back-view-4: '(3/4 BACK VIEW)' -> 'SPOKE' (closer label (cost 62 vs 1000000000); old text is saddle-panel-2's)
- label: 10.props.bike-ride-views/rear-2: 'REAR' -> 'REAR WHEEL (3/4 BAC VIEW) (3/4' (closer label (cost 46 vs 1000000000); old text is rear-wheel-back-view's)
- label: 10.props.bike-ride-views/wheel-back-view: 'WHEEL (BACK VIEW)' -> 'FRONT RING' (closer label (cost 9 vs 1000000000); old text is saddle-panel-2's)
- label: 10.props.bike-ride-views/front-wheel-spoke-back-view: 'FRONT WHEEL SPOKE (BACK VIEW)' -> 'CHASSIS (BACK VIEW)' (closer label (cost 46 vs 1000000000); old text is front-fork-back-view's)
- label: 10.props.bike-ride-views/rear-3: 'REAR' -> 'REAR WHEEL WHEEL' (re-read, more complete)
- label: 10.props.bike-ride-views/front-view-2: '(FRONT VIEW)' -> 'WHEEL' (closer label (cost 27 vs 1000000000); old text is fuel-tank-view's)
- label: 10.props.bike-ride-views/handlebar: 'HANDLEBAR' -> 'HANDLEBAR (FRONT VIEW)' (closer label (cost 14 vs 1000000000); old text is handlebar-3-4-view-back's)
- label: 10.props.bike-ride-views/front-3-4-view-back: 'FRONT (3/4 VIEW) BACK' -> 'FRONT FORK (3/4' (closer label (cost 3 vs 1000000000); old text is fuel-tank-view's)
- ref: 10.props.bike-ride-views/3-4-back-view-2: label fragment (printed words)
- ref: 10.props.bike-ride-views/front-view-3: label fragment (printed words)

### 10.props.bike-skeleton
- label: 10.props.bike-skeleton/8-7-front-tyre-ring: '8. 7. FRONT TYRE RING' -> '1. FRAME' (closer label (cost 64 vs 1000000000))
- label: 10.props.bike-skeleton/10-rear-disc-axle-pivot: '10. REAR DISC AXLE PIVOT' -> '9. REAR TYRE' (closer label (cost 27 vs 83); old text is 10-rear-disc-axle-pivot-2's)
- label: 10.props.bike-skeleton/10-rear-disc-axle-pivot-2: '10. REAR DISC AXLE PIVOT' -> '10. REAR SPOKED DISC AXLE PIVOT' (re-read, more complete)

### 10.props.tree-dawn-sign
- label: 10.props.tree-dawn-sign/c1-sign-panel: 'C1 sign panel' -> 'C1 sign panel (empty)' (re-read, more complete)
- label: 10.props.tree-dawn-sign/c6-leg-left: 'C6 leg (left)' -> 'glyph C6 leg C7 leg (left) (right)' (old text not on the sheet; label 20px-cost away)
- label: 10.props.tree-dawn-sign/c7-leg-right: 'C7 leg (right)' -> 'glyph C6 leg C7 leg (left) (right)' (old text not on the sheet; label 33px-cost away)
- label: 10.props.tree-dawn-sign/c2-left-arrow: 'C2 left arrow' -> "C2 left arrow C3 digit '8' cA digit (x1)" (re-read, more complete)
- label: 10.props.tree-dawn-sign/c3-digit-8-x1: "C3 digit '8' (x1)" -> "C2 left arrow C3 digit '8' cA digit (x1)" (old text not on the sheet; label 8px-cost away)
- ref: 10.props.tree-dawn-sign/branching: label fragment (printed words)
- ref: 10.props.tree-dawn-sign/part-4: label fragment (printed words)
- ref: 10.props.tree-dawn-sign/c2-left: label fragment (printed words)

### 10.set.atlantis_streets
- label: 10.set.atlantis_streets/part-2: '' -> 'SKY' (was empty/garbled)
- label: 10.set.atlantis_streets/low: '(LOW)' -> 'STAR' (closer label (cost 36 vs 1000000000); old text is rooftop-layer-1-far-low's)
- label: 10.set.atlantis_streets/rooftop-layer-1-far-low-2: 'ROOFTOP LAYER 1 FAR (LOW)' -> 'STACK 1 (INDUSTRIAL)' (old text not on the sheet; label 14px-cost away)

### 10.set.mountain_road
- label: 10.set.mountain_road/far-ridge-back-layer-lighter-distant-mountains: 'FAR RIDGE (back layer) lighter, distant mountains' -> 'SKY (front) plain sky card' (closer label (cost 45 vs 52))
- label: 10.set.mountain_road/y-fork-road-ground-base-asphalt-surface: 'Y-FORK ROAD (ground base) asphalt surface' -> 'Y-FORK ROAD (ground base) plain asphalt surface' (re-read, more complete)
- label: 10.set.mountain_road/all-working: 'All working' -> '(2 separate strips)' (old text not on the sheet; label 29px-cost away)

### 11.fx.fog-halo
- label: 11.fx.fog-halo/dash-right: 'DASH RIGHT' -> 'DASH LEFT' (closer label (cost 89 vs 133); old text is dash-right-g-note's)

### 11.fx.light
- label: 11.fx.light/shadow-mask: 'SHADOW MASK' -> 'RAY.03' (closer label (cost 19 vs 1000000000); old text is clearing-above-ridge's)
- label: 11.fx.light/ray-06: 'RAY.06' -> 'RAY.05' (closer label (cost 20 vs 138); old text is temple's)
- label: 11.fx.light/long: '(LONG)' -> 'RAY.07' (closer label (cost 21 vs 55); old text is staging-proof-2-sun's)
- label: 11.fx.light/shadow-mid: 'SHADOW (MID)' -> 'RAY.09' (closer label (cost 17 vs 66); old text is clearing-above-ridge's)
- label: 11.fx.light/shadow-short: 'SHADOW (SHORT)' -> 'RAY.11' (closer label (cost 19 vs 75); old text is temple-shadow-short's)
- label: 11.fx.light/valley: 'VALLEY' -> 'RAY.02' (closer label (cost 20 vs 50); old text is staging-proof-1-sun-behind-ridge-not-visible's)
- label: 11.fx.light/temple: 'TEMPLE' -> 'RAY.06' (closer label (cost 9 vs 1000000000); old text is temple-shadow-short's)
- label: 11.fx.light/temple-2: 'TEMPLE' -> 'RAY.08' (closer label (cost 18 vs 1000000000); old text is temple-shadow-short's)
- label: 11.fx.light/temple-3: 'TEMPLE' -> 'RAY.10' (closer label (cost 21 vs 84); old text is temple-shadow-short's)
- label: 11.fx.light/staging-proof-1-sun-behind-ridge-not-visible: 'STAGING PROOF 1 SUN BEHIND RIDGE (NOT VISIBLE)' -> 'VALLEY' (closer label (cost 53 vs 1000000000); old text is 11-fx-light's)
- label: 11.fx.light/staging-proof-2-sun: 'STAGING PROOF 2 SUN' -> '(LONG)' (closer label (cost 29 vs 1000000000))
- label: 11.fx.light/clearing-above-ridge: 'CLEARING ABOVE RIDGE' -> 'SHADOW (MID)' (old text not on the sheet; label 19px-cost away)
- label: 11.fx.light/11-fx-light: '11.fx.light' -> 'STAGING PROOF SUN CLEARING ABOVE' (old text not on the sheet; label 38px-cost away)
- ref: 11.fx.light/staging-proof-1-sun-behind-ridge-not-visible-2: label says 'PROOF'
- ref: 11.fx.light/11-fx-light: label says 'PROOF'

### 11.hero.clocktower
- label: 11.hero.clocktower/large-cog: 'Large cog' -> 'COG.01 Large cog' (re-read, more complete)

### 11.hero.steps
- label: 11.hero.steps/stair-tread: 'stair tread' -> 'TREAD.O2 stair tread' (re-read, more complete)
- label: 11.hero.steps/stair-tread-2: 'stair tread' -> 'TREAD.0O4 stair tread' (closer label (cost 33 vs 1000000000); old text is stair-tread's)
- label: 11.hero.steps/stair-tread-3: 'stair tread' -> 'TREAD.O6 stair tread' (closer label (cost 36 vs 82); old text is stair-tread's)

### 11.props.inlays-lantern
- label: 11.props.inlays-lantern/seam: 'SEAM' -> 'GLAZIER SEAM (STRAIGHT)' (old text not on the sheet; label 9px-cost away)

### 11.props.journal
- label: 11.props.journal/j1-closed-journal: 'J1 closed journal' -> 'J1 closed journal FRONT' (re-read, more complete)
- label: 11.props.journal/j2-closed-journal: 'J2 closed journal' -> 'J2 closed journal SPINE profile' (closer label (cost 10 vs 1000000000); old text is j3-closed-journal's)
- label: 11.props.journal/j3-closed-journal: 'J3 closed journal' -> 'J3 closed journal BACK' (re-read, more complete)
- label: 11.props.journal/j4-open-leather-flat-cover: 'J4 open leather flat cover' -> 'J4 open leather cover flat with centre brass hinge' (re-read, more complete)
- label: 11.props.journal/left-page-block: 'left page block' -> 'J5 left page block' (re-read, more complete)
- label: 11.props.journal/right-page-block: 'right page block' -> 'J6 right page block' (re-read, more complete)
- label: 11.props.journal/j7-loose-page: 'J7 loose page' -> 'J7 loose page with wristless grip tab' (old text not on the sheet; label 17px-cost away)
- label: 11.props.journal/j8-turned-page-overlay: 'J8 turned-page overlay' -> 'J8 turned-page overlay curled at upper corner' (re-read, more complete)

### 11.props.parked-motorcycle
- label: 11.props.parked-motorcycle/view: 'VIEW)' -> 'PARKED REAR (ALTERNATIVE VIEW)' (re-read, more complete)
- label: 11.props.parked-motorcycle/9: '9.' -> '3' (closer label (cost 6 vs 21))
- label: 11.props.parked-motorcycle/kickstand-11-props-parked-motorcycle: 'KICKSTAND 11.props.parked-motorcycle' -> '4. FRONT' (old text not on the sheet; label 36px-cost away)
- label: 11.props.parked-motorcycle/5-tank: '5. TANK' -> '5. FUEL TANK' (re-read, more complete)
- ref: 11.props.parked-motorcycle/part-3: label fragment (printed words)

### 11.props.ruin
- unclip: 11.props.ruin/arch-opening-cut: +95 px
- label: 11.props.ruin/part-1: '' -> 'TOP LEFT: BROKEN WALL' (was empty/garbled)
- label: 11.props.ruin/arch-opening-cut: 'ARCH (OPENING cuT' -> 'TOP CENTRE: ARCH (OPENING OUT)' (re-read, more complete)
- label: 11.props.ruin/right: 'RIGHT:' -> 'TOP RIGHT: BROKEN WALL' (re-read, more complete)
- label: 11.props.ruin/right-2: 'RIGHT:' -> 'STONE.05' (closer label (cost 9 vs 66); old text is right's)
- label: 11.props.ruin/part-8: '' -> 'STONE.04' (was empty/garbled)
- label: 11.props.ruin/part-9: '' -> 'STONE.06' (was empty/garbled)
- label: 11.props.ruin/floor-strip-separate-card: 'FLOOR STRIP (SEPARATE CARD)' -> 'RUBBLE FLOOR STRIP (SEPARATE CARD)' (re-read, more complete)
- label: 11.props.ruin/1-wet-dark: '1: WET, DARK' -> 'STATEPROOF 1: WET, DARK RUBBLE' (re-read, more complete)
- label: 11.props.ruin/stateproof-2-drying-in-sun: 'STATEPROOF 2: DRYING IN SUN' -> 'STATEPROOF 2: DEW DRYING IN SUN' (re-read, more complete)
- ref: 11.props.ruin/1-wet-dark: label says 'STATEPROOF'
- ref: 11.props.ruin/stateproof-2-drying-in-sun: label says 'STATEPROOF'
- ref: 11.props.ruin/stateproof-3-rubble-under-three-white-11-props-r: label says 'STATEPROOF'

### 11.props.temple.arrival.beams
- label: 11.props.temple.arrival.beams/part-3: '' -> 'BEAM.02' (was empty/garbled)
- label: 11.props.temple.arrival.beams/part-5: '' -> 'BEAM.03' (was empty/garbled)
- label: 11.props.temple.arrival.beams/part-7: '' -> 'BEAM.04' (was empty/garbled)
- label: 11.props.temple.arrival.beams/part-9: '' -> 'BEAM.05' (was empty/garbled)
- label: 11.props.temple.arrival.beams/part-11: '' -> 'BEAM.06' (was empty/garbled)
- label: 11.props.temple.arrival.beams/part-13: '' -> 'BEAM.07' (was empty/garbled)
- label: 11.props.temple.arrival.beams/100-states-11-props-temple-whole-align: '100% states: 11.props.temple.whole; align' -> '100% states: 11.props.temple.whole; align after extraction.' (re-read, more complete)

### 11.props.temple.arrival.roof-finial
- label: 11.props.temple.arrival.roof-finial/right-slope: '(right slope)' -> 'PEDIMENT.R (30% DOTS) (right slope' (re-read, more complete)
- label: 11.props.temple.arrival.roof-finial/pediment-r-right-slope: 'PEDIMENT.R (right slope' -> 'PEDIMENT.R (70% DOTS) (right slope)' (closer label (cost 0 vs 485); old text is right-slope's)
- label: 11.props.temple.arrival.roof-finial/finial-70: 'FINIAL (70%' -> '(70% DOTS)' (closer label (cost 11 vs 1006); old text is finial-30-dots's)
- label: 11.props.temple.arrival.roof-finial/complete-finial-reference: 'COMPLETE FINIAL reference' -> 'COMPLETE FINIAL (100% reference only)' (re-read, more complete)
- ref: 11.props.temple.arrival.roof-finial/complete-finial-reference: label says 'reference'
- ref: 11.props.temple.arrival.roof-finial/reference-only-finial-with-gold: label says 'REFERENCE'
- ref: 11.props.temple.arrival.roof-finial/part-9: label fragment (printed words)

### 11.props.temple.states
- recut: 11.props.temple.states/1-only: framed panel [17, 87, 495, 355] -> figure [21, 352, 487, 86]
- recut: 11.props.temple.states/2: framed panel [522, 87, 494, 355] -> figure [534, 333, 470, 97]
- label: 11.props.temple.states/1-only: '1. ONLY' -> '1. SITE ONLY' (re-read, more complete)
- label: 11.props.temple.states/1-only-2: '1. ONLY' -> '4. COMPLETE' (closer label (cost 13 vs 38); old text is 1-only's)
- label: 11.props.temple.states/3-columns-beams-2: '3. COLUMNS BEAMS' -> '6. SUNLIT' (old text not on the sheet; label 13px-cost away)

### 11.props.temple.whole
- label: 11.props.temple.whole/right-slope: '(right slope)' -> 'BEAM.06' (closer label (cost 77 vs 1000000000))

### 11.set.calm_sea
- label: 11.set.calm_sea/part-2: '' -> 'CLOUD.O1 Thin low cloud streak' (was empty/garbled)
- label: 11.set.calm_sea/part-3: '' -> 'CLOUD.02 Thin low cloud streak' (was empty/garbled)
- label: 11.set.calm_sea/part-4: '' -> 'CREST.O1 Broken-crest strip' (was empty/garbled)
- label: 11.set.calm_sea/part-5: '' -> 'CREST.02 Broken-crest strip' (was empty/garbled)
- label: 11.set.calm_sea/part-6: '' -> 'CREST.03 Broken-crest wave strip' (was empty/garbled)
- label: 11.set.calm_sea/from-11-set-calm-sea-travelling-calm-disc-separa: 'from 11.set.calm_sea travelling calm-disc: separate assets.' -> 'WATER.NEAR Near water backing (flat)' (closer label (cost 47 vs 210))

### 11.set.mirror_hall
- label: 11.set.mirror_hall/10-ml1-mirror-flip-vertically-source: '10 ML1 Mirror flip vertically source' -> '04 L1 Front lof pier' (closer label (cost 11 vs 1000000000); old text is 15-mr3-mirror-flip-vertically-source-2's)
- label: 11.set.mirror_hall/11-mr1-mirror-flip-vertically-source: '11 MR1 Mirror flip vertically source' -> 'Front rghit pier' (closer label (cost 7 vs 1000000000); old text is 15-mr3-mirror-flip-vertically-source-2's)
- label: 11.set.mirror_hall/12-ml2-mirror-flip-vertically-source: '12 ML2 Mirror flip vertically source' -> '06 L2 Rear left pier' (closer label (cost 23 vs 1000000000); old text is 15-mr3-mirror-flip-vertically-source-2's)
- label: 11.set.mirror_hall/13-mr2-mirror-flip-vertically-source: '13 MR2 Mirror flip vertically source' -> 'Rear right pier' (closer label (cost 17 vs 1000000000); old text is 15-mr3-mirror-flip-vertically-source-2's)
- label: 11.set.mirror_hall/14-ml3-mirror-flip-vertically-source: '14 ML3 Mirror flip vertically source' -> 'L3 Rear left pier' (closer label (cost 17 vs 1000000000); old text is 15-mr3-mirror-flip-vertically-source-2's)
- label: 11.set.mirror_hall/water-black-black: 'WATER.BLACK Black' -> '10 ML1 Mirror' (closer label (cost 28 vs 52))
- label: 11.set.mirror_hall/floor-no-baked-piers: 'floor (no baked piers)' -> 'Mirror' (closer label (cost 23 vs 79))

### 11.set.temple_infinity_pool
- label: 11.set.temple_infinity_pool/long-low-cloud-streak: 'LONG LOW CLOUD STREAK' -> 'CLOUD.01 LONG LOW CLOUD STREAK' (re-read, more complete)
- label: 11.set.temple_infinity_pool/reflection-of-wall: 'REFLECTION OF WALL' -> '(INVERTED,' (closer label (cost 119 vs 189))

### 12.elders.memory-drop
- label: 12.elders.memory-drop/part-2: '' -> '4 REFERENCE (assembled, backlit)' (was empty/garbled)
- ref: 12.elders.memory-drop/4-reference-assembled: label says 'REFERENCE'
- ref: 12.elders.memory-drop/part-2: label says 'REFERENCE'
- ref: 12.elders.memory-drop/masks: label fragment (printed words)

### 12.fx.words-wind
- label: 12.fx.words-wind/a3-word: 'A3 word' -> 'word card (large)' (closer label (cost 30 vs 636); old text is a4-word's)
- label: 12.fx.words-wind/a3-word-2: 'A3 word' -> 'A3 word card (small)' (closer label (cost 35 vs 1000000000); old text is a4-word's)
- label: 12.fx.words-wind/a4-word: 'A4 word' -> 'A4 word card' (re-read, more complete)
- label: 12.fx.words-wind/hoodie-b7-brother-hem: 'hoodie B7 Brother hem' -> 'cloth panel (bent)' (old text not on the sheet; label 32px-cost away)
- label: 12.fx.words-wind/b7-brother-hoodie-hem: 'B7 Brother hoodie hem' -> 'Poet jacket hem (left)' (closer label (cost 21 vs 46); old text is b7-brother-hoodie-hem-2's)
- label: 12.fx.words-wind/b8-brother-hoodie-hem-right: 'B8 Brother hoodie hem (right)' -> 'Poet jacket hem (right)' (closer label (cost 25 vs 41); old text is 12-fx-words-wind's)
- label: 12.fx.words-wind/rings-flash-elder-drain-wind: 'Rings, flash, elder drain, wind' -> 'cloth panel (still)' (old text not on the sheet; label 34px-cost away)
- label: 12.fx.words-wind/12-fx-words-wind: '12.fx.words-wind' -> 'Brother hoodie hem (right)' (old text not on the sheet; label 29px-cost away)

### 12.hero.pools
- label: 12.hero.pools/temple: 'TEMPLE' -> 'A1 PORTICO LINTEL ROOF STRIP' (old text not on the sheet; label 2px-cost away)
- label: 12.hero.pools/column4: 'COLUMN4' -> 'A5 COLUMN4' (closer label (cost 4 vs 1000000000); old text is column7's)
- label: 12.hero.pools/l2-2: 'L2' -> 'R2' (old text not on the sheet; label 16px-cost away)
- label: 12.hero.pools/tambourine-fragment-1: 'TAMBOURINE FRAGMENT 1' -> 'R1 POOL (with three empty recesses)' (closer label (cost 35 vs 73); old text is tambourine-fragment's)
- label: 12.hero.pools/tambourine-fragment: 'TAMBOURINE FRAGMENT' -> 'P1 TAMBOURINE FRAGMENT 1' (closer label (cost 10 vs 1000000000); old text is p3-tambourine-fragment's)
- ref: 12.hero.pools/part-2: label fragment (printed words)

### 12.props.hand-hourglass
- label: 12.props.hand-hourglass/sand-inserts-12: 'SAND INSERTS (12)' -> 'MASTER (EMPTY)' (closer label (cost 20 vs 40))
- label: 12.props.hand-hourglass/slumped-a4-dead: '(SLUMPED) A4 DEAD' -> 'A3 GUTTERING (BROKEN)' (old text not on the sheet; label 21px-cost away)
- label: 12.props.hand-hourglass/smoke-only-hide-body: 'SMOKE ONLY: hide body;' -> 'F3 SMOKE ONLY: FLAME hide body;' (re-read, more complete)
- label: 12.props.hand-hourglass/part-8: '' -> '(overlay)' (was empty/garbled)
- ref: 12.props.hand-hourglass/reference-proofs: label says 'REFERENCE'

### 12.props.last-hourglass
- label: 12.props.last-hourglass/21-25-assembled-states: '21-25 ASSEMBLED STATES' -> '21-25 ASSEMBLED STATES (front view)' (re-read, more complete)
- label: 12.props.last-hourglass/front-view: '(front view)' -> '02 GLASS OVERLAY' (closer label (cost 34 vs 83); old text is 21-25-assembled-states's)
- label: 12.props.last-hourglass/12: '12' -> '06 U4' (old text not on the sheet; label 17px-cost away)
- label: 12.props.last-hourglass/13: '13' -> '07 U5' (old text not on the sheet; label 17px-cost away)
- label: 12.props.last-hourglass/14: '14' -> 'U6' (old text not on the sheet; label 18px-cost away)
- label: 12.props.last-hourglass/15: '15' -> 'F1' (old text not on the sheet; label 21px-cost away)
- label: 12.props.last-hourglass/09-li: '09 Li' -> '09-14 LOWER SAND INSERTS (filling) 09 10 11 Li L2 L3' (was empty/garbled)
- label: 12.props.last-hourglass/full-unlit: 'FULL UNLIT' -> '21 FULL UNLIT' (re-read, more complete)
- label: 12.props.last-hourglass/22-running: '22 RUNNING' -> '22 RUNNING SMALL FLAME' (re-read, more complete)
- label: 12.props.last-hourglass/23-running: '23 RUNNING' -> '23 RUNNING FULL FIRE' (re-read, more complete)
- label: 12.props.last-hourglass/last-alight: 'LAST ALIGHT' -> '24 LAST ALIGHT' (re-read, more complete)
- label: 12.props.last-hourglass/ember-fleck-2: 'EMBER FLECK' -> '20 EMBER FLECK (hinged)' (re-read, more complete)
- ref: 12.props.last-hourglass/21-25-assembled-states: label says 'ASSEMBLED'
- ref: 12.props.last-hourglass/full-unlit: under the band heading '21-25 ASSEMBLED STATES (front view)'
- ref: 12.props.last-hourglass/22-running: under the band heading '21-25 ASSEMBLED STATES (front view)'
- ref: 12.props.last-hourglass/23-running: under the band heading '21-25 ASSEMBLED STATES (front view)'
- ref: 12.props.last-hourglass/last-alight: under the band heading '21-25 ASSEMBLED STATES (front view)'
- ref: 12.props.last-hourglass/ember-lifting: under the band heading '21-25 ASSEMBLED STATES (front view)'

### 12.props.niche-porch
- label: 12.props.niche-porch/socket-tab-pivot: 'socket tab pivot' -> '2 backing card' (closer label (cost 42 vs 119); old text is wooden-step's)
- label: 12.props.niche-porch/shade: 'shade' -> 'tin shade' (re-read, more complete)
- label: 12.props.niche-porch/b7-sagging: 'B7 (sagging,' -> 'bulb OFF' (closer label (cost 36 vs 64); old text is step's)
- label: 12.props.niche-porch/on: 'ON' -> '3-B5 bulbs' (was empty/garbled)
- label: 12.props.niche-porch/wooden-step: 'wooden step' -> 'socket pivot tab' (closer label (cost 27 vs 49); old text is wooden-step-2's)
- label: 12.props.niche-porch/step: 'step' -> 'B7 wire (sagging, bulbs)' (closer label (cost 22 vs 115); old text is wooden-step-2's)
- label: 12.props.niche-porch/part-11: '' -> 'A3' (was empty/garbled)
- label: 12.props.niche-porch/assembled-examples: '(assembled examples)' -> 'REFERENCE (assembled examples)' (re-read, more complete)
- ref: 12.props.niche-porch/assembled-examples: label says 'REFERENCE'

### 12.props.reunion
- label: 12.props.reunion/part-2: '' -> 'football spin horizontal' (was empty/garbled)
- label: 12.props.reunion/only-b1-a3-spin-angled: 'only) B1 A3 spin angled' -> 'phone back' (closer label (cost 14 vs 63); old text is spin-angled's)
- label: 12.props.reunion/screen-with-field-b2-screen-with: 'screen with field B2 screen with' -> '9 phone flash insert (white)' (closer label (cost 23 vs 74); old text is b1-screen-with-field's)
- label: 12.props.reunion/spin-angled: 'spin angled' -> 'A3 spin angled' (re-read, more complete)
- label: 12.props.reunion/camera-view: '(camera view)' -> 'B2 screen wit goal flash' (closer label (cost 13 vs 93); old text is c1-phone-front-camera-view's)
- label: 12.props.reunion/12-props-reunion: '12.props.reunion' -> 'C3 phone with flash' (old text not on the sheet; label 31px-cost away)
- ref: 12.props.reunion/assembled-states-reference-held-spin-al-a2-horiz: label says 'ASSEMBLED'
- ref: 12.props.reunion/a2-horizontal-a3-spin: under the band heading 'ASSEMBLED STATES (reference only) Al hel'
- ref: 12.props.reunion/reference-only-spin-a2-horizontal: label says 'reference'
- ref: 12.props.reunion/spin-angled: under the band heading 'ASSEMBLED STATES (reference only) Al hel'
- ref: 12.props.reunion/b1-screen-with-field: under the band heading 'ASSEMBLED STATES (reference only) Al hel'
- ref: 12.props.reunion/camera-view: under the band heading 'ASSEMBLED STATES (reference only) Al hel'
- ref: 12.props.reunion/c1-phone-front-camera-view: under the band heading 'ASSEMBLED STATES (reference only) Al hel'
- ref: 12.props.reunion/c2-phone-back: under the band heading 'ASSEMBLED STATES (reference only) Al hel'
- ref: 12.props.reunion/12-props-reunion: under the band heading 'ASSEMBLED STATES (reference only) Al hel'

### 12.props.snapshot
- label: 12.props.snapshot/24-cm-square-2x-size: '24 cm (square, 2x size)' -> '2. SNAPSHOT (CLOSE-UP, SAME IMAGE) 24 cm (square, 2x size)' (re-read, more complete)
- ref: 12.props.snapshot/poet-brother-adults-3-pose-reference: label says 'REFERENCE'

### 12.set.temple_backroom
- label: 12.set.temple_backroom/back-wall-doorway: 'BACK WALL (DOORWAY)' -> '12-BACK-01 BACK WALL (DOORWAY)' (re-read, more complete)
- label: 12.set.temple_backroom/stairs-short-flight: 'STAIRS (SHORT FLIGHT)' -> '12-BACK- STAIRS (SHORT FLIGHT)' (re-read, more complete)
- label: 12.set.temple_backroom/doorway-light-insert: 'DOORWAY LIGHT INSERT' -> '1 12-BACK-03 DOORWAY' (old text not on the sheet; label 15px-cost away)
- label: 12.set.temple_backroom/1-1-front-chair-turned-away: '1 1 FRONT CHAIR TURNED AWAY' -> '12-FRONT-01' (closer label (cost 8 vs 1000000000))
- label: 12.set.temple_backroom/12-fix-02-bare-bulb: '12-FIX-02 BARE BULB' -> '12-FIX-02 12-FIX-03 BARE BULB 1' (closer label (cost 24 vs 1000000000); old text is bare-bulb's)
- label: 12.set.temple_backroom/12-fix-03-bare-bulb: '12-FIX-03 BARE BULB' -> 'HANGING' (closer label (cost 25 vs 1000000000); old text is bare-bulb's)
- label: 12.set.temple_backroom/bare-bulb: 'BARE BULB' -> '12-FIX-05 BARE BULB 4' (closer label (cost 15 vs 1000000000))
- ref: 12.set.temple_backroom/part-1: label fragment (printed words)
- ref: 12.set.temple_backroom/part-3: label fragment (printed words)
- ref: 12.set.temple_backroom/part-4: label fragment (printed words)
- ref: 12.set.temple_backroom/part-5: label fragment (printed words)
- ref: 12.set.temple_backroom/part-6: label fragment (printed words)
- ref: 12.set.temple_backroom/part-7: label fragment (printed words)

### 12.set.temple_grove
- label: 12.set.temple_grove/fog-screen-blank: 'fog screen (blank)' -> '12-BACK (blank)' (old text not on the sheet; label 11px-cost away)
- label: 12.set.temple_grove/tree-trunk-1: 'tree trunk 1' -> '12-MID-1 tree trunk' (closer label (cost 11 vs 1000000000); old text is tree-trunk-2's)
- label: 12.set.temple_grove/tree-trunk-2: 'tree trunk 2' -> '12-MID-2 tree trunk 2' (re-read, more complete)
- label: 12.set.temple_grove/canopy-front: 'canopy (front)' -> 'fog' (closer label (cost 84 vs 1000000000); old text is grass-strip-front's)
- label: 12.set.temple_grove/grass-strip-front: 'grass strip (front)' -> '12-FRONT-C canopy (front)' (closer label (cost 38 vs 212))

### 12.set.temple_shore_terrace
- label: 12.set.temple_shore_terrace/01-indigo-dusk-first-stars-milky-way: '01 indigo dusk, first stars, Milky Way' -> '01 SKY indigo dusk, first stars, Milky Way' (re-read, more complete)
- label: 12.set.temple_shore_terrace/06-floor-stone: '06 FLOOR stone' -> 'wall (no lamp)' (closer label (cost 36 vs 128))
- label: 12.set.temple_shore_terrace/06-floor-stone-e: '06 FLOOR stone e' -> 'slabs, reflective' (closer label (cost 50 vs 1000000000))
- label: 12.set.temple_shore_terrace/07-wall-lamp: '07 wall lamp' -> '07 LAMP1 lamp (unlit)' (closer label (cost 20 vs 1000000000); old text is 06-floor-stone's)
- label: 12.set.temple_shore_terrace/08-wall-lamp: '08 wall lamp' -> 'LAMP2 wall lamp (unlit)' (closer label (cost 26 vs 44); old text is 06-floor-stone's)
- label: 12.set.temple_shore_terrace/hanging-cloth-wind-1: 'hanging cloth (wind 1)' -> 'slabs, reflective' (closer label (cost 38 vs 1000000000))

### 13.fx.orbit-harvest
- label: 13.fx.orbit-harvest/5-flowers-row-b: '5. FLOWERS_ROW_B' -> '2. PAIR_B' (closer label (cost 36 vs 94); old text is string-lights's)
- label: 13.fx.orbit-harvest/8-pcs: '(8 pcs)' -> '3. PAIR_C' (closer label (cost 31 vs 1000000000); old text is tabs-5's)
- label: 13.fx.orbit-harvest/4-flowers-row-a-8-pcs: '4. FLOWERS_ROW_A (8 pcs)' -> '1. PAIR_A «120°' (closer label (cost 30 vs 91); old text is 6-stem's)
- label: 13.fx.orbit-harvest/6-stem: '6. STEM' -> '4. FLOWERS_ROW_A' (closer label (cost 56 vs 87); old text is hinge's)
- label: 13.fx.orbit-harvest/string-lights: 'STRING_LIGHTS' -> '5. FLOWERS_ROW_B' (closer label (cost 42 vs 59); old text is wire-8's)
- label: 13.fx.orbit-harvest/tabs-5: 'TABS (5' -> 'V_A (8 pcs)' (closer label (cost 46 vs 76); old text is hinge's)
- label: 13.fx.orbit-harvest/6-stem-2: '6. STEM' -> 'HAND.L' (closer label (cost 11 vs 54); old text is hinge's)

### 13.hero.atrium
- label: 13.hero.atrium/13-07-floor-blue-water: '13-07 FLOOR BLUE WATER' -> '13-05 PLANTER1' (closer label (cost 43 vs 132))
- ref: 13.hero.atrium/13-drowned: label fragment (printed words)
- ref: 13.hero.atrium/separate: label fragment (printed words)
- ref: 13.hero.atrium/cards: label fragment (printed words)

### 13.hero.cafe
- label: 13.hero.cafe/03-back: '03 BACK' -> 'BACK WALL' (old text not on the sheet; label 14px-cost away)
- label: 13.hero.cafe/part-4: '' -> 'WINDOW WALL' (was empty/garbled)
- label: 13.hero.cafe/awning-lights-furniture: 'Awning, lights, furniture' -> 'Awning, lights, furniture and distant window: separate props' (re-read, more complete)
- label: 13.hero.cafe/06-glass-reflection-film: '06 GLASS REFLECTION FILM' -> '05 DOOR LEAF O06 GLASS REFLECTION FILM' (re-read, more complete)

### 13.hero.sleepdam
- label: 13.hero.sleepdam/13-04-gate-reflection-strip-cream-cyan-reflectio: '13-04 GATE REFLECTION STRIP cream/cyan reflection layer independently the back (13-02). water to over water' -> '13-04 GATE REFLECTION STRIP Isolated cream/cyan water reflection to layer independently over the back water (13-02)' (re-read, more complete)

### 13.props.cafe
- split: 13.props.cafe/b-table-with-cup (320x162) -> 2 parts
- recut: 13.props.cafe/c-edge-grip-position: framed panel [716, 747, 297, 162] -> figure [720, 773, 257, 132]
- label: 13.props.cafe/9-held-cup-side: '9 HELD CUP (SIDE)' -> 'CHAIR (EMPTY FRONT)' (closer label (cost 18 vs 34))
- label: 13.props.cafe/7-espresso-cup: '7 ESPRESSO CUP' -> '3 TABLE BASE 3-prong' (closer label (cost 20 vs 144); old text is 7-espresso-cup-table's)
- label: 13.props.cafe/part: '' -> 'B. table with cup' (was empty/garbled)
- label: 13.props.cafe/part-2: '' -> 'B. table with cup' (was empty/garbled)
- ref: 13.props.cafe/a-empty-table-chair: under the band heading '10 STATE PROOFS (small, schematic)'
- ref: 13.props.cafe/b-table-with-cup: section box: its 2 contents are cut as separate parts
- ref: 13.props.cafe/c-edge-grip-position: under the band heading '10 STATE PROOFS (small, schematic)'
- ref: 13.props.cafe/d-final-empty-chair: under the band heading '10 STATE PROOFS (small, schematic)'
- ref: 13.props.cafe/part: under the band heading '10 STATE PROOFS (small, schematic)'
- ref: 13.props.cafe/part-2: under the band heading '10 STATE PROOFS (small, schematic)'
- added: 13.props.cafe/part
- added: 13.props.cafe/part-2

### 13.props.distant-window
- label: 13.props.distant-window/wall-gabled-brick-farwall-card: 'WALL gabled brick farwall card' -> '1 WALL gabled brick farwall card with window aperture' (re-read, more complete)
- label: 13.props.distant-window/2-window-frame-empty-frame: '2 WINDOW FRAME empty frame' -> '2 WINDOW FRAME empty frame (fits wall aperture)' (re-read, more complete)
- label: 13.props.distant-window/vertical-window: 'vertical window' -> '3 MULLION vertical window' (re-read, more complete)
- label: 13.props.distant-window/optional-curtain-card: '(OPTIONAL) curtain card' -> '7 CURTAINS (OPTIONAL) inner (freestanding)' (old text not on the sheet; label 38px-cost away)
- label: 13.props.distant-window/4-top-top-ledge-window: '4 ToP top ledge window' -> '4 TOP SILL' (old text not on the sheet; label 12px-cost away)

### 13.props.five-letters
- label: 13.props.five-letters/13-02: '13-02' -> '13-01' (was empty/garbled)
- label: 13.props.five-letters/part-3: '' -> '13-02' (was empty/garbled)
- label: 13.props.five-letters/13-03: '13-03' -> '13-06' (was empty/garbled)
- label: 13.props.five-letters/13-04: '13-04' -> '13-03' (was empty/garbled)
- label: 13.props.five-letters/13-06: '13-06' -> '13-05' (was empty/garbled)
- label: 13.props.five-letters/13-07: '13-07' -> '13-10' (was empty/garbled)
- label: 13.props.five-letters/13-08: '13-08' -> '13-07' (was empty/garbled)
- label: 13.props.five-letters/13-10: '13-10' -> '13-09' (was empty/garbled)
- label: 13.props.five-letters/13-11: '13-11' -> '13-14' (was empty/garbled)
- label: 13.props.five-letters/13-12: '13-12' -> '13-11' (was empty/garbled)
- label: 13.props.five-letters/part-15: '' -> '13-12' (was empty/garbled)
- label: 13.props.five-letters/part-16: '' -> '13-08' (was empty/garbled)
- label: 13.props.five-letters/13-15: '13-15' -> '13-18' (was empty/garbled)
- label: 13.props.five-letters/13-16: '13-16' -> '13-15' (was empty/garbled)
- label: 13.props.five-letters/part-20: '' -> '13-16' (was empty/garbled)
- label: 13.props.five-letters/13-18: '13-18' -> '13-17' (was empty/garbled)
- label: 13.props.five-letters/flame-hinged: 'FLAME (HINGED)' -> '13-22 FLAME (HINGED)' (re-read, more complete)
- label: 13.props.five-letters/13-23: '13-23' -> '13-19' (was empty/garbled)
- ref: 13.props.five-letters/whole: label fragment (printed words)
- ref: 13.props.five-letters/part-3: label fragment (printed words)
- ref: 13.props.five-letters/edge-caught: label fragment (printed words)
- ref: 13.props.five-letters/half-gone: label fragment (printed words)

### 13.props.harvest
- label: 13.props.harvest/armful: 'ARMFUL' -> 'ARMFUL FEW' (re-read, more complete)
- label: 13.props.harvest/ober-large: 'ober LARGE' -> '2 POPPY MEDIUM' (closer label (cost 65 vs 1114))
- label: 13.props.harvest/4-purple-blossom-small: '4 PURPLE BLOSSOM SMALL' -> '3 POPPY LARGE' (closer label (cost 93 vs 131))
- label: 13.props.harvest/purple-blossom-large: 'PURPLE BLOSSOM LARGE' -> '5 PURPLE BLOSSOM' (closer label (cost 64 vs 365))
- label: 13.props.harvest/part-6: '' -> '6 PURPLE BLOSSOM' (was empty/garbled)
- label: 13.props.harvest/crown: 'CROWN' -> '13 SHOULDER.R' (closer label (cost 75 vs 1000000000); old text is petals-4-purple's)
- label: 13.props.harvest/armful-full: 'ARMFUL FULL' -> '12 SHOULDER.L' (closer label (cost 34 vs 154))
- label: 13.props.harvest/petals: 'PETALS' -> '15 FALL PETALS SCARLET' (closer label (cost 42 vs 1000000000); old text is 16-fall's)

### 13.props.personal
- label: 13.props.personal/pearls-wearable-2-1-loop: 'PEARLS (WEARABLE) 2.1 LOOP' -> '1.1 FRONT OPEN' (old text not on the sheet; label 23px-cost away)
- label: 13.props.personal/4-reference-prop-orientation: '4. REFERENCE (PROP ORIENTATION' -> '2.2 FOLDED CLUTCHED LOOP' (closer label (cost 34 vs 93))

### 13.props.planet-boats
- split: 13.props.planet-boats/13-props-planet-boats (1579x158) -> 2 parts
- label: 13.props.planet-boats/02-moon1: '02 MOON1' -> 'BOAT_A' (closer label (cost 62 vs 193); old text is 02-moon1-2's)
- label: 13.props.planet-boats/hull-heeled-low-tide: 'HULL HEELED (LOW TIDE)' -> '07b HULL HEELED (LOW TIDE)' (closer label (cost 9 vs 1000000000); old text is 06b-hull-heeled-low-tide's)
- label: 13.props.planet-boats/08-boat-state-proof-small-band: '08 BOAT STATE PROOF (SMALL BAND)' -> '06e REFLECTION_A' (closer label (cost 34 vs 50))
- label: 13.props.planet-boats/part: '' -> '08c AFLOAT' (was empty/garbled)
- ref: 13.props.planet-boats/13-props-planet-boats: section box: its 2 contents are cut as separate parts
- ref: 13.props.planet-boats/part: under the band heading 'BOAT STATE PROOF (SMALL BAND)'
- ref: 13.props.planet-boats/08a-ground: under the band heading 'BOAT STATE PROOF (SMALL BAND)'
- added: 13.props.planet-boats/part
- added: 13.props.planet-boats/08a-ground

### 13.props.rail-tide-awning
- label: 13.props.rail-tide-awning/wire-card: 'WIRE CARD' -> '4 TIDEBOARD POST' (old text not on the sheet; label 31px-cost away)
- label: 13.props.rail-tide-awning/8-awning-fold-valance: '8 AWNING FOLD VALANCE' -> 'NEXT' (closer label (cost 101 vs 246); old text is 8-awning-fold-valance-flap-2's)

### 13.set.church_pews
- label: 13.set.church_pews/stone-interior-wall-with-three-lancet-windows: 'stone interior wall with three lancet windows' -> '13-03 BACK LANCET WALL stone interior wall with three lancet windows' (re-read, more complete)
- label: 13.set.church_pews/glazing-1-left-lancet-pane: 'GLAZING 1 left lancet pane' -> '13-04 GLAZING 1 left lancet pane' (re-read, more complete)
- label: 13.set.church_pews/13-05-glazing-2: '13-05 GLAZING 2' -> '13-05 GLAZING 2 centre lancet pane right lancet pane' (closer label (cost 45 vs 1000000000); old text is glazing-3-right-lancet-pane's)
- label: 13.set.church_pews/glazing-3-right-lancet-pane: 'GLAZING 3 right lancet pane' -> '13-06 GLAZING 3' (closer label (cost 18 vs 1000000000); old text is glazing-1-left-lancet-pane's)
- label: 13.set.church_pews/part-6: '' -> '13-02 SKY MOON moon disc (separate)' (was empty/garbled)

### 13.set.drowned_atrium
- label: 13.set.drowned_atrium/13-01-grid: '13-01 GRID' -> '13-01 FRONT GLASS GRID' (closer label (cost 91 vs 375); old text is 13-05-mid-planter1's)
- label: 13.set.drowned_atrium/back: 'BACK' -> 'WALL' (closer label (cost 60 vs 73); old text is 13-06-mid-planter2's)
- label: 13.set.drowned_atrium/13-03-tree1: '13-03 TREE1' -> '13-03 MID TREE1' (re-read, more complete)
- label: 13.set.drowned_atrium/13-04-mid-tree2: '13-04 MID TREE2' -> '13-04 MID TREE2 ‘05 MID PLANTER1' (closer label (cost 34 vs 1000000000); old text is 13-03-tree1's)
- ref: 13.set.drowned_atrium/13: label fragment (printed words)
- ref: 13.set.drowned_atrium/part-3: label fragment (printed words)
- ref: 13.set.drowned_atrium/t: label fragment (printed words)
- ref: 13.set.drowned_atrium/t-2: label fragment (printed words)
- ref: 13.set.drowned_atrium/part-6: label fragment (printed words)
- ref: 13.set.drowned_atrium/part-7: label fragment (printed words)

### 13.set.flower_field
- label: 13.set.flower_field/part-6: '' -> '13-06 FRONT PURPLE BLOSSOM FRAME (close)' (was empty/garbled)
- label: 13.set.flower_field/13-07-cut-stalk-1-medium: '13-07 CUT STALK 1 (medium' -> 'FRAME (close)' (closer label (cost 66 vs 96))

### 13.set.harbor_cafe
- label: 13.set.harbor_cafe/04-far-shore-silhouette: '04 FAR SHORE SILHOUETTE)' -> '02 SKY DUSK' (closer label (cost 52 vs 124))
- label: 13.set.harbor_cafe/quay-wall-4-flood-line-m: 'QUAY WALL +4 FLOOD LINE) m' -> '10 QUAY WALL (WITH +4 FLOOD LINE)' (re-read, more complete)
- label: 13.set.harbor_cafe/cafe-facade-teal-wall: 'CAFE FACADE (TEAL WALL)' -> '11 CAFE FACADE (TEAL WALL)' (re-read, more complete)

### 13.set.harbor_quay_night_fire
- label: 13.set.harbor_quay_night_fire/part-1: '' -> 'L1 SKY black-navy' (was empty/garbled)
- label: 13.set.harbor_quay_night_fire/13-set-harbor-quay-night-fire: '13.set.harbor_quay_night_fire' -> 'Poet' (closer label (cost 49 vs 221))
- ref: 13.set.harbor_quay_night_fire/part-2: label fragment (printed words)
- ref: 13.set.harbor_quay_night_fire/part-3: label fragment (printed words)
- ref: 13.set.harbor_quay_night_fire/part-4: label fragment (printed words)
- ref: 13.set.harbor_quay_night_fire/part-5: label fragment (printed words)
- ref: 13.set.harbor_quay_night_fire/part-6: label fragment (printed words)
- ref: 13.set.harbor_quay_night_fire/part-7: label fragment (printed words)

### 14.fx.filmframe
- label: 14.fx.filmframe/02-frame: '02 FRAME' -> '02 PORTRAIT FRAME ROLL)' (closer label (cost 1 vs 422); old text is 01-frame's)
- label: 14.fx.filmframe/vertical-frame: 'VERTICAL FRAME' -> 'O5 VERTICAL FRAME LINE A' (closer label (cost 16 vs 1000000000); old text is vertical-frame-2's)
- label: 14.fx.filmframe/vertical-frame-2: 'VERTICAL FRAME' -> '06 VERTICAL FRAME LINE' (re-read, more complete)
- label: 14.fx.filmframe/cut-to-black: 'CUT-TO-BLACK' -> '09 CUT-TO-BLACK CARD' (re-read, more complete)

### 14.props.door
- label: 14.props.door/10-main-states-assembled: '10. MAIN STATES (assembled' -> '(empty aperture)' (closer label (cost 14 vs 38); old text is appearing-far's)
- label: 14.props.door/hinge-tab-backing-card: 'HINGE TAB BACKING CARD' -> '(open perspective)' (closer label (cost 12 vs 155); old text is backing-card-2's)
- label: 14.props.door/hinge-tab: 'HINGE TAB' -> '5. HINGE TAB (top)' (re-read, more complete)
- label: 14.props.door/8-door-knob-back: '8. DOOR KNOB (back)' -> '7. DOOR (front)' (old text not on the sheet; label 25px-cost away)
- label: 14.props.door/backing-card: 'BACKING CARD' -> 'TAB (bottom)' (closer label (cost 15 vs 41); old text is backing-card-2's)
- label: 14.props.door/b-shut: 'B. SHUT' -> 'nly)' (closer label (cost 20 vs 742); old text is 2-door-slab-shut's)
- ref: 14.props.door/b-shut: under the band heading 'STATES (assembled'
- ref: 14.props.door/c-grip-position: under the band heading 'STATES (assembled'
- ref: 14.props.door/d-opening: under the band heading 'STATES (assembled'
- ref: 14.props.door/e-open: under the band heading 'STATES (assembled'
- ref: 14.props.door/f-closing: under the band heading 'STATES (assembled'
- ref: 14.props.door/appearing-far: under the band heading 'STATES (assembled'

### 14.props.party
- label: 14.props.party/garland-lantern-1: 'garland lantern 1' -> 'window frame' (closer label (cost 20 vs 441); old text is lantern-2-cream's)
- label: 14.props.party/b-paper-garland-400cm-nominal: 'B. PAPER GARLAND (400cm nominal)' -> 'garland cord (sagging)' (old text not on the sheet; label 19px-cost away)
- label: 14.props.party/crank: 'crank' -> 'horn' (closer label (cost 26 vs 134); old text is crank-2's)
- label: 14.props.party/d-champagne-coupe-15cm-nominal-upright-coupe-til: 'D. CHAMPAGNE COUPE (15cm nominal) (upright) coupe (tilt) coupe' -> 'record disc' (old text not on the sheet; label 30px-cost away)
- label: 14.props.party/lantern-1: 'lantern 1' -> 'lantern 1 amber' (closer label (cost 4 vs 1000000000); old text is lantern-2-cream's)
- label: 14.props.party/main-poses-reference: 'MAIN POSES (reference' -> 'window pane (dark)' (closer label (cost 20 vs 98); old text is wine-2's)
- label: 14.props.party/wine-2: 'wine' -> 'MAIN POSES (reference only assembled puppets, not for cutting)' (closer label (cost 95 vs 1000000000))
- label: 14.props.party/d-coupes: 'D. coupes' -> 'D. coupes (assembled)' (re-read, more complete)
- label: 14.props.party/assembled: '(assembled)' -> 'D. coupes (assembled)' (re-read, more complete)
- ref: 14.props.party/assembled-d-coupes: label says 'assembled'
- ref: 14.props.party/a-window-assembled: label says 'assembled'
- ref: 14.props.party/b-garland-assembled: label says 'assembled'
- ref: 14.props.party/d-coupes: label says 'assembled'
- ref: 14.props.party/assembled: label says 'assembled'

### 14.props.reel
- label: 14.props.reel/candle: 'CANDLE' -> '05 CANDLE' (re-read, more complete)
- label: 14.props.reel/temple: 'TEMPLE' -> '08 WHITE TEMPLE' (re-read, more complete)
- label: 14.props.reel/09-burning: '09 BURNING' -> '09 BURNING HOURGLASS' (re-read, more complete)

### 14.set.black_void
- label: 14.set.black_void/back-open-horizon: 'BACK OPEN HORIZON' -> 'FRONT: EMPTY no card' (closer label (cost 110 vs 202))

### 14.set.broll_life
- label: 14.set.broll_life/3-frame-line-mask: '3. FRAME-LINE MASK' -> '3. FRONT FRAME-LINE MASK' (re-read, more complete)
- label: 14.set.broll_life/5-grief-insert-frame: '5. GRIEF INSERT FRAME' -> '5. MID GRIEF INSERT FRAME' (re-read, more complete)
- label: 14.set.broll_life/frame-line: 'FRAME-LINE' -> 'MID contents: separate motif cards FAMILY puppets' (closer label (cost 118 vs 1000000000); old text is 3-frame-line-mask's)
- ref: 14.set.broll_life/part-2: label fragment (printed words)
- ref: 14.set.broll_life/frame-line: label fragment (printed words)
- ref: 14.set.broll_life/grief: label fragment (printed words)

### 14.set.harbor_atlantis_wide
- label: 14.set.harbor_atlantis_wide/back-01-atlantis-skyline: 'BACK.01 ATLANTIS SKYLINE' -> 'SKY.02' (closer label (cost 41 vs 212))
- label: 14.set.harbor_atlantis_wide/front-o1: 'FRONT.O1' -> 'FRONT.O1 QUAY' (re-read, more complete)
- label: 14.set.harbor_atlantis_wide/part-6: '' -> 'MID.03 BOAT' (was empty/garbled)
- label: 14.set.harbor_atlantis_wide/14-set-harbor-atlantis-wide-mid-puppet-slot-rema: '14.set.harbor_atlantis_wide MID: puppet slot remains empty Haze supplied' -> 'FLOOR.02 REFLECTIO' (old text not on the sheet; label 39px-cost away)

### 14.set.vintage_party
- label: 14.set.vintage_party/front-interior-door-frame: 'FRONT INTERIOR DOOR FRAME' -> 'SKY CEILING PANEL' (closer label (cost 31 vs 177); old text is front-interior-door-frame-2's)

### ancestors.05.action-hands
- label: ancestors.05.action-hands/cup-r: 'CUP R' -> 'STAR CUP R' (re-read, more complete)
- label: ancestors.05.action-hands/r: 'R' -> 'INDIGO CUFF R' (was empty/garbled)
- label: ancestors.05.action-hands/cuff-r: 'CUFF R' -> 'WHITE CUFF' (closer label (cost 17 vs 1000000000); old text is r's)

### ancestors.05.ancestor_elder_white_silver.body
- label: ancestors.05.ancestor_elder_white_silver.body/5-rear-seat: '5 REAR SEAT' -> 'SEAT BUTT' (old text not on the sheet; label 17px-cost away)

### ancestors.05.ancestor_robe_indigo_gold.body
- label: ancestors.05.ancestor_robe_indigo_gold.body/h-r: 'H-R' -> 'HIP' (was empty/garbled)
- label: ancestors.05.ancestor_robe_indigo_gold.body/12-l: '12 L' -> '12 SHIN L' (was empty/garbled)
- label: ancestors.05.ancestor_robe_indigo_gold.body/14-front: '14 FRONT' -> 'OVERLAY' (old text not on the sheet; label 24px-cost away)
- label: ancestors.05.ancestor_robe_indigo_gold.body/copper-shoulder-plate-r: 'COPPER SHOULDER PLATE R' -> 'SHOULDER COPPER SHOULDER PLATE L' (re-read, more complete)
- label: ancestors.05.ancestor_robe_indigo_gold.body/foot-l-front: 'FOOT L FRONT' -> '16 FOOTL L' (old text not on the sheet; label 13px-cost away)
- label: ancestors.05.ancestor_robe_indigo_gold.body/20-lifted: '20 LIFTED' -> '20 FOOTL LIFTED' (re-read, more complete)
- ref: ancestors.05.ancestor_robe_indigo_gold.body/id-ancestors-05-ancestor-robe-indigo-gold-body: label fragment (printed words)

### ancestors.05.identities.01
- label: ancestors.05.identities.01/ida-back: 'IDA BACK' -> 'IDA HEAD BLANK BACK' (closer label (cost 2 vs 218); old text is ida-head-blank-profile's)
- label: ancestors.05.identities.01/mouth: 'MOUTH' -> 'IDA CALM RIGHT BROW' (closer label (cost 85 vs 309))
- ref: ancestors.05.identities.01/amos-reference-only: label says 'REFERENCE'
- ref: ancestors.05.identities.01/ida-reference-only: label says 'REFERENCE'

### ancestors.05.identities.02
- label: ancestors.05.identities.02/ruth-l-eye: 'RUTH L.EYE' -> 'RUTH CALM' (closer label (cost 32 vs 149); old text is ruth-l-eye-2's)
- label: ancestors.05.identities.02/ruth-l-brow-2: 'RUTH L.BROW' -> 'MAE EXPRESSIONS (SEPARATE PARTS)' (closer label (cost 106 vs 1000000000); old text is ruth-r-brow's)
- label: ancestors.05.identities.02/mbe-l-eye: 'MBE L.EYE' -> 'MAE JOY' (closer label (cost 20 vs 74); old text is mae-l-eye's)
- ref: ancestors.05.identities.02/ruth-reference-only: label says 'REFERENCE'
- ref: ancestors.05.identities.02/mae-reference-only: label says 'REFERENCE'

### ancestors.05.identities.03
- label: ancestors.05.identities.03/cora-head-blank: 'CORA HEAD BLANK' -> 'CORA HEAD BLANK FRONT' (closer label (cost 10 vs 1000000000); old text is cora-head-blank-2's)
- label: ancestors.05.identities.03/cora-head-blank-2: 'CORA HEAD BLANK' -> 'CORA HEAD BLANK BACK' (re-read, more complete)
- label: ancestors.05.identities.03/part-4: '' -> 'CORA BROWL L BROW' (was empty/garbled)
- label: ancestors.05.identities.03/reference-only: 'REFERENCE ONLY' -> 'CORA' (closer label (cost 4 vs 510); old text is reference-only-2's)
- label: ancestors.05.identities.03/cora-head-blank-3: 'CORA HEAD BLANK' -> 'CORA HEAD BLANK PROFILE' (closer label (cost 10 vs 1000000000); old text is cora-head-blank-2's)
- label: ancestors.05.identities.03/cora-eyel: 'CORA EYEL' -> 'CORA EYE L' (closer label (cost 13 vs 202); old text is cora-eyel-2's)
- label: ancestors.05.identities.03/cora-eyer-2: 'CORA EYER' -> 'CORA EYER BROW L BROW' (closer label (cost 35 vs 115); old text is cora-eyer's)
- label: ancestors.05.identities.03/sol-head-blank: 'SOL HEAD BLANK' -> 'SOL HEAD BLANK FRONT' (closer label (cost 8 vs 1000000000); old text is sol-head-blank-3's)
- label: ancestors.05.identities.03/sol-head-blank-2: 'SOL HEAD BLANK' -> 'SOL HEAD BLANK PROFILE' (closer label (cost 16 vs 1000000000); old text is sol-head-blank-3's)
- label: ancestors.05.identities.03/sol-head-blank-3: 'SOL HEAD BLANK' -> 'SOL HEAD BLANK BACK' (re-read, more complete)
- label: ancestors.05.identities.03/eye-l: 'EYE L' -> 'SOL EYE L' (re-read, more complete)
- label: ancestors.05.identities.03/eye: 'EYE' -> 'SOL SOL EYER BROWL' (closer label (cost 23 vs 1000000000))
- label: ancestors.05.identities.03/brow-l: 'BROW L' -> 'EYER BROW BROWR' (closer label (cost 21 vs 221); old text is sol-eyer's)
- label: ancestors.05.identities.03/sol-eyer: 'SOL EYER' -> 'SOL EYER BROW L' (closer label (cost 28 vs 1000000000); old text is eye-l's)
- label: ancestors.05.identities.03/r-mouth: 'R MOUTH' -> 'SOL JOY (EXPRESSION PARTS)' (closer label (cost 72 vs 1000000000))
- ref: ancestors.05.identities.03/part-3: label fragment (printed words)
- ref: ancestors.05.identities.03/part-4: label fragment (printed words)
- ref: ancestors.05.identities.03/reference-only-2: label says 'REFERENCE'

### ancestors.05.procession-gifts-gate
- ref: ancestors.05.procession-gifts-gate/part-2: label fragment (printed words)
- ref: ancestors.05.procession-gifts-gate/ancestors-2: label fragment (printed words)
- ref: ancestors.05.procession-gifts-gate/ancestors-3: label fragment (printed words)

### atlantis.06.child_traveler.body
- label: atlantis.06.child_traveler.body/15-garment-overlay-back: '15 GARMENT OVERLAY BACK' -> 'CHILD_TRAVELER GARMENT OVERLAY BACK' (re-read, more complete)
- label: atlantis.06.child_traveler.body/child-traveler-uarm-l: 'CHILD_TRAVELER UARM L' -> 'CHILD_TRAVELER 7 CHILD_TRAVELER UARM L' (closer label (cost 41 vs 1000000000); old text is child-traveler-forearm-l's)
- label: atlantis.06.child_traveler.body/child-traveler-uarm-r: 'CHILD_TRAVELER UARM R' -> 'CHILD_TRAVELER 7 CHILD_TRAVELER UARM L' (closer label (cost 35 vs 1000000000); old text is child-traveler-forearm-l's)
- label: atlantis.06.child_traveler.body/child-traveler-thigh-l: 'CHILD_TRAVELER THIGH L' -> '10 CHILD_TRAVELER THIGH L' (re-read, more complete)
- label: atlantis.06.child_traveler.body/child-traveler-thigh-r: 'CHILD_TRAVELER THIGH R' -> '11 CHILD_TRAVELER THIGH' (closer label (cost 17 vs 1000000000); old text is child-traveler-thigh-l's)
- label: atlantis.06.child_traveler.body/child-traveler-shin-l: 'CHILD_TRAVELER SHIN L' -> '12 CHILD_TRAVELER SHIN L' (re-read, more complete)
- label: atlantis.06.child_traveler.body/child-traveler: 'CHILD_TRAVELER' -> '13 CHILD_TRAVELER SHIN' (closer label (cost 21 vs 1000000000); old text is child-traveler-forearm-r's)
- label: atlantis.06.child_traveler.body/child-traveler-foot-l-front: 'CHILD_TRAVELER FOOT L FRONT' -> '16 CHILD_TRAVELER FOOT L FRONT' (re-read, more complete)
- label: atlantis.06.child_traveler.body/child-traveler-foot-r-front: 'CHILD_TRAVELER FOOT R FRONT' -> '17 CHILD_TRAVELER FOOT FRONT' (closer label (cost 13 vs 1000000000); old text is child-traveler-foot-l-front's)

### atlantis.06.child_traveler.heads-hands
- label: atlantis.06.child_traveler.heads-hands/21-hand-l-open: '21 HAND L OPEN' -> '21 HAND L OPEN 22 HAND OPEN' (closer label (cost 33 vs 1000000000); old text is 23-hand-l-grip's)
- label: atlantis.06.child_traveler.heads-hands/22-hand-r-open: '22 HAND R OPEN' -> '21 HAND L OPEN 22 HAND OPEN' (closer label (cost 38 vs 1000000000); old text is 24-hand-grip's)
- label: atlantis.06.child_traveler.heads-hands/25-hand-l-wave: '25 HAND L WAVE' -> '25 HAND L WAVE 26 HAND WAVE' (re-read, more complete)
- label: atlantis.06.child_traveler.heads-hands/26-hand-r: '26 HAND R' -> '25 HAND L WAVE 26 HAND WAVE' (closer label (cost 29 vs 1000000000); old text is 23-hand-l-grip's)

### atlantis.06.citizen_1.body
- label: atlantis.06.citizen_1.body/4-citizen-1: '4 CITIZEN_1' -> '4 CITIZEN_1 HIP BRIDGE' (closer label (cost 2 vs 1000000000); old text is citizen-1-uarm-r's)
- label: atlantis.06.citizen_1.body/citizen-1-uarm-r: 'CITIZEN_1 UARM R' -> '7 CITIZEN_1 UARM' (closer label (cost 12 vs 1000000000); old text is citizen-1-uarm-l's)
- label: atlantis.06.citizen_1.body/8-citizen-1: '8 CITIZEN_1' -> 'CITIZEN_1 FOREARM L' (closer label (cost 33 vs 1000000000); old text is citizen-1-uarm-r's)
- label: atlantis.06.citizen_1.body/10-citizen-1: '10 CITIZEN_1' -> '10 CITIZEN_1 THIGH L' (closer label (cost 6 vs 1000000000); old text is 13-citizen-1's)
- label: atlantis.06.citizen_1.body/11-citizen-1: '11 CITIZEN_1' -> '11 CITIZEN_1 THIGH' (re-read, more complete)
- label: atlantis.06.citizen_1.body/12-citizen-1: '12 CITIZEN_1' -> '12 CITIZEN_1 SHIN L' (re-read, more complete)
- label: atlantis.06.citizen_1.body/13-citizen-1: '13 CITIZEN_1' -> '13 CITIZEN_1 SHIN' (re-read, more complete)
- label: atlantis.06.citizen_1.body/citizen-1-garment-overlay-front: 'CITIZEN_1 GARMENT OVERLAY FRONT' -> '14 CITIZEN_1 GARMENT OVERLAY FRONT' (re-read, more complete)
- label: atlantis.06.citizen_1.body/citizen-1-garment-overlay-back: 'CITIZEN_1 GARMENT OVERLAY BACK' -> '15 CITIZEN_1 GARMENT OVERLAY BACK' (re-read, more complete)
- label: atlantis.06.citizen_1.body/citizen-1-foot-l-front: 'CITIZEN_1 FOOT L FRONT' -> '16 CITIZEN_1 FOOT L FRONT' (re-read, more complete)
- label: atlantis.06.citizen_1.body/citizen-1-foot-r-front: 'CITIZEN_1 FOOT R FRONT' -> '17 CITIZEN_1 FOOT FRONT' (closer label (cost 11 vs 1000000000); old text is citizen-1-foot-l-front's)
- label: atlantis.06.citizen_1.body/18-citizen-1: '18 CITIZEN_1' -> 'CITIZEN_1 FOOT L PROFILE' (closer label (cost 39 vs 1000000000); old text is 13-citizen-1's)
- label: atlantis.06.citizen_1.body/19-citizen-1: '19 CITIZEN_1' -> 'CITIZEN_1 FOOT PROFILE' (closer label (cost 34 vs 1000000000); old text is 13-citizen-1's)
- label: atlantis.06.citizen_1.body/20-citizen-1: '20 CITIZEN_1' -> 'CITIZEN_1 FOOT L LIFTED' (closer label (cost 50 vs 1000000000); old text is citizen-1-uarm-r's)
- label: atlantis.06.citizen_1.body/21-citizen-1: '21 CITIZEN_1' -> '21 CITIZEN_1 FOOT LIFTED' (closer label (cost 9 vs 62); old text is 13-citizen-1's)

### atlantis.06.crowd-head-variants
- split: atlantis.06.crowd-head-variants/head-front-head-back-reference-only (520x1042) -> 5 parts
- label: atlantis.06.crowd-head-variants/reference-only-2: 'REFERENCE ONLY' -> 'TRAVELER_3 REFERENCE ONLY' (closer label (cost 6 vs 360))
- label: atlantis.06.crowd-head-variants/reference-only-3: 'REFERENCE ONLY' -> 'TRAVELER_3 REFERENCE ONLY' (closer label (cost 40 vs 1000000000))
- label: atlantis.06.crowd-head-variants/reference-only-4: 'REFERENCE ONLY' -> 'CITIZEN_3 REFERENCE ONLY' (closer label (cost 12 vs 47))
- label: atlantis.06.crowd-head-variants/sj-traveler-4: 'SJ TRAVELER_4' -> 'TRAVELER_4 HEAD FRONT' (closer label (cost 18 vs 1000000000); old text is traveler-4-head-back's)
- ref: atlantis.06.crowd-head-variants/head-front-head-back-reference-only: section box: its 5 contents are cut as separate parts
- ref: atlantis.06.crowd-head-variants/reference-only: label says 'REFERENCE'
- ref: atlantis.06.crowd-head-variants/reference-only-2: label says 'REFERENCE'
- ref: atlantis.06.crowd-head-variants/reference-only-3: label says 'REFERENCE'
- ref: atlantis.06.crowd-head-variants/reference-only-4: label says 'REFERENCE'
- ref: atlantis.06.crowd-head-variants/traveler-2-reference-only: label says 'REFERENCE'
- ref: atlantis.06.crowd-head-variants/traveler-4-reference-only: label says 'REFERENCE'
- added: atlantis.06.crowd-head-variants/traveler-2-reference-only
- added: atlantis.06.crowd-head-variants/traveler-2-traveler-2-head-front-head-back-2
- added: atlantis.06.crowd-head-variants/traveler-4-reference-only
- added: atlantis.06.crowd-head-variants/sj-traveler-4
- added: atlantis.06.crowd-head-variants/traveler-4-head-back

### atlantis.06.elder_1.body
- label: atlantis.06.elder_1.body/6-elder-1-uarm-l: '6 ELDER_1 UARM.L' -> 'ELDER_1 7 ELDER_1 UARM.L' (closer label (cost 39 vs 1000000000); old text is 8-uarm-r's)
- label: atlantis.06.elder_1.body/8-uarm-r: '8 UARM.R' -> 'ELDER_1 UARM.R' (re-read, more complete)
- label: atlantis.06.elder_1.body/15-garment-overlay-back: '15 GARMENT OVERLAY BACK' -> 'ELDER 1 OVERLAY BACK' (closer label (cost 11 vs 1000000000); old text is elder-garment-overlay-front's)
- label: atlantis.06.elder_1.body/foot-r-lifted: 'FOOT.R LIFTED' -> '21 ELDER_1 FOOT.R LIFTED' (closer label (cost 20 vs 1000000000); old text is 20-elder-1-foot-l-lifted's)
- ref: atlantis.06.elder_1.body/part-4: label fragment (printed words)

### atlantis.06.gatekeeper-elder.heads
- split: atlantis.06.gatekeeper-elder.heads/full-assembled-reference-for-placement-only-full (1016x881) -> 30 parts
- label: atlantis.06.gatekeeper-elder.heads/part: '' -> 'FULL ASSEMBLED REFERENCE (for placement only)' (was empty/garbled)
- label: atlantis.06.gatekeeper-elder.heads/awe: 'AWE' -> 'eye.L' (old text not on the sheet; label 36px-cost away)
- label: atlantis.06.gatekeeper-elder.heads/separate-pieces: '(separate pieces)' -> 'eye.R' (closer label (cost 35 vs 1000000000))
- label: atlantis.06.gatekeeper-elder.heads/awe-2: 'AWE' -> 'eye.L' (old text not on the sheet; label 36px-cost away)
- label: atlantis.06.gatekeeper-elder.heads/separate-pieces-2: '(separate pieces)' -> 'eye.R' (closer label (cost 37 vs 64))
- label: atlantis.06.gatekeeper-elder.heads/joy-separate: 'JOY (separate' -> 'eye.L' (closer label (cost 30 vs 1000000000))
- label: atlantis.06.gatekeeper-elder.heads/separate-pieces-3: '(separate pieces)' -> 'eye.R' (closer label (cost 31 vs 1000000000))
- label: atlantis.06.gatekeeper-elder.heads/separate-pieces-4: '(separate pieces)' -> 'eye.R' (closer label (cost 32 vs 79))
- ref: atlantis.06.gatekeeper-elder.heads/full-assembled-reference-for-placement-only-full: section box: its 30 contents are cut as separate parts
- ref: atlantis.06.gatekeeper-elder.heads/part: label says 'ASSEMBLED'
- added: atlantis.06.gatekeeper-elder.heads/part
- added: atlantis.06.gatekeeper-elder.heads/front-threequarter
- added: atlantis.06.gatekeeper-elder.heads/threequarter-back-back
- added: atlantis.06.gatekeeper-elder.heads/profile
- added: atlantis.06.gatekeeper-elder.heads/threequarter-back-back-2
- added: atlantis.06.gatekeeper-elder.heads/profile-2
- added: atlantis.06.gatekeeper-elder.heads/mouth
- added: atlantis.06.gatekeeper-elder.heads/mouth-2
- added: atlantis.06.gatekeeper-elder.heads/brow-l
- added: atlantis.06.gatekeeper-elder.heads/awe
- added: atlantis.06.gatekeeper-elder.heads/separate-pieces
- added: atlantis.06.gatekeeper-elder.heads/awe-2
- added: atlantis.06.gatekeeper-elder.heads/brow-r
- added: atlantis.06.gatekeeper-elder.heads/separate-pieces-2
- added: atlantis.06.gatekeeper-elder.heads/mouth-3
- added: atlantis.06.gatekeeper-elder.heads/mouth-4
- added: atlantis.06.gatekeeper-elder.heads/brow-l-2
- added: atlantis.06.gatekeeper-elder.heads/joy-separate
- added: atlantis.06.gatekeeper-elder.heads/brow-r-2
- added: atlantis.06.gatekeeper-elder.heads/eye-l
- added: atlantis.06.gatekeeper-elder.heads/separate-pieces-3
- added: atlantis.06.gatekeeper-elder.heads/separate-pieces-4
- added: atlantis.06.gatekeeper-elder.heads/mouth-5
- added: atlantis.06.gatekeeper-elder.heads/mouth-6
- added: atlantis.06.gatekeeper-elder.heads/eye-l-2
- added: atlantis.06.gatekeeper-elder.heads/brow-l-3
- added: atlantis.06.gatekeeper-elder.heads/eye-r
- added: atlantis.06.gatekeeper-elder.heads/eye-l-3
- added: atlantis.06.gatekeeper-elder.heads/brow-r-3
- added: atlantis.06.gatekeeper-elder.heads/eye-r-2

### atlantis.06.gatekeeper.body
- label: atlantis.06.gatekeeper.body/h-r: 'H-R' -> 'H-L' (was empty/garbled)
- label: atlantis.06.gatekeeper.body/10-gatekeeper-thigh-l: '10 GATEKEEPER THIGH L' -> '4 GATEKEEPER HIP BRIDGE' (closer label (cost 42 vs 1000000000); old text is gatekeeper-shin-l's)
- label: atlantis.06.gatekeeper.body/gatekeeper-shin-l: 'GATEKEEPER SHIN L' -> '12 GATEKEEPER SHIN L' (re-read, more complete)
- label: atlantis.06.gatekeeper.body/gatekeeper: 'GATEKEEPER' -> '13 GATEKEEPER SHIN' (closer label (cost 14 vs 1000000000); old text is gatekeeper-forearm-r's)
- label: atlantis.06.gatekeeper.body/17-foot-r-front: '17 FOOT R FRONT' -> '17 GATEKEEPER FOOT FRONT' (closer label (cost 11 vs 1000000000); old text is 16-gatekeeper-foot-l-front's)
- ref: atlantis.06.gatekeeper.body/18-gatekeeper-foot-profile-l: label fragment (printed words)

### atlantis.06.plaza-twelve
- unclip: atlantis.06.plaza-twelve/elder-1: +373 px

### atlantis.06.shared-features-hands
- split: atlantis.06.shared-features-hands/calm (1504x178) -> 5 parts
- split: atlantis.06.shared-features-hands/eyel-eyer-brow-l-browr (1500x180) -> 5 parts
- split: atlantis.06.shared-features-hands/empty-hands-seven-left-right-pairs-14-hands (1502x178) -> 4 parts
- split: atlantis.06.shared-features-hands/eyel-eyer-brow-l-brow-r-mouth (1504x347) -> 14 parts
- label: atlantis.06.shared-features-hands/part: '' -> 'BROW' (was empty/garbled)
- label: atlantis.06.shared-features-hands/welcome: 'WELCOME' -> 'OPEN WELCOME' (re-read, more complete)
- label: atlantis.06.shared-features-hands/child-hand: 'CHILD HAND' -> 'HOLD CHILD HAND' (re-read, more complete)
- label: atlantis.06.shared-features-hands/guitar-3: 'GUITAR' -> 'GUITAR STRUM/PINCH' (closer label (cost 67 vs 1000000000); old text is pairs's)
- label: atlantis.06.shared-features-hands/candle: 'CANDLE' -> 'CANDLE CUP' (re-read, more complete)
- label: atlantis.06.shared-features-hands/lantern: 'LANTERN' -> 'OIL LANTERN HANDLE GRIP' (re-read, more complete)
- ref: atlantis.06.shared-features-hands/calm: section box: its 5 contents are cut as separate parts
- ref: atlantis.06.shared-features-hands/eyel-eyer-brow-l-browr: section box: its 5 contents are cut as separate parts
- ref: atlantis.06.shared-features-hands/empty-hands-seven-left-right-pairs-14-hands: section box: its 4 contents are cut as separate parts
- ref: atlantis.06.shared-features-hands/eyel-eyer-brow-l-brow-r-mouth: section box: its 14 contents are cut as separate parts
- added: atlantis.06.shared-features-hands/mouth
- added: atlantis.06.shared-features-hands/eyer
- added: atlantis.06.shared-features-hands/eyel
- added: atlantis.06.shared-features-hands/part
- added: atlantis.06.shared-features-hands/brow-l
- added: atlantis.06.shared-features-hands/eyer-2
- added: atlantis.06.shared-features-hands/mouth-2
- added: atlantis.06.shared-features-hands/eyel-2
- added: atlantis.06.shared-features-hands/brow-r
- added: atlantis.06.shared-features-hands/brow-l-2
- added: atlantis.06.shared-features-hands/mouth-3
- added: atlantis.06.shared-features-hands/brow-l-3
- added: atlantis.06.shared-features-hands/eyer-3
- added: atlantis.06.shared-features-hands/eyel-3
- added: atlantis.06.shared-features-hands/open
- added: atlantis.06.shared-features-hands/welcome
- added: atlantis.06.shared-features-hands/wave
- added: atlantis.06.shared-features-hands/wave-2
- added: atlantis.06.shared-features-hands/guitar
- added: atlantis.06.shared-features-hands/hold
- added: atlantis.06.shared-features-hands/guitar-2
- added: atlantis.06.shared-features-hands/child-hand
- added: atlantis.06.shared-features-hands/pairs
- added: atlantis.06.shared-features-hands/guitar-3
- added: atlantis.06.shared-features-hands/candle
- added: atlantis.06.shared-features-hands/cup
- added: atlantis.06.shared-features-hands/oil
- added: atlantis.06.shared-features-hands/lantern

### atlantis.06.source-actions
- split: atlantis.06.source-actions/child-traveler-run-cycle-five-instances (1415x347) -> 3 parts
- label: atlantis.06.source-actions/gatekeeper-traveler-1: 'GATEKEEPER TRAVELER_1' -> 'CITIZEN_1' (closer label (cost 63 vs 1000000000); old text is citizen-1's)
- label: atlantis.06.source-actions/citizen-1: 'CITIZEN_1' -> 'TRAVELER_1' (closer label (cost 59 vs 561); old text is gatekeeper-traveler-1's)
- label: atlantis.06.source-actions/part: '' -> 'TRAVELER_1' (was empty/garbled)
- ref: atlantis.06.source-actions/child-traveler-run-cycle-five-instances: section box: its 3 contents are cut as separate parts
- added: atlantis.06.source-actions/citizen-1
- added: atlantis.06.source-actions/part
- added: atlantis.06.source-actions/part-2

### atlantis.06.traveler_1.body
- label: atlantis.06.traveler_1.body/1-torso-front: '1 TORSO FRONT' -> '1 TRAVELER_1 TORSO FRONT' (re-read, more complete)
- label: atlantis.06.traveler_1.body/3-torso-profile: '3 TORSO PROFILE' -> 'TRAVELER_1 TORSO PROFILE' (re-read, more complete)
- label: atlantis.06.traveler_1.body/traveler-1-uarm-l: 'TRAVELER_1 UARM L' -> 'ACCESSORY' (closer label (cost 100 vs 1000000000); old text is 8-traveler-1-forearm-l's)
- label: atlantis.06.traveler_1.body/7-traveler-1-uarm-r: '7 TRAVELER_1 UARM R' -> 'TRAVELER_1 7 TRAVELER_1 L' (closer label (cost 30 vs 1000000000); old text is 8-traveler-1-forearm-l's)
- label: atlantis.06.traveler_1.body/9-forearm-r: '9 FOREARM R' -> 'TRAVELER_1 FOREARM' (old text not on the sheet; label 20px-cost away)
- label: atlantis.06.traveler_1.body/14-garment-overlay-front: '14 GARMENT OVERLAY FRONT' -> '14 TRAVELER_1 GARMENT OVERLAY FRONT' (re-read, more complete)
- label: atlantis.06.traveler_1.body/traveler-1-foot-r-front: 'TRAVELER_1 FOOT R FRONT' -> '17 TRAVELER_1 FRONT' (closer label (cost 10 vs 1000000000); old text is 1-torso-front's)

### atlantis.06.traveler_1.heads
- label: atlantis.06.traveler_1.heads/three-quarter: 'THREE-QUARTER' -> 'THREE-QUARTER RIGHT' (closer label (cost 35 vs 1000000000); old text is three-quarter-2's)
- label: atlantis.06.traveler_1.heads/profile: 'PROFILE' -> 'PROFILE RIGHT' (re-read, more complete)
- label: atlantis.06.traveler_1.heads/three-quarter-2: 'THREE-QUARTER' -> 'THREE-QUARTER BACK' (re-read, more complete)

### ex.01.action.ex_jacket.parts
- unclip: ex.01.action.ex_jacket.parts/uarm-l: +94 px
- label: ex.01.action.ex_jacket.parts/hip-connector-seat-lean: 'hip connector seat (lean' -> 'lean back torso (back view, leaning)' (closer label (cost 19 vs 69); old text is hip-connector's)
- label: ex.01.action.ex_jacket.parts/hip-connector-seat-fall-back: 'hip connector seat (fall back)' -> 'fall back torso (back view, falling, arched)' (closer label (cost 21 vs 69); old text is foot-l-2's)
- label: ex.01.action.ex_jacket.parts/part-5: '' -> 'farm.L' (was empty/garbled)
- label: ex.01.action.ex_jacket.parts/shin-r: 'shin.R' -> 'farm.R' (closer label (cost 19 vs 1000000000); old text is part-13's)
- label: ex.01.action.ex_jacket.parts/foot-l: 'foot.L' -> 'thigh.L' (closer label (cost 16 vs 37); old text is foot-l-3's)
- label: ex.01.action.ex_jacket.parts/part-13: '' -> 'shin.L' (was empty/garbled)
- label: ex.01.action.ex_jacket.parts/foot-l-2: 'foot.L' -> 'seat (fall back)' (closer label (cost 23 vs 161); old text is foot-l-3's)

### ex.02.action.ex_jacket.parts
- label: ex.02.action.ex_jacket.parts/head-back-view: 'head (back view)' -> 'claw' (closer label (cost 106 vs 172); old text is view's)
- label: ex.02.action.ex_jacket.parts/view: 'view)' -> 'head (back view)' (re-read, more complete)

### ex.03.action.ex_jacket.parts
- label: ex.03.action.ex_jacket.parts/torso-stand-back: 'torso stand back' -> 'torso stand back (armless, headless, legless)' (closer label (cost 11 vs 1000000000); old text is seat-stand-back's)
- label: ex.03.action.ex_jacket.parts/placement-only: 'placement only)' -> 'hand.R relaxed (empty)' (closer label (cost 65 vs 90); old text is assembled's)
- ref: ex.03.action.ex_jacket.parts/assembled: label says 'ASSEMBLED'

### ex.07.action.ex_jacket.parts
- split: ex.07.action.ex_jacket.parts/assembled-drererenge-d-main-pose-walk-away-back (1516x593) -> 15 parts
- split: ex.07.action.ex_jacket.parts/hand-l-hand-r-relaxed-relaxed (1516x343) -> 2 parts
- label: ex.07.action.ex_jacket.parts/thigh-r-hip-knee: 'thigh.R (hip-knee)' -> 'thigh.R (hip-knee) (knee-ankle) (knee-ankle)' (re-read, more complete)
- label: ex.07.action.ex_jacket.parts/torso-stand-back: 'torso (stand back)' -> 'torso (stand back) armless, headless, legless' (re-read, more complete)
- label: ex.07.action.ex_jacket.parts/seat-butt-stand: 'seat butt (stand)' -> 'seat butt (stand) separate piece' (re-read, more complete)
- label: ex.07.action.ex_jacket.parts/pelvis-connector-stand: 'pelvis connector (stand)' -> 'pelvis connector (stand) waist 2 thigh pivots' (re-read, more complete)
- label: ex.07.action.ex_jacket.parts/co: 'co' -> 'D - MAIN POSE / ASSEMBLED REFERENCE (walk away - back)' (was empty/garbled)
- label: ex.07.action.ex_jacket.parts/head-back-view: 'head (back view)' -> 'head (back view) separate piece' (re-read, more complete)
- ref: ex.07.action.ex_jacket.parts/assembled-drererenge-d-main-pose-walk-away-back: section box: its 15 contents are cut as separate parts
- ref: ex.07.action.ex_jacket.parts/hand-l-hand-r-relaxed-relaxed: section box: its 2 contents are cut as separate parts
- ref: ex.07.action.ex_jacket.parts/co: label says 'ASSEMBLED'
- ref: ex.07.action.ex_jacket.parts/head-back-view: under the band heading '_D~ MAIN POSE ASSEMBLED REFERENCE (walk '
- added: ex.07.action.ex_jacket.parts/thigh-l-hip-knee
- added: ex.07.action.ex_jacket.parts/thigh-r-hip-knee
- added: ex.07.action.ex_jacket.parts/uarm-r-shoulder-elbow
- added: ex.07.action.ex_jacket.parts/uarm-l-shoulder-elbow
- added: ex.07.action.ex_jacket.parts/torso-stand-back
- added: ex.07.action.ex_jacket.parts/shin-r-knee-ankle
- added: ex.07.action.ex_jacket.parts/shin-l-knee-ankle
- added: ex.07.action.ex_jacket.parts/farm-l-elbow-wrist
- added: ex.07.action.ex_jacket.parts/farm-r-elbow-wrist
- added: ex.07.action.ex_jacket.parts/seat-butt-stand
- added: ex.07.action.ex_jacket.parts/pelvis-connector-stand
- added: ex.07.action.ex_jacket.parts/foot-l
- added: ex.07.action.ex_jacket.parts/foot-r
- added: ex.07.action.ex_jacket.parts/hand-l-relaxed
- added: ex.07.action.ex_jacket.parts/hand-r-relaxed
- added: ex.07.action.ex_jacket.parts/co
- added: ex.07.action.ex_jacket.parts/head-back-view

### ex.09.crouch-parts
- split: ex.09.crouch-parts/5a-crouch-6a-crouch (782x443) -> 2 parts
- split: ex.09.crouch-parts/4a-crouch-threequarter-back-torso (781x443) -> 2 parts
- recut: ex.09.crouch-parts/4a-crouch: framed panel [21, 105, 782, 351] -> figure [276, 109, 271, 313]
- recut: ex.09.crouch-parts/crouch-threequarter-back: framed panel [846, 105, 781, 351] -> figure [1107, 109, 230, 307]
- label: ex.09.crouch-parts/4a-crouch: '4A. CROUCH' -> '1A. CROUCH BACK TORSO' (printed in its panel)
- label: ex.09.crouch-parts/crouch-threequarter-back: 'CROUCH THREEQUARTER-BACK' -> 'THREEQUARTER-BACK' (printed in its panel)
- label: ex.09.crouch-parts/crouch-back-hip-bridge: 'CROUCH BACK HIP BRIDGE' -> '2A. CROUCH BACK HIP BRIDGE' (re-read, more complete)
- label: ex.09.crouch-parts/threequarter-back: 'THREEQUARTER-BACK' -> '5A. CROUCH THREEQUARTER-BACK HIP' (re-read, more complete)
- ref: ex.09.crouch-parts/5a-crouch-6a-crouch: section box: its 2 contents are cut as separate parts
- ref: ex.09.crouch-parts/4a-crouch-threequarter-back-torso: section box: its 2 contents are cut as separate parts
- added: ex.09.crouch-parts/crouch-back-hip-bridge
- added: ex.09.crouch-parts/3a-crouch-back-rear-seat
- added: ex.09.crouch-parts/threequarter-back
- added: ex.09.crouch-parts/6a-crouch-threequarter-back-rear-seat

### ex.09.dissolve-state02
- label: ex.09.dissolve-state02/02-back: '02 BACK' -> '02 BACK TORSO' (re-read, more complete)
- label: ex.09.dissolve-state02/01-rear-head-2: '01 REAR HEAD' -> '05 UPPER L' (closer label (cost 2 vs 34); old text is 01-rear-head's)
- label: ex.09.dissolve-state02/02-back-2: '02 BACK' -> '06 FOREARM L' (closer label (cost 2 vs 54); old text is 02-back's)
- label: ex.09.dissolve-state02/07-arm: '07 ARM' -> '07 UPPER ARM' (re-read, more complete)
- label: ex.09.dissolve-state02/r: 'R' -> '11 THIGH' (was empty/garbled)
- label: ex.09.dissolve-state02/14-r: '14 R' -> '14 FOOT' (was empty/garbled)

### ex.09.dissolve-state03
- label: ex.09.dissolve-state03/06-forearm: '06 FOREARM' -> 'FOREARM L' (closer label (cost 34 vs 1000000000); old text is 08-forearm's)

### ex.ex_jacket.hands
- label: ex.ex_jacket.hands/open-palm: 'open palm' -> 'open back' (closer label (cost 38 vs 52); old text is peace-back's)
- label: ex.ex_jacket.hands/pinch-palm: 'pinch palm' -> 'pinch back' (closer label (cost 42 vs 47); old text is cup-back's)
- label: ex.ex_jacket.hands/thumb-back: 'thumb back' -> 'relaxed palm' (closer label (cost 32 vs 47); old text is thumb-palm's)
- label: ex.ex_jacket.hands/peace-back: 'peace back' -> 'open palm' (closer label (cost 22 vs 44); old text is peace-palm's)
- label: ex.ex_jacket.hands/thumb-palm: 'thumb palm' -> 'thumb back' (closer label (cost 25 vs 36); old text is 24-right-hand-shapes's)
- label: ex.ex_jacket.hands/peace-palm: 'peace palm' -> 'peace back' (closer label (cost 15 vs 40); old text is and-back-eyelet-tabs's)
- label: ex.ex_jacket.hands/wave-palm: 'wave palm' -> 'wave back' (closer label (cost 29 vs 1000000000); old text is and-back-eyelet-tabs's)
- label: ex.ex_jacket.hands/24-right-hand-shapes: '24 right-hand shapes' -> 'thumb palm' (closer label (cost 21 vs 74))
- label: ex.ex_jacket.hands/and-back-eyelet-tabs: 'and back eyelet tabs' -> 'peace palm' (closer label (cost 15 vs 71))

### ex.ex_jacket.hipcore
- split: ex.ex_jacket.hipcore/hip-bridge-5-rear-seat (577x301) -> 2 parts
- recut: ex.ex_jacket.hipcore/3-waist-link: framed panel [735, 120, 178, 461] -> figure [770, 292, 110, 162]
- recut: ex.ex_jacket.hipcore/4-hip-bridge: framed panel [927, 120, 314, 461] -> figure [940, 303, 288, 205]
- recut: ex.ex_jacket.hipcore/5-rear-seat: framed panel [1254, 120, 373, 461] -> figure [1264, 217, 354, 313]
- label: ex.ex_jacket.hipcore/2-torso-3q-back: '2. TORSO 3Q BACK' -> '2. TORSO 3Q BACK 3. 3. WAIST LINK' (closer label (cost 35 vs 1000000000); old text is 1-torso-back's)
- label: ex.ex_jacket.hipcore/proofs: 'PROOFS' -> 'SMALL ASSEMBLY PROOFS' (re-read, more complete)
- ref: ex.ex_jacket.hipcore/hip-rear: label fragment (printed words)
- ref: ex.ex_jacket.hipcore/hip-bridge-5-rear-seat: section box: its 2 contents are cut as separate parts
- ref: ex.ex_jacket.hipcore/proofs: label says 'PROOFS'
- ref: ex.ex_jacket.hipcore/part: under the band heading 'SMALL ASSEMBLY PROOFS'
- added: ex.ex_jacket.hipcore/proofs
- added: ex.ex_jacket.hipcore/part

### ex.ex_jacket.master
- unclip: ex.ex_jacket.master/stand-front-back: +117 px
- label: ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01: 'back view neutral stand with vape pen (01)' -> 'IDENTITY (ASSEMBLED) stand (01)' (old text not on the sheet; label 6px-cost away)
- label: ex.ex_jacket.master/l-back: 'L back' -> 'slight L' (closer label (cost 8 vs 1000000000); old text is head-back's)
- label: ex.ex_jacket.master/r-back: 'R back' -> 'slight' (closer label (cost 9 vs 773))
- label: ex.ex_jacket.master/h1-relaxed-l-back: 'H1 relaxed.L back' -> 'PROPS (SEPARATE)' (closer label (cost 90 vs 104); old text is head-back's)
- label: ex.ex_jacket.master/h2-relaxed-r-back: 'H2 relaxed.R back' -> 'relaxed.L H2 relaxed.R' (closer label (cost 18 vs 1000000000); old text is head-back's)
- label: ex.ex_jacket.master/h6-back: 'H6 back' -> 'point.R' (closer label (cost 9 vs 1000000000); old text is head-back's)
- label: ex.ex_jacket.master/open-n-a-view: 'open (n/a view)' -> 'eyes open' (closer label (cost 9 vs 1000000000); old text is stand-front-back's)
- label: ex.ex_jacket.master/side-l-three-quarter-back: 'side L (three-quarter back)' -> 'side glance L' (old text not on the sheet; label 7px-cost away)
- label: ex.ex_jacket.master/side-r-three-quarter: 'side R (three-quarter' -> 'side glance' (old text not on the sheet; label 9px-cost away)
- ref: ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01: label says 'ASSEMBLED'
- ref: ex.ex_jacket.master/stand-front-back: under the band heading 'MAIN POSES (ASSEMBLED EXAMPLES)'
- ref: ex.ex_jacket.master/lean-back: under the band heading 'MAIN POSES (ASSEMBLED EXAMPLES)'
- ref: ex.ex_jacket.master/03-fall-back-04: under the band heading 'MAIN POSES (ASSEMBLED EXAMPLES)'
- ref: ex.ex_jacket.master/04-float-back-05-crouch-back-over-suitcase: under the band heading 'MAIN POSES (ASSEMBLED EXAMPLES)'
- ref: ex.ex_jacket.master/open-n-a-view: under the band heading 'MAIN POSES (ASSEMBLED EXAMPLES)'
- ref: ex.ex_jacket.master/eyes-closed-n-a-view: under the band heading 'MAIN POSES (ASSEMBLED EXAMPLES)'
- ref: ex.ex_jacket.master/side-l-three-quarter-back: under the band heading 'MAIN POSES (ASSEMBLED EXAMPLES)'
- ref: ex.ex_jacket.master/side-r-three-quarter: under the band heading 'MAIN POSES (ASSEMBLED EXAMPLES)'

### family.10.watcher-head-turns
- label: family.10.watcher-head-turns/right-eye: 'RIGHT EYE' -> 'AWE EXPRESSION PIECES' (closer label (cost 74 vs 220); old text is right-eye-2's)

### family.11.optional.action
- label: family.11.optional.action/05-forearm-elbow-wrist: '05 FOREARM elbow wrist' -> 'FOREARM L elbow wrist' (closer label (cost 16 vs 1000000000); old text is 07-forearm-elbow-wrist's)
- label: family.11.optional.action/08-hand-l-hand-open: '08 HAND L hand open' -> '08 HAND L open hand (palm forward)' (re-read, more complete)
- label: family.11.optional.action/09-hand-r-hand-open: '09 HAND R hand open' -> '09 HAND open hand (palm forward)' (old text not on the sheet; label 13px-cost away)

### family.12.brother_1.body
- recut: family.12.brother_1.body/15-brother-1-garment: framed panel [204, 428, 179, 316] -> figure [241, 478, 100, 262]
- recut: family.12.brother_1.body/brother-1-17-brother-1-l-front-front: framed panel [583, 428, 180, 316] -> figure [625, 480, 97, 258]
- recut: family.12.brother_1.body/18-brother-1-front-foot-l-profile: framed panel [772, 428, 180, 316] -> figure [813, 480, 103, 260]
- recut: family.12.brother_1.body/20-brother-1-foot: framed panel [1153, 428, 182, 316] -> figure [1197, 480, 92, 260]
- recut: family.12.brother_1.body/21-brother-1-foot-r-lifted-2: framed panel [1171, 752, 181, 218] -> figure [1183, 800, 158, 154]
- label: family.12.brother_1.body/15-brother-1-garment: '15 BROTHER_1 GARMENT' -> '7 BROTHER_1 UARM R' (printed in its panel)
- label: family.12.brother_1.body/brother-1-17-brother-1-l-front-front: 'BROTHER_1 17 BROTHER_1 L FRONT FRONT' -> 'BROTHER_1 FOREARM R' (printed in its panel)
- label: family.12.brother_1.body/18-brother-1-front-foot-l-profile: '18 BROTHER_1 FRONT FOOT L PROFILE' -> '10 BROTHER_1 THIGH' (printed in its panel)
- label: family.12.brother_1.body/20-brother-1-foot: '20 BROTHER_1 FOOT' -> 'BROTHER_1 SHIN L' (printed in its panel)
- label: family.12.brother_1.body/21-brother-1-foot-r-lifted-2: '21 BROTHER_1 FOOT R LIFTED' -> '20 BROTHER_1 FOOT L LIFTED' (printed in its panel)
- label: family.12.brother_1.body/6-brother-1-7-brother-1-uarm-l-uarm: '6 BROTHER_1 7 BROTHER_1 UARM L UARM' -> 'BROTHER_1 TORSO FRONT' (closer label (cost 44 vs 1000000000); old text is 16-overlay-ba-foot-l's)
- label: family.12.brother_1.body/8-brother-1-9-l: '8 BROTHER_1 9 L' -> 'BROTHER_1 TORSO BACK' (closer label (cost 44 vs 1000000000))
- label: family.12.brother_1.body/brother-1-10-thigh: 'BROTHER_1 10 THIGH' -> '3 BROTHER_1 TORSO PROFILE' (closer label (cost 29 vs 1000000000); old text is 19-brother-1-foot-r-profile's)
- label: family.12.brother_1.body/16-overlay-ba-foot-l: '16 OVERLAY BA FOOT L' -> 'BROTHER_1 FOREARM L' (closer label (cost 28 vs 48); old text is 17-brother-1-18-brother-1-front-foot-l-profile's)
- label: family.12.brother_1.body/15-brother-1-garment-overlay-ba: '15 BROTHER_1 GARMENT OVERLAY BA' -> '14 BROTHER_1 GARMENT OVERLAY FRONT' (closer label (cost 25 vs 79); old text is 16-brother-1-17-brother-1-foot-l-front-front's)
- label: family.12.brother_1.body/16-brother-1-17-brother-1-foot-l-front-front: '16 BROTHER_1 17 BROTHER_1 FOOT L FRONT FRONT' -> '15 BROTHER_1 GARMENT OVERLAY BACK' (closer label (cost 24 vs 74); old text is 17-brother-1-18-brother-1-front-foot-l-profile's)
- label: family.12.brother_1.body/17-brother-1-18-brother-1-front-foot-l-profile: '17 BROTHER_1 18 BROTHER_1 FRONT FOOT L PROFILE' -> '16 BROTHER_1 FOOT L FRONT' (closer label (cost 24 vs 288); old text is 20-brother-1-19-brother-1-foot-foot-r-profile's)
- label: family.12.brother_1.body/18-brother-1-19-brother-1-foot-l-profile-foot: '18 BROTHER_1 19 BROTHER_1 FOOT L PROFILE FOOT' -> '17 BROTHER_1 FOOT FRONT' (closer label (cost 24 vs 73); old text is 20-brother-1-19-brother-1-foot-foot-r-profile's)
- label: family.12.brother_1.body/20-brother-1-19-brother-1-foot-foot-r-profile: '20 BROTHER_1 19 BROTHER_1 FOOT FOOT R PROFILE' -> '18 BROTHER_1 FOOT L PROFILE' (closer label (cost 26 vs 74); old text is 20-brother-1-21-foot-foot's)
- label: family.12.brother_1.body/20-brother-1-21-foot-foot: '20 BROTHER_1 21 FOOT FOOT' -> '19 BROTHER_1 FOOT PROFILE' (closer label (cost 26 vs 380); old text is 18-brother-1-19-brother-1-foot-l-profile-foot's)
- label: family.12.brother_1.body/family-12-brother-1-body: 'family.12.brother_1.body' -> '21 BROTHER_1 FOOT LIFTED' (closer label (cost 25 vs 1000000000))

### family.12.brother_1.heads-hands
- split: family.12.brother_1.heads-hands/laughing-laughing-eyes-laughing-brows-pair (312x341) -> 5 parts
- split: family.12.brother_1.heads-hands/sad-sad-eyes-sad-brows-pair (313x346) -> 4 parts
- split: family.12.brother_1.heads-hands/back-head-back (309x347) -> 4 parts
- split: family.12.brother_1.heads-hands/l-grip-r-grip-l-cup-r-cup-l-open-r-open-football (1279x236) -> 2 parts
- ref: family.12.brother_1.heads-hands/laughing-laughing-eyes-laughing-brows-pair: section box: its 5 contents are cut as separate parts
- ref: family.12.brother_1.heads-hands/sad-sad-eyes-sad-brows-pair: section box: its 4 contents are cut as separate parts
- ref: family.12.brother_1.heads-hands/back-head-back: section box: its 4 contents are cut as separate parts
- ref: family.12.brother_1.heads-hands/l-grip-r-grip-l-cup-r-cup-l-open-r-open-football: section box: its 2 contents are cut as separate parts
- added: family.12.brother_1.heads-hands/joy
- added: family.12.brother_1.heads-hands/pair
- added: family.12.brother_1.heads-hands/pair-2
- added: family.12.brother_1.heads-hands/joy-2
- added: family.12.brother_1.heads-hands/joy-mouth
- added: family.12.brother_1.heads-hands/calm
- added: family.12.brother_1.heads-hands/eyes-pair
- added: family.12.brother_1.heads-hands/brows-pair
- added: family.12.brother_1.heads-hands/calm-mouth
- added: family.12.brother_1.heads-hands/sad
- added: family.12.brother_1.heads-hands/pair-3
- added: family.12.brother_1.heads-hands/pair-4
- added: family.12.brother_1.heads-hands/sad-mouth
- added: family.12.brother_1.heads-hands/welcome
- added: family.12.brother_1.heads-hands/back

### family.12.friend_1.body
- recut: family.12.friend_1.body/4-friend-1-hip-bridge: framed panel [640, 61, 190, 270] -> figure [663, 134, 141, 125]
- label: family.12.friend_1.body/2-torso-back: '2. TORSO BACK' -> 'FRIEND 1 TORSO BACK' (re-read, more complete)
- label: family.12.friend_1.body/7-friend-1-uarm-r: '7. FRIEND_1 UARM R' -> '7. FRIEND 1 UARM (shoulder elbow)' (closer label (cost 10 vs 1000000000))
- label: family.12.friend_1.body/9-friend-1-forearm-r: '9. FRIEND_1 FOREARM R' -> '9. FRIEND_1 FOREARM (elbow wrist)' (re-read, more complete)
- label: family.12.friend_1.body/10-friend-1-thigh-l: '10. FRIEND_1 THIGH L' -> '1 (hip knee)' (closer label (cost 3 vs 15))
- label: family.12.friend_1.body/11-thigh-r: '11. THIGH R' -> '1 (hip knee)' (closer label (cost 2 vs 1000000000))
- label: family.12.friend_1.body/12-friend-1-shin-l: '12. FRIEND_1 SHIN L' -> '1 (knee ankle)' (closer label (cost 5 vs 16))
- label: family.12.friend_1.body/13-friend-1-shin-r: '13. FRIEND_1 SHIN R' -> '1 (knee ankle)' (closer label (cost 6 vs 16))
- label: family.12.friend_1.body/19-foot-r-profile: '19. FOOT R PROFILE' -> '19. FRIEND_1 FOOT PROFILE' (closer label (cost 17 vs 1000000000); old text is 3-friend-torso-profile's)

### family.12.friend_1.heads-hands
- unclip: family.12.friend_1.heads-hands/profile-3: +151 px
- label: family.12.friend_1.heads-hands/8-mouth: '8. MOUTH' -> '8. MOUTH (JOY)' (re-read, more complete)
- label: family.12.friend_1.heads-hands/10-brows-laughing: '10. BROWS (LAUGHING)' -> 'LAUGHING (OPEN LAUGH)' (closer label (cost 32 vs 1000000000); old text is 9-eyes-laughing's)
- label: family.12.friend_1.heads-hands/11-mouth-laughing: '11. MOUTH (LAUGHING)' -> '10. BROWS (LAUGHING) 11. MOUTH (LAUGHING)' (re-read, more complete)

### family.12.friend_2.body
- recut: family.12.friend_2.body/8-friend-2-9-forearm-l: framed panel [11, 58, 247, 329] -> figure [24, 113, 222, 260]
- recut: family.12.friend_2.body/friend-2-10-friend-2-forearm-r-thigh: framed panel [265, 58, 256, 329] -> figure [280, 114, 227, 260]
- recut: family.12.friend_2.body/11-friend-2-thig: framed panel [528, 57, 184, 329] -> figure [551, 112, 138, 260]
- recut: family.12.friend_2.body/friend-2-12-friend-2-shin-l: framed panel [719, 58, 212, 328] -> figure [742, 174, 163, 144]
- recut: family.12.friend_2.body/13-friend-2-shin: framed panel [937, 58, 227, 329] -> figure [947, 156, 208, 202]
- recut: family.12.friend_2.body/14-friend-2-garment: framed panel [1171, 57, 175, 330] -> figure [1204, 115, 97, 251]
- recut: family.12.friend_2.body/overlay-front: framed panel [1352, 57, 174, 330] -> figure [1397, 115, 97, 252]
- recut: family.12.friend_2.body/15-friend-2-garment-overlay: framed panel [11, 396, 196, 316] -> figure [61, 454, 90, 249]
- recut: family.12.friend_2.body/16-friend-2-back-foot-l-front: framed panel [214, 396, 195, 316] -> figure [266, 454, 90, 248]
- recut: family.12.friend_2.body/17-friend-2-front-foot-r-front: framed panel [416, 396, 196, 317] -> figure [467, 445, 107, 259]
- recut: family.12.friend_2.body/18-friend-2-front-foot-l-profile: framed panel [619, 396, 195, 316] -> figure [657, 445, 106, 259]
- recut: family.12.friend_2.body/19-friend-2-profile-foot-r: framed panel [827, 397, 191, 316] -> figure [879, 450, 77, 250]
- recut: family.12.friend_2.body/20-friend-2-l-profile-foot: framed panel [1023, 397, 179, 316] -> figure [1074, 451, 77, 250]
- recut: family.12.friend_2.body/21-friend-2-l-lifted-foot-r-lifted: framed panel [1216, 397, 310, 316] -> figure [1224, 480, 288, 202]
- recut: family.12.friend_2.body/16-friend-2-17-foot-l-front: framed panel [11, 722, 271, 251] -> figure [19, 788, 252, 179]
- recut: family.12.friend_2.body/17-friend-2-18-foot-r-front: framed panel [288, 722, 192, 251] -> figure [318, 791, 120, 167]
- recut: family.12.friend_2.body/18-friend-2-19-foot-l-profile: framed panel [485, 722, 193, 251] -> figure [517, 791, 121, 167]
- recut: family.12.friend_2.body/family-12-friend-2-body: framed panel [683, 722, 212, 251] -> figure [699, 812, 183, 126]
- recut: family.12.friend_2.body/20-friend-2-l-foot-lifted: framed panel [900, 722, 203, 251] -> figure [913, 812, 175, 126]
- recut: family.12.friend_2.body/21-friend-2-foot-r-lifted: framed panel [1108, 722, 215, 251] -> figure [1115, 789, 181, 159]
- recut: family.12.friend_2.body/part-21: framed panel [1328, 722, 198, 251] -> figure [1348, 789, 167, 162]
- label: family.12.friend_2.body/8-friend-2-9-forearm-l: '8. FRIEND_2 9. FOREARM L' -> '1. FRIEND_2 TORSO' (printed in its panel)
- label: family.12.friend_2.body/friend-2-10-friend-2-forearm-r-thigh: 'FRIEND_2 10. FRIEND_2 FOREARM R THIGH' -> '2. FRIEND_2 TORSO' (printed in its panel)
- label: family.12.friend_2.body/11-friend-2-thig: '11. FRIEND_2 THIG' -> '3. FRIEND_2 TORSO' (printed in its panel)
- label: family.12.friend_2.body/14-friend-2-garment: '14. FRIEND_2 GARMENT' -> '6. FRIEND_2 UARM L' (printed in its panel)
- label: family.12.friend_2.body/overlay-front: 'OVERLAY FRONT' -> 'FRIEND_2 UARM R' (printed in its panel)
- label: family.12.friend_2.body/15-friend-2-garment-overlay: '15. FRIEND_2 GARMENT OVERLAY' -> 'FRIEND_2 FOREARM L' (printed in its panel)
- label: family.12.friend_2.body/16-friend-2-back-foot-l-front: '16. FRIEND_2 BACK FOOT L FRONT' -> 'FRIEND_2 FOREARM R' (printed in its panel)
- label: family.12.friend_2.body/17-friend-2-front-foot-r-front: '17. FRIEND_2 FRONT FOOT R FRONT' -> 'FRIEND_2 THIGH L' (printed in its panel)
- label: family.12.friend_2.body/18-friend-2-front-foot-l-profile: '18. FRIEND_2 FRONT FOOT L PROFILE' -> '11. FRIEND_2 THIGH R' (printed in its panel)
- label: family.12.friend_2.body/19-friend-2-profile-foot-r: '19. FRIEND_2 PROFILE FOOT R' -> 'FRIEND_2 SHIN L' (printed in its panel)
- label: family.12.friend_2.body/20-friend-2-l-profile-foot: '20. FRIEND_2 L PROFILE FOOT' -> 'FRIEND_2 SHIN R' (printed in its panel)
- label: family.12.friend_2.body/21-friend-2-l-lifted-foot-r-lifted: '21. FRIEND_2 L LIFTED FOOT R LIFTED' -> 'GARMENT OVERLAY FRONT' (printed in its panel)
- label: family.12.friend_2.body/16-friend-2-17-foot-l-front: '16. FRIEND_2 17. FOOT L FRONT' -> '15. FRIEND_2 GARMENT OVERLAY BACK' (printed in its panel)
- label: family.12.friend_2.body/17-friend-2-18-foot-r-front: '17. FRIEND_2 18. FOOT R FRONT' -> '16. FRIEND_2 FOOT L FRONT' (printed in its panel)
- label: family.12.friend_2.body/18-friend-2-19-foot-l-profile: '18. FRIEND_2 19. FOOT L PROFILE' -> '17. FRIEND_2 FOOT R FRONT' (printed in its panel)
- label: family.12.friend_2.body/family-12-friend-2-body: 'family.12.friend_2.body' -> 'FOOT L PROFILE' (printed in its panel)
- label: family.12.friend_2.body/20-friend-2-l-foot-lifted: '20. FRIEND_2 L FOOT LIFTED' -> 'FOOT R PROFILE' (printed in its panel)
- label: family.12.friend_2.body/21-friend-2-foot-r-lifted: '21. FRIEND_2 FOOT R LIFTED' -> '20. FRIEND_2 L FOOT LIFTED' (printed in its panel)
- label: family.12.friend_2.body/part-21: '' -> '21. FRIEND_2 FOOT R LIFTED' (printed in its panel)

### family.12.friend_2.heads-hands
- split: family.12.friend_2.heads-hands/c-action-hands-empty-hands-wrist-tab-only (1490x195) -> 9 parts
- label: family.12.friend_2.heads-hands/part: '' -> 'JOY EYE PAIR' (was empty/garbled)
- label: family.12.friend_2.heads-hands/part-2: '' -> 'FACIAL FEATURES (separate cards) JOY' (was empty/garbled)
- label: family.12.friend_2.heads-hands/part-3: '' -> 'JOY MOUTH' (was empty/garbled)
- label: family.12.friend_2.heads-hands/part-4: '' -> 'LAUGHING EYE PAIR' (was empty/garbled)
- label: family.12.friend_2.heads-hands/part-5: '' -> 'LAUGHING EYE PAIR' (was empty/garbled)
- label: family.12.friend_2.heads-hands/part-6: '' -> '11 LAUGHING MOUTH' (was empty/garbled)
- label: family.12.friend_2.heads-hands/part-7: '' -> '4 THREEQUARTER BACK' (was empty/garbled)
- label: family.12.friend_2.heads-hands/part-8: '' -> '12 CALM EYE PAIR' (was empty/garbled)
- label: family.12.friend_2.heads-hands/part-9: '' -> '14 CALM MOUTH' (was empty/garbled)
- ref: family.12.friend_2.heads-hands/c-action-hands-empty-hands-wrist-tab-only: section box: its 9 contents are cut as separate parts
- added: family.12.friend_2.heads-hands/part
- added: family.12.friend_2.heads-hands/part-2
- added: family.12.friend_2.heads-hands/part-3
- added: family.12.friend_2.heads-hands/part-4
- added: family.12.friend_2.heads-hands/part-5
- added: family.12.friend_2.heads-hands/part-6
- added: family.12.friend_2.heads-hands/part-7
- added: family.12.friend_2.heads-hands/part-8
- added: family.12.friend_2.heads-hands/part-9

### family.12.hug-restage
- label: family.12.hug-restage/assembled: 'ASSEMBLED' -> 'POET' (closer label (cost 38 vs 181))

### family.13.couple-orbits
- label: family.13.couple-orbits/seated-lean: 'SEATED LEAN' -> 'DAY SEATED LEAN' (re-read, more complete)
- label: family.13.couple-orbits/seated-lean-3: 'SEATED LEAN' -> 'POSE' (closer label (cost 44 vs 414); old text is seated-lean's)
- label: family.13.couple-orbits/dusk-slow-one-third-turn-3: 'DUSK SLOW ONE-THIRD TURN' -> 'separate components supplied in each actor’s kit' (closer label (cost 34 vs 386); old text is dusk-slow-one-third-turn's)

### family.13.couple_1_a.body
- recut: family.13.couple_1_a.body/02-couple-1-a-torso-back: framed panel [22, 55, 306, 333] -> figure [49, 67, 249, 269]
- recut: family.13.couple_1_a.body/03-couple-1-a-torso-profile: framed panel [340, 55, 311, 333] -> figure [370, 67, 249, 266]
- recut: family.13.couple_1_a.body/04-couple-1-a-hip-bridge: framed panel [664, 55, 208, 333] -> figure [700, 66, 139, 269]
- recut: family.13.couple_1_a.body/05-couple-1-a-rear-seat-butt: framed panel [883, 55, 302, 333] -> figure [927, 105, 213, 201]
- recut: family.13.couple_1_a.body/part-5: framed panel [1196, 55, 318, 333] -> figure [1228, 104, 255, 206]
- recut: family.13.couple_1_a.body/07-couple-1-a-08-uarm-r: framed panel [22, 403, 174, 304] -> figure [60, 415, 89, 232]
- recut: family.13.couple_1_a.body/08-couple-1-a-09-forearm-l: framed panel [208, 403, 175, 304] -> figure [249, 415, 88, 234]
- recut: family.13.couple_1_a.body/09-10-forearm-r: framed panel [395, 403, 177, 304] -> figure [446, 426, 73, 213]
- recut: family.13.couple_1_a.body/10-couple-1-a-11-thigh-l: framed panel [584, 403, 178, 304] -> figure [636, 426, 72, 214]
- recut: family.13.couple_1_a.body/11-couple-1-a-12-thigh-r: framed panel [773, 403, 180, 304] -> figure [820, 413, 84, 239]
- recut: family.13.couple_1_a.body/12-couple-1-a-13-shin-l: framed panel [965, 403, 180, 304] -> figure [1012, 413, 85, 239]
- recut: family.13.couple_1_a.body/13-couple-1-a-shinr: framed panel [1157, 403, 177, 304] -> figure [1213, 424, 68, 223]
- recut: family.13.couple_1_a.body/seat-butt: framed panel [1344, 403, 170, 304] -> figure [1398, 422, 68, 225]
- recut: family.13.couple_1_a.body/15-couple-1-a-garment-overlay-back: framed panel [22, 722, 256, 241] -> figure [40, 743, 224, 163]
- recut: family.13.couple_1_a.body/16-couple-1-a-17-couple-1-a-foot-l-front-foot-r-: framed panel [287, 722, 245, 241] -> figure [299, 743, 225, 161]
- recut: family.13.couple_1_a.body/17-couple-1-a-18-couple-1-a-foot-r-front-foot-l: framed panel [538, 722, 137, 241] -> figure [569, 746, 80, 154]
- recut: family.13.couple_1_a.body/18-couple-1-a-19-couple-1-a-foot-l-profile-foot: framed panel [682, 722, 138, 241] -> figure [705, 746, 80, 153]
- recut: family.13.couple_1_a.body/19-couple-1-a-20-couple-1-a-foot-r-profile-foot: framed panel [828, 722, 167, 241] -> figure [844, 761, 136, 116]
- recut: family.13.couple_1_a.body/20-couple-1-a-21-couple-1-a-foot-l-lifted-foot: framed panel [1004, 722, 163, 241] -> figure [1018, 759, 135, 118]
- recut: family.13.couple_1_a.body/21-couple-1-a-foot-r-lifted: framed panel [1176, 722, 160, 241] -> figure [1193, 741, 128, 157]
- recut: family.13.couple_1_a.body/family-13-couple-1-a-body: framed panel [1344, 722, 170, 241] -> figure [1361, 742, 135, 157]
- label: family.13.couple_1_a.body/02-couple-1-a-torso-back: '02. COUPLE_1_A TORSO BACK' -> '01. COUPLE_1_A TORSO FRONT' (printed in its panel)
- label: family.13.couple_1_a.body/03-couple-1-a-torso-profile: '03. COUPLE_1_A TORSO PROFILE' -> '02. COUPLE_1_A TORSO BACK' (printed in its panel)
- label: family.13.couple_1_a.body/04-couple-1-a-hip-bridge: '04. COUPLE_1_A HIP BRIDGE' -> '03. COUPLE_1_A TORSO PROFILE' (printed in its panel)
- label: family.13.couple_1_a.body/05-couple-1-a-rear-seat-butt: '05. COUPLE_1_A REAR SEAT BUTT' -> '04. HIP BRIDGE' (printed in its panel)
- label: family.13.couple_1_a.body/part-5: '' -> '05. COUPLE_1_A REAR SEAT BUTT' (printed in its panel)
- label: family.13.couple_1_a.body/07-couple-1-a-08-uarm-r: '07. COUPLE_1_A 08. UARM R' -> '06. COUPLE_1_A UARM L' (printed in its panel)
- label: family.13.couple_1_a.body/08-couple-1-a-09-forearm-l: '08. COUPLE_1_A 09. FOREARM L' -> '07 COUPLE_1_A UARM R' (printed in its panel)
- label: family.13.couple_1_a.body/09-10-forearm-r: '09. 10. FOREARM R' -> 'COUPLE_1_A FOREARM L' (printed in its panel)
- label: family.13.couple_1_a.body/10-couple-1-a-11-thigh-l: '10. COUPLE_1_A 11. THIGH L' -> 'COUPLE_1_A FOREARM R' (printed in its panel)
- label: family.13.couple_1_a.body/11-couple-1-a-12-thigh-r: '11. COUPLE_1_A 12. THIGH R' -> '10. COUPLE_1_A THIGH L' (printed in its panel)
- label: family.13.couple_1_a.body/12-couple-1-a-13-shin-l: '12. COUPLE_1_A 13. SHIN L' -> '11. COUPLE_1_A THIGH R' (printed in its panel)
- label: family.13.couple_1_a.body/13-couple-1-a-shinr: '13. COUPLE_1_A SHINR' -> 'COUPLE_1_A SHIN L' (printed in its panel)
- label: family.13.couple_1_a.body/seat-butt: 'SEAT BUTT' -> 'COUPLE_1_A SHINR' (printed in its panel)
- label: family.13.couple_1_a.body/15-couple-1-a-garment-overlay-back: '15. COUPLE_1_A GARMENT OVERLAY BACK' -> '14. GARMENT OVERLAY FRONT' (printed in its panel)
- label: family.13.couple_1_a.body/16-couple-1-a-17-couple-1-a-foot-l-front-foot-r-: '16. COUPLE_1_A 17. COUPLE_1_A FOOT L FRONT FOOT R FRONT' -> '15. A GARMENT OVERLAY BACK' (printed in its panel)
- label: family.13.couple_1_a.body/17-couple-1-a-18-couple-1-a-foot-r-front-foot-l: '17. COUPLE_1_A 18. COUPLE_1_A FOOT R FRONT FOOT L' -> '16. COUPLE_1_A FOOT L FRONT' (printed in its panel)
- label: family.13.couple_1_a.body/18-couple-1-a-19-couple-1-a-foot-l-profile-foot: '18. COUPLE_1_A 19. COUPLE_1_A FOOT L PROFILE FOOT' -> '17. COUPLE_1_A FOOT R FRONT' (printed in its panel)
- label: family.13.couple_1_a.body/19-couple-1-a-20-couple-1-a-foot-r-profile-foot: '19. COUPLE_1_A 20. COUPLE_1_A FOOT R PROFILE FOOT' -> '18. COUPLE_1_A FOOT L PROFILE' (printed in its panel)
- label: family.13.couple_1_a.body/20-couple-1-a-21-couple-1-a-foot-l-lifted-foot: '20. COUPLE_1_A 21. COUPLE_1_A FOOT L LIFTED FOOT' -> '19. FOOT R PROFILE' (printed in its panel)
- label: family.13.couple_1_a.body/21-couple-1-a-foot-r-lifted: '21. COUPLE_1_A FOOT R LIFTED' -> '20. COUPLE_1_A FOOT L LIFTED' (printed in its panel)
- label: family.13.couple_1_a.body/family-13-couple-1-a-body: 'family.13.couple_1_a.body' -> '21. COUPLE_1_A FOOT R LIFTED' (printed in its panel)

### family.13.couple_1_a.heads-hands
- label: family.13.couple_1_a.heads-hands/part-6: '' -> 'ase' (was empty/garbled)
- label: family.13.couple_1_a.heads-hands/part-7: '' -> 'JOY EYE PAIR' (was empty/garbled)
- label: family.13.couple_1_a.heads-hands/part-8: '' -> 'ase' (was empty/garbled)
- label: family.13.couple_1_a.heads-hands/part-9: '' -> 'JOY BROW PAIR' (was empty/garbled)
- label: family.13.couple_1_a.heads-hands/part-10: '' -> 'JOY MOUTH' (was empty/garbled)
- label: family.13.couple_1_a.heads-hands/part-11: '' -> 'eo' (was empty/garbled)
- label: family.13.couple_1_a.heads-hands/part-12: '' -> 'oe' (was empty/garbled)
- label: family.13.couple_1_a.heads-hands/part-14: '' -> 'CALM MOUTH' (was empty/garbled)
- label: family.13.couple_1_a.heads-hands/r-open: 'R OPEN' -> 'ASSEMBLED REFERENCES NOT CUT PARTS' (closer label (cost 82 vs 1000000000); old text is l-open's)
- ref: family.13.couple_1_a.heads-hands/r-open: label says 'ASSEMBLED'

### family.13.couple_1_b.body
- recut: family.13.couple_1_b.body/6-couple-1b-7-couple-1b-uarm-l-uarm-r: framed panel [22, 48, 308, 295] -> figure [83, 88, 215, 248]
- recut: family.13.couple_1_b.body/8-9-forearm-l: framed panel [338, 48, 286, 295] -> figure [379, 88, 215, 249]
- recut: family.13.couple_1_b.body/10-forearm-r: framed panel [632, 48, 268, 295] -> figure [682, 89, 149, 249]
- recut: family.13.couple_1_b.body/11-couple-1b-12-thigh-r-shin: framed panel [910, 48, 301, 295] -> figure [957, 146, 205, 148]
- recut: family.13.couple_1_b.body/13-shin-l-shin-r: framed panel [1220, 48, 297, 295] -> figure [1252, 132, 228, 187]
- recut: family.13.couple_1_b.body/14-garment-overlay: framed panel [23, 352, 175, 273] -> figure [68, 398, 85, 216]
- recut: family.13.couple_1_b.body/15-front: framed panel [205, 352, 183, 273] -> figure [270, 398, 85, 216]
- recut: family.13.couple_1_b.body/overlay-back: framed panel [395, 352, 182, 273] -> figure [458, 406, 69, 211]
- recut: family.13.couple_1_b.body/16-foot-l-front: framed panel [584, 352, 177, 273] -> figure [634, 406, 70, 211]
- recut: family.13.couple_1_b.body/17-front-foot: framed panel [768, 352, 189, 273] -> figure [821, 397, 80, 222]
- recut: family.13.couple_1_b.body/foot-r-front: framed panel [964, 352, 188, 273] -> figure [1012, 397, 81, 222]
- recut: family.13.couple_1_b.body/13-shin-r: framed panel [1159, 352, 179, 273] -> figure [1207, 413, 67, 203]
- recut: family.13.couple_1_b.body/part-13: framed panel [1345, 352, 171, 273] -> figure [1401, 413, 68, 203]
- recut: family.13.couple_1_b.body/16-foot-l-front-18-couple-1b-foot-profile: framed panel [320, 636, 298, 360] -> figure [330, 683, 274, 309]
- recut: family.13.couple_1_b.body/18-couple-1b-foot-profile: framed panel [626, 636, 242, 182] -> figure [709, 688, 92, 126]
- recut: family.13.couple_1_b.body/19-foot-r-profile: framed panel [878, 636, 226, 182] -> figure [936, 688, 91, 126]
- recut: family.13.couple_1_b.body/19-foot-r-profile-2: framed panel [623, 826, 240, 170] -> figure [659, 884, 165, 102]
- recut: family.13.couple_1_b.body/20-21-foot-l-lifted: framed panel [871, 826, 234, 170] -> figure [896, 885, 160, 101]
- recut: family.13.couple_1_b.body/21-foot-r-lifted: framed panel [1114, 823, 200, 173] -> figure [1139, 872, 128, 118]
- recut: family.13.couple_1_b.body/family-13-couple-1-b-body: framed panel [1321, 823, 193, 173] -> figure [1366, 873, 123, 118]
- label: family.13.couple_1_b.body/6-couple-1b-7-couple-1b-uarm-l-uarm-r: '6. COUPLE_1B 7. COUPLE_1B UARM L UARM R' -> 'TORSO FRONT' (printed in its panel)
- label: family.13.couple_1_b.body/8-9-forearm-l: '8 9 FOREARM L' -> 'TORSO BACK' (printed in its panel)
- label: family.13.couple_1_b.body/10-forearm-r: '10. FOREARM R' -> 'COUPLE_1B TORSO PROFILE' (printed in its panel)
- label: family.13.couple_1_b.body/13-shin-l-shin-r: '13. SHIN L SHIN R' -> 'REAR SEAT BUTT' (printed in its panel)
- label: family.13.couple_1_b.body/14-garment-overlay: '14. GARMENT OVERLAY' -> 'COUPLE_1B UARM L' (printed in its panel)
- label: family.13.couple_1_b.body/15-front: '15. FRONT' -> 'COUPLE_1B UARM R' (printed in its panel)
- label: family.13.couple_1_b.body/overlay-back: 'OVERLAY BACK' -> 'FOREARM L' (printed in its panel)
- label: family.13.couple_1_b.body/16-foot-l-front: '16. FOOT L FRONT' -> 'COUPLE 1B FOREARM R' (printed in its panel)
- label: family.13.couple_1_b.body/foot-r-front: 'FOOT R FRONT' -> 'COUPLE_1B THIGH R' (printed in its panel)
- label: family.13.couple_1_b.body/13-shin-r: '13. SHIN R' -> 'SHIN L' (printed in its panel)
- label: family.13.couple_1_b.body/part-13: '' -> 'SHIN R' (printed in its panel)
- label: family.13.couple_1_b.body/16-foot-l-front-18-couple-1b-foot-profile: '16. FOOT L FRONT 18. COUPLE_1B FOOT PROFILE' -> '15. COUPLE_1_B OVERLAY BACK' (printed in its panel)
- label: family.13.couple_1_b.body/18-couple-1b-foot-profile: '18. COUPLE_1B FOOT PROFILE' -> 'FOOT L FRONT' (printed in its panel)
- label: family.13.couple_1_b.body/19-foot-r-profile: '19. FOOT R PROFILE' -> 'FOOT R FRONT' (printed in its panel)
- label: family.13.couple_1_b.body/19-foot-r-profile-2: '19. FOOT R PROFILE' -> '18. FOOT L PROFILE' (printed in its panel)
- label: family.13.couple_1_b.body/20-21-foot-l-lifted: '20. 21. FOOT L LIFTED' -> '19. FOOT R PROFILE' (printed in its panel)
- label: family.13.couple_1_b.body/21-foot-r-lifted: '21. FOOT R LIFTED' -> '20. FOOT L LIFTED' (printed in its panel)
- label: family.13.couple_1_b.body/family-13-couple-1-b-body: 'family.13.couple_1_b.body' -> 'COUPLE_1_B FOOT R LIFTED' (printed in its panel)
- label: family.13.couple_1_b.body/17-front-foot: '17. FRONT FOOT' -> 'THIGH L' (old text not on the sheet; label 20px-cost away)
- label: family.13.couple_1_b.body/15-overlay-back: '15. OVERLAY BACK' -> 'GARMENT OVERLAY FRONT' (closer label (cost 28 vs 92))

### family.13.couple_1_b.heads-hands
- split: family.13.couple_1_b.heads-hands/l-oren-r-open-l-grip-partner-empty (747x126) -> 5 parts
- split: family.13.couple_1_b.heads-hands/r-grip-partner-empty-l-relaxed-r-relaxed (742x126) -> 4 parts
- label: family.13.couple_1_b.heads-hands/eyes-pair-2: 'EYES (PAIR)' -> 'EMPTY' (closer label (cost 43 vs 50))
- ref: family.13.couple_1_b.heads-hands/l-oren-r-open-l-grip-partner-empty: section box: its 5 contents are cut as separate parts
- ref: family.13.couple_1_b.heads-hands/r-grip-partner-empty-l-relaxed-r-relaxed: section box: its 4 contents are cut as separate parts
- added: family.13.couple_1_b.heads-hands/joy-mouth
- added: family.13.couple_1_b.heads-hands/eyes-pair
- added: family.13.couple_1_b.heads-hands/joy
- added: family.13.couple_1_b.heads-hands/pair
- added: family.13.couple_1_b.heads-hands/joy-brows
- added: family.13.couple_1_b.heads-hands/calm-mouth
- added: family.13.couple_1_b.heads-hands/eyes-pair-2
- added: family.13.couple_1_b.heads-hands/calm-brows
- added: family.13.couple_1_b.heads-hands/brows-pair

### family.13.couple_2_a.body
- split: family.13.couple_2_a.body/18-19-foot-l-profile-foot-r-profile (399x303) -> 2 parts
- split: family.13.couple_2_a.body/17-18-foot-r-front (440x260) -> 2 parts
- recut: family.13.couple_2_a.body/19-20-foot-r-profile: framed panel [652, 712, 208, 260] -> figure [664, 804, 181, 136]
- recut: family.13.couple_2_a.body/21-foot-r-lifted-2: framed panel [1072, 712, 219, 260] -> figure [1092, 766, 183, 172]
- label: family.13.couple_2_a.body/19-20-foot-r-profile: '19 20 FOOT R PROFILE' -> 'FOOT L PROFILE' (printed in its panel)
- label: family.13.couple_2_a.body/21-foot-r-lifted-2: '21 FOOT R LIFTED' -> '20 FOOT L LIFTED' (printed in its panel)
- label: family.13.couple_2_a.body/10-forearm-r-thigh: '10 FOREARM R THIGH' -> 'TORSO BACK' (closer label (cost 33 vs 63); old text is 17-front-foot-r-front's)
- label: family.13.couple_2_a.body/11-thigh: '11 THIGH' -> '3 COUPLE_2A TORSO PROFILE' (closer label (cost 25 vs 58); old text is couple-2-a's)
- label: family.13.couple_2_a.body/12-r-shin: '12 R SHIN' -> '4 COUPLE_2.A HIP' (old text not on the sheet; label 35px-cost away)
- label: family.13.couple_2_a.body/shin-l-r: 'SHIN L R' -> 'SEAT BUTT' (old text not on the sheet; label 36px-cost away)
- label: family.13.couple_2_a.body/garment-overlay-front: 'GARMENT OVERLAY FRONT' -> '7 COUPLE 2A UARM' (closer label (cost 29 vs 37); old text is 21-foot-r-lifted's)
- label: family.13.couple_2_a.body/15-garment-overlay: '15 GARMENT OVERLAY' -> 'COUPLE_2 A FOREARM L' (closer label (cost 24 vs 30); old text is 15-garment-overlay-back's)
- label: family.13.couple_2_a.body/16-back-foot-l-front: '16 BACK FOOT L FRONT' -> 'COUPLE _2.A FOREARM' (closer label (cost 26 vs 38); old text is 16-foot-l-front's)
- label: family.13.couple_2_a.body/17-front-foot-r-front: '17 FRONT FOOT R FRONT' -> '10 COUPLE A THIGH L' (old text not on the sheet; label 28px-cost away)
- label: family.13.couple_2_a.body/18-19-foot-l-profile: '18 19 FOOT L PROFILE' -> '17 COUPLE_2A FOOT FRONT' (closer label (cost 26 vs 124))
- label: family.13.couple_2_a.body/20-foot-l-lifted-2: '20 FOOT L LIFTED' -> 'FOOT PROFILE' (closer label (cost 33 vs 80))
- label: family.13.couple_2_a.body/family-13-couple-2-a-body: 'family.13.couple_2_a.body' -> '21 COUPLE 2A FOOT R LIFTED' (closer label (cost 31 vs 1000000000); old text is 20-foot-l-lifted's)
- label: family.13.couple_2_a.body/couple-2-a: 'COUPLE_2.A' -> '11 COUPLE 2A THIGH' (closer label (cost 21 vs 1000000000); old text is 20-foot-l-lifted's)
- label: family.13.couple_2_a.body/part: '' -> '12 COUPLE_2A SHIN L' (was empty/garbled)
- label: family.13.couple_2_a.body/15-garment-overlay-back: '15 GARMENT OVERLAY BACK' -> '15 COUPLE 2A GARMENT OVERLAY BACK' (re-read, more complete)
- label: family.13.couple_2_a.body/16-foot-l-front: '16 FOOT L FRONT' -> '16 COUPLE 2A FOOT L FRONT' (re-read, more complete)
- ref: family.13.couple_2_a.body/18-19-foot-l-profile-foot-r-profile: section box: its 2 contents are cut as separate parts
- ref: family.13.couple_2_a.body/17-18-foot-r-front: section box: its 2 contents are cut as separate parts
- added: family.13.couple_2_a.body/couple-2-a
- added: family.13.couple_2_a.body/part
- added: family.13.couple_2_a.body/15-garment-overlay-back
- added: family.13.couple_2_a.body/16-foot-l-front

### family.13.couple_2_a.heads-hands
- label: family.13.couple_2_a.heads-hands/part-6: '' -> '1 FRONT' (was empty/garbled)
- label: family.13.couple_2_a.heads-hands/part-7: '' -> 'FACIAL FEATURES (SEPARATE CARDS)' (was empty/garbled)
- label: family.13.couple_2_a.heads-hands/part-9: '' -> '4 THREEQUARTER BACK' (was empty/garbled)
- label: family.13.couple_2_a.heads-hands/11-mouth: '11 MOUTH' -> 'FOREARMS)' (closer label (cost 75 vs 306); old text is part-17's)
- label: family.13.couple_2_a.heads-hands/part-17: '' -> '11 CALM MOUTH' (was empty/garbled)
- ref: family.13.couple_2_a.heads-hands/part-8: label fragment (printed words)
- ref: family.13.couple_2_a.heads-hands/part-9: label fragment (printed words)

### family.13.couple_2_b.body
- split: family.13.couple_2_b.body/19-couple-2-20-foot-r-profile (323x344) -> 2 parts
- recut: family.13.couple_2_b.body/8-couple-2-b-9-forearm-l-forearm: framed panel [14, 60, 220, 310] -> figure [35, 113, 175, 253]
- recut: family.13.couple_2_b.body/11-couple-2-b-thigh-r: framed panel [466, 59, 209, 311] -> figure [494, 113, 142, 253]
- recut: family.13.couple_2_b.body/couple-2-b-15-overlay-front: framed panel [1130, 59, 192, 311] -> figure [1190, 122, 76, 227]
- recut: family.13.couple_2_b.body/15-couple-2-b-garment-overlay-back: framed panel [1328, 59, 194, 311] -> figure [1380, 122, 76, 227]
- recut: family.13.couple_2_b.body/16-couple-2-b-foot-l-front: framed panel [14, 378, 158, 344] -> figure [54, 447, 72, 241]
- recut: family.13.couple_2_b.body/17-couple-2-b-foot-r: framed panel [177, 378, 155, 344] -> figure [219, 444, 73, 243]
- recut: family.13.couple_2_b.body/foot-l-profile: framed panel [524, 378, 181, 344] -> figure [560, 426, 109, 274]
- recut: family.13.couple_2_b.body/20-couple-2-b-21-foot-l-lifted: framed panel [1034, 378, 251, 344] -> figure [1038, 431, 237, 287]
- recut: family.13.couple_2_b.body/18-foot-l-profile: framed panel [240, 729, 223, 251] -> figure [293, 787, 101, 186]
- recut: family.13.couple_2_b.body/19-couple-2-foot-r-profile: framed panel [468, 729, 255, 251] -> figure [505, 800, 197, 145]
- recut: family.13.couple_2_b.body/20-couple-2-b-foot-l-lifted: framed panel [730, 729, 261, 250] -> figure [758, 799, 194, 145]
- recut: family.13.couple_2_b.body/21-couple-2-b-foot-r-lifted-2: framed panel [997, 729, 257, 247] -> figure [1072, 794, 157, 163]
- recut: family.13.couple_2_b.body/family-13-couple-2-b-body: framed panel [1259, 729, 263, 250] -> figure [1285, 790, 159, 167]
- label: family.13.couple_2_b.body/8-couple-2-b-9-forearm-l-forearm: '8. COUPLE_2_B 9. FOREARM L FOREARM' -> '1. COUPLE 2 B TORSO' (printed in its panel)
- label: family.13.couple_2_b.body/11-couple-2-b-thigh-r: '11. COUPLE_2_B THIGH R' -> '3. B TORSO PROFILE' (printed in its panel)
- label: family.13.couple_2_b.body/couple-2-b-15-overlay-front: 'COUPLE_2_B 15. OVERLAY FRONT' -> 'COUPLE_2_B UARM L' (printed in its panel)
- label: family.13.couple_2_b.body/15-couple-2-b-garment-overlay-back: '15. COUPLE_2_B GARMENT OVERLAY BACK' -> 'COUPLE_2_B UARM R' (printed in its panel)
- label: family.13.couple_2_b.body/16-couple-2-b-foot-l-front: '16. COUPLE_2_B FOOT L FRONT' -> 'COUPLE_2_B FOREARM L' (printed in its panel)
- label: family.13.couple_2_b.body/17-couple-2-b-foot-r: '17. COUPLE_2_B FOOT R' -> 'COUPLE_2_B FOREARM R' (printed in its panel)
- label: family.13.couple_2_b.body/foot-l-profile: 'FOOT L PROFILE' -> '11. COUPLE_2_B THIGH R' (printed in its panel)
- label: family.13.couple_2_b.body/20-couple-2-b-21-foot-l-lifted: '20. COUPLE_2_B 21. FOOT L LIFTED' -> '14. COUPLE_2_B GARMENT OVERLAY FRONT' (printed in its panel)
- label: family.13.couple_2_b.body/18-foot-l-profile: '18. FOOT L PROFILE' -> 'COUPLE_2_B FOOT R FRONT' (printed in its panel)
- label: family.13.couple_2_b.body/19-couple-2-foot-r-profile: '19. COUPLE_2 FOOT R PROFILE' -> '18. FOOT L PROFILE' (printed in its panel)
- label: family.13.couple_2_b.body/20-couple-2-b-foot-l-lifted: '20. COUPLE_2_B FOOT L LIFTED' -> '19. FOOT R PROFILE' (printed in its panel)
- label: family.13.couple_2_b.body/21-couple-2-b-foot-r-lifted-2: '21. COUPLE_2_B FOOT R LIFTED' -> 'FOOT L LIFTED' (printed in its panel)
- label: family.13.couple_2_b.body/family-13-couple-2-b-body: 'family.13.couple_2_b.body' -> '21. COUPLE_2_B FOOT R LIFTED' (printed in its panel)
- label: family.13.couple_2_b.body/12-couple-2-b: '12. COUPLE_2_B' -> '12. COUPLE_2_B SHIN L' (closer label (cost 19 vs 712))
- label: family.13.couple_2_b.body/13-couple-2-b-14-couple-2-b-shin-r-garment: '13. COUPLE_2_B 14. COUPLE_2_B SHIN R GARMENT' -> '5. COUPLE_2_B REAR SEAT BUTT' (closer label (cost 31 vs 1000000000); old text is 12-couple-2-b's)
- label: family.13.couple_2_b.body/21-couple-2-b-foot-r-lifted: '21. COUPLE_2_B FOOT R LIFTED' -> '15. COUPLE B GARMENT OVERLAY BACK' (closer label (cost 23 vs 36))
- ref: family.13.couple_2_b.body/19-couple-2-20-foot-r-profile: section box: its 2 contents are cut as separate parts
- added: family.13.couple_2_b.body/couple-2-b-shinl
- added: family.13.couple_2_b.body/13-couple-2-b-shin-r

### family.13.couple_2_b.heads-hands
- split: family.13.couple_2_b.heads-hands/joy-features-calm-features (1300x353) -> 5 parts
- ref: family.13.couple_2_b.heads-hands/joy-features-calm-features: section box: its 5 contents are cut as separate parts
- added: family.13.couple_2_b.heads-hands/head-threequarter-back
- added: family.13.couple_2_b.heads-hands/1-head-front
- added: family.13.couple_2_b.heads-hands/5-head-back
- added: family.13.couple_2_b.heads-hands/2-head-threequarter
- added: family.13.couple_2_b.heads-hands/3-head-profile

### family.13.couple_3_a.body
- recut: family.13.couple_3_a.body/2-couple-3-a-torso-back: framed panel [27, 63, 299, 337] -> figure [57, 72, 235, 277]
- recut: family.13.couple_3_a.body/h-l-h-r-4-couple-3-a-bridge-hip: framed panel [665, 63, 207, 337] -> figure [697, 73, 141, 278]
- recut: family.13.couple_3_a.body/5-couple-3-a-rear-seat-butt: framed panel [888, 63, 276, 338] -> figure [930, 129, 187, 175]
- recut: family.13.couple_3_a.body/part-5: framed panel [1181, 63, 330, 338] -> figure [1208, 92, 270, 240]
- recut: family.13.couple_3_a.body/7-couple-3-a-8-uarm-r: framed panel [28, 419, 164, 278] -> figure [65, 427, 87, 219]
- recut: family.13.couple_3_a.body/8-couple-3-a-9-forearm-l: framed panel [210, 419, 171, 278] -> figure [247, 428, 89, 219]
- recut: family.13.couple_3_a.body/9-couple-3-a-10-forearm-r: framed panel [397, 419, 173, 278] -> figure [442, 429, 79, 219]
- recut: family.13.couple_3_a.body/10-couple-3-a-11-thigh-l: framed panel [583, 419, 171, 279] -> figure [626, 429, 80, 220]
- recut: family.13.couple_3_a.body/11-couple-3-a-12-thigh-r: framed panel [771, 419, 184, 279] -> figure [808, 428, 105, 222]
- recut: family.13.couple_3_a.body/12-couple-3-a-couple-3-a-shin: framed panel [970, 420, 183, 278] -> figure [1010, 428, 104, 222]
- recut: family.13.couple_3_a.body/couple-3-a-shin-r: framed panel [1167, 420, 162, 279] -> figure [1206, 430, 85, 218]
- recut: family.13.couple_3_a.body/butt: framed panel [1345, 420, 165, 279] -> figure [1385, 431, 82, 216]
- recut: family.13.couple_3_a.body/15-couple-3-a-garment-overlay-back: framed panel [28, 713, 237, 260] -> figure [34, 721, 226, 197]
- recut: family.13.couple_3_a.body/16-couple-3-a-17-couple-3-a-foot-l-front-foot-r: framed panel [281, 714, 231, 259] -> figure [285, 719, 222, 198]
- recut: family.13.couple_3_a.body/couple-3-a-17-couple-3-a-18-foot-r-foot-l: framed panel [528, 714, 130, 260] -> figure [542, 741, 99, 163]
- recut: family.13.couple_3_a.body/couple-3-a-19-couple-3-a-18-foot-l-profile-foot: framed panel [669, 714, 127, 259] -> figure [680, 739, 99, 164]
- recut: family.13.couple_3_a.body/19-couple-3-a-20-foot-r-profile: framed panel [808, 714, 163, 260] -> figure [812, 762, 152, 121]
- recut: family.13.couple_3_a.body/20-couple-3-a-21-foot-l-lifted: framed panel [985, 714, 165, 259] -> figure [991, 759, 155, 121]
- recut: family.13.couple_3_a.body/21-couple-3-a-foot-lifted: framed panel [1160, 714, 174, 260] -> figure [1176, 736, 140, 163]
- recut: family.13.couple_3_a.body/family-13-couple-3-a-body: framed panel [1346, 714, 165, 260] -> figure [1354, 738, 142, 160]
- label: family.13.couple_3_a.body/2-couple-3-a-torso-back: '2. COUPLE_3_A TORSO BACK' -> '1. COUPLE_3_A TORSO FRONT' (printed in its panel)
- label: family.13.couple_3_a.body/h-l-h-r-4-couple-3-a-bridge-hip: 'H-L H-R 4. COUPLE_3_A BRIDGE HIP' -> '3. COUPLE_3_A TORSO PROFILE' (printed in its panel)
- label: family.13.couple_3_a.body/part-5: '' -> '5. COUPLE_3_A REAR SEAT BUTT' (printed in its panel)
- label: family.13.couple_3_a.body/7-couple-3-a-8-uarm-r: '7. COUPLE_3_A 8. UARM R' -> '6. COUPLE_3_A' (printed in its panel)
- label: family.13.couple_3_a.body/8-couple-3-a-9-forearm-l: '8. COUPLE_3_A 9. FOREARM L' -> '7. COUPLE_3_A UARM R' (printed in its panel)
- label: family.13.couple_3_a.body/9-couple-3-a-10-forearm-r: '9. COUPLE_3_A 10. FOREARM R' -> 'COUPLE_3_A FOREARM L' (printed in its panel)
- label: family.13.couple_3_a.body/10-couple-3-a-11-thigh-l: '10. COUPLE_3_A 11. THIGH L' -> 'COUPLE_3_A FOREARM R' (printed in its panel)
- label: family.13.couple_3_a.body/11-couple-3-a-12-thigh-r: '11. COUPLE_3_A 12. THIGH R' -> '10. COUPLE_3_A THIGH L' (printed in its panel)
- label: family.13.couple_3_a.body/12-couple-3-a-couple-3-a-shin: '12. COUPLE_3_A COUPLE_3_A SHIN' -> '11. COUPLE_3_A THIGH R' (printed in its panel)
- label: family.13.couple_3_a.body/couple-3-a-shin-r: 'COUPLE_3_A SHIN R' -> '12. COUPLE_3_A' (printed in its panel)
- label: family.13.couple_3_a.body/butt: 'BUTT' -> '13. COUPLE_3_A SHIN R' (printed in its panel)
- label: family.13.couple_3_a.body/15-couple-3-a-garment-overlay-back: '15. COUPLE_3_A GARMENT OVERLAY BACK' -> '14. GARMENT OVERLAY FRONT' (printed in its panel)
- label: family.13.couple_3_a.body/16-couple-3-a-17-couple-3-a-foot-l-front-foot-r: '16. COUPLE_3_A 17. COUPLE_3_A FOOT L FRONT FOOT R' -> '15. GARMENT OVERLAY BACK' (printed in its panel)
- label: family.13.couple_3_a.body/couple-3-a-17-couple-3-a-18-foot-r-foot-l: 'COUPLE_3_A 17. COUPLE_3_A 18. FOOT R FOOT L' -> '16. COUPLE_3_A FOOT L FRONT' (printed in its panel)
- label: family.13.couple_3_a.body/couple-3-a-19-couple-3-a-18-foot-l-profile-foot: 'COUPLE_3_A 19. COUPLE_3_A 18. FOOT L PROFILE FOOT' -> '17. FOOT R FRONT' (printed in its panel)
- label: family.13.couple_3_a.body/19-couple-3-a-20-foot-r-profile: '19. COUPLE_3_A 20. FOOT R PROFILE' -> '18, COUPLE_3_A FOOT L PROFILE' (printed in its panel)
- label: family.13.couple_3_a.body/20-couple-3-a-21-foot-l-lifted: '20. COUPLE_3_A 21. FOOT L LIFTED' -> '19. COUPLE_3_A' (printed in its panel)
- label: family.13.couple_3_a.body/21-couple-3-a-foot-lifted: '21. COUPLE_3_A FOOT LIFTED' -> '20. COUPLE_3_A FOOT L LIFTED' (printed in its panel)
- label: family.13.couple_3_a.body/family-13-couple-3-a-body: 'family.13.couple_3_a.body' -> '21. COUPLE_3_A FOOT R LIFTED' (printed in its panel)
- label: family.13.couple_3_a.body/3-couple-3-a-torso-profile: '3. COUPLE_3_A TORSO PROFILE' -> '2. COUPLE 3_A TORSO BACK' (closer label (cost 45 vs 105))

### family.13.couple_3_a.heads-hands
- ref: family.13.couple_3_a.heads-hands/references-not-cut-parts-family-13-couple-3-a-he: label says 'REFERENCES'

### family.13.couple_3_b.body
- recut: family.13.couple_3_b.body/9-forearm-r-10-thigh-l-couple-3-b-forearm-r-coup: framed panel [618, 50, 276, 289] -> figure [659, 100, 175, 235]
- label: family.13.couple_3_b.body/9-forearm-r-10-thigh-l-couple-3-b-forearm-r-coup: '9. FOREARM R 10. THIGH L COUPLE_3_B FOREARM R COUPLE_3_B' -> 'TORSO PROFILE COUPLE_3_B TORSO PROFILE' (printed in its panel)
- label: family.13.couple_3_b.body/uarml-7-uarmr-uarml-couple-3-b: 'UARML 7. UARMR UARML COUPLE_3_B' -> 'COUPLE_3_B TORSO FRONT' (closer label (cost 12 vs 55); old text is front-15-front's)
- label: family.13.couple_3_b.body/8-forearm-l-uarmr-couple-3-b-forearm-l: '8. FOREARM L UARMR COUPLE_3_B FOREARM L' -> 'COUPLE_3_B TORSO BACK' (closer label (cost 14 vs 29); old text is garment-overlay-back-couple-3-b-garment-back's)
- label: family.13.couple_3_b.body/l-11-thigh-r-12-thigh-l-couple-3-b-thigh-r: 'L 11. THIGH R 12. THIGH L COUPLE_3_B THIGH R' -> 'COUPLE_3_B HIP BRIDGE' (closer label (cost 35 vs 71); old text is 17-foot-r-front-l-front-couple-3-b's)
- label: family.13.couple_3_b.body/front-15-front: 'FRONT 15. FRONT' -> '7. UARMR COUPLE_3_B - UARMR' (old text not on the sheet; label 23px-cost away)
- label: family.13.couple_3_b.body/17-foot-r-front-l-front-couple-3-b: '17, FOOT R FRONT L FRONT COUPLE_3_B' -> '10. THIGH L COUPLE_3_B THIGH L' (closer label (cost 23 vs 1000000000); old text is 20-foot-l-lifted-couple-3-b-foot-l-lifted's)
- label: family.13.couple_3_b.body/front-18-foot-l-foot-r-front-couple-3-b: 'FRONT 18. FOOT L FOOT R FRONT COUPLE_3_B' -> '11. THIGH R COUPLE_3_B' (closer label (cost 33 vs 1000000000); old text is 20-foot-l-lifted-couple-3-b-foot-l-lifted's)
- label: family.13.couple_3_b.body/l-profile-19-foot-l-profile: 'L PROFILE 19, FOOT L PROFILE' -> 'COUPLE_3_B SHINL' (old text not on the sheet; label 33px-cost away)
- label: family.13.couple_3_b.body/16-foot-l-couple-3-b: '16. FOOT L COUPLE_3_B' -> '9. FOREARM COUPLE_3_B - |' (closer label (cost 26 vs 37); old text is 20-foot-l-lifted-couple-3-b-foot-l-lifted's)
- label: family.13.couple_3_b.body/r-profile-foot-r-profile: 'R PROFILE FOOT R PROFILE' -> '13. SHINR COUPLE_3_B SHINR' (old text not on the sheet; label 21px-cost away)
- label: family.13.couple_3_b.body/garment-overlay-back-15-couple-3-b-garment-back: 'GARMENT OVERLAY BACK 15. COUPLE_3_B GARMENT BACK' -> '14. GARMENT OVERLAY FRONT COUPLE_3_B' (closer label (cost 26 vs 100); old text is 16-foot-l-front-couple-3-b-foot-front-l-20-foot-'s)
- label: family.13.couple_3_b.body/16-foot-l-front-couple-3-b-foot-front-l-20-foot-: '16. FOOT L FRONT COUPLE_3_B FOOT FRONT L 20. FOOT L LIFTED COUPLE_3_B FOOT L LIFTED' -> '15. GARMENT OVERLAY BACK COUPLE_3_B' (closer label (cost 24 vs 53); old text is 21-foot-r-lifted-couple-3-b-foot-r-lifted-2's)
- label: family.13.couple_3_b.body/part-21: '' -> '19, FOOT PROFILE COUPLE_3_B FOOT' (was empty/garbled)
- label: family.13.couple_3_b.body/21-foot-r-lifted-couple-3-b-foot-r-lifted-2: '21. FOOT R LIFTED COUPLE_3_B FOOT R LIFTED' -> '20. FOOT L LIFTED COUPLE_3_B FOOT L LIFTED' (closer label (cost 49 vs 76); old text is r-lifted-foot-r-lifted's)
- label: family.13.couple_3_b.body/r-lifted-foot-r-lifted: 'R LIFTED FOOT R LIFTED' -> '21. FOOT LIFTED COUPLE_3_B FOOT LIFTED' (re-read, more complete)

### family.13.couple_3_b.heads-hands
- ref: family.13.couple_3_b.heads-hands/d-assembled-references-not-cut-parts: label says 'ASSEMBLED'

### family.13.elder-prayer
- unclip: family.13.elder-prayer/ste-the-upright: +214 px
- unclip: family.13.elder-prayer/step-3-deeper-bow: +501 px
- unclip: family.13.elder-prayer/man: +1182 px
- unclip: family.13.elder-prayer/2-man-profile: +535 px
- unclip: family.13.elder-prayer/3-woman-front: +493 px
- unclip: family.13.elder-prayer/woman-kneel-family-13-elder-prayer: +597 px
- label: family.13.elder-prayer/man: 'MAN' -> 'KNEEL FRONT' (closer label (cost 25 vs 1000000000); old text is 2-man-profile's)
- label: family.13.elder-prayer/2-man-profile: '2 MAN PROFILE' -> '2 MAN KNEEL PROFILE' (re-read, more complete)
- label: family.13.elder-prayer/3-woman-front: '3 WOMAN FRONT' -> '3 WOMAN KNEEL FRONT' (re-read, more complete)
- label: family.13.elder-prayer/woman-kneel-family-13-elder-prayer: 'WOMAN KNEEL family.13.elder-prayer.' -> '4 WOMAN KNEEL PROFILE' (old text not on the sheet; label 16px-cost away)

### family.13.elder_man.body
- recut: family.13.elder_man.body/6-elder-man-7-elder-man-uarm-l-uarm-r: framed panel [10, 54, 285, 320] -> figure [38, 114, 224, 250]
- recut: family.13.elder_man.body/8-elder-man-9-forearm-l: framed panel [307, 54, 279, 320] -> figure [338, 110, 219, 253]
- recut: family.13.elder_man.body/elder-man-10-elder-man-forearm-r-thigh-l: framed panel [596, 54, 259, 320] -> figure [638, 111, 160, 252]
- recut: family.13.elder_man.body/11-elder-man-12-thigh-r: framed panel [866, 54, 278, 320] -> figure [915, 147, 180, 192]
- recut: family.13.elder_man.body/elder-man-13-elder-man-shin-l-shin-r: framed panel [1156, 54, 282, 320] -> figure [1180, 133, 235, 198]
- recut: family.13.elder_man.body/14-overlay: framed panel [10, 384, 165, 273] -> figure [54, 441, 79, 209]
- recut: family.13.elder_man.body/overlay-front: framed panel [184, 384, 165, 273] -> figure [228, 441, 81, 210]
- recut: family.13.elder_man.body/15-elder-man-garment-overlay: framed panel [358, 384, 176, 273] -> figure [409, 444, 74, 205]
- recut: family.13.elder_man.body/16-back-foot: framed panel [544, 384, 176, 273] -> figure [595, 444, 74, 203]
- recut: family.13.elder_man.body/e-elder-man-foot-l-front-foot: framed panel [729, 384, 178, 273] -> figure [780, 440, 82, 210]
- recut: family.13.elder_man.body/18-elder-man-foot-r-front-foot: framed panel [917, 384, 181, 273] -> figure [960, 440, 82, 211]
- recut: family.13.elder_man.body/elder-man-19-foot-l-profile: framed panel [1108, 384, 163, 273] -> figure [1156, 448, 70, 201]
- recut: family.13.elder_man.body/19-elder-man-foot-r-profile: framed panel [1281, 384, 159, 273] -> figure [1327, 449, 69, 199]
- recut: family.13.elder_man.body/15-elder-man-garment-overlay-back: framed panel [10, 666, 329, 386] -> figure [27, 722, 288, 322]
- recut: family.13.elder_man.body/e-elder-man-16-foot-front-foot-l-20-elder-man-fo: framed panel [350, 666, 310, 386] -> figure [371, 722, 269, 320]
- recut: family.13.elder_man.body/20: framed panel [670, 666, 179, 191] -> figure [713, 721, 100, 130]
- recut: family.13.elder_man.body/elder-man-foot-l-lifted: framed panel [856, 666, 180, 191] -> figure [894, 722, 98, 130]
- recut: family.13.elder_man.body/21-elder-man-foot: framed panel [1043, 666, 195, 191] -> figure [1058, 727, 167, 117]
- recut: family.13.elder_man.body/foot-r-lifted: framed panel [1247, 666, 194, 191] -> figure [1268, 729, 153, 114]
- recut: family.13.elder_man.body/21-elder-man-r-foot-lifted: framed panel [816, 865, 277, 187] -> figure [861, 907, 164, 141]
- recut: family.13.elder_man.body/family-13-elder-man-body: framed panel [1105, 865, 276, 187] -> figure [1160, 908, 182, 131]
- label: family.13.elder_man.body/6-elder-man-7-elder-man-uarm-l-uarm-r: '6. ELDER_MAN 7. ELDER_MAN UARM L UARM R' -> '1. ELDER_MAN TORSO FRONT' (printed in its panel)
- label: family.13.elder_man.body/8-elder-man-9-forearm-l: '8. ELDER_MAN 9. FOREARM L' -> '2. ELDER_MAN TORSO BACK' (printed in its panel)
- label: family.13.elder_man.body/elder-man-10-elder-man-forearm-r-thigh-l: 'ELDER_MAN 10. ELDER_MAN FOREARM R THIGH L' -> 'ELDER_MAN TORSO PROFILE' (printed in its panel)
- label: family.13.elder_man.body/elder-man-13-elder-man-shin-l-shin-r: 'ELDER_MAN 13. ELDER_MAN SHIN L SHIN R' -> 'REAR SEAT BUTT' (printed in its panel)
- label: family.13.elder_man.body/14-overlay: '14. OVERLAY' -> 'ELDER_MAN UARM L' (printed in its panel)
- label: family.13.elder_man.body/overlay-front: 'OVERLAY FRONT' -> 'ELDER_MAN UARM R' (printed in its panel)
- label: family.13.elder_man.body/15-elder-man-garment-overlay: '15. ELDER_MAN GARMENT OVERLAY' -> 'ELDER_MAN FOREARM L' (printed in its panel)
- label: family.13.elder_man.body/16-back-foot: '16. BACK FOOT' -> 'ELDER_MAN FOREARM R' (printed in its panel)
- label: family.13.elder_man.body/e-elder-man-foot-l-front-foot: 'E ELDER_MAN FOOT L FRONT FOOT' -> 'ELDER_MAN THIGH L' (printed in its panel)
- label: family.13.elder_man.body/18-elder-man-foot-r-front-foot: '18 ELDER_MAN FOOT R FRONT FOOT' -> '11. ELDER_MAN THIGH R' (printed in its panel)
- label: family.13.elder_man.body/elder-man-19-foot-l-profile: 'ELDER_MAN 19. FOOT L PROFILE' -> 'ELDER_MAN SHIN L' (printed in its panel)
- label: family.13.elder_man.body/19-elder-man-foot-r-profile: '19. ELDER_MAN FOOT R PROFILE' -> 'ELDER_MAN SHIN R' (printed in its panel)
- label: family.13.elder_man.body/15-elder-man-garment-overlay-back: '15. ELDER_MAN GARMENT OVERLAY BACK' -> '14. ELDER_MAN GARMENT OVERLAY FRONT' (printed in its panel)
- label: family.13.elder_man.body/e-elder-man-16-foot-front-foot-l-20-elder-man-fo: 'E ELDER_MAN 16. FOOT FRONT FOOT L 20. ELDER_MAN FOOT' -> '15. ELDER_MAN GARMENT OVERLAY BACK' (printed in its panel)
- label: family.13.elder_man.body/20: '20.' -> 'ELDER_MAN FOOT L FRONT' (printed in its panel)
- label: family.13.elder_man.body/elder-man-foot-l-lifted: 'ELDER_MAN FOOT L LIFTED' -> '17. ELDER_MAN FOOT R FRONT' (printed in its panel)
- label: family.13.elder_man.body/21-elder-man-foot: '21. ELDER_MAN FOOT' -> '18. ELDER_MAN FOOT L PROFILE' (printed in its panel)
- label: family.13.elder_man.body/foot-r-lifted: 'FOOT R LIFTED' -> '19. ELDER_MAN FOOT R PROFILE' (printed in its panel)
- label: family.13.elder_man.body/21-elder-man-r-foot-lifted: '21. ELDER_MAN R FOOT LIFTED' -> 'ELDER_MAN FOOT L LIFTED' (printed in its panel)
- label: family.13.elder_man.body/family-13-elder-man-body: 'family.13.elder_man.body' -> 'ELDER_MAN R FOOT LIFTED' (printed in its panel)

### family.13.elder_man.heads-hands
- split: family.13.elder_man.heads-hands/h7-l-pearls-h8-r-grip-pearls-h9-l-grip-rosary-h1 (1516x211) -> 2 parts
- label: family.13.elder_man.heads-hands/part: '' -> 'L GRIP ROSARY (empty)' (was empty/garbled)
- label: family.13.elder_man.heads-hands/r2-kneel-bowed-threequarter-eyes-closed: 'R2 KNEEL BOWED THREEQUARTER (eyes closed)' -> 'H10 GRIP ROSARY (empty)' (closer label (cost 34 vs 76))
- ref: family.13.elder_man.heads-hands/h7-l-pearls-h8-r-grip-pearls-h9-l-grip-rosary-h1: section box: its 2 contents are cut as separate parts
- added: family.13.elder_man.heads-hands/part
- added: family.13.elder_man.heads-hands/r2-kneel-bowed-threequarter-eyes-closed

### family.13.elder_woman.body
- recut: family.13.elder_woman.body/3-elder-woman-torso-profile: framed panel [474, 60, 169, 303] -> figure [486, 68, 144, 291]
- recut: family.13.elder_woman.body/4-elder-woman-hip-bridge: framed panel [657, 61, 180, 301] -> figure [677, 182, 141, 130]
- recut: family.13.elder_woman.body/15-elder-woman-garment-overlay-back: framed panel [1309, 60, 209, 303] -> figure [1320, 73, 185, 283]
- recut: family.13.elder_woman.body/elder-woman-uarm-l: framed panel [22, 420, 147, 278] -> figure [50, 432, 87, 258]
- recut: family.13.elder_woman.body/7-elder-woman-uarm-r: framed panel [186, 420, 147, 278] -> figure [216, 432, 86, 257]
- recut: family.13.elder_woman.body/9-forearm-r: framed panel [514, 420, 148, 278] -> figure [544, 441, 81, 252]
- recut: family.13.elder_woman.body/10-elder-woman-thigh-l: framed panel [677, 420, 178, 278] -> figure [716, 431, 100, 263]
- recut: family.13.elder_woman.body/16-elder-woman-foot-l-front: framed panel [21, 754, 234, 171] -> figure [52, 777, 178, 144]
- recut: family.13.elder_woman.body/17-foot-r-front: framed panel [267, 754, 228, 171] -> figure [291, 777, 176, 144]
- recut: family.13.elder_woman.body/18-elder-woman-foot-l-profile: framed panel [509, 754, 243, 171] -> figure [540, 776, 187, 138]
- recut: family.13.elder_woman.body/19-elder-woman-foot-r-profile: framed panel [774, 754, 238, 171] -> figure [813, 775, 173, 140]
- recut: family.13.elder_woman.body/20-elder-woman-foot-lifted: framed panel [1030, 754, 230, 172] -> figure [1071, 773, 167, 146]
- recut: family.13.elder_woman.body/21-elder-woman-foot-r-lifted: framed panel [1276, 754, 238, 172] -> figure [1302, 773, 167, 145]
- label: family.13.elder_woman.body/elder-woman-uarm-l: 'ELDER_WOMAN UARM L' -> '6. ELDER_WOMAN L' (closer label (cost 18 vs 1000000000); old text is elder-woman-8-forearm-l's)
- label: family.13.elder_woman.body/9-forearm-r: '9. FOREARM R' -> '9. ELDER_WOMAN 10. ELDER_WOMAN THIGH L' (old text not on the sheet; label 30px-cost away)
- label: family.13.elder_woman.body/10-elder-woman-thigh-l: '10. ELDER_WOMAN THIGH L' -> '4. ELDER_WOMAN' (closer label (cost 67 vs 1000000000); old text is elder-woman-11-thigh-r's)
- label: family.13.elder_woman.body/17-foot-r-front: '17. FOOT R FRONT' -> '17. ELDER_WOMAN FOOT FRONT' (re-read, more complete)

### family.13.elder_woman.heads-hands
- unclip: family.13.elder_woman.heads-hands/threequarter-2-head-h2-5-4-cm: +536 px
- unclip: family.13.elder_woman.heads-hands/9-eyes-cm: +580 px
- unclip: family.13.elder_woman.heads-hands/11-closed-2-6-e6-cm: +496 px
- label: family.13.elder_woman.heads-hands/cm: 'cm' -> 'P' (was empty/garbled)
- label: family.13.elder_woman.heads-hands/cm-2: 'cm' -> 'HEAD BACK H5-5.4 cm' (was empty/garbled)
- label: family.13.elder_woman.heads-hands/9-eyes-cm: '9 EYES cm' -> '9 EYES CLOSED' (re-read, more complete)
- label: family.13.elder_woman.heads-hands/10-brows-closed: '10 BROWS CLOSED' -> 'CLOSED ES 2.8 cm' (closer label (cost 9 vs 1000000000); old text is 11-closed-2-6-e6-cm's)
- label: family.13.elder_woman.heads-hands/11-closed-2-6-e6-cm: '11 CLOSED 2.6 E6 cm' -> '11 MOUTH CLOSED' (closer label (cost 6 vs 1000000000); old text is 10-brows-closed's)
- label: family.13.elder_woman.heads-hands/14-l-grip-rosary-empty-h14-3-8-cm: '14 L GRIP ROSARY EMPTY H14 3.8 cm' -> 'FOREARM, WRIST PIVOT ONLY)' (closer label (cost 21 vs 520); old text is l-grip-pearls-empty-h12-3-8-cm's)

### family.14.action
- label: family.14.action/al-laugh-back: 'Al (laugh, back)' -> 'A1 head (laugh, back)' (re-read, more complete)
- label: family.14.action/lean-back-armless: '(lean back, armless)' -> 'A2 torso (lean back, armless)' (re-read, more complete)
- label: family.14.action/b2-hunched-armless: 'B2 (hunched, armless)' -> 'torso (hunched, armless)' (re-read, more complete)
- label: family.14.action/b5-forearm-l: 'B5 forearm L' -> 'L upperarmR_ forearm L forearm' (closer label (cost 45 vs 1000000000); old text is as-forearm-l's)
- label: family.14.action/pelvis-connector-w-h-l-h-r: 'pelvis connector W/H-L/H-R' -> 'pelvis connector W/H-L/H-R (3 holes)' (re-read, more complete)
- label: family.14.action/b11-thigh-l: 'B11 thigh L' -> 'ef 1 thigh L' (closer label (cost 0 vs 1000000000); old text is b12-thigh-r's)
- label: family.14.action/open: '(open)' -> 'A4 upper arm' (closer label (cost 35 vs 131))
- label: family.14.action/open-2: '(open' -> 'forearm L' (closer label (cost 42 vs 1000000000))

### family.street_clothes.body.back
- label: family.street_clothes.body.back/2-arm-l: '2 ARM.L' -> '2 UPPER ARM.L' (re-read, more complete)
- label: family.street_clothes.body.back/3-arm-r: '3 ARM.R' -> 'UPPER ARM.R' (re-read, more complete)

### family.street_clothes.body.front
- label: family.street_clothes.body.front/3-arm-r: '3 ARM.R' -> 'ARM.L UPPER ARM.R' (closer label (cost 14 vs 1000000000); old text is 5-forearm-r's)

### family.street_clothes.body.profile
- label: family.street_clothes.body.profile/6-shin-near: '6 SHIN.near' -> 'THIGH.near 6 SHIN.near' (re-read, more complete)

### family.street_clothes.face-feet
- label: family.street_clothes.face-feet/part-2: '' -> 'HALF' (was empty/garbled)
- label: family.street_clothes.face-feet/part-10: '' -> 'FROWN' (was empty/garbled)
- label: family.street_clothes.face-feet/part-11: '' -> 'WORRY' (was empty/garbled)
- label: family.street_clothes.face-feet/part-12: '' -> 'SOFT' (was empty/garbled)
- label: family.street_clothes.face-feet/part-13: '' -> 'JOY' (was empty/garbled)

### family.street_clothes.hands
- label: family.street_clothes.hands/relaxed-palm: 'relaxed palm' -> 'relaxed back' (closer label (cost 34 vs 69); old text is thumb-back's)
- label: family.street_clothes.hands/open-palm: 'open palm' -> 'open back' (closer label (cost 24 vs 45); old text is peace-back's)
- label: family.street_clothes.hands/fist-palm: 'fist palm' -> 'fist back' (closer label (cost 54 vs 62); old text is wave-back's)
- label: family.street_clothes.hands/grip-palm: 'grip palm' -> 'grip back' (closer label (cost 32 vs 61); old text is claw-back's)
- label: family.street_clothes.hands/pinch-palm: 'pinch palm' -> 'pinch back' (closer label (cost 29 vs 61); old text is cup-back's)
- label: family.street_clothes.hands/point-palm: 'point palm' -> 'point back' (closer label (cost 45 vs 66); old text is flat-push-back's)
- label: family.street_clothes.hands/thumb-back: 'thumb back' -> 'relaxed palm' (closer label (cost 28 vs 65); old text is thumb-palm's)
- label: family.street_clothes.hands/wave-back: 'wave back' -> 'fist palm' (closer label (cost 31 vs 1000000000); old text is peace-palm's)
- label: family.street_clothes.hands/claw-back: 'claw back' -> 'grip palm' (closer label (cost 34 vs 63); old text is claw-palm's)
- label: family.street_clothes.hands/cup-back: 'cup back' -> 'pinch palm' (closer label (cost 27 vs 62); old text is cup-palm's)
- label: family.street_clothes.hands/flat-push-back: 'flat_push back' -> 'point palm' (closer label (cost 40 vs 59))
- label: family.street_clothes.hands/thumb-palm: 'thumb palm' -> 'thumb back' (closer label (cost 22 vs 52); old text is right-hand-set-mirror's)
- label: family.street_clothes.hands/peace-palm: 'peace palm' -> 'peace back' (closer label (cost 29 vs 62); old text is left's)
- label: family.street_clothes.hands/wave-palm: 'wave palm' -> 'back' (closer label (cost 21 vs 1000000000); old text is left's)
- label: family.street_clothes.hands/claw-palm: 'claw palm' -> 'claw back' (closer label (cost 38 vs 58); old text is claw-palm-2's)
- label: family.street_clothes.hands/right-hand-set-mirror: 'RIGHT HAND SET mirror' -> 'thumb palm' (closer label (cost 16 vs 61))
- label: family.street_clothes.hands/left: 'LEFT' -> 'peace palm' (old text not on the sheet; label 34px-cost away)
- label: family.street_clothes.hands/cup: 'cup' -> 'cup palm' (closer label (cost 81 vs 331); old text is cup-palm's)

### family.street_clothes.heads
- label: family.street_clothes.heads/part-1: '' -> 'FRONT' (was empty/garbled)
- label: family.street_clothes.heads/part-2: '' -> 'THREE-QUARTER' (was empty/garbled)
- label: family.street_clothes.heads/part-3: '' -> 'PROFILE' (was empty/garbled)
- label: family.street_clothes.heads/back: 'BACK' -> 'THREE-QUARTER BACK' (closer label (cost 1 vs 1000000000); old text is part-5's)
- label: family.street_clothes.heads/part-5: '' -> 'BACK' (was empty/garbled)
- label: family.street_clothes.heads/part-6: '' -> 'THREE-QUARTER' (was empty/garbled)
- label: family.street_clothes.heads/part-9: '' -> 'BACK' (was empty/garbled)
- ref: family.street_clothes.heads/part-6: label fragment (printed words)
- ref: family.street_clothes.heads/part-7: label fragment (printed words)
- ref: family.street_clothes.heads/back-2: label fragment (printed words)
- ref: family.street_clothes.heads/part-9: label fragment (printed words)

### family.street_clothes.hipcore
- label: family.street_clothes.hipcore/h-r: 'H-R' -> 'H-L' (was empty/garbled)
- label: family.street_clothes.hipcore/seat: 'SEAT' -> 'REA SE' (closer label (cost 21 vs 479))
- label: family.street_clothes.hipcore/thigh-seat: 'THIGH SEAT' -> 'THIGH SEAT TAB L' (closer label (cost 37 vs 1000000000); old text is tab's)
- label: family.street_clothes.hipcore/tab: 'TAB' -> 'THIGH SEAT TAB' (old text not on the sheet; label 29px-cost away)

### ghost_child.02.action.ghost_nightclothes.parts
- split: ghost_child.02.action.ghost_nightclothes.parts/c-hands-and-props-separate-pieces-empty-grip-han (839x503) -> 9 parts
- split: ghost_child.02.action.ghost_nightclothes.parts/c-hands-and-props-separate-pieces-empty-grip-han-2 (820x474) -> 9 parts
- split: ghost_child.02.action.ghost_nightclothes.parts/head-separate-for-reference-separate-prop (653x502) -> 10 parts
- split: ghost_child.02.action.ghost_nightclothes.parts/main-poses-assembled-reference-small-examples-al (1077x231) -> 5 parts
- split: ghost_child.02.action.ghost_nightclothes.parts/foot-l-foot-r (404x231) -> 2 parts
- label: ghost_child.02.action.ghost_nightclothes.parts/vu: 'vu' -> 'lower nightgown panel (reach profile)' (was empty/garbled)
- label: ghost_child.02.action.ghost_nightclothes.parts/lower-panel-profile: 'lower panel (profile)' -> 'lower nightgown panel (profile)' (re-read, more complete)
- label: ghost_child.02.action.ghost_nightclothes.parts/vu-2: 'vu' -> 'hands (grip)' (was empty/garbled)
- label: ghost_child.02.action.ghost_nightclothes.parts/lower-panel-profile-2: 'lower panel (profile)' -> 'lower nightgown panel (profile)' (re-read, more complete)
- ref: ghost_child.02.action.ghost_nightclothes.parts/c-hands-and-props-separate-pieces-empty-grip-han: section box: its 9 contents are cut as separate parts
- ref: ghost_child.02.action.ghost_nightclothes.parts/c-hands-and-props-separate-pieces-empty-grip-han-2: section box: its 9 contents are cut as separate parts
- ref: ghost_child.02.action.ghost_nightclothes.parts/head-separate-for-reference-separate-prop: section box: its 10 contents are cut as separate parts
- ref: ghost_child.02.action.ghost_nightclothes.parts/main-poses-assembled-reference-small-examples-al: section box: its 5 contents are cut as separate parts
- ref: ghost_child.02.action.ghost_nightclothes.parts/foot-l-foot-r: section box: its 2 contents are cut as separate parts
- added: ghost_child.02.action.ghost_nightclothes.parts/vu
- added: ghost_child.02.action.ghost_nightclothes.parts/torso-reach-profile
- added: ghost_child.02.action.ghost_nightclothes.parts/torso-profile
- added: ghost_child.02.action.ghost_nightclothes.parts/pelvis-connector-profile-reach
- added: ghost_child.02.action.ghost_nightclothes.parts/profile
- added: ghost_child.02.action.ghost_nightclothes.parts/lower-panel-profile
- added: ghost_child.02.action.ghost_nightclothes.parts/reach-profile
- added: ghost_child.02.action.ghost_nightclothes.parts/seat-butt-profile
- added: ghost_child.02.action.ghost_nightclothes.parts/seat-butt-profile-reach
- added: ghost_child.02.action.ghost_nightclothes.parts/vu-2
- added: ghost_child.02.action.ghost_nightclothes.parts/torso-reach-profile-2
- added: ghost_child.02.action.ghost_nightclothes.parts/torso-profile-2
- added: ghost_child.02.action.ghost_nightclothes.parts/pelvis-connector-profile-reach-2
- added: ghost_child.02.action.ghost_nightclothes.parts/profile-2
- added: ghost_child.02.action.ghost_nightclothes.parts/lower-panel-profile-2
- added: ghost_child.02.action.ghost_nightclothes.parts/reach-profile-2
- added: ghost_child.02.action.ghost_nightclothes.parts/seat-butt-profile-2
- added: ghost_child.02.action.ghost_nightclothes.parts/seat-butt-profile-reach-2
- added: ghost_child.02.action.ghost_nightclothes.parts/uarm-l
- added: ghost_child.02.action.ghost_nightclothes.parts/uarm-r
- added: ghost_child.02.action.ghost_nightclothes.parts/farm-l
- added: ghost_child.02.action.ghost_nightclothes.parts/farm-r
- added: ghost_child.02.action.ghost_nightclothes.parts/thigh-l
- added: ghost_child.02.action.ghost_nightclothes.parts/thigh-r
- added: ghost_child.02.action.ghost_nightclothes.parts/shin-l
- added: ghost_child.02.action.ghost_nightclothes.parts/shin-r
- added: ghost_child.02.action.ghost_nightclothes.parts/foot-l
- added: ghost_child.02.action.ghost_nightclothes.parts/foot-r
- added: ghost_child.02.action.ghost_nightclothes.parts/tambourine
- added: ghost_child.02.action.ghost_nightclothes.parts/cup-hand-l
- added: ghost_child.02.action.ghost_nightclothes.parts/grip-tambourine-hand-l
- added: ghost_child.02.action.ghost_nightclothes.parts/cup-hand-r
- added: ghost_child.02.action.ghost_nightclothes.parts/grip-tambourine-hand-r
- added: ghost_child.02.action.ghost_nightclothes.parts/head-profile
- added: ghost_child.02.action.ghost_nightclothes.parts/head-front

### ghost_child.02.faces-hands
- label: ghost_child.02.faces-hands/01-head-front: '01. HEAD FRONT' -> '01. BLANK HEAD FRONT' (re-read, more complete)
- label: ghost_child.02.faces-hands/03-head-back: '03. HEAD BACK' -> '03. BLANK HEAD BACK' (re-read, more complete)
- label: ghost_child.02.faces-hands/04-calm: '04. CALM' -> '04. CALM EYE-PAIR' (closer label (cost 11 vs 172); old text is 06's)
- label: ghost_child.02.faces-hands/05-sad: '05. SAD' -> '07. SAD EYE' (re-read, more complete)
- label: ghost_child.02.faces-hands/brow-pair: 'BROW-PAIR' -> '08. NEUTRAL BROW-PAIR' (closer label (cost 3 vs 1000000000); old text is 09-sad's)
- label: ghost_child.02.faces-hands/09-sad: '09. SAD' -> '09. SAD BROW-PAIR' (closer label (cost 10 vs 1000000000); old text is 05-sad's)
- label: ghost_child.02.faces-hands/mouth-front: 'MOUTH FRONT' -> '12. CLOSED MOUTH FRONT' (closer label (cost 9 vs 1000000000); old text is front's)
- label: ghost_child.02.faces-hands/front: 'FRONT' -> '13. SAD MOUTH FRONT' (re-read, more complete)
- label: ghost_child.02.faces-hands/16-open-l: '16. OPEN L' -> '16. OPEN HAND L' (re-read, more complete)
- label: ghost_child.02.faces-hands/tambourine-grip-hand-r: 'TAMBOURINE-GRIP HAND R' -> '19. TAMBOURINE-GRIP HAND R' (re-read, more complete)
- ref: ghost_child.02.faces-hands/ghost: label fragment (printed words)
- ref: ghost_child.02.faces-hands/ads: label fragment (printed words)
- ref: ghost_child.02.faces-hands/ads-features: label fragment (printed words)

### ghost_child.ghost_nightclothes.compact-core
- label: ghost_child.ghost_nightclothes.compact-core/10-forearm-sleeve: '10 FOREARM (SLEEVE)' -> 'FOREARM L 09 UPPERARMR 10 FOREARM (SLEEVE)' (closer label (cost 60 vs 1000000000); old text is 07-upperarm-l-sleeve's)
- ref: ghost_child.ghost_nightclothes.compact-core/ghost-child: label fragment (printed words)

### parents.02.car-argument
- unclip: parents.02.car-argument/part-2: +2016 px
- unclip: parents.02.car-argument/part-3: +963 px
- unclip: parents.02.car-argument/part-5: +2388 px
- label: parents.02.car-argument/part-2: '' -> 'MOTHER PASSENGER' (was empty/garbled)
- label: parents.02.car-argument/part-3: '' -> 'MOTHER PASSENGER' (was empty/garbled)
- label: parents.02.car-argument/father-driver-profile-2: 'FATHER DRIVER (PROFILE)' -> 'DRIVER (FRONT)' (closer label (cost 47 vs 343); old text is father-driver-profile's)
- label: parents.02.car-argument/part-5: '' -> 'MOTHER PASSENGER (PROFILE)' (was empty/garbled)

### parents.02.father_02.body
- label: parents.02.father_02.body/7-father-02: '7 FATHER_02' -> 'UARM' (closer label (cost 53 vs 608))
- label: parents.02.father_02.body/forearm-r: 'FOREARM R' -> '02 FATHER_02 FOREARM' (old text not on the sheet; label 31px-cost away)
- label: parents.02.father_02.body/4-hip-bridge: '4 HIP BRIDGE' -> '4 FATHER_02 HIP' (old text not on the sheet; label 18px-cost away)
- label: parents.02.father_02.body/10-father-02: '10 FATHER_02' -> '10 FATHER_02 THIGH L' (closer label (cost 9 vs 1000000000))
- label: parents.02.father_02.body/12-father-02: '12 FATHER_02' -> '12 FATHER_02 SHIN L' (closer label (cost 11 vs 1000000000))
- label: parents.02.father_02.body/father-02-shin-r: 'FATHER_02 SHIN R' -> '13 FATHER_02 SHIN' (closer label (cost 11 vs 1000000000); old text is 12-father-02's)
- label: parents.02.father_02.body/15-garment-overlay-back: '15 GARMENT OVERLAY BACK' -> '15 FATHER_02 GARMENT OVERLAY BACK' (re-read, more complete)
- label: parents.02.father_02.body/16-foot-l-front: '16 FOOT L FRONT' -> 'FATHER_02 FOOT L FRONT' (re-read, more complete)
- label: parents.02.father_02.body/17-foot-r-front: '17 FOOT R FRONT' -> '17 FATHER_02 FOOT FRONT' (re-read, more complete)
- label: parents.02.father_02.body/18-foot-l-profile: '18 FOOT L PROFILE' -> '18 FATHER_02 FOOT L PROFILE' (re-read, more complete)
- label: parents.02.father_02.body/19-foot-r-profile: '19 FOOT R PROFILE' -> '19 FATHER_02 FOOT PROFILE' (re-read, more complete)
- label: parents.02.father_02.body/21-foot-lifted: '21 FOOT LIFTED' -> 'FATHER_02 FOOT L LIFTED' (re-read, more complete)
- label: parents.02.father_02.body/21-foot-lifted-2: '21 FOOT LIFTED' -> '21 FATHER_02 FOOT LIFTED' (closer label (cost 21 vs 1000000000); old text is 21-foot-lifted's)
- ref: parents.02.father_02.body/5-father-02-butt-rear-seat-2: label fragment (printed words)
- ref: parents.02.father_02.body/foot-r-front: label fragment (printed words)
- ref: parents.02.father_02.body/foot-r-profile: label fragment (printed words)
- ref: parents.02.father_02.body/part-25: label fragment (printed words)

### parents.02.father_02.heads-hands
- split: parents.02.father_02.heads-hands/action-hands-separate-hands-left-and-right-empty (845x388) -> 5 parts
- label: parents.02.father_02.heads-hands/part: '' -> 'THREEQUARTER BACK BACK' (was empty/garbled)
- ref: parents.02.father_02.heads-hands/action-hands-separate-hands-left-and-right-empty: section box: its 5 contents are cut as separate parts
- added: parents.02.father_02.heads-hands/front
- added: parents.02.father_02.heads-hands/threequarter
- added: parents.02.father_02.heads-hands/back
- added: parents.02.father_02.heads-hands/part
- added: parents.02.father_02.heads-hands/profile

### parents.09.father_elder.body
- label: parents.09.father_elder.body/2-torso-back: '2 TORSO_BACK' -> '2 FATHER_ELDER TORSO_BACK' (re-read, more complete)
- label: parents.09.father_elder.body/3-torso-profile: '3 TORSO_PROFILE' -> 'FATHER_ELDER TORSO_PROFILE' (re-read, more complete)
- label: parents.09.father_elder.body/father-elder-garment-overlay-front: 'FATHER_ELDER GARMENT_OVERLAY_FRONT' -> '14 FATHER_ELDER GARMENT_OVERLAY_FRONT' (re-read, more complete)
- label: parents.09.father_elder.body/h-l-h-r-4-father-elder: 'H-L H-R 4 FATHER_ELDER' -> 'H-L 4 FATHER_ELDER HIP_BRIDGE' (re-read, more complete)
- label: parents.09.father_elder.body/5-rear-seat: '5 REAR_SEAT' -> 'FATHER_ELDER REAR_SEAT' (re-read, more complete)
- label: parents.09.father_elder.body/8-uarm-r: '8 UARM_R' -> 'FATHER_ELDER UARM_R' (closer label (cost 15 vs 1000000000); old text is uarm-l's)
- label: parents.09.father_elder.body/shin: 'SHIN_' -> '13 FATHER_ELDER SHIN_R' (closer label (cost 20 vs 1000000000); old text is 11-father-elder-shin-l's)
- label: parents.09.father_elder.body/21-foot-r-lifted: '21 FOOT_R_LIFTED' -> '21 FATHER_ELDER FOOT_R_LIFTED' (re-read, more complete)
- ref: parents.09.father_elder.body/feet: label fragment (printed words)

### parents.09.father_elder.heads-hands
- label: parents.09.father_elder.heads-hands/calm: 'CALM' -> 'FACIAL FEATURES (SEPARATE CARDS)' (closer label (cost 53 vs 257))
- label: parents.09.father_elder.heads-hands/half-lidded: 'HALF-LIDDED' -> 'CALM EYES (PAIR)' (closer label (cost 43 vs 134))
- label: parents.09.father_elder.heads-hands/eyes-pair-no-only: 'EYES (PAIR) (NO ONLY' -> 'HALF-LIDDED EYES (PAIR)' (old text not on the sheet; label 27px-cost away)
- label: parents.09.father_elder.heads-hands/1-open-shoulder-touch: '1 OPEN SHOULDER TOUCH' -> '1 OPEN SHOULDER TOUCH (LEFT)' (re-read, more complete)
- label: parents.09.father_elder.heads-hands/open-shoulder-touch: 'OPEN SHOULDER TOUCH' -> '2 OPEN SHOULDER TOUCH (RIGHT)' (closer label (cost 12 vs 1000000000); old text is 1-open-shoulder-touch's)
- label: parents.09.father_elder.heads-hands/back-left: 'BACK LEFT)' -> 'RELAXED BACK (LEFT)' (re-read, more complete)
- label: parents.09.father_elder.heads-hands/behind-right: 'BEHIND (RIGHT)' -> '4 RELAXED BACK (RIGHT)' (old text not on the sheet; label 12px-cost away)
- label: parents.09.father_elder.heads-hands/5-grip-cane: '5 GRIP CANE' -> 'GRIP CANE (LEFT)' (re-read, more complete)
- ref: parents.09.father_elder.heads-hands/right-5-grip: label fragment (printed words)
- ref: parents.09.father_elder.heads-hands/1-open-shoulder-2-open-shoulder-back-left-behind: under the band heading 'ASSEMBLED REFERENCES'

### parents.09.phone-prayer-walk
- split: parents.09.phone-prayer-walk/part-3 (888x879) -> 3 parts
- recut: parents.09.phone-prayer-walk/2-mother-prayer-mother-prayer: framed panel [6, 83, 329, 881] -> figure [18, 220, 313, 651]
- label: parents.09.phone-prayer-walk/2-mother-prayer-mother-prayer: '2. MOTHER PRAYER MOTHER (PRAYER)' -> '(PHONE LEAN)' (printed in its panel)
- label: parents.09.phone-prayer-walk/3-father-and-walk-east: '3. FATHER AND (WALK EAST)' -> '2. MOTHER PRAYER' (closer label (cost 24 vs 233))
- label: parents.09.phone-prayer-walk/walk-east: '(WALK EAST)' -> 'FATHER_ELDER (WALK EAST)' (closer label (cost 20 vs 1000000000); old text is poet-walk-east's)
- ref: parents.09.phone-prayer-walk/part-3: section box: its 3 contents are cut as separate parts
- added: parents.09.phone-prayer-walk/walk-east
- added: parents.09.phone-prayer-walk/father-elder-poet-steady-shoulder-falter
- added: parents.09.phone-prayer-walk/poet-walk-east

### party.01.vintage-waltz-instances
- label: party.01.vintage-waltz-instances/assembled: 'ASSEMBLED' -> 'WALTZ_PAIR-1 FRONT-THREEQUARTER CLOSED HOLD' (old text not on the sheet; label 24px-cost away)
- label: party.01.vintage-waltz-instances/choreography-reference: 'CHOREOGRAPHY REFERENCE' -> 'WALTZ_PAIR_2 REAR-THREEQUARTER SLOW TURN' (old text not on the sheet; label 39px-cost away)
- label: party.01.vintage-waltz-instances/waltz-pair-3: 'WALTZ_PAIR_3' -> 'WALTZ_PAIR_3 PROFILE GENTLE SIDE-STEP' (re-read, more complete)
- ref: party.01.vintage-waltz-instances/front-threequarter-closed: label fragment (printed words)
- ref: party.01.vintage-waltz-instances/front-threequarter-hold: label fragment (printed words)
- ref: party.01.vintage-waltz-instances/rear-threequarter-slow: label fragment (printed words)
- ref: party.01.vintage-waltz-instances/rear-threequarter-turn: label fragment (printed words)

### party.07.action.party_guest.torso-parts
- label: party.07.action.party_guest.torso-parts/3-o-walk-back: '3 O WALK BACK' -> '3 TORSO WALK BACK' (re-read, more complete)
- label: party.07.action.party_guest.torso-parts/3-4-3-eyelets: '3/4 (3 EYELETS)' -> '1 TORSO COUCH LEAN 3/4' (closer label (cost 46 vs 1000000000))
- label: party.07.action.party_guest.torso-parts/5-hip-bridge-3-4-3-eyelets: '5 HIP BRIDGE 3/4 (3 EYELETS)' -> 'HIP BRIDGE ARMS-UP STAND 3/4 (3 EYELETS)' (closer label (cost 3 vs 317))
- label: party.07.action.party_guest.torso-parts/6-3-eyelets: '6 (3 EYELETS)' -> '6 HIP BRIDGE WALK BACK (3 EYELETS)' (old text not on the sheet; label 10px-cost away)
- label: party.07.action.party_guest.torso-parts/7-rear-seat-lean-3-4-1-eyelet: '7 REAR SEAT LEAN 3/4 (1 EYELET)' -> '7 REAR SEAT COUCH LEAN 3/4 (1 EYELET)' (re-read, more complete)
- label: party.07.action.party_guest.torso-parts/8-rear-3-4-1-eyelet: '8 REAR 3/4 (1 EYELET)' -> '8 REAR SEAT ARMS-UP STAND 3/4 (1 EYELET)' (closer label (cost 12 vs 1000000000); old text is 7-rear-seat-lean-3-4-1-eyelet's)

### party.07.dj-guest.action-hands
- label: party.07.dj-guest.action-hands/pinch-l: 'PINCH L' -> 'OPEN L' (closer label (cost 20 vs 51); old text is open-l's)
- label: party.07.dj-guest.action-hands/pinch-r: 'PINCH R' -> 'OPEN R' (closer label (cost 29 vs 1000000000); old text is open-l's)
- label: party.07.dj-guest.action-hands/cup-grip-l: 'CUP GRIP L' -> 'RELAX L' (closer label (cost 46 vs 60); old text is relax-l's)
- label: party.07.dj-guest.action-hands/point-l: 'POINT L' -> 'FLAT PUSH L' (closer label (cost 33 vs 52); old text is flat-push-l's)
- label: party.07.dj-guest.action-hands/point-r: 'POINT R' -> 'FLAT PUSH' (closer label (cost 41 vs 1000000000); old text is flat-push-l's)
- label: party.07.dj-guest.action-hands/relax-l: 'RELAX L' -> 'CUP GRIP L' (closer label (cost 26 vs 270); old text is cup-grip-l's)
- label: party.07.dj-guest.action-hands/open-l: 'OPEN L' -> 'PINCH L' (closer label (cost 23 vs 267); old text is pinch-l's)
- label: party.07.dj-guest.action-hands/flat-push-l: 'FLAT PUSH L' -> 'POINT L' (closer label (cost 33 vs 271); old text is point-l's)
- label: party.07.dj-guest.action-hands/flat-push-r: 'FLAT PUSH R' -> 'POINT' (closer label (cost 47 vs 1000000000); old text is point-l's)
- label: party.07.dj-guest.action-hands/cup-grip-l-2: 'CUP GRIP L' -> 'RELAX L' (closer label (cost 48 vs 276); old text is relax-l's)
- label: party.07.dj-guest.action-hands/grip-r: 'GRIP R' -> 'RELAX' (closer label (cost 39 vs 1000000000); old text is relax-l's)
- label: party.07.dj-guest.action-hands/pinch-l-2: 'PINCH L' -> 'OPEN L' (closer label (cost 19 vs 237); old text is open-l's)
- label: party.07.dj-guest.action-hands/pinch-r-2: 'PINCH R' -> 'OPEN' (closer label (cost 26 vs 1000000000); old text is open-l's)
- label: party.07.dj-guest.action-hands/point-l-2: 'POINT L' -> 'FLAT PUSH L' (closer label (cost 38 vs 275); old text is flat-push-l's)
- label: party.07.dj-guest.action-hands/point-r-2: 'POINT R' -> 'FLAT PUSH' (closer label (cost 42 vs 1000000000); old text is flat-push-l's)
- label: party.07.dj-guest.action-hands/party-07-dj-guest-action-hands: 'party.07.dj-guest.action-hands' -> 'PINCH L' (old text not on the sheet; label 22px-cost away)
- label: party.07.dj-guest.action-hands/all-props-supplied-separately: 'all props supplied separately' -> 'PINCH' (old text not on the sheet; label 14px-cost away)

### party.07.party_guest.main-poses
- unclip: party.07.party_guest.main-poses/01-couch-lean-hand-to-chest: +177 px
- label: party.07.party_guest.main-poses/part-7: '' -> '04 LIGHTER UP' (was empty/garbled)

### party.14.action.vintage_party.gown_woman.parts.01
- label: party.14.action.vintage_party.gown_woman.parts.01/threequarter: '(THREEQUARTER)' -> '3 REAR SEAT COVER' (closer label (cost 71 vs 1000000000); old text is thigh-l's)
- label: party.14.action.vintage_party.gown_woman.parts.01/forearm: 'FOREARM' -> '3 FOREARM L' (closer label (cost 13 vs 1000000000); old text is forearm-2's)
- label: party.14.action.vintage_party.gown_woman.parts.01/thigh-r: 'THIGH R' -> '6 THIGH' (closer label (cost 15 vs 1000000000); old text is 3-coupe-l's)
- label: party.14.action.vintage_party.gown_woman.parts.01/4-hand-r: '4 HAND R' -> '7 SHIN L' (closer label (cost 64 vs 1000000000); old text is 1-open-hand-l-complete-assemblies's)
- label: party.14.action.vintage_party.gown_woman.parts.01/champagne: 'CHAMPAGNE' -> '5 CHAMPAGNE COUPE' (re-read, more complete)
- label: party.14.action.vintage_party.gown_woman.parts.01/dance-profile: 'DANCE PROFILE' -> '4 COUPE HAND' (closer label (cost 72 vs 1000000000))

### party.14.action.vintage_party.gown_woman.parts.02
- label: party.14.action.vintage_party.gown_woman.parts.02/upper-arm-r: 'UPPER ARM R' -> '6 UPPER ARM' (closer label (cost 16 vs 1000000000); old text is upper-arm-l's)
- label: party.14.action.vintage_party.gown_woman.parts.02/thigh-r: 'THIGH R' -> '10 THIGH' (closer label (cost 13 vs 1000000000); old text is thigh-l's)
- label: party.14.action.vintage_party.gown_woman.parts.02/shin-l: 'SHIN L' -> '11 SHIN L' (re-read, more complete)
- label: party.14.action.vintage_party.gown_woman.parts.02/shin-r: 'SHIN R' -> '12 SHIN R' (re-read, more complete)

### party.14.action.vintage_party.suit_man.parts
- split: party.14.action.vintage_party.suit_man.parts/tail-r (1046x237) -> 12 parts
- split: party.14.action.vintage_party.suit_man.parts/pelvis-connector-pelvis-connector-pelvis-connect (1506x488) -> 20 parts
- label: party.14.action.vintage_party.suit_man.parts/farm-l: 'farm.L' -> 'uarm.L' (closer label (cost 14 vs 231); old text is farm-l-3's)
- label: party.14.action.vintage_party.suit_man.parts/farm-l-2: 'farm.L' -> 'uarm.R' (closer label (cost 15 vs 108); old text is farm-l-3's)
- label: party.14.action.vintage_party.suit_man.parts/tail-l: 'tail.L' -> 'shin.R' (closer label (cost 18 vs 1000000000); old text is thigh-l's)
- label: party.14.action.vintage_party.suit_man.parts/tail-l-2: 'tail.L' -> 'foot.L' (closer label (cost 28 vs 1000000000); old text is thigh-l's)
- label: party.14.action.vintage_party.suit_man.parts/tail-r-2: 'tail.R' -> 'foot.R' (closer label (cost 28 vs 52); old text is foot-r's)
- label: party.14.action.vintage_party.suit_man.parts/jacket: 'JACKET' -> 'uarm.L' (closer label (cost 14 vs 1000000000); old text is foot-r's)
- label: party.14.action.vintage_party.suit_man.parts/farm-l-4: 'farm.L' -> 'uarm.R' (closer label (cost 15 vs 108); old text is farm-l-3's)
- label: party.14.action.vintage_party.suit_man.parts/single: '(single' -> 'seat threequarter' (closer label (cost 119 vs 1000000000); old text is shin-l's)
- label: party.14.action.vintage_party.suit_man.parts/farm-l-5: 'farm.L' -> 'uarm.L' (closer label (cost 14 vs 231); old text is farm-l-3's)
- label: party.14.action.vintage_party.suit_man.parts/farm-l-6: 'farm.L' -> 'uarm.R' (closer label (cost 15 vs 108); old text is farm-l-3's)
- label: party.14.action.vintage_party.suit_man.parts/tail-l-3: 'tail.L' -> 'shin.R' (closer label (cost 18 vs 1000000000); old text is thigh-l's)
- label: party.14.action.vintage_party.suit_man.parts/single-2: '(single' -> 'farm.L' (closer label (cost 20 vs 1000000000); old text is shin-l's)
- label: party.14.action.vintage_party.suit_man.parts/tail-l-4: 'tail.L' -> 'foot.L' (closer label (cost 28 vs 1000000000); old text is thigh-l's)
- label: party.14.action.vintage_party.suit_man.parts/tail-r-3: 'tail.R' -> 'foot.R' (closer label (cost 28 vs 52); old text is foot-r's)
- label: party.14.action.vintage_party.suit_man.parts/examples-detached-head-separate-piece-dance: 'examples detached head (separate piece) dance' -> 'dance threequarter' (closer label (cost 62 vs 109); old text is detached-head-separate's)
- label: party.14.action.vintage_party.suit_man.parts/champagne-coupe: 'champagne_coupe' -> 'dance profile' (closer label (cost 98 vs 237); old text is champagne-coupe-2's)
- label: party.14.action.vintage_party.suit_man.parts/tail-r-4: 'tail.R' -> 'dance' (closer label (cost 30 vs 113); old text is foot-r's)
- label: party.14.action.vintage_party.suit_man.parts/detached-head-separate: 'detached head (separate' -> 'detached head (separate piece)' (re-read, more complete)
- label: party.14.action.vintage_party.suit_man.parts/part-2: '' -> 'prop (separate)' (was empty/garbled)
- label: party.14.action.vintage_party.suit_man.parts/champagne-coupe-3: 'champagne_coupe' -> 'open' (closer label (cost 13 vs 313); old text is champagne-coupe-2's)
- label: party.14.action.vintage_party.suit_man.parts/champagne-coupe-4: 'champagne_coupe' -> 'pinch (champagne_coupe)' (closer label (cost 20 vs 126); old text is champagne-coupe-2's)
- ref: party.14.action.vintage_party.suit_man.parts/tail-r: section box: its 12 contents are cut as separate parts
- ref: party.14.action.vintage_party.suit_man.parts/pelvis-connector-pelvis-connector-pelvis-connect: section box: its 20 contents are cut as separate parts
- ref: party.14.action.vintage_party.suit_man.parts/tail-l-tail-r-examples: label says 'examples'
- added: party.14.action.vintage_party.suit_man.parts/uarm-l-uarm-r-thigh-l-thigh-r-farm-l-farm-r-shin
- added: party.14.action.vintage_party.suit_man.parts/thigh-l-2
- added: party.14.action.vintage_party.suit_man.parts/attached-thigh-r
- added: party.14.action.vintage_party.suit_man.parts/jacket
- added: party.14.action.vintage_party.suit_man.parts/farm-l-4
- added: party.14.action.vintage_party.suit_man.parts/shin-l-2
- added: party.14.action.vintage_party.suit_man.parts/shin-r
- added: party.14.action.vintage_party.suit_man.parts/single
- added: party.14.action.vintage_party.suit_man.parts/farm-r-2
- added: party.14.action.vintage_party.suit_man.parts/foot-l
- added: party.14.action.vintage_party.suit_man.parts/foot-r
- added: party.14.action.vintage_party.suit_man.parts/part
- added: party.14.action.vintage_party.suit_man.parts/tail-l-tail-r-examples
- added: party.14.action.vintage_party.suit_man.parts/thigh-l-3
- added: party.14.action.vintage_party.suit_man.parts/attached-thigh-r-2
- added: party.14.action.vintage_party.suit_man.parts/farm-l-5
- added: party.14.action.vintage_party.suit_man.parts/farm-l-6
- added: party.14.action.vintage_party.suit_man.parts/shin-l-3
- added: party.14.action.vintage_party.suit_man.parts/tail-l-3
- added: party.14.action.vintage_party.suit_man.parts/single-2
- added: party.14.action.vintage_party.suit_man.parts/farm-r-3
- added: party.14.action.vintage_party.suit_man.parts/tail-l-4
- added: party.14.action.vintage_party.suit_man.parts/tail-r-3
- added: party.14.action.vintage_party.suit_man.parts/examples-detached-head-separate-piece-dance
- added: party.14.action.vintage_party.suit_man.parts/champagne-coupe
- added: party.14.action.vintage_party.suit_man.parts/tail-r-4
- added: party.14.action.vintage_party.suit_man.parts/dance-threequarter-back
- added: party.14.action.vintage_party.suit_man.parts/detached-head-separate
- added: party.14.action.vintage_party.suit_man.parts/part-2
- added: party.14.action.vintage_party.suit_man.parts/champagne-coupe-2
- added: party.14.action.vintage_party.suit_man.parts/champagne-coupe-3
- added: party.14.action.vintage_party.suit_man.parts/champagne-coupe-4

### party.dj_cyber.body.profile
- label: party.dj_cyber.body.profile/part-3: '' -> 'FOREARM' (was empty/garbled)

### party.dj_cyber.compact-core
- label: party.dj_cyber.compact-core/torso: 'TORSO' -> '01 TORSO FRONT' (closer label (cost 5 vs 1000000000); old text is 02-bac's)
- label: party.dj_cyber.compact-core/02-bac: '02 BAC' -> '02 TORSO BACK' (re-read, more complete)
- label: party.dj_cyber.compact-core/07-arm: '07 ARM' -> '07 UPPER' (old text not on the sheet; label 16px-cost away)

### party.dj_cyber.face-feet
- label: party.dj_cyber.face-feet/8-pairs: '(8 PAIRS)' -> 'open' (closer label (cost 9 vs 57); old text is closed's)
- label: party.dj_cyber.face-feet/wide: 'wide' -> 'half' (closer label (cost 29 vs 142); old text is wide-2's)
- label: party.dj_cyber.face-feet/frown: 'frown' -> 'smile' (closer label (cost 20 vs 1000000000); old text is front-2's)
- label: party.dj_cyber.face-feet/feet-6-detached: 'FEET (6) DETACHED' -> 'rest' (old text not on the sheet; label 22px-cost away)
- label: party.dj_cyber.face-feet/part-22: '' -> 'smile' (was empty/garbled)
- label: party.dj_cyber.face-feet/f-v: 'F-V' -> 'M-B-P' (was empty/garbled)
- label: party.dj_cyber.face-feet/part-26: '' -> 'TH' (was empty/garbled)
- label: party.dj_cyber.face-feet/front: 'front' -> 'FEET (6)' (closer label (cost 9 vs 23); old text is front-2's)
- label: party.dj_cyber.face-feet/left: 'left' -> 'profile left' (old text not on the sheet; label 2px-cost away)

### party.party_guest.body.profile
- label: party.party_guest.body.profile/18-rear-butt: '18 rear butt' -> '18 rear seat butt' (re-read, more complete)
- ref: party.party_guest.body.profile/12-2: label fragment (printed words)

### party.party_guest.compact-core
- label: party.party_guest.compact-core/05-upper-arm-l: '05 UPPER ARM L' -> 'UPPER ARM L 06 FOREARM L' (closer label (cost 38 vs 1000000000); old text is 07-upper-armr's)
- label: party.party_guest.compact-core/06-forearm-l: '06 FOREARM L' -> 'UPPER ARM L 06 FOREARM L' (re-read, more complete)
- label: party.party_guest.compact-core/10-l: '10 L' -> '10 SHIN L' (was empty/garbled)

### party.party_guest.face-feet
- label: party.party_guest.face-feet/part-18: '' -> 'A' (was empty/garbled)
- label: party.party_guest.face-feet/part-21: '' -> '0' (was empty/garbled)
- label: party.party_guest.face-feet/part-22: '' -> 'U' (was empty/garbled)

### party.vintage_party.body.back
- label: party.vintage_party.body.back/back: '(back)' -> '4uarm.L' (old text not on the sheet; label 11px-cost away)
- label: party.vintage_party.body.back/5-uarm-r: '5 uarm.R' -> 'uarm.R 7' (closer label (cost 12 vs 468); old text is 5-uarm-r-2's)
- label: party.vintage_party.body.back/2-torso-2: '2 torso' -> 'FEMALE body cards (back)' (closer label (cost 29 vs 132); old text is 2-torso's)

### party.vintage_party.body.front
- label: party.vintage_party.body.front/thigh-l-10: 'thigh.L 10' -> 'seat butt' (closer label (cost 28 vs 213); old text is 10-thigh-l's)
- label: party.vintage_party.body.front/back-seat: '(back) seat' -> 'pelvis (front)' (old text not on the sheet; label 1px-cost away)
- label: party.vintage_party.body.front/separate: 'separate' -> 'seat butt (back)' (closer label (cost 21 vs 62))

### party.vintage_party.body.profile
- label: party.vintage_party.body.profile/female: 'FEMALE' -> '1 TORSO' (closer label (cost 22 vs 31); old text is torso's)
- label: party.vintage_party.body.profile/part-7: '' -> '4 HAND' (was empty/garbled)
- label: party.vintage_party.body.profile/connector: 'CONNECTOR' -> 'PELVIS CONNECTOR' (re-read, more complete)
- label: party.vintage_party.body.profile/part-9: '' -> '7 FOOT' (was empty/garbled)
- label: party.vintage_party.body.profile/torso: 'TORSO' -> 'FEMALE 1 TORSO' (closer label (cost 27 vs 552); old text is female's)
- label: party.vintage_party.body.profile/part-16: '' -> '4' (was empty/garbled)
- label: party.vintage_party.body.profile/part-17: '' -> 'PELVIS CONNECTOR' (was empty/garbled)

### party.vintage_party.face-feet.female
- label: party.vintage_party.face-feet.female/part-23: '' -> 'back' (was empty/garbled)
- label: party.vintage_party.face-feet.female/profi: 'profi' -> 'profile left' (re-read, more complete)

### party.vintage_party.face-feet.male
- label: party.vintage_party.face-feet.male/half-closed: 'half closed' -> 'open' (old text not on the sheet; label 8px-cost away)
- label: party.vintage_party.face-feet.male/look: 'look' -> 'look right' (closer label (cost 4 vs 112); old text is look-2's)
- ref: party.vintage_party.face-feet.male/vintage: label fragment (printed words)

### party.vintage_party.hands
- label: party.vintage_party.hands/relaxed-palm: 'relaxed palm' -> 'relaxed back' (closer label (cost 33 vs 49); old text is relaxed-palm-2's)
- label: party.vintage_party.hands/open-palm: 'open palm' -> 'open back' (closer label (cost 16 vs 33); old text is hand-ivory-gown's)
- label: party.vintage_party.hands/fist-palm: 'fist palm' -> 'fist back' (closer label (cost 22 vs 46); old text is gloves's)
- label: party.vintage_party.hands/grip-palm: 'grip palm' -> 'grip back' (closer label (cost 21 vs 57); old text is grip-palm-2's)
- label: party.vintage_party.hands/pinch-palm: 'pinch palm' -> 'pinch back' (closer label (cost 22 vs 52); old text is pinch-palm-2's)
- label: party.vintage_party.hands/point-palm: 'point palm' -> 'point back' (closer label (cost 38 vs 55); old text is point-palm-2's)
- label: party.vintage_party.hands/hand-ivory-gown: 'HAND (IVORY GOWN' -> 'open palm' (old text not on the sheet; label 12px-cost away)
- label: party.vintage_party.hands/gloves: 'GLOVES)' -> 'fist palm' (old text not on the sheet; label 25px-cost away)
- label: party.vintage_party.hands/relaxed-palm-3: 'relaxed palm' -> 'relaxed back' (closer label (cost 32 vs 319); old text is relaxed-palm-2's)
- label: party.vintage_party.hands/open-palm-2: 'open palm' -> 'open back' (closer label (cost 24 vs 285); old text is hand-ivory-gown's)
- label: party.vintage_party.hands/fist-palm-2: 'fist palm' -> 'fist back' (closer label (cost 25 vs 315); old text is gloves's)
- label: party.vintage_party.hands/grip-palm-3: 'grip palm' -> 'grip pack:' (closer label (cost 8 vs 312); old text is grip-palm-2's)
- label: party.vintage_party.hands/pinch-palm-3: 'pinch palm' -> 'pinch back' (closer label (cost 27 vs 317); old text is pinch-palm-2's)
- label: party.vintage_party.hands/point-palm-3: 'point palm' -> 'point back' (closer label (cost 39 vs 330); old text is point-palm-2's)

### party.vintage_party.heads
- label: party.vintage_party.heads/blank: 'blank' -> 'threequarter' (closer label (cost 7 vs 1000000000); old text is back's)
- label: party.vintage_party.heads/profile-head-plates-with-neck-tabs-five: 'profile head plates with neck tabs five' -> 'profile blank head plates with neck tabs five views' (re-read, more complete)
- label: party.vintage_party.heads/profile-2: 'profile' -> 'threequarter' (old text not on the sheet; label 20px-cost away)
- ref: party.vintage_party.heads/profile-2: label fragment (printed words)

### party.vintage_party.master
- label: party.vintage_party.master/head-back: 'head back' -> 'head back blank head' (closer label (cost 18 vs 740))
- label: party.vintage_party.master/expressions-head-interchangeable-closed-looking-: 'EXPRESSIONS HEAD (INTERCHANGEABLE) closed looking eyes open eyes head brows normal brows raised mouth mouth mouth mouth open HANDS (6 TYPES) 5 relaxed elegant point thigh.R hold grip open (for partner) shin.R PROP foot.R champagne_coupe' -> 'skirt lower' (old text not on the sheet; label 33px-cost away)
- label: party.vintage_party.master/eyes-open: 'eyes open' -> 'brows normal' (closer label (cost 70 vs 1000000000))
- label: party.vintage_party.master/eyes-closed: 'eyes closed' -> '(INTERCHANGEABLE)' (closer label (cost 27 vs 1000000000))
- label: party.vintage_party.master/mouth-hands: 'mouth HANDS' -> 'front' (old text not on the sheet; label 34px-cost away)
- label: party.vintage_party.master/hand-l: 'hand.L' -> 'hand.R' (closer label (cost 17 vs 1000000000))
- label: party.vintage_party.master/mouth-mouth: 'mouth mouth' -> 'open' (closer label (cost 43 vs 1000000000); old text is mouth-mouth-mouth-open's)
- label: party.vintage_party.master/mouth-mouth-open: 'mouth mouth open' -> 'frown' (closer label (cost 26 vs 1000000000); old text is mouth-mouth-mouth-open's)
- label: party.vintage_party.master/farm-r: 'farm.R' -> 'head' (closer label (cost 36 vs 50))
- label: party.vintage_party.master/farm-r-2: 'farm.R' -> 'back' (closer label (cost 30 vs 133))
- label: party.vintage_party.master/mouth-mouth-mouth-mouth-open-hands-6-types: 'mouth mouth mouth mouth open HANDS (6 TYPES)' -> 'neutral' (closer label (cost 56 vs 794); old text is hand-r's)
- label: party.vintage_party.master/mouth: 'mouth' -> 'frown' (old text not on the sheet; label 19px-cost away)
- label: party.vintage_party.master/relaxed-2: 'relaxed' -> 'HANDS (6 TYPES)' (closer label (cost 29 vs 1000000000); old text is relaxed's)
- label: party.vintage_party.master/elegant: 'elegant' -> 'relaxed elegant point' (re-read, more complete)
- label: party.vintage_party.master/relaxed-point-466-fist-open-prop: 'relaxed point 466 fist open PROP' -> 'farm.L' (old text not on the sheet; label 28px-cost away)
- label: party.vintage_party.master/open: 'open' -> 'PROP' (closer label (cost 53 vs 1000000000))
- label: party.vintage_party.master/shin-r: 'shin.R' -> 'thigh.R' (closer label (cost 18 vs 1000000000))

### party.vintage_party.paired-choreography
- label: party.vintage_party.paired-choreography/party-vintage-party: 'party.vintage_party.' -> 'edt ou' (old text not on the sheet; label 39px-cost away)
- label: party.vintage_party.paired-choreography/open-a-gap: 'OPEN A GAP' -> 'REAR PAIR OPEN A GAP' (re-read, more complete)
- label: party.vintage_party.paired-choreography/separate-prop: 'SEPARATE PROP' -> 'COUPE SEPARATE PROP' (re-read, more complete)
- label: party.vintage_party.paired-choreography/separate: 'SEPARATE' -> 'COUPE SEPARATE PROP' (re-read, more complete)

### poet.01.action.black_tshirt.parts.01
- split: poet.01.action.black_tshirt.parts.01/d-main-poses-assembled-reference-small-for-guide (711x640) -> 8 parts
- split: poet.01.action.black_tshirt.parts.01/threequarter (479x640) -> 10 parts
- split: poet.01.action.black_tshirt.parts.01/face-reference-blank-heads-use-core (315x640) -> 7 parts
- label: poet.01.action.black_tshirt.parts.01/farm-l-elbow-wrist-to: 'farm.L (elbow wrist) to' -> 'farm.L (shoulder to elbow) (shoulder to elbow) (elbow to wrist) (elbow to wrist)' (old text not on the sheet; label 32px-cost away)
- label: poet.01.action.black_tshirt.parts.01/claw: 'claw' -> 'pen' (closer label (cost 15 vs 28); old text is poem-page-drawer's)
- label: poet.01.action.black_tshirt.parts.01/claw-2: 'claw' -> 'flat_push' (closer label (cost 19 vs 44); old text is poem-page-drawer's)
- label: poet.01.action.black_tshirt.parts.01/poem-page-drawer: 'poem_page drawer' -> 'claw' (closer label (cost 28 vs 391); old text is pen's)
- ref: poet.01.action.black_tshirt.parts.01/d-main-poses-assembled-reference-small-for-guide: section box: its 8 contents are cut as separate parts
- ref: poet.01.action.black_tshirt.parts.01/threequarter: section box: its 10 contents are cut as separate parts
- ref: poet.01.action.black_tshirt.parts.01/face-reference-blank-heads-use-core: section box: its 7 contents are cut as separate parts
- added: poet.01.action.black_tshirt.parts.01/torso-reach-front
- added: poet.01.action.black_tshirt.parts.01/torso-fall-threequarter
- added: poet.01.action.black_tshirt.parts.01/torso-threequarter-crouch
- added: poet.01.action.black_tshirt.parts.01/pelvis-connector-ffall-threequarter
- added: poet.01.action.black_tshirt.parts.01/pelvis-connector-fall-threequarter
- added: poet.01.action.black_tshirt.parts.01/seat-crouch-threequarter
- added: poet.01.action.black_tshirt.parts.01/seat-reach-front
- added: poet.01.action.black_tshirt.parts.01/seat-fall-threequarter
- added: poet.01.action.black_tshirt.parts.01/farm-r-elbow-wrist-to
- added: poet.01.action.black_tshirt.parts.01/uarm-r-shoulder-to
- added: poet.01.action.black_tshirt.parts.01/uarm-l-shoulder-to-elbow
- added: poet.01.action.black_tshirt.parts.01/farm-l-elbow-wrist-to
- added: poet.01.action.black_tshirt.parts.01/thigh-r-hip-to-knee
- added: poet.01.action.black_tshirt.parts.01/thigh-l-hip-to-knee
- added: poet.01.action.black_tshirt.parts.01/shin-l-knee-to-ankle
- added: poet.01.action.black_tshirt.parts.01/shin-r-knee-to-ankle
- added: poet.01.action.black_tshirt.parts.01/foot-l
- added: poet.01.action.black_tshirt.parts.01/foot-r
- added: poet.01.action.black_tshirt.parts.01/pen
- added: poet.01.action.black_tshirt.parts.01/flat-push
- added: poet.01.action.black_tshirt.parts.01/claw
- added: poet.01.action.black_tshirt.parts.01/claw-2
- added: poet.01.action.black_tshirt.parts.01/poem-page-drawer
- added: poet.01.action.black_tshirt.parts.01/poem-page
- added: poet.01.action.black_tshirt.parts.01/drawer

### poet.01.action.black_tshirt.parts.02
- label: poet.01.action.black_tshirt.parts.02/fall: 'fall' -> 'legless' (closer label (cost 40 vs 1000000000); old text is farm-l's)
- label: poet.01.action.black_tshirt.parts.02/seat: 'seat' -> 'seat (run/standing)' (closer label (cost 7 vs 1000000000))
- label: poet.01.action.black_tshirt.parts.02/part-24: '' -> 'poem_page' (was empty/garbled)

### poet.01.main-poses
- unclip: poet.01.main-poses/search-drawer-hall: +264 px
- label: poet.01.main-poses/fall-reach-back: 'FALL REACH BACK' -> 'FALL HEAD-DOWN REACH BACK' (re-read, more complete)

### poet.02.action.black_tshirt.parts
- split: poet.02.action.black_tshirt.parts/d-main-poses-assembled-reference-for-placement-o (1523x684) -> 28 parts
- label: poet.02.action.black_tshirt.parts/part: '' -> 'hidden' (was empty/garbled)
- ref: poet.02.action.black_tshirt.parts/d-main-poses-assembled-reference-for-placement-o: section box: its 28 contents are cut as separate parts
- added: poet.02.action.black_tshirt.parts/part
- added: poet.02.action.black_tshirt.parts/torso-hips-for-each
- added: poet.02.action.black_tshirt.parts/pieces-no-arms-no
- added: poet.02.action.black_tshirt.parts/part-2
- added: poet.02.action.black_tshirt.parts/uarm-l
- added: poet.02.action.black_tshirt.parts/uarm-r
- added: poet.02.action.black_tshirt.parts/farm-l
- added: poet.02.action.black_tshirt.parts/farm-r
- added: poet.02.action.black_tshirt.parts/torso-threequarter
- added: poet.02.action.black_tshirt.parts/torso-front
- added: poet.02.action.black_tshirt.parts/torso-profile
- added: poet.02.action.black_tshirt.parts/thigh-l
- added: poet.02.action.black_tshirt.parts/thigh-r
- added: poet.02.action.black_tshirt.parts/shin-r
- added: poet.02.action.black_tshirt.parts/shin-l
- added: poet.02.action.black_tshirt.parts/pelvis-connector
- added: poet.02.action.black_tshirt.parts/pelvis-connector-2
- added: poet.02.action.black_tshirt.parts/pelvis-connector-3
- added: poet.02.action.black_tshirt.parts/seat-threequarter
- added: poet.02.action.black_tshirt.parts/seat-front
- added: poet.02.action.black_tshirt.parts/seat-profile
- added: poet.02.action.black_tshirt.parts/foot-l
- added: poet.02.action.black_tshirt.parts/foot-r
- added: poet.02.action.black_tshirt.parts/mirror
- added: poet.02.action.black_tshirt.parts/flat-push-mirror
- added: poet.02.action.black_tshirt.parts/open
- added: poet.02.action.black_tshirt.parts/claw
- added: poet.02.action.black_tshirt.parts/fist

### poet.02.main-poses
- label: poet.02.main-poses/sit-up-awake: 'SIT UP AWAKE' -> 'SHEET' (closer label (cost 33 vs 192))

### poet.03.main-poses
- split: poet.03.main-poses/poet-turns-back-ex-keeps-going (358x921) -> 3 parts
- unclip: poet.03.main-poses/poet-follows-the: +62 px
- ref: poet.03.main-poses/poet-turns-back-ex-keeps-going: section box: its 3 contents are cut as separate parts
- added: poet.03.main-poses/part
- added: poet.03.main-poses/part-2
- added: poet.03.main-poses/part-3

### poet.04.action.red_black_sunglasses.parts.01
- split: poet.04.action.red_black_sunglasses.parts.01/c-hands-and-props-open-l-open-r-sunglasses-separ (930x465) -> 9 parts
- split: poet.04.action.red_black_sunglasses.parts.01/expression-reference-separate-blank-head-use-cor (588x616) -> 9 parts
- split: poet.04.action.red_black_sunglasses.parts.01/d-face-reference-main-poses-on-companion-sheet (930x168) -> 3 parts
- label: poet.04.action.red_black_sunglasses.parts.01/pelvis-connector-seat-kneel: 'pelvis connector seat (kneel)' -> 'TORSO HIPS FOR EACH POSE kneel threequarter torso (kneel threequarter)' (closer label (cost 22 vs 1000000000); old text is pelvis-connector-2's)
- label: poet.04.action.red_black_sunglasses.parts.01/connector-seat: 'connector seat' -> 'kneel profile torso (kneel profile)' (closer label (cost 20 vs 1000000000); old text is pelvis-connector-2's)
- label: poet.04.action.red_black_sunglasses.parts.01/pelvis-seat-crouch-se-connector: 'pelvis seat (crouch) Se connector' -> 'crouch threequarter torso (crouch threequarter)' (closer label (cost 14 vs 48); old text is pelvis-connector-2's)
- label: poet.04.action.red_black_sunglasses.parts.01/se: 'Se' -> 'seat (kneel)' (was empty/garbled)
- label: poet.04.action.red_black_sunglasses.parts.01/se-2: 'Se' -> 'pelvis connector' (was empty/garbled)
- label: poet.04.action.red_black_sunglasses.parts.01/thigh-r-shin-l: 'thigh.R shin.L' -> 'uarm.R' (closer label (cost 23 vs 1000000000); old text is thigh-l-2's)
- label: poet.04.action.red_black_sunglasses.parts.01/shin-r: 'shin.R' -> 'farm.L' (closer label (cost 20 vs 50); old text is foot-l-foot-r's)
- label: poet.04.action.red_black_sunglasses.parts.01/foot-l: 'foot.L' -> 'thigh.R' (closer label (cost 14 vs 344))
- label: poet.04.action.red_black_sunglasses.parts.01/foot-l-2: 'foot.L' -> 'shin.L' (closer label (cost 19 vs 210))
- label: poet.04.action.red_black_sunglasses.parts.01/foot-l-foot-r: 'foot.L foot.R' -> 'shin.R' (closer label (cost 20 vs 83))
- label: poet.04.action.red_black_sunglasses.parts.01/sunglasses-separate: 'sunglasses (separate' -> 'open.R' (closer label (cost 10 vs 175); old text is hidden-earlier's)
- label: poet.04.action.red_black_sunglasses.parts.01/hidden-earlier: 'HIDDEN EARLIER' -> 'sunglasses (separate card)' (old text not on the sheet; label 31px-cost away)
- ref: poet.04.action.red_black_sunglasses.parts.01/c-hands-and-props-open-l-open-r-sunglasses-separ: section box: its 9 contents are cut as separate parts
- ref: poet.04.action.red_black_sunglasses.parts.01/expression-reference-separate-blank-head-use-cor: section box: its 9 contents are cut as separate parts
- ref: poet.04.action.red_black_sunglasses.parts.01/d-face-reference-main-poses-on-companion-sheet: section box: its 3 contents are cut as separate parts
- added: poet.04.action.red_black_sunglasses.parts.01/pelvis-connector-seat-kneel
- added: poet.04.action.red_black_sunglasses.parts.01/connector-seat
- added: poet.04.action.red_black_sunglasses.parts.01/pelvis-seat-crouch-se-connector
- added: poet.04.action.red_black_sunglasses.parts.01/seat-crouch
- added: poet.04.action.red_black_sunglasses.parts.01/se
- added: poet.04.action.red_black_sunglasses.parts.01/se-2
- added: poet.04.action.red_black_sunglasses.parts.01/pelvis-connector
- added: poet.04.action.red_black_sunglasses.parts.01/seat-kneel
- added: poet.04.action.red_black_sunglasses.parts.01/pelvis-connector-2
- added: poet.04.action.red_black_sunglasses.parts.01/thigh-l
- added: poet.04.action.red_black_sunglasses.parts.01/thigh-r-shin-l
- added: poet.04.action.red_black_sunglasses.parts.01/shin-r
- added: poet.04.action.red_black_sunglasses.parts.01/farm-r
- added: poet.04.action.red_black_sunglasses.parts.01/thigh-l-2
- added: poet.04.action.red_black_sunglasses.parts.01/foot-l
- added: poet.04.action.red_black_sunglasses.parts.01/foot-l-2
- added: poet.04.action.red_black_sunglasses.parts.01/foot-l-foot-r
- added: poet.04.action.red_black_sunglasses.parts.01/foot-l-foot-r-2
- added: poet.04.action.red_black_sunglasses.parts.01/sunglasses-separate
- added: poet.04.action.red_black_sunglasses.parts.01/hands-and-open-l
- added: poet.04.action.red_black_sunglasses.parts.01/hidden-earlier

### poet.04.action.red_black_sunglasses.parts.02
- split: poet.04.action.red_black_sunglasses.parts.02/c-recovered-hands-04-5-only-use-from04-5-onward- (1516x520) -> 20 parts
- label: poet.04.action.red_black_sunglasses.parts.02/part: '' -> 'kneel front' (was empty/garbled)
- label: poet.04.action.red_black_sunglasses.parts.02/uarm-l-2: 'uarm.L' -> 'thigh.L' (closer label (cost 12 vs 35); old text is uarm-l's)
- label: poet.04.action.red_black_sunglasses.parts.02/farm-l-2: 'farm.L' -> 'shin.L' (closer label (cost 14 vs 31); old text is farm-l's)
- label: poet.04.action.red_black_sunglasses.parts.02/farm-r-2: 'farm.R' -> 'shin.R' (closer label (cost 18 vs 29); old text is farm-r's)
- ref: poet.04.action.red_black_sunglasses.parts.02/c-recovered-hands-04-5-only-use-from04-5-onward-: section box: its 20 contents are cut as separate parts
- added: poet.04.action.red_black_sunglasses.parts.02/part
- added: poet.04.action.red_black_sunglasses.parts.02/uarm-r
- added: poet.04.action.red_black_sunglasses.parts.02/uarm-l
- added: poet.04.action.red_black_sunglasses.parts.02/farm-r
- added: poet.04.action.red_black_sunglasses.parts.02/farm-l
- added: poet.04.action.red_black_sunglasses.parts.02/torso-profile-crouch
- added: poet.04.action.red_black_sunglasses.parts.02/torso-kneel-front
- added: poet.04.action.red_black_sunglasses.parts.02/torso-crouch-front
- added: poet.04.action.red_black_sunglasses.parts.02/uarm-r-2
- added: poet.04.action.red_black_sunglasses.parts.02/uarm-l-2
- added: poet.04.action.red_black_sunglasses.parts.02/farm-l-2
- added: poet.04.action.red_black_sunglasses.parts.02/farm-r-2
- added: poet.04.action.red_black_sunglasses.parts.02/seat-butt-kneel-front
- added: poet.04.action.red_black_sunglasses.parts.02/pelvis-connector-crouch-front
- added: poet.04.action.red_black_sunglasses.parts.02/pelvis-connector-kneel-front
- added: poet.04.action.red_black_sunglasses.parts.02/pelvis-connector-crouch-profile
- added: poet.04.action.red_black_sunglasses.parts.02/seat-butt-crouch-profile
- added: poet.04.action.red_black_sunglasses.parts.02/seat-butt-crouch-front
- added: poet.04.action.red_black_sunglasses.parts.02/foot-l
- added: poet.04.action.red_black_sunglasses.parts.02/foot-r

### poet.04.chest-sleeves
- label: poet.04.chest-sleeves/02-hollow-chest-threequarter: '02 HOLLOW CHEST THREEQUARTER' -> '02 HOLLOW CHEST TORSO THREEQUARTER' (re-read, more complete)
- label: poet.04.chest-sleeves/03-torso-front: '03 TORSO FRONT' -> '03 HEART-SEATED TORSO FRONT' (re-read, more complete)
- label: poet.04.chest-sleeves/empty-sleeve: 'EMPTY SLEEVE' -> '05 EMPTY SLEEVE FOREARM L' (closer label (cost 18 vs 1000000000); old text is sleeve-forearm's)
- label: poet.04.chest-sleeves/sleeve-forearm: 'SLEEVE FOREARM' -> 'EMPTY SLEEVE FOREARM' (re-read, more complete)
- label: poet.04.chest-sleeves/wrist-socket: 'WRIST SOCKET' -> '07 WRIST SOCKET L' (closer label (cost 15 vs 1000000000); old text is wrist-socket-2's)

### poet.04.main-poses
- unclip: poet.04.main-poses/04-3-walk-the-rows: +876 px
- unclip: poet.04.main-poses/04-5-left-then-right-2: +166 px

### poet.05.main-poses
- unclip: poet.05.main-poses/q3-restless-lying-1: +649 px
- label: poet.05.main-poses/ask-the-universe: 'ASK THE UNIVERSE' -> 'STANDING BOTH HANDS CUP STAR' (old text not on the sheet; label 25px-cost away)
- label: poet.05.main-poses/05-fingerprint-palm: '05 FINGERPRINT PALM' -> 'STANDING RAISE STAR OVERHEAD' (closer label (cost 29 vs 448))
- label: poet.05.main-poses/05-fingerprint-palm-standing-offer: '05 FINGERPRINT PALM STANDING OFFER' -> 'STANDING BOTH PALMS UP' (old text not on the sheet; label 31px-cost away)

### poet.06.action.red_black_sunglasses.parts
- label: poet.06.action.red_black_sunglasses.parts/part-1: '' -> 'foot.R' (was empty/garbled)
- label: poet.06.action.red_black_sunglasses.parts/uarm-r: 'uarm.R' -> 'uarm.L uarm.R' (re-read, more complete)
- label: poet.06.action.red_black_sunglasses.parts/farm-l: 'farm.L' -> 'farm.L farm.R' (re-read, more complete)
- label: poet.06.action.red_black_sunglasses.parts/thigh-l: 'thigh.L' -> 'thigh.L thigh.R' (re-read, more complete)
- label: poet.06.action.red_black_sunglasses.parts/thigh-r: 'thigh.R' -> 'thigh.L thigh.R' (re-read, more complete)
- label: poet.06.action.red_black_sunglasses.parts/hidden-in-pocket: 'hidden in_pocket' -> 'relearned_coin' (closer label (cost 63 vs 200))

### poet.06.main-poses
- label: poet.06.main-poses/02-open-arms-at-shore-chest-open-and-arms-wide: '02 OPEN ARMS AT SHORE CHEST OPEN AND ARMS WIDE.' -> 'FILE QUIET FORWARD WALKING POSE, LISTENING.' (closer label (cost 35 vs 267); old text is 03-set-down-the-coin-small-gold-coin-pinched-bet's)
- label: poet.06.main-poses/03-set-down-the-coin-small-gold-coin-pinched-bet: '03 SET DOWN THE COIN SMALL GOLD COIN PINCHED BETWEEN FINGERS AS HAND LOWERS.' -> 'AT CHEST OPEN AND ARMS WIDE.' (old text not on the sheet; label 35px-cost away)
- label: poet.06.main-poses/04-brace-unclench-two-phases-hand-braced-to-ches: '04 BRACE UNCLENCH TWO PHASES: HAND BRACED TO CHEST TENSE FIST, AND A RELEASE THEN SHOULDERS AND FINGERS OPEN.' -> '03 THE SMALL GOLD COIN PINCHED' (old text not on the sheet; label 24px-cost away)
- label: poet.06.main-poses/05-arms-up-with-crowd-both-long-sleeved-arms-rai: '05 ARMS UP WITH CROWD BOTH LONG-SLEEVED ARMS RAISED OVERHEAD, JOYFUL.' -> 'THEN SHOULDERS RELEASE AND FINGERS OPEN.' (closer label (cost 53 vs 172); old text is poet-06-main-poses-every-working-body's)
- label: poet.06.main-poses/body-part-and-prop-supplied-separately: 'body part and prop supplied separately' -> '06 PARTY A CONFIDENT STEP ACROSS' (old text not on the sheet; label 23px-cost away)

### poet.07.action.red_black_sunglasses.parts
- split: poet.07.action.red_black_sunglasses.parts/microphone-mic-stand-flat-push-pinch-point-open (1520x422) -> 12 parts
- split: poet.07.action.red_black_sunglasses.parts/microphone-mic-stand (1028x212) -> 7 parts
- split: poet.07.action.red_black_sunglasses.parts/part-3 (453x222) -> 2 parts
- label: poet.07.action.red_black_sunglasses.parts/thigh-r: 'thigh.R' -> 'thigh.L thigh.R' (re-read, more complete)
- label: poet.07.action.red_black_sunglasses.parts/thigh-l: 'thigh.L' -> 'thigh.L thigh.R' (re-read, more complete)
- label: poet.07.action.red_black_sunglasses.parts/part-2: '' -> 'flat_push' (was empty/garbled)
- label: poet.07.action.red_black_sunglasses.parts/part-4: '' -> 'point' (was empty/garbled)
- label: poet.07.action.red_black_sunglasses.parts/eleven-petal-daisy-see-poem-props: 'ELEVEN- PETAL DAISY see poem props' -> 'mic_stand' (closer label (cost 23 vs 99))
- label: poet.07.action.red_black_sunglasses.parts/petal-see: 'PETAL see' -> 'microphone' (old text not on the sheet; label 23px-cost away)
- ref: poet.07.action.red_black_sunglasses.parts/microphone-mic-stand-flat-push-pinch-point-open: section box: its 12 contents are cut as separate parts
- ref: poet.07.action.red_black_sunglasses.parts/microphone-mic-stand: section box: its 7 contents are cut as separate parts
- ref: poet.07.action.red_black_sunglasses.parts/part-3: section box: its 2 contents are cut as separate parts
- ref: poet.07.action.red_black_sunglasses.parts/face-reference-stand-front: label says 'REFERENCE'
- ref: poet.07.action.red_black_sunglasses.parts/face-reference: label says 'REFERENCE'
- added: poet.07.action.red_black_sunglasses.parts/thigh-r
- added: poet.07.action.red_black_sunglasses.parts/thigh-l
- added: poet.07.action.red_black_sunglasses.parts/uarm-r
- added: poet.07.action.red_black_sunglasses.parts/uarm-l
- added: poet.07.action.red_black_sunglasses.parts/torso-stand-front
- added: poet.07.action.red_black_sunglasses.parts/shin-r
- added: poet.07.action.red_black_sunglasses.parts/shin-l
- added: poet.07.action.red_black_sunglasses.parts/farm-l
- added: poet.07.action.red_black_sunglasses.parts/farm-r
- added: poet.07.action.red_black_sunglasses.parts/rear-seat-stand
- added: poet.07.action.red_black_sunglasses.parts/pelvis-connecter-waist-thigh-pivots-two
- added: poet.07.action.red_black_sunglasses.parts/foot-l
- added: poet.07.action.red_black_sunglasses.parts/open
- added: poet.07.action.red_black_sunglasses.parts/grip-daisy
- added: poet.07.action.red_black_sunglasses.parts/pinch
- added: poet.07.action.red_black_sunglasses.parts/mie-stand
- added: poet.07.action.red_black_sunglasses.parts/part
- added: poet.07.action.red_black_sunglasses.parts/part-2
- added: poet.07.action.red_black_sunglasses.parts/part-4
- added: poet.07.action.red_black_sunglasses.parts/eleven-petal-daisy-see-poem-props
- added: poet.07.action.red_black_sunglasses.parts/petal-see

### poet.07.main-poses
- unclip: poet.07.main-poses/2: +1934 px

### poet.08.action.red_black_sunglasses.parts
- split: poet.08.action.red_black_sunglasses.parts/b-shared-loose-limbs-single-segments-neighboring (1515x328) -> 12 parts
- split: poet.08.action.red_black_sunglasses.parts/c-hands-and-props-sunglasses (1517x221) -> 10 parts
- split: poet.08.action.red_black_sunglasses.parts/poses-for-reference-only-all-parts-above-remain- (1513x143) -> 5 parts
- label: poet.08.action.red_black_sunglasses.parts/part: '' -> 'reach threequarter_back' (was empty/garbled)
- label: poet.08.action.red_black_sunglasses.parts/part-2: '' -> 'shin.L' (was empty/garbled)
- label: poet.08.action.red_black_sunglasses.parts/part-3: '' -> 'open (R)' (was empty/garbled)
- label: poet.08.action.red_black_sunglasses.parts/part-4: '' -> 'flat_push (R)' (was empty/garbled)
- label: poet.08.action.red_black_sunglasses.parts/part-5: '' -> 'flat_push' (was empty/garbled)
- label: poet.08.action.red_black_sunglasses.parts/in-pocket-control-physical-no: 'in_pocket (control physical no' -> 'sunglasses' (closer label (cost 19 vs 300))
- ref: poet.08.action.red_black_sunglasses.parts/b-shared-loose-limbs-single-segments-neighboring: section box: its 12 contents are cut as separate parts
- ref: poet.08.action.red_black_sunglasses.parts/c-hands-and-props-sunglasses: section box: its 10 contents are cut as separate parts
- ref: poet.08.action.red_black_sunglasses.parts/poses-for-reference-only-all-parts-above-remain-: section box: its 5 contents are cut as separate parts
- added: poet.08.action.red_black_sunglasses.parts/part
- added: poet.08.action.red_black_sunglasses.parts/torso-sit-threequarter-back
- added: poet.08.action.red_black_sunglasses.parts/torso-lean-threequarter
- added: poet.08.action.red_black_sunglasses.parts/pelvis-connector
- added: poet.08.action.red_black_sunglasses.parts/pelvis-connector-2
- added: poet.08.action.red_black_sunglasses.parts/pelvis-connector-3
- added: poet.08.action.red_black_sunglasses.parts/seat-sit
- added: poet.08.action.red_black_sunglasses.parts/seat-lean
- added: poet.08.action.red_black_sunglasses.parts/seat-reach
- added: poet.08.action.red_black_sunglasses.parts/torso-dance-threequarter
- added: poet.08.action.red_black_sunglasses.parts/pelvis-connector-4
- added: poet.08.action.red_black_sunglasses.parts/seat-dance
- added: poet.08.action.red_black_sunglasses.parts/limbs-single-uarm-r
- added: poet.08.action.red_black_sunglasses.parts/thigh-l
- added: poet.08.action.red_black_sunglasses.parts/thigh-r
- added: poet.08.action.red_black_sunglasses.parts/part-2
- added: poet.08.action.red_black_sunglasses.parts/shin-r
- added: poet.08.action.red_black_sunglasses.parts/b-shared-uarm-l
- added: poet.08.action.red_black_sunglasses.parts/segments-no-farm-l
- added: poet.08.action.red_black_sunglasses.parts/parts-farm-r
- added: poet.08.action.red_black_sunglasses.parts/foot-l
- added: poet.08.action.red_black_sunglasses.parts/foot-r
- added: poet.08.action.red_black_sunglasses.parts/part-3
- added: poet.08.action.red_black_sunglasses.parts/part-4
- added: poet.08.action.red_black_sunglasses.parts/hands-and
- added: poet.08.action.red_black_sunglasses.parts/part-5
- added: poet.08.action.red_black_sunglasses.parts/in-pocket-control-physical-no

### poet.08.main-poses
- unclip: poet.08.main-poses/03-gentle-slow-bent-knee-dance-alone: +69 px

### poet.09.main-poses
- unclip: poet.09.main-poses/part-6: +119 px
- unclip: poet.09.main-poses/falter-at-shoulder-contact-2: +103 px
- unclip: poet.09.main-poses/part-14: +302 px
- label: poet.09.main-poses/falter-at-shoulder-contact: 'FALTER AT SHOULDER CONTACT' -> 'REACH THROUGH CROWD' (closer label (cost 34 vs 48); old text is falter-at-shoulder-contact-2's)
- label: poet.09.main-poses/hang-up: 'HANG UP' -> 'GLASS' (closer label (cost 120 vs 169))
- label: poet.09.main-poses/ex-disappears: 'EX DISAPPEARS' -> 'FOLLOW FOOTPRINTS' (closer label (cost 20 vs 68))

### poet.10.main-poses
- label: poet.10.main-poses/q5-left-hand-in: 'Q5 LEFT HAND IN' -> 'LOW' (closer label (cost 43 vs 103))

### poet.11.hands
- label: poet.11.hands/13-guiding-palm-up-l: '13 GUIDING PALM-UP L_' -> 'PALM-UP L_ 14' (old text not on the sheet; label 40px-cost away)
- label: poet.11.hands/15-grip-l: '15 GRIP L' -> '15 JOURNAL' (old text not on the sheet; label 18px-cost away)
- label: poet.11.hands/17-pinch-l: '17 PINCH L' -> '17 PAGE PINCH L' (re-read, more complete)
- label: poet.11.hands/18-page-pinch-r: '18 PAGE PINCH R' -> 'core open/relaxed hands' (closer label (cost 68 vs 1000000000); old text is 17-pinch-l's)
- ref: poet.11.hands/ion-2: label fragment (printed words)

### poet.12.action.lean-parts
- label: poet.12.action.lean-parts/01-torso-threequarter: '01 TORSO THREEQUARTER' -> '01 TORSO LEAN THREEQUARTER' (re-read, more complete)
- label: poet.12.action.lean-parts/02-profile: '02 PROFILE' -> 'PROFILE a' (closer label (cost 34 vs 1000000000); old text is 04-hip-bridge-profile's)
- label: poet.12.action.lean-parts/upper-arm-l: 'UPPER ARM L' -> '07 UPPER ARM L' (re-read, more complete)

### poet.12.faces
- unclip: poet.12.faces/head: +41 px
- label: poet.12.faces/eyes-only: 'EYES ONLY' -> 'SMALL EXPRESSION PROOF' (closer label (cost 18 vs 1000000000))
- label: poet.12.faces/only: 'ONLY' -> 'MOUTH ONLY' (closer label (cost 6 vs 1000000000); old text is brows-only-2's)
- label: poet.12.faces/eyes-only-3: 'EYES ONLY' -> 'REFERENCE' (closer label (cost 16 vs 1000000000))
- label: poet.12.faces/mouth: 'MOUTH' -> 'MOUTH ONLY' (closer label (cost 7 vs 222))
- label: poet.12.faces/refe: 'REFE' -> 'REFERENCE' (closer label (cost 5 vs 211); old text is eyes-only-3's)
- label: poet.12.faces/blank: 'BLANK' -> 'BLANK HEAD (THREEQUARTER)' (re-read, more complete)
- label: poet.12.faces/eyes: 'EYES' -> 'REFERENCE' (closer label (cost 21 vs 1000000000))
- label: poet.12.faces/eyes-2: 'EYES' -> 'EYES ONLY' (closer label (cost 12 vs 648))
- label: poet.12.faces/only-2: 'ONLY' -> 'MOUTH ONLY' (closer label (cost 6 vs 1000000000); old text is brows-only-2's)
- label: poet.12.faces/only-3: 'ONLY' -> 'REFERENCE' (closer label (cost 6 vs 1000000000); old text is brows-only-2's)
- label: poet.12.faces/only-4: 'ONLY' -> 'EYES ONLY' (closer label (cost 18 vs 1000000000); old text is brows-only-2's)
- label: poet.12.faces/only-5: 'ONLY' -> 'MOUTH ONLY' (closer label (cost 5 vs 1000000000); old text is brows-only-2's)
- ref: poet.12.faces/eyes-only: label says 'PROOF'
- ref: poet.12.faces/eyes-only-3: label says 'REFERENCE'
- ref: poet.12.faces/refe: label says 'REFERENCE'
- ref: poet.12.faces/eyes: label says 'REFERENCE'
- ref: poet.12.faces/only-3: label says 'REFERENCE'

### poet.12.hands-pocket
- label: poet.12.hands-pocket/07-relaxed-l: '07 RELAXED L' -> '03 PEACE L' (closer label (cost 47 vs 1000000000))
- label: poet.12.hands-pocket/embrace-reaching-r: 'EMBRACE-REACHING R' -> '10 EMBRACE-REACHING' (closer label (cost 34 vs 1000000000); old text is 09-embrace-reaching's)
- label: poet.12.hands-pocket/jacket-pocket-patch: 'JACKET POCKET PATCH' -> '11 JACKET POCKET PATCH' (re-read, more complete)

### poet.12.main-poses
- ref: poet.12.main-poses/hands-these-poses-not-cut-cards-poet-12-main-pos: label says 'not cut'

### poet.13.action.cafe-fire-parts
- label: poet.13.action.cafe-fire-parts/torso: 'TORSO' -> '1A TORSO SIT THREEQUARTER' (closer label (cost 10 vs 627); old text is torso-sitting-deep-crouch's)

### poet.13.action.harvest-parts
- label: poet.13.action.harvest-parts/01-arms-detached: '01 (ARMS DETACHED)' -> '01 TORSO (ARMS DETACHED)' (re-read, more complete)
- label: poet.13.action.harvest-parts/04-upper-arm-l: '04 UPPER ARM L' -> 'UPPER ARML 05 FOREARM L' (re-read, more complete)
- label: poet.13.action.harvest-parts/06-upper: '06 UPPER' -> 'ARMR' (old text not on the sheet; label 28px-cost away)

### poet.13.faces
- label: poet.13.faces/small-scale-use-isolated: 'small scale; use isolated' -> 'HEAD PROOF' (old text not on the sheet; label 17px-cost away)
- ref: poet.13.faces/small-scale-use-isolated: label says 'PROOF'

### poet.13.hands
- label: poet.13.hands/armful: 'ARMFUL' -> 'ARMFUL 04SUPPORTFLOWERARMFUL' (closer label (cost 34 vs 39))
- label: poet.13.hands/grip-blossom-stem-r: 'GRIP BLOSSOM STEM R' -> '05 GRIP BLOSSOM STEM' (closer label (cost 21 vs 1000000000); old text is grip-blossom-stem-l's)
- label: poet.13.hands/07-wave: '07 WAVE' -> '07 HELLO WAVE' (re-read, more complete)

### poet.14.action.red_black_sunglasses.parts.01
- split: poet.14.action.red_black_sunglasses.parts.01/float-front (454x665) -> 10 parts
- label: poet.14.action.red_black_sunglasses.parts.01/thigh-l: 'thigh.L' -> 'uarm.L' (old text not on the sheet; label 21px-cost away)
- label: poet.14.action.red_black_sunglasses.parts.01/thigh-r: 'thigh.R' -> 'uarm.R' (old text not on the sheet; label 21px-cost away)
- label: poet.14.action.red_black_sunglasses.parts.01/shin-l: 'shin.L' -> 'farm.L' (old text not on the sheet; label 25px-cost away)
- label: poet.14.action.red_black_sunglasses.parts.01/shin-r: 'shin.R' -> 'farm.R' (old text not on the sheet; label 25px-cost away)
- label: poet.14.action.red_black_sunglasses.parts.01/thigh-r-2: 'thigh.R' -> 'thigIER shin.L shin.R' (old text not on the sheet; label 38px-cost away)
- label: poet.14.action.red_black_sunglasses.parts.01/part: '' -> 'head (no glasses)' (was empty/garbled)
- ref: poet.14.action.red_black_sunglasses.parts.01/float-front: section box: its 10 contents are cut as separate parts
- added: poet.14.action.red_black_sunglasses.parts.01/thigh-l
- added: poet.14.action.red_black_sunglasses.parts.01/thigh-r
- added: poet.14.action.red_black_sunglasses.parts.01/shin-l
- added: poet.14.action.red_black_sunglasses.parts.01/shin-r
- added: poet.14.action.red_black_sunglasses.parts.01/foot-l
- added: poet.14.action.red_black_sunglasses.parts.01/thigh-r-2
- added: poet.14.action.red_black_sunglasses.parts.01/shin-l-2
- added: poet.14.action.red_black_sunglasses.parts.01/shin-r-2
- added: poet.14.action.red_black_sunglasses.parts.01/part
- added: poet.14.action.red_black_sunglasses.parts.01/foot-l-2

### poet.14.action.red_black_sunglasses.parts.02
- label: poet.14.action.red_black_sunglasses.parts.02/uarm-r-shoulder-to-elbow: 'uarm.R (shoulder to elbow)' -> 'uarm.R (shoulder to elbow) (elbow to wrist)' (closer label (cost 29 vs 1000000000); old text is uarm-l-shoulder-to-elbow's)
- label: poet.14.action.red_black_sunglasses.parts.02/hidden: 'hidden' -> 'prop vintage_door (knob only)' (closer label (cost 12 vs 148))

### poet.14.exit
- label: poet.14.exit/16-sunglasses: '16 sunglasses' -> '16 sunglasses (separate)' (re-read, more complete)
- label: poet.14.exit/17-hand-l: '17 hand L' -> '17 hand (open)' (re-read, more complete)
- label: poet.14.exit/18-hand-r: '18 hand R' -> '18 hand (open)' (re-read, more complete)
- label: poet.14.exit/19-hand-l: '19 hand L' -> '19 hand L (knob grip)' (closer label (cost 17 vs 1000000000))
- label: poet.14.exit/20-hand-r: '20 hand R' -> '20 hand (knob grip)' (re-read, more complete)
- label: poet.14.exit/21-knob: '21 knob' -> 'knob prop' (old text not on the sheet; label 29px-cost away)
- label: poet.14.exit/part-20: '' -> 'poet.' (was empty/garbled)
- ref: poet.14.exit/part-20: label fragment (printed words)

### poet.14.faces-hands
- label: poet.14.faces-hands/part-4: '' -> 'MOUTH (NEUTRAL)' (was empty/garbled)
- label: poet.14.faces-hands/part-9: '' -> 'MOUTH (CLOSED)' (was empty/garbled)
- label: poet.14.faces-hands/closed: '(CLOSED)' -> 'EYES (CLOSED)' (re-read, more complete)
- label: poet.14.faces-hands/closed-2: '(CLOSED)' -> 'MOUTH (NEUTRAL)' (closer label (cost 3 vs 549); old text is closed's)
- label: poet.14.faces-hands/part-14: '' -> 'EYEBROWS (RAISED)' (was empty/garbled)
- label: poet.14.faces-hands/part-15: '' -> 'MOUTH (SLIGHT OPEN)' (was empty/garbled)
- label: poet.14.faces-hands/part-16: '' -> '8. SUNGLASSES (FRONT)' (was empty/garbled)
- label: poet.14.faces-hands/raise: 'RAISE)' -> 'EYEBROWS (SLIGHT RAISE)' (closer label (cost 10 vs 57); old text is part-14's)
- label: poet.14.faces-hands/part-19: '' -> 'MOUTH (SMILE)' (was empty/garbled)
- label: poet.14.faces-hands/part-20: '' -> '9. SUNGLASSES (THREEQUARTER)' (was empty/garbled)
- label: poet.14.faces-hands/10-l: '10. L' -> '10. RELAXED L' (was empty/garbled)
- label: poet.14.faces-hands/part-24: '' -> '13. OPENR' (was empty/garbled)

### poet.14.muse-dance
- label: poet.14.muse-dance/cards: 'CARDS)' -> 'ORBIT' (closer label (cost 41 vs 99); old text is right-partner-grip's)
- label: poet.14.muse-dance/celebration-hands-separate: 'CELEBRATION HANDS (SEPARATE' -> 'CELEBRATION HANDS (SEPARATE CARDS)' (re-read, more complete)
- label: poet.14.muse-dance/cards-2: 'CARDS)' -> 'VICTORY BOTH ARMS RAISED' (closer label (cost 23 vs 1000000000); old text is right-partner-grip's)
- label: poet.14.muse-dance/left-hand-partner-grip: 'LEFT HAND (PARTNER GRIP)' -> 'Use the' (closer label (cost 110 vs 726); old text is partner-grip-hands-separate's)
- label: poet.14.muse-dance/right-partner-grip: 'RIGHT (PARTNER GRIP)' -> 'GRIP HANDS (SEPARATE CARDS)' (closer label (cost 22 vs 737); old text is partner-grip-hands-separate's)
- label: poet.14.muse-dance/right-hand-partner-grip-right-poet: 'RIGHT HAND (PARTNER GRIP) (RIGHT POET)' -> 'Poet parts twice. POET_MUSE mirrorX true. Pose references only; separate working parts supplied on action sheets.' (closer label (cost 110 vs 1000000000); old text is right-hand-celebration-2's)
- label: poet.14.muse-dance/left-hand-celebration: 'LEFT HAND (CELEBRATION)' -> 'LEFT HAND (CELEBRATION) (LEFT POET)' (re-read, more complete)
- label: poet.14.muse-dance/right-hand-celebration: 'RIGHT HAND (CELEBRATION)' -> 'RIGHT HAND (CELEBRATION) (LEFT POET)' (re-read, more complete)
- label: poet.14.muse-dance/left-hand-celebration-2: 'LEFT HAND (CELEBRATION)' -> 'LEFT HAND (CELEBRATION) (RIGHT POET)' (closer label (cost 10 vs 1000000000); old text is left-hand-celebration's)
- label: poet.14.muse-dance/right-hand-celebration-2: 'RIGHT HAND (CELEBRATION)' -> 'RIGHT HAND (CELEBRATION) (RIGHT POET)' (closer label (cost 11 vs 1000000000); old text is right-hand-celebration's)

### poet.14.reserve
- ref: poet.14.reserve/7-sunglasses-removable: label fragment (printed words)

### poet.black_tshirt.compact-core
- label: poet.black_tshirt.compact-core/upperarm: 'upperarm' -> '05 upperarm L' (closer label (cost 7 vs 1000000000); old text is upperarm-2's)
- label: poet.black_tshirt.compact-core/upperarm-2: 'upperarm' -> '07 upperarm' (re-read, more complete)
- label: poet.black_tshirt.compact-core/forearm: 'forearm' -> '08 forearm' (re-read, more complete)

### poet.red_black_sunglasses.body.back
- label: poet.red_black_sunglasses.body.back/poet-black-upper-arm-l: 'POET BLACK UPPER ARM L' -> 'TORSO' (closer label (cost 22 vs 163); old text is l-2's)
- label: poet.red_black_sunglasses.body.back/for-l: 'FOR L' -> 'L HAND L' (closer label (cost 71 vs 454); old text is thigh's)
- label: poet.red_black_sunglasses.body.back/poet-red-black-sunglasses-body-back: 'poet.red_black_sunglasses.body.back' -> 'TORSO' (old text not on the sheet; label 25px-cost away)
- label: poet.red_black_sunglasses.body.back/l-2: 'L' -> 'UPPER ARM L' (was empty/garbled)
- label: poet.red_black_sunglasses.body.back/thigh: 'THIGH' -> 'FOOT L' (closer label (cost 20 vs 296); old text is thigh-r's)
- label: poet.red_black_sunglasses.body.back/part-13: '' -> 'FOOTR' (was empty/garbled)

### poet.red_black_sunglasses.body.front
- ref: poet.red_black_sunglasses.body.front/sunglasses: label fragment (printed words)
- ref: poet.red_black_sunglasses.body.front/sunglasses-body: label fragment (printed words)

### poet.red_black_sunglasses.body.profile
- label: poet.red_black_sunglasses.body.profile/part-4: '' -> 'UPPER ARML L FOREARM L' (was empty/garbled)

### poet.red_black_sunglasses.body.threequarter
- ref: poet.red_black_sunglasses.body.threequarter/body: label fragment (printed words)

### poet.red_black_sunglasses.face.front
- label: poet.red_black_sunglasses.face.front/part-8: '' -> 'happy_arc' (was empty/garbled)
- label: poet.red_black_sunglasses.face.front/wide-2: 'wide' -> 'glance_side' (closer label (cost 4 vs 27); old text is wide's)
- label: poet.red_black_sunglasses.face.front/part-11: '' -> 'glance_side' (was empty/garbled)
- label: poet.red_black_sunglasses.face.front/part-14: '' -> 'raised' (was empty/garbled)
- label: poet.red_black_sunglasses.face.front/part-18: '' -> 'angry' (was empty/garbled)
- label: poet.red_black_sunglasses.face.front/rest-2: 'rest' -> '12 mouths (front)' (closer label (cost 18 vs 85); old text is part-21's)
- label: poet.red_black_sunglasses.face.front/part-21: '' -> 'rest' (was empty/garbled)
- label: poet.red_black_sunglasses.face.front/part-22: '' -> 'smile' (was empty/garbled)
- label: poet.red_black_sunglasses.face.front/part-23: '' -> 'grin_teeth' (was empty/garbled)
- label: poet.red_black_sunglasses.face.front/open-a: 'open_A' -> 'open_O' (closer label (cost 20 vs 160); old text is open-a-2's)
- label: poet.red_black_sunglasses.face.front/f-v: 'F_V' -> 'grin_teeth' (was empty/garbled)
- label: poet.red_black_sunglasses.face.front/open-a-3: 'open_A' -> 'strain_teeth' (closer label (cost 7 vs 28); old text is open-a-2's)
- ref: poet.red_black_sunglasses.face.front/sunglasses: label fragment (printed words)
- ref: poet.red_black_sunglasses.face.front/part-11: label fragment (printed words)
- ref: poet.red_black_sunglasses.face.front/sad-2: label fragment (printed words)
- ref: poet.red_black_sunglasses.face.front/part-21: label fragment (printed words)

### poet.red_black_sunglasses.feet
- label: poet.red_black_sunglasses.feet/footwear-six-states: 'footwear six states' -> 'right footwear six states.' (re-read, more complete)

### poet.red_black_sunglasses.hands
- label: poet.red_black_sunglasses.hands/relaxed-palm: 'relaxed palm' -> 'relaxed back' (closer label (cost 33 vs 54); old text is thumb-back's)
- label: poet.red_black_sunglasses.hands/open-palm: 'open palm' -> 'open back' (closer label (cost 26 vs 47); old text is peace-back's)
- label: poet.red_black_sunglasses.hands/grip-palm: 'grip palm' -> 'grip back' (closer label (cost 39 vs 47); old text is claw-back's)
- label: poet.red_black_sunglasses.hands/pinch-palm: 'pinch palm' -> 'pinch back' (closer label (cost 36 vs 55); old text is cup-back's)
- label: poet.red_black_sunglasses.hands/thumb-back: 'thumb back' -> 'relaxed palm' (closer label (cost 32 vs 58); old text is thumb-palm's)
- label: poet.red_black_sunglasses.hands/peace-back: 'peace back' -> 'open palm' (closer label (cost 27 vs 45); old text is peace-palm's)
- label: poet.red_black_sunglasses.hands/wave-back: 'wave back' -> 'fist palm' (closer label (cost 49 vs 1000000000); old text is peace-palm's)
- label: poet.red_black_sunglasses.hands/claw-back: 'claw back' -> 'grip palm' (closer label (cost 40 vs 56); old text is claw-palm's)
- label: poet.red_black_sunglasses.hands/cup-back: 'cup back' -> 'pinch palm' (closer label (cost 42 vs 65); old text is cup-palm's)
- label: poet.red_black_sunglasses.hands/peace-palm: 'peace palm' -> 'peace back' (closer label (cost 21 vs 55); old text is back-eyelet-tabs's)
- label: poet.red_black_sunglasses.hands/thumb-palm: 'thumb palm' -> 'thumb back' (closer label (cost 24 vs 52); old text is right-hand-shapes-palm's)
- label: poet.red_black_sunglasses.hands/wave-palm: 'wave palm' -> 'back' (closer label (cost 25 vs 1000000000); old text is back-eyelet-tabs's)
- label: poet.red_black_sunglasses.hands/claw-palm: 'claw palm' -> 'claw back' (closer label (cost 35 vs 51); old text is claw-palm-2's)
- label: poet.red_black_sunglasses.hands/cup-palm: 'cup palm' -> 'cup back' (closer label (cost 45 vs 56); old text is cup-palm-2's)
- label: poet.red_black_sunglasses.hands/right-hand-shapes-palm: 'right-hand shapes palm' -> 'thumb palm' (closer label (cost 22 vs 61))
- label: poet.red_black_sunglasses.hands/back-eyelet-tabs: 'back eyelet tabs' -> 'peace palm' (closer label (cost 37 vs 102))

### poet.red_black_sunglasses.hipcore
- split: poet.red_black_sunglasses.hipcore/hip-bridge-5-rear-seat (569x312) -> 2 parts
- recut: poet.red_black_sunglasses.hipcore/3-waist-link: framed panel [756, 135, 166, 451] -> figure [780, 281, 119, 185]
- recut: poet.red_black_sunglasses.hipcore/4-hip-bridge: framed panel [930, 135, 302, 451] -> figure [944, 263, 272, 230]
- label: poet.red_black_sunglasses.hipcore/standing: 'STANDING' -> 'SMALL ASSEMBLY PROOFS' (old text not on the sheet; label 28px-cost away)
- ref: poet.red_black_sunglasses.hipcore/hip-bridge-5-rear-seat: section box: its 2 contents are cut as separate parts
- ref: poet.red_black_sunglasses.hipcore/standing: label says 'PROOFS'
- ref: poet.red_black_sunglasses.hipcore/seated: under the band heading 'SMALL ASSEMBLY PROOFS'
- added: poet.red_black_sunglasses.hipcore/standing
- added: poet.red_black_sunglasses.hipcore/seated

### poet.red_black_sunglasses.master
- label: poet.red_black_sunglasses.master/mouth: 'MOUTH' -> 'MOUTH SERIOUS' (closer label (cost 5 vs 1000000000); old text is mouth-open-separate's)
- label: poet.red_black_sunglasses.master/2-5-front-left-upper: '2 5 (FRONT) LEFT) (UPPER' -> '2 TORSO (FRONT)' (old text not on the sheet; label 8px-cost away)
- label: poet.red_black_sunglasses.master/5-upper-arm-right: '5 (UPPER ARM RIGHT)' -> 'HEAD BACK' (closer label (cost 42 vs 713); old text is 4-uarm-l-upper-arm-left's)
- label: poet.red_black_sunglasses.master/7-farm-r-forearm-right: '7 FARM.R (FOREARM RIGHT)' -> 'UARM. 7 FARM.R (HAND RIGHT) (UPPER ARM' (old text not on the sheet; label 2px-cost away)
- label: poet.red_black_sunglasses.master/front-2: 'FRONT' -> 'SUNGLASSES' (closer label (cost 6 vs 1000000000))
- label: poet.red_black_sunglasses.master/hand-grip: 'HAND GRIP' -> '(ACTION CARDS WITH WRIST TABS)' (closer label (cost 24 vs 377); old text is 9-hand-right's)
- label: poet.red_black_sunglasses.master/hand-hold-orb: 'HAND HOLD ORB' -> 'SUNGLASSES LEFT' (closer label (cost 91 vs 672); old text is 9-hand-right's)
- label: poet.red_black_sunglasses.master/shin-left: '(SHIN LEFT)' -> '12 SHIN.L (SHIN LEFT)' (re-read, more complete)
- label: poet.red_black_sunglasses.master/11-thigh-right: '11 (THIGH RIGHT)' -> '11 THIGH.R 13 (THIGH RIGHT)' (re-read, more complete)
- label: poet.red_black_sunglasses.master/universe-sphere: 'UNIVERSE_SPHERE' -> '(SEPARATE CARDS)' (old text not on the sheet; label 23px-cost away)
- label: poet.red_black_sunglasses.master/daisy: 'DAISY' -> 'HOLD' (closer label (cost 22 vs 108); old text is daisy-2's)
- label: poet.red_black_sunglasses.master/kneel: 'KNEEL' -> 'KNEEL THREEQUARTER' (closer label (cost 5 vs 1000000000); old text is kneel-crouch-threequarte's)
- label: poet.red_black_sunglasses.master/crouch-poet-red-black-sunglasses-master: 'CROUCH poet.red_black_sunglasses.master' -> 'CROUCH PROFILE' (old text not on the sheet; label 16px-cost away)
- ref: poet.red_black_sunglasses.master/assembled-identity-front: label says 'ASSEMBLED'

### poet.red_black_sunglasses.replacements.back_lying
- label: poet.red_black_sunglasses.replacements.back_lying/left-thigh: 'LEFT THIGH' -> 'TORSO (back lying)' (closer label (cost 21 vs 44); old text is left-thigh-2's)
- label: poet.red_black_sunglasses.replacements.back_lying/right-thigh: 'RIGHT THIGH' -> 'WAIST HIP (back lying)' (closer label (cost 58 vs 72); old text is right-thigh-2's)
- label: poet.red_black_sunglasses.replacements.back_lying/part-3: '' -> 'SEAT OVERLAY (back lying)' (was empty/garbled)
- label: poet.red_black_sunglasses.replacements.back_lying/shin: 'SHIN' -> 'LEFT ARM' (old text not on the sheet; label 28px-cost away)
- label: poet.red_black_sunglasses.replacements.back_lying/hand: 'HAND' -> 'LEFT FOREARM' (closer label (cost 23 vs 327); old text is part-8's)
- label: poet.red_black_sunglasses.replacements.back_lying/hand-hand: 'HAND HAND' -> 'RIGHT FOREARM' (closer label (cost 23 vs 320); old text is part-9's)
- label: poet.red_black_sunglasses.replacements.back_lying/part-8: '' -> 'LEFT HAND' (was empty/garbled)
- label: poet.red_black_sunglasses.replacements.back_lying/part-9: '' -> 'RIGHT HAND' (was empty/garbled)
- label: poet.red_black_sunglasses.replacements.back_lying/left-boot: 'LEFT BOOT' -> 'RIGHT' (closer label (cost 32 vs 315); old text is left-boot-2's)

### poet.red_black_sunglasses.replacements.deep_crouch
- label: poet.red_black_sunglasses.replacements.deep_crouch/left-thigh-2-eyelets: 'LEFT THIGH (2 eyelets)' -> 'TORSO (sleeveless, arms, head)' (closer label (cost 17 vs 40); old text is left-thigh-2-eyelets-2's)
- label: poet.red_black_sunglasses.replacements.deep_crouch/hand-only: '(hand only)' -> 'LEFT (2 eyelets)' (closer label (cost 35 vs 273); old text is hand-only-2's)
- label: poet.red_black_sunglasses.replacements.deep_crouch/hand-only-hand-only: '(hand only) (hand only)' -> 'RIGHT (2 eyelets)' (closer label (cost 36 vs 112); old text is hand-only-2's)
- label: poet.red_black_sunglasses.replacements.deep_crouch/hand-only-2: '(hand only)' -> 'LEFT HAND (hand only)' (re-read, more complete)
- label: poet.red_black_sunglasses.replacements.deep_crouch/hand-only-3: '(hand only)' -> 'RIGHT HAND (hand only)' (closer label (cost 48 vs 1000000000); old text is hand-only-2's)
- label: poet.red_black_sunglasses.replacements.deep_crouch/part-9: '' -> 'WAIST HIP (3 eyelets)' (was empty/garbled)
- label: poet.red_black_sunglasses.replacements.deep_crouch/2-eyelets: '(2 eyelets)' -> 'THIGH eyelets)' (closer label (cost 19 vs 1000000000); old text is right-upper-arm-2-eyelets's)
- label: poet.red_black_sunglasses.replacements.deep_crouch/left-boot-boot-only: 'LEFT BOOT (boot only)' -> 'RIGHT (2 eyelets)' (closer label (cost 21 vs 297); old text is left-boot-boot-only-2's)

### poet.red_black_sunglasses.replacements.falling
- label: poet.red_black_sunglasses.replacements.falling/thigh: 'THIGH' -> 'LEFT' (closer label (cost 32 vs 1000000000); old text is right-shin's)
- label: poet.red_black_sunglasses.replacements.falling/left: 'LEFT' -> 'REAR-SEAT OVERLAY (BACK)' (closer label (cost 33 vs 1000000000); old text is thigh's)
- label: poet.red_black_sunglasses.replacements.falling/a-boot: 'a BOOT' -> 'LEFT' (closer label (cost 26 vs 35); old text is a-boot-2's)
- label: poet.red_black_sunglasses.replacements.falling/right: 'RIGHT' -> 'FOREARM' (closer label (cost 26 vs 1000000000); old text is right-shin's)
- label: poet.red_black_sunglasses.replacements.falling/boot: 'BOOT' -> 'LEFT HAND' (closer label (cost 25 vs 1000000000); old text is a-boot-2's)
- label: poet.red_black_sunglasses.replacements.falling/part-9: '' -> 'RIGHT' (was empty/garbled)

### poet.red_black_sunglasses.replacements.side_lying
- label: poet.red_black_sunglasses.replacements.side_lying/right-upper-arm: 'RIGHT UPPER ARM' -> 'HIPS)' (closer label (cost 32 vs 1000000000); old text is right-forearm's)
- label: poet.red_black_sunglasses.replacements.side_lying/right-shin: 'RIGHT SHIN' -> 'poet.red_black_sunglasses.replacements.side_ lying' (closer label (cost 98 vs 1000000000); old text is right-thigh's)

### poet_soul.08.core
- label: poet_soul.08.core/15-head: '15 HEAD' -> '15 RING HEAD' (re-read, more complete)

### poet_soul.08.main-poses
- label: poet_soul.08.main-poses/stand: 'STAND' -> 'STAND FRONT' (re-read, more complete)

### woman.09.mother.heads-hands
- split: woman.09.mother.heads-hands/assembled-references-not-cut-parts (1512x729) -> 25 parts
- label: woman.09.mother.heads-hands/pain-1: 'PAIN (1)' -> 'eyes (pain)' (closer label (cost 3 vs 12))
- label: woman.09.mother.heads-hands/pain-2: 'PAIN (2)' -> 'brows (pain)' (closer label (cost 7 vs 107))
- label: woman.09.mother.heads-hands/pain-3: 'PAIN (3)' -> 'mouth (pain)' (closer label (cost 3 vs 178))
- label: woman.09.mother.heads-hands/weeping-1: 'WEEPING (1)' -> 'eyes (weeping)' (closer label (cost 3 vs 9))
- label: woman.09.mother.heads-hands/weeping-2: 'WEEPING (2)' -> 'mouth (weeping)' (closer label (cost 20 vs 99))
- label: woman.09.mother.heads-hands/brows: 'brows' -> 'brows (prayer)' (closer label (cost 5 vs 1000000000))
- label: woman.09.mother.heads-hands/brows-2: 'brows' -> 'mouth (prayer)' (closer label (cost 0 vs 1000000000))
- label: woman.09.mother.heads-hands/hand-cards: 'HAND CARDS' -> 'mouth (strain) ACTION HAND CARDS (empty hands, with wrist tabs)' (old text not on the sheet; label 26px-cost away)
- label: woman.09.mother.heads-hands/grip-r-fist-l: 'GRIP R. FIST L.' -> 'R. OPEN ARGUE' (closer label (cost 25 vs 122); old text is r-fist's)
- label: woman.09.mother.heads-hands/cup-prayer: 'CUP PRAYER' -> 'R. CUP PRAYER' (closer label (cost 13 vs 1000000000); old text is l-cup-prayer's)
- ref: woman.09.mother.heads-hands/assembled-references-not-cut-parts: section box: its 25 contents are cut as separate parts
- added: woman.09.mother.heads-hands/pain-1
- added: woman.09.mother.heads-hands/pain-2
- added: woman.09.mother.heads-hands/pain-3
- added: woman.09.mother.heads-hands/1
- added: woman.09.mother.heads-hands/2
- added: woman.09.mother.heads-hands/weeping-1
- added: woman.09.mother.heads-hands/weeping-2
- added: woman.09.mother.heads-hands/back-prayer
- added: woman.09.mother.heads-hands/threequarter-back
- added: woman.09.mother.heads-hands/threequarter
- added: woman.09.mother.heads-hands/profile
- added: woman.09.mother.heads-hands/front-replaceable-parts-expressions
- added: woman.09.mother.heads-hands/eyes-closed
- added: woman.09.mother.heads-hands/eyes-strain
- added: woman.09.mother.heads-hands/brows
- added: woman.09.mother.heads-hands/brows-strain
- added: woman.09.mother.heads-hands/brows-2
- added: woman.09.mother.heads-hands/hand-cards
- added: woman.09.mother.heads-hands/grip-r-fist-l
- added: woman.09.mother.heads-hands/cup-prayer
- added: woman.09.mother.heads-hands/l-open-argue
- added: woman.09.mother.heads-hands/r-fist
- added: woman.09.mother.heads-hands/grip-receiver
- added: woman.09.mother.heads-hands/r-grip-receiver
- added: woman.09.mother.heads-hands/l-cup-prayer

### woman.13.body
- label: woman.13.body/8-upper-arm: '8. UPPER ARM' -> 'UPPER ARM L' (closer label (cost 23 vs 1000000000); old text is upper-arm-r's)

### woman.13.heads-hands
- label: woman.13.heads-hands/10-soft-raise: '10. SOFT RAISE' -> '10. BROWS SOFT RAISE' (re-read, more complete)
- label: woman.13.heads-hands/tender: 'TENDER' -> '11. BROWS TENDER' (re-read, more complete)
- label: woman.13.heads-hands/12-calm: '12. CALM' -> '12. MOUTH CALM' (re-read, more complete)
- label: woman.13.heads-hands/13-small-smile: '13? SMALL SMILE' -> '13. MOUTH SMALL SMILE' (re-read, more complete)
- label: woman.13.heads-hands/open-15-l: 'OPEN 15. L' -> '15. HA OPEN L' (old text not on the sheet; label 3px-cost away)
- label: woman.13.heads-hands/16-hand-r: '16. HAND R' -> '16. HAND OPEN R' (re-read, more complete)
- label: woman.13.heads-hands/hand-relaxed: 'HAND RELAXED' -> '18. HAND RELAXED' (re-read, more complete)
- ref: woman.13.heads-hands/a-face-proof-calm-open: label says 'PROOF'
- ref: woman.13.heads-hands/b-face-proof-meeting-gaze: label says 'PROOF'
- ref: woman.13.heads-hands/c-face-proof-small-smile: label says 'PROOF'

### woman.13.window-action
- label: woman.13.window-action/distant: '(DISTANT)' -> '01 HEAD (DISTANT)' (re-read, more complete)
- label: woman.13.window-action/03-bodice-front: '03 BODICE FRONT' -> '03 BODICE FRONT (ARMSLESS)' (re-read, more complete)
- label: woman.13.window-action/arm-l: 'ARM L' -> '07 UPPER ARM' (closer label (cost 15 vs 1000000000); old text is l's)
- label: woman.13.window-action/arm-r: 'ARM R' -> '08 UPPER ARM R' (old text not on the sheet; label 16px-cost away)
- label: woman.13.window-action/l: 'L' -> 'FOREARM L' (was empty/garbled)
- label: woman.13.window-action/part-7: '' -> '02 EYES OVERLAY (7 POINTS)' (was empty/garbled)
- label: woman.13.window-action/04-bridge-hip: '04 BRIDGE HIP' -> '04 HIP BRIDGE (1 WAIST, 2 THIGH)' (old text not on the sheet; label 35px-cost away)
- label: woman.13.window-action/skirt: 'SKIRT' -> '06 FRONT SKIRT' (re-read, more complete)
- ref: woman.13.window-action/16-13-14-head-proof-stand-small-scale: label says 'PROOF'

### young_ghost.02.main-poses
- unclip: young_ghost.02.main-poses/06-wind-up-ghost-thins: +153 px
- label: young_ghost.02.main-poses/04-side-hug: '04. SIDE HUG' -> '01. BOY AT WINDOW' (closer label (cost 58 vs 74))
- ref: young_ghost.02.main-poses/lights-young: label fragment (printed words)

### young_poet.02.action.pajamas_winter.parts
- split: young_poet.02.action.pajamas_winter.parts/props-c-hands-and-empty-wrist-separate-pieces-ha (985x488) -> 9 parts
- split: young_poet.02.action.pajamas_winter.parts/control-state-not-a-physical-part (519x513) -> 10 parts
- split: young_poet.02.action.pajamas_winter.parts/d-main-poses-assembled-reference-for-constructio (1505x211) -> 7 parts
- label: young_poet.02.action.pajamas_winter.parts/curtain: '(curtain)' -> 'HANDS (empty, attach at wrist)' (closer label (cost 45 vs 1000000000); old text is curtain-2's)
- label: young_poet.02.action.pajamas_winter.parts/state-not-a-physical: 'STATE (not a physical' -> 'hidden' (closer label (cost 29 vs 57); old text is state-not-a-physical-2's)
- label: young_poet.02.action.pajamas_winter.parts/pelvis-connector-thighs-waist-2: 'pelvis connector thighs) (waist 2' -> 'pelvis connector (waist 2 thighs) (threequarter back)' (closer label (cost 37 vs 1000000000); old text is pelvis-connector-thighs-waist-2-2's)
- label: young_poet.02.action.pajamas_winter.parts/pelvis-connector-waist-2-thighs: 'pelvis connector (waist 2 thighs)' -> 'torso (threequarter)' (closer label (cost 51 vs 1000000000); old text is pelvis-connector-thighs-waist-2-2's)
- label: young_poet.02.action.pajamas_winter.parts/seat-threequarter: 'seat (threequarter)' -> 'pelvis connector seat (threequarter) (waist 2 thighs)' (closer label (cost 34 vs 299); old text is torso-threequarter's)
- label: young_poet.02.action.pajamas_winter.parts/foot-l: 'foot.L' -> 'thigh.R' (closer label (cost 35 vs 1000000000))
- label: young_poet.02.action.pajamas_winter.parts/grip-curtain: 'grip (curtain)' -> 'HANDS (empty, attach at wrist)' (closer label (cost 45 vs 1000000000); old text is curtain-2's)
- label: young_poet.02.action.pajamas_winter.parts/state-not-a-physical-2: 'STATE (not a physical' -> 'CONTROL STATE (not physical part)' (re-read, more complete)
- ref: young_poet.02.action.pajamas_winter.parts/props-c-hands-and-empty-wrist-separate-pieces-ha: section box: its 9 contents are cut as separate parts
- ref: young_poet.02.action.pajamas_winter.parts/control-state-not-a-physical-part: section box: its 10 contents are cut as separate parts
- ref: young_poet.02.action.pajamas_winter.parts/d-main-poses-assembled-reference-for-constructio: section box: its 7 contents are cut as separate parts
- added: young_poet.02.action.pajamas_winter.parts/torso-back
- added: young_poet.02.action.pajamas_winter.parts/torso-threequarter
- added: young_poet.02.action.pajamas_winter.parts/torso-threequarter-back
- added: young_poet.02.action.pajamas_winter.parts/pelvis-connector-thighs-waist-2
- added: young_poet.02.action.pajamas_winter.parts/pelvis-connector-thighs-waist-2-2
- added: young_poet.02.action.pajamas_winter.parts/pelvis-connector-waist-2-thighs
- added: young_poet.02.action.pajamas_winter.parts/seat-threequarter-back
- added: young_poet.02.action.pajamas_winter.parts/seat-back
- added: young_poet.02.action.pajamas_winter.parts/seat-threequarter
- added: young_poet.02.action.pajamas_winter.parts/farm-r
- added: young_poet.02.action.pajamas_winter.parts/uarm-l
- added: young_poet.02.action.pajamas_winter.parts/uarm-r
- added: young_poet.02.action.pajamas_winter.parts/farm-l
- added: young_poet.02.action.pajamas_winter.parts/thigh-r
- added: young_poet.02.action.pajamas_winter.parts/thigh-l
- added: young_poet.02.action.pajamas_winter.parts/shin-r
- added: young_poet.02.action.pajamas_winter.parts/shin-l
- added: young_poet.02.action.pajamas_winter.parts/foot-l
- added: young_poet.02.action.pajamas_winter.parts/foot-r
- added: young_poet.02.action.pajamas_winter.parts/tambourine-2
- added: young_poet.02.action.pajamas_winter.parts/open-2
- added: young_poet.02.action.pajamas_winter.parts/curtain-3
- added: young_poet.02.action.pajamas_winter.parts/grip-tambourine-2
- added: young_poet.02.action.pajamas_winter.parts/grip-curtain
- added: young_poet.02.action.pajamas_winter.parts/blind
- added: young_poet.02.action.pajamas_winter.parts/state-not-a-physical-2

### young_poet.13.main-poses
- ref: young_poet.13.main-poses/awe-face-proof: label says 'PROOF'

### young_poet.child_clothes.body.back
- label: young_poet.child_clothes.body.back/03-forearm: '03 forearm' -> '02 upperarm L 03 forearm L 04 handL' (old text not on the sheet; label 31px-cost away)
- label: young_poet.child_clothes.body.back/08-l: '08 L' -> 'thigh L' (was empty/garbled)
- ref: young_poet.child_clothes.body.back/l-09: label fragment (printed words)

### young_poet.child_clothes.body.front
- label: young_poet.child_clothes.body.front/08-l: '08 L' -> 'thigh L' (was empty/garbled)
- label: young_poet.child_clothes.body.front/11-r: '11 R' -> '11 thighR' (was empty/garbled)
- label: young_poet.child_clothes.body.front/1-l: '1 L' -> '10 shoe L' (was empty/garbled)
- label: young_poet.child_clothes.body.front/shoe-r: 'shoe R' -> '13 shoe' (closer label (cost 13 vs 1000000000); old text is 1-l's)
- ref: young_poet.child_clothes.body.front/l-09-shinl: label fragment (printed words)
- ref: young_poet.child_clothes.body.front/r-12-shinr: label fragment (printed words)

### young_poet.child_clothes.body.threequarter
- label: young_poet.child_clothes.body.threequarter/04-l: '04 L' -> '04 handL' (was empty/garbled)
- label: young_poet.child_clothes.body.threequarter/10-l: '10 L' -> '10 shoe L' (was empty/garbled)
- label: young_poet.child_clothes.body.threequarter/13-r: '13 R' -> '13 shoeR' (was empty/garbled)
- ref: young_poet.child_clothes.body.threequarter/04-l-2: label fragment (printed words)

### young_poet.child_clothes.face.front
- label: young_poet.child_clothes.face.front/open-squint: 'open squint' -> 'head (blank)' (closer label (cost 5 vs 221); old text is squint's)
- label: young_poet.child_clothes.face.front/wide-2: 'wide' -> 'happy_arc' (closer label (cost 6 vs 54); old text is wide's)
- label: young_poet.child_clothes.face.front/knit-2: 'knit' -> 'grin_teeth' (old text not on the sheet; label 5px-cost away)
- label: young_poet.child_clothes.face.front/f-v: 'F_V' -> 'grin_teeth' (was empty/garbled)
- label: young_poet.child_clothes.face.front/open-o-2: 'open_O' -> 'grin_teeth' (closer label (cost 20 vs 237); old text is open-o's)
- label: young_poet.child_clothes.face.front/open-a-2: 'open_A' -> 'strain_teeth' (closer label (cost 2 vs 31); old text is open-a's)
- ref: young_poet.child_clothes.face.front/part-10: label fragment (printed words)
- ref: young_poet.child_clothes.face.front/part-11: label fragment (printed words)
- ref: young_poet.child_clothes.face.front/open-o-2: label fragment (printed words)

### young_poet.child_clothes.face.profile
- label: young_poet.child_clothes.face.profile/eye-squint: 'eye_squint' -> 'eye_squint eye_happy_arc' (re-read, more complete)
- label: young_poet.child_clothes.face.profile/eye-happy-arc: 'eye_happy_arc' -> 'eye_squint eye_happy_arc' (re-read, more complete)
- label: young_poet.child_clothes.face.profile/brow-knit-2: 'brow_knit' -> 'mouth_grin_teeth' (closer label (cost 10 vs 1000000000); old text is brow-rest's)
- label: young_poet.child_clothes.face.profile/brow-one-up-2: 'brow_one_up' -> 'mouth_open_A' (closer label (cost 7 vs 42); old text is brow-one-up's)
- label: young_poet.child_clothes.face.profile/mouth-open-o-2: 'mouth_open_O' -> 'mouth_ frown' (closer label (cost 11 vs 40); old text is mouth-open-o's)

### young_poet.child_clothes.feet
- label: young_poet.child_clothes.feet/poet-child: 'POET CHILD' -> '02 HEEL UP' (old text not on the sheet; label 23px-cost away)
- label: young_poet.child_clothes.feet/front: 'FRONT' -> '04 FRONT' (re-read, more complete)
- ref: young_poet.child_clothes.feet/part-7: label fragment (printed words)

### young_poet.child_clothes.hands
- split: young_poet.child_clothes.hands/poem13-young-poet-child-clothes-hands-right-hand (1638x906) -> 11 parts
- label: young_poet.child_clothes.hands/palm: 'palm' -> 'grip palm' (closer label (cost 40 vs 1000000000); old text is palm-7's)
- label: young_poet.child_clothes.hands/palm-2: 'palm' -> 'fist palm' (closer label (cost 43 vs 1000000000); old text is palm-7's)
- label: young_poet.child_clothes.hands/palm-3: 'palm' -> 'pinch palm' (closer label (cost 43 vs 498); old text is palm-7's)
- label: young_poet.child_clothes.hands/thumb-palm: 'thumb palm' -> 'thumb back' (closer label (cost 39 vs 60); old text is thumb-palm-2's)
- label: young_poet.child_clothes.hands/palm-4: 'palm' -> 'peace palm' (closer label (cost 26 vs 1000000000); old text is palm-7's)
- label: young_poet.child_clothes.hands/palm-5: 'palm' -> 'wave palm' (closer label (cost 28 vs 1000000000); old text is palm-7's)
- label: young_poet.child_clothes.hands/palm-6: 'palm' -> 'flat_push palm' (closer label (cost 30 vs 1000000000); old text is palm-7's)
- label: young_poet.child_clothes.hands/palm-7: 'palm' -> 'cup palm' (re-read, more complete)
- label: young_poet.child_clothes.hands/palm-8: 'palm' -> 'claw palm' (closer label (cost 48 vs 1000000000); old text is palm-7's)
- ref: young_poet.child_clothes.hands/poem13-young-poet-child-clothes-hands-right-hand: section box: its 11 contents are cut as separate parts
- added: young_poet.child_clothes.hands/part
- added: young_poet.child_clothes.hands/palm
- added: young_poet.child_clothes.hands/palm-2
- added: young_poet.child_clothes.hands/palm-3
- added: young_poet.child_clothes.hands/thumb-palm
- added: young_poet.child_clothes.hands/palm-4
- added: young_poet.child_clothes.hands/palm-5
- added: young_poet.child_clothes.hands/palm-6
- added: young_poet.child_clothes.hands/palm-7
- added: young_poet.child_clothes.hands/thumb-palm-2
- added: young_poet.child_clothes.hands/palm-8

### young_poet.pajamas_winter.compact-core
- label: young_poet.pajamas_winter.compact-core/shin: 'shin' -> '12 shinR' (closer label (cost 14 vs 1000000000); old text is shinl's)

