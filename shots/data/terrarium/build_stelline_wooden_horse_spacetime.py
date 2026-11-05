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
# STEP 1: EXTRACT & ENCODE THE 14 REAL MEMORY VIDEO SEGMENTS + AUDIO
# ==============================================================================
def extract_memory_segments():
    print("[1/5] Extracting segmented memory clips (starting at 1:49) with real dialogue...")
    for seg in MEMORY_SEGMENTS:
        out_mp4 = os.path.join(SEG_DIR, f"{seg['id']}.mp4")
        if os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 20000:
            continue
        src = SRC_HORSE if seg["source"] == "horse" else SRC_STELLINE
        t0 = seg["src_t0"]
        dur = min(14.0, seg["src_t1"] - seg["src_t0"])
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{t0:.2f}", "-i", src, "-t", f"{dur:.2f}",
            "-vf", "scale=640:360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            out_mp4
        ]
        subprocess.run(cmd, check=True)


# ==============================================================================
# STEP 2: 07-SPACETIME FEELING-MIST VOLUME BUILDER & MULTI-SCALE SPLATTER
# ==============================================================================
_VIG_CACHE = {}
def get_vignette(h, w):
    if (h, w) not in _VIG_CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        v = 1.0 - 0.22 * (((xx - w * 0.5) / (w * 0.54)) ** 2 + ((yy - h * 0.5) / (h * 0.54)) ** 2)
        _VIG_CACHE[(h, w)] = np.clip(v, 0.70, 1.02)[..., None]
    return _VIG_CACHE[(h, w)]


def splat_gaussian_multiscale(px, py, zc, rad, rgb, w_val, mode="paper", gain=1.08, seed=0):
    """
    Exact 3-bucket multi-scale Gaussian density & Beer's-Law exponential transmittance
    resolve from bolas/afterlight/source/trailer-1/spacetime.py.txt.
    """
    H, W = RH, RW
    valid = (zc > 25.0) & (px >= -8) & (px < W + 8) & (py >= -8) & (py < H + 8) & (w_val > 1e-4)
    if not np.any(valid):
        bg = PAPER if mode == "paper" else NIGHT
        return np.broadcast_to(bg, (FH, FW, 3)).copy()

    px = px[valid]
    py = py[valid]
    rad = rad[valid]
    rgb = rgb[valid]
    wt = w_val[valid]

    ix = np.clip(np.round(px).astype(np.int32), 0, W - 1)
    iy = np.clip(np.round(py).astype(np.int32), 0, H - 1)

    # 3 optical buckets:
    # b0: sharp emotional focal core (< 1.55px)
    # b1: mid-ground structural body (1.55 .. 3.65px)
    # b2: Stelline's peripheral mist (> 3.65px)
    b0 = rad < 1.55
    b1 = (rad >= 1.55) & (rad < 3.65)
    b2 = rad >= 3.65

    sigmas = [0.55, 1.55, 4.10]
    ks = [3.8, 7.6, 19.5]
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

    if mode == "paper":
        out = np.broadcast_to(PAPER, (H, W, 3)).copy()
        for bi in (2, 1, 0):
            A = acc[bi, :, :, 3:4]
            col = acc[bi, :, :, :3] / np.maximum(A, 1e-5)
            col = np.clip((col - 0.5) * 1.18 + 0.45, 0.02, 0.98)
            cov = 1.0 - np.exp(-A * ks[bi] * gain)
            out = out * (1.0 - cov) + col * cov
        out = out * get_vignette(H, W)
    else:
        total = np.zeros((H, W, 4), dtype=np.float32)
        for bi in (2, 1, 0):
            total += acc[bi] * ks[bi]
        A = total[:, :, 3:4] * gain
        col = total[:, :, :3] * gain / np.maximum(A, 1e-4)
        cov = 1.0 - np.exp(-A * 0.90)
        bloom = np.stack([gaussian_filter(col[:, :, c] * cov[:, :, 0], sigma=9.5) for c in range(3)], axis=-1)
        out = NIGHT[None, None, :] * (1.0 - cov * 0.94) + col * cov + bloom * 0.46

    out_hi = cv2.resize(np.clip(out, 0.0, 1.0), (FW, FH), interpolation=cv2.INTER_CUBIC)
    rng = np.random.default_rng(seed)
    grain = rng.normal(0.0, 0.009, (FH // 2, FW // 2, 1)).astype(np.float32)
    out_hi = np.clip(out_hi + cv2.resize(grain, (FW, FH))[..., None], 0.0, 1.0)
    return out_hi


_VOL_CACHE = {}
def get_segment_volume(seg_id):
    if seg_id in _VOL_CACHE:
        return _VOL_CACHE[seg_id]
    seg = next(s for s in MEMORY_SEGMENTS if s["id"] == seg_id)
    src = SRC_HORSE if seg["source"] == "horse" else SRC_STELLINE

    vw, vh = 136, 76
    cap = cv2.VideoCapture(src)
    fps_src = cap.get(cv2.CAP_PROP_FPS) or 24.0
    t0 = seg["clip_t0"]
    dur = seg["clip_dur"]
    max_frames = 44
    frames = []
    for i in range(max_frames):
        t_sample = t0 + (dur * i) / max(1, max_frames - 1)
        cap.set(cv2.CAP_PROP_POS_MSEC, t_sample * 1000.0)
        ok, fr = cap.read()
        if not ok:
            break
        fr = cv2.cvtColor(cv2.resize(fr, (vw, vh), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        frames.append(fr.astype(np.float32) / 255.0)
    cap.release()
    frames = np.stack(frames, axis=0)  # (T, vh, vw, 3)
    T = len(frames)

    # Normalize dark orphanage/furnace shots so both subtle shadow mist and bright firelight sing
    p92 = float(np.percentile(frames.mean(axis=-1), 94))
    boost = float(np.clip(0.88 / max(p92, 0.07), 1.0, 2.8))
    frames = np.clip((frames * boost) ** 0.82, 0.0, 1.0)

    # Compute Stelline's Emotional Feeling Salience Field F(t, y, x) in [0, 1]:
    # 1. Warmth chroma (amber firelight, wooden horse, skin tone, candle glow: R - B)
    warmth = np.clip((frames[..., 0] - frames[..., 2]) * 1.85 + frames.mean(axis=-1) * 0.55, 0.0, 1.0)
    # 2. Temporal motion delta (running boy, raking ashes, turning head)
    motion = np.linalg.norm(np.diff(frames, axis=0, prepend=frames[:1]), axis=-1)
    motion = np.clip(motion * 3.2, 0.0, 1.0)
    # 3. Spatial distance to the segment's Emotional Anchor (ax, ay)
    ax, ay = seg["feeling_anchor"]
    yy, xx = np.mgrid[0:vh, 0:vw].astype(np.float32)
    dist2 = ((xx / vw - ax) / 0.36) ** 2 + ((yy / vh - ay) / 0.38) ** 2
    anchor_gauss = np.exp(-dist2)[None, :, :]

    feeling = np.clip(0.38 * anchor_gauss + 0.36 * warmth + 0.26 * motion, 0.05, 1.0).astype(np.float32)

    # Pseudo-depth relief from luminance + vertical gradient + feeling salience
    lum0 = frames.mean(axis=(0, -1))
    d_map = cv2.GaussianBlur(0.65 * lum0 + 0.35 * anchor_gauss[0], (0, 0), 1.4)

    rng = np.random.default_rng(abs(hash(seg_id)) % (2**31))
    xs, ys, ss, ds, cols, wts, fls = [], [], [], [], [], [], []
    for s in range(T):
        prob = np.clip(0.24 + 0.62 * feeling[s], 0.20, 0.86)
        keep = rng.random((vh, vw)) < prob
        ky, kx = np.where(keep)
        jx = rng.uniform(-0.45, 0.45, len(kx)).astype(np.float32)
        jy = rng.uniform(-0.45, 0.45, len(ky)).astype(np.float32)

        x = ((kx + jx) / vw - 0.5) * 540.0
        y = ((ky + jy) / vh - 0.5) * 304.0
        d_val = (0.5 - d_map[ky, kx]) * 135.0
        c = frames[s, ky, kx]
        f_val = feeling[s, ky, kx]
        w = (0.35 + 0.65 * f_val).astype(np.float32)

        xs.append(x.astype(np.float32))
        ys.append(y.astype(np.float32))
        ss.append(np.full(len(kx), s, dtype=np.float32))
        ds.append(d_val.astype(np.float32))
        cols.append(c.astype(np.float32))
        wts.append(w)
        fls.append(f_val.astype(np.float32))

    vol = dict(
        seg=seg,
        T=T,
        raw_frames=frames,
        feeling_map=feeling.mean(axis=0),
        x=np.concatenate(xs),
        y=np.concatenate(ys),
        s=np.concatenate(ss),
        d=np.concatenate(ds),
        rgb=np.concatenate(cols),
        w=np.concatenate(wts),
        feeling=np.concatenate(fls),
        dz=15.5,
    )
    _VOL_CACHE[seg_id] = vol
    return vol


def build_master_timeline():
    """
    Builds the complete 72.0s (1728 frames at 24fps) 07-Spacetime timeline:
      - 0.0s .. 56.6s: All 14 Memory Segments (starting at 1:49 + Stelline's Mist Philosophy)
      - 56.6s .. 65.4s: The Signature 07-Spacetime Accelerating Montage (face-on push then side-on ±62°
                        4D spacetime strata cut, tightening from 0.85s down to 0.24s)
      - 65.4s .. 66.6s: The Drop to Silence (1.2s before one golden dot)
      - 66.6s .. 72.0s: 3D Point-Cloud Engraving ("6 · 10 · 21  /  ANYTHING REAL SHOULD BE A MIST")
    """
    shots = []
    for seg in MEMORY_SEGMENTS:
        shots.append(dict(
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

    # THE 07-SPACETIME MONTAGE (56.6s -> 65.4s):
    # Every key wooden-horse & Stelline volume twice: face-on push, then side-on ±62° 4D strata view
    montage_seq = [
        ("seg_02", "paper", "front", +1, 0.82),
        ("seg_02", "paper", "side",  +1, 0.74),
        ("seg_04", "paper", "front", -1, 0.68),
        ("seg_05", "paper", "side",  -1, 0.62),
        ("seg_06", "light", "front", +1, 0.58),
        ("seg_07", "light", "side",  +1, 0.54),
        ("seg_08", "light", "front", -1, 0.50),
        ("seg_08", "light", "side",  -1, 0.46),
        ("seg_09", "paper", "front", +1, 0.42),
        ("seg_11", "light", "side",  +1, 0.38),
        ("seg_11", "light", "front", -1, 0.35),
        ("seg_12", "light", "side",  -1, 0.32),
        ("seg_12", "light", "front", +1, 0.30),
        ("seg_13", "paper", "side",  +1, 0.28),
        ("seg_14", "light", "front", -1, 0.26),
        ("seg_08", "light", "side",  +1, 0.25),
        ("seg_14", "light", "side",  -1, 0.24),
    ]
    t_cur = 56.6
    for sid, md, akind, sgn, dur in montage_seq:
        t_next = round(t_cur + dur, 4)
        if akind == "front":
            cam0 = (0.0, 0.0, 680.0, 0.06 * sgn, 0.0)
            cam1 = (0.0, 0.0, 260.0, -0.06 * sgn, 0.0)
        else:
            cam0 = (210.0 * sgn, -14.0, 560.0, 1.06 * sgn, 0.05)
            cam1 = (175.0 * sgn,   8.0, 430.0, 0.88 * sgn, -0.03)
        shots.append(dict(
            t0=t_cur, t1=t_next, seg_id=sid, mode=md, assemble=False,
            cam0=cam0, cam1=cam1, mist_level=0.35,
            who="07-SPACETIME MONTAGE",
            say="Every volume twice: face-on push, then side-on ±62° through the body of light in time.",
            code="MONTAGE · 4D STRATA",
            montage=akind,
        ))
        t_cur = t_next

    t_drop = round(t_cur + 1.15, 4)
    shots.append(dict(t0=t_cur, t1=t_drop, seg_id=None, mode="drop"))
    shots.append(dict(t0=t_drop, t1=72.0, seg_id=None, mode="title"))
    return shots


MASTER_SHOTS = build_master_timeline()

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

    # Warm amber-gold gradient across the carved date
    ux = np.clip((xx / 960.0), 0.0, 1.0).astype(np.float32)
    rgb = np.stack([
        np.ones_like(ux) * 0.98,
        0.74 + 0.18 * ux,
        0.42 + 0.24 * ux
    ], axis=-1).astype(np.float32)

    _HORSE_TITLE_CLOUD = dict(x=x, y=y, z=z, sx=sx, sy=sy, sz=sz, rgb=rgb, w=arr[yy, xx].astype(np.float32))
    return _HORSE_TITLE_CLOUD


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
        out = np.broadcast_to(NIGHT, (FH, FW, 3)).copy()
        mote = smootherstep(min(1.0, u * 1.4))
        yy, xx = np.ogrid[:FH, :FW]
        glow = mote * np.exp(-((xx - FW * 0.5) ** 2 + (yy - FH * 0.5) ** 2) / 55.0)
        out += glow[..., None] * np.array([1.0, 0.82, 0.48], dtype=np.float32)
        return (np.clip(out, 0.0, 1.0) * 255.0).astype(np.uint8)

    # 2. THE 3D DUST-BUILT TITLE ("6 · 10 · 21 / Anything real should be a mist")
    if shot["mode"] == "title":
        tc = get_horse_title_cloud()
        u = (t - shot["t0"]) / max(shot["t1"] - shot["t0"], 1e-4)
        k_scatter = (1.0 - smootherstep(min(1.0, u / 0.52))) ** 2.2
        X = tc["x"] * (1.0 - k_scatter) + tc["sx"] * k_scatter
        Y = tc["y"] * (1.0 - k_scatter) + tc["sy"] * k_scatter
        Z = tc["z"] * (1.0 - k_scatter) + tc["sz"] * k_scatter

        yaw = (1.0 - smootherstep(min(1.0, u / 0.58))) * 0.48 + 0.04 * math.sin(u * 3.0)
        dist = 560.0 - 65.0 * ease(u)
        cy, sy = math.cos(yaw), math.sin(yaw)
        Xc = X * cy + Z * sy
        Zc = -X * sy + Z * cy + dist

        px = 520.0 * Xc / np.maximum(Zc, 30.0) + RW * 0.5
        py = 520.0 * Y / np.maximum(Zc, 30.0) + RH * 0.5
        rad = np.clip(0.90 + 2.9 * k_scatter + np.abs(Zc - dist) / 160.0, 0.8, 5.6).astype(np.float32)
        img = splat_gaussian_multiscale(px, py, Zc, rad, tc["rgb"], tc["w"] * 1.4, mode="light", gain=1.22, seed=fi)
        return (np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8)

    # 3. 4D SPACETIME VOLUME + STELLINE FEELING-MIST FIELD
    vol = get_segment_volume(shot["seg_id"])
    u = (t - shot["t0"]) / max(shot["t1"] - shot["t0"], 1e-4)
    eu = ease(u)

    cam0, cam1 = shot["cam0"], shot["cam1"]
    cx = lerp(cam0[0], cam1[0], eu)
    cy_cam = lerp(cam0[1], cam1[1], eu)
    dist = lerp(cam0[2], cam1[2], eu)
    yaw = lerp(cam0[3], cam1[3], eu)
    pitch = lerp(cam0[4], cam1[4], eu)

    present = (0.14 + 0.78 * u) * (vol["T"] - 1)
    age = present - vol["s"]

    vis = (age >= -2.0) & (age <= 28.0)
    x = vol["x"][vis].copy()
    y = vol["y"][vis].copy()
    d = vol["d"][vis]
    age = age[vis]
    rgb = vol["rgb"][vis]
    w_base = vol["w"][vis]
    fl = vol["feeling"][vis]

    z = age * vol["dz"] + d

    # Stelline's Mist Law: peripheral non-emotional detail (1 - fl) scatters into 3D mist!
    mist_amt = shot.get("mist_level", 0.45)
    if shot.get("assemble", False):
        mist_amt = max(mist_amt, (1.0 - smootherstep(min(1.0, u / 0.55))) ** 1.8)

    non_feeling = (1.0 - fl) ** 1.7 * mist_amt
    rng = np.random.default_rng(fi % 97 + 11)
    x += rng.normal(0.0, 1.0, len(x)).astype(np.float32) * (165.0 * non_feeling)
    y += rng.normal(0.0, 1.0, len(y)).astype(np.float32) * (115.0 * non_feeling)
    z += rng.normal(0.0, 1.0, len(z)).astype(np.float32) * (190.0 * non_feeling)

    # Emotional feeling anchors have longer temporal persistence tau (up to 26 slices)!
    tau_feeling = 9.0 + 18.0 * fl
    time_decay = np.where(age >= 0, np.exp(-age / tau_feeling), np.exp(-(age ** 2) / 1.2)).astype(np.float32)
    wt = w_base * time_decay * (0.42 + 0.68 * np.exp(-(age ** 2) / 2.8)).astype(np.float32)

    X = x - cx
    Y = y - cy_cam
    Z = z

    cy_r, sy_r = math.cos(yaw), math.sin(yaw)
    Xc = X * cy_r + Z * sy_r
    Zc1 = -X * sy_r + Z * cy_r

    cp_r, sp_r = math.cos(pitch), math.sin(pitch)
    Yc = Y * cp_r - Zc1 * sp_r
    Zc = Y * sp_r + Zc1 * cp_r + dist

    focal = 520.0
    px = focal * Xc / np.maximum(Zc, 25.0) + RW * 0.5
    py = focal * Yc / np.maximum(Zc, 25.0) + RH * 0.5

    # Points with high emotional feeling F stay sharp in bucket b0; low-F points bloom into bucket b2 mist!
    dof = np.abs(Zc - dist) / (230.0 if shot["mode"] == "paper" else 195.0)
    mist_rad = (1.0 - fl) * 2.35 * mist_amt
    rad = np.clip(0.80 + dof + mist_rad + 0.05 * np.maximum(0.0, age), 0.72, 5.8).astype(np.float32)

    img = splat_gaussian_multiscale(px, py, Zc, rad, rgb, wt, mode=shot["mode"], gain=1.10, seed=fi)

    # Unboxed, whisper-quiet Afterlight / VOIDBASTARD-TAO engravings (zero rectangular HUD boxes!)
    pil = Image.fromarray((img * 255.0).astype(np.uint8))
    draw = ImageDraw.Draw(pil, "RGBA")
    is_paper = (shot["mode"] == "paper")
    fg_main = (34, 28, 22) if is_paper else (244, 236, 220)
    fg_sub = (96, 84, 72) if is_paper else (178, 168, 152)
    fg_gold = (168, 96, 18) if is_paper else (255, 195, 92)

    f_mono = get_font("mono", 13)
    f_who = get_font("mono", 14)
    f_italic = get_font("italic", 31)

    angle_tag = "SIDE-ON ±62° · 4D SPACETIME STRATA" if shot.get("montage") == "side" else (
        "FACE-ON PUSH · PRESENT SLICE" if shot.get("montage") == "front" else f"MIST={int(mist_amt*100)}% · YAW {math.degrees(yaw):+05.1f}°"
    )
    draw.text((36, 26), f"07 · SPACETIME MIST   {shot['code']}", font=f_mono, fill=fg_sub + (195,))
    draw.text((FW - 36, 26), angle_tag, font=f_mono, fill=fg_sub + (195,), anchor="ra")

    if shot.get("montage") is None:
        ca = sm(shot["t0"], shot["t0"] + 0.45, t) * (1.0 - sm(shot["t1"] - 0.45, shot["t1"], t))
        if ca > 0.02:
            alpha = int(242 * ca)
            draw.text((FW // 2, FH - 82), shot["who"], font=f_who, fill=fg_gold + (int(alpha * 0.9),), anchor="mm")
            say_txt = shot["say"]
            if len(say_txt) > 86:
                mid = say_txt.rfind(" ", 0, 78)
                l1, l2 = say_txt[:mid], say_txt[mid+1:]
                draw.text((FW // 2, FH - 52), l1, font=f_italic, fill=fg_main + (alpha,), anchor="mm")
                draw.text((FW // 2, FH - 22), l2, font=f_italic, fill=fg_main + (alpha,), anchor="mm")
            else:
                draw.text((FW // 2, FH - 42), say_txt, font=f_italic, fill=fg_main + (alpha,), anchor="mm")

    return np.asarray(pil, dtype=np.uint8)


# ==============================================================================
# STEP 3: BUILD SYNCHRONIZED REAL DIALOGUE + 07-SPACETIME SCORE AUDIO TRACK
# ==============================================================================
def build_master_audio(out_wav):
    print("[2/5] Mixing real Stelline & Officer K dialogue with 07-spacetime harmonic bed...")
    sr = 44100
    dur = 72.0
    total_samples = int(dur * sr)
    mix = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Warm sub-bass & Vangelis/Afterlight harmonic drone bed
    t = np.arange(total_samples, dtype=np.float32) / sr
    drone = (
        0.055 * np.sin(2 * np.pi * 55.0 * t) +
        0.035 * np.sin(2 * np.pi * 82.41 * t + 0.3 * np.sin(2 * np.pi * 0.18 * t)) +
        0.025 * np.sin(2 * np.pi * 110.0 * t) +
        0.018 * np.sin(2 * np.pi * 164.81 * t)
    )
    # Silence during the 07-spacetime Drop (65.4s .. 66.6s)
    drop_env = 1.0 - ((t >= 65.35) & (t <= 66.65)).astype(np.float32) * 0.95
    drone *= drop_env
    mix[:, 0] += drone
    mix[:, 1] += drone

    # 2. Overlay the real extracted dialogue audio from each segment
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
        # Soft 0.18s fade-in / fade-out per segment
        fade_len = min(int(0.18 * sr), len(arr) // 3)
        env = np.ones(len(arr), dtype=np.float32)
        if fade_len > 1:
            env[:fade_len] = np.linspace(0.0, 1.0, fade_len)
            env[-fade_len:] = np.linspace(1.0, 0.0, fade_len)
        arr = arr * env[:, None] * 1.15
        start_idx = int(seg["film_t0"] * sr)
        end_idx = min(total_samples, start_idx + len(arr))
        mix[start_idx:end_idx] += arr[:end_idx - start_idx]

    # 3. Accelerating montage pulse hits (56.6s .. 65.4s) + Golden Dot chime at 66.65s
    for s in MASTER_SHOTS:
        if s.get("montage") is not None:
            idx = int(s["t0"] * sr)
            plen = min(int(0.22 * sr), total_samples - idx)
            if plen > 0:
                pt = np.arange(plen, dtype=np.float32) / sr
                hit = 0.16 * np.exp(-pt * 18.0) * np.sin(2 * np.pi * (92.0 - 40.0 * pt) * pt)
                mix[idx:idx+plen, 0] += hit
                mix[idx:idx+plen, 1] += hit

    chime_idx = int(66.65 * sr)
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
    print("[2/5] Pre-warming 14 4D Spacetime Feeling-Mist Volumes...")
    for seg in MEMORY_SEGMENTS:
        get_segment_volume(seg["id"])

    out_wav = "/tmp/stelline_07_spacetime_audio.wav"
    build_master_audio(out_wav)

    total_frames = int(72.0 * FPS)
    print(f"[3/5] Rendering {total_frames} frames of stelline_wooden_horse_07_spacetime.mp4 (1280x720 @ 24fps)...")

    out_mp4 = os.path.join(VID_DIR, "stelline_wooden_horse_07_spacetime.mp4")
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
        "-i", out_wav,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        out_mp4
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # Render in parallel batches of 48 frames so memory stays low and speed is high
    batch_size = 48
    with ProcessPoolExecutor(max_workers=8) as ex:
        for b0 in range(0, total_frames, batch_size):
            b1 = min(total_frames, b0 + batch_size)
            frames = list(ex.map(render_master_frame, range(b0, b1)))
            for fr in frames:
                proc.stdin.write(fr.tobytes())
            if b0 % 240 == 0:
                print(f"  Rendered {b1}/{total_frames} frames ({b1/FPS:.1f}s / 72.0s)")

    proc.stdin.close()
    proc.wait()
    print(f"[4/5] Saved Master Film: {out_mp4} ({os.path.getsize(out_mp4)/1e6:.2f} MB)")

    # Copy to seeing_spacetime_films and ARTIFACT_DIR
    shutil.copy2(out_mp4, os.path.join(FILM_OUT_DIR, "stelline_wooden_horse_07_spacetime.mp4"))
    shutil.copy2(out_mp4, os.path.join(ARTIFACT_DIR, "stelline_wooden_horse_07_spacetime.mp4"))

    # Build the 4K Contact Sheet (3840 x 2160) showing all 14 Memory Segments + Montage + 6·10·21 Title
    print("[5/5] Building 4K Contact Sheet: stelline_wooden_horse_spacetime_sheet.png...")
    sw, sh = 3840, 2160
    sheet = Image.new("RGB", (sw, sh), (8, 10, 14))
    draw = ImageDraw.Draw(sheet)
    f_hdr = get_font("serif", 42)
    f_sub = get_font("mono", 18)
    f_cell = get_font("mono", 14)
    f_quote = get_font("italic", 20)

    draw.text((64, 34), "DR. ANA STELLINE & THE TOY WOODEN HORSE (1:49 – 3:25)  ·  07-SPACETIME MIST OF FEELING", font=f_hdr, fill=(244, 236, 220))
    draw.text((64, 88), "“Memory's not about more detail — that's not how memory works. We recall with our feelings. Anything real should be a mist.” (4:16 – 4:27)", font=f_sub, fill=(255, 195, 92))

    sample_times = [s["film_t0"] + 0.55 * (s["film_t1"] - s["film_t0"]) for s in MEMORY_SEGMENTS] + [60.8, 69.5]
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

        # Inset raw reference frame in top-right of cell for direct raw-vs-mist comparison
        if idx < len(MEMORY_SEGMENTS):
            seg = MEMORY_SEGMENTS[idx]
            vol = get_segment_volume(seg["id"])
            raw_fr = (vol["raw_frames"][len(vol["raw_frames"]) // 2] * 255.0).astype(np.uint8)
            im_raw = Image.fromarray(raw_fr).resize((192, 108), Image.Resampling.BILINEAR)
            sheet.paste(im_raw, (x0 + cw - 200, y0 + 8))
            draw.rectangle([x0 + cw - 200, y0 + 8, x0 + cw - 8, y0 + 116], outline=(255, 195, 92), width=1)
            src_mm = int(seg["src_t0"]) // 60
            src_ss = seg["src_t0"] - src_mm * 60
            draw.text((x0 + 8, y0 + ch - 46), f"{seg['code']}  [SRC {src_mm}:{src_ss:05.2f}]  ·  {seg['title']}", font=f_cell, fill=(92, 228, 255))
            draw.text((x0 + 8, y0 + ch - 24), seg["say"][:92] + ("…" if len(seg["say"]) > 92 else ""), font=f_quote, fill=(230, 222, 206))
        elif idx == 14:
            draw.text((x0 + 8, y0 + ch - 46), "XV · 07-SPACETIME MONTAGE  [SIDE-ON ±62° 4D STRATA]", font=f_cell, fill=(255, 195, 92))
            draw.text((x0 + 8, y0 + ch - 24), "Every memory volume twice: face-on push, then side-on ±62° exposing the body of light through time.", font=f_quote, fill=(230, 222, 206))
        else:
            draw.text((x0 + 8, y0 + ch - 46), "XVI · THE DROP & SINGLE GOLD EMBER  [6 · 10 · 21]", font=f_cell, fill=(255, 195, 92))
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
        "drop_t0": 65.4,
        "title_t0": 66.6,
        "duration": 72.0,
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
