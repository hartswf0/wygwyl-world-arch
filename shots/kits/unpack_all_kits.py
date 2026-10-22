#!/usr/bin/env python3
"""
unpack_all_kits.py

Extracts all 14 poem kits and the individual modular components kit from
POEM-KITS/*.zip into structured, git-friendly directories under shots/kits/packs/.

Why this structure:
1. GitHub 100MB Limit: 5 of the zip files are >100MB and cannot be committed directly to Git.
   Inside the zips, all individual PNGs, SVGs, and JSONs are <4MB.
2. Agent Usability: AI agents and web browsers cannot view or inspect assets locked
   inside .zip files. Unpacking them into standard directories gives every agent
   instant file access and allows web pages (production.html, kits.html, p01.html-p14.html)
   to render every sheet directly.
"""

import os
import zipfile
import json
import glob
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POEM_KITS_DIR = os.path.join(ROOT, "POEM-KITS")
PACKS_DEST = os.path.join(ROOT, "shots", "kits", "packs")

ZIP_MAPPING = {
    "Poem_01_Out_of_Life_All_Kits.zip": "poem_01",
    "Poem_02_Flashing_Lights_All_Kits.zip": "poem_02",
    "Poem_03_How_to_break_off_an_engagement_All_Kits.zip": "poem_03",
    "Poem_04_Nevermore_All_Kits.zip": "poem_04",
    "Poem_05_Bloodlines_All_Kits.zip": "poem_05",
    "Poem_06_Resurrecting_Atlantis_All_Kits.zip": "poem_06",
    "Poem_07_DJ_Turn_Me_Up_All_Kits.zip": "poem_07",
    "Poem_08_Newly_Single_All_Kits.zip": "poem_08",
    "Poem_09_Yet_Heard_All_Kits.zip": "poem_09",
    "Poem_10_Magic_Ride_All_Kits.zip": "poem_10",
    "Poem_11_New_Day_All_Kits.zip": "poem_11",
    "Poem_12_Reunion_All_Kits.zip": "poem_12",
    "Poem_13_How_to_Win_My_Heart_All_Kits.zip": "poem_13",
    "Poem_14_Hot_Minute_All_Kits.zip": "poem_14",
    "Poet_Black_Red_Tracksuit_Individual_Parts_v1.zip": "poet_tracksuit_v1",
    "Poet-GEMINI.zip": "poet_gemini_raw",
}

def unpack_kit(zip_filename, target_dir_name):
    zip_path = os.path.join(POEM_KITS_DIR, zip_filename)
    if not os.path.exists(zip_path):
        print(f"Skipping {zip_filename}: file not found.")
        return None

    target_dir = os.path.join(PACKS_DEST, target_dir_name)
    os.makedirs(target_dir, exist_ok=True)
    
    extracted_count = 0
    total_bytes = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Skip OS junk like __MACOSX and .DS_Store
            if "__MACOSX" in member.filename or ".DS_Store" in member.filename:
                continue
            
            # Strip the root folder name from the zip member path
            parts = member.filename.split("/", 1)
            rel_name = parts[1] if len(parts) > 1 and parts[1] else parts[0]
            if not rel_name:
                continue

            dest_file = os.path.join(target_dir, rel_name)
            if member.is_dir():
                os.makedirs(dest_file, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                with open(dest_file, "wb") as f:
                    f.write(zf.read(member.filename))
                extracted_count += 1
                total_bytes += member.file_size

    print(f"  [OK] {zip_filename} -> {target_dir_name}/ ({extracted_count} files, {total_bytes/(1024*1024):.1f} MB)")
    return {
        "kit_id": target_dir_name,
        "source_zip": zip_filename,
        "files_count": extracted_count,
        "total_bytes": total_bytes,
        "rel_path": os.path.relpath(target_dir, ROOT)
    }

def main():
    print("Unpacking Poem Kits for Agent Usability & Git Distribution...")
    os.makedirs(PACKS_DEST, exist_ok=True)
    
    results = []
    for zip_name, dest_name in ZIP_MAPPING.items():
        res = unpack_kit(zip_name, dest_name)
        if res:
            results.append(res)
            
    print(f"\nSuccessfully unpacked {len(results)} kits into {PACKS_DEST}")

if __name__ == "__main__":
    main()
