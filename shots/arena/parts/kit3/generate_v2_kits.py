"""Generate all painted sheets, separate RGBA cut-out parts, assembled poses, Poem Prop Kits, and Poem Multiplane Set Kits for v2.

Usage:
    python3 shots/arena/parts/kit3/generate_v2_kits.py

Outputs under shots/arena/parts/kit3/v2/:
  - sheets/<pid>.jpg                         2048x1152 painted cardboard kit sheets (220 costume + 39 action + 14 prop + 14 set = 287 sheets)
  - packs/<pid>.jpg                          2688x1560 3-panel pack sheets with painted Panel A & populated Panel B
  - parts/<kit_id>/<part_name>.png           Separate transparent RGBA cut-out PNGs for every part of every character, prop, and set kit
  - poses/<kit_id>/<pose_name>.png           Separate transparent RGBA assembled pose PNGs for every kit
  - poses/<kit_id>.poses.jpg                 All-poses contact sheet for every costume kit and poem action kit
  - kits.json                                Complete manifest with cast, poems, prop_kit, set_kit, footage_refs, scenes, and riverbeds
"""
import glob
import json
import math
import os
import shutil
import sys
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit as K
import packs as PKS
import v2 as V2
import painted_bank as PB
from kit import font, FONTB, FONT, MONO, INK, PAPER, SHEET_W, SHEET_H, SOCK_A, SOCK_B, cross, dashed

SHOTS = V2.SHOTS
OUT = V2.OUT


def hex_rgb(c):
    c = c.lstrip('#')
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def draw_brad(d, c, r=6.5, eyelet=False):
    cx, cy = float(c[0]), float(c[1])
    d.ellipse([cx - r - 1.5, cy - r - 1.0, cx + r + 1.5, cy + r + 2.0], fill=(25, 20, 15, 160))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(198, 156, 58, 255), outline=(72, 52, 18, 255), width=1)
    if eyelet:
        ir = max(2.0, r * 0.48)
        d.ellipse([cx - ir, cy - ir, cx + ir, cy + ir], fill=(242, 236, 224, 255), outline=(90, 66, 22, 255), width=1)
    else:
        hr = max(1.5, r * 0.38)
        d.ellipse([cx - r * 0.28 - hr, cy - r * 0.28 - hr, cx - r * 0.28 + hr, cy - r * 0.28 + hr], fill=(248, 224, 138, 255))


def draw_crash_target(d, cx, cy, r):
    amb = (255, 210, 63, 255)
    blk = (18, 20, 24, 255)
    for q in range(4):
        d.pieslice([cx - r, cy - r, cx + r, cy + r], q * 90, (q + 1) * 90, fill=blk if q % 2 == 0 else amb, outline=blk, width=1)


# ---------------------------------------------------------------------------
# Costume Visual Specifications (All 28 Costumes across 14 Cast Entries)
# ---------------------------------------------------------------------------
COSTUME_SPEC = {
    'black_tshirt': dict(
        skin='#8a644e', hair='#1b1715', hair_style='fade_beard',
        top='#23262b', top_hi='#32363e', top_kind='tshirt', sleeve='short',
        piping=None, bottom='#282c34', bottom_hi='#363b46',
        shoe='#1e2024', shoe_sole='#383430', shoe_kind='sneaker', glasses=False
    ),
    'red_black_sunglasses': dict(
        skin='#8a644e', hair='#1b1715', hair_style='fade_beard',
        top='#1d2025', top_hi='#2b2f36', top_kind='track_jacket', sleeve='long',
        piping='#d95040', bottom='#1d2025', bottom_hi='#2b2f36',
        shoe='#16181c', shoe_sole='#2c2018', shoe_kind='chelsea', glasses=True
    ),
    'ex_jacket': dict(
        skin='#825c46', hair='#181514', hair_style='short_back',
        top='#333b2e', top_hi='#454f3e', top_kind='bomber', sleeve='long',
        piping='#22261e', bottom='#232832', bottom_hi='#313846',
        shoe='#e8e4dc', shoe_sole='#989288', shoe_kind='sneaker', glasses=False
    ),
    'pajamas_winter': dict(
        skin='#8c644c', hair='#1c1816', hair_style='child_curls',
        top='#4d6b8e', top_hi='#6889ae', top_kind='flannel_pj', sleeve='long',
        piping='#8faec8', bottom='#4d6b8e', bottom_hi='#6889ae',
        shoe='#d6d0c4', shoe_sole='#aba496', shoe_kind='socks', glasses=False
    ),
    'child_clothes': dict(
        skin='#8c644c', hair='#1c1816', hair_style='child_curls',
        top='#d9962b', top_hi='#e8b252', top_kind='striped_tee', sleeve='short',
        piping='#2b4468', bottom='#364a66', bottom_hi='#486082',
        shoe='#dcd8ce', shoe_sole='#4a4640', shoe_kind='sneaker', glasses=False
    ),
    'ghost_nightclothes': dict(
        skin='#8b99a8', hair='#46505a', hair_style='child_curls',
        top='#cfdbe6', top_hi='#e4edf5', top_kind='nightshirt', sleeve='long',
        piping='#9bb0c4', bottom='#8b99a8', bottom_hi='#a3b2c2',
        shoe='#8b99a8', shoe_sole='#6d7b8a', shoe_kind='bare', glasses=False, opacity=0.82
    ),
    'teal_dress': dict(
        skin='#9b6a4c', hair='#2d1f18', hair_style='afro',
        top='#1b5056', top_hi='#276870', top_kind='floral_bodice', sleeve='sleeveless',
        piping='#dec078', bottom='#1b5056', bottom_hi='#276870',
        shoe='#222026', shoe_sole='#3b2d22', shoe_kind='flat', glasses=False, floral=True
    ),
    'mother_cardigan': dict(
        skin='#9b6a4c', hair='#2d1f18', hair_style='afro',
        top='#6e6a66', top_hi='#87827d', top_kind='cardigan', sleeve='long',
        piping='#4a6670', bottom='#4a6670', bottom_hi='#5d7d88',
        shoe='#7a5c48', shoe_sole='#3e2e24', shoe_kind='slipper', glasses=False
    ),
    'window_woman_dress': dict(
        skin='#9b6a4c', hair='#2d1f18', hair_style='afro',
        top='#b8322a', top_hi='#d4463d', top_kind='summer_dress', sleeve='sleeveless',
        piping='#f0b868', bottom='#b8322a', bottom_hi='#d4463d',
        shoe='#3a2420', shoe_sole='#241614', shoe_kind='flat', glasses=False
    ),
    'parent_coat': dict(
        skin='#845c44', hair='#221d1a', hair_style='fade_beard',
        top='#4a3c32', top_hi='#615043', top_kind='overcoat_scarf', sleeve='long',
        piping='#8c3b2b', bottom='#2b3038', bottom_hi='#3a404a',
        shoe='#241e1a', shoe_sole='#161210', shoe_kind='boot', glasses=False
    ),
    'elder_father_coat': dict(
        skin='#7e5840', hair='#6e6c68', hair_style='cap_beard',
        top='#585c62', top_hi='#70757c', top_kind='overcoat', sleeve='long',
        piping='#3c4046', bottom='#34373c', bottom_hi='#454950',
        shoe='#1e1c1a', shoe_sole='#12100e', shoe_kind='boot', glasses=False
    ),
    'ancestor_robe_indigo_gold': dict(
        skin='#6e4934', hair='#1c1715', hair_style='crown_wrap',
        top='#1f2d5a', top_hi='#2d407a', top_kind='kente_robe', sleeve='long',
        piping='#e0a838', bottom='#1f2d5a', bottom_hi='#2d407a',
        shoe='#8c6238', shoe_sole='#4a321a', shoe_kind='sandal', glasses=False
    ),
    'ancestor_elder_white_silver': dict(
        skin='#6e4934', hair='#d8d6d0', hair_style='white_headwrap',
        top='#eae6dc', top_hi='#f7f5f0', top_kind='silver_robe', sleeve='long',
        piping='#a8b0bc', bottom='#eae6dc', bottom_hi='#f7f5f0',
        shoe='#b8bcc4', shoe_sole='#60646a', shoe_kind='sandal', glasses=False
    ),
    'atlantis_traveler': dict(
        skin='#825a42', hair='#1e1916', hair_style='short_curls',
        top='#5c5042', top_hi='#736554', top_kind='travel_coat', sleeve='long',
        piping='#9c7a4c', bottom='#383c42', bottom_hi='#4a4f56',
        shoe='#3a2c22', shoe_sole='#221a14', shoe_kind='boot', glasses=False
    ),
    'atlantis_citizen': dict(
        skin='#825a42', hair='#1e1916', hair_style='braids',
        top='#285862', top_hi='#387480', top_kind='neon_linen', sleeve='long',
        piping='#48e0d0', bottom='#223c46', bottom_hi='#30525e',
        shoe='#886a3a', shoe_sole='#4a381e', shoe_kind='sandal', glasses=False
    ),
    'atlantis_gatekeeper': dict(
        skin='#78523c', hair='#1c1816', hair_style='fade_beard',
        top='#263448', top_hi='#364862', top_kind='gatekeeper', sleeve='long',
        piping='#d8a842', bottom='#1e2836', bottom_hi='#2b384a',
        shoe='#1c1e22', shoe_sole='#121416', shoe_kind='boot', glasses=False
    ),
    'poet_elder_coat': dict(
        skin='#825c46', hair='#7a7672', hair_style='elder_beard',
        top='#4e443a', top_hi='#66594c', top_kind='patched_coat', sleeve='long',
        piping='#8a6e48', bottom='#322e2a', bottom_hi='#443f3a',
        shoe='#2a221c', shoe_sole='#181410', shoe_kind='boot', glasses=False
    ),
    'vintage_party': dict(
        skin='#845c44', hair='#1c1816', hair_style='vintage_part',
        top='#2c2628', top_hi='#3e3638', top_kind='suit_tie', sleeve='long',
        piping='#c8a868', bottom='#242022', bottom_hi='#342e30',
        shoe='#1a1618', shoe_sole='#100e10', shoe_kind='dress_shoe', glasses=False
    ),
    'dj_cyber': dict(
        skin='#845c44', hair='#1c1816', hair_style='cap_headphones',
        top='#22242c', top_hi='#323540', top_kind='dj_bomber', sleeve='long',
        piping='#38d8f0', bottom='#1e2028', bottom_hi='#2c2f3a',
        shoe='#282c34', shoe_sole='#38d8f0', shoe_kind='sneaker', glasses=False
    ),
    'party_guest': dict(
        skin='#886048', hair='#1e1916', hair_style='short_curls',
        top='#683244', top_hi='#824056', top_kind='jacket_shirt', sleeve='long',
        piping='#d09858', bottom='#262830', bottom_hi='#363944',
        shoe='#221e20', shoe_sole='#141214', shoe_kind='boot', glasses=False
    ),
    'club_dress': dict(
        skin='#92664c', hair='#241c18', hair_style='afro',
        top='#7a2852', top_hi='#9c366a', top_kind='sequin_dress', sleeve='sleeveless',
        piping='#e8b868', bottom='#7a2852', bottom_hi='#9c366a',
        shoe='#241820', shoe_sole='#160e14', shoe_kind='flat', glasses=False
    ),
    'club_shirt': dict(
        skin='#845c44', hair='#1c1816', hair_style='fade_beard',
        top='#8c4828', top_hi='#a85a34', top_kind='silk_shirt', sleeve='long',
        piping='#d89c4a', bottom='#222428', bottom_hi='#32353b',
        shoe='#1c1a18', shoe_sole='#12100e', shoe_kind='chelsea', glasses=False
    ),
    'club_jacket': dict(
        skin='#845c44', hair='#1c1816', hair_style='short_curls',
        top='#282226', top_hi='#3c3439', top_kind='leather_jacket', sleeve='long',
        piping='#a89e94', bottom='#1e1c20', bottom_hi='#2d2a30',
        shoe='#181618', shoe_sole='#100e10', shoe_kind='boot', glasses=False
    ),
    'angel_white_robe': dict(
        skin='#865e46', hair='#221c18', hair_style='short_curls',
        top='#eeeae0', top_hi='#faf8f2', top_kind='angel_robe', sleeve='long',
        piping='#d4be7a', bottom='#eeeae0', bottom_hi='#faf8f2',
        shoe='#865e46', shoe_sole='#6a4834', shoe_kind='bare', glasses=False, wings=True
    ),
    'brother_casual': dict(
        skin='#845c44', hair='#1c1816', hair_style='fade_beard',
        top='#7a3228', top_hi='#944034', top_kind='hoodie', sleeve='long',
        piping='#d8d0c4', bottom='#364860', bottom_hi='#485e7a',
        shoe='#e0dcd2', shoe_sole='#58544e', shoe_kind='sneaker', glasses=False
    ),
    'friend_casual': dict(
        skin='#886048', hair='#1e1916', hair_style='short_curls',
        top='#3a4c3e', top_hi='#4c6250', top_kind='jacket_shirt', sleeve='long',
        piping='#c8b89a', bottom='#8c7658', bottom_hi='#a28a6a',
        shoe='#382c22', shoe_sole='#221a14', shoe_kind='sneaker', glasses=False
    ),
    'elder_memory_silhouette': dict(
        skin='#b8b2a6', hair='#969084', hair_style='elder_beard',
        top='#d4cec0', top_hi='#e6e2d6', top_kind='overcoat', sleeve='long',
        piping='#a69e8e', bottom='#c2bcb0', bottom_hi='#d4cec2',
        shoe='#9e988c', shoe_sole='#827c70', shoe_kind='dress_shoe', glasses=False, opacity=0.86
    ),
    'elder_robe_pearls': dict(
        skin='#7e563e', hair='#888480', hair_style='white_headwrap',
        top='#4a2c48', top_hi='#623c60', top_kind='church_robe', sleeve='long',
        piping='#f0ece2', bottom='#4a2c48', bottom_hi='#623c60',
        shoe='#241a22', shoe_sole='#161014', shoe_kind='flat', glasses=False
    ),
    'couple_summer_casual': dict(
        skin='#886048', hair='#201a16', hair_style='short_curls',
        top='#d8cbb8', top_hi='#eae0d0', top_kind='silk_shirt', sleeve='short',
        piping='#8c7a64', bottom='#465868', bottom_hi='#586e80',
        shoe='#6e5038', shoe_sole='#3c2a1c', shoe_kind='sandal', glasses=False
    ),
    'street_clothes': dict(
        skin='#845c44', hair='#1c1816', hair_style='short_curls',
        top='#3c444e', top_hi='#4e5864', top_kind='jacket_shirt', sleeve='long',
        piping='#9aa4b0', bottom='#282c32', bottom_hi='#363b42',
        shoe='#222428', shoe_sole='#d8d4cc', shoe_kind='sneaker', glasses=False
    ),
    'broll_everyday': dict(
        skin='#865e46', hair='#1e1916', hair_style='short_curls',
        top='#4a5868', top_hi='#5e7082', top_kind='jacket_shirt', sleeve='long',
        piping='#b8c4d0', bottom='#2c323a', bottom_hi='#3c444e',
        shoe='#242220', shoe_sole='#484440', shoe_kind='sneaker', glasses=False
    ),
    'crash_yellow': dict(
        skin='#ffd23f', hair='#ffd23f', hair_style='bola_antenna',
        top='#ffd23f', top_hi='#ffe070', top_kind='dummy_torso', sleeve='stick',
        piping='#181a1e', bottom='#181a1e', bottom_hi='#2c3036',
        shoe='#e3261f', shoe_sole='#181a1e', shoe_kind='dummy_shoe', glasses=False, dummy='bola'
    ),
    'crash_teal': dict(
        skin='#19c9ae', hair='#19c9ae', hair_style='shim_fin',
        top='#19c9ae', top_hi='#48dec6', top_kind='dummy_torso', sleeve='stick',
        piping='#181a1e', bottom='#181a1e', bottom_hi='#2c3036',
        shoe='#2b78e4', shoe_sole='#181a1e', shoe_kind='dummy_shoe', glasses=False, dummy='shim'
    ),
    'crash_dot': dict(
        skin='#ff7a6b', hair='#ff7a6b', hair_style='dot_bow',
        top='#ff7a6b', top_hi='#ff988c', top_kind='dummy_torso', sleeve='stick',
        piping='#181a1e', bottom='#181a1e', bottom_hi='#2c3036',
        shoe='#1c1e22', shoe_sole='#0e1012', shoe_kind='dummy_shoe', glasses=False, dummy='dot'
    ),
}


def decorate_torso_sprite(sp_im, view, spec):
    """Add costume-specific crafted accents onto a recolored painted torso sprite."""
    im = sp_im.copy()
    d = ImageDraw.Draw(im)
    w, h = im.size
    cx = w * (0.56 if view == 'threequarter' else 0.50)
    tk = spec['top_kind']
    pip = hex_rgb(spec['piping']) + (255,) if spec.get('piping') else None
    ink = (22, 18, 16, 255)

    if view not in ('back', 'threequarter_back'):
        if tk == 'kente_robe' and pip:
            d.rectangle([cx - 14, 18, cx + 14, h - 18], fill=pip, outline=ink, width=2)
            for yy in np.linspace(32, h - 32, 8):
                d.line([(cx - 14, float(yy)), (cx + 14, float(yy))], fill=(185, 42, 32, 255), width=3)
        elif tk == 'church_robe' and pip:
            for a in np.linspace(20, 160, 11):
                rad = math.radians(a)
                px_ = cx + math.cos(rad) * w * 0.24
                py_ = 28 + math.sin(rad) * 24
                d.ellipse([px_ - 5, py_ - 5, px_ + 5, py_ + 5], fill=pip, outline=ink, width=1)
        elif tk == 'gatekeeper' and pip:
            d.polygon([(cx + 18, 64), (cx + 34, 72), (cx + 28, 92), (cx + 12, 92)], fill=pip, outline=ink, width=2)
        elif tk == 'striped_tee' and pip:
            for yy in np.linspace(48, h - 32, 6):
                d.line([(28, float(yy)), (w - 28, float(yy))], fill=pip[:3] + (195,), width=6)
        elif tk == 'flannel_pj' and pip:
            for yy in np.linspace(42, h - 28, 6):
                d.line([(24, float(yy)), (w - 24, float(yy))], fill=pip[:3] + (145,), width=2)
        elif tk == 'dummy_torso':
            draw_crash_target(d, cx, h * 0.34, min(18.0, w * 0.16))
    return im


def paste_centered_fit(layer, sprite, box_xywh, opacity=1.0):
    """Resize `sprite` proportionally to fit inside `box_xywh=(x, y, w, h)` and alpha_composite onto `layer`."""
    if sprite is None:
        return (0, 0, 10, 10)
    x, y, w, h = box_xywh
    sp = sprite.copy()
    if opacity < 0.999:
        arr = np.asarray(sp, dtype=np.float32).copy()
        arr[..., 3] = np.clip(arr[..., 3] * opacity, 0, 255)
        sp = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    sw, sh = sp.size
    if sw <= 0 or sh <= 0:
        return (int(x), int(y), int(x + w), int(y + h))
    sc = min(float(w) / sw, float(h) / sh)
    nw, nh = max(4, int(round(sw * sc))), max(4, int(round(sh * sc)))
    sp_r = sp.resize((nw, nh), Image.LANCZOS)
    px = int(round(x + (w - nw) * 0.5))
    py = int(round(y + (h - nh) * 0.5))
    layer.alpha_composite(sp_r, (px, py))
    return (px, py, px + nw, py + nh)


def crop_part_rgba(layer_rgba, bbox, sockets_sheet, out_path, pad=8):
    x0, y0, x1, y1 = [int(round(v)) for v in bbox]
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(layer_rgba.width, x1 + pad), min(layer_rgba.height, y1 + pad)
    sub = layer_rgba.crop((x0, y0, x1, y1))
    ab = sub.getbbox()
    if ab:
        ax0, ay0, ax1, ay1 = ab
        ax0, ay0 = max(0, ax0 - 4), max(0, ay0 - 4)
        ax1, ay1 = min(sub.width, ax1 + 4), min(sub.height, ay1 + 4)
        sub = sub.crop((ax0, ay0, ax1, ay1))
        ox, oy = x0 + ax0, y0 + ay0
    else:
        ox, oy = x0, y0
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sub.save(out_path)
    local_socks = {}
    for k, v in (sockets_sheet or {}).items():
        if isinstance(v, (list, tuple)) and len(v) == 2:
            local_socks[k] = [round(float(v[0]) - ox, 1), round(float(v[1]) - oy, 1)]
    return {'file': out_path, 'size': [sub.width, sub.height], 'sockets': local_socks}


# ---------------------------------------------------------------------------
# 1. Costume Sheet Renderer + Separate Part Slicer (Using Real Painted Bank)
# ---------------------------------------------------------------------------
def render_costume_sheet(cid, build_id, cos_name, sheet_name, spec, parts_dir):
    C = K.CHARS[build_id]
    kind = sheet_name.split('.')[0]
    layer = Image.new('RGBA', (SHEET_W, SHEET_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sliced_parts = []
    op = spec.get('opacity', 1.0)

    if kind == 'body':
        view = sheet_name.split('.')[1]
        geo = 'profile' if view == 'profile' else 'front'
        sh, J = K.shapes(build_id, geo)
        pxcm = 6.0 if build_id != 'dotd' else 9.0
        im_bg, d_bg = K.sheet_frame(f'{cid}.{cos_name}.body.{view}',
                                    f"{C['label']} ({cos_name.replace('_', ' ')}) · painted cardboard body cards, {view} view", pxcm)
        cells = [n for n, _, _ in sh if n not in ('head', 'hair', 'neck') and not (geo == 'profile' and n.endswith('.R'))]
        order = ['torso', 'pelvis', 'uarm.L', 'farm.L', 'hand.L', 'uarm.R', 'farm.R', 'hand.R', 'thigh.L', 'shin.L', 'foot.L', 'thigh.R', 'shin.R', 'foot.R']
        cells = [c for c in order if c in cells]
        x, y, rowh = 60, 120, 0
        by = {n: (p, js) for n, p, js in sh}
        cell_meta = []

        for name in cells:
            poly, (ja, jb) = by[name]
            P = np.array(poly)
            A = np.array(J[ja]) if ja in J else P.mean(0)
            B = np.array(J[jb]) if jb in J else P.mean(0)
            if name == 'torso':
                A, B = np.array(J['neck']), np.array([J['neck'][0], J['hipL'][1]])
            if name == 'pelvis':
                A = np.array([0.0, C['J']['hipL'][1] + 6])
                B = np.array([0.0, C['J']['kneeL'][1] + 4])
            v = B - A
            th = -math.atan2(v[0], -v[1]) if name not in ('foot.L', 'foot.R', 'torso', 'pelvis') else 0
            R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
            Q = (P - A) @ R.T
            Bq = (B - A) @ R.T
            mn, mx = Q.min(0), Q.max(0)
            w, h = (mx[0] - mn[0]) * pxcm, (mx[1] - mn[1]) * pxcm
            if x + w + 60 > SHEET_W:
                x, y, rowh = 60, y + rowh + 70, 0
            org = np.array([x - mn[0] * pxcm, y + mx[1] * pxcm])
            T = lambda q: (float(org[0] + q[0] * pxcm), float(org[1] - q[1] * pxcm))
            a_px, b_px = T((0, 0)), T(Bq)

            extra = {}
            if name in ('torso', 'pelvis'):
                for k in (('shoulderL', 'shoulderR', 'hipL', 'hipR') if name == 'torso' else ('hipL', 'hipR')):
                    if geo == 'profile' and k.endswith('R'):
                        continue
                    if C['pelvis'] == 'skirt' and name == 'torso' and k.startswith('hip'):
                        continue
                    q = T((np.array(J[k]) - A) @ R.T)
                    extra[k] = [round(q[0], 1), round(q[1], 1)]

            sp = PB.get_painted_body_part(name, view, cid, build_id, spec)
            if name == 'torso' and sp is not None:
                sp = decorate_torso_sprite(sp, view, spec)
            pbox = paste_centered_fit(layer, sp, (x - 6, y - 6, w + 12, h + 12), op)

            # Ensure socket brads are crisp at exact A/B coordinates
            draw_brad(d, a_px, r=6.0, eyelet=(name.startswith('hand')))
            if not name.startswith('foot'):
                draw_brad(d, b_px, r=5.5, eyelet=(name.startswith(('farm', 'shin'))))
            for k, q in extra.items():
                draw_brad(d, q, r=5.8)

            d_bg.text((x, y + h + 14), f"{K.NUM.get(name, '')}  {name}", font=font(FONTB, 16), fill=INK)
            d_bg.text((x, y + h + 34), f"{np.linalg.norm(B - A):.0f} cm A-B", font=font(MONO, 13), fill=(110, 100, 90))
            socks = {'A': a_px, 'B': b_px, **extra}
            cell_meta.append((f'body.{view}.{name}', pbox, socks))
            x += w + 70
            rowh = max(rowh, h + 40)

        # Angel wings on their own cards if spec['wings']
        if spec.get('wings') and view in ('front', 'back'):
            for wi, side in enumerate(('L', 'R')):
                wx0, wy0 = 1380 + wi * 300, 560
                wpts = [(wx0 + 40, wy0 + 40), (wx0 + 220, wy0 - 30), (wx0 + 250, wy0 + 180),
                        (wx0 + 160, wy0 + 380), (wx0 + 40, wy0 + 310)]
                PB._draw_bevel_poly(d, wpts, (245, 242, 234), rim=4.0, ink_w=2)
                for fy in range(60, 320, 42):
                    d.line([(wx0 + 55, wy0 + fy), (wx0 + 215, wy0 + fy + 20)], fill=(120, 114, 104, 220), width=2)
                wa = (wx0 + 58, wy0 + 62)
                draw_brad(d, wa, r=6.5)
                d_bg.text((wx0 + 30, wy0 + 392), f'wing.{side}', font=font(FONTB, 16), fill=INK)
                cell_meta.append((f'body.{view}.wing.{side}', (wx0, wy0 - 40, wx0 + 265, wy0 + 390), {'A': wa}))

        for pname, bbox, socks in cell_meta:
            pinfo = crop_part_rgba(layer, bbox, socks, os.path.join(parts_dir, f'{pname}.png'))
            sliced_parts.append({'id': pname, **pinfo})

    elif kind == 'heads':
        r = C['J']['crown'][1] - C['J']['head'][1]
        pxcm = 12.0 if build_id != 'dotd' else 11.0
        im_bg, d_bg = K.sheet_frame(f'{cid}.{cos_name}.heads',
                                    f"{C['label']} ({cos_name.replace('_', ' ')}) · painted blank head plates (features plug in)", pxcm)
        cw = (SHEET_W - 120) / 5
        cell_meta = []
        views = ['threequarter_back', 'back'] if cid == 'ex' else K.HEAD_VIEWS
        for i, v in enumerate(K.HEAD_VIEWS):
            cx, cy = 60 + cw * i + cw / 2, 560
            rx, ry = r * (0.8 if build_id != 'dotd' else 1) * pxcm * (1.05 if 'profile' in v else 1), r * 1.08 * pxcm
            neck = (cx, cy + ry + 6 * pxcm)
            crown = (cx, cy - ry)
            d_bg.text((cx - cw / 2 + 16, 230), v + (' (never seen)' if v not in views else ''), font=font(FONTB, 18), fill=INK)
            if v not in views:
                continue
            sp_head = PB.get_painted_head(cid, build_id, spec, v, blank=True)
            bw, bh = rx * 2.35, (neck[1] - crown[1]) * 1.16
            pbox = paste_centered_fit(layer, sp_head, (cx - bw * 0.5, crown[1] - 24, bw, bh), op)
            draw_brad(d, neck, r=6.5)

            turn = {'front': 0, 'threequarter': .3, 'profile': .5, 'threequarter_back': .6, 'back': None}[v]
            socks = {'A': neck, 'neck': neck, 'crown': crown}
            if turn is not None:
                ex = cx + turn * rx * 1.2
                socks['eyes'] = (ex, cy - r * .15 * pxcm)
                socks['brows'] = (ex, cy - r * .38 * pxcm)
                socks['mouth'] = (ex + (turn * 6 if turn else 0), cy + r * .45 * pxcm)
            cell_meta.append((f'head.{v}', pbox, socks))

        for pname, bbox, socks in cell_meta:
            pinfo = crop_part_rgba(layer, bbox, socks, os.path.join(parts_dir, f'{pname}.png'))
            sliced_parts.append({'id': pname, **pinfo})

    elif kind == 'face':
        view = sheet_name.split('.')[1]
        r = C['J']['crown'][1] - C['J']['head'][1]
        pxcm = 14.0 if build_id != 'dotd' else 12.0
        im_bg, d_bg = K.sheet_frame(f'{cid}.{cos_name}.face.{view}',
                                    f"{C['label']} ({cos_name.replace('_', ' ')}) · painted face plug-in cards, {view}", pxcm)
        hc = (60 + r * 1.2 * pxcm, 140 + r * 1.25 * pxcm)
        rx, ry = r * (0.78 if build_id != 'dotd' else 1) * pxcm * (1.05 if view == 'profile' else 1.0), r * 1.08 * pxcm
        neck = (hc[0], hc[1] + ry + 4 * pxcm)
        crown = (hc[0], hc[1] - ry)
        fx = 0 if view == 'front' else r * .45 * pxcm
        anchors = {'eyes': (hc[0] + fx, hc[1] - r * .15 * pxcm), 'brows': (hc[0] + fx, hc[1] - r * .38 * pxcm),
                   'mouth': (hc[0] + fx, hc[1] + r * .45 * pxcm), 'neck': neck, 'crown': crown}

        sp_head = PB.get_painted_head(cid, build_id, spec, view, blank=True)
        bw, bh = rx * 2.35, (neck[1] - crown[1]) * 1.15
        pbox_h = paste_centered_fit(layer, sp_head, (hc[0] - bw * 0.5, crown[1] - 20, bw, bh), op)
        draw_brad(d, neck, r=6.5)
        d_bg.text((hc[0] - rx, neck[1] + 24), '1  head plate (blank)', font=font(FONTB, 16), fill=INK)
        cell_meta = [(f'face.{view}.plate', pbox_h, anchors)]

        if spec.get('glasses'):
            gx_c, gy_c = hc[0], neck[1] + 115
            sp_gl = PB.get_painted_sunglasses(view)
            pbox_g = paste_centered_fit(layer, sp_gl, (gx_c - 105, gy_c - 42, 210, 84), op)
            d_bg.text((hc[0] - rx, gy_c + 44), '19  sunglasses (plug-in card)', font=font(FONTB, 15), fill=INK)
            cell_meta.append((f'face.{view}.glasses', pbox_g, {'A': (gx_c, gy_c)}))

        gx0 = hc[0] + rx + 80
        rows = [('eyes', K.EYES, 8), ('brows', K.BROWS, 6), ('mouth', K.MOUTHS, 12)]
        y = 130
        for slot, names, n in rows:
            cols = 6 if n > 6 else n
            cw = (SHEET_W - gx0 - 40) / cols
            chh = 120 if slot != 'mouth' else 110
            d_bg.text((gx0, y - 6), f"{K.NUM[slot]}  {slot}", font=font(FONTB, 16), fill=K.ACCENT[build_id])
            y += 18
            for i, nm in enumerate(names):
                cx, cy = gx0 + (i % cols) * cw + cw / 2, y + (i // cols) * chh + chh / 2
                d_bg.rectangle([cx - cw / 2 + 4, cy - chh / 2 + 4, cx + cw / 2 - 4, cy + chh / 2 - 4], outline=(220, 214, 204), width=1)
                sp_feat = PB.get_painted_face_feature(slot, nm, view, spec)
                pbox_f = paste_centered_fit(layer, sp_feat, (cx - cw * 0.42, cy - chh * 0.28 + 10, cw * 0.84, chh * 0.64), op)
                d_bg.text((cx - cw / 2 + 10, cy - chh / 2 + 8), nm, font=font(MONO, 13), fill=INK)
                cell_meta.append((f'face.{view}.{slot}.{nm}', pbox_f, {'A': (cx, cy + 8)}))
            y += chh * math.ceil(n / cols) + 16

        for pname, bbox, socks in cell_meta:
            pinfo = crop_part_rgba(layer, bbox, socks, os.path.join(parts_dir, f'{pname}.png'), pad=2)
            sliced_parts.append({'id': pname, **pinfo})

    elif kind == 'hands':
        pxcm = 11.0 if build_id != 'dotd' else 16.0
        L = float(np.linalg.norm(np.array(C['J']['tipL']) - np.array(C['J']['wristL'])))
        im_bg, d_bg = K.sheet_frame(f'{cid}.{cos_name}.hands.R',
                                    f"{C['label']} ({cos_name.replace('_', ' ')}) · painted right hand cards, 12 shapes x back / palm", pxcm)
        cw, ch = (SHEET_W - 120) / 6, (SHEET_H - 150) / 4
        cell_meta = []
        for i, shape in enumerate(K.HAND_SHAPES):
            for k, face in enumerate(('back', 'palm')):
                col, row = i % 6, (i // 6) * 2 + k
                x0, y0 = 60 + col * cw, 120 + row * ch
                d_bg.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + ch - 4], outline=(220, 214, 204), width=1)
                a = (x0 + 42, y0 + ch * 0.56)
                b = (a[0] + L * 0.55 * pxcm, a[1])
                sp_h = PB.get_painted_hand(shape, face, spec)
                pbox_h = paste_centered_fit(layer, sp_h, (x0 + 18, y0 + 34, cw - 36, ch - 46), op)
                draw_brad(d, a, r=5.5, eyelet=True)
                d_bg.text((x0 + 12, y0 + 10), f'{shape} · {face}', font=font(FONTB, 14), fill=INK)
                cell_meta.append((f'hand.R.{shape}.{face}', pbox_h, {'A': a, 'B': b}))

        for pname, bbox, socks in cell_meta:
            pinfo = crop_part_rgba(layer, bbox, socks, os.path.join(parts_dir, f'{pname}.png'), pad=2)
            sliced_parts.append({'id': pname, **pinfo})

    elif kind == 'feet':
        L = C['height'] * 0.145
        pxcm = 11.0 if build_id != 'dotd' else 16.0
        im_bg, d_bg = K.sheet_frame(f'{cid}.{cos_name}.feet.R',
                                    f"{C['label']} ({cos_name.replace('_', ' ')}) · painted right shoe/boot in 6 states", pxcm)
        cw = (SHEET_W - 120) / 3
        cell_meta = []
        for i, v in enumerate(K.FEET):
            x0, y0 = 60 + cw * (i % 3), 160 + (i // 3) * 470
            floor = y0 + 380
            d_bg.line([(x0 + 20, floor), (x0 + cw - 20, floor)], fill=(200, 192, 180), width=2)
            ank = (x0 + 80 + 6 * pxcm, floor - 9 * pxcm)
            heel, toe = (ank[0] - 6 * pxcm, floor), (ank[0] + (L - 6) * pxcm, floor)
            if v in ('front', 'back'):
                ank = (x0 + cw / 2, floor - 10 * pxcm)
                heel, toe = (ank[0] - 4.5 * pxcm, floor), (ank[0] + 4.5 * pxcm, floor)
            sp_ft = PB.get_painted_body_part('foot.R', v, cid, build_id, spec)
            pbox_ft = paste_centered_fit(layer, sp_ft, (x0 + 70, y0 + 60, cw - 140, 325), op)
            draw_brad(d, ank, r=6.0)
            d_bg.text((x0 + 20, y0), v.replace('_', ' '), font=font(FONTB, 18), fill=INK)
            cell_meta.append((f'foot.R.{v}', pbox_ft, {'A': ank, 'toe': toe, 'heel': heel}))

        for pname, bbox, socks in cell_meta:
            pinfo = crop_part_rgba(layer, bbox, socks, os.path.join(parts_dir, f'{pname}.png'), pad=2)
            sliced_parts.append({'id': pname, **pinfo})

    elif kind == 'replacements':
        pxcm = 4.6 if build_id != 'dotd' else 7.0
        im_bg, d_bg = K.sheet_frame(f'{cid}.{cos_name}.replacements',
                                    f"{C['label']} ({cos_name.replace('_', ' ')}) · painted whole-body replacement pose cards", pxcm)
        poses = [
            ('sit', 'sitting on a chair, side view'),
            ('kneel', 'kneeling on one knee'),
            ('lie_back', 'lying on the back'),
            ('lie_side', 'lying on the side'),
            ('crouch', 'deep crouch'),
            ('fall', 'falling backwards'),
        ]
        cw = (SHEET_W - 120) / 3
        cell_meta = []
        for i, (pslug, plabel) in enumerate(poses):
            x0, y0 = 60 + cw * (i % 3), 130 + (i // 3) * 500
            floor = y0 + 460
            d_bg.rectangle([x0 + 6, y0 + 6, x0 + cw - 6, floor + 20], outline=(222, 216, 206), width=1)
            d_bg.line([(x0 + 20, floor), (x0 + cw - 20, floor)], fill=(200, 192, 180), width=2)
            hip_y = {'lying on the back': 14, 'lying on the side': 16}.get(plabel, 50 if 'sitting' in plabel else 70 if 'kneeling' in plabel else 45 if 'crouch' in plabel else 60)
            hip_px = (x0 + cw / 2, floor - hip_y * pxcm)
            sp_rep = PB.get_painted_replacement_pose(pslug, 'threequarter', cid, build_id, spec)
            pbox_r = paste_centered_fit(layer, sp_rep, (x0 + 40, y0 + 48, cw - 80, 412), op)
            draw_brad(d, hip_px, r=6.5)
            d_bg.text((x0 + 20, y0 + 16), plabel, font=font(FONTB, 18), fill=INK)
            cell_meta.append((f'replacement.{pslug}', pbox_r, {'A': hip_px, 'hip': hip_px}))

        for pname, bbox, socks in cell_meta:
            pinfo = crop_part_rgba(layer, bbox, socks, os.path.join(parts_dir, f'{pname}.png'), pad=2)
            sliced_parts.append({'id': pname, **pinfo})

    im_sheet = im_bg.convert('RGBA')
    im_sheet.alpha_composite(layer)
    return im_sheet.convert('RGB'), sliced_parts


# ---------------------------------------------------------------------------
# 2. Assembled Multi-Pose Renderer Using Real Hand-Painted Parts
# ---------------------------------------------------------------------------
POSE_ANGLES = {
    'stand_front': ('front', 'neutral', {'uL': -10, 'fL': -6, 'uR': 10, 'fR': 6, 'tL': -2, 'sL': 0, 'tR': 2, 'sR': 0}),
    'stand_threequarter': ('threequarter', 'small_smile', {'uL': -18, 'fL': 24, 'uR': 16, 'fR': -18, 'tL': -5, 'sL': 3, 'tR': 6, 'sR': -4}),
    'stand_profile': ('profile', 'neutral', {'uL': -16, 'fL': 28, 'uR': 14, 'fR': 12, 'tL': -12, 'sL': 14, 'tR': 12, 'sR': -6}),
    'stand_back': ('back', 'neutral', {'uL': -10, 'fL': -6, 'uR': 10, 'fR': 6, 'tL': -3, 'sL': 0, 'tR': 3, 'sR': 0}),
    'walk': ('threequarter', 'listening', {'uL': -28, 'fL': 22, 'uR': 26, 'fR': 18, 'tL': -22, 'sL': 16, 'tR': 20, 'sR': -18}),
    'reach': ('front', 'singing', {'uL': -125, 'fL': -18, 'uR': 32, 'fR': 18, 'tL': -8, 'sL': 4, 'tR': 8, 'sR': -4}),
}


def _paste_rot_part(canvas, sprite, p0, p1, w_target):
    """Scale and rotate a painted vertical limb sprite so its top-to-bottom axis spans p0 -> p1."""
    if sprite is None:
        return
    dx, dy = float(p1[0] - p0[0]), float(p1[1] - p0[1])
    L = max(12.0, math.hypot(dx, dy))
    ang_deg = -math.degrees(math.atan2(dx, dy))
    sp = sprite.resize((max(8, int(round(w_target))), max(12, int(round(L * 1.18)))), Image.LANCZOS)
    rot = sp.rotate(ang_deg, resample=Image.BICUBIC, expand=True)
    cx, cy = (p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5
    canvas.alpha_composite(rot, (int(round(cx - rot.width * 0.5)), int(round(cy - rot.height * 0.5))))


def render_assembled_pose(cid, build_id, cos_name, pose_name, spec, out_png, w=440, h=580):
    """Render an assembled cardboard puppet pose using the real painted head, torso, skirt, limbs, boots, and hands."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, floor_y = w * 0.5, h - 38
    op = spec.get('opacity', 1.0)

    if pose_name in ('sit', 'kneel', 'crouch', 'fall', 'lie_back', 'lie_side'):
        rep = PB.get_painted_replacement_pose(pose_name, 'threequarter', cid, build_id, spec)
        pbox = paste_centered_fit(im, rep, (55, 145, w - 110, h - 185), op)
        hview = 'threequarter_back' if cid == 'ex' else ('profile' if pose_name in ('sit', 'fall', 'lie_back') else 'threequarter')
        head = PB.get_painted_head(cid, build_id, spec, hview, blank=False, expr='neutral')
        if spec.get('glasses') and cid != 'ex' and hview not in ('back', 'threequarter_back'):
            gl = PB.get_painted_sunglasses('front' if hview != 'profile' else 'profile')
            gl_s = gl.resize((int(head.width * 0.72), int(head.height * 0.22)), Image.LANCZOS)
            head.alpha_composite(gl_s, (int(head.width * 0.18), int(head.height * 0.34)))
        hx = (pbox[0] + pbox[2]) * 0.5 - 48
        hy = max(14, pbox[1] - 96)
        if 'lie' in pose_name:
            hx, hy = max(16, pbox[0] - 45), pbox[1] + 15
        paste_centered_fit(im, head, (hx, hy, 108, 128), op)
    else:
        view, expr, ang = POSE_ANGLES.get(pose_name, POSE_ANGLES['stand_front'])
        if cid == 'ex':
            view = 'back' if 'front' in view or 'back' in view else 'threequarter_back'
        C = K.CHARS[build_id]
        sc = 0.82 if C['height'] < 140 else 1.0
        torso_w, torso_h = int(124 * sc), int(168 * sc)
        neck = (cx, floor_y - 355 * sc)
        shL = (cx - torso_w * 0.38, neck[1] + 24 * sc)
        shR = (cx + torso_w * 0.38, neck[1] + 24 * sc)
        hipL = (cx - torso_w * 0.26, neck[1] + torso_h - 14 * sc)
        hipR = (cx + torso_w * 0.26, neck[1] + torso_h - 14 * sc)

        def j_end(p0, length, deg):
            rad = math.radians(deg)
            return (p0[0] + math.sin(rad) * length, p0[1] + math.cos(rad) * length)

        torso = decorate_torso_sprite(PB.get_painted_body_part('torso', view, cid, build_id, spec), view, spec)
        uarm = PB.get_painted_body_part('uarm.L', view, cid, build_id, spec)
        farm = PB.get_painted_body_part('farm.L', view, cid, build_id, spec)
        thigh = PB.get_painted_body_part('thigh.L', view, cid, build_id, spec)
        shin = PB.get_painted_body_part('shin.L', view, cid, build_id, spec)
        boot = PB.get_painted_body_part('foot.R', 'front' if view in ('front', 'back') else 'profile_flat', cid, build_id, spec)
        hand = PB.get_painted_hand('open' if pose_name == 'reach' else 'relaxed', 'back', spec)

        # Far leg & arm
        kR = j_end(hipR, 88 * sc, ang['tR'])
        aR = j_end(kR, 86 * sc, ang['tR'] + ang['sR'])
        _paste_rot_part(im, thigh, hipR, kR, 42 * sc)
        _paste_rot_part(im, shin, kR, aR, 36 * sc)
        paste_centered_fit(im, boot, (aR[0] - 24 * sc, aR[1] - 12 * sc, 64 * sc, 48 * sc), op)

        eR = j_end(shR, 68 * sc, ang['uR'])
        wR = j_end(eR, 62 * sc, ang['uR'] + ang['fR'])
        _paste_rot_part(im, uarm, shR, eR, 30 * sc)
        _paste_rot_part(im, farm, eR, wR, 26 * sc)
        paste_centered_fit(im, hand, (wR[0] - 18 * sc, wR[1] - 8 * sc, 38 * sc, 38 * sc), op)

        # Angel wings behind torso
        if spec.get('wings'):
            for sgn in (-1, 1):
                wpts = [(cx + sgn * 18, neck[1] + 18), (cx + sgn * 135, neck[1] - 35),
                        (cx + sgn * 148, neck[1] + 95), (cx + sgn * 88, neck[1] + 195), (cx + sgn * 22, neck[1] + 140)]
                PB._draw_bevel_poly(d, wpts, (245, 242, 234), rim=3.5, ink_w=2)

        # Near leg
        kL = j_end(hipL, 88 * sc, ang['tL'])
        aL = j_end(kL, 86 * sc, ang['tL'] + ang['sL'])
        _paste_rot_part(im, thigh, hipL, kL, 42 * sc)
        _paste_rot_part(im, shin, kL, aL, 36 * sc)
        paste_centered_fit(im, boot, (aL[0] - 24 * sc, aL[1] - 12 * sc, 64 * sc, 48 * sc), op)

        # Skirt / lower robe (ONLY on skirt builds!)
        if C['pelvis'] == 'skirt':
            sk = PB.get_painted_body_part('pelvis', view, cid, build_id, spec)
            paste_centered_fit(im, sk, (cx - torso_w * 0.68, hipL[1] - 18 * sc, torso_w * 1.36, 132 * sc), op)

        # Torso
        paste_centered_fit(im, torso, (cx - torso_w * 0.5, neck[1] - 4, torso_w, torso_h), op)

        # Head + sunglasses
        head = PB.get_painted_head(cid, build_id, spec, view, blank=False, expr=expr)
        if spec.get('glasses') and cid != 'ex' and view not in ('back', 'threequarter_back'):
            gl = PB.get_painted_sunglasses('front' if view != 'profile' else 'profile')
            gl_s = gl.resize((int(head.width * 0.72), int(head.height * 0.22)), Image.LANCZOS)
            head.alpha_composite(gl_s, (int(head.width * (0.14 if view == 'front' else 0.22)), int(head.height * 0.35)))
        hw, hh = int(106 * sc * (1.28 if spec['hair_style'] == 'afro' else 1.0)), int(124 * sc)
        paste_centered_fit(im, head, (neck[0] - hw * 0.5, neck[1] - hh + 14 * sc, hw, hh), op)

        # Near arm in front
        eL = j_end(shL, 68 * sc, ang['uL'])
        wL = j_end(eL, 62 * sc, ang['uL'] + ang['fL'])
        _paste_rot_part(im, uarm, shL, eL, 30 * sc)
        _paste_rot_part(im, farm, eL, wL, 26 * sc)
        paste_centered_fit(im, hand, (wL[0] - 18 * sc, wL[1] - 8 * sc, 38 * sc, 38 * sc), op)

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    im.save(out_png)
    return im


def build_costume_poses(cid, build_id, cos_name, spec):
    pose_dir = os.path.join(OUT, 'poses', f'{cid}.{cos_name}')
    os.makedirs(pose_dir, exist_ok=True)
    pose_names = ['stand_front', 'stand_threequarter', 'stand_profile', 'stand_back', 'walk', 'reach', 'sit', 'kneel', 'crouch', 'fall']
    pose_recs = []
    imgs = []
    for pname in pose_names:
        out_png = os.path.join(pose_dir, f'{pname}.png')
        im = render_assembled_pose(cid, build_id, cos_name, pname, spec, out_png)
        imgs.append((pname, im))
        pose_recs.append({'id': pname, 'file': f'v2/poses/{cid}.{cos_name}/{pname}.png'})

    cw, ch = 360, 480
    sheet = Image.new('RGB', (cw * 5, ch * 2 + 70), PAPER)
    sd = ImageDraw.Draw(sheet)
    sd.text((28, 18), f"{cid.upper()} · {cos_name.replace('_', ' ').upper()} · ALL 10 ASSEMBLED POSES", font=font(FONTB, 24), fill=INK)
    for idx, (pname, pim) in enumerate(imgs):
        col, row = idx % 5, idx // 5
        x0, y0 = col * cw, 70 + row * ch
        sd.rectangle([x0 + 6, y0 + 6, x0 + cw - 6, y0 + ch - 6], outline=(218, 210, 198), width=1)
        t = pim.copy()
        t.thumbnail((cw - 20, ch - 44), Image.LANCZOS)
        sheet.paste(t, (x0 + (cw - t.width) // 2, y0 + 8), t)
        sd.text((x0 + cw // 2, y0 + ch - 22), pname.replace('_', ' '), font=font(FONTB, 15), fill=INK, anchor='mm')

    sheet_rel = f'v2/poses/{cid}.{cos_name}.poses.jpg'
    sheet.save(os.path.join(OUT, 'poses', f'{cid}.{cos_name}.poses.jpg'), quality=88)
    return sheet_rel, pose_recs


# ---------------------------------------------------------------------------
# 3. Per-Poem Character Action Sheet, Prop Kit Sheet, & Set Multiplane Kit Sheet
# ---------------------------------------------------------------------------
def render_action_sheet_and_parts(c, poem, uses, cos_name):
    cid = c['id']
    build_id = c['build']
    b = K.CHARS[build_id]
    spec = COSTUME_SPEC.get(cos_name) or next(COSTUME_SPEC[k] for k in c['kits'] if k in COSTUME_SPEC)
    pid = f"{cid}.{poem['num']}.action"
    parts_dir = os.path.join(OUT, 'parts', pid)
    pose_dir = os.path.join(OUT, 'poses', pid)
    os.makedirs(parts_dir, exist_ok=True)
    os.makedirs(pose_dir, exist_ok=True)
    op = spec.get('opacity', 1.0)

    px = 3.6 if b['height'] > 140 else 5.0
    im_bg, d_bg = K.sheet_frame(pid, f"{c['name']} in {poem['num']} {poem['title']} · painted poses, hands and held props", px)
    layer = Image.new('RGBA', (SHEET_W, SHEET_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cell_meta = []
    pose_recs = []

    poses = uses['poses'][:6]
    cw = (SHEET_W - 120) / max(1, min(6, len(poses)))
    for i, (pose, view, line) in enumerate(poses):
        x0, y0 = 60 + cw * i, 120
        floor = y0 + 560
        d_bg.rectangle([x0 + 6, y0, x0 + cw - 6, floor + 18], outline=(222, 216, 206), width=1)
        d_bg.line([(x0 + 14, floor), (x0 + cw - 14, floor)], fill=(200, 192, 180), width=2)
        hip = V2.POSE_HIP.get(pose, 95 if b['height'] > 140 else 60)
        hip_px = (x0 + cw / 2, floor - hip * px)

        sp_rep = PB.get_painted_replacement_pose(f"{pose}_{view}", view, cid, build_id, spec)
        pbox_r = paste_centered_fit(layer, sp_rep, (x0 + 16, y0 + 92, cw - 32, 465), op)
        draw_brad(d, hip_px, r=6.5)

        d_bg.text((x0 + 14, y0 + 10), f"{pose} · {view}", font=font(FONTB, 17), fill=INK)
        for k, ln in enumerate(textwrap.wrap(line, int(cw / 9))[:3]):
            d_bg.text((x0 + 14, y0 + 34 + k * 18), ln, font=font(FONT, 14), fill=(110, 100, 90))
        pname = f"pose.{i+1}_{pose}_{view}".replace(' ', '_')
        cell_meta.append((pname, pbox_r, {'A': hip_px, 'hip': hip_px}))

        map_p = 'sit' if 'sit' in str(pose) else ('kneel' if 'kneel' in str(pose) else ('crouch' if 'crouch' in str(pose) else ('lie_back' if 'lie' in str(pose) or 'float' in str(pose) else ('fall' if 'fall' in str(pose) else ('walk' if 'walk' in str(pose) else 'stand_threequarter')))))
        ap_path = os.path.join(pose_dir, f'{pname}.png')
        render_assembled_pose(cid, build_id, cos_name, map_p, spec, ap_path)
        pose_recs.append({'id': f"{pose} · {view}", 'file': f'v2/poses/{pid}/{pname}.png'})

    # Hands row
    y = 740
    d_bg.text((60, y), 'HANDS IN THIS POEM', font=font(FONTB, 18), fill=INK)
    x = 60
    for hi, (shape, holds) in enumerate(uses['hands'][:8]):
        d_bg.rectangle([x, y + 30, x + 210, y + 170], outline=(222, 216, 206))
        a_px = (x + 36, y + 105)
        b_px = (x + 146, y + 105)
        h_lookup = 'in_pocket' if 'pocket' in str(shape) or 'hidden' in str(shape) else ('hold_cup' if 'cup' in str(holds) else ('hold_box' if 'box' in str(holds) else ('grip_mic' if 'mic' in str(holds) else ('hold_phone' if 'phone' in str(holds) else shape))))
        sp_h = PB.get_painted_hand(h_lookup, 'back', spec)
        pbox_h = paste_centered_fit(layer, sp_h, (x + 14, y + 54, 182, 110), op)
        draw_brad(d, a_px, r=5.5, eyelet=True)
        d_bg.text((x + 8, y + 36), f"{shape}" + (f" · {holds}" if holds else ''), font=font(MONO, 13), fill=INK)
        hname = f"hand.{hi+1}_{shape}" + (f"_{holds}" if holds else '')
        cell_meta.append((hname, pbox_h, {'A': a_px, 'B': b_px}))
        x += 225

    # Props row
    y = 930
    d_bg.text((60, y), 'PROPS THIS CHARACTER HOLDS OR TOUCHES', font=font(FONTB, 18), fill=INK)
    x = 60
    for pi, (prop_id, what, sc) in enumerate(uses['props'][:9]):
        s = max(90, min(185, float(sc or 20) * 3.2))
        ph = 145
        grip_px = (x + s / 2, y + 30 + ph * 0.5)
        sp_pr = PB.get_painted_prop(prop_id, what, sc)
        pbox_p = paste_centered_fit(layer, sp_pr, (x, y + 28, s, ph), 1.0)
        d_bg.text((x, y + 32 + ph), prop_id[:22], font=font(MONO, 12), fill=INK)
        cell_meta.append((f"prop.{prop_id}", pbox_p, {'B': grip_px, 'grip': grip_px}))
        x += s + 34

    sliced_parts = []
    for pname, bbox, socks in cell_meta:
        pinfo = crop_part_rgba(layer, bbox, socks, os.path.join(parts_dir, f'{pname}.png'), pad=2)
        sliced_parts.append({'id': pname, **pinfo})

    im_sheet = im_bg.convert('RGBA')
    im_sheet.alpha_composite(layer)
    return im_sheet.convert('RGB'), sliced_parts, pose_recs


def render_poem_props_kit(P, footage_refs):
    """Build a dedicated 2048x1152 Poem Prop Kit Sheet (`poem.<NN>.props.jpg`), 3-panel pack, and separate RGBA prop PNGs."""
    num = P['num']
    title = P.get('title', '')
    pid = f"poem.{num}.props"
    parts_dir = os.path.join(OUT, 'parts', pid)
    os.makedirs(parts_dir, exist_ok=True)

    # Collect all props from needs.props + shot props
    props_list = []
    seen = set()
    for pr in P.get('needs', {}).get('props', []):
        if isinstance(pr, dict) and pr.get('id') not in seen:
            seen.add(pr['id'])
            props_list.append((pr['id'], pr.get('what', ''), pr.get('scale_cm', 25)))
    for sc in P.get('scenes', []):
        for sh in sc.get('shots', []):
            for pr in sh.get('props', []):
                pr_id = pr.get('id') if isinstance(pr, dict) else str(pr)
                if pr_id and pr_id not in seen:
                    seen.add(pr_id)
                    props_list.append((pr_id, pr.get('state', 'scene prop') if isinstance(pr, dict) else 'scene prop', 30))

    im_bg, d_bg = K.sheet_frame(pid, f"Poem {num} · {title} · Hero & Scene Prop Kit ({len(props_list)} painted cardboard props)", 6.0)
    layer = Image.new('RGBA', (SHEET_W, SHEET_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    n = max(1, len(props_list))
    cols = min(5, max(3, math.ceil(math.sqrt(n * 1.6))))
    rows = max(1, math.ceil(n / cols))
    cw = (SHEET_W - 120) / cols
    ch = (SHEET_H - 160) / rows

    prop_parts = []
    for idx, (pr_id, pr_what, pr_sc) in enumerate(props_list):
        col, row = idx % cols, idx // cols
        x0, y0 = 60 + col * cw, 120 + row * ch
        d_bg.rectangle([x0 + 6, y0 + 6, x0 + cw - 6, y0 + ch - 6], outline=(218, 210, 198), width=1)

        sp_pr = PB.get_painted_prop(pr_id, pr_what, pr_sc)
        pbox = paste_centered_fit(layer, sp_pr, (x0 + 22, y0 + 38, cw - 44, ch - 84), 1.0)
        grip_px = ((pbox[0] + pbox[2]) * 0.5, (pbox[1] + pbox[3]) * 0.5)
        cross(d_bg, grip_px, SOCK_B, '', 7)

        d_bg.text((x0 + 14, y0 + 12), f"{idx+1}. {pr_id}", font=font(FONTB, 16), fill=INK)
        d_bg.text((x0 + cw - 14, y0 + 14), f"{pr_sc} cm", font=font(MONO, 12), fill=(120, 108, 96), anchor='ra')
        for li, ln in enumerate(textwrap.wrap(str(pr_what), int(cw / 8.5))[:2]):
            d_bg.text((x0 + 14, y0 + ch - 38 + li * 15), ln, font=font(FONT, 13), fill=(95, 86, 76))

        out_png = os.path.join(parts_dir, f"{pr_id}.png")
        sp_pr.save(out_png)
        prop_parts.append({
            'id': pr_id,
            'label': pr_id,
            'what': pr_what,
            'scale_cm': pr_sc,
            'file': f"v2/parts/{pid}/{pr_id}.png",
            'size': list(sp_pr.size),
            'sockets': {'B': [round(sp_pr.width * 0.5, 1), round(sp_pr.height * 0.5, 1)]},
        })

    im_sheet = im_bg.convert('RGBA')
    im_sheet.alpha_composite(layer)
    sheet_rgb = im_sheet.convert('RGB')
    sheet_rgb.save(os.path.join(OUT, 'sheets', f"{pid}.jpg"), quality=88)

    ref_files = [os.path.join(SHOTS, r['image']) for r in footage_refs[:4] if r.get('image') and os.path.exists(os.path.join(SHOTS, r['image']))]
    prop_summary = '; '.join(f"{p['id']} ({p['what']})" for p in prop_parts[:10])
    pack_img = V2.compose(sheet_rgb, ref_files, f"Hero & scene props for Poem {num} {title}: {prop_summary}",
                          [os.path.join(PB.MAN_SHEETS, 'props.jpg'), os.path.join(PB.MAN_SHEETS, 'set_props.jpg')],
                          f"POEM {num} PROPS · {title}")
    pack_img.save(os.path.join(OUT, 'packs', f"{pid}.jpg"), quality=84)

    prompt = (PKS.TEXT + f"POEM {num} ({title}) PROP KIT. Panel A is the prop layout grid; Panel B shows the poem's footage reference plates; "
              f"Panel C shows the hand-painted corrugated cardboard prop craft style (props.jpg / set_props.jpg). "
              f"Paint every prop on its own separate corrugated cardboard cutout card with raw kraft bevel edge, gouache paint, ink linework, "
              f"and a brass eyelet at its red grip cross: {prop_summary}. " + PKS.RULES)

    return {
        'id': pid,
        'sheet_image': f"v2/sheets/{pid}.jpg",
        'image': f"v2/packs/{pid}.jpg",
        'prompt': prompt,
        'parts': prop_parts,
    }


def render_poem_sets_kit(P, footage_refs):
    """Build a dedicated 2048x1152 Poem Place / Multiplane Set Kit Sheet (`poem.<NN>.sets.jpg`),
    3-panel pack, and separate RGBA proscenium stage & multiplane depth layer cards."""
    num = P['num']
    title = P.get('title', '')
    pid = f"poem.{num}.sets"
    parts_dir = os.path.join(OUT, 'parts', pid)
    os.makedirs(parts_dir, exist_ok=True)

    sets_list = P.get('sets', [])
    im_bg, d_bg = K.sheet_frame(pid, f"Poem {num} · {title} · Multiplane Places & Set Kit ({len(sets_list)} stage environments)", 4.0)
    layer = Image.new('RGBA', (SHEET_W, SHEET_H), (0, 0, 0, 0))

    n = max(1, len(sets_list))
    cols = min(3, max(2, math.ceil(math.sqrt(n * 1.3))))
    rows = max(1, math.ceil(n / cols))
    cw = (SHEET_W - 120) / cols
    ch = (SHEET_H - 160) / rows

    set_parts = []
    flat_parts = []
    for idx, s in enumerate(sets_list):
        sid = s['id']
        swhat = s.get('what', '')
        col, row = idx % cols, idx // cols
        x0, y0 = 60 + col * cw, 120 + row * ch
        d_bg.rectangle([x0 + 6, y0 + 6, x0 + cw - 6, y0 + ch - 6], outline=(218, 210, 198), width=1)

        # Match best footage ref for this set
        ref = footage_refs[idx % len(footage_refs)] if footage_refs else None
        stage_card = PB.build_set_stage_card(sid, swhat, ref, w=560, h=330)
        paste_centered_fit(layer, stage_card, (x0 + 18, y0 + 42, cw - 36, ch - 102), 1.0)

        d_bg.text((x0 + 16, y0 + 14), f"SET {idx+1}: {sid}", font=font(FONTB, 17), fill=INK)
        if ref:
            d_bg.text((x0 + cw - 16, y0 + 16), f"Ref: {ref['id'][:14]}", font=font(MONO, 12), fill=(110, 100, 90), anchor='ra')
        for li, ln in enumerate(textwrap.wrap(swhat, int(cw / 8.2))[:2]):
            d_bg.text((x0 + 16, y0 + ch - 50 + li * 16), ln, font=font(FONT, 13), fill=(90, 82, 72))

        stage_out = os.path.join(parts_dir, f"{sid}.stage.png")
        stage_card.save(stage_out)
        flat_parts.append({
            'id': f"{sid}.stage",
            'label': f"{sid} (stage)",
            'what': swhat,
            'file': f"v2/parts/{pid}/{sid}.stage.png",
            'size': list(stage_card.size),
        })

        # Also export up to 3 multiplane RGBA layer cards (P6 Sky/BG, P4 Midground, P1 FG) for this set!
        plane_files = []
        if ref and ref.get('multiplane_layers'):
            for li, mp_rel in enumerate(ref['multiplane_layers'][:3]):
                mp_src = os.path.join(SHOTS, mp_rel)
                if os.path.exists(mp_src):
                    try:
                        mp_im = Image.open(mp_src).convert('RGBA')
                        mp_base = os.path.splitext(os.path.basename(mp_rel))[0]
                        mp_name = f"{sid}.{mp_base}.png"
                        mp_out = os.path.join(parts_dir, mp_name)
                        mp_im.save(mp_out)
                        plane_files.append({'id': f"{sid}.{mp_base}", 'file': f"v2/parts/{pid}/{mp_name}"})
                        flat_parts.append({
                            'id': f"{sid}.{mp_base}",
                            'label': f"{sid} · {mp_base}",
                            'what': f"Multiplane depth layer {mp_base} for {sid}",
                            'file': f"v2/parts/{pid}/{mp_name}",
                            'size': list(mp_im.size),
                        })
                    except Exception:
                        pass

        set_parts.append({
            'id': sid,
            'what': swhat,
            'file': f"v2/parts/{pid}/{sid}.stage.png",
            'ref_id': ref['id'] if ref else None,
            'ref_image': ref.get('image') if ref else None,
            'ref_cel': ref.get('cel') if ref else None,
            'ref_exploded': ref.get('exploded') if ref else None,
            'planes': plane_files,
        })

    im_sheet = im_bg.convert('RGBA')
    im_sheet.alpha_composite(layer)
    sheet_rgb = im_sheet.convert('RGB')
    sheet_rgb.save(os.path.join(OUT, 'sheets', f"{pid}.jpg"), quality=88)

    ref_files = [os.path.join(SHOTS, r['image']) for r in footage_refs[:4] if r.get('image') and os.path.exists(os.path.join(SHOTS, r['image']))]
    set_summary = '; '.join(f"{s['id']} ({s['what']})" for s in sets_list)
    pack_img = V2.compose(sheet_rgb, ref_files, f"Multiplane places & sets for Poem {num} {title}: {set_summary}",
                          [os.path.join(PB.MAN_SHEETS, 'set_props.jpg')],
                          f"POEM {num} PLACES & SETS · {title}")
    pack_img.save(os.path.join(OUT, 'packs', f"{pid}.jpg"), quality=84)

    prompt = (PKS.TEXT + f"POEM {num} ({title}) MULTIPLANE PLACE & SET KIT. Each location is built as a multiplane stack of die-cut "
              f"corrugated cardboard stage planes (Plane 0 FG Occluder, Plane 2 Action Stage, Plane 4 Midground Set, Plane 6 Backdrop/Sky) "
              f"with brass corner registration brads: {set_summary}. " + PKS.RULES)

    return {
        'id': pid,
        'sheet_image': f"v2/sheets/{pid}.jpg",
        'image': f"v2/packs/{pid}.jpg",
        'prompt': prompt,
        'sets': set_parts,
        'parts': flat_parts,
    }


# ---------------------------------------------------------------------------
# 4. Main Pipeline: Build All Kits, Sheets, Poses, Separate Parts & Enriched kits.json
# ---------------------------------------------------------------------------
def main():
    for sub in ('sheets', 'packs', 'parts', 'poses', 'templates'):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)

    # Load film/poems.json for district/score/tagline metadata
    poems_meta_map = {}
    pm_path = os.path.join(SHOTS, 'film', 'poems.json')
    if os.path.exists(pm_path):
        pm_raw = json.load(open(pm_path))
        pm_list = pm_raw.get('poems', []) if isinstance(pm_raw, dict) else pm_raw
        for pm in pm_list:
            if isinstance(pm, dict):
                poems_meta_map[str(pm.get('num')).zfill(2)] = pm

    out = {'about': V2.__doc__.strip().split('\n')[0], 'cast': [], 'poems': []}
    total_sheets, total_parts, total_poses = 0, 0, 0

    # 1. Generate all 14 characters & 28 costume kits
    for c in V2.CAST:
        cid = c['id']
        build_id = c['build']
        sheets = V2.SHEETS_BACK if c.get('back_only') else (V2.SHEETS_FULL if c.get('principal') else V2.SHEETS_EXTRA)
        entry = {'id': cid, 'name': c['name'], 'build': build_id, 'height_cm': K.CHARS[build_id]['height'], 'who': c['who'], 'costumes': []}

        for cos, (desc, poems) in c['kits'].items():
            spec = COSTUME_SPEC[cos]
            kit_id = f"{cid}.{cos}"
            parts_dir = os.path.join(OUT, 'parts', kit_id)
            os.makedirs(parts_dir, exist_ok=True)

            poses_sheet_rel, pose_recs = build_costume_poses(cid, build_id, cos, spec)
            total_poses += len(pose_recs)
            refs = list(c['refs']) if c.get('refs') else [
                os.path.join(OUT, 'poses', kit_id, 'stand_front.png'),
                os.path.join(OUT, 'poses', kit_id, 'stand_threequarter.png'),
                os.path.join(OUT, 'poses', kit_id, 'sit.png'),
            ]

            packs = []
            kit_parts = []
            for sh in sheets:
                kind = sh.split('.')[0]
                pid = f"{cid}.{cos}.{sh}"
                painted_sheet, sh_parts = render_costume_sheet(cid, build_id, cos, sh, spec, parts_dir)
                sheet_path = os.path.join(OUT, 'sheets', pid + '.jpg')
                painted_sheet.save(sheet_path, quality=88)
                total_sheets += 1

                for sp in sh_parts:
                    sp['file'] = os.path.relpath(sp['file'], HERE).replace(os.sep, '/')
                    sp['sheet'] = sh
                    kit_parts.append(sp)
                total_parts += len(sh_parts)

                sty = V2.STYLE('craft_dummy.jpg', *V2.SHEET_STYLE[kind][:2]) if c.get('bolas') else V2.STYLE(*V2.SHEET_STYLE[kind])
                pack_img = V2.compose(painted_sheet, refs, f"{desc}.", sty, f"{c['name']} · {cos.replace('_', ' ')}")
                pack_img.save(os.path.join(OUT, 'packs', pid + '.jpg'), quality=84)

                packs.append({
                    'id': pid,
                    'sheet': sh,
                    'sheet_image': f'v2/sheets/{pid}.jpg',
                    'image': f'v2/packs/{pid}.jpg',
                    'prompt': V2.prompt(c, cos, desc, sh, poems),
                    'parts_count': len(sh_parts),
                })

            entry['costumes'].append({
                'costume': cos,
                'what': desc,
                'poems': poems.split(),
                'poses_sheet': poses_sheet_rel,
                'poses': pose_recs,
                'parts': kit_parts,
                'packs': packs,
            })
            print(f"[kit] {cid}.{cos}: {len(packs)} painted sheets, {len(pose_recs)} poses, {len(kit_parts)} separate RGBA parts")

        out['cast'].append(entry)

    # 2. Generate all 14 Poems: Character Action Kits + Poem Prop Kits + Poem Multiplane Set Kits + Footage Refs
    roles = {'POET': 'poet', 'EX': 'ex', 'YOUNG_POET': 'young_poet', 'GHOST_CHILD': 'ghost_child', 'MOTHER': 'woman', 'SHE': 'woman'}
    bycos = {cos: c for c in V2.CAST for cos in c['kits']}
    for f in sorted(glob.glob(os.path.join(V2.BD, '[0-9][0-9].json'))):
        P = json.load(open(f))
        num = P.get('num') or os.path.basename(f)[:2]
        P['num'] = num
        pm = poems_meta_map.get(num, {})
        rb_path = os.path.join(SHOTS, 'film', f'riverbed_{num}.json')
        rb_data = json.load(open(rb_path)) if os.path.exists(rb_path) else {}

        footage_refs = PB.get_poem_footage_refs(num)
        for r in footage_refs:
            r['shot_id'] = r.get('id', '')
            r['layers'] = r.get('multiplane_layers', [])
        prop_kit = render_poem_props_kit(P, footage_refs)
        set_kit = render_poem_sets_kit(P, footage_refs)
        total_sheets += 2
        total_parts += len(prop_kit['parts']) + len(set_kit['parts'])

        present = {}
        for sc in P.get('scenes') or []:
            for sh in sc.get('shots') or []:
                for b in sh.get('bodies') or []:
                    cos = V2.costume_of(b)
                    role = (b.get('role') or '').upper()
                    cid = roles.get(role) or roles.get(role.rsplit('_', 1)[0])
                    c = next((x for x in V2.CAST if x['id'] == cid), None) or bycos.get(cos)
                    if c is None:
                        continue
                    present.setdefault(c['id'], set()).add(cos)

        chars = []
        for cid, coss in present.items():
            c = next(x for x in V2.CAST if x['id'] == cid)
            if cid in ('poet', 'ex', 'young_poet', 'ghost_child'):
                test = lambda b, cid=cid: roles.get(b.get('role')) == cid
            else:
                test = lambda b, coss=coss: V2.costume_of(b) in coss
            uses = V2.poem_uses(P, test)
            pmap = {p['id']: p for p in (P.get('needs') or {}).get('props') or [] if isinstance(p, dict) and p.get('id')}
            seen_pr = {p[0] for p in uses['props']}
            for sc in P.get('scenes') or []:
                for sh in sc.get('shots') or []:
                    if any(test(b) for b in (sh.get('bodies') or [])):
                        for pr_item in sh.get('props') or []:
                            pr_id = pr_item.get('id') if isinstance(pr_item, dict) else str(pr_item)
                            if pr_id and pr_id not in seen_pr:
                                seen_pr.add(pr_id)
                                e = pmap.get(pr_id, {})
                                uses['props'].append((pr_id, e.get('what', ''), e.get('scale_cm', 20)))
            active_cos = next((x for x in sorted(coss) if x in COSTUME_SPEC), next(iter(c['kits'])))
            pid = f"{cid}.{num}.action"

            painted_action, act_parts, act_poses = render_action_sheet_and_parts(c, P, uses, active_cos)
            painted_action.save(os.path.join(OUT, 'sheets', pid + '.jpg'), quality=88)
            total_sheets += 1
            for sp in act_parts:
                sp['file'] = os.path.relpath(sp['file'], HERE).replace(os.sep, '/')
            total_parts += len(act_parts)
            total_poses += len(act_poses)

            refs = list(c['refs']) if c.get('refs') else [
                os.path.join(OUT, 'poses', f"{cid}.{active_cos}", 'stand_front.png'),
                os.path.join(OUT, 'poses', f"{cid}.{active_cos}", 'stand_threequarter.png'),
            ]
            lines = [f"{p}: {w}" for p, w, s in uses['props']]
            desc = '; '.join(f"{a} ({v}): {l}" for a, v, l in uses['poses'][:6])
            pack_img = V2.compose(painted_action, refs, f"In {P['title']}: " + desc[:500],
                                  V2.STYLE(*V2.SHEET_STYLE['action']), f"{c['name']} · {num} {P['title']}")
            pack_img.save(os.path.join(OUT, 'packs', pid + '.jpg'), quality=84)

            pr = (PKS.TEXT + f"WHO (panel B): {c['who']} COSTUME in this poem: " +
                  ', '.join(c['kits'].get(x, (x,))[0] for x in sorted(coss) if x) + ". " +
                  f"SHEET: {c['name']}'s action sheet for the poem '{P['title']}': one whole-body replacement card per cell for these poses, "
                  f"each with a brass brad at the hip on the green cross, head and hands left off: {desc}. " +
                  (f"Below them, the hands this poem needs ({', '.join(h + (' holding ' + str(o) if o else '') for h, o in uses['hands'][:8])}) on eyelet tabs, " if uses['hands'] else '') +
                  (f"and the props this character holds, each in its own cell with its grip on the red cross: {'; '.join(lines)}. " if lines else '') +
                  ("HIS FACE IS NEVER SEEN. " if c.get('back_only') else '') + PKS.RULES)

            chars.append({
                'id': cid,
                'name': c['name'],
                'costumes': sorted(x for x in coss if x),
                'action': {
                    'id': pid,
                    'sheet_image': f'v2/sheets/{pid}.jpg',
                    'image': f'v2/packs/{pid}.jpg',
                    'prompt': pr,
                    'parts': act_parts,
                    'poses': act_poses,
                },
                'poses': [p[0] + ' · ' + p[1] for p in uses['poses']],
                'hands': [h + (f'({o})' if o else '') for h, o in uses['hands']],
                'props': [p[0] for p in uses['props']],
            })

        # Summarize scenes and movements for the poem page
        scenes_summary = []
        for sc in P.get('scenes', []):
            scenes_summary.append({
                'id': sc.get('id', ''),
                'movement': sc.get('movement', ''),
                'seconds': sc.get('seconds', 0),
                'lines': sc.get('lines', ''),
                'treatment': sc.get('treatment', ''),
                'shot_count': len(sc.get('shots', [])),
                'shots': [
                    {
                        'id': sh.get('id', ''),
                        'framing': sh.get('framing', ''),
                        'camera': sh.get('camera', ''),
                        'set': sh.get('set', ''),
                        'action': sh.get('action', ''),
                        'fx': sh.get('fx', []),
                    }
                    for sh in sc.get('shots', [])
                ],
            })

        out['poems'].append({
            'num': num,
            'title': P.get('title'),
            'style': P.get('style'),
            'pages': P.get('pages', []),
            'tagline': pm.get('tagline', ''),
            'district_name': pm.get('district_name', ''),
            'color': pm.get('color', '#c99765'),
            'riverbed': rb_data.get('riverbed', {}),
            'source_profile': rb_data.get('source_profile', {}),
            'needs': P.get('needs', {}),
            'scenes': scenes_summary,
            'footage_refs': footage_refs,
            'prop_kit': prop_kit,
            'set_kit': set_kit,
            'characters': chars,
            'page_url': f"poems/kits/{num}.html",
        })
        print(f"[poem {num}] {P.get('title')}: {len(chars)} char kits, {len(prop_kit['parts'])} props, {len(set_kit['sets'])} sets, {len(footage_refs)} footage refs")

    for b in V2.BUILDS:
        p = os.path.join(OUT, 'templates', f'{b}.cutchart.png')
        if not os.path.exists(p):
            K.cut_chart(b).save(p)

    json.dump(out, open(os.path.join(OUT, 'kits.json'), 'w'), indent=1)
    print(f"DONE: {total_sheets} painted sheets, {total_poses} assembled poses, {total_parts} separate RGBA cut-out parts.")


if __name__ == '__main__':
    main()
