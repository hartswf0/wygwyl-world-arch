#!/usr/bin/env python3
"""
Builds the Vesper / Stelline Narrative Apparatus Visual Proof & 24s Apparatus Reel
grounded 100% in our actual 3D architectural designs (`_city/hdl.json`, `_city/landmarks_ref.mjs`,
`_city/kit_ref.mjs`) and real worldtext (`shot.json` Midjourney prompts, camera solves & detections,
`multiplane.json` depth planes, `perceive.json` squint/SSIM metrics, `dossier/01..14.json` prop/set
build specs, and `assembly/assembly_p1..33.txt` working poetry drafts):
  - `vesper_narrative_apparatus_proof.png` (2560x1440 2x2 sheet in both OUT_DIR and ARTIFACT_DIR)
  - `wygwyl_vesper_apparatus_reel.mp4` (24.0s at 1280x720 24fps in OUT_DIR, VIDEOS_DIR, and ARTIFACT_DIR)
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
from vesper_3d_world_data import build_vesper_world_bundle

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


def project_3d_point(x, y, z, cx, cy, scale, yaw=0.58, pitch=0.42, roll=0.0):
    """Projects a normalized 3D point `(x, y, z)` (`z` up) onto 2D screen `(sx, sy)` with perspective."""
    cyw, syw = math.cos(yaw), math.sin(yaw)
    x1 = x * cyw - y * syw
    y1 = x * syw + y * cyw
    z1 = z

    cp, sp = math.cos(pitch), math.sin(pitch)
    y2 = y1 * cp - z1 * sp
    z2 = y1 * sp + z1 * cp
    x2 = x1

    if abs(roll) > 1e-4:
        cr, sr = math.cos(roll), math.sin(roll)
        xr = x2 * cr - z2 * sr
        zr = x2 * sr + z2 * cr
        x2, z2 = xr, zr

    persp = 3.2 / max(1.4, 3.2 + y2 * 0.65)
    sx = cx + x2 * scale * persp
    sy = cy - z2 * scale * persp
    return sx, sy, y2


def draw_3d_wireframe_model(
    d, wire3d, cx, cy, scale, yaw=0.58, pitch=0.42, roll=0.0, is_active=False, alpha_mul=1.0, show_title=True
):
    """
    Renders an authentic 3D architectural / landmark wireframe from `vesper_world_bundle.json`
    (`HDL:severn`, `HDL:chapel`, `HDL:marquee`, `HDL:clocktower`, `HDL:cafe + 3-Masted Ship`,
    `LMK:white_temple 16-rib vault`, `LMK:viaduct`, etc.) with:
      - `#5fe8ff` Kintsugi Seams (`role == 'seam'`)
      - `#ecebe4` `+4.00m` Salt Line Datum (`role == 'salt_line'`)
      - `#ffbe44` Amber Hero Features (`role == 'accent'`)
      - `#8ef6c8` / `#58d4e4` Structural Shell & Interior Room Partitions (`role == 'shell' / 'room'`)
    """
    f_xs = get_font("mono", 10)
    a_hi = int(235 * alpha_mul)
    a_mid = int(175 * alpha_mul)
    a_lo = int(105 * alpha_mul)

    role_colors = {
        "shell": (255, 212, 108, a_mid) if is_active else (142, 242, 204, a_mid),
        "room": (118, 215, 225, a_lo) if is_active else (96, 185, 175, a_lo),
        "prop": (255, 165, 82, a_mid),
        "seam": (95, 232, 255, a_hi),       # _city/kit_ref.mjs THE SEAM (#5fe8ff)
        "salt_line": (236, 235, 228, a_hi),  # _city/kit_ref.mjs THE +4.00m SALT LINE (#ecebe4)
        "accent": (255, 204, 84, a_hi) if is_active else (175, 255, 224, a_hi),
    }

    # Base glowing architectural plinth footprint
    plinth_pts = []
    for px, py in [(-0.85, -0.65), (0.85, -0.65), (0.85, 0.65), (-0.85, 0.65)]:
        sx, sy, _ = project_3d_point(px, py, -0.68, cx, cy, scale, yaw, pitch, roll)
        plinth_pts.append((sx, sy))
    d.polygon(
        plinth_pts,
        fill=(255, 196, 78, int(34 * alpha_mul)) if is_active else (88, 218, 188, int(22 * alpha_mul)),
        outline=(255, 214, 102, a_mid) if is_active else (130, 235, 198, a_lo),
    )

    for seg in wire3d.get("segments", []):
        x1, y1, z1, x2, y2, z2, role = seg
        p1 = project_3d_point(x1, y1, z1, cx, cy, scale, yaw, pitch, roll)
        p2 = project_3d_point(x2, y2, z2, cx, cy, scale, yaw, pitch, roll)
        col = role_colors.get(role, role_colors["shell"])
        w_line = 2 if role in ("seam", "salt_line", "accent") and is_active else 1
        d.line([(p1[0], p1[1]), (p2[0], p2[1])], fill=col, width=w_line)

    if show_title:
        title = wire3d.get("title", "HDL MODEL")
        short_t = title.split("·")[0].strip() + " · " + title.split("·")[-1].strip()[:22] if "·" in title else title[:32]
        tw = int(d.textlength(short_t, font=f_xs)) + 10
        d.rectangle(
            [cx - tw // 2, cy + int(scale * 0.68), cx + tw // 2, cy + int(scale * 0.68) + 16],
            fill=(6, 16, 22, int(210 * alpha_mul)),
            outline=(255, 204, 84, a_mid) if is_active else (95, 232, 255, a_lo),
            width=1,
        )
        d.text(
            (cx - tw // 2 + 5, cy + int(scale * 0.68) + 2),
            short_t,
            font=f_xs,
            fill=(255, 218, 118, a_hi) if is_active else (185, 248, 228, a_hi),
        )


def draw_isometric_hdl_floorplan_box(d, poem_data, cx, cy, scale=88.0, angle=-0.52, t=0.0):
    """
    Directly replaces the bottom-center tilted 3D floorplan & point-cloud burst in User Image 3
    with our actual `_city/hdl.json` / `dossier.sets` 3D room & interior-prop floorplan,
    metric scale bars (`0.0m ── 5.0m ── 10.0m · +4.00m SALT LINE`), and point-cloud bursts!
    """
    f_xs = get_font("mono", 9)
    rooms = poem_data["wire3d"].get("floorplan_rooms", [])
    if not rooms:
        return

    max_x = max((r["x"] + r["w"] for r in rooms), default=16.0)
    max_y = max((r["y"] + r["d"] for r in rooms), default=12.0)
    span = max(max_x, max_y, 1.0)
    ca, sa = math.cos(angle), math.sin(angle)

    def iso_pt(rx, ry, rz=0.0):
        nx = (rx / span - 0.5) * scale * 1.45
        ny = (ry / span - 0.5) * scale * 1.05
        ix = cx + (nx * ca - ny * sa)
        iy = cy + (nx * sa + ny * ca) * 0.68 - rz * 4.2
        return (ix, iy)

    # Outer double-walled 3D floorplan tray
    outer_b = [iso_pt(-0.6, -0.6, 0), iso_pt(max_x + 0.6, -0.6, 0), iso_pt(max_x + 0.6, max_y + 0.6, 0), iso_pt(-0.6, max_y + 0.6, 0)]
    outer_t = [iso_pt(-0.6, -0.6, 3.2), iso_pt(max_x + 0.6, -0.6, 3.2), iso_pt(max_x + 0.6, max_y + 0.6, 3.2), iso_pt(-0.6, max_y + 0.6, 3.2)]
    d.polygon(outer_b, fill=(12, 32, 36, 120), outline=(145, 238, 210, 175))
    d.line(outer_t + [outer_t[0]], fill=(185, 252, 232, 215), width=2)
    for i in range(4):
        d.line([outer_b[i], outer_t[i]], fill=(145, 238, 210, 165), width=1)

    # Interior HDL rooms & furniture prop blocks
    for ri, rm in enumerate(rooms[:7]):
        rx, ry, rw, rd = rm["x"], rm["y"], rm["w"], rm["d"]
        rb = [iso_pt(rx, ry, 0), iso_pt(rx + rw, ry, 0), iso_pt(rx + rw, ry + rd, 0), iso_pt(rx, ry + rd, 0)]
        rt = [iso_pt(rx, ry, 2.4), iso_pt(rx + rw, ry, 2.4), iso_pt(rx + rw, ry + rd, 2.4), iso_pt(rx, ry + rd, 2.4)]
        d.line(rb + [rb[0]], fill=(95, 232, 255, 165), width=1)
        d.line(rt + [rt[0]], fill=(210, 255, 240, 195), width=1)
        for k in range(4):
            d.line([rb[k], rt[k]], fill=(130, 220, 205, 125), width=1)
        # Room ID + furniture prop cubes inside room
        rc = iso_pt(rx + rw * 0.5, ry + rd * 0.5, 1.2)
        d.text((rc[0] - 14, rc[1] - 5), rm["id"][:8], font=f_xs, fill=(255, 218, 120, 225))
        for pi in range(min(2, len(rm.get("props", [])))):
            px = rx + rw * (0.28 + 0.42 * pi)
            py = ry + rd * 0.5
            pb = [iso_pt(px - 0.4, py - 0.3, 0), iso_pt(px + 0.4, py - 0.3, 0), iso_pt(px + 0.4, py + 0.3, 0), iso_pt(px - 0.4, py + 0.3, 0)]
            d.polygon(pb, fill=(195, 255, 235, 140), outline=(255, 214, 102, 210))

    # Glowing white/cyan 3D LiDAR point-cloud starbursts next to the floorplan (matching Image 3!)
    for bi, (bx_off, by_off, rad, col_b) in enumerate([
        (-scale * 1.15, -scale * 0.38, 34, (235, 252, 248, 220)),
        (-scale * 1.52, -scale * 0.12, 28, (142, 208, 202, 165)),
    ]):
        bcx, bcy = cx + bx_off, cy + by_off
        for ray in range(44):
            ang = ray * 0.1428 + t * 0.25 + bi
            r_len = rad * (0.35 + 0.65 * abs(math.sin(ray * 1.7 + bi)))
            ex = bcx + math.cos(ang) * r_len
            ey = bcy + math.sin(ang) * r_len * 0.78
            d.line([(bcx, bcy), (ex, ey)], fill=col_b, width=1)

    # Metric scale bars at bottom-left (`0.0m ── 5.0m ── 10.0m`, matching Image 3's `0.5 / 1.0` scale bars!)
    sb_x, sb_y = int(cx - scale * 2.1), int(cy + scale * 0.62)
    d.line([(sb_x, sb_y), (sb_x + 110, sb_y)], fill=(165, 238, 225, 200), width=1)
    d.line([(sb_x, sb_y), (sb_x, sb_y + 6)], fill=(165, 238, 225, 200), width=1)
    d.line([(sb_x + 110, sb_y), (sb_x + 110, sb_y + 6)], fill=(165, 238, 225, 200), width=1)
    d.text((sb_x + 92, sb_y + 7), f"{span * 0.5:.1f}m", font=f_xs, fill=(165, 238, 225, 210))

    d.line([(sb_x, sb_y + 18), (sb_x + 210, sb_y + 18)], fill=(165, 238, 225, 200), width=1)
    d.line([(sb_x, sb_y + 18), (sb_x, sb_y + 24)], fill=(165, 238, 225, 200), width=1)
    d.line([(sb_x + 210, sb_y + 18), (sb_x + 210, sb_y + 24)], fill=(165, 238, 225, 200), width=1)
    d.text((sb_x + 186, sb_y + 25), f"{span:.1f}m · +4.0m LINE", font=f_xs, fill=(255, 214, 102, 220))


def render_amber_pointcloud_scope(rgb, disp, slope, t=0.0, scan_streaks=True):
    """
    Renders the glowing golden/amber 3D LiDAR point-cloud aesthetic from User Images 1 & 2
    over a deep phosphor-teal CRT field (`#06161d`), with perspective ground streaks and green-cyan scan rays.
    """
    yn_01 = _YY / float(H)
    bg = np.zeros((H, W, 3), dtype=np.float32)
    bg[..., 0] = 0.024 + 0.030 * (1.0 - yn_01)
    bg[..., 1] = 0.088 + 0.085 * (1.0 - yn_01)
    bg[..., 2] = 0.118 + 0.105 * (1.0 - yn_01)

    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    structure = np.clip(lum * 1.25 + slope * 1.35 + disp * 0.28, 0.0, 1.0)

    gx_coord = (_XX * 0.28 + disp * 24.0 + t * 1.5)
    gy_coord = (_YY * 0.28 + disp * 32.0)
    lattice = (0.5 + 0.5 * np.sin(gx_coord * 2.1) * np.cos(gy_coord * 2.1)) ** 3.0

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
        upper_env = np.clip((0.58 - yn_01) / 0.58, 0.0, 1.0)
        scan_wave = (0.5 + 0.5 * np.sin(_YY * 0.075 + _XX * 0.008 - t * 2.2)) ** 5.0
        scan_col = np.array([0.18, 0.92, 0.62], dtype=np.float32)[None, None, :]
        out += (scan_wave * upper_env * 0.26)[..., None] * scan_col

    return np.clip(out, 0.0, 1.0)


def draw_tve_viewfinder_hud(
    base_u8,
    poem_data,
    shot_data,
    t=0.0,
    dr_vals=(85, 89, 96, 97),
    right_red=False,
    hud_alpha=1.0,
    top_tag=None,
    show_3d_ghost=True,
):
    """
    Overlays the Blade Runner 2049 / Territory Studio TVE 1/2..4/4 Cyan CRT Viewfinder Bezel
    from User Images 1 & 2 onto `base_u8`, now carrying 100% real data from `shot.json`,
    `multiplane.json`, `perceive.json`, `dossier/*.json`, and `_city/hdl.json`.
    """
    if hud_alpha <= 0.01:
        return base_u8

    pil_im = Image.fromarray(base_u8).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    a_main = int(220 * hud_alpha)
    a_dim = int(155 * hud_alpha)
    a_faint = int(85 * hud_alpha)
    cyan = (108, 228, 242, a_main)
    cyan_dim = (98, 196, 212, a_dim)
    seam_c = (95, 232, 255, a_main)
    salt_c = (236, 235, 228, a_main)
    amber = (255, 204, 88, a_main)
    red_c = (232, 64, 64, a_main)

    f_xs = get_font("mono", 10)
    f_sm = get_font("mono", 11)
    f_lg = get_font("mono", 28)

    # Outer cyan bezel glow + rounded frame
    d.rounded_rectangle([34, 24, W - 34, H - 24], radius=28, outline=(88, 212, 228, a_faint), width=5)
    d.rounded_rectangle([36, 26, W - 36, H - 26], radius=26, outline=cyan, width=2)

    # Top-left `[ / ]` + crimson status bar `[████  ]` + real Perceive Squint & Tide Gate readout
    d.rectangle([86, 52, 144, 80], outline=cyan, width=2)
    d.line([(98, 74), (112, 58)], fill=cyan, width=3)

    d.rectangle([160, 52, 272, 80], outline=red_c, width=2)
    fill_w = 76 + int(16 * math.sin(t * 1.4))
    d.rectangle([164, 56, 164 + fill_w, 76], fill=(232, 62, 62, int(225 * hud_alpha)))

    perc = shot_data.get("perceive", {})
    cam = shot_data.get("camera", {})
    d.text(
        (86, 84),
        f"READS @ σ={perc.get('reads_at_sigma', 8)} · dE={perc.get('dE', 4.5)} · SSIM={perc.get('value_ssim', 0.92)}",
        font=f_xs,
        fill=cyan_dim,
    )

    # Top-right `[ /" ]` Atlantis Emblem prism box + Solved Camera Lens & Height
    d.rectangle([W - 154, 52, W - 86, 80], outline=cyan, width=2)
    d.line([(W - 134, 72), (W - 118, 58)], fill=cyan, width=3)
    # Draw the +4.00m Salt Line inside the top-right box (`_city/kit_ref.mjs` emblem)
    d.line([(W - 154, 68), (W - 86, 68)], fill=salt_c, width=1)
    cam_txt = f"{cam.get('focal_mm', 24.7)}mm · FOV {cam.get('fov_deg', 72.2)}° · h={cam.get('height_m', 0.32)}m"
    d.text((W - 86 - int(d.textlength(cam_txt, font=f_xs)), 84), cam_txt, font=f_xs, fill=amber)

    # Left & Right 16-tick vertical elevation ladders (with +4.00m Salt Line Datum tick highlighted!)
    for i in range(16):
        yt = 104 + i * 28
        is_salt_tick = i == 9  # 4/10 height from bottom = +4.00m Salt Line Datum!
        t_col = salt_c if is_salt_tick else cyan
        t_w = 3 if is_salt_tick else 2
        d.line([(82, yt), (148, yt)], fill=t_col, width=t_w)
        d.line([(W - 148, yt), (W - 82, yt)], fill=t_col, width=t_w)
        if is_salt_tick:
            d.text((84, yt - 13), "+4.00m LINE", font=f_xs, fill=salt_c)
            d.text((W - 148, yt - 13), "DATUM +4m", font=f_xs, fill=salt_c)

    # Central Golden Horizon Reticle (`──┐  ┌──`) driven by real camera solve & +4.00m Salt Line
    cy = int(H * 0.465)
    d.line([(int(W * 0.30), cy), (int(W * 0.70), cy)], fill=amber, width=2)
    by = cy - 22
    d.line([(int(W * 0.435), by), (int(W * 0.475), by), (int(W * 0.475), by + 13)], fill=amber, width=2)
    d.line([(int(W * 0.565), by), (int(W * 0.525), by), (int(W * 0.525), by + 13)], fill=amber, width=2)
    hor_lbl = f"HORIZON SOLVE · {cam.get('shot_class', 'ground').upper()} · PITCH {cam.get('pitch_deg', 3.8):+.1f}° · CONF {cam.get('confidence', 0.98)}"
    d.text((int(W * 0.50) - int(d.textlength(hor_lbl, font=f_xs)) // 2, cy + 6), hor_lbl, font=f_xs, fill=amber)

    # Real Grounding-DINO 3D Object Detection Brackets inside the central viewport (`shot.json.detections`)
    for det in shot_data.get("detections", [])[:3]:
        bn = det.get("box_norm", [0.3, 0.3, 0.6, 0.7])
        x0_d = max(390, min(W - 410, int(bn[0] * W)))
        y0_d = max(120, min(H - 180, int(bn[1] * H)))
        x1_d = max(x0_d + 48, min(W - 390, int(bn[2] * W)))
        y1_d = max(y0_d + 36, min(H - 140, int(bn[3] * H)))
        # Corner brackets only so we never obscure the point cloud
        blen = 10
        for cx_b, cy_b, dx_b, dy_b in [
            (x0_d, y0_d, blen, blen), (x1_d, y0_d, -blen, blen),
            (x0_d, y1_d, blen, -blen), (x1_d, y1_d, -blen, -blen),
        ]:
            d.line([(cx_b, cy_b), (cx_b + dx_b, cy_b)], fill=seam_c, width=1)
            d.line([(cx_b, cy_b), (cx_b, cy_b + dy_b)], fill=seam_c, width=1)
        d.text(
            (x0_d + 4, y0_d + 2),
            f"{det['label'].upper()} {int(det['score']*100)}%",
            font=f_xs,
            fill=seam_c,
        )

    # Optional 3D Architectural Wireframe Registration Overlay inside the Point-Cloud Scope
    if show_3d_ghost and poem_data and "wire3d" in poem_data:
        draw_3d_wireframe_model(
            d,
            poem_data["wire3d"],
            cx=int(W * 0.50),
            cy=int(H * 0.56),
            scale=115.0,
            yaw=0.52 + t * 0.18,
            pitch=0.36,
            is_active=True,
            alpha_mul=0.52 * hud_alpha,
            show_title=False,
        )

    # 4 Vertical TVE Columns (`TVE 1/2`, `TVE 2/2`, `TVE 3/4`, `TVE 4/4`) with Real Layer Sub-Labels
    cols_x = [172, 276, W - 368, W - 264]
    tve_lbls = ["1/2", "2/2", "3/4", "4/4"]
    planes = shot_data.get("planes", [])
    z_p1 = next((p["z_m"] for p in planes if p["id"] == "P1" and p.get("z_m")), 1.64)
    hero_prop = (poem_data.get("props") or [{"id": "prop", "scale_cm": 12}])[0]
    w_title = poem_data["wire3d"]["title"].split("·")[0].strip() if poem_data else "HDL:3D"
    real_sub_tags = [
        (f"{z_p1:.1f}M", "P1·FG"),
        (f"{hero_prop.get('scale_cm') or 18}CM", "PROP"),
        (w_title[:7], "3D"),
        (f"SSIM{int(perc.get('value_ssim', 0.92)*100)}", poem_data.get("fx_code", "FX")),
    ]

    for idx, x0 in enumerate(cols_x):
        cw = 92
        for r in range(11):
            ry = 112 + r * 26
            for dx in range(0, cw, 6):
                d.rectangle([x0 + dx, ry, x0 + dx + 1, ry + 1], fill=(235, 195, 110, a_faint))

        bar_y = int(190 + 44 * math.sin(t * (1.1 + idx * 0.2) + idx * 1.3))
        d.rectangle([x0, bar_y, x0 + cw, bar_y + 22], fill=(255, 196, 78, int(90 * hud_alpha)))
        d.line([(x0, bar_y), (x0 + cw, bar_y)], fill=(255, 232, 132, a_main), width=2)

        by_box = 412
        d.rectangle([x0, by_box, x0 + 30, by_box + 30], outline=cyan, width=2)
        d.polygon([(x0 + 15, by_box + 5), (x0 + 23, by_box + 15), (x0 + 7, by_box + 15)], fill=cyan)
        d.polygon([(x0 + 15, by_box + 14), (x0 + 23, by_box + 24), (x0 + 7, by_box + 24)], fill=cyan)
        d.text((x0 + cw - 10, by_box + 16), str(idx + 1), font=f_sm, fill=amber)
        d.text((x0, by_box + 36), "TVE", font=f_sm, fill=cyan_dim)
        d.text((x0 + cw - 26, by_box + 36), tve_lbls[idx], font=f_sm, fill=cyan_dim)

        sy = 474
        is_red = right_red and idx >= 2
        d.rectangle(
            [x0, sy, x0 + cw, sy + 48],
            fill=(120, 18, 24, int(110 * hud_alpha)) if is_red else (14, 68, 92, int(110 * hud_alpha)),
        )
        ly = sy + 16 + (idx % 2) * 14 + int(6 * math.sin(t * 2.2 + idx))
        d.line([(x0, ly), (x0 + cw, ly)], fill=red_c if is_red else (88, 228, 255, a_main), width=2)

        ny = 582
        d.line([(x0, ny), (x0 + cw, ny)], fill=cyan, width=2)
        d.text((x0, ny + 6), f"{dr_vals[idx]:02d}", font=f_lg, fill=(220, 250, 255, a_main))
        sub_l, sub_r = real_sub_tags[idx]
        d.text((x0, ny + 38), sub_l, font=f_xs, fill=cyan_dim)
        d.text((x0 + cw - int(d.textlength(sub_r, font=f_xs)), ny + 38), sub_r, font=f_xs, fill=amber)

        iy = ny + 58
        d.rectangle([x0, iy, x0 + 32, iy + 26], outline=red_c if idx >= 2 else cyan, width=1)
        d.ellipse([x0 + 10, iy + 7, x0 + 22, iy + 19], outline=red_c if idx >= 2 else cyan, width=1)

    # Bottom-Center Real Corpus Prompt, Prop & Worldtext Strip
    prompt_str = shot_data.get("prompt", "")
    if prompt_str:
        p_clean = f"PROMPT [{shot_data['id']}]: “{prompt_str[:78]}…”"
        prop_clean = f"HERO PROP: {hero_prop.get('id','')} ({hero_prop.get('scale_cm') or 15}cm) · {poem_data['wire3d']['title']}"
        bx0, bx1 = 384, W - 384
        d.rectangle([bx0, H - 84, bx1, H - 38], fill=(5, 14, 20, int(205 * hud_alpha)), outline=(95, 232, 255, a_dim), width=1)
        d.text((bx0 + 10, H - 79), p_clean[:68], font=f_xs, fill=(220, 248, 255, a_main))
        d.text((bx0 + 10, H - 61), prop_clean[:68], font=f_xs, fill=amber)

    if top_tag:
        tw = int(d.textlength(top_tag, font=f_sm)) + 24
        tx0 = (W - tw) // 2
        d.rectangle([tx0, 48, tx0 + tw, 74], fill=(6, 16, 22, int(220 * hud_alpha)), outline=amber, width=1)
        d.text((tx0 + 12, 55), top_tag, font=f_sm, fill=amber)

    return np.asarray(Image.alpha_composite(pil_im, ov).convert("RGB"), dtype=np.uint8)


def render_wireframe_canister_matrix_frame(rgb, disp, bundle, active_poem_idx=0, shot_vn=80, t=0.0):
    """
    Renders Mode II (modeled on User Image 3 `media_1793848931017_a60333cd.jpg`, redesigned to carry
    our actual 3D HDL / Landmark / Kit architectural wireframes, isometric room/prop floorplan,
    and real prompts, assembly drafts, and dossier build specs!):
      1. Left Column: 10 Tactile Slate-Green Slots with real HDL / Landmark IDs, footprints & hero props
      2. Center-Left: 3D Deformed Topography Mesh (`disp`) + Multiplane `P0..P5` depth strata (`z_median_m`)
      3. Bottom-Center: Tilted 3D Isometric HDL Room & Furniture Floorplan Blueprint + Scale Bars + Point-Cloud Bursts
      4. Center-Right: Constellation of 6 Real 3D Architectural Wireframe Models (`HDL:severn`, `HDL:chapel`,
         `HDL:marquee`, `HDL:clocktower`, `LMK:white_temple 16-rib vault`, `HDL:cafe + 3-Masted Ship`)
      5. Right Column: Translucent Worldtext, Assembly Draft, Midjourney Prompt & Dossier Build Spec Inspector
    """
    bg = rgb * 0.16 + np.array([0.025, 0.065, 0.085], dtype=np.float32)[None, None, :]
    pil_im = Image.fromarray((np.clip(bg, 0.0, 1.0) * 255.0).astype(np.uint8)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    f_xs = get_font("mono", 10)
    f_sm = get_font("mono", 11)

    # Outer architectural perspective grid lines
    for gx in range(180, W, 160):
        d.line([(gx, 0), (gx, H)], fill=(88, 164, 158, 30), width=1)
    for gy in range(80, H, 120):
        d.line([(0, gy), (W, gy)], fill=(88, 164, 158, 30), width=1)

    poems = bundle["poems"]
    shot_data = bundle["views_by_no"].get(str(shot_vn), poems[active_poem_idx]["views"][0])

    # 1. Left Column: 10 Real HDL / Landmark / Kit Slots
    slot_poem_indices = [0, 1, 2, 3, 5, 6, 7, 10, 11, 12]
    for row_i, p_idx in enumerate(slot_poem_indices):
        pm = poems[p_idx]
        y0 = 96 + row_i * 56
        is_sel = p_idx == active_poem_idx
        fill_c = (96, 148, 138, 165) if is_sel else (58, 92, 88, 120)
        out_c = (255, 204, 92, 235) if is_sel else (118, 175, 168, 145)
        d.rectangle([24, y0, 196, y0 + 48], fill=fill_c, outline=out_c, width=2 if is_sel else 1)

        w_tag = pm["wire3d"]["title"].split("·")[0].strip()
        v0_id = pm["views"][0]["id"] if pm["views"] else "V92"
        pr0 = pm["props"][0]["id"] if pm["props"] else "kit"
        d.text((32, y0 + 6), f"P{pm['num']} · {v0_id} · {w_tag}", font=f_xs, fill=(255, 218, 118, 245) if is_sel else (225, 248, 242, 235))
        d.text((32, y0 + 20), f"{pm['title'][:22]}", font=f_xs, fill=(240, 252, 248, 235))
        d.text((32, y0 + 33), f"prop: {pr0[:18]}", font=f_xs, fill=(165, 224, 212, 195))

    # 2. Center-Left: 3D Deformed Wireframe Topography Grid (`disp`) + Multiplane Depth Callouts
    gx0, gy0, gw, gh = 235, 255, 330, 190
    cols, rows = 22, 16
    for r in range(rows + 1):
        pts = []
        v = r / float(rows)
        for c in range(cols + 1):
            u = c / float(cols)
            sy = min(H - 1, int((0.25 + 0.5 * v) * H))
            sx = min(W - 1, int((0.25 + 0.5 * u) * W))
            elev = float(disp[sy, sx]) * 38.0 * math.sin(math.pi * u) * math.sin(math.pi * v)
            px = gx0 + u * gw + (v - 0.5) * 30.0
            py = gy0 + v * gh - elev
            pts.append((px, py))
        d.line(pts, fill=(175, 242, 215, 140), width=1)

    for c in range(0, cols + 1, 2):
        pts = []
        u = c / float(cols)
        for r in range(rows + 1):
            v = r / float(rows)
            sy = min(H - 1, int((0.25 + 0.5 * v) * H))
            sx = min(W - 1, int((0.25 + 0.5 * u) * W))
            elev = float(disp[sy, sx]) * 38.0 * math.sin(math.pi * u) * math.sin(math.pi * v)
            px = gx0 + u * gw + (v - 0.5) * 30.0
            py = gy0 + v * gh - elev
            pts.append((px, py))
        d.line(pts, fill=(175, 242, 215, 110), width=1)

    d.text((gx0, gy0 - 18), f"3D DEPTH-PRO MESH · {shot_data['id']} ({shot_data['camera']['focal_mm']}mm, h={shot_data['camera']['height_m']}m)", font=f_xs, fill=(95, 232, 255, 215))

    # 3. Bottom-Center: Tilted 3D Isometric HDL Floorplan & Interior Prop Blueprint + Point-Cloud Bursts
    draw_isometric_hdl_floorplan_box(d, poems[active_poem_idx], cx=495, cy=565, scale=86.0, angle=-0.52, t=t)

    # 4. Center-Right: Constellation of 6 Real 3D Architectural Wireframe Models (Replacing Generic Cylinders!)
    arch_constellation = [
        (0,  535, 172, 74.0, 0.55 + t * 0.22, 0.38),  # P01 HDL:severn (5 floors, 35 rooms, fire escapes)
        (2,  700, 102, 74.0, 0.48 + t * 0.20, 0.36),  # P03 HDL:chapel (gable roof, bell-cote, rose window)
        (7,  850, 152, 72.0, 0.62 + t * 0.18, 0.40),  # P08 HDL:marquee (THE NEW SINGLE, 6 poster boxes)
        (11, 645, 325, 76.0, 0.52 + t * 0.24, 0.38),  # P12 LMK:white_temple (16 concrete vault ribs over ruin)
        (10, 805, 365, 72.0, 0.60 + t * 0.21, 0.35),  # P11 HDL:clocktower (4 clock faces, spire needle)
        (12, 745, 555, 78.0, 0.45 + t * 0.19, 0.38),  # P13 HDL:cafe + Three-Masted Ship on 180m pier
    ]
    for p_idx, m_cx, m_cy, m_scale, m_yaw, m_pitch in arch_constellation:
        draw_3d_wireframe_model(
            d,
            poems[p_idx]["wire3d"],
            cx=m_cx,
            cy=m_cy,
            scale=m_scale,
            yaw=m_yaw,
            pitch=m_pitch,
            is_active=(p_idx == active_poem_idx),
            alpha_mul=1.0,
            show_title=True,
        )

    # 5. Right Column: Translucent Worldtext, Assembly Draft, Prompt & Dossier Build Box (100% Real Data!)
    act_p = poems[active_poem_idx]
    asm_list = act_p.get("assembly_pages") or []
    asm_0 = asm_list[min(1, len(asm_list) - 1)] if asm_list else {"file": "assembly_p2.txt", "reverse_header": ").tnoc( efiL fo tuO", "text": ""}
    asm_lines = [l.strip() for l in asm_0["text"].splitlines() if l.strip()][1:5]
    pr_0 = act_p["props"][0] if act_p["props"] else {"id": "vape_pen", "scale_cm": 12, "build": ""}
    hdl_m = act_p.get("hdl_meta") or {}
    fit_0 = (hdl_m.get("fit") or [{"saw": "reference still", "did": "3D wireframe room & kit geometry"}])[0]

    bx0, by0, bx1, by1 = W - 328, 86, W - 24, H - 36
    d.rectangle([bx0, by0, bx1, by1], fill=(6, 14, 19, 222), outline=(95, 232, 255, 165), width=1)

    real_lines = [
        (f"■ POEM P{act_p['num']} · {act_p['title'].upper()} ({act_p['district'].upper()})", (255, 208, 96, 245)),
        (f"  3D ASSET: {act_p['wire3d']['title'][:38]}", (95, 232, 255, 235)),
        (f"  NOTE: {act_p['wire3d']['subtitle'][:42]}", (175, 232, 218, 210)),
        ("", (0, 0, 0, 0)),
        (f"■ ASSEMBLY DRAFT [{asm_0['file']}]:", (255, 208, 96, 245)),
        (f"  HDR: {asm_0['reverse_header'][:40]}", (142, 245, 204, 230)),
    ]
    for al in asm_lines[:3]:
        real_lines.append((f"  “{al[:41]}”", (215, 242, 236, 215)))

    real_lines.extend([
        ("", (0, 0, 0, 0)),
        (f"■ DOSSIER HERO PROP [{pr_0['id']} · {pr_0.get('scale_cm') or 15}cm]:", (255, 208, 96, 245)),
        (f"  {pr_0.get('build', '')[:42]}", (185, 235, 222, 215)),
        (f"  {pr_0.get('build', '')[42:84]}", (185, 235, 222, 215)),
        ("", (0, 0, 0, 0)),
        ("■ 3D HDL FIT (_city/hdl.json):", (255, 208, 96, 245)),
        (f"  SAW: {fit_0.get('saw', '')[:39]}", (165, 225, 235, 215)),
        (f"  DID: {fit_0.get('did', '')[:39]}", (142, 245, 204, 225)),
        ("", (0, 0, 0, 0)),
        (f"■ MIDJOURNEY PROMPT [{shot_data['id']} · shot.json]:", (255, 208, 96, 245)),
        (f"  {shot_data.get('prompt', '')[:42]}", (215, 242, 236, 215)),
        (f"  {shot_data.get('prompt', '')[42:84]}", (215, 242, 236, 215)),
        (f"  {shot_data.get('prompt', '')[84:126]}", (215, 242, 236, 215)),
        ("", (0, 0, 0, 0)),
        ("■ MULTIPLANE & PERCEIVE (perceive.json):", (255, 208, 96, 245)),
        (f"  FELT: “{shot_data['perceive'].get('felt', '')[:37]}”", (185, 235, 222, 215)),
        (f"  READS@σ={shot_data['perceive']['reads_at_sigma']} · dE={shot_data['perceive']['dE']} · SSIM={shot_data['perceive']['value_ssim']}", (95, 232, 255, 230)),
        ("  DATUM: +4.00m SALT LINE · KINTSUGI SEAM", (236, 235, 228, 230)),
    ])

    y_cursor = by0 + 12
    for txt_ln, col_ln in real_lines:
        if not txt_ln:
            y_cursor += 6
            continue
        if y_cursor < by1 - 16:
            d.text((bx0 + 10, y_cursor), txt_ln, font=f_xs, fill=col_ln)
            y_cursor += 15

    # Top title banner
    top_tag = "MODE II · 3D HDL ARCHITECTURAL & LANDMARK WIREFRAME MATRIX, FLOORPLAN & REAL CORPUS INSPECTOR"
    tw = int(d.textlength(top_tag, font=f_sm)) + 24
    tx0 = (W - tw) // 2
    d.rectangle([tx0, 22, tx0 + tw, 48], fill=(6, 16, 22, 225), outline=(255, 204, 88, 220), width=1)
    d.text((tx0 + 12, 29), top_tag, font=f_sm, fill=(255, 204, 88, 240))

    return np.asarray(Image.alpha_composite(pil_im, ov).convert("RGB"), dtype=np.uint8)


def render_echo_split_comparator_frame(
    rgb_a, disp_a, slope_a, rgb_b, disp_b, slope_b, poem_a, shot_a, poem_b, shot_b, t=0.0
):
    """
    Renders Mode III (PDF Section 06: "What the echo exposes"):
      - Split-screen TVE Viewfinder comparing `P01 · V92` (Left) vs `P10 · V94` (Right)
      - Carries both shots' real `shot.json` prompts, camera solves, and 3D wireframe ghosts (`HDL:severn` vs `LMK:sunken_forum`).
    """
    pc_a = render_amber_pointcloud_scope(rgb_a, disp_a, slope_a, t=t, scan_streaks=False)
    pc_b = render_amber_pointcloud_scope(rgb_b, disp_b, slope_b, t=t + 1.2, scan_streaks=True)

    left_view = np.clip(rgb_a * 0.55 + pc_a * 0.55, 0.0, 1.0)
    right_view = np.clip(rgb_b * 0.55 + pc_b * 0.55, 0.0, 1.0)

    w_right = np.clip((_XX - W * 0.5 + 16.0) / 32.0, 0.0, 1.0)[..., None]
    comp = left_view * (1.0 - w_right) + right_view * w_right

    diff = np.abs(disp_a - disp_b) + np.linalg.norm(rgb_a - rgb_b, axis=-1) * 0.5
    seam_env = np.exp(-((_XX - W * 0.5) / 72.0) ** 2)
    amber_diff = np.array([1.0, 0.52, 0.14], dtype=np.float32)[None, None, :]
    comp = np.clip(comp + (diff * seam_env * 0.55)[..., None] * amber_diff, 0.0, 1.0)

    u8 = (comp * 255.0).astype(np.uint8)
    u8 = draw_tve_viewfinder_hud(
        u8,
        poem_data=poem_a,
        shot_data=shot_a,
        t=t,
        dr_vals=(31, 79, 61, 82),
        right_red=True,
        hud_alpha=1.0,
        top_tag="MODE III · ECHO COMPARATOR: P01 (V92 HDL:SEVERN)  <->  P10 (V94 FORUM DISH) · WATER RIPPLE DELTA",
        show_3d_ghost=False,
    )

    # Overlay Left vs Right 3D Wireframes & Prompt Comparison Callouts
    pil_im = Image.fromarray(u8).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f_xs = get_font("mono", 10)

    draw_3d_wireframe_model(d, poem_a["wire3d"], cx=int(W * 0.39), cy=int(H * 0.30), scale=68.0, yaw=0.5 + t * 0.2, pitch=0.36, is_active=True, alpha_mul=0.82)
    draw_3d_wireframe_model(d, poem_b["wire3d"], cx=int(W * 0.61), cy=int(H * 0.30), scale=68.0, yaw=-0.5 + t * 0.2, pitch=0.36, is_active=False, alpha_mul=0.82)

    d.line([(W // 2, 82), (W // 2, H - 90)], fill=(255, 196, 84, 185), width=2)
    d.text((388, 96), f"LEFT [P01 · {shot_a['id']}]: {shot_a.get('prompt','')[:34]}…", font=f_xs, fill=(95, 232, 255, 230))
    d.text((W // 2 + 12, 96), f"RIGHT [P10 · {shot_b['id']}]: {shot_b.get('prompt','')[:34]}…", font=f_xs, fill=(255, 135, 135, 230))

    return np.asarray(Image.alpha_composite(pil_im, ov).convert("RGB"), dtype=np.uint8)


def render_stelline_condensation_frame(rgb, disp, slope, poem_data, shot_data, u_condense, t=0.0):
    """
    Renders Mode IV: As `u_condense` moves from `0.0 -> 1.0`, the 3D HDL Architectural Wireframe,
    Amber LiDAR Point-Cloud, and TVE Glass Bezel condense smoothly into 100% unobstructed 16:9 Cinema!
    """
    pc = render_amber_pointcloud_scope(rgb, disp, slope, t=t, scan_streaks=True)
    w_cinema = np.clip(u_condense * 1.25 + (disp - 0.5) * 0.35 * math.sin(math.pi * u_condense), 0.0, 1.0)[..., None]
    blended = np.clip(pc * (1.0 - w_cinema) + rgb * w_cinema, 0.0, 1.0)
    u8 = (blended * 255.0).astype(np.uint8)

    hud_a = max(0.0, 1.0 - smootherstep(max(0.0, (u_condense - 0.25) / 0.65)))
    u8 = draw_tve_viewfinder_hud(
        u8,
        poem_data=poem_data,
        shot_data=shot_data,
        t=t,
        dr_vals=(85, 89, 96, 97),
        right_red=False,
        hud_alpha=hud_a,
        top_tag="MODE IV · STELLINE CONDENSATION: 3D HDL WIREFRAME & POINT-CLOUD -> UNOBSTRUCTED 16:9 CINEMA" if hud_a > 0.15 else None,
        show_3d_ghost=True,
    )
    return u8


def main():
    bundle = build_vesper_world_bundle()
    view_map = json.load(open(os.path.join(OUT_DIR, "bible_view_map.json")))

    rgb_92, disp_92, slope_92 = load_view_rgb_and_disp(92, view_map)  # P01 Underpass Shadow-Pool
    rgb_94, disp_94, slope_94 = load_view_rgb_and_disp(94, view_map)  # P10 Underpass Bathers (Echo)
    rgb_98, disp_98, slope_98 = load_view_rgb_and_disp(98, view_map)  # P13 Daimonji Amber Bridge
    rgb_80, disp_80, slope_80 = load_view_rgb_and_disp(80, view_map)  # P07 Naraka Red Shaft

    p01 = bundle["poems"][0]
    p10 = bundle["poems"][9]
    p13 = bundle["poems"][12]

    shot_92 = bundle["views_by_no"]["92"]
    shot_94 = bundle["views_by_no"]["94"]
    shot_98 = bundle["views_by_no"]["98"]

    # 1. Build the 4-Panel 2560x1440 Visual Proof Contact Sheet
    p1_pc = render_amber_pointcloud_scope(rgb_98, disp_98, slope_98, t=1.2, scan_streaks=False)
    panel_1 = draw_tve_viewfinder_hud(
        (p1_pc * 255.0).astype(np.uint8),
        poem_data=p13,
        shot_data=shot_98,
        t=1.2,
        dr_vals=(85, 89, 96, 97),
        right_red=False,
        hud_alpha=1.0,
        top_tag="MODE I · TVE 1/2–4/4 POINT-CLOUD SCOPE, 3D PIER/SHIP WIREFRAME & SHOT.JSON SOLVE (P13 · V98)",
        show_3d_ghost=True,
    )

    panel_2 = render_wireframe_canister_matrix_frame(rgb_80, disp_80, bundle, active_poem_idx=0, shot_vn=92, t=2.0)

    panel_3 = render_echo_split_comparator_frame(
        rgb_92, disp_92, slope_92, rgb_94, disp_94, slope_94, p01, shot_92, p10, shot_94, t=1.8
    )

    panel_4 = render_stelline_condensation_frame(
        rgb_92, disp_92, slope_92, p01, shot_92, u_condense=0.56, t=2.4
    )

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
    frames = []
    n_total = int(24.0 * FPS)
    for f_i in range(n_total):
        t = f_i / float(FPS)
        pan_x = 18.0 * math.sin(t * 0.65)
        pan_y = 6.0 * math.cos(t * 0.50)

        if t < 6.0:
            w_rgb = warp_multiplane_3d(rgb_80, disp_80, pan_x, pan_y, 1.08, 0.03)
            act_p_idx = [0, 2, 7, 11, 10, 12][int(t) % 6]
            frames.append(render_wireframe_canister_matrix_frame(w_rgb, disp_80, bundle, active_poem_idx=act_p_idx, shot_vn=92, t=t))
        elif t < 12.0:
            u_local = (t - 6.0) / 6.0
            w_rgb = warp_multiplane_3d(rgb_98, disp_98, pan_x, pan_y, 1.08 + 0.05 * u_local, 0.04 * u_local)
            pc = render_amber_pointcloud_scope(w_rgb, disp_98, slope_98, t=t, scan_streaks=True)
            frames.append(
                draw_tve_viewfinder_hud(
                    (pc * 255.0).astype(np.uint8),
                    poem_data=p13,
                    shot_data=shot_98,
                    t=t,
                    dr_vals=(85, 89, 96, 97),
                    right_red=False,
                    hud_alpha=1.0,
                    top_tag="MODE I · TVE 1/2–4/4 POINT-CLOUD SCOPE · 3D HDL PIER CAFÉ & 3-MASTED SHIP (P13 · V98)",
                    show_3d_ghost=True,
                )
            )
        elif t < 18.0:
            w_a = warp_multiplane_3d(rgb_92, disp_92, pan_x, pan_y, 1.10, 0.03)
            w_b = warp_multiplane_3d(rgb_94, disp_94, pan_x, pan_y, 1.10, 0.03)
            frames.append(
                render_echo_split_comparator_frame(
                    w_a, disp_92, slope_92, w_b, disp_94, slope_94, p01, shot_92, p10, shot_94, t=t
                )
            )
        else:
            u_cond = min(1.0, (t - 18.0) / 5.2)
            w_rgb = warp_multiplane_3d(rgb_92, disp_92, pan_x, pan_y, 1.08 + 0.06 * u_cond, 0.04 * u_cond)
            frames.append(render_stelline_condensation_frame(w_rgb, disp_92, slope_92, p01, shot_92, u_condense=u_cond, t=t))

    reel_mp4 = os.path.join(OUT_DIR, "wygwyl_vesper_apparatus_reel.mp4")
    encode_video_with_real_audio(frames, reel_mp4, 0.0)
    shutil.copy2(reel_mp4, os.path.join(VIDEOS_DIR, "wygwyl_vesper_apparatus_reel.mp4"))
    shutil.copy2(reel_mp4, os.path.join(ARTIFACT_DIR, "wygwyl_vesper_apparatus_reel.mp4"))
    print("Saved 24.0s Vesper Apparatus Reel:", reel_mp4, flush=True)


if __name__ == "__main__":
    main()
