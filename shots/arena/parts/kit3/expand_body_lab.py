#!/usr/bin/env python3
"""
expand_body_lab.py

Anatomical Body Lab & Cross-Kit Comparative Part Solver for the WYGWYL Cut-Out Animation Suite.
Generates `shots/arena/parts/body_lab/body_lab_unified.json` combining:
  1. All 31 Poet Tracksuit components (`shots/kits/packs/poet_tracksuit_v1/01_COMPONENTS/`) with exact calibrated brass pivot sockets
  2. All 573 isolated PNGs in `shots/arena/parts/body_lab/body_lab_catalog.json` (plus weave/cast/man/cast.json & library_manifest.json sockets/brads)
  3. All anatomical & wardrobe parts across all 14 poems from `release_catalog.json` and `character_faces_catalog.json`

Categorizes every part cleanly into 8 comprehensive anatomical categories:
  1. `hands`          — All Hands (relaxed, open, pointing, fist, holding props, paired waltz hands, L/R orientation)
  2. `shoes_feet`     — All Shoes & Feet (boots, sneakers, dress shoes, heels, bare feet, child shoes, front/profile/3Q/back)
  3. `heads`          — All Heads & Profiles (front, 3/4, profile, back-of-head EX, blank head bases, child/adult/elder)
  4. `eyes_brows`     — All Eyes & Eyebrows (open, closed, half-lidded, wide, raised brows, furrowed brows, rest brows)
  5. `mouths_noses`   — All Mouths & Noses (rest, smile, open O, open A, speaking phonemes, front/profile noses)
  6. `sunglasses_acc` — All Sunglasses, Headgear & Accessories (Poet red/black sunglasses, hats, headphones, jewelry, masks)
  7. `torsos_pelvis`  — All Torsos, Jackets, Dresses & Hip Bridges (Poet tracksuit torso front/back, black t-shirt, EX bomber jacket back/3Q, Woman dresses, Party suits/gowns, hip bridges, pelvis covers)
  8. `limbs`          — All Upper Arms, Forearms, Thighs & Shins (with shoulder/elbow/wrist/hip/knee/ankle brass pivot coordinates)
"""

import os
import re
import json
from PIL import Image

SHOTS_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots"
REPO_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"

BODY_LAB_CAT_PATH = os.path.join(SHOTS_ROOT, "arena/parts/body_lab/body_lab_catalog.json")
RELEASE_CAT_PATH = os.path.join(SHOTS_ROOT, "arena/parts/kit3/release_v2/release_catalog.json")
FACES_CAT_PATH = os.path.join(SHOTS_ROOT, "kits/character_faces_catalog.json")
TRACKSUIT_MANIFEST_PATH = os.path.join(SHOTS_ROOT, "kits/packs/poet_tracksuit_v1/manifest.json")
WEAVE_CAST_PATH = os.path.join(SHOTS_ROOT, "weave/cast/man/cast.json")
WEAVE_LIB_PATH = os.path.join(SHOTS_ROOT, "weave/cast/man/library_manifest.json")
OUT_UNIFIED_PATH = os.path.join(SHOTS_ROOT, "arena/parts/body_lab/body_lab_unified.json")

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

# Calibrated brass pivot coordinates (in native component image pixels) for all 31 Tracksuit parts
TRACKSUIT_CALIBRATED_PIVOTS = {
    "01_torso_front": [
        {"x": 639.0, "y": 108.0, "r": 23.0, "id": "neck"},
        {"x": 300.4, "y": 212.4, "r": 22.0, "id": "shoulder_R"},
        {"x": 979.8, "y": 212.1, "r": 22.0, "id": "shoulder_L"},
        {"x": 639.4, "y": 1048.4, "r": 23.6, "id": "waist"},
    ],
    "02_torso_back": [
        {"x": 649.0, "y": 116.1, "r": 34.5, "id": "neck"},
        {"x": 290.9, "y": 276.6, "r": 40.5, "id": "shoulder_L"},
        {"x": 1013.3, "y": 276.8, "r": 40.0, "id": "shoulder_R"},
        {"x": 651.4, "y": 1087.8, "r": 42.3, "id": "waist"},
    ],
    "03_waist_link": [
        {"x": 647.4, "y": 339.2, "r": 75.9, "id": "top"},
        {"x": 646.3, "y": 895.1, "r": 74.5, "id": "bottom"},
    ],
    "04_hip_bridge": [
        {"x": 759.6, "y": 192.2, "r": 65.0, "id": "waist"},
        {"x": 357.3, "y": 791.2, "r": 64.1, "id": "hip_R"},
        {"x": 1172.8, "y": 791.3, "r": 64.5, "id": "hip_L"},
    ],
    "05_rear_seat_cover": [
        {"x": 726.8, "y": 161.5, "r": 30.9, "id": "waist"},
    ],
    "06_pelvis_front_cover": [
        {"x": 727.3, "y": 180.5, "r": 38.2, "id": "waist"},
    ],
    "07_upper_arm_L": [
        {"x": 507.7, "y": 166.4, "r": 38.6, "id": "shoulder"},
        {"x": 493.6, "y": 1362.5, "r": 36.4, "id": "elbow"},
    ],
    "08_forearm_L": [
        {"x": 512.0, "y": 180.0, "r": 36.0, "id": "elbow"},
        {"x": 510.5, "y": 1320.6, "r": 34.5, "id": "wrist"},
    ],
    "09_upper_arm_R": [
        {"x": 504.0, "y": 138.5, "r": 39.5, "id": "shoulder"},
        {"x": 534.0, "y": 1387.1, "r": 39.5, "id": "elbow"},
    ],
    "10_forearm_R": [
        {"x": 513.8, "y": 176.3, "r": 40.9, "id": "elbow"},
        {"x": 510.7, "y": 1375.5, "r": 38.2, "id": "wrist"},
    ],
    "11_thigh_L": [
        {"x": 511.0, "y": 180.1, "r": 37.3, "id": "hip"},
        {"x": 509.8, "y": 1344.4, "r": 37.7, "id": "knee"},
    ],
    "12_shin_L": [
        {"x": 511.1, "y": 198.3, "r": 32.3, "id": "knee"},
        {"x": 512.3, "y": 1387.6, "r": 32.7, "id": "ankle"},
    ],
    "13_thigh_R": [
        {"x": 511.8, "y": 192.2, "r": 41.8, "id": "hip"},
        {"x": 514.4, "y": 1342.4, "r": 39.5, "id": "knee"},
    ],
    "14_shin_R": [
        {"x": 507.4, "y": 176.0, "r": 33.2, "id": "knee"},
        {"x": 519.9, "y": 1392.9, "r": 32.3, "id": "ankle"},
    ],
    "15_hand_relaxed_L": [{"x": 660.8, "y": 190.1, "r": 55.9, "id": "wrist"}],
    "16_hand_relaxed_R": [{"x": 646.0, "y": 255.5, "r": 43.2, "id": "wrist"}],
    "17_hand_open_L": [{"x": 697.2, "y": 1087.0, "r": 44.1, "id": "wrist"}],
    "18_hand_open_R": [{"x": 672.0, "y": 1072.0, "r": 46.4, "id": "wrist"}],
    "19_boot_front_L": [{"x": 625.0, "y": 315.0, "r": 48.0, "id": "ankle"}],
    "20_boot_front_R": [{"x": 635.0, "y": 315.0, "r": 48.0, "id": "ankle"}],
    "21_head_front_blank": [{"x": 558.0, "y": 1159.0, "r": 42.0, "id": "neck"}],
    "22_eyes_open": [],
    "23_eyes_closed": [],
    "24_brows_rest": [],
    "25_brows_raised": [],
    "26_nose_front": [],
    "27_mouth_rest": [],
    "28_mouth_smile": [],
    "29_mouth_open_O": [],
    "30_mouth_open_A": [],
    "31_sunglasses_front": [
        {"x": 163.4, "y": 280.9, "r": 57.7, "id": "temple_R"},
        {"x": 2011.5, "y": 280.9, "r": 57.7, "id": "temple_L"},
    ],
}

TRACKSUIT_CATEGORY_MAP = {
    "01_torso_front": ("torsos_pelvis", "front"),
    "02_torso_back": ("torsos_pelvis", "back"),
    "03_waist_link": ("torsos_pelvis", "front"),
    "04_hip_bridge": ("torsos_pelvis", "front"),
    "05_rear_seat_cover": ("torsos_pelvis", "back"),
    "06_pelvis_front_cover": ("torsos_pelvis", "front"),
    "07_upper_arm_L": ("limbs", "front"),
    "08_forearm_L": ("limbs", "front"),
    "09_upper_arm_R": ("limbs", "front"),
    "10_forearm_R": ("limbs", "front"),
    "11_thigh_L": ("limbs", "front"),
    "12_shin_L": ("limbs", "front"),
    "13_thigh_R": ("limbs", "front"),
    "14_shin_R": ("limbs", "front"),
    "15_hand_relaxed_L": ("hands", "front"),
    "16_hand_relaxed_R": ("hands", "front"),
    "17_hand_open_L": ("hands", "front"),
    "18_hand_open_R": ("hands", "front"),
    "19_boot_front_L": ("shoes_feet", "front"),
    "20_boot_front_R": ("shoes_feet", "front"),
    "21_head_front_blank": ("heads", "front"),
    "22_eyes_open": ("eyes_brows", "front"),
    "23_eyes_closed": ("eyes_brows", "front"),
    "24_brows_rest": ("eyes_brows", "front"),
    "25_brows_raised": ("eyes_brows", "front"),
    "26_nose_front": ("mouths_noses", "front"),
    "27_mouth_rest": ("mouths_noses", "front"),
    "28_mouth_smile": ("mouths_noses", "front"),
    "29_mouth_open_O": ("mouths_noses", "front"),
    "30_mouth_open_A": ("mouths_noses", "front"),
    "31_sunglasses_front": ("sunglasses_acc", "front"),
}


def to_shots_rel(path_str):
    """Normalize a path so it is relative to `shots/`."""
    if not path_str:
        return ""
    p = path_str.strip().lstrip("/")
    if p.startswith("shots/"):
        p = p[len("shots/"):]
    return p


def infer_character_group(text):
    """Map sheet/character identifier to one of the 7 canonical character groups."""
    t = (text or "").lower()
    if any(k in t for k in ["young_poet", "young poet", "ghost_child", "ghost child", "young_ghost", "child_clothes", "pajamas_winter", "child_traveler"]):
        return "Child / Ghost"
    if any(k in t for k in ["ex.", "the ex", "ex_jacket", "ex_partner"]):
        return "EX"
    if any(k in t for k in ["woman.13", "woman.teal_dress", "muse-dance", "muse", "woman"]):
        if "mother" in t or "woman.09" in t:
            return "Family / Ancestors"
        return "Woman / Muse"
    if any(k in t for k in ["vintage_party", "vintage-waltz", "party_guest_male", "party_guest_female", "party guests", "gown_woman", "suit_man"]):
        return "Vintage Party"
    if any(k in t for k in ["mother", "father", "parents", "family.", "ancestors.", "elder"]):
        if "atlantis" in t:
            return "DJ / Club / Atlantis"
        return "Family / Ancestors"
    if any(k in t for k in ["dj_cyber", "dj-guest", "dj cyber", "club_", "08.cast.", "atlantis", "party.07", "party.party_guest", "bola", "dot"]):
        return "DJ / Club / Atlantis"
    return "Poet"


def infer_poems_from_group_and_text(char_group, text):
    """Infer poem list [1..14] when not explicitly provided."""
    t = (text or "").lower()
    m = re.search(r"\b(?:poem[_\s]*|p)(\d{2})\b", t)
    if m:
        pnum = int(m.group(1))
        if 1 <= pnum <= 14:
            return [pnum]
    for pnum in range(1, 15):
        if f".{pnum:02d}." in t or f"_{pnum:02d}_" in t:
            return [pnum]
    if char_group == "Child / Ghost":
        if "ghost" in t:
            return [2]
        return [2, 13]
    if char_group == "EX":
        return [1, 2, 3, 7, 8, 9]
    if char_group == "Woman / Muse":
        return [13, 14]
    if char_group == "Vintage Party":
        return [1, 14]
    if char_group == "Family / Ancestors":
        if "mother" in t:
            return [2, 9]
        if "father" in t:
            return [2, 9]
        if "ancestor" in t:
            return [5]
        return [2, 5, 9, 10, 11, 12, 13, 14]
    if char_group == "DJ / Club / Atlantis":
        if "atlantis" in t:
            return [6]
        if "dj" in t:
            return [7]
        return [6, 7, 8, 9]
    # Poet default
    if "black_tshirt" in t:
        return [1, 2, 3]
    if "tracksuit" in t or "red_black_sunglasses" in t:
        return [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    return list(range(1, 15))


def infer_view_angle(text, index_hint=None, total_hint=None):
    """Map part/sheet text or turnaround slot index to ('front', 'profile', 'threequarter', 'back')."""
    t = (text or "").lower()
    if any(k in t for k in ["threequarter_back", "3q_back", "three-quarter-back", "rear", ".back", "_back", " back"]):
        if "threequarter" in t or "3q" in t:
            return "threequarter"
        return "back"
    if any(k in t for k in ["threequarter", "3q", "three-quarter", "3/4"]):
        return "threequarter"
    if any(k in t for k in ["profile", "side", "walk", "run", "stride", "step", "lean"]):
        return "profile"
    if "front" in t:
        return "front"
    if index_hint is not None and total_hint in (4, 5):
        if total_hint == 5:
            # Standard 5-turnaround: Front, 3/4, Profile, 3/4 Back, Back
            mapping = {1: "front", 2: "threequarter", 3: "profile", 4: "threequarter", 5: "back"}
            return mapping.get(index_hint, "front")
        if total_hint == 4:
            mapping = {1: "front", 2: "threequarter", 3: "profile", 4: "back"}
            return mapping.get(index_hint, "front")
    return "front"


def compute_normalized_scale(category, width, height, char_group="Poet", name="", visible_bbox=None):
    """
    Calculate the scale factor needed to render the image at true anatomical proportion
    relative to a standard 240px adult torso.
    """
    nl = (name or "").lower()
    is_child = (char_group == "Child / Ghost")
    child_mult = 0.74 if is_child else 1.0

    # Determine target anatomical major dimension in px (relative to 240px adult torso)
    if category == "torsos_pelvis":
        if any(k in nl for k in ["waist link", "waist_link"]):
            target_px = 68.0
        elif any(k in nl for k in ["hip bridge", "hip_bridge", "pelvis", "rear seat", "rear_seat", "butt", "seat"]):
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

    # Use visible bounding box when available (e.g. poet_tracksuit_v1 large canvas with alpha padding)
    eff_w, eff_h = float(max(1, width)), float(max(1, height))
    if visible_bbox and len(visible_bbox) == 4:
        vx0, vy0, vx1, vy1 = visible_bbox
        vw = vx1 - vx0 if vx1 > vx0 else vx1
        vh = vy1 - vy0 if vy1 > vy0 else vy1
        if vw > 20 and vh > 20:
            eff_w, eff_h = float(vw), float(vh)

    major_vis = max(eff_w, eff_h)
    scale = target_px / major_vis
    return round(scale, 4)


def classify_body_lab_catalog_item(item):
    """
    Re-verify and upgrade every item from the 573-part `body_lab_catalog.json` into the 8 unified categories.
    """
    raw_cat = item.get("category", "")
    src = item.get("source", "")
    iid = item.get("id", "")
    name = item.get("name", "")
    w = int(item.get("width", 100))
    h = int(item.get("height", 100))

    # Extract trailing index if present
    m_idx = re.search(r"_(\d+)$", iid)
    idx = int(m_idx.group(1)) if m_idx else 1

    # 1. Special handling for weave/library/misc (which contains 13-part body turnarounds + sitting bodies)
    if src == "weave/library/misc":
        if "sitting" in iid:
            return "torsos_pelvis", f"Poet Sitting Body Study {idx:02d}"
        # On weave body_<view>_01..13:
        # 01, 02, 08 are torsos/pelvises (w >= 200, h >= 260)
        # 03, 04, 05, 06, 09, 10 are arms/legs capsules (w <= 175, h >= 205)
        # 07, 11, 12, 13 are hip bridge / boots (h <= 135)
        v_match = re.search(r"body_(front|back|profile|threequarter)_(\d+)", iid)
        v_label = v_match.group(1).title() if v_match else "Front"
        if h <= 140:
            if w >= 280:
                return "torsos_pelvis", f"Poet {v_label} Hip Bridge {idx:02d}"
            return "shoes_feet", f"Poet {v_label} Chelsea Boot {idx:02d}"
        if w <= 175 and h >= 200:
            limb_type = "Arm Segment" if w < 110 else "Leg Segment"
            return "limbs", f"Poet {v_label} {limb_type} {idx:02d}"
        return "torsos_pelvis", f"Poet {v_label} Torso / Pelvis {idx:02d}"

    # 2. Special handling for party.vintage_party.face-feet.male.png & female.png
    if src in ("party.vintage_party.face-feet.male.png", "party.vintage_party.face-feet.female.png"):
        gender = "Male Guest" if "male.png" in src else "Female Guest"
        if w >= 260 and h <= 105:
            return "eyes_brows", f"Vintage Party {gender} · Eye/Brow Strip {idx:02d}"
        if h <= 136 and w >= 165 and (w / max(1, h)) >= 1.35:
            return "eyes_brows", f"Vintage Party {gender} · Eye/Brow Patch {idx:02d}"
        if (130 <= w <= 190 and 95 <= h <= 160 and idx not in (19, 20, 21, 22, 23, 28, 29, 30, 36, 37, 38, 45, 46, 47)):
            return "mouths_noses", f"Vintage Party {gender} · Mouth Phoneme {idx:02d}"
        return "shoes_feet", f"Vintage Party {gender} · Dress Shoe / Heel {idx:02d}"

    # 3. Special handling for heads-hands / faces-hands in BL catalog
    if src in ("woman.09.mother.heads-hands.png", "parents.09.father_elder.heads-hands.png", "ghost_child.02.faces-hands.png"):
        char_lbl = item.get("character", "").split("(")[0].strip()
        if w >= 190 and h >= 215:
            return "heads", f"{char_lbl} · Head Plate {idx:02d}"
        if h <= 128 and (w / max(1, h)) >= 1.35:
            if h <= 65 or (w / max(1, h)) >= 2.2:
                return "eyes_brows", f"{char_lbl} · Eyebrow Pair {idx:02d}"
            if w >= 210:
                return "eyes_brows", f"{char_lbl} · Eye Pair {idx:02d}"
            return "mouths_noses", f"{char_lbl} · Mouth Patch {idx:02d}"
        return "hands", f"{char_lbl} · Expressive Hand {idx:02d}"

    # 4. Special handling for party.07.dj-guest.cap-noses-headphones.png
    if src == "party.07.dj-guest.cap-noses-headphones.png":
        if 6 <= idx <= 11:
            return "mouths_noses", f"DJ & Club Guest · Nose Patch {idx - 5:02d}"
        if idx <= 5:
            return "sunglasses_acc", f"DJ Cyber · Cap Turnaround {idx:02d}"
        return "sunglasses_acc", f"DJ Cyber · Headphones {idx - 11:02d}"

    # 5. Direct category mapping for remaining clean BL categories
    cat_map = {
        "hands": "hands",
        "shoes": "shoes_feet",
        "heads": "heads",
        "eyes": "eyes_brows",
        "noses": "mouths_noses",
        "mouths": "mouths_noses",
        "accessories": "sunglasses_acc",
        "torsos": "torsos_pelvis",
    }
    return cat_map.get(raw_cat, "torsos_pelvis"), name


def classify_release_sheet_part(sheet, part):
    """
    Classify a cut part from `release_catalog.json` into one of the 8 anatomical categories,
    returning `(category, descriptive_name, view_angle)` or `None` if it is a non-anatomical prop/label/frame.
    """
    sid = sheet["id"]
    sl = sid.lower()
    sub = sheet.get("subfolder", "")
    kind = sheet.get("kind", "")
    p_idx = part["part_index"]
    role = part.get("role", "working_part")
    x, y, bw, bh = part.get("bbox_sheet", [0, 0, part["width"], part["height"]])
    w, h = part["width"], part["height"]
    aspect = float(bw) / max(1.0, float(bh))

    # Skip tiny text labels, thin horizontal divider banners, or huge multi-panel border frames
    if bw < 36 or bh < 28 or (bw * bh) < 1800:
        return None
    if bh <= 38 and aspect >= 3.2:
        return None
    if bw >= 520 and bh >= 250 and "main-poses" not in sl and "mainposes" not in sl:
        return None

    # Only process character core, actions/poses, and the 3 anatomical/wearable prop sheets
    if sub not in ("01_CHARACTER_CORE", "02_ACTIONS_AND_POSES") and sid not in (
        "04.props.poet-jointed-hands",
        "02.props.poet-eye-aperture",
        "13.props.personal",
    ):
        return None

    # Skip main-poses sheets (full assembled stage reference figures, unless torso-variants/torso-parts)
    if ("main-poses" in sl or "mainposes" in sl or kind in ("main_poses", "main_pose", "main_pose_reference")) and "torso" not in sl:
        return None

    # Prefix for human-readable naming
    base_title = re.sub(r"^\d{2}\.", "", sid).replace(".", " · ").replace("_", " ").title()
    v_angle = infer_view_angle(sid)

    # 1. Dedicated Prop Anatomical & Wearable Sheets
    if sid == "04.props.poet-jointed-hands":
        if role != "working_part":
            return None
        return ("hands", f"Poet Jointed Hand Mechanism · Part {p_idx:02d}", v_angle)
    if sid == "02.props.poet-eye-aperture":
        if role != "working_part":
            return None
        return ("eyes_brows", f"Poet Eye Aperture Close-Up · Part {p_idx:02d}", v_angle)
    if sid == "13.props.personal":
        if role != "working_part":
            return None
        if y < 280:
            va = "front" if x < 500 else ("threequarter" if x < 1000 else "profile")
            return ("sunglasses_acc", f"Poet P13 · Angular Sunglasses ({va.title()}) {p_idx:02d}", va)
        if y < 560:
            return ("sunglasses_acc", f"Woman / Muse P13 · Pearl Necklace Jewelry {p_idx:02d}", "front")
        return ("sunglasses_acc", f"Family / Elder P13 · Wood Bead Rosary & Cross {p_idx:02d}", "front")

    # 2. Dedicated Hands Sheets
    if any(sl.endswith(sfx) for sfx in [".hands", ".hands-completion", ".hands-pocket", ".action-hands"]):
        if bw > 450 and bh > 450:
            return None
        va = "profile" if x >= 950 else ("threequarter" if 500 <= x < 950 else "front")
        return ("hands", f"{base_title} · Hand {p_idx:02d}", va)

    # 3. Dedicated Feet / Boots Sheets
    if sl.endswith(".feet"):
        v_map = {1: "profile", 2: "profile", 3: "profile", 4: "front", 5: "front", 6: "threequarter"}
        return ("shoes_feet", f"{base_title} · Shoe/Boot {p_idx:02d}", v_map.get(p_idx, v_angle))

    # 4. Dedicated Heads / Head-Turn Sheets
    if any(sl.endswith(sfx) for sfx in [".heads", ".crowd-head-variants", ".watcher-head-turns"]):
        if bh < 95:
            return None
        v_turn = infer_view_angle(sid, index_hint=(p_idx % 5) + 1, total_hint=5)
        return ("heads", f"{base_title} · Head Turn {p_idx:02d}", v_turn)

    # 5. Dedicated Noses Sheet
    if sl.endswith(".noses"):
        if bh < 50:
            return None
        va = "front" if x < 500 else ("threequarter" if x < 1000 else "profile")
        return ("mouths_noses", f"{base_title} · Nose Patch {p_idx:02d}", va)

    # 6. Dedicated Wings Sheet
    if sl.endswith(".wings"):
        if role != "working_part":
            return None
        va = "front" if x < 500 else ("threequarter" if x < 1000 else "back")
        return ("sunglasses_acc", f"{base_title} · Wing Segment {p_idx:02d}", va)

    # 7. DJ Cap / Noses / Headphones Sheet
    if sid == "party.07.dj-guest.cap-noses-headphones":
        if y < 250:
            v_turn = infer_view_angle(sid, index_hint=p_idx, total_hint=5)
            return ("sunglasses_acc", f"DJ Cyber · Black Baseball Cap ({v_turn.title()})", v_turn)
        if y < 520:
            va = "front" if p_idx in (6, 9) else ("threequarter" if p_idx in (7, 10) else "profile")
            return ("mouths_noses", f"DJ & Club Guest · Nose Patch {p_idx - 5:02d}", va)
        va = "front" if p_idx == 12 else ("threequarter" if p_idx == 13 else "profile")
        return ("sunglasses_acc", f"DJ Cyber · Studio Headphones {p_idx - 11:02d}", va)

    # 8. Dedicated Hipcore Sheets
    if sl.endswith(".hipcore"):
        if role != "working_part":
            return None
        hip_names = {
            1: ("Torso — Front", "front"),
            2: ("Torso — Back", "back"),
            3: ("Rear Seat Cover", "back"),
            4: ("Waist Link", "front"),
            5: ("Hip Bridge (3 Pivots)", "front"),
        }
        lbl, va = hip_names.get(p_idx, (f"Pelvis/Hip Component {p_idx:02d}", v_angle))
        return ("torsos_pelvis", f"{base_title} · {lbl}", va)

    # 9. Face Front & Face Profile 27-part Sheets (`*.face.front`, `*.face.profile`)
    if sl.endswith(".face.front") or sl.endswith(".face.profile"):
        va = "profile" if sl.endswith(".profile") else "front"
        if bh >= 260 and x < 120:
            return ("heads", f"{base_title} · Blank Head Base ({va.title()})", va)
        if y < 290:
            return ("eyes_brows", f"{base_title} · Eye Variant {p_idx - 1:02d}", va)
        if y < 450:
            return ("eyes_brows", f"{base_title} · Eyebrow Variant {p_idx - 9:02d}", va)
        if sl.endswith(".face.profile") and y < 600:
            return ("mouths_noses", f"{base_title} · Profile Nose/Feature {p_idx - 15:02d}", va)
        return ("mouths_noses", f"{base_title} · Mouth Phoneme {p_idx:02d}", va)

    # 10. Poem 12 / 13 Faces Sheets (`poet.12.faces`, `poet.13.faces`)
    if sl in ("poet.12.faces", "poet.13.faces"):
        if x < 400 and bh >= 280:
            va = "front" if y < 350 else "threequarter"
            return ("heads", f"{base_title} · Blank Head Mask ({va.title()})", va)
        if x < 720 and bh >= 130:
            return ("heads", f"{base_title} · Expression Head Study {p_idx:02d}", "front")
        if 720 <= x < 980:
            return ("eyes_brows", f"{base_title} · Eyes Strip {p_idx:02d}", "front")
        if 980 <= x < 1250:
            return ("eyes_brows", f"{base_title} · Eyebrows Strip {p_idx:02d}", "front")
        return ("mouths_noses", f"{base_title} · Mouth Patch {p_idx:02d}", "front")

    # 11. Poem 14 Faces + Door Hands (`poet.14.faces-hands`)
    if sl == "poet.14.faces-hands":
        if x < 240 and bh >= 450:
            return None  # Combined 5-head reference column
        if x >= 980 and y < 400 and bh >= 250:
            va = "front" if x < 1150 else "threequarter"
            return ("heads", f"Poet P14 · Blank Head Plate ({va.title()})", va)
        if x >= 980 and 450 <= y <= 700 and bw >= 320:
            return ("sunglasses_acc", f"Poet P14 · Sunglasses Variant {p_idx:02d}", "front")
        if y >= 730:
            if bw <= 115 and bh <= 115 and x >= 1350:
                return None  # Door knob prop
            return ("hands", f"Poet P14 · Door Action Hand {p_idx - 20:02d}", "front")
        if 240 <= x < 480:
            return ("eyes_brows", f"Poet P14 · Eyes Strip {p_idx:02d}", "front")
        if 480 <= x < 710:
            return ("eyes_brows", f"Poet P14 · Eyebrows Strip {p_idx:02d}", "front")
        return ("mouths_noses", f"Poet P14 · Mouth Patch {p_idx:02d}", "front")

    # 12. Ancestor Identity Sheets (`ancestors.05.identities.01/02/03`)
    if "ancestors.05.identities" in sl:
        if bh >= 190:
            va = "front" if x < 220 else ("threequarter" if x < 440 else ("profile" if x < 700 else "back"))
            return ("heads", f"{base_title} · Ancestor Head {p_idx:02d}", va)
        if x < 900:
            return ("eyes_brows", f"{base_title} · Eye Patch {p_idx:02d}", "front")
        if x < 1120:
            return ("eyes_brows", f"{base_title} · Eyebrow Patch {p_idx:02d}", "front")
        return ("mouths_noses", f"{base_title} · Mouth Patch {p_idx:02d}", "front")

    # 13. Atlantis Shared Features + Hands (`atlantis.06.shared-features-hands`)
    if sl == "atlantis.06.shared-features-hands":
        if y < 600:
            if x < 550:
                return ("eyes_brows", f"Atlantis Shared · Eye Patch {p_idx:02d}", "front")
            if x < 1150:
                return ("eyes_brows", f"Atlantis Shared · Eyebrow Patch {p_idx:02d}", "front")
            return ("mouths_noses", f"Atlantis Shared · Mouth Patch {p_idx:02d}", "front")
        return ("hands", f"Atlantis Shared · Expressive Hand {p_idx - 15:02d}", "front")

    # 14. Multi-Category Heads-Hands & Faces-Hands Sheets (`*.heads-hands`, `*.faces-hands`)
    if sl.endswith(".heads-hands") or sl.endswith(".faces-hands"):
        if role != "working_part" and (bw >= 185 and bh >= 200):
            return None
        if y < 320 and bh >= 175:
            va = infer_view_angle(sid, index_hint=p_idx, total_hint=5)
            return ("heads", f"{base_title} · Blank Head ({va.title()})", va)
        if y >= 680 or (y >= 540 and bh >= 130 and bw <= 260):
            va = "front" if x < 500 else ("threequarter" if x < 950 else "profile")
            return ("hands", f"{base_title} · Hand Gesture {p_idx:02d}", va)
        if bh <= 58 or aspect >= 2.15:
            return ("eyes_brows", f"{base_title} · Eyebrow Patch {p_idx:02d}", "front")
        if y < 500 or (bw <= 135 and bh <= 90):
            return ("eyes_brows", f"{base_title} · Eye Patch {p_idx:02d}", "front")
        return ("mouths_noses", f"{base_title} · Mouth Patch {p_idx:02d}", "front")

    # 15. Multi-Category Face-Feet Sheets (`*.face-feet`, `*.face-feet.male`, `*.face-feet.female`)
    if ".face-feet" in sl:
        if (y >= 640 and bh >= 130) or (y >= 470 and x >= 880 and bh >= 135):
            va = "front" if x < 420 else ("profile" if x < 1050 else "threequarter")
            return ("shoes_feet", f"{base_title} · Shoe / Foot {p_idx:02d}", va)
        if y < 240:
            return ("eyes_brows", f"{base_title} · Eye Pair {p_idx:02d}", "front")
        if y < 400:
            return ("eyes_brows", f"{base_title} · Eyebrow Pair {p_idx:02d}", "front")
        return ("mouths_noses", f"{base_title} · Mouth Phoneme {p_idx:02d}", "front")

    # 16. Standard Body Turnaround Sheets (`*.body.front`, `*.body.back`, `*.body.threequarter*`, `*.body.profile`)
    if any(sfx in sl for sfx in [".body.front", ".body.back", ".body.threequarter", ".body.profile"]):
        if "vintage_party.body.profile" in sl:
            if x < 220 and bh >= 300:
                return ("torsos_pelvis", f"{base_title} · Profile Torso {p_idx:02d}", "profile")
            if x >= 1050 and bh <= 230:
                if bh >= 180 and x >= 1400:
                    return ("torsos_pelvis", f"{base_title} · Profile Pelvis/Seat {p_idx:02d}", "profile")
                return ("shoes_feet", f"{base_title} · Profile Shoe {p_idx:02d}", "profile")
            if 580 <= x <= 710 and bh <= 280:
                return ("hands", f"{base_title} · Profile Hand {p_idx:02d}", "profile")
            return ("limbs", f"{base_title} · Profile Limb Segment {p_idx:02d}", "profile")

        if "vintage_party.body." in sl:
            if bh >= 260 and bw >= 180 and x < 300:
                return ("torsos_pelvis", f"{base_title} · Torso {p_idx:02d}", v_angle)
            if 340 <= y <= 500 and bw >= 140 and bh <= 160:
                return ("torsos_pelvis", f"{base_title} · Hip/Pelvis {p_idx:02d}", v_angle)
            if aspect <= 0.55 and bh >= 190:
                return ("limbs", f"{base_title} · Limb Segment {p_idx:02d}", v_angle)
            if y >= 700 and bh <= 185:
                return ("shoes_feet", f"{base_title} · Shoe {p_idx:02d}", v_angle)
            if 150 <= bh <= 215 and bw <= 135:
                return ("hands", f"{base_title} · Hand {p_idx:02d}", v_angle)
            return ("torsos_pelvis", f"{base_title} · Garment/Body {p_idx:02d}", v_angle)

        if sl.endswith(".body.profile"):
            if p_idx == 1:
                return ("torsos_pelvis", f"{base_title} · Profile Torso", "profile")
            if p_idx == 6:
                return ("hands", f"{base_title} · Profile Hand", "profile")
            if p_idx == 7:
                return ("shoes_feet", f"{base_title} · Profile Boot/Shoe", "profile")
            return ("limbs", f"{base_title} · Profile Limb {p_idx:02d}", "profile")

        # 13-part (or 14-part EX with vape pen) front / back / 3Q sheet
        if p_idx == 1:
            return ("torsos_pelvis", f"{base_title} · Torso", v_angle)
        if p_idx in (2, 3, 4, 5):
            limb_lbl = "Upper Arm" if p_idx in (2, 4) else "Forearm"
            side_lbl = "R" if p_idx in (2, 3) else "L"
            return ("limbs", f"{base_title} · {limb_lbl} {side_lbl}", v_angle)
        if p_idx in (6, 7):
            side_lbl = "R" if p_idx == 6 else "L"
            return ("hands", f"{base_title} · Hand {side_lbl}", v_angle)
        if p_idx in (8, 9, 10, 11):
            limb_lbl = "Thigh" if p_idx in (8, 10) else "Shin"
            side_lbl = "R" if p_idx in (8, 9) else "L"
            return ("limbs", f"{base_title} · {limb_lbl} {side_lbl}", v_angle)
        if "ex_jacket" in sl and p_idx == 12 and bw < 100 and bh < 120:
            return ("sunglasses_acc", f"{base_title} · Vape Pen Prop", v_angle)
        return ("shoes_feet", f"{base_title} · Boot/Shoe {p_idx:02d}", v_angle)

    # 17. Compact-Core 14-to-19-Part Sheets (`*.compact-core`, `poet_soul.08.core`)
    if sl.endswith(".compact-core") or sl == "poet_soul.08.core":
        if y < 340 and bw >= 180:
            va = "back" if (360 <= x <= 750 or x >= 1100) else "front"
            return ("torsos_pelvis", f"{base_title} · Core Torso/Pelvis {p_idx:02d}", va)
        if y >= 700 and bh <= 190:
            return ("shoes_feet", f"{base_title} · Shoe/Foot {p_idx:02d}", v_angle)
        return ("limbs", f"{base_title} · Limb Capsule {p_idx:02d}", v_angle)

    # 18. Multi-View Character `.body` Sheets (`woman.09.mother.body`, `08.cast.*.body`, `family.12.*.body`, `family.13.*.body`, `ancestors.05.*.body`, `atlantis.06.*.body`, `parents.*.body`, `woman.13.body`)
    if sl.endswith(".body"):
        col_va = "front" if x < 260 else ("threequarter" if x < 520 else ("profile" if x < 760 else "back"))
        if aspect <= 0.56 and bh >= 195:
            return ("limbs", f"{base_title} · Limb Capsule {p_idx:02d}", col_va)
        if y < 440 and bw >= 120:
            va = "front" if x < 260 else ("back" if (260 <= x < 500 and "08.cast" not in sl) else col_va)
            return ("torsos_pelvis", f"{base_title} · Torso/Pelvis {p_idx:02d}", va)
        if bh >= 195 and bw >= 185 and y < 720:
            return ("torsos_pelvis", f"{base_title} · Garment Overlay {p_idx:02d}", col_va)
        if y >= 460 and bh <= 265:
            va = "front" if x < 450 else ("profile" if x < 950 else "threequarter")
            return ("shoes_feet", f"{base_title} · Shoe/Foot {p_idx:02d}", va)
        return ("torsos_pelvis", f"{base_title} · Body Component {p_idx:02d}", col_va)

    # 19. Master Sheets (`poet.red_black_sunglasses.master`, `ex.ex_jacket.master`, `party.vintage_party.master`)
    if sl.endswith(".master"):
        if role != "working_part":
            return None
        va = "back" if "ex_jacket" in sl else v_angle
        if aspect <= 0.56 and bh >= 175:
            return ("limbs", f"{base_title} · Limb {p_idx:02d}", va)
        if bh >= 240 and bw >= 160:
            return ("torsos_pelvis", f"{base_title} · Torso/Body {p_idx:02d}", va)
        if bh <= 145 and bw <= 145:
            return ("hands", f"{base_title} · Hand/Detail {p_idx:02d}", va)
        return ("shoes_feet", f"{base_title} · Boot/Part {p_idx:02d}", va)

    # 20. Torso Variants & Chest-Sleeves (`poet_soul.08.torso-variants`, `poet.04.chest-sleeves`, `*.torso-parts`)
    if "torso-variants" in sl or "chest-sleeves" in sl or "torso-parts" in sl:
        if role != "working_part":
            return None
        va = "front" if x < 420 else ("threequarter" if x < 820 else ("profile" if x < 1180 else "back"))
        if aspect <= 0.56 and bh >= 170:
            return ("limbs", f"{base_title} · Sleeve/Arm {p_idx:02d}", va)
        return ("torsos_pelvis", f"{base_title} · Torso Variant {p_idx:02d}", va)

    # 21. Replacement Continuation & Action Part Sheets
    if role != "working_part":
        return None

    va = "back" if ("ex." in sl or "exit" in sl or "back_lying" in sl) else (
        "profile" if ("side_lying" in sl or "crouch" in sl or "kneeling" in sl or "lean" in sl) else v_angle
    )

    if "poet" in sl and bw >= 145 and 42 <= bh <= 75 and aspect >= 2.3:
        return ("sunglasses_acc", f"{base_title} · Sunglasses {p_idx:02d}", va)
    if ("reserve" in sl or "window-action" in sl or "action" in sl) and bw >= 175 and bh >= 200 and (
        (x < 260 and y < 220 and "reserve" in sl)
        or (x < 240 and y < 200 and "window-action" in sl)
        or (x >= 1100 and y >= 400)
    ):
        return ("heads", f"{base_title} · Action Head {p_idx:02d}", va)
    if aspect <= 0.62 and bh >= 135 and bw <= 165:
        return ("limbs", f"{base_title} · Action Limb {p_idx:02d}", va)
    if bw >= 145 and bh >= 175 and y < 380:
        return ("torsos_pelvis", f"{base_title} · Action Torso {p_idx:02d}", va)
    if bw >= 120 and 75 <= bh <= 185 and aspect >= 1.15 and y < 560:
        return ("torsos_pelvis", f"{base_title} · Hip/Pelvis {p_idx:02d}", va)
    if y >= 520 and bw >= 125 and bh <= 230 and aspect >= 0.82:
        return ("shoes_feet", f"{base_title} · Action Boot/Shoe {p_idx:02d}", va)
    if bw <= 160 and bh <= 200:
        return ("hands", f"{base_title} · Action Hand {p_idx:02d}", va)

    return ("torsos_pelvis", f"{base_title} · Action Body Part {p_idx:02d}", va)


def main():
    with open(BODY_LAB_CAT_PATH) as f:
        bl_cat = json.load(f)
    with open(RELEASE_CAT_PATH) as f:
        rel_cat = json.load(f)
    with open(FACES_CAT_PATH) as f:
        faces_cat = json.load(f)
    with open(TRACKSUIT_MANIFEST_PATH) as f:
        ts_manifest = json.load(f)
    with open(WEAVE_CAST_PATH) as f:
        weave_cast = json.load(f)
    with open(WEAVE_LIB_PATH) as f:
        weave_lib = json.load(f)

    # Index weave library pieces by file path relative to `shots/` for calibrated pivots/brads
    weave_pivots_by_file = {}
    for pid, pdata in weave_lib.get("pieces", {}).items():
        wfile = "weave/" + pdata["file"].lstrip("/")
        pivs = []
        if "pivot" in pdata and isinstance(pdata["pivot"], list) and len(pdata["pivot"]) == 2:
            pivs.append({"x": float(pdata["pivot"][0]), "y": float(pdata["pivot"][1]), "r": 8.0, "id": "pivot"})
        for b_idx, brad in enumerate(pdata.get("brads", [])[:4]):
            c = brad.get("center", [0, 0])
            pivs.append({"x": float(c[0]), "y": float(c[1]), "r": 6.5, "id": f"brad_{b_idx+1}"})
        weave_pivots_by_file[wfile] = pivs

    # Also index weave/cast/man/cast.json parts (20 core rig parts with named sockets!)
    cast_parts_by_file = {}
    for pid, pdata in weave_cast.get("parts", {}).items():
        cfile = "weave/" + pdata["file"].lstrip("/")
        pivs = []
        for sname, scoord in pdata.get("sockets", {}).items():
            pivs.append({"x": float(scoord[0]), "y": float(scoord[1]), "r": 8.5, "id": sname})
        if not pivs and "pivot" in pdata:
            pivs.append({"x": float(pdata["pivot"][0]), "y": float(pdata["pivot"][1]), "r": 8.5, "id": "pivot"})
        cast_parts_by_file[cfile] = (pid, pdata, pivs)

    unified_parts = []
    seen_files = set()
    seen_ids = set()

    def add_part(item):
        f_rel = to_shots_rel(item["file"])
        abs_p = os.path.join(SHOTS_ROOT, f_rel)
        if not os.path.exists(abs_p):
            return
        uid = item["id"]
        if uid in seen_ids:
            idx = 2
            while f"{uid}_{idx}" in seen_ids:
                idx += 1
            uid = f"{uid}_{idx}"
        seen_ids.add(uid)
        seen_files.add(f_rel)
        item["id"] = uid
        item["file"] = f_rel
        unified_parts.append(item)

    # =========================================================================
    # 1. All 31 Poet Tracksuit Components (`shots/kits/packs/poet_tracksuit_v1/`)
    # =========================================================================
    print("1. Adding 31 Poet Tracksuit v1 components with calibrated brass pivots...")
    for comp in ts_manifest.get("components", []):
        cid = comp["id"]
        label = comp["label"]
        f_rel = f"kits/packs/poet_tracksuit_v1/{comp['file']}"
        if not os.path.exists(os.path.join(SHOTS_ROOT, f_rel)):
            f_rel = f"arena/parts/kit3/release_v2/tracksuit/{cid}.png"
        w, h = comp["dimensions_px"]
        vbbox = comp.get("visible_bbox_alpha128_px", [0, 0, w, h])
        cat, v_angle = TRACKSUIT_CATEGORY_MAP.get(cid, ("torsos_pelvis", "front"))
        pivs = TRACKSUIT_CALIBRATED_PIVOTS.get(cid, [])
        src_sheets = comp.get("source_files", [])
        sheet_f = f"kits/packs/poet_tracksuit_v1/{src_sheets[0]}" if src_sheets else f_rel
        norm_scale = compute_normalized_scale(cat, w, h, "Poet", label, visible_bbox=vbbox)
        add_part({
            "id": f"poet.tracksuit.{cid}",
            "name": f"Poet Tracksuit · {label}",
            "category": cat,
            "character_group": "Poet",
            "poems": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            "view_angle": v_angle,
            "file": f_rel,
            "sheet_file": sheet_f,
            "bbox_sheet": vbbox,
            "width": int(w),
            "height": int(h),
            "pivots": pivs,
            "normalized_scale": norm_scale,
            "source_origin": "poet_tracksuit_v1",
        })

    # =========================================================================
    # 2. All 573 Isolated PNGs in `shots/arena/parts/body_lab/body_lab_catalog.json`
    # =========================================================================
    print("2. Adding all 573 isolated PNGs from body_lab_catalog.json...")
    for raw_cat, items in bl_cat.items():
        for item in items:
            f_rel = to_shots_rel(item["path"])
            cat, clean_name = classify_body_lab_catalog_item(item)
            c_group = infer_character_group(f"{item.get('character', '')} {item.get('source', '')}")
            poems = infer_poems_from_group_and_text(c_group, f"{item.get('source', '')} {item.get('id', '')}")
            v_angle = infer_view_angle(f"{item.get('id', '')} {clean_name} {item.get('source', '')}")
            w = int(item.get("width", 100))
            h = int(item.get("height", 100))
            pivs = weave_pivots_by_file.get(f_rel, [])
            norm_scale = compute_normalized_scale(cat, w, h, c_group, clean_name)
            add_part({
                "id": item["id"],
                "name": clean_name,
                "category": cat,
                "character_group": c_group,
                "poems": poems,
                "view_angle": v_angle,
                "file": f_rel,
                "sheet_file": item.get("source", f_rel),
                "bbox_sheet": [0, 0, w, h],
                "width": w,
                "height": h,
                "pivots": pivs,
                "normalized_scale": norm_scale,
                "source_origin": "body_lab_573",
            })

    # =========================================================================
    # 3. Calibrated Weave Man Rig Parts (`shots/weave/cast/man/cast.json` & `library_manifest.json`)
    # =========================================================================
    print("3. Adding Weave Man calibrated cast.json & library_manifest.json parts...")
    for cfile, (pid, pdata, pivs) in cast_parts_by_file.items():
        if cfile in seen_files:
            continue
        w, h = pdata.get("size", [150, 250])
        if pid.startswith("torso") or pid.startswith("pelvis"):
            cat = "torsos_pelvis"
        elif any(pid.startswith(k) for k in ["uarm", "farm", "thigh", "shin"]):
            cat = "limbs"
        elif pid.startswith("hand"):
            cat = "hands"
        elif pid.startswith("boot"):
            cat = "shoes_feet"
        else:
            cat = "heads"
        v_angle = infer_view_angle(pid)
        clean_name = f"Poet Weave Rig · {pid.replace('.', ' ').replace('_', ' ').title()}"
        norm_scale = compute_normalized_scale(cat, w, h, "Poet", clean_name)
        add_part({
            "id": f"weave_rig_{pid}",
            "name": clean_name,
            "category": cat,
            "character_group": "Poet",
            "poems": list(range(1, 15)),
            "view_angle": v_angle,
            "file": cfile,
            "sheet_file": f"weave/cast/man/{pdata.get('sheet', 'cast.json')}",
            "bbox_sheet": pdata.get("box", [0, 0, w, h]),
            "width": int(w),
            "height": int(h),
            "pivots": pivs,
            "normalized_scale": norm_scale,
            "source_origin": "weave_cast_rig",
        })

    # Also include any contact arms/grips, run/stair/jump legs, and wearable/handheld accessories from weave/library_manifest.json
    wearable_props = {
        "prop.headphones",
        "prop.microphone",
        "prop.phone",
        "prop.pen",
        "prop.notebook.closed",
        "prop.notebook.open",
        "prop.folded_note",
    }
    for pid, pdata in weave_lib.get("pieces", {}).items():
        wfile = "weave/" + pdata["file"].lstrip("/")
        if wfile in seen_files:
            continue
        lcat = pdata.get("category", "")
        if lcat not in ("contact", "leg") and pid not in wearable_props:
            continue
        w, h = pdata.get("size", [150, 200])
        if pid in wearable_props:
            cat = "sunglasses_acc"
        elif pid.startswith("arm."):
            cat = "limbs"
        elif pid.startswith("grip."):
            cat = "hands"
        elif pid.startswith("leg."):
            cat = "limbs" if h >= 220 else "shoes_feet"
        else:
            continue
        v_angle = infer_view_angle(pid)
        clean_name = f"Poet Weave · {pid.replace('.', ' ').replace('_', ' ').title()}"
        pivs = weave_pivots_by_file.get(wfile, [])
        norm_scale = compute_normalized_scale(cat, w, h, "Poet", clean_name)
        add_part({
            "id": f"weave_lib_{pid}",
            "name": clean_name,
            "category": cat,
            "character_group": "Poet",
            "poems": list(range(1, 15)),
            "view_angle": v_angle,
            "file": wfile,
            "sheet_file": f"weave/cast/man/{pdata.get('source_sheet', 'library')}",
            "bbox_sheet": [0, 0, int(w), int(h)],
            "width": int(w),
            "height": int(h),
            "pivots": pivs,
            "normalized_scale": norm_scale,
            "source_origin": "weave_library",
        })

    # =========================================================================
    # 4. Character Faces Catalog Explicit Turnaround Views (`character_faces_catalog.json`)
    # =========================================================================
    print("4. Checking character_faces_catalog.json turnaround views & base heads...")
    # Ensure base profile heads in poet_tracksuit_v1 & young_poet_v1 are included
    for base_head_rel, c_grp, p_list, h_lbl in [
        ("kits/packs/poet_tracksuit_v1/01_COMPONENTS/profile_face_clean/00_base_profile_head.png", "Poet", list(range(1, 15)), "Poet Tracksuit · Blank Profile Head Base"),
        ("kits/packs/young_poet_v1/01_COMPONENTS/profile_face_clean/00_base_profile_head.png", "Child / Ghost", [2, 13], "Young Poet (Age 6) · Blank Profile Head Base"),
    ]:
        abs_bh = os.path.join(SHOTS_ROOT, base_head_rel)
        if os.path.exists(abs_bh) and base_head_rel not in seen_files:
            im = Image.open(abs_bh)
            w, h = im.width, im.height
            add_part({
                "id": f"face_base_{c_grp.lower().split()[0]}_profile",
                "name": h_lbl,
                "category": "heads",
                "character_group": c_grp,
                "poems": p_list,
                "view_angle": "profile",
                "file": base_head_rel,
                "sheet_file": base_head_rel,
                "bbox_sheet": [0, 0, w, h],
                "width": w,
                "height": h,
                "pivots": [{"x": round(w * 0.48, 1), "y": round(h * 0.86, 1), "r": 16.0, "id": "neck"}],
                "normalized_scale": compute_normalized_scale("heads", w, h, c_grp, h_lbl),
                "source_origin": "character_faces_catalog",
            })

    # =========================================================================
    # 5. All Anatomical & Wardrobe Parts across all 14 Poems (`release_catalog.json`)
    # =========================================================================
    print("5. Classifying and adding anatomical & wardrobe parts across all 14 poems from release_catalog.json...")
    for sheet in rel_cat.get("sheets", []):
        sid = sheet["id"]
        c_group = infer_character_group(sid)
        poems = sheet.get("poems") or infer_poems_from_group_and_text(c_group, sid)
        sheet_file = to_shots_rel(sheet.get("sheet_rel", f"arena/parts/kit3/release_v2/sheets/{sid}.png"))

        for part in sheet.get("parts", []):
            res = classify_release_sheet_part(sheet, part)
            if res is None:
                continue
            cat, clean_name, v_angle = res
            f_rel = to_shots_rel(part["file"])
            if f_rel in seen_files:
                continue
            w = int(part["width"])
            h = int(part["height"])
            # Filter clean brass pivots
            raw_pivs = part.get("pivots", [])
            clean_pivs = [
                {"x": float(p["x"]), "y": float(p["y"]), "r": float(p.get("r", 8.0)), "id": f"piv_{i+1}"}
                for i, p in enumerate(raw_pivs)
                if 3.0 <= float(p.get("r", 8.0)) <= 22.0
            ][:8]
            norm_scale = compute_normalized_scale(cat, w, h, c_group, clean_name)
            add_part({
                "id": part["id"],
                "name": clean_name,
                "category": cat,
                "character_group": c_group,
                "poems": poems,
                "view_angle": v_angle,
                "file": f_rel,
                "sheet_file": sheet_file,
                "bbox_sheet": part.get("bbox_sheet", [0, 0, w, h]),
                "width": w,
                "height": h,
                "pivots": clean_pivs,
                "normalized_scale": norm_scale,
                "source_origin": "release_v2_cuts",
            })

    # Organize into categories and compute summary statistics
    by_category = {c: [] for c in CATEGORIES}
    by_char_group = {g: 0 for g in CHARACTER_GROUPS}
    by_view_angle = {v: 0 for v in VIEW_ANGLES}
    by_poem = {f"P{i:02d}": 0 for i in range(1, 15)}

    for p in unified_parts:
        by_category[p["category"]].append(p)
        by_char_group[p["character_group"]] = by_char_group.get(p["character_group"], 0) + 1
        by_view_angle[p["view_angle"]] = by_view_angle.get(p["view_angle"], 0) + 1
        for pm in p.get("poems", []):
            if 1 <= int(pm) <= 14:
                by_poem[f"P{int(pm):02d}"] += 1

    cat_counts = {c: len(by_category[c]) for c in CATEGORIES}

    unified_payload = {
        "version": "v2.0-body-lab-unified",
        "total_parts": len(unified_parts),
        "reference_torso_height_px": 240,
        "category_counts": cat_counts,
        "character_group_counts": by_char_group,
        "view_angle_counts": by_view_angle,
        "poem_counts": by_poem,
        "categories": by_category,
        "parts": unified_parts,
    }

    os.makedirs(os.path.dirname(OUT_UNIFIED_PATH), exist_ok=True)
    with open(OUT_UNIFIED_PATH, "w") as f:
        json.dump(unified_payload, f, indent=2)

    print("\n=== WYGWYL UNIFIED BODY LAB CATALOG BUILT ===")
    print(f"Output: {OUT_UNIFIED_PATH}")
    print(f"Total Unified Anatomical & Wardrobe Parts: {len(unified_parts)}")
    print("\n--- Breakdown by 8 Anatomical Categories ---")
    for c in CATEGORIES:
        print(f"  • {c:16s}: {cat_counts[c]:4d} parts")
    print("\n--- Breakdown by 7 Character Groups ---")
    for g in CHARACTER_GROUPS:
        print(f"  • {g:22s}: {by_char_group[g]:4d} parts")
    print("\n--- Breakdown by 4 View Angles ---")
    for v in VIEW_ANGLES:
        print(f"  • {v:16s}: {by_view_angle[v]:4d} parts")
    print("\n--- Breakdown by Poem (P01-P14) ---")
    print("  " + ", ".join(f"{k}:{v}" for k, v in by_poem.items()))


if __name__ == "__main__":
    main()
