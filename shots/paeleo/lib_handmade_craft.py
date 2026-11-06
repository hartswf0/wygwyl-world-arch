#!/usr/bin/env python3
"""
PAELEO × WYGWYL — TRUE HANDMADE SCION STUDIO ENGINE (`SCION 01–54`)
===================================================================
Builds every world, architectural stage, prop, and articulated multi-joint human
character from the bottom up in each SCION swarm's native formal primitives—
matching the exact handmade craft of `bolas_repo/paeleo/handmade/01..54`:
  - `01-gilliam` (Poem 12): Cross-hatched 19th-century steel-engraving plates + cream scissor-cut margins + tilted paper speech tags
  - `02-reiniger` (Poem 02): Razor-cut black lead silhouettes + scalloped lace border + diamond fretwork + gold filigree cartouche
  - `04-mouris` (Poem 14): Boiling mosaic of thousands of tiny archive/motif tiles forming walls, floor, door, and figures
  - `05-norstein` (Poem 01): Multiplane painted glass panes in 3D Z-depth + out-of-focus foreground window mullion + volumetric mist gauze
  - `07-foldes` (Poem 13): Hand-drawn calligraphic vector/Bezier line-art on warm parchment/dusk canvas with continuous stroke metamorphosis
  - `08-sutherland` (Poem 11): 1963 TX-2 green-phosphor oscilloscope vector CRT display + Gauss-Seidel constraint solver + Sketchpad console
  - `09-igarashi` (Poem 10): Hand-drawn paper-cutout Rider & Motorcycle with cream die-cut border + triangulated ARAP mesh warp
  - `15-layered-puppet` (Poem 08): 2-cel opaque Body + translucent cyan/gold Soul cel + 2nd-order damped harmonic spring + 3 winged Angels
  - `18-cartoon-saloon` (Poem 05): Flat gouache watercolor washes + Book-of-Kells spiral motifs + gold-leaf 9-node KIN constellation
  - `28-mask-plate-foundry` (Poem 06): Perspective-pinned masonry forum plates + holdout mattes + Snell underwater waterline refraction
  - `33-inverse-kinematics` (Poem 04): 3D perspective camera + 2.5D shaded capsule/cylinder wooden automaton + analytical 2-bone law-of-cosines IK
  - `47-sound-to-action` (Poem 07): Clean 2D studio vector stage + Moho Smart-Bone head/torso rig + rear-screen daisy + audio RMS bars
  - `49-open-content-atelier` (Poem 03): Painterly museum-atelier harbour chapel + 6 decaying material relics + zero human puppets
  - `11-video-puppetry` (Poem 09): Locked harbour glass phone-booth stage across 4-hour relighting clock + wet asphalt mirror reflection
"""
import glob
import math
import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import lib_handmade_round2_assets as R2  # noqa: E402

W, H = 1280, 720
FPS = 24
SHOTS = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots"


def get_font(size, bold=False, mono=False, italic=False):
    candidates = []
    if mono:
        candidates = ["/System/Library/Fonts/Menlo.ttc", "/Library/Fonts/JetBrainsMono-Regular.ttf"]
    elif bold:
        candidates = ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf", "/System/Library/Fonts/Supplemental/Impact.ttf", "/System/Library/Fonts/HelveticaNeue.ttc"]
    elif italic:
        candidates = ["/System/Library/Fonts/Supplemental/Georgia Italic.ttf", "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf", "/System/Library/Fonts/Supplemental/Georgia.ttf"]
    else:
        candidates = ["/System/Library/Fonts/Supplemental/Georgia.ttf", "/System/Library/Fonts/Supplemental/Times New Roman.ttf", "/System/Library/Fonts/HelveticaNeue.ttc"]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, u):
    return a + (b - a) * clamp(u, 0.0, 1.0)


def smoothstep(a, b, x):
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    u = (x - a) / (b - a)
    return u * u * (3.0 - 2.0 * u)


def capsule_poly(p0, p1, r0, r1, n_cap=10):
    """Returns a closed polygon list of (x, y) points for a tapered 2D capsule from p0 to p1."""
    x0, y0 = float(p0[0]), float(p0[1])
    x1, y1 = float(p1[0]), float(p1[1])
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 1e-4:
        return [(x0 + r0 * math.cos(a), y0 + r0 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
    ang = math.atan2(dy, dx)
    pts = []
    for a in np.linspace(ang + math.pi / 2, ang + 3 * math.pi / 2, n_cap):
        pts.append((x0 + r0 * math.cos(a), y0 + r0 * math.sin(a)))
    for a in np.linspace(ang - math.pi / 2, ang + math.pi / 2, n_cap):
        pts.append((x1 + r1 * math.cos(a), y1 + r1 * math.sin(a)))
    return pts


def solve_2bone_2d(root, target, l1, l2, bend_dir=1.0):
    """Analytical 2D law-of-cosines 2-bone IK solver (`root -> mid -> end`)."""
    rx, ry = float(root[0]), float(root[1])
    tx, ty = float(target[0]), float(target[1])
    dx, dy = tx - rx, ty - ry
    d = math.hypot(dx, dy)
    d_clamped = clamp(d, abs(l1 - l2) + 1e-3, (l1 + l2) * 0.998)
    ux, uy = (dx / d, dy / d) if d > 1e-5 else (0.0, 1.0)
    ex, ey = rx + ux * d_clamped, ry + uy * d_clamped
    cos_a = clamp((l1 * l1 + d_clamped * d_clamped - l2 * l2) / (2.0 * l1 * d_clamped), -1.0, 1.0)
    a = math.acos(cos_a) * (1.0 if bend_dir >= 0 else -1.0)
    ang = math.atan2(uy, ux) + a
    mx, my = rx + l1 * math.cos(ang), ry + l1 * math.sin(ang)
    return (mx, my), (ex, ey), abs(d - d_clamped)


def build_human_skeleton(
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
):
    """
    Computes a full 17-joint articulated human skeleton grounded at `(foot_x, foot_y)`.
    Returns a dictionary of joint coordinates and limb segments with planted feet.
    """
    s = height / 220.0
    dir_x = 1.0 if facing >= 0 else -1.0
    lean_rad = math.radians(lean_deg * dir_x)

    # Stride foot positions (planted on floor at foot_y)
    stride_w = 24.0 * s if walking else 10.0 * s
    s_sin = math.sin(walk_phase) if walking else 0.0
    s_cos = math.cos(walk_phase) if walking else 0.0
    bob = abs(s_cos) * 4.5 * s if walking else 0.0

    hip_y = foot_y - (106.0 * (1.0 - 0.42 * sit)) * s - bob
    hip_x = foot_x - 14.0 * sit * dir_x * s
    hip = (hip_x, hip_y)

    # Torso & Head
    torso_len = 66.0 * s
    sh_x = hip_x + math.sin(lean_rad) * torso_len
    sh_y = hip_y - math.cos(lean_rad) * torso_len
    shoulder = (sh_x, sh_y)
    neck = (sh_x + math.sin(lean_rad) * 10.0 * s, sh_y - math.cos(lean_rad) * 10.0 * s)

    head_rad = math.radians((lean_deg * 0.5 - head_pitch_deg) * dir_x)
    head_c = (neck[0] + math.sin(head_rad) * 16.0 * s + 3.0 * dir_x * s, neck[1] - math.cos(head_rad) * 16.0 * s)

    # Legs (2-bone IK from hip to planted/stepping ankles)
    l_thigh, l_shin = 52.0 * s, 52.0 * s
    if sit > 0.1:
        ank1 = (foot_x + 28.0 * sit * dir_x * s, foot_y - 6.0 * s)
        ank2 = (foot_x + 18.0 * sit * dir_x * s, foot_y - 6.0 * s)
    else:
        lift1 = max(0.0, -s_cos) * 14.0 * s if walking else 0.0
        lift2 = max(0.0, s_cos) * 14.0 * s if walking else 0.0
        ank1 = (foot_x + s_sin * stride_w * dir_x, foot_y - 6.0 * s - lift1)
        ank2 = (foot_x - s_sin * stride_w * dir_x, foot_y - 6.0 * s - lift2)

    knee1, ank1, _ = solve_2bone_2d(hip, ank1, l_thigh, l_shin, bend_dir=-dir_x)
    knee2, ank2, _ = solve_2bone_2d(hip, ank2, l_thigh, l_shin, bend_dir=-dir_x)
    toe1 = (ank1[0] + 15.0 * dir_x * s, min(foot_y, ank1[1] + 5.0 * s))
    toe2 = (ank2[0] + 15.0 * dir_x * s, min(foot_y, ank2[1] + 5.0 * s))

    # Arms (2-bone FK/IK with reach & arm_raise)
    l_uarm, l_farm = 38.0 * s, 36.0 * s
    swing = -s_sin * 18.0 if walking else 0.0
    ang_sh1 = math.radians(16.0 + swing + 58.0 * reach + 85.0 * arm_raise) * dir_x + lean_rad * 0.5
    ang_el1 = ang_sh1 - math.radians(28.0 + 25.0 * (1.0 - reach)) * dir_x
    elb1 = (sh_x + math.sin(ang_sh1) * l_uarm, sh_y + math.cos(ang_sh1) * l_uarm)
    wrist1 = (elb1[0] + math.sin(ang_el1) * l_farm, elb1[1] + math.cos(ang_el1) * l_farm)
    hand1 = (wrist1[0] + math.sin(ang_el1) * 10.0 * s, wrist1[1] + math.cos(ang_el1) * 10.0 * s)

    ang_sh2 = math.radians(-10.0 - swing + 42.0 * reach + 75.0 * arm_raise) * dir_x + lean_rad * 0.5
    ang_el2 = ang_sh2 - math.radians(24.0) * dir_x
    elb2 = (sh_x + math.sin(ang_sh2) * l_uarm, sh_y + math.cos(ang_sh2) * l_uarm)
    wrist2 = (elb2[0] + math.sin(ang_el2) * l_farm, elb2[1] + math.cos(ang_el2) * l_farm)
    hand2 = (wrist2[0] + math.sin(ang_el2) * 10.0 * s, wrist2[1] + math.cos(ang_el2) * 10.0 * s)

    return {
        "s": s,
        "dir_x": dir_x,
        "foot_x": foot_x,
        "foot_y": foot_y,
        "hip": hip,
        "shoulder": shoulder,
        "neck": neck,
        "head_c": head_c,
        "head_rad": head_rad,
        "knee1": knee1, "ank1": ank1, "toe1": toe1,
        "knee2": knee2, "ank2": ank2, "toe2": toe2,
        "elb1": elb1, "wrist1": wrist1, "hand1": hand1,
        "elb2": elb2, "wrist2": wrist2, "hand2": hand2,
    }


def draw_articulated_human(
    canvas_pil,
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
    Draws a complete, grounded, multi-joint articulated human figure onto `canvas_pil`
    using the repository's existing de-bradded 4-angle painted WYGWYL characters
    (`solve_and_render_ideal_body`) and poem-specific painted figures (`shots/play/assets/*`),
    operated in the specified SCION studio grammar (`norstein`, `reiniger`, `gilliam`,
    `sutherland`, `foldes`, `cartoon_saloon`, `arap`, `clean_vector`).
    """
    sk = build_human_skeleton(
        foot_x, foot_y, height, facing, walk_phase, walking,
        lean_deg, head_pitch_deg, reach, arm_raise, sit
    )
    return R2.render_round2_human_actor(
        canvas_pil,
        sk,
        foot_x,
        foot_y,
        height=height,
        facing=facing,
        walk_phase=walk_phase,
        walking=walking,
        lean_deg=lean_deg,
        head_pitch_deg=head_pitch_deg,
        reach=reach,
        arm_raise=arm_raise,
        sit=sit,
        style=style,
        coat_rgb=coat_rgb,
        pants_rgb=pants_rgb,
        skin_rgb=skin_rgb,
        rim_rgb=rim_rgb,
        sunglasses=sunglasses,
        wings=wings,
        robe=robe,
        alpha=alpha,
        char_id=char_id,
        view=view,
    )


def draw_clean_subtitle(canvas_pil, text, style="default", t=0.0, sutherland_info=None):
    """
    Renders the quiet literary subtitle at the bottom of the frame in the swarm's
    native formal language—with ZERO debug HUD bars at the top!
    """
    draw = ImageDraw.Draw(canvas_pil, "RGBA")
    if style == "sutherland":
        # 1963 TX-2 Sketchpad vector console at bottom (`08-sutherland` style)
        draw.rectangle([28, H - 108, W - 28, H - 14], fill=(4, 18, 8, 235), outline=(52, 195, 92, 220), width=1)
        f_con = get_font(18, mono=True)
        f_sm = get_font(13, mono=True)
        draw.text((44, H - 98), f"> {text.upper()} _", font=f_con, fill=(95, 255, 140, 255))
        btns = ["PARK", "WAVE=0", "PLINTH", "COLUMNS", "BEAMS", "FINIAL"]
        active_b = min(5, int((t / 32.0) * 6))
        for bi, bname in enumerate(btns):
            bx0 = W - 490 + bi * 76
            by0 = H - 98
            is_on = (bi == active_b)
            draw.rectangle([bx0, by0, bx0 + 68, by0 + 24], fill=(45, 165, 80, 180) if is_on else (6, 26, 12, 200), outline=(74, 255, 122, 230))
            draw.text((bx0 + 8, by0 + 4), bname, font=f_sm, fill=(220, 255, 230, 255) if is_on else (65, 180, 95, 200))
        info_l1 = sutherland_info[0] if sutherland_info else "POET    17 POINTS  42 CONSTRAINTS  RELAXATION  75 PASSES  MAX |E|  0.04 MM"
        info_l2 = sutherland_info[1] if sutherland_info and len(sutherland_info) > 1 else "TEMPLE  19 CARDS   88 CONSTRAINTS  WAVE-FLAT   0.00 MM    OCCLUSION: ALTERNATING"
        draw.text((44, H - 64), info_l1, font=f_sm, fill=(68, 225, 112, 230))
        draw.text((44, H - 42), info_l2, font=f_sm, fill=(68, 225, 112, 210))
        return

    if style == "reiniger":
        # Gold-outlined Lotte Reiniger filigree cartouche at bottom (`02-reiniger` style)
        f_sub = get_font(23, italic=True)
        tb = draw.textbbox((0, 0), text, font=f_sub)
        tw = tb[2] - tb[0]
        cx0 = (W - tw) // 2 - 28
        cx1 = (W + tw) // 2 + 28
        cy0, cy1 = H - 68, H - 18
        draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=10, fill=(8, 7, 11, 245), outline=(198, 156, 98, 255), width=2)
        draw.ellipse([cx0 - 5, (cy0 + cy1) // 2 - 4, cx0 + 3, (cy0 + cy1) // 2 + 4], fill=(198, 156, 98, 255))
        draw.ellipse([cx1 - 3, (cy0 + cy1) // 2 - 4, cx1 + 5, (cy0 + cy1) // 2 + 4], fill=(198, 156, 98, 255))
        draw.text(((W - tw) // 2, cy0 + 11), text, font=f_sub, fill=(244, 232, 208, 255))
        return

    if style == "gilliam":
        # Terry Gilliam cut-out cream paper speech strip (`01-gilliam` style)
        f_sub = get_font(22, bold=False)
        tb = draw.textbbox((0, 0), text, font=f_sub)
        tw = tb[2] - tb[0]
        card = Image.new("RGBA", (tw + 36, 42), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rectangle([2, 2, tw + 33, 39], fill=(245, 239, 222, 248), outline=(32, 28, 24, 255), width=2)
        cd.text((18, 8), text, font=f_sub, fill=(22, 20, 18, 255))
        rot = card.rotate(1.4 * math.sin(t * 0.8), resample=Image.Resampling.BICUBIC, expand=True)
        canvas_pil.alpha_composite(rot, ((W - rot.width) // 2, H - 72))
        return

    # Classic quiet literary serif subtitle (`05-norstein`, `07-foldes`, `09-igarashi`, `18-cartoon-saloon`, `33-inverse-kinematics` style)
    f_sub = get_font(23, bold=False)
    tb = draw.textbbox((0, 0), text, font=f_sub)
    tw = tb[2] - tb[0]
    sx = (W - tw) // 2
    sy = H - 48
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (1, 2)]:
        draw.text((sx + dx, sy + dy), text, font=f_sub, fill=(8, 10, 14, 215))
    draw.text((sx, sy), text, font=f_sub, fill=(246, 240, 228, 252))


# ═════════════════════════════════════════════════════════════════════════════
# THE 14 HANDMADE WORLD & STAGE BUILDERS (MODELLED ON `bolas_repo/paeleo/handmade`)
# ═════════════════════════════════════════════════════════════════════════════

_MOURIS_TILES = None


def _get_mouris_tiles():
    """Builds a bank of rich 28x28 miniature archive & motif tiles from Poems 01-14 for Poem 14 (`04-mouris`)."""
    global _MOURIS_TILES
    if _MOURIS_TILES is not None:
        return _MOURIS_TILES
    tiles = []
    # 1. Sample real 28x28 miniature tiles from existing WYGWYL multiplane plates & cut props
    for p_num, mspec in R2.POEM_SOURCE_MANIFEST.items():
        for pid in mspec["plates"][:1]:
            layers = R2.load_multiplane_plate_dir(pid)
            pl_im = layers.get("plate") or layers.get("mid")
            if pl_im is not None:
                rgb_pl = pl_im.convert("RGB")
                for cx_f, cy_f in [(0.30, 0.45), (0.68, 0.52)]:
                    x0 = int(W * cx_f)
                    y0 = int(H * cy_f)
                    crop = rgb_pl.crop((x0, y0, x0 + 140, y0 + 140)).resize((28, 28), Image.Resampling.LANCZOS)
                    d_c = ImageDraw.Draw(crop)
                    d_c.rectangle([0, 0, 27, 27], outline=(18, 18, 24), width=1)
                    tiles.append(np.array(crop))
        for sheet_id, cut_id in mspec["cuts"][:1]:
            pr_im = R2.load_cut_prop(sheet_id, cut_id)
            if pr_im is not None:
                bg_t = Image.new("RGBA", (28, 28), (34, 38, 52, 255))
                R2.paste_centered(bg_t, pr_im, 14, 14, target_h=24)
                rgb_t = bg_t.convert("RGB")
                d_c = ImageDraw.Draw(rgb_t)
                d_c.rectangle([0, 0, 27, 27], outline=(18, 18, 24), width=1)
                tiles.append(np.array(rgb_t))

    # 2. Include 26 high-contrast miniature graphic motif icons from Poems 01-13
    palettes = [
        ((28, 38, 56), (90, 167, 255), "circle"),      # P01 blue vape ember
        ((42, 28, 58), (245, 195, 110), "arch"),       # P02 Reiniger arch
        ((95, 64, 38), (110, 165, 210), "rose"),       # P03 chapel rose window
        ((38, 46, 68), (248, 212, 72), "bloom"),       # P04 mustard seed bloom
        ((122, 54, 44), (252, 224, 128), "stars"),     # P05 KIN constellation
        ((32, 62, 92), (255, 215, 115), "window"),     # P06 Atlantis window
        ((24, 32, 52), (248, 246, 240), "daisy"),      # P07 daisy petals
        ((34, 44, 74), (135, 235, 255), "moons"),      # P08 3 crescent moons
        ((26, 38, 68), (242, 198, 118), "booth"),      # P09 harbour phone booth
        ((64, 48, 82), (215, 62, 52), "wheel"),        # P10 ARAP motorcycle wheel
        ((6, 22, 12), (78, 255, 128), "temple"),       # P11 Sketchpad green temple
        ((118, 92, 128), (252, 214, 112), "hourglass"),# P12 Gilliam hourglass
        ((168, 162, 148), (228, 52, 48), "poppy"),     # P13 Foldes scarlet poppy
    ]
    for bg, fg, kind in palettes:
        for inv in (0, 1):
            b_col = bg if inv == 0 else tuple(min(255, int(c * 1.35)) for c in bg)
            im = Image.new("RGB", (28, 28), b_col)
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 27, 27], outline=(18, 18, 24), width=1)
            if kind in ("circle", "bloom", "poppy", "wheel"):
                d.ellipse([6, 6, 21, 21], fill=fg, outline=(24, 24, 30))
                d.ellipse([11, 11, 16, 16], fill=b_col)
            elif kind in ("arch", "window", "booth"):
                d.rectangle([7, 5, 20, 23], fill=fg, outline=(24, 24, 30))
                d.line([(7, 14), (20, 14)], fill=b_col, width=2)
            elif kind == "temple":
                d.polygon([(4, 10), (14, 4), (23, 10)], outline=fg)
                for cx in (7, 14, 20):
                    d.line([(cx, 10), (cx, 23)], fill=fg, width=2)
            elif kind == "hourglass":
                d.polygon([(7, 5), (20, 5), (7, 22), (20, 22)], fill=fg)
            else:
                d.ellipse([5, 5, 13, 13], fill=fg)
                d.ellipse([15, 13, 22, 20], fill=fg)
                d.line([(9, 9), (18, 16)], fill=fg, width=2)
            tiles.append(np.array(im))
    _MOURIS_TILES = tiles
    return _MOURIS_TILES


def _draw_engraving_rect(pil_im, box, base_rgb, hatch_step=5, angle_mode=0, border_rgb=None):
    """Fills a rectangle `box=(x0,y0,x1,y1)` with Terry Gilliam 19th-century steel-engraving cross-hatching (`01-gilliam`)."""
    x0, y0, x1, y1 = max(0, int(box[0])), max(0, int(box[1])), min(W, int(box[2])), min(H, int(box[3]))
    if x1 <= x0 or y1 <= y0:
        return
    arr = np.array(pil_im)
    sub = arr[y0:y1, x0:x1, :3].astype(np.float32)
    yy, xx = np.indices((y1 - y0, x1 - x0))
    sub[:, :, 0] = base_rgb[0]
    sub[:, :, 1] = base_rgb[1]
    sub[:, :, 2] = base_rgb[2]
    if angle_mode == 0:
        h1 = ((xx + yy) % hatch_step == 0)
        h2 = ((xx - yy) % (hatch_step + 2) == 0)
    elif angle_mode == 1:
        h1 = (yy % hatch_step == 0)
        h2 = ((xx + yy * 2) % (hatch_step + 3) == 0)
    else:
        h1 = ((xx + (4 * np.sin(yy / 9.0)).astype(int)) % hatch_step == 0)
        h2 = ((yy + (4 * np.cos(xx / 11.0)).astype(int)) % (hatch_step + 1) == 0)
    sub[h1] *= 0.48
    sub[h2] *= 0.62
    arr[y0:y1, x0:x1, :3] = np.clip(sub, 0, 255).astype(np.uint8)
    arr[y0:y1, x0:x1, 3] = 255
    pil_im.paste(Image.fromarray(arr[y0:y1, x0:x1], "RGBA"), (x0, y0))
    if border_rgb is not None:
        d = ImageDraw.Draw(pil_im, "RGBA")
        d.rectangle([x0, y0, x1, y1], outline=(*border_rgb, 255), width=2)


def render_handmade_poem_frame(num, i, t, u, verse_line):
    """
    Renders frame `i` (`t` seconds, normalized `u in [0,1]`) for Poem `num` (`1..14`)
    entirely from the bottom up in that poem's assigned SCION formal language.
    Returns a `(720, 1280, 3)` BGR numpy array ready for video encoding & still saving.
    """
    canvas = Image.new("RGBA", (W, H), (14, 16, 22, 255))
    draw = ImageDraw.Draw(canvas, "RGBA")
    walk_ph = t * 5.6

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 01 · SCION-005 · YURI NORSTEIN ATMOSPHERIC MULTIPLANE (`05-norstein`)
    # ═════════════════════════════════════════════════════════════════════════
    if num == 1:
        # 1. Far plane: twilight harbor & Severn Bridge multiplane plate behind clapboard wall
        for y in range(H):
            k = y / float(H)
            r = int(lerp(24, 52, k))
            g = int(lerp(32, 58, k))
            b = int(lerp(48, 72, k))
            draw.line([(0, y), (W, y)], fill=(r, g, b, 255))
        R2.blend_multiplane_underlay(canvas, "gen_872d16167d_50" if u > 0.45 else "gen_a63bb494b1_10", cam_x=(u - 0.5) * 42.0, opacity=0.52)
        draw = ImageDraw.Draw(canvas, "RGBA")
        # Mid-back clapboard house wall with horizontal siding lines (`05-norstein` style)
        draw.rectangle([0, 40, 820, 565], fill=(42, 52, 62, 238))
        for sy in range(52, 565, 22):
            draw.line([(0, sy), (820, sy)], fill=(30, 38, 46, 230), width=2)
        # Warm lit doorway on left + sliding window on right coupled to Poet's step velocity
        poet_x = int(lerp(230, 595, smoothstep(0.05, 0.65, u)))
        win_x = poet_x + 280
        # Doorway at x=140..280 with warm Norstein amber glow + light spill on floorboards
        draw.rectangle([125, 130, 295, 565], fill=(78, 86, 94, 255))
        draw.rectangle([142, 148, 278, 565], fill=(212, 162, 102, 255))
        # Soft interior gradient inside doorway
        for dy in range(148, 565, 4):
            alpha_d = int(110 * abs((dy - 340) / 225.0))
            draw.rectangle([142, dy, 278, dy + 4], fill=(115, 82, 48, alpha_d))
        # Porch floorboards (`y = 565..670`) with warm light trapezium spill + real cut catwalk & chandelier
        draw.rectangle([0, 565, W, H], fill=(56, 58, 62, 255))
        for py in range(572, 668, 14):
            draw.line([(0, py), (W, py)], fill=(40, 42, 46, 220), width=1)
        spill_poly = [(142, 565), (278, 565), (365, 668), (85, 668)]
        draw.polygon(spill_poly, fill=(228, 188, 132, 130))
        R2.paste_centered(canvas, R2.load_cut_prop("01.props.chandeliers", "p01"), 1020, 140, target_h=145, alpha_mul=0.72)
        R2.paste_centered(canvas, R2.load_cut_prop("01.hero.catwalk", "p01"), 1020, 520, target_w=460, alpha_mul=0.68)

        # Sliding window frame on wall rail (`d(window_x)/dt == d(poet_x)/dt`) + real cut window prop
        draw.rectangle([win_x - 68, 185, win_x + 68, 425], fill=(24, 30, 38, 255), outline=(92, 102, 114, 255), width=6)
        R2.paste_centered(canvas, R2.load_cut_prop("01.props.window", "p01"), win_x, 305, target_h=235, alpha_mul=0.82)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.line([(win_x - 68, 305), (win_x + 68, 305)], fill=(92, 102, 114, 255), width=4)
        draw.line([(win_x, 185), (win_x, 425)], fill=(92, 102, 114, 255), width=4)

        # Articulated EX figure (strictly back-turned at window/rail, tipping into fog at u > 0.56)
        fade_chars = clamp(1.0 - smoothstep(0.78, 0.92, u), 0.0, 1.0)
        ex_drop = int(smoothstep(0.56, 0.82, u) * 240)
        if fade_chars > 0.02:
            if u > 0.35:
                # Deep ballroom waltz couple visible in far Z-plane on right
                draw_articulated_human(
                    canvas, 1030, 558, height=168.0, facing=1.0,
                    walk_phase=walk_ph * 0.8, walking=True, reach=0.45,
                    style="norstein", rim_rgb=(245, 200, 120), alpha=int(185 * fade_chars),
                    char_id="party_gentleman", view="SIDE"
                )
                draw_articulated_human(
                    canvas, 1095, 558, height=164.0, facing=-1.0,
                    walk_phase=walk_ph * 0.8 + math.pi, walking=True, reach=0.45,
                    style="norstein", rim_rgb=(245, 200, 120), alpha=int(185 * fade_chars),
                    char_id="party_woman_gown", view="3Q"
                )
            draw_articulated_human(
                canvas, win_x + 35, 588 + ex_drop, height=205.0, facing=1.0,
                walk_phase=walk_ph * 0.4, walking=False, lean_deg=6.0 + smoothstep(0.52, 0.75, u) * 28.0,
                style="norstein", coat_rgb=(46, 50, 62), pants_rgb=(32, 36, 46),
                skin_rgb=(52, 54, 64), rim_rgb=(245, 175, 105), alpha=int(255 * fade_chars),
                char_id="ex_olive_bomber", view="BACK"
            )
            # Articulated Poet stepping toward her with low offered hand / reading book
            draw_articulated_human(
                canvas, poet_x, 592 + int(ex_drop * 0.7), height=215.0, facing=1.0,
                walk_phase=walk_ph, walking=(0.08 < u < 0.65), lean_deg=8.0,
                reach=smoothstep(0.15, 0.55, u) * 0.7, style="norstein",
                coat_rgb=(48, 52, 66), pants_rgb=(36, 40, 52),
                skin_rgb=(175, 132, 102), rim_rgb=(255, 195, 125), alpha=int(255 * fade_chars),
                char_id="poet_black_tshirt", view="SIDE"
            )

        # Norstein multiplane fog gauze + sodium-orange mist veil claiming bedroom L->R
        arr = np.array(canvas).astype(np.float32)
        yy, xx = np.meshgrid(np.arange(H, dtype=np.float32), np.arange(W, dtype=np.float32), indexing="ij")
        gauze = 0.5 + 0.5 * np.sin((xx * 0.006) + (yy * 0.009) - t * 0.65) * np.cos((xx * 0.004) - (yy * 0.007) + t * 0.4)
        gauze_mask = np.clip((yy - 220.0) / 380.0, 0.15, 1.0) * gauze * 0.34
        haze_front = W * clamp((u - 0.04) * 1.15, 0.0, 0.92)
        sodium_veil = np.clip((haze_front - xx + 45.0 * np.sin(yy / 48.0 + t * 1.4)) / 160.0, 0.0, 1.0) * 0.48
        fog_rgb = np.dstack([
            155.0 * (1.0 - sodium_veil) + 235.0 * sodium_veil,
            165.0 * (1.0 - sodium_veil) + 135.0 * sodium_veil,
            180.0 * (1.0 - sodium_veil) + 55.0 * sodium_veil,
        ])
        w_fog = np.clip(gauze_mask + sodium_veil * 0.65, 0.0, 0.78)[:, :, None]
        arr[:, :, :3] = arr[:, :, :3] * (1.0 - w_fog) + fog_rgb * w_fog

        # Out-of-focus foreground window mullion (`Z = 2.2`, blurred bar passing camera like `05-norstein`)
        mullion_x = int(680 - (poet_x - 230) * 0.85)
        mullion = np.zeros((H, W), dtype=np.float32)
        mullion[:, max(0, mullion_x - 22) : min(W, mullion_x + 22)] = 0.52
        mullion = cv2.GaussianBlur(mullion, (51, 51), 18.0)[:, :, None]
        arr[:, :, :3] = arr[:, :, :3] * (1.0 - mullion) + 18.0 * mullion

        # Fine Norstein film grain
        rng = np.random.default_rng(1000 + i)
        grain = rng.normal(0.0, 5.5, (H, W, 1)).astype(np.float32)
        arr[:, :, :3] = np.clip(arr[:, :, :3] + grain, 0, 255)

        # Final threshold state (u > 0.80): room dissolves to dark fog; only #5aa7ff blue vape ember breathes
        if u > 0.80:
            dark_k = smoothstep(0.80, 0.93, u) * 0.88
            arr[:, :, :3] *= (1.0 - dark_k)
        canvas = Image.fromarray(arr.astype(np.uint8), "RGBA")
        if u > 0.78:
            ember_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d2 = ImageDraw.Draw(ember_layer, "RGBA")
            ex_c, ey_c = int(W * 0.64), int(H * 0.46)
            r_em = int(8 + 3 * math.sin(t * 7.5))
            d2.ellipse([ex_c - r_em * 3, ey_c - r_em * 3, ex_c + r_em * 3, ey_c + r_em * 3], fill=(90, 167, 255, 130))
            for wi in range(5):
                wy_w = ey_c - 14 - wi * 16 - int((t * 18) % 14)
                wx_w = ex_c + int(8 * math.sin(wi * 1.4 + t * 3.0))
                d2.ellipse([wx_w - 10 - wi * 2, wy_w - 6, wx_w + 10 + wi * 2, wy_w + 6], fill=(120, 185, 255, max(15, 75 - wi * 12)))
            ember_layer = ember_layer.filter(ImageFilter.GaussianBlur(radius=6.0))
            d3 = ImageDraw.Draw(ember_layer, "RGBA")
            d3.ellipse([ex_c - r_em, ey_c - r_em, ex_c + r_em, ey_c + r_em], fill=(90, 167, 255, 245))
            d3.ellipse([ex_c - 4, ey_c - 4, ex_c + 4, ey_c + 4], fill=(215, 240, 255, 255))
            canvas.alpha_composite(ember_layer)

        draw_clean_subtitle(canvas, verse_line, style="default", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 02 · SCION-002 · LOTTE REINIGER SILHOUETTE THEATRE (`02-reiniger`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 2:
        # 1. Backlit wax-paper dusk/amber/violet light-table gradient (`02-reiniger` style)
        strobe = 0.5 + 0.5 * math.sin(t * 5.2)
        arr = np.zeros((H, W, 4), dtype=np.uint8)
        yy, xx = np.meshgrid(np.arange(H, dtype=np.float32), np.arange(W, dtype=np.float32), indexing="ij")
        ky = yy / float(H)
        radial = np.exp(-((xx - 560.0) ** 2 + (yy - 440.0) ** 2) / (2.0 * 340.0 ** 2))
        r_ch = np.clip(45 + 185 * (ky ** 0.85) + 48 * radial + 22 * strobe, 0, 255)
        g_ch = np.clip(32 + 145 * (ky ** 1.1) + 42 * radial + 14 * strobe, 0, 255)
        b_ch = np.clip(82 + 95 * (1.0 - abs(ky - 0.45)) + 20 * radial, 0, 255)
        arr[:, :, 0] = r_ch.astype(np.uint8)
        arr[:, :, 1] = g_ch.astype(np.uint8)
        arr[:, :, 2] = b_ch.astype(np.uint8)
        arr[:, :, 3] = 255
        canvas = Image.fromarray(arr).convert("RGBA")
        R2.blend_multiplane_underlay(canvas, "gen_a63bb494b1_50", cam_x=(u - 0.5) * 32.0, opacity=0.36, style_mode="reiniger")
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Distant silhouette hills + crescent moon + delicate scissor-cut tree on right
        hill_pts = [(420, 585)] + [(x, int(495 + 24 * math.sin(x * 0.011))) for x in range(420, W + 20, 20)] + [(W, 585)]
        draw.polygon(hill_pts, fill=(195, 155, 115, 165))
        # Crescent moon at (1010, 185)
        draw.ellipse([985, 160, 1035, 210], fill=(252, 248, 238, 255))
        draw.ellipse([997, 154, 1045, 202], fill=(int(r_ch[180, 1010]), int(g_ch[180, 1010]), int(b_ch[180, 1010]), 255))
        # Scissor-cut silhouette tree at x=730 + silhouetted hazard car below window
        car_sil = R2.style_reiniger_silhouette(R2.load_cut_prop("02.props.car", "p01"), rim_rgb=(255, 210, 95))
        R2.paste_centered(canvas, car_sil, 950, 548, target_w=210, alpha_mul=0.88)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.polygon([(715, 585), (728, 585), (722, 360), (712, 360)], fill=(95, 78, 72, 220))
        for br_ang, br_l in [(-0.7, 130), (-0.35, 150), (0.15, 145), (0.55, 125)]:
            bx1 = int(718 + math.sin(br_ang) * br_l)
            by1 = int(385 - math.cos(br_ang) * br_l)
            draw.line([(718, 385), (bx1, by1)], fill=(95, 78, 72, 220), width=4)
            draw.ellipse([bx1 - 36, by1 - 22, bx1 + 36, by1 + 22], fill=(95, 78, 72, 200))

        # Left bedroom wall in Reiniger silhouette masonry + arched glowing doorway/mirror + Venetian blind window
        draw.rectangle([0, 35, 455, 585], fill=(32, 26, 36, 255))
        for by in range(45, 585, 24):
            draw.line([(0, by), (455, by)], fill=(54, 46, 58, 220), width=1)
        # Glowing arched mirror/doorway (`x = 265..425`)
        draw.rounded_rectangle([265, 175, 425, 585], radius=75, fill=(252, 242, 165, 255), outline=(10, 9, 14, 255), width=8)
        # Window with scissored Venetian blind slats (`x = 48..210, y = 245..410`) + real cut blinds-height prop
        draw.rectangle([48, 245, 210, 410], fill=(242, 185, 105, 255), outline=(10, 9, 14, 255), width=6)
        blinds_sil = R2.style_reiniger_silhouette(R2.load_cut_prop("02.props.blinds-height", "p01"), rim_rgb=(245, 195, 105))
        R2.paste_centered(canvas, blinds_sil, 129, 328, target_w=148, alpha_mul=0.72)
        draw = ImageDraw.Draw(canvas, "RGBA")
        slat_open = smoothstep(0.35, 0.72, u)
        slat_h = max(2, int(9 * (1.0 - 0.65 * slat_open)))
        for sy in range(254, 404, 15):
            draw.rectangle([54, sy, 204, sy + slat_h], fill=(10, 9, 14, 255))
        # Concentric filigree telephone ring waves (`u < 0.45`)
        if u < 0.45:
            for ri in range(3):
                rad = int(((t * 65 + ri * 42) % 130) + 18)
                draw.ellipse([128 - rad, 328 - rad, 128 + rad, 328 + rad], outline=(255, 225, 140, 175), width=2)

        # Articulated Reiniger silhouettes: Young Poet (age 6, h=178) & Ghost Child (age 7, h=196 = +18px taller!)
        draw_articulated_human(
            canvas, 560, 585, height=178.0, facing=1.0, walk_phase=walk_ph,
            walking=(0.15 < u < 0.45), lean_deg=5.0, reach=smoothstep(0.45, 0.85, u),
            style="reiniger", rim_rgb=(255, 215, 125), char_id="young_poet", view="SIDE"
        )
        draw_articulated_human(
            canvas, 675, 585, height=196.0, facing=-1.0, walk_phase=walk_ph,
            walking=False, lean_deg=4.0, reach=smoothstep(0.40, 0.75, u),
            style="reiniger", rim_rgb=(175, 230, 255), char_id="ghost_child", view="SIDE"
        )

        # Filigree silhouette tambourine (`02.props.tambourine`) handed over & hurled toward harbour at u > 0.62
        tamb_u = smoothstep(0.62, 0.96, u)
        tx = int(lerp(615, 1120, tamb_u))
        ty = int(lerp(465, 240, tamb_u) - 85 * math.sin(tamb_u * math.pi))
        tamb_sil = R2.style_reiniger_silhouette(R2.load_cut_prop("02.props.tambourine", "p01"), rim_rgb=(252, 212, 118))
        R2.paste_centered(canvas, tamb_sil, tx, ty, target_h=56, rot_deg=t * 95.0, alpha_mul=0.95)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.ellipse([tx - 24, ty - 24, tx + 24, ty + 24], outline=(252, 212, 118, 255), width=2)
        for ja in range(6):
            ang = ja * (math.pi / 3.0) + t * 6.0
            jx, jy = int(tx + 24 * math.cos(ang)), int(ty + 24 * math.sin(ang))
            draw.ellipse([jx - 4, jy - 4, jx + 4, jy + 4], fill=(252, 212, 118, 255))

        # Reiniger stage floor + diamond latticework fretwork + scalloped lace upper border (`02-reiniger` signature!)
        draw.rectangle([0, 585, W, H], fill=(8, 7, 11, 255))
        draw.line([(0, 588), (W, 588)], fill=(198, 156, 98, 255), width=2)
        for lx in list(range(18, 260, 26)) + list(range(640, 1160, 26)):
            for ly in range(604, 704, 24):
                pts_d = [(lx, ly - 8), (lx + 9, ly), (lx, ly + 8), (lx - 9, ly)]
                draw.polygon(pts_d, fill=(212, 164, 108, 235))
        # Upper scalloped paper-lace border & hanging lantern
        draw.rectangle([0, 0, W, 36], fill=(8, 7, 11, 255))
        draw.rectangle([455, 62, W, 88], fill=(8, 7, 11, 255))
        for sx in range(12, W, 24):
            draw.ellipse([sx - 10, 24, sx + 10, 44], fill=(8, 7, 11, 255))
            if sx > 460:
                draw.ellipse([sx - 10, 78, sx + 10, 98], fill=(8, 7, 11, 255))
                draw.ellipse([sx - 3, 72, sx + 3, 78], fill=(212, 164, 108, 220))
        # Hanging silhouette lantern at x=820
        draw.line([(820, 88), (820, 138)], fill=(8, 7, 11, 255), width=3)
        draw.polygon([(806, 138), (834, 138), (830, 182), (810, 182)], fill=(252, 238, 185, 255), outline=(8, 7, 11, 255), width=4)

        draw_clean_subtitle(canvas, verse_line, style="reiniger", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 03 · SCION-049 · OPEN-CONTENT ATELIER & RELIC STAGE (`49-atelier`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 3:
        # Painterly oil-and-timber ruined harbour chapel interior (STRICTLY 0 HUMAN PUPPETS!)
        for y in range(H):
            k = y / float(H)
            draw.line([(0, y), (W, y)], fill=(int(lerp(36, 22, k)), int(lerp(42, 26, k)), int(lerp(48, 30, k)), 255))
        pl_id = "gen_872d16167d_50" if u < 0.34 else ("gen_933cc247ea_10" if u < 0.68 else "gen_e315da34f9_30")
        R2.blend_multiplane_underlay(canvas, pl_id, cam_x=(u - 0.5) * 28.0, opacity=0.45, style_mode="gilliam")
        # Real cut chapel state progression (`chapel` -> `chapel.decay` -> `chapel.ruin`)
        ch_sheet = "03.hero.chapel" if u < 0.34 else ("03.hero.chapel.decay" if u < 0.68 else "03.hero.chapel.ruin")
        ch_im = R2.style_gilliam_engraved_cutout(R2.load_cut_prop(ch_sheet, "p01"))
        R2.paste_centered(canvas, ch_im, 820, 320, target_h=390, alpha_mul=0.76)

        # Left warm timber sacristy room (`49-open-content-atelier` warm wood tones)
        _draw_engraving_rect(canvas, (0, 0, 410, 580), (112, 76, 44), hatch_step=6, angle_mode=1)
        _draw_engraving_rect(canvas, (45, 75, 345, 580), (154, 110, 64), hatch_step=7, angle_mode=0, border_rgb=(72, 46, 24))
        # Rose window (`03.props.rose-window`) in upper chapel wall (`x=200, y=215`) breached by tambourine
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.ellipse([125, 140, 275, 290], fill=(68, 92, 118, 255), outline=(58, 38, 20, 255), width=8)
        rose_im = R2.style_gilliam_engraved_cutout(R2.load_cut_prop("03.props.rose-window", "p01"))
        R2.paste_centered(canvas, rose_im, 200, 215, target_h=148, alpha_mul=0.92)
        draw = ImageDraw.Draw(canvas, "RGBA")
        for a_deg in range(0, 360, 45):
            ar = math.radians(a_deg)
            draw.line([(200, 215), (int(200 + 72 * math.cos(ar)), int(215 + 72 * math.sin(ar)))], fill=(48, 32, 18, 255), width=3)

        # Right twilight harbour trees & chapel nave flagstones
        for tx, tr in [(540, 95), (720, 120), (920, 110), (1110, 130)]:
            draw.line([(tx, 580), (tx - 18, 240)], fill=(28, 30, 26, 205), width=10)
            draw.ellipse([tx - tr, 150, tx + tr, 340], fill=(32, 38, 32, 185))
        _draw_engraving_rect(canvas, (0, 580, W, H), (78, 62, 46), hatch_step=5, angle_mode=1)
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Counter 1: 6 carved oak pews vanishing one by one (`6 -> 0`)
        pews_left = max(0, 6 - int(u * 6.8))
        for pi in range(6):
            px0 = 445 + pi * 128
            if pi < pews_left:
                _draw_engraving_rect(canvas, (px0, 485, px0 + 104, 578), (118, 82, 48), hatch_step=5, angle_mode=0, border_rgb=(215, 195, 160))
            else:
                draw = ImageDraw.Draw(canvas, "RGBA")
                draw.rectangle([px0, 485, px0 + 104, 578], outline=(120, 125, 132, 110), width=1)

        # Counter 2: Rafter cobweb catenaries (`03.props.cobwebs`) growing across ceiling (`u > 0.12`)
        web_n = int(smoothstep(0.10, 0.70, u) * 9)
        if web_n > 0:
            cob_im = R2.style_gilliam_engraved_cutout(R2.load_cut_prop("03.props.cobwebs", "p01"))
            R2.paste_centered(canvas, cob_im, 540, 92, target_w=260, alpha_mul=min(0.85, web_n * 0.12))
            R2.paste_centered(canvas, cob_im, 980, 96, target_w=260, flip_x=True, alpha_mul=min(0.85, web_n * 0.12))
        draw = ImageDraw.Draw(canvas, "RGBA")
        for wi in range(web_n):
            wx0 = 380 + wi * 95
            draw.arc([wx0, -35, wx0 + 160, 135 + wi * 12], start=0, end=180, fill=(215, 212, 202, 165), width=1)

        # Counter 3: Lightning fork splitting wedding gifts (`03.props.gifts-bread-cups`) on altar (`0.18 < u < 0.55`)
        if u > 0.16:
            split_dx = int(smoothstep(0.24, 0.45, u) * 24)
            _draw_engraving_rect(canvas, (815 - split_dx, 425, 875 - split_dx, 482), (185, 165, 135), hatch_step=4, border_rgb=(45, 35, 25))
            _draw_engraving_rect(canvas, (882 + split_dx, 432, 942 + split_dx, 482), (175, 145, 125), hatch_step=4, border_rgb=(45, 35, 25))
            gifts_im = R2.style_gilliam_engraved_cutout(R2.load_cut_prop("03.props.gifts-bread-cups", "p01"))
            R2.paste_centered(canvas, gifts_im, 880, 445, target_h=115, alpha_mul=0.92)
            if 0.18 <= u <= 0.48:
                draw = ImageDraw.Draw(canvas, "RGBA")
                bolt = [(880, 40), (855, 165), (895, 250), (862, 345), (880, 445)]
                draw.line(bolt, fill=(255, 248, 195, 250), width=5)
                draw.line([(895, 250), (935, 335)], fill=(255, 248, 195, 220), width=3)

        # Counter 4: Moldering sacramental bread & 2 cracked teacups (`u > 0.48`)
        if u > 0.48:
            draw = ImageDraw.Draw(canvas, "RGBA")
            mold = smoothstep(0.48, 0.85, u)
            bread_c = (int(lerp(185, 82, mold)), int(lerp(142, 118, mold)), int(lerp(88, 76, mold)), 255)
            draw.ellipse([630, 542, 692, 576], fill=bread_c, outline=(38, 32, 26, 255), width=2)
            for cx in (725, 768):
                draw.rectangle([cx, 548, cx + 26, 576], fill=(235, 232, 222, 255), outline=(42, 38, 34, 255), width=2)
                draw.line([(cx + 12, 548), (cx + 16, 562), (cx + 10, 576)], fill=(28, 24, 22, 255), width=2)

        # Counter 5: Two diverging trails of mud shoe-prints walking out of phase
        draw = ImageDraw.Draw(canvas, "RGBA")
        steps_n = int(smoothstep(0.55, 0.92, u) * 12)
        for s_i in range(steps_n):
            sx_a = 620 - s_i * 38
            sy_a = 612 + (s_i % 2) * 14
            sx_b = 680 + s_i * 42
            sy_b = 624 - (s_i % 2) * 14
            draw.ellipse([sx_a - 11, sy_a - 5, sx_a + 11, sy_a + 5], fill=(42, 32, 22, 230), outline=(185, 168, 140, 160))
            draw.ellipse([sx_b - 11, sy_b - 5, sx_b + 11, sy_b + 5], fill=(42, 32, 22, 230), outline=(185, 168, 140, 160))

        # Counter 6: Suspended tambourine (`02.props.tambourine`) -> drops & shatters (`03.props.tambourine-broken`) at u > 0.80
        drop_u = smoothstep(0.78, 0.94, u)
        ty = int(lerp(265, 588, drop_u * drop_u))
        if drop_u < 0.90:
            draw.line([(360, 0), (360, ty - 38)], fill=(195, 175, 135, 180), width=1)
            tamb_intact = R2.style_gilliam_engraved_cutout(R2.load_cut_prop("02.props.tambourine", "p01"))
            R2.paste_centered(canvas, tamb_intact, 360, ty, target_h=78, alpha_mul=0.95)
        else:
            tamb_brk = R2.style_gilliam_engraved_cutout(R2.load_cut_prop("03.props.tambourine-broken", "p01"))
            R2.paste_centered(canvas, tamb_brk, 360, 588, target_h=88, alpha_mul=0.96)
            draw = ImageDraw.Draw(canvas, "RGBA")
            for fi, dx_f in enumerate([-48, -22, 14, 38, 62]):
                draw.arc([340 + dx_f, 572, 382 + dx_f, 602], start=20 * fi, end=140 + 20 * fi, fill=(195, 162, 105, 255), width=4)
                draw.ellipse([352 + dx_f, 586, 362 + dx_f, 596], fill=(245, 208, 95, 255))

        draw_clean_subtitle(canvas, verse_line, style="gilliam", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 04 · SCION-033 · INVERSE KINEMATICS & CARVED AUTOMATON (`33-ik`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 4:
        # 3D perspective stage modeled directly on `33-inverse-kinematics/stills/still_09.0s.jpg` + real shore plates
        for y in range(H):
            k = y / float(H)
            draw.line([(0, y), (W, y)], fill=(int(lerp(32, 128, k)), int(lerp(36, 98, k)), int(lerp(62, 112, k)), 255))
        R2.blend_multiplane_underlay(canvas, "world_ef9f6c7e_3" if u > 0.5 else "gen_ca6878be91_90", cam_x=(u - 0.5) * 36.0, opacity=0.46)
        R2.paste_centered(canvas, R2.load_cut_prop("04.hero.viaduct", "p01"), 910, 315, target_w=680, alpha_mul=0.58)
        draw = ImageDraw.Draw(canvas, "RGBA")
        # Distant horizon & dark silhouette tree clusters (`33-inverse-kinematics` style)
        draw.rectangle([520, 345, W, H], fill=(42, 44, 58, 220))
        draw.line([(975, 120), (965, 420)], fill=(18, 20, 28, 255), width=14)
        for cx, cy, cr in [(640, 95, 65), (720, 145, 58), (610, 195, 52), (835, 138, 38), (985, 95, 78), (1095, 130, 68), (1185, 185, 64)]:
            draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(18, 22, 32, 235))

        # Left perspective house wall + glowing interior doorway with table lamp (`33-ik` signature)
        wall_poly = [(0, 0), (590, 0), (590, 525), (0, 685)]
        draw.polygon(wall_poly, fill=(48, 56, 76, 255))
        for wy in range(25, 640, 26):
            y_r = int(wy * 0.78)
            draw.line([(0, wy), (590, y_r)], fill=(36, 42, 58, 220), width=2)
        # Perspective doorway (`x=185..325`) with warm lamp inside
        door_poly = [(185, 32), (328, 72), (328, 635), (185, 672)]
        draw.polygon(door_poly, fill=(172, 142, 92, 255), outline=(88, 96, 115, 255), width=6)
        # Table lamp inside room
        draw.polygon([(232, 212), (272, 212), (282, 248), (222, 248)], fill=(252, 236, 178, 255))
        draw.line([(252, 248), (252, 315)], fill=(95, 78, 52, 255), width=3)

        # 3D perspective boardwalk incline deck (`y = 525..720`) + warm light spill
        deck_poly = [(0, 685), (590, 525), (1245, 608), (1200, 720), (0, 720)]
        draw.polygon(deck_poly, fill=(58, 56, 64, 255))
        light_cone = [(185, 672), (328, 635), (960, 720), (310, 720)]
        draw.polygon(light_cone, fill=(195, 162, 118, 145))
        for pi in range(18):
            u_p = pi / 17.0
            px0, py0 = int(lerp(0, 590, u_p)), int(lerp(685, 525, u_p))
            px1, py1 = int(lerp(310, 1245, u_p)), int(lerp(720, 608, u_p))
            draw.line([(px0, py0), (px1, py1)], fill=(42, 40, 48, 210), width=1)

        # 9 Golden Mustard-Seed Blooms (`04.props.faith-blooms`) on 2-bone IK stems rotating to face the climbing Poet
        poet_x = int(lerp(940, 430, u))
        poet_y = int(lerp(645, 585, u))
        bloom_im = R2.load_cut_prop("04.props.faith-blooms", "p01")
        for bi in range(9):
            bx = 480 + bi * 82
            by = int(lerp(548, 616, bi / 8.0))
            mid_b, end_b, _ = solve_2bone_2d((bx, by), (poet_x, poet_y - 125), 28.0, 26.0, bend_dir=-1.0)
            draw = ImageDraw.Draw(canvas, "RGBA")
            draw.line([(bx, by), mid_b, end_b], fill=(102, 178, 88, 255), width=3)
            draw.ellipse([mid_b[0] - 3, mid_b[1] - 3, mid_b[0] + 3, mid_b[1] + 3], fill=(165, 215, 110, 255))
            R2.paste_centered(canvas, bloom_im, end_b[0], end_b[1], target_h=34, alpha_mul=0.92)

        # Articulated Poet (`poet_tracksuit`) climbing the incline with analytical 2-bone IK
        sk = draw_articulated_human(
            canvas, poet_x, poet_y, height=225.0, facing=-1.0, walk_phase=walk_ph,
            walking=(u < 0.82), lean_deg=9.0, reach=smoothstep(0.55, 0.88, u),
            style="clean_vector", coat_rgb=(112, 92, 74), pants_rgb=(78, 64, 52),
            skin_rgb=(188, 152, 118), rim_rgb=(252, 214, 148),
            char_id="poet_tracksuit", view="SIDE"
        )
        # Floating crimson heart (`04.props.heart`) rising from wet boards into chest mortise (`u < 0.55`)
        chest_pt = ((sk["hip"][0] + sk["shoulder"][0]) * 0.5, (sk["hip"][1] + sk["shoulder"][1]) * 0.5)
        hu = smoothstep(0.10, 0.48, u)
        hx = int(lerp(poet_x - 35, chest_pt[0], hu))
        hy = int(lerp(poet_y - 12, chest_pt[1], hu))
        R2.paste_centered(canvas, R2.load_cut_prop("04.props.heart", "p01"), hx, hy, target_h=36, alpha_mul=0.95)

        # Two articulated 2-bone IK helping arms/hands (`04.props.poet-jointed-hands`) locking onto Poet's wrists (`0.0cm` gap at u >= 0.82)
        attach_u = smoothstep(0.50, 0.84, u)
        hand_prop = R2.load_cut_prop("04.props.poet-jointed-hands", "p01")
        draw = ImageDraw.Draw(canvas, "RGBA")
        for root_pt, wrist_target in [((318, 435), sk["hand1"]), ((318, 468), sk["hand2"])]:
            cur_t = (lerp(395, wrist_target[0], attach_u), lerp(475, wrist_target[1], attach_u))
            elb_h, end_h, _ = solve_2bone_2d(root_pt, cur_t, 56.0, 52.0, bend_dir=1.0)
            draw.polygon(capsule_poly(root_pt, elb_h, 6.5, 5.2), fill=(212, 178, 128, 240), outline=(45, 35, 25, 255))
            draw.polygon(capsule_poly(elb_h, end_h, 5.2, 4.2), fill=(228, 192, 138, 245), outline=(45, 35, 25, 255))
            R2.paste_centered(canvas, hand_prop, end_h[0], end_h[1], target_h=28, alpha_mul=0.95)

        draw_clean_subtitle(canvas, verse_line, style="default", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 05 · SCION-018 · CARTOON SALOON PAINTERLY GOUACHE (`18-saloon`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 5:
        # Modeled directly on `18-cartoon-saloon/stills/still_09.0s.jpg` + real night-field plates!
        for y in range(H):
            k = y / float(H)
            draw.line([(0, y), (W, y)], fill=(int(lerp(36, 218, k)), int(lerp(34, 158, k)), int(lerp(76, 128, k)), 255))
        R2.blend_multiplane_underlay(canvas, "world_bf0a66ea_0", cam_x=(u - 0.5) * 28.0, opacity=0.42)
        R2.paste_centered(canvas, R2.load_cut_prop("05.props.star-names", "p01"), 1040, 96, target_w=135, alpha_mul=0.52)
        draw = ImageDraw.Draw(canvas, "RGBA")
        for mr in range(95, 22, -12):
            draw.ellipse([1040 - mr, 96 - mr, 1040 + mr, 96 + mr], fill=(245, 238, 215, int(22 * (100 - mr) / 80.0)))
        draw.ellipse([1016, 72, 1064, 120], fill=(248, 242, 218, 255))

        # Rolling indigo hills + flat gouache teal trees with Celtic spiral foliage lines
        for hill_y, hill_c in [(515, (58, 66, 102, 255)), (548, (42, 50, 86, 255))]:
            pts_h = [(410, 600)] + [(x, int(hill_y + 22 * math.sin(x * 0.009 + hill_y))) for x in range(410, W + 20, 20)] + [(W, 600)]
            draw.polygon(pts_h, fill=hill_c)
        for tx, ty, tr in [(610, 445, 48), (835, 405, 64), (1215, 420, 58)]:
            draw.rectangle([tx - 6, ty, tx + 6, 595], fill=(34, 48, 52, 255))
            draw.rounded_rectangle([tx - tr, ty - tr, tx + tr, ty + tr // 2], radius=24, fill=(32, 74, 84, 255), outline=(18, 42, 48, 255), width=2)
            draw.arc([tx - tr // 2, ty - tr // 2, tx + tr // 2, ty + tr // 4], 0, 270, fill=(88, 148, 156, 190), width=2)

        # Left ancestral chamber (`x=0..435`) with russet triskelion wallpaper + carved green Atlantis Gate (`05.set.winged_marble_gate`)
        draw.rectangle([0, 155, 435, 595], fill=(142, 66, 52, 255))
        for wx in range(36, 235, 56):
            for wy in range(185, 540, 56):
                draw.arc([wx - 10, wy - 10, wx + 10, wy + 10], 0, 290, fill=(215, 165, 95, 180), width=2)
        # Carved green-and-gold Atlantis Perimeter Gate (`18-cartoon-saloon` green door + winged marble gate!)
        gate_open = int(smoothstep(0.72, 0.96, u) * 58)
        draw.rectangle([245, 235, 412, 595], fill=(242, 224, 172, 255), outline=(62, 52, 38, 255), width=4)
        R2.paste_centered(canvas, R2.load_cut_prop("05.set.winged_marble_gate", "p03"), 328, 415, target_h=345, alpha_mul=0.82)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rectangle([248, 238, 398 - gate_open, 595], fill=(34, 82, 66, 215), outline=(22, 52, 42, 255), width=3)
        for gy in range(275, 565, 44):
            draw.arc([310 - gate_open // 2, gy - 12, 334 - gate_open // 2, gy + 12], 0, 280, fill=(118, 178, 142, 210), width=2)

        # Pine roof & stone foundation + porch balustrade (`18-cartoon-saloon` framing)
        draw.polygon([(0, 0), (465, 155), (1280, 192), (1280, 165), (465, 122), (0, 0)], fill=(62, 46, 42, 255))
        draw.rectangle([0, 595, W, H], fill=(44, 42, 48, 255))
        draw.rectangle([410, 592, 1210, 608], fill=(238, 218, 168, 255))
        for rx in range(445, 1185, 42):
            draw.line([(rx, 505), (rx, 592)], fill=(78, 72, 86, 255), width=4)
        draw.line([(412, 505), (1185, 505)], fill=(88, 82, 96, 255), width=5)

        # Real Painted Cartoon Saloon Elders (`ancestor_elder`, `ancestor_robe`) & De-Bradded Poet (`poet_tracksuit`)
        draw_articulated_human(
            canvas, 175, 595, height=195.0, facing=1.0, walk_phase=walk_ph,
            walking=False, lean_deg=6.0, reach=0.65, style="cartoon_saloon",
            coat_rgb=(156, 54, 42), pants_rgb=(36, 92, 98), skin_rgb=(228, 192, 162), robe=True,
            char_id="ancestor_elder", view="3Q"
        )
        draw_articulated_human(
            canvas, 585, 595, height=205.0, facing=-1.0, walk_phase=walk_ph,
            walking=(0.15 < u < 0.55), lean_deg=4.0, arm_raise=smoothstep(0.20, 0.70, u) * 0.55,
            style="cartoon_saloon", coat_rgb=(46, 78, 118), pants_rgb=(34, 48, 68),
            skin_rgb=(178, 134, 104), sunglasses=True,
            char_id="poet_tracksuit", view="3Q"
        )
        draw_articulated_human(
            canvas, 920, 595, height=198.0, facing=-1.0, walk_phase=walk_ph,
            walking=False, lean_deg=4.0, reach=0.45, style="cartoon_saloon",
            coat_rgb=(64, 58, 112), pants_rgb=(42, 38, 78), skin_rgb=(212, 185, 160), robe=True,
            char_id="ancestor_robe", view="3Q"
        )

        # Invariant 9-node Sacred Geometry KIN Constellation in gold leaf (`r = 1.000` graph topology)
        draw = ImageDraw.Draw(canvas, "RGBA")
        kin_pts = [
            (540, 255), (650, 210), (760, 235), (870, 198), (980, 245),
            (605, 335), (760, 320), (915, 338), (760, 420),
        ]
        kin_edges = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (2, 6), (4, 7), (5, 6), (6, 7), (5, 8), (6, 8), (7, 8)]
        n_active = max(2, min(9, int(u * 10.5)))
        for e0, e1 in kin_edges:
            if e0 < n_active and e1 < n_active:
                draw.line([kin_pts[e0], kin_pts[e1]], fill=(248, 218, 128, 225), width=2)
        for ni in range(n_active):
            kx, ky = kin_pts[ni]
            draw.ellipse([kx - 6, ky - 6, kx + 6, ky + 6], fill=(255, 238, 168, 255), outline=(185, 132, 42, 255), width=2)

        draw_clean_subtitle(canvas, verse_line, style="default", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 06 · SCION-028 · MASK & PLATE FOUNDRY + WATERLINE (`28-foundry`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 6:
        # Modeled on `28-mask-plate-foundry/stills/still_09.0s.jpg`: perspective ashlar masonry & real Atlantis plaza plates
        for by in range(0, 465, 34):
            offset = (by // 34) * 28
            for bx in range(-56, W + 56, 76):
                shade = 36 + ((bx * 7 + by * 13) % 24)
                draw.rectangle([bx + (offset % 76), by, bx + (offset % 76) + 74, by + 32], fill=(shade, shade + 6, shade + 14, 255), outline=(22, 26, 32, 255))
        R2.blend_multiplane_underlay(canvas, "gen_69ee5bb28b_90", cam_x=(u - 0.5) * 32.0, opacity=0.46)
        R2.paste_centered(canvas, R2.load_cut_prop("06.set.atlantis_plaza", "p02"), 780, 260, target_h=340, alpha_mul=0.68)
        R2.paste_centered(canvas, R2.load_cut_prop("06.fx.comet", "p01"), int(lerp(460, 980, u)), 78, target_w=92, alpha_mul=0.75)
        draw = ImageDraw.Draw(canvas, "RGBA")

        # 3D perspective stone-tiled Civic Forum floor (`y = 445..720`)
        draw.polygon([(0, 465), (W, 435), (W, H), (0, H)], fill=(52, 58, 68, 240))
        for ti in range(-6, 18):
            x_top = 180 + ti * 85
            x_bot = -220 + ti * 145
            draw.line([(x_top, 450), (x_bot, H)], fill=(34, 38, 46, 230), width=2)
        for ty in [475, 512, 558, 612, 675]:
            draw.line([(0, ty), (W, ty - 14)], fill=(34, 38, 46, 230), width=2)

        # Left Toll Booth Doorway (`x=180..415, y=85..535`) with warm interior room & real cut coin-booth
        draw.polygon([(180, 82), (415, 104), (415, 535), (180, 548)], fill=(182, 138, 92, 255), outline=(128, 138, 154, 255), width=8)
        draw.polygon([(195, 96), (345, 112), (345, 488), (195, 498)], fill=(208, 164, 112, 255))
        draw.polygon([(180, 548), (415, 535), (840, 685), (320, 710)], fill=(185, 168, 142, 115))
        R2.paste_centered(canvas, R2.load_cut_prop("06.props.coin-booth", "p01"), 295, 345, target_h=310, alpha_mul=0.88)
        draw = ImageDraw.Draw(canvas, "RGBA")

        # 12 Civic Forum Windows across the masonry wall (igniting gold as waterline drops below them)
        y_water = int(lerp(135, 645, u))
        for wi in range(12):
            wx = 485 + (wi % 6) * 124
            wy = 135 + (wi // 6) * 128
            is_lit = (wy + 24 < y_water)
            w_fill = (252, 214, 118, 255) if is_lit else (26, 34, 46, 255)
            draw.rectangle([wx - 22, wy - 32, wx + 22, wy + 32], fill=w_fill, outline=(95, 108, 124, 255), width=3)

        # Articulated Gatekeeper (`citizen_1`), Traveler Child (`young_poet`), and Poet (`poet_tracksuit`) walking the Forum
        draw_articulated_human(
            canvas, 145, 595, height=195.0, facing=1.0, walk_phase=walk_ph,
            walking=False, sit=0.85, reach=0.75, style="clean_vector",
            coat_rgb=(92, 78, 62), pants_rgb=(32, 34, 42), skin_rgb=(172, 134, 106), rim_rgb=(255, 205, 135),
            char_id="citizen_1", view="3Q"
        )
        draw_articulated_human(
            canvas, int(lerp(980, 640, u)), 568, height=162.0, facing=-1.0, walk_phase=walk_ph,
            walking=(u < 0.85), lean_deg=5.0, style="clean_vector",
            coat_rgb=(188, 196, 210), pants_rgb=(88, 98, 115), skin_rgb=(182, 142, 112), rim_rgb=(165, 230, 255),
            char_id="young_poet", view="SIDE"
        )
        draw_articulated_human(
            canvas, int(lerp(1120, 780, u)), 585, height=212.0, facing=-1.0, walk_phase=walk_ph,
            walking=(u < 0.85), lean_deg=6.0, reach=smoothstep(0.15, 0.45, u) * 0.6, style="clean_vector",
            coat_rgb=(44, 56, 74), pants_rgb=(28, 36, 48), skin_rgb=(174, 132, 102), rim_rgb=(255, 212, 128), sunglasses=True,
            char_id="poet_tracksuit", view="SIDE"
        )

        # Holdout matte waterline `y_water(t)` with underwater Snell refraction & caustic wave below
        if y_water < H - 55:
            arr = np.array(canvas)
            sub = arr[y_water:, :, :3].astype(np.float32)
            sub[:, :, 0] = np.clip(sub[:, :, 0] * 0.52, 0, 255)
            sub[:, :, 1] = np.clip(sub[:, :, 1] * 0.94 + 18, 0, 255)
            sub[:, :, 2] = np.clip(sub[:, :, 2] * 1.28 + 42, 0, 255)
            arr[y_water:, :, :3] = sub.astype(np.uint8)
            canvas = Image.fromarray(arr).convert("RGBA")
            draw = ImageDraw.Draw(canvas, "RGBA")
            wave_pts = [(x, int(y_water + 4 * math.sin(x * 0.025 + t * 4.5))) for x in range(0, W + 16, 16)]
            draw.line(wave_pts, fill=(165, 238, 255, 235), width=3)

        draw_clean_subtitle(canvas, verse_line, style="default", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 07 · SCION-047 × 19 · SOUND-TO-ACTION + SMART-BONE RIG (`47-sound`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 7:
        # Modeled on `47-sound-to-action/stills/still_09.0s.jpg` + real Naraka club multiplane plate & DJ props!
        for y in range(H):
            k = y / float(H)
            draw.line([(0, y), (W, y)], fill=(int(lerp(24, 118, k)), int(lerp(28, 86, k)), int(lerp(56, 98, k)), 255))
        R2.blend_multiplane_underlay(canvas, "gen_9c5f9c7c4a_70", cam_x=(u - 0.5) * 28.0, opacity=0.45)
        draw = ImageDraw.Draw(canvas, "RGBA")
        # Distant mountain range & crescent moon on right
        mtn = [(640, 495), (710, 435), (765, 468), (835, 392), (915, 452), (995, 405), (1085, 458), (1185, 398), (1280, 445), (1280, 505), (640, 505)]
        draw.polygon(mtn, fill=(18, 20, 28, 255))
        draw.ellipse([1135, 78, 1162, 105], fill=(242, 236, 218, 255))
        draw.ellipse([1143, 76, 1168, 101], fill=(32, 36, 66, 255))

        # Left corrugated container house wall (`x=0..675`) + warm stage booth doorway
        draw.rectangle([0, 18, 675, 505], fill=(36, 46, 68, 240), outline=(62, 74, 98, 255), width=4)
        for cy in range(36, 505, 22):
            draw.line([(0, cy), (675, cy)], fill=(24, 32, 48, 235), width=2)
        # Glowing stage booth doorway (`x=265..455`) with floor lamp
        draw.rectangle([262, 128, 458, 505], fill=(228, 182, 112, 255), outline=(112, 108, 98, 255), width=10)
        for fy in range(355, 502, 14):
            draw.line([(272, fy), (448, fy)], fill=(172, 124, 68, 220), width=2)
        draw.polygon([(375, 180), (425, 180), (435, 215), (365, 215)], fill=(255, 238, 165, 255))
        draw.line([(400, 215), (400, 372)], fill=(38, 32, 26, 255), width=4)

        # Rear Projection Screen (`x=520..960, y=95..355`): splitting house + 11 daisy petals plucking -> 0
        draw.rectangle([520, 95, 960, 355], fill=(18, 22, 32, 245), outline=(218, 178, 112, 255), width=4)
        petals_left = max(0, 11 - int(u * 12.2))
        for pi in range(petals_left):
            ang = pi * (2.0 * math.pi / 11.0) + t * 0.25
            px = int(740 + 56 * math.cos(ang))
            py = int(225 + 56 * math.sin(ang))
            draw.ellipse([px - 12, py - 12, px + 12, py + 12], fill=(248, 246, 240, 255))
        draw.ellipse([722, 207, 758, 243], fill=(248, 198, 68, 255))
        if u > 0.72:
            # 3 converging highway roads on screen as eyes snap open
            for rx0 in (560, 740, 920):
                draw.line([(rx0, 350), (740, 225)], fill=(125, 225, 255, 220), width=3)

        # Wooden deck stage (`y = 505..615`) + warm doorway light trapezium
        draw.rectangle([0, 505, W, 615], fill=(42, 40, 46, 255))
        for py in range(512, 612, 10):
            draw.line([(0, py), (W, py)], fill=(30, 28, 34, 220), width=1)
        draw.polygon([(268, 505), (452, 505), (545, 615), (242, 615)], fill=(212, 168, 112, 135))
        draw.rectangle([0, 615, W, H], fill=(16, 18, 24, 255))

        # Real cut speaker stacks (`07.props.speakers-vu`) + Audio RMS VU stacks pulsing on stage left & right
        spk_im = R2.load_cut_prop("07.props.speakers-vu", "p01")
        R2.paste_centered(canvas, spk_im, 115, 420, target_h=245, alpha_mul=0.88)
        R2.paste_centered(canvas, spk_im, 1165, 420, target_h=245, flip_x=True, alpha_mul=0.88)
        draw = ImageDraw.Draw(canvas, "RGBA")
        vu_n = int((0.25 + 0.70 * u + 0.12 * math.sin(t * 14.0)) * 12)
        for bi in range(12):
            by = 485 - bi * 22
            col = (95, 235, 135, 240) if bi < 8 else ((255, 210, 75, 240) if bi < 10 else (255, 82, 82, 240))
            if bi < vu_n:
                draw.rectangle([52, by, 98, by + 15], fill=col)
                draw.rectangle([1182, by, 1228, by + 15], fill=col)

        # Articulated Cyber DJ (`dj_cyber`) at real turntables (`07.props.dj-decks`) + Smart-Bone Poet at center mic
        chin_pitch = lerp(-18.0, 15.0, u)
        draw_articulated_human(
            canvas, 230, 575, height=195.0, facing=1.0, walk_phase=walk_ph,
            walking=False, sit=0.65, reach=0.6, style="clean_vector",
            coat_rgb=(68, 76, 98), pants_rgb=(38, 44, 58), skin_rgb=(178, 136, 108),
            char_id="dj_cyber", view="FRONT"
        )
        R2.paste_centered(canvas, R2.load_cut_prop("07.props.dj-decks", "p01"), 235, 535, target_w=240, alpha_mul=0.94)
        draw_articulated_human(
            canvas, 740, 585, height=215.0, facing=-1.0, walk_phase=walk_ph,
            walking=(0.25 < u < 0.65), lean_deg=-chin_pitch * 0.25, head_pitch_deg=chin_pitch,
            arm_raise=smoothstep(0.65, 0.95, u) * 0.65, style="clean_vector",
            coat_rgb=(42, 52, 72), pants_rgb=(28, 34, 48), skin_rgb=(176, 132, 102), sunglasses=(u < 0.72),
            char_id="poet_tracksuit" if u < 0.72 else "poet_black_tshirt", view="3Q"
        )
        R2.paste_centered(canvas, R2.load_cut_prop("07.props.mic-daisy-rings", "p01"), 688, 495, target_h=175, alpha_mul=0.92)
        draw = ImageDraw.Draw(canvas, "RGBA")
        # Microphone stand at x=695
        draw.line([(695, 425), (695, 585)], fill=(185, 192, 205, 255), width=3)
        draw.ellipse([689, 416, 701, 428], fill=(225, 230, 240, 255))

        draw_clean_subtitle(canvas, verse_line, style="default", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 08 · SCION-015 × 41 · LAYERED ACETATE PUPPET + DAMPED SPRING (`15`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 8:
        # Rooftop parapet overlooking Atlantis domes + real multiplane plates + 3 crescent moons (`08.props.moons-laundry`)
        for y in range(H):
            k = y / float(H)
            draw.line([(0, y), (W, y)], fill=(int(lerp(28, 76, k)), int(lerp(36, 88, k)), int(lerp(64, 118, k)), 255))
        R2.blend_multiplane_underlay(canvas, "world_8bc7b3e2_0", cam_x=(u - 0.5) * 32.0, opacity=0.45)
        R2.paste_centered(canvas, R2.load_cut_prop("08.props.moons-laundry", "p01"), 1120, 115, target_w=125, alpha_mul=0.65)
        draw = ImageDraw.Draw(canvas, "RGBA")
        for mx, my in [(480, 92), (760, 74), (1040, 108)]:
            draw.ellipse([mx - 18, my - 18, mx + 18, my + 18], fill=(245, 240, 220, 235))
            draw.ellipse([mx - 10, my - 20, mx + 22, my + 14], fill=(34, 44, 74, 255))
        # Distant Atlantis domes silhouette + rooftop deck + hero marquee (`08.hero.marquee`)
        for dx, dw, dh in [(420, 140, 95), (590, 190, 135), (820, 155, 110), (1020, 130, 85)]:
            draw.chord([dx - dw // 2, 555 - dh, dx + dw // 2, 555 + dh], 180, 360, fill=(38, 48, 68, 255))
        R2.paste_centered(canvas, R2.load_cut_prop("08.hero.marquee", "p01"), 235, 395, target_h=285, alpha_mul=0.84)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rectangle([0, 555, W, H], fill=(44, 46, 54, 255))
        for rx in range(40, W, 52):
            draw.line([(rx, 478), (rx, 555)], fill=(72, 78, 92, 255), width=3)
        draw.line([(0, 478), (W, 478)], fill=(96, 104, 122, 255), width=4)

        # 3 Articulated Winged Angels (`angel`) in upper plain tipping real silver ice basins (`08.props.basins`)
        if 0.18 <= u <= 0.82:
            ang_a = int(245 * math.sin(((u - 0.18) / 0.64) * math.pi))
            basin_im = R2.load_cut_prop("08.props.basins", "p01")
            for ax in (430, 640, 850):
                draw_articulated_human(
                    canvas, ax, 310, height=148.0, facing=1.0, walk_phase=walk_ph,
                    walking=False, reach=0.75, style="cartoon_saloon",
                    coat_rgb=(232, 240, 252), pants_rgb=(205, 222, 245),
                    skin_rgb=(238, 215, 195), wings=True, robe=True, alpha=ang_a,
                    char_id="angel", view="FRONT"
                )
                R2.paste_centered(canvas, basin_im, ax + 28, 244, target_w=54, alpha_mul=ang_a / 255.0)
                draw = ImageDraw.Draw(canvas, "RGBA")
                # Shimmering ice-water cascade from silver basin
                draw.ellipse([ax + 12, 235, ax + 46, 252], fill=(210, 230, 250, ang_a), outline=(120, 160, 195, ang_a))
                for wy_c in range(252, 520, 18):
                    wx_c = ax + 28 + int(6 * math.sin(wy_c * 0.08 - t * 9.0))
                    draw.line([(wx_c, wy_c), (wx_c, wy_c + 10)], fill=(155, 235, 255, int(ang_a * 0.75)), width=2)

        # Damped Spring Solver (`SCION 41`) for the translucent Soul Cel (`offset >= 8px` at end)
        body_x, body_y = 610, 600
        if u < 0.14:
            s_dx, s_dy = int(u * 60), -int(u * 90)
        elif u < 0.66:
            arc = math.sin(((u - 0.14) / 0.52) * math.pi)
            s_dx = int(18 + arc * 95)
            s_dy = -int(16 + arc * 225)
        else:
            # Second-order underdamped harmonic spring settling to permanent (+22px, -12px) double-cel offset
            dt_s = u - 0.66
            osc = math.exp(-dt_s * 11.0) * math.cos(dt_s * 42.0)
            s_dx = int(22 + 28 * osc)
            s_dy = int(-12 - 22 * osc)

        # Cel 1: Grounded Opaque Body Puppet (`poet_tracksuit`)
        draw_articulated_human(
            canvas, body_x, body_y, height=215.0, facing=1.0, walk_phase=walk_ph,
            walking=False, lean_deg=3.0, style="clean_vector",
            coat_rgb=(46, 54, 72), pants_rgb=(30, 36, 48), skin_rgb=(176, 132, 102),
            char_id="poet_tracksuit", view="SIDE"
        )
        # Cel 2: Translucent Luminous Cyan/Gold Acetate Soul Puppet (`poet_soul`)
        draw_articulated_human(
            canvas, body_x + s_dx, body_y + s_dy, height=215.0, facing=1.0, walk_phase=walk_ph,
            walking=True, lean_deg=-6.0, arm_raise=0.45, style="norstein",
            coat_rgb=(95, 225, 255), pants_rgb=(75, 195, 245), skin_rgb=(215, 248, 255),
            rim_rgb=(255, 235, 135), alpha=175,
            char_id="poet_soul", view="3Q"
        )

        draw_clean_subtitle(canvas, verse_line, style="default", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 09 · SCION-011 × 21 · VIDEO PUPPETRY & RELIGHTING CLOCK (`11/21`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 9:
        # 4-Hour Relighting Clock (`03:30 Neon Rain -> 04:15 Abyss -> 05:00 First Grey -> 05:45 Golden Sunrise`)
        warmth = smoothstep(0.25, 0.92, u)
        for y in range(555):
            k = y / 555.0
            r = int(lerp(lerp(18, 52, k), lerp(92, 242, k), warmth))
            g = int(lerp(lerp(28, 68, k), lerp(74, 178, k), warmth))
            b = int(lerp(lerp(62, 118, k), lerp(88, 112, k), warmth))
            draw.line([(0, y), (W, y)], fill=(r, g, b, 255))
        R2.blend_multiplane_underlay(canvas, "gen_ac146f1212_50", cam_x=(u - 0.5) * 28.0, opacity=0.42)
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Sun / Moon disc rising in the East (`x=820`)
        disc_y = int(lerp(185, 125, warmth))
        disc_c = (int(lerp(220, 255, warmth)), int(lerp(232, 215, warmth)), int(lerp(255, 125, warmth)), 255)
        draw.ellipse([785, disc_y - 35, 855, disc_y + 35], fill=disc_c)

        # Distant causeway arches on right (`x=520..1280`) + mother living room cutaway (`09.set.mother_living_room`)
        draw.rectangle([520, 385, W, 555], fill=(38, 44, 58, 255))
        for ax in range(565, 1240, 135):
            draw.chord([ax, 415, ax + 95, 595], 180, 360, fill=(int(lerp(24, 165, warmth)), int(lerp(32, 128, warmth)), int(lerp(58, 92, warmth)), 255))
        R2.paste_centered(canvas, R2.load_cut_prop("09.set.mother_living_room", "p02"), 1045, 425, target_h=245, alpha_mul=0.72)
        R2.paste_centered(canvas, R2.load_cut_prop("09.props.phones-chair", "p01"), 965, 485, target_h=135, alpha_mul=0.85)
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Illuminated Harbour Glass Telephone Booth on left (`x=240..395, y=185..555`) + real cut phonebooth (`09.props.phonebooth`)
        draw.rectangle([240, 185, 395, 555], fill=(238, 198, 124, 235), outline=(42, 54, 72, 255), width=8)
        draw.rectangle([240, 185, 395, 222], fill=(42, 54, 72, 255))
        for gy in (308, 430):
            draw.line([(240, gy), (395, gy)], fill=(42, 54, 72, 255), width=4)
        R2.paste_centered(canvas, R2.load_cut_prop("09.props.phonebooth", "p01"), 318, 370, target_h=355, alpha_mul=0.78)
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Articulated Poet (`poet_tracksuit`) inside booth + Caller (`mother_cardigan` / `father_elder`) across causeway
        rim_c = (int(lerp(120, 255, warmth)), int(lerp(215, 205, warmth)), int(lerp(255, 115, warmth)))
        draw_articulated_human(
            canvas, 318, 552, height=205.0, facing=1.0, walk_phase=walk_ph,
            walking=False, lean_deg=5.0, reach=0.45, style="clean_vector",
            coat_rgb=(44, 54, 72), pants_rgb=(28, 34, 46), skin_rgb=(176, 132, 102), rim_rgb=rim_c,
            char_id="poet_tracksuit", view="SIDE"
        )
        draw_articulated_human(
            canvas, int(lerp(1040, 880, u)), 552, height=200.0, facing=-1.0, walk_phase=walk_ph,
            walking=(u > 0.65), lean_deg=4.0, reach=0.5, style="clean_vector",
            coat_rgb=(88, 68, 92), pants_rgb=(48, 42, 58), skin_rgb=(182, 140, 110), rim_rgb=rim_c, robe=(u < 0.65),
            char_id="mother_cardigan" if u < 0.65 else "father_elder", view="3Q"
        )
        draw = ImageDraw.Draw(canvas, "RGBA")
        for seg in range(18):
            s0 = (seg + (t * 3.5) % 1.0) / 18.0
            s1 = min(1.0, s0 + 0.035)
            p0 = (int(lerp(355, 895, s0)), int(365 - 52 * math.sin(s0 * math.pi)))
            p1 = (int(lerp(355, 895, s1)), int(365 - 52 * math.sin(s1 * math.pi)))
            draw.line([p0, p1], fill=(*rim_c, 235), width=2)

        # Wet asphalt reflection mirror below `y = 555`
        arr = np.array(canvas)
        refl = cv2.flip(arr[390:555, :, :3], 0)
        refl = cv2.GaussianBlur(refl, (15, 5), 3.0)
        refl_resized = cv2.resize(refl, (W, H - 555))
        arr[555:, :, :3] = (arr[555:, :, :3].astype(np.float32) * 0.28 + refl_resized.astype(np.float32) * 0.72).astype(np.uint8)
        canvas = Image.fromarray(arr).convert("RGBA")
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.line([(0, 555), (W, 555)], fill=(180, 195, 215, 220), width=2)

        draw_clean_subtitle(canvas, verse_line, style="default", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 10 · SCION-009 · TAKEO IGARASHI ARAP MESH (`09-igarashi`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 10:
        # Modeled directly on `09-igarashi/stills/still_09.0s.jpg` + real highway multiplane plates & motorcycle cuts!
        for y in range(565):
            k = y / 565.0
            draw.line([(0, y), (W, y)], fill=(int(lerp(42, 192, k)), int(lerp(34, 118, k)), int(lerp(78, 108, k)), 255))
        R2.blend_multiplane_underlay(canvas, "gen_366225426b_70" if u > 0.35 else "gen_f729b3bb28_90", cam_x=-t * 55.0, opacity=0.44)
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Sky dot-matrix flipping column-by-column to dawn gold (`SCION 26` invariant)
        lit_cols = int(u * 28)
        for ci in range(28):
            for ri in range(3):
                dx = 110 + ci * 38
                dy = 52 + ri * 20
                c_dot = (252, 218, 112, 235) if ci <= lit_cols else (72, 62, 92, 160)
                draw.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=c_dot)

        # Scrolling hand-drawn outline trees (`09-igarashi` thick navy ink outline style + `10.props.tree-dawn-sign`)
        scroll = int(t * 220)
        tree_prop = R2.load_cut_prop("10.props.tree-dawn-sign", "p01")
        for ti in range(8):
            tx = 1280 - ((scroll + ti * 210) % 1680) + 120
            draw.line([(tx, 435), (tx, 560)], fill=(24, 24, 48, 255), width=6)
            draw.ellipse([tx - 58, 345, tx + 58, 445], fill=(128, 92, 108, 180), outline=(24, 24, 48, 255), width=5)
            if ti % 2 == 0 and tree_prop is not None:
                R2.paste_centered(canvas, tree_prop, tx, 442, target_h=175, alpha_mul=0.72)
                draw = ImageDraw.Draw(canvas, "RGBA")

        # Scrolling white-and-navy porch balustrade (`y = 485..565`) + wooden deck planks (`y = 565..720`)
        draw.rectangle([0, 482, W, 496], fill=(212, 216, 224, 255), outline=(22, 24, 34, 255), width=3)
        for rx in range(-((scroll * 2) % 36), W, 36):
            draw.rectangle([rx, 496, rx + 12, 565], fill=(198, 204, 214, 255), outline=(22, 24, 34, 255), width=2)
        draw.rectangle([0, 565, W, H], fill=(74, 66, 62, 255))
        for px in range(-((scroll * 3) % 64), W + 64, 64):
            draw.line([(px, 565), (px - 48, H)], fill=(46, 40, 38, 230), width=2)

        # Hand-drawn Paper-Cutout Motorcycle + Rider at center `x = 640px` (`09-igarashi` cream die-cut border + `10.props.bike-ride-views`)
        bx, by = 640, 595
        bounce = int(3.5 * math.sin(t * 14.0))
        draw.ellipse([bx - 122, by - 78 + bounce, bx - 42, by + 2 + bounce], fill=(238, 234, 224, 255), outline=(90, 88, 82, 220), width=2)
        draw.ellipse([bx + 42, by - 78 + bounce, bx + 122, by + 2 + bounce], fill=(238, 234, 224, 255), outline=(90, 88, 82, 220), width=2)
        draw.polygon([(bx - 95, by - 45 + bounce), (bx - 35, by - 115 + bounce), (bx + 65, by - 115 + bounce), (bx + 95, by - 45 + bounce)], fill=(238, 234, 224, 255))
        for wx in (bx - 82, bx + 82):
            draw.ellipse([wx - 34, by - 72 + bounce, wx + 34, by - 4 + bounce], fill=(32, 34, 42, 255), outline=(18, 18, 24, 255), width=4)
            draw.ellipse([wx - 18, by - 56 + bounce, wx + 18, by - 20 + bounce], fill=(168, 174, 186, 255), outline=(18, 18, 24, 255), width=3)
        draw.polygon([(bx - 82, by - 38 + bounce), (bx - 24, by - 96 + bounce), (bx + 48, by - 96 + bounce), (bx + 82, by - 38 + bounce)], fill=(178, 52, 44, 255), outline=(18, 18, 24, 255), width=4)
        bike_im = R2.load_cut_prop("10.props.bike-ride-views", "p01")
        if bike_im is not None:
            bike_styled = R2.style_arap_mesh_overlay(R2.add_cream_paper_margin(bike_im, margin_px=4), step=26)
            R2.paste_centered(canvas, bike_styled, bx, by - 44 + bounce, target_w=235, alpha_mul=0.92)
            draw = ImageDraw.Draw(canvas, "RGBA")
        # Headlight beam
        draw.polygon([(bx + 68, by - 92 + bounce), (W, by - 175), (W, by - 10)], fill=(255, 238, 165, 85))

        # Articulated Paper-Cutout Rider (`poet_tracksuit`, `style="arap"`) leaning forward on the bike
        draw_articulated_human(
            canvas, bx - 12, by - 12 + bounce, height=195.0, facing=1.0, walk_phase=walk_ph,
            walking=False, sit=0.55, lean_deg=24.0, reach=0.75, style="arap",
            coat_rgb=(54, 68, 96), pants_rgb=(34, 42, 62), skin_rgb=(182, 138, 108), sunglasses=True,
            char_id="poet_tracksuit", view="SIDE"
        )
        # Brief brass X-ray ARAP mesh/skeleton flash (`0.18 <= u <= 0.34`, `10.props.bike-skeleton`)
        if 0.18 <= u <= 0.34:
            R2.paste_centered(canvas, R2.load_cut_prop("10.props.bike-skeleton", "p01"), bx, by - 55 + bounce, target_w=235, alpha_mul=0.82)
            draw = ImageDraw.Draw(canvas, "RGBA")
            mesh_pts = [(bx - 82, by - 38), (bx, by - 88), (bx + 82, by - 38), (bx - 12, by - 145), (bx + 32, by - 110)]
            for p0 in mesh_pts:
                for p1 in mesh_pts:
                    draw.line([p0, p1], fill=(255, 215, 95, 165), width=2)

        draw_clean_subtitle(canvas, verse_line, style="default", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 11 · SCION-008 · IVAN SUTHERLAND CONSTRAINT SKETCHPAD (`08-sutherland`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 11:
        # Modeled 100% on `08-sutherland/stills/still_9s.jpg`: 1963 TX-2 Green-Phosphor CRT Display + vectorized temple cuts!
        canvas = Image.new("RGBA", (W, H), (4, 16, 8, 255))
        R2.blend_multiplane_underlay(canvas, "gen_69ee5bb28b_30", cam_x=(u - 0.5) * 28.0, opacity=0.35, style_mode="sutherland")
        t_whole = R2.load_cut_prop("11.props.temple.whole", "p01")
        if t_whole is not None:
            R2.paste_centered(canvas, R2.style_sutherland_crt_blueprint(t_whole), 640, 295, target_w=760, alpha_mul=0.45)
        moto_im = R2.load_cut_prop("11.props.parked-motorcycle", "p01")
        if moto_im is not None:
            R2.paste_centered(canvas, R2.style_sutherland_crt_blueprint(moto_im), 145, 485, target_w=175, alpha_mul=0.82)
        draw = ImageDraw.Draw(canvas, "RGBA")
        c_bright = (78, 255, 128, 255)
        c_mid = (48, 185, 86, 220)
        c_dim = (26, 105, 48, 180)

        # Perspective CRT floor grid + flattened sea wave line under Poet's footsteps
        gy = 525
        draw.line([(40, gy), (W - 40, gy)], fill=c_bright, width=2)
        for gx in range(80, W - 40, 56):
            draw.line([(gx, gy), (gx - 65, 608)], fill=c_dim, width=1)
        draw.line([(20, 608), (W - 20, 608)], fill=c_mid, width=2)

        poet_x = int(lerp(220, 960, u))
        wave_pts = []
        for wx in range(60, W - 60, 12):
            dist_p = abs(wx - poet_x)
            amp = 0.0 if dist_p < 95 else min(12.0, (dist_p - 95) * 0.08)
            wave_pts.append((wx, int(gy + 18 + amp * math.sin(wx * 0.06 - t * 4.5))))
        draw.line(wave_pts, fill=c_mid, width=1)

        # 19 Vector Cards of the White Temple snapping into place with Sketchpad constraints
        cards_n = min(19, int(u * 20.5))
        # Cards 1-5: 5 Plinth courses
        for ci in range(min(5, cards_n)):
            cx0 = 260 + ci * 152
            draw.rectangle([cx0, gy - 26, cx0 + 148, gy], outline=c_bright, width=2)
            for hy in range(gy - 22, gy, 5):
                draw.line([(cx0 + 4, hy), (cx0 + 144, hy)], fill=c_dim, width=1)

        # Cards 6-11: 6 Fluted Columns (even columns behind Poet, odd columns occluding in front!)
        col_xs = [295 + ci * 138 for ci in range(max(0, min(6, cards_n - 5)))]
        for idx_c, cx in enumerate(col_xs):
            if idx_c % 2 == 0:
                draw.rectangle([cx - 16, 215, cx + 16, gy - 26], fill=(4, 18, 8, 255), outline=c_mid, width=2)
                for fx in (-8, 0, 8):
                    draw.line([(cx + fx, 215), (cx + fx, gy - 26)], fill=c_dim, width=1)

        # 17-Point Constraint-Solved Vector Poet (`poet_tracksuit`, Turn-Lab multiview substitution) walking across the temple floor
        turn_view = ["SIDE", "3Q", "FRONT", "SIDE"][min(3, int(u * 3.99))]
        draw_articulated_human(
            canvas, poet_x, gy, height=205.0, facing=1.0, walk_phase=walk_ph,
            walking=(u < 0.88), lean_deg=5.0, reach=0.35, style="sutherland",
            char_id="poet_tracksuit", view=turn_view
        )
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Foreground occluding columns (`idx_c % 2 == 1`)
        for idx_c, cx in enumerate(col_xs):
            if idx_c % 2 == 1:
                draw.rectangle([cx - 16, 215, cx + 16, gy - 26], fill=(4, 18, 8, 255), outline=c_bright, width=2)
                for fx in (-8, 0, 8):
                    draw.line([(cx + fx, 215), (cx + fx, gy - 26)], fill=c_mid, width=1)

        # Cards 12-15: Architrave beams; Cards 16-18: Pediment gable; Card 19: Lantern finial + Light-Pen Crosshair
        if cards_n >= 12:
            draw.rectangle([260, 185, 1020, 215], outline=c_bright, width=2)
        if cards_n >= 16:
            draw.polygon([(250, 185), (640, 92), (1030, 185)], outline=c_bright, width=2)
        if cards_n >= 19:
            draw.ellipse([624, 62, 656, 94], outline=c_bright, width=2)
        # Sketchpad Light-Pen Crosshair (`+`)
        pen_x, pen_y = (640, 78) if cards_n >= 16 else (295 + (cards_n % 6) * 138, 215)
        draw.line([(pen_x - 14, pen_y), (pen_x + 14, pen_y)], fill=c_bright, width=2)
        draw.line([(pen_x, pen_y - 14), (pen_x, pen_y + 14)], fill=c_bright, width=2)
        draw.ellipse([pen_x - 6, pen_y - 6, pen_x + 6, pen_y + 6], outline=c_bright, width=1)

        # CRT Phosphor Bloom pass (exact `08-sutherland` look!)
        arr = np.array(canvas)
        bloom = cv2.GaussianBlur(arr[:, :, :3], (21, 21), 6.0)
        arr[:, :, :3] = np.clip(arr[:, :, :3].astype(np.float32) + bloom.astype(np.float32) * 0.55, 0, 255).astype(np.uint8)
        canvas = Image.fromarray(arr).convert("RGBA")

        info = [
            f"POET    17 POINTS  42 CONSTRAINTS  RELAXATION  75 PASSES  MAX |E|  0.03 MM",
            f"TEMPLE  {cards_n:02d}/19 CARDS  WAVE-AMPLITUDE UNDER FOOT: 0.00 MM  COLUMN-OCCLUDE: ACTIVE",
        ]
        draw_clean_subtitle(canvas, verse_line, style="sutherland", t=t, sutherland_info=info)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 12 · SCION-001 · TERRY GILLIAM CUT-OUT COLLAGE (`01-gilliam`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 12:
        # Modeled directly on `01-gilliam/stills/still_09.0s.jpg` + real multiplane plates & Gilliam cut props!
        for y in range(H):
            k = y / float(H)
            draw.line([(0, y), (W, y)], fill=(int(lerp(22, 232, k)), int(lerp(14, 148, k)), int(lerp(38, 118, k)), 255))
        R2.blend_multiplane_underlay(canvas, "world_f56df2d8_1", cam_x=(u - 0.5) * 28.0, opacity=0.38, style_mode="gilliam")
        # Cross-hatched Gilliam cloud band (`01-gilliam` signature!)
        _draw_engraving_rect(canvas, (480, 145, W, 385), (148, 76, 108), hatch_step=7, angle_mode=2)
        draw = ImageDraw.Draw(canvas, "RGBA")
        mtn_pts = [(480, 585), (560, 465), (675, 512), (820, 395), (960, 365), (1095, 455), (1185, 415), (1280, 495), (1280, 585)]
        draw.polygon(mtn_pts, fill=(24, 18, 28, 255))

        # Left cross-hatched stone temple wall (`x=0..495`) + warm gold cross-hatched doorway (`x=195..395`) + `12.props.niche-porch`
        _draw_engraving_rect(canvas, (0, 95, 495, 585), (138, 128, 162), hatch_step=5, angle_mode=2, border_rgb=(28, 24, 32))
        _draw_engraving_rect(canvas, (195, 205, 395, 585), (238, 196, 112), hatch_step=6, angle_mode=0, border_rgb=(42, 32, 22))
        _draw_engraving_rect(canvas, (0, 585, W, H), (82, 62, 44), hatch_step=5, angle_mode=1, border_rgb=(28, 22, 18))
        niche_im = R2.load_cut_prop("12.props.niche-porch", "p01")
        if niche_im is not None:
            R2.paste_centered(canvas, R2.style_gilliam_engraved_cutout(niche_im), 248, 365, target_h=385, alpha_mul=0.68)

        # 4 Gilliam Cut-Out Elders (`elder_man`) in upper arched stone niches + 12 Extinguishing Hourglasses (`12 -> 1`, `12.props.last-hourglass`)
        for ex in (560, 740, 920, 1100):
            draw = ImageDraw.Draw(canvas, "RGBA")
            draw.rounded_rectangle([ex - 54, 248, ex + 54, 378], radius=32, fill=(32, 26, 38, 195), outline=(218, 198, 158, 220), width=2)
            draw_articulated_human(
                canvas, ex, 372, height=108.0, facing=-1.0, walk_phase=0.0,
                walking=False, style="gilliam", coat_rgb=(128, 115, 98),
                pants_rgb=(88, 78, 66), skin_rgb=(195, 178, 155), robe=True, alpha=215,
                char_id="elder_man", view="FRONT"
            )
        lit_hg = max(1, 12 - int(u * 11.8))
        hg_im = R2.load_cut_prop("12.props.last-hourglass", "p01")
        for hi in range(12):
            hx = 520 + hi * 62
            hy = 105
            is_on = (hi < lit_hg)
            if is_on and hg_im is not None:
                R2.paste_centered(canvas, hg_im, hx, hy, target_h=34, alpha_mul=0.92)
            c_hg = (252, 214, 112, 255) if is_on else (78, 72, 82, 180)
            draw = ImageDraw.Draw(canvas, "RGBA")
            draw.polygon([(hx - 10, hy - 14), (hx + 10, hy - 14), (hx - 10, hy + 14), (hx + 10, hy + 14)], fill=c_hg, outline=(242, 235, 218, 255))

        # Two Living Brothers on porch widening monotonically (`gap: 15px -> 195px`) with Gilliam paper borders
        gap_px = int(lerp(18, 195, u))
        draw_articulated_human(
            canvas, 680 - gap_px, 595, height=210.0, facing=1.0, walk_phase=walk_ph,
            walking=(0.15 < u < 0.85), lean_deg=-5.0, reach=0.65, style="gilliam",
            coat_rgb=(135, 98, 76), pants_rgb=(58, 64, 82), skin_rgb=(176, 134, 104),
            char_id="poet_tracksuit", view="SIDE"
        )
        draw_articulated_human(
            canvas, 680 + gap_px, 595, height=210.0, facing=-1.0, walk_phase=walk_ph,
            walking=(0.15 < u < 0.85), lean_deg=5.0, reach=0.65, style="gilliam",
            coat_rgb=(82, 108, 128), pants_rgb=(48, 56, 72), skin_rgb=(176, 134, 104),
            char_id="brother_1", view="3Q"
        )
        R2.paste_centered(canvas, R2.load_cut_prop("12.props.hand-hourglass", "p01"), 680, 485, target_h=64, alpha_mul=0.88)

        draw_clean_subtitle(canvas, verse_line, style="gilliam", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 13 · SCION-007 · PETER FOLDÈS DRAWN METAMORPHOSIS (`07-foldes`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 13:
        # Modeled directly on `07-foldes/stills/still_09.0s.jpg` + real multiplane plates & Foldès calligraphic cuts!
        for y in range(560):
            k = y / 560.0
            draw.line([(0, y), (W, y)], fill=(int(lerp(112, 218, k)), int(lerp(116, 188, k)), int(lerp(148, 158, k)), 255))
        R2.blend_multiplane_underlay(canvas, "gen_ca6878be91_30" if u > 0.55 else "gen_e315da34f9_70", cam_x=(u - 0.5) * 28.0, opacity=0.38, style_mode="foldes")
        R2.paste_centered(canvas, R2.load_cut_prop("13.props.planet-boats", "p01"), 865, 138, target_w=115, alpha_mul=0.72)
        draw = ImageDraw.Draw(canvas, "RGBA")
        # Crescent moon + 4 moons of Jupiter
        draw.arc([1000, 165, 1042, 215], -75, 105, fill=(248, 244, 232, 255), width=4)
        for mi in range(min(4, int(u * 5) + 1)):
            draw.ellipse([720 + mi * 48, 145 - mi * 8, 730 + mi * 48, 155 - mi * 8], fill=(252, 246, 228, 255), outline=(28, 28, 34, 255))

        # Distant bay hills & 2 line-art sailboats righting themselves (`07-foldes` clean line art)
        pts_m = [(635, 470), (710, 435), (810, 448), (920, 428), (1050, 445), (1180, 425), (1280, 440), (1280, 485), (635, 485)]
        draw.polygon(pts_m, fill=(76, 82, 108, 255), outline=(28, 28, 34, 255), width=2)
        draw.rectangle([635, 475, W, 560], fill=(214, 186, 152, 255), outline=(28, 28, 34, 255), width=2)
        tilt = lerp(24.0, 0.0, smoothstep(0.12, 0.45, u))
        for bx_s in (780, 1110):
            rad_t = math.radians(tilt)
            mx_top = int(bx_s + 42 * math.sin(rad_t))
            my_top = int(472 - 42 * math.cos(rad_t))
            draw.polygon([(bx_s - 22, 475), (bx_s + 22, 475), (bx_s + 14, 486), (bx_s - 14, 486)], fill=(238, 228, 208, 255), outline=(24, 24, 28, 255), width=2)
            draw.polygon([(bx_s, 472), (mx_top, my_top), (bx_s + 18, 468)], fill=(248, 242, 228, 255), outline=(24, 24, 28, 255), width=2)

        # Left Café clapboard wall (`x=0..635`) + warm doorway + `13.props.cafe` + upper window pulling into focus (`sigma: 14 -> 0`)
        draw.rectangle([0, 92, 635, 560], fill=(196, 192, 178, 255), outline=(24, 24, 28, 255), width=3)
        for sy in range(118, 560, 26):
            draw.line([(0, sy), (635, sy)], fill=(152, 148, 136, 255), width=1)
        draw.rectangle([230, 155, 428, 560], fill=(244, 222, 168, 255), outline=(24, 24, 28, 255), width=3)
        R2.paste_centered(canvas, R2.load_cut_prop("13.props.cafe", "p01"), 329, 345, target_w=186, alpha_mul=0.48)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rectangle([230, 155, 428, 560], outline=(24, 24, 28, 255), width=3)
        draw.polygon([(268, 405), (298, 405), (304, 438), (262, 438)], fill=(252, 244, 212, 255), outline=(24, 24, 28, 255), width=2)

        # Upper Window (`x=475..592, y=235..398`) with Woman (`woman_brocade`) inside pulling from blur sigma=14 -> 0
        win_crop = Image.new("RGBA", (120, 165), (235, 205, 138, 255))
        R2.paste_centered(win_crop, R2.load_cut_prop("13.props.distant-window", "p01"), 60, 82, target_h=150, alpha_mul=0.55)
        draw_articulated_human(
            win_crop, 60, 160, height=135.0, facing=1.0, walk_phase=walk_ph,
            walking=False, arm_raise=smoothstep(0.75, 0.96, u) * 0.7, style="foldes",
            coat_rgb=(178, 62, 58), pants_rgb=(92, 54, 68), skin_rgb=(218, 182, 152), rim_rgb=(24, 24, 28),
            char_id="woman_brocade", view="FRONT"
        )
        sigma = max(0.0, 12.0 * (1.0 - smoothstep(0.15, 0.85, u)))
        if sigma > 0.4:
            win_crop = win_crop.filter(ImageFilter.GaussianBlur(radius=sigma))
        canvas.alpha_composite(win_crop, (475, 235))
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rectangle([475, 235, 595, 400], outline=(24, 24, 28, 255), width=3)
        draw.line([(535, 235), (535, 400)], fill=(24, 24, 28, 255), width=2)
        draw.line([(475, 318), (595, 318)], fill=(24, 24, 28, 255), width=2)

        # Porch floorboards (`y=560..665`) + wooden balustrade rail (`x=635..1280`)
        draw.rectangle([0, 560, W, 665], fill=(178, 168, 148, 255), outline=(24, 24, 28, 255), width=2)
        for px in range(40, W, 58):
            draw.line([(px, 560), (px - 28, 665)], fill=(132, 124, 108, 255), width=1)
        for rx in range(650, W, 28):
            draw.line([(rx, 405), (rx, 560)], fill=(92, 86, 78, 255), width=2)
        draw.line([(635, 405), (W, 405)], fill=(24, 24, 28, 255), width=3)
        draw.rectangle([0, 665, W, H], fill=(54, 58, 56, 255))

        # Café guests (`couple_1_a`) + Foldès Line-Art Poet (`poet_tracksuit`) + Scarlet Poppies & Harvest (`13.props.harvest`)
        draw_articulated_human(
            canvas, 145, 575, height=188.0, facing=1.0, walk_phase=walk_ph,
            walking=False, style="foldes", char_id="couple_1_a", view="3Q"
        )
        sk = draw_articulated_human(
            canvas, 920, 578, height=205.0, facing=-1.0, walk_phase=walk_ph,
            walking=(u < 0.35), lean_deg=5.0, reach=smoothstep(0.30, 0.75, u) * 0.85,
            style="foldes", coat_rgb=(98, 112, 142), pants_rgb=(58, 66, 86),
            skin_rgb=(228, 208, 182), rim_rgb=(24, 24, 28), sunglasses=(u < 0.82),
            char_id="poet_tracksuit", view="SIDE"
        )
        if u > 0.38:
            n_pop = int(smoothstep(0.38, 0.88, u) * 9)
            hx_p, hy_p = sk["hand1"]
            R2.paste_centered(canvas, R2.load_cut_prop("13.props.harvest", "p01"), hx_p - 28, hy_p - 18, target_h=95, alpha_mul=smoothstep(0.38, 0.88, u) * 0.85)
            draw = ImageDraw.Draw(canvas, "RGBA")
            for pi in range(n_pop):
                ang = -math.pi * 0.85 + pi * 0.24
                dist_p = 22 + pi * 11
                px = int(hx_p + math.cos(ang) * dist_p)
                py = int(hy_p + math.sin(ang) * dist_p)
                draw.line([(int(hx_p), int(hy_p)), (px, py)], fill=(28, 28, 32, 255), width=2)
                draw.ellipse([px - 9, py - 9, px + 9, py + 9], fill=(228, 52, 48, 255), outline=(24, 24, 28, 255), width=2)
                draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(28, 24, 24, 255))

        draw_clean_subtitle(canvas, verse_line, style="default", t=t)

    # ═════════════════════════════════════════════════════════════════════════
    # POEM 14 · SCION-004 · FRANK MOURIS IMAGE TORRENT MONTAGE (`04-mouris`)
    # ═════════════════════════════════════════════════════════════════════════
    elif num == 14:
        # Modeled directly on `04-mouris/stills/watching-9s.jpg`: the entire world, doorway, floor & figures
        # are constructed from a boiling grid of miniature archive tiles (`_get_mouris_tiles()` now includes real WYGWYL plates & cuts)!
        tiles = _get_mouris_tiles()
        n_t = len(tiles)
        arr = np.zeros((H, W, 3), dtype=np.uint8)
        tw, th = 28, 28
        tick = int(t * 12)

        # 1. Tile the entire background wall (`x < 810` warm grey-purple tiles, `x >= 810` deep night indigo tiles)
        for gy_i, y0 in enumerate(range(0, H, th)):
            for gx_i, x0 in enumerate(range(0, W, tw)):
                y1, x1 = min(H, y0 + th), min(W, x0 + tw)
                tile = tiles[(gx_i * 7 + gy_i * 13 + tick) % n_t][: y1 - y0, : x1 - x0].astype(np.float32)
                if y0 >= 595:
                    tint = np.array([155.0, 112.0, 72.0])
                    arr[y0:y1, x0:x1] = np.clip(tile * 0.48 + tint * 0.52, 0, 255).astype(np.uint8)
                elif x0 < 810:
                    tint = np.array([135.0, 128.0, 152.0])
                    arr[y0:y1, x0:x1] = np.clip(tile * 0.55 + tint * 0.45, 0, 255).astype(np.uint8)
                else:
                    tint = np.array([68.0, 52.0, 98.0])
                    arr[y0:y1, x0:x1] = np.clip(tile * 0.45 + tint * 0.55, 0, 255).astype(np.uint8)

        # 2. Freestanding Golden-Tiled Vintage Door (`x=260..448, y=215..595`) + golden floor spill
        for y0 in range(215, 595, 14):
            for x0 in range(260, 448, 14):
                tile = cv2.resize(tiles[(x0 + y0 + tick * 3) % n_t], (14, 14)).astype(np.float32)
                arr[y0 : y0 + 14, x0 : x0 + 14] = np.clip(tile * 0.35 + np.array([255.0, 224.0, 125.0]) * 0.65, 0, 255).astype(np.uint8)
        for y0 in range(595, 680, 10):
            for x0 in range(280, 1040, 10):
                fade_x = clamp(1.0 - (x0 - 280) / 760.0, 0.15, 1.0)
                arr[y0 : y0 + 10, x0 : x0 + 10] = np.clip(
                    arr[y0 : y0 + 10, x0 : x0 + 10].astype(np.float32) * (1.0 - 0.65 * fade_x)
                    + np.array([248.0, 198.0, 102.0]) * (0.65 * fade_x),
                    0, 255,
                ).astype(np.uint8)

        # Poem 01's exact sodium-orange haze rising from the bottom to chest height (`u < 0.45`)
        if u < 0.55:
            haze_h = int(clamp(u * 1.4, 0.0, 0.48) * H)
            yy = np.arange(H, dtype=np.float32)[:, None]
            h_mask = np.clip((yy - (H - haze_h)) / 90.0, 0.0, 1.0)[:, :, None] * (1.0 - smoothstep(0.35, 0.55, u)) * 0.45
            arr = np.clip(arr.astype(np.float32) * (1.0 - h_mask) + np.array([238.0, 128.0, 38.0])[None, None, :] * h_mask, 0, 255).astype(np.uint8)

        canvas = Image.fromarray(arr).convert("RGBA")
        R2.paste_centered(canvas, R2.load_cut_prop("14.props.door", "p01"), 354, 405, target_h=375, alpha_mul=0.72)
        R2.paste_centered(canvas, R2.load_cut_prop("14.props.reel", "p01"), 155, 145, target_w=210, alpha_mul=0.68)
        R2.paste_centered(canvas, R2.load_cut_prop("14.props.party", "p01"), 965, 155, target_w=235, alpha_mul=0.62)
        draw = ImageDraw.Draw(canvas, "RGBA")
        # Tiled Moon at (1100, 168)
        draw.ellipse([1065, 133, 1135, 203], fill=(248, 240, 195, 255), outline=(95, 86, 68, 255), width=3)

        # Articulated Poet (`poet_tracksuit`) & Partner (`party_woman_gown`) orbiting hand-in-hand and stepping into the vintage door
        orbit = int(95 * math.cos(u * math.pi * 2.0)) * (1.0 - smoothstep(0.75, 0.95, u))
        center_x = int(lerp(760, 355, smoothstep(0.68, 0.96, u)))
        p1_x = int(center_x - orbit)
        p2_x = int(center_x + orbit)

        # Render both figures filled with real painted character cuts + dense 10x10 Mouris mosaic grid!
        fig_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_articulated_human(
            fig_layer, p1_x, 598, height=205.0, facing=-1.0 if u > 0.65 else 1.0, walk_phase=walk_ph,
            walking=True, lean_deg=6.0, reach=0.65, style="clean_vector",
            coat_rgb=(52, 68, 88), pants_rgb=(36, 46, 62), skin_rgb=(188, 148, 118),
            char_id="poet_tracksuit", view="3Q" if 0.25 < u < 0.75 else "SIDE"
        )
        if u < 0.85:
            draw_articulated_human(
                fig_layer, p2_x, 598, height=205.0, facing=-1.0, walk_phase=walk_ph + math.pi,
                walking=True, lean_deg=-6.0, reach=0.65, style="clean_vector",
                coat_rgb=(88, 72, 58), pants_rgb=(58, 48, 38), skin_rgb=(188, 148, 118),
                alpha=int(255 * (1.0 - smoothstep(0.72, 0.85, u))),
                char_id="party_woman_gown", view="3Q"
            )
        fig_arr = np.array(fig_layer)
        f_mask = fig_arr[:, :, 3] > 80
        yy_f, xx_f = np.indices((H, W))
        grid_line = ((xx_f % 10 == 0) | (yy_f % 10 == 0)) & f_mask
        fig_arr[grid_line, :3] = (fig_arr[grid_line, :3].astype(np.float32) * 0.45).astype(np.uint8)
        canvas.alpha_composite(Image.fromarray(fig_arr, "RGBA"))

        draw_clean_subtitle(canvas, verse_line, style="default", t=t)

    return cv2.cvtColor(np.array(canvas.convert("RGB")), cv2.COLOR_RGB2BGR)
