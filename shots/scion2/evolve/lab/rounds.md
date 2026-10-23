# Algorithm lab: rounds

The benchmark is `benchmark.json`: 24 TRAIN targets and 12 HELD-OUT targets, both fixed before round 01. HELD-OUT
runs every 3rd round and is never used for tuning.

**Selection.** The proxy is Q (see `harness.py`). The blind critic's verdicts outrank Q and CLIP whenever they
disagree.

**Files.** Each round's numbers are in `round<NN>/summary.md`, with `round<NN>/failures.jpg` and
`round<NN>/critic/`. Algorithms are in `algos/`; retired ones move to `retired/`.

## Round 01: the seed population

### Algorithms
- `greedy`: the blind greedy fill.
- `greedy_prior`: greedy plus the learned zone prior.
- `grow`: growth from a seed with brad snapping.
- `grow_settle`: grow, then the swarm settle about the joints.

### Scores (TRAIN means)

| algo | Q | coverage | components | CLIP |
|---|---|---|---|---|
| grow_settle | 1.151 | 84.4% | 1 on all 24 | 0.739 |
| grow | 1.130 | 84.9% | 1 on all 24 | 0.739 |
| greedy | 0.711 | 89.1% | 11.5 on average | 0.753 |
| greedy_prior | 0.669 | 89.7% | — | 0.754 |

- greedy_prior crashed on 4 targets: a size check was missing in the prior branch of `fill.best_of`.

### Blind critic
- **Verdict.** 0 of 12 accepted.
- **Mean closeness out of 10:** grow 3.0, grow_settle 2.2, greedy 1.75.
- **Failure kinds** (out of 12 sheets):
  - wrong part substituted: 11;
  - head wrong: 10;
  - pieces not joined or floating: 9;
  - limbs or torso missing: 8;
  - junk content (captions, thumbnails, feature cards, props, blank plates): 8.
- **The critic and CLIP disagree.** CLIP put these renders at about 0.74 (greedy 0.75), while the critic gave them
  1–4 out of 10. CLIP rewards having the colours and the overall silhouette. It does not penalise a hand standing in
  for a foot, or a missing head. From here on CLIP is reported but not trusted for selection.

### My failure analysis (round01/failures.jpg, grow_settle)
- **(a) Whole limbs never grow.** Examples: one arm on arms-up (61% coverage), the back leg on reach-window and 04-6,
  an arm on dance-profile.
  - Cause: the brad at the limb's root is consumed by the first piece that snaps there, and that piece usually grows
    elsewhere.
  - Second cause: with 30° steps, no piece fits a narrow limb exactly at the free brad.
- **(b) Props merged with the figure.** The door frame on walk-into, the table on lean and the window on reach-window
  are counted as silhouette. This is a harness bug, not an algorithm one.
- **(c) Wrong part, and junk.** The picker is blind, so any shape fits. The library holds captions, whole-figure
  thumbnails, mouths, props and blank plates.
- **(d) Head wrong or missing.** Nothing in the search knows that a body has exactly one head, or that a head is
  upright.

### Selection
- greedy_prior: retired (it errors, and adds nothing over greedy).
- grow_settle: retired. The critic put grow (3.0) ahead of it (2.2), and its settle survives inside the new
  variants.
- greedy: retired. Critic 1.75, and never one component.
- grow: kept as the baseline.

## Round 02

### Harness changes (applied to every algorithm, so every score was recomputed)
- **Prop masking.** Alpha farther than 16 cm from every segment of the Pose Lab skeleton is a prop, not figure.
  This applies to every component of at least 40 px.
- **Skeleton coverage term.** `segments_missing` counts the skeleton segments (head, torso, hips, and each arm and
  leg segment, hand and foot) whose region is less than 50% covered. Each one costs 0.05 in Q.
- **Library hygiene** (`puzzle/hygiene.py`, cached in `hygiene.json` so a person can audit it):
  - CLIP zero-shot excludes a card when a junk prompt (text, small whole figure, single feature, prop, blank plate)
    beats the best body-part prompt by 0.02.
  - Pixel tests exclude blank plates and scatters.
  - A margin of 0.005 was tried first. It threw out sleeves as "props" and heads as "figures" (93 of 1,488 cards);
    0.02 keeps 21 poet cards out: mouths, a microphone hand, flowers, a letter, pocket patches and a caption
    thumbnail.
- **Holes.** Holes painted on purpose are no longer filled. A hole of 3% of a card or more stays transparent, which
  covers the hollow-chest card.

### New variants, each with its hypothesis
- `grow_multijoin`: limbs fail because a root brad takes only one child. Let a brad take 3 joins.
- `grow_search`: greedy growth commits too early. A (1+1) evolution over the growth program, run per seed island:
  change one step's rank, regrow the rest, keep the result if it is fitter. It has 90 s and includes multijoin and
  ends.
- `grow_clean`: junk and wrong heads come from an unclean library and no head rule.
  - Uses hygiene plus a head rule: at most one head card, within 40° of upright, with a painted face (dark eye band)
    on front targets and a back-of-head card on back targets.
  - If growth ends with no head, one head is attached anyway.
  - Also uses multijoin, an ends phase at 0.3× piece cost, and the settle.
  - CLIP's painted-face prompt was tried first for heads. It misread most painted heads as backs of heads, so the
    head rule uses the library's head filing and the eye-band pixel test instead.
- `grow_appear`: pure shape cannot tell a hand from a foot.
  - The 120 best attachments by shape are re-scored by appearance. A covered cell counts +1 when the piece's paint is
    within ΔE 30 of the reference's local colour, falling to −0.3 when it is far off.
  - The reference is only a guide; no pixel is copied. Otherwise the same as grow_clean.
- **Not built yet: learned structure (an attachment grammar).** It needs accepted bodies to learn from, and none of
  round 01's renders were accepted. It will come once the critic accepts some bodies.
