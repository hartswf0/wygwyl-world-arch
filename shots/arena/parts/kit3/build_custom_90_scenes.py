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
            L("01.hero.severn__p15", "Nocturnal Sky Backing Outside Bedroom Window", "P6", 6.00, 0.78, 0.30, 0.22, "cloud_drift_L", None, False, 0.88),
            L("01.hero.severn__p02", "Distant Severn Brick Tenement Across Alley", "P5", 3.85, 0.80, 0.62, 0.28, "static", None, False, 0.84),
            L("01.props.room__p19", "Bedroom Baseboard & Dark Television Screen", "P4", 2.60, 0.50, 0.88, 0.24, "static", None),
            L("01.props.window__p01", "Closed High-Rise Sash Window", "P4", 2.40, 0.80, 0.85, 0.50, "portal_aperture", "High-Rise Sash Window"),
            L("01.props.room__p01", "Three-Drawer Wooden Bedroom Dresser", "P3", 1.44, 0.20, 0.88, 0.34, "drawer_slide", "Wooden Bedroom Dresser"),
            L("01.props.room__p18", "Flickering Bedroom Television & Stand", "P3", 1.42, 0.48, 0.88, 0.32, "portal_tv_flicker", "Flickering TV Stand"),
            L("01.props.handheld__p04", "Open Poetry Manuscript Sheaf on Floor", "P2", 1.04, 0.34, 0.90, 0.18, "static", None),
            L("01.fx.haze-words__p01", "Foreground Drifting Blue Vape Haze", "P1", 0.54, 0.82, 0.92, 0.16, "cloud_drift_L", None, False, 0.76),
            L("01.props.window__p04", "Proscenium Bedroom Window Mullion Frame", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "01.1": {
        "backdrop": "world/ef456e2a_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_L",
        "counterpart": None,
        "layers": [
            L("01.fx.haze-words__p05", "Upper Ozone Dome Amber Sky Glow", "P6", 6.00, 0.52, 0.24, 0.18, "cloud_drift_L", None, False, 0.86),
            L("01.hero.catwalk__p03", "Distant Suspended Catwalk Girder", "P5", 3.85, 0.78, 0.54, 0.22, "static", None, False, 0.82),
            L("01.props.window__p01", "Amber-Lit Apartment Sash Window", "P4", 2.42, 0.52, 0.84, 0.52, "portal_aperture", "Haze at the Window"),
            L("01.props.window__p13", "Iron Fire-Escape Balcony Landing", "P4", 2.36, 0.82, 0.86, 0.32, "fire_escape_landing", "Fire-Escape Landing"),
            L("01.props.room__p14", "Wide Bedroom Chest of Open Drawers", "P3", 1.45, 0.21, 0.88, 0.28, "drawer_slide", "Hallway & Drawers"),
            L("01.props.room__p03", "Pulled-Out Wooden Drawer on Focal Floor", "P2", 1.04, 0.34, 0.90, 0.14, "drawer_slide", None),
            L("01.fx.haze-words__p06", "Drifting Pre-Language Vape Haze Plume", "P1", 0.52, 0.56, 0.56, 0.18, "cloud_drift_L", None, False, 0.78),
            L("01.hero.severnescape__p01", "Proscenium Brick Window-Jamb Frame", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "01.2": {
        "backdrop": "world/caaf4b3a_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "fire_escape_climb",
        "counterpart": {"key": "ex/ex_jacket", "x": 1020, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("04.fx.moon-reach__p01", "High-Altitude Night Moon Above the Drop", "P6", 6.00, 0.82, 0.24, 0.18, "lamp_glow", None, False, 0.88),
            L("01.set.city_fall_void__p03", "Distant Nocturnal Skyscraper Tower", "P5", 3.85, 0.34, 0.68, 0.36, "static", None, False, 0.82),
            L("01.props.window__p01", "Open Apartment Sash Window", "P4", 2.46, 0.18, 0.85, 0.44, "portal_aperture", "Open Sash Window"),
            L("01.props.window__p13", "Iron Fire-Escape Balcony & Rail", "P4", 2.38, 0.48, 0.86, 0.36, "fire_escape_landing", "Iron Fire Escape"),
            L("01.hero.severn__p11", "Zig-Zag Iron Fire-Escape Stairs", "P4", 2.34, 0.78, 0.86, 0.42, "fire_escape_landing", "Edge of the Drop"),
            L("01.hero.severn__p12", "Lower Iron Landing Grate Over the Drop", "P3", 1.42, 0.64, 0.89, 0.22, "static", None),
            L("01.props.handheld__p07", "Crumpled Poem Page Caught on the Ledge", "P2", 1.04, 0.36, 0.88, 0.16, "tambourine_arc", None),
            L("01.fx.haze-words__p07", "Fast Foreground Amber Light-Leak Streak", "P1", 0.54, 0.84, 0.92, 0.16, "cloud_drift_L", None, False, 0.78),
            L("01.hero.severnescape__p02", "Proscenium Vertical Iron Escape Ladder", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "01.3": {
        "backdrop": "world/38543022_3/backdrop.webp",
        "floor": 620,
        "initial_cue": "fall_invert",
        "counterpart": {"key": "ex/ex_jacket", "x": 980, "dir": 1, "cue": "fall_back", "y_offset": -75},
        "layers": [
            L("01.hero.severn__p15", "Vertigo Night Sky Above the Spire Canyon", "P6", 6.00, 0.50, 0.22, 0.22, "cloud_drift_L", None, False, 0.88),
            L("01.set.city_fall_void__p04", "Deep Obsidian Spire Horizon Shaft", "P5", 3.85, 0.34, 0.68, 0.40, "static", None, False, 0.82),
            L("01.set.city_fall_void__p01", "Vertical Skyscraper Canyon Left", "P4", 2.52, 0.18, 0.86, 0.58, "portal_other_world", "Tower Canyon Wall"),
            L("01.set.city_fall_void__p02", "Vertical Skyscraper Canyon Right", "P4", 2.50, 0.82, 0.86, 0.58, "portal_other_world", None),
            L("01.fx.haze-words__p09", "Plum & Amber Freefall Light Leak", "P3", 1.40, 0.50, 0.58, 0.22, "cloud_drift_L", "The Vertical Freefall"),
            L("01.props.chandeliers__p10", "Ballroom Chandelier Rising Below", "P3", 1.44, 0.78, 0.42, 0.22, "chandelier_sway", "Skylight Above Ballroom"),
            L("01.props.handheld__p07", "Tumbling Manuscript Pages in Freefall", "P2", 1.04, 0.36, 0.64, 0.18, "tambourine_arc", None),
            L("01.fx.haze-words__p02", "Vertical Streaking Tower Motion-Blur", "P1", 0.52, 0.12, 0.72, 0.32, "cloud_drift_L", None, False, 0.80),
            L("01.set.city_fall_void__p05", "Proscenium Shadow Tower Repoussoir", "P0", 0.25, 0.96, 0.95, 0.42, "proscenium_mask", None, True, 0.85),
        ],
    },
    "01.4": {
        "backdrop": "world/cb6cbbfc_1/backdrop.webp",
        "floor": 612,
        "initial_cue": "sprint_pursuit",
        "counterpart": {"key": "vintage_woman/gown", "x": 920, "dir": -1, "cue": "waltz"},
        "layers": [
            L("01.props.chandeliers__p02", "Vaulted Skylight Chandelier Canopy", "P6", 6.00, 0.50, 0.28, 0.26, "chandelier_sway", None, False, 0.86),
            L("14.set.vintage_party__p01", "Distant 1940s Wood-Panelled Ceiling Gallery", "P5", 3.85, 0.50, 0.24, 0.22, "static", None, False, 0.84),
            L("14.set.vintage_party__p03", "Grand Ballroom Timber Archway", "P4", 2.42, 0.52, 0.86, 0.50, "portal_other_world", "Vintage Waltz Floor"),
            L("01.props.chandeliers__p10", "Crystal Ballroom Chandelier West", "P3", 1.48, 0.24, 0.34, 0.22, "chandelier_sway", "Crystal Chandelier Hall"),
            L("01.props.chandeliers__p11", "Crystal Ballroom Chandelier East", "P3", 1.48, 0.78, 0.34, 0.22, "chandelier_sway", "Ballroom Bandstand"),
            L("14.props.party__p03", "Brass Gramophone Horn on Waltz Floor", "P2", 1.05, 0.16, 0.89, 0.22, "lamp_glow", None),
            L("01.props.chandeliers__p27", "Foreground Crystal Chandelier Glint", "P1", 0.54, 0.86, 0.42, 0.18, "lamp_glow", None, False, 0.82),
            L("14.set.vintage_party__p02", "Proscenium Panelled Ballroom Wall", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "01.5": {
        "backdrop": "world/b0118d62_2/backdrop.webp",
        "floor": 616,
        "initial_cue": "fall_midair",
        "counterpart": {"key": "ex/ex_jacket", "x": 960, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("01.props.chandeliers__p03", "Dimmed Overhead Ballroom Chandelier Arm", "P6", 6.00, 0.50, 0.24, 0.20, "chandelier_sway", None, False, 0.86),
            L("01.set.city_fall_void__p06", "Deep Vertical Elevator Shaft Beyond Floor", "P5", 3.85, 0.78, 0.68, 0.36, "static", None, False, 0.82),
            L("14.set.vintage_party__p03", "Ballroom Threshold Archway", "P4", 2.46, 0.20, 0.86, 0.48, "portal_aperture", "Ballroom Colonnade"),
            L("01.props.trapdoor__p12", "Open Floor Trapdoor Into the Abyss", "P3", 1.36, 0.52, 0.90, 0.28, "portal_aperture", "Hole in the Floor"),
            L("01.props.trapdoor__p11", "Half-Open Trapdoor Timber Frame", "P3", 1.34, 0.80, 0.89, 0.24, "drawer_slide", "Rim of the Void"),
            L("01.props.trapdoor__p02", "Splintered Trapdoor Leaf Under Poet", "P2", 1.04, 0.36, 0.90, 0.22, "static", None),
            L("01.fx.haze-words__p08", "Rising Abyss Vape Mist Plume", "P1", 0.54, 0.64, 0.93, 0.16, "cloud_drift_L", None, False, 0.78),
            L("01.props.trapdoor__p01", "Proscenium Floor Slab Aperture Frame", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
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
            L("02.set.overseer_skyline__p01", "Distant Nocturnal Overseer Cloud Canopy", "P6", 6.00, 0.50, 0.24, 0.18, "cloud_drift_L", None, False, 0.86),
            L("02.set.overseer_skyline__p02", "Far City Tower Silhouette in Darkness", "P5", 3.85, 0.34, 0.66, 0.32, "static", None, False, 0.82),
            L("02.set.black_void__p01", "Inward-Caving Dark Wall Left", "P4", 2.48, 0.18, 0.88, 0.58, "portal_other_world", "Walls Caving Inward"),
            L("02.set.black_void__p02", "Inward-Caving Dark Wall Right", "P4", 2.48, 0.82, 0.88, 0.58, "portal_other_world", "The Silent Scream"),
            L("02.hero.drowned-light__p07", "Submerged Corridor Light Shaft", "P3", 1.40, 0.50, 0.82, 0.28, "lamp_glow", None),
            L("02.props.mirror-phone-rings__p14", "Standing Mirror Reflection in Void", "P2", 1.04, 0.36, 0.78, 0.22, "phone_ring", None),
            L("02.fx.lights-iris__p01", "Sweeping White Headlight Beam", "P1", 0.48, 0.48, 0.56, 0.18, "headlight_beam", "Falling With Headlights Off"),
            L("02.fx.lights-iris__p02", "Flashing Amber Hazard Beam", "P1", 0.46, 0.56, 0.72, 0.18, "headlight_beam", None),
            L("02.hero.drowned-light__p06", "Proscenium Dark Void Glass Panel", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "02.1": {
        "backdrop": "world/fb5ef893_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "bed_despair_sit",
        "counterpart": None,
        "layers": [
            L("02.fx.lights-iris__p06", "1:08 AM Ceiling Iris Glare Ring", "P6", 6.00, 0.78, 0.24, 0.18, "lamp_glow", None, False, 0.86),
            L("02.set.eye_macro.road__p01", "Memory Highway Horizon Beyond the Eye", "P5", 3.88, 0.76, 0.56, 0.20, "static", None, False, 0.82),
            L("02.set.bedroom_night__p01", "Midnight Bedroom Plain Backwall", "P5", 3.80, 0.30, 0.78, 0.32, "static", None, False, 0.86),
            L("02.set.bedroom_night__p03", "Standing Bedroom Mirror Glass Insert", "P4", 2.44, 0.54, 0.85, 0.44, "portal_other_world", None),
            L("02.set.bedroom_night__p02", "Standing Bedroom Mirror Frame (1:08 AM)", "P4", 2.40, 0.54, 0.86, 0.46, "portal_aperture", "The Midnight Mirror"),
            L("02.props.poet-eye-aperture__p12", "Dilating Poet Eye Opening to Past", "P4", 2.46, 0.82, 0.66, 0.24, "portal_aperture", "Dilating Eye Aperture"),
            L("02.set.bedroom_night__p05", "Dark Wooden Bed Headboard", "P3", 1.48, 0.24, 0.78, 0.18, "static", None),
            L("02.set.bedroom_night__p04", "Low Wooden Bed Platform Frame", "P3", 1.46, 0.24, 0.88, 0.18, "lamp_base", "Midnight Bed"),
            L("02.set.bedroom_night__p08", "Rumpled Dark-Blue Midnight Blanket", "P3", 1.42, 0.25, 0.86, 0.20, "lamp_base", None),
            L("02.props.mirror-phone-rings__p06", "Glowing Smartphone Emergency Call", "P2", 1.04, 0.38, 0.84, 0.16, "phone_ring", None),
            L("02.props.mirror-phone-rings__p10", "Foreground Phone Base & Ring Pulse", "P1", 0.54, 0.38, 0.92, 0.14, "phone_ring", None, False, 0.82),
            L("02.props.mirror-phone-rings__p01", "Proscenium Tall Mirror Frame Edge", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "02.2": {
        "backdrop": "world/7fdacba9_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_R",
        "preferred_actor": "young_poet/pajamas_winter",
        "counterpart": None,
        "layers": [
            L("04.fx.moon-reach__p01", "Winter Moon Above the 1990s Driveway", "P6", 6.00, 0.82, 0.22, 0.18, "lamp_glow", None, False, 0.86),
            L("02.set.living_room_1990s__p11", "Suburban Driveway View Outside Window", "P5", 3.88, 0.32, 0.68, 0.24, "static", None, False, 0.88),
            L("02.set.driveway_road_night__p01", "Distant Wet Asphalt Driveway Sky", "P5", 3.82, 0.74, 0.54, 0.18, "static", None, False, 0.82),
            L("02.set.living_room_1990s__p01", "1990s Living Room Window Wall (Transparent Aperture)", "P4", 2.48, 0.32, 0.82, 0.38, "portal_aperture", "Childhood Window View"),
            L("02.set.living_room_1990s__p05", "Left Floral Window Curtain", "P4", 2.44, 0.18, 0.70, 0.26, "curtain_sway_L", None),
            L("02.set.living_room_1990s__p07", "Right Floral Window Curtain", "P4", 2.44, 0.46, 0.70, 0.26, "curtain_sway_R", None),
            L("02.set.living_room_1990s__p04", "1990s Floral Living Room Sofa", "P3", 1.46, 0.26, 0.87, 0.24, "lamp_base", "Living Room Sofa"),
            *car_ensemble(cx=0.74, floor_y=0.87, car_scale=0.25, station_title="Family Sedan Pulling Up", with_parents=False),
            L("02.set.living_room_1990s__p08", "Turned Brass Table-Lamp Base", "P2", 1.06, 0.50, 0.88, 0.22, "lamp_base", None),
            L("02.set.living_room_1990s__p09", "Pleated Table-Lamp Shade", "P2", 1.04, 0.50, 0.72, 0.14, "lamp_glow", None),
            L("02.fx.lights-iris__p01", "Headlight Glare Sweeping Across Ceiling", "P1", 0.46, 0.54, 0.42, 0.16, "headlight_beam", None),
            L("02.props.window__p01", "Proscenium Drawn Living-Room Drape", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "02.3": {
        "backdrop": "world/34a1d5c3_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_L",
        "preferred_actor": "young_poet/pajamas_winter",
        "counterpart": {"key": "ghost_child/ghost_nightclothes", "x": 330, "dir": 1, "cue": "idle"},
        "layers": [
            L("02.hero.drowned-light__p01", "Shadowed Ceiling Moulding & Cold Draft", "P6", 6.00, 0.50, 0.20, 0.16, "static", None, False, 0.86),
            L("02.set.overseer_skyline__p03", "Distant Winter Tower Beyond the Frost", "P5", 3.85, 0.52, 0.62, 0.28, "static", None, False, 0.80),
            L("02.set.living_room_1990s__p02", "1990s Hallway Back Wall & Open Doorway", "P4", 2.48, 0.24, 0.84, 0.38, "portal_aperture", None),
            L("02.set.living_room_1990s__p03", "Childhood Doorpost With 7 Pencil Height Marks", "P4", 2.44, 0.35, 0.84, 0.38, "portal_aperture", "Doorpost Height Marks"),
            L("02.props.window__p22", "Frost-Rimed Living Room Window", "P4", 2.42, 0.56, 0.78, 0.30, "portal_aperture", "Frost at the Window"),
            L("02.set.living_room_1990s__p04", "1990s Floral Living Room Sofa", "P3", 1.46, 0.80, 0.87, 0.24, "lamp_base", None),
            L("02.props.tambourine__p08", "Ghost Child's Wooden Tambourine Jingle", "P2", 1.05, 0.74, 0.74, 0.15, "tambourine_arc", "The Ghost's Tambourine"),
            L("02.fx.lights-iris__p07", "Warm Heavy Breath Frost Halo", "P1", 0.54, 0.36, 0.64, 0.16, "cloud_drift_L", None, False, 0.78),
            L("02.hero.childhouse__p07", "Proscenium Brick Rowhouse Jamb", "P0", 0.25, 0.96, 0.95, 0.40, "proscenium_mask", None, True, 0.85),
        ],
    },
    "02.4": {
        "backdrop": "world/7f7e3980_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "preferred_actor": "young_poet/pajamas_winter",
        "counterpart": None,
        "layers": [
            L("02.props.blinds-height__p22", "Raised Venetian Window Top Rail Overhead", "P6", 6.00, 0.26, 0.22, 0.14, "static", None, False, 0.88),
            L("02.set.driveway_road_night__p03", "Distant Winding Driveway Road Curve", "P5", 3.85, 0.72, 0.68, 0.22, "static", None, False, 0.82),
            L("02.set.living_room_1990s__p01", "Living Room Window Wall Looking Out", "P4", 2.48, 0.24, 0.82, 0.36, "portal_aperture", None),
            L("02.set.living_room_1990s__p06", "Slatted Venetian Window Blinds", "P4", 2.44, 0.24, 0.68, 0.24, "curtain_sway_L", "Raised Window Blinds"),
            *car_ensemble(cx=0.62, floor_y=0.87, car_scale=0.27, station_title="Parents Arguing in the Car", with_parents=True),
            L("02.set.living_room_1990s__p04", "Childhood Floral Sofa by the Window", "P2", 1.05, 0.20, 0.89, 0.20, "static", None),
            L("02.fx.lights-iris__p02", "Flashing Amber Hazard Wash", "P1", 0.46, 0.82, 0.80, 0.18, "headlight_beam", "Flashing Hazard Lights"),
            L("02.props.blinds-height__p08", "Proscenium Notched Height-Mark Doorpost", "P0", 0.25, 0.04, 0.95, 0.40, "proscenium_mask", None, False, 0.85),
        ],
    },
    "02.5": {
        "backdrop": "world/8bc7b3e2_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "sprint_pursuit",
        "preferred_actor": "young_poet/pajamas_winter",
        "counterpart": {"key": "ghost_child/ghost_nightclothes", "x": 240, "dir": 1, "cue": "idle"},
        "layers": [
            L("02.fx.lights-iris__p04", "Fractured Night Sky Glare Outside", "P6", 6.00, 0.78, 0.26, 0.20, "lamp_glow", None, False, 0.86),
            L("02.set.overseer_skyline__p06", "Distant Palace Silhouette Beyond the Pane", "P5", 3.85, 0.74, 0.62, 0.20, "static", None, False, 0.82),
            L("02.props.window__p21", "Cracked Living Room Window & Drapes", "P4", 2.44, 0.22, 0.78, 0.30, "portal_aperture", "Living Room Window"),
            L("02.hero.childhouse__p11", "Shattering Glass Window Pane", "P4", 2.40, 0.78, 0.78, 0.44, "portal_aperture", "Shattering Window Glass"),
            L("02.hero.childhouse__p15", "Forking Glass Hole Into the Night", "P3", 1.38, 0.78, 0.78, 0.38, "portal_other_world", None),
            L("02.props.tambourine__p08", "Wooden Tambourine Hurling Outward", "P2", 1.04, 0.52, 0.56, 0.16, "tambourine_arc", "Tambourine in Flight"),
            L("02.props.tambourine__p11", "Spinning Tambourine Blur Disc & Shards", "P1", 0.52, 0.66, 0.62, 0.18, "tambourine_arc", None, False, 0.84),
            L("02.props.window__p03", "Proscenium Torn Curtain & Window Frame", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
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
            L("03.props.rose-window__p01", "Vaulted Gothic Rose Window Clerestory", "P6", 6.00, 0.50, 0.26, 0.26, "stained_glass_glow", None, False, 0.88),
            L("03.hero.chapel__p06", "Distant Sanctuary Apse Rib Vault", "P5", 3.85, 0.50, 0.64, 0.22, "static", None, False, 0.80),
            L("03.props.rose-window__p10", "Stained-Glass Gothic Rose Window", "P4", 2.46, 0.22, 0.58, 0.38, "stained_glass_glow", "Gothic Rose Window"),
            L("03.hero.chapel__p11", "Stone Gothic Chapel Nave & Arch", "P4", 2.42, 0.78, 0.86, 0.50, "portal_aperture", "Chapel Sanctuary Arch"),
            L("03.hero.chapel.interior-states__p03", "Empty First-Row Sanctuary Pew", "P3", 1.42, 0.34, 0.88, 0.24, "static", None),
            L("02.props.tambourine__p08", "Tambourine Ringing Through the Nave", "P2", 1.04, 0.50, 0.54, 0.15, "tambourine_arc", "Arc of the Tambourine"),
            L("03.fx.storm-light__p14", "Amber Stained-Glass Light Beam", "P1", 0.54, 0.28, 0.74, 0.20, "lamp_glow", None, False, 0.80),
            L("03.set.chapel_side_doors__p02", "Proscenium Carved Stone Nave Pier", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "03.1": {
        "backdrop": "world/fd7ea369_0/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_L",
        "counterpart": None,
        "layers": [
            L("03.props.rose-window__p02", "High Timber Nave Roof Truss", "P6", 6.00, 0.50, 0.20, 0.18, "static", None, False, 0.86),
            L("03.hero.chapel.interior-states__p05", "Distant Empty Choir Loft Gallery", "P5", 3.85, 0.50, 0.62, 0.22, "static", None, False, 0.80),
            L("03.hero.chapel.interior-states__p10", "Tall Gothic Stained-Glass Lancet", "P4", 2.46, 0.20, 0.84, 0.48, "portal_aperture", "Empty Choir & Windows"),
            L("03.hero.chapel.interior-states__p11", "East Gothic Stained-Glass Window", "P4", 2.46, 0.82, 0.84, 0.48, "portal_aperture", None),
            L("03.hero.chapel.interior-states__p03", "Abandoned Wooden Chapel Pew", "P3", 1.44, 0.50, 0.88, 0.26, "lamp_base", "Abandoned Wedding Pews"),
            L("03.props.cobwebs__p01", "Draped Sanctuary Cobwebs", "P3", 1.38, 0.76, 0.68, 0.24, "curtain_sway_L", "Cobwebbed Baptist Pool"),
            L("03.hero.chapel.interior-states__p06", "Dry Stone Baptist Pool Rim on Stage", "P2", 1.05, 0.68, 0.90, 0.20, "static", None),
            L("03.props.cobwebs__p09", "Foreground Hanging Cobweb Veil", "P1", 0.54, 0.14, 0.46, 0.20, "curtain_sway_L", None, False, 0.80),
            L("03.hero.chapel.interior-states__p02", "Proscenium Gothic Lancet Column", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "03.2": {
        "backdrop": "world/3b7236cf_2/backdrop.webp",
        "floor": 612,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "ex/ex_jacket", "x": 1000, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("03.props.rose-window__p03", "Dimmed Sanctuary Triforium Rose", "P6", 6.00, 0.50, 0.26, 0.22, "lamp_glow", None, False, 0.86),
            L("03.hero.chapel__p07", "Distant Altar Steps & Salvations", "P5", 3.85, 0.50, 0.66, 0.22, "static", None, False, 0.80),
            L("03.set.chapel_side_doors__p01", "Left Arched Wooden Side Door", "P4", 2.44, 0.20, 0.86, 0.48, "portal_aperture", "Left Chapel Side Door"),
            L("03.set.chapel_side_doors__p02", "Right Arched Wooden Exit Door", "P4", 2.44, 0.80, 0.86, 0.48, "portal_aperture", "Right Departure Door"),
            L("03.props.gifts-bread-cups__p09", "Opened Wedding Gift Box", "P3", 1.40, 0.48, 0.87, 0.20, "lamp_glow", "Gifts at the Side Doors"),
            L("03.props.gifts-bread-cups__p12", "Abandoned Silver Altar Chalice", "P2", 1.04, 0.62, 0.89, 0.16, "lamp_glow", None),
            L("03.props.strings-footprints__p05", "Unspooled Wedding Ribbon Across Floor", "P1", 0.54, 0.36, 0.93, 0.18, "curtain_sway_L", None, False, 0.82),
            L("03.set.chapel_side_doors__p03", "Proscenium Heavy Oak Door Architrave", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "03.3": {
        "backdrop": "world/42e101f6_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "fall_back_start",
        "counterpart": None,
        "layers": [
            L("03.set.chapel_storm__p01", "Thunderhead Storm Canopy Over Roof", "P6", 6.00, 0.50, 0.22, 0.20, "cloud_drift_L", None, False, 0.88),
            L("03.hero.chapel.decay__p06", "Shattered Nave Roof & Rain Deluge", "P5", 3.85, 0.50, 0.60, 0.24, "static", None, False, 0.80),
            L("03.fx.storm-light__p15", "Storm-Lashed Gothic Window West", "P4", 2.46, 0.22, 0.84, 0.44, "portal_aperture", "Thunder in the Nave"),
            L("03.hero.chapel.decay__p01", "Weathered Stone Bell-Gable Arch", "P4", 2.42, 0.52, 0.86, 0.48, "portal_aperture", "The Storm Breaks"),
            L("03.hero.chapel.decay__p11", "Rain-Flooded Sanctuary Stones", "P3", 1.42, 0.68, 0.88, 0.26, "wave_mid", None),
            L("03.props.gifts-bread-cups__p04", "Toppled Communion Cup in the Downpour", "P2", 1.04, 0.36, 0.90, 0.16, "wave_near", None),
            L("03.fx.storm-light__p07", "Jagged White Lightning Bolt", "P1", 0.46, 0.78, 0.62, 0.38, "light_ray", "Lightning & Downpour"),
            L("03.fx.storm-light__p01", "Proscenium Vertical Storm-Flash Pillar", "P0", 0.25, 0.96, 0.95, 0.40, "proscenium_mask", None, True, 0.85),
        ],
    },
    "03.4": {
        "backdrop": "world/590a0c02_0/backdrop.webp",
        "floor": 616,
        "initial_cue": "walk_away_back",
        "counterpart": {"key": "ex/ex_jacket", "x": 1020, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("03.set.chapel_storm__p02", "Clearing Post-Storm Horizon Clouds", "P6", 6.00, 0.50, 0.24, 0.18, "cloud_drift_L", None, False, 0.86),
            L("03.set.remnants_shore__p01", "Distant Storm-Washed Coastal Reef", "P5", 3.85, 0.50, 0.70, 0.16, "wave_far", None, False, 0.80),
            L("03.hero.chapel.ruin__p01", "Collapsed Stone Chapel Archway", "P4", 2.44, 0.22, 0.86, 0.38, "portal_aperture", "Collapsed Chapel Stone"),
            L("03.props.gifts-bread-cups__p03", "Daily Bread Soaked on the Shore", "P3", 1.40, 0.50, 0.88, 0.18, "wave_mid", "Remnants on the Shore"),
            L("03.props.strings-footprints__p11", "Parting Footsteps in Wet Sand", "P2", 1.04, 0.78, 0.89, 0.24, "drawer_slide", "Footsteps Leading Away"),
            L("03.set.remnants_shore__p06", "Foreground Receding Tide Foam Band", "P1", 0.54, 0.34, 0.94, 0.16, "wave_near", None, False, 0.82),
            L("03.hero.chapel.ruin__p04", "Proscenium Broken Sea-Cliff Buttress", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "03.5": {
        "backdrop": "world/993cc7a2_0/backdrop.webp",
        "floor": 616,
        "initial_cue": "fall_landed",
        "counterpart": None,
        "layers": [
            L("03.props.rose-window__p06", "Broken Rose-Window Arch Against Dusk Sky", "P6", 6.00, 0.76, 0.26, 0.18, "static", None, False, 0.86),
            L("03.hero.chapel.ruin__p06", "Distant Drowned Nave Foundation Stones", "P5", 3.85, 0.50, 0.70, 0.18, "static", None, False, 0.80),
            L("03.hero.chapel.ruin__p01", "Broken Stone Arch on the Tide", "P4", 2.42, 0.22, 0.86, 0.36, "portal_aperture", "Ruined Shore Arch"),
            L("04.props.word-shore__p22", "Rusted Shore Lantern at Dusk", "P3", 1.40, 0.80, 0.86, 0.28, "lamp_glow", "Tide Line at Dusk"),
            L("03.props.tambourine-broken__p13", "Shattered Tambourine Rim & Skin", "P2", 1.04, 0.52, 0.88, 0.20, "tambourine_arc", "Shattered Tambourine"),
            L("03.props.tambourine-broken__p03", "Foreground Scattered Brass Jingle Shard", "P1", 0.54, 0.36, 0.93, 0.16, "wave_near", None, False, 0.84),
            L("03.hero.chapel.ruin__p12", "Proscenium Shattered Sanctuary Arch Pier", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
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
            L("04.fx.moon-reach__p02", "Ash-Veiled Night Moon Above the Surf", "P6", 6.00, 0.80, 0.24, 0.20, "lamp_glow", None, False, 0.88),
            L("04.set.shore_night__p01", "Distant Whitecap Surf Horizon Line", "P5", 3.85, 0.50, 0.70, 0.16, "wave_far", None, False, 0.80),
            L("04.set.shore_night__p08", "Wind-Swept Shore Tree West", "P4", 2.46, 0.20, 0.86, 0.38, "curtain_sway_L", "Ash-Covered Shore"),
            L("04.props.word-shore__p08", "Carved NEVERMORE Stone Tablet", "P3", 1.40, 0.50, 0.88, 0.24, "wave_mid", "Broken Pieces on Sand"),
            L("04.set.shore_night__p06", "Charred Wildfire Driftwood Stump", "P3", 1.42, 0.78, 0.87, 0.26, "static", "Charred Stump & Raven"),
            L("04.props.ravens-stumps__p03", "Perched Black Raven on Focal Stump", "P2", 1.04, 0.78, 0.66, 0.20, "wing_flap_L", None),
            L("04.set.shore_night__p10", "Foreground Wildfire Ash & Tide Drift", "P1", 0.54, 0.34, 0.94, 0.14, "wave_near", None, False, 0.82),
            L("04.set.shore_night__p07", "Proscenium Charred Shore Bough Frame", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "04.1": {
        "backdrop": "world/3238a164_1/backdrop.webp",
        "floor": 616,
        "initial_cue": "still_sentinel",
        "counterpart": None,
        "layers": [
            L("04.fx.moon-reach__p01", "Pale Full Moon Over Still Sea", "P6", 6.00, 0.24, 0.26, 0.22, "sun_pulse", "Moon Over Still Water"),
            L("04.set.shore_night__p02", "Folded Whispering Horizon Wave Band", "P5", 3.85, 0.50, 0.70, 0.16, "static", None, False, 0.80),
            L("04.set.shore_night__p09", "Still Shore Tree in Silence", "P4", 2.42, 0.78, 0.86, 0.36, "static", "Muted Trees in Silence"),
            L("04.props.word-shore__p23", "Still Wrought-Iron Shore Lantern", "P3", 1.42, 0.50, 0.86, 0.28, "static", "The Muted Waves"),
            L("04.props.ravens-stumps__p04", "Silent Watching Raven on the Sand", "P2", 1.04, 0.82, 0.66, 0.18, "static", None),
            L("04.set.shore_night__p03", "Foreground Glassy Still Water Ripple", "P1", 0.54, 0.36, 0.94, 0.14, "static", None, False, 0.82),
            L("04.set.shore_night__p08", "Proscenium Muted Shore Pine Silhouette", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },
    "04.2": {
        "backdrop": "world/ef9f6c7e_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "kneel_hollow",
        "counterpart": None,
        "layers": [
            L("04.fx.moon-reach__p03", "Moonlight Halo Breaking Through Mist", "P6", 6.00, 0.76, 0.24, 0.20, "lamp_glow", None, False, 0.88),
            L("04.set.incline_trail__p01", "Distant Coastal Incline Ridge", "P5", 3.85, 0.52, 0.68, 0.18, "static", None, False, 0.80),
            L("04.hero.viaduct__p02", "Stone Coastal Wall & Incline Steps", "P4", 2.44, 0.80, 0.86, 0.42, "portal_aperture", "Steps Toward the Incline"),
            L("04.props.word-shore__p08", "Carved NEVERMORE Relic in Sand", "P3", 1.42, 0.22, 0.88, 0.22, "drawer_slide", "Folded Whispers"),
            L("04.props.heart__p10", "Throbbing Poet Heart on Stand", "P2", 1.04, 0.50, 0.87, 0.30, "heart_beat", "The Heart on the Sand"),
            L("04.props.word-shore__p02", "Foreground Washed-Ashore Driftwood & Verse", "P1", 0.54, 0.18, 0.94, 0.18, "wave_near", None, False, 0.82),
            L("04.hero.viaduct__p05", "Proscenium Stone Incline Pier", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "04.3": {
        "backdrop": "world/3a2ddc9d_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": None,
        "layers": [
            L("04.fx.moon-reach__p05", "Ascending Moon Over the Viaduct Ridge", "P6", 6.00, 0.82, 0.22, 0.20, "lamp_glow", None, False, 0.88),
            L("04.props.ravens-stumps__p11", "Soaring Raven Overhead", "P5", 3.80, 0.68, 0.28, 0.20, "wing_flap_R", None),
            L("04.hero.viaduct__p02", "Lower Stone Viaduct Retaining Wall", "P4", 2.44, 0.22, 0.86, 0.42, "fire_escape_landing", "Base of the Incline"),
            L("04.hero.viaduct__p04", "Arched Stone Viaduct Bridge", "P4", 2.46, 0.78, 0.86, 0.44, "portal_aperture", "Crest of the Trail"),
            L("04.props.faith-blooms__p27", "First Golden Mustard-Seed Bloom", "P3", 1.38, 0.50, 0.87, 0.28, "flower_bloom", "Handcrafted Faith Bloom"),
            L("04.props.heart__p02", "Reclaimed Beating Heart Carried Uphill", "P2", 1.04, 0.36, 0.88, 0.20, "heart_beat", None),
            L("04.props.faith-blooms__p01", "Foreground Sprouting Mustard Stem", "P1", 0.54, 0.86, 0.94, 0.20, "flower_bloom", None, False, 0.84),
            L("04.hero.viaduct__p06", "Proscenium Viaduct Stone Arch Jamb", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "04.4": {
        "backdrop": "world/2ce9173b_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_L",
        "counterpart": None,
        "layers": [
            L("04.fx.moon-reach__p01", "Luminous Full Moon Overhead", "P6", 6.00, 0.78, 0.24, 0.22, "sun_pulse", "Moonlit Garden Edge"),
            L("04.set.night_garden_field__p01", "Distant Golden Horizon Bloom Meadow", "P5", 3.85, 0.50, 0.68, 0.16, "static", None, False, 0.82),
            L("04.set.night_garden_field__p04", "Perspective Rows of Golden Blooms", "P4", 2.52, 0.50, 0.84, 0.14, "static", None),
            L("04.props.faith-blooms__p27", "Golden Mustard Bloom West", "P3", 1.38, 0.22, 0.87, 0.28, "flower_bloom", "West Garden Row"),
            L("04.props.faith-blooms__p13", "Tall Sunflower Stalk & Leaves", "P3", 1.36, 0.52, 0.88, 0.28, "flower_bloom", None),
            L("04.props.faith-blooms__p08", "Golden Sunflower Head in Full Bloom", "P2", 1.04, 0.52, 0.68, 0.22, "flower_bloom", "Center of the Night Field"),
            L("04.props.faith-blooms__p09", "Foreground Swaying Golden Petal Cluster", "P1", 0.54, 0.84, 0.94, 0.20, "flower_bloom", None, False, 0.84),
            L("04.props.faith-blooms__p03", "Proscenium Tall Garden Stalk Silhouette", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "04.5": {
        "backdrop": "world/5dcae595_1/backdrop.webp",
        "floor": 616,
        "initial_cue": "blind_search",
        "counterpart": None,
        "layers": [
            L("04.fx.moon-reach__p04", "Dark Cloud Covering the Moon", "P6", 6.00, 0.50, 0.24, 0.24, "cloud_drift_L", None, False, 0.88),
            L("04.set.night_garden_field__p07", "Shadowed Bare-Ground Horizon Ridge", "P5", 3.85, 0.50, 0.70, 0.18, "static", None, False, 0.80),
            L("04.fx.moon-reach__p09", "Lit Pool of Red Soil in Darkness", "P4", 2.48, 0.50, 0.89, 0.22, "static", None),
            L("04.props.poet-jointed-hands__p11", "Articulated Left Hand on the Ground", "P3", 1.34, 0.24, 0.86, 0.22, "weave_hand_articulation", "Searching the Bare Ground"),
            L("04.props.poet-jointed-hands__p12", "Articulated Right Hand Reattached", "P3", 1.34, 0.78, 0.86, 0.22, "weave_hand_articulation", "Putting the Hands Back On"),
            L("04.props.heart__p01", "Reclaimed Beating Heart in the Chest", "P2", 1.04, 0.52, 0.78, 0.22, "heart_beat", "The Awakened Chest"),
            L("04.props.poet-jointed-hands__p13", "Foreground Reaching Fingers in Red Soil", "P1", 0.54, 0.16, 0.94, 0.16, "weave_hand_articulation", None, False, 0.82),
            L("04.set.shore_night__p09", "Proscenium Night-Field Bough Frame", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },
    "04.6": {
        "backdrop": "world/f05c1fa5_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": None,
        "layers": [
            L("04.fx.moon-reach__p08", "Star-Crowned Night Sky Canopy", "P6", 6.00, 0.78, 0.24, 0.22, "lamp_glow", None, False, 0.88),
            L("04.hero.viaduct__p01", "Distant Full-Span Stone Viaduct Horizon", "P5", 3.85, 0.50, 0.68, 0.22, "static", None, False, 0.80),
            L("04.set.night_garden_field__p04", "Golden Flower Rows Across Field", "P4", 2.52, 0.50, 0.85, 0.14, "static", None),
            L("04.hero.viaduct__p04", "Distant Stone Viaduct Arch", "P4", 2.44, 0.52, 0.85, 0.42, "portal_aperture", "Standing Whole in the Field"),
            L("04.set.shore_night__p09", "Still Guardian Tree Under Stars", "P4", 2.40, 0.80, 0.86, 0.36, "static", "Still Tree Under Stars"),
            L("04.props.faith-blooms__p27", "Blooming Golden Sunflower West", "P3", 1.38, 0.22, 0.87, 0.28, "flower_bloom", "Western Bloom Row"),
            L("04.props.poet-jointed-hands__p01", "Whole Rejoined Hands Held Over Heart", "P2", 1.04, 0.36, 0.88, 0.20, "heart_beat", None),
            L("04.props.faith-blooms__p07", "Foreground Golden Sunflower Blossom", "P1", 0.54, 0.86, 0.94, 0.18, "flower_bloom", None, False, 0.84),
            L("04.set.shore_night__p08", "Proscenium Western Field Tree Frame", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
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
            L("05.props.galaxy-universe__p02", "Celestial Ancestral Star Canopy", "P6", 6.00, 0.78, 0.24, 0.20, "planet_orbit", None, False, 0.88),
            L("05.set.night_field_parade__p01", "Distant Ancestral Procession Ridge", "P5", 3.85, 0.50, 0.68, 0.18, "static", None, False, 0.80),
            L("05.set.night_field_parade__p03", "Curved Celestial Horizon Meadow", "P4", 2.54, 0.50, 0.88, 0.18, "static", None),
            L("05.set.night_field_parade__p04", "Western Meadow Stone Marker", "P4", 2.42, 0.22, 0.86, 0.42, "curtain_sway_L", "The Field Goes Still"),
            L("05.set.night_field_parade__p06", "Ancestral Procession Archway", "P4", 2.44, 0.78, 0.86, 0.44, "portal_aperture", "Ancestral Perimeter"),
            L("05.props.star-names__p01", "Radiant Sun & Earth Medallion", "P3", 1.38, 0.52, 0.72, 0.24, "planet_orbit", "Inheriting the Earth"),
            L("05.props.staff-mattress-emblem__p01", "Carved Wooden Ancestor Staff on Meadow", "P2", 1.04, 0.36, 0.90, 0.34, "static", None),
            L("05.hero.perimeter__p09", "Foreground Glowing Perimeter Sigil", "P1", 0.54, 0.86, 0.93, 0.16, "lamp_glow", None, False, 0.82),
            L("05.set.winged_marble_gate__p02", "Proscenium Ancestral Marble Column", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "05.1": {
        "backdrop": "world/434b7bdd_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "victory_cry",
        "counterpart": {"key": "ancestor_elder/white_silver", "x": 960, "dir": -1, "cue": "idle"},
        "layers": [
            L("05.props.galaxy-universe__p01", "Swirling Spiral Galaxy Core Overhead", "P6", 6.00, 0.52, 0.28, 0.26, "planet_orbit", "Spiral Galaxies Overhead"),
            L("05.props.star-names__p05", "Carved JUNE Star Nameplate in Sky", "P5", 3.80, 0.22, 0.34, 0.14, "sun_pulse", "Naming My Own Stars"),
            L("05.hero.perimeter__p04", "Star-Inscribed Perimeter Stone Wall", "P4", 2.44, 0.24, 0.86, 0.32, "portal_aperture", None),
            L("05.props.star-names__p06", "Radiant Star Crest Medallion", "P3", 1.40, 0.78, 0.76, 0.24, "sun_pulse", "The Waiting Past"),
            L("05.props.star-names__p02", "Golden Constellation Astrolabe on Stage", "P2", 1.04, 0.48, 0.88, 0.22, "planet_orbit", None),
            L("05.props.star-names__p14", "Foreground Inscribed Star Banner", "P1", 0.54, 0.84, 0.93, 0.16, "lamp_glow", None, False, 0.82),
            L("05.set.winged_marble_gate__p04", "Proscenium East Star-Gate Pillar", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "05.2": {
        "backdrop": "world/05a0677a_3/backdrop.webp",
        "floor": 616,
        "initial_cue": "kneel_hollow",
        "counterpart": None,
        "layers": [
            L("05.set.humid_basement__p04", "Exposed Southern-Pine Ceiling Joist", "P6", 6.00, 0.50, 0.18, 0.16, "static", None, False, 0.88),
            L("05.set.humid_basement__p02", "Cold-Blue Night Window-Well Backing", "P5", 3.85, 0.64, 0.62, 0.24, "static", None, False, 0.88),
            L("05.set.humid_basement__p01", "Damp Grey Cinderblock Wall & Window-Well Aperture", "P4", 2.44, 0.46, 0.72, 0.34, "portal_aperture", "Basement Window Well"),
            L("05.props.staff-mattress-emblem__p05", "Southern-Pine Quilted Basement Mattress", "P3", 1.42, 0.48, 0.88, 0.30, "lamp_base", "Southern-Pine Mattress"),
            L("05.props.staff-mattress-emblem__p02", "Brass Basement Lantern", "P3", 1.38, 0.74, 0.86, 0.32, "lamp_glow", "Basement Timber Stairs"),
            L("05.props.staff-mattress-emblem__p01", "Carved Wooden Ancestor Staff by Mattress", "P2", 1.04, 0.84, 0.88, 0.42, "static", None),
            L("05.props.staff-mattress-emblem__p04", "Foreground Warm Lantern Glow Cone", "P1", 0.54, 0.74, 0.93, 0.18, "lamp_glow", None, False, 0.80),
            L("05.set.humid_basement__p05", "Proscenium Perforated Iron Joist Plate", "P0", 0.25, 0.04, 0.95, 0.34, "proscenium_mask", None, False, 0.85),
        ],
    },
    "05.3": {
        "backdrop": "world/245fd8b5_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "kneel_universe",
        "counterpart": {"key": "ancestor_robe/indigo_gold", "x": 950, "dir": -1, "cue": "idle"},
        "layers": [
            L("05.props.galaxy-universe__p03", "Newly Invented Nebula Canopy Overhead", "P6", 6.00, 0.50, 0.24, 0.24, "planet_orbit", None, False, 0.88),
            L("05.set.night_field_parade__p02", "Distant Ring of Watching Ancestors", "P5", 3.85, 0.50, 0.68, 0.18, "static", None, False, 0.80),
            L("05.set.winged_marble_gate__p03", "Winged Marble Sanctuary Arch", "P4", 2.44, 0.78, 0.86, 0.48, "portal_aperture", "Sanctuary of the Elders"),
            L("05.props.galaxy-universe__p17", "Golden Pedestal Cupping a New Universe", "P3", 1.38, 0.24, 0.84, 0.28, "planet_orbit", "Inventing a New Universe"),
            L("05.props.staff-mattress-emblem__p07", "Radiant Ancestral Star Emblem", "P2", 1.04, 0.52, 0.76, 0.22, "sun_pulse", "Awarding a Blessing"),
            L("05.props.galaxy-universe__p06", "Foreground Orbiting Miniature Cosmos", "P1", 0.54, 0.16, 0.92, 0.18, "planet_orbit", None, False, 0.82),
            L("05.set.winged_marble_gate__p01", "Proscenium West Marble Gate Column", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "05.4": {
        "backdrop": "world/36c9c157_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "ancestor_elder/white_silver", "x": 960, "dir": -1, "cue": "idle"},
        "layers": [
            L("05.props.star-names__p16", "Sun-Kissed Zenith Solar Medallion", "P6", 6.00, 0.78, 0.24, 0.22, "sun_pulse", None, False, 0.88),
            L("05.hero.perimeter__p05", "Distant Bloodline Horizon Colonnade", "P5", 3.85, 0.50, 0.68, 0.24, "static", None, False, 0.80),
            L("05.set.winged_marble_gate__p01", "Winged Marble Watchtower Pillar", "P4", 2.46, 0.80, 0.86, 0.48, "portal_aperture", "Sun-Kissed Watchtower"),
            L("05.props.fingerprint__p01", "Luminous Whorled Fingerprint Left", "P3", 1.38, 0.22, 0.82, 0.32, "heart_beat", "Blood Through the Hands"),
            L("05.props.fingerprint__p13", "Orchestrating Palm & Sun Whorl", "P2", 1.04, 0.52, 0.82, 0.30, "sun_pulse", "Fingerprints of Power"),
            L("05.props.fingerprint__p10", "Foreground Glowing Crimson Pulse Whorl", "P1", 0.54, 0.36, 0.93, 0.18, "heart_beat", None, False, 0.82),
            L("05.props.fingerprint__p05", "Proscenium Giant Fingerprint Arch Frame", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.84),
        ],
    },
    "05.5": {
        "backdrop": "world/11929669_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "vow_hand_raised",
        "counterpart": {"key": "ancestor_robe/indigo_gold", "x": 960, "dir": -1, "cue": "idle"},
        "layers": [
            L("05.set.winged_marble_gate__p06", "High Winged Marble Architrave Lintel", "P6", 6.00, 0.50, 0.22, 0.18, "static", None, False, 0.88),
            L("06.set.atlantis_waterfront.skyline__p01", "First Glimpse of Atlantis Beyond the Gate", "P5", 3.85, 0.52, 0.66, 0.26, "static", None, False, 0.80),
            L("05.set.winged_marble_gate__p01", "West Winged Marble Gate Pillar", "P4", 2.42, 0.20, 0.86, 0.50, "portal_aperture", "West Winged Pillar"),
            L("05.set.winged_marble_gate__p03", "Central Winged Marble Gate Arch", "P4", 2.40, 0.52, 0.86, 0.52, "portal_aperture", "Baritone at the Gate"),
            L("05.set.winged_marble_gate__p05", "East Winged Marble Gate Pillar", "P4", 2.42, 0.82, 0.86, 0.50, "portal_aperture", "Threshold of Atlantis"),
            L("05.props.staff-mattress-emblem__p03", "Carved Ancestral Crest Pedestal", "P3", 1.40, 0.34, 0.88, 0.26, "lamp_glow", None),
            L("05.props.staff-mattress-emblem__p07", "Resonant Baritone Seal on Threshold", "P2", 1.04, 0.64, 0.89, 0.20, "sun_pulse", None),
            L("05.props.star-names__p15", "Foreground Golden Threshold Plinth", "P1", 0.54, 0.50, 0.94, 0.16, "lamp_glow", None, False, 0.82),
            L("05.set.winged_marble_gate__p02", "Proscenium Fluted Gate Jamb", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },

    # =======================================================================
    # POEM 06 · RESURRECTING ATLANTIS — HANDMADE 7-LAYER WORLD STACKS
    # =======================================================================
    "06.0": {
        "backdrop": "world/ba11d121_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "citizen_1/atlantis", "x": 950, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.fx.comet__p01", "Distant Golden Comet Crown in Canopy", "P6", 6.00, 0.24, 0.20, 0.16, "tambourine_arc", None, False, 0.84),
            L("06.set.atlantis_waterfront.skyline__p12", "Distant Domed Sanctuary of Atlantis", "P5", 3.80, 0.76, 0.80, 0.36, "portal_aperture", None, False, 0.90),
            L("05.set.winged_marble_gate__p03", "Winged Marble Evolution Gate", "P4", 2.44, 0.22, 0.86, 0.50, "portal_aperture", "The Light Gates Open"),
            L("06.set.crystal_tree_hall__p13", "Illuminated Atlantis Crystal Arch", "P4", 2.40, 0.52, 0.86, 0.44, "portal_aperture", "Marble Stones & Hymns"),
            L("06.props.lantern-candle-guitar__p15", "NEXT GATES Sanctuary Signpost", "P3", 1.38, 0.80, 0.86, 0.30, "lamp_glow", "Next Gates Signpost"),
            L("06.props.coin-booth__p04", "Glowing Sanctuary Admission Crest", "P2", 1.04, 0.36, 0.88, 0.18, "sun_pulse", None),
            L("06.props.lantern-candle-guitar__p11", "Foreground Sanctuary Brass Lantern", "P1", 0.55, 0.14, 0.92, 0.18, "lamp_glow", None, False, 0.84),
            L("06.set.narrow_streets__p01", "Proscenium Cobblestone Gate Jamb", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "06.1": {
        "backdrop": "world/c8158a76_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "traveler_1/atlantis", "x": 960, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.fx.comet__p01", "Swirling Golden Comet Sphere in Zenith", "P6", 6.00, 0.22, 0.24, 0.20, "tambourine_arc", "Yellow-Brick Causeway", False, 0.88),
            L("06.fx.comet__p07", "Streaking Golden Comet Tail Across Vista", "P5", 3.75, 0.50, 0.28, 0.16, "headlight_beam", "Following the Comets", False, 0.90),
            L("06.set.atlantis_waterfront.skyline__p12", "Rising Domed Cathedral of Atlantis", "P4", 2.46, 0.78, 0.84, 0.46, "portal_aperture", "Atlantis Horizon Ahead"),
            L("06.set.causeway_road__p03", "Yellow-Brick Causeway Perspective Road", "P3", 1.44, 0.50, 0.92, 0.28, "static", None, False, 0.92),
            L("06.props.lantern-candle-guitar__p15", "Causeway Milestone Signpost", "P3", 1.40, 0.22, 0.87, 0.26, "lamp_glow", None),
            L("06.props.lantern-candle-guitar__p11", "Traveler's Brass Causeway Candle", "P2", 1.04, 0.62, 0.89, 0.16, "lamp_glow", None),
            L("06.fx.comet__p07", "Foreground Golden Causeway Dust Trail", "P1", 0.54, 0.48, 0.93, 0.14, "headlight_beam", None, False, 0.76),
            L("06.set.atlantis_plaza__p09", "Proscenium Terracotta Causeway Arch", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.84),
        ],
    },
    "06.2": {
        "backdrop": "world/bb360097_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "arms_sky_high",
        "counterpart": {"key": "citizen_1/atlantis", "x": 940, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.fx.comet__p01", "High Golden Citadel Sun-Comet", "P6", 6.00, 0.50, 0.18, 0.16, "sun_pulse", None, False, 0.86),
            L("06.set.atlantis_waterfront.skyline__p12", "Far Harbor Domed Citadel Silhouette", "P5", 3.82, 0.34, 0.80, 0.34, "portal_aperture", None, False, 0.90),
            L("06.set.atlantis_waterfront.skyline__p10", "Western Waterfront Arch & Greenery", "P4", 2.44, 0.20, 0.86, 0.44, "portal_aperture", "Waterfront Colonnade"),
            L("06.set.atlantis_waterfront.skyline__p13", "Twin-Towered Atlantis Citadel", "P4", 2.40, 0.52, 0.86, 0.52, "portal_aperture", "Resurrecting Atlantis"),
            L("06.set.atlantis_waterfront.skyline__p14", "Golden Waterfront Sanctuary Spires", "P4", 2.44, 0.82, 0.86, 0.48, "portal_aperture", "Here We Are All One"),
            L("06.props.coin-booth__p01", "Waterfront Sanctuary Welcome Kiosk", "P3", 1.40, 0.34, 0.88, 0.28, "lamp_glow", None),
            L("06.props.coin-booth__p04", "Luminous Unity Seal at Colonnade", "P2", 1.04, 0.66, 0.88, 0.18, "sun_pulse", None),
            L("06.props.lantern-candle-guitar__p11", "Foreground Waterfront Quayside Lantern", "P1", 0.55, 0.86, 0.92, 0.18, "lamp_glow", None, False, 0.84),
            L("06.set.atlantis_plaza__p10", "Proscenium Waterfront Colonnade Pillar", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "06.3": {
        "backdrop": "world/646ab0f0_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "child_traveler/atlantis", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.set.crystal_tree_hall__p07", "Luminous Blue Crystal Tree Canopy Left", "P6", 6.00, 0.22, 0.26, 0.24, "sun_pulse", None, False, 0.88),
            L("06.set.crystal_tree_hall__p13", "Distant Arched Crystal Hall Opening", "P5", 3.80, 0.52, 0.78, 0.34, "portal_inner_world", None, False, 0.90),
            L("06.set.crystal_tree_hall__p01", "Golden Jungle Interface Banyan Trunk", "P4", 2.44, 0.22, 0.86, 0.46, "flower_bloom", "Jungle Interface Pact"),
            L("06.props.coin-booth__p01", "Arched Wooden Heart-Scan Booth", "P3", 1.42, 0.52, 0.87, 0.42, "lamp_glow", "Heart-Scan Admission Booth"),
            L("06.props.coin-booth__p04", "Luminous Cyan Heart-Scan Portal", "P2", 1.04, 0.76, 0.80, 0.24, "sun_pulse", "Relearned Currency"),
            L("06.set.crystal_tree_hall__p14", "Foreground Hanging Sanctuary Vine Fringe", "P1", 0.54, 0.50, 0.22, 0.18, "curtain_sway_L", None, False, 0.84),
            L("06.set.narrow_streets__p03", "Proscenium Banyan Root & Stone Frame", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "06.4": {
        "backdrop": "world/06881630_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "elder_1/atlantis", "x": 940, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.set.crystal_tree_hall__p08", "Sanctuary Crystal Canopy Vault Overhead", "P6", 6.00, 0.50, 0.22, 0.22, "sun_pulse", None, False, 0.86),
            L("06.set.atlantis_waterfront.skyline__p13", "Distant Twin-Spire Plaza Backdrop", "P5", 3.80, 0.36, 0.80, 0.34, "portal_aperture", None, False, 0.90),
            L("06.set.atlantis_plaza__p09", "West Terracotta Plaza Arcade", "P4", 2.44, 0.20, 0.86, 0.44, "portal_aperture", "West Plaza Arcade"),
            L("06.set.crystal_tree_hall__p13", "Grand Crystal Tree Sanctuary Arch", "P4", 2.40, 0.52, 0.86, 0.46, "portal_inner_world", "City Center Sanctuary"),
            L("06.set.atlantis_plaza__p10", "East Terracotta Plaza Arcade", "P4", 2.44, 0.82, 0.86, 0.44, "portal_aperture", "East Plaza Colonnade"),
            L("06.props.lantern-candle-guitar__p15", "Central Plaza Sanctuary Signpost", "P3", 1.40, 0.34, 0.87, 0.26, "lamp_glow", None),
            L("06.props.coin-booth__p04", "Elder's Crystal Sanctuary Emblem", "P2", 1.04, 0.66, 0.88, 0.18, "sun_pulse", None),
            L("06.props.lantern-candle-guitar__p11", "Foreground Plaza Sanctuary Candle", "P1", 0.55, 0.14, 0.92, 0.18, "lamp_glow", None, False, 0.84),
            L("06.set.atlantis_plaza__p09", "Proscenium Terracotta Pilaster", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "06.5": {
        "backdrop": "world/cdca7326_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_L",
        "counterpart": {"key": "party_guest/guest", "x": 940, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.hero.house__p10", "High Overhead Night-Alley String Lights", "P6", 6.00, 0.50, 0.22, 0.16, "lamp_glow", None, False, 0.86),
            L("06.set.atlantis_plaza__p10", "Distant Illuminated Alleyway Arch", "P5", 3.78, 0.36, 0.82, 0.34, "portal_aperture", None, False, 0.90),
            L("06.set.narrow_streets__p01", "Cobblestone Lantern Wall West", "P4", 2.44, 0.20, 0.86, 0.48, "portal_aperture", "Narrow Cobblestone Street"),
            L("06.set.narrow_streets__p03", "Arched Night Street Passage East", "P4", 2.44, 0.82, 0.86, 0.48, "portal_aperture", "Musician's Corner"),
            L("06.props.lantern-candle-guitar__p11", "Flickering Brass Street Candle", "P3", 1.40, 0.46, 0.86, 0.24, "lamp_glow", "Flickering Candlelight"),
            L("06.props.lantern-candle-guitar__p14", "Warm Wooden Acoustic Guitar on Cobbles", "P2", 1.04, 0.62, 0.88, 0.22, "lamp_glow", "Busker's Acoustic Guitar"),
            L("06.props.lantern-candle-guitar__p11", "Foreground Cobblestone Votive Lantern", "P1", 0.54, 0.86, 0.93, 0.18, "lamp_glow", None, False, 0.84),
            L("06.set.narrow_streets__p01", "Proscenium Narrow Street Arch Jamb", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "06.6": {
        "backdrop": "world/ee11f371_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_grounded",
        "counterpart": None,
        "layers": [
            L("06.fx.comet__p01", "Quiet Evening Star Over Harbor Teahouse", "P6", 6.00, 0.26, 0.20, 0.14, "sun_pulse", None, False, 0.84),
            L("06.set.atlantis_waterfront.skyline__p10", "Distant Harbor Greenery & Arch", "P5", 3.80, 0.36, 0.82, 0.32, "portal_aperture", None, False, 0.90),
            L("06.hero.teahouse__p01", "Tiled Harbor Teahouse Pavilion", "P4", 2.44, 0.22, 0.85, 0.38, "lamp_glow", "Harbor Teahouse Veranda"),
            L("06.hero.house__p05", "Terracotta House Entry Door", "P4", 2.40, 0.52, 0.86, 0.44, "portal_aperture", "The House at Plaza Edge"),
            L("06.hero.house__p03", "Teal Shanty Facade & Window", "P4", 2.42, 0.80, 0.85, 0.34, "portal_aperture", "Sanctuary Window"),
            L("06.hero.house__p10", "Warm Overhead Festival String Lights", "P3", 1.48, 0.50, 0.34, 0.16, "lamp_glow", None),
            L("06.props.lantern-candle-guitar__p14", "Resting Teahouse Porch Guitar", "P2", 1.04, 0.66, 0.89, 0.20, "lamp_glow", None),
            L("06.props.lantern-candle-guitar__p11", "Foreground Teahouse Veranda Lantern", "P1", 0.55, 0.16, 0.92, 0.18, "lamp_glow", None, False, 0.84),
            L("06.set.narrow_streets__p03", "Proscenium Harbor Veranda Post", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },

    # =======================================================================
    # POEM 07 · DJ TURN ME UP — HANDMADE 7-LAYER WORLD STACKS
    # =======================================================================
    "07.0": {
        "backdrop": "world/b631fc80_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "club_groove",
        "counterpart": {"key": "dj_cyber/cyber", "x": 640, "dir": -1, "cue": "idle"},
        "layers": [
            L("07.props.projection__p10", "Club Ceiling Strobe & Vineyard Wash", "P6", 6.00, 0.50, 0.26, 0.24, "portal_other_world", None, False, 0.84),
            L("07.props.bar-handheld__p01", "Distant Illuminated Club Back-Bar", "P5", 3.80, 0.34, 0.78, 0.24, "lamp_glow", None, False, 0.90),
            L("07.hero.house__p04", "Corrugated Club Hall Acoustic Wall", "P4", 2.42, 0.68, 0.85, 0.36, "portal_aperture", None),
            L("07.props.speakers-vu__p01", "Tall Dual-Driver Bass Speaker Left", "P3", 1.46, 0.20, 0.87, 0.42, "speaker_pulse", "Left Bass Speaker Stack"),
            L("07.props.dj-decks__p03", "Wooden DJ Booth Front Counter", "P3", 1.42, 0.50, 0.88, 0.24, "dj_console", "DJ Turn Me Up Booth"),
            L("07.props.speakers-vu__p02", "Tall Dual-Driver Bass Speaker Right", "P3", 1.46, 0.80, 0.87, 0.42, "speaker_pulse", "Right Bass Speaker Stack"),
            L("07.props.dj-decks__p01", "Dual-Turntable DJ Mixer Console", "P2", 1.04, 0.50, 0.78, 0.22, "dj_console", "Live Turntable Mixer"),
            L("07.fx.party-haze__p01", "Foreground Sub-Bass Club Haze", "P1", 0.54, 0.50, 0.88, 0.18, "cloud_drift_L", None, False, 0.76),
            L("07.props.speakers-vu__p15", "Proscenium Left Speaker Cabinet Wing", "P0", 0.25, 0.04, 0.94, 0.34, "proscenium_mask", None, False, 0.85),
        ],
    },
    "07.1": {
        "backdrop": "world/22ddf809_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "party_guest/guest", "x": 960, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.hero.house__p10", "Overhead House-Party String Lights", "P6", 6.00, 0.50, 0.24, 0.16, "lamp_glow", None, False, 0.86),
            L("07.props.bar-handheld__p01", "Recessed Party Bar Bottle Rack", "P5", 3.78, 0.34, 0.78, 0.24, "lamp_glow", None, False, 0.90),
            L("07.hero.house__p05", "House Party Projection Wall & Picture Window", "P4", 2.42, 0.66, 0.84, 0.36, "portal_aperture", None),
            L("07.hero.house.furniture__p03", "House Party Lounge Sofa", "P3", 1.45, 0.20, 0.87, 0.28, "lamp_base", "House Party Lounge"),
            L("07.props.dj-decks__p02", "Spinning Turntable Platter Deck", "P3", 1.40, 0.78, 0.86, 0.28, "dj_console", "Turntable Platter Deck"),
            L("07.props.mic-daisy-rings__p01", "Chrome Vocal Microphone on Stand", "P2", 1.04, 0.50, 0.88, 0.34, "speaker_pulse", "Eyes Wide Shut at the Mic"),
            L("07.fx.party-haze__p01", "Warm Lounge Haze Across Floor", "P1", 0.54, 0.32, 0.90, 0.16, "cloud_drift_L", None, False, 0.74),
            L("07.hero.house__p09", "Proscenium Timber Stairwell Balustrade", "P0", 0.25, 0.96, 0.95, 0.34, "proscenium_mask", None, True, 0.85),
        ],
    },
    "07.2": {
        "backdrop": "world/a883ad75_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_question",
        "counterpart": {"key": "ex/ex_jacket", "x": 980, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("07.props.projection__p11", "High Projected Golden Rings Halo", "P6", 6.00, 0.50, 0.24, 0.22, "sun_pulse", None, False, 0.82),
            L("07.props.projection__p10", "Projected Sun-Soaked Vineyard Rows", "P5", 3.80, 0.52, 0.78, 0.34, "portal_other_world", "Sun-Soaked Vineyard Projection", False, 0.92),
            L("07.hero.house__p04", "Shadowed Club Acoustic Wall Panel", "P4", 2.42, 0.52, 0.85, 0.36, "portal_aperture", None),
            L("07.props.speakers-vu__p15", "Woven Speaker Mesh Grille Left", "P3", 1.44, 0.22, 0.86, 0.32, "speaker_pulse", "Ghosts in the Speaker Mesh"),
            L("07.props.speakers-vu__p16", "Woven Speaker Mesh Grille Right", "P3", 1.44, 0.80, 0.86, 0.32, "speaker_pulse", "Resonant Mesh Cabinet"),
            L("07.props.mic-daisy-rings__p09", "Memory Daisy Between the Speakers", "P2", 1.04, 0.62, 0.88, 0.22, "flower_bloom", None),
            L("07.fx.party-haze__p01", "Drifting Projector Beam Mist", "P1", 0.54, 0.48, 0.88, 0.16, "cloud_drift_L", None, False, 0.76),
            L("07.props.speakers-vu__p01", "Proscenium Bass Cabinet Frame", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "07.3": {
        "backdrop": "world/f59c59fe_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "arms_sky_high",
        "counterpart": {"key": "dj_cyber/cyber", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("06.fx.comet__p01", "Light-Year Strobe Burst Overhead", "P6", 6.00, 0.50, 0.20, 0.18, "sun_pulse", None, False, 0.86),
            L("07.props.projection__p13", "Deep-Space Highway Projection Screen", "P5", 3.80, 0.50, 0.76, 0.32, "portal_other_world", None, False, 0.90),
            L("07.props.speakers-vu__p01", "Left Sub-Bass Tower Wall", "P4", 2.42, 0.18, 0.86, 0.38, "speaker_pulse", None),
            L("07.props.speakers-vu__p02", "Right Sub-Bass Tower Wall", "P4", 2.42, 0.84, 0.86, 0.38, "speaker_pulse", None),
            L("07.props.speakers-vu__p12", "Glowing Analog VU Meter (-20..+3 dB)", "P3", 1.40, 0.24, 0.74, 0.16, "speaker_pulse", "VU Meter Into the Red"),
            L("07.props.speakers-vu__p17", "Framed Peak VU Meter Dial", "P3", 1.40, 0.78, 0.74, 0.18, "speaker_pulse", "Peak Decibel Dial"),
            L("07.props.dj-decks__p14", "Overdriven Twin-Platter DJ Deck", "P2", 1.04, 0.52, 0.87, 0.26, "dj_console", "A Thousand Light Years Deck"),
            L("07.fx.party-haze__p01", "Overdriven Bass Floor Vapor", "P1", 0.54, 0.52, 0.90, 0.18, "cloud_drift_L", None, False, 0.78),
            L("07.props.speakers-vu__p16", "Proscenium Right Speaker Grille Mask", "P0", 0.25, 0.96, 0.95, 0.34, "proscenium_mask", None, True, 0.85),
        ],
    },
    "07.4": {
        "backdrop": "world/51d1fea8_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_question",
        "counterpart": {"key": "ex/ex_jacket", "x": 980, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("07.props.projection__p11", "Diverging Golden Wedding Bands in Sky", "P6", 6.00, 0.26, 0.32, 0.28, "sun_pulse", "Diverging Wedding Bands", False, 0.88),
            L("07.props.projection__p12", "Projected Shared Home Boxed in Field", "P5", 3.80, 0.52, 0.78, 0.34, "portal_tv_flicker", "The Boxed Home Projection", False, 0.92),
            L("07.hero.house__p05", "Shadowed House Interior Projection Wall", "P4", 2.40, 0.80, 0.85, 0.38, "portal_aperture", "Threshold of the Room"),
            L("07.hero.house.furniture__p03", "Empty Shared Living-Room Sofa", "P3", 1.42, 0.22, 0.87, 0.26, "lamp_base", None),
            L("07.props.mic-daisy-rings__p09", "Dropped Daisy on the Carpet", "P2", 1.04, 0.62, 0.89, 0.22, "flower_bloom", None),
            L("07.fx.party-haze__p01", "Parting Memory Haze Across Threshold", "P1", 0.54, 0.48, 0.88, 0.16, "cloud_drift_L", None, False, 0.76),
            L("07.hero.house__p04", "Proscenium Corrugated Doorframe Jamb", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "07.5": {
        "backdrop": "world/79ea20ae_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "shrug_peace",
        "counterpart": None,
        "layers": [
            L("06.hero.house__p10", "Dimmed Late-Night Bar String Lights", "P6", 6.00, 0.50, 0.22, 0.16, "lamp_glow", None, False, 0.84),
            L("07.props.projection__p11", "Fading Ring Projection on Back Wall", "P5", 3.80, 0.50, 0.74, 0.26, "sun_pulse", None, False, 0.86),
            L("07.props.bar-handheld__p01", "Illuminated Club Bar Bottle Shelves", "P4", 2.44, 0.22, 0.78, 0.26, "lamp_glow", "Illuminated Club Bar"),
            L("07.hero.house__p09", "Wooden Exit Staircase", "P4", 2.40, 0.80, 0.86, 0.36, "fire_escape_landing", "Stairwell to the Street"),
            L("07.props.dj-decks__p03", "Silent Empty DJ Counter", "P3", 1.42, 0.34, 0.88, 0.22, "dj_console", None),
            L("07.props.mic-daisy-rings__p09", "Plucked Eleven-Year Daisy Stem", "P2", 1.04, 0.52, 0.87, 0.28, "flower_bloom", "Eleven Years in Daisy Petals"),
            L("07.fx.party-haze__p01", "Closing-Time Bar Smoke Drift", "P1", 0.54, 0.68, 0.88, 0.16, "cloud_drift_L", None, False, 0.76),
            L("07.hero.house__p04", "Proscenium Bar Exit Wall Jamb", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },
    "07.6": {
        "backdrop": "world/62b9740c_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "chin_high_stand",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Dim Moon Through Frontal Rain Fog", "P6", 6.00, 0.52, 0.22, 0.16, "sun_pulse", None, False, 0.80),
            L("07.props.projection__p13", "Three Diverging Roads Vista", "P5", 3.80, 0.24, 0.78, 0.34, "portal_other_world", "Three Roads in the Rain", False, 0.92),
            L("07.hero.house__p04", "Open Night Doorway to the Rain", "P4", 2.40, 0.80, 0.86, 0.42, "portal_aperture", "Walking Out Chin High"),
            L("07.hero.house__p09", "Wet Wooden Stoop Steps", "P3", 1.42, 0.22, 0.88, 0.28, "fire_escape_landing", None),
            L("07.props.mic-daisy-rings__p01", "Left-Behind Stage Mic Stand", "P2", 1.04, 0.64, 0.88, 0.28, "speaker_pulse", None),
            L("07.fx.party-haze__p01", "Drifting Streetlamp Fog Bank", "P1", 0.48, 0.52, 0.74, 0.20, "cloud_drift_L", "Frontal Fog & Dim Lights", False, 0.84),
            L("07.hero.house__p05", "Proscenium Rain-Slicked Door Frame", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },

    # =======================================================================
    # POEM 08 · NEWLY SINGLE — HANDMADE 7-LAYER WORLD STACKS
    # =======================================================================
    "08.0": {
        "backdrop": "world/959cd1f5_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "soul_rapture",
        "counterpart": {"key": "poet_soul/soul", "x": 620, "dir": 1, "cue": "kneel_2", "y_offset": -85},
        "layers": [
            L("08.props.moons-laundry__p01", "High Equator Moon Above Club Roof", "P6", 6.00, 0.78, 0.22, 0.18, "planet_orbit", None, False, 0.86),
            L("08.set.rooftop_club__p06", "Far Mountain Range Beyond Rooftop Club", "P5", 3.80, 0.50, 0.76, 0.18, "static", None, False, 0.90),
            L("08.hero.marquee__p01", "Glowing NEW SINGLE Theatre Stone Facade", "P4", 2.46, 0.24, 0.85, 0.38, "lamp_glow", "NEW SINGLE Club Marquee"),
            L("08.set.rooftop_club__p04", "Pulsing Rooftop Strobe Tower", "P4", 2.38, 0.52, 0.86, 0.42, "speaker_pulse", "Soul Leaves the Dancer"),
            L("08.props.basins__p01", "Rooftop Terrace Ice-Water Basin", "P3", 1.40, 0.82, 0.88, 0.22, "wave_mid", None),
            L("08.cast.angel.wings__p03", "Luminous Outspread Soul Wings", "P2", 1.04, 0.58, 0.64, 0.24, "wing_flap_L", None),
            L("08.fx.soul-weather__p01", "Ascending Luminous Soul Current", "P1", 0.46, 0.76, 0.58, 0.24, "sun_pulse", "Ascending Soul Vapor", False, 0.86),
            L("08.hero.marquee.interior__p01", "Proscenium Neon Marquee Pillar", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "08.1": {
        "backdrop": "world/e3c427ae_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "club_groove",
        "counterpart": {"key": "club_dress/club", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("08.fx.soul-weather__p01", "High Violet Ceiling Strobe Plume", "P6", 6.00, 0.50, 0.20, 0.18, "sun_pulse", None, False, 0.84),
            L("08.set.rooftop_club__p06", "Club Window Skyline Silhouette", "P5", 3.80, 0.50, 0.82, 0.18, "static", None, False, 0.88),
            L("08.hero.marquee.interior__p01", "Neon NEW SINGLE Stage Arch", "P4", 2.44, 0.22, 0.84, 0.40, "portal_aperture", "Strangers Collide on Floor"),
            L("08.hero.marquee.interior__p08", "Violet Club Colonnade Arch", "P4", 2.42, 0.80, 0.84, 0.40, "lamp_glow", "Midnight Dance Arches"),
            L("07.props.dj-decks__p01", "Late-Night Club DJ Console", "P3", 1.40, 0.52, 0.86, 0.24, "dj_console", "Last One to Leave"),
            L("08.props.basins__p01", "Chilled Club Lounge Basin", "P2", 1.04, 0.34, 0.88, 0.20, "wave_mid", None),
            L("08.fx.soul-weather__p05", "Foreground Dancefloor Dry-Ice Haze", "P1", 0.52, 0.64, 0.88, 0.18, "cloud_drift_L", None, False, 0.78),
            L("08.hero.marquee.interior__p08", "Proscenium Violet Arch Column", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },
    "08.2": {
        "backdrop": "world/cbb5e9c5_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "poet_soul/soul", "x": 720, "dir": -1, "cue": "kneel_2", "y_offset": -80},
        "layers": [
            L("08.props.moons-laundry__p01", "Closest Salted Moon Overhead", "P6", 6.00, 0.80, 0.26, 0.22, "planet_orbit", "Moons of the Equator", False, 0.90),
            L("08.set.atlantis_aerial__p01", "Aerial Mandala of Atlantis Below", "P5", 3.80, 0.22, 0.74, 0.34, "portal_other_world", "Aerial Atlantis Below", False, 0.92),
            L("08.hero.marquee__p01", "High Equator Wind-Tower Colonnade", "P4", 2.42, 0.82, 0.85, 0.34, "portal_aperture", None),
            L("08.props.moons-laundry__p25", "Equator Clothesline & Blowing Laundry", "P3", 1.42, 0.54, 0.74, 0.24, "curtain_sway_L", "Open Field at the Equator"),
            L("08.cast.angel.wings__p03", "Hovering Equator Angel Wing Crest", "P2", 1.04, 0.64, 0.64, 0.22, "wing_flap_L", None),
            L("08.fx.soul-weather__p01", "Foreground Salted Moon-Wind Stream", "P1", 0.52, 0.24, 0.76, 0.20, "sun_pulse", None, False, 0.80),
            L("08.set.rooftop_club__p04", "Proscenium Equator Beacon Frame", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.84),
        ],
    },
    "08.3": {
        "backdrop": "world/f56df2d8_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "kneel_universe",
        "counterpart": {"key": "angel/robe", "x": 880, "dir": -1, "cue": "idle"},
        "layers": [
            L("08.props.moons-laundry__p01", "Sanctuary Moon Above Baptism Font", "P6", 6.00, 0.50, 0.20, 0.18, "planet_orbit", None, False, 0.86),
            L("08.set.atlantis_aerial__p01", "Distant Luminous Mandala Horizon", "P5", 3.80, 0.50, 0.76, 0.28, "portal_other_world", None, False, 0.88),
            L("08.hero.marquee__p01", "Marble Sanctuary Baptism Colonnade", "P4", 2.42, 0.20, 0.85, 0.36, "portal_aperture", None),
            L("08.props.basins__p01", "West Marble Ice-Water Basin", "P3", 1.42, 0.24, 0.87, 0.24, "wave_mid", "Salted Ice-Water Basin"),
            L("08.props.basins__p05", "Central Baptism Font of Ice Water", "P3", 1.38, 0.50, 0.88, 0.26, "wave_near", "Angels' Ice-Water Baptism"),
            L("08.cast.angel.wings__p03", "Feathered Angel Sanctuary Wings", "P2", 1.04, 0.78, 0.72, 0.28, "wing_flap_L", "Choir of Night Angels"),
            L("08.fx.soul-weather__p01", "Rising Ice-Water Baptism Mist", "P1", 0.52, 0.50, 0.84, 0.20, "sun_pulse", None, False, 0.82),
            L("08.hero.marquee.interior__p01", "Proscenium Sanctuary Wing Arch", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },
    "08.4": {
        "backdrop": "world/cf180ca2_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Pale Dawn Disc Over Rooftop Terrace", "P6", 6.00, 0.78, 0.22, 0.16, "sun_pulse", None, False, 0.84),
            L("08.set.rooftop_club__p06", "Quiet Dawn Skyline & Radio Masts", "P5", 3.80, 0.50, 0.84, 0.16, "static", None, False, 0.90),
            L("08.hero.marquee__p01", "Quiet Dawn Rooftop Colonnade", "P4", 2.42, 0.52, 0.85, 0.36, "portal_aperture", "Soul Returns to the Body"),
            L("08.props.basins__p06", "Still Terrace Basin at Dawn", "P3", 1.42, 0.80, 0.87, 0.22, "wave_mid", "Terrace Recovery Basin"),
            L("08.props.basins__p01", "Clear Morning Water Font", "P2", 1.04, 0.34, 0.88, 0.20, "wave_near", None),
            L("08.fx.soul-weather__p05", "Parting Smoke & Haze Cloud", "P1", 0.48, 0.22, 0.68, 0.22, "cloud_drift_L", "Breathing in the Smoke", False, 0.84),
            L("08.set.rooftop_club__p04", "Proscenium Rooftop Parapet Column", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "08.5": {
        "backdrop": "world/0240b488_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "back_horizon",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Morning Sun Over the Peaks", "P6", 6.00, 0.80, 0.26, 0.20, "sun_pulse", "Wandering Eyes at Dawn", False, 0.90),
            L("10.set.mountain_road__p04", "Unfamiliar Mountains in the Distance", "P5", 3.80, 0.52, 0.84, 0.18, "water_backing", "Mountains From the Rooftop", False, 0.92),
            L("08.set.rooftop_club__p06", "Rooftop Skyline & Radio Towers", "P4", 2.54, 0.50, 0.86, 0.16, "static", None),
            L("08.set.rooftop_club__p04", "West Rooftop Beacon Tower", "P4", 2.40, 0.20, 0.86, 0.40, "portal_aperture", "Rooftop Parapet"),
            L("08.props.basins__p06", "Dawn Terrace Parapet Basin", "P3", 1.40, 0.78, 0.88, 0.20, "wave_mid", None),
            L("08.props.moons-laundry__p25", "Fluttering Morning Breeze Line", "P2", 1.04, 0.36, 0.78, 0.18, "curtain_sway_L", None),
            L("08.fx.soul-weather__p05", "Morning Mist Clearing the Parapet", "P1", 0.52, 0.64, 0.86, 0.16, "cloud_drift_L", None, False, 0.78),
            L("08.hero.marquee__p01", "Proscenium East Terrace Pilaster", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },

    # =======================================================================
    # POEM 09 · YET, HEARD — HANDMADE 7-LAYER WORLD STACKS
    # =======================================================================
    "09.0": {
        "backdrop": "world/b05d5b9a_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "ex/ex_jacket", "x": 920, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("09.props.moon-sun__p01", "Shared Full Moon Overhead", "P6", 6.00, 0.80, 0.26, 0.20, "sun_pulse", "Under the Shared Moon", False, 0.90),
            L("09.set.atlantis_harbor_street__p08", "Distant Harbor Crane & Quayside", "P5", 3.80, 0.76, 0.82, 0.34, "portal_aperture", None, False, 0.90),
            L("09.hero.canopy__p08", "Illuminated Neon Club Facade", "P4", 2.44, 0.22, 0.85, 0.44, "lamp_glow", "Outside the Club Canopy"),
            L("09.set.atlantis_club_sidewalk__p04", "Double-Globe Harbor Streetlamp", "P4", 2.40, 0.52, 0.86, 0.44, "lamp_glow", "The EX in the Crowd"),
            L("09.props.suitcases-notice__p19", "Club Sidewalk Iron Gate Signpost", "P3", 1.40, 0.36, 0.87, 0.28, "lamp_glow", None),
            L("09.props.suitcases-notice__p04", "Resting Curbside Leather Valise", "P2", 1.04, 0.66, 0.89, 0.18, "drawer_slide", None),
            L("09.fx.call-abyss__p19", "Foreground Sidewalk Night Mist", "P1", 0.52, 0.82, 0.88, 0.16, "cloud_drift_L", None, False, 0.78),
            L("09.set.atlantis_club_sidewalk__p05", "Proscenium Iron Streetlamp Post", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "09.1": {
        "backdrop": "world/abac8bce_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_L",
        "counterpart": {"key": "ex/ex_jacket", "x": 880, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Moon Settling Over the Water", "P6", 6.00, 0.78, 0.26, 0.22, "sun_pulse", "Moonlight on the Harbor", False, 0.90),
            L("09.set.atlantis_harbor_street__p08", "Distant Harbor Crane Silhouette", "P5", 3.80, 0.54, 0.85, 0.42, "portal_aperture", "Walking Toward the Moon", False, 0.92),
            L("09.set.atlantis_club_sidewalk__p03", "Curved Iron Harbor Bridge Railing", "P4", 2.52, 0.50, 0.87, 0.20, "static", None),
            L("09.set.atlantis_club_sidewalk__p05", "Harbor Quay Streetlamp West", "P4", 2.42, 0.22, 0.86, 0.44, "lamp_glow", "Harbor Quay Promenade"),
            L("13.props.planet-boats__p18", "Moored Harbor Skiff on the Quay", "P3", 1.40, 0.76, 0.87, 0.24, "boat_rock", None),
            L("09.props.suitcases-notice__p04", "Traveler's Suitcase by the Railing", "P2", 1.04, 0.38, 0.89, 0.18, "drawer_slide", None),
            L("09.fx.call-abyss__p19", "Low Harbor Water Vapor", "P1", 0.52, 0.52, 0.90, 0.16, "cloud_drift_L", None, False, 0.78),
            L("09.set.atlantis_club_sidewalk__p04", "Proscenium Harbor Quay Lamp Wing", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "09.2": {
        "backdrop": "world/bf0a66ea_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "shrug_peace",
        "counterpart": {"key": "ex/ex_jacket", "x": 880, "dir": -1, "cue": "suitcase"},
        "layers": [
            L("09.props.moon-sun__p01", "High Harbor Moon Over the Pier", "P6", 6.00, 0.78, 0.22, 0.18, "sun_pulse", None, False, 0.86),
            L("09.set.atlantis_harbor_street__p08", "Distant Pier Crane & Ship Mast", "P5", 3.80, 0.34, 0.84, 0.36, "portal_aperture", None, False, 0.90),
            L("09.set.atlantis_club_sidewalk__p05", "Pier Curbside Lantern Post", "P4", 2.42, 0.18, 0.86, 0.42, "lamp_glow", None),
            L("09.props.phonebooth__p14", "3D Glass Harbor Phone Booth", "P3", 1.44, 0.52, 0.87, 0.42, "booth_frame", "The Harbor Phone Booth"),
            L("09.props.suitcases-notice__p19", "2nd Gate (01/12/14) Iron Signpost", "P3", 1.38, 0.80, 0.86, 0.36, "lamp_glow", "2nd Gate Notice Sign"),
            L("09.props.suitcases-notice__p04", "Packed Brown Leather Suitcase on Curb", "P2", 1.04, 0.28, 0.89, 0.20, "drawer_slide", "Suitcases on the Curb"),
            L("09.fx.call-abyss__p01", "Faint Ringing Echo from the Booth", "P1", 0.52, 0.52, 0.62, 0.14, "phone_ring", None, False, 0.80),
            L("09.set.atlantis_club_sidewalk__p04", "Proscenium Pier Lantern Post", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "09.3": {
        "backdrop": "world/018da7e9_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "mother/poem09", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Shared Moon Spanning the Abyss", "P6", 6.00, 0.50, 0.20, 0.16, "sun_pulse", None, False, 0.86),
            L("09.set.mother_living_room__p01", "Mother's Living Room Back Wall & Window Opening", "P5", 3.80, 0.76, 0.78, 0.32, "portal_aperture", None, False, 0.90),
            L("09.set.mother_living_room__p02", "Mother's Framed Living Room Window", "P4", 2.46, 0.76, 0.66, 0.26, "lamp_glow", "Mother's Living Room"),
            L("09.props.phonebooth__p15", "Open Harbor Phone Booth & Handset", "P3", 1.44, 0.22, 0.87, 0.42, "booth_frame", "Calling From the Booth"),
            L("09.props.phones-chair__p07", "Mother's Floral Armchair", "P2", 1.04, 0.78, 0.88, 0.28, "lamp_base", "Mother's Armchair"),
            L("09.fx.call-abyss__p01", "Voice Waveform Across the Abyss", "P1", 0.48, 0.50, 0.56, 0.16, "phone_ring", "Speaking Across the Abyss", False, 0.88),
            L("09.set.mother_living_room__p06", "Proscenium Living-Room Corner Wall", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "09.4": {
        "backdrop": "world/b036e49b_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "father_elder/poem09", "x": 860, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Late Moon Over Inner Harbor", "P6", 6.00, 0.76, 0.22, 0.18, "sun_pulse", None, False, 0.88),
            L("09.set.atlantis_harbor_street__p05", "Distant Inner-Harbor Shed & Shipway", "P5", 3.80, 0.36, 0.80, 0.20, "portal_aperture", None, False, 0.90),
            L("09.set.atlantis_club_sidewalk__p06", "Warm Inner-Harbor Timber Shopfront", "P4", 2.44, 0.20, 0.85, 0.38, "portal_aperture", "Inner Harbor Watchhouse"),
            L("09.set.atlantis_club_sidewalk__p04", "East Quay Lantern Post", "P4", 2.40, 0.50, 0.86, 0.44, "lamp_glow", "Father & Son Harbor Walk"),
            L("13.props.planet-boats__p18", "Moored Wooden Harbor Sailboat", "P3", 1.42, 0.78, 0.86, 0.28, "boat_rock", "Inner Harbor Mooring"),
            L("09.props.suitcases-notice__p05", "Father's Weathered Harbor Valise", "P2", 1.04, 0.64, 0.89, 0.18, "drawer_slide", None),
            L("09.fx.call-abyss__p19", "Drifting Inner-Harbor Sea Mist", "P1", 0.52, 0.48, 0.90, 0.16, "cloud_drift_L", None, False, 0.78),
            L("09.set.atlantis_club_sidewalk__p05", "Proscenium East Quay Bollard & Lamp", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "09.5": {
        "backdrop": "world/18a6390f_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "shrug_peace",
        "counterpart": {"key": "ex/ex_jacket", "x": 960, "dir": 1, "cue": "walk_away"},
        "layers": [
            L("09.props.moon-sun__p01", "Fading Moon in Pre-Dawn Mist", "P6", 6.00, 0.78, 0.24, 0.18, "sun_pulse", None, False, 0.84),
            L("09.set.atlantis_harbor_street__p08", "Misty Distant Harbor Crane", "P5", 3.80, 0.36, 0.84, 0.36, "portal_aperture", None, False, 0.88),
            L("09.set.atlantis_club_sidewalk__p05", "Misty Quay Streetlamp", "P4", 2.42, 0.22, 0.86, 0.44, "lamp_glow", "Misty Harbor Quay"),
            L("09.props.phonebooth__p14", "Silent Glass Booth in the Fog", "P3", 1.42, 0.66, 0.87, 0.36, "booth_frame", None),
            L("09.props.suitcases-notice__p05", "Single Suitcase Left on the Pier", "P2", 1.04, 0.48, 0.89, 0.20, "drawer_slide", "Yet Broken, Yet Heard"),
            L("09.fx.call-abyss__p19", "Parting Mist as the EX Dissolves", "P1", 0.46, 0.78, 0.68, 0.22, "cloud_drift_L", "The EX Turns to Haze", False, 0.86),
            L("09.set.atlantis_harbor_street__p10", "Proscenium Quay Town Lamp Post", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },


    # =======================================================================
    # POEM 10 · MAGIC RIDE — HANDMADE 7-LAYER WORLD STACKS
    # =======================================================================
    "10.0": {
        "backdrop": "world/6edb9f7b_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_grounded",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Midnight Moon Over Atlantis Curbside", "P6", 6.00, 0.78, 0.24, 0.18, "sun_pulse", None, False, 0.88),
            L("10.set.atlantis_streets__p06", "Glowing Midnight Atlantis Skyline", "P5", 3.80, 0.80, 0.86, 0.28, "portal_aperture", "Midnight Curbside", False, 0.92),
            L("10.set.atlantis_streets__p07", "Tall Wrought-Iron Streetlamp West", "P4", 2.44, 0.22, 0.86, 0.44, "lamp_glow", "Under the Streetlamp"),
            L("11.props.parked-motorcycle__p01", "Parked Cafe Racer Motorcycle", "P3", 1.38, 0.52, 0.87, 0.32, "bike_chassis", "The Parked Motorcycle"),
            L("10.props.tree-dawn-sign__p02", "Curbside Route Marker Post", "P2", 1.04, 0.36, 0.88, 0.22, "lamp_glow", None),
            L("10.fx.ride-light__p22", "Warm Curbside Lamp Pool", "P1", 0.52, 0.22, 0.90, 0.14, "headlight_beam", None, False, 0.78),
            L("10.set.atlantis_streets__p08", "Proscenium East Street Tower Frame", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "10.1": {
        "backdrop": "world/18cff588_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "magic_ride_bike",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Sodium Night Moon Above Alleyway", "P6", 6.00, 0.76, 0.22, 0.18, "sun_pulse", None, False, 0.86),
            L("10.set.atlantis_streets__p06", "Distant Alleyway Industrial Skyline", "P5", 3.80, 0.64, 0.86, 0.26, "portal_aperture", None, False, 0.90),
            L("10.set.atlantis_streets__p07", "Alleyway Streetlamp & Smokestack", "P4", 2.44, 0.20, 0.86, 0.44, "lamp_glow", "Steel Coverings & Ignition"),
            L("11.props.parked-motorcycle__p01", "Ignited Cafe Racer Motorcycle", "P3", 1.38, 0.50, 0.87, 0.34, "bike_chassis", "Mounting the Machine"),
            L("10.props.bike-skeleton__p17", "Roaring Twin-Cylinder Engine Frame", "P2", 1.04, 0.50, 0.88, 0.28, "bike_chassis", None, False, 0.42),
            L("10.fx.ride-light__p22", "Ignited Golden Headlight Beam", "P1", 0.45, 0.78, 0.76, 0.14, "headlight_beam", "Headlight Cutting the Dark", False, 0.88),
            L("10.set.atlantis_streets__p07", "Proscenium Alleyway Iron Lamp Post", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "10.2": {
        "backdrop": "world/31ca5420_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "magic_ride_bike",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "High Midnight Moon Over Intersection", "P6", 6.00, 0.50, 0.20, 0.16, "sun_pulse", None, False, 0.86),
            L("10.set.atlantis_streets__p06", "Distant Intersection Viaduct Skyline", "P5", 3.80, 0.50, 0.86, 0.26, "portal_aperture", None, False, 0.90),
            L("10.set.atlantis_streets__p07", "West Midnight Intersection Tower", "P4", 2.44, 0.20, 0.86, 0.44, "portal_aperture", "First Midnight Intersection"),
            L("10.set.atlantis_streets__p08", "East Intersection Street Tower", "P4", 2.44, 0.80, 0.86, 0.42, "lamp_glow", "Wide-Eyed Intersection"),
            L("10.props.bike-skeleton__p17", "Cruising Cafe Motorcycle in Stride", "P3", 1.38, 0.50, 0.87, 0.32, "bike_chassis", "Loneliness at Speed"),
            L("10.hero.shadowpool__p02", "Amber Asphalt Reflection Pool", "P2", 1.04, 0.50, 0.92, 0.24, "lamp_glow", None, False, 0.76),
            L("10.fx.ride-light__p23", "Foreground Sodium Motion Streak", "P1", 0.48, 0.76, 0.74, 0.14, "headlight_beam", None, False, 0.84),
            L("10.set.atlantis_streets__p08", "Proscenium Intersection Signal Post", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "10.3": {
        "backdrop": "world/3a0da51b_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "magic_ride_bike",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Amber Moon Above the Avenue", "P6", 6.00, 0.78, 0.22, 0.18, "sun_pulse", None, False, 0.86),
            L("10.set.atlantis_streets__p06", "Distant Avenue Skyline Silhouette", "P5", 3.80, 0.50, 0.86, 0.24, "portal_aperture", None, False, 0.90),
            L("10.hero.shadowpool__p02", "Amber Avenue Light Pool", "P4", 2.46, 0.22, 0.87, 0.40, "lamp_glow", "Avenue Light Pool"),
            L("10.set.atlantis_streets__p08", "East Avenue Lamp & Arch", "P4", 2.42, 0.82, 0.86, 0.40, "lamp_glow", None),
            L("11.props.parked-motorcycle__p01", "Cafe Racer Leaning Through the Avenue", "P3", 1.38, 0.52, 0.87, 0.34, "bike_chassis", "Swagger Down the Avenue"),
            L("10.fx.ride-light__p22", "Forward Golden Headlight Cone", "P2", 1.04, 0.72, 0.82, 0.14, "headlight_beam", None),
            L("10.fx.ride-light__p23", "Streaming Sodium Tail-Light Streak", "P1", 0.46, 0.80, 0.68, 0.14, "headlight_beam", "Noise Blocking the Noise", False, 0.88),
            L("10.set.atlantis_streets__p07", "Proscenium Avenue Streetlamp Wing", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "10.4": {
        "backdrop": "world/3c0e1673_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "point_horizon",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Settling Horizon Moon & Dawn Glow", "P6", 6.00, 0.78, 0.28, 0.22, "sun_pulse", "Where the Moon Settles", False, 0.90),
            L("10.set.mountain_road__p04", "Distant Mountain Ridge Beyond Atlantis", "P5", 3.80, 0.54, 0.84, 0.18, "water_backing", None, False, 0.90),
            L("05.set.winged_marble_gate__p01", "Outer Boundary Pillar of Atlantis", "P4", 2.46, 0.20, 0.86, 0.48, "portal_aperture", "Leaving Atlantis Behind"),
            L("10.props.bike-skeleton__p17", "Highway Motorcycle Heading Out", "P3", 1.38, 0.50, 0.87, 0.32, "bike_chassis", "Out of Atlantis"),
            L("10.props.tree-dawn-sign__p02", "Highway Boundary Milepost", "P2", 1.04, 0.76, 0.88, 0.22, "lamp_glow", None),
            L("10.fx.ride-light__p22", "Highway Headlight Cutting Pre-Dawn Mist", "P1", 0.50, 0.68, 0.82, 0.14, "headlight_beam", None, False, 0.84),
            L("05.set.winged_marble_gate__p05", "Proscenium Outer Gate Pillar", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "10.5": {
        "backdrop": "world/ea91d4c4_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "welcome_new_day",
        "counterpart": None,
        "layers": [
            L("11.fx.light__p01", "First Amber Dawn Cresting the Ridge", "P6", 6.00, 0.52, 0.24, 0.20, "sun_pulse", None, False, 0.90),
            L("10.set.mountain_road__p04", "Far Mountain Range at Daybreak (Back Ridge)", "P5", 3.80, 0.48, 0.76, 0.18, "water_backing", None, False, 0.90),
            L("10.set.mountain_road__p05", "Near Darker Mountain Ridge (Front Layer)", "P4", 2.44, 0.48, 0.82, 0.18, "fire_escape_landing", "Mountain Road Switchback"),
            L("10.props.tree-dawn-sign__p01", "Solitary Crest Tree at First Light", "P4", 2.38, 0.78, 0.86, 0.48, "flower_bloom", "First Light on the Ridge"),
            L("11.props.parked-motorcycle__p01", "Idling Motorcycle on the Overlook", "P3", 1.40, 0.30, 0.88, 0.28, "bike_chassis", None),
            L("10.props.tree-dawn-sign__p02", "88 NEW DAWN km Roadside Signpost", "P2", 1.04, 0.52, 0.87, 0.30, "lamp_glow", "88 NEW DAWN km Sign"),
            L("10.set.mountain_road__p09", "Foreground Left Rocky Highway Shoulder", "P1", 0.52, 0.14, 0.94, 0.22, "static", None, False, 0.86),
            L("10.props.tree-dawn-sign__p01", "Proscenium Ridge Pine Bough", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },

    # =======================================================================
    # POEM 11 · NEW DAY — HANDMADE 7-LAYER WORLD STACKS
    # (Note exact scene keys: 11.0, 11.3, 11.1, 11.2, 11.4, 11.5!)
    # =======================================================================
    "11.0": {
        "backdrop": "world/d3d25411_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_grounded",
        "counterpart": None,
        "layers": [
            L("11.fx.light__p01", "Pale Dawn Glow Through Sea Mist", "P6", 6.00, 0.78, 0.24, 0.18, "sun_pulse", None, False, 0.84),
            L("11.set.temple_infinity_pool__p05", "Distant Sea Horizon & Colonnade", "P5", 3.80, 0.50, 0.84, 0.14, "static", None, False, 0.88),
            L("11.props.ruin__p02", "Weathered Shore Ruin Archway", "P4", 2.42, 0.52, 0.86, 0.40, "portal_aperture", "Arrival on the Chilly Shore"),
            L("11.hero.clocktower__p01", "Distant Shore Sanctuary Bell Tower", "P4", 2.46, 0.80, 0.86, 0.52, "portal_aperture", "Misty Shore Bell Tower"),
            L("11.props.parked-motorcycle__p01", "Parked Motorcycle on Chilly Shore", "P3", 1.40, 0.22, 0.87, 0.30, "bike_chassis", "Parked Bike by the Sea"),
            L("11.props.journal__p11", "Traveler's Closed Shore Journal", "P2", 1.04, 0.36, 0.89, 0.18, "lamp_glow", None),
            L("11.props.inlays-lantern__p15", "Foreground Hanging Shore Sanctuary Lantern", "P1", 0.54, 0.14, 0.46, 0.24, "lamp_glow", None, False, 0.84),
            L("11.props.ruin__p03", "Proscenium Weathered Shore Ruin Pillar", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "11.3": {
        "backdrop": "world/6b70f5b3_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": None,
        "layers": [
            L("11.fx.light__p01", "Radiant Sanctuary Ocular Sunbeam", "P6", 6.00, 0.50, 0.22, 0.20, "sun_pulse", None, False, 0.88),
            L("11.set.temple_infinity_pool__p05", "Distant White Sanctuary Colonnade", "P5", 3.80, 0.50, 0.84, 0.14, "static", None, False, 0.90),
            L("11.props.temple.states__p06", "Completed White Marble Temple Nave", "P4", 2.44, 0.22, 0.86, 0.46, "portal_aperture", "New White Temple Nave"),
            L("11.hero.clocktower__p01", "White Sanctuary Clocktower", "P4", 2.46, 0.80, 0.86, 0.54, "portal_aperture", "Sanctuary Clocktower"),
            L("11.props.inlays-lantern__p15", "Hanging Brass Sanctuary Lantern", "P3", 1.38, 0.52, 0.58, 0.32, "lamp_glow", "Choir Chords in the Nave"),
            L("11.props.journal__p11", "Hymnal & Journal on Marble Lectern", "P2", 1.04, 0.64, 0.88, 0.20, "lamp_glow", None),
            L("11.props.inlays-lantern__p15", "Foreground Sanctuary Nave Censer Lamp", "P1", 0.54, 0.86, 0.44, 0.24, "lamp_glow", None, False, 0.84),
            L("11.set.mirror_hall__p14", "Proscenium Fluted Nave Marble Column", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "11.1": {
        "backdrop": "world/08fe12af_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_question",
        "counterpart": None,
        "layers": [
            L("11.fx.light__p01", "Morning Sun Breaking Above the Sea", "P6", 6.00, 0.78, 0.26, 0.22, "sun_pulse", "Morning Sunlight", False, 0.92),
            L("11.set.temple_infinity_pool__p05", "Sunlit Sea Horizon & Far Columns", "P5", 3.80, 0.50, 0.84, 0.14, "static", None, False, 0.90),
            L("11.props.ruin__p03", "Sunlit Ruined Stone Arch", "P4", 2.44, 0.22, 0.86, 0.38, "portal_aperture", "Remnants in the Sunlight"),
            L("11.props.temple.states__p01", "White Marble Plinth & First Courses", "P3", 1.40, 0.52, 0.86, 0.40, "drawer_slide", "First Courses of Stone"),
            L("11.props.temple.states__p03", "Carved Cornerstone Course on Focal Ground", "P2", 1.04, 0.76, 0.89, 0.18, "drawer_slide", None),
            L("11.props.inlays-lantern__p15", "Foreground Morning Sanctuary Lantern", "P1", 0.54, 0.14, 0.46, 0.22, "lamp_glow", None, False, 0.82),
            L("11.props.ruin__p02", "Proscenium Sunlit Stone Ruin Jamb", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "11.2": {
        "backdrop": "world/58cbb4ca_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "arms_sky_high",
        "counterpart": None,
        "layers": [
            L("11.fx.light__p01", "Zenith Sun Crowning the White Roof", "P6", 6.00, 0.50, 0.22, 0.20, "sun_pulse", None, False, 0.90),
            L("11.set.temple_infinity_pool__p05", "Far Reflecting Colonnade Horizon", "P5", 3.80, 0.50, 0.84, 0.14, "static", None, False, 0.90),
            L("11.props.temple.states__p01", "Rising Fluted Marble Columns", "P4", 2.40, 0.50, 0.86, 0.38, "portal_aperture", "The Temple Builds Itself"),
            L("11.props.temple.states__p04", "Crowned White Temple & Pediment", "P4", 2.38, 0.80, 0.86, 0.46, "sun_pulse", "Crowning the White Roof"),
            L("11.props.temple.states__p03", "White Marble Stepped Plinth", "P3", 1.42, 0.20, 0.87, 0.18, "portal_aperture", "Rising Fluted Columns"),
            L("11.props.inlays-lantern__p15", "Golden Temple Dedication Lantern", "P2", 1.04, 0.36, 0.58, 0.26, "lamp_glow", None),
            L("11.fx.light__p01", "Foreground Sunburst Ray Across Plinth", "P1", 0.52, 0.84, 0.32, 0.18, "sun_pulse", None, False, 0.78),
            L("11.set.mirror_hall__p14", "Proscenium White Marble Pilaster", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "11.4": {
        "backdrop": "world/fc83bfee_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": None,
        "layers": [
            L("11.fx.light__p01", "Clear Skylight Glow Above Mirror Hall", "P6", 6.00, 0.50, 0.20, 0.18, "sun_pulse", None, False, 0.88),
            L("11.set.temple_infinity_pool__p05", "Reflected Horizon Colonnade in Glass", "P5", 3.80, 0.50, 0.84, 0.14, "static", None, False, 0.88),
            L("02.set.bedroom_night__p03", "Sanctuary Standing Mirror Glass", "P4", 2.44, 0.22, 0.85, 0.44, "portal_other_world", None),
            L("02.set.bedroom_night__p02", "Tall Standing Sanctuary Mirror", "P4", 2.42, 0.22, 0.86, 0.46, "portal_aperture", "The Lonely Mirror"),
            L("11.set.mirror_hall__p14", "Reflecting Pool Marble Column", "P4", 2.40, 0.80, 0.86, 0.38, "wave_far", "Infinity Pool Colonnade"),
            L("11.hero.pools__p04", "Still Marble Reflecting Basin Steps", "P3", 1.42, 0.66, 0.88, 0.26, "wave_mid", None),
            L("11.props.journal__p11", "Open Two-Page Leather Journal", "P2", 1.04, 0.52, 0.85, 0.24, "lamp_glow", "Open Journal of Clarity"),
            L("11.props.inlays-lantern__p15", "Foreground Mirror-Hall Brass Lantern", "P1", 0.54, 0.86, 0.44, 0.22, "lamp_glow", None, False, 0.84),
            L("11.set.mirror_hall__p14", "Proscenium West Mirror-Hall Column", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "11.5": {
        "backdrop": "world/5bd8dc26_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "welcome_new_day",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Golden Dawn Sun at the Zenith", "P6", 6.00, 0.78, 0.26, 0.22, "sun_pulse", "Welcoming the New Day", False, 0.92),
            L("11.set.temple_infinity_pool__p05", "Reflecting White Colonnade Across Sea", "P5", 3.80, 0.50, 0.85, 0.14, "static", None, False, 0.90),
            L("11.props.temple.whole__p20", "Gleaming White Temple by the Sea", "P4", 2.42, 0.52, 0.86, 0.46, "portal_aperture", "Walking on Calm Water"),
            L("11.hero.pools__p04", "Calm Reflecting Pool Steps", "P3", 1.40, 0.22, 0.87, 0.34, "wave_mid", "Reflecting Pool Steps"),
            L("11.props.journal__p11", "Completed Journal on the Water Steps", "P2", 1.04, 0.36, 0.89, 0.18, "lamp_glow", None),
            L("11.fx.light__p01", "Foreground Shimmering Dawn Water Glint", "P1", 0.52, 0.82, 0.90, 0.18, "sun_pulse", None, False, 0.80),
            L("11.set.mirror_hall__p14", "Proscenium Infinity-Pool Marble Column", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },

    # =======================================================================
    # POEM 12 · REUNION — HANDMADE 7-LAYER WORLD STACKS
    # =======================================================================
    "12.0": {
        "backdrop": "world/58cbb4ca_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "brother_1/poem12", "x": 880, "dir": -1, "cue": "idle"},
        "layers": [
            L("11.fx.light__p01", "Warm Afternoon Sun Above Temple Porch", "P6", 6.00, 0.78, 0.22, 0.18, "sun_pulse", None, False, 0.88),
            L("12.set.temple_grove__p06", "Distant Sanctuary Pine Grove Horizon", "P5", 3.80, 0.50, 0.80, 0.28, "curtain_sway_R", None, False, 0.88),
            L("12.props.niche-porch__p01", "Arched White Temple Sanctuary Porch", "P4", 2.44, 0.22, 0.86, 0.46, "portal_aperture", "Temple Porch Entrance"),
            L("12.set.temple_hall__p04", "Fluted White Temple Hall Column", "P4", 2.42, 0.80, 0.86, 0.42, "portal_aperture", "Hall of Reunion"),
            L("12.props.niche-porch__p15", "Hanging Brass Sanctuary Dome Lamp", "P3", 1.44, 0.52, 0.46, 0.24, "lamp_glow", "Welcome Home in the Hall"),
            L("12.props.snapshot__p02", "Framed Brotherhood Welcome Portrait", "P2", 1.04, 0.64, 0.87, 0.22, "heart_beat", None),
            L("12.props.niche-porch__p15", "Foreground Porch Welcome Lantern", "P1", 0.54, 0.14, 0.42, 0.20, "lamp_glow", None, False, 0.84),
            L("12.set.temple_hall__p04", "Proscenium Fluted Porch Column", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "12.1": {
        "backdrop": "world/08fe12af_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "friend_1/poem12", "x": 880, "dir": -1, "cue": "idle"},
        "layers": [
            L("12.props.niche-porch__p15", "High Vaulted Sanctuary Dome Chandelier", "P6", 6.00, 0.50, 0.24, 0.18, "lamp_glow", None, False, 0.86),
            L("12.props.niche-porch__p01", "Far Sanctuary Hall Arched Alcove", "P5", 3.80, 0.50, 0.82, 0.36, "portal_aperture", None, False, 0.90),
            L("12.set.temple_hall__p04", "West Echoing Marble Column", "P4", 2.44, 0.22, 0.86, 0.42, "portal_aperture", "Echoing Hall Columns"),
            L("12.set.temple_backroom__p06", "Carved Wooden Gathering Chair", "P3", 1.42, 0.78, 0.87, 0.30, "lamp_base", "Gathering Circle"),
            L("04.props.heart__p01", "Overheard Beating Heart in Chorus", "P2", 1.04, 0.52, 0.76, 0.22, "heart_beat", "Overheard Hearts"),
            L("12.props.hand-hourglass__p05", "Foreground Sanctuary Sand Glass", "P1", 0.54, 0.16, 0.92, 0.20, "hourglass_sand", None, False, 0.84),
            L("12.set.temple_hall__p04", "Proscenium East Hall Column", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "12.2": {
        "backdrop": "world/f05c1fa5_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "still_sentinel",
        "counterpart": None,
        "layers": [
            L("12.set.temple_backroom__p09", "Sagging Overhead Backroom Bulb Wire", "P6", 6.00, 0.50, 0.22, 0.16, "lamp_glow", None, False, 0.86),
            L("12.set.temple_backroom__p03", "Warm Doorway Light Insert Beyond Threshold", "P5", 3.86, 0.36, 0.80, 0.34, "lamp_glow", None, False, 0.90),
            L("12.set.temple_backroom__p02", "Upper Stone Staircase Flight in Shadow", "P5", 3.80, 0.52, 0.82, 0.36, "portal_inner_world", "Empty Rooms of Afterlife", False, 0.92),
            L("12.set.temple_backroom__p01", "Stone Backroom Wall & Open Doorway Aperture", "P4", 2.44, 0.32, 0.84, 0.38, "portal_aperture", "Afterlife Chamber Door"),
            L("12.props.niche-porch__p01", "Arched Stone Sanctuary Niche", "P4", 2.42, 0.80, 0.86, 0.44, "lamp_glow", "Silent Wall Niche"),
            L("12.set.temple_backroom__p06", "Silent Empty Chamber Chair", "P3", 1.40, 0.36, 0.88, 0.26, "lamp_base", None),
            L("12.props.hand-hourglass__p05", "Still Hourglass in the Niche", "P2", 1.04, 0.66, 0.87, 0.22, "hourglass_sand", None),
            L("12.props.niche-porch__p15", "Foreground Chamber Votive Pendant", "P1", 0.54, 0.16, 0.44, 0.20, "lamp_glow", None, False, 0.82),
            L("12.set.temple_hall__p04", "Proscenium Stone Chamber Pilaster", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "12.3": {
        "backdrop": "world/3603f621_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "vow_hand_raised",
        "counterpart": {"key": "brother_1/poem12", "x": 900, "dir": -1, "cue": "idle"},
        "layers": [
            L("12.props.niche-porch__p15", "Amber Sanctuary Vault Lamp", "P6", 6.00, 0.50, 0.22, 0.18, "lamp_glow", None, False, 0.86),
            L("12.props.niche-porch__p01", "Distant Sanctuary Reliquary Arch", "P5", 3.80, 0.50, 0.84, 0.36, "portal_aperture", None, False, 0.90),
            L("12.set.temple_hall__p04", "Sanctuary Reliquary Marble Column", "P4", 2.42, 0.16, 0.86, 0.40, "portal_aperture", None),
            L("12.props.hand-hourglass__p05", "Glass Hourglass of Burning Sand", "P3", 1.38, 0.26, 0.84, 0.30, "hourglass_sand", "Glasses of Burning Sand"),
            L("12.props.last-hourglass__p23", "Burning Wooden Hourglass Frame", "P3", 1.36, 0.50, 0.86, 0.34, "hourglass_sand", "The Burning Hourglasses"),
            L("12.props.snapshot__p01", "Framed Archival Group Photograph", "P2", 1.04, 0.78, 0.84, 0.32, "portal_tv_flicker", "The Archival Group Photo"),
            L("12.props.hand-hourglass__p05", "Foreground Glowing Sand Vessel", "P1", 0.54, 0.88, 0.93, 0.18, "hourglass_sand", None, False, 0.82),
            L("12.set.temple_hall__p04", "Proscenium Reliquary Column Wing", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "12.4": {
        "backdrop": "world/22fcebea_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "elders/memory", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Filtered Sun Through Grove Canopy", "P6", 6.00, 0.50, 0.20, 0.18, "sun_pulse", None, False, 0.86),
            L("12.set.temple_grove__p06", "Sanctuary Grove Canopy East", "P5", 3.80, 0.80, 0.78, 0.34, "curtain_sway_R", "Shared Years in the Wind", False, 0.92),
            L("12.set.temple_grove__p08", "Ancient Sanctuary Grove Tree West", "P4", 2.44, 0.22, 0.78, 0.34, "flower_bloom", "Western Forest Edge"),
            L("12.set.temple_grove__p05", "Tall Living Grove Pine Trunk", "P4", 2.40, 0.52, 0.86, 0.44, "curtain_sway_L", "Every Living Tree"),
            L("12.set.temple_backroom__p06", "Elder's Carved Grove Bench", "P3", 1.40, 0.36, 0.88, 0.26, "lamp_base", None),
            L("12.props.snapshot__p01", "Shared-Years Memory Frame in the Grove", "P2", 1.04, 0.66, 0.87, 0.24, "heart_beat", None),
            L("13.props.harvest__p01", "Foreground Forest-Floor Blossoms", "P1", 0.54, 0.16, 0.94, 0.18, "flower_bloom", None, False, 0.84),
            L("12.set.temple_grove__p05", "Proscenium Ancient Pine Trunk", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "12.5": {
        "backdrop": "world/ef9f6c7e_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "brother_1/poem12", "x": 820, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Golden Dusk Sun Over Shore Terrace", "P6", 6.00, 0.50, 0.22, 0.18, "sun_pulse", None, False, 0.88),
            L("11.set.temple_infinity_pool__p05", "Distant Shore Terrace Sea Horizon", "P5", 3.80, 0.50, 0.84, 0.14, "static", None, False, 0.90),
            L("12.set.temple_shore_terrace__p10", "Billowing Shore Terrace Canopy West", "P4", 2.42, 0.22, 0.84, 0.42, "curtain_sway_L", "Shore Terrace Canopy"),
            L("12.set.temple_shore_terrace__p11", "Billowing Shore Terrace Canopy East", "P4", 2.42, 0.80, 0.84, 0.42, "curtain_sway_R", "Overheard Hearts Terrace"),
            L("12.set.temple_backroom__p06", "Terrace Gathering Seat", "P3", 1.40, 0.34, 0.88, 0.26, "lamp_base", None),
            L("12.props.snapshot__p02", "Brotherhood Arm-in-Arm Portrait", "P2", 1.04, 0.52, 0.83, 0.34, "heart_beat", "The Brotherhood Chain"),
            L("04.props.heart__p01", "Foreground Resonant Terrace Heart Emblem", "P1", 0.54, 0.86, 0.90, 0.16, "heart_beat", None, False, 0.82),
            L("12.set.temple_hall__p04", "Proscenium Shore Terrace Column", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "12.6": {
        "backdrop": "world/bdc7d6ec_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "lunge_catch",
        "counterpart": {"key": "friend_1/poem12", "x": 900, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Amber Dusk Sun Over the Meadow", "P6", 6.00, 0.50, 0.24, 0.18, "sun_pulse", None, False, 0.88),
            L("12.set.temple_grove__p06", "Distant Meadow Tree Line", "P5", 3.80, 0.48, 0.80, 0.28, "curtain_sway_R", None, False, 0.90),
            L("12.set.temple_grove__p08", "Meadow Sanctuary Tree West", "P4", 2.46, 0.22, 0.80, 0.32, "flower_bloom", "Football in the Meadow"),
            L("12.props.niche-porch__p01", "Illuminated Temple Home Porch", "P4", 2.40, 0.80, 0.86, 0.46, "portal_aperture", "Recollections Bring Us Home"),
            L("12.props.niche-porch__p15", "Glowing Porch Welcome Lamp", "P3", 1.42, 0.78, 0.48, 0.20, "lamp_glow", None),
            L("12.props.reunion__p01", "Spiraling Leather Football", "P2", 1.04, 0.50, 0.62, 0.16, "tambourine_arc", "Spiraling Pass at Dusk"),
            L("13.props.harvest__p01", "Foreground Meadow Dusk Wildflowers", "P1", 0.54, 0.16, 0.94, 0.18, "flower_bloom", None, False, 0.84),
            L("12.set.temple_grove__p05", "Proscenium Meadow Pine Frame", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },

    # =======================================================================
    # POEM 13 · HOW TO WIN MY HEART — HANDMADE 7-LAYER WORLD STACKS
    # (Note exact scene keys: 13.1, 13.0, 13.2..13.6!)
    # =======================================================================
    "13.1": {
        "backdrop": "world/932cb5b5_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "corner_cafe_cup",
        "counterpart": {"key": "woman/poem13", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("13.props.planet-boats__p01", "Morning Planet & Harbor Sky", "P6", 6.00, 0.50, 0.20, 0.16, "planet_orbit", None, False, 0.84),
            L("13.props.distant-window__p13", "Distant Upper-Story Harbor Window", "P5", 3.80, 0.52, 0.66, 0.24, "portal_aperture", None, False, 0.88),
            L("13.props.rail-tide-awning__p08", "Blue-and-White Striped Cafe Awning", "P4", 2.46, 0.24, 0.44, 0.20, "curtain_sway_L", "Harbor Cafe Awning"),
            L("13.hero.cafe__p01", "Teal Harbor Cafe Storefront Windows", "P4", 2.44, 0.78, 0.86, 0.42, "portal_aperture", "Harbor of the Heavens Cafe"),
            L("13.props.cafe__p13", "Corner Marble Bistro Table & Chairs", "P3", 1.40, 0.48, 0.88, 0.26, "coffee_steam", "The Corner Cafe Table"),
            L("13.props.cafe__p07", "Steaming Porcelain Espresso Cup", "P2", 1.04, 0.46, 0.69, 0.09, "coffee_steam", "Steaming Espresso Cup"),
            L("13.props.cafe__p03", "Foreground Sidewalk Bistro Chair", "P1", 0.54, 0.14, 0.93, 0.24, "cafe_chair", None, False, 0.84),
            L("13.hero.atrium__p03", "Proscenium Harbor Promenade Tree", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "13.0": {
        "backdrop": "world/06881630_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "woman/poem13", "x": 940, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Bright Harbor Morning Sun", "P6", 6.00, 0.78, 0.22, 0.18, "sun_pulse", None, False, 0.88),
            L("11.props.temple.whole__p20", "White Temple on the Point", "P5", 3.80, 0.20, 0.84, 0.42, "portal_aperture", "Leaving the White Temple", False, 0.92),
            L("13.hero.atrium__p01", "Arched Harbor Promenade Colonnade", "P4", 2.40, 0.52, 0.86, 0.36, "fire_escape_landing", "Walk Around the Harbor"),
            L("13.props.planet-boats__p18", "Wooden Sailboat on the Harbor Tide", "P3", 1.42, 0.80, 0.86, 0.26, "boat_rock", "Harbor Sailboat Mooring"),
            L("13.props.harvest__p04", "Fresh Harbor Poppy Bouquet", "P2", 1.04, 0.36, 0.89, 0.20, "flower_bloom", None),
            L("13.props.harvest__p01", "Foreground Quayside Blossoms", "P1", 0.54, 0.14, 0.94, 0.18, "flower_bloom", None, False, 0.84),
            L("13.hero.atrium__p03", "Proscenium Harbor Promenade Arch", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },
    "13.2": {
        "backdrop": "world/7df17df5_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "elder_woman/poem13", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("13.props.planet-boats__p01", "Banded Planet Jupiter & Orbits", "P6", 6.00, 0.22, 0.26, 0.22, "planet_orbit", "Counted Planetary Orbits", False, 0.90),
            L("13.props.planet-boats__p19", "Distant Tall-Masted Dreaming Sailboat", "P5", 3.80, 0.82, 0.82, 0.28, "boat_rock", "Younger Selves Dreaming", False, 0.92),
            L("13.set.church_pews__p02", "Gothic Stained-Glass Sanctuary Window", "P4", 2.46, 0.52, 0.76, 0.38, "portal_aperture", None),
            L("13.set.church_pews__p03", "Carved Wooden Pews of Praying Elders", "P3", 1.44, 0.52, 0.88, 0.20, "lamp_glow", "Praying Elders in the Pews"),
            L("13.props.five-letters__p02", "Kept Prayer-Book Letter in the Pew", "P2", 1.04, 0.34, 0.87, 0.16, "lamp_glow", None),
            L("13.props.harvest__p01", "Foreground Sanctuary Altar Blossoms", "P1", 0.54, 0.16, 0.94, 0.18, "flower_bloom", None, False, 0.84),
            L("13.set.church_pews__p02", "Proscenium Stained-Glass Lancet Frame", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "13.3": {
        "backdrop": "world/590a0c02_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_question",
        "counterpart": None,
        "layers": [
            L("13.props.planet-boats__p01", "Turning Season Sphere in High Vault", "P6", 6.00, 0.78, 0.22, 0.18, "planet_orbit", None, False, 0.86),
            L("13.props.distant-window__p13", "High Arched Atrium Memory Window", "P5", 3.80, 0.52, 0.68, 0.24, "portal_aperture", None, False, 0.88),
            L("13.hero.atrium__p01", "Half-Submerged Stone Atrium Arches", "P4", 2.44, 0.24, 0.86, 0.38, "wave_far", "Drowned Atrium of Seasons"),
            L("13.props.harvest__p10", "Wildflower Bouquet of Old Stories", "P3", 1.38, 0.78, 0.87, 0.26, "flower_bloom", "Fire of Burned Stories"),
            L("13.props.five-letters__p02", "Scorched Unsent Love Letter", "P2", 1.04, 0.54, 0.78, 0.18, "tambourine_arc", "Five Burned Love Letters"),
            L("13.props.harvest__p01", "Foreground Floating Poppy Petals", "P1", 0.54, 0.16, 0.94, 0.18, "flower_bloom", None, False, 0.84),
            L("13.hero.atrium__p03", "Proscenium Submerged Stone Column", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },
    "13.4": {
        "backdrop": "world/2ce9173b_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "kneel_universe",
        "counterpart": {"key": "woman/poem13", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Warm Hilltop Sun Over Poppy Ridge", "P6", 6.00, 0.50, 0.20, 0.18, "sun_pulse", None, False, 0.88),
            L("11.props.temple.whole__p20", "Distant White Temple Beyond the Meadow", "P5", 3.80, 0.50, 0.80, 0.30, "portal_aperture", None, False, 0.88),
            L("13.hero.atrium__p03", "Sunlit Hilltop Meadow Tree", "P4", 2.42, 0.18, 0.85, 0.36, "flower_bloom", None),
            L("13.props.harvest__p01", "Scarlet Poppies & White Blossoms West", "P3", 1.40, 0.26, 0.87, 0.28, "flower_bloom", "Scarlet Poppy Meadow"),
            L("13.props.harvest__p05", "Blossoming Hilltop Poppies East", "P3", 1.40, 0.80, 0.87, 0.28, "flower_bloom", "Purple Blossoms Ridge"),
            L("13.props.harvest__p04", "Harvested Bouquet of Scarlet Poppies", "P2", 1.04, 0.52, 0.87, 0.28, "flower_bloom", "Harvesting the Poppies"),
            L("13.props.harvest__p10", "Foreground Wildflower Ridge Cluster", "P1", 0.54, 0.88, 0.94, 0.20, "flower_bloom", None, False, 0.86),
            L("12.set.temple_grove__p08", "Proscenium Meadow Bough Frame", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },
    "13.5": {
        "backdrop": "world/7fae27c3_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "arms_sky_high",
        "counterpart": {"key": "woman/poem13", "x": 900, "dir": -1, "cue": "idle"},
        "layers": [
            L("13.props.planet-boats__p01", "Evening Star Above the Cafe Window", "P6", 6.00, 0.24, 0.20, 0.16, "planet_orbit", None, False, 0.86),
            L("13.props.distant-window__p13", "Arched Brick Distant Window & Silhouette", "P5", 3.80, 0.52, 0.72, 0.32, "portal_aperture", "From a Distant Window", False, 0.92),
            L("13.hero.cafe__p04", "Harbor Cafe Window & Greenery", "P4", 2.40, 0.80, 0.85, 0.38, "lamp_glow", "Hope Tells Me You'll See Me"),
            L("13.props.cafe__p03", "Empty Bentwood Bistro Chair", "P3", 1.42, 0.22, 0.88, 0.34, "cafe_chair", "Waiting by the Cafe Chair"),
            L("13.props.harvest__p04", "Poppy Bouquet Placed on the Cafe Table", "P2", 1.04, 0.38, 0.88, 0.20, "flower_bloom", None),
            L("13.props.cafe__p07", "Foreground Warm Porcelain Cup", "P1", 0.54, 0.14, 0.92, 0.10, "coffee_steam", None, False, 0.86),
            L("13.hero.cafe__p01", "Proscenium Teal Cafe Mullion", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },
    "13.6": {
        "backdrop": "world/18a6390f_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": {"key": "woman/poem13", "x": 860, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Golden Dusk Sun Over Harbor Horizon", "P6", 6.00, 0.78, 0.24, 0.18, "sun_pulse", None, False, 0.88),
            L("13.props.planet-boats__p19", "Distant Tall-Masted Ship on the Bay", "P5", 3.80, 0.68, 0.82, 0.24, "boat_rock", None, False, 0.90),
            L("13.hero.atrium__p03", "Sunlit Harbor Atrium Tree", "P4", 2.40, 0.52, 0.86, 0.38, "portal_aperture", "Walks the Harbor Promenade"),
            L("13.props.cafe__p14", "Bistro Table & Espresso Cup Left Behind", "P3", 1.42, 0.22, 0.88, 0.24, "coffee_steam", "Rising From the Cafe Table"),
            L("13.props.planet-boats__p18", "Wooden Harbor Sailboat at Dusk", "P2", 1.04, 0.80, 0.87, 0.26, "boat_rock", "Harbor Horizon at Dusk"),
            L("13.props.harvest__p01", "Foreground Promenade Dusk Blossoms", "P1", 0.54, 0.14, 0.94, 0.18, "flower_bloom", None, False, 0.84),
            L("13.hero.atrium__p01", "Proscenium Promenade Stone Arch", "P0", 0.25, 0.04, 0.95, 0.36, "proscenium_mask", None, False, 0.85),
        ],
    },

    # =======================================================================
    # POEM 14 · HOT MINUTE — HANDMADE 7-LAYER WORLD STACKS
    # =======================================================================
    "14.0": {
        "backdrop": "world/ba11d121_3/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Luminous Horizon Moon Over Atlantis", "P6", 6.00, 0.52, 0.24, 0.20, "sun_pulse", "Taken by the Haze", False, 0.90),
            L("14.set.harbor_atlantis_wide__p09", "Panoramic Harbor Bridge & City Lights", "P5", 3.80, 0.50, 0.86, 0.16, "static", None, False, 0.92),
            L("14.set.harbor_atlantis_wide__p04", "Crystal Island of Atlantis", "P4", 2.44, 0.78, 0.85, 0.34, "portal_aperture", "Light-Filled Constellations"),
            L("14.set.harbor_atlantis_wide__p06", "Harbor Trawler Boat on the Bay", "P3", 1.44, 0.22, 0.86, 0.26, "boat_rock", "Everything I Built"),
            L("14.props.reel__p05", "Glimmering Key of Answers Above the Bay", "P2", 1.04, 0.38, 0.78, 0.18, "sun_pulse", None),
            L("14.props.party__p19", "Foreground Harbor Pier Festoon Lights", "P1", 0.54, 0.16, 0.30, 0.18, "lamp_glow", None, False, 0.84),
            L("14.props.door__p11", "Proscenium Threshold Door Frame", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "14.1": {
        "backdrop": "world/3da7e92e_3/backdrop.webp",
        "floor": 616,
        "initial_cue": "soul_rapture",
        "counterpart": None,
        "layers": [
            L("14.props.reel__p02", "Distant Spiral Galaxy in the Void", "P6", 6.00, 0.50, 0.22, 0.20, "planet_orbit", None, False, 0.86),
            L("14.fx.filmframe__p01", "Suspended 35mm Void Aperture", "P5", 3.80, 0.52, 0.74, 0.32, "portal_tv_flicker", None, False, 0.86),
            L("14.props.door__p02", "Closed Freestanding Vintage Door", "P4", 2.44, 0.80, 0.86, 0.48, "portal_aperture", "Distant Door in the Void"),
            L("14.props.reel__p06", "Candle Flame Memory Shard in Void", "P3", 1.40, 0.22, 0.72, 0.24, "lamp_glow", "Floating in the Black"),
            L("14.props.reel__p05", "Starburst Key of Answers", "P2", 1.04, 0.52, 0.64, 0.24, "sun_pulse", "Sharpened Key of Answers"),
            L("14.props.reel__p06", "Foreground Floating Candle Ember", "P1", 0.52, 0.14, 0.86, 0.16, "lamp_glow", None, False, 0.82),
            L("02.set.black_void__p01", "Proscenium Void Shadow Wing", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "14.2": {
        "backdrop": "world/c1eadbdf_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": {"key": "family/street_clothes", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Warm Memory Sun Above the Reel", "P6", 6.00, 0.50, 0.20, 0.16, "sun_pulse", None, False, 0.86),
            L("14.set.harbor_atlantis_wide__p09", "Distant Life-Horizon City Lights", "P5", 3.80, 0.50, 0.84, 0.16, "static", None, False, 0.88),
            L("14.fx.filmframe__p01", "Archival 35mm Life-Reel Proscenium", "P4", 2.44, 0.52, 0.78, 0.36, "portal_tv_flicker", None),
            L("14.props.reel__p02", "Memory Frame · Spiral Galaxy", "P3", 1.40, 0.22, 0.76, 0.26, "planet_orbit", "Highs of Life Memory"),
            L("14.props.reel__p07", "Memory Frame · Temple Under Stars", "P3", 1.38, 0.52, 0.76, 0.26, "portal_tv_flicker", "Cross-Cut of Life"),
            L("14.props.reel__p03", "Memory Frame · Scarlet Poppy", "P2", 1.04, 0.80, 0.76, 0.26, "flower_bloom", "Love & Loss Endured"),
            L("14.props.reel__p05", "Foreground Golden Key of Memory", "P1", 0.54, 0.14, 0.90, 0.16, "sun_pulse", None, False, 0.84),
            L("14.props.door__p11", "Proscenium Memory Threshold Jamb", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "14.3": {
        "backdrop": "world/8519865f_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "chin_high_stand",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Silver Projector Beam Orb in Zenith", "P6", 6.00, 0.50, 0.20, 0.16, "sun_pulse", None, False, 0.84),
            L("14.set.harbor_atlantis_wide__p09", "Distant Graytone Horizon Bridge", "P5", 3.80, 0.50, 0.84, 0.16, "static", None, False, 0.88),
            L("14.fx.filmframe__p01", "Perforated 35mm Graytone Film Frame", "P4", 2.44, 0.22, 0.78, 0.36, "portal_tv_flicker", "Graytone Film Aperture"),
            L("14.props.reel__p01", "Memory Frame · Golden Poppy Field", "P3", 1.38, 0.52, 0.78, 0.26, "portal_tv_flicker", "Battle Scars & Wisdom"),
            L("14.props.reel__p04", "Memory Frame · Open Journal Pages", "P2", 1.04, 0.80, 0.78, 0.26, "lamp_glow", "Unspooling the Reel"),
            L("14.props.reel__p06", "Foreground Projector Candle Flicker", "P1", 0.54, 0.88, 0.90, 0.16, "lamp_glow", None, False, 0.82),
            L("14.fx.filmframe__p01", "Proscenium 35mm Sprocket Mask", "P0", 0.25, 0.96, 0.95, 0.36, "proscenium_mask", None, True, 0.85),
        ],
    },
    "14.4": {
        "backdrop": "world/5bd8dc26_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_R",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Radiant Threshold Sun Beyond the Door", "P6", 6.00, 0.80, 0.24, 0.18, "sun_pulse", None, False, 0.90),
            L("11.set.temple_infinity_pool__p05", "Reflecting Horizon Pool Beyond Door", "P5", 3.80, 0.50, 0.85, 0.14, "static", None, False, 0.90),
            L("14.props.door__p11", "Freestanding Vintage Door Ajar", "P4", 2.42, 0.22, 0.86, 0.44, "portal_aperture", "The Vintage Door Appears"),
            L("14.props.door__p12", "Vintage Door Cracking Open With Light", "P4", 2.40, 0.52, 0.86, 0.46, "portal_aperture", "Light Beyond the Door"),
            L("14.props.door__p13", "Vintage Door Wide Open to Ballroom", "P3", 1.40, 0.80, 0.86, 0.46, "portal_other_world", "Stepping Through the Threshold"),
            L("14.props.reel__p05", "Key of Answers Turning in the Lock", "P2", 1.04, 0.64, 0.78, 0.18, "sun_pulse", None),
            L("14.props.party__p19", "Warm Ballroom Glow Spilling Forward", "P1", 0.54, 0.84, 0.34, 0.18, "lamp_glow", None, False, 0.84),
            L("14.props.door__p02", "Proscenium Vintage Door Architrave", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
    "14.5": {
        "backdrop": "world/cb6cbbfc_1/backdrop.webp",
        "floor": 612,
        "initial_cue": "waltz",
        "counterpart": {"key": "vintage_woman/gown", "x": 760, "dir": -1, "cue": "waltz"},
        "layers": [
            L("14.set.vintage_party__p01", "1940s Ballroom Coffered Ceiling Panel", "P6", 6.04, 0.50, 0.22, 0.20, "static", None, False, 0.92),
            L("01.props.chandeliers__p10", "Grand Crystal Ballroom Chandelier", "P6", 6.00, 0.50, 0.28, 0.22, "chandelier_sway", None, False, 0.92),
            L("14.set.vintage_party__p02", "1940s Wood-Panelled Ballroom Back Wall", "P5", 3.80, 0.50, 0.78, 0.36, "static", None, False, 0.92),
            L("14.set.vintage_party__p04", "Gleaming Hardwood Ballroom Dance Floor", "P4", 2.44, 0.50, 0.92, 0.22, "static", None),
            L("14.set.vintage_party__p03", "1940s Grand Ballroom Archway", "P4", 2.40, 0.52, 0.86, 0.50, "portal_other_world", "The Dance at the Vintage Party"),
            L("14.props.party__p19", "Warm Ballroom Festoon String Lights", "P3", 1.48, 0.50, 0.32, 0.22, "lamp_glow", "Under the Ballroom Lights"),
            L("14.props.party__p01", "Draped Ballroom Refreshment Table", "P3", 1.42, 0.24, 0.88, 0.26, "lamp_glow", None),
            L("14.props.party__p20", "Brass Horn Table Gramophone", "P2", 1.04, 0.80, 0.87, 0.28, "turntable_spin", "Gramophone Waltz"),
            L("14.props.party__p19", "Foreground Festoon Bulb Canopy", "P1", 0.54, 0.78, 0.26, 0.18, "lamp_glow", None, False, 0.84),
            L("14.set.vintage_party__p03", "Proscenium Ballroom Pilaster", "P0", 0.25, 0.96, 0.95, 0.38, "proscenium_mask", None, True, 0.85),
        ],
    },
    "14.6": {
        "backdrop": "world/9572112a_1/backdrop.webp",
        "floor": 612,
        "initial_cue": "idle_grounded",
        "counterpart": {"key": "vintage_man/suit", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("04.fx.moon-reach__p01", "Quiet Pre-Dawn Moon Returning to Genesis", "P6", 6.00, 0.80, 0.22, 0.18, "sun_pulse", None, False, 0.88),
            L("14.set.vintage_party__p02", "Receding 1940s Ballroom Panelled Wall", "P5", 3.80, 0.34, 0.80, 0.34, "static", None, False, 0.90),
            L("14.props.door__p02", "Closing Panelled Vintage Door", "P4", 2.40, 0.52, 0.86, 0.50, "portal_aperture", "The Vintage Door Closes"),
            L("01.props.window__p01", "Quiet Bedroom Sash Window at Dawn", "P4", 2.44, 0.80, 0.85, 0.48, "portal_aperture", "Genesis · Back to Poem 01"),
            L("14.props.party__p01", "Draped Ballroom Champagne Table", "P3", 1.44, 0.22, 0.88, 0.30, "lamp_glow", "Into the Ballroom Crowd"),
            L("01.props.room__p18", "Genesis Bedroom Television & Stand", "P2", 1.04, 0.66, 0.89, 0.22, "portal_tv_flicker", None),
            L("01.fx.haze-words__p08", "Drifting Genesis Morning Breath Plume", "P1", 0.54, 0.84, 0.90, 0.16, "cloud_drift_L", None, False, 0.80),
            L("14.props.door__p11", "Proscenium Closing Threshold Jamb", "P0", 0.25, 0.04, 0.95, 0.38, "proscenium_mask", None, False, 0.85),
        ],
    },
}


# ---------------------------------------------------------------------------
# Canonical 7-Layer Worldbuilding Spec (`P6` Sky -> `P0` Proscenium Mask)
# Matches `shots/cartoon.py` and `shots/multiplane.py`
# ---------------------------------------------------------------------------
SEVEN_PLANES: Dict[str, Dict[str, Any]] = {
    "P6": {
        "depth_index": 1,
        "name": "P6 · Sky & Celestial Atmosphere",
        "short": "SKY",
        "z": 6.00,
        "parallax": 0.08,
        "color_code": "#78c3dc",
        "rgb": (120, 195, 220),
        "ink_weight": 0.5,
        "haze_mix": 0.40,
        "pal_k": 2,
    },
    "P5": {
        "depth_index": 2,
        "name": "P5 · Distant World Vista",
        "short": "VISTA",
        "z": 3.80,
        "parallax": 0.22,
        "color_code": "#6ea0e1",
        "rgb": (110, 160, 225),
        "ink_weight": 1.2,
        "haze_mix": 0.28,
        "pal_k": 2,
    },
    "P4": {
        "depth_index": 3,
        "name": "P4 · Midground Architecture",
        "short": "ARCH",
        "z": 2.40,
        "parallax": 0.48,
        "color_code": "#2d69d2",
        "rgb": (45, 105, 210),
        "ink_weight": 1.8,
        "haze_mix": 0.16,
        "pal_k": 3,
    },
    "P3": {
        "depth_index": 4,
        "name": "P3 · Set Furnishings & Props",
        "short": "PROPS",
        "z": 1.40,
        "parallax": 0.78,
        "color_code": "#eb8c1e",
        "rgb": (235, 140, 30),
        "ink_weight": 2.4,
        "haze_mix": 0.06,
        "pal_k": 3,
    },
    "P2": {
        "depth_index": 5,
        "name": "P2 · Hero & Focal Cast Action",
        "short": "HERO",
        "z": 1.00,
        "parallax": 1.00,
        "color_code": "#cd282d",
        "rgb": (205, 40, 45),
        "ink_weight": 3.8,
        "haze_mix": 0.00,
        "pal_k": 4,
    },
    "P1": {
        "depth_index": 6,
        "name": "P1 · Fast Foreground & Light Beams",
        "short": "FG FX",
        "z": 0.55,
        "parallax": 1.38,
        "color_code": "#c49a6c",
        "rgb": (196, 154, 108),
        "ink_weight": 3.0,
        "haze_mix": 0.04,
        "pal_k": 3,
    },
    "P0": {
        "depth_index": 7,
        "name": "P0 · Proscenium Camera Mask",
        "short": "MASK",
        "z": 0.25,
        "parallax": 1.85,
        "color_code": "#9aa0ab",
        "rgb": (154, 160, 171),
        "ink_weight": 4.2,
        "haze_mix": 0.10,
        "pal_k": 3,
    },
}


def compute_piece_stage_dims(
    pw: int,
    ph: int,
    sc: float,
    plane: str,
    W: int = 1280,
    H: int = 720,
) -> Tuple[int, int]:
    """
    Aspect-Aware Span Scaling Law (shared 1:1 with `shots/play/levels.html`):
      - Preserves 100% native aspect ratio (`target_w / target_h == pw / ph`, zero distortion).
      - For wide architectural/sky/floor cutouts (`ar = pw / ph > 2.2`) whose pure height-based
        width (`H * sc * ar`) would exceed `85%` of the stage width, smoothly damps width into
        `[0.85 * W .. 1.04 * W]` and derives `target_h = round(target_w / ar)`.
      - For ultra-wide distant horizon/sky strips (`plane in ('P6', 'P5') and ar > 4.5`) given
        small `sc`, ensures they span at least `68%` of stage width.
    """
    ar = float(pw) / float(max(1, ph))
    target_h = max(24, min(int(H * 0.78), int(round(H * sc))))
    target_w = max(24, int(round(target_h * ar)))

    if ar > 2.2 and target_w > int(W * 0.85):
        span_cap = int(W * 0.85)
        damped_w = int(round(span_cap + (target_w - span_cap) * 0.18))
        target_w = min(int(W * 1.04), damped_w)
        target_h = max(18, int(round(target_w / ar)))
    elif plane in ("P6", "P5") and ar > 4.5 and target_w < int(W * 0.68):
        target_w = int(W * 0.68)
        target_h = max(18, int(round(target_w / ar)))

    return target_w, target_h


def load_frame_perspective_signals(fid: str) -> Dict[str, Any]:
    """
    Reads 3D perspective & atmosphere signals (`horizon`, `vp`, `haze_rgb`, `scale_ladder`)
    from `shots/out/<fid>/cartoon/signals.json` if available.
    """
    default_sig = {
        "horizon_norm": [[0.0, 0.56], [1.0, 0.56]],
        "vp_norm": [0.50, 0.56],
        "haze_rgb": [24, 30, 44],
        "stage_haze_rgb": [24, 30, 44],
        "scale_ladder": {},
    }
    if not fid:
        return default_sig
    sig_path = SHOTS_DIR / "out" / fid / "cartoon" / "signals.json"
    if not sig_path.exists():
        return default_sig
    try:
        d = json.loads(sig_path.read_text())
        raw_h = d.get("horizon") or [[0.0, 456.0], [1456.0, 456.0]]
        raw_vp = d.get("vp") or [728.0, 456.0]
        raw_haze = d.get("haze_rgb") or [24, 30, 44]
        # Blend 48% frame haze with 52% nocturnal gouache stage tone so bright frames stay cohesive
        sh_r = int(round(raw_haze[0] * 0.48 + 24 * 0.52))
        sh_g = int(round(raw_haze[1] * 0.48 + 30 * 0.52))
        sh_b = int(round(raw_haze[2] * 0.48 + 44 * 0.52))
        return {
            "horizon_norm": [
                [round(float(raw_h[0][0]) / 1456.0, 4), round(float(raw_h[0][1]) / 816.0, 4)],
                [round(float(raw_h[1][0]) / 1456.0, 4), round(float(raw_h[1][1]) / 816.0, 4)],
            ],
            "vp_norm": [
                round(max(-0.5, min(1.5, float(raw_vp[0]) / 1456.0)), 4),
                round(max(0.10, min(0.92, float(raw_vp[1]) / 816.0)), 4),
            ],
            "haze_rgb": [int(raw_haze[0]), int(raw_haze[1]), int(raw_haze[2])],
            "stage_haze_rgb": [sh_r, sh_g, sh_b],
            "scale_ladder": d.get("scale_ladder") or {},
        }
    except Exception:
        return default_sig


def verify_handmade_seven_layers_for_scene(skey: str, base_layers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Strictly verifies that every single scene (`01.0`..`14.6`) explicitly defines
    its own handmade 7-layer stack (`P6`, `P5`, `P4`, `P3`, `P2`, `P1`, `P0`)
    with zero generic fallback.
    """
    required = {"P6", "P5", "P4", "P3", "P2", "P1", "P0"}
    present = {lyr["plane"] for lyr in base_layers}
    missing = required - present
    if missing:
        raise RuntimeError(
            f"Scene {skey} is missing handmade planes {sorted(missing)}! "
            f"Every scene must explicitly author all 7 planes (P6..P0)."
        )
    return [dict(lyr) for lyr in base_layers]


def compute_frame_seven_layer_breakdown(
    fid: str,
    skey: str,
    combined_layers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Computes the frame-specific 7-layer decomposition for `shots/out/<fid>/`
    by combining:
      1. The frame's `arrays.npz` (`seg`, `id2label`), `depth_sharp.npz` (`depth`),
         `multiplane/planes.npz` (`superpixels`), and `shot.json` (`detections`, `stuff`),
      2. The scene's handmade cutout layers assigned to each plane (`P6`..`P0`).
    """
    import numpy as np

    out_dir = SHOTS_DIR / "out" / fid if fid else None
    plane_sem: Dict[str, List[str]] = {p: [] for p in ("P6", "P5", "P4", "P3", "P2", "P1", "P0")}
    plane_z_m: Dict[str, float] = {}
    plane_area_pct: Dict[str, float] = {}

    if out_dir and (out_dir / "arrays.npz").exists() and (out_dir / "depth_sharp.npz").exists():
        try:
            arr = np.load(out_dir / "arrays.npz", allow_pickle=True)
            d_arr = np.load(out_dir / "depth_sharp.npz")
            seg = arr["seg"]
            id2label = json.loads(str(arr["id2label"]))
            depth = d_arr["depth"]
            if seg.shape != depth.shape:
                sh_y = max(1, depth.shape[0] // seg.shape[0])
                sh_x = max(1, depth.shape[1] // seg.shape[1])
                depth_s = depth[::sh_y, ::sh_x][: seg.shape[0], : seg.shape[1]]
            else:
                depth_s = depth

            # Quantile thresholds across the frame's sharp metric depth distribution
            qs = np.quantile(depth_s, [0.12, 0.26, 0.44, 0.64, 0.82, 0.92])
            p_order = ["P0", "P1", "P2", "P3", "P4", "P5", "P6"]
            bins = np.digitize(depth_s, qs)
            total_px = float(seg.size)

            for bi, pname in enumerate(p_order):
                m = bins == bi
                cnt = int(m.sum())
                plane_area_pct[pname] = round((cnt / total_px) * 100.0, 1)
                plane_z_m[pname] = round(float(np.median(depth_s[m])), 2) if cnt > 0 else SEVEN_PLANES[pname]["z"]
                if cnt > 0:
                    vals, counts = np.unique(seg[m], return_counts=True)
                    order = np.argsort(-counts)
                    top_labels = []
                    for idx in order[:3]:
                        if counts[idx] / float(cnt) >= 0.05:
                            lbl = str(id2label.get(str(int(vals[idx])), "region"))
                            if lbl not in top_labels:
                                top_labels.append(lbl)
                    plane_sem[pname] = top_labels
        except Exception:
            pass

    breakdown: List[Dict[str, Any]] = []
    for pname in ("P6", "P5", "P4", "P3", "P2", "P1", "P0"):
        pmeta = SEVEN_PLANES[pname]
        cutouts_on_plane = [l["label"] for l in combined_layers if l["plane"] == pname]
        sem_list = plane_sem.get(pname) or []
        breakdown.append({
            "plane": pname,
            "depth_index": pmeta["depth_index"],
            "name": pmeta["name"],
            "short": pmeta["short"],
            "color_code": pmeta["color_code"],
            "ink_weight": pmeta["ink_weight"],
            "haze_mix": pmeta["haze_mix"],
            "z_stage": pmeta["z"],
            "z_median_m": plane_z_m.get(pname, pmeta["z"]),
            "frame_area_pct": plane_area_pct.get(pname, 14.3),
            "frame_semantics": sem_list,
            "handmade_cutouts": cutouts_on_plane,
        })
    return breakdown


def cel_shade_and_ink_cutout(
    p_img: Image.Image,
    plane_id: str,
    haze_rgb: Tuple[int, int, int] = (24, 30, 44),
) -> Image.Image:
    """
    Applies the `shots/cartoon.py` cel-shading & plane-weighted ink contour law
    to an RGBA cutout piece:
      - Quantizes interior RGB into cel flat steps
      - Mixes atmospheric depth haze proportional to `SEVEN_PLANES[plane_id]['haze_mix']`
      - Strokes the outer silhouette and interior edges with `INK_W` thickness
      - Adds a subtle plane-color-coded rim highlight (`PCOL`)
    """
    import numpy as np

    arr = np.array(p_img.convert("RGBA"), dtype=np.float32)
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    mask = alpha > 24
    if not mask.any():
        return p_img

    pmeta = SEVEN_PLANES.get(plane_id, SEVEN_PLANES["P3"])
    haze_mix = float(pmeta["haze_mix"])
    pcol = np.array(pmeta["rgb"], dtype=np.float32)
    haze = np.array(haze_rgb, dtype=np.float32)

    # 1. Posterize RGB into clean cel-shaded steps (smooth + quantize)
    step = 22.0 if pmeta["pal_k"] <= 2 else (16.0 if pmeta["pal_k"] == 3 else 12.0)
    cel_rgb = np.round(rgb / step) * step
    cel_rgb = 0.38 * rgb + 0.62 * cel_rgb

    # Boost saturation on Hero (P2) & Props (P3); push toward atmospheric haze on far planes (P4..P6)
    if plane_id in ("P2", "P3"):
        lum = cel_rgb.mean(axis=-1, keepdims=True)
        cel_rgb = np.clip(lum + (cel_rgb - lum) * 1.18, 0, 255)
    if haze_mix > 0.0:
        cel_rgb = cel_rgb * (1.0 - haze_mix) + haze * haze_mix

    # 2. Subtle plane-color-coded rim tint on upper-left boundary pixels
    eroded = np.zeros_like(mask)
    eroded[2:, 2:] = mask[:-2, :-2]
    rim_mask = mask & (~eroded)
    cel_rgb[rim_mask] = cel_rgb[rim_mask] * 0.55 + pcol * 0.45

    # 3. Plane-weighted outer ink contour (`INK_W`)
    ink_w = float(pmeta["ink_weight"])
    if ink_w > 0.3:
        pad = max(1, int(round(ink_w * 0.65)))
        dil = mask.copy()
        for dy in range(-pad, pad + 1):
            for dx in range(-pad, pad + 1):
                if dx == 0 and dy == 0:
                    continue
                y0_s = max(0, -dy); y1_s = mask.shape[0] - max(0, dy)
                x0_s = max(0, -dx); x1_s = mask.shape[1] - max(0, dx)
                y0_d = max(0, dy);  y1_d = mask.shape[0] - max(0, -dy)
                x0_d = max(0, dx);  x1_d = mask.shape[1] - max(0, -dx)
                dil[y0_d:y1_d, x0_d:x1_d] |= mask[y0_s:y1_s, x0_s:x1_s]
        outer_line = dil & (~mask)
        # Dark ink with subtle plane-color tint
        ink_rgb = np.array([16.0, 14.0, 22.0], dtype=np.float32) * 0.82 + pcol * 0.18
        cel_rgb[outer_line] = ink_rgb
        alpha = np.where(outer_line, 235.0, alpha)

    out_arr = np.dstack([np.clip(cel_rgb, 0, 255).astype(np.uint8), np.clip(alpha, 0, 255).astype(np.uint8)])
    return Image.fromarray(out_arr, mode="RGBA")


def render_clean_scene_plate(
    out_webp: pathlib.Path,
    backdrop_path: pathlib.Path,
    cel_path: Optional[pathlib.Path],
    ink_path: Optional[pathlib.Path],
    floor_y: int,
    layers: List[Dict[str, Any]],
    district_glow: List[Any],
    haze_rgb: Tuple[int, int, int] = (24, 30, 44),
    return_pil: bool = False,
) -> Optional[Image.Image]:
    """
    Renders a 7-layer cel-shaded 1280x720 WebP scene plate combining:
      - The painted backdrop blended with the world cel-wash (`cel.webp`) and ink pass (`ink.webp`),
      - All 7 multiplane cutout layers (`P6`..`P0`) cel-shaded & plane-inked (`INK_W`)
        with Aspect-Aware Span Scaling (`compute_piece_stage_dims`).
    """
    W, H = 1280, 720
    if backdrop_path.exists():
        bg = Image.open(backdrop_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    else:
        bg = Image.new("RGBA", (W, H), (14, 18, 26, 255))

    # Blend 52% cel-wash plate if available so the backdrop has authentic cel gouache flats
    if cel_path and cel_path.exists():
        try:
            cel_bg = Image.open(cel_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
            bg = Image.blend(bg, cel_bg, alpha=0.52)
        except Exception:
            pass

    bg_rgb = ImageEnhance.Contrast(bg.convert("RGB")).enhance(1.06)
    canvas = bg_rgb.convert("RGBA")

    # Overlay subtle world ink contour pass (`ink.webp`) at 28% opacity
    if ink_path and ink_path.exists():
        try:
            ink_im = Image.open(ink_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
            r_ch, g_ch, b_ch, a_ch = ink_im.split()
            a_ch = a_ch.point(lambda a: int(a * 0.28))
            ink_dark = Image.merge("RGBA", (
                Image.new("L", (W, H), 14),
                Image.new("L", (W, H), 12),
                Image.new("L", (W, H), 20),
                a_ch,
            ))
            canvas = Image.alpha_composite(canvas, ink_dark)
        except Exception:
            pass

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
        plane_id = str(lyr.get("plane", "P3"))
        target_w, target_h = compute_piece_stage_dims(pw, ph, sc, plane_id, W, H)

        p_resized = p_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        if lyr.get("flip"):
            p_resized = p_resized.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        # Apply cel-shading + plane-weighted ink contour + subtle color-code rim
        p_cel = cel_shade_and_ink_cutout(p_resized, plane_id, haze_rgb=haze_rgb)
        alpha_mult = float(lyr.get("alpha", 0.98))
        if alpha_mult < 0.99:
            r_c, g_c, b_c, a_c = p_cel.split()
            a_c = a_c.point(lambda a: int(a * alpha_mult))
            p_cel = Image.merge("RGBA", (r_c, g_c, b_c, a_c))

        cx = int(round(float(lyr.get("x", 0.5)) * W))
        by = int(round(float(lyr.get("y", 0.85)) * H))
        dx = cx - target_w // 2
        dy = by - target_h

        shadow = p_cel.split()[3].point(lambda a: int(a * 0.42))
        shadow_rgba = Image.merge("RGBA", (
            Image.new("L", (target_w, target_h), 6),
            Image.new("L", (target_w, target_h), 8),
            Image.new("L", (target_w, target_h), 12),
            shadow,
        )).filter(ImageFilter.GaussianBlur(radius=4))
        canvas.alpha_composite(shadow_rgba, dest=(dx + 4, dy + 6))
        canvas.alpha_composite(p_cel, dest=(dx, dy))

    out_webp.parent.mkdir(parents=True, exist_ok=True)
    rgb = canvas.convert("RGB")
    rgb.save(out_webp, "WEBP", quality=88, method=4)
    if return_pil:
        return rgb
    return None


def main() -> None:
    print("[1/5] Loading wygwyl_atlas_manifest.json and world_data.js...")
    manifest = json.loads(MANIFEST_PATH.read_text())
    parts_by_id: Dict[str, Dict[str, Any]] = {}
    sheet_by_part: Dict[str, Dict[str, Any]] = {}
    for asset in manifest["assets"]:
        for pt in asset.get("parts", []):
            parts_by_id[pt["id"]] = pt
            sheet_by_part[pt["id"]] = asset

    world_js_path = SHOTS_DIR / "world_data.js"
    world_txt = world_js_path.read_text().replace("window.WORLD = ", "", 1).rstrip(";\n ")
    world_data = json.loads(world_txt)
    world_by_k: Dict[str, Dict[str, Any]] = {s["k"]: s for s in world_data.get("shots", [])}

    # Strictly verify every part_id, backdrop, and all 7 handmade planes (P6..P0) in CUSTOM_SCENES
    missing_parts = []
    missing_bgs = []
    for skey, spec in CUSTOM_SCENES.items():
        bg_p = SHOTS_DIR / spec["backdrop"]
        if not bg_p.exists():
            missing_bgs.append((skey, spec["backdrop"]))
        enriched_layers = verify_handmade_seven_layers_for_scene(skey, spec["layers"])
        for lyr in enriched_layers:
            pid = lyr["part_id"]
            if pid not in parts_by_id:
                missing_parts.append((skey, pid))
    if missing_parts or missing_bgs:
        raise RuntimeError(f"Missing parts: {missing_parts}, Missing bgs: {missing_bgs}")
    print(f"  Verified {len(CUSTOM_SCENES)} custom scenes across all 7 handmade layers (P6..P0): 0 missing parts, 0 generic fallbacks!")

    # Fix poet/black_tshirt in shots/play/data.json so draws[9] (Reading the Manuscript)
    # has has_scene_prop=True and default idle is prop-free upright stance
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
    scenes_with_all_7 = 0

    print("[2/5] Building 7-layer cel-shaded & color-coded level.json files for all 14 poems...")
    for poem_num in range(1, 15):
        num_str = f"{poem_num:02d}"
        lv_path = LEVELS_DIR / num_str / "level.json"
        lv = json.loads(lv_path.read_text())
        fw, fh = int(lv["frame"][0]), int(lv["frame"][1])
        lv["seven_planes_spec"] = SEVEN_PLANES

        for sc_idx, sc in enumerate(lv["scenes"]):
            skey = sc["key"]
            spec = CUSTOM_SCENES.get(skey)
            if not spec:
                raise RuntimeError(f"Missing custom scene spec for {skey}!")

            backdrop_shots_rel = spec["backdrop"]
            backdrop_play_rel = f"../{backdrop_shots_rel}"
            wk = backdrop_shots_rel.split("/")[1]
            wshot = world_by_k.get(wk, {})
            fid = wshot.get("id", "")
            persp = load_frame_perspective_signals(fid)
            stage_haze_tuple = tuple(persp["stage_haze_rgb"])

            # Resolve cel, ink, layout_sheet, planes_gs, notan, exploded, and world 7-plane sheets
            cel_rel = f"world/{wk}/cel.webp"
            ink_rel = f"world/{wk}/ink.webp"
            layout_rel = f"out/{fid}/cartoon/layout_sheet.png" if fid else ""
            planes_gs_rel = f"out/{fid}/cartoon/planes_gs.png" if fid else ""
            notan_rel = f"out/{fid}/cartoon/notan.png" if fid else ""
            exploded_rel = f"out/{fid}/multiplane/exploded.jpg" if fid else ""

            world_sheets = []
            for wsh in wshot.get("sheets", []):
                w_p = wsh.get("plane", "P4")
                pmeta = SEVEN_PLANES.get(w_p, SEVEN_PLANES["P4"])
                world_sheets.append({
                    "file": f"../{wsh['lo']}",
                    "plane": w_p,
                    "depth_index": pmeta["depth_index"],
                    "color_code": pmeta["color_code"],
                    "z": round(float(wsh.get("z", pmeta["z"])), 3),
                    "label": wsh.get("label", w_p),
                    "water": bool(wsh.get("water", False)),
                    "sway": bool(wsh.get("sway", False)),
                })

            enriched_specs = verify_handmade_seven_layers_for_scene(skey, spec["layers"])
            combined_layers: List[Dict[str, Any]] = []
            stations: List[Dict[str, Any]] = []
            sc["cel_passes"] = {
                "world_key": wk,
                "shot_id": fid,
                "cel_file": f"../{cel_rel}" if (SHOTS_DIR / cel_rel).exists() else "",
                "ink_file": f"../{ink_rel}" if (SHOTS_DIR / ink_rel).exists() else "",
                "layout_file": f"../{layout_rel}" if layout_rel and (SHOTS_DIR / layout_rel).exists() else "",
                "planes_map_file": f"../{planes_gs_rel}" if planes_gs_rel and (SHOTS_DIR / planes_gs_rel).exists() else "",
                "notan_file": f"../{notan_rel}" if notan_rel and (SHOTS_DIR / notan_rel).exists() else "",
                "exploded_file": f"../{exploded_rel}" if exploded_rel and (SHOTS_DIR / exploded_rel).exists() else "",
                "perspective": persp,
                "world_sheets": world_sheets,
                "seven_layer_breakdown": compute_frame_seven_layer_breakdown(fid, skey, enriched_specs),
            }

            for e_idx, lspec in enumerate(enriched_specs):
                pid = lspec["part_id"]
                pt = parts_by_id[pid]
                shots_file = pt["file"]
                play_file = f"../{shots_file}"
                st_title = lspec.get("station_title")
                station_id = f"st_{skey.replace('.', '_')}_{e_idx}" if st_title else ""
                plane_id = lspec["plane"]
                pmeta = SEVEN_PLANES.get(plane_id, SEVEN_PLANES["P3"])

                lyr_obj = {
                    "id": f"lyr_{skey.replace('.', '_')}_{e_idx}_{pid.split('__')[-1]}",
                    "part_id": pid,
                    "sheet_id": sheet_by_part[pid]["id"],
                    "label": lspec["label"],
                    "station_id": station_id,
                    "station_title": st_title or lspec["label"],
                    "plane": plane_id,
                    "depth_index": pmeta["depth_index"],
                    "plane_name": pmeta["name"],
                    "color_code": pmeta["color_code"],
                    "ink_weight": pmeta["ink_weight"],
                    "haze_mix": pmeta["haze_mix"],
                    "pal_k": pmeta["pal_k"],
                    "z": round(float(lspec["z"]), 2),
                    "x": round(float(lspec["x"]), 4),
                    "y": round(float(lspec["y"]), 4),
                    "scale": round(float(lspec["scale"]), 4),
                    "width": int(pt.get("width", 240)),
                    "height": int(pt.get("height", 240)),
                    "role": (
                        "sky_canopy" if plane_id == "P6" else
                        "station_horizon" if plane_id == "P5" else
                        "station_arch" if plane_id == "P4" else
                        "focal_cast" if plane_id == "P2" else
                        "fg_fx" if plane_id == "P1" else
                        "proscenium_mask" if plane_id == "P0" else
                        "station_prop"
                    ),
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
                        "plane": plane_id,
                        "color_code": pmeta["color_code"],
                        "x": round(float(lspec["x"]), 3),
                        "mx": round(float(lspec["x"]) * fw, 1),
                        "y": round(float(lspec["y"]), 3),
                        "anim_role": lspec.get("anim_role", "static"),
                    })

            combined_layers.sort(key=lambda item: float(item.get("z", 1.4)), reverse=True)
            total_layers += len(combined_layers)
            if len({l["plane"] for l in combined_layers}) == 7:
                scenes_with_all_7 += 1

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
                cel_path=SHOTS_DIR / cel_rel,
                ink_path=SHOTS_DIR / ink_rel,
                floor_y=sc["floor"],
                layers=combined_layers,
                district_glow=sc.get("palette_glow", ["#d8ab4f"]),
                haze_rgb=stage_haze_tuple,
                return_pil=True,
            )

            if pil_plate is not None:
                thumb = pil_plate.resize((420, 236), Image.Resampling.LANCZOS)
                tdraw = ImageDraw.Draw(thumb)
                tdraw.rectangle([0, 0, 420, 24], fill=(8, 10, 14))
                st_names = " | ".join(s["title"][:16] for s in stations[:3])
                tdraw.text((6, 5), f"{skey} [7L CEL] {sc['name'][:18]} -> {st_names[:36]}", fill=(255, 224, 120))
                # Draw 7 color-coded plane indicator dots in top-right of audit thumbnail
                for p_i, pk in enumerate(("P6", "P5", "P4", "P3", "P2", "P1", "P0")):
                    p_rgb = SEVEN_PLANES[pk]["rgb"]
                    dx_dot = 420 - (7 - p_i) * 11 - 4
                    tdraw.ellipse([dx_dot, 7, dx_dot + 8, 15], fill=p_rgb, outline=(255, 255, 255))
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
        print(f"  Poem {num_str} ({lv['title']}): custom-built {len(lv['scenes'])} 7-layer cel scenes")

    print("[3/5] Enriching level_assets_catalog.json with 7-layer color codes & decomposed World sheets...")
    if CATALOG_OUT_PATH.exists():
        cat_data = json.loads(CATALOG_OUT_PATH.read_text())
        cat_items = [it for it in cat_data.get("items", []) if it.get("category") != "world_sheets"]
        for it in cat_items:
            pl = it.get("plane", "P3")
            pmeta = SEVEN_PLANES.get(pl, SEVEN_PLANES["P3"])
            it["depth_index"] = pmeta["depth_index"]
            it["plane_name"] = pmeta["name"]
            it["color_code"] = pmeta["color_code"]
            it["ink_weight"] = pmeta["ink_weight"]
            it["haze_mix"] = pmeta["haze_mix"]

        # Add decomposed Atlantis World 7-Plane Sheets (`world/<wk>/S*_P*.webp`) as browsable worldbuilding layers!
        reel_poem_by_shot: Dict[str, int] = {}
        for r in world_data.get("reels", []):
            pnum = int(r.get("num", "1"))
            for sid in r.get("shots", []):
                reel_poem_by_shot[sid] = pnum

        for ws in world_data.get("shots", []):
            wk = ws["k"]
            pnum = reel_poem_by_shot.get(ws["id"], 1)
            for sh_i, sh in enumerate(ws.get("sheets", [])):
                w_p = sh.get("plane", "P4")
                pmeta = SEVEN_PLANES.get(w_p, SEVEN_PLANES["P4"])
                sh_rel = sh.get("lo", "")
                if not sh_rel or not (SHOTS_DIR / sh_rel).exists():
                    continue
                cat_items.append({
                    "part_id": f"world.{wk}.s{sh_i:02d}_{w_p}",
                    "sheet_id": f"world.{wk}",
                    "poem": pnum,
                    "category": "world_sheets",
                    "plane": w_p,
                    "depth_index": pmeta["depth_index"],
                    "plane_name": pmeta["name"],
                    "color_code": pmeta["color_code"],
                    "ink_weight": pmeta["ink_weight"],
                    "haze_mix": pmeta["haze_mix"],
                    "z": pmeta["z"],
                    "label": f"[{w_p}] {ws.get('title', wk)[:26]} · {sh.get('label', w_p)}",
                    "default_scale": 0.48 if w_p in ("P6", "P5", "P4", "P0") else 0.34,
                    "width": 768,
                    "height": 430,
                    "anim_role": "wave_near" if sh.get("water") else ("flower_bloom" if sh.get("sway") else "static"),
                    "file": f"../{sh_rel}",
                })

        cat_data["seven_planes"] = SEVEN_PLANES
        cat_data["total_items"] = len(cat_items)
        cat_data["items"] = cat_items
        CATALOG_OUT_PATH.write_text(json.dumps(cat_data, separators=(",", ":")))
        print(f"  Updated {CATALOG_OUT_PATH} with {len(cat_items)} color-coded 7-layer items!")

    print("[4/5] Saving visual audit contact sheets for all 90 7-layer cel scenes...")
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    for bname, thumbs in audit_batches.items():
        cols = 4
        rows = (len(thumbs) + cols - 1) // cols
        grid = Image.new("RGB", (cols * 424, rows * 240), (10, 12, 16))
        for i, im in enumerate(thumbs):
            grid.paste(im, ((i % cols) * 424 + 2, (i // cols) * 240 + 2))
        grid.save(SCRATCH_DIR / bname)
        print(f"  Saved {SCRATCH_DIR / bname} ({len(thumbs)} scenes)")

    print(
        f"[5/5] DONE! Custom-built {total_scenes} scenes with {total_layers} verified multiplane layers "
        f"({scenes_with_all_7}/{total_scenes} scenes have all 7 layers P6->P0 populated!)."
    )


if __name__ == "__main__":
    main()

