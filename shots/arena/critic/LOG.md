# Critic log

One line per turn: what was seen, in which file, what changed, and whether the
next picture confirmed it. **Clean** means the numbers were clean; it does not
mean the picture was right. The cases where those two disagreed are marked ⚠.

## 2026-10-20: the rig as compiled (ACT-010, ACT-003, ACT-007, ACT-016)

| # | seen | where | cause | layer |
| --: | :-- | :-- | :-- | :-- |
| 1 | the pins miss the drawn brads by 18–95px; torso and head pins were written for older files | `out/cards_man.png` | pivots typed as box fractions, never re-checked when the cards were regenerated | compiler |
| 2 | the shorts card hangs at 0° while the body bends; its leg brads are 35–40cm from the thighs | `out/ACT-010/f80_rig_loupes.png` | the pelvis never rotates, and its sockets are unused | compiler |
| 3 | boots 65–100px below the floor on every frame | `report.md` | no contact with the floor | compiler |
| 4 | ⚠ elbows and knees "0.1cm": perfect because those cards are blank tubes with brads stamped on the compiler's own pins | loupes | the number is true and says nothing about the look | — |
| 5 | the 100cm box is an 18cm square, its bottom at the box's centre, never in the hands | `compile_vignette.py:488`, `f146` | the prop's size and holder are ignored | compiler |
| 6 | f70 "casual bend" and f80 "tug: nothing moves" look identical | `keys_rig.png` | the bank's face (`O`, open .7, effort .8) is dropped; the head has one expression and sunglasses | compiler + parts |
| 7 | the clip's `cm_px` is 2.35; the drawing is 4.4 px/cm | `frame.px_per_cm` | a constant, 400/170 | compiler |
| 8 | ACT-016: Shim is a second copy of the man | `keys_rig.png` | one skin for the whole cast | cast |
| 9 | ACT-003 f72: a whole-pose picture replaces the rig | `report.md` | pose swap | compiler |

## 2026-10-20: brad assembly (re-pin on the drawn brads)

| turn | seen | fix | confirmed |
| --: | :-- | :-- | :-- |
| 1 | ⚠ clean numbers, but he stands on his toes in every frame | keep the compiler's boot rotation, re-pin only | yes, `keys_brad.png`; the numbers did not move |
| 2 | ACT-016: fists as big as heads | scale hands by their drawn extent (the fist card is half a hand) | yes, `board_f40.png` |
| 3 | the card sheet shows the brad reader marking skin as brass on faces | tried tighter thresholds; they lose the real brads too | **no**: the reader has a ceiling, so sockets for image parts are now registered by eye |

## 2026-10-20: the part library (`parts/`)

| turn | seen | fix | confirmed |
| --: | :-- | :-- | :-- |
| 1 | code hands: "thumb" points sideways, the "pinch" thumb misses the index | thumb back past the wrist; pinch aims at the index tip | `parts/sheet.png` |
| 2 | the code boot is a wedge with a 2cm toe box, and roll lifts the toe | redrawn on a real last; roll about the ball, heel up | `parts/sheet.png` |
| 3 | kit: planted boots point toes-down | foot angle from the bank's heel and toe joints | `keys_kit.png` |
| 4 | kit: the turn is invisible, because the face can't act | cut 12 expression heads from `heads_intent_effort.jpg`, registered by eye, picked from the bank's face | `keys_kit.png`: listening → **surprised** at the tug → set → **strain** on the lift |
| 5 | the pelvis seat sticks out behind the vest like a bustle; heads a little small | seat brought in to x=−8.9; head 27cm | `board_f80.png` |
| 6 | colour tracing buries the card under its rim colour, then turns it to speckle | paint largest region first; then default to outline + piping in the kit palette; then ignore the light rim | `trace.py` outline mode; `swap_torso.png` |

## Cold read, ACT-010, `keys_kit.png` (by this session, which knows the challenge: not a fresh reader)

> A man walks up to a tall box and bends to it casually. He pulls, and his face
> goes slack with surprise. He drops into a squat with a set jaw, lifts with his
> teeth bared, and carries it, still straining.

The situation sentence is "reach for a box, fail to lift, regrip and lift with
effort". This reading recovers it, including the turn. **It needs a fresh reader
to count**: run it with someone who has not seen the challenge.

## Open, routed

- **ACT-016 motion:** the strike is a fist raised beside the striker's own head
  (bank). It goes to the Crash Lab vignette.
- **Cast:** Shim needs his own skin. `arena/cast/dummy/shim.*` exists with pivots.
- **Faces:** the expression heads are 3/4 on a profile body (one step apart;
  allowed by Gate G, but it shows). The fix is profile expression heads, or
  separate brow/lid/mouth pieces.
- **Proportions:** the Bolas skeleton has long legs and arms against a 27cm head.
  This needs a decision on the cartoon canon, not a fix in the assembler.

## 2026-10-21: drawn from 3D (`puppet/`)

The user's critique: the boots don't flex, the hands face the wrong way,
proportions are off against the main sheet, the side views are broken, and it
should be steerable in any direction. All five share one cause: flat cards stand
in for a body that moves in 3D. `puppet/p3d.py` draws the man from the bank's 3D
joints, the way the Crash Lab draws its dummy, and paints him as the main sheet.

| turn | seen | fix | confirmed |
| --: | :-- | :-- | :-- |
| 1 | first render: chunky and right-sized, but the boots are bricks and the heads have a white halo | rounded rings for the boots; defringe in `cut_sheet.py`, heads re-cut | `puppet/out/ACT-010/keys.png` |
| 2 | palms are round discs (mittens) | palm longer than wide; fingers set at the knuckle line | `closeups_f22.png` |
| 3 | from behind, the shorts are one trapezoid (a skirt) | each leg takes only its own half of the waist and seat | `closeups_f22.png` (crotch notch) |
| 3 | hands: do they face true? | measured, not eyeballed: palms in → palm toward the midline 0.79, thumb forward 0.97, both sides | numbers in `puppet/README.md` |
| 4 | at the strain beats the carried box covers his face; the joint test said "none" | measure on the drawn head's pixels instead | flags f146/219/239 on the vignette camera, none at yaw +30 |
