#!/usr/bin/env python3
"""
SLICE KIT — Extract clean, transparent individual card pieces from:
1. Exploded piece kit sheets (e.g. ACT-002_SPRINT_KIT.jpg)
2. Multi-angle piece sprite sheets (e.g. PIECE_TORSO_5VIEW.jpg, PIECE_HEAD_6VIEW.jpg, PIECE_BOOT_4VIEW.jpg)

Zero occlusion, zero guessing, 0.0% mutual overlap.
"""
import os, sys, cv2, json
import numpy as np

VIEW_NAMES = {
    'PIECE_TORSO_5VIEW': [
        'torso.front', 'torso.threequarter_R', 'torso.profile', 'torso.threequarter_back', 'torso.back'
    ],
    'PIECE_HEAD_6VIEW': [
        'head.front', 'head.threequarter_R', 'head.profile_R', 'head.threequarter_L', 'head.profile_L', 'head.back'
    ],
    'PIECE_BOOT_4VIEW': [
        'boot.flat.profile', 'boot.toe.flexed', 'boot.front', 'boot.back'
    ]
}

def slice_kit(img_path, out_dir=None):
    im = cv2.imread(img_path)
    if im is None:
        print(f"Error reading {img_path}")
        return []
    
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(img_path), '..', 'cut', base_name)
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Segment background (off-white studio paper ~225-255)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    mask = (gray < 220)
    
    # 2. Erase 1px thin grid lines while preserving solid cardboard cards
    opened = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4)))
    
    # 3. Morphological close to bridge internal texture
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(closed)
    
    # Filter major pieces
    min_area = 5000 if 'PIECE_' in base_name else 2000
    valid_indices = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > min_area and stats[i, cv2.CC_STAT_WIDTH] < 1200]
    
    # Sort order
    named_views = VIEW_NAMES.get(base_name, None)
    if named_views:
        # Sort left-to-right
        valid_indices.sort(key=lambda i: stats[i, cv2.CC_STAT_LEFT])
    else:
        # Sort area descending
        valid_indices.sort(key=lambda i: -stats[i, cv2.CC_STAT_AREA])
    
    extracted = []
    for rank, idx in enumerate(valid_indices):
        w = stats[idx, cv2.CC_STAT_WIDTH]
        h = stats[idx, cv2.CC_STAT_HEIGHT]
        left = stats[idx, cv2.CC_STAT_LEFT]
        top = stats[idx, cv2.CC_STAT_TOP]
        
        pad = 6
        y0 = max(0, top - pad)
        y1 = min(im.shape[0], top + h + pad)
        x0 = max(0, left - pad)
        x1 = min(im.shape[1], left + w + pad)
        
        crop_rgb = im[y0:y1, x0:x1]
        crop_mask = (labels[y0:y1, x0:x1] == idx)
        
        # Soften alpha edge
        alpha = (crop_mask * 255).astype(np.uint8)
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0.5)
        
        rgba = np.dstack([crop_rgb, alpha])
        
        if named_views and rank < len(named_views):
            piece_file = f"{named_views[rank]}.png"
        else:
            piece_file = f"card_{rank+1:02d}_{w}x{h}.png"
            
        piece_path = os.path.join(out_dir, piece_file)
        cv2.imwrite(piece_path, rgba)
        
        extracted.append({
            'rank': rank + 1,
            'id': named_views[rank] if (named_views and rank < len(named_views)) else f"card_{rank+1}",
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
    targets = sys.argv[1:] if len(sys.argv) > 1 else [
        'shots/arena/poses/PIECE_TORSO_5VIEW.jpg',
        'shots/arena/poses/PIECE_HEAD_6VIEW.jpg',
        'shots/arena/poses/PIECE_BOOT_4VIEW.jpg'
    ]
    for t in targets:
        slice_kit(t)
