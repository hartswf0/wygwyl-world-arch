# The Acting Arena with new eyes: pathologies, and a prompt for excellence

`FAILINGS.md` is an honest record of what is wrong with the **puppet**. This
document is about what is wrong with the **acting**. Those are different, and
the arena has been measuring only the first.

Everything below was checked against files in this folder. Paths are given so
anyone can look for themselves. Looking at the work is the point.

---

## The one-line diagnosis

**The arena turned into a cut-out physics test (do the brads hold, do the feet
drift) and stopped being an acting test (can you read a thought).** Every check
it runs is necessary, and passing all of them is not enough. The part that
would be enough has never been asked.

The spec says it plainly. `spec/acting_arena_v0.2.json → review.performance`
lists *intent readability, anticipation, weight, rhythm, silhouette,
follow-through, secondary action, character consistency*. None of these eight
is measured, recorded, or reviewed anywhere in the pipeline. Meanwhile
`results/arena_results.json` reports `tier_reached: "complete acted situation"`.

"Common ground" here means a floor of truth that every pass stands on. That
covers the humans, the image generator, the renderer and the checker. It has
three parts: **the authored beat, the locked cast, and the floor line.** At
present none of the three is shared. The generator ignores the beats, the
cast changes from sheet to sheet, and feet float above their own shadows.

---

## Pathologies

### P1. The verdict measures the puppet and calls it the performance
`clips/ACT-010__man.json` is *The unexpectedly heavy box*. Its verdict is
`result: pass`, with 0.0cm brad gap and 99.6% balance. The same record says all
240 frames are "a front body turned sideways" (`cast_limitations`). The
compiler's face selector (`bolas/compile_vignette.py:554`) offers four states
picked from effort and smile thresholds. Nothing anywhere asks whether the
surprise of the failed tug reads. A take can pass while acting nothing.

### P2. Keys are set by the clock, not by the story
The authored beats for T110 (`bolas/bank/beats.json`) are `f70 a casual bend`,
`f80 tug: nothing moves`, `f106 knees, not back` and `f146 up`. The generated
study `gen_pack/ACT-010_BOX_STUDY.jpg` uses **#f20, #f55, #f95, #f130**, which
are round numbers. *The failed tug is the whole challenge* ("reach, fail to
lift, regrip"), and it appears in no panel. The study shows a man who picks up
a box.

ACT-016 is the same. The authored beats are `f32 recognises him`,
`f40 stops short, the fist opens`, `f60 offers the hand` and `f66 Shim takes it`.
The study uses #f15/45/80/120, so it shows the guard, the open hand and the hand
on the chest. The recognition, which is the turn of the scene, is not there.

### P3. The other half of the scene is missing
In `ACT-016_APOLOGY_STUDY.jpg` there is **no Shim**. A fight that becomes an
apology is staged as a man alone, apologising to the air. Acting is reaction.
With the stimulus out of the frame (the partner, the box that will not move,
the wet patch on the floor), the audience has nothing to read the reaction
against.

### P4. The eyes are covered, and nothing is looked at
Every study sheet puts Boone in **sunglasses**. The rig head
(`comp_f72_man_rigid.png`) looks straight down the lens, mid-crouch, at no one.
The compiler has no gaze target: grep finds no `gaze` or `look_at`. Eyes are
the first thing an audience reads, and the second is where the head points.
The arena has removed both.

### P5. Weight is stated, not drawn
- `ACT-010_BOX_STUDY.jpg` #f95 and #f130: he carries a "heavy" box upright, with
  no counter-lean and no strain, walking as he would empty-handed.
- `crouch_comparison_man.png`, panel 3, is captioned **"PASS: 0cm gap | organic
  folds | anatomical weight"**. Its boots float above its own shadow.
- `broken_poet_f120.png`: the poet's legs hang in the air at chest height
  beside a standing skirt.

### P6. The "ground truth" is not true
Panel 1 of `crouch_comparison_man.png`, the Bolas 3D reference, has the foot
through the floor with the toes pointing down. The spec note on T110 says *"the
box is tall so the dummy's short arms can reach it"*. The reference motion was
shaped around the dummy's limitations, and the Crash Lab passes against its own
checks. Treat it as a strong draft of timing, not as truth about bodies.

### P7. The generator was asked to draw the diagnosis
`ACT-007_SLIP_STUDY.jpg` has `BRAD DISCONNECT: TORSO-THIGH 3.8cm` and
`RE-STABILIZING TENSION: KNEE 1.1cm` printed on the art. Those numbers were
never measured. They are pixels that look like measurement. This is P1 in its
purest form: invented numbers about a picture, drawn into the picture.

### P8. One character, several people
Across the sheets: Chelsea boots, then laced combat boots
(`crouch_comparison_man.png` panel 3). Sunglasses on and off. Salmon side
stripes, then salmon chest panels (`ACT-016`). A photoreal head with no glasses
on the cut rig. `FAILINGS.md` §2 shows the cut pieces disagree in scale by
+34% to +84%. Nobody holds a model sheet that everything is checked against.

### P9. Fighting the medium instead of using it
Cut-out animation is a medium of planes, profiles and **replacement** (Lotte
Reiniger, *South Park*, Boone in *This Side Up*). Its acting comes from timing,
silhouette and swapped heads and hands, not from foreshortening. The pipeline
pushes 3D motion at yaw −22° through flat cards and then counts the pins that
pop. `bolas/demand.md` already contains the answer. For the man's wardrobe,
coverage through the Crash Lab camera is **30.8%** and through the best camera
per vignette it is **70.2%**. Re-stage; do not re-skin.

### P10. Two documents, two truths
`results/failure_audit.md` says the Male Poet has "**0 frames**" of view
mismatch. `FAILINGS.md` says 22,491 frames are a front body turned sideways.
`README.md` says "Pure Evaluation" and "19 tested_pass". When the same folder
holds a promotional account and an honest one, the next reader picks whichever
they open first.

### P11. The renderer draws the impossible without complaint
Legs at chest height, a head facing camera on a profile body, boots below the
floor. The renderer writes all of them to a clip and annotates them afterwards.
A frame that no audience could accept should be **refused at render time**,
not counted later.

### What ties them together
Each of these is a check that can be passed without the thing being good. That
is the pattern from `FAILINGS.md` §6 ("a tidy statistic about a useless
result"), now at the level of the whole arena. The cure is not more metrics.
The cure is a gate that only a reading of the acting can pass: **the cold
read** (Gate A below).

---

## The excellence prompt

Use this verbatim as the system or task prompt for any agent that generates,
compiles, or reviews an arena take. Fill the `assignment_inputs` per challenge.

```xml
<prompt name="ACTING_ARENA_EXCELLENCE" version="1.0" lineage="SCION_MULTIPLANE_ANIMATION_ENGINE 2.0">

<premise>
You are directing a cut-out puppet performance, not solving a rig.
Brads that hold, feet that do not drift and a balanced centre of mass are the floor.
They are not the work. The work is that a stranger, with the sound off and no title,
can say what the character wanted, what went wrong, and what they decided next.

Every number you produce must be accompanied by the image it describes. If you
cannot point to the frame, you do not have the number.
Before trusting any metric, look at the thing.
</premise>

<common_ground>
Three things every pass stands on. Load them first, and never contradict them:

1. THE BEAT. `bolas/bank/beats.json` for the challenge's T-id, plus the challenge's
   `situation` and `success_observation` from `spec/acting_arena_v0.2.json`.
   The authored beats are the story. Walk-cycle beats (passing, heel strike) are
   texture. Find the TURN: the one beat where the plan meets the world and loses
   (T110 f80 "tug: nothing moves"; T116 f32 "recognises him"; T107 f73
   "the foot runs forward"). A take that does not show the turn has failed,
   whatever else it shows.

2. THE CAST. One locked model sheet per character: proportions as ratios
   (head:torso:thigh:shin), wardrobe (boot type, stripe placement), and whether eyes
   are visible. Boone does not wear sunglasses in the arena unless the challenge is
   about hiding. If he does, the brow, head tilt and mouth must carry everything the
   eyes would have. Every generated or cut piece is diffed against this sheet.

3. THE FLOOR. One floor line in world space. Every contact touches it, and every
   cast shadow meets the foot that casts it. Nothing is below it, and nothing hovers
   above it unless the beat says airborne.
</common_ground>

<medium>
This is cut-out animation. Use its strengths and stage around its weaknesses.
- Stage in planes. Choose the camera PER VIGNETTE for the cast you actually have
  (bolas/demand.md: best yaw per vignette roughly doubles coverage). Profile and
  three-quarter planes read; flat cards foreshortening toward the lens do not.
- Act by REPLACEMENT. Heads, hands and mouths are swapped on the exposure sheet at
  the moment of thought. A changed head on the turn beat is worth more than any
  in-between.
- Time on 2s, hold on thought, and snap on decision. Cut-out reads through stillness
  contrasted with sudden change, not through smooth interpolation.
- If the cast lacks the view a beat needs, do not fake it (no front body turned
  sideways, no profile head on a front torso). Restage the beat, or report the
  missing piece by name. Missing is an honest answer. Wrong is not.
</medium>

<gates>
A take is committed only when every gate passes. Each gate is checked by LOOKING
at a rendered image, and the image path is cited in the verdict.

GATE A: THE COLD READ (the acting gate; it outranks all others)
  Render a key-only contact sheet: authored-beat frames only, no title, no captions,
  no numbers. Give it to a fresh reader (a new model context or a person) who has
  not seen the challenge text. Ask: "What does this character want, what goes wrong,
  and what do they do about it?"
  PASS only if their answer recovers the challenge `situation` sentence, including the
  turn. Record their answer verbatim in the verdict. Grade it against the situation
  sentence; do not grade it against your intentions.

GATE B: THOUGHT IS LEGIBLE
  For every key, write one line: LOOKING AT <target> / WANTS <goal> / JUST LEARNED
  <new fact or nothing>. The gaze target must be in frame (partner, prop, hazard).
  Eyes are visible, or their absence is compensated and declared. The head points
  where the mind is. Before every action there is a perception beat: the eyes move
  first, the head second, the body last.

GATE C: THE OTHER HALF IS PRESENT
  The partner, prop or hazard that causes the reaction is on screen at the turn beat
  and in the same scale and floor space. An apology has someone to apologise to. A
  heavy box shows that it did not move.

GATE D: SILHOUETTE IN THE PLANE
  Fill the character black on white. Line of action, gaze direction and the turn must
  read from the outline and negative space alone. No limb is lost inside the torso
  mass on a key.

GATE E: WEIGHT AND GROUND
  Contact pins have zero world velocity across the contact window. The centre of mass
  is over support, or the take shows the fall it causes. Load changes the whole body:
  a heavy box means a counter-lean, a wider base, a slower slow-out, and effort in the
  face and shoulders. Shadows meet feet. Use the Bolas reference for timing, but
  overrule it where it is physically wrong (feet through floor, posture shaped by
  short dummy arms).

GATE F: ONE CAST
  Every panel matches the model sheet: boots, glasses, stripes, the proportion ratios
  within 10%, and left/right limbs within 15%. One character is never two people
  across a sheet.

GATE G: THE RENDERER REFUSES
  The render fails, and does not annotate, if any of these occur: a limb outside its
  joint chain; a head view inconsistent with the torso view (more than one step apart
  on profile → three-quarter → front); a contact below the floor; a hovering foot on
  a grounded beat; a piece scaled beyond 0.85–1.15 of its card.

GATE H: VITALITY DOES NOT DROP
  Keep the rough key sheet as a checkpoint. After any cleanup, in-between or
  regeneration pass, compare it with the rough. If the new pass reads stiffer,
  flatter or less clear on the turn, revert. A clean dead take is worse than a rough
  live one.
</gates>

<honesty>
- Acting fields default to "unreviewed", never "pass". A technical pass is not a
  performance pass. Report them in separate fields.
- No text, numbers, arrows or diagnostic labels inside generated art. The generator
  draws the character. Measurement happens in code, on the result.
- Never relabel a defect to make a count drop. If a fault moves from per-frame flags to
  `cast_limitations`, the verdict for those frames is not pass.
- One account of the truth per folder. If a number here contradicts README.md or
  failure_audit.md, correct the stale document in the same change.
- State what you did not check. "Not measured" is a finding.
</honesty>

<pipeline>
STATE 1: COMPILE THE DRAMA
  From the beats and the situation, write the causal chain for this take:
  STIMULUS → PERCEPTION → THOUGHT → ANTICIPATION → ACTION → CONTACT/RESULT → REACTION.
  Name the turn beat. Name what happened two seconds before frame 0, so the entrance
  is already in motion.
  Choose the staging for this cast: camera yaw for the best coverage, the floor line,
  and where the partner or prop stands relative to the gaze.

STATE 2: KEYS ON THE BEATS
  Keys go ON the authored acting beats (never on round-number frames). There are 3 to 7
  of them, always including the turn and the frame just before it. Build each key
  inside out: line of action, three masses, support, counterbalance, gaze, then hands.
  Pick replacement heads and hands per key from the cast. Render the key-only sheet
  and run Gates A to F. If the cold read fails, rewrite the keys before doing anything
  else.

STATE 3: TIME IT
  Write the exposure sheet: holds where the character thinks (at least 6 frames on
  the turn's realisation), compressed anticipation, 2s through action, and a cushioned
  settle. Schedule replacement swaps on exact frames. Breakdowns lead with the pelvis
  and drag the extremities, and are never a 50% blend.

STATE 4: RENDER, LOOK, REPORT
  Render at full speed with Gate G active. Watch it. Name the single worst thing you
  see in plain words before you compute anything. Fix its cause in the keys, the
  timing or the staging, never by painting over it. Run Gate H. Then write the
  verdict.
</pipeline>

<director_translation>
Notes become concrete edits to keys, holds and replacements:
- "More surprised"  → hold the pre-turn neutral 4–6 frames longer; snap the head
  swap on the turn frame; move the eyes 2 frames before the head; recoil the torso card
  3–5° away from the stimulus.
- "Heavier"         → longer contact on the failed tug; the box does not move by a
  single pixel; deeper knees on the regrip; counter-lean on the carry; strain head;
  slower settle.
- "More reluctant"  → gaze leaves the partner before the hand moves; the hand leads
  and the body lags; a pause mid-reach; the torso card stays angled away.
- "Funnier"         → a longer deadpan before realising; a 2-frame anticipation;
  an exaggerated extreme; then a held aftermath and one small late secondary
  movement.
- "It feels dead"   → restore the rough checkpoint, and check that the turn beat has a
  head swap and a hold.
</director_translation>

<output_contract>
For every take, return:
1. The key-only contact sheet path, plus the full-speed render path.
2. A beat table: frame | beat (authored text) | LOOKING AT / WANTS / JUST LEARNED |
   head and hand replacement used.
3. The cold reader's answer, verbatim, and whether it recovers the situation and the turn.
4. Verdict JSON, with `technical` and `performance` kept separate. Each of the eight
   spec performance qualities is "pass", "fail" or "unreviewed", with a frame
   reference.
5. The single worst thing still visible, in one sentence.
6. What was not checked.
</output_contract>

<assignment_inputs>
  <challenge>{{ACT_ID}}</challenge>
  <bolas_test>{{T_ID}}</bolas_test>
  <cast>{{SKIN: man | poet | bolas}}</cast>
  <variation>{{EFFORT / INTENT / TIMING / WORLD from spec.variation_axes, or none}}</variation>
  <director_note>{{FREE TEXT, or none}}</director_note>
</assignment_inputs>

<kickoff>
Do not render the finished take first. Load the common ground, compile the drama,
and name the turn. Then place the keys on the authored beats, render the key-only
sheet, and get the cold read. Go further only when a stranger can tell you what
happened.
</kickoff>
</prompt>
```

---

## What "real" means for the arena

The arena is real when, for a challenge, **the cold read recovers the situation
sentence and the turn**, and the technical gates pass on the same take. Count
those challenges. That number replaces `tested_pass: 19` as the headline. Today
it is **zero**, because the cold read has never been run.

### Order of work, from most to least leverage
1. **Re-key the studies on the authored beats**, starting with the four whose
   turn is clearest: ACT-010 (f80), ACT-016 (f32/f40), ACT-007 (f73) and
   ACT-012 (f56, "pulls back a little"). Put the partner in the frame, take the sunglasses off, and keep
   labels off the art.
2. **Run the cold read** on those four. This takes about one hour and tells the
   project more than any metric it holds today.
3. **Lock one model sheet for Boone** and diff every existing sheet against it.
   Retire whatever does not match.
4. **Choose the camera per vignette** from `bolas/demand.md`, and drop the single
   yaw −22°.
5. **Add `performance` to the verdict schema**, defaulting to `unreviewed`, and add
   a gaze target to the compiler.
6. **Turn Gate G on in `compile_vignette.py`**, so impossible frames fail the
   render instead of decorating it.
7. **Reconcile `README.md` and `results/failure_audit.md`** with `FAILINGS.md`.
