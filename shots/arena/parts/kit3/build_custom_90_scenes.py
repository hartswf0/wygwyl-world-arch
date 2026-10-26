#!/usr/bin/env python3
"""
build_custom_90_scenes.py
=========================
Hand-crafted, visually verified multiplane scene compositions for all 90 scenes
(`01.0` .. `14.6`) across the 14 playable poems in `shots/play/levels/01..14/`.

Every single scene is keyed by its exact scene key (`sc["key"]`), paired with a
hand-picked `shots/world/<id>/backdrop.webp` plate from the 81-backdrop contact
sheet, given pixel-registered composite props (car + wheel-arch wheels + cabin
parents, cafe racer motorcycle, DJ booth + VU meters + speakers, 3D glass phone
booth, harbor bistro table + espresso cup, progressive temple states, burning
hourglasses, progressive vintage doors), and assigned scene-specific initial
character postures and counterpart blocking.
"""

from __future__ import annotations

import json
import math
import pathlib
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


SHOTS_DIR = pathlib.Path(__file__).resolve().parents[3]
PLAY_DIR = SHOTS_DIR / "play"
LEVELS_DIR = PLAY_DIR / "levels"
RELEASE_DIR = SHOTS_DIR / "arena" / "parts" / "kit3" / "release_v2"
MANIFEST_PATH = RELEASE_DIR / "wygwyl_atlas_manifest.json"
CATALOG_OUT_PATH = PLAY_DIR / "level_assets_catalog.json"
SCRATCH_DIR = pathlib.Path("/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584/scratch")


def L(
    part_id: str,
    label: str,
    plane: str,
    z: float,
    x: float,
    y: float,
    scale: float,
    anim_role: str = "static",
    station_title: Optional[str] = None,
    flip: bool = False,
    alpha: float = 0.98,
) -> Dict[str, Any]:
    return {
        "part_id": part_id,
        "label": label,
        "plane": plane,
        "z": z,
        "x": x,
        "y": y,
        "scale": scale,
        "anim_role": anim_role,
        "station_title": station_title,
        "flip": flip,
        "alpha": alpha,
    }


def car_ensemble(
    cx: float,
    floor_y: float = 0.86,
    car_scale: float = 0.25,
    station_title: str = "1990s Family Sedan",
    with_parents: bool = False,
) -> List[Dict[str, Any]]:
    """
    Pixel-verified 1990s Family Sedan (`02.props.car__p01`, 813x255):
      - Front wheel arch center is at -0.585 * car_scale in 16:9 normalized width
      - Rear wheel arch center is at +0.456 * car_scale in 16:9 normalized width
      - Wheel diameter in wheel arch is 0.45 * car_scale
      - Arguing parents (`parents.02.car-argument__p03`) sit behind the window cutout (`z=1.43 > 1.40`)
    """
    body_y = round(floor_y - 0.05 * car_scale, 4)
    wf_x = round(cx - 0.585 * car_scale, 4)
    wr_x = round(cx + 0.456 * car_scale, 4)
    w_scale = round(0.45 * car_scale, 4)
    layers = [
        L("02.props.car__p01", "1990s Family Sedan Body", "P3", 1.40, cx, body_y, car_scale, "car_chassis", station_title),
        L("02.props.car__p05", "Sedan Front Tire & Rim", "P3", 1.38, wf_x, floor_y, w_scale, "wheel_spin", None),
        L("02.props.car__p06", "Sedan Rear Tire & Rim", "P3", 1.38, wr_x, floor_y, w_scale, "wheel_spin", None),
    ]
    if with_parents:
        layers.append(
            L(
                "parents.02.car-argument__p03",
                "Parents Arguing in Car Cabin",
                "P3",
                1.43,
                round(cx - 0.04 * car_scale, 4),
                round(body_y - 0.46 * car_scale, 4),
                round(0.42 * car_scale, 4),
                "lamp_glow",
                None,
            )
        )
    return layers


# ---------------------------------------------------------------------------
# Hand-Crafted Scene Specifications for All 90 Scenes (`01.0` .. `14.6`)
# ---------------------------------------------------------------------------
CUSTOM_SCENES: Dict[str, Dict[str, Any]] = {
    # =======================================================================
    # POEM 01 · OUT OF LIFE
    # =======================================================================
    "01.0": {
        "backdrop": "world/9572112a_1/backdrop.webp",
        "floor": 612,
        "initial_cue": "reading_pages",
        "counterpart": None,
        "layers": [
            L("01.props.room__p19", "Bedroom Baseboard & Floor Molding", "P4", 2.60, 0.50, 0.89, 0.16, "static", None),
            L("01.props.room__p01", "Three-Drawer Wooden Bedroom Dresser", "P3", 1.44, 0.20, 0.88, 0.34, "drawer_slide", "Wooden Bedroom Dresser"),
            L("01.props.room__p18", "Flickering Bedroom Television & Stand", "P3", 1.42, 0.48, 0.88, 0.32, "portal_tv_flicker", "Flickering TV Stand"),
            L("01.props.window__p01", "Closed High-Rise Sash Window", "P4", 2.40, 0.80, 0.85, 0.50, "portal_aperture", "High-Rise Sash Window"),
        ],
    },
    "01.1": {
        "backdrop": "world/ef456e2a_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_L",
        "counterpart": None,
        "layers": [
            L("01.props.room__p14", "Wide Bedroom Chest of Drawers", "P3", 1.45, 0.21, 0.88, 0.28, "drawer_slide", "Hallway & Drawers"),
            L("01.props.window__p01", "Amber-Lit Apartment Sash Window", "P4", 2.42, 0.52, 0.84, 0.52, "portal_aperture", "Haze at the Window"),
            L("01.fx.haze-words__p08", "Drifting Amber Haze Plume", "P1", 0.48, 0.56, 0.54, 0.18, "cloud_drift_L", None),
            L("01.props.window__p13", "Iron Fire-Escape Balcony Landing", "P4", 2.36, 0.82, 0.86, 0.32, "fire_escape_landing", "Fire-Escape Landing"),
        ],
    },
    "01.2": {
        "backdrop": "world/caaf4b3a_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "fire_escape_climb",
        "counterpart": {"key": "ex/ex_jacket", "x": 1020, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("01.props.window__p01", "Open Apartment Sash Window", "P4", 2.46, 0.18, 0.85, 0.44, "portal_aperture", "Open Sash Window"),
            L("01.props.window__p13", "Iron Fire-Escape Balcony & Rail", "P4", 2.38, 0.48, 0.86, 0.36, "fire_escape_landing", "Iron Fire Escape"),
            L("01.hero.severn__p11", "Zig-Zag Iron Fire-Escape Stairs", "P4", 2.34, 0.78, 0.86, 0.42, "fire_escape_landing", "Edge of the Drop"),
        ],
    },
    "01.3": {
        "backdrop": "world/38543022_3/backdrop.webp",
        "floor": 620,
        "initial_cue": "fall_invert",
        "counterpart": {"key": "ex/ex_jacket", "x": 980, "dir": 1, "cue": "fall_back", "y_offset": -75},
        "layers": [
            L("01.set.city_fall_void__p01", "Vertical Skyscraper Canyon Left", "P4", 2.52, 0.18, 0.86, 0.56, "portal_other_world", "Tower Canyon Wall"),
            L("01.fx.haze-words__p05", "Tumbling Haze Cloud in Void", "P3", 1.40, 0.50, 0.58, 0.24, "cloud_drift_L", "The Vertical Freefall"),
            L("01.set.city_fall_void__p02", "Vertical Skyscraper Canyon Right", "P4", 2.50, 0.82, 0.86, 0.56, "portal_other_world", None),
            L("01.props.chandeliers__p10", "Ballroom Chandelier Rising Below", "P3", 1.44, 0.78, 0.42, 0.22, "chandelier_sway", "Skylight Above Ballroom"),
        ],
    },
    "01.4": {
        "backdrop": "world/cb6cbbfc_1/backdrop.webp",
        "floor": 612,
        "initial_cue": "sprint_pursuit",
        "counterpart": {"key": "vintage_woman/gown", "x": 920, "dir": -1, "cue": "waltz"},
        "layers": [
            L("14.set.vintage_party__p01", "1940s Wood-Panelled Ballroom Wall", "P4", 2.56, 0.50, 0.86, 0.34, "static", None),
            L("01.props.chandeliers__p10", "Crystal Ballroom Chandelier West", "P3", 1.48, 0.24, 0.34, 0.22, "chandelier_sway", "Crystal Chandelier Hall"),
            L("14.set.vintage_party__p03", "Grand Ballroom Timber Archway", "P4", 2.42, 0.52, 0.86, 0.50, "portal_other_world", "Vintage Waltz Floor"),
            L("01.props.chandeliers__p11", "Crystal Ballroom Chandelier East", "P3", 1.48, 0.78, 0.34, 0.22, "chandelier_sway", "Ballroom Bandstand"),
        ],
    },
    "01.5": {
        "backdrop": "world/b0118d62_2/backdrop.webp",
        "floor": 616,
        "initial_cue": "fall_midair",
        "counterpart": {"key": "ex/ex_jacket", "x": 960, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("14.set.vintage_party__p03", "Ballroom Threshold Archway", "P4", 2.46, 0.20, 0.86, 0.48, "portal_aperture", "Ballroom Colonnade"),
            L("01.props.trapdoor__p12", "Open Floor Trapdoor Into the Abyss", "P3", 1.36, 0.52, 0.90, 0.28, "portal_aperture", "Hole in the Floor"),
            L("01.props.trapdoor__p11", "Shattered Trapdoor Timber Frame", "P3", 1.34, 0.80, 0.89, 0.24, "drawer_slide", "Rim of the Void"),
        ],
    },

    # =======================================================================
    # POEM 02 · FLASHING LIGHTS
    # =======================================================================
    "02.0": {
        "backdrop": "world/997f5a7b_3/backdrop.webp",
        "floor": 618,
        "initial_cue": "fall_midair",
        "counterpart": {"key": "ex/ex_jacket", "x": 1000, "dir": 1, "cue": "fall_back", "y_offset": -68},
        "layers": [
            L("02.set.black_void__p01", "Inward-Caving Dark Wall Left", "P4", 2.48, 0.18, 0.88, 0.58, "portal_other_world", "Walls Caving Inward"),
            L("02.fx.lights-iris__p01", "Sweeping White Headlight Beam", "P1", 0.48, 0.48, 0.56, 0.18, "headlight_beam", "Falling With Headlights Off"),
            L("02.fx.lights-iris__p02", "Flashing Amber Hazard Beam", "P1", 0.46, 0.56, 0.72, 0.18, "headlight_beam", None),
            L("02.set.black_void__p02", "Inward-Caving Dark Wall Right", "P4", 2.48, 0.82, 0.88, 0.58, "portal_other_world", "The Silent Scream"),
        ],
    },
    "02.1": {
        "backdrop": "world/fb5ef893_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "bed_despair_sit",
        "counterpart": None,
        "layers": [
            L("02.set.bedroom_night__p08", "Unmade Midnight Bed & Blanket", "P3", 1.44, 0.22, 0.88, 0.24, "lamp_base", "Midnight Bed"),
            L("02.props.mirror-phone-rings__p06", "Glowing Smartphone Emergency Call", "P3", 1.38, 0.36, 0.78, 0.16, "phone_ring", None),
            L("02.set.bedroom_night__p03", "Standing Bedroom Mirror Glass", "P4", 2.42, 0.52, 0.85, 0.44, "portal_other_world", None),
            L("02.set.bedroom_night__p02", "Standing Bedroom Mirror Frame (1:08 AM)", "P4", 2.40, 0.52, 0.86, 0.46, "portal_aperture", "The Midnight Mirror"),
            L("02.props.poet-eye-aperture__p12", "Dilating Poet Eye Opening to Past", "P4", 2.44, 0.80, 0.66, 0.24, "portal_aperture", "Dilating Eye Aperture"),
        ],
    },
    "02.2": {
        "backdrop": "world/7fdacba9_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_R",
        "preferred_actor": "young_poet/pajamas_winter",
        "counterpart": None,
        "layers": [
            L("02.set.living_room_1990s__p04", "1990s Floral Living Room Sofa", "P3", 1.46, 0.20, 0.87, 0.24, "lamp_base", "Living Room Sofa"),
            L("02.props.window__p22", "1990s Living Room Window & Curtains", "P4", 2.44, 0.44, 0.78, 0.30, "portal_aperture", "Childhood Window View"),
            *car_ensemble(cx=0.72, floor_y=0.87, car_scale=0.25, station_title="Family Sedan Pulling Up", with_parents=False),
            L("02.fx.lights-iris__p01", "Headlight Glare Across Ceiling", "P1", 0.46, 0.52, 0.42, 0.16, "headlight_beam", None),
        ],
    },
    "02.3": {
        "backdrop": "world/34a1d5c3_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_L",
        "preferred_actor": "young_poet/pajamas_winter",
        "counterpart": {"key": "ghost_child/ghost_nightclothes", "x": 330, "dir": 1, "cue": "idle"},
        "layers": [
            L("02.hero.childhouse__p01", "Childhood Doorway & Pencil Notches", "P4", 2.44, 0.22, 0.86, 0.46, "portal_aperture", "Doorpost Height Marks"),
            L("02.props.window__p22", "Frost-Rimed Living Room Window", "P4", 2.42, 0.52, 0.78, 0.30, "portal_aperture", "Frost at the Window"),
            L("02.set.living_room_1990s__p04", "1990s Floral Living Room Sofa", "P3", 1.46, 0.80, 0.87, 0.24, "lamp_base", None),
            L("02.props.tambourine__p08", "Ghost Child's Wooden Tambourine", "P3", 1.34, 0.76, 0.72, 0.15, "tambourine_arc", "The Ghost's Tambourine"),
        ],
    },
    "02.4": {
        "backdrop": "world/7f7e3980_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "preferred_actor": "young_poet/pajamas_winter",
        "counterpart": None,
        "layers": [
            L("02.props.window__p22", "Living Room Window & Floral Curtains", "P4", 2.44, 0.22, 0.78, 0.30, "curtain_sway_L", "Raised Window Blinds"),
            *car_ensemble(cx=0.58, floor_y=0.87, car_scale=0.27, station_title="Parents Arguing in the Car", with_parents=True),
            L("02.fx.lights-iris__p02", "Flashing Amber Hazard Wash", "P1", 0.46, 0.82, 0.80, 0.18, "headlight_beam", "Flashing Hazard Lights"),
        ],
    },
    "02.5": {
        "backdrop": "world/8bc7b3e2_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "sprint_pursuit",
        "preferred_actor": "young_poet/pajamas_winter",
        "counterpart": {"key": "ghost_child/ghost_nightclothes", "x": 240, "dir": 1, "cue": "idle"},
        "layers": [
            L("02.props.window__p21", "Cracked Living Room Window & Drapes", "P4", 2.44, 0.22, 0.78, 0.30, "portal_aperture", "Living Room Window"),
            L("02.props.tambourine__p08", "Wooden Tambourine Hurling Outward", "P3", 1.28, 0.52, 0.56, 0.16, "tambourine_arc", "Tambourine in Flight"),
            L("02.hero.childhouse__p11", "Shattering Glass Window Pane", "P4", 2.40, 0.78, 0.78, 0.44, "portal_aperture", "Shattering Window Glass"),
            L("02.hero.childhouse__p15", "Forking Glass Hole Into the Night", "P3", 1.38, 0.78, 0.78, 0.38, "portal_other_world", None),
        ],
    },

    # =======================================================================
    # POEM 03 · HOW TO BREAK OFF AN ENGAGEMENT
    # =======================================================================
    "03.0": {
        "backdrop": "world/e0154328_1/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "ex/ex_jacket", "x": 960, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("03.props.rose-window__p10", "Stained-Glass Gothic Rose Window", "P4", 2.46, 0.22, 0.58, 0.38, "stained_glass_glow", "Gothic Rose Window"),
            L("02.props.tambourine__p08", "Tambourine Ringing Through the Nave", "P3", 1.28, 0.50, 0.54, 0.15, "tambourine_arc", "Arc of the Tambourine"),
            L("03.hero.chapel__p11", "Stone Gothic Chapel Nave & Arch", "P4", 2.42, 0.78, 0.86, 0.50, "portal_aperture", "Chapel Sanctuary Arch"),
        ],
    },
    "03.1": {
        "backdrop": "world/fd7ea369_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_L",
        "counterpart": None,
        "layers": [
            L("03.hero.chapel.interior-states__p10", "Tall Gothic Stained-Glass Lancet", "P4", 2.46, 0.20, 0.84, 0.48, "portal_aperture", "Empty Choir & Windows"),
            L("03.hero.chapel.interior-states__p03", "Abandoned Wooden Chapel Pew", "P3", 1.44, 0.50, 0.88, 0.26, "lamp_base", "Abandoned Wedding Pews"),
            L("03.props.cobwebs__p01", "Draped Sanctuary Cobwebs", "P3", 1.38, 0.76, 0.68, 0.24, "curtain_sway_L", "Cobwebbed Baptist Pool"),
            L("03.hero.chapel.interior-states__p11", "East Gothic Stained-Glass Window", "P4", 2.46, 0.82, 0.84, 0.48, "portal_aperture", None),
        ],
    },
    "03.2": {
        "backdrop": "world/3b7236cf_2/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "ex/ex_jacket", "x": 1000, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("03.set.chapel_side_doors__p01", "Left Arched Wooden Side Door", "P4", 2.44, 0.20, 0.86, 0.48, "portal_aperture", "Left Chapel Side Door"),
            L("03.props.gifts-bread-cups__p09", "Opened Wedding Gift Box", "P3", 1.40, 0.48, 0.87, 0.20, "lamp_glow", "Gifts at the Side Doors"),
            L("03.props.gifts-bread-cups__p12", "Abandoned Silver Altar Chalice", "P3", 1.38, 0.60, 0.87, 0.18, "lamp_glow", None),
            L("03.set.chapel_side_doors__p02", "Right Arched Wooden Exit Door", "P4", 2.44, 0.80, 0.86, 0.48, "portal_aperture", "Right Departure Door"),
        ],
    },
    "03.3": {
        "backdrop": "world/42e101f6_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "fall_back_start",
        "counterpart": None,
        "layers": [
            L("03.fx.storm-light__p15", "Storm-Lashed Gothic Window West", "P4", 2.46, 0.22, 0.84, 0.44, "portal_aperture", "Thunder in the Nave"),
            L("03.hero.chapel.decay__p01", "Weathered Stone Bell-Gable Arch", "P4", 2.42, 0.52, 0.86, 0.48, "portal_aperture", "The Storm Breaks"),
            L("03.fx.storm-light__p07", "Jagged White Lightning Bolt", "P1", 0.46, 0.78, 0.62, 0.38, "light_ray", "Lightning & Downpour"),
        ],
    },
    "03.4": {
        "backdrop": "world/590a0c02_0/backdrop.webp",
        "floor": 616,
        "initial_cue": "walk_away_back",
        "counterpart": {"key": "ex/ex_jacket", "x": 1020, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("03.hero.chapel.ruin__p01", "Collapsed Stone Chapel Archway", "P4", 2.44, 0.22, 0.86, 0.38, "portal_aperture", "Collapsed Chapel Stone"),
            L("03.props.gifts-bread-cups__p03", "Daily Bread Soaked on the Shore", "P3", 1.40, 0.50, 0.88, 0.18, "wave_mid", "Remnants on the Shore"),
            L("03.props.strings-footprints__p11", "Parting Footsteps in Wet Sand", "P3", 1.36, 0.78, 0.89, 0.26, "drawer_slide", "Footsteps Leading Away"),
        ],
    },
    "03.5": {
        "backdrop": "world/993cc7a2_0/backdrop.webp",
        "floor": 616,
        "initial_cue": "fall_landed",
        "counterpart": None,
        "layers": [
            L("03.hero.chapel.ruin__p01", "Broken Stone Arch on the Tide", "P4", 2.42, 0.22, 0.86, 0.36, "portal_aperture", "Ruined Shore Arch"),
            L("03.props.tambourine-broken__p13", "Shattered Tambourine Rim & Skin", "P3", 1.34, 0.52, 0.88, 0.20, "tambourine_arc", "Shattered Tambourine"),
            L("04.props.word-shore__p22", "Rusted Shore Lantern at Dusk", "P3", 1.40, 0.80, 0.86, 0.28, "lamp_glow", "Tide Line at Dusk"),
        ],
    },

    # =======================================================================
    # POEM 04 · NEVERMORE
    # =======================================================================
    "04.0": {
        "backdrop": "world/7a904269_0/backdrop.webp",
        "floor": 616,
        "initial_cue": "shore_recovery",
        "counterpart": None,
        "layers": [
            L("04.set.shore_night__p08", "Wind-Swept Shore Tree West", "P4", 2.46, 0.20, 0.86, 0.38, "curtain_sway_L", "Ash-Covered Shore"),
            L("04.props.word-shore__p08", "Carved NEVERMORE Stone Tablet", "P3", 1.40, 0.50, 0.88, 0.24, "wave_mid", "Broken Pieces on Sand"),
            L("04.set.shore_night__p06", "Charred Wildfire Driftwood Stump", "P3", 1.42, 0.78, 0.87, 0.26, "static", "Charred Stump & Raven"),
            L("04.props.ravens-stumps__p03", "Perched Black Raven on Stump", "P3", 1.36, 0.78, 0.66, 0.20, "wing_flap_L", None),
        ],
    },
    "04.1": {
        "backdrop": "world/3238a164_1/backdrop.webp",
        "floor": 616,
        "initial_cue": "still_sentinel",
        "counterpart": None,
        "layers": [
            L("04.fx.moon-reach__p01", "Pale Full Moon Over Still Sea", "P5", 3.60, 0.24, 0.30, 0.22, "sun_pulse", "Moon Over Still Water"),
            L("04.props.word-shore__p23", "Still Wrought-Iron Shore Lantern", "P3", 1.42, 0.50, 0.86, 0.28, "static", "The Muted Waves"),
            L("04.set.shore_night__p09", "Still Shore Tree in Silence", "P4", 2.42, 0.78, 0.86, 0.36, "static", "Muted Trees in Silence"),
            L("04.props.ravens-stumps__p04", "Silent Watching Raven", "P3", 1.38, 0.82, 0.64, 0.18, "static", None),
        ],
    },
    "04.2": {
        "backdrop": "world/ef9f6c7e_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "kneel_hollow",
        "counterpart": None,
        "layers": [
            L("04.props.word-shore__p08", "Carved NEVERMORE Relic in Sand", "P3", 1.42, 0.22, 0.88, 0.22, "drawer_slide", "Folded Whispers"),
            L("04.props.heart__p10", "Throbbing Poet Heart on Stand", "P3", 1.32, 0.50, 0.87, 0.32, "heart_beat", "The Heart on the Sand"),
            L("04.hero.viaduct__p02", "Stone Coastal Wall & Incline Steps", "P4", 2.44, 0.80, 0.86, 0.42, "portal_aperture", "Steps Toward the Incline"),
        ],
    },
    "04.3": {
        "backdrop": "world/3a2ddc9d_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": None,
        "layers": [
            L("04.hero.viaduct__p02", "Lower Stone Viaduct Retaining Wall", "P4", 2.44, 0.22, 0.86, 0.42, "fire_escape_landing", "Base of the Incline"),
            L("04.props.faith-blooms__p27", "First Golden Mustard-Seed Bloom", "P3", 1.36, 0.50, 0.87, 0.28, "flower_bloom", "Handcrafted Faith Bloom"),
            L("04.hero.viaduct__p04", "Arched Stone Viaduct Bridge", "P4", 2.46, 0.78, 0.86, 0.44, "portal_aperture", "Crest of the Trail"),
            L("04.props.ravens-stumps__p11", "Soaring Raven Overhead", "P5", 3.50, 0.68, 0.28, 0.20, "wing_flap_R", None),
        ],
    },
    "04.4": {
        "backdrop": "world/2ce9173b_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_L",
        "counterpart": None,
        "layers": [
            L("04.set.night_garden_field__p04", "Perspective Rows of Golden Blooms", "P4", 2.52, 0.50, 0.84, 0.14, "static", None),
            L("04.props.faith-blooms__p27", "Golden Mustard Bloom West", "P3", 1.38, 0.22, 0.87, 0.28, "flower_bloom", "West Garden Row"),
            L("04.props.faith-blooms__p13", "Tall Sunflower Stalk & Leaves", "P3", 1.36, 0.52, 0.88, 0.28, "flower_bloom", None),
            L("04.props.faith-blooms__p08", "Golden Sunflower Head in Full Bloom", "P3", 1.34, 0.52, 0.68, 0.22, "flower_bloom", "Center of the Night Field"),
            L("04.fx.moon-reach__p01", "Luminous Full Moon Overhead", "P5", 3.60, 0.78, 0.26, 0.22, "sun_pulse", "Moonlit Garden Edge"),
        ],
    },
    "04.5": {
        "backdrop": "world/5dcae595_1/backdrop.webp",
        "floor": 616,
        "initial_cue": "blind_search",
        "counterpart": None,
        "layers": [
            L("04.fx.moon-reach__p04", "Dark Cloud Covering the Moon", "P5", 3.55, 0.50, 0.28, 0.24, "cloud_drift_L", None),
            L("04.fx.moon-reach__p09", "Lit Pool of Red Soil in Darkness", "P4", 2.48, 0.50, 0.89, 0.22, "static", None),
            L("04.props.poet-jointed-hands__p11", "Articulated Left Hand on the Ground", "P3", 1.34, 0.24, 0.86, 0.22, "weave_hand_articulation", "Searching the Bare Ground"),
            L("04.props.heart__p01", "Reclaimed Beating Heart", "P3", 1.32, 0.52, 0.78, 0.22, "heart_beat", "The Awakened Chest"),
            L("04.props.poet-jointed-hands__p12", "Articulated Right Hand Reattached", "P3", 1.34, 0.78, 0.86, 0.22, "weave_hand_articulation", "Putting the Hands Back On"),
        ],
    },
    "04.6": {
        "backdrop": "world/f05c1fa5_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": None,
        "layers": [
            L("04.set.night_garden_field__p04", "Golden Flower Rows Across Field", "P4", 2.52, 0.50, 0.85, 0.14, "static", None),
            L("04.props.faith-blooms__p27", "Blooming Golden Sunflower West", "P3", 1.38, 0.22, 0.87, 0.28, "flower_bloom", "Western Bloom Row"),
            L("04.hero.viaduct__p04", "Distant Stone Viaduct Arch", "P4", 2.44, 0.52, 0.85, 0.42, "portal_aperture", "Standing Whole in the Field"),
            L("04.set.shore_night__p09", "Still Guardian Tree Under Stars", "P4", 2.40, 0.80, 0.86, 0.36, "static", "Still Tree Under Stars"),
        ],
    },

    # =======================================================================
    # POEM 05 · BLOODLINES
    # =======================================================================
    "05.0": {
        "backdrop": "world/c410eb27_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_grounded",
        "counterpart": {"key": "ancestor_robe/indigo_gold", "x": 940, "dir": -1, "cue": "idle"},
        "layers": [
            L("05.set.night_field_parade__p03", "Curved Celestial Horizon Meadow", "P4", 2.54, 0.50, 0.88, 0.18, "static", None),
            L("05.set.night_field_parade__p04", "Western Meadow Stone Marker", "P4", 2.42, 0.22, 0.86, 0.42, "curtain_sway_L", "The Field Goes Still"),
            L("05.props.star-names__p01", "Radiant Sun & Earth Medallion", "P3", 1.38, 0.52, 0.72, 0.24, "planet_orbit", "Inheriting the Earth"),
            L("05.set.night_field_parade__p06", "Ancestral Procession Archway", "P4", 2.44, 0.78, 0.86, 0.44, "portal_aperture", "Ancestral Perimeter"),
        ],
    },
    "05.1": {
        "backdrop": "world/434b7bdd_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "victory_cry",
        "counterpart": {"key": "ancestor_elder/white_silver", "x": 960, "dir": -1, "cue": "idle"},
        "layers": [
            L("05.props.star-names__p05", "Carved JUNE Star Nameplate", "P5", 3.50, 0.22, 0.34, 0.14, "sun_pulse", "Naming My Own Stars"),
            L("05.props.galaxy-universe__p01", "Swirling Spiral Galaxy Core", "P5", 3.55, 0.52, 0.36, 0.28, "planet_orbit", "Spiral Galaxies Overhead"),
            L("05.props.star-names__p06", "Radiant Star Crest Medallion", "P3", 1.40, 0.78, 0.76, 0.24, "sun_pulse", "The Waiting Past"),
        ],
    },
    "05.2": {
        "backdrop": "world/05a0677a_3/backdrop.webp",
        "floor": 616,
        "initial_cue": "kneel_hollow",
        "counterpart": None,
        "layers": [
            L("05.set.humid_basement__p05", "Riveted Iron Basement Grate Window", "P4", 2.44, 0.22, 0.68, 0.26, "portal_aperture", "Basement Window Well"),
            L("05.props.staff-mattress-emblem__p05", "Southern-Pine Quilted Basement Mattress", "P3", 1.42, 0.52, 0.88, 0.30, "lamp_base", "Southern-Pine Mattress"),
            L("05.props.staff-mattress-emblem__p02", "Brass Basement Lantern", "P3", 1.38, 0.76, 0.86, 0.32, "lamp_glow", "Basement Timber Stairs"),
            L("05.props.staff-mattress-emblem__p01", "Carved Wooden Ancestor Staff", "P3", 1.36, 0.84, 0.86, 0.46, "static", None),
        ],
    },
    "05.3": {
        "backdrop": "world/245fd8b5_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "kneel_universe",
        "counterpart": {"key": "ancestor_robe/indigo_gold", "x": 950, "dir": -1, "cue": "idle"},
        "layers": [
            L("05.props.galaxy-universe__p17", "Golden Pedestal Cupping a New Universe", "P3", 1.38, 0.24, 0.84, 0.28, "planet_orbit", "Inventing a New Universe"),
            L("05.props.staff-mattress-emblem__p07", "Radiant Ancestral Star Emblem", "P3", 1.36, 0.52, 0.74, 0.24, "sun_pulse", "Awarding a Blessing"),
            L("05.set.winged_marble_gate__p03", "Winged Marble Sanctuary Arch", "P4", 2.44, 0.78, 0.86, 0.48, "portal_aperture", "Sanctuary of the Elders"),
        ],
    },
    "05.4": {
        "backdrop": "world/36c9c157_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "ancestor_elder/white_silver", "x": 960, "dir": -1, "cue": "idle"},
        "layers": [
            L("05.props.fingerprint__p01", "Luminous Whorled Fingerprint Left", "P3", 1.38, 0.22, 0.82, 0.32, "heart_beat", "Blood Through the Hands"),
            L("05.props.fingerprint__p13", "Orchestrating Palm & Sun Whorl", "P3", 1.34, 0.52, 0.82, 0.34, "sun_pulse", "Fingerprints of Power"),
            L("05.set.winged_marble_gate__p01", "Winged Marble Watchtower Pillar", "P4", 2.46, 0.80, 0.86, 0.48, "portal_aperture", "Sun-Kissed Watchtower"),
        ],
    },
    "05.5": {
        "backdrop": "world/11929669_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "vow_hand_raised",
        "counterpart": {"key": "ancestor_robe/indigo_gold", "x": 960, "dir": -1, "cue": "idle"},
        "layers": [
            L("05.set.winged_marble_gate__p01", "West Winged Marble Gate Pillar", "P4", 2.42, 0.20, 0.86, 0.50, "portal_aperture", "West Winged Pillar"),
            L("05.set.winged_marble_gate__p03", "Central Winged Marble Gate Arch", "P4", 2.40, 0.52, 0.86, 0.52, "portal_aperture", "Baritone at the Gate"),
            L("05.set.winged_marble_gate__p05", "East Winged Marble Gate Pillar", "P4", 2.42, 0.82, 0.86, 0.50, "portal_aperture", "Threshold of Atlantis"),
        ],
    },

    # =======================================================================
    # POEM 06 · RESURRECTING ATLANTIS
    # =======================================================================
    "06.0": {
        "backdrop": "world/ba11d121_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "citizen_1/atlantis", "x": 950, "dir": -1, "cue": "idle"},
        "layers": [
            L("05.set.winged_marble_gate__p03", "Winged Marble Evolution Gate", "P4", 2.44, 0.22, 0.86, 0.50, "portal_aperture", "The Light Gates Open"),
            L("06.set.crystal_tree_hall__p08", "Illuminated Atlantis Crystal Arch", "P4", 2.40, 0.52, 0.86, 0.46, "portal_aperture", "Marble Stones & Hymns"),
            L("06.props.lantern-candle-guitar__p15", "NEXT GATES Sanctuary Signpost", "P3", 1.38, 0.80, 0.86, 0.30, "lamp_glow", "Next Gates Signpost"),
        ],
    },
    "06.1": {
        "backdrop": "world/c8158a76_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "traveler_1/atlantis", "x": 960, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.fx.comet__p01", "Swirling Golden Comet Sphere", "P5", 3.60, 0.22, 0.30, 0.22, "tambourine_arc", "Yellow-Brick Causeway"),
            L("06.fx.comet__p07", "Streaking Golden Comet Tail", "P5", 3.55, 0.50, 0.26, 0.14, "headlight_beam", "Following the Comets"),
            L("06.set.atlantis_waterfront.skyline__p12", "Rising Domed Cathedral of Atlantis", "P4", 2.46, 0.78, 0.86, 0.50, "portal_aperture", "Atlantis Horizon Ahead"),
        ],
    },
    "06.2": {
        "backdrop": "world/bb360097_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "arms_sky_high",
        "counterpart": {"key": "citizen_1/atlantis", "x": 940, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.set.atlantis_waterfront.skyline__p10", "Western Waterfront Arch & Greenery", "P4", 2.44, 0.20, 0.86, 0.44, "portal_aperture", "Waterfront Colonnade"),
            L("06.set.atlantis_waterfront.skyline__p13", "Twin-Towered Atlantis Citadel", "P4", 2.40, 0.52, 0.86, 0.52, "portal_aperture", "Resurrecting Atlantis"),
            L("06.set.atlantis_waterfront.skyline__p14", "Golden Waterfront Sanctuary Spires", "P4", 2.44, 0.82, 0.86, 0.48, "portal_aperture", "Here We Are All One"),
        ],
    },
    "06.3": {
        "backdrop": "world/646ab0f0_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "child_traveler/atlantis", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.set.crystal_tree_hall__p01", "Golden Jungle Interface Banyan Tree", "P4", 2.44, 0.20, 0.86, 0.46, "flower_bloom", "Jungle Interface Pact"),
            L("06.props.coin-booth__p01", "Arched Wooden Heart-Scan Booth", "P3", 1.42, 0.52, 0.87, 0.42, "lamp_glow", "Heart-Scan Admission Booth"),
            L("06.props.coin-booth__p04", "Luminous Cyan Heart-Scan Portal", "P3", 1.38, 0.78, 0.78, 0.26, "sun_pulse", "Relearned Currency"),
        ],
    },
    "06.4": {
        "backdrop": "world/06881630_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "elder_1/atlantis", "x": 940, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.set.atlantis_plaza__p09", "West Terracotta Plaza Arcade", "P4", 2.44, 0.20, 0.86, 0.44, "portal_aperture", "West Plaza Arcade"),
            L("06.set.crystal_tree_hall__p08", "Grand Crystal Tree Sanctuary Hall", "P4", 2.40, 0.52, 0.86, 0.48, "portal_inner_world", "City Center Sanctuary"),
            L("06.set.atlantis_plaza__p10", "East Terracotta Plaza Arcade", "P4", 2.44, 0.82, 0.86, 0.44, "portal_aperture", "East Plaza Colonnade"),
        ],
    },
    "06.5": {
        "backdrop": "world/cdca7326_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_L",
        "counterpart": {"key": "party_guest/guest", "x": 940, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.set.narrow_streets__p01", "Cobblestone Lantern Wall West", "P4", 2.44, 0.20, 0.86, 0.48, "portal_aperture", "Narrow Cobblestone Street"),
            L("06.props.lantern-candle-guitar__p11", "Flickering Brass Street Candle", "P3", 1.40, 0.48, 0.86, 0.24, "lamp_glow", "Flickering Candlelight"),
            L("06.props.lantern-candle-guitar__p14", "Warm Wooden Acoustic Guitar", "P3", 1.36, 0.62, 0.86, 0.22, "lamp_glow", None),
            L("06.set.narrow_streets__p03", "Arched Night Street Passage East", "P4", 2.44, 0.82, 0.86, 0.48, "portal_aperture", "Musician's Corner"),
        ],
    },
    "06.6": {
        "backdrop": "world/ee11f371_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_grounded",
        "counterpart": None,
        "layers": [
            L("06.hero.teahouse__p01", "Tiled Harbor Teahouse Pavilion", "P4", 2.44, 0.22, 0.85, 0.38, "lamp_glow", "Harbor Teahouse Veranda"),
            L("06.hero.house__p10", "Warm Overhead Festival String Lights", "P3", 1.48, 0.50, 0.34, 0.16, "lamp_glow", None),
            L("06.hero.house__p05", "Terracotta House Entry Door", "P4", 2.40, 0.52, 0.86, 0.44, "portal_aperture", "The House at Plaza Edge"),
            L("06.hero.house__p03", "Teal Shanty Facade & Window", "P4", 2.42, 0.80, 0.85, 0.34, "portal_aperture", "Sanctuary Window"),
        ],
    },

    # =======================================================================
    # POEM 07 · DJ TURN ME UP
    # =======================================================================
    "07.0": {
        "backdrop": "world/b631fc80_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "club_groove",
        "counterpart": {"key": "dj_cyber/cyber", "x": 640, "dir": -1, "cue": "idle"},
        "layers": [
            L("07.props.speakers-vu__p01", "Tall Dual-Driver Bass Speaker Left", "P3", 1.46, 0.20, 0.87, 0.42, "speaker_pulse", "Left Bass Speaker Stack"),
            L("07.props.dj-decks__p03", "Wooden DJ Booth Front Counter", "P3", 1.42, 0.50, 0.88, 0.24, "dj_console", "DJ Turn Me Up Booth"),
            L("07.props.dj-decks__p01", "Dual-Turntable DJ Mixer Console", "P3", 1.38, 0.50, 0.72, 0.22, "dj_console", None),
            L("07.props.speakers-vu__p02", "Tall Dual-Driver Bass Speaker Right", "P3", 1.46, 0.80, 0.87, 0.42, "speaker_pulse", "Right Bass Speaker Stack"),
        ],
    },
    "07.1": {
        "backdrop": "world/22ddf809_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "party_guest/guest", "x": 960, "dir": -1, "cue": "idle"},
        "layers": [
            L("07.hero.house.furniture__p03", "House Party Lounge Sofa", "P3", 1.45, 0.20, 0.87, 0.28, "lamp_base", "House Party Lounge"),
            L("07.props.mic-daisy-rings__p01", "Chrome Vocal Microphone on Stand", "P3", 1.34, 0.50, 0.87, 0.36, "speaker_pulse", "Eyes Wide Shut at the Mic"),
            L("07.props.dj-decks__p02", "Spinning Turntable Platter Deck", "P3", 1.40, 0.78, 0.86, 0.28, "dj_console", "Turntable Platter Deck"),
        ],
    },
    "07.2": {
        "backdrop": "world/a883ad75_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_question",
        "counterpart": {"key": "ex/ex_jacket", "x": 980, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("07.props.speakers-vu__p15", "Woven Speaker Mesh Grille Left", "P3", 1.44, 0.22, 0.86, 0.32, "speaker_pulse", "Ghosts in the Speaker Mesh"),
            L("07.props.projection__p10", "Projected Sun-Soaked Vineyard Rows", "P4", 2.46, 0.52, 0.78, 0.34, "portal_other_world", "Sun-Soaked Vineyard Projection"),
            L("07.props.speakers-vu__p16", "Woven Speaker Mesh Grille Right", "P3", 1.44, 0.80, 0.86, 0.32, "speaker_pulse", "Resonant Mesh Cabinet"),
        ],
    },
    "07.3": {
        "backdrop": "world/f59c59fe_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "arms_sky_high",
        "counterpart": {"key": "dj_cyber/cyber", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("07.props.speakers-vu__p12", "Glowing Analog VU Meter (-20..+3 dB)", "P3", 1.40, 0.22, 0.74, 0.16, "speaker_pulse", "VU Meter Into the Red"),
            L("07.props.dj-decks__p14", "Overdriven Twin-Platter DJ Deck", "P3", 1.38, 0.52, 0.86, 0.26, "dj_console", "A Thousand Light Years Deck"),
            L("07.props.speakers-vu__p17", "Framed Peak VU Meter Dial", "P3", 1.40, 0.80, 0.74, 0.18, "speaker_pulse", "Peak Decibel Dial"),
        ],
    },
    "07.4": {
        "backdrop": "world/51d1fea8_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_question",
        "counterpart": {"key": "ex/ex_jacket", "x": 980, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("07.props.projection__p11", "Diverging Golden Wedding Bands Frame", "P4", 2.44, 0.22, 0.78, 0.34, "sun_pulse", "Diverging Wedding Bands"),
            L("07.props.projection__p12", "Projected Shared Home Boxed in Field", "P4", 2.42, 0.52, 0.78, 0.34, "portal_tv_flicker", "The Boxed Home Projection"),
            L("07.hero.house__p03", "Shadowed House Interior Doorway", "P4", 2.40, 0.80, 0.86, 0.44, "portal_aperture", "Threshold of the Room"),
        ],
    },
    "07.5": {
        "backdrop": "world/79ea20ae_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "shrug_peace",
        "counterpart": None,
        "layers": [
            L("07.props.bar-handheld__p01", "Illuminated Club Bar Bottle Shelves", "P4", 2.44, 0.22, 0.78, 0.26, "lamp_glow", "Illuminated Club Bar"),
            L("07.props.mic-daisy-rings__p09", "Plucked Eleven-Year Daisy Stem", "P3", 1.34, 0.52, 0.86, 0.28, "flower_bloom", "Eleven Years in Daisy Petals"),
            L("07.hero.house__p09", "Wooden Exit Staircase", "P4", 2.40, 0.80, 0.86, 0.36, "fire_escape_landing", "Stairwell to the Street"),
        ],
    },
    "07.6": {
        "backdrop": "world/62b9740c_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "chin_high_stand",
        "counterpart": None,
        "layers": [
            L("07.props.projection__p13", "Three Diverging Roads Projection", "P4", 2.46, 0.22, 0.78, 0.34, "portal_other_world", "Three Roads in the Rain"),
            L("07.fx.party-haze__p01", "Drifting Streetlamp Fog Bank", "P1", 0.48, 0.52, 0.68, 0.18, "cloud_drift_L", "Frontal Fog & Dim Lights"),
            L("07.hero.house__p04", "Open Night Doorway to the Rain", "P4", 2.40, 0.80, 0.86, 0.42, "portal_aperture", "Walking Out Chin High"),
        ],
    },

    # =======================================================================
    # POEM 08 · NEWLY SINGLE
    # =======================================================================
    "08.0": {
        "backdrop": "world/959cd1f5_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "soul_rapture",
        "counterpart": {"key": "poet_soul/soul", "x": 620, "dir": 1, "cue": "kneel_2", "y_offset": -85},
        "layers": [
            L("08.hero.marquee__p16", "Glowing NEW SINGLE Club Marquee", "P4", 2.44, 0.24, 0.85, 0.42, "lamp_glow", "NEW SINGLE Club Marquee"),
            L("08.set.rooftop_club__p04", "Pulsing Rooftop Light Tower", "P4", 2.38, 0.52, 0.86, 0.42, "speaker_pulse", "Soul Leaves the Dancer"),
            L("08.fx.soul-weather__p01", "Ascending Luminous Soul Current", "P1", 0.46, 0.78, 0.58, 0.24, "sun_pulse", "Ascending Soul Vapor"),
        ],
    },
    "08.1": {
        "backdrop": "world/e3c427ae_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "club_groove",
        "counterpart": {"key": "club_dress/club", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("08.hero.marquee.interior__p01", "Neon NEW SINGLE Stage Arch", "P4", 2.44, 0.22, 0.84, 0.40, "portal_aperture", "Strangers Collide on Floor"),
            L("07.props.dj-decks__p01", "Late-Night Club DJ Console", "P3", 1.40, 0.52, 0.86, 0.24, "dj_console", "Last One to Leave"),
            L("08.hero.marquee.interior__p08", "Violet Club Colonnade Arch", "P4", 2.42, 0.80, 0.84, 0.40, "lamp_glow", "Midnight Dance Arches"),
        ],
    },
    "08.2": {
        "backdrop": "world/cbb5e9c5_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "poet_soul/soul", "x": 720, "dir": -1, "cue": "kneel_2", "y_offset": -80},
        "layers": [
            L("08.set.atlantis_aerial__p01", "Aerial Mandala of Atlantis Below", "P4", 2.50, 0.22, 0.74, 0.34, "portal_other_world", "Aerial Atlantis Below"),
            L("08.props.moons-laundry__p25", "Equator Clothesline & Blowing Laundry", "P3", 1.42, 0.54, 0.72, 0.22, "curtain_sway_L", "Open Field at the Equator"),
            L("08.props.moons-laundry__p01", "Closest Salted Moon Overhead", "P5", 3.55, 0.80, 0.28, 0.22, "planet_orbit", "Moons of the Equator"),
        ],
    },
    "08.3": {
        "backdrop": "world/f56df2d8_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "kneel_universe",
        "counterpart": {"key": "angel/robe", "x": 880, "dir": -1, "cue": "idle"},
        "layers": [
            L("08.props.basins__p01", "West Marble Ice-Water Basin", "P3", 1.42, 0.22, 0.87, 0.24, "wave_mid", "Salted Ice-Water Basin"),
            L("08.props.basins__p05", "Central Baptism Font of Ice Water", "P3", 1.38, 0.50, 0.88, 0.26, "wave_near", "Angels' Ice-Water Baptism"),
            L("08.cast.angel.wings__p03", "Feathered Angel Sanctuary Wings", "P3", 1.36, 0.78, 0.72, 0.28, "wing_flap_L", "Choir of Night Angels"),
        ],
    },
    "08.4": {
        "backdrop": "world/cf180ca2_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": None,
        "layers": [
            L("08.fx.soul-weather__p05", "Parting Smoke & Haze Cloud", "P1", 0.48, 0.22, 0.66, 0.22, "cloud_drift_L", "Breathing in the Smoke"),
            L("08.hero.marquee__p01", "Quiet Dawn Rooftop Colonnade", "P4", 2.42, 0.52, 0.85, 0.36, "portal_aperture", "Soul Returns to the Body"),
            L("08.props.basins__p06", "Still Terrace Basin at Dawn", "P3", 1.42, 0.80, 0.87, 0.22, "wave_mid", "Terrace Recovery Basin"),
        ],
    },
    "08.5": {
        "backdrop": "world/0240b488_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "back_horizon",
        "counterpart": None,
        "layers": [
            L("08.set.rooftop_club__p06", "Rooftop Skyline & Radio Towers", "P4", 2.54, 0.50, 0.86, 0.16, "static", None),
            L("08.set.rooftop_club__p04", "West Rooftop Beacon Tower", "P4", 2.40, 0.20, 0.86, 0.40, "portal_aperture", "Rooftop Parapet"),
            L("10.set.mountain_road__p04", "Unfamiliar Mountains in the Distance", "P4", 2.46, 0.52, 0.84, 0.18, "water_backing", "Mountains From the Rooftop"),
            L("09.props.moon-sun__p01", "Morning Sun Over the Peaks", "P5", 3.60, 0.80, 0.26, 0.20, "sun_pulse", "Wandering Eyes at Dawn"),
        ],
    },

    # =======================================================================
    # POEM 09 · YET, HEARD
    # =======================================================================
    "09.0": {
        "backdrop": "world/b05d5b9a_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "ex/ex_jacket", "x": 920, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("09.hero.canopy__p08", "Illuminated Neon Club Facade", "P4", 2.44, 0.22, 0.85, 0.44, "lamp_glow", "Outside the Club Canopy"),
            L("09.set.atlantis_club_sidewalk__p04", "Double-Globe Harbor Streetlamp", "P4", 2.40, 0.52, 0.86, 0.44, "lamp_glow", "The EX in the Crowd"),
            L("09.props.moon-sun__p01", "Shared Full Moon Overhead", "P5", 3.60, 0.80, 0.26, 0.20, "sun_pulse", "Under the Shared Moon"),
        ],
    },
    "09.1": {
        "backdrop": "world/abac8bce_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_L",
        "counterpart": {"key": "ex/ex_jacket", "x": 880, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.set.atlantis_club_sidewalk__p03", "Curved Iron Harbor Bridge Railing", "P4", 2.52, 0.50, 0.87, 0.20, "static", None),
            L("09.set.atlantis_club_sidewalk__p05", "Harbor Quay Streetlamp West", "P4", 2.42, 0.22, 0.86, 0.44, "lamp_glow", "Harbor Quay Promenade"),
            L("09.set.atlantis_harbor_street__p08", "Distant Harbor Crane Silhouette", "P4", 2.46, 0.54, 0.85, 0.42, "portal_aperture", "Walking Toward the Moon"),
            L("09.props.moon-sun__p01", "Moon Settling Over the Water", "P5", 3.58, 0.78, 0.26, 0.22, "sun_pulse", "Moonlight on the Harbor"),
        ],
    },
    "09.2": {
        "backdrop": "world/bf0a66ea_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "shrug_peace",
        "counterpart": {"key": "ex/ex_jacket", "x": 880, "dir": -1, "cue": "suitcase"},
        "layers": [
            L("09.props.suitcases-notice__p04", "Packed Brown Leather Suitcase", "P3", 1.42, 0.22, 0.88, 0.20, "drawer_slide", "Suitcases on the Curb"),
            L("09.props.phonebooth__p14", "3D Glass Harbor Phone Booth", "P3", 1.44, 0.52, 0.87, 0.42, "booth_frame", "The Harbor Phone Booth"),
            L("09.props.suitcases-notice__p19", "2nd Gate (01/12/14) Iron Signpost", "P3", 1.38, 0.80, 0.86, 0.36, "lamp_glow", "2nd Gate Notice Sign"),
        ],
    },
    "09.3": {
        "backdrop": "world/018da7e9_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "mother/poem09", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.phonebooth__p15", "Open Harbor Phone Booth & Handset", "P3", 1.44, 0.22, 0.87, 0.42, "booth_frame", "Calling From the Booth"),
            L("09.fx.call-abyss__p01", "Voice Waveform Across the Abyss", "P1", 0.48, 0.50, 0.56, 0.16, "phone_ring", "Speaking Across the Abyss"),
            L("09.set.mother_living_room__p07", "Mother's Framed Living Room Wall", "P4", 2.46, 0.78, 0.74, 0.34, "lamp_glow", "Mother's Living Room"),
            L("09.props.phones-chair__p07", "Mother's Floral Armchair", "P3", 1.40, 0.78, 0.88, 0.28, "lamp_base", None),
        ],
    },
    "09.4": {
        "backdrop": "world/b036e49b_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "father_elder/poem09", "x": 860, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.set.harbor_path_east__p02", "Warm Inner-Harbor Watchhouse Window", "P4", 2.44, 0.20, 0.84, 0.42, "portal_aperture", "Inner Harbor Watchhouse"),
            L("09.set.atlantis_club_sidewalk__p04", "East Quay Lantern Post", "P4", 2.40, 0.50, 0.86, 0.44, "lamp_glow", "Father & Son Harbor Walk"),
            L("13.props.planet-boats__p18", "Moored Wooden Harbor Sailboat", "P3", 1.42, 0.78, 0.86, 0.28, "boat_rock", "Inner Harbor Mooring"),
        ],
    },
    "09.5": {
        "backdrop": "world/18a6390f_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "shrug_peace",
        "counterpart": {"key": "ex/ex_jacket", "x": 960, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("09.set.atlantis_club_sidewalk__p05", "Misty Quay Streetlamp", "P4", 2.42, 0.22, 0.86, 0.44, "lamp_glow", "Misty Harbor Quay"),
            L("09.props.suitcases-notice__p05", "Single Suitcase Left on the Pier", "P3", 1.40, 0.50, 0.88, 0.20, "drawer_slide", "Yet Broken, Yet Heard"),
            L("09.fx.call-abyss__p19", "Parting Mist as the EX Dissolves", "P1", 0.46, 0.78, 0.68, 0.22, "cloud_drift_L", "The EX Turns to Haze"),
        ],
    },

    # =======================================================================
    # POEM 10 · MAGIC RIDE
    # =======================================================================
    "10.0": {
        "backdrop": "world/6edb9f7b_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_grounded",
        "counterpart": None,
        "layers": [
            L("10.set.atlantis_streets__p07", "Tall Wrought-Iron Streetlamp West", "P4", 2.44, 0.22, 0.86, 0.44, "lamp_glow", "Under the Streetlamp"),
            L("11.props.parked-motorcycle__p01", "Parked Cafe Racer Motorcycle", "P3", 1.38, 0.52, 0.87, 0.32, "bike_chassis", "The Parked Motorcycle"),
            L("10.set.atlantis_streets__p06", "Glowing Midnight Atlantis Skyline", "P4", 2.48, 0.80, 0.86, 0.28, "portal_aperture", "Midnight Curbside"),
        ],
    },
    "10.1": {
        "backdrop": "world/18cff588_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "magic_ride_bike",
        "counterpart": None,
        "layers": [
            L("10.set.atlantis_streets__p07", "Alleyway Streetlamp & Smokestack", "P4", 2.44, 0.20, 0.86, 0.44, "lamp_glow", "Steel Coverings & Ignition"),
            L("11.props.parked-motorcycle__p01", "Ignited Cafe Racer Motorcycle", "P3", 1.38, 0.50, 0.87, 0.34, "bike_chassis", "Mounting the Machine"),
            L("10.fx.ride-light__p22", "Ignited Golden Headlight Beam", "P1", 0.45, 0.78, 0.76, 0.14, "headlight_beam", "Headlight Cutting the Dark"),
        ],
    },
    "10.2": {
        "backdrop": "world/31ca5420_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "magic_ride_bike",
        "counterpart": None,
        "layers": [
            L("10.set.atlantis_streets__p07", "West Midnight Intersection Tower", "P4", 2.44, 0.20, 0.86, 0.44, "portal_aperture", "First Midnight Intersection"),
            L("10.props.bike-skeleton__p17", "Cruising Cafe Motorcycle in Stride", "P3", 1.38, 0.50, 0.87, 0.32, "bike_chassis", "Loneliness at Speed"),
            L("10.set.atlantis_streets__p08", "East Intersection Street Tower", "P4", 2.44, 0.80, 0.86, 0.42, "lamp_glow", "Wide-Eyed Intersection"),
        ],
    },
    "10.3": {
        "backdrop": "world/3a0da51b_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "magic_ride_bike",
        "counterpart": None,
        "layers": [
            L("10.hero.shadowpool__p02", "Amber Avenue Light Pool", "P4", 2.46, 0.22, 0.87, 0.40, "lamp_glow", "Avenue Light Pool"),
            L("11.props.parked-motorcycle__p01", "Cafe Racer Leaning Through the Avenue", "P3", 1.38, 0.52, 0.87, 0.34, "bike_chassis", "Swagger Down the Avenue"),
            L("10.fx.ride-light__p23", "Streaming Sodium Tail-Light Streak", "P1", 0.46, 0.80, 0.68, 0.14, "headlight_beam", "Noise Blocking the Noise"),
        ],
    },
    "10.4": {
        "backdrop": "world/3c0e1673_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "point_horizon",
        "counterpart": None,
        "layers": [
            L("05.set.winged_marble_gate__p01", "Outer Boundary Pillar of Atlantis", "P4", 2.46, 0.20, 0.86, 0.48, "portal_aperture", "Leaving Atlantis Behind"),
            L("10.props.bike-skeleton__p17", "Highway Motorcycle Heading Out", "P3", 1.38, 0.50, 0.87, 0.32, "bike_chassis", "Out of Atlantis"),
            L("09.props.moon-sun__p01", "Settling Horizon Moon & Dawn Glow", "P5", 3.60, 0.78, 0.28, 0.22, "sun_pulse", "Where the Moon Settles"),
        ],
    },
    "10.5": {
        "backdrop": "world/ea91d4c4_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "welcome_new_day",
        "counterpart": None,
        "layers": [
            L("10.set.mountain_road__p03", "Winding Mountain Highway Switchback", "P4", 2.44, 0.22, 0.86, 0.34, "fire_escape_landing", "Mountain Road Switchback"),
            L("10.props.tree-dawn-sign__p02", "88 NEW DAWN km Roadside Signpost", "P3", 1.40, 0.50, 0.86, 0.30, "lamp_glow", "88 NEW DAWN km Sign"),
            L("10.props.tree-dawn-sign__p01", "Solitary Crest Tree at First Light", "P4", 2.38, 0.78, 0.86, 0.48, "flower_bloom", "First Light on the Ridge"),
        ],
    },

    # =======================================================================
    # POEM 11 · NEW DAY (Note exact scene keys: 11.0, 11.3, 11.1, 11.2, 11.4, 11.5!)
    # =======================================================================
    "11.0": {
        "backdrop": "world/d3d25411_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_grounded",
        "counterpart": None,
        "layers": [
            L("11.props.parked-motorcycle__p01", "Parked Motorcycle on Chilly Shore", "P3", 1.40, 0.22, 0.87, 0.30, "bike_chassis", "Parked Bike by the Sea"),
            L("11.props.ruin__p02", "Weathered Shore Ruin Archway", "P4", 2.42, 0.52, 0.86, 0.40, "portal_aperture", "Arrival on the Chilly Shore"),
            L("11.hero.clocktower__p01", "Distant Shore Sanctuary Bell Tower", "P4", 2.46, 0.80, 0.86, 0.52, "portal_aperture", "Misty Shore Bell Tower"),
        ],
    },
    "11.3": {
        "backdrop": "world/6b70f5b3_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": None,
        "layers": [
            L("11.props.temple.states__p06", "Completed White Marble Temple Nave", "P4", 2.44, 0.22, 0.86, 0.46, "portal_aperture", "New White Temple Nave"),
            L("11.props.inlays-lantern__p15", "Hanging Brass Sanctuary Lantern", "P3", 1.38, 0.52, 0.58, 0.32, "lamp_glow", "Choir Chords in the Nave"),
            L("11.hero.clocktower__p01", "White Sanctuary Clocktower", "P4", 2.46, 0.80, 0.86, 0.54, "portal_aperture", "Sanctuary Clocktower"),
        ],
    },
    "11.1": {
        "backdrop": "world/08fe12af_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_question",
        "counterpart": None,
        "layers": [
            L("11.props.ruin__p03", "Sunlit Ruined Stone Arch", "P4", 2.44, 0.22, 0.86, 0.38, "portal_aperture", "Remnants in the Sunlight"),
            L("11.props.temple.states__p01", "White Marble Plinth & First Courses", "P4", 2.38, 0.52, 0.86, 0.40, "drawer_slide", "First Courses of Stone"),
            L("11.fx.light__p01", "Morning Sun Breaking Above the Sea", "P5", 3.60, 0.78, 0.26, 0.22, "sun_pulse", "Morning Sunlight"),
        ],
    },
    "11.2": {
        "backdrop": "world/58cbb4ca_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "arms_sky_high",
        "counterpart": None,
        "layers": [
            L("11.props.temple.states__p03", "White Marble Stepped Plinth", "P4", 2.44, 0.20, 0.86, 0.18, "portal_aperture", "Rising Fluted Columns"),
            L("11.props.temple.states__p01", "Rising Fluted Marble Columns", "P4", 2.40, 0.50, 0.86, 0.38, "portal_aperture", "The Temple Builds Itself"),
            L("11.props.temple.states__p04", "Crowned White Temple & Pediment", "P4", 2.38, 0.80, 0.86, 0.46, "sun_pulse", "Crowning the White Roof"),
        ],
    },
    "11.4": {
        "backdrop": "world/fc83bfee_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": None,
        "layers": [
            L("02.set.bedroom_night__p03", "Sanctuary Standing Mirror Glass", "P4", 2.44, 0.22, 0.85, 0.44, "portal_other_world", None),
            L("02.set.bedroom_night__p02", "Tall Standing Sanctuary Mirror", "P4", 2.42, 0.22, 0.86, 0.46, "portal_aperture", "The Lonely Mirror"),
            L("11.props.journal__p11", "Open Two-Page Leather Journal", "P3", 1.38, 0.52, 0.84, 0.24, "lamp_glow", "Open Journal of Clarity"),
            L("11.set.mirror_hall__p14", "Reflecting Pool Marble Column", "P4", 2.40, 0.80, 0.86, 0.38, "wave_far", "Infinity Pool Colonnade"),
        ],
    },
    "11.5": {
        "backdrop": "world/5bd8dc26_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "welcome_new_day",
        "counterpart": None,
        "layers": [
            L("11.set.temple_infinity_pool__p05", "Reflecting White Colonnade Across Sea", "P4", 2.52, 0.50, 0.85, 0.14, "static", None),
            L("11.hero.pools__p04", "Calm Reflecting Pool Steps", "P4", 2.40, 0.22, 0.87, 0.34, "wave_mid", "Reflecting Pool Steps"),
            L("11.props.temple.whole__p20", "Gleaming White Temple by the Sea", "P4", 2.42, 0.52, 0.86, 0.46, "portal_aperture", "Walking on Calm Water"),
            L("09.props.moon-sun__p01", "Golden Dawn Sun at the Zenith", "P5", 3.55, 0.78, 0.28, 0.22, "sun_pulse", "Welcoming the New Day"),
        ],
    },

    # =======================================================================
    # POEM 12 · REUNION
    # =======================================================================
    "12.0": {
        "backdrop": "world/58cbb4ca_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "brother_1/poem12", "x": 880, "dir": -1, "cue": "idle"},
        "layers": [
            L("12.props.niche-porch__p01", "Arched White Temple Sanctuary Porch", "P4", 2.44, 0.22, 0.86, 0.46, "portal_aperture", "Temple Porch Entrance"),
            L("12.props.niche-porch__p15", "Hanging Brass Sanctuary Dome Lamp", "P3", 1.44, 0.52, 0.46, 0.24, "lamp_glow", "Welcome Home in the Hall"),
            L("12.set.temple_hall__p04", "Fluted White Temple Hall Column", "P4", 2.42, 0.80, 0.86, 0.42, "portal_aperture", "Hall of Reunion"),
        ],
    },
    "12.1": {
        "backdrop": "world/08fe12af_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "friend_1/poem12", "x": 880, "dir": -1, "cue": "idle"},
        "layers": [
            L("12.set.temple_hall__p04", "West Echoing Marble Column", "P4", 2.44, 0.22, 0.86, 0.42, "portal_aperture", "Echoing Hall Columns"),
            L("04.props.heart__p01", "Overheard Beating Heart in Chorus", "P3", 1.34, 0.52, 0.76, 0.22, "heart_beat", "Overheard Hearts"),
            L("12.set.temple_backroom__p06", "Carved Wooden Gathering Chair", "P3", 1.42, 0.78, 0.87, 0.30, "lamp_base", "Gathering Circle"),
        ],
    },
    "12.2": {
        "backdrop": "world/f05c1fa5_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "still_sentinel",
        "counterpart": None,
        "layers": [
            L("12.set.temple_backroom__p01", "Stone Afterlife Chamber Doorway", "P4", 2.44, 0.22, 0.86, 0.42, "portal_aperture", "Afterlife Chamber Door"),
            L("12.set.temple_backroom__p02", "Quiet Stone Staircase in Shadow", "P4", 2.40, 0.52, 0.86, 0.40, "portal_inner_world", "Empty Rooms of Afterlife"),
            L("12.props.niche-porch__p01", "Arched Stone Sanctuary Niche", "P4", 2.42, 0.80, 0.86, 0.44, "lamp_glow", "Silent Wall Niche"),
        ],
    },
    "12.3": {
        "backdrop": "world/3603f621_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "vow_hand_raised",
        "counterpart": {"key": "brother_1/poem12", "x": 900, "dir": -1, "cue": "idle"},
        "layers": [
            L("12.props.hand-hourglass__p05", "Glass Hourglass of Burning Sand", "P3", 1.38, 0.22, 0.84, 0.30, "hourglass_sand", "Glasses of Burning Sand"),
            L("12.props.last-hourglass__p23", "Burning Wooden Hourglass Frame", "P3", 1.36, 0.50, 0.86, 0.34, "hourglass_sand", "The Burning Hourglasses"),
            L("12.props.snapshot__p01", "Framed Archival Group Photograph", "P3", 1.40, 0.78, 0.82, 0.34, "portal_tv_flicker", "The Archival Group Photo"),
        ],
    },
    "12.4": {
        "backdrop": "world/22fcebea_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "elders/memory", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("12.set.temple_grove__p08", "Ancient Sanctuary Grove Tree West", "P4", 2.44, 0.22, 0.78, 0.34, "flower_bloom", "Western Forest Edge"),
            L("12.set.temple_grove__p05", "Tall Living Grove Pine Trunk", "P4", 2.40, 0.52, 0.86, 0.44, "curtain_sway_L", "Every Living Tree"),
            L("12.set.temple_grove__p06", "Sanctuary Grove Canopy East", "P4", 2.42, 0.80, 0.78, 0.34, "curtain_sway_R", "Shared Years in the Wind"),
        ],
    },
    "12.5": {
        "backdrop": "world/ef9f6c7e_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "brother_1/poem12", "x": 820, "dir": -1, "cue": "idle"},
        "layers": [
            L("12.set.temple_shore_terrace__p10", "Billowing Shore Terrace Canopy West", "P4", 2.42, 0.22, 0.84, 0.42, "curtain_sway_L", "Shore Terrace Canopy"),
            L("12.props.snapshot__p02", "Brotherhood Arm-in-Arm Portrait", "P3", 1.38, 0.52, 0.82, 0.36, "heart_beat", "The Brotherhood Chain"),
            L("12.set.temple_shore_terrace__p11", "Billowing Shore Terrace Canopy East", "P4", 2.42, 0.80, 0.84, 0.42, "curtain_sway_R", "Overheard Hearts Terrace"),
        ],
    },
    "12.6": {
        "backdrop": "world/bdc7d6ec_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "lunge_catch",
        "counterpart": {"key": "friend_1/poem12", "x": 900, "dir": -1, "cue": "idle"},
        "layers": [
            L("12.set.temple_grove__p08", "Meadow Sanctuary Tree West", "P4", 2.46, 0.22, 0.80, 0.32, "flower_bloom", "Football in the Meadow"),
            L("12.props.reunion__p01", "Spiraling Leather Football", "P3", 1.32, 0.50, 0.62, 0.16, "tambourine_arc", "Spiraling Pass at Dusk"),
            L("12.props.niche-porch__p01", "Illuminated Temple Home Porch", "P4", 2.40, 0.80, 0.86, 0.46, "portal_aperture", "Recollections Bring Us Home"),
        ],
    },

    # =======================================================================
    # POEM 13 · HOW TO WIN MY HEART (Note exact scene keys: 13.1, 13.0, 13.2..13.6!)
    # =======================================================================
    "13.1": {
        "backdrop": "world/932cb5b5_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "corner_cafe_cup",
        "counterpart": {"key": "woman/poem13", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("13.props.rail-tide-awning__p08", "Blue-and-White Striped Cafe Awning", "P4", 2.46, 0.24, 0.44, 0.20, "curtain_sway_L", "Harbor Cafe Awning"),
            L("13.props.cafe__p13", "Corner Marble Bistro Table & Chairs", "P3", 1.40, 0.48, 0.88, 0.26, "coffee_steam", "The Corner Cafe Table"),
            L("13.props.cafe__p07", "Steaming Porcelain Espresso Cup", "P3", 1.34, 0.46, 0.69, 0.09, "coffee_steam", None),
            L("13.hero.cafe__p01", "Teal Harbor Cafe Storefront Windows", "P4", 2.44, 0.78, 0.86, 0.42, "portal_aperture", "Harbor of the Heavens Cafe"),
        ],
    },
    "13.0": {
        "backdrop": "world/06881630_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "woman/poem13", "x": 940, "dir": -1, "cue": "idle"},
        "layers": [
            L("11.props.temple.whole__p20", "White Temple on the Point", "P4", 2.46, 0.20, 0.86, 0.44, "portal_aperture", "Leaving the White Temple"),
            L("13.hero.atrium__p01", "Arched Harbor Promenade Colonnade", "P4", 2.40, 0.52, 0.86, 0.36, "fire_escape_landing", "Walk Around the Harbor"),
            L("13.props.planet-boats__p18", "Wooden Sailboat on the Harbor Tide", "P3", 1.42, 0.80, 0.86, 0.26, "boat_rock", "Harbor Sailboat Mooring"),
        ],
    },
    "13.2": {
        "backdrop": "world/7df17df5_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "elder_woman/poem13", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("13.props.planet-boats__p01", "Banded Planet Jupiter & Orbits", "P5", 3.60, 0.22, 0.28, 0.22, "planet_orbit", "Counted Planetary Orbits"),
            L("13.set.church_pews__p02", "Gothic Stained-Glass Sanctuary Window", "P4", 2.46, 0.52, 0.76, 0.38, "portal_aperture", None),
            L("13.set.church_pews__p03", "Carved Wooden Pews of Praying Elders", "P3", 1.44, 0.52, 0.88, 0.20, "lamp_glow", "Praying Elders in the Pews"),
            L("13.props.planet-boats__p19", "Tall-Masted Dreaming Sailboat", "P3", 1.40, 0.82, 0.86, 0.28, "boat_rock", "Younger Selves Dreaming"),
        ],
    },
    "13.3": {
        "backdrop": "world/590a0c02_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_question",
        "counterpart": None,
        "layers": [
            L("13.hero.atrium__p01", "Half-Submerged Stone Atrium Arches", "P4", 2.44, 0.24, 0.86, 0.38, "wave_far", "Drowned Atrium of Seasons"),
            L("13.props.five-letters__p02", "Scorched Unsent Love Letter", "P3", 1.36, 0.54, 0.76, 0.18, "tambourine_arc", "Five Burned Love Letters"),
            L("13.props.harvest__p10", "Wildflower Bouquet of Old Stories", "P3", 1.38, 0.78, 0.87, 0.26, "flower_bloom", "Fire of Burned Stories"),
        ],
    },
    "13.4": {
        "backdrop": "world/2ce9173b_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "kneel_universe",
        "counterpart": {"key": "woman/poem13", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("13.props.harvest__p01", "Scarlet Poppies & White Blossoms West", "P3", 1.40, 0.22, 0.87, 0.28, "flower_bloom", "Scarlet Poppy Meadow"),
            L("13.props.harvest__p04", "Harvested Bouquet of Scarlet Poppies", "P3", 1.36, 0.52, 0.86, 0.28, "flower_bloom", "Harvesting the Poppies"),
            L("13.props.harvest__p05", "Blossoming Hilltop Poppies East", "P3", 1.40, 0.80, 0.87, 0.28, "flower_bloom", "Purple Blossoms Ridge"),
        ],
    },
    "13.5": {
        "backdrop": "world/7fae27c3_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "arms_sky_high",
        "counterpart": {"key": "woman/poem13", "x": 900, "dir": -1, "cue": "idle"},
        "layers": [
            L("13.props.cafe__p03", "Empty Bentwood Bistro Chair", "P3", 1.42, 0.22, 0.88, 0.34, "cafe_chair", "Waiting by the Cafe Chair"),
            L("13.props.distant-window__p13", "Arched Brick Distant Window & Silhouette", "P4", 2.42, 0.52, 0.74, 0.32, "portal_aperture", "From a Distant Window"),
            L("13.hero.cafe__p04", "Harbor Cafe Window & Greenery", "P4", 2.40, 0.80, 0.85, 0.38, "lamp_glow", "Hope Tells Me You'll See Me"),
        ],
    },
    "13.6": {
        "backdrop": "world/18a6390f_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "woman/poem13", "x": 860, "dir": -1, "cue": "idle"},
        "layers": [
            L("13.props.cafe__p14", "Bistro Table & Espresso Cup Left Behind", "P3", 1.42, 0.22, 0.88, 0.24, "coffee_steam", "Rising From the Cafe Table"),
            L("13.hero.atrium__p03", "Sunlit Harbor Atrium Tree", "P4", 2.40, 0.52, 0.86, 0.38, "portal_aperture", "Walks the Harbor Promenade"),
            L("13.props.planet-boats__p18", "Wooden Harbor Sailboat at Dusk", "P3", 1.42, 0.80, 0.86, 0.26, "boat_rock", "Harbor Horizon at Dusk"),
        ],
    },

    # =======================================================================
    # POEM 14 · HOT MINUTE
    # =======================================================================
    "14.0": {
        "backdrop": "world/ba11d121_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": None,
        "layers": [
            L("14.set.harbor_atlantis_wide__p09", "Panoramic Harbor Bridge & City Lights", "P4", 2.54, 0.50, 0.86, 0.16, "static", None),
            L("14.set.harbor_atlantis_wide__p06", "Harbor Trawler Boat on the Bay", "P3", 1.44, 0.22, 0.86, 0.26, "boat_rock", "Everything I Built"),
            L("09.props.moon-sun__p01", "Luminous Horizon Moon Over Atlantis", "P5", 3.55, 0.52, 0.26, 0.20, "sun_pulse", "Taken by the Haze"),
            L("14.set.harbor_atlantis_wide__p04", "Crystal Island of Atlantis", "P4", 2.44, 0.78, 0.85, 0.34, "portal_aperture", "Light-Filled Constellations"),
        ],
    },
    "14.1": {
        "backdrop": "world/3da7e92e_3/backdrop.webp",
        "floor": 616,
        "initial_cue": "soul_rapture",
        "counterpart": None,
        "layers": [
            L("14.props.reel__p06", "Candle Flame Memory Shard in Void", "P3", 1.40, 0.22, 0.72, 0.24, "lamp_glow", "Floating in the Black"),
            L("14.props.reel__p05", "Starburst Key of Answers", "P3", 1.36, 0.52, 0.64, 0.24, "sun_pulse", "Sharpened Key of Answers"),
            L("14.props.door__p02", "Closed Freestanding Vintage Door", "P4", 2.44, 0.80, 0.86, 0.48, "portal_aperture", "Distant Door in the Void"),
        ],
    },
    "14.2": {
        "backdrop": "world/c1eadbdf_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "family/street_clothes", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("14.props.reel__p02", "Memory Frame · Spiral Galaxy", "P3", 1.40, 0.22, 0.76, 0.26, "planet_orbit", "Highs of Life Memory"),
            L("14.props.reel__p07", "Memory Frame · Temple Under Stars", "P3", 1.38, 0.52, 0.76, 0.26, "portal_tv_flicker", "Cross-Cut of Life"),
            L("14.props.reel__p03", "Memory Frame · Scarlet Poppy", "P3", 1.40, 0.80, 0.76, 0.26, "flower_bloom", "Love & Loss Endured"),
        ],
    },
    "14.3": {
        "backdrop": "world/8519865f_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "chin_high_stand",
        "counterpart": None,
        "layers": [
            L("14.fx.filmframe__p01", "Perforated 35mm Graytone Film Frame", "P4", 2.44, 0.22, 0.78, 0.36, "portal_tv_flicker", "Graytone Film Aperture"),
            L("14.props.reel__p01", "Memory Frame · Golden Poppy Field", "P3", 1.38, 0.52, 0.78, 0.26, "portal_tv_flicker", "Battle Scars & Wisdom"),
            L("14.props.reel__p04", "Memory Frame · Open Journal Pages", "P3", 1.40, 0.80, 0.78, 0.26, "lamp_glow", "Unspooling the Reel"),
        ],
    },
    "14.4": {
        "backdrop": "world/5bd8dc26_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": None,
        "layers": [
            L("14.props.door__p11", "Freestanding Vintage Door Ajar", "P4", 2.42, 0.22, 0.86, 0.44, "portal_aperture", "The Vintage Door Appears"),
            L("14.props.door__p12", "Vintage Door Cracking Open With Light", "P4", 2.40, 0.52, 0.86, 0.46, "portal_aperture", "Light Beyond the Door"),
            L("14.props.door__p13", "Vintage Door Wide Open to Ballroom", "P4", 2.38, 0.80, 0.86, 0.46, "portal_other_world", "Stepping Through the Threshold"),
        ],
    },
    "14.5": {
        "backdrop": "world/cb6cbbfc_1/backdrop.webp",
        "floor": 612,
        "initial_cue": "waltz",
        "counterpart": {"key": "vintage_woman/gown", "x": 760, "dir": -1, "cue": "waltz"},
        "layers": [
            L("14.set.vintage_party__p01", "1940s Wood-Panelled Ballroom Wall", "P4", 2.56, 0.50, 0.86, 0.34, "static", None),
            L("14.props.party__p19", "Warm Ballroom Festoon String Lights", "P3", 1.48, 0.24, 0.34, 0.22, "lamp_glow", "Under the Ballroom Lights"),
            L("14.set.vintage_party__p03", "1940s Grand Ballroom Archway", "P4", 2.42, 0.52, 0.86, 0.50, "portal_other_world", "The Dance at the Vintage Party"),
            L("14.props.party__p20", "Brass Horn Table Gramophone", "P3", 1.40, 0.80, 0.87, 0.28, "turntable_spin", "Gramophone Waltz"),
        ],
    },
    "14.6": {
        "backdrop": "world/9572112a_1/backdrop.webp",
        "floor": 612,
        "initial_cue": "idle_grounded",
        "counterpart": {"key": "vintage_man/suit", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("14.props.party__p01", "Draped Ballroom Champagne Table", "P3", 1.44, 0.22, 0.88, 0.30, "lamp_glow", "Into the Ballroom Crowd"),
            L("14.props.door__p02", "Closing Panelled Vintage Door", "P4", 2.40, 0.52, 0.86, 0.50, "portal_aperture", "The Vintage Door Closes"),
            L("01.props.window__p01", "Quiet Bedroom Sash Window at Dawn", "P4", 2.44, 0.80, 0.85, 0.48, "portal_aperture", "Genesis · Back to Poem 01"),
        ],
    },
}


def compute_opaque_ratio(img_path: pathlib.Path) -> Tuple[float, float]:
    if not img_path.exists():
        return (1.0, 1.0)
    try:
        im = Image.open(img_path).convert("RGBA")
        w, h = im.size
        ar = w / float(max(1, h))
        hist = im.split()[3].histogram()
        op = sum(hist[200:]) / float(max(1, w * h))
        return (ar, op)
    except Exception:
        return (1.0, 1.0)


def render_clean_scene_plate(
    out_webp: pathlib.Path,
    backdrop_path: pathlib.Path,
    floor_y: int,
    layers: List[Dict[str, Any]],
    district_glow: List[Any],
    return_pil: bool = False,
) -> Optional[Image.Image]:
    """
    Renders a clean, high-legibility 1280x720 WebP scene plate using the exact
    same layer geometry as `drawMultiplaneLayer` in `shots/play/levels.html`.
    """
    W, H = 1280, 720
    if backdrop_path.exists():
        bg = Image.open(backdrop_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    else:
        bg = Image.new("RGBA", (W, H), (14, 18, 26, 255))

    bg_rgb = ImageEnhance.Contrast(bg.convert("RGB")).enhance(1.06)
    canvas = bg_rgb.convert("RGBA")

    fy = max(480, min(660, int(floor_y)))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    r_g, g_g, b_g = 216, 171, 79
    if district_glow:
        first_c = district_glow[0]
        if isinstance(first_c, str) and first_c.startswith("#") and len(first_c) >= 7:
            r_g = int(first_c[1:3], 16)
            g_g = int(first_c[3:5], 16)
            b_g = int(first_c[5:7], 16)
        elif len(district_glow) >= 3 and all(isinstance(x, (int, float)) for x in district_glow[:3]):
            r_g, g_g, b_g = int(district_glow[0]), int(district_glow[1]), int(district_glow[2])

    for y in range(fy - 18, H):
        if y < fy:
            t = (y - (fy - 18)) / 18.0
            alpha = int(38 * (t ** 2))
            odraw.line([(0, y), (W, y)], fill=(r_g, g_g, b_g, alpha))
        else:
            t = (y - fy) / max(1.0, float(H - fy))
            dark_a = int(115 + 95 * math.sqrt(t))
            odraw.line([(0, y), (W, y)], fill=(10, 13, 18, dark_a))

    odraw.line([(0, fy), (W, fy)], fill=(r_g, g_g, b_g, 110), width=2)
    for px_frac in (0.15, 0.32, 0.50, 0.68, 0.85):
        top_x = int(W * px_frac)
        bot_x = int(W * 0.5 + (top_x - W * 0.5) * 1.35)
        odraw.line([(top_x, fy), (bot_x, H)], fill=(255, 255, 255, 18), width=1)

    canvas = Image.alpha_composite(canvas, overlay)

    draw_layers = sorted(layers, key=lambda item: float(item.get("z", 1.4)), reverse=True)
    for lyr in draw_layers:
        part_rel = lyr.get("shots_file", "")
        p_path = SHOTS_DIR / part_rel
        if not p_path.exists():
            continue
        try:
            p_img = Image.open(p_path).convert("RGBA")
        except Exception:
            continue
        pw, ph = p_img.size
        if pw <= 1 or ph <= 1:
            continue
        sc = float(lyr.get("scale", 0.35))
        target_h = max(24, min(int(H * 0.78), int(round(H * sc))))
        target_w = max(24, int(round(target_h * (pw / float(ph)))))

        p_resized = p_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        if lyr.get("flip"):
            p_resized = p_resized.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        cx = int(round(float(lyr.get("x", 0.5)) * W))
        by = int(round(float(lyr.get("y", 0.85)) * H))
        dx = cx - target_w // 2
        dy = by - target_h

        shadow = p_resized.split()[3].point(lambda a: int(a * 0.45))
        shadow_rgba = Image.merge("RGBA", (
            Image.new("L", (target_w, target_h), 6),
            Image.new("L", (target_w, target_h), 8),
            Image.new("L", (target_w, target_h), 12),
            shadow,
        )).filter(ImageFilter.GaussianBlur(radius=4))
        canvas.alpha_composite(shadow_rgba, dest=(dx + 4, dy + 6))
        canvas.alpha_composite(p_resized, dest=(dx, dy))

    out_webp.parent.mkdir(parents=True, exist_ok=True)
    rgb = canvas.convert("RGB")
    rgb.save(out_webp, "WEBP", quality=88, method=4)
    if return_pil:
        return rgb
    return None


def main() -> None:
    print("[1/4] Loading wygwyl_atlas_manifest.json and verifying all 90 custom scenes...")
    manifest = json.loads(MANIFEST_PATH.read_text())
    parts_by_id: Dict[str, Dict[str, Any]] = {}
    sheet_by_part: Dict[str, Dict[str, Any]] = {}
    for asset in manifest["assets"]:
        for pt in asset.get("parts", []):
            parts_by_id[pt["id"]] = pt
            sheet_by_part[pt["id"]] = asset

    # Verify every part_id and backdrop in CUSTOM_SCENES before writing a single file
    missing_parts = []
    missing_bgs = []
    for skey, spec in CUSTOM_SCENES.items():
        bg_p = SHOTS_DIR / spec["backdrop"]
        if not bg_p.exists():
            missing_bgs.append((skey, spec["backdrop"]))
        for lyr in spec["layers"]:
            pid = lyr["part_id"]
            if pid not in parts_by_id:
                missing_parts.append((skey, pid))
    if missing_parts or missing_bgs:
        raise RuntimeError(f"Missing parts: {missing_parts}, Missing bgs: {missing_bgs}")
    print(f"  Verified {len(CUSTOM_SCENES)} custom scenes: 0 missing parts, 0 missing backdrops!")

    # Also fix poet/black_tshirt in shots/play/data.json so draws[9] (Reading the Manuscript)
    # has has_scene_prop=True and default idle is prop-free upright stance!
    data_path = PLAY_DIR / "data.json"
    play_data = json.loads(data_path.read_text())
    for ch in play_data.get("characters", []):
        if ch.get("key") == "poet/black_tshirt":
            for dr in ch.get("draws", []):
                if dr.get("sem_id") == "reading_pages":
                    dr["has_scene_prop"] = True
                elif dr.get("sem_id") == "walk_stride_L":
                    dr["sem_label"] = "Ready Stance / Stride Left"
    data_path.write_text(json.dumps(play_data, separators=(",", ":")))

    audit_batches: Dict[str, List[Image.Image]] = {
        "audit_scenes_01_04.png": [],
        "audit_scenes_05_08.png": [],
        "audit_scenes_09_11.png": [],
        "audit_scenes_12_14.png": [],
    }

    total_scenes = 0
    total_layers = 0

    print("[2/4] Updating all 14 poem level.json files and rendering 90 scene plates...")
    for poem_num in range(1, 15):
        num_str = f"{poem_num:02d}"
        lv_path = LEVELS_DIR / num_str / "level.json"
        lv = json.loads(lv_path.read_text())
        fw, fh = int(lv["frame"][0]), int(lv["frame"][1])

        for sc_idx, sc in enumerate(lv["scenes"]):
            skey = sc["key"]
            spec = CUSTOM_SCENES.get(skey)
            if not spec:
                raise RuntimeError(f"Missing custom scene spec for {skey}!")

            backdrop_shots_rel = spec["backdrop"]
            backdrop_play_rel = f"../{backdrop_shots_rel}"

            combined_layers: List[Dict[str, Any]] = []
            stations: List[Dict[str, Any]] = []

            for e_idx, lspec in enumerate(spec["layers"]):
                pid = lspec["part_id"]
                pt = parts_by_id[pid]
                shots_file = pt["file"]
                play_file = f"../{shots_file}"
                st_title = lspec.get("station_title")
                station_id = f"st_{skey.replace('.', '_')}_{e_idx}" if st_title else ""

                lyr_obj = {
                    "id": f"lyr_{skey.replace('.', '_')}_{e_idx}_{pid.split('__')[-1]}",
                    "part_id": pid,
                    "sheet_id": sheet_by_part[pid]["id"],
                    "label": lspec["label"],
                    "station_id": station_id,
                    "station_title": st_title or lspec["label"],
                    "plane": lspec["plane"],
                    "z": round(float(lspec["z"]), 2),
                    "x": round(float(lspec["x"]), 4),
                    "y": round(float(lspec["y"]), 4),
                    "scale": round(float(lspec["scale"]), 4),
                    "width": int(pt.get("width", 240)),
                    "height": int(pt.get("height", 240)),
                    "role": "station_arch" if lspec["plane"] == "P4" else ("station_horizon" if lspec["plane"] == "P5" else "station_prop"),
                    "anim_role": lspec.get("anim_role", "static"),
                    "flip": bool(lspec.get("flip", False)),
                    "alpha": round(float(lspec.get("alpha", 0.98)), 3),
                    "file": play_file,
                    "shots_file": shots_file,
                }
                combined_layers.append(lyr_obj)

                if st_title:
                    stations.append({
                        "id": station_id,
                        "title": st_title,
                        "part_label": lspec["label"],
                        "part_id": pid,
                        "plane": lspec["plane"],
                        "x": round(float(lspec["x"]), 3),
                        "mx": round(float(lspec["x"]) * fw, 1),
                        "y": round(float(lspec["y"]), 3),
                        "anim_role": lspec.get("anim_role", "static"),
                    })

            combined_layers.sort(key=lambda item: float(item.get("z", 1.4)), reverse=True)
            total_layers += len(combined_layers)

            stations.sort(key=lambda s: s["x"])
            n_st = len(stations)
            station_order = [0, 1, 2, 1] if n_st >= 3 else list(range(max(1, n_st)))
            for l_idx, ln in enumerate(sc.get("lines", [])):
                if stations:
                    st_pick = stations[station_order[l_idx % len(station_order)] % n_st]
                    jitter = ((l_idx % 3) - 1) * 18.0
                    ln["mx"] = round(max(160.0, min(fw - 160.0, float(st_pick["mx"]) + jitter)), 1)
                    ln["station_id"] = st_pick["id"]
                    ln["station_label"] = st_pick["title"]
                    ln["station_part_label"] = st_pick["part_label"]
                    ln["station_anim"] = st_pick["anim_role"]

            # Ensure first line's posture_cue matches the scene's initial_cue if initial_cue is set
            if spec.get("initial_cue") and sc.get("lines"):
                sc["lines"][0]["posture_cue"] = spec["initial_cue"]

            sc["floor"] = int(spec.get("floor", 614))
            sc["backdrop_file"] = backdrop_play_rel
            sc["initial_cue"] = spec.get("initial_cue", "walk_stride_R")
            sc["preferred_actor"] = spec.get("preferred_actor")
            sc["counterpart"] = spec.get("counterpart")
            sc["stations"] = stations
            sc["multiplane_layers"] = [
                {k: v for k, v in lyr.items() if k != "shots_file"}
                for lyr in combined_layers
            ]

            out_webp = LEVELS_DIR / num_str / sc["img"]
            pil_plate = render_clean_scene_plate(
                out_webp=out_webp,
                backdrop_path=SHOTS_DIR / backdrop_shots_rel,
                floor_y=sc["floor"],
                layers=combined_layers,
                district_glow=sc.get("palette_glow", ["#d8ab4f"]),
                return_pil=True,
            )

            if pil_plate is not None:
                thumb = pil_plate.resize((420, 236), Image.Resampling.LANCZOS)
                tdraw = ImageDraw.Draw(thumb)
                tdraw.rectangle([0, 0, 420, 24], fill=(8, 10, 14))
                st_names = " | ".join(s["title"][:18] for s in stations[:3])
                tdraw.text((6, 5), f"{skey} {sc['name'][:22]} -> {st_names[:42]}", fill=(255, 224, 120))
                if poem_num <= 4:
                    audit_batches["audit_scenes_01_04.png"].append(thumb)
                elif poem_num <= 8:
                    audit_batches["audit_scenes_05_08.png"].append(thumb)
                elif poem_num <= 11:
                    audit_batches["audit_scenes_09_11.png"].append(thumb)
                else:
                    audit_batches["audit_scenes_12_14.png"].append(thumb)

            total_scenes += 1

        lv_path.write_text(json.dumps(lv, separators=(",", ":")))
        print(f"  Poem {num_str} ({lv['title']}): custom-built {len(lv['scenes'])} scenes")

    print("[3/4] Saving visual audit contact sheets for all 90 scenes...")
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    for bname, thumbs in audit_batches.items():
        cols = 4
        rows = (len(thumbs) + cols - 1) // cols
        grid = Image.new("RGB", (cols * 424, rows * 240), (10, 12, 16))
        for i, im in enumerate(thumbs):
            grid.paste(im, ((i % cols) * 424 + 2, (i // cols) * 240 + 2))
        grid.save(SCRATCH_DIR / bname)
        print(f"  Saved {SCRATCH_DIR / bname} ({len(thumbs)} scenes)")

    print(f"[4/4] DONE! Custom-built {total_scenes} scenes with {total_layers} verified multiplane layers.")


if __name__ == "__main__":
    main()
