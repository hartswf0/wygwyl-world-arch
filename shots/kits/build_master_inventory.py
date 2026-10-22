#!/usr/bin/env python3
"""
build_master_inventory.py

Builds a consolidated index of all 14 poem kits, the modular tracksuit kit,
and source assets under shots/kits/packs/. Outputs shots/kits/packs/master_inventory.json.
"""

import os
import json
import glob
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKS_DIR = os.path.join(ROOT, "shots", "kits", "packs")

def inspect_pack(pack_dir):
    pack_name = os.path.basename(pack_dir)
    manifest_path = os.path.join(pack_dir, "manifest.json")
    prompts_path = os.path.join(pack_dir, "prompts.json")
    plan_path = os.path.join(pack_dir, "instance_plan.json")
    svg_guide = os.path.join(pack_dir, "Assembly_Guide.svg")
    
    meta = {
        "id": pack_name,
        "path": os.path.relpath(pack_dir, ROOT),
        "has_manifest": os.path.exists(manifest_path),
        "has_prompts": os.path.exists(prompts_path),
        "has_assembly_guide": os.path.exists(svg_guide),
        "has_instance_plan": os.path.exists(plan_path),
        "subfolders": {},
        "sheet_count": 0,
        "components_count": 0
    }
    
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path) as f:
                mf = json.load(f)
                meta["title"] = mf.get("title", "")
                meta["poem"] = mf.get("poem", "")
                meta["manifest_sheet_count"] = mf.get("sheet_count", 0)
                meta["poet_identity"] = mf.get("poet_identity", {})
                meta["sheets"] = mf.get("sheets", [])
        except Exception as e:
            meta["manifest_error"] = str(e)
            
    # Count images in subfolders
    for sub in sorted(os.listdir(pack_dir)):
        sub_path = os.path.join(pack_dir, sub)
        if os.path.isdir(sub_path):
            imgs = [f for f in os.listdir(sub_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            meta["subfolders"][sub] = {
                "count": len(imgs),
                "sample_files": imgs[:5]
            }
            if sub == "01_COMPONENTS":
                meta["components_count"] = len(imgs)
            else:
                meta["sheet_count"] += len(imgs)
                
    return meta

def main():
    print("Building master inventory for shots/kits/packs...")
    packs = sorted([d for d in glob.glob(os.path.join(PACKS_DIR, "*")) if os.path.isdir(d)])
    
    inventory = {
        "suite": "WYGWYL (Where You Go When You Leave)",
        "total_packs": len(packs),
        "packs": []
    }
    
    total_sheets = 0
    total_cut_components = 0
    
    for p in packs:
        meta = inspect_pack(p)
        inventory["packs"].append(meta)
        total_sheets += meta.get("sheet_count", 0)
        total_cut_components += meta.get("components_count", 0)
        print(f"  Indexed {meta['id']}: {meta.get('title', meta['id'])} ({meta['sheet_count']} sheets, {meta['components_count']} cut parts)")
        
    inventory["total_sheets"] = total_sheets
    inventory["total_cut_components"] = total_cut_components
    
    out_path = os.path.join(PACKS_DIR, "master_inventory.json")
    with open(out_path, "w") as f:
        json.dump(inventory, f, indent=2)
        
    print(f"\nSaved master inventory to {out_path} ({total_sheets} sheets, {total_cut_components} cut parts across {len(packs)} packs).")

if __name__ == "__main__":
    main()
