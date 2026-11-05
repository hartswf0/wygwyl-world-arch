#!/usr/bin/env python3
"""
VOIDBASTARD-TAO — All 14 Poems × 6 Unobstructed Diegetic Cinema Apparatus Paradigms
====================================================================================
"I will first construct the way of the surface, then remove obstruction until the
operation can proceed without force. Leave the center open."

Generates 100% full-bleed (1920x1080) cinema-grade plates with ZERO rectangular HUD
boxes, ZERO split-screen text sidebars, and ZERO decorative chrome across all 14 poems:

  Option I   : Full-Bleed 3D Metric Point Cloud (points.ply) + Depth-Occluded Worldtext
  Option II  : Full-Bleed 3D Isometric Exploded Multiplane (exploded.jpg) + Optical Plane Hairlines
  Option III : Full-Bleed Surveyor's Perspective Grid & Darkroom Line Layout Wipe + Horizon Manuscript
  Option IV  : Full-Bleed Machine-Eye Optical Aperture Lens (Photographic Still ↔ SAM2 Contours & Vector ΔE)
  Option V   : Full-Bleed Darkroom Animator's Light-Table Cut-Out Kit (poems/kits/NN.*.jpg) + Registration Marks
  Option VI  : Full-Bleed 4-Layer Optical Slit-Scan & Shared Common-Place Echo Curtain + Horizon Verse
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


def load_font(size: int, mono: bool = True, italic: bool = False):
    candidates = (
        [
            "/System/Library/Fonts/SFNSMono.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/Monaco.ttf",
        ]
        if mono
        else [
            "/System/Library/Fonts/Supplemental/Georgia Italic.ttf" if italic else "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
        ]
    )
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


FONT_MICRO = load_font(11, mono=True)
FONT_XS = load_font(13, mono=True)
FONT_SM = load_font(15, mono=True)
FONT_MD = load_font(18, mono=True)
FONT_LG = load_font(22, mono=True)
FONT_XL = load_font(28, mono=True)
FONT_SERIF_SM = load_font(19, mono=False, italic=True)
FONT_SERIF_MD = load_font(24, mono=False, italic=True)
FONT_SERIF_LG = load_font(34, mono=False, italic=True)
FONT_SERIF_XL = load_font(44, mono=False, italic=True)


def load_ply_points(ply_path: Path, max_pts: int = 129264):
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
        return np.full((target_h, target_w, 3), (6, 8, 11), dtype=np.uint8)
    h, w = img_bgr.shape[:2]
    scale = max(target_w / max(w, 1), target_h / max(h, 1))
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = cv2.resize(img_bgr, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    x0 = max(0, (nw - target_w) // 2)
    y0 = max(0, (nh - target_h) // 2)
    return resized[y0 : y0 + target_h, x0 : x0 + target_w].copy()


def fit_contain(img_bgr: np.ndarray, target_w: int, target_h: int, bg_color=(6, 8, 11)) -> np.ndarray:
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


def extract_clean_lines(poem_meta: dict, breakdown_json: dict) -> list[str]:
    scenes = breakdown_json.get("scenes", [])
    sc0 = scenes[0] if scenes else {}
    raw = [s.strip() for s in sc0.get("lines", "").split("/") if s.strip()]
    if not raw:
        ft = poem_meta.get("full_text", [])
        raw = [
            (s.get("line", "") if isinstance(s, dict) else str(s)).strip()
            for s in (ft if isinstance(ft, list) else str(ft).splitlines())
        ]
        raw = [s for s in raw if s]
    return raw if raw else [poem_meta.get("title", "")]


def draw_shadow_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill=(240, 244, 248, 235), shadow=(0, 0, 0, 210)):
    """Draws unboxed optical viewfinder text with a crisp 1px dark halo — zero background rectangles."""
    x, y = xy
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 2)]:
        draw.text((x + dx, y + dy), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def draw_viewfinder_whisper(
    draw: ImageDraw.ImageDraw,
    W: int,
    H: int,
    left_mark: str,
    right_mark: str,
    bottom_left_mark: str = "",
    bottom_right_mark: str = "",
    accent=(92, 228, 255, 215),
):
    """Whisper-quiet 35mm optical viewfinder marks at the extreme margin — no boxes, no panels."""
    # Tiny 8px corner registration ticks
    m = 22
    tlen = 10
    col = (accent[0], accent[1], accent[2], 140)
    for cx, cy, sx, sy in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        draw.line([(cx, cy), (cx + sx * tlen, cy)], fill=col, width=1)
        draw.line([(cx, cy), (cx, cy + sy * tlen)], fill=col, width=1)

    draw_shadow_text(draw, (m + 14, m + 2), left_mark, FONT_XS, fill=accent)
    rw = len(right_mark) * 8
    draw_shadow_text(draw, (W - m - 14 - rw, m + 2), right_mark, FONT_XS, fill=(210, 222, 235, 200))

    if bottom_left_mark:
        draw_shadow_text(draw, (m + 14, H - m - 18), bottom_left_mark, FONT_MICRO, fill=(185, 200, 215, 190))
    if bottom_right_mark:
        brw = len(bottom_right_mark) * 7
        draw_shadow_text(draw, (W - m - 14 - brw, H - m - 18), bottom_right_mark, FONT_MICRO, fill=accent)


# ==============================================================================
# OPTION I: Full-Bleed 3D Metric Point Cloud (points.ply) + Depth-Occluded Worldtext
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
    canvas = np.full((H, W, 3), (5, 7, 10), dtype=np.uint8)
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    place_name = view_meta.get("place_name", "")
    vid = view_meta.get("id", "V92")

    raw_z = -pts["z"].astype(np.float32)
    z_med = float(np.clip(np.median(raw_z), 2.2, 14.0))
    z_p75 = float(np.clip(np.percentile(raw_z, 75), z_med + 1.5, 24.0))
    z_p25 = float(np.clip(np.percentile(raw_z, 25), 1.2, z_med - 0.5))

    angle = math.sin(t_phase * math.tau) * 0.13 + 0.06
    cam_tx = (math.sin(t_phase * math.tau) * 0.10 + 0.05) * z_med
    cam_ty = (math.cos(t_phase * math.tau) * 0.025 + 0.01) * z_med
    cam_tz = -0.08 * z_med + 0.04 * z_med * math.sin(t_phase * math.pi)

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

    fx = W * 0.74
    fy = W * 0.74
    cx, cy = W * 0.50, H * 0.51
    u = np.round(cx + (xr / zr) * fx).astype(np.int32)
    v = np.round(cy - (y / zr) * fy).astype(np.int32)

    in_bounds = (u >= 0) & (u < W - 2) & (v >= 0) & (v < H - 2)
    u, v, zr, r, g, b = u[in_bounds], v[in_bounds], zr[in_bounds], r[in_bounds], g[in_bounds], b[in_bounds]

    order = np.argsort(-zr)
    u, v, zr, r, g, b = u[order], v[order], zr[order], r[order], g[order], b[order]

    scan_z = z_p25 + ((t_phase * 1.15) % 1.0) * max(2.0, z_p75 - z_p25)

    def splat_depth_band(img_bgr: np.ndarray, z_far: float, z_near: float):
        mask = (zr <= z_far) & (zr > z_near)
        if not np.any(mask):
            return
        uu, vv, zz = u[mask], v[mask], zr[mask]
        rr, gg, bb = r[mask], g[mask], b[mask]

        dist_scan = np.abs(zz - scan_z)
        pulse = np.exp(-0.5 * (dist_scan / max(0.55, 0.16 * z_med)) ** 2)
        lum = 0.299 * rr + 0.587 * gg + 0.114 * bb

        out_r = np.clip(rr * 1.38 * (1.0 - 0.45 * pulse) + (lum * 1.45 + 115) * (0.80 * pulse), 0, 255).astype(np.uint8)
        out_g = np.clip(gg * 1.38 * (1.0 - 0.45 * pulse) + (lum * 1.05 + 60) * (0.80 * pulse), 0, 255).astype(np.uint8)
        out_b = np.clip(bb * 1.38 * (1.0 - 0.45 * pulse) + (lum * 0.40 + 18) * (0.80 * pulse), 0, 255).astype(np.uint8)

        img_bgr[vv, uu, 0] = out_b
        img_bgr[vv, uu, 1] = out_g
        img_bgr[vv, uu, 2] = out_r
        img_bgr[vv, uu + 1, 0] = out_b
        img_bgr[vv, uu + 1, 1] = out_g
        img_bgr[vv, uu + 1, 2] = out_r
        img_bgr[vv + 1, uu, 0] = (out_b.astype(np.uint16) * 4 // 5).astype(np.uint8)
        img_bgr[vv + 1, uu, 1] = (out_g.astype(np.uint16) * 4 // 5).astype(np.uint8)
        img_bgr[vv + 1, uu, 2] = (out_r.astype(np.uint16) * 4 // 5).astype(np.uint8)

    # 1. Far & Mid-Deep Point Cloud (100m -> z_med)
    splat_depth_band(canvas, 100.0, z_med)

    # 2. Unboxed Diegetic Worldtext floating inside the 3D space at Z = z_med
    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    raw_lines = extract_clean_lines(poem_meta, breakdown_json)
    line_a = raw_lines[0] if raw_lines else title_str
    line_b = raw_lines[1] if len(raw_lines) > 1 else ""

    tx = int(W * 0.16 - angle * 180)
    ty = int(H * 0.48)
    # Thin 1px horizontal datum hairline at Z = z_med
    d.line([(tx - 30, ty - 14), (tx + 520, ty - 14)], fill=(255, 195, 90, 120), width=1)
    draw_shadow_text(d, (tx, ty - 34), f"Z = {z_med:.2f}m · P2 ACTION THRESHOLD", FONT_MICRO, fill=(255, 195, 90, 210))
    draw_shadow_text(d, (tx, ty), f"“{line_a[:58]}”", FONT_SERIF_XL, fill=(255, 246, 225, 248))
    if line_b:
        draw_shadow_text(d, (tx + 24, ty + 54), f"“{line_b[:58]}”", FONT_SERIF_LG, fill=(235, 215, 175, 230))

    pil = Image.alpha_composite(pil, ov)
    canvas = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)

    # 3. Foreground Point Cloud (z_med -> 0.55m) — naturally occludes the unboxed worldtext in 3D space!
    splat_depth_band(canvas, z_med, 0.55)

    # Subtle optical bloom
    blur = cv2.GaussianBlur(canvas, (0, 0), sigmaX=3.5)
    canvas = cv2.addWeighted(canvas, 0.90, blur, 0.22, 0)

    # Minimal right-margin metric Z ruler + corner viewfinder whisper
    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    hud = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hud)

    rx = W - 44
    y_top, y_bot = int(H * 0.22), int(H * 0.78)
    hd.line([(rx, y_top), (rx, y_bot)], fill=(255, 195, 90, 110), width=1)
    for frac, z_val, lbl in [(0.0, z_p75, f"{z_p75:.1f}m P5"), (0.5, z_med, f"{z_med:.1f}m P2"), (1.0, z_p25, f"{z_p25:.1f}m P1")]:
        yy = int(y_top + frac * (y_bot - y_top))
        hd.line([(rx - 8, yy), (rx + 4, yy)], fill=(255, 195, 90, 180), width=1)
        draw_shadow_text(hd, (rx - 82, yy - 7), lbl, FONT_MICRO, fill=(255, 195, 90, 195))

    draw_viewfinder_whisper(
        hd,
        W,
        H,
        f"{num_str} · {title_str.upper()}  //  {vid} {place_name.upper()}",
        f"I · METRIC POINT FIELD ({len(pts):,} PTS · Δx={cam_tx:+.2f}m)",
        bottom_left_mark=f"P0/P1 FOREGROUND OCCLUSION @ Z < {z_med:.2f}m",
        bottom_right_mark=f"SCAN WAVE Z = {scan_z:.2f}m",
        accent=(255, 195, 90, 225),
    )
    pil = Image.alpha_composite(pil, hud)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION II: Full-Bleed 3D Isometric Exploded Multiplane Stratigraphy
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
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    vid = view_meta.get("id", "V92")
    place_name = view_meta.get("place_name", "")

    exploded_img = cv2.imread(str(shot_dir / "multiplane/exploded.jpg"))
    plane_map_img = cv2.imread(str(shot_dir / "multiplane/plane_map.jpg"))
    orig_img = cv2.imread(str(shot_dir / "image.jpg"))

    # Full-bleed atmospheric background from heavily darkened & blurred depth map
    bg = cover_crop(plane_map_img if plane_map_img is not None else orig_img, W, H)
    bg = (bg.astype(np.float32) * 0.16).astype(np.uint8)
    bg = cv2.GaussianBlur(bg, (0, 0), sigmaX=18.0)

    # Full-bleed centered isometric exploded stack occupying the open center
    if exploded_img is not None:
        eh, ew = exploded_img.shape[:2]
        scale = min((W * 0.88) / max(ew, 1), (H * 0.84) / max(eh, 1))
        nw, nh = int(round(ew * scale)), int(round(eh * scale))
        exp_resized = cv2.resize(exploded_img, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        x0 = (W - nw) // 2
        y0 = (H - nh) // 2
        bg[y0 : y0 + nh, x0 : x0 + nw] = exp_resized

    pil = Image.fromarray(cv2.cvtColor(bg, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # Delicate unboxed optical callout hairlines along the right side of the exploded stack
    planes = [p for p in multiplane_json.get("planes", []) if (p.get("area_frac") or 0) > 0.01][:5]
    active_idx = int(t_phase * max(1, len(planes))) % max(1, len(planes))
    for idx, p in enumerate(planes):
        pid = p.get("id", f"P{idx}")
        pname = p.get("name", "").upper()
        zm = p.get("z_median_m")
        z_str = f"{zm:.2f}m" if isinstance(zm, (int, float)) else "∞"
        par = p.get("parallax") or 0.0
        yy = int(H * (0.24 + idx * 0.12))
        col = (92, 228, 255, 240) if idx == active_idx else (180, 205, 225, 175)
        d.line([(int(W * 0.72), yy), (int(W * 0.78), yy)], fill=col, width=1)
        draw_shadow_text(d, (int(W * 0.78) + 10, yy - 8), f"{pid} {pname} · Z={z_str} · ×{par:.2f}", FONT_XS, fill=col)

    # Whisper the Golden Riverbed law along the lower center without any box
    rb_core = riverbed_json.get("riverbed", {}).get("core_identity", "") or poem_meta.get("essence", "")
    if rb_core:
        draw_shadow_text(d, (int(W * 0.12), H - 64), f"“{rb_core[:112]}”", FONT_SERIF_SM, fill=(242, 232, 210, 220))

    draw_viewfinder_whisper(
        d,
        W,
        H,
        f"{num_str} · {title_str.upper()}  //  {vid} {place_name.upper()}",
        "II · MULTIPLANE GLASS STRATIGRAPHY (P0–P6)",
        bottom_left_mark="ISOMETRIC PLANE SEPARATION · TRUE METRIC PARALLAX",
        bottom_right_mark=f"GOLDEN RIVERBED · WYGWYL {num_str}",
        accent=(92, 228, 255, 225),
    )
    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION III: Full-Bleed Surveyor's Perspective Grid & Darkroom Line Layout Wipe
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
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    vid = view_meta.get("id", "V92")
    place_name = view_meta.get("place_name", "")

    layout_sheet = cv2.imread(str(shot_dir / "cartoon/layout_sheet.png"))
    layout_draw = cv2.imread(str(shot_dir / "multiplane/layout_drawing.png"))
    orig_img = cv2.imread(str(shot_dir / "image.jpg"))

    # Full-bleed Left: Solved 3D perspective floor grid (layout_sheet) blended with dark original
    left_full = cover_crop(layout_sheet if layout_sheet is not None else orig_img, W, H)
    # Full-bleed Right: Darkroom architectural blueprint of traditional animation linework (layout_drawing)
    raw_line = cover_crop(layout_draw if layout_draw is not None else orig_img, W, H)
    inv_line = 255 - raw_line
    right_full = np.zeros_like(inv_line)
    right_full[:, :, 0] = np.clip(inv_line[:, :, 0].astype(np.int32) * 1.15 + 16, 0, 255).astype(np.uint8)
    right_full[:, :, 1] = np.clip(inv_line[:, :, 1].astype(np.int32) * 1.05 + 12, 0, 255).astype(np.uint8)
    right_full[:, :, 2] = np.clip(inv_line[:, :, 2].astype(np.int32) * 0.75 + 8, 0, 255).astype(np.uint8)
    if orig_img is not None:
        orig_cov = cover_crop(orig_img, W, H)
        right_full = cv2.addWeighted(orig_cov, 0.24, right_full, 0.88, 0)

    split_x = int(W * (0.48 + 0.18 * math.sin(t_phase * math.tau)))
    canvas = left_full.copy()
    canvas[:, split_x:] = right_full[:, split_x:]

    # 1px surveyor's plumb-line at split_x and solved horizon line across full width
    hy = int(shot_json.get("camera", {}).get("horizon_y_norm", 0.50) * H)
    cv2.line(canvas, (split_x, 0), (split_x, H), (130, 245, 175), 1, cv2.LINE_AA)
    cv2.line(canvas, (0, hy), (W, hy), (130, 245, 175), 1, cv2.LINE_AA)

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # Whisper assembly manuscript line right along the solved horizon datum — zero boxes
    ms_lines = [ln.strip() for ln in str(assembly_text).splitlines() if ln.strip() and not ln.strip().startswith("{")]
    ms_excerpt = "  /  ".join(ms_lines[:3]) if ms_lines else title_str
    draw_shadow_text(d, (split_x + 18, hy - 30), f"HORIZON Y={hy}px · ASSEMBLY P.{assembly_page_num}", FONT_MICRO, fill=(130, 245, 175, 225))
    draw_shadow_text(d, (split_x + 18, hy + 8), f"“{ms_excerpt[:78]}”", FONT_SERIF_MD, fill=(245, 242, 230, 240))

    draw_viewfinder_whisper(
        d,
        W,
        H,
        f"{num_str} · {title_str.upper()}  //  {vid} {place_name.upper()}",
        f"III · SURVEYOR PERSPECTIVE & LINE TABLE (SEAM X={split_x}px)",
        bottom_left_mark="◀ SOLVED 3D PERSPECTIVE FLOOR GRID (layout_sheet.png)",
        bottom_right_mark="DARKROOM ANIMATION LINEWORK (layout_drawing.png) ▶",
        accent=(130, 245, 175, 225),
    )
    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION IV: Full-Bleed Machine-Eye Optical Aperture Lens (SAM2 & Vector ΔE)
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
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    vid = view_meta.get("id", "V92")
    place_name = view_meta.get("place_name", "")

    orig_img = cover_crop(cv2.imread(str(shot_dir / "image.jpg")), W, H)
    overlay_img = cover_crop(cv2.imread(str(shot_dir / "overlay.jpg")), W, H)
    cel_img = cover_crop(cv2.imread(str(shot_dir / "cartoon/cel.png")), W, H)

    # Outer field: darkened photographic still blended with subtle cel edges
    outer = cv2.addWeighted(orig_img, 0.55, cel_img, 0.25, 0)
    # Inner lens aperture: full-clarity pixel-accurate SAM2 object boundaries (overlay.jpg)
    cx = int(W * (0.50 + 0.14 * math.cos(t_phase * math.tau)))
    cy = int(H * (0.50 + 0.08 * math.sin(t_phase * math.tau)))
    radius = int(H * 0.37)

    yy, xx = np.ogrid[:H, :W]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    alpha = np.clip((radius - dist) / 3.0, 0.0, 1.0)[..., None]
    canvas = (overlay_img.astype(np.float32) * alpha + outer.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)

    # Crisp 1px optical reticle ring & crosshair ticks
    cv2.circle(canvas, (cx, cy), radius, (255, 130, 195), 1, cv2.LINE_AA)
    cv2.circle(canvas, (cx, cy), radius + 8, (92, 228, 255), 1, cv2.LINE_AA)
    for deg in range(0, 360, 15):
        rad = math.radians(deg)
        r_in = radius + 8
        r_out = radius + (18 if deg % 45 == 0 else 12)
        x1, y1 = int(cx + r_in * math.cos(rad)), int(cy + r_in * math.sin(rad))
        x2, y2 = int(cx + r_out * math.cos(rad)), int(cy + r_out * math.sin(rad))
        cv2.line(canvas, (x1, y1), (x2, y2), (92, 228, 255), 1, cv2.LINE_AA)

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    felt_str = perceive_json.get("felt", "enclosed, close walls, no horizon to escape to")
    n_reg = perceive_json.get("n_regions", 0)
    draw_shadow_text(
        d,
        (cx - radius + 20, cy + radius + 22),
        f"SAM2 RETICLE ({n_reg} REGIONS) · FELT: “{felt_str[:76]}”",
        FONT_XS,
        fill=(255, 130, 195, 235),
    )

    draw_viewfinder_whisper(
        d,
        W,
        H,
        f"{num_str} · {title_str.upper()}  //  {vid} {place_name.upper()}",
        f"IV · MACHINE-EYE SAM2 APERTURE (R={radius}px)",
        bottom_left_mark="OUTER FIELD: PHOTOGRAPHIC STILL (image.jpg)",
        bottom_right_mark="APERTURE: PIXEL-ACCURATE SAM2 CONTOURS (overlay.jpg)",
        accent=(255, 130, 195, 225),
    )
    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION V: Full-Bleed Darkroom Animator's Light-Table Cut-Out Kit
# ==============================================================================
def render_option_5_tactile_kits(
    W: int,
    H: int,
    poem_meta: dict,
    dossier_json: dict,
    breakdown_json: dict,
    t_phase: float = 0.0,
) -> np.ndarray:
    canvas = np.full((H, W, 3), (8, 9, 12), dtype=np.uint8)
    num_str = poem_meta.get("num", "01")
    title_str = poem_meta.get("title", "")
    kits_dir = SHOTS_DIR / "poems/kits"

    set_kits = sorted(kits_dir.glob(f"{num_str}.set.*.jpg"))
    prop_kits = sorted(kits_dir.glob(f"{num_str}.props*.jpg"))
    hero_kits = sorted(kits_dir.glob(f"{num_str}.hero.*.jpg")) + sorted(kits_dir.glob(f"{num_str}.fx*.jpg"))
    all_kits = sorted(kits_dir.glob(f"{num_str}.*.jpg"))

    kit_a_path = set_kits[0] if set_kits else (all_kits[0] if all_kits else None)
    kit_b_path = prop_kits[0] if prop_kits else (all_kits[1] if len(all_kits) > 1 else kit_a_path)

    kit_main = cv2.imread(str(kit_a_path)) if kit_a_path else None
    kit_sub = cv2.imread(str(kit_b_path)) if kit_b_path else None

    # Full-bleed primary cut-out sheet centered on the darkroom light-table
    if kit_main is not None:
        fitted = fit_contain(kit_main, int(W * 0.90), int(H * 0.84), bg_color=(8, 9, 12))
        y0 = (H - fitted.shape[0]) // 2
        x0 = (W - fitted.shape[1]) // 2
        canvas[y0 : y0 + fitted.shape[0], x0 : x0 + fitted.shape[1]] = fitted

    # Subtle optical loupe / inset of the prop kit sheet in bottom-right corner if distinct
    if kit_sub is not None and kit_b_path != kit_a_path:
        sub_w, sub_h = int(W * 0.25), int(H * 0.25)
        sub_fit = fit_contain(kit_sub, sub_w, sub_h, bg_color=(12, 14, 18))
        sy0, sx0 = H - sub_h - 48, W - sub_w - 42
        canvas[sy0 : sy0 + sub_h, sx0 : sx0 + sub_w] = sub_fit
        cv2.rectangle(canvas, (sx0, sy0), (sx0 + sub_w - 1, sy0 + sub_h - 1), (255, 195, 90), 1)

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    props = dossier_json.get("props", [])
    prop_note = f"{props[0]['id']}: {props[0].get('build', '')[:88]}" if props else ""
    draw_viewfinder_whisper(
        d,
        W,
        H,
        f"{num_str} · {title_str.upper()}  //  MULTIPLANE CUT-OUT LIGHT-TABLE",
        f"V · PHYSICAL CRAFT KIT ({kit_a_path.name if kit_a_path else ''})",
        bottom_left_mark=f"BRASS-BRAD PIVOTS (+) · {prop_note}",
        bottom_right_mark=f"INSET: {kit_b_path.name if kit_b_path else ''}",
        accent=(255, 195, 90, 225),
    )
    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==============================================================================
# OPTION VI: Full-Bleed 4-Layer Optical Slit-Scan & Echo Curtain
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
    x1 = int(W * (0.27 + shift))
    x2 = int(W * (0.53 + shift * 0.5))
    x3 = int(W * (0.76 - shift * 0.5))

    canvas = img_orig.copy()
    canvas[:, x1:x2] = img_cel[:, x1:x2]
    line_inv = 255 - img_line
    line_blueprint = np.zeros_like(line_inv)
    line_blueprint[:, :, 0] = np.clip(line_inv[:, :, 0].astype(np.int32) + 22, 0, 255).astype(np.uint8)
    line_blueprint[:, :, 1] = np.clip(line_inv[:, :, 1].astype(np.int32) + 16, 0, 255).astype(np.uint8)
    line_blueprint[:, :, 2] = np.clip(line_inv[:, :, 2].astype(np.int32) + 10, 0, 255).astype(np.uint8)
    canvas[:, x2:x3] = cv2.addWeighted(img_orig[:, x2:x3], 0.28, line_blueprint[:, x2:x3], 0.88, 0)
    canvas[:, x3:] = img_echo[:, x3:]

    # Razor-thin 1px vertical optical hairlines — zero heavy bars
    for sx, col in [(x1, (92, 228, 255)), (x2, (255, 195, 90)), (x3, (255, 130, 195))]:
        cv2.line(canvas, (sx, 0), (sx, H), col, 1, cv2.LINE_AA)

    hy = int(shot_json.get("camera", {}).get("horizon_y_norm", 0.50) * H)
    cv2.line(canvas, (0, hy), (W, hy), (92, 228, 255), 1, cv2.LINE_AA)

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # Unboxed micro-engravings at top of each optical curtain band
    bands = [
        (36, f"I · {vid} STILL", (225, 235, 245, 210)),
        (x1 + 14, f"II · {vid} CARTOON CEL", (92, 228, 255, 225)),
        (x2 + 14, f"III · {vid} LINE LAYOUT", (255, 195, 90, 225)),
        (x3 + 14, f"IV · ECHO {evid} ({echo_place[:20]})", (255, 130, 195, 235)),
    ]
    for bx, btxt, bcol in bands:
        draw_shadow_text(d, (bx, H - 44), btxt, FONT_MICRO, fill=bcol)

    ft = poem_meta.get("full_text", [])
    poem_lines = [
        (ln.get("line", "") if isinstance(ln, dict) else str(ln)).strip()
        for ln in (ft if isinstance(ft, list) else str(ft).splitlines())
    ]
    poem_lines = [ln for ln in poem_lines if ln]
    v_str = "  /  ".join(poem_lines[:2]) if poem_lines else title_str
    draw_shadow_text(d, (42, hy - 36), f"“{v_str[:88]}”", FONT_SERIF_MD, fill=(250, 244, 228, 245))

    draw_viewfinder_whisper(
        d,
        W,
        H,
        f"{num_str} · {title_str.upper()}  //  {vid} ({place_name.upper()}) ↔ {evid} ({echo_place.upper()})",
        f"VI · 4-LAYER OPTICAL SLIT-SCAN (HORIZON Y={hy}px)",
        accent=(92, 228, 255, 225),
    )
    pil = Image.alpha_composite(pil, ov)
    return cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)


def build_14_poem_master_sheet(items: list, out_path: Path, title_banner: str):
    sheet = np.full((2160, 3840, 3), (5, 7, 10), dtype=np.uint8)
    cw, ch = 960, 540
    for idx, (num_str, title_str, img) in enumerate(items[:14]):
        r = idx // 4
        c = idx % 4
        cell = fit_contain(img, cw, ch, bg_color=(6, 8, 11))
        y0, x0 = r * ch, c * cw
        sheet[y0 : y0 + ch, x0 : x0 + cw] = cell
        cv2.rectangle(sheet, (x0, y0), (x0 + cw - 1, y0 + ch - 1), (32, 48, 66), 1)

    pil = Image.fromarray(cv2.cvtColor(sheet, cv2.COLOR_BGR2RGB)).convert("RGBA")
    d = ImageDraw.Draw(pil)
    x0, y0 = 1920, 1620
    draw_shadow_text(d, (x0 + 48, y0 + 48), "WHERE YOU GO WHEN YOU LEAVE — ALL 14 POEMS", FONT_XL, fill=(92, 228, 255, 245))
    draw_shadow_text(d, (x0 + 48, y0 + 92), title_banner, FONT_LG, fill=(255, 195, 90, 240))
    draw_shadow_text(
        d,
        (x0 + 48, y0 + 138),
        "VOIDBASTARD-TAO UNOBSTRUCTED SURFACE · 100% FULL-BLEED CINEMA PLATES · ZERO HUD BOXES",
        FONT_SM,
        fill=(195, 212, 228, 220),
    )

    py = y0 + 196
    for col_idx in range(2):
        subset = items[col_idx * 7 : (col_idx + 1) * 7]
        px = x0 + 48 + col_idx * 910
        for i, (ns, ts, _) in enumerate(subset):
            p_num = int(ns)
            hid, eid = HERO_AND_ECHO_VIEWS[p_num]
            draw_shadow_text(d, (px, py + i * 40), f"{ns} · {ts[:24]:24s}  [{hid} ↔ {eid}]", FONT_MD, fill=(130, 245, 175, 230))

    out_bgr = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(out_path), out_bgr)
    shutil.copy2(out_path, ARTIFACT_DIR / out_path.name)
    print(f"[master-sheet] Saved {out_path.name}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bundle_path = OUT_DIR / "vesper_world_bundle.json"
    bundle = json.loads(bundle_path.read_text())

    opt1_all, opt2_all, opt3_all, opt4_all, opt5_all, opt6_all = [], [], [], [], [], []
    per_poem_mp4s = []

    W, H = 1920, 1080
    fps = 24
    frames_per_opt = 12

    for p in bundle["poems"]:
        num = int(p["num"])
        num_str = f"{num:02d}"
        title_str = p.get("title", "")
        hid, eid = HERO_AND_ECHO_VIEWS[num]
        vmap = {v["id"]: v for v in p.get("views", [])}
        hv = vmap.get(hid, p["views"][0])
        ev = vmap.get(eid, p["views"][-1])

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
            assembly_text = apages[0].get("text", "") or p.get("poem_text", "")
        else:
            apage_num = apages[0] if apages else 1
            apage_path = SHOTS_DIR / f"poems/assembly/assembly_p{apage_num}.txt"
            assembly_text = apage_path.read_text() if apage_path.exists() else p.get("poem_text", "")
        p["assembly_excerpt"] = str(assembly_text)[:1200]

        print(f"[poem {num_str}] Rendering 6 Full-Bleed VOIDBASTARD-TAO Plates for Poem {num_str} ({title_str})...")
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
            cv2.imwrite(str(OUT_DIR / o_name), o_img, [int(cv2.IMWRITE_JPEG_QUALITY), 93])
            opt_paths[f"opt{o_idx}"] = f"data/terrarium/seeing_spacetime_films/{o_name}"

        opt1_all.append((num_str, title_str, opt1))
        opt2_all.append((num_str, title_str, opt2))
        opt3_all.append((num_str, title_str, opt3))
        opt4_all.append((num_str, title_str, opt4))
        opt5_all.append((num_str, title_str, opt5))
        opt6_all.append((num_str, title_str, opt6))

        sheet = np.full((2160, 3840, 3), (5, 7, 10), dtype=np.uint8)
        for idx, o_img in enumerate(opt_imgs):
            r = idx // 2
            c = idx % 2
            cell = fit_contain(o_img, 1920, 720, bg_color=(6, 8, 11))
            y0, x0 = r * 720, c * 1920
            sheet[y0 : y0 + 720, x0 : x0 + 1920] = cell
            cv2.rectangle(sheet, (x0, y0), (x0 + 1919, y0 + 719), (32, 48, 66), 1)

        sheet_name = f"poem_{num_str}_apparatus_6options.png"
        cv2.imwrite(str(OUT_DIR / sheet_name), sheet)
        shutil.copy2(OUT_DIR / sheet_name, ARTIFACT_DIR / sheet_name)
        opt_paths["sheet"] = f"data/terrarium/seeing_spacetime_films/{sheet_name}"

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

    bundle_path.write_text(json.dumps(bundle, indent=2))
    print(f"[bundle] Saved enriched 14-poem bundle -> {bundle_path}")

    build_14_poem_master_sheet(
        opt1_all,
        OUT_DIR / "all_14_poems_pointcloud_worldtext_sheet.png",
        "I · METRIC 3D POINT CLOUD (points.ply) + UNBOXED DEPTH-OCCLUDED WORLDTEXT",
    )
    build_14_poem_master_sheet(
        opt2_all,
        OUT_DIR / "all_14_poems_exploded_multiplane_sheet.png",
        "II · FULL-BLEED ISOMETRIC EXPLODED MULTIPLANE STACKS (exploded.jpg)",
    )
    build_14_poem_master_sheet(
        opt3_all,
        OUT_DIR / "all_14_poems_perspective_layout_sheet.png",
        "III · SURVEYOR 3D PERSPECTIVE FLOOR GRID ↔ DARKROOM LINE LAYOUT WIPE",
    )
    build_14_poem_master_sheet(
        opt4_all,
        OUT_DIR / "all_14_poems_semantic_perceptual_sheet.png",
        "IV · MACHINE-EYE SAM2 OPTICAL APERTURE RETICLE (image.jpg ↔ overlay.jpg)",
    )
    build_14_poem_master_sheet(
        opt5_all,
        OUT_DIR / "all_14_poems_tactile_kits_sheet.png",
        "V · DARKROOM ANIMATOR'S LIGHT-TABLE CUT-OUT KITS (poems/kits/NN.*.jpg)",
    )
    build_14_poem_master_sheet(
        opt6_all,
        OUT_DIR / "all_14_poems_xray_echo_sheet.png",
        "VI · 4-LAYER OPTICAL SLIT-SCAN & SHARED COMMON-PLACE ECHO CURTAIN",
    )

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
    print(f"[master-reel] Saved 14-Poem Master Apparatus Reel -> {master_mp4}")


if __name__ == "__main__":
    main()
