#!/usr/bin/env python3
"""
SLICE KIT — Extract clean, transparent individual card pieces from an exploded piece kit sheet.
Zero occlusion, zero guessing, 0.0% mutual overlap.
"""
import os, sys, cv2, json
import numpy as np

def slice_kit(img_path, out_dir=None):
    im = cv2.imread(img_path)
    if im is None:
        print(f"Error reading {img_path}")
        return []
    
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(img_path), '..', 'cut', base_name)
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Segment background (off-white studio paper ~230-255)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    mask = (gray < 225)
    
    # Clean morphological closing to ensure cardboard texture holes aren't split
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_clean = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
    
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_clean)
    
    extracted = []
    # Sort by area descending
    valid_indices = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > 2000 and stats[i, cv2.CC_STAT_WIDTH] < 1200]
    valid_indices.sort(key=lambda i: -stats[i, cv2.CC_STAT_AREA])
    
    for rank, idx in enumerate(valid_indices):
        x = stats[idx, cv2.CC_STAT_AREA]
        w = stats[idx, cv2.CC_STAT_WIDTH]
        h = stats[idx, cv2.CC_STAT_HEIGHT]
        left = stats[idx, cv2.CC_STAT_LEFT]
        top = stats[idx, cv2.CC_STAT_TOP]
        
        # Crop region with 4px padding
        pad = 4
        y0 = max(0, top - pad)
        y1 = min(im.shape[0], top + h + pad)
        x0 = max(0, left - pad)
        x1 = min(im.shape[1], left + w + pad)
        
        crop_rgb = im[y0:y1, x0:x1]
        crop_mask = (labels[y0:y1, x0:x1] == idx)
        
        # Soften alpha border
        alpha = (crop_mask * 255).astype(np.uint8)
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0.5)
        
        rgba = np.dstack([crop_rgb, alpha])
        
        piece_file = f"card_{rank+1:02d}_{w}x{h}.png"
        piece_path = os.path.join(out_dir, piece_file)
        cv2.imwrite(piece_path, rgba)
        
        extracted.append({
            'rank': rank + 1,
            'file': piece_file,
            'path': piece_path,
            'size': [int(w), int(h)],
            'area': int(stats[idx, cv2.CC_STAT_AREA]),
            'center': [round(float(centroids[idx][0]), 1), round(float(centroids[idx][1]), 1)]
        })
    
    manifest_path = os.path.join(out_dir, 'manifest.json')
    json.dump({'source': img_path, 'piece_count': len(extracted), 'pieces': extracted}, open(manifest_path, 'w'), indent=2)
    print(f"Extracted {len(extracted)} transparent cards to {out_dir}")
    return extracted

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'shots/arena/poses/ACT-002_SPRINT_KIT.jpg'
    slice_kit(target)
