#!/usr/bin/env python3
"""
WYGWYL Crash Lab, 360° Range-Test & Centaur CAPTCHA Studio Catalog Builder
==========================================================================
Generates `shots/arena/parts/kit3/release_v2/crash_lab_catalog.json` containing:
  1. 10 Rig Profiles (the 8 canonical WYGWYL rigs from `character_rigs_library.json`
     + `bolas_dummy` Bola/Shim/Dot + `weave_man`), each with verified git-tracked slot
     cards (`head`, `torso`, `pelvis`, `uarm_L`, `uarm_R`, `farm_L`, `farm_R`, `hand_L`,
     `hand_R`, `thigh_L`, `thigh_R`, `shin_L`, `shin_R`, `foot_L`, `foot_R`), exact
     normalized `pivot_A` and `socket_B` coordinates, `cuff_clip_ratio`, `rot_offset_deg`,
     `canonical_cm_len`, and `view_variants`.
  2. 20 Range-of-Motion & Acting Arena Crash Tests (`rom_and_crash_tests`) across:
     - ROM & Spin Battery (T01..T06)
     - Locomotion & Gait (T07..T10)
     - Acting Arena Challenges (T11..T20)
     Each with 3D Bolas keyframes and a verified `reference_body_img` template.
  3. 12 "What's Fucked Up?" Quick CAPTCHA Repair Challenges (`captcha_challenges`)
     modeled directly on the measured defects in `shots/arena/FAILINGS.md` and
     `shots/arena/REGISTRATION.md`.
  4. Curated Normalized Parts Swapper Bank (`swapper_bank`) across `shoes_feet`,
     `hands`, `heads`, `torsos_pelvis`, and `limbs` with unified physical scale
     (`normalized_cm_scale`), `pivot_A`, and `socket_B`.
"""

import json
import math
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS_DIR = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT_PATH = os.path.join(HERE, "release_v2", "crash_lab_catalog.json")

CHAR_LIB_PATH = os.path.join(HERE, "release_v2", "character_rigs_library.json")
BODY_LAB_PATH = os.path.join(SHOTS_DIR, "arena", "parts", "body_lab", "body_lab_unified.json")
DUMMY_PARTS_PATH = os.path.join(SHOTS_DIR, "arena", "cast", "dummy", "parts.json")
WEAVE_MAN_PATH = os.path.join(SHOTS_DIR, "weave", "cast", "man", "cast.json")

_IMG_CACHE = {}


def inspect_img(rel_shots_path: str) -> dict:
    clean = rel_shots_path.lstrip("/")
    if clean.startswith("shots/"):
        clean = clean[len("shots/"):]
    if clean in _IMG_CACHE:
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
    try:
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
    except Exception:
        info = {
            "exists": True,
            "file": clean,
            "width": 256,
            "height": 256,
            "visible_bbox": [0, 0, 256, 256],
            "visible_w": 256,
            "visible_h": 256,
        }
    _IMG_CACHE[clean] = info
    return info


# Canonical physical lengths in cm for an adult (170cm Bolas reference skeleton)
CANONICAL_SLOT_CM = {
    "head": 24.0,
    "torso": 52.0,
    "pelvis": 24.0,
    "uarm_L": 30.0,
    "uarm_R": 30.0,
    "farm_L": 27.0,
    "farm_R": 27.0,
    "hand_L": 19.0,
    "hand_R": 19.0,
    "thigh_L": 45.0,
    "thigh_R": 45.0,
    "shin_L": 45.0,
    "shin_R": 45.0,
    "foot_L": 26.0,
    "foot_R": 26.0,
}

# Default visible-bbox-relative [nx, ny] for proximal Pivot A and distal Socket B
DEFAULT_SLOT_ENDS = {
    "head": ([0.50, 0.84], [0.50, 0.12]),     # neck -> crown
    "torso": ([0.50, 0.88], [0.50, 0.12]),    # waist/pelvis -> neck
    "pelvis": ([0.50, 0.22], [0.50, 0.82]),   # waist -> hip line
    "uarm_L": ([0.50, 0.15], [0.50, 0.85]),   # shoulder -> elbow
    "uarm_R": ([0.50, 0.15], [0.50, 0.85]),
    "farm_L": ([0.50, 0.15], [0.50, 0.82]),   # elbow -> wrist
    "farm_R": ([0.50, 0.15], [0.50, 0.82]),
    "hand_L": ([0.50, 0.22], [0.50, 0.88]),   # wrist -> fingertips
    "hand_R": ([0.50, 0.22], [0.50, 0.88]),
    "thigh_L": ([0.50, 0.15], [0.50, 0.86]),  # hip -> knee
    "thigh_R": ([0.50, 0.15], [0.50, 0.86]),
    "shin_L": ([0.50, 0.14], [0.50, 0.84]),   # knee -> ankle
    "shin_R": ([0.50, 0.14], [0.50, 0.84]),
    "foot_L": ([0.42, 0.28], [0.75, 0.88]),   # ankle -> toe/sole
    "foot_R": ([0.42, 0.28], [0.75, 0.88]),
}


def make_slot_entry(
    slot_name: str,
    rel_file: str,
    scale_factor: float = 1.0,
    pivot_A_override=None,
    socket_B_override=None,
    cuff_clip_ratio: float = 1.0,
    rot_offset_deg: float = 0.0,
    view_variants: dict = None,
    face_overlays: list = None,
) -> dict:
    meta = inspect_img(rel_file)
    w, h = meta["width"], meta["height"]
    bx0, by0, bx1, by1 = meta["visible_bbox"]
    bw, bh = max(1, bx1 - bx0), max(1, by1 - by0)

    def_pA, def_sB = DEFAULT_SLOT_ENDS.get(slot_name, ([0.5, 0.15], [0.5, 0.85]))

    # Detect horizontal v2 hands (e.g. 74x43) or horizontal dummy limbs
    is_horiz_v2_hand = slot_name.startswith("hand_") and (w > h * 1.35) and w <= 120
    if is_horiz_v2_hand and pivot_A_override is None:
        # Wrist is on left (nx=0.22, ny=0.48), fingertips on right (nx=0.88, ny=0.50)
        pA = [round((bx0 + 0.22 * bw) / w, 4), round((by0 + 0.48 * bh) / h, 4)]
        sB = [round((bx0 + 0.88 * bw) / w, 4), round((by0 + 0.50 * bh) / h, 4)]
        if rot_offset_deg == 0.0:
            rot_offset_deg = 90.0
    elif pivot_A_override is not None and socket_B_override is not None:
        pA = [round(float(pivot_A_override[0]), 4), round(float(pivot_A_override[1]), 4)]
        sB = [round(float(socket_B_override[0]), 4), round(float(socket_B_override[1]), 4)]
    else:
        pA = [round((bx0 + def_pA[0] * bw) / w, 4), round((by0 + def_pA[1] * bh) / h, 4)]
        sB = [round((bx0 + def_sB[0] * bw) / w, 4), round((by0 + def_sB[1] * bh) / h, 4)]

    pA_px = [round(pA[0] * w, 1), round(pA[1] * h, 1)]
    sB_px = [round(sB[0] * w, 1), round(sB[1] * h, 1)]

    cm_len = round(CANONICAL_SLOT_CM.get(slot_name, 30.0) * scale_factor, 2)
    card_span_px = max(8.0, math.hypot(sB_px[0] - pA_px[0], sB_px[1] - pA_px[1]))
    cm_per_px = round(cm_len / card_span_px, 5)

    verified_variants = {}
    if view_variants:
        for vk, vf in view_variants.items():
            vmeta = inspect_img(vf)
            if vmeta["exists"]:
                verified_variants[vk] = vmeta["file"]
    if not verified_variants:
        verified_variants["front"] = meta["file"]

    entry = {
        "slot": slot_name,
        "file": meta["file"],
        "exists": meta["exists"],
        "width": w,
        "height": h,
        "visible_bbox": meta["visible_bbox"],
        "pivot_A": pA,
        "socket_B": sB,
        "pivot_A_px": pA_px,
        "socket_B_px": sB_px,
        "cuff_clip_ratio": round(cuff_clip_ratio, 4),
        "rot_offset_deg": round(rot_offset_deg, 2),
        "canonical_cm_len": cm_len,
        "cm_per_px": cm_per_px,
        "view_variants": verified_variants,
    }
    if face_overlays:
        entry["face_overlays"] = face_overlays
    return entry


def build_kit_rig_slots(kit_dir: str, scale_factor: float = 1.0, views=("front", "threequarter", "profile", "back"), default_view="front") -> dict:
    base = f"arena/parts/kit3/v2/parts/{kit_dir}"
    slot_file_map = {
        "head": "head",
        "torso": "body.{v}.torso",
        "pelvis": "body.{v}.pelvis",
        "uarm_L": "body.{v}.uarm.L",
        "uarm_R": "body.{v}.uarm.R",
        "farm_L": "body.{v}.farm.L",
        "farm_R": "body.{v}.farm.R",
        "hand_L": "body.{v}.hand.L",
        "hand_R": "body.{v}.hand.R",
        "thigh_L": "body.{v}.thigh.L",
        "thigh_R": "body.{v}.thigh.R",
        "shin_L": "body.{v}.shin.L",
        "shin_R": "body.{v}.shin.R",
        "foot_L": "body.{v}.foot.L",
        "foot_R": "body.{v}.foot.R",
    }
    slots = {}
    for slot_name, pat in slot_file_map.items():
        variants = {}
        for v in views:
            fn = f"head.{v}.png" if slot_name == "head" else f"{pat.format(v=v)}.png"
            rel = f"{base}/{fn}"
            if inspect_img(rel)["exists"]:
                variants[v] = rel
        # Choose primary file
        prim = variants.get(default_view) or next(iter(variants.values()), None)
        if not prim:
            if slot_name == "pelvis":
                pelvis_fallbacks = {
                    "poet.black_tshirt": "weave/cast/man/parts/pelvis.front.png",
                    "ex.ex_jacket": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.hipcore/ex.ex_jacket.hipcore__p01.png",
                    "party.vintage_party": "arena/parts/kit3/release_v2/cuts/party.vintage_party.hipcore/party.vintage_party.hipcore__p01.png",
                    "young_poet.child_clothes": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.hipcore/young_poet.child_clothes.hipcore__p01.png",
                    "party.dj_cyber": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/06_pelvis_front_cover.png",
                }
                cand = pelvis_fallbacks.get(kit_dir, "kits/packs/poet_tracksuit_v1/01_COMPONENTS/06_pelvis_front_cover.png")
                if not inspect_img(cand)["exists"]:
                    cand = "kits/packs/poet_tracksuit_v1/01_COMPONENTS/06_pelvis_front_cover.png"
                prim = cand
                variants[default_view] = prim
            else:
                fb_v = default_view if default_view in ("front", "threequarter", "profile", "back") else "back"
                fn = f"head.{fb_v}.png" if slot_name == "head" else f"{pat.format(v=fb_v)}.png"
                prim = f"arena/parts/kit3/v2/parts/poet.red_black_sunglasses/{fn}"
                variants[default_view] = prim

        cuff = 0.86 if slot_name.startswith("farm_") else (0.88 if slot_name.startswith("shin_") else 1.0)
        rot_off = 90.0 if slot_name.startswith("hand_") else 0.0
        slots[slot_name] = make_slot_entry(
            slot_name,
            prim,
            scale_factor=scale_factor,
            cuff_clip_ratio=cuff,
            rot_offset_deg=rot_off,
            view_variants=variants,
        )
    return slots


def build_all_rigs() -> list:
    rigs = []

    # 1. poet_tracksuit_31 (High-res 31-part tracksuit rig + multi-view variants)
    ts_base = "kits/packs/poet_tracksuit_v1/01_COMPONENTS"
    v2_ts = "arena/parts/kit3/v2/parts/poet.red_black_sunglasses"
    ts_slots = {
        "head": make_slot_entry(
            "head",
            f"{v2_ts}/head.front.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.833],
            socket_B_override=[0.50, 0.12],
            cuff_clip_ratio=0.833,
            view_variants={
                "front": f"{v2_ts}/head.front.png",
                "threequarter": f"{v2_ts}/head.threequarter.png",
                "profile": f"{v2_ts}/head.profile.png",
                "back": f"{v2_ts}/head.back.png",
                "blank_base": f"{ts_base}/21_head_front_blank.png",
            },
            face_overlays=[
                f"{ts_base}/22_eyes_open.png",
                f"{ts_base}/24_brows_rest.png",
                f"{ts_base}/26_nose_front.png",
                f"{ts_base}/27_mouth_rest.png",
                f"{ts_base}/31_sunglasses_front.png",
            ],
        ),
        "torso": make_slot_entry(
            "torso",
            f"{ts_base}/01_torso_front.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.86],
            socket_B_override=[0.50, 0.088],
            view_variants={
                "front": f"{ts_base}/01_torso_front.png",
                "threequarter": f"{v2_ts}/body.threequarter.torso.png",
                "profile": f"{v2_ts}/body.profile.torso.png",
                "back": f"{ts_base}/02_torso_back.png",
            },
        ),
        "pelvis": make_slot_entry(
            "pelvis",
            f"{ts_base}/06_pelvis_front_cover.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.18],
            socket_B_override=[0.50, 0.82],
            view_variants={
                "front": f"{ts_base}/06_pelvis_front_cover.png",
                "threequarter": f"{v2_ts}/body.threequarter.pelvis.png",
                "profile": f"{v2_ts}/body.profile.pelvis.png",
                "back": f"{ts_base}/05_rear_seat_cover.png",
            },
        ),
        "uarm_L": make_slot_entry(
            "uarm_L",
            f"{ts_base}/07_upper_arm_L.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.14],
            socket_B_override=[0.50, 0.84],
            view_variants={
                "front": f"{ts_base}/07_upper_arm_L.png",
                "threequarter": f"{v2_ts}/body.threequarter.uarm.L.png",
                "profile": f"{v2_ts}/body.profile.uarm.L.png",
                "back": f"{v2_ts}/body.back.uarm.L.png",
            },
        ),
        "uarm_R": make_slot_entry(
            "uarm_R",
            f"{ts_base}/09_upper_arm_R.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.14],
            socket_B_override=[0.50, 0.84],
            view_variants={
                "front": f"{ts_base}/09_upper_arm_R.png",
                "threequarter": f"{v2_ts}/body.threequarter.uarm.R.png",
                "profile": f"{v2_ts}/body.profile.uarm.R.png",
                "back": f"{v2_ts}/body.back.uarm.R.png",
            },
        ),
        "farm_L": make_slot_entry(
            "farm_L",
            f"{ts_base}/08_forearm_L.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.13],
            socket_B_override=[0.50, 0.778],
            cuff_clip_ratio=0.806,
            view_variants={
                "front": f"{ts_base}/08_forearm_L.png",
                "threequarter": f"{v2_ts}/body.threequarter.farm.L.png",
                "profile": f"{v2_ts}/body.profile.farm.L.png",
                "back": f"{v2_ts}/body.back.farm.L.png",
            },
        ),
        "farm_R": make_slot_entry(
            "farm_R",
            f"{ts_base}/10_forearm_R.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.13],
            socket_B_override=[0.50, 0.778],
            cuff_clip_ratio=0.806,
            view_variants={
                "front": f"{ts_base}/10_forearm_R.png",
                "threequarter": f"{v2_ts}/body.threequarter.farm.R.png",
                "profile": f"{v2_ts}/body.profile.farm.R.png",
                "back": f"{v2_ts}/body.back.farm.R.png",
            },
        ),
        "hand_L": make_slot_entry(
            "hand_L",
            f"{ts_base}/15_hand_relaxed_L.png",
            scale_factor=1.0,
            pivot_A_override=[0.52, 0.255],
            socket_B_override=[0.50, 0.88],
            rot_offset_deg=0.0,
            view_variants={
                "front": f"{ts_base}/15_hand_relaxed_L.png",
                "open": f"{ts_base}/17_hand_open_L.png",
                "grip": f"{v2_ts}/hand.R.grip.back.png",
                "fist": f"{v2_ts}/hand.R.fist.back.png",
            },
        ),
        "hand_R": make_slot_entry(
            "hand_R",
            f"{ts_base}/16_hand_relaxed_R.png",
            scale_factor=1.0,
            pivot_A_override=[0.48, 0.255],
            socket_B_override=[0.50, 0.88],
            rot_offset_deg=0.0,
            view_variants={
                "front": f"{ts_base}/16_hand_relaxed_R.png",
                "open": f"{ts_base}/18_hand_open_R.png",
                "grip": f"{v2_ts}/hand.R.grip.back.png",
                "fist": f"{v2_ts}/hand.R.fist.back.png",
            },
        ),
        "thigh_L": make_slot_entry(
            "thigh_L",
            f"{ts_base}/11_thigh_L.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.13],
            socket_B_override=[0.50, 0.84],
            view_variants={
                "front": f"{ts_base}/11_thigh_L.png",
                "threequarter": f"{v2_ts}/body.threequarter.thigh.L.png",
                "profile": f"{v2_ts}/body.profile.thigh.L.png",
                "back": f"{v2_ts}/body.back.thigh.L.png",
            },
        ),
        "thigh_R": make_slot_entry(
            "thigh_R",
            f"{ts_base}/13_thigh_R.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.13],
            socket_B_override=[0.50, 0.84],
            view_variants={
                "front": f"{ts_base}/13_thigh_R.png",
                "threequarter": f"{v2_ts}/body.threequarter.thigh.R.png",
                "profile": f"{v2_ts}/body.profile.thigh.R.png",
                "back": f"{v2_ts}/body.back.thigh.R.png",
            },
        ),
        "shin_L": make_slot_entry(
            "shin_L",
            f"{ts_base}/12_shin_L.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.12],
            socket_B_override=[0.50, 0.814],
            cuff_clip_ratio=0.843,
            view_variants={
                "front": f"{ts_base}/12_shin_L.png",
                "threequarter": f"{v2_ts}/body.threequarter.shin.L.png",
                "profile": f"{v2_ts}/body.profile.shin.L.png",
                "back": f"{v2_ts}/body.back.shin.L.png",
            },
        ),
        "shin_R": make_slot_entry(
            "shin_R",
            f"{ts_base}/14_shin_R.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.12],
            socket_B_override=[0.50, 0.814],
            cuff_clip_ratio=0.843,
            view_variants={
                "front": f"{ts_base}/14_shin_R.png",
                "threequarter": f"{v2_ts}/body.threequarter.shin.R.png",
                "profile": f"{v2_ts}/body.profile.shin.R.png",
                "back": f"{v2_ts}/body.back.shin.R.png",
            },
        ),
        "foot_L": make_slot_entry(
            "foot_L",
            f"{ts_base}/19_boot_front_L.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.293],
            socket_B_override=[0.55, 0.88],
            view_variants={
                "front": f"{ts_base}/19_boot_front_L.png",
                "profile": f"{v2_ts}/foot.R.flat.png",
                "heel_up": f"{v2_ts}/foot.R.heel_up.png",
                "toe_up": f"{v2_ts}/foot.R.toe_up.png",
            },
        ),
        "foot_R": make_slot_entry(
            "foot_R",
            f"{ts_base}/20_boot_front_R.png",
            scale_factor=1.0,
            pivot_A_override=[0.50, 0.293],
            socket_B_override=[0.45, 0.88],
            view_variants={
                "front": f"{ts_base}/20_boot_front_R.png",
                "profile": f"{v2_ts}/foot.R.flat.png",
                "heel_up": f"{v2_ts}/foot.R.heel_up.png",
                "toe_up": f"{v2_ts}/foot.R.toe_up.png",
            },
        ),
    }

    rigs.append({
        "id": "poet_tracksuit_31",
        "name": "Poet — Tracksuit 31-Part Rig",
        "short_name": "Poet (Tracksuit 31)",
        "poems": ["04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14"],
        "ref_height_cm": 170,
        "bone_lengths_cm": {"thigh": 45, "shin": 45, "upper": 30, "fore": 27, "spine": 52, "hipW": 10, "shW": 18, "headR": 11},
        "strict_view_rule": None,
        "slots": ts_slots,
    })

    # 2. poet_black_tshirt
    rigs.append({
        "id": "poet_black_tshirt",
        "name": "Poet — Black T-Shirt Rig (Poems 01–03)",
        "short_name": "Poet (Black Tee)",
        "poems": ["01", "02", "03"],
        "ref_height_cm": 170,
        "bone_lengths_cm": {"thigh": 45, "shin": 45, "upper": 30, "fore": 27, "spine": 52, "hipW": 10, "shW": 18, "headR": 11},
        "strict_view_rule": None,
        "slots": build_kit_rig_slots("poet.black_tshirt", scale_factor=1.0),
    })

    # 3. ex_jacket_back (Strict Back / 3Q-Back rule)
    rigs.append({
        "id": "ex_jacket_back",
        "name": "The EX — Olive Bomber (Strict Back/3Q-Back)",
        "short_name": "EX (Olive Bomber)",
        "poems": ["01", "02", "03", "07", "08", "09", "12"],
        "ref_height_cm": 174,
        "bone_lengths_cm": {"thigh": 46, "shin": 46, "upper": 31, "fore": 28, "spine": 53, "hipW": 10.5, "shW": 19, "headR": 11},
        "strict_view_rule": "BACK_AND_3Q_BACK_ONLY_NEVER_FRONT_FACE",
        "slots": build_kit_rig_slots("ex.ex_jacket", scale_factor=1.02, views=("back", "threequarter_back"), default_view="back"),
    })

    # 4. vintage_party_couple
    rigs.append({
        "id": "vintage_party_couple",
        "name": "Vintage Party Couple — 1940s Suit & Satin Gown",
        "short_name": "Vintage Couple",
        "poems": ["01", "14"],
        "ref_height_cm": 170,
        "bone_lengths_cm": {"thigh": 45, "shin": 45, "upper": 30, "fore": 27, "spine": 52, "hipW": 10, "shW": 18, "headR": 11},
        "strict_view_rule": None,
        "slots": build_kit_rig_slots("party.vintage_party", scale_factor=1.0),
    })

    # 5. woman_muse_costumes
    rigs.append({
        "id": "woman_muse_costumes",
        "name": "The Woman / Muse — Teal Dress & 7 Costumes",
        "short_name": "Woman / Muse",
        "poems": ["01", "02", "05", "06", "07", "08", "09", "12", "13", "14"],
        "ref_height_cm": 165,
        "bone_lengths_cm": {"thigh": 43.5, "shin": 43.5, "upper": 29, "fore": 26, "spine": 50, "hipW": 10, "shW": 16.5, "headR": 10.8},
        "strict_view_rule": None,
        "slots": build_kit_rig_slots("woman.teal_dress", scale_factor=0.97),
    })

    # 6. child_traveler_ghost (Age 7, 118cm = 0.694x adult)
    c_scale = 118.0 / 170.0
    rigs.append({
        "id": "child_traveler_ghost",
        "name": "Child Traveler / Ghost Child (Age 7 · 118cm · 5.2H)",
        "short_name": "Child (Age 7 · 118cm)",
        "poems": ["02", "05", "06", "09", "13"],
        "ref_height_cm": 118,
        "bone_lengths_cm": {
            "thigh": round(45 * c_scale, 1),
            "shin": round(45 * c_scale, 1),
            "upper": round(30 * c_scale, 1),
            "fore": round(27 * c_scale, 1),
            "spine": round(52 * c_scale, 1),
            "hipW": round(10 * c_scale, 1),
            "shW": round(18 * c_scale, 1),
            "headR": round(11 * 0.84, 1),  # 5.2-head child proportion has relatively larger head
        },
        "strict_view_rule": None,
        "slots": build_kit_rig_slots("young_poet.child_clothes", scale_factor=c_scale),
    })

    # 7. mother_ancestors_family
    rigs.append({
        "id": "mother_ancestors_family",
        "name": "Mother, Ancestors & Street-Clothes Family",
        "short_name": "Mother / Ancestors",
        "poems": ["02", "05", "09", "10", "11", "12", "13", "14"],
        "ref_height_cm": 168,
        "bone_lengths_cm": {"thigh": 44.5, "shin": 44.5, "upper": 29.5, "fore": 26.5, "spine": 51.5, "hipW": 10, "shW": 17.5, "headR": 11},
        "strict_view_rule": None,
        "slots": build_kit_rig_slots("ancestors.ancestor_robe_indigo_gold", scale_factor=0.99),
    })

    # 8. dj_club_citizens
    rigs.append({
        "id": "dj_club_citizens",
        "name": "Cyber DJ, Club Dancers & Atlantis Citizens",
        "short_name": "Cyber DJ / Club",
        "poems": ["06", "07", "08", "10", "12"],
        "ref_height_cm": 170,
        "bone_lengths_cm": {"thigh": 45, "shin": 45, "upper": 30, "fore": 27, "spine": 52, "hipW": 10, "shW": 18, "headR": 11},
        "strict_view_rule": None,
        "slots": build_kit_rig_slots("party.dj_cyber", scale_factor=1.0),
    })

    # 9. bolas_dummy (Bola / Shim / Dot from `arena/cast/dummy/parts.json`)
    d_base = "arena/cast/dummy"
    bola_slots = {
        "head": make_slot_entry(
            "head", f"{d_base}/bola.head.front.neutral.png", 1.0,
            pivot_A_override=[12/226, 95/190], socket_B_override=[212/226, 95/190],
            view_variants={
                "front": f"{d_base}/bola.head.front.neutral.png",
                "profile": f"{d_base}/bola.head.side.neutral.png",
                "smile": f"{d_base}/bola.head.front.smile.png",
                "strain": f"{d_base}/bola.head.front.strain.png",
            },
        ),
        "torso": make_slot_entry(
            "torso", f"{d_base}/bola.torso_front.png", 1.0,
            pivot_A_override=[69/348, 79/158], socket_B_override=[269/348, 79/158],
            view_variants={
                "front": f"{d_base}/bola.torso_front.png",
                "profile": f"{d_base}/bola.torso_side.png",
            },
        ),
        "pelvis": make_slot_entry(
            "pelvis", f"{d_base}/bola.torso_side.png", 1.0,
            pivot_A_override=[62/314, 62/124], socket_B_override=[162/314, 62/124],
        ),
        "uarm_L": make_slot_entry(
            "uarm_L", f"{d_base}/bola.uarm.png", 1.0,
            pivot_A_override=[44/282, 44/88], socket_B_override=[244/282, 44/88],
        ),
        "uarm_R": make_slot_entry(
            "uarm_R", f"{d_base}/bola.uarm.far.png", 1.0,
            pivot_A_override=[44/282, 44/88], socket_B_override=[244/282, 44/88],
        ),
        "farm_L": make_slot_entry(
            "farm_L", f"{d_base}/bola.farm.png", 1.0,
            pivot_A_override=[43/279, 43/86], socket_B_override=[243/279, 43/86],
        ),
        "farm_R": make_slot_entry(
            "farm_R", f"{d_base}/bola.farm.far.png", 1.0,
            pivot_A_override=[43/279, 43/86], socket_B_override=[243/279, 43/86],
        ),
        "hand_L": make_slot_entry(
            "hand_L", f"{d_base}/bola.hand.relaxed.png", 1.0,
            pivot_A_override=[14/230, 73/146], socket_B_override=[214/230, 73/146],
            view_variants={
                "front": f"{d_base}/bola.hand.relaxed.png",
                "open": f"{d_base}/bola.hand.open.png",
                "fist": f"{d_base}/bola.hand.fist.png",
                "grip": f"{d_base}/bola.hand.grip.png",
            },
        ),
        "hand_R": make_slot_entry(
            "hand_R", f"{d_base}/bola.hand.relaxed.far.png", 1.0,
            pivot_A_override=[14/230, 73/146], socket_B_override=[214/230, 73/146],
            view_variants={
                "front": f"{d_base}/bola.hand.relaxed.far.png",
                "open": f"{d_base}/bola.hand.open.far.png",
                "fist": f"{d_base}/bola.hand.fist.far.png",
                "grip": f"{d_base}/bola.hand.grip.far.png",
            },
        ),
        "thigh_L": make_slot_entry(
            "thigh_L", f"{d_base}/bola.thigh.png", 1.0,
            pivot_A_override=[48/286, 48/96], socket_B_override=[248/286, 48/96],
        ),
        "thigh_R": make_slot_entry(
            "thigh_R", f"{d_base}/bola.thigh.far.png", 1.0,
            pivot_A_override=[48/286, 48/96], socket_B_override=[248/286, 48/96],
        ),
        "shin_L": make_slot_entry(
            "shin_L", f"{d_base}/bola.shin.png", 1.0,
            pivot_A_override=[37/267, 37/74], socket_B_override=[237/267, 37/74],
        ),
        "shin_R": make_slot_entry(
            "shin_R", f"{d_base}/bola.shin.far.png", 1.0,
            pivot_A_override=[37/267, 37/74], socket_B_override=[237/267, 37/74],
        ),
        "foot_L": make_slot_entry(
            "foot_L", f"{d_base}/bola.foot.png", 1.0,
            pivot_A_override=[86/300, 24/109], socket_B_override=[286/300, 24/109],
        ),
        "foot_R": make_slot_entry(
            "foot_R", f"{d_base}/bola.foot.far.png", 1.0,
            pivot_A_override=[86/300, 24/109], socket_B_override=[286/300, 24/109],
        ),
    }
    rigs.append({
        "id": "bolas_dummy",
        "name": "Bolas Crash-Test Dummy (Bola / Shim / Dot)",
        "short_name": "Bolas Dummy (Bola)",
        "poems": ["ARENA"],
        "ref_height_cm": 170,
        "bone_lengths_cm": {"thigh": 45, "shin": 45, "upper": 30, "fore": 27, "spine": 52, "hipW": 10, "shW": 18, "headR": 11},
        "strict_view_rule": None,
        "slots": bola_slots,
    })

    # 10. weave_man (Weave Cast Man from `shots/weave/cast/man/cast.json`)
    w_base = "weave/cast/man/parts"
    weave_slots = {
        "head": make_slot_entry(
            "head", f"{w_base}/head.front.png", 1.0,
            pivot_A_override=[107/214, 257/300], socket_B_override=[107/214, 30/300],
            view_variants={
                "front": f"{w_base}/head.front.png",
                "threequarter": f"{w_base}/head.threequarter_R.png",
                "profile": f"{w_base}/head.profile_R.png",
                "back": f"{w_base}/head.back.png",
            },
        ),
        "torso": make_slot_entry(
            "torso", f"{w_base}/torso.front.png", 1.0,
            pivot_A_override=[110/220, 308/350], socket_B_override=[110/220, 35/350],
            view_variants={
                "front": f"{w_base}/torso.front.png",
                "profile": f"{w_base}/torso.profile.png",
            },
        ),
        "pelvis": make_slot_entry(
            "pelvis", f"{w_base}/proc.pelvis.front.png", 1.0,
            pivot_A_override=[118/236, 25/172], socket_B_override=[118/236, 135/172],
            view_variants={
                "front": f"{w_base}/proc.pelvis.front.png",
                "profile": f"{w_base}/proc.pelvis.profile.png",
            },
        ),
        "uarm_L": make_slot_entry(
            "uarm_L", f"{w_base}/proc.uarm.png", 1.0,
            pivot_A_override=[39/78, 10/168], socket_B_override=[39/78, 158/168],
        ),
        "uarm_R": make_slot_entry(
            "uarm_R", f"{w_base}/proc.uarm.png", 1.0,
            pivot_A_override=[39/78, 10/168], socket_B_override=[39/78, 158/168],
        ),
        "farm_L": make_slot_entry(
            "farm_L", f"{w_base}/proc.farm.png", 1.0,
            pivot_A_override=[35/70, 10/158], socket_B_override=[35/70, 148/158],
        ),
        "farm_R": make_slot_entry(
            "farm_R", f"{w_base}/proc.farm.png", 1.0,
            pivot_A_override=[35/70, 10/158], socket_B_override=[35/70, 148/158],
        ),
        "hand_L": make_slot_entry(
            "hand_L", f"{w_base}/hand.profile.open.png", 1.0,
            pivot_A_override=[31/402, 145.5/264], socket_B_override=[350/402, 145.5/264],
            view_variants={
                "front": f"{w_base}/hand.profile.open.png",
                "grip": f"{w_base}/hand.grip.png",
                "fist": f"{w_base}/hand.fist.png",
                "point": f"{w_base}/hand.point.png",
            },
        ),
        "hand_R": make_slot_entry(
            "hand_R", f"{w_base}/hand.profile.open.png", 1.0,
            pivot_A_override=[31/402, 145.5/264], socket_B_override=[350/402, 145.5/264],
            view_variants={
                "front": f"{w_base}/hand.profile.open.png",
                "grip": f"{w_base}/hand.grip.png",
                "fist": f"{w_base}/hand.fist.png",
                "point": f"{w_base}/hand.point.png",
            },
        ),
        "thigh_L": make_slot_entry(
            "thigh_L", f"{w_base}/proc.thigh.png", 1.0,
            pivot_A_override=[52/104, 10/254], socket_B_override=[52/104, 244/254],
        ),
        "thigh_R": make_slot_entry(
            "thigh_R", f"{w_base}/proc.thigh.png", 1.0,
            pivot_A_override=[52/104, 10/254], socket_B_override=[52/104, 244/254],
        ),
        "shin_L": make_slot_entry(
            "shin_L", f"{w_base}/proc.shin.png", 1.0,
            pivot_A_override=[43/86, 10/248], socket_B_override=[43/86, 238/248],
        ),
        "shin_R": make_slot_entry(
            "shin_R", f"{w_base}/proc.shin.png", 1.0,
            pivot_A_override=[43/86, 10/248], socket_B_override=[43/86, 238/248],
        ),
        "foot_L": make_slot_entry(
            "foot_L", f"{w_base}/boot.flat.png", 1.0,
            pivot_A_override=[66/240, 35/120], socket_B_override=[210/240, 95/120],
            view_variants={
                "front": f"{w_base}/boot.flat.png",
                "toe": f"{w_base}/boot.toe.png",
            },
        ),
        "foot_R": make_slot_entry(
            "foot_R", f"{w_base}/boot.flat.png", 1.0,
            pivot_A_override=[66/240, 35/120], socket_B_override=[210/240, 95/120],
            view_variants={
                "front": f"{w_base}/boot.flat.png",
                "toe": f"{w_base}/boot.toe.png",
            },
        ),
    }
    rigs.append({
        "id": "weave_man",
        "name": "Weave Cast Man (Arena Compiled Cutout Rig)",
        "short_name": "Weave Man",
        "poems": ["01", "02", "03", "ARENA"],
        "ref_height_cm": 170,
        "bone_lengths_cm": {"thigh": 45, "shin": 45, "upper": 30, "fore": 27, "spine": 52, "hipW": 10, "shW": 18, "headR": 11},
        "strict_view_rule": None,
        "slots": weave_slots,
    })

    return rigs


def make_kf(
    f: int,
    note: str = "",
    ktype: str = "key",
    ease: str = "io",
    root=None,
    spine=None,
    head=None,
    armL=None,
    armR=None,
    footL=None,
    footR=None,
    handL=None,
    handR=None,
    handShapeL: str = "relaxed",
    handShapeR: str = "relaxed",
    footShapeL: str = "flat",
    footShapeR: str = "flat",
    pinL: bool = True,
    pinR: bool = True,
) -> dict:
    r = {"x": 0.0, "y": 93.0, "z": 0.0, "yaw": 0.0, "pitch": 0.0, "roll": 0.0}
    if root:
        r.update(root)
    sp = {"fwd": 0.0, "side": 0.0, "twist": 0.0}
    if spine:
        sp.update(spine)
    hd = {"nod": 0.0, "turn": 0.0, "tilt": 0.0}
    if head:
        hd.update(head)
    aL = {"flex": 0.0, "abd": 8.0, "horiz": 0.0, "rot": 0.0, "elbow": 12.0}
    if armL:
        aL.update(armL)
    aR = {"flex": 0.0, "abd": 8.0, "horiz": 0.0, "rot": 0.0, "elbow": 12.0}
    if armR:
        aR.update(armR)
    return {
        "f": f,
        "note": note,
        "type": ktype,
        "ease": ease,
        "root": r,
        "spine": sp,
        "head": hd,
        "armL": aL,
        "armR": aR,
        "footL": footL if footL is not None else [10.0, 5.0, 0.0],
        "footR": footR if footR is not None else [-10.0, 5.0, 0.0],
        "handL": handL,
        "handR": handR,
        "handShapeL": handShapeL,
        "handShapeR": handShapeR,
        "footShapeL": footShapeL,
        "footShapeR": footShapeR,
        "pinL": pinL,
        "pinR": pinR,
    }


def build_rom_and_crash_tests() -> list:
    tests = [
        # =====================================================================
        # GROUP 1: ROM & Spin Battery (T01..T06)
        # =====================================================================
        {
            "id": "T01_360_Turntable_Spin",
            "group": "ROM & Spin Battery",
            "name": "360° Turntable Yaw Spin & View-Cell Switch",
            "cue": "Full 360° continuous rotation testing front → 3/4 → profile → back card swaps, strict EX back-view rules, and 2.5D limb foreshortening.",
            "len": 96,
            "default_view": "front",
            "reference_body_img": "arena/bodies/ACT-004_p0.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Front 0°", "key", root={"yaw": 0}, armL={"abd": 14, "elbow": 18}, armR={"abd": 14, "elbow": 18}),
                make_kf(24, "Profile Right 90°", "brk", root={"yaw": 90}, armL={"flex": 18, "abd": 12}, armR={"flex": -14, "abd": 12}, footL=[10, 5, 4], footR=[-10, 5, -4]),
                make_kf(48, "Back 180°", "key", root={"yaw": 180}, armL={"abd": 16, "elbow": 20}, armR={"abd": 16, "elbow": 20}),
                make_kf(72, "Profile Left 270°", "brk", root={"yaw": 270}, armL={"flex": -14, "abd": 12}, armR={"flex": 18, "abd": 12}, footL=[10, 5, -4], footR=[-10, 5, 4]),
                make_kf(95, "Return Front 360°", "key", root={"yaw": 360}, armL={"abd": 14, "elbow": 18}, armR={"abd": 14, "elbow": 18}),
            ],
        },
        {
            "id": "T02_Deep_Squat_ROM",
            "group": "ROM & Spin Battery",
            "name": "Deep Squat & Aspect-Compensated Knee Flexion",
            "cue": "Descend to pelvis y=48cm with heels planted on floor and arms counterbalancing forward; tests knee/hip IK and crouch bbox compensation.",
            "len": 84,
            "default_view": "tq",
            "reference_body_img": "arena/bodies/man_crouch_f72_clean.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Standing Ready", "key", root={"y": 93, "yaw": -24}, footL=[13, 5, 0], footR=[-13, 5, 0]),
                make_kf(28, "Deep Squat Parallel", "key", "out", root={"y": 52, "z": -6, "yaw": -24}, spine={"fwd": 26}, head={"nod": -18}, armL={"flex": 85, "abd": 6, "elbow": 12}, armR={"flex": 85, "abd": 6, "elbow": 12}, footL=[13, 5, 0], footR=[-13, 5, 0], handShapeL="open", handShapeR="open"),
                make_kf(48, "Bottom Hold", "brk", root={"y": 49, "z": -7, "yaw": -24}, spine={"fwd": 28}, head={"nod": -20}, armL={"flex": 90, "abd": 8, "elbow": 10}, armR={"flex": 90, "abd": 8, "elbow": 10}, footL=[13, 5, 0], footR=[-13, 5, 0], handShapeL="open", handShapeR="open"),
                make_kf(83, "Drive Up to Stand", "key", "in", root={"y": 93, "yaw": -24}, footL=[13, 5, 0], footR=[-13, 5, 0]),
            ],
        },
        {
            "id": "T03_Shoulder_Arm_Wheel",
            "group": "ROM & Spin Battery",
            "name": "180° Overhead Shoulder Wheel & Elbow Brad Check",
            "cue": "Sweep both arms forward, overhead to 178°, out into a T-pose, and behind the back; tests shoulder/elbow brads and wrist cuff-tuck.",
            "len": 96,
            "default_view": "front",
            "reference_body_img": "arena/bodies/ACT-005_p0.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Arms at Sides", "key", root={"yaw": -12}),
                make_kf(24, "Forward 90° Reach", "brk", root={"yaw": -12}, armL={"flex": 90, "abd": 6, "elbow": 6}, armR={"flex": 90, "abd": 6, "elbow": 6}, handShapeL="open", handShapeR="open"),
                make_kf(48, "Full Overhead 178°", "key", "out", root={"y": 95, "yaw": -12}, spine={"fwd": -6}, head={"nod": -14}, armL={"flex": 176, "abd": 14, "elbow": 4}, armR={"flex": 176, "abd": 14, "elbow": 4}, handShapeL="open", handShapeR="open"),
                make_kf(72, "90/90 Abduction T-Pose", "brk", root={"yaw": -12}, armL={"flex": 0, "abd": 92, "elbow": 85}, armR={"flex": 0, "abd": 92, "elbow": 85}, handShapeL="point", handShapeR="point"),
                make_kf(95, "Settle Neutral", "key", root={"yaw": -12}),
            ],
        },
        {
            "id": "T04_One_Foot_Balance_Reach",
            "group": "ROM & Spin Battery",
            "name": "Single-Leg Arabesque Balance & CoM Plumb Test",
            "cue": "Shift CoM strictly over planted Left foot (`x=+10cm`) while extending Right leg back and reaching forward.",
            "len": 84,
            "default_view": "side",
            "reference_body_img": "arena/bodies/kick_balance_f60_p1_f60.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Two-Foot Stance", "key", root={"yaw": -75}),
                make_kf(28, "Weight Shift onto L Foot", "key", "out", root={"x": 9, "y": 89, "z": 4, "yaw": -75}, spine={"fwd": 32}, head={"nod": -22}, armL={"flex": 105, "abd": 12, "elbow": 10}, armR={"flex": 95, "abd": 12, "elbow": 10}, footL=[10, 5, 0], footR=[-6, 42, -38], footShapeR="heel_up", pinL=True, pinR=False),
                make_kf(54, "Arabesque Hold", "brk", root={"x": 10, "y": 87, "z": 6, "yaw": -75}, spine={"fwd": 42}, head={"nod": -28}, armL={"flex": 125, "abd": 10, "elbow": 8}, armR={"flex": 115, "abd": 15, "elbow": 8}, footL=[10, 5, 0], footR=[-6, 56, -48], footShapeR="heel_up", pinL=True, pinR=False),
                make_kf(83, "Recover Stance", "key", root={"yaw": -75}),
            ],
        },
        {
            "id": "T05_High_Knee_Step",
            "group": "ROM & Spin Battery",
            "name": "Alternating High-Knee March & Skirt/Pelvis Clearance",
            "cue": "Drive each knee above hip height (`115°` flexion) while keeping the stance heel locked within `0.6 cm/f`.",
            "len": 80,
            "default_view": "tq",
            "reference_body_img": "arena/bodies/ACT-014_p1.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Stance", "key", root={"yaw": -30}),
                make_kf(20, "High Right Knee Drive", "key", "out", root={"x": 8, "y": 92, "yaw": -30}, spine={"fwd": 4}, armL={"flex": 55, "elbow": 65}, armR={"flex": -35, "elbow": 45}, footL=[10, 5, 0], footR=[-8, 48, 22], footShapeR="heel_up", pinL=True, pinR=False),
                make_kf(40, "Plant Center", "brk", root={"x": 0, "y": 93, "yaw": -30}, footL=[10, 5, 0], footR=[-10, 5, 0]),
                make_kf(60, "High Left Knee Drive", "key", "out", root={"x": -8, "y": 92, "yaw": -30}, spine={"fwd": 4}, armL={"flex": -35, "elbow": 45}, armR={"flex": 55, "elbow": 65}, footL=[8, 48, 22], footR=[-10, 5, 0], footShapeL="heel_up", pinL=False, pinR=True),
                make_kf(79, "Return Stance", "key", root={"yaw": -30}),
            ],
        },
        {
            "id": "T06_Spine_Pitch_Twist",
            "group": "ROM & Spin Battery",
            "name": "Trunk Forward Fold, Arch & Axial Twist",
            "cue": "Hinge hips back to fold trunk forward `65°`, rise into thoracic extension, then twist left and right.",
            "len": 96,
            "default_view": "tq",
            "reference_body_img": "arena/bodies/ACT-016_p2.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Upright", "key", root={"yaw": -35}),
                make_kf(24, "Forward Bow 65°", "key", "out", root={"y": 86, "z": -10, "yaw": -35}, spine={"fwd": 62}, head={"nod": 18}, armL={"flex": 55, "elbow": 15}, armR={"flex": 55, "elbow": 15}),
                make_kf(48, "Back Arch Extension", "key", root={"y": 93, "z": 5, "yaw": -35}, spine={"fwd": -24}, head={"nod": -22}, armL={"flex": -18, "abd": 18}, armR={"flex": -18, "abd": 18}),
                make_kf(72, "Thoracic Twist Left", "brk", root={"yaw": -35}, spine={"twist": 40, "side": 8}, head={"turn": 28}, armL={"flex": 35, "horiz": 25, "elbow": 50}, armR={"flex": 45, "horiz": -20, "elbow": 60}),
                make_kf(95, "Neutral", "key", root={"yaw": -35}),
            ],
        },

        # =====================================================================
        # GROUP 2: Locomotion & Gait (T07..T10)
        # =====================================================================
        {
            "id": "T07_Even_Walk_Heel_Strike",
            "group": "Locomotion & Gait",
            "name": "Foot-Pinned Stride Walk (Zero Moonwalk Certification)",
            "cue": "Four-phase stride with heel strike, weight transfer, and toe-off; planted stance foot remains pinned to the floor within 0.6 cm/frame.",
            "len": 72,
            "default_view": "side",
            "reference_body_img": "arena/bodies/ACT-001_p0.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Heel Strike L", "key", root={"x": 0, "y": 91, "z": -36, "yaw": 0}, spine={"fwd": 4, "twist": -8}, armL={"flex": -24, "elbow": 18}, armR={"flex": 26, "elbow": 24}, footL=[10, 5, -18], footR=[-10, 5, -54], footShapeL="toe_up", footShapeR="heel_up", pinL=True, pinR=False),
                make_kf(18, "Passing Over L", "brk", root={"x": 2, "y": 94, "z": -18, "yaw": 0}, spine={"fwd": 3, "twist": 0}, armL={"flex": 0, "elbow": 16}, armR={"flex": 0, "elbow": 16}, footL=[10, 5, -18], footR=[-10, 18, -14], footShapeL="flat", footShapeR="heel_up", pinL=True, pinR=False),
                make_kf(36, "Heel Strike R", "key", root={"x": -2, "y": 91, "z": 0, "yaw": 0}, spine={"fwd": 4, "twist": 8}, armL={"flex": 26, "elbow": 24}, armR={"flex": -24, "elbow": 18}, footL=[10, 5, -18], footR=[-10, 5, 18], footShapeL="heel_up", footShapeR="toe_up", pinL=False, pinR=True),
                make_kf(54, "Passing Over R", "brk", root={"x": -2, "y": 94, "z": 18, "yaw": 0}, spine={"fwd": 3, "twist": 0}, armL={"flex": 0, "elbow": 16}, armR={"flex": 0, "elbow": 16}, footL=[10, 18, 22], footR=[-10, 5, 18], footShapeL="heel_up", footShapeR="flat", pinL=False, pinR=True),
                make_kf(71, "Settle Step L", "key", root={"x": 0, "y": 92, "z": 36, "yaw": 0}, spine={"fwd": 3}, armL={"flex": -18, "elbow": 16}, armR={"flex": 18, "elbow": 20}, footL=[10, 5, 52], footR=[-10, 5, 18], pinL=True, pinR=True),
            ],
        },
        {
            "id": "T08_Fast_Sprint",
            "group": "Locomotion & Gait",
            "name": "Corridor Sprint Drive & Aerial Suspension",
            "cue": "High-cadence run with 16° forward trunk lean, fisted hands, aerial suspension phase, and braking stop.",
            "len": 64,
            "default_view": "side",
            "reference_body_img": "arena/bodies/sprint_brake_f65_p0_f65.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Drive Strike L", "key", root={"x": 0, "y": 86, "z": -45, "yaw": 0}, spine={"fwd": 18, "twist": -14}, head={"nod": -10}, armL={"flex": -45, "elbow": 75}, armR={"flex": 55, "elbow": 70}, footL=[10, 5, -35], footR=[-10, 28, -68], handShapeL="fist", handShapeR="fist", footShapeR="heel_up", pinL=True, pinR=False),
                make_kf(16, "Aerial Flight 1", "brk", root={"x": 0, "y": 97, "z": -15, "yaw": 0}, spine={"fwd": 16, "twist": 0}, armL={"flex": 10, "elbow": 80}, armR={"flex": -10, "elbow": 80}, footL=[10, 22, -25], footR=[-10, 32, 12], handShapeL="fist", handShapeR="fist", pinL=False, pinR=False),
                make_kf(32, "Drive Strike R", "key", root={"x": 0, "y": 86, "z": 10, "yaw": 0}, spine={"fwd": 18, "twist": 14}, head={"nod": -10}, armL={"flex": 55, "elbow": 70}, armR={"flex": -45, "elbow": 75}, footL=[10, 28, -12], footR=[-10, 5, 18], handShapeL="fist", handShapeR="fist", footShapeL="heel_up", pinL=False, pinR=True),
                make_kf(48, "Brake Plant L", "key", "out", root={"x": 0, "y": 84, "z": 38, "yaw": 0}, spine={"fwd": 8}, armL={"flex": 35, "abd": 22, "elbow": 30}, armR={"flex": 30, "abd": 22, "elbow": 30}, footL=[11, 5, 52], footR=[-10, 5, 18], handShapeL="open", handShapeR="open", footShapeL="toe_up", pinL=True, pinR=True),
                make_kf(63, "Brake Hold", "key", root={"x": 0, "y": 91, "z": 42, "yaw": 0}, footL=[11, 5, 52], footR=[-10, 5, 32], pinL=True, pinR=True),
            ],
        },
        {
            "id": "T09_Stair_Climb",
            "group": "Locomotion & Gait",
            "name": "Three-Riser Stair Ascent (High Knee & Skirt Check)",
            "cue": "Climb three 18cm steps (`y=18, 36, 54cm`); tests high knee flexion against rigid skirt/coat cards and vertical CoM transfer.",
            "len": 84,
            "default_view": "side",
            "reference_body_img": "arena/bodies/ACT-009_p1.png",
            "props": [
                {"type": "steps", "pos": [0, 0, 20], "label": "3-Step Staircase"}
            ],
            "keyframes": [
                make_kf(0, "Base of Stairs", "key", root={"x": 0, "y": 93, "z": -24, "yaw": 0}, footL=[10, 5, -24], footR=[-10, 5, -24]),
                make_kf(28, "Step 1 Left Foot (y=23)", "key", root={"x": 4, "y": 108, "z": 0, "yaw": 0}, spine={"fwd": 12}, armL={"flex": -20, "elbow": 35}, armR={"flex": 38, "elbow": 45}, footL=[10, 23, 4], footR=[-10, 5, -24], pinL=True, pinR=True),
                make_kf(56, "Step 2 Right Foot (y=41)", "key", root={"x": -4, "y": 126, "z": 24, "yaw": 0}, spine={"fwd": 12}, armL={"flex": 38, "elbow": 45}, armR={"flex": -20, "elbow": 35}, footL=[10, 23, 4], footR=[-10, 41, 28], pinL=True, pinR=True),
                make_kf(83, "Top Landing Settle (y=41)", "key", root={"x": 0, "y": 129, "z": 28, "yaw": 0}, spine={"fwd": 2}, footL=[10, 41, 28], footR=[-10, 41, 28], pinL=True, pinR=True),
            ],
        },
        {
            "id": "T10_Backwards_Step_Turn",
            "group": "Locomotion & Gait",
            "name": "Backwards Retreat Step & 180° Pivot Turn",
            "cue": "Step backward twice, pivot 180° on the ball of the foot, and settle facing away (Poem 01 EX Vape Turn motion).",
            "len": 84,
            "default_view": "tq",
            "reference_body_img": "arena/bodies/sprint_turn_f118_p0_f118.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Face Front", "key", root={"x": 0, "y": 93, "z": 18, "yaw": 0}),
                make_kf(28, "Step Back L", "key", root={"x": 0, "y": 90, "z": -6, "yaw": -25}, spine={"fwd": 6, "twist": -15}, armL={"flex": 25, "elbow": 40}, armR={"flex": 15, "elbow": 30}, footL=[12, 5, -18], footR=[-10, 5, 18], pinL=True, pinR=True),
                make_kf(56, "Pivot Turn 145°", "brk", root={"x": 0, "y": 91, "z": -18, "yaw": -145}, spine={"twist": -20}, head={"turn": 22}, armL={"flex": 42, "elbow": 75}, armR={"flex": 18, "elbow": 25}, footL=[10, 5, -18], footR=[-12, 5, -14], handShapeL="grip", pinL=True, pinR=True),
                make_kf(83, "Settle Back 180°", "key", root={"x": 0, "y": 93, "z": -22, "yaw": -180}, footL=[10, 5, -22], footR=[-10, 5, -22], pinL=True, pinR=True),
            ],
        },

        # =====================================================================
        # GROUP 3: Acting Arena Challenges (T11..T20)
        # =====================================================================
        {
            "id": "T11_ACT001_Walk_With_Cup",
            "group": "Acting Arena Challenges",
            "name": "ACT-001 · Carry Full Cup Across Room Without Spilling",
            "cue": "Walk steadily holding a full cup in Right grip hand (`hand.R.grip`) stabilized in front of chest (`jerk < 0.45 cm/f²`).",
            "len": 80,
            "default_view": "tq",
            "reference_body_img": "arena/bodies/ACT-001_p1.png",
            "props": [
                {"type": "cup", "attach": "wristR", "label": "Full Coffee Cup"}
            ],
            "keyframes": [
                make_kf(0, "Hold Cup Steady", "key", root={"x": 0, "y": 92, "z": -30, "yaw": -18}, head={"nod": 12}, armL={"flex": -12, "elbow": 18}, handR=[14, 112, -12], handShapeR="grip", footL=[10, 5, -30], footR=[-10, 5, -30]),
                make_kf(26, "Smooth Step L", "key", root={"x": 2, "y": 91, "z": -10, "yaw": -18}, head={"nod": 10}, armL={"flex": 16, "elbow": 22}, handR=[14, 111, 8], handShapeR="grip", footL=[10, 5, 2], footR=[-10, 5, -30], pinL=True, pinR=False),
                make_kf(52, "Smooth Step R", "key", root={"x": -2, "y": 91, "z": 12, "yaw": -18}, head={"nod": 10}, armL={"flex": -16, "elbow": 20}, handR=[12, 111, 30], handShapeR="grip", footL=[10, 5, 2], footR=[-10, 5, 26], pinL=False, pinR=True),
                make_kf(79, "Present Cup", "key", root={"x": 0, "y": 92, "z": 26, "yaw": -18}, head={"nod": 6}, handR=[10, 116, 48], handShapeR="grip", footL=[10, 5, 26], footR=[-10, 5, 26], pinL=True, pinR=True),
            ],
        },
        {
            "id": "T12_ACT002_Crouch_Pick_Flower",
            "group": "Acting Arena Challenges",
            "name": "ACT-002 · Kneel & Pick Object from Floor (`foot.R.heel_up`)",
            "cue": "Drop into an asymmetrical one-knee crouch, flexing rear toes (`heel_up`) while reaching Right hand to `y=8cm` on the floor.",
            "len": 84,
            "default_view": "side",
            "reference_body_img": "arena/bodies/poet_crouch_f72_clean.png",
            "props": [
                {"type": "flower", "pos": [-6, 4, 24], "label": "Floor Object / Flower"}
            ],
            "keyframes": [
                make_kf(0, "Approach Object", "key", root={"x": 0, "y": 93, "z": 0, "yaw": -65}),
                make_kf(32, "Kneel & Reach Floor", "key", "out", root={"x": 0, "y": 56, "z": 4, "yaw": -65}, spine={"fwd": 36}, head={"nod": 24}, armL={"flex": 35, "abd": 18, "elbow": 40}, handR=[-6, 12, 24], handShapeR="grip", footL=[10, 5, 18], footR=[-10, 8, -22], footShapeL="flat", footShapeR="heel_up", pinL=True, pinR=True),
                make_kf(52, "Grasp & Lift", "brk", root={"x": 0, "y": 60, "z": 4, "yaw": -65}, spine={"fwd": 24}, head={"nod": 14}, handR=[-6, 38, 22], handShapeR="grip", footL=[10, 5, 18], footR=[-10, 8, -22], footShapeR="heel_up", pinL=True, pinR=True),
                make_kf(83, "Rise Holding Object", "key", root={"x": 0, "y": 93, "z": 6, "yaw": -65}, handR=[-8, 112, 22], handShapeR="grip", footL=[10, 5, 12], footR=[-10, 5, 2], pinL=True, pinR=True),
            ],
        },
        {
            "id": "T13_ACT004_Heavy_Box_Lift",
            "group": "Acting Arena Challenges",
            "name": "ACT-004 · Two-Hand Heavy Crate Lift & Counterweight Lean",
            "cue": "Squat wide beside a 25kg cardboard crate, lock both hands (`grip`) onto the crate sides, and drive through the legs with `-8°` trunk counterweight lean.",
            "len": 90,
            "default_view": "tq",
            "reference_body_img": "arena/bodies/heavy_box_f95_p0_f95.png",
            "props": [
                {"type": "box", "pos": [0, 22, 24], "attach_frames": [28, 90], "label": "25kg Cardboard Box"}
            ],
            "keyframes": [
                make_kf(0, "Wide Stance Over Box", "key", root={"x": 0, "y": 92, "z": 0, "yaw": -28}, footL=[15, 5, 8], footR=[-15, 5, 8]),
                make_kf(28, "Deep Squat Grip Crate", "key", "out", root={"x": 0, "y": 58, "z": -4, "yaw": -28}, spine={"fwd": 32}, head={"nod": 12}, handL=[16, 26, 22], handR=[-16, 26, 22], handShapeL="grip", handShapeR="grip", footL=[15, 5, 8], footR=[-15, 5, 8]),
                make_kf(58, "Strain & Drive Up", "brk", root={"x": 0, "y": 89, "z": 2, "yaw": -28}, spine={"fwd": -8}, head={"nod": -6}, handL=[16, 96, 20], handR=[-16, 96, 20], handShapeL="grip", handShapeR="grip", footL=[15, 5, 8], footR=[-15, 5, 8]),
                make_kf(89, "Hold Crate at Chest", "key", root={"x": 0, "y": 91, "z": 4, "yaw": -28}, spine={"fwd": -6}, handL=[15, 102, 20], handR=[-15, 102, 20], handShapeL="grip", handShapeR="grip", footL=[15, 5, 8], footR=[-15, 5, 8]),
            ],
        },
        {
            "id": "T14_ACT007_Slip_Floor_Recovery",
            "group": "Acting Arena Challenges",
            "name": "ACT-007 · Heel Slip, Prone Catch & Push-Up Floor Recovery",
            "cue": "Right heel skids forward, body drops to hands-and-knees floor support polygon, and pushes back up to standing.",
            "len": 96,
            "default_view": "side",
            "reference_body_img": "arena/bodies/poet_floor_recovery_clean.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Stride Entry", "key", root={"x": 0, "y": 93, "z": -16, "yaw": -78}),
                make_kf(22, "Heel Skid Shock", "brk", "out", root={"x": 0, "y": 72, "z": 0, "yaw": -78, "pitch": -18}, spine={"fwd": 22}, head={"nod": 18}, armL={"flex": 75, "abd": 35, "elbow": 15}, armR={"flex": 80, "abd": 35, "elbow": 15}, footL=[10, 5, -18], footR=[-10, 12, 34], handShapeL="open", handShapeR="open", footShapeR="toe_up", pinL=True, pinR=False),
                make_kf(48, "Hands & Knees Floor Catch", "key", root={"x": 0, "y": 42, "z": 6, "yaw": -78, "pitch": 35}, spine={"fwd": 38}, head={"nod": -24}, handL=[14, 6, 38], handR=[-14, 6, 38], footL=[11, 5, -24], footR=[-11, 5, -18], handShapeL="open", handShapeR="open", footShapeL="heel_up", footShapeR="heel_up", pinL=True, pinR=True),
                make_kf(72, "Push-Up Tuck Knee", "brk", root={"x": 0, "y": 64, "z": 8, "yaw": -78}, spine={"fwd": 28}, handL=[14, 48, 26], handR=[-14, 48, 26], footL=[11, 5, 16], footR=[-11, 5, -14], pinL=True, pinR=True),
                make_kf(95, "Stand & Dust Off", "key", root={"x": 0, "y": 93, "z": 10, "yaw": -78}, footL=[10, 5, 12], footR=[-10, 5, 8], pinL=True, pinR=True),
            ],
        },
        {
            "id": "T15_ACT011_Ledge_Put_On_Hands",
            "group": "Acting Arena Challenges",
            "name": "ACT-011 · Lean on Window Ledge / Table (`Put On Hands`)",
            "cue": "Step to window ledge (`y=82cm`), plant both open palms onto the sill, and lean chest weight forward over the hands.",
            "len": 84,
            "default_view": "tq",
            "reference_body_img": "arena/bodies/ledge_hang_f110_p0_f110.png",
            "props": [
                {"type": "table", "pos": [0, 82, 30], "label": "Window Ledge / Table (82cm)"}
            ],
            "keyframes": [
                make_kf(0, "Stand Before Ledge", "key", root={"x": 0, "y": 93, "z": 0, "yaw": -25}),
                make_kf(28, "Plant Palms on Ledge", "key", "out", root={"x": 0, "y": 89, "z": 8, "yaw": -25}, spine={"fwd": 28}, head={"nod": -16}, handL=[18, 84, 28], handR=[-18, 84, 28], handShapeL="open", handShapeR="open", footL=[11, 5, 0], footR=[-11, 5, -6]),
                make_kf(56, "Lean Weight & Gaze Out", "brk", root={"x": 0, "y": 87, "z": 12, "yaw": -25}, spine={"fwd": 36}, head={"nod": -24, "turn": 15}, handL=[18, 84, 28], handR=[-18, 84, 28], handShapeL="open", handShapeR="open", footL=[11, 5, 0], footR=[-11, 5, -6]),
                make_kf(83, "Push Off to Upright", "key", root={"x": 0, "y": 93, "z": 4, "yaw": -25}),
            ],
        },
        {
            "id": "T16_ACT014_Vintage_Waltz_Hold",
            "group": "Acting Arena Challenges",
            "name": "ACT-014 · 3/4 Ballroom Waltz Frame & Rise-and-Fall",
            "cue": "Hold partner waltz frame with Left arm raised (`open`) and Right hand at partner's shoulder blade, sweeping through 3/4 rise-and-fall.",
            "len": 96,
            "default_view": "tq",
            "reference_body_img": "arena/bodies/ACT-017_p0.png",
            "props": [],
            "keyframes": [
                make_kf(0, "Beat 1 · Lower & Lead L", "key", root={"x": -8, "y": 89, "z": -12, "yaw": -20, "roll": -4}, spine={"fwd": -4, "twist": 10}, head={"turn": -12, "tilt": 4}, armL={"flex": 65, "abd": 75, "elbow": 55}, armR={"flex": 58, "abd": 45, "elbow": 65}, footL=[8, 5, 8], footR=[-14, 5, -18], handShapeL="open", handShapeR="open"),
                make_kf(32, "Beat 2 · Rise & Sweep R", "key", "out", root={"x": 10, "y": 97, "z": 10, "yaw": 25, "roll": 5}, spine={"fwd": -6, "twist": -12}, head={"turn": -8, "tilt": -4}, armL={"flex": 70, "abd": 78, "elbow": 50}, armR={"flex": 62, "abd": 48, "elbow": 60}, footL=[14, 8, 4], footR=[-6, 5, 16], handShapeL="open", handShapeR="open", footShapeL="heel_up", footShapeR="heel_up"),
                make_kf(64, "Beat 3 · Close Suspension", "brk", root={"x": 6, "y": 95, "z": 12, "yaw": 12}, spine={"fwd": -3, "twist": 0}, armL={"flex": 68, "abd": 76, "elbow": 52}, armR={"flex": 60, "abd": 46, "elbow": 62}, footL=[8, 5, 14], footR=[-8, 5, 14], handShapeL="open", handShapeR="open"),
                make_kf(95, "Return Frame", "key", root={"x": -8, "y": 89, "z": -12, "yaw": -20}, armL={"flex": 65, "abd": 75, "elbow": 55}, armR={"flex": 58, "abd": 45, "elbow": 65}, footL=[8, 5, 8], footR=[-14, 5, -18], handShapeL="open", handShapeR="open"),
            ],
        },
        {
            "id": "T17_ACT019_Motorcycle_Straddle",
            "group": "Acting Arena Challenges",
            "name": "ACT-019 · Motorcycle Straddle & Throttle Grip (`Poem 04`)",
            "cue": "Straddle wide over motorcycle saddle (`y=72cm`), lock both hands in `grip` onto the handlebars, lean into a banked turn.",
            "len": 84,
            "default_view": "tq",
            "reference_body_img": "arena/bodies/ACT-011_p4.png",
            "props": [
                {"type": "motorcycle", "pos": [0, 68, 18], "label": "Motorcycle Saddle & Bars"}
            ],
            "keyframes": [
                make_kf(0, "Saddle Mount", "key", root={"x": 0, "y": 74, "z": -6, "yaw": -32}, spine={"fwd": 26}, head={"nod": -18}, handL=[18, 96, 26], handR=[-18, 96, 26], handShapeL="grip", handShapeR="grip", footL=[18, 16, -4], footR=[-18, 16, -4], footShapeL="heel_up", footShapeR="heel_up"),
                make_kf(28, "Throttle Twist & Bank Left", "key", root={"x": 8, "y": 71, "z": -4, "yaw": -24, "roll": 12}, spine={"fwd": 32, "side": 10}, head={"nod": -22, "turn": 14}, handL=[18, 94, 26], handR=[-18, 95, 28], handShapeL="grip", handShapeR="grip", footL=[18, 16, -4], footR=[-18, 16, -4]),
                make_kf(56, "Bank Right Countersteer", "brk", root={"x": -8, "y": 71, "z": -4, "yaw": -40, "roll": -12}, spine={"fwd": 32, "side": -10}, head={"nod": -22, "turn": -14}, handL=[18, 95, 28], handR=[-18, 94, 26], handShapeL="grip", handShapeR="grip", footL=[18, 16, -4], footR=[-18, 16, -4]),
                make_kf(83, "Cruising Straight", "key", root={"x": 0, "y": 74, "z": -6, "yaw": -32}, spine={"fwd": 26}, head={"nod": -18}, handL=[18, 96, 26], handR=[-18, 96, 26], handShapeL="grip", handShapeR="grip", footL=[18, 16, -4], footR=[-18, 16, -4]),
            ],
        },
        {
            "id": "T18_ACT024_Tambourine_Throw",
            "group": "Acting Arena Challenges",
            "name": "ACT-024 · Tambourine Rhythm Shake & Overhead Toss (`Poem 07/14`)",
            "cue": "Shake tambourine in Right `grip` hand at shoulder height, wind back, and toss/reach high overhead (`172°` arc).",
            "len": 84,
            "default_view": "front",
            "reference_body_img": "arena/bodies/ACT-012_p1.png",
            "props": [
                {"type": "tambourine", "attach": "wristR", "label": "Brass Tambourine"}
            ],
            "keyframes": [
                make_kf(0, "Rhythm Ready", "key", root={"yaw": -15}, armL={"flex": 40, "abd": 25, "elbow": 65}, armR={"flex": 75, "abd": 35, "elbow": 75}, handShapeL="open", handShapeR="grip"),
                make_kf(24, "Cross-Body Strike", "brk", root={"y": 90, "yaw": -8}, spine={"twist": -18}, armL={"flex": 55, "horiz": -20, "elbow": 70}, armR={"flex": 85, "horiz": -32, "elbow": 65}, handShapeL="open", handShapeR="grip"),
                make_kf(52, "High Overhead Toss Apex", "key", "out", root={"y": 96, "yaw": -18}, spine={"fwd": -10, "twist": 14}, head={"nod": -26}, armL={"flex": 65, "abd": 45, "elbow": 35}, armR={"flex": 172, "abd": 22, "elbow": 8}, handShapeL="open", handShapeR="open", footL=[12, 5, 4], footR=[-12, 8, -6], footShapeR="heel_up"),
                make_kf(83, "Catch & Settle", "key", root={"y": 92, "yaw": -15}, armL={"flex": 35, "abd": 20, "elbow": 55}, armR={"flex": 80, "abd": 30, "elbow": 70}, handShapeL="open", handShapeR="grip"),
            ],
        },
        {
            "id": "T19_ACT028_Phone_Booth_Call",
            "group": "Acting Arena Challenges",
            "name": "ACT-028 · Phone Receiver to Ear & Pacing (`Poem 09`)",
            "cue": "Pin Right `grip` hand directly to Right ear (`< 2.0 cm` target error) while pacing and gesturing with Left `open` hand.",
            "len": 84,
            "default_view": "front",
            "reference_body_img": "arena/bodies/ACT-016_p0.png",
            "props": [
                {"type": "phone", "attach": "wristR", "label": "Phone Receiver"}
            ],
            "keyframes": [
                make_kf(0, "Receiver to Ear", "key", root={"yaw": -10}, head={"tilt": -8, "nod": 6}, armL={"flex": 35, "abd": 18, "elbow": 65}, armR={"flex": 85, "abd": 42, "elbow": 128}, handShapeL="open", handShapeR="grip"),
                make_kf(28, "Emphatic Left Hand Gesture", "key", root={"x": 4, "y": 92, "yaw": 12}, spine={"twist": 12}, head={"tilt": -10, "nod": 8}, armL={"flex": 72, "abd": 38, "elbow": 42}, armR={"flex": 88, "abd": 40, "elbow": 130}, handShapeL="point", handShapeR="grip", footL=[12, 5, 8], footR=[-10, 5, -6]),
                make_kf(56, "Listen & Bow Head", "brk", root={"x": -2, "y": 90, "yaw": -18}, spine={"fwd": 12}, head={"tilt": -12, "nod": 18}, armL={"flex": 20, "abd": 12, "elbow": 85}, armR={"flex": 86, "abd": 38, "elbow": 132}, handShapeL="relaxed", handShapeR="grip", footL=[10, 5, 2], footR=[-10, 5, -4]),
                make_kf(83, "Hold Call", "key", root={"yaw": -10}, head={"tilt": -8, "nod": 6}, armL={"flex": 35, "abd": 18, "elbow": 65}, armR={"flex": 85, "abd": 42, "elbow": 128}, handShapeL="open", handShapeR="grip"),
            ],
        },
        {
            "id": "T20_ACT031_DJ_Scratch_Bounce",
            "group": "Acting Arena Challenges",
            "name": "ACT-031 · Cyber DJ Turntable Scratch & Headphone Cue (`Poem 07`)",
            "cue": "Rhythmic knee bounce behind DJ deck (`y=86cm`); Left hand holds headphone cup to ear while Right hand scratches vinyl platter.",
            "len": 80,
            "default_view": "front",
            "reference_body_img": "arena/bodies/ACT-013_p1.png",
            "props": [
                {"type": "dj_deck", "pos": [0, 84, 24], "label": "Turntable Platter Deck"}
            ],
            "keyframes": [
                make_kf(0, "Deck Groove Down", "key", root={"y": 87, "yaw": -8}, spine={"fwd": 14}, head={"nod": 16, "tilt": 10}, armL={"flex": 88, "abd": 42, "elbow": 126}, handR=[-14, 88, 24], handShapeL="grip", handShapeR="open", footL=[14, 5, 0], footR=[-14, 5, 0]),
                make_kf(20, "Crossfader Scratch In", "brk", root={"y": 92, "yaw": -4}, spine={"fwd": 10, "twist": 8}, head={"nod": 6, "tilt": 8}, armL={"flex": 88, "abd": 42, "elbow": 126}, handR=[-4, 88, 26], handShapeL="grip", handShapeR="point", footL=[14, 5, 0], footR=[-14, 5, 0]),
                make_kf(40, "Bass Drop Bounce & Hand Raise", "key", "out", root={"y": 85, "yaw": 6}, spine={"fwd": 16, "twist": -10}, head={"nod": 20}, armL={"flex": 158, "abd": 28, "elbow": 14}, handR=[-16, 88, 22], handShapeL="open", handShapeR="open", footL=[14, 5, 0], footR=[-14, 5, 0]),
                make_kf(60, "Platter Spin Back", "brk", root={"y": 91, "yaw": -6}, spine={"fwd": 12}, head={"nod": 10}, armL={"flex": 88, "abd": 42, "elbow": 126}, handR=[-22, 88, 25], handShapeL="grip", handShapeR="open", footL=[14, 5, 0], footR=[-14, 5, 0]),
                make_kf(79, "Groove Lock", "key", root={"y": 87, "yaw": -8}, spine={"fwd": 14}, head={"nod": 16, "tilt": 10}, armL={"flex": 88, "abd": 42, "elbow": 126}, handR=[-14, 88, 24], handShapeL="grip", handShapeR="open", footL=[14, 5, 0], footR=[-14, 5, 0]),
            ],
        },
    ]

    # Verify every reference_body_img exists
    for t in tests:
        info = inspect_img(t["reference_body_img"])
        t["reference_body_exists"] = info["exists"]
        t["reference_body_size"] = [info["width"], info["height"]]

    return tests


def build_captcha_challenges() -> list:
    """
    Build the 12 "What's Fucked Up?" Quick CAPTCHA Repair Challenges directly from
    `shots/arena/FAILINGS.md`, `shots/arena/REGISTRATION.md`, and the WYGWYL rig audits.
    """
    return [
        {
            "id": "cap_01_sideways_hand",
            "title": "CAPTCHA #01 · Sideways 74×43 Horizontal Hand (89° Off Forearm Bone Axis)",
            "rig_id": "poet_black_tshirt",
            "test_id": "T03_Shoulder_Arm_Wheel",
            "frame": 24,
            "target_slot": "hand_L",
            "symptom_summary": "The left hand cut-out (`74×43 px` horizontal card) sticks out sideways at 89° from the wrist like a broken fin instead of extending along the forearm.",
            "measured_defect": "Card long axis is horizontal (+X, 74px wide × 43px tall) while the forearm bone runs vertically (+Y). Naive placement sets rotation offset = 0° and pivot at [0.50, 0.18], producing an 89.2° axial error (`FAILINGS.md §5`).",
            "broken_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.38,
                "cuff_tuck": False,
                "pivot_A": [0.50, 0.18],
                "socket_B": [0.50, 0.88],
                "part_file": "arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.L.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 90.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.22, 0.48],
                "socket_B": [0.88, 0.50],
                "part_file": "arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.L.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "The 74×43 hand card was cut horizontally (wrist on left, fingers right) and placed with 0° rotation offset instead of +90° bone-axis alignment and [0.22, 0.48] wrist pin.",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The shoulder 2-bone IK pole vector is inverted behind the spine.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The torso neck socket is missing its Z-order depth offset.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The camera focal length is set to orthographic projection.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "`fit_bone(pivot_A, socket_B, wrist, tip)` measures the card's internal vector `cv = socket_B - pivot_A` (`[0.66, 0.02]`, horizontal) and rotates by `aw - ac` (`+90°`), pinning `pivot_A = [0.22, 0.48]` directly inside the sleeve cuff.",
        },
        {
            "id": "cap_02_wrist_grommet_tab",
            "title": "CAPTCHA #02 · Exposed Tracksuit Forearm & Hand Grommet Tabs Colliding",
            "rig_id": "poet_tracksuit_31",
            "test_id": "T11_ACT001_Walk_With_Cup",
            "frame": 26,
            "target_slot": "farm_R",
            "symptom_summary": "A beige/salmon rounded cardboard connector tab with a brass grommet sticks out below the Poet's black ribbed sleeve cuff (`y=1238..1408`), colliding with the top of the hand.",
            "measured_defect": "In `10_forearm_R.png` (`1024×1536`), the ribbed sleeve cuff ends at `y = 1238 px` (`0.806 * H`), while `y = 1238..1408` is an exposed paper connector tongue (`cuff_clip_ratio = 1.0` leaves 170px of raw tab visible).",
            "broken_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": False,
                "cuff_clip_ratio": 1.00,
                "pivot_A": [0.50, 0.13],
                "socket_B": [0.50, 0.90],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/10_forearm_R.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "cuff_clip_ratio": 0.806,
                "pivot_A": [0.50, 0.13],
                "socket_B": [0.50, 0.778],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/10_forearm_R.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "The forearm card's bottom grommet tongue (`y > 0.806`) is unclipped and the hand is layered in front of the sleeve instead of tucked under `socket_B = [0.50, 0.778]`.",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The upper arm card is missing its alpha channel transparency.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The pelvis hip bridge is rotated 45° clockwise.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The coffee cup prop has negative mass in the CoM solver.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "Enables `cuff_tuck = True` with `wrist_cuff_clip_y_ratio = 0.806` (clipping the protruding tab below `y=1238`), moves the wrist socket to `0.778` inside the black ribbed cuff, and renders `farm_R` (`z=9`) over `hand_R` (`z=8`).",
        },
        {
            "id": "cap_03_ankle_boot_pulltab",
            "title": "CAPTCHA #03 · Oversized Chelsea Boot (+74%) with Pull-Tab Over Jogger Cuff",
            "rig_id": "poet_tracksuit_31",
            "test_id": "T07_Even_Walk_Heel_Strike",
            "frame": 0,
            "target_slot": "foot_L",
            "symptom_summary": "The Poet's Chelsea boot is giant (`+74%` un-normalized export scale) and its upper leather shaft & tan pull-tab render on top of the black jogger pant cuff.",
            "measured_defect": "`19_boot_front_L.png` was exported at zoomed-in `1285×1230 px` card resolution (`+74%` oversize in `FAILINGS.md §2`) with `foot_L` drawn above `shin_L` and anchored at top of pull-tab (`ny=0.10`) instead of ankle shaft (`ny=0.293`).",
            "broken_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.74,
                "cuff_tuck": False,
                "cuff_clip_ratio": 1.00,
                "pivot_A": [0.50, 0.10],
                "socket_B": [0.55, 0.88],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/19_boot_front_L.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "cuff_clip_ratio": 0.843,
                "pivot_A": [0.50, 0.293],
                "socket_B": [0.55, 0.88],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/19_boot_front_L.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "The boot card is +74% un-normalized from a zoomed 1230px export and its ankle shaft (`ny=0.293`) is not tucked behind the clipped shin jogger cuff (`0.843`).",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The floor plane Y coordinate is above the knee joint.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The left and right thigh bones have zero length.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The head nod angle exceeds 90 degrees.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "Normalizes `foot_L` to `canonical_cm_len = 26 cm` (`boot_scale_to_torso = 0.29`), sets `pivot_A = [0.50, 0.293]` (`y=360px` on the boot shaft), clips `shin_L` at `0.843`, and layers `shin_L` (`z=7`) over `foot_L` (`z=6`).",
        },
        {
            "id": "cap_04_unnormalized_scale",
            "title": "CAPTCHA #04 · Six Independent Sheet Scales (Head +84%, Forearm +68%)",
            "rig_id": "weave_man",
            "test_id": "T01_360_Turntable_Spin",
            "frame": 0,
            "target_slot": "head",
            "symptom_summary": "The character looks like a caricature: the head is +84% too huge and the forearms are +68% swollen compared to the thighs.",
            "measured_defect": "Exact `FAILINGS.md §2` defect: 'The cards were never cut to one body: shin +34%, forearm +68%, torso +60%, upper arm +79%, boot +74%, head +84%. Six different errors mean six independent drawings.'",
            "broken_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.84,
                "cuff_tuck": False,
                "pivot_A": [0.50, 0.86],
                "socket_B": [0.50, 0.10],
                "part_file": "weave/cast/man/parts/head.front.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.86],
                "socket_B": [0.50, 0.10],
                "part_file": "weave/cast/man/parts/head.front.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "Cards harvested from mixed-resolution study sheets were placed at raw pixel size (+84% head, +68% forearm) without normalizing each slot to `canonical_cm_len / L_card_px`.",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The camera zoom is oscillating at 24Hz.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The character rig is using child 5.2-head bone lengths on an adult.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The ankle IK pin is attached to the neck joint.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "Divides every slot's target anatomical bone span (`canonical_cm_len`, e.g. `24 cm` head, `27 cm` forearm, `45 cm` thigh) by the pixel distance `||socket_B_px - pivot_A_px||`, bringing all 15 slots onto a single unified `cm_per_px` physical scale.",
        },
        {
            "id": "cap_05_fake_profile_torso",
            "title": "CAPTCHA #05 · Fake Side Profile Torso (IoU 0.973 Front Copy at 90° Side View)",
            "rig_id": "weave_man",
            "test_id": "T07_Even_Walk_Heel_Strike",
            "frame": 18,
            "target_slot": "torso",
            "symptom_summary": "During a 90° side-profile walk, the character's head is in profile but his chest is 220px wide facing dead-front toward the camera.",
            "measured_defect": "Exact `FAILINGS.md §2` defect: '`torso.profile` and `torso.front` are the same picture — IoU 0.973, both 220px wide, where a real side torso is about 60% of the front's width. Drawn 7,484 times across 84 clips.'",
            "broken_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.88],
                "socket_B": [0.50, 0.10],
                "part_file": "weave/cast/man/parts/torso.front.png",
                "ik_pin_foot": True,
                "foreshorten_25d": False,
            },
            "solved_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.88],
                "socket_B": [0.50, 0.10],
                "part_file": "arena/parts/kit3/v2/parts/poet.black_tshirt/body.profile.torso.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "`torso.profile` is a near-duplicate of `torso.front` (IoU 0.973, full 220px front width) with 2.5D yaw foreshortening disabled, so the chest faces the camera during a side walk.",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The spine twist angle is set to 180 degrees.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "Both arms are rendered on the far layer behind the background.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The walk cycle stride length is zero.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "Swaps in the true narrower profile torso (`body.profile.torso.png`) AND applies 2.5D cylindrical yaw foreshortening (`sx *= clamp(|cos(yaw)|, 0.62, 1.0)`) with near/far shoulder depth sorting so the torso silhouette narrows naturally at 90°.",
        },
        {
            "id": "cap_06_crouch_bbox_blowup",
            "title": "CAPTCHA #06 · Crouched Pose Scaled to Standing Height (1.85× Giant Blow-Up)",
            "rig_id": "poet_tracksuit_31",
            "test_id": "T02_Deep_Squat_ROM",
            "frame": 48,
            "target_slot": "torso",
            "symptom_summary": "At the bottom of a deep crouch (`f=48`), the figure suddenly balloons into a 1.85× giant with a massive head and torso.",
            "measured_defect": "Crouched replacement cards have wide aspect ratio (`w/h = 0.79..1.25`). Naive stage scaling maps the card's vertical bbox height to full standing height (`0.54 * stage_H`) instead of crouched height (`0.36 * stage_H`), blowing the character up by `1.50×..1.85×`.",
            "broken_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.65,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.86],
                "socket_B": [0.50, 0.088],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/01_torso_front.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.86],
                "socket_B": [0.50, 0.088],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/01_torso_front.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "The crouched pose was scaled to full standing bounding-box height (`0.54 * stage_H`) without posture-height & aspect-ratio compensation (`0.65x` for `w/h > 0.75`).",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The knee joint pole vector flipped backward.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The left foot sole pin drifted below the floor.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The head card was swapped with the pelvis card.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "Applies the global aspect-compensation formula (`if w/h > 0.75: mult = clamp(1/sqrt(1 + 1.35*(w/h - 0.5)^2), 0.36, 0.82)`) and locks single-part torso scaling to anatomical spine length (`52 cm`) regardless of crouch depth.",
        },
        {
            "id": "cap_07_elbow_brad_disconnect",
            "title": "CAPTCHA #07 · 3.8 cm Elbow & Knee Brad Disconnect During Overhead Reach",
            "rig_id": "poet_tracksuit_31",
            "test_id": "T03_Shoulder_Arm_Wheel",
            "frame": 48,
            "target_slot": "uarm_R",
            "symptom_summary": "When the arm reaches overhead, the elbow joint separates by `3.8 cm` (exceeding the `2.0 cm` brad tolerance), leaving a visible gap between upper arm and forearm.",
            "measured_defect": "The upper arm card was placed using fixed rotation around `pivot_A` (`mat_part`) with a shortened `socket_B = [0.50, 0.62]` instead of bone-span `fit_bone(pivot_A, socket_B, shoulder, elbow)`, causing a `3.8 cm` brad gap.",
            "broken_params": {
                "rot_deg": -14.0,
                "scale_mult": 0.78,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.24],
                "socket_B": [0.50, 0.62],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/09_upper_arm_R.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.14],
                "socket_B": [0.50, 0.84],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/09_upper_arm_R.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "The upper arm's distal `socket_B` is miscalibrated (`ny=0.62` instead of `0.84`) and rigid rotation was used instead of axial `fit_bone(pivot_A, socket_B, shoulder, elbow)`, opening a 3.8 cm gap.",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The hand card is missing its thumb polygon.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The floor shadow opacity is too high.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The neck collar clip ratio is inverted.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "`fit_bone(pivot_A, socket_B, pt_shoulder, pt_elbow, girth)` maps `pivot_A` (`[0.50, 0.14]`) to the shoulder and `socket_B` (`[0.50, 0.84]`) to the elbow, guaranteeing `0.0 cm` brad gap by construction while preserving transverse limb girth.",
        },
        {
            "id": "cap_08_planted_foot_drift",
            "title": "CAPTCHA #08 · Moonwalking Stance Foot (4.2 cm/frame Drift vs 0.6 cm/f Limit)",
            "rig_id": "poet_tracksuit_31",
            "test_id": "T07_Even_Walk_Heel_Strike",
            "frame": 18,
            "target_slot": "foot_L",
            "symptom_summary": "While the Poet walks forward, his planted Left stance foot slides backward across the floor like he is moonwalking on ice (`4.2 cm/frame` slip).",
            "measured_defect": "Root translation was animated without floor contact IK pinning (`ik_pin_foot = False`), causing the stance ankle to slide `4.2 cm/frame` (7× over the `TOL_DRIFT = 0.6 cm/frame` limit in `compile_vignette.py`).",
            "broken_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.293],
                "socket_B": [0.55, 0.88],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/19_boot_front_L.png",
                "ik_pin_foot": False,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.293],
                "socket_B": [0.55, 0.88],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/19_boot_front_L.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "Floor-contact IK pinning (`ik_pin_foot`) is disabled during the stance phase (`t=0.0..0.5`), allowing root motion to drag the planted foot at 4.2 cm/frame (> 0.6 cm/f tolerance).",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The Poet's sunglasses are slightly off-center.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The upper arm z-order is behind the torso.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The head card is using the 3/4 view instead of profile.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "Locks the planted foot world target `footL = [10, 5, -18]` during stance (`pinL = True`) and solves 2-bone analytical leg IK (`ik3(hipL, footL, thigh=45, shin=45, pole)`), reducing stance drift from `4.20 cm/f` to `0.00 cm/f`.",
        },
        {
            "id": "cap_09_wrong_hand_for_prop",
            "title": "CAPTCHA #09 · Flat Open Palm Used on Motorcycle Handlebar / Tambourine Rim",
            "rig_id": "poet_tracksuit_31",
            "test_id": "T17_ACT019_Motorcycle_Straddle",
            "frame": 28,
            "target_slot": "hand_R",
            "symptom_summary": "The Poet is riding the Poem 04 motorcycle, but his right hand on the throttle is a flat, spread-finger open palm instead of a closed grip.",
            "measured_defect": "Exact `FAILINGS.md §2` defect: '1,787 frames want a grip or a fist that does not exist in the default slot.' Using `18_hand_open_R.png` on a handlebar or tambourine rim breaks visual contact.",
            "broken_params": {
                "rot_deg": 25.0,
                "scale_mult": 1.15,
                "cuff_tuck": True,
                "pivot_A": [0.48, 0.255],
                "socket_B": [0.50, 0.88],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/18_hand_open_R.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.48, 0.255],
                "socket_B": [0.50, 0.88],
                "part_file": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/hand.R.grip.back.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "Slot `hand_R` is using the spread-finger `18_hand_open_R.png` card on a cylindrical prop handle instead of swapping to the closed `hand.R.grip.back.png` card.",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The motorcycle saddle height is set to 200 cm.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The shin bone is longer than the spine.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The head nod is locked to zero.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "Hot-swaps `hand_R` from `18_hand_open_R.png` to the high-res `hand.R.grip.back.png` card when `handShapeR == 'grip'` and aligns its grip center with the handlebar target.",
        },
        {
            "id": "cap_10_wrong_foot_for_kneel",
            "title": "CAPTCHA #10 · Flat Stance Boot Used on Kneeling Rear Leg Instead of `heel_up`",
            "rig_id": "poet_tracksuit_31",
            "test_id": "T12_ACT002_Crouch_Pick_Flower",
            "frame": 32,
            "target_slot": "foot_R",
            "symptom_summary": "In the kneeling flower pick (`f=32`), the rear Right foot is stiffly horizontal (`foot.R.flat`) and stabs into the floor instead of flexing on its toes (`foot.R.heel_up`).",
            "measured_defect": "When the rear knee drops low (`ankle_y = 8cm`, `shin` nearly horizontal), a flat-soled stance boot (`19_boot_front_R.png` or `foot.R.flat.png`) cannot articulate at the metatarsal ball joint.",
            "broken_params": {
                "rot_deg": -45.0,
                "scale_mult": 1.15,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.293],
                "socket_B": [0.45, 0.88],
                "part_file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/20_boot_front_R.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.35, 0.25],
                "socket_B": [0.82, 0.88],
                "part_file": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/foot.R.heel_up.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "The kneeling rear leg is using a flat stance boot instead of swapping to the flexed-toe `foot.R.heel_up.png` card anchored at the ball of the foot.",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The left arm is too short to reach the knee.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The torso is using a back view instead of profile.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The flower prop is above the head.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "Swaps `foot_R` to `foot.R.heel_up.png` whenever `footShapeR == 'heel_up'` or ankle pitch > 28°, pinning `socket_B` (`[0.82, 0.88]`) on the floor contact ball while the heel lifts cleanly.",
        },
        {
            "id": "cap_11_ex_front_face_violation",
            "title": "CAPTCHA #11 · Front-Facing Head Assigned to The EX (Violates Strict Back-Only Rule)",
            "rig_id": "ex_jacket_back",
            "test_id": "T10_Backwards_Step_Turn",
            "frame": 0,
            "target_slot": "head",
            "symptom_summary": "The EX in the Olive Bomber Jacket (`ex_jacket_back`) is rendered with the Poet's front-facing bearded face looking at the camera!",
            "measured_defect": "Director's strict canon rule for `ex_jacket_back` (Poems 01–03, 07–09, 12): `BACK_AND_3Q_BACK_ONLY_NEVER_FRONT_FACE` — the Ex's front face must never be shown at any camera yaw.",
            "broken_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.84],
                "socket_B": [0.50, 0.12],
                "part_file": "arena/parts/kit3/v2/parts/poet.black_tshirt/head.front.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 0.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.84],
                "socket_B": [0.50, 0.12],
                "part_file": "arena/parts/kit3/v2/parts/ex.ex_jacket/head.back.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "A front-facing head card was assigned to `ex_jacket_back`, violating the strict `BACK_AND_3Q_BACK_ONLY_NEVER_FRONT_FACE` rule that clamps The Ex to `head.back.png` or `head.threequarter_back.png`.",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The olive bomber jacket sleeves are too long.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The white sneakers are missing sole pins.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The camera elevation is negative.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "Enforces `strict_view_rule = 'BACK_AND_3Q_BACK_ONLY_NEVER_FRONT_FACE'` in the view-cell selector so `ex_jacket_back` only ever selects `back` or `threequarter_back` cards across all 360° of turntable yaw.",
        },
        {
            "id": "cap_12_skirt_knee_collision",
            "title": "CAPTCHA #12 · Rigid Single-Card Skirt / Dress Colliding with High Knee in Stair Climb",
            "rig_id": "woman_muse_costumes",
            "test_id": "T09_Stair_Climb",
            "frame": 56,
            "target_slot": "pelvis",
            "symptom_summary": "As the Woman / Muse climbs the stairs (`f=56`), her raised thigh and knee slice straight through the rigid vertical teal dress skirt card.",
            "measured_defect": "Exact `FAILINGS.md §2` defect: 'The skirt is one rigid card: 780 frames put her knees through it.' The pelvis/skirt card stayed locked at `0°` vertical pitch while `thigh_R` flexed to `+48°`.",
            "broken_params": {
                "rot_deg": -28.0,
                "scale_mult": 1.25,
                "cuff_tuck": False,
                "pivot_A": [0.50, 0.22],
                "socket_B": [0.50, 0.88],
                "part_file": "weave/assets/parts/skirt.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "solved_params": {
                "rot_deg": 18.0,
                "scale_mult": 1.00,
                "cuff_tuck": True,
                "pivot_A": [0.50, 0.20],
                "socket_B": [0.50, 0.82],
                "part_file": "arena/parts/kit3/v2/parts/woman.teal_dress/body.profile.pelvis.png",
                "ik_pin_foot": True,
                "foreshorten_25d": True,
            },
            "diagnostic_options": [
                {
                    "id": "opt_a",
                    "text": "The rigid `skirt.png` card is locked at 0° vertical while the knee rises through it; it needs the articulated `body.profile.pelvis.png` card coupled to `0.45 * max(thigh_flex)` drape pitch.",
                    "is_correct": True,
                },
                {
                    "id": "opt_b",
                    "text": "The staircase riser height is negative.",
                    "is_correct": False,
                },
                {
                    "id": "opt_c",
                    "text": "The Woman's head scale is set to child 5.2H.",
                    "is_correct": False,
                },
                {
                    "id": "opt_d",
                    "text": "The wrist cuff clip ratio is too small.",
                    "is_correct": False,
                },
            ],
            "solver_explanation": "Replaces the unsplit rigid `skirt.png` with the modular `body.profile.pelvis.png` hip-drape card and couples pelvis pitch to `0.45 * lead_thigh_angle` (`+18°`), clearing the rising knee.",
        },
    ]


def build_swapper_bank(rigs: list) -> dict:
    """
    Build a rich, curated, 100% git-tracked Normalized Parts Swapper Bank (`swapper_bank`)
    across `shoes_feet`, `hands`, `heads`, `torsos_pelvis`, and `limbs` so the user can see
    all shoes, hands, heads, torsos, and limbs scaled to a unified physical scale (`cm_per_px`)
    with their Control Points (`pivot_A` and `socket_B`) and hot-swap them onto any rig in 1 click!
    """
    with open(BODY_LAB_PATH, "r", encoding="utf-8") as f:
        body_lab = json.load(f)

    bank = {
        "shoes_feet": [],
        "hands": [],
        "heads": [],
        "torsos_pelvis": [],
        "limbs": [],
    }
    seen_files = {k: set() for k in bank}

    def add_item(cat: str, item_id: str, name: str, rel_file: str, char_group: str, clip_tag: str, view_angle: str, slot_hint: str, pA=None, sB=None, rot_off=0.0, cuff_clip=1.0):
        meta = inspect_img(rel_file)
        if not meta["exists"] or meta["file"] in seen_files[cat]:
            return
        seen_files[cat].add(meta["file"])
        slot_entry = make_slot_entry(
            slot_hint,
            meta["file"],
            scale_factor=1.0,
            pivot_A_override=pA,
            socket_B_override=sB,
            cuff_clip_ratio=cuff_clip,
            rot_offset_deg=rot_off,
        )
        bank[cat].append({
            "id": item_id,
            "name": name,
            "file": meta["file"],
            "character_group": char_group,
            "clip_tag": clip_tag,
            "view_angle": view_angle,
            "target_slot": slot_hint,
            "width": meta["width"],
            "height": meta["height"],
            "visible_bbox": meta["visible_bbox"],
            "canonical_cm_len": slot_entry["canonical_cm_len"],
            "normalized_cm_scale": slot_entry["cm_per_px"],
            "rot_offset_deg": slot_entry["rot_offset_deg"],
            "cuff_clip_ratio": slot_entry["cuff_clip_ratio"],
            "pivot_A": slot_entry["pivot_A"],
            "socket_B": slot_entry["socket_B"],
            "pivot_A_px": slot_entry["pivot_A_px"],
            "socket_B_px": slot_entry["socket_B_px"],
        })

    # 1. Seed first from all 10 Rigs' verified primary & variant slot cards so every rig's parts are in the swapper
    slot_to_cat = {
        "foot_L": ("shoes_feet", "Boot / Shoe L"),
        "foot_R": ("shoes_feet", "Boot / Shoe R"),
        "hand_L": ("hands", "Hand L"),
        "hand_R": ("hands", "Hand R"),
        "head": ("heads", "Head"),
        "torso": ("torsos_pelvis", "Torso"),
        "pelvis": ("torsos_pelvis", "Pelvis / Skirt"),
        "uarm_L": ("limbs", "Upper Arm"),
        "farm_L": ("limbs", "Forearm"),
        "thigh_L": ("limbs", "Thigh"),
        "shin_L": ("limbs", "Shin"),
    }

    for r in rigs:
        rname = r["short_name"]
        for sname, (cat, tag) in slot_to_cat.items():
            sdata = r["slots"].get(sname)
            if not sdata:
                continue
            add_item(
                cat,
                f"{r['id']}.{sname}",
                f"{rname} · {sname}",
                sdata["file"],
                rname,
                tag,
                "front",
                sname,
                pA=sdata["pivot_A"],
                sB=sdata["socket_B"],
                rot_off=sdata["rot_offset_deg"],
                cuff_clip=sdata["cuff_clip_ratio"],
            )
            for vk, vf in sdata.get("view_variants", {}).items():
                add_item(
                    cat,
                    f"{r['id']}.{sname}.{vk}",
                    f"{rname} · {sname} ({vk})",
                    vf,
                    rname,
                    f"{tag} ({vk})",
                    vk,
                    sname,
                    rot_off=sdata["rot_offset_deg"],
                    cuff_clip=sdata["cuff_clip_ratio"],
                )

    # 2. Add curated high-variety items from `body_lab_unified.json` across all character groups
    cat_slot_default = {
        "shoes_feet": "foot_R",
        "hands": "hand_R",
        "heads": "head",
        "torsos_pelvis": "torso",
        "limbs": "farm_R",
    }
    target_per_cat = {
        "shoes_feet": 36,
        "hands": 36,
        "heads": 36,
        "torsos_pelvis": 32,
        "limbs": 32,
    }

    for cat, max_count in target_per_cat.items():
        items = body_lab.get("categories", {}).get(cat, [])
        # Pick evenly across character groups and clip tags
        by_group = {}
        for it in items:
            cg = it.get("character_group", "Other")
            by_group.setdefault(cg, []).append(it)
        groups = list(by_group.keys())
        idx = 0
        while len(bank[cat]) < max_count and groups:
            progressed = False
            for cg in groups:
                g_list = by_group[cg]
                if idx < len(g_list):
                    progressed = True
                    it = g_list[idx]
                    sh = cat_slot_default[cat]
                    if cat == "torsos_pelvis" and "Pelvis" in it.get("clip_tag", ""):
                        sh = "pelvis"
                    elif cat == "limbs":
                        fn_low = it["file"].lower()
                        if "thigh" in fn_low:
                            sh = "thigh_L"
                        elif "shin" in fn_low or "leg" in fn_low:
                            sh = "shin_L"
                        elif "uarm" in fn_low or "upper" in fn_low:
                            sh = "uarm_L"
                        else:
                            sh = "farm_L"
                    add_item(
                        cat,
                        it["id"],
                        it["name"],
                        it["file"],
                        cg,
                        it.get("clip_tag", cat),
                        it.get("view_angle", "front"),
                        sh,
                    )
                    if len(bank[cat]) >= max_count:
                        break
            if not progressed:
                break
            idx += 1

    return bank


def build_target_poses() -> list:
    """
    Build the Target Pose Brad-Snap Bank from `shots/arena/bodies/index.json` and the clean
    harvested action figures. Each target pose carries 15 normalized Brad Socket coordinates
    (`brads_norm`) so any character rig can snap its cut-out pieces directly onto the target
    pose via `fit_bone(pivot_A, socket_B, brad_A, brad_B)`.
    """
    presets = [
        {
            "id": "TGT_01_ACT001_Walk_Stride",
            "act": "ACT-001",
            "label": "ACT-001 · Stride Walk Contact (Profile)",
            "file": "arena/bodies/ACT-001_p0.png",
            "recommended_view": "profile",
            "handShapeL": "relaxed", "handShapeR": "relaxed",
            "footShapeL": "toe_up", "footShapeR": "heel_up",
            "pose_type": "walk",
        },
        {
            "id": "TGT_02_ACT001_Walk_Passing",
            "act": "ACT-001",
            "label": "ACT-001 · Walk Passing High (Profile)",
            "file": "arena/bodies/ACT-001_p1.png",
            "recommended_view": "profile",
            "handShapeL": "relaxed", "handShapeR": "grip",
            "footShapeL": "flat", "footShapeR": "heel_up",
            "pose_type": "walk_passing",
        },
        {
            "id": "TGT_03_Man_Crouch_f72",
            "act": "ACT-003",
            "label": "ACT-003 · Man Deep Crouch #f72 (ViTPose 15/17)",
            "file": "arena/bodies/man_crouch_f72_clean.png",
            "recommended_view": "profile",
            "handShapeL": "open", "handShapeR": "grip",
            "footShapeL": "flat", "footShapeR": "heel_up",
            "pose_type": "crouch",
        },
        {
            "id": "TGT_04_Poet_Crouch_f72",
            "act": "ACT-003",
            "label": "ACT-003 · Poet Deep Crouch #f72 Clean",
            "file": "arena/bodies/poet_crouch_f72_clean.png",
            "recommended_view": "profile",
            "handShapeL": "open", "handShapeR": "grip",
            "footShapeL": "flat", "footShapeR": "heel_up",
            "pose_type": "crouch",
        },
        {
            "id": "TGT_05_Heavy_Box_f95",
            "act": "ACT-010",
            "label": "ACT-010 · Heavy Box Squat Lift #f95 (ViTPose 17/17)",
            "file": "arena/bodies/heavy_box_f95_p0_f95.png",
            "recommended_view": "threequarter",
            "handShapeL": "grip", "handShapeR": "grip",
            "footShapeL": "flat", "footShapeR": "flat",
            "pose_type": "box_lift",
        },
        {
            "id": "TGT_06_Slip_Recover_f50",
            "act": "ACT-007",
            "label": "ACT-007 · Heel Slip Shock #f50 (ViTPose 17/17)",
            "file": "arena/bodies/slip_recover_f50_p0_f50.png",
            "recommended_view": "profile",
            "handShapeL": "open", "handShapeR": "open",
            "footShapeL": "flat", "footShapeR": "toe_up",
            "pose_type": "slip",
        },
        {
            "id": "TGT_07_Floor_Recovery_Clean",
            "act": "ACT-008",
            "label": "ACT-008 · Push-Up Floor Recovery Clean",
            "file": "arena/bodies/poet_floor_recovery_clean.png",
            "recommended_view": "profile",
            "handShapeL": "open", "handShapeR": "open",
            "footShapeL": "heel_up", "footShapeR": "heel_up",
            "pose_type": "floor_recovery",
        },
        {
            "id": "TGT_08_Ledge_Hang_f110",
            "act": "ACT-006",
            "label": "ACT-006 · Window Ledge Brace #f110 (ViTPose 17/17)",
            "file": "arena/bodies/ledge_hang_f110_p0_f110.png",
            "recommended_view": "threequarter",
            "handShapeL": "open", "handShapeR": "open",
            "footShapeL": "flat", "footShapeR": "heel_up",
            "pose_type": "reach_ledge",
        },
        {
            "id": "TGT_09_Sprint_Brake_f65",
            "act": "ACT-002",
            "label": "ACT-002 · Fast Sprint Brake Plant #f65",
            "file": "arena/bodies/sprint_brake_f65_p0_f65.png",
            "recommended_view": "profile",
            "handShapeL": "fist", "handShapeR": "fist",
            "footShapeL": "toe_up", "footShapeR": "flat",
            "pose_type": "sprint",
        },
        {
            "id": "TGT_10_Sprint_Turn_f118",
            "act": "ACT-004",
            "label": "ACT-004 · 180 deg Pivot Turn #f118",
            "file": "arena/bodies/sprint_turn_f118_p0_f118.png",
            "recommended_view": "threequarter",
            "handShapeL": "open", "handShapeR": "fist",
            "footShapeL": "heel_up", "footShapeR": "flat",
            "pose_type": "turn",
        },
        {
            "id": "TGT_11_Kick_Balance_f60",
            "act": "ACT-014",
            "label": "ACT-014 · Single-Leg Balance Kick #f60",
            "file": "arena/bodies/kick_balance_f60_p1_f60.png",
            "recommended_view": "profile",
            "handShapeL": "open", "handShapeR": "open",
            "footShapeL": "flat", "footShapeR": "heel_up",
            "pose_type": "kick_balance",
        },
        {
            "id": "TGT_12_Dance_Waltz_ACT017",
            "act": "ACT-017",
            "label": "ACT-017 · Vintage Waltz Hold Frame",
            "file": "arena/bodies/ACT-017_p0.png",
            "recommended_view": "threequarter",
            "handShapeL": "open", "handShapeR": "open",
            "footShapeL": "flat", "footShapeR": "heel_up",
            "pose_type": "waltz",
        },
        {
            "id": "TGT_13_Handover_ACT012",
            "act": "ACT-012",
            "label": "ACT-012 · Prop Handover & Reach",
            "file": "arena/bodies/ACT-012_p1.png",
            "recommended_view": "front",
            "handShapeL": "open", "handShapeR": "grip",
            "footShapeL": "flat", "footShapeR": "flat",
            "pose_type": "reach_ledge",
        },
        {
            "id": "TGT_14_Apology_Phone_ACT016",
            "act": "ACT-016",
            "label": "ACT-016 · Phone Call / Apology Gesture",
            "file": "arena/bodies/ACT-016_p0.png",
            "recommended_view": "front",
            "handShapeL": "open", "handShapeR": "grip",
            "footShapeL": "flat", "footShapeR": "flat",
            "pose_type": "phone_gesture",
        },
    ]

    # Normalized 15-brad templates keyed by pose_type
    brad_templates = {
        "walk": {
            "headTop": [0.52, 0.06], "head": [0.52, 0.13], "neck": [0.50, 0.20],
            "shoulderL": [0.46, 0.23], "shoulderR": [0.54, 0.23],
            "elbowL": [0.36, 0.37], "elbowR": [0.64, 0.36],
            "wristL": [0.28, 0.49], "wristR": [0.74, 0.46],
            "handTipL": [0.24, 0.54], "handTipR": [0.79, 0.50],
            "pelvis": [0.50, 0.50], "hipL": [0.47, 0.52], "hipR": [0.53, 0.52],
            "kneeL": [0.62, 0.71], "kneeR": [0.38, 0.72],
            "ankleL": [0.70, 0.90], "ankleR": [0.28, 0.89],
            "toeL": [0.80, 0.92], "toeR": [0.36, 0.94],
        },
        "walk_passing": {
            "headTop": [0.50, 0.05], "head": [0.50, 0.12], "neck": [0.49, 0.19],
            "shoulderL": [0.46, 0.22], "shoulderR": [0.53, 0.22],
            "elbowL": [0.44, 0.36], "elbowR": [0.58, 0.35],
            "wristL": [0.48, 0.48], "wristR": [0.68, 0.33],
            "handTipL": [0.50, 0.53], "handTipR": [0.74, 0.31],
            "pelvis": [0.50, 0.49], "hipL": [0.48, 0.51], "hipR": [0.52, 0.51],
            "kneeL": [0.51, 0.72], "kneeR": [0.62, 0.66],
            "ankleL": [0.50, 0.92], "ankleR": [0.48, 0.82],
            "toeL": [0.60, 0.94], "toeR": [0.56, 0.88],
        },
        "crouch": {
            "headTop": [0.58, 0.14], "head": [0.57, 0.22], "neck": [0.52, 0.30],
            "shoulderL": [0.46, 0.34], "shoulderR": [0.55, 0.34],
            "elbowL": [0.42, 0.52], "elbowR": [0.66, 0.54],
            "wristL": [0.50, 0.66], "wristR": [0.76, 0.76],
            "handTipL": [0.55, 0.70], "handTipR": [0.82, 0.82],
            "pelvis": [0.34, 0.62], "hipL": [0.32, 0.64], "hipR": [0.38, 0.64],
            "kneeL": [0.62, 0.64], "kneeR": [0.56, 0.78],
            "ankleL": [0.56, 0.90], "ankleR": [0.30, 0.88],
            "toeL": [0.68, 0.92], "toeR": [0.38, 0.94],
        },
        "box_lift": {
            "headTop": [0.50, 0.10], "head": [0.50, 0.18], "neck": [0.49, 0.26],
            "shoulderL": [0.40, 0.30], "shoulderR": [0.58, 0.30],
            "elbowL": [0.36, 0.46], "elbowR": [0.64, 0.46],
            "wristL": [0.44, 0.60], "wristR": [0.58, 0.60],
            "handTipL": [0.46, 0.65], "handTipR": [0.56, 0.65],
            "pelvis": [0.48, 0.58], "hipL": [0.40, 0.60], "hipR": [0.56, 0.60],
            "kneeL": [0.34, 0.76], "kneeR": [0.64, 0.76],
            "ankleL": [0.36, 0.92], "ankleR": [0.62, 0.92],
            "toeL": [0.30, 0.95], "toeR": [0.68, 0.95],
        },
        "slip": {
            "headTop": [0.38, 0.12], "head": [0.40, 0.20], "neck": [0.43, 0.28],
            "shoulderL": [0.36, 0.31], "shoulderR": [0.48, 0.31],
            "elbowL": [0.22, 0.26], "elbowR": [0.64, 0.28],
            "wristL": [0.12, 0.18], "wristR": [0.76, 0.20],
            "handTipL": [0.08, 0.14], "handTipR": [0.82, 0.16],
            "pelvis": [0.48, 0.56], "hipL": [0.44, 0.58], "hipR": [0.52, 0.58],
            "kneeL": [0.42, 0.76], "kneeR": [0.68, 0.72],
            "ankleL": [0.36, 0.92], "ankleR": [0.84, 0.82],
            "toeL": [0.44, 0.94], "toeR": [0.92, 0.78],
        },
        "floor_recovery": {
            "headTop": [0.72, 0.24], "head": [0.70, 0.32], "neck": [0.64, 0.38],
            "shoulderL": [0.58, 0.42], "shoulderR": [0.66, 0.42],
            "elbowL": [0.56, 0.64], "elbowR": [0.68, 0.64],
            "wristL": [0.58, 0.86], "wristR": [0.70, 0.86],
            "handTipL": [0.64, 0.88], "handTipR": [0.76, 0.88],
            "pelvis": [0.38, 0.54], "hipL": [0.36, 0.56], "hipR": [0.40, 0.56],
            "kneeL": [0.48, 0.76], "kneeR": [0.26, 0.78],
            "ankleL": [0.38, 0.90], "ankleR": [0.14, 0.88],
            "toeL": [0.44, 0.94], "toeR": [0.18, 0.94],
        },
        "reach_ledge": {
            "headTop": [0.52, 0.08], "head": [0.52, 0.15], "neck": [0.50, 0.22],
            "shoulderL": [0.42, 0.26], "shoulderR": [0.58, 0.26],
            "elbowL": [0.32, 0.38], "elbowR": [0.68, 0.36],
            "wristL": [0.26, 0.48], "wristR": [0.78, 0.44],
            "handTipL": [0.22, 0.50], "handTipR": [0.84, 0.44],
            "pelvis": [0.48, 0.52], "hipL": [0.43, 0.54], "hipR": [0.53, 0.54],
            "kneeL": [0.42, 0.74], "kneeR": [0.56, 0.74],
            "ankleL": [0.40, 0.92], "ankleR": [0.58, 0.92],
            "toeL": [0.36, 0.95], "toeR": [0.64, 0.95],
        },
        "sprint": {
            "headTop": [0.62, 0.08], "head": [0.60, 0.15], "neck": [0.56, 0.22],
            "shoulderL": [0.52, 0.26], "shoulderR": [0.58, 0.26],
            "elbowL": [0.36, 0.36], "elbowR": [0.72, 0.36],
            "wristL": [0.44, 0.26], "wristR": [0.82, 0.24],
            "handTipL": [0.48, 0.22], "handTipR": [0.86, 0.20],
            "pelvis": [0.48, 0.50], "hipL": [0.46, 0.52], "hipR": [0.50, 0.52],
            "kneeL": [0.68, 0.66], "kneeR": [0.32, 0.70],
            "ankleL": [0.78, 0.88], "ankleR": [0.18, 0.82],
            "toeL": [0.86, 0.86], "toeR": [0.22, 0.90],
        },
        "turn": {
            "headTop": [0.48, 0.07], "head": [0.48, 0.14], "neck": [0.49, 0.21],
            "shoulderL": [0.40, 0.25], "shoulderR": [0.58, 0.25],
            "elbowL": [0.30, 0.38], "elbowR": [0.66, 0.38],
            "wristL": [0.36, 0.48], "wristR": [0.60, 0.48],
            "handTipL": [0.40, 0.52], "handTipR": [0.56, 0.52],
            "pelvis": [0.50, 0.50], "hipL": [0.45, 0.52], "hipR": [0.55, 0.52],
            "kneeL": [0.42, 0.72], "kneeR": [0.58, 0.72],
            "ankleL": [0.38, 0.91], "ankleR": [0.62, 0.91],
            "toeL": [0.32, 0.94], "toeR": [0.68, 0.94],
        },
        "kick_balance": {
            "headTop": [0.58, 0.10], "head": [0.56, 0.17], "neck": [0.52, 0.24],
            "shoulderL": [0.48, 0.28], "shoulderR": [0.56, 0.28],
            "elbowL": [0.66, 0.32], "elbowR": [0.36, 0.34],
            "wristL": [0.80, 0.28], "wristR": [0.22, 0.30],
            "handTipL": [0.86, 0.26], "handTipR": [0.16, 0.28],
            "pelvis": [0.48, 0.52], "hipL": [0.48, 0.54], "hipR": [0.46, 0.52],
            "kneeL": [0.50, 0.74], "kneeR": [0.28, 0.48],
            "ankleL": [0.50, 0.92], "ankleR": [0.12, 0.42],
            "toeL": [0.58, 0.94], "toeR": [0.08, 0.48],
        },
        "waltz": {
            "headTop": [0.48, 0.06], "head": [0.49, 0.13], "neck": [0.50, 0.20],
            "shoulderL": [0.40, 0.24], "shoulderR": [0.60, 0.24],
            "elbowL": [0.26, 0.28], "elbowR": [0.72, 0.32],
            "wristL": [0.22, 0.18], "wristR": [0.66, 0.24],
            "handTipL": [0.20, 0.14], "handTipR": [0.62, 0.22],
            "pelvis": [0.50, 0.50], "hipL": [0.45, 0.52], "hipR": [0.55, 0.52],
            "kneeL": [0.42, 0.72], "kneeR": [0.58, 0.72],
            "ankleL": [0.38, 0.92], "ankleR": [0.62, 0.90],
            "toeL": [0.34, 0.94], "toeR": [0.68, 0.94],
        },
        "phone_gesture": {
            "headTop": [0.50, 0.06], "head": [0.50, 0.13], "neck": [0.50, 0.20],
            "shoulderL": [0.40, 0.24], "shoulderR": [0.60, 0.24],
            "elbowL": [0.30, 0.38], "elbowR": [0.68, 0.34],
            "wristL": [0.24, 0.32], "wristR": [0.58, 0.16],
            "handTipL": [0.20, 0.28], "handTipR": [0.56, 0.13],
            "pelvis": [0.50, 0.50], "hipL": [0.45, 0.52], "hipR": [0.55, 0.52],
            "kneeL": [0.44, 0.72], "kneeR": [0.56, 0.72],
            "ankleL": [0.43, 0.92], "ankleR": [0.57, 0.92],
            "toeL": [0.39, 0.95], "toeR": [0.61, 0.95],
        },
    }

    out = []
    for pr in presets:
        meta = inspect_img(pr["file"])
        if not meta["exists"]:
            continue
        tmpl = brad_templates.get(pr["pose_type"], brad_templates["walk"])
        out.append({
            "id": pr["id"],
            "act": pr["act"],
            "label": pr["label"],
            "file": meta["file"],
            "exists": meta["exists"],
            "width": meta["width"],
            "height": meta["height"],
            "recommended_view": pr["recommended_view"],
            "handShapeL": pr["handShapeL"],
            "handShapeR": pr["handShapeR"],
            "footShapeL": pr["footShapeL"],
            "footShapeR": pr["footShapeR"],
            "brads_norm": tmpl,
        })
    return out


def main():
    rigs = build_all_rigs()
    tests = build_rom_and_crash_tests()
    captchas = build_captcha_challenges()
    swapper_bank = build_swapper_bank(rigs)
    target_poses = build_target_poses()

    # Verify zero missing files across rigs, tests, captchas, target_poses, and swapper_bank
    missing = []
    for r in rigs:
        for sname, s in r["slots"].items():
            if not inspect_img(s["file"])["exists"]:
                missing.append(("rig_slot", r["id"], sname, s["file"]))
            for vk, vf in s.get("view_variants", {}).items():
                if not inspect_img(vf)["exists"]:
                    missing.append(("rig_variant", r["id"], f"{sname}.{vk}", vf))
    for t in tests:
        if not inspect_img(t["reference_body_img"])["exists"]:
            missing.append(("test_ref_body", t["id"], t["reference_body_img"]))
    for c in captchas:
        if not inspect_img(c["broken_params"]["part_file"])["exists"]:
            missing.append(("captcha_broken", c["id"], c["broken_params"]["part_file"]))
        if not inspect_img(c["solved_params"]["part_file"])["exists"]:
            missing.append(("captcha_solved", c["id"], c["solved_params"]["part_file"]))
    for tp in target_poses:
        if not inspect_img(tp["file"])["exists"]:
            missing.append(("target_pose", tp["id"], tp["file"]))
    for cat, items in swapper_bank.items():
        for it in items:
            if not inspect_img(it["file"])["exists"]:
                missing.append(("swapper", cat, it["id"], it["file"]))

    catalog = {
        "version": "1.1.0-wygwyl-crash-lab-centaur-studio",
        "generated_by": "shots/arena/parts/kit3/build_crash_lab_data.py",
        "tolerances": {
            "TOL_DRIFT_CM_PER_FRAME": 0.6,
            "TOL_BRAD_GAP_CM": 2.0,
            "TOL_BALANCED_PCT": 95.0,
            "TOL_BONE_STRETCH_MAX": 1.15,
        },
        "stats": {
            "rig_count": len(rigs),
            "test_count": len(tests),
            "captcha_count": len(captchas),
            "target_pose_count": len(target_poses),
            "swapper_counts": {k: len(v) for k, v in swapper_bank.items()},
            "total_swapper_parts": sum(len(v) for v in swapper_bank.values()),
            "missing_files": len(missing),
        },
        "rigs": rigs,
        "rom_and_crash_tests": tests,
        "captcha_challenges": captchas,
        "target_poses": target_poses,
        "swapper_bank": swapper_bank,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"[OK] Generated {OUT_PATH}")
    print(f"     Rigs          : {len(rigs)}")
    print(f"     ROM/Crash Tests: {len(tests)}")
    print(f"     CAPTCHAs      : {len(captchas)}")
    print(f"     Target Poses  : {len(target_poses)}")
    print(f"     Swapper Parts : {catalog['stats']['total_swapper_parts']} {catalog['stats']['swapper_counts']}")
    print(f"     Missing Files : {len(missing)}")
    if missing:
        for m in missing[:15]:
            print("     [ERR] Missing:", m)
        sys.exit(1)


if __name__ == "__main__":
    main()

