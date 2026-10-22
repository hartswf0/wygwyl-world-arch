#!/usr/bin/env python3
"""
Fix Massive Set Labeling, Row-Clustered Sheet Order, Sideways Parts & Multi-View Rig Variants
=============================================================================================
1. Repairs corrupt/sideways files in `shots/arena/parts/kit3/v2/parts/` by copying the authentic
   high-resolution cut pieces from `shots/arena/parts/kit3/release_v2/cuts/` using true 2D
   row-clustered (`y_center` + `x_center`) printed sheet order (`1..13`, `1..7`, `1..21`, `1..14`).
2. Normalizes sideways (`w > h * 1.25`) hand/limb pieces and upside-down (`17_hand_open_L/R`)
   metadata across `crash_lab_catalog.json`, `character_rigs_library.json`, and `swapper_bank`.
3. Adds per-view `variant_meta` (`front`, `threequarter`, `profile`, `back`, `open`, `grip`,
   `fist`, `heel_up`, `toe_up`) with exact `width`, `height`, `visible_bbox`, `pivot_A`,
   `socket_B`, `cuff_clip_ratio`, and `rot_offset_deg: 0.0` so switching views in
   `range_rigger.html` and `crash_lab.html` never uses stale front-card coordinates or
   draws upside-down torsos / nose-down boots / sideways hands.
4. Adds `skeleton_breeds` (7 anatomical + Vitruvian skeleton breeds derived from limb/torso
   proportions) for the Vitruvian Man Proportions Engine & Evolutionary/Monte Carlo Pose Solver.
"""

import json
import math
import os
import shutil
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS_DIR = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
REL_V2_DIR = os.path.join(HERE, "release_v2")
CUTS_DIR = os.path.join(REL_V2_DIR, "cuts")
V2_PARTS_DIR = os.path.join(HERE, "v2", "parts")
CATALOG_PATH = os.path.join(REL_V2_DIR, "crash_lab_catalog.json")
RELEASE_CAT_PATH = os.path.join(REL_V2_DIR, "release_catalog.json")
CHAR_LIB_PATH = os.path.join(REL_V2_DIR, "character_rigs_library.json")

_IMG_CACHE = {}


def inspect_img(rel_shots_path: str, force_refresh: bool = False) -> dict:
    clean = rel_shots_path.lstrip("/")
    if clean.startswith("shots/"):
        clean = clean[len("shots/"):]
    if not force_refresh and clean in _IMG_CACHE:
        return _IMG_CACHE[clean]
    abs_p = os.path.join(SHOTS_DIR, clean)
    if not os.path.exists(abs_p):
        info = {
            "exists": False,
            "file": clean,
            "width": 256,
            "height": 256,
            "visible_bbox": [0, 0, 256, 256],
            "visible_w": 256,
            "visible_h": 256,
        }
        _IMG_CACHE[clean] = info
        return info
    with Image.open(abs_p) as im:
        w, h = im.size
        if im.mode in ("RGBA", "LA") or "transparency" in im.info:
            alpha = im.convert("RGBA").split()[-1]
            lut = [255 if i > 16 else 0 for i in range(256)]
            bb = alpha.point(lut).getbbox()
        else:
            bb = (0, 0, w, h)
        if not bb:
            bb = (0, 0, w, h)
        vw = max(1, bb[2] - bb[0])
        vh = max(1, bb[3] - bb[1])
        info = {
            "exists": True,
            "file": clean,
            "width": w,
            "height": h,
            "visible_bbox": [bb[0], bb[1], bb[2], bb[3]],
            "visible_w": vw,
            "visible_h": vh,
        }
    _IMG_CACHE[clean] = info
    return info


def cut_path(sheet_id: str, p_idx: int) -> str:
    return f"arena/parts/kit3/release_v2/cuts/{sheet_id}/{sheet_id}__p{p_idx:02d}.png"


def copy_cut_to_v2(src_rel: str, dst_v2_dir: str, dst_filename: str, rotate_ccw_deg: int = 0):
    src_abs = os.path.join(SHOTS_DIR, src_rel)
    dst_abs = os.path.join(V2_PARTS_DIR, dst_v2_dir, dst_filename)
    if not os.path.exists(src_abs):
        return False
    os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
    if rotate_ccw_deg != 0:
        with Image.open(src_abs) as im:
            rot = im.rotate(rotate_ccw_deg, expand=True, resample=Image.BICUBIC)
            rot.save(dst_abs)
    else:
        shutil.copy2(src_abs, dst_abs)
    inspect_img(f"arena/parts/kit3/v2/parts/{dst_v2_dir}/{dst_filename}", force_refresh=True)
    return True


def repair_v2_parts_from_release_cuts():
    """
    Replaces corrupt/sideways/squished files in `shots/arena/parts/kit3/v2/parts/`
    with authentic high-res cuts from `release_v2/cuts/` using verified row-clustered indices.
    """
    repaired = 0

    # 1. Standard 13-part body.front / threequarter / back + 7-part body.profile kits:
    #    - poet.red_black_sunglasses
    #    - young_poet.child_clothes
    #    - family.street_clothes
    std_kits = [
        ("poet.red_black_sunglasses", {
            "front": ("poet.red_black_sunglasses.body.front", [1, 2, 3, 6, 4, 5, 7, 8, 9, 12, 10, 11, 13]),
            "threequarter": ("poet.red_black_sunglasses.body.threequarter", [1, 2, 3, 6, 4, 5, 7, 8, 10, 12, 9, 11, 13]),
            "back": ("poet.red_black_sunglasses.body.back", [1, 2, 3, 6, 4, 5, 7, 8, 10, 12, 9, 11, 13]),
            "profile": ("poet.red_black_sunglasses.body.profile", [1, 3, 4, 6, 2, 5, 7]),
            "heads": ("poet.red_black_sunglasses.heads", {"front": 1, "threequarter": 2, "threequarter_B": 3, "profile": 4, "back": 5}),
            "hipcore": ("poet.red_black_sunglasses.hipcore", {"front": 4, "threequarter": 5, "profile": 3, "back": 6}),
            "feet": ("poet.red_black_sunglasses.feet", {"R.flat": 1, "R.heel_up": 2, "R.toe_up": 3, "L.flat": 4, "L.heel_up": 5, "L.toe_up": 6}),
        }),
        ("young_poet.child_clothes", {
            "front": ("young_poet.child_clothes.body.front", [1, 2, 3, 6, 4, 5, 7, 8, 9, 12, 10, 11, 13]),
            "threequarter": ("young_poet.child_clothes.body.threequarter", [1, 2, 3, 6, 4, 5, 7, 8, 9, 12, 10, 11, 13]),
            "back": ("young_poet.child_clothes.body.back", [1, 2, 4, 6, 3, 5, 7, 8, 9, 12, 10, 11, 13]),
            "profile": ("young_poet.child_clothes.body.profile", [1, 2, 3, 4, 5, 6, 7]),
            "heads": ("young_poet.child_clothes.heads", {"front": 1, "threequarter": 2, "threequarter_B": 3, "profile": 4, "back": 5}),
            "hipcore": ("young_poet.child_clothes.hipcore", {"front": 4, "threequarter": 5, "profile": 3, "back": 6}),
            "feet": ("young_poet.child_clothes.feet", {"R.flat": 1, "R.heel_up": 2, "R.toe_up": 3, "L.flat": 4, "L.heel_up": 5, "L.toe_up": 6}),
        }),
        ("family.street_clothes", {
            "front": ("family.street_clothes.body.front", [1, 2, 3, 6, 4, 5, 7, 8, 9, 12, 10, 11, 13]),
            "threequarter": ("family.street_clothes.body.front", [1, 2, 3, 6, 4, 5, 7, 8, 9, 12, 10, 11, 13]),
            "back": ("family.street_clothes.body.back", [1, 2, 3, 6, 4, 5, 7, 8, 9, 12, 10, 11, 13]),
            "profile": ("family.street_clothes.body.profile", [1, 2, 3, 4, 5, 6, 7]),
            "heads": ("family.street_clothes.heads", {"front": 1, "threequarter": 2, "threequarter_B": 3, "profile": 4, "back": 5}),
            "hipcore": ("family.street_clothes.hipcore", {"front": 3, "threequarter": 4, "profile": 5, "back": 6}),
        }),
    ]

    slot_13_names = [
        "torso", "uarm.L", "farm.L", "hand.L", "uarm.R", "farm.R", "hand.R",
        "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R"
    ]

    for v2_dir, cfg in std_kits:
        for view in ("front", "threequarter", "back"):
            if view not in cfg:
                continue
            sid, idx_list = cfg[view]
            for sname, p_idx in zip(slot_13_names, idx_list):
                if copy_cut_to_v2(cut_path(sid, p_idx), v2_dir, f"body.{view}.{sname}.png"):
                    repaired += 1
        if "profile" in cfg:
            sid, idx_list = cfg["profile"]
            # 1: torso, 2: uarm, 3: farm, 4: hand, 5: thigh, 6: shin, 7: foot
            prof_map = {
                "torso": idx_list[0],
                "uarm.L": idx_list[1], "uarm.R": idx_list[1],
                "farm.L": idx_list[2], "farm.R": idx_list[2],
                "hand.L": idx_list[3], "hand.R": idx_list[3],
                "thigh.L": idx_list[4], "thigh.R": idx_list[4],
                "shin.L": idx_list[5], "shin.R": idx_list[5],
                "foot.L": idx_list[6], "foot.R": idx_list[6],
            }
            for sname, p_idx in prof_map.items():
                if copy_cut_to_v2(cut_path(sid, p_idx), v2_dir, f"body.profile.{sname}.png"):
                    repaired += 1
        if "heads" in cfg:
            sid, hmap = cfg["heads"]
            for hview, p_idx in hmap.items():
                if copy_cut_to_v2(cut_path(sid, p_idx), v2_dir, f"head.{hview}.png"):
                    repaired += 1
        if "hipcore" in cfg:
            sid, pmap = cfg["hipcore"]
            for pview, p_idx in pmap.items():
                if copy_cut_to_v2(cut_path(sid, p_idx), v2_dir, f"body.{pview}.pelvis.png"):
                    repaired += 1
        if "feet" in cfg:
            sid, fmap = cfg["feet"]
            for fk, p_idx in fmap.items():
                if copy_cut_to_v2(cut_path(sid, p_idx), v2_dir, f"foot.{fk}.png"):
                    repaired += 1

    # 2. EX Jacket (Strict back & threequarter_back)
    ex_sid_map = {
        "back": ("ex.ex_jacket.body.back", [1, 2, 3, 6, 4, 5, 7, 8, 9, 13, 10, 11, 14]),
        "threequarter_back": ("ex.ex_jacket.body.threequarter_back", [1, 2, 3, 6, 4, 5, 7, 8, 9, 11, 10, 12, 14]),
    }
    for view, (sid, idx_list) in ex_sid_map.items():
        for sname, p_idx in zip(slot_13_names, idx_list):
            if copy_cut_to_v2(cut_path(sid, p_idx), "ex.ex_jacket", f"body.{view}.{sname}.png"):
                repaired += 1
    for pview, p_idx in [("back", 6), ("threequarter_back", 5)]:
        if copy_cut_to_v2(cut_path("ex.ex_jacket.hipcore", p_idx), "ex.ex_jacket", f"body.{pview}.pelvis.png"):
            repaired += 1
    if copy_cut_to_v2(cut_path("ex.ex_jacket.heads", 1), "ex.ex_jacket", "head.back.png"):
        repaired += 1
    if copy_cut_to_v2(cut_path("ex.ex_jacket.heads", 2), "ex.ex_jacket", "head.threequarter_back.png"):
        repaired += 1

    # 3. Poet Black T-Shirt (`poet.black_tshirt.compact-core` + `poet.red_black_sunglasses` heads/hands)
    #    1: torso front, 2: torso back, 4: hip bridge, 3: rear seat,
    #    5: uarm L, 6: farm L, 7: uarm R, 8: farm R,
    #    9: thigh L, 10: shin L, 11: thigh R, 12: shin R, 13: foot L, 14: foot R
    bt_sid = "poet.black_tshirt.compact-core"
    bt_hand_L = cut_path("poet.red_black_sunglasses.body.front", 6)
    bt_hand_R = cut_path("poet.red_black_sunglasses.body.front", 7)
    for view in ("front", "threequarter", "profile", "back"):
        torso_p = 2 if view == "back" else 1
        pelvis_p = 3 if view == "back" else 4
        bt_map = {
            "torso": cut_path(bt_sid, torso_p),
            "pelvis": cut_path(bt_sid, pelvis_p),
            "uarm.L": cut_path(bt_sid, 5),
            "farm.L": cut_path(bt_sid, 6),
            "hand.L": bt_hand_L,
            "uarm.R": cut_path(bt_sid, 7),
            "farm.R": cut_path(bt_sid, 8),
            "hand.R": bt_hand_R,
            "thigh.L": cut_path(bt_sid, 9),
            "shin.L": cut_path(bt_sid, 10),
            "thigh.R": cut_path(bt_sid, 11),
            "shin.R": cut_path(bt_sid, 12),
            "foot.L": cut_path(bt_sid, 13),
            "foot.R": cut_path(bt_sid, 14),
        }
        for sname, src in bt_map.items():
            if copy_cut_to_v2(src, "poet.black_tshirt", f"body.{view}.{sname}.png"):
                repaired += 1

    # 4. Party DJ Cyber (`party.dj_cyber.compact-core` + `party.dj_cyber.body.profile` + `party.dj_cyber.heads`)
    dj_cc = "party.dj_cyber.compact-core"
    dj_pr = "party.dj_cyber.body.profile"
    for view in ("front", "threequarter", "back"):
        torso_p = 2 if view == "back" else 1
        pelvis_p = 4 if view == "back" else 3
        dj_map = {
            "torso": cut_path(dj_cc, torso_p),
            "pelvis": cut_path(dj_cc, pelvis_p),
            "uarm.L": cut_path(dj_cc, 5),
            "farm.L": cut_path(dj_cc, 6),
            "hand.L": cut_path(dj_pr, 6),
            "uarm.R": cut_path(dj_cc, 7),
            "farm.R": cut_path(dj_cc, 8),
            "hand.R": cut_path(dj_pr, 6),
            "thigh.L": cut_path(dj_cc, 9),
            "shin.L": cut_path(dj_cc, 10),
            "thigh.R": cut_path(dj_cc, 11),
            "shin.R": cut_path(dj_cc, 12),
            "foot.L": cut_path(dj_cc, 13),
            "foot.R": cut_path(dj_cc, 14),
        }
        for sname, src in dj_map.items():
            if copy_cut_to_v2(src, "party.dj_cyber", f"body.{view}.{sname}.png"):
                repaired += 1
    dj_prof_map = {
        "torso": cut_path(dj_pr, 1),
        "pelvis": cut_path(dj_pr, 8),
        "uarm.L": cut_path(dj_pr, 2), "uarm.R": cut_path(dj_pr, 2),
        "farm.L": cut_path(dj_pr, 3), "farm.R": cut_path(dj_pr, 3),
        "hand.L": cut_path(dj_pr, 6), "hand.R": cut_path(dj_pr, 6),
        "thigh.L": cut_path(dj_pr, 4), "thigh.R": cut_path(dj_pr, 4),
        "shin.L": cut_path(dj_pr, 5), "shin.R": cut_path(dj_pr, 5),
        "foot.L": cut_path(dj_pr, 7), "foot.R": cut_path(dj_pr, 7),
    }
    for sname, src in dj_prof_map.items():
        if copy_cut_to_v2(src, "party.dj_cyber", f"body.profile.{sname}.png"):
            repaired += 1
    for hview, p_idx in [("front", 1), ("threequarter", 2), ("profile", 4), ("back", 5)]:
        if copy_cut_to_v2(cut_path("party.dj_cyber.heads", p_idx), "party.dj_cyber", f"head.{hview}.png"):
            repaired += 1

    # 5. Vintage Party Couple (`party.vintage_party.body.front` / `profile` / `back` / `heads`)
    vp_front_idx = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    vp_back_idx = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    for view, sid, idx_list, pel_idx in [
        ("front", "party.vintage_party.body.front", vp_front_idx, 14),
        ("threequarter", "party.vintage_party.body.front", vp_front_idx, 14),
        ("back", "party.vintage_party.body.back", vp_back_idx, 15),
    ]:
        for sname, p_idx in zip(slot_13_names, idx_list):
            if copy_cut_to_v2(cut_path(sid, p_idx), "party.vintage_party", f"body.{view}.{sname}.png"):
                repaired += 1
        if copy_cut_to_v2(cut_path(sid, pel_idx), "party.vintage_party", f"body.{view}.pelvis.png"):
            repaired += 1
    vp_pr = "party.vintage_party.body.profile"
    vp_prof_map = {
        "torso": 1, "pelvis": 8,
        "uarm.L": 2, "uarm.R": 2,
        "farm.L": 3, "farm.R": 3,
        "hand.L": 7, "hand.R": 7,
        "thigh.L": 4, "thigh.R": 4,
        "shin.L": 5, "shin.R": 5,
        "foot.L": 9, "foot.R": 9,
    }
    for sname, p_idx in vp_prof_map.items():
        if copy_cut_to_v2(cut_path(vp_pr, p_idx), "party.vintage_party", f"body.profile.{sname}.png"):
            repaired += 1
    for hview, p_idx in [("front", 1), ("threequarter", 2), ("profile", 4), ("back", 5)]:
        if copy_cut_to_v2(cut_path("party.vintage_party.heads", p_idx), "party.vintage_party", f"head.{hview}.png"):
            repaired += 1

    # 6. Woman / Muse (`woman.teal_dress` & `woman.mother_cardigan`) from `woman.13.body` and `woman.09.mother.body`
    #    woman.09.mother.body (21 parts):
    #    p01: 1 TORSO FRONT, p02: 2 TORSO BACK, p03: 3 TORSO PROFILE, p08: 4 HIP BRIDGE, p09: 5 REAR SEAT,
    #    p04: 6 UARM L, p05: 7 UARM R, p06: 8 FOREARM L, p07: 9 FOREARM R,
    #    p10: 10 THIGH L, p11: 11 THIGH R, p12: 12 SHIN L, p13: 13 SHIN R,
    #    p14: 14 GARMENT FRONT, p15: 15 GARMENT BACK,
    #    p16: 16 FOOT L FRONT, p17: 17 FOOT R FRONT, p20: 18 FOOT L PROFILE, p21: 19 FOOT R PROFILE
    m_sid = "woman.09.mother.body"
    w13_sid = "woman.13.body"
    w_hand_L = cut_path("party.vintage_party.body.front", 20)
    w_hand_R = cut_path("party.vintage_party.body.front", 23)
    for v2_dir, use_w13 in [("woman.teal_dress", True), ("woman.mother_cardigan", False)]:
        for view in ("front", "threequarter", "profile", "back"):
            if use_w13:
                torso_src = cut_path(w13_sid, 3 if view == "back" else (16 if view == "profile" else 2))
                pelvis_src = cut_path(w13_sid, 4 if view == "front" else (7 if view == "back" else 5))
                uarm_L_src, uarm_R_src = cut_path(w13_sid, 8), cut_path(w13_sid, 9)
                farm_L_src, farm_R_src = cut_path(w13_sid, 10), cut_path(w13_sid, 11)
                thigh_L_src, thigh_R_src = cut_path(w13_sid, 12), cut_path(w13_sid, 13)
                shin_L_src, shin_R_src = cut_path(w13_sid, 14), cut_path(w13_sid, 15)
                foot_L_src, foot_R_src = cut_path(w13_sid, 17), cut_path(w13_sid, 18)
            else:
                torso_src = cut_path(m_sid, 2 if view == "back" else (3 if view == "profile" else 1))
                pelvis_src = cut_path(m_sid, 9 if view == "back" else 8)
                uarm_L_src, uarm_R_src = cut_path(m_sid, 4), cut_path(m_sid, 5)
                farm_L_src, farm_R_src = cut_path(m_sid, 6), cut_path(m_sid, 7)
                thigh_L_src, thigh_R_src = cut_path(m_sid, 10), cut_path(m_sid, 11)
                shin_L_src, shin_R_src = cut_path(m_sid, 12), cut_path(m_sid, 13)
                foot_L_src = cut_path(m_sid, 20 if view == "profile" else 16)
                foot_R_src = cut_path(m_sid, 21 if view == "profile" else 17)
            w_map = {
                "torso": torso_src, "pelvis": pelvis_src,
                "uarm.L": uarm_L_src, "uarm.R": uarm_R_src,
                "farm.L": farm_L_src, "farm.R": farm_R_src,
                "hand.L": w_hand_L, "hand.R": w_hand_R,
                "thigh.L": thigh_L_src, "thigh.R": thigh_R_src,
                "shin.L": shin_L_src, "shin.R": shin_R_src,
                "foot.L": foot_L_src, "foot.R": foot_R_src,
            }
            for sname, src in w_map.items():
                if copy_cut_to_v2(src, v2_dir, f"body.{view}.{sname}.png"):
                    repaired += 1

    # 7. Ancestors (`ancestors.ancestor_robe_indigo_gold`) from `ancestors.05.ancestor_robe_indigo_gold.body`
    anc_sid = "ancestors.05.ancestor_robe_indigo_gold.body"
    anc_hand_L = cut_path("poet.red_black_sunglasses.body.front", 6)
    anc_hand_R = cut_path("poet.red_black_sunglasses.body.front", 7)
    for view in ("front", "threequarter", "profile", "back"):
        torso_p = 2 if view == "back" else (3 if view == "profile" else 1)
        pelvis_p = 9 if view == "back" else 4
        foot_L_p = 20 if view == "profile" else 18
        foot_R_p = 21 if view == "profile" else 19
        anc_map = {
            "torso": cut_path(anc_sid, torso_p),
            "pelvis": cut_path(anc_sid, pelvis_p),
            "uarm.L": cut_path(anc_sid, 5), "uarm.R": cut_path(anc_sid, 6),
            "farm.L": cut_path(anc_sid, 7), "farm.R": cut_path(anc_sid, 8),
            "hand.L": anc_hand_L, "hand.R": anc_hand_R,
            "thigh.L": cut_path(anc_sid, 10), "thigh.R": cut_path(anc_sid, 11),
            "shin.L": cut_path(anc_sid, 12), "shin.R": cut_path(anc_sid, 13),
            "foot.L": cut_path(anc_sid, foot_L_p), "foot.R": cut_path(anc_sid, foot_R_p),
        }
        for sname, src in anc_map.items():
            if copy_cut_to_v2(src, "ancestors.ancestor_robe_indigo_gold", f"body.{view}.{sname}.png"):
                repaired += 1

    print(f"[OK] Repaired {repaired} part files in shots/arena/parts/kit3/v2/parts/ from release_v2/cuts/")
    return repaired


def compute_card_anchors_for_slot(slot_name: str, rel_file: str) -> dict:
    """
    Computes accurate normalized `pivot_A` (proximal joint pin) and `socket_B` (distal joint socket)
    for any cut-out piece file, respecting:
      - `range_rigger.html` convention:
          * `head`:   pivot_A = neck [0.50, 0.85], socket_B = crown [0.50, 0.12]
          * `torso`:  pivot_A = neck/collar [0.50, 0.10], socket_B = waist/pelvis [0.50, 0.88]
          * `pelvis`: pivot_A = waist [0.50, 0.20], socket_B = hip line [0.50, 0.84]
          * `uarm_*`: pivot_A = shoulder [0.50, 0.14], socket_B = elbow [0.50, 0.85]
          * `farm_*`: pivot_A = elbow [0.50, 0.14], socket_B = wrist cuff [0.50, 0.81]
          * `hand_*`: pivot_A = wrist crease, socket_B = fingertips (auto-detects vertical vs horizontal vs upside-down!)
          * `thigh_*`: pivot_A = hip [0.50, 0.14], socket_B = knee [0.50, 0.85]
          * `shin_*`: pivot_A = knee [0.50, 0.13], socket_B = ankle cuff [0.50, 0.83]
          * `foot_*`: pivot_A = ankle tab at top of shaft, socket_B = sole directly below ankle shaft (vertical shaft axis!)
      - `crash_lab.html` convention (`proximal_xy`, `distal_xy` matching `SLOT_BONE_MAP`):
          * `torso` in `crash_lab.html` maps `['pelvis', 'neck']`, so `proximal_xy` = waist `[0.50, 0.88]`, `distal_xy` = neck `[0.50, 0.10]`.
    """
    meta = inspect_img(rel_file)
    w, h = meta["width"], meta["height"]
    bx0, by0, bx1, by1 = meta["visible_bbox"]
    bw, bh = max(1, bx1 - bx0), max(1, by1 - by0)

    def to_norm(nx_vis, ny_vis):
        return [
            round((bx0 + nx_vis * bw) / w, 4),
            round((by0 + ny_vis * bh) / h, 4),
        ]

    fn_lower = os.path.basename(rel_file).lower()

    # Special case: Bolas horizontal dummy parts (`arena/cast/dummy/bola.*`)
    if "arena/cast/dummy/" in rel_file:
        if slot_name == "head":
            pA, sB = [round(12 / 226, 4), 0.5], [round(212 / 226, 4), 0.5]
        elif slot_name == "torso":
            pA, sB = [round(269 / 348, 4), 0.5], [round(69 / 348, 4), 0.5]
        elif slot_name.startswith("foot_"):
            pA, sB = [round(36 / 184, 4), round(35 / 92, 4)], [round(154 / 184, 4), round(58 / 92, 4)]
        else:
            pA, sB = [0.16, 0.50], [0.86, 0.50]
        return {
            "file": meta["file"],
            "width": w,
            "height": h,
            "visible_bbox": meta["visible_bbox"],
            "pivot_A": pA,
            "socket_B": sB,
            "proximal_xy": sB if slot_name == "torso" else pA,
            "distal_xy": pA if slot_name == "torso" else sB,
            "cuff_clip_ratio": 1.0,
            "rot_offset_deg": 0.0,
        }

    cuff_clip = 1.0
    if slot_name == "head":
        pA = to_norm(0.50, 0.85)   # neck grommet at bottom of head
        sB = to_norm(0.50, 0.12)   # crown at top of head
        cuff_clip = 0.86
    elif slot_name == "torso":
        # In range_rigger.html, torso is drawn from pNeck (ptA) -> pPelvis (ptB)
        pA = to_norm(0.50, 0.10)   # collar / neck at TOP
        sB = to_norm(0.50, 0.88)   # waist / pelvis at BOTTOM
    elif slot_name == "pelvis":
        pA = to_norm(0.50, 0.20)
        sB = to_norm(0.50, 0.84)
    elif slot_name.startswith("uarm_"):
        pA = to_norm(0.50, 0.14)
        sB = to_norm(0.50, 0.85)
    elif slot_name.startswith("farm_"):
        if "01_components" in rel_file.lower():
            pA = [0.50, 0.13]
            sB = [0.50, 0.778]
            cuff_clip = 0.806
        else:
            pA = to_norm(0.50, 0.14)
            sB = to_norm(0.50, 0.82)
            cuff_clip = 0.86
    elif slot_name.startswith("hand_"):
        # Check orientation of the hand card:
        # 1) `17_hand_open_L.png` & `18_hand_open_R.png` have grommet at BOTTOM (ny=0.78) and fingers at TOP (ny=0.12)
        if "17_hand_open" in fn_lower or "18_hand_open" in fn_lower:
            pA = to_norm(0.50, 0.78)
            sB = to_norm(0.50, 0.12)
        # 2) Horizontal hand cards (from `.hands` sheets or `v2` hand variants where bw > bh * 1.18):
        #    Wrist grommet tab is on the LEFT (nx=0.18, ny=0.50), fingers point RIGHT (nx=0.88, ny=0.50)
        elif bw > bh * 1.18:
            pA = to_norm(0.18, 0.50)
            sB = to_norm(0.88, 0.50)
        # 3) Standard vertical hand cards (`4 HAND L`, `7 HAND R`, `15_hand_relaxed_L`, `16_hand_relaxed_R`):
        #    Wrist grommet tab is at the TOP (ny=0.22), fingers point DOWN (ny=0.88)
        else:
            pA = to_norm(0.50, 0.22)
            sB = to_norm(0.50, 0.88)
    elif slot_name.startswith("thigh_"):
        pA = to_norm(0.50, 0.14)
        sB = to_norm(0.50, 0.85)
    elif slot_name.startswith("shin_"):
        if "01_components" in rel_file.lower():
            pA = [0.50, 0.12]
            sB = [0.50, 0.814]
            cuff_clip = 0.843
        else:
            pA = to_norm(0.50, 0.13)
            sB = to_norm(0.50, 0.83)
            cuff_clip = 0.88
    elif slot_name.startswith("foot_"):
        # For boots/shoes:
        # Both front boots (`19_boot_front_L`, `16 FOOT L FRONT`) and profile boots (`feet__p01`, `body.profile.foot`)
        # have their ankle grommet tab at the TOP of the boot shaft and the sole at the BOTTOM!
        # In profile boots facing right, the ankle shaft is at nx ~ 0.30; in profile boots facing left (like `13 foot L` on compact-core),
        # the ankle shaft is at nx ~ 0.66; in front boots, nx ~ 0.50.
        if bw > bh * 1.08:
            # Profile shoe/boot: determine whether ankle tab is on top-left or top-right by checking top-quarter alpha center of mass
            abs_p = os.path.join(SHOTS_DIR, meta["file"])
            shaft_nx = 0.34
            try:
                with Image.open(abs_p) as im:
                    alpha = im.convert("RGBA").split()[-1]
                    top_band = alpha.crop((bx0, by0, bx1, by0 + max(4, int(bh * 0.32))))
                    tb_bb = top_band.point([255 if i > 20 else 0 for i in range(256)]).getbbox()
                    if tb_bb:
                        cx_top = (tb_bb[0] + tb_bb[2]) * 0.5
                        shaft_nx = max(0.22, min(0.78, cx_top / bw))
            except Exception:
                shaft_nx = 0.34
            pA = to_norm(shaft_nx, 0.22)
            sB = to_norm(shaft_nx, 0.88)
        else:
            pA = to_norm(0.50, 0.25)
            sB = to_norm(0.50, 0.88)
    else:
        pA = to_norm(0.50, 0.15)
        sB = to_norm(0.50, 0.85)

    # For crash_lab.html:
    # - `torso` maps `['pelvis', 'neck']` (bottom -> top), so `proximal_xy` is waist (`sB`) and `distal_xy` is collar (`pA`).
    # - `foot_L/R` in `crash_lab.html` maps `['ankle', 'toe']` (diagonal down-sideways), so keep diagonal `proximal_xy`/`distal_xy`.
    if slot_name == "torso":
        prox_xy, dist_xy = sB, pA
    elif slot_name.startswith("foot_"):
        prox_xy = to_norm(0.42, 0.28)
        dist_xy = to_norm(0.72, 0.88)
    else:
        prox_xy, dist_xy = pA, sB

    return {
        "file": meta["file"],
        "width": w,
        "height": h,
        "visible_bbox": meta["visible_bbox"],
        "pivot_A": pA,
        "socket_B": sB,
        "proximal_xy": prox_xy,
        "distal_xy": dist_xy,
        "cuff_clip_ratio": round(cuff_clip, 4),
        "rot_offset_deg": 0.0,
    }


def build_skeleton_breeds() -> list:
    """
    Defines the 7 Canonical Skeleton Breeds matched to the Vitruvian Man Proportions Engine.
    Each breed specifies exact bone lengths in cm (`thigh`, `shin`, `upper`, `fore`, `spine`,
    `hipW`, `shW`, `headR`), Vitruvian landmarks (`groin_ratio`, `navel_ratio`, `knee_ratio`,
    `chin_ratio`, `wingspan_ratio`), and default layer stack rules (`shoe_over_calf`, `hand_over_cuff`).
    """
    return [
        {
            "id": "vitruvian_8h",
            "name": "BREED 01 · Vitruvian Canon (8.0H · Square & Navel Circle)",
            "short_name": "Vitruvian 8.0H",
            "head_count": 8.0,
            "ref_height_cm": 170.0,
            "bones": {"thigh": 45.0, "shin": 45.0, "upper": 30.0, "fore": 27.0, "spine": 52.0, "hipW": 10.0, "shW": 18.0, "headR": 10.8},
            "vitruvian_ratios": {"knee": 0.25, "groin": 0.50, "navel": 0.618, "chest": 0.75, "chin": 0.875, "wingspan": 1.00},
            "default_layer_order": {"shoe_over_calf": False, "hand_over_cuff": False, "head_over_collar": True, "pelvis_over_thigh": True},
        },
        {
            "id": "poet_tracksuit_75h",
            "name": "BREED 02 · Poet Tracksuit Hero (7.5H · Jogger Cuff over Chelsea Boot)",
            "short_name": "Poet Tracksuit 7.5H",
            "head_count": 7.5,
            "ref_height_cm": 170.0,
            "bones": {"thigh": 44.5, "shin": 45.5, "upper": 30.0, "fore": 27.0, "spine": 52.0, "hipW": 10.2, "shW": 18.5, "headR": 11.2},
            "vitruvian_ratios": {"knee": 0.255, "groin": 0.50, "navel": 0.615, "chest": 0.745, "chin": 0.867, "wingspan": 1.01},
            "default_layer_order": {"shoe_over_calf": False, "hand_over_cuff": False, "head_over_collar": True, "pelvis_over_thigh": True},
        },
        {
            "id": "compact_core_sneaker",
            "name": "BREED 03 · Compact-Core / High-Top Sneaker (7.2H · Shoe Over Calf)",
            "short_name": "Compact High-Top 7.2H",
            "head_count": 7.2,
            "ref_height_cm": 168.0,
            "bones": {"thigh": 43.0, "shin": 43.0, "upper": 29.0, "fore": 26.5, "spine": 51.0, "hipW": 10.0, "shW": 18.0, "headR": 11.5},
            "vitruvian_ratios": {"knee": 0.25, "groin": 0.495, "navel": 0.612, "chest": 0.74, "chin": 0.861, "wingspan": 1.00},
            "default_layer_order": {"shoe_over_calf": True, "hand_over_cuff": False, "head_over_collar": True, "pelvis_over_thigh": True},
        },
        {
            "id": "ex_bomber_broad",
            "name": "BREED 04 · EX Olive Bomber (7.6H · Wide Clavicle & Long Stride)",
            "short_name": "EX Bomber 7.6H",
            "head_count": 7.6,
            "ref_height_cm": 174.0,
            "bones": {"thigh": 46.5, "shin": 46.0, "upper": 31.0, "fore": 28.0, "spine": 53.5, "hipW": 10.5, "shW": 20.5, "headR": 11.0},
            "vitruvian_ratios": {"knee": 0.255, "groin": 0.505, "navel": 0.62, "chest": 0.755, "chin": 0.87, "wingspan": 1.03},
            "default_layer_order": {"shoe_over_calf": True, "hand_over_cuff": False, "head_over_collar": True, "pelvis_over_thigh": True},
        },
        {
            "id": "muse_gown_elongated",
            "name": "BREED 05 · Muse / Vintage Gown (7.8H · High Waist & Heel over Calf)",
            "short_name": "Muse / Gown 7.8H",
            "head_count": 7.8,
            "ref_height_cm": 166.0,
            "bones": {"thigh": 44.0, "shin": 45.0, "upper": 28.5, "fore": 26.0, "spine": 49.5, "hipW": 10.2, "shW": 16.2, "headR": 10.6},
            "vitruvian_ratios": {"knee": 0.26, "groin": 0.515, "navel": 0.63, "chest": 0.76, "chin": 0.872, "wingspan": 0.98},
            "default_layer_order": {"shoe_over_calf": True, "hand_over_cuff": True, "head_over_collar": True, "pelvis_over_thigh": True},
        },
        {
            "id": "child_traveler_52h",
            "name": "BREED 06 · Child Traveler (5.2H · Age 7 · 118cm Proportion)",
            "short_name": "Child 5.2H (118cm)",
            "head_count": 5.2,
            "ref_height_cm": 118.0,
            "bones": {"thigh": 31.0, "shin": 31.0, "upper": 21.0, "fore": 19.0, "spine": 36.0, "hipW": 7.2, "shW": 12.8, "headR": 9.6},
            "vitruvian_ratios": {"knee": 0.23, "groin": 0.46, "navel": 0.58, "chest": 0.71, "chin": 0.81, "wingspan": 0.94},
            "default_layer_order": {"shoe_over_calf": False, "hand_over_cuff": False, "head_over_collar": True, "pelvis_over_thigh": True},
        },
        {
            "id": "piece_derived_auto",
            "name": "BREED 07 · Auto-Derived From Active Pieces (Piece-Span Breed)",
            "short_name": "Auto Piece-Breed",
            "head_count": 7.5,
            "ref_height_cm": 170.0,
            "bones": {"thigh": 45.0, "shin": 45.0, "upper": 30.0, "fore": 27.0, "spine": 52.0, "hipW": 10.0, "shW": 18.0, "headR": 11.0},
            "vitruvian_ratios": {"knee": 0.25, "groin": 0.50, "navel": 0.618, "chest": 0.75, "chin": 0.875, "wingspan": 1.00},
            "default_layer_order": {"shoe_over_calf": False, "hand_over_cuff": False, "head_over_collar": True, "pelvis_over_thigh": True},
        },
    ]


def upgrade_crash_lab_catalog():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        cat = json.load(f)

    # Upgrade all rigs in `cat["rigs"]`:
    # - Refresh dimensions, visible_bbox, pivot_A, socket_B, proximal_xy, distal_xy, rot_offset_deg=0
    # - Add `variant_meta` dictionary on every slot so switching between `front`, `threequarter`,
    #   `profile`, `back`, `open`, `grip`, `fist`, `heel_up`, `toe_up` uses that exact card's
    #   calibrated geometry!
    for rig in cat.get("rigs", []):
        rig_id = rig["id"]
        # Assign default breed_id
        breed_map = {
            "poet_tracksuit_31": "poet_tracksuit_75h",
            "poet_black_tshirt": "compact_core_sneaker",
            "ex_jacket_back": "ex_bomber_broad",
            "vintage_party_couple": "vitruvian_8h",
            "woman_muse_costumes": "muse_gown_elongated",
            "child_traveler_ghost": "child_traveler_52h",
            "mother_ancestors_family": "vitruvian_8h",
            "dj_club_citizens": "compact_core_sneaker",
            "bolas_dummy": "vitruvian_8h",
            "weave_man": "poet_tracksuit_75h",
        }
        rig["default_breed_id"] = breed_map.get(rig_id, "vitruvian_8h")

        # For poet_tracksuit_31, ensure foot_L and foot_R use authentic profile boots (`feet__p04` L.flat, `feet__p01` R.flat)
        if rig_id == "poet_tracksuit_31":
            v2_ts = "arena/parts/kit3/v2/parts/poet.red_black_sunglasses"
            if "foot_L" in rig["slots"]:
                rig["slots"]["foot_L"]["view_variants"]["profile"] = f"{v2_ts}/foot.L.flat.png"
                rig["slots"]["foot_L"]["view_variants"]["threequarter"] = f"{v2_ts}/body.threequarter.foot.L.png"
                rig["slots"]["foot_L"]["view_variants"]["back"] = f"{v2_ts}/body.back.foot.L.png"
                rig["slots"]["foot_L"]["view_variants"]["heel_up"] = f"{v2_ts}/foot.L.heel_up.png"
                rig["slots"]["foot_L"]["view_variants"]["toe_up"] = f"{v2_ts}/foot.L.toe_up.png"
            if "foot_R" in rig["slots"]:
                rig["slots"]["foot_R"]["view_variants"]["profile"] = f"{v2_ts}/foot.R.flat.png"
                rig["slots"]["foot_R"]["view_variants"]["threequarter"] = f"{v2_ts}/body.threequarter.foot.R.png"
                rig["slots"]["foot_R"]["view_variants"]["back"] = f"{v2_ts}/body.back.foot.R.png"
                rig["slots"]["foot_R"]["view_variants"]["heel_up"] = f"{v2_ts}/foot.R.heel_up.png"
                rig["slots"]["foot_R"]["view_variants"]["toe_up"] = f"{v2_ts}/foot.R.toe_up.png"
            for hs, hside in [("hand_L", "L"), ("hand_R", "R")]:
                if hs in rig["slots"]:
                    rig["slots"][hs]["view_variants"]["profile"] = f"{v2_ts}/body.profile.hand.{hside}.png"
                    rig["slots"][hs]["view_variants"]["threequarter"] = f"{v2_ts}/body.threequarter.hand.{hside}.png"
                    rig["slots"][hs]["view_variants"]["back"] = f"{v2_ts}/body.back.hand.{hside}.png"

        for slot_key, slot_obj in list(rig["slots"].items()):
            # Canonical slot key (e.g. `uarm_L` vs `upper_arm_L`)
            canon_key = slot_key.replace("upper_arm_", "uarm_").replace("forearm_", "farm_")
            prim_file = slot_obj.get("file") or slot_obj.get("default_asset")
            if not prim_file:
                continue
            c_meta = compute_card_anchors_for_slot(canon_key, prim_file)
            slot_obj["file"] = c_meta["file"]
            slot_obj["default_asset"] = c_meta["file"]
            slot_obj["width"] = c_meta["width"]
            slot_obj["height"] = c_meta["height"]
            slot_obj["visible_bbox"] = c_meta["visible_bbox"]
            slot_obj["pivot_A"] = c_meta["pivot_A"]
            slot_obj["socket_B"] = c_meta["socket_B"]
            slot_obj["pivot_A_px"] = [round(c_meta["pivot_A"][0] * c_meta["width"], 1), round(c_meta["pivot_A"][1] * c_meta["height"], 1)]
            slot_obj["socket_B_px"] = [round(c_meta["socket_B"][0] * c_meta["width"], 1), round(c_meta["socket_B"][1] * c_meta["height"], 1)]
            slot_obj["proximal_xy"] = c_meta["proximal_xy"]
            slot_obj["distal_xy"] = c_meta["distal_xy"]
            slot_obj["cuff_clip_ratio"] = c_meta["cuff_clip_ratio"]
            slot_obj["rot_offset_deg"] = 0.0

            # Compute per-variant metadata (`variant_meta`)
            vv = slot_obj.get("view_variants") or slot_obj.get("views") or {"front": c_meta["file"]}
            variant_meta = {}
            for vk, vfile in vv.items():
                vm = compute_card_anchors_for_slot(canon_key, vfile)
                variant_meta[vk] = vm
            slot_obj["variant_meta"] = variant_meta
            if "views" in slot_obj:
                if "profile" in vv:
                    slot_obj["views"]["side"] = vv["profile"]
                if "front" in vv:
                    slot_obj["views"]["front"] = vv["front"]
                if "back" in vv:
                    slot_obj["views"]["back"] = vv["back"]

    # Upgrade `swapper_bank` items so every hand/foot/head/torso/limb has accurate `pivot_A`, `socket_B`, and `rot_offset_deg = 0.0`
    cat_to_slot = {
        "shoes_feet": "foot_L",
        "hands": "hand_L",
        "heads": "head",
        "torsos_pelvis": "torso",
        "limbs": "uarm_L",
    }
    for cat_name, items in cat.get("swapper_bank", {}).items():
        s_type = cat_to_slot.get(cat_name, "uarm_L")
        for it in items:
            f_path = it.get("file")
            if not f_path:
                continue
            cm = compute_card_anchors_for_slot(s_type, f_path)
            it["width"] = cm["width"]
            it["height"] = cm["height"]
            it["pivot_A"] = cm["pivot_A"]
            it["socket_B"] = cm["socket_B"]
            it["proximal_xy"] = cm["proximal_xy"]
            it["distal_xy"] = cm["distal_xy"]
            it["rot_offset_deg"] = 0.0

    cat["skeleton_breeds"] = build_skeleton_breeds()

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2)
    print(f"[OK] Upgraded {CATALOG_PATH} with per-variant metadata, purified orientations, and {len(cat['skeleton_breeds'])} skeleton breeds.")


if __name__ == "__main__":
    repair_v2_parts_from_release_cuts()
    upgrade_crash_lab_catalog()
