#!/usr/bin/env python3
"""
CHOP LIBRARY — Automated Sheet Chopper & Code Rotoscoper for Cut-Out Puppet Parts

Chops the 18 master character sheets in `shots/weave/cast/man/sheets/` into
clean transparent PNG cards with softened alpha borders, detects brass brads /
pivot eyelets, and builds a comprehensive unified catalog:
`shots/weave/cast/man/library/` and `shots/weave/cast/man/library_manifest.json`.
"""
import os, glob, json
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS_DIR = os.path.join(HERE, '..', 'weave', 'cast', 'man', 'sheets')
LIB_DIR = os.path.join(HERE, '..', 'weave', 'cast', 'man', 'library')
os.makedirs(LIB_DIR, exist_ok=True)

# Semantic mapping of piece labels based on sheet naming and position
SHEET_SCHEMAS = {
    'heads.jpg': {
        'category': 'head',
        'labels': [
            'head.profile_R.neutral', 'head.threequarter_R.neutral', 'head.front.neutral',
            'head.threequarter_L.neutral', 'head.profile_L.neutral', 'head.back.neutral',
            'head.sunglasses.smile', 'head.closed_eyes', 'head.look_up',
            'head.look_down', 'head.sunglasses_shades', 'head.speaking'
        ]
    },
    'heads_front.jpg': {
        'category': 'head',
        'labels': [
            'head.front.neutral', 'head.front.big_smile', 'head.front.small_smile',
            'head.front.closed', 'head.front.look_up', 'head.front.look_down',
            'head.front.sunglasses', 'head.front.sunglasses_smile', 'head.front.speaking',
            'head.front.singing', 'head.front.surprised', 'head.front.frowning'
        ]
    },
    'heads_intent_effort.jpg': {
        'category': 'head',
        'labels': [
            'head.effort.strain', 'head.effort.pain', 'head.effort.panting',
            'head.effort.tired', 'head.effort.afraid', 'head.effort.surprised',
            'head.intent.reluctant', 'head.intent.embarrassed', 'head.intent.forced_grin',
            'head.intent.recognition', 'head.intent.listening', 'head.intent.sad'
        ]
    },
    'heads_effort_threequarter.jpg': {
        'category': 'head',
        'labels': [
            'head.3q.strain', 'head.3q.pain', 'head.3q.panting',
            'head.3q.tired', 'head.3q.afraid', 'head.3q.surprised',
            'head.3q.reluctant', 'head.3q.embarrassed', 'head.3q.forced_grin',
            'head.3q.recognition', 'head.3q.listening', 'head.3q.sad'
        ]
    },
    'hands.jpg': {
        'category': 'hand',
        'labels': [
            'hand.open.flat', 'hand.palm.down', 'hand.palm.up', 'hand.loose.fist',
            'hand.fist.tight', 'hand.pinch', 'hand.point', 'hand.thumbs_up',
            'hand.hold.sunglasses', 'hand.adjust.sunglasses', 'hand.knob.grip',
            'hand.notebook', 'hand.pen', 'hand.wave', 'hand.curled'
        ]
    },
    'hands_2.jpg': {
        'category': 'hand',
        'labels': [
            'hand.front.hanging', 'hand.curled.side', 'hand.edge.on', 'hand.back.facing',
            'hand.palm.out', 'hand.peace', 'hand.cupped.ear', 'hand.microphone',
            'hand.phone', 'hand.record', 'hand.turntable', 'hand.pocket'
        ]
    },
    'arms_hands_contact.jpg': {
        'category': 'contact',
        'labels': [
            'arm.foreshortened.uarm', 'arm.flared.elbow', 'arm.overhead.reach',
            'grip.bar.handle', 'grip.edge.hook', 'grip.flat.palm_brace',
            'grip.spread.catch', 'grip.ball.pinch', 'grip.cupped.pair',
            'contact.box.lift', 'contact.shoulder.touch', 'contact.clasped.hands'
        ]
    },
    'legs_walk.jpg': {
        'category': 'leg',
        'labels': [
            'leg.walk.flat', 'leg.walk.toe_off', 'leg.walk.passing', 'leg.walk.heel_strike',
            'leg.walk.step', 'leg.bent.knee', 'leg.thigh.long', 'leg.thigh.mid',
            'leg.trouser.full', 'boot.loose.1', 'boot.loose.2', 'leg.front.facing'
        ]
    },
    'legs_segmented.jpg': {
        'category': 'leg',
        'labels': [
            'leg.thigh.segmented_1', 'leg.thigh.segmented_2', 'leg.thigh.short_1', 'leg.thigh.short_2',
            'leg.shin.bunched_knee', 'leg.shin.straight', 'boot.chelsea.flat', 'boot.chelsea.toe',
            'boot.chelsea.pointed', 'boot.chelsea.front', 'pose.crouch.study', 'pose.kneel.study'
        ]
    },
    'legs_run_stairs.jpg': {
        'category': 'leg',
        'labels': [
            'leg.run.stride', 'leg.run.push_off', 'leg.stair.step_up', 'leg.stair.step_down',
            'leg.jump.tuck_1', 'leg.jump.tuck_2', 'leg.ground.recovery_1', 'leg.ground.recovery_2'
        ]
    },
    'props.jpg': {
        'category': 'prop',
        'labels': [
            'prop.sunglasses.front', 'prop.sunglasses.profile', 'prop.sunglasses.folded',
            'prop.notebook.closed', 'prop.notebook.open', 'prop.pen', 'prop.phone',
            'prop.microphone', 'prop.record', 'prop.turntable', 'prop.headphones',
            'prop.lamp', 'prop.folded_note', 'prop.bench'
        ]
    },
    'set_props.jpg': {
        'category': 'prop',
        'labels': [
            'prop.railing.1', 'prop.railing.2', 'prop.stairs.handrail', 'prop.door.leaf',
            'prop.door.frame', 'prop.car_door', 'prop.box.crate', 'prop.table',
            'prop.cups', 'prop.baseball', 'prop.basketball', 'prop.soccer_ball',
            'prop.racket', 'prop.street_sign'
        ]
    }
}

def detect_brad_in_crop(rgba):
    """Locate the golden brass brad or eyelet inside an extracted transparent card."""
    h, w = rgba.shape[:2]
    alpha = rgba[..., 3]
    b, g, r = rgba[..., 0], rgba[..., 1], rgba[..., 2]
    
    # Golden brass color signature
    gold = (alpha > 180) & (r > 130) & (g > 105) & (b < 130)
    gold_clean = cv2.morphologyEx(gold.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(gold_clean)
    
    brads = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if 8 <= area <= 600:
            cx, cy = centroids[i]
            brads.append({'center': [round(float(cx), 1), round(float(cy), 1)], 'area': int(area)})
            
    # Sort brads by area descending
    brads.sort(key=lambda b: -b['area'])
    return brads

def chop_sheet(sheet_path):
    im = cv2.imread(sheet_path)
    if im is None:
        return []
    
    fname = os.path.basename(sheet_path)
    schema = SHEET_SCHEMAS.get(fname, {'category': 'misc', 'labels': []})
    cat = schema['category']
    labels = schema['labels']
    
    # Segment off-white paper background
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    mask = (gray < 220).astype(np.uint8)
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4)))
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    
    n, labels_im, stats, centroids = cv2.connectedComponentsWithStats(closed)
    
    min_area = 1200
    valid_indices = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > min_area and stats[i, cv2.CC_STAT_WIDTH] < 1300]
    
    # Sort by reading order: row-major (top-to-bottom, left-to-right)
    def reading_order(idx):
        top = stats[idx, cv2.CC_STAT_TOP]
        left = stats[idx, cv2.CC_STAT_LEFT]
        row = top // 220 # group by rows
        return (row, left)
        
    valid_indices.sort(key=reading_order)
    
    extracted_cards = []
    sheet_base = os.path.splitext(fname)[0]
    sub_dir = os.path.join(LIB_DIR, cat)
    os.makedirs(sub_dir, exist_ok=True)
    
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
        crop_mask = (labels_im[y0:y1, x0:x1] == idx)
        
        # Soften alpha border
        alpha = (crop_mask * 255).astype(np.uint8)
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0.5)
        rgba = np.dstack([crop_rgb, alpha])
        
        # Semantic ID
        if rank < len(labels):
            piece_id = labels[rank]
        else:
            piece_id = f"{sheet_base}_{rank+1:02d}"
            
        piece_fn = f"{piece_id}.png"
        piece_path = os.path.join(sub_dir, piece_fn)
        rel_path = os.path.join('cast', 'man', 'library', cat, piece_fn)
        cv2.imwrite(piece_path, rgba)
        
        # Detect brads
        brads = detect_brad_in_crop(rgba)
        
        # Primary pivot
        if brads:
            primary_pivot = brads[0]['center']
        else:
            # Default to top center or base
            primary_pivot = [round(rgba.shape[1] / 2.0, 1), round(rgba.shape[0] * 0.1, 1)]
            
        extracted_cards.append({
            'id': piece_id,
            'category': cat,
            'source_sheet': fname,
            'file': rel_path,
            'size': [int(rgba.shape[1]), int(rgba.shape[0])],
            'pivot': primary_pivot,
            'brads': brads
        })
        
    return extracted_cards

def main():
    sheets = sorted(glob.glob(os.path.join(SHEETS_DIR, '*.jpg')))
    total_extracted = 0
    all_pieces = {}
    
    print(f"Chopping {len(sheets)} master library sheets...")
    for s in sheets:
        cards = chop_sheet(s)
        total_extracted += len(cards)
        for c in cards:
            all_pieces[c['id']] = c
        print(f"  {os.path.basename(s):30s} -> extracted {len(cards):2d} transparent cards")
        
    catalog = {
        'about': 'The Man (Boone) Complete Modular Cut-Out Library',
        'total_pieces': total_extracted,
        'categories': list(set(p['category'] for p in all_pieces.values())),
        'pieces': all_pieces
    }
    
    out_manifest = os.path.join(HERE, '..', 'weave', 'cast', 'man', 'library_manifest.json')
    with open(out_manifest, 'w') as f:
        json.dump(catalog, f, indent=2)
        
    print(f"\nSuccessfully chopped and registered {total_extracted} modular parts into {LIB_DIR}")
    print(f"Manifest written to {out_manifest}")

if __name__ == '__main__':
    main()
