#!/usr/bin/env python3
"""
WYGWYL "Some Assembly Required" Compound Rigs, Multi-Beat Action Sequences,
Portal Worlds, Water Dioramas, Interior Set Ensembles & Foot/Hand Trust Matrix Builder
======================================================================================
Builds `shots/arena/parts/kit3/release_v2/assemblies_library.json` covering all 14
canonical interactive assemblies requested by the director:

  1.  car_wheels_headlights_passengers  (Poem 02 Family Sedan + Spinning Wheels + Headlights + Passengers Talking Inside)
  2.  poet_motorcycle_multi_aspect      (Poem 10 & 11 Poet Riding Motorcycle across 5 Aspects/Dimensions)
  3.  beating_heart_and_hourglass       (Poem 04 Beating Heart Systole/Diastole + Poem 12 Turning Hourglass & Sand)
  4.  putting_on_the_hands_weave        (Weave P04 4-Beat "Putting On the Hands" Brad-Snap Assembly Sequence)
  5.  throwing_tambourine_rose_window   (Poem 02 & 03 Throwing Tambourine Through Gothic Rose Window + Shatter)
  6.  phone_booth_walk_and_call         (Poem 02 & 09 Walking Up to Phone Booth + Talking on Phone + Lip-Sync Two-Shot)
  7.  dj_booth_speakers_and_club_extras (Poem 07 & 08 DJ Decks + Pulsing Speakers/VU + Club Extras Dancing)
  8.  picking_up_the_flower_harvest     (Poem 04 & 13 Mustard Seed Blooming + Picking Up Flower + Becoming Harvest)
  9.  angel_and_raven_wings_flight      (Poem 04 & 08 Articulated Angel Wings 4-Pair Cycle + Raven Wings & Foley)
  10. tv_window_door_portals            (Poem 01, 02, 03, 06, 09 TVs, Windows, Doors & Atlantis Gate Portals)
  11. water_worlds_and_boats_ensemble   (Poem 03, 04, 11, 13, 14 Multi-Layer Water Dioramas & Jupiter Boats)
  12. interior_decorator_reusable_sets  (Poem 02, 09, 13 Interactive Interior Decorator: Living Room, Mother's Room, Bistro Cafe)
  13. clouds_and_volumetric_light_rig   (Poem 02, 04, 06, 11 Parting Clouds, Moon Reach, Drowned Light & Fog Halo)
  14. right_foot_right_hand_matrix      (12-Action "Right Foot & Right Hand for the Job" Interactive Trust Matrix)

Every single image/video/audio asset path is verified on disk under `shots/`.
"""

import json
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS_DIR = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT_PATH = os.path.join(HERE, "release_v2", "assemblies_library.json")

_IMG_CACHE = {}


def cut_path(pack_id: str, idx: int) -> str:
    return f"arena/parts/kit3/release_v2/cuts/{pack_id}/{pack_id}__p{idx:02d}.png"


def ts_path(comp_name: str) -> str:
    return f"kits/packs/poet_tracksuit_v1/01_COMPONENTS/{comp_name}.png"


def v2_part_path(kit_dir: str, filename: str) -> str:
    return f"arena/parts/kit3/v2/parts/{kit_dir}/{filename}"


def verify_asset(rel_shots_path: str) -> dict:
    """Verify an asset relative to `shots/` and return its dimensions and metadata."""
    clean = rel_shots_path.lstrip("/")
    if clean.startswith("shots/"):
        clean = clean[len("shots/"):]
    if clean in _IMG_CACHE:
        return _IMG_CACHE[clean]

    abs_p = os.path.join(SHOTS_DIR, clean)
    exists = os.path.exists(abs_p)
    w, h = 256, 256
    if exists and clean.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        try:
            with Image.open(abs_p) as im:
                w, h = im.size
        except Exception:
            pass
    info = {
        "file": clean,
        "repo_path": "shots/" + clean,
        "exists": exists,
        "width": w,
        "height": h,
    }
    _IMG_CACHE[clean] = info
    return info


def make_layer(
    layer_id: str,
    label: str,
    rel_file: str,
    role: str,
    z_order: int,
    assembled_pose: dict,
    exploded_pose: dict = None,
    pivot_nx: float = 0.5,
    pivot_ny: float = 0.5,
    anim_behavior: str = "static",
) -> dict:
    meta = verify_asset(rel_file)
    if not exploded_pose:
        exploded_pose = {
            "x": round(assembled_pose.get("x", 0.5) + (0.18 if z_order % 2 == 0 else -0.18), 3),
            "y": round(assembled_pose.get("y", 0.5) + ((z_order - 5) * 0.045), 3),
            "scale": assembled_pose.get("scale", 1.0),
            "rot_deg": 0.0,
        }
    return {
        "id": layer_id,
        "label": label,
        "role": role,
        "z_order": z_order,
        "file": meta["file"],
        "repo_path": meta["repo_path"],
        "exists": meta["exists"],
        "width": meta["width"],
        "height": meta["height"],
        "pivot": {"nx": pivot_nx, "ny": pivot_ny},
        "assembled": assembled_pose,
        "exploded": exploded_pose,
        "anim_behavior": anim_behavior,
    }


def main():
    assemblies = []

    # =========================================================================
    # 1. car_wheels_headlights_passengers (Poem 02)
    # =========================================================================
    assemblies.append({
        "id": "car_wheels_headlights_passengers",
        "number": 1,
        "title": "1. Family Sedan: Putting On Wheels + Headlights + People Talking Inside",
        "poem": "Poem 02 — Car Argument & Night Highway",
        "category": "vehicle_rig",
        "sound_fx_preset": "car_engine_roll",
        "summary": "Explodable 18-part 1990s family sedan with independent spinning front/rear wheel discs, interior seats, Father & Mother talking behind the door sheet metal inside the window cutouts, tinted window glass overlay, steering wheel, flashing amber hazards, and volumetric iris headlight beams.",
        "assembly_modes": [
            {"id": "exploded", "label": "1. Exploded Parts Sheet (Unassembled)"},
            {"id": "snap_wheels", "label": "2. Snap Wheels & Seats On (Brad-Snap)"},
            {"id": "seat_passengers", "label": "3. Seat Father, Mother & Young Poet Inside Window Cutouts"},
            {"id": "drive_headlights", "label": "4. Roll Car, Spin Wheels & Flash Headlights/Hazards"},
        ],
        "layers": [
            make_layer("rear_departure_card", "Rear-View Sedan Departure Variant (p02)", cut_path("02.props.car", 2), "variant_view", 0, {"x": 0.12, "y": 0.34, "scale": 0.34, "rot_deg": 0}),
            make_layer("seat_rear", "Rear Bench Seat (p14)", cut_path("02.props.car", 14), "interior_back", 1, {"x": 0.37, "y": 0.54, "scale": 0.32, "rot_deg": 0, "flipX": True}),
            make_layer("seat_front", "Front Bucket Seat (p13)", cut_path("02.props.car", 13), "interior_back", 2, {"x": 0.50, "y": 0.54, "scale": 0.32, "rot_deg": 0, "flipX": True}),
            make_layer("passenger_mother", "Mother Turning & Talking in Cabin (car-argument p02)", cut_path("parents.02.car-argument", 2), "passenger", 3, {"x": 0.40, "y": 0.50, "scale": 0.33, "rot_deg": 0}, anim_behavior="talk_bob_passenger"),
            make_layer("passenger_father", "Father Driving & Talking in Cabin (car-argument p01)", cut_path("parents.02.car-argument", 1), "passenger", 4, {"x": 0.53, "y": 0.50, "scale": 0.34, "rot_deg": 0, "flipX": True}, anim_behavior="talk_bob_driver"),
            make_layer("passenger_gesture", "Conversational Hand Gesture (car-argument p04)", cut_path("parents.02.car-argument", 4), "passenger_hand", 5, {"x": 0.47, "y": 0.51, "scale": 0.32, "rot_deg": -8}, anim_behavior="gesture_wave"),
            make_layer("steering_wheel", "Steering Wheel & Column (p12)", cut_path("02.props.car", 12), "interior_control", 6, {"x": 0.59, "y": 0.51, "scale": 0.26, "rot_deg": -12, "flipX": True}, anim_behavior="steer_rock"),
            make_layer("window_glass", "Translucent Side-Window Glazing Insert (p03)", cut_path("02.props.car", 3), "glazing", 7, {"x": 0.47, "y": 0.49, "scale": 0.68, "rot_deg": 0, "alpha": 0.14, "flipX": True}),
            make_layer("car_body_shell", "Sedan Profile Body Shell w/ Empty Wheel Wells & Window Cutouts (p01)", cut_path("02.props.car", 1), "chassis_shell", 8, {"x": 0.48, "y": 0.56, "scale": 1.08, "rot_deg": 0, "flipX": True}, anim_behavior="chassis_suspension_bounce"),
            make_layer("wheel_rear", "Rear Wheel & Tire Disc w/ Axle Hub (p06)", cut_path("02.props.car", 6), "wheel_spin", 9, {"x": 0.305, "y": 0.675, "scale": 0.52, "rot_deg": 0}, {"x": 0.18, "y": 0.84, "scale": 0.52, "rot_deg": 45}, anim_behavior="spin_wheel_cw"),
            make_layer("wheel_front", "Front Wheel & Tire Disc w/ Axle Hub (p05)", cut_path("02.props.car", 5), "wheel_spin", 10, {"x": 0.695, "y": 0.675, "scale": 0.52, "rot_deg": 0}, {"x": 0.82, "y": 0.84, "scale": 0.52, "rot_deg": -45}, anim_behavior="spin_wheel_cw"),
            make_layer("headlight_lens_L", "Front Headlight Lens Insert (p07)", cut_path("02.props.car", 7), "light_insert", 11, {"x": 0.81, "y": 0.56, "scale": 0.28, "rot_deg": 0, "flipX": True}, anim_behavior="headlight_glow"),
            make_layer("hazard_amber", "Amber Turn-Signal / Hazard Light Insert (p09)", cut_path("02.props.car", 9), "hazard_blink", 12, {"x": 0.80, "y": 0.60, "scale": 0.22, "rot_deg": 0}, anim_behavior="hazard_flash"),
            make_layer("headlight_beam", "Volumetric Iris Headlight Cone (lights-iris p01)", cut_path("02.fx.lights-iris", 1), "fx_beam", 13, {"x": 0.90, "y": 0.57, "scale": 0.72, "rot_deg": 4, "alpha": 0.78}, anim_behavior="beam_pulse"),
        ],
    })

    # =========================================================================
    # 2. poet_motorcycle_multi_aspect (Poem 10 & 11)
    # =========================================================================
    assemblies.append({
        "id": "poet_motorcycle_multi_aspect",
        "number": 2,
        "title": "2. Poet Riding the Motorcycle Across 5 Aspects / Dimensions",
        "poem": "Poems 10 & 11 — Night Ride, Banking Turn & Parked Motorcycle",
        "category": "vehicle_rig",
        "sound_fx_preset": "motorcycle_rev",
        "summary": "Modular motorcycle skeleton (frame, spoked wheels, brake rotors, front fork, exhaust, headlight) straddled by the 31-part Tracksuit Poet rig (far leg behind frame, grip hands on bars, near boot on footpeg in front of frame), plus 5 switchable aspect dimensions.",
        "aspect_dimensions": [
            {"id": "side_profile_cruise", "label": "1. Side Profile Cruise (Skeleton + Straddled Poet)"},
            {"id": "threequarter_bank_lean", "label": "2. 3/4 Banking Turn Lean (-22° Tilt)"},
            {"id": "front_headlight_approach", "label": "3. Front Headlight Approach (Toward Camera)"},
            {"id": "rear_taillight_departure", "label": "4. Rear Tail-Light Departure (Into Horizon)"},
            {"id": "parked_motorcycle_11", "label": "5. Parked Motorcycle Assembly (Poem 11)"},
        ],
        "layers": [
            make_layer("poet_far_leg", "Poet Far Thigh & Boot (Behind Frame)", ts_path("13_thigh_R"), "rider_far", 1, {"x": 0.47, "y": 0.55, "scale": 0.40, "rot_deg": 38}),
            make_layer("bike_rear_wheel", "Rear Spoked Wheel (bike-skeleton p09)", cut_path("10.props.bike-skeleton", 9), "wheel_spin", 2, {"x": 0.33, "y": 0.64, "scale": 0.52, "rot_deg": 0}, anim_behavior="spin_wheel_cw"),
            make_layer("bike_front_wheel", "Front Spoked Wheel (bike-skeleton p07)", cut_path("10.props.bike-skeleton", 7), "wheel_spin", 3, {"x": 0.65, "y": 0.64, "scale": 0.52, "rot_deg": 0}, anim_behavior="spin_wheel_cw"),
            make_layer("bike_brake_rotor", "Front Disc Brake Rotor (bike-skeleton p08)", cut_path("10.props.bike-skeleton", 8), "wheel_spin", 4, {"x": 0.65, "y": 0.64, "scale": 0.30, "rot_deg": 0}, anim_behavior="spin_wheel_cw"),
            make_layer("bike_exhaust", "Chrome Exhaust Pipe (bike-skeleton p11)", cut_path("10.props.bike-skeleton", 11), "chassis", 5, {"x": 0.40, "y": 0.63, "scale": 0.48, "rot_deg": 0}),
            make_layer("bike_frame", "Tubular Frame, Tank & Engine Block (bike-skeleton p01)", cut_path("10.props.bike-skeleton", 1), "chassis_shell", 6, {"x": 0.49, "y": 0.56, "scale": 0.88, "rot_deg": 0}, anim_behavior="chassis_suspension_bounce"),
            make_layer("bike_front_fork", "Telescopic Front Fork & Bars (bike-skeleton p04)", cut_path("10.props.bike-skeleton", 4), "chassis", 7, {"x": 0.60, "y": 0.52, "scale": 0.56, "rot_deg": -14}),
            make_layer("poet_torso_lean", "Poet Tracksuit Torso Leaning Forward (01_torso_front)", ts_path("01_torso_front"), "rider_core", 8, {"x": 0.46, "y": 0.42, "scale": 0.44, "rot_deg": 24}),
            make_layer("poet_head_sunglasses", "Poet Head + Sunglasses (21_head + 31_sunglasses)", ts_path("21_head_front_blank"), "rider_head", 9, {"x": 0.51, "y": 0.30, "scale": 0.28, "rot_deg": 8}),
            make_layer("poet_near_thigh", "Poet Near Thigh Straddling Tank (11_thigh_L)", ts_path("11_thigh_L"), "rider_near", 10, {"x": 0.48, "y": 0.54, "scale": 0.42, "rot_deg": 44}),
            make_layer("poet_near_shin", "Poet Near Shin Tucked Over Boot (12_shin_L)", ts_path("12_shin_L"), "rider_near", 11, {"x": 0.51, "y": 0.62, "scale": 0.38, "rot_deg": -28}),
            make_layer("poet_peg_boot", "Poet Chelsea Boot Planted on Footpeg (19_boot_front_L)", ts_path("19_boot_front_L"), "rider_foot", 12, {"x": 0.50, "y": 0.68, "scale": 0.25, "rot_deg": 12}),
            make_layer("poet_grip_arm", "Poet Forearm & Grip Hand on Throttle (08_forearm_L)", ts_path("08_forearm_L"), "rider_arm", 13, {"x": 0.55, "y": 0.44, "scale": 0.36, "rot_deg": -52}),
            make_layer("bike_headlight", "Headlight Bucket & Lens (bike-skeleton p12)", cut_path("10.props.bike-skeleton", 12), "light_insert", 14, {"x": 0.64, "y": 0.46, "scale": 0.28, "rot_deg": 0}),
            make_layer("ride_light_beam", "Headlight Cone & Wet Asphalt Glare (10.fx.ride-light p01)", cut_path("10.fx.ride-light", 1), "fx_beam", 15, {"x": 0.82, "y": 0.54, "scale": 0.72, "rot_deg": 6}, anim_behavior="beam_pulse"),
            make_layer("aspect_3q_view", "3/4 Banking Turn Rider Cutout (bike-ride-views p01)", cut_path("10.props.bike-ride-views", 1), "aspect_card", 16, {"x": 0.50, "y": 0.54, "scale": 0.85, "rot_deg": -18}),
            make_layer("aspect_front_view", "Front Headlight Approach Cutout (bike-ride-views p05)", cut_path("10.props.bike-ride-views", 5), "aspect_card", 17, {"x": 0.50, "y": 0.54, "scale": 0.85, "rot_deg": 0}),
            make_layer("aspect_rear_view", "Rear Tail-Light Departure Cutout (bike-ride-views p09)", cut_path("10.props.bike-ride-views", 9), "aspect_card", 18, {"x": 0.50, "y": 0.54, "scale": 0.85, "rot_deg": 0}),
            make_layer("aspect_parked_11", "Parked Motorcycle on Kickstand (11.props.parked-motorcycle p01)", cut_path("11.props.parked-motorcycle", 1), "aspect_card", 19, {"x": 0.50, "y": 0.56, "scale": 0.88, "rot_deg": 0}),
        ],
    })

    # =========================================================================
    # 3. beating_heart_and_hourglass (Poem 04 & 12)
    # =========================================================================
    assemblies.append({
        "id": "beating_heart_and_hourglass",
        "number": 3,
        "title": "3. The Beating Heart (Systole/Diastole) + Turning Hourglass & Falling Sand",
        "poem": "Poems 04 & 12 — Cardiac Pulse & The Last Hourglass",
        "category": "symbolic_mechanism",
        "sound_fx_preset": "heartbeat_lubdub",
        "summary": "Dual symbolic mechanism pairing the anatomical cardboard Heart (`04.props.heart` chambers, aorta, vessels, and concentric pulse rings contracting in dual-beat Lub-Dub systole/diastole) with the Last Hourglass (`12.props.last-hourglass` 6 progressive sand-fill levels, falling sand stream, and `12.props.hand-hourglass` 180° hand flip).",
        "layers": [
            make_layer("heart_pulse_ring_outer", "Outer Acoustic Pulse Ring (04.props.heart p11)", cut_path("04.props.heart", 11), "pulse_fx", 1, {"x": 0.29, "y": 0.50, "scale": 0.86, "rot_deg": 0}, anim_behavior="systole_ring_expand"),
            make_layer("heart_pulse_ring_inner", "Inner Systole Pulse Ring (04.props.heart p10)", cut_path("04.props.heart", 10), "pulse_fx", 2, {"x": 0.29, "y": 0.50, "scale": 0.68, "rot_deg": 0}, anim_behavior="systole_ring_expand"),
            make_layer("heart_aorta_vessels", "Superior Aorta & Pulmonary Vessels (04.props.heart p05)", cut_path("04.props.heart", 5), "heart_vessel", 3, {"x": 0.29, "y": 0.34, "scale": 0.58, "rot_deg": 0}, anim_behavior="diastole_recoil"),
            make_layer("heart_atrium_R", "Right Atrium & Coronary Branch (04.props.heart p03)", cut_path("04.props.heart", 3), "heart_chamber", 4, {"x": 0.24, "y": 0.48, "scale": 0.56, "rot_deg": 0}, anim_behavior="systole_contract"),
            make_layer("heart_ventricle_main", "Left/Right Ventricle Core Chamber (04.props.heart p01)", cut_path("04.props.heart", 1), "heart_chamber", 5, {"x": 0.29, "y": 0.52, "scale": 0.78, "rot_deg": 0}, anim_behavior="systole_contract"),
            make_layer("heart_apex_valve", "Cardiac Apex & Lower Ventricle (04.props.heart p02)", cut_path("04.props.heart", 2), "heart_chamber", 6, {"x": 0.31, "y": 0.58, "scale": 0.54, "rot_deg": 0}, anim_behavior="systole_contract"),
            make_layer("hourglass_frame", "Turned Wood & Brass Hourglass Frame (12.props.last-hourglass p01)", cut_path("12.props.last-hourglass", 1), "hourglass_body", 7, {"x": 0.71, "y": 0.50, "scale": 0.84, "rot_deg": 0}, anim_behavior="hourglass_flip_180"),
            make_layer("hourglass_glass_bulbs", "Upper & Lower Blown-Glass Bulbs (12.props.last-hourglass p02)", cut_path("12.props.last-hourglass", 2), "hourglass_glass", 8, {"x": 0.71, "y": 0.50, "scale": 0.76, "rot_deg": 0}, anim_behavior="hourglass_flip_180"),
            make_layer("hourglass_sand_stage1", "Sand Level 1 — Full Upper Bulb (p03)", cut_path("12.props.last-hourglass", 3), "sand_stage", 9, {"x": 0.71, "y": 0.42, "scale": 0.52, "rot_deg": 0}, anim_behavior="sand_drain_top"),
            make_layer("hourglass_sand_stage4", "Sand Level 4 — Mid Transfer (p06)", cut_path("12.props.last-hourglass", 6), "sand_stage", 10, {"x": 0.71, "y": 0.52, "scale": 0.52, "rot_deg": 0}, anim_behavior="sand_stream_mid"),
            make_layer("hourglass_sand_stage6", "Sand Level 6 — Lower Cone Mound (p08)", cut_path("12.props.last-hourglass", 8), "sand_stage", 11, {"x": 0.71, "y": 0.61, "scale": 0.52, "rot_deg": 0}, anim_behavior="sand_fill_bottom"),
            make_layer("hourglass_falling_stream", "Falling Crystalline Sand Stream (p09)", cut_path("12.props.last-hourglass", 9), "sand_stream", 12, {"x": 0.71, "y": 0.52, "scale": 0.42, "rot_deg": 0}, anim_behavior="sand_shimmer"),
            make_layer("hand_turning_hourglass", "Poet's Hand Gripping & Flipping Hourglass (12.props.hand-hourglass p01)", cut_path("12.props.hand-hourglass", 1), "actor_hand", 13, {"x": 0.79, "y": 0.48, "scale": 0.58, "rot_deg": -15}, anim_behavior="hand_flip_gesture"),
        ],
    })

    # =========================================================================
    # 4. putting_on_the_hands_weave (Weave P04 Multi-Beat Sequence)
    # =========================================================================
    assemblies.append({
        "id": "putting_on_the_hands_weave",
        "number": 4,
        "title": "4. Putting On the Hands — Weave P04 Brad-Snap Assembly Sequence",
        "poem": "Weave Passage P04 / Poem 04 — Attaching the Spare Hands",
        "category": "character_assembly_sequence",
        "sound_fx_preset": "brad_snap",
        "summary": "4-beat interactive sequence where the kneeling Poet starts with bare forearm stumps (exposed brass grommets), presses his left wrist stump onto Spare Hand A on the stone ledge (SNAP!), then uses his newly attached left hand to pick up Spare Hand B and snap it into his right sleeve cuff as the 1969 archive citizen rises behind the ledge.",
        "beats": [
            {"beat": 1, "t_range": [0.00, 0.25], "label": "Beat 1: Kneeling w/ Bare Forearm Stumps · Both Hands on Ledge"},
            {"beat": 2, "t_range": [0.25, 0.50], "label": "Beat 2: Left Stump Presses Onto Hand A → BRAD SNAP! (Cuff-Tuck)"},
            {"beat": 3, "t_range": [0.50, 0.75], "label": "Beat 3: Left Hand Picks Up Hand B & Carries to Right Wrist → BRAD SNAP!"},
            {"beat": 4, "t_range": [0.75, 1.00], "label": "Beat 4: Both Hands Flex & Rise · 1969 Archive Citizen Emerges"},
        ],
        "layers": [
            make_layer("weave_sky_1969", "1969 Archive Sky Backdrop", "weave/p04_hands/archive/sky1969.jpg", "bg_sky", 1, {"x": 0.50, "y": 0.45, "scale": 1.00, "rot_deg": 0}),
            make_layer("weave_citizen_1969", "1969 Archive Citizen Rising Behind Ledge", "weave/p04_hands/archive/citizen/0285.jpg", "archive_citizen", 2, {"x": 0.68, "y": 0.46, "scale": 0.62, "rot_deg": 0}, anim_behavior="citizen_rise_beat4"),
            make_layer("weave_plate", "P04 Painted Stage Plate", "weave/p04_hands/set/plate.jpg", "stage_plate", 3, {"x": 0.50, "y": 0.50, "scale": 1.00, "rot_deg": 0, "alpha": 0.55}),
            make_layer("weave_ledge", "Foreground Stone Ledge Cutout", "weave/p04_hands/set/ledge.png", "foreground_ledge", 4, {"x": 0.50, "y": 0.74, "scale": 1.00, "rot_deg": 0}),
            make_layer("kneel_foot_heel_up", "Kneeling Rear Foot (`foot.R.heel_up`)", v2_part_path("poet.red_black_sunglasses", "foot.R.heel_up.png"), "kneel_foot", 5, {"x": 0.34, "y": 0.72, "scale": 0.42, "rot_deg": 18}),
            make_layer("kneel_foot_toe_up", "Planted Front Foot (`foot.R.toe_up`)", v2_part_path("poet.red_black_sunglasses", "foot.R.toe_up.png"), "kneel_foot", 6, {"x": 0.48, "y": 0.73, "scale": 0.42, "rot_deg": -8}),
            make_layer("poet_torso_kneel", "Poet Tracksuit Torso Leaning Toward Ledge", ts_path("01_torso_front"), "actor_torso", 7, {"x": 0.42, "y": 0.48, "scale": 0.48, "rot_deg": 18}),
            make_layer("poet_head_kneel", "Poet Head Looking Down at Hands", ts_path("21_head_front_blank"), "actor_head", 8, {"x": 0.45, "y": 0.31, "scale": 0.30, "rot_deg": 16}),
            make_layer("stump_forearm_R", "Right Forearm Stump w/ Brass Grommet Socket (10_forearm_R)", ts_path("10_forearm_R"), "forearm_stump", 9, {"x": 0.36, "y": 0.54, "scale": 0.38, "rot_deg": 24}, anim_behavior="stump_R_await_snap"),
            make_layer("spare_hand_B", "Spare Right Hand B (`hand_open.png` — Picked Up in Beat 3)", "weave/p04_hands/assets/parts/hand_open.png", "spare_hand", 10, {"x": 0.57, "y": 0.70, "scale": 0.26, "rot_deg": 65}, anim_behavior="hand_B_pickup_and_snap"),
            make_layer("spare_hand_A", "Spare Left Hand A (`15_hand_relaxed_L` — Snapped in Beat 2)", ts_path("15_hand_relaxed_L"), "spare_hand", 11, {"x": 0.48, "y": 0.69, "scale": 0.24, "rot_deg": -40}, anim_behavior="hand_A_snap_into_cuff"),
            make_layer("stump_forearm_L", "Left Forearm Cuff Pressing Down (`08_forearm_L` — Cuff Over Hand)", ts_path("08_forearm_L"), "forearm_cuff", 12, {"x": 0.47, "y": 0.54, "scale": 0.38, "rot_deg": -28}, anim_behavior="stump_L_press_and_carry"),
        ],
    })

    # =========================================================================
    # 5. throwing_tambourine_rose_window (Poem 02 & 03)
    # =========================================================================
    assemblies.append({
        "id": "throwing_tambourine_rose_window",
        "number": 5,
        "title": "5. Throwing the Tambourine Through the Rose Window + Shatter",
        "poem": "Poems 02 & 03 — Tambourine Flight & Gothic Rose Window Shatter",
        "category": "action_prop_sequence",
        "sound_fx_preset": "tambourine_jingle_shatter",
        "summary": "Full windup, foot-plant (`heel_up` -> `flat` -> `toe_up`), release (`hand.grip` -> `hand.open`), spinning parabolic flight of the tambourine with 8 independent brass jingles (`02.props.tambourine`), and explosive impact through the center aperture of the Gothic Rose Window (`03.props.rose-window` + `03.props.tambourine-broken`).",
        "layers": [
            make_layer("rose_window_frame", "Gothic Stone Rose Window Tracery w/ Center Aperture (03.props.rose-window p01)", cut_path("03.props.rose-window", 1), "portal_target", 1, {"x": 0.76, "y": 0.42, "scale": 0.88, "rot_deg": 0}),
            make_layer("rose_petal_1", "Stained-Glass Petal Insert N (03.props.rose-window p02)", cut_path("03.props.rose-window", 2), "glass_petal", 2, {"x": 0.76, "y": 0.28, "scale": 0.36, "rot_deg": 0}, anim_behavior="shatter_burst_petal"),
            make_layer("rose_petal_2", "Stained-Glass Petal Insert E (03.props.rose-window p04)", cut_path("03.props.rose-window", 4), "glass_petal", 3, {"x": 0.85, "y": 0.42, "scale": 0.36, "rot_deg": 45}, anim_behavior="shatter_burst_petal"),
            make_layer("rose_petal_3", "Stained-Glass Petal Insert S (03.props.rose-window p06)", cut_path("03.props.rose-window", 6), "glass_petal", 4, {"x": 0.76, "y": 0.56, "scale": 0.36, "rot_deg": 90}, anim_behavior="shatter_burst_petal"),
            make_layer("thrower_torso", "Poet Throw Windup & Release Torso", ts_path("01_torso_front"), "actor_torso", 5, {"x": 0.22, "y": 0.52, "scale": 0.46, "rot_deg": -12}, anim_behavior="thrower_torso_whip"),
            make_layer("thrower_foot_front", "Planted Front Foot (`foot.R.flat`)", v2_part_path("poet.red_black_sunglasses", "foot.R.flat.png"), "actor_foot", 6, {"x": 0.27, "y": 0.78, "scale": 0.42, "rot_deg": 0}),
            make_layer("thrower_foot_rear", "Pivoting Rear Push-Off Foot (`foot.R.toe_up`)", v2_part_path("poet.red_black_sunglasses", "foot.R.toe_up.png"), "actor_foot", 7, {"x": 0.16, "y": 0.78, "scale": 0.42, "rot_deg": -22}),
            make_layer("thrower_hand_grip", "Windup Grip Hand (`hand.R.grip.palm`)", v2_part_path("poet.red_black_sunglasses", "hand.R.grip.palm.png"), "actor_hand", 8, {"x": 0.29, "y": 0.44, "scale": 0.32, "rot_deg": -25}),
            make_layer("thrower_hand_open", "Release Open Hand (`hand.R.open.palm`)", v2_part_path("poet.red_black_sunglasses", "hand.R.open.palm.png"), "actor_hand", 9, {"x": 0.33, "y": 0.40, "scale": 0.32, "rot_deg": 15}),
            make_layer("tambourine_trail", "Parabolic Spin Motion Trail (02.props.tambourine p11)", cut_path("02.props.tambourine", 11), "fx_trail", 10, {"x": 0.50, "y": 0.36, "scale": 0.62, "rot_deg": -18}, anim_behavior="tambourine_arc_trail"),
            make_layer("tambourine_whole", "Spinning Wood & Parchment Tambourine (02.props.tambourine p01)", cut_path("02.props.tambourine", 1), "projectile", 11, {"x": 0.52, "y": 0.34, "scale": 0.46, "rot_deg": 0}, anim_behavior="tambourine_parabolic_flight"),
            make_layer("tambourine_jingle_1", "Brass Zil Jingle Disc 1 (02.props.tambourine p03)", cut_path("02.props.tambourine", 3), "jingle_disc", 12, {"x": 0.55, "y": 0.31, "scale": 0.22, "rot_deg": 0}, anim_behavior="jingle_orbit"),
            make_layer("tambourine_shatter_rim", "Shattered Tambourine Rim Burst (03.props.tambourine-broken p01)", cut_path("03.props.tambourine-broken", 1), "shatter_piece", 13, {"x": 0.76, "y": 0.42, "scale": 0.56, "rot_deg": 25}, anim_behavior="shatter_on_impact"),
            make_layer("tambourine_shatter_jingles", "Flying Brass Jingles & Splinters (03.props.tambourine-broken p05)", cut_path("03.props.tambourine-broken", 5), "shatter_piece", 14, {"x": 0.80, "y": 0.38, "scale": 0.48, "rot_deg": -40}, anim_behavior="shatter_on_impact"),
        ],
    })

    # =========================================================================
    # 6. phone_booth_walk_and_call (Poem 02 & 09)
    # =========================================================================
    assemblies.append({
        "id": "phone_booth_walk_and_call",
        "number": 6,
        "title": "6. Walking Up to the Phone Booth + Talking on the Phone (Two-Shot Lip-Sync)",
        "poem": "Poems 02 & 09 — Ringing Payphone, Booth Entry & Two-Shot Conversation",
        "category": "acting_sequence",
        "sound_fx_preset": "phone_ring_and_voice",
        "summary": "4-beat narrative sequence: (1) Payphone rings inside the glass Phone Booth with expanding acoustic ring waves (`02.props.mirror-phone-rings`); (2) Poet walks up (`heel_up` -> `flat` -> `toe_up`), folds open the booth door (`09.props.phonebooth`), and steps inside behind the glazing; (3) Lifts detached receiver (`09.props.phones-chair`) with dynamic coiled cord; (4) Split-screen Two-Shot conversation with Mother/Muse featuring live 7-phoneme lip-sync (`rest`, `open_A`, `open_O`, `smile`).",
        "phoneme_cycle": [
            {"id": "rest", "file": ts_path("27_mouth_rest"), "label": "M / B / P (Closed Rest)"},
            {"id": "open_A", "file": ts_path("30_mouth_open_A"), "label": "AH / AI (Wide Open A)"},
            {"id": "open_O", "file": ts_path("29_mouth_open_O"), "label": "OH / OO (Rounded O)"},
            {"id": "smile", "file": ts_path("28_mouth_smile"), "label": "EE / S / V (Spread Smile)"},
        ],
        "layers": [
            make_layer("booth_back_wall", "Phone Booth Back Panel & Payphone Box (09.props.phonebooth p02)", cut_path("09.props.phonebooth", 2), "booth_back", 1, {"x": 0.34, "y": 0.52, "scale": 0.88, "rot_deg": 0}),
            make_layer("payphone_cradle", "Wall Payphone / Rotary Body (09.props.phones-chair p01)", cut_path("09.props.phones-chair", 1), "phone_base", 2, {"x": 0.37, "y": 0.48, "scale": 0.44, "rot_deg": 0}),
            make_layer("poet_inside_booth", "Poet Walking Up & Stepping Inside Booth (01_torso_front)", ts_path("01_torso_front"), "actor_core", 3, {"x": 0.31, "y": 0.52, "scale": 0.46, "rot_deg": 0}, anim_behavior="walk_into_booth"),
            make_layer("poet_head_talking", "Poet Head w/ Live Phoneme Lip-Sync (21_head_front_blank)", ts_path("21_head_front_blank"), "actor_head", 4, {"x": 0.31, "y": 0.34, "scale": 0.30, "rot_deg": -4}, anim_behavior="lip_sync_head"),
            make_layer("poet_mouth_phoneme", "Active Mouth Phoneme Card (29_mouth_open_O)", ts_path("29_mouth_open_O"), "actor_mouth", 5, {"x": 0.31, "y": 0.36, "scale": 0.11, "rot_deg": 0}, anim_behavior="phoneme_swap"),
            make_layer("phone_handset_receiver", "Detached Handset Receiver Held to Ear (09.props.phones-chair p03)", cut_path("09.props.phones-chair", 3), "handset", 6, {"x": 0.35, "y": 0.36, "scale": 0.32, "rot_deg": -28}, anim_behavior="receiver_lift_to_ear"),
            make_layer("phone_coiled_cord", "Dynamic Coiled Telephone Cord (09.props.phones-chair p05)", cut_path("09.props.phones-chair", 5), "cord_spring", 7, {"x": 0.36, "y": 0.44, "scale": 0.36, "rot_deg": 12}, anim_behavior="cord_stretch"),
            make_layer("booth_folding_door", "Bi-Fold Glass Booth Door (09.props.phonebooth p04)", cut_path("09.props.phonebooth", 4), "booth_door", 8, {"x": 0.27, "y": 0.52, "scale": 0.84, "rot_deg": 0}, anim_behavior="door_fold_open"),
            make_layer("booth_front_frame", "Phone Booth Outer Frame & TELEPHONE Header (09.props.phonebooth p01)", cut_path("09.props.phonebooth", 1), "booth_front", 9, {"x": 0.34, "y": 0.52, "scale": 0.90, "rot_deg": 0}),
            make_layer("acoustic_ring_waves", "Expanding Telephone Ring Waves (02.props.mirror-phone-rings p01)", cut_path("02.props.mirror-phone-rings", 1), "fx_ring", 10, {"x": 0.37, "y": 0.36, "scale": 0.58, "rot_deg": 0}, anim_behavior="ring_wave_pulse"),
            make_layer("mother_chair_twoshot", "Two-Shot Call Partner: Mother Seated by Phone (09.props.phones-chair p08)", cut_path("09.props.phones-chair", 8), "twoshot_furniture", 11, {"x": 0.76, "y": 0.60, "scale": 0.64, "rot_deg": 0}),
            make_layer("mother_torso_twoshot", "Mother in Cardigan Answering Call (body.front.torso)", v2_part_path("woman.mother_cardigan", "body.front.torso.png"), "twoshot_actor", 12, {"x": 0.76, "y": 0.50, "scale": 0.50, "rot_deg": 0}, anim_behavior="talk_bob_passenger"),
            make_layer("mother_head_twoshot", "Mother Head Nodding & Listening (head.front)", v2_part_path("woman.mother_cardigan", "head.front.png"), "twoshot_head", 13, {"x": 0.76, "y": 0.34, "scale": 0.34, "rot_deg": 4}),
        ],
    })

    # =========================================================================
    # 7. dj_booth_speakers_and_club_extras (Poem 07 & 08)
    # =========================================================================
    assemblies.append({
        "id": "dj_booth_speakers_and_club_extras",
        "number": 7,
        "title": "7. DJ Equipment, Pulsing Speakers/VU Meter & Club Extras Dancing",
        "poem": "Poems 07 & 08 — Cyber DJ Booth, Turntables & Club Ensemble",
        "category": "ensemble_stage",
        "sound_fx_preset": "dj_beat_and_scratch",
        "summary": "Interactive club stage where Cyber DJ scratches dual spinning vinyl platters (`07.props.dj-decks`), slides 8 mixer fader knobs, and cues headphones while speaker woofer cones (`07.props.speakers-vu`) pulse between normal and bass-thump states, the red VU needle pivots to the beat, and background Club Extras (`club_dress`, `club_jacket`, `club_shirt`) dance.",
        "layers": [
            make_layer("club_extra_dress", "Club Extra 1 — Sequin Dress Dancer (08.cast.club_dress.body p01)", cut_path("08.cast.club_dress.body", 1), "club_extra", 1, {"x": 0.18, "y": 0.54, "scale": 0.62, "rot_deg": 0}, anim_behavior="club_dancer_bounce"),
            make_layer("club_extra_jacket", "Club Extra 2 — Club Jacket Dancer (08.cast.club_jacket.body p01)", cut_path("08.cast.club_jacket.body", 1), "club_extra", 2, {"x": 0.82, "y": 0.54, "scale": 0.64, "rot_deg": 0}, anim_behavior="club_dancer_sway"),
            make_layer("club_extra_shirt", "Club Extra 3 — Silk Shirt Dancer (08.cast.club_shirt.body p01)", cut_path("08.cast.club_shirt.body", 1), "club_extra", 3, {"x": 0.68, "y": 0.52, "scale": 0.58, "rot_deg": 0}, anim_behavior="club_dancer_bounce"),
            make_layer("speaker_tower_L", "Left Bass Speaker Cabinet & Grille (07.props.speakers-vu p01)", cut_path("07.props.speakers-vu", 1), "speaker_box", 4, {"x": 0.12, "y": 0.56, "scale": 0.76, "rot_deg": 0}),
            make_layer("woofer_cone_L", "Pulsing Sub-Woofer Cone L (07.props.speakers-vu p05)", cut_path("07.props.speakers-vu", 5), "woofer_pulse", 5, {"x": 0.12, "y": 0.60, "scale": 0.44, "rot_deg": 0}, anim_behavior="woofer_bass_thump"),
            make_layer("speaker_tower_R", "Right Bass Speaker Cabinet & Grille (07.props.speakers-vu p02)", cut_path("07.props.speakers-vu", 2), "speaker_box", 6, {"x": 0.88, "y": 0.56, "scale": 0.76, "rot_deg": 0}),
            make_layer("vu_meter_dial", "Analog VU Meter Dial & Pivoting Red Needle (07.props.speakers-vu p09)", cut_path("07.props.speakers-vu", 9), "vu_needle", 7, {"x": 0.88, "y": 0.34, "scale": 0.46, "rot_deg": 0}, anim_behavior="vu_needle_swing"),
            make_layer("dj_actor_torso", "Cyber DJ Torso Behind Decks (party.dj_cyber)", v2_part_path("party.dj_cyber", "body.front.torso.png"), "dj_actor", 8, {"x": 0.48, "y": 0.44, "scale": 0.54, "rot_deg": 0}, anim_behavior="dj_head_bob"),
            make_layer("dj_actor_head", "Cyber DJ Head w/ Headphones (party.dj_cyber)", v2_part_path("party.dj_cyber", "head.front.png"), "dj_actor", 9, {"x": 0.48, "y": 0.28, "scale": 0.36, "rot_deg": -6}, anim_behavior="dj_head_bob"),
            make_layer("dj_booth_console", "DJ Booth Console & Mixer Table (07.props.dj-decks p01)", cut_path("07.props.dj-decks", 1), "dj_console", 10, {"x": 0.48, "y": 0.62, "scale": 0.86, "rot_deg": 0}),
            make_layer("vinyl_platter_L", "Left Spinning Vinyl Record Platter (07.props.dj-decks p03)", cut_path("07.props.dj-decks", 3), "vinyl_spin", 11, {"x": 0.39, "y": 0.56, "scale": 0.38, "rot_deg": 0}, anim_behavior="spin_vinyl_scratch"),
            make_layer("vinyl_platter_R", "Right Spinning Vinyl Record Platter (07.props.dj-decks p04)", cut_path("07.props.dj-decks", 4), "vinyl_spin", 12, {"x": 0.57, "y": 0.56, "scale": 0.38, "rot_deg": 0}, anim_behavior="spin_wheel_cw"),
            make_layer("mixer_fader_knobs", "8 Sliding Crossfader & EQ Knobs (07.props.dj-decks p07)", cut_path("07.props.dj-decks", 7), "fader_slider", 13, {"x": 0.48, "y": 0.57, "scale": 0.34, "rot_deg": 0}, anim_behavior="fader_slide"),
            make_layer("dj_hand_scratch", "DJ Flat-Push Hand Scratching Vinyl (`hand.R.flat_push.palm`)", v2_part_path("poet.red_black_sunglasses", "hand.R.flat_push.palm.png"), "dj_hand", 14, {"x": 0.39, "y": 0.54, "scale": 0.28, "rot_deg": 90}, anim_behavior="hand_scratch_osc"),
        ],
    })

    # =========================================================================
    # 8. picking_up_the_flower_harvest (Poem 04 & 13)
    # =========================================================================
    assemblies.append({
        "id": "picking_up_the_flower_harvest",
        "number": 8,
        "title": "8. Mustard Seed Blooming + Picking Up the Flower + Becoming Harvest",
        "poem": "Poems 04 & 13 — Faith Blooms Puzzle & Becoming Harvest",
        "category": "botanical_transformation",
        "sound_fx_preset": "hourglass_sand",
        "summary": "Combines the 6 gilded wood puzzle pieces and blooming golden flowerheads of `04.props.faith-blooms` with the crouching Poet (`foot.R.heel_up` + `hand.R.pinch.palm`) plucking the flower and triggering the Poem 13 'Becoming Harvest' botanical transformation (`13.props.harvest` scarlet poppies & purple blossoms sprouting from hands, shoulders, and crown).",
        "layers": [
            make_layer("faith_puzzle_base", "Gilded Wood Puzzle Base Cards P1–P6 (04.props.faith-blooms p01)", cut_path("04.props.faith-blooms", 1), "puzzle_card", 1, {"x": 0.64, "y": 0.72, "scale": 0.68, "rot_deg": 0}),
            make_layer("mustard_seeds", "Golden Mustard Seeds & Roots (04.props.faith-blooms p08)", cut_path("04.props.faith-blooms", 8), "seed_stage", 2, {"x": 0.64, "y": 0.76, "scale": 0.44, "rot_deg": 0}),
            make_layer("flower_stem_green", "Rising Green Botanical Stem (04.props.faith-blooms p15)", cut_path("04.props.faith-blooms", 15), "stem_grow", 3, {"x": 0.64, "y": 0.60, "scale": 0.54, "rot_deg": 0}, anim_behavior="stem_rise_grow"),
            make_layer("flower_bloom_head", "Blooming Golden Flowerhead (04.props.faith-blooms p20)", cut_path("04.props.faith-blooms", 20), "bloom_head", 4, {"x": 0.64, "y": 0.46, "scale": 0.50, "rot_deg": 0}, anim_behavior="flower_bloom_open"),
            make_layer("poet_harvest_figure", "Poet Crouching / Reaching Figure (poet.13.action.harvest-parts p01)", cut_path("poet.13.action.harvest-parts", 1), "actor_core", 5, {"x": 0.36, "y": 0.54, "scale": 0.78, "rot_deg": 0}),
            make_layer("poet_crouch_foot_heel", "Crouched Balance Foot (`foot.R.heel_up`)", v2_part_path("poet.red_black_sunglasses", "foot.R.heel_up.png"), "actor_foot", 6, {"x": 0.32, "y": 0.78, "scale": 0.40, "rot_deg": 14}),
            make_layer("poet_pinch_hand", "Delicate Pinch Hand Plucking Stem (`hand.R.pinch.palm`)", v2_part_path("poet.red_black_sunglasses", "hand.R.pinch.palm.png"), "actor_hand", 7, {"x": 0.54, "y": 0.52, "scale": 0.30, "rot_deg": -12}, anim_behavior="hand_reach_pluck"),
            make_layer("harvest_poppy_shoulder_L", "Scarlet Poppy Cluster on Left Shoulder (13.props.harvest p01)", cut_path("13.props.harvest", 1), "harvest_bloom", 8, {"x": 0.42, "y": 0.38, "scale": 0.44, "rot_deg": 12}, anim_behavior="flower_bloom_open"),
            make_layer("harvest_poppy_shoulder_R", "Purple Blossom Cluster on Right Shoulder (13.props.harvest p05)", cut_path("13.props.harvest", 5), "harvest_bloom", 9, {"x": 0.29, "y": 0.39, "scale": 0.44, "rot_deg": -15}, anim_behavior="flower_bloom_open"),
            make_layer("harvest_crown_bloom", "Botanical Crown Garland (13.props.harvest p09)", cut_path("13.props.harvest", 9), "harvest_bloom", 10, {"x": 0.36, "y": 0.24, "scale": 0.46, "rot_deg": 0}, anim_behavior="flower_bloom_open"),
            make_layer("harvest_hand_bouquet", "Blooming Hand Bouquet (13.props.harvest p14)", cut_path("13.props.harvest", 14), "harvest_bloom", 11, {"x": 0.56, "y": 0.48, "scale": 0.42, "rot_deg": 18}, anim_behavior="flower_bloom_open"),
        ],
    })

    # =========================================================================
    # 9. angel_and_raven_wings_flight (Poem 04 & 08)
    # =========================================================================
    assemblies.append({
        "id": "angel_and_raven_wings_flight",
        "number": 9,
        "title": "9. Articulated Angel Wings (4-State Cycle) & Raven Wings + Feather Foley",
        "poem": "Poems 04 & 08 — Winged Guardian Angel & Ravens on Charred Stumps",
        "category": "wing_articulation",
        "sound_fx_preset": "wing_whoosh",
        "summary": "Demonstrates true shoulder-blade socket pinning for the 4 mirrored wing pairs of `08.cast.angel.wings` (`FOLDED`, `HALF-OPEN`, `FULLY-OPEN`, `DOWNSTROKE` drawn behind `08.cast.angel.body`), alongside the wingless raven bodies and independent flapping left/right wings perched on charred stumps (`04.props.ravens-stumps`).",
        "wing_states": [
            {"id": "folded", "label": "State 1: Folded Rest (p01 / p02)"},
            {"id": "half_open", "label": "State 2: Half-Open Lift (p05 / p06)"},
            {"id": "fully_open", "label": "State 3: Fully-Open Apex Span (p09 / p10)"},
            {"id": "downstroke", "label": "State 4: Power Downstroke Whoosh (p13 / p14)"},
        ],
        "layers": [
            make_layer("angel_wing_L_open", "Angel Left Wing — Shoulder-Blade Socket L (08.cast.angel.wings p01)", cut_path("08.cast.angel.wings", 1), "wing_L", 1, {"x": 0.25, "y": 0.42, "scale": 0.82, "rot_deg": 0}, pivot_nx=0.85, pivot_ny=0.45, anim_behavior="flap_wing_L"),
            make_layer("angel_wing_R_open", "Angel Right Wing — Shoulder-Blade Socket R (08.cast.angel.wings p02)", cut_path("08.cast.angel.wings", 2), "wing_R", 2, {"x": 0.47, "y": 0.42, "scale": 0.82, "rot_deg": 0}, pivot_nx=0.15, pivot_ny=0.45, anim_behavior="flap_wing_R"),
            make_layer("angel_wing_alt_pair", "Angel Downstroke Wing Pair (08.cast.angel.wings p05)", cut_path("08.cast.angel.wings", 5), "wing_alt", 3, {"x": 0.36, "y": 0.40, "scale": 0.78, "rot_deg": 0}, anim_behavior="flap_wing_swap"),
            make_layer("angel_body_core", "Guardian Angel Robed Figure (08.cast.angel.body p01 — In Front of Wings)", cut_path("08.cast.angel.body", 1), "angel_body", 4, {"x": 0.36, "y": 0.54, "scale": 0.82, "rot_deg": 0}, anim_behavior="angel_hover"),
            make_layer("charred_stump_base", "Charred Nevermore Tree Stump (04.props.ravens-stumps p09)", cut_path("04.props.ravens-stumps", 9), "stump_prop", 5, {"x": 0.76, "y": 0.68, "scale": 0.66, "rot_deg": 0}),
            make_layer("raven_wing_far", "Raven Independent Far Wing (04.props.ravens-stumps p05)", cut_path("04.props.ravens-stumps", 5), "raven_wing", 6, {"x": 0.73, "y": 0.44, "scale": 0.48, "rot_deg": -15}, anim_behavior="flap_wing_L"),
            make_layer("raven_body_core", "Wingless Raven Body Perched on Stump (04.props.ravens-stumps p01)", cut_path("04.props.ravens-stumps", 1), "raven_body", 7, {"x": 0.76, "y": 0.50, "scale": 0.52, "rot_deg": 0}),
            make_layer("raven_wing_near", "Raven Independent Near Wing (04.props.ravens-stumps p06)", cut_path("04.props.ravens-stumps", 6), "raven_wing", 8, {"x": 0.79, "y": 0.44, "scale": 0.48, "rot_deg": 15}, anim_behavior="flap_wing_R"),
        ],
    })

    # =========================================================================
    # 10. tv_window_door_portals (Poem 01, 02, 03, 06, 09)
    # =========================================================================
    assemblies.append({
        "id": "tv_window_door_portals",
        "number": 10,
        "title": "10. TVs, Windows, Doors & Atlantis Gate as Portals into Other Worlds",
        "poem": "Poems 01, 02, 03, 06 & 09 — Multi-World Portal Apertures",
        "category": "portal_worlds",
        "sound_fx_preset": "ocean_waves",
        "summary": "5 switchable Portal Ensembles where live HTML5 archive video (`weave/archive/*.mp4`) and parallax Halfworld plates render inside the masked aperture of (1) the Flat-Screen TV (`01.props.room`), (2) the 1990s Childhood Window with parting curtains (`02.set.living_room_1990s`), (3) the High-Rise Steel Sash Window (`01.props.window`), (4) the Hinged Trapdoor & Chapel Doors (`01.props.trapdoor`, `03.set.chapel_side_doors`), and (5) the Atlantis Gate (`06.set.atlantis_gate`) with inverted pool reflection.",
        "portal_presets": [
            {"id": "tv_screen_portal", "label": "1. Flat-Screen TV Portal (`01.props.room` + Live Archive Video)", "aperture_rect": [0.22, 0.28, 0.24, 0.22]},
            {"id": "living_room_window", "label": "2. Childhood Window + Parting Curtains (`02.set.living_room_1990s`)", "aperture_rect": [0.35, 0.20, 0.30, 0.36]},
            {"id": "steel_sash_window", "label": "3. High-Rise Steel Sash Window + Fire Escape (`01.props.window`)", "aperture_rect": [0.36, 0.18, 0.28, 0.42]},
            {"id": "chapel_and_trapdoor", "label": "4. Chapel Side Doors & Floor Trapdoor (`03.set.chapel_side_doors`)", "aperture_rect": [0.38, 0.24, 0.24, 0.46]},
            {"id": "atlantis_gate_pool", "label": "5. Atlantis Gate Portal + Crystal Tree Hall + Pool Reflection (`06.set.atlantis_gate`)", "aperture_rect": [0.34, 0.18, 0.32, 0.48]},
        ],
        "archive_videos": [
            "weave/archive/6bb6d333-facb-5c4e-b540-0c150f87833b.mp4",
            "weave/archive/da69b1ba-1eb8-5072-8cf7-19fc272eba0f.mp4",
            "weave/p04_hands/passage.mp4",
        ],
        "layers": [
            make_layer("other_world_crystal_hall", "Other World Inside Portal: Crystal Tree Hall (06.set.crystal_tree_hall p01)", cut_path("06.set.crystal_tree_hall", 1), "portal_interior_world", 1, {"x": 0.50, "y": 0.44, "scale": 0.86, "rot_deg": 0}, anim_behavior="parallax_inner_world"),
            make_layer("atlantis_pool_water", "Atlantis Reflecting Pool Water Surface (06.set.atlantis_gate p03)", cut_path("06.set.atlantis_gate", 3), "water_reflection", 2, {"x": 0.50, "y": 0.78, "scale": 0.92, "rot_deg": 0}, anim_behavior="wave_drift_1"),
            make_layer("atlantis_gate_arch", "Atlantis Gold/Marble Portal Arch Frame (06.set.atlantis_gate p01)", cut_path("06.set.atlantis_gate", 1), "portal_frame", 3, {"x": 0.50, "y": 0.48, "scale": 0.94, "rot_deg": 0}),
            make_layer("tv_dresser_frame", "Room Flat-Screen TV & Dresser Frame (01.props.room p01)", cut_path("01.props.room", 1), "portal_frame", 4, {"x": 0.22, "y": 0.58, "scale": 0.64, "rot_deg": 0}),
            make_layer("window_sash_frame", "High-Rise Steel Window Frame & Sliding Sash (01.props.window p01)", cut_path("01.props.window", 1), "portal_frame", 5, {"x": 0.78, "y": 0.44, "scale": 0.68, "rot_deg": 0}, anim_behavior="window_sash_slide"),
            make_layer("living_room_curtains", "1990s Window & Parting Curtains (02.set.living_room_1990s p02)", cut_path("02.set.living_room_1990s", 2), "portal_curtain", 6, {"x": 0.50, "y": 0.38, "scale": 0.76, "rot_deg": 0}, anim_behavior="curtain_part_open"),
            make_layer("chapel_side_door", "Gothic Chapel Hinged Portal Door (03.set.chapel_side_doors p01)", cut_path("03.set.chapel_side_doors", 1), "portal_door", 7, {"x": 0.16, "y": 0.50, "scale": 0.68, "rot_deg": 0}, anim_behavior="door_fold_open"),
            make_layer("floor_trapdoor", "Hinged Floor Trapdoor Portal (01.props.trapdoor p01)", cut_path("01.props.trapdoor", 1), "portal_door", 8, {"x": 0.80, "y": 0.76, "scale": 0.54, "rot_deg": 0}),
        ],
    })

    # =========================================================================
    # 11. water_worlds_and_boats_ensemble (Poem 03, 04, 11, 13, 14)
    # =========================================================================
    assemblies.append({
        "id": "water_worlds_and_boats_ensemble",
        "number": 11,
        "title": "11. Multi-Layer Water Dioramas: Nevermore Shore & Jupiter Boats",
        "poem": "Poems 03, 04, 11, 13 & 14 — Shore Wavefronts, Submerged Ankles & Planet Boats",
        "category": "water_diorama",
        "sound_fx_preset": "ocean_waves",
        "summary": "Thoughtfully layered water stage combining `04.set.shore_night` (`SKY`, `SEA`, 3 independent horizontal wavefront strips `WAVE.1`, `WAVE.2`, `WAVE.3`, falling ash layers, and shore trees) with `13.props.planet-boats` (`JUPITER`, 4 cratered moons, `BOAT_A` & `BOAT_B` with separate hulls, masts, sails, and rippled water reflections) and characters wading between wave layers with submerged ankle masking.",
        "layers": [
            make_layer("shore_sky_plate", "Night Sky Backdrop (04.set.shore_night p01)", cut_path("04.set.shore_night", 1), "sky_bg", 1, {"x": 0.50, "y": 0.34, "scale": 1.00, "rot_deg": 0}),
            make_layer("jupiter_planet_disc", "Giant Banded Jupiter Planet (13.props.planet-boats p01)", cut_path("13.props.planet-boats", 1), "celestial", 2, {"x": 0.72, "y": 0.28, "scale": 0.66, "rot_deg": 0}),
            make_layer("jupiter_moons", "4 Cratered Galilean Moons (13.props.planet-boats p03)", cut_path("13.props.planet-boats", 3), "celestial", 3, {"x": 0.54, "y": 0.22, "scale": 0.44, "rot_deg": 0}, anim_behavior="moon_orbit_drift"),
            make_layer("shore_sea_horizon", "Deep Sea Horizon Body (04.set.shore_night p02)", cut_path("04.set.shore_night", 2), "water_deep", 4, {"x": 0.50, "y": 0.58, "scale": 1.00, "rot_deg": 0}),
            make_layer("wave_strip_far", "Far Horizontal Wavefront Strip WAVE.1 (04.set.shore_night p03)", cut_path("04.set.shore_night", 3), "wave_layer", 5, {"x": 0.50, "y": 0.60, "scale": 1.02, "rot_deg": 0}, anim_behavior="wave_drift_1"),
            make_layer("boat_A_sails_hull", "Sailboat A — Heeled Hull, Mast & Sail (13.props.planet-boats p08)", cut_path("13.props.planet-boats", 8), "boat_rig", 6, {"x": 0.68, "y": 0.56, "scale": 0.58, "rot_deg": -6}, anim_behavior="boat_pitch_roll"),
            make_layer("boat_water_reflection", "Rippled Boat Reflection on Water (13.props.planet-boats p14)", cut_path("13.props.planet-boats", 14), "water_reflection", 7, {"x": 0.68, "y": 0.69, "scale": 0.54, "rot_deg": 0, "alpha": 0.65}, anim_behavior="wave_drift_2"),
            make_layer("wading_muse_figure", "Muse Wading in Shallows (Submerged Ankle Masking)", v2_part_path("woman.teal_dress", "body.front.torso.png"), "wading_actor", 8, {"x": 0.32, "y": 0.56, "scale": 0.54, "rot_deg": 0}),
            make_layer("wave_strip_mid", "Mid Horizontal Wavefront Strip WAVE.2 — Covers Ankles! (04.set.shore_night p04)", cut_path("04.set.shore_night", 4), "wave_layer", 9, {"x": 0.50, "y": 0.67, "scale": 1.04, "rot_deg": 0}, anim_behavior="wave_drift_2"),
            make_layer("boat_B_foreground", "Foreground Skiff Boat B (13.props.planet-boats p11)", cut_path("13.props.planet-boats", 11), "boat_rig", 10, {"x": 0.22, "y": 0.66, "scale": 0.52, "rot_deg": 4}, anim_behavior="boat_pitch_roll"),
            make_layer("wave_strip_near", "Foreground Surf Wavefront WAVE.3 (04.set.shore_night p05)", cut_path("04.set.shore_night", 5), "wave_layer", 11, {"x": 0.50, "y": 0.76, "scale": 1.06, "rot_deg": 0}, anim_behavior="wave_drift_3"),
            make_layer("shore_trees_ash", "Shore Silhouette Trees & Drifting Ash (04.set.shore_night p08)", cut_path("04.set.shore_night", 8), "foreground_frame", 12, {"x": 0.14, "y": 0.48, "scale": 0.76, "rot_deg": 0}),
        ],
    })

    # =========================================================================
    # 12. interior_decorator_reusable_sets (1990s Living Room, Mother's Room, Bistro Cafe)
    # =========================================================================
    assemblies.append({
        "id": "interior_decorator_reusable_sets",
        "number": 12,
        "title": "12. Interior Decorator & Reusable Set Ensembles (Living Room, Mother's Room, Cafe)",
        "poem": "Poems 02, 09 & 13 — Modular Production Design & Character Seating",
        "category": "interior_decorator",
        "sound_fx_preset": "brad_snap",
        "summary": "Interactive production-design sandbox combining `02.set.living_room_1990s`, `09.set.mother_living_room`, and `13.props.cafe` (tabletop, pedestal stem, 3-prong base, chairs, espresso cup & saucer, sofa back/cushion/arms, rug, and floor lamp with warm light cone). Drag any furniture piece, snap the bistro table or lamp together, and seat characters on the sofa or cafe chair!",
        "room_presets": [
            {"id": "bistro_cafe_13", "label": "1. Poem 13 Bistro Cafe & Sofa Ensemble (`13.props.cafe`)"},
            {"id": "living_room_1990s_02", "label": "2. Poem 02 1990s Family Living Room (`02.set.living_room_1990s`)"},
            {"id": "mother_living_room_09", "label": "3. Poem 09 Mother's Sanctum Living Room (`09.set.mother_living_room`)"},
        ],
        "layers": [
            make_layer("room_wall_shell", "1990s Living Room Wall & Baseboard Shell (02.set.living_room_1990s p01)", cut_path("02.set.living_room_1990s", 1), "room_shell", 1, {"x": 0.50, "y": 0.48, "scale": 0.96, "rot_deg": 0}),
            make_layer("mother_room_backdrop", "Mother's Framed Photographs & Wallpaper (09.set.mother_living_room p01)", cut_path("09.set.mother_living_room", 1), "room_decor", 2, {"x": 0.24, "y": 0.34, "scale": 0.62, "rot_deg": 0}),
            make_layer("cafe_woven_rug", "Patterned Floor Rug (13.props.cafe p11)", cut_path("13.props.cafe", 11), "floor_rug", 3, {"x": 0.50, "y": 0.78, "scale": 0.84, "rot_deg": 0}),
            make_layer("floor_lamp_base", "Floor Lamp Stand & Stem (13.props.cafe p12)", cut_path("13.props.cafe", 12), "lamp_rig", 4, {"x": 0.82, "y": 0.54, "scale": 0.72, "rot_deg": 0}),
            make_layer("floor_lamp_shade", "Warm Parchment Lamp Shade & Light Cone (13.props.cafe p13)", cut_path("13.props.cafe", 13), "lamp_rig", 5, {"x": 0.82, "y": 0.32, "scale": 0.52, "rot_deg": 0}, anim_behavior="beam_pulse"),
            make_layer("sofa_back_cushion", "Modular Sofa Backrest & Cushions (13.props.cafe p08)", cut_path("13.props.cafe", 8), "sofa_rig", 6, {"x": 0.28, "y": 0.60, "scale": 0.72, "rot_deg": 0}),
            make_layer("seated_poet_actor", "Poet Seated on Sofa / Chair (`pose.sitting_chair`)", "arena/parts/kit3/v2/cut/poet.red_black_sunglasses.replacements/pose.sitting_chair.png", "seated_actor", 7, {"x": 0.28, "y": 0.56, "scale": 0.56, "rot_deg": 0}),
            make_layer("sofa_arm_front", "Foreground Sofa Armrest Overlay (13.props.cafe p09)", cut_path("13.props.cafe", 9), "sofa_front", 8, {"x": 0.22, "y": 0.64, "scale": 0.54, "rot_deg": 0}),
            make_layer("cafe_chair_profile", "Bentwood Bistro Chair (13.props.cafe p04)", cut_path("13.props.cafe", 4), "chair_rig", 9, {"x": 0.68, "y": 0.64, "scale": 0.58, "rot_deg": 0}),
            make_layer("table_3prong_base", "Cast-Iron 3-Prong Table Base (13.props.cafe p03)", cut_path("13.props.cafe", 3), "table_rig", 10, {"x": 0.56, "y": 0.74, "scale": 0.46, "rot_deg": 0}),
            make_layer("table_pedestal_stem", "Cafe Table Pedestal Column (13.props.cafe p02)", cut_path("13.props.cafe", 2), "table_rig", 11, {"x": 0.56, "y": 0.64, "scale": 0.48, "rot_deg": 0}),
            make_layer("table_round_top", "Round Marble Bistro Tabletop (13.props.cafe p01)", cut_path("13.props.cafe", 1), "table_rig", 12, {"x": 0.56, "y": 0.54, "scale": 0.52, "rot_deg": 0}),
            make_layer("espresso_cup_saucer", "Porcelain Espresso Cup & Saucer on Table (13.props.cafe p06)", cut_path("13.props.cafe", 6), "table_prop", 13, {"x": 0.56, "y": 0.50, "scale": 0.26, "rot_deg": 0}),
        ],
    })

    # =========================================================================
    # 13. clouds_and_volumetric_light_rig (Poem 02, 04, 06, 11)
    # =========================================================================
    assemblies.append({
        "id": "clouds_and_volumetric_light_rig",
        "number": 13,
        "title": "13. Drifting Clouds, Moon Reach, Drowned Light & Fog Halo Rig",
        "poem": "Poems 02, 04, 06 & 11 — Atmospheric Cloud Parting & Volumetric God-Rays",
        "category": "atmospheric_fx",
        "sound_fx_preset": "ocean_waves",
        "summary": "Multi-plane sky and volumetric light rig combining `04.fx.moon-reach`, `06.fx.water-rainbow-clouds`, `02.hero.drowned-light`, and `11.fx.fog-halo`. Clouds drift apart at independent parallax speeds while volumetric moonbeams and fog haloes rotate and breathe.",
        "layers": [
            make_layer("moon_disc_core", "Full Luminous Moon Disc (04.fx.moon-reach p01)", cut_path("04.fx.moon-reach", 1), "celestial", 1, {"x": 0.50, "y": 0.28, "scale": 0.68, "rot_deg": 0}, anim_behavior="beam_pulse"),
            make_layer("fog_halo_ring", "Atmospheric Fog Halo Ring (11.fx.fog-halo p01)", cut_path("11.fx.fog-halo", 1), "fx_halo", 2, {"x": 0.50, "y": 0.32, "scale": 0.88, "rot_deg": 0}, anim_behavior="systole_ring_expand"),
            make_layer("drowned_light_rays", "Volumetric Drowned Light God-Rays (02.hero.drowned-light p01)", cut_path("02.hero.drowned-light", 1), "fx_rays", 3, {"x": 0.50, "y": 0.48, "scale": 0.92, "rot_deg": -8}, anim_behavior="ray_slow_sweep"),
            make_layer("rainbow_cloud_bank_L", "Parting Cloud Bank Left (06.fx.water-rainbow-clouds p01)", cut_path("06.fx.water-rainbow-clouds", 1), "cloud_layer", 4, {"x": 0.28, "y": 0.34, "scale": 0.74, "rot_deg": 0}, anim_behavior="cloud_part_left"),
            make_layer("rainbow_cloud_bank_R", "Parting Cloud Bank Right (06.fx.water-rainbow-clouds p02)", cut_path("06.fx.water-rainbow-clouds", 2), "cloud_layer", 5, {"x": 0.72, "y": 0.34, "scale": 0.74, "rot_deg": 0}, anim_behavior="cloud_part_right"),
            make_layer("rainbow_arc_prism", "Refracted Water Rainbow Arc (06.fx.water-rainbow-clouds p06)", cut_path("06.fx.water-rainbow-clouds", 6), "fx_prism", 6, {"x": 0.50, "y": 0.42, "scale": 0.82, "rot_deg": 0, "alpha": 0.78}),
            make_layer("moon_reach_hand", "Poet Silhouette Hand Reaching into Moonbeam (04.fx.moon-reach p05)", cut_path("04.fx.moon-reach", 5), "actor_reach", 7, {"x": 0.50, "y": 0.66, "scale": 0.64, "rot_deg": 0}, anim_behavior="hand_reach_pluck"),
        ],
    })

    # =========================================================================
    # 14. right_foot_right_hand_matrix (12-Action Trust Matrix)
    # =========================================================================
    trust_matrix_rows = [
        {
            "action_id": "walk_heel_strike",
            "title": "1. Walk Cycle — Heel-Strike Contact",
            "poem_context": "All Poems (Arena Stride t=0.00)",
            "foot_card": v2_part_path("poet.red_black_sunglasses", "foot.R.toe_up.png"),
            "foot_label": "foot.R.toe_up.png (Dorsiflexed +16° Heel Contact)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": v2_part_path("poet.red_black_sunglasses", "hand.R.relaxed.side.png") if os.path.exists(os.path.join(SHOTS_DIR, v2_part_path("poet.red_black_sunglasses", "hand.R.relaxed.side.png"))) else v2_part_path("poet.red_black_sunglasses", "hand.R.relaxed.back.png"),
            "hand_label": "hand.R.relaxed.back.png (Natural Counter-Swing)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "Shin clipped at y=1295 (0.843h) OVER boot shaft; Forearm clipped at y=1238 (0.806h) OVER wrist crease.",
        },
        {
            "action_id": "walk_flat_stance",
            "title": "2. Walk / Stand — Planted Flat Stance",
            "poem_context": "All Poems (Mid-Stance Weight Bearing)",
            "foot_card": v2_part_path("poet.red_black_sunglasses", "foot.R.flat.png"),
            "foot_label": "foot.R.flat.png (100% Floor Baseline Lock)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": ts_path("15_hand_relaxed_L"),
            "hand_label": "15_hand_relaxed_L.png (0.23x Torso Scale, Crease y=315)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "Sole pinned to floor_Y; boot pull-tab tucked behind ribbed jogger cuff.",
        },
        {
            "action_id": "walk_toe_pushoff",
            "title": "3. Walk / Run — Toe Push-Off Drive",
            "poem_context": "Poems 01–14 (Propulsion Phase t=0.38)",
            "foot_card": v2_part_path("poet.red_black_sunglasses", "foot.R.heel_up.png"),
            "foot_label": "foot.R.heel_up.png (Plantarflexed Heel-Raised Drive)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": v2_part_path("poet.red_black_sunglasses", "hand.R.fist.back.png"),
            "hand_label": "hand.R.fist.back.png (Sprint Drive Fist)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "Ball of foot pinned while heel lifts -24°; ankle tucked inside pant cuff.",
        },
        {
            "action_id": "deep_kneel_ledge",
            "title": "4. Deep Kneel on Ledge (Weave P04)",
            "poem_context": "Weave P04 / Poem 04 (Putting On the Hands)",
            "foot_card": v2_part_path("poet.red_black_sunglasses", "foot.R.heel_up.png"),
            "foot_label": "foot.R.heel_up.png (Tucked Under Kneeling Shin)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": "weave/p04_hands/assets/parts/hand_open.png",
            "hand_label": "hand_open.png (Brad-Snapped into Wrist Grommet)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "Bare forearm grommet (y=1320) snaps onto hand grommet (y=190), then tucks into cuff (y=1195).",
        },
        {
            "action_id": "crouch_pluck_flower",
            "title": "5. Crouch & Pluck Mustard Flower",
            "poem_context": "Poems 04 & 13 (Faith Blooms / Harvest)",
            "foot_card": v2_part_path("poet.red_black_sunglasses", "foot.R.threequarter.png"),
            "foot_label": "foot.R.threequarter.png (3/4 Planted Crouch Balance)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": v2_part_path("poet.red_black_sunglasses", "hand.R.pinch.palm.png"),
            "hand_label": "hand.R.pinch.palm.png (Precision Thumb-Index Stem Pinch)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "Crouch height compensated to 0.36 stage_H; pinch fingers align with flower stem.",
        },
        {
            "action_id": "motorcycle_peg_straddle",
            "title": "6. Motorcycle Footpeg Straddle & Throttle Grip",
            "poem_context": "Poems 10 & 11 (Night Motorcycle Ride)",
            "foot_card": ts_path("19_boot_front_L"),
            "foot_label": "19_boot_front_L.png (Chelsea Boot Locked on Footpeg)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": v2_part_path("poet.red_black_sunglasses", "hand.R.grip.back.png"),
            "hand_label": "hand.R.grip.back.png (Wrapped Around Handlebar Throttle)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "Near leg (z=10..12) in front of bike frame (z=6); far leg (z=1) behind frame.",
        },
        {
            "action_id": "waltz_threequarter_rise",
            "title": "7. Ballroom Waltz 3/4 Rise & Frame Hold",
            "poem_context": "Poems 01 & 14 (Vintage Party Couple)",
            "foot_card": v2_part_path("poet.red_black_sunglasses", "foot.R.threequarter.png"),
            "foot_label": "foot.R.threequarter.png (3/4 Ballroom Turn Alignment)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": v2_part_path("poet.red_black_sunglasses", "hand.R.cup.palm.png"),
            "hand_label": "hand.R.cup.palm.png (Gentle Partner Lead Hand Cup)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "3/4 foot matches 3/4 torso yaw; wrist tucked under suit/tracksuit cuff.",
        },
        {
            "action_id": "throw_tambourine_whip",
            "title": "8. Tambourine Windup & Release Whip",
            "poem_context": "Poems 02 & 03 (Rose Window Shatter)",
            "foot_card": v2_part_path("poet.red_black_sunglasses", "foot.R.flat.png"),
            "foot_label": "foot.R.flat.png (Braced Front Plant Foot)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": v2_part_path("poet.red_black_sunglasses", "hand.R.open.palm.png"),
            "hand_label": "hand.R.grip.palm -> hand.R.open.palm (Release Follow-Through)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "Swaps from grip.palm to open.palm at release apex (t=0.42).",
        },
        {
            "action_id": "hold_phone_receiver",
            "title": "9. Phone Booth Step-In & Receiver Hold",
            "poem_context": "Poems 02 & 09 (Phone Booth Call)",
            "foot_card": v2_part_path("poet.red_black_sunglasses", "foot.R.front.png"),
            "foot_label": "foot.R.front.png (Planted Front View Inside Booth)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": v2_part_path("poet.red_black_sunglasses", "hand.R.grip.palm.png"),
            "hand_label": "hand.R.grip.palm.png (Closed Around Payphone Handset)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "Forearm bends -95° upward to ear; cuff overlaps wrist crease cleanly.",
        },
        {
            "action_id": "dj_turntable_scratch",
            "title": "10. DJ Vinyl Platter Scratch & Crossfader",
            "poem_context": "Poems 07 & 08 (Cyber DJ Booth)",
            "foot_card": v2_part_path("poet.red_black_sunglasses", "foot.R.front.png"),
            "foot_label": "foot.R.front.png (Planted Behind DJ Booth)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": v2_part_path("poet.red_black_sunglasses", "hand.R.flat_push.palm.png"),
            "hand_label": "hand.R.flat_push.palm.png (Flat Fingers on Vinyl Grooves)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "Flat-push hand oscillates +-18° over spinning platter while fader hand pinches knob.",
        },
        {
            "action_id": "horizon_point_gesture",
            "title": "11. Horizon Callout & Directional Point",
            "poem_context": "Poems 05, 06 & 12 (Ancestors & Atlantis Gate)",
            "foot_card": v2_part_path("poet.red_black_sunglasses", "foot.R.threequarter.png"),
            "foot_label": "foot.R.threequarter.png (Angled Stance Toward Gate)",
            "shin_card": ts_path("12_shin_L"),
            "hand_card": v2_part_path("poet.red_black_sunglasses", "hand.R.point.back.png"),
            "hand_label": "hand.R.point.back.png (Extended Index Finger Point)",
            "forearm_card": ts_path("08_forearm_L"),
            "cuff_tuck_rule": "2.5D limb foreshortening scales arm length cos(theta_z) while boosting hand 1.18x.",
        },
        {
            "action_id": "v2_horizontal_hand_fix",
            "title": "12. Kit3/v2 Horizontal Hand (+90° Cuff-Tuck Fix)",
            "poem_context": "All 7 kit3/v2 Modular Rigs (Poems 01–14)",
            "foot_card": v2_part_path("poet.black_tshirt", "body.front.foot.L.png"),
            "foot_label": "body.front.foot.L.png (42×74 Vertical Foot Tucked Under Shin)",
            "shin_card": v2_part_path("poet.black_tshirt", "body.front.shin.L.png"),
            "hand_card": v2_part_path("poet.black_tshirt", "body.front.hand.L.png"),
            "hand_label": "body.front.hand.L.png (74×43 Horizontal -> Rotated +90° + R-Mirrored)",
            "forearm_card": v2_part_path("poet.black_tshirt", "body.front.farm.L.png"),
            "cuff_tuck_rule": "Rotates 74×43 horizontal hand +90° around (0.24w, 0.48h) and tucks behind 0.86h clipped forearm.",
        },
    ]

    # Verify all trust matrix asset files
    for row in trust_matrix_rows:
        for k in ("foot_card", "shin_card", "hand_card", "forearm_card"):
            meta = verify_asset(row[k])
            row[f"{k}_meta"] = meta

    assemblies.append({
        "id": "right_foot_right_hand_matrix",
        "number": 14,
        "title": "14. 'Right Foot & Right Hand for the Job' — 12-Action Interactive Trust Matrix",
        "poem": "All 14 Poems — Verified Limb-to-Extremity Pairing & Cuff-Tuck Audit",
        "category": "trust_matrix",
        "sound_fx_preset": "brad_snap",
        "summary": "Interactive 12-action verification matrix proving we have the exact right foot card (`flat`, `heel_up`, `toe_up`, `threequarter`, `front`, `boot_front`) and right hand card (`relaxed`, `open`, `grip`, `pinch`, `flat_push`, `cup`, `point`, `fist`) properly scaled, rotated, and cuff-tucked for every action in the film.",
        "trust_matrix_rows": trust_matrix_rows,
        "layers": [
            make_layer("matrix_shin_cuff", "Active Shin Cuff (`12_shin_L` Clipped at y=1295)", ts_path("12_shin_L"), "shin_cuff", 2, {"x": 0.28, "y": 0.44, "scale": 0.72, "rot_deg": 0}),
            make_layer("matrix_foot_card", "Selected Action Foot Card (Tucked Behind Shin Cuff)", v2_part_path("poet.red_black_sunglasses", "foot.R.heel_up.png"), "foot_extremity", 1, {"x": 0.28, "y": 0.68, "scale": 0.52, "rot_deg": 0}),
            make_layer("matrix_forearm_cuff", "Active Forearm Cuff (`08_forearm_L` Clipped at y=1238)", ts_path("08_forearm_L"), "forearm_cuff", 4, {"x": 0.72, "y": 0.42, "scale": 0.72, "rot_deg": 0}),
            make_layer("matrix_hand_card", "Selected Action Hand Card (Tucked Behind Forearm Cuff)", v2_part_path("poet.red_black_sunglasses", "hand.R.pinch.palm.png"), "hand_extremity", 3, {"x": 0.72, "y": 0.66, "scale": 0.46, "rot_deg": 0}),
        ],
    })

    # Verify all layers and archive videos across all 14 assemblies
    missing = []
    total_layers = 0
    for asm in assemblies:
        for lyr in asm.get("layers", []):
            total_layers += 1
            if not lyr.get("exists", False):
                missing.append((asm["id"], lyr["id"], lyr["file"]))
        for vid in asm.get("archive_videos", []):
            vmeta = verify_asset(vid)
            if not vmeta["exists"]:
                missing.append((asm["id"], "video", vid))
        for row in asm.get("trust_matrix_rows", []):
            for k in ("foot_card", "shin_card", "hand_card", "forearm_card"):
                if not row[f"{k}_meta"]["exists"]:
                    missing.append((asm["id"], row["action_id"], row[k]))

    catalog = {
        "version": "2.5.0-some-assembly-required-toybox",
        "generated_by": "shots/arena/parts/kit3/build_assemblies_catalog.py",
        "description": "WYGWYL 14 Playable Compound Prop Rigs, Multi-Beat Action Sequences, Portal Worlds, Water Dioramas, Interior Decorator Sets & 12-Action Foot/Hand Trust Matrix",
        "stats": {
            "total_assemblies": len(assemblies),
            "total_interactive_layers": total_layers,
            "total_trust_matrix_actions": len(trust_matrix_rows),
            "missing_asset_files": len(missing),
            "sound_fx_presets": [
                "brad_snap",
                "car_engine_roll",
                "motorcycle_rev",
                "heartbeat_lubdub",
                "hourglass_sand",
                "tambourine_jingle_shatter",
                "phone_ring_and_voice",
                "dj_beat_and_scratch",
                "wing_whoosh",
                "ocean_waves",
            ],
        },
        "assemblies": assemblies,
        "assemblies_by_id": {a["id"]: a for a in assemblies},
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"[OK] Wrote {OUT_PATH}")
    print(f"     Assemblies           : {len(assemblies)}")
    print(f"     Interactive layers   : {total_layers}")
    print(f"     Trust matrix actions : {len(trust_matrix_rows)}")
    print(f"     Missing asset files  : {len(missing)}")
    if missing:
        for m in missing[:10]:
            print("     [ERROR] Missing:", m)
        sys.exit(1)


if __name__ == "__main__":
    main()
