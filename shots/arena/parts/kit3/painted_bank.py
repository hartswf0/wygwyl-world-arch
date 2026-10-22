"""Bank of real hand-painted cardboard parts extracted from weave/cast/man/sheets, weave/src, and arena/parts/cut.

Provides:
  - Automatic connected-component & bounding-box extraction of all painted cardboard pieces
  - Structure-preserving gouache + corrugated-flute recoloring (LAB/luminance detail transfer)
  - Blank-plate inpainting for turnaround heads & open-eye fusion for THE WOMAN (via arena/puppet/fusion.py)
  - Real painted face feature plug-ins (eyes, brows, mouths, sunglasses)
  - Real painted body parts (torsos, skirts, upper/lower arms, thighs, shins, boots, hands, replacement poses)
  - Comprehensive Poem Prop & Multiplane Set card builders fusing real painted props and poem footage plates
"""
import glob
import json
import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
MAN_SHEETS = os.path.join(SHOTS, 'weave', 'cast', 'man', 'sheets')
MAN_PARTS = os.path.join(SHOTS, 'weave', 'cast', 'man', 'parts')
WOMAN_PARTS = os.path.join(SHOTS, 'weave', 'assets', 'parts')
WEAVE_SRC = os.path.join(SHOTS, 'weave', 'src')
CUT_DIR = os.path.join(SHOTS, 'arena', 'parts', 'cut')

sys.path.insert(0, os.path.join(SHOTS, 'arena', 'puppet'))
try:
    import fusion as FUSION
except Exception:
    FUSION = None

_SHEET_CACHE = {}
_PIECE_CACHE = {}
_INPAINT_CACHE = {}


def hex_rgb(c):
    c = c.lstrip('#')
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def mix_rgb(c1, c2, t):
    return (
        int(round(c1[0] * (1 - t) + c2[0] * t)),
        int(round(c1[1] * (1 - t) + c2[1] * t)),
        int(round(c1[2] * (1 - t) + c2[2] * t)),
    )


def _load_sheet(path):
    if path not in _SHEET_CACHE:
        _SHEET_CACHE[path] = Image.open(path).convert('RGB')
    return _SHEET_CACHE[path]


def cut_from_sheet(sheet_path, box, keep_holes=False, pad=2):
    """Extract a clean RGBA cardboard cutout from a white-background sheet inside box=(x0,y0,x1,y1)."""
    key = (sheet_path, tuple(box), keep_holes)
    if key in _PIECE_CACHE:
        return _PIECE_CACHE[key].copy()

    im = _load_sheet(sheet_path).crop(box)
    a = np.asarray(im, dtype=np.int32)
    # Near-white background connected to border
    light = (a.min(axis=2) > 208) & (np.ptp(a, axis=2) < 28)
    lab, _ = nd.label(light)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(edge))
    if keep_holes:
        sizes = nd.sum(light, lab, range(1, lab.max() + 1))
        big = [i + 1 for i, s in enumerate(sizes) if s > 140]
        bg |= np.isin(lab, big)
    card = nd.binary_opening(~bg, iterations=1)
    if not keep_holes:
        card = nd.binary_fill_holes(card)
    lab_c, n_c = nd.label(card)
    if n_c > 1:
        sizes = nd.sum(card, lab_c, range(1, n_c + 1))
        # Keep components that are at least 12% of the largest (for 2-piece items like sunglasses hands)
        mx_s = max(sizes)
        keep_ids = [i + 1 for i, s in enumerate(sizes) if s >= mx_s * 0.12]
        card = np.isin(lab_c, keep_ids)
    alpha = np.clip(nd.gaussian_filter(card.astype(np.float32), 0.55) * 255.0, 0, 255).astype(np.uint8)
    rgba = np.dstack([a.astype(np.uint8), alpha])
    ys, xs = np.nonzero(alpha > 12)
    if len(xs) > 0:
        x0 = max(0, int(xs.min()) - pad)
        y0 = max(0, int(ys.min()) - pad)
        x1 = min(rgba.shape[1], int(xs.max()) + 1 + pad)
        y1 = min(rgba.shape[0], int(ys.max()) + 1 + pad)
        rgba = rgba[y0:y1, x0:x1]
    out = Image.fromarray(rgba, 'RGBA')
    _PIECE_CACHE[key] = out
    return out.copy()


def load_cut_png(rel_path):
    """Load an already-cut RGBA PNG from arena/parts/cut, weave/cast/man/parts, or weave/assets/parts."""
    if rel_path in _PIECE_CACHE:
        return _PIECE_CACHE[rel_path].copy()
    im = Image.open(rel_path).convert('RGBA')
    ab = im.getbbox()
    if ab:
        im = im.crop(ab)
    _PIECE_CACHE[rel_path] = im
    return im.copy()


# ---------------------------------------------------------------------------
# Catalog of Exact Bounding Boxes on the Hand-Painted Sheets
# ---------------------------------------------------------------------------
HEADS_TURN_BOXES = {
    'profile_R': (50, 68, 266, 362),
    'threequarter_R': (290, 69, 469, 361),
    'front': (501, 68, 679, 363),
    'threequarter_L': (707, 68, 884, 361),
    'profile_L': (912, 68, 1124, 359),
    'back': (1149, 68, 1333, 369),
    '3q_smile': (51, 425, 247, 714),
    '3q_closed': (269, 425, 459, 711),
    '3q_up': (485, 424, 682, 708),
    '3q_down': (709, 424, 895, 709),
    '3q_sunglasses': (920, 425, 1124, 711),
    '3q_singing': (1142, 424, 1330, 709),
}

HEADS_3Q_EFFORT_BOXES = {
    'prof_strain': (48, 69, 264, 362),
    '3q_pain': (284, 69, 463, 362),
    '3q_yell': (489, 68, 682, 361),
    '3q_tired': (709, 68, 885, 361),
    'prof_L_sad': (911, 68, 1121, 359),
    '3q_afraid': (1139, 69, 1330, 363),
    '3q_shock': (51, 425, 245, 713),
    '3q_angry': (271, 425, 461, 711),
    '3q_warm_smile': (484, 424, 684, 711),
    '3q_laugh': (707, 425, 897, 711),
    '3q_reluctant': (921, 424, 1114, 711),
    '3q_crying': (1138, 425, 1329, 714),
}

BODY_SHEET_BOXES = {
    'front': ('body_front.jpg', {
        'torso': (465, 46, 688, 377),
        'pelvis': (458, 381, 698, 635),
        'uarm.L': (776, 53, 854, 280),
        'uarm.R': (1091, 54, 1169, 279),
        'farm.L': (925, 186, 998, 384),
        'farm.R': (1200, 187, 1279, 385),
        'bent_arm.L': (103, 419, 411, 536),
        'bent_arm.R': (103, 573, 414, 681),
        'leg_boot.L': (742, 412, 896, 736),
        'leg_boot.R': (908, 414, 1065, 736),
        'hand.L': (1108, 468, 1275, 562),
        'hand.R': (1107, 594, 1275, 694),
    }),
    'threequarter': ('body_threequarter.jpg', {
        'torso': (466, 45, 690, 372),
        'pelvis': (457, 375, 698, 629),
        'uarm.L': (779, 57, 856, 281),
        'uarm.R': (1088, 54, 1167, 280),
        'farm.L': (923, 188, 999, 385),
        'farm.R': (1198, 187, 1277, 386),
        'bent_arm.L': (107, 417, 415, 540),
        'bent_arm.R': (103, 569, 413, 682),
        'leg_boot.L': (741, 413, 896, 738),
        'leg_boot.R': (906, 415, 1065, 739),
        'hand.L': (1107, 455, 1277, 552),
        'hand.R': (1108, 596, 1259, 700),
    }),
    'profile': ('body_profile.jpg', {
        'torso': (466, 44, 689, 371),
        'pelvis': (457, 372, 696, 624),
        'uarm.L': (776, 54, 852, 279),
        'uarm.R': (1090, 54, 1169, 279),
        'farm.L': (925, 187, 997, 382),
        'farm.R': (1199, 187, 1276, 385),
        'bent_arm.L': (106, 417, 414, 535),
        'bent_arm.R': (102, 571, 412, 680),
        'leg_boot.L': (740, 412, 893, 735),
        'leg_boot.R': (904, 415, 1063, 737),
        'hand.L': (1107, 455, 1276, 552),
        'hand.R': (1108, 596, 1259, 700),
    }),
    'back': ('body_back.jpg', {
        'torso': (468, 44, 691, 374),
        'pelvis': (458, 372, 699, 625),
        'uarm.L': (775, 54, 852, 279),
        'uarm.R': (1085, 54, 1165, 281),
        'farm.L': (925, 186, 999, 383),
        'farm.R': (1200, 186, 1277, 383),
        'bent_arm.L': (106, 420, 414, 539),
        'bent_arm.R': (104, 572, 414, 683),
        'leg_boot.L': (744, 413, 898, 738),
        'leg_boot.R': (907, 413, 1064, 738),
        'hand.L': (1108, 454, 1277, 553),
        'hand.R': (1107, 595, 1259, 701),
    }),
}

LEGS_SEG_BOXES = {
    'leg_joined.L': (65, 46, 175, 552),
    'leg_joined.R': (217, 46, 327, 554),
    'thigh.L': (391, 47, 499, 244),
    'thigh.R': (579, 47, 685, 241),
    'thigh.short': (762, 49, 868, 199),
    'run_pair': (981, 48, 1315, 390),
    'shin.L': (396, 296, 489, 554),
    'shin.R': (588, 296, 676, 553),
    'shin.bent': (752, 254, 884, 552),
    'boot.flat': (72, 591, 263, 739),
    'boot.heel_up': (305, 563, 482, 737),
    'boot.profile': (557, 589, 743, 734),
    'boot.front': (793, 580, 875, 737),
    'kneel_pair': (963, 462, 1337, 734),
}

LEGS_RUN_BOXES = {
    'run_pass': (55, 42, 299, 294),
    'run_stride': (336, 43, 708, 296),
    'run_kick': (712, 44, 937, 295),
    'float_legs': (1042, 44, 1325, 246),
    'climb_legs': (102, 324, 324, 617),
    'walk_wide': (385, 322, 690, 596),
    'crouch_legs': (778, 333, 943, 574),
    'kneel_tuck': (1074, 332, 1250, 581),
    'lie_flat_legs': (236, 619, 639, 739),
    'lie_bent_legs': (730, 636, 1151, 740),
}

HANDS2_BOXES = {
    'hang_L': (134, 40, 258, 276),
    'hang_R': (379, 39, 500, 276),
    'claw_L': (604, 89, 804, 213),
    'claw_R': (869, 86, 1077, 211),
    'flat_push': (1195, 29, 1230, 278),
    'reach_L': (70, 323, 297, 450),
    'reach_R': (335, 322, 558, 449),
    'open_splay': (639, 273, 788, 501),
    'peace': (919, 277, 1019, 504),
    'listen_ear': (1140, 295, 1286, 495),
    'grip_mic': (78, 521, 291, 712),
    'hold_phone': (340, 528, 542, 706),
    'hold_vinyl': (585, 534, 814, 728),
    'dj_scratch': (854, 531, 1071, 730),
    'in_pocket': (1156, 526, 1297, 743),
}

CONTACT_BOXES = {
    'shoulder_cap_1': (80, 57, 220, 171),
    'forearm_short_1': (310, 66, 534, 152),
    'arm_bent_piped': (599, 60, 906, 267),
    'forearm_long_1': (951, 59, 1303, 155),
    'shoulder_cap_2': (80, 175, 221, 287),
    'forearm_short_2': (311, 184, 533, 268),
    'forearm_long_2': (953, 173, 1305, 268),
    'grip_bar_palm': (68, 344, 265, 496),
    'grip_bar_back': (311, 344, 511, 488),
    'hand_rest': (556, 351, 729, 461),
    'palm_up': (772, 312, 879, 505),
    'palm_spread': (938, 306, 1082, 503),
    'pinch_orb': (1125, 348, 1309, 463),
    'cup_both': (68, 571, 278, 700),
    'hold_box': (345, 523, 548, 749),
    'hand_on_shoulder': (612, 540, 848, 722),
    'hands_clasped': (915, 548, 1085, 726),
    'hold_cup': (1136, 551, 1305, 717),
}

PROPS_SHEET_BOXES = {
    'sunglasses_front': ('props.jpg', (96, 65, 356, 170), False),
    'sunglasses_profile': ('props.jpg', (417, 63, 672, 164), False),
    'sunglasses_folded': ('props.jpg', (754, 57, 965, 161), False),
    'mic_hand_cord': ('props.jpg', (1052, 59, 1249, 351), True),
    'notebook': ('props.jpg', (142, 211, 283, 411), False),
    'open_book': ('props.jpg', (373, 218, 654, 412), False),
    'pen': ('props.jpg', (729, 209, 761, 403), False),
    'smartphone': ('props.jpg', (862, 202, 968, 397), False),
    'vinyl_record': ('props.jpg', (98, 444, 373, 725), False),
    'turntable': ('props.jpg', (415, 462, 645, 707), False),
    'tonearm': ('props.jpg', (660, 462, 743, 707), False),
    'headphones': ('props.jpg', (820, 427, 1009, 609), True),
    'lantern': ('props.jpg', (1115, 356, 1294, 620), False),
    'folded_letter': ('props.jpg', (846, 632, 978, 736), False),
    'stone_bench': ('props.jpg', (1040, 636, 1286, 731), True),
    'railing_tall': ('set_props.jpg', (81, 63, 431, 247), True),
    'railing_low': ('set_props.jpg', (83, 265, 427, 431), True),
    'stairs': ('set_props.jpg', (500, 61, 809, 392), True),
    'wooden_door': ('set_props.jpg', (862, 61, 1045, 385), False),
    'doorframe': ('set_props.jpg', (1074, 57, 1294, 388), True),
    'car_door': ('set_props.jpg', (83, 444, 341, 725), True),
    'cardboard_box': ('set_props.jpg', (374, 549, 529, 724), False),
    'coffee_cup': ('set_props.jpg', (581, 436, 653, 546), False),
    'paper_cup': ('set_props.jpg', (679, 441, 751, 542), False),
    'cup_lid': ('set_props.jpg', (756, 487, 831, 539), False),
    'wooden_table': ('set_props.jpg', (558, 570, 778, 723), True),
    'street_sign': ('set_props.jpg', (1095, 409, 1296, 729), False),
}


# ---------------------------------------------------------------------------
# Structure-Preserving Cardboard Garment & Skin Recoloring
# ---------------------------------------------------------------------------
def recolor_painted_garment(rgba_im, target_hex, piping_hex=None, preserve_kraft=True, floral=False):
    """Recolor a dark hand-painted cardboard garment piece (torso, sleeve, leg, skirt, boot)
    to target_hex (and piping_hex), while 100% preserving its gouache brushwork, horizontal
    corrugated cardboard ribs, raw kraft edge bevel, and brass brads!"""
    arr = np.asarray(rgba_im.convert('RGBA'), dtype=np.float32).copy()
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    fg = alpha > 16
    if not np.any(fg):
        return rgba_im.copy()

    # Distance from alpha edge to protect the raw kraft bevel (outer 3.5 px)
    dist = nd.distance_transform_edt(fg)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)

    # Identify brass brads (warm gold/olive circular highlights inside the piece)
    brad_mask = fg & (r > g * 1.05) & (g > b * 1.18) & (sat > 26) & (lum > 75) & (lum < 225)
    # Identify raw kraft edge bevel
    kraft_edge = fg & (dist <= 3.8) & (r > b + 12) & (lum > 75)
    # Identify existing terracotta piping on the male tracksuit (warm reddish-tan lines inside the garment)
    piping_mask = fg & (~kraft_edge) & (dist > 3.8) & (r > g + 16) & (r > b + 28) & (sat > 24) & (lum > 65)

    # Garment fabric mask: everything inside that isn't kraft edge or brad
    fabric_mask = fg & (~kraft_edge if preserve_kraft else fg) & (~brad_mask) & (~piping_mask)
    if not np.any(fabric_mask):
        fabric_mask = fg & (~kraft_edge)

    tgt = np.array(hex_rgb(target_hex), dtype=np.float32)
    # Extract zero-mean gouache + corrugated flute luminance modulation from fabric pixels
    fab_lum = lum[fabric_mask]
    mean_l = float(np.median(fab_lum)) if len(fab_lum) else 45.0
    std_l = max(8.0, float(np.std(fab_lum))) if len(fab_lum) else 14.0
    # Normalized detail in [-2.5, +2.5]
    detail = np.clip((lum - mean_l) / std_l, -2.4, 2.6)

    # Target contrast scale: brighter targets get strong gouache shadow/highlight modulation
    tgt_lum = 0.299 * tgt[0] + 0.587 * tgt[1] + 0.114 * tgt[2]
    amp = 16.0 if tgt_lum < 75 else (24.0 if tgt_lum < 170 else 20.0)

    for c in range(3):
        ch = rgb[..., c]
        ch[fabric_mask] = np.clip(tgt[c] + detail[fabric_mask] * amp, 0, 255)
        rgb[..., c] = ch

    if np.any(piping_mask):
        if piping_hex:
            ptgt = np.array(hex_rgb(piping_hex), dtype=np.float32)
        else:
            ptgt = tgt * 1.12
        p_detail = np.clip((lum - float(np.median(lum[piping_mask]))) / 16.0, -2.0, 2.0)
        for c in range(3):
            ch = rgb[..., c]
            ch[piping_mask] = np.clip(ptgt[c] + p_detail[piping_mask] * 14.0, 0, 255)
            rgb[..., c] = ch

    arr[..., :3] = rgb
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def recolor_woman_floral_piece(rgba_im, target_hex, piping_hex='#dec078'):
    """Recolor woman's floral torso.png or skirt.png while keeping the hand-painted gold botanical linework."""
    arr = np.asarray(rgba_im.convert('RGBA'), dtype=np.float32).copy()
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    fg = alpha > 16
    if not np.any(fg):
        return rgba_im.copy()
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    dist = nd.distance_transform_edt(fg)

    # In torso.png / skirt.png, the background fabric is teal (b > r, g > r) and the floral vines + brads are warm gold (r > b + 10)
    floral_or_brad = fg & ((r > b + 6) | (lum > 115))
    fabric = fg & (~floral_or_brad) & (dist > 2.5)
    if not np.any(fabric):
        return rgba_im.copy()

    tgt = np.array(hex_rgb(target_hex), dtype=np.float32)
    fl_lum = lum[fabric]
    mean_l = float(np.median(fl_lum))
    std_l = max(7.0, float(np.std(fl_lum)))
    detail = np.clip((lum - mean_l) / std_l, -2.5, 2.5)
    for c in range(3):
        ch = rgb[..., c]
        ch[fabric] = np.clip(tgt[c] + detail[fabric] * 18.0, 0, 255)
        rgb[..., c] = ch

    if piping_hex and piping_hex.lower() != '#dec078':
        ptgt = np.array(hex_rgb(piping_hex), dtype=np.float32)
        vines = floral_or_brad & (dist > 4.0) & (lum < 210)
        if np.any(vines):
            v_det = np.clip((lum - float(np.median(lum[vines]))) / 22.0, -2.0, 2.0)
            for c in range(3):
                ch = rgb[..., c]
                ch[vines] = np.clip(ptgt[c] + v_det[vines] * 20.0, 0, 255)
                rgb[..., c] = ch

    arr[..., :3] = rgb
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def recolor_skin_piece(rgba_im, skin_hex, dummy=False):
    """Adjust skin tone of a painted hand or arm while preserving ink creases, kraft tab, and eyelet."""
    if dummy:
        # Cartoon glove / amber dummy hand
        return recolor_painted_garment(rgba_im, skin_hex, preserve_kraft=True)
    arr = np.asarray(rgba_im.convert('RGBA'), dtype=np.float32).copy()
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    fg = alpha > 16
    if not np.any(fg):
        return rgba_im.copy()
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    dist = nd.distance_transform_edt(fg)

    # Protect ink lines (dark) and kraft wrist tab (light tan near socket)
    ink_mask = fg & (lum < 58)
    skin_mask = fg & (~ink_mask) & (dist > 3.0) & (lum < 190)
    if not np.any(skin_mask):
        return rgba_im.copy()

    tgt = np.array(hex_rgb(skin_hex), dtype=np.float32)
    cur_med = np.array([np.median(rgb[skin_mask, i]) for i in range(3)], dtype=np.float32)
    shift = (tgt - cur_med) * 0.65
    for c in range(3):
        ch = rgb[..., c]
        ch[skin_mask] = np.clip(ch[skin_mask] + shift[c], 0, 255)
        rgb[..., c] = ch
    arr[..., :3] = rgb
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


# ---------------------------------------------------------------------------
# Head Plates (Turnaround + Blank Inpainted + Expression + Woman Fusion)
# ---------------------------------------------------------------------------
def _inpaint_box_smooth(rgba_im, box_rel, replace_with_skin=True):
    """Smoothly inpaint a relative rectangle (x0_f, y0_f, x1_f, y1_f) on a painted head card
    using horizontal cardboard rib continuation + skin grain."""
    im = rgba_im.copy()
    arr = np.asarray(im, dtype=np.float32).copy()
    h, w = arr.shape[:2]
    x0, y0 = int(w * box_rel[0]), int(h * box_rel[1])
    x1, y1 = int(w * box_rel[2]), int(h * box_rel[3])
    x0, y0 = max(2, x0), max(2, y0)
    x1, y1 = min(w - 2, x1), min(h - 2, y1)
    if x1 <= x0 or y1 <= y0:
        return im

    # Sample skin border pixels around the box
    ring = np.zeros((h, w), dtype=bool)
    ring[max(0, y0 - 8):min(h, y1 + 8), max(0, x0 - 10):min(w, x1 + 10)] = True
    ring[y0:y1, x0:x1] = False
    ring &= (arr[..., 3] > 180)
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    skin_ring = ring & (lum > 72) & (lum < 205) & (arr[..., 0] > arr[..., 2] + 15)

    if np.any(skin_ring):
        base_col = np.median(arr[skin_ring, :3], axis=0)
    else:
        base_col = np.array([156.0, 114.0, 84.0], dtype=np.float32)

    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    cy, cx = (y0 + y1) * 0.5, (x0 + x1) * 0.5
    ry, rx = max(1.0, (y1 - y0) * 0.5), max(1.0, (x1 - x0) * 0.5)
    # Soft elliptical feather weight
    d2 = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    w_mask = np.clip(1.0 - np.power(np.clip(d2, 0.0, 1.0), 1.8), 0.0, 1.0)[..., None]

    # Horizontal corrugated cardboard flute + brushstroke grain
    flute = 4.2 * np.sin(yy * (2.0 * math.pi / 6.2))[..., None]
    rng = np.random.default_rng(int(w * 31 + h * 17 + x0))
    grain = nd.gaussian_filter(rng.normal(0.0, 3.2, (y1 - y0, x1 - x0)).astype(np.float32), 0.8)[..., None]
    # Vertical shading gradient matching forehead-to-cheek
    v_grad = ((yy - cy) / ry)[..., None] * (-6.0)
    patch = np.clip(base_col[None, None, :] + flute + grain + v_grad, 0, 255)

    cur = arr[y0:y1, x0:x1, :3]
    arr[y0:y1, x0:x1, :3] = cur * (1.0 - w_mask) + patch * w_mask
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def get_painted_head(cid, build_id, spec, view='front', blank=False, expr='neutral'):
    """Return a real hand-painted cardboard head RGBA card for the given character, view, and blank/expression state."""
    cache_key = ('head', cid, build_id, spec['skin'], spec['hair'], spec['hair_style'], view, blank, expr)
    if cache_key in _INPAINT_CACHE:
        return _INPAINT_CACHE[cache_key].copy()

    hs = spec['hair_style']
    is_woman = (cid == 'woman') or (hs == 'afro') or (build_id == 'wom')

    if is_woman:
        # Use the real hand-painted woman head from weave/assets/parts/head.png + fusion.py open eyes!
        if FUSION is not None:
            if blank:
                base_w = FUSION.plate().copy()
            elif expr in ('closed', 'eyes_closed', 'sleep'):
                base_w = FUSION.poet_head({'eyes': 'closed'})[0].copy()
            elif expr in ('up', 'looking_up', 'awe'):
                base_w = FUSION.poet_head({'eyes': 'o', 'gy': 1.0})[0].copy()
            elif expr in ('down', 'looking_down', 'sad'):
                base_w = FUSION.poet_head({'eyes': 'o', 'lid': 0.45, 'gy': -0.8})[0].copy()
            else:
                base_w = FUSION.poet_head({'eyes': 'o', 'gx': 0.4 if view == 'front' else 0.0})[0].copy()
        else:
            base_w = load_cut_png(os.path.join(WOMAN_PARTS, 'head.png'))

        if view in ('back', 'threequarter_back'):
            # Back of afro head: fill face area with the painted dark-brown afro texture from the left half of head.png
            arr = np.asarray(base_w, dtype=np.float32).copy()
            h, w = arr.shape[:2]
            afro_patch = arr[:, :int(w * 0.52), :3]
            afro_resized = np.asarray(Image.fromarray(afro_patch.astype(np.uint8)).resize((w, h), Image.BILINEAR), dtype=np.float32)
            fg = (arr[..., 3] > 20)
            dist = nd.distance_transform_edt(fg)
            # Keep neck tab at bottom (y > 0.78*h) and kraft edge (dist <= 4)
            yy, xx = np.mgrid[0:h, 0:w]
            replace = fg & (dist > 4.0) & (yy < int(h * 0.77))
            if view == 'threequarter_back':
                replace &= (xx < int(w * 0.85))
            arr[replace, :3] = afro_resized[replace]
            base_w = Image.fromarray(arr.astype(np.uint8), 'RGBA')

        _INPAINT_CACHE[cache_key] = base_w
        return base_w.copy()

    # Male / Child / Elder / Dummy heads
    v_map = {
        'front': 'front',
        'threequarter': 'threequarter_R',
        'profile': 'profile_R',
        'threequarter_back': 'back',
        'back': 'back',
    }.get(view, 'front')

    im = _get_man_turn_head(v_map, expr=expr, blank=blank)

    # If threequarter_back, blend a subtle cheek/ear silhouette on the right edge of back head
    if view == 'threequarter_back':
        prof = _get_man_turn_head('profile_R', expr='neutral', blank=True)
        im = im.copy()

    # Child / clean-shaven adjustment (smooth out beard into painted skin)
    if hs in ('child_curls', 'short_curls', 'braids', 'vintage_part', 'crown_wrap', 'white_headwrap') and view not in ('back', 'threequarter_back'):
        if view == 'front':
            im = _inpaint_box_smooth(im, (0.14, 0.56, 0.86, 0.83))
        elif view == 'threequarter':
            im = _inpaint_box_smooth(im, (0.24, 0.55, 0.92, 0.83))
        elif view == 'profile':
            im = _inpaint_box_smooth(im, (0.36, 0.54, 0.94, 0.83))
        if not blank:
            # Redraw clean painted mouth on the un-bearded chin
            d = ImageDraw.Draw(im)
            w, h = im.size
            mcx = w * (0.50 if view == 'front' else (0.64 if view == 'threequarter' else 0.78))
            mcy = h * 0.65
            d.polygon([(mcx - 18, mcy), (mcx, mcy - 6), (mcx + 18, mcy), (mcx, mcy + 7)],
                      fill=(132, 78, 62, 255), outline=(32, 22, 18, 255), width=2)
            d.line([(mcx - 18, mcy), (mcx + 18, mcy)], fill=(32, 22, 18, 255), width=2)

    # Elder silver/white hair & beard tint or headwrap/crown overlay
    if hs in ('elder_beard', 'cap_beard', 'white_headwrap', 'crown_wrap'):
        arr = np.asarray(im, dtype=np.float32).copy()
        r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        yy, _ = np.mgrid[0:arr.shape[0], 0:arr.shape[1]]
        # Dark hair pixels in top 38% or beard zone
        hair_m = (a > 120) & (lum < 68) & ((yy < arr.shape[0] * 0.38) | (yy > arr.shape[0] * 0.52))
        if hs in ('elder_beard', 'cap_beard', 'white_headwrap') and np.any(hair_m):
            htgt = np.array(hex_rgb(spec['hair']), dtype=np.float32)
            hdet = np.clip((lum - 35.0) / 14.0, -2.0, 2.5)
            for c in range(3):
                ch = arr[..., c]
                ch[hair_m] = np.clip(htgt[c] + hdet[hair_m] * 18.0, 0, 255)
                arr[..., c] = ch
        im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
        if hs in ('crown_wrap', 'white_headwrap', 'cap_beard', 'cap_headphones'):
            d = ImageDraw.Draw(im)
            w, h = im.size
            wcol = hex_rgb(spec['piping'] or spec['hair']) + (255,) if hs == 'crown_wrap' else hex_rgb(spec['hair']) + (255,)
            if hs in ('crown_wrap', 'white_headwrap'):
                d.rounded_rectangle([w * 0.12, 4, w * 0.88, h * 0.28], radius=14, fill=wcol, outline=(28, 22, 18, 255), width=3)
                d.line([(w * 0.14, h * 0.20), (w * 0.86, h * 0.20)], fill=(220, 175, 65, 255), width=4)
            elif hs in ('cap_beard', 'cap_headphones'):
                c_col = (44, 48, 56, 255) if hs == 'cap_headphones' else (88, 92, 98, 255)
                d.chord([w * 0.10, 4, w * 0.90, h * 0.42], 180, 360, fill=c_col, outline=(24, 20, 18, 255), width=3)
                d.line([(w * 0.08, h * 0.23), (w * 0.95, h * 0.23)], fill=c_col, width=8)

    # Ghost / translucent or crash-test dummy styling
    if spec.get('dummy'):
        im = recolor_painted_garment(im, spec['skin'], piping_hex=spec.get('piping'))
    elif spec['skin'] in ('#8b99a8', '#b8b2a6'):
        im = recolor_skin_piece(im, spec['skin'])

    _INPAINT_CACHE[cache_key] = im
    return im.copy()


def _get_man_turn_head(v_key, expr='neutral', blank=False):
    """Load one of the painted male heads from heads.jpg / man_heads_front / man_heads_ie / heads_effort_threequarter."""
    if v_key == 'front' and not blank and expr != 'neutral':
        p1 = os.path.join(CUT_DIR, 'man_heads_front', f'{expr}.png')
        p2 = os.path.join(CUT_DIR, 'man_heads_ie', f'{expr}.png')
        if os.path.exists(p1):
            return load_cut_png(p1)
        if os.path.exists(p2):
            return load_cut_png(p2)
    if v_key == 'threequarter_R' and not blank and expr in HEADS_3Q_EFFORT_BOXES:
        return cut_from_sheet(os.path.join(MAN_SHEETS, 'heads_effort_threequarter.jpg'), HEADS_3Q_EFFORT_BOXES[expr])
    if v_key == 'threequarter_R' and not blank and expr in HEADS_TURN_BOXES:
        return cut_from_sheet(os.path.join(MAN_SHEETS, 'heads.jpg'), HEADS_TURN_BOXES[expr])

    box = HEADS_TURN_BOXES.get(v_key, HEADS_TURN_BOXES['front'])
    im = cut_from_sheet(os.path.join(MAN_SHEETS, 'heads.jpg'), box)
    if blank and v_key != 'back':
        # Smoothly inpaint brows, eyes, and mouth so the head plate is a true blank plate (nose, ears, hair, beard intact!)
        if v_key == 'front':
            im = _inpaint_box_smooth(im, (0.16, 0.30, 0.84, 0.49))  # brows + eyes
            im = _inpaint_box_smooth(im, (0.30, 0.60, 0.70, 0.73))  # mouth inside beard
        elif 'threequarter' in v_key:
            im = _inpaint_box_smooth(im, (0.28, 0.30, 0.92, 0.49))
            im = _inpaint_box_smooth(im, (0.45, 0.60, 0.88, 0.73))
        elif 'profile' in v_key:
            im = _inpaint_box_smooth(im, (0.48, 0.31, 0.90, 0.49))
            im = _inpaint_box_smooth(im, (0.64, 0.60, 0.95, 0.73))
    return im


def get_painted_face_feature(slot, name, view, spec):
    """Extract a real painted cardboard eye pair, brow pair, or mouth plug-in card from the painted expression sheets!"""
    key = ('feat', slot, name, view, spec['skin'], spec.get('dummy'))
    if key in _INPAINT_CACHE:
        return _INPAINT_CACHE[key].copy()

    # Map feature name to the best matching painted expression head
    if view == 'front':
        head_map = {
            'eyes': {
                'open': ('front', 'neutral'),
                'glance_side': ('ie', 'reluctant'),
                'glance_up': ('front', 'looking_up'),
                'glance_down': ('front', 'looking_down'),
                'half': ('ie', 'tired'),
                'closed': ('front', 'eyes_closed'),
                'wide': ('front', 'surprised'),
                'happy_arc': ('front', 'big_smile'),
            },
            'brows': {
                'rest': ('front', 'neutral'),
                'raised': ('front', 'surprised'),
                'sad': ('ie', 'sad'),
                'angry': ('front', 'frowning'),
                'knit': ('ie', 'strain'),
                'one_up': ('ie', 'recognition'),
            },
            'mouth': {
                'rest': ('front', 'neutral'),
                'M_B_P': ('front', 'eyes_closed'),
                'open_A': ('front', 'singing'),
                'open_O': ('ie', 'panting'),
                'E': ('front', 'speaking'),
                'F_V': ('ie', 'listening'),
                'U': ('front', 'surprised'),
                'smile': ('front', 'small_smile'),
                'grin_teeth': ('front', 'big_smile'),
                'frown': ('ie', 'sad'),
                'strain_teeth': ('ie', 'strain'),
                'wavy': ('ie', 'pain'),
            },
        }
        src_folder, src_name = head_map.get(slot, {}).get(name, ('front', 'neutral'))
        folder = 'man_heads_front' if src_folder == 'front' else 'man_heads_ie'
        h_im = load_cut_png(os.path.join(CUT_DIR, folder, f'{src_name}.png'))
        w, h = h_im.size
        if slot == 'eyes':
            crop_box = (int(w * 0.16), int(h * 0.36), int(w * 0.84), int(h * 0.49))
        elif slot == 'brows':
            crop_box = (int(w * 0.15), int(h * 0.29), int(w * 0.85), int(h * 0.38))
        else:
            crop_box = (int(w * 0.28), int(h * 0.58), int(w * 0.72), int(h * 0.74))
    else:
        # Three-quarter or profile painted expression heads
        h3q_map = {
            'open': ('turn', 'threequarter_R'),
            'glance_side': ('eff', '3q_reluctant'),
            'glance_up': ('turn', '3q_up'),
            'glance_down': ('turn', '3q_down'),
            'half': ('eff', '3q_tired'),
            'closed': ('turn', '3q_closed'),
            'wide': ('eff', '3q_shock'),
            'happy_arc': ('eff', '3q_laugh'),
            'rest': ('turn', 'threequarter_R'),
            'raised': ('eff', '3q_shock'),
            'sad': ('eff', '3q_crying'),
            'angry': ('eff', '3q_angry'),
            'knit': ('eff', '3q_pain'),
            'one_up': ('eff', '3q_reluctant'),
            'M_B_P': ('turn', '3q_closed'),
            'open_A': ('eff', '3q_yell'),
            'open_O': ('eff', '3q_shock'),
            'E': ('turn', '3q_singing'),
            'F_V': ('turn', '3q_up'),
            'U': ('eff', '3q_afraid'),
            'smile': ('turn', '3q_smile'),
            'grin_teeth': ('eff', '3q_laugh'),
            'frown': ('eff', '3q_crying'),
            'strain_teeth': ('eff', 'prof_strain'),
            'wavy': ('eff', '3q_pain'),
        }
        kind_s, sname = h3q_map.get(name, ('turn', 'threequarter_R'))
        if kind_s == 'turn':
            h_im = cut_from_sheet(os.path.join(MAN_SHEETS, 'heads.jpg'), HEADS_TURN_BOXES[sname])
        else:
            h_im = cut_from_sheet(os.path.join(MAN_SHEETS, 'heads_effort_threequarter.jpg'), HEADS_3Q_EFFORT_BOXES[sname])
        w, h = h_im.size
        if slot == 'eyes':
            crop_box = (int(w * 0.30), int(h * 0.36), int(w * 0.92), int(h * 0.49))
        elif slot == 'brows':
            crop_box = (int(w * 0.28), int(h * 0.29), int(w * 0.92), int(h * 0.38))
        else:
            crop_box = (int(w * 0.44), int(h * 0.58), int(w * 0.90), int(h * 0.74))

    patch = h_im.crop(crop_box)
    if spec.get('dummy') or spec['skin'] in ('#8b99a8', '#b8b2a6'):
        patch = recolor_skin_piece(patch, spec['skin'], dummy=bool(spec.get('dummy')))

    # Mount the painted feature patch onto a die-cut kraft cardboard plug-in tab with rounded bevel & ink rim
    pw, ph = patch.size
    pad = 6
    cw, ch = pw + pad * 2, ph + pad * 2
    card = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([1, 1, cw - 2, ch - 2], radius=10, fill=(202, 166, 118, 255), outline=(92, 68, 42, 255), width=2)
    mask = Image.new('L', (pw, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle([1, 1, pw - 2, ph - 2], radius=8, fill=255)
    card.paste(patch, (pad, pad), mask)
    cd.rounded_rectangle([pad, pad, cw - pad - 1, ch - pad - 1], radius=8, outline=(28, 22, 18, 255), width=2)

    _INPAINT_CACHE[key] = card
    return card.copy()


def get_painted_sunglasses(view='front'):
    """Return the real hand-painted cardboard sunglasses card from props.jpg."""
    k = 'sunglasses_front' if view == 'front' else ('sunglasses_folded' if view == 'folded' else 'sunglasses_profile')
    sh, box, holes = PROPS_SHEET_BOXES[k]
    return cut_from_sheet(os.path.join(MAN_SHEETS, sh), box, holes)


# ---------------------------------------------------------------------------
# Body Parts, Hands, Boots, and Replacement Pose Sprites
# ---------------------------------------------------------------------------
def get_painted_body_part(part_name, view, cid, build_id, spec):
    """Return a real hand-painted cardboard body part (torso, pelvis, uarm, farm, thigh, shin, boot, hand)
    recolored and styled to match `spec` while preserving painted gouache & corrugated flutes."""
    ckey = ('body_part', part_name, view, cid, build_id, spec['top'], spec['bottom'], spec['skin'], spec['shoe'], spec.get('piping'), spec.get('floral'))
    if ckey in _INPAINT_CACHE:
        return _INPAINT_CACHE[ckey].copy()
    v_key = 'profile' if view == 'profile' else ('back' if 'back' in view else ('threequarter' if 'threequarter' in view else 'front'))
    is_woman_floral = bool(spec.get('floral')) or (cid == 'woman')
    out = None

    if part_name == 'torso':
        if is_woman_floral and v_key in ('front', 'threequarter'):
            base = load_cut_png(os.path.join(WOMAN_PARTS, 'torso.png'))
            out = recolor_woman_floral_piece(base, spec['top'], spec.get('piping'))
        else:
            sh_name, boxes = BODY_SHEET_BOXES[v_key]
            base = cut_from_sheet(os.path.join(MAN_SHEETS, sh_name), boxes['torso'])
            out = recolor_painted_garment(base, spec['top'], spec.get('piping'))
    elif part_name == 'pelvis':
        # Used ONLY for skirt/robe builds!
        base = load_cut_png(os.path.join(WOMAN_PARTS, 'skirt.png'))
        if spec.get('floral'):
            out = recolor_woman_floral_piece(base, spec['bottom'], spec.get('piping'))
        else:
            out = recolor_painted_garment(base, spec['bottom'], spec.get('piping'))
    elif part_name.startswith('uarm'):
        sh_name, boxes = BODY_SHEET_BOXES[v_key]
        base = cut_from_sheet(os.path.join(MAN_SHEETS, sh_name), boxes.get(part_name, boxes['uarm.L']))
        col = spec['skin'] if spec['sleeve'] == 'sleeveless' else ('#181a1e' if spec['sleeve'] == 'stick' else spec['top'])
        out = recolor_painted_garment(base, col, spec.get('piping') if col == spec['top'] else None)
    elif part_name.startswith('farm'):
        sh_name, boxes = BODY_SHEET_BOXES[v_key]
        base = cut_from_sheet(os.path.join(MAN_SHEETS, sh_name), boxes.get(part_name, boxes['farm.L']))
        col = spec['skin'] if spec['sleeve'] in ('sleeveless', 'short') else ('#181a1e' if spec['sleeve'] == 'stick' else spec['top'])
        out = recolor_painted_garment(base, col, spec.get('piping') if col == spec['top'] else None)
    elif part_name.startswith('thigh'):
        bkey = 'thigh.R' if part_name.endswith('.R') else 'thigh.L'
        base = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_segmented.jpg'), LEGS_SEG_BOXES[bkey])
        out = recolor_painted_garment(base, spec['bottom'], spec.get('piping'))
    elif part_name.startswith('shin'):
        if cid == 'woman' or spec.get('floral') or spec['top_kind'] in ('summer_dress', 'sequin_dress'):
            base = cut_from_sheet(os.path.join(WEAVE_SRC, 'poet_parts_sheet.jpg'), (840, 412, 1005, 723))
            out = recolor_skin_piece(base, spec['skin'])
        else:
            bkey = 'shin.R' if part_name.endswith('.R') else 'shin.L'
            base = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_segmented.jpg'), LEGS_SEG_BOXES[bkey])
            col = spec['skin'] if spec['top_kind'] in ('nightshirt', 'striped_tee') else spec['bottom']
            out = recolor_painted_garment(base, col, spec.get('piping') if col == spec['bottom'] else None)
    elif part_name.startswith('foot'):
        fmap = {
            'profile_flat': 'boot.flat',
            'heel_up': 'boot.heel_up',
            'toe_up': 'boot.heel_up',
            'threequarter': 'boot.profile',
            'point_in': 'boot.profile',
            'front': 'boot.front',
            'back': 'boot.front',
        }
        fk = fmap.get(view, 'boot.flat' if v_key != 'front' else 'boot.front')
        base = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_segmented.jpg'), LEGS_SEG_BOXES[fk])
        if view == 'toe_up':
            base = base.rotate(18, resample=Image.BICUBIC, expand=True)
        elif view == 'point_in':
            base = ImageOps.mirror(base)
        out = recolor_painted_garment(base, spec['shoe'], spec.get('shoe_sole'))
    elif part_name.startswith('hand'):
        out = get_painted_hand('relaxed', 'back', spec)

    if out is not None:
        _INPAINT_CACHE[ckey] = out
        return out.copy()
    return None


def get_painted_hand(shape, face='back', spec=None):
    """Return one of the real hand-painted cardboard hands from arena/parts/cut/man_hands, hands_2.jpg, or arms_hands_contact.jpg."""
    s = (shape or 'relaxed').lower()
    hkey = ('hand_card', s, face, spec['skin'] if spec else None, spec.get('dummy') if spec else None)
    if hkey in _INPAINT_CACHE:
        return _INPAINT_CACHE[hkey].copy()
    im = None
    # Check special action/contact hands first
    if s in HANDS2_BOXES:
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'hands_2.jpg'), HANDS2_BOXES[s])
    elif s in CONTACT_BOXES:
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'arms_hands_contact.jpg'), CONTACT_BOXES[s])
    else:
        cut_map = {
            'relaxed': 'relaxed.png' if face == 'back' else 'open_palm.png',
            'open': 'open_back.png' if face == 'back' else 'open_palm.png',
            'flat_push': 'open_back.png' if face == 'back' else 'open_palm.png',
            'fist': 'fist.png',
            'grip': 'grip.png',
            'pinch': 'pinch.png',
            'point': 'point.png',
            'thumb': 'thumb.png',
            'peace': 'peace.png',
            'wave': 'wave.png',
            'hang': 'hang.png',
        }
        if s == 'claw':
            im = cut_from_sheet(os.path.join(MAN_SHEETS, 'hands_2.jpg'), HANDS2_BOXES['claw_L' if face == 'back' else 'claw_R'])
        elif s == 'cup':
            im = cut_from_sheet(os.path.join(MAN_SHEETS, 'arms_hands_contact.jpg'), CONTACT_BOXES['palm_up' if face == 'palm' else 'cup_both'])
        elif s in cut_map:
            p = os.path.join(CUT_DIR, 'man_hands', cut_map[s])
            if os.path.exists(p):
                im = load_cut_png(p)

    if im is None:
        im = load_cut_png(os.path.join(CUT_DIR, 'man_hands', 'relaxed.png'))

    if spec is not None:
        im = recolor_skin_piece(im, spec['skin'], dummy=bool(spec.get('dummy')))
    _INPAINT_CACHE[hkey] = im
    return im.copy()


def get_painted_replacement_pose(pose_slug, view, cid, build_id, spec):
    """Assemble a rich, real hand-painted whole-body replacement card (head & hands left off, or full pose)
    using the painted seated/running/kneeling/crouching/lying sheets (`body_sitting.jpg`, `legs_run_stairs.jpg`, `body_*.jpg`)."""
    p = pose_slug.lower()
    v_key = 'profile' if 'profile' in view else ('back' if 'back' in view else ('threequarter' if 'threequarter' in view else 'front'))
    torso = get_painted_body_part('torso', v_key, cid, build_id, spec)
    uarm = get_painted_body_part('uarm.L', v_key, cid, build_id, spec)
    farm = get_painted_body_part('farm.L', v_key, cid, build_id, spec)

    # Choose lower body from the real painted legs_run_stairs.jpg / legs_segmented.jpg / body_sitting.jpg!
    if 'sit' in p:
        if v_key == 'front':
            # Crop lower seated body from body_sitting.jpg front figure
            sit_full = cut_from_sheet(os.path.join(MAN_SHEETS, 'body_sitting.jpg'), (123, 210, 584, 748))
            return recolor_painted_garment(sit_full, spec['top'], spec.get('piping'))
        else:
            sit_prof = cut_from_sheet(os.path.join(MAN_SHEETS, 'body_sitting.jpg'), (758, 215, 1062, 739))
            return recolor_painted_garment(sit_prof, spec['top'], spec.get('piping'))
    elif 'kneel' in p:
        legs = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_segmented.jpg'), LEGS_SEG_BOXES['kneel_pair'])
    elif 'crouch' in p or 'huddle' in p:
        legs = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_run_stairs.jpg'), LEGS_RUN_BOXES['crouch_legs'])
    elif 'lie_back' in p or 'float' in p or ('back' in p and 'ly' in p):
        legs = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_run_stairs.jpg'), LEGS_RUN_BOXES['lie_flat_legs'])
    elif 'lie_side' in p or 'side' in p or 'sleep' in p or 'curl' in p:
        legs = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_run_stairs.jpg'), LEGS_RUN_BOXES['lie_bent_legs'])
    elif 'fall' in p:
        legs = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_run_stairs.jpg'), LEGS_RUN_BOXES['float_legs'])
    elif 'run' in p or 'dash' in p:
        legs = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_run_stairs.jpg'), LEGS_RUN_BOXES['run_stride'])
    elif 'climb' in p or 'mount' in p:
        legs = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_run_stairs.jpg'), LEGS_RUN_BOXES['climb_legs'])
    else:
        legs = cut_from_sheet(os.path.join(MAN_SHEETS, 'legs_run_stairs.jpg'), LEGS_RUN_BOXES['walk_wide'])

    legs = recolor_painted_garment(legs, spec['bottom'], spec.get('piping'))
    bent_arm = cut_from_sheet(os.path.join(MAN_SHEETS, 'arms_hands_contact.jpg'), CONTACT_BOXES['arm_bent_piped'])
    bent_arm = recolor_painted_garment(bent_arm, spec['top'] if spec['sleeve'] != 'sleeveless' else spec['skin'], spec.get('piping'))

    canvas = Image.new('RGBA', (520, 560), (0, 0, 0, 0))
    if 'lie' in p or 'float' in p or 'sleep' in p:
        t_rot = torso.rotate(82 if 'back' in p else 72, resample=Image.BICUBIC, expand=True)
        t_rot.thumbnail((240, 240), Image.LANCZOS)
        legs.thumbnail((290, 220), Image.LANCZOS)
        bent_arm.thumbnail((190, 150), Image.LANCZOS)
        canvas.alpha_composite(legs, (205, 250))
        canvas.alpha_composite(t_rot, (45, 210))
        canvas.alpha_composite(bent_arm, (95, 185))
    elif 'fall' in p:
        t_rot = torso.rotate(28, resample=Image.BICUBIC, expand=True)
        t_rot.thumbnail((230, 260), Image.LANCZOS)
        legs.thumbnail((260, 240), Image.LANCZOS)
        bent_arm = bent_arm.rotate(-35, resample=Image.BICUBIC, expand=True)
        bent_arm.thumbnail((200, 180), Image.LANCZOS)
        canvas.alpha_composite(legs, (195, 255))
        canvas.alpha_composite(t_rot, (95, 85))
        canvas.alpha_composite(bent_arm, (125, 40))
    else:
        torso.thumbnail((210, 270), Image.LANCZOS)
        legs.thumbnail((290, 280), Image.LANCZOS)
        bent_arm.thumbnail((210, 165), Image.LANCZOS)
        canvas.alpha_composite(legs, (135, 255))
        if spec.get('floral') or cid in ('woman', 'ancestors', 'club_angels'):
            sk = get_painted_body_part('pelvis', v_key, cid, build_id, spec)
            sk.thumbnail((220, 210), Image.LANCZOS)
            canvas.alpha_composite(sk, (145, 225))
        canvas.alpha_composite(torso, (150, 35))
        canvas.alpha_composite(bent_arm, (175, 65))

    ab = canvas.getbbox()
    return canvas.crop(ab) if ab else canvas


# ---------------------------------------------------------------------------
# Poem-Specific Hero Props & Set Multiplane Cards
# ---------------------------------------------------------------------------
def _cardboard_canvas(w, h):
    """Create a transparent RGBA canvas and a corrugated cardboard texture sampler."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _draw_bevel_poly(d, pts, fill_rgb, kraft=(204, 168, 120), ink=(24, 20, 18), rim=4.0, ink_w=2):
    if len(pts) < 3:
        return
    P = np.asarray(pts, dtype=float)
    c = P.mean(0)
    outer = []
    for p in P:
        v = p - c
        nm = np.linalg.norm(v)
        u = v / nm if nm > 1e-6 else np.array([1.0, 0.0])
        outer.append((float(p[0] + u[0] * rim), float(p[1] + u[1] * rim)))
    shadow = [(x + 2.0, y + 2.5) for x, y in outer]
    d.polygon(shadow, fill=(32, 24, 18, 75))
    d.polygon(outer, fill=kraft + (255,), outline=(115, 86, 54, 255), width=1)
    d.polygon(pts, fill=fill_rgb + (255,))
    d.line(list(pts) + [pts[0]], fill=ink + (255,), width=ink_w, joint='curve')


def _draw_brad_px(d, cx, cy, r=6.5, eyelet=False):
    d.ellipse([cx - r - 1.5, cy - r - 1.0, cx + r + 1.5, cy + r + 2.0], fill=(25, 20, 15, 160))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(198, 156, 58, 255), outline=(72, 52, 18, 255), width=1)
    if eyelet:
        ir = max(2.0, r * 0.46)
        d.ellipse([cx - ir, cy - ir, cx + ir, cy + ir], fill=(240, 234, 222, 255), outline=(90, 66, 22, 255), width=1)
    else:
        hr = max(1.5, r * 0.36)
        d.ellipse([cx - r * 0.28 - hr, cy - r * 0.28 - hr, cx - r * 0.28 + hr, cy - r * 0.28 + hr], fill=(248, 224, 138, 255))


def _apply_flutes(im):
    arr = np.asarray(im, dtype=np.float32).copy()
    alpha = arr[..., 3]
    fg = alpha > 12
    if not np.any(fg):
        return im
    h, w = alpha.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    wave = np.sin((yy + 1.2 * np.sin(xx / 45.0)) * (2.0 * math.pi / 6.2)) * 9.5
    rng = np.random.default_rng(int(h * 19 + w * 7))
    grain = nd.gaussian_filter(rng.normal(0.0, 3.5, (h, w)).astype(np.float32), 0.7)
    delta = wave + grain
    for c in range(3):
        ch = arr[..., c]
        ch[fg] = np.clip(ch[fg] + delta[fg], 0, 255)
        arr[..., c] = ch
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def get_painted_prop(prop_id, what='', scale_cm=20):
    """Return a high-resolution RGBA painted cardboard cutout for any prop across Poems 01-14."""
    pid = (prop_id or '').lower().strip()
    key = ('prop', pid)
    if key in _PIECE_CACHE:
        return _PIECE_CACHE[key].copy()

    im = None
    # 1. Direct match or composite from the real painted sheets (props.jpg, set_props.jpg, hands_2.jpg, arms_hands_contact.jpg, arena/parts/cut/props)
    if pid in ('sunglasses', 'sunglasses_front'):
        im = get_painted_sunglasses('front')
    elif pid in ('poem_page', 'letter', 'folded_letter'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['folded_letter'][1])
    elif pid == 'love_letters':
        base = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['folded_letter'][1])
        im = Image.new('RGBA', (260, 210), (0, 0, 0, 0))
        for ang, pos in [(-18, (15, 45)), (12, (75, 25)), (-4, (48, 65))]:
            r_im = base.rotate(ang, resample=Image.BICUBIC, expand=True)
            im.alpha_composite(r_im, pos)
        d = ImageDraw.Draw(im)
        # Ember curl glow on corner
        d.ellipse([175, 110, 225, 160], fill=(245, 110, 32, 210), outline=(255, 210, 90, 255), width=2)
    elif pid in ('notebook', 'journal', 'script', 'hymnal'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['notebook'][1])
        if pid in ('journal', 'hymnal'):
            im = recolor_painted_garment(im, '#5c3c28' if pid == 'journal' else '#682428', '#d8b878')
    elif pid in ('book', 'open_book'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['open_book'][1])
    elif pid in ('pen', 'vape_pen', 'lighter'):
        base = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['pen'][1])
        base = base.rotate(75, resample=Image.BICUBIC, expand=True)
        im = Image.new('RGBA', (base.width + 60, base.height + 50), (0, 0, 0, 0))
        im.alpha_composite(base, (10, 25))
        d = ImageDraw.Draw(im)
        if pid == 'vape_pen':
            d.ellipse([base.width - 6, 38, base.width + 10, 54], fill=(80, 220, 255, 255), outline=(24, 20, 18, 255), width=2)
            for r_w, op in [(18, 110), (30, 65)]:
                d.ellipse([base.width + 6, 22 - r_w // 2, base.width + 26 + r_w, 48 + r_w // 2], fill=(210, 225, 238, op))
        elif pid == 'lighter':
            d.polygon([(base.width - 8, 38), (base.width + 18, 12), (base.width + 6, 46)], fill=(255, 195, 55, 245), outline=(235, 95, 25, 255), width=2)
    elif pid in ('phone', 'phone_camera', 'smartphone'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['smartphone'][1])
    elif pid in ('microphone', 'mic_grip', 'mic_stand'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['mic_hand_cord'][1], True)
    elif pid in ('vinyl_record', 'record'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['vinyl_record'][1])
    elif pid in ('dj_controller', 'turntable'):
        deck = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['turntable'][1])
        arm = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['tonearm'][1])
        im = Image.new('RGBA', (deck.width * 2 + 90, deck.height + 24), (0, 0, 0, 0))
        im.alpha_composite(deck, (8, 12))
        im.alpha_composite(deck, (deck.width + 80, 12))
        im.alpha_composite(arm, (deck.width + 4, 12))
        d = ImageDraw.Draw(im)
        mx = deck.width + 16
        _draw_bevel_poly(d, [(mx, 24), (mx + 56, 24), (mx + 56, deck.height), (mx, deck.height)], (44, 48, 56))
        for fy in range(55, deck.height - 35, 34):
            d.line([(mx + 12, fy), (mx + 44, fy)], fill=(56, 220, 245, 255), width=4)
        _draw_brad_px(d, mx + 28, deck.height // 2, r=6.5)
    elif pid == 'headphones':
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['headphones'][1], True)
    elif pid in ('oil_lantern', 'lantern'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['lantern'][1])
    elif pid in ('bench', 'church_pew', 'pews', 'choir_stand', 'choir_stands', 'kneelers', 'white_shelf', 'hourglass_shelf'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'props.jpg'), PROPS_SHEET_BOXES['stone_bench'][1], True)
        if pid in ('church_pew', 'pews', 'choir_stand', 'choir_stands', 'kneelers'):
            im = recolor_painted_garment(im, '#6b4c35', '#9c7452')
        elif pid in ('white_shelf', 'hourglass_shelf'):
            im = recolor_painted_garment(im, '#ece8df', '#c8c2b6')
    elif pid in ('railing', 'harbor_rail', 'height_marks'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'set_props.jpg'), PROPS_SHEET_BOXES['railing_tall' if pid != 'height_marks' else 'street_sign'][1], pid != 'height_marks')
    elif pid == 'stairs':
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'set_props.jpg'), PROPS_SHEET_BOXES['stairs'][1], True)
    elif pid in ('vintage_door', 'door', 'distant_window', 'motif_window', 'window_glass', 'mirror'):
        door = cut_from_sheet(os.path.join(MAN_SHEETS, 'set_props.jpg'), PROPS_SHEET_BOXES['wooden_door'][1])
        frame = cut_from_sheet(os.path.join(MAN_SHEETS, 'set_props.jpg'), PROPS_SHEET_BOXES['doorframe'][1], True)
        im = Image.new('RGBA', (frame.width + 40, frame.height + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.polygon([(12, frame.height + 4), (frame.width + 28, frame.height + 4), (frame.width + 38, frame.height + 34), (4, frame.height + 34)],
                  fill=(185, 224, 245, 185) if pid in ('window_glass', 'mirror') else (255, 214, 122, 185))
        im.alpha_composite(frame, (20, 8))
        if pid not in ('window_glass', 'mirror'):
            im.alpha_composite(door, (38, 12))
    elif pid in ('car_door', 'family_car', 'traffic', 'motif_ride'):
        cdoor = cut_from_sheet(os.path.join(MAN_SHEETS, 'set_props.jpg'), PROPS_SHEET_BOXES['car_door'][1], True)
        if pid == 'car_door':
            im = cdoor
        else:
            im, d = _cardboard_canvas(420, 240)
            _draw_bevel_poly(d, [(45, 95), (125, 42), (285, 42), (355, 95), (395, 110), (395, 185), (35, 185)], (58, 72, 86))
            d.polygon([(392, 118), (418, 92), (418, 165), (392, 145)], fill=(255, 232, 140, 220))
            cdoor_s = cdoor.resize((125, 130), Image.LANCZOS)
            im.alpha_composite(cdoor_s, (155, 48))
            for wx in (105, 315):
                _draw_bevel_poly(d, [(wx + 32 * math.cos(t), 185 + 32 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 24)], (28, 30, 34))
                _draw_brad_px(d, wx, 185, r=7.0)
            im = _apply_flutes(im)
    elif pid in ('box', 'salvation_gift_boxes', 'gift_boxes', 'drawer'):
        base = cut_from_sheet(os.path.join(MAN_SHEETS, 'set_props.jpg'), PROPS_SHEET_BOXES['cardboard_box'][1]).copy()
        if 'gift' in pid:
            d = ImageDraw.Draw(base)
            w, h = base.size
            d.line([(w * 0.5, 12), (w * 0.5, h - 10)], fill=(195, 48, 42, 240), width=8)
            d.line([(12, h * 0.48), (w - 12, h * 0.48)], fill=(195, 48, 42, 240), width=8)
        im = base
    elif pid in ('coffee_cup', 'drink_cup', 'cup', 'champagne_coupe'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'set_props.jpg'),
                            PROPS_SHEET_BOXES['coffee_cup' if pid == 'coffee_cup' else 'paper_cup'][1])
    elif pid in ('table', 'cafe_table', 'bar_counter', 'admission_booth', 'cafe_chair', 'armchair'):
        im = cut_from_sheet(os.path.join(MAN_SHEETS, 'set_props.jpg'), PROPS_SHEET_BOXES['wooden_table'][1], True).copy()
        if pid == 'bar_counter':
            d = ImageDraw.Draw(im)
            d.line([(14, 24), (im.width - 14, 24)], fill=(56, 225, 245, 255), width=5)
        elif pid in ('cafe_chair', 'armchair'):
            im = recolor_painted_garment(im, '#7c4c34' if pid == 'armchair' else '#485862', '#d2a868')
    elif pid in ('football', 'basketball', 'soccer', 'baseball'):
        p_ball = os.path.join(CUT_DIR, 'props', 'basketball.png')
        base = load_cut_png(p_ball)
        if pid == 'football':
            im = base.resize((int(base.width * 1.38), int(base.height * 0.88)), Image.LANCZOS)
            im = recolor_painted_garment(im, '#7a4428', '#f2ece0')
            d = ImageDraw.Draw(im)
            cx, cy = im.width * 0.5, im.height * 0.45
            d.line([(cx - 28, cy), (cx + 28, cy)], fill=(245, 240, 230, 255), width=4)
            for lx in range(-20, 25, 9):
                d.line([(cx + lx, cy - 8), (cx + lx, cy + 8)], fill=(245, 240, 230, 255), width=3)
        else:
            im = base
    elif pid in ('hand_l', 'hand_r'):
        base = load_cut_png(os.path.join(CUT_DIR, 'man_hands', 'open_back.png' if pid == 'hand_l' else 'relaxed.png'))
        if pid == 'hand_l':
            base = ImageOps.mirror(base)
        d = ImageDraw.Draw(base)
        rng = np.random.default_rng(404 if pid == 'hand_l' else 405)
        for _ in range(28):
            rx = int(rng.uniform(25, base.width - 25))
            ry = int(rng.uniform(20, base.height - 20))
            d.ellipse([rx - 2, ry - 2, rx + 2, ry + 2], fill=(168, 146, 114, 190))
        _draw_brad_px(d, 28, base.height * 0.5, r=7.5)
        im = base

    # 2. Bespoke Poetic Hero Props (painted on corrugated cardboard with kraft bevels & brass brads)
    if im is None:
        if 'tambourine_pieces' in pid:
            im, d = _cardboard_canvas(320, 240)
            _draw_bevel_poly(d, [(35, 110), (95, 45), (175, 58), (155, 88), (95, 76), (58, 128)], (156, 108, 64))
            _draw_bevel_poly(d, [(145, 145), (235, 118), (285, 168), (255, 195), (215, 152), (155, 175)], (148, 100, 58))
            _draw_bevel_poly(d, [(78, 132), (168, 98), (192, 148), (112, 188)], (228, 214, 184))
            for jx, jy in [(75, 68), (138, 62), (248, 138), (195, 195), (92, 198), (275, 112)]:
                _draw_brad_px(d, jx, jy, r=8.0)
            im = _apply_flutes(im)
        elif 'tambourine' in pid:
            im, d = _cardboard_canvas(280, 280)
            cx, cy, r_out, r_in = 140, 140, 108, 82
            outer = [(cx + r_out * math.cos(t), cy + r_out * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 36)]
            inner = [(cx + r_in * math.cos(t), cy + r_in * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 32)]
            _draw_bevel_poly(d, outer, (158, 108, 62))
            _draw_bevel_poly(d, inner, (238, 226, 198), rim=2.0)
            for a_deg in range(25, 340, 48):
                rad = math.radians(a_deg)
                jx, jy = cx + (r_out - 12) * math.cos(rad), cy + (r_out - 12) * math.sin(rad)
                _draw_brad_px(d, jx, jy, r=8.5)
            _draw_brad_px(d, cx, cy + r_out - 12, r=7.0, eyelet=True)
            im = _apply_flutes(im)
        elif pid == 'heart':
            im, d = _cardboard_canvas(260, 280)
            for rad_g, op in [(115, 45), (90, 80)]:
                d.ellipse([130 - rad_g, 145 - rad_g, 130 + rad_g, 145 + rad_g], fill=(255, 185, 75, op))
            _draw_bevel_poly(d, [(95, 38), (122, 38), (126, 95), (92, 95)], (142, 34, 38))
            _draw_bevel_poly(d, [(135, 28), (168, 34), (162, 95), (132, 95)], (168, 42, 44))
            h_pts = [(130, 82), (178, 62), (218, 98), (212, 162), (138, 242), (62, 168), (54, 102), (92, 66)]
            _draw_bevel_poly(d, h_pts, (164, 28, 34))
            d.line([(128, 92), (142, 148), (126, 215)], fill=(92, 14, 18, 255), width=4, joint='curve')
            d.line([(140, 135), (182, 162)], fill=(92, 14, 18, 255), width=3)
            d.ellipse([82, 96, 114, 138], fill=(215, 68, 68, 180))
            _draw_brad_px(d, 130, 145, r=7.5)
            im = _apply_flutes(im)
        elif 'raven' in pid:
            im, d = _cardboard_canvas(340, 240)
            for ox, oy, sc in [(20, 45, 1.0), (165, 18, 0.78), (125, 115, 0.65)]:
                body = [(ox + 20 * sc, oy + 65 * sc), (ox + 75 * sc, oy + 48 * sc), (ox + 135 * sc, oy + 58 * sc),
                        (ox + 158 * sc, oy + 64 * sc), (ox + 132 * sc, oy + 74 * sc), (ox + 75 * sc, oy + 82 * sc), (ox + 12 * sc, oy + 84 * sc)]
                wing_u = [(ox + 58 * sc, oy + 55 * sc), (ox + 95 * sc, oy + 4 * sc), (ox + 145 * sc, oy + 18 * sc), (ox + 105 * sc, oy + 58 * sc)]
                _draw_bevel_poly(d, wing_u, (28, 30, 36), rim=3.0)
                _draw_bevel_poly(d, body, (22, 24, 28), rim=3.0)
                _draw_brad_px(d, ox + 78 * sc, oy + 58 * sc, r=5.0 * sc)
            im = _apply_flutes(im)
        elif 'chapel_remnants' in pid or 'chapel_rubble' in pid:
            im, d = _cardboard_canvas(360, 260)
            # Shattered Gothic arch + charred rose window wheel + fallen ash stones
            _draw_bevel_poly(d, [(36, 224), (58, 72), (132, 28), (165, 64), (138, 92), (98, 78), (84, 224)], (74, 68, 64))
            _draw_bevel_poly(d, [(172, 132), (245, 96), (318, 148), (298, 224), (158, 224)], (62, 56, 52))
            # Broken rose window spokes
            cx, cy = 232, 165
            d.ellipse([cx - 38, cy - 38, cx + 38, cy + 38], fill=(42, 48, 58, 230), outline=(188, 152, 82, 255), width=3)
            for a in range(0, 360, 45):
                ra = math.radians(a)
                d.line([(cx, cy), (cx + 36 * math.cos(ra), cy + 36 * math.sin(ra))], fill=(188, 152, 82, 255), width=2)
            _draw_brad_px(d, cx, cy, r=6.5)
            im = _apply_flutes(im)
        elif 'sea_debris' in pid:
            im, d = _cardboard_canvas(340, 230)
            # Driftwood timber + coiled marine rope + spiral sea shells + kelp fronds
            _draw_bevel_poly(d, [(28, 145), (145, 92), (298, 118), (312, 152), (158, 142), (42, 178)], (104, 78, 54))
            _draw_bevel_poly(d, [(68, 118), (118, 62), (168, 86), (135, 138)], (48, 82, 62))  # kelp
            for sx, sy, sr in [(215, 168, 24), (112, 172, 18)]:
                _draw_bevel_poly(d, [(sx + sr * math.cos(t), sy + sr * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 18)], (228, 212, 188), rim=2.5)
            _draw_brad_px(d, 168, 128, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif 'puzzle_pieces' in pid:
            im, d = _cardboard_canvas(320, 240)
            # 3 interlocking gilded wooden jigsaw puzzle pieces
            for ox, oy, col in [(36, 48, (186, 142, 68)), (152, 38, (164, 118, 52)), (96, 124, (204, 162, 82))]:
                pts = [(ox, oy), (ox + 42, oy), (ox + 52, oy - 14), (ox + 68, oy - 14), (ox + 78, oy),
                       (ox + 112, oy), (ox + 112, oy + 36), (ox + 126, oy + 46), (ox + 126, oy + 62), (ox + 112, oy + 72),
                       (ox + 112, oy + 96), (ox, oy + 96)]
                _draw_bevel_poly(d, pts, col, rim=3.0)
                _draw_brad_px(d, ox + 56, oy + 48, r=5.5)
            im = _apply_flutes(im)
        elif 'mustard_seeds' in pid:
            im, d = _cardboard_canvas(280, 240)
            # Scattered glowing golden-brown mustard seeds on a dark earth disc
            _draw_bevel_poly(d, [(140 + 98 * math.cos(t), 120 + 78 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 32)], (54, 44, 36))
            rng = np.random.default_rng(407)
            for _ in range(18):
                sx = int(rng.uniform(68, 212))
                sy = int(rng.uniform(64, 176))
                d.ellipse([sx - 8, sy - 6, sx + 8, sy + 6], fill=(228, 176, 58, 255), outline=(92, 64, 18, 255), width=2)
            _draw_brad_px(d, 140, 120, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif 'weed' in pid:
            im, d = _cardboard_canvas(280, 280)
            # Recoiling jagged dark thorny weeds
            for bx, ang in [(85, -24), (140, 4), (195, 28)]:
                pts = [(bx, 248), (bx - 24 + ang, 178), (bx + 12 + ang, 142), (bx - 28 + ang, 96),
                       (bx + 18 + ang, 42), (bx + 28 + ang, 108), (bx - 4 + ang, 148), (bx + 32 + ang, 192), (bx + 16, 248)]
                _draw_bevel_poly(d, pts, (46, 56, 42), rim=2.8)
            _draw_brad_px(d, 140, 232, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif 'lantern_staff' in pid:
            im, d = _cardboard_canvas(220, 420)
            _draw_bevel_poly(d, [(98, 95), (118, 95), (114, 402), (102, 402)], (52, 36, 26))
            for r_s, op in [(54, 65), (36, 125)]:
                d.ellipse([108 - r_s, 62 - r_s, 108 + r_s, 62 + r_s], fill=(255, 225, 120, op))
            _draw_bevel_poly(d, [(72, 22), (144, 22), (156, 62), (136, 102), (80, 102), (60, 62)], (188, 146, 54), rim=3.0)
            d.ellipse([86, 40, 130, 84], fill=(255, 246, 195, 255), outline=(120, 88, 24, 255), width=2)
            _draw_brad_px(d, 108, 225, r=7.0)
            im = _apply_flutes(im)
        elif any(w in pid for w in ('star_orb', 'galaxy_disc', 'universe_sphere', 'jupiter_moons', 'moon', 'sun', 'relearned_coin', 'motif_stars')):
            im, d = _cardboard_canvas(280, 280)
            cx, cy, r = 140, 140, 96
            for rg, op in [(125, 55), (108, 95)]:
                d.ellipse([cx - rg, cy - rg, cx + rg, cy + rg], fill=(255, 220, 125, op) if 'sun' in pid or 'star' in pid else (130, 195, 255, op))
            col = (242, 198, 78) if ('star' in pid or 'sun' in pid) else ((52, 74, 118) if 'galaxy' in pid or 'universe' in pid else ((208, 162, 114) if 'jupiter' in pid else (226, 232, 240)))
            _draw_bevel_poly(d, [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 36)], col)
            if 'galaxy' in pid or 'coin' in pid:
                for arm_a in (0, math.pi):
                    pts_sp = [(cx + (t * 11) * math.cos(t + arm_a), cy + (t * 11) * math.sin(t + arm_a)) for t in np.linspace(0.4, 7.2, 28)]
                    d.line(pts_sp, fill=(255, 234, 165, 235), width=4, joint='curve')
            elif 'jupiter' in pid:
                for by, bcol in [(-38, (184, 122, 78, 220)), (-10, (236, 212, 178, 220)), (18, (168, 96, 62, 220)), (44, (218, 184, 144, 220))]:
                    d.line([(cx - r + 14, cy + by), (cx + r - 14, cy + by)], fill=bcol, width=14)
                for mx_o, my_o in [(-118, -55), (-112, 48), (114, -35), (120, 52)]:
                    _draw_brad_px(d, cx + mx_o, cy + my_o, r=8.0)
            _draw_brad_px(d, cx, cy, r=7.0)
            im = _apply_flutes(im)
        elif 'motorcycle' in pid:
            im, d = _cardboard_canvas(440, 260)
            for wx in (92, 348):
                _draw_bevel_poly(d, [(wx + 52 * math.cos(t), 182 + 52 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 28)], (28, 30, 34))
                d.ellipse([wx - 32, 182 - 32, wx + 32, 182 + 32], fill=(92, 96, 104, 255), outline=(22, 20, 18, 255), width=3)
                _draw_brad_px(d, wx, 182, r=7.5)
            _draw_bevel_poly(d, [(92, 182), (175, 112), (285, 108), (348, 182), (235, 182)], (48, 52, 58))
            _draw_bevel_poly(d, [(115, 112), (205, 114), (215, 138), (105, 134)], (58, 42, 32))
            _draw_bevel_poly(d, [(202, 88), (298, 84), (312, 118), (198, 118)], (34, 38, 44))
            d.line([(208, 102), (296, 98)], fill=(215, 222, 230, 255), width=4)
            d.line([(235, 92), (262, 108)], fill=(175, 182, 190, 210), width=2)
            d.line([(295, 62), (348, 182)], fill=(185, 192, 202, 255), width=8)
            _draw_bevel_poly(d, [(312, 72), (344, 72), (344, 104), (312, 104)], (248, 232, 164))
            _draw_brad_px(d, 285, 64, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif 'temple' in pid or 'platform_course' in pid:
            im, d = _cardboard_canvas(440, 300)
            white = (242, 240, 234)
            shade = (218, 214, 204)
            for i in range(3):
                _draw_bevel_poly(d, [(32 + i * 14, 252 - i * 18), (408 - i * 14, 252 - i * 18),
                                     (408 - i * 14, 270 - i * 18), (32 + i * 14, 270 - i * 18)], white if i % 2 == 0 else shade)
            if 'platform' not in pid:
                for ci in range(6):
                    cx_c = 78 + ci * 56
                    _draw_bevel_poly(d, [(cx_c - 11, 96), (cx_c + 11, 96), (cx_c + 13, 216), (cx_c - 13, 216)], white, rim=2.5)
                _draw_bevel_poly(d, [(56, 74), (384, 74), (384, 96), (56, 96)], shade)
                _draw_bevel_poly(d, [(48, 74), (220, 22), (392, 74)], white)
            _draw_brad_px(d, 220, 242, r=7.0)
            im = _apply_flutes(im)
        elif 'hourglass' in pid:
            im, d = _cardboard_canvas(240, 320)
            _draw_bevel_poly(d, [(52, 32), (188, 32), (188, 54), (52, 54)], (74, 48, 34))
            _draw_bevel_poly(d, [(52, 266), (188, 266), (188, 288), (52, 288)], (74, 48, 34))
            bulb_u = [(68, 54), (172, 54), (158, 128), (128, 158), (112, 158), (82, 128)]
            bulb_l = [(112, 162), (128, 162), (158, 192), (172, 266), (68, 266), (82, 192)]
            _draw_bevel_poly(d, bulb_u, (212, 226, 234))
            _draw_bevel_poly(d, bulb_l, (212, 226, 234))
            d.polygon([(88, 118), (152, 118), (124, 156), (116, 156)], fill=(235, 178, 68, 255))
            d.polygon([(120, 164), (164, 264), (76, 264)], fill=(235, 178, 68, 255))
            d.polygon([(108, 158), (120, 115), (134, 158)], fill=(255, 115, 28, 235))
            _draw_brad_px(d, 120, 160, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif any(w in pid for w in ('poppy', 'blossom', 'flower', 'daisy', 'bloom', 'motif_field', 'garland')):
            im, d = _cardboard_canvas(260, 300)
            _draw_bevel_poly(d, [(124, 115), (136, 115), (132, 278), (120, 278)], (58, 96, 52), rim=2.5)
            _draw_bevel_poly(d, [(128, 195), (178, 168), (162, 212), (128, 212)], (68, 112, 58), rim=2.5)
            cx, cy = 130, 98
            pcol = (212, 42, 38) if 'poppy' in pid else ((138, 64, 168) if 'purple' in pid else ((246, 244, 238) if 'daisy' in pid else (238, 184, 48)))
            n_pet = 11 if 'daisy' in pid else 6
            for i in range(n_pet):
                ang = i * (2 * math.pi / n_pet)
                px, py = cx + 44 * math.cos(ang), cy + 44 * math.sin(ang)
                r_p = 16 if 'daisy' in pid else 28
                pts_p = [(px + r_p * math.cos(t), py + r_p * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 18)]
                _draw_bevel_poly(d, pts_p, pcol, rim=2.5)
            _draw_bevel_poly(d, [(cx + 22 * math.cos(t), cy + 22 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 20)],
                             (238, 192, 48) if 'daisy' in pid else (38, 28, 24), rim=2.0)
            _draw_brad_px(d, 128, 235, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif 'phone_booth' in pid:
            im, d = _cardboard_canvas(260, 380)
            _draw_bevel_poly(d, [(48, 28), (212, 28), (212, 352), (48, 352)], (64, 78, 92))
            d.rectangle([58, 38, 202, 64], fill=(255, 242, 185, 255), outline=(24, 20, 18, 255), width=2)
            for gy in (74, 164, 254):
                d.rectangle([64, gy, 196, gy + 78], fill=(168, 212, 228, 185), outline=(32, 36, 42, 255), width=3)
            d.rectangle([148, 138, 184, 196], fill=(42, 46, 52, 255), outline=(20, 18, 16, 255), width=2)
            _draw_brad_px(d, 130, 195, r=7.0)
            im = _apply_flutes(im)
        elif any(w in pid for w in ('booth_handset', 'corded_receiver', 'corded_phone')):
            im, d = _cardboard_canvas(280, 240)
            if 'phone' in pid:
                _draw_bevel_poly(d, [(65, 118), (215, 118), (235, 195), (45, 195)], (42, 46, 54))
                d.ellipse([108, 132, 172, 184], fill=(228, 220, 204, 255), outline=(24, 20, 18, 255), width=2)
            # Classic curved handset + coiled cord
            _draw_bevel_poly(d, [(48, 62), (98, 48), (182, 48), (232, 62), (222, 98), (182, 82), (98, 82), (58, 98)], (34, 38, 44))
            pts_c = [(68, 98 + i * 10 + 6 * math.sin(i * 1.5)) for i in range(10)]
            for i in range(len(pts_c) - 1):
                d.line([pts_c[i], pts_c[i + 1]], fill=(28, 30, 34, 255), width=4)
            _draw_brad_px(d, 140, 66, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif 'suitcase' in pid:
            im, d = _cardboard_canvas(260, 300)
            col = (38, 42, 48) if 'poet' in pid else (128, 84, 52)
            _draw_bevel_poly(d, [(98, 28), (162, 28), (162, 82), (148, 82), (148, 44), (112, 44), (112, 82), (98, 82)], (62, 66, 72), rim=2.5)
            _draw_bevel_poly(d, [(54, 78), (206, 78), (206, 258), (54, 258)], col)
            d.line([(68, 135), (192, 135)], fill=(24, 20, 18, 220), width=3)
            d.line([(68, 198), (192, 198)], fill=(24, 20, 18, 220), width=3)
            _draw_brad_px(d, 130, 36, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif 'guitar' in pid or 'gramophone' in pid:
            im, d = _cardboard_canvas(260, 380)
            if 'gramophone' in pid:
                _draw_bevel_poly(d, [(58, 235), (202, 235), (212, 338), (48, 338)], (118, 76, 44))
                _draw_bevel_poly(d, [(125, 195), (92, 68), (218, 34), (232, 158)], (218, 174, 68))
                _draw_brad_px(d, 130, 285, r=7.0)
            else:
                _draw_bevel_poly(d, [(116, 24), (144, 24), (140, 195), (120, 195)], (78, 52, 34))
                body = [(102, 168), (158, 168), (186, 205), (168, 245), (204, 295), (184, 348), (76, 348), (56, 295), (92, 245), (74, 205)]
                _draw_bevel_poly(d, body, (178, 118, 62))
                d.ellipse([104, 224, 156, 276], fill=(38, 26, 20, 255), outline=(232, 198, 132, 255), width=3)
                _draw_brad_px(d, 130, 195, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif 'ice_bath' in pid or 'basin' in pid or 'baptism' in pid:
            im, d = _cardboard_canvas(340, 220)
            _draw_bevel_poly(d, [(32, 68), (308, 68), (276, 178), (64, 178)], (178, 208, 226))
            d.ellipse([32, 44, 308, 96], fill=(132, 188, 218, 255), outline=(28, 34, 42, 255), width=3)
            for ix, iy in [(95, 62), (155, 58), (215, 66), (132, 74), (188, 72)]:
                d.polygon([(ix, iy), (ix + 22, iy - 6), (ix + 28, iy + 10), (ix + 6, iy + 14)], fill=(242, 250, 255, 235), outline=(92, 138, 168, 255), width=2)
            _draw_brad_px(d, 48, 95, r=6.5, eyelet=True)
            _draw_brad_px(d, 292, 95, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif any(w in pid for w in ('pearl', 'rosary', 'wedding_band', 'engagement_ring', 'wedding_ring')):
            im, d = _cardboard_canvas(280, 240)
            cx, cy = 140, 120
            if 'ring' in pid or 'band' in pid:
                for ox, col in [(-38, (232, 188, 64)), (38, (232, 188, 64))]:
                    pts_r = [(cx + ox + 52 * math.cos(t), cy + 52 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 28)]
                    _draw_bevel_poly(d, pts_r, col)
                    d.ellipse([cx + ox - 32, cy - 32, cx + ox + 32, cy + 32], fill=(242, 236, 224, 255), outline=(92, 68, 22, 255), width=2)
                if 'engagement' in pid:
                    d.polygon([(cx - 38, cy - 78), (cx - 20, cy - 58), (cx - 38, cy - 44), (cx - 56, cy - 58)], fill=(215, 242, 255, 255), outline=(24, 20, 18, 255), width=2)
            else:
                bcol = (246, 242, 234) if 'pearl' in pid else (112, 74, 46)
                for a in np.linspace(0, 2 * math.pi, 18, endpoint=False):
                    bx, by = cx + 68 * math.cos(a), cy + 54 * math.sin(a)
                    _draw_bevel_poly(d, [(bx + 11 * math.cos(t), by + 11 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 14)], bcol, rim=2.0)
            _draw_brad_px(d, cx, cy - 54, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        elif any(w in pid for w in ('candle', 'letter_fire')):
            im, d = _cardboard_canvas(220, 300)
            for rg, op in [(64, 55), (42, 95)]:
                d.ellipse([110 - rg, 75 - rg, 110 + rg, 75 + rg], fill=(255, 195, 65, op))
            _draw_bevel_poly(d, [(82, 112), (138, 112), (142, 268), (78, 268)], (242, 234, 214))
            d.polygon([(110, 28), (132, 78), (110, 108), (88, 78)], fill=(255, 175, 38, 255), outline=(212, 68, 18, 255), width=2)
            _draw_brad_px(d, 110, 195, r=6.5)
            im = _apply_flutes(im)
        elif any(w in pid for w in ('tv', 'escape_screens', 'projection_wall', 'wall_screen', 'archival_photo', 'title_card')):
            im, d = _cardboard_canvas(340, 240)
            _draw_bevel_poly(d, [(24, 24), (316, 24), (316, 216), (24, 216)], (74, 62, 52) if 'tv' in pid else (188, 154, 112))
            scr_col = (64, 152, 186, 255) if ('tv' in pid or 'screen' in pid or 'projection' in pid) else (238, 228, 208, 255)
            d.rectangle([42, 40, 298, 196], fill=scr_col, outline=(24, 20, 18, 255), width=3)
            if 'title_card' in pid:
                d.text((170, 118), "WHERE YOU GO\nWHEN YOU LEAVE", fill=(28, 22, 18, 255), anchor='mm')
            else:
                for sy in range(54, 190, 16):
                    d.line([(48, sy), (292, sy)], fill=(195, 238, 255, 110), width=2)
            _draw_brad_px(d, 170, 204, r=6.5)
            im = _apply_flutes(im)
        elif 'steering_wheel' in pid:
            im, d = _cardboard_canvas(260, 260)
            cx, cy = 130, 130
            _draw_bevel_poly(d, [(cx + 96 * math.cos(t), cy + 96 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 32)], (38, 42, 48))
            d.ellipse([cx - 68, cy - 68, cx + 68, cy + 68], fill=(242, 236, 224, 255), outline=(24, 20, 18, 255), width=3)
            _draw_bevel_poly(d, [(cx - 72, cy - 12), (cx + 72, cy - 12), (cx + 72, cy + 12), (cx - 72, cy + 12)], (48, 52, 58))
            _draw_brad_px(d, cx, cy, r=8.0)
            im = _apply_flutes(im)
        elif 'moored_boat' in pid:
            im, d = _cardboard_canvas(380, 260)
            _draw_bevel_poly(d, [(178, 28), (192, 28), (192, 175), (178, 175)], (98, 68, 44))
            _draw_bevel_poly(d, [(194, 36), (312, 148), (194, 158)], (242, 236, 222))
            _draw_bevel_poly(d, [(36, 168), (344, 168), (298, 228), (82, 228)], (68, 92, 114))
            _draw_brad_px(d, 185, 195, r=7.0)
            im = _apply_flutes(im)
        elif 'nest_tree' in pid:
            im, d = _cardboard_canvas(320, 340)
            _draw_bevel_poly(d, [(136, 148), (184, 148), (198, 318), (122, 318)], (88, 62, 42))
            _draw_bevel_poly(d, [(160 + 112 * math.cos(t), 118 + 82 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 28)], (54, 88, 52))
            _draw_bevel_poly(d, [(118, 128), (202, 128), (186, 162), (134, 162)], (142, 104, 62))
            _draw_brad_px(d, 160, 145, r=6.5)
            im = _apply_flutes(im)
        elif 'footprints' in pid:
            im, d = _cardboard_canvas(320, 220)
            for fx, fy, ang in [(58, 138, -12), (148, 86, 8), (238, 128, -8)]:
                _draw_bevel_poly(d, [(fx - 18, fy - 34), (fx + 18, fy - 34), (fx + 22, fy + 28), (fx - 22, fy + 28)], (78, 68, 58), rim=2.5)
            _draw_brad_px(d, 148, 86, r=6.0)
            im = _apply_flutes(im)
        elif 'bread_loaves' in pid:
            im, d = _cardboard_canvas(300, 220)
            for ox, oy in [(38, 88), (138, 68)]:
                _draw_bevel_poly(d, [(ox, oy + 48), (ox + 22, oy), (ox + 108, oy), (ox + 128, oy + 48), (ox + 118, oy + 78), (ox + 12, oy + 78)], (194, 138, 72))
            _draw_brad_px(d, 150, 125, r=6.5)
            im = _apply_flutes(im)
        elif any(w in pid for w in ('curtain', 'blind_cord', 'blankets', 'mattress_pad', 'folded_jacket', 'puppet_strings')):
            im, d = _cardboard_canvas(280, 260)
            col = (44, 48, 56) if 'jacket' in pid else ((148, 54, 48) if 'curtain' in pid else (196, 186, 168))
            _draw_bevel_poly(d, [(42, 42), (238, 42), (248, 218), (32, 218)], col)
            for lx in range(68, 220, 36):
                d.line([(lx, 48), (lx - 6, 212)], fill=(28, 22, 18, 180), width=3)
            _draw_brad_px(d, 140, 130, r=6.5, eyelet=True)
            im = _apply_flutes(im)
        else:
            im, d = _cardboard_canvas(280, 220)
            _draw_bevel_poly(d, [(28, 28), (252, 28), (252, 192), (28, 192)], (182, 148, 108))
            d.rectangle([42, 42, 238, 178], fill=(64, 58, 52, 255), outline=(24, 20, 18, 255), width=2)
            _draw_brad_px(d, 140, 110, r=7.0, eyelet=True)
            im = _apply_flutes(im)

    _PIECE_CACHE[key] = im
    return im.copy()


def get_poem_footage_refs(poem_num):
    """Collect all matched footage frames, cel renders, multiplane exploded views, and Prelinger archive metadata
    for Poem `poem_num` ('01'..'14') from cel_assets/scion, cel_assets/posters, cel_assets/video, film/poems.json, and shots/out."""
    pnum = f"{int(poem_num):02d}"
    refs = []
    # 1. Scion / cel_assets/video beats (P01-001 .. P14-009)
    scion_jsons = sorted(glob.glob(os.path.join(SHOTS, 'cel_assets', 'scion', f'P{pnum}-*.json')))
    for sj_path in scion_jsons:
        sj = json.load(open(sj_path))
        bid = sj['id']
        poster_rel = f"cel_assets/posters/{bid}.jpg"
        scion_rel = f"cel_assets/scion/{bid}.jpg"
        patch_rel = f"cel_assets/patches/{bid}.mp4"
        kfs = sorted(glob.glob(os.path.join(SHOTS, 'cel_assets', 'video', bid, 'out', '*')))
        kf_rel = os.path.relpath(kfs[0], SHOTS).replace(os.sep, '/') if kfs else None
        mp_layers = []
        if kfs:
            for sp in sorted(glob.glob(os.path.join(kfs[0], 'multiplane', 'S*.png'))):
                mp_layers.append(os.path.relpath(sp, SHOTS).replace(os.sep, '/'))
        refs.append({
            'id': bid,
            'kind': 'poem_beat',
            'scene': sj.get('scene', ''),
            'name': sj.get('name', ''),
            'what': sj.get('what', ''),
            'line': sj.get('line', ''),
            'archive_title': sj.get('title', ''),
            'archive_year': sj.get('year', ''),
            'poster': poster_rel if os.path.exists(os.path.join(SHOTS, poster_rel)) else None,
            'scion_strip': scion_rel if os.path.exists(os.path.join(SHOTS, scion_rel)) else None,
            'video_patch': patch_rel if os.path.exists(os.path.join(SHOTS, patch_rel)) else None,
            'image': f"{kf_rel}/image.jpg" if kf_rel and os.path.exists(os.path.join(SHOTS, kf_rel, 'image.jpg')) else poster_rel,
            'cel': f"{kf_rel}/cartoon/cel.png" if kf_rel and os.path.exists(os.path.join(SHOTS, kf_rel, 'cartoon', 'cel.png')) else None,
            'exploded': f"{kf_rel}/multiplane/exploded.jpg" if kf_rel and os.path.exists(os.path.join(SHOTS, kf_rel, 'multiplane', 'exploded.jpg')) else None,
            'multiplane_layers': mp_layers,
        })

    # 2. High-res district/poem shots from film/poems.json -> shots/out/<uuid>/ & shots/world/<short_uuid>/
    poems_json = os.path.join(SHOTS, 'film', 'poems.json')
    if os.path.exists(poems_json):
        pdata = next((x for x in json.load(open(poems_json)) if x.get('num') == pnum), None)
        if pdata:
            for sh in pdata.get('shots', []):
                sid = sh['id']
                out_dir = os.path.join(SHOTS, 'out', sid)
                wkey = sid.split('-')[0] + '_' + sid.split('_')[-1]
                w_dir = os.path.join(SHOTS, 'world', wkey)
                if os.path.exists(os.path.join(out_dir, 'image.jpg')):
                    w_layers = [f"world/{wkey}/{os.path.basename(p)}" for p in sorted(glob.glob(os.path.join(w_dir, 'S*.webp')))]
                    refs.append({
                        'id': sid,
                        'kind': 'district_plate',
                        'scene': pdata.get('district_name', ''),
                        'name': f"Shot #{sh.get('n')} · {sh.get('move', 'push')}",
                        'what': sh.get('action', ''),
                        'line': pdata.get('tagline', ''),
                        'archive_title': f"District: {pdata.get('district_name', 'Atlantis')}",
                        'archive_year': 'Multiplane Volume',
                        'image': f"out/{sid}/image.jpg",
                        'clean_plate': f"out/{sid}/clean_plate.jpg" if os.path.exists(os.path.join(out_dir, 'clean_plate.jpg')) else None,
                        'cel': f"out/{sid}/cartoon/cel.png" if os.path.exists(os.path.join(out_dir, 'cartoon', 'cel.png')) else None,
                        'exploded': f"out/{sid}/multiplane/exploded.jpg" if os.path.exists(os.path.join(out_dir, 'multiplane', 'exploded.jpg')) else None,
                        'multiplane_layers': w_layers,
                    })
    return refs


def build_set_stage_card(set_id, set_what, ref_entry, w=560, h=340):
    """Build a die-cut corrugated cardboard Multiplane Set Card framing a real footage/plate image
    with kraft stage wings, depth-plane registration tabs (P0/P2/P4/P6), and brass corner brads."""
    im, d = _cardboard_canvas(w, h)
    _draw_bevel_poly(d, [(18, 18), (w - 18, 18), (w - 18, h - 18), (18, h - 18)], (196, 160, 114), rim=5.0, ink_w=3)

    # Paste matched plate or cel inside the cardboard proscenium opening
    iw, ih = w - 68, h - 78
    ix0, iy0 = 34, 34
    plate_im = None
    if ref_entry:
        for cand in (ref_entry.get('clean_plate'), ref_entry.get('image'), ref_entry.get('poster')):
            if cand and os.path.exists(os.path.join(SHOTS, cand)):
                try:
                    plate_im = Image.open(os.path.join(SHOTS, cand)).convert('RGB').resize((iw, ih), Image.LANCZOS)
                    break
                except Exception:
                    pass
    if plate_im is None:
        plate_im = Image.new('RGB', (iw, ih), (32, 38, 48))

    im.paste(plate_im.convert('RGBA'), (ix0, iy0))
    d.rectangle([ix0, iy0, ix0 + iw, iy0 + ih], outline=(24, 20, 18, 255), width=3)

    # Four corner brass stage registration brads + bottom proscenium tab
    for bx, by in [(26, 26), (w - 26, 26), (26, h - 26), (w - 26, h - 26), (w // 2, h - 24)]:
        _draw_brad_px(d, bx, by, r=6.5)

    return im
