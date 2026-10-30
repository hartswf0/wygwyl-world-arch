#!/usr/bin/env python3
"""
build_onion_depth_planes.py
===========================
1. Generates Rectilinear Depth Masks (`foundry/refs/XX-YY-depth.jpg`) for all 104 reference shots.
2. Generates 360°x180° (2:1) Equirectangular Depth Masks (`foundry/equirec/XX-YY-eq-depth.jpg`)
   for all 104 references and 14 Shared Poem Equirectangular Depth Panoramas
   (`foundry/equirec/poem_XX_shared_depth.jpg`), locked to each poem's Shared Equirectangular Horizon Line.
3. Organizes every shot's image layers and WYGWYL cut-out kit items into 6 Concentric Onion Depth Shells
   (`R0` Core Veil -> `R1` Inner Actor Ring -> `R2` Midground Set/Props -> `R3` Architectural Room/Aperture
   -> `R4` Foundry 3D Topography Sculpt -> `R5` Outer 360° Sky Dome) and saves `foundry/onion_planes.json`.
4. Renders 119 high-resolution Onion Depth & 6-Shell Peel PNG plates into `shots/png_vault/onion_depth/`:
   - 104 Per-Reference Onion Depth & 6-Shell Peel Plates (`onion_depth_ref_XX_YY.png`, 1440x820)
   - 14 Shared Poem 360° Equirectangular Onion Depth Panoramas (`onion_shared_poem_01.png..14.png`, 1600x900)
   - 1 All-14-Poems Master Onion Depth Contact Sheet (`all_14_poems_onion_depth_master.png`)
5. Updates `refs.json`, `inverse.json`, and `shots/png_vault/png_catalog.json`.
"""

import json
import math
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch")
SHOTS_DIR = ROOT / "shots"
FOUNDRY_DIR = SHOTS_DIR / "data" / "terrarium" / "foundry"
REFS_DIR = FOUNDRY_DIR / "refs"
EQUIREC_DIR = FOUNDRY_DIR / "equirec"
VAULT_DIR = SHOTS_DIR / "png_vault"
VAULT_ONION_DIR = VAULT_DIR / "onion_depth"

EQUIREC_DIR.mkdir(parents=True, exist_ok=True)
VAULT_ONION_DIR.mkdir(parents=True, exist_ok=True)

# The 6 Concentric Onion Depth Shells (from camera center R0 outward to sky dome R5)
ONION_SHELLS = [
    {
        "idx": 0,
        "id": "R0",
        "name": "R0 · Core Veil & Foreground FX",
        "short": "R0 Core FX",
        "d_min": 0.00,
        "d_max": 0.16,
        "radius_m": 1.2,
        "color": (255, 61, 110),      # #ff3d6e Hot Pink
        "hex": "#ff3d6e",
        "role": "Close lens veil, smoke/embers, handheld props & foreground silhouette edge",
    },
    {
        "idx": 1,
        "id": "R1",
        "name": "R1 · Inner Actor Ring",
        "short": "R1 Actors",
        "d_min": 0.16,
        "d_max": 0.32,
        "radius_m": 3.2,
        "color": (255, 159, 28),      # #ff9f1c Warm Amber
        "hex": "#ff9f1c",
        "role": "Hero & supporting cut-out cast (Poet, EX, Woman/Muse, Child) & foreground figures",
    },
    {
        "idx": 2,
        "id": "R2",
        "name": "R2 · Midground Set & Props Ring",
        "short": "R2 Set & Props",
        "d_min": 0.32,
        "d_max": 0.48,
        "radius_m": 7.5,
        "color": (255, 210, 63),      # #ffd23f Gold
        "hex": "#ffd23f",
        "role": "Grounded furniture, streetlamps, vehicles, DJ booth, tables & near-ground floor",
    },
    {
        "idx": 3,
        "id": "R3",
        "name": "R3 · Architectural Aperture Ring",
        "short": "R3 Arch Aperture",
        "d_min": 0.48,
        "d_max": 0.66,
        "radius_m": 18.0,
        "color": (143, 214, 148),     # #8fd694 Emerald
        "hex": "#8fd694",
        "role": "Room walls, window mullions, brick alleys & viaduct arches with depth-punched portals",
    },
    {
        "idx": 4,
        "id": "R4",
        "name": "R4 · Foundry 3D Land & City Ring",
        "short": "R4 Foundry Land",
        "d_min": 0.66,
        "d_max": 0.84,
        "radius_m": 95.0,
        "color": (92, 225, 230),      # #5ce1e6 Cyan
        "hex": "#5ce1e6",
        "role": "Inverse-sculpted 3D Foundry voxel cityscape, harbor water, ridges & forest horizon",
    },
    {
        "idx": 5,
        "id": "R5",
        "name": "R5 · Outer 360° Horizon Sky Dome",
        "short": "R5 Sky Dome",
        "d_min": 0.84,
        "d_max": 1.00,
        "radius_m": 800.0,
        "color": (123, 97, 255),      # #7b61ff Violet-Indigo
        "hex": "#7b61ff",
        "role": "360°×180° Atlantis gouache sky dome, moon/sun & shared equirectangular horizon glow",
    },
]

# Class depth priors in [0, 1] (0 = near camera, 1 = far sky dome)
CLASS_DEPTH_PRIORS = {
    "person":   0.22,
    "interior": 0.54,
    "street":   0.46,
    "beach":    0.58,
    "rock":     0.62,
    "meadow":   0.68,
    "field":    0.70,
    "forest":   0.73,
    "city":     0.75,
    "water":    0.79,
    "sky":      0.95,
    "other":    0.52,
}

# Canonical Kit Cast & Props per Poem to populate the Concentric Onion Shells
DEFAULT_CAST_BY_POEM = {
    "01": [
        {"name": "Poet (Black Tee)", "shell": 1, "d": 0.22, "file": "weave/cast/man/library/misc/body_front_08.png", "kind": "actor"},
        {"name": "EX (Olive Bomber Back)", "shell": 1, "d": 0.27, "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.master/ex.ex_jacket.master__p30.png", "kind": "actor"},
        {"name": "Sash Window Frame", "shell": 3, "d": 0.55, "file": "arena/parts/kit3/release_v2/cuts/01.props.window/01.props.window__p01.png", "kind": "arch"},
    ],
    "02": [
        {"name": "Poet Walking", "shell": 1, "d": 0.23, "file": "weave/cast/man/library/misc/body_front_09.png", "kind": "actor"},
        {"name": "EX Turning Back", "shell": 1, "d": 0.28, "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.master/ex.ex_jacket.master__p30.png", "kind": "actor"},
        {"name": "Streetlight & Neon", "shell": 2, "d": 0.40, "file": "arena/parts/kit3/release_v2/cuts/01.props.window/01.props.window__p01.png", "kind": "prop"},
    ],
}


def get_font(size=12, bold=False):
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


def colorize_onion_depth(depth: np.ndarray, draw_contours: bool = True, shared_hor: float = None) -> np.ndarray:
    """
    Maps a normalized depth array `depth` in [0, 1] (H, W) into an RGB image (H, W, 3) uint8
    using a continuous 6-shell Onion Depth Colormap (Hot Pink R0 -> Amber R1 -> Gold R2 ->
    Emerald R3 -> Cyan R4 -> Deep Indigo-Violet R5) with crisp onion-shell boundary contours!
    """
    d = np.clip(depth, 0.0, 1.0)
    H, W = d.shape

    # Control stops for smooth turbo/onion interpolation + shell tinting
    stops = np.array([0.00, 0.16, 0.32, 0.48, 0.66, 0.84, 1.00], dtype=np.float32)
    colors = np.array([
        [255, 42, 98],     # 0.00 R0 Core (Hot Magenta-Pink)
        [255, 138, 24],    # 0.16 R0/R1 boundary (Deep Amber)
        [255, 210, 63],    # 0.32 R1/R2 boundary (Bright Gold)
        [120, 218, 132],   # 0.48 R2/R3 boundary (Emerald Green)
        [68, 212, 232],    # 0.66 R3/R4 boundary (Electric Cyan)
        [88, 114, 245],    # 0.84 R4/R5 boundary (Royal Cobalt)
        [38, 22, 92],      # 1.00 R5 Far Sky Dome (Deep Cosmic Violet)
    ], dtype=np.float32)

    rgb = np.zeros((H, W, 3), dtype=np.float32)
    for c in range(3):
        rgb[:, :, c] = np.interp(d, stops, colors[:, c])

    # Add subtle quantized shell banding (22% blend with discrete shell color) so the 6 onion rings read clearly
    discrete = np.zeros_like(rgb)
    for sh in ONION_SHELLS:
        mask = (d >= sh["d_min"]) & (d <= (sh["d_max"] if sh["idx"] == 5 else sh["d_max"]))
        discrete[mask] = np.array(sh["color"], dtype=np.float32)
    rgb = rgb * 0.78 + discrete * 0.22

    if draw_contours:
        # Draw crisp iso-depth contour lines at each onion shell boundary
        for sh in ONION_SHELLS[:-1]:
            thresh = sh["d_max"]
            dist = np.abs(d - thresh)
            # Local gradient magnitude so contour is ~1.5px thick
            gy, gx = np.gradient(d)
            grad = np.hypot(gx, gy) + 1e-4
            px_dist = dist / np.maximum(grad, 0.003)
            contour_mask = (px_dist < 1.25).astype(np.float32)[:, :, None]
            c_col = np.array(sh["color"], dtype=np.float32) * 0.5 + 127.0
            rgb = rgb * (1.0 - contour_mask * 0.85) + c_col * (contour_mask * 0.85)

    if shared_hor is not None:
        hy = int(round(max(0.05, min(0.95, shared_hor)) * (H - 1)))
        for dy in (-1, 0, 1):
            ry = max(0, min(H - 1, hy + dy))
            if dy == 0:
                # Dashed gold/white horizon equator
                xs = np.arange(W)
                dash = ((xs // 10) % 2 == 0)[:, None]
                rgb[ry] = np.where(dash, np.array([255, 230, 90], dtype=np.float32), np.array([255, 61, 110], dtype=np.float32))
            else:
                rgb[ry] = rgb[ry] * 0.4

    return np.clip(rgb, 0, 255).astype(np.uint8)


def compute_rectilinear_depth_field(
    ref_img: Image.Image,
    seg_img: Image.Image,
    ref_obj: dict,
    shared_hor: float,
    target_w: int = 640,
    target_h: int = 268,
) -> np.ndarray:
    """
    Computes a continuous, edge-aware rectilinear depth map D(x, y) in [0, 1]
    (0 = closest R0 core, 1 = farthest R5 sky dome) from:
    1. The 5x12 panoptic grid & segmentation colors (`seg_img`),
    2. Spherical perspective floor/water ramp below `shared_hor`,
    3. Luminance/contrast structure cues from `ref_img` (dark foreground silhouettes pull into R1,
       bright window/sky apertures push out into R4/R5).
    """
    im_rgb = np.asarray(ref_img.convert("RGB").resize((target_w, target_h), Image.Resampling.BILINEAR), dtype=np.float32)
    im_seg = np.asarray(seg_img.convert("RGB").resize((target_w, target_h), Image.Resampling.BILINEAR), dtype=np.float32)

    # 1. Coarse 5x12 panoptic class depth grid upsampled smoothly
    grid = ref_obj.get("grid") or []
    if len(grid) == 5 and len(grid[0]) == 12:
        g_depth = np.zeros((5, 12), dtype=np.float32)
        for r in range(5):
            for c in range(12):
                cls_name = grid[r][c]
                g_depth[r, c] = CLASS_DEPTH_PRIORS.get(cls_name, 0.52)
        g_img = Image.fromarray(np.clip(g_depth * 255.0, 0, 255).astype(np.uint8)).resize(
            (target_w, target_h), Image.Resampling.BICUBIC
        )
        prior_d = np.asarray(g_img, dtype=np.float32) / 255.0
    else:
        prior_d = np.full((target_h, target_w), 0.55, dtype=np.float32)

    # 2. Geometric perspective ramp anchored at `shared_hor`
    y_norm = np.linspace(0.0, 1.0, target_h, dtype=np.float32)[:, None]
    hor = float(max(0.20, min(0.68, shared_hor)))
    above_t = np.clip(1.0 - (y_norm / max(0.05, hor)), 0.0, 1.0)
    below_t = np.clip(1.0 - (y_norm - hor) / max(0.05, 1.0 - hor), 0.0, 1.0)
    geo_d = np.where(
        y_norm <= hor,
        0.82 + 0.16 * above_t,
        0.10 + 0.72 * (below_t ** 1.15),
    )
    geo_d = np.broadcast_to(geo_d, (target_h, target_w))

    # 3. Photometric & segmentation cues from `im_rgb` and `im_seg`
    lum = (0.299 * im_rgb[:, :, 0] + 0.587 * im_rgb[:, :, 1] + 0.114 * im_rgb[:, :, 2]) / 255.0
    blue_ness = np.clip((im_rgb[:, :, 2] - im_rgb[:, :, 0] * 0.6) / 255.0, 0.0, 1.0)

    # Detect foreground dark silhouette / actor presence near center-bottom
    x_norm = np.linspace(-1.0, 1.0, target_w, dtype=np.float32)[None, :]
    center_weight = np.exp(-1.4 * (x_norm ** 2)) * np.clip((y_norm - 0.18) / 0.75, 0.0, 1.0)
    dark_fg = np.clip((0.36 - lum) / 0.36, 0.0, 1.0) * center_weight

    # Bright window aperture / sky opening in interior sets pushes through to R4/R5
    bright_aperture = np.clip((lum - 0.52) / 0.42, 0.0, 1.0) * np.clip(1.2 - y_norm * 0.9, 0.2, 1.0)

    # Combine prior + geometric + photometric cues
    raw_d = prior_d * 0.46 + geo_d * 0.38 + (0.28 + 0.55 * lum + 0.17 * blue_ness) * 0.16
    raw_d = raw_d * (1.0 - dark_fg * 0.68) + 0.20 * (dark_fg * 0.68)
    raw_d = raw_d * (1.0 - bright_aperture * 0.55) + 0.88 * (bright_aperture * 0.55)

    raw_d = np.nan_to_num(raw_d, nan=0.5, posinf=0.99, neginf=0.02)
    d_pil = Image.fromarray(np.clip(raw_d * 255.0, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=2.2))
    d_smooth = np.asarray(d_pil, dtype=np.float32) / 255.0
    final_d = d_smooth * 0.72 + raw_d * 0.28
    return np.clip(final_d, 0.02, 0.99)


def project_scalar_into_equirec(
    scalar_rect: np.ndarray,
    shared_hor: float,
    ref_hor: float,
    eq_w: int,
    eq_h: int,
    az_center_deg: float,
    hfov_deg: float = 76.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Projects a 2D rectilinear scalar map (such as a depth map `scalar_rect` in [0, 1])
    onto a 2:1 (360° x 180°) equirectangular sphere centered at `az_center_deg` with
    its horizon locked to `shared_hor`.
    Returns (projected_scalar, weight_mask).
    """
    src_h, src_w = scalar_rect.shape
    aspect = src_w / float(src_h)

    hfov = math.radians(hfov_deg)
    tan_half_w = math.tan(hfov * 0.5)
    tan_half_h = tan_half_w / aspect

    phi_hor = (0.5 - shared_hor) * math.pi
    vy_hor = (0.5 - ref_hor) * 2.0 * tan_half_h
    alpha_hor = math.atan(vy_hor)
    phi_0 = phi_hor - alpha_hor

    lon = (np.linspace(0.0, 1.0, eq_w, endpoint=False, dtype=np.float32) - 0.5) * (2.0 * math.pi)
    lat = (0.5 - np.linspace(0.0, 1.0, eq_h, endpoint=True, dtype=np.float32)) * math.pi

    lam_0 = math.radians(((az_center_deg + 180.0) % 360.0) - 180.0)
    dlam = (lon[None, :] - lam_0 + math.pi) % (2.0 * math.pi) - math.pi
    phi = lat[:, None]

    sin_p0 = math.sin(phi_0)
    cos_p0 = math.cos(phi_0)
    sin_p = np.sin(phi)
    cos_p = np.cos(phi)
    cos_dl = np.cos(dlam)
    sin_dl = np.sin(dlam)

    cos_c = sin_p0 * sin_p + cos_p0 * cos_p * cos_dl
    valid = cos_c > 0.08
    safe_cos_c = np.where(valid, cos_c, 1.0)

    vx = (cos_p * sin_dl) / safe_cos_c
    vy = (cos_p0 * sin_p - sin_p0 * cos_p * cos_dl) / safe_cos_c

    nx = vx / tan_half_w
    ny = -vy / tan_half_h

    in_frustum = valid & (np.abs(nx) <= 1.0) & (np.abs(ny) <= 1.0)

    u = np.clip((nx + 1.0) * 0.5 * (src_w - 1), 0.0, src_w - 1.001)
    v = np.clip((ny + 1.0) * 0.5 * (src_h - 1), 0.0, src_h - 1.001)

    u0 = np.floor(u).astype(np.int32)
    v0 = np.floor(v).astype(np.int32)
    u1 = np.minimum(src_w - 1, u0 + 1)
    v1 = np.minimum(src_h - 1, v0 + 1)

    wu = u - u0
    wv = v - v0

    sampled = (
        scalar_rect[v0, u0] * (1.0 - wu) * (1.0 - wv)
        + scalar_rect[v0, u1] * wu * (1.0 - wv)
        + scalar_rect[v1, u0] * (1.0 - wu) * wv
        + scalar_rect[v1, u1] * wu * wv
    )

    wx = np.clip((1.0 - np.abs(nx)) / 0.28, 0.0, 1.0)
    wy = np.clip((1.0 - np.abs(ny)) / 0.28, 0.0, 1.0)
    wx = 0.5 - 0.5 * np.cos(np.pi * wx)
    wy = 0.5 - 0.5 * np.cos(np.pi * wy)
    weight = np.where(in_frustum, wx * wy, 0.0).astype(np.float32)

    return sampled.astype(np.float32), weight


def build_base_equirec_depth(poem: str, shared_hor: float, eq_w: int, eq_h: int, eq_rgb: np.ndarray) -> np.ndarray:
    """
    Constructs the base 360°x180° spherical depth field D_base(lambda, phi) in [0, 1]
    from the spherical geometry around `shared_hor` AND the 3D urban/topographic structure
    present in the 360° outpainted panorama `eq_rgb`.
    """
    y_norm = np.linspace(0.0, 1.0, eq_h, dtype=np.float32)[:, None]
    hor = float(max(0.22, min(0.65, shared_hor)))

    above_t = np.clip(1.0 - y_norm / max(0.05, hor), 0.0, 1.0)
    below_t = np.clip(1.0 - (y_norm - hor) / max(0.05, 1.0 - hor), 0.0, 1.0)

    # 1. Spherical floor & sky dome elevation depth profile
    sph_d = np.where(
        y_norm <= hor,
        0.84 + 0.15 * (above_t ** 0.85),
        0.05 + 0.77 * (below_t ** 1.15),
    )
    sph_d = np.broadcast_to(sph_d, (eq_h, eq_w)).copy()

    # 2. Extract 3D urban blocks, towers, water channels & foreground structures from `eq_rgb`
    lum = (0.299 * eq_rgb[:, :, 0] + 0.587 * eq_rgb[:, :, 1] + 0.114 * eq_rgb[:, :, 2]) / 255.0
    # Smooth structural luminance + local vertical relief
    lum_pil = Image.fromarray(np.clip(lum * 255.0, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=3.5))
    lum_s = np.asarray(lum_pil, dtype=np.float32) / 255.0

    lon = np.linspace(0.0, 2.0 * math.pi, eq_w, endpoint=False, dtype=np.float32)[None, :]
    p_seed = int(poem) * 1.37
    skyline_h = 0.075 + 0.038 * np.sin(lon * 3.0 + p_seed) + 0.028 * np.cos(lon * 7.0 - p_seed * 1.7)
    in_skyline_band = (y_norm >= (hor - skyline_h)) & (y_norm <= (hor + 0.12))
    building_weight = np.where(in_skyline_band, np.clip((0.62 - lum_s) / 0.45, 0.15, 0.92), 0.0)
    sph_d = sph_d * (1.0 - building_weight * 0.75) + 0.72 * (building_weight * 0.75)

    # Below the horizon, modulate ground/city depth by structural blocks, alleys, and azimuthal perspective waves
    below_mask = np.clip((y_norm - hor) / max(0.05, 1.0 - hor), 0.0, 1.0)
    az_wave = (
        0.055 * np.sin(lon * 4.0 + p_seed * 0.8)
        + 0.040 * np.cos(lon * 9.0 - p_seed * 1.3)
        + (lum_s - 0.35) * 0.22
    ) * (below_mask * (1.0 - below_mask * 0.45))
    sph_d = sph_d + az_wave

    return np.clip(sph_d, 0.03, 0.99)


def stamp_kit_items_into_onion_shells(
    poem: str,
    ref_id: str,
    az_center_deg: float,
    shared_hor: float,
    scene_items_by_poem: dict,
    eq_depth: np.ndarray = None,
    kit_img_cache: dict = None,
) -> list[dict]:
    """
    Assigns every staged cut-out item and structural layer of `ref_id` to one of the
    6 Concentric Onion Depth Shells (R0..R5) with exact spherical coordinates, and
    stamps their silhouettes directly into `eq_depth` so the equirectangular depth mask
    carries the exact onion-shell depth footprints of the actors and props!
    """
    raw_items = scene_items_by_poem.get(poem) or DEFAULT_CAST_BY_POEM.get(poem, DEFAULT_CAST_BY_POEM["01"])
    actors = [it for it in raw_items if it.get("kind") == "actor"]
    props = [it for it in raw_items if it.get("kind") == "prop"]
    archs = [it for it in raw_items if it.get("kind") == "arch"]

    if not actors:
        actors = [
            {"name": "Poet (Tracksuit / Black Tee)", "file": "weave/cast/man/library/misc/body_front_08.png", "kind": "actor"},
            {"name": "EX (Olive Bomber Back)", "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.master/ex.ex_jacket.master__p30.png", "kind": "actor"},
        ]
    elif len(actors) == 1:
        actors.append({"name": "Supporting Figure", "file": "weave/cast/man/library/misc/body_front_09.png", "kind": "actor"})

    fg_file = "weave/cast/man/library/misc/body_sitting_04.png"
    prop_item = props[0] if props else (archs[0] if archs else {"name": "Midground Set Furnishing", "file": "weave/cast/man/library/misc/body_sitting_01.png"})
    arch_item = archs[-1] if archs else {"name": "Sash Window Portal Frame", "file": "arena/parts/kit3/release_v2/cuts/01.props.window/01.props.window__p01.png"}

    placed = [
        {
            "id": f"{ref_id}_R0_veil",
            "label": "Close Foreground Silhouette & Lens Veil",
            "kind": "fx",
            "shell_idx": 0,
            "shell_id": "R0",
            "depth_val": 0.09,
            "radius_m": 1.2,
            "azimuth_deg": round((az_center_deg - 22.0) % 360.0, 1),
            "elevation_deg": -16.0,
            "x_norm": 0.20,
            "y_norm": 0.90,
            "scale": 0.78,
            "file": fg_file,
        },
        {
            "id": f"{ref_id}_R1_actor_0",
            "label": actors[0]["name"],
            "kind": "actor",
            "shell_idx": 1,
            "shell_id": "R1",
            "depth_val": 0.21,
            "radius_m": 2.8,
            "azimuth_deg": round((az_center_deg - 9.0) % 360.0, 1),
            "elevation_deg": -6.0,
            "x_norm": 0.36,
            "y_norm": 0.84,
            "scale": 1.0,
            "file": actors[0]["file"],
        },
        {
            "id": f"{ref_id}_R1_actor_1",
            "label": actors[1]["name"],
            "kind": "actor",
            "shell_idx": 1,
            "shell_id": "R1",
            "depth_val": 0.27,
            "radius_m": 3.8,
            "azimuth_deg": round((az_center_deg + 11.0) % 360.0, 1),
            "elevation_deg": -5.0,
            "x_norm": 0.65,
            "y_norm": 0.80,
            "scale": 0.90,
            "file": actors[1]["file"],
        },
        {
            "id": f"{ref_id}_R2_prop",
            "label": prop_item["name"],
            "kind": "prop",
            "shell_idx": 2,
            "shell_id": "R2",
            "depth_val": 0.40,
            "radius_m": 7.5,
            "azimuth_deg": round((az_center_deg + 24.0) % 360.0, 1),
            "elevation_deg": -3.5,
            "x_norm": 0.52,
            "y_norm": 0.72,
            "scale": 0.76,
            "file": prop_item["file"],
        },
        {
            "id": f"{ref_id}_R3_arch",
            "label": arch_item["name"],
            "kind": "arch",
            "shell_idx": 3,
            "shell_id": "R3",
            "depth_val": 0.56,
            "radius_m": 18.0,
            "azimuth_deg": round(az_center_deg % 360.0, 1),
            "elevation_deg": 2.0,
            "x_norm": 0.50,
            "y_norm": 0.64,
            "scale": 0.92,
            "file": arch_item["file"],
            "aperture_cutout": True,
        },
        {
            "id": f"{ref_id}_R4_foundry",
            "label": f"Sculpted 3D Foundry Voxel City & Coast (w1623 · {ref_id})",
            "kind": "topography",
            "shell_idx": 4,
            "shell_id": "R4",
            "depth_val": 0.75,
            "radius_m": 95.0,
            "azimuth_deg": round(az_center_deg % 360.0, 1),
            "elevation_deg": round((0.5 - shared_hor) * 90.0, 1),
            "x_norm": 0.50,
            "y_norm": round(shared_hor, 3),
            "scale": 1.0,
            "file": f"data/terrarium/foundry/inv/w1623/{ref_id}-b.jpg",
        },
        {
            "id": f"{ref_id}_R5_skydome",
            "label": f"360°×180° Outpainted Equirectangular Sky Dome (Hor {round(shared_hor*100)}%)",
            "kind": "skydome",
            "shell_idx": 5,
            "shell_id": "R5",
            "depth_val": 0.93,
            "radius_m": 800.0,
            "azimuth_deg": round(az_center_deg % 360.0, 1),
            "elevation_deg": 28.0,
            "x_norm": 0.50,
            "y_norm": round(shared_hor * 0.55, 3),
            "scale": 1.0,
            "file": f"data/terrarium/foundry/equirec/{ref_id}-eq.jpg",
        },
    ]

    # Stamp the alpha masks of R0..R3 cut-out items directly into the 360° equirectangular depth map!
    if eq_depth is not None and kit_img_cache is not None:
        H, W = eq_depth.shape
        for it in reversed(placed[:5]):
            f_rel = it["file"]
            f_path = SHOTS_DIR / f_rel
            if not f_path.exists():
                continue
            if f_rel not in kit_img_cache:
                try:
                    kit_img_cache[f_rel] = Image.open(f_path).convert("RGBA")
                except Exception:
                    kit_img_cache[f_rel] = None
            im_k = kit_img_cache.get(f_rel)
            if im_k is None:
                continue
            # Map item's azimuth_deg -> horizontal pixel x on the 360° sphere
            az = float(it["azimuth_deg"])
            lon_norm = (((az + 180.0) % 360.0) / 360.0)
            cx = int(lon_norm * W) % W
            sh_idx = it["shell_idx"]
            dh = int(H * (0.34 if sh_idx <= 1 else (0.28 if sh_idx == 2 else 0.36)))
            dw = max(14, int(dh * (im_k.width / max(1, im_k.height))))
            cy_bot = int(H * min(0.92, shared_hor + 0.14 + (3 - sh_idx) * 0.08))
            y0 = max(4, cy_bot - dh)
            x0 = max(0, min(W - dw, cx - dw // 2))
            alpha_arr = np.asarray(im_k.resize((dw, y0 + dh - y0), Image.Resampling.BILINEAR), dtype=np.float32)[:, :, 3] / 255.0
            if it.get("aperture_cutout"):
                # Punch window center open so outer shells R4/R5 show through the window frame
                ah, aw = alpha_arr.shape
                alpha_arr[int(ah * 0.18) : int(ah * 0.82), int(aw * 0.18) : int(aw * 0.82)] *= 0.15
            sub = eq_depth[y0 : y0 + dh, x0 : x0 + dw]
            h_s, w_s = sub.shape
            a_crop = alpha_arr[:h_s, :w_s]
            eq_depth[y0 : y0 + dh, x0 : x0 + dw] = sub * (1.0 - a_crop * 0.88) + float(it["depth_val"]) * (a_crop * 0.88)

    return placed


def draw_onion_radar_diagram(
    canvas: Image.Image,
    x0: int,
    y0: int,
    w: int,
    h: int,
    az_center_deg: float,
    shared_hor: float,
    placed_items: list[dict],
    title_str: str = "CONCENTRIC ONION DEPTH SHELLS (TOP-DOWN 360° RADAR)",
):
    """
    Draws a high-precision polar "Concentric Onion Shell" diagram showing the 6 spherical
    depth shells R0..R5 around the camera center, the active 76° camera frustum wedge,
    and every item plotted on its exact concentric onion ring!
    """
    dr = ImageDraw.Draw(canvas, "RGBA")
    f_hdr = get_font(11, bold=True)
    f_sm = get_font(10, bold=False)
    f_xs = get_font(9, bold=True)

    dr.rectangle([x0, y0, x0 + w, y0 + h], fill=(10, 14, 20, 245), outline=(92, 225, 230, 95), width=1)
    dr.text((x0 + 10, y0 + 7), title_str, fill=(255, 210, 63), font=f_hdr)

    cx = x0 + int(w * 0.34)
    cy = y0 + int(h * 0.56)
    max_r = int(min(w * 0.29, h * 0.38))

    for sh in reversed(ONION_SHELLS):
        k = sh["idx"]
        r_outer = int(max_r * ((k + 1) / 6.0))
        col = sh["color"]
        fill_rgba = (col[0], col[1], col[2], 22 if k % 2 == 0 else 14)
        stroke_rgba = (col[0], col[1], col[2], 175)
        dr.ellipse(
            [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
            fill=fill_rgba,
            outline=stroke_rgba,
            width=1,
        )

    for deg, lab in [(0, "N"), (90, "E"), (180, "S"), (270, "W")]:
        rad = math.radians(deg - 90.0)
        ex = cx + int((max_r + 3) * math.cos(rad))
        ey = cy + int((max_r + 3) * math.sin(rad))
        dr.line([(cx, cy), (ex, ey)], fill=(243, 234, 210, 45), width=1)
        tx = cx + int((max_r + 11) * math.cos(rad)) - 4
        ty = cy + int((max_r + 11) * math.sin(rad)) - 5
        dr.text((tx, ty), lab, fill=(169, 159, 134), font=f_xs)

    a1 = math.radians(az_center_deg - 90.0 - 38.0)
    a2 = math.radians(az_center_deg - 90.0 + 38.0)
    wx1, wy1 = cx + int(max_r * math.cos(a1)), cy + int(max_r * math.sin(a1))
    wx2, wy2 = cx + int(max_r * math.cos(a2)), cy + int(max_r * math.sin(a2))
    dr.polygon([(cx, cy), (wx1, wy1), (wx2, wy2)], fill=(255, 210, 63, 30), outline=(255, 210, 63, 190))

    for it in placed_items:
        s_idx = int(it.get("shell_idx", 1))
        sh = ONION_SHELLS[min(5, max(0, s_idx))]
        r_ring = max_r * ((s_idx + 0.55) / 6.0)
        ang = math.radians(float(it.get("azimuth_deg", az_center_deg)) - 90.0)
        px = cx + int(r_ring * math.cos(ang))
        py = cy + int(r_ring * math.sin(ang))
        col = sh["color"]
        dr.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(col[0], col[1], col[2], 255), outline=(10, 14, 20, 255), width=1)
        dr.text((px + 7, py - 5), f"R{s_idx}", fill=col, font=f_xs)

    dr.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 255, 255, 255), outline=(255, 61, 110, 255), width=2)

    lx = x0 + int(w * 0.66)
    ly = y0 + 28
    row_h = int((h - 34) / 6.0)
    for sh in ONION_SHELLS:
        k = sh["idx"]
        col = sh["color"]
        cy_row = ly + k * row_h
        dr.rectangle([lx, cy_row + 2, lx + 10, cy_row + 12], fill=col, outline=(255, 255, 255, 140))
        dr.text(
            (lx + 15, cy_row),
            f"{sh['id']} ({int(sh['d_min']*100)}-{int(sh['d_max']*100)}%) · {sh['radius_m']}m",
            fill=col,
            font=f_xs,
        )
        dr.text(
            (lx + 15, cy_row + 11),
            sh["short"],
            fill=(220, 212, 194),
            font=f_sm,
        )


def render_peeled_shell_card(
    eq_rgb: np.ndarray,
    eq_depth: np.ndarray,
    shell: dict,
    placed_items: list[dict],
    card_w: int,
    card_h: int,
    kit_img_cache: dict,
) -> Image.Image:
    """
    Renders a single peeled Onion Depth Shell (`R0`..`R5`) of size `(card_w, card_h)`
    showing ONLY the pixels of the 360° equirectangular panorama whose depth `d` falls
    inside `[d_min, d_max]` (with soft feathered shell edges over a dark onion-grid substrate),
    PLUS the cut-out kit items assigned to this onion shell!
    """
    H, W, _ = eq_rgb.shape
    d_min, d_max = shell["d_min"], shell["d_max"]
    pad = 0.032

    in_low = np.clip((eq_depth - (d_min - pad)) / max(1e-4, pad), 0.0, 1.0)
    in_high = np.clip(((d_max + pad) - eq_depth) / max(1e-4, pad), 0.0, 1.0)
    if shell["idx"] == 0:
        in_low = np.ones_like(eq_depth)
    if shell["idx"] == 5:
        in_high = np.ones_like(eq_depth)
    mask = in_low * in_high

    yy, xx = np.mgrid[0:H, 0:W]
    checker = (((xx // 12) + (yy // 12)) % 2).astype(np.float32)
    bg = np.zeros((H, W, 3), dtype=np.float32)
    bg[:, :, 0] = 11 + checker * 5
    bg[:, :, 1] = 15 + checker * 6
    bg[:, :, 2] = 22 + checker * 8

    edge_band = mask * (1.0 - mask) * 4.0
    col = np.array(shell["color"], dtype=np.float32)

    comp = bg * (1.0 - mask[:, :, None]) + eq_rgb * mask[:, :, None]
    comp = comp * (1.0 - edge_band[:, :, None] * 0.45) + col[None, None, :] * (edge_band[:, :, None] * 0.45)
    comp = np.nan_to_num(comp, nan=12.0, posinf=255.0, neginf=0.0)

    pil_card = Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8)).resize(
        (card_w, card_h), Image.Resampling.BICUBIC
    ).convert("RGBA")

    shell_items = [it for it in placed_items if it.get("shell_idx") == shell["idx"]]
    for it in shell_items:
        f_rel = it.get("file", "")
        if f_rel.startswith("data/") or f_rel.startswith("equirec/"):
            continue
        f_path = SHOTS_DIR / f_rel
        if f_path.exists():
            if f_rel not in kit_img_cache:
                try:
                    kit_img_cache[f_rel] = Image.open(f_path).convert("RGBA")
                except Exception:
                    kit_img_cache[f_rel] = None
            im_k = kit_img_cache.get(f_rel)
            if im_k is not None:
                kh = int(card_h * (0.58 if shell["idx"] == 1 else 0.48))
                kw = max(12, min(card_w - 16, int(kh * (im_k.width / max(1, im_k.height)))))
                im_r = im_k.resize((kw, kh), Image.Resampling.LANCZOS)
                kx = int(card_w * float(it.get("x_norm", 0.5))) - kw // 2
                ky = int(card_h * float(it.get("y_norm", 0.80))) - kh
                pil_card.alpha_composite(im_r, (max(4, min(card_w - kw - 4, kx)), max(22, min(card_h - kh - 20, ky))))

    dr = ImageDraw.Draw(pil_card, "RGBA")
    f_b = get_font(10, bold=True)
    f_s = get_font(9, bold=False)
    cov_pct = int(round(float((mask > 0.35).mean()) * 100.0))
    c_rgb = shell["color"]
    dr.rectangle([0, 0, card_w - 1, card_h - 1], outline=(c_rgb[0], c_rgb[1], c_rgb[2], 210), width=2)
    dr.rectangle([0, 0, card_w, 20], fill=(8, 11, 16, 235))
    dr.text((6, 4), f"{shell['short']} ({shell['radius_m']}m · d={int(shell['d_min']*100)}-{int(shell['d_max']*100)}%)", fill=c_rgb, font=f_b)
    dr.text((card_w - 34, 4), f"{cov_pct}%", fill=(243, 234, 210), font=f_b)

    item_names = " + ".join(it["label"][:18] for it in shell_items) if shell_items else shell["role"][:32]
    dr.rectangle([0, card_h - 18, card_w, card_h], fill=(8, 11, 16, 230))
    dr.text((6, card_h - 14), item_names[:36], fill=(215, 208, 190), font=f_s)

    return pil_card.convert("RGB")


def build_ref_onion_plate(
    ref_obj: dict,
    poem_title: str,
    shared_hor: float,
    rect_rgb_img: Image.Image,
    rect_depth_rgb: np.ndarray,
    eq_rgb: np.ndarray,
    eq_depth: np.ndarray,
    eq_depth_rgb: np.ndarray,
    placed_items: list[dict],
    kit_img_cache: dict,
) -> Image.Image:
    """
    Renders the 1440x820 high-resolution Per-Reference Onion Depth Mask & 6-Shell Peel Plate.
    """
    W, H = 1440, 820
    canvas = Image.new("RGB", (W, H), (8, 11, 16))
    dr = ImageDraw.Draw(canvas, "RGBA")
    f_title = get_font(13, bold=True)
    f_sub = get_font(11, bold=True)

    rid = ref_obj["id"]
    poem = ref_obj["poem"]
    az = int(round(ref_obj.get("eq_azimuth_deg", 150.0))) % 360
    hor_pct = int(round(shared_hor * 100))

    dr.rectangle([0, 0, W, 38], fill=(12, 17, 24))
    dr.line([(0, 38), (W, 38)], fill=(255, 210, 63, 120), width=1)
    dr.text(
        (14, 11),
        f"REF {rid} ({ref_obj.get('source','').upper()}) · POEM {poem} {poem_title[:24].upper()} · EQUIRECTANGULAR DEPTH MASK & 6 ONION SHELLS",
        fill=(255, 210, 63),
        font=f_title,
    )
    dr.text(
        (W - 535, 12),
        f"SHARED HORIZON: {hor_pct}% · AZIMUTH: {az}° · 6 CONCENTRIC ONION PLANES (R0 1.2m -> R5 800m)",
        fill=(92, 225, 230),
        font=f_sub,
    )

    # 1. Top Left: 360°x180° Equirectangular Depth Mask (780x390)
    eq_d_pil = Image.fromarray(eq_depth_rgb).resize((780, 390), Image.Resampling.BICUBIC)
    canvas.paste(eq_d_pil, (14, 48))
    dr.rectangle([14, 48, 14 + 780, 48 + 390], outline=(92, 225, 230, 180), width=1)
    dr.rectangle([20, 54, 515, 75], fill=(8, 11, 16, 225))
    dr.text(
        (26, 58),
        f"1. 360°×180° EQUIRECTANGULAR DEPTH MASK + ONION CONTOURS (HORIZON {hor_pct}%)",
        fill=(92, 225, 230),
        font=f_sub,
    )

    # 2. Top Right Upper: Concentric Onion Radar Diagram (618x225)
    draw_onion_radar_diagram(
        canvas,
        x0=808,
        y0=48,
        w=618,
        h=225,
        az_center_deg=float(az),
        shared_hor=shared_hor,
        placed_items=placed_items,
    )

    # 3. Top Right Lower: Rectilinear Reference RGB + Rectilinear Depth Mask Pair (618x155)
    dr.rectangle([808, 283, 808 + 618, 283 + 155], fill=(12, 16, 22), outline=(255, 210, 63, 110), width=1)
    r_rgb_thumb = rect_rgb_img.convert("RGB").resize((296, 124), Image.Resampling.BICUBIC)
    r_dep_thumb = Image.fromarray(rect_depth_rgb).resize((296, 124), Image.Resampling.BICUBIC)
    canvas.paste(r_rgb_thumb, (816, 306))
    canvas.paste(r_dep_thumb, (1122, 306))
    dr.text((816, 288), f"2A. RECTILINEAR FRAME ({rid})", fill=(243, 234, 210), font=f_sub)
    dr.text((1122, 288), f"2B. RECTILINEAR DEPTH MASK (6 ONION BANDS)", fill=(255, 210, 63), font=f_sub)

    # 4. Bottom Strip: The 6 Peeled Onion Depth Shells (R0..R5) side-by-side
    dr.text(
        (14, 448),
        "3. PEELED CONCENTRIC ONION DEPTH SHELLS (EACH SHELL SLICED BY EQUIRECTANGULAR DEPTH MASK + STAGED CUT-OUT ITEMS):",
        fill=(255, 210, 63),
        font=f_sub,
    )
    card_w = 228
    card_h = 330
    gap = 8
    for k, sh in enumerate(ONION_SHELLS):
        cx = 14 + k * (card_w + gap)
        cy = 470
        card_im = render_peeled_shell_card(
            eq_rgb=eq_rgb,
            eq_depth=eq_depth,
            shell=sh,
            placed_items=placed_items,
            card_w=card_w,
            card_h=card_h,
            kit_img_cache=kit_img_cache,
        )
        canvas.paste(card_im, (cx, cy))

    return canvas


def build_poem_shared_onion_plate(
    poem: str,
    poem_title: str,
    shared_hor: float,
    zone: str,
    poem_eq_rgb: np.ndarray,
    poem_eq_depth: np.ndarray,
    poem_eq_depth_rgb: np.ndarray,
    poem_items: list[dict],
    kit_img_cache: dict,
) -> Image.Image:
    """
    Renders the 1600x900 Shared Poem-Level 360°x180° Equirectangular Depth Mask &
    Concentric Onion Shell Arena Plate (`onion_shared_poem_XX.png`).
    """
    W, H = 1600, 900
    canvas = Image.new("RGB", (W, H), (8, 11, 16))
    dr = ImageDraw.Draw(canvas, "RGBA")
    f_title = get_font(15, bold=True)
    f_sub = get_font(11, bold=True)

    hor_pct = int(round(shared_hor * 100))
    dr.rectangle([0, 0, W, 40], fill=(12, 17, 24))
    dr.line([(0, 40), (W, 40)], fill=(255, 210, 63, 140), width=1)
    dr.text(
        (16, 11),
        f"POEM {poem} · {poem_title.upper()} · SHARED 360°×180° EQUIRECTANGULAR DEPTH MASK & CONCENTRIC ONION SHELLS",
        fill=(255, 210, 63),
        font=f_title,
    )
    dr.text(
        (W - 470, 13),
        f"SHARED HORIZON: {hor_pct}% · {zone.upper()} · 8 REFS FUSED",
        fill=(92, 225, 230),
        font=f_sub,
    )

    # Top Left (920x460): Shared 360°x180° Equirectangular Depth Mask
    eq_d_pil = Image.fromarray(poem_eq_depth_rgb).resize((920, 460), Image.Resampling.BICUBIC)
    canvas.paste(eq_d_pil, (16, 52))
    dr.rectangle([16, 52, 16 + 920, 52 + 460], outline=(92, 225, 230, 190), width=1)
    dr.rectangle([24, 60, 560, 82], fill=(8, 11, 16, 225))
    dr.text(
        (30, 65),
        f"SHARED 360°×180° EQUIRECTANGULAR DEPTH MASK (ALL 8 REFS FUSED AT {hor_pct}% HORIZON)",
        fill=(92, 225, 230),
        font=f_sub,
    )

    # Top Right (632x460): Concentric Onion Radar Diagram + Shared RGB Panorama Preview
    draw_onion_radar_diagram(
        canvas,
        x0=950,
        y0=52,
        w=634,
        h=260,
        az_center_deg=150.0,
        shared_hor=shared_hor,
        placed_items=poem_items,
        title_str=f"POEM {poem} · 360° CONCENTRIC ONION SHELL ARENA (R0..R5)",
    )
    eq_rgb_thumb = Image.fromarray(poem_eq_rgb.astype(np.uint8)).resize((634, 190), Image.Resampling.BICUBIC)
    canvas.paste(eq_rgb_thumb, (950, 322))
    dr.rectangle([950, 322, 950 + 634, 322 + 190], outline=(255, 210, 63, 140), width=1)
    dr.rectangle([956, 328, 1340, 348], fill=(8, 11, 16, 220))
    dr.text((962, 332), f"SHARED 360°×180° RGB OUTPAINT PANORAMA (POEM {poem})", fill=(255, 210, 63), font=f_sub)

    # Bottom Strip: 6 Peeled Poem-Wide Equirectangular Onion Shells
    dr.text(
        (16, 524),
        f"POEM {poem} · 6 CONCENTRIC ONION DEPTH SHELLS PEELED FROM THE SHARED 360° EQUIRECTANGULAR SPHERE:",
        fill=(255, 210, 63),
        font=f_sub,
    )
    card_w = 254
    card_h = 336
    gap = 8
    for k, sh in enumerate(ONION_SHELLS):
        cx = 16 + k * (card_w + gap)
        cy = 548
        card_im = render_peeled_shell_card(
            eq_rgb=poem_eq_rgb,
            eq_depth=poem_eq_depth,
            shell=sh,
            placed_items=poem_items,
            card_w=card_w,
            card_h=card_h,
            kit_img_cache=kit_img_cache,
        )
        canvas.paste(card_im, (cx, cy))

    return canvas


def load_scene_items_by_poem() -> dict:
    """
    Loads authentic cut-out actors, props, and architectural pieces per poem from
    `scene_collage_plans.json` so every poem's onion shells contain its real kit pieces.
    """
    out = {}
    plans_path = SHOTS_DIR / "arena" / "parts" / "kit3" / "release_v2" / "scene_collage_plans.json"
    if not plans_path.exists():
        return out
    try:
        plans = json.loads(plans_path.read_text())
        for sc in plans.get("scenes", []):
            p_num = f"{int(sc.get('book', 1)):02d}"
            bucket = out.setdefault(p_num, [])
            seen = {x["file"] for x in bucket}
            for pl in sc.get("staged_placements", []):
                f = pl.get("file", "")
                sem = pl.get("semantic_class", "")
                if not f or f in seen or not (SHOTS_DIR / f).exists():
                    continue
                if "figure" in sem:
                    kind = "actor"
                    sh_idx = 1
                    d_val = 0.24
                elif sem in ("door_window_arch", "room_wall", "stair_bridge_viaduct", "building_facade"):
                    kind = "arch"
                    sh_idx = 3
                    d_val = 0.56
                else:
                    kind = "prop"
                    sh_idx = 2
                    d_val = 0.40
                seen.add(f)
                bucket.append({
                    "name": (pl.get("label") or "Kit Piece")[:22],
                    "kind": kind,
                    "shell": sh_idx,
                    "d": d_val,
                    "file": f,
                })
                if len(bucket) >= 8:
                    break
    except Exception:
        pass
    return out


def main():
    print("[1/5] Loading refs.json, inverse.json, and scene_collage_plans.json...")
    refs_path = FOUNDRY_DIR / "refs.json"
    inv_path = FOUNDRY_DIR / "inverse.json"
    refs_data = json.loads(refs_path.read_text())
    inv_data = json.loads(inv_path.read_text())

    scene_items_by_poem = load_scene_items_by_poem()
    kit_img_cache = {}

    refs_by_poem = {}
    for r in refs_data["refs"]:
        refs_by_poem.setdefault(r["poem"], []).append(r)

    poems_meta = refs_data.get("poems", {})
    shared_horizons = refs_data.get("shared_horizons", {})

    onion_manifest = {
        "title": "WYGWYL Concentric Onion Depth Shells & 360° Equirectangular Depth Masks",
        "shells": ONION_SHELLS,
        "poems": {},
        "refs": {},
    }

    eq_w, eq_h = 960, 480
    poem_master_plates = []
    vault_new_items = []

    print("[2/5] Building Rectilinear Depth Masks, 360° Equirectangular Depth Masks & 6-Shell Onion Plates...")
    all_poem_keys = sorted(list(set(list(refs_by_poem.keys()) + ["14"])))

    for poem in all_poem_keys:
        p_refs = refs_by_poem.get(poem) or refs_by_poem.get("13", [])
        sh_info = shared_horizons.get(poem) or shared_horizons.get("13") or {"shared_hor": 0.40, "zone": "Atlantis"}
        shared_hor = float(sh_info.get("shared_hor", 0.40))
        zone = sh_info.get("zone", "Baltimere & Atlantis")
        p_title = poems_meta.get(poem, {}).get("title") or ("Hot Minute" if poem == "14" else f"Poem {poem}")

        shared_eq_path = EQUIREC_DIR / f"poem_{poem}_shared_eq.jpg"
        if not shared_eq_path.exists():
            shared_eq_path = EQUIREC_DIR / "poem_13_shared_eq.jpg"
        shared_eq_pil = Image.open(shared_eq_path).convert("RGB").resize((eq_w, eq_h), Image.Resampling.BICUBIC)
        shared_eq_rgb = np.asarray(shared_eq_pil, dtype=np.float32)

        poem_base_depth = build_base_equirec_depth(poem, shared_hor, eq_w, eq_h, shared_eq_rgb)
        poem_depth_acc = poem_base_depth.copy()
        poem_w_acc = np.ones((eq_h, eq_w), dtype=np.float32) * 0.45

        ref_rect_depths = {}
        ref_imgs = {}
        for r in p_refs:
            rid = r["id"]
            r_img_path = FOUNDRY_DIR / r["img"]
            r_seg_path = FOUNDRY_DIR / r["seg"]
            im_r = Image.open(r_img_path).convert("RGB")
            im_s = Image.open(r_seg_path).convert("RGB") if r_seg_path.exists() else im_r
            ref_imgs[rid] = im_r

            d_rect = compute_rectilinear_depth_field(im_r, im_s, r, shared_hor, target_w=640, target_h=268)
            ref_rect_depths[rid] = d_rect

            if r["poem"] == poem:
                rect_depth_rgb = colorize_onion_depth(d_rect, draw_contours=True, shared_hor=shared_hor)
                rect_depth_rel = f"refs/{rid}-depth.jpg"
                Image.fromarray(rect_depth_rgb).save(FOUNDRY_DIR / rect_depth_rel, quality=90)
                r["depth_img"] = rect_depth_rel

            az_deg = float(r.get("eq_azimuth_deg", 150.0))
            ref_hor = float(r.get("intrinsic_horizon", shared_hor))
            proj_d, proj_w = project_scalar_into_equirec(d_rect, shared_hor, ref_hor, eq_w, eq_h, az_deg, hfov_deg=76.0)
            poem_depth_acc += proj_d * proj_w * 1.4
            poem_w_acc += proj_w * 1.4

        poem_eq_depth = np.clip(poem_depth_acc / np.maximum(1e-4, poem_w_acc), 0.02, 0.99)

        poem_all_placed_items = []
        if poem != "14":
            for r in p_refs:
                rid = r["id"]
                rid_u = rid.replace("-", "_")
                az_deg = float(r.get("eq_azimuth_deg", 150.0))
                ref_hor = float(r.get("intrinsic_horizon", shared_hor))

                eq_ref_path = FOUNDRY_DIR / r.get("eq_img", f"equirec/{rid}-eq.jpg")
                eq_ref_pil = Image.open(eq_ref_path).convert("RGB").resize((eq_w, eq_h), Image.Resampling.BICUBIC)
                eq_ref_rgb = np.asarray(eq_ref_pil, dtype=np.float32)

                ref_base_d = build_base_equirec_depth(poem, shared_hor, eq_w, eq_h, eq_ref_rgb)
                proj_d, proj_w = project_scalar_into_equirec(
                    ref_rect_depths[rid], shared_hor, ref_hor, eq_w, eq_h, az_deg, hfov_deg=78.0
                )
                ref_eq_depth = (poem_eq_depth * 0.55 + ref_base_d * 0.45) * (1.0 - proj_w * 0.88) + proj_d * (proj_w * 0.88)

                placed_items = stamp_kit_items_into_onion_shells(
                    poem, rid, az_deg, shared_hor, scene_items_by_poem, eq_depth=ref_eq_depth, kit_img_cache=kit_img_cache
                )
                poem_all_placed_items.extend(placed_items[:4])

                eq_depth_rgb = colorize_onion_depth(ref_eq_depth, draw_contours=True, shared_hor=shared_hor)
                eq_depth_rel = f"equirec/{rid}-eq-depth.jpg"
                Image.fromarray(eq_depth_rgb).save(FOUNDRY_DIR / eq_depth_rel, quality=90)

                # Compute per-shell coverage percentages across the 360° sphere
                shell_fracs = {}
                for sh in ONION_SHELLS:
                    m = (ref_eq_depth >= sh["d_min"]) & (ref_eq_depth < (1.01 if sh["idx"] == 5 else sh["d_max"]))
                    shell_fracs[sh["id"]] = round(float(m.mean()) * 100.0, 1)

                r["eq_depth_img"] = eq_depth_rel
                r["onion_shells"] = shell_fracs
                r["onion_vault_png"] = f"png_vault/onion_depth/onion_depth_ref_{rid_u}.png"

                # Render & save 1440x820 Per-Reference Onion Depth & 6-Shell Peel PNG
                rect_depth_rgb = colorize_onion_depth(ref_rect_depths[rid], draw_contours=True, shared_hor=shared_hor)
                ref_plate = build_ref_onion_plate(
                    ref_obj=r,
                    poem_title=p_title,
                    shared_hor=shared_hor,
                    rect_rgb_img=ref_imgs[rid],
                    rect_depth_rgb=rect_depth_rgb,
                    eq_rgb=eq_ref_rgb,
                    eq_depth=ref_eq_depth,
                    eq_depth_rgb=eq_depth_rgb,
                    placed_items=placed_items,
                    kit_img_cache=kit_img_cache,
                )
                vault_ref_path = VAULT_ONION_DIR / f"onion_depth_ref_{rid_u}.png"
                ref_plate.save(vault_ref_path, optimize=True)

                onion_manifest["refs"][rid] = {
                    "id": rid,
                    "poem": poem,
                    "shared_horizon": shared_hor,
                    "azimuth_deg": az_deg,
                    "depth_img": r["depth_img"],
                    "eq_depth_img": eq_depth_rel,
                    "onion_vault_png": r["onion_vault_png"],
                    "shell_coverage_pct": shell_fracs,
                    "items": placed_items,
                }

                vault_new_items.append({
                    "id": f"onion_depth_ref_{rid_u}",
                    "title": f"Ref {rid} · 360° Equirectangular Depth Mask & 6 Onion Shells (Poem {poem} {p_title})",
                    "filename": f"onion_depth_ref_{rid_u}.png",
                    "file": f"png_vault/onion_depth/onion_depth_ref_{rid_u}.png",
                    "category": "onion_depth",
                    "category_label": "Onion Depth Masks & 360° Equirec Shells",
                    "subcategory": "ref_onion_depth_peel",
                    "poem": poem,
                    "ref_id": rid,
                    "world": "w1623",
                    "width": 1440,
                    "height": 820,
                    "size_kb": round(vault_ref_path.stat().st_size / 1024),
                    "desc": f"360°×180° Equirectangular Depth Mask, Rectilinear Depth Mask, Top-Down Onion Radar, and 6 Peeled Concentric Onion Shells (R0..R5) for {rid} at {round(shared_hor*100)}% shared horizon.",
                })

        if not poem_all_placed_items:
            poem_all_placed_items = stamp_kit_items_into_onion_shells(poem, f"{poem}-00", 150.0, shared_hor, scene_items_by_poem)

        # Save Shared Poem-Level 360° Equirectangular Depth Mask (`equirec/poem_XX_shared_depth.jpg`)
        poem_eq_depth_rgb = colorize_onion_depth(poem_eq_depth, draw_contours=True, shared_hor=shared_hor)
        poem_depth_rel = f"equirec/poem_{poem}_shared_depth.jpg"
        Image.fromarray(poem_eq_depth_rgb).resize((1600, 800), Image.Resampling.BICUBIC).save(
            FOUNDRY_DIR / poem_depth_rel, quality=91
        )

        # Render Shared Poem 1600x900 Onion Depth & 6-Shell Arena PNG
        poem_plate = build_poem_shared_onion_plate(
            poem=poem,
            poem_title=p_title,
            shared_hor=shared_hor,
            zone=zone,
            poem_eq_rgb=shared_eq_rgb,
            poem_eq_depth=poem_eq_depth,
            poem_eq_depth_rgb=poem_eq_depth_rgb,
            poem_items=poem_all_placed_items[:12],
            kit_img_cache=kit_img_cache,
        )
        vault_poem_path = VAULT_ONION_DIR / f"onion_shared_poem_{poem}.png"
        poem_plate.save(vault_poem_path, optimize=True)
        poem_master_plates.append((poem, poem_plate))

        if poem in shared_horizons:
            shared_horizons[poem]["eq_depth_img"] = poem_depth_rel
            shared_horizons[poem]["onion_vault_png"] = f"png_vault/onion_depth/onion_shared_poem_{poem}.png"

        onion_manifest["poems"][poem] = {
            "poem": poem,
            "title": p_title,
            "shared_horizon": shared_hor,
            "zone": zone,
            "eq_depth_img": poem_depth_rel,
            "onion_vault_png": f"png_vault/onion_depth/onion_shared_poem_{poem}.png",
        }

        vault_new_items.append({
            "id": f"onion_shared_poem_{poem}",
            "title": f"Poem {poem} ({p_title}) · Shared 360° Equirectangular Depth Mask & 6 Onion Shells",
            "filename": f"onion_shared_poem_{poem}.png",
            "file": f"png_vault/onion_depth/onion_shared_poem_{poem}.png",
            "category": "onion_depth",
            "category_label": "Onion Depth Masks & 360° Equirec Shells",
            "subcategory": "shared_poem_onion_depth",
            "poem": poem,
            "world": "w1623",
            "width": 1600,
            "height": 900,
            "size_kb": round(vault_poem_path.stat().st_size / 1024),
            "desc": f"Shared 360°×180° Equirectangular Depth Mask, Concentric Onion Radar, and 6 Peeled Spherical Shells (R0..R5) across Poem {poem} ({p_title}).",
        })
        print(f"  ✓ Poem {poem} ({p_title}): Equirectangular Depth Masks & 6 Concentric Onion Shells built")

    print("[3/5] Building All-14-Poems Master Onion Depth Contact Sheet...")
    cols, rows = 2, 7
    thumb_w, thumb_h = 1200, 675
    sheet_w = cols * thumb_w + 48
    sheet_h = rows * thumb_h + 96
    master_sheet = Image.new("RGB", (sheet_w, sheet_h), (6, 9, 14))
    dr_m = ImageDraw.Draw(master_sheet)
    f_m = get_font(22, bold=True)
    dr_m.text(
        (24, 22),
        "WYGWYL · ALL 14 POEMS 360°×180° EQUIRECTANGULAR DEPTH MASKS & 6 CONCENTRIC ONION DEPTH SHELLS (R0..R5)",
        fill=(255, 210, 63),
        font=f_m,
    )
    for idx, (p_num, p_im) in enumerate(poem_master_plates[:14]):
        r_i = idx // cols
        c_i = idx % cols
        x0 = 16 + c_i * (thumb_w + 16)
        y0 = 68 + r_i * (thumb_h + 4)
        master_sheet.paste(p_im.resize((thumb_w, thumb_h), Image.Resampling.BICUBIC), (x0, y0))

    master_path = VAULT_ONION_DIR / "all_14_poems_onion_depth_master.png"
    master_sheet.save(master_path, optimize=True)
    vault_new_items.insert(0, {
        "id": "all_14_poems_onion_depth_master",
        "title": "All 14 Poems · Shared 360°×180° Equirectangular Depth Masks & 6 Concentric Onion Shells Master Sheet",
        "filename": "all_14_poems_onion_depth_master.png",
        "file": "png_vault/onion_depth/all_14_poems_onion_depth_master.png",
        "category": "onion_depth",
        "category_label": "Onion Depth Masks & 360° Equirec Shells",
        "subcategory": "master_onion_depth_sheet",
        "poem": "all",
        "world": "w1623",
        "width": sheet_w,
        "height": sheet_h,
        "size_kb": round(master_path.stat().st_size / 1024),
        "desc": "Master contact sheet of all 14 poems' 360°×180° Equirectangular Depth Masks, Top-Down Concentric Onion Radar Rings, and 6 Peeled Spherical Depth Shells (R0..R5).",
    })

    print("[4/5] Saving onion_planes.json, refs.json, and inverse.json...")
    (FOUNDRY_DIR / "onion_planes.json").write_text(json.dumps(onion_manifest, indent=2))
    refs_data["onion_shells"] = ONION_SHELLS
    inv_data["onion_shells"] = ONION_SHELLS
    refs_path.write_text(json.dumps(refs_data, indent=2))
    inv_path.write_text(json.dumps(inv_data, indent=2))

    print("[5/5] Updating shots/png_vault/png_catalog.json...")
    cat_path = VAULT_DIR / "png_catalog.json"
    cat = json.loads(cat_path.read_text())
    existing = [it for it in cat.get("items", []) if it.get("category") != "onion_depth"]
    all_items = vault_new_items + existing
    cat["items"] = all_items
    cat["total_count"] = len(all_items)
    cat["onion_depth_count"] = len(vault_new_items)

    cat_labels = {
        "onion_depth": "🧅 Onion Depth Masks & 6-Shell Peel Plates",
        "equirectangular": "🌐 360° Equirectangular Outpaints & Shared Horizons",
        "painted_tapes": "🎞️ Continuous Painted Tapes & Contact Sheets",
        "painted_shots": "🎨 Individual Painted & Shaped Shots",
        "foundry_inverse": "🔨 Foundry & Inverse Through-Frame Builds",
        "session_artifacts": "🧪 Session Proof & Audit PNGs",
        "multiplane_tapes": "🏛️ Multiplane Scene Plates & Corridors",
        "master_kit_sheets": "🎭 Character & Kit Cut-Out Sheets",
    }
    counts = {}
    for it in all_items:
        c = it.get("category", "other")
        counts[c] = counts.get(c, 0) + 1
    cat["categories"] = [
        {"id": cid, "label": cat_labels.get(cid, cid), "count": cnt}
        for cid, cnt in counts.items()
    ]
    cat_path.write_text(json.dumps(cat, indent=2))
    print(f"DONE! Generated {len(vault_new_items)} Onion Depth & 6-Shell Peel PNGs + 104 Rectilinear Depth Masks + 118 Equirectangular Depth Masks.")


if __name__ == "__main__":
    main()
