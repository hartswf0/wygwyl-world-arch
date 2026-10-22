#!/usr/bin/env python3
"""
build_cards_atlas.py

Builds the complete periodic atlas database (shots/cards_data.json) for
WYGWYL Cards & Staging Environment, modeled on odyssey-halfworld/viewer/cards.html.

Extracts:
1. All Scenes (14 poems, each broken into choreographic movements/beats)
2. All Assets (Characters, Action Poses, Props, Sets, Effects)
3. Asset-to-Scene Requirements ("Shot Manifest" / "Needs Grid")
4. Sliced card references & brass brad pivot telemetry
"""

import os
import json
import glob
import re
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BREAKDOWN_DIR = os.path.join(ROOT, "shots", "poems", "breakdown")
PACKS_DIR = os.path.join(ROOT, "shots", "kits", "packs")
FILM_POEMS_FILE = os.path.join(ROOT, "shots", "film", "poems.json")
OUTPUT_FILE = os.path.join(ROOT, "shots", "cards_data.json")

# Map of District names for all 14 poems
DISTRICTS = {
    1: "Naraka Market",
    2: "The Overseer",
    3: "Mirror Thread Bay",
    4: "The Hollows",
    5: "Sub-level 0",
    6: "Neon Causeway",
    7: "The Gilded Spire",
    8: "Chamber of the Bell",
    9: "The Obsidian Shallows",
    10: "The Cloud Foundry",
    11: "The Echo Garden",
    12: "The Core / Memory Well",
    13: "Celestial Basin",
    14: "Aethelgard"
}

TYPE_COLORS = {
    "scene": "#e7a35a",
    "character": "#efe6da",
    "action_pose": "#f5b942",
    "prop": "#01acd4",
    "set_piece": "#9fe08a",
    "painted_effect": "#ff7b6b"
}

def make_symbol(name):
    """Generate 2-letter atomic symbol from name."""
    words = re.split(r'[\s\-_\.:]+', name.strip())
    words = [w for w in words if w and not w.isdigit()]
    if not words:
        return "El"
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).capitalize()
    w = words[0]
    return (w[:2] if len(w) >= 2 else w + "x").capitalize()

def load_film_poems():
    if os.path.exists(FILM_POEMS_FILE):
        try:
            with open(FILM_POEMS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []

def main():
    print("Building WYGWYL Cards & Staging Atlas Database...")
    film_poems = load_film_poems()
    film_map = {int(p.get("num", 0)): p for p in film_poems if "num" in p}
    
    scenes = []
    assets_dict = {}  # id -> asset
    
    # Process each of the 14 poems
    for p_num in range(1, 15):
        num_str = f"{p_num:02d}"
        bd_path = os.path.join(BREAKDOWN_DIR, f"{num_str}.json")
        pack_path = os.path.join(PACKS_DIR, f"poem_{num_str}")
        
        if not os.path.exists(bd_path):
            continue
            
        with open(bd_path) as f:
            bd = json.load(f)
            
        film_info = film_map.get(p_num, {})
        poem_title = bd.get("title", f"Poem {num_str}")
        district = DISTRICTS.get(p_num, "The City")
        tagline = film_info.get("tagline", "")
        
        # Load pack manifest & prompts if available
        manifest_path = os.path.join(pack_path, "manifest.json")
        prompts_path = os.path.join(pack_path, "prompts.json")
        manifest_sheets = []
        prompts_map = {}
        
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path) as mf:
                    manifest_sheets = json.load(mf).get("sheets", [])
            except Exception:
                pass
                
        if os.path.exists(prompts_path):
            try:
                with open(prompts_path) as pf:
                    p_list = json.load(pf)
                    for item in p_list:
                        if isinstance(item, dict) and "id" in item:
                            prompts_map[item["id"]] = item.get("generation_prompt", item.get("final_revision_prompt", ""))
            except Exception:
                pass
                
        # Register Sets as Assets
        for s in bd.get("sets", []):
            s_id = f"p{num_str}.set.{s['id']}"
            if s_id not in assets_dict:
                assets_dict[s_id] = {
                    "id": s_id,
                    "name": s["id"].replace("_", " ").title(),
                    "type": "set_piece",
                    "symbol": make_symbol(s["id"]),
                    "description": s.get("what", ""),
                    "poems": [p_num],
                    "uses": 1,
                    "scenes": [],
                    "prompt": f"Multiplane cardboard stage layer for {district}: {s.get('what', '')}",
                    "rel_sheet": f"shots/kits/packs/poem_{num_str}/04_SETS_AND_BUILDINGS/{num_str}.hero.severn.png"
                }
            else:
                if p_num not in assets_dict[s_id]["poems"]:
                    assets_dict[s_id]["poems"].append(p_num)
                assets_dict[s_id]["uses"] += 1

        # Register Pack Sheets as Assets
        for ms in manifest_sheets:
            sheet_id = ms.get("id", "")
            cat = ms.get("category", ms.get("kind", "prop"))
            rel_file = ms.get("file", "")
            
            type_label = "prop"
            if "character" in cat or "hero" in cat or "face" in sheet_id or "body" in sheet_id or "hands" in sheet_id:
                type_label = "character"
            elif "action" in cat or "poses" in sheet_id:
                type_label = "action_pose"
            elif "set" in cat or "building" in cat or "room" in sheet_id:
                type_label = "set_piece"
            elif "fx" in cat or "effect" in cat or "haze" in sheet_id:
                type_label = "painted_effect"
                
            clean_name = sheet_id.replace(f"{num_str}.", "").replace("_", " ").replace(".", " ").title()
            asset_full_id = f"p{num_str}.{sheet_id}"
            
            assets_dict[asset_full_id] = {
                "id": asset_full_id,
                "name": clean_name,
                "type": type_label,
                "symbol": make_symbol(clean_name),
                "description": f"Cardboard sheet for Poem {num_str} ({cat}): {sheet_id}",
                "poems": [p_num],
                "uses": 1,
                "scenes": [],
                "prompt": prompts_map.get(sheet_id, f"Artisan gouache cardboard puppet sheet for {sheet_id}"),
                "rel_sheet": f"shots/kits/packs/poem_{num_str}/{rel_file}",
                "sheet_bytes": ms.get("bytes", 0),
                "sha256": ms.get("sha256", "")
            }
            
        # Process Scenes / Movements
        for sc in bd.get("scenes", []):
            sc_id = sc.get("id", f"{num_str}.1")
            sc_num = sc_id.split(".")[-1]
            mov_name = sc.get("movement", f"Movement {sc_num}")
            secs = sc.get("seconds", 12)
            lines = sc.get("lines", "")
            treatment = sc.get("treatment", "")
            
            # Find required assets for this scene
            needed_assets = []
            for shot in sc.get("shots", []):
                set_id = f"p{num_str}.set.{shot.get('set', '')}"
                if set_id in assets_dict and set_id not in needed_assets:
                    needed_assets.append(set_id)
                    assets_dict[set_id]["scenes"].append(sc_id)
                    
                for body in shot.get("bodies", []):
                    puppet = body.get("puppet", "")
                    costume = body.get("costume", "")
                    char_asset_id = f"char.{puppet}.{costume}"
                    if char_asset_id not in assets_dict:
                        assets_dict[char_asset_id] = {
                            "id": char_asset_id,
                            "name": f"{puppet.title()} ({costume.replace('_', ' ')})",
                            "type": "character",
                            "symbol": make_symbol(puppet),
                            "description": f"Cardboard puppet body for {puppet} in {costume}",
                            "poems": [p_num],
                            "uses": 1,
                            "scenes": [sc_id],
                            "prompt": f"Cardboard jointed puppet {puppet} wearing {costume} with brass split-pin brad pivots",
                            "rel_sheet": f"shots/kits/packs/poem_{num_str}/01_CHARACTER_CORE/poet.black_tshirt.compact-core.png"
                        }
                    else:
                        if p_num not in assets_dict[char_asset_id]["poems"]:
                            assets_dict[char_asset_id]["poems"].append(p_num)
                        assets_dict[char_asset_id]["uses"] += 1
                        assets_dict[char_asset_id]["scenes"].append(sc_id)
                    if char_asset_id not in needed_assets:
                        needed_assets.append(char_asset_id)
                        
            # Link matching props from pack manifest
            for aid, a in assets_dict.items():
                if a["type"] == "prop" and p_num in a["poems"] and aid not in needed_assets:
                    needed_assets.append(aid)
                    a["scenes"].append(sc_id)
                    
            scene_item = {
                "id": f"SC_{sc_id.replace('.', '_')}",
                "scene_num": sc_id,
                "poem": p_num,
                "poem_num": num_str,
                "poem_title": poem_title,
                "district": district,
                "title": f"0{p_num}.{sc_num} {mov_name}",
                "movement": mov_name,
                "seconds": secs,
                "lines": lines,
                "treatment": treatment,
                "assets": needed_assets,
                "beats": [
                    f"Action: {treatment[:180]}...",
                    f"Spoken text ({secs}s): \"{lines[:140]}...\"",
                    f"Set staging: {district} multiplane card layer"
                ],
                "composePrompt": f"Scene {sc_id} staging in {district}: {treatment}\nSpoken: {lines}",
                "exitState": f"Transition to next movement in Poem {num_str} or crossfade to district sky."
            }
            scenes.append(scene_item)

    # Attach Tracksuit components
    tracksuit_dir = os.path.join(PACKS_DIR, "poet_tracksuit_v1", "01_COMPONENTS")
    if os.path.exists(tracksuit_dir):
        for comp in sorted(os.listdir(tracksuit_dir)):
            if comp.endswith(".png"):
                c_name = os.path.splitext(comp)[0].replace("_", " ").title()
                c_id = f"tracksuit.{comp}"
                assets_dict[c_id] = {
                    "id": c_id,
                    "name": c_name,
                    "type": "character",
                    "symbol": make_symbol(c_name),
                    "description": f"Adult Poet modular tracksuit cut component: {c_name}",
                    "poems": list(range(4, 15)),
                    "uses": 11,
                    "scenes": [],
                    "prompt": f"Modular cut card {c_name} with brass pivot tab for adult Poet puppet",
                    "rel_sheet": f"shots/kits/packs/poet_tracksuit_v1/01_COMPONENTS/{comp}",
                    "is_cut": True
                }

    # Format list
    assets_list = list(assets_dict.values())
    
    atlas = {
        "suite": "Where You Go When You Leave",
        "districts": DISTRICTS,
        "total_scenes": len(scenes),
        "total_assets": len(assets_list),
        "scenes": scenes,
        "assets": assets_list
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(atlas, f, indent=2)
        
    print(f"Generated {OUTPUT_FILE}: {len(scenes)} scenes, {len(assets_list)} assets across 14 poems.")

if __name__ == "__main__":
    main()
