#!/usr/bin/env python3
"""
build_body_lab.py

Slices and organizes ALL hands, ALL shoes/feet, ALL heads, ALL eyes, ALL noses, ALL mouths,
and ALL accessories across ALL characters and poem kits into a unified, high-res Body Lab library.
Outputs:
- Clean transparent PNGs in shots/arena/parts/body_lab/<category>/
- Master catalog in shots/arena/parts/body_lab/body_lab_catalog.json
"""

import os
import glob
import json
import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_ROOT = os.path.join(ROOT, "shots", "arena", "parts", "body_lab")
os.makedirs(OUT_ROOT, exist_ok=True)

for cat in ["hands", "shoes", "heads", "eyes", "noses", "mouths", "accessories", "torsos"]:
    os.makedirs(os.path.join(OUT_ROOT, cat), exist_ok=True)

catalog = {
    "hands": [],
    "shoes": [],
    "heads": [],
    "eyes": [],
    "noses": [],
    "mouths": [],
    "accessories": [],
    "torsos": []
}

def clean_and_save_crop(img, bbox, out_path, bg_is_white=True):
    x, y, w, h = bbox
    pad = 4
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(img.shape[1], x + w + pad), min(img.shape[0], y + h + pad)
    crop = img[y0:y1, x0:x1]
    
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    alpha = np.zeros(gray.shape, dtype=np.uint8)
    if bg_is_white:
        alpha[gray < 238] = 255
    else:
        alpha[gray > 18] = 255
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
    
    rgba = cv2.cvtColor(crop, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha
    cv2.imwrite(out_path, rgba)

def slice_sheet_contours(sheet_path, min_area=1200):
    img = cv2.imread(sheet_path)
    if img is None:
        return []
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # check background color
    corner = np.mean([gray[0,0], gray[0, w-1], gray[h-1, 0], gray[h-1, w-1]])
    bg_is_white = corner > 128
    
    if bg_is_white:
        _, thresh = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)
    else:
        _, thresh = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
        
    kernel = np.ones((3,3), np.uint8)
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes = []
    for c in contours:
        area = cv2.contourArea(c)
        if area >= min_area:
            x, y, bw, bh = cv2.boundingRect(c)
            # ignore full sheet borders
            if bw > w * 0.95 and bh > h * 0.95:
                continue
            boxes.append((x, y, bw, bh, int(area)))
            
    # sort top-to-bottom, left-to-right
    boxes.sort(key=lambda b: (b[1] // 160, b[0]))
    return img, boxes, bg_is_white

print("1. Indexing existing Weave library parts...")
# 1. Weave Man Library Parts
weave_dir = os.path.join(ROOT, "shots", "weave", "cast", "man", "library")
if os.path.exists(weave_dir):
    # Hands
    for f in sorted(glob.glob(os.path.join(weave_dir, "hand", "*.png"))):
        base = os.path.basename(f)
        rel = os.path.relpath(f, ROOT)
        im = Image.open(f)
        catalog["hands"].append({
            "id": f"weave_hand_{base[:-4]}",
            "name": base[:-4].replace("hand.", "").replace(".", " ").title(),
            "character": "Poet (The Man)",
            "source": "weave/library/hand",
            "category": "hands",
            "path": rel,
            "width": im.width,
            "height": im.height
        })
    # Shoes / Boots
    for f in sorted(glob.glob(os.path.join(weave_dir, "leg", "boot.*.png"))):
        base = os.path.basename(f)
        rel = os.path.relpath(f, ROOT)
        im = Image.open(f)
        catalog["shoes"].append({
            "id": f"weave_boot_{base[:-4]}",
            "name": base[:-4].replace("boot.", "").replace(".", " ").title(),
            "character": "Poet (The Man)",
            "source": "weave/library/leg",
            "category": "shoes",
            "path": rel,
            "width": im.width,
            "height": im.height
        })
    # Walk step legs
    for f in sorted(glob.glob(os.path.join(weave_dir, "leg", "leg.walk.*.png"))):
        base = os.path.basename(f)
        rel = os.path.relpath(f, ROOT)
        im = Image.open(f)
        catalog["shoes"].append({
            "id": f"weave_walk_{base[:-4]}",
            "name": base[:-4].replace("leg.walk.", "Walk Step: ").replace(".", " ").title(),
            "character": "Poet (The Man)",
            "source": "weave/library/leg",
            "category": "shoes",
            "path": rel,
            "width": im.width,
            "height": im.height
        })
    # Heads
    for f in sorted(glob.glob(os.path.join(weave_dir, "head", "*.png"))):
        base = os.path.basename(f)
        rel = os.path.relpath(f, ROOT)
        im = Image.open(f)
        catalog["heads"].append({
            "id": f"weave_head_{base[:-4]}",
            "name": base[:-4].replace("head.", "").replace("intent.", "Intent: ").replace(".", " ").title(),
            "character": "Poet (The Man)",
            "source": "weave/library/head",
            "category": "heads",
            "path": rel,
            "width": im.width,
            "height": im.height
        })
    # Props / Accessories
    for f in sorted(glob.glob(os.path.join(weave_dir, "prop", "prop.sunglasses.*.png"))):
        base = os.path.basename(f)
        rel = os.path.relpath(f, ROOT)
        im = Image.open(f)
        catalog["accessories"].append({
            "id": f"weave_glasses_{base[:-4]}",
            "name": base[:-4].replace("prop.", "").replace(".", " ").title(),
            "character": "Poet (The Man)",
            "source": "weave/library/prop",
            "category": "accessories",
            "path": rel,
            "width": im.width,
            "height": im.height
        })

print(f"  Indexed Weave: {len(catalog['hands'])} hands, {len(catalog['shoes'])} shoes, {len(catalog['heads'])} heads")

print("2. Indexing Kit 3 v2 Poet Tracksuit cut parts...")
# Poet Tracksuit v2 Cut Parts
poet_hands_dir = os.path.join(ROOT, "shots", "arena", "parts", "kit3", "v2", "cut", "poet.red_black_sunglasses.hands")
if os.path.exists(poet_hands_dir):
    for f in sorted(glob.glob(os.path.join(poet_hands_dir, "*.png"))):
        base = os.path.basename(f)
        rel = os.path.relpath(f, ROOT)
        im = Image.open(f)
        catalog["hands"].append({
            "id": f"poet_hand_{base[:-4]}",
            "name": base[:-4].replace("hand.", "").replace("_", " ").title(),
            "character": "Poet (Tracksuit)",
            "source": "poet.red_black_sunglasses.hands",
            "category": "hands",
            "path": rel,
            "width": im.width,
            "height": im.height
        })

poet_feet_dir = os.path.join(ROOT, "shots", "arena", "parts", "kit3", "v2", "cut", "poet.red_black_sunglasses.feet")
if os.path.exists(poet_feet_dir):
    for f in sorted(glob.glob(os.path.join(poet_feet_dir, "*.png"))):
        base = os.path.basename(f)
        rel = os.path.relpath(f, ROOT)
        im = Image.open(f)
        catalog["shoes"].append({
            "id": f"poet_boot_{base[:-4]}",
            "name": f"Tracksuit Boot {base[:-4]}",
            "character": "Poet (Tracksuit)",
            "source": "poet.red_black_sunglasses.feet",
            "category": "shoes",
            "path": rel,
            "width": im.width,
            "height": im.height
        })

poet_heads_dir = os.path.join(ROOT, "shots", "arena", "parts", "kit3", "v2", "cut", "poet.red_black_sunglasses.heads")
if os.path.exists(poet_heads_dir):
    for f in sorted(glob.glob(os.path.join(poet_heads_dir, "*.png"))):
        base = os.path.basename(f)
        rel = os.path.relpath(f, ROOT)
        im = Image.open(f)
        catalog["heads"].append({
            "id": f"poet_head_{base[:-4]}",
            "name": base[:-4].replace("head.", "").replace("_", " ").title(),
            "character": "Poet (Tracksuit)",
            "source": "poet.red_black_sunglasses.heads",
            "category": "heads",
            "path": rel,
            "width": im.width,
            "height": im.height
        })

print("3. Indexing clean modular face components (Eyes, Noses, Mouths, Glasses)...")
# Poet Profile Face Clean
poet_face_dir = os.path.join(ROOT, "shots", "kits", "packs", "poet_tracksuit_v1", "01_COMPONENTS", "profile_face_clean")
if os.path.exists(poet_face_dir):
    for f in sorted(glob.glob(os.path.join(poet_face_dir, "profile_eyes_*.png"))):
        base = os.path.basename(f)
        im = Image.open(f)
        catalog["eyes"].append({
            "id": f"poet_{base[:-4]}",
            "name": f"Poet Profile Eye {base[-6:-4]}",
            "character": "Poet (Tracksuit)",
            "source": "poet.face.profile",
            "category": "eyes",
            "path": os.path.relpath(f, ROOT),
            "width": im.width,
            "height": im.height
        })
    for f in sorted(glob.glob(os.path.join(poet_face_dir, "profile_nose_*.png"))):
        base = os.path.basename(f)
        im = Image.open(f)
        catalog["noses"].append({
            "id": f"poet_{base[:-4]}",
            "name": f"Poet Profile Nose {base[-6:-4]}",
            "character": "Poet (Tracksuit)",
            "source": "poet.face.profile",
            "category": "noses",
            "path": os.path.relpath(f, ROOT),
            "width": im.width,
            "height": im.height
        })
    for f in sorted(glob.glob(os.path.join(poet_face_dir, "profile_mouth_*.png"))):
        base = os.path.basename(f)
        im = Image.open(f)
        catalog["mouths"].append({
            "id": f"poet_{base[:-4]}",
            "name": f"Poet Profile Mouth {base[-6:-4]}",
            "character": "Poet (Tracksuit)",
            "source": "poet.face.profile",
            "category": "mouths",
            "path": os.path.relpath(f, ROOT),
            "width": im.width,
            "height": im.height
        })
    for f in sorted(glob.glob(os.path.join(poet_face_dir, "profile_sunglasses_*.png"))):
        base = os.path.basename(f)
        im = Image.open(f)
        catalog["accessories"].append({
            "id": f"poet_{base[:-4]}",
            "name": f"Poet Sunglasses Variant {base[-6:-4]}",
            "character": "Poet (Tracksuit)",
            "source": "poet.face.profile",
            "category": "accessories",
            "path": os.path.relpath(f, ROOT),
            "width": im.width,
            "height": im.height
        })

# Young Poet Profile Face Clean
yp_face_dir = os.path.join(ROOT, "shots", "kits", "packs", "young_poet_v1", "01_COMPONENTS", "profile_face_clean")
if os.path.exists(yp_face_dir):
    for f in sorted(glob.glob(os.path.join(yp_face_dir, "young_poet_eyes_*.png"))):
        base = os.path.basename(f)
        im = Image.open(f)
        catalog["eyes"].append({
            "id": f"yp_{base[:-4]}",
            "name": f"Young Poet Eye {base[-6:-4]}",
            "character": "Young Poet (Age 6)",
            "source": "young_poet.face.profile",
            "category": "eyes",
            "path": os.path.relpath(f, ROOT),
            "width": im.width,
            "height": im.height
        })
    for f in sorted(glob.glob(os.path.join(yp_face_dir, "young_poet_nose_*.png"))):
        base = os.path.basename(f)
        im = Image.open(f)
        catalog["noses"].append({
            "id": f"yp_{base[:-4]}",
            "name": f"Young Poet Nose {base[-6:-4]}",
            "character": "Young Poet (Age 6)",
            "source": "young_poet.face.profile",
            "category": "noses",
            "path": os.path.relpath(f, ROOT),
            "width": im.width,
            "height": im.height
        })
    for f in sorted(glob.glob(os.path.join(yp_face_dir, "young_poet_mouth_*.png"))):
        base = os.path.basename(f)
        im = Image.open(f)
        catalog["mouths"].append({
            "id": f"yp_{base[:-4]}",
            "name": f"Young Poet Mouth {base[-6:-4]}",
            "character": "Young Poet (Age 6)",
            "source": "young_poet.face.profile",
            "category": "mouths",
            "path": os.path.relpath(f, ROOT),
            "width": im.width,
            "height": im.height
        })
    for f in sorted(glob.glob(os.path.join(yp_face_dir, "young_poet_acc_*.png"))):
        base = os.path.basename(f)
        im = Image.open(f)
        catalog["accessories"].append({
            "id": f"yp_{base[:-4]}",
            "name": f"Young Poet Spectacles/Acc {base[-6:-4]}",
            "character": "Young Poet (Age 6)",
            "source": "young_poet.face.profile",
            "category": "accessories",
            "path": os.path.relpath(f, ROOT),
            "width": im.width,
            "height": im.height
        })

print("4. Butchering and slicing unique sheets across remaining cast...")

def butcher_target_sheet(sheet_rel_path, target_category, character_label, prefix, min_area=1000):
    sheet_abs = os.path.join(ROOT, sheet_rel_path)
    if not os.path.exists(sheet_abs):
        return
    img, boxes, bg_white = slice_sheet_contours(sheet_abs, min_area=min_area)
    if not boxes:
        return
    
    char_slug = character_label.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
    cat_dir = os.path.join(OUT_ROOT, target_category, char_slug)
    os.makedirs(cat_dir, exist_ok=True)
    
    for i, (x, y, bw, bh, area) in enumerate(boxes):
        fname = f"{prefix}_{i+1:02d}.png"
        fpath = os.path.join(cat_dir, fname)
        clean_and_save_crop(img, (x, y, bw, bh), fpath, bg_is_white=bg_white)
        
        catalog[target_category].append({
            "id": f"{char_slug}_{prefix}_{i+1:02d}",
            "name": f"{character_label} {target_category[:-1].title()} {i+1:02d}",
            "character": character_label,
            "source": os.path.basename(sheet_rel_path),
            "category": target_category,
            "path": os.path.relpath(fpath, ROOT),
            "width": bw + 8,
            "height": bh + 8
        })

# Young Poet Hands & Feet & Heads
butcher_target_sheet("shots/kits/packs/poem_02/01_CHARACTER_CORE/young_poet.child_clothes.hands.png", "hands", "Young Poet (Age 6)", "yp_hand")
butcher_target_sheet("shots/kits/packs/poem_02/01_CHARACTER_CORE/young_poet.child_clothes.feet.png", "shoes", "Young Poet (Age 6)", "yp_shoe")
butcher_target_sheet("shots/kits/packs/poem_02/01_CHARACTER_CORE/young_poet.child_clothes.heads.png", "heads", "Young Poet (Age 6)", "yp_head", min_area=10000)

# The Ex Hands & Feet & Heads
butcher_target_sheet("shots/kits/packs/poem_01/01_CHARACTER_CORE/ex.ex_jacket.hands.png", "hands", "The Ex (Bomber Jacket)", "ex_hand")
butcher_target_sheet("shots/kits/packs/poem_01/01_CHARACTER_CORE/ex.ex_jacket.feet.png", "shoes", "The Ex (Bomber Jacket)", "ex_boot")
butcher_target_sheet("shots/kits/packs/poem_01/01_CHARACTER_CORE/ex.ex_jacket.heads.png", "heads", "The Ex (Bomber Jacket)", "ex_head", min_area=10000)

# The Mother Hands & Heads
butcher_target_sheet("shots/kits/packs/poem_09/01_CHARACTER_CORE/woman.09.mother.heads-hands.png", "heads", "The Mother (Teal Dress)", "mother_head", min_area=8000)
butcher_target_sheet("shots/kits/packs/poem_09/01_CHARACTER_CORE/woman.09.mother.heads-hands.png", "hands", "The Mother (Teal Dress)", "mother_hand", min_area=1000)

# The Father Hands & Heads
butcher_target_sheet("shots/kits/packs/poem_09/01_CHARACTER_CORE/parents.09.father_elder.heads-hands.png", "heads", "The Father (Long Coat)", "father_head", min_area=8000)
butcher_target_sheet("shots/kits/packs/poem_09/01_CHARACTER_CORE/parents.09.father_elder.heads-hands.png", "hands", "The Father (Long Coat)", "father_hand", min_area=1000)

# Ghost Child Faces & Hands
butcher_target_sheet("shots/kits/packs/poem_02/01_CHARACTER_CORE/ghost_child.02.faces-hands.png", "heads", "Ghost Child (Age 7)", "ghost_head", min_area=8000)
butcher_target_sheet("shots/kits/packs/poem_02/01_CHARACTER_CORE/ghost_child.02.faces-hands.png", "hands", "Ghost Child (Age 7)", "ghost_hand", min_area=1000)

# Shared Noses across Cast
butcher_target_sheet("shots/kits/packs/poem_08/01_CHARACTER_CORE/08.cast.shared.noses.png", "noses", "Cast Shared Features", "shared_nose", min_area=800)

# DJ Cyber & Guest Accessories (Caps, Noses, Headphones)
butcher_target_sheet("shots/kits/packs/poem_07/01_CHARACTER_CORE/party.07.dj-guest.cap-noses-headphones.png", "accessories", "DJ Cyber & Club", "dj_acc", min_area=2000)

# Party Feet & Heads
butcher_target_sheet("shots/kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.face-feet.male.png", "shoes", "Party Guest (Male)", "party_male_shoe", min_area=2000)
butcher_target_sheet("shots/kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.face-feet.female.png", "shoes", "Party Guest (Female)", "party_female_shoe", min_area=2000)
butcher_target_sheet("shots/kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.hands.png", "hands", "Party Guests", "party_hand", min_area=1000)
butcher_target_sheet("shots/kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.heads.png", "heads", "Party Guests", "party_head", min_area=8000)

# Atlantis Crowd Heads
butcher_target_sheet("shots/kits/packs/poem_06/01_CHARACTER_CORE/atlantis.06.crowd-head-variants.png", "heads", "Atlantis Ancestors", "atlantis_head", min_area=6000)

# Save Master Catalog
catalog_path = os.path.join(OUT_ROOT, "body_lab_catalog.json")
with open(catalog_path, "w") as f:
    json.dump(catalog, f, indent=2)

print("\n=== BODY LAB MASTER CATALOGUE BUILT ===")
total_parts = sum(len(v) for v in catalog.values())
print(f"Total Isolated Body Parts: {total_parts}")
for k, v in catalog.items():
    print(f"  • {k.upper():12s}: {len(v)} parts")
print(f"Catalog saved to: {catalog_path}")
