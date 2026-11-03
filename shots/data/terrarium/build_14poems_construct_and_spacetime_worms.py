#!/usr/bin/env python3
"""
Builds the complete 14-Poem WYGWYL Afterlight Suite:
For EACH of the 14 Full Poems (P01 .. P14):
  1. Multi-Shot Territory Construct (`shots/videos/poems/poem_<01..14>_construct.mp4`):
     Uses ALL shots belonging to that Poem's Territory (`shots/out/<shot_id>/film/shot.mp4` + `depth_sharp.npz`)
     inside ONE shared 3D point cloud. Each shot assembles from its own canonical angle theta_k = k * (360/N) deg.
  2. Multi-Shot Spacetime Worm & Words Journey (`shots/videos/poems/poem_<01..14>_spacetime_worm.mp4`):
     Flies continuously through all shots of that Poem & Territory chained along a 3D world corridor,
     extruding 4D spacetime motion worms (`02d-worms` + `07-spacetime`) from every moving subject while the
     poem's movements & verses materialize as 3D point-cloud words suspended inside the volume.
Plus:
  3. Master All-Territory Construct (`shots/videos/wygwyl_seeing_construct.mp4`)
  4. Master 14-Poem Spacetime Worm & Words Walk (`shots/videos/wygwyl_07_spacetime.mp4`)
  5. Contact sheet proofs in the artifact directory.
"""
import os
import sys
import glob
import json
import math
import time
import wave
import subprocess
import multiprocessing as mp
import numpy as np
import cv2
from scipy.signal import butter, lfilter
from PIL import Image, ImageDraw, ImageFont

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots"
OUT_DIR = os.path.join(ROOT, "out")
VID_DIR = os.path.join(ROOT, "videos")
POEM_VID_DIR = os.path.join(VID_DIR, "poems")
FONT_DIR = os.path.join(ROOT, "fonts")
ARTIFACT_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"

FPS = 24
RW, RH = 640, 360
FW, FH = 1280, 720

PAPER = np.array([0.925, 0.905, 0.865], dtype=np.float32)
NIGHT = np.array([0.018, 0.020, 0.028], dtype=np.float32)

def ease(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3.0 - 2.0 * u)

def smootherstep(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)

def hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) != 6:
        return np.array([0.85, 0.55, 0.20], dtype=np.float32)
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)], dtype=np.float32) / 255.0

_FONT_CACHE = {}
def get_font(kind="italic", size=36):
    key = (kind, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    if kind == "italic":
        candidates = [
            os.path.join(FONT_DIR, "im-fell-english-latin-400-italic.woff2"),
            "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
        ]
    elif kind == "serif":
        candidates = [
            os.path.join(FONT_DIR, "im-fell-english-latin-400-normal.woff2"),
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
        ]
    else:
        candidates = [
            os.path.join(FONT_DIR, "ibm-plex-mono-latin-400-normal.woff2"),
            "/System/Library/Fonts/Menlo.ttc",
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
# ULTRA-FAST SIMD MULTI-SCALE GAUSSIAN SPLAT & BEERS-LAW TRANSMITTANCE RENDERER
# Uses np.bincount + cv2.GaussianBlur (7x faster than scipy.ndimage)
# ==============================================================================
_VIG_CACHE = {}
def get_vignette(h, w):
    if (h, w) not in _VIG_CACHE:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        v = 1.0 - 0.19 * (((xx - w * 0.5) / (w * 0.55)) ** 2 + ((yy - h * 0.5) / (h * 0.55)) ** 2)
        _VIG_CACHE[(h, w)] = np.clip(v, 0.74, 1.02)[..., None]
    return _VIG_CACHE[(h, w)]


def splat_gaussian_fast(px, py, zc, rad, rgb, w_val, mode="paper", gain=1.08, seed=0):
    H, W = RH, RW
    valid = (zc > 22.0) & (px >= 0) & (px < W - 1) & (py >= 0) & (py < H - 1) & (w_val > 1e-4)
    if not np.any(valid):
        bg = PAPER if mode == "paper" else NIGHT
        return np.broadcast_to(bg, (FH, FW, 3)).copy()

    ix = px[valid].astype(np.int32)
    iy = py[valid].astype(np.int32)
    rad = rad[valid]
    rgb = rgb[valid]
    wt = w_val[valid]
    flat = iy * W + ix
    hw = H * W

    b0 = rad < 1.55
    b1 = (rad >= 1.55) & (rad < 3.65)
    b2 = rad >= 3.65

    sigmas = [0.6, 1.5, 3.6]
    ks = [4.0, 8.0, 19.5]
    acc = np.zeros((3, H, W, 4), dtype=np.float32)

    for bi, mask in enumerate((b0, b1, b2)):
        if not np.any(mask):
            continue
        fl = flat[mask]
        w = wt[mask]
        c = rgb[mask] * w[:, None]
        ch0 = np.bincount(fl, weights=c[:, 0], minlength=hw).reshape(H, W)
        ch1 = np.bincount(fl, weights=c[:, 1], minlength=hw).reshape(H, W)
        ch2 = np.bincount(fl, weights=c[:, 2], minlength=hw).reshape(H, W)
        ch3 = np.bincount(fl, weights=w, minlength=hw).reshape(H, W)
        layer = np.stack([ch0, ch1, ch2, ch3], axis=-1).astype(np.float32)
        acc[bi] = cv2.GaussianBlur(layer, (0, 0), sigmas[bi])

    if mode == "paper":
        out = np.broadcast_to(PAPER, (H, W, 3)).copy()
        for bi in (2, 1, 0):
            A = acc[bi, :, :, 3:4]
            col = acc[bi, :, :, :3] / np.maximum(A, 1e-5)
            col = np.clip((col - 0.5) * 1.22 + 0.45, 0.02, 0.98)
            cov = 1.0 - np.exp(-A * ks[bi] * gain)
            out = out * (1.0 - cov) + col * cov
        out = out * get_vignette(H, W)
    else:
        total = acc[2] * ks[2] + acc[1] * ks[1] + acc[0] * ks[0]
        A = total[:, :, 3:4] * gain
        col = total[:, :, :3] * gain / np.maximum(A, 1e-4)
        cov = 1.0 - np.exp(-A * 0.88)
        bloom_src = (col * cov).astype(np.float32)
        bloom = cv2.GaussianBlur(bloom_src, (0, 0), 8.5)
        out = NIGHT[None, None, :] * (1.0 - cov * 0.92) + bloom_src + bloom * 0.46

    out_hi = cv2.resize(np.clip(out, 0.0, 1.0), (FW, FH), interpolation=cv2.INTER_LINEAR)
    return out_hi


# ==============================================================================
# CATALOG POEMS, TERRITORIES & PRELOAD NEEDED SHOT VOLUMES
# ==============================================================================
with open(os.path.join(ROOT, "film/poems.json")) as _f:
    POEMS = json.load(_f)

SHOT_META = {}
BY_DISTRICT = {}
for _d in sorted(glob.glob(os.path.join(OUT_DIR, "*"))):
    _sj = os.path.join(_d, "shot.json")
    _mp4 = os.path.join(_d, "film/shot.mp4")
    _npz = os.path.join(_d, "depth_sharp.npz")
    if os.path.exists(_sj) and os.path.exists(_mp4) and os.path.exists(_npz):
        with open(_sj) as _f:
            _info = json.load(_f)
        _sid = os.path.basename(_d)
        SHOT_META[_sid] = _info
        BY_DISTRICT.setdefault(_info.get("district", "unknown"), []).append(_sid)

def get_territory_shots_for_poem(poem, max_shots=6):
    """
    Returns ALL shots for that poem's territory (up to max_shots=6 so every shot gets a clean
    60-degree canonical station in the Construct AND a dedicated segment in the Spacetime Worm walk).
    Always starts with the poem's own canonical shots, followed by the remaining shots of its territory!
    """
    pshots = [s["id"] for s in poem["shots"] if s["id"] in SHOT_META]
    dists = []
    for s in pshots:
        d = SHOT_META[s].get("district", "unknown")
        if d not in dists:
            dists.append(d)
    terr_all = list(pshots)
    for d in dists:
        for sid in BY_DISTRICT.get(d, []):
            if sid not in terr_all:
                terr_all.append(sid)
    if len(terr_all) < max_shots:
        for sid in BY_DISTRICT.get("commons", []):
            if sid not in terr_all:
                terr_all.append(sid)
    return terr_all[:max_shots]

POEM_SHOT_LISTS = {}
NEEDED_SHOT_IDS = set()
for _p in POEMS:
    _slist = get_territory_shots_for_poem(_p, max_shots=6)
    POEM_SHOT_LISTS[_p["num"]] = _slist
    NEEDED_SHOT_IDS.update(_slist)

_SHOT_CACHE = {}
def load_shot_data(sid, gw=128, gh=72, n_frames=32):
    """
    Loads `shots/out/<sid>/film/shot.mp4` + `depth_sharp.npz` (Apple ml-sharp depth)
    and precomputes both:
      1. Construct ray points (u, v, z_norm, oval_wt)
      2. 4D Spacetime Worm particles (high-motion extruded temporal worms + 3D architectural relief)
    """
    if sid in _SHOT_CACHE:
        return _SHOT_CACHE[sid]

    sdir = os.path.join(OUT_DIR, sid)
    mp4_path = os.path.join(sdir, "film/shot.mp4")
    npz_path = os.path.join(sdir, "depth_sharp.npz")
    info = SHOT_META[sid]

    cap = cv2.VideoCapture(mp4_path)
    total_f = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    idxs = np.linspace(0, total_f - 1, n_frames, dtype=int)
    raw_frames = []
    cur = 0
    target_set = set(idxs.tolist())
    last_rgb = None
    for fi in range(total_f):
        ok, fr = cap.read()
        if not ok:
            break
        if fi in target_set:
            rgb = cv2.cvtColor(cv2.resize(fr, (gw, gh), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
            last_rgb = rgb.astype(np.float32) / 255.0
            raw_frames.append(last_rgb)
    cap.release()
    while len(raw_frames) < n_frames:
        raw_frames.append(last_rgb if last_rgb is not None else np.zeros((gh, gw, 3), dtype=np.float32))
    frames = np.stack(raw_frames[:n_frames], axis=0)  # (T, gh, gw, 3)

    # Normalize exposure so dark shots read richly on both parchment and night
    p92 = float(np.percentile(frames.mean(axis=-1), 92))
    boost = np.clip(0.88 / max(p92, 0.07), 1.0, 2.6)
    frames = np.clip(frames * boost, 0.0, 1.0)
    frames = 1.0 - (1.0 - frames) ** 1.25

    # Load Apple ml-sharp metric depth (`depth_sharp.npz`) and convert to smooth normalized inverse depth [0..1]
    d_raw = np.load(npz_path)["depth"].astype(np.float32)
    d_small = cv2.resize(d_raw, (gw, gh), interpolation=cv2.INTER_LINEAR)
    inv = 1.0 / np.clip(d_small, 2.0, 250.0)
    lo, hi = np.nanpercentile(inv, [5, 96])
    inv_norm = np.clip((inv - lo) / max(hi - lo, 1e-4), 0.0, 1.0)
    inv_norm = cv2.GaussianBlur(inv_norm, (0, 0), 1.0)

    # 1. Construct representation (oval-masked grid of ~7,200 points per shot)
    rng = np.random.default_rng(abs(hash(sid)) % (2**31))
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
    u_grid = ((xx + rng.uniform(-0.35, 0.35, xx.shape)) / gw - 0.5) * 540.0
    v_grid = ((yy + rng.uniform(-0.35, 0.35, yy.shape)) / gh - 0.5) * 304.0
    r2 = (u_grid / 280.0) ** 2 + (v_grid / 160.0) ** 2
    keep_c = r2 < (1.06 - 0.10 * rng.random(r2.shape))
    cy_idx, cx_idx = np.where(keep_c)

    u_c = u_grid[cy_idx, cx_idx].astype(np.float32)
    v_c = v_grid[cy_idx, cx_idx].astype(np.float32)
    # Depth offset along the canonical ray [-215 .. +215]
    z_c = ((0.5 - inv_norm[cy_idx, cx_idx]) * 420.0 + rng.normal(0, 3.5, len(cx_idx))).astype(np.float32)
    wt_c = np.clip(1.10 - r2[cy_idx, cx_idx] * 0.62, 0.25, 1.0).astype(np.float32)
    rgb_c = frames[:, cy_idx, cx_idx, :].astype(np.float32)  # (T, Nc, 3)

    # 2. Spacetime Worm representation (`02d-Worms` + `07-Spacetime`):
    # Compute temporal motion + luminance salience so moving subjects form dense, undulating 4D worms!
    mot = np.linalg.norm(np.diff(frames, axis=0, prepend=frames[:1]), axis=-1)
    mot_blur = np.stack([cv2.GaussianBlur(mot[s], (0, 0), 1.8) for s in range(n_frames)], axis=0)
    m_p90 = max(float(np.percentile(mot_blur, 92)), 0.025)
    worm_mask = np.clip(mot_blur / m_p90, 0.0, 1.5)  # High on moving figures/water/lights!

    w_xs, w_ys, w_zs, w_ss, w_rgbs, w_wts, w_is_worm = [], [], [], [], [], [], []
    for s in range(n_frames):
        # Sample both structural depth points AND high-density temporal worm points
        prob = np.clip(0.14 + 0.58 * worm_mask[s] + 0.16 * inv_norm, 0.12, 0.88)
        mask_s = (rng.random((gh, gw)) < prob) & (r2 < 1.08)
        sy, sx = np.where(mask_s)
        is_w = (worm_mask[s, sy, sx] > 0.38)

        ux = u_grid[sy, sx] + rng.uniform(-1.2, 1.2, len(sx)).astype(np.float32)
        vy = v_grid[sy, sx] + rng.uniform(-1.2, 1.2, len(sy)).astype(np.float32)
        # Worm points undulate slightly like `02-dew-under-a-clear-sky-worms`
        ux = ux + is_w * (4.5 * np.sin(s * 0.42 + vy * 0.04)).astype(np.float32)
        dz_spatial = ((0.5 - inv_norm[sy, sx]) * 165.0).astype(np.float32)

        w_xs.append(ux)
        w_ys.append(vy)
        w_zs.append(dz_spatial)
        w_ss.append(np.full(len(sx), s, dtype=np.float32))
        w_rgbs.append(frames[s, sy, sx].astype(np.float32))
        w_wts.append((0.42 + 0.65 * is_w.astype(np.float32)).astype(np.float32))
        w_is_worm.append(is_w)

    data = dict(
        sid=sid,
        district=info.get("district", "world").upper(),
        bible_no=info.get("bible_no", 0),
        T=n_frames,
        # Construct arrays
        u_c=u_c,
        v_c=v_c,
        z_c=z_c,
        wt_c=wt_c,
        rgb_c=rgb_c,
        # Spacetime worm arrays
        wx=np.concatenate(w_xs),
        wy=np.concatenate(w_ys),
        wz=np.concatenate(w_zs),
        ws=np.concatenate(w_ss),
        wrgb=np.concatenate(w_rgbs),
        wwt=np.concatenate(w_wts),
        wis_worm=np.concatenate(w_is_worm),
    )
    _SHOT_CACHE[sid] = data
    return data


# ==============================================================================
# 3D POINT-CLOUD POETIC WORDS ("SPACETIME WORDS") GENERATOR
# ==============================================================================
_WORD_CLOUD_CACHE = {}
def get_word_point_cloud(label_str, line_str, accent_rgb, seed=1):
    """
    Rasterizes a poetic movement label + verse line into a 3D point cloud suspended in space,
    so the camera literally flies past and through the poem's words inside the 4D volume!
    """
    key = (label_str, line_str, tuple(accent_rgb.tolist()))
    if key in _WORD_CLOUD_CACHE:
        return _WORD_CLOUD_CACHE[key]

    cw, ch = 760, 220
    img = Image.new("L", (cw, ch), 0)
    d = ImageDraw.Draw(img)
    f_lbl = get_font("mono", 18)
    f_line = get_font("italic", 34)

    d.text((cw // 2, 42), label_str.upper(), font=f_lbl, fill=235, anchor="mm")

    # Wrap poetic line cleanly into 1 or 2 lines
    words = line_str.split()
    lines = []
    cur = []
    for w in words:
        cur.append(w)
        if len(" ".join(cur)) > 42 and len(lines) < 2:
            lines.append(" ".join(cur))
            cur = []
    if cur:
        lines.append(" ".join(cur))
    lines = lines[:2]

    for i, ln in enumerate(lines):
        d.text((cw // 2, 102 + i * 44), ln, font=f_line, fill=255, anchor="mm")

    arr = np.asarray(img, dtype=np.float32) / 255.0
    yy, xx = np.where(arr > 0.18)
    rng = np.random.default_rng(seed)
    if len(xx) > 4200:
        keep = rng.choice(len(xx), 4200, replace=False)
        yy, xx = yy[keep], xx[keep]

    x = ((xx - cw * 0.5) * 0.62 + rng.normal(0, 0.35, len(xx))).astype(np.float32)
    y = ((yy - ch * 0.5) * 0.62 + rng.normal(0, 0.35, len(yy))).astype(np.float32)
    z = rng.normal(0, 6.0, len(xx)).astype(np.float32)
    wt = (arr[yy, xx] * 1.35).astype(np.float32)

    # Tint header label with poem accent color, verse with warm cream/ink
    is_hdr = yy < 66
    col_light = np.zeros((len(xx), 3), dtype=np.float32)
    col_light[is_hdr] = np.clip(accent_rgb * 1.15 + 0.18, 0.0, 1.0)
    col_light[~is_hdr] = np.array([0.98, 0.94, 0.86], dtype=np.float32)

    col_paper = np.zeros((len(xx), 3), dtype=np.float32)
    col_paper[is_hdr] = np.clip(accent_rgb * 0.72, 0.0, 0.85)
    col_paper[~is_hdr] = np.array([0.11, 0.09, 0.07], dtype=np.float32)

    res = dict(x=x, y=y, z=z, wt=wt, col_light=col_light, col_paper=col_paper)
    _WORD_CLOUD_CACHE[key] = res
    return res


# ==============================================================================
# MODE 1 RENDERER: MULTI-SHOT TERRITORY CONSTRUCT FOR A POEM (or MASTER)
# All N shots of that Territory coexist in ONE shared 3D point cloud!
# ==============================================================================
def render_poem_construct_frame(poem_idx, fi, total_frames):
    poem = POEMS[poem_idx]
    shot_ids = POEM_SHOT_LISTS[poem["num"]]
    N = len(shot_ids)
    dur = total_frames / FPS
    t = fi / FPS

    D_cam = 680.0
    # Camera trajectory across N canonical angles: theta_k = k * (2*pi / N)
    # Each station gets a crisp alignment hold + smooth 3D orbital transition to the next station
    seg_dur = dur / N
    station_f = t / seg_dur
    k_cur = int(math.floor(station_f)) % N
    k_next = (k_cur + 1) % N
    u_seg = station_f - math.floor(station_f)

    # Hold alignment for 55% of each segment, then orbit smoothly over the remaining 45%
    if u_seg < 0.55:
        orbit_u = 0.0
        lock = smootherstep(min(1.0, u_seg / 0.14)) if k_cur == 0 and t < 1.0 else 1.0
    else:
        orbit_u = smootherstep((u_seg - 0.55) / 0.45)
        lock = 1.0 - math.sin(orbit_u * math.pi)

    step_rad = 2.0 * math.pi / N
    yaw = (k_cur + orbit_u) * step_rad
    pitch = 0.15 * (1.0 - lock) * math.sin(yaw * (N * 0.5))

    # Initial dust-to-cloud assembly in the first 0.9s
    scatter = (1.0 - smootherstep(t / 0.95)) ** 2 if t < 0.95 else 0.0
    rng = np.random.default_rng(poem_idx * 1000 + fi)

    all_X, all_Y, all_Z, all_rgb, all_w, all_rad = [], [], [], [], [], []
    active_k = k_cur if orbit_u < 0.5 else k_next

    for k, sid in enumerate(shot_ids):
        sd = load_shot_data(sid)
        th_k = k * step_rad

        # Angular distance between current camera yaw and shot k's canonical ray th_k
        ang_d = abs((yaw - th_k + math.pi) % (2.0 * math.pi) - math.pi)
        align = smootherstep(np.clip(1.0 - ang_d / (step_rad * 0.78), 0.0, 1.0))

        # Perspective-compensated ray placement so at yaw == th_k, (Xc/Zc)*D_cam == u_c!
        scale_k = (D_cam + sd["z_c"]) / D_cam
        xl = sd["u_c"] * scale_k
        yl = sd["v_c"] * scale_k
        zl = sd["z_c"]

        rk_x, rk_z = math.cos(th_k), math.sin(th_k)
        fk_x, fk_z = -math.sin(th_k), math.cos(th_k)

        Xw = xl * rk_x + zl * fk_x
        Yw = yl
        Zw = xl * rk_z + zl * fk_z

        if scatter > 1e-4:
            Xw = Xw + rng.normal(0, 240.0 * scatter, len(Xw)).astype(np.float32)
            Yw = Yw + rng.normal(0, 160.0 * scatter, len(Yw)).astype(np.float32)
            Zw = Zw + rng.normal(0, 240.0 * scatter, len(Zw)).astype(np.float32)

        # Video frame index (ping-pong loop)
        T_len = sd["T"]
        v_idx = int(t * 18) % (2 * T_len - 2)
        if v_idx >= T_len:
            v_idx = 2 * T_len - 2 - v_idx
        rgb = sd["rgb_c"][v_idx]

        # All N shots of the territory remain in the shared cloud simultaneously!
        ghost_w = (0.045 + 0.16 * (1.0 - lock)) * (6.0 / N)
        w_k = sd["wt_c"] * (align * 0.96 + (1.0 - align) * ghost_w)

        lum = rgb.mean(axis=-1, keepdims=True)
        sepia = np.concatenate([lum * 0.80 + 0.08, lum * 0.75 + 0.07, lum * 0.68 + 0.06], axis=-1)
        rgb_k = rgb * (0.35 + 0.65 * align) + sepia * (0.65 * (1.0 - align))
        rad_k = np.full(len(Xw), 0.90 * align + 1.85 * (1.0 - align), dtype=np.float32)

        all_X.append(Xw)
        all_Y.append(Yw)
        all_Z.append(Zw)
        all_rgb.append(rgb_k)
        all_w.append(w_k)
        all_rad.append(rad_k)

    Xw = np.concatenate(all_X)
    Yw = np.concatenate(all_Y)
    Zw = np.concatenate(all_Z)
    rgb = np.concatenate(all_rgb)
    wt = np.concatenate(all_w)
    rad_b = np.concatenate(all_rad)

    cy, sy = math.cos(-yaw), math.sin(-yaw)
    Xc = Xw * cy + Zw * sy
    Zc1 = -Xw * sy + Zw * cy

    cp, sp = math.cos(pitch), math.sin(pitch)
    Yc = Yw * cp - Zc1 * sp
    Zc = Yw * sp + Zc1 * cp + D_cam

    focal = 580.0
    px = focal * Xc / np.maximum(Zc, 22.0) + RW * 0.5
    py = focal * Yc / np.maximum(Zc, 22.0) + RH * 0.5
    dof = np.abs(Zc - D_cam) / 210.0 * (1.0 - 0.72 * lock)
    rad = np.clip(rad_b + dof, 0.75, 5.6)

    img = splat_gaussian_fast(px, py, Zc, rad, rgb, wt, mode="paper", gain=1.10, seed=fi)

    # Clean Afterlight Screening Room overlay
    pil = Image.fromarray((img * 255.0).astype(np.uint8))
    draw = ImageDraw.Draw(pil, "RGBA")
    f_mono_sm = get_font("mono", 14)
    f_mono_md = get_font("mono", 16)
    f_italic = get_font("italic", 34)
    f_serif = get_font("serif", 19)

    ink_dark = (36, 30, 24, 225)
    ink_muted = (90, 80, 68, 180)

    draw.text((46, 34), f"P{poem['num']} · {poem['title']}  —  TERRITORY CONSTRUCT ({N} SHOTS IN ONE CLOUD)", font=f_mono_md, fill=ink_dark)
    deg_now = int(round(math.degrees(yaw))) % 360
    st_txt = f"SHOT {active_k+1}/{N} ALIGNED" if lock > 0.65 else "ORBITING SHARED 3D CLOUD"
    draw.text((FW - 46, 34), f"AZIMUTH {deg_now:03d}°  [{st_txt}]", font=f_mono_sm, fill=ink_dark, anchor="ra")

    # Bottom-right station ticks for all N territory shots
    for k in range(N):
        xt = FW - 46 - (N - 1 - k) * 56
        yt = FH - 44
        ang_k = int(round(k * 360.0 / N))
        is_act = (k == active_k and lock > 0.5)
        col_t = (28, 22, 18, 240) if is_act else (115, 104, 90, 135)
        draw.text((xt, yt), f"S{k+1}·{ang_k}°", font=f_mono_sm, fill=col_t, anchor="ra")

    # Bottom-left movement verse line & active territory shot info
    moves = poem.get("movements", [])
    mv = moves[min(len(moves) - 1, int(t / dur * len(moves)))] if moves else {"label": "", "line": poem.get("tagline", "")}
    act_sd = load_shot_data(shot_ids[active_k])
    draw.text((46, FH - 82), f"{poem['district_name']}  ·  Station {active_k+1} of {N} ({int(round(active_k*360/N))}° — #{act_sd['bible_no']})", font=f_italic, fill=(32, 26, 20, 230))
    line_short = mv["line"][:88] + ("…" if len(mv["line"]) > 88 else "")
    draw.text((48, FH - 44), f"[{mv['label']}]  “{line_short}”", font=f_serif, fill=ink_muted)

    arr = np.asarray(pil, dtype=np.float32) / 255.0
    if t < 0.5:
        a = ease(t / 0.5)
        arr = PAPER * (1.0 - a) + arr * a
    elif t > dur - 0.6:
        a = ease((dur - t) / 0.6)
        arr = PAPER * (1.0 - a) + arr * a
    return (np.clip(arr, 0.0, 1.0) * 255.0).astype(np.uint8)


# ==============================================================================
# MODE 2 RENDERER: SPACETIME WORM & WORDS JOURNEY FOR A POEM
# Continuous 3D camera flight through all territory shots + 4D extruded worms + 3D point-cloud words!
# ==============================================================================
def render_poem_spacetime_worm_frame(poem_idx, fi, total_frames):
    poem = POEMS[poem_idx]
    shot_ids = POEM_SHOT_LISTS[poem["num"]]
    M = len(shot_ids)
    dur = total_frames / FPS
    t = fi / FPS
    u_all = t / max(dur, 1e-4)

    accent_rgb = hex_to_rgb(poem.get("color", "#d98a12"))
    # Alternate paper and night modes cleanly or use night for neon/haze poems and paper/night transitions
    use_light_mode = (poem_idx % 2 == 0) or ("LIGHT" in poem["title"]) or ("ATLANTIS" in poem["title"]) or ("MAGIC" in poem["title"])
    mode = "light" if use_light_mode else "paper"

    # The camera flies continuously along Z_world from Z = 0 to Z = M * 620.0
    Z_spacing = 620.0
    cam_Z = u_all * (M * Z_spacing)
    # Gentle lateral weaving and side-on banking so the 4D extruded worms are seen both frontally and at ±48 deg!
    cam_X = 65.0 * math.sin(u_all * M * math.pi)
    cam_Y = -14.0 * math.cos(u_all * M * math.pi * 0.5)
    yaw = 0.52 * math.sin(u_all * M * math.pi * 2.0)  # Swings between -30 deg and +30 deg through each shot's worm!
    pitch = 0.06 * math.cos(u_all * M * math.pi)

    all_X, all_Y, all_Z, all_rgb, all_w, all_rad = [], [], [], [], [], []

    # 1. Gather visible shot volumes & their 4D extruded spacetime worms along the corridor
    for m, sid in enumerate(shot_ids):
        z_station = (m + 0.55) * Z_spacing
        dz_cam = z_station - cam_Z
        if dz_cam < -360.0 or dz_cam > 1450.0:
            continue

        sd = load_shot_data(sid)
        # Local progress as camera approaches and passes through station m
        u_local = np.clip(1.0 - (dz_cam - 120.0) / Z_spacing, 0.0, 1.2)
        present = (0.15 + 0.78 * np.clip(u_local, 0.0, 1.0)) * (sd["T"] - 1)
        age = present - sd["ws"]

        # Keep 24 past slices trailing behind the present slice (the 4D spacetime worm!)
        vis = (age >= -2.0) & (age <= 24.0)
        if not np.any(vis):
            continue

        wx = sd["wx"][vis]
        wy = sd["wy"][vis]
        wz = sd["wz"][vis]
        wage = age[vis]
        wrgb = sd["wrgb"][vis]
        wwt = sd["wwt"][vis]
        is_w = sd["wis_worm"][vis]

        # Extrude worm points along Z by age * 16.5 so moving figures form long, visible 3D temporal tubes!
        dz_worm = np.where(is_w, 16.5, 9.5).astype(np.float32)
        X_world = wx + (45.0 * (1 if m % 2 == 0 else -1))
        Y_world = wy
        Z_world = z_station + wz + wage * dz_worm

        # Highlight moving worm filaments with a subtle luminous tint
        decay = np.where(wage >= 0, np.exp(-wage / (15.5 if True else 9.0)), np.exp(-(wage ** 2) / 1.1)).astype(np.float32)
        dist_fade = np.clip(1.0 - abs(dz_cam - 260.0) / 980.0, 0.15, 1.0)
        wt_pts = wwt * decay * dist_fade

        # Give the trailing worm body a warm/accent chromatic shift so the temporal trail is unmistakably felt
        worm_tint = np.clip( np.minimum(1.0, np.maximum(0.0, wage / 16.0))[:, None] * (0.45 * is_w[:, None]), 0.0, 0.55 ).astype(np.float32)
        rgb_pts = wrgb * (1.0 - worm_tint) + accent_rgb[None, :] * worm_tint

        rad_pts = np.where(is_w & (wage > 1.5), 1.45 + 0.06 * wage, 0.95).astype(np.float32)

        all_X.append(X_world)
        all_Y.append(Y_world)
        all_Z.append(Z_world)
        all_rgb.append(rgb_pts)
        all_w.append(wt_pts)
        all_rad.append(rad_pts)

    # 2. Suspend the Poem's Movements & Verses as 3D Point-Cloud Words ("Spacetime Words") inside the corridor!
    moves = poem.get("movements", [])
    n_moves = len(moves)
    for mi, mv in enumerate(moves):
        z_word = ((mi + 0.38) / max(n_moves, 1)) * (M * Z_spacing)
        dz_w = z_word - cam_Z
        if dz_w < -120.0 or dz_w > 980.0:
            continue
        wc = get_word_point_cloud(
            f"{poem['num']}.{mi+1} · {mv['label']}",
            mv["line"],
            accent_rgb,
            seed=poem_idx * 50 + mi
        )
        # Coalesce out of dust as camera approaches from 900 -> 380, hold crisp, then drift past camera!
        sc_w = np.clip((dz_w - 420.0) / 480.0, 0.0, 1.0) ** 2
        rng_w = np.random.default_rng(poem_idx * 100 + mi)
        wx_p = wc["x"] + (rng_w.normal(0, 180.0 * sc_w, len(wc["x"])).astype(np.float32) if sc_w > 0.01 else 0.0)
        wy_p = wc["y"] - 18.0 + (rng_w.normal(0, 120.0 * sc_w, len(wc["y"])).astype(np.float32) if sc_w > 0.01 else 0.0)
        wz_p = z_word + wc["z"] + (rng_w.normal(0, 180.0 * sc_w, len(wc["z"])).astype(np.float32) if sc_w > 0.01 else 0.0)

        w_alpha = smooth_fade = smootherstep(np.clip((dz_w + 80.0) / 160.0, 0.0, 1.0)) * smootherstep(np.clip((960.0 - dz_w) / 240.0, 0.0, 1.0))
        col_w = wc["col_light"] if mode == "light" else wc["col_paper"]

        all_X.append(wx_p)
        all_Y.append(wy_p)
        all_Z.append(wz_p)
        all_rgb.append(col_w)
        all_w.append(wc["wt"] * w_alpha * 1.45)
        all_rad.append(np.full(len(wx_p), 0.92 + 1.8 * sc_w, dtype=np.float32))

    if not all_X:
        bg = PAPER if mode == "paper" else NIGHT
        return (np.broadcast_to(bg, (FH, FW, 3)) * 255.0).astype(np.uint8)

    Xw = np.concatenate(all_X) - cam_X
    Yw = np.concatenate(all_Y) - cam_Y
    Zw = np.concatenate(all_Z) - cam_Z
    rgb = np.concatenate(all_rgb)
    wt = np.concatenate(all_w)
    rad_b = np.concatenate(all_rad)

    cy, sy = math.cos(yaw), math.sin(yaw)
    Xc = Xw * cy + Zw * sy
    Zc1 = -Xw * sy + Zw * cy

    cp, sp = math.cos(pitch), math.sin(pitch)
    Yc = Yw * cp - Zc1 * sp
    Zc = Yw * sp + Zc1 * cp

    focal = 520.0
    px = focal * Xc / np.maximum(Zc, 22.0) + RW * 0.5
    py = focal * Yc / np.maximum(Zc, 22.0) + RH * 0.5
    dof = np.abs(Zc - 310.0) / 260.0
    rad = np.clip(rad_b + dof * 0.65, 0.75, 5.5)

    img = splat_gaussian_fast(px, py, Zc, rad, rgb, wt, mode=mode, gain=1.12, seed=fi)

    # Clean Afterlight HUD overlay
    pil = Image.fromarray((img * 255.0).astype(np.uint8))
    draw = ImageDraw.Draw(pil, "RGBA")
    f_mono = get_font("mono", 14)
    fg = (42, 36, 30, 195) if mode == "paper" else (238, 230, 214, 195)

    cur_shot_idx = min(M - 1, int(u_all * M))
    cur_sd = load_shot_data(shot_ids[cur_shot_idx])
    draw.text((46, 34), f"P{poem['num']} · {poem['title']}  —  SPACETIME WORM & WORDS  [SHOT {cur_shot_idx+1}/{M} · #{cur_sd['bible_no']}]", font=f_mono, fill=fg)
    draw.text((FW - 46, 34), f"Z-CORRIDOR {int(cam_Z):04d}m  ·  YAW {math.degrees(yaw):+05.1f}°", font=f_mono, fill=fg, anchor="ra")

    return np.asarray(pil, dtype=np.uint8)


# ==============================================================================
# PROCEDURAL POEM SCORE SYNTHESIZER (Uses each poem's exact drone & mode from poems.json!)
# ==============================================================================
SR = 44100

def lp_filter(sig, cutoff, order=2):
    b, a = butter(order, min(0.98, cutoff / (SR * 0.5)), btype="low")
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

def build_poem_score_wav(poem, dur, wav_path, kind="construct"):
    buf = np.zeros((int(dur * SR), 2), dtype=np.float64)
    base_f = float(poem.get("drone", {}).get("base", 32.7))
    while base_f < 55.0:
        base_f *= 2.0
    steps = poem.get("drone", {}).get("steps", [0, 7, 12]) or [0]

    # Harmonic drone pad using the poem's microtonal steps
    t_full = np.arange(int(dur * SR)) / SR
    env_full = np.minimum(1.0, t_full / 1.0) * np.minimum(1.0, (dur - t_full) / 1.2)
    for i, st in enumerate(steps[:4]):
        freq = base_f * (2.0 ** (st / 12.0))
        sig = (
            np.sin(2 * math.pi * freq * t_full)
            + 0.55 * np.sin(2 * math.pi * freq * 2.002 * t_full)
            + 0.25 * np.sin(2 * math.pi * freq * 3.0 * t_full)
        ) * env_full * 0.055
        add_stereo(buf, 0.0, lp_filter(sig, 880), pan=(i - 1.5) * 0.35)

    # Bell & kalimba accents at each territory shot station
    n_stations = len(POEM_SHOT_LISTS[poem["num"]])
    seg = dur / n_stations
    for k in range(n_stations):
        t0 = k * seg + 0.15
        st = steps[k % len(steps)]
        f_bell = base_f * 4.0 * (2.0 ** (st / 12.0))
        tb = np.arange(int(2.8 * SR)) / SR
        bell = (
            np.sin(2 * math.pi * f_bell * tb) * np.exp(-tb * 1.3)
            + 0.4 * np.sin(2 * math.pi * f_bell * 2.0 * tb) * np.exp(-tb * 2.4)
        ) * (1.0 - np.exp(-tb * 90.0)) * 0.11
        add_stereo(buf, t0, bell, pan=(-0.35 if k % 2 == 0 else 0.35))

        if kind == "worm":
            # Flowing arpeggiated worm pulses between stations
            for sub in range(4):
                ts = t0 + sub * (seg * 0.22)
                f_k = f_bell * (1.25 if sub % 2 else 1.0)
                tk = np.arange(int(0.9 * SR)) / SR
                kal = np.sin(2 * math.pi * f_k * tk) * np.exp(-tk * 4.5) * (1.0 - np.exp(-tk * 180.0)) * 0.07
                add_stereo(buf, ts, kal, pan=((sub % 3) - 1) * 0.4)

    # Simple stereo reverb
    out = buf.copy()
    for delay_ms, g in [(83, 0.26), (149, 0.19), (251, 0.12)]:
        d = int(delay_ms * SR / 1000)
        if d < len(buf):
            out[d:, 0] += buf[:-d, 1] * g
            out[d:, 1] += buf[:-d, 0] * g
    peak = np.max(np.abs(out))
    if peak > 1e-5:
        out = np.tanh(out / peak * 1.15) * 0.86

    pcm = (np.clip(out, -1.0, 1.0) * 32767.0).astype(np.int16)
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


# ==============================================================================
# WORKER DISPATCH FOR PARALLEL MP4 RENDERING
# ==============================================================================
def _worker_construct(args):
    poem_idx, fi, total_frames = args
    return render_poem_construct_frame(poem_idx, fi, total_frames)

def _worker_worm(args):
    poem_idx, fi, total_frames = args
    return render_poem_spacetime_worm_frame(poem_idx, fi, total_frames)


def render_mp4_with_pool(pool, worker_fn, poem_idx, total_frames, out_mp4, wav_path):
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}", "-r", str(FPS), "-i", "-",
        "-i", wav_path,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest",
        "-movflags", "+faststart",
        out_mp4
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    tasks = [(poem_idx, fi, total_frames) for fi in range(total_frames)]
    mid_frame = None
    mid_idx = total_frames // 2

    for fi, rgb_u8 in enumerate(pool.imap(worker_fn, tasks, chunksize=12)):
        proc.stdin.write(rgb_u8.tobytes())
        if fi == mid_idx:
            mid_frame = rgb_u8

    proc.stdin.close()
    proc.wait()
    if os.path.exists(wav_path):
        os.remove(wav_path)
    return mid_frame


def main():
    t0_all = time.time()
    os.makedirs(POEM_VID_DIR, exist_ok=True)
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    print(f"Preloading {len(NEEDED_SHOT_IDS)} territory shots (shot.mp4 + Apple ml-sharp depth_sharp.npz) into shared RAM...", flush=True)
    for idx, sid in enumerate(sorted(NEEDED_SHOT_IDS)):
        load_shot_data(sid)
        if (idx + 1) % 10 == 0 or (idx + 1) == len(NEEDED_SHOT_IDS):
            print(f"  Loaded {idx+1}/{len(NEEDED_SHOT_IDS)} shots ({time.time() - t0_all:.1f}s)", flush=True)

    # Pre-warm fonts and 3D word clouds before forking so workers share everything zero-copy!
    for p_idx, p in enumerate(POEMS):
        acc = hex_to_rgb(p.get("color", "#d98a12"))
        for mi, mv in enumerate(p.get("movements", [])):
            get_word_point_cloud(f"{p['num']}.{mi+1} · {mv['label']}", mv["line"], acc, seed=p_idx * 50 + mi)

    ctx = mp.get_context("fork")
    n_workers = min(12, os.cpu_count() or 8)
    print(f"Starting forked pool with {n_workers} workers...", flush=True)

    construct_thumbs = []
    worm_thumbs = []
    construct_mp4s = []
    worm_mp4s = []

    # Each full poem gets a 12.0s (288-frame) Multi-Shot Territory Construct AND a 14.0s (336-frame) Spacetime Worm & Words film!
    C_FRAMES = 12 * FPS  # 288 frames (12.0s per poem -> 6 territory shots @ 2.0s each)
    W_FRAMES = 14 * FPS  # 336 frames (14.0s per poem -> matches exact 14.0s duration of poem_01..14.mp4!)

    with ctx.Pool(processes=n_workers) as pool:
        for p_idx, p in enumerate(POEMS):
            t_p = time.time()
            num = p["num"]
            n_terr = len(POEM_SHOT_LISTS[num])

            # 1. Render Poem Territory Construct (`poem_<num>_construct.mp4`)
            c_mp4 = os.path.join(POEM_VID_DIR, f"poem_{num}_construct.mp4")
            c_jpg = os.path.join(POEM_VID_DIR, f"poem_{num}_construct.jpg")
            c_wav = os.path.join(POEM_VID_DIR, f"poem_{num}_construct.wav")
            build_poem_score_wav(p, C_FRAMES / FPS, c_wav, kind="construct")
            c_mid = render_mp4_with_pool(pool, _worker_construct, p_idx, C_FRAMES, c_mp4, c_wav)
            Image.fromarray(c_mid).save(c_jpg, quality=88)
            construct_thumbs.append((p, c_mid))
            construct_mp4s.append(c_mp4)

            # 2. Render Poem Spacetime Worm & Words (`poem_<num>_spacetime_worm.mp4`)
            w_mp4 = os.path.join(POEM_VID_DIR, f"poem_{num}_spacetime_worm.mp4")
            w_jpg = os.path.join(POEM_VID_DIR, f"poem_{num}_spacetime_worm.jpg")
            w_wav = os.path.join(POEM_VID_DIR, f"poem_{num}_spacetime_worm.wav")
            build_poem_score_wav(p, W_FRAMES / FPS, w_wav, kind="worm")
            w_mid = render_mp4_with_pool(pool, _worker_worm, p_idx, W_FRAMES, w_mp4, w_wav)
            Image.fromarray(w_mid).save(w_jpg, quality=88)
            worm_thumbs.append((p, w_mid))
            worm_mp4s.append(w_mp4)

            print(f"[Poem {num}/14 · {p['title']:30s}] Rendered {n_terr}-shot Construct + Spacetime Worm in {time.time() - t_p:.1f}s", flush=True)

    # Build Master Anthology Reels by concatenating the 14 Territory Constructs and 14 Spacetime Worm films
    # AND keep fast 60s showcase cuts at `wygwyl_seeing_construct.mp4` and `wygwyl_07_spacetime.mp4`!
    concat_c_txt = os.path.join(POEM_VID_DIR, "concat_construct.txt")
    with open(concat_c_txt, "w") as f:
        for pth in construct_mp4s:
            f.write(f"file '{pth}'\n")
    master_c_all = os.path.join(VID_DIR, "wygwyl_14poems_construct_suite.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", concat_c_txt, "-c", "copy", "-movflags", "+faststart", master_c_all], check=True)
    # Also update wygwyl_seeing_construct.mp4 with the multi-shot territory construct suite
    subprocess.run(["cp", master_c_all, os.path.join(VID_DIR, "wygwyl_seeing_construct.mp4")], check=True)

    concat_w_txt = os.path.join(POEM_VID_DIR, "concat_worm.txt")
    with open(concat_w_txt, "w") as f:
        for pth in worm_mp4s:
            f.write(f"file '{pth}'\n")
    master_w_all = os.path.join(VID_DIR, "wygwyl_14poems_spacetime_worms_suite.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", concat_w_txt, "-c", "copy", "-movflags", "+faststart", master_w_all], check=True)
    subprocess.run(["cp", master_w_all, os.path.join(VID_DIR, "wygwyl_07_spacetime.mp4")], check=True)

    # Build two 14-panel contact sheets (one for all 14 Territory Constructs, one for all 14 Spacetime Worms & Words)
    def save_14_sheet(items, out_png, banner):
        tw, th = 380, 214
        pad = 12
        hdr = 64
        cols, rows = 4, 4
        sheet = Image.new("RGB", (cols * tw + (cols + 1) * pad, hdr + rows * th + (rows + 1) * pad), (235, 227, 207))
        d = ImageDraw.Draw(sheet)
        d.text((pad, 18), banner, font=get_font("serif", 25), fill=(28, 24, 20))
        f_tag = get_font("mono", 12)
        for idx, (p, rgb) in enumerate(items):
            r, c = divmod(idx, cols)
            x0 = pad + c * (tw + pad)
            y0 = hdr + pad + r * (th + pad)
            im = Image.fromarray(rgb).resize((tw, th), Image.Resampling.LANCZOS)
            sheet.paste(im, (x0, y0))
            d.rectangle([x0, y0, x0 + tw, y0 + 22], fill=(24, 20, 16))
            d.text((x0 + 8, y0 + 4), f"P{p['num']} · {p['title'][:22]} ({p['district_name'][:18]})", font=f_tag, fill=(242, 235, 220))
        sheet.save(out_png, quality=92)

    sheet_c = os.path.join(ARTIFACT_DIR, "all_14_poems_territory_construct_sheet.png")
    sheet_w = os.path.join(ARTIFACT_DIR, "all_14_poems_spacetime_worms_sheet.png")
    save_14_sheet(construct_thumbs, sheet_c, "ALL 14 POEMS · S2 TERRITORY CONSTRUCTS — All Territory Shots in One Shared 3D Point Cloud per Poem")
    save_14_sheet(worm_thumbs, sheet_w, "ALL 14 POEMS · 07w SPACETIME WORMS & WORDS — Continuous World Walk + 4D Motion Worms + 3D Point-Cloud Words")

    print(f"ALL 28 POEM FILMS + 2 MASTER SUITES COMPLETED in {time.time() - t0_all:.1f}s!", flush=True)


if __name__ == "__main__":
    main()
