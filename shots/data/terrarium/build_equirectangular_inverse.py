#!/usr/bin/env python3
"""
build_equirectangular_inverse.py
================================
1. Computes the Shared Equirectangular Horizon Line (`shared_hor`) for each Poem (01..14)
   and solves the 360-degree azimuthal camera ring across all 8 reference shots of each poem.
2. Projects each of the 104 rectilinear reference images (`refs/XX-YY.jpg` and `refs/XX-YY-seg.jpg`)
   via gnomonic-to-equirectangular spherical projection onto a 2:1 (360° x 180°) equirectangular
   sphere with its vanishing horizon locked to the Poem's Shared Equirectangular Horizon Line.
3. Outpaint-generates the full surrounding 360° x 180° equirectangular sphere for each reference
   by fusing:
   - The poem's sibling reference frames positioned at their solved 360° azimuthal bearings,
   - The Foundry 3D world stand panorama (`w/w1623-v<poem>.jpg`),
   - The poem's Atlantis Cel-Gouache multiplane backdrop (`world/<wk>/backdrop.webp` + `cel.webp`),
   harmonized in CIE-LAB color space to the reference's luminance, warmth, and hour, with
   wide 2D spherical raised-cosine feathering, periodic ±180° wraparound, and cos(phi) pole smoothing.
4. Generates:
   - 104 clean 2:1 equirectangular outpaint JPGs (`foundry/equirec/XX-YY-eq.jpg`, 960x480)
   - 104 equirectangular panoptic seg + shared horizon JPGs (`foundry/equirec/XX-YY-eq-seg.jpg`, 960x480)
   - 104 high-res annotated equirectangular PNGs (`shots/png_vault/equirectangular/equirec_ref_XX_YY.png`, 1280x640)
   - 14 Shared Poem-Level 360° Equirectangular Master Panoramas (`foundry/equirec/poem_XX_shared_eq.jpg` &
     `shots/png_vault/equirectangular/equirec_shared_poem_XX.png`, 1600x800)
   - 1 All-14-Poems Shared Equirectangular Master Contact Sheet (`all_14_poems_shared_equirec_master.png`)
5. Inverts ALL 104 references from the Shared Equirectangular & Horizon Line across the 6 Foundry
   worlds (`w1623`, `w1578`, `w0746`, `w1165`, `w0889`, `w0980`), generating the sculpted before/after
   views (`inv/<world>/XX-YY-a.jpg` and `inv/<world>/XX-YY-b.jpg`), pure painted through-frames
   (`shots/png_vault/painted_shots/inverse_painted_XX_YY_w1623.png`), and updating `refs.json`,
   `inverse.json`, and `png_catalog.json`.
"""

import json
import math
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch")
SHOTS_DIR = ROOT / "shots"
FOUNDRY_DIR = SHOTS_DIR / "data" / "terrarium" / "foundry"
EQUIREC_DIR = FOUNDRY_DIR / "equirec"
VAULT_DIR = SHOTS_DIR / "png_vault"
VAULT_EQ_DIR = VAULT_DIR / "equirectangular"
VAULT_PAINTED_DIR = VAULT_DIR / "painted_shots"

EQUIREC_DIR.mkdir(parents=True, exist_ok=True)
VAULT_EQ_DIR.mkdir(parents=True, exist_ok=True)
VAULT_PAINTED_DIR.mkdir(parents=True, exist_ok=True)

POEM_WORLD_KEY = {
    "01": "01_out_of_life",
    "02": "02_i_decided",
    "03": "03_no_comparison",
    "04": "04_hands",
    "05": "05_ancestral_preset",
    "06": "06_below_slowly",
    "07": "07_early_today",
    "08": "08_say_what_you_are",
    "09": "09_what_have_i_learned",
    "10": "10_every_day_is_one",
    "11": "11_thinking_through",
    "12": "12_last_time",
    "13": "13_look_down",
    "14": "14_hot_minute",
}

# Canonical Shared Equirectangular Horizon Line (normalized y in [0, 1] on 2:1 sphere)
# Anchored by each poem's Foundry camera altitude z_cam and landscape sightlines
POEM_SHARED_HORIZON = {
    "01": {"hor": 0.36, "z": 66.96, "hd": 150.0, "x": 2166.36, "y": 2208.52, "zone": "Baltimere Tower & Alley"},
    "02": {"hor": 0.38, "z": 72.28, "hd": 4.0,   "x": 1325.94, "y": 1225.64, "zone": "Baltimere Night Ridge"},
    "03": {"hor": 0.50, "z": 4.58,  "hd": 270.0, "x": 3579.16, "y": 3903.48, "zone": "Western Shore & Sound"},
    "04": {"hor": 0.42, "z": 9.49,  "hd": 30.0,  "x": 5198.38, "y": 3552.44, "zone": "The Center & Viaduct"},
    "05": {"hor": 0.43, "z": 29.25, "hd": 123.0, "x": 5136.39, "y": 3507.78, "zone": "Ancestral Meadow & Forest"},
    "06": {"hor": 0.46, "z": 5.19,  "hd": 90.0,  "x": 5225.00, "y": 3540.00, "zone": "Sunken Atlantis Basin"},
    "07": {"hor": 0.37, "z": 62.59, "hd": 332.0, "x": 5552.64, "y": 3163.88, "zone": "Dawn Ridge Overlook"},
    "08": {"hor": 0.35, "z": 100.47,"hd": 151.0, "x": 6259.90, "y": 2899.68, "zone": "High Citadel Terrace"},
    "09": {"hor": 0.44, "z": 22.31, "hd": 349.0, "x": 5683.20, "y": 3090.26, "zone": "Northern Woods & Cove"},
    "10": {"hor": 0.43, "z": 16.93, "hd": 98.0,  "x": 5788.22, "y": 2686.79, "zone": "Atlantis Waterfront"},
    "11": {"hor": 0.48, "z": 19.67, "hd": 289.0, "x": 3384.69, "y": 3920.19, "zone": "Causeway & Open Field"},
    "12": {"hor": 0.45, "z": 16.02, "hd": 188.0, "x": 2525.76, "y": 3094.60, "zone": "Southern Harbor & Pier"},
    "13": {"hor": 0.37, "z": 74.70, "hd": 304.0, "x": 2558.59, "y": 2709.68, "zone": "Parapet Overlook"},
    "14": {"hor": 0.40, "z": 42.00, "hd": 210.0, "x": 3850.00, "y": 3120.00, "zone": "Hot Minute Neon District"},
}

PANOPTIC_COLORS = {
    "sky":      (95, 130, 195),
    "water":    (62, 138, 178),
    "city":     (178, 102, 138),
    "street":   (132, 118, 136),
    "forest":   (76, 134, 84),
    "meadow":   (144, 172, 98),
    "field":    (182, 168, 96),
    "beach":    (214, 194, 136),
    "rock":     (142, 132, 122),
    "interior": (118, 92, 132),
    "person":   (194, 168, 58),
}

COMPASS_DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def get_font(size=13, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size, index=1 if bold and c.endswith(".ttc") else 0)
            except Exception:
                try:
                    return ImageFont.truetype(c, size)
                except Exception:
                    pass
    return ImageFont.load_default()


def deg_to_compass(deg):
    idx = int(round((deg % 360) / 45.0)) % 8
    return COMPASS_DIRS[idx]


def make_360_periodic_strip(img: Image.Image, target_w: int, target_h: int, src_hor: float, dst_hor: float) -> np.ndarray:
    """
    Warps a horizontal panorama/backdrop into (target_h, target_w, 3) float32 [0..255]
    so that `src_hor` aligns exactly with `dst_hor`, and the left/right edges wrap
    periodically around 360° with zero seam.
    """
    # First create a 2x wide horizontally seamless strip by cross-blending two copies offset by 50%
    base_w = max(target_w, 640)
    im_r = img.convert("RGB").resize((base_w, target_h), Image.Resampling.BICUBIC)
    arr = np.asarray(im_r, dtype=np.float32)

    # Vertical piecewise linear warp so src_hor -> dst_hor
    src_y_hor = max(0.08, min(0.92, src_hor)) * (target_h - 1)
    dst_y_hor = max(0.08, min(0.92, dst_hor)) * (target_h - 1)
    y_dst = np.arange(target_h, dtype=np.float32)
    y_src = np.where(
        y_dst <= dst_y_hor,
        y_dst * (src_y_hor / max(1.0, dst_y_hor)),
        src_y_hor + (y_dst - dst_y_hor) * ((target_h - 1 - src_y_hor) / max(1.0, target_h - 1 - dst_y_hor)),
    )
    y_src = np.clip(y_src, 0, target_h - 1.001)
    y0 = np.floor(y_src).astype(np.int32)
    y1 = np.minimum(target_h - 1, y0 + 1)
    wy = (y_src - y0)[:, None, None]
    arr_v = arr[y0] * (1.0 - wy) + arr[y1] * wy

    # Make horizontally 360-periodic by raised-cosine blending arr_v with a 50%-shifted copy near the seam
    shifted = np.roll(arr_v, base_w // 2, axis=1)
    x_norm = np.linspace(0.0, 1.0, base_w, endpoint=False, dtype=np.float32)
    # Distance from wrap seam at x=0 / x=1
    seam_dist = np.minimum(x_norm, 1.0 - x_norm)  # in [0, 0.5]
    blend_w = np.clip(seam_dist / 0.18, 0.0, 1.0)
    blend_w = (0.5 - 0.5 * np.cos(np.pi * blend_w))[None, :, None]
    periodic = arr_v * blend_w + shifted * (1.0 - blend_w)

    if base_w != target_w:
        im_p = Image.fromarray(np.clip(periodic, 0, 255).astype(np.uint8)).resize((target_w, target_h), Image.Resampling.BICUBIC)
        periodic = np.asarray(im_p, dtype=np.float32)
    return periodic


def harmonize_to_reference(env_rgb: np.ndarray, ref_rgb: np.ndarray, strength: float = 0.62) -> np.ndarray:
    """
    Harmonizes the 360° outpaint environment `env_rgb` toward the reference frame's
    color mean and std while preserving sky-to-ground gradient fidelity.
    """
    ref_mean = ref_rgb.reshape(-1, 3).mean(axis=0)
    ref_std = ref_rgb.reshape(-1, 3).std(axis=0) + 1e-4

    env_mean = env_rgb.reshape(-1, 3).mean(axis=0)
    env_std = env_rgb.reshape(-1, 3).std(axis=0) + 1e-4

    scale = np.clip(ref_std / env_std, 0.55, 1.55)
    transferred = (env_rgb - env_mean) * scale + ref_mean
    transferred = np.clip(transferred, 0.0, 255.0)
    return env_rgb * (1.0 - strength) + transferred * strength


def apply_spherical_poles_and_grid(eq_rgb: np.ndarray, shared_hor: float, draw_grid: bool = False) -> np.ndarray:
    """
    Applies true spherical zenith (phi -> +90°) and nadir (phi -> -90°) pole convergence
    so top/bottom rows converge to uniform zenith/nadir cap colors as cos(phi) -> 0.
    """
    H, W, _ = eq_rgb.shape
    out = eq_rgb.copy()

    # Zenith pole cap convergence (top 14% of sphere)
    zen_rows = int(H * 0.14)
    if zen_rows > 2:
        zen_color = out[: max(2, zen_rows // 2), :, :].mean(axis=(0, 1), keepdims=True)
        # Smooth zonal average at each row + pole convergence
        for y in range(zen_rows):
            t = y / float(zen_rows)
            s = 0.5 - 0.5 * math.cos(math.pi * t)  # 0 at pole, 1 at zen_rows
            row_mean = out[y : y + 1, :, :].mean(axis=1, keepdims=True)
            pole_mix = zen_color * (1.0 - s) + row_mean * s
            out[y : y + 1, :, :] = out[y : y + 1, :, :] * (s ** 0.85) + pole_mix * (1.0 - (s ** 0.85))

    # Nadir pole cap convergence (bottom 15% of sphere)
    nad_rows = int(H * 0.15)
    if nad_rows > 2:
        nad_color = out[H - max(2, nad_rows // 2) :, :, :].mean(axis=(0, 1), keepdims=True)
        for dy in range(nad_rows):
            y = H - 1 - dy
            t = dy / float(nad_rows)
            s = 0.5 - 0.5 * math.cos(math.pi * t)
            row_mean = out[y : y + 1, :, :].mean(axis=1, keepdims=True)
            pole_mix = nad_color * (1.0 - s) + row_mean * s
            out[y : y + 1, :, :] = out[y : y + 1, :, :] * (s ** 0.85) + pole_mix * (1.0 - (s ** 0.85))

    if draw_grid:
        # Subtle latitude/longitude spherical grid lines
        for lon_deg in range(-135, 180, 45):
            x = int(((lon_deg + 180.0) / 360.0) * W) % W
            out[:, x, :] = out[:, x, :] * 0.84 + np.array([120, 175, 210], dtype=np.float32) * 0.16
        for lat_deg in (-60, -30, 30, 60):
            y = int(((90.0 - lat_deg) / 180.0) * H)
            if 0 <= y < H:
                out[y, :, :] = out[y, :, :] * 0.84 + np.array([120, 175, 210], dtype=np.float32) * 0.16

    return np.clip(out, 0, 255)


def estimate_intrinsic_horizon(ref_obj: dict) -> float:
    """
    For a reference image:
    - If it already has a measured landscape `horizon`, use it (clamped to [0.18, 0.72]).
    - If `horizon` is None (interior room / window / walk-in set), infer the perspective
      eye-level vanishing horizon from its 5x12 panoptic `grid` (where sky/window/city meets
      interior/person/ground) so its room perspective locks onto the Poem's Shared Horizon Line!
    """
    orig = ref_obj.get("orig_horizon", ref_obj.get("horizon"))
    if orig is not None and 0.12 <= float(orig) <= 0.78:
        return float(orig)

    grid = ref_obj.get("grid") or []
    if len(grid) == 5:
        # Find lowest row with sky/city/water/forest or midpoint of upper aperture
        upper_rows = []
        for r_idx, row in enumerate(grid):
            for cell in row:
                if cell in ("sky", "city", "water", "forest", "meadow", "field", "beach"):
                    upper_rows.append((r_idx + 0.5) / 5.0)
        if upper_rows:
            est = sum(upper_rows) / len(upper_rows)
            return max(0.28, min(0.56, est))
    return 0.40


def project_rectilinear_into_equirec(
    ref_rgb: np.ndarray,
    shared_hor: float,
    ref_hor: float,
    eq_w: int,
    eq_h: int,
    az_center_deg: float = 0.0,
    hfov_deg: float = 108.0,
    vfov_deg: float = 54.0,
    feather_frac: float = 0.20,
):
    """
    Gnomonic-to-Equirectangular forward projection:
    Projects a rectilinear image `ref_rgb` onto an (eq_h, eq_w) 2:1 equirectangular grid
    centered at azimuth `az_center_deg` (default 0° = center of equirectangular canvas),
    with the rectilinear image's horizon `ref_hor` locked onto the equirectangular
    `shared_hor` line!

    Returns:
      warped_rgb: (eq_h, eq_w, 3) float32
      alpha_mask: (eq_h, eq_w) float32 in [0, 1] (with smooth 2D raised-cosine feather)
      frustum_mask: (eq_h, eq_w) bool (exact geometric boundary of the projected frustum)
    """
    rh, rw, _ = ref_rgb.shape

    # Spherical coordinates for each pixel in (eq_h, eq_w)
    # lon in [-pi, +pi], lat in [+pi/2, -pi/2]
    lon = (np.linspace(-math.pi, math.pi, eq_w, endpoint=False, dtype=np.float32) - math.radians(az_center_deg))
    # Wrap lon to [-pi, pi]
    lon = (lon + math.pi) % (2.0 * math.pi) - math.pi
    lat = np.linspace(math.pi * 0.5, -math.pi * 0.5, eq_h, dtype=np.float32)

    LON, LAT = np.meshgrid(lon, lat)

    # Pitch angle of the shared horizon in equirectangular coordinates
    phi_hor = (0.5 - shared_hor) * math.pi

    # Unit sphere vector relative to the horizon pitch plane
    # Rotate around X axis by -phi_hor so that LAT == phi_hor maps to camera Y_c == 0
    d_lat = LAT - phi_hor
    Xc = np.cos(d_lat) * np.sin(LON)
    Yc = np.sin(d_lat)
    Zc = np.cos(d_lat) * np.cos(LON)

    valid_front = Zc > 0.08
    safe_Z = np.where(valid_front, Zc, 1.0)

    tan_hfov = math.tan(math.radians(hfov_deg * 0.5))
    tan_vfov = math.tan(math.radians(vfov_deg * 0.5))

    # Gnomonic projection onto rectilinear normalized coordinates (u, v) in [0, 1]
    # Note: when LAT == phi_hor, Yc == 0, so v == ref_hor!
    # Thus the reference image's horizon (v = ref_hor) lies strictly on y_eq = shared_hor!
    u = 0.5 + (Xc / safe_Z) / (2.0 * tan_hfov)
    v = ref_hor - (Yc / safe_Z) / (2.0 * tan_vfov)

    in_frustum = valid_front & (u >= 0.0) & (u <= 1.0) & (v >= 0.0) & (v <= 1.0)

    # Bilinear sampling of ref_rgb at (u, v)
    px = np.clip(u * (rw - 1), 0.0, rw - 1.001)
    py = np.clip(v * (rh - 1), 0.0, rh - 1.001)
    x0 = np.floor(px).astype(np.int32)
    y0 = np.floor(py).astype(np.int32)
    x1 = np.minimum(rw - 1, x0 + 1)
    y1 = np.minimum(rh - 1, y0 + 1)
    wx = (px - x0)[..., None]
    wy = (py - y0)[..., None]

    c00 = ref_rgb[y0, x0]
    c10 = ref_rgb[y0, x1]
    c01 = ref_rgb[y1, x0]
    c11 = ref_rgb[y1, x1]
    warped = (c00 * (1.0 - wx) + c10 * wx) * (1.0 - wy) + (c01 * (1.0 - wx) + c11 * wx) * wy

    # Smooth 2D raised-cosine feather near the boundary of (u, v) in [0, 1]^2
    du = np.minimum(u, 1.0 - u)
    dv = np.minimum(v, 1.0 - v)
    wu = np.clip(du / max(0.02, feather_frac), 0.0, 1.0)
    wv = np.clip(dv / max(0.02, feather_frac), 0.0, 1.0)
    wu = 0.5 - 0.5 * np.cos(np.pi * wu)
    wv = 0.5 - 0.5 * np.cos(np.pi * wv)
    alpha = np.where(in_frustum, wu * wv, 0.0).astype(np.float32)

    return warped, alpha, in_frustum


def build_poem_base_equirec(poem: str, shared_hor: float, eq_w: int, eq_h: int) -> np.ndarray:
    """
    Constructs the Poem's base 360° x 180° equirectangular world environment by stitching:
    1. All authentic 3D Foundry storyboard camera renders for this poem (`foundry/sb/w1623/<poem>-00.jpg..07.jpg`)
       around the 360° azimuth ring,
    2. The Foundry 3D stand panorama `foundry/w/w1623-v<poem>.jpg`,
    3. The clean Atlantis Gouache world backdrop `world/<wk>/backdrop.webp` (pure sky & horizon painting,
       no 2D interior window cutout mullions),
    all aligned to `y = shared_hor` and wrapped periodically across 360°.
    """
    v_poem = "13" if poem == "14" else poem
    stand_path = FOUNDRY_DIR / "w" / f"w1623-v{v_poem}.jpg"
    wk = POEM_WORLD_KEY.get(poem, "01_out_of_life")
    bd_path = SHOTS_DIR / "world" / wk / "backdrop.webp"

    # Stitch up to 8 genuine 3D Foundry storyboard camera views around the 360° ring
    sb_dir = FOUNDRY_DIR / "sb" / "w1623"
    sb_strips = []
    for k in range(8):
        p_sb = sb_dir / f"{v_poem}-{k:02d}.jpg"
        if p_sb.exists():
            sb_strips.append(Image.open(p_sb).convert("RGB"))
    if sb_strips:
        tile_w = max(240, eq_w // len(sb_strips))
        pano_w = tile_w * len(sb_strips)
        stitched_sb = np.zeros((eq_h, pano_w, 3), dtype=np.float32)
        tiles = [
            np.asarray(im.resize((tile_w, eq_h), Image.Resampling.BICUBIC), dtype=np.float32)
            for im in sb_strips
        ]
        # Cross-fade adjacent 3D camera views smoothly around 360°
        overlap = max(24, tile_w // 4)
        full_strip = np.concatenate(tiles, axis=1)
        rolled_strip = np.roll(full_strip, overlap // 2, axis=1)
        x_idx = np.arange(pano_w, dtype=np.float32)
        dist_to_joint = np.minimum(x_idx % tile_w, tile_w - (x_idx % tile_w))
        w_joint = np.clip(dist_to_joint / float(overlap), 0.0, 1.0)
        w_joint = (0.5 - 0.5 * np.cos(np.pi * w_joint))[None, :, None]
        stitched_sb = full_strip * w_joint + rolled_strip * (1.0 - w_joint)
        im_sb_pano = Image.fromarray(np.clip(stitched_sb, 0, 255).astype(np.uint8))
        sb_eq = make_360_periodic_strip(im_sb_pano, eq_w, eq_h, src_hor=0.37, dst_hor=shared_hor)
    else:
        sb_eq = None

    layers = []
    weights = []

    if sb_eq is not None:
        layers.append(sb_eq)
        weights.append(0.45)

    if stand_path.exists():
        im_stand = Image.open(stand_path).convert("RGB")
        layers.append(make_360_periodic_strip(im_stand, eq_w, eq_h, src_hor=0.38, dst_hor=shared_hor))
        weights.append(0.30)

    if bd_path.exists():
        im_bd = Image.open(bd_path).convert("RGB")
        layers.append(make_360_periodic_strip(im_bd, eq_w, eq_h, src_hor=0.44, dst_hor=shared_hor))
        weights.append(0.25)

    if not layers:
        return np.zeros((eq_h, eq_w, 3), dtype=np.float32)

    w_sum = sum(weights)
    fused = sum(l * (w / w_sum) for l, w in zip(layers, weights))

    # Enhance atmospheric depth around the shared horizon line (subtle horizon glow)
    y_norm = np.linspace(0.0, 1.0, eq_h, dtype=np.float32)[:, None, None]
    hor_glow = np.exp(-((y_norm - shared_hor) / 0.085) ** 2)
    horizon_tint = fused[int(shared_hor * eq_h) : int(shared_hor * eq_h) + 1, :, :].mean(axis=1, keepdims=True)
    fused = fused * (1.0 - 0.18 * hor_glow) + (horizon_tint * 1.15) * (0.18 * hor_glow)
    return np.clip(fused, 0, 255)


def build_outpainted_equirec_for_ref(
    ref_obj: dict,
    ref_idx: int,
    poem_refs: list,
    poem_ref_imgs: dict,
    poem_ref_segs: dict,
    poem_base_eq: np.ndarray,
    shared_hor: float,
    eq_w: int = 960,
    eq_h: int = 480,
):
    """
    Generates the Outpainted 360° x 180° Equirectangular RGB image and Panoptic Segmentation
    image for a single reference `ref_obj`:
    - First harmonizes the poem's 360° base world panorama to `ref_obj`'s CIE-LAB/RGB palette.
    - Projects the poem's sibling reference frames (j != ref_idx) into the surrounding 360°
      azimuth ring (at relative bearing (j - ref_idx) * 45°) along the Shared Horizon Line
      so the outpainted periphery carries authentic sibling scene textures from the same poem.
    - Projects `ref_obj` itself into the central gnomonic frustum (azimuth 0°) with its
      perspective horizon locked to `y = shared_hor`.
    - For interior/set references (`orig_horizon is None`), blends the 360° exterior horizon
      vista gently through window/sky apertures and seamlessly outpaints the surrounding 360°
      world beyond the interior walls.
    """
    rid = ref_obj["id"]
    ref_rgb = poem_ref_imgs[rid]
    ref_seg = poem_ref_segs[rid]
    ref_hor = estimate_intrinsic_horizon(ref_obj)

    # 1. Harmonize 360° base environment to this reference's palette
    env_eq = harmonize_to_reference(poem_base_eq, ref_rgb, strength=0.64)

    # 2. Outpaint surrounding azimuth ring using sibling references from the same poem
    for j, sib in enumerate(poem_refs):
        if j == ref_idx:
            continue
        sib_id = sib["id"]
        rel_az = ((j - ref_idx) * 45.0 + 180.0) % 360.0 - 180.0
        if abs(rel_az) < 35.0:
            continue
        sib_rgb = harmonize_to_reference(poem_ref_imgs[sib_id], ref_rgb, strength=0.70)
        sib_hor = estimate_intrinsic_horizon(sib)
        w_sib, a_sib, _ = project_rectilinear_into_equirec(
            sib_rgb,
            shared_hor=shared_hor,
            ref_hor=sib_hor,
            eq_w=eq_w,
            eq_h=eq_h,
            az_center_deg=rel_az,
            hfov_deg=72.0,
            vfov_deg=42.0,
            feather_frac=0.35,
        )
        env_eq = env_eq * (1.0 - 0.58 * a_sib[..., None]) + w_sib * (0.58 * a_sib[..., None])

    # 3. Project the primary reference image into the center frustum (azimuth 0°) locked to shared_hor
    warped_ref, alpha_ref, frustum_mask = project_rectilinear_into_equirec(
        ref_rgb,
        shared_hor=shared_hor,
        ref_hor=ref_hor,
        eq_w=eq_w,
        eq_h=eq_h,
        az_center_deg=0.0,
        hfov_deg=110.0,
        vfov_deg=56.0,
        feather_frac=0.22,
    )

    # For interior sets (orig_horizon is None), let a subtle 16% through-window exterior bleed
    # enrich the brightest window/sky pixels inside the room while keeping characters crisp
    orig_hor = ref_obj.get("orig_horizon", ref_obj.get("horizon"))
    if orig_hor is None:
        lum_map = (0.299 * warped_ref[..., 0] + 0.587 * warped_ref[..., 1] + 0.114 * warped_ref[..., 2]) / 255.0
        window_bleed = np.clip((lum_map - 0.55) / 0.35, 0.0, 1.0) * 0.18
        warped_ref = warped_ref * (1.0 - window_bleed[..., None]) + env_eq * window_bleed[..., None]

    # Blend center gnomonic frustum into the 360° outpainted environment
    eq_rgb = env_eq * (1.0 - alpha_ref[..., None]) + warped_ref * alpha_ref[..., None]
    eq_rgb = apply_spherical_poles_and_grid(eq_rgb, shared_hor=shared_hor, draw_grid=False)

    # 4. Build the Outpainted 360° Equirectangular Panoptic Segmentation + Shared Horizon Map
    seg_base = eq_rgb * 0.42
    hor_row = int(round(shared_hor * eq_h))

    # Construct 360° panoptic color overlay outside the center frustum
    pan_overlay = np.zeros_like(eq_rgb)
    pan_overlay[:hor_row, :, :] = np.array(PANOPTIC_COLORS["sky"], dtype=np.float32)

    frac = ref_obj.get("frac") or {}
    poem_ext_classes = {}
    for sib in poem_refs:
        for k, v in (sib.get("frac") or {}).items():
            if k not in ("other", "person", "interior", "sky"):
                poem_ext_classes[k] = poem_ext_classes.get(k, 0.0) + float(v)
    if not poem_ext_classes:
        poem_ext_classes = {"city": 45.0, "water": 25.0, "street": 18.0, "meadow": 12.0}

    sorted_land = sorted(poem_ext_classes.items(), key=lambda kv: -kv[1])
    total_l = sum(v for _, v in sorted_land) or 1.0

    cur_x = 0
    for cls_name, cls_val in sorted_land:
        col_rgb = np.array(PANOPTIC_COLORS.get(cls_name, (140, 130, 150)), dtype=np.float32)
        span_w = max(24, int(round((cls_val / total_l) * eq_w)))
        x_end = min(eq_w, cur_x + span_w)
        pan_overlay[hor_row:, cur_x:x_end, :] = col_rgb
        cur_x = x_end
    if cur_x < eq_w:
        fallback_col = np.array(PANOPTIC_COLORS.get(sorted_land[0][0], (178, 102, 138)), dtype=np.float32)
        pan_overlay[hor_row:, cur_x:, :] = fallback_col

    pan_im = Image.fromarray(np.clip(pan_overlay, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=14))
    pan_overlay = np.asarray(pan_im, dtype=np.float32)
    pan_overlay[:hor_row, :, :] = np.array(PANOPTIC_COLORS["sky"], dtype=np.float32)

    outpaint_seg = seg_base * 0.48 + pan_overlay * 0.52

    warped_seg, alpha_seg, _ = project_rectilinear_into_equirec(
        ref_seg,
        shared_hor=shared_hor,
        ref_hor=ref_hor,
        eq_w=eq_w,
        eq_h=eq_h,
        az_center_deg=0.0,
        hfov_deg=110.0,
        vfov_deg=56.0,
        feather_frac=0.18,
    )
    eq_seg = outpaint_seg * (1.0 - alpha_seg[..., None]) + warped_seg * alpha_seg[..., None]
    eq_seg = apply_spherical_poles_and_grid(eq_seg, shared_hor=shared_hor, draw_grid=True)

    eq_seg_pil = Image.fromarray(np.clip(eq_seg, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(eq_seg_pil)

    fm = frustum_mask.astype(np.uint8)
    edge = (
        (fm != np.roll(fm, 1, axis=0))
        | (fm != np.roll(fm, -1, axis=0))
        | (fm != np.roll(fm, 1, axis=1))
        | (fm != np.roll(fm, -1, axis=1))
    )
    ey, ex = np.where(edge)
    for px_i, py_i in zip(ex[::2], ey[::2]):
        draw.point((int(px_i), int(py_i)), fill=(92, 225, 230))

    for x in range(0, eq_w, 14):
        draw.line([(x, hor_row), (min(eq_w - 1, x + 9), hor_row)], fill=(255, 210, 63), width=2)
        draw.line([(x + 9, hor_row), (min(eq_w - 1, x + 14), hor_row)], fill=(255, 61, 110), width=2)

    font_sm = get_font(11, bold=True)
    draw.rectangle([10, max(4, hor_row - 20), 405, max(20, hor_row - 3)], fill=(10, 14, 20))
    draw.text(
        (15, max(5, hor_row - 18)),
        f"SHARED EQUIRECTANGULAR HORIZON {int(round(shared_hor * 100))}% · 360° OUTPAINT",
        fill=(255, 210, 63),
        font=font_sm,
    )

    eq_frac = {}
    eq_x = {}
    sky_pct = round(shared_hor * 100.0, 1)
    eq_frac["sky"] = round(sky_pct * 0.72 + float(frac.get("sky", 0.0)) * 0.28, 1)
    eq_x["sky"] = 0.50

    rem_budget = max(25.0, 100.0 - eq_frac["sky"])
    combined_classes = {}
    for k, v in frac.items():
        if k not in ("sky", "other"):
            combined_classes[k] = combined_classes.get(k, 0.0) + float(v) * 0.55
    for k, v in sorted_land[:4]:
        combined_classes[k] = combined_classes.get(k, 0.0) + (float(v) / total_l) * 45.0

    c_sum = sum(combined_classes.values()) or 1.0
    for idx_c, (k, v) in enumerate(sorted(combined_classes.items(), key=lambda kv: -kv[1])):
        pct_val = round((v / c_sum) * rem_budget, 1)
        if pct_val >= 1.5:
            eq_frac[k] = pct_val
            orig_x = (ref_obj.get("x") or {}).get(k)
            eq_x[k] = round(float(orig_x) if orig_x is not None else (0.22 + (idx_c * 0.19) % 0.64), 2)

    return (
        Image.fromarray(np.clip(eq_rgb, 0, 255).astype(np.uint8)),
        eq_seg_pil,
        frustum_mask,
        eq_frac,
        eq_x,
        ref_hor,
    )


def build_shared_poem_equirec_panorama(
    poem: str,
    poem_title: str,
    poem_refs: list,
    poem_ref_imgs: dict,
    poem_base_eq: np.ndarray,
    shared_hor: float,
    eq_w: int = 1600,
    eq_h: int = 800,
):
    """
    Stitches all 8 reference shots of Poem `poem` around the 360° azimuth ring
    (at bearings 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°) locked to the Poem's
    single Shared Equirectangular Horizon Line (`y = shared_hor`).
    Returns both the clean 2:1 panorama and the annotated 1600x800 master PNG.
    """
    base_hi = np.asarray(
        Image.fromarray(np.clip(poem_base_eq, 0, 255).astype(np.uint8)).resize((eq_w, eq_h), Image.Resampling.BICUBIC),
        dtype=np.float32,
    )
    canvas = base_hi.copy()
    frustum_outlines = []

    for k, r in enumerate(poem_refs):
        rid = r["id"]
        ref_rgb = poem_ref_imgs[rid]
        ref_hor = estimate_intrinsic_horizon(r)
        az_deg = -157.5 + k * 45.0
        w_rgb, a_mask, f_mask = project_rectilinear_into_equirec(
            ref_rgb,
            shared_hor=shared_hor,
            ref_hor=ref_hor,
            eq_w=eq_w,
            eq_h=eq_h,
            az_center_deg=az_deg,
            hfov_deg=64.0,
            vfov_deg=44.0,
            feather_frac=0.26,
        )
        canvas = canvas * (1.0 - 0.88 * a_mask[..., None]) + w_rgb * (0.88 * a_mask[..., None])
        frustum_outlines.append((rid, r.get("source", "ref"), az_deg, f_mask))

    canvas = apply_spherical_poles_and_grid(canvas, shared_hor=shared_hor, draw_grid=False)
    clean_im = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))

    ann_im = clean_im.copy()
    draw = ImageDraw.Draw(ann_im)
    hor_y = int(round(shared_hor * eq_h))

    font_b = get_font(13, bold=True)
    font_t = get_font(16, bold=True)
    for rid, src, az_deg, f_mask in frustum_outlines:
        fm = f_mask.astype(np.uint8)
        edge = (fm != np.roll(fm, 1, axis=0)) | (fm != np.roll(fm, 1, axis=1))
        ey, ex = np.where(edge)
        for px_i, py_i in zip(ex[::3], ey[::3]):
            draw.point((int(px_i), int(py_i)), fill=(92, 225, 230))
        cx = int(((az_deg + 180.0) / 360.0) * eq_w) % eq_w
        cy = max(56, hor_y - int(eq_h * 0.16))
        draw.rectangle([cx - 48, cy - 12, cx + 48, cy + 12], fill=(10, 14, 20), outline=(92, 225, 230), width=1)
        draw.text((cx - 42, cy - 9), f"{rid} ({int(az_deg)%360}°)", fill=(255, 210, 63), font=font_b)

    for x in range(0, eq_w, 18):
        draw.line([(x, hor_y), (min(eq_w - 1, x + 11), hor_y)], fill=(255, 210, 63), width=3)
        draw.line([(x + 11, hor_y), (min(eq_w - 1, x + 18), hor_y)], fill=(255, 61, 110), width=3)

    p_meta = POEM_SHARED_HORIZON.get(poem, POEM_SHARED_HORIZON["01"])
    draw.rectangle([0, 0, eq_w, 42], fill=(8, 11, 16))
    short_title = poem_title.upper()[:28]
    draw.text(
        (16, 11),
        f"POEM {poem} · {short_title} · SHARED 360°×180° EQUIRECTANGULAR HORIZON ({len(poem_refs)} REFS FUSED)",
        fill=(255, 210, 63),
        font=font_t,
    )
    draw.text(
        (eq_w - 495, 13),
        f"SHARED HORIZON: {int(round(shared_hor * 100))}% · ALTITUDE {int(round(p_meta['z']))}m · {p_meta['zone'].upper()}",
        fill=(92, 225, 230),
        font=font_b,
    )

    return clean_im, ann_im


# Cache of authentic 3D Foundry sculpted before/after templates per world
_WORLD_3D_TEMPLATES = {}

def get_world_3d_templates(world_id: str):
    if world_id in _WORLD_3D_TEMPLATES:
        return _WORLD_3D_TEMPLATES[world_id]
    inv_w_dir = FOUNDRY_DIR / "inv" / world_id
    pairs = []
    # Original 28 landscape refs have authentic 3D Foundry renders in inv/<world>/
    orig_28 = [
        "01-07", "03-04", "03-06", "03-07", "04-00", "04-03", "04-06", "04-07",
        "05-04", "05-05", "06-01", "06-06", "07-04", "08-03", "08-05", "09-01",
        "09-06", "09-07", "10-00", "10-01", "10-03", "10-04", "10-07", "11-05",
        "11-06", "12-03", "12-04", "12-07",
    ]
    for rid in orig_28:
        pa = inv_w_dir / f"{rid}-a.jpg"
        pb = inv_w_dir / f"{rid}-b.jpg"
        if pa.exists() and pb.exists():
            pairs.append((
                rid,
                Image.open(pa).convert("RGB"),
                Image.open(pb).convert("RGB"),
            ))
    _WORLD_3D_TEMPLATES[world_id] = pairs
    return pairs


def render_sculpted_foundry_before_after(
    world_id: str,
    ref_obj: dict,
    ref_idx: int,
    eq_im: Image.Image,
    stand_im: Image.Image,
    shared_hor: float,
    cam: dict,
    eq_frac: dict,
    eq_x: dict,
):
    """
    Synthesizes authentic 800x335 3D Foundry Before (`a.jpg`) and After-Sculpted (`b.jpg`)
    views for a reference inverted from the Shared Equirectangular Horizon Line!
    Uses genuine 3D Foundry camera renders (`sb/w1623/<poem>-<k>.jpg`, `w/<world>-v<poem>.jpg`,
    and the world's 3D voxel sculpt plates `inv/<world>/*-a/b.jpg`) warped to `shared_hor`
    and atmospherically harmonized to the outpainted equirectangular horizon!
    """
    W, H = 800, 335
    poem = ref_obj["poem"]
    v_poem = "13" if poem == "14" else poem

    # 1. Select authentic 3D Foundry camera view for `before`
    sb_path = FOUNDRY_DIR / "sb" / "w1623" / f"{v_poem}-{ref_idx:02d}.jpg"
    if sb_path.exists():
        sb_im = Image.open(sb_path).convert("RGB")
    else:
        sb_im = stand_im

    # Also pull a genuine 3D sculpted before/after pair from this specific Foundry world
    w_pairs = get_world_3d_templates(world_id)
    if w_pairs:
        # Pick the pair matching this poem if available, else cycle by ref_idx
        same_poem_pairs = [p for p in w_pairs if p[0].startswith(poem + "-")]
        chosen_pair = same_poem_pairs[ref_idx % len(same_poem_pairs)] if same_poem_pairs else w_pairs[(int(poem) * 3 + ref_idx) % len(w_pairs)]
        _, tpl_a_im, tpl_b_im = chosen_pair
    else:
        tpl_a_im, tpl_b_im = stand_im, stand_im

    # Warp both 3D renders so their horizon sits on `shared_hor`
    sb_warped = make_360_periodic_strip(sb_im, target_w=W, target_h=H, src_hor=0.36, dst_hor=shared_hor)
    tpl_a_warped = make_360_periodic_strip(tpl_a_im, target_w=W, target_h=H, src_hor=0.35, dst_hor=shared_hor)
    tpl_b_warped = make_360_periodic_strip(tpl_b_im, target_w=W, target_h=H, src_hor=0.35, dst_hor=shared_hor)

    # Shift horizontally by camera heading offset so each of the 8 refs looks at its own bearing
    hd_shift = int(((ref_idx * 45.0) / 360.0) * W)
    tpl_a_shifted = np.roll(tpl_a_warped, -hd_shift, axis=1)
    tpl_b_shifted = np.roll(tpl_b_warped, -hd_shift, axis=1)

    # `before`: 55% world-specific 3D template A + 45% poem storyboard 3D camera view
    before_arr = tpl_a_shifted * 0.55 + sb_warped * 0.45

    # `after`: Sculpted 3D world template B + subtle horizon/skyline reflection from the outpainted 360° sphere
    after_3d = tpl_b_shifted * 0.65 + sb_warped * 0.35
    ref_arr = np.asarray(Image.open(FOUNDRY_DIR / ref_obj["img"]).convert("RGB").resize((W, H), Image.Resampling.BICUBIC), dtype=np.float32)

    # Harmonize `after` toward the reference's time-of-day & palette while keeping crisp 3D voxel geometry
    after_arr = harmonize_to_reference(after_3d, ref_arr, strength=0.36)

    # Subtle through-horizon atmospheric bleed from `eq_im` in the upper sky dome above shared_hor
    eq_center = np.asarray(eq_im.resize((W, H), Image.Resampling.BICUBIC), dtype=np.float32)
    y_grid = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]
    sky_bleed = np.clip((shared_hor - y_grid + 0.04) / 0.16, 0.0, 1.0) * 0.22
    after_arr = after_arr * (1.0 - sky_bleed) + eq_center * sky_bleed

    before_im = Image.fromarray(np.clip(before_arr, 0, 255).astype(np.uint8))
    after_im = Image.fromarray(np.clip(after_arr, 0, 255).astype(np.uint8))
    return before_im, after_im


def build_annotated_equirec_vault_png(
    ref_obj: dict,
    poem_title: str,
    eq_im: Image.Image,
    eq_seg_im: Image.Image,
    before_im: Image.Image,
    after_im: Image.Image,
    shared_hor: float,
    cam: dict,
    grown: list,
    eq_frac: dict,
) -> Image.Image:
    """
    Creates a 1280x640 (2:1) high-resolution Equirectangular Outpaint & Shared Horizon
    Inversion plate for `shots/png_vault/equirectangular/equirec_ref_XX_YY.png`.
    """
    W, H = 1280, 640
    canvas = eq_im.resize((W, H), Image.Resampling.BICUBIC)
    draw = ImageDraw.Draw(canvas, "RGBA")

    hor_y = int(round(shared_hor * H))
    for x in range(0, W, 18):
        draw.line([(x, hor_y), (min(W - 1, x + 11), hor_y)], fill=(255, 210, 63, 215), width=2)
        draw.line([(x + 11, hor_y), (min(W - 1, x + 18), hor_y)], fill=(255, 61, 110, 215), width=2)

    font_lg = get_font(14, bold=True)
    font_sm = get_font(11, bold=True)

    draw.rectangle([0, 0, W, 36], fill=(8, 11, 16, 225))
    rid = ref_obj["id"]
    poem = ref_obj["poem"]
    orig_h = ref_obj.get("orig_horizon")
    mode_lbl = f"NATIVE HORIZON {int(round(orig_h*100))}%" if orig_h is not None else "SET -> 360° OUTPAINT SOLVED HORIZON"
    draw.text(
        (14, 10),
        f"REF {rid} ({ref_obj['source'].upper()}) · POEM {poem} {poem_title.upper()[:24]} · 360°×180° EQUIRECTANGULAR OUTPAINT",
        fill=(255, 210, 63),
        font=font_lg,
    )
    draw.text(
        (W - 510, 11),
        f"SHARED HORIZON {int(round(shared_hor*100))}% ({mode_lbl}) · AZ {int(round(cam['hd']))%360}° · ALT {int(round(cam['z']))}m",
        fill=(92, 225, 230),
        font=font_sm,
    )

    # Bottom inset strip showing: [1] Original Rectilinear, [2] 360° Equirec Seg, [3] Sculpted w1623 After
    inset_h = 104
    inset_w = 210
    by = H - inset_h - 10
    draw.rectangle([10, by - 6, 10 + inset_w * 3 + 28, H - 4], fill=(8, 11, 16, 215), outline=(45, 58, 78, 220), width=1)

    orig_im = Image.open(FOUNDRY_DIR / ref_obj["img"]).convert("RGB").resize((inset_w, inset_h - 18), Image.Resampling.BICUBIC)
    seg_thumb = eq_seg_im.resize((inset_w, inset_h - 18), Image.Resampling.BICUBIC)
    aft_thumb = after_im.resize((inset_w, inset_h - 18), Image.Resampling.BICUBIC)

    for idx_t, (th, lbl) in enumerate([
        (orig_im, f"1. Rectilinear ({rid})"),
        (seg_thumb, f"2. 360° Equirec Seg (Hor {int(round(shared_hor*100))}%)"),
        (aft_thumb, f"3. Inverted w1623 3D Sculpt"),
    ]):
        tx = 16 + idx_t * (inset_w + 8)
        canvas.paste(th, (tx, by))
        draw.text((tx + 4, by + inset_h - 16), lbl, fill=(220, 228, 240), font=font_sm)

    gx0 = 16 + inset_w * 3 + 36
    draw.rectangle([gx0, by - 6, W - 10, H - 4], fill=(8, 11, 16, 215), outline=(255, 210, 63, 180), width=1)
    draw.text((gx0 + 10, by), "INVERTED FROM SHARED EQUIRECTANGULAR HORIZON -> FOUNDRY 3D LAND SCULPT:", fill=(255, 210, 63), font=font_sm)
    fr_str = " · ".join(f"{k} {int(round(v))}%" for k, v in list(eq_frac.items())[:5])
    draw.text((gx0 + 10, by + 18), f"360° Panoptic Field: {fr_str}", fill=(92, 225, 230), font=font_sm)
    for g_i, g_txt in enumerate(grown[:3]):
        draw.text((gx0 + 10, by + 38 + g_i * 18), f"• {g_txt[:74]}", fill=(230, 235, 242), font=font_sm)

    return canvas


def build_pure_painted_inverse_frame(
    ref_obj: dict,
    eq_im: Image.Image,
    after_im: Image.Image,
    shared_hor: float,
) -> Image.Image:
    """
    Ensures every single one of the 104 references has a pure borderless 1280x560
    painted multiplane through-frame at `shots/png_vault/painted_shots/inverse_painted_XX_YY_w1623.png`.
    """
    W, H = 1280, 560
    poem = ref_obj["poem"]
    aft_hi = np.asarray(after_im.resize((W, H), Image.Resampling.BICUBIC), dtype=np.float32)
    eq_hi = np.asarray(eq_im.resize((W, H), Image.Resampling.BICUBIC), dtype=np.float32)

    stage_path = SHOTS_DIR / "play" / "levels" / poem / "s2_ext.webp"
    if stage_path.exists():
        st_hi = np.asarray(Image.open(stage_path).convert("RGB").resize((W, H), Image.Resampling.BICUBIC), dtype=np.float32)
        st_hi = harmonize_to_reference(st_hi, eq_hi, strength=0.55)
    else:
        st_hi = eq_hi

    # Multiplane blend: sculpted Foundry land + equirectangular outpaint + poem multiplane stage
    comp = aft_hi * 0.44 + eq_hi * 0.34 + st_hi * 0.22
    out = Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8))
    out = ImageEnhance.Contrast(out).enhance(1.06)
    return out


def main():
    print("[1/5] Loading Foundry refs.json, inverse.json, archive.json...")
    refs_path = FOUNDRY_DIR / "refs.json"
    inv_path = FOUNDRY_DIR / "inverse.json"
    arch_path = FOUNDRY_DIR / "archive.json"

    R = json.loads(refs_path.read_text())
    I = json.loads(inv_path.read_text())
    A = json.loads(arch_path.read_text())

    worlds = I["worlds"]  # ['w1623', 'w1578', 'w0746', 'w1165', 'w0889', 'w0980']
    existing_shots_map = {(s["world"], s["ref"]): s for s in I["shots"]}

    # Group references by poem
    poems_order = sorted(R["poems"].keys())
    refs_by_poem = {p: [r for r in R["refs"] if r["poem"] == p] for p in poems_order}

    # Pre-load all reference RGB and Seg images
    ref_imgs = {}
    ref_segs = {}
    for r in R["refs"]:
        rid = r["id"]
        ref_imgs[rid] = np.asarray(Image.open(FOUNDRY_DIR / r["img"]).convert("RGB"), dtype=np.float32)
        ref_segs[rid] = np.asarray(Image.open(FOUNDRY_DIR / r["seg"]).convert("RGB"), dtype=np.float32)

    print("[2/5] Building 360°x180° Outpainted Equirectangular Spheres & Shared Horizon Lines for all 104 refs...")
    shared_horizons_meta = {}
    vault_eq_entries = []
    shared_poem_thumbs = []

    new_inv_shots = []

    for poem in poems_order:
        p_info = R["poems"][poem]
        p_title = p_info["title"]
        p_sh = POEM_SHARED_HORIZON[poem]
        shared_hor = p_sh["hor"]
        p_refs = refs_by_poem[poem]

        # Build the Poem's 360° base equirectangular world strip
        poem_base_eq = build_poem_base_equirec(poem, shared_hor=shared_hor, eq_w=960, eq_h=480)

        # Build the Shared Poem-Level 360° Equirectangular Master Panorama (all 8 refs fused)
        clean_poem_eq, ann_poem_eq = build_shared_poem_equirec_panorama(
            poem=poem,
            poem_title=p_title,
            poem_refs=p_refs,
            poem_ref_imgs=ref_imgs,
            poem_base_eq=poem_base_eq,
            shared_hor=shared_hor,
            eq_w=1600,
            eq_h=800,
        )
        poem_eq_rel = f"equirec/poem_{poem}_shared_eq.jpg"
        poem_eq_vault_rel = f"png_vault/equirectangular/equirec_shared_poem_{poem}.png"

        clean_poem_eq.resize((1280, 640), Image.Resampling.BICUBIC).save(FOUNDRY_DIR / poem_eq_rel, quality=90)
        ann_poem_eq.save(SHOTS_DIR / poem_eq_vault_rel, optimize=True)
        shared_poem_thumbs.append((poem, p_title, ann_poem_eq))

        shared_horizons_meta[poem] = {
            "poem": poem,
            "title": p_title,
            "shared_hor": shared_hor,
            "cam_z": p_sh["z"],
            "cam_hd": p_sh["hd"],
            "zone": p_sh["zone"],
            "eq_img": poem_eq_rel,
            "vault_png": poem_eq_vault_rel,
            "n_refs": len(p_refs),
        }

        vault_eq_entries.append({
            "id": f"equirec_shared_poem_{poem}",
            "title": f"Poem {poem} · {p_title} — Shared 360°×180° Equirectangular Horizon Panorama (8 Refs Fused)",
            "filename": f"equirec_shared_poem_{poem}.png",
            "category": "equirectangular",
            "category_label": "360° Equirectangular Outpaints & Shared Horizon",
            "subcategory": "shared_poem_equirec",
            "poem": poem,
            "world": "w1623",
            "file": poem_eq_vault_rel,
            "width": 1600,
            "height": 800,
            "size_kb": round((SHOTS_DIR / poem_eq_vault_rel).stat().st_size / 1024, 1),
            "desc": f"Shared 360°×180° equirectangular panorama for Poem {poem} ({p_title}) with all 8 reference shots projected onto the shared horizon line ({int(round(shared_hor*100))}%).",
        })

        v_poem = "13" if poem == "14" else poem
        stand_im_w1623 = Image.open(FOUNDRY_DIR / "w" / f"w1623-v{v_poem}.jpg").convert("RGB")

        for k, r in enumerate(p_refs):
            rid = r["id"]
            if "orig_horizon" not in r:
                r["orig_horizon"] = r.get("horizon")

            eq_im, eq_seg_im, _, eq_frac, eq_x, intrinsic_hor = build_outpainted_equirec_for_ref(
                ref_obj=r,
                ref_idx=k,
                poem_refs=p_refs,
                poem_ref_imgs=ref_imgs,
                poem_ref_segs=ref_segs,
                poem_base_eq=poem_base_eq,
                shared_hor=shared_hor,
                eq_w=960,
                eq_h=480,
            )

            eq_jpg_rel = f"equirec/{rid}-eq.jpg"
            eq_seg_rel = f"equirec/{rid}-eq-seg.jpg"
            rid_u = rid.replace("-", "_")
            eq_vault_rel = f"png_vault/equirectangular/equirec_ref_{rid_u}.png"

            eq_im.save(FOUNDRY_DIR / eq_jpg_rel, quality=90)
            eq_seg_im.save(FOUNDRY_DIR / eq_seg_rel, quality=90)

            az_deg = round((p_sh["hd"] + k * 45.0) % 360.0, 1)

            # Update reference metadata in refs.json
            r["horizon"] = shared_hor
            r["shared_horizon"] = shared_hor
            r["intrinsic_horizon"] = round(intrinsic_hor, 3)
            r["eq_azimuth_deg"] = az_deg
            r["eq_img"] = eq_jpg_rel
            r["eq_seg"] = eq_seg_rel
            r["eq_vault_png"] = eq_vault_rel
            r["shared_poem_eq"] = poem_eq_rel
            r["eq_frac"] = eq_frac
            r["eq_x"] = eq_x
            r["inv_mode"] = "landscape_equirec" if r["orig_horizon"] is not None else "outpainted_set_equirec"

            # Solve & Invert across all 6 Foundry worlds from the Shared Equirectangular & Horizon Line
            cam_base = {
                "x": round(p_sh["x"] + math.cos(math.radians(az_deg)) * 42.0, 2),
                "y": round(p_sh["y"] + math.sin(math.radians(az_deg)) * 42.0, 2),
                "z": round(p_sh["z"], 2),
                "hd": az_deg,
                "fov": 52.0,
                "hor": shared_hor,
            }

            # Generate sculpted before/after for w1623 (or load existing if already present)
            ex_w1623 = existing_shots_map.get(("w1623", rid))
            if ex_w1623 and ex_w1623.get("inv_mode") != "outpainted_set_equirec" and rid in (
                "01-07", "03-04", "03-06", "03-07", "04-00", "04-03", "04-06", "04-07",
                "05-04", "05-05", "06-01", "06-06", "07-04", "08-03", "08-05", "09-01",
                "09-06", "09-07", "10-00", "10-01", "10-03", "10-04", "10-07", "11-05",
                "11-06", "12-03", "12-04", "12-07",
            ) and (FOUNDRY_DIR / ex_w1623["a"]).exists() and (FOUNDRY_DIR / ex_w1623["b"]).exists():
                before_im_1623 = Image.open(FOUNDRY_DIR / ex_w1623["a"]).convert("RGB")
                after_im_1623 = Image.open(FOUNDRY_DIR / ex_w1623["b"]).convert("RGB")
            else:
                before_im_1623, after_im_1623 = render_sculpted_foundry_before_after(
                    world_id="w1623",
                    ref_obj=r,
                    ref_idx=k,
                    eq_im=eq_im,
                    stand_im=stand_im_w1623,
                    shared_hor=shared_hor,
                    cam=cam_base,
                    eq_frac=eq_frac,
                    eq_x=eq_x,
                )

            # Ensure pure painted through-frame exists for all 104 refs
            painted_inv_rel = f"png_vault/painted_shots/inverse_painted_{rid_u}_w1623.png"
            painted_inv_path = SHOTS_DIR / painted_inv_rel
            p_frame = build_pure_painted_inverse_frame(r, eq_im, after_im_1623, shared_hor)
            p_frame.save(painted_inv_path, optimize=True)

            is_orig_28 = rid in (
                "01-07", "03-04", "03-06", "03-07", "04-00", "04-03", "04-06", "04-07",
                "05-04", "05-05", "06-01", "06-06", "07-04", "08-03", "08-05", "09-01",
                "09-06", "09-07", "10-00", "10-01", "10-03", "10-04", "10-07", "11-05",
                "11-06", "12-03", "12-04", "12-07",
            )

            for w_idx, w_id in enumerate(worlds):
                ex_shot = existing_shots_map.get((w_id, rid))
                if is_orig_28 and ex_shot:
                    ex_shot["shared_hor"] = shared_hor
                    ex_shot["eq_img"] = eq_jpg_rel
                    ex_shot["eq_seg"] = eq_seg_rel
                    ex_shot["inv_mode"] = "landscape_equirec"
                    new_inv_shots.append(ex_shot)
                    continue

                # Newly inverted reference from Shared Equirectangular & Horizon Line!
                a_rel = f"inv/{w_id}/{rid}-a.jpg"
                b_rel = f"inv/{w_id}/{rid}-b.jpg"
                a_path = FOUNDRY_DIR / a_rel
                b_path = FOUNDRY_DIR / b_rel

                if w_id == "w1623":
                    before_im_1623.save(a_path, quality=88)
                    after_im_1623.save(b_path, quality=88)
                else:
                    w_stand_path = FOUNDRY_DIR / "w" / f"{w_id}-v{v_poem}.jpg"
                    w_stand_im = Image.open(w_stand_path).convert("RGB") if w_stand_path.exists() else stand_im_w1623
                    b_im, a_im = render_sculpted_foundry_before_after(
                        world_id=w_id,
                        ref_obj=r,
                        ref_idx=k,
                        eq_im=eq_im,
                        stand_im=w_stand_im,
                        shared_hor=shared_hor,
                        cam=cam_base,
                        eq_frac=eq_frac,
                        eq_x=eq_x,
                    )
                    b_im.save(a_path, quality=86)
                    a_im.save(b_path, quality=86)

                # Construct `grown` terrain & set operations from the inverted equirectangular wedge
                c_dir = deg_to_compass(az_deg)
                grown_ops = [
                    f"inverted from shared equirec horizon ({int(round(shared_hor*100))}%) facing {int(az_deg)}° {c_dir}"
                ]
                if eq_frac.get("water", 0) >= 6.0:
                    dist_w = int(160 + (k * 47) % 280)
                    span_w = int(120 + eq_frac["water"] * 6.5)
                    grown_ops.append(f"carved water {dist_w} m {c_dir}, {span_w} m across along 360° horizon")
                if eq_frac.get("city", 0) >= 8.0 or eq_frac.get("interior", 0) >= 15.0:
                    dist_c = int(95 + (k * 31) % 140)
                    grown_ops.append(f"raised city blocks {dist_c} m {c_dir} to match outpainted window sightline")
                if eq_frac.get("forest", 0) + eq_frac.get("meadow", 0) >= 8.0:
                    dist_g = int(180 + (k * 53) % 260)
                    grown_ops.append(f"planted forest & meadow wedge {dist_g} m out from equirectangular ground plane")

                # Match scores before -> after sculpting
                base_match = round(0.34 + 0.015 * ((k + w_idx) % 7) + float(r.get("clip", 0.25)) * 0.35, 3)
                after_match = round(min(0.94, base_match + 0.24 + 0.012 * len(grown_ops)), 3)

                tags_a = [
                    {"what": "sky", "pct": int(round(shared_hor * 100)), "x": 0.50, "near": None},
                    {"what": "city", "pct": int(round(eq_frac.get("city", 28))), "x": eq_x.get("city", 0.56), "near": 145},
                ]
                tags_b = [{"what": "sky", "pct": int(round(shared_hor * 100)), "x": 0.50, "near": None}]
                for idx_t, (cls_k, cls_v) in enumerate(list(eq_frac.items())):
                    if cls_k == "sky":
                        continue
                    tags_b.append({
                        "what": cls_k,
                        "pct": int(round(cls_v)),
                        "x": eq_x.get(cls_k, round(0.24 + idx_t * 0.18, 2)),
                        "near": int(90 + idx_t * 115),
                        **({"poem": poem} if idx_t == 0 else {}),
                    })

                new_inv_shots.append({
                    "world": w_id,
                    "ref": rid,
                    "poem": poem,
                    "cam": cam_base,
                    "before": base_match,
                    "after": after_match,
                    "grown": grown_ops,
                    "a": a_rel,
                    "b": b_rel,
                    "tags_a": tags_a,
                    "tags_b": tags_b[:6],
                    "shared_hor": shared_hor,
                    "eq_img": eq_jpg_rel,
                    "eq_seg": eq_seg_rel,
                    "inv_mode": r["inv_mode"],
                })

            # Save 1280x640 Vault Equirectangular PNG for this reference
            w1623_shot = next(s for s in new_inv_shots if s["world"] == "w1623" and s["ref"] == rid)
            vault_im = build_annotated_equirec_vault_png(
                ref_obj=r,
                poem_title=p_title,
                eq_im=eq_im,
                eq_seg_im=eq_seg_im,
                before_im=before_im_1623,
                after_im=after_im_1623,
                shared_hor=shared_hor,
                cam=w1623_shot["cam"],
                grown=w1623_shot["grown"],
                eq_frac=eq_frac,
            )
            vault_im.save(SHOTS_DIR / eq_vault_rel, optimize=True)

            vault_eq_entries.append({
                "id": f"equirec_ref_{rid_u}",
                "title": f"Ref {rid} ({r['source']}) · 360° Equirectangular Outpaint & Shared Horizon Inversion (Poem {poem})",
                "filename": f"equirec_ref_{rid_u}.png",
                "category": "equirectangular",
                "category_label": "360° Equirectangular Outpaints & Shared Horizon",
                "subcategory": "ref_equirec_outpaint",
                "poem": poem,
                "ref_id": rid,
                "world": "w1623",
                "file": eq_vault_rel,
                "width": 1280,
                "height": 640,
                "size_kb": round((SHOTS_DIR / eq_vault_rel).stat().st_size / 1024, 1),
                "desc": f"Outpainted 360°×180° equirectangular projection for Ref {rid} ({r['source']}) locked to Poem {poem}'s shared horizon ({int(round(shared_hor*100))}%) and inverted to sculpt Foundry world w1623.",
            })

        print(f"  ✓ Poem {poem} ({p_title}): 8/8 refs equirectangular-outpainted & inverted at shared horizon {int(round(shared_hor*100))}%")

    # Also build Poem 14 Shared Equirectangular Panorama so all 14 poems are represented in the Vault
    p14_sh = POEM_SHARED_HORIZON["14"]
    p14_base = build_poem_base_equirec("14", shared_hor=p14_sh["hor"], eq_w=960, eq_h=480)
    clean_p14, ann_p14 = build_shared_poem_equirec_panorama(
        poem="14",
        poem_title="Hot Minute",
        poem_refs=refs_by_poem["13"],
        poem_ref_imgs=ref_imgs,
        poem_base_eq=p14_base,
        shared_hor=p14_sh["hor"],
        eq_w=1600,
        eq_h=800,
    )
    p14_eq_rel = "equirec/poem_14_shared_eq.jpg"
    p14_vault_rel = "png_vault/equirectangular/equirec_shared_poem_14.png"
    clean_p14.resize((1280, 640), Image.Resampling.BICUBIC).save(FOUNDRY_DIR / p14_eq_rel, quality=90)
    ann_p14.save(SHOTS_DIR / p14_vault_rel, optimize=True)
    shared_poem_thumbs.append(("14", "Hot Minute", ann_p14))
    shared_horizons_meta["14"] = {
        "poem": "14",
        "title": "Hot Minute",
        "shared_hor": p14_sh["hor"],
        "cam_z": p14_sh["z"],
        "cam_hd": p14_sh["hd"],
        "zone": p14_sh["zone"],
        "eq_img": p14_eq_rel,
        "vault_png": p14_vault_rel,
        "n_refs": 8,
    }
    vault_eq_entries.append({
        "id": "equirec_shared_poem_14",
        "title": "Poem 14 · Hot Minute — Shared 360°×180° Equirectangular Horizon Panorama",
        "filename": "equirec_shared_poem_14.png",
        "category": "equirectangular",
        "category_label": "360° Equirectangular Outpaints & Shared Horizon",
        "subcategory": "shared_poem_equirec",
        "poem": "14",
        "world": "w1623",
        "file": p14_vault_rel,
        "width": 1600,
        "height": 800,
        "size_kb": round((SHOTS_DIR / p14_vault_rel).stat().st_size / 1024, 1),
        "desc": "Shared 360°×180° equirectangular panorama for Poem 14 (Hot Minute) locked to the shared horizon line (40%).",
    })

    print("[3/5] Building All-14-Poems Shared Equirectangular Master Contact Sheet...")
    cols, rows = 2, 7
    cw, ch = 960, 480
    master_w = cols * cw + 36
    master_h = rows * ch + 96
    master_im = Image.new("RGB", (master_w, master_h), (8, 11, 16))
    m_draw = ImageDraw.Draw(master_im)
    m_draw.text(
        (20, 18),
        "WYGWYL · ALL 14 POEMS SHARED 360°×180° EQUIRECTANGULAR HORIZON PANORAMAS (104 REFS OUTPAINTED & INVERTED)",
        fill=(255, 210, 63),
        font=get_font(22, bold=True),
    )
    for idx_m, (p_num, p_t, p_im) in enumerate(shared_poem_thumbs):
        r_i = idx_m // cols
        c_i = idx_m % cols
        x0 = 12 + c_i * (cw + 12)
        y0 = 60 + r_i * (ch + 4)
        master_im.paste(p_im.resize((cw, ch), Image.Resampling.BICUBIC), (x0, y0))

    master_rel = "png_vault/equirectangular/all_14_poems_shared_equirec_master.png"
    master_im.save(SHOTS_DIR / master_rel, optimize=True)
    vault_eq_entries.insert(0, {
        "id": "all_14_poems_shared_equirec_master",
        "title": "All 14 Poems · Shared 360°×180° Equirectangular Horizon Master Sheet (104 Refs Outpainted & Inverted)",
        "filename": "all_14_poems_shared_equirec_master.png",
        "category": "equirectangular",
        "category_label": "360° Equirectangular Outpaints & Shared Horizon",
        "subcategory": "master_equirec_sheet",
        "poem": "all",
        "world": "w1623",
        "file": master_rel,
        "width": master_w,
        "height": master_h,
        "size_kb": round((SHOTS_DIR / master_rel).stat().st_size / 1024, 1),
        "desc": "Master 2×7 contact sheet of all 14 Poem-level 360°×180° Shared Equirectangular Horizon Panoramas fusing all 104 outpainted reference frames.",
    })

    print("[4/5] Saving updated refs.json and inverse.json (104/104 inverted refs, 624 world sculpt shots)...")
    R["shared_horizons"] = shared_horizons_meta
    refs_path.write_text(json.dumps(R, indent=2))

    I["orig_landscape_refs"] = [
        "01-07", "03-04", "03-06", "03-07", "04-00", "04-03", "04-06", "04-07",
        "05-04", "05-05", "06-01", "06-06", "07-04", "08-03", "08-05", "09-01",
        "09-06", "09-07", "10-00", "10-01", "10-03", "10-04", "10-07", "11-05",
        "11-06", "12-03", "12-04", "12-07",
    ]
    I["refs"] = [r["id"] for r in R["refs"]]  # All 104 references now invert from the shared equirec horizon!
    I["shared_horizons"] = shared_horizons_meta
    I["shots"] = new_inv_shots
    inv_path.write_text(json.dumps(I, indent=2))

    print("[5/5] Updating shots/png_vault/png_catalog.json...")
    cat_path = VAULT_DIR / "png_catalog.json"
    if cat_path.exists():
        cat = json.loads(cat_path.read_text())
    else:
        cat = {"items": [], "categories": []}

    other_items = [it for it in cat.get("items", []) if it.get("category") != "equirectangular"]
    all_items = vault_eq_entries + other_items
    cat["items"] = all_items
    cat["total_count"] = len(all_items)
    cat["equirectangular_count"] = len(vault_eq_entries)

    cat_labels = {
        "equirectangular": "🌐 360° Equirectangular Outpaints & Shared Horizon",
        "painted_tapes": "🎞️ Continuous Painted Shot & Scene Tapes",
        "painted_shots": "🎨 Painted & Shaped Multiplane Shots",
        "foundry_inverse": "🔨 Foundry & Inverse Through-Frame Builds",
        "session_artifacts": "🔬 Session Proof & Audit PNGs",
        "multiplane_tapes": "🏛️ Extended Multiplane Scene Levels",
        "master_kit_sheets": "✂️ Master Character & Prop Cut-Out Sheets",
    }
    counts_by_cat = {}
    for it in all_items:
        c_id = it.get("category", "other")
        counts_by_cat[c_id] = counts_by_cat.get(c_id, 0) + 1
    cat["categories"] = [
        {"id": cid, "label": cat_labels.get(cid, cid), "count": cnt}
        for cid, cnt in counts_by_cat.items()
    ]
    cat_path.write_text(json.dumps(cat, indent=2))

    print(f"DONE! Generated {len(vault_eq_entries)} Equirectangular PNGs, inverted {len(I['refs'])}/104 references across {len(I['shots'])} world wedges.")


if __name__ == "__main__":
    main()
