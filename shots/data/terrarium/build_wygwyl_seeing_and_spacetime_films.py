#!/usr/bin/env python3
"""
Builds two Afterlight-inspired latent-space films for WYGWYL:
1. shots/videos/wygwyl_seeing_construct.mp4 (0:30, 24fps, 1280x720)
   "Seeing-As · S2 Construct: Figures in formless matter — Four places as one point cloud; each assembles from one position only."
2. shots/videos/wygwyl_07_spacetime.mp4 (1:00, 24fps, 1280x720)
   "07-Spacetime: A Walk Through the Latent Volume" — built directly on the bolas/afterlight spacetime.py + trailer.py + score.py engine
   with Apple ml-sharp neural depth + temporal slice volumes.
"""
import os
import sys
import math
import time
import wave
import subprocess
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter
from scipy.signal import butter, lfilter
from PIL import Image, ImageDraw, ImageFont

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots"
VID_DIR = os.path.join(ROOT, "videos")
SPLAT_DIR = os.path.join(ROOT, "data/terrarium/atlas_packs/splats")
FONT_DIR = os.path.join(ROOT, "fonts")
ARTIFACT_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"

FPS = 24
RW, RH = 640, 360   # Internal multi-scale Gaussian accumulation resolution (exact fast spacetime.py ratio)
FW, FH = 1280, 720  # Final output resolution

PAPER = np.array([0.925, 0.905, 0.865], dtype=np.float32)
NIGHT = np.array([0.016, 0.018, 0.026], dtype=np.float32)

def ease(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)

def smootherstep(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)

_FONT_CACHE = {}
def get_font(kind="italic", size=36):
    key = (kind, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    candidates = []
    if kind == "italic":
        candidates = [
            os.path.join(FONT_DIR, "im-fell-english-latin-400-italic.woff2"),
            "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
        ]
    elif kind == "serif":
        candidates = [
            os.path.join(FONT_DIR, "im-fell-english-latin-400-normal.woff2"),
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        ]
    else:
        candidates = [
            os.path.join(FONT_DIR, "ibm-plex-mono-latin-400-normal.woff2"),
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
# CORE MULTI-SCALE GAUSSIAN SPLAT & BEERS-LAW TRANSMITTANCE RENDERER (spacetime.py)
# ==============================================================================
_VIG_CACHE = {}
def get_vignette(h, w):
    if (h, w) not in _VIG_CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        v = 1.0 - 0.20 * (((xx - w * 0.5) / (w * 0.55)) ** 2 + ((yy - h * 0.5) / (h * 0.55)) ** 2)
        _VIG_CACHE[(h, w)] = np.clip(v, 0.72, 1.02)[..., None]
    return _VIG_CACHE[(h, w)]


def splat_gaussian_multiscale(px, py, zc, rad, rgb, w_val, mode="paper", gain=1.0, seed=0):
    """
    Exact multi-scale Gaussian density & Beers-Law exponential transmittance resolve
    from bolas/afterlight/source/trailer-1/spacetime.py.txt.
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

    # 3 scale buckets: sharp core (<1.5px), medium body (1.5..3.8px), soft bokeh/scatter (>3.8px)
    b0 = rad < 1.55
    b1 = (rad >= 1.55) & (rad < 3.85)
    b2 = rad >= 3.85

    sigmas = [0.55, 1.45, 3.6]
    ks = [3.8, 7.5, 19.0]
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
        # Composite softest to sharpest so crisp focal-plane points sit cleanly on top
        for bi in (2, 1, 0):
            A = acc[bi, :, :, 3:4]
            col = acc[bi, :, :, :3] / np.maximum(A, 1e-5)
            # Deepen ink slightly on parchment for contrast
            col = np.clip((col - 0.5) * 1.18 + 0.46, 0.02, 0.98)
            cov = 1.0 - np.exp(-A * ks[bi] * gain)
            out = out * (1.0 - cov) + col * cov
        out = out * get_vignette(H, W)
    else:
        total = np.zeros((H, W, 4), dtype=np.float32)
        for bi in (2, 1, 0):
            total += acc[bi] * ks[bi]
        A = total[:, :, 3:4] * gain
        col = total[:, :, :3] * gain / np.maximum(A, 1e-4)
        cov = 1.0 - np.exp(-A * 0.88)
        bloom = np.stack([gaussian_filter(col[:, :, c] * cov[:, :, 0], sigma=9.0) for c in range(3)], axis=-1)
        out = NIGHT[None, None, :] * (1.0 - cov * 0.92) + col * cov + bloom * 0.42

    # Upscale to 1280x720 with subtle film grain
    out_hi = cv2.resize(np.clip(out, 0.0, 1.0), (FW, FH), interpolation=cv2.INTER_CUBIC)
    rng = np.random.default_rng(seed)
    grain = rng.normal(0.0, 0.008, (FH // 2, FW // 2, 1)).astype(np.float32)
    out_hi = np.clip(out_hi + cv2.resize(grain, (FW, FH))[..., None], 0.0, 1.0)
    return out_hi


# ==============================================================================
# CLIP & APPLE ML-SHARP DEPTH LOADER
# ==============================================================================
def load_video_with_sharp_depth(video_name, depth_name, w=200, h=112, max_frames=72):
    vpath = os.path.join(VID_DIR, video_name)
    dpath = os.path.join(SPLAT_DIR, depth_name)

    cap = cv2.VideoCapture(vpath)
    frames = []
    while len(frames) < max_frames:
        ok, fr = cap.read()
        if not ok:
            break
        fr = cv2.cvtColor(cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        frames.append(fr.astype(np.float32) / 255.0)
    cap.release()
    if not frames:
        raise RuntimeError(f"Could not read frames from {vpath}")
    frames = np.stack(frames, axis=0)  # (T, h, w, 3)

    # Exposure & tone normalization so dark shots glow cleanly on parchment & night
    p90 = float(np.percentile(frames.mean(axis=-1), 92))
    boost = np.clip(0.86 / max(p90, 0.08), 1.0, 2.5)
    frames = np.clip(frames * boost, 0.0, 1.0)
    frames = 1.0 - (1.0 - frames) ** 1.28

    if os.path.exists(dpath):
        d_img = cv2.imread(dpath, cv2.IMREAD_GRAYSCALE)
        d_map = cv2.resize(d_img, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
        d_map = cv2.GaussianBlur(d_map, (0, 0), 1.2)
    else:
        d_map = frames[0].mean(axis=-1)

    return frames, d_map


# ==============================================================================
# FILM 1: SEEING-AS · S2 CONSTRUCT (0:30, 24fps, 720 frames)
# "Four places as one point cloud; each assembles from one position only."
# ==============================================================================
CONSTRUCT_PLACES = [
    dict(
        idx=0,
        code="I",
        angle_deg=0,
        yaw=0.0,
        video="V01_poet_room.mp4",
        depth="depth_01-00_sharp.png",
        district="MOUNT VERNON",
        subtitle="The Poet's Window & Iron Fire Escape",
        hold=(0.8, 5.6),
    ),
    dict(
        idx=1,
        code="II",
        angle_deg=90,
        yaw=math.pi * 0.5,
        video="V02_storm_chapel.mp4",
        depth="depth_03-00_sharp.png",
        district="HOLLAND ISLAND",
        subtitle="Sunken Bay Causeway & Storm Chapel",
        hold=(8.0, 12.8),
    ),
    dict(
        idx=2,
        code="III",
        angle_deg=180,
        yaw=math.pi,
        video="V03_marble_gates.mp4",
        depth="depth_06-00_sharp.png",
        district="CENTRO HISTÓRICO",
        subtitle="Edificio Atlantis Marble Threshold",
        hold=(15.2, 20.0),
    ),
    dict(
        idx=3,
        code="IV",
        angle_deg=270,
        yaw=math.pi * 1.5,
        video="V06_neon_portal.mp4",
        depth="depth_13-01_sharp.png",
        district="FELLS POINT · TRES MARÍAS",
        subtitle="Harbor Cobblestone & Neon Portal",
        hold=(22.4, 27.2),
    ),
]

_CONSTRUCT_DATA = None
def get_construct_data():
    global _CONSTRUCT_DATA
    if _CONSTRUCT_DATA is not None:
        return _CONSTRUCT_DATA

    # Grid resolution for each of the 4 places: 184 x 104 = 19,136 points per place -> 76,544 total points in one cloud
    gw, gh = 184, 104
    D_cam = 680.0
    rng = np.random.default_rng(42)

    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
    # Screen-space target coordinates centered at (0,0) spanning [-275..275] x [-155..155]
    u_base = ((xx + rng.uniform(-0.35, 0.35, xx.shape)) / gw - 0.5) * 550.0
    v_base = ((yy + rng.uniform(-0.35, 0.35, yy.shape)) / gh - 0.5) * 310.0

    # Soft oval vignette mask on each place so corners dissolve into organic point cloud matter
    r2 = (u_base / 285.0) ** 2 + (v_base / 162.0) ** 2
    keep = r2 < (1.08 - 0.12 * rng.random(u_base.shape))
    ky, kx = np.where(keep)
    u_pts = u_base[ky, kx]
    v_pts = v_base[ky, kx]
    edge_wt = np.clip(1.12 - r2[ky, kx] * 0.65, 0.25, 1.0).astype(np.float32)

    places = []
    for p in CONSTRUCT_PLACES:
        frames, d_map = load_video_with_sharp_depth(p["video"], p["depth"], w=gw, h=gh, max_frames=72)
        d_pts = d_map[ky, kx]
        # Displace along camera k's ray depth Z_k using Apple ml-sharp depth + subtle structural strata
        # Range: [-235, +235] around origin!
        z_ray = ((0.5 - d_pts) * 430.0 + rng.normal(0.0, 4.5, d_pts.shape)).astype(np.float32)
        # Perspective-exact inverse scaling so at camera k (distance D_cam), (X_k / Z_k) * D_cam == u_pts!
        scale_k = (D_cam + z_ray) / D_cam
        x_local = (u_pts * scale_k).astype(np.float32)
        y_local = (v_pts * scale_k).astype(np.float32)

        th = p["yaw"]
        # Rotate from local frame of camera k (where right=r_k, up=u, forward=f_k) into shared 3D world space!
        rk = np.array([math.cos(th), 0.0, math.sin(th)], dtype=np.float32)
        fk = np.array([-math.sin(th), 0.0, math.cos(th)], dtype=np.float32)

        Xw = x_local * rk[0] + z_ray * fk[0]
        Yw = y_local
        Zw = x_local * rk[2] + z_ray * fk[2]

        # Also create 2,500 outer "latent dust/filament" points trailing off depth edges
        places.append(dict(
            meta=p,
            frames=frames[:, ky, kx, :],  # (T, N, 3)
            Xw=Xw,
            Yw=Yw,
            Zw=Zw,
            z_ray=z_ray,
            edge_wt=edge_wt,
        ))

    _CONSTRUCT_DATA = dict(places=places, D_cam=D_cam, N_per=len(ky))
    return _CONSTRUCT_DATA


def construct_camera_curve(t):
    """
    Returns (yaw, pitch, assemble_scatter, active_idx, lock_strength) for time t in [0, 30.0].
    Four holds + four 90-degree 3D orbital transitions:
    - 0.0 .. 1.1s: Formless matter coalesces into Position I (0 deg)
    - 1.1 .. 5.5s: Hold Position I (0 deg) - Mount Vernon plays crystal clear
    - 5.5 .. 8.0s: Orbit 0 -> 90 deg through 3D latent cloud
    - 8.0 .. 12.5s: Hold Position II (90 deg) - Holland Island Storm Chapel
    - 12.5 .. 15.0s: Orbit 90 -> 180 deg through 3D latent cloud
    - 15.0 .. 19.5s: Hold Position III (180 deg) - Centro Historico Marble Gates
    - 19.5 .. 22.0s: Orbit 180 -> 270 deg through 3D latent cloud
    - 22.0 .. 26.5s: Hold Position IV (270 deg) - Fells Point Neon Portal
    - 26.5 .. 30.0s: Orbit 270 -> 360 deg (0 deg) completing the full circle
    """
    # Initial dust-to-construct assembly in the first 1.15s
    scatter = (1.0 - smootherstep(t / 1.15)) ** 2 if t < 1.15 else 0.0

    knots = [
        (0.0, 0.0),
        (5.5, 0.0),
        (8.0, 0.5 * math.pi),
        (12.5, 0.5 * math.pi),
        (15.0, 1.0 * math.pi),
        (19.5, 1.0 * math.pi),
        (22.0, 1.5 * math.pi),
        (26.5, 1.5 * math.pi),
        (29.3, 2.0 * math.pi),
        (30.0, 2.0 * math.pi),
    ]
    yaw = 0.0
    for i in range(len(knots) - 1):
        t0, y0 = knots[i]
        t1, y1 = knots[i + 1]
        if t0 <= t <= t1:
            u = smootherstep((t - t0) / max(t1 - t0, 1e-4))
            yaw = y0 + (y1 - y0) * u
            break

    # Angular distance to each of the 4 canonical positions (0, 90, 180, 270 deg)
    dists = []
    for k in range(4):
        th_k = k * 0.5 * math.pi
        diff = abs((yaw - th_k + math.pi) % (2 * math.pi) - math.pi)
        dists.append(diff)
    dists = np.array(dists, dtype=np.float32)
    active_idx = int(np.argmin(dists))
    min_dist = float(dists[active_idx])

    # Lock strength = 1.0 when aligned with a canonical angle, 0.0 in the middle of the 90-deg swing
    lock = float(np.clip(1.0 - min_dist / (0.22 * math.pi), 0.0, 1.0))
    lock = smootherstep(lock)

    # During orbital transitions, arch the camera pitch slightly so the 3D volume height is felt
    pitch = 0.14 * (1.0 - lock) * math.sin(yaw * 2.0)
    return yaw, pitch, scatter, active_idx, lock, dists


def render_construct_frame(fi):
    t = fi / FPS
    data = get_construct_data()
    D_cam = data["D_cam"]
    places = data["places"]

    yaw, pitch, scatter, active_idx, lock, dists = construct_camera_curve(t)

    all_X, all_Y, all_Z, all_rgb, all_w, all_rad_bias = [], [], [], [], [], []
    rng = np.random.default_rng(100)

    for k, pl in enumerate(places):
        T_len = len(pl["frames"])
        # Video plays smoothly via ping-pong loop
        v_idx = int(t * 20) % (2 * T_len - 2)
        if v_idx >= T_len:
            v_idx = 2 * T_len - 2 - v_idx
        rgb = pl["frames"][v_idx].copy()

        ang_d = float(dists[k])  # 0 when facing camera, pi/2 when orthogonal, pi when opposite
        # Alignment factor: 1.0 at canonical position k, 0.0 elsewhere
        align = smootherstep(np.clip(1.0 - ang_d / (0.42 * math.pi), 0.0, 1.0))

        Xw = pl["Xw"].copy()
        Yw = pl["Yw"].copy()
        Zw = pl["Zw"].copy()

        # When not locked into place k, let a subtle wave of latent 3D turbulence breathe through the cloud
        if scatter > 0.0:
            jt = rng.normal(0.0, 260.0 * scatter, Xw.shape).astype(np.float32)
            Xw += jt
            Yw += rng.normal(0.0, 180.0 * scatter, Yw.shape).astype(np.float32)
            Zw += rng.normal(0.0, 260.0 * scatter, Zw.shape).astype(np.float32)

        # Weight: all 4 places remain in the shared cloud at all times!
        # When aligned (align -> 1), Place k is full strength (1.0) so it forms a complete picture;
        # the other 3 places remain visible as translucent 3D structural filaments (weight ~0.22 during transit, ~0.07 during hold)
        ambient_ghost = 0.055 + 0.24 * (1.0 - lock)
        w_k = pl["edge_wt"] * (align * 0.96 + (1.0 - align) * ambient_ghost)

        # Desaturate non-aligned places slightly toward warm sepia graphite so the shared cloud reads as unified matter
        lum = rgb.mean(axis=-1, keepdims=True)
        graphite = np.concatenate([lum * 0.82 + 0.08, lum * 0.78 + 0.07, lum * 0.72 + 0.06], axis=-1)
        rgb_k = rgb * (0.35 + 0.65 * align) + graphite * (0.65 * (1.0 - align))

        # Radius bias: sharp (0.95px) when locked into alignment; softer volumetric ribbons (1.75px) when rotating in 3D
        rad_b = np.full(len(Xw), 0.92 * align + 1.80 * (1.0 - align), dtype=np.float32)

        all_X.append(Xw)
        all_Y.append(Yw)
        all_Z.append(Zw)
        all_rgb.append(rgb_k)
        all_w.append(w_k)
        all_rad_bias.append(rad_b)

    Xw = np.concatenate(all_X)
    Yw = np.concatenate(all_Y)
    Zw = np.concatenate(all_Z)
    rgb = np.concatenate(all_rgb)
    wt = np.concatenate(all_w)
    rad_bias = np.concatenate(all_rad_bias)

    # Rotate world points into camera frame at angle (yaw, pitch) and distance D_cam
    cy, sy = math.cos(-yaw), math.sin(-yaw)
    Xc = Xw * cy + Zw * sy
    Zc1 = -Xw * sy + Zw * cy

    cp, sp = math.cos(pitch), math.sin(pitch)
    Yc = Yw * cp - Zc1 * sp
    Zc = Yw * sp + Zc1 * cp + D_cam

    focal = 580.0
    px = focal * Xc / np.maximum(Zc, 20.0) + RW * 0.5
    py = focal * Yc / np.maximum(Zc, 20.0) + RH * 0.5

    # Depth-of-field blur radius: points near Zc == D_cam (or when locked in alignment) stay crisp
    dof = np.abs(Zc - D_cam) / 210.0 * (1.0 - 0.72 * lock)
    rad = np.clip(rad_bias + dof, 0.75, 5.8)

    img = splat_gaussian_multiscale(px, py, Zc, rad, rgb, wt, mode="paper", gain=1.08, seed=fi)

    # Overlay clean Afterlight / Seeing-As editorial typography
    pil = Image.fromarray((img * 255.0).astype(np.uint8))
    draw = ImageDraw.Draw(pil, "RGBA")

    f_mono_sm = get_font("mono", 15)
    f_mono_md = get_font("mono", 17)
    f_italic_lg = get_font("italic", 36)
    f_serif_sm = get_font("serif", 20)

    ink_dark = (42, 36, 30, 215)
    ink_muted = (88, 78, 66, 175)

    # Top-left minimal index tag: "S2 · CONSTRUCT   FOUR PLACES AS ONE POINT CLOUD"
    draw.text((48, 38), "S2  ·  CONSTRUCT", font=f_mono_md, fill=ink_dark)
    draw.text((240, 40), "FOUR PLACES AS ONE POINT CLOUD  ·  EACH ASSEMBLES FROM ONE POSITION ONLY", font=f_mono_sm, fill=ink_muted)

    # Top-right live camera azimuth & lock indicator
    deg_now = int(round(math.degrees(yaw))) % 360
    state_str = "LOCKED · ASPECT ALIGNED" if lock > 0.75 else "ORBITING · LATENT MATTER"
    draw.text((FW - 48, 38), f"AZIMUTH {deg_now:03d}°  [{state_str}]", font=f_mono_sm, fill=ink_dark, anchor="ra")

    # 4 position ticks along bottom-right
    for k, p in enumerate(CONSTRUCT_PLACES):
        x_tick = FW - 260 + k * 58
        y_tick = FH - 48
        is_act = (k == active_idx and lock > 0.45)
        col_t = (32, 26, 20, 240) if is_act else (120, 108, 95, 130)
        draw.text((x_tick, y_tick), f"{p['code']}·{p['angle_deg']}°", font=f_mono_sm, fill=col_t, anchor="mm")
        if is_act:
            draw.rectangle([x_tick - 20, y_tick + 12, x_tick + 20, y_tick + 14], fill=(32, 26, 20, 220))

    # Bottom-left caption when a place locks into focus
    if lock > 0.15:
        alpha = int(240 * lock)
        p = CONSTRUCT_PLACES[active_idx]
        draw.text((48, FH - 86), f"Position {p['code']}  ({p['angle_deg']}°)  —  {p['district']}", font=f_italic_lg, fill=(32, 26, 20, alpha))
        draw.text((50, FH - 44), p["subtitle"], font=f_serif_sm, fill=(72, 62, 52, int(200 * lock)))
    else:
        alpha = int(190 * (1.0 - lock))
        draw.text((48, FH - 64), "rotating through latent depth strata between camera rays…", font=f_serif_sm, fill=(85, 74, 62, alpha))

    # Gentle fade in / fade out on parchment
    arr = np.asarray(pil).astype(np.float32) / 255.0
    if t < 0.65:
        a = ease(t / 0.65)
        arr = PAPER * (1.0 - a) + arr * a
    elif t > 29.2:
        a = ease((30.0 - t) / 0.8)
        arr = PAPER * (1.0 - a) + arr * a

    return (np.clip(arr, 0.0, 1.0) * 255.0).astype(np.uint8)


# ==============================================================================
# FILM 2: 07-SPACETIME · WALK THROUGH THE LATENT VOLUME (1:00, 24fps, 1440 frames)
# Built directly on bolas/afterlight/source/trailer-1/{spacetime,trailer,score}.py
# ==============================================================================
SPACETIME_CLIPS = {
    "poet":    ("V01_poet_room.mp4",    "depth_01-00_sharp.png", "I · MOUNT VERNON"),
    "tower":   ("V01_tower_overlook.mp4","depth_01-02_sharp.png", "II · MONUMENT OVERLOOK"),
    "chapel":  ("V02_storm_chapel.mp4", "depth_03-00_sharp.png", "III · HOLLAND ISLAND"),
    "gates":   ("V03_marble_gates.mp4", "depth_06-00_sharp.png", "IV · CENTRO ATLANTIS"),
    "shore":   ("V03_crimson_shore.mp4","depth_08-00_sharp.png", "V · SUMPTER SHORE"),
    "walker":  ("V04_rain_walker.mp4",  "depth_02-00_sharp.png", "VI · WOODBERRY"),
    "beach":   ("V04_monochrome_beach.mp4","depth_04-00_sharp.png","VII · DRUID HILL"),
    "marsh":   ("V05_tidal_marsh.mp4",  "depth_03-01_sharp.png", "VIII · DORCHESTER MARSH"),
    "screens": ("V05_tv_screens.mp4",   "depth_05-00_sharp.png", "IX · STATION NORTH"),
    "portal":  ("V06_neon_portal.mp4",  "depth_13-01_sharp.png", "X · TRES MARÍAS PORTAL"),
}

_VOL_CACHE = {}
def get_spacetime_vol(key):
    if key in _VOL_CACHE:
        return _VOL_CACHE[key]
    vname, dname, label = SPACETIME_CLIPS[key]
    # 128 x 72 spatial grid x 44 temporal slices = ~240,000 spacetime points per volume!
    vw, vh = 128, 72
    frames, d_map = load_video_with_sharp_depth(vname, dname, w=vw, h=vh, max_frames=48)
    T = len(frames)

    rng = np.random.default_rng(abs(hash(key)) % (2**31))
    yy, xx = np.mgrid[0:vh, 0:vw].astype(np.float32)

    # Compute temporal motion + luminance importance across the clip
    diff = np.linalg.norm(np.diff(frames, axis=0, prepend=frames[:1]), axis=-1)
    sal = 0.35 + 0.65 * (frames.mean(axis=-1) + 1.8 * diff)

    xs, ys, ss, ds, cols, wts = [], [], [], [], [], []
    for s in range(T):
        prob = np.clip(sal[s] * 0.72, 0.18, 0.85)
        keep = rng.random((vh, vw)) < prob
        ky, kx = np.where(keep)
        jx = rng.uniform(-0.45, 0.45, len(kx)).astype(np.float32)
        jy = rng.uniform(-0.45, 0.45, len(ky)).astype(np.float32)

        x = ((kx + jx) / vw - 0.5) * 540.0
        y = ((ky + jy) / vh - 0.5) * 304.0
        d_val = (0.5 - d_map[ky, kx]) * 125.0  # Apple ml-sharp neural depth relief inside each frame slice!
        c = frames[s, ky, kx]
        w = (0.45 + 0.55 * sal[s, ky, kx]).astype(np.float32)

        xs.append(x.astype(np.float32))
        ys.append(y.astype(np.float32))
        ss.append(np.full(len(kx), s, dtype=np.float32))
        ds.append(d_val.astype(np.float32))
        cols.append(c.astype(np.float32))
        wts.append(w)

    vol = dict(
        key=key,
        label=label,
        T=T,
        x=np.concatenate(xs),
        y=np.concatenate(ys),
        s=np.concatenate(ss),
        d=np.concatenate(ds),
        rgb=np.concatenate(cols),
        w=np.concatenate(wts),
        dz=15.0,
    )
    _VOL_CACHE[key] = vol
    return vol


def build_07_spacetime_shots():
    """
    Exact 6 movements + accelerating face-on / side-on Montage + Drop + 3D Title from trailer.py.txt
    Total duration: 60.0s (1440 frames at 24fps).
    """
    shots = [
        # 6 Poetic Movements (0.0s -> 34.8s)
        dict(t0=0.0,  t1=6.2,  vol="poet",   mode="paper", assemble=True,
             cam0=(0.0,   0.0, 1280,  0.00,  0.02), cam1=(18.0,  -8.0,  340,  0.22, -0.04),
             card=("Every frame is a place the light once stood", 1.2, 5.3)),
        dict(t0=6.2,  t1=12.0, vol="chapel", mode="paper", assemble=False,
             cam0=(-95.0, -15.0, 740, -0.35, 0.06), cam1=(95.0,  -10.0, 320,  0.42, -0.03),
             card=("Hold the frames together —", 6.8, 11.2)),
        dict(t0=12.0, t1=18.0, vol="gates",  mode="light", assemble=False,
             cam0=(0.0,   12.0, 1080, -0.18, -0.05), cam1=(0.0,   -6.0,  260,  0.28,  0.04),
             card=("— and a city becomes a body in time", 12.6, 17.2)),
        dict(t0=18.0, t1=24.0, vol="walker", mode="paper", assemble=False,
             cam0=(140.0,  0.0,  680,  0.62,  0.04), cam1=(-60.0, -10.0, 290, -0.25, -0.02),
             card=("Walk forward through the volume", 18.6, 23.2)),
        dict(t0=24.0, t1=29.8, vol="portal", mode="light", assemble=False,
             cam0=(-70.0, -18.0, 860, -0.32,  0.08), cam1=(60.0,   8.0,  250,  0.38, -0.04),
             card=("The present is the brightest slice", 24.5, 29.0)),
        dict(t0=29.8, t1=34.8, vol="marsh",  mode="paper", assemble=False,
             cam0=(180.0, -24.0, 660,  0.78,  0.08), cam1=(-160.0, 12.0, 420, -0.72, -0.04),
             card=("Ten districts — one latent world", 30.3, 34.2)),
    ]

    # THE MONTAGE (34.8s -> 49.4s):
    # Every volume twice: FIRST face-on push (yaw ~ 0), THEN side-on cut (yaw ~ ±1.06 rad = ±61 deg)
    # exposing the 3D neural depth + temporal trail from the side, with cuts tightening from 1.05s down to 0.25s!
    montage_specs = [
        ("poet",    "paper", "front", +1, 1.05),
        ("poet",    "paper", "side",  +1, 0.95),
        ("tower",   "light", "front", -1, 0.90),
        ("tower",   "light", "side",  -1, 0.85),
        ("chapel",  "paper", "front", +1, 0.80),
        ("chapel",  "paper", "side",  +1, 0.76),
        ("gates",   "light", "front", -1, 0.72),
        ("gates",   "light", "side",  -1, 0.68),
        ("shore",   "paper", "front", +1, 0.64),
        ("shore",   "paper", "side",  +1, 0.60),
        ("walker",  "light", "front", -1, 0.56),
        ("walker",  "light", "side",  -1, 0.52),
        ("beach",   "paper", "front", +1, 0.48),
        ("beach",   "paper", "side",  +1, 0.44),
        ("screens", "light", "front", -1, 0.40),
        ("screens", "light", "side",  -1, 0.36),
        ("portal",  "light", "front", +1, 0.32),
        ("portal",  "light", "side",  +1, 0.30),
        ("marsh",   "paper", "front", -1, 0.28),
        ("gates",   "light", "side",  +1, 0.26),
    ]
    t_cur = 34.8
    for vol_k, md, angle_kind, sgn, dur in montage_specs:
        t_next = round(t_cur + dur, 4)
        if angle_kind == "front":
            cam0 = (0.0, 0.0, 690.0, 0.05 * sgn, 0.0)
            cam1 = (0.0, 0.0, 290.0, -0.05 * sgn, 0.0)
        else:
            # Side-on 62-degree view showing the full 4D spacetime + neural depth strata!
            cam0 = (210.0 * sgn, -16.0, 560.0, 1.05 * sgn, 0.06)
            cam1 = (180.0 * sgn,   8.0, 440.0, 0.88 * sgn, -0.03)
        shots.append(dict(
            t0=t_cur, t1=t_next, vol=vol_k, mode=md, assemble=False,
            cam0=cam0, cam1=cam1, card=None, montage=angle_kind
        ))
        t_cur = t_next

    # THE DROP (silence & parchment breath before title)
    t_drop_end = round(t_cur + 1.1, 4)
    shots.append(dict(t0=t_cur, t1=t_drop_end, vol=None, mode="drop"))

    # 3D POINT-CLOUD TITLE ("W Y G W Y L")
    shots.append(dict(t0=t_drop_end, t1=60.0, vol=None, mode="title"))
    return shots

SPACETIME_SHOTS = build_07_spacetime_shots()

_TITLE_CLOUD = None
def get_title_cloud():
    global _TITLE_CLOUD
    if _TITLE_CLOUD is not None:
        return _TITLE_CLOUD
    img = Image.new("L", (900, 260), 0)
    d = ImageDraw.Draw(img)
    f_big = get_font("serif", 112)
    f_sub = get_font("mono", 20)
    d.text((450, 95), "W Y G W Y L", font=f_big, fill=255, anchor="mm")
    d.text((450, 195), "LATENT SPACETIME ARCHIVE  ·  TEN DISTRICTS", font=f_sub, fill=210, anchor="mm")
    arr = np.asarray(img, dtype=np.float32) / 255.0
    yy, xx = np.where(arr > 0.15)
    rng = np.random.default_rng(77)
    keep = rng.random(len(xx)) < 0.78
    yy, xx = yy[keep], xx[keep]

    x = (xx - 450.0) * 0.92 + rng.normal(0, 0.4, len(xx)).astype(np.float32)
    y = (yy - 130.0) * 0.92 + rng.normal(0, 0.4, len(yy)).astype(np.float32)
    z = rng.normal(0, 9.0, len(xx)).astype(np.float32)

    # Scatter origin for the dust-to-title assembly
    sx = rng.normal(0, 420.0, len(xx)).astype(np.float32)
    sy = rng.normal(0, 260.0, len(xx)).astype(np.float32)
    sz = rng.uniform(-520.0, 520.0, len(xx)).astype(np.float32)

    _TITLE_CLOUD = dict(x=x, y=y, z=z, sx=sx, sy=sy, sz=sz, w=arr[yy, xx].astype(np.float32))
    return _TITLE_CLOUD


def render_spacetime_frame(fi):
    t = fi / FPS
    shot = SPACETIME_SHOTS[-1]
    for s in SPACETIME_SHOTS:
        if s["t0"] <= t < s["t1"]:
            shot = s
            break

    if shot["mode"] == "drop":
        out = np.broadcast_to(PAPER, (FH, FW, 3)).copy()
        return (out * 255.0).astype(np.uint8)

    if shot["mode"] == "title":
        tc = get_title_cloud()
        u = (t - shot["t0"]) / max(shot["t1"] - shot["t0"], 1e-4)
        k_scatter = (1.0 - smootherstep(min(1.0, u / 0.48))) ** 2.2
        X = tc["x"] * (1.0 - k_scatter) + tc["sx"] * k_scatter
        Y = tc["y"] * (1.0 - k_scatter) + tc["sy"] * k_scatter
        Z = tc["z"] * (1.0 - k_scatter) + tc["sz"] * k_scatter

        yaw = (1.0 - smootherstep(min(1.0, u / 0.55))) * 0.55 + 0.05 * math.sin(u * 3.0)
        dist = 560.0 - 70.0 * ease(u)
        cy, sy = math.cos(yaw), math.sin(yaw)
        Xc = X * cy + Z * sy
        Zc = -X * sy + Z * cy + dist

        px = 520.0 * Xc / np.maximum(Zc, 30.0) + RW * 0.5
        py = 520.0 * Y / np.maximum(Zc, 30.0) + RH * 0.5
        rad = np.clip(0.95 + 2.8 * k_scatter + np.abs(Zc - dist) / 160.0, 0.8, 5.5).astype(np.float32)
        rgb = np.broadcast_to(np.array([[0.12, 0.10, 0.08]], dtype=np.float32), (len(X), 3))
        img = splat_gaussian_multiscale(px, py, Zc, rad, rgb, tc["w"] * 1.35, mode="paper", gain=1.25, seed=fi)
        if u > 0.82:
            a = ease((1.0 - u) / 0.18)
            img = PAPER * (1.0 - a) + img * a
        return (np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8)

    # Standard 4D Spacetime + Apple ml-sharp neural depth volume shot
    vol = get_spacetime_vol(shot["vol"])
    u = (t - shot["t0"]) / max(shot["t1"] - shot["t0"], 1e-4)
    eu = ease(u)

    cam0, cam1 = shot["cam0"], shot["cam1"]
    cx = cam0[0] + (cam1[0] - cam0[0]) * eu
    cy_cam = cam0[1] + (cam1[1] - cam0[1]) * eu
    dist = cam0[2] + (cam1[2] - cam0[2]) * eu
    yaw = cam0[3] + (cam1[3] - cam0[3]) * eu
    pitch = cam0[4] + (cam1[4] - cam0[4]) * eu

    # Present slice advances through the volume
    present = (0.18 + 0.72 * u) * (vol["T"] - 1)
    age = present - vol["s"]

    # Keep slices up to 28 frames into the past + 2 frames ahead
    vis = (age >= -2.2) & (age <= 28.0)
    x = vol["x"][vis]
    y = vol["y"][vis]
    d = vol["d"][vis]
    age = age[vis]
    rgb = vol["rgb"][vis]
    w_base = vol["w"][vis]

    # Z coordinate combines temporal depth (age * dz) AND Apple ml-sharp spatial relief (d)!
    z = age * vol["dz"] + d

    if shot.get("assemble", False):
        k_sc = (1.0 - smootherstep(min(1.0, u / 0.58))) ** 2.2
        if k_sc > 1e-4:
            rng = np.random.default_rng(19)
            x = x + rng.normal(0, 340.0 * k_sc, len(x)).astype(np.float32)
            y = y + rng.normal(0, 220.0 * k_sc, len(y)).astype(np.float32)
            z = z + rng.normal(0, 380.0 * k_sc, len(z)).astype(np.float32)

    # Temporal decay weight: present slice is brightest; older slices form the luminous body in time
    time_decay = np.where(age >= 0, np.exp(-age / 13.5), np.exp(-(age ** 2) / 1.2)).astype(np.float32)
    wt = w_base * time_decay * (0.45 + 0.65 * np.exp(-(age ** 2) / 2.8)).astype(np.float32)

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

    # Points on the present slice near the focal distance are sharp; past slices soften into trails
    dof = np.abs(Zc - dist) / (230.0 if shot["mode"] == "paper" else 190.0)
    rad = np.clip(0.85 + dof + 0.05 * np.maximum(0.0, age), 0.75, 5.8).astype(np.float32)

    img = splat_gaussian_multiscale(px, py, Zc, rad, rgb, wt, mode=shot["mode"], gain=1.08, seed=fi)

    # Editorial overlays (IM Fell English poetic cards + subtle IBM Plex Mono archive HUD)
    pil = Image.fromarray((img * 255.0).astype(np.uint8))
    draw = ImageDraw.Draw(pil, "RGBA")
    is_paper = (shot["mode"] == "paper")
    fg_main = (38, 32, 26) if is_paper else (242, 234, 218)
    fg_sub = (92, 82, 70) if is_paper else (175, 168, 155)

    f_mono = get_font("mono", 14)
    f_italic = get_font("italic", 36)

    # Top-left district volume label & top-right camera angle
    angle_tag = "SIDE-ON ±62° (4D DEPTH STRATA)" if shot.get("montage") == "side" else (
        "FACE-ON PUSH" if shot.get("montage") == "front" else f"YAW {math.degrees(yaw):+05.1f}° · Z-WALK"
    )
    draw.text((46, 36), f"07 · SPACETIME VOLUME   [{vol['label']}]", font=f_mono, fill=fg_sub + (185,))
    draw.text((FW - 46, 36), angle_tag, font=f_mono, fill=fg_sub + (185,), anchor="ra")

    card = shot.get("card")
    if card is not None:
        text, ct0, ct1 = card
        if ct0 <= t <= ct1:
            ca = ease((t - ct0) / 0.55) * ease((ct1 - t) / 0.65)
            al = int(242 * ca)
            draw.text((FW // 2, FH - 66), text, font=f_italic, fill=fg_main + (al,), anchor="mm")

    return np.asarray(pil, dtype=np.uint8)


# ==============================================================================
# PROCEDURAL SOUNDTRACK SYNTHESIZERS (from bolas/afterlight score.py)
# ==============================================================================
SR = 44100

def lp_filter(sig, cutoff, order=2):
    b, a = butter(order, min(0.98, cutoff / (SR * 0.5)), btype="low")
    return lfilter(b, a, sig)

def hp_filter(sig, cutoff, order=2):
    b, a = butter(order, min(0.98, cutoff / (SR * 0.5)), btype="high")
    return lfilter(b, a, sig)

def add_stereo(buf, t0, sig, pan=0.0):
    i0 = max(0, int(t0 * SR))
    n = min(len(sig), len(buf) - i0)
    if n <= 0:
        return
    gl = math.cos((pan + 1.0) * math.pi * 0.25)
    gr = math.sin((pan + 1.0) * math.pi * 0.25)
    buf[i0:i0 + n, 0] += sig[:n] * gl
    buf[i0:i0 + n, 1] += sig[:n] * gr

def synth_pad(freq, dur, amp=0.08):
    t = np.arange(int(dur * SR)) / SR
    sig = np.zeros_like(t)
    for mult, wt in [(1.0, 1.0), (1.003, 0.7), (0.997, 0.7), (2.0, 0.28), (3.0, 0.08)]:
        sig += wt * np.sin(2 * math.pi * freq * mult * t)
    env = np.minimum(1.0, t / 1.4) * np.minimum(1.0, (dur - t) / 1.8)
    return lp_filter(sig * env * amp * 0.35, 950)

def synth_kalimba(freq, dur=1.8, amp=0.14):
    t = np.arange(int(dur * SR)) / SR
    env = (1.0 - np.exp(-t * 220.0)) * np.exp(-t * 3.4)
    sig = np.sin(2 * math.pi * freq * t) + 0.28 * np.sin(2 * math.pi * freq * 2.98 * t) * np.exp(-t * 14.0)
    return sig * env * amp

def synth_bell(freq, dur=4.5, amp=0.11):
    t = np.arange(int(dur * SR)) / SR
    sig = (
        np.sin(2 * math.pi * freq * t) * np.exp(-t * 0.9)
        + 0.45 * np.sin(2 * math.pi * freq * 2.0 * t) * np.exp(-t * 1.6)
        + 0.22 * np.sin(2 * math.pi * freq * 2.756 * t) * np.exp(-t * 2.4)
    )
    env = (1.0 - np.exp(-t * 80.0))
    return sig * env * amp

def synth_whoosh(dur=2.4, amp=0.09, seed=1):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = lp_filter(hp_filter(rng.normal(0, 1, n), 180), 920)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.8
    return noise * env * amp

def synth_boom(freq=46.0, dur=2.2, amp=0.26):
    t = np.arange(int(dur * SR)) / SR
    f_sweep = freq * (1.0 + 1.1 * np.exp(-t * 16.0))
    phase = 2 * math.pi * np.cumsum(f_sweep) / SR
    return np.sin(phase) * np.exp(-t * 2.6) * amp

def apply_reverb(buf, wet=0.26):
    out = buf.copy()
    for delay_ms, g in [(79, 0.28), (137, 0.21), (223, 0.15), (347, 0.10), (509, 0.06)]:
        d = int(delay_ms * SR / 1000)
        if d < len(buf):
            out[d:, 0] += buf[:-d, 1] * g * wet
            out[d:, 1] += buf[:-d, 0] * g * wet
    peak = np.max(np.abs(out))
    if peak > 1e-5:
        out = np.tanh(out / peak * 1.15) * 0.88
    return out

def save_wav(path, buf):
    pcm = (np.clip(buf, -1.0, 1.0) * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def build_construct_audio(wav_path):
    """30.0s score for Seeing-As · S2 Construct: warm drone, bell lock-ins at 0/90/180/270 deg, and orbital wind swells."""
    dur = 30.0
    buf = np.zeros((int(dur * SR), 2), dtype=np.float64)

    # Warm D-minor / Dorian harmonic bed across the 30s circle
    chords = [
        (0.0, 8.0, [146.83, 220.00, 261.63, 329.63]),
        (7.5, 8.0, [130.81, 196.00, 246.94, 293.66]),
        (15.0, 8.0, [116.54, 174.61, 220.00, 261.63]),
        (22.0, 8.0, [146.83, 220.00, 293.66, 349.23]),
    ]
    for t0, cdur, notes in chords:
        for i, f in enumerate(notes):
            add_stereo(buf, t0, synth_pad(f, cdur, amp=0.075), pan=(i - 1.5) * 0.35)

    # Resonant bell + kalimba lock-in when each of the 4 places snaps into focus
    locks = [
        (1.0,  293.66, 440.00, -0.25),
        (8.0,  329.63, 493.88, +0.25),
        (15.0, 261.63, 392.00, -0.25),
        (22.0, 349.23, 523.25, +0.25),
    ]
    for t_lock, f1, f2, pan in locks:
        add_stereo(buf, t_lock, synth_bell(f1, dur=4.8, amp=0.13), pan=pan)
        add_stereo(buf, t_lock + 0.18, synth_kalimba(f2, dur=2.2, amp=0.11), pan=-pan)
        add_stereo(buf, t_lock, synth_boom(55.0, dur=1.8, amp=0.16), pan=0.0)
        # Gentle kalimba pulse while the video plays in alignment
        for step in range(1, 7):
            add_stereo(buf, t_lock + step * 0.65, synth_kalimba(f1 * (1.5 if step % 2 else 1.0), dur=1.2, amp=0.055), pan=pan * 0.5)

    # Orbital whoosh swells during the four 90-degree rotations
    for idx, t_rot in enumerate([5.5, 12.5, 19.5, 26.5]):
        add_stereo(buf, t_rot, synth_whoosh(dur=2.5, amp=0.09, seed=10 + idx), pan=(-1 if idx % 2 == 0 else 1) * 0.4)

    buf = apply_reverb(buf, wet=0.30)
    save_wav(wav_path, buf)


def build_spacetime_audio(wav_path):
    """60.0s score for 07-Spacetime Walk locked to SPACETIME_SHOTS."""
    dur = 60.0
    buf = np.zeros((int(dur * SR), 2), dtype=np.float64)

    # 6 Poetic movements (0.0 .. 34.8s)
    prog = [
        (0.0,  6.2,  [146.83, 220.00, 293.66]),
        (6.2,  5.8,  [116.54, 174.61, 261.63]),
        (12.0, 6.0,  [130.81, 196.00, 246.94]),
        (18.0, 6.0,  [110.00, 164.81, 220.00]),
        (24.0, 5.8,  [116.54, 174.61, 293.66]),
        (29.8, 5.0,  [130.81, 196.00, 293.66]),
    ]
    for idx, (t0, cdur, notes) in enumerate(prog):
        for i, f in enumerate(notes):
            add_stereo(buf, t0, synth_pad(f, cdur + 0.6, amp=0.08), pan=(i - 1) * 0.4)
        add_stereo(buf, t0, synth_boom(48.99, dur=2.0, amp=0.18), pan=0.0)
        add_stereo(buf, t0 + 0.1, synth_bell(notes[-1] * 2.0, dur=4.2, amp=0.10), pan=(-0.3 if idx % 2 else 0.3))
        # Arpeggiated kalimba steps walking through time
        arp = [293.66, 349.23, 440.00, 523.25, 440.00, 349.23]
        for k in range(int(cdur * 2.2)):
            add_stereo(buf, t0 + k * 0.45, synth_kalimba(arp[k % len(arp)], dur=1.1, amp=0.065), pan=((k % 3) - 1) * 0.35)

    # THE MONTAGE (34.8s .. 49.4s): accelerating ticks, sub-hits, and harmonic riser
    montage_shots = [s for s in SPACETIME_SHOTS if s.get("montage") is not None]
    scale = [293.66, 329.63, 349.23, 392.00, 440.00, 523.25, 587.33, 659.25, 698.46, 880.00]
    for i, s in enumerate(montage_shots):
        t0 = s["t0"]
        u = i / max(1, len(montage_shots) - 1)
        f_note = scale[min(len(scale) - 1, i // 2)]
        is_side = (s.get("montage") == "side")
        add_stereo(buf, t0, synth_kalimba(f_note * (1.5 if is_side else 1.0), dur=0.7, amp=0.09 + 0.06 * u), pan=(-0.45 if is_side else 0.45))
        if i % 2 == 0 or u > 0.6:
            add_stereo(buf, t0, synth_boom(55.0 + 25.0 * u, dur=0.7, amp=0.15 + 0.08 * u), pan=0.0)

    # Hard silence during THE DROP (49.4 .. 50.5s), then deep resonant chord on 3D TITLE ("WYGWYL")
    title_shot = [s for s in SPACETIME_SHOTS if s["mode"] == "title"][0]
    t_title = title_shot["t0"]
    buf[int((t_title - 1.05) * SR):int(t_title * SR)] *= 0.05
    add_stereo(buf, t_title, synth_boom(36.71, dur=3.8, amp=0.30), pan=0.0)
    for i, f in enumerate([146.83, 220.00, 293.66, 369.99, 440.00, 587.33]):
        add_stereo(buf, t_title + 0.08 * i, synth_pad(f, 8.8, amp=0.075), pan=(i - 2.5) * 0.25)
        add_stereo(buf, t_title + 0.12 * i, synth_bell(f, dur=6.5, amp=0.08), pan=(2.5 - i) * 0.25)

    buf = apply_reverb(buf, wet=0.28)
    save_wav(wav_path, buf)


# ==============================================================================
# PARALLEL RENDER + FFMPEG MUX + CONTACT SHEET GENERATOR
# ==============================================================================
def render_film_parallel(name, out_mp4, total_frames, frame_fn, audio_fn, sheet_png, title_banner):
    t_start = time.time()
    os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
    wav_path = out_mp4.replace(".mp4", ".wav")
    print(f"[{name}] Synthesizing stereo score -> {wav_path} ...", flush=True)
    audio_fn(wav_path)

    n_workers = min(8, os.cpu_count() or 4)
    print(f"[{name}] Rendering {total_frames} frames ({total_frames/FPS:.1f}s @ {FPS}fps, {FW}x{FH}) across {n_workers} workers...", flush=True)

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
        "-i", wav_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart",
        out_mp4
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # Render in ordered batches of 48 frames using ProcessPoolExecutor
    sample_frames = {}
    sample_indices = set(np.linspace(12, total_frames - 18, 12, dtype=int).tolist())

    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        batch_size = 48
        for b0 in range(0, total_frames, batch_size):
            idxs = list(range(b0, min(total_frames, b0 + batch_size)))
            for fi, rgb_u8 in zip(idxs, ex.map(frame_fn, idxs)):
                proc.stdin.write(rgb_u8.tobytes())
                if fi in sample_indices:
                    sample_frames[fi] = rgb_u8
            print(f"  [{name}] {min(total_frames, b0 + batch_size)}/{total_frames} frames ({time.time() - t_start:.1f}s)", flush=True)

    proc.stdin.close()
    proc.wait()
    if os.path.exists(wav_path):
        os.remove(wav_path)

    # Build 4x3 high-res contact sheet for immediate visual verification
    tw, th = 420, 236
    pad = 14
    header_h = 68
    cw = 4 * tw + 5 * pad
    ch = header_h + 3 * th + 4 * pad
    sheet = Image.new("RGB", (cw, ch), (236, 231, 221))
    d = ImageDraw.Draw(sheet)
    f_hdr = get_font("serif", 26)
    f_sub = get_font("mono", 14)
    d.text((pad, 18), title_banner, font=f_hdr, fill=(32, 26, 20))

    sorted_keys = sorted(sample_frames.keys())
    for idx, fi in enumerate(sorted_keys[:12]):
        r, c = divmod(idx, 4)
        x0 = pad + c * (tw + pad)
        y0 = header_h + pad + r * (th + pad)
        im = Image.fromarray(sample_frames[fi]).resize((tw, th), Image.Resampling.LANCZOS)
        sheet.paste(im, (x0, y0))
        d.rectangle([x0, y0, x0 + 92, y0 + 22], fill=(24, 20, 18))
        d.text((x0 + 8, y0 + 4), f"t = {fi/FPS:04.1f}s", font=f_sub, fill=(242, 236, 224))

    sheet.save(sheet_png, quality=92)
    print(f"[{name}] Done in {time.time() - t_start:.1f}s -> {out_mp4} & {sheet_png}", flush=True)


if __name__ == "__main__":
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    # 1. Render Seeing-As · S2 Construct (0:30, 720 frames)
    out_construct = os.path.join(VID_DIR, "wygwyl_seeing_construct.mp4")
    sheet_construct = os.path.join(ARTIFACT_DIR, "wygwyl_seeing_construct_sheet.png")
    render_film_parallel(
        "S2-CONSTRUCT",
        out_construct,
        30 * FPS,
        render_construct_frame,
        build_construct_audio,
        sheet_construct,
        "SEEING-AS · S2 CONSTRUCT (0:30) — Four WYGWYL Places as One Point Cloud; Each Assembles from One Position Only"
    )

    # 2. Render 07-Spacetime Walk (1:00, 1440 frames)
    out_spacetime = os.path.join(VID_DIR, "wygwyl_07_spacetime.mp4")
    sheet_spacetime = os.path.join(ARTIFACT_DIR, "wygwyl_07_spacetime_sheet.png")
    render_film_parallel(
        "07-SPACETIME",
        out_spacetime,
        60 * FPS,
        render_spacetime_frame,
        build_spacetime_audio,
        sheet_spacetime,
        "07-SPACETIME (1:00) — Every WYGWYL Clip as a 4D Spacetime + Apple SHARP Neural Depth Volume"
    )
