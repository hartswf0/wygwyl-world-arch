# WYGWYL · Atlantis Urbanism
### Multiplane Animation Studio & 3D Walkable World

> *"Your job is not to generate one polished illustration. Your job is to DRAW A CARTOON THROUGH TIME."*  
> — Classical Multiplane Animation Studio Doctrine

[![Three.js](https://img.shields.io/badge/Three.js-r160-black?logo=three.js)](https://threejs.org/)
[![24fps Parallax](https://img.shields.io/badge/Cinema-24fps%20Multiplane-amber)](shots/reel.html)
[![12 Districts](https://img.shields.io/badge/World-12%20Districts-teal)](shots/world.html)
[![Golden Riverbed](https://img.shields.io/badge/Architecture-Golden%20Riverbed-indigo)](shots/film/reels.js)

---

## 1. What Happened? (The Genesis)

This repository transforms **81 Midjourney visual generations** into an interconnected **3D walkable multiplane universe** and **24fps animated film suite**.

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
        └── 5. Walkable 3D Universe (build_world.py + world.html)
               ├── 81 spatial dioramas assembled in Three.js (580 depth sheets)
               ├── 12 district constellations positioned at authentic city coordinates
               ├── Multi-touch gesture navigation (orbit, pinch dolly, pan, swipe flipper)
               └── Minimal Cartoon Inspector (light box, layer soloing, notan thresholding)
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

## 3. The 6 Web Suite Tools

All tools run locally with any static HTTP server (e.g. `python3 -m http.server 8765` inside `shots/`):

### 1. `shots/world.html` — The Walkable 3D Multiplane World
- **Full Three.js multiplane universe:** 81 dioramas composed of 580 physical depth sheets standing at measured optical distances.
- **Touch-Friendly Controls:**
  - `1 finger drag`: Orbit / Look around
  - `2 finger pinch`: Dolly camera forward / backward
  - `2 finger drag`: Pan camera
  - `Tap diorama`: Focus and zoom straight to that shot's optical viewpoint
  - `Swipe horizontal`: Flip forward/backward through dioramas in the district
- **Minimal Cartoon Inspector:**
  - **Animation Desk Presets:** Switch background between `World 3D`, `Studio Dark` (`#0d1015`), `Light Box` (`#f4f6fa`), and `Inspection Grid`.
  - **Layer Soloing:** Instantly toggle or solo individual planes (`P0 Mask`, `P1 FG`, `P2 Hero`, `P3 2nd`, `P4 MG`, `P5 BG`, `P6 Sky`, `Backdrop`).
  - **Signal Modes:** Cycle between `Master Plate`, `Cel Wash`, `Ink Line Only`, and `Notan Silhouette` (binary luminance thresholding for readability testing).
  - **🎯 Snap Frontal:** Locks the camera to a zero-distortion frontal orthographic angle for layout verification.
- **Flight Paths:** 14 automated cinematic camera tours following each poem sequence.

### 2. `shots/reel.html` — Golden Riverbed Multiplane Animatics
- 14 rendered 24fps poem animatics (`poem_01.mp4` – `poem_14.mp4`) with smooth dissolves.
- Live timecode HUD, interactive shot strip scrubber, and Golden Riverbed JSON inspector (`master`, `riverbed`, `flow`, `segments`, `bridges`).
- Mobile-responsive vertical stack on viewports $\le 900\text{px}$.

### 3. `shots/index.html` — Shot Lab Deep Inspector
- Per-shot multi-modal inspection: Original photograph, SAM segment masks, Monocular depth maps, Ground/Sky consensus grids, Exploded 3D multiplane views, and interactive WebGL point clouds (`points.ply`).

### 4. `shots/film.html` — The Film Suite
- Continuous narrative film playback of the assembled sequence with beat titles and district metadata.

### 5. `shots/map.html` — Geospatial Atlas
- Interactive 2D map of the Atlantis archipelago showing district coordinates, topological height curves, and camera nodes.

### 6. `shots/storyboard.html` — Storyboard Studio
- Markov-chained beat generator, shot transitions, and visual rhythm breakdown.

---

## 4. Pipeline Scripts & Architecture

For an incoming agent or developer, the CLI tools in `shots/` operate deterministically:

```bash
# Activate environment
source .venv-shots/bin/activate  # or use system python with numpy, pillow, opencv-python

# 1. Vision & camera recovery per shot
python3 shots/analyze.py --all

# 2. Slice into multiplane depth sheets & cartoon signals
python3 shots/multiplane.py --all
python3 shots/cartoon.py --all

# 3. Render 24fps eased animatics & 14 poem reels
python3 shots/film_render.py --all

# 4. Compile 3D diorama cards & compile world data
python3 shots/build_world.py
```

### Key Data Files
- `shots/world_data.js`: Master JavaScript payload loaded by `world.html`. Contains the 12 districts, 81 diorama coordinate transforms, sheet dimensions, and flight paths.
- `shots/film/reels.js`: Manifest of all 14 poem animatics, timecodes, camera directions, and Golden Riverbed prompt links.
- `shots/film/riverbed_*.json`: Full POML prompt architecture records (Master prompt, riverbed context, segment transitions, flow constraints).
- `shots/out/<id>/shot.json`: Recovered camera parameters ($H_{\text{fov}}$, pitch, altitude, horizon line, vanishing point).

---

## 5. Roadmap for the Next Agent

If you are an AI agent continuing this project, here are the highest-leverage next tasks:

1. **Character Keyframe Rotoscoping (`X-Sheets`):**
   - In `shots/reel.html`, notice the `keys to draw` warnings. Each hero plane (`P2`) is isolated and ready for 2D character action keys on twos.
2. **LaMa / Edge-Aware Inpainting (Back-Paint):**
   - When the multiplane camera makes deep truck or crane moves, occluded regions behind foreground silhouettes currently use Telea inpainting. Integrating LaMa (`large-mask-inpaint`) will produce seamless clean plates for extreme parallax.
3. **Audio Voice-Clock Synchronization:**
   - Attach spoken word poem tracks to `shots/film/reels.js`. Map syllable beats to camera easing keyframes so the camera breathes with the vocal meter.

---

*Authored by the Multiplane Animation Studio & Deleuzian Cineosis Engine.*
