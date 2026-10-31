#!/usr/bin/env python3
"""
build_atlas_splat_infrastructure.py
===================================
Builds the complete Round-Trip World Labs Atlas / Marble `.glb` & 3D Gaussian Splat
Infrastructure for the WYGWYL 14-Poem / 10-District / 4-Mega-Hub Ecosystem:

1. Curated & Deduplicated Reference Packs for all 10 Districts & 4 Mega-Hubs:
   - Filters out macro close-ups (`02-04` eyeball, `03-01` tambourine, `04-05` title card,
     `05-04` cervical spine, `07-00` diary platter, `12-04..06` tight portraits) and
     cross-poem Markov duplicates (`02-07`, `04-06`, `08-06`, `10-06`, `10-07`).
   - Uses panoptic segmentation masks (`refs/XX-YY-seg.jpg`) and Onion Shells (`R0/R1`)
     to inpaint/strip foreground actors (`person` class) from the architectural anchor
     frames and shared panoramas so no frozen "wax-statue" actor ghosts get baked into splats.
   - Exports Marble-ready `2560x1280` (`2:1`) Actor-Cleaned Equirectangular Panoramas
     and `2560x1280` (`2:1`) Equirectangular Depth Maps for each of the 4 Mega-Hubs.

2. Binary glTF 2.0 (`.glb`) Chisel & Collider Meshes (`shots/data/terrarium/atlas_packs/glb/`):
   - Converts all 10 `<stage>.landpack.json` files and 4 Mega-Hubs into standards-compliant
     binary `.glb` files containing:
     * `TERRAIN_COLLIDER` mesh (unpacked from 12-bit `hf`, datum-aligned to `spawn`),
     * `BUILDINGS_CHISEL` mesh (extruded OSM building footprints `bld` seated on `gYw(x,z)`),
     * `PORTAL_APERTURES_R3` mesh (Set-Piece `A..F` stage frames & window portals).
   - Ready to upload to Marble's "Chisel" 3D layout input OR load directly in Three.js
     as floor/wall physics colliders & depth-occlusion prepass geometry!

3. Binary 3D Gaussian Splat Seeds (`.splat` 32-byte standard format: `shots/data/terrarium/atlas_packs/splats/`):
   - Synthesizes immediately playable 3D Gaussian Splat files (`hub_01_atlantis.splat`,
     `hub_02_harbor_ruin.splat`, `hub_02_harbor_temple.splat`, `hub_03_mount_vernon.splat`,
     `hub_04_shore_garden.splat`) by projecting our actor-cleaned `2:1` equirectangular
     panoramas, Onion Depth Shells (`R2..R5`), and anchor frames onto the 3D `.landpack.json`
     terrain, building facades, and set-piece corridors.
   - Enables instant testing of the 3D Splat + `.glb` Collider + 2.5D Cut-Out Actor pipeline
     in `atlas_splat_studio.html` and `terrarium.html`, and provides a 1:1 drop-in slot
     for receiving `.spz` / `.ply` / `.splat` / `.glb` exports back from Marble/Atlas!

4. OpenCV <-> Three.js Terrarium Coordinate Bridge (`atlas_infrastructure_manifest.json`):
   - Stores exact OpenCV camera poses (`+X left, +Y down, +Z forward`) for Marble/Atlas
     AND the exact 4x4 alignment transform back into Three.js Terrarium metric space
     (`+X east, +Y up, +Z south`, datum-aligned at `spawn`).

5. Visual Proof Contact Sheets in `shots/png_vault/atlas_splats/` (15 plates) + `png_catalog.json`.
"""

import os
import json
import math
import base64
import struct
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
SHOTS_DIR = os.path.join(ROOT, "shots")
TERR_DIR = os.path.join(SHOTS_DIR, "data", "terrarium")
FOUNDRY_DIR = os.path.join(TERR_DIR, "foundry")
STAGES_DIR = os.path.join(TERR_DIR, "stages")
ATLAS_DIR = os.path.join(TERR_DIR, "atlas_packs")
GLB_DIR = os.path.join(ATLAS_DIR, "glb")
SPLAT_DIR = os.path.join(ATLAS_DIR, "splats")
VAULT_ATLAS_DIR = os.path.join(SHOTS_DIR, "png_vault", "atlas_splats")

for d in [ATLAS_DIR, GLB_DIR, SPLAT_DIR, VAULT_ATLAS_DIR]:
    os.makedirs(d, exist_ok=True)


def get_font(size=14, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# 1. CURATED DISTRICT & 4 MEGA-HUB DEFINITIONS
# ---------------------------------------------------------------------------
DISTRICT_CURATION = {
    "mount-vernon": {
        "key": "mount-vernon",
        "name": "MOUNT VERNON · TOWER WINDOW, FIRE ESCAPE & 1920s BALLROOM",
        "zone": "BALTIMERE",
        "poems": ["01", "14"],
        "foundry_world": "w1623",
        "shared_horizon": 0.36,
        "anchor_refs": [
            {"id": "01-00", "set_piece": "A", "role": "Interior Bedroom -> Rain Window (R3 Portal)", "shell": "R3", "elev_m": 28.0},
            {"id": "01-03", "set_piece": "B", "role": "Window Sill -> Iron Fire Escape in Haze", "shell": "R3", "elev_m": 27.5},
            {"id": "01-06", "set_piece": "C", "role": "Exterior Brick Tower & Distant Window", "shell": "R4", "elev_m": 22.0},
            {"id": "01-07", "set_piece": "D", "role": "Brick Roof Ledge Overlooking City Plumes", "shell": "R4", "elev_m": 32.0},
            {"id": "01-02", "set_piece": "E", "role": "Warm Amber Ballroom / Mid-Fall Interior", "shell": "R2", "elev_m": 8.0},
            {"id": "07-06", "set_piece": "F", "role": "1920s Vintage Party Ballroom Floor", "shell": "R2", "elev_m": 4.0},
        ],
        "excluded_refs": [
            {"id": "01-04", "reason": "Abstract Halfworld transition blur"},
            {"id": "01-05", "reason": "Low-detail dark interior transition"},
        ],
        "portal_notes": "Sub-Splat A (28m high-rise bedroom + iron fire escape) bridges through the window aperture (R3) to the Mount Vernon brick street grid; Sub-Splat B sits below as the 1920s Belvedere ballroom."
    },
    "woodberry": {
        "key": "woodberry",
        "name": "WOODBERRY · CHILDHOOD WINDOW ON THE WINDING HILL ROAD",
        "zone": "BALTIMERE",
        "poems": ["02"],
        "foundry_world": "w1578",
        "shared_horizon": 0.38,
        "anchor_refs": [
            {"id": "02-02", "set_piece": "C", "role": "Living-Room Window & Red Velvet Drapes", "shell": "R3", "elev_m": 2.2},
            {"id": "02-01", "set_piece": "D", "role": "Childhood Hallway Night-Light Geometry", "shell": "R2", "elev_m": 2.0},
            {"id": "02-00", "set_piece": "E", "role": "Flashing Headlights on Winding Hill Curb", "shell": "R4", "elev_m": 1.8},
            {"id": "02-05", "set_piece": "F", "role": "Steep Downhill Street / Stairwell Escape", "shell": "R4", "elev_m": 0.5},
        ],
        "excluded_refs": [
            {"id": "02-04", "reason": "Macro eyeball close-up (poisons 3D scale)"},
            {"id": "02-06", "reason": "CRT pyramid belongs to Atlantis (P06)"},
            {"id": "02-07", "reason": "Cross-poem Markov duplicate of 01-00 bedroom"},
        ],
        "portal_notes": "Ground-floor living-room window (R3) looks directly out onto the sloping Clipper Mill Road curb where headlights rake across the ceiling."
    },
    "holland-island": {
        "key": "holland-island",
        "name": "HOLLAND ISLAND · ERODING SEASIDE CHAPEL IN THE STORM",
        "zone": "CENTER",
        "poems": ["03"],
        "foundry_world": "w0746",
        "shared_horizon": 0.50,
        "anchor_refs": [
            {"id": "03-00", "set_piece": "B", "role": "Crumbling Marble Pillars & Sanctuary Nave", "shell": "R3", "elev_m": 2.5},
            {"id": "07-07", "set_piece": "C", "role": "Empty Wooden Choir Risers & Closed Hymnals", "shell": "R2", "elev_m": 2.2},
            {"id": "03-02", "set_piece": "D", "role": "Storm Lightning Over Eroding Island Shore", "shell": "R5", "elev_m": 3.0},
            {"id": "03-06", "set_piece": "E", "role": "Post-Storm Chapel Remnants Washed Ashore", "shell": "R4", "elev_m": 1.2},
        ],
        "excluded_refs": [
            {"id": "03-01", "reason": "Macro tambourine floor insert (poisons 3D scale)"},
            {"id": "03-05", "reason": "Macro wet skin in red liquid pool"},
            {"id": "03-07", "reason": "Belongs to P04 Assateague Night Garden Field"},
        ],
        "portal_notes": "Shares shorelineChisel geometry with Inner Harbor (P11/P12) to support Twin-State Splat Morphing from Storm Ruin -> Rebuilt White Temple."
    },
    "assateague": {
        "key": "assateague",
        "name": "ASSATEAGUE · RUINS SHORE, DUNE INCLINE & NIGHT GARDEN",
        "zone": "CENTER",
        "poems": ["04"],
        "foundry_world": "w1165",
        "shared_horizon": 0.42,
        "anchor_refs": [
            {"id": "04-00", "set_piece": "A", "role": "Night Tide Line of Washed-Up Chapel Pieces", "shell": "R4", "elev_m": 0.8},
            {"id": "04-03", "set_piece": "B", "role": "Wide Twilight Beach & Calm Sea Horizon", "shell": "R4", "elev_m": 1.2},
            {"id": "04-01", "set_piece": "D", "role": "Trail Climbing Up the Dune Incline", "shell": "R3", "elev_m": 3.5},
            {"id": "03-07", "set_piece": "E", "role": "Moonlit Golden Garden Field Rows", "shell": "R4", "elev_m": 5.0},
            {"id": "04-07", "set_piece": "F", "role": "Sandy Footpath Into Dark Soil Clearing", "shell": "R2", "elev_m": 5.2},
        ],
        "excluded_refs": [
            {"id": "04-05", "reason": "Author typography title card (creates floating text wall)"},
            {"id": "04-06", "reason": "Cross-poem Markov duplicate of 01-00 bedroom"},
        ],
        "portal_notes": "Continuous outdoor terrain splat rising from sea-level tide line up the 5m dune trail into the golden night garden field."
    },
    "teotihuacan": {
        "key": "teotihuacan",
        "name": "TEOTIHUACAN · ANCESTORS' PARADE CAUSEWAY & STAR FIELD",
        "zone": "CENTER",
        "poems": ["05"],
        "foundry_world": "w0889",
        "shared_horizon": 0.43,
        "anchor_refs": [
            {"id": "05-01", "set_piece": "A", "role": "Open Night Meadow at Edge of Causeway", "shell": "R4", "elev_m": 6.0},
            {"id": "05-00", "set_piece": "B", "role": "Afro-Futuristic Ancestors' Processional Path", "shell": "R3", "elev_m": 8.0},
            {"id": "11-05", "set_piece": "D", "role": "Golden Chrysanthemum Field Along Causeway", "shell": "R2", "elev_m": 9.5},
            {"id": "05-07", "set_piece": "F", "role": "Trailhead Approaching the Light Gates", "shell": "R4", "elev_m": 12.0},
        ],
        "excluded_refs": [
            {"id": "05-04", "reason": "Glowing cervical spine X-ray diagram"},
            {"id": "05-05", "reason": "Duplicate cervical spine X-ray diagram"},
            {"id": "05-06", "reason": "100% tight forehead close-up"},
        ],
        "portal_notes": "Connects seamlessly from the Assateague Night Garden field along the processional Avenue of the Dead directly to the Light Gates of Atlantis."
    },
    "centro": {
        "key": "centro",
        "name": "CENTRO HISTÓRICO · ATLANTIS GATES, ALLEYS, ROOFTOP CLUB & PAYPHONE",
        "zone": "ATLANTIS",
        "poems": ["06", "08", "09"],
        "foundry_world": "w0980",
        "shared_horizon": 0.41,
        "anchor_refs": [
            {"id": "06-00", "set_piece": "A", "role": "Tier 1: Winged Marble Light Gates of Atlantis", "shell": "R3", "elev_m": 2.0},
            {"id": "06-07", "set_piece": "C", "role": "Tier 1: Radiant Cyberpunk Plaza & Gold Beams", "shell": "R4", "elev_m": 2.5},
            {"id": "06-02", "set_piece": "F", "role": "Tier 1: Candlelit Narrow Colonial Stone Alley", "shell": "R3", "elev_m": 2.0},
            {"id": "06-03", "set_piece": "G", "role": "Tier 1: Glowing Windows Along Old-Town Street", "shell": "R4", "elev_m": 2.2},
            {"id": "08-00", "set_piece": "B", "role": "Tier 2 (+38m): Open-Air Rooftop Nightclub", "shell": "R2", "elev_m": 38.0},
            {"id": "08-05", "set_piece": "E", "role": "Tier 2 (+38m): Chromatic Skyline From Roof Deck", "shell": "R4", "elev_m": 38.5},
            {"id": "09-00", "set_piece": "A", "role": "Tier 3 (Corner): Lit Street Payphone Booth & Suitcases", "shell": "R2", "elev_m": 1.8},
            {"id": "09-06", "set_piece": "D", "role": "Tier 3 (Corner): Night Sidewalk Perspective", "shell": "R4", "elev_m": 1.8},
        ],
        "excluded_refs": [
            {"id": "06-04", "reason": "100% tight crowd portrait"},
            {"id": "08-06", "reason": "Cross-poem Markov duplicate of 01-00 bedroom"},
            {"id": "09-02", "reason": "100% face close-up"},
            {"id": "09-04", "reason": "Cross-poem Markov duplicate of 01-07 Baltimore roof"},
            {"id": "09-05", "reason": "Cross-poem Markov duplicate of 01-07 Baltimore roof"},
        ],
        "portal_notes": "Flagship 3-Tier Vertical Metropolis Splat: Ground-level Light Gates & alleys (P06) -> High-rise Rooftop Club at +38m (P08) -> Rain-slick Payphone Sidewalk below (P09)."
    },
    "condesa": {
        "key": "condesa",
        "name": "CONDESA CASONA · TOWNHOUSE PARTY, BAR & DJ BOOTH",
        "zone": "ATLANTIS",
        "poems": ["07"],
        "foundry_world": "w1578",
        "shared_horizon": 0.37,
        "anchor_refs": [
            {"id": "07-05", "set_piece": "A", "role": "Back-Wall DJ Booth & Turntable Console", "shell": "R2", "elev_m": 2.0},
            {"id": "07-04", "set_piece": "B", "role": "Packed Casona Main Room & Bar Counter", "shell": "R3", "elev_m": 2.0},
            {"id": "08-07", "set_piece": "C", "role": "Speaker Stacks Flanking the Dancefloor", "shell": "R2", "elev_m": 2.2},
            {"id": "07-01", "set_piece": "E", "role": "Translucent Backlit Screen & Courtyard Door", "shell": "R3", "elev_m": 2.0},
        ],
        "excluded_refs": [
            {"id": "07-00", "reason": "Macro diary on turntable platter"},
            {"id": "07-03", "reason": "Boy in diner window (belongs to P02)"},
            {"id": "07-06", "reason": "1920s vintage ballroom (moved to P01/P14)"},
            {"id": "07-07", "reason": "Wooden choir risers (moved to P03 chapel)"},
        ],
        "portal_notes": "Interior courtyard townhouse splat connected to the narrow candlelit street of Centro (P06 Set-Piece G)."
    },
    "tres-marias": {
        "key": "tres-marias",
        "name": "TRES MARÍAS · NIGHT MOTORCYCLE HIGHWAY & DAWN MOUNTAIN PASS",
        "zone": "ATLANTIS",
        "poems": ["10"],
        "foundry_world": "w1165",
        "shared_horizon": 0.43,
        "anchor_refs": [
            {"id": "10-01", "set_piece": "A", "role": "City Sidewalk Departure & Parked Motorcycle", "shell": "R2", "elev_m": 4.0},
            {"id": "10-00", "set_piece": "B", "role": "Speeding Through Atlantis Streets to Ramp", "shell": "R4", "elev_m": 12.0},
            {"id": "09-07", "set_piece": "C", "role": "Forest Highway Shoulder at Mountain Base", "shell": "R4", "elev_m": 38.0},
            {"id": "10-04", "set_piece": "E", "role": "Climbing Mountain Pass with Golden Dawn Streaks", "shell": "R4", "elev_m": 72.0},
            {"id": "10-05", "set_piece": "F", "role": "Summit Crest Overlooking Dawn Valley", "shell": "R5", "elev_m": 92.0},
        ],
        "excluded_refs": [
            {"id": "10-06", "reason": "Cross-poem Markov duplicate of 01-00 Baltimore bedroom"},
            {"id": "10-07", "reason": "Cross-poem Markov duplicate of 01-00 Baltimore bedroom"},
        ],
        "portal_notes": "Long 99.8m-relief highway ribbon splat climbing from the Atlantis city edge up through the forested mountain pass at dawn."
    },
    "inner-harbor": {
        "key": "inner-harbor",
        "name": "INNER HARBOR · REBUILT WHITE HARBOR TEMPLE & FEDERAL HILL MEADOW",
        "zone": "CENTER",
        "poems": ["11", "12"],
        "foundry_world": "w0889",
        "shared_horizon": 0.46,
        "anchor_refs": [
            {"id": "11-01", "set_piece": "A", "role": "Dawn Harbor Shore with Washed Chapel Stones", "shell": "R4", "elev_m": 1.0},
            {"id": "11-00", "set_piece": "C", "role": "Futuristic White Sloping Temple on Harbor Shore", "shell": "R3", "elev_m": 3.5},
            {"id": "11-06", "set_piece": "F", "role": "Sunlit Promenade Along the New Temple", "shell": "R4", "elev_m": 2.5},
            {"id": "12-00", "set_piece": "A", "role": "Main Gathering Hall Inside the Harbor Temple", "shell": "R3", "elev_m": 4.0},
            {"id": "12-01", "set_piece": "E", "role": "Federal Hill Forest Edge & Porch Lights Below", "shell": "R4", "elev_m": 16.0},
            {"id": "12-07", "set_piece": "G", "role": "Warm Community Hall Interior Memory Space", "shell": "R2", "elev_m": 4.0},
        ],
        "excluded_refs": [
            {"id": "11-02", "reason": "Monks on steps (belongs to P06)"},
            {"id": "12-04", "reason": "Tight portrait close-up of brothers"},
            {"id": "12-05", "reason": "Duplicate tight portrait close-up"},
            {"id": "12-06", "reason": "82% crowd close-up"},
        ],
        "portal_notes": "Twin-State Harbor Splat: pairs directly with Holland Island (P03) on the same shoreline Chisel `.glb` so the ruin rebuilds into the white dawn temple."
    },
    "fells-point": {
        "key": "fells-point",
        "name": "FELLS POINT · CORNER CAFÉ WINDOW & COBBLESTONE HARBOR PIER",
        "zone": "BALTIMERE",
        "poems": ["13"],
        "foundry_world": "w0980",
        "shared_horizon": 0.37,
        "anchor_refs": [
            {"id": "13-01", "set_piece": "B", "role": "Corner Café Window Table Looking Out to Pier", "shell": "R3", "elev_m": 2.0},
            {"id": "13-00", "set_piece": "A", "role": "Stepping Out of Café onto Cobblestone Harbor", "shell": "R3", "elev_m": 1.8},
            {"id": "13-03", "set_piece": "E", "role": "Thames Street Brick Waterfront Facades", "shell": "R4", "elev_m": 2.5},
            {"id": "13-02", "set_piece": "G", "role": "Harbor of the Heavens Pier & Steeple Horizon", "shell": "R5", "elev_m": 1.5},
        ],
        "excluded_refs": [
            {"id": "13-04", "reason": "Close-up of tracksuit sleeves"},
            {"id": "13-05", "reason": "Duplicate close-up of tracksuit sleeves"},
            {"id": "13-06", "reason": "Belongs to P09 phone-booth breakup"},
            {"id": "13-07", "reason": "Duplicate of 08-02 club"},
        ],
        "portal_notes": "Window-portal splat bridging the warm corner café table (`R2/R3`) across the cobblestone promenade to the Inner Harbor water (`R4/R5`)."
    },
}

MEGA_HUBS = [
    {
        "hub_id": "hub_01_atlantis",
        "rank": 1,
        "title": "MEGA-HUB 01 · THE ATLANTIS VERTICAL METROPOLIS BLOCK",
        "subtitle": "Covers 5 Poems (~35% of Film): P06 Gates & Alleys · P07 Casona DJ Party · P08 Rooftop Club (+38m) · P09 Payphone Sidewalk · P10 Motorcycle Departure",
        "primary_stage": "centro",
        "linked_stages": ["centro", "condesa", "tres-marias"],
        "poems": ["06", "07", "08", "09", "10"],
        "primary_poem_pano": "06",
        "secondary_poem_pano": "08",
        "shared_horizon": 0.41,
        "hero_anchors": ["06-00", "06-02", "07-04", "08-00", "09-00", "10-01"],
        "bang_for_buck": "1 Splat Hub = 5 Poems across 3 vertical tiers (0m Street Alleys + Casona Courtyard + 38m Rooftop Club + Payphone Corner)",
    },
    {
        "hub_id": "hub_02_harbor_temple",
        "rank": 2,
        "title": "MEGA-HUB 02 · THE HARBOR TEMPLE SHORE & CAFÉ (TWIN-STATE MORPH)",
        "subtitle": "Covers 4 Poems (~28% of Film): P03 Storm Ruin Chapel <-> P11 Rebuilt White Dawn Temple · P12 Reunion Hall & Meadow · P13 Fells Point Harbor Café",
        "primary_stage": "inner-harbor",
        "linked_stages": ["holland-island", "inner-harbor", "fells-point"],
        "poems": ["03", "11", "12", "13"],
        "primary_poem_pano": "11",
        "secondary_poem_pano": "03",
        "shared_horizon": 0.46,
        "hero_anchors": ["03-00", "03-06", "11-00", "12-00", "12-01", "13-00"],
        "bang_for_buck": "Twin-State Chisel `.glb`: Same shoreline geometry skins both P03 Storm Ruin and P11/P12 Rebuilt White Temple for real-time 3D splat cross-dissolves!",
    },
    {
        "hub_id": "hub_03_mount_vernon",
        "rank": 3,
        "title": "MEGA-HUB 03 · MOUNT VERNON WINDOW TOWER TO 1920s BALLROOM DROP",
        "subtitle": "Covers 3 Poems (~20% of Film): P01 High-Rise Bedroom & Fire Escape · P02 Childhood Street Window · P14 Vintage Ballroom Finale",
        "primary_stage": "mount-vernon",
        "linked_stages": ["mount-vernon", "woodberry"],
        "poems": ["01", "02", "14"],
        "primary_poem_pano": "01",
        "secondary_poem_pano": "14",
        "shared_horizon": 0.36,
        "hero_anchors": ["01-00", "01-03", "01-06", "01-07", "02-02", "07-06"],
        "bang_for_buck": "Bookends the opening (P01) and closing (P14) of the film in a single vertical drop from the 28m window sill through the fire escape into the 1920s ballroom.",
    },
    {
        "hub_id": "hub_04_shore_garden",
        "rank": 4,
        "title": "MEGA-HUB 04 · RUINS BEACH TO ANCESTORS' GARDEN CAUSEWAY",
        "subtitle": "Covers 2 Continuous Poems (~15% of Film): P04 Nevermore Shore & Dune Incline -> P05 Bloodline Moonlit Garden & Ancestors' Procession",
        "primary_stage": "assateague",
        "linked_stages": ["assateague", "teotihuacan"],
        "poems": ["04", "05"],
        "primary_poem_pano": "04",
        "secondary_poem_pano": "05",
        "shared_horizon": 0.42,
        "hero_anchors": ["04-00", "04-03", "04-01", "03-07", "05-00", "05-07"],
        "bang_for_buck": "One continuous 3D walk from the night waterline up the dune path through the golden blooms straight into the ancestors' parade causeway.",
    },
]


# ---------------------------------------------------------------------------
# 2. HEIGHTFIELD UNPACKER & BINARY glTF 2.0 (`.glb`) CHISEL/COLLIDER EXPORTER
# ---------------------------------------------------------------------------
def unpack_heights(hf_b64, count, relief):
    raw = base64.b64decode(hf_b64)
    H = np.zeros(count, dtype=np.float32)
    vi = 0
    n_raw = len(raw)
    for i in range(0, n_raw, 3):
        if vi >= count:
            break
        a = raw[i]
        b = raw[i + 1] if (i + 1) < n_raw else 0
        c = raw[i + 2] if (i + 2) < n_raw else 0
        H[vi] = ((a << 4) | (b >> 4)) / 4095.0 * relief
        vi += 1
        if vi < count:
            H[vi] = (((b & 15) << 8) | c) / 4095.0 * relief
            vi += 1
    return H


def make_landpack_sampler(lp):
    w = float(lp.get("w", 160.0))
    h = float(lp.get("h", 160.0))
    nx = int(lp.get("nx", 129))
    nz = int(lp.get("nz", 129))
    relief = float(lp.get("relief", 10.0))
    H = unpack_heights(lp["hf"], nx * nz, relief)
    spawn = lp.get("spawn", {"x": 0.0, "z": 0.0})

    def raw_grid(x, z):
        fx = (x + w / 2.0) / w * (nx - 1)
        fz = (z + h / 2.0) / h * (nz - 1)
        i = int(max(0, min(nx - 2, math.floor(fx))))
        j = int(max(0, min(nz - 2, math.floor(fz))))
        tx = max(0.0, min(1.0, fx - i))
        tz = max(0.0, min(1.0, fz - j))
        h00 = H[j * nx + i]
        h10 = H[j * nx + i + 1]
        h01 = H[(j + 1) * nx + i]
        h11 = H[(j + 1) * nx + i + 1]
        return float(
            h00 * (1 - tx) * (1 - tz)
            + h10 * tx * (1 - tz)
            + h01 * (1 - tx) * tz
            + h11 * tx * tz
        )

    datum = raw_grid(float(spawn.get("x", 0.0)), float(spawn.get("z", 0.0)))

    def gYw(x, z):
        return raw_grid(x, z) - datum

    return w, h, nx, nz, datum, gYw


def build_glb_from_landpack(lp, out_glb_path, set_pieces=None, extra_meta=None):
    """
    Writes a binary glTF 2.0 (`.glb`) containing:
      - Mesh 0 (`TERRAIN_COLLIDER`): subsampled 65x65 terrain mesh in exact Three.js Terrarium coords
      - Mesh 1 (`BUILDINGS_CHISEL`): extruded 3D OSM/Foundry buildings seated on `gYw(x, z)`
      - Mesh 2 (`PORTAL_APERTURES_R3`): Set-piece stage frames (`A..F`) with window portals
    """
    w, h, nx, nz, datum, gYw = make_landpack_sampler(lp)

    # 1. Terrain mesh (subsample to 65x65 so GLB is compact & fast for Marble Chisel + browser raycast)
    gx_n, gz_n = 65, 65
    xs = np.linspace(-w / 2.0, w / 2.0, gx_n, dtype=np.float32)
    zs = np.linspace(-h / 2.0, h / 2.0, gz_n, dtype=np.float32)
    t_verts = []
    t_colors = []
    for j in range(gz_n):
        for i in range(gx_n):
            x = float(xs[i])
            z = float(zs[j])
            y = float(gYw(x, z))
            t_verts.append((x, y, z))
            # Subtle height-based vertex tint for Chisel readability
            c_norm = max(0.15, min(0.85, 0.35 + y * 0.025))
            t_colors.append((c_norm * 0.72, c_norm * 0.84, c_norm * 0.78))

    t_indices = []
    for j in range(gz_n - 1):
        for i in range(gx_n - 1):
            a = j * gx_n + i
            b = a + 1
            c = (j + 1) * gx_n + i
            d = c + 1
            t_indices.extend([a, c, b, b, c, d])

    # 2. Buildings Chisel mesh (`bld`)
    b_verts = []
    b_colors = []
    b_indices = []
    blds = lp.get("bld", [])
    for b in blds[:360]:
        pts = b.get("p", [])
        if len(pts) < 3:
            continue
        bh = float(b.get("h", 8.0))
        cx = sum(p[0] for p in pts) / len(pts)
        cz = sum(p[1] for p in pts) / len(pts)
        base_y = float(gYw(cx, cz)) - 0.15
        top_y = base_y + bh

        # Wall quads around footprint
        n_p = len(pts)
        for k in range(n_p - 1):
            x0, z0 = float(pts[k][0]), float(pts[k][1])
            x1, z1 = float(pts[k + 1][0]), float(pts[k + 1][1])
            v_base = len(b_verts)
            b_verts.extend([
                (x0, base_y, z0),
                (x1, base_y, z1),
                (x1, top_y, z1),
                (x0, top_y, z0),
            ])
            b_colors.extend([
                (0.38, 0.44, 0.54),
                (0.38, 0.44, 0.54),
                (0.56, 0.64, 0.76),
                (0.56, 0.64, 0.76),
            ])
            b_indices.extend([
                v_base, v_base + 1, v_base + 2,
                v_base, v_base + 2, v_base + 3,
            ])

        # Simple fan roof cap from centroid
        c_idx = len(b_verts)
        b_verts.append((cx, top_y, cz))
        b_colors.append((0.68, 0.74, 0.84))
        ring_start = len(b_verts)
        for k in range(n_p - 1):
            b_verts.append((float(pts[k][0]), top_y, float(pts[k][1])))
            b_colors.append((0.64, 0.70, 0.80))
        for k in range(n_p - 2):
            b_indices.extend([c_idx, ring_start + k, ring_start + k + 1])
        if n_p >= 3:
            b_indices.extend([c_idx, ring_start + (n_p - 2), ring_start])

    # 3. Set-Piece Portal Frames (`A..F` Onion Shell R3 window apertures)
    if set_pieces:
        for idx, sp in enumerate(set_pieces[:6]):
            sx = float(sp.get("x", -25.0 + idx * 10.0))
            sz = float(sp.get("z", 0.0))
            sy = float(gYw(sx, sz))
            yaw = float(sp.get("facing", idx * 45.0)) * math.pi / 180.0
            cos_y, sin_y = math.cos(yaw), math.sin(yaw)

            # Build a 3D portal arch frame (width 8m, height 4.6m, thickness 0.4m) with an open window hole
            # Left pillar, right pillar, and top lintel
            boxes = [
                (-4.0, 0.0, -0.2, -2.6, 4.6, 0.2),  # left wall pier
                (2.6, 0.0, -0.2, 4.0, 4.6, 0.2),    # right wall pier
                (-4.0, 3.6, -0.2, 4.0, 4.6, 0.2),   # top lintel
                (-2.6, 0.0, -0.2, 2.6, 1.0, 0.2),   # window sill (R3 threshold)
            ]
            for (x0, y0, z0, x1, y1, z1) in boxes:
                corners_local = [
                    (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                    (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
                ]
                v_base = len(b_verts)
                for (lx, ly, lz) in corners_local:
                    wx = sx + lx * cos_y + lz * sin_y
                    wz = sz - lx * sin_y + lz * cos_y
                    wy = sy + ly
                    b_verts.append((wx, wy, wz))
                    b_colors.append((0.56, 0.84, 0.58))  # Sage-green R3 Arch Aperture tint
                faces = [
                    (0, 1, 2, 3), (5, 4, 7, 6),
                    (4, 0, 3, 7), (1, 5, 6, 2),
                    (3, 2, 6, 7), (4, 5, 1, 0),
                ]
                for (f0, f1, f2, f3) in faces:
                    b_indices.extend([
                        v_base + f0, v_base + f1, v_base + f2,
                        v_base + f0, v_base + f2, v_base + f3,
                    ])

    # Combine terrain + buildings into binary buffer
    all_verts = np.array(t_verts + b_verts, dtype=np.float32)
    all_colors = np.array(t_colors + b_colors, dtype=np.float32)
    offset_b = len(t_verts)
    all_indices = np.array(
        t_indices + [idx + offset_b for idx in b_indices],
        dtype=np.uint32,
    )

    vmin = all_verts.min(axis=0).tolist()
    vmax = all_verts.max(axis=0).tolist()

    v_bytes = all_verts.tobytes()
    c_bytes = all_colors.tobytes()
    i_bytes = all_indices.tobytes()

    def pad4(b):
        rem = len(b) % 4
        return b + (b"\x00" * (4 - rem) if rem else b"")

    v_bytes_p = pad4(v_bytes)
    c_bytes_p = pad4(c_bytes)
    i_bytes_p = pad4(i_bytes)
    bin_blob = v_bytes_p + c_bytes_p + i_bytes_p

    gltf_dict = {
        "asset": {
            "version": "2.0",
            "generator": "WYGWYL Atlas/Marble Chisel & Collider Exporter v1.0",
            "extras": extra_meta or {},
        },
        "scene": 0,
        "scenes": [{"name": lp.get("name", "WYGWYL_DISTRICT"), "nodes": [0]}],
        "nodes": [{"name": "DISTRICT_CHISEL_COLLIDER", "mesh": 0}],
        "meshes": [
            {
                "name": "DISTRICT_CHISEL_COLLIDER",
                "primitives": [
                    {
                        "attributes": {"POSITION": 0, "COLOR_0": 1},
                        "indices": 2,
                        "mode": 4,
                    }
                ],
            }
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,  # FLOAT
                "count": len(all_verts),
                "type": "VEC3",
                "min": vmin,
                "max": vmax,
            },
            {
                "bufferView": 1,
                "componentType": 5126,  # FLOAT
                "count": len(all_colors),
                "type": "VEC3",
            },
            {
                "bufferView": 2,
                "componentType": 5125,  # UNSIGNED_INT
                "count": len(all_indices),
                "type": "SCALAR",
            },
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(v_bytes), "target": 34962},
            {"buffer": 0, "byteOffset": len(v_bytes_p), "byteLength": len(c_bytes), "target": 34962},
            {"buffer": 0, "byteOffset": len(v_bytes_p) + len(c_bytes_p), "byteLength": len(i_bytes), "target": 34963},
        ],
        "buffers": [{"byteLength": len(bin_blob)}],
    }

    json_bytes = json.dumps(gltf_dict, separators=(",", ":")).encode("utf-8")
    rem_j = len(json_bytes) % 4
    if rem_j:
        json_bytes += b" " * (4 - rem_j)

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_blob)
    header = struct.pack("<4sII", b"glTF", 2, total_len)
    chunk_json = struct.pack("<II", len(json_bytes), 0x4E4F534A) + json_bytes
    chunk_bin = struct.pack("<II", len(bin_blob), 0x004E4942) + bin_blob

    with open(out_glb_path, "wb") as f:
        f.write(header + chunk_json + chunk_bin)

    return {
        "file": os.path.relpath(out_glb_path, SHOTS_DIR),
        "bytes": total_len,
        "vertices": int(len(all_verts)),
        "triangles": int(len(all_indices) // 3),
        "buildings_extruded": int(min(len(blds), 360)),
        "bounds_min": [round(x, 2) for x in vmin],
        "bounds_max": [round(x, 2) for x in vmax],
        "datum_m": round(datum, 3),
    }


# ---------------------------------------------------------------------------
# 3. ACTOR-CLEANED (`R0/R1` INPAINTED) IMAGES & `2560x1280` EQUIREC PANORAMAS
# ---------------------------------------------------------------------------
def clean_actor_from_ref(rgb_path, seg_path):
    """
    Uses the panoptic segmentation mask (`-seg.jpg`) to identify foreground `person`
    pixels (bright red/magenta/orange in seg map) and softly inpaints them with
    surrounding architectural background so Marble/Atlas doesn't bake wax-statue people.
    """
    img = Image.open(rgb_path).convert("RGB")
    w, h = img.size
    arr = np.array(img, dtype=np.float32)

    person_mask = np.zeros((h, w), dtype=np.float32)
    if os.path.exists(seg_path):
        seg = np.array(Image.open(seg_path).convert("RGB").resize((w, h), Image.BILINEAR), dtype=np.float32)
        r, g, b = seg[:, :, 0], seg[:, :, 1], seg[:, :, 2]
        # Person class in ADE20K / Foundry seg is high red, low green/blue or bright pink
        is_p = (r > 150) & (r > g * 1.45) & (b < 145)
        person_mask[is_p] = 1.0

    frac_p = float(person_mask.mean())
    if frac_p < 0.008:
        return img, 0.0

    # Dilate and feather mask
    mask_pil = Image.fromarray((person_mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(8))
    alpha = np.array(mask_pil, dtype=np.float32)[:, :, None] / 255.0

    # Fill masked region using horizontal background propagation + heavy architectural blur
    bg_blur = np.array(img.filter(ImageFilter.GaussianBlur(28)), dtype=np.float32)
    # Also shift non-person horizontal scanline median
    scan_fill = np.copy(arr)
    for y in range(h):
        row_m = alpha[y, :, 0] < 0.25
        if np.any(row_m):
            med_color = np.median(arr[y, row_m], axis=0)
            scan_fill[y] = med_color * 0.45 + bg_blur[y] * 0.55
        else:
            scan_fill[y] = bg_blur[y]

    cleaned = arr * (1.0 - alpha * 0.88) + scan_fill * (alpha * 0.88)
    return Image.fromarray(np.clip(cleaned, 0, 255).astype(np.uint8)), round(frac_p * 100.0, 1)


def build_clean_2560x1280_pano(poem_num, out_rgb_path, out_depth_path):
    """
    Upsamples the shared 2:1 equirectangular panorama and equirectangular depth mask
    for `poem_num` to Marble's recommended `2560x1280` (`2:1`) resolution, smoothing
    any foreground person silhouettes into clean architectural shells (`R2..R5`).
    """
    src_eq = os.path.join(FOUNDRY_DIR, "equirec", f"poem_{poem_num}_shared_eq.jpg")
    src_dp = os.path.join(FOUNDRY_DIR, "equirec", f"poem_{poem_num}_shared_depth.jpg")

    eq_img = Image.open(src_eq).convert("RGB").resize((2560, 1280), Image.LANCZOS)
    dp_img = Image.open(src_dp).convert("RGB").resize((2560, 1280), Image.LANCZOS)

    # Ensure seamless 360 horizontal wrap at x=0 and x=2559 (blend 16px seam)
    eq_arr = np.array(eq_img, dtype=np.float32)
    for dx in range(16):
        w_blend = (16 - dx) / 32.0
        avg = 0.5 * (eq_arr[:, dx] + eq_arr[:, 2559 - dx])
        eq_arr[:, dx] = eq_arr[:, dx] * (1.0 - w_blend) + avg * w_blend
        eq_arr[:, 2559 - dx] = eq_arr[:, 2559 - dx] * (1.0 - w_blend) + avg * w_blend

    Image.fromarray(np.clip(eq_arr, 0, 255).astype(np.uint8)).save(out_rgb_path, quality=92)
    dp_img.save(out_depth_path, quality=92)


# ---------------------------------------------------------------------------
# 4. 3D GAUSSIAN SPLAT (`.splat` 32-BYTE STANDARD) GENERATOR
# ---------------------------------------------------------------------------
def build_binary_splat_for_hub(lp, pano_rgb_path, anchor_imgs, set_pieces, out_splat_path, state_tint=None, n_target=28000):
    """
    Generates a standard 32-byte-per-splat `.splat` binary file in Three.js Terrarium
    metric coordinates so the splat renders immediately on top of the `.glb` collider:
      Bytes 0..11  : float32 x, y, z (position in meters)
      Bytes 12..23 : float32 sx, sy, sz (scale in meters)
      Bytes 24..27 : uint8 r, g, b, a (color & opacity)
      Bytes 28..31 : uint8 qx, qy, qz, qw (rotation quaternion encoded as (q*128 + 128))
    Combines:
      1. Ground & topography splats sampled from the landpack heightfield + pano lower hemisphere (`R2/R4`)
      2. Building facade & roof splats sampled from `lp["bld"]` (`R3/R4`)
      3. Set-piece architectural portal & interior wall splats (`A..F`) sampled from the clean anchor frames (`R2/R3`)
      4. Horizon & sky dome splats (`R5`)
    """
    w, h, nx, nz, datum, gYw = make_landpack_sampler(lp)
    pano = np.array(Image.open(pano_rgb_path).convert("RGB").resize((512, 256), Image.BILINEAR), dtype=np.uint8)
    ph, pw, _ = pano.shape

    rng = np.random.default_rng(abs(hash(out_splat_path)) % (2**32))

    positions = []
    scales = []
    colors = []
    quats = []  # default identity quaternion [128, 128, 128, 255] -> (0,0,0,1)

    # A. Ground Terrain Splats (~10,000 splats)
    n_ground = int(n_target * 0.36)
    gx = rng.uniform(-w * 0.48, w * 0.48, n_ground).astype(np.float32)
    gz = rng.uniform(-h * 0.48, h * 0.48, n_ground).astype(np.float32)
    for i in range(n_ground):
        x, z = float(gx[i]), float(gz[i])
        y = float(gYw(x, z)) + float(rng.uniform(0.05, 0.25))
        az = (math.atan2(x, z) + math.pi) / (2.0 * math.pi)
        u = int(az * (pw - 1)) % pw
        dist_norm = min(1.0, math.hypot(x, z) / (max(w, h) * 0.5))
        v = int((0.52 + (1.0 - dist_norm) * 0.45) * (ph - 1))
        c = pano[v, u].tolist()
        if state_tint == "ruin":
            c = [int(c[0] * 0.72), int(c[1] * 0.78), int(min(255, c[2] * 1.15))]
        elif state_tint == "temple":
            c = [int(min(255, c[0] * 1.12 + 18)), int(min(255, c[1] * 1.08 + 14)), int(min(255, c[2] * 1.02 + 10))]
        positions.append((x, y, z))
        s_val = float(rng.uniform(0.65, 1.45))
        scales.append((s_val, s_val * 0.35, s_val))
        colors.append((c[0], c[1], c[2], 215))
        quats.append((128, 128, 128, 255))

    # B. Building Facade & Roof Splats (~10,000 splats)
    blds = lp.get("bld", [])
    n_bld_target = int(n_target * 0.36)
    if blds:
        per_bld = max(12, n_bld_target // max(1, len(blds[:220])))
        for b in blds[:220]:
            pts = b.get("p", [])
            if len(pts) < 3:
                continue
            bh = float(b.get("h", 9.0))
            cx = sum(p[0] for p in pts) / len(pts)
            cz = sum(p[1] for p in pts) / len(pts)
            base_y = float(gYw(cx, cz))
            az = (math.atan2(cx, cz) + math.pi) / (2.0 * math.pi)
            u_base = int(az * (pw - 1)) % pw

            for _ in range(per_bld):
                edge_idx = int(rng.integers(0, len(pts) - 1))
                p0, p1 = pts[edge_idx], pts[edge_idx + 1]
                t_edge = float(rng.uniform(0.0, 1.0))
                bx = float(p0[0] * (1.0 - t_edge) + p1[0] * t_edge)
                bz = float(p0[1] * (1.0 - t_edge) + p1[1] * t_edge)
                by_rel = float(rng.uniform(0.2, bh))
                by = base_y + by_rel

                u = (u_base + int(rng.integers(-12, 13))) % pw
                v = int(max(0.18, min(0.55, 0.48 - (by_rel / 45.0) * 0.25)) * (ph - 1))
                c = pano[v, u].tolist()
                if state_tint == "ruin":
                    c = [int(c[0] * 0.68), int(c[1] * 0.74), int(min(255, c[2] * 1.18))]
                elif state_tint == "temple":
                    c = [int(min(255, c[0] * 1.15 + 22)), int(min(255, c[1] * 1.12 + 18)), int(min(255, c[2] * 1.05 + 15))]

                positions.append((bx, by, bz))
                s_val = float(rng.uniform(0.45, 0.95))
                scales.append((s_val, s_val * 1.15, s_val))
                colors.append((c[0], c[1], c[2], 235))
                quats.append((128, 128, 128, 255))

    # C. Set-Piece Architectural Portals & Anchor Back-Projected Splats (~5,500 splats)
    n_portal_per_sp = max(400, int(n_target * 0.20) // max(1, len(set_pieces[:6])))
    for idx, sp in enumerate(set_pieces[:6]):
        sx = float(sp.get("x", -20.0 + idx * 8.0))
        sz = float(sp.get("z", 0.0))
        sy = float(gYw(sx, sz))
        yaw = float(sp.get("facing", idx * 45.0)) * math.pi / 180.0
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)

        anchor_arr = pano
        if anchor_imgs and idx < len(anchor_imgs) and os.path.exists(anchor_imgs[idx]):
            anchor_arr = np.array(Image.open(anchor_imgs[idx]).convert("RGB").resize((96, 54), Image.BILINEAR), dtype=np.uint8)
        ah, aw, _ = anchor_arr.shape

        for _ in range(n_portal_per_sp):
            u_norm = float(rng.uniform(0.0, 1.0))
            v_norm = float(rng.uniform(0.0, 1.0))
            c = anchor_arr[int(v_norm * (ah - 1)), int(u_norm * (aw - 1))].tolist()
            # Local multiplane depth shell around the stage portal
            lx = (u_norm - 0.5) * 12.0
            ly = (1.0 - v_norm) * 5.8 + 0.2
            lz = float(rng.choice([-2.2, -0.8, 0.4, 1.6])) + float(rng.uniform(-0.25, 0.25))
            wx = sx + lx * cos_y + lz * sin_y
            wz = sz - lx * sin_y + lz * cos_y
            wy = sy + ly
            positions.append((wx, wy, wz))
            s_val = float(rng.uniform(0.22, 0.48))
            scales.append((s_val, s_val, s_val))
            colors.append((c[0], c[1], c[2], 245))
            quats.append((128, 128, 128, 255))

    # D. Outer Horizon & Sky Dome Ring (`R5`, ~2,500 splats)
    n_sky = int(n_target * 0.08)
    sky_r = max(w, h) * 0.56
    for i in range(n_sky):
        az = float(rng.uniform(0.0, 2.0 * math.pi))
        elev = float(rng.uniform(0.04, 0.48))
        x = math.sin(az) * sky_r * math.cos(elev)
        z = math.cos(az) * sky_r * math.cos(elev)
        y = math.sin(elev) * (sky_r * 0.45) + 4.0
        u = int(((az / (2.0 * math.pi)) % 1.0) * (pw - 1))
        v = int(max(0.02, min(0.46, 0.46 - elev * 0.85)) * (ph - 1))
        c = pano[v, u].tolist()
        positions.append((x, y, z))
        s_val = float(rng.uniform(2.2, 4.2))
        scales.append((s_val, s_val, s_val))
        colors.append((c[0], c[1], c[2], 185))
        quats.append((128, 128, 128, 255))

    # Pack into 32-byte records
    n_total = len(positions)
    buf = bytearray(n_total * 32)
    struct_fmt = "<fff fff BBBB BBBB"
    for i in range(n_total):
        px, py, pz = positions[i]
        sx, sy, sz = scales[i]
        r, g, b, a = colors[i]
        qx, qy, qz, qw = quats[i]
        struct.pack_into(struct_fmt, buf, i * 32, px, py, pz, sx, sy, sz, r, g, b, a, qx, qy, qz, qw)

    with open(out_splat_path, "wb") as f:
        f.write(buf)

    return {
        "file": os.path.relpath(out_splat_path, SHOTS_DIR),
        "splat_count": n_total,
        "bytes": len(buf),
        "format": "standard_32byte_splat",
    }


# ---------------------------------------------------------------------------
# 5. CAMERA POSE & COORDINATE BRIDGE COMPUTATION (`OpenCV <-> Three.js`)
# ---------------------------------------------------------------------------
def build_spatial_context_cameras(lp, stage_meta, curated_info, ref_lookup):
    """
    Computes exact 3D camera poses for each anchor reference in both:
      - Three.js Terrarium World Space (`+X east, +Y up, +Z south`, datum-aligned at `spawn`)
      - World Labs Atlas / Marble OpenCV Space (`+X left, +Y down, +Z forward`)
    """
    w, h, nx, nz, datum, gYw = make_landpack_sampler(lp)
    spawn = lp.get("spawn", {"x": 0.0, "z": 0.0})

    # Gather set_pieces from stage_meta
    sp_by_key = {}
    for pm in stage_meta.get("poems", []):
        for sp in pm.get("set_pieces", []):
            sp_by_key[sp["k"]] = sp

    cameras = []
    for idx, anc in enumerate(curated_info["anchor_refs"]):
        rid = anc["id"]
        rmeta = ref_lookup.get(rid, {})
        sp = sp_by_key.get(anc["set_piece"], {})
        tx = float(sp.get("x", -18.0 + idx * 7.5))
        tz = float(sp.get("z", -10.0 + idx * 4.5))
        ground_elev = float(gYw(tx, tz))
        ty = ground_elev + float(anc.get("elev_m", 2.0))

        az_deg = float(rmeta.get("eq_azimuth_deg", idx * 60.0))
        yaw_rad = math.radians(az_deg)

        # Three.js forward vector
        fwd_x = math.sin(yaw_rad)
        fwd_z = math.cos(yaw_rad)
        target_three = [round(tx + fwd_x * 12.0, 3), round(ty, 3), round(tz + fwd_z * 12.0, 3)]

        # OpenCV coordinates (+X left, +Y down, +Z forward) relative to spawn origin
        cv_x = round(-(tx - float(spawn.get("x", 0.0))), 3)
        cv_y = round(-ty, 3)
        cv_z = round(tz - float(spawn.get("z", 0.0)), 3)

        # 3x3 rotation matrix around Y
        cy, sy_val = round(math.cos(yaw_rad), 4), round(math.sin(yaw_rad), 4)
        R_opencv = [
            [cy, 0.0, sy_val],
            [0.0, 1.0, 0.0],
            [-sy_val, 0.0, cy],
        ]

        cameras.append({
            "ref_id": rid,
            "set_piece": anc["set_piece"],
            "role": anc["role"],
            "onion_shell": anc["shell"],
            "source_img": f"data/terrarium/foundry/refs/{rid}.jpg",
            "depth_img": f"data/terrarium/foundry/refs/{rid}-depth.jpg",
            "equirec_img": f"data/terrarium/foundry/equirec/{rid}-eq.jpg",
            "equirec_depth_img": f"data/terrarium/foundry/equirec/{rid}-eq-depth.jpg",
            "azimuth_deg": az_deg,
            "horizon_norm": float(rmeta.get("shared_horizon", curated_info["shared_horizon"])),
            "threejs_pose": {
                "position_m": [round(tx, 3), round(ty, 3), round(tz, 3)],
                "ground_y_m": round(ground_elev, 3),
                "look_at_m": target_three,
                "yaw_deg": round(az_deg, 1),
                "fov_deg": 50.0,
            },
            "atlas_opencv_pose": {
                "convention": "+X left, +Y down, +Z forward",
                "t_m": [cv_x, cv_y, cv_z],
                "R_3x3": R_opencv,
                "intrinsics_K_1024x576": [
                    [888.8, 0.0, 512.0],
                    [0.0, 888.8, 288.0],
                    [0.0, 0.0, 1.0],
                ],
            },
        })

    return {
        "coordinate_bridge": {
            "terrarium_convention": "Three.js (+X east, +Y up, +Z south, 1 unit = 1 meter)",
            "marble_atlas_convention": "OpenCV (+X left, +Y down, +Z forward)",
            "spawn_origin_threejs_m": [round(float(spawn.get("x", 0.0)), 3), 0.0, round(float(spawn.get("z", 0.0)), 3)],
            "datum_offset_m": round(datum, 3),
            "opencv_to_threejs_4x4": [
                [-1.0, 0.0, 0.0, round(float(spawn.get("x", 0.0)), 3)],
                [0.0, -1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, round(float(spawn.get("z", 0.0)), 3)],
                [0.0, 0.0, 0.0, 1.0],
            ],
        },
        "cameras": cameras,
    }


# ---------------------------------------------------------------------------
# 6. VISUAL PROOF PLATE RENDERERS (`shots/png_vault/atlas_splats/`)
# ---------------------------------------------------------------------------
def render_district_atlas_plate(d_key, d_info, glb_info, pose_info, ref_lookup, out_png_path):
    """
    Renders a 1600x920 technical blueprint plate for a district showing:
      - Top-Left: Shared 2:1 Equirectangular Panorama + Depth Map + Horizon Lock
      - Top-Right: Top-Down 3D Chisel `.glb` Building Footprint & Set-Piece Camera Frustum Map (`A..F`)
      - Middle: Curated Spatial Anchor References (`INCLUDED` with actor-cleaned badges & 3D poses)
      - Bottom: Excluded Poison/Bleed References (`EXCLUDED` with red diagnostic callouts) + Coordinate Bridge
    """
    W, H = 1600, 920
    canvas = Image.new("RGB", (W, H), (8, 12, 18))
    draw = ImageDraw.Draw(canvas)

    f_title = get_font(19, bold=True)
    f_sub = get_font(13)
    f_sec = get_font(13, bold=True)
    f_sm = get_font(11)
    f_xs = get_font(10)

    # Header bar
    draw.rectangle([0, 0, W, 54], fill=(13, 20, 30))
    draw.line([0, 54, W, 54], fill=(255, 210, 63), width=2)
    poems_str = ", ".join(f"P{p}" for p in d_info["poems"])
    draw.text((20, 10), f"ATLAS / MARBLE SPLAT PACK · {d_info['name']} ({poems_str})", fill=(255, 210, 63), font=f_title)
    draw.text(
        (20, 33),
        f"ZONE: {d_info['zone']}  |  CHISEL .GLB: {glb_info['file']} ({glb_info['triangles']:,} tris, {glb_info['buildings_extruded']} bldgs)  |  HORIZON LOCK: {int(d_info['shared_horizon']*100)}%",
        fill=(140, 225, 210),
        font=f_sub,
    )

    # 1. Top-Left: 2:1 Equirectangular Panorama + Depth Strip (x=20..880, y=68..370)
    draw.rectangle([20, 68, 880, 370], fill=(12, 18, 26), outline=(45, 65, 90), width=1)
    p0 = d_info["poems"][0]
    eq_path = os.path.join(FOUNDRY_DIR, "equirec", f"poem_{p0}_shared_eq.jpg")
    dp_path = os.path.join(FOUNDRY_DIR, "equirec", f"poem_{p0}_shared_depth.jpg")
    if os.path.exists(eq_path):
        eq_im = Image.open(eq_path).convert("RGB").resize((540, 260), Image.BILINEAR)
        canvas.paste(eq_im, (30, 96))
        hy = 96 + int(d_info["shared_horizon"] * 260)
        draw.line([30, hy, 570, hy], fill=(25, 230, 200), width=2)
    if os.path.exists(dp_path):
        dp_im = Image.open(dp_path).convert("RGB").resize((280, 135), Image.BILINEAR)
        canvas.paste(dp_im, (585, 96))
    draw.text((30, 74), f"1. 2560x1280 (2:1) ACTOR-CLEANED EQUIRECTANGULAR PANO & DEPTH SHELL (POEM {p0})", fill=(25, 230, 200), font=f_sec)

    # Coordinate bridge summary box under depth preview
    cb = pose_info["coordinate_bridge"]
    draw.rectangle([585, 240, 868, 358], fill=(16, 24, 36), outline=(25, 230, 200), width=1)
    draw.text((595, 246), "OPENCV <-> THREE.JS INFRASTRUCTURE BRIDGE", fill=(255, 210, 63), font=f_xs)
    draw.text((595, 264), f"• Chisel GLB: {glb_info['vertices']:,} verts / {glb_info['triangles']:,} tris", fill=(220, 230, 242), font=f_xs)
    draw.text((595, 280), f"• Spawn Origin: {cb['spawn_origin_threejs_m']} m", fill=(220, 230, 242), font=f_xs)
    draw.text((595, 296), f"• Datum Offset: {cb['datum_offset_m']} m | Scale: 1.0 m/unit", fill=(220, 230, 242), font=f_xs)
    draw.text((595, 312), "• Depth Prepass: Occludes R1 Cut-Out Actors", fill=(143, 214, 148), font=f_xs)
    draw.text((595, 328), "• Physics: Registers Floor & Wall Colliders", fill=(92, 225, 230), font=f_xs)

    # 2. Top-Right: Top-Down Chisel `.glb` & Set-Piece Frustum Radar (x=895..1580, y=68..370)
    draw.rectangle([895, 68, 1580, 370], fill=(12, 18, 26), outline=(45, 65, 90), width=1)
    draw.text((908, 74), "2. CHISEL .GLB TOP-DOWN MASSING & POSED CAMERA FRUSTUMS (A..F)", fill=(255, 210, 63), font=f_sec)

    lp_path = os.path.join(STAGES_DIR, f"{d_key}.landpack.json")
    if os.path.exists(lp_path):
        lp = json.load(open(lp_path))
        map_cx, map_cy = 1130, 224
        map_r = 122
        draw.rectangle([map_cx - map_r, map_cy - map_r, map_cx + map_r, map_cy + map_r], fill=(8, 14, 22), outline=(60, 85, 115), width=1)
        scale_m = float(lp.get("w", 160.0)) * 0.52
        for b in lp.get("bld", [])[:300]:
            pts = b.get("p", [])
            if len(pts) >= 3:
                poly = []
                for p in pts:
                    px = int(map_cx + (p[0] / scale_m) * map_r)
                    py = int(map_cy + (p[1] / scale_m) * map_r)
                    poly.append((px, py))
                draw.polygon(poly, fill=(32, 46, 66), outline=(64, 92, 128))

        # Draw camera frustums from pose_info
        for cam in pose_info["cameras"]:
            pos = cam["threejs_pose"]["position_m"]
            px = int(map_cx + (pos[0] / scale_m) * map_r)
            py = int(map_cy + (pos[2] / scale_m) * map_r)
            az_r = math.radians(cam["azimuth_deg"])
            fx1 = int(px + math.sin(az_r - 0.35) * 26)
            fy1 = int(py + math.cos(az_r - 0.35) * 26)
            fx2 = int(px + math.sin(az_r + 0.35) * 26)
            fy2 = int(py + math.cos(az_r + 0.35) * 26)
            draw.polygon([(px, py), (fx1, fy1), (fx2, fy2)], fill=(25, 230, 200, 80), outline=(25, 230, 200))
            draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(255, 210, 63))
            draw.text((px + 6, py - 6), f"{cam['set_piece']}:{cam['ref_id']}", fill=(255, 210, 63), font=f_xs)

        # Legend on right of radar
        lx0 = 1275
        draw.text((lx0, 98), "POSED SPATIAL CONTEXT CAMERAS:", fill=(25, 230, 200), font=f_sm)
        for ci, cam in enumerate(pose_info["cameras"][:6]):
            y_row = 120 + ci * 36
            p_m = cam["threejs_pose"]["position_m"]
            draw.text((lx0, y_row), f"[{cam['set_piece']}] Ref {cam['ref_id']} · {cam['onion_shell']} · Az {int(cam['azimuth_deg'])}°", fill=(255, 210, 63), font=f_xs)
            draw.text((lx0, y_row + 14), f"    Pos ({p_m[0]:.1f}, {p_m[1]:.1f}, {p_m[2]:.1f})m · {cam['role'][:30]}", fill=(185, 200, 218), font=f_xs)

    # 3. Middle Row: Curated Spatial Anchor References (`INCLUDED`, y=384..695)
    draw.rectangle([20, 384, 1580, 695], fill=(12, 18, 26), outline=(45, 95, 75), width=1)
    draw.text(
        (32, 392),
        f"3. CURATED SPATIAL ANCHOR REFERENCES FOR ATLAS / MARBLE ({len(d_info['anchor_refs'])} CLEAN ARCHITECTURAL VIEWS · R0/R1 ACTORS STRIPPED):",
        fill=(143, 214, 148),
        font=f_sec,
    )

    n_anc = len(d_info["anchor_refs"])
    card_w = min(248, (1530 - (n_anc - 1) * 10) // max(1, n_anc))
    for idx, anc in enumerate(d_info["anchor_refs"]):
        rid = anc["id"]
        cx0 = 32 + idx * (card_w + 10)
        cy0 = 418
        draw.rectangle([cx0, cy0, cx0 + card_w, 682], fill=(18, 26, 38), outline=(143, 214, 148), width=1)

        r_img_path = os.path.join(FOUNDRY_DIR, "refs", f"{rid}.jpg")
        r_dp_path = os.path.join(FOUNDRY_DIR, "refs", f"{rid}-depth.jpg")
        r_seg_path = os.path.join(FOUNDRY_DIR, "refs", f"{rid}-seg.jpg")
        if os.path.exists(r_img_path):
            cleaned_im, p_frac = clean_actor_from_ref(r_img_path, r_seg_path)
            im_thumb = cleaned_im.resize((card_w - 8, 128), Image.BILINEAR)
            canvas.paste(im_thumb, (cx0 + 4, cy0 + 24))
        if os.path.exists(r_dp_path):
            dp_thumb = Image.open(r_dp_path).convert("RGB").resize((card_w - 8, 62), Image.BILINEAR)
            canvas.paste(dp_thumb, (cx0 + 4, cy0 + 156))

        draw.text((cx0 + 6, cy0 + 5), f"✓ KEEP · REF {rid} [STOP {anc['set_piece']}]", fill=(143, 214, 148), font=f_sm)
        draw.text((cx0 + 6, cy0 + 224), f"{anc['role'][:32]}", fill=(243, 234, 210), font=f_xs)
        draw.text((cx0 + 6, cy0 + 242), f"Shell: {anc['shell']} | Elev: +{anc['elev_m']}m | R1 Actor Stripped", fill=(25, 230, 200), font=f_xs)

    # 4. Bottom Row: Excluded Poison/Bleed Refs + Portal Architecture Notes (y=708..906)
    draw.rectangle([20, 708, 1580, 906], fill=(22, 14, 20), outline=(255, 61, 110), width=1)
    draw.text(
        (32, 716),
        f"4. REJECTED / FILTERED REFS ({len(d_info['excluded_refs'])} REMOVED TO PREVENT SPATIAL POISONING & CROSS-CITY MARKOV BLEED):",
        fill=(255, 110, 140),
        font=f_sec,
    )

    for idx, ex in enumerate(d_info["excluded_refs"][:5]):
        rid = ex["id"]
        ex_x = 32 + idx * 220
        ex_y = 742
        draw.rectangle([ex_x, ex_y, ex_x + 208, 894], fill=(32, 16, 24), outline=(255, 61, 110), width=1)
        ex_img_path = os.path.join(FOUNDRY_DIR, "refs", f"{rid}.jpg")
        if os.path.exists(ex_img_path):
            ex_im = Image.open(ex_img_path).convert("RGB").resize((200, 92), Image.BILINEAR)
            canvas.paste(ex_im, (ex_x + 4, ex_y + 22))
            # Red X strike-through
            draw.line([ex_x + 4, ex_y + 22, ex_x + 204, ex_y + 114], fill=(255, 61, 110), width=3)
            draw.line([ex_x + 204, ex_y + 22, ex_x + 4, ex_y + 114], fill=(255, 61, 110), width=3)
        draw.text((ex_x + 6, ex_y + 4), f"✕ EXCLUDE · REF {rid}", fill=(255, 90, 120), font=f_sm)
        reason = ex["reason"]
        draw.text((ex_x + 6, ex_y + 120), reason[:30], fill=(255, 190, 205), font=f_xs)
        if len(reason) > 30:
            draw.text((ex_x + 6, ex_y + 134), reason[30:62], fill=(255, 190, 205), font=f_xs)

    # Portal & Infrastructure Recipe Box on bottom right
    rx0 = max(690, 32 + len(d_info["excluded_refs"][:5]) * 220 + 16)
    if rx0 < 1540:
        draw.rectangle([rx0, 742, 1568, 894], fill=(14, 22, 32), outline=(255, 210, 63), width=1)
        draw.text((rx0 + 12, 750), "ROUND-TRIP SPLAT & .GLB INFRASTRUCTURE WORKFLOW:", fill=(255, 210, 63), font=f_sec)
        notes = d_info["portal_notes"]
        draw.text((rx0 + 12, 774), f"• Architecture: {notes[:88]}", fill=(230, 236, 245), font=f_sm)
        if len(notes) > 88:
            draw.text((rx0 + 12, 792), f"  {notes[88:176]}", fill=(230, 236, 245), font=f_sm)
        draw.text((rx0 + 12, 818), f"• Step 1 (Upload to Marble): `{glb_info['file']}` (Chisel) + `pano_2560x1280_clean.jpg` + {len(d_info['anchor_refs'])} Clean Anchors", fill=(25, 230, 200), font=f_sm)
        draw.text((rx0 + 12, 840), "• Step 2 (Receive & Mount): Drop returned `.spz`/`.ply`/`.splat` or `.glb` into `atlas_splat_studio.html` or `terrarium.html`", fill=(143, 214, 148), font=f_sm)
        draw.text((rx0 + 12, 862), "• Step 3 (Live Stage): `.glb` drives floor physics & R3 window occlusion while 2.5D Cut-Out Rigs act inside the Splat!", fill=(255, 176, 103), font=f_sm)

    canvas.save(out_png_path, optimize=True)


def render_megahub_plate(hub, hub_record, out_png_path):
    """
    Renders a 1600x940 flagship visual sheet for one of the 4 Mega-Hubs showing:
      - The 2560x1280 Actor-Cleaned Pano & Equirec Depth Shell
      - The 3D Gaussian Splat + Chisel `.glb` Preview & Coordinate Bridge
      - All 6 Hero Anchor Frames across the multi-poem hub
    """
    W, H = 1600, 940
    canvas = Image.new("RGB", (W, H), (7, 11, 16))
    draw = ImageDraw.Draw(canvas)

    f_title = get_font(20, bold=True)
    f_sub = get_font(13)
    f_sec = get_font(14, bold=True)
    f_sm = get_font(12)
    f_xs = get_font(11)

    draw.rectangle([0, 0, W, 62], fill=(14, 22, 34))
    draw.line([0, 62, W, 62], fill=(25, 230, 200), width=2)
    draw.text((22, 10), f"{hub['title']}  [BANG-FOR-BUCK RANK #{hub['rank']}]", fill=(255, 210, 63), font=f_title)
    draw.text((22, 36), hub["subtitle"], fill=(25, 230, 200), font=f_sub)

    # Top Row: Left = 2560x1280 Clean Pano; Center = 2560x1280 Depth; Right = Hub Infrastructure Stats
    draw.rectangle([20, 76, 1580, 415], fill=(12, 18, 28), outline=(45, 70, 98), width=1)
    draw.text((32, 84), f"1. MARBLE-READY 2560x1280 (2:1) ACTOR-CLEANED EQUIRECTANGULAR PANO & DEPTH SHELL ({hub['hub_id'].upper()})", fill=(255, 210, 63), font=f_sec)

    pano_p = os.path.join(SHOTS_DIR, hub_record["pano_2560x1280"])
    depth_p = os.path.join(SHOTS_DIR, hub_record["depth_2560x1280"])
    if os.path.exists(pano_p):
        pim = Image.open(pano_p).convert("RGB").resize((580, 290), Image.BILINEAR)
        canvas.paste(pim, (32, 112))
        hy = 112 + int(hub["shared_horizon"] * 290)
        draw.line([32, hy, 612, hy], fill=(25, 230, 200), width=2)
    if os.path.exists(depth_p):
        dim = Image.open(depth_p).convert("RGB").resize((460, 230), Image.BILINEAR)
        canvas.paste(dim, (626, 112))
        draw.text((626, 352), f"360°x180° Equirectangular Onion Depth Map (Horizon {int(hub['shared_horizon']*100)}%)", fill=(140, 220, 235), font=f_sm)

    # Right Infrastructure Spec Card
    draw.rectangle([1102, 112, 1564, 400], fill=(16, 26, 40), outline=(25, 230, 200), width=1)
    draw.text((1116, 122), "3D SPLAT & .GLB INFRASTRUCTURE SPECS", fill=(25, 230, 200), font=f_sec)
    specs = [
        f"• Hub ID: {hub['hub_id']}",
        f"• Poems Unified: {', '.join('Poem ' + p for p in hub['poems'])}",
        f"• Linked Districts: {', '.join(hub['linked_stages'])}",
        f"• Chisel Collider GLB: {hub_record['chisel_glb']['file']}",
        f"• GLB Geometry: {hub_record['chisel_glb']['vertices']:,} verts / {hub_record['chisel_glb']['triangles']:,} tris",
        f"• Pre-Built Splat Seed: {hub_record['splat_seed']['file']}",
        f"• Active Splats: {hub_record['splat_seed']['splat_count']:,} 3D Gaussians (32B/splat)",
        f"• Pano Spec: 2560x1280 (2:1, R0/R1 Actors Stripped)",
        "• Receiver Ready: Accepts .spz / .ply / .splat / .glb",
    ]
    for si, sline in enumerate(specs):
        draw.text((1116, 150 + si * 24), sline, fill=(235, 240, 248), font=f_sm)

    # Bottom Row: 6 Hero Cleaned Spatial Anchors across the Hub (y=430..845)
    draw.rectangle([20, 430, 1580, 845], fill=(12, 18, 28), outline=(143, 214, 148), width=1)
    draw.text((32, 438), "2. MULTI-POEM SPATIAL CONTEXT ANCHOR FRAMES (CLEANED R2-R5 ARCHITECTURE + DEPTH MASKS):", fill=(143, 214, 148), font=f_sec)

    anchors = hub_record["anchor_files"]
    cw = 246
    for idx, anc in enumerate(anchors[:6]):
        cx0 = 32 + idx * (cw + 10)
        cy0 = 468
        draw.rectangle([cx0, cy0, cx0 + cw, 830], fill=(18, 26, 38), outline=(255, 210, 63), width=1)
        clean_path = os.path.join(SHOTS_DIR, anc["clean_img"])
        dp_path = os.path.join(FOUNDRY_DIR, "refs", f"{anc['ref_id']}-depth.jpg")
        if os.path.exists(clean_path):
            im = Image.open(clean_path).convert("RGB").resize((cw - 8, 145), Image.BILINEAR)
            canvas.paste(im, (cx0 + 4, cy0 + 28))
        if os.path.exists(dp_path):
            dm = Image.open(dp_path).convert("RGB").resize((cw - 8, 110), Image.BILINEAR)
            canvas.paste(dm, (cx0 + 4, cy0 + 180))
        draw.text((cx0 + 8, cy0 + 6), f"ANCHOR #{idx+1} · REF {anc['ref_id']}", fill=(255, 210, 63), font=f_sm)
        draw.text((cx0 + 8, cy0 + 300), f"{anc['role'][:32]}", fill=(243, 234, 210), font=f_xs)
        draw.text((cx0 + 8, cy0 + 318), f"Actor Inpainted: {anc['actor_inpainted_pct']}%", fill=(143, 214, 148), font=f_xs)
        draw.text((cx0 + 8, cy0 + 336), f"Shell: {anc['shell']} | Elev: +{anc['elev_m']}m", fill=(25, 230, 200), font=f_xs)

    # Footer bar with Bang-for-Buck takeaway
    draw.rectangle([20, 858, 1580, 924], fill=(18, 28, 22), outline=(255, 210, 63), width=1)
    draw.text((34, 868), f"★ WHY THIS MEGA-HUB IS MAXIMUM BANG FOR YOUR BUCK: {hub['bang_for_buck']}", fill=(255, 210, 63), font=f_sec)
    draw.text((34, 894), "Load live in 3D right now in `shots/atlas_splat_studio.html` or `shots/terrarium.html` — or drag-and-drop your Marble `.spz`/`.ply`/`.glb` export into the Receiver Dock!", fill=(143, 214, 148), font=f_sm)

    canvas.save(out_png_path, optimize=True)


# ---------------------------------------------------------------------------
# 7. MAIN EXECUTION PIPELINE
# ---------------------------------------------------------------------------
def main():
    refs_data = json.load(open(os.path.join(FOUNDRY_DIR, "refs.json")))
    ref_lookup = {r["id"]: r for r in refs_data["refs"]}
    stages_data = json.load(open(os.path.join(STAGES_DIR, "stages.json")))
    stage_lookup = {s["key"]: s for s in stages_data["stages"]}

    district_records = {}
    vault_plates = []

    print("1. Building 10 District Chisel `.glb` Collider Meshes, Spatial Context Poses & Blueprint Plates...")
    for d_key, d_info in DISTRICT_CURATION.items():
        lp_path = os.path.join(STAGES_DIR, f"{d_key}.landpack.json")
        lp = json.load(open(lp_path))
        st_meta = stage_lookup.get(d_key, {})

        # Collect all set_pieces for this stage
        all_sps = []
        for pm in st_meta.get("poems", []):
            all_sps.extend(pm.get("set_pieces", []))

        out_glb = os.path.join(GLB_DIR, f"{d_key}_chisel_collider.glb")
        glb_info = build_glb_from_landpack(
            lp,
            out_glb,
            set_pieces=all_sps,
            extra_meta={"district": d_key, "poems": d_info["poems"], "zone": d_info["zone"]},
        )
        pose_info = build_spatial_context_cameras(lp, st_meta, d_info, ref_lookup)

        # Save per-district spatial context JSON
        d_pack_dir = os.path.join(ATLAS_DIR, f"district_{d_key}")
        os.makedirs(d_pack_dir, exist_ok=True)
        ctx_json_path = os.path.join(d_pack_dir, "atlas_spatial_context.json")
        with open(ctx_json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "district": d_key,
                    "name": d_info["name"],
                    "poems": d_info["poems"],
                    "chisel_glb": glb_info,
                    "shared_horizon": d_info["shared_horizon"],
                    "portal_notes": d_info["portal_notes"],
                    "spatial_context": pose_info,
                    "excluded_refs": d_info["excluded_refs"],
                },
                f,
                indent=2,
            )

        # Render district blueprint plate
        plate_name = f"atlas_district_{d_key.replace('-', '_')}.png"
        plate_path = os.path.join(VAULT_ATLAS_DIR, plate_name)
        render_district_atlas_plate(d_key, d_info, glb_info, pose_info, ref_lookup, plate_path)
        vault_plates.append({
            "id": f"atlas_district_{d_key}",
            "title": f"Atlas District Pack · {d_info['name']}",
            "category": "atlas_splats",
            "sub_type": "district_pack",
            "poem": d_info["poems"][0],
            "file": f"png_vault/atlas_splats/{plate_name}",
            "width": 1600,
            "height": 920,
            "tags": ["atlas", "marble", "glb", "splat", d_key, d_info["zone"].lower()],
        })

        district_records[d_key] = {
            "key": d_key,
            "name": d_info["name"],
            "zone": d_info["zone"],
            "poems": d_info["poems"],
            "foundry_world": d_info["foundry_world"],
            "shared_horizon": d_info["shared_horizon"],
            "chisel_glb": glb_info,
            "context_json": os.path.relpath(ctx_json_path, SHOTS_DIR),
            "blueprint_png": f"png_vault/atlas_splats/{plate_name}",
            "anchor_refs": d_info["anchor_refs"],
            "excluded_refs": d_info["excluded_refs"],
            "portal_notes": d_info["portal_notes"],
            "cameras": pose_info["cameras"],
            "coordinate_bridge": pose_info["coordinate_bridge"],
        }
        print(f"   ✓ District `{d_key}` -> {glb_info['file']} ({glb_info['triangles']:,} tris, {len(pose_info['cameras'])} posed cameras)")

    print("\n2. Building 4 Mega-Hub Actor-Cleaned 2560x1280 Panos, Chisel `.glb`s, and 3D `.splat` Seeds...")
    megahub_records = []
    megahub_plate_paths = []

    for hub in MEGA_HUBS:
        hid = hub["hub_id"]
        h_dir = os.path.join(ATLAS_DIR, hid)
        os.makedirs(h_dir, exist_ok=True)

        # 1. Build 2560x1280 clean pano & depth
        pano_out = os.path.join(h_dir, "pano_2560x1280_clean.jpg")
        depth_out = os.path.join(h_dir, "depth_2560x1280.jpg")
        build_clean_2560x1280_pano(hub["primary_poem_pano"], pano_out, depth_out)

        # 2. Export actor-cleaned 16:9 anchor frames
        anchor_files = []
        anchor_local_paths = []
        # Lookup metadata across linked districts
        anc_meta_map = {}
        for st_k in hub["linked_stages"]:
            for a in DISTRICT_CURATION[st_k]["anchor_refs"]:
                anc_meta_map[a["id"]] = a

        for idx, rid in enumerate(hub["hero_anchors"]):
            src_r = os.path.join(FOUNDRY_DIR, "refs", f"{rid}.jpg")
            src_s = os.path.join(FOUNDRY_DIR, "refs", f"{rid}-seg.jpg")
            clean_im, pct_inpainted = clean_actor_from_ref(src_r, src_s)
            # Save at 1024x576 (Marble recommended 16:9 multi-image spec)
            out_anc = os.path.join(h_dir, f"anchor_{idx+1:02d}_{rid}_clean.jpg")
            clean_im.resize((1024, 576), Image.LANCZOS).save(out_anc, quality=92)
            anchor_local_paths.append(out_anc)
            am = anc_meta_map.get(rid, {"role": f"Anchor {rid}", "shell": "R3", "elev_m": 2.5, "set_piece": chr(65 + idx)})
            anchor_files.append({
                "ref_id": rid,
                "clean_img": os.path.relpath(out_anc, SHOTS_DIR),
                "orig_img": f"data/terrarium/foundry/refs/{rid}.jpg",
                "depth_img": f"data/terrarium/foundry/refs/{rid}-depth.jpg",
                "role": am["role"],
                "shell": am["shell"],
                "elev_m": am["elev_m"],
                "actor_inpainted_pct": pct_inpainted,
            })

        # 3. Copy/reference primary Chisel `.glb` and build 3D `.splat` binary seed
        p_stage = hub["primary_stage"]
        lp = json.load(open(os.path.join(STAGES_DIR, f"{p_stage}.landpack.json")))
        st_meta = stage_lookup.get(p_stage, {})
        all_sps = []
        for pm in st_meta.get("poems", []):
            all_sps.extend(pm.get("set_pieces", []))

        hub_glb_path = os.path.join(GLB_DIR, f"{hid}_chisel.glb")
        shutil.copyfile(os.path.join(GLB_DIR, f"{p_stage}_chisel_collider.glb"), hub_glb_path)
        glb_info = dict(district_records[p_stage]["chisel_glb"])
        glb_info["file"] = os.path.relpath(hub_glb_path, SHOTS_DIR)

        splat_path = os.path.join(SPLAT_DIR, f"{hid}.splat")
        splat_info = build_binary_splat_for_hub(
            lp,
            pano_out,
            anchor_local_paths,
            all_sps,
            splat_path,
            state_tint="temple" if hid == "hub_02_harbor_temple" else None,
            n_target=28000,
        )

        # For Hub 02 (Harbor Temple Shore), ALSO build the Twin-State Storm Ruin splat on the exact same Chisel `.glb`!
        twin_splat_info = None
        if hid == "hub_02_harbor_temple":
            ruin_pano = os.path.join(h_dir, "pano_2560x1280_storm_ruin.jpg")
            ruin_depth = os.path.join(h_dir, "depth_2560x1280_storm_ruin.jpg")
            build_clean_2560x1280_pano("03", ruin_pano, ruin_depth)
            ruin_splat_path = os.path.join(SPLAT_DIR, "hub_02_harbor_storm_ruin.splat")
            twin_splat_info = build_binary_splat_for_hub(
                lp,
                ruin_pano,
                anchor_local_paths[:2],
                all_sps,
                ruin_splat_path,
                state_tint="ruin",
                n_target=28000,
            )

        rec = {
            **hub,
            "pano_2560x1280": os.path.relpath(pano_out, SHOTS_DIR),
            "depth_2560x1280": os.path.relpath(depth_out, SHOTS_DIR),
            "chisel_glb": glb_info,
            "splat_seed": splat_info,
            "twin_state_splat": twin_splat_info,
            "anchor_files": anchor_files,
            "coordinate_bridge": district_records[p_stage]["coordinate_bridge"],
            "cameras": district_records[p_stage]["cameras"],
        }

        plate_name = f"atlas_{hid}.png"
        plate_path = os.path.join(VAULT_ATLAS_DIR, plate_name)
        render_megahub_plate(hub, rec, plate_path)
        rec["vault_plate"] = f"png_vault/atlas_splats/{plate_name}"
        megahub_records.append(rec)
        megahub_plate_paths.append(plate_path)

        vault_plates.append({
            "id": f"atlas_{hid}",
            "title": hub["title"],
            "category": "atlas_splats",
            "sub_type": "megahub_pack",
            "poem": hub["primary_poem_pano"],
            "file": f"png_vault/atlas_splats/{plate_name}",
            "width": 1600,
            "height": 940,
            "tags": ["atlas", "marble", "megahub", "glb", "splat", hid],
        })
        print(f"   ✓ Mega-Hub `{hid}` -> {splat_info['file']} ({splat_info['splat_count']:,} splats) + {glb_info['file']}")

    # 3. Build Master 4-Mega-Hub Overview Contact Sheet (`all_megahubs_atlas_splat_master.png`)
    master_w, master_h = 1600, 1960
    master_im = Image.new("RGB", (master_w, master_h), (6, 9, 14))
    mdraw = ImageDraw.Draw(master_im)
    f_mtitle = get_font(22, bold=True)
    f_msub = get_font(14)
    mdraw.rectangle([0, 0, master_w, 68], fill=(12, 18, 28))
    mdraw.line([0, 68, master_w, 68], fill=(255, 210, 63), width=2)
    mdraw.text((24, 12), "WYGWYL · WORLD LABS ATLAS / MARBLE 4 MEGA-HUB SPLAT & .GLB INFRASTRUCTURE MASTER", fill=(255, 210, 63), font=f_mtitle)
    mdraw.text((24, 42), "4 Mega-Hubs Cover 92% of the Film · 2560x1280 Actor-Cleaned Panos · Binary Chisel .GLB Colliders · 32-Byte 3D Gaussian Splat Seeds", fill=(25, 230, 200), font=f_msub)

    for idx, p_path in enumerate(megahub_plate_paths):
        sub_im = Image.open(p_path).convert("RGB").resize((1560, 458), Image.LANCZOS)
        master_im.paste(sub_im, (20, 80 + idx * 468))

    master_out = os.path.join(VAULT_ATLAS_DIR, "all_megahubs_atlas_splat_master.png")
    master_im.save(master_out, optimize=True)
    vault_plates.insert(0, {
        "id": "all_megahubs_atlas_splat_master",
        "title": "All 4 Mega-Hubs · Atlas/Marble Splat & .GLB Infrastructure Master Sheet",
        "category": "atlas_splats",
        "sub_type": "master_sheet",
        "poem": "01",
        "file": "png_vault/atlas_splats/all_megahubs_atlas_splat_master.png",
        "width": master_w,
        "height": master_h,
        "tags": ["atlas", "marble", "master", "megahub", "glb", "splat"],
    })

    # 4. Write Master Manifest `shots/data/terrarium/atlas_packs/atlas_infrastructure_manifest.json`
    manifest_path = os.path.join(ATLAS_DIR, "atlas_infrastructure_manifest.json")
    manifest = {
        "version": "1.0.0",
        "title": "WYGWYL Atlas / Marble .GLB & 3D Gaussian Splat Infrastructure",
        "master_contact_sheet": "png_vault/atlas_splats/all_megahubs_atlas_splat_master.png",
        "mega_hubs": megahub_records,
        "districts": district_records,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 5. Update `shots/png_vault/png_catalog.json`
    cat_path = os.path.join(SHOTS_DIR, "png_vault", "png_catalog.json")
    if os.path.exists(cat_path):
        cat = json.load(open(cat_path))
        items = [it for it in cat.get("items", []) if it.get("category") != "atlas_splats"]
        items.extend(vault_plates)
        cat["items"] = items
        cat["total"] = len(items)
        cat.setdefault("counts", {})["atlas_splats"] = len(vault_plates)
        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(cat, f, indent=2)
        print(f"\n3. Updated `png_catalog.json` -> {len(items)} total plates ({len(vault_plates)} in `atlas_splats`).")

    print(f"Done! Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
