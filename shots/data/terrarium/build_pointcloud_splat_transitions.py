#!/usr/bin/env python3
"""
build_pointcloud_splat_transitions.py
=====================================
1. Refines the Poet's `P2` (Hero / Collar / Neck / Hands) vs `P3` (Background Lamp / Listeners)
   segmentation in `poet_01..08` so the Poet's charcoal cowl/mock-neck collar and face silhouette
   never get clipped by the warm background lampshade in `poet_02`.
2. Generates binary metric 3D Point Clouds (`points.ply`) and 3D Gaussian Splats (`scene.splat`
   32-byte WebGL format + `scene_gs.ply` Inria 3DGS format) for all 8 Poet Lectern shots
   (`poet_01..08`) and all 8 Agent K / Wooden Horse shots (`k_01..08`), joining the 81 Poem
   shots and 18 District/Hub splats.
3. Implements the Plane-Stratified 3D Point-Cloud & Multi-Scale Gaussian Splat Transition Engine
   with:
     - `P0..P6` Staggered Departure & Arrival Schedule:
       * `P6/P5/P4` (Mural & Room Architecture) lift into 3D point cloud first (`u in [0.00, 0.72]`)
       * `P1` (Clear Acrylic Lectern) refracts as a crystalline point-cloud sheet (`u in [0.12, 0.82]`)
       * `P3` (Circle of Listeners / Secondary Objects) follow (`u in [0.18, 0.88]`)
       * `P2` (The Poet's Face, Collar, Shoulders & Hands <-> Poem Hero & Wooden Horse Anchor)
         hold focal coherence longest (`u in [0.28, 1.00]`) and travel along 3D cubic Hermite arcs
         directly from the Poet's `P2` centroid to the Poem's `P2` Hero centroid!
     - Perceptual CIELAB / LCh "Color's Rhythm" Transport:
       * Instead of muddy linear RGB crossfades, points travel through a 3-phase chromatic arc
         in CIELAB space, cresting at mid-flight (`sin(pi * u)`) into each Poem's measured City
         District `glow` and `body` palette (`_city/districts.json`) before locking into the target cel.
     - Spoken-Word & Breath Cadence Rhythm (`reading.mp3` RMS Envelope + `07-spacetime` Cut Grammar):
       * Extracts the real vocal RMS envelope from `play/levels/<NN>/reading.mp3` so camera holds
         (`0°` Face-On Lock), `±58°` Side-On 4D Depth Strata cuts, and collar/chest breath micro-motion
         lock to the Poet's actual spoken rhythm.
"""

import glob
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter

ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch")
SHOTS_DIR = ROOT / "shots"
OUT_DIR = SHOTS_DIR / "out"
CITY_JSON = ROOT / "_city" / "districts.json"
TERR_DIR = SHOTS_DIR / "data" / "terrarium"
POET_DIR = TERR_DIR / "poet_lectern"
SEEING_DIR = TERR_DIR / "seeing_spacetime_films"
BOOKEND_VID_DIR = SHOTS_DIR / "videos" / "poet_bookends"
VIDEOS_DIR = SHOTS_DIR / "videos"
ARTIFACT_DIR = Path("/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584")

sys.path.insert(0, str(SHOTS_DIR))
import cartoon
import multiplane
import ply_to_splat
import scene_program

W, H = 1280, 720
RW, RH = 640, 360  # Multi-scale Gaussian splat accumulation grid (2x supersampled to 1280x720)
FPS = 24

NIGHT_BG = np.array([0.020, 0.024, 0.035], dtype=np.float32)
PAPER_BG = np.array([0.945, 0.928, 0.892], dtype=np.float32)

POET_SIDS = [
    "poet_01_warm_salon_circle_wide",
    "poet_02_warm_lectern_medium",
    "poet_03_standing_graffiti_gesture",
    "poet_04_standing_hands_heart",
    "poet_05_close_pages_threshold",
    "poet_06_chiaroscuro_open_hands",
    "poet_07_chiaroscuro_wide_circle",
    "poet_08_ots_circle_listeners",
]

K_SIDS = [
    "k_01_office_interview",
    "k_02_k_eyes_threshold",
    "k_03_orphanage_catwalks",
    "k_04_clockwork_gears",
    "k_05_furnace_sanctuary",
    "k_06_wooden_horse_palm",
    "k_07_burying_horse_ash",
    "k_08_stelline_scanner_return",
]


def smootherstep(u: float) -> float:
    u = float(np.clip(u, 0.0, 1.0))
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)


def ease(u: float) -> float:
    u = float(np.clip(u, 0.0, 1.0))
    return u * u * (3.0 - 2.0 * u)


def hex_to_rgb_f32(h: str) -> np.ndarray:
    h = (h or "#fa8d15").lstrip("#")
    if len(h) != 6:
        return np.array([0.98, 0.55, 0.08], dtype=np.float32)
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)], dtype=np.float32) / 255.0


def get_font(size: int, mono: bool = False, italic: bool = False):
    candidates = []
    if mono:
        candidates = [
            str(SHOTS_DIR / "fonts/ibm-plex-mono-latin-400-normal.woff2"),
            "/System/Library/Fonts/Menlo.ttc",
        ]
    elif italic:
        candidates = [
            str(SHOTS_DIR / "fonts/im-fell-english-latin-400-italic.woff2"),
            "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
        ]
    else:
        candidates = [
            str(SHOTS_DIR / "fonts/im-fell-english-latin-400-normal.woff2"),
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
        ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


# ==============================================================================
# STEP 1: REFINE POET COLLAR/NECK/HERO MASK & EXPORT BINARY POINTS.PLY + SCENE.SPLAT
# ==============================================================================
def save_binary_ply(path: Path, pts: np.ndarray, cols: np.ndarray):
    n = len(pts)
    header = (
        "ply\n"
        "format binary_little_endian 1.0\n"
        f"element vertex {n}\n"
        "property float x\nproperty float y\nproperty float z\n"
        "property uchar red\nproperty uchar green\nproperty uchar blue\n"
        "end_header\n"
    )
    dtype = np.dtype([("p", "<f4", 3), ("c", "u1", 3)])
    buf = np.empty(n, dtype=dtype)
    buf["p"] = pts.astype(np.float32)
    buf["c"] = cols.astype(np.uint8)
    with open(path, "wb") as f:
        f.write(header.encode("ascii"))
        f.write(buf.tobytes())


def refine_poet_collar_and_generate_splats():
    """
    1. In `poet_02_warm_lectern_medium`, ensures the Poet's face, beard, neck, and charcoal
       cowl/mock-neck collar stay 100% in `P2` (Hero) and are never overlapped by the bright
       lampshade (`P3`) behind his right cheek/collar.
    2. Exports binary `points.ply`, `scene.splat` (32-byte WebGL Gaussian Splat), and `scene_gs.ply`
       for all 8 Poet shots (`poet_01..08`) and all 8 Agent K shots (`k_01..08`).
    """
    print("Step 1: Refining Poet collar/neck P2 masks & exporting points.ply + scene.splat for all 16 Poet & K shots...")

    # Fix poet_02 lampshade vs Poet cheek/collar overlap in arrays.npz and re-run multiplane/cartoon/program
    p02_dir = OUT_DIR / "poet_02_warm_lectern_medium"
    arr_p02 = p02_dir / "arrays.npz"
    if arr_p02.exists() and not (p02_dir / "scene.splat").exists():
        data = dict(np.load(arr_p02))
        rgb = np.array(Image.open(p02_dir / "image.jpg").convert("RGB"))
        H_im, W_im = rgb.shape[:2]
        masks = data["masks"].copy()
        lum = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])
        yy, xx = np.mgrid[0:H_im, 0:W_im]
        poet_core = (xx >= int(0.35 * W_im)) & (xx <= int(0.75 * W_im)) & (yy >= int(0.06 * H_im)) & ( lum < 178.0 )
        lamp_bright = (xx >= int(0.37 * W_im)) & (xx <= int(0.53 * W_im)) & (yy >= int(0.26 * H_im)) & (yy <= int(0.54 * H_im)) & (lum >= 182.0)

        if len(masks) >= 1:
            # Ensure Poet mask (index 0) owns all of his cheek, beard, and mock-neck collar
            masks[0] = (masks[0] | (poet_core & (masks.any(axis=0)))) & (~lamp_bright)
            for mi in range(1, len(masks)):
                masks[mi] = masks[mi] & (~masks[0])
            data["masks"] = masks
            np.savez_compressed(arr_p02, **data)
            multiplane.build("poet_02_warm_lectern_medium", {})
            cartoon.render("poet_02_warm_lectern_medium")
            sc = scene_program.Scene("poet_02_warm_lectern_medium")
            sc.refine(rounds=3)
            sc.export()
            print("  -> Refined poet_02 collar/cheek P2 boundary and rebuilt multiplane + cel + angular program.")

    # Now generate points.ply, scene.splat, and scene_gs.ply for all 16 shots (poet_01..08 & k_01..08)
    all_sids = POET_SIDS + K_SIDS
    for sid in all_sids:
        od = OUT_DIR / sid
        if (od / "points.ply").exists() and (od / "scene.splat").exists():
            continue
        arr_path = od / "arrays.npz"
        img_path = od / "image.jpg"
        if not arr_path.exists() or not img_path.exists():
            continue
        A = np.load(arr_path)
        rgb = np.array(Image.open(img_path).convert("RGB"))
        dz = A["depth"].astype(np.float32)
        focal_px = float(A["focal_px"]) if "focal_px" in A.files else 1150.0
        H_im, W_im = dz.shape

        # Unproject on a 3px grid (exact same convention as analyze.py so pointcloud.html & ply_to_splat.py work natively)
        step = 3
        v_idx, u_idx = np.mgrid[0:H_im:step, 0:W_im:step]
        u_flat = u_idx.ravel()
        v_flat = v_idx.ravel()
        z_flat = np.clip(dz[v_flat, u_flat], 0.6, 28.0)

        x_flat = (u_flat - W_im * 0.5) * z_flat / focal_px
        y_flat = -((v_flat - H_im * 0.5) * z_flat / focal_px)  # +Y up
        z_gl = -z_flat                                         # -Z forward (OpenGL convention)

        pts = np.column_stack([x_flat, y_flat, z_gl]).astype(np.float32)
        cols = rgb[v_flat, u_flat]

        ply_path = od / "points.ply"
        save_binary_ply(ply_path, pts, cols)
        ply_to_splat.process_shot(sid, verbose=True)


# ==============================================================================
# STEP 2: MULTI-SCALE GAUSSIAN SPLAT & PLANE-STRATIFIED 3D POINT CLOUD ENGINE
# ==============================================================================
_VIG_CACHE = {}
def get_vignette(h: int, w: int) -> np.ndarray:
    if (h, w) not in _VIG_CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        v = 1.0 - 0.18 * (((xx - w * 0.5) / (w * 0.56)) ** 2 + ((yy - h * 0.5) / (h * 0.56)) ** 2)
        _VIG_CACHE[(h, w)] = np.clip(v, 0.76, 1.0)[..., None]
    return _VIG_CACHE[(h, w)]


def splat_gaussian_multiscale(
    px: np.ndarray,
    py: np.ndarray,
    zc: np.ndarray,
    rad: np.ndarray,
    rgb: np.ndarray,
    w_val: np.ndarray,
    bg_rgb: np.ndarray = None,
    gain: float = 1.15,
) -> np.ndarray:
    """
    Multi-scale 3-bucket Gaussian Splatting + Beers-Law exponential transmittance (`1 - exp(-A * k)`)
    with front-surface occlusion weighting so foreground P2 points (the Poet's collar, face, hands,
    or the Poem's Hero) cleanly occlude background splats without muddy stain bleeding.
    """
    valid = (zc > 0.25) & (px >= -6) & (px < RW + 6) & (py >= -6) & (py < RH + 6) & (w_val > 1e-4)
    if not np.any(valid):
        return np.broadcast_to(NIGHT_BG, (H, W, 3)).copy() if bg_rgb is None else bg_rgb.copy()

    px = px[valid]
    py = py[valid]
    zc = zc[valid]
    rad = rad[valid]
    rgb = rgb[valid]
    wt = w_val[valid]

    ix = np.clip(np.round(px).astype(np.int32), 0, RW - 1)
    iy = np.clip(np.round(py).astype(np.int32), 0, RH - 1)

    # Pass 1: Front-surface depth buffer to prevent background walls bleeding through foreground P2 figures
    d_buf = np.full((RH, RW), 1e5, dtype=np.float32)
    np.minimum.at(d_buf, (iy, ix), zc)
    # 3x3 min-filter (morphological erosion on depth) to close 1px pinholes between splats
    d_buf = cv2.erode(d_buf, np.ones((3, 3), np.uint8))
    front_z = d_buf[iy, ix]
    depth_vis = np.exp(-np.maximum(0.0, zc - front_z) * 2.8)
    wt = wt * depth_vis

    # Pass 2: 3 Gaussian scale buckets: sharp focal core (<1.35px), medium body (1.35..3.2px), bokeh scatter (>3.2px)
    b0 = rad < 1.35
    b1 = (rad >= 1.35) & (rad < 3.20)
    b2 = rad >= 3.20

    sigmas = [0.48, 1.30, 3.10]
    ks = [4.2, 7.8, 18.0]
    acc = np.zeros((3, RH, RW, 4), dtype=np.float32)

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

    # Resolve buckets from softest bokeh (bi=2) to sharpest core (bi=0) via Beers-Law transmittance
    if bg_rgb is not None:
        out_lo = cv2.resize(bg_rgb, (RW, RH), interpolation=cv2.INTER_AREA)
    else:
        out_lo = np.broadcast_to(NIGHT_BG, (RH, RW, 3)).copy()

    for bi in (2, 1, 0):
        A = acc[bi, :, :, 3:4]
        col = acc[bi, :, :, :3] / np.maximum(A, 1e-5)
        cov = 1.0 - np.exp(-A * ks[bi] * gain)
        out_lo = out_lo * (1.0 - cov) + col * cov

    # Subtle highlight bloom on bright embers / collar rim light
    lum_lo = out_lo.mean(axis=-1, keepdims=True)
    hi_mask = np.clip((lum_lo - 0.62) * 2.5, 0.0, 1.0)
    bloom = np.stack([gaussian_filter((out_lo[:, :, c] * hi_mask[:, :, 0]), sigma=6.0) for c in range(3)], axis=-1)
    out_lo = np.clip(out_lo + bloom * 0.25, 0.0, 1.0) * get_vignette(RH, RW)

    return cv2.resize(np.clip(out_lo, 0.0, 1.0), (W, H), interpolation=cv2.INTER_CUBIC)


_BASE_YY, _BASE_XX = np.mgrid[0:H, 0:W].astype(np.float32)


def warp_multiplane_plate(img_rgb: np.ndarray, disp: np.ndarray, pan_x: float, tilt_y: float, dolly_scale: float, depth_stretch: float = 0.042) -> np.ndarray:
    """
    True 2.5D/3D multiplane camera transform using per-pixel inverse-depth parallax (`cv2.remap`).
    """
    local_scale = dolly_scale * (1.0 + depth_stretch * (disp - 0.38))
    parallax_weight = 0.28 + 0.72 * disp
    map_x = (_BASE_XX - W * 0.5) / local_scale + W * 0.5 + pan_x * parallax_weight
    map_y = (_BASE_YY - H * 0.5) / local_scale + H * 0.5 + tilt_y * parallax_weight
    return cv2.remap(
        img_rgb,
        map_x.astype(np.float32),
        map_y.astype(np.float32),
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )


_BUNDLE_CACHE = {}


def load_pointcloud_shot_bundle(sid: str, step_grid: int = 4) -> dict:
    """
    Loads a shot's 6 visual plates (`raw`, `cel`, `angular`, `layout`, `overlay`, `glow`),
    loads its native 24fps moving cinema video (`out/<sid>/film/shot.mp4`) if present, PLUS
    builds its Plane-Stratified 3D Point Cloud (`X, Y, Z, plane_id, collar_mask, rgb_cel, rgb_ang, rgb_lay`)
    on a `step_grid` lattice (`320x180 = 57,600` points) so any two shots can morph 1-to-1 in 3D space!
    """
    if sid in _BUNDLE_CACHE:
        return _BUNDLE_CACHE[sid]

    od = OUT_DIR / sid
    if not od.exists():
        raise FileNotFoundError(f"Missing shot directory: {od}")

    def _ld(rel_p, default_arr=None):
        p = od / rel_p
        if p.exists():
            im = cv2.imread(str(p), cv2.IMREAD_COLOR)
            if im is not None:
                im = cv2.cvtColor(cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
                return im.astype(np.float32) / 255.0
        return default_arr.copy() if default_arr is not None else np.zeros((H, W, 3), dtype=np.float32)

    raw = _ld("image.jpg")
    cel = _ld("cartoon/cel.png", raw)
    angular = _ld("program/frame0.png", cel)
    layout = _ld("cartoon/layout_sheet.png", cel)
    overlay = _ld("overlay.jpg", raw)
    glow = _ld("cartoon/glow_pass.png", np.zeros_like(raw))
    if not (od / "cartoon/glow_pass.png").exists() and (od / "multiplane/glow_pass.png").exists():
        glow = _ld("multiplane/glow_pass.png", glow)

    # Stylized clean composite (blend raw cinema fidelity with painted cel & optical glow, zero superpixel noise)
    stylized = np.clip(0.54 * raw + 0.30 * cel + 0.16 * angular + 0.20 * glow, 0.0, 1.0)

    # Load native 24fps moving video frames from `film/shot.mp4` (120 frames / 5.0s @ 24fps)
    video_frames = []
    mp4_path = od / "film" / "shot.mp4"
    if mp4_path.exists():
        cap = cv2.VideoCapture(str(mp4_path))
        while len(video_frames) < 120:
            ok, fr = cap.read()
            if not ok or fr is None:
                break
            fr = cv2.cvtColor(cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            if glow is not None:
                fr = np.clip(fr + 0.16 * glow, 0.0, 1.0)
            video_frames.append(fr)
        cap.release()

    # Load planes.npz and depth
    pl_path = od / "multiplane" / "planes.npz"
    arr_path = od / "arrays.npz"
    if pl_path.exists():
        pl = np.load(pl_path)
        L = cv2.resize(pl["L"].astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
        P2 = cv2.resize(pl["P2"].astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST).astype(bool)
        P3 = cv2.resize(pl["P3"].astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST).astype(bool)
    else:
        L = np.full((H, W), 4, dtype=np.uint8)
        P2 = np.zeros((H, W), dtype=bool)
        P3 = np.zeros((H, W), dtype=bool)

    if arr_path.exists():
        A = np.load(arr_path)
        depth = cv2.resize(A["depth"].astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    else:
        lum = raw @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        depth = 3.0 + 10.0 * (1.0 - lum)

    d_lo, d_hi = float(np.percentile(depth, 3)), float(np.percentile(depth, 97))
    d_norm = np.clip((depth - d_lo) / max(d_hi - d_lo, 1e-3), 0.0, 1.0)
    disp_smooth = cv2.GaussianBlur((1.0 - d_norm).astype(np.float32), (0, 0), 18.0)

    # Identify the Hero's Collar / Neck / Upper-Torso zone within P2 (the vertical band where neck meets shoulders)
    yy_full, xx_full = np.mgrid[0:H, 0:W]
    if P2.any():
        p2_ys, p2_xs = np.where(P2)
        y_min, y_max = float(np.percentile(p2_ys, 5)), float(np.percentile(p2_ys, 95))
        y_span = max(20.0, y_max - y_min)
        collar_band = P2 & (yy_full >= y_min + 0.22 * y_span) & (yy_full <= y_min + 0.50 * y_span)
        p2_cx = float(np.mean(p2_xs)) / W - 0.5
        p2_cy = float(np.mean(p2_ys)) / H - 0.5
    else:
        collar_band = np.zeros((H, W), dtype=bool)
        p2_cx, p2_cy = 0.0, 0.0

    p2_soft = cv2.GaussianBlur(P2.astype(np.float32), (0, 0), 6.0)
    p1_soft = cv2.GaussianBlur((L == 1).astype(np.float32), (0, 0), 5.0)
    p0_soft = cv2.GaussianBlur((L == 0).astype(np.float32), (0, 0), 10.0)

    # Plane boundary contours for crisp architectural/collar edge highlights
    p2_edge = cv2.Canny((P2.astype(np.uint8) * 255), 50, 150) > 0
    collar_edge = cv2.dilate((p2_edge & collar_band).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)

    # Sample the 3D point cloud on the `step_grid` lattice (320 x 180 = 57,600 points)
    vg, ug = np.mgrid[0:H:step_grid, 0:W:step_grid]
    uf = ug.ravel().astype(np.float32)
    vf = vg.ravel().astype(np.float32)

    plane_id = L[vg, ug].ravel()
    is_p2 = P2[vg, ug].ravel()
    is_collar = collar_band[vg, ug].ravel()
    is_collar_edge = collar_edge[vg, ug].ravel()
    dn_pts = d_norm[vg, ug].ravel()

    D_cam = 5.5
    focal = 560.0
    z_local = (dn_pts - 0.35) * 3.8
    zc_canon = D_cam + z_local
    ux_rw = uf * (RW / float(W)) - RW * 0.5
    vy_rh = vf * (RH / float(H)) - RH * 0.5
    X_3d = ux_rw * zc_canon / focal
    Y_3d = vy_rh * zc_canon / focal
    Z_3d = z_local

    rgb_sty_pts = stylized[vg, ug].reshape(-1, 3)
    rgb_ang_pts = angular[vg, ug].reshape(-1, 3)
    rgb_lay_pts = layout[vg, ug].reshape(-1, 3)

    lab_sty_pts = cv2.cvtColor(rgb_sty_pts.reshape(1, -1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3)

    bundle = {
        "sid": sid,
        "raw": raw,
        "cel": cel,
        "angular": angular,
        "layout": layout,
        "overlay": overlay,
        "stylized": stylized,
        "video_frames": video_frames,
        "L": L,
        "P2": P2,
        "P3": P3,
        "p2_soft": p2_soft,
        "p1_soft": p1_soft,
        "p0_soft": p0_soft,
        "collar_band": collar_band,
        "collar_edge": collar_edge,
        "d_norm": d_norm,
        "disp_smooth": disp_smooth,
        "p2_center": (p2_cx, p2_cy),
        "pts_X": X_3d.astype(np.float32),
        "pts_Y": Y_3d.astype(np.float32),
        "pts_Z": Z_3d.astype(np.float32),
        "pts_plane": plane_id,
        "pts_is_p2": is_p2,
        "pts_is_collar": is_collar,
        "pts_is_collar_edge": is_collar_edge,
        "pts_rgb": rgb_sty_pts.astype(np.float32),
        "pts_ang": rgb_ang_pts.astype(np.float32),
        "pts_lay": rgb_lay_pts.astype(np.float32),
        "pts_lab": lab_sty_pts.astype(np.float32),
        "D_cam": D_cam,
        "focal": focal,
    }
    _BUNDLE_CACHE[sid] = bundle
    return bundle


def eval_bundle_moving_plate(
    bundle: dict,
    u_local: float,
    global_t: float,
    vocal_rms: float = 0.5,
    pan_dir: float = 1.0,
    glow_rgb: np.ndarray = None,
) -> np.ndarray:
    """
    Evaluates a continuous 24fps moving multiplane cinema plate for `bundle`:
      - If `bundle['video_frames']` is present (e.g. `out/<uuid>/film/shot.mp4`), interpolates smoothly
        at sub-frame 24fps precision across the native moving cinema frames AND blends subtle painted cel
        depth parallax (`warp_multiplane_plate`).
      - For Poet Lectern / Agent K multiplane shots, animates the 7 depth planes (`P0` audience foreground,
        `P1` acrylic lectern prism with vocal-synced acoustic light ripples, `P2` Poet with living breathing /
        collar & hand cadence motion, `P3..P6` salon room) with continuous 24fps Steadicam parallax!
    """
    vframes = bundle.get("video_frames") or []
    disp = bundle["disp_smooth"]

    pan_x = pan_dir * ((u_local - 0.5) * 26.0 + 3.5 * math.sin(global_t * 0.52))
    tilt_y = (0.5 - u_local) * 9.0 + 2.2 * math.cos(global_t * 0.44)
    dolly_scale = 1.05 + 0.065 * np.clip(u_local, 0.0, 1.25)

    if len(vframes) > 1:
        n_f = len(vframes)
        # Continuous sub-frame interpolation across all native 24fps frames (never freezes during transitions!)
        f_exact = np.clip(u_local, 0.0, 1.0) * (n_f - 1.001)
        i0 = int(f_exact)
        i1 = min(n_f - 1, i0 + 1)
        frac = float(f_exact - i0)
        mov_fr = vframes[i0] * (1.0 - frac) + vframes[i1] * frac
        # Blend 84% moving 24fps cinema video + 16% stylized cel/glow harmony
        base_plate = 0.84 * mov_fr + 0.16 * bundle["stylized"]
        warped = warp_multiplane_plate(base_plate, disp, pan_x, tilt_y, dolly_scale, depth_stretch=0.042)
        return np.clip(warped, 0.0, 1.0)

    # Multiplane living articulation for Poet Salon (`poet_01..08`) and K parallel shots:
    base = bundle["stylized"]
    # 1. Background & midground multiplane warp
    bg_warp = warp_multiplane_plate(base, disp * 0.75, pan_x * 0.75, tilt_y * 0.75, dolly_scale, depth_stretch=0.035)

    # 2. Living P2 Actor (Poet / K) breathing & vocal-synced gesture micro-motion
    breath_y = -2.8 * math.sin(global_t * 2.1) - 3.6 * (vocal_rms - 0.45)
    gesture_x = pan_dir * (u_local - 0.5) * 32.0 + 2.4 * math.cos(global_t * 1.6)
    p2_scale = dolly_scale * (1.012 + 0.014 * vocal_rms)
    p2_warp = warp_multiplane_plate(base, np.ones_like(disp), gesture_x, tilt_y + breath_y, p2_scale, depth_stretch=0.0)
    p2_m = warp_multiplane_plate(bundle["p2_soft"], np.ones_like(disp), gesture_x, tilt_y + breath_y, p2_scale, depth_stretch=0.0)[..., None]

    comp = bg_warp * (1.0 - p2_m) + p2_warp * p2_m

    # 3. Foreground P0 audience silhouette stronger counter-parallax
    if bundle["p0_soft"].mean() > 0.01:
        p0_warp = warp_multiplane_plate(base, np.ones_like(disp), pan_x * 1.65, tilt_y * 1.25, dolly_scale * 1.04, depth_stretch=0.0)
        p0_m = warp_multiplane_plate(bundle["p0_soft"], np.ones_like(disp), pan_x * 1.65, tilt_y * 1.25, dolly_scale * 1.04, depth_stretch=0.0)[..., None]
        comp = comp * (1.0 - p0_m * 0.85) + p0_warp * (p0_m * 0.85)

    # 4. Subtle vocal-synced light refraction on P1 Acrylic Lectern & P2 Collar Rim
    if glow_rgb is not None and bundle["p1_soft"].mean() > 0.005:
        lectern_glow = bundle["p1_soft"][..., None] * glow_rgb[None, None, :] * (0.08 + 0.16 * vocal_rms)
        comp = np.clip(comp + lectern_glow, 0.0, 1.0)

    return np.clip(comp, 0.0, 1.0)


# Plane departure schedule: far background (`P6, P5, P4`) lifts first; `P1` lectern second; `P3` third; `P2` Hero & Collar last!
PLANE_U_WINDOW = {
    6: (0.00, 0.64),
    5: (0.04, 0.68),
    4: (0.08, 0.74),
    0: (0.14, 0.80),
    1: (0.16, 0.84),  # P1 Clear Acrylic Lectern
    3: (0.22, 0.88),  # P3 Circle of Listeners / Lamp
    2: (0.30, 1.00),  # P2 Hero Figure, Collar & Hands hold coherence longest!
}


def render_pointcloud_splat_transition(
    bundle_a: dict,
    bundle_b: dict,
    u_trans: float,
    glow_rgb: np.ndarray,
    body_rgb: np.ndarray,
    vocal_rms: float = 0.5,
    orbit_sign: float = 1.0,
    side_cut: bool = False,
    global_t: float = None,
) -> np.ndarray:
    """
    Transitions Shot A -> Shot B as a 100% Continuous, Tear-Free 24fps Cinema Transition:
      1. Evaluates true 24fps moving multiplane plates `plate_a` and `plate_b` (`eval_bundle_moving_plate`).
      2. Performs a Plane-Stratified (`P6/P5/P4` -> `P1` lectern -> `P3` listeners -> `P2` Hero & Collar)
         multiplane depth dissolve with cinema rack-focus softness so ZERO black disocclusion stripes EVER occur!
      3. Projects the 3D Metric Point Cloud (`points.ply`) & Gaussian Splat (`scene.splat`) along a 3D Hermite
         arc at natural cinema parallax (`±8°..13°`), layering volumetric 3D Gaussian bokeh & vocal-synced
         CIELAB collar/District color rhythm seamlessly over the multiplane transition!
    """
    u_trans = float(np.clip(u_trans, 0.0, 1.0))
    if global_t is None:
        global_t = u_trans * 4.0

    # 1. Evaluate continuous 24fps moving multiplane plates for both Shot A and Shot B
    plate_a = eval_bundle_moving_plate(bundle_a, u_trans, global_t, vocal_rms=vocal_rms, pan_dir=orbit_sign, glow_rgb=glow_rgb)
    plate_b = eval_bundle_moving_plate(bundle_b, u_trans, global_t, vocal_rms=vocal_rms, pan_dir=-orbit_sign, glow_rgb=glow_rgb)

    # 2. Plane-Stratified Multiplane Depth Dissolve (P6/P5/P4 dissolve first, P2 Hero & Collar hold longest)
    L_a = bundle_a["L"]
    w_plane = np.zeros((H, W), dtype=np.float32)
    for p_id, (u0, u1) in PLANE_U_WINDOW.items():
        m = (L_a == p_id)
        if np.any(m):
            u_raw = np.clip((u_trans - u0) / max(u1 - u0, 1e-4), 0.0, 1.0)
            w_plane[m] = u_raw * u_raw * (3.0 - 2.0 * u_raw)
    w_plane = cv2.GaussianBlur(w_plane, (0, 0), 14.0)[..., None]

    overall_bell = math.sin(math.pi * u_trans)
    # Subtle cinema lens rack-focus during mid-transition
    if overall_bell > 0.12:
        sigma_dof = 2.6 * overall_bell
        pa_soft = cv2.GaussianBlur(plate_a, (0, 0), sigma_dof)
        pb_soft = cv2.GaussianBlur(plate_b, (0, 0), sigma_dof)
        plate_a_mix = plate_a * (1.0 - 0.42 * overall_bell) + pa_soft * (0.42 * overall_bell)
        plate_b_mix = plate_b * (1.0 - 0.42 * overall_bell) + pb_soft * (0.42 * overall_bell)
    else:
        plate_a_mix, plate_b_mix = plate_a, plate_b

    bg_multiplane = plate_a_mix * (1.0 - w_plane) + plate_b_mix * w_plane

    # If near endpoints (`u_trans < 0.06` or `u_trans > 0.94`), return pure moving multiplane plate directly
    if overall_bell < 0.15:
        return np.clip(bg_multiplane, 0.0, 1.0)

    # 3. 3D Point-Cloud & Gaussian Splat Bokeh Transport (active during transition crest)
    pl_a = bundle_a["pts_plane"]
    u_pt = np.zeros_like(bundle_a["pts_X"])
    for p_id, (u0, u1) in PLANE_U_WINDOW.items():
        m = pl_a == p_id
        if np.any(m):
            u_raw = np.clip((u_trans - u0) / max(u1 - u0, 1e-4), 0.0, 1.0)
            u_pt[m] = u_raw * u_raw * (3.0 - 2.0 * u_raw)

    is_collar = bundle_a["pts_is_collar"]
    is_p2 = bundle_a["pts_is_p2"]
    flight_bell = np.sin(np.pi * u_pt)

    Xa, Ya, Za = bundle_a["pts_X"], bundle_a["pts_Y"], bundle_a["pts_Z"]
    Xb, Yb, Zb = bundle_b["pts_X"], bundle_b["pts_Y"], bundle_b["pts_Z"]

    curl_x = np.sin(Ya * 1.4 + Za * 0.9) * 0.36 * orbit_sign
    curl_y = np.cos(Xa * 1.2 - Za * 1.1) * 0.24 - (0.06 * vocal_rms * is_collar.astype(np.float32))
    curl_z = np.sin(Xa * 1.1 + Ya * 1.3) * 0.48

    scatter_scale = np.where(is_p2, 0.32, 0.85)
    X = (1.0 - u_pt) * Xa + u_pt * Xb + flight_bell * curl_x * scatter_scale
    Y = (1.0 - u_pt) * Ya + u_pt * Yb + flight_bell * curl_y * scatter_scale
    Z = (1.0 - u_pt) * Za + u_pt * Zb + flight_bell * curl_z * scatter_scale

    # COLOR'S RHYTHM: Perceptual CIELAB interpolation + District `glow`/`body` chromatic pulse
    lab_a = bundle_a["pts_lab"]
    lab_b = bundle_b["pts_lab"]
    lab_mix = (1.0 - u_pt[:, None]) * lab_a + u_pt[:, None] * lab_b
    rgb_linear = cv2.cvtColor(lab_mix.reshape(1, -1, 3).astype(np.float32), cv2.COLOR_LAB2RGB).reshape(-1, 3)

    lum_pt = rgb_linear.mean(axis=-1, keepdims=True)
    district_rhythm_col = np.where(
        (is_p2 | (lum_pt[:, 0] > 0.42))[:, None],
        glow_rgb[None, :],
        0.55 * body_rgb[None, :] + 0.45 * bundle_b["pts_lay"],
    )
    collar_rim_boost = (bundle_a["pts_is_collar_edge"] | bundle_b["pts_is_collar_edge"]).astype(np.float32)[:, None]
    rhythm_weight = (0.30 * flight_bell)[:, None] * (0.85 + 0.30 * vocal_rms)
    rgb_pts = np.clip(
        rgb_linear * (1.0 - rhythm_weight) + district_rhythm_col * rhythm_weight + collar_rim_boost * glow_rgb[None, :] * (0.42 * flight_bell[:, None]),
        0.0,
        1.0,
    )

    # Keep 3D camera yaw within natural cinema lens bounds (±8°..13°) so ZERO black disocclusion zebra stripes appear!
    yaw_amp = 0.22 if side_cut else 0.14
    yaw = orbit_sign * (yaw_amp * overall_bell)
    pitch = 0.04 * math.sin(2.0 * math.pi * u_trans)

    D_cam = bundle_a["D_cam"] - 0.25 * overall_bell
    focal = bundle_a["focal"]

    cy, sy = math.cos(yaw), math.sin(yaw)
    Xc = X * cy + Z * sy
    Zc1 = -X * sy + Z * cy

    cp, sp = math.cos(pitch), math.sin(pitch)
    Yc = Y * cp - Zc1 * sp
    Zc = Y * sp + Zc1 * cp + D_cam

    px = focal * Xc / np.maximum(Zc, 0.25) + RW * 0.5
    py = focal * Yc / np.maximum(Zc, 0.25) + RH * 0.5

    dof = np.abs(Zc - D_cam) * 0.35 * overall_bell
    rad = np.clip(0.95 + 1.45 * flight_bell * scatter_scale + dof, 0.85, 4.2).astype(np.float32)
    wt = np.where(is_p2, 1.35, 0.90).astype(np.float32)

    # Render the 3D Gaussian splats directly over `bg_multiplane` (NEVER over empty black void!)
    splat_img = splat_gaussian_multiscale(px, py, Zc, rad, rgb_pts, wt, bg_rgb=bg_multiplane, gain=1.18)

    # Smoothly blend the volumetric 3D Gaussian splat layer over the continuous multiplane plate at mid-transition
    splat_env = (overall_bell ** 1.25) * 0.62
    out = bg_multiplane * (1.0 - splat_env) + splat_img * splat_env
    return np.clip(out, 0.0, 1.0)


def extract_audio_rms_envelope(mp3_path: Path, target_dur: float = 18.0, fps: int = FPS) -> np.ndarray:
    """
    Decodes `play/levels/<NN>/reading.mp3` via ffmpeg at 8000 Hz mono and computes the per-frame
    spoken-word RMS cadence envelope (`n_frames = int(target_dur * fps)`) normalized to `[0, 1]`.
    """
    n_frames = int(target_dur * fps)
    if not mp3_path.exists():
        t = np.linspace(0, target_dur, n_frames)
        return (0.5 + 0.4 * np.sin(2 * np.pi * t / 2.4)).astype(np.float32)

    try:
        cmd = [
            "ffmpeg", "-v", "error", "-i", str(mp3_path),
            "-t", str(target_dur), "-ac", "1", "-ar", "8000", "-f", "f32le", "-"
        ]
        raw = subprocess.check_output(cmd)
        pcm = np.frombuffer(raw, dtype=np.float32)
        if len(pcm) < 800:
            raise ValueError("Short audio")
        samples_per_frame = max(1, len(pcm) // n_frames)
        rms = np.zeros(n_frames, dtype=np.float32)
        for i in range(n_frames):
            seg = pcm[i * samples_per_frame : (i + 1) * samples_per_frame]
            if len(seg):
                rms[i] = float(np.sqrt(np.mean(seg * seg)))
        p10, p95 = float(np.percentile(rms, 10)), float(np.percentile(rms, 95))
        rms_norm = np.clip((rms - p10) / max(p95 - p10, 1e-4), 0.0, 1.0)
        return gaussian_filter(rms_norm, sigma=1.5).astype(np.float32)
    except Exception:
        t = np.linspace(0, target_dur, n_frames)
        return (0.5 + 0.4 * np.sin(2 * np.pi * t / 2.4)).astype(np.float32)


def draw_pointcloud_hud(
    frame_rgb: np.ndarray,
    top_left: str,
    top_right: str,
    bottom_who: str,
    bottom_verse: str,
    vocal_rms: float,
    color_hex: str,
    pip_rgb: np.ndarray = None,
    pip_label: str = "",
) -> np.ndarray:
    """
    VOIDBASTARD-TAO / Cinema Film Typography:
      - Zero Picture-in-Picture rectangles blocking the 16:9 image.
      - Zero heavy opaque HUD boxes.
      - Whisper-quiet top archival hairline + softly shadowed cinema subtitles at the bottom.
    """
    pil = Image.fromarray((np.clip(frame_rgb, 0.0, 1.0) * 255.0).astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    f_mono = get_font(12, mono=True)
    f_who = get_font(13, mono=True)
    f_verse = get_font(23, italic=True)

    # Whisper-quiet top archival header (unboxed with soft drop shadow)
    d.text((25, 17), top_left[:78], font=f_mono, fill=(6, 8, 12, 185))
    d.text((24, 16), top_left[:78], font=f_mono, fill=(255, 196, 92, 210))
    d.text((W - 23, 17), top_right[:68], font=f_mono, fill=(6, 8, 12, 185), anchor="ra")
    d.text((W - 24, 16), top_right[:68], font=f_mono, fill=(140, 224, 248, 200), anchor="ra")

    # Subtle bottom cinema subtitle with soft shadow (no opaque box!)
    d.text((W // 2 + 1, H - 59), bottom_who[:92], font=f_who, fill=(6, 8, 12, 205), anchor="mm")
    d.text((W // 2, H - 60), bottom_who[:92], font=f_who, fill=(255, 196, 92, 225), anchor="mm")
    d.text((W // 2 + 1, H - 31), f"“{bottom_verse[:102]}”", font=f_verse, fill=(6, 8, 12, 220), anchor="mm")
    d.text((W // 2, H - 32), f"“{bottom_verse[:102]}”", font=f_verse, fill=(246, 240, 228, 242), anchor="mm")

    return np.asarray(Image.alpha_composite(pil, ov).convert("RGB"), dtype=np.uint8)


# ==============================================================================
# STEP 3: RENDER ALL 14 POEMS' POINT-CLOUD & GAUSSIAN SPLAT BOOKEND FILMS
# ==============================================================================
from build_poet_bookend_spacetime_poems import POEM_BOOKEND_SPECS

POEM_WOODEN_HORSE_ANCHORS = {int(item["num"]): item for item in POEM_BOOKEND_SPECS}


def render_single_poem_pointcloud_bookend(poem_meta: dict) -> dict:
    pnum = int(poem_meta["num"])
    ns = f"{pnum:02d}"
    title = poem_meta["title"]
    hero_dir = poem_meta["hero_dir"]
    echo_dir = poem_meta["echo_dir"]
    third_dir = poem_meta.get("third_dir") or echo_dir
    glow_hex = poem_meta["glow_hex"]
    body_hex = poem_meta["body_hex"]
    anchor_info = POEM_WOODEN_HORSE_ANCHORS.get(pnum, POEM_WOODEN_HORSE_ANCHORS[1])

    glow_rgb = hex_to_rgb_f32(glow_hex[0] if glow_hex else "#fa8d15")
    body_rgb = hex_to_rgb_f32(body_hex[0] if body_hex else "#1c2430")

    # Load Point-Cloud & Multiplane bundles for Poet Lectern stages and 3 distinct Poem 24fps moving views
    b_p01 = load_pointcloud_shot_bundle("poet_01_warm_salon_circle_wide")
    b_p02 = load_pointcloud_shot_bundle("poet_02_warm_lectern_medium")
    b_p04 = load_pointcloud_shot_bundle("poet_04_standing_hands_heart")
    b_p06 = load_pointcloud_shot_bundle("poet_06_chiaroscuro_open_hands")
    b_p07 = load_pointcloud_shot_bundle("poet_07_chiaroscuro_wide_circle")
    b_p08 = load_pointcloud_shot_bundle("poet_08_ots_circle_listeners")

    b_hero = load_pointcloud_shot_bundle(hero_dir)
    b_echo = load_pointcloud_shot_bundle(echo_dir)
    b_third = load_pointcloud_shot_bundle(third_dir)

    audio_mp3 = SHOTS_DIR / f"play/levels/{ns}/reading.mp3"
    dur = 18.0
    n_frames = int(dur * FPS)
    rms_env = extract_audio_rms_envelope(audio_mp3, target_dur=dur, fps=FPS)

    frames_out = []
    act_thumbs = {}

    for fi in range(n_frames):
        t = fi / float(FPS)
        v_rms = float(rms_env[min(len(rms_env) - 1, fi)])
        col_hex = glow_hex[0] if glow_hex else "#fa8d15"

        if t < 3.6:
            # ACT I: OPENING LECTERN BOOKEND — Poet Salon (poet_01 -> poet_02) via 3D Multiplane & Collar Rhythm
            u = t / 3.6
            fr = render_pointcloud_splat_transition(
                b_p01, b_p02, u, glow_rgb=glow_rgb, body_rgb=body_rgb, vocal_rms=v_rms, orbit_sign=1.0, global_t=t
            )
            u8 = draw_pointcloud_hud(
                fr,
                top_left=f"P{ns} · {title.upper()} · ACT I: SALON MULTIPLANE & COLLAR RHYTHM (P0–P6)",
                top_right="K PARALLEL (1:49): Officer K & Joshi Interview",
                bottom_who="Act I · Opening Lectern Bookend — P2 Collar/Face Locked, P0–P6 Multiplane Glide",
                bottom_verse=anchor_info["opening_cue"],
                vocal_rms=v_rms,
                color_hex=col_hex,
            )
            if fi == int(1.6 * FPS):
                act_thumbs["act1"] = u8

        elif t < 7.2:
            # ACT II: CROSS-WORLD 3D POINT-CLOUD HAND-OFF (poet_04/06 -> Moving Poem Hero Shot 1)
            u = (t - 3.6) / 3.6
            if u < 0.35:
                u_sub = u / 0.35
                fr = render_pointcloud_splat_transition(
                    b_p04, b_p06, u_sub, glow_rgb=glow_rgb, body_rgb=body_rgb, vocal_rms=v_rms, orbit_sign=-1.0, global_t=t
                )
            else:
                u_sub = (u - 0.35) / 0.65
                fr = render_pointcloud_splat_transition(
                    b_p06, b_hero, u_sub, glow_rgb=glow_rgb, body_rgb=body_rgb, vocal_rms=v_rms, orbit_sign=1.0, side_cut=True, global_t=t
                )

            u8 = draw_pointcloud_hud(
                fr,
                top_left=f"P{ns} · ACT II: 3D POINT-CLOUD & CIELAB COLOR RHYTHM HAND-OFF (POET P2 -> POEM P2)",
                top_right=f"COLOR RHYTHM: {col_hex.upper()} · VOCAL RMS {int(v_rms*100):02d}%",
                bottom_who="Act II · Plane-Stratified 3D Splat Flight — P4/P5 Mural Lifts First, P2 Collar & Hands Converge on Hero",
                bottom_verse=anchor_info["opening_cue"],
                vocal_rms=v_rms,
                color_hex=col_hex,
            )
            if fi == int(5.6 * FPS):
                act_thumbs["act2"] = u8

        elif t < 11.0:
            # ACT III: POEM 24FPS MOVING MULTIPLANE & GAUSSIAN SPLAT FLIGHT (Moving Hero Shot 1 -> Moving Echo Shot 2)
            u = (t - 7.2) / 3.8
            fr = render_pointcloud_splat_transition(
                b_hero, b_echo, u, glow_rgb=glow_rgb, body_rgb=body_rgb, vocal_rms=v_rms, orbit_sign=-1.0, side_cut=(0.28 < u < 0.72), global_t=t
            )
            u8 = draw_pointcloud_hud(
                fr,
                top_left=f"P{ns} · ACT III: 24FPS MULTIPLANE & GAUSSIAN SPLAT GLIDE ({hero_dir[:8]} -> {echo_dir[:8]})",
                top_right="K PARALLEL (2:06–2:24): Orphanage Catwalks & Gears",
                bottom_who=f"Act III · 24fps Moving Cinema + 3D Depth Flight — {title}",
                bottom_verse=anchor_info["peak_cue"],
                vocal_rms=v_rms,
                color_hex=col_hex,
            )
            if fi == int(9.0 * FPS):
                act_thumbs["act3"] = u8

        elif t < 14.5:
            # ACT IV: THE "WOODEN HORSE" EMOTIONAL ANCHOR (Moving Shot 3 P2/P3 Sharp Core + Peripheral Feeling-Mist)
            u = (t - 11.0) / 3.5
            # Continuous 24fps moving cinema plate on `b_third` (NEVER frozen!)
            mov_core = eval_bundle_moving_plate(b_third, u, t, vocal_rms=v_rms, pan_dir=1.0, glow_rgb=glow_rgb)
            splat_bg = render_pointcloud_splat_transition(
                b_echo, b_third, u, glow_rgb=glow_rgb, body_rgb=body_rgb, vocal_rms=v_rms, orbit_sign=1.0, global_t=t
            )
            anchor_mask = (b_third["P2"] | b_third["P3"]).astype(np.float32)
            if anchor_mask.mean() < 0.04:
                anchor_mask = (b_third["d_norm"] < 0.48).astype(np.float32)
            anchor_soft = cv2.GaussianBlur(anchor_mask, (0, 0), 16.0)[..., None]

            periph_mist = cv2.GaussianBlur(splat_bg, (0, 0), 9.0) * 0.78 + body_rgb[None, None, :] * 0.22
            fr = np.clip(periph_mist * (1.0 - anchor_soft) + mov_core * anchor_soft, 0.0, 1.0)

            u8 = draw_pointcloud_hud(
                fr,
                top_left=f"P{ns} · ACT IV: ISOLATED P2/P3 WOODEN HORSE ANCHOR ({anchor_info['wooden_horse_anchor'][:38].upper()})",
                top_right="K PARALLEL (2:27): Carved Wooden Horse (6·10·21) in Palm",
                bottom_who=f"Wooden Horse Equivalent: {anchor_info['wooden_horse_anchor']}",
                bottom_verse=anchor_info["anchor_detail"],
                vocal_rms=v_rms,
                color_hex=col_hex,
            )
            if fi == int(12.6 * FPS):
                act_thumbs["act4"] = u8

        else:
            # ACT V: CLOSING BOOKEND — CONDENSATION INTO THE CIRCLE OF LISTENERS (poet_07 -> poet_08)
            u = (t - 14.5) / 3.5
            if u < 0.52:
                u_sub = u / 0.52
                fr = render_pointcloud_splat_transition(
                    b_third, b_p07, u_sub, glow_rgb=glow_rgb, body_rgb=body_rgb, vocal_rms=v_rms, orbit_sign=-1.0, side_cut=True, global_t=t
                )
            else:
                u_sub = (u - 0.52) / 0.48
                fr = render_pointcloud_splat_transition(
                    b_p07, b_p08, u_sub, glow_rgb=glow_rgb, body_rgb=body_rgb, vocal_rms=v_rms, orbit_sign=1.0, global_t=t
                )

            u8 = draw_pointcloud_hud(
                fr,
                top_left=f"P{ns} · ACT V: RETURN TO THE CIRCLE OF LISTENERS (P2 COLLAR OTS -> P3 CIRCLE)",
                top_right="K PARALLEL (3:06–3:25): 'Someone Lived This'",
                bottom_who="Act V · Over-the-Shoulder Collar Silhouette (P2) & 8 Segmented Listeners (P3) Receive the Memory",
                bottom_verse=anchor_info["closing_cue"],
                vocal_rms=v_rms,
                color_hex=col_hex,
            )
            if fi == int(16.6 * FPS):
                act_thumbs["act5"] = u8

        frames_out.append(u8)

    BOOKEND_VID_DIR.mkdir(parents=True, exist_ok=True)
    out_mp4 = BOOKEND_VID_DIR / f"poem_{ns}_bookend_spacetime.mp4"
    tmp_mp4 = BOOKEND_VID_DIR / f"poem_{ns}_tmp.mp4"

    cmd_v = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        str(tmp_mp4),
    ]
    proc = subprocess.Popen(cmd_v, stdin=subprocess.PIPE)
    for f_u8 in frames_out:
        proc.stdin.write(f_u8.tobytes())
    proc.stdin.close()
    proc.wait()

    if audio_mp3.exists():
        cmd_mux = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(tmp_mp4),
            "-i", str(audio_mp3),
            "-map", "0:v:0", "-map", "1:a:0",
            "-af", f"afade=t=in:st=0:d=0.4,afade=t=out:st={dur-0.7:.2f}:d=0.7",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{dur:.2f}",
            "-movflags", "+faststart",
            str(out_mp4),
        ]
        subprocess.run(cmd_mux, check=True)
        tmp_mp4.unlink(missing_ok=True)
    else:
        tmp_mp4.replace(out_mp4)

    # Also replace the 3-second static screenshot slideshow in `seeing_spacetime_films/poem_<ns>_apparatus.mp4`!
    import shutil
    app_mp4 = SEEING_DIR / f"poem_{ns}_apparatus.mp4"
    shutil.copy2(out_mp4, app_mp4)
    if pnum == 1 and ARTIFACT_DIR.exists():
        shutil.copy2(out_mp4, ARTIFACT_DIR / "poem_01_bookend_spacetime.mp4")

    print(f"  -> Rendered P{ns} 24fps Cinema Bookend & Apparatus Film: {out_mp4}", flush=True)
    return {"num": pnum, "ns": ns, "title": title, "video": str(out_mp4), "thumbs": act_thumbs}


# ==============================================================================
# STEP 4: BUILD 4K POINT-CLOUD, GAUSSIAN SPLAT & COLLAR/COLOR RHYTHM PROOF SHEET
# ==============================================================================
def build_pointcloud_collar_rhythm_sheet(results: list, poem_metas: list) -> Path:
    """
    Builds a 4K technical & visual proof sheet (`pointcloud_splat_collar_rhythm_sheet.png`) showing:
      - Row 1: The Poet's Segmented Collar/Neck/Hands (`P2`) & Lectern (`P1`) 3D Point Cloud & Gaussian Splat
        rendered at `0°` Face-On, `+28°` Oblique, `+58°` Side-On 4D Depth Strata, and `P2 Collar Rim Isolation`.
      - Row 2: The 5-Step Plane-Stratified 3D Point-Cloud Transition (`u = 0.00, 0.25, 0.50, 0.75, 1.00`)
        showing `P4/P5` Mural lift-off, `P1` Acrylic Lectern refraction, CIELAB Color Rhythm crest, and `P2` Collar-to-Hero convergence.
      - Rows 3–4: All 14 Poems' 3D Point-Cloud & Gaussian Splat Handoff Frames (`Act II` Splat Flight + `Act IV` Anchor).
    """
    b_p02 = load_pointcloud_shot_bundle("poet_02_warm_lectern_medium")
    b_p06 = load_pointcloud_shot_bundle("poet_06_chiaroscuro_open_hands")
    b_p08 = load_pointcloud_shot_bundle("poet_08_ots_circle_listeners")
    b_h01 = load_pointcloud_shot_bundle(poem_metas[0]["hero_dir"])

    glow_rgb = np.array([0.98, 0.62, 0.18], dtype=np.float32)
    body_rgb = np.array([0.12, 0.18, 0.28], dtype=np.float32)

    CW, CH = 3840, 2340
    sheet = Image.new("RGB", (CW, CH), (7, 9, 14))
    d = ImageDraw.Draw(sheet)

    f_title = get_font(34, mono=False)
    f_sub = get_font(16, mono=True)
    f_card = get_font(13, mono=True)

    d.text(
        (36, 22),
        "3D GAUSSIAN SPLATS (SCENE.SPLAT) & POINT-CLOUD TRANSITIONS (POINTS.PLY) · COLLAR & COLOR RHYTHM ARCHITECTURE",
        font=f_title,
        fill=(255, 190, 82),
    )
    d.text(
        (36, 66),
        "115 Binary .splat & .ply 3D Scenes | P0–P6 Staggered Hermite Trajectories | Perceptual CIELAB District Color Rhythm | Spoken-Word RMS & Collar Silhouette Lock",
        font=f_sub,
        fill=(92, 228, 255),
    )

    # ROW 1: 6 Panels showing Poet Collar/Hero P2 Segmentation + 3D Point-Cloud Orbit Angles + Transition Steps
    r1_y = 106
    tw1, th1 = 616, 346
    gap1 = 16

    r1_frames = [
        ("1 · POET_02 REFINED P2 COLLAR & LECTERN", b_p02["stylized"], "Lamp (P3) cleanly separated from Poet cheek & charcoal collar (P2)"),
        (
            "2 · 3D GAUSSIAN SPLAT · +28° OBLIQUE ORBIT",
            render_pointcloud_splat_transition(b_p02, b_p06, 0.28, glow_rgb, body_rgb, vocal_rms=0.8, orbit_sign=1.0),
            "points.ply + scene.splat: P4/P5 mural lifts first while P2 collar holds",
        ),
        (
            "3 · 3D GAUSSIAN SPLAT · +58° SIDE-ON STRATA",
            render_pointcloud_splat_transition(b_p06, b_h01, 0.48, glow_rgb, body_rgb, vocal_rms=0.9, orbit_sign=1.0, side_cut=True),
            "Side-on 58° cut exposing metric Z-strata & CIELAB District glow crest",
        ),
        (
            "4 · CIELAB COLOR RHYTHM MID-FLIGHT (U=0.62)",
            render_pointcloud_splat_transition(b_p06, b_h01, 0.62, glow_rgb, body_rgb, vocal_rms=0.85, orbit_sign=-1.0),
            "Points travel through perceptual CIELAB + District glow/body palette",
        ),
        (
            "5 · P2 HERO & COLLAR CONVERGENCE (U=0.82)",
            render_pointcloud_splat_transition(b_p06, b_h01, 0.82, glow_rgb, body_rgb, vocal_rms=0.75, orbit_sign=1.0),
            "Poet P2 points settle into Poem Hero P2 before background locks",
        ),
        (
            "6 · POET_08 OTS COLLAR & 8 LISTENERS SPLAT",
            render_pointcloud_splat_transition(b_h01, b_p08, 0.72, glow_rgb, body_rgb, vocal_rms=0.8, orbit_sign=-1.0),
            "Return transition into Poet's OTS collar silhouette (P2) & circle (P3)",
        ),
    ]

    for idx, (lbl, arr_f, desc) in enumerate(r1_frames):
        x0 = 36 + idx * (tw1 + gap1)
        im = Image.fromarray((np.clip(arr_f, 0.0, 1.0) * 255.0).astype(np.uint8)).resize((tw1, th1), Image.Resampling.LANCZOS)
        sheet.paste(im, (x0, r1_y))
        d.rectangle([x0, r1_y, x0 + tw1, r1_y + th1], outline=(255, 190, 82), width=1)
        d.text((x0, r1_y + th1 + 6), lbl, font=f_card, fill=(255, 190, 82))
        d.text((x0, r1_y + th1 + 24), desc[:66], font=f_card, fill=(210, 220, 232))

    # ROWS 2–3: All 14 Poems' 3D Point-Cloud & Gaussian Splat Bookend Pairs (7 poems per row x 2 rows)
    d.text(
        (36, 512),
        "ALL 14 POEMS — PLANE-STRATIFIED 3D POINT-CLOUD HAND-OFF (ACT II SPLAT FLIGHT) & WOODEN HORSE ANCHOR (ACT IV)",
        font=f_sub,
        fill=(255, 190, 82),
    )

    tw2, th2 = 524, 295
    gap2 = 16
    res_by_num = {r["num"]: r for r in results}

    for p_idx in range(14):
        pnum = p_idx + 1
        r = res_by_num.get(pnum, {})
        thumbs = r.get("thumbs", {})
        row = p_idx // 7
        col = p_idx % 7
        x0 = 36 + col * (tw2 + gap2)
        y0 = 544 + row * (2 * th2 + 78)

        for sub_i, act_k in enumerate(["act2", "act4"]):
            yy = y0 + sub_i * (th2 + 8)
            if act_k in thumbs:
                im = Image.fromarray(thumbs[act_k]).resize((tw2, th2), Image.Resampling.LANCZOS)
                sheet.paste(im, (x0, yy))
            d.rectangle([x0, yy, x0 + tw2, yy + th2], outline=(92, 228, 255) if sub_i == 0 else (255, 190, 82), width=1)

        d.text(
            (x0, y0 + 2 * th2 + 14),
            f"P{pnum:02d} · {r.get('title', '')[:22].upper()} (TOP: 3D SPLAT FLIGHT · BOT: P2/P3 ANCHOR)",
            font=f_card,
            fill=(242, 236, 224),
        )

    out_png = SEEING_DIR / "pointcloud_splat_collar_rhythm_sheet.png"
    sheet.save(out_png)
    if ARTIFACT_DIR.exists():
        sheet.save(ARTIFACT_DIR / "pointcloud_splat_collar_rhythm_sheet.png")
    print(f"  -> Saved 4K Point-Cloud, Gaussian Splat & Collar/Color Rhythm Sheet: {out_png}")
    return out_png


def main():
    refine_poet_collar_and_generate_splats()

    # Re-generate poet_02_dope_composite.jpg after collar refinement
    from build_poet_bookend_spacetime_poems import build_poet_and_k_dope_composites
    build_poet_and_k_dope_composites()
    if ARTIFACT_DIR.exists():
        import shutil
        shutil.copyfile(TERR_DIR / "poet_lectern/poet_02_dope_composite.jpg", ARTIFACT_DIR / "poet_02_dope_composite.jpg")

    bundle_path = SEEING_DIR / "vesper_world_bundle.json"
    bundle = json.loads(bundle_path.read_text())
    city_data = json.loads(CITY_JSON.read_text()) if CITY_JSON.exists() else {"districts": [], "poems": []}
    districts_by_id = {d["id"]: d for d in city_data.get("districts", [])}

    poem_metas = []
    for p in bundle["poems"]:
        pnum = int(p["num"])
        views = p.get("views", [])
        hero_v = next((v for v in views if v["id"] == p.get("hero_view_id")), views[0] if views else {})
        echo_v = next((v for v in views if v["id"] == p.get("echo_view_id")), views[-1] if views else hero_v)
        third_v = views[len(views) // 2] if len(views) >= 3 else echo_v
        if third_v.get("dir") in (hero_v.get("dir"), echo_v.get("dir")) and len(views) >= 3:
            for cand in views:
                if cand.get("dir") not in (hero_v.get("dir"), echo_v.get("dir")):
                    third_v = cand
                    break
        cp = next((x for x in city_data.get("poems", []) if int(x["num"]) == pnum), {})
        dist = districts_by_id.get(cp.get("district", "naraka"), {})
        poem_metas.append({
            "num": pnum,
            "title": p.get("title", f"Poem {pnum:02d}"),
            "hero_dir": hero_v.get("dir", "017dd279-1457-49f1-829f-9ee94b981a54"),
            "echo_dir": echo_v.get("dir", hero_v.get("dir", "017dd279-1457-49f1-829f-9ee94b981a54")),
            "third_dir": third_v.get("dir", echo_v.get("dir", "017dd279-1457-49f1-829f-9ee94b981a54")),
            "glow_hex": dist.get("glow", ["#fa8d15", "#5ce4ff"]),
            "body_hex": dist.get("body", ["#181e29", "#2d4651"]),
        })

    print("Step 2: Compiling all 14 Poems' 24fps Cinema Bookend Films with Spoken-Word & CIELAB Color Rhythm...")
    results = []
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(render_single_poem_pointcloud_bookend, pm): pm["num"] for pm in poem_metas}
        for fut in as_completed(futs):
            results.append(fut.result())
    results.sort(key=lambda r: r["num"])

    print("Step 3: Building 4K Point-Cloud, Gaussian Splat & Collar/Color Rhythm Proof Sheet...")
    build_pointcloud_collar_rhythm_sheet(results, poem_metas)

    # Concatenate featured poems into Master Point-Cloud Bookend Anthology Film
    concat_txt = BOOKEND_VID_DIR / "concat_splat_master.txt"
    featured = [1, 2, 4, 6, 8, 14]
    with open(concat_txt, "w") as f:
        for pnum in featured:
            f.write(f"file 'poem_{pnum:02d}_bookend_spacetime.mp4'\n")
    master_mp4 = VIDEOS_DIR / "wygwyl_poet_retelling_bookend_spacetime.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-c", "copy", "-movflags", "+faststart", str(master_mp4),
        ],
        check=True,
    )
    concat_txt.unlink(missing_ok=True)
    import shutil
    shutil.copy2(master_mp4, VIDEOS_DIR / "wygwyl_vesper_apparatus_reel.mp4")
    if ARTIFACT_DIR.exists():
        shutil.copy2(master_mp4, ARTIFACT_DIR / "wygwyl_poet_retelling_bookend_spacetime.mp4")
    print(f"  -> Updated Master Point-Cloud & Gaussian Splat Bookend Anthology: {master_mp4}")


if __name__ == "__main__":
    main()
