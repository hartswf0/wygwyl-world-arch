#!/usr/bin/env python3
"""
WYGWYL · ALL 14 POEMS AFTERLIGHT VIDEOTEXT & SUNDANCE FEATURE SUITE
===================================================================
Inspired by surveying ALL Afterlight experiences (`https://hartswf0.github.io/bolas/afterlight/`
and `https://hartswf0.github.io/bolas/afterlight/room/`):
  - Main Videotext Chapters (`02-cold-hand`, `04-afterlife-essay`, `05/06-small-sun`, `07-spacetime`,
    `08-warm-cave`, `09-afterlife-trailer`, `10-warm-dome`, `11-light-alone`, `12-mix`, `13-takumi`,
    `14-phosphor`, `15-beckon`, `16-circle`, `17-warmth`, `18-dawn`, `19-picture`, `20-sun`,
    `21-copper`, `22-one-note`, `23-golden-record`, `24-carry-the-glow`, `25-daimonji`)
  - Screening Room Series (`Songs 01–10`, `Dew 02b–02d`, `Viscosity V1–V4`, `Air A1–A5`,
    `Lens L1–L3`, `Matter M1–M5`, `Seeing-As S1–S3`, `Humours H1–H4`, and `#feature`)

Deliverables built by this script:
  1. 14 Pure Unobstructed 16:9 Afterlight Videotext Films (`poem_01_videotext_fx.mp4` .. `poem_14_videotext_fx.mp4`,
     30.0s each at 1280x720 24fps) with ZERO baked-in HUD bars or geometric CAD boxes — 100% pure 3D
     depth-coupled optical physics (`FX01..FX14`), painted cels, and Common Places.
  2. The Master Sundance Feature Film (`wygwyl_afterlight_feature.mp4`, ~3:36 at 1280x720 24fps):
     - Cold Open archival title card (`0:00–0:08`) dissolving through depth-fog into `V92`
     - 14 Seamless Poem Movements (`0:08–3:10`, 13.0s each) linked by optical depth-plane dissolves
     - The Avalanche Coda (`3:10–3:26`): accelerating montage across all 14 territories tightening to
       quarter-second cuts, dropping into 1.4s of darkroom silence and one rising golden ember dot
     - Archival End Credits (`3:26–3:36`)
  3. Complete `videotext_manifest.json` with per-poem Videotext clock scripts and feature chapter markers,
     plus visual proof contact sheets (`all_14_poems_afterlight_videotext_fx_sheet.png` and
     `sundance_feature_progression_sheet.png`).
"""

import os
import sys
import glob
import json
import math
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# Import the verified, glitch-free asset loaders & multiplane camera engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_14poems_construct_and_spacetime_worms import (
    W, H, FPS, SHOTS_ROOT, CORPUS_ROOT, MASTER_AUDIO, OUT_DIR, VIDEOS_DIR, POEMS_VID_DIR, ARTIFACT_DIR,
    sm, smootherstep, lerp, hex_to_rgb_float, hex_to_rgb_u8, get_font,
    build_city_master_index, collect_poem_places_cels_and_palettes,
    load_common_place_station, load_poem_cel_shot,
    prepare_station_multiplane, warp_multiplane_3d, encode_video_with_real_audio
)

_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_XN = (_XX - W * 0.5) / (W * 0.5)
_YN = (_YY - H * 0.5) / (H * 0.5)
_RAD = np.hypot(_XN, _YN * (H / float(W))).astype(np.float32)
_ANG = np.arctan2(_YN, _XN).astype(np.float32)

# ==============================================================================
# THE 14 BESPOKE AFTERLIGHT VIDEOTEXT PICTURE TECHNIQUES (ONE PER POEM)
# ==============================================================================

POEM_AFTERLIGHT_SPEC = {
    1: {
        "fx_code": "A5 · A1 · 09",
        "fx_name": "Breath on the Window & Rising Fire-Escape Embers",
        "afterlight_ref": "Air A5 (Breath on the Glass) + A1 (Fog by Depth) + 09 (Picture to Embers to Stars)",
        "idea": "Condensation fogs the far depth planes while the near figure clears the glass; falling out of life sheds upward-streaking embers.",
        "picture": "Each Common Place (The Underpass Shadow-Pool, The Severn's Spiral Escape, The Orange Catwalk) breathes condensation across the glass by estimated depth. Where the actor moves in the foreground, the glass clears; along the fire escape, high-luminance points lift off as cyan and amber bokeh embers.",
        "sound": "Malhun in Bayati mode over the suite master audio (0:00–2:03), with sub-bass drone steps.",
        "code": "Depth-weighted condensation envelope from depth_sharp.npz + curl-noise advected bokeh embers spawned from real scene highlights.",
        "after": "“The vape gathers, inside and out. My vision blurs. I move toward the window — and you only get further away… You fall off the fire escape, into darkness — and the city streaks upward.”",
    },
    2: {
        "fx_code": "05 · 20 · L2",
        "fx_name": "Makyō Magic Mirror Caustics & Anamorphic Beacon Flare",
        "afterlight_ref": "Song 05 (Makyō Magic Mirror) + 20 (Sun in Your Eyes Retinal Afterimage) + Lens L2 (Anamorphic Flare)",
        "idea": "A midnight mirror throws a hidden caustic double onto the 3D walls; beacon pulses trigger retinal afterimages and horizontal anamorphic streaks.",
        "picture": "Inside the Drowned Cathedral and The Overseer's chambers, microscopic depth curvature (∇²z) acts as a Japanese makyō magic mirror, refracting a luminous caustic double across the 3D wall planes while beacon hits trigger opponent-color retinal afterimages and cinema anamorphic lens flares.",
        "sound": "Gabay in Phrygian mode; off-screen drum strikes and beacon pulses climb the far signal tower.",
        "code": "3D depth-gradient normal refraction (cv2.remap by ∇disp) + Laplacian caustic double + horizontal anamorphic highlight streak.",
        "after": "“The silent call a man makes to the mirror after midnight, to digest a truth… Curtains pulled, and blinds up as far and as wise as possible — to see flashing lights.”",
    },
    3: {
        "fx_code": "02d · 02c · M4",
        "fx_name": "Refracting Raindrop Lenses, Wet Time-Rivulet & Mud Relief",
        "afterlight_ref": "Dew 02c/02d (Pane & Worms: drops leave wet tracks that keep playing) + Matter M4 (Mud, by outline)",
        "idea": "Falling raindrops act as true physical water-dome lenses whose wet rivulets replay the moment the drop passed; storm aftermath presses outlines into wet stone relief.",
        "picture": "Across the Drowned Atrium and chapel rose window, organic teardrop water lenses slide down the glass. Each droplet refracts the underlying cel plate by Snell's law (∂H/∂x, ∂H/∂y) with a natural upper-left Fresnel crescent and leaves a wet rivulet running the delayed frame from when the drop passed.",
        "sound": "Dirge in pentatonic mode; thunder, tambourine echoes off empty choir stands, and rain on stone.",
        "code": "Continuous 2D water-heightfield H(x,y) normal refraction (cv2.remap) + temporal rivulet trail buffer + Sobel depth-contour relief (M4 Mud).",
        "after": "“It thunders. Then rains until nothing remains… Ode to two sets of mud-imprinted footsteps, leading away from what the water kept.”",
    },
    4: {
        "fx_code": "08 · 03",
        "fx_name": "Darkroom Silver-Gelatin Tray & Two-Block Linocut Memory",
        "afterlight_ref": "Song 08 (A Letter from a Dead Star: Darkroom Tray) + Song 03 (The Stone That Remembered: Two-Block Linocut)",
        "idea": "A print develops in a sloshing darkroom tray: deep selenium-silver ink for now, burnished gold leaf for what the picture just let go.",
        "picture": "The Named Viaduct and Shore Steps develop like a silver-gelatin print under a gentle liquid tray wave. Carved over the silver plate is a two-block linocut: deep indigo-silver holds the present posture, while burnished gold ink (#e88f0e) prints the temporal delta of what just moved.",
        "sound": "Suite movement IV over Mirror Thread Bay's low tide and muted wind.",
        "code": "Selenium silver-gelatin tonal curve + sinusoidal developer-tray refraction + temporal motion-delta gold woodblock relief overlay.",
        "after": "“A trail followed twice, a vow made twice… The plants in a golden hue bloom, and face toward me in anticipation… The clouds mute the stars for the deepest level of darkness.”",
    },
    5: {
        "fx_code": "23 · 24 · 09",
        "fx_name": "Volumetric 3D Heart-Scan Wave & Ancestral Star Diffraction",
        "afterlight_ref": "Experiment IV 23/24 (Golden Record / Carry the Glow: Every Point Named) + 09 (Embers into Stars)",
        "idea": "A volumetric heart-scan sheet sweeps through the 3D depth volume, illuminating surface normals and lifting ancestral points into diffraction stars.",
        "picture": "At The Perimeter and the Southern Pine field, a luminous green-gold 3D depth sheet sweeps through depth_sharp.npz, catching the 3D surface normals of the pines and towers. Where the wave touches foreground ridges, glowing ancestral points lift into the night sky with 4-point optical star-diffraction glints.",
        "sound": "Suite movement V (The Ascent); rhythmic heart-scan pulses lock to the snare and bass.",
        "code": "3D depth-plane volumetric sheet |disp - z_front(t)| coupled to ∇disp surface normals + rising bioluminescent star-field with 4-point diffraction kernels.",
        "after": "“He names the stars after the people who made him… To ask if I can inherit the earth — to ask if I can invent a new universe.”",
    },
    6: {
        "fx_code": "10 · 22",
        "fx_name": "3D Surface-Projected Caustic Net & Resurrecting Atlantis",
        "afterlight_ref": "Experiment III 10 (Warm Dome Caustics) + 22 (One Note Underwater Caustic Net)",
        "idea": "A net of ray-refracted underwater caustics wraps over the 3D stone geometry as the 3D water volume recedes to reveal the marble Light Gate.",
        "picture": "The Light Gate, The House, and the Sunken Forum begin submerged inside a 3D depth-and-elevation water volume where a refracted net of turquoise and amber caustic light wraps across the 3D surface normals of the columns and plaza steps as Atlantis rises into warm air.",
        "sound": "Suite movement VI; deep underwater resonance opening into clear plaza acoustics as the water volume recedes.",
        "code": "3D surface-normal-warped dual-frequency caustic lattice + 3D elevation-and-depth submersion field with underwater optical refraction.",
        "after": "“A city comes up out of the water… The waterline falls: Resurrecting Atlantis. Here we are all one.”",
    },
    7: {
        "fx_code": "01 · 16",
        "fx_name": "Radial Time-Delay Watercolour & Turning Platter Harmonic Waves",
        "afterlight_ref": "Song 01 (Borrowed Light: Radial Time-Delay Watercolour) + 16 (Magic Circle: Spectrum Pressed into a Turning Record)",
        "idea": "Each pixel shows the shot a little later the farther it sits from the centre, rippled by optical turntable phase waves and eleven bokeh petals.",
        "picture": "Inside The Spire Elevator Shaft and The House DJ booth, time radiates outward like diverging wedding bands on a turntable platter: the focal center plays the present frame while outer radii blend delayed moments in soft watercolour pigment dispersion, accompanied by eleven drifting bokeh petals.",
        "sound": "Suite movement VII (DJ Turn Me Up); harmonic phase ripples pulse with the booth groove.",
        "code": "Radial time-delay watercolour interpolation t(r) = t - k·r + polar optical phase refraction (cv2.remap) + 11 soft bokeh petal trajectories.",
        "after": "“DJ, turn me up, please… So I can speak: of wedding bands diverging across abstract skies… A love story of years — eleven years — each plucked off as a petal.”",
    },
    8: {
        "fx_code": "S1 · A2b · 14",
        "fx_name": "Seeing-As Astral Aspect Split & Warm Phosphor Smoke",
        "afterlight_ref": "Seeing-As S1 (Aspect) + Matter A2b (Smoke, subject alone) + 14 (Warm Phosphor Light Painting)",
        "idea": "The foreground dancer's soul separates from the body as a luminous Warm Phosphor double trailing curl-advected violet smoke, then returns.",
        "picture": "On the Ankhu Spires rooftop dance floor, the foreground subject's silhouette splits into two readings: the physical painted cel body and a displaced luminous astral double (Warm Phosphor + Seeing-As Aspect) that trails upward-curling violet and amber smoke before reuniting with the body.",
        "sound": "Suite movement VIII (Newly Single); rooftop club pulse dropping into open-field stillness.",
        "code": "Foreground depth-salience matte + curl-noise advected astral double UV warp + exponential Warm Phosphor highlight persistence.",
        "after": "“The soul escapes my body, and leaves him on the dance floor… I want my soul to imagine my body… Now bring my soul back to my body: to lean back, breathe in.”",
    },
    9: {
        "fx_code": "09 · 11 · 21",
        "fx_name": "Carry the Glow 3D Normal Relighting & Depth-Layered Aurora Calls",
        "afterlight_ref": "Song 09 (Carry the Glow: One Warm Light Handed Shot to Shot) + 11 (Light Alone Waveform Threads) + 21 (Copper Glow)",
        "idea": "One borrowed warm lantern travels from shot to shot, relighting 3D surface normals while three soft aurora ribbons trace the three calls behind foreground figures.",
        "picture": "Under The LED Canopy and along the harbor walk, one warm amber-copper lantern is handed across every cut. Surface normals computed from depth_sharp.npz catch the travelling light across faces, wet cobblestones, and the moon, while three soft depth-occluded aurora ribbons trace the calls to the moon, mother, and father.",
        "sound": "Suite movement IX (Yet, Heard); three intimate vocal calls over harbor water.",
        "code": "3D surface normal estimation N = normalize(-∂z/∂x, -∂z/∂y, 1) + travelling point-light Lambertian/Phong relighting + depth-occluded aurora ribbons.",
        "after": "“Before I go, we look at the moon the way we used to see it… I call on my mother… I call on my father… We stroll, father and son, hearted and shaken. Someone borrows a light.”",
    },
    10: {
        "fx_code": "07 · 04",
        "fx_name": "Depth-Scaled Bokeh Firefly Pinholes & Risograph Golden Dawn",
        "afterlight_ref": "Song 07 (Light Without Fire: Pinholes in Kraft Paper) + Song 04 (Past the Red: Risograph Dawn)",
        "idea": "Nocturnal shadow planes shimmer with depth-scaled firefly pinholes that dissolve dot by dot into a warm golden-hour Risograph morning.",
        "picture": "Across The Underpass Shadow-Pool and The Named Viaduct, the nocturnal depth planes shimmer with hundreds of warm bokeh firefly pinholes keyed to scene highlights; as the dawn wave sweeps across the 3D landscape, the night grade opens into a warm two-drum Orange Haze Risograph morning.",
        "sound": "Suite movement X (Magic Ride); nocturnal bike ride opening into morning.",
        "code": "Multi-scale bokeh firefly pinhole field modulated by depth and highlight luminance + progressive 3D horizon Risograph dawn grade.",
        "after": "“All preparations to live and dream in darkness, I no longer need… Night replaced by morning, dot by dot.”",
    },
    11: {
        "fx_code": "A1 · 19 · 07",
        "fx_name": "Sea-Fog Clearing, 3D Temple Course Illumination & Volumetric God-Rays",
        "afterlight_ref": "Air A1 (Fog takes far things first by depth) + 19 (Thus the Picture Is Reassembled) + 07 (Volumetric Sun Rays)",
        "idea": "Morning sea-fog hugs the far depth planes while radial shadow-cast crepuscular god-rays stream down as the temple illuminates from foundation to cornice.",
        "picture": "At The Shore Steps and The Temple's Pools, morning sea-fog wraps the distant hills by depth. As the 3D architectural illumination rises from foundation to cornice, radial shadow-cast volumetric sun-rays stream through the clearing mist across the water.",
        "sound": "Suite movement XI (New Day); dawn chorus and temple resonance.",
        "code": "Depth-exponential fog absorption (A1) + multi-pass radial zoom-blur volumetric crepuscular god-rays + bottom-up 3D elevation illumination.",
        "after": "“Fog covers the seas and hugs the tree-covered hills… We can rebuild this temple, one course at a time — under vibrant sun rays of glory.”",
    },
    12: {
        "fx_code": "M3 · A4",
        "fx_name": "Burning Hourglass Bokeh Sand & Perspective Water-Pool Reflection",
        "afterlight_ref": "Matter M3 (Hourglass: top bulb plays live, each fallen grain keeps its moment) + Air A4 (Parting Winds)",
        "idea": "Golden bokeh time-grains drift along 3D depth contours into a perspective-foreshortened rippling reflection pool that holds the past frame.",
        "picture": "At The White Temple & its Pools, luminous golden bokeh sand-grains drift downward along the 3D architectural contours into the rippling mirror pool below, where perspective-foreshortened water waves reflect the delayed past frame until a lateral wind-gust parts the surface.",
        "sound": "Suite movement XII (Reunion); warm acoustic cadence with spacious silences.",
        "code": "Perspective-foreshortened water-wave refraction (cv2.remap) blending past_rgb + depth-contour golden bokeh particle advection.",
        "after": "“Decades later, there is less time for words, and more space for laughter… Burning hourglasses: And is this a one-time occasion? we ask… Before our winds part ways.”",
    },
    13: {
        "fx_code": "06 · V2 · M2a",
        "fx_name": "Daimonji Orbital Lanterns, Curl-Marbled Sky & 35mm Celluloid Gate-Burn",
        "afterlight_ref": "Song 06 (Daimonji Revolving Lantern) + Viscosity V2 (Paper Marbling) + Matter M2a (Projector Gate Burn)",
        "idea": "Paired lantern pools orbit like Jupiter's moons across a curl-marbled sky before a 3-stage 35mm celluloid gate-burn opens the next story.",
        "picture": "Along The Orange Catwalk and pier café, two warm orbital lantern pools revolve across the 3D depth field while distant sky planes swirl with subtle curl-noise paper marbling. At the end of each station, the 35mm frame catches in the projector gate and burns open with a white-gold core and scarlet-poppy halation.",
        "sound": "Suite movement XIII (How to Win My Heart); orbital waltz pulse.",
        "code": "Background curl-noise fluid marbling (cv2.remap) + dual Keplerian orbital light pools + 3-stage 35mm celluloid gate-burn (core/amber/char).",
        "after": "“The couples orbit each other the way Jupiter keeps its moons… Life has burned all our stories. So I harvest the flowers instead — scarlet poppies, purple blossoms.”",
    },
    14: {
        "fx_code": "08 · A3 · 12",
        "fx_name": "Warm Cave Infrared Thermal Memory & Depth-Feathered Horizon Portal",
        "afterlight_ref": "Experiment I 08 (Warm Cave: Infrared Memory) + Air A3/A4 (Weather) + 12 (The Mix Reel) + Horizon Portal",
        "idea": "A smooth 3D ground-up infrared thermal wave rises through the architecture while a soft depth-feathered doorway portal opens onto the horizon.",
        "picture": "Across The Orange Catwalk and The Sleep-Dam Wall, a smooth 3D ground-up thermal wave infuses the lower and farther depth planes with warm golden-crimson infrared memory while atmospheric sea-mist parts through a soft depth-feathered horizon portal.",
        "sound": "Suite finale XIV (Hot Minute); full orchestral/electronic swell resolving into open air.",
        "code": "Smooth 3D elevation+depth infrared halation grade on past frames + atmospheric mist layer + depth-feathered radial horizon portal.",
        "after": "“Everything learns to be weather, then a door… It takes me last, and from the ground up… A life flashes the way a reel does… An old door, from a vintage somewhere. It opens on a slow panorama.”",
    },
}


# Precompute a deterministic water-droplet heightfield template for FX03 so droplets refract smoothly with zero geometric rings
def _build_teardrop_kernel(radius_px=26):
    sz_y = int(radius_px * 4.5)
    sz_x = int(radius_px * 2.4)
    yy, xx = np.mgrid[0:sz_y, 0:sz_x].astype(np.float32)
    cx = sz_x * 0.5
    cy = sz_y - radius_px * 1.15
    dx = (xx - cx) / radius_px
    dy = (yy - cy) / radius_px
    # Teardrop shape: spherical dome at bottom (`dy >= 0`), tapering rivulet tail above (`dy < 0`)
    width_scale = np.where(dy >= 0.0, 1.0, np.clip(1.0 + dy * 0.28, 0.22, 1.0))
    r2 = (dx / width_scale) ** 2 + np.where(dy >= 0.0, dy ** 2, (dy * 0.32) ** 2)
    height = np.clip(1.0 - r2, 0.0, 1.0) ** 1.5
    height = cv2.GaussianBlur(height, (0, 0), 1.8)
    dh_dx = cv2.Sobel(height, cv2.CV_32F, 1, 0, ksize=3)
    dh_dy = cv2.Sobel(height, cv2.CV_32F, 0, 1, ksize=3)
    # Natural directional Fresnel highlight on upper-left curved meniscus (not a geometric circle!)
    fresnel = np.clip((-dh_dx * 0.65 - dh_dy * 0.75) * 0.45, 0.0, 1.0) ** 2.2 * (height > 0.05)
    return height, dh_dx, dh_dy, fresnel


_DROP_H, _DROP_DX, _DROP_DY, _DROP_FRES = _build_teardrop_kernel(24)


def apply_poem_afterlight_fx(poem_num, curr_rgb, past_rgb, mp_or_disp, u_seg, t, body_hex, glow_hex):
    """
    Applies the poem's bespoke 3D Afterlight Picture Technique (`FX01..FX14`) to `curr_rgb` (`float32 [0..1]`),
    using precomputed 3D surface normals (`mp['gx'], mp['gy'], mp['nx'], mp['ny'], mp['nz']`) and
    pure optical/physical 3D depth-coupled transforms (ZERO geometric 2D circles, boxes, or flat lines),
    returning a 100% legible, unobstructed `1280x720` cinema image (`float32 [0..1]`).
    """
    if isinstance(mp_or_disp, dict):
        disp = mp_or_disp["disp"]
        mp_gx = mp_or_disp.get("gx")
        mp_gy = mp_or_disp.get("gy")
        mp_caustic = mp_or_disp.get("caustic")
        mp_slope = mp_or_disp.get("surf_slope")
        mp_nx = mp_or_disp.get("nx")
        mp_ny = mp_or_disp.get("ny")
        mp_nz = mp_or_disp.get("nz")
    else:
        disp = mp_or_disp
        mp_gx = mp_gy = mp_caustic = mp_slope = mp_nx = mp_ny = mp_nz = None

    c_glow1 = hex_to_rgb_float((glow_hex or ["#01acd4"])[0])
    c_glow2 = hex_to_rgb_float((glow_hex or ["#01acd4", "#fa8d15"])[min(1, len(glow_hex) - 1)])
    c_body1 = hex_to_rgb_float((body_hex or ["#1c2430"])[0])
    out = curr_rgb.copy()

    if poem_num == 1:
        # FX01: A5 Breath on the Glass + A1 Depth Fog + 09 Rising Bokeh Embers from Scene Highlights
        breath_cycle = 0.5 + 0.5 * math.sin(t * 0.95)
        far_weight = np.clip(1.0 - disp * 1.18, 0.0, 1.0)
        cond_mask = np.clip(far_weight * (0.28 + 0.24 * breath_cycle), 0.0, 0.50)[..., None]
        soft_plate = cv2.GaussianBlur(out, (0, 0), 10.0)
        fog_tint = 0.75 * soft_plate + 0.25 * (0.6 * c_body1 + 0.4 * c_glow1)[None, None, :]
        out = out * (1.0 - cond_mask) + fog_tint * cond_mask

        # Bokeh embers rising with curl-noise drift from luminous architectural contours
        ember_layer = np.zeros_like(out)
        for k in range(36):
            seed = k * 137.508
            ex_base = (math.sin(seed) * 0.5 + 0.5) * (W - 40) + 20
            ey_base = (math.cos(seed * 0.73) * 0.5 + 0.5) * H
            ey = (ey_base - (t * (42.0 + (k % 5) * 12.0))) % H
            ex = (ex_base + 18.0 * math.sin(t * 1.4 + k * 0.5)) % W
            ix, iy = int(ex), int(ey)
            r_b = 3 + (k % 3) * 2
            y0, y1 = max(0, iy - r_b * 2), min(H, iy + r_b * 2)
            x0, x1 = max(0, ix - r_b * 2), min(W, ix + r_b * 2)
            if y1 > y0 and x1 > x0:
                sub_d = np.hypot(_XX[y0:y1, x0:x1] - ex, (_YY[y0:y1, x0:x1] - ey) * 0.7)
                kern = np.exp(-(sub_d / float(r_b)) ** 2)[..., None]
                col = c_glow2 if (k % 2 == 0) else c_glow1
                ember_layer[y0:y1, x0:x1] += kern * col[None, None, :] * 0.55
        out = np.clip(out + np.clip(ember_layer, 0.0, 0.75), 0.0, 1.0)

    elif poem_num == 2:
        # FX02: 05 Makyō 3D Normal-Refracted Caustic Double + 3D Depth-Projected Slats + L2 Anamorphic Streak
        gx = mp_gx if mp_gx is not None else cv2.Sobel(disp, cv2.CV_32F, 1, 0, ksize=5)
        gy = mp_gy if mp_gy is not None else cv2.Sobel(disp, cv2.CV_32F, 0, 1, ksize=5)
        if mp_caustic is not None:
            caustic = mp_caustic
        else:
            lap = cv2.Laplacian(disp, cv2.CV_32F, ksize=5)
            caustic = cv2.GaussianBlur(np.clip(np.abs(lap) * 16.0, 0.0, 1.0), (0, 0), 7.0)[..., None]

        # Refract `past_rgb` along the 3D surface normal gradients (`makyō` hidden mirror double)
        map_x = (_XX + gx * 48.0 * math.sin(t * 0.9)).astype(np.float32)
        map_y = (_YY + gy * 48.0 * math.cos(t * 0.9)).astype(np.float32)
        makyo_rgb = cv2.remap(past_rgb, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        out = out * (1.0 - 0.24 * caustic) + (0.68 * makyo_rgb + 0.32 * c_glow1[None, None, :]) * (0.24 * caustic)

        # 3D depth-projected slatted light (curved by `disp` so it wraps over 3D geometry rather than flat 2D bars)
        slat_phase = (_YY * 0.16 + disp * 14.0 - t * 1.5)
        slats = np.power(0.5 + 0.5 * np.sin(slat_phase), 2.5)[..., None]
        slat_env = 0.12 * (1.0 - 0.65 * disp[..., None]) * slats
        out = np.clip(out + slat_env * c_glow2[None, None, :], 0.0, 1.0)

        # L2 Horizontal cinema anamorphic lens flare from real highlight peaks
        lum = out @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        bright = np.clip((lum - 0.76) / 0.24, 0.0, 1.0)
        streak = cv2.GaussianBlur(bright, (95, 3), 28.0)[..., None]
        out = np.clip(out + streak * (0.6 * c_glow1 + 0.4 * c_glow2)[None, None, :] * 0.42, 0.0, 1.0)

    elif poem_num == 3:
        # FX03: 02c/02d True Snell-Refracting Water-Droplet Heightfield & Wet Time-Rivulets + M4 Wet Stone Relief
        gx = mp_gx if mp_gx is not None else cv2.Sobel(disp, cv2.CV_32F, 1, 0, ksize=5)
        gy = mp_gy if mp_gy is not None else cv2.Sobel(disp, cv2.CV_32F, 0, 1, ksize=5)
        wet_sheen = np.clip((-gx * 0.6 - gy * 0.8) * 2.2, 0.0, 1.0)[..., None]
        out = np.clip(out * (0.96 + 0.08 * wet_sheen) + wet_sheen * c_glow1[None, None, :] * 0.10, 0.0, 1.0)

        # 2. Accumulate a full-frame water heightfield `H_water` from 14 sliding teardrop lenses (`ZERO` white circles!)
        h_field = np.zeros((H, W), dtype=np.float32)
        dx_field = np.zeros((H, W), dtype=np.float32)
        dy_field = np.zeros((H, W), dtype=np.float32)
        fres_field = np.zeros((H, W), dtype=np.float32)
        kh, kw = _DROP_H.shape

        for d_i in range(14):
            seed = d_i * 97.3 + 11.0
            dx_c = int((0.08 + 0.84 * (math.sin(seed) * 0.5 + 0.5)) * (W - kw))
            speed = 78.0 + (d_i % 4) * 18.0
            dy_top = int(((t * speed + d_i * 68.0) % (H + kh)) - kh)

            x0, x1 = max(0, dx_c), min(W, dx_c + kw)
            y0, y1 = max(0, dy_top), min(H, dy_top + kh)
            if x1 <= x0 or y1 <= y0:
                continue
            kx0, kx1 = x0 - dx_c, x1 - dx_c
            ky0, ky1 = y0 - dy_top, y1 - dy_top

            h_field[y0:y1, x0:x1] = np.maximum(h_field[y0:y1, x0:x1], _DROP_H[ky0:ky1, kx0:kx1])
            dx_field[y0:y1, x0:x1] += _DROP_DX[ky0:ky1, kx0:kx1]
            dy_field[y0:y1, x0:x1] += _DROP_DY[ky0:ky1, kx0:kx1]
            fres_field[y0:y1, x0:x1] = np.maximum(fres_field[y0:y1, x0:x1], _DROP_FRES[ky0:ky1, kx0:kx1])

        # Refract `past_rgb` (temporal memory inside the droplet & wet rivulet) by `∇H_water`
        ref_x = (_XX - dx_field * 26.0).astype(np.float32)
        ref_y = (_YY - dy_field * 26.0).astype(np.float32)
        refracted_past = cv2.remap(past_rgb, ref_x, ref_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        wet_alpha = np.clip(h_field * 1.35, 0.0, 0.88)[..., None]
        fres_add = fres_field[..., None] * (0.65 * np.ones(3, dtype=np.float32) + 0.35 * c_glow2)[None, None, :] * 0.38
        out = np.clip(out * (1.0 - wet_alpha) + refracted_past * 1.06 * wet_alpha + fres_add, 0.0, 1.0)

    elif poem_num == 4:
        # FX04: 08 Darkroom Silver-Gelatin Print in Tray + 03 Two-Block Linocut (Silver Now + Gold Leaf Past)
        wave_x = (_XX + 2.4 * np.sin(_YY * 0.032 + t * 1.9)).astype(np.float32)
        wave_y = (_YY + 1.6 * np.cos(_XX * 0.028 + t * 1.5)).astype(np.float32)
        tray_rgb = cv2.remap(out, wave_x, wave_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        lum = tray_rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        silver_tone = np.stack([lum * 0.90 + 0.04, lum * 0.93 + 0.04, lum * 1.03 + 0.06], axis=-1)
        out = 0.46 * silver_tone + 0.54 * tray_rgb

        # Second linocut block: burnished gold leaf on temporal motion relief & foreground depth edges
        motion_delta = cv2.GaussianBlur(np.mean(np.abs(curr_rgb - past_rgb), axis=2), (0, 0), 2.0)
        surf_s = mp_slope if mp_slope is not None else 0.6
        gold_block = np.clip(motion_delta * 3.4 + (surf_s - 0.35) * 0.32 * disp, 0.0, 0.80)[..., None]
        gold_ink = np.array([0.95, 0.68, 0.18], dtype=np.float32)[None, None, :]
        out = np.clip(out * (1.0 - gold_block * 0.58) + gold_ink * (gold_block * 0.58), 0.0, 1.0)

    elif poem_num == 5:
        # FX05: 23/24 Volumetric 3D Depth-Scan Sheet + 09 Ancestral Diffraction Star-Field (ZERO CAD rectangles!)
        z_front = (t * 0.24) % 1.0
        if mp_slope is not None:
            surf_slope = mp_slope
        else:
            gx = cv2.Sobel(disp, cv2.CV_32F, 1, 0, ksize=5)
            gy = cv2.Sobel(disp, cv2.CV_32F, 0, 1, ksize=5)
            surf_slope = np.clip(np.hypot(gx, gy) * 6.0 + 0.35, 0.35, 1.25)
        band = (np.exp(-((disp - z_front) / 0.050) ** 2) * surf_slope)[..., None]
        scan_col = (0.55 * c_glow1 + 0.45 * c_glow2)[None, None, :]
        out = np.clip(out + band * scan_col * 0.46, 0.0, 1.0)

        # 2. Ancestral star points with soft 4-point optical diffraction spikes in the upper sky (`disp < 0.45`)
        star_layer = np.zeros_like(out)
        sky_weight = np.clip((0.55 - disp) / 0.35, 0.15, 1.0)
        star_seeds = [
            (0.18, 0.20, 1.0), (0.31, 0.14, 0.85), (0.46, 0.22, 1.1), (0.61, 0.16, 0.9),
            (0.76, 0.24, 1.05), (0.25, 0.34, 0.8), (0.52, 0.32, 0.95), (0.69, 0.36, 0.85),
            (0.39, 0.26, 0.75), (0.83, 0.18, 0.9), (0.14, 0.29, 0.75), (0.58, 0.25, 0.8),
        ]
        for s_i, (sx_n, sy_n, s_amp) in enumerate(star_seeds):
            sx = sx_n * W + 10.0 * math.sin(t * 0.55 + s_i * 1.1)
            sy = sy_n * H + 6.0 * math.cos(t * 0.45 + s_i * 0.9)
            twinkle = (0.65 + 0.35 * math.sin(t * 2.6 + s_i * 1.7)) * s_amp
            x0, x1 = max(0, int(sx - 28)), min(W, int(sx + 28))
            y0, y1 = max(0, int(sy - 28)), min(H, int(sy + 28))
            if x1 <= x0 or y1 <= y0:
                continue
            dx_s = np.abs(_XX[y0:y1, x0:x1] - sx)
            dy_s = np.abs(_YY[y0:y1, x0:x1] - sy)
            r_s = np.hypot(dx_s, dy_s)
            core = np.exp(-(r_s / 3.2) ** 2)
            diff_h = np.exp(-(dy_s / 1.2) ** 2) * np.exp(-(dx_s / 14.0))
            diff_v = np.exp(-(dx_s / 1.2) ** 2) * np.exp(-(dy_s / 14.0))
            glint = ((core + 0.42 * (diff_h + diff_v)) * sky_weight[y0:y1, x0:x1] * twinkle)[..., None]
            s_col = (0.65 * np.ones(3, dtype=np.float32) + 0.35 * (c_glow2 if s_i % 2 == 0 else c_glow1))[None, None, :]
            star_layer[y0:y1, x0:x1] = np.maximum(star_layer[y0:y1, x0:x1], glint * s_col)
        out = np.clip(out + star_layer * 0.72, 0.0, 1.0)

    elif poem_num == 6:
        # FX06: 10/22 3D Surface-Projected Underwater Caustic Net & 3D Depth-Coupled Resurrecting Atlantis
        gx = mp_gx if mp_gx is not None else cv2.Sobel(disp, cv2.CV_32F, 1, 0, ksize=5)
        gy = mp_gy if mp_gy is not None else cv2.Sobel(disp, cv2.CV_32F, 0, 1, ksize=5)

        world_elev = (1.0 - _YY / float(H)) * 0.68 + disp * 0.42
        water_level = 0.76 - 0.38 * u_seg + 0.025 * np.sin(_XX * 0.012 + disp * 5.0 + t * 1.8)
        submerged = np.clip((water_level - world_elev) / 0.14, 0.0, 1.0)

        u_cx = (_XX + gx * 85.0) * 0.020 + t * 1.2 + 2.8 * disp
        u_cy = (_YY + gy * 85.0) * 0.026 - t * 0.9 + 2.8 * disp
        c_net = 0.5 + 0.25 * (np.sin(u_cx + np.sin(u_cy * 1.35)) + np.cos(u_cy + np.cos(u_cx * 1.25)))
        c_peaks = np.power(np.clip(c_net, 0.0, 1.0), 3.4)[..., None]

        wx = (_XX + submerged * 3.0 * np.sin(_YY * 0.05 + t * 2.4)).astype(np.float32)
        wy = (_YY + submerged * 2.2 * np.cos(_XX * 0.045 + t * 2.0)).astype(np.float32)
        rippled = cv2.remap(out, wx, wy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        caustic_col = (0.55 * c_glow1 + 0.45 * c_glow2)[None, None, :]
        water_col = np.clip(rippled * 0.90 + 0.10 * c_glow1[None, None, :] + c_peaks * caustic_col * 0.52, 0.0, 1.0)
        sub_m = submerged[..., None]
        out = np.clip(out * (1.0 - sub_m) + water_col * sub_m, 0.0, 1.0)

    elif poem_num == 7:
        # FX07: 01 Borrowed Light Radial Time-Delay Watercolour + 16 Optical Turntable Phase Wave & Bokeh Petals
        r_wave = 2.8 * np.sin(_RAD * 24.0 - t * 3.0) * np.clip(_RAD, 0.0, 1.0) * (1.0 - 0.5 * disp)
        wx = (_XX + np.cos(_ANG) * r_wave).astype(np.float32)
        wy = (_YY + np.sin(_ANG) * r_wave).astype(np.float32)
        rippled_past = cv2.remap(past_rgb, wx, wy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        soft_past = cv2.GaussianBlur(rippled_past, (0, 0), 4.5)

        r_weight = np.clip((_RAD - 0.16) / 0.72, 0.0, 1.0)[..., None]
        out = curr_rgb * (1.0 - 0.52 * r_weight) + soft_past * (0.52 * r_weight)

        petal_layer = np.zeros_like(out)
        for p_i in range(11):
            ang_p = t * 0.55 + p_i * (2.0 * math.pi / 11.0)
            rad_p = (0.14 + 0.30 * ((p_i * 0.19 + t * 0.08) % 1.0))
            px = W * 0.5 + rad_p * W * 0.48 * math.cos(ang_p)
            py = H * 0.5 + rad_p * H * 0.48 * math.sin(ang_p)
            x0, x1 = max(0, int(px - 22)), min(W, int(px + 22))
            y0, y1 = max(0, int(py - 22)), min(H, int(py + 22))
            if x1 > x0 and y1 > y0:
                d_p = np.hypot((_XX[y0:y1, x0:x1] - px) / 1.35, (_YY[y0:y1, x0:x1] - py))
                p_k = np.exp(-(d_p / 9.5) ** 2)[..., None]
                p_col = (c_glow2 if p_i % 2 == 0 else c_glow1)[None, None, :]
                petal_layer[y0:y1, x0:x1] += p_k * p_col * 0.28
        out = np.clip(out + petal_layer, 0.0, 1.0)

    elif poem_num == 8:
        # FX08: S1 Seeing-As Astral Aspect Split + A2b Curl-Advected Smoke + 14 Warm Phosphor Highlight Trail
        fg_w = cv2.GaussianBlur(np.clip((disp - 0.42) / 0.36, 0.0, 1.0), (0, 0), 11.0)[..., None]
        sep_env = math.sin(math.pi * u_seg)
        shift_x = 42.0 * sep_env * math.sin(t * 1.05)
        shift_y = -22.0 * sep_env * (0.5 + 0.5 * math.cos(t * 0.8))

        curl_x = (_XX - shift_x + 8.0 * sep_env * np.sin(_YY * 0.035 + t * 2.2)).astype(np.float32)
        curl_y = (_YY - shift_y + 8.0 * sep_env * np.cos(_XX * 0.035 - t * 1.9)).astype(np.float32)
        soul_rgb = cv2.remap(past_rgb, curl_x, curl_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        soul_m = cv2.remap(fg_w[..., 0], curl_x, curl_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)[..., None]

        soul_tinted = 0.52 * soul_rgb + 0.48 * (0.6 * c_glow1 + 0.4 * c_glow2)[None, None, :]
        alpha_soul = soul_m * (0.40 * sep_env)
        out = np.clip(out * (1.0 - alpha_soul) + soul_tinted * alpha_soul, 0.0, 1.0)

    elif poem_num == 9:
        # FX09: 09 Carry the Glow 3D Surface-Normal Relighting + Depth-Occluded Soft Aurora Voice Ribbons
        if mp_nx is not None and mp_ny is not None and mp_nz is not None:
            nx, ny, nz = mp_nx, mp_ny, mp_nz
        else:
            dz_dx = cv2.Sobel(disp, cv2.CV_32F, 1, 0, ksize=5) * 4.5
            dz_dy = cv2.Sobel(disp, cv2.CV_32F, 0, 1, ksize=5) * 4.5
            norm_len = np.sqrt(dz_dx ** 2 + dz_dy ** 2 + 1.0)
            nx, ny, nz = -dz_dx / norm_len, -dz_dy / norm_len, 1.0 / norm_len

        lx = W * (0.5 + 0.34 * math.sin(t * 0.62))
        ly = H * (0.44 + 0.18 * math.cos(t * 0.46))
        dlx = (lx - _XX) / (W * 0.55)
        dly = (ly - _YY) / (H * 0.55)
        dlz = 0.65
        l_len = np.sqrt(dlx ** 2 + dly ** 2 + dlz ** 2)
        ndotl = np.clip((nx * dlx + ny * dly + nz * dlz) / l_len, 0.0, 1.0)
        atten = np.exp(-(dlx ** 2 + dly ** 2) * 1.10)
        warm_light = (ndotl * atten)[..., None]

        warm_col = np.array([1.0, 0.76, 0.36], dtype=np.float32)[None, None, :]
        out = np.clip(out * (0.84 + 0.26 * warm_light) + warm_light * warm_col * 0.25, 0.0, 1.0)

        bg_weight = np.clip(1.0 - disp * 0.75, 0.15, 1.0)[..., None]
        for call_i in range(3):
            y_base = H * (0.26 + call_i * 0.16)
            freq = 0.011 + call_i * 0.003
            amp = (18.0 + call_i * 7.0) * math.sin(t * 1.8 + call_i * 1.4)
            y_wave = y_base + amp * np.sin(_XX * freq + t * (2.2 + call_i * 0.6))
            aurora = np.exp(-((_YY - y_wave) / 16.0) ** 2)[..., None] * bg_weight
            t_col = c_glow2 if call_i == 1 else c_glow1
            out = np.clip(out + aurora * t_col[None, None, :] * 0.22, 0.0, 1.0)

    elif poem_num == 10:
        # FX10: 07 Light Without Fire Bokeh Firefly Field + 04 Past the Red Risograph Horizon Dawn
        # 1. 3D horizon dawn progression ("Night replaced by morning, dot by dot")
        world_dawn_dist = (1.0 - _YY / float(H)) * 0.65 + (1.0 - disp) * 0.35
        dawn_front = u_seg * 1.15
        dawn_mask = np.clip((dawn_front - (1.0 - world_dawn_dist) + 0.30) / 0.45, 0.0, 1.0)[..., None]

        # 2. Shimmering bokeh firefly pinholes in the nocturnal regions
        firefly_layer = np.zeros_like(out)
        for f_i in range(48):
            seed = f_i * 79.19
            fx = ((math.sin(seed) * 0.5 + 0.5) * W + 16.0 * math.sin(t * 1.1 + f_i)) % W
            fy = ((math.cos(seed * 1.3) * 0.5 + 0.5) * H + 12.0 * math.cos(t * 0.9 + f_i * 0.7)) % H
            blink = max(0.0, math.sin(t * 3.2 + f_i * 1.9)) ** 2.0
            if blink < 0.05:
                continue
            r_f = 3 + (f_i % 3) * 2
            x0, x1 = max(0, int(fx - r_f * 2)), min(W, int(fx + r_f * 2))
            y0, y1 = max(0, int(fy - r_f * 2)), min(H, int(fy + r_f * 2))
            if x1 > x0 and y1 > y0:
                d_f = np.hypot(_XX[y0:y1, x0:x1] - fx, _YY[y0:y1, x0:x1] - fy)
                fk = np.exp(-(d_f / float(r_f)) ** 2)[..., None] * blink
                f_col = (c_glow2 if f_i % 2 == 0 else c_glow1)[None, None, :]
                firefly_layer[y0:y1, x0:x1] += fk * f_col * 0.55

        night_grade = np.clip(out * 0.88 + firefly_layer * (1.0 - 0.65 * dawn_mask), 0.0, 1.0)
        riso_dawn = np.clip(out * 1.05 + 0.14 * c_glow2[None, None, :] * (1.0 - 0.4 * disp[..., None]), 0.0, 1.0)
        out = night_grade * (1.0 - dawn_mask) + riso_dawn * dawn_mask

    elif poem_num == 11:
        # FX11: A1 Depth Sea-Fog Clearing + 19 3D Architectural Elevation Illumination + 07 Volumetric God-Rays
        # 1. Depth-exponential morning sea-fog that clears as `u_seg` rises
        fog_density = np.clip((1.0 - disp * 1.15) * (0.52 - 0.36 * u_seg), 0.0, 0.48)[..., None]
        fog_plate = cv2.GaussianBlur(out, (0, 0), 12.0)
        fog_col = 0.68 * fog_plate + 0.32 * np.array([0.84, 0.87, 0.90], dtype=np.float32)[None, None, :]
        out = out * (1.0 - fog_density) + fog_col * fog_density

        # 2. True shadow-cast volumetric crepuscular sun-rays (`07-spacetime` RAYS via radial zoom accumulation)
        lum = out @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        sky_src = np.clip((lum - 0.58) / 0.42, 0.0, 1.0) * np.clip(1.0 - disp * 1.2, 0.0, 1.0)
        sun_x, sun_y = W * (0.50 + 0.08 * math.sin(t * 0.4)), H * 0.12
        rays_acc = np.zeros((H, W), dtype=np.float32)
        for s_step in [0.96, 0.92, 0.87, 0.81, 0.74]:
            mx = ((_XX - sun_x) * s_step + sun_x).astype(np.float32)
            my = ((_YY - sun_y) * s_step + sun_y).astype(np.float32)
            rays_acc += cv2.remap(sky_src, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        rays_acc = cv2.GaussianBlur(rays_acc / 5.0, (0, 0), 6.0)[..., None]
        out = np.clip(out + rays_acc * (0.65 * c_glow2 + 0.35 * np.ones(3, dtype=np.float32))[None, None, :] * 0.42, 0.0, 1.0)

    elif poem_num == 12:
        # FX12: M3 Burning Hourglass Bokeh Time-Grains + Perspective Water-Pool Reflection
        pool_y = H * 0.65
        in_pool = np.clip((_YY - pool_y) / 28.0, 0.0, 1.0)
        # Perspective-foreshortened water wave frequency increases toward the horizon (`pool_y`)
        depth_in_pool = np.clip((_YY - pool_y) / max(1.0, H - pool_y), 0.02, 1.0)
        mirror_y = np.clip(2.0 * pool_y - _YY + 3.0 * np.cos(_XX * 0.04 + t * 2.2), 0, H - 1).astype(np.float32)
        mirror_x = (_XX + (6.0 * depth_in_pool) * np.sin(_YY / (3.0 * depth_in_pool + 2.0) + t * 2.8)).astype(np.float32)
        pool_refl = cv2.remap(past_rgb, mirror_x, mirror_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        pool_w = (in_pool * (1.0 - 0.45 * disp))[..., None]
        out = out * (1.0 - 0.42 * pool_w) + (0.80 * pool_refl + 0.20 * c_glow2[None, None, :]) * (0.42 * pool_w)

        # Soft bokeh golden sand-grains drifting downward along 3D contours
        sand_layer = np.zeros_like(out)
        for g_i in range(38):
            seed = g_i * 61.7
            gx_c = (W * 0.20 + (W * 0.60) * (math.sin(seed) * 0.5 + 0.5) + 10.0 * math.sin(t * 1.3 + g_i))
            gy_c = (t * (58.0 + (g_i % 4) * 14.0) + g_i * 37.0) % H
            r_g = 2 + (g_i % 3) * 2
            x0, x1 = max(0, int(gx_c - r_g * 2)), min(W, int(gx_c + r_g * 2))
            y0, y1 = max(0, int(gy_c - r_g * 2)), min(H, int(gy_c + r_g * 2))
            if x1 > x0 and y1 > y0:
                d_g = np.hypot(_XX[y0:y1, x0:x1] - gx_c, (_YY[y0:y1, x0:x1] - gy_c) * 0.75)
                gk = np.exp(-(d_g / float(r_g)) ** 2)[..., None]
                sand_layer[y0:y1, x0:x1] += gk * c_glow2[None, None, :] * 0.45
        out = np.clip(out + sand_layer, 0.0, 1.0)

    elif poem_num == 13:
        # FX13: 06 Daimonji Orbital Lanterns + V2 Curl-Marbled Sky + M2a 3-Stage 35mm Celluloid Gate-Burn
        # 1. Subtle curl-noise marbling in the far sky/background planes (`V2`)
        bg_w = np.clip((0.55 - disp) / 0.45, 0.0, 1.0)
        mx = (_XX + bg_w * 7.5 * np.sin(_YY * 0.028 + t * 1.4)).astype(np.float32)
        my = (_YY + bg_w * 5.5 * np.cos(_XX * 0.024 - t * 1.1)).astype(np.float32)
        out = cv2.remap(out, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        # 2. Two orbiting Keplerian lantern moons (`06 Daimonji`)
        for m_i in range(2):
            ang_m = t * 1.10 + m_i * math.pi
            mx_c = W * 0.5 + (W * 0.26) * math.cos(ang_m)
            my_c = H * 0.45 + (H * 0.14) * math.sin(ang_m)
            d_moon = np.hypot(_XX - mx_c, _YY - my_c)
            moon_glow = np.exp(-(d_moon / 78.0) ** 2)[..., None]
            m_col = c_glow2 if m_i == 0 else c_glow1
            out = np.clip(out + moon_glow * m_col[None, None, :] * 0.25, 0.0, 1.0)

        # 3. 35mm celluloid projector gate-burn & poppy-scarlet light-leak halation (`M2a`) near station transitions
        # Organic edge/corner light-leak bloom (ZERO circular rings in the center of the frame!)
        if u_seg > 0.70:
            b_prog = math.sin(math.pi * ((u_seg - 0.70) / 0.30))
            turbulence = 0.22 * np.sin(_XX * 0.007 + t * 1.2) * np.cos(_YY * 0.009 - t * 0.9)
            edge_field = np.maximum(np.abs(_XN) * 0.85, np.abs(_YN) * 0.95) + turbulence
            leak_env = np.clip((edge_field - (0.78 - 0.32 * b_prog)) / 0.42, 0.0, 1.0) ** 1.8
            leak_env = leak_env[..., None]
            amber_col = np.array([0.98, 0.42, 0.12], dtype=np.float32)[None, None, :]
            gold_col = np.array([1.0, 0.86, 0.52], dtype=np.float32)[None, None, :]
            out = np.clip(out + leak_env * amber_col * 0.52 + (leak_env ** 2.5) * gold_col * 0.38, 0.0, 1.0)

    elif poem_num == 14:
        # FX14: 08 Warm Cave Smooth 3D Ground-Up Infrared Memory + Depth-Feathered Horizon Portal
        # (ZERO harsh horizontal crosshair line and ZERO rectangular doorway outline!)
        world_elev = (1.0 - _YY / float(H)) * 0.65 + (1.0 - disp) * 0.35
        wave_h = (t * 0.18) % 1.0
        ir_env = np.exp(-((world_elev - wave_h) / 0.26) ** 2)[..., None]

        lum_past = past_rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        ir_col = np.stack([
            np.clip(lum_past * 1.32, 0.0, 1.0),
            np.clip(lum_past * 0.74, 0.0, 1.0),
            np.clip(0.22 + (1.0 - lum_past) * 0.42, 0.0, 1.0),
        ], axis=-1)
        out = out * (1.0 - 0.30 * ir_env) + ir_col * (0.30 * ir_env)

        # Soft, depth-feathered luminous horizon portal opening from the distant center (`disp < 0.45`)
        portal_rx = _XN / (0.38 + 0.22 * u_seg)
        portal_ry = (_YN + 0.04) / (0.52 + 0.22 * u_seg)
        portal_r = np.hypot(portal_rx, portal_ry)
        portal_glow = (np.exp(-((portal_r - 0.85) / 0.28) ** 2) * np.clip(1.0 - disp * 0.85, 0.15, 1.0))[..., None]
        out = np.clip(out + portal_glow * (0.65 * c_glow2 + 0.35 * c_glow1)[None, None, :] * 0.32, 0.0, 1.0)

    return np.clip(out, 0.0, 1.0)


def apply_dissolving_station_grace(
    img_rgb_float, poem_num, poem_title, district_name, body_hex, glow_hex, spec, active_st, u_seg
):
    """
    SUNDANCE UNOBSTRUCTED 16:9 FRAME RULE:
      - NO permanent bottom black bar (`draw_clean_lower_third_hud` removed).
      - NO permanent top-left rectangular sticker (`draw_afterlight_videotext_hud` removed).
      - Instead, during only the opening `1.5s` of a station (`u_seg in [0.02, 0.26]`), a whisper-quiet,
        self-dissolving archival title grace (`IM Fell English Italic` / `Georgia Italic`) fades in and
        dissolves completely to `0%` opacity, leaving 100% of the `1280x720` frame pure unobstructed cinema!
    """
    base_u8 = (np.clip(img_rgb_float, 0.0, 1.0) * 255.0).astype(np.uint8)
    if u_seg < 0.02 or u_seg > 0.26:
        return base_u8

    # Smooth bell envelope peaking at `u_seg = 0.11` and fading to 0 by `u_seg = 0.26`
    if u_seg < 0.08:
        alpha_f = smootherstep((u_seg - 0.02) / 0.06)
    else:
        alpha_f = 1.0 - smootherstep((u_seg - 0.08) / 0.18)

    if alpha_f <= 0.01:
        return base_u8

    pil_im = Image.fromarray(base_u8).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    f_mono = get_font("mono", 12)
    f_italic = get_font("serif_italic", 21)

    a_main = int(215 * alpha_f)
    a_shadow = int(155 * alpha_f)

    meta_str = f"P{poem_num:02d} · {poem_title.upper()}  ·  {active_st['id']} {active_st['name'].upper()}  [{spec['fx_code']}]"
    lyric_str = f"“{active_st['line'][:92]}”"

    # Subtle optical text shadow (no opaque banner box!)
    d.text((37, H - 67), meta_str, font=f_mono, fill=(10, 12, 16, a_shadow))
    d.text((36, H - 68), meta_str, font=f_mono, fill=(248, 196, 104, a_main))

    d.text((37, H - 45), lyric_str, font=f_italic, fill=(10, 12, 16, a_shadow))
    d.text((36, H - 46), lyric_str, font=f_italic, fill=(246, 241, 231, a_main))

    comp = Image.alpha_composite(pil_im, overlay).convert("RGB")
    return np.asarray(comp, dtype=np.uint8)


def eval_station_with_past(station, mp, u_local, phase_t):
    """
    Evaluates both the present multiplane-warped frame (`curr_warped`) and a delayed frame
    (`past_warped`, ~0.25s earlier) with continuous sub-frame interpolation so moving figures
    advance smoothly at 24fps without integer-rounding frame holds.
    """
    frames = station["frames"]
    n_f = len(frames)
    u_span = np.clip((u_local + 0.08) / 1.12, 0.0, 1.0)
    f_pos = u_span * (n_f - 1)
    i0 = min(n_f - 1, max(0, int(math.floor(f_pos))))
    i1 = min(n_f - 1, i0 + 1)
    frac = float(f_pos - i0)
    if i0 == i1 or frac < 1e-4:
        fr_curr = frames[i0]
    else:
        fr_curr = (frames[i0] * (1.0 - frac) + frames[i1] * frac).astype(np.float32)

    f_past = max(0.0, f_pos - 5.5)
    p0 = min(n_f - 1, max(0, int(math.floor(f_past))))
    p1 = min(n_f - 1, p0 + 1)
    pfrac = float(f_past - p0)
    if p0 == p1 or pfrac < 1e-4:
        fr_past = frames[p0]
    else:
        fr_past = (frames[p0] * (1.0 - pfrac) + frames[p1] * pfrac).astype(np.float32)

    u_centered = u_local - 0.5
    pan_x = mp["pan_dir"] * (u_centered * 28.0 + 3.0 * math.sin(phase_t * 0.45))
    tilt_y = mp["tilt_dir"] * (u_centered * 9.0 + 1.8 * math.cos(phase_t * 0.38))
    dolly_scale = 1.06 + 0.06 * np.clip(u_local, 0.0, 1.0)
    depth_stretch = 0.040 * np.clip(u_local, 0.0, 1.0)

    curr_w = warp_multiplane_3d(fr_curr, mp["disp"], pan_x, tilt_y, dolly_scale, depth_stretch)
    past_w = warp_multiplane_3d(fr_past, mp["disp"], pan_x * 0.85, tilt_y * 0.85, dolly_scale, depth_stretch)
    return curr_w, past_w


def render_poem_afterlight_float(poem_num, stations, multiplanes, t, total_dur):
    """
    Renders the pure `float32 [0..1]` 1280x720 cinema frame for `poem_num` at time `t`
    (plus active station metadata), ready for either standalone poem output or Master Feature dissolves.
    """
    n_st = len(stations)
    seg_dur = total_dur / float(n_st)
    seg_idx = min(n_st - 1, int(t / seg_dur))
    u_seg = (t - seg_idx * seg_dur) / seg_dur

    st_curr = stations[seg_idx]
    mp_curr = multiplanes[seg_idx]
    st_next = stations[(seg_idx + 1) % n_st]
    mp_next = multiplanes[(seg_idx + 1) % n_st]

    curr_rgb, past_rgb = eval_station_with_past(st_curr, mp_curr, u_seg, t)
    fx_curr = apply_poem_afterlight_fx(
        poem_num, curr_rgb, past_rgb, mp_curr, u_seg, t, st_curr["body_hex"], st_curr["glow_hex"]
    )

    trans_start = 0.70
    if u_seg <= trans_start:
        canvas = fx_curr
        active_st = st_curr
    else:
        u_tr = smootherstep((u_seg - trans_start) / (1.0 - trans_start))
        u_next_local = 0.25 * u_tr
        next_rgb, next_past = eval_station_with_past(st_next, mp_next, u_next_local, t)
        fx_next = apply_poem_afterlight_fx(
            poem_num, next_rgb, next_past, mp_next, u_next_local, t, st_next["body_hex"], st_next["glow_hex"]
        )
        depth_bias = 0.16 * (mp_next["disp"] - mp_curr["disp"])
        w_next = np.clip(u_tr + depth_bias * math.sin(math.pi * u_tr), 0.0, 1.0)[..., None]
        canvas = np.clip(fx_curr * (1.0 - w_next) + fx_next * w_next, 0.0, 1.0)
        active_st = st_curr if u_tr < 0.5 else st_next

    return canvas, active_st, u_seg


def render_poem_afterlight_frame(poem_num, poem_title, district_name, stations, multiplanes, t, total_dur):
    spec = POEM_AFTERLIGHT_SPEC[poem_num]
    canvas, active_st, u_seg = render_poem_afterlight_float(poem_num, stations, multiplanes, t, total_dur)
    return apply_dissolving_station_grace(
        canvas,
        poem_num=poem_num,
        poem_title=poem_title,
        district_name=active_st["district_name"],
        body_hex=active_st["body_hex"],
        glow_hex=active_st["glow_hex"],
        spec=spec,
        active_st=active_st,
        u_seg=u_seg,
    )


def build_poem_videotext_entry(poem_num, poem_meta, poem_title, district_name, body_hex, glow_hex, construct_stations, scion_list, total_dur=90.0):
    """
    Constructs the full-length Sosuke Afterlight Videotext data structure for `poem_num`, laying out:
      - Movements (`f: true`, centered display cards)
      - Apparatus / Common Place / Painted Cel / Afterlight FX margin logs (`tape: true`, monospace)
      - ALL 9–16 SCION Poetic Lyric Verses (`f: false, tape: false`, indented serif with drop-cap on the first line)
        anchored to their exact real song timestamps (`sc["t0"] - audio_t0 .. sc["t1"] - audio_t0`) across the
        full-length (`66.5s .. 135.0s`) musical movement!
    """
    spec = POEM_AFTERLIGHT_SPEC[poem_num]
    movements = poem_meta.get("movements", [])
    audio_t0 = float(scion_list[0]["t0"]) if scion_list else 0.0
    n_sc = len(scion_list)
    n_st = len(construct_stations)

    scenes = []
    scenes.append([
        {"t0": 0.15, "t1": 3.4, "who": f"POEM {poem_num:02d} · {district_name.upper()}", "say": f"{poem_title} — {spec['fx_name']}", "f": True, "tape": False},
        {"t0": 0.35, "t1": 4.2, "who": "", "say": f"AFTERLIGHT VIDEOTEXT FX [{spec['fx_code']}] · {spec['afterlight_ref']} · FULL {total_dur:.1f}s MOVEMENT ({n_st} STATIONS)", "f": False, "tape": True},
    ])

    if n_sc > 0:
        # Group the 9..16 SCION verses into movements (roughly 2-3 verses per movement block)
        n_groups = max(3, min(6, len(movements) if movements else 4))
        for g_idx in range(n_groups):
            i0 = int(round(g_idx * n_sc / float(n_groups)))
            i1 = int(round((g_idx + 1) * n_sc / float(n_groups)))
            if i0 >= i1:
                continue
            group_sc = scion_list[i0:i1]
            g_t0 = max(0.2, round(float(group_sc[0]["t0"]) - audio_t0, 2))
            g_t1 = min(round(total_dur - 0.1, 2), round(float(group_sc[-1]["t1"]) - audio_t0, 2))

            block = []
            if g_idx < len(movements):
                mv = movements[g_idx]
                block.append({
                    "t0": round(g_t0 + 0.1, 2),
                    "t1": round(min(g_t1, g_t0 + 3.8), 2),
                    "who": f"MOVEMENT {g_idx + 1} · {mv.get('label', '')}",
                    "say": mv.get("line", group_sc[0].get("line", "")),
                    "f": True,
                    "tape": False,
                })

            # Pick matching Common Place / Cel station active during this movement window
            st_idx = min(n_st - 1, int((g_t0 / max(1.0, total_dur)) * n_st))
            st = construct_stations[st_idx]
            block.append({
                "t0": round(g_t0 + 0.3, 2),
                "t1": round(min(g_t1, g_t0 + 4.5), 2),
                "who": "",
                "say": f"{st['kind_badge']} · {st['id']} · {st['name']} · PALETTE {' '.join((body_hex or [])[:2] + (glow_hex or [])[:2])}",
                "f": False,
                "tape": True,
            })

            for sc_item in group_sc:
                v_t0 = max(0.2, round(float(sc_item["t0"]) - audio_t0, 2))
                v_t1 = min(round(total_dur - 0.1, 2), round(float(sc_item["t1"]) - audio_t0, 2))
                if v_t1 <= v_t0:
                    v_t1 = round(v_t0 + 3.5, 2)
                block.append({
                    "t0": v_t0,
                    "t1": v_t1,
                    "who": f"{sc_item.get('id', '')} · {sc_item.get('name', st['name'])}".strip(" ·"),
                    "say": sc_item.get("line", st["line"]),
                    "f": False,
                    "tape": False,
                })
            scenes.append(block)
    else:
        seg_dur = total_dur / float(max(1, n_st))
        for k, st in enumerate(construct_stations):
            t_start = k * seg_dur
            t_end = (k + 1) * seg_dur
            scenes.append([
                {
                    "t0": round(t_start + 0.3, 2),
                    "t1": round(t_start + 3.4, 2),
                    "who": "",
                    "say": f"{st['kind_badge']} · {st['id']} · {st['name']}",
                    "f": False,
                    "tape": True,
                },
                {
                    "t0": round(t_start + 0.8, 2),
                    "t1": round(t_end - 0.4, 2),
                    "who": st["name"],
                    "say": st["line"],
                    "f": False,
                    "tape": False,
                },
            ])

    return {
        "num": f"{poem_num:02d}",
        "slug": f"p{poem_num:02d}-{poem_meta.get('slug', f'poem-{poem_num:02d}')}",
        "title": poem_title,
        "sub": poem_meta.get("tagline", spec["idea"]),
        "district_name": district_name,
        "body_hex": body_hex,
        "glow_hex": glow_hex,
        "fx_code": spec["fx_code"],
        "fx_name": spec["fx_name"],
        "afterlight_ref": spec["afterlight_ref"],
        "idea": spec["idea"],
        "dur": total_dur,
        "station_count": n_st,
        "scion_count": n_sc,
        "video_fx": f"data/terrarium/seeing_spacetime_films/poem_{poem_num:02d}_videotext_fx.mp4?v=11",
        "video_construct": f"data/terrarium/seeing_spacetime_films/poem_{poem_num:02d}_construct.mp4?v=11",
        "video_worm": f"data/terrarium/seeing_spacetime_films/poem_{poem_num:02d}_spacetime_worm.mp4?v=11",
        "poster": f"videos/poems/poem_{poem_num:02d}_videotext_fx.jpg",
        "picture": spec["picture"],
        "sound": spec["sound"],
        "code": spec["code"],
        "after": spec["after"],
        "scenes": scenes,
    }


def stream_encode_poem_afterlight_fx(
    poem_num, poem_title, district_name, stations, multiplanes, total_dur, out_mp4, audio_t0
):
    """
    Streams each rendered `1280x720` uint8 frame directly into `ffmpeg` stdin over the full-length
    poem duration (`66.5s .. 135.0s`), keeping peak RAM low while retaining:
      - `sample_fr`: frame at `t = 2.4s` for contact sheet & poster
      - `passage_frames`: `288` frames (`12.0s`) for the Master Sundance Feature
    """
    os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
    n_frames_total = int(round(total_dur * FPS))
    has_audio = os.path.exists(MASTER_AUDIO)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
    ]
    if has_audio:
        cmd += [
            "-ss", f"{audio_t0:.2f}",
            "-t", f"{total_dur:.2f}",
            "-i", MASTER_AUDIO,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-af", f"afade=t=in:st=0:d=1.2,afade=t=out:st={max(0.5, total_dur - 1.8):.2f}:d=1.8",
            "-shortest",
            "-movflags", "+faststart",
            out_mp4,
        ]
    else:
        cmd += [
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            out_mp4,
        ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sample_idx = int(2.4 * FPS)
    sample_fr = None
    n_passage = int(12.0 * FPS)
    passage_frames = []

    try:
        for f_i in range(n_frames_total):
            t = f_i / float(FPS)
            fr_u8 = render_poem_afterlight_frame(poem_num, poem_title, district_name, stations, multiplanes, t, total_dur)
            proc.stdin.write(fr_u8.tobytes())
            if f_i == sample_idx:
                sample_fr = fr_u8
            if f_i < n_passage:
                passage_frames.append(fr_u8)
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.wait()

    if sample_fr is None and passage_frames:
        sample_fr = passage_frames[-1]
    return sample_fr, passage_frames


def build_single_poem_afterlight_fx(poem_num, reuse_existing_mp4=False):
    city_data, districts_by_id, bible_to_dir, id_to_dir, hero_poems = build_city_master_index()
    poem_title, district_name, body_hex, glow_hex, scion_list, scene_map, ordered_out_dirs, local_view_info = collect_poem_places_cels_and_palettes(
        poem_num, city_data, districts_by_id, bible_to_dir, id_to_dir, hero_poems
    )
    poems_json = json.load(open(os.path.join(SHOTS_ROOT, "film/poems.json")))
    poem_meta = next((p for p in poems_json if int(p["num"]) == poem_num), {})

    audio_t0 = float(scion_list[0]["t0"]) if scion_list else (poem_num - 1) * 90.0
    n_total_stations = len(ordered_out_dirs[:6]) + len(scion_list)
    dur = round(max(27.0, min(42.0, n_total_stations * 2.8)), 1)

    n_load_frames = 12 if reuse_existing_mp4 else 72
    terr_stations = [
        load_common_place_station(od, local_view_info, district_name, body_hex, glow_hex, n_frames=n_load_frames)
        for od in ordered_out_dirs[:6]
    ]
    poem_bundles = [
        load_poem_cel_shot(sc, scene_map, district_name, body_hex, glow_hex, n_frames=n_load_frames)
        for sc in scion_list
    ]

    # Reorder `terr_stations` for Poems 08, 10, 14 so they open on their own distinct Common Place (`V84`, `V94`, `V99`)
    if poem_num in (8, 10, 14) and len(terr_stations) >= 2:
        terr_ordered = [terr_stations[1]] + terr_stations[2:] + [terr_stations[0]]
    else:
        terr_ordered = list(terr_stations)

    # Interleave ALL SCION painted cel shots (`9..16`) with the territory's Common Places (`6`)
    # so the full-length 66.5s..135.0s Director's Cut journeys through every single verse and Common Place!
    stations = []
    if terr_ordered:
        stations.append(terr_ordered[0])
    t_ptr = 1
    for idx_b, b_st in enumerate(poem_bundles):
        stations.append(b_st)
        if idx_b % 2 == 0 and t_ptr < len(terr_ordered):
            stations.append(terr_ordered[t_ptr])
            t_ptr += 1
    while t_ptr < len(terr_ordered):
        stations.append(terr_ordered[t_ptr])
        t_ptr += 1

    out_mp4 = os.path.join(OUT_DIR, f"poem_{poem_num:02d}_videotext_fx.mp4")

    if reuse_existing_mp4 and os.path.exists(out_mp4):
        cap = cv2.VideoCapture(out_mp4)
        passage_frames = []
        n_need = int(12.0 * FPS)
        sample_idx = int(2.4 * FPS)
        sample_fr = None
        for idx_f in range(n_need):
            ok, fr = cap.read()
            if not ok or fr is None:
                break
            rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
            passage_frames.append(rgb)
            if idx_f == sample_idx:
                sample_fr = rgb
        cap.release()
        if sample_fr is None and passage_frames:
            sample_fr = passage_frames[-1]
    else:
        multiplanes = [prepare_station_multiplane(st, k) for k, st in enumerate(stations)]
        sample_fr, passage_frames = stream_encode_poem_afterlight_fx(
            poem_num, poem_title, district_name, stations, multiplanes, dur, out_mp4, audio_t0
        )

        os.makedirs(POEMS_VID_DIR, exist_ok=True)
        shutil.copy2(out_mp4, os.path.join(POEMS_VID_DIR, f"poem_{poem_num:02d}_videotext_fx.mp4"))
        Image.fromarray(sample_fr).save(os.path.join(POEMS_VID_DIR, f"poem_{poem_num:02d}_videotext_fx.jpg"), quality=92)

    vtext_entry = build_poem_videotext_entry(
        poem_num, poem_meta, poem_title, district_name, body_hex, glow_hex, stations, scion_list, total_dur=dur
    )
    return {
        "poem_num": poem_num,
        "poem_title": poem_title,
        "district_name": district_name,
        "body_hex": body_hex,
        "glow_hex": glow_hex,
        "fx_code": POEM_AFTERLIGHT_SPEC[poem_num]["fx_code"],
        "fx_name": POEM_AFTERLIGHT_SPEC[poem_num]["fx_name"],
        "dur": dur,
        "station_count": len(stations),
        "mp4": out_mp4,
        "sample_frame": sample_fr,
        "passage_frames": passage_frames,
        "vtext_entry": vtext_entry,
    }


# ==============================================================================
# THE MASTER SUNDANCE FEATURE FILM (`wygwyl_afterlight_feature.mp4`)
# Modeled after `hartswf0.github.io/bolas/afterlight/room/#feature` and `07-spacetime`
# ==============================================================================

def _render_archival_title_card(u_norm, first_frame_u8):
    """
    Renders the 7.0s Cold Open archival title card (`0:00 - 0:07`):
      - Double-ruled warm celluloid frame (`#0e0d0b`) with subtle film grain
      - `WHERE YOU GO WHEN YOU LEAVE`
      - `An Afterlight Feature in Fourteen Poems`
      - Dissolving smoothly (`u_norm > 0.52`) through golden embers into `first_frame_u8` (`P01 · V92`).
    """
    pil_bg = Image.new("RGBA", (W, H), (14, 13, 11, 255))
    d = ImageDraw.Draw(pil_bg)

    # Double-ruled archival border
    d.rectangle([44, 38, W - 44, H - 38], outline=(218, 176, 102, 165), width=1)
    d.rectangle([50, 44, W - 50, H - 44], outline=(218, 176, 102, 85), width=1)

    f_kicker = get_font("mono", 13)
    f_title = get_font("serif_bold", 42)
    f_sub = get_font("serif_italic", 24)
    f_meta = get_font("mono", 12)

    fade_in = smootherstep(min(1.0, u_norm / 0.18))
    a_hi = int(245 * fade_in)
    a_mid = int(195 * fade_in)
    a_lo = int(145 * fade_in)

    kicker = "SUNDANCE NEW FRONTIER EDITION  ·  AFTERLIGHT VIDEOTEXT FEATURE"
    title = "WHERE YOU GO WHEN YOU LEAVE"
    sub = "Figures in formless matter: fourteen poems, ten districts, one latent city."
    meta = "COMMON PLACES (V01–V108)  ·  PAINTED CELS (SCION P01–P14)  ·  FOURTEEN 3D OPTICAL TECHNIQUES"

    d.text((int((W - d.textlength(kicker, font=f_kicker)) * 0.5), H // 2 - 96), kicker, font=f_kicker, fill=(248, 192, 96, a_mid))
    d.text((int((W - d.textlength(title, font=f_title)) * 0.5), H // 2 - 42), title, font=f_title, fill=(246, 240, 228, a_hi))
    d.text((int((W - d.textlength(sub, font=f_sub)) * 0.5), H // 2 + 22), sub, font=f_sub, fill=(225, 216, 198, a_mid))
    d.text((int((W - d.textlength(meta, font=f_meta)) * 0.5), H // 2 + 86), meta, font=f_meta, fill=(185, 176, 158, a_lo))

    card_rgb = np.asarray(pil_bg.convert("RGB"), dtype=np.float32) / 255.0
    if u_norm <= 0.52:
        return (card_rgb * 255.0).astype(np.uint8)

    u_diss = smootherstep((u_norm - 0.52) / 0.48)
    first_f = first_frame_u8.astype(np.float32) / 255.0
    amber = np.array([0.98, 0.62, 0.18], dtype=np.float32)[None, None, :]
    flash = math.sin(math.pi * u_diss) * 0.18
    blended = np.clip(card_rgb * (1.0 - u_diss) + first_f * u_diss + amber * flash, 0.0, 1.0)
    return (blended * 255.0).astype(np.uint8)


def _render_archival_credits_card(u_norm, results):
    """
    Renders the 8.0s Archival End Credits (`u_norm in [0, 1]`):
    Lists all 14 Poems, their City Districts, and their Afterlight Optical Techniques (`FX01–FX14`).
    """
    pil_bg = Image.new("RGBA", (W, H), (12, 11, 10, 255))
    d = ImageDraw.Draw(pil_bg)

    d.rectangle([44, 38, W - 44, H - 38], outline=(218, 176, 102, 145), width=1)
    d.rectangle([50, 44, W - 50, H - 44], outline=(218, 176, 102, 75), width=1)

    fade = smootherstep(min(1.0, u_norm / 0.18)) * (1.0 - smootherstep(max(0.0, (u_norm - 0.82) / 0.18)))
    a_hi = int(240 * fade)
    a_mid = int(195 * fade)
    a_gold = int(235 * fade)

    f_head = get_font("serif_bold", 24)
    f_sub = get_font("serif_italic", 16)
    f_mono = get_font("mono", 12)

    head = "WHERE YOU GO WHEN YOU LEAVE  ·  THE FOURTEEN AFTERLIGHT MOVEMENTS"
    d.text((84, 68), head, font=f_head, fill=(246, 240, 228, a_hi))
    d.text((84, 100), "Every Common Place, Painted Cel, and City District Palette on its own clock.", font=f_sub, fill=(218, 196, 156, a_mid))

    for i, r in enumerate(results):
        col = i // 7
        row = i % 7
        x0 = 84 + col * 560
        y0 = 152 + row * 68
        p_line = f"P{r['poem_num']:02d} · {r['poem_title'].upper()}  ({r['district_name']})"
        fx_line = f"    [{r['fx_code']}] {r['fx_name']}"
        d.text((x0, y0), p_line[:58], font=f_mono, fill=(250, 192, 96, a_gold))
        d.text((x0, y0 + 20), fx_line[:62], font=f_sub, fill=(230, 224, 212, a_mid))

    foot = "BUILT WITH REAL DEPTH_SHARP MULTIPLANE PARALLAX  ·  PAINTED CELS  ·  MASTER SUITE SCORE"
    d.text((84, H - 74), foot, font=f_mono, fill=(175, 168, 152, a_mid))
    return np.asarray(pil_bg.convert("RGB"), dtype=np.uint8)


def build_master_sundance_feature(results):
    """
    Assembles the complete Master Sundance Feature (`wygwyl_afterlight_feature.mp4`) from the 14 poem passages:
      1. Cold Open Title (`0:00 – 0:06`, 6.0s = 144 frames)
      2. 14 Poem Passages (`14 × 10.5s` effective with 1.5s optical depth/halation dissolves = ~148.5s)
      3. The Avalanche Coda (`15.0s` = 360 frames): accelerating montage across all 14 territories
         tightening to 0.17s cuts, then 1.4s of darkroom silence and one single rising golden dot!
      4. Archival Credits (`8.0s` = 192 frames)
    Returns `(feature_mp4_path, chapters_list, progression_sheet_path)`.
    """
    print("Assembling Master Sundance Feature (`wygwyl_afterlight_feature.mp4`)...", flush=True)
    feature_frames = []
    chapters = []

    # 1. Cold Open (6.0s = 144 frames)
    n_cold = int(6.0 * FPS)
    first_f = results[0]["passage_frames"][0]
    chapters.append({
        "id": "cold-open",
        "label": "00 · Cold Open",
        "title": "Where You Go When You Leave",
        "fx_code": "TITLE · V92",
        "t0": 0.0,
    })
    for i in range(n_cold):
        feature_frames.append(_render_archival_title_card(i / float(max(1, n_cold - 1)), first_f))
    chapters[-1]["t1"] = round(len(feature_frames) / float(FPS), 2)

    # 2. 14 Poem Passages with 1.25s (30-frame) celluloid halation dissolves between consecutive poems
    overlap = int(1.25 * FPS)
    cur_poem_frames = list(results[0]["passage_frames"])

    for idx in range(len(results)):
        r_curr = results[idx]
        t_chap_start = round(len(feature_frames) / float(FPS), 2)
        chapters.append({
            "id": f"p{r_curr['poem_num']:02d}",
            "num": r_curr["poem_num"],
            "label": f"P{r_curr['poem_num']:02d} · {r_curr['poem_title']}",
            "title": f"{r_curr['poem_title']} ({r_curr['district_name']})",
            "fx_code": r_curr["fx_code"],
            "fx_name": r_curr["fx_name"],
            "t0": t_chap_start,
        })

        if idx < len(results) - 1:
            r_next = results[idx + 1]
            next_frames = list(r_next["passage_frames"])
            # Append main body of current poem up to `len - overlap`
            body_end = len(cur_poem_frames) - overlap
            feature_frames.extend(cur_poem_frames[:body_end])

            # Render 30-frame optical celluloid gate-burn / halation dissolve into `next_frames[:overlap]`
            c_glow = hex_to_rgb_float((r_curr["glow_hex"] or ["#fa8d15"])[0])[None, None, :]
            for k_ov in range(overlap):
                u_ov = smootherstep((k_ov + 1) / float(overlap + 1))
                f_a = cur_poem_frames[body_end + k_ov].astype(np.float32) / 255.0
                f_b = next_frames[k_ov].astype(np.float32) / 255.0
                # Warm celluloid halation pulse at the midpoint of the dissolve
                halo = math.sin(math.pi * u_ov) * 0.22
                comp = np.clip(f_a * (1.0 - u_ov) + f_b * u_ov + halo * c_glow, 0.0, 1.0)
                feature_frames.append((comp * 255.0).astype(np.uint8))

            cur_poem_frames = next_frames[overlap:]
        else:
            feature_frames.extend(cur_poem_frames)

        chapters[-1]["t1"] = round(len(feature_frames) / float(FPS), 2)

    # 3. The Avalanche Coda ("Every volume twice, cuts tightening to a quarter second, then 1.4s of silence before one gold dot")
    t_av_start = round(len(feature_frames) / float(FPS), 2)
    chapters.append({
        "id": "avalanche",
        "label": "XV · The Avalanche",
        "title": "The Avalanche & Single Gold Dot",
        "fx_code": "CODA · 14×2",
        "t0": t_av_start,
    })

    # Single accelerating pass across all 14 poems (14 frames down to 5 frames) so no poem replays twice
    avalanche_schedule = [
        (r, max(5, 15 - idx_r), 85 + idx_r * 6)
        for idx_r, r in enumerate(results)
    ]
    for step_i, (r_item, n_cut, start_off) in enumerate(avalanche_schedule):
        pf = r_item["passage_frames"]
        accel_progress = step_i / float(max(1, len(avalanche_schedule) - 1))
        gold_vec = np.array([0.98, 0.68, 0.20], dtype=np.float32)[None, None, :]
        for k_c in range(n_cut):
            src_fr = pf[min(len(pf) - 1, start_off + k_c)].astype(np.float32) / 255.0
            # Subtle warm halation build as cuts tighten
            warm_boost = 0.14 * accel_progress * (1.0 if k_c == 0 else 0.4)
            fr_c = np.clip(src_fr * (1.0 + 0.10 * accel_progress) + warm_boost * gold_vec, 0.0, 1.0)
            feature_frames.append((fr_c * 255.0).astype(np.uint8))

    # 1.4s (34 frames) of pure darkroom silence (`#0a0908`), then 2.2s (53 frames) of one single rising warm gold dot (`#fa8d15`)
    for _ in range(34):
        feature_frames.append(np.full((H, W, 3), 9, dtype=np.uint8))

    for k_dot in range(53):
        u_dot = k_dot / 52.0
        canvas_dot = np.full((H, W, 3), 9.0 / 255.0, dtype=np.float32)
        dot_x = W * 0.5 + 4.0 * math.sin(u_dot * 4.0)
        dot_y = H * (0.54 - 0.12 * u_dot)
        r_d = np.hypot(_XX - dot_x, _YY - dot_y)
        dot_env = math.sin(math.pi * min(1.0, u_dot * 1.15))
        core = np.exp(-(r_d / 4.5) ** 2)[..., None] * dot_env
        halo = np.exp(-(r_d / 28.0) ** 2)[..., None] * dot_env * 0.42
        gold_core = np.array([1.0, 0.92, 0.72], dtype=np.float32)[None, None, :]
        gold_halo = np.array([0.98, 0.56, 0.12], dtype=np.float32)[None, None, :]
        canvas_dot = np.clip(canvas_dot + halo * gold_halo + core * gold_core, 0.0, 1.0)
        feature_frames.append((canvas_dot * 255.0).astype(np.uint8))

    chapters[-1]["t1"] = round(len(feature_frames) / float(FPS), 2)

    # 4. Archival End Credits (7.5s = 180 frames)
    t_cred_start = round(len(feature_frames) / float(FPS), 2)
    chapters.append({
        "id": "credits",
        "label": "XVI · Credits",
        "title": "Archival Colophon & Credits",
        "fx_code": "COLOPHON",
        "t0": t_cred_start,
    })
    n_cred = int(7.5 * FPS)
    for i in range(n_cred):
        feature_frames.append(_render_archival_credits_card(i / float(max(1, n_cred - 1)), results))
    chapters[-1]["t1"] = round(len(feature_frames) / float(FPS), 2)

    feature_mp4 = os.path.join(OUT_DIR, "wygwyl_afterlight_feature.mp4")
    encode_video_with_real_audio(feature_frames, feature_mp4, 0.0)
    shutil.copy2(feature_mp4, os.path.join(VIDEOS_DIR, "wygwyl_afterlight_feature.mp4"))
    shutil.copy2(feature_mp4, os.path.join(ARTIFACT_DIR, "wygwyl_afterlight_feature.mp4"))

    # Build Sundance Feature Progression Contact Sheet (16 tiles: Cold Open + 14 Poems + Avalanche/Gold Dot)
    cols, rows = 4, 4
    tw, th = 480, 270
    label_h = 34
    cell_h = th + label_h
    prog_sheet = Image.new("RGB", (cols * tw, rows * cell_h), (18, 17, 15))
    d_ps = ImageDraw.Draw(prog_sheet)
    f_lbl = get_font("mono", 12)

    sample_indices = [int(2.2 * FPS)]  # Cold open title card
    for ch in chapters[1:15]:
        sample_indices.append(int((ch["t0"] + 2.6) * FPS))
    sample_indices.append(int((chapters[15]["t1"] - 1.1) * FPS))  # The Avalanche -> Single Gold Dot climax

    for idx_tile, f_idx in enumerate(sample_indices[:16]):
        wx = (idx_tile % cols) * tw
        wy = (idx_tile // cols) * cell_h
        fr_u8 = feature_frames[min(len(feature_frames) - 1, max(0, f_idx))]
        im_t = Image.fromarray(fr_u8).resize((tw, th), Image.Resampling.LANCZOS)
        prog_sheet.paste(im_t, (wx, wy))
        ch_info = chapters[min(idx_tile, len(chapters) - 1)]
        cap = f"{ch_info['label']}  [{ch_info.get('fx_code', '')}]  ({ch_info['t0']:.1f}s)"
        d_ps.text((wx + 12, wy + th + 9), cap[:58], font=f_lbl, fill=(238, 214, 168))

    prog_path = os.path.join(OUT_DIR, "sundance_feature_progression_sheet.png")
    prog_sheet.save(prog_path)
    prog_sheet.save(os.path.join(ARTIFACT_DIR, "sundance_feature_progression_sheet.png"))
    return feature_mp4, chapters, prog_path


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(POEMS_VID_DIR, exist_ok=True)

    reuse_existing = "--assemble" in sys.argv
    args_clean = [a for a in sys.argv[1:] if a != "--assemble"]

    if args_clean:
        poems_to_run = [int(x) for x in args_clean]
    else:
        poems_to_run = list(range(1, 15))

    print(f"Building Sundance Unobstructed 16:9 Afterlight Videotext Films (FX01..FX14) for Poems: {poems_to_run} (reuse_existing={reuse_existing})", flush=True)
    results = []
    if len(poems_to_run) == 1:
        r = build_single_poem_afterlight_fx(poems_to_run[0], reuse_existing_mp4=reuse_existing)
        results.append(r)
        print(f"Done P{r['poem_num']:02d} [{r['fx_code']}] {r['fx_name']}: {r['mp4']}", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(build_single_poem_afterlight_fx, p, reuse_existing): p for p in poems_to_run}
            for fut in as_completed(futs):
                r = fut.result()
                results.append(r)
                print(f"Done P{r['poem_num']:02d} ({r['poem_title']} · {r['district_name']} · {r['dur']:.1f}s · {r['station_count']} stations) -> [{r['fx_code']}] {r['fx_name']}", flush=True)

    results.sort(key=lambda x: x["poem_num"])

    if len(results) == 14:
        feature_mp4, feature_chapters, prog_path = build_master_sundance_feature(results)

        manifest = {
            "title": "WYGWYL · Afterlight Videotext & Sundance Feature Suite",
            "subtitle": "Fourteen poems, ten city districts, Common Places, painted cels, and fourteen 3D optical techniques.",
            "feature_video": "data/terrarium/seeing_spacetime_films/wygwyl_afterlight_feature.mp4?v=11",
            "feature_dur": feature_chapters[-1]["t1"] if feature_chapters else 216.0,
            "feature_chapters": feature_chapters,
            "poems": [r["vtext_entry"] for r in results],
        }
        manifest_path = os.path.join(OUT_DIR, "videotext_manifest.json")
        with open(manifest_path, "w") as jf:
            json.dump(manifest, jf, indent=2)

        # Build 4x4 archival contact sheet where each 16:9 film frame is 100% unobstructed and captions sit in the margin below each tile
        cols, rows = 4, 4
        tw, th = 480, 270
        cap_h = 34
        cell_h = th + cap_h
        sheet = Image.new("RGB", (cols * tw, rows * cell_h), (235, 227, 207))
        d_sh = ImageDraw.Draw(sheet)
        f_cap = get_font("mono", 12)

        for i, r in enumerate(results):
            wx, wy = (i % cols) * tw, (i // cols) * cell_h
            im_tile = Image.fromarray(r["sample_frame"]).resize((tw, th), Image.Resampling.LANCZOS)
            sheet.paste(im_tile, (wx, wy))
            d_sh.rectangle([wx, wy + th, wx + tw, wy + cell_h], fill=(24, 22, 19))
            lbl = f"P{r['poem_num']:02d} · {r['poem_title'].upper()[:20]}  [{r['fx_code']}] {r['fx_name'][:28]}"
            d_sh.text((wx + 10, wy + th + 9), lbl, font=f_cap, fill=(246, 204, 122))

        # Put Cold Open and Avalanche in tiles 15 and 16 of the 4x4 grid!
        extra_tiles = [
            ("FEATURE COLD OPEN · TITLE CARD", _render_archival_title_card(0.35, results[0]["sample_frame"])),
            ("FEATURE COLOPHON · 14 MOVEMENTS", _render_archival_credits_card(0.50, results)),
        ]
        for j, (e_lbl, e_fr) in enumerate(extra_tiles):
            idx_e = 14 + j
            wx, wy = (idx_e % cols) * tw, (idx_e // cols) * cell_h
            im_tile = Image.fromarray(e_fr).resize((tw, th), Image.Resampling.LANCZOS)
            sheet.paste(im_tile, (wx, wy))
            d_sh.rectangle([wx, wy + th, wx + tw, wy + cell_h], fill=(24, 22, 19))
            d_sh.text((wx + 10, wy + th + 9), e_lbl, font=f_cap, fill=(246, 204, 122))

        sheet_path = os.path.join(OUT_DIR, "all_14_poems_afterlight_videotext_fx_sheet.png")
        sheet.save(sheet_path)
        sheet.save(os.path.join(ARTIFACT_DIR, "all_14_poems_afterlight_videotext_fx_sheet.png"))
        print("Saved manifest, Master Sundance Feature, & contact sheets:", manifest_path, feature_mp4, sheet_path, prog_path, flush=True)
