#!/usr/bin/env python3
"""
WYGWYL Canonical Character Kinematics, Proportion Normalization & Piece-Scaling Solver
======================================================================================
Builds `shots/arena/parts/kit3/release_v2/character_rigs_library.json` covering all 8
canonical character rig families across the 14 poems:

  1. poet_tracksuit_31       (Poet Black/Red Tracksuit 31-part brass-pivot rig, Poems 04-14)
  2. poet_black_tshirt       (Poet Black T-Shirt rig & action packs + weave/man cycles, Poems 01-03)
  3. ex_jacket_back          (EX in Olive Bomber Jacket, strictly back/3Q-back, Poems 01-03, 07, 08, 12)
  4. vintage_party_couple    (Vintage Party Suit Man & Gown Woman paired waltz rig, Poems 01-14)
  5. woman_muse_costumes     (The Woman / Muse across 7 poem costumes: teal_dress, indigo_dress,
                              yellow_coat, apron_dress, work_shirt, stage_black, gold_gown)
  6. child_traveler_ghost    (Child Traveler / Young Poet / Ghost Child age 7 at 5.2-head 0.68x scale,
                              Poems 02, 05, 06, 09, 13)
  7. mother_ancestors_family (Mother, Ancestors, and Street-Clothes Family rigs, Poems 05, 09, 11, 14)
  8. dj_club_citizens        (DJ, Club Dancers, Guardians/Angels & Atlantis Citizens, Poems 06, 07, 08, 10, 12)

Solves:
  - Zoomed-Card Export Discrepancy via `part_scale_table` and per-part visible-axis pixel normalization
  - BBox-Height Distortion on Crouched/Seated/Falling/Prone cutouts via `canonical_height_stage_ratio`
    and continuous `aspect_compensation`
  - Adult (7.5H) vs Child Age 7 (5.2H = 0.68x adult) comparative anatomical scale
  - Foot-contact pins (`left_foot_pin`, `right_foot_pin`) and root horizontal velocity across the arena
"""

import json
import math
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS_DIR = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
REPO_ROOT = os.path.normpath(os.path.join(SHOTS_DIR, ".."))
OUT_PATH = os.path.join(HERE, "release_v2", "character_rigs_library.json")

STAGE_REF_W = 1920
STAGE_REF_H = 1080

# Canonical Per-Part Relative Scale Table (relative to Torso = 1.0)
# Solves zoomed-in card exports where hands/boots/heads/eyes were exported at ~1200px card size.
BASE_PART_SCALE_TABLE = {
    "torso": 1.00,
    "pelvis": 0.65,
    "waist_link": 0.38,
    "hip_bridge": 0.52,
    "rear_seat_cover": 0.62,
    "pelvis_front_cover": 0.62,
    "upper_arm": 0.48,
    "forearm": 0.44,
    "hand": 0.28,
    "thigh": 0.62,
    "shin": 0.58,
    "foot": 0.40,
    "head": 0.64,
    "eyes": 0.20,
    "brows": 0.18,
    "nose": 0.16,
    "mouth": 0.22,
    "sunglasses": 0.28,
    "wings": 1.35,
    "full_replacement": 1.00,
}


def compute_aspect_compensation(width: float, height: float, posture: str = "standing") -> dict:
    """
    Compute aspect compensation multiplier based on part/pose width-to-height ratio.
    Standing cutouts have w/h ~ 0.35..0.50.
    Crouched/seated cutouts have w/h ~ 0.75..1.10.
    Falling/prone/floor-recovery cutouts have w/h ~ 1.15..2.45.
    Without compensation, scaling bounding-box height to standing height blows up wide poses into giants.
    """
    ar = float(width) / max(1.0, float(height))
    threshold = 0.75
    if ar > threshold:
        raw_mult = 1.0 / math.sqrt(1.0 + 1.35 * ((ar - 0.50) ** 2))
        aspect_mult = max(0.36, min(0.84, raw_mult))
    elif ar > 0.55 and posture in ("crouch", "deep_crouch", "sitting", "kneeling", "fall", "floor_recovery"):
        raw_mult = 1.0 / math.sqrt(1.0 + 1.10 * ((ar - 0.42) ** 2))
        aspect_mult = max(0.55, min(0.88, raw_mult))
    else:
        aspect_mult = 1.0

    posture_factors = {
        "standing": 1.00,
        "walk": 1.00,
        "run": 0.96,
        "waltz": 1.00,
        "read": 0.98,
        "reach": 1.02,
        "vape_turn": 1.00,
        "dj_spin": 0.96,
        "idle_breathe": 1.00,
        "kneeling": 0.78,
        "sitting": 0.67,
        "crouch": 0.67,
        "deep_crouch": 0.65,
        "floor_recovery": 0.58,
        "fall": 0.62,
        "falling": 0.62,
        "back_lying": 0.41,
        "side_lying": 0.41,
        "prone": 0.41,
    }
    p_factor = posture_factors.get(posture, 1.0)
    combined = round(min(aspect_mult, p_factor) if posture != "standing" else aspect_mult, 4)
    return {
        "aspect_ratio": round(ar, 4),
        "exceeds_wide_threshold": bool(ar > threshold),
        "aspect_formula_mult": round(aspect_mult, 4),
        "posture_height_mult": round(p_factor, 4),
        "combined_compensation": combined,
    }


_IMG_CACHE = {}


def inspect_image_rel(rel_shots_path: str) -> dict:
    """Inspect an image relative to `shots/` and return its dimensions and visible alpha bbox."""
    clean_rel = rel_shots_path.lstrip("/")
    if clean_rel.startswith("shots/"):
        clean_rel = clean_rel[len("shots/"):]
    abs_path = os.path.join(SHOTS_DIR, clean_rel)
    if clean_rel in _IMG_CACHE:
        return _IMG_CACHE[clean_rel]

    if not os.path.exists(abs_path):
        info = {
            "exists": False,
            "file": clean_rel,
            "repo_path": "shots/" + clean_rel,
            "width": 256,
            "height": 256,
            "visible_bbox": [0, 0, 256, 256],
            "visible_w": 256,
            "visible_h": 256,
            "aspect_ratio": 1.0,
        }
        _IMG_CACHE[clean_rel] = info
        return info

    try:
        with Image.open(abs_path) as im:
            w, h = im.size
            if im.mode in ("RGBA", "LA") or "transparency" in im.info:
                alpha = im.convert("RGBA").split()[-1]
                # Use threshold 16 to ignore faint edge noise
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
                "file": clean_rel,
                "repo_path": "shots/" + clean_rel,
                "width": w,
                "height": h,
                "visible_bbox": [bb[0], bb[1], bb[2], bb[3]],
                "visible_w": vw,
                "visible_h": vh,
                "aspect_ratio": round(vw / max(1.0, float(vh)), 4),
            }
    except Exception:
        info = {
            "exists": True,
            "file": clean_rel,
            "repo_path": "shots/" + clean_rel,
            "width": 256,
            "height": 256,
            "visible_bbox": [0, 0, 256, 256],
            "visible_w": 256,
            "visible_h": 256,
            "aspect_ratio": 1.0,
        }
    _IMG_CACHE[clean_rel] = info
    return info


def resolve_part_entry(
    slot: str,
    rel_shots_path: str,
    canonical_height_ratio: float,
    torso_fraction: float,
    part_scale_table: dict,
    pivots: list = None,
    view: str = "front",
    posture: str = "standing",
    label: str = None,
) -> dict:
    """
    Build a resolved part specification with exact anatomical pixel scale normalization.
    """
    meta = inspect_image_rel(rel_shots_path)
    slot_key = slot.split(".")[0]
    rel_scale = part_scale_table.get(slot, part_scale_table.get(slot_key, 0.50))

    # Target anatomical size on a 1080p reference stage at Z = 1.0
    torso_stage_px = STAGE_REF_H * canonical_height_ratio * torso_fraction
    if slot_key == "full_replacement":
        comp = compute_aspect_compensation(meta["visible_w"], meta["visible_h"], posture=posture)
        target_stage_px = STAGE_REF_H * canonical_height_ratio * comp["combined_compensation"]
        ref_span_px = float(meta["visible_h"])
    elif slot_key in ("eyes", "brows", "mouth", "sunglasses", "hand", "foot"):
        # Use major visible axis so wide/flat hands, shoes, and eye strips never blow up vertically
        comp = compute_aspect_compensation(meta["visible_w"], meta["visible_h"], posture="standing")
        target_stage_px = torso_stage_px * rel_scale
        ref_span_px = float(max(meta["visible_w"], meta["visible_h"]))
    else:
        comp = compute_aspect_compensation(meta["visible_w"], meta["visible_h"], posture="standing")
        target_stage_px = torso_stage_px * rel_scale
        ref_span_px = float(meta["visible_h"])

    pixel_scale_1080p = round(target_stage_px / max(1.0, ref_span_px), 5)
    naive_scale_1080p = round((STAGE_REF_H * canonical_height_ratio) / max(1.0, float(meta["visible_h"])), 5)

    # Default normalized pivots if none supplied
    if not pivots:
        default_pivots = {
            "torso": [
                {"id": "waist", "nx": 0.50, "ny": 0.88},
                {"id": "neck", "nx": 0.50, "ny": 0.10},
                {"id": "shoulder_L", "nx": 0.78, "ny": 0.20},
                {"id": "shoulder_R", "nx": 0.22, "ny": 0.20},
            ],
            "pelvis": [
                {"id": "waist", "nx": 0.50, "ny": 0.16},
                {"id": "hip_L", "nx": 0.68, "ny": 0.72},
                {"id": "hip_R", "nx": 0.32, "ny": 0.72},
            ],
            "upper_arm": [
                {"id": "shoulder", "nx": 0.50, "ny": 0.14},
                {"id": "elbow", "nx": 0.50, "ny": 0.86},
            ],
            "forearm": [
                {"id": "elbow", "nx": 0.50, "ny": 0.14},
                {"id": "wrist", "nx": 0.50, "ny": 0.86},
            ],
            "hand": [{"id": "wrist", "nx": 0.50, "ny": 0.18}],
            "thigh": [
                {"id": "hip", "nx": 0.50, "ny": 0.14},
                {"id": "knee", "nx": 0.50, "ny": 0.86},
            ],
            "shin": [
                {"id": "knee", "nx": 0.50, "ny": 0.14},
                {"id": "ankle", "nx": 0.50, "ny": 0.88},
            ],
            "foot": [
                {"id": "ankle", "nx": 0.45, "ny": 0.28},
                {"id": "sole_pin", "nx": 0.55, "ny": 0.92},
            ],
            "head": [{"id": "neck", "nx": 0.50, "ny": 0.86}],
            "full_replacement": [
                {"id": "hip_root", "nx": 0.50, "ny": 0.55},
                {"id": "floor_pin", "nx": 0.50, "ny": 0.95},
            ],
        }
        bx0, by0, bx1, by1 = meta["visible_bbox"]
        bw, bh = max(1, bx1 - bx0), max(1, by1 - by0)
        pivots = []
        for dp in default_pivots.get(slot_key, [{"id": "center", "nx": 0.5, "ny": 0.5}]):
            pivots.append({
                "id": dp["id"],
                "x": round(bx0 + dp["nx"] * bw, 1),
                "y": round(by0 + dp["ny"] * bh, 1),
                "nx": dp["nx"],
                "ny": dp["ny"],
                "r": 12.0,
            })

    return {
        "slot": slot,
        "label": label or f"{slot} ({view})",
        "view": view,
        "posture": posture,
        "file": meta["file"],
        "repo_path": meta["repo_path"],
        "exists": meta["exists"],
        "width": meta["width"],
        "height": meta["height"],
        "visible_bbox": meta["visible_bbox"],
        "visible_w": meta["visible_w"],
        "visible_h": meta["visible_h"],
        "aspect_ratio": meta["aspect_ratio"],
        "part_scale_ratio": rel_scale,
        "target_stage_px_1080p": round(target_stage_px, 2),
        "solved_pixel_scale_1080p": pixel_scale_1080p,
        "naive_bbox_scale_1080p": naive_scale_1080p,
        "scale_correction_factor": round(pixel_scale_1080p / max(1e-6, naive_scale_1080p), 4),
        "aspect_compensation": comp,
        "pivots": pivots,
    }


def build_locomotion_cycles(
    rig_id: str,
    base_h_ratio: float,
    adult_scale: float = 1.0,
    back_only: bool = False,
    paired_couple: bool = False,
) -> dict:
    """
    Generate the 11 canonical locomotion and acting cycles with exact foot-contact pin intervals,
    root horizontal velocity, posture height ratios, aspect compensation, and joint angles.
    """
    default_view_move = "threequarter_back" if back_only else "profile"
    default_view_front = "back" if back_only else "front"
    default_view_3q = "threequarter_back" if back_only else "threequarter"

    v_scale = round(adult_scale, 3)

    cycles = {
        "walk": {
            "cycle_id": "walk",
            "label": "Arena Stride Walk (Foot-Pinned)",
            "duration_sec": round(1.15 / max(0.75, math.sqrt(adult_scale)), 2),
            "loop": True,
            "mode": "procedural_jointed",
            "posture_state": "standing",
            "active_height_stage_ratio": round(base_h_ratio, 4),
            "root_velocity_stage_per_sec": round(0.115 * v_scale, 4),
            "stride_length_stage_ratio": round(0.088 * v_scale, 4),
            "view_constraint": default_view_move,
            "foot_contact_pins": [
                {
                    "pin_id": "left_foot_pin",
                    "foot": "L",
                    "t_start": 0.00,
                    "t_end": 0.50,
                    "pin_to_floor": True,
                    "anchor_socket": "sole_pin",
                    "ground_y_offset_ratio": 0.0,
                },
                {
                    "pin_id": "right_foot_pin",
                    "foot": "R",
                    "t_start": 0.50,
                    "t_end": 1.00,
                    "pin_to_floor": True,
                    "anchor_socket": "sole_pin",
                    "ground_y_offset_ratio": 0.0,
                },
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "contact_heel_L",
                    "left_foot_pin": True,
                    "right_foot_pin": False,
                    "root_dy_ratio": -0.008,
                    "height_stage_ratio": round(base_h_ratio * 0.985, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 4.0, "pelvis": -2.0, "head": -2.0,
                        "uarm_L": -24.0, "farm_L": -18.0, "hand_L": -5.0,
                        "uarm_R": 22.0, "farm_R": -12.0, "hand_R": 4.0,
                        "thigh_L": 26.0, "shin_L": -6.0, "foot_L": 12.0,
                        "thigh_R": -22.0, "shin_R": -28.0, "foot_R": -18.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "relaxed"},
                },
                {
                    "t": 0.25,
                    "phase": "passing_high_L_pinned",
                    "left_foot_pin": True,
                    "right_foot_pin": False,
                    "root_dy_ratio": 0.012,
                    "height_stage_ratio": round(base_h_ratio * 1.008, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 2.0, "pelvis": 0.0, "head": 0.0,
                        "uarm_L": 0.0, "farm_L": -14.0, "hand_L": 0.0,
                        "uarm_R": 0.0, "farm_R": -14.0, "hand_R": 0.0,
                        "thigh_L": 4.0, "shin_L": -2.0, "foot_L": 0.0,
                        "thigh_R": 14.0, "shin_R": -48.0, "foot_R": -12.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "relaxed"},
                },
                {
                    "t": 0.50,
                    "phase": "contact_heel_R",
                    "left_foot_pin": False,
                    "right_foot_pin": True,
                    "root_dy_ratio": -0.008,
                    "height_stage_ratio": round(base_h_ratio * 0.985, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 4.0, "pelvis": 2.0, "head": -2.0,
                        "uarm_L": 22.0, "farm_L": -12.0, "hand_L": 4.0,
                        "uarm_R": -24.0, "farm_R": -18.0, "hand_R": -5.0,
                        "thigh_L": -22.0, "shin_L": -28.0, "foot_L": -18.0,
                        "thigh_R": 26.0, "shin_R": -6.0, "foot_R": 12.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "relaxed"},
                },
                {
                    "t": 0.75,
                    "phase": "passing_high_R_pinned",
                    "left_foot_pin": False,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.012,
                    "height_stage_ratio": round(base_h_ratio * 1.008, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 2.0, "pelvis": 0.0, "head": 0.0,
                        "uarm_L": 0.0, "farm_L": -14.0, "hand_L": 0.0,
                        "uarm_R": 0.0, "farm_R": -14.0, "hand_R": 0.0,
                        "thigh_L": 14.0, "shin_L": -48.0, "foot_L": -12.0,
                        "thigh_R": 4.0, "shin_R": -2.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "relaxed"},
                },
            ],
        },
        "run": {
            "cycle_id": "run",
            "label": "Urgent Corridor Run / Sprint",
            "duration_sec": round(0.72 / max(0.75, math.sqrt(adult_scale)), 2),
            "loop": True,
            "mode": "procedural_jointed",
            "posture_state": "run",
            "active_height_stage_ratio": round(base_h_ratio * 0.96, 4),
            "root_velocity_stage_per_sec": round(0.235 * v_scale, 4),
            "stride_length_stage_ratio": round(0.145 * v_scale, 4),
            "view_constraint": default_view_move,
            "foot_contact_pins": [
                {"pin_id": "left_foot_pin", "foot": "L", "t_start": 0.00, "t_end": 0.35, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "flight_A", "foot": "none", "t_start": 0.35, "t_end": 0.50, "pin_to_floor": False, "anchor_socket": "airborne"},
                {"pin_id": "right_foot_pin", "foot": "R", "t_start": 0.50, "t_end": 0.85, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "flight_B", "foot": "none", "t_start": 0.85, "t_end": 1.00, "pin_to_floor": False, "anchor_socket": "airborne"},
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "drive_strike_L",
                    "left_foot_pin": True,
                    "right_foot_pin": False,
                    "root_dy_ratio": -0.022,
                    "height_stage_ratio": round(base_h_ratio * 0.95, 4),
                    "aspect_comp_mult": 0.96,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 16.0, "pelvis": 6.0, "head": -8.0,
                        "uarm_L": -48.0, "farm_L": -65.0, "hand_L": 0.0,
                        "uarm_R": 44.0, "farm_R": -58.0, "hand_R": 0.0,
                        "thigh_L": 42.0, "shin_L": -18.0, "foot_L": 16.0,
                        "thigh_R": -38.0, "shin_R": -64.0, "foot_R": -28.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_O", "hand_L": "fist", "hand_R": "fist"},
                },
                {
                    "t": 0.38,
                    "phase": "aerial_suspension_L",
                    "left_foot_pin": False,
                    "right_foot_pin": False,
                    "root_dy_ratio": 0.028,
                    "height_stage_ratio": round(base_h_ratio * 0.98, 4),
                    "aspect_comp_mult": 0.96,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 14.0, "pelvis": 4.0, "head": -6.0,
                        "uarm_L": 12.0, "farm_L": -72.0, "hand_L": 0.0,
                        "uarm_R": -12.0, "farm_R": -72.0, "hand_R": 0.0,
                        "thigh_L": -26.0, "shin_L": -42.0, "foot_L": -22.0,
                        "thigh_R": 48.0, "shin_R": -52.0, "foot_R": 8.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_O", "hand_L": "fist", "hand_R": "fist"},
                },
                {
                    "t": 0.50,
                    "phase": "drive_strike_R",
                    "left_foot_pin": False,
                    "right_foot_pin": True,
                    "root_dy_ratio": -0.022,
                    "height_stage_ratio": round(base_h_ratio * 0.95, 4),
                    "aspect_comp_mult": 0.96,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 16.0, "pelvis": -6.0, "head": -8.0,
                        "uarm_L": 44.0, "farm_L": -58.0, "hand_L": 0.0,
                        "uarm_R": -48.0, "farm_R": -65.0, "hand_R": 0.0,
                        "thigh_L": -38.0, "shin_L": -64.0, "foot_L": -28.0,
                        "thigh_R": 42.0, "shin_R": -18.0, "foot_R": 16.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_O", "hand_L": "fist", "hand_R": "fist"},
                },
                {
                    "t": 0.88,
                    "phase": "aerial_suspension_R",
                    "left_foot_pin": False,
                    "right_foot_pin": False,
                    "root_dy_ratio": 0.028,
                    "height_stage_ratio": round(base_h_ratio * 0.98, 4),
                    "aspect_comp_mult": 0.96,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 14.0, "pelvis": -4.0, "head": -6.0,
                        "uarm_L": -12.0, "farm_L": -72.0, "hand_L": 0.0,
                        "uarm_R": 12.0, "farm_R": -72.0, "hand_R": 0.0,
                        "thigh_L": 48.0, "shin_L": -52.0, "foot_L": 8.0,
                        "thigh_R": -26.0, "shin_R": -42.0, "foot_R": -22.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_O", "hand_L": "fist", "hand_R": "fist"},
                },
            ],
        },
        "waltz": {
            "cycle_id": "waltz",
            "label": "3/4 Slow-Motion Ballroom Waltz",
            "duration_sec": 2.40,
            "loop": True,
            "mode": "paired_choreography" if paired_couple else "procedural_jointed",
            "posture_state": "waltz",
            "active_height_stage_ratio": round(base_h_ratio, 4),
            "root_velocity_stage_per_sec": round(0.042 * v_scale, 4),
            "stride_length_stage_ratio": round(0.065 * v_scale, 4),
            "view_constraint": default_view_3q,
            "foot_contact_pins": [
                {"pin_id": "left_foot_pin", "foot": "L", "t_start": 0.00, "t_end": 0.34, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "right_foot_pin", "foot": "R", "t_start": 0.34, "t_end": 0.67, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "both_feet_close", "foot": "LR", "t_start": 0.67, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "beat_1_lower_lead_L",
                    "left_foot_pin": True,
                    "right_foot_pin": False,
                    "root_dy_ratio": -0.015,
                    "height_stage_ratio": round(base_h_ratio * 0.98, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_3q,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": -5.0, "pelvis": -3.0, "head": 6.0,
                        "uarm_L": -58.0, "farm_L": -35.0, "hand_L": 12.0,
                        "uarm_R": 46.0, "farm_R": -48.0, "hand_R": -10.0,
                        "thigh_L": 20.0, "shin_L": -14.0, "foot_L": 6.0,
                        "thigh_R": -18.0, "shin_R": -10.0, "foot_R": -12.0,
                    },
                    "expression": {"eyes": "closed", "brows": "rest", "mouth": "smile", "hand_L": "open", "hand_R": "open"},
                },
                {
                    "t": 0.34,
                    "phase": "beat_2_rise_sweep_R",
                    "left_foot_pin": False,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.018,
                    "height_stage_ratio": round(base_h_ratio * 1.015, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_front,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 5.0, "pelvis": 3.0, "head": -4.0,
                        "uarm_L": -64.0, "farm_L": -28.0, "hand_L": 16.0,
                        "uarm_R": 52.0, "farm_R": -42.0, "hand_R": -8.0,
                        "thigh_L": -14.0, "shin_L": -8.0, "foot_L": -14.0,
                        "thigh_R": 18.0, "shin_R": -6.0, "foot_R": -10.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "smile", "hand_L": "open", "hand_R": "open"},
                },
                {
                    "t": 0.67,
                    "phase": "beat_3_close_suspension",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.010,
                    "height_stage_ratio": round(base_h_ratio * 1.005, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_3q,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 0.0, "pelvis": 0.0, "head": 2.0,
                        "uarm_L": -60.0, "farm_L": -32.0, "hand_L": 14.0,
                        "uarm_R": 48.0, "farm_R": -45.0, "hand_R": -9.0,
                        "thigh_L": 3.0, "shin_L": -4.0, "foot_L": 0.0,
                        "thigh_R": -3.0, "shin_R": -4.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "smile", "hand_L": "open", "hand_R": "open"},
                },
            ],
        },
        "read": {
            "cycle_id": "read",
            "label": "Poem Sheet Reading & Gesture",
            "duration_sec": 2.20,
            "loop": True,
            "mode": "procedural_jointed",
            "posture_state": "read",
            "active_height_stage_ratio": round(base_h_ratio * 0.99, 4),
            "root_velocity_stage_per_sec": 0.0,
            "stride_length_stage_ratio": 0.0,
            "view_constraint": default_view_3q,
            "foot_contact_pins": [
                {"pin_id": "left_foot_pin", "foot": "L", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "right_foot_pin", "foot": "R", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "hold_page_scan",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.0,
                    "height_stage_ratio": round(base_h_ratio * 0.99, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_3q,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 3.0, "pelvis": 0.0, "head": 14.0,
                        "uarm_L": 32.0, "farm_L": -68.0, "hand_L": 12.0,
                        "uarm_R": 18.0, "farm_R": -54.0, "hand_R": 8.0,
                        "thigh_L": 2.0, "shin_L": -2.0, "foot_L": 0.0,
                        "thigh_R": -3.0, "shin_R": -2.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "open_A", "hand_L": "grip", "hand_R": "open"},
                },
                {
                    "t": 0.50,
                    "phase": "recite_cadence_lift",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.006,
                    "height_stage_ratio": round(base_h_ratio, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_front,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": -2.0, "pelvis": 0.0, "head": -4.0,
                        "uarm_L": 28.0, "farm_L": -62.0, "hand_L": 10.0,
                        "uarm_R": 45.0, "farm_R": -32.0, "hand_R": 18.0,
                        "thigh_L": 2.0, "shin_L": 0.0, "foot_L": 0.0,
                        "thigh_R": -2.0, "shin_R": 0.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_O", "hand_L": "grip", "hand_R": "open"},
                },
            ],
        },
        "reach": {
            "cycle_id": "reach",
            "label": "High Overhead / Horizon Reach",
            "duration_sec": 1.80,
            "loop": True,
            "mode": "procedural_jointed",
            "posture_state": "reach",
            "active_height_stage_ratio": round(base_h_ratio * 1.02, 4),
            "root_velocity_stage_per_sec": round(0.020 * v_scale, 4),
            "stride_length_stage_ratio": round(0.035 * v_scale, 4),
            "view_constraint": default_view_3q,
            "foot_contact_pins": [
                {"pin_id": "left_foot_pin", "foot": "L", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "right_foot_pin", "foot": "R", "t_start": 0.00, "t_end": 0.45, "pin_to_floor": True, "anchor_socket": "sole_pin"},
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "gather_chest",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": -0.006,
                    "height_stage_ratio": round(base_h_ratio * 0.99, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_3q,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 4.0, "pelvis": 0.0, "head": -4.0,
                        "uarm_L": 25.0, "farm_L": -45.0, "hand_L": 0.0,
                        "uarm_R": 30.0, "farm_R": -55.0, "hand_R": 0.0,
                        "thigh_L": 6.0, "shin_L": -6.0, "foot_L": 0.0,
                        "thigh_R": -6.0, "shin_R": -4.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "open", "hand_R": "open"},
                },
                {
                    "t": 0.55,
                    "phase": "apex_extension",
                    "left_foot_pin": True,
                    "right_foot_pin": False,
                    "root_dy_ratio": 0.016,
                    "height_stage_ratio": round(base_h_ratio * 1.02, 4),
                    "aspect_comp_mult": 0.95,
                    "active_view": default_view_3q,
                    "replacement_pose": "reach",
                    "joint_angles_deg": {
                        "torso": -8.0, "pelvis": -4.0, "head": -18.0,
                        "uarm_L": 118.0, "farm_L": -12.0, "hand_L": 20.0,
                        "uarm_R": 132.0, "farm_R": -8.0, "hand_R": 24.0,
                        "thigh_L": 10.0, "shin_L": -2.0, "foot_L": -8.0,
                        "thigh_R": -18.0, "shin_R": -12.0, "foot_R": -16.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_O", "hand_L": "open", "hand_R": "open"},
                },
            ],
        },
        "crouch": {
            "cycle_id": "crouch",
            "label": "Deep Crouch & Aspect-Compensated Hold",
            "duration_sec": 1.90,
            "loop": True,
            "mode": "hybrid_replacement",
            "posture_state": "deep_crouch",
            "active_height_stage_ratio": round(base_h_ratio * 0.667, 4),  # 0.36 for 0.54 adult, 0.25 for 0.37 child
            "root_velocity_stage_per_sec": 0.0,
            "stride_length_stage_ratio": 0.0,
            "view_constraint": default_view_move,
            "foot_contact_pins": [
                {"pin_id": "left_foot_pin", "foot": "L", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "right_foot_pin", "foot": "R", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "standing_entry",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.0,
                    "height_stage_ratio": round(base_h_ratio, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 6.0, "pelvis": 0.0, "head": 4.0,
                        "uarm_L": 10.0, "farm_L": -20.0, "hand_L": 0.0,
                        "uarm_R": 14.0, "farm_R": -24.0, "hand_R": 0.0,
                        "thigh_L": 8.0, "shin_L": -10.0, "foot_L": 2.0,
                        "thigh_R": -4.0, "shin_R": -8.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "relaxed"},
                },
                {
                    "t": 0.35,
                    "phase": "kneel_transition",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": -0.12,
                    "height_stage_ratio": round(base_h_ratio * 0.778, 4),  # 0.42 for adult
                    "aspect_comp_mult": 0.78,
                    "active_view": default_view_move,
                    "replacement_pose": "kneeling",
                    "joint_angles_deg": {
                        "torso": 22.0, "pelvis": 12.0, "head": -10.0,
                        "uarm_L": 34.0, "farm_L": -48.0, "hand_L": 12.0,
                        "uarm_R": 38.0, "farm_R": -52.0, "hand_R": 15.0,
                        "thigh_L": 58.0, "shin_L": -78.0, "foot_L": 20.0,
                        "thigh_R": 42.0, "shin_R": -86.0, "foot_R": 24.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "rest", "hand_L": "open", "hand_R": "open"},
                },
                {
                    "t": 0.65,
                    "phase": "deep_crouch_locked",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": -0.18,
                    "height_stage_ratio": round(base_h_ratio * 0.667, 4),  # 0.36 for adult, 0.25 for child
                    "aspect_comp_mult": 0.67,
                    "active_view": default_view_move,
                    "replacement_pose": "deep_crouch",
                    "joint_angles_deg": {
                        "torso": 36.0, "pelvis": 20.0, "head": -18.0,
                        "uarm_L": 48.0, "farm_L": -65.0, "hand_L": 22.0,
                        "uarm_R": 52.0, "farm_R": -70.0, "hand_R": 25.0,
                        "thigh_L": 82.0, "shin_L": -112.0, "foot_L": 30.0,
                        "thigh_R": 76.0, "shin_R": -115.0, "foot_R": 32.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_O", "hand_L": "open", "hand_R": "open"},
                },
            ],
        },
        "fall": {
            "cycle_id": "fall",
            "label": "Gravity Fall to Prone (Aspect-Solved)",
            "duration_sec": 1.65,
            "loop": True,
            "mode": "hybrid_replacement",
            "posture_state": "prone",
            "active_height_stage_ratio": round(base_h_ratio * 0.407, 4),  # 0.22 for 0.54 adult, 0.15 for 0.37 child
            "root_velocity_stage_per_sec": round(-0.045 * v_scale, 4),
            "stride_length_stage_ratio": round(0.075 * v_scale, 4),
            "view_constraint": default_view_move,
            "foot_contact_pins": [
                {"pin_id": "left_foot_pin", "foot": "L", "t_start": 0.00, "t_end": 0.30, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "hip_ground_pin", "foot": "pelvis", "t_start": 0.65, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "hip_root"},
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "loss_of_balance",
                    "left_foot_pin": True,
                    "right_foot_pin": False,
                    "root_dy_ratio": 0.0,
                    "height_stage_ratio": round(base_h_ratio, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": -18.0, "pelvis": -10.0, "head": 12.0,
                        "uarm_L": 65.0, "farm_L": -20.0, "hand_L": 25.0,
                        "uarm_R": -45.0, "farm_R": -15.0, "hand_R": -15.0,
                        "thigh_L": 18.0, "shin_L": -22.0, "foot_L": 8.0,
                        "thigh_R": -28.0, "shin_R": -35.0, "foot_R": -20.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_O", "hand_L": "open", "hand_R": "open"},
                },
                {
                    "t": 0.42,
                    "phase": "midair_falling_card",
                    "left_foot_pin": False,
                    "right_foot_pin": False,
                    "root_dy_ratio": -0.14,
                    "height_stage_ratio": round(base_h_ratio * 0.63, 4),  # 0.34 for adult
                    "aspect_comp_mult": 0.62,
                    "active_view": default_view_move,
                    "replacement_pose": "falling",
                    "joint_angles_deg": {
                        "torso": -48.0, "pelvis": -36.0, "head": 22.0,
                        "uarm_L": 88.0, "farm_L": -28.0, "hand_L": 30.0,
                        "uarm_R": 72.0, "farm_R": -32.0, "hand_R": 20.0,
                        "thigh_L": 44.0, "shin_L": -40.0, "foot_L": -12.0,
                        "thigh_R": 22.0, "shin_R": -52.0, "foot_R": -18.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_A", "hand_L": "open", "hand_R": "open"},
                },
                {
                    "t": 0.78,
                    "phase": "prone_back_lying_settled",
                    "left_foot_pin": False,
                    "right_foot_pin": False,
                    "root_dy_ratio": -0.32,
                    "height_stage_ratio": round(base_h_ratio * 0.407, 4),  # 0.22 for adult, 0.15 for child
                    "aspect_comp_mult": 0.41,
                    "active_view": default_view_move,
                    "replacement_pose": "back_lying",
                    "joint_angles_deg": {
                        "torso": -82.0, "pelvis": -78.0, "head": 18.0,
                        "uarm_L": 35.0, "farm_L": -15.0, "hand_L": 0.0,
                        "uarm_R": -25.0, "farm_R": -10.0, "hand_R": 0.0,
                        "thigh_L": 78.0, "shin_L": -18.0, "foot_L": -10.0,
                        "thigh_R": 72.0, "shin_R": -24.0, "foot_R": -14.0,
                    },
                    "expression": {"eyes": "closed", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "relaxed"},
                },
            ],
        },
        "floor_recovery": {
            "cycle_id": "floor_recovery",
            "label": "Floor Push-Up & Rise Recovery",
            "duration_sec": 2.10,
            "loop": True,
            "mode": "hybrid_replacement",
            "posture_state": "floor_recovery",
            "active_height_stage_ratio": round(base_h_ratio * 0.574, 4),  # 0.31 for 0.54 adult, 0.21 for 0.37 child
            "root_velocity_stage_per_sec": round(0.032 * v_scale, 4),
            "stride_length_stage_ratio": round(0.055 * v_scale, 4),
            "view_constraint": default_view_move,
            "foot_contact_pins": [
                {"pin_id": "hand_floor_pin", "foot": "hand_L", "t_start": 0.00, "t_end": 0.55, "pin_to_floor": True, "anchor_socket": "wrist"},
                {"pin_id": "left_foot_pin", "foot": "L", "t_start": 0.40, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "right_foot_pin", "foot": "R", "t_start": 0.70, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "prone_side_lying",
                    "left_foot_pin": False,
                    "right_foot_pin": False,
                    "root_dy_ratio": -0.32,
                    "height_stage_ratio": round(base_h_ratio * 0.407, 4),  # 0.22 for adult
                    "aspect_comp_mult": 0.41,
                    "active_view": default_view_move,
                    "replacement_pose": "side_lying",
                    "joint_angles_deg": {
                        "torso": 72.0, "pelvis": 68.0, "head": -22.0,
                        "uarm_L": 54.0, "farm_L": -82.0, "hand_L": 35.0,
                        "uarm_R": 42.0, "farm_R": -70.0, "hand_R": 28.0,
                        "thigh_L": 65.0, "shin_L": -95.0, "foot_L": 15.0,
                        "thigh_R": 52.0, "shin_R": -85.0, "foot_R": 10.0,
                    },
                    "expression": {"eyes": "closed", "brows": "rest", "mouth": "rest", "hand_L": "open", "hand_R": "open"},
                },
                {
                    "t": 0.38,
                    "phase": "floor_recovery_pushup",
                    "left_foot_pin": True,
                    "right_foot_pin": False,
                    "root_dy_ratio": -0.22,
                    "height_stage_ratio": round(base_h_ratio * 0.574, 4),  # 0.31 for adult
                    "aspect_comp_mult": 0.58,
                    "active_view": default_view_move,
                    "replacement_pose": "floor_recovery",
                    "joint_angles_deg": {
                        "torso": 52.0, "pelvis": 36.0, "head": -28.0,
                        "uarm_L": 40.0, "farm_L": -25.0, "hand_L": 45.0,
                        "uarm_R": 35.0, "farm_R": -30.0, "hand_R": 40.0,
                        "thigh_L": 74.0, "shin_L": -105.0, "foot_L": 28.0,
                        "thigh_R": 38.0, "shin_R": -72.0, "foot_R": 18.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_O", "hand_L": "open", "hand_R": "open"},
                },
                {
                    "t": 0.72,
                    "phase": "crouch_gather_kneel",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": -0.14,
                    "height_stage_ratio": round(base_h_ratio * 0.72, 4),  # 0.39 for adult
                    "aspect_comp_mult": 0.72,
                    "active_view": default_view_move,
                    "replacement_pose": "deep_crouch",
                    "joint_angles_deg": {
                        "torso": 28.0, "pelvis": 16.0, "head": -12.0,
                        "uarm_L": 24.0, "farm_L": -48.0, "hand_L": 10.0,
                        "uarm_R": 18.0, "farm_R": -42.0, "hand_R": 8.0,
                        "thigh_L": 52.0, "shin_L": -74.0, "foot_L": 22.0,
                        "thigh_R": 44.0, "shin_R": -68.0, "foot_R": 18.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "relaxed"},
                },
                {
                    "t": 1.00,
                    "phase": "recovered_stand",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.0,
                    "height_stage_ratio": round(base_h_ratio, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_move,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 4.0, "pelvis": 0.0, "head": 0.0,
                        "uarm_L": 6.0, "farm_L": -14.0, "hand_L": 0.0,
                        "uarm_R": -6.0, "farm_R": -12.0, "hand_R": 0.0,
                        "thigh_L": 4.0, "shin_L": -4.0, "foot_L": 0.0,
                        "thigh_R": -4.0, "shin_R": -4.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "relaxed"},
                },
            ],
        },
        "vape_turn": {
            "cycle_id": "vape_turn",
            "label": "Back-to-3Q-Back Vape Exhale & Shoulder Turn",
            "duration_sec": 2.30,
            "loop": True,
            "mode": "procedural_jointed",
            "posture_state": "vape_turn",
            "active_height_stage_ratio": round(base_h_ratio, 4),
            "root_velocity_stage_per_sec": 0.0,
            "stride_length_stage_ratio": 0.0,
            "view_constraint": "threequarter_back" if back_only else default_view_3q,
            "foot_contact_pins": [
                {"pin_id": "left_foot_pin", "foot": "L", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "right_foot_pin", "foot": "R", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "strict_back_stance",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.0,
                    "height_stage_ratio": round(base_h_ratio, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": "back" if back_only else default_view_front,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 0.0, "pelvis": 0.0, "head": 0.0,
                        "uarm_L": -8.0, "farm_L": -16.0, "hand_L": 0.0,
                        "uarm_R": 18.0, "farm_R": -42.0, "hand_R": 10.0,
                        "thigh_L": 3.0, "shin_L": -2.0, "foot_L": 0.0,
                        "thigh_R": -4.0, "shin_R": -2.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "grip"},
                },
                {
                    "t": 0.50,
                    "phase": "threequarter_back_vape_lift",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.005,
                    "height_stage_ratio": round(base_h_ratio, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": "threequarter_back" if back_only else default_view_3q,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": -4.0, "pelvis": -2.0, "head": -12.0,
                        "uarm_L": -12.0, "farm_L": -22.0, "hand_L": 0.0,
                        "uarm_R": 58.0, "farm_R": -95.0, "hand_R": 22.0,
                        "thigh_L": 4.0, "shin_L": 0.0, "foot_L": 0.0,
                        "thigh_R": -5.0, "shin_R": -4.0, "foot_R": 4.0,
                    },
                    "expression": {"eyes": "closed", "brows": "raised", "mouth": "open_O", "hand_L": "relaxed", "hand_R": "grip"},
                },
            ],
        },
        "dj_spin": {
            "cycle_id": "dj_spin",
            "label": "Turntable Crossfader Bounce & Headphone Cue",
            "duration_sec": 1.25,
            "loop": True,
            "mode": "procedural_jointed",
            "posture_state": "dj_spin",
            "active_height_stage_ratio": round(base_h_ratio * 0.96, 4),
            "root_velocity_stage_per_sec": 0.0,
            "stride_length_stage_ratio": 0.0,
            "view_constraint": default_view_front,
            "foot_contact_pins": [
                {"pin_id": "left_foot_pin", "foot": "L", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "right_foot_pin", "foot": "R", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "deck_scratch_downbeat",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": -0.018,
                    "height_stage_ratio": round(base_h_ratio * 0.95, 4),
                    "aspect_comp_mult": 0.98,
                    "active_view": default_view_front,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 10.0, "pelvis": 4.0, "head": 14.0,
                        "uarm_L": 36.0, "farm_L": -64.0, "hand_L": 18.0,
                        "uarm_R": -42.0, "farm_R": 52.0, "hand_R": -15.0,
                        "thigh_L": 14.0, "shin_L": -22.0, "foot_L": 8.0,
                        "thigh_R": -12.0, "shin_R": -20.0, "foot_R": 6.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "smile", "hand_L": "open", "hand_R": "grip"},
                },
                {
                    "t": 0.50,
                    "phase": "drop_hand_raise_upbeat",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.012,
                    "height_stage_ratio": round(base_h_ratio * 0.99, 4),
                    "aspect_comp_mult": 0.98,
                    "active_view": default_view_3q,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": -4.0, "pelvis": -2.0, "head": -8.0,
                        "uarm_L": 115.0, "farm_L": -24.0, "hand_L": 12.0,
                        "uarm_R": 28.0, "farm_R": -58.0, "hand_R": 10.0,
                        "thigh_L": 4.0, "shin_L": -6.0, "foot_L": 0.0,
                        "thigh_R": -4.0, "shin_R": -6.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "raised", "mouth": "open_A", "hand_L": "open", "hand_R": "open"},
                },
            ],
        },
        "idle_breathe": {
            "cycle_id": "idle_breathe",
            "label": "Planted Stage Breathing & Subtle Weight Shift",
            "duration_sec": 2.80,
            "loop": True,
            "mode": "procedural_jointed",
            "posture_state": "standing",
            "active_height_stage_ratio": round(base_h_ratio, 4),
            "root_velocity_stage_per_sec": 0.0,
            "stride_length_stage_ratio": 0.0,
            "view_constraint": default_view_front,
            "foot_contact_pins": [
                {"pin_id": "left_foot_pin", "foot": "L", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
                {"pin_id": "right_foot_pin", "foot": "R", "t_start": 0.00, "t_end": 1.00, "pin_to_floor": True, "anchor_socket": "sole_pin"},
            ],
            "keyframes": [
                {
                    "t": 0.00,
                    "phase": "exhale_rest",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.0,
                    "height_stage_ratio": round(base_h_ratio, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_front,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": 0.0, "pelvis": 0.0, "head": 0.0,
                        "uarm_L": 4.0, "farm_L": -8.0, "hand_L": 0.0,
                        "uarm_R": -4.0, "farm_R": -8.0, "hand_R": 0.0,
                        "thigh_L": 2.0, "shin_L": -2.0, "foot_L": 0.0,
                        "thigh_R": -2.0, "shin_R": -2.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "relaxed"},
                },
                {
                    "t": 0.50,
                    "phase": "inhale_chest_lift",
                    "left_foot_pin": True,
                    "right_foot_pin": True,
                    "root_dy_ratio": 0.004,
                    "height_stage_ratio": round(base_h_ratio * 1.004, 4),
                    "aspect_comp_mult": 1.0,
                    "active_view": default_view_front,
                    "replacement_pose": None,
                    "joint_angles_deg": {
                        "torso": -1.5, "pelvis": 1.0, "head": -2.0,
                        "uarm_L": 7.0, "farm_L": -11.0, "hand_L": 2.0,
                        "uarm_R": -7.0, "farm_R": -11.0, "hand_R": -2.0,
                        "thigh_L": 2.0, "shin_L": -2.0, "foot_L": 0.0,
                        "thigh_R": -2.0, "shin_R": -2.0, "foot_R": 0.0,
                    },
                    "expression": {"eyes": "open", "brows": "rest", "mouth": "rest", "hand_L": "relaxed", "hand_R": "relaxed"},
                },
            ],
        },
    }
    return cycles


def build_joint_hierarchy(head_scale: float = 0.64, back_only: bool = False) -> dict:
    """Return the canonical brass-pivot hierarchy and socket offsets relative to torso height."""
    return {
        "root_bone": "pelvis",
        "hip_elevation_of_standing_height": 0.53,
        "torso_height_of_standing_height": 0.32,
        "back_only_enforced": back_only,
        "bones": {
            "pelvis": {
                "parent": None,
                "slot": "pelvis",
                "z_order": 4,
                "sockets": {
                    "waist": {"dx": 0.0, "dy": -0.18},
                    "hip_L": {"dx": 0.22, "dy": 0.12},
                    "hip_R": {"dx": -0.22, "dy": 0.12},
                },
            },
            "torso": {
                "parent": "pelvis",
                "attach_socket": "waist",
                "slot": "torso",
                "z_order": 5,
                "sockets": {
                    "neck": {"dx": 0.0, "dy": -0.86},
                    "shoulder_L": {"dx": 0.36, "dy": -0.74},
                    "shoulder_R": {"dx": -0.36, "dy": -0.74},
                },
            },
            "head": {
                "parent": "torso",
                "attach_socket": "neck",
                "slot": "head",
                "z_order": 8,
                "relative_scale_to_torso": head_scale,
                "sockets": {
                    "eyes": {"dx": 0.0, "dy": -0.44},
                    "brows": {"dx": 0.0, "dy": -0.56},
                    "nose": {"dx": 0.0, "dy": -0.34},
                    "mouth": {"dx": 0.0, "dy": -0.20},
                    "sunglasses": {"dx": 0.0, "dy": -0.45},
                },
            },
            "uarm_L": {
                "parent": "torso",
                "attach_socket": "shoulder_L",
                "slot": "upper_arm",
                "z_order": 7,
                "sockets": {"elbow": {"dx": 0.0, "dy": 0.42}},
            },
            "farm_L": {
                "parent": "uarm_L",
                "attach_socket": "elbow",
                "slot": "forearm",
                "z_order": 8,
                "sockets": {"wrist": {"dx": 0.0, "dy": 0.38}},
            },
            "hand_L": {
                "parent": "farm_L",
                "attach_socket": "wrist",
                "slot": "hand",
                "z_order": 9,
                "sockets": {},
            },
            "uarm_R": {
                "parent": "torso",
                "attach_socket": "shoulder_R",
                "slot": "upper_arm",
                "z_order": 2,
                "sockets": {"elbow": {"dx": 0.0, "dy": 0.42}},
            },
            "farm_R": {
                "parent": "uarm_R",
                "attach_socket": "elbow",
                "slot": "forearm",
                "z_order": 2,
                "sockets": {"wrist": {"dx": 0.0, "dy": 0.38}},
            },
            "hand_R": {
                "parent": "farm_R",
                "attach_socket": "wrist",
                "slot": "hand",
                "z_order": 3,
                "sockets": {},
            },
            "thigh_L": {
                "parent": "pelvis",
                "attach_socket": "hip_L",
                "slot": "thigh",
                "z_order": 6,
                "sockets": {"knee": {"dx": 0.0, "dy": 0.54}},
            },
            "shin_L": {
                "parent": "thigh_L",
                "attach_socket": "knee",
                "slot": "shin",
                "z_order": 6,
                "sockets": {"ankle": {"dx": 0.0, "dy": 0.50}},
            },
            "foot_L": {
                "parent": "shin_L",
                "attach_socket": "ankle",
                "slot": "foot",
                "z_order": 7,
                "sockets": {"sole_pin": {"dx": 0.08, "dy": 0.14}},
            },
            "thigh_R": {
                "parent": "pelvis",
                "attach_socket": "hip_R",
                "slot": "thigh",
                "z_order": 1,
                "sockets": {"knee": {"dx": 0.0, "dy": 0.54}},
            },
            "shin_R": {
                "parent": "thigh_R",
                "attach_socket": "knee",
                "slot": "shin",
                "z_order": 1,
                "sockets": {"ankle": {"dx": 0.0, "dy": 0.50}},
            },
            "foot_R": {
                "parent": "shin_R",
                "attach_socket": "ankle",
                "slot": "foot",
                "z_order": 2,
                "sockets": {"sole_pin": {"dx": 0.08, "dy": 0.14}},
            },
        },
    }


def make_posture_ratios(standing_ratio: float) -> dict:
    """Return exact stage height ratios at Z = 1.0 for every posture of a given character."""
    scale = standing_ratio / 0.54
    return {
        "standing": round(standing_ratio, 4),
        "walk": round(standing_ratio, 4),
        "run": round(standing_ratio * 0.96, 4),
        "waltz": round(standing_ratio, 4),
        "read": round(standing_ratio * 0.99, 4),
        "reach": round(standing_ratio * 1.02, 4),
        "vape_turn": round(standing_ratio, 4),
        "dj_spin": round(standing_ratio * 0.96, 4),
        "idle_breathe": round(standing_ratio, 4),
        "kneeling": round(0.42 * scale, 4),
        "sitting": round(0.36 * scale, 4),
        "crouch": round(0.36 * scale, 4),
        "deep_crouch": round(0.36 * scale, 4),
        "floor_recovery": round(0.31 * scale, 4),
        "fall": round(0.22 * scale, 4),
        "falling": round(0.34 * scale, 4),
        "back_lying": round(0.22 * scale, 4),
        "side_lying": round(0.22 * scale, 4),
        "prone": round(0.22 * scale, 4),
    }


def collect_kit_modular_parts(kit_dir: str, h_ratio: float, torso_frac: float, scale_table: dict, views=("front", "threequarter", "profile", "back")) -> dict:
    """Collect verified modular parts and assembled poses from `arena/parts/kit3/v2/parts/<kit_dir>` and `poses/<kit_dir>`."""
    parts_out = {}
    base_parts = f"arena/parts/kit3/v2/parts/{kit_dir}"
    base_poses = f"arena/parts/kit3/v2/poses/{kit_dir}"

    slot_map = [
        ("torso", "torso"),
        ("pelvis", "pelvis"),
        ("upper_arm.L", "uarm.L"),
        ("upper_arm.R", "uarm.R"),
        ("forearm.L", "farm.L"),
        ("forearm.R", "farm.R"),
        ("hand.L", "hand.L"),
        ("hand.R", "hand.R"),
        ("thigh.L", "thigh.L"),
        ("thigh.R", "thigh.R"),
        ("shin.L", "shin.L"),
        ("shin.R", "shin.R"),
        ("foot.L", "foot.L"),
        ("foot.R", "foot.R"),
    ]

    for v in views:
        for slot_name, file_suffix in slot_map:
            rel = f"{base_parts}/body.{v}.{file_suffix}.png"
            if os.path.exists(os.path.join(SHOTS_DIR, rel)):
                key = f"{v}.{slot_name}"
                parts_out[key] = resolve_part_entry(slot_name.split(".")[0], rel, h_ratio, torso_frac, scale_table, view=v, label=f"{kit_dir} {v} {slot_name}")

        head_rel = f"{base_parts}/head.{v}.png"
        if os.path.exists(os.path.join(SHOTS_DIR, head_rel)):
            parts_out[f"{v}.head"] = resolve_part_entry("head", head_rel, h_ratio, torso_frac, scale_table, view=v, label=f"{kit_dir} {v} head")

    # High-res close-up hands & feet from sheet
    for hand_fn in ("hand.R.open.palm.png", "hand.R.relaxed.back.png", "hand.R.fist.back.png", "hand.R.grip.back.png", "hand.R.point.back.png"):
        rel = f"{base_parts}/{hand_fn}"
        if os.path.exists(os.path.join(SHOTS_DIR, rel)):
            parts_out[f"closeup.{hand_fn[:-4]}"] = resolve_part_entry("hand", rel, h_ratio, torso_frac, scale_table, view="front", label=f"{kit_dir} {hand_fn[:-4]}")

    for foot_fn in ("foot.R.flat.png", "foot.R.heel_up.png", "foot.R.toe_up.png", "foot.R.front.png", "foot.R.back.png"):
        rel = f"{base_parts}/{foot_fn}"
        if os.path.exists(os.path.join(SHOTS_DIR, rel)):
            parts_out[f"closeup.{foot_fn[:-4]}"] = resolve_part_entry("foot", rel, h_ratio, torso_frac, scale_table, view="profile", label=f"{kit_dir} {foot_fn[:-4]}")

    # Replacement cards
    rep_map = [
        ("kneeling", "replacement.kneel.png", "kneeling"),
        ("deep_crouch", "replacement.crouch.png", "deep_crouch"),
        ("sitting", "replacement.sit.png", "sitting"),
        ("falling", "replacement.fall.png", "falling"),
        ("back_lying", "replacement.lie_back.png", "back_lying"),
        ("side_lying", "replacement.lie_side.png", "side_lying"),
    ]
    for rep_key, rep_fn, posture in rep_map:
        rel = f"{base_parts}/{rep_fn}"
        if os.path.exists(os.path.join(SHOTS_DIR, rel)):
            parts_out[f"replacement.{rep_key}"] = resolve_part_entry(
                "full_replacement", rel, h_ratio, torso_frac, scale_table, view="profile", posture=posture, label=f"{kit_dir} replacement {rep_key}"
            )

    # Assembled reference poses
    pose_map = [
        ("pose.stand_front", "stand_front.png", "front", "standing"),
        ("pose.stand_threequarter", "stand_threequarter.png", "threequarter", "standing"),
        ("pose.stand_profile", "stand_profile.png", "profile", "standing"),
        ("pose.stand_back", "stand_back.png", "back", "standing"),
        ("pose.walk", "walk.png", "profile", "walk"),
        ("pose.reach", "reach.png", "threequarter", "reach"),
        ("pose.kneel", "kneel.png", "profile", "kneeling"),
        ("pose.crouch", "crouch.png", "profile", "deep_crouch"),
        ("pose.sit", "sit.png", "profile", "sitting"),
        ("pose.fall", "fall.png", "profile", "falling"),
    ]
    for p_key, p_fn, p_view, posture in pose_map:
        rel = f"{base_poses}/{p_fn}"
        if os.path.exists(os.path.join(SHOTS_DIR, rel)):
            parts_out[p_key] = resolve_part_entry(
                "full_replacement", rel, h_ratio, torso_frac, scale_table, view=p_view, posture=posture, label=f"{kit_dir} assembled {p_fn[:-4]}"
            )

    return parts_out


def verify_sheets(sheet_list: list) -> list:
    """Return only sheet paths under `shots/` that exist on disk."""
    out = []
    seen = set()
    for s in sheet_list:
        clean = s.lstrip("/")
        if clean.startswith("shots/"):
            clean = clean[len("shots/"):]
        if clean not in seen and os.path.exists(os.path.join(SHOTS_DIR, clean)):
            seen.add(clean)
            out.append(clean)
    return out


def main():
    atlas_path = os.path.join(HERE, "release_v2", "wygwyl_atlas_manifest.json")
    with open(atlas_path, "r", encoding="utf-8") as f:
        atlas = json.load(f)

    tracksuit_manifest_items = {item["comp_id"]: item for item in atlas.get("tracksuitRig", [])}
    atlas_assets_by_id = {item["id"]: item for item in atlas.get("assets", [])}

    with open(os.path.join(SHOTS_DIR, "weave", "cast", "man", "cast.json"), "r", encoding="utf-8") as f:
        weave_man_cast = json.load(f)

    with open(os.path.join(SHOTS_DIR, "weave", "assets", "poet.crouch_manifest.json"), "r", encoding="utf-8") as f:
        crouch_manifest = json.load(f)

    with open(os.path.join(SHOTS_DIR, "weave", "assets", "poet.floor_recovery_manifest.json"), "r", encoding="utf-8") as f:
        recovery_manifest = json.load(f)

    rigs = {}

    # =========================================================================
    # 1. poet_tracksuit_31
    # =========================================================================
    ts_scale_table = dict(BASE_PART_SCALE_TABLE)
    ts_h_ratio = 0.54
    ts_torso_frac = 0.32
    ts_parts = {}

    # Map all 31 high-res tracksuit parts from release_v2/tracksuit/
    ts_slot_mapping = {
        "01_torso_front": ("torso", "front"),
        "02_torso_back": ("torso", "back"),
        "03_waist_link": ("waist_link", "front"),
        "04_hip_bridge": ("hip_bridge", "front"),
        "05_rear_seat_cover": ("pelvis", "back"),
        "06_pelvis_front_cover": ("pelvis", "front"),
        "07_upper_arm_L": ("upper_arm", "front"),
        "08_forearm_L": ("forearm", "front"),
        "09_upper_arm_R": ("upper_arm", "front"),
        "10_forearm_R": ("forearm", "front"),
        "11_thigh_L": ("thigh", "front"),
        "12_shin_L": ("shin", "front"),
        "13_thigh_R": ("thigh", "front"),
        "14_shin_R": ("shin", "front"),
        "15_hand_relaxed_L": ("hand", "front"),
        "16_hand_relaxed_R": ("hand", "front"),
        "17_hand_open_L": ("hand", "front"),
        "18_hand_open_R": ("hand", "front"),
        "19_boot_front_L": ("foot", "front"),
        "20_boot_front_R": ("foot", "front"),
        "21_head_front_blank": ("head", "front"),
        "22_eyes_open": ("eyes", "front"),
        "23_eyes_closed": ("eyes", "front"),
        "24_brows_rest": ("brows", "front"),
        "25_brows_raised": ("brows", "front"),
        "26_nose_front": ("nose", "front"),
        "27_mouth_rest": ("mouth", "front"),
        "28_mouth_smile": ("mouth", "front"),
        "29_mouth_open_O": ("mouth", "front"),
        "30_mouth_open_A": ("mouth", "front"),
        "31_sunglasses_front": ("sunglasses", "front"),
    }

    for comp_id, (slot_type, view_name) in ts_slot_mapping.items():
        t_item = tracksuit_manifest_items.get(comp_id, {})
        rel_file = t_item.get("file", f"arena/parts/kit3/release_v2/tracksuit/{comp_id}.png")
        pivots = t_item.get("pivots", [])
        ts_parts[f"tracksuit31.{comp_id}"] = resolve_part_entry(
            slot_type,
            rel_file,
            ts_h_ratio,
            ts_torso_frac,
            ts_scale_table,
            pivots=pivots,
            view=view_name,
            label=t_item.get("label", comp_id),
        )

    # Also merge multi-view modular parts (front/3Q/profile/back) + replacement poses
    ts_parts.update(
        collect_kit_modular_parts(
            "poet.red_black_sunglasses",
            ts_h_ratio,
            ts_torso_frac,
            ts_scale_table,
            views=("front", "threequarter", "profile", "back"),
        )
    )

    # Add cut replacement poses from kit3/v2/cut/poet.red_black_sunglasses.replacements/
    cut_rep_map = [
        ("cut_replacement.kneeling", "arena/parts/kit3/v2/cut/poet.red_black_sunglasses.replacements/pose.kneeling_one_knee.png", "kneeling"),
        ("cut_replacement.deep_crouch", "arena/parts/kit3/v2/cut/poet.red_black_sunglasses.replacements/pose.deep_crouch.png", "deep_crouch"),
        ("cut_replacement.sitting", "arena/parts/kit3/v2/cut/poet.red_black_sunglasses.replacements/pose.sitting_chair.png", "sitting"),
        ("cut_replacement.falling", "arena/parts/kit3/v2/cut/poet.red_black_sunglasses.replacements/pose.falling_back.png", "falling"),
        ("cut_replacement.back_lying", "arena/parts/kit3/v2/cut/poet.red_black_sunglasses.replacements/pose.lying_back.png", "back_lying"),
        ("cut_replacement.side_lying", "arena/parts/kit3/v2/cut/poet.red_black_sunglasses.replacements/pose.lying_side.png", "side_lying"),
    ]
    for rk, rf, rpost in cut_rep_map:
        ts_parts[rk] = resolve_part_entry("full_replacement", rf, ts_h_ratio, ts_torso_frac, ts_scale_table, view="profile", posture=rpost, label=rk)

    ts_sheets = verify_sheets([
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.master.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.body.front.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.body.threequarter.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.body.profile.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.body.back.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.hipcore.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.feet.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/poet.red_black_sunglasses.heads.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/poet.red_black_sunglasses.hands.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/poet.red_black_sunglasses.face.front.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/poet.red_black_sunglasses.face.profile.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.replacements.kneeling.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.replacements.deep_crouch.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.replacements.sitting.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.replacements.falling.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.replacements.back_lying.png",
        "kits/packs/poem_04/01_CHARACTER_CORE/poet.red_black_sunglasses.replacements.side_lying.png",
        "kits/packs/poem_04/02_ACTIONS_AND_POSES/poet.04.action.red_black_sunglasses.parts.01.png",
        "kits/packs/poem_05/02_ACTIONS_AND_POSES/poet.05.action.red_black_sunglasses.parts.png",
        "kits/packs/poem_07/02_ACTIONS_AND_POSES/poet.07.action.red_black_sunglasses.parts.png",
        "kits/packs/poem_08/02_ACTIONS_AND_POSES/poet.08.action.red_black_sunglasses.parts.png",
        "kits/packs/poem_14/02_ACTIONS_AND_POSES/poet.14.action.red_black_sunglasses.parts.01.png",
    ])

    rigs["poet_tracksuit_31"] = {
        "id": "poet_tracksuit_31",
        "name": "Poet — Black/Red Tracksuit (31-Part Brass-Pivot Rig)",
        "character_role": "Principal Adult Male Poet in black tracksuit with red piping, Chelsea boots, and modular plug-in sunglasses",
        "poems": ["04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14"],
        "anatomy": {
            "head_count": 7.5,
            "height_cm": 184,
            "adult_scale_ratio": 1.00,
            "torso_to_body_fraction": ts_torso_frac,
            "hip_elevation_fraction": 0.53,
        },
        "canonical_height_stage_ratio": ts_h_ratio,
        "posture_stage_ratios": make_posture_ratios(ts_h_ratio),
        "aspect_compensation": {
            "threshold_w_over_h": 0.75,
            "standing_reference_ar": 0.40,
            "formula": "aspect_mult = (w/h > 0.75) ? clamp(1.0 / sqrt(1.0 + 1.35 * pow((w/h) - 0.50, 2)), 0.36, 0.82) : 1.0",
            "replacement_posture_examples": {
                "standing_front": compute_aspect_compensation(190, 474, "standing"),
                "kneeling": compute_aspect_compensation(320, 354, "kneeling"),
                "deep_crouch": compute_aspect_compensation(232, 293, "deep_crouch"),
                "sitting": compute_aspect_compensation(287, 373, "sitting"),
                "falling": compute_aspect_compensation(435, 346, "falling"),
                "back_lying": compute_aspect_compensation(496, 206, "back_lying"),
                "side_lying": compute_aspect_compensation(416, 202, "side_lying"),
            },
        },
        "part_scale_table": ts_scale_table,
        "joint_hierarchy": build_joint_hierarchy(head_scale=0.64, back_only=False),
        "costume_variants": [
            {
                "id": "red_black_sunglasses",
                "label": "Black Tracksuit w/ Red Piping & Plug-In Sunglasses (Poems 04-14)",
                "poems": ["04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14"],
                "primary_torso": "arena/parts/kit3/release_v2/tracksuit/01_torso_front.png",
                "primary_pose": "arena/parts/kit3/v2/poses/poet.red_black_sunglasses/stand_front.png",
            },
            {
                "id": "poet_soul_08",
                "label": "Poet Soul / Double Variant (Poem 08)",
                "poems": ["08"],
                "primary_torso": "arena/parts/kit3/release_v2/cuts/poet_soul.08.core/poet_soul.08.core__p01.png",
                "primary_pose": "arena/parts/kit3/v2/poses/poet.red_black_sunglasses/reach.png",
            },
        ],
        "locomotion_cycles": build_locomotion_cycles("poet_tracksuit_31", ts_h_ratio, adult_scale=1.0),
        "available_sheets": ts_sheets,
        "resolved_parts": ts_parts,
    }

    # =========================================================================
    # 2. poet_black_tshirt
    # =========================================================================
    bt_scale_table = dict(BASE_PART_SCALE_TABLE)
    bt_h_ratio = 0.54
    bt_torso_frac = 0.32
    bt_parts = collect_kit_modular_parts(
        "poet.black_tshirt",
        bt_h_ratio,
        bt_torso_frac,
        bt_scale_table,
        views=("front", "threequarter", "profile", "back"),
    )

    # Add Weave Cast Man modular parts (`shots/weave/cast/man/cast.json`)
    weave_slot_map = {
        "torso.profile": ("torso", "profile"),
        "torso.front": ("torso", "front"),
        "torso.threequarter_R": ("torso", "threequarter"),
        "torso.back": ("torso", "back"),
        "pelvis.profile": ("pelvis", "profile"),
        "pelvis.front": ("pelvis", "front"),
        "uarm.profile": ("upper_arm", "profile"),
        "farm.profile": ("forearm", "profile"),
        "hand.profile.open": ("hand", "profile"),
        "hand.fist": ("hand", "profile"),
        "hand.grip": ("hand", "profile"),
        "hand.point": ("hand", "profile"),
        "thigh.profile": ("thigh", "profile"),
        "shin.profile": ("shin", "profile"),
        "boot.flat.profile": ("foot", "profile"),
        "boot.toe.flexed": ("foot", "profile"),
        "head.profile_R": ("head", "profile"),
        "head.front": ("head", "front"),
        "head.threequarter_R": ("head", "threequarter"),
        "head.back": ("head", "back"),
    }
    for wid, (wslot, wview) in weave_slot_map.items():
        wpart = weave_man_cast.get("parts", {}).get(wid, {})
        wfile = "weave/" + wpart.get("file", f"cast/man/parts/{wid}.png")
        pivots = []
        if "pivot" in wpart:
            pivots.append({"id": "root", "x": wpart["pivot"][0], "y": wpart["pivot"][1], "r": 10.0})
        for sk_name, sk_xy in wpart.get("sockets", {}).items():
            pivots.append({"id": sk_name, "x": sk_xy[0], "y": sk_xy[1], "r": 9.0})
        bt_parts[f"weave_man.{wid}"] = resolve_part_entry(
            wslot, wfile, bt_h_ratio, bt_torso_frac, bt_scale_table, pivots=pivots, view=wview, label=f"Weave Man {wid}"
        )

    # Add crouch & floor recovery multi-part cutouts from weave/assets and arena/bodies
    bt_parts["weave.man_crouch_clean"] = resolve_part_entry(
        "full_replacement", "arena/bodies/man_crouch_f72_clean.png", bt_h_ratio, bt_torso_frac, bt_scale_table, view="profile", posture="deep_crouch", label="Man Crouch f72 Clean"
    )
    bt_parts["weave.poet_floor_recovery_clean"] = resolve_part_entry(
        "full_replacement", "arena/bodies/poet_floor_recovery_clean.png", bt_h_ratio, bt_torso_frac, bt_scale_table, view="profile", posture="floor_recovery", label="Poet Floor Recovery Clean"
    )
    bt_parts["arena.walk_study_p0"] = resolve_part_entry(
        "full_replacement", "arena/bodies/ACT-001_p0.png", bt_h_ratio, bt_torso_frac, bt_scale_table, view="profile", posture="walk", label="ACT-001 Walk Study Panel 0"
    )
    bt_parts["arena.walk_study_p1"] = resolve_part_entry(
        "full_replacement", "arena/bodies/ACT-001_p1.png", bt_h_ratio, bt_torso_frac, bt_scale_table, view="profile", posture="walk", label="ACT-001 Walk Study Panel 1"
    )
    bt_parts["arena.sprint_brake_f65"] = resolve_part_entry(
        "full_replacement", "arena/bodies/sprint_brake_f65_p0_f65.png", bt_h_ratio, bt_torso_frac, bt_scale_table, view="profile", posture="run", label="Sprint Brake f65"
    )
    bt_parts["arena.floor_recovery_pushup_f110"] = resolve_part_entry(
        "full_replacement", "arena/bodies/floor_recovery_pushup_f110_p0_f110.png", bt_h_ratio, bt_torso_frac, bt_scale_table, view="profile", posture="floor_recovery", label="Floor Recovery Pushup f110"
    )

    # Also include compact-core and action cut pieces from Poems 01-03
    for aid in ("poet.black_tshirt.compact-core", "poet.01.action.black_tshirt.parts.01", "poet.02.action.black_tshirt.parts", "poet.03.action.black_tshirt.parts"):
        a_obj = atlas_assets_by_id.get(aid)
        if a_obj:
            for p_item in a_obj.get("parts", [])[:4]:
                pid = p_item["id"]
                bt_parts[f"cut.{pid}"] = resolve_part_entry(
                    "torso" if p_item["part_index"] <= 2 else "upper_arm",
                    p_item["file"],
                    bt_h_ratio,
                    bt_torso_frac,
                    bt_scale_table,
                    pivots=p_item.get("pivots", []),
                    view="front",
                    label=p_item.get("label", pid),
                )

    bt_sheets = verify_sheets([
        "kits/packs/poem_01/01_CHARACTER_CORE/poet.black_tshirt.compact-core.png",
        "kits/packs/poem_01/02_ACTIONS_AND_POSES/poet.01.action.black_tshirt.parts.01.png",
        "kits/packs/poem_01/02_ACTIONS_AND_POSES/poet.01.action.black_tshirt.parts.02.png",
        "kits/packs/poem_01/02_ACTIONS_AND_POSES/poet.01.main-poses.png",
        "kits/packs/poem_02/02_ACTIONS_AND_POSES/poet.02.action.black_tshirt.parts.png",
        "kits/packs/poem_02/02_ACTIONS_AND_POSES/poet.02.main-poses.png",
        "kits/packs/poem_03/02_ACTIONS_AND_POSES/poet.03.action.black_tshirt.parts.png",
        "kits/packs/poem_03/02_ACTIONS_AND_POSES/poet.03.main-poses.png",
        "weave/cast/man/sheets/PIECE_TORSO_5VIEW.jpg",
        "weave/cast/man/sheets/PIECE_LIMBS_MODULAR.jpg",
        "weave/cast/man/sheets/arms_hands_contact.jpg",
    ])

    rigs["poet_black_tshirt"] = {
        "id": "poet_black_tshirt",
        "name": "Poet — Black T-Shirt & Weave Action Rig (Poems 01–03)",
        "character_role": "Adult Male Poet in plain black crew-neck t-shirt, dark trousers, and dark sneakers (no sunglasses) for Poems 01–03, integrated with Weave Man walk/crouch/floor-recovery library",
        "poems": ["01", "02", "03"],
        "anatomy": {
            "head_count": 7.5,
            "height_cm": 184,
            "adult_scale_ratio": 1.00,
            "torso_to_body_fraction": bt_torso_frac,
            "hip_elevation_fraction": 0.53,
        },
        "canonical_height_stage_ratio": bt_h_ratio,
        "posture_stage_ratios": make_posture_ratios(bt_h_ratio),
        "aspect_compensation": {
            "threshold_w_over_h": 0.75,
            "standing_reference_ar": 0.40,
            "formula": "aspect_mult = (w/h > 0.75) ? clamp(1.0 / sqrt(1.0 + 1.35 * pow((w/h) - 0.50, 2)), 0.36, 0.82) : 1.0",
            "replacement_posture_examples": {
                "walk_study_ACT001": compute_aspect_compensation(251, 632, "walk"),
                "man_crouch_f72": compute_aspect_compensation(495, 705, "deep_crouch"),
                "floor_recovery_clean": compute_aspect_compensation(945, 878, "floor_recovery"),
                "crouch_study_ACT003": compute_aspect_compensation(1376, 620, "deep_crouch"),
            },
        },
        "part_scale_table": bt_scale_table,
        "joint_hierarchy": build_joint_hierarchy(head_scale=0.64, back_only=False),
        "costume_variants": [
            {
                "id": "black_tshirt",
                "label": "Black Crew-Neck T-Shirt & Dark Sneakers (Poems 01-03)",
                "poems": ["01", "02", "03"],
                "primary_torso": "arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/poet.black_tshirt/stand_front.png",
            },
            {
                "id": "weave_man_profile",
                "label": "Weave Cast Man Modular Profile Rig",
                "poems": ["01", "02", "03"],
                "primary_torso": "weave/cast/man/parts/torso.profile.png",
                "primary_pose": "arena/bodies/ACT-001_p0.png",
            },
        ],
        "locomotion_cycles": build_locomotion_cycles("poet_black_tshirt", bt_h_ratio, adult_scale=1.0),
        "available_sheets": bt_sheets,
        "resolved_parts": bt_parts,
    }

    # =========================================================================
    # 3. ex_jacket_back
    # =========================================================================
    ex_scale_table = dict(BASE_PART_SCALE_TABLE)
    ex_h_ratio = 0.555  # 188cm taller broad-shouldered build
    ex_torso_frac = 0.33
    ex_parts = collect_kit_modular_parts(
        "ex.ex_jacket",
        ex_h_ratio,
        ex_torso_frac,
        ex_scale_table,
        views=("back", "threequarter_back"),
    )

    # Add EX cut parts from wygwyl_atlas_manifest
    for aid in (
        "ex.ex_jacket.body.back",
        "ex.ex_jacket.body.threequarter_back",
        "ex.ex_jacket.hipcore",
        "ex.ex_jacket.heads",
        "ex.ex_jacket.hands",
        "ex.ex_jacket.feet",
        "ex.01.action.ex_jacket.parts",
        "ex.02.action.ex_jacket.parts",
        "ex.03.action.ex_jacket.parts",
        "ex.07.action.ex_jacket.parts",
        "ex.08.action.ex_jacket.parts",
        "ex.09.crouch-parts",
    ):
        a_obj = atlas_assets_by_id.get(aid)
        if a_obj:
            for p_item in a_obj.get("parts", [])[:3]:
                pid = p_item["id"]
                slot_guess = "torso" if "body" in aid and p_item["part_index"] == 1 else ("head" if "heads" in aid else ("hand" if "hands" in aid else ("foot" if "feet" in aid else "pelvis")))
                ex_parts[f"cut.{pid}"] = resolve_part_entry(
                    slot_guess,
                    p_item["file"],
                    ex_h_ratio,
                    ex_torso_frac,
                    ex_scale_table,
                    pivots=p_item.get("pivots", []),
                    view="threequarter_back" if "threequarter" in aid else "back",
                    posture="deep_crouch" if "crouch" in aid else "standing",
                    label=p_item.get("label", pid),
                )

    ex_sheets = verify_sheets([
        "kits/packs/poem_01/01_CHARACTER_CORE/ex.ex_jacket.master.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/ex.ex_jacket.body.back.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/ex.ex_jacket.body.threequarter_back.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/ex.ex_jacket.hipcore.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/ex.ex_jacket.heads.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/ex.ex_jacket.hands.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/ex.ex_jacket.feet.png",
        "kits/packs/poem_01/02_ACTIONS_AND_POSES/ex.01.action.ex_jacket.parts.png",
        "kits/packs/poem_02/02_ACTIONS_AND_POSES/ex.02.action.ex_jacket.parts.png",
        "kits/packs/poem_03/02_ACTIONS_AND_POSES/ex.03.action.ex_jacket.parts.png",
        "kits/packs/poem_07/02_ACTIONS_AND_POSES/ex.07.action.ex_jacket.parts.png",
        "kits/packs/poem_08/02_ACTIONS_AND_POSES/ex.08.action.ex_jacket.parts.png",
        "kits/packs/poem_09/01_CHARACTER_CORE/ex.09.crouch-parts.png",
        "kits/packs/poem_09/01_CHARACTER_CORE/ex.09.dissolve-state02.png",
        "kits/packs/poem_09/01_CHARACTER_CORE/ex.09.dissolve-state03.png",
    ])

    rigs["ex_jacket_back"] = {
        "id": "ex_jacket_back",
        "name": "The EX — Olive Bomber Jacket (Strict Back / 3Q-Back Rig)",
        "character_role": "The Ex in olive bomber jacket, dark jeans, and white sneakers. Strictly back and three-quarter-back views only (face is never seen). Includes Poem 01 vape turn and Poem 09 crouch/dissolve.",
        "poems": ["01", "02", "03", "07", "08", "09", "12"],
        "strict_view_rule": "BACK_AND_3Q_BACK_ONLY_NEVER_FRONT_FACE",
        "allowed_views": ["back", "threequarter_back"],
        "anatomy": {
            "head_count": 7.6,
            "height_cm": 188,
            "adult_scale_ratio": 1.022,
            "torso_to_body_fraction": ex_torso_frac,
            "hip_elevation_fraction": 0.535,
        },
        "canonical_height_stage_ratio": ex_h_ratio,
        "posture_stage_ratios": make_posture_ratios(ex_h_ratio),
        "aspect_compensation": {
            "threshold_w_over_h": 0.75,
            "standing_reference_ar": 0.40,
            "formula": "aspect_mult = (w/h > 0.75) ? clamp(1.0 / sqrt(1.0 + 1.35 * pow((w/h) - 0.50, 2)), 0.36, 0.82) : 1.0",
            "replacement_posture_examples": {
                "standing_back": compute_aspect_compensation(190, 474, "standing"),
                "ex_09_crouch": compute_aspect_compensation(245, 310, "deep_crouch"),
            },
        },
        "part_scale_table": ex_scale_table,
        "joint_hierarchy": build_joint_hierarchy(head_scale=0.63, back_only=True),
        "costume_variants": [
            {
                "id": "ex_jacket",
                "label": "Olive Bomber Jacket — Back & 3Q-Back Only (Poems 01-03, 07-09, 12)",
                "poems": ["01", "02", "03", "07", "08", "09", "12"],
                "primary_torso": "arena/parts/kit3/v2/parts/ex.ex_jacket/body.back.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/ex.ex_jacket/stand_back.png",
            },
        ],
        "locomotion_cycles": build_locomotion_cycles("ex_jacket_back", ex_h_ratio, adult_scale=1.022, back_only=True),
        "available_sheets": ex_sheets,
        "resolved_parts": ex_parts,
    }

    # =========================================================================
    # 4. vintage_party_couple
    # =========================================================================
    vp_scale_table = dict(BASE_PART_SCALE_TABLE)
    vp_h_ratio = 0.535
    vp_torso_frac = 0.32
    vp_parts = collect_kit_modular_parts(
        "party.vintage_party",
        vp_h_ratio,
        vp_torso_frac,
        vp_scale_table,
        views=("front", "threequarter", "profile", "back"),
    )

    for aid in (
        "party.vintage_party.paired-choreography",
        "party.01.vintage-waltz-instances",
        "party.vintage_party.main-poses",
        "party.vintage_party.body.front",
        "party.vintage_party.body.profile",
        "party.vintage_party.body.back",
        "party.14.action.vintage_party.suit_man.parts",
        "party.14.action.vintage_party.gown_woman.parts.01",
        "party.14.action.vintage_party.gown_woman.parts.02",
    ):
        a_obj = atlas_assets_by_id.get(aid)
        if a_obj:
            for p_item in a_obj.get("parts", [])[:3]:
                pid = p_item["id"]
                vp_parts[f"cut.{pid}"] = resolve_part_entry(
                    "full_replacement" if ("paired" in aid or "waltz" in aid or "main-poses" in aid) else "torso",
                    p_item["file"],
                    vp_h_ratio,
                    vp_torso_frac,
                    vp_scale_table,
                    pivots=p_item.get("pivots", []),
                    view="threequarter",
                    posture="waltz",
                    label=p_item.get("label", pid),
                )

    vp_sheets = verify_sheets([
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.master.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.paired-choreography.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.01.vintage-waltz-instances.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.body.front.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.body.profile.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.body.back.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.hipcore.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.heads.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.hands.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.hands-completion.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.face-feet.male.png",
        "kits/packs/poem_01/01_CHARACTER_CORE/party.vintage_party.face-feet.female.png",
        "kits/packs/poem_01/02_ACTIONS_AND_POSES/party.vintage_party.main-poses.png",
        "kits/packs/poem_14/02_ACTIONS_AND_POSES/party.14.action.vintage_party.suit_man.parts.png",
        "kits/packs/poem_14/02_ACTIONS_AND_POSES/party.14.action.vintage_party.gown_woman.parts.01.png",
        "kits/packs/poem_14/02_ACTIONS_AND_POSES/party.14.action.vintage_party.gown_woman.parts.02.png",
    ])

    rigs["vintage_party_couple"] = {
        "id": "vintage_party_couple",
        "name": "Vintage Party Couple — Suit Man & Satin Gown Woman (Paired Waltz Rig)",
        "character_role": "1940s Vintage Evening Suit Man & Satin Gown Woman performing slow-motion paired waltz choreography across Poems 01 and 14",
        "poems": ["01", "14"],
        "anatomy": {
            "head_count": 7.5,
            "height_cm": 181,
            "adult_scale_ratio": 0.99,
            "torso_to_body_fraction": vp_torso_frac,
            "hip_elevation_fraction": 0.53,
            "partner_offset_stage_x": 0.048,
        },
        "canonical_height_stage_ratio": vp_h_ratio,
        "posture_stage_ratios": make_posture_ratios(vp_h_ratio),
        "aspect_compensation": {
            "threshold_w_over_h": 0.75,
            "standing_reference_ar": 0.48,
            "formula": "aspect_mult = (w/h > 0.75) ? clamp(1.0 / sqrt(1.0 + 1.35 * pow((w/h) - 0.50, 2)), 0.36, 0.82) : 1.0",
            "paired_couple_note": "Paired waltz silhouette is wider (ar ~ 0.65..0.85) because two partners share the frame; height stays locked to 0.535 * stage_H without vertical compression.",
        },
        "part_scale_table": vp_scale_table,
        "joint_hierarchy": build_joint_hierarchy(head_scale=0.64, back_only=False),
        "costume_variants": [
            {
                "id": "vintage_suit_man",
                "label": "1940s Evening Suit & Tie Man (Poems 01, 14)",
                "poems": ["01", "14"],
                "primary_torso": "arena/parts/kit3/v2/parts/party.vintage_party/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/party.vintage_party/stand_front.png",
            },
            {
                "id": "vintage_gown_woman",
                "label": "Satin Evening Gown & Gloves Woman (Poems 01, 14)",
                "poems": ["01", "14"],
                "primary_torso": "arena/parts/kit3/release_v2/cuts/party.14.action.vintage_party.gown_woman.parts.01/party.14.action.vintage_party.gown_woman.parts.01__p01.png",
                "primary_pose": "arena/parts/kit3/v2/poses/party.vintage_party/walk.png",
            },
        ],
        "locomotion_cycles": build_locomotion_cycles("vintage_party_couple", vp_h_ratio, adult_scale=0.99, paired_couple=True),
        "available_sheets": vp_sheets,
        "resolved_parts": vp_parts,
    }

    # =========================================================================
    # 5. woman_muse_costumes
    # =========================================================================
    wm_scale_table = dict(BASE_PART_SCALE_TABLE)
    wm_scale_table["pelvis"] = 0.82  # Dress / skirt pelvis card
    wm_h_ratio = 0.52  # 174cm adult female proportion (7.3H)
    wm_torso_frac = 0.31
    wm_parts = collect_kit_modular_parts(
        "woman.teal_dress",
        wm_h_ratio,
        wm_torso_frac,
        wm_scale_table,
        views=("front", "threequarter", "profile", "back"),
    )

    # Also collect parts from woman.window_woman_dress and woman.mother_cardigan
    for extra_kit in ("woman.window_woman_dress", "woman.mother_cardigan"):
        sub_parts = collect_kit_modular_parts(extra_kit, wm_h_ratio, wm_torso_frac, wm_scale_table, views=("front", "profile", "back"))
        for k, v in sub_parts.items():
            wm_parts[f"{extra_kit}.{k}"] = v

    # Include original Weave Woman / Muse parts (`shots/weave/assets/parts/` + crouch/floor_recovery)
    for w_fn, w_slot in (
        ("torso.png", "torso"),
        ("skirt.png", "pelvis"),
        ("head.png", "head"),
        ("upper_arm_near.png", "upper_arm"),
        ("forearm_near.png", "forearm"),
        ("hand_near.png", "hand"),
        ("leg_near.png", "shin"),
        ("proc.boot.near.png", "foot"),
    ):
        wm_parts[f"weave_muse.{w_fn[:-4]}"] = resolve_part_entry(
            w_slot, f"weave/assets/parts/{w_fn}", wm_h_ratio, wm_torso_frac, wm_scale_table, view="profile", label=f"Weave Muse {w_fn[:-4]}"
        )

    for ck, cpart in crouch_manifest.get("parts", {}).items():
        wm_parts[f"weave_crouch.{ck}"] = resolve_part_entry(
            "torso" if "torso" in ck else ("head" if ck == "head" else ("upper_arm" if ck == "arm" else "thigh")),
            cpart["path"],
            wm_h_ratio,
            wm_torso_frac,
            wm_scale_table,
            view="profile",
            posture="deep_crouch",
            label=f"Muse Crouch {ck}",
        )
    for rk, rpart in recovery_manifest.get("parts", {}).items():
        wm_parts[f"weave_recovery.{rk}"] = resolve_part_entry(
            "torso" if "torso" in rk else ("head" if rk == "head" else ("upper_arm" if rk == "arm" else "thigh")),
            rpart["path"],
            wm_h_ratio,
            wm_torso_frac,
            wm_scale_table,
            view="profile",
            posture="floor_recovery",
            label=f"Muse Floor Recovery {rk}",
        )
    wm_parts["weave_crouch.clean_figure"] = resolve_part_entry(
        "full_replacement", "arena/bodies/poet_crouch_f72_clean.png", wm_h_ratio, wm_torso_frac, wm_scale_table, view="profile", posture="deep_crouch", label="Muse Crouch Clean Figure"
    )

    wm_sheets = verify_sheets([
        "arena/parts/kit3/v2/sheets/woman.teal_dress.body.front.jpg",
        "arena/parts/kit3/v2/sheets/woman.teal_dress.body.profile.jpg",
        "arena/parts/kit3/v2/sheets/woman.teal_dress.replacements.jpg",
        "kits/packs/poem_02/01_CHARACTER_CORE/woman.09.mother.body.png",
        "kits/packs/poem_02/01_CHARACTER_CORE/woman.09.mother.heads-hands.png",
        "kits/packs/poem_13/01_CHARACTER_CORE/woman.13.body.png",
        "kits/packs/poem_13/01_CHARACTER_CORE/woman.13.heads-hands.png",
        "kits/packs/poem_13/02_ACTIONS_AND_POSES/woman.13.window-action.png",
        "kits/packs/poem_14/01_CHARACTER_CORE/poet.14.muse-dance.png",
        "kits/packs/poem_14/02_ACTIONS_AND_POSES/party.14.action.vintage_party.gown_woman.parts.01.png",
        "kits/packs/poem_07/01_CHARACTER_CORE/08.cast.club_dress.body.png",
    ])

    rigs["woman_muse_costumes"] = {
        "id": "woman_muse_costumes",
        "name": "The Woman / Muse — All 7 Poem Costume Rigs",
        "character_role": "The Woman / Muse across all 7 canonical poem costumes: teal_dress, indigo_dress, yellow_coat, apron_dress, work_shirt, stage_black, and gold_gown",
        "poems": ["01", "02", "05", "06", "07", "08", "09", "12", "13", "14"],
        "anatomy": {
            "head_count": 7.3,
            "height_cm": 174,
            "adult_scale_ratio": 0.963,
            "torso_to_body_fraction": wm_torso_frac,
            "hip_elevation_fraction": 0.525,
        },
        "canonical_height_stage_ratio": wm_h_ratio,
        "posture_stage_ratios": make_posture_ratios(wm_h_ratio),
        "aspect_compensation": {
            "threshold_w_over_h": 0.75,
            "standing_reference_ar": 0.42,
            "formula": "aspect_mult = (w/h > 0.75) ? clamp(1.0 / sqrt(1.0 + 1.35 * pow((w/h) - 0.50, 2)), 0.36, 0.82) : 1.0",
            "replacement_posture_examples": {
                "standing_teal_dress": compute_aspect_compensation(190, 474, "standing"),
                "crouch_f72_clean": compute_aspect_compensation(575, 738, "deep_crouch"),
                "floor_recovery_clean": compute_aspect_compensation(945, 878, "floor_recovery"),
                "lying_back_card": compute_aspect_compensation(563, 268, "back_lying"),
            },
        },
        "part_scale_table": wm_scale_table,
        "joint_hierarchy": build_joint_hierarchy(head_scale=0.65, back_only=False),
        "costume_variants": [
            {
                "id": "teal_dress",
                "label": "1. Teal Dress w/ Gold Floral Print (Arena / Muse Signature)",
                "poems": ["01", "04", "13"],
                "kit_dir": "woman.teal_dress",
                "primary_torso": "arena/parts/kit3/v2/parts/woman.teal_dress/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/woman.teal_dress/stand_front.png",
            },
            {
                "id": "indigo_dress",
                "label": "2. Indigo Dress w/ Gold Trim (Poems 05, 06)",
                "poems": ["05", "06"],
                "kit_dir": "ancestors.ancestor_robe_indigo_gold",
                "primary_torso": "arena/parts/kit3/v2/parts/ancestors.ancestor_robe_indigo_gold/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/ancestors.ancestor_robe_indigo_gold/stand_front.png",
            },
            {
                "id": "yellow_coat",
                "label": "3. Warm Yellow / Ochre Window & Travel Dress-Coat (Poems 06, 13)",
                "poems": ["06", "13"],
                "kit_dir": "woman.window_woman_dress",
                "primary_torso": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/woman.window_woman_dress/stand_front.png",
            },
            {
                "id": "apron_dress",
                "label": "4. House Apron Dress & Cardigan (Poems 02, 09)",
                "poems": ["02", "09"],
                "kit_dir": "woman.mother_cardigan",
                "primary_torso": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/woman.mother_cardigan/stand_front.png",
            },
            {
                "id": "work_shirt",
                "label": "5. Everyday Work Shirt & Linen Trousers (Poems 10, 13)",
                "poems": ["10", "13"],
                "kit_dir": "family.couple_summer_casual",
                "primary_torso": "arena/parts/kit3/v2/parts/family.couple_summer_casual/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/family.couple_summer_casual/stand_front.png",
            },
            {
                "id": "stage_black",
                "label": "6. Stage Black Performance Attire (Poems 08, 14)",
                "poems": ["08", "14"],
                "kit_dir": "party.club_jacket",
                "primary_torso": "arena/parts/kit3/v2/parts/party.club_jacket/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/party.club_jacket/stand_front.png",
            },
            {
                "id": "gold_gown",
                "label": "7. Gold Evening Satin Gown (Poems 01, 07, 14)",
                "poems": ["01", "07", "14"],
                "kit_dir": "party.club_dress",
                "primary_torso": "arena/parts/kit3/v2/parts/party.club_dress/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/party.club_dress/stand_front.png",
            },
        ],
        "locomotion_cycles": build_locomotion_cycles("woman_muse_costumes", wm_h_ratio, adult_scale=0.963),
        "available_sheets": wm_sheets,
        "resolved_parts": wm_parts,
    }

    # =========================================================================
    # 6. child_traveler_ghost (SOLVED AT 5.2-HEAD CHILD SCALE = 0.68x ADULT!)
    # =========================================================================
    ch_scale_table = dict(BASE_PART_SCALE_TABLE)
    # Larger head-to-torso ratio for 5.2-head child (0.78 vs 0.64 adult) and slightly shorter limb ratios
    ch_scale_table["head"] = 0.78
    ch_scale_table["thigh"] = 0.56
    ch_scale_table["shin"] = 0.52
    ch_scale_table["upper_arm"] = 0.45
    ch_scale_table["forearm"] = 0.41
    ch_h_ratio = 0.37  # 0.68x of 0.54 adult standing height!
    ch_torso_frac = 0.34

    ch_parts = collect_kit_modular_parts(
        "young_poet.child_clothes",
        ch_h_ratio,
        ch_torso_frac,
        ch_scale_table,
        views=("front", "threequarter", "profile", "back"),
    )
    for extra_child_kit in ("ghost_child.ghost_nightclothes", "young_poet.pajamas_winter"):
        sub_parts = collect_kit_modular_parts(
            extra_child_kit,
            ch_h_ratio,
            ch_torso_frac,
            ch_scale_table,
            views=("front", "threequarter", "profile", "back"),
        )
        for k, v in sub_parts.items():
            ch_parts[f"{extra_child_kit}.{k}"] = v

    for aid in (
        "atlantis.06.child_traveler.body",
        "atlantis.06.child_traveler.heads-hands",
        "ghost_child.ghost_nightclothes.compact-core",
        "ghost_child.02.action.ghost_nightclothes.parts",
        "young_poet.pajamas_winter.compact-core",
        "young_poet.02.action.pajamas_winter.parts",
        "young_poet.13.action.lean-parts",
    ):
        a_obj = atlas_assets_by_id.get(aid)
        if a_obj:
            for p_item in a_obj.get("parts", [])[:3]:
                pid = p_item["id"]
                ch_parts[f"cut.{pid}"] = resolve_part_entry(
                    "torso" if p_item["part_index"] == 1 else "head",
                    p_item["file"],
                    ch_h_ratio,
                    ch_torso_frac,
                    ch_scale_table,
                    pivots=p_item.get("pivots", []),
                    view="front",
                    label=p_item.get("label", pid),
                )

    ch_sheets = verify_sheets([
        "kits/packs/poem_06/01_CHARACTER_CORE/atlantis.06.child_traveler.body.png",
        "kits/packs/poem_06/01_CHARACTER_CORE/atlantis.06.child_traveler.heads-hands.png",
        "kits/packs/poem_02/01_CHARACTER_CORE/ghost_child.ghost_nightclothes.compact-core.png",
        "kits/packs/poem_02/01_CHARACTER_CORE/ghost_child.02.faces-hands.png",
        "kits/packs/poem_02/02_ACTIONS_AND_POSES/ghost_child.02.action.ghost_nightclothes.parts.png",
        "kits/packs/poem_02/02_ACTIONS_AND_POSES/young_ghost.02.main-poses.png",
        "kits/packs/poem_02/01_CHARACTER_CORE/young_poet.pajamas_winter.compact-core.png",
        "kits/packs/poem_02/02_ACTIONS_AND_POSES/young_poet.02.action.pajamas_winter.parts.png",
        "kits/packs/poem_13/01_CHARACTER_CORE/young_poet.child_clothes.body.front.png",
        "kits/packs/poem_13/01_CHARACTER_CORE/young_poet.child_clothes.body.threequarter.png",
        "kits/packs/poem_13/01_CHARACTER_CORE/young_poet.child_clothes.body.profile.png",
        "kits/packs/poem_13/01_CHARACTER_CORE/young_poet.child_clothes.body.back.png",
        "kits/packs/poem_13/01_CHARACTER_CORE/young_poet.child_clothes.hipcore.png",
        "kits/packs/poem_13/01_CHARACTER_CORE/young_poet.child_clothes.feet.png",
        "kits/packs/poem_02/01_CHARACTER_CORE/young_poet.child_clothes.heads.png",
        "kits/packs/poem_02/01_CHARACTER_CORE/young_poet.child_clothes.hands.png",
    ])

    rigs["child_traveler_ghost"] = {
        "id": "child_traveler_ghost",
        "name": "Child Traveler / Young Poet / Ghost Child (Age 7, 5.2-Head 0.68x Scale)",
        "character_role": "Age 6–7 Child Traveler (Poem 06), Ghost Child (Poem 02, 05, 09), and Young Poet (Poem 02, 13). Solved at 5.2-head child anatomy = 0.68x adult height (0.37 stage ratio) so child cutouts never scale up to giant adult height.",
        "poems": ["02", "05", "06", "09", "13"],
        "anatomy": {
            "head_count": 5.2,
            "height_cm": 122,
            "adult_scale_ratio": 0.68,
            "torso_to_body_fraction": ch_torso_frac,
            "hip_elevation_fraction": 0.47,
            "child_proportion_lock": "LOCKED_0.68X_ADULT_HEIGHT_5.2_HEADS",
        },
        "canonical_height_stage_ratio": ch_h_ratio,
        "posture_stage_ratios": make_posture_ratios(ch_h_ratio),
        "aspect_compensation": {
            "threshold_w_over_h": 0.75,
            "standing_reference_ar": 0.40,
            "formula": "child_scale = 0.68 * adult_scale; aspect_mult = (w/h > 0.75) ? clamp(1.0 / sqrt(1.0 + 1.35 * pow((w/h) - 0.50, 2)), 0.36, 0.82) : 1.0",
            "child_bug_solved": "In v2/poses/young_poet.child_clothes, crouch.png (491px) and head.front.png (447px) had adult pixel dimensions. This solver locks standing child height to 0.37 * stage_H, crouched child to 0.25 * stage_H, and prone child to 0.15 * stage_H.",
            "replacement_posture_examples": {
                "standing_child": compute_aspect_compensation(155, 387, "standing"),
                "crouched_child": compute_aspect_compensation(214, 491, "deep_crouch"),
                "falling_child": compute_aspect_compensation(330, 476, "falling"),
            },
        },
        "part_scale_table": ch_scale_table,
        "joint_hierarchy": build_joint_hierarchy(head_scale=0.78, back_only=False),
        "costume_variants": [
            {
                "id": "child_traveler_06",
                "label": "Atlantis Child Traveler (Poem 05, 06)",
                "poems": ["05", "06"],
                "kit_dir": "young_poet.child_clothes",
                "primary_torso": "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/young_poet.child_clothes/stand_front.png",
            },
            {
                "id": "ghost_nightclothes",
                "label": "Ghost Child in Pale Translucent Nightshirt (Poems 02, 05, 09)",
                "poems": ["02", "05", "09"],
                "kit_dir": "ghost_child.ghost_nightclothes",
                "primary_torso": "arena/parts/kit3/v2/parts/ghost_child.ghost_nightclothes/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/ghost_child.ghost_nightclothes/stand_front.png",
            },
            {
                "id": "pajamas_winter",
                "label": "Young Poet in Blue Flannel Winter Pajamas (Poem 02)",
                "poems": ["02"],
                "kit_dir": "young_poet.pajamas_winter",
                "primary_torso": "arena/parts/kit3/v2/parts/young_poet.pajamas_winter/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/young_poet.pajamas_winter/stand_front.png",
            },
        ],
        "locomotion_cycles": build_locomotion_cycles("child_traveler_ghost", ch_h_ratio, adult_scale=0.68),
        "available_sheets": ch_sheets,
        "resolved_parts": ch_parts,
    }

    # =========================================================================
    # 7. mother_ancestors_family
    # =========================================================================
    mf_scale_table = dict(BASE_PART_SCALE_TABLE)
    mf_scale_table["pelvis"] = 0.78  # Robes / coats / skirts
    mf_h_ratio = 0.53
    mf_torso_frac = 0.32
    mf_parts = collect_kit_modular_parts(
        "ancestors.ancestor_robe_indigo_gold",
        mf_h_ratio,
        mf_torso_frac,
        mf_scale_table,
        views=("front", "threequarter", "profile", "back"),
    )

    for fam_kit in (
        "woman.mother_cardigan",
        "ancestors.ancestor_elder_white_silver",
        "family.street_clothes",
        "parents.elder_father_coat",
        "family.brother_casual",
        "family.elder_robe_pearls",
    ):
        sub_parts = collect_kit_modular_parts(fam_kit, mf_h_ratio, mf_torso_frac, mf_scale_table, views=("front", "profile", "back"))
        for k, v in sub_parts.items():
            mf_parts[f"{fam_kit}.{k}"] = v

    for aid in (
        "woman.09.mother.body",
        "ancestors.05.ancestor_robe_indigo_gold.body",
        "ancestors.05.ancestor_elder_white_silver.body",
        "ancestors.05.procession-gifts-gate",
        "family.street_clothes.body.front",
        "family.14.action",
        "parents.09.father_elder.body",
    ):
        a_obj = atlas_assets_by_id.get(aid)
        if a_obj:
            for p_item in a_obj.get("parts", [])[:2]:
                pid = p_item["id"]
                mf_parts[f"cut.{pid}"] = resolve_part_entry(
                    "torso",
                    p_item["file"],
                    mf_h_ratio,
                    mf_torso_frac,
                    mf_scale_table,
                    pivots=p_item.get("pivots", []),
                    view="front",
                    label=p_item.get("label", pid),
                )

    mf_sheets = verify_sheets([
        "kits/packs/poem_02/01_CHARACTER_CORE/woman.09.mother.body.png",
        "kits/packs/poem_02/01_CHARACTER_CORE/woman.09.mother.heads-hands.png",
        "kits/packs/poem_05/01_CHARACTER_CORE/ancestors.05.ancestor_robe_indigo_gold.body.png",
        "kits/packs/poem_05/01_CHARACTER_CORE/ancestors.05.ancestor_elder_white_silver.body.png",
        "kits/packs/poem_05/01_CHARACTER_CORE/ancestors.05.identities.01.png",
        "kits/packs/poem_05/01_CHARACTER_CORE/ancestors.05.procession-gifts-gate.png",
        "kits/packs/poem_05/02_ACTIONS_AND_POSES/ancestors.05.action-hands.png",
        "kits/packs/poem_09/01_CHARACTER_CORE/parents.09.father_elder.body.png",
        "kits/packs/poem_09/01_CHARACTER_CORE/parents.09.phone-prayer-walk.png",
        "kits/packs/poem_10/01_CHARACTER_CORE/family.street_clothes.body.front.png",
        "kits/packs/poem_10/01_CHARACTER_CORE/family.street_clothes.body.profile.png",
        "kits/packs/poem_10/01_CHARACTER_CORE/family.street_clothes.body.back.png",
        "kits/packs/poem_11/02_ACTIONS_AND_POSES/family.11.optional.action.png",
        "kits/packs/poem_14/02_ACTIONS_AND_POSES/family.14.action.png",
    ])

    rigs["mother_ancestors_family"] = {
        "id": "mother_ancestors_family",
        "name": "Mother, Ancestors & Street-Clothes Family Rigs",
        "character_role": "The Poet's Mother (Poems 02, 09), Afro-Futurist Ancestors in Indigo/Gold & White/Silver Robes (Poem 05), Elder Father (Poem 09), and Street-Clothes Family/Elders (Poems 10, 11, 12, 13, 14)",
        "poems": ["02", "05", "09", "10", "11", "12", "13", "14"],
        "anatomy": {
            "head_count": 7.4,
            "height_cm": 179,
            "adult_scale_ratio": 0.98,
            "torso_to_body_fraction": mf_torso_frac,
            "hip_elevation_fraction": 0.53,
        },
        "canonical_height_stage_ratio": mf_h_ratio,
        "posture_stage_ratios": make_posture_ratios(mf_h_ratio),
        "aspect_compensation": {
            "threshold_w_over_h": 0.75,
            "standing_reference_ar": 0.43,
            "formula": "aspect_mult = (w/h > 0.75) ? clamp(1.0 / sqrt(1.0 + 1.35 * pow((w/h) - 0.50, 2)), 0.36, 0.82) : 1.0",
            "robed_pelvis_note": "Floor-length ancestor and church robes use pelvis scale 0.78 while keeping total standing height locked to 0.53 * stage_H.",
        },
        "part_scale_table": mf_scale_table,
        "joint_hierarchy": build_joint_hierarchy(head_scale=0.64, back_only=False),
        "costume_variants": [
            {
                "id": "ancestor_robe_indigo_gold",
                "label": "Ancestor in Indigo & Gold Kente Robe (Poem 05)",
                "poems": ["05"],
                "kit_dir": "ancestors.ancestor_robe_indigo_gold",
                "primary_torso": "arena/parts/kit3/v2/parts/ancestors.ancestor_robe_indigo_gold/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/ancestors.ancestor_robe_indigo_gold/stand_front.png",
            },
            {
                "id": "ancestor_elder_white_silver",
                "label": "Ancestor Elder in White & Silver Robe (Poem 05)",
                "poems": ["05"],
                "kit_dir": "ancestors.ancestor_elder_white_silver",
                "primary_torso": "arena/parts/kit3/v2/parts/ancestors.ancestor_elder_white_silver/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/ancestors.ancestor_elder_white_silver/stand_front.png",
            },
            {
                "id": "mother_cardigan",
                "label": "The Mother in Grey Cardigan & House Dress (Poems 02, 09)",
                "poems": ["02", "09"],
                "kit_dir": "woman.mother_cardigan",
                "primary_torso": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/woman.mother_cardigan/stand_front.png",
            },
            {
                "id": "street_clothes_family",
                "label": "Street-Clothes Family & Reunion Brothers/Elders (Poems 10, 11, 12, 14)",
                "poems": ["10", "11", "12", "14"],
                "kit_dir": "family.street_clothes",
                "primary_torso": "arena/parts/kit3/v2/parts/family.street_clothes/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/family.street_clothes/stand_front.png",
            },
        ],
        "locomotion_cycles": build_locomotion_cycles("mother_ancestors_family", mf_h_ratio, adult_scale=0.98),
        "available_sheets": mf_sheets,
        "resolved_parts": mf_parts,
    }

    # =========================================================================
    # 8. dj_club_citizens
    # =========================================================================
    dj_scale_table = dict(BASE_PART_SCALE_TABLE)
    dj_h_ratio = 0.54
    dj_torso_frac = 0.32
    dj_parts = collect_kit_modular_parts(
        "party.dj_cyber",
        dj_h_ratio,
        dj_torso_frac,
        dj_scale_table,
        views=("front", "threequarter", "profile", "back"),
    )

    for club_kit in (
        "party.club_dress",
        "party.club_jacket",
        "party.club_shirt",
        "atlantis.atlantis_citizen",
        "atlantis.atlantis_gatekeeper",
        "angels.angel_white_robe",
    ):
        sub_parts = collect_kit_modular_parts(club_kit, dj_h_ratio, dj_torso_frac, dj_scale_table, views=("front", "profile", "back"))
        for k, v in sub_parts.items():
            dj_parts[f"{club_kit}.{k}"] = v

    for aid in (
        "party.dj_cyber.compact-core",
        "party.07.action.dj_cyber.torso-parts",
        "party.07.dj_cyber.main-poses",
        "08.cast.club.main-poses",
        "08.cast.angel.body",
        "08.cast.angel.wings",
        "atlantis.06.citizen_1.body",
        "atlantis.06.gatekeeper.body",
    ):
        a_obj = atlas_assets_by_id.get(aid)
        if a_obj:
            for p_item in a_obj.get("parts", [])[:2]:
                pid = p_item["id"]
                dj_parts[f"cut.{pid}"] = resolve_part_entry(
                    "wings" if "wings" in aid else "torso",
                    p_item["file"],
                    dj_h_ratio,
                    dj_torso_frac,
                    dj_scale_table,
                    pivots=p_item.get("pivots", []),
                    view="front",
                    label=p_item.get("label", pid),
                )

    dj_sheets = verify_sheets([
        "kits/packs/poem_07/01_CHARACTER_CORE/party.dj_cyber.compact-core.png",
        "kits/packs/poem_07/01_CHARACTER_CORE/party.dj_cyber.body.profile.png",
        "kits/packs/poem_07/01_CHARACTER_CORE/party.dj_cyber.heads.png",
        "kits/packs/poem_07/01_CHARACTER_CORE/party.dj_cyber.face-feet.png",
        "kits/packs/poem_07/01_CHARACTER_CORE/party.07.dj-guest.cap-noses-headphones.png",
        "kits/packs/poem_07/02_ACTIONS_AND_POSES/party.07.action.dj_cyber.torso-parts.png",
        "kits/packs/poem_07/02_ACTIONS_AND_POSES/party.07.dj_cyber.main-poses.png",
        "kits/packs/poem_07/01_CHARACTER_CORE/08.cast.club_dress.body.png",
        "kits/packs/poem_07/01_CHARACTER_CORE/08.cast.club_jacket.body.png",
        "kits/packs/poem_07/01_CHARACTER_CORE/08.cast.club_shirt.body.png",
        "kits/packs/poem_07/02_ACTIONS_AND_POSES/08.cast.club.main-poses.png",
        "kits/packs/poem_08/01_CHARACTER_CORE/08.cast.angel.body.png",
        "kits/packs/poem_08/01_CHARACTER_CORE/08.cast.angel.wings.png",
        "kits/packs/poem_06/01_CHARACTER_CORE/atlantis.06.citizen_1.body.png",
        "kits/packs/poem_06/01_CHARACTER_CORE/atlantis.06.gatekeeper.body.png",
        "kits/packs/poem_06/01_CHARACTER_CORE/atlantis.06.traveler_1.body.png",
    ])

    rigs["dj_club_citizens"] = {
        "id": "dj_club_citizens",
        "name": "DJ, Club Dancers, Guardians & Atlantis Citizens",
        "character_role": "Cyber DJ with LED bomber & headphones (Poem 07), Club Dancers in dress/jacket/silk shirt (Poems 07, 08, 09), Winged Guardians/Angels (Poem 08), and Atlantis Citizens & Gatekeeper (Poems 06, 10, 12)",
        "poems": ["06", "07", "08", "10", "12"],
        "anatomy": {
            "head_count": 7.5,
            "height_cm": 182,
            "adult_scale_ratio": 1.00,
            "torso_to_body_fraction": dj_torso_frac,
            "hip_elevation_fraction": 0.53,
        },
        "canonical_height_stage_ratio": dj_h_ratio,
        "posture_stage_ratios": make_posture_ratios(dj_h_ratio),
        "aspect_compensation": {
            "threshold_w_over_h": 0.75,
            "standing_reference_ar": 0.41,
            "formula": "aspect_mult = (w/h > 0.75) ? clamp(1.0 / sqrt(1.0 + 1.35 * pow((w/h) - 0.50, 2)), 0.36, 0.82) : 1.0",
            "winged_guardian_note": "Angel wings use slot scale 1.35 relative to torso and attach to shoulder-blade sockets without altering the figure's 0.54 standing height.",
        },
        "part_scale_table": dj_scale_table,
        "joint_hierarchy": build_joint_hierarchy(head_scale=0.64, back_only=False),
        "costume_variants": [
            {
                "id": "dj_cyber",
                "label": "Cyber DJ w/ LED Piping & Headphones (Poem 07)",
                "poems": ["07"],
                "kit_dir": "party.dj_cyber",
                "primary_torso": "arena/parts/kit3/v2/parts/party.dj_cyber/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/party.dj_cyber/stand_front.png",
            },
            {
                "id": "club_dancer_dress",
                "label": "Club Dancer in Sequin Dress (Poems 07, 08)",
                "poems": ["07", "08"],
                "kit_dir": "party.club_dress",
                "primary_torso": "arena/parts/kit3/v2/parts/party.club_dress/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/party.club_dress/stand_front.png",
            },
            {
                "id": "atlantis_citizen",
                "label": "Atlantis Citizen in Neon-Trimmed Linen (Poems 06, 10)",
                "poems": ["06", "10"],
                "kit_dir": "atlantis.atlantis_citizen",
                "primary_torso": "arena/parts/kit3/v2/parts/atlantis.atlantis_citizen/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/atlantis.atlantis_citizen/stand_front.png",
            },
            {
                "id": "atlantis_gatekeeper",
                "label": "Atlantis Gatekeeper Guardian (Poem 06)",
                "poems": ["06"],
                "kit_dir": "atlantis.atlantis_gatekeeper",
                "primary_torso": "arena/parts/kit3/v2/parts/atlantis.atlantis_gatekeeper/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/atlantis.atlantis_gatekeeper/stand_front.png",
            },
            {
                "id": "angel_guardian",
                "label": "Winged Guardian / Angel in White Robe (Poem 08)",
                "poems": ["08"],
                "kit_dir": "angels.angel_white_robe",
                "primary_torso": "arena/parts/kit3/v2/parts/angels.angel_white_robe/body.front.torso.png",
                "primary_pose": "arena/parts/kit3/v2/poses/angels.angel_white_robe/stand_front.png",
            },
        ],
        "locomotion_cycles": build_locomotion_cycles("dj_club_citizens", dj_h_ratio, adult_scale=1.0),
        "available_sheets": dj_sheets,
        "resolved_parts": dj_parts,
    }

    # Summary statistics
    total_resolved_parts = sum(len(r["resolved_parts"]) for r in rigs.values())
    total_verified_sheets = sum(len(r["available_sheets"]) for r in rigs.values())
    missing_parts = [
        (rid, pk, pv["file"])
        for rid, r in rigs.items()
        for pk, pv in r["resolved_parts"].items()
        if not pv.get("exists", False)
    ]

    library = {
        "version": "2.0.0-canonical-kinematics-solver",
        "generated_by": "shots/arena/parts/kit3/build_character_rigs.py",
        "description": "WYGWYL Canonical Cast, Proportion Normalization, Aspect-Compensated Piece-Scaling & Locomotion Solver Library across all 14 poems",
        "stats": {
            "canonical_rig_count": len(rigs),
            "poems_covered": 14,
            "total_resolved_parts": total_resolved_parts,
            "total_verified_sheets": total_verified_sheets,
            "missing_part_files": len(missing_parts),
            "locomotion_cycle_types": [
                "walk",
                "run",
                "waltz",
                "read",
                "reach",
                "crouch",
                "fall",
                "floor_recovery",
                "vape_turn",
                "dj_spin",
                "idle_breathe",
            ],
        },
        "stage_calibration": {
            "focal_plane_z": 1.0,
            "reference_stage_px": [STAGE_REF_W, STAGE_REF_H],
            "floor_baseline_y_ratio": 0.86,
            "adult_head_count": 7.5,
            "child_age7_head_count": 5.2,
            "child_to_adult_height_ratio": 0.68,
            "posture_height_ratios": {
                "standing_adult": 0.54,
                "standing_tall_ex": 0.555,
                "standing_woman": 0.52,
                "standing_child_age7": 0.37,
                "kneeling_adult": 0.42,
                "kneeling_child": 0.29,
                "seated_or_crouched_adult": 0.36,
                "seated_or_crouched_child": 0.25,
                "floor_recovery_adult": 0.31,
                "floor_recovery_child": 0.21,
                "prone_or_falling_adult": 0.22,
                "prone_or_falling_child": 0.15,
            },
            "global_aspect_compensation_formula": {
                "threshold_w_over_h": 0.75,
                "standing_reference_ar": 0.40,
                "formula": "if (w/h > 0.75) multiplier = clamp(1.0 / sqrt(1.0 + 1.35 * pow((w/h) - 0.50, 2)), 0.36, 0.82); else multiplier = 1.0",
                "single_part_torso_rule": "Scale single-part torso cards by anatomical torso height (canonical_height_stage_ratio * 0.32 * stage_H) rather than full standing figure bbox height.",
            },
        },
        "canonical_part_scale_table": BASE_PART_SCALE_TABLE,
        "rigs": rigs,
        "rigs_list": list(rigs.values()),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2)

    print(f"[OK] Wrote {OUT_PATH}")
    print(f"     Canonical rigs : {len(rigs)}")
    print(f"     Resolved parts : {total_resolved_parts} (missing: {len(missing_parts)})")
    print(f"     Verified sheets: {total_verified_sheets}")
    if missing_parts:
        for mp in missing_parts[:10]:
            print("     [WARN] Missing:", mp)
        sys.exit(1)


if __name__ == "__main__":
    main()
