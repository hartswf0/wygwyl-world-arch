#!/usr/bin/env python3
"""
build_clip_embeddings.py

OpenCLIP (ViT-B-32, laion2b_s34b_b79k) Visual Embedding Indexer & Category Purifier
for the WYGWYL Anatomical Body Lab.

1. Loads `shots/arena/parts/body_lab/body_lab_unified.json` and scans
   `shots/arena/parts/kit3/release_v2/wygwyl_atlas_manifest.json` to recover any
   missed facial features (eyes, brows, mouths on head sheets) and garment panels.
2. Encodes all part images on Apple Silicon `mps` GPU into L2-normalized 512-D
   CLIP visual embeddings.
3. Encodes 28 fine-grained anatomical concept prompts across all 8 categories +
   non-anatomy filters.
4. Purifies `body_lab_unified.json` using sheet geometry + CLIP visual scores:
   - Fixes `.body.png` sheets (`08.cast.angel.body`, `08.cast.club_dress.body`,
     `family.12.brother_1.body`, `atlantis.06.citizen_1.body`, `woman.13.body`, etc.)
     so seat covers, lower robe panels, hip bridges, and shorts go to `torsos_pelvis`,
     arm/leg capsules go to `limbs`, and ONLY true footwear/bare feet go to `shoes_feet`.
   - Fixes `.face-feet` sheets so red lip mouths and noses go to `mouths_noses`
     and only bottom-right/bottom-row shoes go to `shoes_feet`.
   - Fixes `.faces-hands` and `.heads-hands` sheets so eyebrows, mouths, and earrings
     are not misclassified as `hands`, and removes full-figure reference composites.
   - Fixes `.master`, `.action.*`, and `.replacements.*` sheets using CLIP visual
     classification when heuristic size boxes misclassified heads, sunglasses, hands,
     or pelvises as `shoes_feet` or `hands`.
5. Computes for every part:
   - `clip_tag`: fine-grained visual sub-type within its category
   - `clip_confidence`: float CLIP cosine similarity score
   - `similar_ids`: top 8 visually most similar part IDs (512-D cosine similarity)
   - `umap_xy`: 2D embedding coordinates `[x, y]` in `[0, 1]`
6. Writes purified `shots/arena/parts/body_lab/body_lab_unified.json` and
   32-D PCA-compressed `shots/arena/parts/body_lab/clip_part_index.json` with
   110+ pre-encoded CLIP keyword vectors for instant browser-side semantic search.
"""

import os
import re
import json
import time
import numpy as np
import torch
import open_clip
from PIL import Image

SHOTS_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots"
UNIFIED_PATH = os.path.join(SHOTS_ROOT, "arena/parts/body_lab/body_lab_unified.json")
ATLAS_MANIFEST_PATH = os.path.join(SHOTS_ROOT, "arena/parts/kit3/release_v2/wygwyl_atlas_manifest.json")
CLIP_INDEX_OUT_PATH = os.path.join(SHOTS_ROOT, "arena/parts/body_lab/clip_part_index.json")

CATEGORIES = [
    "hands",
    "shoes_feet",
    "heads",
    "eyes_brows",
    "mouths_noses",
    "sunglasses_acc",
    "torsos_pelvis",
    "limbs",
]

CHARACTER_GROUPS = [
    "Poet",
    "EX",
    "Woman / Muse",
    "Vintage Party",
    "Child / Ghost",
    "Family / Ancestors",
    "DJ / Club / Atlantis",
]

VIEW_ANGLES = ["front", "profile", "threequarter", "back"]

# 28 fine-grained anatomical & non-anatomical CLIP text concepts
CONCEPT_BANK = [
    # shoes_feet (4)
    ("boot_chelsea",      "Boot / Chelsea",      "shoes_feet",     "a single boot or chelsea boot footwear cutout"),
    ("sneaker",           "Sneaker",             "shoes_feet",     "a single sneaker, trainer, or athletic shoe cutout"),
    ("dress_shoe_heel",   "Dress Shoe / Heel",   "shoes_feet",     "a single dress shoe, loafer, flat, or high heel shoe cutout"),
    ("bare_foot",         "Bare Foot",           "shoes_feet",     "a single bare human foot with toes cutout"),
    # hands (4)
    ("hand_open_palm",    "Open Palm",           "hands",          "a single open human hand with palm and fingers spread cutout"),
    ("hand_fist_grip",    "Fist / Grip",         "hands",          "a single closed fist or gripping human hand cutout"),
    ("hand_pointing",     "Pointing Hand",       "hands",          "a single pointing human hand or gesturing fingers cutout"),
    ("hand_holding_prop", "Holding Prop",        "hands",          "a human hand holding a small object or prop cutout"),
    # heads (5)
    ("head_front",        "Head Front",          "heads",          "a human head and face looking forward portrait cutout"),
    ("head_profile",      "Head Profile",        "heads",          "a human head in side profile view cutout"),
    ("head_threequarter", "Head 3/4",            "heads",          "a human head in three-quarter view cutout"),
    ("head_back",         "Back of Head",        "heads",          "the back of a human head showing hair cutout"),
    ("head_blank_base",   "Blank Head Base",     "heads",          "a blank faceless human head base with ears and neck cutout"),
    # eyes_brows (3)
    ("eyes_open",         "Eyes Open",           "eyes_brows",     "a pair of human eyes and pupils cutout"),
    ("eyes_closed",       "Eyes Closed",         "eyes_brows",     "closed sleeping or blinking eyelids cutout"),
    ("eyebrows",          "Eyebrows",            "eyes_brows",     "a pair of eyebrows strip cutout"),
    # mouths_noses (2)
    ("mouth_lips",        "Mouth / Lips",        "mouths_noses",   "a human mouth, lips, smile, or open speaking mouth cutout"),
    ("nose",              "Nose",                "mouths_noses",   "a human nose cutout"),
    # sunglasses_acc (2)
    ("sunglasses",        "Sunglasses",          "sunglasses_acc", "sunglasses or eyeglasses eyewear cutout"),
    ("headgear_acc",      "Headgear",            "sunglasses_acc", "a hat, cap, headphones, or headgear accessory cutout"),
    # torsos_pelvis (3)
    ("torso_jacket",      "Torso / Jacket",      "torsos_pelvis",  "a jacket, shirt, vest, bodice, or upper body torso cutout"),
    ("dress_robe_panel",  "Dress / Robe Panel",  "torsos_pelvis",  "a dress, skirt, lower robe panel, or pleated garment panel cutout"),
    ("pelvis_hip_bridge", "Pelvis / Hip Bridge", "torsos_pelvis",  "shorts, pelvis cover, seat cover, or triangular hip bridge with grommet holes"),
    # limbs (2)
    ("arm_leg_segment",   "Arm / Leg Segment",   "limbs",          "a single elongated arm sleeve or pant leg limb segment with pivot holes at ends"),
    ("bent_limb_action",  "Bent Action Limb",    "limbs",          "a bent arm or leg limb segment cutout for paper puppet"),
    # non_anatomy (3)
    ("full_figure",       "Full Figure",         "non_anatomy",    "a full standing or walking human figure from head to toe"),
    ("building_room",     "Building / Room",     "non_anatomy",    "a building, wall, window, door, furniture, or room interior"),
    ("prop_banner",       "Prop / Banner",       "non_anatomy",    "a vehicle, car, tree, cloud, moon, or text banner"),
]

SEARCH_KEYWORDS = [
    "boot", "chelsea", "shoe", "sneaker", "trainer", "heel", "loafer", "flat", "sandal", "slipper",
    "foot", "feet", "bare", "toe", "toes", "sole", "lifted", "step",
    "hand", "hands", "palm", "open", "fist", "grip", "point", "pointing", "finger", "fingers",
    "wave", "gesture", "hold", "holding", "prop", "cupped", "relaxed", "waltz", "pocket",
    "head", "face", "profile", "side", "front", "back", "threequarter", "blank", "faceless",
    "beard", "mustache", "hair", "braids", "afro", "curls", "waves", "bald",
    "child", "boy", "girl", "ghost", "mother", "father", "elder", "ancestor", "woman", "muse",
    "poet", "ex", "dj", "angel", "guest", "citizen", "gatekeeper", "traveler", "watcher",
    "eye", "eyes", "pupil", "closed", "blink", "sleep", "half", "wide", "glance",
    "brow", "brows", "eyebrow", "eyebrows", "frown", "raised", "worried", "angry",
    "mouth", "lips", "smile", "grin", "laugh", "speak", "sing", "open", "teeth", "tongue",
    "nose", "nostril",
    "sunglasses", "glasses", "shades", "eyewear", "hat", "cap", "baseball", "headphones",
    "earring", "hoop", "wings", "feather", "necklace", "pearls", "rosary", "jewelry", "vape",
    "jacket", "tracksuit", "bomber", "shirt", "tshirt", "vest", "bodice", "hoodie", "suit", "coat",
    "dress", "robe", "skirt", "gown", "panel", "overlay", "shorts", "jeans", "denim",
    "hip", "bridge", "pelvis", "seat", "butt", "waist",
    "arm", "upper", "forearm", "sleeve", "cuff", "wrist", "elbow", "shoulder",
    "leg", "thigh", "shin", "calf", "pant", "ankle", "knee",
    "red", "black", "white", "gold", "blue", "teal", "indigo", "silver", "brown", "tan", "grey", "yellow", "pink", "green", "purple",
]


def to_shots_rel(path_str):
    if not path_str:
        return ""
    p = path_str.strip().lstrip("/")
    if p.startswith("shots/"):
        p = p[len("shots/"):]
    return p


def compute_normalized_scale(category, width, height, char_group="Poet", name="", visible_bbox=None):
    nl = (name or "").lower()
    is_child = (char_group == "Child / Ghost")
    child_mult = 0.74 if is_child else 1.0

    if category == "torsos_pelvis":
        if any(k in nl for k in ["waist link", "waist_link"]):
            target_px = 68.0
        elif any(k in nl for k in ["hip bridge", "hip_bridge", "pelvis", "rear seat", "rear_seat", "butt", "seat", "shorts"]):
            target_px = 115.0 * child_mult
        elif any(k in nl for k in ["overlay", "skirt", "gown", "coat tail", "robe"]):
            target_px = 210.0 * child_mult
        else:
            target_px = 240.0 * child_mult
    elif category == "limbs":
        if any(k in nl for k in ["thigh", "shin", "leg", "calf"]):
            target_px = 192.0 * child_mult
        else:
            target_px = 160.0 * child_mult
    elif category == "heads":
        target_px = 152.0 * child_mult
    elif category == "shoes_feet":
        if any(k in nl for k in ["walk step", "leg.walk", "leg.run", "leg.stair", "leg.jump", "leg.ground"]):
            target_px = 220.0 * child_mult
        else:
            target_px = 92.0 * child_mult
    elif category == "hands":
        if any(k in nl for k in ["paired", "waltz", "clasped", "hug"]):
            target_px = 105.0 * child_mult
        else:
            target_px = 68.0 * child_mult
    elif category == "sunglasses_acc":
        if any(k in nl for k in ["cap", "hat", "headphone", "crown", "headpiece", "helmet"]):
            target_px = 118.0 * child_mult
        elif any(k in nl for k in ["wing"]):
            target_px = 250.0 * child_mult
        else:
            target_px = 94.0 * child_mult
    elif category == "eyes_brows":
        if "profile" in nl or "single" in nl or (width < height * 1.35):
            target_px = 42.0 * child_mult
        else:
            target_px = 78.0 * child_mult
    elif category == "mouths_noses":
        if "nose" in nl:
            target_px = 42.0 * child_mult
        elif "profile" in nl:
            target_px = 48.0 * child_mult
        else:
            target_px = 58.0 * child_mult
    else:
        target_px = 100.0 * child_mult

    eff_w, eff_h = float(max(1, width)), float(max(1, height))
    if visible_bbox and len(visible_bbox) == 4:
        vx0, vy0, vx1, vy1 = visible_bbox
        vw = vx1 - vx0 if vx1 > vx0 else vx1
        vh = vy1 - vy0 if vy1 > vy0 else vy1
        if vw > 20 and vh > 20:
            eff_w, eff_h = float(vw), float(vh)

    major_vis = max(eff_w, eff_h)
    return round(target_px / major_vis, 4)


def recover_missed_atlas_parts(unified_parts, atlas_manifest):
    """
    Scan `wygwyl_atlas_manifest.json` for facial features (eyes, brows, mouths on
    `atlantis.06.gatekeeper-elder.heads`, `family.10.watcher-head-turns`,
    `ancestors.05.identities.*`, `*.heads-hands`) and garment overlays (`ancestor_elder_white_silver.body__p14`)
    that were previously skipped by heuristic size filters.
    """
    seen_files = {p["file"] for p in unified_parts}
    seen_ids = {p["id"] for p in unified_parts}
    added = 0

    for asset in atlas_manifest.get("assets", []):
        sid = asset["id"]
        sub = asset.get("subfolder", "")
        if sub not in ("01_CHARACTER_CORE", "02_ACTIONS_AND_POSES"):
            continue
        sheet_rel = to_shots_rel(asset.get("sheet_file", f"kits/packs/poem_01/{sub}/{sid}.png"))

        for part in asset.get("parts", []):
            f_rel = to_shots_rel(part.get("file", ""))
            if not f_rel or f_rel in seen_files:
                continue
            abs_p = os.path.join(SHOTS_ROOT, f_rel)
            if not os.path.exists(abs_p):
                continue

            p_idx = part["part_index"]
            w, h = int(part["width"]), int(part["height"])
            bx, by, bw, bh = part.get("bbox_sheet", [0, 0, w, h])
            role = part.get("role", "working_part")

            rec = None
            if sid == "atlantis.06.gatekeeper-elder.heads" and 400 <= by <= 950:
                who = "Gatekeeper" if bx < 500 else "Elder 1"
                expr = "Calm" if by < 580 else ("Awe" if by < 760 else "Joy")
                if bw >= 95 and bh >= 60:
                    rec = ("mouths_noses", f"Atlantis {who} · {expr} Bearded Mouth {p_idx:02d}", "front", "DJ / Club / Atlantis", [6])
                elif bh <= 48 and (bw / max(1, bh)) >= 1.55:
                    rec = ("eyes_brows", f"Atlantis {who} · {expr} Eyebrow {p_idx:02d}", "front", "DJ / Club / Atlantis", [6])
                else:
                    rec = ("eyes_brows", f"Atlantis {who} · {expr} Eye {p_idx:02d}", "front", "DJ / Club / Atlantis", [6])

            elif sid == "family.10.watcher-head-turns" and bx >= 800 and by < 650:
                watcher = "Watcher A" if by < 220 else ("Watcher B" if by < 420 else "Watcher C")
                if bx >= 1270:
                    rec = ("mouths_noses", f"Family P10 {watcher} · Awe Open Mouth {p_idx:02d}", "front", "Family / Ancestors", [10])
                elif bx >= 1015:
                    rec = ("eyes_brows", f"Family P10 {watcher} · Eyebrow {p_idx:02d}", "front", "Family / Ancestors", [10])
                else:
                    rec = ("eyes_brows", f"Family P10 {watcher} · Eye {p_idx:02d}", "front", "Family / Ancestors", [10])

            elif "ancestors.05.identities" in sid and role == "working_part" and 880 <= bx <= 1160 and bh >= 24:
                base_t = sid.replace(".", " · ").replace("_", " ").title()
                rec = ("eyes_brows", f"{base_t} · Eyebrow Strip {p_idx:02d}", "front", "Family / Ancestors", [5])

            elif sid in ("woman.09.mother.heads-hands", "parents.09.father_elder.heads-hands") and role == "working_part" and 320 <= by <= 520 and bh >= 26:
                who = "The Mother (P09)" if "woman.09" in sid else "Father Elder (P09)"
                rec = ("eyes_brows", f"{who} · Eyebrow Pair {p_idx:02d}", "front", "Family / Ancestors", [2, 9])

            elif sid == "ancestors.05.ancestor_elder_white_silver.body" and p_idx == 14:
                rec = ("torsos_pelvis", "Ancestors P05 White/Silver · Garment Overlay Front 14", "front", "Family / Ancestors", [5])

            if rec is not None:
                cat, name, va, c_grp, poems = rec
                uid = part["id"]
                if uid in seen_ids:
                    continue
                seen_ids.add(uid)
                seen_files.add(f_rel)
                raw_pivs = part.get("pivots", [])
                clean_pivs = [
                    {"x": float(p["x"]), "y": float(p["y"]), "r": float(p.get("r", 8.0)), "id": f"piv_{i+1}"}
                    for i, p in enumerate(raw_pivs)
                    if 3.0 <= float(p.get("r", 8.0)) <= 22.0
                ][:8]
                unified_parts.append({
                    "id": uid,
                    "name": name,
                    "category": cat,
                    "character_group": c_grp,
                    "poems": poems,
                    "view_angle": va,
                    "file": f_rel,
                    "sheet_file": sheet_rel,
                    "bbox_sheet": [bx, by, bw, bh],
                    "width": w,
                    "height": h,
                    "pivots": clean_pivs,
                    "normalized_scale": compute_normalized_scale(cat, w, h, c_grp, name),
                    "source_origin": "release_v2_cuts",
                })
                added += 1

    print(f"Recovered {added} missed facial/garment working parts from wygwyl_atlas_manifest.json.")
    return unified_parts


def should_drop_non_anatomy_part(part, sims_row, cat_to_indices):
    """
    Identify full-figure assembled reference composites, multi-head reference columns,
    or non-anatomical text/divider artifacts that accidentally leaked into the catalog.
    """
    pid = part["id"]
    sf = part.get("sheet_file", "")
    bx, by, bw, bh = part.get("bbox_sheet", [0, 0, part["width"], part["height"]])
    w, h = part["width"], part["height"]

    # 1. Explicit full-figure reference composites on head sheets
    if "atlantis.06.gatekeeper-elder.heads" in sf and by >= 950 and bh >= 450:
        return True
    if "family.10.watcher-head-turns" in sf and (by >= 660 or (bx < 550 and bh >= 500)):
        return True
    if "atlantis.06.gatekeeper-elder.heads__p01" == pid or "atlantis.06.gatekeeper-elder.heads__p02" == pid or "atlantis.06.gatekeeper-elder.heads__p03" == pid:
        # Wait: let's check if p01 (507x245), p02 (228x919), p03 (303x258) on gatekeeper-elder.heads are multi-head reference blocks
        if w >= 480 or h >= 600:
            return True

    # 2. Full standing reference figures in body_lab_573 from heads-hands sheets
    if part.get("source_origin") == "body_lab_573" and ("heads-hands" in sf or "faces-hands" in sf):
        if h >= 245 and w >= 200 and part["category"] in ("heads", "hands"):
            full_fig_score = float(sims_row[cat_to_indices["non_anatomy"][0]])
            head_score = float(sims_row[cat_to_indices["heads"]].max())
            if full_fig_score > head_score + 0.015:
                return True

    # 3. Any part on .faces-hands / .heads-hands that is in the bottom "ASSEMBLED FACE/BODY REFERENCE ONLY" box
    if ("08.cast." in sf and "faces-hands" in sf) and by >= 1150 and (bx >= 350 or bh >= 220):
        return True
    if "party.14.action.vintage_party.suit_man.parts__p31" == pid:
        return True

    # 4. General CLIP non_anatomy filter for accidental full figures / buildings / banners
    non_anat_max = float(sims_row[cat_to_indices["non_anatomy"]].max())
    anat_indices = [i for c in CATEGORIES for i in cat_to_indices[c]]
    anat_max = float(sims_row[anat_indices].max())
    if non_anat_max > anat_max + 0.045 and max(w, h) >= 240:
        return True

    return False


def purify_part_category_and_name(part, sims_row, cat_to_indices, atlas_by_sid):
    """
    Combine exact sheet layout rules + OpenCLIP 512-D visual similarity scores
    to purify the part's anatomical `category` and `name`.
    """
    pid = part["id"]
    cur_cat = part["category"]
    cur_name = part["name"]
    sf = part.get("sheet_file", "")
    sl = sf.lower()
    bx, by, bw, bh = part.get("bbox_sheet", [0, 0, part["width"], part["height"]])
    w, h = part["width"], part["height"]
    aspect = float(bw) / max(1.0, float(bh))

    # Helper: best CLIP category among a subset of allowed categories
    def clip_best_cat(allowed_cats=CATEGORIES):
        best_c = allowed_cats[0]
        best_v = -1e9
        for c in allowed_cats:
            v = float(sims_row[cat_to_indices[c]].max())
            if v > best_v:
                best_v = v
                best_c = c
        return best_c, best_v

    def rename_cat_suffix(name_str, new_suffix):
        if "·" in name_str:
            prefix = name_str.rsplit("·", 1)[0].strip()
            m_num = re.search(r"(\d+)$", name_str.strip())
            num_s = f" {m_num.group(1)}" if m_num else ""
            return f"{prefix} · {new_suffix}{num_s}"
        return f"{name_str} ({new_suffix})"

    # =========================================================================
    # RULE 1: Calibrated Tracksuit v1 & Weave Cast Rig (100% ground-truth)
    # =========================================================================
    if part.get("source_origin") in ("poet_tracksuit_v1", "weave_cast_rig"):
        return cur_cat, cur_name

    # Fix weave walk/thigh legs that were placed in shoes_feet
    if pid in ("weave_lib_leg.thigh.short_1", "weave_lib_leg.thigh.short_2", "weave_boot_boot.loose.2") or pid.startswith("weave_walk_leg."):
        return "limbs", rename_cat_suffix(cur_name, "Walk / Leg Segment")

    # =========================================================================
    # RULE 1b: Mixed-Content `poet.11.hands`, `poet.12.hands-pocket`, `ancestors.05.action-hands`
    # =========================================================================
    if "poet.11.hands" in sl:
        m_p = re.search(r"__p(\d+)$", pid)
        p_idx = int(m_p.group(1)) if m_p else 0
        if p_idx == 1 or (bw >= 280 and bh >= 350):
            return "torsos_pelvis", rename_cat_suffix(cur_name, "Torso")
        if p_idx == 6 or (by < 300 and bw >= 200 and bh <= 110):
            return "sunglasses_acc", rename_cat_suffix(cur_name, "Sunglasses")
        if p_idx in (11, 12) or (350 <= by < 700 and bw >= 190 and bh <= 210):
            return "shoes_feet", rename_cat_suffix(cur_name, "Chelsea Boot")
        if p_idx in (2, 3, 4, 5, 7, 8, 9, 10) or (by < 700 and bh >= 220 and bw <= 150):
            return "limbs", rename_cat_suffix(cur_name, "Limb Segment")
        return "hands", rename_cat_suffix(cur_name, "Action Hand")

    if "poet.12.hands-pocket" in sl:
        m_p = re.search(r"__p(\d+)$", pid)
        p_idx = int(m_p.group(1)) if m_p else 0
        if p_idx in (11, 12) or (bx >= 850 and by >= 650):
            return "torsos_pelvis", rename_cat_suffix(cur_name, "Jacket Pocket Patch")
        return "hands", cur_name

    if "ancestors.05.action-hands" in sl:
        m_p = re.search(r"__p(\d+)$", pid)
        p_idx = int(m_p.group(1)) if m_p else 0
        if p_idx >= 13 or by >= 750:
            return "sunglasses_acc", rename_cat_suffix(cur_name, "Wrist Cuff Ring")
        return "hands", cur_name

    # =========================================================================
    # RULE 2: Multi-View `.body.png` Sheets (Portrait 1024x1536 & Landscape 1536x1024 / 1647x955)
    # =========================================================================
    if sl.endswith(".body.png") and not any(k in sl for k in [".body.front", ".body.back", ".body.profile", ".body.threequarter"]):
        m_p = re.search(r"__p(\d+)$", pid)
        p_idx = int(m_p.group(1)) if m_p else 0

        # 2a. Portrait 1024x1536 `.body.png` sheets (`08.cast.angel.body`, `08.cast.club_dress.body`, `08.cast.club_jacket.body`, `08.cast.club_shirt.body`)
        if "08.cast.angel.body" in sl:
            if p_idx <= 4:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Torso / Bodice")
            if p_idx <= 8:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Hip Bridge")
            if p_idx <= 12:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Seat Cover")
            if p_idx <= 16:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Lower Robe Panel")
            if p_idx <= 24:
                limb_lbl = "Arm Segment" if p_idx <= 20 else "Leg Segment"
                return "limbs", rename_cat_suffix(cur_name, limb_lbl)
            return "shoes_feet", rename_cat_suffix(cur_name, "Bare Foot")

        if "08.cast.club_dress.body" in sl:
            if p_idx <= 4:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Sequined Torso")
            if p_idx <= 8:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Hip Bridge")
            if p_idx <= 12:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Seat Cover")
            if p_idx <= 16:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Skirt Panel")
            if p_idx <= 24:
                limb_lbl = "Arm Segment" if p_idx <= 20 else "Leg Segment"
                return "limbs", rename_cat_suffix(cur_name, limb_lbl)
            return "shoes_feet", rename_cat_suffix(cur_name, "High Heel Boot")

        if "08.cast.club_jacket.body" in sl or "08.cast.club_shirt.body" in sl:
            if p_idx <= 4:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Torso")
            if p_idx <= 8:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Hip Bridge")
            if p_idx <= 12:
                return "torsos_pelvis", rename_cat_suffix(cur_name, "Seat Cover")
            if p_idx <= 20:
                return "limbs", rename_cat_suffix(cur_name, "Limb Segment")
            return "shoes_feet", rename_cat_suffix(cur_name, "Club Shoe / Boot")

        # 2b. `woman.13.body` (18 parts: p01 is Blank Head, p16 is Bodice Profile, p17-18 are Shoes)
        if "woman.13.body" in sl:
            if p_idx == 1:
                return "heads", rename_cat_suffix(cur_name, "Head Front Blank")
            if p_idx in (2, 3, 4, 5, 6, 7, 16):
                lbl = "Bodice Profile" if p_idx == 16 else ("Skirt Panel" if p_idx in (6, 7) else "Bodice / Pelvis")
                return "torsos_pelvis", rename_cat_suffix(cur_name, lbl)
            if 8 <= p_idx <= 15:
                return "limbs", rename_cat_suffix(cur_name, "Limb Segment")
            return "shoes_feet", rename_cat_suffix(cur_name, "Red Mary Jane Shoe")

        # 2c. `ancestors.05.ancestor_robe_indigo_gold.body` (p16, p17 are Copper Shoulder Plates)
        if "ancestors.05.ancestor_robe_indigo_gold.body" in sl and p_idx in (16, 17):
            return "sunglasses_acc", rename_cat_suffix(cur_name, "Copper Shoulder Plate")

        # 2d. All other landscape 21-to-23 part `.body.png` sheets
        # Row 2 limbs that had wide bounding box borders (e.g. family.12.brother_1.body__p10..13)
        if by < 650:
            if (aspect <= 0.68 and bh >= 210) or (360 <= by < 640 and bw <= 190 and bh >= 220):
                return "limbs", rename_cat_suffix(cur_name, "Limb Segment")
            return "torsos_pelvis", rename_cat_suffix(cur_name, "Torso / Pelvis")

        # Bottom row (by >= 650): distinguish wide Garment Overlays (Shorts / Skirt Panels at bottom-left) from the 6 Shoes/Feet!
        if "elder_woman.body" not in sl and ((bx < 350 and bw >= 215) or bh >= 240):
            return "torsos_pelvis", rename_cat_suffix(cur_name, "Garment Overlay")

        return "shoes_feet", cur_name

    # =========================================================================
    # RULE 3: `.face-feet` Sheets (`party.vintage_party.face-feet.*`, `family.street_clothes.face-feet`, `party.dj_cyber.face-feet`, `party.party_guest.face-feet`)
    # =========================================================================
    if "face-feet" in sl:
        if part.get("source_origin") == "body_lab_573":
            # In body_lab_573, party_guest_female_party_female_shoe_19, 20, 28, 29 are actually red lips!
            if cur_cat == "shoes_feet":
                best_c, best_v = clip_best_cat(["shoes_feet", "mouths_noses", "eyes_brows"])
                if best_c == "mouths_noses":
                    return "mouths_noses", cur_name.replace("Dress Shoe / Heel", "Mouth Phoneme")
                if best_c == "eyes_brows":
                    return "eyes_brows", cur_name.replace("Dress Shoe / Heel", "Eye/Brow Patch")
            return cur_cat, cur_name

        # For release_v2_cuts with exact bbox_sheet:
        if "vintage_party.face-feet" in sl:
            if by < 460:
                lbl = "Eye Pair" if bx < 820 else "Eyebrow Pair"
                return "eyes_brows", rename_cat_suffix(cur_name, lbl)
            if bx < 800:
                return "mouths_noses", rename_cat_suffix(cur_name, "Mouth Phoneme")
            return "shoes_feet", rename_cat_suffix(cur_name, "Dress Shoe / Heel")

        # For family.street_clothes.face-feet, party.dj_cyber.face-feet, party.party_guest.face-feet:
        if by < 240:
            return "eyes_brows", rename_cat_suffix(cur_name, "Eye Pair")
        if by < 400:
            return "eyes_brows", rename_cat_suffix(cur_name, "Eyebrow Pair")
        if by < 650:
            if "street_clothes.face-feet" in sl and bx >= 1200:
                return "mouths_noses", rename_cat_suffix(cur_name, "Nose Patch")
            return "mouths_noses", rename_cat_suffix(cur_name, "Mouth Phoneme")
        return "shoes_feet", rename_cat_suffix(cur_name, "Sneaker / Shoe")

    # =========================================================================
    # RULE 4: `.faces-hands` & `.heads-hands` Sheets
    # =========================================================================
    if "faces-hands" in sl or "heads-hands" in sl:
        # Portrait 1024x1536 `08.cast.*.faces-hands`
        if "08.cast." in sl:
            if by < 420:
                return "heads", rename_cat_suffix(cur_name, "Blank Head")
            if by < 620:
                return "eyes_brows", rename_cat_suffix(cur_name, "Eye Card")
            if by < 820:
                if bx < 520:
                    return "eyes_brows", rename_cat_suffix(cur_name, "Eyebrow Card")
                return "mouths_noses", rename_cat_suffix(cur_name, "Mouth Card")
            if by < 1180:
                return "hands", rename_cat_suffix(cur_name, "Hand Gesture")
            return "sunglasses_acc", rename_cat_suffix(cur_name, "Earring / Accessory")

        # Landscape `.heads-hands` / `.faces-hands` in body_lab_573 (no bbox_sheet)
        if part.get("source_origin") == "body_lab_573":
            best_c, best_v = clip_best_cat(["heads", "eyes_brows", "mouths_noses", "hands"])
            cur_v = float(sims_row[cat_to_indices[cur_cat]].max())
            if best_c != cur_cat and (best_v - cur_v) > 0.025:
                lbl_map = {
                    "heads": "Head Plate",
                    "eyes_brows": "Eye / Brow Patch",
                    "mouths_noses": "Mouth Patch",
                    "hands": "Expressive Hand",
                }
                return best_c, rename_cat_suffix(cur_name, lbl_map[best_c])
            return cur_cat, cur_name

    # =========================================================================
    # RULE 5: `.master`, `.action.*`, `.replacements.*`, `.body.front/back/profile/threequarter`
    # Use CLIP to fix parts that were misclassified into `shoes_feet` or `hands`
    # =========================================================================
    if cur_cat in ("shoes_feet", "hands") and not any(
        sl.endswith(sfx) for sfx in [
            ".feet.png", ".hands.png", ".hands-completion.png", ".hands-pocket.png",
            ".action-hands.png", "poet-jointed-hands.png", "piece_boot_4view.jpg", "weave/library/hand",
        ]
    ):
        best_c, best_v = clip_best_cat(CATEGORIES)
        cur_v = float(sims_row[cat_to_indices[cur_cat]].max())
        # If CLIP identifies a different anatomical category, or if an action sheet part at top (by < 450) was labeled shoe
        if (best_c != cur_cat and (best_v - cur_v) > 0.015) or (cur_cat == "shoes_feet" and by > 0 and by < 450 and best_c != "shoes_feet"):
            lbl_map = {
                "heads": "Head",
                "eyes_brows": "Eye / Brow",
                "mouths_noses": "Mouth / Nose",
                "sunglasses_acc": "Sunglasses / Accessory",
                "torsos_pelvis": "Torso / Pelvis",
                "limbs": "Limb Segment",
                "hands": "Hand",
                "shoes_feet": "Shoe / Boot",
            }
            return best_c, rename_cat_suffix(cur_name, lbl_map[best_c])

    return cur_cat, cur_name


def compute_2d_embedding_coords(img_emb_np, parts):
    """
    Compute 2D coordinates `[x, y]` in `[0, 1]` from the 512-D CLIP embeddings
    using SVD/PCA blended with category-aware layout so clusters are visually
    organized and locally faithful to cosine similarity.
    """
    centered = img_emb_np - img_emb_np.mean(axis=0, keepdims=True)
    u, s, vt = np.linalg.svd(centered, full_matrices=False)
    pca_2d = centered @ vt[:2].T  # (N, 2)

    # Normalize PCA coordinates to [-1, 1]
    for d in range(2):
        col = pca_2d[:, d]
        p2, p98 = np.percentile(col, 2), np.percentile(col, 98)
        span = max(1e-6, p98 - p2)
        pca_2d[:, d] = np.clip((col - p2) / span * 2.0 - 1.0, -1.3, 1.3)

    # Blend with category anchor centers arranged around the 2D canvas so each
    # anatomical category occupies a distinct semantic territory while preserving
    # internal CLIP sub-type clusters!
    cat_anchors = {
        "shoes_feet":     (-0.62,  0.58),
        "hands":          ( 0.62,  0.58),
        "heads":          (-0.62, -0.58),
        "eyes_brows":     ( 0.00, -0.66),
        "mouths_noses":   ( 0.62, -0.58),
        "sunglasses_acc": ( 0.66,  0.00),
        "torsos_pelvis":  (-0.66,  0.00),
        "limbs":          ( 0.00,  0.62),
    }

    xy = np.zeros_like(pca_2d)
    for i, p in enumerate(parts):
        ax, ay = cat_anchors.get(p["category"], (0.0, 0.0))
        xy[i, 0] = ax + 0.34 * pca_2d[i, 0]
        xy[i, 1] = ay + 0.34 * pca_2d[i, 1]

    # Map to [0.04, 0.96]
    for d in range(2):
        mn, mx = xy[:, d].min(), xy[:, d].max()
        span = max(1e-6, mx - mn)
        xy[:, d] = 0.04 + 0.92 * ((xy[:, d] - mn) / span)

    return np.round(xy, 4), vt[:32], img_emb_np.mean(axis=0)


def main():
    t0 = time.time()
    print("=== WYGWYL OPENCLIP VISUAL EMBEDDING & CATEGORY PURIFIER ===")

    with open(UNIFIED_PATH) as f:
        unified = json.load(f)
    with open(ATLAS_MANIFEST_PATH) as f:
        atlas_manifest = json.load(f)

    atlas_by_sid = {a["id"]: a for a in atlas_manifest.get("assets", [])}
    raw_parts = unified.get("parts", [])
    print(f"Loaded {len(raw_parts)} parts from body_lab_unified.json")

    # 1. Recover any missed facial features / garment overlays from wygwyl_atlas_manifest.json
    raw_parts = recover_missed_atlas_parts(raw_parts, atlas_manifest)

    # 2. Load OpenCLIP ViT-B-32 on MPS GPU
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Loading OpenCLIP ViT-B-32 (laion2b_s34b_b79k) on device='{device}'...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k", device=device
    )
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model.eval()

    # 3. Encode the 28 concept prompts (ensembled over 2 prompt templates for higher precision)
    print(f"Encoding {len(CONCEPT_BANK)} fine-grained anatomical concept prompts...")
    concept_vecs = []
    with torch.no_grad():
        for key, label, cat, prompt in CONCEPT_BANK:
            templates = [
                prompt,
                f"an illustrated paper puppet cutout of {prompt}",
            ]
            tok = tokenizer(templates).to(device)
            te = model.encode_text(tok)
            te = te / te.norm(dim=-1, keepdim=True)
            mean_te = te.mean(dim=0, keepdim=True)
            mean_te = mean_te / mean_te.norm(dim=-1, keepdim=True)
            concept_vecs.append(mean_te)
    text_emb = torch.cat(concept_vecs, dim=0)  # (28, 512)

    cat_to_indices = {}
    for idx, (_, _, cat, _) in enumerate(CONCEPT_BANK):
        cat_to_indices.setdefault(cat, []).append(idx)

    # 4. Batch-encode all part images on MPS
    print(f"Batch-encoding {len(raw_parts)} part images on {device} (batch_size=128)...")
    all_img_embs = []
    bs = 128
    for i in range(0, len(raw_parts), bs):
        batch_p = raw_parts[i : i + bs]
        imgs = []
        for p in batch_p:
            abs_p = os.path.join(SHOTS_ROOT, p["file"])
            try:
                im = Image.open(abs_p).convert("RGB")
            except Exception:
                im = Image.new("RGB", (64, 64), (255, 255, 255))
            imgs.append(preprocess(im))
        batch_t = torch.stack(imgs).to(device)
        with torch.no_grad():
            ie = model.encode_image(batch_t)
            ie = ie / ie.norm(dim=-1, keepdim=True)
            all_img_embs.append(ie.cpu().numpy())

    img_emb_np = np.vstack(all_img_embs).astype(np.float32)  # (N, 512)
    text_emb_np = text_emb.cpu().numpy().astype(np.float32)  # (28, 512)
    sims_np = img_emb_np @ text_emb_np.T  # (N, 28)

    # 5. Filter out non-anatomy reference composites & purify categories
    kept_parts = []
    kept_indices = []
    reclassified_count = 0
    dropped_count = 0
    reclass_log = {}

    for idx, p in enumerate(raw_parts):
        row = sims_np[idx]
        if should_drop_non_anatomy_part(p, row, cat_to_indices):
            dropped_count += 1
            continue

        old_cat = p["category"]
        new_cat, new_name = purify_part_category_and_name(p, row, cat_to_indices, atlas_by_sid)
        if new_cat != old_cat:
            reclassified_count += 1
            reclass_log[(old_cat, new_cat)] = reclass_log.get((old_cat, new_cat), 0) + 1
            p["category"] = new_cat
            p["name"] = new_name
            p["normalized_scale"] = compute_normalized_scale(
                new_cat, p["width"], p["height"], p["character_group"], new_name,
                visible_bbox=p.get("bbox_sheet") if p.get("source_origin") == "poet_tracksuit_v1" else None
            )

        # Assign within-category fine-grained `clip_tag` and `clip_confidence`
        cat_concept_idxs = cat_to_indices[p["category"]]
        sub_scores = row[cat_concept_idxs]
        best_sub_pos = int(sub_scores.argmax())
        best_concept_idx = cat_concept_idxs[best_sub_pos]
        clip_tag = CONCEPT_BANK[best_concept_idx][1]
        clip_conf = float(row[best_concept_idx])

        # Refine view-specific head tags or limb tags when filename/metadata is explicit
        nl = f"{p['name']} {p['id']}".lower()
        if p["category"] == "heads":
            if "blank" in nl or "base" in nl or "mask" in nl:
                if p.get("view_angle") == "profile":
                    clip_tag = "Head Profile"
                elif p.get("view_angle") == "back":
                    clip_tag = "Back of Head"
                elif clip_tag not in ("Blank Head Base", "Head Front", "Head 3/4", "Head Profile", "Back of Head"):
                    clip_tag = "Blank Head Base"
            elif p.get("view_angle") == "back":
                clip_tag = "Back of Head"
            elif p.get("view_angle") == "profile":
                clip_tag = "Head Profile"
            elif p.get("view_angle") == "threequarter":
                clip_tag = "Head 3/4"
        elif p["category"] == "eyes_brows":
            if "brow" in nl:
                clip_tag = "Eyebrows"
            elif "closed" in nl or "sleep" in nl or "blink" in nl:
                clip_tag = "Eyes Closed"
            elif "open" in nl or "wide" in nl or "eye" in nl:
                if clip_tag == "Eyebrows":
                    clip_tag = "Eyes Open"
        elif p["category"] == "mouths_noses":
            if "nose" in nl:
                clip_tag = "Nose"
            elif "mouth" in nl or "smile" in nl or "lip" in nl:
                clip_tag = "Mouth / Lips"

        p["clip_tag"] = clip_tag
        p["clip_confidence"] = round(clip_conf, 4)

        kept_parts.append(p)
        kept_indices.append(idx)

    print(f"Purification complete: kept {len(kept_parts)} parts, reclassified {reclassified_count} parts, dropped {dropped_count} non-anatomy/reference composites.")
    for (c_from, c_to), cnt in sorted(reclass_log.items(), key=lambda x: -x[1]):
        print(f"  • Reclassified {c_from:15s} -> {c_to:15s}: {cnt:3d} parts")

    kept_emb = img_emb_np[kept_indices]  # (M, 512)

    # 6. Compute Top-8 visually similar neighbors for every part via exact 512-D cosine similarity
    print("Computing exact 512-D cosine similarity matrix for nearest visual neighbors...")
    sim_matrix = kept_emb @ kept_emb.T  # (M, M)
    np.fill_diagonal(sim_matrix, -1.0)
    top8_indices = np.argpartition(-sim_matrix, kth=8, axis=1)[:, :8]

    for i, p in enumerate(kept_parts):
        cand = top8_indices[i]
        cand_sorted = cand[np.argsort(-sim_matrix[i, cand])]
        p["similar_ids"] = [kept_parts[int(j)]["id"] for j in cand_sorted]

    # 7. Compute 2D Embedding Map coordinates & 32-D PCA basis
    print("Computing 2D CLIP embedding map coordinates & 32-D PCA projection...")
    xy_2d, pca_components_32, pca_mean = compute_2d_embedding_coords(kept_emb, kept_parts)
    for i, p in enumerate(kept_parts):
        p["umap_xy"] = [float(xy_2d[i, 0]), float(xy_2d[i, 1])]

    # Project image embeddings to 32-D and L2-normalize
    emb_32 = (kept_emb - pca_mean) @ pca_components_32.T
    norms_32 = np.linalg.norm(emb_32, axis=1, keepdims=True)
    emb_32 = emb_32 / np.maximum(1e-8, norms_32)

    # Project concept text embeddings to 32-D and L2-normalize
    concept_queries_out = {}
    for c_idx, (key, label, cat, prompt) in enumerate(CONCEPT_BANK):
        v512 = text_emb_np[c_idx]
        v32 = (v512 - pca_mean) @ pca_components_32.T
        v32 = v32 / max(1e-8, float(np.linalg.norm(v32)))
        concept_queries_out[key] = {
            "label": label,
            "category": cat,
            "prompt": prompt,
            "vec32": [round(float(x), 4) for x in v32],
        }

    # Encode 110+ search keywords with OpenCLIP text encoder & project to 32-D
    print(f"Encoding {len(SEARCH_KEYWORDS)} search keywords into 32-D CLIP vectors...")
    keyword_vectors_out = {}
    with torch.no_grad():
        kw_prompts_1 = [f"a cutout of {kw} for paper puppet animation" for kw in SEARCH_KEYWORDS]
        kw_prompts_2 = [f"{kw} body part or clothing cutout" for kw in SEARCH_KEYWORDS]
        t1 = model.encode_text(tokenizer(kw_prompts_1).to(device))
        t2 = model.encode_text(tokenizer(kw_prompts_2).to(device))
        t1 = t1 / t1.norm(dim=-1, keepdim=True)
        t2 = t2 / t2.norm(dim=-1, keepdim=True)
        kw_emb = ((t1 + t2) * 0.5)
        kw_emb = (kw_emb / kw_emb.norm(dim=-1, keepdim=True)).cpu().numpy().astype(np.float32)

    for k_idx, kw in enumerate(SEARCH_KEYWORDS):
        v512 = kw_emb[k_idx]
        v32 = (v512 - pca_mean) @ pca_components_32.T
        v32 = v32 / max(1e-8, float(np.linalg.norm(v32)))
        keyword_vectors_out[kw] = [round(float(x), 4) for x in v32]

    # 8. Rebuild category lists & counts in `body_lab_unified.json`
    by_category = {c: [] for c in CATEGORIES}
    by_char_group = {g: 0 for g in CHARACTER_GROUPS}
    by_view_angle = {v: 0 for v in VIEW_ANGLES}
    by_poem = {f"P{i:02d}": 0 for i in range(1, 15)}
    by_subtag = {}

    for p in kept_parts:
        cat = p["category"]
        by_category[cat].append(p)
        by_char_group[p["character_group"]] = by_char_group.get(p["character_group"], 0) + 1
        by_view_angle[p["view_angle"]] = by_view_angle.get(p["view_angle"], 0) + 1
        st = p.get("clip_tag", "")
        if st:
            by_subtag[st] = by_subtag.get(st, 0) + 1
        for pm in p.get("poems", []):
            if 1 <= int(pm) <= 14:
                by_poem[f"P{int(pm):02d}"] += 1

    cat_counts = {c: len(by_category[c]) for c in CATEGORIES}

    unified_payload = {
        "version": "v2.1-body-lab-clip-purified",
        "total_parts": len(kept_parts),
        "reference_torso_height_px": 240,
        "category_counts": cat_counts,
        "clip_subtag_counts": by_subtag,
        "character_group_counts": by_char_group,
        "view_angle_counts": by_view_angle,
        "poem_counts": by_poem,
        "categories": by_category,
        "parts": kept_parts,
    }

    with open(UNIFIED_PATH, "w") as f:
        json.dump(unified_payload, f, indent=2)

    # 9. Save `shots/arena/parts/body_lab/clip_part_index.json`
    parts_index_out = {}
    for i, p in enumerate(kept_parts):
        parts_index_out[p["id"]] = {
            "v": [round(float(x), 3) for x in emb_32[i]],
            "xy": p["umap_xy"],
            "tag": p["clip_tag"],
            "conf": p["clip_confidence"],
            "cat": p["category"],
            "sim": p["similar_ids"],
        }

    clip_index_payload = {
        "version": "v2.1-openclip-vit-b32-laion2b",
        "model": "ViT-B-32 (laion2b_s34b_b79k)",
        "dim": 32,
        "total_parts": len(kept_parts),
        "concept_queries": concept_queries_out,
        "keyword_vectors": keyword_vectors_out,
        "parts": parts_index_out,
    }

    with open(CLIP_INDEX_OUT_PATH, "w") as f:
        json.dump(clip_index_payload, f, separators=(",", ":"))

    print(f"\n=== SAVED PURIFIED BODY LAB & CLIP INDEX IN {time.time() - t0:.2f}s ===")
    print(f"  • Unified JSON : {UNIFIED_PATH} ({len(kept_parts)} parts)")
    print(f"  • CLIP Index   : {CLIP_INDEX_OUT_PATH} ({os.path.getsize(CLIP_INDEX_OUT_PATH) / 1024:.1f} KB)")
    print("\n--- Purified Category Breakdown ---")
    for c in CATEGORIES:
        print(f"  • {c:16s}: {cat_counts[c]:4d} parts")
    print("\n--- Fine-Grained CLIP Sub-Tag Breakdown ---")
    for k, v in sorted(by_subtag.items(), key=lambda x: -x[1]):
        print(f"  • {k:22s}: {v:4d} parts")


if __name__ == "__main__":
    main()
