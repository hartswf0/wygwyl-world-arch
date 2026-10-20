# Acting Arena Engine

Runs the physical performance challenges in [Acting Arena v0.2](spec/acting_arena_v0.2.json) on a cut-out rig: separate card pieces joined at brads, in profile, 3/4 and front views. It checks each take against the spec's `crash_lab_checks`. Technical results are kept apart from performance notes, and failed takes are preserved for audit.

The interactive viewer is [../arena.html](../arena.html). It displays:
- Complete challenge list (32 challenges across 8 movement families)
- Frame scrubber with 24fps live playback and contact-point visualizations
- Beat strip with authentic dramaturgical beats, flagged frames (red), declared faults (amber), and in situ pose swaps (green)
- Checks overlay with center of mass balance projection and support spans
- Technical results table, ledger, and performance notes
- Skin switcher (`bolas` dummy, `poet`, `man`, `short_limbs`)

---

## 1. Where It Stands (Empirical Results)

The Acting Arena operates two complementary engines:
1. **Hand-Authored Situations (`run_arena.py`):** Keyframed 2D scenes testing precise prop manipulation and ledge traversal (`ACT-001` pass, `ACT-006` fail/kept).
2. **3D Bolas Motion Bank Compiler (`bolas/compile_vignette.py`):** Compiles all 32 3D physical animation vignettes from Bolas (`T101`–`T132` in `bolas/bank/`) into 24fps 2D cardboard cut-out takes with camera projection, ground contact solving, and Crash Lab verification.

### Empirical Verdicts (No Constants, Pure Evaluation)
Every take is evaluated strictly against the specification tolerances:
- **Planted Foot Drift:** $\le 0.6\text{ cm/frame}$ along the ground surface.
- **Brad Disconnects:** $\le 2.0\text{ cm}$ joint separation.
- **Center of Mass Balance:** $\ge 95.0\%$ of grounded frames supported.
- **Defects:** Zero un-declared hand constraints, view mismatches, knee-to-sole rigidity violations, or skirt collisions.

Current challenge status across the 32 challenges:
- **`tested_pass`:** **19 challenges**
- **`tested_fail`:** **13 challenges** (retained with exact frame ranges flagged in `results/arena_results.json`)
- **`unsearched`:** **0**

### The 3 Skinned Cut-Out Rigs
Every challenge is compiled and playable under three distinct skins:
- **`dummy` (`bolas_3d`):** Cardboard stand-in rig (Bola, Shim, Dot) with isolated limbs, brad pivots, and clean profile parts.
- **`poet`:** The female POET cut-out puppet from `shots/weave/assets/` (fused skirt, scroll-clutching far hand, fused shin/foot).
- **`man`:** The Male Poet cut-out library from `shots/weave/cast/man/` (15+ generated sheets: profile, 3/4, front, back, replacement heads, expressions, and segmented limbs).

In total, **96+ playable takes** are compiled into `clips/` and tracked in `results/arena_results.json`.

---

## 2. Restored Dramaturgy (Authentic Bolas Beats)

Bolas vignettes carry rich acting notes that define the physical intentions of the performers. The compiler loads the authentic beat events directly from [`bolas/bank/beats.json`](bolas/bank/beats.json) (extracted from the Bolas Crash Lab source), replacing arbitrary frame-interval counters with true dramaturgical beats:

- E.g. **ACT-002 (Sprint and Reconsider)**: 40 named beats:
  - `f 7`: Bola -> *weight onto the right foot*
  - `f 15`: Bola -> *heel strike*
  - `f 56`: Bola -> *braking step*
  - `f 65`: Bola -> *braking step*
  - `f 84`: Bola -> *last brake*
  - `f 109`: Bola -> *turn*
  - `f 118`: Bola -> *turned*
  - `f 232`: Bola -> *settle*

In the viewer, walking beats (`passing`, `heel strike`) are filtered so the beat strip clearly highlights key acting decisions, turns, and braking moments.

---

## 3. The Keyframe-Budget Lab (`keyframe_budget.py`)

A fundamental theorem of cut-out animation under 3D camera projection:
1. **At the generated keyframe**, decompiling parts cut at the projected 2D joint coordinates yields a brad gap of **0.0 cm by construction**.
2. **Between keyframes**, as the 3D skeleton moves, foreshortens, and rotates under the camera triple $(yaw, elev, zoom)$, planar rigid cards inevitably diverge. The brad gap reopens.
3. The **Keyframe-Budget Lab** measures the exact frame count where the interpolated brad gap crosses the $0.6\text{ cm}$ tight tolerance or $2.0\text{ cm}$ disconnect limit. This turns "generate everything" into an exact generation budget per challenge.

Run the lab across all 32 vignettes:
```bash
python3 shots/arena/bolas/keyframe_budget.py --all
```

### Keyframe Budget Summary Table

| Vignette | Title | Frames | Acting Beats | Budget $\le 0.6\text{ cm}$ | Budget $\le 2.0\text{ cm}$ |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **T101** | Walk without spilling | 250 | 10 | 196 | 123 |
| **T102** | Sprint and reconsider | 260 | 18 | 151 | 49 |
| **T103** | Crouch under trouble | 230 | 8 | 88 | **8** |
| **T104** | Spin and find the target | 200 | 18 | 78 | 45 |
| **T105** | Jump into water | 240 | 13 | 128 | 53 |
| **T106** | Catch the ledge | 250 | 13 | 123 | 46 |
| **T107** | Slip and recover | 170 | 7 | 94 | 35 |
| **T108** | Stand after a fall | 260 | 13 | 181 | 79 |
| **T109** | Door opens the wrong way | 260 | 15 | 192 | 145 |
| **T110** | The unexpectedly heavy box | 240 | 10 | 108 | 24 |
| **T111** | Chair moved away | 200 | 8 | 63 | 27 |
| **T112** | Hand over reluctantly | 200 | 7 | 17 | **11** |
| **T113** | Punch that misses | 170 | 8 | 64 | 26 |
| **T114** | Kick and keep balance | 160 | 6 | 26 | **10** |
| **T115** | Block into retreat | 190 | 9 | 65 | 23 |
| **T116** | Fight becomes apology | 190 | 8 | 71 | 30 |
| **T117** | Dance through a missed beat | 150 | 6 | 112 | 81 |
| **T118** | Spin with a partner | 200 | 12 | 107 | 61 |
| **T119** | Celebration interrupted | 220 | 15 | 145 | 88 |
| **T120** | Too big for the stage | 200 | 5 | 163 | 126 |
| **T121** | Cower then help | 340 | 49 | 188 | 105 |
| **T122** | Pretend the box is light | 240 | 6 | 146 | 36 |
| **T123** | The false confident entrance | 230 | 14 | 169 | 134 |
| **T124** | Wait without becoming inert | 280 | 18 | 200 | 106 |
| **T125** | Fielding a grounder | 220 | 11 | 88 | 43 |
| **T126** | Basketball fake | 240 | 11 | 114 | 63 |
| **T127** | Soccer whiff | 220 | 13 | 154 | 88 |
| **T128** | Tennis: the late return | 220 | 14 | 79 | 42 |
| **T129** | A table through a door | 260 | 5 | 188 | 152 |
| **T130** | Holding the door | 250 | 16 | 178 | 173 |
| **T131** | Catch a falling friend | 200 | 11 | 86 | **19** |
| **T132** | Chain reaction | 220 | 19 | 105 | 87 |
| **TOTALS** | **32 Challenges** | **7,160 frames** | | **3,867 images** | **2,138 images** |

---

## 4. Keyframe Disassembly Gallery (`gallery.html`)

An interactive side-by-side pose audit and disassembly inspector is available at [gallery.html](gallery.html) (also accessible via the top header in [../arena.html](../arena.html)).

For each core dramaturgical key pose, the gallery renders four synchronous columns:
1. **Bolas 3D Ground Truth Skeleton**: The raw 3D joint telemetry projected at $(yaw=-22^\circ, elev=12^\circ, zoom=1.0556)$, showing active support nodes and pelvic gravity line.
2. **Rigid Rig Breakdown State**: Visualizing where planar rigid cardboard broke down (popped brad pins, limb overlap, or inverted boots).
3. **In Situ Generated Keyframe**: High-resolution photorealistic cardboard paper doll synthesis under the exact camera triple.
4. **Disassembled Modular Part Map**: Cut-out cards with joint socket anchors $(A, B)$, zero-overlap boundary masks, and bounded axial stretch scaling ($s_y = L_{\text{meas}}/L_{\text{card}} \le 1.15$).

---

## 5. Architectural Rig Corrections

### 1. Bounded Axial Stretch (Brad Gap $\to$ 0.0 cm by Construction)
- Rather than uniform 2D card scaling, `mat_bone` scales each limb piece along its anatomical bone vector ($s_y = L_{\text{measured}} / L_{\text{card}}$) while preserving character girth ($s_x = S_{\text{man}}$).
- The brad gap becomes **0.0 cm by construction**, moving the failure mode from unbounded physical disarticulation to a readable, bounded number: `axial stretch ratio`. Limb stretch is tracked per frame and flagged whenever $s_y / S_{\text{man}} > 1.15$ or $< 0.85$.

### 2. Boot Axis Correction
- When performers walk left ($fwd\_cam\_x < 0$), horizontal mirroring (`flip_x=True`) combined with a $180^\circ$ coordinate rotation previously inverted the vertical axis, rendering boots upside-down in 389 of 520 frames.
- Re-anchoring the toe vector to character forward space ($dx = -(toe_x - ank_x)$ if flipped) guarantees boots remain grounded and right-side up.

### 3. Decompiler Segmentation (Disjoint Masks vs. Overlapping Rectangles)
- Hardcoded rectangular fractional slices in `pose_decompiler.py` created 35%–110% duplicate material across neighboring boxes, causing doubled limbs.
- The pipeline architecture moves to prompt-guided SAM segmentation where part masks are disjoint by definition: $\text{Part} = \text{Mask} \cap \text{Region}(A, B)$, with joint $A$ as pivot.

---

## 6. Defect & Failure Instrumentation

The compiler actively instruments real-world cut-out failure modes:

| Defect / Check | Threshold / Condition |
| :-- | :-- |
| **Brad Disconnect** | Forearm or lower leg separation > 2.0 cm from expected anatomical length. |
| **Axial Stretch** | Limb stretching > 1.15x or compressing < 0.85x to bridge 3D perspective foreshortening. |
| **View Mismatch** | Profile head on a frontal torso, or forward head while walking away (> 135° yaw). |
| **Hand Constraint Defect** | Attempting to grip or fist when the asset hand is fixed/clutching (e.g. POET far hand clutched around scroll). |
| **Foot Rigidity Defect** | Fused knee-to-sole asset unable to achieve ankle dorsiflexion/plantarflexion. |
| **Rig Skirt Collision** | Knee joints penetrating the bounding hull of a rigid skirt piece. |
| **Planted Contact Drift** | Planted foot moving > 0.6 cm/frame along the 3D ground surface. |
| **Balance / Center of Mass** | Center of mass outside support polygon (unless airborne or caught within 4 frames). |

---

## 6. Execution Commands

All tools operate deterministically. Start a static server from the repo root:

```bash
# 1. Start server (port 8800)
python3 -m http.server 8800

# 2. Run Keyframe-Budget Lab for a vignette or all 32 challenges
python3 shots/arena/bolas/keyframe_budget.py T102
python3 shots/arena/bolas/keyframe_budget.py --all

# 3. Compile hand-authored arena challenges
python3 shots/arena/run_arena.py

# 4. Compile Bolas 3D challenges (all 32 challenges across all 3 skins)
python3 shots/arena/bolas/compile_vignette.py --all --look all

# 5. Compile specific vignettes with in situ pose swaps
python3 shots/arena/bolas/compile_vignette.py T101 T102 T103 T108 --look all

# 6. Run diagnostics on a specific challenge frame range
python3 shots/arena/diag.py ACT-003 60 85

# 7. Render Puppeteer contact sheet
node shots/arena/sheet.mjs ACT-003 '' 20 shots/arena/out_act003.jpg

# 8. Recompute requirements matrix
python3 shots/arena/requirements/requirements.py
```
