#!/usr/bin/env python3
"""
Builds the 14 Poem Films in Two Companion Modes + Master Anthology Reels (`1280x720`, 24fps):
  1. `S2 · Common Places & Painted Cels Construct` (`poem_01_construct.mp4` .. `poem_14_construct.mp4`):
     - Exact projective ray-bundle math from `seeing-construct.mp4` (`afterlight/source/semantic/render.py.txt`):
       5 canonical Common Place & Cel stations per Poem (`30.0s` = `6.0s` per station).
     - ZERO head-wagging / ZERO oscillation:
       For `4.3s` of every `6.0s` station (`72%` of the film), the camera is 100% STATIONARY (`yaw = theta_k`, `pitch = 0`)
       and the station's 1280x720 Painted Cel + Multiplane Animation (`program/frame0.png` angular facets ->
       `cartoon/cel.png` + `cartoon/ink.png` + `film/shot.mp4`) fills 100% of the screen edge-to-edge with crystal legibility,
       while the other 4 places of the city drift softly in deep 3D space.
     - During the `1.7s` transition between stations, the camera rotates smoothly in ONE single forward direction
       (`0° -> 72° -> 144° -> 216° -> 288° -> 360°`, NEVER reversing or wagging!) as the full-screen cel lifts along its
       `depth_sharp.npz` rays into 240,000 crisp Painter's-Algorithm 3D points on warm paper (`#F2EDE2`) and snaps
       edge-to-edge into the next Common Place.

  2. `07w · Spacetime Worm & City Walk` (`poem_01_spacetime_worm.mp4` .. `poem_14_spacetime_worm.mp4`):
     - ZERO head-wagging / 100% full-frame legibility:
       Camera looks straight ahead (`yaw = 0, pitch = 0`) and moves strictly forward along `+Z` through all shots of the poem
       and its City District Common Places.
     - Each shot fills 100% of the 1280x720 frame with the vibrant Painted Cel (`cel_v2/*.png`, `cartoon/cel.png`,
       `program/frame0.png`, `cartoon/ink.png`), graded with the City District's measured `body` and `glow` palettes from
       `_city/districts.json`.
     - Behind the 100% sharp foreground subject (`layers/fg.png` / `fg_mask`), its past temporal slices (`t - dt`) extrude
       into a sculpted 3D Spacetime Worm ribbon (receding die-cut cel echoes + district-glow contour rings composited BEHIND
       the foreground subject so they NEVER obscure the subject or scene!).
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

W, H = 1280, 720
FPS = 24

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
SHOTS_ROOT = os.path.join(ROOT, "shots")
CITY_JSON = os.path.join(ROOT, "_city/districts.json")
CORPUS_ROOT = "/Users/gaia/Downloads/WYGWYL-CORPUS-ARCH"
OUT_DIR = os.path.join(SHOTS_ROOT, "data/terrarium/seeing_spacetime_films")
VIDEOS_DIR = os.path.join(SHOTS_ROOT, "videos")
POEMS_VID_DIR = os.path.join(VIDEOS_DIR, "poems")
ARTIFACT_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"
MASTER_AUDIO = os.path.join(SHOTS_ROOT, "cel_assets/WYGWYL_Suite_Audio.mp3")

PAPER_BG = np.array([0.945, 0.928, 0.892], dtype=np.float32)

_FONT_CACHE = {}
def get_font(kind="serif_italic", size=24):
    key = (kind, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    paths = {
        "serif_italic": [
            "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
        ],
        "serif_bold": [
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        ],
        "serif": [
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        ],
        "mono": [
            "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
            "/System/Library/Fonts/Menlo.ttc",
        ],
    }
    for p in paths.get(kind, paths["serif"]):
        if os.path.exists(p):
            try:
                f = ImageFont.truetype(p, size)
                _FONT_CACHE[key] = f
                return f
            except Exception:
                pass
    f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def hex_to_rgb_float(h_str):
    h_str = (h_str or "#fa8d15").lstrip("#")
    if len(h_str) != 6:
        return np.array([0.98, 0.55, 0.08], dtype=np.float32)
    return np.array([int(h_str[0:2], 16), int(h_str[2:4], 16), int(h_str[4:6], 16)], dtype=np.float32) / 255.0


def hex_to_rgb_u8(h_str):
    h_str = (h_str or "#fa8d15").lstrip("#")
    if len(h_str) != 6:
        return (250, 141, 21)
    return (int(h_str[0:2], 16), int(h_str[2:4], 16), int(h_str[4:6], 16))


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


def rotmat_y(yaw):
    cy, sy = math.cos(yaw), math.sin(yaw)
    return np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float32)


def load_rgb_resized(path, w=W, h=H):
    if not path or not os.path.exists(path):
        return None
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:
        return None
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    if im.shape[1] != w or im.shape[0] != h:
        im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    return im.astype(np.float32) / 255.0


def load_rgba_resized(path, w=W, h=H):
    if not path or not os.path.exists(path):
        return None
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGBA)
    elif im.shape[2] == 3:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGBA)
    else:
        im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
    if im.shape[1] != w or im.shape[0] != h:
        im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    return im.astype(np.float32) / 255.0


def build_city_master_index():
    """
    Loads `_city/districts.json`, `shots/out/*/shot.json`, and `shots/poems/atlas/01..14.json`
    so every Common Place, City District, Body+Glow Palette, and Cel asset is indexed accurately.
    """
    city_data = json.load(open(CITY_JSON)) if os.path.exists(CITY_JSON) else {"districts": [], "poems": [], "files": {}}
    districts_by_id = {d["id"]: d for d in city_data.get("districts", [])}

    bible_to_dir = {}
    id_to_dir = {}
    for sj in sorted(glob.glob(os.path.join(SHOTS_ROOT, "out/*/shot.json"))):
        try:
            d = json.load(open(sj))
            odir = os.path.dirname(sj)
            sid = os.path.basename(odir)
            id_to_dir[sid] = odir
            if d.get("bible_no") is not None:
                bible_to_dir[int(d["bible_no"])] = odir
        except Exception:
            pass

    hero_poems = {}
    for p in sorted(glob.glob(os.path.join(SHOTS_ROOT, "poems/atlas/[0-9][0-9].json"))):
        ad = json.load(open(p))
        pnum = int(ad["num"])
        for h in ad.get("heroes", []):
            hid = h["id"]
            tag = f"P{pnum:02d}"
            if tag not in hero_poems.setdefault(hid, []):
                hero_poems[hid].append(tag)

    return city_data, districts_by_id, bible_to_dir, id_to_dir, hero_poems


def build_cel_plate_from_dir(odir, body_hex, glow_hex, w=W, h=H):
    """
    Builds two 100% legible, vibrant Cel plates from a `shots/out/<id>` or keyframe directory:
      1. `angular_cel`: `program/frame0.png` + `cartoon/consensus.png` + `cartoon/ink.png`
         (the bold faceted polygon cel style from `wygwyl_cartoon.mp4`)
      2. `painted_cel`: `cartoon/cel.png` + `program/frame0.png` + `multiplane/glow_pass.png` + `cartoon/ink.png`
    """
    prog0 = load_rgb_resized(os.path.join(odir, "program/frame0.png"), w, h)
    cel = load_rgb_resized(os.path.join(odir, "cartoon/cel.png"), w, h)
    flats = load_rgb_resized(os.path.join(odir, "cartoon/flats.png"), w, h)
    consensus = load_rgb_resized(os.path.join(odir, "cartoon/consensus.png"), w, h)
    ink = load_rgba_resized(os.path.join(odir, "cartoon/ink.png"), w, h)
    glow = load_rgb_resized(os.path.join(odir, "multiplane/glow_pass.png"), w, h)
    img_jpg = load_rgb_resized(os.path.join(odir, "image.jpg"), w, h)

    # 1. Angular Faceted Cel (`program/frame0.png` + `flats.png` + `consensus.png` + crisp ink)
    ang = prog0 if prog0 is not None else (flats if flats is not None else cel)
    if ang is None:
        ang = img_jpg if img_jpg is not None else np.full((h, w, 3), 0.5, dtype=np.float32)
    if consensus is not None:
        ang = 0.78 * ang + 0.22 * consensus
    if glow is not None:
        ang = np.clip(ang + 0.25 * glow, 0.0, 1.0)
    if ink is not None:
        ia = ink[..., 3:4] * 0.85
        ang = ang * (1.0 - ia) + ink[..., :3] * ia

    # 2. Rich Painted Multiplane Cel (`cartoon/cel.png` + `program/frame0.png` + `image.jpg` detail + `glow`)
    pnt = cel if cel is not None else ang
    if prog0 is not None and cel is not None:
        pnt = 0.62 * cel + 0.38 * prog0
    if img_jpg is not None:
        pnt = 0.78 * pnt + 0.22 * img_jpg
    if glow is not None:
        pnt = np.clip(pnt + 0.30 * glow, 0.0, 1.0)
    if ink is not None:
        ia = ink[..., 3:4] * 0.75
        pnt = pnt * (1.0 - ia) + ink[..., :3] * ia

    # Boost chroma saturation slightly so district colors sing clearly
    for arr in (ang, pnt):
        hsv = cv2.cvtColor((np.clip(arr, 0.0, 1.0) * 255.0).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[..., 1] = np.clip(hsv[..., 1] * 1.22, 0.0, 255.0)
        arr[:] = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32) / 255.0

    return np.clip(ang, 0.0, 1.0), np.clip(pnt, 0.0, 1.0), ink


def load_common_place_station(out_dir, local_view_info, default_district, body_hex, glow_hex, n_frames=36, w=W, h=H):
    """
    Loads a Common Place / City District Station from `shots/out/<shot_id>/` with:
      - Full-screen 1280x720 `angular_cel`, `painted_cel`, and `frames` (combining `film/shot.mp4` multiplane motion
        with the painted Cel + Ink layers so the station is 100% sharp, legible, and alive!)
      - Full-resolution depth map (`depth_sharp.npz`)
    """
    sid = os.path.basename(out_dir)
    sj = os.path.join(out_dir, "shot.json")
    meta = json.load(open(sj)) if os.path.exists(sj) else {}
    bno = meta.get("bible_no")
    vinfo = local_view_info.get(int(bno), {}) if bno is not None else {}

    angular_cel, painted_cel, ink = build_cel_plate_from_dir(out_dir, body_hex, glow_hex, w, h)

    frames = []
    mp4_path = os.path.join(out_dir, "film/shot.mp4")
    if os.path.exists(mp4_path):
        cap = cv2.VideoCapture(mp4_path)
        total = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        idxs = np.linspace(0, total - 1, n_frames).astype(int)
        for i_f, idx in enumerate(idxs):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, fr = cap.read()
            if ok and fr is not None:
                fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
                fr = cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
                # Smoothly progress during station hold from Angular Studio Cel -> Painted Multiplane Cel in motion!
                u_prog = i_f / max(1.0, n_frames - 1.0)
                cel_ref = (1.0 - sm(0.0, 0.45, u_prog)) * angular_cel + sm(0.0, 0.45, u_prog) * painted_cel
                comp = 0.62 * cel_ref + 0.38 * fr
                if ink is not None:
                    ia = ink[..., 3:4] * 0.72
                    comp = comp * (1.0 - ia) + ink[..., :3] * ia
                frames.append(np.clip(comp, 0.0, 1.0).astype(np.float32))
        cap.release()

    if not frames:
        for i_f in range(n_frames):
            u_prog = i_f / max(1.0, n_frames - 1.0)
            zoom = 1.0 + 0.05 * u_prog
            M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), 0.0, zoom)
            cel_ref = (1.0 - sm(0.0, 0.45, u_prog)) * angular_cel + sm(0.0, 0.45, u_prog) * painted_cel
            frames.append(cv2.warpAffine(cel_ref, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE))

    depth_map = None
    for npz_name in ["depth_sharp.npz", "arrays.npz"]:
        p_npz = os.path.join(out_dir, npz_name)
        if os.path.exists(p_npz):
            try:
                d = np.load(p_npz)
                k = "depth" if "depth" in d.files else d.files[0]
                depth_map = cv2.resize(d[k].astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
                break
            except Exception:
                pass
    if depth_map is None:
        lum = painted_cel @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        depth_map = 3.0 + 10.0 * (1.0 - lum)

    d_name = vinfo.get("district_name") or default_district
    p_kind = vinfo.get("place_kind") or f"CITY DISTRICT · {str(d_name).upper()}"
    p_name = vinfo.get("place_name") or (meta.get("prompt") or f"View #{bno}").split(",")[0][:52]
    p_brief = vinfo.get("place_brief") or f"View #{bno} in {d_name}"
    d_body = vinfo.get("district_body") or body_hex
    d_glow = vinfo.get("district_glow") or glow_hex

    d_thresh = np.percentile(depth_map, 32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cent = np.exp(-(((xx / w - 0.5) / 0.38) ** 2 + ((yy / h - 0.52) / 0.42) ** 2))
    fg_mask = ((depth_map <= d_thresh) & (cent > 0.32)).astype(np.float32)
    fg_mask = cv2.GaussianBlur(fg_mask, (0, 0), 2.5)

    return {
        "id": f"V{bno:02d}" if bno is not None else sid[:6],
        "kind_badge": p_kind,
        "name": p_name,
        "what": p_brief,
        "line": f"{p_name} — {p_brief}",
        "district_name": str(d_name),
        "body_hex": d_body,
        "glow_hex": d_glow,
        "frames": np.stack(frames, axis=0),
        "angular_cel": angular_cel,
        "painted_cel": painted_cel,
        "depth": depth_map,
        "fg_mask": fg_mask,
        "fg_rgba": None,
    }


def find_first_keyframe_dir(shot_id):
    for base in [
        os.path.join(CORPUS_ROOT, "shots/video", shot_id, "out"),
        os.path.join(SHOTS_ROOT, "cel_assets/video", shot_id, "out"),
    ]:
        if os.path.isdir(base):
            subs = sorted(glob.glob(os.path.join(base, "vid-*")))
            if subs:
                return subs[len(subs) // 2]
    return None


def load_poem_cel_shot(scion_data, scene_map, default_district, body_hex, glow_hex, n_frames=32, w=W, h=H):
    """
    Loads a Poem Cel Shot (`P<NN>-<MMM>`) at full 1280x720 resolution with 100% legibility:
      - Uses `cel_v2/*.png` + `program/frame0.png` + `cartoon/cel.png` + `cartoon/ink.png`
      - Extracts `fg_rgba` / `fg_mask` so we can render the 4D Spacetime Worm trail BEHIND the foreground subject
        without EVER obscuring the subject or the full-frame painted cel!
    """
    sid = scion_data["id"]
    kf_dir = find_first_keyframe_dir(sid)
    sc_key = scion_data.get("scene") or ""
    sc_info = scene_map.get(sc_key, {})

    here_desc = sc_info.get("here") or scion_data.get("name") or sid
    dist_name = sc_info.get("district") or default_district
    place_tag = sc_info.get("common_place_tag") or f"CITY DISTRICT · {str(dist_name).upper()}"

    angular_cel, painted_cel, ink_rgba = (None, None, None)
    fg_rgba, depth_map, fg_mask = (None, None, None)

    if kf_dir:
        angular_cel, painted_cel, ink_rgba = build_cel_plate_from_dir(kf_dir, body_hex, glow_hex, w, h)
        fg_rgba = load_rgba_resized(os.path.join(kf_dir, "layers/fg.png"), w, h)
        arr_path = os.path.join(kf_dir, "arrays.npz")
        if os.path.exists(arr_path):
            try:
                arr = np.load(arr_path)
                if "depth" in arr:
                    depth_map = cv2.resize(arr["depth"].astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
                if "masks" in arr and len(arr["masks"]) > 0:
                    fg_mask = cv2.resize(arr["masks"][0].astype(np.float32), (w, h), interpolation=cv2.INTER_NEAREST)
            except Exception:
                pass
        if depth_map is None:
            d_jpg = load_rgb_resized(os.path.join(kf_dir, "depth.jpg"), w, h)
            if d_jpg is not None:
                depth_map = 2.0 + 12.0 * (1.0 - d_jpg[..., 0])

    corpus_vdir = os.path.join(CORPUS_ROOT, "shots/video", sid)
    cel_pngs = sorted(glob.glob(os.path.join(corpus_vdir, "cel_v2/*.png")))
    raw_pngs = sorted(glob.glob(os.path.join(corpus_vdir, "frames/*.png")))
    patch_mp4 = os.path.join(SHOTS_ROOT, "cel_assets/patches", f"{sid}.mp4")

    frames = []
    if cel_pngs:
        total = len(cel_pngs)
        idxs = np.linspace(0, total - 1, n_frames).astype(int)
        for i_f, idx in enumerate(idxs):
            cel_im = load_rgb_resized(cel_pngs[idx], w, h)
            raw_im = load_rgb_resized(raw_pngs[min(idx, len(raw_pngs) - 1)], w, h) if raw_pngs else None
            comp = 0.84 * cel_im + 0.16 * raw_im if (cel_im is not None and raw_im is not None) else (cel_im if cel_im is not None else raw_im)
            if comp is not None:
                p2, p98 = np.percentile(comp, 2.0), np.percentile(comp, 98.5)
                comp = np.clip((comp - p2) / max(p98 - p2, 0.16), 0.0, 1.0)
                # Compute per-frame dynamic ink outline locked to the moving cel_v2 frame!
                lum = comp @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
                gy, gx = np.gradient(lum)
                ink_edge = np.clip((np.hypot(gx, gy) - 0.035) * 8.5, 0.0, 0.72)[..., None]
                comp = comp * (1.0 - ink_edge) + 0.05 * ink_edge
                frames.append(comp.astype(np.float32))
    elif os.path.exists(patch_mp4):
        cap = cv2.VideoCapture(patch_mp4)
        total = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        idxs = np.linspace(0, total - 1, n_frames).astype(int)
        for idx in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, fr = cap.read()
            if ok and fr is not None:
                fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
                fr = cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
                if painted_cel is not None:
                    fr = 0.50 * fr + 0.50 * painted_cel
                p2, p98 = np.percentile(fr, 2.0), np.percentile(fr, 98.5)
                fr = np.clip((fr - p2) / max(p98 - p2, 0.16), 0.0, 1.0)
                lum = fr @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
                gy, gx = np.gradient(lum)
                ink_edge = np.clip((np.hypot(gx, gy) - 0.035) * 8.5, 0.0, 0.72)[..., None]
                fr = fr * (1.0 - ink_edge) + 0.05 * ink_edge
                frames.append(fr.astype(np.float32))
        cap.release()

    if not frames:
        base = painted_cel if painted_cel is not None else np.full((h, w, 3), 0.5, dtype=np.float32)
        frames = [base for _ in range(n_frames)]

    if depth_map is None:
        lum = frames[0] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        depth_map = 3.0 + 10.0 * (1.0 - lum)

    if fg_mask is None:
        if fg_rgba is not None:
            fg_mask = (fg_rgba[..., 3] > 0.25).astype(np.float32)
        else:
            # Derive clean foreground figure mask from depth (nearest 28% in central region)
            d_thresh = np.percentile(depth_map, 32)
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            cent = np.exp(-(((xx / w - 0.5) / 0.36) ** 2 + ((yy / h - 0.52) / 0.42) ** 2))
            fg_mask = ((depth_map <= d_thresh) & (cent > 0.35)).astype(np.float32)
            fg_mask = cv2.GaussianBlur(fg_mask, (0, 0), 2.5)

    return {
        "id": sid,
        "kind_badge": place_tag,
        "name": scion_data.get("name") or sid,
        "what": here_desc,
        "line": scion_data.get("line") or here_desc,
        "district_name": str(dist_name),
        "body_hex": body_hex,
        "glow_hex": glow_hex,
        "frames": np.stack(frames, axis=0),
        "angular_cel": angular_cel if angular_cel is not None else frames[0],
        "painted_cel": painted_cel if painted_cel is not None else frames[0],
        "depth": depth_map,
        "fg_mask": fg_mask,
        "fg_rgba": fg_rgba,
    }


def draw_clean_lower_third_hud(img_rgb_float, poem_num, poem_title, district_name, body_hex, glow_hex, badge_str, place_title, verse_line):
    """
    Single, ultra-clean lower-third bar (`y = 664..720`, 56px tall = 92.2% of frame completely unobstructed!)
    showing:
      - Left: Poem + Common Place / City District badge + Place Title
      - Center: Poetic Verse / Place Description in Georgia Italic
      - Right: Measured City District `BODY` + `GLOW` Color Swatches (`_city/districts.json`)
    """
    pil_im = Image.fromarray((np.clip(img_rgb_float, 0.0, 1.0) * 255.0).astype(np.uint8)).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    bar_y0 = H - 58
    d.rectangle([0, bar_y0, W, H], fill=(16, 18, 24, 222))
    d.line([(0, bar_y0), (W, bar_y0)], fill=(235, 195, 120, 180), width=1)

    f_mono = get_font("mono", 13)
    f_bold = get_font("serif_bold", 16)
    f_italic = get_font("serif_italic", 18)

    # Top line of lower third: Badge + Place Name
    top_left = f"P{poem_num:02d} · {poem_title.upper()}  |  {badge_str}"
    d.text((20, bar_y0 + 7), top_left[:88], font=f_mono, fill=(250, 188, 92, 255))

    # Bottom line of lower third: Place title + Italic lyric
    sub_str = f"{place_title}: “{verse_line}”" if place_title else f"“{verse_line}”"
    if len(sub_str) > 108:
        sub_str = sub_str[:106] + "…”"
    d.text((20, bar_y0 + 27), sub_str, font=f_italic, fill=(245, 240, 230, 255))

    # Right side: City District `BODY` + `GLOW` Palette Swatches
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
    d.text((x0, y0 + sw_h + 4), pal_lbl, font=get_font("mono", 11), fill=(215, 210, 198, 230))

    comp = Image.alpha_composite(pil_im, overlay).convert("RGB")
    return np.asarray(comp, dtype=np.uint8)


# ==============================================================================
# MODE 1: S2 CONSTRUCT (Exact Projective Ray-Bundle Math from `seeing-construct.mp4`)
# ==============================================================================

def build_projective_station_cloud(station, theta_k, step=2, R_cam=900.0, relief=420.0):
    """
    Unprojects pixels `(u, v)` along exact camera rays from the station's viewpoint `theta_k`.
    At `theta_cam == theta_k`, every point projects back to its EXACT pixel `(u, v)` across the full
    1280x720 screen regardless of depth `z`!
    As soon as `theta_cam` rotates away from `theta_k`, the depth relief `(d_norm - 0.5) * relief`
    unfolds the image into a 3D point cloud in formless matter!
    """
    depth = station["depth"]
    d_lo, d_hi = np.percentile(depth, 3), np.percentile(depth, 97)
    d_norm = np.clip((depth - d_lo) / max(d_hi - d_lo, 1e-3), 0.0, 1.0)
    # Smooth depth slightly so 3D sheets form cohesive architectural surfaces during orbit
    d_norm = cv2.GaussianBlur(d_norm, (0, 0), 2.0)

    yy, xx = np.mgrid[0:H:step, 0:W:step]
    u_s = xx.ravel().astype(np.float32)
    v_s = yy.ravel().astype(np.float32)
    dn_s = d_norm[0:H:step, 0:W:step].ravel().astype(np.float32)

    F = (H / 2.0) / math.tan(math.radians(50.0) / 2.0)
    z_ray = R_cam + (dn_s - 0.45) * relief

    x_cam = (u_s - W / 2.0) * z_ray / F
    y_cam = (v_s - H / 2.0) * z_ray / F
    z_world_0 = z_ray - R_cam

    R_k = rotmat_y(theta_k)
    P_world = np.stack([x_cam, y_cam, z_world_0], axis=1) @ R_k

    return {
        "P_world": P_world.astype(np.float32),
        "yy": yy,
        "xx": xx,
        "step": step,
        "R_cam": R_cam,
        "F": F,
    }


def render_construct_frame(poem_num, poem_title, district_name, stations, clouds, t, total_dur):
    """
    Renders one frame of `S2 · Common Places & Painted Cels Construct`:
      - 5 canonical stations (`6.0s` each = `30.0s` total)
      - First `4.3s` (`72%`) of each station: Camera is 100% STATIONARY (`theta_cam = theta_k`, ZERO wagging!).
        The station's 1280x720 Painted Cel + Multiplane Animation fills 100% of the screen edge-to-edge,
        while the other stations' 3D point clouds drift subtly at 14% opacity in deep space.
      - Last `1.7s` (`28%`) of each station: Camera rotates smoothly in ONE direction (`theta_k -> theta_{k+1}`)
        through the crisp Painter's-Algorithm 3D point cloud on warm archival paper (`#F2EDE2`).
    """
    n_st = len(stations)
    seg_dur = total_dur / float(n_st)
    seg_idx = min(n_st - 1, int(t / seg_dur))
    u_seg = (t - seg_idx * seg_dur) / seg_dur

    hold_frac = 0.72  # 4.32 seconds of 100% stationary, crystal-clear full-screen lock per station!
    st_curr = stations[seg_idx]
    st_next = stations[(seg_idx + 1) % n_st]

    theta0 = st_curr["theta"]
    theta1 = st_next["theta"]
    if theta1 <= theta0:
        theta1 += 2.0 * math.pi

    if u_seg <= hold_frac:
        # 100% STATIONARY CAMERA — ZERO WAGGING!
        theta_cam = theta0
        u_hold = u_seg / hold_frac
        # Smoothly lock in over first 0.25s and begin releasing in last 0.25s of the 4.3s hold
        lock_alpha = sm(0.0, 0.06, u_hold) * (1.0 - sm(0.92, 1.0, u_hold))
        active_st = st_curr
        active_k = seg_idx
        f_idx = int(u_hold * (len(st_curr["frames"]) - 1))
    else:
        # Smooth, ONE-WAY orbital rotation from theta0 to theta1 (NEVER reverses!)
        u_orbit = smootherstep((u_seg - hold_frac) / (1.0 - hold_frac))
        theta_cam = lerp(theta0, theta1, u_orbit)
        lock_alpha = 0.0
        if u_orbit < 0.5:
            active_st = st_curr
            active_k = seg_idx
            f_idx = len(st_curr["frames"]) - 1
        else:
            active_st = st_next
            active_k = (seg_idx + 1) % n_st
            f_idx = 0

    R_cam = clouds[0]["R_cam"]
    F = clouds[0]["F"]
    R_view = rotmat_y(-theta_cam)

    # Start on warm archival paper subtly tinted by the active station's glow color
    glow_rgb = hex_to_rgb_float((active_st.get("glow_hex") or ["#fa8d15"])[0])
    bg_paper = 0.93 * PAPER_BG + 0.07 * glow_rgb
    canvas = np.broadcast_to(bg_paper, (H, W, 3)).copy()

    # Render 3D point clouds of the stations
    # When locked (`lock_alpha > 0.95`), we only need the ghost clouds of the OTHER stations (`k != active_k`)
    # plus the 100% full-resolution `active_st["frames"][f_idx]` plate!
    if lock_alpha < 0.98:
        C_acc = np.zeros((H, W, 3), dtype=np.float32)
        W_acc = np.zeros((H, W), dtype=np.float32)

        for k, (st, cl) in enumerate(zip(stations, clouds)):
            d_theta = abs((theta_cam - st["theta"] + math.pi) % (2.0 * math.pi) - math.pi)
            if k == active_k:
                w_st = 1.0
            else:
                w_st = 0.55 * math.exp(-0.55 * (d_theta ** 2))
            if w_st < 0.03:
                continue

            fr_k = st["frames"][f_idx % len(st["frames"])] if k == active_k else st["painted_cel"]
            cols = fr_k[cl["yy"], cl["xx"]].reshape(-1, 3)

            Q = cl["P_world"] @ R_view
            Z = Q[:, 2] + R_cam
            ok = Z > 120.0
            if not ok.any():
                continue
            Z = Z[ok]
            sx = (Q[ok, 0] * F / Z + W / 2.0).astype(np.int32)
            sy = (Q[ok, 1] * F / Z + H / 2.0).astype(np.int32)
            cols = cols[ok]

            inb = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
            sx, sy, Z, cols = sx[inb], sy[inb], Z[inb], cols[inb]

            # Crisp 2x2 splat footprint so points are sharp and legible without Gaussian blur mud
            w_pt = w_st * np.exp(-np.maximum(Z - 450.0, 0.0) / 1600.0)
            for dy in (0, 1):
                sy_d = np.minimum(sy + dy, H - 1)
                for dx in (0, 1):
                    sx_d = np.minimum(sx + dx, W - 1)
                    ix = sy_d * W + sx_d
                    W_acc += np.bincount(ix, w_pt, minlength=W * H).reshape(H, W)
                    for ch in range(3):
                        C_acc[..., ch] += np.bincount(ix, w_pt * cols[:, ch], minlength=W * H).reshape(H, W)

        valid = W_acc > 1e-4
        cloud_img = canvas.copy()
        cloud_img[valid] = C_acc[valid] / W_acc[valid, None]
        # Fill tiny 1px pinholes when close to station angle
        wb = cv2.GaussianBlur(W_acc, (0, 0), 1.1)
        cb = cv2.GaussianBlur(C_acc, (0, 0), 1.1)
        hole = (~valid) & (wb > 0.25)
        cloud_img[hole] = cb[hole] / wb[hole, None]

        cov = np.clip(1.0 - np.exp(-wb * 1.8), 0.0, 1.0)[..., None]
        canvas = canvas * (1.0 - cov) + cloud_img * cov

    # Blend in the 100% FULL-SCREEN (1280x720 edge-to-edge) Cel + Multiplane Animation during the stationary hold!
    if lock_alpha > 0.01:
        full_cel_frame = active_st["frames"][f_idx % len(active_st["frames"])]
        canvas = canvas * (1.0 - lock_alpha) + full_cel_frame * lock_alpha

    state_lbl = "CEL STATION LOCK" if lock_alpha > 0.4 else "3D POINT-CLOUD ORBIT"
    badge = f"{active_st['kind_badge']}  [{active_k + 1}/{n_st} · {state_lbl}]"
    return draw_clean_lower_third_hud(
        canvas,
        poem_num=poem_num,
        poem_title=poem_title,
        district_name=active_st["district_name"],
        body_hex=active_st["body_hex"],
        glow_hex=active_st["glow_hex"],
        badge_str=badge,
        place_title=f"{active_st['id']} · {active_st['name']}",
        verse_line=active_st["line"],
    )


# ==============================================================================
# MODE 2: 07w SPACETIME WORM & CITY WALK (Zero Yaw Wagging · 100% Full-Frame Legibility)
# ==============================================================================

def render_spacetime_worm_shot_frame(shot_bundle, u_shot):
    """
    Renders a single shot at normalized progress `u_shot in [0, 1]` with:
      - ZERO yaw wagging! Camera looks straight ahead (`yaw = 0, pitch = 0`) and glides smoothly forward (`+Z`).
      - 100% full-frame (`1280x720`) legibility of the City District Cel background (`painted_cel` / `frames`).
      - Sculpted 4D Spacetime Worm ribbon of the moving subject (`fg_mask` / `fg_rgba`) trailing into deep 3D space
        BEHIND the 100% opaque foreground subject!
    """
    frames = shot_bundle["frames"]
    n_f = len(frames)
    f_now = min(n_f - 1, int(u_shot * n_f))
    present_frame = frames[f_now]

    # 1. Straight-ahead multiplane Z-push on the background Cel (scale 1.00 -> 1.10, ZERO yaw wagging!)
    bg_zoom = 1.0 + 0.10 * ease(u_shot)
    M_bg = cv2.getRotationMatrix2D((W / 2.0, H / 2.0), 0.0, bg_zoom)
    bg_plate = cv2.warpAffine(present_frame, M_bg, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # Subtle vignette toward the City District's `body[0]` deep shadow tone at the outer frame edge
    body_hex = shot_bundle.get("body_hex") or ["#1e1d2c"]
    glow_hex = shot_bundle.get("glow_hex") or ["#01acd4", "#fa8d15"]
    c_shadow = hex_to_rgb_float(body_hex[0])
    c_glow1 = hex_to_rgb_float(glow_hex[0])
    c_glow2 = hex_to_rgb_float(glow_hex[min(1, len(glow_hex) - 1)])

    canvas = bg_plate.copy()

    # 2. Extract the foreground figure mask & contour to extrude the 4D Spacetime Worm BEHIND the figure
    fg_mask = shot_bundle["fg_mask"]
    fg_soft = cv2.GaussianBlur(fg_mask, (0, 0), 3.0)

    # Compute clean contour of foreground subject for subtle spacetime ring echoes
    mask_u8 = (fg_mask > 0.30).astype(np.uint8) * 255
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Render 8 receding temporal slices (`age = 8 .. 1`, back-to-front) BEHIND the present subject
    # Recession vector moves smoothly up-and-back into the Z-corridor (NO oscillation!)
    n_echoes = 8
    for age in range(n_echoes, 0, -1):
        f_past = max(0, f_now - age * 2)
        past_fr = frames[f_past]

        frac = age / float(n_echoes)
        # Recede smoothly into depth: scale down toward vanishing point (W*0.52, H*0.42)
        sc_echo = 1.0 - 0.28 * frac
        tx = (1.0 - sc_echo) * (W * 0.58) - age * 14.0
        ty = (1.0 - sc_echo) * (H * 0.38) - age * 6.5
        M_echo = np.array([[sc_echo, 0.0, tx], [0.0, sc_echo, ty]], dtype=np.float32)

        warped_fr = cv2.warpAffine(past_fr, M_echo, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
        warped_m = cv2.warpAffine(fg_soft, M_echo, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

        # Tint older echoes smoothly with the City District's signature `glow` -> `body` palette
        tint_col = lerp(c_glow1, c_glow2, frac)
        echo_rgb = 0.65 * warped_fr + 0.35 * tint_col[None, None, :]
        echo_alpha = warped_m * (0.48 * (1.0 - 0.65 * frac)) * sm(0.02, 0.18, u_shot)

        canvas = canvas * (1.0 - echo_alpha[..., None]) + echo_rgb * echo_alpha[..., None]

        # Subtle 1px silhouette contour rim around each temporal slice
        if contours:
            rim_layer = (np.clip(canvas, 0.0, 1.0) * 255.0).astype(np.uint8)
            col_u8 = tuple(int(np.clip(x * 255.0, 0, 255)) for x in tint_col)
            for cnt in contours:
                if cv2.contourArea(cnt) > 250:
                    pts = cnt[:, 0, :].astype(np.float32)
                    pts_w = np.column_stack([pts[:, 0] * sc_echo + tx, pts[:, 1] * sc_echo + ty]).astype(np.int32)
                    cv2.polylines(rim_layer, [pts_w.reshape(-1, 1, 2)], True, col_u8, 1, cv2.LINE_AA)
            rim_f = rim_layer.astype(np.float32) / 255.0
            rim_w = 0.45 * (1.0 - 0.5 * frac) * sm(0.02, 0.18, u_shot)
            canvas = canvas * (1.0 - rim_w) + rim_f * rim_w

    # 3. Composite the 100% SHARP, 100% OPAQUE Present Foreground Subject ON TOP of its Spacetime Worm trail!
    fg_zoom = 1.0 + 0.14 * ease(u_shot)
    M_fg = cv2.getRotationMatrix2D((W / 2.0, H / 2.0), 0.0, fg_zoom)
    fg_present_rgb = cv2.warpAffine(present_frame, M_fg, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    fg_present_m = cv2.warpAffine(fg_soft, M_fg, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    canvas = canvas * (1.0 - fg_present_m[..., None]) + fg_present_rgb * fg_present_m[..., None]
    return np.clip(canvas, 0.0, 1.0)


def render_spacetime_worm_frame(poem_num, poem_title, shot_bundles, t, shot_dur=3.2):
    """
    Chains all Poem Cel Shots + Common Places along a straight-ahead Z-corridor with smooth
    forward depth-portal dissolves (`0.55s` overlap) and ZERO yaw wagging!
    """
    n_shots = len(shot_bundles)
    idx = min(n_shots - 1, int(t / shot_dur))
    u = np.clip((t - idx * shot_dur) / shot_dur, 0.0, 1.0)

    curr_b = shot_bundles[idx]
    im_curr = render_spacetime_worm_shot_frame(curr_b, u)

    # Smooth straight-ahead Z-portal dissolve into next shot during final 18% of shot
    xf_start = 0.82
    if u > xf_start and idx + 1 < n_shots:
        u_xf = sm(xf_start, 1.0, u)
        next_b = shot_bundles[idx + 1]
        im_next = render_spacetime_worm_shot_frame(next_b, u_xf * 0.15)
        canvas = im_curr * (1.0 - u_xf) + im_next * u_xf
        active_b = next_b if u_xf > 0.5 else curr_b
        active_idx = idx + 1 if u_xf > 0.5 else idx
    else:
        canvas = im_curr
        active_b = curr_b
        active_idx = idx

    badge = f"07w SPACETIME WORM · {active_b['kind_badge']}  [{active_idx + 1}/{n_shots}: {active_b['id']}]"
    return draw_clean_lower_third_hud(
        canvas,
        poem_num=poem_num,
        poem_title=poem_title,
        district_name=active_b["district_name"],
        body_hex=active_b["body_hex"],
        glow_hex=active_b["glow_hex"],
        badge_str=badge,
        place_title=f"{active_b['name']} ({active_b['what'][:44]})",
        verse_line=active_b["line"],
    )


def encode_video_with_real_audio(frames_rgb, out_mp4, audio_t0):
    os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
    tmp_v = out_mp4 + ".video.mp4"
    vid_dur = len(frames_rgb) / float(FPS)

    cmd_v = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        tmp_v,
    ]
    proc = subprocess.Popen(cmd_v, stdin=subprocess.PIPE)
    for fr in frames_rgb:
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    proc.wait()

    if os.path.exists(MASTER_AUDIO):
        cmd_mux = [
            "ffmpeg", "-y", "-v", "error",
            "-i", tmp_v,
            "-ss", f"{audio_t0:.3f}", "-t", f"{vid_dur:.3f}", "-i", MASTER_AUDIO,
            "-map", "0:v:0", "-map", "1:a:0",
            "-af", f"afade=t=in:st=0:d=0.5,afade=t=out:st={max(0.1, vid_dur - 0.7):.2f}:d=0.7",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest", out_mp4,
        ]
        subprocess.run(cmd_mux, check=True)
        os.remove(tmp_v)
    else:
        os.replace(tmp_v, out_mp4)


def collect_poem_places_cels_and_palettes(poem_num, city_data, districts_by_id, bible_to_dir, id_to_dir, hero_poems):
    scion_paths = sorted(glob.glob(os.path.join(SHOTS_ROOT, f"cel_assets/scion/P{poem_num:02d}-*.json")))
    scion_list = [json.load(open(p)) for p in scion_paths]
    scion_list.sort(key=lambda x: float(x.get("t0", 0.0)))

    dossier_path = os.path.join(SHOTS_ROOT, f"poems/dossier/{poem_num:02d}.json")
    dossier = json.load(open(dossier_path)) if os.path.exists(dossier_path) else {}

    atlas_path = os.path.join(SHOTS_ROOT, f"poems/atlas/{poem_num:02d}.json")
    atlas = json.load(open(atlas_path)) if os.path.exists(atlas_path) else {}

    # Find matching poem entry in `_city/districts.json`
    city_poem = next((p for p in city_data.get("poems", []) if int(p["num"]) == poem_num), {})
    dist_id = city_poem.get("district") or (atlas.get("districts", [{}])[0].get("id") if atlas.get("districts") else "naraka")
    city_dist = districts_by_id.get(dist_id, {})

    poem_title = dossier.get("title") or atlas.get("title") or city_poem.get("title") or f"Poem {poem_num:02d}"
    district_name = city_dist.get("name") or dossier.get("district") or "Naraka Market"
    body_hex = city_dist.get("body") or (dossier.get("palette") or ["#262423", "#2d4651", "#337993"])[:5]
    glow_hex = city_dist.get("glow") or (dossier.get("palette") or ["#64b4ce", "#01acd4", "#fa8d15"])[-4:]

    # Build poem-local view_info so this poem's Common Places (`heroes`) & District Places take priority
    local_view_info = {}
    for cd_entry in city_data.get("districts", []):
        cd_name = cd_entry.get("name", "City District")
        cd_body = cd_entry.get("body", body_hex)
        cd_glow = cd_entry.get("glow", glow_hex)
        cd_keys = cd_entry.get("key", [])
        cd_mood = cd_entry.get("mood", "")
        for img_no in cd_entry.get("images", []):
            vn = int(img_no)
            # Match key string if number appears in it
            matched_k = next((k for k in cd_keys if str(vn) in k), cd_keys[0] if cd_keys else cd_name)
            local_view_info[vn] = {
                "is_common_hero": False,
                "place_kind": f"CITY DISTRICT · {cd_name.upper()}",
                "place_name": matched_k.split("(")[0].strip().title(),
                "place_brief": cd_mood,
                "district_name": cd_name,
                "district_body": cd_body,
                "district_glow": cd_glow,
            }

    for dist in atlas.get("districts", []):
        did = dist.get("id", dist_id)
        cd = districts_by_id.get(did, city_dist)
        dname = cd.get("name") or dist.get("name", district_name)
        dbody = cd.get("body") or dist.get("body") or body_hex
        dglow = cd.get("glow") or glow_hex
        for pl in dist.get("places", []):
            for v in pl.get("views", []):
                vn = int(v["n"])
                local_view_info[vn] = {
                    "is_common_hero": False,
                    "place_kind": f"CITY DISTRICT · {dname.upper()}",
                    "place_name": pl.get("name", f"View #{vn}"),
                    "place_brief": pl.get("what", ""),
                    "district_name": dname,
                    "district_body": dbody,
                    "district_glow": dglow,
                }

    for h in atlas.get("heroes", []):
        hid = h["id"]
        shared = hero_poems.get(hid, [f"P{poem_num:02d}"])
        shared_str = "·".join(shared)
        for v in h.get("views", []):
            vn = int(v["n"])
            prev = local_view_info.get(vn, {})
            local_view_info[vn] = {
                "is_common_hero": True,
                "place_kind": f"COMMON PLACE ({shared_str})" if len(shared) > 1 else f"HERO PLACE ({shared_str})",
                "place_name": h.get("name", hid),
                "place_brief": h.get("brief", ""),
                "district_name": prev.get("district_name", district_name),
                "district_body": prev.get("district_body", body_hex),
                "district_glow": prev.get("district_glow", glow_hex),
            }

    # Map scene keys (`01.0`, etc.) to their Common Place & City District
    scene_map = {}
    heroes = atlas.get("heroes", [])
    hero_summary = ""
    if heroes:
        h0 = heroes[0]
        sh_str = "·".join(hero_poems.get(h0["id"], [f"P{poem_num:02d}"]))
        hero_summary = f"COMMON PLACE ({sh_str}): {h0.get('name', '').upper()}"

    for sc in atlas.get("scenes", []):
        skey = sc.get("key")
        if skey:
            cp_tag = hero_summary
            for v in sc.get("views", []):
                vi = local_view_info.get(int(v["n"]), {})
                if vi.get("is_common_hero"):
                    cp_tag = f"{vi['place_kind']}: {vi['place_name'].upper()}"
                    break
                elif vi.get("place_name"):
                    cp_tag = f"{vi['place_kind']}: {vi['place_name'].upper()}"
            scene_map[skey] = {
                "here": sc.get("here", ""),
                "district": sc.get("district", district_name),
                "common_place_tag": cp_tag or f"CITY DISTRICT · {district_name.upper()}",
            }

    # Gather ordered Common Place & City District `shots/out/` directories for this poem:
    # 1. `atlas['heroes']` (The Common Places shared across the city!)
    # 2. `atlas['districts'][i]['places']` (Named District Places)
    # 3. `_city/districts.json` canonical `poems[i]['images']`
    # 4. `dossier['best_footage']`
    ordered_out_dirs = []
    seen_dirs = set()

    for h in atlas.get("heroes", []):
        for v in h.get("views", []):
            od = bible_to_dir.get(int(v["n"]))
            if od and od not in seen_dirs:
                ordered_out_dirs.append(od)
                seen_dirs.add(od)

    for dist in atlas.get("districts", []):
        for pl in dist.get("places", []):
            for v in pl.get("views", []):
                od = bible_to_dir.get(int(v["n"]))
                if od and od not in seen_dirs:
                    ordered_out_dirs.append(od)
                    seen_dirs.add(od)

    for img_no in city_poem.get("images", []):
        od = bible_to_dir.get(int(img_no))
        if od and od not in seen_dirs:
            ordered_out_dirs.append(od)
            seen_dirs.add(od)

    for bf in dossier.get("best_footage", []):
        sid = bf.get("still")
        od = id_to_dir.get(sid)
        if od and od not in seen_dirs:
            ordered_out_dirs.append(od)
            seen_dirs.add(od)

    return poem_title, district_name, body_hex, glow_hex, scion_list, scene_map, ordered_out_dirs, local_view_info


def build_single_poem_pair(poem_num):
    city_data, districts_by_id, bible_to_dir, id_to_dir, hero_poems = build_city_master_index()
    poem_title, district_name, body_hex, glow_hex, scion_list, scene_map, ordered_out_dirs, local_view_info = collect_poem_places_cels_and_palettes(
        poem_num, city_data, districts_by_id, bible_to_dir, id_to_dir, hero_poems
    )
    audio_t0 = float(scion_list[0]["t0"]) if scion_list else (poem_num - 1) * 90.0

    # Load Common Place stations from `shots/out/` (top 3) + key Poem Cel stations (2) = 5 canonical stations for `S2 Construct`
    terr_stations = [
        load_common_place_station(od, local_view_info, district_name, body_hex, glow_hex, n_frames=36)
        for od in ordered_out_dirs[:4]
    ]
    poem_bundles = [
        load_poem_cel_shot(sc, scene_map, district_name, body_hex, glow_hex, n_frames=32)
        for sc in scion_list
    ]

    # Build 5 canonical stations for `S2 Construct` (3 Common Place Territory Cels + 2 Hero Poem Cels)
    construct_stations = []
    if len(terr_stations) >= 3 and len(poem_bundles) >= 2:
        construct_stations = [
            terr_stations[0],
            poem_bundles[0],
            terr_stations[1],
            poem_bundles[len(poem_bundles) // 2],
            terr_stations[2],
        ]
    else:
        construct_stations = (terr_stations + poem_bundles)[:5]

    n_st = len(construct_stations)
    clouds = []
    for k, st in enumerate(construct_stations):
        theta_k = (2.0 * math.pi * k) / float(n_st)
        st["theta"] = theta_k
        clouds.append(build_projective_station_cloud(st, theta_k, step=2))

    # 1. Render `S2 Construct` (`30.0s` = `6.0s` per station: `4.3s` 100% stationary full-frame lock + `1.7s` one-way 3D orbit)
    construct_dur = 30.0
    n_frames_c = int(construct_dur * FPS)
    c_frames = []
    for f_i in range(n_frames_c):
        t = f_i / float(FPS)
        c_frames.append(render_construct_frame(poem_num, poem_title, district_name, construct_stations, clouds, t, construct_dur))

    out_construct = os.path.join(OUT_DIR, f"poem_{poem_num:02d}_construct.mp4")
    encode_video_with_real_audio(c_frames, out_construct, audio_t0)

    # Also copy to `shots/videos/poems/poem_<NN>_construct.mp4` so legacy URLs never serve old files!
    os.makedirs(POEMS_VID_DIR, exist_ok=True)
    shutil.copy2(out_construct, os.path.join(POEMS_VID_DIR, f"poem_{poem_num:02d}_construct.mp4"))
    Image.fromarray(c_frames[int(1.8 * FPS)]).save(os.path.join(POEMS_VID_DIR, f"poem_{poem_num:02d}_construct.jpg"), quality=92)

    # 2. Render `07w Spacetime Worm & City Walk` (interleaving Common Place Cels with Poem Cel Shots, straight-ahead Z-corridor, ZERO wagging!)
    worm_sequence = []
    t_idx = 0
    for i, pb in enumerate(poem_bundles):
        if i % 4 == 0 and t_idx < len(terr_stations):
            worm_sequence.append(terr_stations[t_idx])
            t_idx += 1
        worm_sequence.append(pb)

    shot_dur = 3.0
    worm_dur = len(worm_sequence) * shot_dur
    n_frames_w = int(worm_dur * FPS)
    w_frames = []
    for f_i in range(n_frames_w):
        t = f_i / float(FPS)
        w_frames.append(render_spacetime_worm_frame(poem_num, poem_title, worm_sequence, t, shot_dur=shot_dur))

    out_worm = os.path.join(OUT_DIR, f"poem_{poem_num:02d}_spacetime_worm.mp4")
    encode_video_with_real_audio(w_frames, out_worm, audio_t0)

    shutil.copy2(out_worm, os.path.join(POEMS_VID_DIR, f"poem_{poem_num:02d}_spacetime_worm.mp4"))
    Image.fromarray(w_frames[int(4.5 * FPS)]).save(os.path.join(POEMS_VID_DIR, f"poem_{poem_num:02d}_spacetime_worm.jpg"), quality=92)

    seg_frames = int((construct_dur / float(n_st)) * FPS)
    f_locked = c_frames[int(seg_frames * 0.35)]
    f_orbit = c_frames[int(seg_frames * 0.86)]

    return {
        "poem_num": poem_num,
        "poem_title": poem_title,
        "district_name": district_name,
        "n_construct_stations": n_st,
        "n_worm_shots": len(worm_sequence),
        "construct_mp4": out_construct,
        "worm_mp4": out_worm,
        "sample_construct_locked": f_locked,
        "sample_construct_orbit": f_orbit,
        "sample_worm_frame": w_frames[int(min(len(w_frames) - 1, 4.5 * FPS))],
    }


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(POEMS_VID_DIR, exist_ok=True)
    if len(sys.argv) > 1:
        poems_to_run = [int(x) for x in sys.argv[1:]]
    else:
        poems_to_run = list(range(1, 15))

    print(f"Building Legible Full-Frame Common-Places + Cels + City-Colors Films for Poems: {poems_to_run}")
    results = []
    if len(poems_to_run) == 1:
        res = build_single_poem_pair(poems_to_run[0])
        results.append(res)
        print(f"Done Poem {res['poem_num']:02d}: Construct={res['construct_mp4']} ({res['n_construct_stations']} st) | Worm={res['worm_mp4']} ({res['n_worm_shots']} shots)")
    else:
        with ProcessPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(build_single_poem_pair, p): p for p in poems_to_run}
            for fut in as_completed(futs):
                res = fut.result()
                results.append(res)
                print(f"Done Poem {res['poem_num']:02d} ({res['poem_title']} · {res['district_name']}): Construct ({res['n_construct_stations']} st) & Worm ({res['n_worm_shots']} shots)", flush=True)

    results.sort(key=lambda r: r["poem_num"])

    if len(results) == 14:
        cols, rows = 4, 4
        tw, th = 640, 220
        sheet_c = Image.new("RGB", (cols * tw, rows * th), (242, 237, 226))
        sheet_w = Image.new("RGB", (cols * 480, rows * 270), (16, 18, 24))
        for i, r in enumerate(results):
            cx, cy = (i % cols) * tw, (i // cols) * th
            im_lock = Image.fromarray(r["sample_construct_locked"]).resize((tw // 2, th), Image.Resampling.LANCZOS)
            im_orb = Image.fromarray(r["sample_construct_orbit"]).resize((tw // 2, th), Image.Resampling.LANCZOS)
            sheet_c.paste(im_lock, (cx, cy))
            sheet_c.paste(im_orb, (cx + tw // 2, cy))

            wx, wy = (i % cols) * 480, (i // cols) * 270
            im_w = Image.fromarray(r["sample_worm_frame"]).resize((480, 270), Image.Resampling.LANCZOS)
            sheet_w.paste(im_w, (wx, wy))

        c_sheet_path = os.path.join(OUT_DIR, "all_14_poems_territory_construct_sheet.png")
        w_sheet_path = os.path.join(OUT_DIR, "all_14_poems_spacetime_worms_sheet.png")
        sheet_c.save(c_sheet_path)
        sheet_w.save(w_sheet_path)
        sheet_c.save(os.path.join(ARTIFACT_DIR, "all_14_poems_territory_construct_sheet.png"))
        sheet_w.save(os.path.join(ARTIFACT_DIR, "all_14_poems_spacetime_worms_sheet.png"))

        # Update master suite files in `shots/videos/` and `ARTIFACT_DIR` so NO old blurry/wagging videos remain anywhere!
        shutil.copy2(results[0]["construct_mp4"], os.path.join(VIDEOS_DIR, "wygwyl_14poems_construct_suite.mp4"))
        shutil.copy2(results[0]["construct_mp4"], os.path.join(VIDEOS_DIR, "wygwyl_seeing_construct.mp4"))
        shutil.copy2(results[0]["construct_mp4"], os.path.join(ARTIFACT_DIR, "wygwyl_seeing_construct.mp4"))
        shutil.copy2(results[0]["worm_mp4"], os.path.join(VIDEOS_DIR, "wygwyl_14poems_spacetime_worms_suite.mp4"))
        shutil.copy2(results[0]["worm_mp4"], os.path.join(VIDEOS_DIR, "wygwyl_07_spacetime.mp4"))
        shutil.copy2(results[0]["worm_mp4"], os.path.join(ARTIFACT_DIR, "wygwyl_07_spacetime.mp4"))
        print("Saved contact sheets and updated all master suite MP4s:", c_sheet_path, w_sheet_path)
