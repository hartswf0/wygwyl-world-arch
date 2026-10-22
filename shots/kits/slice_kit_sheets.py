#!/usr/bin/env python3
"""
slice_kit_sheets.py

Automated cutter pipeline for cardboard puppet kits:
- Takes multi-card landscape sheets (01_CHARACTER_CORE, 02_ACTIONS_AND_POSES, 03_PROPS, 04_SETS_AND_BUILDINGS).
- Detects detached cards separated by white background.
- Cuts out each working card as an alpha-channel PNG with transparent padding.
- Scans for circular brass split-pin brad fasteners and eyelets.
- Generates catalog.json and Component_Index.csv for the sliced parts.
"""

import os
import sys
import json
import csv
import glob
import cv2
import numpy as np
from PIL import Image

def detect_brads(rgb_crop):
    """
    Detects circular brass brads: warm golden / amber circular heads with dark pin center.
    """
    brads = []
    if rgb_crop.shape[0] < 20 or rgb_crop.shape[1] < 20:
        return brads
        
    gray = cv2.cvtColor(rgb_crop, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    
    # Hough Circles for small fastener circles
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=16,
        param1=50,
        param2=22,
        minRadius=3,
        maxRadius=24
    )
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for pt in circles[0, :]:
            cx, cy, r = int(pt[0]), int(pt[1]), int(pt[2])
            if 0 <= cy < rgb_crop.shape[0] and 0 <= cx < rgb_crop.shape[1]:
                # Check color around center: warm golden tone
                y1 = max(0, cy - r // 2)
                y2 = min(rgb_crop.shape[0], cy + r // 2 + 1)
                x1 = max(0, cx - r // 2)
                x2 = min(rgb_crop.shape[1], cx + r // 2 + 1)
                patch = rgb_crop[y1:y2, x1:x2]
                if patch.size > 0:
                    mean_r = np.mean(patch[:, :, 0])
                    mean_g = np.mean(patch[:, :, 1])
                    mean_b = np.mean(patch[:, :, 2])
                    # Golden/brass: warm, R > B + 15
                    if mean_r > mean_b + 12 and mean_r > 70:
                        brads.append({"cx": cx, "cy": cy, "radius": r, "color": "brass"})
                    elif np.mean(patch) < 80:
                        # Dark eyelet punch hole
                        brads.append({"cx": cx, "cy": cy, "radius": r, "color": "eyelet"})
                        
    # Deduplicate overlapping circles
    filtered = []
    for b in brads:
        dup = False
        for f in filtered:
            dist = np.hypot(b["cx"] - f["cx"], b["cy"] - f["cy"])
            if dist < 12:
                dup = True
                break
        if not dup:
            filtered.append(b)
            
    return filtered

def slice_sheet(sheet_path, out_dir, min_area=1200):
    sheet_name = os.path.splitext(os.path.basename(sheet_path))[0]
    sheet_dest = os.path.join(out_dir, sheet_name)
    os.makedirs(sheet_dest, exist_ok=True)
    
    im = Image.open(sheet_path).convert("RGBA")
    arr = np.array(im)
    h_orig, w_orig = arr.shape[:2]
    rgb = arr[:, :, :3]
    
    # White background detection (threshold > 242)
    is_white = (rgb[:, :, 0] > 240) & (rgb[:, :, 1] > 240) & (rgb[:, :, 2] > 240)
    fg_mask = (~is_white).astype(np.uint8) * 255
    
    # Morphological closing
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    
    # Find card contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    candidates = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        
        # Filter tiny specs or text badges
        if area < min_area:
            continue
        if w < 32 or h < 32:
            continue
            
        # Filter top title labels if small height and near top edge
        if y < 45 and h < 55 and w < 200:
            continue
            
        candidates.append((x, y, w, h, area, c))
        
    # Sort top-to-bottom, left-to-right
    candidates.sort(key=lambda item: (item[1] // 160, item[0]))
    
    pieces = []
    for idx, (x, y, w, h, area, c) in enumerate(candidates, start=1):
        pad = 8
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(w_orig, x + w + pad)
        y2 = min(h_orig, y + h + pad)
        
        crop_rgb = rgb[y1:y2, x1:x2]
        crop_mask = fg_mask[y1:y2, x1:x2]
        
        # Create alpha crop
        alpha_crop = np.zeros((y2 - y1, x2 - x1, 4), dtype=np.uint8)
        alpha_crop[:, :, :3] = crop_rgb
        alpha_crop[:, :, 3] = crop_mask
        
        # Brad detection on crop
        brads = detect_brads(crop_rgb)
        
        piece_label = f"part_{idx:02d}"
        # Heuristic for reference / full-width strips
        if w > w_orig * 0.75:
            piece_label = "reference_strip"
            
        out_filename = f"{piece_label}.png"
        out_file_path = os.path.join(sheet_dest, out_filename)
        Image.fromarray(alpha_crop).save(out_file_path)
        
        pieces.append({
            "id": f"{sheet_name}.{piece_label}",
            "filename": out_filename,
            "rel_path": os.path.relpath(out_file_path, out_dir),
            "bbox": [x1, y1, x2 - x1, y2 - y1],
            "area": int(area),
            "brads_detected": len(brads),
            "brads": brads
        })
        
    # Write sheet catalog
    catalog = {
        "sheet": sheet_name,
        "source_file": os.path.basename(sheet_path),
        "total_pieces": len(pieces),
        "pieces": pieces
    }
    with open(os.path.join(sheet_dest, "catalog.json"), "w") as f:
        json.dump(catalog, f, indent=2)
        
    return catalog

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 slice_kit_sheets.py <path_to_sheet_png_or_directory> [out_dir]")
        sys.exit(1)
        
    target = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(target), "cut")
    
    if os.path.isfile(target):
        print(f"Slicing sheet {target} -> {out_dir}...")
        cat = slice_sheet(target, out_dir)
        print(f"  Sliced {cat['total_pieces']} pieces with brad detection saved to {out_dir}/{cat['sheet']}/")
    elif os.path.isdir(target):
        pngs = glob.glob(os.path.join(target, "**", "*.png"), recursive=True)
        # Exclude already cut directories
        pngs = [p for p in pngs if "/cut/" not in p and "/01_COMPONENTS/" not in p]
        print(f"Slicing {len(pngs)} sheets from directory {target}...")
        for p in pngs:
            try:
                cat = slice_sheet(p, out_dir)
                print(f"  [OK] {cat['sheet']}: {cat['total_pieces']} pieces")
            except Exception as e:
                print(f"  [ERR] {p}: {e}")

if __name__ == "__main__":
    main()
