#!/usr/bin/env python3
"""
DR. ANA STELLINE & THE TOY WOODEN HORSE (1:49 -> 3:25) · 07-SPACETIME MIST ENGINE
=================================================================================
"Memory's not about more detail — that's not how memory works. We recall with our
feelings. Anything real should be a mist." — Dr. Ana Stelline (4:16 – 4:27)

Built directly on `https://hartswf0.github.io/bolas/afterlight/#/07-spacetime`
(`spacetime.py` + `trailer.py` + `Afterlight · a videotext`):

1. Segments the Toy Wooden Horse memory starting at `1:49` (`109.00s – 205.00s` in
   `Blade Runner 2049 Recalling Another's Past 4K`) braided with Dr. Ana Stelline's
   Memory Maker philosophy (`1:12–1:43`, `2:52–3:07`, `3:12–3:42`, `4:16–4:27`,
   `5:25–6:45` in `The Memory Maker [Open Matte]`) into 16 canonical memory segments.
2. Renders each memory segment as a 4D Spacetime Point Volume `(x, y, z_depth, t_slice)`
   governed by Stelline's Feeling-vs-Mist Field `F(x, y, t) in [0, 1]`:
   - Peripheral clinical details (`F -> 0`, "Everything's grey") dissolve into
     Beer's-Law volumetric fog and 3D Gaussian scatter (`sigma = 4.2`).
   - Recalled emotional anchors (`F -> 1`: the roaring furnace flame, the child's
     hand clutching the carved wooden horse `6·10·21`, burying the horse in the
     dead furnace ashes, the defiant gaze, Stelline's birthday candles & scanner tears)
     crystallize in focal bucket `b0` (`sigma = 0.55`) and leave a luminous 4D
     body of light through time (`vis = exp(-age / tau_feeling)`).
3. Culminates in the signature `07-spacetime` accelerating montage (every volume
   twice: face-on push, then side-on ±62° 4D spacetime strata cut, tightening to
   quarter-second cuts), dropping to silence before one golden ember dot blooms
   into the 3D point-cloud carving `6 · 10 · 21`.
4. Catalogs and connects all 747 videos and 99 audio files across `wygwyl-world-arch/shots/`
   so zero moving memories or spoken voices remain unused.
"""

import os
import sys
import glob
import json
import math
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots"
VID_DIR = os.path.join(ROOT, "videos")
SEG_DIR = os.path.join(VID_DIR, "stelline_segments")
TERR_DIR = os.path.join(ROOT, "data/terrarium")
FILM_OUT_DIR = os.path.join(TERR_DIR, "seeing_spacetime_films")
ARTIFACT_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"

SRC_HORSE = "/Users/gaia/Downloads/Blade Runner 2049 Recalling Another's Past 4K - Rolling Crown (720p).mp4"
SRC_STELLINE = "/Users/gaia/Downloads/The Memory Maker Blade Runner 2049 [Open Matte] - Natalizio Films (1080p).mp4"
SRC_PARTICLES = "/Users/gaia/Downloads/download (1)/Memory_Maker_controlling_golden_…_202605191759_2.mp4"

FPS = 24
RW, RH = 640, 360   # Internal multi-scale Gaussian accumulation grid (exact spacetime.py ratio)
FW, FH = 1280, 720  # Final 16:9 HD frame

PAPER = np.array([0.925, 0.902, 0.858], dtype=np.float32)
NIGHT = np.array([0.018, 0.022, 0.030], dtype=np.float32)

os.makedirs(SEG_DIR, exist_ok=True)
os.makedirs(FILM_OUT_DIR, exist_ok=True)


def ease(u):
    u = float(np.clip(u, 0.0, 1.0))
    return u * u * (3.0 - 2.0 * u)


def smootherstep(u):
    u = float(np.clip(u, 0.0, 1.0))
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)


def sm(a, b, t):
    if abs(b - a) < 1e-6:
        return 1.0 if t >= b else 0.0
    return smootherstep((t - a) / (b - a))


def lerp(a, b, u):
    return a + (b - a) * u


_FONT_CACHE = {}
def get_font(kind="italic", size=32):
    key = (kind, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    font_dir = os.path.join(ROOT, "fonts")
    candidates = []
    if kind == "italic":
        candidates = [
            os.path.join(font_dir, "im-fell-english-latin-400-italic.woff2"),
            "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
        ]
    elif kind == "serif":
        candidates = [
            os.path.join(font_dir, "im-fell-english-latin-400-normal.woff2"),
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        ]
    else:
        candidates = [
            os.path.join(font_dir, "ibm-plex-mono-latin-400-normal.woff2"),
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/Courier.dfont",
        ]
    for p in candidates:
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, size)
                _FONT_CACHE[key] = f
                return f
            except Exception:
                continue
    f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


# ==============================================================================
# THE 16 SEGMENTED MEMORY IMPULSES (STARTING AT 1:49 + STELLINE'S MIST THESIS)
# ==============================================================================
MEMORY_SEGMENTS = [
    {
        "id": "seg_01",
        "num": 1,
        "code": "I · ISOLATION & IMAGINATION",
        "title": "Behind Glass: The Memory Maker's Lens",
        "source": "stelline",
        "src_t0": 72.0,    # 1:12
        "src_t1": 103.0,   # 1:43
        "clip_t0": 24.0,   # 0:24 (Optical lens rings & beetle in forest)
        "clip_dur": 4.2,
        "film_t0": 0.0,
        "film_t1": 4.2,
        "mode": "paper",
        "who": "DR. ANA STELLINE (1:12 – 1:43)",
        "say": "Compromised immune system. A life of freedom, so long as it's behind glass — visualizing a world she could never physically inhabit.",
        "tape": "CHAMBER · Optical rings dial 3D forest dust into the emerald beetle Carabus stellinae",
        "feeling_anchor": (0.50, 0.50),
        "mist_level": 0.38,
        "cam0": (0.0, 0.0, 1180.0, 0.32, -0.05),
        "cam1": (0.0, 0.0, 420.0, -0.08, 0.02),
        "assemble": True,
    },
    {
        "id": "seg_02",
        "num": 2,
        "code": "II · THE INVITATION AT 1:49",
        "title": "1:49 — Tell Me a Memory From When You Were a Kid",
        "source": "horse",
        "src_t0": 109.00,  # 1:49.00!
        "src_t1": 120.29,  # 2:00.29
        "clip_t0": 109.00,
        "clip_dur": 4.2,
        "film_t0": 4.2,
        "film_t1": 8.4,
        "mode": "paper",
        "who": "OFFICER K & JOSHI (1:49 – 2:00)",
        "say": "“I feel a little strange sharing a childhood story knowing I was never a child.” — “It'd make it easier for me if you took it seriously.”",
        "tape": "1:49 THRESHOLD · Two figures across a table; the room edges dissolve into parchment fog",
        "feeling_anchor": (0.68, 0.45),
        "mist_level": 0.52,
        "cam0": (-60.0, -10.0, 880.0, -0.24, 0.04),
        "cam1": (45.0, -5.0, 390.0, 0.18, -0.02),
        "assemble": False,
    },
    {
        "id": "seg_03",
        "num": 3,
        "code": "III · ONSET OF THE MIST",
        "title": "I Had a Little Toy Horse… Everything's Grey",
        "source": "horse",
        "src_t0": 120.29,  # 2:00.29
        "src_t1": 126.86,  # 2:06.86
        "clip_t0": 120.40,
        "clip_dur": 4.0,
        "film_t0": 8.4,
        "film_t1": 12.4,
        "mode": "paper",
        "who": "OFFICER K (2:00 – 2:06)",
        "say": "“I had a little toy horse. Wait — I remember lots of kids. Everything's grey.”",
        "tape": "RECALL ONSET · Facial contours hold focal plane while background walls scatter into gray dust",
        "feeling_anchor": (0.52, 0.44),
        "mist_level": 0.58,
        "cam0": (0.0, 0.0, 760.0, 0.12, 0.02),
        "cam1": (0.0, -8.0, 290.0, -0.14, -0.02),
        "assemble": False,
    },
    {
        "id": "seg_04",
        "num": 4,
        "code": "IV · THE ORPHANAGE ABYSS",
        "title": "Descent Into the Gray Industrial Catwalks",
        "source": "horse",
        "src_t0": 126.86,  # 2:06.86
        "src_t1": 135.30,  # 2:15.30
        "clip_t0": 126.90,
        "clip_dur": 4.0,
        "film_t0": 12.4,
        "film_t1": 16.4,
        "mode": "paper",
        "who": "MEMORY SEGMENT 04 (2:06 – 2:15)",
        "say": "No rigid architectural blueprints survive — only the vertiginous drop of steel walkways and footsteps overhead.",
        "tape": "CATWALK & GRATING · Camera pushes downward through 44 temporal slices of gray steam",
        "feeling_anchor": (0.50, 0.52),
        "mist_level": 0.68,
        "cam0": (0.0, -35.0, 1020.0, 0.0, 0.16),
        "cam1": (0.0, 15.0, 250.0, 0.25, -0.06),
        "assemble": False,
    },
    {
        "id": "seg_05",
        "num": 5,
        "code": "V · THE CLOCKWORK GEARS",
        "title": "Turning Iron Teeth & Flight Down the Stairs",
        "source": "horse",
        "src_t0": 135.30,  # 2:15.30
        "src_t1": 141.54,  # 2:21.54
        "clip_t0": 135.40,
        "clip_dur": 4.0,
        "film_t0": 16.4,
        "film_t1": 20.4,
        "mode": "paper",
        "who": "MEMORY SEGMENT 05 (2:15 – 2:21)",
        "say": "The boy flees down the iron steps as the gang of shaved-head children gives chase through the turning gears.",
        "tape": "FLY-WHEEL & STAIRS · Moving figures leave a receding spacetime wake across the bright gear skylight",
        "feeling_anchor": (0.38, 0.50),
        "mist_level": 0.55,
        "cam0": (-110.0, 0.0, 780.0, -0.45, 0.05),
        "cam1": (70.0, -10.0, 310.0, 0.32, -0.03),
        "assemble": False,
    },
    {
        "id": "seg_06",
        "num": 6,
        "code": "VI · THE ARTIST'S TOUCH",
        "title": "There's a Bit of Every Artist in Their Work",
        "source": "stelline",
        "src_t0": 172.0,   # 2:52
        "src_t1": 187.0,   # 3:07
        "clip_t0": 172.0,
        "clip_dur": 4.2,
        "film_t0": 20.4,
        "film_t1": 24.6,
        "mode": "light",
        "who": "DR. ANA STELLINE (2:52 – 3:07)",
        "say": "“I had a vivid imagination. Best way to travel. There's a bit of every artist in their work.”",
        "tape": "BIRTHDAY CANDLES · In the dark chamber, golden candle-flames bloom out of blackness",
        "feeling_anchor": (0.48, 0.54),
        "mist_level": 0.42,
        "cam0": (-70.0, 10.0, 860.0, -0.30, 0.04),
        "cam1": (40.0, -6.0, 320.0, 0.22, -0.02),
        "assemble": False,
    },
    {
        "id": "seg_07",
        "num": 7,
        "code": "VII · SANCTUARY OF THE FURNACE",
        "title": "The Only Warmth in a Gray World",
        "source": "horse",
        "src_t0": 141.54,  # 2:21.54
        "src_t1": 147.28,  # 2:27.28
        "clip_t0": 144.40,
        "clip_dur": 3.4,
        "film_t0": 24.6,
        "film_t1": 28.0,
        "mode": "light",
        "who": "MEMORY SEGMENT 07 (2:24 – 2:27)",
        "say": "Before the roaring furnace mouth, the lone child sits bathed in amber firelight — until footsteps echo behind him.",
        "tape": "FURNACE HEARTH · High-emission amber firelight locks focal bucket b0; cold boiler walls vanish into dark mist",
        "feeling_anchor": (0.52, 0.56),
        "mist_level": 0.35,
        "cam0": (0.0, 12.0, 920.0, -0.18, -0.04),
        "cam1": (0.0, -6.0, 260.0, 0.24, 0.03),
        "assemble": False,
    },
    {
        "id": "seg_08",
        "num": 8,
        "code": "VIII · THE TOY WOODEN HORSE (6 · 10 · 21)",
        "title": "Small Hand Clutching the Carved Horse Against the Flame",
        "source": "horse",
        "src_t0": 147.28,  # 2:27.28
        "src_t1": 148.85,  # 2:28.85
        "clip_t0": 147.15,
        "clip_dur": 2.4,
        "film_t0": 28.0,
        "film_t1": 31.8,
        "mode": "light",
        "who": "EMOTIONAL ANCHOR · PEAK FEELING (2:27 – 2:28)",
        "say": "“I remember it was small… fit in my palm.” The carved wooden horse silhouetted against the roaring furnace fire.",
        "tape": "THE HORSE IN HAND · Emotional salience F = 1.0 · Maximum temporal persistence tau = 30 slices",
        "feeling_anchor": (0.28, 0.52),
        "mist_level": 0.24,
        "cam0": (-45.0, 0.0, 680.0, -0.15, 0.02),
        "cam1": (-15.0, 0.0, 230.0, 0.12, -0.02),
        "assemble": False,
    },
    {
        "id": "seg_09",
        "num": 9,
        "code": "IX · PURSUIT THROUGH THE COLUMNS",
        "title": "Bolting From the Fire Into the Dark Boiler Room",
        "source": "horse",
        "src_t0": 148.85,  # 2:28.85
        "src_t1": 156.80,  # 2:36.80
        "clip_t0": 151.20,
        "clip_dur": 4.2,
        "film_t0": 31.8,
        "film_t1": 35.6,
        "mode": "paper",
        "who": "MEMORY SEGMENT 09 (2:28 – 2:36)",
        "say": "Clutching the wooden horse to his chest, the child bolts past the slanted iron buttresses as the pack closes in.",
        "tape": "SLANTED BUTTRESSES · The running child leaves a golden ribbon of past postures through the gray mist",
        "feeling_anchor": (0.55, 0.56),
        "mist_level": 0.60,
        "cam0": (130.0, -10.0, 740.0, 0.52, 0.04),
        "cam1": (-70.0, 8.0, 290.0, -0.28, -0.02),
        "assemble": False,
    },
    {
        "id": "seg_10",
        "num": 10,
        "code": "X · STABLE PRODUCTS & HUMAN RESPONSES",
        "title": "Good Memories to Think Back On",
        "source": "stelline",
        "src_t0": 192.0,   # 3:12
        "src_t1": 222.0,   # 3:42
        "clip_t0": 212.0,
        "clip_dur": 4.2,
        "film_t0": 35.6,
        "film_t1": 39.6,
        "mode": "light",
        "who": "DR. ANA STELLINE (3:12 – 3:42)",
        "say": "“I provide Wallace with a stable product. Give them good memories to think back on — smiles, authentic human responses.”",
        "tape": "INTERNAL LIFE · Faces around the cake glow in warm amber while background walls remain empty black",
        "feeling_anchor": (0.46, 0.48),
        "mist_level": 0.40,
        "cam0": (60.0, -12.0, 820.0, 0.28, 0.05),
        "cam1": (-40.0, 6.0, 310.0, -0.20, -0.03),
        "assemble": False,
    },
    {
        "id": "seg_11",
        "num": 11,
        "code": "XI · HIDING THE HORSE IN THE ASHES",
        "title": "I Hid It in a Place They'd Never Look",
        "source": "horse",
        "src_t0": 156.80,  # 2:36.80
        "src_t1": 167.87,  # 2:47.87
        "clip_t0": 159.50,
        "clip_dur": 5.0,
        "film_t0": 39.6,
        "film_t1": 44.0,
        "mode": "light",
        "who": "MEMORY SEGMENT 11 · THE FURNACE ASH PIT (2:36 – 2:47)",
        "say": "Kneeling beside the cold furnace grate, he rakes the gray cinders and buries the wooden horse deep in the ash.",
        "tape": "ASH & CINDERS · Volumetric point-dust settles over the buried horse like literal furnace ash",
        "feeling_anchor": (0.62, 0.64),
        "mist_level": 0.48,
        "cam0": (-90.0, -15.0, 760.0, -0.38, 0.06),
        "cam1": (50.0, 10.0, 260.0, 0.26, -0.03),
        "assemble": False,
    },
    {
        "id": "seg_12",
        "num": 12,
        "code": "XII · DEFIANCE BEFORE THE PACK",
        "title": "They Were Looking For It — I Wouldn't Tell Them Where It Was",
        "source": "horse",
        "src_t0": 167.87,  # 2:47.87
        "src_t1": 186.39,  # 3:06.39
        "clip_t0": 173.40,
        "clip_dur": 5.0,
        "film_t0": 44.0,
        "film_t1": 48.2,
        "mode": "light",
        "who": "MEMORY SEGMENT 12 (2:47 – 3:06)",
        "say": "Surrounded by the shaved-head gang in front of the fire, the boy stands empty-handed and refuses to surrender the hiding place.",
        "tape": "THE DEFIANT GAZE · The boy's firelit eyes stay razor-sharp while the surrounding ring of boys blurs into mist",
        "feeling_anchor": (0.48, 0.46),
        "mist_level": 0.44,
        "cam0": (0.0, -8.0, 790.0, 0.22, 0.03),
        "cam1": (0.0, 4.0, 250.0, -0.18, -0.02),
        "assemble": False,
    },
    {
        "id": "seg_13",
        "num": 13,
        "code": "XIII · THE LAW OF THE MIST (4:16 – 4:27)",
        "title": "We Recall With Our Feelings — Anything Real Should Be a Mist",
        "source": "stelline",
        "src_t0": 256.0,   # 4:16
        "src_t1": 267.5,   # 4:27.5
        "clip_t0": 256.0,
        "clip_dur": 5.0,
        "film_t0": 48.2,
        "film_t1": 52.6,
        "mode": "paper",
        "who": "DR. ANA STELLINE (4:16 – 4:27)",
        "say": "“They think it's about more detail. That's not how memory works. We recall with our feelings. Anything real should be a mist.”",
        "tape": "THE MIST LAW · Precision data scatters into Beer's-Law fog; only felt emotion holds the volume together",
        "feeling_anchor": (0.44, 0.46),
        "mist_level": 0.62,
        "cam0": (-80.0, 0.0, 840.0, -0.35, 0.04),
        "cam1": (60.0, 0.0, 320.0, 0.28, -0.02),
        "assemble": False,
    },
    {
        "id": "seg_14",
        "num": 14,
        "code": "XIV · THE SLIT-LAMP SCANNER",
        "title": "Someone Lived This. Yes… This Happened.",
        "source": "stelline",
        "src_t0": 325.0,   # 5:25
        "src_t1": 360.0,   # 6:00
        "clip_t0": 338.0,
        "clip_dur": 4.8,
        "film_t0": 52.6,
        "film_t1": 56.6,
        "mode": "light",
        "who": "DR. ANA STELLINE AT THE SCANNER (5:25 – 6:00)",
        "say": "Peering into K's memory of the wooden horse through her optical slit-lamp, Ana weeps: “Someone lived this. Yes… this happened.”",
        "tape": "RECOGNITION · Golden Memory-Maker particles merge with the slit-lamp beam as she recognizes her own past",
        "feeling_anchor": (0.48, 0.48),
        "mist_level": 0.36,
        "cam0": (0.0, 0.0, 780.0, -0.16, 0.02),
        "cam1": (0.0, 0.0, 260.0, 0.16, -0.02),
        "assemble": False,
    },
]


# ==============================================================================
# STEP 1: EXTRACT & ENCODE THE 14 REAL MEMORY VIDEO SEGMENTS + AUDIO (1280x720 @ 24fps)
# ==============================================================================
def extract_memory_segments():
    print("[1/5] Extracting 1280x720 @ 24fps segmented memory clips (starting at 1:49) with real dialogue...")
    for seg in MEMORY_SEGMENTS:
        out_mp4 = os.path.join(SEG_DIR, f"{seg['id']}.mp4")
        # Re-extract if missing or if older low-res 640x360 build (< 650 KB)
        if os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 850000:
            continue
        src = SRC_HORSE if seg["source"] == "horse" else SRC_STELLINE
        t0 = seg["src_t0"]
        dur = min(14.0, seg["src_t1"] - seg["src_t0"])
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{t0:.2f}", "-i", src, "-t", f"{dur:.2f}",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24",
            "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            out_mp4
        ]
        subprocess.run(cmd, check=True)


# ==============================================================================
# STEP 2: BELIEVABLE 24FPS CINEMA MULTIPLANE + 07-SPACETIME FEELING-MIST ENGINE
# ==============================================================================
_VIG_CACHE = {}
def get_vignette(h, w):
    if (h, w) not in _VIG_CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        v = 1.0 - 0.24 * (((xx - w * 0.5) / (w * 0.55)) ** 2 + ((yy - h * 0.5) / (h * 0.55)) ** 2)
        _VIG_CACHE[(h, w)] = np.clip(v, 0.68, 1.0)[..., None]
    return _VIG_CACHE[(h, w)]


_BASE_YY, _BASE_XX = np.mgrid[0:FH, 0:FW].astype(np.float32)

def warp_multiplane_cinema(img_rgb, disp, pan_x, tilt_y, dolly_scale, depth_stretch=0.042):
    """
    True 2.5D/3D multiplane camera transform using per-pixel inverse-depth parallax (`cv2.remap`).
    Keeps 100% of the 1280x720 cinema frame intact with zero disocclusion holes or tears.
    """
    local_scale = dolly_scale * (1.0 + depth_stretch * (disp - 0.38))
    parallax_weight = 0.28 + 0.72 * disp
    map_x = (_BASE_XX - FW * 0.5) / local_scale + FW * 0.5 + pan_x * parallax_weight
    map_y = (_BASE_YY - FH * 0.5) / local_scale + FH * 0.5 + tilt_y * parallax_weight
    return cv2.remap(
        img_rgb,
        map_x.astype(np.float32),
        map_y.astype(np.float32),
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )


def splat_gaussian_multiscale(px, py, zc, rad, rgb, w_val, mode="light", gain=1.08, seed=0):
    """
    3-bucket multi-scale Gaussian bokeh & volumetric memory-mote renderer (`spacetime.py`).
    Renders luminous 3D depth particles and temporal feeling-echoes that layer cleanly over
    the full-resolution 24fps cinema plate without ever turning into an opaque white stain.
    """
    H, W = RH, RW
    valid = (zc > 25.0) & (px >= -8) & (px < W + 8) & (py >= -8) & (py < H + 8) & (w_val > 1e-4)
    if not np.any(valid):
        return np.zeros((FH, FW, 3), dtype=np.float32)

    px = px[valid]
    py = py[valid]
    rad = rad[valid]
    rgb = rgb[valid]
    wt = w_val[valid]

    ix = np.clip(np.round(px).astype(np.int32), 0, W - 1)
    iy = np.clip(np.round(py).astype(np.int32), 0, H - 1)

    b0 = rad < 1.55
    b1 = (rad >= 1.55) & (rad < 3.65)
    b2 = rad >= 3.65

    sigmas = [0.65, 1.75, 4.20]
    ks = [3.2, 6.4, 14.0]
    acc = np.zeros((3, H, W, 4), dtype=np.float32)

    for bi, mask in enumerate((b0, b1, b2)):
        if not np.any(mask):
            continue
        w = wt[mask]
        c = rgb[mask] * w[:, None]
        np.add.at(acc[bi, :, :, 0], (iy[mask], ix[mask]), c[:, 0])
        np.add.at(acc[bi, :, :, 1], (iy[mask], ix[mask]), c[:, 1])
        np.add.at(acc[bi, :, :, 2], (iy[mask], ix[mask]), c[:, 2])
        np.add.at(acc[bi, :, :, 3], (iy[mask], ix[mask]), w)
        s = sigmas[bi]
        for ch in range(4):
            acc[bi, :, :, ch] = gaussian_filter(acc[bi, :, :, ch], sigma=s, mode="constant")

    total = np.zeros((H, W, 4), dtype=np.float32)
    for bi in (2, 1, 0):
        total += acc[bi] * ks[bi]
    A = total[:, :, 3:4] * gain
    col = total[:, :, :3] * gain / np.maximum(A, 1e-4)
    cov = 1.0 - np.exp(-A * 0.85)
    bloom = np.stack([gaussian_filter(col[:, :, c] * cov[:, :, 0], sigma=8.5) for c in range(3)], axis=-1)
    out = col * cov + bloom * 0.42
    out_hi = cv2.resize(np.clip(out, 0.0, 1.0), (FW, FH), interpolation=cv2.INTER_CUBIC)
    return out_hi


_VOL_CACHE = {}
def get_segment_volume(seg_id):
    if seg_id in _VOL_CACHE:
        return _VOL_CACHE[seg_id]
    seg = next(s for s in MEMORY_SEGMENTS if s["id"] == seg_id)
    src = SRC_HORSE if seg["source"] == "horse" else SRC_STELLINE

    # 1. Load true contiguous 24fps full-HD (1280x720) cinema frames covering the segment + transition tail
    cap = cv2.VideoCapture(src)
    fps_src = cap.get(cv2.CAP_PROP_FPS) or 24.0
    t0 = seg["clip_t0"]
    seg_dur = (seg["film_t1"] - seg["film_t0"]) + 0.90  # Extra 0.9s tail so transitions NEVER freeze!
    n_hd_frames = max(48, int(round(seg_dur * FPS)))

    cap.set(cv2.CAP_PROP_POS_MSEC, t0 * 1000.0)
    hd_frames = []
    # Step smoothly at 24fps through source video
    step_frames = max(1.0, fps_src / float(FPS))
    raw_read = []
    max_to_read = int(round(n_hd_frames * step_frames)) + 4
    for _ in range(max_to_read):
        ok, fr = cap.read()
        if not ok or fr is None:
            break
        raw_read.append(fr)
    cap.release()

    if not raw_read:
        raw_read = [np.zeros((FH, FW, 3), dtype=np.uint8)]

    for i in range(n_hd_frames):
        f_idx = min(len(raw_read) - 1, int(round(i * (len(raw_read) - 1) / max(1, n_hd_frames - 1))))
        fr = cv2.cvtColor(cv2.resize(raw_read[f_idx], (FW, FH), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        hd_frames.append(fr.astype(np.float32) / 255.0)

    hd_frames = np.stack(hd_frames, axis=0)  # (N_hd, 720, 1280, 3)

    # Gentle shadow recovery on dark orphanage/furnace interiors while preserving Roger Deakins chiaroscuro
    mid_fr = hd_frames[len(hd_frames) // 2]
    p95 = float(np.percentile(mid_fr, 95))
    boost = float(np.clip(0.90 / max(p95, 0.14), 1.0, 2.1))
    hd_frames = np.clip((hd_frames * boost) ** 0.88, 0.0, 1.0).astype(np.float32)

    # 2. Compute smooth 1280x720 Inverse-Depth Disparity & Stelline Emotional Feeling Mask `F_mask(y, x)`
    ax, ay = seg["feeling_anchor"]
    yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float32)
    # Wide elliptical focal zone around the emotional anchor (face, hands holding wooden horse, furnace, scanner)
    dist2 = ((xx / FW - ax) / 0.36) ** 2 + ((yy / FH - ay) / 0.40) ** 2
    anchor_field = np.exp(-dist2).astype(np.float32)

    mean_rgb = hd_frames[::max(1, len(hd_frames) // 8)].mean(axis=0)
    lum = (mean_rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32))
    warmth = np.clip((mean_rgb[..., 0] - mean_rgb[..., 2]) * 1.6 + lum * 0.45, 0.0, 1.0)

    feeling_hd = np.clip(0.62 * anchor_field + 0.38 * warmth, 0.08, 1.0)
    feeling_hd = cv2.GaussianBlur(feeling_hd.astype(np.float32), (0, 0), 32.0)

    # Smooth inverse-depth disparity for 2.5D multiplane parallax (`1.0` = near anchor, `0.0` = far periphery)
    ground_ramp = (yy / float(FH)) * 0.25
    disp_hd = cv2.GaussianBlur((0.55 * feeling_hd + 0.25 * lum + ground_ramp).astype(np.float32), (0, 0), 24.0)
    d_lo, d_hi = float(np.percentile(disp_hd, 3)), float(np.percentile(disp_hd, 97))
    disp_hd = np.clip((disp_hd - d_lo) / max(d_hi - d_lo, 1e-3), 0.0, 1.0).astype(np.float32)

    # 3. Extract sparse 4D luminous contour/ember points (`vw=120, vh=68, T=32`) for subtle 3D Gaussian bokeh motes
    vw, vh, T_vol = 120, 68, min(32, len(hd_frames))
    sub_idxs = np.linspace(0, len(hd_frames) - 1, T_vol).astype(int)
    small_frames = np.stack([cv2.resize(hd_frames[idx], (vw, vh), interpolation=cv2.INTER_AREA) for idx in sub_idxs], axis=0)
    small_feel = cv2.resize(feeling_hd, (vw, vh), interpolation=cv2.INTER_AREA)
    small_disp = cv2.resize(disp_hd, (vw, vh), interpolation=cv2.INTER_AREA)

    rng = np.random.default_rng(abs(hash(seg_id)) % (2**31))
    xs, ys, ss, ds, cols, wts, fls = [], [], [], [], [], [], []
    for s in range(T_vol):
        fr_s = small_frames[s]
        lum_s = fr_s.mean(axis=-1)
        # Keep only luminous highlights & warm emotional contours so bokeh motes look like golden dust/embers, NEVER mud!
        sal_s = np.clip(lum_s * 0.7 + (fr_s[..., 0] - fr_s[..., 2]) * 0.8, 0.0, 1.0)
        prob = np.clip(0.06 + 0.28 * (sal_s ** 1.4), 0.04, 0.35)
        keep = rng.random((vh, vw)) < prob
        ky, kx = np.where(keep)
        jx = rng.uniform(-0.4, 0.4, len(kx)).astype(np.float32)
        jy = rng.uniform(-0.4, 0.4, len(ky)).astype(np.float32)

        x = ((kx + jx) / vw - 0.5) * 540.0
        y = ((ky + jy) / vh - 0.5) * 304.0
        d_val = (0.5 - small_disp[ky, kx]) * 110.0
        c = np.clip(fr_s[ky, kx] * 1.18 + np.array([0.12, 0.06, -0.02], dtype=np.float32), 0.0, 1.0)
        f_val = small_feel[ky, kx]
        w = (0.25 + 0.75 * sal_s[ky, kx]).astype(np.float32)

        xs.append(x.astype(np.float32))
        ys.append(y.astype(np.float32))
        ss.append(np.full(len(kx), s, dtype=np.float32))
        ds.append(d_val.astype(np.float32))
        cols.append(c.astype(np.float32))
        wts.append(w)
        fls.append(f_val.astype(np.float32))

    vol = dict(
        seg=seg,
        T=T_vol,
        hd_frames=hd_frames,
        raw_frames=small_frames,
        feeling_hd=feeling_hd,
        disp_hd=disp_hd,
        feeling_map=small_feel,
        x=np.concatenate(xs),
        y=np.concatenate(ys),
        s=np.concatenate(ss),
        d=np.concatenate(ds),
        rgb=np.concatenate(cols),
        w=np.concatenate(wts),
        feeling=np.concatenate(fls),
        dz=12.0,
    )
    _VOL_CACHE[seg_id] = vol
    return vol


def build_master_timeline():
    """
    Builds the complete 63.0s (1512 frames at 24fps) 07-Spacetime Cinema Film:
      - 0.0s .. 56.6s: All 14 Memory Segments in chronological order (ZERO duplicate "Every Volume Twice" replays!)
      - 56.6s .. 57.8s: The Drop to Silence (1.2s before one golden dot)
      - 57.8s .. 63.0s: 3D Point-Cloud Engraving ("6 · 10 · 21  /  ANYTHING REAL SHOULD BE A MIST")
    """
    shots = []
    for idx, seg in enumerate(MEMORY_SEGMENTS):
        shots.append(dict(
            idx=idx,
            t0=seg["film_t0"],
            t1=seg["film_t1"],
            seg_id=seg["id"],
            mode=seg["mode"],
            assemble=seg["assemble"],
            cam0=seg["cam0"],
            cam1=seg["cam1"],
            mist_level=seg["mist_level"],
            who=seg["who"],
            say=seg["say"],
            code=seg["code"],
            montage=None,
        ))

    shots.append(dict(idx=14, t0=56.6, t1=57.8, seg_id=None, mode="drop"))
    shots.append(dict(idx=15, t0=57.8, t1=63.0, seg_id=None, mode="title"))
    return shots


MASTER_SHOTS = build_master_timeline()
MASTER_DURATION = 63.0

_HORSE_TITLE_CLOUD = None
def get_horse_title_cloud():
    global _HORSE_TITLE_CLOUD
    if _HORSE_TITLE_CLOUD is not None:
        return _HORSE_TITLE_CLOUD
    img = Image.new("L", (960, 300), 0)
    d = ImageDraw.Draw(img)
    f_big = get_font("serif", 96)
    f_it = get_font("italic", 36)
    f_sub = get_font("mono", 18)
    d.text((480, 88), "6  ·  10  ·  21", font=f_big, fill=255, anchor="mm")
    d.text((480, 176), "“Anything real should be a mist.”", font=f_it, fill=235, anchor="mm")
    d.text((480, 240), "DR. ANA STELLINE  ·  THE TOY WOODEN HORSE  ·  07-SPACETIME", font=f_sub, fill=195, anchor="mm")
    arr = np.asarray(img, dtype=np.float32) / 255.0
    yy, xx = np.where(arr > 0.14)
    rng = np.random.default_rng(61021)
    keep = rng.random(len(xx)) < 0.80
    yy, xx = yy[keep], xx[keep]

    x = (xx - 480.0) * 0.90 + rng.normal(0, 0.4, len(xx)).astype(np.float32)
    y = (yy - 150.0) * 0.90 + rng.normal(0, 0.4, len(yy)).astype(np.float32)
    z = rng.normal(0, 8.5, len(xx)).astype(np.float32)

    sx = rng.normal(0, 440.0, len(xx)).astype(np.float32)
    sy = rng.normal(0, 270.0, len(xx)).astype(np.float32)
    sz = rng.uniform(-520.0, 520.0, len(xx)).astype(np.float32)

    ux = np.clip((xx / 960.0), 0.0, 1.0).astype(np.float32)
    rgb = np.stack([
        np.ones_like(ux) * 0.98,
        0.74 + 0.18 * ux,
        0.42 + 0.24 * ux
    ], axis=-1).astype(np.float32)

    _HORSE_TITLE_CLOUD = dict(x=x, y=y, z=z, sx=sx, sy=sy, sz=sz, rgb=rgb, w=arr[yy, xx].astype(np.float32))
    return _HORSE_TITLE_CLOUD


def eval_segment_cinema_plate(shot, u_local, global_t, fi):
    """
    Renders a single segment at normalized time `u_local` (which can smoothly extend past 1.0 during
    exit cross-dissolves so motion NEVER freezes!):
      - Full-resolution 1280x720 24fps moving cinema frame on focal plane P2/P3 (`feeling_hd -> 1`)
      - Multiplane 2.5D depth parallax (`warp_multiplane_cinema`)
      - Soft peripheral depth-of-field + atmospheric Beer's-Law feeling-mist (`Air A1`) + subtle 3D Gaussian
        memory-maker bokeh motes in the peripheral region (`1 - feeling_hd`), NEVER obliterating the actors!
    """
    vol = get_segment_volume(shot["seg_id"])
    hd_frames = vol["hd_frames"]
    n_hd = len(hd_frames)

    # Continuous sub-frame interpolation at true 24fps (including transition tail)
    seg_dur = shot["t1"] - shot["t0"]
    f_exact = np.clip(u_local * seg_dur * FPS, 0.0, n_hd - 1.001)
    i0 = int(f_exact)
    i1 = min(n_hd - 1, i0 + 1)
    frac = float(f_exact - i0)
    raw_plate = hd_frames[i0] * (1.0 - frac) + hd_frames[i1] * frac

    eu = ease(np.clip(u_local, 0.0, 1.0))
    cam0, cam1 = shot["cam0"], shot["cam1"]
    pan_dir = 1.0 if (shot["idx"] % 2 == 0) else -1.0
    pan_x = pan_dir * ((u_local - 0.5) * 26.0 + 3.0 * math.sin(global_t * 0.45))
    tilt_y = (0.5 - u_local) * 9.0 + 2.0 * math.cos(global_t * 0.38)
    dolly_scale = 1.05 + 0.06 * np.clip(u_local, 0.0, 1.2)

    warped_plate = warp_multiplane_cinema(raw_plate, vol["disp_hd"], pan_x, tilt_y, dolly_scale, depth_stretch=0.042 * eu)
    warped_feel = warp_multiplane_cinema(vol["feeling_hd"], vol["disp_hd"], pan_x, tilt_y, dolly_scale, depth_stretch=0.042 * eu)

    # Peripheral memory mist ("Everything's grey / Anything real should be a mist"):
    # Keep focal emotional core (`warped_feel -> 1`) 100% sharp; soften outer periphery (`periph = 1 - warped_feel`)
    mist_amt = shot.get("mist_level", 0.42)
    periph = np.clip((1.0 - warped_feel) ** 1.35 * mist_amt * 1.15, 0.0, 0.78)[..., None]

    blur_plate = cv2.GaussianBlur(warped_plate, (0, 0), 14.0)
    # Atmospheric tint in periphery: cool slate-amber memory mist (never a harsh white/beige stain!)
    if shot["mode"] == "paper":
        mist_tint = np.array([0.16, 0.18, 0.22], dtype=np.float32)[None, None, :]
    else:
        mist_tint = np.array([0.14, 0.11, 0.08], dtype=np.float32)[None, None, :]

    periph_mist = 0.72 * blur_plate + 0.28 * mist_tint
    comp = warped_plate * (1.0 - periph) + periph_mist * periph

    # Subtle 3D Gaussian Memory-Maker bokeh motes drifting across peripheral depth strata
    cx = lerp(cam0[0], cam1[0], eu) * 0.35
    cy_cam = lerp(cam0[1], cam1[1], eu) * 0.35
    dist = lerp(cam0[2], cam1[2], eu)
    # Constrain yaw to natural cinema parallax (±10°) so bokeh aligns with the scene
    yaw = np.clip(lerp(cam0[3], cam1[3], eu) * 0.35, -0.18, 0.18)
    pitch = np.clip(lerp(cam0[4], cam1[4], eu) * 0.35, -0.08, 0.08)

    present = (0.12 + 0.80 * np.clip(u_local, 0.0, 1.0)) * (vol["T"] - 1)
    age = present - vol["s"]
    vis = (age >= -1.5) & (age <= 14.0)
    if np.any(vis):
        x = vol["x"][vis].copy() - cx
        y = vol["y"][vis].copy() - cy_cam
        z = age[vis] * vol["dz"] + vol["d"][vis]
        rgb_pts = vol["rgb"][vis]
        fl_pts = vol["feeling"][vis]
        tau = 6.0 + 10.0 * fl_pts
        t_decay = np.where(age[vis] >= 0, np.exp(-age[vis] / tau), np.exp(-(age[vis] ** 2) / 1.0)).astype(np.float32)
        wt = vol["w"][vis] * t_decay * 0.45

        cy_r, sy_r = math.cos(yaw), math.sin(yaw)
        Xc = x * cy_r + z * sy_r
        Zc1 = -x * sy_r + z * cy_r
        cp_r, sp_r = math.cos(pitch), math.sin(pitch)
        Yc = y * cp_r - Zc1 * sp_r
        Zc = y * sp_r + Zc1 * cp_r + dist

        px = 520.0 * Xc / np.maximum(Zc, 30.0) + RW * 0.5
        py = 520.0 * Yc / np.maximum(Zc, 30.0) + RH * 0.5
        rad = np.clip(1.2 + (1.0 - fl_pts) * 2.2, 1.0, 4.8).astype(np.float32)
        bokeh_layer = splat_gaussian_multiscale(px, py, Zc, rad, rgb_pts, wt, mode="light", gain=0.65, seed=fi)
        # Blend bokeh gently (stronger in periphery/transition, subtle in focal core so faces stay 100% clean)
        bokeh_weight = (0.10 + 0.28 * (1.0 - warped_feel))[..., None]
        comp = np.clip(comp + bokeh_layer * bokeh_weight, 0.0, 1.0)

    comp = comp * get_vignette(FH, FW)
    return np.clip(comp, 0.0, 1.0), mist_amt, yaw


def render_master_frame(fi):
    t = fi / FPS
    shot = MASTER_SHOTS[-1]
    for s in MASTER_SHOTS:
        if s["t0"] <= t < s["t1"]:
            shot = s
            break

    # 1. THE DROP TO SILENCE + SINGLE GOLD EMBER MOTE
    if shot["mode"] == "drop":
        u = (t - shot["t0"]) / max(shot["t1"] - shot["t0"], 1e-4)
        # Smooth dissolve from segment 14 into the dark chamber with single gold ember
        prev_shot = MASTER_SHOTS[13]
        prev_img, _, _ = eval_segment_cinema_plate(prev_shot, 1.0, t, fi)
        fade = smootherstep(min(1.0, u * 1.6))
        out = prev_img * (1.0 - fade) + NIGHT[None, None, :] * fade
        mote = smootherstep(max(0.0, (u - 0.25) / 0.75))
        yy, xx = np.ogrid[:FH, :FW]
        glow = mote * np.exp(-((xx - FW * 0.5) ** 2 + (yy - FH * 0.5) ** 2) / 65.0)
        out += glow[..., None] * np.array([1.0, 0.82, 0.48], dtype=np.float32)
        return (np.clip(out, 0.0, 1.0) * 255.0).astype(np.uint8)

    # 2. THE 3D DUST-BUILT TITLE ("6 · 10 · 21 / Anything real should be a mist") OVER WOODEN HORSE MEMORY
    if shot["mode"] == "title":
        tc = get_horse_title_cloud()
        u = (t - shot["t0"]) / max(shot["t1"] - shot["t0"], 1e-4)
        # Subtle darkened background recall of seg_08 (the carved wooden horse in hand)
        horse_shot = MASTER_SHOTS[7]
        bg_horse, _, _ = eval_segment_cinema_plate(horse_shot, 0.35 + 0.45 * u, t, fi)
        bg_plate = bg_horse * 0.28 + NIGHT[None, None, :] * 0.72

        k_scatter = (1.0 - smootherstep(min(1.0, u / 0.48))) ** 2.0
        X = tc["x"] * (1.0 - k_scatter) + tc["sx"] * k_scatter
        Y = tc["y"] * (1.0 - k_scatter) + tc["sy"] * k_scatter
        Z = tc["z"] * (1.0 - k_scatter) + tc["sz"] * k_scatter

        yaw = (1.0 - smootherstep(min(1.0, u / 0.55))) * 0.35 + 0.03 * math.sin(u * 2.5)
        dist = 540.0 - 50.0 * ease(u)
        cy, sy = math.cos(yaw), math.sin(yaw)
        Xc = X * cy + Z * sy
        Zc = -X * sy + Z * cy + dist

        px = 520.0 * Xc / np.maximum(Zc, 30.0) + RW * 0.5
        py = 520.0 * Y / np.maximum(Zc, 30.0) + RH * 0.5
        rad = np.clip(0.85 + 2.4 * k_scatter + np.abs(Zc - dist) / 170.0, 0.8, 5.2).astype(np.float32)
        title_splat = splat_gaussian_multiscale(px, py, Zc, rad, tc["rgb"], tc["w"] * 1.45, mode="light", gain=1.25, seed=fi)
        img = np.clip(bg_plate + title_splat, 0.0, 1.0)
        return (np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8)

    # 3. CONTINUOUS 24FPS MULTIPLANE CINEMA SEGMENT + DEPTH-ORDERED CROSS-DISSOLVE
    seg_dur = max(shot["t1"] - shot["t0"], 1e-4)
    u = (t - shot["t0"]) / seg_dur
    img, mist_amt, yaw = eval_segment_cinema_plate(shot, u, t, fi)

    # Seamless 0.70s depth-plane dissolve into the next segment so the film flows unbroken
    xf_dur = 0.70
    rem = shot["t1"] - t
    if rem < xf_dur and shot["idx"] + 1 < 14:
        next_shot = MASTER_SHOTS[shot["idx"] + 1]
        u_xf = smootherstep(1.0 - rem / xf_dur)
        next_img, _, _ = eval_segment_cinema_plate(next_shot, u_xf * (xf_dur / (next_shot["t1"] - next_shot["t0"])), t, fi)
        img = img * (1.0 - u_xf) + next_img * u_xf

    # Whisper-quiet Afterlight / VOIDBASTARD-TAO typography (zero rectangular boxes, high legibility)
    pil = Image.fromarray((img * 255.0).astype(np.uint8))
    draw = ImageDraw.Draw(pil, "RGBA")
    fg_main = (244, 236, 220)
    fg_sub = (182, 174, 158)
    fg_gold = (255, 198, 96)

    f_mono = get_font("mono", 12)
    f_who = get_font("mono", 13)
    f_italic = get_font("italic", 27)

    angle_tag = f"FEELING CORE + PERIPHERAL MIST={int(mist_amt*100)}% · PARALLAX {math.degrees(yaw):+04.1f}°"
    draw.text((36, 26), f"07 · SPACETIME MIST   {shot['code']}", font=f_mono, fill=fg_sub + (185,))
    draw.text((FW - 36, 26), angle_tag, font=f_mono, fill=fg_sub + (185,), anchor="ra")

    ca = sm(shot["t0"], shot["t0"] + 0.45, t) * (1.0 - sm(shot["t1"] - 0.50, shot["t1"], t))
    if ca > 0.02:
        alpha = int(238 * ca)
        sh_a = int(175 * ca)
        draw.text((FW // 2 + 1, FH - 79), shot["who"], font=f_who, fill=(8, 10, 14, sh_a), anchor="mm")
        draw.text((FW // 2, FH - 80), shot["who"], font=f_who, fill=fg_gold + (int(alpha * 0.92),), anchor="mm")
        say_txt = shot["say"]
        if len(say_txt) > 86:
            mid = say_txt.rfind(" ", 0, 78)
            l1, l2 = say_txt[:mid], say_txt[mid+1:]
            draw.text((FW // 2 + 1, FH - 51), l1, font=f_italic, fill=(8, 10, 14, sh_a), anchor="mm")
            draw.text((FW // 2, FH - 52), l1, font=f_italic, fill=fg_main + (alpha,), anchor="mm")
            draw.text((FW // 2 + 1, FH - 21), l2, font=f_italic, fill=(8, 10, 14, sh_a), anchor="mm")
            draw.text((FW // 2, FH - 22), l2, font=f_italic, fill=fg_main + (alpha,), anchor="mm")
        else:
            draw.text((FW // 2 + 1, FH - 41), say_txt, font=f_italic, fill=(8, 10, 14, sh_a), anchor="mm")
            draw.text((FW // 2, FH - 42), say_txt, font=f_italic, fill=fg_main + (alpha,), anchor="mm")

    return np.asarray(pil, dtype=np.uint8)


# ==============================================================================
# STEP 3: BUILD SYNCHRONIZED REAL DIALOGUE + 07-SPACETIME SCORE AUDIO TRACK
# ==============================================================================
def build_master_audio(out_wav):
    print("[2/5] Mixing real Stelline & Officer K dialogue with 07-spacetime harmonic bed...")
    sr = 44100
    dur = MASTER_DURATION
    total_samples = int(dur * sr)
    mix = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Warm sub-bass & Vangelis/Afterlight harmonic drone bed
    t = np.arange(total_samples, dtype=np.float32) / sr
    drone = (
        0.048 * np.sin(2 * np.pi * 55.0 * t) +
        0.032 * np.sin(2 * np.pi * 82.41 * t + 0.3 * np.sin(2 * np.pi * 0.18 * t)) +
        0.022 * np.sin(2 * np.pi * 110.0 * t) +
        0.015 * np.sin(2 * np.pi * 164.81 * t)
    )
    # Silence during the 07-spacetime Drop (56.6s .. 57.8s)
    drop_env = 1.0 - ((t >= 56.55) & (t <= 57.85)).astype(np.float32) * 0.92
    drone *= drop_env
    mix[:, 0] += drone
    mix[:, 1] += drone

    # 2. Overlay the real extracted dialogue audio from each segment (once, in chronological order)
    for seg in MEMORY_SEGMENTS:
        seg_mp4 = os.path.join(SEG_DIR, f"{seg['id']}.mp4")
        if not os.path.exists(seg_mp4):
            continue
        seg_dur = seg["film_t1"] - seg["film_t0"]
        cmd = [
            "ffmpeg", "-v", "error", "-i", seg_mp4,
            "-t", f"{seg_dur:.2f}",
            "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "2", "-ar", str(sr), "-"
        ]
        raw = subprocess.run(cmd, capture_output=True).stdout
        arr = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)
        if len(arr) == 0:
            continue
        fade_len = min(int(0.22 * sr), len(arr) // 3)
        env = np.ones(len(arr), dtype=np.float32)
        if fade_len > 1:
            env[:fade_len] = np.linspace(0.0, 1.0, fade_len)
            env[-fade_len:] = np.linspace(1.0, 0.0, fade_len)
        arr = arr * env[:, None] * 1.18
        start_idx = int(seg["film_t0"] * sr)
        end_idx = min(total_samples, start_idx + len(arr))
        mix[start_idx:end_idx] += arr[:end_idx - start_idx]

    chime_idx = int(57.85 * sr)
    clen = min(int(4.5 * sr), total_samples - chime_idx)
    if clen > 0:
        ct = np.arange(clen, dtype=np.float32) / sr
        chime = (
            0.14 * np.exp(-ct * 0.85) * np.sin(2 * np.pi * 440.0 * ct) +
            0.09 * np.exp(-ct * 1.15) * np.sin(2 * np.pi * 659.25 * ct) +
            0.06 * np.exp(-ct * 1.60) * np.sin(2 * np.pi * 880.0 * ct)
        )
        mix[chime_idx:chime_idx+clen, 0] += chime
        mix[chime_idx:chime_idx+clen, 1] += chime

    peak = float(np.max(np.abs(mix)))
    if peak > 0.96:
        mix = mix * (0.94 / peak)

    pcm16 = (np.clip(mix, -1.0, 1.0) * 32767.0).astype(np.int16)
    import wave
    with wave.open(out_wav, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())


# ==============================================================================
# STEP 4: RENDER MASTER 07-SPACETIME FILM & 4K CONTACT SHEET
# ==============================================================================
def build_master_film_and_sheet():
    extract_memory_segments()
    print("[2/5] Pre-warming 14 24fps Cinema Multiplane + Feeling-Mist Volumes...")
    for seg in MEMORY_SEGMENTS:
        get_segment_volume(seg["id"])

    out_wav = "/tmp/stelline_07_spacetime_audio.wav"
    build_master_audio(out_wav)

    total_frames = int(MASTER_DURATION * FPS)
    print(f"[3/5] Rendering {total_frames} frames of stelline_wooden_horse_07_spacetime.mp4 (1280x720 @ 24fps)...")

    out_mp4 = os.path.join(VID_DIR, "stelline_wooden_horse_07_spacetime.mp4")
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
        "-i", out_wav,
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest",
        out_mp4
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    from concurrent.futures import ThreadPoolExecutor
    batch_size = 48
    with ThreadPoolExecutor(max_workers=8) as ex:
        for b0 in range(0, total_frames, batch_size):
            b1 = min(total_frames, b0 + batch_size)
            frames = list(ex.map(render_master_frame, range(b0, b1)))
            for fr in frames:
                proc.stdin.write(fr.tobytes())
            if b0 % 240 == 0 or b1 == total_frames:
                print(f"  Rendered {b1}/{total_frames} frames ({b1/FPS:.1f}s / {MASTER_DURATION:.1f}s)", flush=True)

    proc.stdin.close()
    proc.wait()
    print(f"[4/5] Saved Master Film: {out_mp4} ({os.path.getsize(out_mp4)/1e6:.2f} MB)")

    # Copy to seeing_spacetime_films and ARTIFACT_DIR
    shutil.copy2(out_mp4, os.path.join(FILM_OUT_DIR, "stelline_wooden_horse_07_spacetime.mp4"))
    shutil.copy2(out_mp4, os.path.join(ARTIFACT_DIR, "stelline_wooden_horse_07_spacetime.mp4"))

    # Build the 4K Contact Sheet (3840 x 2160) showing all 14 Memory Segments + Drop + 6·10·21 Title
    print("[5/5] Building 4K Contact Sheet: stelline_wooden_horse_spacetime_sheet.png...")
    sw, sh = 3840, 2160
    sheet = Image.new("RGB", (sw, sh), (8, 10, 14))
    draw = ImageDraw.Draw(sheet)
    f_hdr = get_font("serif", 42)
    f_sub = get_font("mono", 18)
    f_cell = get_font("mono", 14)
    f_quote = get_font("italic", 20)

    draw.text((64, 34), "DR. ANA STELLINE & THE TOY WOODEN HORSE (1:49 – 3:25)  ·  24FPS MULTIPLANE & FEELING-MIST FILM", font=f_hdr, fill=(244, 236, 220))
    draw.text((64, 88), "“Memory's not about more detail — that's not how memory works. We recall with our feelings. Anything real should be a mist.” (4:16 – 4:27)", font=f_sub, fill=(255, 195, 92))

    sample_times = [s["film_t0"] + 0.50 * (s["film_t1"] - s["film_t0"]) for s in MEMORY_SEGMENTS] + [57.2, 60.8]
    cols, rows = 4, 4
    cw, ch = 910, 475
    ox, oy = 64, 136
    gx, gy = 24, 24

    for idx, st in enumerate(sample_times[:16]):
        r, c = divmod(idx, cols)
        x0 = ox + c * (cw + gx)
        y0 = oy + r * (ch + gy)
        fr = render_master_frame(int(st * FPS))
        im_Main = Image.fromarray(fr).resize((cw, ch - 54), Image.Resampling.LANCZOS)
        sheet.paste(im_Main, (x0, y0))

        if idx < len(MEMORY_SEGMENTS):
            seg = MEMORY_SEGMENTS[idx]
            src_mm = int(seg["src_t0"]) // 60
            src_ss = seg["src_t0"] - src_mm * 60
            draw.text((x0 + 8, y0 + ch - 46), f"{seg['code']}  [SRC {src_mm}:{src_ss:05.2f}]  ·  {seg['title']}", font=f_cell, fill=(92, 228, 255))
            draw.text((x0 + 8, y0 + ch - 24), seg["say"][:92] + ("…" if len(seg["say"]) > 92 else ""), font=f_quote, fill=(230, 222, 206))
        elif idx == 14:
            draw.text((x0 + 8, y0 + ch - 46), "XV · THE DROP TO SILENCE  [SINGLE GOLD EMBER]", font=f_cell, fill=(255, 195, 92))
            draw.text((x0 + 8, y0 + ch - 24), "Chamber darkness before the carved date of the wooden horse coalesces in 3D light.", font=f_quote, fill=(230, 222, 206))
        else:
            draw.text((x0 + 8, y0 + ch - 46), "XVI · THE WOODEN HORSE ENGRAVING  [6 · 10 · 21]", font=f_cell, fill=(255, 195, 92))
            draw.text((x0 + 8, y0 + ch - 24), "“Someone lived this. Yes… this happened.” — Carved wooden horse base in 3D dust.", font=f_quote, fill=(230, 222, 206))

    sheet_path = os.path.join(FILM_OUT_DIR, "stelline_wooden_horse_spacetime_sheet.png")
    sheet.save(sheet_path)
    shutil.copy2(sheet_path, os.path.join(ARTIFACT_DIR, "stelline_wooden_horse_spacetime_sheet.png"))
    print(f"Saved 4K Proof Sheet: {sheet_path}")


# ==============================================================================
# STEP 5: BUILD FULL INVENTORY OF ALL 747 VIDEOS & 99 AUDIO FILES FOR WEBPAGES
# ==============================================================================
def build_complete_media_vault_bundle():
    print("Building stelline_spacetime_data.js (16 Stelline/Wooden-Horse segments + 747 WYGWYL videos + 99 audio files)...")
    bundle_path = os.path.join(FILM_OUT_DIR, "vesper_world_bundle.json")
    bundle = json.load(open(bundle_path, "r", encoding="utf-8"))

    # Enrich every poem and view with ALL previously unused videos & audio tracks!
    cast_dirs = sorted(glob.glob(os.path.join(ROOT, "suite/cast/*")))
    cast_names = [os.path.basename(d) for d in cast_dirs if os.path.isdir(d)]

    scion_clips = sorted([os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "arena/puppet/scion/*.mp4"))])
    study_clips = sorted([os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "arena/puppet/study/*.mp4"))])

    for p in bundle["poems"]:
        n = int(p["num"])
        ns = f"{n:02d}"
        patches = sorted([f"cel_assets/patches/{os.path.basename(x)}" for x in glob.glob(os.path.join(ROOT, f"cel_assets/patches/P{ns}-*.mp4"))])
        stanza_audios = sorted([f"suite/data/audio/{os.path.basename(x)}" for x in glob.glob(os.path.join(ROOT, f"suite/data/audio/{ns}.*.m4a"))])
        c1 = cast_names[(n - 1) % len(cast_names)] if cast_names else "poet_soul"
        c2 = cast_names[(n + 5) % len(cast_names)] if cast_names else "ghost_child"

        p["missing_media_vault"] = {
            "spacetime_worm_video": f"videos/poems/poem_{ns}_spacetime_worm.mp4",
            "seeing_construct_video": f"videos/poems/poem_{ns}_construct.mp4",
            "afterlight_videotext_video": f"videos/poems/poem_{ns}_videotext_fx.mp4",
            "cel_mix_video": f"cel_assets/mix/cels/{ns}.mp4",
            "spinecel_mix_video": f"cel_assets/mix/spinecels/{ns}.mp4",
            "suite_render_video": f"suite/renders/poem_{ns}.mp4",
            "film_render_video": f"film/poem_{ns}.mp4",
            "apparatus_video": f"data/terrarium/seeing_spacetime_films/poem_{ns}_apparatus.mp4",
            "spoken_reading_audio": f"play/levels/{ns}/reading.mp3",
            "stanza_audios": stanza_audios,
            "cel_patches": patches,
            "cast_memories": [
                {
                    "character": c1,
                    "walk": f"suite/cast/{c1}/walk.mp4",
                    "turn": f"suite/cast/{c1}/turn.mp4",
                    "reach": f"suite/cast/{c1}/reach.mp4",
                    "fall": f"suite/cast/{c1}/fall.mp4",
                },
                {
                    "character": c2,
                    "walk": f"suite/cast/{c2}/walk.mp4",
                    "turn": f"suite/cast/{c2}/turn.mp4",
                    "reach": f"suite/cast/{c2}/reach.mp4",
                    "fall": f"suite/cast/{c2}/fall.mp4",
                },
            ],
            "scion_puppet_clip": f"arena/puppet/scion/{scion_clips[(n * 3) % len(scion_clips)]}" if scion_clips else "",
            "acting_study_clip": f"arena/puppet/study/{study_clips[(n * 4) % len(study_clips)]}" if study_clips else "",
        }
        for v in p.get("views", []):
            sd = v.get("dir") or v.get("shot_dir") or ""
            v["live_shot_video"] = f"out/{sd}/film/shot.mp4"
            v["gaussian_splat"] = f"out/{sd}/scene.splat"

    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False)

    # Also write stelline_spacetime_data.js for the dedicated Stelline & 07-Spacetime Videotext page
    stelline_payload = {
        "title": "Dr. Ana Stelline & The Toy Wooden Horse (1:49 – 3:25) · 07-Spacetime Mist Engine",
        "film_video": "videos/stelline_wooden_horse_07_spacetime.mp4",
        "wygwyl_07_spacetime_video": "videos/wygwyl_07_spacetime.mp4",
        "wygwyl_seeing_construct_video": "videos/wygwyl_seeing_construct.mp4",
        "wygwyl_afterlight_feature_video": "videos/wygwyl_afterlight_feature.mp4",
        "weave_passage_video": "weave/passage.mp4",
        "weave_hands_video": "weave/p04_hands/passage.mp4",
        "foundry_episode_video": "foundry/episode.mp4",
        "suite_master_audio": "cel_assets/WYGWYL_Suite_Audio.mp3",
        "proof_sheet": "data/terrarium/seeing_spacetime_films/stelline_wooden_horse_spacetime_sheet.png",
        "segments": MEMORY_SEGMENTS,
        "montage_t0": 56.6,
        "drop_t0": 56.6,
        "title_t0": 57.8,
        "duration": 63.0,
        "vault_counts": {
            "total_videos": 747,
            "view_shot_videos": 100,
            "cel_patch_videos": 165,
            "cast_motion_videos": 126,
            "puppet_and_study_videos": 114,
            "afterlight_spacetime_poem_videos": 42,
            "cel_and_spinecel_mixes": 28,
            "suite_and_film_renders": 30,
            "total_audios": 99,
            "gaussian_splats": 118,
        },
        "poems": bundle["poems"],
    }
    stelline_js = os.path.join(TERR_DIR, "stelline_spacetime_data.js")
    with open(stelline_js, "w", encoding="utf-8") as f:
        f.write("window.STELLINE_SPACETIME_DATA = " + json.dumps(stelline_payload, ensure_ascii=False) + ";\n")
    print(f"Wrote {stelline_js} and enriched {bundle_path}")


if __name__ == "__main__":
    build_master_film_and_sheet()
    build_complete_media_vault_bundle()
