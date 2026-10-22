#!/usr/bin/env python3
"""
Builds the unified WYGWYL Periodic Atlas & Multiplane Stage Manifest
(`shots/arena/parts/kit3/release_v2/wygwyl_atlas_manifest.json`)
combining:
  - All 365 unique sheets + 6,265 cut-out RGBA pieces from v2.0-poem-kits
  - All 31 pre-cut Poet Black/Red Tracksuit RGBA components with calibrated brass pivot coordinates
  - All 14 Poems, 80 Scenes, and 252 Shots from shots/poems/breakdown/01.json..14.json
  - Automatic multiplane stage layout (P5 -> P0) for every scene using the real cut-out RGBA pieces
"""

import os
import re
import glob
import json

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots"
REL_V2 = os.path.join(ROOT, "arena/parts/kit3/release_v2")
CAT_PATH = os.path.join(REL_V2, "release_catalog.json")
BREAKDOWN_DIR = os.path.join(ROOT, "poems/breakdown")
OUT_MANIFEST = os.path.join(REL_V2, "wygwyl_atlas_manifest.json")

ROMAN = [
    "", "I", "II", "III", "IV", "V", "VI", "VII",
    "VIII", "IX", "X", "XI", "XII", "XIII", "XIV"
]

# Exact calibrated brass pivot coordinates (in native component image pixels) for all 31 Tracksuit parts
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


def classify_sheet_type(sheet):
    sub = sheet.get("subfolder", "")
    kind = sheet.get("kind", "")
    sid = sheet.get("id", "")
    if sub == "05_PAINTED_EFFECTS" or kind in ("fx", "painted_fx") or ".fx." in sid:
        return "fx"
    if sub == "04_SETS_AND_BUILDINGS":
        if kind in ("hero", "hero-continuation") or ".hero." in sid:
            return "hero"
        return "location"
    if sub == "03_PROPS" or kind == "props" or ".props." in sid:
        return "prop"
    if sub == "02_ACTIONS_AND_POSES" or kind in ("main_poses", "main_pose", "action_parts", "action", "main_pose_reference", "pose_reference"):
        return "pose"
    return "character"


def human_title_from_id(sid):
    s = re.sub(r"^\d{2}\.", "", sid)
    s = s.replace(".", " · ").replace("_", " ").replace("-", " ")
    return s.upper()


def select_best_parts_for_sheet(sheet, role_filter=None, min_area=1200):
    parts = sheet.get("parts", [])
    if role_filter:
        cand = [p for p in parts if p.get("role") == role_filter and p.get("area_px", 0) >= min_area]
        if cand:
            return cand
    cand = [p for p in parts if p.get("area_px", 0) >= min_area]
    return cand if cand else parts


def filter_clean_pivots(part, sheet_type):
    """Keep only high-confidence circular brass pivots on character/pose/prop parts."""
    pivs = part.get("pivots", [])
    if sheet_type in ("hero", "location", "fx"):
        return []
    # Cap at 14 pivots per part (e.g. a full assembled pose figure has ~10-12 joint grommets; an individual limb has 1-4)
    clean = [p for p in pivs if 3.0 <= p.get("r", 5.0) <= 18.0]
    return clean[:12]


def main():
    cat = json.load(open(CAT_PATH))
    packs_root = os.path.join(ROOT, "kits", "packs")
    all_pack_pngs = {}
    for fn in glob.glob(os.path.join(packs_root, "poem_*", "*", "*.png")):
        all_pack_pngs[os.path.basename(fn)] = os.path.relpath(fn, ROOT)

    # Clean up pivots on sheet parts and map sheet_rel to tracked kits/packs paths
    total_clean_pivots = 0
    for s in cat["sheets"]:
        stype = classify_sheet_type(s)
        s["asset_type"] = stype
        fname = os.path.basename(s.get("original_file", f"{s['id']}.png"))
        pnum0 = (s.get("poems") or [1])[0]
        cand_rel = f"kits/packs/poem_{pnum0:02d}/{s.get('subfolder', '')}/{fname}"
        if os.path.exists(os.path.join(ROOT, cand_rel)):
            s["sheet_rel"] = cand_rel
        elif fname in all_pack_pngs:
            s["sheet_rel"] = all_pack_pngs[fname]
        for p in s.get("parts", []):
            p["pivots"] = filter_clean_pivots(p, stype)
            p["sheet_file"] = s["sheet_rel"]
            total_clean_pivots += len(p["pivots"])

    # Apply calibrated pivots and map tracksuit_components to tracked kits/packs/poet_tracksuit_v1/
    for tc in cat.get("tracksuit_components", []):
        cid = tc["comp_id"]
        tracked_tc = f"kits/packs/poet_tracksuit_v1/{cid}.png"
        if os.path.exists(os.path.join(ROOT, tracked_tc)):
            tc["file"] = tracked_tc
        if cid in TRACKSUIT_CALIBRATED_PIVOTS:
            tc["pivots"] = TRACKSUIT_CALIBRATED_PIVOTS[cid]
        total_clean_pivots += len(tc.get("pivots", []))
        vb = tc.get("visible_bbox", [0, 0, tc["width"], tc["height"]])
        if len(vb) == 4 and vb[2] > vb[0] and vb[3] > vb[1] and (vb[0] + vb[2] > tc["width"] or vb[1] + vb[3] > tc["height"]):
            tc["crop_bbox"] = [vb[0], vb[1], vb[2] - vb[0], vb[3] - vb[1]]
        else:
            tc["crop_bbox"] = vb

    # Load all 14 poem breakdowns
    breakdowns = {}
    for fn in sorted(glob.glob(os.path.join(BREAKDOWN_DIR, "[0-1][0-9].json"))):
        d = json.load(open(fn))
        pnum = int(d["num"])
        breakdowns[pnum] = d

    sheets_by_poem = {i: [] for i in range(1, 15)}
    for s in cat["sheets"]:
        for pnum in s.get("poems", []):
            sheets_by_poem[pnum].append(s)

    asset_scenes = {}
    asset_perfs = {}

    def record_use(aid, scene_id, perf=None):
        asset_scenes.setdefault(aid, [])
        if scene_id not in asset_scenes[aid]:
            asset_scenes[aid].append(scene_id)
        if perf:
            asset_perfs.setdefault(aid, []).append(perf)

    scenes_out = []
    for pnum in range(1, 15):
        bd = breakdowns.get(pnum, {})
        ptitle = bd.get("title", f"Poem {pnum:02d}")
        p_sheets = sheets_by_poem.get(pnum, [])

        p_sets = [s for s in p_sheets if s["asset_type"] in ("hero", "location")]
        p_props = [s for s in p_sheets if s["asset_type"] == "prop"]
        p_fx = [s for s in p_sheets if s["asset_type"] == "fx"]
        p_poses = [s for s in p_sheets if s["asset_type"] == "pose"]
        p_chars = [s for s in p_sheets if s["asset_type"] == "character"]

        # IMPORTANT: Always select POET's main-poses sheet for actor_poet!
        poet_main_pose_sheet = next(
            (s for s in p_poses if "poet" in s["id"].lower() and ("main-poses" in s["id"] or "main_pose" in s.get("kind", ""))),
            None,
        )
        if not poet_main_pose_sheet:
            poet_main_pose_sheet = next(
                (s for s in p_poses + p_chars if "poet" in s["id"].lower() and ("main-poses" in s["id"] or "action" in s["id"] or "master" in s["id"])),
                p_poses[0] if p_poses else (p_chars[0] if p_chars else None),
            )

        poet_core_sheet = next(
            (s for s in p_chars if "poet" in s["id"].lower() and ("compact-core" in s["id"] or "body.front" in s["id"] or "master" in s["id"])),
            p_chars[0] if p_chars else None,
        )

        raw_scenes = bd.get("scenes", [])
        for s_idx, sc in enumerate(raw_scenes):
            sc_num_id = sc["id"]
            sc_code = f"P{pnum:02d}-S{s_idx + 1:02d}"
            shots = sc.get("shots", [])
            first_shot = shots[0] if shots else {}
            target_set_id = first_shot.get("set", "")

            # 1. Match set / hero kit sheet
            matched_set_sheets = []
            for s in p_sets:
                if (
                    target_set_id
                    and (
                        target_set_id in s["id"]
                        or any(target_set_id in cov for cov in s.get("covered_source_ids", []))
                        or any(tok in s["id"] for tok in target_set_id.split("_") if len(tok) > 3)
                    )
                ):
                    matched_set_sheets.append(s)
            if not matched_set_sheets and p_sets:
                matched_set_sheets = [p_sets[s_idx % len(p_sets)]]

            # 2. Match prop sheets
            scene_prop_ids = []
            for sh in shots:
                for pr in sh.get("props", []):
                    if isinstance(pr, dict) and pr.get("id"):
                        scene_prop_ids.append(pr["id"])
                    elif isinstance(pr, str):
                        scene_prop_ids.append(pr)
            matched_prop_sheets = []
            for s in p_props:
                if any(pid.split("_")[0] in s["id"] or pid.split("_")[0] in s.get("prompt", "").lower() for pid in scene_prop_ids):
                    matched_prop_sheets.append(s)
            if not matched_prop_sheets and p_props:
                matched_prop_sheets = [p_props[s_idx % len(p_props)]]

            # 3. Match FX sheet
            matched_fx_sheets = p_fx[:1] if p_fx else []

            # 4. Supporting character sheets (prefer master / main-poses / paired-choreography so we get full figures, not headless torso parts!)
            scene_bodies = [b for sh in shots for b in sh.get("bodies", [])]
            matched_supp_sheets = []
            seen_supp_roles = set()
            for b in scene_bodies:
                role_key = (b.get("role") or "").strip().upper()
                if not role_key or role_key == "POET" or role_key in seen_supp_roles:
                    continue
                seen_supp_roles.add(role_key)
                role_str = (b.get("role", "") + " " + b.get("costume", "") + " " + b.get("puppet", "")).lower()
                # Search for assembled/master/pose sheet for this supporting character first
                best_s = None
                for s in p_poses + p_chars:
                    if s in (poet_main_pose_sheet, poet_core_sheet) or s in matched_supp_sheets:
                        continue
                    sid_low = s["id"].lower()
                    if any(k in role_str and k in sid_low for k in ["ex", "vintage", "party", "mother", "young", "family", "muse", "dj", "ancest", "crowd", "woman", "double", "soul"]):
                        if any(tag in sid_low for tag in ["master", "main-poses", "main_pose", "paired", "dance"]):
                            best_s = s
                            break
                        if not best_s:
                            best_s = s
                if best_s:
                    matched_supp_sheets.append(best_s)

            stage_layers = []
            required_assets = []

            def add_req(aid):
                if aid and aid not in required_assets:
                    required_assets.append(aid)

            # Layer P5 / P4: Set & Architecture
            if matched_set_sheets:
                set_sheet = matched_set_sheets[0]
                add_req(set_sheet["id"])
                record_use(set_sheet["id"], sc_code, {"scene": sc_code, "poem": pnum, "role": "SET / LOCATION", "set": target_set_id})
                set_parts = select_best_parts_for_sheet(set_sheet, role_filter="working_part", min_area=1800)
                by_area = sorted(set_parts, key=lambda p: p["area_px"], reverse=True)
                if len(by_area) >= 1:
                    bg_part = by_area[0]
                    stage_layers.append({
                        "instance": f"set_bg_{bg_part['part_index']}",
                        "plane": "P5",
                        "z": 4.0,
                        "sheet_id": set_sheet["id"],
                        "part_id": bg_part["id"],
                        "label": bg_part["label"],
                        "file": bg_part["file"],
                        "width": bg_part["width"],
                        "height": bg_part["height"],
                        "x": 0.50,
                        "y": 0.80,
                        "scale": 0.84,
                        "alpha": 0.96,
                        "blend": "source-over",
                        "role": "set_backdrop",
                    })
                arch_anchors = [(0.22, 0.86, 0.56), (0.78, 0.86, 0.56), (0.50, 0.93, 0.65), (0.14, 0.72, 0.45)]
                for a_idx, ap in enumerate(by_area[1:5]):
                    ax, ay, asc = arch_anchors[a_idx % len(arch_anchors)]
                    if ap["width"] > ap["height"] * 2.3:
                        ax, ay, asc = 0.50, 0.95, 0.88
                    stage_layers.append({
                        "instance": f"set_arch_{ap['part_index']}",
                        "plane": "P4",
                        "z": 2.5,
                        "sheet_id": set_sheet["id"],
                        "part_id": ap["id"],
                        "label": ap["label"],
                        "file": ap["file"],
                        "width": ap["width"],
                        "height": ap["height"],
                        "x": ax,
                        "y": ay,
                        "scale": asc,
                        "alpha": 1.0,
                        "blend": "source-over",
                        "role": "set_architecture",
                    })

            # Layer P3: Props
            if matched_prop_sheets:
                prop_sheet = matched_prop_sheets[0]
                add_req(prop_sheet["id"])
                record_use(prop_sheet["id"], sc_code, {"scene": sc_code, "poem": pnum, "role": "STAGE PROPS", "props": scene_prop_ids[:4]})
                prop_parts = select_best_parts_for_sheet(prop_sheet, role_filter="working_part", min_area=1400)
                prop_xs = [0.16, 0.84, 0.65]
                for p_idx, pp in enumerate(prop_parts[:3]):
                    stage_layers.append({
                        "instance": f"prop_{pp['part_index']}",
                        "plane": "P3",
                        "z": 1.4,
                        "sheet_id": prop_sheet["id"],
                        "part_id": pp["id"],
                        "label": pp["label"],
                        "file": pp["file"],
                        "width": pp["width"],
                        "height": pp["height"],
                        "x": prop_xs[p_idx % len(prop_xs)],
                        "y": 0.87 - 0.04 * p_idx,
                        "scale": 0.34,
                        "alpha": 1.0,
                        "blend": "source-over",
                        "role": "prop",
                    })

            # Layer P2: Hero Poet (from poet.XX.main-poses!)
            if poet_main_pose_sheet:
                add_req(poet_main_pose_sheet["id"])
                # Pick tall full-figure pose cutouts
                pose_parts = [
                    p for p in select_best_parts_for_sheet(poet_main_pose_sheet, min_area=6000)
                    if p["height"] >= 160
                ]
                if not pose_parts:
                    pose_parts = select_best_parts_for_sheet(poet_main_pose_sheet, min_area=3000)
                if pose_parts:
                    chosen_pose = pose_parts[s_idx % len(pose_parts)]
                    poet_body = next((b for b in scene_bodies if b.get("role") == "POET"), {})
                    px = poet_body.get("position", {}).get("x", 0.38)
                    px = max(0.24, min(0.76, float(px)))
                    record_use(poet_main_pose_sheet["id"], sc_code, {
                        "scene": sc_code,
                        "poem": pnum,
                        "role": "POET POSE",
                        "pose": poet_body.get("pose", "stand"),
                        "action": poet_body.get("action", sc.get("movement", "")),
                    })
                    stage_layers.append({
                        "instance": "actor_poet",
                        "plane": "P2",
                        "z": 1.0,
                        "sheet_id": poet_main_pose_sheet["id"],
                        "part_id": chosen_pose["id"],
                        "label": f"POET · {poet_body.get('pose', 'pose').upper()}",
                        "file": chosen_pose["file"],
                        "width": chosen_pose["width"],
                        "height": chosen_pose["height"],
                        "pivots": chosen_pose.get("pivots", []),
                        "x": px,
                        "y": 0.92,
                        "scale": 0.58,
                        "alpha": 1.0,
                        "blend": "source-over",
                        "role": "character_hero",
                        "rig_mode": "cutout_or_articulated",
                        "costume": "black_tshirt" if pnum <= 3 else "tracksuit",
                        "action": poet_body.get("action", ""),
                        "expression": poet_body.get("expression", "neutral"),
                    })

            if poet_core_sheet:
                add_req(poet_core_sheet["id"])
                record_use(poet_core_sheet["id"], sc_code, {
                    "scene": sc_code,
                    "poem": pnum,
                    "role": "POET CORE RIG",
                    "costume": "black_tshirt" if pnum <= 3 else "tracksuit",
                })

            if pnum >= 4:
                for tc_id in ["poet.tracksuit.01_torso_front", "poet.tracksuit.21_head_front_blank", "poet.tracksuit.31_sunglasses_front"]:
                    add_req(tc_id)
                    record_use(tc_id, sc_code, {"scene": sc_code, "poem": pnum, "role": "TRACKSUIT RIG COMPONENT"})

            # Supporting cast cutouts (pick tallest full-figure cutout from master/pose sheet)
            for sup_idx, sup_s in enumerate(matched_supp_sheets[:2]):
                add_req(sup_s["id"])
                record_use(sup_s["id"], sc_code, {"scene": sc_code, "poem": pnum, "role": "SUPPORTING CHARACTER"})
                sup_parts = sorted(
                    select_best_parts_for_sheet(sup_s, min_area=3500),
                    key=lambda p: p["height"],
                    reverse=True,
                )
                if sup_parts:
                    sp = sup_parts[s_idx % min(3, len(sup_parts))]
                    stage_layers.append({
                        "instance": f"actor_supp_{sup_idx + 1}",
                        "plane": "P3",
                        "z": 1.25,
                        "sheet_id": sup_s["id"],
                        "part_id": sp["id"],
                        "label": sp["label"],
                        "file": sp["file"],
                        "width": sp["width"],
                        "height": sp["height"],
                        "pivots": sp.get("pivots", []),
                        "x": 0.72 if sup_idx == 0 else 0.24,
                        "y": 0.88,
                        "scale": 0.48,
                        "alpha": 1.0,
                        "blend": "source-over",
                        "role": "character_supporting",
                    })

            # Layer P1 / P0: Painted FX cards
            if matched_fx_sheets:
                fx_sheet = matched_fx_sheets[0]
                add_req(fx_sheet["id"])
                record_use(fx_sheet["id"], sc_code, {"scene": sc_code, "poem": pnum, "role": "PAINTED FX"})
                fx_parts = select_best_parts_for_sheet(fx_sheet, role_filter="working_part", min_area=1200)
                # Prefer horizontal haze/light strips over tall vertical tower streaks for top overlay
                horiz_fx = [p for p in fx_parts if p["width"] >= p["height"]]
                chosen_fx = (horiz_fx if horiz_fx else fx_parts)[:2]
                for f_idx, fp in enumerate(chosen_fx):
                    stage_layers.append({
                        "instance": f"fx_{f_idx + 1}",
                        "plane": "P1" if f_idx == 0 else "P0",
                        "z": 0.5 if f_idx == 0 else 0.25,
                        "sheet_id": fx_sheet["id"],
                        "part_id": fp["id"],
                        "label": fp["label"],
                        "file": fp["file"],
                        "width": fp["width"],
                        "height": fp["height"],
                        "x": 0.35 + 0.32 * f_idx,
                        "y": 0.26 + 0.12 * f_idx,
                        "scale": 0.32,
                        "alpha": 0.76,
                        "blend": "source-over",
                        "role": "fx_overlay",
                    })

            part_lookup = {p["id"]: p for s in cat["sheets"] for p in s.get("parts", [])}
            for sl in stage_layers:
                p_ref = part_lookup.get(sl.get("part_id"))
                if p_ref:
                    sl["sheet_file"] = p_ref.get("sheet_file")
                    sl["bbox_sheet"] = p_ref.get("bbox_sheet")

            beats = []
            if sc.get("lines"):
                beats.append(f"VERSE: \"{sc['lines']}\"")
            if sc.get("treatment"):
                beats.append(f"TREATMENT: {sc['treatment']}")
            for sh in shots:
                beats.append(f"[{sh['id']} · {sh.get('framing', 'wide').upper()} / {sh.get('camera', 'eye').upper()}] {sh.get('action', '')}")

            scenes_out.append({
                "id": sc_code,
                "scene_num": sc_num_id,
                "title": f"{sc_num_id} · {sc.get('movement', ptitle)}",
                "movement": sc.get("movement", ""),
                "book": pnum,
                "bookTitle": ptitle,
                "seconds": sc.get("seconds", 12),
                "lines": sc.get("lines", ""),
                "treatment": sc.get("treatment", ""),
                "set_id": target_set_id,
                "shot_count": len(shots),
                "shots": shots,
                "assets": required_assets,
                "beats": beats,
                "stage_layers": stage_layers,
                "composePrompt": (
                    f"Assemble WYGWYL Scene {sc_code} ({sc_num_id} — {sc.get('movement', '')}) for Poem {pnum:02d} '{ptitle}' "
                    f"on the 7-plane cardboard stage (P6..P0). Set: {target_set_id}. "
                    f"Required kits: {', '.join(required_assets)}. Verse: {sc.get('lines', '')}"
                ),
                "exitState": f"Completed {sc_num_id} ({len(shots)} shots, {sc.get('seconds', 12)}s) -> transitions to next movement.",
            })

    assets_out = []
    for s in cat["sheets"]:
        aid = s["id"]
        poems = sorted(s.get("poems", []))
        sc_list = asset_scenes.get(aid, [])
        if not sc_list and poems:
            for pnum in poems:
                p_sc = [sc["id"] for sc in scenes_out if sc["book"] == pnum]
                if p_sc:
                    sc_list.extend(p_sc[:2])
        piv_count = sum(len(p.get("pivots", [])) for p in s.get("parts", []))
        assets_out.append({
            "id": aid,
            "name": human_title_from_id(aid),
            "type": s["asset_type"],
            "subfolder": s.get("subfolder", ""),
            "kind": s.get("kind", ""),
            "books": poems,
            "uses": max(len(sc_list), len(poems)),
            "scenes": sc_list,
            "sheet_file": s["sheet_rel"],
            "width": s.get("width", 1536),
            "height": s.get("height", 1024),
            "part_count": s.get("part_count", 0),
            "working_part_count": s.get("working_part_count", 0),
            "reference_part_count": s.get("reference_part_count", 0),
            "pivot_count": piv_count,
            "qa_notes": s.get("qa_notes", []),
            "prompt": s.get("prompt", ""),
            "perfs": asset_perfs.get(aid, []),
            "parts": s.get("parts", []),
        })

    for tc in cat.get("tracksuit_components", []):
        aid = tc["id"]
        sc_list = asset_scenes.get(aid, [sc["id"] for sc in scenes_out if sc["book"] >= 4][:6])
        assets_out.append({
            "id": aid,
            "name": f"TRACKSUIT · {tc['label'].upper()}",
            "type": "tracksuit",
            "subfolder": "Poet_Black_Red_Tracksuit_Individual_Parts_v1",
            "kind": tc.get("group", "Component"),
            "books": tc.get("poems", list(range(4, 15))),
            "uses": len(sc_list),
            "scenes": sc_list,
            "sheet_file": tc["file"],
            "width": tc["width"],
            "height": tc["height"],
            "visible_bbox": tc.get("crop_bbox"),
            "part_count": 1,
            "working_part_count": 1,
            "reference_part_count": 0,
            "pivot_count": len(tc.get("pivots", [])),
            "qa_notes": [f"Group: {tc.get('group', '')}", f"Calibrated brass pivots: {len(tc.get('pivots', []))}"],
            "prompt": tc.get("prompt", ""),
            "perfs": asset_perfs.get(aid, []),
            "parts": [{
                "id": aid,
                "part_index": 1,
                "label": tc["label"],
                "role": "working_part",
                "file": tc["file"],
                "bbox_sheet": tc.get("crop_bbox", [0, 0, tc["width"], tc["height"]]),
                "width": tc["width"],
                "height": tc["height"],
                "area_px": tc["width"] * tc["height"] // 3,
                "pivots": tc.get("pivots", []),
            }],
        })

    poems_meta = []
    for pnum in range(1, 15):
        bd = breakdowns.get(pnum, {})
        poems_meta.append({
            "book": pnum,
            "num": f"{pnum:02d}",
            "roman": ROMAN[pnum],
            "title": bd.get("title", f"Poem {pnum:02d}"),
            "style": bd.get("style", "cardboard cut-out"),
            "scene_count": sum(1 for sc in scenes_out if sc["book"] == pnum),
            "shot_count": sum(sc["shot_count"] for sc in scenes_out if sc["book"] == pnum),
            "kit_count": sum(1 for a in assets_out if pnum in a["books"]),
        })

    manifest = {
        "generated": "v2.0-poem-kits-cutout-atlas",
        "poemCount": 14,
        "assetCount": len(assets_out),
        "cutPieceCount": cat["total_cut_parts"],
        "workingPieceCount": cat["total_working_parts"],
        "pivotCount": total_clean_pivots,
        "sceneCount": len(scenes_out),
        "shotCount": sum(sc["shot_count"] for sc in scenes_out),
        "poems": poems_meta,
        "tracksuitRig": cat.get("tracksuit_components", []),
        "assets": assets_out,
        "scenes": scenes_out,
    }

    with open(OUT_MANIFEST, "w") as f:
        json.dump(manifest, f, separators=(",", ":"))

    print("=== WYGWYL ATLAS MANIFEST UPDATED ===")
    print(f"Master Assets:   {manifest['assetCount']}")
    print(f"Cut RGBA Pieces: {manifest['cutPieceCount']}")
    print(f"Clean Pivots:    {manifest['pivotCount']}")
    print(f"Staged Scenes:   {manifest['sceneCount']} ({manifest['shotCount']} shots)")


if __name__ == "__main__":
    main()
