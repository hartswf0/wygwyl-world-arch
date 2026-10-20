# Acting Arena engine

Runs the challenges in [Acting Arena v0.2](spec/acting_arena_v0.2.json) on a cut-out rig: separate card pieces joined at brads, in profile. It checks each take against the spec's `crash_lab_checks`. Technical results are kept apart from performance notes, and failed takes are kept.

The viewer is [../arena.html](../arena.html). It shows the challenge list, a scrubber, a beat strip with flagged frames, a checks overlay, the technical table and the notes. The pieces the man and the POET still need are listed in [requirements/arena_requirements.md](requirements/arena_requirements.md).

## Where it stands (2026-10-20)

| Challenge | Standard take | short_limbs take | Crash Lab (2026-10-16) |
| :-- | :-- | :-- | :-- |
| ACT-001 Walk without spilling | **pass** | fail (leg short of its foot by 2.6 cm) | pass |
| ACT-006 Overshoot the ledge | **fail**: thigh across the ledge corner, hands miss their marks walking forward on the top, two foot touches on the step-up | fail | fail (mantle) |
| the other 30 | not authored (`unsearched`) | | pass |

- **Performances are authored keyframes.** No Mixamo clip was searched or imported.
- **The stress variant fails.** It swaps the body proportions under the same keys. A take keyed for one body does not survive a body change; the motions would have to be re-solved from targets, not replayed.
- **Review.** Performance notes come from one reviewer (the coding agent) reading contact sheets. This is not a panel review.

## Files

| File | What |
| :-- | :-- |
| `arena_lib.py` | The rig, motions, scene, solver and checks. |
| `build_dummy.py` | Draws the stand-in pieces (DRAWN) into `cast/dummy/` (bola, shim, dot), plus `parts.json` with pivots. |
| `run_arena.py` | Compiles a scene into `clips/<ACT>[__variant].json` (a display list per frame) and updates `results/arena_results.json`. |
| `challenges/act_NNN.py` | One module per challenge, exposing `build(variant)`, `TIER` and `PERFORMANCE_NOTE`. |
| `diag.py` | Prints flagged ranges, beats and joint positions at chosen frames. |
| `sheet.mjs`, `frame.mjs` | Contact sheet and single frame through the viewer (Puppeteer; the server must be on port 8800). |
| `requirements/requirements.py` | Builds the requirements matrix and the ranked gap list (`.json` and `.md`). |

```
python3 -m http.server 8800                          # repo root
cd shots/arena
python3 run_arena.py                                 # every authored challenge
python3 run_arena.py ACT-006 --variant short_limbs
python3 diag.py ACT-006 211 240
node sheet.mjs ACT-006 '' 20 out.jpg                 # from the repo root: node shots/arena/sheet.mjs ...
python3 requirements/requirements.py
```

## Units and calibration

- **Scale.** Figure height H is in stage px; 1 cm = H/170 px, so the figure stands 1.7 m tall.
- **Gravity and frame rate.** g = 9.81 m/s² at 24 fps.
- **Body proportions** are fractions of H (`arena_lib.PROPS`, radii in `RADII`, segment masses in `MASS`). The variants are `standard`, `short_limbs`, `long_limbs` and `bulky_torso`.
- **Tolerances.** The spec's numbers (cm, cm/frame) are converted with the same scale, which follows the spec's rule that tolerances are calibrated to asset scale and frame rate.

## The rig

- **Joints.** Pelvis point, lean, and a head with a view (side or front) and a face. Each leg is thigh, shin and foot, solved by two-bone IK with the knee forward. The foot has heel, ball and toe points, a pitch, and no toe joint. Arms are upper arm and forearm, with an elbow side chosen per key. Hands have a shape and an angle.
- **Hand targets:** `rest`, `rel` (relative to the body), `world`, `carry` (follows the pelvis in x), `prop` (a socket on a prop, with an offset), and `body` (a point on another actor).
- **Props** have sockets and a signed distance. A prop is solid if marked `fixed`. Grips and releases change ownership, and carried props follow the hand.
- **Solve order, per frame:** bodies, then hands, then carried props. A hand that cannot reach its target is held where it was and logged.

## Checks (what `check()` measures)

| Spec check | Here |
| :-- | :-- |
| planted-contact drift | A planted heel or ball moving more than 0.6 cm/frame along the surface. |
| mesh penetration | Body segments as capsules against solid props, below the floor outside water, and torsos or heads overlapping in the same lane. |
| prop attachment | Hand-to-target over 2 cm; a prop jumping more than 2.5 cm when it changes owner; cup tilt over 20° or acceleration over 0.45 cm/frame². |
| weight | Centre of mass, plus carried mass, inside the support span. Hanging, water, gripping a fixed prop and being held all count as supported. A static loss that a step catches within 4 frames is accepted, and those frames are counted separately (normal walking needs this). |
| limbs | Arm overreach (card arms do not stretch), and a leg short of its foot by more than 1.5 cm. |

**Not measured** (also listed in the viewer):
- pose continuity beyond these checks;
- crossed feet and foot turn-out, which a profile rig cannot show;
- depth: the figure is 2D, so anything toward or away from camera is not checked;
- event synchronisation other than contact frames.

A thigh *resting* on a ledge corner is counted as penetration. There is no contact-versus-penetration distinction for body segments yet, and that is part of why ACT-006 fails.

## Adding a challenge

1. Create `challenges/act_0NN.py` with `TIER`, `PERFORMANCE_NOTE = {}` and `build(variant)`, which returns a `Scene`. Use `sc.actor(...)` and `sc.prop(...)`; the motions are `walk`, `turn`, `crouch`, `stand`, `pose`, `hand`, `grip`/`release`, `face`, `head_view` and `beat`. Use `sc.declare(kind, f0, f1, why)` for faults the challenge intends, such as a slip.
2. Run `python3 run_arena.py ACT-0NN`, then `diag.py` on flagged frames, then `sheet.mjs`.
3. Only after looking at the sheet, write `PERFORMANCE_NOTE['standard']`.

## From the dummy to the man and the POET

The dummy pieces are named by role (`thigh`, `shin`, `foot`, `hand.grip`, `head.side.strain`, ...). The next step is `shots/weave/cast/man/build_cast.py`. It will cut the generated sheets into pieces with the same role names, pivots and bone length, and write a `parts.json` in the dummy's format. A challenge then runs with `look="man"` and needs no code changes. The POET's parts in `shots/weave/assets/` fuse shin and foot and lack front, back and 3/4 sets; the requirements matrix lists what she would need.
