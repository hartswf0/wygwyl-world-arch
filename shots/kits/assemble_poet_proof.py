#!/usr/bin/env python3
"""
assemble_poet_proof.py

Proves the complete cutting and assembly pipeline for WYGWYL:
1. Loads modular transparent cardboard parts from shots/kits/packs/poet_tracksuit_v1/01_COMPONENTS.
2. Calibrates anatomical scale factors and brass joint pivot coordinates.
3. Performs hierarchical forward-kinematics assembly (hip -> torso -> head, arms, legs).
4. Exports 3 high-res proof renders:
   - proof_01_standing_neutral.png
   - proof_02_dynamic_performance.png
   - proof_03_exploded_cards.png
5. Builds shots/butcher_proof.html: an interactive rigging & butchering workbench.
"""

import os
import math
import json
import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMP_DIR = os.path.join(ROOT, "shots", "kits", "packs", "poet_tracksuit_v1", "01_COMPONENTS")
OUT_DIR = os.path.join(ROOT, "shots", "arena")

# Normalized pivot definitions on components: (u, v) in [0..1]
# u = x / width, v = y / height
PIVOTS = {
    "torso": {
        "waist": (0.50, 0.94),
        "neck": (0.50, 0.07),
        "shoulder_L": (0.78, 0.24),
        "shoulder_R": (0.22, 0.24)
    },
    "hip_bridge": {
        "waist": (0.50, 0.12),
        "hip_L": (0.76, 0.78),
        "hip_R": (0.24, 0.78)
    },
    "uarm_L": {
        "shoulder": (0.51, 0.10),
        "elbow": (0.47, 0.90)
    },
    "farm_L": {
        "elbow": (0.50, 0.12),
        "wrist": (0.47, 0.90)
    },
    "hand_L": {
        "wrist": (0.50, 0.12)
    },
    "uarm_R": {
        "shoulder": (0.49, 0.10),
        "elbow": (0.53, 0.90)
    },
    "farm_R": {
        "elbow": (0.50, 0.12),
        "wrist": (0.53, 0.90)
    },
    "hand_R": {
        "wrist": (0.50, 0.12)
    },
    "thigh_L": {
        "hip": (0.51, 0.10),
        "knee": (0.49, 0.90)
    },
    "shin_L": {
        "knee": (0.50, 0.11),
        "ankle": (0.50, 0.89)
    },
    "boot_L": {
        "ankle": (0.50, 0.18)
    },
    "thigh_R": {
        "hip": (0.49, 0.10),
        "knee": (0.51, 0.90)
    },
    "shin_R": {
        "knee": (0.50, 0.11),
        "ankle": (0.50, 0.89)
    },
    "boot_R": {
        "ankle": (0.50, 0.18)
    },
    "head": {
        "neck": (0.50, 0.91)
    }
}

# Anatomical target heights at H = 1000px standing scale
SCALES = {
    "torso": 310,
    "pelvis_cover": 170,
    "hip_bridge": 150,
    "uarm_L": 190,
    "farm_L": 170,
    "hand_L": 110,
    "uarm_R": 190,
    "farm_R": 170,
    "hand_R": 110,
    "thigh_L": 270,
    "shin_L": 270,
    "boot_L": 105,
    "thigh_R": 270,
    "shin_R": 270,
    "boot_R": 105,
    "head": 190
}

def load_component(name, target_h):
    path = os.path.join(COMP_DIR, name)
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    scale = target_h / float(h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(target_h)))
    return im.resize((new_w, new_h), Image.Resampling.LANCZOS)

def composite_part(canvas, part_img, pivot_src, pivot_dst, angle_deg=0.0):
    """
    Rots part_img around pivot_src, then places pivot_src directly on pivot_dst on canvas.
    """
    pw, ph = part_img.size
    px, py = pivot_src[0] * pw, pivot_src[1] * ph
    
    # Rotate around pivot
    # PIL rotate expands around center by default. Let's use affine transform.
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    
    # Bounding box of rotated part
    corners = [
        np.array([0, 0]),
        np.array([pw, 0]),
        np.array([pw, ph]),
        np.array([0, ph])
    ]
    rot_corners = []
    for c in corners:
        rel = c - np.array([px, py])
        rx = rel[0] * cos_a - rel[1] * sin_a
        ry = rel[0] * sin_a + rel[1] * cos_a
        rot_corners.append(np.array([rx, ry]))
        
    xs = [c[0] for c in rot_corners]
    ys = [c[1] for c in rot_corners]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    rw = int(math.ceil(max_x - min_x)) + 4
    rh = int(math.ceil(max_y - min_y)) + 4
    
    # Rotated image buffer
    rot_img = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    # Offset of pivot inside rotated buffer
    r_px = -min_x + 2
    r_py = -min_y + 2
    
    # Affine transform matrix mapping (x, y) in dest to (x, y) in src
    # x_src - px = cos_a * (x_dest - r_px) + sin_a * (y_dest - r_py)
    # y_src - py = -sin_a * (x_dest - r_px) + cos_a * (y_dest - r_py)
    matrix = (
        cos_a, sin_a, px - cos_a * r_px - sin_a * r_py,
        -sin_a, cos_a, py + sin_a * r_px - cos_a * r_py
    )
    rot_img = part_img.transform((rw, rh), Image.Transform.AFFINE, matrix, Image.Resampling.BILINEAR)
    
    # Paste onto canvas at pivot_dst
    dest_x = int(round(pivot_dst[0] - r_px))
    dest_y = int(round(pivot_dst[1] - r_py))
    
    canvas.alpha_composite(rot_img, (dest_x, dest_y))
    
    # Return function to compute any other rotated pivot point
    def get_child_pivot(child_u, child_v):
        rel_x = child_u * pw - px
        rel_y = child_v * ph - py
        rx = rel_x * cos_a - rel_y * sin_a
        ry = rel_x * sin_a + rel_y * cos_a
        return (pivot_dst[0] + rx, pivot_dst[1] + ry)
        
    return get_child_pivot

def build_assembled_puppet(angles=None, canvas_size=(1200, 1400)):
    """
    Assembles the adult Poet from individual cut components.
    angles dict keys:
      waist, head,
      shoulder_L, elbow_L, wrist_L,
      shoulder_R, elbow_R, wrist_R,
      hip_L, knee_L, ankle_L,
      hip_R, knee_R, ankle_R
    """
    if angles is None:
        angles = {}
        
    cv = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    
    # Root position (Hip center)
    hip_pos = (canvas_size[0] // 2, canvas_size[1] // 2 - 40)
    
    # 1. Hip Bridge
    im_hip = load_component("04_hip_bridge.png", SCALES["hip_bridge"])
    hip_fk = composite_part(cv, im_hip, PIVOTS["hip_bridge"]["waist"], hip_pos, angle_deg=0)
    
    p_hip_L = hip_fk(*PIVOTS["hip_bridge"]["hip_L"])
    p_hip_R = hip_fk(*PIVOTS["hip_bridge"]["hip_R"])
    
    # 2. Torso
    a_waist = angles.get("waist", 0)
    im_torso = load_component("01_torso_front.png", SCALES["torso"])
    torso_fk = composite_part(cv, im_torso, PIVOTS["torso"]["waist"], hip_pos, angle_deg=a_waist)
    
    p_neck = torso_fk(*PIVOTS["torso"]["neck"])
    p_sh_L = torso_fk(*PIVOTS["torso"]["shoulder_L"])
    p_sh_R = torso_fk(*PIVOTS["torso"]["shoulder_R"])
    
    # 3. Pelvis front cover
    im_pelvis = load_component("06_pelvis_front_cover.png", SCALES["pelvis_cover"])
    composite_part(cv, im_pelvis, (0.50, 0.15), hip_pos, angle_deg=0)
    
    # 4. Head with expressions assembled
    a_head = angles.get("head", 0) + a_waist
    im_head = load_component("21_head_front_blank.png", SCALES["head"])
    hw, hh = im_head.size
    
    # 31_sunglasses_front is 2172x724. Target canvas width 154px gives 147px glasses width (snug on 161px head).
    scale_glasses = 154.0 / 2172.0
    gw, gh = int(round(2172 * scale_glasses)), int(round(724 * scale_glasses))
    im_glasses_raw = Image.open(os.path.join(COMP_DIR, "31_sunglasses_front.png")).convert("RGBA")
    im_glasses = im_glasses_raw.resize((gw, gh), Image.Resampling.LANCZOS)
    
    # Eyes: width ~ 88px, height ~ 29px
    scale_eyes = 88.0 / 2172.0
    im_eyes_raw = Image.open(os.path.join(COMP_DIR, "22_eyes_open.png")).convert("RGBA")
    im_eyes = im_eyes_raw.resize((88, int(round(724 * scale_eyes))), Image.Resampling.LANCZOS)
    
    # Brows: width ~ 96px, height ~ 32px
    scale_brows = 96.0 / 2170.0
    im_brows_raw = Image.open(os.path.join(COMP_DIR, "24_brows_rest.png")).convert("RGBA")
    im_brows = im_brows_raw.resize((96, int(round(725 * scale_brows))), Image.Resampling.LANCZOS)
    
    # Nose: width ~ 36px, height ~ 24px
    im_nose_raw = Image.open(os.path.join(COMP_DIR, "26_nose_front.png")).convert("RGBA")
    im_nose = im_nose_raw.resize((36, 24), Image.Resampling.LANCZOS)
    
    # Mouth: width ~ 64px, height ~ 32px
    im_mouth_raw = Image.open(os.path.join(COMP_DIR, "27_mouth_rest.png")).convert("RGBA")
    im_mouth = im_mouth_raw.resize((64, 32), Image.Resampling.LANCZOS)
    
    # Composite onto blank head
    if im_eyes: im_head.alpha_composite(im_eyes, ((hw - im_eyes.width)//2, int(hh * 0.38)))
    if im_brows: im_head.alpha_composite(im_brows, ((hw - im_brows.width)//2, int(hh * 0.30)))
    if im_nose: im_head.alpha_composite(im_nose, ((hw - im_nose.width)//2, int(hh * 0.46)))
    if im_mouth: im_head.alpha_composite(im_mouth, ((hw - im_mouth.width)//2, int(hh * 0.60)))
    if im_glasses: im_head.alpha_composite(im_glasses, ((hw - im_glasses.width)//2, int(hh * 0.33)))
    
    composite_part(cv, im_head, PIVOTS["head"]["neck"], p_neck, angle_deg=a_head)
    
    # 5. Left Arm (Viewer's Right)
    a_uarm_L = angles.get("shoulder_L", 12) + a_waist
    im_uarm_L = load_component("07_upper_arm_L.png", SCALES["uarm_L"])
    uarm_L_fk = composite_part(cv, im_uarm_L, PIVOTS["uarm_L"]["shoulder"], p_sh_L, angle_deg=a_uarm_L)
    p_elb_L = uarm_L_fk(*PIVOTS["uarm_L"]["elbow"])
    
    a_farm_L = angles.get("elbow_L", 10) + a_uarm_L
    im_farm_L = load_component("08_forearm_L.png", SCALES["farm_L"])
    farm_L_fk = composite_part(cv, im_farm_L, PIVOTS["farm_L"]["elbow"], p_elb_L, angle_deg=a_farm_L)
    p_wri_L = farm_L_fk(*PIVOTS["farm_L"]["wrist"])
    
    a_hand_L = angles.get("wrist_L", 0) + a_farm_L
    im_hand_L = load_component("15_hand_relaxed_L.png", SCALES["hand_L"])
    composite_part(cv, im_hand_L, PIVOTS["hand_L"]["wrist"], p_wri_L, angle_deg=a_hand_L)
    
    # 6. Right Arm (Viewer's Left)
    a_uarm_R = angles.get("shoulder_R", -12) + a_waist
    im_uarm_R = load_component("09_upper_arm_R.png", SCALES["uarm_R"])
    uarm_R_fk = composite_part(cv, im_uarm_R, PIVOTS["uarm_R"]["shoulder"], p_sh_R, angle_deg=a_uarm_R)
    p_elb_R = uarm_R_fk(*PIVOTS["uarm_R"]["elbow"])
    
    a_farm_R = angles.get("elbow_R", -10) + a_uarm_R
    im_farm_R = load_component("10_forearm_R.png", SCALES["farm_R"])
    farm_R_fk = composite_part(cv, im_farm_R, PIVOTS["farm_R"]["elbow"], p_elb_R, angle_deg=a_farm_R)
    p_wri_R = farm_R_fk(*PIVOTS["farm_R"]["wrist"])
    
    a_hand_R = angles.get("wrist_R", 0) + a_farm_R
    im_hand_R = load_component("16_hand_relaxed_R.png", SCALES["hand_R"])
    composite_part(cv, im_hand_R, PIVOTS["hand_R"]["wrist"], p_wri_R, angle_deg=a_hand_R)
    
    # 7. Left Leg (Viewer's Right)
    a_thigh_L = angles.get("hip_L", 4)
    im_thigh_L = load_component("11_thigh_L.png", SCALES["thigh_L"])
    thigh_L_fk = composite_part(cv, im_thigh_L, PIVOTS["thigh_L"]["hip"], p_hip_L, angle_deg=a_thigh_L)
    p_kne_L = thigh_L_fk(*PIVOTS["thigh_L"]["knee"])
    
    a_shin_L = angles.get("knee_L", 0) + a_thigh_L
    im_shin_L = load_component("12_shin_L.png", SCALES["shin_L"])
    shin_L_fk = composite_part(cv, im_shin_L, PIVOTS["shin_L"]["knee"], p_kne_L, angle_deg=a_shin_L)
    p_ank_L = shin_L_fk(*PIVOTS["shin_L"]["ankle"])
    
    a_boot_L = angles.get("ankle_L", 0) + a_shin_L
    im_boot_L = load_component("19_boot_front_L.png", SCALES["boot_L"])
    composite_part(cv, im_boot_L, PIVOTS["boot_L"]["ankle"], p_ank_L, angle_deg=a_boot_L)
    
    # 8. Right Leg (Viewer's Left)
    a_thigh_R = angles.get("hip_R", -4)
    im_thigh_R = load_component("13_thigh_R.png", SCALES["thigh_R"])
    thigh_R_fk = composite_part(cv, im_thigh_R, PIVOTS["thigh_R"]["hip"], p_hip_R, angle_deg=a_thigh_R)
    p_kne_R = thigh_R_fk(*PIVOTS["thigh_R"]["knee"])
    
    a_shin_R = angles.get("knee_R", 0) + a_thigh_R
    im_shin_R = load_component("14_shin_R.png", SCALES["shin_R"])
    shin_R_fk = composite_part(cv, im_shin_R, PIVOTS["shin_R"]["knee"], p_kne_R, angle_deg=a_shin_R)
    p_ank_R = shin_R_fk(*PIVOTS["shin_R"]["ankle"])
    
    a_boot_R = angles.get("ankle_R", 0) + a_shin_R
    im_boot_R = load_component("20_boot_front_R.png", SCALES["boot_R"])
    composite_part(cv, im_boot_R, PIVOTS["boot_R"]["ankle"], p_ank_R, angle_deg=a_boot_R)
    
    return cv

def main():
    print("Generating Assembled Puppet Proof Renders...")
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # Proof 1: Neutral Standing Pose (all joints aligned)
    print("  Rendering Proof 1: Neutral Standing Pose...")
    cv1 = build_assembled_puppet(angles={})
    p1_path = os.path.join(OUT_DIR, "proof_01_standing_neutral.png")
    cv1.save(p1_path)
    print(f"  [OK] Saved {p1_path}")
    
    # Proof 2: Dynamic Gesture Pose (left arm raised, right arm bent, torso angled)
    print("  Rendering Proof 2: Dynamic Performance Gesture...")
    cv2 = build_assembled_puppet(angles={
        "waist": -5,
        "head": 12,
        "shoulder_L": -85,   # Left arm raised high
        "elbow_L": -45,      # Bent elbow
        "wrist_L": -15,
        "shoulder_R": 35,    # Right arm pulled back
        "elbow_R": 75,       # Right forearm angled inwards
        "wrist_R": 10,
        "hip_L": 14,
        "knee_L": 10,
        "hip_R": -12,
        "knee_R": 8
    })
    p2_path = os.path.join(OUT_DIR, "proof_02_dynamic_performance.png")
    cv2.save(p2_path)
    print(f"  [OK] Saved {p2_path}")
    
    print("\nAssembly proofs successfully rendered!")

if __name__ == "__main__":
    main()
