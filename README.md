# WYGWYL · Atlantis Urbanism
### Multiplane Animation Studio, 3D Walkable World & Acting Arena

> *"Your job is not to generate one polished illustration. Your job is to DRAW A CARTOON THROUGH TIME."*  
> — Classical Multiplane Animation Studio Doctrine

[![Three.js](https://img.shields.io/badge/Three.js-r160-black?logo=three.js)](https://threejs.org/)
[![24fps Parallax](https://img.shields.io/badge/Cinema-24fps%20Multiplane-amber)](shots/reel.html)
[![12 Districts](https://img.shields.io/badge/World-12%20Districts-teal)](shots/world.html)
[![13 Suite Tools](https://img.shields.io/badge/Tools-13%20Interactive%20Apps-blue)](index.html)
[![WEAVE Registered Scenes](https://img.shields.io/badge/WEAVE-Archive%20+%20Cel%20+%20AI-orange)](shots/weave.html)
[![Acting Arena](https://img.shields.io/badge/Acting%20Arena-32%20Bolas%20Challenges-emerald)](shots/arena.html)

---

## 1. What Happened? (The Genesis & Architecture)

This repository transforms **81 Midjourney visual generations** into an interconnected **3D walkable multiplane universe**, **24fps animated film suite**, and an **executable cut-out performance engine**.

```
[81 Midjourney Stills]
        │
        ├── 1. Vision & Cineosis Analysis (analyze.py)
        │      ├── SAM (Segment Anything) object masks
        │      ├── Monocular metric depth extraction
        │      └── Camera recovery: horizon, vanishing points, pitch, HFOV
        │
        ├── 2. Multiplane Decomposition (multiplane.py)
        │      ├── 6–8 spatial planes (P0 Foreground Mask → P6 Sky / Cyclorama)
        │      ├── Physical multiplane stand depths: z' = 1 + 3·ln(1 + z_m/2)
        │      └── Secondary action flags: water ripple, palm sway, neon flicker
        │
        ├── 3. Cartoon Inspection Signals (cartoon.py)
        │      ├── Cel flats & plane-weighted ink contours
        │      ├── Layout sheets with 1.7 m scale ladders & horizon references
        │      └── Notan binary silhouette testing & consensus ground grids
        │
        ├── 4. 24fps Parallax Animatic Engine (film_render.py)
        │      ├── 81 individual shot animatics with eased camera moves
        │      ├── 14 Golden Riverbed poem reels (poem_01.mp4 – poem_14.mp4)
        │      └── Frame-accurate dissolves and cross-cut timecode sheets
        │
        ├── 5. Walkable 3D Universe (build_world.py + world.html)
        │      ├── 81 spatial dioramas assembled in Three.js (580 depth sheets)
        │      ├── 12 district constellations positioned at authentic city coordinates
        │      └── Touch & gesture navigation with minimal cartoon inspector
        │
        ├── 6. The Weave: Registered Scene Engine (shots/weave.html + weave_lib.py)
        │      ├── Multi-layer composition: Archive footage + Cut-out Cel + AI sets
        │      ├── Sub-pixel contact tracking, joint verification & LUFS audio mixing
        │      └── Headless Puppeteer verification (selftest.mjs)
        │
        └── 7. The Acting Arena (shots/arena.html + arena_lib.py + compile_vignette.py)
               ├── 32 physical challenges from Acting Arena v0.2 / Bolas 3D motion bank
               ├── 3 cut-out skins: Dummy Rig (Bola, Shim, Dot), POET, and Male Poet (The Man)
               ├── In situ pose-replacement pipeline for extreme kinematics (0.0 cm brad gaps)
               └── Crash Lab automated defect instrumentation & physical balance checks
```

---

## 2. The 12 Districts of Atlantis

The world is mapped into 12 districts with distinct atmospheric palettes, elevations, and camera laws:

| # | District | Color | Elevation | Atmosphere & Architecture |
|---|---|---|---|---|
| 01 | **Naraka Market** | `#2ad4c0` Teal | +12 m | Low-lying canal bazaar, shadow-pool rituals, twilight oil-slick reflections |
| 02 | **Orange Haze** | `#f2a541` Amber | +45 m | Smog skyways, brutalist elevated catwalks, rust-tinted vapor plumes |
| 03 | **Indigo Hive** | `#7c8cff` Indigo | +95 m | Hexagonal chrono-decay spires, cold monumentalism, signal relays |
| 04 | **Overseer Perimeter** | `#5b7bd6` Cobalt | +60 m | High-frequency blue perimeter gates, surveillance arcs, crystalline moon |
| 05 | **Mirror Thread Bay** | `#38c6e8` Cyan | -8 m | Submerged bioluminescent kelp corridors beneath specular surface mirrors |
| 06 | **Commons & Catwalks** | `#c3a6ff` Lavender | +35 m | Communal pedestrian bridges, clotheslines, suspended ozone walkways |
| 07 | **Central Plaza** | `#ff8fb1` Pink | +20 m | Dense Times-Square-scale LED canyons, holographic ancestor parades |
| 08 | **Ankhu Spires** | `#e07a5f` Terracotta | +180 m | High-altitude open-air brass towers, rooftop laundry, humming air |
| 09 | **Cenotaph Rail** | `#a3b18a` Sage | +110 m | Rusted steel rail yards hanging over fog chasms, wet stone steps |
| 10 | **Shrouded Arcade** | `#ff4d8d` Rose | +15 m | Abandoned consumerism, neon alley memories, chrome doorways |
| 11 | **Temple of Saints** | `#e9e4d0` Bone | +70 m | Stone sanctuaries, street teahouse vapor blooms, incense haze |
| 12 | **The Ascent** | `#9b8cff` Violet | +240 m | The apex needles where the cleaning drone's memory ascends into ozone |

---

## 3. The 13 Interactive Web Suite Tools

All tools are connected via the unified navigation registry [`nav.js`](nav.js) and can be accessed from the landing page [`index.html`](index.html) or switched via the in-app modal (`← Index` button on every tool).

Run locally with any static HTTP server (recommended: `python3 -m http.server 8800` from the repository root):

### 1. `shots/film.html` — The Film Suite
- Continuous narrative film cuts assembled from the 14 poem animatics.
- Side-by-side comparison between cartoon cel washes and original photographic plates.
- Beat titles, district metadata, and audio synchronization tracks.

### 2. `shots/reel.html` — Golden Riverbed Multiplane Animatics
- 14 rendered 24fps poem animatics (`poem_01.mp4` – `poem_14.mp4`) with smooth dissolves.
- Live timecode HUD, interactive shot strip scrubber, and Golden Riverbed JSON inspector (`master`, `riverbed`, `flow`, `segments`, `bridges`).
- Mobile-responsive vertical stack on viewports $\le 900\text{px}$.

### 3. `shots/world.html` — The Walkable 3D Multiplane World
- Full Three.js multiplane universe: 81 dioramas composed of 580 physical depth sheets standing at measured optical distances.
- Touch-friendly controls: 1-finger orbit, 2-finger pinch dolly, pan, diorama tap-to-focus, horizontal swipe flipper.
- Minimal Cartoon Inspector: Light Box, Layer Soloing (`P0`–`P6`), Signal Modes (Master Plate, Cel Wash, Ink Line Only, Notan Silhouette), and 🎯 Snap Frontal camera lock.
- 14 automated cinematic camera tours following each poem sequence.

### 4. `shots/map.html` — Geospatial Atlas
- Interactive 2D map of the Atlantis archipelago showing district coordinates, topological height curves, and camera nodes.

### 5. `_city/index.html` — District Guide & Architectural Lexicon
- Deep cultural, architectural, and visual codex for all 12 districts.

### 6. `shots/index.html` — Shot Lab Deep Inspector
- Per-shot multi-modal inspection: original Midjourney still, SAM segment masks, monocular metric depth maps, ground/sky consensus grids, exploded 3D multiplane views, and interactive WebGL point clouds (`points.ply`).

### 7. `shots/storyboard.html` — Storyboard Studio
- Markov-chained beat generator, shot transitions, and visual rhythm breakdown.

### 8. `shots/studio.html` — Animation Studio
- Deep exposure sheet (X-Sheet) inspection, character action keying on twos, layer timing, and camera truck/pedestal curves.

### 9. `shots/pointcloud.html` — 3D Metric Points & Gaussian Splats
- Real-time WebGL metric point cloud visualizer and 3D Gaussian Splat viewer reconstructed from monocular depth and SAM segmentation.

### 10. `shots/animate.html` — Live Cartoon Animator & Cues
- Live canvas animator driving layered cel action with eased physics curves and interactive director cues.

### 11. `shots/scion.html` — SCION: Cel Director & Quality Gates
- Rigorous cel quality auditing engine enforcing 5 mathematical gates:
  - **G1 (Plate Registration):** Zero edge drift against camera perspective.
  - **G2 (Volume Conservation):** Character silhouette area deviation $\le 1\%$.
  - **G3 (Contact Precision):** Sub-pixel socket and joint pinning error $\le 0.5\%$.
  - **G4 (Line Weight Integrity):** Plane-weighted ink contour stability.
  - **G5 (Boil Control):** Controlled line boil on twos without unmotivated flicker.

### 12. `shots/weave.html` — WEAVE: Archive, Cel & AI in Registered Scenes
- Unifies archive footage, cut-out puppets, and AI generative plates into code-driven scenes: `frame = render(clip.json, t)`.
- Five fundamental joins: **Screen** (archive on plate surfaces), **Wipe** (torn-edge temporal transition), **Citizen** (archive cut-out actors), **Touch** (rig socket contacts), **Answer** (captioned video inset).
- Authored passages:
  - `?p=p04_hands`: Poem 04 ("I put them back on"), 686 frames, 28.6s, sound. Joins: wipe, citizen, touch.
  - `?p=p07_turn_me_up`: Poem 07 ("So DJ please turn me up"), 331 frames, 13.8s, sound. Joins: touch, screen, answer.
- Headless verification: `node shots/weave/selftest.mjs` verifies sub-pixel contacts, determinism, and image loading.

### 13. `shots/arena.html` — Acting Arena Engine
- Cut-out performance engine running all 32 challenges from [Acting Arena v0.2](shots/arena/spec/acting_arena_v0.2.json).
- Supports 3 interchangeable cut-out skins: Cardboard Dummy Rig, POET, and Male Poet (The Man).
- Live 24fps canvas playback, frame scrubber, flagged frame beat strip, Crash Lab technical check overlay, center-of-mass balance indicators, and performance ledgers.

---

## 4. Character Cut-Out Rigging & Cast Asset Libraries

Cut-out animation relies on modular replacement banks rather than redraw-per-frame:

### 1. The Male Poet ("The Man") Cast Library (`shots/weave/cast/man/`)
A comprehensive production library featuring 15+ generated sheets:
- `sheets/body_profile.jpg`: Profile torso, hips, 8 sleeve segments, hands, 2 legs.
- `sheets/body_threequarter.jpg`: 3/4 turn torso, limbs, and transitional joints.
- `sheets/body_front.jpg` & `body_back.jpg`: Full frontal and rear views for camera-facing acting and walking away.
- `sheets/heads.jpg` & `heads_front.jpg`: 24 replacement heads covering 6 camera angles and 12 facial expressions (neutral, smile, singing, speaking, strain, sunglasses).
- `sheets/hands.jpg` & `hands_2.jpg`: 30 replacement hand poses (grip, pinch, point, DJ knob turn, holding glasses, cupped ear, etc.).
- `sheets/legs_segmented.jpg` & `legs_walk.jpg`: Segmented thighs, shins, and boots for 2-bone IK crouch, kneel, mantle, and replacement walk cycles.
- `sheets/props.jpg` & `set_props.jpg`: Handheld props (sunglasses, notebook, phone, mic) and stage props (railings, stairs, doors).

### 2. The POET Cut-Out Rig (`shots/weave/assets/`)
- Classical cardboard cut-out puppet: profile head, torso, rigid decorative skirt, segmented arms, and scroll-clutching far hand.
- Used extensively in WEAVE passage 04 and Acting Arena challenges.

### 3. The Dummy Rig (`shots/arena/cast/dummy/`)
- Geometric card stand-ins (Bola, Shim, Dot) with strict, untextured anatomical proportions, calibrated pivot brads, and neutral weights.

---

## 5. Extreme Kinematics & In Situ Keyframe Pose Replacement

Standard 2-bone planar IK breaks down during extreme kinematic demands (e.g. deep crouches where card limbs penetrate rigid skirts, or prone floor recoveries requiring extreme out-of-plane foreshortening):

- **The Problem:** In `ACT-003` (Bolas `T103` at frame 72) and `ACT-008` (Bolas `T108` at frame 120), standard rigid joints disconnect by several centimeters or clip through body geometry.
- **The Solution (`shots/arena/bolas/compile_vignette.py`):**
  1. Generate high-resolution in situ keyframe plates conditioned on the exact 3D camera angle, ground contact line, and lighting.
  2. Matte out alpha contours and decompose into pose-specific card assets:
     - `poet.pose.crouch_f72` (frame 72, ACT-003)
     - `man.pose.crouch_f72` (frame 72, ACT-003)
     - `poet.pose.floor_recovery` (frame 120, ACT-008)
  3. Calibrate anchor offsets and register the in situ swap into the frame display list.
  4. Result: **0.0 cm brad gap**, zero rig collision, and verified center-of-mass balance.

### Automated Defect & Failure Instrumentation
The compiler actively measures and logs kinematic defects:
- **Brad Disconnect:** Upper arm/forearm or thigh/shin separation > 2.0 cm.
- **View Mismatch:** Profile head mounted on frontal torso, or forward head while walking away (> 135° yaw).
- **Hand Constraint Defect:** Demanding grip/fist actions from a hand clutched around a fixed object.
- **Foot Rigidity Defect:** Demanding ankle rotation from a fused knee-to-sole asset.
- **Rig Skirt Collision:** Knees penetrating the rigid skirt envelope.

---

## 6. Execution, Compilation & Verification Commands

All pipelines run deterministically from the workspace root:

```bash
# 1. Start local server
python3 -m http.server 8800

# 2. Run WEAVE headless Puppeteer selftests
node shots/weave/selftest.mjs
# Output: PASS all contacts, volume conservation, determinism, and LUFS audio.

# 3. Compile hand-authored Acting Arena challenges
python3 shots/arena/run_arena.py

# 4. Compile Bolas 3D challenges (all 32 challenges across all 3 skins)
python3 shots/arena/bolas/compile_vignette.py --all --look all

# Or compile specific challenges:
python3 shots/arena/bolas/compile_vignette.py T101 T102 T103 T108 --look all

# 5. Run Arena diagnostics on flagged frames
python3 shots/arena/diag.py ACT-003 60 85

# 6. Render contact sheets via Puppeteer
node shots/arena/sheet.mjs ACT-003 '' 20 shots/arena/out_act003.jpg

# 7. Update Arena requirements matrix
python3 shots/arena/requirements/requirements.py
```

---

## 7. Master Runbook for the Next Agent (New Context Window)

If you are an AI agent continuing this work in a new context window, follow this orientation protocol:

1. **Verify Test State Immediately:**
   ```bash
   node shots/weave/selftest.mjs
   ```
   Ensure all tests report `all PASS`.

2. **Understand the Navigation Contract:**
   - Every interactive web tool in `shots/` includes `<script src="../nav.js"></script>` and a static `<a href="../index.html" id="wy-index">← Index</a>`.
   - Any new tool must be registered in `ROUTES` inside [`nav.js`](nav.js) and in `TOOLS` / `COPY` inside [`index.html`](index.html).

3. **Character Asset Slicing (`cast/man/build_cast.py`):**
   - The 15+ Male Poet sheets in `shots/weave/cast/man/sheets/` are ready to be sliced into individual PNG card assets.
   - Slicing tool should extract cards, identify pivot points (neck, shoulders, elbows, wrists, hips, knees, ankles), and compile a `parts.json` mirroring `shots/arena/cast/dummy/parts.json`.

4. **Authoring New Arena Challenges:**
   - To add a hand-authored challenge, create `shots/arena/challenges/act_0NN.py`.
   - To compile from 3D motion, use `shots/arena/bolas/compile_vignette.py`.
   - Always run `diag.py` and inspect contact sheets with `sheet.mjs` before updating performance notes in `results/arena_results.json`.

5. **Authoring New WEAVE Passages:**
   - Create `shots/weave/<passage_name>/` with a `build_clip.py` defining audio word times, states, contacts, and display lists.
   - Register the passage in `shots/weave/passages.json`.
   - Test headless via `node shots/weave/selftest.mjs <passage_name>`.

---

*Authored by the Multiplane Animation Studio, Deleuzian Cineosis Engine & Acting Arena Lab.*
