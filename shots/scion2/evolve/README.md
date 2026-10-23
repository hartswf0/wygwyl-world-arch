# evolve: puppets evolved from the card library

Every candidate here is made only of **library cards**. No pixel of a candidate comes from the
painting it is compared with. Each pose's Pose Lab markers are the skeleton the candidate must
match. The painting is the reference: the fitness reads its shape, and the copy check reads its
pixels.

Run from `shots/scion2/` with python3, numpy, OpenCV and Pillow:

    python3 -m evolve.evolve kill                     # the 4 kill-experiment poses, 2 processes
    python3 -m evolve.evolve one poet red_black_sunglasses poet.13.main-poses/06-refocus
    python3 -m evolve.sheet evolve/kill/candidates.json   # remake the sheets from saved genomes

Outputs go to `evolve/kill/`:
- `<pose>.jpg`: the review sheet for each pose.
- `candidates.json`: for each pose, the 6 genomes and their scores, the card per part, the pool
  sizes, every excluded card with the reason it was excluded, and the best and median score per
  generation.
- `log_*.txt`: the run logs.

## Files
| file | what |
|---|---|
| `library.py` | Merges `library.json`, the `labels.json` overlays, the poet contract's `fix` fields (A/B, px/cm, erase, trim) and `library_harvest.json`. Applies the **hard filter** per target (below). |
| `cards.py` | Prepares each card: the pixels (erase and trim applied), the painted paper-border width, the anchors, the cloth width at both joint ends, the median Lab colour, skin share, and the eye-band darkness of heads. |
| `assemble.py` | Turns a genome into placed cards on the target markers. Also the fast rigid render used for fitness, and the full render used for sheets (mesh bend, edge, brads). |
| `fitness.py` | The fitness terms. |
| `evolve.py` | Pool filters, the genetic algorithm, final polish, and the top 6 distinct candidates. |
| `sheet.py` | The review sheet (layout and labels after `rigkit/sheets.py`, copied, not imported). |

## Hard filter: nothing from the target painting
A card leaves the pool when any of these is true:
- It is a harvest card whose `source` is the target painting.
- Its id is the target painting, or any painting with markers. Some whole paintings are filed in
  the library as hands or feet.
- It is a kit card on the target's own sheet whose box on the sheet (`sheet.json` bbox) touches
  the target painting's box.
- The sheet marks it `ref` or `pose`, meaning an assembled figure and not a part. Heads are the
  exception.

Two further rules apply:
- Cards flagged `bad` (harvest checks, `labels.json`) are dropped.
- The brad sprite is cut from a kit torso card (`assemble.BRAD_CARD`). It is not rigkit's EX brad
  source, which is the EX target painting.

`candidates.json` lists every exclusion with its reason.

## Usability filters (evolve.usable)
These cards are junk for their slot and are dropped:
- dissolve and haze effect states;
- blank kit heads (no dark pixels in the eye band, `blank` or `plate` in the id, or the three
  blank `heads/*` cards);
- "hands" that are whole figures, eye strips or faces;
- cloth cards carrying a hand or head;
- white, unpainted "reserve" cards (poet only);
- pocket patches filed as torsos.

## Anchors
- **Limbs, hands, feet, heads.** The library's A (proximal joint) and B (distal joint) are kept
  when both points lie on or next to the paint and span at least 45% of the card. A hand's A must
  also sit in the wrist quarter, on the end with the tan tab or brass eyelet.
  - Otherwise the anchors are re-read from the alpha's principal axis.
- **Torso.** The neck (collar top) and waist (hem centre) always come from the alpha. Many torso
  cards carry the two shoulder brads as A/B. The torso is scaled so that neck to hem is 50 card-cm.
- **Pelvis.** The waist is the top centre. The hips are the two lowest brads, which are placed
  26 cm apart.
- **Kit hands and boots.** These are sized from their drawing: a hand is 19 cm from wrist to tip,
  a profile boot is 26 cm long and a front boot is 11 cm wide. Contract `px_per_cm` fixes win.
  Harvest cards keep their painting's px/cm.

## Genome
- `view` is front, threequarter or side for a front-facing target. For a back target it is back
  or threequarter_back.
- Each of the 15 slots has one card id (`pelvis` may be `none`) and these parameters:
  - `k`: scale, 0.9 to 1.1 of canon.
  - `rot`: trim of ±10°. Hands, heads and feet get ±30°.
  - `mir`: mirror across the card's own axis. It starts as true when a card's L/R side is the
    other side.
- Feet are flipped so the toe points the way the toe marker does. Heads face the way the chin
  does. These two are not evolved.

## Placement (forward kinematics on the markers)
- **Torso.** The neck sits at the neck marker, and the torso is aimed at the mid-hip.
- **Head.** The head sits on the neck marker, aimed 60% along the spine and 40% toward the head
  marker.
- **Pelvis.** The pelvis sits on the spine, 25% above the mid-hip.
- **Arms.** The upper arm runs from the shoulder marker toward the elbow marker. The forearm
  starts where the upper arm actually ended, aimed at the wrist marker. The hand continues the
  forearm.
- **Legs.** The leg is built the same way, from the hip marker to the knee and then the ankle.
  The foot is drawn upright, as painted.
- **Stretch.** A part may stretch along its own axis by at most ±12%. Whatever remains shows up
  as joint error, so it is not hidden.
- **Scale.** The target scale, in px per card-cm, comes from the least foreshortened arm and leg
  bones measured against the library's normalised lengths (30.4, 26.7, 46 and 42.8 cm).

## Rendering (full, for sheets)
- **Bend.** Each arm and leg card is a triangle mesh bent inside the part near its joints, using
  the method of rigkit `core.py`. The thigh end turns halfway toward the shin and the shin top
  halfway back, so the two read as one trouser leg bending at the knee.
- **Overlap fade.** The cap of a card drawn over its parent (shin over thigh, forearm over upper
  arm) fades into the parent's cloth above the joint.
- **Edge.** The painted paper border is stripped, and one crisp edge is drawn back in rigkit's
  brown line and tan hairline:
  - none at a joint whose neighbour is drawn later;
  - only over empty paper at a joint whose neighbour is already drawn.
- **Brads.** One clean brad is drawn at each shoulder, elbow, wrist, hip, knee and ankle.
- **Order, back to front.**
  - Hips, then legs (foot under shin, shin over thigh), then the head under the torso, then the
    torso (jacket hem over the trousers), then the arms (hand under the cuff).
  - In a turned view, the far arm and far leg go behind.

## Fitness (lower is better; all are proxies)
`total = joint/4 + 2·sil + coh + integ + 2·copy`

| term | what it measures | what it does not |
|---|---|---|
| joint | Mean cm from where the candidate's elbows, wrists, knees, ankles and toes (half weight) landed to the markers. Shoulders, hips and neck are pinned. | Looks; whether the cards are the right drawings. |
| sil | 1 − IoU with the painting's alpha. | Interior detail. A painting's sleeve folds or a big painted head count only as shape. |
| coh | Colour ΔE/10 between neighbouring and twin parts; +0.15 per extra kit family among the cloth cards; +0.5 when the two hands or the two boots come from different families; view mismatch per card (a back of head on a front body costs ×3); spread of scale genes; +0.1 per harvest card; +0.3 for another costume's head. | Style differences that ΔE misses, such as finish, line weight, sunglasses on or off, or expression. |
| integ | 2× width step at elbows and knees (cloth width at each card's joint end); 0.3× shoulder and hip gap in cm beyond half the root width; 2× stretch wanted beyond 12%. | Gaps at the wrists and ankles, which are closed by construction. |
| copy | For each placed card, the grey normalised cross-correlation with the painting under it. Any excess over 0.6 is added. | Excluded cards are already gone, so this only catches a kit card that is the same drawing. |

## Evolution
- **Islands.** The population is 56 genomes, split into 7 islands of 8, over 30 generations.
  - Each island has a home kit family. The character's own body sheets (front, 3/4, profile,
    back) come first, then the action-part sheets that can dress most of the body; the last island
    has no home family.
  - An island's genomes start in its home sheet's view. Each slot takes from the home sheet 60% of
    the time when the view fits, and otherwise draws by view fit, with harvest cards at half weight.
  - There is no migration between islands, so they stay distinct card sets.
  - The poet contract assembly (one genome per view) seeds island 0.
- **Selection.** Each island uses a tournament of 3 and elitism of 2. A child that repeats a card
  set already in the next generation is rejected 80% of the time.
- **Operators.** Crossover swaps whole chains (arm L, arm R, leg L, leg R, head, torso and
  pelvis). Mutation swaps one card (half the time from the home or neighbour family), nudges `k`
  or `rot`, or toggles a mirror.
- **Output.** The 6 returned are the best of each island first, then the archive of every
  genome scored, each differing from every other pick in at least 4 of 9 slot groups. The groups
  are torso, hips, head and the six L/R pairs; swapping a pair's L and R cards does not count as
  new. Each pick then gets a short coordinate descent on `k` and `rot`, which does not change its
  cards.
- **Head and boots.** The view these must show comes from the target:
  - the head is profile when the chin sits far from the neck, back for a back view, otherwise
    3/4 or front;
  - a boot is side-on when the toe marker lies sideways from the ankle.
