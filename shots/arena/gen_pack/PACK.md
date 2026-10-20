# Arena generation pack

- **68 card briefs** — `briefs/pieces_brief.json`, one per piece, length in cm from the Bolas skeleton, pivot declared.
- **32 pose sheets** — `poses/`, the skeleton at every named beat, drawn at that vignette's own camera.
- **15 style references** — `style/`, only cards that pass acceptance, plus the three generated poses.

## The camera

yaw across these vignettes: {-22: 32} — effectively one camera.
elevation: {10: 1, 12: 10, 14: 8, 16: 7, 18: 2, 20: 2, 22: 1, 24: 1} — this is what changes, and it foreshortens the vertical rather than turning the body.

## How to use it

1. Condition on the matching tile in `poses/` for the beat you are generating.
2. Hold the look from `style/` — drawn cardboard, fluting at the cut edge, brass brads.
3. Take the size, pivot and prompt from the brief in `briefs/pieces_brief.json`.
4. Run `pieces_accept.py` on the result. A piece that fails is regenerated, not placed.

## Production Movement Contact Sheets

To ensure physical coherence across acting beats without arbitrary bounding-box cuts,
13 full-bleed production movement contact sheets were synthesized directly under the canonical Bolas camera (yaw -22°, elev 12°),
conditioned on the reference cardboard puppet ("The Man" / Boone style: Black man in 30s, neat beard, sunglasses, black jacket with salmon-pink side stripes, corrugated fluting, brass split-pin brad joints):

| Sheet File | Challenge & Title | Keyframe Sequence & Acting Beats |
| :--- | :--- | :--- |
| `MAN_01_MOVEMENT.jpg` | **Movement Master** | Overview of canonical motions: Walk, Brake, Run, Crouch, Turn, Jump, Slip |
| `ACT-001_WALK_STUDY.jpg` | **ACT-001 (T101) Walk Without Spilling** | Heel-strike (#f15), Passing stride (#f45), Brake step (#f120), Settle with level cup (#f180) |
| `ACT-002_SPRINT_STUDY.jpg` | **ACT-002 (T102) Sprint and Reconsider** | Sprint acceleration (#f20), Hard brake (#f65), 180° turnaround (#f118), Balanced settle (#f232) |
| `ACT-003_CROUCH_STUDY.jpg` | **ACT-003 (T103) Crouch and Sneak** | Alert standing (#f10), Ducking (#f40), Peak crouch (#f72), Low crawl (#f150) |
| `ACT-004_SPIN_STUDY.jpg` | **ACT-004 (T104) Spin and Find Target** | Stance windup (#f20), 180° half-spin (#f65), 360° whip (#f110), Target lock-in (#f145) |
| `ACT-005_JUMP_STUDY.jpg` | **ACT-005 (T105) Jump Over Obstacle** | Compression (#f20), Launch (#f50), Airborne apex tuck (#f85), Impact splashdown (#f130) |
| `ACT-006_LEDGE_STUDY.jpg` | **ACT-006 (T106) Catch the Ledge** | Vertical leap (#f20), Ledge grip contact (#f60), Overhead hang (#f110), Pull-up (#f160) |
| `ACT-007_SLIP_STUDY.jpg` | **ACT-007 (T107) Slip and Recover** | Normal stride (#f15), Sudden foot slip (#f35), Torso back 45° flail (#f50), Recovery step (#f95) |
| `ACT-008_FLOOR_STUDY.jpg` | **ACT-008 (T108) Stand After a Fall** | Prone lying (#f30), Palm push-up (#f110), All-fours crawl (#f160), Rise to upright (#f220) |
| `ACT-010_BOX_STUDY.jpg` | **ACT-010 (T110) The Heavy Box** | Standing approach (#f20), Deep deadlift squat (#f55), Leg drive lift (#f95), Upright carry (#f130) |
| `ACT-013_PUNCH_STUDY.jpg` | **ACT-013 (T113) Punch That Misses** | Boxing guard (#f15), Straight right cross (#f55), Over-rotated whiff (#f75), Recoil guard (#f110) |
| `ACT-014_KICK_STUDY.jpg` | **ACT-014 (T114) Kick and Keep Balance** | Knee chamber (#f20), Horizontal snap kick (#f60), Apex hold (#f85), Controlled recoil (#f120) |
| `ACT-015_BLOCK_STUDY.jpg` | **ACT-015 (T115) Block into Retreat** | Ready stance (#f15), Crossed forearm block (#f50), Weight shift brace (#f85), Tactical retreat (#f120) |

## What is deliberately not here

- Nothing cut out of a pose. The four-box decompile shares 35–110% of each card with its
  neighbours, which is the duplicate-limb artefact; there is nothing to segment if the
  piece was never joined.
- No photographic source. The cast is drawn.