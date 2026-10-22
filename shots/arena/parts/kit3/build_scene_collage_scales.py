#!/usr/bin/env python3
"""
build_scene_collage_scales.py
=============================
Multiplane Set Architecture, Cohesive Set-Piece Ensembles, Water/Portal/Vehicle
Assembly & Scene Scale Solver for the WYGWYL Cut-Out Animation Suite
(Poems 01–14, 80 Scenes, 252 Shots).

Generates & Updates:
  1. shots/arena/parts/kit3/release_v2/scene_collage_plans.json
  2. shots/arena/parts/kit3/release_v2/wygwyl_atlas_manifest.json (merges
     `scene_collage_plans`, `scenes[].stage_layers`, `scenes[].staged_placements`,
     `scenes[].ensembles`, and `poems[].scenes[]`).

Creative & Structural Principles:
  - Every scene (P01-S01 .. P14-S06) is composed of **3 to 4 Cohesive Set-Piece
    Ensembles (`ensembles: [...]`)** with **6 to 9 thoughtfully co-located cut
    pieces** (`stage_layers` / `staged_placements`) and **35%–45% breathable
    negative space**.
  - True Parent-Child Co-Location:
      * `car_ensemble`: `02.props.car__p01` chassis + front/rear spinning wheels
        (`p05`, `p06` at `car_x ± 0.11, y=0.89`) + window (`p03`) + seated parents
        (`parents.02.car-argument__p01`) + headlight beam (`02.fx.lights-iris__p01`).
      * `motorcycle_ensemble`: `10.props.bike-skeleton__p01` / `11.props.parked-motorcycle__p01`
        frame + rear/front spinning wheels (`p07`, `p09` at `bike_x ± 0.08, y=0.89`)
        + headlight cone (`10.fx.ride-light__p02`) + mounted rider (`poet.10.main-poses__p01`).
      * `water_shore_ensemble` (39 scenes across Poems 01, 03, 04, 05, 06, 08, 09,
        10, 11, 12, 13, 14): multiplane water horizon stacking `SEA / POOL.WATER`
        (`P5 y=0.78`), `WAVE.1` (`P4 y=0.79`), `WAVE.2` (`P3 y=0.84`), `WAVE.3`
        (`P1 y=0.91`), `ASH.DARK / POOL.RIM` (`P4 y=0.93`), plus assembled
        `13.props.planet-boats` (hull + mast + sail + reflection at `boat_x, y=0.81`
        and `JUPITER` + `MOONS` in the upper sky `y=0.25..0.31`).
      * `portal_window_tv_ensemble`: co-located `WINDOW.WALL` + `WINDOW.VIEW`
        (other world behind aperture) + `CURTAIN.L` + `CURTAIN.R` + `BLINDS`;
        `06.set.atlantis_gate` portal with `06.set.crystal_tree_hall` glowing inside;
        `03.props.rose-window` with stained-glass petals and flying `02.props.tambourine`;
        `14.props.door` portal opening into the vintage ballroom.
      * `interior_furniture_ensemble`, `dj_booth_ensemble`, `phone_booth_ensemble`,
        `cafe_table_ensemble`: `LAMP.SHADE` stacked directly on `LAMP.BASE` at the
        same `x`; cafe tabletop + stem + 3-prong base + espresso cup + chair;
        DJ booth + left/right spinning platters flanked by left/right pulsing
        speakers and dancing club extras; phone booth frame + door + payphone +
        ringing waves.
      * Kinetic Hero Props: `beating_heart_ensemble` + `jointed_hands_ensemble`
        (like the Weave hand test), `hourglass_ensemble` (frame + bulbs + falling
        sand), `faith_bloom_ensemble` (stem + golden flowerhead on top),
        `angel_wings_ensemble` (left & right wings pinned symmetrically to the
        Angel's shoulder blades behind `08.cast.angel.main-poses`), and
        `clouds_light_ensemble`.
"""

from __future__ import annotations

import json
import math
import pathlib
import re
from typing import Any, Dict, List, Optional, Tuple


SHOTS_DIR = pathlib.Path(__file__).resolve().parents[3]
RELEASE_DIR = SHOTS_DIR / "arena" / "parts" / "kit3" / "release_v2"
OUTPUT_PATH = RELEASE_DIR / "scene_collage_plans.json"
MANIFEST_PATH = RELEASE_DIR / "wygwyl_atlas_manifest.json"


# ---------------------------------------------------------------------------
# 1. Semantic Physical Classes & Canonical Multiplane Calibration
# ---------------------------------------------------------------------------

SEMANTIC_CLASS_SPECS: Dict[str, Dict[str, Any]] = {
    "sky_canopy": {
        "plane": "P6",
        "z": 6.0,
        "scale_range": [0.95, 1.05],
        "default_scale": 0.98,
        "y_range": [0.95, 1.00],
        "default_y": 0.98,
        "scale_cm": 1200,
        "description": "Sky plates, cloud canopies, archive sky wipes, ballroom ceilings",
    },
    "horizon_vista": {
        "plane": "P5",
        "z": 3.8,
        "scale_range": [0.72, 0.92],
        "default_scale": 0.84,
        "y_range": [0.76, 0.84],
        "default_y": 0.80,
        "scale_cm": 800,
        "description": "Skyline strips, distant ridges, sea horizons, city void tower vistas",
    },
    "building_facade": {
        "plane": "P4",
        "z": 2.4,
        "scale_range": [0.46, 0.78],
        "default_scale": 0.64,
        "y_range": [0.84, 0.92],
        "default_y": 0.88,
        "scale_cm": 450,
        "description": "Exterior walls, market stalls, church naves, tower slabs, plaza colonnades",
    },
    "room_wall": {
        "plane": "P4",
        "z": 2.4,
        "scale_range": [0.48, 0.78],
        "default_scale": 0.66,
        "y_range": [0.84, 0.92],
        "default_y": 0.88,
        "scale_cm": 320,
        "description": "Bedroom walls, hallways, apartment interiors, elevator shafts, temple halls",
    },
    "door_window_arch": {
        "plane": "P4",
        "z": 2.4,
        "scale_range": [0.34, 0.74],
        "default_scale": 0.56,
        "y_range": [0.46, 0.92],
        "default_y": 0.84,
        "scale_cm": 210,
        "description": "Sash windows, fire-escape frames, arches, gates, doorways, rose windows, mirrors",
    },
    "stair_bridge_viaduct": {
        "plane": "P4",
        "z": 2.4,
        "scale_range": [0.22, 0.76],
        "default_scale": 0.58,
        "y_range": [0.78, 0.93],
        "default_y": 0.89,
        "scale_cm": 380,
        "description": "Fire escapes, spiral stairs, stone steps, aqueduct bridges, water wave swells, shore banks",
    },
    "large_furniture": {
        "plane": "P3",
        "z": 1.4,
        "scale_range": [0.24, 0.46],
        "default_scale": 0.36,
        "y_range": [0.82, 0.90],
        "default_y": 0.87,
        "scale_cm": 180,
        "description": "Beds, dressers, pews, consoles, DJ booths, tables, benches, cars, motorcycles, phone booths",
    },
    "medium_prop": {
        "plane": "P3",
        "z": 1.4,
        "scale_range": [0.12, 0.28],
        "default_scale": 0.20,
        "y_range": [0.24, 0.91],
        "default_y": 0.86,
        "scale_cm": 75,
        "description": "Suitcases, TVs, chairs, lamps, boats, wheels, speakers, ice basins, hourglasses",
    },
    "handheld_prop": {
        "plane": "P3",
        "z": 1.35,
        "scale_range": [0.08, 0.15],
        "default_scale": 0.11,
        "y_range": [0.48, 0.89],
        "default_y": 0.64,
        "scale_cm": 18,
        "description": "Vape pens, phones, tambourines, coffee cups, coins, letters, rings, heart chambers, flower blooms",
    },
    "full_figure_adult": {
        "plane": "P2",
        "z": 1.0,
        "scale_range": [0.50, 0.60],
        "default_scale": 0.54,
        "y_range": [0.82, 0.93],
        "default_y": 0.91,
        "scale_cm": 175,
        "description": "Standing, walking, or dancing full-body adult characters",
    },
    "full_figure_child": {
        "plane": "P2",
        "z": 1.0,
        "scale_range": [0.35, 0.41],
        "default_scale": 0.38,
        "y_range": [0.86, 0.93],
        "default_y": 0.91,
        "scale_cm": 120,
        "description": "Young Poet, Ghost Child, Child Traveler (~0.68x adult height)",
    },
    "crouched_or_prone_figure": {
        "plane": "P2",
        "z": 1.0,
        "scale_range": [0.18, 0.40],
        "default_scale": 0.32,
        "y_range": [0.78, 0.93],
        "default_y": 0.89,
        "scale_cm": 105,
        "description": "Crouching, sitting, car-seated, bike-mounted, kneeling, or falling figures",
    },
    "limb_or_head_detail": {
        "plane": "P2",
        "z": 1.0,
        "scale_range": [0.11, 0.28],
        "default_scale": 0.16,
        "y_range": [0.52, 0.82],
        "default_y": 0.65,
        "scale_cm": 28,
        "description": "Articulated jointed hands, eye apertures, angel wings pinned to shoulders",
    },
    "atmospheric_fx": {
        "plane": "P1",
        "z": 0.45,
        "scale_range": [0.14, 0.38],
        "default_scale": 0.24,
        "y_range": [0.22, 0.92],
        "default_y": 0.72,
        "scale_cm": 140,
        "description": "Headlight beams, sun/cloud rays, near-shore wave foam, phone ring waves, vape haze",
    },
    "typography_banner": {
        "plane": "P1",
        "z": 0.45,
        "scale_range": [0.18, 0.36],
        "default_scale": 0.26,
        "y_range": [0.24, 0.76],
        "default_y": 0.42,
        "scale_cm": 90,
        "description": "Falling word dashes, NEVERMORE cards, star nameplates, film-frame apertures",
    },
}

CAMERA_FRAMING_SPECS: Dict[str, Dict[str, Any]] = {
    "extreme_wide": {
        "actor_mult": 0.96,
        "prop_mult": 0.94,
        "arch_mult": 0.95,
        "focal_length_mm": 21,
        "description": "Architectural / water horizon dominance; multiplane set breathes around ensembles",
    },
    "wide": {
        "actor_mult": 0.98,
        "prop_mult": 0.97,
        "arch_mult": 0.98,
        "focal_length_mm": 28,
        "description": "Full room or harbor proscenium; 3–4 ensembles clearly staged with 40% open air",
    },
    "medium_wide": {
        "actor_mult": 1.00,
        "prop_mult": 1.00,
        "arch_mult": 1.00,
        "focal_length_mm": 35,
        "description": "Canonical stage framing; balanced dialogue between actors, portals, and set pieces",
    },
    "medium": {
        "actor_mult": 1.03,
        "prop_mult": 1.04,
        "arch_mult": 1.02,
        "focal_length_mm": 50,
        "description": "Intimate ensemble focus; kinetic hero props and gestures read with tactile clarity",
    },
    "close": {
        "actor_mult": 1.06,
        "prop_mult": 1.08,
        "arch_mult": 1.04,
        "focal_length_mm": 75,
        "description": "Tactile focus on hands, beating heart, hourglass, or eye aperture against deeper planes",
    },
}


# ---------------------------------------------------------------------------
# 2. Sheet & Character Pose Classification Tables
# ---------------------------------------------------------------------------

HANDHELD_PROP_SHEETS: Dict[str, Tuple[int, float]] = {
    "01.props.handheld": (16, 0.11),
    "02.props.tambourine": (25, 0.12),
    "03.props.tambourine-broken": (15, 0.10),
    "03.props.gifts-bread-cups": (18, 0.11),
    "04.props.heart": (12, 0.12),
    "04.props.faith-blooms": (16, 0.12),
    "06.props.lantern-candle-guitar": (28, 0.13),
    "07.props.mic-daisy-rings": (18, 0.11),
    "11.props.inlays-lantern": (22, 0.12),
    "11.props.journal": (24, 0.12),
    "12.props.hand-hourglass": (20, 0.12),
    "12.props.snapshot": (15, 0.10),
    "13.props.five-letters": (22, 0.11),
    "13.props.personal": (14, 0.10),
    "14.props.reel": (20, 0.12),
}

LARGE_FURNITURE_PROP_SHEETS: Dict[str, Tuple[int, float]] = {
    "02.props.car": (480, 0.28),
    "07.props.dj-decks": (125, 0.34),
    "09.props.phonebooth": (220, 0.42),
    "10.props.bike-ride-views": (210, 0.32),
    "10.props.bike-skeleton": (210, 0.30),
    "10.props.tree-dawn-sign": (240, 0.40),
    "11.props.parked-motorcycle": (210, 0.30),
    "13.props.cafe": (130, 0.32),
    "13.props.rail-tide-awning": (140, 0.38),
    "07.hero.house.furniture": (160, 0.36),
    "13.set.church_pews": (300, 0.38),
}

DOOR_WINDOW_PROP_SHEETS: Dict[str, Tuple[int, float]] = {
    "01.props.window": (150, 0.56),
    "02.props.window": (150, 0.56),
    "03.props.rose-window": (180, 0.48),
    "12.props.niche-porch": (200, 0.56),
    "13.props.distant-window": (150, 0.54),
    "14.props.door": (210, 0.58),
    "03.set.chapel_side_doors": (220, 0.58),
    "05.set.winged_marble_gate": (320, 0.62),
    "06.set.atlantis_gate": (350, 0.62),
}

BUILDING_PROP_SHEETS: Dict[str, Tuple[int, float]] = {
    "11.props.ruin": (280, 0.58),
    "11.props.temple.arrival.beams": (300, 0.56),
    "11.props.temple.arrival.courses-columns": (300, 0.58),
    "11.props.temple.arrival.roof-finial": (300, 0.54),
    "11.props.temple.states": (320, 0.62),
    "11.props.temple.whole": (320, 0.62),
}

LIMB_DETAIL_PROP_SHEETS: Dict[str, Tuple[int, float]] = {
    "02.props.poet-eye-aperture": (24, 0.22),
    "04.props.poet-jointed-hands": (22, 0.15),
    "05.props.fingerprint": (35, 0.24),
    "08.cast.angel.wings": (140, 0.27),
}

TYPOGRAPHY_SHEETS: Dict[str, Tuple[int, float]] = {
    "01.fx.haze-words": (75, 0.26),
    "04.props.word-shore": (85, 0.25),
    "05.props.star-names": (60, 0.24),
    "12.fx.words-wind": (80, 0.26),
    "14.fx.filmframe": (110, 0.30),
}

BODY_PART_ONLY_SHEETS = {
    "woman.09.mother.body",
    "parents.02.father_02.body",
    "parents.02.mother_02.body",
    "atlantis.06.citizen_1.body",
    "atlantis.06.citizen_2.body",
    "atlantis.06.elder_1.body",
    "atlantis.06.elder_2.body",
    "atlantis.06.gatekeeper.body",
    "atlantis.06.traveler_1.body",
    "atlantis.06.traveler_2.body",
    "atlantis.06.child_traveler.body",
    "08.cast.angel.body",
    "08.cast.club_1.body",
    "08.cast.club_2.body",
    "08.cast.club_dress.body",
    "08.cast.club_jacket.body",
    "08.cast.club_shirt.body",
    "party.07.action.dj_cyber.torso-parts",
    "party.07.action.party_guest.torso-parts",
    "party.dj_cyber.compact-core",
    "party.party_guest.compact-core",
    "poet.black_tshirt.compact-core",
    "poet.tracksuit.31_components",
    "woman.13.body",
}

CURATED_POET_POSES: Dict[int, List[Tuple[str, str, str, str]]] = {
    1: [
        ("poet.01.main-poses__p01", "full_figure_adult", "poet_black_tshirt", "Poet (Black T-Shirt) · Reading Poem Aloud"),
        ("poet.01.main-poses__p02", "full_figure_adult", "poet_black_tshirt", "Poet (Black T-Shirt) · Crossing Bedroom to Window"),
        ("poet.01.main-poses__p03", "full_figure_adult", "poet_black_tshirt", "Poet (Black T-Shirt) · Fire-Escape Witness"),
        ("poet.01.main-poses__p04", "crouched_or_prone_figure", "poet_black_tshirt", "Poet (Black T-Shirt) · Plunging Through Void"),
    ],
    2: [
        ("poet.02.main-poses__p01", "full_figure_adult", "poet_black_tshirt", "Poet · Standing in Flashing Lights"),
        ("poet.02.main-poses__p02", "full_figure_adult", "poet_black_tshirt", "Poet · Stepping Toward Mirror Portal"),
        ("poet.02.main-poses__p03", "crouched_or_prone_figure", "poet_black_tshirt", "Poet · Kneeling by Living Room Window"),
    ],
    3: [
        ("poet.03.main-poses__p01", "full_figure_adult", "poet_black_tshirt", "Poet · Chapel Nave Witness"),
        ("poet.03.main-poses__p02", "full_figure_adult", "poet_black_tshirt", "Poet · Reaching Toward Rose Window"),
        ("poet.03.main-poses__p03", "crouched_or_prone_figure", "poet_black_tshirt", "Poet · Kneeling by Shattered Tambourine on Shore"),
    ],
    4: [
        ("poet.04.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Washed Ashore Stand"),
        ("poet.04.main-poses__p02", "crouched_or_prone_figure", "poet_tracksuit_31", "Poet (Tracksuit) · Kneeling with Beating Heart"),
        ("poet.04.main-poses__p03", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Climbing Incline Trail"),
    ],
    5: [
        ("poet.05.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Walking in Ancestor Parade"),
        ("poet.05.main-poses__p02", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Naming the Stars"),
    ],
    6: [
        ("poet.06.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Atlantis Causeway Arrival"),
        ("poet.06.main-poses__p02", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Offering Admission Coin"),
    ],
    7: [
        ("poet.07.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · House Party Witness"),
        ("poet.07.main-poses__p02", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Listening to DJ Turn Me Up"),
    ],
    8: [
        ("poet.08.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Rooftop Club Stand"),
        ("poet.08.main-poses__p02", "crouched_or_prone_figure", "poet_tracksuit_31", "Poet (Tracksuit) · Receiving Cleansing Water"),
    ],
    9: [
        ("poet.09.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Harbor Sidewalk by Phone Booth"),
        ("poet.09.main-poses__p02", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Walking East Along Harbor"),
    ],
    10: [
        ("poet.10.main-poses__p02", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Inspecting Parked Motorcycle"),
        ("poet.10.main-poses__p01", "crouched_or_prone_figure", "poet_tracksuit_31", "Poet (Tracksuit) · Mounted Motorcycle Rider"),
    ],
    11: [
        ("poet.11.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Raising White Temple on Shore"),
        ("poet.11.main-poses__p02", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Walking on Calm Sea"),
    ],
    12: [
        ("poet.12.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Welcoming Friends in Temple"),
        ("poet.12.main-poses__p02", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Holding Burning Hourglass"),
    ],
    13: [
        ("poet.13.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Harbor Cafe Table Witness"),
        ("poet.13.main-poses__p02", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit) · Watching Orbits & Sailboats"),
    ],
    14: [
        ("poet.14.muse-dance__p01", "full_figure_adult", "poet_tracksuit_31", "Poet & Muse · Entwined Waltz"),
        ("poet.14.exit__p08", "full_figure_adult", "poet_tracksuit_31", "Poet · Stepping Through Vintage Door"),
    ],
}


# ---------------------------------------------------------------------------
# 3. Aspect Ratio & Physical Scale Helpers
# ---------------------------------------------------------------------------

def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def aspect_compensation_multiplier(width: int, height: int, sem_class: str) -> float:
    if height <= 0 or width <= 0:
        return 1.0
    ar = width / float(height)
    if sem_class in ("full_figure_adult", "full_figure_child"):
        if ar > 0.85:
            return max(0.68, min(1.0, 1.0 / math.sqrt(1.0 + 0.85 * ((ar - 0.55) ** 2))))
        return 1.0
    if sem_class == "crouched_or_prone_figure":
        if ar > 0.75:
            return max(0.58, min(0.95, 1.0 / math.sqrt(1.0 + 1.15 * ((ar - 0.50) ** 2))))
        return 0.92
    return 1.0


def classify_part(
    sheet: Dict[str, Any],
    part: Dict[str, Any],
    ocr_labels_by_part: Dict[str, str],
) -> Dict[str, Any]:
    sid = sheet["id"]
    pid = part["id"]
    subfolder = sheet.get("subfolder", "")
    kind = sheet.get("kind", "")
    w = int(part.get("width", 100))
    h = int(part.get("height", 100))
    ar = w / float(max(1, h))
    bbox = part.get("bbox_sheet", [0, 0, w, h])
    sheet_w = max(1, int(sheet.get("width", 1600)))
    sheet_h = max(1, int(sheet.get("height", 1000)))
    rel_y = bbox[1] / float(sheet_h)
    rel_h = bbox[3] / float(sheet_h)
    rel_w = bbox[2] / float(sheet_w)
    ocr_label = ocr_labels_by_part.get(pid, part.get("label", ""))
    low_sid = sid.lower()
    low_lbl = (ocr_label or "").lower()

    sem_class = "medium_prop"
    scale_cm = 75
    base_scale: Optional[float] = None

    if subfolder == "05_PAINTED_EFFECTS" or kind in ("fx", "painted_fx"):
        if sid in TYPOGRAPHY_SHEETS or any(k in low_lbl for k in ("word", "letter", "frame", "aperture")):
            sem_class = "typography_banner"
            scale_cm, base_scale = TYPOGRAPHY_SHEETS.get(sid, (85, 0.26))
        elif any(k in low_sid for k in ("sky", "clouds", "light")) and rel_w > 0.45 and ar > 2.2:
            sem_class = "sky_canopy"
            scale_cm, base_scale = 1200, 0.96
        else:
            sem_class = "atmospheric_fx"
            scale_cm, base_scale = 140, 0.26
    elif subfolder == "03_PROPS" or kind == "props":
        if sid in HANDHELD_PROP_SHEETS:
            sem_class = "handheld_prop"
            scale_cm, base_scale = HANDHELD_PROP_SHEETS[sid]
        elif sid in LIMB_DETAIL_PROP_SHEETS:
            sem_class = "limb_or_head_detail"
            scale_cm, base_scale = LIMB_DETAIL_PROP_SHEETS[sid]
        elif sid in LARGE_FURNITURE_PROP_SHEETS:
            sem_class = "large_furniture"
            scale_cm, base_scale = LARGE_FURNITURE_PROP_SHEETS[sid]
        elif sid in DOOR_WINDOW_PROP_SHEETS:
            sem_class = "door_window_arch"
            scale_cm, base_scale = DOOR_WINDOW_PROP_SHEETS[sid]
        elif sid in BUILDING_PROP_SHEETS:
            sem_class = "building_facade"
            scale_cm, base_scale = BUILDING_PROP_SHEETS[sid]
        elif sid in TYPOGRAPHY_SHEETS:
            sem_class = "typography_banner"
            scale_cm, base_scale = TYPOGRAPHY_SHEETS[sid]
        elif sid == "07.props.bar-handheld":
            if max(w, h) < 260:
                sem_class, scale_cm, base_scale = "handheld_prop", 14, 0.11
            else:
                sem_class, scale_cm, base_scale = "large_furniture", 110, 0.34
        elif sid == "02.props.mirror-phone-rings":
            if max(w, h) < 220:
                sem_class, scale_cm, base_scale = "handheld_prop", 12, 0.10
            else:
                sem_class, scale_cm, base_scale = "medium_prop", 95, 0.24
        elif sid == "06.props.coin-booth":
            if max(w, h) < 240:
                sem_class, scale_cm, base_scale = "handheld_prop", 4, 0.10
            else:
                sem_class, scale_cm, base_scale = "large_furniture", 200, 0.36
        else:
            sem_class, scale_cm, base_scale = "medium_prop", 75, 0.20
    elif subfolder == "04_SETS_AND_BUILDINGS" or kind in ("set", "hero", "hero-continuation"):
        if sid in LARGE_FURNITURE_PROP_SHEETS:
            sem_class, scale_cm, base_scale = "large_furniture", *LARGE_FURNITURE_PROP_SHEETS[sid]
        elif sid in DOOR_WINDOW_PROP_SHEETS:
            sem_class, scale_cm, base_scale = "door_window_arch", *DOOR_WINDOW_PROP_SHEETS[sid]
        elif any(k in low_sid for k in ("black_void", "calm_sea")):
            sem_class, scale_cm, base_scale = "sky_canopy", 1200, 0.96
        elif any(k in low_sid for k in ("skyline", "aerial", "equator_plain", "harbor_atlantis_wide", "broll_life")):
            if rel_y < 0.35 and ar > 1.8:
                sem_class, scale_cm, base_scale = "sky_canopy", 1200, 0.96
            else:
                sem_class, scale_cm, base_scale = "horizon_vista", 850, 0.82
        elif any(k in low_sid for k in (
            "catwalk", "severnescape", "viaduct", "steps", "shore_steps",
            "causeway_road", "mountain_road", "incline_trail", "harbor_path_east", "perimeter", "shore_night"
        )):
            sem_class, scale_cm, base_scale = "stair_bridge_viaduct", 380, 0.56
        elif any(k in low_sid for k in (
            "bedroom_night", "living_room_1990s", "humid_basement", "mother_living_room",
            "mirror_hall", "temple_backroom", "temple_hall", "marquee.interior",
            "chapel.interior-states", "drowned_atrium", "atrium", "crystal_tree_hall"
        )):
            sem_class, scale_cm, base_scale = "room_wall", 320, 0.62
        else:
            if rel_w > 0.55 and rel_y < 0.38 and ar > 1.9:
                sem_class, scale_cm, base_scale = "sky_canopy", 1100, 0.96
            elif rel_w > 0.48 and ar > 2.1:
                sem_class, scale_cm, base_scale = "horizon_vista", 750, 0.80
            else:
                sem_class, scale_cm, base_scale = "building_facade", 450, 0.62
    else:
        if sid in LIMB_DETAIL_PROP_SHEETS:
            sem_class, scale_cm, base_scale = "limb_or_head_detail", *LIMB_DETAIL_PROP_SHEETS[sid]
        else:
            is_child = any(k in low_sid for k in ("young_ghost", "young_poet", "child_traveler")) or (
                sid == "atlantis.06.plaza-twelve" and pid.endswith("__p03")
            ) or (
                sid == "atlantis.06.source-actions" and any(pid.endswith(f"__p0{i}") for i in range(5, 10))
            )
            is_pose_sheet = any(k in low_sid for k in (
                "main-poses", "mainposes", "locomotion", "waltz-instances",
                "paired-choreography", "procession-gifts-gate", "plaza-twelve",
                "phone-prayer-walk", "hug-restage", "memory-drop", "couple-orbits",
                "elder-prayer", "bike-mounted-poses", "car-argument", "source-actions"
            ))
            is_crouched_sheet = any(k in low_sid for k in (
                "crouch", "floor_recovery", "car-argument", "bike-mounted-poses", "fall"
            ))
            if sid in BODY_PART_ONLY_SHEETS or any(k in low_sid for k in (
                ".body", "heads", "faces", "hands", "hips-waist", "torso-parts",
                "compact-core", "expressions"
            )):
                sem_class, scale_cm, base_scale = "limb_or_head_detail", 30, 0.16
            elif is_child:
                if ar > 0.95 or is_crouched_sheet:
                    sem_class, scale_cm, base_scale = "crouched_or_prone_figure", 85, 0.28
                else:
                    sem_class, scale_cm, base_scale = "full_figure_child", 120, 0.38
            elif is_crouched_sheet:
                sem_class, scale_cm, base_scale = "crouched_or_prone_figure", 105, 0.32
            elif is_pose_sheet:
                if ar > 0.92:
                    sem_class, scale_cm, base_scale = "crouched_or_prone_figure", 105, 0.32
                else:
                    sem_class, scale_cm, base_scale = "full_figure_adult", 175, 0.54
            else:
                if rel_h >= 0.24 and h >= 210 and ar <= 0.90:
                    sem_class, scale_cm, base_scale = "full_figure_adult", 175, 0.54
                elif rel_h >= 0.22 and h >= 190 and ar <= 1.25:
                    sem_class, scale_cm, base_scale = "crouched_or_prone_figure", 105, 0.32
                else:
                    sem_class, scale_cm, base_scale = "limb_or_head_detail", 30, 0.16

    spec = SEMANTIC_CLASS_SPECS[sem_class]
    lo_s, hi_s = spec["scale_range"]
    raw_scale = base_scale if base_scale is not None else spec["default_scale"]
    comp = aspect_compensation_multiplier(w, h, sem_class)
    calibrated_scale = round(clamp(raw_scale * comp, lo_s, hi_s), 4)

    return {
        "part_id": pid,
        "sheet_id": sid,
        "semantic_class": sem_class,
        "plane": spec["plane"],
        "z": spec["z"],
        "scale": calibrated_scale,
        "scale_range": spec["scale_range"],
        "y": spec["default_y"],
        "scale_cm": scale_cm,
        "width": w,
        "height": h,
        "aspect_ratio": round(ar, 3),
        "ocr_label": ocr_label,
    }


def infer_camera_framing(scene: Dict[str, Any]) -> str:
    beats_text = " ".join(scene.get("beats", [])).upper()
    treatment_text = (scene.get("treatment", "") or "").upper()
    title_text = (scene.get("title", "") or "").upper()
    combined = f"{beats_text} {treatment_text} {title_text}"

    tag_counts = {
        "extreme_wide": len(re.findall(r"\b(EXTREME[ _-]?WIDE|AERIAL|HORIZON|PANORAMA)\b", combined)),
        "wide": len(re.findall(r"\bWIDE\b", combined)),
        "medium_wide": len(re.findall(r"\b(MEDIUM[ _-]?WIDE|TWO[ _-]?SHOT|FULL[ _-]?SHOT)\b", combined)),
        "medium": len(re.findall(r"\bMEDIUM\b", combined)),
        "close": len(re.findall(r"\b(CLOSE|MACRO|INSERT|TIGHT|DETAIL)\b", combined)),
    }
    if tag_counts["extreme_wide"] >= 1 and any(k in combined for k in ("SKYLINE", "VOID", "AERIAL", "HORIZON", "EQUATOR")):
        return "extreme_wide"
    if tag_counts["close"] >= 2 and tag_counts["wide"] == 0:
        return "close"
    if tag_counts["medium"] > tag_counts["wide"] and tag_counts["medium"] >= 2:
        return "medium"
    if tag_counts["wide"] >= 2:
        return "wide"
    return "medium_wide"


# ---------------------------------------------------------------------------
# 4. Cohesive Set-Piece Ensemble Composer
# ---------------------------------------------------------------------------

WATER_SCENE_IDS = {
    # 39 scenes across Poems 01, 03, 04, 05, 06, 08, 09, 10, 11, 12, 13, 14
    "P01-S03",
    "P03-S04", "P03-S05", "P03-S06",
    "P04-S01", "P04-S02", "P04-S03",
    "P05-S05",
    "P06-S01", "P06-S02", "P06-S03", "P06-S04", "P06-S05", "P06-S06",
    "P08-S04", "P08-S05",
    "P09-S01", "P09-S02", "P09-S03", "P09-S04",
    "P10-S01", "P10-S03", "P10-S06",
    "P11-S01", "P11-S02", "P11-S03", "P11-S04", "P11-S05", "P11-S06",
    "P12-S03", "P12-S05",
    "P13-S01", "P13-S02", "P13-S03", "P13-S05", "P13-S06",
    "P14-S01", "P14-S02", "P14-S04",
}


def main() -> None:
    print("[1/6] Loading release_catalog.json, wygwyl_atlas_manifest.json, suite_scion_timeline.json, character_rigs_library.json...")
    catalog = json.loads((RELEASE_DIR / "release_catalog.json").read_text())
    manifest = json.loads(MANIFEST_PATH.read_text())
    timeline = json.loads((RELEASE_DIR / "suite_scion_timeline.json").read_text())
    rigs_lib = json.loads((RELEASE_DIR / "character_rigs_library.json").read_text())
    weave_lib = json.loads((SHOTS_DIR / "weave" / "cast" / "man" / "library_manifest.json").read_text())

    wd_text = (SHOTS_DIR / "world_data.js").read_text()
    wd_match = re.search(r"window\.WORLD\s*=\s*(\{.*\})\s*;?\s*$", wd_text, re.S)
    world_data = json.loads(wd_match.group(1)) if wd_match else {"districts": [], "shots": [], "reels": []}
    world_shots_by_id = {s["id"]: s for s in world_data.get("shots", [])}
    world_reels_by_poem = {int(r["num"]): r for r in world_data.get("reels", [])}
    districts_by_id = {d["id"]: d for d in world_data.get("districts", [])}

    dossiers: Dict[int, Dict[str, Any]] = {}
    atlases: Dict[int, Dict[str, Any]] = {}
    dossier_sets_by_poem: Dict[int, Dict[str, Dict[str, Any]]] = {}

    for p in range(1, 15):
        d_path = SHOTS_DIR / "poems" / "dossier" / f"{p:02d}.json"
        a_path = SHOTS_DIR / "poems" / "atlas" / f"{p:02d}.json"
        dossiers[p] = json.loads(d_path.read_text()) if d_path.exists() else {}
        atlases[p] = json.loads(a_path.read_text()) if a_path.exists() else {}
        dossier_sets_by_poem[p] = {s["id"]: s for s in dossiers[p].get("sets", [])}

    sheets_by_id: Dict[str, Dict[str, Any]] = {}
    parts_by_id: Dict[str, Dict[str, Any]] = {}
    sheet_of_part: Dict[str, Dict[str, Any]] = {}
    ocr_labels_by_part: Dict[str, str] = {}

    for sh in catalog["sheets"]:
        sid = sh["id"]
        sheets_by_id[sid] = sh
        for pt in sh.get("parts", []):
            pid = pt["id"]
            parts_by_id[pid] = pt
            sheet_of_part[pid] = sh
            ocr_labels_by_part[pid] = pt.get("label", "")

    if catalog.get("tracksuit_components"):
        ts_sheet = {
            "id": "poet.tracksuit.31_components",
            "subfolder": "01_CHARACTER_CORE",
            "kind": "working_components",
            "poems": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            "width": 1600,
            "height": 1200,
            "sheet_rel": "arena/parts/kit3/release_v2/tracksuit/01_torso_front.png",
            "parts": catalog["tracksuit_components"],
        }
        for comp in catalog["tracksuit_components"]:
            cid = comp["id"]
            parts_by_id[cid] = comp
            sheet_of_part[cid] = ts_sheet
            ocr_labels_by_part[cid] = comp.get("label", cid)

    print(f"[2/6] Classifying all {len(parts_by_id)} cut parts across {len(sheets_by_id)} sheets + 31 tracksuit components...")
    part_classifications: Dict[str, Dict[str, Any]] = {}
    class_counts: Dict[str, int] = {k: 0 for k in SEMANTIC_CLASS_SPECS}

    for pid, pt in parts_by_id.items():
        sh = sheet_of_part[pid]
        info = classify_part(sh, pt, ocr_labels_by_part)
        part_classifications[pid] = info
        class_counts[info["semantic_class"]] = class_counts.get(info["semantic_class"], 0) + 1

    films_by_poem = {int(f["n"]): f for f in timeline.get("films", [])}
    scion_shots_by_poem: Dict[int, List[Dict[str, Any]]] = {}
    for s in timeline.get("shots", []):
        scion_shots_by_poem.setdefault(int(s["poem"]), []).append(s)

    scenes_by_poem: Dict[int, List[Dict[str, Any]]] = {}
    for sc in manifest["scenes"]:
        scenes_by_poem.setdefault(int(sc["book"]), []).append(sc)

    scene_audio_windows: Dict[str, Dict[str, Any]] = {}
    for p, p_scenes in scenes_by_poem.items():
        film = films_by_poem[p]
        c0, c1 = float(film["container"][0]), float(film["container"][1])
        w0, w1 = float(film["poem"][0]), float(film["poem"][1])
        total_local_sec = sum(max(1.0, float(s.get("seconds", 10))) for s in p_scenes)
        cur_c, cur_w = c0, w0
        p_scion = scion_shots_by_poem.get(p, [])

        for idx, s in enumerate(p_scenes):
            frac = max(1.0, float(s.get("seconds", 10))) / total_local_sec
            next_c = c1 if idx == len(p_scenes) - 1 else cur_c + (c1 - c0) * frac
            next_w = w1 if idx == len(p_scenes) - 1 else cur_w + (w1 - w0) * frac
            overlapping = [
                sh for sh in p_scion
                if not (float(sh["t1"]) <= cur_w - 0.5 or float(sh["t0"]) >= next_w + 0.5)
            ]
            if not overlapping and p_scion:
                chosen_idx = min(len(p_scion) - 1, int(round(idx * (len(p_scion) - 1) / max(1, len(p_scenes) - 1))))
                overlapping = [p_scion[chosen_idx]]
            scene_audio_windows[s["id"]] = {
                "audio_window": [round(cur_c, 3), round(next_c, 3)],
                "poem_vocal_window": [round(cur_w, 3), round(next_w, 3)],
                "poem_container_window": [round(c0, 3), round(c1, 3)],
                "duration_sec": round(next_c - cur_c, 3),
                "film_slug": film["slug"],
                "scion_shots": overlapping,
            }
            cur_c, cur_w = next_c, next_w

    # Layer factory that attaches `ensemble_id`, `ensemble_type`, `anim_role`, and exact coordinates
    def build_layer(
        instance: str,
        pid: str,
        role: str,
        plane: str,
        z: float,
        x: float,
        y: float,
        scale: float,
        ensemble_id: str,
        ensemble_type: str,
        anim_role: str = "static",
        label_override: Optional[str] = None,
        alpha: float = 0.98,
        blend: str = "source-over",
        sem_class_override: Optional[str] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pt = parts_by_id[pid]
        sh = sheet_of_part[pid]
        cls_info = part_classifications[pid]
        sem_class = sem_class_override or cls_info["semantic_class"]
        lo_s, hi_s = SEMANTIC_CLASS_SPECS[sem_class]["scale_range"]
        clamped_scale = round(clamp(scale, lo_s, hi_s), 4)

        lyr: Dict[str, Any] = {
            "instance": instance,
            "plane": plane,
            "z": round(float(z), 2),
            "semantic_class": sem_class,
            "scale_cm": cls_info["scale_cm"],
            "sheet_id": sh["id"],
            "part_id": pid,
            "label": label_override or pt.get("label") or f"{sh['id']} · {pid}",
            "file": pt["file"],
            "width": int(pt["width"]),
            "height": int(pt["height"]),
            "x": round(float(x), 3),
            "y": round(float(y), 3),
            "scale": clamped_scale,
            "alpha": round(float(alpha), 3),
            "blend": blend,
            "role": role,
            "anim_role": anim_role,
            "ensemble_id": ensemble_id,
            "ensemble_type": ensemble_type,
            "sheet_file": sh.get("sheet_rel", ""),
            "bbox_sheet": pt.get("bbox_sheet", [0, 0, int(pt["width"]), int(pt["height"])]),
            "pivots": pt.get("pivots", []),
        }
        if extra_meta:
            lyr.update(extra_meta)
        return lyr

    # -----------------------------------------------------------------------
    # Cohesive Set-Piece Ensemble Generators
    # -----------------------------------------------------------------------

    def make_water_shore_ensemble(poem_num: int, sc_idx: int, include_boat_planets: bool = False) -> Dict[str, Any]:
        ens_id = f"ens_water_shore_{poem_num:02d}_{sc_idx + 1:02d}"
        ens_type = "water_shore_ensemble"
        layers: List[Dict[str, Any]] = [
            build_layer(
                instance="water_sea_backing",
                pid="11.set.calm_sea__p01" if poem_num >= 9 else "06.fx.water-rainbow-clouds__p01",
                role="set_water",
                plane="P5",
                z=3.80,
                x=0.50,
                y=0.78,
                scale=0.86,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="water_backing",
                label_override="SEA / POOL.WATER Horizon Backing",
                sem_class_override="horizon_vista",
            ),
            build_layer(
                instance="water_wave_1_far",
                pid="04.set.shore_night__p01",
                role="set_water",
                plane="P4",
                z=2.52,
                x=0.50,
                y=0.79,
                scale=0.24,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="wave_far",
                label_override="WAVE.1 · Far Horizon Swell",
                sem_class_override="stair_bridge_viaduct",
            ),
            build_layer(
                instance="water_wave_2_mid",
                pid="04.set.shore_night__p02",
                role="set_water",
                plane="P3",
                z=1.56,
                x=0.50,
                y=0.84,
                scale=0.22,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="wave_mid",
                label_override="WAVE.2 · Midground Whitecap",
                sem_class_override="medium_prop",
            ),
            build_layer(
                instance="water_wave_3_near",
                pid="04.set.shore_night__p03",
                role="fx_overlay",
                plane="P1",
                z=0.52,
                x=0.50,
                y=0.91,
                scale=0.16,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="wave_near",
                label_override="WAVE.3 · Near Shore Foam",
                sem_class_override="atmospheric_fx",
                alpha=0.88,
            ),
        ]
        if include_boat_planets:
            boat_x = 0.68
            layers.extend([
                build_layer(
                    instance="boat_hull",
                    pid="13.props.planet-boats__p06",
                    role="prop",
                    plane="P3",
                    z=1.48,
                    x=boat_x,
                    y=0.81,
                    scale=0.16,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="boat_rock",
                    label_override="Sailboat Hull on Waterline",
                    sem_class_override="medium_prop",
                ),
                build_layer(
                    instance="boat_sail",
                    pid="13.props.planet-boats__p09",
                    role="prop_subpart",
                    plane="P3",
                    z=1.47,
                    x=boat_x + 0.01,
                    y=0.73,
                    scale=0.20,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="boat_rock",
                    label_override="Sailboat Mast & Canvas Sail",
                    sem_class_override="medium_prop",
                ),
                build_layer(
                    instance="planet_jupiter",
                    pid="13.props.planet-boats__p01",
                    role="prop_subpart",
                    plane="P5",
                    z=4.10,
                    x=0.74,
                    y=0.28,
                    scale=0.22,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="planet_orbit",
                    label_override="JUPITER & Moons in Dusk Sky",
                    sem_class_override="medium_prop",
                ),
            ])
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Multiplane Water Horizon, Swells & Sailboat Ensemble" if include_boat_planets else "Multiplane Water Horizon & Shore Waves Ensemble",
            "anchor_x": 0.50,
            "anchor_y": 0.84,
            "description": "Stacked SEA backing (P5 y=0.78), WAVE.1 far swell (P4 y=0.79), WAVE.2 whitecap (P3 y=0.84), and WAVE.3 shore foam (P1 y=0.91).",
            "layers": layers,
        }

    def make_car_ensemble(car_x: float = 0.56, car_y: float = 0.86) -> Dict[str, Any]:
        ens_id = "ens_family_sedan_car"
        ens_type = "car_ensemble"
        layers = [
            build_layer(
                instance="car_passengers",
                pid="parents.02.car-argument__p01",
                role="character_supporting",
                plane="P3",
                z=1.44,
                x=car_x - 0.02,
                y=car_y - 0.04,
                scale=0.20,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="cabin_passengers",
                label_override="Parents Arguing Inside Car Cabin",
                sem_class_override="crouched_or_prone_figure",
            ),
            build_layer(
                instance="car_body_shell",
                pid="02.props.car__p01",
                role="prop",
                plane="P3",
                z=1.40,
                x=car_x,
                y=car_y,
                scale=0.28,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="car_chassis",
                label_override="1990s Family Sedan Body Shell",
                sem_class_override="large_furniture",
            ),
            build_layer(
                instance="car_side_window",
                pid="02.props.car__p03",
                role="prop_subpart",
                plane="P3",
                z=1.38,
                x=car_x,
                y=car_y - 0.05,
                scale=0.13,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="car_window",
                label_override="Sedan Side Window Glazing",
                sem_class_override="medium_prop",
                alpha=0.86,
            ),
            build_layer(
                instance="car_wheel_front",
                pid="02.props.car__p05",
                role="prop",
                plane="P3",
                z=1.35,
                x=car_x - 0.11,
                y=0.89,
                scale=0.11,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="wheel_spin",
                label_override="Front Wheel (Pinned to Front Arch)",
                sem_class_override="handheld_prop",
            ),
            build_layer(
                instance="car_wheel_rear",
                pid="02.props.car__p06",
                role="prop",
                plane="P3",
                z=1.35,
                x=car_x + 0.11,
                y=0.89,
                scale=0.11,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="wheel_spin",
                label_override="Rear Wheel (Pinned to Rear Arch)",
                sem_class_override="handheld_prop",
            ),
            build_layer(
                instance="car_headlight_beam",
                pid="02.fx.lights-iris__p01",
                role="fx_overlay",
                plane="P1",
                z=0.46,
                x=car_x - 0.22,
                y=0.85,
                scale=0.22,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="headlight_beam",
                label_override="Sweeping Headlight Beam Cone",
                sem_class_override="atmospheric_fx",
                alpha=0.82,
                blend="screen",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Assembled Family Sedan (Chassis + Spinning Wheels + Window + Passengers + Headlights)",
            "anchor_x": car_x,
            "anchor_y": car_y,
            "description": "Co-locates car body shell, front & rear wheels at wheel-arch offsets (car_x ± 0.11, y=0.89), cabin window, seated parents, and headlight beam.",
            "layers": layers,
        }

    def make_motorcycle_ensemble(bike_x: float = 0.52, bike_y: float = 0.86, parked: bool = False) -> Dict[str, Any]:
        ens_id = "ens_motorcycle_ride"
        ens_type = "motorcycle_ensemble"
        frame_pid = "11.props.parked-motorcycle__p01" if parked else "10.props.bike-skeleton__p01"
        layers = [
            build_layer(
                instance="bike_frame_chassis",
                pid=frame_pid,
                role="prop",
                plane="P3",
                z=1.38,
                x=bike_x,
                y=bike_y,
                scale=0.28,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="bike_chassis",
                label_override="Cafe Motorcycle Frame & Engine Tank",
                sem_class_override="large_furniture",
            ),
            build_layer(
                instance="bike_wheel_rear",
                pid="10.props.bike-skeleton__p07",
                role="prop",
                plane="P3",
                z=1.35,
                x=bike_x - 0.08,
                y=0.89,
                scale=0.12,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="wheel_spin",
                label_override="Motorcycle Rear Wheel (Spinning)",
                sem_class_override="handheld_prop",
            ),
            build_layer(
                instance="bike_wheel_front",
                pid="10.props.bike-skeleton__p09",
                role="prop",
                plane="P3",
                z=1.35,
                x=bike_x + 0.08,
                y=0.89,
                scale=0.12,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="wheel_spin",
                label_override="Motorcycle Front Wheel (Spinning)",
                sem_class_override="handheld_prop",
            ),
            build_layer(
                instance="bike_headlight_beam",
                pid="10.fx.ride-light__p02",
                role="fx_overlay",
                plane="P1",
                z=0.45,
                x=bike_x + 0.22,
                y=0.83,
                scale=0.18,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="headlight_beam",
                label_override="Motorcycle Headlight Cone & Tank Glint",
                sem_class_override="atmospheric_fx",
                alpha=0.84,
                blend="screen",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Assembled Cafe Motorcycle (Frame + Spinning Front/Rear Wheels + Headlight Cone)",
            "anchor_x": bike_x,
            "anchor_y": bike_y,
            "description": "Co-locates motorcycle chassis, spinning rear/front wheels at (bike_x ± 0.08, y=0.89), and forward headlight cone.",
            "layers": layers,
        }

    def make_living_room_window_portal_ensemble(win_x: float = 0.64, win_y: float = 0.82) -> Dict[str, Any]:
        ens_id = "ens_window_portal_living_room"
        ens_type = "portal_window_tv_ensemble"
        layers = [
            build_layer(
                instance="portal_window_view",
                pid="02.set.living_room_1990s__p07",
                role="set_portal",
                plane="P4",
                z=2.58,
                x=win_x,
                y=win_y - 0.08,
                scale=0.38,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="portal_other_world",
                label_override="WINDOW.VIEW · Exterior Night World Beyond Glass",
                sem_class_override="door_window_arch",
            ),
            build_layer(
                instance="portal_window_wall",
                pid="02.set.living_room_1990s__p01",
                role="set_portal",
                plane="P4",
                z=2.42,
                x=win_x,
                y=win_y,
                scale=0.54,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="portal_aperture",
                label_override="WINDOW.WALL · Living Room Window Frame",
                sem_class_override="door_window_arch",
            ),
            build_layer(
                instance="portal_curtain_left",
                pid="02.set.living_room_1990s__p03",
                role="set_portal",
                plane="P4",
                z=2.36,
                x=win_x - 0.12,
                y=win_y - 0.01,
                scale=0.46,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="curtain_sway_L",
                label_override="CURTAIN.L · Left Window Drape",
                sem_class_override="door_window_arch",
            ),
            build_layer(
                instance="portal_curtain_right",
                pid="02.set.living_room_1990s__p04",
                role="set_portal",
                plane="P4",
                z=2.36,
                x=win_x + 0.12,
                y=win_y - 0.01,
                scale=0.36,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="curtain_sway_R",
                label_override="CURTAIN.R · Right Window Drape & Blinds",
                sem_class_override="door_window_arch",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Living Room Window Portal (Window Wall + Exterior View + Left/Right Curtains)",
            "anchor_x": win_x,
            "anchor_y": win_y,
            "description": "Co-locates WINDOW.VIEW behind WINDOW.WALL flanked symmetrically by CURTAIN.L and CURTAIN.R at (win_x ± 0.12).",
            "layers": layers,
        }

    def make_bedroom_window_and_tv_portal_ensemble() -> Dict[str, Any]:
        ens_id = "ens_bedroom_window_tv_portal"
        ens_type = "portal_window_tv_ensemble"
        win_x = 0.66
        layers = [
            build_layer(
                instance="bedroom_sash_window",
                pid="01.props.window__p01",
                role="set_portal",
                plane="P4",
                z=2.42,
                x=win_x,
                y=0.82,
                scale=0.56,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="portal_aperture",
                label_override="High-Rise Sash Window Frame Portal",
                sem_class_override="door_window_arch",
            ),
            build_layer(
                instance="fire_escape_rail",
                pid="01.props.window__p06",
                role="set_portal",
                plane="P4",
                z=2.34,
                x=win_x,
                y=0.86,
                scale=0.26,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="fire_escape_landing",
                label_override="Steel Fire-Escape Landing & Rail Outside Window",
                sem_class_override="stair_bridge_viaduct",
            ),
            build_layer(
                instance="bedroom_dresser_chest",
                pid="01.props.room__p01",
                role="prop",
                plane="P3",
                z=1.45,
                x=0.22,
                y=0.88,
                scale=0.34,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="drawer_slide",
                label_override="Wooden Bedroom Dresser with Sliding Drawers",
                sem_class_override="large_furniture",
            ),
            build_layer(
                instance="bedroom_tv_portal",
                pid="01.props.room__p05",
                role="prop_subpart",
                plane="P3",
                z=1.42,
                x=0.22,
                y=0.66,
                scale=0.20,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="portal_tv_flicker",
                label_override="Television Screen Portal (Stacked on Dresser)",
                sem_class_override="medium_prop",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Bedroom Sash Window & Television Portal Ensemble",
            "anchor_x": win_x,
            "anchor_y": 0.84,
            "description": "Co-locates sash window + exterior fire-escape rail at x=0.66, and stacks the flickering TV portal directly atop the wooden dresser at x=0.22.",
            "layers": layers,
        }

    def make_atlantis_gate_portal_ensemble() -> Dict[str, Any]:
        ens_id = "ens_atlantis_gate_portal"
        ens_type = "portal_window_tv_ensemble"
        layers = [
            build_layer(
                instance="portal_crystal_tree_hall",
                pid="06.set.crystal_tree_hall__p01",
                role="set_portal",
                plane="P4",
                z=2.62,
                x=0.50,
                y=0.76,
                scale=0.48,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="portal_inner_world",
                label_override="Crystal Tree Hall Glowing Inside Portal Arch",
                sem_class_override="room_wall",
            ),
            build_layer(
                instance="portal_atlantis_arch",
                pid="06.set.atlantis_gate__p01",
                role="set_portal",
                plane="P4",
                z=2.40,
                x=0.50,
                y=0.80,
                scale=0.62,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="portal_aperture",
                label_override="Atlantis Gate Portal Arch",
                sem_class_override="door_window_arch",
            ),
            build_layer(
                instance="portal_pool_rim",
                pid="06.set.atlantis_gate__p02",
                role="set_water",
                plane="P4",
                z=2.32,
                x=0.50,
                y=0.92,
                scale=0.28,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="portal_reflection_pool",
                label_override="POOL.RIM & POOL.WATER at Portal Threshold",
                sem_class_override="stair_bridge_viaduct",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Atlantis Gate Portal & Inner Crystal Tree Hall Ensemble",
            "anchor_x": 0.50,
            "anchor_y": 0.80,
            "description": "Co-locates Atlantis Gate PORTAL (x=0.50, y=0.80), POOL.RIM/WATER (y=0.92), and Crystal Tree Hall nested inside the portal aperture (z=2.62).",
            "layers": layers,
        }

    def make_rose_window_tambourine_ensemble(shattered: bool = False) -> Dict[str, Any]:
        ens_id = "ens_rose_window_tambourine"
        ens_type = "portal_window_tv_ensemble"
        tamb_pid = "03.props.tambourine-broken__p01" if shattered else "02.props.tambourine__p01"
        tamb_y = 0.88 if shattered else 0.52
        layers = [
            build_layer(
                instance="rose_window_tracery",
                pid="03.props.rose-window__p01",
                role="set_portal",
                plane="P4",
                z=2.45,
                x=0.52,
                y=0.58,
                scale=0.46,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="portal_aperture",
                label_override="Gothic Rose Window Tracery Portal",
                sem_class_override="door_window_arch",
            ),
            build_layer(
                instance="rose_window_petals",
                pid="03.props.rose-window__p03",
                role="set_portal",
                plane="P4",
                z=2.48,
                x=0.52,
                y=0.48,
                scale=0.34,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="stained_glass_glow",
                label_override="Twelve Stained-Glass Rose Window Petals",
                sem_class_override="door_window_arch",
            ),
            build_layer(
                instance="thrown_tambourine",
                pid=tamb_pid,
                role="prop" if shattered else "prop_subpart",
                plane="P3",
                z=1.28,
                x=0.50,
                y=tamb_y,
                scale=0.12,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="tambourine_arc",
                label_override="Shattered Tambourine Shards on Shore" if shattered else "Flying Wooden Tambourine Crossing Rose Window",
                sem_class_override="handheld_prop",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Gothic Rose Window Portal & Flying Tambourine Ensemble",
            "anchor_x": 0.52,
            "anchor_y": 0.56,
            "description": "Co-locates Gothic rose window tracery + stained-glass petals at (0.52, 0.58) with the thrown 25cm tambourine arcing through the center.",
            "layers": layers,
        }

    def make_vintage_door_ballroom_portal_ensemble() -> Dict[str, Any]:
        ens_id = "ens_vintage_door_portal"
        ens_type = "portal_window_tv_ensemble"
        layers = [
            build_layer(
                instance="portal_ballroom_interior",
                pid="14.set.vintage_party__p01",
                role="set_portal",
                plane="P4",
                z=2.62,
                x=0.54,
                y=0.84,
                scale=0.54,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="portal_other_world",
                label_override="Warm 1940s Ballroom Glowing Inside Doorway",
                sem_class_override="building_facade",
            ),
            build_layer(
                instance="portal_vintage_doorframe",
                pid="14.props.door__p01",
                role="set_portal",
                plane="P4",
                z=2.40,
                x=0.54,
                y=0.86,
                scale=0.58,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="portal_aperture",
                label_override="Panelled Vintage Wooden Doorway Frame",
                sem_class_override="door_window_arch",
            ),
            build_layer(
                instance="ballroom_chandelier",
                pid="01.props.chandeliers__p01",
                role="prop_subpart",
                plane="P3",
                z=1.50,
                x=0.54,
                y=0.28,
                scale=0.22,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="chandelier_sway",
                label_override="Six-Arm Crystal Ballroom Chandelier",
                sem_class_override="medium_prop",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Vintage Doorway Portal & Chandelier Ballroom Ensemble",
            "anchor_x": 0.54,
            "anchor_y": 0.86,
            "description": "Co-locates the panelled vintage door frame (x=0.54, y=0.86), warm ballroom interior visible inside the doorway, and crystal chandelier above.",
            "layers": layers,
        }

    def make_interior_lamp_and_furniture_ensemble(lamp_x: float = 0.20, lamp_y: float = 0.86) -> Dict[str, Any]:
        ens_id = "ens_interior_lamp_furniture"
        ens_type = "interior_furniture_ensemble"
        layers = [
            build_layer(
                instance="interior_lamp_base",
                pid="02.set.living_room_1990s__p05",
                role="prop",
                plane="P3",
                z=1.45,
                x=lamp_x,
                y=lamp_y,
                scale=0.22,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="lamp_base",
                label_override="LAMP.BASE · Turned Ceramic Table Lamp Base",
                sem_class_override="medium_prop",
            ),
            build_layer(
                instance="interior_lamp_shade",
                pid="02.set.living_room_1990s__p06",
                role="prop_subpart",
                plane="P3",
                z=1.44,
                x=lamp_x,
                y=lamp_y - 0.16,
                scale=0.16,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="lamp_glow",
                label_override="LAMP.SHADE · Warm Pleated Shade (Stacked on Base)",
                sem_class_override="medium_prop",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Assembled Living Room Lamp (Shade Stacked on Base)",
            "anchor_x": lamp_x,
            "anchor_y": lamp_y,
            "description": "Stacks LAMP.SHADE (y = lamp_y - 0.16) directly on top of LAMP.BASE (y = lamp_y) at the exact same x = lamp_x.",
            "layers": layers,
        }

    def make_dj_booth_ensemble() -> Dict[str, Any]:
        ens_id = "ens_dj_booth_club"
        ens_type = "dj_booth_ensemble"
        layers = [
            build_layer(
                instance="dj_speaker_left",
                pid="07.props.speakers-vu__p01",
                role="prop",
                plane="P3",
                z=1.46,
                x=0.22,
                y=0.86,
                scale=0.35,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="speaker_pulse",
                label_override="Left Club Speaker Stack & VU Meter",
                sem_class_override="large_furniture",
            ),
            build_layer(
                instance="dj_speaker_right",
                pid="07.props.speakers-vu__p02",
                role="prop",
                plane="P3",
                z=1.46,
                x=0.78,
                y=0.86,
                scale=0.35,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="speaker_pulse",
                label_override="Right Club Speaker Stack & VU Meter",
                sem_class_override="large_furniture",
            ),
            build_layer(
                instance="actor_dj_cyber",
                pid="party.07.dj_cyber.main-poses__p01",
                role="character_supporting",
                plane="P2",
                z=1.44,
                x=0.50,
                y=0.83,
                scale=0.52,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="dj_mix",
                label_override="DJ Cyber Mixing Behind the Decks",
                sem_class_override="full_figure_adult",
            ),
            build_layer(
                instance="dj_booth_console",
                pid="07.props.dj-decks__p01",
                role="prop",
                plane="P3",
                z=1.40,
                x=0.50,
                y=0.85,
                scale=0.34,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="dj_console",
                label_override="DJ Booth Console & Fader Deck",
                sem_class_override="large_furniture",
            ),
            build_layer(
                instance="dj_platter_left",
                pid="07.props.dj-decks__p04",
                role="prop_subpart",
                plane="P3",
                z=1.38,
                x=0.45,
                y=0.71,
                scale=0.11,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="turntable_spin",
                label_override="Left Spinning Vinyl Platter",
                sem_class_override="handheld_prop",
            ),
            build_layer(
                instance="dj_platter_right",
                pid="07.props.dj-decks__p05",
                role="prop_subpart",
                plane="P3",
                z=1.38,
                x=0.55,
                y=0.71,
                scale=0.11,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="turntable_spin",
                label_override="Right Spinning Vinyl Platter",
                sem_class_override="handheld_prop",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Assembled DJ Booth, Spinning Turntables & Left/Right Speaker Stacks",
            "anchor_x": 0.50,
            "anchor_y": 0.85,
            "description": "Co-locates DJ booth + left/right spinning platters at (0.50, 0.85) with DJ Cyber behind the decks and symmetrical speaker stacks at x=0.22 and x=0.78.",
            "layers": layers,
        }

    def make_phone_booth_ensemble(booth_x: float = 0.64, booth_y: float = 0.86) -> Dict[str, Any]:
        ens_id = "ens_harbor_phone_booth"
        ens_type = "phone_booth_ensemble"
        layers = [
            build_layer(
                instance="phone_booth_frame",
                pid="09.props.phonebooth__p01",
                role="prop",
                plane="P3",
                z=1.44,
                x=booth_x,
                y=booth_y,
                scale=0.42,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="booth_frame",
                label_override="Modular Harbor Phone Booth Frame",
                sem_class_override="large_furniture",
            ),
            build_layer(
                instance="phone_booth_door",
                pid="09.props.phonebooth__p03",
                role="prop_subpart",
                plane="P3",
                z=1.42,
                x=booth_x,
                y=booth_y - 0.01,
                scale=0.38,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="booth_door",
                label_override="Phone Booth Folding Glass Door",
                sem_class_override="large_furniture",
                alpha=0.86,
            ),
            build_layer(
                instance="phone_booth_payphone",
                pid="09.props.phones-chair__p01",
                role="prop_subpart",
                plane="P3",
                z=1.43,
                x=booth_x - 0.01,
                y=booth_y - 0.18,
                scale=0.14,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="payphone_handset",
                label_override="Black Rotary Payphone Mounted in Booth",
                sem_class_override="handheld_prop",
            ),
            build_layer(
                instance="phone_ring_waves",
                pid="02.props.mirror-phone-rings__p03",
                role="fx_overlay",
                plane="P1",
                z=0.48,
                x=booth_x,
                y=booth_y - 0.34,
                scale=0.16,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="phone_ring",
                label_override="Ringing Acoustic Wave Rings Above Booth",
                sem_class_override="atmospheric_fx",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Assembled Harbor Phone Booth (Frame + Glass Door + Payphone + Ring Waves)",
            "anchor_x": booth_x,
            "anchor_y": booth_y,
            "description": "Co-locates phone booth frame, glass door, interior payphone, and acoustic ring waves at (x=0.64, y=0.86).",
            "layers": layers,
        }

    def make_cafe_table_ensemble(table_x: float = 0.60, table_y: float = 0.88) -> Dict[str, Any]:
        ens_id = "ens_harbor_cafe_table"
        ens_type = "cafe_table_ensemble"
        layers = [
            build_layer(
                instance="cafe_table_base",
                pid="13.props.cafe__p06",
                role="prop",
                plane="P3",
                z=1.45,
                x=table_x,
                y=table_y,
                scale=0.13,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="table_base",
                label_override="3-Prong Cast-Iron Bistro Table Base",
                sem_class_override="medium_prop",
            ),
            build_layer(
                instance="cafe_table_stem",
                pid="13.props.cafe__p02",
                role="prop_subpart",
                plane="P3",
                z=1.44,
                x=table_x,
                y=table_y - 0.02,
                scale=0.22,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="table_stem",
                label_override="Bistro Table Pedestal Stem",
                sem_class_override="medium_prop",
            ),
            build_layer(
                instance="cafe_table_top",
                pid="13.props.cafe__p01",
                role="prop_subpart",
                plane="P3",
                z=1.43,
                x=table_x,
                y=table_y - 0.16,
                scale=0.16,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="table_top",
                label_override="Round Marble Bistro Tabletop (Mounted on Stem)",
                sem_class_override="medium_prop",
            ),
            build_layer(
                instance="cafe_espresso_cup",
                pid="13.props.personal__p01",
                role="prop_subpart",
                plane="P3",
                z=1.41,
                x=table_x + 0.02,
                y=table_y - 0.22,
                scale=0.09,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="coffee_steam",
                label_override="Warm Espresso Cup Resting on Tabletop",
                sem_class_override="handheld_prop",
            ),
            build_layer(
                instance="cafe_bistro_chair",
                pid="13.props.cafe__p03",
                role="prop",
                plane="P3",
                z=1.46,
                x=table_x - 0.11,
                y=table_y,
                scale=0.34,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="cafe_chair",
                label_override="Bentwood Bistro Chair Beside Table",
                sem_class_override="large_furniture",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Assembled Harbor Cafe Table (Base + Stem + Tabletop + Espresso Cup + Chair)",
            "anchor_x": table_x,
            "anchor_y": table_y,
            "description": "Stacks 3-prong base, pedestal stem, round tabletop, and espresso cup at x=0.60 with the bistro chair beside it at x=0.49.",
            "layers": layers,
        }

    def make_beating_heart_and_hands_ensemble(poet_x: float = 0.36) -> Dict[str, Any]:
        ens_id = "ens_beating_heart_weave_hands"
        ens_type = "beating_heart_ensemble"
        hx = round(poet_x + 0.09, 3)
        layers = [
            build_layer(
                instance="weave_jointed_hand_left",
                pid="04.props.poet-jointed-hands__p01",
                role="prop_subpart",
                plane="P2",
                z=0.96,
                x=hx - 0.03,
                y=0.66,
                scale=0.15,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="weave_hand_articulation",
                label_override="Jointed Poet Left Palm & Fingers (Weave Hand Rig)",
                sem_class_override="limb_or_head_detail",
            ),
            build_layer(
                instance="weave_jointed_hand_right",
                pid="04.props.poet-jointed-hands__p02",
                role="prop_subpart",
                plane="P2",
                z=0.95,
                x=hx + 0.03,
                y=0.66,
                scale=0.15,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="weave_hand_articulation",
                label_override="Jointed Poet Right Palm & Fingers (Weave Hand Rig)",
                sem_class_override="limb_or_head_detail",
            ),
            build_layer(
                instance="beating_heart_core",
                pid="04.props.heart__p01",
                role="prop_subpart",
                plane="P3",
                z=0.94,
                x=hx,
                y=0.60,
                scale=0.12,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="heart_beat",
                label_override="Beating Anatomical Poet Heart Chambers",
                sem_class_override="handheld_prop",
            ),
            build_layer(
                instance="beating_heart_vessels",
                pid="04.props.heart__p05",
                role="fx_overlay",
                plane="P1",
                z=0.93,
                x=hx,
                y=0.53,
                scale=0.14,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="heart_pulse_ring",
                label_override="Aortic Vessels & Crimson Pulse Glow",
                sem_class_override="atmospheric_fx",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Articulated Weave Hands & Beating Poet Heart Ensemble",
            "anchor_x": hx,
            "anchor_y": 0.62,
            "description": "Co-locates left & right jointed Poet hands (04.props.poet-jointed-hands) cupping the beating heart chambers and aortic pulse glow.",
            "layers": layers,
        }

    def make_faith_bloom_ensemble(flower_x: float = 0.56, flower_y: float = 0.86) -> Dict[str, Any]:
        ens_id = "ens_faith_bloom_flower"
        ens_type = "faith_bloom_ensemble"
        layers = [
            build_layer(
                instance="flower_stem_leaves",
                pid="04.props.faith-blooms__p05",
                role="prop",
                plane="P3",
                z=1.34,
                x=flower_x,
                y=flower_y,
                scale=0.14,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="flower_stem",
                label_override="Mustard Seed / Golden Bloom Stem & Leaves",
                sem_class_override="handheld_prop",
            ),
            build_layer(
                instance="flower_golden_head",
                pid="04.props.faith-blooms__p07",
                role="prop_subpart",
                plane="P3",
                z=1.33,
                x=flower_x,
                y=flower_y - 0.11,
                scale=0.11,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="flower_bloom",
                label_override="Golden Flowerhead (Stacked on Top of Stem)",
                sem_class_override="handheld_prop",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Assembled Golden Faith Bloom (Flowerhead on Stem)",
            "anchor_x": flower_x,
            "anchor_y": flower_y,
            "description": "Places the golden flowerhead (y = stem_y - 0.11) directly atop its rooted stem so the Poet can bend and pick up the whole flower.",
            "layers": layers,
        }

    def make_hourglass_ensemble(hg_x: float = 0.52, hg_y: float = 0.84) -> Dict[str, Any]:
        ens_id = "ens_burning_hourglass"
        ens_type = "hourglass_ensemble"
        layers = [
            build_layer(
                instance="hourglass_frame",
                pid="12.props.last-hourglass__p01",
                role="prop",
                plane="P3",
                z=1.36,
                x=hg_x,
                y=hg_y,
                scale=0.24,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="hourglass_frame",
                label_override="Carved Wooden Hourglass Stand",
                sem_class_override="medium_prop",
            ),
            build_layer(
                instance="hourglass_glass_bulbs",
                pid="12.props.last-hourglass__p02",
                role="prop_subpart",
                plane="P3",
                z=1.35,
                x=hg_x,
                y=hg_y - 0.02,
                scale=0.21,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="hourglass_bulbs",
                label_override="Twin Glass Hourglass Chambers",
                sem_class_override="medium_prop",
            ),
            build_layer(
                instance="hourglass_falling_sand",
                pid="12.props.last-hourglass__p05",
                role="prop_subpart",
                plane="P3",
                z=1.34,
                x=hg_x,
                y=hg_y - 0.06,
                scale=0.11,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="hourglass_sand",
                label_override="Falling Stream of Burning Sand",
                sem_class_override="handheld_prop",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Assembled Burning Hourglass (Frame + Glass Bulbs + Falling Sand Stream)",
            "anchor_x": hg_x,
            "anchor_y": hg_y,
            "description": "Co-locates the hourglass frame, twin glass bulbs, and active falling sand stream at (x=0.52, y=0.84).",
            "layers": layers,
        }

    def make_angel_wings_ensemble(angel_x: float = 0.66, angel_y: float = 0.89) -> Dict[str, Any]:
        ens_id = "ens_winged_angel"
        ens_type = "angel_wings_ensemble"
        layers = [
            build_layer(
                instance="angel_wing_left",
                pid="08.cast.angel.wings__p03",
                role="prop_subpart",
                plane="P2",
                z=1.08,
                x=angel_x - 0.07,
                y=angel_y - 0.18,
                scale=0.27,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="wing_flap_L",
                label_override="Left Feathered Angel Wing (Pinned to Left Shoulder)",
                sem_class_override="limb_or_head_detail",
            ),
            build_layer(
                instance="angel_wing_right",
                pid="08.cast.angel.wings__p04",
                role="prop_subpart",
                plane="P2",
                z=1.08,
                x=angel_x + 0.07,
                y=angel_y - 0.18,
                scale=0.27,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="wing_flap_R",
                label_override="Right Feathered Angel Wing (Pinned to Right Shoulder)",
                sem_class_override="limb_or_head_detail",
            ),
            build_layer(
                instance="actor_angel_body",
                pid="08.cast.angel.main-poses__p01",
                role="character_supporting",
                plane="P2",
                z=1.04,
                x=angel_x,
                y=angel_y,
                scale=0.54,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="angel_hover",
                label_override="Angel in White Robe (Wings Articulated Behind Shoulders)",
                sem_class_override="full_figure_adult",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Winged Angel Ensemble (Left & Right Wings Pinned Behind Shoulder Blades)",
            "anchor_x": angel_x,
            "anchor_y": angel_y,
            "description": "Pins Left & Right wings (08.cast.angel.wings__p03/p04) symmetrically at (angel_x ± 0.07, angel_y - 0.18, z=1.08) behind the Angel figure.",
            "layers": layers,
        }

    def make_clouds_and_light_ensemble(poem_num: int) -> Dict[str, Any]:
        ens_id = f"ens_clouds_light_{poem_num:02d}"
        ens_type = "clouds_light_ensemble"
        layers = [
            build_layer(
                instance="sky_sun_moon_disc",
                pid="11.fx.light__p01" if poem_num >= 9 else "09.props.moon-sun__p01",
                role="fx_overlay",
                plane="P5",
                z=3.65,
                x=0.50,
                y=0.26,
                scale=0.18,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="sun_pulse",
                label_override="Luminous Sun / Moon Paper Disc",
                sem_class_override="atmospheric_fx",
            ),
            build_layer(
                instance="sky_cloud_band_left",
                pid="11.fx.light__p02",
                role="fx_overlay",
                plane="P5",
                z=3.55,
                x=0.36,
                y=0.29,
                scale=0.16,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="cloud_drift_L",
                label_override="Drifting Dawn Cloud Band Left",
                sem_class_override="atmospheric_fx",
            ),
            build_layer(
                instance="sky_light_ray_beam",
                pid="11.fx.light__p05",
                role="fx_overlay",
                plane="P1",
                z=0.45,
                x=0.50,
                y=0.48,
                scale=0.28,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="light_ray",
                label_override="Crepuscular Light Ray Beaming Through Clouds",
                sem_class_override="atmospheric_fx",
                alpha=0.78,
                blend="screen",
            ),
        ]
        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Clouds, Sun Disc & Crepuscular Light Rays Ensemble",
            "anchor_x": 0.50,
            "anchor_y": 0.28,
            "description": "Co-locates the sun/moon disc, drifting cloud band, and diagonal crepuscular light ray in the upper sky canopy.",
            "layers": layers,
        }

    def make_hero_and_extras_ensemble(poem_num: int, sc_idx: int, sc_id: str) -> Dict[str, Any]:
        """
        Build the Hero Poet & Supporting Cast Action Ensemble on Plane P2 (Z=1.0),
        positioning characters so they actively interact with the scene's portals,
        vehicles, water, and props.
        """
        ens_id = f"ens_cast_action_{sc_id.lower()}"
        ens_type = "cast_interaction_ensemble"
        poet_poses = CURATED_POET_POSES.get(poem_num, CURATED_POET_POSES[4])
        p_pid, p_sem, p_rig, p_lbl = poet_poses[sc_idx % len(poet_poses)]

        poet_x = 0.36
        poet_y = 0.91
        if poem_num == 10 and sc_idx >= 1:
            poet_x, poet_y = 0.51, 0.87
        elif poem_num == 14 and sc_idx >= 4:
            poet_x, poet_y = 0.44, 0.90

        rig_obj = rigs_lib.get("rigs", {}).get(p_rig, {})
        loco_keys = list(rig_obj.get("locomotion_cycles", {}).keys())
        active_cycle = loco_keys[sc_idx % len(loco_keys)] if loco_keys else "idle_breathe"

        layers: List[Dict[str, Any]] = [
            build_layer(
                instance="actor_poet",
                pid=p_pid,
                role="character_hero",
                plane="P2",
                z=1.00,
                x=poet_x,
                y=poet_y,
                scale=0.38 if p_sem == "crouched_or_prone_figure" else 0.54,
                ensemble_id=ens_id,
                ensemble_type=ens_type,
                anim_role="hero_performance",
                label_override=p_lbl,
                sem_class_override=p_sem,
                extra_meta={
                    "rig_id": p_rig,
                    "locomotion_cycle": active_cycle,
                },
            )
        ]

        # Add 1 interactive supporting character or extra with a handheld prop where appropriate
        if poem_num == 1:
            layers.append(
                build_layer(
                    instance="actor_ex_window",
                    pid="ex.ex_jacket.master__p30" if sc_idx < 2 else ("ex.ex_jacket.master__p31" if sc_idx == 2 else "party.01.vintage-waltz-instances__p01"),
                    role="character_supporting",
                    plane="P2",
                    z=1.04,
                    x=0.66 if sc_idx < 2 else 0.64,
                    y=0.84 if sc_idx < 2 else 0.90,
                    scale=0.36 if sc_idx < 3 else 0.54,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="ex_vaping_at_rail" if sc_idx < 2 else "supporting_action",
                    label_override="Ex Leaning on Fire-Escape Rail (Back View)" if sc_idx < 2 else "Vintage Party Waltz Couple",
                    sem_class_override="crouched_or_prone_figure" if sc_idx < 3 else "full_figure_adult",
                )
            )
            layers.append(
                build_layer(
                    instance="prop_vape_ember",
                    pid="01.props.handheld__p01",
                    role="prop_subpart",
                    plane="P3",
                    z=1.02,
                    x=0.70 if sc_idx < 2 else poet_x + 0.06,
                    y=0.63,
                    scale=0.10,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="ember_pulse",
                    label_override="Glowing Vape Pen & Poem Sheet in Hand",
                    sem_class_override="handheld_prop",
                )
            )
        elif poem_num == 2:
            layers.append(
                build_layer(
                    instance="actor_young_poet",
                    pid="young_ghost.02.main-poses__p02",
                    role="character_supporting",
                    plane="P2",
                    z=1.03,
                    x=0.46,
                    y=0.91,
                    scale=0.38,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="child_witness",
                    label_override="Young Poet (Age 7) Watching at Window with Tambourine",
                    sem_class_override="full_figure_child",
                )
            )
        elif poem_num == 5:
            layers.append(
                build_layer(
                    instance="actor_ancestor_parade",
                    pid=f"ancestors.05.procession-gifts-gate__p0{(sc_idx % 4) + 1}",
                    role="character_supporting",
                    plane="P2",
                    z=1.04,
                    x=0.64,
                    y=0.91,
                    scale=0.55,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="ancestor_procession",
                    label_override="Ancestor Procession Bearer with Lantern Staff",
                    sem_class_override="full_figure_adult",
                )
            )
        elif poem_num == 6:
            layers.append(
                build_layer(
                    instance="actor_atlantis_citizen",
                    pid=f"atlantis.06.plaza-twelve__p0{(sc_idx % 5) + 1}",
                    role="character_supporting",
                    plane="P2",
                    z=1.04,
                    x=0.66,
                    y=0.91,
                    scale=0.38 if (sc_idx % 5) + 1 == 3 else 0.54,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="plaza_citizen",
                    label_override="Atlantis Plaza Citizen & Gatekeeper",
                    sem_class_override="full_figure_child" if (sc_idx % 5) + 1 == 3 else "full_figure_adult",
                )
            )
        elif poem_num == 7:
            layers.append(
                build_layer(
                    instance="actor_club_dancer",
                    pid=f"party.07.party_guest.main-poses__p0{(sc_idx % 2) + 1}",
                    role="character_supporting",
                    plane="P2",
                    z=1.04,
                    x=0.68,
                    y=0.91,
                    scale=0.54,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="club_groove",
                    label_override="House Party Guest Dancing to DJ Set",
                    sem_class_override="full_figure_adult",
                )
            )
        elif poem_num == 9:
            layers.append(
                build_layer(
                    instance="actor_parents_09",
                    pid=f"parents.09.phone-prayer-walk__p0{(sc_idx % 4) + 1}",
                    role="character_supporting",
                    plane="P2",
                    z=1.04,
                    x=0.62,
                    y=0.90,
                    scale=0.36 if (sc_idx % 4) + 1 == 2 else 0.54,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="parent_call_walk",
                    label_override="Mother on Phone / Father Walking East Harbor",
                    sem_class_override="crouched_or_prone_figure" if (sc_idx % 4) + 1 == 2 else "full_figure_adult",
                )
            )
        elif poem_num in (11, 12):
            layers.append(
                build_layer(
                    instance="actor_temple_family",
                    pid="family.12.hug-restage__p01" if poem_num == 12 else f"family.11.optional.action__p1{(sc_idx % 3)}",
                    role="character_supporting",
                    plane="P2",
                    z=1.04,
                    x=0.66,
                    y=0.91,
                    scale=0.54,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="family_reunion",
                    label_override="Family & Temple Elders Gathering in Welcome",
                    sem_class_override="full_figure_adult",
                )
            )
        elif poem_num == 13:
            layers.append(
                build_layer(
                    instance="actor_woman_window",
                    pid=f"woman.13.window-action__p1{(sc_idx % 3) + 3}",
                    role="character_supporting",
                    plane="P2",
                    z=1.04,
                    x=0.72,
                    y=0.90,
                    scale=0.53,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="window_farewell",
                    label_override="Woman by Distant Harbor Window / Couple in Orbit",
                    sem_class_override="full_figure_adult",
                )
            )
        elif poem_num == 14:
            layers.append(
                build_layer(
                    instance="actor_muse_waltz",
                    pid=f"poet.14.muse-dance__p0{(sc_idx % 3) + 2}",
                    role="character_supporting",
                    plane="P2",
                    z=1.03,
                    x=0.58,
                    y=0.91,
                    scale=0.54,
                    ensemble_id=ens_id,
                    ensemble_type=ens_type,
                    anim_role="muse_waltz",
                    label_override="Muse Dancing in Vintage Ballroom",
                    sem_class_override="full_figure_adult",
                )
            )

        return {
            "ensemble_id": ens_id,
            "ensemble_type": ens_type,
            "title": "Hero Poet & Supporting Cast Action Ensemble",
            "anchor_x": poet_x,
            "anchor_y": poet_y,
            "description": "Stages the Hero Poet (instance='actor_poet') and active supporting cast in clear negative-space lanes interacting with the scene's set pieces.",
            "layers": layers,
        }

    weave_walk_legs = sorted([
        p["file"] for p in weave_lib["pieces"].values()
        if p.get("source_sheet") == "legs_walk.jpg"
    ])
    weave_run_stairs_legs = sorted([
        p["file"] for p in weave_lib["pieces"].values()
        if p.get("source_sheet") == "legs_run_stairs.jpg"
    ])
    weave_contacts = sorted([
        p["file"] for p in weave_lib["pieces"].values()
        if p.get("category") == "contact"
    ])

    print("[3/6] Composing 80 scenes into 3–4 Cohesive Set-Piece Ensembles (6–9 co-located pieces per scene)...")
    scenes_out: List[Dict[str, Any]] = []
    water_scene_count = 0

    for sc in manifest["scenes"]:
        sc_id = sc["id"]
        poem_num = int(sc["book"])
        sc_idx = int(sc_id.split("-S")[-1]) - 1
        set_id = sc.get("set_id", "")
        atlas = atlases.get(poem_num, {})
        dossier_set = dossier_sets_by_poem.get(poem_num, {}).get(set_id, {})

        framing = infer_camera_framing(sc)
        framing_spec = CAMERA_FRAMING_SPECS[framing]
        audio_info = scene_audio_windows[sc_id]
        scion_shots = audio_info["scion_shots"]
        primary_scion = scion_shots[0] if scion_shots else (
            scion_shots_by_poem[poem_num][0] if scion_shots_by_poem.get(poem_num) else {}
        )

        # World Backdrop
        set_refs = [r for r in dossier_set.get("refs", []) if r in world_shots_by_id]
        reel_shots = [r for r in world_reels_by_poem.get(poem_num, {}).get("shots", []) if r in world_shots_by_id]
        candidate_world_ids = set_refs or reel_shots or list(world_shots_by_id.keys())
        world_shot_id = candidate_world_ids[sc_idx % len(candidate_world_ids)]
        world_shot = world_shots_by_id[world_shot_id]
        district_id = world_shot.get("district") or world_reels_by_poem.get(poem_num, {}).get("district", "naraka")
        district_info = districts_by_id.get(district_id, {})

        still_rel = f"poems/refs/stills/{world_shot_id}.jpg"
        if not (SHOTS_DIR / still_rel).exists():
            still_rel = world_shot["thumb"]

        atlas_scene_list = atlas.get("scenes", [])
        matched_atlas_scene = atlas_scene_list[sc_idx % len(atlas_scene_list)] if atlas_scene_list else {}
        atlas_views: List[str] = []
        for v in matched_atlas_scene.get("views", []):
            v_img = f"poems/{v['img']}" if not v["img"].startswith("poems/") else v["img"]
            if (SHOTS_DIR / v_img).exists():
                atlas_views.append(v_img)
        for ar_ref in dossier_set.get("atlas_refs", []):
            ar_img = f"poems/{ar_ref}" if not ar_ref.startswith("poems/") else ar_ref
            if (SHOTS_DIR / ar_img).exists() and ar_img not in atlas_views:
                atlas_views.append(ar_img)

        clean_plate_file = world_shot["backdrop"]
        canopy_mask_file = None
        if poem_num == 4 and (SHOTS_DIR / "weave/p04_hands/set/plate.jpg").exists():
            clean_plate_file = "weave/p04_hands/set/plate.jpg"
            canopy_mask_file = "weave/p04_hands/set/sky_mask.png"
        elif poem_num == 7 and (SHOTS_DIR / "weave/set/plate.jpg").exists():
            clean_plate_file = "weave/set/plate.jpg"
            canopy_mask_file = "weave/set/canopy_mask.png"

        world_backdrop = {
            "world_shot_id": world_shot_id,
            "world_shot_k": world_shot["k"],
            "district_id": district_id,
            "district_name": district_info.get("name", district_id.title()),
            "realm": district_info.get("realm", ""),
            "palette_glow": district_info.get("glow", []),
            "palette_body": district_info.get("body", []),
            "backdrop_file": world_shot["backdrop"],
            "cel_file": world_shot["cel"],
            "ink_file": world_shot["ink"],
            "still_file": still_rel,
            "clean_plate_file": clean_plate_file,
            "canopy_mask_file": canopy_mask_file,
            "multiplane_sheets": [
                {
                    "file": s["hi"],
                    "plane": s["plane"],
                    "z": s["z"],
                    "zm": s["zm"],
                    "label": s["label"],
                }
                for s in world_shot.get("sheets", [])
                if (SHOTS_DIR / s["hi"]).exists()
            ],
            "atlas_views": atlas_views[:6],
            "camera_grammar": {
                "fov_deg": world_shot.get("fov", 45.0),
                "pitch_deg": world_shot.get("pitch", 0.0),
                "camera_height_m": world_shot.get("height", 1.45),
                "move": primary_scion.get("camera", {}).get("move", world_shot.get("move", "push")),
            },
        }

        # Archive Plate
        atlas_sets = atlas.get("sets", [])
        archive_ref_files: List[str] = [a for a in atlas_views if "/archive/" in a]
        for a_set in atlas_sets:
            s_img = f"poems/{a_set['img']}" if not a_set["img"].startswith("poems/") else a_set["img"]
            if (SHOTS_DIR / s_img).exists() and s_img not in archive_ref_files:
                archive_ref_files.append(s_img)

        poster_file = primary_scion.get("poster", "cel_assets/posters/P01-001.jpg")
        if not (SHOTS_DIR / poster_file).exists():
            poster_file = world_shot["thumb"]
        video_file = primary_scion.get("video", "cel_assets/video/P01-001.mp4")
        scion_atlas_file = primary_scion.get("atlas", "cel_assets/scion/P01-001.jpg")
        key_cels = [kc for kc in primary_scion.get("key_cels", []) if (SHOTS_DIR / kc).exists()]

        combined_text = f"{sc.get('title', '')} {sc.get('treatment', '')}".upper()
        if any(k in combined_text for k in ("TV", "SCREEN", "WINDOW", "PROJECTION", "MIRROR", "DOOR")):
            comp_mode = "window_screen_quad"
            aperture_quad = [[0.54, 0.18], [0.84, 0.18], [0.84, 0.56], [0.54, 0.56]]
        elif any(k in combined_text for k in ("EYE", "IRIS", "MEMORY", "SNAPSHOT", "GALAXY")):
            comp_mode = "iris_memory_aperture"
            aperture_quad = [[0.22, 0.12], [0.78, 0.12], [0.78, 0.68], [0.22, 0.68]]
        else:
            comp_mode = "sky_torn_aperture"
            aperture_quad = [[0.0, 0.0], [1.0, 0.0], [1.0, 0.62], [0.0, 0.68]]

        archive_plate = {
            "scion_shot_id": primary_scion.get("id", f"P{poem_num:02d}-001"),
            "archive_title": primary_scion.get("archive_title", "Prelinger / Atlantis Studio Plate"),
            "archive_year": primary_scion.get("archive_year", 1959),
            "poster_file": poster_file,
            "video_file": video_file,
            "scion_atlas_file": scion_atlas_file,
            "key_cels": key_cels,
            "atlas_archive_refs": archive_ref_files[:6],
            "compositing_mode": comp_mode,
            "aperture_quad": aperture_quad,
            "feather_px": 18,
            "paper_edge_lip_px": 4,
        }

        # -------------------------------------------------------------------
        # Assemble 3 to 4 Cohesive Set-Piece Ensembles for this Scene
        # -------------------------------------------------------------------
        ensembles: List[Dict[str, Any]] = []

        # 1. Water & Shore / Boat / Pool Ensemble (for all 39 water scenes!)
        has_water = sc_id in WATER_SCENE_IDS
        if has_water:
            water_scene_count += 1
            include_boats = (poem_num == 13 and sc_idx in (1, 4, 5)) or sc_id in ("P14-S01", "P14-S04")
            ensembles.append(make_water_shore_ensemble(poem_num, sc_idx, include_boat_planets=include_boats))

        # 2. Poem & Scene-Specific Set-Piece Ensembles (Vehicles, Portals, Interiors, Kinetic Props)
        if poem_num == 1:
            if sc_idx in (0, 1):
                ensembles.append(make_bedroom_window_and_tv_portal_ensemble())
                ensembles.append(make_interior_lamp_and_furniture_ensemble(lamp_x=0.14, lamp_y=0.86))
            elif sc_idx == 2:
                ensembles.append(make_bedroom_window_and_tv_portal_ensemble())
            else:
                ensembles.append(make_vintage_door_ballroom_portal_ensemble())
                ensembles.append(make_interior_lamp_and_furniture_ensemble(lamp_x=0.18, lamp_y=0.86))

        elif poem_num == 2:
            if sc_idx in (0, 3, 4):
                ensembles.append(make_car_ensemble(car_x=0.58, car_y=0.86))
                ensembles.append(make_living_room_window_portal_ensemble(win_x=0.64, win_y=0.82))
            else:
                ensembles.append(make_living_room_window_portal_ensemble(win_x=0.62, win_y=0.82))
                ensembles.append(make_interior_lamp_and_furniture_ensemble(lamp_x=0.20, lamp_y=0.86))
                if sc_idx == 5:
                    ensembles.append(make_rose_window_tambourine_ensemble(shattered=False))

        elif poem_num == 3:
            is_shattered = sc_idx >= 4
            ensembles.append(make_rose_window_tambourine_ensemble(shattered=is_shattered))
            if not has_water:
                ensembles.append(make_interior_lamp_and_furniture_ensemble(lamp_x=0.20, lamp_y=0.86))

        elif poem_num == 4:
            if sc_idx in (1, 3, 4, 5):
                ensembles.append(make_beating_heart_and_hands_ensemble(poet_x=0.36))
            if sc_idx in (2, 3, 4, 5):
                ensembles.append(make_faith_bloom_ensemble(flower_x=0.58, flower_y=0.86))
            if sc_idx == 0:
                ensembles.append(make_beating_heart_and_hands_ensemble(poet_x=0.36))
            if sc_idx == 3:
                ensembles.append(make_clouds_and_light_ensemble(poem_num))

        elif poem_num == 5:
            ensembles.append(make_atlantis_gate_portal_ensemble())
            ensembles.append(make_clouds_and_light_ensemble(poem_num))

        elif poem_num == 6:
            ensembles.append(make_atlantis_gate_portal_ensemble())
            if sc_idx in (0, 2, 4):
                ensembles.append(make_clouds_and_light_ensemble(poem_num))

        elif poem_num == 7:
            ensembles.append(make_dj_booth_ensemble())
            ensembles.append(make_interior_lamp_and_furniture_ensemble(lamp_x=0.14, lamp_y=0.86))

        elif poem_num == 8:
            ensembles.append(make_angel_wings_ensemble(angel_x=0.66, angel_y=0.89))
            if sc_idx in (0, 1, 2):
                ensembles.append(make_dj_booth_ensemble())
            else:
                ensembles.append(make_clouds_and_light_ensemble(poem_num))

        elif poem_num == 9:
            ensembles.append(make_phone_booth_ensemble(booth_x=0.64, booth_y=0.86))
            if sc_idx in (0, 3):
                ensembles.append(make_clouds_and_light_ensemble(poem_num))

        elif poem_num == 10:
            ensembles.append(make_motorcycle_ensemble(bike_x=0.52, bike_y=0.86, parked=(sc_idx in (0, 5))))
            if not has_water:
                ensembles.append(make_clouds_and_light_ensemble(poem_num))

        elif poem_num == 11:
            if sc_idx == 0:
                ensembles.append(make_motorcycle_ensemble(bike_x=0.24, bike_y=0.87, parked=True))
            else:
                ensembles.append(make_atlantis_gate_portal_ensemble())
            ensembles.append(make_clouds_and_light_ensemble(poem_num))

        elif poem_num == 12:
            ensembles.append(make_hourglass_ensemble(hg_x=0.52, hg_y=0.84))
            if not has_water:
                ensembles.append(make_atlantis_gate_portal_ensemble())

        elif poem_num == 13:
            if sc_idx == 3:
                ensembles.append(make_faith_bloom_ensemble(flower_x=0.56, flower_y=0.86))
                ensembles.append(make_clouds_and_light_ensemble(poem_num))
            else:
                ensembles.append(make_cafe_table_ensemble(table_x=0.58, table_y=0.88))

        elif poem_num == 14:
            ensembles.append(make_vintage_door_ballroom_portal_ensemble())
            if sc_idx == 3:
                ensembles.append(make_car_ensemble(car_x=0.62, car_y=0.86))
            elif not has_water:
                ensembles.append(make_clouds_and_light_ensemble(poem_num))

        # 3. Hero Poet & Supporting Cast Action Ensemble (always included so every scene has live actors!)
        ensembles.append(make_hero_and_extras_ensemble(poem_num, sc_idx, sc_id))

        # Keep 3 to 4 cohesive ensembles per scene, and cap total cut-out layers to 6–9 high-impact pieces!
        ensembles = ensembles[:4]
        stage_layers: List[Dict[str, Any]] = []
        for ens in ensembles:
            for lyr in ens["layers"]:
                stage_layers.append(lyr)

        # Ensure actor_poet is always preserved if we trim to 9 layers max
        if len(stage_layers) > 9:
            poet_layers = [l for l in stage_layers if l["instance"] == "actor_poet"]
            other_layers = [l for l in stage_layers if l["instance"] != "actor_poet"]
            stage_layers = other_layers[:8] + poet_layers[:1]

        # Sort back-to-front by Z descending
        stage_layers.sort(key=lambda item: float(item.get("z", 1.0)), reverse=True)

        # Walking & Action Assets from weave
        is_stairs_or_climb = any(k in combined_text for k in ("STAIR", "STEP", "CLIMB", "ASCENT", "FIRE ESCAPE", "VIADUCT", "HILL"))
        is_crouch_or_fall = any(k in combined_text for k in ("CROUCH", "KNEEL", "FALL", "FLOOR", "PRONE"))
        walking_and_action_assets = {
            "primary_rig_id": "poet_black_tshirt" if poem_num in (1, 2, 3) else "poet_tracksuit_31",
            "locomotion_mode": "run_stairs_ascent" if is_stairs_or_climb else ("crouch_floor_recovery" if is_crouch_or_fall else "walk_stride_cycle"),
            "weave_leg_cycle_files": [
                f"weave/{f}" for f in (weave_run_stairs_legs[:6] if is_stairs_or_climb else weave_walk_legs[:6])
            ],
            "weave_contact_arm_files": [
                f"weave/{f}" for f in weave_contacts[(sc_idx * 2) % max(1, len(weave_contacts) - 3):(sc_idx * 2) % max(1, len(weave_contacts) - 3) + 3]
            ],
            "crouch_recovery_manifest": "weave/assets/poet.crouch_manifest.json" if is_crouch_or_fall else "weave/assets/poet.floor_recovery_manifest.json",
        }

        scene_plan = {
            "id": sc_id,
            "scene_num": sc["scene_num"],
            "book": poem_num,
            "bookTitle": sc["bookTitle"],
            "title": sc["title"],
            "movement": sc.get("movement", ""),
            "set_id": set_id,
            "set_name": dossier_set.get("name", set_id.replace("_", " ").title()),
            "set_look": dossier_set.get("look", ""),
            "set_light": dossier_set.get("light", ""),
            "seconds": sc["seconds"],
            "audio_window": audio_info["audio_window"],
            "poem_vocal_window": audio_info["poem_vocal_window"],
            "poem_container_window": audio_info["poem_container_window"],
            "camera_framing": framing,
            "camera_framing_spec": framing_spec,
            "has_water_ensemble": has_water,
            "breathable_negative_space_ratio": round(clamp(0.46 - 0.012 * len(stage_layers), 0.35, 0.45), 2),
            "world_backdrop": world_backdrop,
            "archive_plate": archive_plate,
            "walking_and_action_assets": walking_and_action_assets,
            "shot_count": sc.get("shot_count", len(sc.get("shots", []))),
            "shots": sc.get("shots", []),
            "beats": sc.get("beats", []),
            "lines": sc.get("lines", []),
            "treatment": sc.get("treatment", ""),
            "composePrompt": sc.get("composePrompt", ""),
            "exitState": sc.get("exitState", ""),
            "ensembles": ensembles,
            "stage_layers": stage_layers,
            "staged_placements": stage_layers,
        }
        scenes_out.append(scene_plan)

    print(f"  Water & Shore multi-layer scenes assembled: {water_scene_count}/80 scenes")

    sheets_scale_index: Dict[str, Dict[str, Any]] = {}
    for sh in catalog["sheets"]:
        sid = sh["id"]
        sh_parts = [part_classifications[pt["id"]] for pt in sh.get("parts", [])]
        sheets_scale_index[sid] = {
            "sheet_id": sid,
            "subfolder": sh.get("subfolder", ""),
            "kind": sh.get("kind", ""),
            "poems": sh.get("poems", []),
            "part_count": len(sh_parts),
            "dominant_semantic_class": sh_parts[0]["semantic_class"] if sh_parts else "medium_prop",
            "parts": {
                p["part_id"]: {
                    "semantic_class": p["semantic_class"],
                    "plane": p["plane"],
                    "z": p["z"],
                    "scale": p["scale"],
                    "y": p["y"],
                    "scale_cm": p["scale_cm"],
                }
                for p in sh_parts
            },
        }

    output_payload = {
        "version": "2.1.0",
        "generated_by": "shots/arena/parts/kit3/build_scene_collage_scales.py",
        "title": "WYGWYL Multiplane Set Architecture, Cohesive Set-Piece Ensembles & Calibrated Scene Scale Plans",
        "audio_master": {
            "file": "film/suite_audio.mp3",
            "duration_sec": 1440.072,
        },
        "semantic_classes": SEMANTIC_CLASS_SPECS,
        "camera_framing_specs": CAMERA_FRAMING_SPECS,
        "stats": {
            "poem_count": 14,
            "scene_count": len(scenes_out),
            "water_scene_count": water_scene_count,
            "min_layers_per_scene": min(len(s["stage_layers"]) for s in scenes_out),
            "max_layers_per_scene": max(len(s["stage_layers"]) for s in scenes_out),
            "avg_layers_per_scene": round(sum(len(s["stage_layers"]) for s in scenes_out) / len(scenes_out), 2),
            "total_catalog_sheets": len(sheets_by_id),
            "total_catalog_cut_parts": len(parts_by_id),
            "semantic_class_counts": class_counts,
        },
        "scenes": scenes_out,
        "scenes_by_id": {s["id"]: s for s in scenes_out},
        "catalog_scale_index": sheets_scale_index,
    }

    print(f"[4/6] Writing {OUTPUT_PATH} ...")
    OUTPUT_PATH.write_text(json.dumps(output_payload, indent=2))
    print(f"  Wrote {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size / (1024 * 1024):.2f} MB)")

    print(f"[5/6] Merging ensembles, stage_layers, and staged_placements into {MANIFEST_PATH} ...")
    plans_by_id = {s["id"]: s for s in scenes_out}
    for m_sc in manifest.get("scenes", []):
        plan = plans_by_id.get(m_sc["id"])
        if plan:
            m_sc["camera_framing"] = plan["camera_framing"]
            m_sc["has_water_ensemble"] = plan["has_water_ensemble"]
            m_sc["breathable_negative_space_ratio"] = plan["breathable_negative_space_ratio"]
            m_sc["world_backdrop"] = plan["world_backdrop"]
            m_sc["archive_plate"] = plan["archive_plate"]
            m_sc["audio_window"] = plan["audio_window"]
            m_sc["ensembles"] = plan["ensembles"]
            m_sc["stage_layers"] = plan["stage_layers"]
            m_sc["staged_placements"] = plan["staged_placements"]

    for p_entry in manifest.get("poems", []):
        b_num = int(p_entry.get("book", p_entry.get("num", 0)))
        p_scenes = [s for s in scenes_out if int(s["book"]) == b_num]
        p_entry["scenes"] = [
            {
                "id": s["id"],
                "scene_num": s["scene_num"],
                "title": s["title"],
                "set_id": s["set_id"],
                "camera_framing": s["camera_framing"],
                "has_water_ensemble": s["has_water_ensemble"],
                "audio_window": s["audio_window"],
                "ensembles": s["ensembles"],
                "stage_layers": s["stage_layers"],
                "staged_placements": s["staged_placements"],
            }
            for s in p_scenes
        ]

    manifest["scene_collage_plans"] = {
        "version": "2.1.0",
        "water_scene_count": water_scene_count,
        "scenes_by_id": {
            s["id"]: {
                "id": s["id"],
                "camera_framing": s["camera_framing"],
                "has_water_ensemble": s["has_water_ensemble"],
                "breathable_negative_space_ratio": s["breathable_negative_space_ratio"],
                "audio_window": s["audio_window"],
                "ensembles": s["ensembles"],
                "stage_layers": s["stage_layers"],
                "staged_placements": s["staged_placements"],
            }
            for s in scenes_out
        },
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    print(f"  Updated {MANIFEST_PATH} ({MANIFEST_PATH.stat().st_size / (1024 * 1024):.2f} MB)")

    print("[6/6] Running strict verification checks across all 80 scenes...")
    missing_files: List[str] = []
    scale_violations: List[str] = []
    headless_torso_actors: List[str] = []
    layer_count_violations: List[str] = []

    for sc in scenes_out:
        sid = sc["id"]
        n_layers = len(sc["stage_layers"])
        n_ens = len(sc["ensembles"])
        if not (5 <= n_layers <= 9):
            layer_count_violations.append(f"{sid}: {n_layers} layers (expected 6..9)")
        if not (2 <= n_ens <= 4):
            layer_count_violations.append(f"{sid}: {n_ens} ensembles (expected 2..4)")
        for lyr in sc["stage_layers"]:
            lf = lyr["file"]
            if not (SHOTS_DIR / lf).exists():
                missing_files.append(f"{sid} {lyr['instance']}: {lf}")
            s_cls = lyr["semantic_class"]
            sc_val = lyr["scale"]
            lo, hi = SEMANTIC_CLASS_SPECS[s_cls]["scale_range"]
            if not (lo - 1e-4 <= sc_val <= hi + 1e-4):
                scale_violations.append(f"{sid} {lyr['instance']} ({s_cls}): scale {sc_val} outside [{lo}, {hi}]")
            if lyr["plane"] == "P2" and lyr["sheet_id"] in BODY_PART_ONLY_SHEETS:
                headless_torso_actors.append(f"{sid} {lyr['instance']}: {lyr['part_id']}")

    print(f"  Scenes verified: {len(scenes_out)}/80")
    print(f"  Water scenes: {water_scene_count}/80 (target >= 30)")
    print(f"  Layers per scene: min={output_payload['stats']['min_layers_per_scene']}, max={output_payload['stats']['max_layers_per_scene']}, avg={output_payload['stats']['avg_layers_per_scene']}")
    print(f"  Missing image files: {len(missing_files)}")
    print(f"  Physical scale violations: {len(scale_violations)}")
    print(f"  Layer/ensemble count violations: {len(layer_count_violations)}")
    print(f"  Headless torso vests on P2: {len(headless_torso_actors)}")

    if missing_files or scale_violations or headless_torso_actors or layer_count_violations:
        for err in (missing_files + scale_violations + headless_torso_actors + layer_count_violations)[:20]:
            print("   ERROR:", err)
        raise SystemExit(1)

    print("SUCCESS: All 80 scenes composed into cohesive Set-Piece Ensembles and merged into wygwyl_atlas_manifest.json!")


if __name__ == "__main__":
    main()
