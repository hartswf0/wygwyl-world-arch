# SCION 2: start from the paintings

The person, after 11 rounds of the card puppet: "you're choosing the cowpaths make a new scion prompt and start again this is disgusting."

They were right. This prompt replaces the card-puppet run (`SCION_PUPPET_FOUNDRY.md`, `production/recognition/**`) as the way forward. That run's code is a cautionary record, not a base to build on.

## 1. The cowpaths the last run walked (do not walk them again)
1. **The template kit as the unit of truth.** We assembled a man from rigid cut cards at brads: torso, pelvis band, thigh, shin and boot, each from a different sheet. Every defect the mean critic named is that choice showing through: the pelvis band, knee steps, boots at the wrong scale, the boxy torso, wrong heads. Patching one defect per round could never remove the seams, because the seams are the method.
2. **Mocap and joint angles as the source of motion.** We solved the paintings into joint angles, then drew cards back onto those angles. The paintings were reduced to markers, and their drawing was thrown away.
3. **Global rules patched round by round.** Head clamps, minimum shin lengths, width matching, sleeves: each rule fixed some poses and broke others.
4. **Proxy metrics.** IoU, marker error and blind recognition rose (recognition went from 7 to 20 of 30) while the work stayed ugly (the mean critic accepted 0/30). Recognition is a necessary check, not the goal.
5. **Builders grading themselves**, and an orchestrator who kept routing fixes instead of questioning the method.

## 2. What is actually good here
**The paintings.** There are 130 painted whole-figure poses of the poet in `shots/kits/cut/poet.*.main-poses/` (RGBA, median about 400 px tall, as small as 73 and as large as 921), plus other characters. The person likes them: they are the film's look. They are drawn by one hand, with one face, the right boots, a seat and real knees. Pose Lab markers exist for 90 of them in `shots/rig/poses_v2/poet__red_black_sunglasses.json` (targets[].markers: shoulders, elbows, wrists, hips, knees, ankles, neck, groin, chin, head, toes, each with a confidence). Those markers may be used as data.

**The new unit of truth: a painted pose, kept whole.** Motion is made from paintings: chosen, held, cut between and deformed only as far as the drawing stays true.

## 3. The question
Can we make the poet move through the poems, staying as good as his paintings, and reach poses nobody painted? And can the system say exactly which new painting would close each remaining gap?

## 4. Three competing hypotheses (a bake-off, not a favourite)
Each hypothesis gets its own builder, in its own directory under `shots/scion2/<h>/`. They share nothing except the inputs in §2 and the test in §5. No code from `puppet-core.js`, `harness.html`, `harvest.py`, `contracts/**` or `cut_harvest/**` may be used. The card puppet is the control, scored once on the same test.

- **H1. Pose graph + mesh warp (deform the nearest painting).**
  - **Representation:** each painting becomes a triangle mesh over its alpha, skinned to its own markers, with part masks so overlapping limbs can separate: an arm in front of the chest moves without dragging the chest.
  - **Making a target pose:** choose the nearest painting by a view-aware pose distance, then deform it with as-rigid-as-possible (ARAP) or skinning toward the target.
  - **Limits:** each bone may rotate at most about 25–30° from its painting. Beyond that, choose another source or refuse and log the gap.
  - **Hidden regions** are filled from the same painting family's other poses, never smeared.
- **H2. Replacement animation (choose, hold, cut; no deformation).**
  - **Representation:** the paintings themselves, as replacement drawings, as in classic cut-out and limited animation.
  - **Making a pose:** select the painting by pose and view distance. Motion is pose-to-pose: holds, then cuts or 2–4-frame dissolves or smears, timed to the voice.
  - **Coverage:** the system outputs a coverage map. For every pose the poems need that no painting covers, it writes a painting brief: view, limb angles, hands, gaze, and a reference frame. That brief is the person's residual job.
- **H3. One painting made into a layered rig (Live2D / Spine style).**
  - **Representation:** per view, one master painting of the poet, segmented into overlapping layered parts. Each part's hidden area is completed by inpainting from other paintings of him, with soft pivots and mesh deformation inside each part (bends, not brads).
  - **Coverage:** this is the professional route for unpainted poses. It must not look like the card puppet: there may be no visible seam at any joint that the painting doesn't have.

Each builder first runs a **kill experiment**: 3 held-out poses, one day's effort. If its 3 sheets are worse than the card puppet on the mean critic, it stops and reports why. A hypothesis that survives scales to the full test.

## 5. The test (fixed before anyone builds)
**Held-out set:** the 12 paintings in `shots/scion2/test_set.json`:
- front stand;
- arms up with fists;
- push-apart;
- palms up;
- hand at the ear (three-quarter);
- crouch;
- kneel;
- seated profile with a cup;
- lying;
- bent-knee dance;
- side stride;
- head thrown back.

Each must be **reproduced from the OTHER paintings only, leave-one-family-out:** no painting from the same `poet.NN` sheet may be used as a source.

**Judge 1, the mean critic** (`production/recognition/MEAN_CRITIC.md`, unchanged): painting | reproduction side by side, at the same height, as ACCEPT or FAIL, with instant fails on sight. A fresh agent judges with no builder notes.

**Judge 2, the motion critic.** One 4-second move per hypothesis: from palms up (`poet.04.main-poses/04-6-rise-flex-reflect`) to fists up (`poet.12.main-poses/02`) and back. It is rendered at 1600×900, 24 fps, as an mp4 with a contact strip. The two end poses may be the paintings themselves, since it is animation between painted keys; everything in between must come from the method. A fresh critic judges it from frames, stating that this is not playback. It asks: is it one man, drawn by one hand, at every frame? Are there pops, stretching or swimming textures? Does the motion read as weight, not as a slide?

**Judge 3, blind recognition:** the 12 reproductions, matched blind against all 108 paintings. This is a floor, not the goal.

**Pass (the stop condition):**
- the mean critic accepts ≥ 10 of 12;
- the motion critic finds no frame that breaks "one man by one hand";
- recognition is ≥ 11 of 12.

Ceilings count only if the critic agrees that the painting itself is the limit. H2's coverage gaps are a legitimate output only as painting briefs, never as a silent miss.

## 6. Process rules
- **The orchestrator** owns the test and the judges. Builders never see the critics' prompts and never self-certify; their reports describe and do not grade. Builders compare their own output to the target painting at the same height before handing over, and must not hand over something visibly broken.
- **One method per builder; no mixing during the kill phase.** After the bake-off, the winner may borrow ideas from the losers, with the reason written down.
- **No global rule without its side-by-side.** Any rule that changes many poses is shown on all 12 poses, as painting | before | after.
- **When a critic fails something, ask first whether the method can ever pass it.** If not, say so to the person; don't patch around it.
- **Commit** each version with a clear message ending in the session trailers, and push to `claude/cool-hypatia-2dxa8w`.

## 6b. Tools in this container
Python 3 with numpy, scipy, OpenCV (cv2) and scikit-image; ffmpeg at /usr/bin/ffmpeg; Chromium at /opt/pw-browsers/chromium-1194/chrome-linux/chrome (puppeteer at /tmp/claude-0/shot/node_modules) if a browser is wanted. Offline: no image-generation models, no downloads.

## 7. Deliverables
- `shots/scion2/<h>/`: the code, a `README.md` (method, what it can't do), `out/<test id>.png` (12 reproductions), `out/move.mp4` and `out/move_strip.jpg`, and `gaps.json` (H2 and others: the poses it couldn't reach, with painting briefs).
- `shots/scion2/BAKEOFF.md` (orchestrator): the three judges' verdicts per hypothesis, the card-puppet control, the winner and why, and the next step.

## Amendment 1 (after H3 round 2; applies from round 3; earlier scores stand)
**Problem.** The mean critic fails poses for parts that exist only in the target painting's own family:
- the phone (09);
- the laughing head (12);
- sunglasses held in the hand (13);
- the chest emblem (04).

Under leave-one-family-out for everything, those parts are unreachable, so the test demanded what it forbade.

**Rule from round 3.**
- **The BODY POSE** (the master or rig, and limb placement) still comes only from other families. This is the generalisation test: poses nobody painted.
- **REPLACEMENT PARTS** may come from any painting except the target painting itself (leave-one-painting-out). Parts are heads and expressions, hands and hand-props, props, and costume details such as the emblem. This matches production, where a parts library holds every drawing of him.
- Every output records the source painting of every part, and the orchestrator checks that none is the target.
