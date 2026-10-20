# Arena generation pack

- **68 card briefs** — `briefs/pieces_brief.json`, one per piece, length in cm from the Bolas skeleton, pivot declared.
- **32 pose sheets** — `poses/`, the skeleton at every named beat, drawn at that vignette's own camera.
- **19 style references** — `style/`, only cards that pass acceptance, plus the three generated poses.

## The camera

yaw across these vignettes: {-22: 32} — effectively one camera.
elevation: {10: 1, 12: 10, 14: 8, 16: 7, 18: 2, 20: 2, 22: 1, 24: 1} — this is what changes, and it foreshortens the vertical rather than turning the body.

## How to use it

1. Condition on the matching tile in `poses/` for the beat you are generating.
2. Hold the look from `style/` — drawn cardboard, fluting at the cut edge, brass brads.
3. Take the size, pivot and prompt from the brief in `briefs/pieces_brief.json`.
4. Run `pieces_accept.py` on the result. A piece that fails is regenerated, not placed.

## What is deliberately not here

- Nothing cut out of a pose. The four-box decompile shares 35–110% of each card with its
  neighbours, which is the duplicate-limb artefact; there is nothing to segment if the
  piece was never joined.
- No photographic source. The cast is drawn.