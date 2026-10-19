# Validation log · p07_turn_me_up

Deliverable checks, contact statistics and every critic report, in order.

## Critic report · 2026-10-19T17:58:39 · PASS

Scripted critic (not an independent model). Each line is measured from the clip or the rendered frames.

| Criterion | Result | Evidence |
| :-- | :-- | :-- |
| nothing visible before its reveal | **PASS** | inset first at 7.96s (line ends 7.68s); canopy label only when canopy > 0.3 |
| the failure is on screen | **PASS** | N/A for this passage: it has no failure beat (it is a request that is granted). Recorded, not claimed. |
| result on screen in >= 2 frames, wide | **PASS** | 125 frames with canopy > 0.6 at camera z < 1.08, from 8.58s to 13.75s |
| the change persists after she lets go | **PASS** | knob 75.0 deg from 8.46s to the end; canopy min 1.00 after release + 0.5 s |
| no pop-ins; the knob turns continuously | **PASS** | 11 parts in all 331 frames; largest knob step 7.75 deg/frame |
| feet do not skate | **PASS** | skirt and legs are not animated, so both soles stay on the floor line (0 px) |
| head and hand readable at grip / turn / flood | **PASS** | grip@6.67s arm-over-head 172px, arm covers 76% of knob face; turn@7.33s arm-over-head 115px, arm covers 64% of knob face; flood@7.92s arm-over-head 81px, arm covers 50% of knob face |
| nobody stands inside the console or the meter | **PASS** | 0.00s body/console 0 arm/meter 0; 6.62s body/console 0 arm/meter 0; 7.88s body/console 0 arm/meter 0; 8.92s body/console 0 arm/meter 0; 13.75s body/console 0 arm/meter 0 |
| archive registered to the canopy and labelled while it shows | **PASS** | canopy is the plate's own ceiling class (palms and pillars occlude it); label present in every frame with canopy > 0.5; console carries ARCHIVE 1956 throughout; inset captioned |
| no stray artefacts (mesh seams in the canopy) | **PASS** | frame 220: 0 long straight thin lines in the canopy crop (Hough on the Laplacian) |
| fingertip error < 1% of height while gripping | **PASS** | max 2.55 px = 0.257% of 991.2 px over 43 grip frames; released frames logged as released |
| reach travels on an arc with slow-in / slow-out | **PASS** | 27 reach frames, 0 x-reversals, speed first/peak/last 4.4/20.6/1.6 px/frame |
