#!/usr/bin/env python3
"""
100x Multi-Character Pose & Parametric Face Engine (`build_100x_pose_face_library.py`)
Scales the WYGWYL visual-first cut-out character & face assembly pipeline 100x:
  1. Generates 108 Assembled Faces (`faces_100x/`) across 9 cast groups, front/3Q/profile/back views,
     brow states, eye states, sunglasses states, and phoneme/emotional mouths with luminance-preserving
     skin-tone matching and zero two-tone patches.
  2. Generates 120 Assembled Multi-Character Poses (`poses_100x/`) across 10 distinct character rigs
     × 12 canonical acting/locomotion poses using rectified medial-axis bone sockets, width-normalized
     girth compensation, cuff-tucks, and true anatomical proportions (7.5H adult vs 5.2H child).
  3. Renders high-resolution visual contact sheets (`scratch_100x_faces_atlas.png` and
     `scratch_100x_characters_poses_atlas.png`) and exports `faces_100x_catalog.json` + `poses_100x_catalog.json`.
"""

import os
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance
from scipy.ndimage import binary_erosion, binary_dilation, binary_fill_holes, gaussian_filter, label

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
REL_DIR = os.path.join(ROOT, "shots/arena/parts/kit3/release_v2")
FACES_OUT = os.path.join(REL_DIR, "faces_100x")
POSES_OUT = os.path.join(REL_DIR, "poses_100x")
ART_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"

os.makedirs(FACES_OUT, exist_ok=True)
os.makedirs(POSES_OUT, exist_ok=True)

TS_DIR = os.path.join(ROOT, "shots/kits/packs/poet_tracksuit_v1/01_COMPONENTS")
TS_PROF_DIR = os.path.join(TS_DIR, "profile_face_clean")
YP_PROF_DIR = os.path.join(ROOT, "shots/kits/packs/young_poet_v1/01_COMPONENTS/profile_face_clean")
V2_PARTS = os.path.join(ROOT, "shots/arena/parts/kit3/v2/parts")
V2_CUT = os.path.join(ROOT, "shots/arena/parts/kit3/v2/cut")
WM_HEADS = os.path.join(ROOT, "shots/weave/cast/man/library/head")
BL_HEADS = os.path.join(ROOT, "shots/arena/parts/body_lab/heads")

# Import calibrated Poet pose engine helpers so Poet rigs use the exact verified solver
import sys
sys.path.insert(0, os.path.join(ROOT, "shots/arena/parts/kit3"))
import build_poem09_37_characters as p09


# ============================================================================
# PART 1: 100x PARAMETRIC & MULTI-CAST FACE ENGINE (108 FACES)
# ============================================================================

def feather_part(path, erode_px=36, blur_sigma=7.0, clip_temple_tabs=False):
    im = Image.open(path).convert("RGBA")
    arr = np.array(im, dtype=np.float32)
    H, W = arr.shape[:2]
    if clip_temple_tabs:
        arr[:, :int(W * 0.115), 3] = 0
        arr[:, int(W * 0.885):, 3] = 0
    fg = arr[:, :, 3] > 20
    if erode_px > 0:
        inner = binary_erosion(fg, iterations=erode_px)
    else:
        inner = fg
    if blur_sigma > 0:
        soft_a = gaussian_filter(inner.astype(np.float32), sigma=blur_sigma)
        arr[:, :, 3] = np.clip(soft_a * 255.0, 0, 255)
    u8 = arr.astype(np.uint8)
    ys, xs = np.where(u8[:, :, 3] > 8)
    if len(xs) == 0:
        return im
    return Image.fromarray(u8[ys.min():ys.max() + 1, xs.min():xs.max() + 1])


def blend_profile_part(path, target_skin_rgb, erode_px=10, blur_sigma=4.5):
    """
    Cleans outer kraft border, color-matches skin pixels to `target_skin_rgb` while preserving
    local shading, and applies radial + feature-boost feathering so there is zero two-tone patch.
    """
    im = Image.open(path).convert("RGBA")
    u8 = np.array(im, dtype=np.uint8)
    p09.defringe_white_halo(u8, radius=3)
    p09.strip_outer_kraft_margin(u8, max_px=12)
    arr = u8.astype(np.float32)
    fg = arr[:, :, 3] > 20
    ys, xs = np.where(fg)
    if len(xs) == 0:
        return im
    arr = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    H, W = arr.shape[:2]
    fg = arr[:, :, 3] > 20

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    skin_mask = fg & (lum > 60) & (lum < 220) & ((r - b) > 22) & (g > 38)
    if np.any(skin_mask):
        med_rgb = np.median(arr[skin_mask][:, :3], axis=0)
        weight = gaussian_filter(skin_mask.astype(np.float32), sigma=3.0)
        for c in range(3):
            delta = target_skin_rgb[c] - med_rgb[c]
            arr[:, :, c] = np.clip(arr[:, :, c] + delta * weight, 0, 255)

    inner = binary_erosion(fg, iterations=erode_px) if erode_px > 0 else fg
    soft_a = gaussian_filter(inner.astype(np.float32), sigma=blur_sigma)
    yy, xx = np.ogrid[:H, :W]
    rx = (xx - W * 0.52) / (W * 0.48)
    ry = (yy - H * 0.50) / (H * 0.50)
    radial = np.clip(1.0 - (rx * rx + ry * ry), 0.0, 1.0)
    is_feature = (lum < 72) | (lum > 195) | ((r - g) > 58)
    feat_boost = gaussian_filter(is_feature.astype(np.float32), sigma=2.5)
    alpha_mult = np.clip(radial * 0.85 + feat_boost * 0.95, 0.0, 1.0)
    arr[:, :, 3] = np.clip(soft_a * alpha_mult * 255.0, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def blend_ghost_part(path, target_rgb=(181.0, 177.0, 169.0), erode_px=4, blur_sigma=3.0):
    """
    Strips warm brown/kraft borders from Ghost Child feature cards and color-matches
    the surround skin to `ghost_head_01.png` spectral grey-blue.
    """
    im = Image.open(path).convert("RGBA")
    u8 = np.array(im, dtype=np.uint8)
    p09.defringe_white_halo(u8, radius=3)
    p09.strip_outer_kraft_margin(u8, max_px=12)
    arr = u8.astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    warm_kraft = (r - b) > 9
    arr[warm_kraft, 3] = 0
    fg = arr[:, :, 3] > 20
    ys, xs = np.where(fg)
    if len(xs) == 0:
        return im
    arr = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    H, W = arr.shape[:2]
    fg = arr[:, :, 3] > 20
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    skin_mask = fg & (lum > 95) & (lum < 210)
    if np.any(skin_mask):
        med = np.median(arr[skin_mask][:, :3], axis=0)
        w = gaussian_filter(skin_mask.astype(np.float32), sigma=3.0)
        for c in range(3):
            arr[:, :, c] = np.clip(arr[:, :, c] + (target_rgb[c] - med[c]) * w, 0, 255)
    inner = binary_erosion(fg, iterations=erode_px) if erode_px > 0 else fg
    soft_a = gaussian_filter(inner.astype(np.float32), sigma=blur_sigma)
    is_feat = (lum < 105) | (lum > 210)
    feat_boost = gaussian_filter(is_feat.astype(np.float32), sigma=2.5)
    yy, xx = np.ogrid[:H, :W]
    rx = (xx - W * 0.5) / (W * 0.5)
    ry = (yy - H * 0.5) / (H * 0.5)
    radial = np.clip(1.0 - (rx * rx + ry * ry), 0.0, 1.0)
    arr[:, :, 3] = np.clip(soft_a * np.clip(radial * 0.78 + feat_boost * 1.0, 0.0, 1.0) * 255.0, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def fit_on_card(im, cw=220, ch=260, pad=14):
    """Centers an RGBA head image cleanly inside a uniform (cw, ch) card."""
    arr = np.array(im)
    ys, xs = np.where(arr[:, :, 3] > 16)
    if len(xs) == 0:
        return Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    crop = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    avail_w = cw - pad * 2
    avail_h = ch - pad * 2
    scale = min(avail_w / crop.width, avail_h / crop.height)
    nw = max(1, int(round(crop.width * scale)))
    nh = max(1, int(round(crop.height * scale)))
    resized = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    card.alpha_composite(resized, ((cw - nw) // 2, (ch - nh) // 2))
    return card


def build_poet_front_face(brows="rest", eyes="sunglasses", mouth="rest", tilt_deg=0.0):
    hb = Image.open(os.path.join(TS_DIR, "21_head_front_blank.png")).convert("RGBA")
    arr = np.array(hb)
    p09.defringe_white_halo(arr, radius=3)
    H, W = arr.shape[:2]
    # Fill chin-beard bridge so open/smiling mouths connect seamlessly to the beard
    yy, xx = np.ogrid[:H, :W]
    chin_patch = (yy > int(H * 0.58)) & (yy < int(H * 0.73)) & (np.abs(xx - W * 0.50) < W * 0.14) & (arr[:, :, 3] > 200)
    arr[chin_patch, 0] = 28
    arr[chin_patch, 1] = 24
    arr[chin_patch, 2] = 22
    base = Image.fromarray(arr).resize((220, 260), Image.Resampling.LANCZOS)
    cx = 110

    b_file = "25_brows_raised.png" if brows == "raised" else "24_brows_rest.png"
    b_im = feather_part(os.path.join(TS_DIR, b_file), erode_px=42, blur_sigma=8.0).resize((104, 27), Image.Resampling.LANCZOS)
    base.alpha_composite(b_im, (cx - 52, 62 if brows == "raised" else 67))

    e_file = "23_eyes_closed.png" if eyes == "closed" else "22_eyes_open.png"
    e_im = feather_part(os.path.join(TS_DIR, e_file), erode_px=44, blur_sigma=8.0).resize((98, 31), Image.Resampling.LANCZOS)
    base.alpha_composite(e_im, (cx - 49, 86))

    n_im = feather_part(os.path.join(TS_DIR, "26_nose_front.png"), erode_px=42, blur_sigma=9.0).resize((38, 43), Image.Resampling.LANCZOS)
    base.alpha_composite(n_im, (cx - 19, 102))

    if eyes == "sunglasses":
        g_im = feather_part(os.path.join(TS_DIR, "31_sunglasses_front.png"), erode_px=22, blur_sigma=2.5, clip_temple_tabs=True).resize((126, 36), Image.Resampling.LANCZOS)
        base.alpha_composite(g_im, (cx - 63, 82))

    m_map = {
        "rest": ("27_mouth_rest.png", (74, 34), 140),
        "smile": ("28_mouth_smile.png", (72, 32), 141),
        "open_O": ("29_mouth_open_O.png", (74, 42), 137),
        "open_A": ("30_mouth_open_A.png", (76, 45), 136),
    }
    mf, msz, my = m_map[mouth]
    m_im = feather_part(os.path.join(TS_DIR, mf), erode_px=38, blur_sigma=6.0).resize(msz, Image.Resampling.LANCZOS)
    base.alpha_composite(m_im, (cx - msz[0] // 2, my))

    if abs(tilt_deg) > 0.1:
        base = base.rotate(tilt_deg, resample=Image.Resampling.BICUBIC, expand=True)
    return fit_on_card(base)


def build_poet_profile_face(eye_idx=1, brow_idx=9, mouth_file="profile_nose_15.png", with_sunglasses=True):
    """
    Assembles the modular side-profile Poet head using verified visual mappings from `profile_face_clean`:
      - Keeps the largest connected component of `00_base_profile_head.png` (461x542) so the Poet's
        forehead, nose tip (x=458), lips, and beard chin remain 100% intact.
      - Color-matches `sunglasses_09..14.png` (brows), `eyes_01..08.png` (eyes), and `nose_15..20.png` /
        `mouth_21..26.png` (mouths) to the exact Poet cheek skin RGB `[132, 85, 56]`.
    """
    base_full = Image.open(os.path.join(TS_PROF_DIR, "00_base_profile_head.png")).convert("RGBA")
    arr = np.array(base_full)
    labeled, _ = label(arr[:, :, 3] > 20)
    sizes = np.bincount(labeled.ravel())
    sizes[0] = 0
    arr[labeled != sizes.argmax(), 3] = 0
    p09.defringe_white_halo(arr, radius=3)
    base = Image.fromarray(arr)
    target_skin = (132.0, 85.0, 56.0)

    b_im = blend_profile_part(os.path.join(TS_PROF_DIR, f"profile_sunglasses_{brow_idx:02d}.png"), target_skin, erode_px=10, blur_sigma=4.5).resize((92, 36), Image.Resampling.LANCZOS)
    base.alpha_composite(b_im, (318, 174))

    e_im = blend_profile_part(os.path.join(TS_PROF_DIR, f"profile_eyes_{eye_idx:02d}.png"), target_skin, erode_px=10, blur_sigma=4.5).resize((88, 74), Image.Resampling.LANCZOS)
    base.alpha_composite(e_im, (320, 202))

    if with_sunglasses:
        sh_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh_layer)
        # Temple arm resting on ear (192, 212) to front frame (368, 198)
        sd.polygon([(192, 212), (370, 198), (370, 212), (192, 223)], fill=(20, 20, 24, 248), outline=(10, 10, 12, 255))
        sd.polygon([(218, 214), (362, 203), (362, 207), (218, 218)], fill=(195, 38, 38, 238))
        # Side-profile frame & dark crimson lens covering eye socket (356..424, 192..254)
        sd.polygon([(356, 192), (424, 195), (418, 254), (352, 248)], fill=(18, 18, 22, 252), outline=(10, 10, 12, 255))
        sd.polygon([(363, 198), (417, 201), (412, 247), (359, 242)], fill=(48, 18, 20, 246))
        sd.line([(374, 204), (396, 238)], fill=(225, 195, 195, 135), width=3)
        base.alpha_composite(sh_layer)

    m_im = blend_profile_part(os.path.join(TS_PROF_DIR, mouth_file), target_skin, erode_px=10, blur_sigma=4.5).resize((104, 92), Image.Resampling.LANCZOS)
    base.alpha_composite(m_im, (336, 308))
    return fit_on_card(base)


def clean_young_poet_painted_head(path, add_button_nose=True):
    """
    Removes the tiny light-colored dashed cut lines around the eyes/brows/mouth on
    `young_poet.child_clothes/head.front.true.png` and `head.threequarter.true.png`
    and adds a warm gouache child button nose shadow so the face looks completely real.
    """
    im = Image.open(path).convert("RGBA")
    arr = np.array(im, dtype=np.uint8)
    p09.defringe_white_halo(arr, radius=3)
    H, W = arr.shape[:2]
    # Replace light dashed pixels inside the interior face oval (excluding actual eye sclera)
    yy, xx = np.ogrid[:H, :W]
    in_face = (yy > int(H * 0.35)) & (yy < int(H * 0.76)) & (xx > int(W * 0.22)) & (xx < int(W * 0.82))
    # Eye sclera boxes to preserve
    in_sclera = (yy > int(H * 0.45)) & (yy < int(H * 0.525)) & (xx > int(W * 0.30)) & (xx < int(W * 0.74))
    r, g, b = arr[:, :, 0].astype(np.int32), arr[:, :, 1].astype(np.int32), arr[:, :, 2].astype(np.int32)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    dash_mask = in_face & (~in_sclera) & (lum > 156) & ((r - b) < 68)
    blurred = np.zeros_like(arr)
    for c in range(3):
        blurred[:, :, c] = gaussian_filter(arr[:, :, c].astype(np.float32), sigma=3.5).astype(np.uint8)
    arr[dash_mask, :3] = blurred[dash_mask, :3]

    out = Image.fromarray(arr)
    if add_button_nose:
        nd = ImageDraw.Draw(out, "RGBA")
        cx = int(W * 0.50) if "front" in path else int(W * 0.58)
        ny = int(H * 0.56)
        nd.arc([cx - 9, ny - 5, cx + 9, ny + 5], start=15, end=165, fill=(122, 72, 36, 185), width=2)
        nd.ellipse([cx - 6, ny - 4, cx + 6, ny + 1], fill=(198, 138, 84, 95))
    return out


def build_young_poet_face(mode="front_neutral", brow_idx=1, eye_idx=1, mouth_file="young_poet_nose_01.png"):
    if mode == "front_neutral":
        return fit_on_card(clean_young_poet_painted_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.front.true.png"), add_button_nose=True))
    elif mode == "threequarter_neutral":
        return fit_on_card(clean_young_poet_painted_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.threequarter.true.png"), add_button_nose=True))
    elif mode == "profile_painted":
        im = Image.open(os.path.join(V2_PARTS, "young_poet.child_clothes/head.profile.true.png")).convert("RGBA")
        arr = np.array(im)
        p09.defringe_white_halo(arr, radius=3)
        return fit_on_card(Image.fromarray(arr))
    else:
        # Modular Young Poet Profile (`00_young_poet_base_head.png` 279x333)
        base = Image.open(os.path.join(YP_PROF_DIR, "00_young_poet_base_head.png")).convert("RGBA")
        arr = np.array(base)
        p09.defringe_white_halo(arr, radius=3)
        base = Image.fromarray(arr)
        yp_skin = (205.0, 147.0, 90.0)
        b_im = blend_profile_part(os.path.join(YP_PROF_DIR, f"young_poet_acc_{brow_idx:02d}.png"), yp_skin, erode_px=8, blur_sigma=4.0).resize((64, 34), Image.Resampling.LANCZOS)
        base.alpha_composite(b_im, (186, 102))
        e_im = blend_profile_part(os.path.join(YP_PROF_DIR, f"young_poet_eyes_{eye_idx:02d}.png"), yp_skin, erode_px=8, blur_sigma=4.0).resize((74, 80), Image.Resampling.LANCZOS)
        base.alpha_composite(e_im, (190, 124))
        m_im = blend_profile_part(os.path.join(YP_PROF_DIR, mouth_file), yp_skin, erode_px=8, blur_sigma=4.0).resize((72, 54), Image.Resampling.LANCZOS)
        base.alpha_composite(m_im, (192, 192))
        return fit_on_card(base)


def build_ghost_child_face(mode="front", eye_file="ghost_head_04.png", brow_file="ghost_head_08.png", mouth_file="ghost_head_12.png"):
    if mode == "front":
        base = Image.open(os.path.join(BL_HEADS, "ghost_child_age_7/ghost_head_01.png")).convert("RGBA")
        W, H = base.size  # 248x318
        cx = W // 2
        b_im = blend_ghost_part(os.path.join(BL_HEADS, "ghost_child_age_7", brow_file), erode_px=4, blur_sigma=3.0).resize((104, 26), Image.Resampling.LANCZOS)
        base.alpha_composite(b_im, (cx - 52, 98))
        e_im = blend_ghost_part(os.path.join(BL_HEADS, "ghost_child_age_7", eye_file), erode_px=4, blur_sigma=3.0).resize((104, 36), Image.Resampling.LANCZOS)
        base.alpha_composite(e_im, (cx - 52, 122))
        m_im = blend_ghost_part(os.path.join(BL_HEADS, "ghost_child_age_7", mouth_file), erode_px=4, blur_sigma=3.0).resize((62, 26), Image.Resampling.LANCZOS)
        base.alpha_composite(m_im, (cx - 31, 184))
        return fit_on_card(base)
    else:
        base = Image.open(os.path.join(BL_HEADS, "ghost_child_age_7/ghost_head_02.png")).convert("RGBA")
        b_im = blend_ghost_part(os.path.join(BL_HEADS, "ghost_child_age_7", brow_file), erode_px=4, blur_sigma=3.0).resize((62, 26), Image.Resampling.LANCZOS)
        base.alpha_composite(b_im, (152, 98))
        e_im = blend_ghost_part(os.path.join(BL_HEADS, "ghost_child_age_7", eye_file), erode_px=4, blur_sigma=3.0).resize((56, 38), Image.Resampling.LANCZOS)
        base.alpha_composite(e_im, (154, 122))
        m_im = blend_ghost_part(os.path.join(BL_HEADS, "ghost_child_age_7", mouth_file), erode_px=4, blur_sigma=3.0).resize((58, 36), Image.Resampling.LANCZOS)
        base.alpha_composite(m_im, (168, 174))
        return fit_on_card(base)


def generate_108_faces():
    faces_catalog = []

    # 1. Row 1 & 2 (24 Faces): Poet High-Res Front Modular Expressions
    front_combos = [
        ("rest", "sunglasses", "rest", 0, "Poet Shade - Rest"),
        ("rest", "sunglasses", "smile", 0, "Poet Shade - Warm Smile"),
        ("rest", "sunglasses", "open_O", 0, "Poet Shade - Singing O"),
        ("rest", "sunglasses", "open_A", 0, "Poet Shade - Calling A"),
        ("raised", "sunglasses", "rest", 0, "Poet Shade - Alert Brows"),
        ("raised", "sunglasses", "smile", 0, "Poet Shade - Joyful Smile"),
        ("raised", "sunglasses", "open_O", 0, "Poet Shade - Anthem O"),
        ("raised", "sunglasses", "open_A", 0, "Poet Shade - Cheer Laugh"),
        ("raised", "sunglasses", "open_A", -6, "Poet Shade - Tilt L Laugh"),
        ("raised", "sunglasses", "smile", 6, "Poet Shade - Tilt R Smile"),
        ("rest", "sunglasses", "open_O", -5, "Poet Shade - Tilt L Sing"),
        ("rest", "sunglasses", "rest", 5, "Poet Shade - Tilt R Listen"),
        ("rest", "open", "rest", 0, "Poet Unmasked - Calm Gaze"),
        ("rest", "open", "smile", 0, "Poet Unmasked - Gentle Smile"),
        ("rest", "open", "open_O", 0, "Poet Unmasked - Speaking O"),
        ("rest", "open", "open_A", 0, "Poet Unmasked - Exclaim A"),
        ("raised", "open", "rest", 0, "Poet Unmasked - Surprised"),
        ("raised", "open", "smile", 0, "Poet Unmasked - Radiant Grin"),
        ("raised", "open", "open_O", 0, "Poet Unmasked - Belting O"),
        ("raised", "open", "open_A", 0, "Poet Unmasked - Wide Laugh"),
        ("rest", "closed", "rest", 0, "Poet Unmasked - Eyes Closed"),
        ("rest", "closed", "smile", 0, "Poet Unmasked - Serene Smile"),
        ("raised", "closed", "open_O", 0, "Poet Unmasked - Soulful O"),
        ("raised", "closed", "open_A", 0, "Poet Unmasked - Ecstatic Cry"),
    ]
    for br, ey, mo, tilt, label_txt in front_combos:
        idx = len(faces_catalog) + 1
        fid = f"face_{idx:03d}_poet_front_{br}_{ey}_{mo}"
        im = build_poet_front_face(br, ey, mo, tilt)
        im.save(os.path.join(FACES_OUT, f"{fid}.png"))
        faces_catalog.append({
            "id": fid, "index": idx, "character": "Poet (Tracksuit)", "view": "front",
            "label": label_txt, "brows": br, "eyes": ey, "mouth": mo,
            "file": f"arena/parts/kit3/release_v2/faces_100x/{fid}.png"
        })

    # 2. Row 3 & 4 (24 Faces): Poet Side-Profile Modular Combinations (12 With Sunglasses + 12 Unmasked)
    prof_mouths = [
        ("profile_nose_15.png", "Rest"),
        ("profile_nose_16.png", "Warm Smile"),
        ("profile_nose_17.png", "Bright Grin"),
        ("profile_nose_18.png", "Singing O"),
        ("profile_nose_19.png", "Calling A"),
        ("profile_nose_20.png", "Joy Laugh"),
        ("profile_mouth_21.png", "Chant U"),
        ("profile_mouth_22.png", "Hum M_B_P"),
        ("profile_mouth_23.png", "Lyric F_V"),
        ("profile_mouth_24.png", "Solemn Frown"),
        ("profile_mouth_25.png", "Speak E"),
        ("profile_mouth_26.png", "Whistle O"),
    ]
    for i, (m_file, m_lbl) in enumerate(prof_mouths):
        idx = len(faces_catalog) + 1
        b_idx = 9 + (i % 6)
        fid = f"face_{idx:03d}_poet_prof_shade_{i+1:02d}"
        im = build_poet_profile_face(eye_idx=1, brow_idx=b_idx, mouth_file=m_file, with_sunglasses=True)
        im.save(os.path.join(FACES_OUT, f"{fid}.png"))
        faces_catalog.append({
            "id": fid, "index": idx, "character": "Poet (Profile)", "view": "profile",
            "label": f"Profile Shade - {m_lbl}", "eyes": "sunglasses", "mouth": m_lbl,
            "file": f"arena/parts/kit3/release_v2/faces_100x/{fid}.png"
        })
    for i, (m_file, m_lbl) in enumerate(prof_mouths):
        idx = len(faces_catalog) + 1
        e_idx = 1 + (i % 8)
        b_idx = 9 + (i % 6)
        fid = f"face_{idx:03d}_poet_prof_unmasked_{i+1:02d}"
        im = build_poet_profile_face(eye_idx=e_idx, brow_idx=b_idx, mouth_file=m_file, with_sunglasses=False)
        im.save(os.path.join(FACES_OUT, f"{fid}.png"))
        faces_catalog.append({
            "id": fid, "index": idx, "character": "Poet (Profile)", "view": "profile",
            "label": f"Profile Unmasked - {m_lbl}", "eyes": f"eyes_{e_idx:02d}", "mouth": m_lbl,
            "file": f"arena/parts/kit3/release_v2/faces_100x/{fid}.png"
        })

    # 3. Row 5 & 6 (24 Faces): Poet 3/4 & Front Emotional Acting Heads (Weave Library)
    weave_files = [
        ("head.front.sunglasses.png", "front", "Weave - Shade Neutral"),
        ("head.front.sunglasses_smile.png", "front", "Weave - Shade Smile"),
        ("head.front.big_smile.png", "front", "Weave - Big Grin"),
        ("head.front.singing.png", "front", "Weave - Singing Lyric"),
        ("head.front.speaking.png", "front", "Weave - Speaking"),
        ("head.front.surprised.png", "front", "Weave - Surprised"),
        ("head.front.frowning.png", "front", "Weave - Frowning"),
        ("head.front.look_up.png", "front", "Weave - Look Up Sky"),
        ("head.front.look_down.png", "front", "Weave - Look Down"),
        ("head.front.closed.png", "front", "Weave - Eyes Closed"),
        ("head.3q.listening.png", "threequarter", "Weave 3/4 - Listening"),
        ("head.3q.recognition.png", "threequarter", "Weave 3/4 - Recognition"),
        ("head.3q.sad.png", "threequarter", "Weave 3/4 - Sad Sorrow"),
        ("head.3q.reluctant.png", "threequarter", "Weave 3/4 - Reluctant"),
        ("head.3q.embarrassed.png", "threequarter", "Weave 3/4 - Embarrassed"),
        ("head.3q.forced_grin.png", "threequarter", "Weave 3/4 - Forced Grin"),
        ("head.3q.afraid.png", "threequarter", "Weave 3/4 - Afraid"),
        ("head.3q.surprised.png", "threequarter", "Weave 3/4 - Surprised"),
        ("head.3q.pain.png", "threequarter", "Weave 3/4 - Sharp Pain"),
        ("head.3q.strain.png", "threequarter", "Weave 3/4 - Heavy Strain"),
        ("head.3q.panting.png", "threequarter", "Weave 3/4 - Panting"),
        ("head.3q.tired.png", "threequarter", "Weave 3/4 - Exhausted"),
        ("head.threequarter_L.neutral.png", "threequarter", "Weave 3/4 L - Neutral"),
        ("head.profile_R.neutral.png", "profile", "Weave Profile R - Neutral"),
    ]
    for wf, vw, label_txt in weave_files:
        idx = len(faces_catalog) + 1
        fid = f"face_{idx:03d}_weave_{wf.replace('.png','').replace('.','_')}"
        im = Image.open(os.path.join(WM_HEADS, wf)).convert("RGBA")
        arr = np.array(im)
        p09.defringe_white_halo(arr, radius=3)
        card = fit_on_card(Image.fromarray(arr))
        card.save(os.path.join(FACES_OUT, f"{fid}.png"))
        faces_catalog.append({
            "id": fid, "index": idx, "character": "Poet (Black T-Shirt)", "view": vw,
            "label": label_txt, "eyes": "painted", "mouth": "painted",
            "file": f"arena/parts/kit3/release_v2/faces_100x/{fid}.png"
        })

    # 4. Row 7 (12 Faces): Young Poet (Age 6) Front, 3/4 & Modular Profile Expressions
    yp_specs = [
        ("front_neutral", 1, 1, "young_poet_nose_01.png", "front", "Young Poet - Front Calm"),
        ("threequarter_neutral", 1, 1, "young_poet_nose_01.png", "threequarter", "Young Poet - 3/4 Curious"),
        ("profile_painted", 1, 1, "young_poet_nose_01.png", "profile", "Young Poet - Profile Gaze"),
        ("prof", 1, 1, "young_poet_nose_01.png", "profile", "Young Poet - Profile Rest"),
        ("prof", 2, 2, "young_poet_nose_02.png", "profile", "Young Poet - Profile Wonder"),
        ("prof", 3, 3, "young_poet_nose_03.png", "profile", "Young Poet - Profile Smile"),
        ("prof", 4, 4, "young_poet_nose_04.png", "profile", "Young Poet - Eyes Closed O"),
        ("prof", 5, 6, "young_poet_nose_05.png", "profile", "Young Poet - Happy Laugh"),
        ("prof", 6, 7, "young_poet_nose_06.png", "profile", "Young Poet - Profile Call"),
        ("prof", 2, 8, "young_poet_mouth_03.png", "profile", "Young Poet - Profile Speak"),
        ("prof", 4, 5, "young_poet_mouth_04.png", "profile", "Young Poet - Profile Pout"),
        ("prof", 3, 1, "young_poet_nose_05.png", "profile", "Young Poet - Bright Cheer"),
    ]
    for mode, bi, ei, mf, vw, label_txt in yp_specs:
        idx = len(faces_catalog) + 1
        fid = f"face_{idx:03d}_young_poet_{mode}_b{bi}_e{ei}"
        card = build_young_poet_face(mode, bi, ei, mf)
        card.save(os.path.join(FACES_OUT, f"{fid}.png"))
        faces_catalog.append({
            "id": fid, "index": idx, "character": "Young Poet (Age 6)", "view": vw,
            "label": label_txt, "eyes": f"eyes_{ei}", "mouth": mf,
            "file": f"arena/parts/kit3/release_v2/faces_100x/{fid}.png"
        })

    # 5. Row 8 (12 Faces): Ghost Child (Age 7) & Woman / Mother
    ghost_specs = [
        ("front", "ghost_head_04.png", "ghost_head_08.png", "ghost_head_12.png", "front", "Ghost Child - Open Gaze"),
        ("front", "ghost_head_05.png", "ghost_head_09.png", "ghost_head_13.png", "front", "Ghost Child - Melancholy"),
        ("front", "ghost_head_04.png", "ghost_head_09.png", "ghost_head_12.png", "front", "Ghost Child - Pleading"),
        ("front", "ghost_head_05.png", "ghost_head_08.png", "ghost_head_13.png", "front", "Ghost Child - Sorrow"),
        ("prof", "ghost_head_06.png", "ghost_head_10.png", "ghost_head_14.png", "threequarter", "Ghost Child - 3/4 Calm"),
        ("prof", "ghost_head_07.png", "ghost_head_11.png", "ghost_head_15.png", "threequarter", "Ghost Child - 3/4 Wistful"),
    ]
    for mode, ef, bf, mf, vw, label_txt in ghost_specs:
        idx = len(faces_catalog) + 1
        fid = f"face_{idx:03d}_ghost_child_{idx}"
        card = build_ghost_child_face(mode, ef, bf, mf)
        card.save(os.path.join(FACES_OUT, f"{fid}.png"))
        faces_catalog.append({
            "id": fid, "index": idx, "character": "Ghost Child (Age 7)", "view": vw,
            "label": label_txt, "eyes": ef, "mouth": mf,
            "file": f"arena/parts/kit3/release_v2/faces_100x/{fid}.png"
        })

    direct_cast_heads = [
        (os.path.join(BL_HEADS, "ghost_child_age_7/ghost_head_03.png"), "Ghost Child (Age 7)", "back", "Ghost Child - Back Curls"),
        (os.path.join(V2_PARTS, "woman.teal_dress/head.front.png"), "Woman / Muse", "front", "Woman Muse - Front Serene"),
        (os.path.join(V2_PARTS, "woman.teal_dress/head.profile.png"), "Woman / Muse", "profile", "Woman Muse - Side Profile"),
        (os.path.join(V2_PARTS, "woman.window_woman_dress/head.front.png"), "Window Woman", "threequarter", "Window Woman - 3/4 Gaze"),
        (os.path.join(BL_HEADS, "the_mother_teal_dress/mother_head_03.png"), "The Mother", "threequarter", "Mother - 3/4 Earrings"),
        (os.path.join(BL_HEADS, "the_mother_teal_dress/mother_head_04.png"), "The Mother", "profile", "Mother - Profile Afro"),
        # 6. Row 9 (12 Faces): Father, Ex & Vintage Party Expressive Heads
        (os.path.join(BL_HEADS, "the_father_long_coat/father_head_01.png"), "The Father", "front", "Father - Flat Cap Calm"),
        (os.path.join(BL_HEADS, "the_father_long_coat/father_head_02.png"), "The Father", "threequarter", "Father - Flat Cap 3/4 L"),
        (os.path.join(BL_HEADS, "the_father_long_coat/father_head_03.png"), "The Father", "threequarter", "Father - Flat Cap 3/4 R"),
        (os.path.join(BL_HEADS, "the_father_long_coat/father_head_04.png"), "The Father", "profile", "Father - Flat Cap Profile"),
        (os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_01.png"), "The Ex", "back", "The Ex - Back Fade"),
        (os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_04.png"), "The Ex", "threequarter_back", "The Ex - 3/4 Back Turn"),
        (os.path.join(BL_HEADS, "party_guests/party_head_02.png"), "Vintage Party", "threequarter", "Party Gentleman - 3/4"),
        (os.path.join(BL_HEADS, "party_guests/party_head_04.png"), "Vintage Party", "profile", "Party Gentleman - Profile"),
        (os.path.join(BL_HEADS, "party_guests/party_head_08.png"), "Vintage Party", "threequarter", "Party Lady - Finger Waves"),
        (os.path.join(BL_HEADS, "party_guests/party_head_09.png"), "Vintage Party", "profile", "Party Lady - Profile"),
        (os.path.join(BL_HEADS, "party_guests/party_head_03.png"), "Vintage Party", "threequarter", "Party Gentleman - 3/4 R"),
        (os.path.join(BL_HEADS, "party_guests/party_head_10.png"), "Vintage Party", "back", "Party Lady - Back Waves"),
    ]
    def composite_cast_features_if_blank(im, path, vw):
        """
        Adds skin-matched eyes, brows, nose, and mouth onto blank head bases in `body_lab/heads`
        (`mother_head_03/04`, `father_head_01..04`, `party_head_02/03/04/08/09`, `woman.teal_dress/head.profile`)
        so every non-back head in Rows 8 and 9 has a complete, realistic painted face.
        """
        if vw in ("back", "threequarter_back") or "ghost" in path:
            return im
        if "woman." in path and "woman.teal_dress/head.profile" not in path:
            return im
        arr = np.array(im)
        H, W = arr.shape[:2]
        fg = arr[:, :, 3] > 180
        # Sample cheek skin RGB from center-right of face
        sy0, sy1 = int(H * 0.48), int(H * 0.65)
        sx0, sx1 = int(W * 0.45), int(W * 0.72)
        patch = arr[sy0:sy1, sx0:sx1]
        pmask = patch[:, :, 3] > 180
        skin_rgb = tuple(np.median(patch[pmask][:, :3], axis=0)) if np.any(pmask) else (152.0, 98.0, 62.0)

        out = im.copy()
        if "father_head_01" in path:
            # Front Father with flat cap & beard: add brows, eyes, nose, and beard-framed mouth
            b_im = blend_profile_part(os.path.join(TS_DIR, "24_brows_rest.png"), skin_rgb, erode_px=32, blur_sigma=6.0).resize((int(W * 0.46), int(H * 0.10)), Image.Resampling.LANCZOS)
            e_im = blend_profile_part(os.path.join(TS_DIR, "22_eyes_open.png"), skin_rgb, erode_px=34, blur_sigma=6.0).resize((int(W * 0.44), int(H * 0.12)), Image.Resampling.LANCZOS)
            n_im = blend_profile_part(os.path.join(TS_DIR, "26_nose_front.png"), skin_rgb, erode_px=34, blur_sigma=7.0).resize((int(W * 0.18), int(H * 0.17)), Image.Resampling.LANCZOS)
            m_im = feather_part(os.path.join(BL_HEADS, "the_father_long_coat/father_head_06.png"), erode_px=6, blur_sigma=2.5).resize((int(W * 0.32), int(H * 0.09)), Image.Resampling.LANCZOS)
            cx = W // 2
            out.alpha_composite(b_im, (cx - b_im.width // 2, int(H * 0.36)))
            out.alpha_composite(e_im, (cx - e_im.width // 2, int(H * 0.43)))
            out.alpha_composite(n_im, (cx - n_im.width // 2, int(H * 0.49)))
            out.alpha_composite(m_im, (cx - m_im.width // 2, int(H * 0.67)))
            return out

        # Profile / 3Q heads for Woman, Mother, Father, and Party Guests
        facing_left = any(k in path for k in ["father_head_04", "party_head_04", "party_head_08", "party_head_09"])
        if facing_left:
            out = out.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        is_female = any(k in path for k in ["mother_head", "party_head_08", "party_head_09", "woman.teal_dress"])
        if is_female:
            b_im = blend_profile_part(os.path.join(YP_PROF_DIR, "young_poet_acc_02.png"), skin_rgb, erode_px=6, blur_sigma=3.5).resize((int(W * 0.20), int(H * 0.08)), Image.Resampling.LANCZOS)
            e_im = blend_profile_part(os.path.join(YP_PROF_DIR, "young_poet_eyes_03.png"), skin_rgb, erode_px=6, blur_sigma=3.5).resize((int(W * 0.22), int(H * 0.16)), Image.Resampling.LANCZOS)
            m_im = blend_profile_part(os.path.join(YP_PROF_DIR, "young_poet_nose_01.png"), skin_rgb, erode_px=6, blur_sigma=3.5).resize((int(W * 0.20), int(H * 0.13)), Image.Resampling.LANCZOS)
            fx = int(W * 0.64) if ("mother" in path or "woman.teal_dress" in path) else int(W * 0.60)
            ey = int(H * 0.55) if "mother" in path else (int(H * 0.46) if "woman.teal_dress" in path else int(H * 0.49))
            out.alpha_composite(b_im, (fx, ey - int(H * 0.06)))
            out.alpha_composite(e_im, (fx + 2, ey))
            out.alpha_composite(m_im, (fx + 5, ey + int(H * 0.15)))
        else:
            # Father 3Q/Profile or Party Gentleman 3Q/Profile
            b_im = blend_profile_part(os.path.join(TS_PROF_DIR, "profile_sunglasses_10.png"), skin_rgb, erode_px=8, blur_sigma=4.0).resize((int(W * 0.22), int(H * 0.08)), Image.Resampling.LANCZOS)
            e_im = blend_profile_part(os.path.join(TS_PROF_DIR, "profile_eyes_02.png"), skin_rgb, erode_px=8, blur_sigma=4.0).resize((int(W * 0.21), int(H * 0.14)), Image.Resampling.LANCZOS)
            m_im = blend_profile_part(os.path.join(TS_PROF_DIR, "profile_nose_16.png"), skin_rgb, erode_px=8, blur_sigma=4.0).resize((int(W * 0.22), int(H * 0.16)), Image.Resampling.LANCZOS)
            fx = int(W * 0.64) if "party_head_04" in path else int(W * 0.62)
            ey = int(H * 0.41) if "father" in path else int(H * 0.42)
            out.alpha_composite(b_im, (fx, ey - int(H * 0.06)))
            out.alpha_composite(e_im, (fx + 2, ey))
            out.alpha_composite(m_im, (fx + 6, ey + int(H * 0.17)))

        if facing_left:
            out = out.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        return out

    for path, char_name, vw, label_txt in direct_cast_heads:
        idx = len(faces_catalog) + 1
        fid = f"face_{idx:03d}_{char_name.lower().replace(' ','_').replace('/','').replace('&','').replace('(','').replace(')','')}_{idx}"
        im = Image.open(path).convert("RGBA")
        arr = np.array(im)
        p09.defringe_white_halo(arr, radius=3)
        im_clean = composite_cast_features_if_blank(Image.fromarray(arr), path, vw)
        card = fit_on_card(im_clean)
        card.save(os.path.join(FACES_OUT, f"{fid}.png"))
        faces_catalog.append({
            "id": fid, "index": idx, "character": char_name, "view": vw,
            "label": label_txt, "eyes": "painted", "mouth": "painted",
            "file": f"arena/parts/kit3/release_v2/faces_100x/{fid}.png"
        })

    # Render the 108-Face High-Res Contact Sheet (12 columns x 9 rows)
    cols, rows = 12, 9
    cw, ch = 220, 275
    sheet = Image.new("RGBA", (cols * cw + 24, rows * ch + 90), (234, 229, 220, 255))
    draw = ImageDraw.Draw(sheet)
    draw.rectangle([0, 0, sheet.width, 68], fill=(24, 20, 18, 255))
    draw.text((24, 18), "WYGWYL 100X FACE & EXPRESSION ATLAS -- 108 MODULAR & MULTI-CAST HEADS (SKIN-MATCHED & SEAMLESS)", fill=(245, 185, 66, 255))
    draw.text((24, 42), "Rows 1-2: Poet High-Res Gouache Modular Front | Rows 3-4: Poet Seamless Side-Profile | Rows 5-6: Weave 3/4 & Acting | Rows 7-9: Young Poet, Ghost Child, Mother, Father, Ex, Party", fill=(195, 188, 176, 255))

    for i, item in enumerate(faces_catalog):
        c = i % cols
        r = i // cols
        x0 = 12 + c * cw
        y0 = 78 + r * ch
        draw.rectangle([x0 + 3, y0 + 3, x0 + cw - 3, y0 + ch - 3], fill=(244, 240, 232, 255), outline=(198, 190, 178, 255), width=1)
        im = Image.open(os.path.join(FACES_OUT, f"{item['id']}.png")).convert("RGBA")
        sheet.alpha_composite(im, (x0, y0 + 14))
        draw.rectangle([x0 + 3, y0 + 3, x0 + cw - 3, y0 + 24], fill=(32, 28, 24, 255))
        lbl_ascii = f"#{item['index']:03d} {item['label'].replace('·', '-')[:23]}".encode("ascii", "replace").decode("ascii")
        draw.text((x0 + 8, y0 + 7), lbl_ascii, fill=(240, 232, 215, 255))

    atlas_path = os.path.join(ART_DIR, "scratch_100x_faces_atlas.png")
    sheet.save(atlas_path)
    sheet.save(os.path.join(REL_DIR, "faces_100x_atlas.png"))
    with open(os.path.join(REL_DIR, "faces_100x_catalog.json"), "w") as f:
        json.dump({"total_faces": len(faces_catalog), "faces": faces_catalog}, f, indent=2)
    print(f"Saved 108 faces and atlas -> {atlas_path}")
    return faces_catalog


# ============================================================================
# PART 2: 100x MULTI-CHARACTER POSE ENGINE (10 CHARACTERS x 12 POSES = 120 POSES)
# ============================================================================

CHARACTER_RIG_SPECS = [
    {
        "id": "poet_tracksuit",
        "name": "Poet (Tracksuit & Shades)",
        "scale": 1.0,
        "engine": "poet_native",
        "head_override": None,
    },
    {
        "id": "poet_unmasked",
        "name": "Poet (Tracksuit Unmasked)",
        "scale": 1.0,
        "engine": "poet_native",
        "head_override": "unmasked",
    },
    {
        "id": "poet_black_tshirt",
        "name": "Poet (Black T-Shirt)",
        "scale": 1.0,
        "dir": "poet.black_tshirt",
        "head_path": os.path.join(WM_HEADS, "head.front.neutral.png"),
        "head_cheer": os.path.join(WM_HEADS, "head.front.big_smile.png"),
        "head_3q": os.path.join(WM_HEADS, "head.3q.recognition.png"),
        "head_prof": os.path.join(WM_HEADS, "head.profile_R.neutral.png"),
        "torso_path": os.path.join(ROOT, "shots/weave/cast/man/parts/torso.front.png"),
        "pelvis_path": os.path.join(TS_DIR, "06_pelvis_front_cover.png"),
        "uarm_path": os.path.join(ROOT, "shots/weave/cast/man/parts/uarm.profile.png"),
        "farm_path": os.path.join(ROOT, "shots/weave/cast/man/parts/farm.profile.png"),
        "hand_path": os.path.join(TS_DIR, "15_hand_relaxed_L.png"),
        "hand_open_path": os.path.join(TS_DIR, "17_hand_open_L.png"),
        "thigh_path": os.path.join(ROOT, "shots/weave/cast/man/parts/thigh.profile.png"),
        "shin_path": os.path.join(ROOT, "shots/weave/cast/man/parts/shin.profile.png"),
        "foot_L": "body.front.foot.L.png",
        "foot_is_side": True,
    },
    {
        "id": "woman_teal_dress",
        "name": "Woman / Muse (Brocade)",
        "scale": 0.96,
        "dir": "woman.teal_dress",
        "head_path": os.path.join(V2_PARTS, "woman.teal_dress/head.front.png"),
        "head_cheer": os.path.join(V2_PARTS, "woman.teal_dress/head.front.png"),
        "head_3q": os.path.join(V2_PARTS, "woman.teal_dress/head.front.png"),
        "head_prof": os.path.join(FACES_OUT, "face_093_woman__muse_93.png"),
        "torso": "body.front.torso.png",
        "pelvis_path": os.path.join(V2_PARTS, "woman.window_woman_dress/body.front.pelvis.png"),
        "uarm_L": "body.front.uarm.L.png",
        "farm_L": "body.front.farm.L.png",
        "hand_path": os.path.join(TS_DIR, "15_hand_relaxed_L.png"),
        "hand_open_path": os.path.join(TS_DIR, "17_hand_open_L.png"),
        "thigh_L": "body.front.thigh.L.png",
        "shin_L": "body.front.shin.L.png",
        "foot_L": "body.front.foot.L.png",
        "foot_is_side": True,
    },
    {
        "id": "woman_mother_cardigan",
        "name": "The Mother (Cardigan)",
        "scale": 0.94,
        "dir": "woman.mother_cardigan",
        "head_path": os.path.join(FACES_OUT, "face_095_the_mother_95.png"),
        "head_cheer": os.path.join(FACES_OUT, "face_095_the_mother_95.png"),
        "head_3q": os.path.join(FACES_OUT, "face_095_the_mother_95.png"),
        "head_prof": os.path.join(FACES_OUT, "face_096_the_mother_96.png"),
        "torso": "body.front.torso.png",
        "pelvis": "body.front.pelvis.png",
        "uarm_L": "body.front.uarm.L.png",
        "farm_L": "body.front.farm.L.png",
        "hand_path": os.path.join(TS_DIR, "15_hand_relaxed_L.png"),
        "hand_open_path": os.path.join(TS_DIR, "17_hand_open_L.png"),
        "thigh_L": "body.front.thigh.L.png",
        "shin_L": "body.front.shin.L.png",
        "foot_L": "body.front.foot.L.png",
        "foot_is_side": False,
    },
    {
        "id": "ex_olive_bomber",
        "name": "The Ex (Olive Bomber)",
        "scale": 0.98,
        "dir": "ex.ex_jacket",
        "head_path": os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_01.png"),
        "head_cheer": os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_04.png"),
        "head_3q": os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_04.png"),
        "head_prof": os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_05.png"),
        "torso": "body.front.torso.png",
        "pelvis_path": os.path.join(TS_DIR, "06_pelvis_front_cover.png"),
        "uarm_L": "body.front.uarm.L.png",
        "farm_L": "body.front.farm.L.png",
        "hand_path": os.path.join(TS_DIR, "15_hand_relaxed_L.png"),
        "hand_open_path": os.path.join(TS_DIR, "17_hand_open_L.png"),
        "thigh_L": "body.front.thigh.L.png",
        "shin_L": "body.front.shin.L.png",
        "foot_L": "body.front.foot.L.png",
        "foot_is_side": True,
    },
    {
        "id": "vintage_party_suit",
        "name": "Party Gentleman (Suit)",
        "scale": 1.0,
        "dir": "party.vintage_party",
        "head_path": os.path.join(WM_HEADS, "head.front.small_smile.png"),
        "head_cheer": os.path.join(WM_HEADS, "head.front.big_smile.png"),
        "head_3q": os.path.join(FACES_OUT, "face_103_vintage_party_103.png"),
        "head_prof": os.path.join(FACES_OUT, "face_104_vintage_party_104.png"),
        "torso": "body.front.torso.png",
        "pelvis": "body.front.pelvis.png",
        "uarm_L": "body.front.uarm.L.png",
        "farm_L": "body.front.farm.L.png",
        "hand_path": os.path.join(TS_DIR, "15_hand_relaxed_L.png"),
        "hand_open_path": os.path.join(TS_DIR, "17_hand_open_L.png"),
        "thigh_L": "body.front.thigh.L.png",
        "shin_L": "body.front.shin.L.png",
        "foot_L": "body.front.foot.L.png",
        "foot_is_side": False,
    },
    {
        "id": "dj_cyber_naraka",
        "name": "DJ Cyber (Naraka Club)",
        "scale": 1.0,
        "dir": "party.dj_cyber",
        "head_path": os.path.join(WM_HEADS, "head.front.sunglasses.png"),
        "head_cheer": os.path.join(WM_HEADS, "head.front.sunglasses_smile.png"),
        "head_3q": os.path.join(WM_HEADS, "head.3q.listening.png"),
        "head_prof": os.path.join(WM_HEADS, "head.profile_R.neutral.png"),
        "torso": "body.front.torso.png",
        "pelvis_path": os.path.join(TS_DIR, "06_pelvis_front_cover.png"),
        "uarm_L": "body.front.uarm.L.png",
        "farm_L": "body.front.farm.L.png",
        "hand_path": os.path.join(TS_DIR, "15_hand_relaxed_L.png"),
        "hand_open_path": os.path.join(TS_DIR, "17_hand_open_L.png"),
        "thigh_L": "body.front.thigh.L.png",
        "shin_L": "body.front.shin.L.png",
        "foot_L": "body.front.foot.L.png",
        "foot_is_side": True,
    },
    {
        "id": "young_poet_child",
        "name": "Young Poet (Age 6 · 5.2H)",
        "scale": 0.72,
        "dir": "young_poet.child_clothes",
        "head_path": os.path.join(FACES_OUT, "face_073_young_poet_front_neutral_b1_e1.png"),
        "head_cheer": os.path.join(FACES_OUT, "face_080_young_poet_prof_b5_e6.png"),
        "head_3q": os.path.join(FACES_OUT, "face_074_young_poet_threequarter_neutral_b1_e1.png"),
        "head_prof": os.path.join(FACES_OUT, "face_078_young_poet_prof_b3_e3.png"),
        "torso": "body.front.torso.png",
        "pelvis": "body.front.pelvis.denim.png",
        "uarm_L": "body.front.uarm.L.png",
        "farm_L": "body.front.farm.L.png",
        "hand_path": os.path.join(TS_DIR, "15_hand_relaxed_L.png"),
        "hand_open_path": os.path.join(TS_DIR, "17_hand_open_L.png"),
        "thigh_L": "body.front.thigh.L.png",
        "shin_L": "body.front.shin.L.png",
        "foot_L": "body.front.foot.L.png",
        "foot_is_side": False,
    },
    {
        "id": "ancestor_indigo_gold",
        "name": "Father / Elder (Indigo)",
        "scale": 1.0,
        "dir": "ancestors.ancestor_robe_indigo_gold",
        "head_path": os.path.join(FACES_OUT, "face_097_the_father_97.png"),
        "head_cheer": os.path.join(FACES_OUT, "face_098_the_father_98.png"),
        "head_3q": os.path.join(FACES_OUT, "face_098_the_father_98.png"),
        "head_prof": os.path.join(FACES_OUT, "face_100_the_father_100.png"),
        "torso": "body.front.torso.png",
        "pelvis": "body.front.pelvis.png",
        "uarm_L": "body.front.uarm.L.png",
        "farm_L": "body.front.farm.L.png",
        "hand_path": os.path.join(TS_DIR, "15_hand_relaxed_L.png"),
        "hand_open_path": os.path.join(TS_DIR, "17_hand_open_L.png"),
        "thigh_L": "body.front.thigh.L.png",
        "shin_L": "body.front.shin.L.png",
        "foot_L": "body.front.foot.L.png",
        "foot_is_side": False,
    },
]

CANONICAL_12_POSES = [
    ("falter-reach-accepting", "01 Accepting Reach",
     dict(view="3Q", torso_lean_dx=12, head_turn="3Q",
          sh_L=(146, 128), el_L=(120, 174), wr_L=(102, 220), tip_L=(94, 248),
          sh_R=(214, 122), el_R=(258, 108), wr_R=(302, 92), tip_R=(334, 80),
          hip_L=(162, 224), kn_L=(146, 286), an_L=(130, 344), ft_L=(158, 366),
          hip_R=(198, 224), kn_R=(212, 286), an_R=(222, 344), ft_R=(256, 366))),
    ("falter-on-shoulder-contact-2", "02 Falter / Heart",
     dict(view="3Q", torso_lean_dx=0, head_turn="3Q",
          sh_L=(144, 128), el_L=(126, 174), wr_L=(172, 160), tip_L=(196, 154),
          sh_R=(214, 128), el_R=(232, 178), wr_R=(244, 224), tip_R=(250, 250),
          hip_L=(162, 224), kn_L=(152, 286), an_L=(144, 346), ft_L=(126, 374),
          hip_R=(198, 224), kn_R=(210, 286), an_R=(220, 344), ft_R=(252, 366))),
    ("02-front-guide-stone", "03 Guide / Welcome",
     dict(view="F", torso_lean_dx=0, head_turn="F",
          sh_L=(138, 128), el_L=(118, 176), wr_L=(76, 178), tip_L=(44, 174),
          sh_R=(222, 128), el_R=(242, 176), wr_R=(284, 178), tip_R=(316, 174),
          hip_L=(162, 224), kn_L=(154, 286), an_L=(148, 346), ft_L=(134, 374),
          hip_R=(198, 224), kn_R=(206, 286), an_R=(212, 346), ft_R=(226, 374))),
    ("ex-disappears-gather", "04 Gather / Converse",
     dict(view="3Q", torso_lean_dx=4, head_turn="3Q",
          sh_L=(144, 128), el_L=(126, 176), wr_L=(112, 222), tip_L=(104, 248),
          sh_R=(214, 126), el_R=(236, 172), wr_R=(278, 166), tip_R=(308, 160),
          hip_L=(162, 224), kn_L=(148, 286), an_L=(136, 344), ft_L=(162, 366),
          hip_R=(198, 224), kn_R=(212, 286), an_R=(224, 344), ft_R=(256, 366))),
    ("04-6-rise-flex-reflect", "05 Prayer / Reflect",
     dict(view="F", torso_lean_dx=0, head_turn="F",
          sh_L=(140, 128), el_L=(112, 168), wr_L=(88, 132), tip_L=(74, 108),
          sh_R=(220, 128), el_R=(248, 168), wr_R=(272, 132), tip_R=(286, 108),
          hip_L=(162, 224), kn_L=(154, 286), an_L=(148, 346), ft_L=(134, 374),
          hip_R=(198, 224), kn_R=(206, 286), an_R=(212, 346), ft_R=(226, 374))),
    ("wince-standing-still", "06 Standing Still",
     dict(view="F", torso_lean_dx=0, head_turn="F",
          sh_L=(140, 128), el_L=(130, 178), wr_L=(126, 226), tip_L=(124, 254),
          sh_R=(220, 128), el_R=(230, 178), wr_R=(234, 226), tip_R=(236, 254),
          hip_L=(162, 224), kn_L=(156, 286), an_L=(150, 346), ft_L=(138, 374),
          hip_R=(198, 224), kn_R=(204, 286), an_R=(210, 346), ft_R=(222, 374))),
    ("walk-the-room", "07 Walk Stride",
     dict(view="3Q", torso_lean_dx=6, head_turn="3Q",
          sh_L=(146, 128), el_L=(128, 174), wr_L=(110, 218), tip_L=(100, 244),
          sh_R=(214, 126), el_R=(238, 168), wr_R=(278, 158), tip_R=(306, 150),
          hip_L=(162, 224), kn_L=(144, 286), an_L=(128, 344), ft_L=(158, 366),
          hip_R=(198, 224), kn_R=(214, 286), an_R=(228, 344), ft_R=(260, 366))),
    ("02-good-fists-up", "08 Triumph / Cheer",
     dict(view="F", torso_lean_dx=0, head_turn="CHEER",
          sh_L=(138, 126), el_L=(98, 114), wr_L=(90, 66), tip_L=(86, 38),
          sh_R=(222, 126), el_R=(262, 114), wr_R=(270, 66), tip_R=(274, 38),
          hip_L=(160, 224), kn_L=(140, 286), an_L=(122, 346), ft_L=(104, 374),
          hip_R=(200, 224), kn_R=(220, 286), an_R=(238, 346), ft_R=(256, 374))),
    ("open-arms-02-at-show", "09 Wide Embrace",
     dict(view="F", torso_lean_dx=0, head_turn="F",
          sh_L=(138, 128), el_L=(96, 146), wr_L=(52, 146), tip_L=(22, 144),
          sh_R=(222, 128), el_R=(264, 146), wr_R=(308, 146), tip_R=(338, 144),
          hip_L=(162, 224), kn_L=(154, 286), an_L=(148, 346), ft_L=(134, 374),
          hip_R=(198, 224), kn_R=(206, 286), an_R=(212, 346), ft_R=(226, 374))),
    ("phone-palm-mother", "10 Phone / Listen",
     dict(view="3Q", torso_lean_dx=0, head_turn="3Q",
          sh_L=(146, 128), el_L=(130, 168), wr_L=(152, 112), tip_L=(160, 92),
          sh_R=(214, 126), el_R=(240, 164), wr_R=(278, 152), tip_R=(306, 142),
          hip_L=(162, 224), kn_L=(156, 286), an_L=(152, 344), ft_L=(180, 366),
          hip_R=(198, 224), kn_R=(204, 286), an_R=(206, 344), ft_R=(238, 366))),
    ("03-gentle-slow-dance", "11 Joyful Dance",
     dict(view="3Q", torso_lean_dx=2, head_turn="CHEER",
          sh_L=(144, 126), el_L=(114, 156), wr_L=(96, 110), tip_L=(88, 86),
          sh_R=(216, 126), el_R=(246, 158), wr_R=(264, 114), tip_R=(272, 90),
          hip_L=(162, 224), kn_L=(178, 284), an_L=(160, 344), ft_L=(188, 366),
          hip_R=(198, 224), kn_R=(214, 284), an_R=(196, 344), ft_R=(228, 366))),
    ("a04-point-at", "12 Point Horizon",
     dict(view="3Q", torso_lean_dx=8, head_turn="P",
          sh_L=(146, 128), el_L=(126, 174), wr_L=(108, 220), tip_L=(100, 248),
          sh_R=(214, 122), el_R=(258, 118), wr_R=(304, 112), tip_R=(336, 108),
          hip_L=(162, 224), kn_L=(146, 286), an_L=(132, 344), ft_L=(160, 366),
          hip_R=(198, 224), kn_R=(212, 286), an_R=(224, 344), ft_R=(256, 366))),
]

_GENERIC_PART_CACHE = {}
_LIMB_AXIS_CACHE = {}


def load_generic_clean_part(path, kind="limb"):
    key = (path, kind)
    if key in _GENERIC_PART_CACHE:
        return _GENERIC_PART_CACHE[key].copy()
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    H, W = arr.shape[:2]
    p09.defringe_white_halo(arr, radius=3)
    if kind == "limb":
        arr[:int(H * 0.11), :, 3] = 0
        arr[int(H * 0.85):, :, 3] = 0
        p09.strip_outer_kraft_margin(arr, max_px=12)
        p09.fill_internal_grommet_holes(arr)
        p09.remove_internal_tan_and_brass(arr, 0, H)
    elif kind == "torso":
        arr[:int(H * 0.08), :, 3] = 0
        p09.strip_outer_kraft_margin(arr, max_px=10)
        p09.fill_internal_grommet_holes(arr)
        p09.remove_internal_tan_and_brass(arr, 0, int(H * 0.28))
        p09.remove_internal_tan_and_brass(arr, int(H * 0.78), H)
    elif kind == "pelvis":
        p09.strip_outer_kraft_margin(arr, max_px=10)
        p09.fill_internal_grommet_holes(arr)
        p09.remove_internal_tan_and_brass(arr, 0, int(H * 0.30))
    elif kind == "hand":
        arr[:int(H * 0.23), :, 3] = 0
        p09.strip_outer_kraft_margin(arr, max_px=18)
        p09.fill_internal_grommet_holes(arr)
        p09.remove_internal_tan_and_brass(arr, 0, int(H * 0.36))
    elif kind == "foot":
        arr[:int(H * 0.16), :, 3] = 0
        p09.strip_outer_kraft_margin(arr, max_px=10)
        p09.fill_internal_grommet_holes(arr)
        p09.remove_internal_tan_and_brass(arr, 0, int(H * 0.42))
    elif kind == "head":
        arr[int(H * 0.84):, :, 3] = 0
        p09.remove_internal_tan_and_brass(arr, int(H * 0.72), int(H * 0.85))
    clean = Image.fromarray(arr)
    _GENERIC_PART_CACHE[key] = clean
    return clean.copy()


def measure_limb_axis_and_girth(path, im, target_aspect=0.50):
    """
    Measures the exact top (8%..24% Y) and bottom (76%..92% Y) medial-axis joint centroids
    `(anc_a, anc_b)` and mid-limb perpendicular width ratio `w_mid / bone_len`, returning
    `(anc_a, anc_b, auto_girth)` so pre-angled or thin/wide limbs render straight and proportional.
    """
    key = (path, round(target_aspect, 3))
    if key in _LIMB_AXIS_CACHE:
        return _LIMB_AXIS_CACHE[key]
    arr = np.array(im)
    H, W = arr.shape[:2]
    fg = arr[:, :, 3] > 32
    ys, xs = np.where(fg)
    if len(xs) < 20:
        res = ((0.5, 0.18), (0.5, 0.80), 1.0)
        _LIMB_AXIS_CACHE[key] = res
        return res
    y0, y1 = ys.min(), ys.max()
    dh = max(10.0, float(y1 - y0))
    yt_0, yt_1 = int(y0 + 0.08 * dh), int(y0 + 0.24 * dh)
    yb_0, yb_1 = int(y0 + 0.76 * dh), int(y0 + 0.92 * dh)
    ym_0, ym_1 = int(y0 + 0.40 * dh), int(y0 + 0.60 * dh)

    t_xs = np.where(fg[yt_0:yt_1 + 1, :])[1]
    b_xs = np.where(fg[yb_0:yb_1 + 1, :])[1]
    cx_t = float(np.mean(t_xs)) if len(t_xs) else W * 0.5
    cy_t = 0.5 * (yt_0 + yt_1)
    cx_b = float(np.mean(b_xs)) if len(b_xs) else W * 0.5
    cy_b = 0.5 * (yb_0 + yb_1)

    dx = cx_b - cx_t
    dy = cy_b - cy_t
    bone_len = max(10.0, math.hypot(dx, dy))
    cos_t = abs(dy) / bone_len

    row_widths = []
    for y in range(ym_0, ym_1 + 1):
        rxs = np.where(fg[y, :])[0]
        if len(rxs) > 2:
            row_widths.append(float(rxs.max() - rxs.min()))
    w_mid = float(np.median(row_widths)) * cos_t if row_widths else W * 0.35
    native_aspect = w_mid / bone_len
    auto_girth = float(np.clip(target_aspect / max(0.18, native_aspect), 0.68, 1.55))
    res = ((cx_t / W, cy_t / H), (cx_b / W, cy_b / H), auto_girth)
    _LIMB_AXIS_CACHE[key] = res
    return res


def paste_generic_bone(canvas, im, anc_a, anc_b, pt_a, pt_b, girth=1.0, flip_x=False, brightness=1.0):
    """
    Rectifies any pre-angled bone axis `(anc_a -> anc_b)` to vertical around `pa`, scales along
    the bone (`scale_y`) and perpendicular to the bone (`scale_x = scale_y * girth`) without shear,
    and rotates to the target skeleton vector `(pt_a -> pt_b)`.
    """
    if flip_x:
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        anc_a = (1.0 - anc_a[0], anc_a[1])
        anc_b = (1.0 - anc_b[0], anc_b[1])
    if abs(brightness - 1.0) > 1e-3:
        im = ImageEnhance.Brightness(im).enhance(brightness)
    w, h = im.size
    pa = (anc_a[0] * w, anc_a[1] * h)
    pb = (anc_b[0] * w, anc_b[1] * h)
    dx_s, dy_s = pb[0] - pa[0], pb[1] - pa[1]
    len_s = max(1.0, math.hypot(dx_s, dy_s))
    ang_s = math.atan2(dy_s, dx_s)

    # Step 1: Rectify native bone axis to vertical (+90 deg) around `pa` if tilted
    tilt_from_vert = math.degrees(ang_s - math.pi / 2.0)
    if abs(tilt_from_vert) > 1.5:
        pad0 = int(math.hypot(w, h)) + 8
        tmp0 = Image.new("RGBA", (pad0 * 2, pad0 * 2), (0, 0, 0, 0))
        tmp0.paste(im, (int(round(pad0 - pa[0])), int(round(pad0 - pa[1]))))
        im = tmp0.rotate(tilt_from_vert, resample=Image.Resampling.BICUBIC, center=(pad0, pad0))
        w, h = im.size
        pa = (float(pad0), float(pad0))

    # Step 2: Scale along vertical bone axis (scale_y) and perpendicular to bone axis (scale_x)
    dx_t, dy_t = pt_b[0] - pt_a[0], pt_b[1] - pt_a[1]
    len_t = max(1.0, math.hypot(dx_t, dy_t))
    scale_y = len_t / len_s
    scale_x = scale_y * girth
    sw = max(1, int(round(w * scale_x)))
    sh = max(1, int(round(h * scale_y)))
    im_scaled = im.resize((sw, sh), Image.Resampling.LANCZOS)
    pa_s = (pa[0] * scale_x, pa[1] * scale_y)

    # Step 3: Rotate from vertical (+pi/2) to target bone angle
    rot_rad = math.atan2(dy_t, dx_t) - (math.pi / 2.0)
    rot_deg = -math.degrees(rot_rad)
    pad = int(math.hypot(sw, sh)) + 8
    tmp = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    tmp.paste(im_scaled, (int(round(pad - pa_s[0])), int(round(pad - pa_s[1]))))
    rot_im = tmp.rotate(rot_deg, resample=Image.Resampling.BICUBIC, center=(pad, pad))
    canvas.alpha_composite(rot_im, (int(round(pt_a[0] - pad)), int(round(pt_a[1] - pad))))


def render_character_pose(rig, pose_key, pose_cfg, cw=360, ch=420):
    if rig.get("engine") == "poet_native":
        canvas = p09.render_pose_archetype(pose_key, show_pins=True, cw=cw, ch=ch)
        if rig.get("head_override") == "unmasked":
            mode = "front_cheer_unmasked" if pose_key in ("02-good-fists-up", "03-gentle-slow-dance") else "front_smile_unmasked"
            uh = p09.build_modular_head(mode)
            lean_dx = pose_cfg.get("torso_lean_dx", 0)
            paste_generic_bone(canvas, uh, (0.50, 0.74), (0.50, 0.10), (180 + lean_dx, 108), (180 + lean_dx, 64), girth=0.88)
        return canvas

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    pins = []
    sc = rig["scale"]
    cx_floor, cy_floor = 180.0, 368.0

    def S(pt):
        return (cx_floor + (pt[0] - cx_floor) * sc, cy_floor + (pt[1] - cy_floor) * sc)

    cdir = os.path.join(V2_PARTS, rig["dir"])
    torso_p = rig.get("torso_path") or os.path.join(cdir, rig["torso"])
    torso_im = load_generic_clean_part(torso_p, "torso")
    pelvis_p = rig.get("pelvis_path") or os.path.join(cdir, rig["pelvis"])
    pelvis_im = load_generic_clean_part(pelvis_p, "pelvis")

    uarm_p = rig.get("uarm_path") or os.path.join(cdir, rig["uarm_L"])
    farm_p = rig.get("farm_path") or os.path.join(cdir, rig["farm_L"])
    thigh_p = rig.get("thigh_path") or os.path.join(cdir, rig["thigh_L"])
    shin_p = rig.get("shin_path") or os.path.join(cdir, rig["shin_L"])

    uarm_im = load_generic_clean_part(uarm_p, "limb")
    farm_im = load_generic_clean_part(farm_p, "limb")
    thigh_im = load_generic_clean_part(thigh_p, "limb")
    shin_im = load_generic_clean_part(shin_p, "limb")

    # Measure true medial bone axis & width-normalized girth for every limb card
    ua_a, ua_b, ua_g = measure_limb_axis_and_girth(uarm_p, uarm_im, target_aspect=0.52)
    fa_a, fa_b, fa_g = measure_limb_axis_and_girth(farm_p, farm_im, target_aspect=0.46)
    th_a, th_b, th_g = measure_limb_axis_and_girth(thigh_p, thigh_im, target_aspect=0.56)
    sh_a, sh_b, sh_g = measure_limb_axis_and_girth(shin_p, shin_im, target_aspect=0.46)

    use_open_hand = pose_key in ("falter-reach-accepting", "02-front-guide-stone", "02-good-fists-up", "open-arms-02-at-show", "a04-point-at")
    hand_p = rig.get("hand_open_path") if use_open_hand and rig.get("hand_open_path") else (rig.get("hand_path") or os.path.join(cdir, rig.get("hand_L", "body.front.hand.L.png")))
    hand_im = load_generic_clean_part(hand_p, "hand")
    foot_im = load_generic_clean_part(os.path.join(cdir, rig["foot_L"]), "foot")

    ht = pose_cfg["head_turn"]
    if ht == "CHEER":
        head_p = rig["head_cheer"]
    elif ht == "P":
        head_p = rig["head_prof"]
    elif ht == "3Q":
        head_p = rig["head_3q"]
    else:
        head_p = rig["head_path"]
    head_im = load_generic_clean_part(head_p, "head")

    lean_dx = pose_cfg.get("torso_lean_dx", 0)
    sh_L, el_L, wr_L, tip_L = S(pose_cfg["sh_L"]), S(pose_cfg["el_L"]), S(pose_cfg["wr_L"]), S(pose_cfg["tip_L"])
    sh_R, el_R, wr_R, tip_R = S(pose_cfg["sh_R"]), S(pose_cfg["el_R"]), S(pose_cfg["wr_R"]), S(pose_cfg["tip_R"])
    hip_L, kn_L, an_L, ft_L = S(pose_cfg["hip_L"]), S(pose_cfg["kn_L"]), S(pose_cfg["an_L"]), S(pose_cfg["ft_L"])
    hip_R, kn_R, an_R, ft_R = S(pose_cfg["hip_R"]), S(pose_cfg["kn_R"]), S(pose_cfg["an_R"]), S(pose_cfg["ft_R"])

    # Normalize hand span to proportional anatomical length
    hand_span = (22.0 if "child" in rig["id"] else 25.0) * sc
    tip_L = p09.unit_step(wr_L, tip_L, hand_span)
    tip_R = p09.unit_step(wr_R, tip_R, hand_span)

    # Foot anchors (side-profile shoes vs vertical front boots)
    if rig.get("foot_is_side"):
        f_anc = ((0.30, 0.28), (0.85, 0.78))
        ft_L = (an_L[0] - 25 * sc, an_L[1] + 20 * sc) if pose_cfg["view"] == "F" else (an_L[0] + 26 * sc, an_L[1] + 19 * sc)
        ft_R = (an_R[0] + 26 * sc, an_R[1] + 19 * sc)
        flip_fL = (pose_cfg["view"] == "F")
        f_girth = 1.02
    else:
        f_anc = ((0.50, 0.22), (0.50, 0.86))
        ft_L = (an_L[0] - 3 * sc, an_L[1] + 25 * sc)
        ft_R = (an_R[0] + 3 * sc, an_R[1] + 25 * sc)
        flip_fL = False
        f_girth = 0.88 if "child" in rig["id"] else 0.98

    # 1. Left Arm (if hanging behind torso in 3Q)
    if pose_cfg["view"] == "3Q" and wr_L[1] > el_L[1]:
        paste_generic_bone(canvas, hand_im, (0.50, 0.26), (0.50, 0.88), wr_L, tip_L, girth=0.92, brightness=0.92)
        paste_generic_bone(canvas, farm_im, fa_a, fa_b, el_L, wr_L, girth=fa_g, brightness=0.92)
        paste_generic_bone(canvas, uarm_im, ua_a, ua_b, sh_L, el_L, girth=ua_g, brightness=0.92)

    # 2. Legs (Foot behind Shin, Shin behind Thigh)
    paste_generic_bone(canvas, foot_im, f_anc[0], f_anc[1], an_L, ft_L, girth=f_girth, flip_x=flip_fL, brightness=0.94)
    paste_generic_bone(canvas, shin_im, sh_a, sh_b, kn_L, an_L, girth=sh_g, brightness=0.94)
    paste_generic_bone(canvas, thigh_im, th_a, th_b, hip_L, kn_L, girth=th_g, brightness=0.94)

    paste_generic_bone(canvas, foot_im, f_anc[0], f_anc[1], an_R, ft_R, girth=f_girth, flip_x=False)
    paste_generic_bone(canvas, shin_im, sh_a, sh_b, kn_R, an_R, girth=sh_g, flip_x=True)
    paste_generic_bone(canvas, thigh_im, th_a, th_b, hip_R, kn_R, girth=th_g, flip_x=True)

    # 3. Pelvis / Skirt (drawn BEHIND torso so torso jacket/bodice/cardigan sits naturally on top!)
    if rig["id"] == "woman_teal_dress":
        pel_girth = 0.72
        pel_y_end = 248
    elif "woman" in rig["id"]:
        pel_girth = 0.88
        pel_y_end = 244
    elif "child" in rig["id"]:
        pel_girth = 0.62
        pel_y_end = 236
    else:
        pel_girth = 0.88
        pel_y_end = 236
    pel_b = rig.get("pelvis_brightness", 1.0)
    paste_generic_bone(canvas, pelvis_im, (0.50, 0.16), (0.50, 0.86), S((180, 194)), S((180, pel_y_end)), girth=pel_girth, brightness=pel_b)
    if rig["id"] == "poet_black_tshirt":
        torso_girth = 1.48
    elif "child" in rig["id"]:
        torso_girth = 0.94
    elif "woman" in rig["id"]:
        torso_girth = 1.00
    else:
        torso_girth = 1.06
    paste_generic_bone(canvas, torso_im, (0.50, 0.10), (0.50, 0.89), S((180 + lean_dx, 108)), S((180, 208)), girth=torso_girth)

    # 4. Head
    head_span = 54 if "child" in rig["id"] else 46
    paste_generic_bone(canvas, head_im, (0.50, 0.78), (0.50, 0.10), S((180 + lean_dx, 110)), S((180 + lean_dx, 110 - head_span)), girth=0.92)

    # 5. Front / Raised Left Arm & Right Arm (Hand tucked behind Forearm cuff!)
    if not (pose_cfg["view"] == "3Q" and wr_L[1] > el_L[1]):
        paste_generic_bone(canvas, uarm_im, ua_a, ua_b, sh_L, el_L, girth=ua_g)
        paste_generic_bone(canvas, hand_im, (0.50, 0.26), (0.50, 0.88), wr_L, tip_L, girth=0.92)
        paste_generic_bone(canvas, farm_im, fa_a, fa_b, el_L, wr_L, girth=fa_g)

    paste_generic_bone(canvas, uarm_im, ua_a, ua_b, sh_R, el_R, girth=ua_g, flip_x=True)
    paste_generic_bone(canvas, hand_im, (0.50, 0.26), (0.50, 0.88), wr_R, tip_R, girth=0.92, flip_x=True)
    paste_generic_bone(canvas, farm_im, fa_a, fa_b, el_R, wr_R, girth=fa_g, flip_x=True)

    pins.extend([sh_L, el_L, sh_R, el_R, hip_L, kn_L, an_L, hip_R, kn_R, an_R])
    canvas = p09.apply_exterior_diecut_border(canvas)
    d = ImageDraw.Draw(canvas)
    for pt in pins:
        p09.draw_brass_grommet(d, pt, r_outer=max(3.5, 4.5 * sc))
    return canvas


def generate_120_poses():
    poses_catalog = []
    cols = 12  # 12 canonical poses
    rows = len(CHARACTER_RIG_SPECS)  # 10 character rigs
    cw, ch = 220, 270
    sheet = Image.new("RGBA", (cols * cw + 24, rows * ch + 90), (234, 229, 220, 255))
    draw = ImageDraw.Draw(sheet)
    draw.rectangle([0, 0, sheet.width, 68], fill=(24, 20, 18, 255))
    draw.text((24, 18), "WYGWYL 100X MULTI-CHARACTER POSE MATRIX -- 120 ASSEMBLED PUPPET POSES (RECTIFIED BONE AXES & NORMALIZED GIRTH)", fill=(245, 185, 66, 255))
    draw.text((24, 42), "Rectified Medial-Axis Bone Sockets + Auto-Girth Width Compensation | True Proportions (7.5H Adult vs 5.2H Child Age 6) | Cuff-Tuck Joints", fill=(195, 188, 176, 255))

    for r_idx, rig in enumerate(CHARACTER_RIG_SPECS):
        for c_idx, (pose_key, pose_label, pose_cfg) in enumerate(CANONICAL_12_POSES):
            idx = len(poses_catalog) + 1
            pid = f"pose_{idx:03d}_{rig['id']}_{pose_key}"
            im = render_character_pose(rig, pose_key, pose_cfg, cw=360, ch=420)
            im.save(os.path.join(POSES_OUT, f"{pid}.png"))

            x0 = 12 + c_idx * cw
            y0 = 78 + r_idx * ch
            draw.rectangle([x0 + 2, y0 + 2, x0 + cw - 2, y0 + ch - 2], fill=(242, 238, 230, 255), outline=(196, 188, 176, 255), width=1)
            # Ground line
            gy = y0 + int(368 * (240 / 420.0)) + 22
            draw.line([(x0 + 12, gy), (x0 + cw - 12, gy)], fill=(180, 172, 160, 255), width=2)

            thumb = im.resize((int(360 * (235 / 420.0)), 235), Image.Resampling.LANCZOS)
            sheet.alpha_composite(thumb, (x0 + (cw - thumb.width) // 2, y0 + 26))

            draw.rectangle([x0 + 2, y0 + 2, x0 + cw - 2, y0 + 23], fill=(32, 28, 24, 255))
            lbl_ascii = f"{rig['name'][:14]} - {pose_label[3:14]}".encode("ascii", "replace").decode("ascii")
            draw.text((x0 + 6, y0 + 6), lbl_ascii, fill=(240, 232, 215, 255))

            poses_catalog.append({
                "id": pid,
                "index": idx,
                "character_id": rig["id"],
                "character_name": rig["name"],
                "pose_key": pose_key,
                "pose_label": pose_label,
                "scale": rig["scale"],
                "view": pose_cfg["view"],
                "file": f"arena/parts/kit3/release_v2/poses_100x/{pid}.png",
            })

    atlas_path = os.path.join(ART_DIR, "scratch_100x_characters_poses_atlas.png")
    sheet.save(atlas_path)
    sheet.save(os.path.join(REL_DIR, "poses_100x_atlas.png"))
    with open(os.path.join(REL_DIR, "poses_100x_catalog.json"), "w") as f:
        json.dump({"total_poses": len(poses_catalog), "poses": poses_catalog}, f, indent=2)
    print(f"Saved 120 character poses and atlas -> {atlas_path}")
    return poses_catalog


if __name__ == "__main__":
    generate_108_faces()
    generate_120_poses()
