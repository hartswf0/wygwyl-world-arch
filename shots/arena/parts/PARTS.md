# Parts: one contract, any source, connection points that are never guessed

The arena was assembled from generated cards whose connection points were
**hallucinated twice**: once by the generator, which draws brads where it likes,
and again by us, typing pivots as fractions of a bounding box. Every card was
then pinned to the skeleton on its own, with nothing making it meet its
neighbour. See `../critic/out/cards_man.png`: the compiler's pins miss the drawn
brads by 18–95px on every drawn card, and the torso and head pins were written
for files that have since been replaced.

This folder replaces guessing with a contract.

## The contract

Every part is a file plus a record in `library.json`:

| field | meaning |
| :-- | :-- |
| `id` | `kit.hand.R.back.fist`, `man.head.ie.surprised`, `man.torso.profile.traced` |
| `kind` | head, torso, pelvis, uarm, farm, hand, thigh, shin, boot |
| `view` `side` `shows` `state` | what it is, so it can be picked and swapped: profile/front/threequarter_R, L/R, palm/back, `{shape, grip}`, `{roll}`, `{expression}` |
| `source` | `code` drawn by `kit/` from its joints · `image` a generated card · `traced` code shapes cut to an image card's outline |
| `file` (+ `svg`) | the picture; code parts also ship a resolution-free SVG |
| `sockets` | `{A, B, …}` in file px. **Axis rule: A at the pivot, B straight down.** |
| `socket_source` | `constructed` (code: exact by construction) or `registered` (image: placed by a person on a grid, checked by the critic). There is no third value. |

`registered.json` holds every image part's sockets, with the file size they were
placed on. If the file changes, the library **refuses** the part until someone
re-registers it. Nothing is allowed to quietly drift the way `torso.profile.png` did.

The assembler only ever calls `library.pick(kind, view=, side=, shows=, shape=, expression=)`.
It gets back a part with sockets it can trust, plus the list of keys it could not
match. That list goes straight into the critic's report as **"library missing"**.

## Three sources, and when to use each

**Code (`kit/`)** is for anything that has to bend, swap or match exactly:
hands, feet, pelvis, limbs.
- `kit/hand.py` uses the Crash Lab's own hand parameters (`gloveDraw`: shape, grip
  0–1, palm facing, side). It draws four three-segment fingers and a two-segment
  thumb. Curl foreshortens each segment, so a fist falls out of the geometry.
- Handedness is drawn, never mirrored. With the fingers down, a right hand
  showing its palm has its thumb on −x.
- The library holds 10 shapes × L/R × palm/back = 40 hands:
  flat, open, relaxed, point, fist, thumb, pinch, peace, grip and cup.
- `kit/body.py` has:
  - **limbs** with round ends centred on their joints, so a bend never opens a gap;
  - a **profile pelvis** with a seat;
  - a **front pelvis** with two hip sockets;
  - a **chelsea boot** with a real last, sole, heel, gusset and pull tab, plus a
    `roll` that lifts the heel about the ball;
  - a **front boot**.

**Image** is for likeness and acting: heads and anything a generator does better
than code.
- Its sockets are registered by eye. Don't read them by colour: on the heads the
  brad reader was off by up to 30px and missed two of twelve neck brads.

**Traced (`trace.py`)** is a code rotoscope.
- It takes a generated card's silhouette, light panels and piping, and refills
  them in the kit's palette.
- The result is a code part with the card's cut, and it carries the card's
  registered sockets.
- `--mode colours` traces every quantised colour instead. It is kept to show why
  that isn't the default: the fluting turns to speckle and the piping is lost.

Swapping is one argument. `assemble_kit.assemble(..., prefer={'torso': 'traced'})`
swaps the image vest for the traced one with the same sockets. See
`../critic/out/ACT-010/swap_torso.png`.

## Expression parity with Bolas

The Crash Lab's characters act with their hands and faces. The bank carries both
per frame (`bolas/export_bank.mjs`, re-baked 2026-10-20 from `lab/crash-lab`).
The compiler dropped them.

| Bolas field | was | now |
| :-- | :-- | :-- |
| `hand.shape`, `grip`, `palm`, side | 4 cards, no side, palm always toward camera | 40 code hands picked per frame by shape × side × palm/back |
| `face.mouth/eyes/brow/lid/smile/open`, `effort` | one sunglasses head per view | 12 expression heads cut from `heads_intent_effort.jpg` and picked by `face_to_expression()`; the critic reports every frame whose face no head can show |
| props with `size` and `held` | every box is an 80×70px square with its bottom at the box's centre | the real cuboid projected through the clip's camera, drawn in front of the torso when held |
| heel/ball/toe joints | boot angle from the compiler | foot angle from the bank's own heel and toe |

Still missing:
- Brows, lids and mouths as separate replaceable pieces. Today the whole head is
  swapped.
- Profile expression heads. The cut bank is 3/4.
- Gaze (`gx`, `gy`).
- Wrist bend (`bend`).

## What else in the repos can be chopped

From the inventory (2026-10-20). Cut with `cut_sheet.py`, then register by eye:

| sheet | holds | why it matters |
| :-- | :-- | :-- |
| `weave/cast/man/sheets/hands_2.jpg` | 15 hands, several as true L/R pairs (front hanging, curled, back of hand) | image hands with real handedness, to set beside the code hands |
| `…/arms_hands_contact.jpg` | bar grips, edge hook, catch, box lift, hand on shoulder, clasped hands | contact shapes the code hand doesn't do yet |
| `…/heads_front.jpg` | 12 front expressions, including speaking and singing visemes | front-view acting and lip sync |
| `…/heads_effort_threequarter.jpg` | 12 more effort and intent heads | a second 3/4 bank |
| `…/legs_segmented.jpg`, `legs_run_stairs.jpg` | thighs, shins and boots, several fused in pairs | reference for the kit's proportions; cut the single pieces |
| `…/props.jpg`, `set_props.jpg` | door, railing, stairs, balls, cups, phone | props with real sizes, replacing the compiler's rectangles |
| `arena/cast/dummy/` | bola, shim and dot, 40 cut parts each with pivots (`parts.json`) | a second cast, so Shim stops being a copy of the man |

Boone's *This Side Up* parts and pivots are not in either repo; only the JPG
review sheets are (`bolas/this-side-up/media/case/*`). They were made in a
session folder that no longer exists.

## Commands

    python3 shots/arena/parts/library.py                 # build lib/, library.json, sheet.png
    python3 shots/arena/parts/cut_sheet.py <sheet> <dir> a,b,c
    python3 shots/arena/parts/trace.py man.torso.profile
    python3 shots/arena/critic/loop.py ACT-010           # rig | brad | kit, side by side
