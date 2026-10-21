#!/usr/bin/env python3
"""
CHOP ALL KITS — Slices finished rendered kit sheets into isolated transparent PNG parts
with automatic brass brad and eyelet pivot detection.
"""
import os, sys, cv2, json, glob
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RENDERED_DIR = os.path.join(HERE, 'parts', 'kit3', 'v2', 'rendered')
CUT_BASE = os.path.join(HERE, 'parts', 'kit3', 'v2', 'cut')
os.makedirs(CUT_BASE, exist_ok=True)

# Semantic piece naming hints based on sheet type and aspect/size
SEMANTIC_HINTS = {
    'replacements': [
        'pose.sitting_chair',
        'pose.kneeling_one_knee',
        'pose.lying_back',
        'pose.lying_side',
        'pose.deep_crouch',
        'pose.falling_back',
        'pose.extra'
    ],
    'heads': [
        'head.front',
        'head.threequarter_R',
        'head.profile_R',
        'head.threequarter_back',
        'head.back'
    ],
    'hands': [
        'hand.palm_open_L', 'hand.palm_open_R', 'hand.fist', 'hand.point',
        'hand.grip_bar', 'hand.cup_palm', 'hand.thumbs_up', 'hand.pinch_grip',
        'hand.splayed', 'hand.grip_alt', 'hand.relaxed_curl', 'hand.palm_flat'
    ]
}

def detect_brads_and_eyelets(crop_rgb, crop_mask):
    """Detect circular brass split-pin brad discs and grommet eyelets."""
    hsv = cv2.cvtColor(crop_rgb, cv2.COLOR_BGR2HSV)
    # Brass hue: 12-40, saturation: 60-255, value: 80-255
    brass_mask = cv2.inRange(hsv, np.array([10, 60, 80]), np.array([42, 255, 255])) & (crop_mask > 0)
    
    # Eyelet hole: center is transparent or bright white/paper inside brass ring
    nb, blabels, bstats, bcentroids = cv2.connectedComponentsWithStats(brass_mask)
    brads = []
    for bi in range(1, nb):
        b_area = bstats[bi, cv2.CC_STAT_AREA]
        b_w = bstats[bi, cv2.CC_STAT_WIDTH]
        b_h = bstats[bi, cv2.CC_STAT_HEIGHT]
        aspect = b_w / (b_h + 1e-5)
        if 25 < b_area < 3500 and 0.45 < aspect < 2.2:
            cx = round(float(bcentroids[bi][0]), 1)
            cy = round(float(bcentroids[bi][1]), 1)
            radius = round(float((b_w + b_h) / 4.0), 1)
            brads.append({
                'cx': cx,
                'cy': cy,
                'radius': radius,
                'area': int(b_area)
            })
    return brads

def chop_sheet(sheet_path):
    sheet_name = os.path.splitext(os.path.basename(sheet_path))[0]
    out_dir = os.path.join(CUT_BASE, sheet_name)
    os.makedirs(out_dir, exist_ok=True)
    
    im = cv2.imread(sheet_path)
    if im is None:
        print(f"Error reading {sheet_path}")
        return None

    # Detect white/off-white background
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    mask = (gray < 236).astype(np.uint8)
    
    # Morphological operations to clean pinhole fluting without joining adjacent parts
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(opened)
    
    min_area = 1200
    valid_ids = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > min_area]
    
    # Spatial sorting: top-to-bottom bands, then left-to-right
    # Band size depends on sheet height
    band_size = 280
    valid_ids.sort(key=lambda i: (stats[i, cv2.CC_STAT_TOP] // band_size, stats[i, cv2.CC_STAT_LEFT]))
    
    # Check if we have semantic hints
    sheet_type = None
    for k in SEMANTIC_HINTS.keys():
        if k in sheet_name:
            sheet_type = k
            break
            
    hints = SEMANTIC_HINTS.get(sheet_type, [])
    
    pieces = []
    print(f"Processing {sheet_name}: found {len(valid_ids)} pieces")
    
    for rank, idx in enumerate(valid_ids):
        x = stats[idx, cv2.CC_STAT_LEFT]
        y = stats[idx, cv2.CC_STAT_TOP]
        w = stats[idx, cv2.CC_STAT_WIDTH]
        h = stats[idx, cv2.CC_STAT_HEIGHT]
        
        pad = 6
        y0 = max(0, y - pad)
        y1 = min(im.shape[0], y + h + pad)
        x0 = max(0, x - pad)
        x1 = min(im.shape[1], x + w + pad)
        
        crop_rgb = im[y0:y1, x0:x1]
        crop_mask = (labels[y0:y1, x0:x1] == idx).astype(np.uint8)
        
        # Smooth alpha
        alpha = crop_mask * 255
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0.5)
        rgba = np.dstack([crop_rgb, alpha])
        
        # Detect brads
        brads = detect_brads_and_eyelets(crop_rgb, crop_mask)
        
        # Determine semantic piece name
        if rank < len(hints):
            piece_label = hints[rank]
        else:
            # Classify by shape/aspect
            ar = h / float(w + 1e-5)
            if ar > 2.5:
                piece_label = f"limb_segment_{rank+1}"
            elif ar < 0.6:
                piece_label = f"horizontal_card_{rank+1}"
            elif w > 300 and h > 300:
                piece_label = f"torso_or_body_{rank+1}"
            else:
                piece_label = f"part_{rank+1:02d}"
                
        fname = f"{piece_label}.png"
        fpath = os.path.join(out_dir, fname)
        cv2.imwrite(fpath, rgba)
        
        pieces.append({
            'rank': rank + 1,
            'label': piece_label,
            'file': fname,
            'rel_path': f"arena/parts/kit3/v2/cut/{sheet_name}/{fname}",
            'bbox': [int(x), int(y), int(w), int(h)],
            'area': int(stats[idx, cv2.CC_STAT_AREA]),
            'brads': brads
        })
        
    manifest = {
        'sheet': sheet_name,
        'image': f"arena/parts/kit3/v2/rendered/{os.path.basename(sheet_path)}",
        'piece_count': len(pieces),
        'pieces': pieces
    }
    
    with open(os.path.join(out_dir, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
        
    return manifest

def main():
    sheets = sorted(glob.glob(os.path.join(RENDERED_DIR, '*.png')))
    print(f"Found {len(sheets)} rendered sheets to chop.")
    
    master_catalog = []
    for s in sheets:
        res = chop_sheet(s)
        if res:
            master_catalog.append(res)
            
    master_path = os.path.join(CUT_BASE, 'catalog.json')
    with open(master_path, 'w') as f:
        json.dump(master_catalog, f, indent=2)
    print(f"Successfully generated catalog with {len(master_catalog)} sheets and saved to {master_path}")

if __name__ == '__main__':
    main()
