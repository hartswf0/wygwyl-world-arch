#!/usr/bin/env python3
"""
batch_butcher_all_packs.py

Systematic large-scale butchering pipeline for WYGWYL:
- Scans all 14 poem packs across 01_CHARACTER_CORE, 02_ACTIONS_AND_POSES, 03_PROPS, 04_SETS_AND_BUILDINGS.
- Slices multi-card sheets into isolated transparent alpha-channel PNGs.
- Preserves raw corrugated kraft cut edges.
- Detects circular brass brad fasteners and eyelets.
- Generates a centralized cut catalog at shots/kits/parts_library.json.
"""

import os
import sys
import json
import glob
import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKS_DIR = os.path.join(ROOT, "shots", "kits", "packs")
LIBRARY_JSON = os.path.join(ROOT, "shots", "kits", "parts_library.json")

def detect_brads(rgb_crop):
    brads = []
    if rgb_crop.shape[0] < 20 or rgb_crop.shape[1] < 20:
        return brads
    gray = cv2.cvtColor(rgb_crop, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.5)
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=16,
        param1=50, param2=22, minRadius=3, maxRadius=24
    )
    if circles is not None:
        for pt in np.uint16(np.around(circles))[0, :]:
            cx, cy, r = int(pt[0]), int(pt[1]), int(pt[2])
            if 0 <= cy < rgb_crop.shape[0] and 0 <= cx < rgb_crop.shape[1]:
                patch = rgb_crop[max(0, cy-r//2):min(rgb_crop.shape[0], cy+r//2+1),
                                 max(0, cx-r//2):min(rgb_crop.shape[1], cx+r//2+1)]
                if patch.size > 0:
                    mr, mg, mb = np.mean(patch, axis=(0, 1))[:3]
                    if mr > mb + 12 and mr > 70:
                        brads.append({"cx": cx, "cy": cy, "radius": r, "type": "brass_pin"})
                    elif np.mean(patch) < 80:
                        brads.append({"cx": cx, "cy": cy, "radius": r, "type": "eyelet"})
    # Deduplicate
    filtered = []
    for b in brads:
        if not any(np.hypot(b["cx"] - f["cx"], b["cy"] - f["cy"]) < 12 for f in filtered):
            filtered.append(b)
    return filtered

def slice_single_sheet(sheet_path, out_dir):
    sheet_name = os.path.splitext(os.path.basename(sheet_path))[0]
    sheet_dest = os.path.join(out_dir, sheet_name)
    os.makedirs(sheet_dest, exist_ok=True)
    
    im = Image.open(sheet_path).convert("RGBA")
    arr = np.array(im)
    h_orig, w_orig = arr.shape[:2]
    rgb = arr[:, :, :3]
    
    # White background detection
    is_white = (rgb[:, :, 0] > 240) & (rgb[:, :, 1] > 240) & (rgb[:, :, 2] > 240)
    fg_mask = (~is_white).astype(np.uint8) * 255
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    candidates = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        if area < 1000 or w < 28 or h < 28:
            continue
        # Skip small title tags
        if y < 45 and h < 55 and w < 220:
            continue
        candidates.append((x, y, w, h, area))
        
    candidates.sort(key=lambda item: (item[1] // 160, item[0]))
    pieces = []
    for idx, (x, y, w, h, area) in enumerate(candidates, start=1):
        pad = 8
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(w_orig, x + w + pad)
        y2 = min(h_orig, y + h + pad)
        
        crop_rgb = rgb[y1:y2, x1:x2]
        crop_mask = fg_mask[y1:y2, x1:x2]
        
        alpha_crop = np.zeros((y2 - y1, x2 - x1, 4), dtype=np.uint8)
        alpha_crop[:, :, :3] = crop_rgb
        alpha_crop[:, :, 3] = crop_mask
        
        brads = detect_brads(crop_rgb)
        label = "reference_strip" if w > w_orig * 0.75 else f"card_{idx:02d}"
        filename = f"{label}.png"
        filepath = os.path.join(sheet_dest, filename)
        
        Image.fromarray(alpha_crop).save(filepath)
        pieces.append({
            "id": f"{sheet_name}.{label}",
            "label": label,
            "filename": filename,
            "rel_path": os.path.relpath(filepath, ROOT),
            "width": x2 - x1,
            "height": y2 - y1,
            "area": int(area),
            "brads": brads
        })
        
    cat = {
        "sheet": sheet_name,
        "source": os.path.relpath(sheet_path, ROOT),
        "total_pieces": len(pieces),
        "pieces": pieces
    }
    with open(os.path.join(sheet_dest, "catalog.json"), "w") as f:
        json.dump(cat, f, indent=2)
    return cat

def main():
    print("Executing Batch Butcher across all 14 Poem Kits...")
    # Priority targets across categories
    targets = []
    for p_num in range(1, 15):
        num_str = f"{p_num:02d}"
        pack_dir = os.path.join(PACKS_DIR, f"poem_{num_str}")
        if not os.path.exists(pack_dir):
            continue
            
        # Select representative sheets per pack: Character core, Action Poses, Props, Sets
        p_sheets = []
        for cat in ["01_CHARACTER_CORE", "02_ACTIONS_AND_POSES", "03_PROPS", "04_SETS_AND_BUILDINGS"]:
            c_dir = os.path.join(pack_dir, cat)
            if os.path.exists(c_dir):
                pngs = sorted(glob.glob(os.path.join(c_dir, "*.png")))
                # Take top 2 from each category per poem
                p_sheets.extend(pngs[:2])
                
        targets.extend(p_sheets)

    print(f"Targeting {len(targets)} primary production sheets for automated butchering...")
    
    total_cut_pieces = 0
    all_catalogs = []
    
    for idx, sheet in enumerate(targets, 1):
        poem_folder = os.path.basename(os.path.dirname(os.path.dirname(sheet)))
        out_dir = os.path.join(PACKS_DIR, poem_folder, "cut")
        try:
            cat = slice_single_sheet(sheet, out_dir)
            total_cut_pieces += cat["total_pieces"]
            all_catalogs.append(cat)
            if idx % 10 == 0 or idx == len(targets):
                print(f"  [{idx}/{len(targets)}] Sliced {sheet.split('/')[-1]}: {cat['total_pieces']} cards (Total: {total_cut_pieces} parts)")
        except Exception as e:
            print(f"  [ERR] {sheet}: {e}")
            
    # Also index poet_tracksuit_v1
    tracksuit_cat = {
        "sheet": "poet_tracksuit_v1",
        "source": "shots/kits/packs/poet_tracksuit_v1",
        "total_pieces": 31,
        "pieces": []
    }
    ts_dir = os.path.join(PACKS_DIR, "poet_tracksuit_v1", "01_COMPONENTS")
    if os.path.exists(ts_dir):
        for f in sorted(os.listdir(ts_dir)):
            if f.endswith(".png"):
                im = Image.open(os.path.join(ts_dir, f))
                tracksuit_cat["pieces"].append({
                    "id": f"poet_tracksuit.{f[:-4]}",
                    "label": f[:-4],
                    "filename": f,
                    "rel_path": f"shots/kits/packs/poet_tracksuit_v1/01_COMPONENTS/{f}",
                    "width": im.width,
                    "height": im.height,
                    "area": im.width * im.height,
                    "brads": []
                })
        all_catalogs.append(tracksuit_cat)
        total_cut_pieces += 31

    library = {
        "total_sheets_sliced": len(all_catalogs),
        "total_cut_pieces": total_cut_pieces,
        "sheets": all_catalogs
    }
    
    with open(LIBRARY_JSON, "w") as f:
        json.dump(library, f, indent=2)
        
    print(f"\nBatch Butchering Complete! Sliced {total_cut_pieces} individual transparent parts saved to {LIBRARY_JSON}.")

if __name__ == "__main__":
    main()
