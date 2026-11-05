#!/usr/bin/env python3
"""
All 14 Poems — Six Unobstructed Narrative Apparatus Paradigms
==============================================================
Generates the 6 unobstructed, real-asset Narrative Apparatus Options for
EVERY SINGLE POEM (01 through 14) in Where You Go When You Leave:

  1. Per-Poem Full-HD Option Plates (84 plates: poem_01_opt1.jpg .. poem_14_opt6.jpg)
  2. Per-Poem 4K 6-Option Contact Sheets (14 sheets: poem_01_apparatus_6options.png .. poem_14_apparatus_6options.png)
  3. Per-Poem H.264 6-Paradigm Films (14 MP4s: poem_01_apparatus.mp4 .. poem_14_apparatus.mp4)
  4. Master 14-Poem 4K Contact Sheets:
       - all_14_poems_pointcloud_worldtext_sheet.png (All 14 Poems in Option I: True 3D points.ply + Depth-Occluded Text)
       - all_14_poems_exploded_multiplane_sheet.png  (All 14 Poems in Option II: 3D Isometric Exploded Multiplane + Riverbed)
       - all_14_poems_apparatus_6options_sheet.png   (All 14 Poems Master Apparatus Matrix)
  5. Master All-14-Poems Feature Reel (wygwyl_all_14_poems_apparatus_reel.mp4 & wygwyl_vesper_apparatus_reel.mp4)
"""

import json
import math
import shutil
import subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch")
SHOTS_DIR = ROOT / "shots"
OUT_DIR = SHOTS_DIR / "data/terrarium/seeing_spacetime_films"
ARTIFACT_DIR = Path("/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584")

# 14 unique Hero Common Place views + 14 paired Echo views across the 14 poems
HERO_AND_ECHO_VIEWS = {
    1: ("V92", "V26"),
    2: ("V57", "V88"),
    3: ("V53", "V55"),
    4: ("V43", "V71"),
    5: ("V89", "V69"),
    6: ("V19", "V96"),
    7: ("V82", "V17"),
    8: ("V11", "V83"),
    9: ("V94", "V62"),
    10: ("V14", "V93"),
    11: ("V97", "V37"),
    12: ("V52", "V72"),
    13: ("V84", "V23"),
    14: ("V75", "V5"),
}


def load_font(size: int, mono: bool = True, bold: bool = False):
    candidates = (
        [
            "/System/Library/Fonts/SFNSMono.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/Monaco.ttf",
        ]
        if mono
        else [
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    )
    if bold and mono:
        candidates = ["/System/Library/Fonts/Menlo.ttc"] + candidates
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


FONT_XS = load_font(12, mono=True)
FONT_SM = load_font(14, mono=True)
FONT_MD = load_font(17, mono=True, bold=True)
FONT_LG = load_font(22, mono=True, bold=True)
FONT_XL = load_font(28, mono=True, bold=True)
FONT_SERIF_MD = load_font(20, mono=False)
FONT_SERIF_LG = load_font(26, mono=False)


def load_ply_points(ply_path: Path, max_pts: int = 129264):
    """Load binary_little_endian PLY (x, y, z, r, g, b)."""
    with open(ply_path, "rb") as f:
        while True:
            line = f.readline().decode("ascii", errors="ignore").strip()
            if line == "end_header":
                break
        dt = np.dtype([("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("r", "u1"), ("g", "u1"), ("b", "u1")])
        pts = np.fromfile(f, dtype=dt)
    if len(pts) > max_pts:
        step = max(1, len(pts) // max_pts)
        pts = pts[::step]
    return pts


def cover_crop(img_bgr: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    if img_bgr is None:
        return np.full((target_h, target_w, 3), (10, 12, 16), dtype=np.uint8)
    h, w = img_bgr.shape[:2]
    scale = max(target_w / max(w, 1), target_h / max(h, 1))
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = cv2.resize(img_bgr, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    x0 = max(0, (nw - target_w) // 2)
    y0 = max(0, (nh - target_h) // 2)
    return resized[y0 : y0 + target_h, x0 : x0 + target_w].copy()


def fit_contain(img_bgr: np.ndarray, target_w: int, target_h: int, bg_color=(10, 12, 16)) -> np.ndarray:
    if img_bgr is None:
        return np.full((target_h, target_w, 3), bg_color, dtype=np.uint8)
    h, w = img_bgr.shape[:2]
    scale = min(target_w / max(w, 1), target_h / max(h, 1))
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = cv2.resize(img_bgr, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    canvas = np.full((target_h, target_w, 3), bg_color, dtype=np.uint8)
    x0 = (target_w - nw) // 2
    y0 = (target_h - nh) // 2
    canvas[y0 : y0 + nh, x0 : x0 + nw] = resized
    return canvas


def draw_pill_header(draw: ImageDraw.ImageDraw, x: int, y: int, tag: str, title: str, subtitle: str, accent=(92, 228, 255)):
    top_str = f"{tag}  ·  {title}"
    w1 = len(top_str) * 10 + 44
    w2 = len(subtitle) * 8 + 44
    box_w = min(1860, max(780, w1, w2))
    draw.rectangle([x, y, x + box_w, y + 60], fill=(7, 10, 14, 218), outline=(accent[0], accent[1], accent[2], 130), width=1)
    draw.rectangle([x, y, x + 5, y + 60], fill=(accent[0], accent[1], accent[2], 255))
    draw.text((x + 16, y + 8), top_str, font=FONT_MD, fill=accent)
    draw.text((x + 16, y + 34), subtitle, font=FONT_SM, fill=(215, 226, 236))


# ==============================================================================
# OPTION I: True 3D Metric Point-Cloud & Depth-Occluded Worldtext (points.ply)
# ==============================================================================
def render_option_1_pointcloud_worldtext(
    W: int,
    H: int,
    poem_meta: dict,
    view_meta: dict,
    pts: np.ndarray,
    shot_json: dict,
    multiplane_json: dict,
    breakdown_json: dict,
    t_phase: float = 0.35,
) -> np.ndarray:
    canvas = np.full((H, W, 3), (6, 9, 13), dtype=np.uint8)
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    place_name = view_meta.get("place_name", "")
    vid = view_meta.get("id", "V92")

    raw_z = -pts["z"].astype(np.float32)
    z_med = float(np.clip(np.median(raw_z), 2.2, 14.0))
    z_p75 = float(np.clip(np.percentile(raw_z, 75), z_med + 1.5, 24.0))
    z_p25 = float(np.clip(np.percentile(raw_z, 25), 1.2, z_med - 0.5))

    angle = math.sin(t_phase * math.tau) * 0.13 + 0.07
    cam_tx = (math.sin(t_phase * math.tau) * 0.11 + 0.06) * z_med
    cam_ty = (math.cos(t_phase * math.tau) * 0.03 + 0.01) * z_med
    cam_tz = -0.07 * z_med + 0.04 * z_med * math.sin(t_phase * math.pi)

    x = pts["x"].astype(np.float32) - cam_tx
    y = pts["y"].astype(np.float32) - cam_ty
    z = raw_z - cam_tz

    z_piv = z_med
    dz = z - z_piv
    ca, sa = math.cos(angle), math.sin(angle)
    xr = x * ca + dz * sa
    zr = -x * sa + dz * ca + z_piv

    valid = zr > 0.55
    xr, y, zr = xr[valid], y[valid], zr[valid]
    r = pts["r"][valid].astype(np.float32)
    g = pts["g"][valid].astype(np.float32)
    b = pts["b"][valid].astype(np.float32)

    fx = W * 0.72
    fy = W * 0.72
    cx, cy = W * 0.50, H * 0.52
    u = np.round(cx + (xr / zr) * fx).astype(np.int32)
    v = np.round(cy - (y / zr) * fy).astype(np.int32)

    in_bounds = (u >= 0) & (u < W - 2) & (v >= 0) & (v < H - 2)
    u, v, zr, r, g, b = u[in_bounds], v[in_bounds], zr[in_bounds], r[in_bounds], g[in_bounds], b[in_bounds]

    order = np.argsort(-zr)
    u, v, zr, r, g, b = u[order], v[order], zr[order], r[order], g[order], b[order]

    scan_z = z_p25 + ((t_phase * 1.2) % 1.0) * max(2.0, z_p75 - z_p25)

    def splat_depth_band(img_bgr: np.ndarray, z_far: float, z_near: float):
        mask = (zr <= z_far) & (zr > z_near)
        if not np.any(mask):
            return
        uu, vv, zz = u[mask], v[mask], zr[mask]
        rr, gg, bb = r[mask], g[mask], b[mask]

        dist_scan = np.abs(zz - scan_z)
        pulse = np.exp(-0.5 * (dist_scan / max(0.6, 0.18 * z_med)) ** 2)
        lum = 0.299 * rr + 0.587 * gg + 0.114 * bb

        out_r = np.clip(rr * 1.35 * (1.0 - 0.50 * pulse) + (lum * 1.5 + 125) * (0.85 * pulse), 0, 255).astype(np.uint8)
        out_g = np.clip(gg * 1.35 * (1.0 - 0.50 * pulse) + (lum * 1.05 + 65) * (0.85 * pulse), 0, 255).astype(np.uint8)
        out_b = np.clip(bb * 1.35 * (1.0 - 0.50 * pulse) + (lum * 0.40 + 20) * (0.85 * pulse), 0, 255).astype(np.uint8)

        img_bgr[vv, uu, 0] = out_b
        img_bgr[vv, uu, 1] = out_g
        img_bgr[vv, uu, 2] = out_r
        img_bgr[vv, uu + 1, 0] = out_b
        img_bgr[vv, uu + 1, 1] = out_g
        img_bgr[vv, uu + 1, 2] = out_r
        img_bgr[vv + 1, uu, 0] = (out_b.astype(np.uint16) * 4 // 5).astype(np.uint8)
        img_bgr[vv + 1, uu, 1] = (out_g.astype(np.uint16) * 4 // 5).astype(np.uint8)
        img_bgr[vv + 1, uu, 2] = (out_r.astype(np.uint16) * 4 // 5).astype(np.uint8)

    def project_3d_pt(wx: float, wy: float, wz: float):
        dx = wx - cam_tx
        dy = wy - cam_ty
        dz_c = wz - cam_tz - z_piv
        xr_p = dx * ca + dz_c * sa
        zr_p = -dx * sa + dz_c * ca + z_piv
        if zr_p <= 0.5:
            zr_p = 0.5
        px = int(round(cx + (xr_p / zr_p) * fx))
        py = int(round(cy - (dy / zr_p) * fy))
        return px, py, zr_p

    # 1. Far Background (Z: 100m -> z_p75)
    splat_depth_band(canvas, 100.0, z_p75)

    # Interleave 3D Prompt Plane at z_p75
    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov1 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(ov1)
    p4_x, p4_y, _ = project_3d_pt(-0.12 * z_p75, 0.10 * z_p75, z_p75)
    p4_x = int(np.clip(p4_x, 40, W - 680))
    p4_y = int(np.clip(p4_y, 120, H - 280))
    prompt_str = shot_json.get("prompt", "")
    d1.rectangle([p4_x, p4_y, p4_x + 640, p4_y + 84], fill=(8, 14, 22, 195), outline=(92, 228, 255, 175), width=1)
    d1.text((p4_x + 14, p4_y + 8), f"P4/P5 DEEP ARCHITECTURE @ Z = {z_p75:.1f}m · {vid} ({place_name[:28]})", font=FONT_XS, fill=(92, 228, 255, 250))
    d1.text((p4_x + 14, p4_y + 30), prompt_str[:78], font=FONT_SM, fill=(235, 242, 248, 240))
    d1.text((p4_x + 14, p4_y + 52), prompt_str[78:156], font=FONT_SM, fill=(190, 208, 225, 225))
    pil = Image.alpha_composite(pil, ov1)
    canvas = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)

    # 2. Midground Architecture (Z: z_p75 -> z_med) — occludes the deep prompt plane!
    splat_depth_band(canvas, z_p75, z_med)

    # Interleave 3D Poem Verse Plane at z_med
    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(ov2)
    p2_x, p2_y, _ = project_3d_pt(-0.08 * z_med, -0.02 * z_med, z_med)
    p2_x = int(np.clip(p2_x, 60, W - 620))
    p2_y = int(np.clip(p2_y, 240, H - 180))

    scenes = breakdown_json.get("scenes", [])
    sc0 = scenes[0] if scenes else {}
    raw_lines = [s.strip() for s in sc0.get("lines", "").split("/") if s.strip()]
    if not raw_lines:
        ft = poem_meta.get("full_text", [])
        raw_lines = [
            (s.get("line", "") if isinstance(s, dict) else str(s)).strip()
            for s in (ft if isinstance(ft, list) else str(ft).splitlines())
        ]
        raw_lines = [s for s in raw_lines if s]
    line_a = " / ".join(raw_lines[:2]) if raw_lines else title_str
    line_b = " / ".join(raw_lines[2:4]) if len(raw_lines) > 2 else str(poem_meta.get("essence", ""))[:64]

    d2.rectangle([p2_x, p2_y, p2_x + 580, p2_y + 94], fill=(22, 14, 9, 205), outline=(255, 190, 82, 195), width=1)
    d2.text((p2_x + 14, p2_y + 8), f"P2 ACTION THRESHOLD @ Z = {z_med:.2f}m · POEM {num_str} ({title_str.upper()})", font=FONT_XS, fill=(255, 190, 82, 250))
    d2.text((p2_x + 14, p2_y + 30), f"“{line_a[:56]}", font=FONT_SERIF_MD, fill=(255, 242, 215, 255))
    d2.text((p2_x + 14, p2_y + 58), f" {line_b[:56]}”", font=FONT_SERIF_MD, fill=(255, 220, 165, 245))
    pil = Image.alpha_composite(pil, ov2)
    canvas = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)

    # 3. Foreground Architecture (Z: z_med -> 0.55m) — naturally occludes edges of z_med verse!
    splat_depth_band(canvas, z_med, 0.55)

    # Foreground P0/P1 Plane Callout
    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov3 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d3 = ImageDraw.Draw(ov3)
    planes = multiplane_json.get("planes", [])
    p_fg = planes[1] if len(planes) > 1 else (planes[0] if planes else {})
    fg_contents = ", ".join(p_fg.get("contents", [])[:4]) or "foreground architecture"
    d3.rectangle([28, H - 78, 610, H - 20], fill=(8, 16, 18, 208), outline=(125, 245, 185, 180), width=1)
    d3.text((40, H - 70), f"P0/P1 FOREGROUND OCCLUDER @ Z = {z_p25:.2f}m · {len(pts):,} METRIC VERTICES (points.ply)", font=FONT_XS, fill=(125, 245, 185, 250))
    d3.text((40, H - 50), f"Objects: {fg_contents[:58]} · occludes deeper 3D text planes", font=FONT_SM, fill=(225, 240, 232, 240))
    pil = Image.alpha_composite(pil, ov3)
    canvas = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)

    blur = cv2.GaussianBlur(canvas, (0, 0), sigmaX=4.0)
    canvas = cv2.addWeighted(canvas, 0.88, blur, 0.24, 0)

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    hdr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(hdr)
    draw_pill_header(
        hdraw,
        24,
        20,
        f"POEM {num_str} · {title_str.upper()} · OPTION I (3D POINT CLOUD)",
        f"{vid} {place_name} ({len(pts):,} Vertices in points.ply + Depth-Occluded Worldtext)",
        f"Camera Δx={cam_tx:+.2f}m yaw={math.degrees(angle):+.1f}° · Scan wave Z={scan_z:.1f}m · Text placed at metric Z planes ({z_med:.1f}m, {z_p75:.1f}m)",
        accent=(255, 190, 82),
    )
    pil = Image.alpha_composite(pil, hdr)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION II: 3D Isometric Exploded Multiplane Stratigraphy (multiplane/exploded.jpg)
# ==============================================================================
def render_option_2_exploded_multiplane(
    W: int,
    H: int,
    poem_meta: dict,
    view_meta: dict,
    shot_dir: Path,
    multiplane_json: dict,
    riverbed_json: dict,
    dossier_json: dict,
    t_phase: float = 0.0,
) -> np.ndarray:
    canvas = np.full((H, W, 3), (12, 14, 18), dtype=np.uint8)
    exploded_img = cv2.imread(str(shot_dir / "multiplane/exploded.jpg"))
    plane_map_img = cv2.imread(str(shot_dir / "multiplane/plane_map.jpg"))
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    vid = view_meta.get("id", "V92")
    place_name = view_meta.get("place_name", "")

    left_w = int(W * 0.60)
    if exploded_img is not None:
        fitted = fit_contain(exploded_img, left_w - 24, H - 104, bg_color=(16, 18, 22))
        canvas[88 : 88 + fitted.shape[0], 16 : 16 + fitted.shape[1]] = fitted

    rx = left_w + 8
    rw = W - rx - 20
    if plane_map_img is not None:
        pm_h = int(H * 0.33)
        pm_fit = fit_contain(plane_map_img, rw, pm_h, bg_color=(14, 17, 22))
        canvas[88 : 88 + pm_h, rx : rx + rw] = pm_fit

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    draw_pill_header(
        d,
        20,
        16,
        f"POEM {num_str} · {title_str.upper()} · OPTION II (EXPLODED MULTIPLANE)",
        f"{vid} {place_name} — Isometric Plane Stratigraphy (multiplane/exploded.jpg + riverbed_{num_str}.json)",
        "Separated P0–P6 painted planes with metric Z medians, parallax multipliers, loop cycles & Golden Riverbed laws",
        accent=(92, 228, 255),
    )

    ty = 88 + int(H * 0.33) + 12
    d.rectangle([rx, ty, rx + rw, H - 18], fill=(9, 13, 18, 238), outline=(92, 228, 255, 115), width=1)
    d.text((rx + 14, ty + 10), f"MULTIPLANE CAMERA STRATIGRAPHY ({vid} · multiplane.json)", font=FONT_MD, fill=(92, 228, 255))

    planes = [p for p in multiplane_json.get("planes", []) if p.get("area_frac", 0) > 0 or p.get("id") in ("P0", "P1", "P2", "P4", "P5", "P6")]
    plane_colors = {
        "P0": (140, 220, 255),
        "P1": (255, 185, 90),
        "P2": (255, 110, 110),
        "P4": (120, 240, 170),
        "P5": (180, 165, 255),
        "P6": (210, 220, 235),
    }
    row_y = ty + 38
    active_idx = int((t_phase * len(planes))) % max(1, len(planes))
    for idx, p in enumerate(planes[:6]):
        pid = p.get("id", f"P{idx}")
        name = p.get("name", "")
        z_m = p.get("z_median_m")
        z_str = f"{z_m:.2f}m" if isinstance(z_m, (int, float)) else "∞ (sky)"
        par = p.get("parallax") or 0.0
        area_pct = int(round((p.get("area_frac") or 0.0) * 100))
        motions = p.get("motion", [])
        mot_str = ", ".join(str(m) for m in motions[:2]) if motions else "static hold"
        contents = ", ".join(p.get("contents", [])[:4]) or "atmosphere"
        col = plane_colors.get(pid, (200, 220, 240))
        if idx == active_idx:
            d.rectangle([rx + 8, row_y - 2, rx + rw - 8, row_y + 42], fill=(col[0], col[1], col[2], 32), outline=(col[0], col[1], col[2], 165), width=1)
        d.text((rx + 16, row_y + 2), f"{pid} [{name.upper()}]  Z={z_str}  ×{par:.2f}  ({area_pct}% frame)", font=FONT_SM, fill=col)
        d.text((rx + 16, row_y + 21), f"Motion: {mot_str[:46]} · Objects: {contents[:38]}", font=FONT_XS, fill=(195, 208, 222))
        row_y += 45

    rb_y = max(row_y + 6, H - 150)
    d.line([(rx + 12, rb_y), (rx + rw - 12, rb_y)], fill=(92, 228, 255, 90), width=1)
    rb_core = riverbed_json.get("riverbed", {}).get("core_identity", "")
    rb_diegesis = riverbed_json.get("diegesis", {})
    rb_flow = ", ".join(riverbed_json.get("flow", {}).get("mutable_variables", [])[:5])
    rb_rules = " · ".join(rb_diegesis.get("world_rules", [])[:2])
    d.text((rx + 16, rb_y + 8), f"GOLDEN RIVERBED LAW — {riverbed_json.get('source_profile', {}).get('source_title', f'WYGWYL {num_str}')}", font=FONT_SM, fill=(255, 195, 90))
    d.text((rx + 16, rb_y + 28), f"Identity: {rb_core[:74]}", font=FONT_XS, fill=(225, 235, 245))
    d.text((rx + 16, rb_y + 46), f"Mutable Flow: {rb_flow[:74]}", font=FONT_XS, fill=(185, 205, 222))
    d.text((rx + 16, rb_y + 64), f"World Rules: {rb_rules[:76]}", font=FONT_XS, fill=(130, 245, 175))

    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION III: Architectural Perspective Grid, Horizon/VP & Line Layout
# ==============================================================================
def render_option_3_perspective_layout(
    W: int,
    H: int,
    poem_meta: dict,
    view_meta: dict,
    shot_dir: Path,
    shot_json: dict,
    signals_json: dict,
    assembly_text: str,
    assembly_page_num: int,
    t_phase: float = 0.0,
) -> np.ndarray:
    canvas = np.full((H, W, 3), (12, 14, 18), dtype=np.uint8)
    layout_sheet = cv2.imread(str(shot_dir / "cartoon/layout_sheet.png"))
    layout_draw = cv2.imread(str(shot_dir / "multiplane/layout_drawing.png"))
    planes_gs = cv2.imread(str(shot_dir / "cartoon/planes_gs.png"))
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    vid = view_meta.get("id", "V92")
    place_name = view_meta.get("place_name", "")

    left_w = int(W * 0.62)
    if layout_sheet is not None and layout_draw is not None:
        ls_fit = fit_contain(layout_sheet, left_w - 24, H - 104, bg_color=(16, 18, 22))
        ld_fit = fit_contain(layout_draw, left_w - 24, H - 104, bg_color=(245, 242, 235))
        split_x = int((0.58 + 0.25 * math.sin(t_phase * math.tau)) * ls_fit.shape[1])
        combined = ls_fit.copy()
        combined[:, split_x:] = ld_fit[:, split_x:]
        cv2.line(combined, (split_x, 0), (split_x, combined.shape[0]), (92, 228, 255), 2)
        canvas[88 : 88 + combined.shape[0], 16 : 16 + combined.shape[1]] = combined

    rx = left_w + 8
    rw = W - rx - 20
    if planes_gs is not None:
        pg_h = int(H * 0.35)
        pg_fit = fit_contain(planes_gs, rw, pg_h, bg_color=(14, 16, 20))
        canvas[88 : 88 + pg_h, rx : rx + rw] = pg_fit

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    draw_pill_header(
        d,
        20,
        16,
        f"POEM {num_str} · {title_str.upper()} · OPTION III (PERSPECTIVE & LINE LAYOUT)",
        f"{vid} {place_name} — Solved 3D Ground Grid, Horizon/VP & Colour-Coded Line Layout",
        f"Left: 3D perspective floor grid (layout_sheet.png) · Curtain: Traditional animation linework (layout_drawing.png) + assembly_p{assembly_page_num}.txt",
        accent=(130, 245, 175),
    )

    ay = 88 + int(H * 0.35) + 12
    d.rectangle([rx, ay, rx + rw, H - 18], fill=(10, 14, 19, 238), outline=(130, 245, 175, 120), width=1)
    cam = shot_json.get("camera", {})
    vp = signals_json.get("vp", [])
    ink = signals_json.get("ink_coverage", {})
    d.text((rx + 14, ay + 10), f"SOLVED PERSPECTIVE & HORIZON GEOMETRY ({vid} · cartoon/signals.json)", font=FONT_MD, fill=(130, 245, 175))
    d.text(
        (rx + 14, ay + 34),
        f"Horizon Y: {cam.get('horizon_y_norm', 0.50):.2f} · Tilt: {cam.get('tilt_deg', 0.0):.1f}° · VP: {str(vp)[:34]} · Ink: {str(ink)[:28]}",
        font=FONT_SM,
        fill=(225, 235, 245),
    )
    sugs = signals_json.get("suggestions", [])
    if sugs:
        d.text((rx + 14, ay + 54), f"Staging Note: {sugs[0][:74]}", font=FONT_XS, fill=(195, 212, 228))

    d.line([(rx + 12, ay + 78), (rx + rw - 12, ay + 78)], fill=(130, 245, 175, 80), width=1)
    d.text((rx + 14, ay + 86), f"ASSEMBLY WORKING MANUSCRIPT (poems/assembly/assembly_p{assembly_page_num}.txt)", font=FONT_SM, fill=(255, 200, 95))

    lines = [ln.strip() for ln in assembly_text.splitlines() if ln.strip()][:14]
    ly = ay + 110
    for ln in lines:
        col = (255, 185, 95) if ("[strikethrough" in ln or "Open on" in ln or "POET" in ln) else (225, 232, 240)
        d.text((rx + 14, ly), ln[:68], font=FONT_XS if len(ln) > 46 else FONT_SM, fill=col)
        ly += 21
        if ly > H - 34:
            break

    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION IV: Pixel-Accurate SAM2 Contours, Vector Program & ΔE Perceptual Anatomy
# ==============================================================================
def render_option_4_semantic_perceptual(
    W: int,
    H: int,
    poem_meta: dict,
    view_meta: dict,
    shot_dir: Path,
    shot_json: dict,
    perceive_json: dict,
    signals_json: dict,
    t_phase: float = 0.0,
) -> np.ndarray:
    canvas = np.full((H, W, 3), (10, 12, 16), dtype=np.uint8)
    overlay_img = cv2.imread(str(shot_dir / "overlay.jpg"))
    compare_img = cv2.imread(str(shot_dir / "program/compare.jpg"))
    perceive_img = cv2.imread(str(shot_dir / "program/perceive.jpg"))
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    vid = view_meta.get("id", "V92")
    place_name = view_meta.get("place_name", "")

    left_w = int(W * 0.54)
    top_h = int((H - 104) * 0.62)
    if overlay_img is not None:
        ov_fit = fit_contain(overlay_img, left_w - 20, top_h, bg_color=(12, 15, 20))
        canvas[88 : 88 + top_h, 16 : 16 + ov_fit.shape[1]] = ov_fit

    bot_h = (H - 104) - top_h - 10
    if perceive_img is not None:
        pr_fit = fit_contain(perceive_img, left_w - 20, bot_h, bg_color=(14, 16, 20))
        canvas[88 + top_h + 10 : 88 + top_h + 10 + bot_h, 16 : 16 + pr_fit.shape[1]] = pr_fit

    rx = left_w + 8
    rw = W - rx - 20
    comp_h = int((H - 104) * 0.54)
    if compare_img is not None:
        cp_fit = fit_contain(compare_img, rw, comp_h, bg_color=(14, 16, 20))
        canvas[88 : 88 + comp_h, rx : rx + rw] = cp_fit

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    draw_pill_header(
        d,
        20,
        16,
        f"POEM {num_str} · {title_str.upper()} · OPTION IV (SAM2 CONTOURS & ΔE PROGRAM)",
        f"{vid} {place_name} — Pixel-Accurate SAM2 Contours (overlay.jpg) + Vector Program & ΔE Error",
        "Exact SAM2 object boundaries, SVG vector compilation (compare.jpg), squint SSIM (σ=1..32) & verbatim Midjourney prompt",
        accent=(255, 130, 195),
    )

    by = 88 + comp_h + 10
    d.rectangle([rx, by, rx + rw, H - 18], fill=(10, 13, 18, 238), outline=(255, 130, 195, 120), width=1)
    sq = perceive_json.get("squint", {})
    if isinstance(sq, dict):
        ssim_str = " · ".join([f"{k}={v.get('ssim', 0):.3f}" if isinstance(v, dict) else f"{k}={v}" for k, v in list(sq.items())[:5]])
    elif isinstance(sq, list):
        ssim_str = " · ".join([f"σ{x.get('sigma', i)}={x.get('ssim', 0):.2f}" if isinstance(x, dict) else str(x) for i, x in enumerate(sq[:5])])
    else:
        ssim_str = ""
    reads_sigma = perceive_json.get("reads_at_sigma", 8)
    senses = perceive_json.get("senses", {})
    felt_str = senses.get("felt", view_meta.get("perceive", {}).get("felt", "")) if isinstance(senses, dict) else ""

    d.text(
        (rx + 14, by + 10),
        f"PERCEPTUAL COMPILER ({vid}): Reads at σ={reads_sigma} · Regions={signals_json.get('regions', 140)} · {felt_str[:48]}",
        font=FONT_SM,
        fill=(255, 130, 195),
    )
    if ssim_str:
        d.text((rx + 14, by + 32), f"SQUINT PYRAMID (program/perceive.json): {ssim_str[:76]}", font=FONT_XS, fill=(215, 228, 240))

    prompt = shot_json.get("prompt", "")
    d.text((rx + 14, by + 54), "VERBATIM MIDJOURNEY PROMPT (shot.json):", font=FONT_XS, fill=(92, 228, 255))
    for i, chunk in enumerate([prompt[j : j + 78] for j in range(0, min(len(prompt), 234), 78)]):
        d.text((rx + 14, by + 72 + i * 18), chunk, font=FONT_XS, fill=(235, 240, 245))

    sugs = signals_json.get("suggestions", [])
    ny = by + 132
    d.text((rx + 14, ny), "COMPUTED STAGING & VALUE DIAGNOSTICS (cartoon/signals.json):", font=FONT_XS, fill=(255, 195, 90))
    for s in sugs[:4]:
        d.text((rx + 14, ny + 18), f"• {s[:80]}", font=FONT_XS, fill=(205, 215, 228))
        ny += 18

    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION V: Tactile Physical Cut-Out Workbench (kits/*.jpg + breakdown/NN.json)
# ==============================================================================
def render_option_5_tactile_kits(
    W: int,
    H: int,
    poem_meta: dict,
    dossier_json: dict,
    breakdown_json: dict,
    t_phase: float = 0.0,
) -> np.ndarray:
    canvas = np.full((H, W, 3), (12, 13, 16), dtype=np.uint8)
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    kits_dir = SHOTS_DIR / "poems/kits"

    set_kits = sorted(kits_dir.glob(f"{num_str}.set.*.jpg"))
    prop_kits = sorted(kits_dir.glob(f"{num_str}.props*.jpg"))
    hero_kits = sorted(kits_dir.glob(f"{num_str}.hero.*.jpg")) + sorted(kits_dir.glob(f"{num_str}.fx*.jpg"))
    all_kits = sorted(kits_dir.glob(f"{num_str}.*.jpg"))

    kit_a_path = set_kits[0] if set_kits else (all_kits[0] if all_kits else None)
    kit_b_path = prop_kits[0] if prop_kits else (all_kits[1] if len(all_kits) > 1 else kit_a_path)
    kit_c_path = hero_kits[0] if hero_kits else (all_kits[2] if len(all_kits) > 2 else kit_b_path)

    kit_set = cv2.imread(str(kit_a_path)) if kit_a_path else None
    kit_props = cv2.imread(str(kit_b_path)) if kit_b_path else None
    kit_hero = cv2.imread(str(kit_c_path)) if kit_c_path else None

    left_w = int(W * 0.52)
    if kit_set is not None:
        ks_fit = fit_contain(kit_set, left_w - 20, H - 104, bg_color=(18, 19, 22))
        canvas[88 : 88 + ks_fit.shape[0], 16 : 16 + ks_fit.shape[1]] = ks_fit

    rx = left_w + 8
    rw = W - rx - 20
    top_h = int((H - 104) * 0.54)
    if kit_props is not None and kit_hero is not None:
        w_half = (rw - 8) // 2
        kp_fit = fit_contain(kit_props, w_half, top_h, bg_color=(18, 19, 22))
        kh_fit = fit_contain(kit_hero, w_half, top_h, bg_color=(18, 19, 22))
        canvas[88 : 88 + top_h, rx : rx + w_half] = kp_fit
        canvas[88 : 88 + top_h, rx + w_half + 8 : rx + w_half + 8 + w_half] = kh_fit

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    draw_pill_header(
        d,
        20,
        16,
        f"POEM {num_str} · {title_str.upper()} · OPTION V (TACTILE CUT-OUT WORKBENCH)",
        f"Multiplane Set & Prop Kits with Brass-Brad Pivots (+) & Grip Crosses (+) (poems/kits/{num_str}.*.jpg)",
        f"Showing: {kit_a_path.name if kit_a_path else ''} · {kit_b_path.name if kit_b_path else ''} · {kit_c_path.name if kit_c_path else ''}",
        accent=(255, 200, 90),
    )

    by = 88 + top_h + 10
    d.rectangle([rx, by, rx + rw, H - 18], fill=(12, 14, 18, 240), outline=(255, 200, 90, 130), width=1)
    scenes = breakdown_json.get("scenes", [])
    sc0 = scenes[0] if scenes else {}
    sh0 = sc0.get("shots", [{}])[0] if sc0.get("shots") else {}
    d.text(
        (rx + 14, by + 10),
        f"SHOT BREAKDOWN {sh0.get('id', f'{num_str}.1a')} · SET: {str(sh0.get('set', '')).upper()} · {sc0.get('movement', '')} ({sc0.get('seconds', 12)}s)",
        font=FONT_MD,
        fill=(255, 200, 90),
    )
    d.text((rx + 14, by + 34), f"Lines: “{sc0.get('lines', '')[:78]}”", font=FONT_SERIF_MD, fill=(245, 238, 220))
    d.text((rx + 14, by + 60), f"Action: {sh0.get('action', '')[:86]}", font=FONT_XS, fill=(200, 212, 225))

    ry = by + 84
    for b in sh0.get("bodies", [])[:2]:
        hands = b.get("hands", {}) if isinstance(b.get("hands"), dict) else {}
        hl = (hands.get("L", {}).get("holds") or hands.get("L", {}).get("shape", "")) if isinstance(hands.get("L"), dict) else ""
        hr = (hands.get("R", {}).get("holds") or hands.get("R", {}).get("shape", "")) if isinstance(hands.get("R"), dict) else ""
        pos = b.get("position", {}) if isinstance(b.get("position"), dict) else {}
        d.text(
            (rx + 14, ry),
            f"• PUPPET [{b.get('role')}]: costume={b.get('costume')} · view={b.get('view')} · expr={b.get('expression')} · L={hl} R={hr} @ ({pos.get('x')},{pos.get('depth')})",
            font=FONT_XS,
            fill=(130, 245, 175),
        )
        ry += 20

    props = dossier_json.get("props", [])
    prop_summary = " · ".join([f"{p.get('id','')} ({p.get('scale_cm', '')}cm: {', '.join(p.get('states', [])[:2])})" for p in props[:3]])
    d.text((rx + 14, ry + 6), f"PROP CARDS (dossier/{num_str}.json): {prop_summary[:82]}", font=FONT_XS, fill=(92, 228, 255))
    if props:
        d.text((rx + 14, ry + 24), f"HERO PROP BUILD ({props[0]['id']}): {props[0].get('build', '')[:84]}", font=FONT_XS, fill=(215, 225, 235))

    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION VI: Unobstructed Spatial X-Ray & Common-Place Echo Curtain
# ==============================================================================
def render_option_6_unobstructed_xray_curtain(
    W: int,
    H: int,
    poem_meta: dict,
    view_meta: dict,
    echo_view_meta: dict,
    shot_dir: Path,
    echo_shot_dir: Path,
    dossier_json: dict,
    shot_json: dict,
    t_phase: float = 0.0,
) -> np.ndarray:
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    vid = view_meta.get("id", "V92")
    evid = echo_view_meta.get("id", "V26")
    place_name = view_meta.get("place_name", "")
    echo_place = echo_view_meta.get("place_name", "")

    img_orig = cover_crop(cv2.imread(str(shot_dir / "image.jpg")), W, H)
    img_cel = cover_crop(cv2.imread(str(shot_dir / "cartoon/cel.png")), W, H)
    img_line = cover_crop(cv2.imread(str(shot_dir / "multiplane/layout_drawing.png")), W, H)
    echo_img_path = echo_shot_dir / "image.jpg"
    if not echo_img_path.exists():
        echo_img_path = shot_dir / "multiplane/plane_map.jpg"
    img_echo = cover_crop(cv2.imread(str(echo_img_path)), W, H)

    shift = math.sin(t_phase * math.tau) * 0.06
    x1 = int(W * (0.28 + shift))
    x2 = int(W * (0.54 + shift * 0.5))
    x3 = int(W * (0.77 - shift * 0.5))

    canvas = img_orig.copy()
    canvas[:, x1:x2] = img_cel[:, x1:x2]
    line_inv = 255 - img_line
    line_blueprint = np.zeros_like(line_inv)
    line_blueprint[:, :, 0] = np.clip(line_inv[:, :, 0].astype(np.int32) + 22, 0, 255).astype(np.uint8)
    line_blueprint[:, :, 1] = np.clip(line_inv[:, :, 1].astype(np.int32) + 16, 0, 255).astype(np.uint8)
    line_blueprint[:, :, 2] = np.clip(line_inv[:, :, 2].astype(np.int32) + 10, 0, 255).astype(np.uint8)
    canvas[:, x2:x3] = cv2.addWeighted(img_orig[:, x2:x3], 0.28, line_blueprint[:, x2:x3], 0.88, 0)
    canvas[:, x3:] = img_echo[:, x3:]

    for sx, col in [(x1, (92, 228, 255)), (x2, (255, 195, 90)), (x3, (255, 130, 195))]:
        cv2.line(canvas, (sx, 0), (sx, H), col, 2, cv2.LINE_AA)

    hy = int(shot_json.get("camera", {}).get("horizon_y_norm", 0.50) * H)
    cv2.line(canvas, (0, hy), (W, hy), (92, 228, 255), 1, cv2.LINE_AA)

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    draw_pill_header(
        d,
        24,
        20,
        f"POEM {num_str} · {title_str.upper()} · OPTION VI (X-RAY & ECHO CURTAIN)",
        f"{vid} ({place_name}) ↔ Cartoon Cel ↔ Blueprint Line Layout ↔ {evid} ({echo_place})",
        "Zero HUD chrome · Every seam exposes a real computed layer of the shot + poem verses anchored on the solved horizon",
        accent=(92, 228, 255),
    )

    bands = [
        (16, f"I. {vid} ORIGINAL STILL (image.jpg)", (225, 235, 245)),
        (x1 + 12, f"II. {vid} CARTOON CEL + DEPTH CONTOURS (cel.png)", (92, 228, 255)),
        (x2 + 12, f"III. {vid} MULTIPLANE LINE LAYOUT (layout_drawing.png)", (255, 195, 90)),
        (x3 + 12, f"IV. PAIRED ECHO VIEW: {evid} ({echo_place[:22]})", (255, 130, 195)),
    ]
    for bx, btxt, bcol in bands:
        d.rectangle([bx, H - 46, bx + 380, H - 16], fill=(8, 11, 16, 210), outline=(bcol[0], bcol[1], bcol[2], 130), width=1)
        d.text((bx + 10, H - 39), btxt[:46], font=FONT_XS, fill=bcol)

    ft = poem_meta.get("full_text", [])
    poem_lines = [
        (ln.get("line", "") if isinstance(ln, dict) else str(ln)).strip()
        for ln in (ft if isinstance(ft, list) else str(ft).splitlines())
    ]
    poem_lines = [ln for ln in poem_lines if ln]
    v_str = "  /  ".join(poem_lines[:4]) if poem_lines else title_str
    d.rectangle([24, hy - 38, 24 + 920, hy - 4], fill=(8, 12, 18, 190), outline=(92, 228, 255, 130), width=1)
    d.text((36, hy - 32), f"SOLVED HORIZON (y={hy}px) · “{v_str[:96]}”", font=FONT_SERIF_MD, fill=(245, 240, 225))

    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


def build_14_poem_master_sheet(items: list, out_path: Path, title_banner: str):
    """Build a 3840x2160 14-cell master contact sheet (4 cols x 4 rows, with 2-col header banner)."""
    sheet = np.full((2160, 3840, 3), (6, 8, 12), dtype=np.uint8)
    cw, ch = 960, 540
    # 14 poems placed in cells 0..13 of the 16-cell 4x4 grid, cells 14..15 hold summary legend
    for idx, (num_str, title_str, img) in enumerate(items[:14]):
        r = idx // 4
        c = idx % 4
        cell = fit_contain(img, cw, ch, bg_color=(8, 10, 14))
        y0, x0 = r * ch, c * cw
        sheet[y0 : y0 + ch, x0 : x0 + cw] = cell
        cv2.rectangle(sheet, (x0, y0), (x0 + cw - 1, y0 + ch - 1), (45, 75, 105), 1)

    # Bottom-right 2 cells (row 3, cols 2..3 -> x=1920..3840, y=1620..2160): Title & Legend Card
    pil = Image.fromarray(cv2.cvtColor(sheet, cv2.COLOR_BGR2RGB)).convert("RGBA")
    d = ImageDraw.Draw(pil)
    x0, y0 = 1920, 1620
    d.rectangle([x0 + 12, y0 + 12, 3840 - 12, 2160 - 12], fill=(10, 14, 20, 245), outline=(92, 228, 255, 180), width=2)
    d.text((x0 + 40, y0 + 38), "WHERE YOU GO WHEN YOU LEAVE — ALL 14 POEMS", font=FONT_XL, fill=(92, 228, 255))
    d.text((x0 + 40, y0 + 82), title_banner, font=FONT_LG, fill=(255, 195, 90))
    d.text(
        (x0 + 40, y0 + 128),
        "Every poem is driven 100% by its real computed 3D point cloud (points.ply), exploded multiplane stack (exploded.jpg),",
        font=FONT_MD,
        fill=(220, 232, 242),
    )
    d.text(
        (x0 + 40, y0 + 156),
        "solved 3D ground grid & horizon (layout_sheet.png), SAM2/SVG perceptual compiler (overlay.jpg / compare.jpg),",
        font=FONT_MD,
        fill=(220, 232, 242),
    )
    d.text(
        (x0 + 40, y0 + 184),
        "physical multiplane cardboard craft kits (poems/kits/NN.*.jpg), and Golden Riverbed structural laws (riverbed_NN.json).",
        font=FONT_MD,
        fill=(220, 232, 242),
    )

    # List the 14 poems and their Hero → Echo Common Place pairings
    py = y0 + 232
    for col_idx in range(2):
        subset = items[col_idx * 7 : (col_idx + 1) * 7]
        px = x0 + 40 + col_idx * 920
        for i, (ns, ts, _) in enumerate(subset):
            p_num = int(ns)
            hid, eid = HERO_AND_ECHO_VIEWS[p_num]
            d.text((px, py + i * 36), f"• POEM {ns} ({ts[:24]:24s}) — Hero {hid:4s} ↔ Echo {eid:4s}", font=FONT_MD, fill=(130, 245, 175))

    out_bgr = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(out_path), out_bgr)
    shutil.copy2(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[master-sheet] Saved {out_path.name}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bundle_path = OUT_DIR / "vesper_world_bundle.json"
    bundle = json.loads(bundle_path.read_text())

    opt1_all = []
    opt2_all = []
    opt3_all = []
    opt4_all = []
    opt5_all = []
    opt6_all = []
    per_poem_mp4s = []

    W, H = 1920, 1080
    fps = 24
    frames_per_opt = 12  # 6 options * 12f = 72 frames (3.0s per poem, 42s across all 14 poems)

    for p in bundle["poems"]:
        num = int(p["num"])
        num_str = f"{num:02d}"
        title_str = p.get("title", "")
        hid, eid = HERO_AND_ECHO_VIEWS[num]
        vmap = {v["id"]: v for v in p.get("views", [])}
        hv = vmap.get(hid, p["views"][0])
        ev = vmap.get(eid, p["views"][-1])

        # Ensure every view in bundle has both dir and shot_dir + assets populated
        for v in p.get("views", []):
            sd_str = v.get("dir") or v.get("shot_dir", "")
            v["shot_dir"] = sd_str
            v["place"] = v.get("place_name", "")
            v["view_id"] = v.get("id", "")
            v["signals_notes"] = v.get("signals", {}).get("suggestions", [])
            v["assets"] = {
                "image": f"out/{sd_str}/image.jpg",
                "cel": f"out/{sd_str}/cartoon/cel.png",
                "layout_sheet": f"out/{sd_str}/cartoon/layout_sheet.png",
                "planes_gs": f"out/{sd_str}/cartoon/planes_gs.png",
                "exploded": f"out/{sd_str}/multiplane/exploded.jpg",
                "layout_drawing": f"out/{sd_str}/multiplane/layout_drawing.png",
                "plane_map": f"out/{sd_str}/multiplane/plane_map.jpg",
                "overlay": f"out/{sd_str}/overlay.jpg",
                "ground": f"out/{sd_str}/ground.jpg",
                "compare": f"out/{sd_str}/program/compare.jpg",
                "perceive": f"out/{sd_str}/program/perceive.jpg",
                "points_ply": f"out/{sd_str}/points.ply",
            }

        ft_val = p.get("full_text", [])
        if isinstance(ft_val, list):
            p["poem_text"] = "\n".join(
                (x.get("line", "") if isinstance(x, dict) else str(x)).strip()
                for x in ft_val
                if (x.get("line", "") if isinstance(x, dict) else str(x)).strip()
            )
        else:
            p["poem_text"] = str(ft_val)
        bd_path = SHOTS_DIR / f"poems/breakdown/{num_str}.json"
        breakdown_json = json.loads(bd_path.read_text()) if bd_path.exists() else {}
        p["breakdown_sets"] = breakdown_json.get("sets", [])
        p["breakdown_scenes"] = breakdown_json.get("scenes", [])
        p["breakdown_needs"] = breakdown_json.get("needs", {})

        kit_json_path = SHOTS_DIR / f"poems/kits/{num_str}.json"
        if kit_json_path.exists():
            kj = json.loads(kit_json_path.read_text())
            kits_list = kj if isinstance(kj, list) else kj.get("kits", [])
            p["kit_sheets"] = [
                {
                    "kind": k.get("kind", ""),
                    "id": k.get("id", ""),
                    "title": k.get("title", ""),
                    "image": f"poems/kits/{Path(k.get('image', '')).name}" if k.get("image") else "",
                    "prompt": k.get("prompt", "")[:320],
                }
                for k in kits_list
            ]

        shot_dir = SHOTS_DIR / "out" / hv["dir"]
        echo_shot_dir = SHOTS_DIR / "out" / ev["dir"]

        pts = load_ply_points(shot_dir / "points.ply", max_pts=110000)
        shot_json = json.loads((shot_dir / "shot.json").read_text())
        multiplane_json = json.loads((shot_dir / "multiplane/multiplane.json").read_text())
        perceive_json = json.loads((shot_dir / "program/perceive.json").read_text())
        signals_json = json.loads((shot_dir / "cartoon/signals.json").read_text())
        dossier_json = json.loads((SHOTS_DIR / f"poems/dossier/{num_str}.json").read_text())
        riverbed_json = json.loads((SHOTS_DIR / f"film/riverbed_{num_str}.json").read_text())

        apages = p.get("assembly_pages", [])
        if apages and isinstance(apages[0], dict):
            apage_num = apages[0].get("file", "assembly_p1.txt").replace("assembly_p", "").replace(".txt", "")
            assembly_text = apages[0].get("text", "") or p.get("full_text", "")
        else:
            apage_num = apages[0] if apages else 1
            apage_path = SHOTS_DIR / f"poems/assembly/assembly_p{apage_num}.txt"
            assembly_text = apage_path.read_text() if apage_path.exists() else p.get("full_text", "")
        p["assembly_excerpt"] = assembly_text[:1200]

        print(f"[poem {num_str}] Rendering 6 Apparatus Options for Poem {num_str} ({title_str}) — Hero {hid} / Echo {eid}...")
        opt1 = render_option_1_pointcloud_worldtext(W, H, p, hv, pts, shot_json, multiplane_json, breakdown_json, t_phase=0.32)
        opt2 = render_option_2_exploded_multiplane(W, H, p, hv, shot_dir, multiplane_json, riverbed_json, dossier_json, t_phase=0.25)
        opt3 = render_option_3_perspective_layout(W, H, p, hv, shot_dir, shot_json, signals_json, assembly_text, apage_num, t_phase=0.20)
        opt4 = render_option_4_semantic_perceptual(W, H, p, hv, shot_dir, shot_json, perceive_json, signals_json, t_phase=0.35)
        opt5 = render_option_5_tactile_kits(W, H, p, dossier_json, breakdown_json, t_phase=0.40)
        opt6 = render_option_6_unobstructed_xray_curtain(W, H, p, hv, ev, shot_dir, echo_shot_dir, dossier_json, shot_json, t_phase=0.15)

        opt_imgs = [opt1, opt2, opt3, opt4, opt5, opt6]
        opt_paths = {}
        for o_idx, o_img in enumerate(opt_imgs, start=1):
            o_name = f"poem_{num_str}_opt{o_idx}.jpg"
            cv2.imwrite(str(OUT_DIR / o_name), o_img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
            opt_paths[f"opt{o_idx}"] = f"data/terrarium/seeing_spacetime_films/{o_name}"

        opt1_all.append((num_str, title_str, opt1))
        opt2_all.append((num_str, title_str, opt2))
        opt3_all.append((num_str, title_str, opt3))
        opt4_all.append((num_str, title_str, opt4))
        opt5_all.append((num_str, title_str, opt5))
        opt6_all.append((num_str, title_str, opt6))

        # Per-Poem 4K 6-Options Contact Sheet (3840x2160)
        sheet = np.full((2160, 3840, 3), (6, 8, 12), dtype=np.uint8)
        for idx, o_img in enumerate(opt_imgs):
            r = idx // 2
            c = idx % 2
            cell = fit_contain(o_img, 1920, 720, bg_color=(8, 10, 14))
            y0, x0 = r * 720, c * 1920
            sheet[y0 : y0 + 720, x0 : x0 + 1920] = cell
            cv2.rectangle(sheet, (x0, y0), (x0 + 1919, y0 + 719), (45, 70, 95), 1)

        sheet_name = f"poem_{num_str}_apparatus_6options.png"
        cv2.imwrite(str(OUT_DIR / sheet_name), sheet)
        shutil.copy2(OUT_DIR / sheet_name, ARTIFACT_DIR / sheet_name)
        opt_paths["sheet"] = f"data/terrarium/seeing_spacetime_films/{sheet_name}"

        # Per-Poem 6-Paradigm H.264 Film (poem_NN_apparatus.mp4)
        mp4_raw = OUT_DIR / f"_tmp_poem_{num_str}_apparatus.mp4"
        mp4_final = OUT_DIR / f"poem_{num_str}_apparatus.mp4"
        writer = cv2.VideoWriter(str(mp4_raw), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
        for s_idx in range(6):
            for f in range(frames_per_opt):
                t_p = f / float(frames_per_opt)
                if s_idx == 0:
                    frm = render_option_1_pointcloud_worldtext(W, H, p, hv, pts, shot_json, multiplane_json, breakdown_json, t_phase=t_p)
                elif s_idx == 1:
                    frm = render_option_2_exploded_multiplane(W, H, p, hv, shot_dir, multiplane_json, riverbed_json, dossier_json, t_phase=t_p)
                elif s_idx == 2:
                    frm = render_option_3_perspective_layout(W, H, p, hv, shot_dir, shot_json, signals_json, assembly_text, apage_num, t_phase=t_p)
                elif s_idx == 3:
                    frm = render_option_4_semantic_perceptual(W, H, p, hv, shot_dir, shot_json, perceive_json, signals_json, t_phase=t_p)
                elif s_idx == 4:
                    frm = render_option_5_tactile_kits(W, H, p, dossier_json, breakdown_json, t_phase=t_p)
                else:
                    frm = render_option_6_unobstructed_xray_curtain(W, H, p, hv, ev, shot_dir, echo_shot_dir, dossier_json, shot_json, t_phase=t_p)
                writer.write(frm)
        writer.release()
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(mp4_raw),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "23",
                "-movflags",
                "+faststart",
                str(mp4_final),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        mp4_raw.unlink(missing_ok=True)
        per_poem_mp4s.append(mp4_final)
        opt_paths["video"] = f"data/terrarium/seeing_spacetime_films/poem_{num_str}_apparatus.mp4"
        p["apparatus"] = opt_paths
        p["hero_view_id"] = hid
        p["echo_view_id"] = eid

    # Save enriched bundle with all 14 poems' apparatus paths and fixed view assets
    bundle_path.write_text(json.dumps(bundle, indent=2))
    print(f"[bundle] Saved enriched 14-poem bundle -> {bundle_path}")

    # Build Master 14-Poem 4K Sheets
    build_14_poem_master_sheet(
        opt1_all,
        OUT_DIR / "all_14_poems_pointcloud_worldtext_sheet.png",
        "OPTION I ACROSS ALL 14 POEMS — True 3D Metric Point Clouds (points.ply) + Depth-Occluded 3D Worldtext",
    )
    build_14_poem_master_sheet(
        opt2_all,
        OUT_DIR / "all_14_poems_exploded_multiplane_sheet.png",
        "OPTION II ACROSS ALL 14 POEMS — Isometric 3D Exploded Multiplane Stacks (exploded.jpg) + Golden Riverbed Laws",
    )
    build_14_poem_master_sheet(
        opt3_all,
        OUT_DIR / "all_14_poems_perspective_layout_sheet.png",
        "OPTION III ACROSS ALL 14 POEMS — Solved 3D Perspective Grids, Horizon/VP & Animation Line Layouts",
    )
    build_14_poem_master_sheet(
        opt4_all,
        OUT_DIR / "all_14_poems_semantic_perceptual_sheet.png",
        "OPTION IV ACROSS ALL 14 POEMS — Pixel-Accurate SAM2 Contours, Vector Programs & Perceptual ΔE Maps",
    )
    build_14_poem_master_sheet(
        opt5_all,
        OUT_DIR / "all_14_poems_tactile_kits_sheet.png",
        "OPTION V ACROSS ALL 14 POEMS — Tactile Cut-Out Multiplane Set & Prop Kits with Brass-Brad Pivots",
    )
    build_14_poem_master_sheet(
        opt6_all,
        OUT_DIR / "all_14_poems_xray_echo_sheet.png",
        "OPTION VI ACROSS ALL 14 POEMS — Unobstructed 4-Layer X-Ray & Shared Common-Place Echo Curtains",
    )

    # Concatenate all 14 per-poem apparatus MP4s into the master anthology reel
    concat_txt = OUT_DIR / "_concat_14_apparatus.txt"
    concat_txt.write_text("\n".join([f"file '{p.name}'" for p in per_poem_mp4s]) + "\n")
    master_mp4 = OUT_DIR / "wygwyl_all_14_poems_apparatus_reel.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(master_mp4),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    concat_txt.unlink(missing_ok=True)
    shutil.copy2(master_mp4, OUT_DIR / "wygwyl_vesper_apparatus_reel.mp4")
    shutil.copy2(master_mp4, ARTIFACT_DIR / "wygwyl_all_14_poems_apparatus_reel.mp4")
    shutil.copy2(master_mp4, ARTIFACT_DIR / "wygwyl_vesper_apparatus_reel.mp4")
    print(f"[master-reel] Saved 14-Poem Master Apparatus Reel -> {master_mp4} ({master_mp4.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
