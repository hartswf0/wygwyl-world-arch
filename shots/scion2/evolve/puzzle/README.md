# The blind puzzle

A shape-picker that knows nothing about bodies. It covers a reference painting's silhouette with as
few library cards as it can, with no overflow outside the silhouette. Only after a fill does it
look at the Pose Lab skeleton, to learn which body zone each piece ended up filling.

Run from `shots/scion2`. The driver runs until stopped and uses two worker processes:

    nohup python3 -m evolve.puzzle.run > /tmp/claude-0/evolve-scratch/puzzle.log 2>&1 &

## What it uses
- **Target.** The reference painting's alpha, minus `assemble.REF_IGNORE` (the props; so far only
  the EX vape pen). Nothing else is used to choose pieces: no labels, no skeleton, no slot names.
- **Pieces.** Every card of the character in `library.json` and `library_harvest.json`, with the
  same costume (the poet: red_black; the EX: ex_jacket). Heads from another costume are allowed.
  Cards flagged bad stay in, because as shapes they may still fit. Holes keyed out of a card's
  white paint are filled back, so each piece is one solid shape. Excluded (`pieces.excluded`):
  - harvest cards cut from the target painting;
  - kit cards that overlap the target on its own sheet;
  - whole figures filed as cards: another painting with markers, or a sheet `ref`/`pose` figure
    that is not a head.
- **Transforms.**
  - Translation and mirroring.
  - Rotation, in 20° steps during the search and refined by ±3° and ±6° steps afterwards.
  - Uniform scale of 0.85, 1.0 or 1.18 × (target px per cm / the card's px per cm), refined
    within 0.8 to 1.25. There is no non-uniform stretch.

## Search (`fill.py`)
- **Work resolution.** The target is 128 px tall. Each cell scores one of four ways:
  - +1 for a figure cell nobody has covered yet;
  - −0.12 for a figure cell already covered (layering is allowed, at a small cost);
  - 0 for a cell on the edge (figure share 0.15–0.6);
  - −10⁴ for a cell outside the figure, so a placement cannot leave the figure.
- **Scoring a variant.** Each variant (piece × scale × mirror × angle, about 155,000 for the
  poet) is scored with `cv2.matchTemplate` (TM_CCORR) against that map. A bound on each variant's
  area skips most of them, so one full pass over all variants takes about 1 s.
- **Piece cost.** Each piece costs 0.5% of the figure area. A piece goes in only if it fills more
  than that, which keeps the count low.
- **Greedy, then local search.** Pieces are placed greedily. Local search then:
  - prunes pieces whose unique contribution no longer pays;
  - re-places each piece;
  - tries merging two touching pieces into one bigger piece.
- **Full-resolution refinement.**
  - Each piece's position, angle and scale are hill-climbed.
  - Overflow beyond a 2 px anti-alias band is hard: a piece that still overflows is shrunk, and
    dropped if shrinking does not clear it.
  - The overflow inside the 2 px band is reported separately (`overflow_in_band`).
- **Render.** Each piece is drawn with its own painted pixels, back to front, with bigger pieces
  behind.

## Learning zones (`zones.py`)
- **Recording.** After each blind fill, each placed piece is given the skeleton zone holding most
  of its pixels: head, torso, hips, upper_arm, forearm, hand, thigh, shin or foot. Each figure
  pixel belongs to its nearest marker segment. The result is counted in `zones.json` as
  piece → zone counts. Only blind fills are recorded.
- **`relabel.md`.** Lists the pieces whose most frequent learned zone (at least 2 landings) is not
  their library label. Contact sheets are in `relabel/<zone>.jpg`.
- **Prior mode.**
  - In prior mode, the uncovered cells of a zone are worth +35% to pieces that learned that zone.
    This only changes which piece wins; the gain reported is the blind one.
  - Every 3rd target is run in both modes. The 4 kill poses are run in prior mode once 8 blind
    fills exist.
  - `live/notes.md` compares the two modes.

## Output
- `live/<pose>_<mode>_<step>.jpg`: REFERENCE | PUZZLE RENDER | PIECE MAP (numbered outlines) |
  COVERAGE (grey filled, blue empty, red overflow, pink anti-alias band, yellow ignored prop).
  Each frame also gives the coverage, overflow and piece count, and the piece ids.
  - Frames are written at every improvement, then pruned to 6 per pose when the pose finishes.
- `live/_row_*.jpg`: each fill's current frame.
- `../live/latest.jpg`: the 4 kill poses plus the most recent others, one row each.
- `results.json`: per target and mode, the coverage, overflow, piece count and every placed piece
  (id, label, landed zone, scale, mirror, angle, centre).
- The driver commits `puzzle/` and `../live/` every 25 minutes.
