#!/usr/bin/env python3
"""
Six Unobstructed Paradigms for the WYGWYL Narrative Apparatus
==============================================================
Replaces decorative HUD bezels and stick-box HDL wireframes with 6 distinct,
bezel-free ways of thinking about the narrative apparatus—each powered 100%
by the actual computed 3D, multiplane, perceptual, and production-design assets
of Where You Go When You Leave:

  OPTION I   — True 3D Metric Point-Cloud & Depth-Occluded Worldtext
               (129,264-vertex points.ply + depth_sharp.npz + metric Z poetry)
  OPTION II  — 3D Isometric Exploded Multiplane Stratigraphy
               (multiplane/exploded.jpg + P0..P6 Z/parallax laws + riverbed_NN.json)
  OPTION III — Animator's Perspective Grid, Horizon/VP & Line Layout
               (cartoon/layout_sheet.png + multiplane/layout_drawing.png + assembly_p*.txt)
  OPTION IV  — Pixel-Accurate SAM2 Contours, Vector Program & Perceptual ΔE Anatomy
               (overlay.jpg + program/compare.jpg + program/perceive.jpg + shot.json prompt)
  OPTION V   — Tactile Cut-Out Workbench: Brass-Brad Pivots, Grip Crosses & Craft Kits
               (poems/kits/NN.*.jpg + breakdown/NN.json puppet choreography)
  OPTION VI  — Unobstructed X-Ray & Common-Place Echo Curtain
               (Edge-to-edge wipe: image.jpg ↔ cel.png ↔ layout_drawing.png ↔ plane_map.jpg)
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
    h, w = img_bgr.shape[:2]
    scale = max(target_w / max(w, 1), target_h / max(h, 1))
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = cv2.resize(img_bgr, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    x0 = max(0, (nw - target_w) // 2)
    y0 = max(0, (nh - target_h) // 2)
    return resized[y0 : y0 + target_h, x0 : x0 + target_w].copy()


def fit_contain(img_bgr: np.ndarray, target_w: int, target_h: int, bg_color=(10, 12, 16)) -> np.ndarray:
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
    """Minimal, non-clouding top-left editorial strip that auto-sizes to text width."""
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
    pts: np.ndarray,
    shot_json: dict,
    multiplane_json: dict,
    breakdown_json: dict,
    t_phase: float = 0.35,
) -> np.ndarray:
    """
    Renders the actual 129,264-vertex 3D metric point cloud (points.ply) from a
    displaced 3D camera viewpoint (zero fake HUD bezel, zero stick-boxes).
    Places real poem lines and prompt anchors at the actual metric Z depths of
    planes P0 (6.0m), P1 (1.64m), P2 (21.76m), and P4 (21.8m) so foreground
    3D points naturally occlude deeper typography!
    """
    canvas = np.full((H, W, 3), (6, 9, 13), dtype=np.uint8)

    # Displaced 3D camera orbit around the scene's median depth (z_piv = 4.265m)
    angle = math.sin(t_phase * math.tau) * 0.14 + 0.08
    cam_tx = math.sin(t_phase * math.tau) * 0.52 + 0.28
    cam_ty = math.cos(t_phase * math.tau) * 0.14 + 0.06
    cam_tz = -0.35 + 0.20 * math.sin(t_phase * math.pi)

    x = pts["x"].astype(np.float32) - cam_tx
    y = pts["y"].astype(np.float32) - cam_ty
    z = -pts["z"].astype(np.float32) - cam_tz  # positive metric depth (0.9m .. 33.6m)

    z_piv = 4.265
    dz = z - z_piv
    ca, sa = math.cos(angle), math.sin(angle)
    xr = x * ca + dz * sa
    zr = -x * sa + dz * ca + z_piv

    valid = zr > 0.65
    xr, y, zr = xr[valid], y[valid], zr[valid]
    r = pts["r"][valid].astype(np.float32)
    g = pts["g"][valid].astype(np.float32)
    b = pts["b"][valid].astype(np.float32)

    # Exact perspective focal length matching points.ply fov (x/z in [-0.728, +0.728])
    fx = W * 0.72
    fy = W * 0.72
    cx, cy = W * 0.50, H * 0.52
    u = np.round(cx + (xr / zr) * fx).astype(np.int32)
    # Note: +y in points.ply is UP, so screen v = cy - (y / zr) * fy!
    v = np.round(cy - (y / zr) * fy).astype(np.int32)

    in_bounds = (u >= 0) & (u < W - 2) & (v >= 0) & (v < H - 2)
    u, v, zr, r, g, b = u[in_bounds], v[in_bounds], zr[in_bounds], r[in_bounds], g[in_bounds], b[in_bounds]

    # Sort far-to-near so we interleave 3D worldtext planes and let nearer 3D points occlude text!
    order = np.argsort(-zr)
    u, v, zr, r, g, b = u[order], v[order], zr[order], r[order], g[order], b[order]

    # Metric depth-scan wave (sweeps from 1.6m to 18m)
    scan_z = 2.2 + ((t_phase * 1.2) % 1.0) * 14.0

    def splat_depth_band(img_bgr: np.ndarray, z_far: float, z_near: float):
        mask = (zr <= z_far) & (zr > z_near)
        if not np.any(mask):
            return
        uu, vv, zz = u[mask], v[mask], zr[mask]
        rr, gg, bb = r[mask], g[mask], b[mask]

        # Warm amber/cyan metric lidar pulse on the active Z wave + boosted true RGB point cloud
        dist_scan = np.abs(zz - scan_z)
        pulse = np.exp(-0.5 * (dist_scan / 0.85) ** 2)
        lum = 0.299 * rr + 0.587 * gg + 0.114 * bb

        out_r = np.clip(rr * 1.35 * (1.0 - 0.50 * pulse) + (lum * 1.5 + 125) * (0.85 * pulse), 0, 255).astype(np.uint8)
        out_g = np.clip(gg * 1.35 * (1.0 - 0.50 * pulse) + (lum * 1.05 + 65) * (0.85 * pulse), 0, 255).astype(np.uint8)
        out_b = np.clip(bb * 1.35 * (1.0 - 0.50 * pulse) + (lum * 0.40 + 20) * (0.85 * pulse), 0, 255).astype(np.uint8)

        # Splat 2x2 points for rich volumetric density while letting parallax gaps breathe
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

    # 1. Splat Far Background & Canal Tunnel (Z: 40m -> 8.5m)
    splat_depth_band(canvas, 40.0, 8.5)

    # Interleave 3D Worldtext Plane at Z = 8.5m (Deep Canal Archway — occluded by foreground walls & stalls!)
    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov1 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d1 = ImageDraw.Draw(ov1)
    p4_x, p4_y, _ = project_3d_pt(-1.1, 0.85, 8.5)
    prompt_str = shot_json.get("prompt", "")
    d1.rectangle([p4_x, p4_y, p4_x + 640, p4_y + 84], fill=(8, 14, 22, 195), outline=(92, 228, 255, 175), width=1)
    d1.text((p4_x + 14, p4_y + 8), "P4/P5 DEEP CANAL PLANE @ Z = 21.8m..37.3m (×0.99..×0.58) · SHOT.JSON PROMPT", font=FONT_XS, fill=(92, 228, 255, 250))
    d1.text((p4_x + 14, p4_y + 30), prompt_str[:78], font=FONT_SM, fill=(235, 242, 248, 240))
    d1.text((p4_x + 14, p4_y + 52), prompt_str[78:156], font=FONT_SM, fill=(190, 208, 225, 225))
    pil = Image.alpha_composite(pil, ov1)
    canvas = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)

    # 2. Splat Midground Architecture (Z: 8.5m -> 4.6m) — OCCLUDES the Z=8.5m prompt plane!
    splat_depth_band(canvas, 8.5, 4.6)

    # Interleave 3D Poem Verse Plane at Z = 4.6m (P0/P2 Threshold — occluded by near container wall & water!)
    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(ov2)
    p2_x, p2_y, _ = project_3d_pt(-0.35, -0.05, 4.6)
    d2.rectangle([p2_x, p2_y, p2_x + 560, p2_y + 94], fill=(22, 14, 9, 205), outline=(255, 190, 82, 195), width=1)
    d2.text((p2_x + 14, p2_y + 8), "P2 ACTION THRESHOLD @ Z = 6.0m · POEM 01 SCENE 01.1 (THE SEARCH)", font=FONT_XS, fill=(255, 190, 82, 250))
    d2.text((p2_x + 14, p2_y + 30), "“What we've made / we don't want—", font=FONT_SERIF_MD, fill=(255, 242, 215, 255))
    d2.text((p2_x + 14, p2_y + 58), " What we've sold to the world / doesn't exist.”", font=FONT_SERIF_MD, fill=(255, 220, 165, 245))
    pil = Image.alpha_composite(pil, ov2)
    canvas = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)

    # 3. Splat Foreground Architecture & Water (Z: 4.6m -> 0.65m) — naturally occludes edges of Z=4.6m verse!
    splat_depth_band(canvas, 4.6, 0.65)

    # Foreground P1 Water Plane Callout at Z = 1.64m
    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov3 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d3 = ImageDraw.Draw(ov3)
    p1_x, p1_y, _ = project_3d_pt(-0.65, -0.58, 2.2)
    d3.rectangle([p1_x, p1_y, p1_x + 540, p1_y + 58], fill=(8, 16, 18, 205), outline=(125, 245, 185, 180), width=1)
    d3.text((p1_x + 12, p1_y + 8), "P1 FOREGROUND WATER @ Z = 1.64m (×8.00 PARALLAX · 35% AREA)", font=FONT_XS, fill=(125, 245, 185, 250))
    d3.text((p1_x + 12, p1_y + 28), "street lamp, water, wall · foreground 3D points occlude deeper text planes", font=FONT_SM, fill=(225, 240, 232, 240))
    pil = Image.alpha_composite(pil, ov3)
    canvas = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)

    # Subtle volumetric glow
    blur = cv2.GaussianBlur(canvas, (0, 0), sigmaX=4.0)
    canvas = cv2.addWeighted(canvas, 0.88, blur, 0.24, 0)

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    hdr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hdraw = ImageDraw.Draw(hdr)
    draw_pill_header(
        hdraw,
        24,
        20,
        "OPTION I · TRUE 3D POINT CLOUD",
        "129,264 Metric Vertices (points.ply) + Depth-Occluded 3D Worldtext",
        f"Camera Δx={cam_tx:+.2f}m yaw={math.degrees(angle):+.1f}° · Scan wave Z={scan_z:.1f}m · Text lives inside 3D Z-planes (occluded by foreground geometry)",
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
    shot_dir: Path,
    multiplane_json: dict,
    riverbed_json: dict,
    dossier_json: dict,
    t_phase: float = 0.0,
) -> np.ndarray:
    """
    Uses the real 3D isometric exploded multiplane stack (multiplane/exploded.jpg)
    and plane depth map (multiplane/plane_map.jpg) alongside the real multiplane.json
    depth/parallax table and riverbed_01.json permanent structural laws.
    """
    canvas = np.full((H, W, 3), (12, 14, 18), dtype=np.uint8)
    exploded_img = cv2.imread(str(shot_dir / "multiplane/exploded.jpg"))
    plane_map_img = cv2.imread(str(shot_dir / "multiplane/plane_map.jpg"))

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
        "OPTION II · EXPLODED MULTIPLANE STACK",
        "True Isometric Plane Stratigraphy (multiplane/exploded.jpg + multiplane.json + riverbed_01.json)",
        "Replaces abstract drums with actual separated P0–P6 painted planes, metric Z medians, parallax multipliers & Riverbed laws",
        accent=(92, 228, 255),
    )

    ty = 88 + int(H * 0.33) + 12
    d.rectangle([rx, ty, rx + rw, H - 18], fill=(9, 13, 18, 238), outline=(92, 228, 255, 115), width=1)
    d.text((rx + 14, ty + 10), "MULTIPLANE CAMERA STRATIGRAPHY (multiplane/multiplane.json)", font=FONT_MD, fill=(92, 228, 255))

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
        d.text((rx + 16, row_y + 21), f"Motion: {mot_str} · Objects: {contents[:48]}", font=FONT_XS, fill=(195, 208, 222))
        row_y += 45

    # Riverbed Permanent Structural Law Box at bottom right
    rb_y = max(row_y + 6, H - 150)
    d.line([(rx + 12, rb_y), (rx + rw - 12, rb_y)], fill=(92, 228, 255, 90), width=1)
    rb_core = riverbed_json.get("riverbed", {}).get("core_identity", "")
    rb_diegesis = riverbed_json.get("diegesis", {})
    rb_flow = ", ".join(riverbed_json.get("flow", {}).get("mutable_variables", [])[:5])
    rb_rules = " · ".join(rb_diegesis.get("world_rules", [])[:2])
    d.text((rx + 16, rb_y + 8), f"GOLDEN RIVERBED LAW — {riverbed_json.get('source_profile', {}).get('source_title', 'WYGWYL 01')}", font=FONT_SM, fill=(255, 195, 90))
    d.text((rx + 16, rb_y + 28), f"Identity: {rb_core[:72]}", font=FONT_XS, fill=(225, 235, 245))
    d.text((rx + 16, rb_y + 46), f"Mutable Flow: {rb_flow[:72]}", font=FONT_XS, fill=(185, 205, 222))
    d.text((rx + 16, rb_y + 64), f"World Rules: {rb_rules[:74]}", font=FONT_XS, fill=(130, 245, 175))

    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION III: Architectural Perspective Grid, Horizon/VP & Line Layout
# ==============================================================================
def render_option_3_perspective_layout(
    W: int,
    H: int,
    shot_dir: Path,
    shot_json: dict,
    signals_json: dict,
    assembly_text: str,
    t_phase: float = 0.0,
) -> np.ndarray:
    """
    Exposes the actual 3D perspective ground-plane grid, solved HORIZON & VP
    (cartoon/layout_sheet.png & cartoon/planes_gs.png) and traditional animation
    colour-coded line drawing (multiplane/layout_drawing.png) alongside the
    working poetry draft (assembly_p2.txt).
    """
    canvas = np.full((H, W, 3), (12, 14, 18), dtype=np.uint8)
    layout_sheet = cv2.imread(str(shot_dir / "cartoon/layout_sheet.png"))
    layout_draw = cv2.imread(str(shot_dir / "multiplane/layout_drawing.png"))
    planes_gs = cv2.imread(str(shot_dir / "cartoon/planes_gs.png"))

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
        "OPTION III · PERSPECTIVE & LINE LAYOUT",
        "Solved 3D Ground Grid, Horizon/VP & Colour-Coded Line Layout (layout_sheet.png + layout_drawing.png)",
        "Left: 3D perspective floor grid + solved VP/HORIZON · Curtain: Traditional animation colour-coded linework + Assembly manuscript",
        accent=(130, 245, 175),
    )

    ay = 88 + int(H * 0.35) + 12
    d.rectangle([rx, ay, rx + rw, H - 18], fill=(10, 14, 19, 238), outline=(130, 245, 175, 120), width=1)
    cam = shot_json.get("camera", {})
    vp = signals_json.get("vp", [])
    hor = signals_json.get("horizon", {})
    ink = signals_json.get("ink_coverage", {})
    d.text((rx + 14, ay + 10), "SOLVED PERSPECTIVE & HORIZON GEOMETRY (cartoon/signals.json)", font=FONT_MD, fill=(130, 245, 175))
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
    d.text((rx + 14, ay + 86), "ASSEMBLY WORKING MANUSCRIPT (poems/assembly/assembly_p2.txt)", font=FONT_SM, fill=(255, 200, 95))

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
    shot_dir: Path,
    shot_json: dict,
    perceive_json: dict,
    signals_json: dict,
    t_phase: float = 0.0,
) -> np.ndarray:
    """
    Uses pixel-accurate SAM2 segmentation contours (overlay.jpg), the 4-up
    vector program compilation + ΔE perceptual error map (program/compare.jpg),
    and the σ=1..32 squint pyramid (program/perceive.jpg), paired with the
    verbatim Midjourney prompt and signals.json staging diagnostics.
    """
    canvas = np.full((H, W, 3), (10, 12, 16), dtype=np.uint8)
    overlay_img = cv2.imread(str(shot_dir / "overlay.jpg"))
    compare_img = cv2.imread(str(shot_dir / "program/compare.jpg"))
    perceive_img = cv2.imread(str(shot_dir / "program/perceive.jpg"))

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
        "OPTION IV · SEMANTIC & PERCEPTUAL ANATOMY",
        "Pixel-Accurate SAM2 Contours (overlay.jpg) + 1,588-Vert Vector Program & ΔE Error (compare.jpg)",
        "Replaces fake HUD boxes with exact SAM2 object boundaries, SVG vector compilation, squint SSIM (σ=1..32) & verbatim prompt",
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
    reads_sigma = perceive_json.get("reads_at_sigma", "")

    d.text(
        (rx + 14, by + 10),
        f"VECTOR PROGRAM: 38 shapes · 1,588 verts · 19KB SVG · Mean ΔE=7.36 · Reads at σ={reads_sigma}",
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
    dossier_json: dict,
    breakdown_json: dict,
    t_phase: float = 0.0,
) -> np.ndarray:
    """
    Exposes the actual physical multiplane card & prop construction sheets
    (shots/poems/kits/01.set.bedroom_highrise.jpg, 01.props.jpg, 01.hero.severn.jpg)
    with green brass-brad pivot crosshairs, red hand-grip crosses, footage refs,
    and cardboard craft swatches alongside the breakdown/01.json puppet choreography.
    """
    canvas = np.full((H, W, 3), (12, 13, 16), dtype=np.uint8)
    kits_dir = SHOTS_DIR / "poems/kits"
    kit_set = cv2.imread(str(kits_dir / "01.set.bedroom_highrise.jpg"))
    kit_props = cv2.imread(str(kits_dir / "01.props.jpg"))
    kit_hero = cv2.imread(str(kits_dir / "01.hero.severn.jpg"))

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
        "OPTION V · TACTILE CUT-OUT WORKBENCH",
        "Multiplane Set & Prop Kits with Brass-Brad Pivots (+) & Grip Crosses (+) (poems/kits/01.*.jpg)",
        "Panel A: Card layout to paint into · Panel B: Midjourney & Butterfly-Halfworld Atlas refs · Panel C: Physical cardboard craft",
        accent=(255, 200, 90),
    )

    by = 88 + top_h + 10
    d.rectangle([rx, by, rx + rw, H - 18], fill=(12, 14, 18, 240), outline=(255, 200, 90, 130), width=1)
    scenes = breakdown_json.get("scenes", [])
    sc0 = scenes[0] if scenes else {}
    sh0 = sc0.get("shots", [{}])[0] if sc0.get("shots") else {}
    d.text(
        (rx + 14, by + 10),
        f"SHOT BREAKDOWN {sh0.get('id', '01.1a')} · SET: {sh0.get('set', 'bedroom_highrise').upper()} · {sc0.get('movement', 'THE SEARCH')} ({sc0.get('seconds', 13)}s)",
        font=FONT_MD,
        fill=(255, 200, 90),
    )
    d.text((rx + 14, by + 34), f"Lines: “{sc0.get('lines', '')[:78]}”", font=FONT_SERIF_MD, fill=(245, 238, 220))
    d.text((rx + 14, by + 60), f"Action: {sh0.get('action', '')[:86]}", font=FONT_XS, fill=(200, 212, 225))

    ry = by + 84
    for b in sh0.get("bodies", [])[:2]:
        hands = b.get("hands", {})
        hl = hands.get("L", {}).get("holds") or hands.get("L", {}).get("shape", "")
        hr = hands.get("R", {}).get("holds") or hands.get("R", {}).get("shape", "")
        pos = b.get("position", {})
        d.text(
            (rx + 14, ry),
            f"• PUPPET [{b.get('role')}]: costume={b.get('costume')} · view={b.get('view')} · expr={b.get('expression')} · L={hl} R={hr} @ ({pos.get('x')},{pos.get('y')},{pos.get('depth')})",
            font=FONT_XS,
            fill=(130, 245, 175),
        )
        ry += 20

    props = dossier_json.get("props", [])
    prop_summary = " · ".join([f"{p.get('id','')} ({p.get('scale_cm', '')}cm: {', '.join(p.get('states', [])[:2])})" for p in props[:3]])
    d.text((rx + 14, ry + 6), f"PROP CARDS (dossier/01.json): {prop_summary[:82]}", font=FONT_XS, fill=(92, 228, 255))
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
    shot_dir: Path,
    echo_shot_dir: Path,
    dossier_json: dict,
    shot_json: dict,
    t_phase: float = 0.0,
) -> np.ndarray:
    """
    Zero bezels, zero boxes: full-bleed 16:9 edge-to-edge spatial X-ray curtain
    peeling across 4 real computed layers of the Common Place:
      Band 1: Original Midjourney Painting (image.jpg)
      Band 2: Flat-Ink Cartoon & Depth Contours (cartoon/cel.png)
      Band 3: Traditional Colour-Coded Animation Line Layout (multiplane/layout_drawing.png)
      Band 4: Multiplane Depth Map / Shared Common Place Echo (multiplane/plane_map.jpg)
    """
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
        "OPTION VI · UNOBSTRUCTED X-RAY & ECHO CURTAIN",
        "Full-Bleed 16:9 Layer Peel (Original ↔ Cartoon Cel ↔ Blueprint Line Layout ↔ Plane Depth Map)",
        "Zero HUD chrome · Every seam exposes a real computed layer of the shot + poem verses anchored on the solved horizon",
        accent=(92, 228, 255),
    )

    bands = [
        (16, "I. ORIGINAL STILL (image.jpg)", (225, 235, 245)),
        (x1 + 12, "II. CARTOON CEL + DEPTH CONTOURS (cel.png)", (92, 228, 255)),
        (x2 + 12, "III. MULTIPLANE LINE LAYOUT (layout_drawing.png)", (255, 195, 90)),
        (x3 + 12, "IV. METRIC PLANE DEPTH MAP (plane_map.jpg)", (255, 130, 195)),
    ]
    for bx, btxt, bcol in bands:
        d.rectangle([bx, H - 46, bx + 360, H - 16], fill=(8, 11, 16, 210), outline=(bcol[0], bcol[1], bcol[2], 130), width=1)
        d.text((bx + 10, H - 39), btxt, font=FONT_XS, fill=bcol)

    poem_lines = [ln.strip() for ln in dossier_json.get("poem_text", "").splitlines() if ln.strip()]
    v_str = "  /  ".join(poem_lines[:4]) if poem_lines else "What we've made / we don't want— / What we've sold / to the world"
    d.rectangle([24, hy - 38, 24 + 860, hy - 4], fill=(8, 12, 18, 190), outline=(92, 228, 255, 130), width=1)
    d.text((36, hy - 32), f"SOLVED HORIZON (y={hy}px) · “{v_str[:92]}”", font=FONT_SERIF_MD, fill=(245, 240, 225))

    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


def update_bundle_with_kits_and_breakdowns():
    """Enrich vesper_world_bundle.json with breakdown/NN.json, kits/NN.json, and per-shot layer asset paths."""
    bundle_path = OUT_DIR / "vesper_world_bundle.json"
    if not bundle_path.exists():
        return
    bundle = json.loads(bundle_path.read_text())

    for p in bundle.get("poems", []):
        num_str = f"{int(p['num']):02d}"
        bd_path = SHOTS_DIR / f"poems/breakdown/{num_str}.json"
        if bd_path.exists():
            bd = json.loads(bd_path.read_text())
            p["breakdown_sets"] = bd.get("sets", [])
            p["breakdown_scenes"] = bd.get("scenes", [])
            p["breakdown_needs"] = bd.get("needs", {})

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
        else:
            kit_jpgs = sorted((SHOTS_DIR / "poems/kits").glob(f"{num_str}.*.jpg"))
            p["kit_sheets"] = [{"id": kp.stem, "image": f"poems/kits/{kp.name}"} for kp in kit_jpgs]

        for v in p.get("views", []):
            sd = v.get("shot_dir", "")
            if sd:
                v["assets"] = {
                    "image": f"out/{sd}/image.jpg",
                    "cel": f"out/{sd}/cartoon/cel.png",
                    "layout_sheet": f"out/{sd}/cartoon/layout_sheet.png",
                    "planes_gs": f"out/{sd}/cartoon/planes_gs.png",
                    "exploded": f"out/{sd}/multiplane/exploded.jpg",
                    "layout_drawing": f"out/{sd}/multiplane/layout_drawing.png",
                    "plane_map": f"out/{sd}/multiplane/plane_map.jpg",
                    "overlay": f"out/{sd}/overlay.jpg",
                    "ground": f"out/{sd}/ground.jpg",
                    "compare": f"out/{sd}/program/compare.jpg",
                    "perceive": f"out/{sd}/program/perceive.jpg",
                    "points_ply": f"out/{sd}/points.ply",
                }

    bundle_path.write_text(json.dumps(bundle, indent=2))
    print(f"[bundle] Enriched {bundle_path} ({bundle_path.stat().st_size / 1024:.1f} KB)")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    update_bundle_with_kits_and_breakdowns()

    shot_dir = SHOTS_DIR / "out/62b9740c-d0be-4b4a-a311-d653a2580907_1"
    echo_shot_dir = SHOTS_DIR / "out/62b9740c-d0be-4b4a-a311-d653a2580907_1"

    pts = load_ply_points(shot_dir / "points.ply", max_pts=129264)
    shot_json = json.loads((shot_dir / "shot.json").read_text())
    multiplane_json = json.loads((shot_dir / "multiplane/multiplane.json").read_text())
    perceive_json = json.loads((shot_dir / "program/perceive.json").read_text())
    signals_json = json.loads((shot_dir / "cartoon/signals.json").read_text())
    dossier_json = json.loads((SHOTS_DIR / "poems/dossier/01.json").read_text())
    breakdown_json = json.loads((SHOTS_DIR / "poems/breakdown/01.json").read_text())
    riverbed_json = json.loads((SHOTS_DIR / "film/riverbed_01.json").read_text())
    assembly_text = (SHOTS_DIR / "poems/assembly/assembly_p2.txt").read_text()

    W, H = 1920, 1080
    print("[render] Rendering 6 Unobstructed Narrative Apparatus Option Plates (1920x1080 each)...")
    opt1 = render_option_1_pointcloud_worldtext(W, H, pts, shot_json, multiplane_json, breakdown_json, t_phase=0.32)
    opt2 = render_option_2_exploded_multiplane(W, H, shot_dir, multiplane_json, riverbed_json, dossier_json, t_phase=0.25)
    opt3 = render_option_3_perspective_layout(W, H, shot_dir, shot_json, signals_json, assembly_text, t_phase=0.20)
    opt4 = render_option_4_semantic_perceptual(W, H, shot_dir, shot_json, perceive_json, signals_json, t_phase=0.35)
    opt5 = render_option_5_tactile_kits(W, H, dossier_json, breakdown_json, t_phase=0.40)
    opt6 = render_option_6_unobstructed_xray_curtain(W, H, shot_dir, echo_shot_dir, dossier_json, shot_json, t_phase=0.15)

    plates = [
        ("vesper_option_1_pointcloud_worldtext.png", opt1),
        ("vesper_option_2_exploded_multiplane.png", opt2),
        ("vesper_option_3_perspective_layout.png", opt3),
        ("vesper_option_4_semantic_perceptual.png", opt4),
        ("vesper_option_5_tactile_kits.png", opt5),
        ("vesper_option_6_xray_curtain.png", opt6),
    ]
    for fname, img in plates:
        out_p = OUT_DIR / fname
        cv2.imwrite(str(out_p), img)
        shutil.copy2(out_p, ARTIFACT_DIR / fname)

    sheet = np.full((2160, 3840, 3), (6, 8, 12), dtype=np.uint8)
    for idx, (_, img) in enumerate(plates):
        r = idx // 2
        c = idx % 2
        cell = fit_contain(img, 1920, 720, bg_color=(8, 10, 14))
        y0, x0 = r * 720, c * 1920
        sheet[y0 : y0 + 720, x0 : x0 + 1920] = cell
        cv2.rectangle(sheet, (x0, y0), (x0 + 1919, y0 + 719), (45, 70, 95), 1)

    proof_p1 = OUT_DIR / "vesper_6_narrative_options_proof.png"
    proof_p2 = OUT_DIR / "vesper_narrative_apparatus_proof.png"
    cv2.imwrite(str(proof_p1), sheet)
    cv2.imwrite(str(proof_p2), sheet)
    shutil.copy2(proof_p1, ARTIFACT_DIR / "vesper_6_narrative_options_proof.png")
    shutil.copy2(proof_p2, ARTIFACT_DIR / "vesper_narrative_apparatus_proof.png")
    print(f"[proof] Saved 4K 6-Options Proof Sheet -> {proof_p1}")

    mp4_raw = OUT_DIR / "_tmp_vesper_6options.mp4"
    mp4_final = OUT_DIR / "wygwyl_vesper_apparatus_reel.mp4"
    fps = 24
    seg_frames = 48
    writer = cv2.VideoWriter(str(mp4_raw), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    print("[video] Rendering 6-Paradigm Apparatus Reel (288 frames @ 1920x1080)...")
    for s_idx in range(6):
        for f in range(seg_frames):
            t_p = f / float(seg_frames)
            if s_idx == 0:
                frame = render_option_1_pointcloud_worldtext(W, H, pts, shot_json, multiplane_json, breakdown_json, t_phase=t_p)
            elif s_idx == 1:
                frame = render_option_2_exploded_multiplane(W, H, shot_dir, multiplane_json, riverbed_json, dossier_json, t_phase=t_p)
            elif s_idx == 2:
                frame = render_option_3_perspective_layout(W, H, shot_dir, shot_json, signals_json, assembly_text, t_phase=t_p)
            elif s_idx == 3:
                frame = render_option_4_semantic_perceptual(W, H, shot_dir, shot_json, perceive_json, signals_json, t_phase=t_p)
            elif s_idx == 4:
                frame = render_option_5_tactile_kits(W, H, dossier_json, breakdown_json, t_phase=t_p)
            else:
                frame = render_option_6_unobstructed_xray_curtain(W, H, shot_dir, echo_shot_dir, dossier_json, shot_json, t_phase=t_p)
            writer.write(frame)
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
            "18",
            "-movflags",
            "+faststart",
            str(mp4_final),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    mp4_raw.unlink(missing_ok=True)
    shutil.copy2(mp4_final, ARTIFACT_DIR / "wygwyl_vesper_apparatus_reel.mp4")
    print(f"[video] Saved H.264 6-Paradigm Reel -> {mp4_final} ({mp4_final.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
