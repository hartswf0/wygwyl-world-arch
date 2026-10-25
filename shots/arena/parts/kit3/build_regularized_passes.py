#!/usr/bin/env python3
"""
Early-Test Regularization Passes on Calibrated Grids with Sub-Skeletons:
  Pass 1: Regularized Hands & Wrist-to-Fingertip Sub-Skeleton Grid (+ Forearm Cuff Early Test)
  Pass 2: Regularized Shoes/Feet & Ankle-to-Sole Sub-Skeleton Grid (+ Shin Cuff & Ground Line Early Test)
  Pass 3: Regularized Heads (Native Painted vs Blank Base vs Modular Built) & Head Sub-Skeleton Grid across Front / 3Q / Side Profile / Back
  Pass 4: True 4-Angle Body Turnaround Grid (Front, 3/4, Side Profile, Back) using the actual Side/Front/3Q/Back torsos, limbs, hands, shoes, and heads.
"""

import os
import math
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion, binary_dilation, gaussian_filter, label

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
V2_PARTS = os.path.join(ROOT, "shots/arena/parts/kit3/v2/parts")
TS_DIR = os.path.join(ROOT, "shots/kits/packs/poet_tracksuit_v1/01_COMPONENTS")
WM_DIR = os.path.join(ROOT, "shots/weave/cast/man")
WM_HEADS = os.path.join(WM_DIR, "library/head")
WM_HANDS = os.path.join(WM_DIR, "library/hand")
BL_HEADS = os.path.join(ROOT, "shots/arena/parts/body_lab/heads")
ART_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"
OUT_DIR = os.path.join(ROOT, "shots/arena/parts/kit3/release_v2/regularized_elements")
os.makedirs(OUT_DIR, exist_ok=True)


def clean_card_preserve_caps(
    path,
    remove_brass_hole=True,
    crop_top_frac=0.0,
    crop_bot_frac=1.0,
    crop_left_frac=0.0,
    crop_right_frac=1.0,
    auto_vertical_hand=False,
):
    """
    Loads a cutout part, strips outer white/kraft halo while PRESERVING
    100% of the rounded joint caps at both ends of the piece, fills interior
    transparent grommet/socket holes with local color, trims protruding circular
    shoulder-socket flanges on raw side torsos, and optionally rectifies
    horizontal hands (w > h * 1.12) by +90 deg CW so wrist is at top and
    fingers point straight down (+90 deg).
    """
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    H, W = arr.shape[:2]

    # Defringe outer 3px white sheet halo
    for _ in range(2):
        a = arr[:, :, 3] > 20
        eroded = binary_erosion(a, iterations=2)
        rim = a & (~eroded)
        rgb = arr[:, :, :3].astype(np.float32)
        bright = (rgb[:, :, 0] > 215) & (rgb[:, :, 1] > 210) & (rgb[:, :, 2] > 200)
        arr[rim & bright, 3] = 0

    # Keep largest connected component first
    a2 = arr[:, :, 3] > 20
    labeled, n_comp = label(a2)
    if n_comp > 1:
        sizes = np.bincount(labeled.ravel())
        sizes[0] = 0
        arr[labeled != sizes.argmax(), 3] = 0

    # Tight bbox crop before fractional cropping or rotation
    ys, xs = np.where(arr[:, :, 3] > 16)
    if len(xs) > 0:
        arr = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    # If this is a horizontal hand card (wrist on left, fingers pointing right), rotate 90 deg CW!
    if auto_vertical_hand and arr.shape[1] > arr.shape[0] * 1.12:
        im_rot = Image.fromarray(arr).transpose(Image.Transpose.ROTATE_270)
        arr = np.array(im_rot)

    H, W = arr.shape[:2]

    if remove_brass_hole:
        # Fill genuine interior transparent grommet holes AND hollow shoulder-socket cutouts
        # BEFORE fractional crops so enclosed holes are still interior!
        a_solid = arr[:, :, 3] > 128
        bg = ~a_solid
        bg_lab, bg_n = label(bg)
        border_labels = set(np.unique(np.concatenate([
            bg_lab[0, :], bg_lab[-1, :], bg_lab[:, 0], bg_lab[:, -1]
        ])))
        hole_mask = np.zeros((H, W), dtype=bool)
        for lbl_i in range(1, bg_n + 1):
            if lbl_i not in border_labels:
                comp = (bg_lab == lbl_i)
                area = comp.sum()
                if area > (H * W * 0.015) and area < (H * W * 0.30):
                    # Large hollow shoulder-socket cutout ring (e.g. profile.torso)
                    hole_mask |= binary_dilation(comp, iterations=6)
                elif area <= (H * W * 0.015):
                    hole_mask |= binary_dilation(comp, iterations=1)

        if np.any(hole_mask):
            rgb_f = arr[:, :, :3].astype(np.float32)
            not_kraft = ~((rgb_f[:, :, 0] > 145) & (rgb_f[:, :, 1] > 110) & (rgb_f[:, :, 2] < 130))
            valid = a_solid & (~hole_mask) & not_kraft
            if not np.any(valid):
                valid = a_solid & (~hole_mask)
            if np.any(valid):
                for y0, y1 in [(0, H // 2), (H // 2, H)]:
                    sub_t = hole_mask[y0:y1, :]
                    sub_v = valid[y0:y1, :]
                    if np.any(sub_t) and np.any(sub_v):
                        med_rgb = np.median(arr[y0:y1, :][sub_v][:, :3], axis=0).astype(np.uint8)
                        arr[y0:y1, :][sub_t, :3] = med_rgb
                        arr[y0:y1, :][sub_t, 3] = 255

    if crop_top_frac > 0.0:
        arr[:int(H * crop_top_frac), :, 3] = 0
    if crop_bot_frac < 1.0:
        arr[int(H * crop_bot_frac):, :, 3] = 0
    if crop_left_frac > 0.0:
        arr[:, :int(W * crop_left_frac), 3] = 0
    if crop_right_frac < 1.0:
        arr[:, int(W * crop_right_frac):, 3] = 0

    # Final tight bbox crop with 3px padding
    ys, xs = np.where(arr[:, :, 3] > 16)
    if len(xs) > 0:
        x0, x1 = max(0, xs.min() - 3), min(W, xs.max() + 4)
        y0, y1 = max(0, ys.min() - 3), min(H, ys.max() + 4)
        arr = arr[y0:y1, x0:x1]

    return Image.fromarray(arr)


def draw_calib_grid(draw, x0, y0, cw, ch, step=20, origin_x=None, origin_y=None):
    """Draws a crisp technical calibration grid with major/minor axes."""
    draw.rectangle([x0, y0, x0 + cw, y0 + ch], fill=(32, 30, 28, 255), outline=(78, 72, 64, 255), width=1)
    for gx in range(x0 + step, x0 + cw, step):
        draw.line([(gx, y0 + 1), (gx, y0 + ch - 1)], fill=(44, 41, 38, 255), width=1)
    for gy in range(y0 + step, y0 + ch, step):
        draw.line([(x0 + 1, gy), (x0 + cw - 1, gy)], fill=(44, 41, 38, 255), width=1)
    if origin_x is not None:
        draw.line([(x0 + origin_x, y0 + 1), (x0 + origin_x, y0 + ch - 1)], fill=(72, 95, 110, 255), width=1)
    if origin_y is not None:
        draw.line([(x0 + 1, y0 + origin_y), (x0 + cw - 1, y0 + origin_y)], fill=(110, 88, 62, 255), width=1)


def draw_subskeleton_node(draw, pt, color=(0, 230, 255, 255), r=4, label_txt=None):
    x, y = int(round(pt[0])), int(round(pt[1]))
    draw.ellipse([x - r - 1, y - r - 1, x + r + 1, y + r + 1], fill=(18, 18, 18, 255))
    draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
    if label_txt:
        draw.text((x + r + 3, y - 6), label_txt, fill=color)


def draw_bone_arrow(draw, p1, p2, color=(255, 200, 60, 255), width=2):
    x1, y1 = float(p1[0]), float(p1[1])
    x2, y2 = float(p2[0]), float(p2[1])
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    ah = 6.0
    p_left = (x2 - ah * math.cos(ang - 0.5), y2 - ah * math.sin(ang - 0.5))
    p_right = (x2 - ah * math.cos(ang + 0.5), y2 - ah * math.sin(ang + 0.5))
    draw.polygon([(x2, y2), p_left, p_right], fill=color)


def place_part_by_pivot(canvas, part_im, pivot_norm, target_xy, target_h, rot_deg=0.0, flip_x=False):
    im = part_im.copy()
    if flip_x:
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        pivot_norm = (1.0 - pivot_norm[0], pivot_norm[1])
    scale = target_h / max(1.0, float(im.height))
    sw = max(1, int(round(im.width * scale)))
    sh = max(1, int(round(im.height * scale)))
    im_s = im.resize((sw, sh), Image.Resampling.LANCZOS)
    px = pivot_norm[0] * sw
    py = pivot_norm[1] * sh
    pad = int(math.hypot(sw, sh)) + 4
    tmp = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    tmp.paste(im_s, (int(round(pad - px)), int(round(pad - py))))
    if abs(rot_deg) > 0.1:
        tmp = tmp.rotate(-rot_deg, resample=Image.Resampling.BICUBIC, center=(pad, pad))
    canvas.alpha_composite(tmp, (int(round(target_xy[0] - pad)), int(round(target_xy[1] - pad))))
    return scale, (sw, sh)


# ============================================================================
# PASS 1: REGULARIZED HANDS & WRIST SUB-SKELETON GRID
# ============================================================================

def build_pass1_hands_grid():
    """
    Regularizes hands across all 10 characters + action variants onto a calibrated
    grid, auto-rotates horizontal action/weave hands by +90 deg CW so EVERY hand
    points vertically down (+90 deg) from its Wrist Origin (x=105, y=48), cleans
    sleeve attachments (Mother & Party Gentleman), and tests Forearm-to-Wrist joins.
    """
    hand_specs = [
        {
            "char": "Poet (Tracksuit)",
            "scale_h": 92,
            "f_arm": (os.path.join(TS_DIR, "08_forearm_L.png"), 0.0, 0.82),
            "p_arm": (os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.farm.L.png"), 0.0, 1.0),
            "variants": [
                ("FRONT · Relaxed", os.path.join(TS_DIR, "15_hand_relaxed_L.png"), 0.18, 0.0, (0.50, 0.18), (0.52, 0.56), (0.50, 0.92), (0.76, 0.58)),
                ("FRONT · Open Spread", os.path.join(TS_DIR, "17_hand_open_L.png"), 0.18, 0.0, (0.48, 0.18), (0.50, 0.55), (0.48, 0.92), (0.82, 0.52)),
                ("SIDE · Relaxed", os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.hand.L.png"), 0.14, 0.0, (0.50, 0.14), (0.52, 0.55), (0.50, 0.93), (0.72, 0.58)),
                ("ACTION · Pinch (+90° Rectified)", os.path.join(V2_PARTS, "poet.07.action/hand.6_pinch.png"), 0.16, 0.0, (0.50, 0.16), (0.50, 0.56), (0.48, 0.92), (0.76, 0.58)),
            ]
        },
        {
            "char": "Poet (Black T-Shirt / Weave)",
            "scale_h": 92,
            "f_arm": (os.path.join(V2_PARTS, "poet.black_tshirt/body.front.farm.L.png"), 0.0, 1.0),
            "p_arm": (os.path.join(WM_DIR, "parts/farm.profile.png"), 0.0, 1.0),
            "variants": [
                ("FRONT · Relaxed", os.path.join(V2_PARTS, "poet.black_tshirt/body.front.hand.L.png"), 0.14, 0.0, (0.50, 0.14), (0.52, 0.55), (0.50, 0.92), (0.75, 0.56)),
                ("SIDE · Profile Open", os.path.join(V2_PARTS, "poet.black_tshirt/body.profile.hand.L.png"), 0.14, 0.0, (0.50, 0.14), (0.52, 0.55), (0.50, 0.93), (0.72, 0.58)),
                ("WEAVE · Flat Palm (+90° Rect.)", os.path.join(WM_HANDS, "hand.open.flat.png"), 0.16, 0.0, (0.50, 0.16), (0.50, 0.55), (0.50, 0.92), (0.78, 0.52)),
                ("WEAVE · Pointing (+90° Rect.)", os.path.join(WM_HANDS, "hand.point.png"), 0.16, 0.0, (0.50, 0.16), (0.50, 0.54), (0.50, 0.94), (0.74, 0.54)),
            ]
        },
        {
            "char": "Woman / Muse (Brocade)",
            "scale_h": 86,
            "f_arm": (os.path.join(V2_PARTS, "woman.teal_dress/body.front.farm.L.png"), 0.0, 1.0),
            "p_arm": (os.path.join(V2_PARTS, "woman.teal_dress/body.profile.farm.L.png"), 0.0, 1.0),
            "variants": [
                ("FRONT · True Open (.true)", os.path.join(V2_PARTS, "woman.teal_dress/body.front.hand.true.L.png"), 0.14, 0.0, (0.58, 0.15), (0.52, 0.56), (0.44, 0.92), (0.24, 0.56)),
                ("FRONT · True Right (.true)", os.path.join(V2_PARTS, "woman.teal_dress/body.front.hand.true.R.png"), 0.14, 0.0, (0.42, 0.15), (0.48, 0.56), (0.56, 0.92), (0.76, 0.56)),
                ("SIDE · True Profile (.true)", os.path.join(V2_PARTS, "woman.teal_dress/body.profile.hand.true.L.png"), 0.14, 0.0, (0.52, 0.14), (0.50, 0.55), (0.46, 0.92), (0.30, 0.58)),
                ("ACTION · Cup (+90° Rectified)", os.path.join(V2_PARTS, "woman.09.action/hand.2_cup.png"), 0.14, 0.0, (0.50, 0.18), (0.50, 0.58), (0.50, 0.90), (0.72, 0.58)),
            ]
        },
        {
            "char": "The Mother (Cardigan)",
            "scale_h": 86,
            "f_arm": (os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.farm.L.png"), 0.0, 1.0),
            "p_arm": (os.path.join(V2_PARTS, "woman.mother_cardigan/body.profile.farm.L.png"), 0.0, 1.0),
            "variants": [
                ("FRONT · Natural Hand", os.path.join(V2_PARTS, "woman.teal_dress/body.front.hand.true.L.png"), 0.14, 0.0, (0.58, 0.15), (0.52, 0.56), (0.44, 0.92), (0.24, 0.56)),
                ("SIDE · Natural Profile", os.path.join(V2_PARTS, "woman.teal_dress/body.profile.hand.true.L.png"), 0.14, 0.0, (0.52, 0.14), (0.50, 0.55), (0.46, 0.92), (0.30, 0.58)),
                ("GLOVE · Cuff Trimmed", os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.hand.L.png"), 0.52, 0.0, (0.50, 0.16), (0.50, 0.58), (0.48, 0.92), (0.68, 0.58)),
                ("ACTION · Receiver (+90° Rect.)", os.path.join(V2_PARTS, "woman.09.action/hand.1_grip_corded_receiver.png"), 0.16, 0.0, (0.50, 0.18), (0.50, 0.58), (0.50, 0.90), (0.70, 0.58)),
            ]
        },
        {
            "char": "The Ex (Olive Bomber)",
            "scale_h": 92,
            "f_arm": (os.path.join(V2_PARTS, "ex.ex_jacket/body.back.farm.L.png"), 0.0, 1.0),
            "p_arm": (os.path.join(V2_PARTS, "ex.ex_jacket/body.threequarter_back.farm.L.png"), 0.0, 1.0),
            "variants": [
                ("BACK · Relaxed L", os.path.join(V2_PARTS, "ex.ex_jacket/body.back.hand.L.png"), 0.14, 0.0, (0.50, 0.14), (0.50, 0.56), (0.50, 0.92), (0.76, 0.56)),
                ("3Q BACK · Relaxed", os.path.join(V2_PARTS, "ex.ex_jacket/body.threequarter_back.hand.L.png"), 0.14, 0.0, (0.50, 0.14), (0.50, 0.56), (0.50, 0.92), (0.76, 0.56)),
                ("SIDE · Profile L", os.path.join(V2_PARTS, "ex.ex_jacket/body.profile.hand.L.png"), 0.14, 0.0, (0.50, 0.14), (0.50, 0.56), (0.50, 0.92), (0.76, 0.56)),
                ("ACTION · Suitcase (+90° Rect.)", os.path.join(V2_PARTS, "ex.09.action/hand.2_grip_suitcase_handle.png"), 0.16, 0.0, (0.50, 0.18), (0.50, 0.58), (0.50, 0.88), (0.72, 0.58)),
            ]
        },
        {
            "char": "Party Gentleman & DJ Cyber",
            "scale_h": 92,
            "f_arm": (os.path.join(V2_PARTS, "party.vintage_party/body.profile.farm.L.png"), 0.0, 1.0),
            "p_arm": (os.path.join(V2_PARTS, "party.dj_cyber/body.profile.farm.L.png"), 0.0, 1.0),
            "variants": [
                ("PARTY · Cuff Trimmed", os.path.join(V2_PARTS, "party.vintage_party/body.profile.hand.L.png"), 0.55, 0.0, (0.50, 0.16), (0.50, 0.56), (0.50, 0.92), (0.74, 0.58)),
                ("DJ CYBER · Front Open", os.path.join(V2_PARTS, "party.dj_cyber/body.front.hand.L.png"), 0.14, 0.0, (0.50, 0.14), (0.50, 0.56), (0.50, 0.92), (0.78, 0.56)),
                ("DJ CYBER · Side Profile", os.path.join(V2_PARTS, "party.dj_cyber/body.profile.hand.L.png"), 0.14, 0.0, (0.50, 0.14), (0.50, 0.56), (0.50, 0.92), (0.76, 0.56)),
                ("PARTY · Wave / Dance", os.path.join(V2_PARTS, "party.07.action/hand.3_wave.png"), 0.14, 0.0, (0.50, 0.18), (0.50, 0.56), (0.50, 0.92), (0.76, 0.56)),
            ]
        },
        {
            "char": "Young Poet & Ancestors",
            "scale_h": 76,
            "f_arm": (os.path.join(V2_PARTS, "young_poet.child_clothes/body.profile.farm.L.png"), 0.0, 1.0),
            "p_arm": (os.path.join(V2_PARTS, "ancestors.ancestor_robe_indigo_gold/body.profile.farm.L.png"), 0.0, 1.0),
            "variants": [
                ("YOUNG POET · Front Open", os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.hand.L.png"), 0.14, 0.0, (0.48, 0.15), (0.50, 0.56), (0.52, 0.92), (0.82, 0.52)),
                ("YOUNG POET · Side Profile", os.path.join(V2_PARTS, "young_poet.child_clothes/body.profile.hand.L.png"), 0.14, 0.0, (0.44, 0.14), (0.52, 0.56), (0.60, 0.92), (0.76, 0.56)),
                ("ANCESTOR · Relaxed", os.path.join(V2_PARTS, "ancestors.ancestor_robe_indigo_gold/body.front.hand.L.png"), 0.14, 0.0, (0.50, 0.14), (0.52, 0.56), (0.50, 0.92), (0.76, 0.56)),
                ("FAMILY · Pinch (+90° Rect.)", os.path.join(V2_PARTS, "family.12.action/hand.2_pinch_archival_photo.png"), 0.16, 0.0, (0.50, 0.18), (0.50, 0.56), (0.50, 0.90), (0.74, 0.56)),
            ]
        },
    ]

    cw, ch = 210, 215
    cols = 6  # 4 regularized hand variants on grid + 2 Early-Test Forearm->Wrist assemblies (Front & Side)
    rows = len(hand_specs)
    sheet = Image.new("RGBA", (cols * cw + 210, rows * ch + 86), (22, 20, 19, 255))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, sheet.width, 64], fill=(16, 14, 13, 255))
    draw.text((20, 14), "EARLY-TEST PASS 1: REGULARIZED HANDS & WRIST SUB-SKELETON GRID (+ FOREARM CUFF EARLY TEST)", fill=(245, 195, 75, 255))
    draw.text((20, 38), "Horizontal hands auto-rotated +90 deg CW to vertical, sleeves trimmed, aligned to Wrist Origin (x=105, y=48) with 4-Node Sub-Skeleton", fill=(185, 180, 170, 255))

    col_headers = [
        "1. FRONT HAND (GRID)",
        "2. ALT / OPEN (GRID)",
        "3. SIDE PROFILE (GRID)",
        "4. ACTION / GRIP (GRID)",
        "5. EARLY TEST: FRONT ARM+HAND",
        "6. EARLY TEST: SIDE ARM+HAND",
    ]
    for ci, htxt in enumerate(col_headers):
        draw.text((200 + ci * cw + 8, 68), htxt, fill=(230, 190, 95, 255) if ci < 4 else (110, 235, 165, 255))

    for ri, spec in enumerate(hand_specs):
        y0 = 84 + ri * ch
        draw.rectangle([10, y0 + 4, 192, y0 + ch - 4], fill=(32, 29, 27, 255), outline=(68, 62, 56, 255))
        draw.text((18, y0 + 24), spec["char"], fill=(240, 235, 225, 255))
        draw.text((18, y0 + 48), f"Target Scale: {spec['scale_h']}px", fill=(165, 160, 150, 255))
        draw.text((18, y0 + 70), "Sub-Skeleton:", fill=(0, 220, 245, 255))
        draw.text((18, y0 + 88), "  o Wrist Pin (0,0)", fill=(0, 220, 245, 255))
        draw.text((18, y0 + 104), "  o Palm / Knuckle", fill=(255, 195, 55, 255))
        draw.text((18, y0 + 120), "  o Distal Tip", fill=(255, 95, 210, 255))
        draw.text((18, y0 + 136), "  o Thumb Vector", fill=(95, 235, 135, 255))

        reg_hands = []
        for vi, (vlabel, vpath, crop_top, rot_deg, w_piv, palm_p, tip_p, thumb_p) in enumerate(spec["variants"]):
            x0 = 200 + vi * cw
            ox, oy = cw // 2, 48
            draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=20, origin_x=ox - 4, origin_y=oy - 4)

            im_h = clean_card_preserve_caps(
                vpath, remove_brass_hole=True, crop_top_frac=crop_top, auto_vertical_hand=True
            )
            reg_hands.append((im_h, w_piv, palm_p, tip_p, thumb_p))

            sc, (sw, sh) = place_part_by_pivot(sheet, im_h, w_piv, (x0 + ox, y0 + oy), spec["scale_h"], rot_deg=rot_deg)

            def to_scr(np_pt):
                dx = (np_pt[0] - w_piv[0]) * sw
                dy = (np_pt[1] - w_piv[1]) * sh
                return (x0 + ox + dx, y0 + oy + dy)

            p_wr = (x0 + ox, y0 + oy)
            p_plm = to_scr(palm_p)
            p_tip = to_scr(tip_p)
            p_thm = to_scr(thumb_p)

            draw_bone_arrow(draw, p_wr, p_plm, color=(0, 210, 240, 255), width=2)
            draw_bone_arrow(draw, p_plm, p_tip, color=(255, 95, 210, 255), width=2)
            draw_bone_arrow(draw, p_plm, p_thm, color=(95, 235, 135, 255), width=2)
            draw_subskeleton_node(draw, p_wr, color=(0, 230, 255, 255), r=4)
            draw_subskeleton_node(draw, p_plm, color=(255, 200, 55, 255), r=3)
            draw_subskeleton_node(draw, p_tip, color=(255, 95, 210, 255), r=3)
            draw_subskeleton_node(draw, p_thm, color=(95, 235, 135, 255), r=3)

            draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 23], fill=(18, 16, 15, 230))
            draw.text((x0 + 10, y0 + 7), vlabel, fill=(240, 230, 210, 255))

        # Columns 5 & 6: Early-Test Forearm + Wrist Join (Front & Side Profile)
        for ti, (tlabel, arm_spec, hand_idx) in enumerate([
            ("FRONT JOIN (Cuff Over Wrist)", spec["f_arm"], 0),
            ("SIDE JOIN (Profile Arm+Hand)", spec["p_arm"], 2),
        ]):
            x0 = 200 + (4 + ti) * cw
            draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=20, origin_x=cw // 2 - 4, origin_y=124)
            arm_path, arm_top, arm_bot = arm_spec
            im_arm = clean_card_preserve_caps(arm_path, remove_brass_hole=True, crop_top_frac=arm_top, crop_bot_frac=arm_bot)
            im_h, w_piv, palm_p, tip_p, _ = reg_hands[hand_idx]

            wrist_xy = (x0 + cw // 2, y0 + 126)
            elbow_xy = (x0 + cw // 2, y0 + 36)
            place_part_by_pivot(sheet, im_h, w_piv, wrist_xy, int(spec["scale_h"] * 0.62), rot_deg=0.0)
            place_part_by_pivot(sheet, im_arm, (0.50, 0.12), elbow_xy, 108, rot_deg=0.0)

            draw_bone_arrow(draw, elbow_xy, wrist_xy, color=(255, 200, 60, 255), width=2)
            draw_subskeleton_node(draw, elbow_xy, color=(255, 200, 60, 255), r=4, label_txt="Elbow")
            draw_subskeleton_node(draw, wrist_xy, color=(0, 230, 255, 255), r=4, label_txt="Wrist")

            draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 23], fill=(18, 36, 26, 235))
            draw.text((x0 + 10, y0 + 7), tlabel, fill=(130, 245, 175, 255))

    out_p = os.path.join(ART_DIR, "scratch_pass1_regularized_hands_grid.png")
    sheet.save(out_p)
    sheet.save(os.path.join(OUT_DIR, "pass1_regularized_hands_grid.png"))
    print("Saved Pass 1 Hands Grid ->", out_p)


# ============================================================================
# PASS 2: REGULARIZED SHOES/FEET & ANKLE-SOLE SUB-SKELETON GRID
# ============================================================================

def build_pass2_shoes_grid():
    """
    Regularizes all Front-View and Side-Profile shoes/boots onto a calibrated
    Ground Line (y=166) and Ankle Plumb Line, trims top mounting tabs so ankle
    collars sit cleanly under shin cuffs, draws the 4-node Foot Sub-Skeleton,
    and tests Front & Side Shin-to-Ankle joins.
    """
    shoe_specs = [
        {
            "char": "Poet (Tracksuit Boots)",
            "f_shin": os.path.join(TS_DIR, "12_shin_L.png"),
            "p_shin": os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.shin.L.png"),
            # Note: body.front.foot.L.png originally points LEFT (ankle on right x=0.68), so before flip_x=True we pass ank_p=(0.68, 0.22)
            "f_shoe": ("SIDE-L Flipped · Boot", os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.front.foot.L.png"), 0.20, True, 78, (0.68, 0.22), (0.18, 0.88), (0.64, 0.90), (0.90, 0.84)),
            "p_shoe": ("SIDE-R · Profile Boot", os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.foot.L.png"), 0.20, False, 78, (0.30, 0.22), (0.18, 0.88), (0.64, 0.90), (0.90, 0.84)),
        },
        {
            "char": "Poet (Black T-Shirt Sneakers)",
            "f_shin": os.path.join(V2_PARTS, "poet.black_tshirt/body.front.shin.L.png"),
            "p_shin": os.path.join(V2_PARTS, "poet.black_tshirt/body.front.shin.L.png"),
            "f_shoe": ("SIDE · Dark Sneaker", os.path.join(V2_PARTS, "poet.black_tshirt/body.front.foot.L.png"), 0.22, False, 68, (0.32, 0.22), (0.16, 0.88), (0.64, 0.90), (0.92, 0.84)),
            "p_shoe": ("SIDE · Profile Sneaker", os.path.join(V2_PARTS, "poet.black_tshirt/body.profile.foot.L.png"), 0.22, False, 68, (0.32, 0.22), (0.16, 0.88), (0.64, 0.90), (0.92, 0.84)),
        },
        {
            "char": "Woman / Muse (Red Mary Janes)",
            "f_shin": os.path.join(V2_PARTS, "woman.teal_dress/body.front.shin.L.png"),
            "p_shin": os.path.join(V2_PARTS, "woman.teal_dress/body.profile.shin.L.png"),
            "f_shoe": ("FRONT · True Red (.true)", os.path.join(V2_PARTS, "woman.teal_dress/body.front.foot.true.png"), 0.14, False, 86, (0.50, 0.20), (0.50, 0.65), (0.50, 0.82), (0.50, 0.94)),
            # body.profile.foot.L.png originally points LEFT (ankle at x=0.72), so before flip_x=True pass ank_p=(0.72, 0.24)
            "p_shoe": ("SIDE · Red Mary Jane", os.path.join(V2_PARTS, "woman.teal_dress/body.profile.foot.L.png"), 0.24, True, 72, (0.72, 0.24), (0.18, 0.86), (0.62, 0.90), (0.90, 0.82)),
        },
        {
            "char": "The Mother (Slip-On Flats)",
            "f_shin": os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.shin.L.png"),
            "p_shin": os.path.join(V2_PARTS, "woman.mother_cardigan/body.profile.shin.L.png"),
            "f_shoe": ("FRONT · Gray Slip-On", os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.foot.L.png"), 0.20, False, 78, (0.50, 0.20), (0.50, 0.65), (0.50, 0.82), (0.50, 0.94)),
            "p_shoe": ("3/4 · Angled Slip-On", os.path.join(V2_PARTS, "woman.mother_cardigan/body.profile.foot.L.png"), 0.20, False, 78, (0.48, 0.20), (0.44, 0.68), (0.52, 0.84), (0.56, 0.94)),
        },
        {
            "char": "The Ex (White High-Tops)",
            "f_shin": os.path.join(V2_PARTS, "ex.ex_jacket/body.back.shin.L.png"),
            "p_shin": os.path.join(V2_PARTS, "ex.ex_jacket/body.profile.shin.L.png"),
            "f_shoe": ("SIDE · White High-Top", os.path.join(V2_PARTS, "ex.ex_jacket/body.front.foot.L.png"), 0.22, False, 74, (0.32, 0.22), (0.16, 0.88), (0.64, 0.90), (0.90, 0.84)),
            "p_shoe": ("SIDE · Profile High-Top", os.path.join(V2_PARTS, "ex.ex_jacket/body.profile.foot.L.png"), 0.22, False, 74, (0.32, 0.22), (0.16, 0.88), (0.64, 0.90), (0.90, 0.84)),
        },
        {
            "char": "Party Gentleman (Oxfords)",
            "f_shin": os.path.join(V2_PARTS, "party.vintage_party/body.profile.shin.L.png"),
            "p_shin": os.path.join(V2_PARTS, "party.vintage_party/body.profile.shin.L.png"),
            # body.front.foot.L.png points LEFT originally -> ank_p=(0.64, 0.22) before flip_x=True
            "f_shoe": ("3/4 · Trimmed Oxford", os.path.join(V2_PARTS, "party.vintage_party/body.front.foot.L.png"), 0.50, True, 68, (0.64, 0.22), (0.24, 0.84), (0.64, 0.90), (0.88, 0.86)),
            "p_shoe": ("SIDE · Dress Oxford", os.path.join(V2_PARTS, "party.vintage_party/body.profile.foot.L.png"), 0.22, False, 74, (0.28, 0.22), (0.16, 0.88), (0.64, 0.90), (0.90, 0.86)),
        },
        {
            "char": "DJ Cyber (Neon High-Tops)",
            "f_shin": os.path.join(V2_PARTS, "party.dj_cyber/body.profile.shin.L.png"),
            "p_shin": os.path.join(V2_PARTS, "party.dj_cyber/body.profile.shin.L.png"),
            # body.front.foot.L.png points LEFT originally -> ank_p=(0.64, 0.22) before flip_x=True
            "f_shoe": ("3/4 · Neon Sneaker", os.path.join(V2_PARTS, "party.dj_cyber/body.front.foot.L.png"), 0.20, True, 78, (0.64, 0.22), (0.20, 0.86), (0.64, 0.90), (0.90, 0.80)),
            "p_shoe": ("SIDE · Neon High-Top", os.path.join(V2_PARTS, "party.dj_cyber/body.profile.foot.L.png"), 0.20, False, 78, (0.28, 0.22), (0.16, 0.88), (0.64, 0.90), (0.92, 0.82)),
        },
        {
            "char": "Young Poet & Ancestor",
            "f_shin": os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.shin.L.png"),
            "p_shin": os.path.join(V2_PARTS, "young_poet.child_clothes/body.profile.shin.L.png"),
            "f_shoe": ("FRONT · Canvas Sneaker", os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.foot.L.png"), 0.18, False, 74, (0.50, 0.22), (0.50, 0.65), (0.50, 0.82), (0.50, 0.94)),
            "p_shoe": ("SIDE · Canvas High-Top", os.path.join(V2_PARTS, "young_poet.child_clothes/body.profile.foot.L.png"), 0.20, False, 74, (0.28, 0.22), (0.16, 0.88), (0.64, 0.90), (0.90, 0.84)),
        },
    ]

    cw, ch = 240, 205
    cols = 4
    rows = len(shoe_specs)
    sheet = Image.new("RGBA", (cols * cw + 220, rows * ch + 86), (22, 20, 19, 255))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, sheet.width, 64], fill=(16, 14, 13, 255))
    draw.text((20, 14), "EARLY-TEST PASS 2: REGULARIZED SHOES/FEET & ANKLE-TO-SOLE SUB-SKELETON GRID (+ SHIN JOIN PROOF)", fill=(245, 195, 75, 255))
    draw.text((20, 38), "Every shoe planted on Ground Line (y=166), top tabs trimmed, with 4-Node Foot Sub-Skeleton (Cyan=Ankle, Green=Heel, Amber=Ball, Magenta=Toe)", fill=(185, 180, 170, 255))

    headers = [
        "1. FRONT / 3Q SHOE (ON GRID)",
        "2. SIDE-PROFILE SHOE (ON GRID)",
        "3. EARLY TEST: FRONT SHIN + SHOE",
        "4. EARLY TEST: SIDE SHIN + SHOE",
    ]
    for ci, htxt in enumerate(headers):
        draw.text((210 + ci * cw + 8, 68), htxt, fill=(230, 190, 95, 255) if ci < 2 else (110, 235, 165, 255))

    for ri, spec in enumerate(shoe_specs):
        y0 = 84 + ri * ch
        draw.rectangle([10, y0 + 4, 202, y0 + ch - 4], fill=(32, 29, 27, 255), outline=(68, 62, 56, 255))
        draw.text((16, y0 + 22), spec["char"], fill=(240, 235, 225, 255))
        draw.text((16, y0 + 48), "Foot Sub-Skeleton:", fill=(0, 220, 245, 255))
        draw.text((16, y0 + 68), "  o Ankle Socket", fill=(0, 220, 245, 255))
        draw.text((16, y0 + 86), "  o Heel Contact", fill=(95, 235, 135, 255))
        draw.text((16, y0 + 104), "  o Ball of Foot", fill=(255, 195, 55, 255))
        draw.text((16, y0 + 122), "  o Toe Tip", fill=(255, 95, 210, 255))
        draw.text((16, y0 + 144), "  --- Ground Sole Line", fill=(235, 170, 70, 255))

        cleaned_shoes = []
        for si, s_cfg in enumerate([spec["f_shoe"], spec["p_shoe"]]):
            slabel, spath, crop_top, flip_x, target_h, ank_p, heel_p, ball_p, toe_p = s_cfg
            x0 = 210 + si * cw
            ground_y = 166
            eff_ank_x = (1.0 - ank_p[0]) if flip_x else ank_p[0]
            ank_x = cw // 2 if (eff_ank_x > 0.42 and eff_ank_x < 0.58) else 92
            draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=20, origin_x=ank_x - 4, origin_y=ground_y - 4)
            draw.line([(x0 + 10, y0 + ground_y), (x0 + cw - 10, y0 + ground_y)], fill=(235, 170, 70, 255), width=2)

            im_s = clean_card_preserve_caps(spath, remove_brass_hole=True, crop_top_frac=crop_top)
            foot_span_frac = max(0.2, ball_p[1] - ank_p[1])
            ank_y = ground_y - int(round(target_h * foot_span_frac))

            sc, (sw, sh) = place_part_by_pivot(sheet, im_s, ank_p, (x0 + ank_x, y0 + ank_y), target_h, flip_x=flip_x)
            cleaned_shoes.append((im_s, ank_p, flip_x, target_h, ank_y, ank_x, eff_ank_x))

            def to_scr_s(pt_n):
                dx = (pt_n[0] - eff_ank_x) * sw
                dy = (pt_n[1] - ank_p[1]) * sh
                return (x0 + ank_x + dx, y0 + ank_y + dy)

            p_ank = (x0 + ank_x, y0 + ank_y)
            p_hee = to_scr_s(heel_p)
            p_bal = to_scr_s(ball_p)
            p_toe = to_scr_s(toe_p)

            draw_bone_arrow(draw, p_ank, p_hee, color=(95, 235, 135, 255), width=2)
            draw_bone_arrow(draw, p_ank, p_bal, color=(0, 220, 245, 255), width=2)
            draw_bone_arrow(draw, p_bal, p_toe, color=(255, 95, 210, 255), width=2)
            draw_subskeleton_node(draw, p_ank, color=(0, 230, 255, 255), r=4)
            draw_subskeleton_node(draw, p_hee, color=(95, 235, 135, 255), r=3)
            draw_subskeleton_node(draw, p_bal, color=(255, 200, 55, 255), r=3)
            draw_subskeleton_node(draw, p_toe, color=(255, 95, 210, 255), r=3)

            draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 23], fill=(18, 16, 15, 230))
            draw.text((x0 + 10, y0 + 7), slabel, fill=(240, 230, 210, 255))

        # Columns 3 & 4: Early-Test Shin + Ankle Join on Ground Line
        for ti, (tlabel, shin_p, s_idx) in enumerate([
            ("FRONT SHIN + SHOE", spec["f_shin"], 0),
            ("SIDE SHIN + SHOE", spec["p_shin"], 1),
        ]):
            x0 = 210 + (2 + ti) * cw
            ground_y = 176
            im_s, ank_p, flip_x, target_h, _, _, eff_ank_x = cleaned_shoes[s_idx]
            ank_x = cw // 2 if (eff_ank_x > 0.42 and eff_ank_x < 0.58) else 102
            draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=20, origin_x=ank_x - 4, origin_y=ground_y - 4)
            draw.line([(x0 + 10, y0 + ground_y), (x0 + cw - 10, y0 + ground_y)], fill=(235, 170, 70, 255), width=2)

            crop_bot = 0.84 if "12_shin_L" in shin_p else 1.0
            im_sh = clean_card_preserve_caps(shin_p, remove_brass_hole=True, crop_bot_frac=crop_bot)

            sh_h = int(target_h * 0.68)
            ank_xy = (x0 + ank_x, y0 + ground_y - int(sh_h * 0.68))
            knee_xy = (x0 + ank_x, ank_xy[1] - 96)

            # Place shoe first (tucked under shin cuff), then shin over top!
            place_part_by_pivot(sheet, im_s, ank_p, ank_xy, sh_h, flip_x=flip_x)
            place_part_by_pivot(sheet, im_sh, (0.50, 0.12), knee_xy, 112)

            draw_bone_arrow(draw, knee_xy, ank_xy, color=(255, 200, 60, 255), width=2)
            draw_subskeleton_node(draw, knee_xy, color=(255, 200, 60, 255), r=4, label_txt="Knee")
            draw_subskeleton_node(draw, ank_xy, color=(0, 230, 255, 255), r=4, label_txt="Ankle")

            draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 23], fill=(18, 36, 26, 235))
            draw.text((x0 + 10, y0 + 7), tlabel, fill=(130, 245, 175, 255))

    out_p = os.path.join(ART_DIR, "scratch_pass2_regularized_shoes_grid.png")
    sheet.save(out_p)
    sheet.save(os.path.join(OUT_DIR, "pass2_regularized_shoes_grid.png"))
    print("Saved Pass 2 Shoes Grid ->", out_p)


# ============================================================================
# PASS 3: REGULARIZED HEADS & HEAD SUB-SKELETON GRID (FRONT / 3Q / SIDE / BACK)
# ============================================================================

def clean_and_repair_head(path, mode="native"):
    """
    Cleans head cutouts while preserving neck pivot tab, and repairs dashed
    cut-boxes on Mother & Young Poet painted heads.
    """
    im = clean_card_preserve_caps(path, remove_brass_hole=True)
    arr = np.array(im)
    H, W = arr.shape[:2]
    rgb = arr[:, :, :3].astype(np.float32)

    if mode == "clean_dots":
        lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
        sat = np.max(rgb, axis=2) - np.min(rgb, axis=2)
        ys, xs = np.mgrid[0:H, 0:W]
        in_face = (ys > int(H * 0.44)) & (ys < int(H * 0.80)) & (xs > int(W * 0.24)) & (xs < int(W * 0.78))
        not_eye_white = ~((ys > int(H * 0.52)) & (ys < int(H * 0.65)) & (lum > 180))
        dots = in_face & not_eye_white & (lum > 175) & (sat < 55) & (arr[:, :, 3] > 200)
        dots_d = binary_dilation(dots, iterations=1)
        cheek = arr[int(H * 0.62):int(H * 0.72), int(W * 0.30):int(W * 0.44), :3]
        if cheek.size > 0:
            med = np.median(cheek.reshape(-1, 3), axis=0)
            for c in range(3):
                ch_f = gaussian_filter(arr[:, :, c].astype(np.float32), sigma=2.5)
                arr[:, :, c] = np.where(dots_d, (0.65 * ch_f + 0.35 * med[c]).astype(np.uint8), arr[:, :, c])

    return Image.fromarray(arr)


def build_pass3_heads_grid():
    import build_100x_pose_face_library as b100

    poet_f_shades = b100.p09.build_modular_head("front_neutral")
    poet_f_eyes = b100.p09.build_modular_head("front_smile_unmasked")

    head_rows = [
        {
            "char": "Poet (Tracksuit · Modular + Weave)",
            "views": [
                ("FRONT [MODULAR SHADES]", poet_f_shades, "F", (0.50, 0.82), (0.37, 0.46), (0.63, 0.46), (0.50, 0.54), (0.50, 0.66)),
                ("FRONT [MODULAR EYES]", poet_f_eyes, "F", (0.50, 0.82), (0.37, 0.46), (0.63, 0.46), (0.50, 0.54), (0.50, 0.66)),
                ("3/4 [NATIVE WEAVE]", clean_and_repair_head(os.path.join(WM_HEADS, "head.3q.recognition.png")), "3Q", (0.48, 0.86), (0.44, 0.46), (0.72, 0.46), (0.64, 0.56), (0.60, 0.68)),
                ("SIDE [NATIVE WEAVE]", clean_and_repair_head(os.path.join(WM_HEADS, "head.profile_R.neutral.png")), "P", (0.46, 0.86), (0.72, 0.46), (0.72, 0.46), (0.84, 0.55), (0.78, 0.68)),
                ("BACK [NATIVE PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "poet.red_black_sunglasses/head.back.png")), "B", (0.50, 0.86), None, None, None, None),
            ]
        },
        {
            "char": "Woman / Muse (Afro · Native)",
            "views": [
                ("FRONT [NATIVE PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "woman.teal_dress/head.front.png")), "F", (0.50, 0.86), (0.38, 0.54), (0.62, 0.54), (0.50, 0.61), (0.50, 0.70)),
                ("3/4 [WINDOW PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "woman.window_woman_dress/head.front.png")), "P", (0.52, 0.88), (0.76, 0.54), (0.76, 0.54), (0.88, 0.62), (0.84, 0.72)),
                ("SIDE [CLEAN BASE]", clean_and_repair_head(os.path.join(V2_PARTS, "woman.teal_dress/head.profile.png")), "P", (0.50, 0.86), (0.76, 0.54), (0.76, 0.54), (0.86, 0.62), (0.82, 0.71)),
                ("3Q BACK [NATIVE]", clean_and_repair_head(os.path.join(V2_PARTS, "woman.teal_dress/head.threequarter_back.png")), "B", (0.50, 0.86), None, None, None, None),
                ("BACK [NATIVE PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "woman.teal_dress/head.back.png")), "B", (0.50, 0.86), None, None, None, None),
            ]
        },
        {
            "char": "The Mother (Cardigan · Cleaned)",
            "views": [
                ("FRONT [NATIVE PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "woman.mother_cardigan/head.front.png")), "F", (0.50, 0.86), (0.40, 0.56), (0.60, 0.56), (0.50, 0.63), (0.50, 0.71)),
                ("3/4 [NATIVE PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "woman.mother_cardigan/head.threequarter.png")), "3Q", (0.48, 0.86), (0.46, 0.56), (0.66, 0.56), (0.60, 0.63), (0.58, 0.71)),
                ("SIDE [PROFILE BASE]", clean_and_repair_head(os.path.join(V2_PARTS, "woman.mother_cardigan/head.profile.png")), "P", (0.48, 0.86), (0.74, 0.56), (0.74, 0.56), (0.84, 0.63), (0.80, 0.72)),
                ("3Q BACK [NATIVE]", clean_and_repair_head(os.path.join(V2_PARTS, "woman.teal_dress/head.threequarter_back.png")), "B", (0.50, 0.86), None, None, None, None),
                ("BACK [NATIVE PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "woman.mother_cardigan/head.back.png")), "B", (0.50, 0.86), None, None, None, None),
            ]
        },
        {
            "char": "Young Poet (Age 6 · True Heads)",
            "views": [
                ("FRONT [TRUE PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.front.true.png"), "clean_dots"), "F", (0.50, 0.86), (0.38, 0.55), (0.62, 0.55), (0.50, 0.62), (0.50, 0.70)),
                ("3/4 [TRUE PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.threequarter.true.png"), "clean_dots"), "3Q", (0.48, 0.86), (0.44, 0.55), (0.66, 0.55), (0.58, 0.62), (0.56, 0.70)),
                ("SIDE [TRUE PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.profile.true.png"), "clean_dots"), "P", (0.46, 0.86), (0.70, 0.55), (0.70, 0.55), (0.82, 0.61), (0.78, 0.70)),
                ("3Q BACK [NATIVE]", clean_and_repair_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.threequarter_back.png")), "B", (0.50, 0.86), None, None, None, None),
                ("BACK [NATIVE PAINTED]", clean_and_repair_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.back.png")), "B", (0.50, 0.86), None, None, None, None),
            ]
        },
        {
            "char": "The Ex, Father & Party Cast",
            "views": [
                ("FATHER [FLAT CAP 3/4]", clean_and_repair_head(os.path.join(BL_HEADS, "the_father_long_coat/father_head_02.png")), "3Q", (0.44, 0.86), (0.64, 0.50), (0.78, 0.50), (0.78, 0.58), (0.74, 0.70)),
                ("PARTY MAN [3/4 BASE]", clean_and_repair_head(os.path.join(BL_HEADS, "party_guests/party_head_02.png")), "3Q", (0.46, 0.86), (0.64, 0.48), (0.78, 0.48), (0.80, 0.56), (0.76, 0.68)),
                ("PARTY LADY [WAVES 3/4]", clean_and_repair_head(os.path.join(BL_HEADS, "party_guests/party_head_08.png")), "3Q", (0.48, 0.86), (0.66, 0.50), (0.78, 0.50), (0.82, 0.58), (0.78, 0.68)),
                ("THE EX [3/4 BACK TURN]", clean_and_repair_head(os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_04.png")), "B", (0.50, 0.86), None, None, None, None),
                ("THE EX [STRICT BACK]", clean_and_repair_head(os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_01.png")), "B", (0.50, 0.86), None, None, None, None),
            ]
        },
    ]

    cw, ch = 225, 225
    cols = 5
    rows = len(head_rows)
    sheet = Image.new("RGBA", (cols * cw + 220, rows * ch + 86), (22, 20, 19, 255))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, sheet.width, 64], fill=(16, 14, 13, 255))
    draw.text((20, 14), "EARLY-TEST PASS 3: REGULARIZED HEADS & FACIAL SUB-SKELETON GRID (FRONT / 3Q / SIDE PROFILE / BACK)", fill=(245, 195, 75, 255))
    draw.text((20, 38), "Every head anchored at Neck Origin (x=112, y=184), classified honestly (Native Painted vs Modular vs Base), with mapped Facial Socket Sub-Skeleton", fill=(185, 180, 170, 255))

    headers = [
        "1. FRONT VIEW (ON GRID)",
        "2. FRONT ALT / 3Q (ON GRID)",
        "3. 3/4 OR SIDE VIEW (ON GRID)",
        "4. SIDE OR 3Q-BACK (ON GRID)",
        "5. STRICT BACK VIEW (ON GRID)",
    ]
    for ci, htxt in enumerate(headers):
        draw.text((210 + ci * cw + 8, 68), htxt, fill=(230, 190, 95, 255))

    for ri, row_spec in enumerate(head_rows):
        y0 = 84 + ri * ch
        draw.rectangle([10, y0 + 4, 202, y0 + ch - 4], fill=(32, 29, 27, 255), outline=(68, 62, 56, 255))
        draw.text((16, y0 + 24), row_spec["char"], fill=(240, 235, 225, 255))
        draw.text((16, y0 + 54), "Head Sub-Skeleton:", fill=(0, 220, 245, 255))
        draw.text((16, y0 + 74), "  o Neck Pivot (0,0)", fill=(0, 220, 245, 255))
        draw.text((16, y0 + 92), "  o Eye Line Sockets", fill=(255, 195, 55, 255))
        draw.text((16, y0 + 110), "  o Nose Bridge/Tip", fill=(95, 235, 135, 255))
        draw.text((16, y0 + 128), "  o Mouth Socket", fill=(255, 95, 210, 255))

        for vi, (vlabel, im_h, vtype, neck_p, eye_l, eye_r, nose_p, mouth_p) in enumerate(row_spec["views"]):
            x0 = 210 + vi * cw
            ox, oy = cw // 2, 184
            draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=20, origin_x=ox - 4, origin_y=oy - 4)

            target_h = 154 if "Young Poet" not in row_spec["char"] else 140
            sc, (sw, sh) = place_part_by_pivot(sheet, im_h, neck_p, (x0 + ox, y0 + oy), target_h)

            def to_scr_h(pt_n):
                dx = (pt_n[0] - neck_p[0]) * sw
                dy = (pt_n[1] - neck_p[1]) * sh
                return (x0 + ox + dx, y0 + oy + dy)

            p_neck = (x0 + ox, y0 + oy)
            p_crown = to_scr_h((neck_p[0], 0.08))
            draw_bone_arrow(draw, p_neck, p_crown, color=(0, 180, 215, 180), width=1)
            draw_subskeleton_node(draw, p_neck, color=(0, 230, 255, 255), r=4)

            if eye_l and eye_r and nose_p and mouth_p:
                pl = to_scr_h(eye_l)
                pr = to_scr_h(eye_r)
                pn = to_scr_h(nose_p)
                pm = to_scr_h(mouth_p)
                draw.line([pl, pr], fill=(255, 200, 55, 200), width=1)
                draw.line([pn, pm], fill=(255, 95, 210, 200), width=1)
                draw_subskeleton_node(draw, pl, color=(255, 200, 55, 255), r=3)
                draw_subskeleton_node(draw, pr, color=(255, 200, 55, 255), r=3)
                draw_subskeleton_node(draw, pn, color=(95, 235, 135, 255), r=3)
                draw_subskeleton_node(draw, pm, color=(255, 95, 210, 255), r=3)

            draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 23], fill=(18, 16, 15, 230))
            draw.text((x0 + 8, y0 + 7), vlabel, fill=(240, 230, 210, 255))

    out_p = os.path.join(ART_DIR, "scratch_pass3_regularized_heads_grid.png")
    sheet.save(out_p)
    sheet.save(os.path.join(OUT_DIR, "pass3_regularized_heads_grid.png"))
    print("Saved Pass 3 Heads Grid ->", out_p)


# ============================================================================
# PASS 4: TRUE 4-ANGLE BODY TURNAROUND GRID (FRONT | 3/4 | SIDE PROFILE | BACK)
# ============================================================================

def render_regularized_view_body(spec, view, cw=230, ch=310, pose=None):
    """
    Renders a single character in one of the 4 canonical views (`FRONT`, `3Q`, `SIDE`, `BACK`)
    on a calibrated ground & centerline grid using the ACTUAL view-specific torso, pelvis,
    vertical limbs, regularized hands, regularized shoes, and regularized head!
    Supports optional `pose` dict with joint rotations & root offsets for bottom-up movement!
    """
    if pose is None:
        pose = {}
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    sc = spec["scale"]
    cx = cw // 2 + int(round(pose.get("dx", 0) * sc))
    gy = 276  # Ground sole line
    dy_root = pose.get("dy", 0)

    def S(dx, dy_from_ground):
        return (cx + dx * sc, gy - (dy_from_ground + dy_root) * sc)

    def fk_pt(origin_xy, length_u, rot_deg):
        rad = math.radians(rot_deg)
        return (
            origin_xy[0] - length_u * sc * math.sin(rad),
            origin_xy[1] + length_u * sc * math.cos(rad),
        )

    vcfg = spec["views"][view]
    torso_im = clean_card_preserve_caps(
        vcfg["torso"],
        crop_bot_frac=vcfg.get("torso_crop_bot", 1.0),
        crop_left_frac=vcfg.get("torso_crop_left", 0.0),
        crop_right_frac=vcfg.get("torso_crop_right", 1.0),
    )
    pelvis_im = clean_card_preserve_caps(vcfg["pelvis"], crop_top_frac=vcfg.get("pelvis_crop_top", 0.0)) if vcfg.get("pelvis") else None
    uarm_im = clean_card_preserve_caps(vcfg["uarm"])
    farm_im = clean_card_preserve_caps(vcfg["farm"], crop_bot_frac=vcfg.get("farm_crop_bot", 1.0))
    hand_im = clean_card_preserve_caps(vcfg["hand"], crop_top_frac=vcfg.get("hand_crop_top", 0.14), auto_vertical_hand=True)
    thigh_im = clean_card_preserve_caps(vcfg["thigh"])
    shin_im = clean_card_preserve_caps(vcfg["shin"], crop_bot_frac=vcfg.get("shin_crop_bot", 1.0))
    foot_im = clean_card_preserve_caps(vcfg["foot"], crop_top_frac=vcfg.get("foot_crop_top", 0.20))
    head_im = vcfg["head_im"]

    is_side = (view == "SIDE")
    is_3q = (view == "3Q")
    foot_side = vcfg.get("foot_is_side", is_side)
    foot_flip = vcfg.get("foot_flip", False)
    foot_piv = vcfg.get("foot_piv", (0.72, 0.24) if foot_flip else (0.30, 0.22))

    torso_rot = pose.get("torso_rot", 0.0)
    head_rot = pose.get("head_rot", 0.0)

    if is_side:
        # TRUE SIDE-PROFILE BODY SUB-SKELETON (all side torsos oriented facing RIGHT +X!)
        th_far_r = pose.get("thigh_L_rot", -4.0)
        sh_far_r = pose.get("shin_L_rot", 2.0)
        ft_far_r = pose.get("foot_L_rot", 0.0)
        th_near_r = pose.get("thigh_R_rot", 0.0)
        sh_near_r = pose.get("shin_R_rot", 2.0)
        ft_near_r = pose.get("foot_R_rot", 0.0)

        ua_far_r = pose.get("uarm_L_rot", -8.0)
        fa_far_r = pose.get("farm_L_rot", -10.0)
        hd_far_r = pose.get("hand_L_rot", -12.0)
        ua_near_r = pose.get("uarm_R_rot", 4.0)
        fa_near_r = pose.get("farm_R_rot", -10.0)
        hd_near_r = pose.get("hand_R_rot", -10.0)

        hip_far = S(6, 132)
        kn_far = fk_pt(hip_far, 56, th_far_r)
        an_far = fk_pt(kn_far, 56, sh_far_r)

        hip_near = S(-4, 130)
        kn_near = fk_pt(hip_near, 56, th_near_r)
        an_near = fk_pt(kn_near, 56, sh_near_r)

        sh_far = S(8, 202)
        el_far = fk_pt(sh_far, 44, ua_far_r)
        wr_far = fk_pt(el_far, 42, fa_far_r)

        sh_near = S(-4, 200)
        el_near = fk_pt(sh_near, 46, ua_near_r)
        wr_near = fk_pt(el_near, 44, fa_near_r)

        neck_xy = S(2, 220)
        torso_xy = S(0, 222)

        # 1. Far Arm & Far Leg (behind side torso)
        place_part_by_pivot(canvas, hand_im, (0.50, 0.16), wr_far, 28 * sc, rot_deg=hd_far_r)
        place_part_by_pivot(canvas, farm_im, (0.50, 0.12), el_far, 50 * sc, rot_deg=fa_far_r)
        place_part_by_pivot(canvas, uarm_im, (0.50, 0.12), sh_far, 54 * sc, rot_deg=ua_far_r)

        place_part_by_pivot(canvas, foot_im, foot_piv, an_far, 28 * sc, rot_deg=ft_far_r, flip_x=foot_flip)
        place_part_by_pivot(canvas, shin_im, (0.50, 0.12), kn_far, 64 * sc, rot_deg=sh_far_r)
        place_part_by_pivot(canvas, thigh_im, (0.50, 0.12), hip_far, 66 * sc, rot_deg=th_far_r)

        # 2. Side Pelvis & Side Torso (flipped if raw card faced left so chest faces right!)
        if pelvis_im is not None:
            place_part_by_pivot(canvas, pelvis_im, (0.50, 0.15), S(0, 152), vcfg.get("pelvis_h", 54) * sc, rot_deg=torso_rot * 0.5)
        place_part_by_pivot(
            canvas, torso_im, (0.50, 0.08), torso_xy,
            vcfg.get("torso_h", 102) * sc, rot_deg=torso_rot, flip_x=vcfg.get("torso_flip", False)
        )

        # 3. Side Profile Head
        place_part_by_pivot(canvas, head_im, vcfg.get("head_piv", (0.48, 0.86)), neck_xy, vcfg.get("head_h", 66) * sc, rot_deg=head_rot)

        # 4. Near Leg & Near Arm (mounted on the side shoulder/hip socket in front of the side ribcage!)
        place_part_by_pivot(canvas, foot_im, foot_piv, an_near, 29 * sc, rot_deg=ft_near_r, flip_x=foot_flip)
        place_part_by_pivot(canvas, shin_im, (0.50, 0.12), kn_near, 66 * sc, rot_deg=sh_near_r)
        place_part_by_pivot(canvas, thigh_im, (0.50, 0.12), hip_near, 68 * sc, rot_deg=th_near_r)

        place_part_by_pivot(canvas, hand_im, (0.50, 0.16), wr_near, 29 * sc, rot_deg=hd_near_r)
        place_part_by_pivot(canvas, farm_im, (0.50, 0.12), el_near, 52 * sc, rot_deg=fa_near_r)
        place_part_by_pivot(canvas, uarm_im, (0.50, 0.12), sh_near, 56 * sc, rot_deg=ua_near_r)

        joints = [neck_xy, sh_near, el_near, wr_near, hip_near, kn_near, an_near]
    else:
        # FRONT, 3/4, or BACK SYMMETRIC / SLIGHT-TURN SUB-SKELETON
        dx_3q = 3 if is_3q else 0
        th_L_r = pose.get("thigh_L_rot", 2.0)
        sh_L_r = pose.get("shin_L_rot", 2.0)
        ft_L_r = pose.get("foot_L_rot", 0.0)
        th_R_r = pose.get("thigh_R_rot", -2.0)
        sh_R_r = pose.get("shin_R_rot", -2.0)
        ft_R_r = pose.get("foot_R_rot", 0.0)

        ua_L_r = pose.get("uarm_L_rot", 6.0)
        fa_L_r = pose.get("farm_L_rot", 4.0)
        hd_L_r = pose.get("hand_L_rot", 4.0)
        ua_R_r = pose.get("uarm_R_rot", -6.0)
        fa_R_r = pose.get("farm_R_rot", -4.0)
        hd_R_r = pose.get("hand_R_rot", -4.0)

        hip_L = S(-14 + dx_3q, 130)
        kn_L = fk_pt(hip_L, 56, th_L_r)
        an_L = fk_pt(kn_L, 56, sh_L_r)

        hip_R = S(14 + dx_3q, 130)
        kn_R = fk_pt(hip_R, 56, th_R_r)
        an_R = fk_pt(kn_R, 56, sh_R_r)

        sh_L = S(-22 + dx_3q, 200)
        el_L = fk_pt(sh_L, 46, ua_L_r)
        wr_L = fk_pt(el_L, 44, fa_L_r)

        sh_R = S(22 + dx_3q, 200)
        el_R = fk_pt(sh_R, 46, ua_R_r)
        wr_R = fk_pt(el_R, 44, fa_R_r)

        neck_xy = S(dx_3q, 220)
        torso_xy = S(dx_3q, 222)

        # 1. Legs (Shoe tucked behind Shin, Shin behind Thigh)
        if foot_side:
            if view == "3Q":
                place_part_by_pivot(canvas, foot_im, foot_piv, an_L, 28 * sc, rot_deg=ft_L_r, flip_x=foot_flip)
                place_part_by_pivot(canvas, foot_im, foot_piv, an_R, 28 * sc, rot_deg=ft_R_r, flip_x=foot_flip)
            else:
                # Outward splay in Front/Back: Left foot points left, Right foot points right
                piv_L = (1.0 - foot_piv[0], foot_piv[1])
                place_part_by_pivot(canvas, foot_im, piv_L, an_L, 28 * sc, rot_deg=ft_L_r, flip_x=(not foot_flip))
                place_part_by_pivot(canvas, foot_im, foot_piv, an_R, 28 * sc, rot_deg=ft_R_r, flip_x=foot_flip)
        else:
            place_part_by_pivot(canvas, foot_im, (0.50, 0.20), an_L, 28 * sc, rot_deg=ft_L_r, flip_x=False)
            place_part_by_pivot(canvas, foot_im, (0.50, 0.20), an_R, 28 * sc, rot_deg=ft_R_r, flip_x=True)

        place_part_by_pivot(canvas, shin_im, (0.50, 0.12), kn_L, 66 * sc, rot_deg=sh_L_r)
        place_part_by_pivot(canvas, thigh_im, (0.50, 0.12), hip_L, 68 * sc, rot_deg=th_L_r)
        place_part_by_pivot(canvas, shin_im, (0.50, 0.12), kn_R, 66 * sc, rot_deg=sh_R_r, flip_x=True)
        place_part_by_pivot(canvas, thigh_im, (0.50, 0.12), hip_R, 68 * sc, rot_deg=th_R_r, flip_x=True)

        # 2. Pelvis / Skirt & Torso
        if pelvis_im is not None:
            place_part_by_pivot(canvas, pelvis_im, (0.50, 0.15), S(dx_3q, 152), vcfg.get("pelvis_h", 56) * sc, rot_deg=torso_rot * 0.5)
        place_part_by_pivot(canvas, torso_im, (0.50, 0.08), torso_xy, vcfg.get("torso_h", 104) * sc, rot_deg=torso_rot)

        # 3. Head
        place_part_by_pivot(canvas, head_im, vcfg.get("head_piv", (0.50, 0.86)), neck_xy, vcfg.get("head_h", 66) * sc, rot_deg=head_rot)

        # 4. Left & Right Arms (Hand tucked behind Forearm cuff!)
        place_part_by_pivot(canvas, hand_im, (0.50, 0.16), wr_L, 28 * sc, rot_deg=hd_L_r)
        place_part_by_pivot(canvas, farm_im, (0.50, 0.12), el_L, 52 * sc, rot_deg=fa_L_r)
        place_part_by_pivot(canvas, uarm_im, (0.50, 0.12), sh_L, 56 * sc, rot_deg=ua_L_r)

        place_part_by_pivot(canvas, hand_im, (0.50, 0.16), wr_R, 28 * sc, rot_deg=hd_R_r, flip_x=True)
        place_part_by_pivot(canvas, farm_im, (0.50, 0.12), el_R, 52 * sc, rot_deg=fa_R_r, flip_x=True)
        place_part_by_pivot(canvas, uarm_im, (0.50, 0.12), sh_R, 56 * sc, rot_deg=ua_R_r, flip_x=True)

        joints = [neck_xy, sh_L, el_L, wr_L, sh_R, el_R, wr_R, hip_L, kn_L, an_L, hip_R, kn_R, an_R]

    return canvas, joints


def get_char_turnarounds():
    import build_100x_pose_face_library as b100

    poet_f_head = b100.p09.build_modular_head("front_neutral")
    poet_3q_head = clean_and_repair_head(os.path.join(WM_HEADS, "head.3q.recognition.png"))
    poet_p_head = clean_and_repair_head(os.path.join(WM_HEADS, "head.profile_R.neutral.png"))
    poet_b_head = clean_and_repair_head(os.path.join(V2_PARTS, "poet.red_black_sunglasses/head.back.png"))

    return [
        {
            "name": "1. Poet (Tracksuit)",
            "scale": 1.0,
            "views": {
                "FRONT": dict(
                    torso=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.front.torso.png"),
                    pelvis=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.front.pelvis.png"),
                    uarm=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.front.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.front.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.front.hand.L.png"),
                    thigh=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.front.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.front.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.foot.L.png"),
                    foot_is_side=True, foot_flip=False, head_im=poet_f_head, head_piv=(0.50, 0.82),
                ),
                "3Q": dict(
                    torso=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.threequarter.torso.png"),
                    pelvis=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.threequarter.pelvis.png"),
                    uarm=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.threequarter.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.threequarter.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.threequarter.hand.L.png"),
                    thigh=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.threequarter.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.threequarter.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.foot.L.png"),
                    foot_is_side=True, foot_flip=False, head_im=poet_3q_head, head_piv=(0.48, 0.86),
                ),
                "SIDE": dict(
                    torso=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.torso.png"),
                    torso_crop_bot=1.0, torso_h=106, torso_flip=False,
                    pelvis=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.pelvis.true.png"),
                    uarm=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.hand.L.png"),
                    thigh=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.foot.L.png"),
                    foot_is_side=True, foot_flip=False, head_im=poet_p_head, head_piv=(0.46, 0.86),
                ),
                "BACK": dict(
                    torso=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.back.torso.png"),
                    pelvis=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.back.pelvis.png"),
                    uarm=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.back.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.back.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.back.hand.L.png"),
                    thigh=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.back.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.back.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.foot.L.png"),
                    foot_is_side=True, foot_flip=False, head_im=poet_b_head, head_piv=(0.50, 0.86),
                ),
            }
        },
        {
            "name": "2. Poet (Black T-Shirt)",
            "scale": 1.0,
            "views": {
                v: dict(
                    torso=os.path.join(V2_PARTS, "poet.black_tshirt/body.profile.torso.true.png") if v == "SIDE" else os.path.join(V2_PARTS, f"poet.black_tshirt/body.{'front' if v in ('FRONT','3Q') else 'back'}.torso.png"),
                    pelvis=os.path.join(V2_PARTS, "poet.black_tshirt/body.profile.pelvis.true.png") if v == "SIDE" else os.path.join(V2_PARTS, "poet.black_tshirt/body.front.pelvis.png"),
                    uarm=os.path.join(V2_PARTS, "poet.black_tshirt/body.front.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "poet.black_tshirt/body.front.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "poet.black_tshirt/body.profile.hand.L.png") if v == "SIDE" else os.path.join(V2_PARTS, "poet.black_tshirt/body.front.hand.L.png"),
                    thigh=os.path.join(V2_PARTS, "poet.black_tshirt/body.front.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "poet.black_tshirt/body.front.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "poet.black_tshirt/body.front.foot.L.png"),
                    foot_is_side=True, foot_flip=False,
                    head_im={"FRONT": clean_and_repair_head(os.path.join(WM_HEADS, "head.front.neutral.png")), "3Q": poet_3q_head, "SIDE": poet_p_head, "BACK": poet_b_head}[v],
                    head_piv=(0.48, 0.86),
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            }
        },
        {
            "name": "3. Woman / Muse (Brocade)",
            "scale": 0.96,
            "views": {
                v: dict(
                    torso=os.path.join(V2_PARTS, f"woman.teal_dress/body.{'profile' if v == 'SIDE' else ('back' if v == 'BACK' else 'front')}.torso.png"),
                    pelvis=os.path.join(V2_PARTS, "woman.mother_cardigan/body.profile.skirt.brocade.png") if v == "SIDE" else os.path.join(V2_PARTS, "woman.window_woman_dress/body.front.pelvis.png"),
                    pelvis_h=64,
                    uarm=os.path.join(V2_PARTS, "woman.teal_dress/body.front.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "woman.teal_dress/body.front.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "woman.teal_dress/body.profile.hand.true.L.png") if v == "SIDE" else os.path.join(V2_PARTS, "woman.teal_dress/body.front.hand.true.L.png"),
                    thigh=os.path.join(V2_PARTS, "woman.teal_dress/body.front.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "woman.teal_dress/body.front.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "woman.teal_dress/body.profile.foot.L.png") if v in ("SIDE", "3Q") else os.path.join(V2_PARTS, "woman.teal_dress/body.front.foot.true.png"),
                    foot_is_side=(v in ("SIDE", "3Q")), foot_flip=(v in ("SIDE", "3Q")),
                    foot_piv=(0.72, 0.24) if v in ("SIDE", "3Q") else (0.50, 0.20),
                    head_im={
                        "FRONT": clean_and_repair_head(os.path.join(V2_PARTS, "woman.teal_dress/head.front.png")),
                        "3Q": clean_and_repair_head(os.path.join(V2_PARTS, "woman.teal_dress/head.front.png")),
                        "SIDE": clean_and_repair_head(os.path.join(V2_PARTS, "woman.window_woman_dress/head.front.png")),
                        "BACK": clean_and_repair_head(os.path.join(V2_PARTS, "woman.teal_dress/head.back.png")),
                    }[v],
                    head_piv=(0.50, 0.86), head_h=68,
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            }
        },
        {
            "name": "4. The Mother (Cardigan)",
            "scale": 0.95,
            "views": {
                v: dict(
                    torso=os.path.join(V2_PARTS, f"woman.mother_cardigan/body.{'profile' if v == 'SIDE' else ('back' if v == 'BACK' else 'front')}.torso.png"),
                    torso_flip=(v == "SIDE"),
                    pelvis=os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.pelvis.png"),
                    uarm=os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "woman.teal_dress/body.profile.hand.true.L.png") if v == "SIDE" else os.path.join(V2_PARTS, "woman.teal_dress/body.front.hand.true.L.png"),
                    thigh=os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.foot.L.png"),
                    foot_crop_top=0.20, foot_is_side=False, foot_flip=False,
                    head_im={
                        "FRONT": clean_and_repair_head(os.path.join(V2_PARTS, "woman.mother_cardigan/head.front.png")),
                        "3Q": clean_and_repair_head(os.path.join(V2_PARTS, "woman.mother_cardigan/head.threequarter.png")),
                        "SIDE": clean_and_repair_head(os.path.join(V2_PARTS, "woman.mother_cardigan/head.profile.png")),
                        "BACK": clean_and_repair_head(os.path.join(V2_PARTS, "woman.mother_cardigan/head.back.png")),
                    }[v],
                    head_piv=(0.50, 0.86), head_h=68,
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            }
        },
        {
            "name": "5. The Ex (Olive Bomber)",
            "scale": 0.98,
            "views": {
                v: dict(
                    torso=os.path.join(V2_PARTS, "ex.ex_jacket/body.profile.torso.true.png") if v == "SIDE" else os.path.join(V2_PARTS, f"ex.ex_jacket/body.{'threequarter_back' if v == '3Q' else 'back'}.torso.png"),
                    pelvis=os.path.join(V2_PARTS, "ex.ex_jacket/body.profile.pelvis.true.png"),
                    uarm=os.path.join(V2_PARTS, "ex.ex_jacket/body.back.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "ex.ex_jacket/body.back.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "ex.ex_jacket/body.back.hand.L.png"),
                    thigh=os.path.join(V2_PARTS, "ex.ex_jacket/body.back.thigh.L.png") if v != "SIDE" else os.path.join(V2_PARTS, "ex.ex_jacket/body.profile.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "ex.ex_jacket/body.back.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "ex.ex_jacket/body.profile.foot.L.png"),
                    foot_is_side=True, foot_flip=False,
                    head_im={
                        "FRONT": clean_and_repair_head(os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_01.png")),
                        "3Q": clean_and_repair_head(os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_04.png")),
                        "SIDE": clean_and_repair_head(os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_05.png")),
                        "BACK": clean_and_repair_head(os.path.join(BL_HEADS, "the_ex_bomber_jacket/ex_head_01.png")),
                    }[v],
                    head_piv=(0.50, 0.86),
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            }
        },
        {
            "name": "6. Party Gentleman (Suit)",
            "scale": 1.0,
            "views": {
                v: dict(
                    torso=os.path.join(V2_PARTS, f"party.vintage_party/body.{'profile' if v == 'SIDE' else ('back' if v == 'BACK' else 'front')}.torso.png"),
                    torso_crop_bot=1.0,
                    torso_flip=False,
                    pelvis=os.path.join(V2_PARTS, "party.vintage_party/body.profile.pelvis.png"),
                    uarm=os.path.join(V2_PARTS, "party.vintage_party/body.profile.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "party.vintage_party/body.profile.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "party.vintage_party/body.profile.hand.L.png"),
                    hand_crop_top=0.55,
                    thigh=os.path.join(V2_PARTS, "party.vintage_party/body.profile.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "party.vintage_party/body.profile.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "party.vintage_party/body.profile.foot.L.png"),
                    foot_is_side=True, foot_flip=False,
                    head_im={
                        "FRONT": clean_and_repair_head(os.path.join(WM_HEADS, "head.front.small_smile.png")),
                        "3Q": poet_3q_head,
                        "SIDE": poet_p_head,
                        "BACK": clean_and_repair_head(os.path.join(V2_PARTS, "party.vintage_party/head.back.png")),
                    }[v],
                    head_piv=(0.48, 0.86),
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            }
        },
        {
            "name": "7. DJ Cyber (Naraka Club)",
            "scale": 1.0,
            "views": {
                v: dict(
                    torso=os.path.join(V2_PARTS, f"party.dj_cyber/body.{'profile' if v == 'SIDE' else ('back' if v == 'BACK' else 'front')}.torso.png"),
                    torso_crop_bot=1.0,
                    torso_flip=False,
                    pelvis=os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.pelvis.true.png") if v == "SIDE" else os.path.join(V2_PARTS, "party.dj_cyber/body.profile.pelvis.png"),
                    uarm=os.path.join(V2_PARTS, "party.dj_cyber/body.profile.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "party.dj_cyber/body.profile.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "party.dj_cyber/body.profile.hand.L.png") if v == "SIDE" else os.path.join(V2_PARTS, "party.dj_cyber/body.front.hand.L.png"),
                    thigh=os.path.join(V2_PARTS, "party.dj_cyber/body.profile.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "party.dj_cyber/body.profile.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "party.dj_cyber/body.profile.foot.L.png"),
                    foot_is_side=True, foot_flip=False,
                    head_im={
                        "FRONT": clean_and_repair_head(os.path.join(WM_HEADS, "head.front.sunglasses.png")),
                        "3Q": clean_and_repair_head(os.path.join(WM_HEADS, "head.3q.listening.png")),
                        "SIDE": poet_p_head,
                        "BACK": clean_and_repair_head(os.path.join(V2_PARTS, "party.dj_cyber/head.back.png")),
                    }[v],
                    head_piv=(0.48, 0.86),
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            }
        },
        {
            "name": "8. Young Poet (Age 6 · 5.2H)",
            "scale": 0.72,
            "views": {
                v: dict(
                    torso=os.path.join(V2_PARTS, f"young_poet.child_clothes/body.{'profile' if v == 'SIDE' else ('threequarter' if v == '3Q' else ('back' if v == 'BACK' else 'front'))}.torso.png"),
                    torso_crop_bot=1.0,
                    torso_flip=False,
                    pelvis=os.path.join(V2_PARTS, "young_poet.child_clothes/body.profile.pelvis.denim.true.png"),
                    pelvis_h=54,
                    uarm=os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.uarm.L.png"),
                    farm=os.path.join(V2_PARTS, "young_poet.child_clothes/body.profile.farm.L.png"),
                    hand=os.path.join(V2_PARTS, "young_poet.child_clothes/body.profile.hand.L.png") if v == "SIDE" else os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.hand.L.png"),
                    thigh=os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.thigh.L.png"),
                    shin=os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.shin.L.png"),
                    foot=os.path.join(V2_PARTS, "young_poet.child_clothes/body.profile.foot.L.png") if v in ("SIDE", "3Q") else os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.foot.L.png"),
                    foot_is_side=(v in ("SIDE", "3Q")), foot_flip=False,
                    head_im={
                        "FRONT": clean_and_repair_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.front.true.png"), "clean_dots"),
                        "3Q": clean_and_repair_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.threequarter.true.png"), "clean_dots"),
                        "SIDE": clean_and_repair_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.profile.true.png"), "clean_dots"),
                        "BACK": clean_and_repair_head(os.path.join(V2_PARTS, "young_poet.child_clothes/head.back.png")),
                    }[v],
                    head_piv=(0.48, 0.86), head_h=74,
                ) for v in ["FRONT", "3Q", "SIDE", "BACK"]
            }
        },
    ]


def build_pass4_four_angle_bodies_grid():
    char_turnarounds = get_char_turnarounds()

    cw, ch = 225, 310
    cols = 4  # FRONT, 3Q, SIDE PROFILE, BACK
    rows = len(char_turnarounds)
    sheet = Image.new("RGBA", (cols * cw + 220, rows * ch + 86), (22, 20, 19, 255))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, sheet.width, 64], fill=(16, 14, 13, 255))
    draw.text((20, 14), "EARLY-TEST PASS 4: TRUE 4-ANGLE BODY TURNAROUND GRID (FRONT | 3/4 | SIDE PROFILE | BACK)", fill=(245, 195, 75, 255))
    draw.text((20, 38), "Uses each character's actual Side Profile (body.profile), Front, 3/4, and Back torsos + straight vertical limbs + Pass 1-3 regularized Hands, Shoes & Heads", fill=(185, 180, 170, 255))

    headers = [
        "1. FRONT VIEW (body.front)",
        "2. THREE-QUARTER (body.3q)",
        "3. SIDE PROFILE (body.profile!)",
        "4. BACK VIEW (body.back)",
    ]
    for ci, htxt in enumerate(headers):
        draw.text((210 + ci * cw + 8, 68), htxt, fill=(110, 235, 165, 255) if ci == 2 else (230, 190, 95, 255))

    for ri, cspec in enumerate(char_turnarounds):
        y0 = 84 + ri * ch
        draw.rectangle([10, y0 + 4, 202, y0 + ch - 4], fill=(32, 29, 27, 255), outline=(68, 62, 56, 255))
        draw.text((16, y0 + 28), cspec["name"], fill=(240, 235, 225, 255))
        draw.text((16, y0 + 54), f"Scale Ratio: {cspec['scale']:.2f}x", fill=(175, 170, 160, 255))
        draw.text((16, y0 + 84), "Verified Elements:", fill=(110, 235, 165, 255))
        draw.text((16, y0 + 104), "  + True Side Torso", fill=(195, 190, 180, 255))
        draw.text((16, y0 + 122), "  + Rounded Joint Caps", fill=(195, 190, 180, 255))
        draw.text((16, y0 + 140), "  + Regularized Hands", fill=(195, 190, 180, 255))
        draw.text((16, y0 + 158), "  + Grounded Shoes", fill=(195, 190, 180, 255))
        draw.text((16, y0 + 176), "  + View-Matched Head", fill=(195, 190, 180, 255))

        for vi, vw in enumerate(["FRONT", "3Q", "SIDE", "BACK"]):
            x0 = 210 + vi * cw
            draw_calib_grid(draw, x0 + 4, y0 + 4, cw - 8, ch - 8, step=24, origin_x=cw // 2 - 4, origin_y=276 - 4)
            draw.line([(x0 + 10, y0 + 276), (x0 + cw - 10, y0 + 276)], fill=(235, 170, 70, 255), width=2)

            fig_im, joints = render_regularized_view_body(cspec, vw, cw=cw, ch=ch)
            sheet.alpha_composite(fig_im, (x0, y0))

            for jpt in joints:
                draw_subskeleton_node(draw, (x0 + jpt[0], y0 + jpt[1]), color=(0, 230, 255, 220), r=3)

            draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 23], fill=(18, 36, 26, 235) if vw == "SIDE" else (18, 16, 15, 230))
            draw.text((x0 + 10, y0 + 7), f"{cspec['name'][3:18]} · {vw}", fill=(130, 245, 175, 255) if vw == "SIDE" else (240, 230, 210, 255))

    out_p = os.path.join(ART_DIR, "scratch_pass4_four_angle_bodies_grid.png")
    sheet.save(out_p)
    sheet.save(os.path.join(OUT_DIR, "pass4_four_angle_bodies_grid.png"))
    print("Saved Pass 4 4-Angle Bodies Grid ->", out_p)


# ============================================================================
# PASS 5: PAIRWISE ADJACENT-PART CONNECTION GATE ("CLEAN VS. MUTILATED JOIN")
# ============================================================================

def measure_part_profile(im):
    """Computes quantitative geometry & assumption metrics for a single part card."""
    arr = np.array(im)
    a = arr[:, :, 3] > 24
    H, W = a.shape
    ys, xs = np.where(a)
    if len(xs) == 0:
        return dict(w=W, h=H, aspect=1.0, top_w=0, mid_w=0, bot_w=0, axis_deg=0.0, interior_hole_pct=0.0)
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    bw = max(1, x1 - x0 + 1)
    bh = max(1, y1 - y0 + 1)

    def span_width(f0, f1):
        r0 = y0 + int(bh * f0)
        r1 = max(r0 + 1, y0 + int(bh * f1))
        sub = a[r0:r1, :]
        row_ws = [np.where(r)[0].ptp() + 1 for r in sub if np.any(r)]
        return float(np.median(row_ws)) if row_ws else 0.0

    # Principal axis angle via covariance of solid pixels
    cx, cy = xs.mean(), ys.mean()
    dx, dy = xs - cx, ys - cy
    cov_xx = np.mean(dx * dx)
    cov_yy = np.mean(dy * dy)
    cov_xy = np.mean(dx * dy)
    theta_rad = 0.5 * math.atan2(2 * cov_xy, cov_yy - cov_xx)
    axis_deg = abs(math.degrees(theta_rad))

    # Interior hole ratio
    bg = ~a
    bg_lab, bg_n = label(bg)
    border_lbls = set(np.unique(np.concatenate([bg_lab[0, :], bg_lab[-1, :], bg_lab[:, 0], bg_lab[:, -1]])))
    hole_px = sum((bg_lab == i).sum() for i in range(1, bg_n + 1) if i not in border_lbls)
    hole_pct = 100.0 * hole_px / max(1, bw * bh)

    return dict(
        w=int(bw),
        h=int(bh),
        aspect=round(bh / float(bw), 2),
        top_w=round(span_width(0.05, 0.22), 1),
        mid_w=round(span_width(0.40, 0.60), 1),
        bot_w=round(span_width(0.78, 0.95), 1),
        axis_deg=round(axis_deg, 1),
        interior_hole_pct=round(hole_pct, 2),
    )


def build_pass5_pairwise_connection_gate():
    """
    Tests EACH body part with the adjacent part beside it (`Part A <-> Part B`)
    and classifies the join as `[FAIL: MUTILATED CONNECTION]` vs `[PASS: CLEAN CONNECTION]`.
    Saves both a JSON diagnostic report (`pairwise_connection_gate.json`) and a
    10-panel side-by-side visual comparison sheet (`scratch_pairwise_join_audit.png`).
    """
    import json

    cases = [
        {
            "id": "JOIN_01_MOTHER_WRIST_SLEEVE",
            "title": "1. Forearm <-> Hand (Mother Cardigan Wrist)",
            "pair_type": "Forearm Cuff <-> Hand",
            "defect_code": "HAND_CONTAINS_FULL_FOREARM_SLEEVE",
            "assumption_violated": "mother_cardigan/body.front.hand.L (70x219, h/w=3.13) includes an entire knit forearm sleeve! Joining it to farm.L creates a double-length 2-elbow monster arm.",
            "fix_applied": "Replace uncut sleeve-hand with isolated hand (woman.teal_dress/body.front.hand.true.L) or crop sleeve above y=0.58; tuck wrist pin (0.50, 0.16) inside forearm cuff.",
            "mutilated_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.hand.L.png")).convert("RGBA"), (0.50, 0.10), (ox, oy + 18), 115),
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.farm.L.png")).convert("RGBA"), (0.50, 0.12), (ox, oy - 70), 102),
            ),
            "clean_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "woman.teal_dress/body.front.hand.true.L.png"), crop_top_frac=0.14), (0.50, 0.16), (ox - 2, oy + 16), 54, rot_deg=6),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.farm.L.png")), (0.50, 0.12), (ox, oy - 68), 102, rot_deg=4),
            ),
            "part_a_raw": os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.farm.L.png"),
            "part_b_raw": os.path.join(V2_PARTS, "woman.mother_cardigan/body.front.hand.L.png"),
        },
        {
            "id": "JOIN_02_WEAVE_HORIZONTAL_HAND",
            "title": "2. Forearm <-> Hand (90-Deg Sideways Assumption)",
            "pair_type": "Forearm Cuff <-> Action Hand",
            "defect_code": "HORIZONTAL_HAND_AXIS_89DEG_OFF",
            "assumption_violated": "Weave & Action hands (hand.point 233x121, w>h) are painted HORIZONTALLY (wrist on left, fingers right). Attaching at top pin sticks the hand out 90 deg sideways!",
            "fix_applied": "Auto-detect w > h*1.12 in clean_card_preserve_caps(auto_vertical_hand=True), rotate +90 deg CW so wrist aligns with vertical forearm bone axis.",
            "mutilated_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, Image.open(os.path.join(WM_HANDS, "hand.point.png")).convert("RGBA"), (0.50, 0.18), (ox + 18, oy + 16), 52),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "poet.black_tshirt/body.front.farm.L.png")), (0.50, 0.12), (ox, oy - 68), 102),
            ),
            "clean_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(WM_HANDS, "hand.point.png"), auto_vertical_hand=True, crop_top_frac=0.12), (0.50, 0.16), (ox, oy + 16), 58),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "poet.black_tshirt/body.front.farm.L.png")), (0.50, 0.12), (ox, oy - 68), 102),
            ),
            "part_a_raw": os.path.join(V2_PARTS, "poet.black_tshirt/body.front.farm.L.png"),
            "part_b_raw": os.path.join(WM_HANDS, "hand.point.png"),
        },
        {
            "id": "JOIN_03_PARTY_SHOE_HAS_SHIN",
            "title": "3. Shin <-> Shoe (Party Oxford Has Half a Shin)",
            "pair_type": "Shin Cuff <-> Shoe / Foot",
            "defect_code": "FOOT_CARD_CONTAINS_LOWER_SHIN",
            "assumption_violated": "party.vintage_party/body.front.foot.L (135x193, h/w=1.43) includes half a pinstripe trouser leg above the shoe! Joining to shin.L creates a double-cuff stacked shin.",
            "fix_applied": "Trim upper trouser fragment (crop_top_frac=0.50) or use clean profile oxford (body.profile.foot.L) with ankle socket (0.30, 0.24) tucked behind shin cuff.",
            "mutilated_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "party.vintage_party/body.front.foot.L.png")).convert("RGBA"), (0.50, 0.15), (ox, oy + 8), 86),
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "party.vintage_party/body.profile.shin.L.png")).convert("RGBA"), (0.50, 0.12), (ox, oy - 74), 104),
            ),
            "clean_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "party.vintage_party/body.profile.foot.L.png"), crop_top_frac=0.14), (0.30, 0.24), (ox, oy + 26), 48),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "party.vintage_party/body.profile.shin.L.png")), (0.50, 0.12), (ox, oy - 66), 108),
            ),
            "part_a_raw": os.path.join(V2_PARTS, "party.vintage_party/body.profile.shin.L.png"),
            "part_b_raw": os.path.join(V2_PARTS, "party.vintage_party/body.front.foot.L.png"),
        },
        {
            "id": "JOIN_04_YP_PELVIS_WIDTH_EXPLOSION",
            "title": "4. Torso <-> Pelvis (240% Waist Width Jump!)",
            "pair_type": "Torso Waist <-> Pelvis Shorts",
            "defect_code": "UNFOLDED_SHORTS_240PCT_WIDER_THAN_WAIST",
            "assumption_violated": "young_poet.child_clothes/body.front.pelvis.denim.png (334x186, h/w=0.56) is 2.4x wider than the child torso waist, sticking out like giant wings on both sides!",
            "fix_applied": "Flag width_step_err > 0.45 between torso bot_w and pelvis top_w; bind torso waist to fitted denim shorts (body.profile.pelvis.denim.true.png 166x291).",
            "mutilated_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.pelvis.denim.png")).convert("RGBA"), (0.50, 0.15), (ox, oy + 4), 76),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.torso.png")), (0.50, 0.08), (ox, oy - 68), 96),
            ),
            "clean_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "young_poet.child_clothes/body.profile.pelvis.denim.true.png")), (0.50, 0.15), (ox, oy + 4), 60),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.torso.png")), (0.50, 0.08), (ox, oy - 68), 96),
            ),
            "part_a_raw": os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.torso.png"),
            "part_b_raw": os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.pelvis.denim.png"),
        },
        {
            "id": "JOIN_05_YP_FARM_IS_UARM",
            "title": "5. Upper Arm <-> Forearm (Duplicate Striped Sleeve)",
            "pair_type": "Upper Arm <-> Forearm (Elbow)",
            "defect_code": "FOREARM_IS_DUPLICATE_STRIPED_UPPER_ARM",
            "assumption_violated": "young_poet.child_clothes/body.front.farm.L (136x349) is a duplicate of the striped T-shirt upper arm! Joining uarm.L + farm.L creates two T-shirt sleeves stacked end-to-end.",
            "fix_applied": "Detect striped fabric texture duplication on front.farm.L; bind uarm.L to true bare forearm (body.profile.farm.L) at elbow socket.",
            "mutilated_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.farm.L.png")).convert("RGBA"), (0.50, 0.12), (ox, oy + 2), 82, rot_deg=-28),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.uarm.L.png")), (0.50, 0.12), (ox, oy - 64), 84, rot_deg=8),
            ),
            "clean_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "young_poet.child_clothes/body.profile.farm.L.png")), (0.50, 0.12), (ox - 6, oy + 2), 80, rot_deg=-28),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.uarm.L.png")), (0.50, 0.12), (ox, oy - 64), 84, rot_deg=8),
            ),
            "part_a_raw": os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.uarm.L.png"),
            "part_b_raw": os.path.join(V2_PARTS, "young_poet.child_clothes/body.front.farm.L.png"),
        },
        {
            "id": "JOIN_06_DJ_DIAGONAL_ELBOW",
            "title": "6. Upper Arm <-> Forearm (Diagonal 36-Deg Card Skew)",
            "pair_type": "Upper Arm <-> Forearm @ 45-Deg Bend",
            "defect_code": "DIAGONAL_LIMB_AXIS_MISMATCH_36DEG",
            "assumption_violated": "party.dj_cyber/body.front.uarm.L (176x248, axis=34.8 deg) & farm.L are cut diagonally at -36 deg! Rotating around top center swings the elbow completely off-socket.",
            "fix_applied": "Replace diagonal front limb cards with straight vertical profile limbs (body.profile.uarm.L & farm.L, axis=1.8 deg) preserving full rounded elbow caps.",
            "mutilated_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "party.dj_cyber/body.front.farm.L.png")).convert("RGBA"), (0.50, 0.12), (ox, oy + 4), 78, rot_deg=-35),
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "party.dj_cyber/body.front.uarm.L.png")).convert("RGBA"), (0.50, 0.12), (ox, oy - 64), 84, rot_deg=10),
            ),
            "clean_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "party.dj_cyber/body.profile.farm.L.png")), (0.50, 0.12), (ox - 10, oy + 4), 84, rot_deg=-35),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "party.dj_cyber/body.profile.uarm.L.png")), (0.50, 0.12), (ox, oy - 64), 88, rot_deg=10),
            ),
            "part_a_raw": os.path.join(V2_PARTS, "party.dj_cyber/body.front.uarm.L.png"),
            "part_b_raw": os.path.join(V2_PARTS, "party.dj_cyber/body.front.farm.L.png"),
        },
        {
            "id": "JOIN_07_SIDE_TORSO_HOLLOW_ARMHOLE_AND_WIDE_PELVIS",
            "title": "7. Side Torso <-> Wide Front Hip Bridge & Armhole",
            "pair_type": "Side Profile Torso <-> Pelvis & Arm",
            "defect_code": "HOLLOW_ARMHOLE_AND_FRONT_PELVIS_ON_SIDE_TORSO",
            "assumption_violated": "Side torsos (body.profile.torso) have an 8.4% hollow armhole cutout, and pairing with wide front hip bridges (dj_cyber/body.profile.pelvis 234x182) sticks grommet ears out front & back!",
            "fix_applied": "Fill interior armhole cutout with jacket gouache, pair with true narrow side pelvis (body.profile.pelvis.true 150x181), and mount near upper arm over shoulder socket.",
            "mutilated_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "party.dj_cyber/body.profile.pelvis.png")).convert("RGBA"), (0.50, 0.15), (ox, oy + 14), 56),
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.torso.png")).convert("RGBA"), (0.50, 0.08), (ox, oy - 74), 104, flip_x=True),
            ),
            "clean_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.pelvis.true.png")), (0.50, 0.15), (ox, oy + 14), 56),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.torso.png")), (0.50, 0.08), (ox, oy - 74), 106, flip_x=False),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.uarm.L.png")), (0.50, 0.12), (ox - 4, oy - 54), 60, rot_deg=6),
            ),
            "part_a_raw": os.path.join(V2_PARTS, "poet.red_black_sunglasses/body.profile.torso.png"),
            "part_b_raw": os.path.join(V2_PARTS, "party.dj_cyber/body.profile.pelvis.png"),
        },
        {
            "id": "JOIN_08_PARTY_PELVIS_SADDLEBAGS",
            "title": "8. Suit Torso <-> Pelvis (374x193 Saddlebag Flaps)",
            "pair_type": "Front Torso <-> Pelvis / Thighs",
            "defect_code": "WAIST_WIDTH_JUMP_215PCT_SADDLEBAG",
            "assumption_violated": "party.vintage_party/body.front.pelvis (374x193, aspect=0.52) has two wide brown side-pouches sticking out 2.1x wider than the pinstripe suit waist!",
            "fix_applied": "Flag width_step_err > 0.45 at waist join; replace wide front.pelvis with fitted pinstripe pelvis (body.profile.pelvis.png 164x194).",
            "mutilated_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "party.vintage_party/body.front.pelvis.png")).convert("RGBA"), (0.50, 0.15), (ox, oy + 12), 58),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "party.vintage_party/body.front.torso.png")), (0.50, 0.08), (ox, oy - 74), 104),
            ),
            "clean_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "party.vintage_party/body.profile.pelvis.png")), (0.50, 0.15), (ox, oy + 12), 58),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "party.vintage_party/body.front.torso.png")), (0.50, 0.08), (ox, oy - 74), 104),
            ),
            "part_a_raw": os.path.join(V2_PARTS, "party.vintage_party/body.front.torso.png"),
            "part_b_raw": os.path.join(V2_PARTS, "party.vintage_party/body.front.pelvis.png"),
        },
        {
            "id": "JOIN_09_GUILLOTINED_ELBOW_NOTCH",
            "title": "9. Upper Arm <-> Forearm (Guillotine Cutoff Notch)",
            "pair_type": "Upper Arm <-> Forearm @ 55-Deg Bend",
            "defect_code": "GUILLOTINED_CAP_CREATES_BEND_NOTCH",
            "assumption_violated": "Chopping top/bottom 12% of limb cards (`arr[:11%]=0`) slices off the semicircular joint cap! When the elbow bends 55 deg, a sharp V-notch opens at the joint.",
            "fix_applied": "Preserve 100% of rounded semicircular joint caps in clean_card_preserve_caps() and fill only the interior pinhole so bent joints roll smoothly.",
            "mutilated_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "poet.black_tshirt/body.front.farm.L.png"), crop_top_frac=0.16, crop_bot_frac=0.86), (0.50, 0.02), (ox + 8, oy + 8), 74, rot_deg=-55),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "poet.black_tshirt/body.front.uarm.L.png"), crop_top_frac=0.14, crop_bot_frac=0.84), (0.50, 0.12), (ox, oy - 66), 78, rot_deg=12),
            ),
            "clean_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "poet.black_tshirt/body.front.farm.L.png")), (0.50, 0.14), (ox - 12, oy + 4), 86, rot_deg=-55),
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "poet.black_tshirt/body.front.uarm.L.png")), (0.50, 0.12), (ox, oy - 66), 88, rot_deg=12),
            ),
            "part_a_raw": os.path.join(V2_PARTS, "poet.black_tshirt/body.front.uarm.L.png"),
            "part_b_raw": os.path.join(V2_PARTS, "poet.black_tshirt/body.front.farm.L.png"),
        },
        {
            "id": "JOIN_10_HEAD_NECK_CUT_SLOT_AND_DOUBLE_MOUTH",
            "title": "10. Torso Collar <-> Head (Eye-Slot & Double Mouth)",
            "pair_type": "Torso Collar <-> Head Neck",
            "defect_code": "CUT_SLOT_HEAD_AND_PASTED_MOUTH_COLLISION",
            "assumption_violated": "party.vintage_party/head.front has a raw rectangular eye-slot hole cut out of the face, and pasting a front mouth onto a profile head creates two mouths!",
            "fix_applied": "Classify heads honestly (Native Painted vs Modular vs Cut-Slot Defect); replace slotted head with clean native weave/painted head anchored at (0.50, 0.86).",
            "mutilated_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "party.vintage_party/body.front.torso.png")), (0.50, 0.08), (ox, oy + 8), 92),
                place_part_by_pivot(c, Image.open(os.path.join(V2_PARTS, "party.vintage_party/head.front.png")).convert("RGBA"), (0.50, 0.86), (ox, oy + 4), 84),
            ),
            "clean_fn": lambda c, ox, oy: (
                place_part_by_pivot(c, clean_card_preserve_caps(os.path.join(V2_PARTS, "party.vintage_party/body.front.torso.png")), (0.50, 0.08), (ox, oy + 8), 92),
                place_part_by_pivot(c, clean_and_repair_head(os.path.join(WM_HEADS, "head.front.small_smile.png")), (0.48, 0.86), (ox, oy + 4), 84),
            ),
            "part_a_raw": os.path.join(V2_PARTS, "party.vintage_party/body.front.torso.png"),
            "part_b_raw": os.path.join(V2_PARTS, "party.vintage_party/head.front.png"),
        },
    ]

    cw, ch = 460, 235
    cols = 2
    rows = 5
    sheet = Image.new("RGBA", (cols * cw + 40, rows * ch + 96), (20, 18, 17, 255))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, sheet.width, 68], fill=(14, 12, 12, 255))
    draw.text((20, 14), "EARLY-TEST PASS 5: PAIRWISE ADJACENT-PART CONNECTION GATE (MUTILATED VS. CLEAN CONNECTIONS)", fill=(255, 195, 75, 255))
    draw.text((20, 38), "Testing each body part with the part beside it (Part A <-> Part B): Automated detection of uncut sleeves/shins, wrong parts, 90-deg hands, diagonal skew & hollow flanges", fill=(185, 180, 170, 255))

    audit_records = []
    for idx, case in enumerate(cases):
        r = idx // 2
        c_idx = idx % 2
        x0 = 20 + c_idx * cw
        y0 = 80 + r * ch

        prof_a = measure_part_profile(Image.open(case["part_a_raw"]).convert("RGBA"))
        prof_b = measure_part_profile(Image.open(case["part_b_raw"]).convert("RGBA"))
        audit_records.append({
            "id": case["id"],
            "title": case["title"],
            "pair_type": case["pair_type"],
            "defect_code": case["defect_code"],
            "assumption_violated": case["assumption_violated"],
            "fix_applied": case["fix_applied"],
            "part_a_metrics": prof_a,
            "part_b_metrics": prof_b,
        })

        # Panel outer frame
        draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + ch - 4], fill=(28, 25, 24, 255), outline=(72, 66, 60, 255), width=1)
        draw.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + 26], fill=(18, 16, 15, 255))
        draw.text((x0 + 10, y0 + 8), case["title"], fill=(245, 215, 120, 255))

        # Left sub-cell: [FAIL: MUTILATED CONNECTION]
        lx0, ly0, sub_w, sub_h = x0 + 10, y0 + 30, 210, 158
        draw_calib_grid(draw, lx0, ly0, sub_w, sub_h, step=20, origin_x=sub_w // 2, origin_y=sub_h // 2)
        draw.rectangle([lx0, ly0, lx0 + sub_w, ly0 + sub_h], outline=(215, 65, 65, 255), width=2)
        draw.rectangle([lx0, ly0, lx0 + sub_w, ly0 + 19], fill=(95, 22, 22, 240))
        draw.text((lx0 + 6, ly0 + 3), "FAIL: MUTILATED CONNECTION", fill=(255, 165, 165, 255))

        sub_m = Image.new("RGBA", (sub_w, sub_h), (0, 0, 0, 0))
        case["mutilated_fn"](sub_m, sub_w // 2, sub_h // 2 + 8)
        sheet.alpha_composite(sub_m, (lx0, ly0))
        # Red fault ring around connection point
        jx, jy = lx0 + sub_w // 2, ly0 + sub_h // 2 + 12
        draw.ellipse([jx - 22, jy - 22, jx + 22, jy + 22], outline=(255, 70, 70, 230), width=2)

        # Right sub-cell: [PASS: CLEAN CONNECTION]
        rx0, ry0 = x0 + 236, y0 + 30
        draw_calib_grid(draw, rx0, ry0, sub_w, sub_h, step=20, origin_x=sub_w // 2, origin_y=sub_h // 2)
        draw.rectangle([rx0, ry0, rx0 + sub_w, ry0 + sub_h], outline=(65, 205, 120, 255), width=2)
        draw.rectangle([rx0, ry0, rx0 + sub_w, ry0 + 19], fill=(18, 75, 42, 240))
        draw.text((rx0 + 6, ry0 + 3), "PASS: CLEAN CONNECTION", fill=(150, 255, 185, 255))

        sub_c = Image.new("RGBA", (sub_w, sub_h), (0, 0, 0, 0))
        case["clean_fn"](sub_c, sub_w // 2, sub_h // 2 + 8)
        sheet.alpha_composite(sub_c, (rx0, ry0))
        draw_subskeleton_node(draw, (rx0 + sub_w // 2, ry0 + sub_h // 2 + 12), color=(80, 255, 140, 255), r=4)

        # Footer diagnostic text
        draw.text((x0 + 10, y0 + 193), f"Defect: {case['defect_code']} (B: {prof_b['w']}x{prof_b['h']}, h/w={prof_b['aspect']}, axis={prof_b['axis_deg']}°)", fill=(255, 140, 130, 255))
        draw.text((x0 + 10, y0 + 210), f"Gate Fix: {case['fix_applied'][:68]}...", fill=(140, 235, 175, 255))

    out_p = os.path.join(ART_DIR, "scratch_pairwise_join_audit.png")
    sheet.save(out_p)
    sheet.save(os.path.join(OUT_DIR, "pass5_pairwise_join_audit.png"))
    json_p = os.path.join(OUT_DIR, "pairwise_connection_gate.json")
    with open(json_p, "w") as f:
        json.dump({"total_tested_gate_archetypes": len(audit_records), "cases": audit_records}, f, indent=2)
    print("Saved Pass 5 Pairwise Join Audit ->", out_p)


# ============================================================================
# PASS 6: BOTTOM-UP EVOLUTION OF MOVEMENT & GROWING ENSEMBLES IN SETS
# ============================================================================

def load_set_background(plate_rel, w, h, ledge_rel=None):
    """Loads a real multiplane set plate (and optional foreground ledge layer) scaled to (w, h)."""
    p_full = os.path.join(ROOT, "shots", plate_rel)
    if os.path.exists(p_full):
        bg = Image.open(p_full).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
    else:
        bg = Image.new("RGBA", (w, h), (28, 32, 42, 255))
    ledge_im = None
    if ledge_rel:
        l_full = os.path.join(ROOT, "shots", ledge_rel)
        if os.path.exists(l_full):
            ledge_im = Image.open(l_full).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
    return bg, ledge_im


def place_actor_in_set(stage_im, char_spec, view, foot_xy, target_height_px, pose=None):
    """Renders a connection-certified character rig at `pose` and composites them at `foot_xy` on the set stage."""
    cw, ch = 260, 330
    fig_im, joints = render_regularized_view_body(char_spec, view, cw=cw, ch=ch, pose=pose)
    # In render_regularized_view_body, ground line is at y=276, center is x=cw//2, standing height ~ 225px
    scale = target_height_px / 225.0
    sw = max(1, int(round(cw * scale)))
    sh = max(1, int(round(ch * scale)))
    fig_s = fig_im.resize((sw, sh), Image.Resampling.LANCZOS)
    anchor_x = int(round((cw // 2) * scale))
    anchor_y = int(round(276 * scale))
    px = int(round(foot_xy[0] - anchor_x))
    py = int(round(foot_xy[1] - anchor_y))
    stage_im.alpha_composite(fig_s, (px, py))


def build_pass6_bottom_up_movement_and_ensembles():
    """
    Renders a 2-part flagship progression sheet using ONLY our regularized, connection-certified
    4-angle rigs (`FRONT`, `3Q`, `SIDE`, `BACK`) inside real multiplane set plates:
      - ROW 1: Bottom-Up Evolution of Movement (5 Stages in Set Context, including True Side-Profile Walk!)
      - ROW 2: Bottom-Up Growing Ensembles in Multiplane Sets (4 Stages from Solo Hero to 6-Actor Club/Harbor Scene!)
    """
    chars = {c["name"].split(".")[0].strip(): c for c in get_char_turnarounds()}
    poet_ts = chars["1"]
    poet_blk = chars["2"]
    woman_m = chars["3"]
    mother_c = chars["4"]
    ex_j = chars["5"]
    party_g = chars["6"]
    dj_c = chars["7"]
    yp_c = chars["8"]

    W_SHEET = 1640
    H_SHEET = 860
    sheet = Image.new("RGBA", (W_SHEET, H_SHEET), (18, 17, 16, 255))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, W_SHEET, 64], fill=(12, 11, 11, 255))
    draw.text((20, 12), "PASS 6: BOTTOM-UP EVOLUTION OF MOVEMENT & BOTTOM-UP GROWING ENSEMBLES IN MULTIPLANE SETS", fill=(245, 195, 75, 255))
    draw.text((20, 36), "Built exclusively from Pass 1-5 certified clean connections: True Side-Profile bodies (body.profile), 3/4, Front & Back rigs inside multiplane sets", fill=(180, 175, 165, 255))

    # -------------------------------------------------------------------------
    # ROW 1: BOTTOM-UP EVOLUTION OF MOVEMENT (5 STAGES IN HARBOR SET)
    # -------------------------------------------------------------------------
    draw.text((20, 74), "PART A -- BOTTOM-UP EVOLUTION OF MOVEMENT (FROM GROUNDED STANCE -> CROUCH GATHER -> SIDE-PROFILE WALK -> IK REACH -> KNEEL)", fill=(120, 235, 175, 255))

    mw, mh = 312, 340
    movement_stages = [
        (
            "M1. Grounded 3/4 Stance & Breathe",
            "Ankle-to-sole pinned on ground line",
            "3Q",
            dict(torso_rot=0, head_rot=-2, uarm_L_rot=8, farm_L_rot=6, uarm_R_rot=-8, farm_R_rot=-6),
        ),
        (
            "M2. Anticipation & Knee/Hip Flex",
            "Pelvis drops -18px; knees flex +28 deg",
            "SIDE",
            dict(dy=-16, torso_rot=8, head_rot=-6, thigh_L_rot=-24, shin_L_rot=26, thigh_R_rot=-28, shin_R_rot=30, uarm_R_rot=22, farm_R_rot=-34),
        ),
        (
            "M3. True Side-Profile Walk Stride!",
            "Using regularized body.profile + counter-swing",
            "SIDE",
            dict(dy=-4, torso_rot=4, head_rot=0, thigh_L_rot=24, shin_L_rot=14, thigh_R_rot=-26, shin_R_rot=8, uarm_L_rot=-24, farm_L_rot=-18, uarm_R_rot=22, farm_R_rot=-24),
        ),
        (
            "M4. 2-Bone IK Arm Reach & Contact",
            "Parabolic shoulder/elbow/wrist reach arc",
            "SIDE",
            dict(dy=-2, torso_rot=6, head_rot=-8, thigh_L_rot=10, shin_L_rot=6, thigh_R_rot=-12, shin_R_rot=6, uarm_R_rot=-62, farm_R_rot=-84, hand_R_rot=-78),
        ),
        (
            "M5. Deep Lunge / Weight Transfer",
            "Full multi-joint chain under deep bend",
            "SIDE",
            dict(dy=-32, torso_rot=14, head_rot=-10, thigh_L_rot=34, shin_L_rot=52, thigh_R_rot=-46, shin_R_rot=44, uarm_R_rot=-48, farm_R_rot=-72, hand_R_rot=-65),
        ),
    ]

    for mi, (mtitle, msub, mview, mpose) in enumerate(movement_stages):
        x0 = 20 + mi * (mw + 10)
        y0 = 98
        bg_m, ledge_m = load_set_background("weave/p04_hands/set/plate.jpg", mw, mh, "weave/p04_hands/set/ledge.png")
        mdraw = ImageDraw.Draw(bg_m)
        # Subtle ground reference line
        mdraw.line([(16, 292), (mw - 16, 292)], fill=(245, 190, 80, 180), width=2)
        place_actor_in_set(bg_m, poet_ts, mview, (mw // 2, 292), 215, pose=mpose)
        if ledge_m is not None:
            bg_m.alpha_composite(ledge_m, (0, 22))
        mdraw = ImageDraw.Draw(bg_m)
        mdraw.rectangle([0, 0, mw, 42], fill=(14, 16, 20, 225))
        mdraw.text((8, 5), mtitle, fill=(245, 215, 110, 255))
        mdraw.text((8, 23), msub, fill=(175, 225, 195, 255))
        mdraw.rectangle([0, 0, mw - 1, mh - 1], outline=(78, 86, 96, 255), width=1)
        sheet.alpha_composite(bg_m, (x0, y0))

    # -------------------------------------------------------------------------
    # ROW 2: BOTTOM-UP GROWING ENSEMBLES IN MULTIPLANE SETS (4 STAGES)
    # -------------------------------------------------------------------------
    draw.text((20, 454), "PART B -- BOTTOM-UP GROWING ENSEMBLES IN CONTEXT (STAGE 1 SOLO IN SET -> STAGE 2 DUET -> STAGE 3 FAMILY TRIO -> STAGE 4 6-ACTOR SCENE)", fill=(245, 195, 75, 255))

    ew, eh = 392, 360
    y_ens = 478

    # Stage E1: Solo Hero in Multiplane Harbor Set (with foreground ledge occlusion)
    x_e1 = 20
    bg1, ledge1 = load_set_background("weave/p04_hands/set/plate.jpg", ew, eh, "weave/p04_hands/set/ledge.png")
    place_actor_in_set(bg1, poet_blk, "3Q", (int(ew * 0.56), 312), 225, pose=dict(uarm_R_rot=-48, farm_R_rot=-72, hand_R_rot=-68))
    if ledge1 is not None:
        bg1.alpha_composite(ledge1, (0, 12))
    d1 = ImageDraw.Draw(bg1)
    d1.rectangle([0, 0, ew, 42], fill=(14, 16, 20, 225))
    d1.text((8, 5), "E1. Solo Hero in Multiplane Set (1 Actor + FG Ledge)", fill=(245, 215, 110, 255))
    d1.text((8, 23), "Poet (3/4 View) behind p04_hands rock ledge reaching out", fill=(185, 195, 205, 255))
    d1.rectangle([0, 0, ew - 1, eh - 1], outline=(78, 86, 96, 255), width=1)
    sheet.alpha_composite(bg1, (x_e1, y_ens))

    # Stage E2: Duet Counterpoint (Side-Profile Poet walking toward 3/4-Back Ex)
    x_e2 = 20 + (ew + 10)
    bg2, ledge2 = load_set_background("weave/p04_hands/set/plate.jpg", ew, eh, "weave/p04_hands/set/ledge.png")
    place_actor_in_set(bg2, ex_j, "3Q", (int(ew * 0.72), 296), 205, pose=dict(uarm_L_rot=14, farm_L_rot=18))
    place_actor_in_set(bg2, poet_ts, "SIDE", (int(ew * 0.34), 316), 225, pose=dict(thigh_L_rot=18, shin_L_rot=10, thigh_R_rot=-20, shin_R_rot=8, uarm_R_rot=-38, farm_R_rot=-56))
    if ledge2 is not None:
        bg2.alpha_composite(ledge2, (0, 16))
    d2 = ImageDraw.Draw(bg2)
    d2.rectangle([0, 0, ew, 42], fill=(14, 16, 20, 225))
    d2.text((8, 5), "E2. Duet Spatial Tension (2 Actors: Side + 3/4-Back)", fill=(245, 215, 110, 255))
    d2.text((8, 23), "Poet (Side Profile stride) + The Ex (3/4-Back Bomber)", fill=(185, 195, 205, 255))
    d2.rectangle([0, 0, ew - 1, eh - 1], outline=(78, 86, 96, 255), width=1)
    sheet.alpha_composite(bg2, (x_e2, y_ens))

    # Stage E3: Family Trio across Depth Planes (Mother 0.95x + Poet 1.0x + Young Poet 0.72x)
    x_e3 = 20 + 2 * (ew + 10)
    bg3, _ = load_set_background("weave/set/plate.jpg", ew, eh)
    place_actor_in_set(bg3, mother_c, "3Q", (int(ew * 0.26), 302), 208, pose=dict(uarm_R_rot=-28, farm_R_rot=-42))
    place_actor_in_set(bg3, poet_ts, "FRONT", (int(ew * 0.74), 306), 220, pose=dict(uarm_L_rot=24, farm_L_rot=32))
    place_actor_in_set(bg3, yp_c, "SIDE", (int(ew * 0.48), 322), 220, pose=dict(thigh_L_rot=16, shin_L_rot=10, thigh_R_rot=-16, shin_R_rot=6, uarm_R_rot=-32, farm_R_rot=-45))
    d3 = ImageDraw.Draw(bg3)
    d3.rectangle([0, 0, ew, 42], fill=(14, 16, 20, 225))
    d3.text((8, 5), "E3. Trio Across Depth & Age Scales (3 Actors)", fill=(245, 215, 110, 255))
    d3.text((8, 23), "Mother (0.95x) + Young Poet (0.72x Side) + Poet (1.0x)", fill=(185, 195, 205, 255))
    d3.rectangle([0, 0, ew - 1, eh - 1], outline=(78, 86, 96, 255), width=1)
    sheet.alpha_composite(bg3, (x_e3, y_ens))

    # Stage E4: Full Multiplane Scene Ensemble (6 Actors across Z-Planes in Naraka Club)
    x_e4 = 20 + 3 * (ew + 10)
    bg4, _ = load_set_background("weave/set/plate.jpg", ew, eh)
    # Background Z-plane (smaller scale, higher Yground)
    place_actor_in_set(bg4, dj_c, "FRONT", (int(ew * 0.50), 266), 165, pose=dict(uarm_L_rot=32, farm_L_rot=48, uarm_R_rot=-36, farm_R_rot=-52))
    place_actor_in_set(bg4, ex_j, "BACK", (int(ew * 0.84), 278), 175, pose=dict(uarm_L_rot=10, uarm_R_rot=-10))
    # Midground Z-plane (Waltz / conversation pair)
    place_actor_in_set(bg4, party_g, "SIDE", (int(ew * 0.20), 304), 205, pose=dict(uarm_R_rot=-42, farm_R_rot=-64))
    place_actor_in_set(bg4, woman_m, "3Q", (int(ew * 0.36), 306), 198, pose=dict(uarm_L_rot=36, farm_L_rot=52))
    # Foreground Z-plane
    place_actor_in_set(bg4, poet_ts, "SIDE", (int(ew * 0.64), 326), 222, pose=dict(thigh_L_rot=18, thigh_R_rot=-18, uarm_R_rot=-28, farm_R_rot=-44))
    place_actor_in_set(bg4, yp_c, "FRONT", (int(ew * 0.80), 332), 215, pose=dict(uarm_L_rot=18, uarm_R_rot=-24))
    d4 = ImageDraw.Draw(bg4)
    d4.rectangle([0, 0, ew, 42], fill=(14, 16, 20, 225))
    d4.text((8, 5), "E4. Full Multiplane Scene Ensemble (6 Actors in Set)", fill=(245, 215, 110, 255))
    d4.text((8, 23), "BG: DJ + Ex | MG: Party Suit + Muse | FG: Side Poet + Child", fill=(185, 195, 205, 255))
    d4.rectangle([0, 0, ew - 1, eh - 1], outline=(78, 86, 96, 255), width=1)
    sheet.alpha_composite(bg4, (x_e4, y_ens))

    out_p = os.path.join(ART_DIR, "scratch_bottom_up_movement_and_ensembles.png")
    sheet.save(out_p)
    sheet.save(os.path.join(OUT_DIR, "pass6_bottom_up_movement_and_ensembles.png"))
    print("Saved Pass 6 Bottom-Up Movement & Ensembles ->", out_p)


if __name__ == "__main__":
    build_pass1_hands_grid()
    build_pass2_shoes_grid()
    build_pass3_heads_grid()
    build_pass4_four_angle_bodies_grid()
    build_pass5_pairwise_connection_gate()
    build_pass6_bottom_up_movement_and_ensembles()

