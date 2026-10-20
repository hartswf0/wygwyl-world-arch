# The Acting Arena: what is wrong with it, measured

A handover. Everything below was measured, not estimated, and every number can
be re-derived from the scripts named beside it. Written so the next person —
or the next model — does not repeat the four days it took to find them.

The single most useful thing in this document is the pattern at the bottom:
**a tidy statistic about a useless result**. It happened four times, to me, in
one session, and it is the failure mode to watch for here.

---

## 1. What is actually fixed

| | before | after | by |
| :-- | --: | --: | :-- |
| verdict | `'pass' if drift<=0.6 else 'pass'` | reads the tolerances | `compile_vignette.py` |
| beats | `frame 0, frame 24, frame 48` | 2,508 named beats | `mark_beats()` + `bolas/bank/beats.json` |
| thigh card | 29.3cm for a 44.0cm bone, stretched 1.50× on 11,409 frames | 234px, stretch 1.00 | `tube.py` |
| poet's leg | one card, knee to sole, no ankle | shin + boot, each on a bone | cut at the card's own waist, y=216 of 310 |
| per-frame flags | 62,500 | 173 | — |

Of the ~62,000 flags that went, about 23,200 were genuinely fixed and about
6,890 were **re-labelled** from per-frame defects to per-clip `cast_limitations`.
That distinction matters and is easy to lose: a low flag count means the checks
you have are satisfied, which is a different claim from the thing being right.

---

## 2. What is still broken

### The body has no side view
`torso.profile` and `torso.front` are the same picture — **IoU 0.973**, both
220px wide, where a real side torso is about 60% of the front's width. `pelvis`
the same at 0.983. `head.back` is `head.front` at 0.964. `head.profile_L` is
`head.threequarter_L` at 0.917.

Of six head "views" about three are distinct; the torso and the pelvis have one
each under two names. **The renderer draws the fake profile 7,484 times — more
often than the front** — so the majority of the arena is a man facing the camera
with a profile head on. 84 clips, 22,491 frames.

Caught by `pieces_accept.py --library`, which compares every pair of cards in a
piece group. Nothing caught it for months because every other check judged cards
one at a time, and a perfect copy of its neighbour passes all of them.

### The hands have no handedness and no facing
Four shapes, one card each. The same palm faces camera whether the arm reaches
toward it or away. 1,787 frames want a grip or a fist that does not exist.

### The skirt is one rigid card
780 frames put her knees through it.

### The cards were never cut to one body
Pinned on the thigh — the only piece that fits — every other card is out, and
each by a different amount and in a different direction:

    shin +34%   forearm +68%   torso +60%   upper arm +79%   boot +74%   head +84%

A scale error is uniform. Six different errors mean six independent drawings.

---

## 3. Dead ends, and why they are dead

**Four-box decompile** (`pose_decompiler.py`). Cuts fractional rectangles that
share **35–110%** of their own area with their neighbours — the man's torso box
overlaps its neighbours by more than its whole area. That is the duplicate limb
on screen. Better segmentation moves this problem; it does not remove it.

**Capsule-per-bone.** 92.2% overlap. A capsule wide enough to hold a thigh also
holds most of the torso.

**Nearest-bone partition.** 0.0% overlap, 99% coverage — and still wrong,
because a partition cannot represent occlusion. A forearm crossing the chest
takes a bite out of the torso. Use TSU-01's ordered claiming instead: hands,
forearms, upper arms, head, and whatever is left is the body.

**Brass-brad colour detection.** Across twelve study sheets, **99.94%** of all
saturated pixels are red or orange — skin, cardboard, salmon piping and brass
are one population. Found 3 joints of 12 on the 1024px renders, 0 on
`slip_recover_f50`. It works for Boone in *This Side Up* because he is a
physical puppet photographed under a light: real metal, specular, not the colour
of card.

**Medial axis / morphological skeleton.** 131 branch points and 62 endpoints on
a figure with five extremities. Needs proper Zhang–Suen thinning and pruning to
be worth anything, which is more work than the thing that already works.

**Fitting the known skeleton by bounding box.** Silhouette IoU 0.517, 15 of 26
joints landing inside the figure, and 1 of 10 pieces usable. A uniform scale
cannot absorb the difference between a drawn body's proportions and the
skeleton's — which is the same mismatch as the 29cm thigh.

**Guessing the frame by silhouette IoU.** Picks frame 64 for a panel captioned
`#f95`. A stick figure will never match a clothed silhouette well enough.

**Reinforcement learning.** Wrong tool. This is keypoint localisation with
abundant free labels — the Bolas bank can render any pose with known joints —
which is supervised learning. RL would be slower, less stable and worse.

---

## 4. What works: read the joints, do not infer them

`usyd-community/vitpose-base-simple`, off the shelf, no training:

    heavy_box_f95     17/17 keypoints over 0.5 confidence
    slip_recover_f50  17/17
    ledge_hang_f110   17/17
    man_crouch_f72    15/17

It is trained on photographs of people and the cast is a flat cardboard cut-out,
so it should be out of distribution. It is not. See `vitpose_check.jpg` — four
drawings with the detected skeleton drawn over them.

Cutting on those joints rather than a fitted skeleton:

    joints inside the figure   15 of 26  ->  22 of 23
    usable pieces              1 of 10   ->  6 of 10

**The constraint is resolution, not drawing style.** On a 144px harvested panel
the same model drops to 11 of 17 and puts the ankles at 0.13. Cut from the full
renders, and generate larger.

Still missing from COCO's 17: toe and ball, a separate thigh top, and **which
frame a drawing is of** — nothing about pose estimation tells you that. The
frame code from *This Side Up* TSU-02 is still worth asking the generation for.

---

## 5. Common sense is a check nobody wrote

Several of these would have been caught by asserting what a body obviously is,
and the assertions are cheap:

- a torso has more area than an upper arm (it did not, for three attempts)
- a shin and a thigh are within ~10% of each other (the cards were 31% apart)
- a profile torso is narrower than a front torso (it was identical)
- left and right limbs are within ~15% of each other
- a piece labelled `boot` touches the lowest point of the figure (one was the
  cardboard box)
- a card's long axis runs along its bone (arms, hands and boots were drawn
  horizontally — 86°, 89°, 64° off)

`pieces_accept.py` holds aspect, single-component, upright, ends-have-ink and
view-distinctness. The anatomical ratios above are not in it yet and should be.

---

## 6. The pattern to watch for

Four times in one session I produced a clean number about a worthless result:

1. `result: 'pass'` on 96 clips, because both branches of the ternary returned
   `'pass'`.
2. `0cm brad gap` written as a string literal on frames where the measurement is
   explicitly skipped.
3. `0.0% overlap` from a nearest-bone partition whose pieces were a sliver of
   torso and a corner of a cardboard box.
4. `173 flags` reported as near-clean, while the largest fault in the arena —
   22,491 frames of a front body turned sideways — had no check at all.

In every case the number was true. In every case it was answering a question
nobody should have asked. **Before trusting a metric here, look at the thing.**

---

## 7. Where everything is

    bolas/bank/*.json       the motion: 191 vignettes, joints in cm, 24fps
    bolas/bank/beats.json   the authored beats, keyed by T-id
    bolas/compile_vignette.py  the renderer — two people edit this, coordinate
    clips/ACT-NNN__*.json   96 compiled clips, arena_version v2
    pieces.json             9 pieces, lengths measured from the skeleton
    pieces_brief.json       one generation brief per card
    pieces_accept.py        the gate: run it before placing anything
    butcher.py              SAM for the silhouette, ViTPose for the joints
    harvest.py              83 bodies split from the study sheets, 60 usable
    bodies/quality.json     which of them are usable, and why the rest are not
    REGISTRATION.md         the magenta-marker and frame-code spec
    gen_pack/               briefs, style references, 32 pose sheets
    ../acts/                one page per act
    ../arena-compare.html   Bolas / cards / generated, same frame, side by side
