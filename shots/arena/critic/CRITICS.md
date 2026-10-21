# The critic loop

One turn: **render → measure on the pixels → look → name the single worst thing →
fix its cause → re-render → compare.** The numbers point at a crop. They never
pass anything on their own; three times in the first session they read clean
while the picture was wrong (`LOG.md`).

    python3 shots/arena/critic/cards.py                  # the cards, with every pin drawn on them
    python3 shots/arena/critic/loop.py ACT-010           # one turn on a take's authored beats

`loop.py` writes `out/<ACT>/`:

| file | look at it for |
| :-- | :-- |
| `board_f<N>.png` | one beat assembled three ways (`rig` as compiled, `brad` re-pinned on drawn brads, `kit` from the parts library), plain and in silhouette |
| `keys_<variant>.png` | authored-beat frames only, no captions: **the cold read** |
| `f<N>_<v>_loupes.png` | every joint close up, with its gap |
| `f<N>_<v>_overlay.png` | parent socket (cyan), child socket (magenta), red where they part |
| `report.md` | open joints, boots versus floor, head/figure ratio, stretched cards, view mismatch; for `kit`, what Bolas asked for against what the parts showed |

Measurements are taken from the rendered pixels and the parts' contracts.
`px_per_cm` comes from the skeleton, because the clip's own `cm_px` is a
constant (2.35 where the drawing is 4.4).

## The critics

Each critic answers from images only, and names the file and the crop. Run them
in this order: a later critic's finding means nothing if an earlier one fails.

**1. Parts critic** (`cards_man.png`, the library's `sheet.png`)
- Is every pin on the drawn connector?
- Is the part what it says it is? A shoe is a shoe; a pelvis has a seat; a left
  hand has its thumb where a left hand's thumb is.
- Do the parts share one scale and one palette?

**2. Assembly critic** (loupes, overlay, silhouette)
- Does each child meet its parent at one point?
- Do the soles touch the floor?
- Is anything detached, smeared by stretch, or seen from two views at once?
- Is the prop the size the bank says, and in the hands that hold it?

**3. Body critic** (plain boards)
- Does the weight read?
- Does the pose read in silhouette?
- Does load change the whole body?

**4. Acting critic** (`keys_kit.png` only, given to a fresh reader with no title)
- What does he want, what goes wrong, what does he do?
- Pass only if the answer recovers the challenge's `situation` sentence,
  including the turn.

## A finding routes to its layer

| the fault is in | fix it in |
| :-- | :-- |
| a part's drawing (shape, handedness, scale) | `parts/kit/*.py`, or regenerate/re-cut the image and re-register |
| a socket | `parts/registered.json` (image) or the kit function (code) |
| how parts are joined, ordered or grounded | `critic/assemble_kit.py` |
| what was asked for (pose, timing, face, staging) | the Bolas Crash Lab vignette; then re-bake the bank |
| what the compiler dropped | `bolas/compile_vignette.py`, coordinated with its other editor |

A turn fixes one thing, re-runs, and writes one line in `LOG.md`: what was
seen, where, what changed, and whether the next picture confirmed it.

## Output format for a critic

```json
{"critic": "assembly", "file": "out/ACT-010/board_f80.png", "variant": "kit",
 "worst": "planted boots point toes-down", "where": "both boots, f0 and f146-239",
 "layer": "assemble_kit.py", "fix": "foot angle from bank heel->toe", "confirmed_by": "keys_kit.png turn 2"}
```
