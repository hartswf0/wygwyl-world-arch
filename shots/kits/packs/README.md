# WYGWYL Poem Production Kits (01–14 & Modular Puppet Parts)

Welcome to the production kit asset repository for **Where You Go When You Leave (WYGWYL)**.

This directory contains the unpacked, git-friendly production kits for all 14 poems, the adult Poet modular tracksuit puppet (31 transparent components), and source reference assets.

---

## 1. Directory Structure

```text
shots/kits/packs/
├── master_inventory.json       # Consolidated index of all 16 packs, sheets, and cut parts
├── README.md                   # This specification guide
├── poet_tracksuit_v1/          # 31 transparent, single-card PNG parts for adult Poet
│   ├── 01_COMPONENTS/          # Sliced parts (torso, limbs, hands, boots, modular faces)
│   ├── 02_POSE_REFERENCES/     # Main-pose reference sheets
│   ├── 03_SOURCE_SHEETS/       # Source generation cards
│   ├── Component_Index.csv     # Pivot and dimension metadata for all 31 parts
│   ├── manifest.json           # Kit manifest
│   └── index.html              # Interactive visual component viewer
├── poem_01/                    # Out of Life (Naraka Market)
│   ├── 01_CHARACTER_CORE/      # Poet & Ex character cards
│   ├── 02_ACTIONS_AND_POSES/   # Dynamic action replacement poses
│   ├── 03_PROPS/               # Handheld props, room props, vape, poem paper
│   ├── 04_SETS_AND_BUILDINGS/  # Multiplane background, midground, foreground sets
│   ├── 05_PAINTED_EFFECTS/     # Haze, text projections, light leaks
│   ├── Assembly_Guide.svg      # Vector puppet assembly guide with pivot links
│   ├── manifest.json           # Sheet definitions, SHA-256 hashes, review status
│   ├── prompts.json            # Exact generation & revision prompts used
│   └── instance_plan.json      # Choreographic casting plan
├── poem_02/ ... poem_14/       # Complete production kits for poems 02 through 14
└── poet_gemini_raw/            # High-resolution concept art reference renders
```

---

## 2. GitHub Strategy & File Limits

### Why Not Push Monolithic `.zip` Files to Git?
- **GitHub 100 MB Limit**: GitHub strictly rejects any single file exceeding 100 MB (`GH001: Large files detected`). Five of the zip files (`Poem_07`, `Poem_08`, `Poem_13`, `Poem_14`, and `Poet-GEMINI`) are between 100.5 MB and 146.8 MB. Pushing them directly will fail and block the repository push.
- **Agent Usability**: When assets are zipped, AI agents and web browsers cannot load, inspect, or render them without first running decompression scripts.
- **Clean Git Tracking**: Unpacked into `shots/kits/packs/`, **no individual file exceeds 3.72 MB**. Every PNG, SVG, and JSON can be committed directly to Git, versioned, and served locally or via GitHack / GitHub Pages.

### Monolithic Zip Distribution via GitHub Releases
For developers or agents needing the offline raw `.zip` files:
```bash
# Upload all pristine zips to a GitHub Release (supports up to 2GB per asset):
gh release create v2.0-poem-kits POEM-KITS/*.zip --title "WYGWYL Poem Kits v2.0 Archives" --notes "Monolithic zip archives for all 14 poems."

# Download all zips on another machine:
gh release download v2.0-poem-kits --dir POEM-KITS/
```

---

## 3. How to Cut Apart Sheets into Modular Pieces

Each landscape sheet in `01_CHARACTER_CORE`, `02_ACTIONS_AND_POSES`, `03_PROPS`, and `04_SETS_AND_BUILDINGS` was generated with **"generous white gaps: every working part fully detached and nothing touches"**.

Use the automated Python slicer tool located at [shots/kits/slice_kit_sheets.py](file:///Users/gaia/Downloads/WYGWYL-WORLD-ARCH/shots/kits/slice_kit_sheets.py):

### Slicing a Single Sheet:
```bash
python3 shots/kits/slice_kit_sheets.py \
  shots/kits/packs/poem_01/03_PROPS/01.props.handheld.png \
  shots/kits/packs/poem_01/cut
```
This produces:
- Individual transparent alpha PNG cards (`part_01.png`, `part_02.png`, etc.)
- Automatic circular brass split-pin brad & grommet eyelet detection (`cx`, `cy`, `radius`, `color`)
- `catalog.json` describing bounding boxes and connection points.

### Slicing an Entire Poem Kit:
```bash
python3 shots/kits/slice_kit_sheets.py \
  shots/kits/packs/poem_01 \
  shots/kits/packs/poem_01/cut
```

---

## 4. Querying Kits Programmatically (Agent API)

Any AI agent can query all packs and assets using `master_inventory.json`:

```python
import json

with open("shots/kits/packs/master_inventory.json") as f:
    inventory = json.load(f)

# Find all props for Poem 04
p04 = next(p for p in inventory["packs"] if p["id"] == "poem_04")
props = p04["subfolders"].get("03_PROPS", {}).get("sample_files", [])
print("Poem 04 Props:", props)

# Access individual transparent components
tracksuit = next(p for p in inventory["packs"] if p["id"] == "poet_tracksuit_v1")
print(f"Modular Poet has {tracksuit['components_count']} transparent pieces ready to animate.")
```

---

## 5. Web Portals & Visual Inspection
- **Interactive Character Kits Explorer**: [shots/kits.html](file:///Users/gaia/Downloads/WYGWYL-WORLD-ARCH/shots/kits.html)
- **Master Production Bible**: [shots/production.html](file:///Users/gaia/Downloads/WYGWYL-WORLD-ARCH/shots/production.html)
- **Poem Production Bibles**: [shots/poems/p01.html](file:///Users/gaia/Downloads/WYGWYL-WORLD-ARCH/shots/poems/p01.html) through [shots/poems/p14.html](file:///Users/gaia/Downloads/WYGWYL-WORLD-ARCH/shots/poems/p14.html)
- **Tracksuit Component Viewer**: [shots/kits/packs/poet_tracksuit_v1/index.html](file:///Users/gaia/Downloads/WYGWYL-WORLD-ARCH/shots/kits/packs/poet_tracksuit_v1/index.html)
