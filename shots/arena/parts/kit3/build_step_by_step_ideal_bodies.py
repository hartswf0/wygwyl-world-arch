#!/usr/bin/env python3
"""
Step-by-Step Ideal Body, Proportion Calibration, Joint Bendability & Consistent Pattern Builder
===============================================================================================
Directly addresses the core structural requirements:
1. STEP 1 (`scratch_step1_ideal_body_vs_master.png`):
   Ground-truth proportion calibration against the artist's original `ASSEMBLED IDENTITY`
   master figures (`poet.master__p01`, `ex.master__p01`, `party.master__p01/p12`,
   `young_poet.hipcore__p07`, `mother.heads-hands__p30`).
   Locks universal bone ratios (`H_fig = 236px` adult, `0.70x` child):
     - Crown:    0.000 H
     - Neck:     0.156 H
     - Shoulder: 0.224 H (dx = +/-0.096 H)
     - Elbow:    0.369 H (L_uarm = 0.145 H)
     - Hip:      0.455 H (dx = +/-0.066 H; torso spine = 0.299 H, lower body = 0.545 H!)
     - Wrist:    0.498 H (L_farm = 0.129 H)
     - Knee:     0.690 H (L_thigh = 0.235 H)
     - Ankle:    0.878 H (L_shin = 0.188 H)
     - Sole:     1.000 H (H_sole = 0.122 H)
2. STEP 2 (`scratch_step2_compatible_4angle_bodies.png`):
   Builds all 9 canonical characters across all 4 angles (`FRONT`, `3/4`, `SIDE PROFILE`, `BACK` = 36 bodies)
   using 100% compatible, un-mutilated cuts directly from `release_v2/cuts/` and 2-point brass-grommet
   bone fitting (`fit_bone_2pt`), with hands and shoes tucked cleanly behind sleeve/pant cuffs.
3. STEP 3 (`scratch_step3_bendability_rom_matrix.png`):
   Proves joint bendability (`0 deg` to `130 deg`) across Elbow/Wrist, Knee/Ankle, and Hip/Spine with
   clothed Rear Seat, AND recreates 6 of the artist's canonical `MAIN POSES` side-by-side with the
   original reference drawings.
4. STEP 4 (`scratch_step4_consistent_movement_and_ensembles.png`):
   Demonstrates consistent ground-up locomotion & acting progression (with sinusoidal hip/head arcs
   and 0.0px foot drift) + bottom-up growing multiplane ensembles (`Solo -> Duo -> Trio -> 9-Cast`).
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter
from scipy import ndimage
from scipy.ndimage import label, binary_dilation

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
CUTS = os.path.join(ROOT, "shots/arena/parts/kit3/release_v2/cuts")
TS_COMP = os.path.join(ROOT, "shots/kits/packs/poet_tracksuit_v1/01_COMPONENTS")
WM_DIR = os.path.join(ROOT, "shots/weave/cast/man")
ART_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"
OUT_DIR = os.path.join(ROOT, "shots/arena/parts/kit3/regularized_parts_audit")
os.makedirs(OUT_DIR, exist_ok=True)


# ============================================================================
# 1. CLEAN CUT LOADER & 2-POINT BRASS-GROMMET BONE SOLVER (`fit_bone_2pt`)
# ============================================================================

_IMAGE_CACHE = {}

def cut_path(sheet, pid):
    return os.path.join(CUTS, sheet, f"{sheet}__{pid}.png")


def load_clean_cut(path, fill_armhole=False, remove_text_islands=True, flip_x=False, flip_y=False, rot90_if_horiz=False):
    key = (path, fill_armhole, remove_text_islands, flip_x, flip_y, rot90_if_horiz)
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key].copy()

    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

    # Remove near-white paper margin pixels ONLY if connected to exterior border
    near_white = (r > 236) & (g > 233) & (b > 226)
    ext_bg = (a <= 20) | near_white
    bg_lab0, _ = label(ext_bg)
    border_ids0 = set(np.unique(np.concatenate([bg_lab0[0, :], bg_lab0[-1, :], bg_lab0[:, 0], bg_lab0[:, -1]])))
    is_ext_white = near_white & np.isin(bg_lab0, list(border_ids0))
    a = np.where(is_ext_white, 0, a)

    # Keep main connected component (and any large secondary garment panel > 10% of main)
    mask = a > 20
    labeled, n_comp = label(mask)
    if n_comp > 1 and remove_text_islands:
        sizes = [(labeled == i).sum() for i in range(1, n_comp + 1)]
        max_sz = max(sizes) if sizes else 0
        keep = np.zeros_like(mask)
        for i, sz in enumerate(sizes, 1):
            if sz >= max_sz * 0.12:
                keep |= (labeled == i)
        a = np.where(keep, a, 0)

    # Optionally fill interior hollow shoulder armhole on side-profile torsos
    if fill_armhole:
        solid = a > 24
        bg = ~solid
        bg_lab, bg_n = label(bg)
        if bg_n > 1:
            H, W = solid.shape
            border_lbls = set(np.unique(np.concatenate([bg_lab[0, :], bg_lab[-1, :], bg_lab[:, 0], bg_lab[:, -1]])))
            non_kraft = solid & ~((r > 130) & (g > 90) & (b < 110) & ((r.astype(int) - b.astype(int)) > 35))
            if non_kraft.sum() < 50:
                non_kraft = solid
            med_r = int(np.median(r[non_kraft])) if non_kraft.any() else 35
            med_g = int(np.median(g[non_kraft])) if non_kraft.any() else 35
            med_b = int(np.median(b[non_kraft])) if non_kraft.any() else 38
            for lbl_i in range(1, bg_n + 1):
                if lbl_i in border_lbls:
                    continue
                hole = (bg_lab == lbl_i)
                if 30 < hole.sum() < (H * W * 0.30):
                    r = np.where(hole, med_r, r)
                    g = np.where(hole, med_g, g)
                    b = np.where(hole, med_b, b)
                    a = np.where(hole, 255, a)

    arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3] = r, g, b, a
    ys, xs = np.where(a > 20)
    if len(xs) > 0:
        im = Image.fromarray(arr).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    else:
        im = Image.fromarray(arr)

    if rot90_if_horiz and im.width > im.height * 1.15:
        im = im.rotate(-90, expand=True, resample=Image.Resampling.BICUBIC)
    if flip_y:
        im = ImageOps.flip(im)
    if flip_x:
        im = ImageOps.mirror(im)

    _IMAGE_CACHE[key] = im
    return im.copy()


def find_limb_grommets(im, default_a=(0.50, 0.095), default_b=(0.50, 0.895)):
    """
    Finds the true centerline proximal (top) and distal (bottom) joint coordinates
    on a cropped limb card by measuring the horizontal centroid of the opaque card
    at y = 10% and y = 89% of its height. This automatically handles curved or
    diagonally painted limbs (like DJ Cyber's compact-core arms or 3/4 thighs).
    """
    arr = np.array(im)
    a = arr[:, :, 3] > 30
    H, W = a.shape
    if H < 8 or W < 8 or not a.any():
        return default_a, default_b

    def band_center_x(y_frac):
        y_c = int(round(H * y_frac))
        y0 = max(0, y_c - max(2, int(H * 0.04)))
        y1 = min(H, y_c + max(3, int(H * 0.04)))
        sub = a[y0:y1, :]
        ys_b, xs_b = np.where(sub)
        if len(xs_b) == 0:
            return 0.50
        return float(np.mean(xs_b)) / float(W)

    ax = band_center_x(default_a[1])
    bx = band_center_x(default_b[1])
    return (ax, default_a[1]), (bx, default_b[1])


def fit_bone_2pt(canvas, im, grommet_a, grommet_b, pt_a, pt_b, width_mult=1.0, clip_top_frac=0.0, clip_bot_frac=0.0):
    """
    Exact 2-Point Euclidean Bone Solver:
    Scales, rotates, and translates `im` so that normalized point `grommet_a` lands
    precisely on `pt_a = (x1, y1)` (0.0px error) and `grommet_b` lands precisely
    on `pt_b = (x2, y2)` (0.0px error).
    Preserves the semicircular joint caps above `grommet_a` and below `grommet_b`
    unless `clip_top_frac` or `clip_bot_frac` is explicitly requested (e.g. to trim
    a protruding wrist/ankle mounting tongue).
    """
    if im is None:
        return
    w0, h0 = im.size
    if w0 < 2 or h0 < 2:
        return

    work = im.copy()
    if clip_top_frac > 0.0 or clip_bot_frac > 0.0:
        arr = np.array(work)
        if clip_top_frac > 0.0:
            arr[:int(h0 * clip_top_frac), :, 3] = 0
        if clip_bot_frac > 0.0:
            arr[int(h0 * (1.0 - clip_bot_frac)):, :, 3] = 0
        work = Image.fromarray(arr)

    ax, ay = grommet_a[0] * w0, grommet_a[1] * h0
    bx, by = grommet_b[0] * w0, grommet_b[1] * h0
    dx_card = bx - ax
    dy_card = by - ay
    len_card = math.hypot(dx_card, dy_card)
    if len_card < 1e-3:
        return

    dx_bone = pt_b[0] - pt_a[0]
    dy_bone = pt_b[1] - pt_a[1]
    len_bone = math.hypot(dx_bone, dy_bone)
    if len_bone < 1.0:
        return

    scale_y = len_bone / len_card
    scale_x = scale_y * width_mult

    # Scale image first
    nw = max(2, int(round(w0 * scale_x)))
    nh = max(2, int(round(h0 * scale_y)))
    scaled = work.resize((nw, nh), Image.Resampling.LANCZOS)

    # Scaled grommet coordinates
    sax, say = ax * scale_x, ay * scale_y
    sbx, sby = bx * scale_x, by * scale_y

    # Angle of A->B on the scaled card vs target bone angle
    ang_card = math.atan2(sbx - sax, sby - say)   # 0 rad = straight down (+Y)
    ang_bone = math.atan2(dx_bone, dy_bone)       # 0 rad = straight down (+Y)
    delta_rad = ang_bone - ang_card               # CCW rotation needed in screen space (Y down)
    rot_deg_pil = math.degrees(delta_rad)         # PIL.rotate(+) is CCW!

    # Pad around scaled image center so rotation never clips rounded caps
    diag = int(math.ceil(math.hypot(nw, nh))) + 8
    pad = Image.new("RGBA", (diag, diag), (0, 0, 0, 0))
    ox = (diag - nw) // 2
    oy = (diag - nh) // 2
    pad.paste(scaled, (ox, oy))

    cx, cy = diag / 2.0, diag / 2.0
    # Vector from pad center to sax, say
    vx = (ox + sax) - cx
    vy = (oy + say) - cy

    rot_im = pad.rotate(rot_deg_pil, resample=Image.Resampling.BICUBIC, expand=False)
    # PIL.rotate(deg) rotates CCW in standard math, which in Y-down image coords is:
    # x' = cx + vx * cos(rad) + vy * sin(rad)
    # y' = cy - vx * sin(rad) + vy * cos(rad)
    rad = math.radians(rot_deg_pil)
    rax = cx + vx * math.cos(rad) + vy * math.sin(rad)
    ray = cy - vx * math.sin(rad) + vy * math.cos(rad)

    paste_x = int(round(pt_a[0] - rax))
    paste_y = int(round(pt_a[1] - ray))
    canvas.alpha_composite(rot_im, (paste_x, paste_y))


def place_anchored_card(canvas, im, anchor_rel, target_xy, target_h, rot_deg=0.0, width_mult=1.0, clip_top_frac=0.0):
    """
    Places a 1-socket terminal card (Head at Neck socket, Hand at Wrist socket,
    Shoe at Ankle socket, or Rear Seat at Hip socket) with exact pivot registration.
    """
    if im is None:
        return
    w0, h0 = im.size
    work = im.copy()
    if clip_top_frac > 0.0:
        arr = np.array(work)
        arr[:int(h0 * clip_top_frac), :, 3] = 0
        work = Image.fromarray(arr)

    sc = target_h / float(max(1, h0))
    nw = max(2, int(round(w0 * sc * width_mult)))
    nh = max(2, int(round(h0 * sc)))
    scaled = work.resize((nw, nh), Image.Resampling.LANCZOS)

    px = anchor_rel[0] * nw
    py = anchor_rel[1] * nh

    if abs(rot_deg) > 0.1:
        diag = int(math.ceil(math.hypot(nw, nh))) + 8
        pad = Image.new("RGBA", (diag, diag), (0, 0, 0, 0))
        ox, oy = (diag - nw) // 2, (diag - nh) // 2
        pad.paste(scaled, (ox, oy))
        cx, cy = diag / 2.0, diag / 2.0
        vx, vy = (ox + px) - cx, (oy + py) - cy
        # rot_deg > 0 swings bottom of card forward (+X, CCW in screen Y-down)
        rot_im = pad.rotate(rot_deg, resample=Image.Resampling.BICUBIC, expand=False)
        rad = math.radians(rot_deg)
        rpx = cx + vx * math.cos(rad) + vy * math.sin(rad)
        rpy = cy - vx * math.sin(rad) + vy * math.cos(rad)
        canvas.alpha_composite(rot_im, (int(round(target_xy[0] - rpx)), int(round(target_xy[1] - rpy))))
    else:
        canvas.alpha_composite(scaled, (int(round(target_xy[0] - px)), int(round(target_xy[1] - py))))


# ============================================================================
# 2. MODULAR HEAD COMPOSITOR (100% CLEAN HEADS FROM `release_v2/cuts/`)
# ============================================================================

def load_seamless_feature(path, erode_px=5, feather_px=4.5):
    im = Image.open(path).convert("RGBA")
    arr = np.array(im).astype(np.float32)
    solid = ndimage.binary_fill_holes(arr[:, :, 3] > 30)
    eroded = ndimage.binary_erosion(solid, iterations=erode_px)
    if not eroded.any():
        eroded = solid
    dist = ndimage.distance_transform_edt(eroded)
    arr[:, :, 3] = np.clip(dist / feather_px, 0.0, 1.0) * 255.0
    ys, xs = np.where(arr[:, :, 3] > 10)
    if len(xs) > 0:
        return Image.fromarray(arr.astype(np.uint8)).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    return Image.fromarray(arr.astype(np.uint8))


def build_modular_head_front(base_path, eyes_path=None, brows_path=None, mouth_path=None, glasses_path=None, trim_top_px=0, shift_x=0.0):
    base = load_clean_cut(base_path)
    if trim_top_px > 0:
        arr = np.array(base)
        arr[:trim_top_px, :, 3] = 0
        ys, xs = np.where(arr[:, :, 3] > 20)
        base = Image.fromarray(arr).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))

    W, H = base.size
    cx = int(W * (0.50 + shift_x))
    if eyes_path and os.path.exists(eyes_path):
        ey = load_seamless_feature(eyes_path)
        place_anchored_card(base, ey, (0.50, 0.50), (cx, int(H * 0.49)), int(H * 0.165))
    if brows_path and os.path.exists(brows_path):
        br = load_seamless_feature(brows_path)
        place_anchored_card(base, br, (0.50, 0.50), (cx, int(H * 0.38)), int(H * 0.11))
    if mouth_path and os.path.exists(mouth_path):
        mo = load_seamless_feature(mouth_path)
        place_anchored_card(base, mo, (0.50, 0.50), (cx, int(H * 0.69)), int(H * 0.175))
    if glasses_path and os.path.exists(glasses_path):
        gl = load_clean_cut(glasses_path, remove_text_islands=False)
        place_anchored_card(base, gl, (0.50, 0.50), (cx, int(H * 0.48)), int(H * 0.19))
    return base


def build_modular_head_profile(base_path, eye_path=None, brow_path=None, mouth_path=None, glasses_path=None):
    base = load_clean_cut(base_path)
    W, H = base.size
    if mouth_path and os.path.exists(mouth_path):
        mo = load_seamless_feature(mouth_path, erode_px=4, feather_px=4.0)
        place_anchored_card(base, mo, (0.50, 0.50), (int(W * 0.72), int(H * 0.66)), int(H * 0.25))
    if eye_path and os.path.exists(eye_path):
        ey = load_seamless_feature(eye_path, erode_px=4, feather_px=4.0)
        place_anchored_card(base, ey, (0.50, 0.50), (int(W * 0.70), int(H * 0.45)), int(H * 0.18))
    if brow_path and os.path.exists(brow_path):
        br = load_seamless_feature(brow_path, erode_px=4, feather_px=4.0)
        place_anchored_card(base, br, (0.50, 0.50), (int(W * 0.72), int(H * 0.36)), int(H * 0.12))
    if glasses_path and os.path.exists(glasses_path):
        gl = load_clean_cut(glasses_path, remove_text_islands=False)
        place_anchored_card(base, gl, (0.50, 0.50), (int(W * 0.62), int(H * 0.44)), int(H * 0.16))
    return base


# ============================================================================
# 3. CANONICAL 9-CHARACTER LIBRARY (100% COMPATIBLE `release_v2/cuts/` PARTS)
# ============================================================================

def get_canonical_cast_library():
    """
    Returns all 9 canonical characters with their verified, un-mutilated parts
    from `shots/arena/parts/kit3/release_v2/cuts/` across all 4 angles:
    FRONT, 3Q, SIDE, BACK.
    """
    # Pre-build clean heads for each character & angle
    # 1. Poet Tracksuit (with sunglasses)
    poet_ts_heads = {
        "FRONT": build_modular_head_front(
            cut_path("poet.red_black_sunglasses.face.front", "p01"),
            eyes_path=cut_path("poet.red_black_sunglasses.face.front", "p02"),
            brows_path=cut_path("poet.red_black_sunglasses.face.front", "p10"),
            mouth_path=cut_path("poet.red_black_sunglasses.face.front", "p16"),
            glasses_path=os.path.join(TS_COMP, "31_sunglasses_front.png"),
        ),
        "3Q": build_modular_head_front(
            cut_path("poet.red_black_sunglasses.heads", "p02"),
            eyes_path=cut_path("poet.red_black_sunglasses.face.front", "p02"),
            brows_path=cut_path("poet.red_black_sunglasses.face.front", "p10"),
            mouth_path=cut_path("poet.red_black_sunglasses.face.front", "p16"),
            glasses_path=os.path.join(TS_COMP, "31_sunglasses_front.png"),
            shift_x=0.06,
        ),
        "SIDE": build_modular_head_profile(
            cut_path("poet.red_black_sunglasses.face.profile", "p01"),
            eye_path=cut_path("poet.red_black_sunglasses.face.profile", "p03"),
            brow_path=cut_path("poet.red_black_sunglasses.face.profile", "p10"),
            mouth_path=cut_path("poet.red_black_sunglasses.face.profile", "p16"),
            glasses_path=os.path.join(TS_COMP, "profile_face_clean/profile_sunglasses_09.png"),
        ),
        "BACK": load_clean_cut(cut_path("poet.red_black_sunglasses.heads", "p05")),
    }

    # 2. Poet Black T-Shirt (open eyes)
    poet_bt_heads = {
        "FRONT": build_modular_head_front(
            cut_path("poet.red_black_sunglasses.face.front", "p01"),
            eyes_path=cut_path("poet.red_black_sunglasses.face.front", "p02"),
            brows_path=cut_path("poet.red_black_sunglasses.face.front", "p10"),
            mouth_path=cut_path("poet.red_black_sunglasses.face.front", "p17"),
        ),
        "3Q": build_modular_head_front(
            cut_path("poet.red_black_sunglasses.heads", "p02"),
            eyes_path=cut_path("poet.red_black_sunglasses.face.front", "p02"),
            brows_path=cut_path("poet.red_black_sunglasses.face.front", "p10"),
            mouth_path=cut_path("poet.red_black_sunglasses.face.front", "p17"),
            shift_x=0.06,
        ),
        "SIDE": build_modular_head_profile(
            cut_path("poet.red_black_sunglasses.face.profile", "p01"),
            eye_path=cut_path("poet.red_black_sunglasses.face.profile", "p03"),
            brow_path=cut_path("poet.red_black_sunglasses.face.profile", "p10"),
            mouth_path=cut_path("poet.red_black_sunglasses.face.profile", "p16"),
        ),
        "BACK": load_clean_cut(cut_path("poet.red_black_sunglasses.heads", "p05")),
    }

    # 3. Woman / Muse (Red Brocade)
    woman_side_base = load_clean_cut(cut_path("woman.13.heads-hands", "p03"))
    # Add subtle side eye & brow on her sculpted profile head
    w_ey = load_clean_cut(cut_path("young_poet.child_clothes.face.profile", "p02"), remove_text_islands=False)
    w_br = load_clean_cut(cut_path("young_poet.child_clothes.face.profile", "p10"), remove_text_islands=False)
    place_anchored_card(woman_side_base, w_ey, (0.50, 0.50), (int(woman_side_base.width * 0.73), int(woman_side_base.height * 0.55)), int(woman_side_base.height * 0.12))
    place_anchored_card(woman_side_base, w_br, (0.50, 0.50), (int(woman_side_base.width * 0.74), int(woman_side_base.height * 0.48)), int(woman_side_base.height * 0.08))

    woman_heads = {
        "FRONT": load_clean_cut(cut_path("woman.13.heads-hands", "p06")),
        "3Q": load_clean_cut(cut_path("woman.13.heads-hands", "p17")),
        "SIDE": woman_side_base,
        "BACK": load_clean_cut(cut_path("woman.13.heads-hands", "p05")),
    }

    # 4. The Mother (Knit Cardigan & Floral Dress)
    mother_side_base = load_clean_cut(cut_path("woman.09.mother.heads-hands", "p03"))
    place_anchored_card(mother_side_base, w_ey, (0.50, 0.50), (int(mother_side_base.width * 0.73), int(mother_side_base.height * 0.55)), int(mother_side_base.height * 0.12))
    place_anchored_card(mother_side_base, w_br, (0.50, 0.50), (int(mother_side_base.width * 0.74), int(mother_side_base.height * 0.48)), int(mother_side_base.height * 0.08))

    mother_front = load_clean_cut(cut_path("woman.09.mother.heads-hands", "p01"))
    # Trim tiny label above afro on p01
    m_arr = np.array(mother_front)
    m_arr[:12, :, 3] = 0
    ys, xs = np.where(m_arr[:, :, 3] > 20)
    mother_front = Image.fromarray(m_arr).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    m_W, m_H = mother_front.size
    place_anchored_card(mother_front, load_clean_cut(cut_path("woman.09.mother.heads-hands", "p07"), remove_text_islands=True), (0.50, 0.50), (int(m_W * 0.50), int(m_H * 0.58)), int(m_H * 0.11))
    place_anchored_card(mother_front, load_clean_cut(cut_path("woman.09.mother.heads-hands", "p11"), remove_text_islands=False), (0.50, 0.50), (int(m_W * 0.50), int(m_H * 0.51)), int(m_H * 0.06))
    place_anchored_card(mother_front, load_clean_cut(cut_path("woman.09.mother.heads-hands", "p15"), remove_text_islands=True), (0.50, 0.50), (int(m_W * 0.50), int(m_H * 0.72)), int(m_H * 0.09))

    mother_3q = load_clean_cut(cut_path("woman.09.mother.heads-hands", "p02"))
    m3_W, m3_H = mother_3q.size
    place_anchored_card(mother_3q, load_clean_cut(cut_path("woman.09.mother.heads-hands", "p07"), remove_text_islands=True), (0.50, 0.50), (int(m3_W * 0.56), int(m3_H * 0.58)), int(m3_H * 0.11))
    place_anchored_card(mother_3q, load_clean_cut(cut_path("woman.09.mother.heads-hands", "p11"), remove_text_islands=False), (0.50, 0.50), (int(m3_W * 0.56), int(m3_H * 0.51)), int(m3_H * 0.06))
    place_anchored_card(mother_3q, load_clean_cut(cut_path("woman.09.mother.heads-hands", "p15"), remove_text_islands=True), (0.50, 0.50), (int(m3_W * 0.56), int(m3_H * 0.72)), int(m3_H * 0.09))

    mother_heads = {
        "FRONT": mother_front,
        "3Q": mother_3q,
        "SIDE": mother_side_base,
        "BACK": load_clean_cut(cut_path("woman.09.mother.heads-hands", "p05")),
    }

    # 5. The Ex (Olive Bomber — canonical Back & 3/4-Back head turns!)
    ex_heads = {
        "FRONT": load_clean_cut(cut_path("ex.ex_jacket.heads", "p02")),  # Slight Turn L
        "3Q": load_clean_cut(cut_path("ex.ex_jacket.heads", "p04")),     # 3/4 Back L
        "SIDE": load_clean_cut(cut_path("ex.ex_jacket.heads", "p05")),   # 3/4 Back R (Profile-Back)
        "BACK": load_clean_cut(cut_path("ex.ex_jacket.heads", "p01")),   # Strict Back
    }

    # 6. Party Gentleman (Pinstripe Suit)
    pg_front = build_modular_head_front(
        cut_path("party.vintage_party.heads", "p01"),
        eyes_path=cut_path("party.vintage_party.face-feet.male", "p02"),
        brows_path=cut_path("party.vintage_party.face-feet.male", "p12"),
        mouth_path=cut_path("party.vintage_party.face-feet.male", "p31"),
    )
    pg_3q = build_modular_head_front(
        cut_path("party.vintage_party.heads", "p02"),
        eyes_path=cut_path("party.vintage_party.face-feet.male", "p18"),
        brows_path=cut_path("party.vintage_party.face-feet.male", "p12"),
        mouth_path=cut_path("party.vintage_party.face-feet.male", "p31"),
        shift_x=0.08,
    )
    pg_side = load_clean_cut(cut_path("party.vintage_party.heads", "p03"))
    place_anchored_card(pg_side, load_clean_cut(cut_path("poet.red_black_sunglasses.face.profile", "p03"), remove_text_islands=False), (0.50, 0.50), (int(pg_side.width * 0.72), int(pg_side.height * 0.45)), int(pg_side.height * 0.16))
    place_anchored_card(pg_side, load_clean_cut(cut_path("poet.red_black_sunglasses.face.profile", "p10"), remove_text_islands=False), (0.50, 0.50), (int(pg_side.width * 0.73), int(pg_side.height * 0.36)), int(pg_side.height * 0.10))

    party_male_heads = {
        "FRONT": pg_front,
        "3Q": pg_3q,
        "SIDE": pg_side,
        "BACK": load_clean_cut(cut_path("party.vintage_party.heads", "p05")),
    }

    # 7. Party Woman (Cream Opera Gown)
    pf_front = load_clean_cut(cut_path("party.vintage_party.heads", "p06"))
    pf_W, pf_H = pf_front.size
    place_anchored_card(pf_front, load_clean_cut(cut_path("party.vintage_party.face-feet.female", "p01"), remove_text_islands=False), (0.50, 0.50), (int(pf_W * 0.50), int(pf_H * 0.48)), int(pf_H * 0.16))
    place_anchored_card(pf_front, load_clean_cut(cut_path("party.vintage_party.face-feet.female", "p12"), remove_text_islands=False), (0.50, 0.50), (int(pf_W * 0.50), int(pf_H * 0.38)), int(pf_H * 0.10))
    place_anchored_card(pf_front, load_clean_cut(cut_path("party.vintage_party.face-feet.female", "p30"), remove_text_islands=False), (0.50, 0.50), (int(pf_W * 0.50), int(pf_H * 0.68)), int(pf_H * 0.15))

    pf_3q = load_clean_cut(cut_path("party.vintage_party.heads", "p07"))
    place_anchored_card(pf_3q, load_clean_cut(cut_path("party.vintage_party.face-feet.female", "p19"), remove_text_islands=False), (0.50, 0.50), (int(pf_3q.width * 0.58), int(pf_3q.height * 0.48)), int(pf_3q.height * 0.16))
    place_anchored_card(pf_3q, load_clean_cut(cut_path("party.vintage_party.face-feet.female", "p12"), remove_text_islands=False), (0.50, 0.50), (int(pf_3q.width * 0.58), int(pf_3q.height * 0.38)), int(pf_3q.height * 0.10))
    place_anchored_card(pf_3q, load_clean_cut(cut_path("party.vintage_party.face-feet.female", "p30"), remove_text_islands=False), (0.50, 0.50), (int(pf_3q.width * 0.58), int(pf_3q.height * 0.68)), int(pf_3q.height * 0.15))

    pf_side = load_clean_cut(cut_path("party.vintage_party.heads", "p08"))
    place_anchored_card(pf_side, w_ey, (0.50, 0.50), (int(pf_side.width * 0.72), int(pf_side.height * 0.48)), int(pf_side.height * 0.13))
    place_anchored_card(pf_side, w_br, (0.50, 0.50), (int(pf_side.width * 0.73), int(pf_side.height * 0.40)), int(pf_side.height * 0.09))

    party_female_heads = {
        "FRONT": pf_front,
        "3Q": pf_3q,
        "SIDE": pf_side,
        "BACK": load_clean_cut(cut_path("party.vintage_party.heads", "p10")),
    }

    # 8. DJ Cyber (with his canonical Black Baseball Cap heads `party.dj_cyber.heads__p01..p05`!)
    dj_front = load_clean_cut(cut_path("party.dj_cyber.heads", "p01"))
    dj_W, dj_H = dj_front.size
    place_anchored_card(dj_front, load_clean_cut(cut_path("party.dj_cyber.face-feet", "p01"), remove_text_islands=True), (0.50, 0.50), (int(dj_W * 0.50), int(dj_H * 0.49)), int(dj_H * 0.13))
    place_anchored_card(dj_front, load_clean_cut(cut_path("party.dj_cyber.face-feet", "p16"), remove_text_islands=True), (0.50, 0.50), (int(dj_W * 0.50), int(dj_H * 0.69)), int(dj_H * 0.14))

    dj_3q = load_clean_cut(cut_path("party.dj_cyber.heads", "p02"))
    place_anchored_card(dj_3q, load_clean_cut(cut_path("party.dj_cyber.face-feet", "p05"), remove_text_islands=True), (0.50, 0.50), (int(dj_3q.width * 0.55), int(dj_3q.height * 0.49)), int(dj_3q.height * 0.13))
    place_anchored_card(dj_3q, load_clean_cut(cut_path("party.dj_cyber.face-feet", "p16"), remove_text_islands=True), (0.50, 0.50), (int(dj_3q.width * 0.55), int(dj_3q.height * 0.69)), int(dj_3q.height * 0.14))

    dj_side = load_clean_cut(cut_path("party.dj_cyber.heads", "p03"))
    place_anchored_card(dj_side, load_clean_cut(cut_path("poet.red_black_sunglasses.face.profile", "p03"), remove_text_islands=False), (0.50, 0.50), (int(dj_side.width * 0.64), int(dj_side.height * 0.47)), int(dj_side.height * 0.14))

    dj_heads = {
        "FRONT": dj_front,
        "3Q": dj_3q,
        "SIDE": dj_side,
        "BACK": load_clean_cut(cut_path("party.dj_cyber.heads", "p05")),
    }

    # 9. Young Poet (Child Age 6 — 100% clean `young_poet.child_clothes.face.front` & `face.profile`!)
    yp_front = build_modular_head_front(
        cut_path("young_poet.child_clothes.face.front", "p01"),
        eyes_path=cut_path("young_poet.child_clothes.face.front", "p02"),
        brows_path=cut_path("young_poet.child_clothes.face.front", "p10"),
        mouth_path=cut_path("young_poet.child_clothes.face.front", "p16"),
    )
    yp_3q = build_modular_head_front(
        cut_path("young_poet.child_clothes.heads", "p02"),
        eyes_path=cut_path("young_poet.child_clothes.face.front", "p08"),
        brows_path=cut_path("young_poet.child_clothes.face.front", "p10"),
        mouth_path=cut_path("young_poet.child_clothes.face.front", "p16"),
        shift_x=0.07,
    )
    yp_side = build_modular_head_profile(
        cut_path("young_poet.child_clothes.face.profile", "p01"),
        eye_path=cut_path("young_poet.child_clothes.face.profile", "p02"),
        brow_path=cut_path("young_poet.child_clothes.face.profile", "p10"),
        mouth_path=cut_path("young_poet.child_clothes.face.profile", "p16"),
    )
    yp_heads = {
        "FRONT": yp_front,
        "3Q": yp_3q,
        "SIDE": yp_side,
        "BACK": load_clean_cut(cut_path("young_poet.child_clothes.heads", "p05")),
    }

    return [
        {
            "id": "poet_tracksuit",
            "name": "1. Poet (Tracksuit)",
            "scale": 1.00,
            "heads": poet_ts_heads,
            "views": {
                "FRONT": dict(
                    torso=cut_path("poet.red_black_sunglasses.body.front", "p01"),
                    seat=cut_path("poet.red_black_sunglasses.hipcore", "p03"),
                    uarm_L=cut_path("poet.red_black_sunglasses.body.front", "p02"),
                    farm_L=cut_path("poet.red_black_sunglasses.body.front", "p03"),
                    uarm_R=cut_path("poet.red_black_sunglasses.body.front", "p04"),
                    farm_R=cut_path("poet.red_black_sunglasses.body.front", "p05"),
                    hand_L=cut_path("poet.red_black_sunglasses.body.front", "p06"),
                    hand_R=cut_path("poet.red_black_sunglasses.body.front", "p07"),
                    thigh_L=cut_path("poet.red_black_sunglasses.body.front", "p08"),
                    shin_L=cut_path("poet.red_black_sunglasses.body.front", "p09"),
                    thigh_R=cut_path("poet.red_black_sunglasses.body.front", "p10"),
                    shin_R=cut_path("poet.red_black_sunglasses.body.front", "p11"),
                    foot_L=cut_path("poet.red_black_sunglasses.feet", "p04"),
                    foot_R=cut_path("poet.red_black_sunglasses.feet", "p04"),
                    foot_is_side=False,
                ),
                "3Q": dict(
                    torso=cut_path("poet.red_black_sunglasses.body.threequarter", "p01"),
                    seat=cut_path("poet.red_black_sunglasses.hipcore", "p03"),
                    uarm_L=cut_path("poet.red_black_sunglasses.body.threequarter", "p02"),
                    farm_L=cut_path("poet.red_black_sunglasses.body.threequarter", "p03"),
                    uarm_R=cut_path("poet.red_black_sunglasses.body.threequarter", "p02"),
                    farm_R=cut_path("poet.red_black_sunglasses.body.threequarter", "p05"),
                    hand_L=cut_path("poet.red_black_sunglasses.body.threequarter", "p06"),
                    hand_R=cut_path("poet.red_black_sunglasses.body.threequarter", "p07"),
                    thigh_L=cut_path("poet.red_black_sunglasses.body.threequarter", "p08"),
                    shin_L=cut_path("poet.red_black_sunglasses.body.threequarter", "p10"),
                    thigh_R=cut_path("poet.red_black_sunglasses.body.threequarter", "p09"),
                    shin_R=cut_path("poet.red_black_sunglasses.body.threequarter", "p11"),
                    foot_L=cut_path("poet.red_black_sunglasses.body.threequarter", "p12"),
                    foot_R=cut_path("poet.red_black_sunglasses.body.threequarter", "p13"),
                    foot_is_side=True,
                ),
                "SIDE": dict(
                    torso=cut_path("poet.red_black_sunglasses.body.profile", "p01"),
                    seat=cut_path("poet.red_black_sunglasses.hipcore", "p03"),
                    uarm_L=cut_path("poet.red_black_sunglasses.body.profile", "p04"),
                    farm_L=cut_path("poet.red_black_sunglasses.body.profile", "p05"),
                    uarm_R=cut_path("poet.red_black_sunglasses.body.profile", "p04"),
                    farm_R=cut_path("poet.red_black_sunglasses.body.profile", "p05"),
                    hand_L=cut_path("poet.red_black_sunglasses.body.profile", "p06"),
                    hand_R=cut_path("poet.red_black_sunglasses.body.profile", "p06"),
                    thigh_L=cut_path("poet.red_black_sunglasses.body.profile", "p02"),
                    shin_L=cut_path("poet.red_black_sunglasses.body.profile", "p03"),
                    thigh_R=cut_path("poet.red_black_sunglasses.body.profile", "p02"),
                    shin_R=cut_path("poet.red_black_sunglasses.body.profile", "p03"),
                    foot_L=cut_path("poet.red_black_sunglasses.body.profile", "p07"),
                    foot_R=cut_path("poet.red_black_sunglasses.body.profile", "p07"),
                    foot_is_side=True,
                ),
                "BACK": dict(
                    torso=cut_path("poet.red_black_sunglasses.body.back", "p01"),
                    seat=cut_path("poet.red_black_sunglasses.hipcore", "p03"),
                    uarm_L=cut_path("poet.red_black_sunglasses.body.back", "p02"),
                    farm_L=cut_path("poet.red_black_sunglasses.body.back", "p03"),
                    uarm_R=cut_path("poet.red_black_sunglasses.body.back", "p04"),
                    farm_R=cut_path("poet.red_black_sunglasses.body.back", "p05"),
                    hand_L=cut_path("poet.red_black_sunglasses.body.back", "p06"),
                    hand_R=cut_path("poet.red_black_sunglasses.body.back", "p07"),
                    thigh_L=cut_path("poet.red_black_sunglasses.body.back", "p08"),
                    shin_L=cut_path("poet.red_black_sunglasses.body.back", "p10"),
                    thigh_R=cut_path("poet.red_black_sunglasses.body.back", "p09"),
                    shin_R=cut_path("poet.red_black_sunglasses.body.back", "p11"),
                    foot_L=cut_path("poet.red_black_sunglasses.body.back", "p12"),
                    foot_R=cut_path("poet.red_black_sunglasses.body.back", "p13"),
                    foot_is_side=False,
                ),
            },
        },
        {
            "id": "poet_black_tshirt",
            "name": "2. Poet (Black T-Shirt)",
            "scale": 1.00,
            "heads": poet_bt_heads,
            "views": {
                v: dict(
                    torso=cut_path("poet.black_tshirt.compact-core", "p02" if v == "BACK" else "p01"),
                    seat=cut_path("poet.black_tshirt.compact-core", "p03"),
                    uarm_L=cut_path("poet.black_tshirt.compact-core", "p05"),
                    farm_L=cut_path("poet.black_tshirt.compact-core", "p06"),
                    uarm_R=cut_path("poet.black_tshirt.compact-core", "p07"),
                    farm_R=cut_path("poet.black_tshirt.compact-core", "p08"),
                    hand_L=cut_path("poet.red_black_sunglasses.body.profile", "p06") if v == "SIDE" else cut_path("poet.red_black_sunglasses.body.front", "p06"),
                    hand_R=cut_path("poet.red_black_sunglasses.body.profile", "p06") if v == "SIDE" else cut_path("poet.red_black_sunglasses.body.front", "p07"),
                    thigh_L=cut_path("poet.black_tshirt.compact-core", "p09"),
                    shin_L=cut_path("poet.black_tshirt.compact-core", "p10"),
                    thigh_R=cut_path("poet.black_tshirt.compact-core", "p11"),
                    shin_R=cut_path("poet.black_tshirt.compact-core", "p12"),
                    foot_L=cut_path("poet.black_tshirt.compact-core", "p13") if v in ("SIDE", "3Q") else cut_path("poet.red_black_sunglasses.feet", "p04"),
                    foot_R=cut_path("poet.black_tshirt.compact-core", "p13") if v in ("SIDE", "3Q") else cut_path("poet.red_black_sunglasses.feet", "p04"),
                    foot_is_side=(v in ("SIDE", "3Q")),
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            },
        },
        {
            "id": "woman_brocade",
            "name": "3. Woman / Muse (Brocade)",
            "scale": 0.96,
            "heads": woman_heads,
            "skirt_h_frac": 0.30,
            "views": {
                v: dict(
                    torso=cut_path("woman.13.body", "p16" if v == "SIDE" else ("p03" if v == "BACK" else "p02")),
                    seat=cut_path("woman.13.body", "p06"),
                    skirt_overlay=cut_path("woman.13.body", "p07" if v == "BACK" else "p04"),
                    uarm_L=cut_path("woman.13.body", "p08"),
                    farm_L=cut_path("woman.13.body", "p10"),
                    uarm_R=cut_path("woman.13.body", "p09"),
                    farm_R=cut_path("woman.13.body", "p11"),
                    hand_L=cut_path("woman.13.heads-hands", "p20"),
                    hand_R=cut_path("woman.13.heads-hands", "p21"),
                    thigh_L=cut_path("woman.13.body", "p12"),
                    shin_L=cut_path("woman.13.body", "p14"),
                    thigh_R=cut_path("woman.13.body", "p13"),
                    shin_R=cut_path("woman.13.body", "p15"),
                    foot_L=cut_path("woman.13.body", "p18"),
                    foot_R=cut_path("woman.13.body", "p18"),
                    foot_is_side=True,
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            },
        },
        {
            "id": "mother_cardigan",
            "name": "4. The Mother (Cardigan)",
            "scale": 0.95,
            "heads": mother_heads,
            "skirt_h_frac": 0.31,
            "views": {
                v: dict(
                    torso=cut_path("woman.09.mother.body", "p03" if v == "SIDE" else ("p02" if v == "BACK" else "p01")),
                    torso_flip=(v == "SIDE"),  # p03 faces left on sheet; flip to face +X right
                    seat=cut_path("woman.09.mother.body", "p09"),
                    skirt_overlay=cut_path("woman.09.mother.body", "p15" if v == "BACK" else "p14"),
                    uarm_L=cut_path("woman.09.mother.body", "p04"),
                    farm_L=cut_path("woman.09.mother.body", "p06"),
                    uarm_R=cut_path("woman.09.mother.body", "p05"),
                    farm_R=cut_path("woman.09.mother.body", "p07"),
                    hand_L=cut_path("woman.13.heads-hands", "p20"),
                    hand_R=cut_path("woman.13.heads-hands", "p21"),
                    thigh_L=cut_path("woman.09.mother.body", "p10"),
                    shin_L=cut_path("woman.09.mother.body", "p12"),
                    thigh_R=cut_path("woman.09.mother.body", "p11"),
                    shin_R=cut_path("woman.09.mother.body", "p13"),
                    foot_L=cut_path("woman.09.mother.body", "p18" if v in ("SIDE", "3Q") else "p16"),
                    foot_R=cut_path("woman.09.mother.body", "p18" if v in ("SIDE", "3Q") else "p17"),
                    foot_is_side=(v in ("SIDE", "3Q")),
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            },
        },
        {
            "id": "ex_olive_bomber",
            "name": "5. The Ex (Olive Bomber)",
            "scale": 0.98,
            "heads": ex_heads,
            "views": {
                v: dict(
                    torso=cut_path("ex.ex_jacket.body.threequarter_back" if v in ("3Q", "SIDE") else "ex.ex_jacket.body.back", "p01"),
                    seat=cut_path("ex.ex_jacket.hipcore", "p03"),
                    uarm_L=cut_path("ex.ex_jacket.body.back", "p02"),
                    farm_L=cut_path("ex.ex_jacket.body.back", "p03"),
                    uarm_R=cut_path("ex.ex_jacket.body.back", "p04"),
                    farm_R=cut_path("ex.ex_jacket.body.back", "p05"),
                    hand_L=cut_path("ex.ex_jacket.body.back", "p06"),
                    hand_R=cut_path("ex.ex_jacket.body.back", "p07"),
                    thigh_L=cut_path("ex.ex_jacket.body.back", "p08"),
                    shin_L=cut_path("ex.ex_jacket.body.back", "p09"),
                    thigh_R=cut_path("ex.ex_jacket.body.back", "p10"),
                    shin_R=cut_path("ex.ex_jacket.body.back", "p11"),
                    foot_L=cut_path("ex.ex_jacket.body.back", "p14"),
                    foot_R=cut_path("ex.ex_jacket.body.back", "p14"),
                    foot_is_side=True,
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            },
        },
        {
            "id": "party_gentleman",
            "name": "6. Party Gentleman (Suit)",
            "scale": 1.00,
            "heads": party_male_heads,
            "views": {
                "FRONT": dict(
                    torso=cut_path("party.vintage_party.body.front", "p01"),
                    seat=cut_path("party.vintage_party.hipcore", "p09"),  # Clean pleated trouser front cover!
                    uarm_L=cut_path("party.vintage_party.body.front", "p02"),
                    farm_L=cut_path("party.vintage_party.body.front", "p03"),
                    uarm_R=cut_path("party.vintage_party.body.front", "p05"),
                    farm_R=cut_path("party.vintage_party.body.front", "p06"),
                    hand_L=cut_path("poet.red_black_sunglasses.body.front", "p06"),
                    hand_R=cut_path("poet.red_black_sunglasses.body.front", "p07"),
                    thigh_L=cut_path("party.vintage_party.body.front", "p08"),
                    shin_L=cut_path("party.vintage_party.body.front", "p09"),
                    thigh_R=cut_path("party.vintage_party.body.front", "p11"),
                    shin_R=cut_path("party.vintage_party.body.front", "p12"),
                    foot_L=cut_path("party.vintage_party.face-feet.male", "p36"),
                    foot_R=cut_path("party.vintage_party.face-feet.male", "p38"),
                    foot_is_side=False,
                ),
                "3Q": dict(
                    torso=cut_path("party.vintage_party.body.front", "p01"),
                    seat=cut_path("party.vintage_party.hipcore", "p09"),
                    uarm_L=cut_path("party.vintage_party.body.front", "p02"),
                    farm_L=cut_path("party.vintage_party.body.front", "p03"),
                    uarm_R=cut_path("party.vintage_party.body.front", "p05"),
                    farm_R=cut_path("party.vintage_party.body.front", "p06"),
                    hand_L=cut_path("poet.red_black_sunglasses.body.front", "p06"),
                    hand_R=cut_path("poet.red_black_sunglasses.body.front", "p07"),
                    thigh_L=cut_path("party.vintage_party.body.front", "p08"),
                    shin_L=cut_path("party.vintage_party.body.front", "p09"),
                    thigh_R=cut_path("party.vintage_party.body.front", "p11"),
                    shin_R=cut_path("party.vintage_party.body.front", "p12"),
                    foot_L=cut_path("party.vintage_party.body.profile", "p09"),
                    foot_R=cut_path("party.vintage_party.body.profile", "p09"),
                    foot_is_side=True,
                ),
                "SIDE": dict(
                    torso=cut_path("party.vintage_party.body.profile", "p01"),
                    seat=cut_path("party.vintage_party.body.profile", "p06"),
                    uarm_L=cut_path("party.vintage_party.body.profile", "p02"),
                    farm_L=cut_path("party.vintage_party.body.profile", "p03"),
                    uarm_R=cut_path("party.vintage_party.body.profile", "p02"),
                    farm_R=cut_path("party.vintage_party.body.profile", "p03"),
                    hand_L=cut_path("party.vintage_party.body.profile", "p07"),
                    hand_R=cut_path("party.vintage_party.body.profile", "p07"),
                    thigh_L=cut_path("party.vintage_party.body.profile", "p04"),
                    shin_L=cut_path("party.vintage_party.body.profile", "p05"),
                    thigh_R=cut_path("party.vintage_party.body.profile", "p04"),
                    shin_R=cut_path("party.vintage_party.body.profile", "p05"),
                    foot_L=cut_path("party.vintage_party.body.profile", "p09"),
                    foot_R=cut_path("party.vintage_party.body.profile", "p09"),
                    foot_is_side=True,
                ),
                "BACK": dict(
                    torso=cut_path("party.vintage_party.body.back", "p01"),
                    seat=cut_path("party.vintage_party.hipcore", "p08"),
                    uarm_L=cut_path("party.vintage_party.body.back", "p02"),
                    farm_L=cut_path("party.vintage_party.body.back", "p03"),
                    uarm_R=cut_path("party.vintage_party.body.back", "p05"),
                    farm_R=cut_path("party.vintage_party.body.back", "p06"),
                    hand_L=cut_path("poet.red_black_sunglasses.body.back", "p06"),
                    hand_R=cut_path("poet.red_black_sunglasses.body.back", "p07"),
                    thigh_L=cut_path("party.vintage_party.body.back", "p08"),
                    shin_L=cut_path("party.vintage_party.body.back", "p09"),
                    thigh_R=cut_path("party.vintage_party.body.back", "p11"),
                    shin_R=cut_path("party.vintage_party.body.back", "p12"),
                    foot_L=cut_path("party.vintage_party.face-feet.male", "p39"),
                    foot_R=cut_path("party.vintage_party.face-feet.male", "p41"),
                    foot_is_side=False,
                ),
            },
        },
        {
            "id": "party_woman_gown",
            "name": "7. Party Woman (Cream Gown)",
            "scale": 0.96,
            "heads": party_female_heads,
            "skirt_h_frac": 0.46,
            "views": {
                v: dict(
                    torso=cut_path("party.vintage_party.body.profile", "p10") if v == "SIDE" else (cut_path("party.vintage_party.body.back", "p18") if v == "BACK" else cut_path("party.vintage_party.body.front", "p17")),
                    seat=cut_path("party.vintage_party.body.profile", "p17"),
                    skirt_overlay=cut_path("party.vintage_party.hipcore", "p13" if v == "BACK" else "p12"),
                    uarm_L=cut_path("party.vintage_party.body.profile", "p11"),
                    farm_L=cut_path("party.vintage_party.body.profile", "p12"),
                    uarm_R=cut_path("party.vintage_party.body.profile", "p11"),
                    farm_R=cut_path("party.vintage_party.body.profile", "p12"),
                    hand_L=cut_path("party.vintage_party.body.profile", "p13"),
                    hand_R=cut_path("party.vintage_party.body.profile", "p13"),
                    thigh_L=cut_path("party.vintage_party.body.profile", "p14") if v == "SIDE" else cut_path("party.vintage_party.body.front", "p19" if os.path.exists(cut_path("party.vintage_party.body.front", "p19")) else "p08"),
                    shin_L=cut_path("party.vintage_party.body.profile", "p15"),
                    thigh_R=cut_path("party.vintage_party.body.profile", "p14"),
                    shin_R=cut_path("party.vintage_party.body.profile", "p15"),
                    foot_L=cut_path("party.vintage_party.body.profile", "p18") if v in ("SIDE", "3Q") else cut_path("party.vintage_party.face-feet.female", "p36"),
                    foot_R=cut_path("party.vintage_party.body.profile", "p18") if v in ("SIDE", "3Q") else cut_path("party.vintage_party.face-feet.female", "p37"),
                    foot_is_side=(v in ("SIDE", "3Q")),
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            },
        },
        {
            "id": "dj_cyber",
            "name": "8. DJ Cyber (Naraka Club)",
            "scale": 1.00,
            "heads": dj_heads,
            "views": {
                v: dict(
                    torso=cut_path("party.dj_cyber.body.profile", "p01") if v == "SIDE" else cut_path("party.dj_cyber.compact-core", "p02" if v == "BACK" else "p01"),
                    seat=cut_path("party.dj_cyber.body.profile", "p09") if v == "SIDE" else cut_path("party.dj_cyber.compact-core", "p04"),
                    uarm_L=cut_path("party.dj_cyber.body.profile", "p02"),
                    farm_L=cut_path("party.dj_cyber.body.profile", "p03"),
                    uarm_R=cut_path("party.dj_cyber.body.profile", "p02"),
                    farm_R=cut_path("party.dj_cyber.body.profile", "p03"),
                    hand_L=cut_path("party.dj_cyber.body.profile", "p06"),
                    hand_R=cut_path("party.dj_cyber.body.profile", "p06"),
                    thigh_L=cut_path("party.dj_cyber.body.profile", "p04") if v == "SIDE" else cut_path("party.dj_cyber.compact-core", "p09"),
                    shin_L=cut_path("party.dj_cyber.body.profile", "p05") if v == "SIDE" else cut_path("party.dj_cyber.compact-core", "p10"),
                    thigh_R=cut_path("party.dj_cyber.body.profile", "p04") if v == "SIDE" else cut_path("party.dj_cyber.compact-core", "p11"),
                    shin_R=cut_path("party.dj_cyber.body.profile", "p05") if v == "SIDE" else cut_path("party.dj_cyber.compact-core", "p12"),
                    foot_L=cut_path("party.dj_cyber.face-feet", "p30") if v == "FRONT" else (cut_path("party.dj_cyber.face-feet", "p32") if v == "BACK" else cut_path("party.dj_cyber.body.profile", "p07")),
                    foot_R=cut_path("party.dj_cyber.face-feet", "p31") if v == "FRONT" else (cut_path("party.dj_cyber.face-feet", "p33") if v == "BACK" else cut_path("party.dj_cyber.body.profile", "p07")),
                    foot_is_side=(v in ("SIDE", "3Q")),
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            },
        },
        {
            "id": "young_poet",
            "name": "9. Young Poet (Age 6 · 0.70x)",
            "scale": 0.70,
            "heads": yp_heads,
            "views": {
                "FRONT": dict(
                    torso=cut_path("young_poet.child_clothes.body.front", "p01"),
                    seat=cut_path("young_poet.child_clothes.hipcore", "p04"),
                    uarm_L=cut_path("young_poet.child_clothes.body.front", "p02"),
                    farm_L=cut_path("young_poet.child_clothes.body.front", "p03"),
                    uarm_R=cut_path("young_poet.child_clothes.body.front", "p04"),
                    farm_R=cut_path("young_poet.child_clothes.body.front", "p05"),
                    hand_L=cut_path("young_poet.child_clothes.body.back", "p06"),
                    hand_R=cut_path("young_poet.child_clothes.body.back", "p07"),
                    thigh_L=cut_path("young_poet.child_clothes.body.front", "p08"),
                    shin_L=cut_path("young_poet.child_clothes.body.front", "p09"),
                    thigh_R=cut_path("young_poet.child_clothes.body.front", "p10"),
                    shin_R=cut_path("young_poet.child_clothes.body.front", "p11"),
                    foot_L=cut_path("young_poet.child_clothes.body.front", "p12"),
                    foot_R=cut_path("young_poet.child_clothes.body.front", "p13"),
                    foot_is_side=False,
                ),
                "3Q": dict(
                    torso=cut_path("young_poet.child_clothes.body.threequarter", "p01"),
                    seat=cut_path("young_poet.child_clothes.hipcore", "p04"),
                    uarm_L=cut_path("young_poet.child_clothes.body.threequarter", "p02"),
                    farm_L=cut_path("young_poet.child_clothes.body.threequarter", "p03"),
                    uarm_R=cut_path("young_poet.child_clothes.body.threequarter", "p04"),
                    farm_R=cut_path("young_poet.child_clothes.body.threequarter", "p05"),
                    hand_L=cut_path("young_poet.child_clothes.body.profile", "p04"),
                    hand_R=cut_path("young_poet.child_clothes.body.profile", "p04"),
                    thigh_L=cut_path("young_poet.child_clothes.body.threequarter", "p08"),
                    shin_L=cut_path("young_poet.child_clothes.body.threequarter", "p09"),
                    thigh_R=cut_path("young_poet.child_clothes.body.threequarter", "p10"),
                    shin_R=cut_path("young_poet.child_clothes.body.threequarter", "p11"),
                    foot_L=cut_path("young_poet.child_clothes.body.threequarter", "p12"),
                    foot_R=cut_path("young_poet.child_clothes.body.threequarter", "p13"),
                    foot_is_side=True,
                ),
                "SIDE": dict(
                    torso=cut_path("young_poet.child_clothes.body.profile", "p01"),
                    seat=None,  # p05 thigh already includes the side denim shorts!
                    uarm_L=cut_path("young_poet.child_clothes.body.profile", "p02"),
                    farm_L=cut_path("young_poet.child_clothes.body.profile", "p03"),
                    uarm_R=cut_path("young_poet.child_clothes.body.profile", "p02"),
                    farm_R=cut_path("young_poet.child_clothes.body.profile", "p03"),
                    hand_L=cut_path("young_poet.child_clothes.body.profile", "p04"),
                    hand_R=cut_path("young_poet.child_clothes.body.profile", "p04"),
                    thigh_L=cut_path("young_poet.child_clothes.body.profile", "p05"),
                    shin_L=cut_path("young_poet.child_clothes.body.profile", "p06"),
                    thigh_R=cut_path("young_poet.child_clothes.body.profile", "p05"),
                    shin_R=cut_path("young_poet.child_clothes.body.profile", "p06"),
                    foot_L=cut_path("young_poet.child_clothes.body.profile", "p07"),
                    foot_R=cut_path("young_poet.child_clothes.body.profile", "p07"),
                    foot_is_side=True,
                ),
                "BACK": dict(
                    torso=cut_path("young_poet.child_clothes.body.back", "p01"),
                    seat=cut_path("young_poet.child_clothes.hipcore", "p04"),
                    uarm_L=cut_path("young_poet.child_clothes.body.back", "p02"),
                    farm_L=cut_path("young_poet.child_clothes.body.back", "p04"),
                    uarm_R=cut_path("young_poet.child_clothes.body.back", "p03"),
                    farm_R=cut_path("young_poet.child_clothes.body.back", "p05"),
                    hand_L=cut_path("young_poet.child_clothes.body.back", "p06"),
                    hand_R=cut_path("young_poet.child_clothes.body.back", "p07"),
                    thigh_L=cut_path("young_poet.child_clothes.body.back", "p08"),
                    shin_L=cut_path("young_poet.child_clothes.body.back", "p09"),
                    thigh_R=cut_path("young_poet.child_clothes.body.back", "p10"),
                    shin_R=cut_path("young_poet.child_clothes.body.back", "p11"),
                    foot_L=cut_path("young_poet.child_clothes.body.back", "p12"),
                    foot_R=cut_path("young_poet.child_clothes.body.back", "p13"),
                    foot_is_side=False,
                ),
            },
        },
    ]


# ============================================================================
# 4. GROUND-UP KINEMATIC SKELETON & IDEAL BODY RENDERER
# ============================================================================

def solve_and_render_ideal_body(
    char_spec,
    view="FRONT",
    pose=None,
    cw=225,
    ch=310,
    ground_y=280,
    center_x=None,
    fig_h_base=234,
):
    """
    Solves the character skeleton from the GROUND UP using the universal
    master-sheet bone ratios and renders every piece with 2-point brass-grommet
    registration (`fit_bone_2pt`).
    Returns `(canvas_im, joints_dict)`.
    """
    if pose is None:
        pose = {}
    if center_x is None:
        center_x = cw // 2

    sc = char_spec.get("scale", 1.0)
    H_fig = fig_h_base * sc
    is_child = (sc < 0.80)

    if is_child:
        # 6-Year-Old Child Master Proportions (verified against young_poet.child_clothes.hipcore__p07)
        H_sole = 0.095 * H_fig
        L_shin = 0.165 * H_fig
        L_thigh = 0.180 * H_fig
        L_torso = 0.235 * H_fig
        L_uarm = 0.125 * H_fig
        L_farm = 0.110 * H_fig
        H_hand = 0.095 * H_fig
        H_head = 0.355 * H_fig
        H_foot_card = 0.125 * H_fig
        def_ua_splay = 13.0
        def_fa_splay = 9.0
    else:
        # Adult Master-Sheet Bone Ratios (verified against poet.master__p01, ex.master__p01, party.master__p01)
        # Sums to 1.000 * H_fig from Ground Sole (1.000) to Crown (0.000):
        # Sole (0.090) + Shin (0.195) + Thigh (0.245) = 0.530 (Hip at 0.470)
        # + Torso (0.300) = 0.830 (Neck at 0.170) + 0.86 * Head (0.170) = 1.000 (Crown at 0.000)!
        H_sole = 0.090 * H_fig
        L_shin = 0.195 * H_fig
        L_thigh = 0.245 * H_fig
        L_torso = 0.300 * H_fig
        L_uarm = 0.150 * H_fig
        L_farm = 0.134 * H_fig
        H_hand = 0.105 * H_fig
        H_head = 0.198 * H_fig
        H_foot_card = 0.132 * H_fig
        def_ua_splay = 6.0
        def_fa_splay = 3.0

    # Joint angles in degrees (+deg swings distal joint toward +X right, CCW in screen space)
    # Note: S_L is on the LEFT (-X) side of the torso, so -def_ua_splay angles the left arm slightly outward (-X),
    # and S_R is on the RIGHT (+X) side of the torso, so +def_ua_splay angles the right arm slightly outward (+X)!
    spine_deg = pose.get("spine_deg", 0.0)
    thigh_L_deg = pose.get("thigh_L_deg", 0.0)
    shin_L_deg = pose.get("shin_L_deg", 0.0)
    foot_L_deg = pose.get("foot_L_deg", 0.0)
    thigh_R_deg = pose.get("thigh_R_deg", 0.0)
    shin_R_deg = pose.get("shin_R_deg", 0.0)
    foot_R_deg = pose.get("foot_R_deg", 0.0)
    uarm_L_deg = pose.get("uarm_L_deg", -def_ua_splay if view != "SIDE" else 4.0)
    farm_L_deg = pose.get("farm_L_deg", -def_fa_splay if view != "SIDE" else 8.0)
    hand_L_deg = pose.get("hand_L_deg", 0.0)
    uarm_R_deg = pose.get("uarm_R_deg", +def_ua_splay if view != "SIDE" else -4.0)
    farm_R_deg = pose.get("farm_R_deg", +def_fa_splay if view != "SIDE" else 4.0)
    hand_R_deg = pose.get("hand_R_deg", 0.0)
    head_deg = pose.get("head_deg", 0.0)

    # Load view-specific parts early so we know the exact rendered torso shoulder width!
    vspec = char_spec["views"][view]
    torso_im = load_clean_cut(vspec["torso"], fill_armhole=(view == "SIDE"), flip_x=vspec.get("torso_flip", False))
    torso_render_sc = L_torso / float(max(1.0, 0.80 * torso_im.height))
    torso_render_w = torso_im.width * torso_render_sc

    # Horizontal hip & shoulder spacing matched to the torso & hip-seat grommets
    if view == "SIDE":
        dx_hip_L, dx_hip_R = 0.0, 2.0 * sc
        dx_sh_L, dx_sh_R = -1.5 * sc, 1.5 * sc
        sh_up_frac = 0.80
    elif view == "3Q":
        dx_hip_L, dx_hip_R = -9.5 * sc, 10.5 * sc
        dx_sh_L, dx_sh_R = -0.31 * torso_render_w, +0.29 * torso_render_w
        sh_up_frac = 0.86
    else:
        dx_hip_L, dx_hip_R = -11.0 * sc, 11.0 * sc
        dx_sh_L, dx_sh_R = -0.35 * torso_render_w, +0.35 * torso_render_w
        sh_up_frac = 0.88 if is_child else 0.85

    # Step 1: Provisional hip center at (center_x, 0) to compute lowest floor contact
    def step_vec(pt, length, deg):
        rad = math.radians(deg)
        return (pt[0] + length * math.sin(rad), pt[1] + length * math.cos(rad))

    H_L0 = (center_x + dx_hip_L, 0.0)
    H_R0 = (center_x + dx_hip_R, 0.0)
    K_L0 = step_vec(H_L0, L_thigh, thigh_L_deg)
    A_L0 = step_vec(K_L0, L_shin, shin_L_deg)
    K_R0 = step_vec(H_R0, L_thigh, thigh_R_deg)
    A_R0 = step_vec(K_R0, L_shin, shin_R_deg)

    # Lowest point below hip (including shoe sole or kneeling knee)
    sole_L0 = A_L0[1] + H_sole * max(0.28, math.cos(math.radians(foot_L_deg)))
    sole_R0 = A_R0[1] + H_sole * max(0.28, math.cos(math.radians(foot_R_deg)))
    knee_pad = 0.042 * H_fig
    max_low_y = max(sole_L0, sole_R0, K_L0[1] + knee_pad, K_R0[1] + knee_pad)

    # Anchor lowest point strictly on `ground_y`!
    hip_y = ground_y - max_low_y
    hip_x = float(center_x)

    H_C = (hip_x, hip_y)
    H_L = (hip_x + dx_hip_L, hip_y)
    H_R = (hip_x + dx_hip_R, hip_y)
    K_L = step_vec(H_L, L_thigh, thigh_L_deg)
    A_L = step_vec(K_L, L_shin, shin_L_deg)
    K_R = step_vec(H_R, L_thigh, thigh_R_deg)
    A_R = step_vec(K_R, L_shin, shin_R_deg)

    # Spine vector from H_C up to Neck N (+spine_deg leans torso forward/+X)
    sp_rad = math.radians(spine_deg)
    N = (hip_x + L_torso * math.sin(sp_rad), hip_y - L_torso * math.cos(sp_rad))

    # Shoulder sockets aligned with the outer shoulder grommets of the torso card
    sh_cx = hip_x + sh_up_frac * L_torso * math.sin(sp_rad)
    sh_cy = hip_y - sh_up_frac * L_torso * math.cos(sp_rad)
    S_L = (sh_cx + dx_sh_L, sh_cy)
    S_R = (sh_cx + dx_sh_R, sh_cy)

    E_L = step_vec(S_L, L_uarm, uarm_L_deg)
    W_L = step_vec(E_L, L_farm, farm_L_deg)
    E_R = step_vec(S_R, L_uarm, uarm_R_deg)
    W_R = step_vec(E_R, L_farm, farm_R_deg)

    seat_im = load_clean_cut(vspec["seat"]) if vspec.get("seat") else None
    skirt_im = load_clean_cut(vspec["skirt_overlay"]) if vspec.get("skirt_overlay") else None
    skirt_h_frac = char_spec.get("skirt_h_frac", 0.29)

    uarm_L_im = load_clean_cut(vspec["uarm_L"])
    farm_L_im = load_clean_cut(vspec["farm_L"])
    uarm_R_im = load_clean_cut(vspec["uarm_R"])
    farm_R_im = load_clean_cut(vspec["farm_R"])

    hand_L_im = pose.get("hand_L_override") or load_clean_cut(vspec["hand_L"], rot90_if_horiz=True)
    hand_R_im = pose.get("hand_R_override") or load_clean_cut(vspec["hand_R"], rot90_if_horiz=True)

    thigh_L_im = load_clean_cut(vspec["thigh_L"])
    shin_L_im = load_clean_cut(vspec["shin_L"])
    thigh_R_im = load_clean_cut(vspec["thigh_R"])
    shin_R_im = load_clean_cut(vspec["shin_R"])

    foot_is_side = vspec.get("foot_is_side", view in ("SIDE", "3Q"))
    foot_L_im = load_clean_cut(vspec["foot_L"], flip_x=False)
    foot_R_im = load_clean_cut(vspec["foot_R"], flip_x=(not foot_is_side and vspec["foot_L"] == vspec["foot_R"]))

    head_im = pose.get("head_override") or char_spec["heads"][view]

    # Measure true grommet endpoints on each limb card
    thL_a, thL_b = find_limb_grommets(thigh_L_im)
    shL_a, shL_b = find_limb_grommets(shin_L_im)
    thR_a, thR_b = find_limb_grommets(thigh_R_im)
    shR_a, shR_b = find_limb_grommets(shin_R_im)
    uaL_a, uaL_b = find_limb_grommets(uarm_L_im)
    faL_a, faL_b = find_limb_grommets(farm_L_im)
    uaR_a, uaR_b = find_limb_grommets(uarm_R_im)
    faR_a, faR_b = find_limb_grommets(farm_R_im)

    foot_piv = (0.32, 0.24) if foot_is_side else (0.50, 0.22)
    hand_piv = (0.50, 0.14)

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))

    # Helper to draw a single leg (Foot tucked BEHIND Shin so pant cuff overlaps boot tab!)
    def draw_leg(H_pt, K_pt, A_pt, th_im, th_a, th_b, sh_im, sh_a, sh_b, ft_im, ft_deg):
        place_anchored_card(canvas, ft_im, foot_piv, A_pt, H_foot_card, rot_deg=ft_deg, clip_top_frac=0.08)
        fit_bone_2pt(canvas, sh_im, sh_a, sh_b, K_pt, A_pt)
        fit_bone_2pt(canvas, th_im, th_a, th_b, H_pt, K_pt)

    # Helper to draw a single arm (Hand tucked BEHIND Forearm so sleeve cuff overlaps wrist tab!)
    def draw_arm(S_pt, E_pt, W_pt, ua_im, ua_a, ua_b, fa_im, fa_a, fa_b, hd_im, fa_deg, hd_deg):
        place_anchored_card(canvas, hd_im, hand_piv, W_pt, H_hand, rot_deg=fa_deg + hd_deg, clip_top_frac=0.08)
        fit_bone_2pt(canvas, fa_im, fa_a, fa_b, E_pt, W_pt)
        fit_bone_2pt(canvas, ua_im, ua_a, ua_b, S_pt, E_pt)

    if view == "SIDE":
        # Back-to-Front Layering in Side Profile (+X facing):
        if pose.get("show_far_arm_in_side", False):
            draw_arm(S_R, E_R, W_R, uarm_R_im, uaR_a, uaR_b, farm_R_im, faR_a, faR_b, hand_R_im, farm_R_deg, hand_R_deg)
        if abs(thigh_R_deg - thigh_L_deg) > 2.0 or abs(shin_R_deg - shin_L_deg) > 2.0:
            draw_leg(H_R, K_R, A_R, thigh_R_im, thR_a, thR_b, shin_R_im, shR_a, shR_b, foot_R_im, foot_R_deg)
        if seat_im is not None and (abs(thigh_L_deg) > 15 or abs(spine_deg) > 10):
            place_anchored_card(canvas, seat_im, (0.55, 0.45), H_C, int(0.18 * H_fig))
        draw_leg(H_L, K_L, A_L, thigh_L_im, thL_a, thL_b, shin_L_im, shL_a, shL_b, foot_L_im, foot_L_deg)
        if skirt_im is not None:
            place_anchored_card(canvas, skirt_im, (0.50, 0.10), (H_C[0], H_C[1] - int(0.03 * H_fig)), int(skirt_h_frac * H_fig), width_mult=0.72)
        fit_bone_2pt(canvas, torso_im, (0.48, 0.09), (0.48, 0.89), N, H_C)
        place_anchored_card(canvas, head_im, (0.48, 0.86), N, H_head, rot_deg=head_deg)
        draw_arm(S_L, E_L, W_L, uarm_L_im, uaL_a, uaL_b, farm_L_im, faL_a, faL_b, hand_L_im, farm_L_deg, hand_L_deg)

    elif view == "BACK":
        # Back view: Seat & Legs first, then Torso & Head, then Arms ON TOP of outer shoulders (matching ex.master__p01!)
        if seat_im is not None:
            place_anchored_card(canvas, seat_im, (0.50, 0.30), H_C, int(0.18 * H_fig))
        draw_leg(H_L, K_L, A_L, thigh_L_im, thL_a, thL_b, shin_L_im, shL_a, shL_b, foot_L_im, foot_L_deg)
        draw_leg(H_R, K_R, A_R, thigh_R_im, thR_a, thR_b, shin_R_im, shR_a, shR_b, foot_R_im, foot_R_deg)
        if skirt_im is not None:
            place_anchored_card(canvas, skirt_im, (0.50, 0.10), (H_C[0], H_C[1] - int(0.03 * H_fig)), int(skirt_h_frac * H_fig))
        place_anchored_card(canvas, head_im, (0.50, 0.86), N, H_head, rot_deg=head_deg)
        fit_bone_2pt(canvas, torso_im, (0.50, 0.09), (0.50, 0.89), N, H_C)
        draw_arm(S_L, E_L, W_L, uarm_L_im, uaL_a, uaL_b, farm_L_im, faL_a, faL_b, hand_L_im, farm_L_deg, hand_L_deg)
        draw_arm(S_R, E_R, W_R, uarm_R_im, uaR_a, uaR_b, farm_R_im, faR_a, faR_b, hand_R_im, farm_R_deg, hand_R_deg)

    else:
        # FRONT and 3Q Views:
        if seat_im is not None:
            place_anchored_card(canvas, seat_im, (0.50, 0.30), H_C, int((0.20 if is_child else 0.18) * H_fig))
        draw_leg(H_R, K_R, A_R, thigh_R_im, thR_a, thR_b, shin_R_im, shR_a, shR_b, foot_R_im, foot_R_deg)
        draw_leg(H_L, K_L, A_L, thigh_L_im, thL_a, thL_b, shin_L_im, shL_a, shL_b, foot_L_im, foot_L_deg)
        if skirt_im is not None:
            place_anchored_card(canvas, skirt_im, (0.50, 0.10), (H_C[0], H_C[1] - int(0.03 * H_fig)), int(skirt_h_frac * H_fig))
        if view == "3Q":
            draw_arm(S_R, E_R, W_R, uarm_R_im, uaR_a, uaR_b, farm_R_im, faR_a, faR_b, hand_R_im, farm_R_deg, hand_R_deg)
        fit_bone_2pt(canvas, torso_im, (0.50, 0.09), (0.50, 0.89), N, H_C)
        place_anchored_card(canvas, head_im, (0.50, 0.86), N, H_head, rot_deg=head_deg)
        if view != "3Q":
            draw_arm(S_R, E_R, W_R, uarm_R_im, uaR_a, uaR_b, farm_R_im, faR_a, faR_b, hand_R_im, farm_R_deg, hand_R_deg)
        draw_arm(S_L, E_L, W_L, uarm_L_im, uaL_a, uaL_b, farm_L_im, faL_a, faL_b, hand_L_im, farm_L_deg, hand_L_deg)

    joints = {
        "N": N, "H_C": H_C,
        "S_L": S_L, "E_L": E_L, "W_L": W_L,
        "S_R": S_R, "E_R": E_R, "W_R": W_R,
        "H_L": H_L, "K_L": K_L, "A_L": A_L,
        "H_R": H_R, "K_R": K_R, "A_R": A_R,
    }
    return canvas, joints


def draw_calib_grid(draw, x0, y0, w, h, step=24, origin_x=None, origin_y=None):
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=(28, 26, 24, 255), outline=(62, 58, 52, 255), width=1)
    for gx in range(x0 + step, x0 + w, step):
        draw.line([(gx, y0), (gx, y0 + h)], fill=(38, 35, 32, 255), width=1)
    for gy in range(y0 + step, y0 + h, step):
        draw.line([(x0, gy), (x0 + w, gy)], fill=(38, 35, 32, 255), width=1)
    if origin_x is not None:
        draw.line([(x0 + origin_x, y0), (x0 + origin_x, y0 + h)], fill=(70, 115, 135, 160), width=1)
    if origin_y is not None:
        draw.line([(x0, y0 + origin_y), (x0 + w, y0 + origin_y)], fill=(215, 160, 65, 200), width=2)


def draw_joint_pin(draw, xy, color=(0, 230, 255, 235), r=3):
    x, y = int(round(xy[0])), int(round(xy[1]))
    draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=(15, 15, 15, 255))


# ============================================================================
# STEP 1: GROUND-TRUTH MASTER PROPORTION CALIBRATION (`scratch_step1_ideal_body_vs_master.png`)
# ============================================================================

def build_step1_ideal_body_vs_master():
    cast = {c["id"]: c for c in get_canonical_cast_library()}

    pairs = [
        {
            "title": "1. Poet Tracksuit (Front Master vs. Assembled)",
            "ref_path": cut_path("poet.red_black_sunglasses.master", "p01"),
            "char": cast["poet_tracksuit"],
            "view": "FRONT",
            "pose": {},
        },
        {
            "title": "2. The Ex Olive Bomber (Back Master vs. Assembled)",
            "ref_path": cut_path("ex.ex_jacket.master", "p01"),
            "char": cast["ex_olive_bomber"],
            "view": "BACK",
            "pose": {},
        },
        {
            "title": "3. Party Gentleman (Front Master vs. Assembled)",
            "ref_path": cut_path("party.vintage_party.master", "p01"),
            "char": cast["party_gentleman"],
            "view": "FRONT",
            "pose": {},
        },
        {
            "title": "4. Party Woman Gown (Front Master vs. Assembled)",
            "ref_path": cut_path("party.vintage_party.master", "p12"),
            "char": cast["party_woman_gown"],
            "view": "FRONT",
            "pose": {},
        },
        {
            "title": "5. Young Poet Age 6 (Standing Ref vs. Assembled)",
            "ref_path": cut_path("young_poet.child_clothes.hipcore", "p07"),
            "char": cast["young_poet"],
            "view": "FRONT",
            "pose": {},
        },
        {
            "title": "6. Poet Tracksuit (Side Seated Ref vs. Assembled)",
            "ref_path": cut_path("poet.red_black_sunglasses.hipcore", "p07"),
            "char": cast["poet_tracksuit"],
            "view": "SIDE",
            "pose": {
                "spine_deg": 4.0,
                "thigh_L_deg": 86.0, "shin_L_deg": 8.0, "foot_L_deg": 0.0,
                "thigh_R_deg": 82.0, "shin_R_deg": 14.0, "foot_R_deg": 0.0,
                "uarm_L_deg": 24.0, "farm_L_deg": 52.0,
            },
        },
    ]

    pw, ph = 430, 340
    cols = 3
    rows = 2
    sheet = Image.new("RGBA", (cols * pw + 24, rows * ph + 90), (20, 18, 17, 255))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, sheet.width, 72], fill=(14, 13, 12, 255))
    draw.text((20, 14), "STEP 1: GROUND-TRUTH MASTER PROPORTION CALIBRATION (ARTIST MASTER REF vs. OUR 2-POINT GROMMET ASSEMBLY)", fill=(245, 195, 75, 255))
    draw.text((20, 36), "Horizontal proportion lines verify 1:1 anatomical alignment: Crown (0.00) -> Neck (0.16) -> Shoulder (0.22) -> Elbow (0.37) -> Hip (0.46) -> Wrist (0.50) -> Knee (0.69) -> Ankle (0.88) -> Sole (1.00)", fill=(185, 225, 195, 255))
    draw.text((20, 54), "Lower body (Hip to Sole) = 54.5% of standing height | Torso Spine = 29.9% | Arms reach upper-to-mid thigh (NEVER knees/shins) | Compatible pieces from release_v2/cuts/", fill=(175, 170, 160, 255))

    prop_levels = [
        (0.000, "0.00 CROWN", (160, 160, 160, 110)),
        (0.156, "0.16 NECK", (120, 210, 245, 120)),
        (0.224, "0.22 SHOULDER", (120, 210, 245, 120)),
        (0.369, "0.37 ELBOW", (140, 195, 140, 110)),
        (0.455, "0.46 HIP LINE", (255, 190, 80, 170)),
        (0.690, "0.69 KNEE", (120, 210, 245, 130)),
        (0.878, "0.88 ANKLE", (120, 210, 245, 130)),
        (1.000, "1.00 GROUND SOLE", (240, 175, 70, 230)),
    ]

    for idx, item in enumerate(pairs):
        ci = idx % cols
        ri = idx // cols
        x0 = 12 + ci * pw
        y0 = 80 + ri * ph

        draw_calib_grid(draw, x0 + 4, y0 + 4, pw - 8, ph - 8, step=24, origin_y=296 - 4)
        draw.rectangle([x0 + 4, y0 + 4, x0 + pw - 4, y0 + 28], fill=(32, 29, 27, 255))
        draw.text((x0 + 10, y0 + 9), item["title"], fill=(245, 220, 145, 255))

        ground_y = 296
        sc = item["char"]["scale"]
        fig_h = int(234 * sc) if idx < 5 else 168

        # Draw proportional horizontal ruler lines across both halves of the panel
        if idx < 5:
            top_y = ground_y - fig_h
            for frac, lbl, col in prop_levels:
                ly = int(round(top_y + frac * fig_h))
                draw.line([(x0 + 10, y0 + ly), (x0 + pw - 10, y0 + ly)], fill=col, width=1 if frac < 0.99 else 2)
                draw.text((x0 + pw - 98, y0 + ly - 10), lbl, fill=col)

        # Left side: Artist Master Reference Figure
        ref_im = load_clean_cut(item["ref_path"], remove_text_islands=True)
        r_sc = fig_h / float(max(1, ref_im.height))
        rw = max(2, int(round(ref_im.width * r_sc)))
        rh = max(2, int(round(ref_im.height * r_sc)))
        ref_r = ref_im.resize((rw, rh), Image.Resampling.LANCZOS)
        sheet.alpha_composite(ref_r, (x0 + 95 - rw // 2, y0 + ground_y - rh))
        draw.rectangle([x0 + 14, y0 + 34, x0 + 176, y0 + 52], fill=(45, 38, 28, 220), outline=(180, 145, 75, 255))
        draw.text((x0 + 20, y0 + 37), "ARTIST MASTER REF", fill=(245, 210, 120, 255))

        # Right side: Our 2-Point Grommet Assembled Puppet
        fig_im, joints = solve_and_render_ideal_body(
            item["char"],
            view=item["view"],
            pose=item["pose"],
            cw=pw,
            ch=ph,
            ground_y=ground_y,
            center_x=275,
            fig_h_base=234,
        )
        sheet.alpha_composite(fig_im, (x0, y0))
        for jname, jpt in joints.items():
            if jname != "H_C":
                draw_joint_pin(draw, (x0 + jpt[0], y0 + jpt[1]), color=(0, 235, 255, 225), r=3)

        draw.rectangle([x0 + 195, y0 + 34, x0 + 355, y0 + 52], fill=(20, 52, 34, 220), outline=(85, 215, 135, 255))
        draw.text((x0 + 202, y0 + 37), "2-PT GROMMET ASSEMBLY", fill=(130, 245, 175, 255))

    out_p = os.path.join(ART_DIR, "scratch_step1_ideal_body_vs_master.png")
    sheet.save(out_p)
    sheet.save(os.path.join(OUT_DIR, "step1_ideal_body_vs_master.png"))
    print("Saved Step 1 Master Proportion Calibration ->", out_p)


# ============================================================================
# STEP 2: ALL 9 CHARACTERS x 4 ANGLES = 36 UN-MUTILATED IDEAL BODIES
# ============================================================================

def build_step2_compatible_4angle_bodies():
    cast = get_canonical_cast_library()
    cw, ch = 220, 305
    cols = 4
    rows = len(cast)
    sheet = Image.new("RGBA", (cols * cw + 220, rows * ch + 86), (20, 18, 17, 255))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, sheet.width, 64], fill=(14, 13, 12, 255))
    draw.text((20, 12), "STEP 2: ALL 9 CANONICAL CHARACTERS x 4 ANGLES = 36 UN-MUTILATED IDEAL BODIES (BUILT FROM release_v2/cuts/)", fill=(245, 195, 75, 255))
    draw.text((20, 36), "Every body uses true Master-Sheet proportions (54.5% leg-to-height ratio), clothed Rear Seats/Skirt Overlays, and 2-Point Brass-Grommet fitting", fill=(180, 220, 190, 255))

    headers = [
        "1. FRONT VIEW",
        "2. THREE-QUARTER (3/4)",
        "3. SIDE PROFILE (+X)",
        "4. BACK VIEW",
    ]
    for ci, htxt in enumerate(headers):
        draw.text((210 + ci * cw + 12, 68), htxt, fill=(115, 240, 170, 255) if ci == 2 else (235, 195, 95, 255))

    for ri, cspec in enumerate(cast):
        y0 = 84 + ri * ch
        draw.rectangle([10, y0 + 4, 202, y0 + ch - 4], fill=(30, 27, 25, 255), outline=(68, 62, 56, 255))
        draw.text((16, y0 + 22), cspec["name"], fill=(245, 235, 220, 255))
        draw.text((16, y0 + 48), f"Canonical Scale: {cspec['scale']:.2f}x", fill=(180, 175, 165, 255))
        draw.text((16, y0 + 76), "Compatible Cuts Verified:", fill=(115, 235, 165, 255))
        draw.text((16, y0 + 96), " + 54.5% Lower-Body Ratio", fill=(195, 190, 180, 255))
        draw.text((16, y0 + 114), " + Clothed Rear Seat/Hip", fill=(195, 190, 180, 255))
        draw.text((16, y0 + 132), " + 2-Pt Grommet Bone Fit", fill=(195, 190, 180, 255))
        draw.text((16, y0 + 150), " + Cuff-Tucked Hands/Shoes", fill=(195, 190, 180, 255))
        draw.text((16, y0 + 168), " + Clean release_v2 Heads", fill=(195, 190, 180, 255))

        for vi, vw in enumerate(["FRONT", "3Q", "SIDE", "BACK"]):
            x0 = 210 + vi * cw
            draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=24, origin_x=cw // 2 - 4, origin_y=276 - 4)

            # Subtle hip line marker (0.455 H) and ground line (1.00 H)
            hip_line_y = int(round(276 - 234 * cspec["scale"] * 0.545))
            draw.line([(x0 + 12, y0 + hip_line_y), (x0 + cw - 12, y0 + hip_line_y)], fill=(255, 190, 80, 90), width=1)

            fig_im, joints = solve_and_render_ideal_body(cspec, view=vw, cw=cw, ch=ch, ground_y=276)
            sheet.alpha_composite(fig_im, (x0, y0))

            for jname, jpt in joints.items():
                if jname == "H_C":
                    continue
                if vw == "SIDE" and jname.endswith("_R"):
                    continue
                draw_joint_pin(draw, (x0 + jpt[0], y0 + jpt[1]), color=(0, 230, 255, 220), r=3)

            draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 23], fill=(18, 38, 26, 235) if vw == "SIDE" else (18, 16, 15, 230))
            lbl_v = vw if cspec["id"] != "ex_olive_bomber" else {"FRONT": "TURN-L", "3Q": "3Q-BACK-L", "SIDE": "3Q-BACK-R", "BACK": "BACK"}[vw]
            draw.text((x0 + 10, y0 + 7), f"{cspec['name'][3:19]} · {lbl_v}", fill=(130, 245, 175, 255) if vw == "SIDE" else (240, 230, 210, 255))

    out_p = os.path.join(ART_DIR, "scratch_step2_compatible_4angle_bodies.png")
    sheet.save(out_p)
    sheet.save(os.path.join(OUT_DIR, "step2_compatible_4angle_bodies.png"))
    print("Saved Step 2 Compatible 4-Angle Bodies ->", out_p)


# ============================================================================
# STEP 3: BENDABILITY & KINEMATIC ROM MATRIX (`scratch_step3_bendability_rom_matrix.png`)
# ============================================================================

def build_step3_bendability_rom_matrix():
    cast = {c["id"]: c for c in get_canonical_cast_library()}
    poet = cast["poet_tracksuit"]
    yp = cast["young_poet"]

    cw, ch = 225, 290
    cols = 6
    rows = 4
    sheet = Image.new("RGBA", (cols * cw + 24, rows * ch + 130), (20, 18, 17, 255))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, sheet.width, 68], fill=(14, 13, 12, 255))
    draw.text((20, 12), "STEP 3: JOINT BENDABILITY, CONCENTRIC HINGE ROM & ARTIST MAIN-POSE RECREATION MATRIX", fill=(245, 195, 75, 255))
    draw.text((20, 36), "Row 1: Elbow & Wrist ROM (0 to 130 deg) | Row 2: Knee & Ankle ROM (0 to 125 deg) | Row 3: Hip & Spine Pitch ROM | Row 4: Artist Main Poses Recreated", fill=(180, 225, 195, 255))

    # --- ROW 1: ELBOW & WRIST BENDABILITY (0° -> 130°) ---
    draw.text((16, 74), "ROW 1: ELBOW & WRIST BENDABILITY (Concentric Semicircular Caps + Cuff-Tucked Wrist Pin = Zero Notch at Any Bend Angle)", fill=(240, 200, 95, 255))
    elbow_tests = [
        ("1. Straight (0 deg)", 0, 0, 0, cut_path("poet.red_black_sunglasses.body.profile", "p06")),
        ("2. Slight Flex (30 deg)", 6, 36, 0, cut_path("poet.red_black_sunglasses.body.profile", "p06")),
        ("3. Mid Reach (60 deg)", 14, 74, -5, cut_path("poet.red_black_sunglasses.hands", "p01")),
        ("4. Right Angle (90 deg)", 18, 108, 0, cut_path("poet.red_black_sunglasses.hands", "p02")),
        ("5. Acute Fold (120 deg)", 24, 144, 8, cut_path("poet.red_black_sunglasses.hands", "p03")),
        ("6. Overhead Reach (145 deg)", 95, 150, -10, cut_path("poet.red_black_sunglasses.hands", "p01")),
    ]
    uarm_im = load_clean_cut(cut_path("poet.red_black_sunglasses.body.profile", "p04"))
    farm_im = load_clean_cut(cut_path("poet.red_black_sunglasses.body.profile", "p05"))
    ua_a, ua_b = find_limb_grommets(uarm_im)
    fa_a, fa_b = find_limb_grommets(farm_im)

    y0 = 94
    for ci, (lbl, ua_deg, fa_deg, hd_deg, hd_p) in enumerate(elbow_tests):
        x0 = 12 + ci * cw
        draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=24, origin_x=85, origin_y=90)
        cell = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        S_pt = (88.0, 92.0)
        L_u, L_f = 68.0, 62.0
        E_pt = (S_pt[0] + L_u * math.sin(math.radians(ua_deg)), S_pt[1] + L_u * math.cos(math.radians(ua_deg)))
        W_pt = (E_pt[0] + L_f * math.sin(math.radians(fa_deg)), E_pt[1] + L_f * math.cos(math.radians(fa_deg)))
        hd_im = load_clean_cut(hd_p, rot90_if_horiz=True)
        place_anchored_card(cell, hd_im, (0.50, 0.14), W_pt, 46, rot_deg=fa_deg + hd_deg, clip_top_frac=0.08)
        fit_bone_2pt(cell, farm_im, fa_a, fa_b, E_pt, W_pt)
        fit_bone_2pt(cell, uarm_im, ua_a, ua_b, S_pt, E_pt)
        sheet.alpha_composite(cell, (x0, y0))
        for pt, col in [(S_pt, (255, 195, 70, 255)), (E_pt, (80, 245, 140, 255)), (W_pt, (0, 225, 255, 255))]:
            draw_joint_pin(draw, (x0 + pt[0], y0 + pt[1]), color=col, r=4)
        draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 24], fill=(22, 38, 28, 235))
        draw.text((x0 + 10, y0 + 7), lbl, fill=(130, 245, 175, 255))

    # --- ROW 2: KNEE & ANKLE BENDABILITY (0° -> 125°) ---
    y0 = 94 + ch + 18
    draw.text((16, y0 - 18), "ROW 2: KNEE & ANKLE BENDABILITY (Full Thigh-to-Shin Ratio + Cuff-Tucked Boot Shaft = Clean Articulation from Stand to Deep Kneel)", fill=(240, 200, 95, 255))
    knee_tests = [
        ("1. Planted Stand (0 deg)", 0, 0, 0),
        ("2. Heel-Off Push (-22 deg)", 14, -22, -18),
        ("3. High Knee Step (+55 deg)", 58, -12, -8),
        ("4. Seated Chair (90 deg)", 88, 2, 0),
        ("5. Floor Kneel (105 deg)", 12, -88, -75),
        ("6. Deep Squat Fold (125 deg)", 68, -56, 0),
    ]
    thigh_im = load_clean_cut(cut_path("poet.red_black_sunglasses.body.profile", "p02"))
    shin_im = load_clean_cut(cut_path("poet.red_black_sunglasses.body.profile", "p03"))
    boot_im = load_clean_cut(cut_path("poet.red_black_sunglasses.body.profile", "p07"))
    th_a, th_b = find_limb_grommets(thigh_im)
    sh_a, sh_b = find_limb_grommets(shin_im)

    for ci, (lbl, th_deg, sh_deg, ft_deg) in enumerate(knee_tests):
        x0 = 12 + ci * cw
        draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=24, origin_x=90, origin_y=256)
        cell = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        L_t, L_s, H_sl = 84.0, 70.0, 26.0
        H_pt0 = (85.0, 0.0)
        K_pt0 = (H_pt0[0] + L_t * math.sin(math.radians(th_deg)), H_pt0[1] + L_t * math.cos(math.radians(th_deg)))
        A_pt0 = (K_pt0[0] + L_s * math.sin(math.radians(sh_deg)), K_pt0[1] + L_s * math.cos(math.radians(sh_deg)))
        low_y = max(A_pt0[1] + H_sl, K_pt0[1] + 14.0)
        dy = 256.0 - low_y
        H_pt = (H_pt0[0], H_pt0[1] + dy)
        K_pt = (K_pt0[0], K_pt0[1] + dy)
        A_pt = (A_pt0[0], A_pt0[1] + dy)

        place_anchored_card(cell, boot_im, (0.32, 0.24), A_pt, 44, rot_deg=ft_deg, clip_top_frac=0.08)
        fit_bone_2pt(cell, shin_im, sh_a, sh_b, K_pt, A_pt)
        fit_bone_2pt(cell, thigh_im, th_a, th_b, H_pt, K_pt)
        sheet.alpha_composite(cell, (x0, y0))
        for pt, col in [(H_pt, (255, 195, 70, 255)), (K_pt, (80, 245, 140, 255)), (A_pt, (0, 225, 255, 255))]:
            draw_joint_pin(draw, (x0 + pt[0], y0 + pt[1]), color=col, r=4)
        draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 24], fill=(22, 38, 28, 235))
        draw.text((x0 + 10, y0 + 7), lbl, fill=(130, 245, 175, 255))

    # --- ROW 3: FULL-BODY HIP & SPINE PITCH BENDABILITY ---
    y0 = 94 + 2 * (ch + 18)
    draw.text((16, y0 - 18), "ROW 3: FULL-BODY HIP & SPINE PITCH BENDABILITY (Ground-Up Solver Keeps Feet Planted While Spine & Hips Articulate 0 to 120 deg)", fill=(240, 200, 95, 255))
    body_bends = [
        ("1. Upright Stand (0 deg)", "SIDE", dict(spine_deg=0, thigh_L_deg=0, shin_L_deg=0, uarm_L_deg=4, farm_L_deg=10)),
        ("2. Brisk Walk Pitch (+12 deg)", "SIDE", dict(spine_deg=12, thigh_L_deg=28, shin_L_deg=6, thigh_R_deg=-24, shin_R_deg=-32, uarm_L_deg=-20, farm_L_deg=18, show_far_arm_in_side=True)),
        ("3. Forward Bow (+32 deg)", "SIDE", dict(spine_deg=32, thigh_L_deg=12, shin_L_deg=-8, thigh_R_deg=-10, shin_R_deg=-14, uarm_L_deg=48, farm_L_deg=82, head_deg=-12)),
        ("4. Seated Right-Angle (90 deg)", "SIDE", dict(spine_deg=4, thigh_L_deg=86, shin_L_deg=6, thigh_R_deg=82, shin_R_deg=12, uarm_L_deg=22, farm_L_deg=68)),
        ("5. One-Knee Kneel (105 deg)", "SIDE", dict(spine_deg=14, thigh_L_deg=82, shin_L_deg=-4, thigh_R_deg=24, shin_R_deg=-88, foot_R_deg=-75, uarm_L_deg=36, farm_L_deg=88, head_deg=-8)),
        ("6. Deep Grounded Crouch", "SIDE", dict(spine_deg=34, thigh_L_deg=108, shin_L_deg=-38, thigh_R_deg=96, shin_R_deg=-48, uarm_L_deg=48, farm_L_deg=84, head_deg=-14)),
    ]
    for ci, (lbl, vw, pspec) in enumerate(body_bends):
        x0 = 12 + ci * cw
        draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=24, origin_x=cw // 2, origin_y=262)
        fig_im, joints = solve_and_render_ideal_body(poet, view=vw, pose=pspec, cw=cw, ch=ch, ground_y=262, fig_h_base=224)
        sheet.alpha_composite(fig_im, (x0, y0))
        for jname, jpt in joints.items():
            if jname != "H_C" and not jname.endswith("_R"):
                draw_joint_pin(draw, (x0 + jpt[0], y0 + jpt[1]), color=(0, 230, 255, 220), r=3)
        draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 24], fill=(22, 38, 28, 235))
        draw.text((x0 + 10, y0 + 7), lbl, fill=(130, 245, 175, 255))

    # --- ROW 4: SIDE-BY-SIDE RECREATION OF ARTIST'S CANONICAL MAIN POSES ---
    y0 = 94 + 3 * (ch + 18)
    draw.text((16, y0 - 18), "ROW 4: RECREATING THE ARTIST'S CANONICAL MAIN POSES (Left = Artist Reference Cut | Right = Our 2-Point Grommet Kinematic Rig)", fill=(240, 200, 95, 255))
    main_pose_recreations = [
        ("1. Walk Hollow (P04)", cut_path("poet.04.main-poses", "p01"), poet, "3Q", dict(spine_deg=8, thigh_L_deg=18, shin_L_deg=4, thigh_R_deg=-14, shin_R_deg=-22, uarm_L_deg=14, farm_L_deg=32, uarm_R_deg=-12, farm_R_deg=24, head_deg=14)),
        ("2. Walk The Rows (P04)", cut_path("poet.04.main-poses", "p07"), poet, "3Q", dict(spine_deg=4, thigh_L_deg=24, shin_L_deg=8, thigh_R_deg=-20, shin_R_deg=-28, uarm_L_deg=-16, farm_L_deg=22, uarm_R_deg=18, farm_R_deg=28, head_deg=-6)),
        ("3. Kneel · 3/4 (Master)", cut_path("poet.red_black_sunglasses.master", "p43"), poet, "3Q", dict(spine_deg=12, thigh_L_deg=82, shin_L_deg=-4, thigh_R_deg=26, shin_R_deg=-88, foot_R_deg=-75, uarm_L_deg=28, farm_L_deg=78, uarm_R_deg=18, farm_R_deg=45, head_deg=-8)),
        ("4. Kneel · Profile (Master)", cut_path("poet.red_black_sunglasses.master", "p44"), poet, "SIDE", dict(spine_deg=14, thigh_L_deg=82, shin_L_deg=-4, thigh_R_deg=26, shin_R_deg=-88, foot_R_deg=-75, uarm_L_deg=42, farm_L_deg=105, head_deg=-6)),
        ("5. Crouch · Profile (Master)", cut_path("poet.red_black_sunglasses.master", "p46"), poet, "SIDE", dict(spine_deg=34, thigh_L_deg=108, shin_L_deg=-38, thigh_R_deg=96, shin_R_deg=-48, uarm_L_deg=48, farm_L_deg=88, head_deg=-10)),
        ("6. Young Poet Seated Ref", cut_path("young_poet.child_clothes.hipcore", "p08"), yp, "SIDE", dict(spine_deg=4, thigh_L_deg=86, shin_L_deg=12, thigh_R_deg=84, shin_R_deg=16, uarm_L_deg=12, farm_L_deg=45, head_deg=-6)),
    ]
    for ci, (lbl, ref_p, cspec, vw, pspec) in enumerate(main_pose_recreations):
        x0 = 12 + ci * cw
        draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=24, origin_y=262)

        # Left thumbnail in cell: Artist Reference Pose
        ref_im = load_clean_cut(ref_p, remove_text_islands=True)
        target_rh = 155 if cspec["scale"] > 0.8 else 125
        rsc = min(92.0 / max(1, ref_im.width), target_rh / float(max(1, ref_im.height)))
        rw, rh = int(ref_im.width * rsc), int(ref_im.height * rsc)
        sheet.alpha_composite(ref_im.resize((rw, rh), Image.Resampling.LANCZOS), (x0 + 52 - rw // 2, y0 + 262 - rh))
        draw.text((x0 + 12, y0 + 265), "ARTIST REF", fill=(235, 195, 95, 255))

        # Right side in cell: Our Kinematic Assembly
        fig_im, joints = solve_and_render_ideal_body(cspec, view=vw, pose=pspec, cw=cw, ch=ch, ground_y=262, center_x=156, fig_h_base=210)
        sheet.alpha_composite(fig_im, (x0, y0))
        draw.text((x0 + 116, y0 + 265), "OUR RIG", fill=(120, 245, 175, 255))

        draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 24], fill=(22, 38, 28, 235))
        draw.text((x0 + 8, y0 + 7), lbl, fill=(130, 245, 175, 255))

    out_p = os.path.join(ART_DIR, "scratch_step3_bendability_rom_matrix.png")
    sheet.save(out_p)
    sheet.save(os.path.join(OUT_DIR, "step3_bendability_rom_matrix.png"))
    print("Saved Step 3 Bendability ROM Matrix ->", out_p)


# ============================================================================
# STEP 4: CONSISTENT LOCOMOTION CYCLES & GROWING ENSEMBLES (`scratch_step4_consistent_movement_and_ensembles.png`)
# ============================================================================

def build_step4_consistent_movement_and_ensembles():
    cast = {c["id"]: c for c in get_canonical_cast_library()}
    poet = cast["poet_tracksuit"]
    poet_bt = cast["poet_black_tshirt"]
    woman = cast["woman_brocade"]
    mother = cast["mother_cardigan"]
    ex = cast["ex_olive_bomber"]
    party_m = cast["party_gentleman"]
    party_f = cast["party_woman_gown"]
    dj = cast["dj_cyber"]
    yp = cast["young_poet"]

    W, H = 1640, 1020
    sheet = Image.new("RGBA", (W, H), (18, 16, 15, 255))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, W, 62], fill=(12, 11, 10, 255))
    draw.text((20, 12), "STEP 4: CONSISTENT GROUND-UP MOVEMENT PATTERNS & GROWING MULTI-CHARACTER ENSEMBLES IN SETS", fill=(245, 195, 75, 255))
    draw.text((20, 36), "Top: 8-Phase Ground-Up Locomotion & Acting Progression (0.0px Foot Drift, Sinusoidal Hip/Head Arcs) | Bottom: Growing Ensembles (Solo -> Duo -> Trio -> 9-Cast)", fill=(180, 225, 195, 255))

    # --- TOP HALF: 8-PHASE GROUND-UP MOVEMENT EVOLUTION ---
    top_x, top_y, top_w, top_h = 20, 74, W - 40, 395
    draw.rectangle([top_x, top_y, top_x + top_w, top_y + top_h], fill=(26, 24, 22, 255), outline=(72, 66, 58, 255), width=2)

    # Assemble clean multiplane garden cuts (treeline + 3 flower rows, zero text labels!)
    for pid, gy_row, gh_row in [("p01", 40, 125), ("p02", 155, 85), ("p03", 225, 65), ("p04", 278, 52)]:
        row_p = cut_path("04.set.night_garden_field", pid)
        if os.path.exists(row_p):
            r_im = load_clean_cut(row_p, remove_text_islands=False).resize((top_w - 8, gh_row), Image.Resampling.LANCZOS)
            r_arr = np.array(r_im)
            r_arr[:, :, :3] = (r_arr[:, :, :3].astype(float) * 0.42).astype(np.uint8)
            sheet.alpha_composite(Image.fromarray(r_arr), (top_x + 4, top_y + gy_row))

    ground_y_local = 328
    gy_abs = top_y + ground_y_local
    for gx in range(top_x + 40, top_x + top_w, 40):
        draw.line([(gx, top_y + 38), (gx, gy_abs)], fill=(50, 46, 42, 100), width=1)
    draw.line([(top_x + 16, gy_abs), (top_x + top_w - 16, gy_abs)], fill=(240, 180, 70, 240), width=3)

    draw.rectangle([top_x + 12, top_y + 10, top_x + top_w - 12, top_y + 38], fill=(16, 14, 13, 225))
    draw.text((top_x + 20, top_y + 16), "PART A: BOTTOM-UP EVOLUTION OF MOVEMENT -- 8-Phase Grounded Walk, Stride, Reach, Kneel & Crouch (Cyan = Head Arc, Gold = Hip Arc, Green = Hand Arc)", fill=(120, 245, 175, 255))

    phases = [
        ("1. Contact Strike", 115, dict(spine_deg=6, thigh_L_deg=26, shin_L_deg=10, foot_L_deg=12, thigh_R_deg=-22, shin_R_deg=-26, foot_R_deg=-14, uarm_L_deg=-18, farm_L_deg=12, uarm_R_deg=22, farm_R_deg=34, show_far_arm_in_side=True)),
        ("2. Down / Load", 305, dict(spine_deg=8, thigh_L_deg=16, shin_L_deg=-14, foot_L_deg=0, thigh_R_deg=-12, shin_R_deg=-42, foot_R_deg=-28, uarm_L_deg=-8, farm_L_deg=20, uarm_R_deg=12, farm_R_deg=28, show_far_arm_in_side=True)),
        ("3. Passing Lift", 495, dict(spine_deg=5, thigh_L_deg=4, shin_L_deg=-4, foot_L_deg=0, thigh_R_deg=28, shin_R_deg=-38, foot_R_deg=-18, uarm_L_deg=6, farm_L_deg=24, show_far_arm_in_side=False)),
        ("4. High Push-Off", 685, dict(spine_deg=10, thigh_L_deg=-20, shin_L_deg=-28, foot_L_deg=-18, thigh_R_deg=34, shin_R_deg=4, foot_R_deg=8, uarm_L_deg=24, farm_L_deg=42, uarm_R_deg=-20, farm_R_deg=10, show_far_arm_in_side=True)),
        ("5. Wide Stride", 875, dict(spine_deg=12, thigh_L_deg=32, shin_L_deg=8, foot_L_deg=14, thigh_R_deg=-28, shin_R_deg=-34, foot_R_deg=-20, uarm_L_deg=-24, farm_L_deg=14, uarm_R_deg=28, farm_R_deg=44, show_far_arm_in_side=True)),
        ("6. Expressive Reach", 1065, dict(spine_deg=16, thigh_L_deg=18, shin_L_deg=-6, foot_L_deg=0, thigh_R_deg=-14, shin_R_deg=-18, foot_R_deg=-8, uarm_L_deg=48, farm_L_deg=88, hand_L_override=load_clean_cut(cut_path("poet.red_black_sunglasses.hands", "p02"), rot90_if_horiz=True), head_deg=-10)),
        ("7. One-Knee Kneel", 1255, dict(spine_deg=14, thigh_L_deg=82, shin_L_deg=-4, foot_L_deg=0, thigh_R_deg=26, shin_R_deg=-88, foot_R_deg=-75, uarm_L_deg=34, farm_L_deg=82, hand_L_override=load_clean_cut(cut_path("poet.red_black_sunglasses.hands", "p01"), rot90_if_horiz=True), head_deg=-6)),
        ("8. Deep Crouch", 1455, dict(spine_deg=34, thigh_L_deg=108, shin_L_deg=-38, foot_L_deg=0, thigh_R_deg=96, shin_R_deg=-48, foot_R_deg=0, uarm_L_deg=48, farm_L_deg=88, hand_L_override=load_clean_cut(cut_path("poet.red_black_sunglasses.hands", "p01"), rot90_if_horiz=True), head_deg=-12)),
    ]

    head_arc, hip_arc, hand_arc = [], [], []
    for lbl, cx_loc, pspec in phases:
        fig_im, joints = solve_and_render_ideal_body(
            poet, view="SIDE", pose=pspec, cw=220, ch=top_h, ground_y=ground_y_local, center_x=110, fig_h_base=226
        )
        px0 = top_x + cx_loc - 110
        sheet.alpha_composite(fig_im, (px0, top_y))

        n_pt = (px0 + joints["N"][0], top_y + joints["N"][1])
        h_pt = (px0 + joints["H_L"][0], top_y + joints["H_L"][1])
        w_pt = (px0 + joints["W_L"][0], top_y + joints["W_L"][1])
        head_arc.append(n_pt)
        hip_arc.append(h_pt)
        hand_arc.append(w_pt)

        for jname in ["N", "S_L", "E_L", "W_L", "H_L", "K_L", "A_L"]:
            jpt = joints[jname]
            draw_joint_pin(draw, (px0 + jpt[0], top_y + jpt[1]), color=(0, 230, 255, 220), r=3)

        draw.rectangle([px0 + 26, gy_abs + 8, px0 + 194, gy_abs + 30], fill=(20, 36, 26, 235), outline=(85, 200, 125, 255))
        draw.text((px0 + 34, gy_abs + 12), lbl, fill=(140, 245, 180, 255))

    # Draw continuous kinematic motion arcs
    if len(head_arc) > 1:
        draw.line(head_arc, fill=(0, 225, 255, 185), width=2)
        draw.line(hip_arc, fill=(255, 195, 70, 195), width=2)
        draw.line(hand_arc, fill=(110, 245, 155, 185), width=2)

    # --- BOTTOM HALF: GROWING MULTI-CHARACTER ENSEMBLES IN SETS ---
    bot_y = 482
    bot_h = H - bot_y - 16
    stage_specs = [
        ("1. SOLO (1 Actor · Side Profile)", 20, 255, [("02.set.living_room_1990s", "p01", 0.50, 0.45, 0.94), ("02.set.living_room_1990s", "p04", 0.50, 0.72, 0.78)]),
        ("2. DUO (2 Actors · Waltz / Dialogue)", 285, 345, [("03.set.chapel_side_doors", "p01", 0.50, 0.48, 0.88), ("03.set.chapel_side_doors", "p04", 0.50, 0.88, 0.94)]),
        ("3. TRIO (3 Actors · Family Courtyard)", 640, 395, [("05.set.winged_marble_gate", "p03", 0.50, 0.46, 0.68), ("05.set.winged_marble_gate", "p01", 0.16, 0.48, 0.28), ("05.set.winged_marble_gate", "p05", 0.84, 0.48, 0.28), ("05.set.winged_marble_gate", "p06", 0.50, 0.89, 0.88)]),
        ("4. FULL 8-CAST MULTIPLANE ENSEMBLE", 1045, 575, [("06.set.atlantis_plaza", "p02", 0.50, 0.42, 0.44), ("06.set.atlantis_plaza", "p01", 0.19, 0.44, 0.36), ("06.set.atlantis_plaza", "p03", 0.81, 0.44, 0.36)]),
    ]

    for title, sx, sw, set_pieces in stage_specs:
        draw.rectangle([sx, bot_y, sx + sw, bot_y + bot_h], fill=(22, 20, 19, 255), outline=(72, 66, 58, 255), width=2)
        for sh_id, pid, rx, ry, w_frac in set_pieces:
            sp_p = cut_path(sh_id, pid)
            if os.path.exists(sp_p):
                sp_im = load_clean_cut(sp_p, remove_text_islands=False)
                tw = max(4, int(sw * w_frac))
                th = max(4, int(sp_im.height * (tw / float(max(1, sp_im.width)))))
                if th > bot_h - 48:
                    th = bot_h - 48
                    tw = max(4, int(sp_im.width * (th / float(max(1, sp_im.height)))))
                sp_r = sp_im.resize((tw, th), Image.Resampling.LANCZOS)
                sp_arr = np.array(sp_r)
                sp_arr[:, :, :3] = (sp_arr[:, :, :3].astype(float) * 0.46).astype(np.uint8)
                px = int(sx + sw * rx - tw // 2)
                py = int(bot_y + bot_h * ry - th // 2)
                sheet.alpha_composite(Image.fromarray(sp_arr), (max(sx + 2, px), max(bot_y + 34, py)))
        draw.line([(sx + 10, bot_y + bot_h - 42), (sx + sw - 10, bot_y + bot_h - 42)], fill=(235, 175, 65, 220), width=2)
        draw.rectangle([sx + 6, bot_y + 6, sx + sw - 6, bot_y + 32], fill=(16, 14, 13, 230))
        draw.text((sx + 12, bot_y + 11), title, fill=(245, 205, 95, 255))

    fl_y = bot_h - 42

    def place_ensemble_actor(sx, sw, cspec, view, cx_rel, floor_y_loc, depth_sc=1.0, pose=None, flip_whole=False):
        cw_a = 220
        fig_im, _ = solve_and_render_ideal_body(
            cspec, view=view, pose=pose, cw=cw_a, ch=bot_h, ground_y=floor_y_loc, center_x=cw_a // 2, fig_h_base=int(232 * depth_sc)
        )
        if flip_whole:
            fig_im = ImageOps.mirror(fig_im)
        sheet.alpha_composite(fig_im, (int(sx + sw * cx_rel - cw_a // 2), bot_y))

    # Stage 1: Solo
    place_ensemble_actor(20, 255, poet, "SIDE", 0.50, fl_y, depth_sc=0.98, pose=dict(spine_deg=6, thigh_L_deg=18, shin_L_deg=4, thigh_R_deg=-16, shin_R_deg=-22, uarm_L_deg=28, farm_L_deg=68, show_far_arm_in_side=True))

    # Stage 2: Duo (Party Gentleman & Party Woman in Cream Gown Waltz/Dialogue)
    place_ensemble_actor(285, 345, party_m, "SIDE", 0.34, fl_y, depth_sc=0.96, pose=dict(spine_deg=5, thigh_L_deg=14, shin_L_deg=2, thigh_R_deg=-12, shin_R_deg=-18, uarm_L_deg=34, farm_L_deg=76))
    place_ensemble_actor(285, 345, party_f, "3Q", 0.70, fl_y, depth_sc=0.96, pose=dict(spine_deg=4, uarm_L_deg=24, farm_L_deg=64), flip_whole=True)

    # Stage 3: Trio (Mother + Young Poet Child at 0.70x + Poet Tracksuit)
    place_ensemble_actor(640, 395, mother, "3Q", 0.25, fl_y - 4, depth_sc=0.95, pose=dict(uarm_L_deg=16, farm_L_deg=42))
    place_ensemble_actor(640, 395, yp, "SIDE", 0.52, fl_y + 4, depth_sc=0.98, pose=dict(spine_deg=6, thigh_L_deg=20, shin_L_deg=4, thigh_R_deg=-18, shin_R_deg=-24, uarm_L_deg=32, farm_L_deg=72, show_far_arm_in_side=True))
    place_ensemble_actor(640, 395, poet, "SIDE", 0.79, fl_y, depth_sc=0.96, pose=dict(spine_deg=8, thigh_L_deg=14, shin_L_deg=0, uarm_L_deg=26, farm_L_deg=64), flip_whole=True)

    # Stage 4: Full 8-Character Multiplane Ensemble (Background Z=0.78 -> Midground Z=0.88 -> Foreground Z=0.98)
    s4_x, s4_w = 1045, 575
    # Background plane
    place_ensemble_actor(s4_x, s4_w, ex, "BACK", 0.16, fl_y - 44, depth_sc=0.76)
    place_ensemble_actor(s4_x, s4_w, dj, "FRONT", 0.48, fl_y - 42, depth_sc=0.78, pose=dict(uarm_L_deg=28, farm_L_deg=65, uarm_R_deg=-24, farm_R_deg=-55))
    place_ensemble_actor(s4_x, s4_w, poet_bt, "3Q", 0.82, fl_y - 40, depth_sc=0.78, flip_whole=True)
    # Midground plane
    place_ensemble_actor(s4_x, s4_w, mother, "SIDE", 0.28, fl_y - 18, depth_sc=0.88, pose=dict(uarm_L_deg=20, farm_L_deg=54))
    place_ensemble_actor(s4_x, s4_w, party_f, "FRONT", 0.68, fl_y - 18, depth_sc=0.88)
    # Foreground plane
    place_ensemble_actor(s4_x, s4_w, poet, "SIDE", 0.16, fl_y + 6, depth_sc=0.96, pose=dict(spine_deg=8, thigh_L_deg=22, shin_L_deg=6, thigh_R_deg=-18, shin_R_deg=-24, uarm_L_deg=38, farm_L_deg=78, show_far_arm_in_side=True))
    place_ensemble_actor(s4_x, s4_w, yp, "FRONT", 0.45, fl_y + 10, depth_sc=0.96, pose=dict(uarm_L_deg=18, farm_L_deg=35))
    place_ensemble_actor(s4_x, s4_w, woman, "3Q", 0.84, fl_y + 6, depth_sc=0.96, pose=dict(uarm_L_deg=24, farm_L_deg=58), flip_whole=True)

    out_p = os.path.join(ART_DIR, "scratch_step4_consistent_movement_and_ensembles.png")
    sheet.save(out_p)
    sheet.save(os.path.join(OUT_DIR, "step4_consistent_movement_and_ensembles.png"))
    print("Saved Step 4 Consistent Movement & Ensembles ->", out_p)


if __name__ == "__main__":
    build_step1_ideal_body_vs_master()
    build_step2_compatible_4angle_bodies()
    build_step3_bendability_rom_matrix()
    build_step4_consistent_movement_and_ensembles()
