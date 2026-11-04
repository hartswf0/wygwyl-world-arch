#!/usr/bin/env python3
"""
WYGWYL · ALL 14 POEMS AFTERLIGHT VIDEOTEXT & BESPOKE PICTURE-TECHNIQUE SUITE
=============================================================================
Inspired by surveying ALL Afterlight experiences (`https://hartswf0.github.io/bolas/afterlight/`
and `https://hartswf0.github.io/bolas/afterlight/room/`):
  - Main Videotext Chapters (`02-cold-hand`, `04-afterlife-essay`, `05/06-small-sun`, `07-spacetime`,
    `08-warm-cave`, `09-afterlife-trailer`, `10-warm-dome`, `11-light-alone`, `12-mix`, `13-takumi`,
    `14-phosphor`, `15-beckon`, `16-circle`, `17-warmth`, `18-dawn`, `19-picture`, `20-sun`,
    `21-copper`, `22-one-note`, `23-golden-record`, `24-carry-the-glow`, `25-daimonji`)
  - Screening Room Series (`Songs 01–10`, `Dew 02b–02d`, `Viscosity V1–V4`, `Air A1–A5`,
    `Lens L1–L3`, `Matter M1–M5`, `Seeing-As S1–S3`, `Humours H1–H4`)

For each of the 14 Poems (`P01..P14`), this script:
  1. Renders a bespoke 30.0s `1280x720` 24fps film (`poem_<NN>_videotext_fx.mp4`) with real suite audio,
     pairing each poem's poetic imagery, Common Places (`atlas.heroes`), Painted Cels (`cel_v2` + `frames`),
     and City District `body` + `glow` palette (`_city/districts.json`) with its own signature
     Afterlight picture technique (`FX01..FX14`).
  2. Exports `videotext_manifest.json` with each poem's complete Videotext Clock Script (`scenes` with
     `t0, t1, who, say, f, tape`, plus `picture, sound, code, after` notes) so the interactive
     Videotext reader scrolls on the film's own clock (scroll moves the film; play scrolls the text).
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
        "picture": "Each Common Place (The Underpass Shadow-Pool, The Severn's Spiral Escape, The Orange Catwalk) breathes condensation across the glass by estimated depth. Where the actor moves in the foreground, the glass clears; along the fire escape, high-luminance points lift off as cyan and amber embers.",
        "sound": "Malhun in Bayati mode over the suite master audio (0:00–2:03), with sub-bass drone steps.",
        "code": "Depth-weighted condensation envelope from depth_sharp.npz + deterministic curl-drift ember particles spawned from luminance peaks.",
        "after": "“The vape gathers, inside and out. My vision blurs. I move toward the window — and you only get further away… You fall off the fire escape, into darkness — and the city streaks upward.”",
    },
    2: {
        "fx_code": "05 · 20 · L2",
        "fx_name": "Makyō Magic Mirror, Venetian Blinds & Retinal Afterimage",
        "afterlight_ref": "Song 05 (Makyō Magic Mirror) + 20 (Sun in Your Eyes Retinal Afterimage) + Lens L2 (Anamorphic Flare)",
        "idea": "A midnight mirror throws a hidden caustic double onto the wall; blinds slice the light and each beacon pulse leaves a retinal afterimage.",
        "picture": "Inside the Drowned Cathedral and The Overseer's chambers, microscopic depth curvature (∇²z) acts as a Japanese makyō magic mirror throwing a luminous double figure across the wall. Slatted Venetian blinds open across the depth layers while beacon hits trigger opponent-color retinal afterimages and horizontal anamorphic streaks.",
        "sound": "Gabay in Phrygian mode; off-screen drum strikes and beacon pulses climb the far signal tower.",
        "code": "Laplacian depth-caustic projection + slatted blind phase mask + opponent-color retinal adaptation decay on beat peaks.",
        "after": "“The silent call a man makes to the mirror after midnight, to digest a truth… Curtains pulled, and blinds up as far and as wise as possible — to see flashing lights.”",
    },
    3: {
        "fx_code": "02d · 02c · M4",
        "fx_name": "Falling Raindrop Video Lenses & Mud-Imprinted Relief",
        "afterlight_ref": "Dew 02c/02d (Pane & Worms: drops leave wet tracks that keep playing) + Matter M4 (Mud, by outline)",
        "idea": "Falling raindrops act as convex lenses whose wet tracks replay the moment the drop passed; storm aftermath presses outlines into wet mud.",
        "picture": "Across the Drowned Atrium and chapel rose window, sixteen raindrop lenses slide down the glass. Each drop magnifies the cel plate and leaves a wet track running the delayed frame from when the drop passed. As the storm subsides, figures and footsteps press into wet mud relief by their outline.",
        "sound": "Dirge in pentatonic mode; thunder, tambourine echoes off empty choir stands, and rain on stone.",
        "code": "14 deterministic falling droplet lenses with barrel refraction + temporal trail buffer + directional Sobel contour relief (M4 Mud).",
        "after": "“It thunders. Then rains until nothing remains… Ode to two sets of mud-imprinted footsteps, leading away from what the water kept.”",
    },
    4: {
        "fx_code": "08 · 03",
        "fx_name": "Darkroom Silver-Gelatin Tray & Two-Block Linocut Memory",
        "afterlight_ref": "Song 08 (A Letter from a Dead Star: Darkroom Tray) + Song 03 (The Stone That Remembered: Two-Block Linocut)",
        "idea": "A print develops in a sloshing darkroom tray: deep silver-indigo ink for now, luminous gold ink for what the picture just let go.",
        "picture": "The Named Viaduct and Shore Steps develop like a silver-gelatin print under a gentle liquid tray wave. Carved over the silver plate is a two-block linocut: deep indigo-charcoal holds the present posture, while warm gold ink (#e88f0e) prints the temporal delta of what just moved.",
        "sound": "Suite movement IV over Mirror Thread Bay's low tide and muted wind.",
        "code": "Silver-gelatin tonal curve + sinusoidal developer-tray refraction + temporal motion-delta gold woodblock relief overlay.",
        "after": "“A trail followed twice, a vow made twice… The plants in a golden hue bloom, and face toward me in anticipation… The clouds mute the stars for the deepest level of darkness.”",
    },
    5: {
        "fx_code": "23 · 24 · 09",
        "fx_name": "Semantic 3D Heart-Scan Naming (LIFT · LABEL · STAR)",
        "afterlight_ref": "Experiment IV 23/24 (Golden Record / Carry the Glow: Every Point Named) + 09 (Embers into Stars)",
        "idea": "A heart-scan front sweeps through the 3D depth volume, naming every class and lifting ancestral points into named stars.",
        "picture": "At The Perimeter and the Southern Pine field, a luminous green-gold scan-front sweeps back through depth_sharp.npz. As the front passes, semantic constellation nodes (ANCESTOR, HEART-SCAN, SOUTHERN PINE, BLOODLINE, LIGHT GATE) flash with archival telemetry and shed rising points that lock into the sky as stars.",
        "sound": "Suite movement V (The Ascent); rhythmic heart-scan pulses lock to the snare and bass.",
        "code": "Depth-plane scan wave |disp - z_front(t)| + local depth/salience peak tracker + persistent star-field particle accumulator.",
        "after": "“He names the stars after the people who made him… To ask if I can inherit the earth — to ask if I can invent a new universe.”",
    },
    6: {
        "fx_code": "10 · 22",
        "fx_name": "Refracted Caustic Net & Falling Atlantis Waterline",
        "afterlight_ref": "Experiment III 10 (Warm Dome Caustics) + 22 (One Note Underwater Caustic Net)",
        "idea": "A net of refracted underwater caustics dances over submerged Atlantis as the waterline falls to reveal the marble Light Gate.",
        "picture": "The Light Gate, The House, and the Sunken Forum begin submerged beneath a refracted net of turquoise and magenta caustic light rays. As each station progresses, the optical waterline descends by depth and altitude, lifting the marble plaza out of the rippling water into warm golden air.",
        "sound": "Suite movement VI; deep underwater resonance opening into clear plaza acoustics as the waterline drops.",
        "code": "Dual-frequency ray-refracted caustic lattice + depth-coupled waterline boundary with specular meniscus and sub-surface ripple.",
        "after": "“A city comes up out of the water… The waterline falls: Resurrecting Atlantis. Here we are all one.”",
    },
    7: {
        "fx_code": "01 · 16",
        "fx_name": "Radial Time-Delay Watercolour & Turning Platter Rings",
        "afterlight_ref": "Song 01 (Borrowed Light: Radial Time-Delay Watercolour) + 16 (Magic Circle: Spectrum Pressed into a Turning Record)",
        "idea": "Each pixel shows the shot a little later the farther it sits from the centre, rippled by turning turntable rings and eleven petals.",
        "picture": "Inside The Spire Elevator Shaft and The House DJ booth, time radiates outward like diverging wedding bands on a turntable platter: the center plays the present frame while concentric outer rings show moments from 0.2s to 1.0s ago in soft watercolour pigment bleed, accompanied by eleven drifting luminous petals.",
        "sound": "Suite movement VII (DJ Turn Me Up); amplitude rings pulse with the booth groove.",
        "code": "Per-pixel radial frame-buffer interpolation t(r) = t - k·r + polar harmonic groove rings + 11 petal trajectories.",
        "after": "“DJ, turn me up, please… So I can speak: of wedding bands diverging across abstract skies… A love story of years — eleven years — each plucked off as a petal.”",
    },
    8: {
        "fx_code": "S1 · A2b · 14",
        "fx_name": "Seeing-As Astral Aspect Split & Subject-Alone Smoke",
        "afterlight_ref": "Seeing-As S1 (Aspect) + Matter A2b (Smoke, subject alone) + 14 (Warm Phosphor Light Painting)",
        "idea": "The foreground dancer's soul separates from the body as a luminous phosphor double giving off violet curl-smoke, then returns.",
        "picture": "On the Ankhu Spires rooftop dance floor, the foreground subject's silhouette splits into two readings: the physical painted cel body and a displaced luminous astral double (Warm Phosphor + Seeing-As Aspect) that trails upward-curling violet and amber smoke before reuniting with the body.",
        "sound": "Suite movement VIII (Newly Single); rooftop club pulse dropping into open-field stillness.",
        "code": "Foreground salience matte extraction + sinusoidal astral-double UV offset + upward curl-advected smoke buffer + phosphor highlight persistence.",
        "after": "“The soul escapes my body, and leaves him on the dance floor… I want my soul to imagine my body… Now bring my soul back to my body: to lean back, breathe in.”",
    },
    9: {
        "fx_code": "09 · 11 · 21",
        "fx_name": "Carry the Glow 3D Normal Relighting & Three Voice Threads",
        "afterlight_ref": "Song 09 (Carry the Glow: One Warm Light Handed Shot to Shot) + 11 (Light Alone Waveform Threads) + 21 (Copper Glow)",
        "idea": "One borrowed warm light travels from shot to shot, relighting 3D surface normals while three voice threads trace the three calls.",
        "picture": "Under The LED Canopy and along the harbor walk, one warm amber lantern is handed across every cut. Surface normals computed from depth_sharp.npz catch the travelling light across faces, wet cobblestones, and the moon, while three glowing harmonic threads trace the calls to the moon, mother, and father.",
        "sound": "Suite movement IX (Yet, Heard); three intimate vocal calls over harbor water.",
        "code": "3D surface normal estimation N = normalize(-∂z/∂x, -∂z/∂y, 1) + travelling point-light Lambertian/specular relighting + 3 harmonic ribbon curves.",
        "after": "“Before I go, we look at the moon the way we used to see it… I call on my mother… I call on my father… We stroll, father and son, hearted and shaken. Someone borrows a light.”",
    },
    10: {
        "fx_code": "07 · 04",
        "fx_name": "Nine Thousand Firefly Pinholes & Risograph Dot-by-Dot Dawn",
        "afterlight_ref": "Song 07 (Light Without Fire: 9,000 Pinholes in Kraft Paper) + Song 04 (Past the Red: Risograph)",
        "idea": "Night is pierced by 9,000 blinking firefly pinholes that expand dot by dot into a warm Risograph morning.",
        "picture": "Across The Underpass Shadow-Pool and The Named Viaduct, the night scene is held behind a lattice of 9,000 pinholes. Each pinhole blinks like a firefly keyed to the underlying luminance; as the dawn wave sweeps across the frame, the dots expand into a warm two-drum Orange Haze Risograph morning.",
        "sound": "Suite movement X (Magic Ride); nocturnal bike ride opening into morning.",
        "code": "Hexagonal 9,000-pinhole aperture lattice + phase-blinking firefly modulation + progressive radial dot-aperture expansion into warm Risograph grade.",
        "after": "“All preparations to live and dream in darkness, I no longer need… Night replaced by morning, dot by dot.”",
    },
    11: {
        "fx_code": "A1 · 19 · 07",
        "fx_name": "Sea-Fog Clearing & 30-Course Nipkow Temple Assembly",
        "afterlight_ref": "Air A1 (Fog takes far things first by depth) + 19 (Thus the Picture Is Reassembled: 30-line Nipkow scan) + 07 (Sun Rays)",
        "idea": "Morning fog hugs the far depth planes while thirty horizontal masonry courses scan and assemble the temple from the ground up under sun rays.",
        "picture": "At The Shore Steps and The Temple's Pools, morning sea-fog wraps the distant hills by depth. Thirty horizontal architectural courses (after the 30-line Nipkow disk in Thus the Picture Is Reassembled) scan upward from foundation to cornice, locking the temple into clear dawn light beneath volumetric sun rays.",
        "sound": "Suite movement XI (New Day); dawn chorus and temple resonance.",
        "code": "Depth-exponential fog absorption + 30-band horizontal course assembly wave with golden seam glints + volumetric god-ray projection.",
        "after": "“Fog covers the seas and hugs the tree-covered hills… We can rebuild this temple, one course at a time — under vibrant sun rays of glory.”",
    },
    12: {
        "fx_code": "M3 · A4",
        "fx_name": "Burning Hourglass Sand of Time & Parting Winds",
        "afterlight_ref": "Matter M3 (Hourglass: top bulb plays live, each fallen grain keeps its moment) + Air A4 (Wind)",
        "idea": "Golden grains fall from the live upper scene into the reflection pool below, each grain keeping its moment until the wind parts.",
        "picture": "At The White Temple & its Pools, the upper frame plays live while luminous golden sand-grains stream downward into the mirror pool below. Each fallen grain preserves the color of the moment it fell, building a shimmering stratum of past time on the water until a lateral wind-gust parts the surface.",
        "sound": "Suite movement XII (Reunion); warm acoustic cadence with spacious silences.",
        "code": "Vertical particle-grain advection from upper frame to lower pool + temporal memory accumulation in the pool reflection + A4 wind-shear transition.",
        "after": "“Decades later, there is less time for words, and more space for laughter… Burning hourglasses: And is this a one-time occasion? we ask… Before our winds part ways.”",
    },
    13: {
        "fx_code": "06 · V2 · M2a",
        "fx_name": "Daimonji Revolving Lantern Orbits, Marbled Wakes & Gate Burn",
        "afterlight_ref": "Song 06 (Daimonji Revolving Lantern) + Viscosity V2 (Marble Chevrons) + Matter M2a (Projector Gate Burn)",
        "idea": "Paired scenes orbit like Jupiter's moons inside a revolving lantern, trailing marbled wakes before burning through the gate to the next story.",
        "picture": "Along The Orange Catwalk and pier café, the camera curves gently like a revolving Daimonji shadow-lantern while two luminous satellite moons orbit across the depth field trailing paper-marbled chevrons. At the end of each station, the film catches in the gate and burns open with a scarlet-poppy and amber rim into the next scene.",
        "sound": "Suite movement XIII (How to Win My Heart); orbital waltz pulse.",
        "code": "Cylindrical lantern projection + dual Keplerian orbital light-moons with combed chevron displacement + organic Perlin gate-burn transition front.",
        "after": "“The couples orbit each other the way Jupiter keeps its moons… Life has burned all our stories. So I harvest the flowers instead — scarlet poppies, purple blossoms.”",
    },
    14: {
        "fx_code": "08 · A3 · 12",
        "fx_name": "Warm Cave Ground-Up Thermal Scanline, Weather Front & Vintage Doorway",
        "afterlight_ref": "Experiment I 08 (Warm Cave: Scanline Arrival & Infrared Memory) + Air A3/A4 (Weather) + 12 (The Mix Reel) + Doorway Aperture",
        "idea": "A thermal scanline and weather front take the city from the ground up, flashing a reel of memory before opening a vintage doorway onto the horizon.",
        "picture": "Across The Orange Catwalk and The Sleep-Dam Wall, a rising ground-up thermal scanline turns older frames into warm infrared ember-memory while cloud-haze gathers on the water. As the life-reel flashes, a tall vintage doorway aperture opens from the center, framing the luminous panoramic horizon.",
        "sound": "Suite finale XIV (Hot Minute); full orchestral/electronic swell resolving into open air.",
        "code": "Ground-up scanline decode + thermal infrared memory grade on past frames + atmospheric cloud-vapor layer + expanding doorway portal vignette.",
        "after": "“Everything learns to be weather, then a door… It takes me last, and from the ground up… A life flashes the way a reel does… An old door, from a vintage somewhere. It opens on a slow panorama.”",
    },
}


def apply_poem_afterlight_fx(poem_num, curr_rgb, past_rgb, disp, u_seg, t, body_hex, glow_hex):
    """
    Applies the poem's bespoke Afterlight Picture Technique (`FX01..FX14`) to `curr_rgb` (`float32 [0..1]`),
    returning a 100% legible, full-frame `1280x720` cinema image (`float32 [0..1]`).
    """
    c_glow1 = hex_to_rgb_float((glow_hex or ["#01acd4"])[0])
    c_glow2 = hex_to_rgb_float((glow_hex or ["#01acd4", "#fa8d15"])[min(1, len(glow_hex) - 1)])
    c_body1 = hex_to_rgb_float((body_hex or ["#1c2430"])[0])
    out = curr_rgb.copy()

    if poem_num == 1:
        # FX01: A5 Breath on the Glass + A1 Depth Fog + 09 Rising Fire-Escape Embers
        breath_cycle = 0.5 + 0.5 * math.sin(t * 0.95)
        far_weight = np.clip(1.0 - disp * 1.15, 0.0, 1.0)
        cond_mask = np.clip(far_weight * (0.32 + 0.28 * breath_cycle), 0.0, 0.58)[..., None]
        soft_plate = cv2.GaussianBlur(out, (0, 0), 9.0)
        fog_tint = 0.72 * soft_plate + 0.28 * (0.6 * c_body1 + 0.4 * c_glow1)[None, None, :]
        out = out * (1.0 - cond_mask) + fog_tint * cond_mask

        # Upward-streaking embers (`09 Picture to Embers to Stars`) rising from luminous edges
        ember_layer = np.zeros_like(out)
        n_embers = 42
        for k in range(n_embers):
            seed = k * 137.5
            ex = int((math.sin(seed) * 0.5 + 0.5) * (W - 20) + 10)
            ey_base = (math.cos(seed * 0.73) * 0.5 + 0.5) * H
            ey = int((ey_base - (t * (48.0 + (k % 5) * 14.0))) % H)
            ex_curl = int(ex + 14.0 * math.sin(t * 1.6 + k * 0.4)) % W
            rad = 2 if (k % 3 != 0) else 3
            col = c_glow2 if (k % 2 == 0) else c_glow1
            y0, y1 = max(0, ey - rad * 3), min(H, ey + rad)
            x0, x1 = max(0, ex_curl - rad), min(W, ex_curl + rad)
            ember_layer[y0:y1, x0:x1] = np.maximum(ember_layer[y0:y1, x0:x1], col[None, None, :] * 0.85)
        ember_soft = cv2.GaussianBlur(ember_layer, (0, 0), 2.2)
        out = np.clip(out + ember_soft * 0.65, 0.0, 1.0)

    elif poem_num == 2:
        # FX02: 05 Makyo Magic Mirror Caustic Double + Venetian Blinds + 20 Retinal Afterimage & L2 Flare
        lap = cv2.Laplacian(disp, cv2.CV_32F, ksize=5)
        caustic = np.clip(np.abs(lap) * 18.0, 0.0, 1.0)
        caustic_soft = cv2.GaussianBlur(caustic, (0, 0), 6.0)[..., None]
        mirror_double = np.fliplr(past_rgb)
        out = out * (1.0 - 0.22 * caustic_soft) + (0.65 * mirror_double + 0.35 * c_glow1[None, None, :]) * (0.22 * caustic_soft)

        # Subtle Venetian blind light slats ("Curtains pulled, and blinds up")
        blinds = (0.5 + 0.5 * np.sin(_YY * 0.24 - t * 1.8))[..., None]
        blind_env = 0.14 * (1.0 - disp[..., None]) * blinds
        out = np.clip(out + blind_env * c_glow2[None, None, :], 0.0, 1.0)

        # Retinal afterimage & horizontal anamorphic streak on beacon pulse
        pulse = max(0.0, math.sin(t * 2.4) - 0.65) / 0.35
        if pulse > 0.01:
            after_im = 1.0 - cv2.GaussianBlur(past_rgb, (0, 0), 8.0)
            after_tinted = 0.55 * after_im + 0.45 * c_glow1[None, None, :]
            out = out * (1.0 - 0.26 * pulse) + after_tinted * (0.26 * pulse)
        # L2 Horizontal anamorphic flare from brightest highlights
        lum = out @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        bright = np.clip((lum - 0.78) / 0.22, 0.0, 1.0)
        streak = cv2.GaussianBlur(bright, (81, 3), 24.0)[..., None]
        out = np.clip(out + streak * c_glow1[None, None, :] * 0.45, 0.0, 1.0)

    elif poem_num == 3:
        # FX03: 02c/02d Falling Raindrop Video Lenses & Wet Tracks + M4 Mud Relief
        # 1. M4 Mud-imprinted outline relief on midground/background
        gx = cv2.Sobel(disp, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(disp, cv2.CV_32F, 0, 1, ksize=3)
        relief = np.clip(0.5 + 3.5 * (gx * 0.7 + gy * 0.7), 0.0, 1.0)[..., None]
        mud_tint = (0.88 + 0.24 * (relief - 0.5)) * out
        out = 0.65 * out + 0.35 * np.clip(mud_tint, 0.0, 1.0)

        # 2. 12 Falling Raindrop Lenses with wet time-tracks (`02d Worms`: track plays moment drop passed)
        for d_i in range(12):
            seed = d_i * 97.3 + 11.0
            dx_c = (0.08 + 0.84 * ((math.sin(seed) * 0.5 + 0.5))) * W
            speed = 85.0 + (d_i % 4) * 22.0
            dy_c = ((t * speed + d_i * 65.0) % (H + 120.0)) - 40.0
            r_drop = 22.0 + (d_i % 3) * 6.0

            # Bounding box for droplet + vertical wet wake above it
            x0, x1 = max(0, int(dx_c - r_drop - 4)), min(W, int(dx_c + r_drop + 4))
            y0, y1 = max(0, int(dy_c - r_drop * 4.5)), min(H, int(dy_c + r_drop + 4))
            if x1 <= x0 or y1 <= y0:
                continue

            sub_x = _XX[y0:y1, x0:x1] - dx_c
            sub_y = _YY[y0:y1, x0:x1] - dy_c
            dist_d = np.hypot(sub_x, sub_y / 1.18)

            # Droplet convex lens mask
            drop_mask = np.clip((r_drop - dist_d) / 3.0, 0.0, 1.0)[..., None]
            # Wet track above droplet (`sub_y < 0` and `|sub_x| < r_drop * 0.48`)
            wake_mask = (
                np.clip((r_drop * 0.48 - np.abs(sub_x)) / 3.0, 0.0, 1.0)
                * np.clip((-sub_y) / 8.0, 0.0, 1.0)
                * np.clip(1.0 - (-sub_y) / (r_drop * 4.2), 0.0, 1.0)
            )[..., None]

            total_m = np.maximum(drop_mask, wake_mask * 0.65)
            # Inside droplet & wake, show magnified/refracted `past_rgb` (the moment the drop passed) + specular rim
            rim = (np.clip(1.0 - np.abs(dist_d - r_drop * 0.82) / 2.2, 0.0, 1.0) * (dist_d <= r_drop))[..., None]
            sub_past = past_rgb[y0:y1, x0:x1]
            drop_col = np.clip(sub_past * 1.12 + 0.14 * c_glow2[None, None, :] + rim * 0.42, 0.0, 1.0)
            out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1.0 - total_m) + drop_col * total_m

    elif poem_num == 4:
        # FX04: 08 Darkroom Silver-Gelatin Print in Tray + 03 Two-Block Linocut (Silver Now + Gold Past)
        # Subtle liquid developer tray wave
        wave_x = (_XX + 2.6 * np.sin(_YY * 0.035 + t * 2.1)).astype(np.float32)
        wave_y = (_YY + 1.8 * np.cos(_XX * 0.030 + t * 1.7)).astype(np.float32)
        tray_rgb = cv2.remap(out, wave_x, wave_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        lum = tray_rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        silver_tone = np.stack([lum * 0.92 + 0.04, lum * 0.94 + 0.04, lum * 1.02 + 0.06], axis=-1)
        out = 0.52 * silver_tone + 0.48 * tray_rgb

        # Two-block linocut second block: luminous gold (`c_glow2`) for "what the picture just let go"
        motion_delta = np.mean(np.abs(curr_rgb - past_rgb), axis=2)
        gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
        grad = np.clip(np.hypot(gx, gy) * 1.8, 0.0, 1.0)
        gold_block = np.clip(motion_delta * 3.8 + grad * 0.28 * disp, 0.0, 0.85)[..., None]
        gold_ink = np.array([0.95, 0.68, 0.18], dtype=np.float32)[None, None, :]
        out = out * (1.0 - gold_block * 0.62) + gold_ink * (gold_block * 0.62)

    elif poem_num == 5:
        # FX05: 23/24 Semantic 3D Heart-Scan Depth Front (`LIFT · LABEL · STAR`) + 09 Constellation Stars
        z_front = (t * 0.26) % 1.0
        band = np.exp(-((disp - z_front) / 0.055) ** 2)[..., None]
        out = np.clip(out + band * (0.55 * c_glow1[None, None, :] + 0.45 * c_glow2[None, None, :]) * 0.52, 0.0, 1.0)

        # Constellation star-lines & named semantic nodes in the upper/mid field
        overlay = Image.fromarray((np.clip(out, 0.0, 1.0) * 255.0).astype(np.uint8)).convert("RGBA")
        d_ov = ImageDraw.Draw(overlay)
        f_lbl = get_font("mono", 11)
        nodes = [
            (int(W * 0.22 + 12 * math.sin(t * 0.7)), int(H * 0.24), "STAR · ANCESTOR I"),
            (int(W * 0.48 + 10 * math.cos(t * 0.6)), int(H * 0.18), "SOURCE · SOUTHERN PINE"),
            (int(W * 0.74 - 12 * math.sin(t * 0.8)), int(H * 0.26), "CLASS · HEART-SCAN"),
            (int(W * 0.36 + 8 * math.sin(t * 0.9)), int(H * 0.46), "BODY · BLOODLINE"),
            (int(W * 0.64 - 8 * math.cos(t * 0.7)), int(H * 0.42), "GATE · NEW UNIVERSE"),
        ]
        # Connect constellation thread
        for i in range(len(nodes) - 1):
            d_ov.line([nodes[i][:2], nodes[i + 1][:2]], fill=(249, 174, 6, 115), width=1)
        for nx, ny, lbl in nodes:
            d_ov.ellipse([nx - 4, ny - 4, nx + 4, ny + 4], fill=(250, 210, 90, 230), outline=(255, 255, 255, 200))
            d_ov.rectangle([nx + 8, ny - 8, nx + 8 + len(lbl) * 7 + 8, ny + 8], fill=(16, 20, 28, 175), outline=(249, 174, 6, 150))
            d_ov.text((nx + 12, ny - 6), lbl, font=f_lbl, fill=(250, 220, 130, 240))
        out = np.asarray(overlay.convert("RGB"), dtype=np.float32) / 255.0

    elif poem_num == 6:
        # FX06: 10/22 Underwater Caustic Net & Falling Atlantis Waterline
        # Waterline descends from y = 0.22*H to y = 0.76*H across each station
        water_y = H * (0.24 + 0.50 * u_seg) + 10.0 * np.sin(_XX * 0.025 + t * 2.4)
        submerged = np.clip((_YY - water_y) / 14.0, 0.0, 1.0)
        meniscus = np.exp(-((_YY - water_y) / 3.5) ** 2)[..., None]

        # Procedural refracted caustic light net (`22 One Note` / `10 Warm Dome`)
        u_cx = _XX * 0.022 + t * 1.3 + 2.5 * disp
        u_cy = _YY * 0.028 - t * 0.95 + 2.5 * disp
        c_net = 0.5 + 0.25 * (np.sin(u_cx + np.sin(u_cy * 1.4)) + np.cos(u_cy + np.cos(u_cx * 1.3)))
        c_peaks = np.power(np.clip(c_net, 0.0, 1.0), 3.6)[..., None]

        # Underwater ripple below waterline
        wx = (_XX + submerged * 3.5 * np.sin(_YY * 0.06 + t * 2.8)).astype(np.float32)
        wy = (_YY + submerged * 2.5 * np.cos(_XX * 0.05 + t * 2.2)).astype(np.float32)
        rippled = cv2.remap(out, wx, wy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        water_col = np.clip(rippled * 0.88 + 0.12 * c_glow1[None, None, :] + c_peaks * (0.42 * c_glow1 + 0.28 * c_glow2)[None, None, :], 0.0, 1.0)
        sub_m = submerged[..., None]
        out = out * (1.0 - sub_m) + water_col * sub_m + meniscus * (0.6 * c_glow1 + 0.4 * np.ones(3, dtype=np.float32))[None, None, :] * 0.65
        out = np.clip(out, 0.0, 1.0)

    elif poem_num == 7:
        # FX07: 01 Borrowed Light Radial Time-Delay + 16 Magic Circle Turntable Rings & 11 Petals
        # Radial blend: center = present (`curr_rgb`), outer rings blend `past_rgb` with watercolor softness
        soft_past = cv2.GaussianBlur(past_rgb, (0, 0), 5.0)
        r_weight = np.clip((_RAD - 0.18) / 0.75, 0.0, 1.0)[..., None]
        out = curr_rgb * (1.0 - 0.55 * r_weight) + soft_past * (0.55 * r_weight)

        # Concentric turntable harmonic rings (`16 Magic Circle`: "wedding bands diverging across abstract skies")
        rings = np.power(0.5 + 0.5 * np.sin(_RAD * 28.0 - t * 3.2), 6.0)[..., None]
        ring_env = rings * np.clip(_RAD[..., None] * 1.2, 0.0, 1.0) * (1.0 - 0.5 * disp[..., None])
        out = np.clip(out + ring_env * (0.5 * c_glow1 + 0.5 * c_glow2)[None, None, :] * 0.32, 0.0, 1.0)

    elif poem_num == 8:
        # FX08: S1 Seeing-As Astral Aspect Split + A2b Subject-Alone Smoke + 14 Warm Phosphor
        # Separate foreground subject and project a displaced astral soul double that orbits and returns
        fg_w = np.clip((disp - 0.45) / 0.35, 0.0, 1.0)
        fg_w = cv2.GaussianBlur(fg_w, (0, 0), 10.0)[..., None]

        sep_env = math.sin(math.pi * u_seg)  # 0 at start, peaks mid-station ("escapes my body"), 0 at end ("back to my body")
        shift_x = 46.0 * sep_env * math.sin(t * 1.1)
        shift_y = -26.0 * sep_env * (0.5 + 0.5 * math.cos(t * 0.8))
        M_soul = np.array([[1.0, 0.0, shift_x], [0.0, 1.0, shift_y]], dtype=np.float32)
        soul_rgb = cv2.warpAffine(past_rgb, M_soul, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        soul_m = cv2.warpAffine(fg_w[..., 0], M_soul, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)[..., None]

        # A2b Curl-smoke & Warm Phosphor aura around the displaced soul double
        soul_tinted = 0.55 * soul_rgb + 0.45 * c_glow1[None, None, :]
        alpha_soul = soul_m * (0.38 * sep_env)
        out = np.clip(out * (1.0 - alpha_soul) + soul_tinted * alpha_soul, 0.0, 1.0)

    elif poem_num == 9:
        # FX09: 09 Carry the Glow 3D Normal Relighting + 11/21 Three Voice Waveform Threads
        # 1. Compute 3D surface normals from `disp` and relight with a warm travelling lantern
        dz_dx = cv2.Sobel(disp, cv2.CV_32F, 1, 0, ksize=5) * 4.5
        dz_dy = cv2.Sobel(disp, cv2.CV_32F, 0, 1, ksize=5) * 4.5
        norm_len = np.sqrt(dz_dx ** 2 + dz_dy ** 2 + 1.0)
        nx, ny, nz = -dz_dx / norm_len, -dz_dy / norm_len, 1.0 / norm_len

        lx = W * (0.5 + 0.32 * math.sin(t * 0.65))
        ly = H * (0.44 + 0.18 * math.cos(t * 0.48))
        dlx = (lx - _XX) / (W * 0.55)
        dly = (ly - _YY) / (H * 0.55)
        dlz = 0.65
        l_len = np.sqrt(dlx ** 2 + dly ** 2 + dlz ** 2)
        ndotl = np.clip((nx * dlx + ny * dly + nz * dlz) / l_len, 0.0, 1.0)
        atten = np.exp(-(dlx ** 2 + dly ** 2) * 1.15)
        warm_light = (ndotl * atten)[..., None]

        warm_col = np.array([1.0, 0.76, 0.36], dtype=np.float32)[None, None, :]
        out = np.clip(out * (0.82 + 0.28 * warm_light) + warm_light * warm_col * 0.26, 0.0, 1.0)

        # 2. Three delicate luminous voice-waveform threads ("three calls before leaving")
        for call_i in range(3):
            y_base = H * (0.28 + call_i * 0.18)
            freq = 0.014 + call_i * 0.004
            amp = (14.0 + call_i * 6.0) * math.sin(t * 2.2 + call_i * 1.3)
            y_wave = y_base + amp * np.sin(_XX * freq + t * (3.0 + call_i)) * np.sin(_XX * 0.004 - t * 0.8)
            thread = np.exp(-((_YY - y_wave) / 2.2) ** 2)[..., None]
            t_col = c_glow2 if call_i == 1 else c_glow1
            out = np.clip(out + thread * t_col[None, None, :] * 0.38, 0.0, 1.0)

    elif poem_num == 10:
        # FX10: 07 Nine Thousand Firefly Pinholes + 04 Past the Red Dot-by-Dot Dawn
        # Progressive dawn wave ("night replaced by morning, dot by dot")
        dawn_front = u_seg * 1.25 - 0.12
        dist_from_dawn = (_XN * 0.65 - _YN * 0.35) * 0.5 + 0.5
        dawn_mask = np.clip((dawn_front - dist_from_dawn + 0.25) / 0.45, 0.0, 1.0)[..., None]

        # 9,000-pinhole lattice (`cell = 11px` -> `116 x 65 = 7,540` to `9,000` pinholes)
        cell = 10.0
        gx_c = ((_XX % cell) - cell * 0.5) / (cell * 0.5)
        gy_c = ((_YY % cell) - cell * 0.5) / (cell * 0.5)
        r_cell = np.hypot(gx_c, gy_c)
        blink = 0.65 + 0.35 * np.sin((_XX // cell) * 1.7 + (_YY // cell) * 2.3 + t * 3.4)
        pinhole = np.clip(1.0 - r_cell / (0.62 + 0.65 * dawn_mask[..., 0] * blink), 0.0, 1.0)[..., None]

        # Night kraft/pinhole state vs warm Risograph dawn state
        pinhole_view = out * (0.42 + 0.58 * pinhole) + pinhole * (1.0 - dawn_mask) * c_glow2[None, None, :] * 0.25
        dawn_warm = np.clip(out * 1.06 + 0.12 * c_glow2[None, None, :], 0.0, 1.0)
        out = pinhole_view * (1.0 - dawn_mask) + dawn_warm * dawn_mask

    elif poem_num == 11:
        # FX11: A1 Depth Sea-Fog + 19 Thirty-Course Nipkow Temple Assembly + 07 Volumetric Sun Rays
        # 30 horizontal architectural courses scanning upward ("the temple assembles, one course at a time")
        n_courses = 30
        course_idx = np.floor((H - 1 - _YY) / (H / float(n_courses)))
        assembled_courses = (0.25 + 0.85 * u_seg) * n_courses
        course_ready = np.clip(assembled_courses - course_idx, 0.0, 1.0)[..., None]
        course_seam = (np.exp(-((assembled_courses - course_idx) / 0.85) ** 2) * (np.mod(_YY, H / float(n_courses)) < 2.5))[..., None]

        # Unassembled upper courses sit in soft morning sea-fog (`A1 Fog` by depth)
        fog_plate = cv2.GaussianBlur(out, (0, 0), 11.0)
        fog_col = 0.65 * fog_plate + 0.35 * np.array([0.82, 0.85, 0.88], dtype=np.float32)[None, None, :]
        out = fog_col * (1.0 - course_ready * 0.85) + out * (course_ready * 0.85 + 0.15)

        # Volumetric dawn sun-rays streaming from top-center (`07-spacetime` RAYS)
        ray_ang = np.arctan2(_YY + 60.0, _XX - W * 0.52)
        rays = np.power(0.5 + 0.5 * np.sin(ray_ang * 22.0 + t * 0.8), 4.0) * np.exp(-_YY / (H * 0.75)) * (1.0 - disp * 0.5)
        out = np.clip(out + rays[..., None] * c_glow2[None, None, :] * 0.28 + course_seam * c_glow2[None, None, :] * 0.55, 0.0, 1.0)

    elif poem_num == 12:
        # FX12: M3 Burning Hourglass Sand of Time + A4 Parting Winds
        # Lower mirror-pool (`y > 0.64 * H`) accumulates golden reflections & falling time-grains
        pool_y = H * 0.64
        in_pool = np.clip((_YY - pool_y) / 18.0, 0.0, 1.0)[..., None]
        # Mirror reflection of upper scene mixed with past_rgb ("each fallen grain keeps its moment")
        mirror_y = np.clip(2.0 * pool_y - _YY, 0, H - 1).astype(np.float32)
        mirror_x = (_XX + 4.0 * np.sin(_YY * 0.12 + t * 2.6)).astype(np.float32)
        pool_refl = cv2.remap(past_rgb, mirror_x, mirror_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        out = out * (1.0 - 0.38 * in_pool) + (0.78 * pool_refl + 0.22 * c_glow2[None, None, :]) * (0.38 * in_pool)

        # Falling hourglass sand stream near the center/golden columns
        waist_env = np.exp(-((_XX - W * 0.5) / (W * 0.18 + 0.22 * np.abs(_YY - H * 0.5))) ** 2)
        grain_hash = np.sin(_XX * 1.9 + (_YY - t * 110.0) * 0.85) * np.cos(_XX * 1.3 - (_YY - t * 95.0) * 0.6)
        grains = np.clip((grain_hash - 0.72) / 0.28, 0.0, 1.0) * waist_env
        out = np.clip(out + grains[..., None] * c_glow2[None, None, :] * 0.48, 0.0, 1.0)

    elif poem_num == 13:
        # FX13: 06 Daimonji Revolving Lantern Orbits + V2 Paper-Marbled Wakes + M2a Gate Burn
        # Two orbiting Keplerian moons ("The couples orbit each other the way Jupiter keeps its moons")
        for m_i in range(2):
            ang_m = t * 1.15 + m_i * math.pi
            mx = W * 0.5 + (W * 0.26) * math.cos(ang_m)
            my = H * 0.46 + (H * 0.14) * math.sin(ang_m)
            d_moon = np.hypot(_XX - mx, _YY - my)
            moon_glow = np.exp(-(d_moon / 68.0) ** 2)[..., None]
            m_col = c_glow2 if m_i == 0 else c_glow1
            out = np.clip(out + moon_glow * m_col[None, None, :] * 0.28, 0.0, 1.0)

        # M2a Gate-burn amber/scarlet rim near the end of each station ("Life has burned all our stories")
        if u_seg > 0.72:
            b_prog = (u_seg - 0.72) / 0.28
            noise_field = 0.5 + 0.25 * (np.sin(_XX * 0.015 + t) + np.cos(_YY * 0.018 - t)) + 0.25 * (1.0 - _RAD)
            burn_rim = np.exp(-((noise_field - (1.05 - b_prog * 0.65)) / 0.055) ** 2)[..., None]
            scarlet = np.array([0.96, 0.34, 0.12], dtype=np.float32)[None, None, :]
            out = np.clip(out + burn_rim * scarlet * 0.68, 0.0, 1.0)

    elif poem_num == 14:
        # FX14: 08 Warm Cave Ground-Up Thermal Scanline + A3 Weather Haze + Vintage Doorway Aperture
        # Ground-up scanline ("It takes me last, and from the ground up")
        scan_y = H * (1.0 - ((t * 0.22) % 1.0))
        scan_line = np.exp(-((_YY - scan_y) / 6.0) ** 2)[..., None]
        below_scan = np.clip((_YY - scan_y) / 24.0, 0.0, 1.0)[..., None]

        # Infrared thermal memory below the rising scanline (`08 Warm Cave`)
        lum_past = past_rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        ir_col = np.stack([
            np.clip(lum_past * 1.35, 0.0, 1.0),
            np.clip(lum_past * 0.72, 0.0, 1.0),
            np.clip(0.25 + (1.0 - lum_past) * 0.45, 0.0, 1.0)
        ], axis=-1)
        out = out * (1.0 - 0.28 * below_scan) + ir_col * (0.28 * below_scan)
        out = np.clip(out + scan_line * c_glow2[None, None, :] * 0.65, 0.0, 1.0)

        # Subtle glowing doorway frame ("I choose the door: An old door... opens on a slow panorama")
        door_w = W * (0.28 + 0.18 * u_seg)
        door_h = H * (0.42 + 0.18 * u_seg)
        dx_d = np.abs(_XX - W * 0.5)
        dy_d = np.abs(_YY - H * 0.48)
        door_rim = (
            (np.exp(-((dx_d - door_w) / 3.5) ** 2) * (dy_d <= door_h))
            + (np.exp(-((dy_d - door_h) / 3.5) ** 2) * (dx_d <= door_w))
        )[..., None]
        out = np.clip(out + door_rim * c_glow2[None, None, :] * 0.42, 0.0, 1.0)

    return np.clip(out, 0.0, 1.0)


def draw_afterlight_videotext_hud(img_rgb_float, poem_num, poem_title, district_name, body_hex, glow_hex, spec, active_st, st_idx, n_st):
    """
    Renders:
      1. Top-left archival paper margin tag (`PHOTOGRAPHED / CEL PLATE` + `AFTERLIGHT FX · <fx_code>`),
         styled after `04-afterlife-essay` and `23-golden-record`.
      2. Clean 56px lower-third Videotext clock bar with City District `body` + `glow` palette swatches.
    """
    pil_im = Image.fromarray((np.clip(img_rgb_float, 0.0, 1.0) * 255.0).astype(np.uint8)).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    f_mono = get_font("mono", 12)
    f_mono_sm = get_font("mono", 11)
    f_italic = get_font("serif_italic", 18)

    # Top-left archival paper slip (`ebe3cf` paper with `1c1814` double border, compact 28px high)
    slip_text = f"AFTERLIGHT FX [{spec['fx_code']}] · {spec['fx_name'].upper()[:48]}"
    slip_w = min(W - 40, len(slip_text) * 7 + 28)
    d.rectangle([18, 16, 18 + slip_w, 44], fill=(235, 227, 207, 228), outline=(28, 24, 20, 240), width=1)
    d.text((28, 23), slip_text, font=f_mono, fill=(28, 24, 20, 255))

    # Lower-third bar (`y = 662..720`)
    bar_y0 = H - 58
    d.rectangle([0, bar_y0, W, H], fill=(16, 18, 24, 226))
    d.line([(0, bar_y0), (W, bar_y0)], fill=(235, 195, 120, 190), width=1)

    top_left = f"P{poem_num:02d} · {poem_title.upper()}  |  {active_st['kind_badge']}  [{st_idx + 1}/{n_st}]"
    d.text((20, bar_y0 + 7), top_left[:90], font=f_mono, fill=(250, 188, 92, 255))

    place_title = f"{active_st['id']} · {active_st['name']}"
    verse_line = active_st["line"]
    sub_str = f"{place_title}: “{verse_line}”"
    if len(sub_str) > 106:
        sub_str = sub_str[:104] + "…”"
    d.text((20, bar_y0 + 27), sub_str, font=f_italic, fill=(245, 240, 230, 255))

    swatches = list((body_hex or [])[:5]) + list((glow_hex or [])[:4])
    if not swatches:
        swatches = ["#262423", "#2d4651", "#337993", "#64b4ce", "#01acd4"]
    sw_w, sw_h = 20, 16
    total_w = len(swatches) * sw_w
    x0 = W - 20 - total_w
    y0 = bar_y0 + 10
    for i, hx in enumerate(swatches):
        c_u8 = hex_to_rgb_u8(hx)
        sx = x0 + i * sw_w
        d.rectangle([sx, y0, sx + sw_w - 2, y0 + sw_h], fill=c_u8 + (255,), outline=(240, 235, 225, 190))

    pal_lbl = f"{district_name.upper()[:18]} PALETTE"
    d.text((x0, y0 + sw_h + 4), pal_lbl, font=f_mono_sm, fill=(215, 210, 198, 230))

    comp = Image.alpha_composite(pil_im, overlay).convert("RGB")
    return np.asarray(comp, dtype=np.uint8)


def eval_station_with_past(station, mp, u_local, phase_t):
    """
    Evaluates both the present multiplane-warped frame (`curr_warped`) and a delayed frame
    (`past_warped`, ~0.6s earlier) with direct integer frame indexing so moving figures never ghost.
    """
    frames = station["frames"]
    n_f = len(frames)
    f_pos = np.clip(u_local, 0.0, 1.0) * (n_f - 1)
    idx_curr = min(n_f - 1, max(0, int(round(f_pos))))
    idx_past = min(n_f - 1, max(0, idx_curr - 7))

    u_centered = u_local - 0.5
    pan_x = mp["pan_dir"] * (u_centered * 32.0 + 3.5 * math.sin(phase_t * 0.45))
    tilt_y = mp["tilt_dir"] * (u_centered * 10.0 + 2.2 * math.cos(phase_t * 0.38))
    dolly_scale = 1.07 + 0.07 * np.clip(u_local, 0.0, 1.0)
    depth_stretch = 0.045 * np.clip(u_local, 0.0, 1.0)

    curr_w = warp_multiplane_3d(frames[idx_curr], mp["disp"], pan_x, tilt_y, dolly_scale, depth_stretch)
    past_w = warp_multiplane_3d(frames[idx_past], mp["disp"], pan_x * 0.85, tilt_y * 0.85, dolly_scale, depth_stretch)
    return curr_w, past_w


def render_poem_afterlight_frame(poem_num, poem_title, district_name, stations, multiplanes, t, total_dur):
    spec = POEM_AFTERLIGHT_SPEC[poem_num]
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
        poem_num, curr_rgb, past_rgb, mp_curr["disp"], u_seg, t, st_curr["body_hex"], st_curr["glow_hex"]
    )

    trans_start = 0.70
    if u_seg <= trans_start:
        canvas = fx_curr
        active_st = st_curr
        active_k = seg_idx
    else:
        u_tr = smootherstep((u_seg - trans_start) / (1.0 - trans_start))
        u_next_local = 0.25 * u_tr
        next_rgb, next_past = eval_station_with_past(st_next, mp_next, u_next_local, t)
        fx_next = apply_poem_afterlight_fx(
            poem_num, next_rgb, next_past, mp_next["disp"], u_next_local, t, st_next["body_hex"], st_next["glow_hex"]
        )
        depth_bias = 0.16 * (mp_next["disp"] - mp_curr["disp"])
        w_next = np.clip(u_tr + depth_bias * math.sin(math.pi * u_tr), 0.0, 1.0)[..., None]
        canvas = np.clip(fx_curr * (1.0 - w_next) + fx_next * w_next, 0.0, 1.0)
        if u_tr < 0.5:
            active_st = st_curr
            active_k = seg_idx
        else:
            active_st = st_next
            active_k = (seg_idx + 1) % n_st

    return draw_afterlight_videotext_hud(
        canvas,
        poem_num=poem_num,
        poem_title=poem_title,
        district_name=active_st["district_name"],
        body_hex=active_st["body_hex"],
        glow_hex=active_st["glow_hex"],
        spec=spec,
        active_st=active_st,
        st_idx=active_k,
        n_st=n_st,
    )


def build_poem_videotext_entry(poem_num, poem_meta, poem_title, district_name, body_hex, glow_hex, construct_stations, scion_list, total_dur=30.0):
    """
    Constructs the exact Sosuke Afterlight Videotext data structure for `poem_num`, laying out:
      - Movements (`f: true`, centered display cards)
      - Apparatus / Common Place / Painted Cel / Afterlight FX margin logs (`tape: true`, monospace)
      - Poetic lyric lines (`f: false, tape: false`, indented serif with drop-cap on the first line)
    on the film's 30.0s clock so scrolling through the text seeks the film and playing the film scrolls the text.
    """
    spec = POEM_AFTERLIGHT_SPEC[poem_num]
    movements = poem_meta.get("movements", [])
    n_st = len(construct_stations)
    seg_dur = total_dur / float(max(1, n_st))

    scenes = []
    # Scene 0: Opening title + Afterlight FX apparatus log
    scenes.append([
        {"t0": 0.15, "t1": 2.6, "who": f"POEM {poem_num:02d} · {district_name.upper()}", "say": f"{poem_title} — {spec['fx_name']}", "f": True, "tape": False},
        {"t0": 0.35, "t1": 3.2, "who": "", "say": f"AFTERLIGHT VIDEOTEXT FX [{spec['fx_code']}] · {spec['afterlight_ref']}", "f": False, "tape": True},
    ])

    for k, st in enumerate(construct_stations):
        t_start = k * seg_dur
        t_end = (k + 1) * seg_dur
        mv = movements[min(k, len(movements) - 1)] if movements else {"label": f"STATION {k+1}", "line": st["line"]}
        block = []
        # 1. Movement / Station card (`f: True`)
        if k < len(movements):
            block.append({
                "t0": round(t_start + 0.25, 2),
                "t1": round(t_start + 2.4, 2),
                "who": f"MOVEMENT {k+1} · {mv.get('label', '')}",
                "say": mv.get("line", st["line"]),
                "f": True,
                "tape": False,
            })
        # 2. Apparatus / Common Place / Cel tape log (`tape: True`)
        block.append({
            "t0": round(t_start + 0.55, 2),
            "t1": round(t_start + 3.6, 2),
            "who": "",
            "say": f"{st['kind_badge']} · {st['id']} · {st['name']} · PALETTE {' '.join((body_hex or [])[:2] + (glow_hex or [])[:2])}",
            "f": False,
            "tape": True,
        })
        # 3. Poetic verse & spatial description from `st` and matching `scion_list` shots (`f: False, tape: False`)
        block.append({
            "t0": round(t_start + 1.4, 2),
            "t1": round(t_end - 1.2, 2),
            "who": st["name"],
            "say": st["line"],
            "f": False,
            "tape": False,
        })
        # Add an additional SCION shot lyric if available
        sc_idx = min(len(scion_list) - 1, k * 2 + 1) if scion_list else -1
        if sc_idx >= 0 and scion_list[sc_idx].get("line") and scion_list[sc_idx].get("line") != st["line"]:
            sc_item = scion_list[sc_idx]
            block.append({
                "t0": round(t_start + 3.1, 2),
                "t1": round(t_end - 0.3, 2),
                "who": sc_item.get("name", sc_item.get("id", "")),
                "say": sc_item.get("line", ""),
                "f": False,
                "tape": False,
            })
        scenes.append(block)

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
        "video_fx": f"data/terrarium/seeing_spacetime_films/poem_{poem_num:02d}_videotext_fx.mp4?v=9",
        "video_construct": f"data/terrarium/seeing_spacetime_films/poem_{poem_num:02d}_construct.mp4?v=8",
        "video_worm": f"data/terrarium/seeing_spacetime_films/poem_{poem_num:02d}_spacetime_worm.mp4?v=8",
        "poster": f"videos/poems/poem_{poem_num:02d}_videotext_fx.jpg",
        "picture": spec["picture"],
        "sound": spec["sound"],
        "code": spec["code"],
        "after": spec["after"],
        "scenes": scenes,
    }


def build_single_poem_afterlight_fx(poem_num):
    city_data, districts_by_id, bible_to_dir, id_to_dir, hero_poems = build_city_master_index()
    poem_title, district_name, body_hex, glow_hex, scion_list, scene_map, ordered_out_dirs, local_view_info = collect_poem_places_cels_and_palettes(
        poem_num, city_data, districts_by_id, bible_to_dir, id_to_dir, hero_poems
    )
    poems_json = json.load(open(os.path.join(SHOTS_ROOT, "film/poems.json")))
    poem_meta = next((p for p in poems_json if int(p["num"]) == poem_num), {})

    audio_t0 = float(scion_list[0]["t0"]) if scion_list else (poem_num - 1) * 90.0

    terr_stations = [
        load_common_place_station(od, local_view_info, district_name, body_hex, glow_hex, n_frames=48)
        for od in ordered_out_dirs[:4]
    ]
    poem_bundles = [
        load_poem_cel_shot(sc, scene_map, district_name, body_hex, glow_hex, n_frames=48)
        for sc in scion_list[:4]
    ]

    if len(terr_stations) >= 3 and len(poem_bundles) >= 2:
        stations = [
            terr_stations[0],
            poem_bundles[0],
            terr_stations[1],
            poem_bundles[min(1, len(poem_bundles) - 1)],
            terr_stations[2],
        ]
    else:
        stations = (terr_stations + poem_bundles)[:5]

    multiplanes = [prepare_station_multiplane(st, k) for k, st in enumerate(stations)]

    dur = 30.0
    n_frames_total = int(dur * FPS)
    frames_out = []
    for f_i in range(n_frames_total):
        t = f_i / float(FPS)
        frames_out.append(
            render_poem_afterlight_frame(poem_num, poem_title, district_name, stations, multiplanes, t, dur)
        )

    out_mp4 = os.path.join(OUT_DIR, f"poem_{poem_num:02d}_videotext_fx.mp4")
    encode_video_with_real_audio(frames_out, out_mp4, audio_t0)

    os.makedirs(POEMS_VID_DIR, exist_ok=True)
    shutil.copy2(out_mp4, os.path.join(POEMS_VID_DIR, f"poem_{poem_num:02d}_videotext_fx.mp4"))
    sample_fr = frames_out[int(2.4 * FPS)]
    Image.fromarray(sample_fr).save(os.path.join(POEMS_VID_DIR, f"poem_{poem_num:02d}_videotext_fx.jpg"), quality=92)

    vtext_entry = build_poem_videotext_entry(
        poem_num, poem_meta, poem_title, district_name, body_hex, glow_hex, stations, scion_list, total_dur=dur
    )
    return {
        "poem_num": poem_num,
        "poem_title": poem_title,
        "district_name": district_name,
        "fx_code": POEM_AFTERLIGHT_SPEC[poem_num]["fx_code"],
        "fx_name": POEM_AFTERLIGHT_SPEC[poem_num]["fx_name"],
        "mp4": out_mp4,
        "sample_frame": sample_fr,
        "vtext_entry": vtext_entry,
    }


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(POEMS_VID_DIR, exist_ok=True)

    if len(sys.argv) > 1:
        poems_to_run = [int(x) for x in sys.argv[1:]]
    else:
        poems_to_run = list(range(1, 15))

    print(f"Building Afterlight Videotext Effect Films (FX01..FX14) for Poems: {poems_to_run}", flush=True)
    results = []
    if len(poems_to_run) == 1:
        r = build_single_poem_afterlight_fx(poems_to_run[0])
        results.append(r)
        print(f"Done P{r['poem_num']:02d} [{r['fx_code']}] {r['fx_name']}: {r['mp4']}", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(build_single_poem_afterlight_fx, p): p for p in poems_to_run}
            for fut in as_completed(futs):
                r = fut.result()
                results.append(r)
                print(f"Done P{r['poem_num']:02d} ({r['poem_title']} · {r['district_name']}) -> [{r['fx_code']}] {r['fx_name']}", flush=True)

    results.sort(key=lambda x: x["poem_num"])

    if len(results) == 14:
        manifest = {
            "title": "WYGWYL · Afterlight Videotext & 14 Picture-Technique Suite",
            "subtitle": "Each poem on its own film clock, paired with a bespoke Afterlight visual effect.",
            "poems": [r["vtext_entry"] for r in results],
        }
        manifest_path = os.path.join(OUT_DIR, "videotext_manifest.json")
        with open(manifest_path, "w") as jf:
            json.dump(manifest, jf, indent=2)

        # Build 4x4 contact sheet of all 14 Afterlight Videotext Effects
        cols, rows = 4, 4
        tw, th = 480, 270
        sheet = Image.new("RGB", (cols * tw, rows * th), (235, 227, 207))
        for i, r in enumerate(results):
            wx, wy = (i % cols) * tw, (i // cols) * th
            im_tile = Image.fromarray(r["sample_frame"]).resize((tw, th), Image.Resampling.LANCZOS)
            sheet.paste(im_tile, (wx, wy))

        sheet_path = os.path.join(OUT_DIR, "all_14_poems_afterlight_videotext_fx_sheet.png")
        sheet.save(sheet_path)
        sheet.save(os.path.join(ARTIFACT_DIR, "all_14_poems_afterlight_videotext_fx_sheet.png"))
        print("Saved manifest & contact sheet:", manifest_path, sheet_path, flush=True)
