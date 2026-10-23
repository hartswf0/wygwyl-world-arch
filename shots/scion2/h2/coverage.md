# H2 coverage map: what the 130 paintings can and can't play

Source: my own hand reading of all 130 `shots/kits/cut/poet.*.main-poses/*.webp` (`tools/catalog_src.py`). For each painting I recorded costume, whether it is a whole usable figure, view, posture, hands, gaze and props. Picture map: `coverage.jpg` (posture x view, a thumbnail of every usable suited painting, pink = nothing). Counts: `coverage.json`. Regenerate with `python3 tools/coverage.py`.

## What the 130 are

| | count |
|---|---|
| whole, usable poet figures | **62** (50 in the red/black suit, 12 in the black t-shirt of poems 01–03) |
| cut by a straight edge (half figures, the bike sheets, 13/part-2, 09/phone-palm) | 20 |
| fragments (a boot, a hand, a line, a phone cord) | 18 |
| empty alpha (the cut produced nothing) | 13 |
| the ex (olive bomber, jeans, white sneakers), not the poet | 9 + 1 ghosted + 1 triple |
| sheet text painted into the cut ("04 RIDE LOW", "OPEN", "04 TERRACE OPEN PALMS", ...) | 5 |
| two figures in one cut (06/brace-04-unclench) | 1 |

So the replacement library for the suited poet holds **50 drawings**: 43 in the plain suit and 7 from poet.04, whose suit has a glowing chest disc or ring that the others don't. The t-shirt paintings are a different costume, and H2 never mixes them into a suited shot.

Style differs across families inside the suit as well. poet.12 has a thick tan outline and a bigger painted head. poet.04 is bulkier with a bigger head. poet.13/06 and 13/07 have the sunglasses off. A cut between families shows these differences (see the move).

## Suit: posture x view (usable whole paintings)

| posture | front | 3/4 to screen-right | 3/4 to screen-left | profile R | profile L | back / back-3/4 | total |
|---|---|---|---|---|---|---|---|
| stand | 18 | 6 | **0** | **0** | **0** | **0** | 24 |
| walk | 3 | 4 | **0** | 1 | **0** | **0** | 8 |
| lunge | **0** | 3 | **0** | **0** | **0** | **0** | 3 |
| dance | **0** | 1 | **0** | **0** | **0** | **0** | 1 |
| lean / stoop | **0** | 2 | **0** | **0** | **0** | **0** | 2 |
| crouch | 1 | 3 | **0** | **0** | **0** | **0** | 4 |
| kneel | **0** | 3 | **0** | **0** | **0** | **0** | 3 |
| sit | **0** | 2 | **0** | **0** | **0** | 1 | 3 |
| lie | **0** | **0** | **0** | **0** | 2 | **0** | 2 |
| fall | **0** | **0** | **0** | **0** | **0** | **0** | 0 |
| ride | **0** | **0** | **0** | **0** | **0** | **0** | 0 (all bike paintings are cut or labelled) |

Mirroring turns every "screen-right" cell into "screen-left". The suit, zip, stripes and brads are symmetric enough for that (the chest disc is centred), so the empty screen-left column is not a real hole. Mirroring does flip the light and any held prop.

T-shirt (poems 01–03), 12 usable: 1 stand, 4 walk (one from behind), 1 lunge, 1 lean, 1 sit on a bed, 1 reclining, 3 falls. These are the only falls and the only poet back view in the set.

## Well covered (replacement can play these now)
- **Front stand with the arms in many places**: 18 drawings. Arms low and open (05/ask-the-universe-2, 11/02-front-guide-stone, 07/chin-up-open-arms), arms wide at shoulder height (07/push-two-sides-apart), arms up (11/welcome-new-day, 06/arms-up-05, 12/02 fists), head back (08/04, 08/05), holding things (book, star, cup-star). Palms-up and head-thrown-back were reached from other families at D ≈ 0.5.
- **3/4 to screen-right standing and walking**: pointing, mic, daisy, suitcase walk, reading walk, bike approach.
- **3/4 lunges and reaches**: 12/01, 08/07, 09/falter.

## Thin (one or two drawings, often with a prop stuck to them)
- **Sitting**: 11/pool-edge (stone block and book), 13/02-cafe (cup, no seat painted) and 08/o06 (on a ledge, seen from behind). There is no frontal sit, no profile sit, no sit with empty hands and no sit on the floor.
- **Kneeling**: 04/04-2 x2 (both poet.04, with the disc) and 13/04 (with flowers). Nothing outside poet.04 kneels upright.
- **Crouch**: one frontal squat (04/04-4-empty-cuffs, with no hands), plus 3/4 crouches with a letter, a bike, or empty cuffs.
- **Lying**: 2, both poet.05, both head to screen-left. Nothing on the front, nothing curled up.
- **Dance**: 1 (08/03).
- **Hands**: fists only twice (12/02, 08/03). Hands in pockets only in poet.04. Hand at the head only in 13/06 (glasses off). Hands without sleeves-and-hands ("empty cuffs") in poet.04.
- **Gaze**: "up" 5 times and "head back" twice. Most suited paintings look forward or toward screen right.

## Holes (zero drawings)
- **The suited poet from behind, in any posture.** Every back view in the 130 is the ex or the t-shirt poet. (`poet.14.exit/1-stand` and `3-walk-reach-to` are suited rear figures outside the 130 main-poses; H2 did not use or score them.)
- **Profile standing or turning** (only one profile walk), and any turn between views: there is no front-to-3/4 pair of the same pose.
- **Falls, stumbles, jumps, running** in the suit.
- **Riding**: every bike painting is cut by a straight edge or carries sheet text.
- **Seated profile, frontal sit, floor sit.**
- **Upright kneel outside poet.04**, and any frontal kneel.

## What this means for H2
Replacement plays whatever the library holds, and plays it at full painting quality. It can't reach anything outside that list. The 12-pose test splits into 2 covered, 6 approximate and 4 gaps (`out/picks.json`). The gaps are exactly the thin and empty cells above: crouch, kneel, seated profile, lying. `gaps.json` turns each into a painting brief.
