# Acting Arena Engine

Runs the physical performance challenges in [Acting Arena v0.2](spec/acting_arena_v0.2.json) on a cut-out rig: separate card pieces joined at brads, in profile, 3/4 and front views. It checks each take against the spec's `crash_lab_checks`. Technical results are kept apart from performance notes, and failed takes are preserved for audit.

The interactive viewer is [../arena.html](../arena.html). It displays:
- Complete challenge list (32 challenges across 8 movement families)
- Frame scrubber with 24fps live playback and contact-point visualizations
- Beat strip with flagged frames (red), declared faults (amber), and in situ pose swaps (green)
- Checks overlay with center of mass balance projection and support spans
- Technical results table, ledger, and performance notes
- Skin switcher (`bolas` dummy, `poet`, `man`, `short_limbs`)

---

## 1. Where It Stands (Current State)

The Acting Arena operates two complementary engines:
1. **Hand-Authored Situations (`run_arena.py`):** Keyframed 2D scenes testing precise prop manipulation and ledge traversal (`ACT-001` pass, `ACT-006` fail/kept).
2. **3D Bolas Motion Bank Compiler (`bolas/compile_vignette.py`):** Compiles all 32 3D physical animation vignettes from Bolas (`T101`–`T132` in `bolas/data/vignettes/`) into 24fps 2D cardboard cut-out takes with automatic camera projection, ground contact solving, and Crash Lab verification.

### The 3 Skinned Cut-Out Rigs
Every challenge can be compiled and played under three distinct skins:
- **`dummy` (`bolas_3d`):** Cardboard stand-in rig (Bola, Shim, Dot) with isolated limbs, brad pivots, and clean profile parts.
- **`poet`:** The female POET cut-out puppet from `shots/weave/assets/` (fused skirt, scroll-clutching far hand, fused shin/foot).
- **`man`:** The Male Poet cut-out library from `shots/weave/cast/man/` (15+ generated sheets: profile, 3/4, front, back, replacement heads, expressions, and segmented limbs).

In total, **96+ playable takes** are compiled into `clips/` and tracked in `results/arena_results.json`.

---

## 2. In Situ Keyframe Pose Replacement & Decompilation

Standard 2-bone planar IK fails when a cut-out figure encounters extreme kinematics:
- **Deep Crouch (`ACT-003`, Bolas `T103` at frame 72):** Normal card limbs disconnect at the knee/elbow or penetrate the rigid skirt.
- **Floor Recovery (`ACT-008`, Bolas `T108` at frame 120):** Figure lies prone on the ground, requiring extreme limb foreshortening that planar brads cannot represent.

### The Solution: Pose-Conditioned In Situ Generation
To eliminate false failures without compromising cut-out physics:
1. Generate an in situ high-resolution pose plate conditioned on the exact 3D camera angle, ground line, and lighting (`poet_crouch_f72.jpg`, `ref_floor_recovery_crop.jpg`).
2. Extract clean alpha contours and decompose into pose-specific card assets (`shots/arena/bolas/compile_vignette.py`).
3. Calibrate anchor offsets and register the in situ card swap at the peak kinematic frames:
   - `poet.pose.crouch_f72` (frame 72, ACT-003)
   - `man.pose.crouch_f72` (frame 72, ACT-003)
   - `poet.pose.floor_recovery` (frame 120, ACT-008)
4. Result: **0.0 cm brad gap**, zero rig penetration, and green contact confirmation flags in the viewer HUD.

---

## 3. Defect & Failure Instrumentation

The compiler actively instruments real-world cut-out failure modes:

| Defect / Check | Threshold / Condition |
| :-- | :-- |
| **Brad Disconnect** | Forearm or lower leg separation > 2.0 cm from expected anatomical length. |
| **View Mismatch** | Profile head on a frontal torso, or forward head while walking away (> 135° yaw). |
| **Hand Constraint Defect** | Attempting to grip or fist when the asset hand is fixed/clutching (e.g. POET far hand clutched around scroll). |
| **Foot Rigidity Defect** | Fused knee-to-sole asset unable to achieve ankle dorsiflexion/plantarflexion. |
| **Rig Skirt Collision** | Knee joints penetrating the bounding hull of a rigid skirt piece. |
| **Planted Contact Drift** | Planted foot moving > 0.6 cm/frame along the surface. |
| **Balance / Center of Mass** | Center of mass outside support polygon (unless airborne or caught within 4 frames). |

---

## 4. File Structure

| File / Directory | Description |
| :-- | :-- |
| `arena_lib.py` | Core rig solver, two-bone IK, physics checks, and display-list builder. |
| `bolas/compile_vignette.py` | 3D Bolas motion bank compilation pipeline, camera projection, skinning, and in situ pose swapping. |
| `bolas/data/vignettes/` | Source 3D joint coordinate files (`T101.json` – `T132.json`). |
| `run_arena.py` | Compiles hand-authored scenes into `clips/<ACT>[__variant].json`. |
| `challenges/act_*.py` | Hand-authored challenge modules (`act_001.py`, `act_006.py`). |
| `clips/` | Master display-list JSON clips (96+ files) loaded by `arena.html`. |
| `results/arena_results.json` | Persistent test database of all takes, flags, and pass/fail verdicts. |
| `requirements/` | Requirements matrix and gap analysis for character cut-out sheets. |
| `diag.py` | CLI diagnostic utility printing joint coordinates and flagged frames. |
| `sheet.mjs`, `frame.mjs` | Puppeteer contact sheet and frame renderer (requires HTTP server). |

---

## 5. Execution Commands

All tools operate deterministically. Start a static server from the repo root:

```bash
# 1. Start server (port 8800)
python3 -m http.server 8800

# 2. Compile hand-authored arena challenges
python3 shots/arena/run_arena.py

# 3. Compile Bolas 3D challenges (single or all vignettes across all 3 skins)
python3 shots/arena/bolas/compile_vignette.py T101 T102 T103 --look all
python3 shots/arena/bolas/compile_vignette.py --all --look all

# 4. Run diagnostics on a specific challenge frame range
python3 shots/arena/diag.py ACT-003 60 85

# 5. Render Puppeteer contact sheet
node shots/arena/sheet.mjs ACT-003 '' 20 shots/arena/out_act003.jpg

# 6. Recompute requirements matrix
python3 shots/arena/requirements/requirements.py
```
