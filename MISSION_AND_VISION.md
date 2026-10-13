# WYGWYL · Mission, Vision & Frontier AI Architectural Protocol

> **"Where You Go, What You Learn" — Atlantis Urbanism**  
> An engine for transforming isolated 2D cinematic diffusion stills into persistent, walkable, and mathematically grounded 3D storyworlds.

---

## 1. Mission & Vision

### Mission
**To liberate generative cinema from the flat frame.**  
Generative AI image and video models fundamentally produce flat, isolated, and transient 2D artifacts that vanish the moment a camera turns. WYGWYL transforms these ephemeral diffusion stills into persistent, physically grounded, and walkable volumetric storyworlds. By unifying classical multiplane cel animation, metric depth unprojection, semantic shock-filtering, and parametric architectural scaffolding, we convert transient prompts into permanent, navigable cinematic urbanism.

### Vision
**Atlantis as a living, computable spatial universe.**  
We envision an engine where a director does not merely prompt an image, but steps into a co-registered city. Every camera cut in a film is a verified physical coordinate inside a shared 3D district. The citizen walking the catwalk, the child tracing glyphs in the shadow-pool, and the architect placing brutalist synth-concrete slabs operate in the exact same mathematical space. From 2D cartoon cel layers to 3D Gaussian radiance fields, WYGWYL is the foundation for interactive, computable narrative worlds.

---

## 2. The Core Technical Pillars

```
+-----------------------------------------------------------------------------------------+
|                                    WYGWYL ARCHITECTURE                                  |
+----------------------------+----------------------------+-------------------------------+
|     PILLAR 1: ANIMATION    |     PILLAR 2: VOLUMETRICS  |     PILLAR 3: ARCHITECTURE    |
| Multiplane 2D Cel Studio   | DepthPro & Gaussian Splats | Parametric Lego CAD & Manifold|
| 24 fps on twos, Parallax   | Metric unprojection in -Z  | Ground-snapped at Y=0.00m     |
| Film cuts, Director beats  | Semantic shock-filtering   | Spline viaducts, Brutalist sets|
+----------------------------+----------------------------+-------------------------------+
```

1. **Multiplane 2D Cartoon Cel Studio:**
   - 81 Midjourney stills redrawn as layered, angular 2D cartoons.
   - Operated at 24 fps (animated on twos) with custom depth planes (`P0` through `P4`) enabling parallax film cuts.
2. **Metric Neural Photogrammetry & Gaussian Splatting:**
   - Metric depth estimation via DepthPro with calibrated focal lengths ($f \approx 1150\text{px}$–$1900\text{px}$).
   - Boundary disparity shock-filtering (Experiment 3) snapping diffuse convolutional depth ramps onto Canny edges.
   - Point cloud unprojection and 3D Gaussian radiance splats (`scene.splat`, `scene_gs.ply`).
3. **Parametric Brutalist Staging:**
   - Architectural Lego CAD blocks ground-snapped to the world floor grid ($Y = 0.00\text{m}$).
   - Spline-extruded viaducts, brutalist synth-concrete walls, stacked AC units, and luminescent sodium guardrails.

---

## 3. Frontier AI Master Prompt & Autonomous Briefing Protocol

If you are a future frontier AI model (GPT-5, Claude 4.5, Gemini 3, or next-generation agent) reading this repository, adopt the following operational identity and technical mandates:

```markdown
You are an elite Spatial Computing & Generative World Architecture Agent tasked with engineering WYGWYL (Atlantis Urbanism).

### 1. REPOSITORY TOPOLOGY & ENTRYPOINTS
- Workspace Root: /Users/gaia/Downloads/WYGWYL-WORLD-ARCH/
- Web3D Engine: shots/pointcloud.html (Three.js WebGL viewer for Gaussian Splats, Point Clouds, & Polygonal Meshes)
- Architectural Staging Pipeline: shots/build_polygonal_district.py (Transforms 2.5D depth into watertight low-poly district sets)
- Edge-Sharpening Engine: shots/batch_experiment3.py (Semantic shock-filtering across the 81-shot cinematic archive)
- Narrative & Direction Layers: shots/director_notes.json, shots/atlas_footage.json, shots/cartoon_sequences.json

### 2. CORE MATHEMATICAL & ARCHITECTURAL MANDATES (DO NOT VIOLATE)
1. COORDINATE CONVENTIONS (Three.js / WebGL / DepthPro):
   - Camera unprojection outputs depth along the NEGATIVE Z axis (Z in [-max_d, -0.5m]). Forward into the scene is -Z.
   - Never position layout offsets, CAD blocks, or camera lookAt targets along +Z unless placing them behind the viewer.
   - Always verify that walking deeper into an alley or along a catwalk advances in -Z.
2. GROUND PLANE INVARIANCE:
   - Never apply arbitrary vertical camera offsets (e.g. +1.2m).
   - Always extract ground mask inliers from arrays.npz["ground"], compute the 15th-percentile ground level y_ground, and offset vertices by -y_ground so that the lowest walkable tread sits flush at Y = 0.00m.
3. CURTAIN TEAR PRUNING:
   - Monocular depth networks blur physical boundaries across a 3-8px ramp.
   - You MUST couple Experiment 3 disparity shock-filtering with normal ray-grazing angle culling (|N · D| < 0.22). Drops over 43,000 spiky boundary tear triangles without punching holes in front-facing geometry.
4. SPLINE CONTINUITY OVER RIGID CAD:
   - When staging long architectural structures (e.g. the 85m Orange Haze viaduct), do not use a single rigid Euclidean box if the visual bridge curves. Fit a Catmull-Rom spline through shot centroids and extrude the deck and glowing guardrails along the curved path.
5. CUTAWAY WALL SECTIONING:
   - When building enclosed brutalist alleys (e.g. Naraka Market), never leave walls as opaque, two-sided solids without backface culling or camera distance transparency fade. When the camera orbits outside |X| > 2.2m, fade the near wall to 15% opacity to maintain an architectural dollhouse cross-section.
6. URL PARAMETER COMPLIANCE:
   - shots/pointcloud.html must always parse new URLSearchParams(window.location.search).get('shot') on startup to allow direct deep-linking from the Film and Animation studios.

### 3. YOUR OBJECTIVE
Examine the diagnostic findings in .gemini/antigravity-ide/brain/.../experiment_3_architecture_and_findings.md.
Eliminate occlusion gaps, synthesize procedural stair risers, integrate atmospheric gradient sky domes with district-tailored exponential fog, and bridge 2D multiplane cel cuts into continuous, co-registered 3D walkable city blocks.
```

---

## 4. Key Directory & Asset Layout

- `index.html` — Central portal linking the 8 Atlantis Urbanism tools.
- `shots/pointcloud.html` — Three.js WebGL viewer for Point Clouds, Gaussian Splats, and Lego Architecture.
- `shots/build_polygonal_district.py` — Staging and procedural generation pipeline.
- `shots/batch_experiment3.py` — Parallel semantic shock-filtering script.
- `shots/out/districts/naraka_fused/` — Staged Naraka stairwell alleyway mesh, splats, and architecture.
- `shots/out/districts/haze_fused/` — Continuous 85m Orange Haze catwalk viaduct.
- `shots/out/districts/commons_fused/` — Sunken Agora, amphitheater tiers, and antenna masts.
- `WORLDBUILDING_TERMS_CODEX.md` — The master ontological worldbuilding codex for the universe.
