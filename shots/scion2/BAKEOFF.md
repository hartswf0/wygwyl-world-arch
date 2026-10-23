# SCION 2 bake-off: verdicts and the next step

**Test:** the fixed `test_set.json`. That is 12 held-out paintings, each reproduced from other families only, plus one 4-second move.

**Judges:** all fresh, and blind to the method:
- two mean critics, splitting 44 sheets from all methods and the card-puppet control, shuffled together;
- one motion critic, judging moves X, Y and Z from frames, not playback.

The keys are in the orchestrator's scratchpad; the sheet maker is `judge/sheets.py`.

## Mean critic (painting | reproduction, ACCEPT or FAIL, on pose and drawing)

| method | sheets | accepted | pose right | drawing clean | what kills it |
|---|---|---|---|---|---|
| control (card puppet, round 11) | 12 | 0 | 0 | 0 | seams, hip band, knee breaks, tiny boots, wrong heads |
| H1 pose graph + capped warp | 12 | 0 | 1 | 0 | wrong pose (the cap stops it reaching); tears at crotch and armpits; smeared outline |
| H2 replacement (whole paintings) | 12 | 0 | 0 | **2** | always a different pose; nearest-painting substitutes add book, envelope or flowers |
| H3 layered rig from one painting | 8 + 4 not attempted | 0 | 0 | 0 | **head always frontal and level**; hand shapes wrong; smeared halo on the outline; filled areas soft |

**The one near miss:** H1's head-thrown-back pose had the pose right but the drawing smeared.

**Cross-method finding.** The head and the hands carry most of a pose's identity: gaze, tilt, expression, fist or palm or phone or sunglasses. None of the three methods can change them. H1 and H3 keep their source's head and hands; H2 can only pick another painting's.

## Motion critic (X = H3, Y = H1, Z = H2; unblinded after)

1. **H3: FAIL, but the closest.** It is the only continuous, weighted move: one costume, one scale, knees bend, it eases in and out. It fails on:
   - the face texture swims, frames 9–30 and 60–84;
   - quality drifts from crisp to muddy by the end;
   - the feet skate about 20 px;
   - the hands change from open to fist in one frame;
   - holds frozen dead, with no settle;
   - the fists reach only head height.
2. **H1: FAIL.** The warp tears the jacket and crotch, and cross-cuts give three different men (frames 26, 29, 72, 74).
3. **H2: FAIL.** A slideshow: six jump-cuts between drawings that don't match.

## Verdict
**No method passes.** The stop condition (mean ≥ 10/12, motion clean, recognition ≥ 11/12) is not met by any. Blind recognition was not run: H1 and H2 are drawn from paintings that are themselves in the 108-painting matching set, so a match would only find their source. H3 would only be worth testing once it passes the mean critic.

**H3 is the base to build on.** It alone:
- reads as one man moving with weight;
- has no paper-doll seams (no band, no knee break);
- reaches the most poses (8 of 12).

Most of its failures are craft defects inside the method, not limits of the method:
- the outline halo;
- the face swimming and the quality drift, from repeated resampling (render every frame from the master, once);
- foot skating (plant the feet);
- the dead holds (settle, breath).

Its two real limits are:
1. **Head and hands can't change.** There is one painted head and one set of painted hands.
2. **One view only.** The 3/4 and profile poses can't be reached.

## Next step (borrowing from the losers, as SCION 2 §6 allows; reasons written)
**H3 + replacement heads and hands from the paintings**, which is how professional cut-out productions handle the face and hands.
- **Replacement heads:** a library cut from the 50 usable whole paintings (H2's catalogue), covering frontal, 3/4 left/right, up, down, turned away, laughing and so on. Each is used on the H3 body only when it is sharp at the target size, and is chosen by the target's head direction and expression.
- **Replacement hands:** fist, open palm, palm up, stop palm, pointing, holding (phone, cup, sunglasses), pocket and empty cuff. They are cut the same way.
- **Swap timing:** a hand or head swap lands on a held frame with a one-frame anticipation, never as a cross-dissolve.
- **Views:** a 3/4 rig and a profile rig built the same way from the best 3/4 and profile paintings, once a master exists outside the test families. If no master exists, H2's `gaps.json` painting briefs say what to paint.
- **Craft fixes:**
  - no halo (an alpha-correct paper edge);
  - every frame rendered from the master, so no drift;
  - feet planted with IK;
  - holds that settle and breathe.

**Judges unchanged.** The same mean critic and motion critic, fresh each round, until the stop condition is met.
