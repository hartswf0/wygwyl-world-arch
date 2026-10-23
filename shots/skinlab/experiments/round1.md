# Round 1 — AGENT_FIRST_PUPPET_FOUNDRY, run on the 2026-10-23 evidence pack

Prompt: `../AGENT_FOUNDRY_PROMPT.xml` (rendered with `STATE.md` → `../prompt.rendered.xml`). Queue: `round1.json`.

## BIOLOGICAL_ARTIFACTS_EXPOSED
- **Artifact 1: the sheet as the unit of truth.**
  - **The ritual:** one painted sheet per character per view, named for a human reader.
  - **The state change:** a card is a bundle of independent claims (part, view, facing, true length, joint sites), each with its own evidence. The sheet fused them. So one wrong filename makes a card wrong in five ways at once: 26 confident misfilings, 159 of 200 upper arms with a guessed view.
- **Artifact 2: the eye as the only judge.**
  - Painted-vs-blank is unsettled for all 87 front heads.
  - Nothing has been settled by a person (0 of 2,392).
  - Taste lives only in a person's glance at one auto-dressed body at a time.
  - **Hidden bottleneck:** reading. 2,392 cards × 3 views × 191 trials cannot be eyeballed.
- **The 100x failure point:** breeding and kitbashing multiply assemblies faster than anyone can look at them. The two numbers that look reassuring are self-confirming:
  - Arm and leg lengths agree within a character only because `normalize.py` set them from the skeleton.
  - The label-versus-CLIP view conflicts are 0 only because CLIP learnt from those labels.

  The foundry is producing more bodies with no independent judge.

## AGENT_FIRST_ARCHITECTURE
- **Atomic unit of state:** a claim: `(card_id, attribute, value, evidence, confidence, author)`. Claims are append-only, and they overlay the cut cards, which are never edited.
- **Concurrency and collisions:** agents write claims optimistically. Evidence weight decides between conflicting claims, in this order:
  1. a person;
  2. a model validated on held-out cards;
  3. the existing label;
  4. a pixel rule;
  5. the filename.

  Near-ties become one captcha card in the label sweep.
- **Intent verification:** invariants checked on every frame:
  - a planted foot slides less than 0.6 cm per frame;
  - the centre of mass stays inside the support polygon;
  - joints stay within their limits;
  - no card is stretched more than 12% off its true length;
  - left and right twins come from one sheet;
  - cloth colour (ΔE) stays under a cap between a piece and its parent, and skin tone under a cap across head and hands;
  - every part is within 0.75–1.35× of the Vitruvian canon;
  - a painted head gets no feature cards.
- **Human residual role:**
  - **Taste:** ♥/✕ in the grid.
  - **Disputes:** settled through the most informative captcha, the card where the judges disagree most.
  - **Liability:** signing off a body for a film shot, with the claims and invariants it passed attached.

## NEW_FAILURE_REGIME
- **Correlated blind spot:** CLIP labels the cards and also grades the labels. The Creature Lab's fitness both breeds the bodies and judges them. Guards:
  - a person-settled held-out set (20 per question) that no agent trains on;
  - a second, unrelated judge for every claim that changes what is shown (pixels, physics, or a person).
- **Accountability trap:** a ♥ on a body cannot vouch for the 15 claims under it. A shipped body carries its claim trail.
- **Hard circuit breaker:** stop the round if:
  - more than 3% of claims flip;
  - any held-out accuracy drops;
  - a source card would be modified;
  - Skin Lab miss/gap or Creature Lab fall rate regresses beyond the noise across seeds;
  - a metric's definition changed in the same commit as its "improvement".

## THE_OPPORTUNITY_WEDGE
- **Obsolete cow path:**
  - the per-character template kit, with one sheet per view and pivots placed by hand;
  - the rigger who places pivots per puppet;
  - the asset librarian.
- **The Scion:** a claim graph over cards, with a physics-and-taste judge. Any body can be assembled for any motion, then proven against the invariants and shown in about a second.
- **The incumbent's dilemma:** kit vendors sell sheets and rigging tools sell seats. Verified assemblies would make both obsolete.

## EXPERIMENT_QUEUE (worst first; full JSON in `round1.json`)

| id | focus | the change | metric (baseline → target) | independent judge | clicks |
|---|---|---|---|---|---|
| E-01 | labels | Run the "part" label sweep on CLIP's flags; re-file or junk each card. | `misfiled.n` 26 → 0 | Pixel features: skin fraction, aspect, painted area vs part canon | ~4 |
| E-02 | torso/pelvis | Label sweep on torso + hip views, least certain first; retrain `clip_label.py` with the answers. | `views.torso.guessed_only` 51 → ≤10; `views.pelvis.guessed_only` 67 → ≤10 | Pixel symmetry (front/back symmetric, side lopsided); held-out 20 | ~10 pages |
| E-03 | pelvis | Code-built 3-brad hip bridge for the 15 characters with none, plus standard brad sites (waist, hip L, hip R) for the 32 bridges that don't have exactly 3 brads. | Skin Lab puppet miss, hip-bridge rig vs 14 cards, on T001/T006/T016 per character | Creature Lab "stand" seconds upright | 0 |
| E-04 | feet | Foot body becomes a heel–ball–toe polygon taken from the card's painted outline, with the joint at the ankle brad. Add a foot-slide metric to the sim. | Creature Lab: mean planted-foot slide (cm/frame) and walk distance at gen 50, 3 seeds | Skin Lab IK: planted foot slides under 0.6 cm/frame (Crash Lab rule) | 0 |
| E-05 | tendons | Tendon anchor points read from each card's brads instead of fixed fractions. Add knee/ankle ligaments (stiff, short) separately from the muscle springs. Put far-side limbs on their own collision layer against near-side ones. | Creature Lab track-mode fall rate over T001/T006/T014, 3 seeds | Joint-limit hits per second (fewer = ligaments carry load) | 0 |
| E-06 | scale | Re-measure heads (crown→chin) and feet (heel→toe of the sole) from the painted outline; flag cards outside 0.7–1.4× canon. | `scale.head.median_vs_canon` 1.19 → 1.0 ± .08; `scale.foot` 1.19 → 1.0 ± .08; worst spreads (friend_1 head 7.5, ex pelvis 7.4, poet foot 6.5) → < 1.5 | Vitruvian figure in the Skin Lab: span/height ≈ 1.0 when dressed true-scale | 0 |
| E-07 | faces | "Painted?" sweep on 24 front heads (one page); train painted/blank on CLIP embeddings with those answers; hold out 20. | `faces.painted_unsettled` 87 → 0; held-out accuracy ≥ 90% | Pixel marks inside the skin oval, used only as a check | 2–3 pages |
| E-08 | faces | A head takes features from its own family first, else nearest skin tone (ΔE < 8). Give the 8 characters with no feature kit borrowed sets. | ♥ rate in the faces grid, strict vs free, 3 batches of 12 each | Feature tone ΔE to the head; band placement within canon ratios | ~36 ♥/✕ |
| E-09 | look | Auto-dress and breeding enforce one sheet per view (borrowing only for absent parts); report sheets per body. | Mean sheets per body (target ≤ 3); ♥ rate, strict vs free | Cloth ΔE between each piece and its parent | ~36 ♥/✕ |
| E-10 | meta (adversarial) | Try to raise Creature Lab "walk" fitness by crouch-shuffling, and Skin Lab miss by fit-mode stretching. Add the guards: pelvis height ≥ 0.8 of rest while walking, steps counted from foot contacts; no card stretched > 12%. | Fitness with the guards vs without on the same seeds; gamed runs must drop | Footfall count vs distance; stretch histogram | 0 |
