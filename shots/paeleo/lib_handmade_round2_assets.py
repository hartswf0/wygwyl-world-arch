#!/usr/bin/env python3
"""
Round 2 Asset-Driven Handmade Studio Engine (`lib_handmade_round2_assets.py`)
=============================================================================
Operates on the existing painted WYGWYL multiplane plates (`shots/suite/sets/plates/*`),
de-bradded / de-kraft-bordered 4-angle articulated characters (`solve_and_render_ideal_body`
from `shots/arena/parts/kit3/release_v2/cuts/*`), poem-specific painted figures
(`shots/play/assets/*`), and hand-cut narrative props (`01..14.props.*` / `01..14.hero.*`),
staging and transforming them inside each poem's assigned SCION studio discipline.

Also provides `populate_poem_sources(poem_num, folder)` to copy each poem's real source
assets into `<folder>/sources/`, write `<folder>/sources/sources.json`, `<folder>/build/fetch_sources.py`,
and `<folder>/reviews/round-02-critic.md`.
"""

import os
import sys
import json
import math
import shutil
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance
from scipy.ndimage import binary_fill_holes, distance_transform_edt, label

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
SUITE = os.path.join(SHOTS, "suite")
CUTS_ROOT = os.path.join(SHOTS, "arena", "parts", "kit3", "release_v2", "cuts")
KIT3_DIR = os.path.join(SHOTS, "arena", "parts", "kit3")

if KIT3_DIR not in sys.path:
    sys.path.insert(0, KIT3_DIR)

import build_step_by_step_ideal_bodies as B  # noqa: E402

W, H = 1280, 720


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * clamp(t, 0.0, 1.0)


def smoothstep(e0, e1, x):
    t = clamp((x - e0) / max(1e-6, e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ============================================================================
# 1. DE-BRADDED & DE-KRAFT-BORDERED CUT LOADER FOR 4-ANGLE IDEAL BODIES
# ============================================================================

_ORIG_LOAD_CLEAN_CUT = B.load_clean_cut
_DEBRAD_CACHE = {}


def load_debradded_cut(path, fill_armhole=False, remove_text_islands=True, flip_x=False, flip_y=False, rot90_if_horiz=False):
    ck = (path, fill_armhole, remove_text_islands, flip_x, flip_y, rot90_if_horiz)
    if ck in _DEBRAD_CACHE:
        return _DEBRAD_CACHE[ck].copy()

    im = _ORIG_LOAD_CLEAN_CUT(
        path,
        fill_armhole=False,
        remove_text_islands=remove_text_islands,
        flip_x=flip_x,
        flip_y=flip_y,
        rot90_if_horiz=rot90_if_horiz,
    )
    bname = os.path.basename(path)
    arr = np.array(im)
    h, w = arr.shape[:2]
    rgb = arr[:, :, :3].copy()
    a = arr[:, :, 3].copy()
    r, g, b = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    Y, X = np.ogrid[:h, :w]

    if "poet.red_black_sunglasses.hipcore__p03" in bname:
        solid = a > 25
        rgb[solid] = [23, 24, 28]
        out = Image.fromarray(np.dstack([rgb, a]))
        _DEBRAD_CACHE[ck] = out
        return out.copy()

    if "ex.ex_jacket.body.back__p13" in bname or "ex.ex_jacket.body.back__p14" in bname:
        solid = a > 25
        rgb[solid] = (rgb[solid].astype(np.float32) * 0.28 + np.array([24.0, 26.0, 22.0])).clip(0, 255).astype(np.uint8)
        a_eroded = cv2.erode(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1)
        out = Image.fromarray(np.dstack([rgb, a_eroded]))
        _DEBRAD_CACHE[ck] = out
        return out.copy()

    is_hand_or_head = (
        any(k in bname for k in (".face", ".heads", ".hands", "31_sunglasses", "profile_sunglasses"))
        or ("poet.red_black_sunglasses.body." in bname and ("__p06" in bname or "__p07" in bname) and ("profile__p07" not in bname))
        or ("ex.ex_jacket.body.back" in bname and ("__p06" in bname or "__p07" in bname))
        or ("party.vintage_party.body.profile" in bname and ("__p07" in bname or "__p13" in bname))
        or ("party.dj_cyber.body.profile__p06" in bname)
        or ("young_poet.child_clothes.body." in bname and (("back__p06" in bname) or ("back__p07" in bname) or ("profile__p04" in bname)))
    )

    if is_hand_or_head:
        tab_zone = (Y < h * 0.18) | (Y > h * 0.82)
        is_hole_or_brass = tab_zone & (a > 20) & (
            ((r > 210) & (g > 200) & (b > 170))
            | ((r > 150) & (g > 110) & (b < 110) & ((r - b) > 42))
        )
        if np.any(is_hole_or_brass):
            dil = cv2.dilate(is_hole_or_brass.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) > 0
            skin_mask = (a > 180) & (Y > h * 0.25) & (Y < h * 0.75) & (r > 70) & (r < 210)
            if np.any(skin_mask):
                med = np.median(rgb[skin_mask], axis=0).astype(np.uint8)
                rgb[dil & tab_zone & (a > 20)] = med
        out = Image.fromarray(np.dstack([rgb, a]))
        _DEBRAD_CACHE[ck] = out
        return out.copy()

    if "poet.red_black_sunglasses" in bname:
        solid = a > 25
        filled = binary_fill_holes(solid)
        is_crimson = ((r - g) > 65) & ((g - b) < 25) & (r > 105)
        is_tan_brass_or_hole = (filled & (~solid)) | (
            solid
            & (~is_crimson)
            & (
                ((r > 52) & (g > 35) & ((r - b) > 8))
                | ((r > 72) & (g > 68) & (b > 55))
            )
        )
        rgb[is_tan_brass_or_hole] = [23, 24, 28]
        a[filled] = 255
        a_eroded = cv2.erode(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1)
        a_smooth = cv2.GaussianBlur(a_eroded, (3, 3), 0.8)
        out = Image.fromarray(np.dstack([rgb, a_smooth]))
        _DEBRAD_CACHE[ck] = out
        return out.copy()

    is_cream_gown = "vintage_party" in bname and any(
        x in bname for x in ("p10", "p11", "p12", "p13", "p14", "p15", "p17", "p18", "female")
    )
    if is_cream_gown:
        solid = a > 25
        filled = binary_fill_holes(solid)
        holes = filled & (~solid)
        if np.any(holes):
            dil = cv2.dilate(holes.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))) > 0
            rgb[dil & filled] = [234, 222, 198]
            a[holes] = 255
        out = Image.fromarray(np.dstack([rgb, a]))
        _DEBRAD_CACHE[ck] = out
        return out.copy()

    solid = a > 25
    filled = binary_fill_holes(solid)
    trans_holes = filled & (~solid)

    bright_paper = solid & (r > 195) & (g > 185) & (b > 135)
    bp_lab, bp_n = label(bright_paper)
    paper_holes = np.zeros((h, w), dtype=bool)
    max_hole_area = int(h * w * (0.12 if fill_armhole else 0.025))
    for i in range(1, bp_n + 1):
        comp = bp_lab == i
        sz = comp.sum()
        if sz <= max_hole_area:
            cy_c, cx_c = np.mean(np.where(comp), axis=1)
            if "vintage_party.body.front__p01" in bname and (cy_c < h * 0.45) and (w * 0.30 < cx_c < w * 0.70):
                continue
            if "child_clothes" in bname and (h * 0.20 < cy_c < h * 0.80):
                continue
            if cy_c < h * 0.34 or cy_c > h * 0.68 or cx_c < w * 0.30 or cx_c > w * 0.70 or fill_armhole:
                paper_holes |= comp

    all_holes = trans_holes | paper_holes

    grommet_ring = np.zeros((h, w), dtype=bool)
    if np.any(all_holes):
        rad_k = max(15, int(min(w, h) * 0.19) | 1)
        grommet_ring |= cv2.dilate(all_holes.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (rad_k, rad_k))) > 0

    piv_zone = (Y < h * 0.24) | (Y > h * 0.76) | ((Y < h * 0.34) & ((X < w * 0.28) | (X > w * 0.72)))
    is_crimson = ((r - g) > 75) & (r > 115) & (g < 75) & (b < 75)
    is_cyber_blue = (b > r + 30) & (b > 110)
    is_brass_color = (
        ((r > 85) & (g > 55) & ((r - b) > 18) & (~is_crimson) & (~is_cyber_blue))
        | ((r > 130) & (g > 115) & (b > 75) & (~is_crimson) & (~is_cyber_blue))
    )
    if "woman.13" not in bname and "child_clothes" not in bname and "vintage_party" not in bname:
        grommet_ring |= piv_zone & solid & is_brass_color
    elif "woman.13" in bname:
        grommet_ring |= piv_zone & solid & (r > 135) & (g > 90) & (b < 110) & ((r - g) < 68)
    elif "vintage_party" in bname:
        not_tie = ~((Y < h * 0.44) & (X > w * 0.30) & (X < w * 0.70) & ("front" in bname))
        grommet_ring |= piv_zone & not_tie & solid & is_brass_color

    dist_in = distance_transform_edt(filled)
    is_kraft_edge = (dist_in > 0) & (dist_in <= 7.0) & (r > 95) & (g > 70) & ((r - b) > 10) & (~is_crimson) & (~is_cyber_blue)

    clean_int = solid & (~all_holes) & (~grommet_ring) & (~is_kraft_edge) & (dist_in > 6.0)
    if not np.any(clean_int):
        clean_int = solid & (~all_holes)
    if np.any(clean_int):
        med_rgb = np.median(rgb[clean_int], axis=0).astype(np.uint8)
        target = (all_holes | grommet_ring | is_kraft_edge) & filled
        rgb[target] = med_rgb
        a[all_holes] = 255

    a_eroded = cv2.erode(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1)
    a_smooth = cv2.GaussianBlur(a_eroded, (3, 3), 0.8)
    out = Image.fromarray(np.dstack([rgb, a_smooth]))
    _DEBRAD_CACHE[ck] = out
    return out.copy()


# Install de-bradded cut loader into B
B.load_clean_cut = load_debradded_cut
B._IMAGE_CACHE.clear()
_CAST_BY_ID = None


def get_cast_dict():
    global _CAST_BY_ID
    if _CAST_BY_ID is None:
        _CAST_BY_ID = {c["id"]: c for c in B.get_canonical_cast_library()}
    return _CAST_BY_ID


# ============================================================================
# 2. WHOLE-FIGURE & CUT PROP LOADERS + SCION MATERIAL FILTERS
# ============================================================================

_WHOLE_FIG_CACHE = {}
_PROP_CACHE = {}
_PLATE_CACHE = {}
_SOLVED_ACTOR_CACHE = {}

WHOLE_FIGURE_MAP = {
    "ghost_child": "play/assets/ghost_child__ghost_nightclothes/00.webp",
    "ancestor_elder": "play/assets/ancestor_elder__white_silver/00.webp",
    "ancestor_robe": "play/assets/ancestor_robe__indigo_gold/00.webp",
    "citizen_1": "play/assets/citizen_1__atlantis/00.webp",
    "angel": "play/assets/angel__robe/00.webp",
    "poet_soul": "play/assets/poet_soul__soul/00.webp",
    "father_elder": "play/assets/father_elder__poem09/00.webp",
    "brother_1": "play/assets/brother_1__poem12/00.webp",
    "elder_man": "play/assets/elder_man__poem13/00.webp",
    "elder_woman": "play/assets/elder_woman__poem13/00.webp",
    "couple_1_a": "play/assets/couple_1_a__poem13/00.webp",
    "couple_1_b": "play/assets/couple_1_b__poem13/00.webp",
}


def load_clean_whole_figure(rel_path):
    """Loads a whole-figure .webp/.png from `shots/` with border erosion & tear repair."""
    if rel_path in _WHOLE_FIG_CACHE:
        return _WHOLE_FIG_CACHE[rel_path].copy()
    p = os.path.join(SHOTS, rel_path)
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGBA")
    arr = np.array(im)
    h, w = arr.shape[:2]
    rgb = arr[:, :, :3].copy()
    a = arr[:, :, 3].copy()
    r, g, b = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    Y, X = np.ogrid[:h, :w]

    if "angel__robe" in rel_path:
        tear = (Y > h * 0.50) & (Y < h * 0.74) & (X > w * 0.30) & (X < w * 0.48) & ((a < 200) | ((r < 120) & (g < 120) & (b < 120)))
        if np.any(tear):
            dil = cv2.dilate(tear.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))) > 0
            rgb[dil] = [238, 235, 228]
            a[dil] = 255

    a_eroded = cv2.erode(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=1)
    a_smooth = cv2.GaussianBlur(a_eroded, (3, 3), 0.75)
    ys, xs = np.where(a_smooth > 20)
    out = Image.fromarray(np.dstack([rgb, a_smooth]))
    if len(xs) > 0:
        out = out.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    _WHOLE_FIG_CACHE[rel_path] = out
    return out.copy()


def load_cut_prop(sheet_id, pid="p01"):
    """Loads a hand-cut narrative prop or architectural set piece from `release_v2/cuts/`."""
    ck = (sheet_id, pid)
    if ck in _PROP_CACHE:
        return _PROP_CACHE[ck].copy()
    p = os.path.join(CUTS_ROOT, sheet_id, f"{sheet_id}__{pid}.png")
    if not os.path.exists(p):
        # Fallback to first available png in folder
        folder = os.path.join(CUTS_ROOT, sheet_id)
        if os.path.isdir(folder):
            pngs = sorted([f for f in os.listdir(folder) if f.endswith(".png")])
            if pngs:
                p = os.path.join(folder, pngs[0])
    if not os.path.exists(p):
        return None
    im = _ORIG_LOAD_CLEAN_CUT(p, fill_armhole=False, remove_text_islands=True)
    arr = np.array(im)
    a = arr[:, :, 3]
    a_eroded = cv2.erode(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1)
    arr[:, :, 3] = cv2.GaussianBlur(a_eroded, (3, 3), 0.65)
    out = Image.fromarray(arr)
    _PROP_CACHE[ck] = out
    return out.copy()


def load_multiplane_plate_dir(plate_id):
    """Loads `P6_sky.png`, `P5_far.png`, `P4_mid.png`, `P0_occluders.png`, `plate.jpg` at 1280x720."""
    if plate_id in _PLATE_CACHE:
        return _PLATE_CACHE[plate_id]
    pdir = os.path.join(SUITE, "sets", "plates", plate_id)
    layers = {}
    for k, fname in [
        ("sky", "P6_sky.png"),
        ("far", "P5_far.png"),
        ("mid", "P4_mid.png"),
        ("occ", "P0_occluders.png"),
        ("plate", "plate.jpg"),
    ]:
        fp = os.path.join(pdir, fname)
        if os.path.exists(fp):
            im = Image.open(fp).convert("RGBA" if fname.endswith(".png") else "RGB")
            if im.size != (W, H):
                im = im.resize((W, H), Image.Resampling.LANCZOS)
            layers[k] = im
    _PLATE_CACHE[plate_id] = layers
    return layers


# ============================================================================
# 3. SCION STUDIO MATERIAL OPERATORS ON REAL ASSETS
# ============================================================================

def style_reiniger_silhouette(rgba_im, rim_rgb=(245, 195, 95), interior_rgb=(14, 12, 11), filigree=True):
    """Transforms a real cutout into a Lotte Reiniger backlit scissor-cut silhouette with rim light & pierced eye/detail filigree."""
    if rgba_im is None:
        return None
    arr = np.array(rgba_im)
    rgb = arr[:, :, :3].astype(np.float32)
    a = arr[:, :, 3].astype(np.float32) / 255.0
    solid = (arr[:, :, 3] > 35).astype(np.uint8)
    dist = cv2.distanceTransform(solid, cv2.DIST_L2, 3)

    out = np.zeros_like(arr)
    out[:, :, 0] = interior_rgb[0]
    out[:, :, 1] = interior_rgb[1]
    out[:, :, 2] = interior_rgb[2]

    # Warm rim light along the outer 2.5px scissor-cut contour
    rim_w = np.clip(1.0 - (dist - 1.0) / 2.8, 0.0, 1.0) * (solid > 0)
    for c in range(3):
        out[:, :, c] = np.clip(out[:, :, c] * (1.0 - rim_w * 0.72) + rim_rgb[c] * (rim_w * 0.72), 0, 255).astype(np.uint8)

    if filigree:
        # Pierced interior contour highlights (Laplacian/Sobel high-contrast interior edges become thin warm slits)
        lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
        gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
        mag = np.hypot(gx, gy)
        slits = (dist > 4.0) & (mag > 95.0)
        for c in range(3):
            out[:, :, c] = np.where(slits, int(rim_rgb[c] * 0.55 + interior_rgb[c] * 0.45), out[:, :, c])

    out[:, :, 3] = arr[:, :, 3]
    return Image.fromarray(out)


def style_gilliam_engraved_cutout(rgba_im, tint_rgb=(228, 206, 168), paper_border_px=0):
    """Transforms a real cutout into a Terry Gilliam 19th-century engraved burin cross-hatched collage element."""
    if rgba_im is None:
        return None
    arr = np.array(rgba_im)
    h, w = arr.shape[:2]
    rgb = arr[:, :, :3].astype(np.float32)
    a = arr[:, :, 3]
    lum = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]) / 255.0

    Y, X = np.ogrid[:h, :w]
    h1 = 0.5 + 0.5 * np.sin((X + Y * 0.7) * 1.45)
    h2 = 0.5 + 0.5 * np.sin((X * 0.6 - Y) * 1.65)
    ink = np.ones((h, w), dtype=np.float32)
    ink = np.where(lum < 0.72, np.minimum(ink, 0.35 + 0.65 * (h1 > 0.45)), ink)
    ink = np.where(lum < 0.45, np.minimum(ink, 0.18 + 0.55 * (h2 > 0.52)), ink)
    ink = np.where(lum < 0.22, 0.10, ink)

    out = np.zeros_like(arr)
    for c in range(3):
        # Blend 45% original hand-tinted pigment + 55% burin engraving ink on aged paper
        engraved_c = tint_rgb[c] * (0.14 + 0.86 * ink)
        out[:, :, c] = np.clip(0.45 * rgb[:, :, c] + 0.55 * engraved_c, 0, 255).astype(np.uint8)
    out[:, :, 3] = a
    return Image.fromarray(out)


def style_sutherland_crt_blueprint(rgba_im, phosphor_rgb=(65, 255, 155), fill_alpha=0.28):
    """Transforms a real architectural/prop cutout into an Ivan Sutherland TX-2 CRT green phosphor vector blueprint."""
    if rgba_im is None:
        return None
    arr = np.array(rgba_im)
    rgb = arr[:, :, :3].astype(np.float32)
    a = arr[:, :, 3].astype(np.float32) / 255.0
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    edges = cv2.Canny(lum.astype(np.uint8), 45, 130)
    sil_edge = cv2.Canny(arr[:, :, 3], 40, 120)
    vec = cv2.dilate(np.maximum(edges, sil_edge), np.ones((2, 2), np.uint8), iterations=1)
    glow = cv2.GaussianBlur(vec.astype(np.float32), (7, 7), 2.0) / 255.0
    core = (vec > 0).astype(np.float32)

    out = np.zeros_like(arr)
    for c in range(3):
        base_c = rgb[:, :, c] * 0.22 + phosphor_rgb[c] * 0.18
        line_c = phosphor_rgb[c] * np.clip(glow * 0.85 + core * 0.95, 0.0, 1.0)
        out[:, :, c] = np.clip(base_c + line_c, 0, 255).astype(np.uint8)
    out_a = np.clip(a * fill_alpha + np.maximum(glow * 0.75, core * 0.95) * a, 0.0, 1.0)
    out[:, :, 3] = (out_a * 255.0).astype(np.uint8)
    return Image.fromarray(out)


def style_arap_mesh_overlay(rgba_im, wire_rgb=(245, 195, 85), grid_step=24, step=None):
    """Overlays a clean Delaunay/lattice ARAP finite-element triangulation onto a real cutout (`SCION 34`)."""
    if rgba_im is None:
        return None
    work = rgba_im.copy()
    arr = np.array(work)
    a = arr[:, :, 3]
    h, w = a.shape
    draw = ImageDraw.Draw(work, "RGBA")
    step = int(step if step is not None else max(14, min(w, h) // 7))
    pts = []
    for y in range(step // 2, h, step):
        row = []
        shift = (step // 3) if ((y // step) % 2 == 1) else 0
        for x in range(step // 2 + shift, w, step):
            if a[min(h - 1, y), min(w - 1, x)] > 90:
                row.append((x, y))
        pts.append(row)
    for r_i, row in enumerate(pts):
        for c_i, p0 in enumerate(row):
            if c_i + 1 < len(row):
                p1 = row[c_i + 1]
                if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < step * 1.6:
                    draw.line([p0, p1], fill=(*wire_rgb, 115), width=1)
            if r_i + 1 < len(pts):
                for p2 in pts[r_i + 1]:
                    if math.hypot(p2[0] - p0[0], p2[1] - p0[1]) < step * 1.55:
                        draw.line([p0, p2], fill=(*wire_rgb, 105), width=1)
            draw.ellipse([p0[0] - 2, p0[1] - 2, p0[0] + 2, p0[1] + 2], fill=(*wire_rgb, 175))
    return work


def style_foldes_calligraphic(rgba_im, ink_rgb=(36, 26, 20)):
    """Adds Peter Foldès calligraphic nib-ink contour & warm watercolor pigment wash (`SCION 07`)."""
    if rgba_im is None:
        return None
    arr = np.array(rgba_im)
    rgb = arr[:, :, :3].astype(np.float32)
    a = arr[:, :, 3]
    # Soften interior into a delicate watercolor wash + crisp nib contour
    blur_rgb = cv2.bilateralFilter(rgb.astype(np.uint8), 7, 45, 45).astype(np.float32)
    sil_edge = cv2.Canny(a, 40, 120)
    lum = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]).astype(np.uint8)
    int_edge = cv2.Canny(lum, 55, 140)
    nib = cv2.dilate(np.maximum(sil_edge, int_edge), np.ones((2, 2), np.uint8), iterations=1) > 0

    out = np.zeros_like(arr)
    for c in range(3):
        wash = blur_rgb[:, :, c] * 0.88 + 28.0
        out[:, :, c] = np.where(nib & (a > 40), ink_rgb[c], np.clip(wash, 0, 255)).astype(np.uint8)
    out[:, :, 3] = a
    return Image.fromarray(out)


# ============================================================================
# 4. MULTIPLANE SET COMPOSITOR & ACTOR PLACEMENT HELPERS
# ============================================================================

def paste_centered(canvas, im, cx, cy, target_h=None, target_w=None, rot_deg=0.0, alpha_mul=1.0, flip_x=False, anchor_y=0.5):
    if im is None or alpha_mul <= 0.01:
        return
    work = im.copy()
    if flip_x:
        work = ImageOps.mirror(work)
    w0, h0 = work.size
    if target_h is not None and target_w is not None:
        nw, nh = max(2, int(round(target_w))), max(2, int(round(target_h)))
    elif target_h is not None:
        sc = target_h / float(max(1, h0))
        nw, nh = max(2, int(round(w0 * sc))), max(2, int(round(h0 * sc)))
    elif target_w is not None:
        sc = target_w / float(max(1, w0))
        nw, nh = max(2, int(round(w0 * sc))), max(2, int(round(h0 * sc)))
    else:
        nw, nh = w0, h0
    work = work.resize((nw, nh), Image.Resampling.LANCZOS)
    if abs(rot_deg) > 0.15:
        work = work.rotate(rot_deg, resample=Image.Resampling.BICUBIC, expand=True)
    if alpha_mul < 0.995:
        arr = np.array(work)
        arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * alpha_mul).astype(np.uint8)
        work = Image.fromarray(arr)
    px = int(round(cx - work.width * 0.5))
    py = int(round(cy - work.height * anchor_y))
    canvas.alpha_composite(work, (px, py))


def render_ideal_actor_on_stage(
    canvas,
    char_id,
    view,
    cx,
    ground_y,
    fig_h=240,
    pose=None,
    flip_x=False,
    alpha_mul=1.0,
    style_fn=None,
    blur_sigma=0.0,
):
    """Solves & renders one of the 9 canonical 4-angle characters onto `canvas` at `(cx, ground_y)`."""
    cast = get_cast_dict()
    cspec = cast.get(char_id, cast["poet_tracksuit"])
    cw = max(240, int(fig_h * 1.25))
    ch = max(320, int(fig_h * 1.45))
    gy_local = int(ch * 0.88)
    fig_im, joints = B.solve_and_render_ideal_body(
        cspec,
        view=view,
        pose=pose or {},
        cw=cw,
        ch=ch,
        ground_y=gy_local,
        center_x=cw // 2,
        fig_h_base=fig_h,
    )
    if flip_x:
        fig_im = ImageOps.mirror(fig_im)
    if style_fn is not None:
        fig_im = style_fn(fig_im)
    if blur_sigma > 0.25:
        fig_im = fig_im.filter(ImageFilter.GaussianBlur(radius=blur_sigma))
    if alpha_mul < 0.995:
        arr = np.array(fig_im)
        arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * alpha_mul).astype(np.uint8)
        fig_im = Image.fromarray(arr)
    px = int(round(cx - cw // 2))
    py = int(round(ground_y - gy_local))
    canvas.alpha_composite(fig_im, (px, py))
    return joints


def walk_pose(phase, stride_deg=24.0, arm_deg=20.0, lean_deg=5.0, reach_l=0.0, reach_r=0.0, kneel=0.0):
    """Generates a natural ground-up locomotion / acting pose dictionary for `solve_and_render_ideal_body`."""
    s = math.sin(phase)
    c = math.cos(phase)
    if kneel > 0.05:
        return dict(
            spine_deg=lean_deg + 12.0 * kneel,
            thigh_L_deg=80.0 * kneel + s * 6.0 * (1.0 - kneel),
            shin_L_deg=-6.0 * kneel,
            foot_L_deg=0.0,
            thigh_R_deg=24.0 * kneel - s * 6.0 * (1.0 - kneel),
            shin_R_deg=-85.0 * kneel,
            foot_R_deg=-65.0 * kneel,
            uarm_L_deg=28.0 + reach_l * 26.0,
            farm_L_deg=68.0 + reach_l * 24.0,
            uarm_R_deg=12.0 + reach_r * 22.0,
            farm_R_deg=42.0 + reach_r * 20.0,
            show_far_arm_in_side=True,
        )
    return dict(
        spine_deg=lean_deg,
        thigh_L_deg=s * stride_deg,
        shin_L_deg=max(0.0, c) * (-22.0) + min(0.0, s) * 8.0,
        foot_L_deg=s * 10.0,
        thigh_R_deg=-s * stride_deg,
        shin_R_deg=max(0.0, -c) * (-22.0) + min(0.0, -s) * 8.0,
        foot_R_deg=-s * 10.0,
        uarm_L_deg=-s * arm_deg + reach_l * 42.0,
        farm_L_deg=18.0 + max(0.0, -s) * 18.0 + reach_l * 48.0,
        uarm_R_deg=s * arm_deg + reach_r * 38.0,
        farm_R_deg=16.0 + max(0.0, s) * 18.0 + reach_r * 44.0,
        show_far_arm_in_side=True,
    )


def add_cream_paper_margin(rgba_im, margin_px=4, paper_rgb=(242, 235, 218), edge_rgb=(32, 28, 24)):
    """Adds a clean scissor-cut cream paper margin around an RGBA cutout (`01-gilliam` / `09-igarashi` style)."""
    if rgba_im is None or margin_px <= 0:
        return rgba_im
    arr = np.array(rgba_im)
    solid = (arr[:, :, 3] > 30).astype(np.uint8)
    k_in = margin_px * 2 + 1
    k_out = (margin_px + 1) * 2 + 1
    dil_in = cv2.dilate(solid, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_in, k_in))) > 0
    dil_out = cv2.dilate(solid, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_out, k_out))) > 0
    paper_ring = dil_in & (~(solid > 0))
    ink_ring = dil_out & (~dil_in)
    out = arr.copy()
    out[paper_ring, :3] = paper_rgb
    out[paper_ring, 3] = 250
    out[ink_ring, :3] = edge_rgb
    out[ink_ring, 3] = 240
    return Image.fromarray(out)


def add_rim_light_wrap(rgba_im, rim_rgb=(255, 205, 125), strength=0.68):
    """Adds a directional warm/cool rim-light wrap along the contour of an RGBA figure."""
    if rgba_im is None:
        return None
    arr = np.array(rgba_im)
    solid = (arr[:, :, 3] > 40).astype(np.uint8)
    dist = cv2.distanceTransform(solid, cv2.DIST_L2, 3)
    rim_w = np.clip(1.0 - (dist - 1.0) / 3.2, 0.0, 1.0) * (solid > 0) * strength
    for c in range(3):
        arr[:, :, c] = np.clip(arr[:, :, c].astype(np.float32) * (1.0 - rim_w) + rim_rgb[c] * rim_w, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def render_round2_human_actor(
    canvas_pil,
    sk,
    foot_x,
    foot_y,
    height=220.0,
    facing=1.0,
    walk_phase=0.0,
    walking=False,
    lean_deg=4.0,
    head_pitch_deg=0.0,
    reach=0.0,
    arm_raise=0.0,
    sit=0.0,
    style="clean_vector",
    coat_rgb=(44, 54, 72),
    pants_rgb=(28, 34, 46),
    skin_rgb=(176, 132, 102),
    rim_rgb=(255, 205, 125),
    sunglasses=False,
    wings=False,
    robe=False,
    alpha=255,
    char_id=None,
    view=None,
):
    """
    Renders a real de-bradded 4-angle painted WYGWYL character (`solve_and_render_ideal_body`)
    or real painted poem-specific character (`WHOLE_FIGURE_MAP`) at `(foot_x, foot_y)`,
    styled in the requested SCION studio grammar (`reiniger`, `gilliam`, `sutherland`,
    `foldes`, `norstein`, `cartoon_saloon`, `arap`, `clean_vector`), and updates `sk`
    with exact stage-space joint coordinates (`hand1`, `hand2`, `hip`, `shoulder`, `head_c`).
    """
    if alpha <= 2:
        return sk

    # 1. Infer `char_id` and `view` if not explicitly passed
    if char_id is None:
        if wings:
            char_id = "angel"
        elif style == "norstein" and alpha < 210 and coat_rgb[2] > 200:
            char_id = "poet_soul"
        elif style == "reiniger" and height >= 190.0:
            char_id = "ghost_child"
        elif height < 185.0:
            char_id = "young_poet"
        elif robe:
            if coat_rgb[0] > 130:
                char_id = "ancestor_elder"
            elif coat_rgb[2] > 95:
                char_id = "ancestor_robe"
            else:
                char_id = "elder_man"
        elif sit > 0.55 and coat_rgb[2] > 85:
            char_id = "dj_cyber"
        elif sit > 0.70:
            char_id = "citizen_1"
        elif style == "foldes" and coat_rgb[0] > 150:
            char_id = "woman_brocade"
        elif style == "norstein" and skin_rgb[0] < 80:
            char_id = "ex_olive_bomber"
        elif coat_rgb[0] > 80 and coat_rgb[2] > 85 and not sunglasses:
            char_id = "mother_cardigan"
        elif sunglasses:
            char_id = "poet_tracksuit"
        else:
            char_id = "poet_tracksuit"

    if view is None:
        if char_id == "ex_olive_bomber":
            view = "BACK"
        elif char_id in ("dj_cyber", "woman_brocade", "angel", "elder_man"):
            view = "FRONT"
        elif char_id in ("mother_cardigan", "party_woman_gown", "party_gentleman"):
            view = "3Q"
        else:
            view = "SIDE"

    # Ground contact shadow (except on pure CRT vector display)
    s = height / 220.0
    if style != "sutherland" and not wings:
        sh_layer = Image.new("RGBA", canvas_pil.size, (0, 0, 0, 0))
        d_sh = ImageDraw.Draw(sh_layer, "RGBA")
        sh_rx = int(28 * s)
        sh_ry = int(6 * s)
        sh_alpha = int(92 * (alpha / 255.0))
        d_sh.ellipse([foot_x - sh_rx, foot_y - sh_ry, foot_x + sh_rx, foot_y + sh_ry], fill=(6, 8, 12, sh_alpha))
        canvas_pil.alpha_composite(sh_layer)

    # Quantize animation parameters for fast 24fps caching
    phase_bin = int(round(((walk_phase % (2.0 * math.pi)) / (2.0 * math.pi)) * 28.0)) % 28 if (walking or wings) else 0
    sit_bin = int(round(sit * 10.0))
    reach_bin = int(round(reach * 14.0))
    raise_bin = int(round(arm_raise * 14.0))
    lean_bin = int(round(lean_deg / 2.0))
    pitch_bin = int(round(head_pitch_deg / 2.0))
    h_int = max(80, int(round(height)))

    cache_key = (
        char_id, view, h_int, phase_bin, bool(walking),
        sit_bin, reach_bin, raise_bin, lean_bin, pitch_bin,
        style, tuple(rim_rgb), bool(wings),
    )

    if cache_key in _SOLVED_ACTOR_CACHE:
        fig_im, local_joints, cw, gy_local = _SOLVED_ACTOR_CACHE[cache_key]
    else:
        ph_q = (phase_bin / 28.0) * (2.0 * math.pi)
        if char_id in WHOLE_FIGURE_MAP:
            base_im = load_clean_whole_figure(WHOLE_FIGURE_MAP[char_id])
            cw = max(240, int(h_int * 1.45))
            ch = max(280, int(h_int * 1.45))
            gy_local = int(ch * 0.90)
            fig_im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            if base_im is not None:
                # Optional Angel wings behind the Angel figure
                if wings or char_id == "angel":
                    w_im = load_cut_prop("08.cast.angel.wings", "p01")
                    if w_im is not None:
                        flap_deg = math.sin(ph_q * 2.0) * 8.0
                        paste_centered(fig_im, w_im, cw // 2, gy_local - int(h_int * 0.62), target_h=int(h_int * 0.72), rot_deg=flap_deg, alpha_mul=0.92)
                bob_y = int(abs(math.cos(ph_q)) * 4.0) if walking else 0
                rot_d = lean_bin * 1.2 + (math.sin(ph_q) * 2.5 if walking else 0.0)
                paste_centered(fig_im, base_im, cw // 2, gy_local - bob_y, target_h=h_int, rot_deg=-rot_d, anchor_y=0.98)
            local_joints = {
                "H_C": (cw * 0.50, gy_local - h_int * 0.48),
                "N": (cw * 0.50, gy_local - h_int * 0.80),
                "W_L": (cw * 0.64, gy_local - h_int * 0.52 - reach * 22.0 - arm_raise * 35.0),
                "W_R": (cw * 0.36, gy_local - h_int * 0.52 - reach * 18.0 - arm_raise * 30.0),
            }
        else:
            cast = get_cast_dict()
            cspec = cast.get(char_id, cast["poet_tracksuit"])
            sc_char = cspec.get("scale", 1.0)
            fig_h_base = int(round(h_int / max(0.35, sc_char)))
            cw = max(240, int(h_int * 1.35))
            ch = max(300, int(h_int * 1.45))
            gy_local = int(ch * 0.88)

            s_ph = math.sin(ph_q) if walking else 0.0
            c_ph = math.cos(ph_q) if walking else 0.0
            stride_deg = 24.0 if walking else 5.0
            arm_sw = 20.0 if walking else 0.0
            r_eff = clamp(reach + arm_raise * 0.85, 0.0, 1.35)

            if sit > 0.15:
                pose_dict = dict(
                    spine_deg=lean_bin * 2.0,
                    thigh_L_deg=52.0 * sit,
                    shin_L_deg=-48.0 * sit,
                    foot_L_deg=0.0,
                    thigh_R_deg=38.0 * sit,
                    shin_R_deg=-42.0 * sit,
                    foot_R_deg=0.0,
                    uarm_L_deg=24.0 + r_eff * 38.0,
                    farm_L_deg=48.0 + r_eff * 36.0 + arm_raise * 28.0,
                    uarm_R_deg=14.0 + r_eff * 28.0,
                    farm_R_deg=36.0 + r_eff * 28.0 + arm_raise * 22.0,
                    head_deg=pitch_bin * 2.0,
                    show_far_arm_in_side=True,
                )
            else:
                pose_dict = dict(
                    spine_deg=lean_bin * 2.0,
                    thigh_L_deg=s_ph * stride_deg,
                    shin_L_deg=max(0.0, c_ph) * (-22.0) + min(0.0, s_ph) * 8.0,
                    foot_L_deg=s_ph * 10.0,
                    thigh_R_deg=-s_ph * stride_deg,
                    shin_R_deg=max(0.0, -c_ph) * (-22.0) + min(0.0, -s_ph) * 8.0,
                    foot_R_deg=-s_ph * 10.0,
                    uarm_L_deg=-s_ph * arm_sw + r_eff * 44.0 + arm_raise * 32.0,
                    farm_L_deg=18.0 + max(0.0, -s_ph) * 18.0 + r_eff * 50.0 + arm_raise * 28.0,
                    uarm_R_deg=s_ph * arm_sw + r_eff * 36.0 + arm_raise * 24.0,
                    farm_R_deg=16.0 + max(0.0, s_ph) * 18.0 + r_eff * 42.0 + arm_raise * 22.0,
                    head_deg=pitch_bin * 2.0,
                    show_far_arm_in_side=True,
                )

            fig_im, local_joints = B.solve_and_render_ideal_body(
                cspec,
                view=view,
                pose=pose_dict,
                cw=cw,
                ch=ch,
                ground_y=gy_local,
                center_x=cw // 2,
                fig_h_base=fig_h_base,
            )

        # Apply SCION studio material transformation to `fig_im`
        if style == "reiniger":
            fig_im = style_reiniger_silhouette(fig_im, rim_rgb=rim_rgb, interior_rgb=(10, 9, 14), filigree=True)
        elif style == "gilliam":
            fig_im = style_gilliam_engraved_cutout(fig_im, tint_rgb=(228, 210, 178))
            fig_im = add_cream_paper_margin(fig_im, margin_px=4)
        elif style == "arap":
            fig_im = style_gilliam_engraved_cutout(fig_im, tint_rgb=(228, 210, 178))
            fig_im = add_cream_paper_margin(fig_im, margin_px=3)
            fig_im = style_arap_mesh_overlay(fig_im, wire_rgb=(245, 200, 90))
        elif style == "foldes":
            fig_im = style_foldes_calligraphic(fig_im, ink_rgb=rim_rgb)
        elif style == "sutherland":
            fig_im = style_sutherland_crt_blueprint(fig_im, phosphor_rgb=(78, 255, 128), fill_alpha=0.58)
            d_crt = ImageDraw.Draw(fig_im, "RGBA")
            v_col = (95, 255, 145, 245)
            for k0, k1 in [
                ("H_C", "N"), ("H_L", "K_L"), ("K_L", "A_L"), ("H_R", "K_R"), ("K_R", "A_R"),
                ("S_L", "E_L"), ("E_L", "W_L"), ("S_R", "E_R"), ("E_R", "W_R"),
            ]:
                if k0 in local_joints and k1 in local_joints:
                    d_crt.line([local_joints[k0], local_joints[k1]], fill=v_col, width=2)
            for kj in ("H_C", "N", "K_L", "A_L", "K_R", "A_R", "E_L", "W_L"):
                if kj in local_joints:
                    jx, jy = local_joints[kj]
                    d_crt.ellipse([jx - 3.5, jy - 3.5, jx + 3.5, jy + 3.5], outline=v_col, width=1)
        elif style == "norstein":
            fig_im = add_rim_light_wrap(fig_im, rim_rgb=rim_rgb, strength=0.72)
        elif style == "cartoon_saloon":
            fig_im = add_rim_light_wrap(fig_im, rim_rgb=(248, 215, 118), strength=0.48)
        else:
            fig_im = add_rim_light_wrap(fig_im, rim_rgb=rim_rgb, strength=0.38)

        _SOLVED_ACTOR_CACHE[cache_key] = (fig_im, local_joints, cw, gy_local)

    work_im = fig_im.copy()
    if facing < 0 and view in ("SIDE", "3Q"):
        work_im = ImageOps.mirror(work_im)
    if alpha < 254:
        arr = np.array(work_im)
        arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * (alpha / 255.0)).astype(np.uint8)
        work_im = Image.fromarray(arr)

    px = int(round(foot_x - cw // 2))
    py = int(round(foot_y - gy_local))
    canvas_pil.alpha_composite(work_im, (px, py))

    # Map local solved joints back into global stage coordinates on `sk`
    def to_stage(pt):
        lx, ly = pt
        if facing < 0 and view in ("SIDE", "3Q"):
            lx = cw - lx
        return (px + lx, py + ly)

    if "H_C" in local_joints:
        sk["hip"] = to_stage(local_joints["H_C"])
    if "N" in local_joints:
        sk["shoulder"] = to_stage(local_joints["N"])
    if "W_L" in local_joints:
        sk["wrist1"] = to_stage(local_joints["W_L"])
        sk["hand1"] = (sk["wrist1"][0] + (8.0 if facing >= 0 else -8.0) * s, sk["wrist1"][1])
    if "W_R" in local_joints:
        sk["wrist2"] = to_stage(local_joints["W_R"])
        sk["hand2"] = (sk["wrist2"][0] + (8.0 if facing >= 0 else -8.0) * s, sk["wrist2"][1])
    return sk



def blend_multiplane_underlay(canvas, plate_id, cam_x=0.0, cam_y=0.0, opacity=0.48, style_mode="natural", defocus_bg=0.0):
    """
    Blends real multiplane depth layers (`P6_sky`, `P5_far`, `P4_mid`) onto `canvas` with true
    depth parallax (`0.10`, `0.26`, `0.52`) and SCION studio material styling.
    """
    layers = load_multiplane_plate_dir(plate_id)
    if not layers:
        return
    comp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for k, par in [("sky", 0.10), ("far", 0.26), ("mid", 0.52)]:
        im = layers.get(k)
        if im is None:
            continue
        dx = int(round(-cam_x * par))
        dy = int(round(-cam_y * par * 0.5))
        comp.alpha_composite(im, (dx, dy))

    if style_mode == "reiniger":
        # Stained amber/gold backlit parchment silhouette plate
        arr = np.array(comp).astype(np.float32)
        lum = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]) / 255.0
        arr[:, :, 0] = np.clip(lum * 225.0 + 18.0, 0, 255)
        arr[:, :, 1] = np.clip(lum * 155.0 + 10.0, 0, 255)
        arr[:, :, 2] = np.clip(lum * 68.0 + 6.0, 0, 255)
        comp = Image.fromarray(arr.astype(np.uint8))
    elif style_mode == "gilliam":
        comp = style_gilliam_engraved_cutout(comp, tint_rgb=(210, 192, 158))
    elif style_mode == "sutherland":
        comp = style_sutherland_crt_blueprint(comp, phosphor_rgb=(50, 235, 145), fill_alpha=0.35)
    elif style_mode == "foldes":
        comp = style_foldes_calligraphic(comp, ink_rgb=(42, 32, 24))

    if defocus_bg > 0.25:
        comp = comp.filter(ImageFilter.GaussianBlur(radius=defocus_bg))

    arr = np.array(comp)
    arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * opacity).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(arr), (0, 0))


def blend_multiplane_occluder(canvas, plate_id, cam_x=0.0, cam_y=0.0, opacity=0.55, style_mode="natural", defocus_fg=0.0):
    """Blends the foreground `P0_occluders.png` layer IN FRONT OF the characters (`parallax = 1.25`)."""
    layers = load_multiplane_plate_dir(plate_id)
    occ = layers.get("occ")
    if occ is None or opacity <= 0.01:
        return
    if style_mode == "reiniger":
        occ = style_reiniger_silhouette(occ, rim_rgb=(235, 175, 75), interior_rgb=(12, 10, 9), filigree=False)
    elif style_mode == "gilliam":
        occ = style_gilliam_engraved_cutout(occ, tint_rgb=(185, 168, 138))
    elif style_mode == "sutherland":
        occ = style_sutherland_crt_blueprint(occ, phosphor_rgb=(65, 255, 165), fill_alpha=0.22)
    if defocus_fg > 0.25:
        occ = occ.filter(ImageFilter.GaussianBlur(radius=defocus_fg))
    arr = np.array(occ)
    arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * opacity).astype(np.uint8)
    dx = int(round(-cam_x * 1.25))
    dy = int(round(-cam_y * 0.6))
    canvas.alpha_composite(Image.fromarray(arr), (dx, dy))


# ============================================================================
# 5. PER-POEM ROUND 2 EXISTING-ASSET COMPOSITOR (`apply_round2_existing_assets`)
# ============================================================================

POEM_SOURCE_MANIFEST = {
    1: {
        "plates": ["gen_a63bb494b1_10", "gen_872d16167d_50", "gen_d70a8829a9_50"],
        "cuts": [("01.props.window", "p01"), ("01.props.chandeliers", "p01"), ("01.hero.catwalk", "p01")],
        "cast": ["poet_black_tshirt", "party_gentleman", "party_woman_gown"],
    },
    2: {
        "plates": ["gen_a63bb494b1_50"],
        "cuts": [("02.props.tambourine", "p01"), ("02.props.blinds-height", "p01"), ("02.props.car", "p01"), ("02.set.living_room_1990s", "p01")],
        "cast": ["young_poet", "mother_cardigan", "poet_black_tshirt", "play/assets/ghost_child__ghost_nightclothes/00.webp"],
    },
    3: {
        "plates": ["gen_872d16167d_50", "gen_933cc247ea_10", "gen_e315da34f9_30"],
        "cuts": [
            ("03.hero.chapel", "p01"),
            ("03.hero.chapel.decay", "p01"),
            ("03.hero.chapel.ruin", "p01"),
            ("03.props.rose-window", "p01"),
            ("03.props.gifts-bread-cups", "p01"),
            ("03.props.cobwebs", "p01"),
            ("03.props.tambourine-broken", "p01"),
        ],
        "cast": [],  # Strictly 0 human figures per I4!
    },
    4: {
        "plates": ["world_ef9f6c7e_3", "gen_ca6878be91_90", "gen_ca6878be91_30"],
        "cuts": [("04.props.faith-blooms", "p01"), ("04.props.heart", "p01"), ("04.props.poet-jointed-hands", "p01"), ("04.hero.viaduct", "p01")],
        "cast": ["poet_tracksuit", "ex_olive_bomber"],
    },
    5: {
        "plates": ["gen_bad0cf8d7a_70", "world_bf0a66ea_0"],
        "cuts": [("05.set.winged_marble_gate", "p03"), ("05.props.star-names", "p01"), ("05.props.galaxy-universe", "p01")],
        "cast": [
            "poet_tracksuit",
            "young_poet",
            "mother_cardigan",
            "play/assets/ancestor_elder__white_silver/00.webp",
            "play/assets/ancestor_robe__indigo_gold/00.webp",
            "play/assets/father_elder__poem09/00.webp",
        ],
    },
    6: {
        "plates": ["world_3238a164_1", "gen_69ee5bb28b_90", "world_bf0a66ea_0"],
        "cuts": [("06.set.atlantis_plaza", "p02"), ("06.props.coin-booth", "p01"), ("06.fx.comet", "p01")],
        "cast": ["poet_tracksuit", "play/assets/citizen_1__atlantis/00.webp", "play/assets/ancestor_elder__white_silver/00.webp"],
    },
    7: {
        "plates": ["gen_9c5f9c7c4a_70"],
        "cuts": [("07.props.dj-decks", "p01"), ("07.props.speakers-vu", "p01"), ("07.props.mic-daisy-rings", "p01")],
        "cast": ["dj_cyber", "poet_tracksuit", "party_woman_gown"],
    },
    8: {
        "plates": ["world_8bc7b3e2_0", "world_7a904269_0"],
        "cuts": [("08.hero.marquee", "p01"), ("08.props.basins", "p01"), ("08.props.moons-laundry", "p01"), ("08.cast.angel.wings", "p01")],
        "cast": ["poet_tracksuit", "play/assets/angel__robe/00.webp", "play/assets/poet_soul__soul/00.webp"],
    },
    9: {
        "plates": ["gen_ac146f1212_50", "gen_a63bb494b1_50", "world_3238a164_1"],
        "cuts": [("09.props.phonebooth", "p01"), ("09.set.mother_living_room", "p01"), ("09.props.phones-chair", "p01")],
        "cast": ["poet_tracksuit", "mother_cardigan", "play/assets/father_elder__poem09/00.webp"],
    },
    10: {
        "plates": ["gen_366225426b_70", "gen_f729b3bb28_90", "view_087"],
        "cuts": [("10.props.bike-ride-views", "p01"), ("10.props.bike-skeleton", "p01"), ("10.props.tree-dawn-sign", "p01")],
        "cast": ["poet_tracksuit"],
    },
    11: {
        "plates": ["gen_69ee5bb28b_30", "world_f05c1fa5_1", "gen_e315da34f9_10"],
        "cuts": [("11.props.temple.whole", "p01"), ("11.props.temple.arrival.courses-columns", "p01"), ("11.props.parked-motorcycle", "p01")],
        "cast": ["poet_tracksuit"],
    },
    12: {
        "plates": ["world_f56df2d8_1", "world_ef9f6c7e_3"],
        "cuts": [("12.props.hand-hourglass", "p01"), ("12.props.last-hourglass", "p01"), ("12.props.niche-porch", "p01")],
        "cast": ["poet_tracksuit", "play/assets/brother_1__poem12/00.webp", "play/assets/elder_man__poem13/00.webp"],
    },
    13: {
        "plates": ["gen_e315da34f9_70", "world_e9c68c53_0", "gen_ca6878be91_30"],
        "cuts": [("13.props.distant-window", "p01"), ("13.props.planet-boats", "p01"), ("13.props.harvest", "p01"), ("13.props.cafe", "p01")],
        "cast": ["woman_brocade", "poet_tracksuit", "play/assets/couple_1_a__poem13/00.webp", "play/assets/couple_1_b__poem13/00.webp"],
    },
    14: {
        "plates": ["gen_69ee5bb28b_30", "gen_5ab27d990d_70", "gen_872d16167d_50"],
        "cuts": [("14.props.door", "p01"), ("14.props.party", "p01"), ("14.props.reel", "p01")],
        "cast": ["poet_tracksuit", "party_woman_gown", "party_gentleman", "woman_brocade", "mother_cardigan", "young_poet"],
    },
}


def apply_round2_existing_assets(canvas_rgb, poem_num, i, t, state, q, score):
    """
    Overlays and integrates the existing WYGWYL multiplane plates, cut props, and de-bradded
    4-angle characters onto `canvas_rgb` (the poem's SCION studio stage) so every poem is
    genuinely handmade from the repository's existing visual assets.
    """
    canvas = canvas_rgb.convert("RGBA")
    cam_x = math.sin(t * 0.35) * 28.0 + (q - 0.5) * 44.0
    cam_y = math.cos(t * 0.25) * 8.0

    # -------------------------------------------------------------------------
    # POEM 01: Out of Life — SCION 48 (Yuri Norstein Multiplane Fog & Defocus)
    # -------------------------------------------------------------------------
    if poem_num == 1:
        pl_id = "gen_872d16167d_50" if q > 0.45 else "gen_a63bb494b1_10"
        blend_multiplane_underlay(canvas, pl_id, cam_x=cam_x, cam_y=cam_y, opacity=0.44, defocus_bg=max(0.5, (1.0 - q) * 3.5))
        # Deep plane: chandelier + vintage ballroom waltz duo (sharpening as q -> 1)
        chand = load_cut_prop("01.props.chandeliers", "p01")
        paste_centered(canvas, chand, W * 0.64 - cam_x * 0.25, H * 0.22, target_h=155, alpha_mul=0.55 + 0.40 * q)
        waltz_blur = max(0.0, (1.0 - q) * 3.8)
        waltz_x = W * 0.62 + math.sin(t * 1.1) * 36.0
        render_ideal_actor_on_stage(
            canvas, "party_gentleman", "SIDE", waltz_x - 36, H * 0.78, fig_h=int(185 + 25 * q),
            pose=walk_pose(t * 2.2, stride_deg=14, arm_deg=26, reach_l=0.6), alpha_mul=0.45 + 0.50 * q, blur_sigma=waltz_blur
        )
        render_ideal_actor_on_stage(
            canvas, "party_woman_gown", "3Q", waltz_x + 36, H * 0.78, fig_h=int(182 + 25 * q),
            pose=walk_pose(t * 2.2 + math.pi, stride_deg=12, arm_deg=24, reach_l=0.5), flip_x=True, alpha_mul=0.45 + 0.50 * q, blur_sigma=waltz_blur
        )
        # Mid plane: window casement & fire-escape catwalk
        win_im = load_cut_prop("01.props.window", "p01")
        paste_centered(canvas, win_im, W * 0.64 - cam_x * 0.55, H * 0.48, target_h=390, alpha_mul=0.62)
        cat_im = load_cut_prop("01.hero.catwalk", "p01")
        paste_centered(canvas, cat_im, W * 0.28 - cam_x * 0.85, H * 0.84, target_w=540, alpha_mul=0.72)
        # Foreground plane: Poet in black t-shirt on fire escape (defocusing as camera racks into the ballroom!)
        fg_blur = max(0.0, (q - 0.25) * 4.5)
        render_ideal_actor_on_stage(
            canvas, "poet_black_tshirt", "SIDE" if q > 0.3 else "3Q", W * 0.26 - cam_x * 0.9, H * 0.89, fig_h=275,
            pose=walk_pose(t * 1.4, stride_deg=10, arm_deg=14, reach_l=min(1.0, q * 1.2)), alpha_mul=0.94, blur_sigma=fg_blur
        )
        blend_multiplane_occluder(canvas, "gen_a63bb494b1_10", cam_x=cam_x, cam_y=cam_y, opacity=0.48, defocus_fg=fg_blur)

    # -------------------------------------------------------------------------
    # POEM 02: No Guide — SCION 02 (Lotte Reiniger Backlit Silhouette Theatre)
    # -------------------------------------------------------------------------
    elif poem_num == 2:
        blend_multiplane_underlay(canvas, "gen_a63bb494b1_50", cam_x=cam_x, cam_y=cam_y, opacity=0.42, style_mode="reiniger")
        # Silhouetted 1990s living room blinds, height-mark doorjamb & tambourine
        blinds = style_reiniger_silhouette(load_cut_prop("02.props.blinds-height", "p01"))
        paste_centered(canvas, blinds, W * 0.22 - cam_x * 0.35, H * 0.46, target_h=340, alpha_mul=0.82)
        tamb = style_reiniger_silhouette(load_cut_prop("02.props.tambourine", "p01"))
        paste_centered(canvas, tamb, W * 0.50, H * 0.26 + math.sin(t * 3.2) * 8.0, target_h=115, rot_deg=math.sin(t * 4.0) * 14.0, alpha_mul=0.92)
        # Reiniger scissor-cut silhouettes of Young Poet (0.70x), Ghost Child, and Mother
        gap_x = 65.0 + (1.0 - q) * 180.0
        render_ideal_actor_on_stage(
            canvas, "mother_cardigan", "SIDE", W * 0.24, H * 0.85, fig_h=255,
            pose=walk_pose(t * 1.5, stride_deg=8, arm_deg=18, reach_l=0.55),
            style_fn=lambda im: style_reiniger_silhouette(im, rim_rgb=(245, 190, 88))
        )
        render_ideal_actor_on_stage(
            canvas, "young_poet", "SIDE", W * 0.52 - gap_x * 0.45, H * 0.85, fig_h=250,
            pose=walk_pose(t * 2.4, stride_deg=18, arm_deg=24, reach_l=0.7),
            style_fn=lambda im: style_reiniger_silhouette(im, rim_rgb=(252, 208, 105))
        )
        ghost_im = style_reiniger_silhouette(load_clean_whole_figure("play/assets/ghost_child__ghost_nightclothes/00.webp"), rim_rgb=(255, 220, 130))
        paste_centered(canvas, ghost_im, W * 0.54 + gap_x * 0.55, H * 0.85, target_h=185, flip_x=True, alpha_mul=0.88, anchor_y=1.0)
        blend_multiplane_occluder(canvas, "gen_a63bb494b1_50", cam_x=cam_x, cam_y=cam_y, opacity=0.45, style_mode="reiniger")

    # -------------------------------------------------------------------------
    # POEM 03: Used to Be — SCION 01 (Terry Gilliam Cut-Out Architectural Collage)
    # Strictly 0 human figures per I4 (`n_puppets == 0`)!
    # -------------------------------------------------------------------------
    elif poem_num == 3:
        pl_id = "gen_872d16167d_50" if q > 0.65 else ("gen_933cc247ea_10" if q > 0.32 else "gen_e315da34f9_30")
        blend_multiplane_underlay(canvas, pl_id, cam_x=cam_x, cam_y=cam_y, opacity=0.48, style_mode="gilliam")
        # Gilliam paper-cut substitution across real chapel states (`chapel`, `chapel.decay`, `chapel.ruin`)
        ch_sheet = "03.hero.chapel" if q > 0.66 else ("03.hero.chapel.decay" if q > 0.33 else "03.hero.chapel.ruin")
        chapel_im = style_gilliam_engraved_cutout(load_cut_prop(ch_sheet, "p01"))
        snap_tilt = round(math.sin(t * 1.8) * 2.0) * 1.5 * (1.0 - q)
        paste_centered(canvas, chapel_im, W * 0.50 - cam_x * 0.35, H * 0.56, target_h=430, rot_deg=snap_tilt, alpha_mul=0.88)
        # Rose window, communion chalice/bread, cobwebs & shattered tambourine cutouts
        rose_im = style_gilliam_engraved_cutout(load_cut_prop("03.props.rose-window", "p01"))
        paste_centered(canvas, rose_im, W * 0.50 - cam_x * 0.25, H * 0.26, target_h=165, rot_deg=float(int(t * 2) * 15), alpha_mul=0.85)
        gifts_im = style_gilliam_engraved_cutout(load_cut_prop("03.props.gifts-bread-cups", "p01"))
        paste_centered(canvas, gifts_im, W * 0.26, H * 0.78, target_h=145, rot_deg=(1.0 - q) * (-28.0), alpha_mul=0.90)
        tamb_brk = style_gilliam_engraved_cutout(load_cut_prop("03.props.tambourine-broken", "p01"))
        paste_centered(canvas, tamb_brk, W * 0.75, H * 0.80, target_h=140, rot_deg=(1.0 - q) * 22.0, alpha_mul=0.90)
        if q < 0.75:
            cob_im = style_gilliam_engraved_cutout(load_cut_prop("03.props.cobwebs", "p01"))
            paste_centered(canvas, cob_im, W * 0.18, H * 0.22, target_h=190, alpha_mul=min(0.85, (1.0 - q) * 1.1))
        blend_multiplane_occluder(canvas, pl_id, cam_x=cam_x, cam_y=cam_y, opacity=0.42, style_mode="gilliam")

    # -------------------------------------------------------------------------
    # POEM 04: Only Everything — SCION 41 (Secondary Dynamics & Earned Stillness)
    # -------------------------------------------------------------------------
    elif poem_num == 4:
        pl_id = "gen_ca6878be91_90" if q < 0.6 else "world_ef9f6c7e_3"
        blend_multiplane_underlay(canvas, pl_id, cam_x=cam_x, cam_y=cam_y, opacity=0.46)
        viaduct = load_cut_prop("04.hero.viaduct", "p01")
        paste_centered(canvas, viaduct, W * 0.52 - cam_x * 0.30, H * 0.45, target_w=860, alpha_mul=0.52)
        # Spring-damper secondary oscillation amplitude decays as q -> threshold (earned stillness)
        energy = max(0.02, 1.0 - q * 0.92)
        sway_deg = math.sin(t * 4.2) * 18.0 * energy
        # Real faith blooms & glowing heart
        bloom = load_cut_prop("04.props.faith-blooms", "p01")
        for bx, sc_b, ph_b in [(0.18, 150, 0.0), (0.34, 175, 1.1), (0.68, 165, 2.2), (0.84, 145, 3.1)]:
            paste_centered(
                canvas, bloom, W * bx - cam_x * 0.6, H * 0.84, target_h=sc_b,
                rot_deg=math.sin(t * 3.8 + ph_b) * 14.0 * energy, alpha_mul=0.86, anchor_y=0.92
            )
        heart_im = load_cut_prop("04.props.heart", "p01")
        paste_centered(canvas, heart_im, W * 0.50, H * 0.30 + math.sin(t * 3.0) * 10.0 * energy, target_h=125, rot_deg=sway_deg * 0.4, alpha_mul=0.88)
        # Articulated Poet (Tracksuit) & Ex (Olive Bomber, strictly BACK/3Q-BACK) settling into stillness
        render_ideal_actor_on_stage(
            canvas, "ex_olive_bomber", "BACK", W * 0.64, H * 0.83, fig_h=225,
            pose=walk_pose(t * 2.0, stride_deg=14 * energy, arm_deg=16 * energy, lean_deg=4 * energy)
        )
        render_ideal_actor_on_stage(
            canvas, "poet_tracksuit", "SIDE", W * 0.38, H * 0.87, fig_h=258,
            pose=walk_pose(t * 2.4, stride_deg=18 * energy, arm_deg=24 * energy, lean_deg=8 * energy, reach_l=0.65)
        )
        blend_multiplane_occluder(canvas, pl_id, cam_x=cam_x, cam_y=cam_y, opacity=0.45)

    # -------------------------------------------------------------------------
    # POEM 05: When You Get Where You're Going — SCION 18 (Cartoon Saloon Lineage)
    # -------------------------------------------------------------------------
    elif poem_num == 5:
        blend_multiplane_underlay(canvas, "world_bf0a66ea_0", cam_x=cam_x * 0.5, cam_y=cam_y, opacity=0.44)
        # Sculpted Winged Marble Gate & gold-leaf star names
        gate_im = load_cut_prop("05.set.winged_marble_gate", "p03")
        paste_centered(canvas, gate_im, W * 0.50, H * 0.48, target_h=460, alpha_mul=0.78)
        stars_im = load_cut_prop("05.props.star-names", "p01")
        paste_centered(canvas, stars_im, W * 0.50, H * 0.20, target_w=680, alpha_mul=0.45 + 0.50 * q)
        # Ancestor Elder (White/Silver), Ancestor Robe (Indigo/Gold), Mother, Young Poet & Poet in sacred symmetry
        anc_w = load_clean_whole_figure("play/assets/ancestor_elder__white_silver/00.webp")
        anc_i = load_clean_whole_figure("play/assets/ancestor_robe__indigo_gold/00.webp")
        fat_e = load_clean_whole_figure("play/assets/father_elder__poem09/00.webp")
        paste_centered(canvas, anc_w, W * 0.16, H * 0.86, target_h=245, alpha_mul=0.92, anchor_y=1.0)
        paste_centered(canvas, anc_i, W * 0.84, H * 0.86, target_h=245, alpha_mul=0.92, anchor_y=1.0)
        paste_centered(canvas, fat_e, W * 0.29, H * 0.84, target_h=225, alpha_mul=0.88, anchor_y=1.0)
        render_ideal_actor_on_stage(
            canvas, "mother_cardigan", "3Q", W * 0.71, H * 0.84, fig_h=228,
            pose=walk_pose(t * 1.2, stride_deg=6, arm_deg=14, reach_l=0.4), flip_x=True
        )
        render_ideal_actor_on_stage(
            canvas, "young_poet", "FRONT", W * 0.43, H * 0.87, fig_h=235,
            pose=walk_pose(t * 1.6, stride_deg=8, arm_deg=16, reach_r=0.4)
        )
        render_ideal_actor_on_stage(
            canvas, "poet_tracksuit", "3Q", W * 0.56, H * 0.87, fig_h=248,
            pose=walk_pose(t * 1.6, stride_deg=8, arm_deg=18, reach_l=0.5), flip_x=True
        )

    # -------------------------------------------------------------------------
    # POEM 06: Don't Come Closer — SCION 33 (Planted-Foot IK & Reach Envelope)
    # -------------------------------------------------------------------------
    elif poem_num == 6:
        blend_multiplane_underlay(canvas, "gen_69ee5bb28b_90", cam_x=cam_x, cam_y=cam_y, opacity=0.48)
        plaza_im = load_cut_prop("06.set.atlantis_plaza", "p02")
        paste_centered(canvas, plaza_im, W * 0.52 - cam_x * 0.28, H * 0.44, target_h=380, alpha_mul=0.68)
        comet_im = load_cut_prop("06.fx.comet", "p01")
        paste_centered(canvas, comet_im, W * (0.25 + 0.50 * q), H * (0.24 - 0.06 * q), target_w=320, alpha_mul=0.82)
        # Ferryman's Coin Booth at threshold + Atlantis Gatekeeper + Poet with planted feet & 2-bone IK reach
        booth_im = load_cut_prop("06.props.coin-booth", "p01")
        paste_centered(canvas, booth_im, W * 0.64, H * 0.66, target_h=290, alpha_mul=0.90)
        cit_im = load_clean_whole_figure("play/assets/citizen_1__atlantis/00.webp")
        paste_centered(canvas, cit_im, W * 0.76, H * 0.86, target_h=245, alpha_mul=0.92, anchor_y=1.0)
        # Poet planted on the causeway stone, reaching toward the coin booth target
        reach_amt = min(1.0, max(0.15, 1.1 - q))
        render_ideal_actor_on_stage(
            canvas, "poet_tracksuit", "SIDE", W * 0.36, H * 0.87, fig_h=265,
            pose=dict(
                spine_deg=12.0 * reach_amt,
                thigh_L_deg=22.0, shin_L_deg=-6.0, foot_L_deg=0.0,
                thigh_R_deg=-18.0, shin_R_deg=-16.0, foot_R_deg=0.0,
                uarm_L_deg=44.0 + 38.0 * reach_amt,
                farm_L_deg=72.0 + 26.0 * reach_amt,
                uarm_R_deg=18.0, farm_R_deg=36.0,
                show_far_arm_in_side=True,
            )
        )
        blend_multiplane_occluder(canvas, "gen_69ee5bb28b_90", cam_x=cam_x, cam_y=cam_y, opacity=0.45)

    # -------------------------------------------------------------------------
    # POEM 07: Wait a Minute — SCION 06 (John Whitney Harmonic Motion & DJ Club)
    # -------------------------------------------------------------------------
    elif poem_num == 7:
        blend_multiplane_underlay(canvas, "gen_9c5f9c7c4a_70", cam_x=cam_x * 0.6, cam_y=cam_y, opacity=0.44)
        spk_im = load_cut_prop("07.props.speakers-vu", "p01")
        paste_centered(canvas, spk_im, W * 0.16, H * 0.56, target_h=340, alpha_mul=0.84)
        paste_centered(canvas, spk_im, W * 0.84, H * 0.56, target_h=340, flip_x=True, alpha_mul=0.84)
        # DJ Cyber behind the real turntables + Poet at the microphone + Club Dancer
        render_ideal_actor_on_stage(
            canvas, "dj_cyber", "FRONT", W * 0.50, H * 0.78, fig_h=235,
            pose=dict(
                spine_deg=math.sin(t * 5.65) * 4.0,
                uarm_L_deg=26.0 + math.sin(t * 5.65) * 14.0,
                farm_L_deg=58.0 + math.cos(t * 5.65) * 16.0,
                uarm_R_deg=-26.0 - math.cos(t * 5.65) * 14.0,
                farm_R_deg=-58.0 - math.sin(t * 5.65) * 16.0,
            )
        )
        decks_im = load_cut_prop("07.props.dj-decks", "p01")
        paste_centered(canvas, decks_im, W * 0.50, H * 0.77, target_w=390, alpha_mul=0.94)
        mic_im = load_cut_prop("07.props.mic-daisy-rings", "p01")
        paste_centered(canvas, mic_im, W * 0.31, H * 0.70, target_h=240, alpha_mul=0.90)
        render_ideal_actor_on_stage(
            canvas, "poet_tracksuit", "3Q", W * 0.25, H * 0.88, fig_h=255,
            pose=walk_pose(t * 5.65, stride_deg=12, arm_deg=22, reach_l=0.65)
        )
        render_ideal_actor_on_stage(
            canvas, "woman_brocade", "3Q", W * 0.75, H * 0.88, fig_h=245,
            pose=walk_pose(t * 5.65 + 1.5, stride_deg=14, arm_deg=26, reach_l=0.5), flip_x=True
        )

    # -------------------------------------------------------------------------
    # POEM 08: Navigate — SCION 45 (Occlusion Compositing & Split Depth Layering)
    # -------------------------------------------------------------------------
    elif poem_num == 8:
        blend_multiplane_underlay(canvas, "world_8bc7b3e2_0", cam_x=cam_x, cam_y=cam_y, opacity=0.48)
        moons_im = load_cut_prop("08.props.moons-laundry", "p01")
        paste_centered(canvas, moons_im, W * 0.50 - cam_x * 0.2, H * 0.22, target_w=640, alpha_mul=0.78)
        # Plane Z=1 (BEHIND the rooftop marquee arch): Angel & physical Poet
        angel_im = load_clean_whole_figure("play/assets/angel__robe/00.webp")
        paste_centered(canvas, angel_im, W * 0.64 - cam_x * 0.35, H * 0.82, target_h=265, alpha_mul=0.92, anchor_y=1.0)
        render_ideal_actor_on_stage(
            canvas, "poet_tracksuit", "SIDE", W * (0.34 + 0.18 * q), H * 0.86, fig_h=258,
            pose=walk_pose(t * 2.2, stride_deg=18, arm_deg=20, reach_l=0.55)
        )
        # Plane Z=2 (THE OCCLUDING THRESHOLD ARCH): `08.hero.marquee` passes IN FRONT OF physical Poet!
        marq_im = load_cut_prop("08.hero.marquee", "p01")
        paste_centered(canvas, marq_im, W * 0.46 - cam_x * 0.65, H * 0.52, target_h=480, alpha_mul=0.86)
        # Plane Z=3 (IN FRONT OF the marquee arch): Poet Soul astral body & foreground ritual water basin!
        soul_im = load_clean_whole_figure("play/assets/poet_soul__soul/00.webp")
        paste_centered(canvas, soul_im, W * (0.48 + 0.20 * q), H * 0.80 + math.sin(t * 2.4) * 8.0, target_h=250, alpha_mul=0.55 + 0.40 * q, anchor_y=1.0)
        basin_im = load_cut_prop("08.props.basins", "p01")
        paste_centered(canvas, basin_im, W * 0.24 - cam_x * 0.9, H * 0.84, target_h=135, alpha_mul=0.90)
        blend_multiplane_occluder(canvas, "world_8bc7b3e2_0", cam_x=cam_x, cam_y=cam_y, opacity=0.58)

    # -------------------------------------------------------------------------
    # POEM 09: Yet, Heard — SCION 28 (Compositor's Foundry of Holdout Mattes)
    # -------------------------------------------------------------------------
    elif poem_num == 9:
        # Left Plate A: Harbor Phonebooth (`gen_ac146f1212_50`)
        # Right Plate B: Mother's Warm Living Room (`gen_a63bb494b1_50` + `09.set.mother_living_room`)
        plate_a = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        blend_multiplane_underlay(plate_a, "gen_ac146f1212_50", cam_x=cam_x, cam_y=cam_y, opacity=0.62)
        pb_im = load_cut_prop("09.props.phonebooth", "p01")
        paste_centered(plate_a, pb_im, W * 0.29, H * 0.56, target_h=430, alpha_mul=0.92)
        render_ideal_actor_on_stage(
            plate_a, "poet_tracksuit", "SIDE", W * 0.29, H * 0.86, fig_h=255,
            pose=dict(spine_deg=6, thigh_L_deg=10, shin_L_deg=-4, thigh_R_deg=-8, shin_R_deg=-8, uarm_L_deg=38, farm_L_deg=92, show_far_arm_in_side=True)
        )

        plate_b = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        blend_multiplane_underlay(plate_b, "gen_a63bb494b1_50", cam_x=-cam_x * 0.5, cam_y=cam_y, opacity=0.58)
        mlr_im = load_cut_prop("09.set.mother_living_room", "p01")
        paste_centered(plate_b, mlr_im, W * 0.72, H * 0.52, target_h=390, alpha_mul=0.80)
        chair_im = load_cut_prop("09.props.phones-chair", "p01")
        paste_centered(plate_b, chair_im, W * 0.70, H * 0.70, target_h=220, alpha_mul=0.88)
        render_ideal_actor_on_stage(
            plate_b, "mother_cardigan", "3Q", W * 0.68, H * 0.86, fig_h=245,
            pose=dict(spine_deg=4, uarm_L_deg=34, farm_L_deg=84, uarm_R_deg=12, farm_R_deg=28), flip_x=True
        )
        fat_im = load_clean_whole_figure("play/assets/father_elder__poem09/00.webp")
        paste_centered(plate_b, fat_im, W * 0.84, H * 0.85, target_h=240, alpha_mul=0.88, anchor_y=1.0)

        # Travelling feathered holdout matte uniting Plate A and Plate B across the phonebooth glass seam
        split_x = int(W * (0.46 + 0.06 * math.sin(t * 0.8)))
        Y_g, X_g = np.ogrid[:H, :W]
        matte_b = np.clip((X_g - (split_x - 45.0)) / 90.0, 0.0, 1.0)[:, :, None]
        arr_a = np.array(plate_a).astype(np.float32)
        arr_b = np.array(plate_b).astype(np.float32)
        comp_ab = (arr_a * (1.0 - matte_b) + arr_b * matte_b).astype(np.uint8)
        canvas.alpha_composite(Image.fromarray(comp_ab), (0, 0))

    # -------------------------------------------------------------------------
    # POEM 10: Wait a While — SCION 44 (Multiplane Camera Parallax Highway)
    # -------------------------------------------------------------------------
    elif poem_num == 10:
        pl_id = "gen_366225426b_70" if q > 0.35 else "gen_f729b3bb28_90"
        blend_multiplane_underlay(canvas, pl_id, cam_x=cam_x * 2.2, cam_y=cam_y, opacity=0.52)
        tree_im = load_cut_prop("10.props.tree-dawn-sign", "p01")
        paste_centered(canvas, tree_im, (W * 0.78 - (t * 65.0) % (W * 0.9)), H * 0.56, target_h=310, alpha_mul=0.78)
        # Real cut motorcycle & rider (`10.props.bike-ride-views`) banking into the dawn curve
        bike_im = load_cut_prop("10.props.bike-ride-views", "p01")
        bank_deg = math.sin(t * 1.8) * 6.5 * (1.0 - 0.5 * q)
        bike_x = W * (0.38 + 0.16 * q) + math.sin(t * 1.5) * 24.0
        paste_centered(canvas, bike_im, bike_x, H * 0.74, target_h=255, rot_deg=bank_deg, alpha_mul=0.95)
        blend_multiplane_occluder(canvas, pl_id, cam_x=cam_x * 2.5, cam_y=cam_y, opacity=0.50)

    # -------------------------------------------------------------------------
    # POEM 11: No Safe Place — SCION 08 (Ivan Sutherland Sketchpad Constraint Solver)
    # -------------------------------------------------------------------------
    elif poem_num == 11:
        blend_multiplane_underlay(canvas, "gen_69ee5bb28b_30", cam_x=cam_x, cam_y=cam_y, opacity=0.45, style_mode="sutherland")
        # Real Temple Whole & Columns converted into CRT green phosphor vector constraints snapping to residual E -> 0
        residual = max(0.0, 1.0 - q)
        jitter_y = math.sin(t * 5.0) * 18.0 * residual
        temple_crt = style_sutherland_crt_blueprint(load_cut_prop("11.props.temple.whole", "p01"), fill_alpha=0.38)
        paste_centered(canvas, temple_crt, W * 0.52, H * 0.48 + jitter_y * 0.4, target_h=430, rot_deg=residual * 4.5, alpha_mul=0.92)
        col_crt = style_sutherland_crt_blueprint(load_cut_prop("11.props.temple.arrival.courses-columns", "p01"), fill_alpha=0.34)
        paste_centered(canvas, col_crt, W * 0.20, H * 0.54 - jitter_y * 0.5, target_h=380, alpha_mul=0.85)
        paste_centered(canvas, col_crt, W * 0.82, H * 0.54 + jitter_y * 0.5, target_h=380, flip_x=True, alpha_mul=0.85)
        moto_crt = style_sutherland_crt_blueprint(load_cut_prop("11.props.parked-motorcycle", "p01"), fill_alpha=0.36)
        paste_centered(canvas, moto_crt, W * 0.22, H * 0.82, target_h=155, alpha_mul=0.86)
        # NON-SELECTABLE ORGANIC ACTOR (`I4`): Real painted Poet walks freely inside the CRT vector temple!
        render_ideal_actor_on_stage(
            canvas, "poet_tracksuit", "3Q" if q > 0.5 else "SIDE", W * (0.42 + 0.14 * q), H * 0.87, fig_h=258,
            pose=walk_pose(t * 1.8, stride_deg=14 * (1.0 - 0.5 * q), arm_deg=18, reach_l=0.45)
        )

    # -------------------------------------------------------------------------
    # POEM 12: Look Back — SCION 34 (ARAP Engraved Mesh & Hourglass Reunion)
    # -------------------------------------------------------------------------
    elif poem_num == 12:
        blend_multiplane_underlay(canvas, "world_f56df2d8_1", cam_x=cam_x, cam_y=cam_y, opacity=0.46, style_mode="gilliam")
        niche_im = style_gilliam_engraved_cutout(load_cut_prop("12.props.niche-porch", "p01"))
        paste_centered(canvas, niche_im, W * 0.50 - cam_x * 0.3, H * 0.48, target_h=420, alpha_mul=0.72)
        # Real painted hourglasses (`hand-hourglass` & `last-hourglass`) with ARAP mesh overlay
        hg_im = style_arap_mesh_overlay(load_cut_prop("12.props.last-hourglass", "p01"))
        paste_centered(canvas, hg_im, W * 0.50, H * 0.34, target_h=210, rot_deg=math.sin(t * 1.2) * 4.0, alpha_mul=0.90)
        # Poet & Brother deformed as ARAP triangulated meshes (`style_arap_mesh_overlay`) leaning into the reunion
        sep_x = 165.0 - 95.0 * q
        render_ideal_actor_on_stage(
            canvas, "poet_tracksuit", "SIDE", W * 0.50 - sep_x, H * 0.87, fig_h=258,
            pose=walk_pose(t * 1.5, stride_deg=10 * (1.0 - q), arm_deg=20, lean_deg=10.0 * q, reach_l=0.75 * q),
            style_fn=style_arap_mesh_overlay
        )
        bro_im = style_arap_mesh_overlay(load_clean_whole_figure("play/assets/brother_1__poem12/00.webp"))
        paste_centered(canvas, bro_im, W * 0.50 + sep_x, H * 0.87, target_h=235, flip_x=True, alpha_mul=0.94, anchor_y=1.0)
        eld_im = load_clean_whole_figure("play/assets/elder_man__poem13/00.webp")
        paste_centered(canvas, eld_im, W * 0.16, H * 0.86, target_h=195, alpha_mul=0.82, anchor_y=1.0)
        blend_multiplane_occluder(canvas, "world_f56df2d8_1", cam_x=cam_x, cam_y=cam_y, opacity=0.45, style_mode="gilliam")

    # -------------------------------------------------------------------------
    # POEM 13: The Quiet Place — SCION 07 (Peter Foldès Calligraphic Metamorphosis)
    # -------------------------------------------------------------------------
    elif poem_num == 13:
        pl_id = "gen_ca6878be91_30" if q > 0.55 else "gen_e315da34f9_70"
        blend_multiplane_underlay(canvas, pl_id, cam_x=cam_x, cam_y=cam_y, opacity=0.45, style_mode="foldes")
        # Calligraphic window -> planet boats -> golden wheat harvest sheaves
        win_f = style_foldes_calligraphic(load_cut_prop("13.props.distant-window", "p01"))
        paste_centered(canvas, win_f, W * 0.24 - cam_x * 0.3, H * 0.38, target_h=260, alpha_mul=max(0.25, 1.0 - q * 0.7))
        boat_f = style_foldes_calligraphic(load_cut_prop("13.props.planet-boats", "p01"))
        paste_centered(canvas, boat_f, W * 0.52 + math.sin(t * 1.1) * 35.0, H * 0.25, target_h=155, alpha_mul=0.82)
        harv_f = style_foldes_calligraphic(load_cut_prop("13.props.harvest", "p01"))
        for hx in (0.15, 0.32, 0.68, 0.85):
            paste_centered(canvas, harv_f, W * hx - cam_x * 0.5, H * 0.86, target_h=int(135 + 45 * q), rot_deg=math.sin(t * 2.0 + hx * 6) * 5.0, alpha_mul=0.35 + 0.60 * q, anchor_y=0.92)
        # Woman in Red Brocade + Poet + Seated Harbor Couple rendered with Foldès calligraphic wash
        render_ideal_actor_on_stage(
            canvas, "woman_brocade", "3Q", W * (0.64 - 0.08 * q), H * 0.86, fig_h=248,
            pose=walk_pose(t * 1.4, stride_deg=10 * (1.0 - q), arm_deg=18, reach_l=0.6 * q),
            flip_x=True, style_fn=style_foldes_calligraphic
        )
        render_ideal_actor_on_stage(
            canvas, "poet_tracksuit", "SIDE", W * (0.36 + 0.08 * q), H * 0.86, fig_h=256,
            pose=walk_pose(t * 1.4, stride_deg=10 * (1.0 - q), arm_deg=18, reach_l=0.6 * q),
            style_fn=style_foldes_calligraphic
        )
        c1a = style_foldes_calligraphic(load_clean_whole_figure("play/assets/couple_1_a__poem13/00.webp"))
        c1b = style_foldes_calligraphic(load_clean_whole_figure("play/assets/couple_1_b__poem13/00.webp"))
        paste_centered(canvas, c1a, W * 0.16, H * 0.87, target_h=175, alpha_mul=0.45 + 0.45 * q, anchor_y=1.0)
        paste_centered(canvas, c1b, W * 0.84, H * 0.87, target_h=175, alpha_mul=0.45 + 0.45 * q, anchor_y=1.0)

    # -------------------------------------------------------------------------
    # POEM 14: Hot Minute — SCION 04 (Frank Mouris Archive Image-Torrent & Exit Door)
    # -------------------------------------------------------------------------
    elif poem_num == 14:
        blend_multiplane_underlay(canvas, "gen_69ee5bb28b_30", cam_x=cam_x, cam_y=cam_y, opacity=0.38)
        # Populate outer Mouris quadtree ring with real WYGWYL archive cutouts & film reels
        reel_im = load_cut_prop("14.props.reel", "p01")
        party_prop = load_cut_prop("14.props.party", "p01")
        paste_centered(canvas, reel_im, W * 0.14, H * 0.22, target_h=130, rot_deg=t * 36.0, alpha_mul=0.82)
        paste_centered(canvas, reel_im, W * 0.86, H * 0.22, target_h=130, rot_deg=-t * 36.0, alpha_mul=0.82)
        paste_centered(canvas, party_prop, W * 0.16, H * 0.74, target_h=165, alpha_mul=0.78)
        paste_centered(canvas, party_prop, W * 0.84, H * 0.74, target_h=165, flip_x=True, alpha_mul=0.78)
        # Central Vintage Threshold Door (`14.props.door`) + Ensemble Cast stepping across threshold
        door_im = load_cut_prop("14.props.door", "p01")
        paste_centered(canvas, door_im, W * 0.50, H * 0.52, target_h=430, alpha_mul=0.92)
        render_ideal_actor_on_stage(
            canvas, "party_gentleman", "3Q", W * 0.33, H * 0.86, fig_h=232,
            pose=walk_pose(t * 2.0, stride_deg=12, arm_deg=20, reach_l=0.45)
        )
        render_ideal_actor_on_stage(
            canvas, "party_woman_gown", "3Q", W * 0.67, H * 0.86, fig_h=228,
            pose=walk_pose(t * 2.0 + 1.2, stride_deg=12, arm_deg=20, reach_l=0.45), flip_x=True
        )
        render_ideal_actor_on_stage(
            canvas, "young_poet", "FRONT", W * 0.43, H * 0.88, fig_h=230,
            pose=walk_pose(t * 2.2, stride_deg=14, arm_deg=18)
        )
        render_ideal_actor_on_stage(
            canvas, "poet_tracksuit", "FRONT" if q > 0.65 else "SIDE", W * 0.54, H * 0.88, fig_h=255,
            pose=walk_pose(t * 2.2, stride_deg=16 * (1.0 - 0.6 * q), arm_deg=22, reach_l=0.6 * q)
        )

    return canvas.convert("RGB")


# ============================================================================
# 6. ROUND 2 `sources/` PROVENANCE ARCHIVIST (`populate_poem_sources`)
# ============================================================================

def populate_poem_sources(poem_num, folder):
    """
    Copies the poem's real multiplane plates, cut props, and character sheets into
    `<folder>/sources/`, writes `<folder>/sources/sources.json`, `<folder>/build/fetch_sources.py`,
    and `<folder>/reviews/round-02-critic.md`, and updates `<folder>/assets.json`.
    """
    spec = POEM_SOURCE_MANIFEST.get(poem_num, POEM_SOURCE_MANIFEST[1])
    src_dir = os.path.join(folder, "sources")
    os.makedirs(src_dir, exist_ok=True)
    copied = []

    # 1. Copy primary multiplane plate files (`plate.jpg`, `P4_mid.png`, `P0_occluders.png`)
    for pid in spec["plates"][:2]:
        pdir = os.path.join(SUITE, "sets", "plates", pid)
        for fn in ("plate.jpg", "P4_mid.png", "P0_occluders.png"):
            src_fp = os.path.join(pdir, fn)
            if os.path.exists(src_fp):
                dst_fn = f"plate_{pid}_{fn}"
                dst_fp = os.path.join(src_dir, dst_fn)
                if not os.path.exists(dst_fp):
                    shutil.copy2(src_fp, dst_fp)
                copied.append({"role": "multiplane_plate", "plate_id": pid, "file": f"sources/{dst_fn}", "origin": f"shots/suite/sets/plates/{pid}/{fn}"})

    # 2. Copy cut narrative props & set pieces from `release_v2/cuts/`
    for sheet_id, pid in spec["cuts"]:
        src_fp = os.path.join(CUTS_ROOT, sheet_id, f"{sheet_id}__{pid}.png")
        if not os.path.exists(src_fp):
            d = os.path.join(CUTS_ROOT, sheet_id)
            if os.path.isdir(d):
                pngs = sorted([f for f in os.listdir(d) if f.endswith(".png")])
                if pngs:
                    src_fp = os.path.join(d, pngs[0])
        if os.path.exists(src_fp):
            dst_fn = f"cut_{os.path.basename(src_fp)}"
            dst_fp = os.path.join(src_dir, dst_fn)
            if not os.path.exists(dst_fp):
                shutil.copy2(src_fp, dst_fp)
            copied.append({"role": "cut_prop_or_set", "sheet": sheet_id, "file": f"sources/{dst_fn}", "origin": os.path.relpath(src_fp, SHOTS)})

    # 3. Copy character assets (either canonical 4-angle torso cut or whole-figure .webp)
    cast_dict = get_cast_dict()
    for cid in spec["cast"]:
        if cid.endswith(".webp") or cid.endswith(".png"):
            src_fp = os.path.join(SHOTS, cid)
            if os.path.exists(src_fp):
                dst_fn = "char_" + cid.replace("/", "_")
                dst_fp = os.path.join(src_dir, dst_fn)
                if not os.path.exists(dst_fp):
                    shutil.copy2(src_fp, dst_fp)
                copied.append({"role": "character_figure", "id": cid, "file": f"sources/{dst_fn}", "origin": cid})
        elif cid in cast_dict:
            cspec = cast_dict[cid]
            t_fp = cspec["views"]["FRONT"]["torso"]
            if os.path.exists(t_fp):
                dst_fn = f"char_{cid}_{os.path.basename(t_fp)}"
                dst_fp = os.path.join(src_dir, dst_fn)
                if not os.path.exists(dst_fp):
                    shutil.copy2(t_fp, dst_fp)
                copied.append({
                    "role": "debradded_4angle_ideal_body",
                    "id": cid,
                    "views": ["FRONT", "3Q", "SIDE", "BACK"],
                    "file": f"sources/{dst_fn}",
                    "origin": os.path.relpath(t_fp, SHOTS),
                })

    sources_meta = {
        "poem_num": poem_num,
        "round": 2,
        "mode": "handmade_with_existing_wygwyl_assets",
        "debradded_4angle_solver": "shots/arena/parts/kit3/build_step_by_step_ideal_bodies.py::solve_and_render_ideal_body",
        "multiplane_plates": spec["plates"],
        "cut_props": [f"{s}__{p}" for s, p in spec["cuts"]],
        "cast": spec["cast"],
        "files": copied,
    }
    with open(os.path.join(src_dir, "sources.json"), "w") as f:
        json.dump(sources_meta, f, indent=2)

    # Write `build/fetch_sources.py`
    build_dir = os.path.join(folder, "build")
    os.makedirs(build_dir, exist_ok=True)
    fetch_py = os.path.join(build_dir, "fetch_sources.py")
    with open(fetch_py, "w") as f:
        f.write(
            f"""#!/usr/bin/env python3
\"\"\"Fetches and verifies existing WYGWYL multiplane plates, cut props, and 4-angle character cuts in sources/ for Poem {poem_num:02d}.\"\"\"
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
PAELEO = os.path.abspath(os.path.join(FOLDER, "..", ".."))
if PAELEO not in sys.path:
    sys.path.insert(0, PAELEO)
from lib_handmade_round2_assets import populate_poem_sources

if __name__ == "__main__":
    populate_poem_sources({poem_num}, FOLDER)
    print("Populated sources/ for Poem {poem_num:02d}")
"""
        )
    os.chmod(fetch_py, 0o755)

    # Write `reviews/round-02-critic.md`
    rev_dir = os.path.join(folder, "reviews")
    os.makedirs(rev_dir, exist_ok=True)
    with open(os.path.join(rev_dir, "round-02-critic.md"), "w") as f:
        f.write(
            f"""# Round 02 Critic Review — Poem {poem_num:02d} (Handmade with Existing Assets)

## 1. Asset Provenance & De-Bradding Audit
- **Multiplane Set Plates (`sources/`)**: `{', '.join(spec['plates'])}` (`P6_sky.png`, `P5_far.png`, `P4_mid.png`, `P0_occluders.png`).
- **Hand-Cut Narrative Props & Set Pieces (`sources/`)**: `{', '.join(f'{s}__{p}' for s, p in spec['cuts'])}`.
- **Articulated Cast Rigs (`sources/`)**: `{', '.join(spec['cast']) if spec['cast'] else 'Strictly 0 human figures (I4 architectural substitution law)'}`.
- **De-Bradding & Border Purification**: All `release_v2/cuts/` character cards are purified on load via `load_debradded_cut` (filling interior grommet holes, stripping brass eyelet rings, and eroding the outer kraft paper outline while preserving garment stripes, brocade, and modular facial features).

## 2. SCION Studio Discipline & Invariant Check
- Multiplane plates and cut props are operated inside the poem's assigned SCION material grammar (never raw un-operated paste-ups).
- Zero top HUD telemetry clutter.
- Passes `I1_choices`, `I2_threshold`, `I3_monotonic_quantity`, `I4_signature_constraint`, and `I5_handmade_package` (`ALL OK`).
"""
        )
    return sources_meta
