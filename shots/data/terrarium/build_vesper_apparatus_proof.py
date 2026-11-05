#!/usr/bin/env python3
"""
Builds the Vesper / Stelline Narrative Apparatus Visual Proof & 24s Apparatus Reel:
  - `vesper_narrative_apparatus_proof.png` (2560x1440 2x2 sheet in both OUT_DIR and ARTIFACT_DIR)
  - `wygwyl_vesper_apparatus_reel.mp4` (24.0s at 1280x720 24fps in OUT_DIR, VIDEOS_DIR, and ARTIFACT_DIR)

Directly synthesizes the three uploaded reference aesthetics + the 8-page Vesper Research PDF:
  1. Mode I (Images 1 & 2): TVE 1/2..4/4 Amber LiDAR Point-Cloud Scope & Cyan CRT Viewfinder
  2. Mode II (Image 3): 14-Canister Wireframe Memory Matrix (`SPINNER P01..P14`), 3D Terrain Mesh & Naurian Code Block
  3. Mode III (PDF Section 06): "What the Echo Exposes" — Precrime vs. Stelline Split-Screen Water-Discrepancy Comparator (`P01 V92` vs `P10 V94`)
  4. Mode IV (PDF Section 01/04): Apparatus-to-Cinema Condensation (Point-Cloud & TVE Bezel dissolving into 100% unobstructed 16:9 Afterlight Cinema)
"""

import os
import sys
import math
import json
import shutil
import numpy as np
import cv2
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_14poems_construct_and_spacetime_worms import (
    W, H, FPS, SHOTS_ROOT, OUT_DIR, VIDEOS_DIR, ARTIFACT_DIR,
    smootherstep, get_font, encode_video_with_real_audio, warp_multiplane_3d
)

_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_XN = (_XX - W * 0.5) / (W * 0.5)
_YN = (_YY - H * 0.5) / (H * 0.5)


def load_view_rgb_and_disp(vn, view_map):
    sub = view_map.get(str(vn), "018da7e9-231c-44d0-87f5-b0b0cb7b61cb_0")
    vdir = os.path.join(SHOTS_ROOT, "out", sub)
    img_p = os.path.join(vdir, "image.jpg")
    dep_p = os.path.join(vdir, "depth.jpg")
    im = Image.open(img_p).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    rgb = np.asarray(im, dtype=np.float32) / 255.0
    if os.path.exists(dep_p):
        dm = Image.open(dep_p).convert("L").resize((W, H), Image.Resampling.BILINEAR)
        d_raw = np.asarray(dm, dtype=np.float32) / 255.0
        disp = np.clip(1.0 - d_raw, 0.0, 1.0)
    else:
        disp = np.clip((_YY / float(H)), 0.0, 1.0)
    disp = cv2.GaussianBlur(disp, (9, 9), 2.0)
    gx = cv2.Sobel(disp, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(disp, cv2.CV_32F, 0, 1, ksize=3)
    slope = np.clip(np.hypot(gx, gy) * 4.5, 0.0, 1.0)
    return rgb, disp, slope


def render_amber_pointcloud_scope(rgb, disp, slope, t=0.0, scan_streaks=True):
    """
    Renders the exact glowing golden/amber 3D LiDAR point-cloud aesthetic from User Images 1 & 2
    over a deep phosphor-teal CRT field (`#06161d`), with perspective ground streaks and green-cyan scan rays.
    """
    # Deep phosphor-teal background with subtle vignette
    yn_01 = _YY / float(H)
    bg = np.zeros((H, W, 3), dtype=np.float32)
    bg[..., 0] = 0.024 + 0.030 * (1.0 - yn_01)
    bg[..., 1] = 0.088 + 0.085 * (1.0 - yn_01)
    bg[..., 2] = 0.118 + 0.105 * (1.0 - yn_01)

    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    structure = np.clip(lum * 1.25 + slope * 1.35 + disp * 0.28, 0.0, 1.0)

    # 3D Depth-warped point-cloud lattice
    gx_coord = (_XX * 0.28 + disp * 24.0 + t * 1.5)
    gy_coord = (_YY * 0.28 + disp * 32.0)
    lattice = (0.5 + 0.5 * np.sin(gx_coord * 2.1) * np.cos(gy_coord * 2.1)) ** 3.0

    # Perspective ground-plane golden streaks (matching bottom half of Images 1 & 2)
    ground_mask = np.clip((yn_01 - 0.44) / 0.56, 0.0, 1.0)
    persp_u = _XN / np.maximum(0.18, yn_01 - 0.25)
    ground_dots = ((0.5 + 0.5 * np.sin(persp_u * 42.0 + disp * 10.0)) ** 8.0) * (
        (0.5 + 0.5 * np.cos(_YY * 0.35 - t * 6.0)) ** 4.0
    ) * ground_mask

    amber_lo = np.array([0.92, 0.42, 0.05], dtype=np.float32)[None, None, :]
    amber_hi = np.array([1.00, 0.86, 0.36], dtype=np.float32)[None, None, :]
    w_hi = np.clip(lum * 1.15 + slope * 0.65, 0.0, 1.0)[..., None]
    pt_col = amber_lo * (1.0 - w_hi) + amber_hi * w_hi

    intensity = (structure * (0.45 + 0.85 * lattice) + ground_dots * 0.78)[..., None]
    out = bg + pt_col * intensity

    if scan_streaks:
        # Diagonal green-cyan optical scan bands across the upper canopy (from Image 2)
        upper_env = np.clip((0.58 - yn_01) / 0.58, 0.0, 1.0)
        scan_wave = (0.5 + 0.5 * np.sin(_YY * 0.075 + _XX * 0.008 - t * 2.2)) ** 5.0
        scan_col = np.array([0.18, 0.92, 0.62], dtype=np.float32)[None, None, :]
        out += (scan_wave * upper_env * 0.26)[..., None] * scan_col

    return np.clip(out, 0.0, 1.0)


def draw_tve_viewfinder_hud(
    base_u8, t=0.0, dr_vals=(85, 89, 96, 97), right_red=False, hud_alpha=1.0, top_tag=None
):
    """
    Overlays the exact Blade Runner 2049 / Territory Studio TVE 1/2..4/4 Cyan CRT Viewfinder Bezel
    from User Images 1 & 2 onto `base_u8`.
    """
    if hud_alpha <= 0.01:
        return base_u8

    pil_im = Image.fromarray(base_u8).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    a_main = int(215 * hud_alpha)
    a_dim = int(145 * hud_alpha)
    a_faint = int(85 * hud_alpha)
    cyan = (108, 228, 242, a_main)
    cyan_dim = (98, 196, 212, a_dim)
    amber = (255, 204, 88, a_main)
    red_c = (232, 64, 64, a_main)

    # Outer cyan bezel glow + rounded frame
    d.rounded_rectangle([34, 24, W - 34, H - 24], radius=28, outline=(88, 212, 228, a_faint), width=5)
    d.rounded_rectangle([36, 26, W - 36, H - 26], radius=26, outline=cyan, width=2)

    # Top-left `[ / ]` + crimson status bar `[████  ]`
    d.rectangle([86, 52, 144, 80], outline=cyan, width=2)
    d.line([(98, 74), (112, 58)], fill=cyan, width=3)

    d.rectangle([160, 52, 272, 80], outline=red_c, width=2)
    fill_w = 76 + int(16 * math.sin(t * 1.4))
    d.rectangle([164, 56, 164 + fill_w, 76], fill=(232, 62, 62, int(225 * hud_alpha)))

    # Top-right `[ /" ]` prism box
    d.rectangle([W - 154, 52, W - 86, 80], outline=cyan, width=2)
    d.line([(W - 134, 72), (W - 118, 58)], fill=cyan, width=3)

    # Left & Right 16-tick vertical elevation ladders
    for i in range(16):
        yt = 104 + i * 28
        d.line([(82, yt), (148, yt)], fill=cyan, width=2)
        d.line([(W - 148, yt), (W - 82, yt)], fill=cyan, width=2)

    # Central Golden Horizon Reticle (`──┐  ┌──`)
    cy = int(H * 0.465)
    d.line([(int(W * 0.30), cy), (int(W * 0.70), cy)], fill=amber, width=2)
    by = cy - 22
    d.line([(int(W * 0.435), by), (int(W * 0.475), by), (int(W * 0.475), by + 13)], fill=amber, width=2)
    d.line([(int(W * 0.565), by), (int(W * 0.525), by), (int(W * 0.525), by + 13)], fill=amber, width=2)

    # 4 Vertical TVE Columns (`TVE 1/2`, `TVE 2/2`, `TVE 3/4`, `TVE 4/4`)
    cols_x = [172, 276, W - 368, W - 264]
    tve_lbls = ["1/2", "2/2", "3/4", "4/4"]
    f_sm = get_font("mono", 11)
    f_lg = get_font("mono", 28)

    for idx, x0 in enumerate(cols_x):
        cw = 92
        # Dotted ladder rungs
        for r in range(11):
            ry = 112 + r * 26
            for dx in range(0, cw, 6):
                d.rectangle([x0 + dx, ry, x0 + dx + 1, ry + 1], fill=(235, 195, 110, a_faint))

        # Glowing Amber Level Bar
        bar_y = int(190 + 44 * math.sin(t * (1.1 + idx * 0.2) + idx * 1.3))
        d.rectangle([x0, bar_y, x0 + cw, bar_y + 22], fill=(255, 196, 78, int(90 * hud_alpha)))
        d.line([(x0, bar_y), (x0 + cw, bar_y)], fill=(255, 232, 132, a_main), width=2)

        # `[⬆]` Chevron Box & `TVE` label
        by_box = 412
        d.rectangle([x0, by_box, x0 + 30, by_box + 30], outline=cyan, width=2)
        d.polygon([(x0 + 15, by_box + 5), (x0 + 23, by_box + 15), (x0 + 7, by_box + 15)], fill=cyan)
        d.polygon([(x0 + 15, by_box + 14), (x0 + 23, by_box + 24), (x0 + 7, by_box + 24)], fill=cyan)
        d.text((x0 + cw - 10, by_box + 16), str(idx + 1), font=f_sm, fill=amber)
        d.text((x0, by_box + 36), "TVE", font=f_sm, fill=cyan_dim)
        d.text((x0 + cw - 26, by_box + 36), tve_lbls[idx], font=f_sm, fill=cyan_dim)

        # Mini Waveform Scope Box (Blue on left, Crimson on right when `right_red=True` like Image 2!)
        sy = 474
        is_red = right_red and idx >= 2
        d.rectangle(
            [x0, sy, x0 + cw, sy + 48],
            fill=(120, 18, 24, int(110 * hud_alpha)) if is_red else (14, 68, 92, int(110 * hud_alpha)),
        )
        ly = sy + 16 + (idx % 2) * 14 + int(6 * math.sin(t * 2.2 + idx))
        d.line([(x0, ly), (x0 + cw, ly)], fill=red_c if is_red else (88, 228, 255, a_main), width=2)

        # Bottom Big 2-Digit Telemetry (`85`, `89`, `96`, `97` over `24556 DR`)
        ny = 582
        d.line([(x0, ny), (x0 + cw, ny)], fill=cyan, width=2)
        d.text((x0, ny + 6), f"{dr_vals[idx]:02d}", font=f_lg, fill=(220, 250, 255, a_main))
        d.text((x0, ny + 38), "24556", font=f_sm, fill=cyan_dim)
        d.text((x0 + cw - 18, ny + 38), "DR", font=f_sm, fill=cyan_dim)

        # Bottom Target Icon Box
        iy = ny + 58
        d.rectangle([x0, iy, x0 + 32, iy + 26], outline=red_c if idx >= 2 else cyan, width=1)
        d.ellipse([x0 + 10, iy + 7, x0 + 22, iy + 19], outline=red_c if idx >= 2 else cyan, width=1)

    if top_tag:
        tw = int(d.textlength(top_tag, font=f_sm)) + 24
        tx0 = (W - tw) // 2
        d.rectangle([tx0, 48, tx0 + tw, 74], fill=(6, 16, 22, int(215 * hud_alpha)), outline=amber, width=1)
        d.text((tx0 + 12, 55), top_tag, font=f_sm, fill=amber)

    return np.asarray(Image.alpha_composite(pil_im, ov).convert("RGB"), dtype=np.uint8)


def render_wireframe_canister_matrix_frame(rgb, disp, t=0.0):
    """
    Renders Mode II (directly modeled on User Image 3 `media_1793848931017_a60333cd.jpg`):
      - Left stack of 10 tactile slate-green `SPINNER P01..P10` slots
      - Center 3D deformed wireframe topography mesh (driven by real `disp`) + 7 tilted wireframe memory canisters
      - Right translucent Naurian Reconstruction & SCION Code Evaluator block
    """
    # Subtle dark slate-indigo background blended with 18% of the underlying Common Place
    bg = rgb * 0.18 + np.array([0.03, 0.07, 0.09], dtype=np.float32)[None, None, :]
    pil_im = Image.fromarray((np.clip(bg, 0.0, 1.0) * 255.0).astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    f_xs = get_font("mono", 10)
    f_sm = get_font("mono", 11)

    # Outer architectural grid lines
    for gx in range(180, W, 160):
        d.line([(gx, 0), (gx, H)], fill=(88, 164, 158, 32), width=1)
    for gy in range(80, H, 120):
        d.line([(0, gy), (W, gy)], fill=(88, 164, 158, 32), width=1)

    # 1. Left Column: 10 Tactile Slate-Green `SPINNER` Memory Canister Slots (Exact match to Image 3!)
    spinner_labels = [
        ("SPINNER P01 · V92", "NARAKA SHADOW-POOL"),
        ("SPINNER P02 · V22", "OVERSEER MIRROR BAY"),
        ("SPINNER P03 · V28", "RAIN PAVILION DEW"),
        ("SPINNER P04 · V45", "SILVER LINOCUT ARCH"),
        ("SPINNER P05 · V52", "ASCENT HEART-SCAN"),
        ("SPINNER P06 · V62", "ATLANTIS CAUSTIC NET"),
        ("SPINNER P07 · V80", "CRIMSON PLINTH SHAFT"),
        ("SPINNER P08 · V84", "ANKHU ASTRAL GALLERY"),
        ("SPINNER P09 · V77", "SHROUDED ARCADE GLOW"),
        ("SPINNER P13 · V98", "DAIMONJI AMBER BRIDGE"),
    ]
    for i, (sp_code, sp_sub) in enumerate(spinner_labels):
        y0 = 112 + i * 54
        is_sel = i == int(t * 0.8) % len(spinner_labels)
        fill_c = (96, 148, 138, 155) if is_sel else (68, 98, 94, 115)
        out_c = (255, 204, 92, 230) if is_sel else (128, 178, 172, 140)
        d.rectangle([32, y0, 176, y0 + 44], fill=fill_c, outline=out_c, width=1)
        d.text((42, y0 + 10), sp_code, font=f_xs, fill=(235, 250, 246, 240))
        d.text((42, y0 + 25), sp_sub[:19], font=f_xs, fill=(185, 224, 216, 195))

    # 2. Center-Left: 3D Deformed Wireframe Topography Grid (sampled from real `disp`!)
    gx0, gy0, gw, gh = 260, 310, 380, 220
    cols, rows = 24, 18
    for r in range(rows + 1):
        pts = []
        v = r / float(rows)
        for c in range(cols + 1):
            u = c / float(cols)
            sy = min(H - 1, int((0.25 + 0.5 * v) * H))
            sx = min(W - 1, int((0.25 + 0.5 * u) * W))
            elev = float(disp[sy, sx]) * 42.0 * math.sin(math.pi * u) * math.sin(math.pi * v)
            px = gx0 + u * gw + (v - 0.5) * 34.0
            py = gy0 + v * gh - elev
            pts.append((px, py))
        d.line(pts, fill=(185, 245, 220, 145), width=1)

    for c in range(0, cols + 1, 2):
        pts = []
        u = c / float(cols)
        for r in range(rows + 1):
            v = r / float(rows)
            sy = min(H - 1, int((0.25 + 0.5 * v) * H))
            sx = min(W - 1, int((0.25 + 0.5 * u) * W))
            elev = float(disp[sy, sx]) * 42.0 * math.sin(math.pi * u) * math.sin(math.pi * v)
            px = gx0 + u * gw + (v - 0.5) * 34.0
            py = gy0 + v * gh - elev
            pts.append((px, py))
        d.line(pts, fill=(185, 245, 220, 115), width=1)

    # 3. Center-Right: 7 Tilted 3D Wireframe Memory Cylinders (Exact match to Image 3!)
    cylinders = [
        (560, 195, 48, 145, "P01 · V92"),
        (725, 92, 48, 145, "P02 · V22"),
        (890, 145, 48, 145, "P04 · V45"),
        (665, 310, 48, 145, "P06 · V62"),
        (1015, 225, 48, 145, "P07 · V80"),
        (770, 455, 48, 145, "P09 · V77"),
        (825, 605, 48, 145, "P13 · V98"),
    ]
    ang = 0.46
    ca, sa = math.cos(ang), math.sin(ang)

    for ci, (cx, cy, rad, length, c_lbl) in enumerate(cylinders):
        is_hi = ci == (int(t * 0.8) % len(cylinders))
        wire_c = (255, 214, 102, 210) if is_hi else (152, 245, 204, 155)
        cap_c = (255, 230, 140, 235) if is_hi else (195, 255, 225, 215)
        rx, ry = rad, rad * 0.26
        h2 = length * 0.5

        def rot_pt(lx, ly):
            return (cx + lx * ca - ly * sa, cy + lx * sa + ly * ca)

        # Longitudinal ribs
        for k in range(16):
            a = (k / 16.0) * math.pi * 2.0 + t * 0.45
            lx = math.cos(a) * rx
            ly_off = math.sin(a) * ry
            p1 = rot_pt(lx, -h2 + ly_off)
            p2 = rot_pt(lx, h2 + ly_off)
            d.line([p1, p2], fill=wire_c, width=1)

        # Cross-sectional rings + glowing bottom cap
        for ring_i in range(-4, 5):
            ly_r = (ring_i / 4.0) * h2
            ring_pts = []
            for s in range(33):
                a = (s / 32.0) * math.pi * 2.0
                ring_pts.append(rot_pt(math.cos(a) * rx, ly_r + math.sin(a) * ry))
            if ring_i == 4:
                d.polygon(ring_pts, fill=(165, 255, 215, 58), outline=cap_c)
                d.line(ring_pts, fill=cap_c, width=3)
            else:
                d.line(ring_pts, fill=wire_c, width=1)

        d.text((cx - 28, cy - 6), c_lbl, font=f_xs, fill=cap_c)

    # 4. Right Column: Translucent Naurian Reconstruction & Scene Evaluator Code Box (Exact match to Image 3!)
    bx0, by0, bx1, by1 = W - 268, 128, W - 38, 445
    d.rectangle([bx0, by0, bx1, by1], fill=(8, 16, 20, 205), outline=(138, 215, 195, 135), width=1)
    code_lines = [
        "def evaluate_echo(canister_a, canister_b):",
        "  for view in working_set(canister_a):",
        "    try:",
        "      clue = isolate_tve(view, ch=1..4)",
        "      if water_delta(clue, canister_b):",
        "        return expose_echo(clue)",
        "    except DuplicateVision:",
        "      pass",
        "",
        "# NAURIAN RECONSTRUCTION:",
        "# <fragment> [enters] <working_set>",
        "#   -> [isolate] <TVE 1/2..4/4>",
        "#   -> [scrub/reframe] <clue V92>",
        "#   -> [compare] <P01 <-> P10 ECHO>",
        "",
        "STATUS = 'ECHO_DISCREPANCY_LOCKED'",
        "CANISTER_ACTIVE = 'P01_V92_NARAKA'",
        "OPTICAL_SHADER  = 'FX01..FX14_GLSL'",
    ]
    for li, ln in enumerate(code_lines):
        d.text((bx0 + 10, by0 + 12 + li * 16), ln, font=f_xs, fill=(182, 232, 214, 215))

    return np.asarray(Image.alpha_composite(pil_im, ov).convert("RGB"), dtype=np.uint8)


def render_echo_split_comparator_frame(rgb_a, disp_a, slope_a, rgb_b, disp_b, slope_b, t=0.0):
    """
    Renders Mode III (PDF Section 06: "What the echo exposes"):
      - Split-screen TVE Viewfinder comparing `P01 · V92` (Left) vs `P10 · V94` (Right)
      - Shows how the same flooded market underpass changes water ripples and optical state between the two poems,
        with blue scopes on the left (`31 / 79`) and crimson scopes on the right (`61 / 82`, exact match to Image 2!).
    """
    pc_a = render_amber_pointcloud_scope(rgb_a, disp_a, slope_a, t=t, scan_streaks=False)
    pc_b = render_amber_pointcloud_scope(rgb_b, disp_b, slope_b, t=t + 1.2, scan_streaks=True)

    # Blend 55% real cinema + 45% amber LiDAR point-cloud so both the painted water/figures and the 3D point-cloud are legible!
    left_view = np.clip(rgb_a * 0.55 + pc_a * 0.55, 0.0, 1.0)
    right_view = np.clip(rgb_b * 0.55 + pc_b * 0.55, 0.0, 1.0)

    w_right = np.clip((_XX - W * 0.5 + 16.0) / 32.0, 0.0, 1.0)[..., None]
    comp = left_view * (1.0 - w_right) + right_view * w_right

    # Highlight the water-movement discrepancy along the center seam
    diff = np.abs(disp_a - disp_b) + np.linalg.norm(rgb_a - rgb_b, axis=-1) * 0.5
    seam_env = np.exp(-((_XX - W * 0.5) / 72.0) ** 2)
    amber_diff = np.array([1.0, 0.52, 0.14], dtype=np.float32)[None, None, :]
    comp = np.clip(comp + (diff * seam_env * 0.55)[..., None] * amber_diff, 0.0, 1.0)

    u8 = (comp * 255.0).astype(np.uint8)
    u8 = draw_tve_viewfinder_hud(
        u8,
        t=t,
        dr_vals=(31, 79, 61, 82),  # Exact match to User Image 2's numbers (31, 79, 61, 82)!
        right_red=True,
        hud_alpha=1.0,
        top_tag="ECHO COMPARATOR · P01 (V92 UNDERPASS)  <->  P10 (V94 ECHO) · WATER RIPPLE DELTA",
    )
    return u8


def render_stelline_condensation_frame(rgb, disp, slope, u_condense, t=0.0):
    """
    Renders Mode IV: As `u_condense` moves from `0.0 -> 1.0`, the Amber LiDAR Point-Cloud and TVE Glass Bezel
    condense and dissolve smoothly into 100% unobstructed 16:9 widescreen Afterlight Cinema!
    """
    pc = render_amber_pointcloud_scope(rgb, disp, slope, t=t, scan_streaks=True)
    # Depth-ordered condensation wave: foreground condenses into painted cinema first, then deep horizon
    w_cinema = np.clip(u_condense * 1.25 + (disp - 0.5) * 0.35 * math.sin(math.pi * u_condense), 0.0, 1.0)[..., None]
    blended = np.clip(pc * (1.0 - w_cinema) + rgb * w_cinema, 0.0, 1.0)
    u8 = (blended * 255.0).astype(np.uint8)

    hud_a = max(0.0, 1.0 - smootherstep(max(0.0, (u_condense - 0.25) / 0.65)))
    u8 = draw_tve_viewfinder_hud(
        u8,
        t=t,
        dr_vals=(85, 89, 96, 97),
        right_red=False,
        hud_alpha=hud_a,
        top_tag="STELLINE / VESPER CONDENSATION · POINT-CLOUD -> UNOBSTRUCTED 16:9 CINEMA" if hud_a > 0.15 else None,
    )
    return u8


def main():
    view_map = json.load(open(os.path.join(OUT_DIR, "bible_view_map.json")))

    rgb_92, disp_92, slope_92 = load_view_rgb_and_disp(92, view_map)  # P01 Underpass Shadow-Pool
    rgb_94, disp_94, slope_94 = load_view_rgb_and_disp(94, view_map)  # P10 Underpass Bathers (Echo)
    rgb_98, disp_98, slope_98 = load_view_rgb_and_disp(98, view_map)  # P13 Daimonji Amber Bridge
    rgb_80, disp_80, slope_80 = load_view_rgb_and_disp(80, view_map)  # P07 Naraka Red Shaft

    # 1. Build the 4-Panel 2560x1440 Visual Proof Contact Sheet
    p1_pc = render_amber_pointcloud_scope(rgb_98, disp_98, slope_98, t=1.2, scan_streaks=False)
    panel_1 = draw_tve_viewfinder_hud(
        (p1_pc * 255.0).astype(np.uint8),
        t=1.2,
        dr_vals=(85, 89, 96, 97),  # Exact match to User Image 1!
        right_red=False,
        hud_alpha=1.0,
        top_tag="MODE I · TVE 1/2–4/4 AMBER LIDAR POINT-CLOUD VIEWFINDER (CANISTER P13 · V98)",
    )

    panel_2 = render_wireframe_canister_matrix_frame(rgb_80, disp_80, t=2.0)

    panel_3 = render_echo_split_comparator_frame(rgb_92, disp_92, slope_92, rgb_94, disp_94, slope_94, t=1.8)

    panel_4 = render_stelline_condensation_frame(rgb_92, disp_92, slope_92, u_condense=0.58, t=2.4)

    sheet = Image.new("RGB", (W * 2, H * 2), (6, 14, 18))
    sheet.paste(Image.fromarray(panel_1), (0, 0))
    sheet.paste(Image.fromarray(panel_2), (W, 0))
    sheet.paste(Image.fromarray(panel_3), (0, H))
    sheet.paste(Image.fromarray(panel_4), (W, H))

    sheet_out = os.path.join(OUT_DIR, "vesper_narrative_apparatus_proof.png")
    sheet.save(sheet_out)
    sheet.save(os.path.join(ARTIFACT_DIR, "vesper_narrative_apparatus_proof.png"))
    print("Saved 2560x1440 Vesper Narrative Apparatus Proof Sheet:", sheet_out, flush=True)

    # 2. Render 24.0s (576 frames) Apparatus Reel (`wygwyl_vesper_apparatus_reel.mp4`)
    #    - 0..6s: Mode II (14-Canister Wireframe Matrix & Naurian Ingest)
    #    - 6..12s: Mode I (TVE 1/2..4/4 Amber Point-Cloud Viewfinder orbiting V98 & V92)
    #    - 12..18s: Mode III (Precrime Echo Split Comparator: P01 V92 <-> P10 V94 Water Mismatch)
    #    - 18..24s: Mode IV (Stelline/Vesper Condensation: Point-Cloud & TVE Bezel condense into pure 16:9 Cinema!)
    frames = []
    n_total = int(24.0 * FPS)
    for f_i in range(n_total):
        t = f_i / float(FPS)
        pan_x = 18.0 * math.sin(t * 0.65)
        pan_y = 6.0 * math.cos(t * 0.50)

        if t < 6.0:
            w_rgb = warp_multiplane_3d(rgb_80, disp_80, pan_x, pan_y, 1.08, 0.03)
            frames.append(render_wireframe_canister_matrix_frame(w_rgb, disp_80, t=t))
        elif t < 12.0:
            u_local = (t - 6.0) / 6.0
            w_rgb = warp_multiplane_3d(rgb_98, disp_98, pan_x, pan_y, 1.08 + 0.05 * u_local, 0.04 * u_local)
            pc = render_amber_pointcloud_scope(w_rgb, disp_98, slope_98, t=t, scan_streaks=True)
            frames.append(
                draw_tve_viewfinder_hud(
                    (pc * 255.0).astype(np.uint8),
                    t=t,
                    dr_vals=(85, 89, 96, 97),
                    right_red=False,
                    hud_alpha=1.0,
                    top_tag="MODE I · TVE 1/2–4/4 AMBER POINT-CLOUD SCOPE · CANISTER P13 (V98)",
                )
            )
        elif t < 18.0:
            w_a = warp_multiplane_3d(rgb_92, disp_92, pan_x, pan_y, 1.10, 0.03)
            w_b = warp_multiplane_3d(rgb_94, disp_94, pan_x, pan_y, 1.10, 0.03)
            frames.append(render_echo_split_comparator_frame(w_a, disp_92, slope_92, w_b, disp_94, slope_94, t=t))
        else:
            u_cond = min(1.0, (t - 18.0) / 5.2)
            w_rgb = warp_multiplane_3d(rgb_92, disp_92, pan_x, pan_y, 1.08 + 0.06 * u_cond, 0.04 * u_cond)
            frames.append(render_stelline_condensation_frame(w_rgb, disp_92, slope_92, u_condense=u_cond, t=t))

    reel_mp4 = os.path.join(OUT_DIR, "wygwyl_vesper_apparatus_reel.mp4")
    encode_video_with_real_audio(frames, reel_mp4, 0.0)
    shutil.copy2(reel_mp4, os.path.join(VIDEOS_DIR, "wygwyl_vesper_apparatus_reel.mp4"))
    shutil.copy2(reel_mp4, os.path.join(ARTIFACT_DIR, "wygwyl_vesper_apparatus_reel.mp4"))
    print("Saved 24.0s Vesper Apparatus Reel:", reel_mp4, flush=True)


if __name__ == "__main__":
    main()
