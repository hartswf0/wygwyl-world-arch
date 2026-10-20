# Validation log - poem 04, the hands

Each run of critic.py appends a table. Earlier runs are kept.

## critic run 2026-10-20 01:07 - PASS

| check | result | evidence |
|---|---|---|
| the failure is on screen (wrong attempts) | PASS | 2 pats at [6.45, 7.33] s, before the reveal at 8.07 s; stub x [965.0, 1004.6] < hand A rest x 1075.0 |
| dust lands and stays | PASS | 34 of 34 particles drawn in the last frame, 34 resting on the ground line |
| archive labelled whenever it shows | PASS | 0 unlabelled archive frames; 933 of 933 label-frames |
| nothing pops in | PASS | late entries {'sky1969': 15, 'seq:cit': 228}; the citizen enters with its top at y 965.4 (ledge top 952); the sky enters with its wipe edge above the frame: True |
| near toe drift | PASS | 0.0 px |
| grip error < 1% (A pinching B) | PASS | 2.189 px max over 50 frames (0.262%) |
| press error < 1% (wrist onto A) | PASS | 0.0 px over 6 frames |
| pat error < 1% (stub on ground) | PASS | 2.092 px over 10 frames |
| fit gap before the brad < 1% | PASS | 2.16 px (0.259%) |
| knees on ground after kneel | PASS | 0.0 px off |
| far knee joint gap < 1% (rigid far leg vs skirt) | PASS | 7.89 px max |
| IK reach ratio max | PASS | 0.998 |
| far toe planted (outside its one step 3.69-4.84 s) | PASS | 0.0 px along, 0.0 px off ground |
| her head stays readable (>= 85% of it uncovered) | PASS | worst 98.8% visible at 27.5 s (sampled every 6th frame) |
| every frame rendered | PASS | 686 of 686 frames on disk |
| no jump cuts or pops between frames (max step < 6x median and < 12 grey levels) | PASS | median step 2.04, max 8.87 between f484 and f485 (20.1667 s) |
| passage.mp4 has picture and sound of the clip length | PASS | {'video': 28.58, 'audio': 28.58}; clip 28.58 s |
| an independent critic watched it | POLISH | no separate model was available; these are scripted measurements, and a person still has to watch it |
