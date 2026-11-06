#!/usr/bin/env python3
"""
Purify all repository puppet part libraries in-place:
  1. shots/arena/parts/kit3/v2/parts/*/*.png       (3,869 files)
  2. shots/arena/parts/kit3/release_v2/cuts/*/*.png (6,234 files)
  3. shots/suite/parts/cut/*/*.webp                 (3,489 files)

Removes:
  - Brass grommet rings and internal grommet holes at joints/sockets/neck-tabs
  - Tan/kraft/white die-cut cardboard sticker bevels around the outer perimeter
while preserving exact (W, H) image dimensions and card coverage so all JSON
pivots/sockets and Arena measurements (brad_gap, holes == 0) remain valid.
"""

import glob
import json
import os
import sys
import time
from multiprocessing import Pool
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)

# Load known brad/socket points per relative path from cast_parts.json and parts.json
FILE_BRADS = {}
cp_path = os.path.join(SHOTS, "suite", "data", "cast_parts.json")
if os.path.exists(cp_path):
    cp = json.load(open(cp_path)).get("characters", {})
    for cid, c in cp.items():
        for v, parts in c.get("views", {}).items():
            for pname, p in parts.items():
                f = p.get("file")
                if not f:
                    continue
                pts = FILE_BRADS.setdefault(f, [])
                if "A" in p:
                    pts.append(p["A"])
                if "B" in p:
                    pts.append(p["B"])
                for s, q in p.get("sockets", {}).items():
                    pts.append(q)
        for v, h in c.get("heads", {}).items():
            f = h.get("file")
            if not f:
                continue
            pts = FILE_BRADS.setdefault(f, [])
            if "neck" in h:
                pts.append(h["neck"])

pp_path = os.path.join(SHOTS, "suite", "data", "parts.json")
if os.path.exists(pp_path):
    pp = json.load(open(pp_path)).get("parts", [])
    for p in pp:
        f = p.get("file")
        if not f:
            continue
        pts = FILE_BRADS.setdefault(f, [])
        if p.get("pivot"):
            pts.append(p["pivot"])
        for s, q in (p.get("sockets") or {}).items():
            if isinstance(q, list) and len(q) == 2:
                pts.append(q)


def purify_part_rgba(rgba, rel_file="", known_pts=None):
    h, w = rgba.shape[:2]
    if h < 8 or w < 8:
        return rgba
    rgb = rgba[:, :, :3].copy()
    alpha = rgba[:, :, 3].copy()
    fg = (alpha > 24).astype(np.uint8)
    if fg.sum() < 20:
        return rgba

    bname = os.path.basename(rel_file)
    is_head = ("head." in bname) or ("/head" in rel_file)
    is_v2_body = ("arena/parts/kit3/v2/parts/" in rel_file)

    # 1. Fill internal transparent holes (grommet center holes)
    inv_a = (alpha <= 200).astype(np.uint8)
    num_l, labels, stats, _ = cv2.connectedComponentsWithStats(inv_a)
    hole_mask = np.zeros((h, w), dtype=np.uint8)
    max_hole_area = h * w * (0.08 if is_v2_body else 0.04)
    for i in range(1, num_l):
        x0, y0, cw, ch, area = stats[i]
        touches_border = (x0 <= 1 or y0 <= 1 or x0 + cw >= w - 1 or y0 + ch >= h - 1)
        if not touches_border and area < max_hole_area and cw < 42 and ch < 42:
            hole_mask[labels == i] = 255
            alpha[labels == i] = 255
            fg[labels == i] = 1

    dist_out = cv2.distanceTransform(fg, cv2.DIST_L2, 5)
    r = rgb[:, :, 0].astype(np.float32)
    g = rgb[:, :, 1].astype(np.float32)
    b = rgb[:, :, 2].astype(np.float32)
    lum = 0.299 * r + 0.587 * g + 0.114 * b

    # 2. Allowed Grommet Search Zone
    allowed_zone = np.zeros((h, w), dtype=np.uint8)
    ys, xs = np.where(fg > 0)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    bw, bh = max(1, x1 - x0), max(1, y1 - y0)

    if is_head:
        ny0 = int(y0 + bh * 0.74)
        allowed_zone[ny0:y1 + 1, x0:x1 + 1] = 255
        if known_pts:
            for pt in known_pts:
                cv2.circle(allowed_zone, (int(round(pt[0])), int(round(pt[1]))), 28, 255, -1)
    elif known_pts and len(known_pts) > 0:
        for pt in known_pts:
            cv2.circle(allowed_zone, (int(round(pt[0])), int(round(pt[1]))), 36, 255, -1)
        if "torso" in bname or "pelvis" in bname:
            allowed_zone[y0:int(y0 + bh * 0.28), x0:x1 + 1] = 255
            allowed_zone[int(y1 - bh * 0.22):y1 + 1, x0:x1 + 1] = 255
    else:
        if bh >= bw:
            allowed_zone[y0:int(y0 + bh * 0.25), x0:x1 + 1] = 255
            allowed_zone[int(y1 - bh * 0.25):y1 + 1, x0:x1 + 1] = 255
        else:
            allowed_zone[y0:y1 + 1, x0:int(x0 + bw * 0.25)] = 255
            allowed_zone[y0:y1 + 1, int(x1 - bw * 0.25):x1 + 1] = 255

    is_gold_ring = (
        (allowed_zone > 0) &
        (dist_out > 3.5) &
        (r > 130) & (g > 95) & (b < 140) &
        (r - b > 32) &
        (g / np.maximum(r, 1.0) > 0.56) &
        (g / np.maximum(r, 1.0) < 0.96)
    ).astype(np.uint8) * 255

    grommet_mask = np.zeros((h, w), dtype=np.uint8)
    if hole_mask.max() > 0:
        hole_in_zone = cv2.bitwise_and(hole_mask, allowed_zone)
        if hole_in_zone.max() > 0:
            grommet_mask = cv2.dilate(hole_in_zone, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))

    num_g, g_labels, g_stats, g_cent = cv2.connectedComponentsWithStats(is_gold_ring)
    for i in range(1, num_g):
        gx, gy, gw, gh, garea = g_stats[i]
        if 16 <= garea <= 2800 and gw <= 56 and gh <= 56:
            aspect = max(gw, gh) / max(1.0, min(gw, gh))
            if aspect <= 2.2:
                cx, cy = int(round(g_cent[i][0])), int(round(g_cent[i][1]))
                rad = int(max(gw, gh) * 0.60) + 4
                cv2.circle(grommet_mask, (cx, cy), min(rad, 22), 255, -1)

    # On head cards, detect the neck stud highlight/shadow crescent inside the bottom 25% neck tab
    if is_head:
        neck_zone = (np.arange(h)[:, None] >= int(y0 + bh * 0.76)) & (dist_out > 5.5)
        stud_feat = neck_zone & (
            ((r > 205) & (g > 180) & (r - b > 25)) |
            ((b < 48) & (lum < 92) & (r > b + 28))
        )
        if stud_feat.sum() >= 3:
            ys_s, xs_s = np.where(stud_feat)
            scx = int(np.median(xs_s))
            scy = int(np.median(ys_s))
            cv2.circle(grommet_mask, (scx, scy), 15, 255, -1)

    # 3. Perimeter cardboard/kraft/white sticker bevel replacement
    if is_head:
        is_perimeter_bevel = (
            (dist_out <= 5.5) & (dist_out > 0) &
            (
                ((lum > 185) & (np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b) < 45)) |
                (dist_out <= 3.0)
            )
        )
        int_thresh = 4.0
    elif is_v2_body:
        is_perimeter_bevel = (
            (dist_out <= 8.0) & (dist_out > 0) &
            (
                ((g / np.maximum(r, 1.0) > 0.56) & (r - b > 16) & (lum > 60)) |
                ((lum > 195) & (np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b) < 40)) |
                (dist_out <= 5.0)
            )
        )
        int_thresh = 6.0
    else:
        # release_v2/cuts and suite/parts/cut: lighter perimeter cleanup so delicate props stay crisp
        is_perimeter_bevel = (
            (dist_out <= 5.5) & (dist_out > 0) &
            (
                ((g / np.maximum(r, 1.0) > 0.58) & (r - b > 22) & (lum > 95)) |
                ((lum > 210) & (np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b) < 32)) |
                (dist_out <= 2.5)
            )
        )
        int_thresh = 4.0

    valid_interior = (dist_out > int_thresh) & (~is_perimeter_bevel) & (grommet_mask == 0)
    if valid_interior.sum() < 20:
        valid_interior = (dist_out > 2.5) & (grommet_mask == 0)

    if valid_interior.sum() > 15:
        inv_valid = (~valid_interior).astype(np.uint8)
        _, labels_near = cv2.distanceTransformWithLabels(inv_valid, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        vy, vx = np.where(inv_valid == 0)
        idx = np.clip(labels_near - 1, 0, len(vy) - 1)
        nearest_rgb = rgb[vy[idx], vx[idx]]

        replace_bevel = is_perimeter_bevel | (dist_out <= 2.2)
        rgb[replace_bevel] = nearest_rgb[replace_bevel]

        if grommet_mask.max() > 0:
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            inpainted = cv2.inpaint(bgr, grommet_mask, 7, cv2.INPAINT_TELEA)
            rgb = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)

    edge_shade = np.clip((dist_out - 1.0) / 5.0, 0.84, 1.0)[:, :, None]
    rgb = np.clip(rgb.astype(np.float32) * edge_shade, 0, 255).astype(np.uint8)

    # Keep alpha size within ~1.5px of original so all sockets/pivots and brad hole checks pass
    erode_px = 1.6 if is_v2_body else 1.2
    core_u8 = (dist_out > erode_px).astype(np.uint8) * 255
    new_alpha = cv2.GaussianBlur(core_u8, (3, 3), 0.75)

    return np.dstack([rgb, new_alpha])


def process_one_file(abs_path):
    try:
        rel_file = os.path.relpath(abs_path, SHOTS)
        im = cv2.imread(abs_path, cv2.IMREAD_UNCHANGED)
        if im is None or im.ndim != 3 or im.shape[2] != 4:
            return False
        rgba = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
        known_pts = FILE_BRADS.get(rel_file, [])
        clean = purify_part_rgba(rgba, rel_file, known_pts)
        bgra = cv2.cvtColor(clean, cv2.COLOR_RGBA2BGRA)
        if abs_path.endswith(".webp"):
            cv2.imwrite(abs_path, bgra, [cv2.IMWRITE_WEBP_QUALITY, 92])
        else:
            cv2.imwrite(abs_path, bgra)
        return True
    except Exception:
        return False


def main():
    t0 = time.time()
    p1 = sorted(glob.glob(os.path.join(SHOTS, "arena/parts/kit3/v2/parts/*/*.png")))
    p2 = sorted(glob.glob(os.path.join(SHOTS, "arena/parts/kit3/release_v2/cuts/*/*.png")))
    p3 = sorted(glob.glob(os.path.join(SHOTS, "suite/parts/cut/*/*.webp")))
    all_files = p1 + p2 + p3
    print(f"Purifying {len(all_files)} part files ({len(p1)} v2/parts, {len(p2)} release_v2/cuts, {len(p3)} suite/parts/cut)...")
    with Pool(10) as pool:
        res = pool.map(process_one_file, all_files, chunksize=64)
    ok = sum(1 for r in res if r)
    print(f"Purified {ok}/{len(all_files)} files in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
