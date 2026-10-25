#!/usr/bin/env python3
"""
Visual-First Methodical Character Builder for Poem 09 ("Yet, Heard" — 37 Beats).
Iteration 5 — Direct 1:1 Pixel & Girth Calibration against `scratch_ref_vs_built_comparison.png`:

1. Exact 1:1 Component Dimensions (measured against P11-02, P09-01, P09-02, P09-05, P12-02 at 330px height):
   - Head (`head_*`): 44px collar-to-crown span (`y=108..64`), `girth=0.86` -> 48px crown-to-chin height x 37px width!
   - Torso (`torso_F` / `torso_3Q`): 98px collar-to-hem span (`y=108..206`), `girth=1.15` (front) / `1.12` (3Q) -> broad 95px athletic jacket chest!
   - Pelvis (`pelvis_F`): `y=190..238`, `girth=0.88` (front) / `0.82` (3Q) -> 74px hip width, tucked BEHIND the torso's ribbed waist hem!
   - Upper Arm & Forearm: `u_girth=1.24` (25px puffy jacket sleeve!), `f_girth=1.22` (22px forearm sleeve!).
   - Thigh & Shin: `t_girth=1.18` (36px jogger thigh!), `s_girth=1.12` (30px jogger shin!).
   - Hands:
     * Open / Point / Relaxed: 30px span, `h_girth=0.94` (32px long x 20px wide).
     * Closed Fists (`08 GOOD`, `22 DANCING`): 23px span, `h_girth=0.90` (25px long x 20px wide).
     * Phone / Cupped-Ear (`14 MOTHER`, `15 ABYSS`, `23 EARS`, `25 FATHER`): 25px span, `h_girth=0.84`.
   - Boots:
     * Front boots: 30px span (`y=346..376`), `b_girth=1.18`, angled outward in a grounded A-stance!
     * Profile boots: 43px diagonal span (`dx=+35, dy=+26`), `b_girth=1.05` (52px long x 34px tall Chelsea boots!).
   - Brass Grommet Brads: `r_outer=5.0px` (`10px` diameter hollow-center metallic eyelets) on the 10 primary limb sockets
     (2 Shoulders, 2 Elbows, 2 Hips, 2 Knees, 2 Ankles — matching `poet.09` and `poet.11` reference sheets!).
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
OUT_DIR = os.path.join(ROOT, "shots/arena/parts/kit3/release_v2/poem09_37_poses")
ART_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"
os.makedirs(OUT_DIR, exist_ok=True)

TS_DIR = os.path.join(ROOT, "shots/kits/packs/poet_tracksuit_v1/01_COMPONENTS")
PR_DIR = os.path.join(ROOT, "shots/arena/parts/kit3/v2/parts/poet.red_black_sunglasses")
WM_LIB = os.path.join(ROOT, "shots/weave/cast/man/library")
WM_PARTS = os.path.join(ROOT, "shots/weave/cast/man/parts")

_PART_CACHE = {}


from scipy.ndimage import binary_erosion, binary_dilation, binary_fill_holes, gaussian_filter


def remove_internal_tan_and_brass(arr, y_start=0, y_end=None, x_start=0, x_end=None):
    if y_end is None:
        y_end = arr.shape[0]
    if x_end is None:
        x_end = arr.shape[1]
    sub = arr[y_start:y_end, x_start:x_end]
    r, g, b, a = sub[:, :, 0].astype(int), sub[:, :, 1].astype(int), sub[:, :, 2].astype(int), sub[:, :, 3]
    # True gouache crimson red stripe has R >> G and G ≈ B (whereas tan/brass has high G > B)
    is_crimson = ((r - g) > 52) & (r > (g * 16) // 10) & ((g - b) < 42)
    is_tan_or_brass = (a > 35) & (~is_crimson) & (
        ((r > 58) & (g > 38) & ((r - b) > 12)) | ((r > 95) & (g > 90) & (b > 70))
    )
    sub[is_tan_or_brass, 0] = 23
    sub[is_tan_or_brass, 1] = 24
    sub[is_tan_or_brass, 2] = 28


def fill_internal_grommet_holes(arr):
    """
    Fills transparent punched holes inside clothing cards (like the shoulder grommet holes
    on 01_torso_front.png) with dark cloth [23, 24, 28, 255] so exterior border dilation
    never draws orange rings inside the shoulders or joints!
    """
    a = arr[:, :, 3] > 24
    filled = binary_fill_holes(a)
    holes = filled & (~a)
    arr[holes, 0] = 23
    arr[holes, 1] = 24
    arr[holes, 2] = 28
    arr[holes, 3] = 255


def add_outer_red_pant_stripe(arr, side="L"):
    """
    `11_thigh_L.png`, `12_shin_L.png`, `13_thigh_R.png`, `14_shin_R.png` in 01_COMPONENTS
    were exported without the outer crimson tracksuit stripe (`crimson_px = 0`), whereas
    every reference pose (P09-01, P09-02, P09-05, P11-02, P12-02) has a bold crimson stripe
    running down the outer edge of the thigh and shin. This paints the exact crimson stripe
    along the outer contour of the pant leg.
    """
    a = arr[:, :, 3] > 120
    H, W = a.shape
    for y in range(int(H * 0.12), int(H * 0.83)):
        xs = np.where(a[y])[0]
        if len(xs) < 40:
            continue
        if side == "L":
            # Viewer's left pant leg -> outer seam is on the left edge (xs[0])
            x0 = xs[0] + 10
            x1 = min(xs[-1], x0 + 26)
        else:
            # Viewer's right pant leg -> outer seam is on the right edge (xs[-1])
            x1 = xs[-1] - 10
            x0 = max(xs[0], x1 - 26)
        if x1 > x0:
            arr[y, x0:x1, 0] = 212
            arr[y, x0:x1, 1] = 34
            arr[y, x0:x1, 2] = 28


def strip_outer_kraft_margin(arr, max_px=18):
    """
    Strips the artificial outer tan kraft-paper margin around isolated clothing/boot cards
    right down to the painted dark ink outline while preserving 100% of crimson stripes.
    """
    a = arr[:, :, 3] > 24
    r = arr[:, :, 0].astype(int)
    g = arr[:, :, 1].astype(int)
    b = arr[:, :, 2].astype(int)
    inner = binary_erosion(a, iterations=max_px)
    rim = a & (~inner)
    is_crimson = ((r - g) > 52) & (r > (g * 16) // 10) & ((g - b) < 42)
    is_kraft = rim & (~is_crimson) & (r > 58) & (g > 34) & ((r - b) > 16)
    edge3 = a & (~binary_erosion(a, iterations=3))
    is_fringe = edge3 & (~is_crimson) & (r > 68) & (g > 48)
    arr[is_kraft | is_fringe, 3] = 0
    keep = binary_erosion(binary_dilation(arr[:, :, 3] > 24, iterations=1), iterations=1)
    arr[~keep, 3] = 0


def defringe_white_halo(arr, radius=4):
    a = arr[:, :, 3]
    trans = (a < 32)
    near_edge = trans.copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                near_edge |= np.roll(np.roll(trans, dy, axis=0), dx, axis=1)

    r = arr[:, :, 0].astype(int)
    g = arr[:, :, 1].astype(int)
    b = arr[:, :, 2].astype(int)
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    is_white_fringe = near_edge & (a > 0) & (r > 125) & (g > 125) & (b > 118) & ((cmax - cmin) < 34)
    arr[is_white_fringe, 3] = 0

    is_bright_rim = near_edge & (a > 0) & (r > 95) & (g > 95) & (b > 90) & ((cmax - cmin) < 26)
    arr[is_bright_rim, 0] = 28
    arr[is_bright_rim, 1] = 29
    arr[is_bright_rim, 2] = 33


def feather_ts_face_part(filename, erode_px=42, blur_sigma=8.0, clip_temple_tabs=False):
    im = Image.open(os.path.join(TS_DIR, filename)).convert("RGBA")
    arr = np.array(im, dtype=np.float32)
    H, W = arr.shape[:2]
    if clip_temple_tabs:
        arr[:, :int(W * 0.115), 3] = 0
        arr[:, int(W * 0.885):, 3] = 0
    fg = arr[:, :, 3] > 20
    inner = binary_erosion(fg, iterations=erode_px)
    soft_a = gaussian_filter(inner.astype(np.float32), sigma=blur_sigma)
    arr[:, :, 3] = np.clip(soft_a * 255.0, 0, 255)
    u8 = arr.astype(np.uint8)
    ys, xs = np.where(u8[:, :, 3] > 8)
    return Image.fromarray(u8[ys.min():ys.max() + 1, xs.min():xs.max() + 1])


def build_modular_head(mode="front_cheer_laugh"):
    """
    Assembles expressive heads from the high-res gouache facial components in `01_COMPONENTS`
    (`21_head_front_blank.png` + `24/25_brows` + `22/23_eyes` + `26_nose` + `27..30_mouth` + `31_sunglasses`)!
    """
    cache_key = f"__mod_head_{mode}"
    if cache_key in _PART_CACHE:
        return _PART_CACHE[cache_key].copy()

    hb = Image.open(os.path.join(TS_DIR, "21_head_front_blank.png")).convert("RGBA")
    arr = np.array(hb)
    defringe_white_halo(arr, radius=3)
    H, W = arr.shape[:2]
    arr[int(H * 0.82):, :, 3] = 0
    remove_internal_tan_and_brass(arr, int(H * 0.72), int(H * 0.82))
    # Fill the chin-beard connection zone (between lower lip and beard) so open/smiling mouths connect seamlessly to the beard
    yy, xx = np.ogrid[:H, :W]
    chin_patch = (yy > int(H * 0.58)) & (yy < int(H * 0.73)) & (np.abs(xx - W * 0.50) < W * 0.14) & (arr[:, :, 3] > 200)
    arr[chin_patch, 0] = 28
    arr[chin_patch, 1] = 24
    arr[chin_patch, 2] = 22

    base = Image.fromarray(arr).resize((195, 290), Image.Resampling.LANCZOS)
    cx = 98

    brows_file = "25_brows_raised.png" if "cheer" in mode or "sing" in mode else "24_brows_rest.png"
    b_im = feather_ts_face_part(brows_file, erode_px=42, blur_sigma=8.0).resize((94, 25), Image.Resampling.LANCZOS)
    base.alpha_composite(b_im, (cx - 47, 62 if "cheer" in mode else 66))

    e_im = feather_ts_face_part("22_eyes_open.png", erode_px=44, blur_sigma=8.0).resize((88, 29), Image.Resampling.LANCZOS)
    base.alpha_composite(e_im, (cx - 44, 84))

    n_im = feather_ts_face_part("26_nose_front.png", erode_px=42, blur_sigma=9.0).resize((35, 41), Image.Resampling.LANCZOS)
    base.alpha_composite(n_im, (cx - 17, 98))

    if "unmasked" not in mode:
        g_im = feather_ts_face_part("31_sunglasses_front.png", erode_px=22, blur_sigma=2.5, clip_temple_tabs=True).resize((114, 34), Image.Resampling.LANCZOS)
        base.alpha_composite(g_im, (cx - 57, 80))

    if "cheer" in mode:
        m_im = feather_ts_face_part("30_mouth_open_A.png", erode_px=38, blur_sigma=6.0).resize((72, 44), Image.Resampling.LANCZOS)
        base.alpha_composite(m_im, (cx - 36, 134))
    elif "sing" in mode:
        m_im = feather_ts_face_part("29_mouth_open_O.png", erode_px=38, blur_sigma=6.0).resize((68, 40), Image.Resampling.LANCZOS)
        base.alpha_composite(m_im, (cx - 34, 136))
    else:
        m_im = feather_ts_face_part("28_mouth_smile.png", erode_px=38, blur_sigma=6.0).resize((66, 31), Image.Resampling.LANCZOS)
        base.alpha_composite(m_im, (cx - 33, 138))

    _PART_CACHE[cache_key] = base
    return base.copy()


def load_clean_part(key):
    if key in _PART_CACHE:
        return _PART_CACHE[key].copy()

    if key == "head_cheer":
        im = build_modular_head("front_cheer_laugh")
        _PART_CACHE[key] = im
        return im.copy()

    paths = {
        "torso_F": os.path.join(TS_DIR, "01_torso_front.png"),
        "torso_B": os.path.join(TS_DIR, "02_torso_back.png"),
        "torso_3Q": os.path.join(TS_DIR, "01_torso_front.png"),
        "torso_P": os.path.join(PR_DIR, "body.profile.torso.png"),
        "waist": os.path.join(TS_DIR, "03_waist_link.png"),
        "hip_br": os.path.join(TS_DIR, "04_hip_bridge.png"),
        "seat_B": os.path.join(TS_DIR, "05_rear_seat_cover.png"),
        "pelvis_F": os.path.join(TS_DIR, "06_pelvis_front_cover.png"),
        "uarm_L": os.path.join(TS_DIR, "07_upper_arm_L.png"),
        "farm_L": os.path.join(TS_DIR, "08_forearm_L.png"),
        "uarm_R": os.path.join(TS_DIR, "09_upper_arm_R.png"),
        "farm_R": os.path.join(TS_DIR, "10_forearm_R.png"),
        "thigh_L": os.path.join(TS_DIR, "11_thigh_L.png"),
        "shin_L": os.path.join(TS_DIR, "12_shin_L.png"),
        "thigh_R": os.path.join(TS_DIR, "13_thigh_R.png"),
        "shin_R": os.path.join(TS_DIR, "14_shin_R.png"),
        "hand_rel_L": os.path.join(TS_DIR, "15_hand_relaxed_L.png"),
        "hand_rel_R": os.path.join(TS_DIR, "16_hand_relaxed_R.png"),
        "hand_op_L": os.path.join(TS_DIR, "17_hand_open_L.png"),
        "hand_op_R": os.path.join(TS_DIR, "18_hand_open_R.png"),
        "boot_F_L": os.path.join(TS_DIR, "19_boot_front_L.png"),
        "boot_F_R": os.path.join(TS_DIR, "20_boot_front_R.png"),
        "boot_heel_R": os.path.join(PR_DIR, "foot.R.heel_up.png"),
        "boot_toe_L": os.path.join(PR_DIR, "foot.L.toe_up.png"),
        "head_F": os.path.join(PR_DIR, "head.front.png"),
        "head_3Q": os.path.join(PR_DIR, "head.threequarter.png"),
        "head_P": os.path.join(WM_PARTS, "head.profile_R.png"),
        "head_smile": os.path.join(WM_LIB, "head/head.front.sunglasses_smile.png"),
        "head_sad_3Q": os.path.join(WM_LIB, "head/head.3q.sad.png"),
        "hand_smartphone": os.path.join(WM_LIB, "hand/hand.pocket.png"),
        "hand_cupped_ear": os.path.join(WM_LIB, "hand/hand.record.png"),
        "hand_point_R": os.path.join(PR_DIR, "hand.R.point.back.png"),
        "hand_fist_R": os.path.join(PR_DIR, "hand.R.fist.palm.png"),
        "hand_open_R": os.path.join(PR_DIR, "hand.R.open.palm.png"),
        "hand_open_back_R": os.path.join(PR_DIR, "hand.R.open.back.png"),
        "hand_rel_side_R": os.path.join(PR_DIR, "hand.R.relaxed.back.png"),
        "hand_flat_push_R": os.path.join(PR_DIR, "hand.R.flat_push.palm.png"),
    }
    im = Image.open(paths[key]).convert("RGBA")
    arr = np.array(im)
    H, W = arr.shape[:2]

    defringe_white_halo(arr, radius=4)

    if key in ("torso_F", "torso_3Q", "torso_B"):
        # Clip the protruding top neck-grommet tab (y < 0.085) and the two outer shoulder-cap
        # grommet ears around (324, 232) and (953, 232) so the shoulders slope smoothly!
        arr[:int(H * 0.085), :, 3] = 0
        yy, xx = np.ogrid[:H, :W]
        # Trim outer shoulder-cap bumps above the diagonal shoulder slope
        left_bump = (xx < int(W * 0.36)) & (yy < int(H * 0.19) - (xx - int(W * 0.22)) * 0.42)
        right_bump = (xx > int(W * 0.64)) & (yy < int(H * 0.19) - (int(W * 0.78) - xx) * 0.42)
        arr[left_bump | right_bump, 3] = 0
        strip_outer_kraft_margin(arr, max_px=20)
        fill_internal_grommet_holes(arr)
        remove_internal_tan_and_brass(arr, 0, H)
    elif key == "torso_P":
        arr[int(H * 0.93):, :, 3] = 0
        strip_outer_kraft_margin(arr, max_px=10)
        fill_internal_grommet_holes(arr)
        remove_internal_tan_and_brass(arr, 0, H)
    elif key in ("pelvis_F", "seat_B", "hip_br", "waist"):
        strip_outer_kraft_margin(arr, max_px=22)
        fill_internal_grommet_holes(arr)
        remove_internal_tan_and_brass(arr, 0, H)
    elif key in ("thigh_L", "thigh_R"):
        arr[:int(H * 0.12), :, 3] = 0
        arr[int(H * 0.83):, :, 3] = 0
        strip_outer_kraft_margin(arr, max_px=22)
        fill_internal_grommet_holes(arr)
        remove_internal_tan_and_brass(arr, 0, H)
        add_outer_red_pant_stripe(arr, side="L" if key == "thigh_L" else "R")
    elif key in ("uarm_L", "uarm_R"):
        arr[:int(H * 0.13), :, 3] = 0
        arr[int(H * 0.83):, :, 3] = 0
        strip_outer_kraft_margin(arr, max_px=22)
        fill_internal_grommet_holes(arr)
        remove_internal_tan_and_brass(arr, 0, H)
    elif key in ("farm_L", "farm_R"):
        arr[:int(H * 0.12), :, 3] = 0
        arr[int(H * 0.808):, :, 3] = 0
        strip_outer_kraft_margin(arr, max_px=22)
        fill_internal_grommet_holes(arr)
        remove_internal_tan_and_brass(arr, 0, H)
    elif key in ("shin_L", "shin_R"):
        arr[:int(H * 0.12), :, 3] = 0
        arr[int(H * 0.843):, :, 3] = 0
        strip_outer_kraft_margin(arr, max_px=22)
        fill_internal_grommet_holes(arr)
        remove_internal_tan_and_brass(arr, 0, H)
        add_outer_red_pant_stripe(arr, side="L" if key == "shin_L" else "R")
    elif key in ("hand_rel_L", "hand_rel_R"):
        arr[:int(H * 0.22), :, 3] = 0
        strip_outer_kraft_margin(arr, max_px=16)
    elif key in ("hand_op_L", "hand_op_R"):
        arr[int(H * 0.78):, :, 3] = 0
        strip_outer_kraft_margin(arr, max_px=16)
    elif key in ("boot_F_L", "boot_F_R"):
        arr[:int(H * 0.21), :, 3] = 0
        strip_outer_kraft_margin(arr, max_px=20)
        fill_internal_grommet_holes(arr)
        remove_internal_tan_and_brass(arr, 0, int(H * 0.45))
    elif key in ("boot_heel_R", "boot_toe_L"):
        strip_outer_kraft_margin(arr, max_px=6)
        fill_internal_grommet_holes(arr)
        remove_internal_tan_and_brass(arr, 0, int(H * 0.48), 0, int(W * 0.48))
    elif key in ("hand_point_R", "hand_fist_R", "hand_open_R", "hand_open_back_R", "hand_rel_side_R"):
        arr[:, :int(W * 0.21), 3] = 0
    elif key == "hand_smartphone":
        arr[int(H * 0.84):, :int(W * 0.38), 3] = 0
    elif key == "hand_cupped_ear":
        arr[int(H * 0.80):, :, 3] = 0
    elif key in ("head_F", "head_3Q", "head_P", "head_smile", "head_sad_3Q"):
        arr[int(H * 0.78):, :, 3] = 0
        remove_internal_tan_and_brass(arr, int(H * 0.68), int(H * 0.78))

    clean_im = Image.fromarray(arr)
    _PART_CACHE[key] = clean_im
    return clean_im.copy()


PART_ANCHORS = {
    "torso_F":          ((0.50, 0.10), (0.50, 0.89)),
    "torso_B":          ((0.50, 0.10), (0.50, 0.89)),
    "torso_3Q":         ((0.50, 0.10), (0.50, 0.89)),
    "torso_P":          ((0.48, 0.09), (0.50, 0.90)),
    "waist":            ((0.50, 0.28), (0.50, 0.72)),
    "hip_br":           ((0.50, 0.22), (0.50, 0.82)),
    "seat_B":           ((0.50, 0.18), (0.50, 0.85)),
    "pelvis_F":         ((0.50, 0.18), (0.50, 0.85)),
    "uarm_L":           ((0.50, 0.17), (0.50, 0.77)),
    "farm_L":           ((0.50, 0.18), (0.50, 0.77)),
    "uarm_R":           ((0.50, 0.17), (0.50, 0.77)),
    "farm_R":           ((0.50, 0.18), (0.50, 0.77)),
    "thigh_L":          ((0.50, 0.17), (0.50, 0.77)),
    "shin_L":           ((0.50, 0.19), (0.50, 0.78)),
    "thigh_R":          ((0.50, 0.17), (0.50, 0.77)),
    "shin_R":           ((0.50, 0.19), (0.50, 0.78)),
    "hand_rel_L":       ((0.52, 0.25), (0.52, 0.90)),
    "hand_rel_R":       ((0.52, 0.25), (0.52, 0.90)),
    "hand_op_L":        ((0.54, 0.75), (0.48, 0.10)),
    "hand_op_R":        ((0.54, 0.75), (0.48, 0.10)),
    "hand_point_R":     ((0.23, 0.48), (0.95, 0.44)),
    "hand_fist_R":      ((0.23, 0.50), (0.92, 0.50)),
    "hand_open_R":      ((0.23, 0.52), (0.95, 0.52)),
    "hand_open_back_R": ((0.23, 0.52), (0.95, 0.52)),
    "hand_rel_side_R":  ((0.23, 0.46), (0.93, 0.62)),
    "hand_smartphone":  ((0.32, 0.78), (0.72, 0.18)),
    "hand_cupped_ear":  ((0.48, 0.78), (0.48, 0.14)),
    "boot_F_L":         ((0.52, 0.27), (0.50, 0.93)),
    "boot_F_R":         ((0.48, 0.27), (0.50, 0.93)),
    "boot_heel_R":      ((0.22, 0.25), (0.90, 0.84)),
    "boot_toe_L":       ((0.22, 0.25), (0.90, 0.82)),
    "head_F":           ((0.50, 0.74), (0.50, 0.06)),
    "head_cheer":       ((0.50, 0.74), (0.50, 0.06)),
    "head_3Q":          ((0.44, 0.74), (0.50, 0.06)),
    "head_P":           ((0.42, 0.74), (0.52, 0.06)),
    "head_smile":       ((0.50, 0.74), (0.50, 0.06)),
    "head_sad_3Q":      ((0.44, 0.74), (0.50, 0.06)),
}


def paste_bone(canvas, part_key, pt_a, pt_b, girth=1.0, flip_x=False, brightness=1.0):
    im = load_clean_part(part_key)
    if brightness != 1.0:
        rgb = ImageEnhance.Brightness(im.convert("RGB")).enhance(brightness)
        im = Image.merge("RGBA", (*rgb.split(), im.split()[3]))

    W, H = im.size
    (nax, nay), (nbx, nby) = PART_ANCHORS[part_key]
    if flip_x:
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        nax = 1.0 - nax
        nbx = 1.0 - nbx

    ax, ay = nax * W, nay * H
    bx, by = nbx * W, nby * H
    cdx, cdy = bx - ax, by - ay
    c_span = max(8.0, math.hypot(cdx, cdy))
    theta_card = math.atan2(cdy, cdx)

    tdx, tdy = pt_b[0] - pt_a[0], pt_b[1] - pt_a[1]
    t_span = max(4.0, math.hypot(tdx, tdy))
    theta_target = math.atan2(tdy, tdx)

    scale_along = t_span / c_span
    scale_perp = scale_along * girth

    ca, sa = math.cos(theta_card), math.sin(theta_card)
    ct, st = math.cos(theta_target), math.sin(theta_target)

    inv_sa = 1.0 / max(1e-4, scale_along)
    inv_sp = 1.0 / max(1e-4, scale_perp)

    m00 = ca * (inv_sa * ct) - sa * (-inv_sp * st)
    m01 = ca * (inv_sa * st) - sa * (inv_sp * ct)
    m10 = sa * (inv_sa * ct) + ca * (-inv_sp * st)
    m11 = sa * (inv_sa * st) + ca * (inv_sp * ct)

    tx = ax - (m00 * pt_a[0] + m01 * pt_a[1])
    ty = ay - (m10 * pt_a[0] + m11 * pt_a[1])

    warped = im.transform(
        canvas.size,
        Image.Transform.AFFINE,
        (m00, m01, tx, m10, m11, ty),
        resample=Image.Resampling.BICUBIC,
    )
    canvas.alpha_composite(warped)


def fill_pelvis_core(canvas, poly_pts):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon(poly_pts, fill=(23, 24, 28, 255))
    canvas.alpha_composite(layer)


def apply_exterior_diecut_border(canvas):
    """
    Adds a clean, continuous warm kraft-paper die-cut outline ONLY around the exterior
    silhouette of the assembled character (matching P09-01, P11-02, P12-02 references),
    with zero internal joint seams.
    """
    arr = np.array(canvas)
    a = binary_fill_holes(arr[:, :, 3] > 36)
    outer1 = binary_dilation(a, iterations=1) & (~a)
    outer2 = binary_dilation(a, iterations=2) & (~binary_dilation(a, iterations=1))
    bg = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    bg_arr = np.array(bg)
    bg_arr[outer1] = [194, 140, 84, 230]
    bg_arr[outer2] = [142, 96, 52, 135]
    out = Image.fromarray(bg_arr)
    out.alpha_composite(canvas)
    return out


def draw_brass_grommet(draw, pt, r_outer=6.0):
    """
    Draws an authentic 12px-diameter hollow-center metallic brass eyelet matching the
    reference brads on `poet.09.main-poses.png` and `poet.11.main-poses.png`.
    """
    x, y = pt
    draw.ellipse([x - r_outer - 1.5, y - r_outer - 1.5, x + r_outer + 1.5, y + r_outer + 1.5],
                 fill=(20, 16, 12, 245))
    draw.ellipse([x - r_outer, y - r_outer, x + r_outer, y + r_outer],
                 fill=(228, 180, 68, 255), outline=(122, 82, 22, 255), width=1)
    draw.arc([x - r_outer + 1.0, y - r_outer + 1.0, x + r_outer - 1.0, y + r_outer - 1.0],
             start=200, end=340, fill=(255, 242, 175, 255), width=1)
    r_hole = r_outer * 0.44
    draw.ellipse([x - r_hole, y - r_hole, x + r_hole, y + r_hole],
                 fill=(24, 22, 20, 255), outline=(92, 64, 18, 255), width=1)


def unit_step(pt_from, pt_to, length):
    dx, dy = pt_to[0] - pt_from[0], pt_to[1] - pt_from[1]
    d = max(1e-4, math.hypot(dx, dy))
    return (pt_from[0] + dx / d * length, pt_from[1] + dy / d * length)


# Exact 1:1 hand spans & girths calibrated against P11-02 (35px open hand), P12-02 (29px fist), P09-02 (29px phone hand)
HAND_SPAN_PX = {
    "hand_rel_L":       32.0,
    "hand_rel_R":       32.0,
    "hand_op_L":        33.0,
    "hand_op_R":        33.0,
    "hand_open_R":      35.0,
    "hand_open_back_R": 35.0,
    "hand_point_R":     35.0,
    "hand_rel_side_R":  32.0,
    "hand_fist_R":      29.0,
    "hand_smartphone":  29.0,
    "hand_cupped_ear":  28.0,
}

HAND_GIRTH = {
    "hand_rel_L":       0.95,
    "hand_rel_R":       0.95,
    "hand_op_L":        0.92,
    "hand_op_R":        0.92,
    "hand_open_R":      0.98,
    "hand_open_back_R": 0.98,
    "hand_point_R":     0.98,
    "hand_rel_side_R":  0.96,
    "hand_fist_R":      1.04,
    "hand_smartphone":  0.90,
    "hand_cupped_ear":  0.90,
}


def draw_arm_chain(canvas, pins, uarm_key, farm_key, hand_key, sh, el, wr, tip_dir,
                   u_girth=1.02, f_girth=1.08, h_girth=None,
                   flip_u=False, flip_f=False, flip_h=False,
                   brightness=1.0, hand_over_cuff=False, pin_wrist=False):
    target_hand_len = HAND_SPAN_PX.get(hand_key, 32.0)
    if h_girth is None:
        h_girth = HAND_GIRTH.get(hand_key, 0.95)
    tip = unit_step(wr, tip_dir, target_hand_len)
    forearm_folded_up = (wr[1] < el[1] - 4)

    if not forearm_folded_up:
        if not hand_over_cuff:
            paste_bone(canvas, hand_key, wr, tip, girth=h_girth, flip_x=flip_h, brightness=brightness)
            paste_bone(canvas, farm_key, el, wr, girth=f_girth, flip_x=flip_f, brightness=brightness)
        else:
            paste_bone(canvas, farm_key, el, wr, girth=f_girth, flip_x=flip_f, brightness=brightness)
            paste_bone(canvas, hand_key, wr, tip, girth=h_girth, flip_x=flip_h, brightness=brightness)
        paste_bone(canvas, uarm_key, sh, el, girth=u_girth, flip_x=flip_u, brightness=brightness)
    else:
        paste_bone(canvas, uarm_key, sh, el, girth=u_girth, flip_x=flip_u, brightness=brightness)
        if not hand_over_cuff:
            paste_bone(canvas, hand_key, wr, tip, girth=h_girth, flip_x=flip_h, brightness=brightness)
            paste_bone(canvas, farm_key, el, wr, girth=f_girth, flip_x=flip_f, brightness=brightness)
        else:
            paste_bone(canvas, farm_key, el, wr, girth=f_girth, flip_x=flip_f, brightness=brightness)
            paste_bone(canvas, hand_key, wr, tip, girth=h_girth, flip_x=flip_h, brightness=brightness)

    pins.extend([sh, el])
    if pin_wrist:
        pins.append(wr)


def draw_leg_chain(canvas, pins, thigh_key, shin_key, boot_key, hip, kn, an, foot_tip,
                   t_girth=1.02, s_girth=1.02, b_girth=1.06,
                   flip_t=False, flip_s=False, flip_b=False, brightness=1.0):
    paste_bone(canvas, boot_key, an, foot_tip, girth=b_girth, flip_x=flip_b, brightness=brightness)
    paste_bone(canvas, shin_key, kn, an, girth=s_girth, flip_x=flip_s, brightness=brightness)
    paste_bone(canvas, thigh_key, hip, kn, girth=t_girth, flip_x=flip_t, brightness=brightness)
    pins.extend([hip, kn, an])


def render_pose_archetype(pose_id, show_pins=False, cw=360, ch=420):
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cx = cw // 2
    pins_front = []

    if pose_id in (
        "02-front-guide-stone",
        "04-6-rise-flex-reflect",
        "04-6-prayer-cup",
        "wince-standing-still",
        "phone-down-standing",
        "02-good-fists-up",
        "aw-the-universe-2",
        "open-arms-02-at-show",
        "welcome-new-day",
        "05-chest-lean-hurt",
    ):
        if pose_id == "02-good-fists-up":
            # Matching P12_02_CHEER wide celebratory power stance (knee span=150px, boot span=220px)!
            hip_dx, kn_dx, an_dx = 22, 46, 66
            hip_L, hip_R = (cx - hip_dx, 212), (cx + hip_dx, 212)
            kn_L,  kn_R  = (cx - kn_dx, 280), (cx + kn_dx, 280)
            an_L,  an_R  = (cx - an_dx, 340), (cx + an_dx, 340)
            # Outward-turned 3/4 boots matching P12-02!
            ft_L,  ft_R  = (cx - an_dx - 38, 368), (cx + an_dx + 38, 368)
            fill_pelvis_core(canvas, [(cx - 34, 188), (cx + 34, 188), (cx + 32, 236), (cx - 32, 236)])
            draw_leg_chain(canvas, pins_front, "thigh_R", "shin_R", "boot_toe_L", hip_R, kn_R, an_R, ft_R, b_girth=1.06)
            draw_leg_chain(canvas, pins_front, "thigh_L", "shin_L", "boot_toe_L", hip_L, kn_L, an_L, ft_L, b_girth=1.06, flip_b=True)
        else:
            if pose_id in ("welcome-new-day", "05-chest-lean-hurt", "open-arms-02-at-show"):
                hip_dx, kn_dx, an_dx, toe_dx = 21, 33, 42, 8
            else:
                # Matching P11_02_GUIDE grounded A-stance (knee span=99px, shin span=104px, boot span=123px)!
                hip_dx, kn_dx, an_dx, toe_dx = 20, 30, 36, 8

            hip_L = (cx - hip_dx, 212)
            hip_R = (cx + hip_dx, 212)
            kn_L  = (cx - kn_dx, 280)
            kn_R  = (cx + kn_dx, 280)
            an_L  = (cx - an_dx, 334)
            an_R  = (cx + an_dx, 334)
            ft_L  = (cx - an_dx - toe_dx, 373)
            ft_R  = (cx + an_dx + toe_dx, 373)

            fill_pelvis_core(canvas, [(cx - 32, 188), (cx + 32, 188), (cx + 30, 236), (cx - 30, 236)])
            draw_leg_chain(canvas, pins_front, "thigh_R", "shin_R", "boot_F_R", hip_R, kn_R, an_R, ft_R, b_girth=1.22)
            draw_leg_chain(canvas, pins_front, "thigh_L", "shin_L", "boot_F_L", hip_L, kn_L, an_L, ft_L, b_girth=1.22)

        # Pelvis sits ON TOP of upper thigh mounting tabs and BEHIND torso waist!
        paste_bone(canvas, "pelvis_F", (cx, 190), (cx, 238), girth=0.86)

        neck = (cx, 114)
        waist = (cx, 208)
        sh_L = (cx - 28, 134)
        sh_R = (cx + 28, 134)

        if pose_id == "02-front-guide-stone":
            el_L, wr_L, tip_L = (cx - 48, 174), (cx - 90, 168), (cx - 126, 158)
            el_R, wr_R, tip_R = (cx + 48, 174), (cx + 90, 168), (cx + 126, 158)
            h_L, h_R, flip_hL, flip_hR = "hand_open_R", "hand_open_R", True, False
        elif pose_id == "04-6-rise-flex-reflect":
            el_L, wr_L, tip_L = (cx - 52, 170), (cx - 82, 130), (cx - 100, 100)
            el_R, wr_R, tip_R = (cx + 52, 170), (cx + 82, 130), (cx + 100, 100)
            h_L, h_R, flip_hL, flip_hR = "hand_op_L", "hand_op_R", False, False
        elif pose_id == "04-6-prayer-cup":
            el_L, wr_L, tip_L = (cx - 48, 172), (cx - 72, 138), (cx - 88, 108)
            el_R, wr_R, tip_R = (cx + 48, 172), (cx + 72, 138), (cx + 88, 108)
            h_L, h_R, flip_hL, flip_hR = "hand_op_L", "hand_op_R", False, False
        elif pose_id == "wince-standing-still":
            el_L, wr_L, tip_L = (cx - 42, 174), (cx - 42, 218), (cx - 42, 250)
            el_R, wr_R, tip_R = (cx + 42, 174), (cx + 42, 218), (cx + 42, 250)
            h_L, h_R, flip_hL, flip_hR = "hand_rel_L", "hand_rel_R", False, False
        elif pose_id == "phone-down-standing":
            el_L, wr_L, tip_L = (cx - 42, 174), (cx - 44, 218), (cx - 46, 250)
            el_R, wr_R, tip_R = (cx + 42, 174), (cx + 42, 218), (cx + 42, 250)
            h_L, h_R, flip_hL, flip_hR = "hand_smartphone", "hand_rel_R", True, False
        elif pose_id == "02-good-fists-up":
            # Matching P12-02: upper arms go horizontally outward to wide elbows (cx ± 72, 128),
            # and forearms bend 90 deg upward to raised fists (cx ± 84, 68)!
            sh_L, sh_R = (cx - 28, 136), (cx + 28, 136)
            el_L, wr_L, tip_L = (cx - 72, 128), (cx - 84, 68), (cx - 86, 38)
            el_R, wr_R, tip_R = (cx + 72, 128), (cx + 84, 68), (cx + 86, 38)
            h_L, h_R, flip_hL, flip_hR = "hand_fist_R", "hand_fist_R", True, False
        elif pose_id == "aw-the-universe-2":
            el_L, wr_L, tip_L = (cx - 52, 168), (cx - 94, 180), (cx - 126, 186)
            el_R, wr_R, tip_R = (cx + 52, 168), (cx + 94, 180), (cx + 126, 186)
            h_L, h_R, flip_hL, flip_hR = "hand_open_R", "hand_open_R", True, False
        elif pose_id == "open-arms-02-at-show":
            el_L, wr_L, tip_L = (cx - 58, 146), (cx - 100, 142), (cx - 132, 134)
            el_R, wr_R, tip_R = (cx + 58, 146), (cx + 100, 142), (cx + 132, 134)
            h_L, h_R, flip_hL, flip_hR = "hand_open_R", "hand_open_R", True, False
        elif pose_id == "welcome-new-day":
            el_L, wr_L, tip_L = (cx - 62, 108), (cx - 98, 74), (cx - 126, 48)
            el_R, wr_R, tip_R = (cx + 62, 108), (cx + 98, 74), (cx + 126, 48)
            h_L, h_R, flip_hL, flip_hR = "hand_op_L", "hand_op_R", False, False
        elif pose_id == "05-chest-lean-hurt":
            neck = (cx, 116)
            el_L, wr_L, tip_L = (cx - 54, 168), (cx - 90, 196), (cx - 120, 212)
            el_R, wr_R, tip_R = (cx + 54, 168), (cx + 90, 196), (cx + 120, 212)
            h_L, h_R, flip_hL, flip_hR = "hand_open_R", "hand_open_R", True, False

        tip_L = unit_step(wr_L, tip_L, HAND_SPAN_PX[h_L])
        tip_R = unit_step(wr_R, tip_R, HAND_SPAN_PX[h_R])
        hg_L = HAND_GIRTH[h_L]
        hg_R = HAND_GIRTH[h_R]

        arms_hanging = pose_id in ("wince-standing-still", "phone-down-standing")
        if arms_hanging:
            paste_bone(canvas, h_R, wr_R, tip_R, girth=hg_R, flip_x=flip_hR)
            paste_bone(canvas, "farm_R", el_R, wr_R, girth=1.08)
            paste_bone(canvas, "uarm_R", sh_R, el_R, girth=1.02)
            paste_bone(canvas, h_L, wr_L, tip_L, girth=hg_L, flip_x=flip_hL)
            paste_bone(canvas, "farm_L", el_L, wr_L, girth=1.08)
            paste_bone(canvas, "uarm_L", sh_L, el_L, girth=1.02)
            paste_bone(canvas, "torso_F", neck, waist, girth=1.04)
        else:
            paste_bone(canvas, "uarm_R", sh_R, el_R, girth=1.02)
            paste_bone(canvas, "uarm_L", sh_L, el_L, girth=1.02)
            paste_bone(canvas, "torso_F", neck, waist, girth=1.04)
            paste_bone(canvas, h_R, wr_R, tip_R, girth=hg_R, flip_x=flip_hR)
            paste_bone(canvas, "farm_R", el_R, wr_R, girth=1.08)
            paste_bone(canvas, h_L, wr_L, tip_L, girth=hg_L, flip_x=flip_hL)
            paste_bone(canvas, "farm_L", el_L, wr_L, girth=1.08)

        # Goldilocks 1:1 Head (`48px` span -> `52px` crown-to-chin x `40px` width, snug on collar)!
        if pose_id in ("04-6-rise-flex-reflect", "04-6-prayer-cup", "open-arms-02-at-show", "05-chest-lean-hurt"):
            h_base = (cx, 113)
            h_crown = (cx + 5, 65) if pose_id != "05-chest-lean-hurt" else (cx - 5, 65)
            paste_bone(canvas, "head_3Q", h_base, h_crown, girth=0.87, flip_x=(pose_id == "05-chest-lean-hurt"))
        elif pose_id == "02-good-fists-up":
            # Ecstatic open-mouth laughing head tilted slightly back matching P12-02!
            paste_bone(canvas, "head_cheer", (cx, 114), (cx - 3, 62), girth=0.92)
        elif pose_id == "welcome-new-day":
            paste_bone(canvas, "head_smile", (cx, 113), (cx, 63), girth=0.90)
        elif pose_id in ("wince-standing-still", "phone-down-standing", "aw-the-universe-2"):
            paste_bone(canvas, "head_3Q", (cx, 113), (cx + 4, 65), girth=0.87)
        else:
            paste_bone(canvas, "head_F", (cx, 113), (cx, 65), girth=0.88)

        pins_front.extend([sh_L, el_L, sh_R, el_R])

    # -----------------------------------------------------------------------
    # ARCHETYPE B: HAND TO CHEST / FALTER (`02 REAL`, `11 HEARTBREAKS`, `17 WOUNDS`, `34 SHAKEN`)
    # Matching `P09_05_FALTER`:
    # - Clean rounded-shoulder 3/4 jacket torso (`girth=1.02`), wide grounded A-stance
    # - Right upper arm (`uarm_R`) at outer right shoulder `(cx+26, 134) -> (cx+48, 174)`
    # - Right forearm + open hand crossing horizontally over heart `(cx+48, 174) -> (cx+12, 158) -> (cx-18, 150)`
    # -----------------------------------------------------------------------
    elif pose_id == "falter-on-shoulder-contact-2":
        hip_L, hip_R = (cx - 18, 212), (cx + 18, 212)
        kn_L,  kn_R  = (cx - 32, 280), (cx + 30, 280)
        an_L,  an_R  = (cx - 44, 340), (cx + 36, 340)
        ft_L,  ft_R  = (cx,      368), (cx + 80, 368)

        fill_pelvis_core(canvas, [(cx - 30, 188), (cx + 30, 188), (cx + 28, 236), (cx - 28, 236)])
        draw_leg_chain(canvas, pins_front, "thigh_L", "shin_L", "boot_heel_R", hip_L, kn_L, an_L, ft_L, brightness=0.90)
        draw_leg_chain(canvas, pins_front, "thigh_R", "shin_R", "boot_toe_L", hip_R, kn_R, an_R, ft_R)
        paste_bone(canvas, "pelvis_F", (cx, 190), (cx, 238), girth=0.84)

        sh_L, el_L, wr_L, tip_L = (cx - 26, 134), (cx - 48, 176), (cx - 62, 216), (cx - 68, 246)
        paste_bone(canvas, "uarm_L", sh_L, el_L, girth=1.02)

        paste_bone(canvas, "torso_3Q", (cx - 2, 114), (cx, 208), girth=1.02)
        paste_bone(canvas, "head_3Q", (cx + 2, 113), (cx + 7, 65), girth=0.87)

        tip_L_cal = unit_step(wr_L, tip_L, HAND_SPAN_PX["hand_rel_L"])
        paste_bone(canvas, "hand_rel_L", wr_L, tip_L_cal, girth=HAND_GIRTH["hand_rel_L"])
        paste_bone(canvas, "farm_L", el_L, wr_L, girth=1.08)
        pins_front.extend([sh_L, el_L])

        sh_R, el_R, wr_R, tip_R = (cx + 26, 134), (cx + 48, 174), (cx + 12, 158), (cx - 18, 150)
        draw_arm_chain(canvas, pins_front, "uarm_R", "farm_R", "hand_open_R", sh_R, el_R, wr_R, tip_R, flip_h=True)

    # -----------------------------------------------------------------------
    # ARCHETYPE C: PHONE / HAND AT EAR (`14 MOTHER`, `15 ABYSS`, `23 EARS`, `25 FATHER`)
    # Matching `P09_02_PHONE`:
    # - Near upper arm angles down-left `(cx-24, 134) -> (cx-36, 172)`
    # - Near forearm folds UPWARD ON TOP `(cx-36, 172) -> (cx-14, 110)`
    # - 29px phone / cupped-ear hand sits right at the left ear `(cx-8, 84)`!
    # -----------------------------------------------------------------------
    elif pose_id in ("phone-palm-mother", "phone-palm-ears"):
        hip_L, hip_R = (cx - 16, 212), (cx + 16, 212)
        kn_L,  kn_R  = (cx - 24, 280), (cx + 24, 280)
        an_L,  an_R  = (cx - 28, 340), (cx + 26, 340)
        ft_L,  ft_R  = (cx + 16, 368), (cx + 70, 368)

        sh_R = (cx + 24, 134)
        if pose_id == "phone-palm-mother":
            el_R, wr_R, tip_R = (cx + 54, 152), (cx + 90, 138), (cx + 120, 126)
            draw_arm_chain(canvas, pins_front, "uarm_R", "farm_R", "hand_open_R", sh_R, el_R, wr_R, tip_R, brightness=0.92)
        else:
            el_R, wr_R, tip_R = (cx + 38, 174), (cx + 36, 216), (cx + 36, 246)
            draw_arm_chain(canvas, pins_front, "uarm_R", "farm_R", "hand_rel_R", sh_R, el_R, wr_R, tip_R, brightness=0.90)

        fill_pelvis_core(canvas, [(cx - 28, 188), (cx + 28, 188), (cx + 26, 236), (cx - 26, 236)])
        draw_leg_chain(canvas, pins_front, "thigh_L", "shin_L", "boot_heel_R", hip_L, kn_L, an_L, ft_L, brightness=0.90)
        draw_leg_chain(canvas, pins_front, "thigh_R", "shin_R", "boot_toe_L", hip_R, kn_R, an_R, ft_R)
        paste_bone(canvas, "pelvis_F", (cx, 190), (cx, 238), girth=0.82)

        paste_bone(canvas, "torso_3Q", (cx, 114), (cx, 208), girth=1.00)
        paste_bone(canvas, "head_3Q", (cx + 4, 113), (cx + 9, 65), girth=0.87)

        sh_L = (cx - 24, 134)
        el_L = (cx - 36, 172)
        wr_L = (cx - 16, 110)
        if pose_id == "phone-palm-mother":
            draw_arm_chain(canvas, pins_front, "uarm_L", "farm_L", "hand_smartphone",
                           sh_L, el_L, wr_L, (cx - 8, 82), flip_h=False, hand_over_cuff=True)
        else:
            draw_arm_chain(canvas, pins_front, "uarm_L", "farm_L", "hand_cupped_ear",
                           sh_L, el_L, wr_L, (cx - 10, 82), flip_h=True, hand_over_cuff=True)

    # -----------------------------------------------------------------------
    # ARCHETYPE D: REACHING / POINTING (`01 ACCEPTING`, `26 YONDERS`)
    # Matching `P09_01_REACH` & `poet.07` Panel 06 (forward lunge & torso lean!)
    # -----------------------------------------------------------------------
    elif pose_id in ("falter-reach-accepting", "a04-point-at"):
        hip_L, hip_R = (cx - 20, 210), (cx + 12, 210)
        kn_L,  kn_R  = (cx - 38, 278), (cx + 36, 274)
        an_L,  an_R  = (cx - 64, 340), (cx + 44, 340)
        ft_L,  ft_R  = (cx - 20, 368), (cx + 88, 368)

        sh_R = (cx + 30, 128)
        if pose_id == "falter-reach-accepting":
            el_R, wr_R, tip_R = (cx + 72, 124), (cx + 116, 108), (cx + 150, 94)
            draw_arm_chain(canvas, pins_front, "uarm_R", "farm_R", "hand_open_R", sh_R, el_R, wr_R, tip_R)
        else:
            el_R, wr_R, tip_R = (cx + 72, 122), (cx + 116, 114), (cx + 150, 108)
            draw_arm_chain(canvas, pins_front, "uarm_R", "farm_R", "hand_point_R", sh_R, el_R, wr_R, tip_R)

        fill_pelvis_core(canvas, [(cx - 32, 186), (cx + 26, 186), (cx + 26, 236), (cx - 32, 236)])
        draw_leg_chain(canvas, pins_front, "thigh_L", "shin_L", "boot_heel_R", hip_L, kn_L, an_L, ft_L, brightness=0.88)
        draw_leg_chain(canvas, pins_front, "thigh_R", "shin_R", "boot_toe_L", hip_R, kn_R, an_R, ft_R)
        paste_bone(canvas, "pelvis_F", (cx - 2, 188), (cx - 4, 236), girth=0.84)

        paste_bone(canvas, "torso_3Q", (cx + 12, 112), (cx - 4, 206), girth=1.00)
        paste_bone(canvas, "head_3Q", (cx + 14, 111), (cx + 24, 63), girth=0.87)

        sh_L, el_L, wr_L, tip_L = (cx - 14, 130), (cx - 42, 172), (cx - 60, 212), (cx - 68, 242)
        draw_arm_chain(canvas, pins_front, "uarm_L", "farm_L", "hand_rel_L", sh_L, el_L, wr_L, tip_L)

    # -----------------------------------------------------------------------
    # ARCHETYPE E: PROFILE / 3Q WALKS (`ex-disappears-gather`, `walk-the-room`, `03-walk-profile-colonnade`)
    # -----------------------------------------------------------------------
    elif pose_id in ("ex-disappears-gather", "walk-the-room", "03-walk-profile-colonnade"):
        hip_L, hip_R = (cx - 14, 212), (cx + 14, 212)
        kn_L,  kn_R  = (cx - 32, 280), (cx + 32, 280)
        an_L,  an_R  = (cx - 54, 340), (cx + 42, 340)
        ft_L,  ft_R  = (cx - 10, 368), (cx + 86, 368)

        sh_R = (cx + 22, 130)
        if pose_id == "ex-disappears-gather":
            el_R, wr_R, tip_R = (cx + 48, 164), (cx + 88, 156), (cx + 118, 148)
            draw_arm_chain(canvas, pins_front, "uarm_R", "farm_R", "hand_open_R", sh_R, el_R, wr_R, tip_R)
        elif pose_id == "walk-the-room":
            el_R, wr_R, tip_R = (cx + 52, 160), (cx + 94, 146), (cx + 124, 136)
            draw_arm_chain(canvas, pins_front, "uarm_R", "farm_R", "hand_open_R", sh_R, el_R, wr_R, tip_R)
        else:
            el_R, wr_R, tip_R = (cx + 44, 164), (cx + 80, 180), (cx + 108, 190)
            draw_arm_chain(canvas, pins_front, "uarm_R", "farm_R", "hand_rel_side_R", sh_R, el_R, wr_R, tip_R)

        fill_pelvis_core(canvas, [(cx - 26, 188), (cx + 26, 188), (cx + 26, 236), (cx - 26, 236)])
        draw_leg_chain(canvas, pins_front, "thigh_L", "shin_L", "boot_heel_R", hip_L, kn_L, an_L, ft_L, brightness=0.88)
        draw_leg_chain(canvas, pins_front, "thigh_R", "shin_R", "boot_toe_L", hip_R, kn_R, an_R, ft_R)
        paste_bone(canvas, "pelvis_F", (cx, 190), (cx, 238), girth=0.80)

        paste_bone(canvas, "torso_3Q", (cx + 2, 114), (cx, 208), girth=0.98)
        if pose_id == "03-walk-profile-colonnade":
            paste_bone(canvas, "head_P", (cx + 4, 113), (cx + 8, 65), girth=0.88)
        else:
            paste_bone(canvas, "head_3Q", (cx + 4, 113), (cx + 9, 65), girth=0.87)

        sh_L, el_L, wr_L, tip_L = (cx - 22, 134), (cx - 42, 174), (cx - 56, 214), (cx - 64, 244)
        draw_arm_chain(canvas, pins_front, "uarm_L", "farm_L", "hand_rel_L", sh_L, el_L, wr_L, tip_L)

    # -----------------------------------------------------------------------
    # ARCHETYPE F: GENTLE SLOW BENT-KNEE SOLO DANCE (`22 DANCING`)
    # -----------------------------------------------------------------------
    elif pose_id == "03-gentle-slow-dance":
        hip_L, hip_R = (cx - 16, 212), (cx + 16, 212)
        kn_L,  kn_R  = (cx + 2,  280), (cx + 34, 278)
        an_L,  an_R  = (cx - 28, 340), (cx + 12, 340)
        ft_L,  ft_R  = (cx + 16, 368), (cx + 56, 368)

        sh_R, el_R, wr_R, tip_R = (cx + 24, 134), (cx + 48, 168), (cx + 68, 124), (cx + 76, 94)
        draw_arm_chain(canvas, pins_front, "uarm_R", "farm_R", "hand_fist_R", sh_R, el_R, wr_R, tip_R)

        fill_pelvis_core(canvas, [(cx - 28, 188), (cx + 28, 188), (cx + 28, 236), (cx - 28, 236)])
        draw_leg_chain(canvas, pins_front, "thigh_L", "shin_L", "boot_heel_R", hip_L, kn_L, an_L, ft_L, brightness=0.88)
        draw_leg_chain(canvas, pins_front, "thigh_R", "shin_R", "boot_toe_L", hip_R, kn_R, an_R, ft_R)
        paste_bone(canvas, "pelvis_F", (cx, 190), (cx + 2, 238), girth=0.82)

        paste_bone(canvas, "torso_3Q", (cx - 2, 114), (cx, 208), girth=1.00)
        paste_bone(canvas, "head_3Q", (cx, 113), (cx + 5, 65), girth=0.87)

        sh_L, el_L, wr_L, tip_L = (cx - 26, 134), (cx - 54, 162), (cx - 72, 118), (cx - 78, 90)
        draw_arm_chain(canvas, pins_front, "uarm_L", "farm_L", "hand_fist_R", sh_L, el_L, wr_L, tip_L, flip_h=True)

    # -----------------------------------------------------------------------
    # ARCHETYPE G: KNEELING HEART SEATED (`21 FALL`, `31 TEARS`, `36 BROKEN`)
    # Matching `poet.04` Panel `04.2 HEART SEATED`:
    # - Broad kneeling base (`kn_L = cx-12`, `kn_R = cx+44`), substantial thighs/shins,
    #   clean rounded-shoulder 3/4 torso (`girth=1.04`), glowing heart emblem, and 48px head!
    # -----------------------------------------------------------------------
    elif pose_id == "04-2-heart-seated":
        hip_L, hip_R = (cx - 14, 274), (cx + 18, 274)
        kn_L,  kn_R  = (cx - 12, 352), (cx + 44, 352)
        an_L,  an_R  = (cx - 64, 344), (cx - 14, 346)
        ft_L,  ft_R  = (cx - 78, 374), (cx - 28, 374)

        paste_bone(canvas, "boot_heel_R", an_L, ft_L, girth=1.10, flip_x=True, brightness=0.82)
        paste_bone(canvas, "shin_L", kn_L, an_L, girth=1.02, brightness=0.82)
        paste_bone(canvas, "thigh_L", hip_L, kn_L, girth=1.06, brightness=0.86)

        paste_bone(canvas, "boot_heel_R", an_R, ft_R, girth=1.10, flip_x=True, brightness=0.90)
        paste_bone(canvas, "shin_R", kn_R, an_R, girth=1.04, brightness=0.92)
        paste_bone(canvas, "thigh_R", hip_R, kn_R, girth=1.08)
        pins_front.extend([hip_L, kn_L, hip_R, kn_R])

        fill_pelvis_core(canvas, [(cx - 28, 246), (cx + 28, 246), (cx + 30, 296), (cx - 30, 296)])
        paste_bone(canvas, "pelvis_F", (cx, 246), (cx + 2, 296), girth=0.86)

        sh_R, el_R, wr_R, tip_R = (cx + 26, 190), (cx + 46, 236), (cx + 30, 276), (cx + 24, 304)
        paste_bone(canvas, "uarm_R", sh_R, el_R, girth=1.04, brightness=0.92)

        paste_bone(canvas, "torso_3Q", (cx, 174), (cx + 2, 266), girth=1.04)
        # Glowing blue/white heart emblem on chest matching P04-02 (`04.2 HEART SEATED`)!
        edraw = ImageDraw.Draw(canvas)
        hx, hy = cx + 4, 212
        edraw.ellipse([hx - 9, hy - 9, hx + 9, hy + 9], fill=(24, 52, 112, 245), outline=(218, 176, 78, 255), width=2)
        edraw.ellipse([hx - 5, hy - 5, hx + 5, hy + 5], fill=(95, 168, 255, 255))
        edraw.ellipse([hx - 2, hy - 2, hx + 2, hy + 2], fill=(245, 252, 255, 255))

        paste_bone(canvas, "head_3Q", (cx + 4, 173), (cx + 11, 125), girth=0.87)

        tip_R_cal = unit_step(wr_R, tip_R, HAND_SPAN_PX["hand_rel_R"])
        paste_bone(canvas, "hand_rel_R", wr_R, tip_R_cal, girth=HAND_GIRTH["hand_rel_R"])
        paste_bone(canvas, "farm_R", el_R, wr_R, girth=1.08)
        pins_front.extend([sh_R, el_R])

        sh_L, el_L, wr_L, tip_L = (cx - 26, 190), (cx - 46, 236), (cx - 28, 276), (cx - 20, 304)
        draw_arm_chain(canvas, pins_front, "uarm_L", "farm_L", "hand_rel_L", sh_L, el_L, wr_L, tip_L)

    # -----------------------------------------------------------------------
    # ARCHETYPE H: KNEELING / LUNGING REACH (`35 BLEW`)
    # -----------------------------------------------------------------------
    elif pose_id == "falter-kneel-reach-blew":
        hip_L, hip_R = (cx - 12, 262), (cx + 16, 260)
        kn_L,  an_L,  ft_L = (cx - 12, 350), (cx - 64, 344), (cx - 78, 374)
        kn_R,  an_R,  ft_R = (cx + 50, 284), (cx + 46, 340), (cx + 90, 368)

        sh_R, el_R, wr_R, tip_R = (cx + 28, 178), (cx + 72, 182), (cx + 114, 164), (cx + 146, 150)
        draw_arm_chain(canvas, pins_front, "uarm_R", "farm_R", "hand_open_R", sh_R, el_R, wr_R, tip_R)

        paste_bone(canvas, "boot_heel_R", an_L, ft_L, girth=1.10, flip_x=True, brightness=0.86)
        paste_bone(canvas, "shin_L", kn_L, an_L, girth=1.02, brightness=0.86)
        paste_bone(canvas, "thigh_L", hip_L, kn_L, girth=1.06, brightness=0.88)
        pins_front.extend([hip_L, kn_L, an_L])

        fill_pelvis_core(canvas, [(cx - 24, 232), (cx + 28, 232), (cx + 44, 284), (cx - 20, 292)])
        paste_bone(canvas, "pelvis_F", (cx + 2, 234), (cx + 8, 286), girth=0.84)
        draw_leg_chain(canvas, pins_front, "thigh_R", "shin_R", "boot_toe_L", hip_R, kn_R, an_R, ft_R)

        paste_bone(canvas, "torso_3Q", (cx + 10, 162), (cx, 252), girth=1.02)
        paste_bone(canvas, "head_3Q", (cx + 14, 161), (cx + 21, 113), girth=0.87)

        sh_L, el_L, wr_L, tip_L = (cx - 12, 178), (cx - 42, 216), (cx - 60, 254), (cx - 68, 282)
        draw_arm_chain(canvas, pins_front, "uarm_L", "farm_L", "hand_rel_L", sh_L, el_L, wr_L, tip_L)

    canvas = apply_exterior_diecut_border(canvas)

    if show_pins:
        draw = ImageDraw.Draw(canvas)
        for pt in pins_front:
            draw_brass_grommet(draw, pt, r_outer=6.0)

    return canvas


POEM09_37_BEATS = [
    (1,  "0.0s",   "ACCEPTING",   "\"Accepting you'll never say nor ever feel,\"",               "falter-on-shoulder-contact",                 "09: reaching through the crowd toward the ex", "falter-reach-accepting"),
    (2,  "3.9s",   "REAL",        "\"Accepting you'll never say nor ever feel,\"",               "falter-on-shoulder-contact-2",               "09: falter, hand to the chest",                "falter-on-shoulder-contact-2"),
    (3,  "7.1s",   "GIVE",        "\"What isn't mine I still cannot give.\"",                    "02-front-guide-stone",                       "palms open: nothing to give (11)",             "02-front-guide-stone"),
    (4,  "9.7s",   "THINGS",      "\"I gather my things to go.\"",                               "ex-disappears",                              "09: gathering his things, walking with the",   "ex-disappears-gather"),
    (5,  "13.3s",  "MOON",        "\"Before I go,\"",                                            "04-6-rise-flex-reflect",                     "looking up at the moon (04)",                  "04-6-rise-flex-reflect"),
    (6,  "15.8s",  "SETTLE",      "\"we look at the moon the way we used to see it\"",           "wince-standing-still-on-with-the-shoulders-b","settle down, stillness (08)",                 "wince-standing-still"),
    (7,  "20.4s",  "TRAVEL",      "\"We talk for years and travel through time\"",               "walk-the-room",                              "travel through time (07 walk)",                "walk-the-room"),
    (8,  "22.6s",  "GOOD",        "\"We talk for years and travel through time\"",               "02",                                         "it feels so good: fists up, laughing (12)",    "02-good-fists-up"),
    (9,  "24.1s",  "OLD",         "\"and it feels so good.\"",                                   "aw-the-universe-2",                          "we grow old together: arms open low (05)",     "aw-the-universe-2"),
    (10, "27.2s",  "ALL",         "\"I believe maybe we could have it all,\"",                   "open-arms-02-at-show",                       "we could have it all: arms wide (06)",         "open-arms-02-at-show"),
    (11, "30.5s",  "HEARTBREAKS", "\"or swing in my humbled late nights and heartbreaks\"",      "falter-on-shoulder-contact-2",               "09: hand to the chest",                        "falter-on-shoulder-contact-2"),
    (12, "32.7s",  "UNCHANGING",  "\"and an end story unchanging.\"",                            "02-front-guide-stone",                       "an end story: still, open hands",              "02-front-guide-stone"),
    (13, "35.5s",  "GATHER",      "\"You help me gather my things to go.\"",                     "ex-disappears",                              "09: gathering his things",                     "ex-disappears-gather"),
    (14, "39.2s",  "MOTHER",      "\"Before I go,\"",                                            "phone-palm (flip)",                          "09: the call to mother, phone at the ear",     "phone-palm-mother"),
    (15, "41.5s",  "ABYSS",       "\"In tears, speaking of an abyss, she's never known.\"",      "phone-palm (flip)",                          "09: still on the phone",                       "phone-palm-mother"),
    (16, "43.0s",  "KNOWN",       "\"In tears, speaking of an abyss, she's never known.\"",      "wince-standing-still-on-with-the-shoulders-b","she's never known: the phone down, standing", "phone-down-standing"),
    (17, "46.9s",  "WOUNDS",      "\"And we talk for years and we close wounds,\"",              "falter-on-shoulder-contact-2",               "09: close wounds, hand to the chest",          "falter-on-shoulder-contact-2"),
    (18, "52.2s",  "PRAYER",      "\"and we explain my way of birth then and even after prayer.\"","04-6-rise-flex-reflect",                   "after prayer: palms up, face up (04)",         "04-6-prayer-cup"),
    (19, "55.4s",  "GIVE",        "\"What isn't mine I still cannot give.\"",                    "02-front-guide-stone",                       "palms open: nothing to give",                  "02-front-guide-stone"),
    (20, "58.8s",  "MOON",        "\"We grow old together with the moon looking at us\"",        "04-6-rise-flex-reflect",                     "the moon looking at us",                       "04-6-rise-flex-reflect"),
    (21, "62.6s",  "FALL",        "\"As my tears fall between the creases and faith,\"",         "04-2-heart-seated",                          "tears fall: down on one knee (04 kneel)",      "04-2-heart-seated"),
    (22, "65.4s",  "DANCING",     "\"As my tears fall between the creases and faith,\"",         "03-gentle-slow-bent-knee-dance-alone",       "dancing on my own (08)",                       "03-gentle-slow-dance"),
    (23, "67.6s",  "EARS",        "\"dancing on my own,\"",                                      "phone-palm (flip)",                          "09: maternal ears, hand at the ear",           "phone-palm-ears"),
    (24, "71.4s",  "GATHER",      "\"She watches us gather my things to go.\"",                  "ex-disappears",                              "09: gathering his things to go",               "ex-disappears-gather"),
    (25, "75.0s",  "FATHER",      "\"Before I go, I call on my father.\"",                       "phone-palm (flip)",                          "09: the call to father",                       "phone-palm-mother"),
    (26, "78.5s",  "YONDERS",     "\"Summon his calming demeanor from the yonders\"",            "a04-point-at",                               "from the yonders: pointing far (07)",          "a04-point-at"),
    (27, "80.5s",  "WALK",        "\"Summon his calming demeanor from the yonders\"",            "03-walk-profile-colonnade",                  "we walk for years (11 walk)",                  "03-walk-profile-colonnade"),
    (28, "82.9s",  "SUNRISES",    "\"and we walk for years and travel east toward the sunrises\"","welcome-new-day",                           "toward the sunrises: welcome the day (11)",    "welcome-new-day"),
    (29, "85.5s",  "FOOTSTEPS",   "\"and retrace his footsteps now and then,\"",                 "walk-the-room",                              "retrace his footsteps (07 walk)",              "walk-the-room"),
    (30, "90.1s",  "MOON",        "\"Guiding a settling down moon the way it used to leave\"",   "04-6-rise-flex-reflect",                     "guiding a settling down moon",                 "04-6-rise-flex-reflect"),
    (31, "92.2s",  "TEARS",       "\"Guiding a settling down moon the way it used to leave\"",   "04-2-heart-seated",                          "my tears fell: kneel",                         "04-2-heart-seated"),
    (32, "96.8s",  "HARBOR",      "\"and wave shadows of the inner harbor.\"",                   "02-front-guide-stone",                       "the inner harbor: rise, still",                "02-front-guide-stone"),
    (33, "98.5s",  "STROLL",      "\"and wave shadows of the inner harbor.\"",                   "walk-the-room",                              "we stroll (07 walk)",                          "walk-the-room"),
    (34, "102.2s", "SHAKEN",      "\"hearted and shaken.\"",                                     "falter-on-shoulder-contact-2",               "09: hearted and shaken, hand to the chest",    "falter-on-shoulder-contact-2"),
    (35, "105.3s", "BLEW",        "\"Someone borrowed and someone blew.\"",                      "falter-on-shoulder-contact",                 "09: reaching after the one who blew",          "falter-kneel-reach-blew"),
    (36, "106.7s", "BROKEN",      "\"Someone borrowed and someone blew.\"",                      "04-2-heart-seated",                          "yet broken: kneel",                            "04-2-heart-seated"),
    (37, "108.0s", "HURT",        "\"Yet broken, yet hurt.\"",                                   "05-chest-lean-opened-back-head-inhale-back-a","yet hurt / heard: head back, arms open (08)", "05-chest-lean-hurt"),
]


def make_silhouette(rgba_im):
    arr = np.array(rgba_im)
    sil = np.zeros_like(arr)
    mask = arr[:, :, 3] > 32
    sil[mask] = [20, 24, 30, 255]
    return Image.fromarray(sil)


def build_ref_comparison_sheet():
    p09 = Image.open(os.path.join(ROOT, "shots/kits/packs/poem_09/02_ACTIONS_AND_POSES/poet.09.main-poses.png")).convert("RGBA")
    p11 = Image.open(os.path.join(ROOT, "shots/kits/packs/poem_11/02_ACTIONS_AND_POSES/poet.11.main-poses.png")).convert("RGBA")
    p12 = Image.open(os.path.join(ROOT, "shots/kits/packs/poem_12/02_ACTIONS_AND_POSES/poet.12.main-poses.png")).convert("RGBA")
    p04 = Image.open(os.path.join(ROOT, "shots/kits/packs/poem_04/02_ACTIONS_AND_POSES/poet.04.main-poses.png")).convert("RGBA")

    pairs = [
        ("01 ACCEPTING (P09-01)",      p09.crop((5, 95, 325, 480)),     315, "falter-reach-accepting"),
        ("02 REAL / FALTER (P09-05)",  p09.crop((5, 528, 305, 935)),    270, "falter-on-shoulder-contact-2"),
        ("14 MOTHER / PHONE (P09-02)", p09.crop((435, 88, 705, 485)),   315, "phone-palm-mother"),
        ("03 GIVE / GUIDE (P11-02)",   p11.crop((520, 88, 965, 492)),   315, "02-front-guide-stone"),
        ("08 GOOD / CHEER (P12-02)",   p12.crop((985, 76, 1295, 490)),  340, "02-good-fists-up"),
        ("21 FALL / KNEEL (P04-02)",   p04.crop((780, 110, 1115, 492)), 255, "04-2-heart-seated"),
    ]

    col_w, row_h = 920, 430
    comp = Image.new("RGBA", (col_w * 2, row_h * 3), (235, 232, 224, 255))
    cdraw = ImageDraw.Draw(comp)

    for idx, (title, ref_crop, ref_h, pid) in enumerate(pairs):
        c, r = idx % 2, idx // 2
        x0, y0 = c * col_w, r * row_h
        cdraw.rectangle([x0 + 4, y0 + 4, x0 + col_w - 4, y0 + row_h - 4], fill=(244, 242, 236, 255), outline=(185, 180, 170, 255), width=2)
        floor_y = y0 + 394
        cdraw.line([x0 + 12, floor_y, x0 + col_w - 12, floor_y], fill=(160, 154, 142, 255), width=3)

        rw, rh = ref_crop.size
        scale = ref_h / float(rh)
        ref_resized = ref_crop.resize((int(rw * scale), ref_h), Image.Resampling.LANCZOS)
        rx = x0 + 20
        ry = floor_y - ref_h
        comp.alpha_composite(ref_resized, (rx, ry))

        im_pinned = render_pose_archetype(pid, show_pins=True)
        im_clean = render_pose_archetype(pid, show_pins=False)
        comp.alpha_composite(im_pinned, (x0 + 305, floor_y - 374))
        comp.alpha_composite(im_clean, (x0 + 585, floor_y - 374))

        cdraw.text((x0 + 16, y0 + 10), f"{title} -- ORIGINAL REF vs BUILT (PINNED & CLEAN)", fill=(20, 20, 20, 255))
        cdraw.text((x0 + 30, y0 + 32), "1. ORIGINAL REFERENCE", fill=(140, 40, 40, 255))
        cdraw.text((x0 + 355, y0 + 32), "2. BUILT (WITH BRASS BRADS)", fill=(30, 90, 40, 255))
        cdraw.text((x0 + 645, y0 + 32), "3. BUILT (CLEAN)", fill=(30, 60, 130, 255))

    comp_path = os.path.join(ART_DIR, "scratch_ref_vs_built_comparison.png")
    comp.save(comp_path)
    print("Saved side-by-side reference comparison:", comp_path)


def build_all():
    build_ref_comparison_sheet()

    unique_ids = []
    for b in POEM09_37_BEATS:
        if b[6] not in unique_ids:
            unique_ids.append(b[6])

    cols = 4
    rows = (len(unique_ids) + cols - 1) // cols
    pw, ph = 520, 440
    proof = Image.new("RGBA", (cols * pw, rows * ph), (225, 222, 214, 255))
    pdraw = ImageDraw.Draw(proof)

    for idx, pid in enumerate(unique_ids):
        c, r = idx % cols, idx // cols
        x0, y0 = c * pw, r * ph
        pdraw.rectangle([x0 + 2, y0 + 2, x0 + pw - 2, y0 + ph - 2], outline=(180, 175, 165, 255), width=2)
        pdraw.line([x0 + 6, y0 + 392, x0 + pw - 6, y0 + 392], fill=(168, 162, 150, 255), width=4)

        im_clean = render_pose_archetype(pid, show_pins=False)
        im_sil = make_silhouette(im_clean).resize((160, 186), Image.Resampling.LANCZOS)
        proof.alpha_composite(im_clean, (x0 + 10, y0 + 20))
        proof.alpha_composite(im_sil, (x0 + 345, y0 + 195))
        pdraw.text((x0 + 12, y0 + 8), f"[{idx+1:02d}] {pid}", fill=(20, 20, 20, 255))
        pdraw.text((x0 + 350, y0 + 176), "GATE 2: SILHOUETTE", fill=(90, 85, 78, 255))

    proof_path = os.path.join(ART_DIR, "scratch_18_modular_poses_proof.png")
    proof.save(proof_path)
    print("Saved 21-pose proof:", proof_path)

    for mode_name, show_pins in [("clean", False), ("pinned", True)]:
        scols, srows = 6, 7
        cw, ch = 300, 390
        stage_h = 285
        sheet = Image.new("RGBA", (scols * cw, srows * ch), (242, 240, 236, 255))
        sdraw = ImageDraw.Draw(sheet)

        for beat_num, ts, kw, lyric, red_pose, desc, pid in POEM09_37_BEATS:
            idx = beat_num - 1
            c, r = idx % scols, idx // scols
            x0, y0 = c * cw, r * ch

            sdraw.rectangle([x0, y0, x0 + cw - 2, y0 + stage_h], fill=(224, 221, 212, 255))
            sdraw.rectangle([x0, y0 + stage_h - 8, x0 + cw - 2, y0 + stage_h], fill=(172, 168, 158, 255))
            sdraw.rectangle([x0, y0 + stage_h + 1, x0 + cw - 2, y0 + ch - 2], fill=(252, 252, 250, 255))
            sdraw.rectangle([x0, y0, x0 + cw - 2, y0 + ch - 2], outline=(210, 207, 198, 255), width=1)

            char_im = render_pose_archetype(pid, show_pins=show_pins)
            if mode_name == "clean":
                char_im.save(os.path.join(OUT_DIR, f"pose_{beat_num:02d}_{kw.lower()}.png"))

            target_w = int(360 * 0.74)
            target_h = int(420 * 0.74)
            char_scaled = char_im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            px = x0 + (cw - target_w) // 2
            py = y0 + stage_h - int(372 * 0.74) - 2
            sheet.alpha_composite(char_scaled, (px, py))

            ty = y0 + stage_h + 6
            sdraw.text((x0 + 6, ty), f"{beat_num:02d}  {ts} {kw}", fill=(18, 18, 18, 255))
            sdraw.text((x0 + 6, ty + 18), lyric[:46] + ("..." if len(lyric) > 46 else ""), fill=(90, 90, 90, 255))
            sdraw.text((x0 + 6, ty + 34), red_pose, fill=(155, 44, 44, 255))
            sdraw.text((x0 + 6, ty + 50), desc[:46], fill=(105, 105, 105, 255))

        out_sheet = os.path.join(OUT_DIR, f"poem09_37_contact_sheet_{mode_name}.png")
        art_sheet = os.path.join(ART_DIR, f"poem09_37_contact_sheet_{mode_name}.png")
        sheet.save(out_sheet)
        sheet.save(art_sheet)
        print("Saved:", out_sheet)


if __name__ == "__main__":
    build_all()
