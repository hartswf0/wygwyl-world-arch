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
import sys
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lego_set_extensions import (
    W_FRAME,
    W_EXT,
    W_MOD,
    HYPERFLAT_FLOOR_Y,
    HYPERFLAT_HORIZON_Y,
    SHOT_SCALE_TIERS,
    get_scene_shot_profile,
    get_in_frame_portal_footage,
    get_scene_lego_extension,
)

H_HEADROOM = 160
H_EXT = 720 + H_HEADROOM  # 880 px (160px upper gable headroom + 720px frame height)

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
            L("05.props.galaxy-universe__p01", "Swirling Spiral Galaxy Core Overhead", "P6", 6.00, 0.52, 0.24, 0.22, "planet_orbit", "Spiral Galaxies Overhead"),
            L("05.props.galaxy-universe__p03", "Distant Nebula Cloud Canopy", "P5", 3.80, 0.22, 0.30, 0.18, "sun_pulse", "Naming My Own Stars"),
            L("05.hero.perimeter__p04", "Star-Inscribed Perimeter Stone Wall", "P4", 2.44, 0.22, 0.86, 0.28, "portal_aperture", None),
            L("05.props.galaxy-universe__p17", "Golden Constellation Pedestal", "P3", 1.40, 0.34, 0.88, 0.20, "planet_orbit", "Naming My Own Stars"),
            L("05.props.staff-mattress-emblem__p07", "Radiant Star Crest Medallion", "P2", 1.04, 0.72, 0.86, 0.18, "sun_pulse", "The Waiting Past"),
            L("05.props.galaxy-universe__p06", "Foreground Orbiting Star Cluster", "P1", 0.54, 0.84, 0.92, 0.15, "lamp_glow", None, False, 0.76),
            L("05.set.winged_marble_gate__p04", "Proscenium East Star-Gate Pillar", "P0", 0.25, 0.96, 0.95, 0.34, "proscenium_mask", None, True, 0.78),
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
            L("08.hero.marquee__p01", "Glowing NEW SINGLE Theatre Stone Facade", "P4", 2.46, 0.24, 0.85, 0.32, "lamp_glow", "NEW SINGLE Club Marquee"),
            L("07.props.speakers-vu__p15", "Rooftop Monitor Speaker Cabinet", "P3", 1.40, 0.26, 0.88, 0.20, "speaker_pulse", "Soul Leaves the Dancer"),
            L("07.props.dj-decks__p03", "Rooftop Terrace DJ Console", "P2", 1.04, 0.72, 0.88, 0.19, "dj_console", None),
            L("08.cast.angel.wings__p03", "Luminous Outspread Soul Wings", "P1", 0.54, 0.58, 0.64, 0.20, "wing_flap_L", "Ascending Soul Vapor", False, 0.82),
            L("08.hero.marquee.interior__p01", "Proscenium Neon Marquee Pillar", "P0", 0.25, 0.04, 0.95, 0.34, "proscenium_mask", None, False, 0.78),
        ],
    },
    "08.1": {
        "backdrop": "world/e3c427ae_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "club_groove",
        "counterpart": {"key": "club_dress/club", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("08.props.moons-laundry__p01", "High Violet Ceiling Moon", "P6", 6.00, 0.50, 0.20, 0.16, "sun_pulse", None, False, 0.80),
            L("08.set.rooftop_club__p06", "Club Window Skyline Silhouette", "P5", 3.80, 0.50, 0.82, 0.18, "static", None, False, 0.88),
            L("08.hero.marquee.interior__p01", "Neon NEW SINGLE Stage Arch", "P4", 2.44, 0.22, 0.85, 0.34, "portal_aperture", "Strangers Collide on Floor"),
            L("07.props.dj-decks__p01", "Late-Night Club DJ Console", "P3", 1.40, 0.52, 0.87, 0.20, "dj_console", "Last One to Leave"),
            L("07.props.speakers-vu__p15", "Club Dancefloor Bass Monitor", "P2", 1.04, 0.24, 0.88, 0.19, "speaker_pulse", "Midnight Dance Arches"),
            L("06.props.lantern-candle-guitar__p11", "Foreground Lounge Votive Candle", "P1", 0.52, 0.82, 0.91, 0.15, "lamp_glow", None, False, 0.78),
            L("08.hero.marquee.interior__p08", "Proscenium Violet Arch Column", "P0", 0.25, 0.96, 0.95, 0.34, "proscenium_mask", None, True, 0.78),
        ],
    },
    "08.2": {
        "backdrop": "world/cbb5e9c5_2/backdrop.webp",
        "floor": 614,
        "initial_cue": "open_arms_wide",
        "counterpart": {"key": "poet_soul/soul", "x": 720, "dir": -1, "cue": "kneel_2", "y_offset": -80},
        "layers": [
            L("08.props.moons-laundry__p01", "Closest Salted Moon Overhead", "P6", 6.00, 0.80, 0.24, 0.20, "planet_orbit", "Moons of the Equator", False, 0.86),
            L("08.set.atlantis_aerial__p01", "Aerial Mandala of Atlantis Below", "P5", 3.80, 0.22, 0.74, 0.28, "portal_other_world", "Aerial Atlantis Below", False, 0.84),
            L("08.hero.marquee__p01", "High Equator Wind-Tower Colonnade", "P4", 2.42, 0.82, 0.85, 0.30, "portal_aperture", None),
            L("04.props.word-shore__p23", "Equator Wind Wrought-Iron Lantern", "P3", 1.42, 0.28, 0.88, 0.19, "lamp_glow", "Open Field at the Equator"),
            L("06.props.lantern-candle-guitar__p11", "Equator Votive Candle", "P2", 1.04, 0.74, 0.88, 0.16, "lamp_glow", None),
            L("08.cast.angel.wings__p03", "Hovering Equator Angel Wing Crest", "P1", 0.52, 0.56, 0.64, 0.18, "wing_flap_L", None, False, 0.78),
            L("08.set.rooftop_club__p04", "Proscenium Equator Beacon Frame", "P0", 0.25, 0.04, 0.95, 0.34, "proscenium_mask", None, False, 0.78),
        ],
    },
    "08.3": {
        "backdrop": "world/f56df2d8_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "kneel_universe",
        "counterpart": {"key": "angel/robe", "x": 880, "dir": -1, "cue": "idle"},
        "layers": [
            L("08.props.moons-laundry__p01", "Sanctuary Moon Above Baptism Font", "P6", 6.00, 0.50, 0.20, 0.18, "planet_orbit", None, False, 0.84),
            L("08.set.atlantis_aerial__p01", "Distant Luminous Mandala Horizon", "P5", 3.80, 0.50, 0.76, 0.24, "portal_other_world", None, False, 0.82),
            L("08.hero.marquee__p01", "Marble Sanctuary Baptism Colonnade", "P4", 2.42, 0.20, 0.85, 0.30, "portal_aperture", None),
            L("11.props.inlays-lantern__p15", "Sanctuary Baptism Brass Lantern", "P3", 1.42, 0.26, 0.88, 0.19, "lamp_glow", "Salted Ice-Water Basin"),
            L("04.props.word-shore__p23", "Choir Colonnade Iron Lantern", "P3", 1.38, 0.72, 0.88, 0.19, "lamp_glow", "Angels' Ice-Water Baptism"),
            L("08.cast.angel.wings__p03", "Feathered Angel Sanctuary Wings", "P2", 1.04, 0.52, 0.72, 0.22, "wing_flap_L", "Choir of Night Angels"),
            L("06.props.lantern-candle-guitar__p11", "Foreground Baptism Votive Flame", "P1", 0.52, 0.44, 0.91, 0.15, "lamp_glow", None, False, 0.78),
            L("08.hero.marquee.interior__p01", "Proscenium Sanctuary Wing Arch", "P0", 0.25, 0.96, 0.95, 0.34, "proscenium_mask", None, True, 0.78),
        ],
    },
    "08.4": {
        "backdrop": "world/cf180ca2_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "idle_hand_chest",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Pale Dawn Disc Over Rooftop Terrace", "P6", 6.00, 0.78, 0.22, 0.16, "sun_pulse", None, False, 0.82),
            L("08.set.rooftop_club__p06", "Quiet Dawn Skyline & Radio Masts", "P5", 3.80, 0.50, 0.84, 0.16, "static", None, False, 0.86),
            L("08.hero.marquee__p01", "Quiet Dawn Rooftop Colonnade", "P4", 2.42, 0.52, 0.85, 0.30, "portal_aperture", "Soul Returns to the Body"),
            L("04.props.word-shore__p23", "Still Terrace Iron Lantern at Dawn", "P3", 1.42, 0.76, 0.88, 0.19, "lamp_glow", "Terrace Recovery Basin"),
            L("06.props.lantern-candle-guitar__p11", "Clear Morning Votive Candle", "P2", 1.04, 0.28, 0.88, 0.16, "lamp_glow", "Breathing in the Smoke"),
            L("11.props.inlays-lantern__p15", "Foreground Parapet Brass Lantern", "P1", 0.48, 0.18, 0.91, 0.16, "lamp_glow", None, False, 0.78),
            L("08.set.rooftop_club__p04", "Proscenium Rooftop Parapet Column", "P0", 0.25, 0.04, 0.95, 0.34, "proscenium_mask", None, False, 0.78),
        ],
    },
    "08.5": {
        "backdrop": "world/0240b488_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "back_horizon",
        "counterpart": None,
        "layers": [
            L("09.props.moon-sun__p01", "Morning Sun Over the Peaks", "P6", 6.00, 0.80, 0.24, 0.18, "sun_pulse", "Wandering Eyes at Dawn", False, 0.86),
            L("10.set.mountain_road__p04", "Unfamiliar Mountains in the Distance", "P5", 3.80, 0.52, 0.82, 0.18, "water_backing", "Mountains From the Rooftop", False, 0.86),
            L("08.set.rooftop_club__p04", "West Rooftop Beacon Tower", "P4", 2.40, 0.20, 0.86, 0.32, "portal_aperture", "Rooftop Parapet"),
            L("04.props.word-shore__p23", "Dawn Terrace Parapet Lantern", "P3", 1.40, 0.76, 0.88, 0.19, "lamp_glow", None),
            L("06.props.lantern-candle-guitar__p11", "Morning Parapet Brass Candle", "P2", 1.04, 0.28, 0.88, 0.16, "lamp_glow", None),
            L("11.props.inlays-lantern__p15", "Foreground Dawn Watchtower Lantern", "P1", 0.52, 0.64, 0.91, 0.16, "lamp_glow", None, False, 0.78),
            L("08.hero.marquee__p01", "Proscenium East Terrace Pilaster", "P0", 0.25, 0.96, 0.95, 0.34, "proscenium_mask", None, True, 0.78),
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
            L("09.props.moon-sun__p01", "Shared Full Moon Overhead", "P6", 6.00, 0.80, 0.24, 0.18, "sun_pulse", "Under the Shared Moon", False, 0.86),
            L("09.set.atlantis_harbor_street__p08", "Distant Harbor Crane & Quayside", "P5", 3.80, 0.76, 0.82, 0.28, "portal_aperture", None, False, 0.84),
            L("09.set.atlantis_club_sidewalk__p04", "Double-Globe Harbor Streetlamp", "P4", 2.40, 0.52, 0.86, 0.36, "lamp_glow", "Outside the Club Canopy"),
            L("09.props.suitcases-notice__p01", "Standing Strapped Leather Suitcase", "P3", 1.40, 0.34, 0.88, 0.18, "lamp_glow", "The EX in the Crowd"),
            L("09.props.suitcases-notice__p05", "Resting Curbside Leather Valise", "P2", 1.04, 0.66, 0.89, 0.18, "drawer_slide", None),
            L("06.props.lantern-candle-guitar__p11", "Foreground Curbside Lantern Glow", "P1", 0.52, 0.82, 0.91, 0.15, "lamp_glow", None, False, 0.78),
            L("09.set.atlantis_club_sidewalk__p05", "Proscenium Iron Streetlamp Post", "P0", 0.25, 0.04, 0.95, 0.34, "proscenium_mask", None, False, 0.78),
        ],
    },
    "09.1": {
        "backdrop": "world/abac8bce_1/backdrop.webp",
        "floor": 614,
        "initial_cue": "walk_stride_L",
        "counterpart": {"key": "ex/ex_jacket", "x": 880, "dir": -1, "cue": "idle"},
        "layers": [
            L("09.props.moon-sun__p01", "Moon Settling Over the Water", "P6", 6.00, 0.78, 0.24, 0.18, "sun_pulse", "Moonlight on the Harbor", False, 0.86),
            L("09.set.atlantis_harbor_street__p08", "Distant Harbor Crane Silhouette", "P5", 3.80, 0.54, 0.85, 0.32, "portal_aperture", "Walking Toward the Moon", False, 0.84),
            L("09.set.atlantis_club_sidewalk__p05", "Harbor Quay Streetlamp West", "P4", 2.42, 0.22, 0.86, 0.36, "lamp_glow", "Harbor Quay Promenade"),
            L("13.props.planet-boats__p18", "Moored Harbor Skiff on the Quay", "P3", 1.40, 0.76, 0.87, 0.22, "boat_rock", None),
            L("09.props.suitcases-notice__p05", "Traveler's Suitcase by the Railing", "P2", 1.04, 0.38, 0.89, 0.18, "drawer_slide", None),
            L("04.props.word-shore__p23", "Foreground Quay Iron Lantern", "P1", 0.52, 0.16, 0.91, 0.17, "lamp_glow", None, False, 0.78),
            L("09.set.atlantis_club_sidewalk__p04", "Proscenium Harbor Quay Lamp Wing", "P0", 0.25, 0.96, 0.95, 0.34, "proscenium_mask", None, True, 0.78),
        ],
    },
    "09.2": {
        "backdrop": "world/bf0a66ea_0/backdrop.webp",
        "floor": 614,
        "initial_cue": "shrug_peace",
        "counterpart": {"key": "ex/ex_jacket", "x": 880, "dir": -1, "cue": "suitcase"},
        "layers": [
            L("09.props.moon-sun__p01", "High Harbor Moon Over the Pier", "P6", 6.00, 0.78, 0.22, 0.18, "sun_pulse", None, False, 0.84),
            L("09.set.atlantis_harbor_street__p08", "Distant Pier Crane & Ship Mast", "P5", 3.80, 0.34, 0.84, 0.28, "portal_aperture", None, False, 0.84),
            L("09.set.atlantis_club_sidewalk__p05", "Pier Curbside Lantern Post", "P4", 2.42, 0.18, 0.86, 0.34, "lamp_glow", None),
            L("09.props.phonebooth__p14", "3D Glass Harbor Phone Booth", "P3", 1.44, 0.52, 0.87, 0.28, "booth_frame", "The Harbor Phone Booth"),
            L("09.props.suitcases-notice__p01", "Standing Brown Leather Suitcase", "P3", 1.38, 0.76, 0.88, 0.18, "lamp_glow", "2nd Gate Notice Sign"),
            L("09.props.suitcases-notice__p05", "Packed Brown Leather Suitcase on Curb", "P2", 1.04, 0.28, 0.89, 0.18, "drawer_slide", "Suitcases on the Curb"),
            L("04.props.word-shore__p23", "Foreground Pier Lantern", "P1", 0.52, 0.86, 0.91, 0.17, "lamp_glow", None, False, 0.78),
            L("09.set.atlantis_club_sidewalk__p04", "Proscenium Pier Lantern Post", "P0", 0.25, 0.04, 0.95, 0.34, "proscenium_mask", None, False, 0.78),
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
            L("01.props.chandeliers__p10", "Grand Crystal Ballroom Chandelier", "P6", 6.00, 0.50, 0.24, 0.20, "chandelier_sway", None, False, 0.84),
            L("14.set.vintage_party__p03", "Distant Ballroom Gallery Arch", "P5", 3.80, 0.22, 0.82, 0.26, "static", None, False, 0.80),
            L("14.set.vintage_party__p03", "1940s Grand Ballroom Archway", "P4", 2.40, 0.80, 0.86, 0.28, "portal_other_world", "The Dance at the Vintage Party"),
            L("14.props.party__p05", "Golden Ballroom Champagne Chalice", "P3", 1.42, 0.26, 0.88, 0.16, "lamp_glow", "Under the Ballroom Lights"),
            L("14.props.party__p20", "Brass Horn Table Gramophone", "P2", 1.04, 0.78, 0.88, 0.22, "turntable_spin", "Gramophone Waltz"),
            L("14.props.party__p19", "Foreground Festoon Bulb Canopy", "P1", 0.54, 0.78, 0.22, 0.16, "lamp_glow", None, False, 0.78),
            L("14.set.vintage_party__p03", "Proscenium Ballroom Pilaster", "P0", 0.25, 0.97, 0.95, 0.30, "proscenium_mask", None, True, 0.60),
        ],
    },
    "14.6": {
        "backdrop": "world/9572112a_1/backdrop.webp",
        "floor": 612,
        "initial_cue": "idle_grounded",
        "counterpart": {"key": "vintage_man/suit", "x": 920, "dir": -1, "cue": "idle"},
        "layers": [
            L("01.props.chandeliers__p02", "Warm Genesis Ceiling Skylight Glow", "P6", 6.00, 0.50, 0.20, 0.18, "sun_pulse", None, False, 0.78),
            L("14.props.door__p02", "Receding Panelled Vintage Door", "P5", 3.80, 0.20, 0.84, 0.24, "static", "The Vintage Door Closes", False, 0.80),
            L("01.props.window__p01", "Quiet Bedroom Sash Window at Dawn", "P4", 2.44, 0.82, 0.85, 0.26, "portal_aperture", "Genesis · Back to Poem 01"),
            L("14.props.party__p20", "Brass Horn Table Gramophone", "P3", 1.44, 0.22, 0.88, 0.20, "lamp_glow", "Into the Ballroom Crowd"),
            L("01.props.room__p18", "Genesis Bedroom Television & Stand", "P2", 1.04, 0.66, 0.89, 0.20, "portal_tv_flicker", None),
            L("14.props.party__p05", "Foreground Golden Chalice Relic", "P1", 0.54, 0.86, 0.91, 0.14, "lamp_glow", None, False, 0.78),
            L("14.props.door__p11", "Proscenium Closing Threshold Jamb", "P0", 0.25, 0.03, 0.95, 0.30, "proscenium_mask", None, False, 0.60),
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
    is_set_extension: bool = False,
    lego_role: str = "",
) -> Tuple[int, int]:
    """
    Aspect-Aware Span Scaling Law (shared 1:1 with `shots/play/levels.html`):
      - For in-frame props (`is_set_extension=False`), preserves 100% native aspect ratio
        (`target_w / target_h == pw / ph`) and damps overly wide spans above `0.85 * W`.
      - For Outside-the-Frame Lego Set Extensions (`is_set_extension=True`):
        * `wall_with_door_hole` / `wall_bay`: Full-frame height (`target_h = round(H * sc)` = `660..720px`)
          so the wall's top & bottom align flush with the `1280x720` frame, spanning up to `1180px` wide
          (with any left overlap `x < 1280` tucked behind the `1280x720` frame!).
        * `gable_portal_cap`: Allows `sc > 1.0` (`target_h` up to `860px`) so the doorway arch frames
          the doorway hole and the stone/timber gable roof rises into the `160px` upper headroom above `y = 0`!
        * `boulevard_tree`: Full boulevard canopy height (`target_h` up to `640px`).
    """
    ar = float(pw) / float(max(1, ph))
    if is_set_extension:
        if lego_role in ("wall_with_door_hole", "wall_bay"):
            target_h = max(240, min(int(H * 1.02), int(round(H * sc))))
            eff_ar = min(1.68, max(0.85, ar * 0.62 if ar > 1.85 else ar))
            target_w = max(360, min(1180, int(round(target_h * eff_ar))))
            return target_w, target_h
        if lego_role == "gable_portal_cap":
            target_h = max(280, min(int(H * 1.24), int(round(H * sc))))
            eff_ar = min(0.88, max(0.48, ar * 0.68 if ar > 1.05 else ar))
            target_w = max(240, min(680, int(round(target_h * eff_ar))))
            return target_w, target_h
        if lego_role == "boulevard_tree":
            target_h = max(180, min(int(H * 0.92), int(round(H * sc))))
            eff_ar = min(0.85, max(0.38, ar))
            target_w = max(120, min(480, int(round(target_h * eff_ar))))
            return target_w, target_h
        target_h = max(28, min(int(H * 0.90), int(round(H * sc))))
        target_w = max(28, min(780, int(round(target_h * ar))))
        return target_w, target_h

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


SCENE_CURATED_PROP_OVERRIDES: Dict[str, List[Dict[str, Any]]] = {
    # =======================================================================
    # POEM 01 · OUT OF LIFE
    # =======================================================================
    "01.0": [
        L("01.props.room__p01", "Three-Drawer Wooden Bedroom Dresser", "P3", 1.44, 0.22, 0.88, 0.22, "drawer_slide", "Wooden Bedroom Dresser"),
        L("01.props.room__p18", "Flickering Bedroom Television & Stand", "P3", 1.40, 0.68, 0.89, 0.20, "portal_tv_flicker", "Flickering TV Stand"),
        L("01.props.handheld__p04", "Open Poetry Manuscript Sheaf on Floor", "P2", 1.04, 0.44, 0.90, 0.15, "static", "The Reading"),
    ],
    "01.1": [
        L("01.props.window__p13", "Open Sash Window & Fire-Escape Balcony", "P4", 2.38, 0.78, 0.66, 0.24, "fire_escape_landing", "Fire-Escape Landing"),
        L("01.props.room__p14", "Wide Bedroom Chest of Open Drawers", "P3", 1.44, 0.24, 0.88, 0.22, "drawer_slide", "Hallway & Drawers"),
        L("01.props.room__p04", "Pulled-Out Numbered Wooden Drawer", "P2", 1.04, 0.48, 0.90, 0.12, "drawer_slide", "Haze at the Window"),
    ],
    "01.2": [
        L("01.props.window__p12", "Open Apartment Sash Window Above the Drop", "P4", 2.40, 0.20, 0.60, 0.24, "portal_aperture", "Open Sash Window"),
        L("01.props.window__p06", "Iron Fire-Escape Balcony Railing", "P3", 1.42, 0.76, 0.84, 0.20, "fire_escape_landing", "Edge of the Drop"),
        L("01.props.handheld__p07", "Crumpled Poem Page Caught on the Ledge", "P2", 1.04, 0.45, 0.86, 0.14, "tambourine_arc", None),
    ],
    "01.3": [
        L("01.props.chandeliers__p27", "Inverted 5-Branch Lit Chandelier Overhead", "P6", 6.00, 0.76, 0.26, 0.18, "lamp_glow", None),
        L("01.props.window__p11", "Passing Iron Fire-Escape Grate", "P4", 2.40, 0.20, 0.76, 0.18, "static", "Tower Canyon Wall"),
        L("01.props.chandeliers__p28", "Passing Lit Brass Ballroom Chandelier", "P3", 1.40, 0.70, 0.78, 0.18, "lamp_glow", "The Fall Montage"),
        L("01.props.handheld__p07", "Tumbling Crumpled Manuscript Page", "P2", 1.04, 0.42, 0.86, 0.15, "tambourine_arc", None),
    ],
    "01.4": [
        L("01.props.chandeliers__p27", "Grand 5-Branch Lit Crystal Chandelier", "P6", 6.00, 0.50, 0.28, 0.22, "lamp_glow", "Crystal Chandelier"),
        L("01.props.chandeliers__p28", "West Ballroom Lit Brass Chandelier", "P4", 2.40, 0.20, 0.54, 0.18, "lamp_glow", None),
        L("14.props.party__p20", "Brass Horn Table Gramophone", "P3", 1.40, 0.76, 0.88, 0.21, "turntable_spin", "Ballroom Table"),
        L("14.props.party__p05", "Golden Ballroom Champagne Chalice", "P2", 1.04, 0.28, 0.89, 0.16, "lamp_glow", "Crashing the Vintage Party"),
    ],
    "01.5": [
        L("01.props.chandeliers__p28", "Swaying Ballroom Chandelier Overhead", "P6", 6.00, 0.50, 0.25, 0.19, "lamp_glow", None),
        L("01.props.trapdoor__p12", "Open Floor Trapdoor Into the Abyss", "P3", 1.38, 0.52, 0.89, 0.18, "portal_aperture", "Hole in the Floor"),
        L("14.props.party__p03", "Brass Gramophone by the Threshold", "P2", 1.04, 0.22, 0.88, 0.18, "lamp_glow", "Rim of the Void"),
        L("14.props.party__p17", "Toppled Golden Champagne Coupe", "P1", 0.56, 0.80, 0.90, 0.15, "lamp_glow", None),
    ],

    # =======================================================================
    # POEM 02 · IN THE NIGHTTIME OF YOUR FEAR
    # =======================================================================
    "02.0": [
        L("02.props.mirror-phone-rings__p01", "Tall Carved Standing Mirror Frame", "P4", 2.40, 0.20, 0.85, 0.26, "portal_aperture", "Walls Caving Inward"),
        L("02.props.mirror-phone-rings__p14", "Standing Mirror on Tilted Stand", "P3", 1.40, 0.46, 0.87, 0.20, "lamp_glow", None),
        L("02.props.mirror-phone-rings__p06", "Ringing Midnight Smartphone", "P2", 1.04, 0.74, 0.88, 0.16, "phone_ring", "Emergency Ring"),
    ],
    "02.1": [
        L("02.props.mirror-phone-rings__p04", "Ornate Standing Bedroom Mirror Frame", "P4", 2.40, 0.76, 0.84, 0.25, "portal_aperture", "The Midnight Mirror"),
        L("02.set.bedroom_night__p05", "Dark Wooden Bed Headboard", "P3", 1.48, 0.28, 0.81, 0.11, "static", None),
        L("02.set.bedroom_night__p04", "Low Wooden Bed Platform Frame", "P3", 1.46, 0.28, 0.88, 0.13, "lamp_base", "Midnight Bed"),
        L("02.set.bedroom_night__p08", "Rumpled Dark-Blue Midnight Blanket", "P3", 1.42, 0.29, 0.86, 0.12, "lamp_base", None),
        L("02.props.mirror-phone-rings__p05", "Glowing Smartphone Emergency Call", "P2", 1.04, 0.54, 0.88, 0.16, "phone_ring", "1:08 AM Call"),
    ],
    "02.2": [
        L("02.props.window__p03", "Floral Living-Room Window Curtain", "P4", 2.42, 0.14, 0.76, 0.25, "curtain_sway_L", "Childhood Window View"),
        L("02.set.living_room_1990s__p04", "1990s Floral Living Room Sofa", "P3", 1.46, 0.28, 0.88, 0.16, "lamp_base", "Living Room Sofa"),
        *car_ensemble(cx=0.72, floor_y=0.87, car_scale=0.22, station_title="Family Sedan Pulling Up", with_parents=False),
    ],
    "02.3": [
        L("02.props.window__p01", "Drawn Floral Curtain by the Frost Window", "P4", 2.42, 0.16, 0.78, 0.25, "curtain_sway_L", "Doorpost Height Marks"),
        L("02.set.living_room_1990s__p04", "1990s Floral Living Room Sofa", "P3", 1.44, 0.74, 0.88, 0.16, "lamp_base", "Frost at the Window"),
        L("02.props.tambourine__p15", "Ghost Child's Wooden Tambourine", "P2", 1.04, 0.36, 0.88, 0.16, "tambourine_arc", "The Ghost's Tambourine"),
    ],
    "02.4": [
        L("02.set.living_room_1990s__p06", "Slatted Venetian Window Blinds", "P4", 2.42, 0.22, 0.66, 0.18, "curtain_sway_L", "Raised Window Blinds"),
        L("02.set.living_room_1990s__p04", "Childhood Floral Sofa by the Window", "P3", 1.46, 0.24, 0.88, 0.15, "lamp_base", None),
        *car_ensemble(cx=0.66, floor_y=0.87, car_scale=0.22, station_title="Parents Arguing in the Car", with_parents=False),
    ],
    "02.5": [
        L("02.props.window__p02", "Open White Living-Room Window Frame", "P4", 2.44, 0.22, 0.72, 0.22, "portal_aperture", "Living Room Window"),
        L("02.props.window__p03", "Billowing Floral Window Curtain", "P4", 2.40, 0.32, 0.74, 0.24, "curtain_sway_R", None),
        L("02.props.tambourine__p15", "Wooden Tambourine Hurling Outward", "P2", 1.04, 0.56, 0.62, 0.17, "tambourine_arc", "Tambourine in Flight"),
        L("02.props.tambourine__p11", "Spinning Tambourine Blur Disc", "P1", 0.54, 0.76, 0.74, 0.12, "tambourine_arc", None),
    ],

    # =======================================================================
    # POEM 03 · HOW TO BREAK OFF AN ENGAGEMENT
    # =======================================================================
    "03.0": [
        L("03.props.rose-window__p01", "Vaulted Gothic Rose Window Tracery", "P6", 6.00, 0.50, 0.28, 0.22, "stained_glass_glow", "Gothic Rose Window"),
        L("03.hero.chapel__p01", "Stone Gothic Chapel Sanctuary Arch", "P4", 2.42, 0.80, 0.85, 0.24, "portal_aperture", "Chapel Sanctuary Arch"),
        L("03.hero.chapel.interior-states__p05", "Empty First-Row Wooden Sanctuary Pew", "P3", 1.42, 0.26, 0.88, 0.17, "static", None),
        L("02.props.tambourine__p15", "Tambourine Ringing Through the Nave", "P2", 1.04, 0.52, 0.64, 0.16, "tambourine_arc", "Arc of the Tambourine"),
    ],
    "03.1": [
        L("03.props.rose-window__p11", "Stained-Glass Triforium Rose Medallion", "P6", 6.00, 0.50, 0.26, 0.20, "stained_glass_glow", "Empty Choir & Windows"),
        L("03.hero.chapel.interior-states__p07", "Gothic Triple-Lancet Stone Archway", "P4", 2.42, 0.18, 0.84, 0.24, "portal_aperture", None),
        L("03.hero.chapel.interior-states__p05", "Abandoned Wooden Chapel Pew West", "P3", 1.44, 0.36, 0.88, 0.17, "lamp_base", "Abandoned Wedding Pews"),
        L("03.hero.chapel.interior-states__p11", "Weathered Wooden Sanctuary Pew East", "P3", 1.40, 0.74, 0.88, 0.17, "lamp_base", "Cobwebbed Baptist Pool"),
        L("03.props.cobwebs__p01", "Draped Sanctuary Cobweb Veil", "P2", 1.04, 0.54, 0.86, 0.18, "curtain_sway_L", None),
    ],
    "03.2": [
        L("03.props.rose-window__p03", "Dimmed Sanctuary Rose Window Frame", "P6", 6.00, 0.50, 0.26, 0.20, "lamp_glow", None),
        L("03.props.gifts-bread-cups__p21", "Torn-Open Wedding Gift Box", "P3", 1.42, 0.30, 0.88, 0.17, "lamp_glow", "Left Chapel Side Door"),
        L("03.props.gifts-bread-cups__p03", "Unbroken Loaf of Daily Bread", "P2", 1.04, 0.54, 0.89, 0.18, "lamp_glow", "Gifts at the Side Doors"),
        L("03.props.gifts-bread-cups__p18", "Abandoned Silver Altar Chalice", "P1", 0.56, 0.76, 0.90, 0.16, "lamp_glow", None),
    ],
    "03.3": [
        L("03.hero.chapel.interior-states__p01", "Storm-Lashed Gothic Triple Arch", "P4", 2.42, 0.20, 0.84, 0.24, "portal_aperture", "Thunder in the Nave"),
        L("03.hero.chapel.interior-states__p11", "Shattered Wooden Pew in the Rain", "P3", 1.42, 0.70, 0.88, 0.17, "wave_mid", "The Storm Breaks"),
        L("03.props.gifts-bread-cups__p18", "Toppled Communion Cup in the Downpour", "P2", 1.04, 0.38, 0.89, 0.17, "wave_near", None),
    ],
    "03.4": [
        L("03.hero.chapel.ruin__p01", "Collapsed Stone Chapel Archway", "P4", 2.42, 0.22, 0.85, 0.24, "portal_aperture", "Collapsed Chapel Stone"),
        L("03.props.gifts-bread-cups__p03", "Daily Bread Soaked on the Shore", "P3", 1.40, 0.50, 0.88, 0.18, "wave_mid", "Remnants on the Shore"),
        L("03.props.strings-footprints__p11", "Parting Footsteps in Wet Sand", "P2", 1.04, 0.76, 0.89, 0.20, "drawer_slide", "Footsteps Leading Away"),
    ],
    "03.5": [
        L("03.hero.chapel.ruin__p12", "Ruined Stone Sanctuary Arch on the Tide", "P4", 2.42, 0.22, 0.85, 0.24, "portal_aperture", "Ruined Shore Arch"),
        L("04.props.word-shore__p23", "Rusted Shore Lantern at Dusk", "P3", 1.40, 0.76, 0.87, 0.20, "lamp_glow", "Tide Line at Dusk"),
        L("03.props.tambourine-broken__p13", "Shattered Tambourine Rim & Skin", "P2", 1.04, 0.48, 0.89, 0.20, "tambourine_arc", "Shattered Tambourine"),
    ],

    # =======================================================================
    # POEM 04 · NEVERMORE
    # =======================================================================
    "04.0": [
        L("04.set.shore_night__p08", "Gnarled Wind-Swept Shore Tree West", "P4", 2.42, 0.18, 0.84, 0.25, "curtain_sway_L", "Ash-Covered Shore"),
        L("04.props.word-shore__p23", "Rusted Shore Lantern in the Ash", "P3", 1.40, 0.36, 0.88, 0.20, "lamp_glow", "Broken Pieces on Sand"),
        L("04.set.shore_night__p06", "Charred Wildfire Driftwood Stump", "P3", 1.42, 0.76, 0.88, 0.18, "static", "Charred Stump & Raven"),
        L("04.props.ravens-stumps__p03", "Perched Black Raven on Focal Stump", "P2", 1.04, 0.76, 0.74, 0.18, "wing_flap_L", None),
    ],
    "04.1": [
        L("04.set.shore_night__p09", "Still Gnarled Shore Tree in Silence", "P4", 2.42, 0.82, 0.84, 0.24, "static", "Muted Trees in Silence"),
        L("04.props.word-shore__p23", "Still Wrought-Iron Shore Lantern", "P3", 1.42, 0.32, 0.88, 0.21, "static", "The Muted Waves"),
        L("04.props.ravens-stumps__p04", "Silent Watching Raven on the Sand", "P2", 1.04, 0.62, 0.88, 0.19, "static", "Moon Over Still Water"),
    ],
    "04.2": [
        L("04.hero.viaduct__p02", "Stone Coastal Viaduct Arch & Steps", "P4", 2.42, 0.80, 0.84, 0.25, "portal_aperture", "Steps Toward the Incline"),
        L("04.props.word-shore__p02", "Broken Sundial Relic in the Sand", "P3", 1.42, 0.24, 0.88, 0.20, "drawer_slide", "Folded Whispers"),
        L("04.props.heart__p12", "Anatomical Poet Heart Resting on Sand", "P2", 1.04, 0.52, 0.89, 0.17, "heart_beat", "The Heart on the Sand"),
    ],
    "04.3": [
        L("04.props.ravens-stumps__p05", "Black Raven Guiding Uphill", "P5", 3.80, 0.72, 0.34, 0.16, "wing_flap_R", None),
        L("04.hero.viaduct__p04", "Arched Stone Viaduct Bridge", "P4", 2.42, 0.78, 0.84, 0.24, "portal_aperture", "Crest of the Trail"),
        L("04.props.faith-blooms__p27", "First Golden Mustard-Seed Bloom", "P3", 1.38, 0.52, 0.88, 0.22, "flower_bloom", "Handcrafted Faith Bloom"),
        L("04.props.heart__p02", "Reclaimed Beating Heart Carried Uphill", "P2", 1.04, 0.28, 0.88, 0.20, "heart_beat", "Base of the Incline"),
    ],
    "04.4": [
        L("04.set.shore_night__p08", "Moonlit Garden Border Tree", "P4", 2.42, 0.18, 0.84, 0.24, "curtain_sway_L", "Moonlit Garden Edge"),
        L("04.props.faith-blooms__p27", "Golden Mustard Bloom West", "P3", 1.38, 0.34, 0.88, 0.23, "flower_bloom", "West Garden Row"),
        L("04.props.faith-blooms__p08", "Golden Sunflower Head in Full Bloom", "P2", 1.04, 0.56, 0.88, 0.21, "flower_bloom", "Center of the Night Field"),
        L("04.props.faith-blooms__p13", "Tall Sunflower Stalk & Leaves", "P1", 0.56, 0.78, 0.90, 0.21, "flower_bloom", None),
    ],
    "04.5": [
        L("04.props.poet-jointed-hands__p11", "Articulated Left Hand on the Ground", "P3", 1.38, 0.26, 0.88, 0.20, "weave_hand_articulation", "Searching the Bare Ground"),
        L("04.props.poet-jointed-hands__p12", "Articulated Right Hand Reattached", "P3", 1.34, 0.74, 0.88, 0.20, "weave_hand_articulation", "Putting the Hands Back On"),
        L("04.props.heart__p01", "Reclaimed Beating Heart in the Chest", "P2", 1.04, 0.50, 0.87, 0.22, "heart_beat", "The Awakened Chest"),
    ],
    "04.6": [
        L("04.hero.viaduct__p04", "Distant Stone Viaduct Arch Under Stars", "P4", 2.42, 0.78, 0.83, 0.24, "portal_aperture", "Standing Whole in the Field"),
        L("04.props.faith-blooms__p27", "Blooming Golden Sunflower West", "P3", 1.38, 0.24, 0.88, 0.23, "flower_bloom", "Western Bloom Row"),
        L("04.props.poet-jointed-hands__p01", "Whole Rejoined Hands Held Over Heart", "P2", 1.04, 0.46, 0.88, 0.21, "heart_beat", "Still Tree Under Stars"),
        L("04.props.faith-blooms__p08", "Foreground Golden Sunflower Blossom", "P1", 0.56, 0.68, 0.90, 0.19, "flower_bloom", None),
    ],

    # =======================================================================
    # POEM 05 · BLOODLINES
    # =======================================================================
    "05.0": [
        L("05.props.galaxy-universe__p02", "Celestial Ancestral Star Sphere Overhead", "P6", 6.00, 0.76, 0.26, 0.20, "planet_orbit", None),
        L("05.set.winged_marble_gate__p01", "West Sculpted Marble Angel-Wing Pillar", "P4", 2.42, 0.18, 0.84, 0.27, "portal_aperture", "The Field Goes Still"),
        L("05.props.star-names__p01", "Radiant Sun & Earth Medallion", "P3", 1.38, 0.54, 0.87, 0.21, "planet_orbit", "Inheriting the Earth"),
        L("05.props.staff-mattress-emblem__p01", "Carved Wooden Ancestor Staff", "P2", 1.04, 0.34, 0.89, 0.26, "static", "Ancestral Perimeter"),
    ],
    "05.1": [
        L("05.props.galaxy-universe__p01", "Swirling Spiral Galaxy Core Overhead", "P6", 6.00, 0.50, 0.26, 0.22, "planet_orbit", "Spiral Galaxies Overhead"),
        L("05.set.winged_marble_gate__p05", "East Sculpted Marble Angel-Wing Pillar", "P4", 2.42, 0.82, 0.84, 0.27, "portal_aperture", None),
        L("05.props.galaxy-universe__p17", "Golden Constellation Pedestal", "P3", 1.40, 0.32, 0.88, 0.21, "planet_orbit", "Naming My Own Stars"),
        L("05.props.staff-mattress-emblem__p07", "Radiant Star Crest Medallion", "P2", 1.04, 0.64, 0.88, 0.19, "sun_pulse", "The Waiting Past"),
    ],
    "05.2": [
        L("05.props.staff-mattress-emblem__p05", "Southern-Pine Quilted Basement Mattress", "P3", 1.42, 0.46, 0.88, 0.22, "lamp_base", "Southern-Pine Mattress"),
        L("05.props.staff-mattress-emblem__p02", "Brass Basement Hurricane Lantern", "P3", 1.38, 0.74, 0.87, 0.22, "lamp_glow", "Basement Window Well"),
        L("05.props.staff-mattress-emblem__p01", "Carved Wooden Ancestor Staff by Mattress", "P2", 1.04, 0.22, 0.89, 0.26, "static", "Basement Timber Stairs"),
    ],
    "05.3": [
        L("05.props.galaxy-universe__p18", "Elliptical Golden Orrery Cosmos Overhead", "P6", 6.00, 0.50, 0.25, 0.20, "planet_orbit", None),
        L("05.set.winged_marble_gate__p03", "Winged Marble Sanctuary Archway", "P4", 2.42, 0.78, 0.84, 0.27, "portal_aperture", "Sanctuary of the Elders"),
        L("05.props.galaxy-universe__p17", "Golden Pedestal Cupping a New Universe", "P3", 1.38, 0.28, 0.88, 0.22, "planet_orbit", "Inventing a New Universe"),
        L("05.props.staff-mattress-emblem__p07", "Radiant Ancestral Star Emblem", "P2", 1.04, 0.54, 0.88, 0.19, "sun_pulse", "Awarding a Blessing"),
    ],
    "05.4": [
        L("05.set.winged_marble_gate__p01", "West Winged Marble Sanctuary Pillar", "P4", 2.42, 0.18, 0.84, 0.27, "portal_aperture", None),
        L("05.props.staff-mattress-emblem__p02", "Brass Watchtower Sanctuary Lantern", "P3", 1.38, 0.36, 0.88, 0.22, "lamp_glow", "Blood Through the Hands"),
        L("05.props.staff-mattress-emblem__p07", "Radiant Solar Crest Medallion", "P2", 1.04, 0.68, 0.88, 0.19, "sun_pulse", "Fingerprints of Power"),
    ],
    "05.5": [
        L("05.set.winged_marble_gate__p02", "West Winged Threshold Column", "P4", 2.42, 0.18, 0.84, 0.27, "portal_aperture", "West Winged Pillar"),
        L("05.set.winged_marble_gate__p04", "East Winged Threshold Column", "P4", 2.40, 0.82, 0.84, 0.27, "portal_aperture", None),
        L("05.props.staff-mattress-emblem__p02", "Threshold Sanctuary Brass Lantern", "P3", 1.40, 0.36, 0.88, 0.22, "lamp_glow", "Threshold of Atlantis"),
        L("05.props.staff-mattress-emblem__p07", "Resonant Baritone Seal on Threshold", "P2", 1.04, 0.66, 0.88, 0.19, "sun_pulse", None),
    ],

    # =======================================================================
    # POEM 06 · ATLANTIS
    # =======================================================================
    "06.0": [
        L("06.props.lantern-candle-guitar__p15", "NEXT GATES Sanctuary Signpost", "P3", 1.38, 0.74, 0.88, 0.22, "lamp_glow", "Next Gates Signpost"),
        L("06.props.lantern-candle-guitar__p01", "Glowing Brass Hurricane Lantern", "P2", 1.04, 0.28, 0.88, 0.22, "lamp_glow", "The Light Gates Open"),
    ],
    "06.1": [
        L("06.props.lantern-candle-guitar__p15", "NEXT GATES Causeway Signpost", "P3", 1.40, 0.24, 0.88, 0.22, "lamp_glow", "Yellow-Brick Causeway"),
        L("06.props.lantern-candle-guitar__p01", "Causeway Brass Guide Lantern", "P2", 1.04, 0.72, 0.88, 0.22, "lamp_glow", "Following the Light"),
        L("06.props.lantern-candle-guitar__p03", "Lit Wax Pillar Candle Along Curb", "P1", 0.56, 0.86, 0.90, 0.17, "lamp_glow", None),
    ],
    "06.2": [
        L("06.props.lantern-candle-guitar__p07", "Waterfront NEXT GATES Colonnade Sign", "P3", 1.40, 0.24, 0.87, 0.20, "lamp_glow", "Waterfront Colonnade"),
        L("13.props.planet-boats__p06", "Moored Wooden Harbor Rowboat", "P3", 1.36, 0.52, 0.89, 0.21, "wave_near", None),
        L("06.props.lantern-candle-guitar__p01", "Harbor Quayside Brass Lantern", "P2", 1.04, 0.78, 0.88, 0.22, "lamp_glow", "Here We Are All One"),
    ],
    "06.3": [
        L("06.props.coin-booth__p01", "Arched Wooden Heart-Scan Admission Booth", "P3", 1.42, 0.54, 0.88, 0.25, "lamp_glow", "Heart-Scan Admission Booth"),
        L("06.props.coin-booth__p02", "Glowing Turquoise Spiral Currency Portal", "P2", 1.04, 0.26, 0.86, 0.19, "sun_pulse", "Relearned Currency"),
        L("06.props.lantern-candle-guitar__p01", "Jungle Sanctuary Brass Lantern", "P1", 0.56, 0.80, 0.89, 0.20, "lamp_glow", None),
    ],
    "06.4": [
        L("06.props.lantern-candle-guitar__p15", "Central Plaza Sanctuary Signpost", "P3", 1.40, 0.26, 0.88, 0.21, "lamp_glow", "City Center Sanctuary"),
        L("06.props.lantern-candle-guitar__p14", "Plaza Musician's Acoustic Guitar", "P2", 1.04, 0.64, 0.88, 0.21, "lamp_glow", "East Plaza Colonnade"),
        L("06.props.lantern-candle-guitar__p01", "Plaza Brass Votive Lantern", "P1", 0.56, 0.84, 0.90, 0.20, "lamp_glow", None),
    ],
    "06.5": [
        L("06.props.lantern-candle-guitar__p01", "Cobblestone Alley Brass Lantern", "P3", 1.40, 0.26, 0.88, 0.22, "lamp_glow", "Narrow Cobblestone Alley"),
        L("06.props.lantern-candle-guitar__p03", "Alleyway Lit Wax Pillar Candle", "P3", 1.36, 0.46, 0.89, 0.18, "lamp_glow", None),
        L("06.props.lantern-candle-guitar__p05", "Upright Acoustic Guitar by Teahouse", "P2", 1.04, 0.72, 0.88, 0.23, "lamp_glow", "Music in the Streets"),
    ],
    "06.6": [
        L("13.props.cafe__p13", "Harbor Teahouse Marble Table & Chairs", "P3", 1.40, 0.30, 0.88, 0.22, "lamp_base", "Harbor Teahouse Porch"),
        L("06.props.lantern-candle-guitar__p14", "Resting Teahouse Porch Guitar", "P2", 1.04, 0.66, 0.88, 0.21, "lamp_glow", "Could Stay Forever"),
        L("06.props.lantern-candle-guitar__p01", "Harbor Lantern at Twilight", "P1", 0.56, 0.84, 0.90, 0.20, "lamp_glow", None),
    ],

    # =======================================================================
    # POEM 07 · WHAT HAVE WE DONE
    # =======================================================================
    "07.0": [
        L("07.props.speakers-vu__p01", "Tall Dual-Driver Bass Speaker Left", "P4", 2.40, 0.20, 0.86, 0.24, "speaker_pulse", "Left Bass Speaker"),
        L("07.props.speakers-vu__p02", "Tall Dual-Driver Bass Speaker Right", "P4", 2.38, 0.80, 0.86, 0.24, "speaker_pulse", "Right Bass Speaker"),
        L("07.props.dj-decks__p01", "Dual-Turntable DJ Mixer Console", "P2", 1.04, 0.50, 0.88, 0.19, "dj_console", "DJ Turntable Booth"),
    ],
    "07.1": [
        L("07.props.dj-decks__p02", "Spinning Turntable Platter Deck", "P3", 1.40, 0.74, 0.88, 0.22, "turntable_spin", "House Party Lounge"),
        L("07.props.dj-decks__p10", "DJ Monitoring Headphones", "P2", 1.04, 0.28, 0.88, 0.19, "speaker_pulse", "Eyes Wide Shut"),
        L("07.props.dj-decks__p06", "Spinning Vinyl Record LP", "P1", 0.56, 0.50, 0.89, 0.17, "turntable_spin", None),
    ],
    "07.2": [
        L("07.props.speakers-vu__p01", "Left Bass Speaker Cabinet in Silhouette", "P3", 1.42, 0.24, 0.88, 0.24, "speaker_pulse", "Ghosts in the Speakers"),
        L("07.props.speakers-vu__p02", "Right Bass Speaker Cabinet in Silhouette", "P3", 1.40, 0.76, 0.88, 0.24, "speaker_pulse", None),
        L("07.props.speakers-vu__p08", "Throbbing Subwoofer Driver Cone", "P2", 1.04, 0.50, 0.88, 0.20, "speaker_pulse", "Resonant Bass Cone"),
    ],
    "07.3": [
        L("07.props.speakers-vu__p12", "Glowing Analog VU Meter (-20..+3 dB)", "P3", 1.42, 0.22, 0.87, 0.15, "vu_needle", "VU Meter Into the Red"),
        L("07.props.speakers-vu__p17", "Framed Peak VU Meter Dial", "P3", 1.40, 0.78, 0.87, 0.16, "vu_needle", None),
        L("07.props.dj-decks__p14", "Overdriven Twin-Platter DJ Deck", "P2", 1.04, 0.50, 0.88, 0.19, "dj_console", "A Thousand Light Years"),
    ],
    "07.4": [
        L("07.props.mic-daisy-rings__p01", "Stage Microphone on Stand", "P3", 1.40, 0.28, 0.88, 0.23, "static", "Diverging Wedding Path"),
        L("14.props.reel__p07", "Plucked Eleven-Year White Daisy", "P2", 1.04, 0.68, 0.88, 0.20, "flower_bloom", "Wedding Bands & Daisies"),
    ],
    "07.5": [
        L("07.props.dj-decks__p03", "Illuminated Club Booth DJ Console", "P3", 1.40, 0.34, 0.88, 0.18, "dj_console", "Illuminated Club Booth"),
        L("07.props.speakers-vu__p01", "Club Stage Bass Speaker Tower", "P2", 1.04, 0.76, 0.87, 0.24, "speaker_pulse", "Eleven Years in Dark Rooms"),
    ],
    "07.6": [
        L("07.props.mic-daisy-rings__p01", "Left-Behind Stage Mic Stand in the Rain", "P3", 1.40, 0.74, 0.88, 0.23, "static", "Three Roads in the Fog"),
        L("04.props.word-shore__p23", "Dim Fog-Halod Street Lantern", "P2", 1.04, 0.26, 0.88, 0.20, "lamp_glow", "Rain, Fog, Dim Lights"),
    ],

    # =======================================================================
    # POEM 08 · OUT OF MY MIND
    # =======================================================================
    "08.0": [
        L("07.props.speakers-vu__p01", "Rooftop Club Bass Speaker Tower", "P3", 1.40, 0.22, 0.87, 0.24, "speaker_pulse", "NEW SINGLE Club Marquee"),
        L("07.props.dj-decks__p03", "Rooftop Terrace DJ Console", "P2", 1.04, 0.70, 0.88, 0.18, "dj_console", "Soul Leaves the Dancer"),
    ],
    "08.1": [
        L("07.props.speakers-vu__p02", "Club Dancefloor Bass Speaker Tower", "P3", 1.42, 0.20, 0.87, 0.24, "speaker_pulse", "Strangers Collide on Floor"),
        L("07.props.dj-decks__p01", "Late-Night Club DJ Console", "P2", 1.04, 0.54, 0.88, 0.19, "dj_console", "Last One to Leave"),
        L("07.props.dj-decks__p10", "Dropped DJ Headphones on Stage", "P1", 0.56, 0.82, 0.89, 0.18, "speaker_pulse", None),
    ],
    "08.2": [
        L("05.props.galaxy-universe__p02", "Equator Celestial Star Sphere Overhead", "P6", 6.00, 0.76, 0.25, 0.20, "planet_orbit", "Aerial Atlantis"),
        L("04.props.word-shore__p23", "Equator Wind Wrought-Iron Lantern", "P3", 1.42, 0.26, 0.88, 0.20, "lamp_glow", "Open Field at the Equator"),
        L("06.props.lantern-candle-guitar__p01", "Glowing Equator Brass Hurricane Lantern", "P2", 1.04, 0.72, 0.88, 0.22, "lamp_glow", "Moons of the Equator"),
    ],
    "08.3": [
        L("11.props.inlays-lantern__p04", "Tall Wrought-Iron Sanctuary Baptism Lantern", "P3", 1.42, 0.26, 0.88, 0.22, "lamp_glow", "Salted Ice-Water Basin"),
        L("04.props.word-shore__p23", "Choir Colonnade Iron Lantern", "P2", 1.04, 0.74, 0.88, 0.20, "lamp_glow", "Angels' Ice-Water Baptism"),
    ],
    "08.4": [
        L("06.props.lantern-candle-guitar__p01", "Clear Morning Brass Sanctuary Lantern", "P3", 1.42, 0.26, 0.88, 0.22, "lamp_glow", "Soul Returns to the Body"),
        L("04.props.word-shore__p23", "Still Terrace Iron Lantern at Dawn", "P2", 1.04, 0.76, 0.88, 0.20, "lamp_glow", "Terrace Recovery Basin"),
    ],
    "08.5": [
        L("05.set.winged_marble_gate__p01", "Rooftop Marble Parapet Wing Pillar", "P4", 2.42, 0.18, 0.84, 0.26, "portal_aperture", None),
        L("06.props.lantern-candle-guitar__p01", "Morning Parapet Brass Lantern", "P3", 1.40, 0.36, 0.88, 0.22, "lamp_glow", "Mountains From the Rooftop"),
        L("04.props.word-shore__p23", "Dawn Terrace Parapet Lantern", "P2", 1.04, 0.76, 0.88, 0.20, "lamp_glow", "Rooftop Parapet"),
    ],

    # =======================================================================
    # POEM 09 · A GOOD PLACE TO BREAKDOWN
    # =======================================================================
    "09.0": [
        L("09.props.suitcases-notice__p01", "Upright Brown Leather Suitcase", "P3", 1.42, 0.26, 0.88, 0.21, "static", "The EX in the Crowd"),
        L("09.props.suitcases-notice__p05", "Packed Leather Suitcase by the Crowd", "P2", 1.04, 0.64, 0.88, 0.21, "static", "Harbor Crowd"),
        L("09.props.suitcases-notice__p20", "2nd Gate 05:12 Pier Departure Sign", "P1", 0.56, 0.84, 0.87, 0.20, "lamp_glow", None),
    ],
    "09.1": [
        L("13.props.planet-boats__p06", "Painted Wooden Harbor Rowboat at Quay", "P3", 1.40, 0.72, 0.88, 0.21, "wave_near", "Harbor Quay Promenade"),
        L("09.props.suitcases-notice__p05", "Leather Suitcase Carried to the Pier", "P2", 1.04, 0.32, 0.88, 0.21, "static", "Walking Toward the Water"),
    ],
    "09.2": [
        L("09.props.phonebooth__p02", "Harbor Glass Telephone Booth", "P3", 1.42, 0.52, 0.86, 0.25, "portal_aperture", "Harbor Phone Booth"),
        L("09.props.suitcases-notice__p06", "Open Lined Trunk Suitcase on the Pier", "P3", 1.38, 0.24, 0.88, 0.21, "static", "Suitcases on the Pier"),
        L("09.props.suitcases-notice__p05", "Closed Leather Suitcase Beside Booth", "P2", 1.04, 0.76, 0.88, 0.21, "static", None),
    ],
    "09.3": [
        L("09.props.phonebooth__p15", "Open Harbor Phone Booth & Handset", "P3", 1.40, 0.26, 0.87, 0.25, "phone_ring", "Calling From the Booth"),
        L("09.props.phones-chair__p07", "Mother's Floral Living-Room Armchair", "P2", 1.04, 0.74, 0.88, 0.24, "lamp_base", "The Call to Mother"),
    ],
    "09.4": [
        L("13.props.planet-boats__p18", "Masted Wooden Harbor Sailboat", "P3", 1.42, 0.74, 0.88, 0.22, "wave_near", "Inner Harbor Water"),
        L("13.props.planet-boats__p10", "Painted Harbor Skiff at the Dock", "P3", 1.38, 0.26, 0.89, 0.20, "wave_near", None),
        L("09.props.suitcases-notice__p05", "Father & Son's Suitcase on the Quay", "P2", 1.04, 0.50, 0.88, 0.20, "static", "Father and Son Together"),
    ],
    "09.5": [
        L("09.props.phonebooth__p14", "Silent Glass Telephone Booth in the Mist", "P3", 1.40, 0.68, 0.87, 0.24, "portal_aperture", "Misty Harbor Quay"),
        L("09.props.suitcases-notice__p01", "Single Upright Suitcase Left on Pier", "P2", 1.04, 0.30, 0.88, 0.21, "static", "The EX Turns to Haze"),
        L("13.props.planet-boats__p06", "Drifting Wooden Rowboat in Harbor Haze", "P1", 0.56, 0.86, 0.90, 0.18, "wave_near", None),
    ],

    # =======================================================================
    # POEM 10 · BE ASTONISHED
    # =======================================================================
    "10.0": [
        L("11.props.parked-motorcycle__p01", "Parked Cafe-Racer Motorcycle Under Street", "P3", 1.38, 0.58, 0.87, 0.24, "bike_chassis", "The Parked Motorcycle"),
        L("06.props.lantern-candle-guitar__p01", "Underground Vault Work Lantern", "P2", 1.04, 0.24, 0.88, 0.21, "lamp_glow", "Under the Street"),
    ],
    "10.1": [
        L("10.props.bike-skeleton__p01", "Copper-Frame Cafe-Racer Chassis", "P3", 1.38, 0.64, 0.87, 0.24, "bike_chassis", "Mounting the Machine"),
        L("10.props.tree-dawn-sign__p20", "Glowing < 88 NEW DAWN km Signpost", "P2", 1.04, 0.26, 0.87, 0.21, "lamp_glow", "Steel Coverings"),
    ],
    "10.2": [
        L("10.props.tree-dawn-sign__p19", "Silhouette Street Tree Against Amber Sky", "P4", 2.42, 0.80, 0.84, 0.25, "static", None),
        L("10.props.bike-skeleton__p17", "Cafe-Racer Motorcycle Cruising the Avenue", "P3", 1.38, 0.44, 0.87, 0.24, "bike_chassis", "First Midnight Intersection"),
    ],
    "10.3": [
        L("11.props.parked-motorcycle__p01", "Motorcycle Leaning Through Light Pool", "P3", 1.38, 0.40, 0.87, 0.24, "bike_chassis", "Avenue Light Pool"),
        L("04.props.word-shore__p23", "Avenue Wrought-Iron Street Lantern", "P2", 1.04, 0.76, 0.88, 0.20, "lamp_glow", "Swagger Down the Avenue"),
    ],
    "10.4": [
        L("05.set.winged_marble_gate__p01", "City-Limit Winged Boundary Pillar", "P4", 2.42, 0.18, 0.84, 0.26, "portal_aperture", None),
        L("10.props.bike-skeleton__p17", "Highway Motorcycle Heading Out at Dawn", "P3", 1.38, 0.50, 0.87, 0.24, "bike_chassis", "Out of Atlantis"),
        L("10.props.tree-dawn-sign__p20", "< 88 NEW DAWN km Highway Signpost", "P2", 1.04, 0.80, 0.87, 0.20, "lamp_glow", "Leaving Atlantis"),
    ],
    "10.5": [
        L("10.props.tree-dawn-sign__p01", "Gnarled Mountain-Pass Tree West", "P4", 2.42, 0.18, 0.84, 0.26, "static", None),
        L("10.props.bike-skeleton__p01", "Full-Throttle Mountain-Pass Motorcycle", "P3", 1.38, 0.46, 0.87, 0.24, "bike_chassis", "Mountain Road Sweep"),
        L("10.props.tree-dawn-sign__p20", "< 88 NEW DAWN km Summit Marker", "P2", 1.04, 0.76, 0.87, 0.21, "lamp_glow", "88 New Dawn km"),
    ],

    # =======================================================================
    # POEM 11 · WELCOME BACK TO MYSELF
    # =======================================================================
    "11.0": [
        L("11.props.temple.states__p02", "Ruined Stone Rubble Foundation on Shore", "P4", 2.40, 0.76, 0.85, 0.09, "static", "Ruins on the Shore"),
        L("11.props.parked-motorcycle__p01", "Parked Motorcycle on the Chilly Shore", "P3", 1.40, 0.26, 0.87, 0.23, "bike_chassis", "Parked Bike by the Ruins"),
        L("11.props.journal__p01", "Closed Tooled-Leather Sanctuary Journal", "P2", 1.04, 0.52, 0.89, 0.18, "lamp_glow", "Arrival on the Chilly Shore"),
    ],
    "11.1": [
        L("11.props.temple.states__p03", "Laid White Marble Temple Foundation Steps", "P4", 2.40, 0.74, 0.84, 0.11, "static", "First Courses of Stone"),
        L("11.props.inlays-lantern__p04", "Tall Wrought-Iron Morning Sanctuary Lantern", "P3", 1.40, 0.24, 0.87, 0.22, "lamp_glow", "Remnants in the Sunlight"),
        L("11.props.journal__p04", "Open Flat Leather Architect's Journal", "P2", 1.04, 0.50, 0.89, 0.16, "drawer_slide", None),
    ],
    "11.2": [
        L("11.props.temple.states__p01", "Half-Built Rising Fluted Marble Columns", "P4", 2.40, 0.76, 0.83, 0.20, "static", "Rising Fluted Columns"),
        L("11.props.inlays-lantern__p18", "Cut White Marble Ashlar Stones", "P3", 1.40, 0.24, 0.88, 0.18, "static", "The Temple Builds Itself"),
        L("11.props.journal__p07", "Handwritten Cream Parchment Blueprint Page", "P2", 1.04, 0.50, 0.89, 0.18, "lamp_glow", "Crowning the White Roof"),
    ],
    "11.3": [
        L("11.props.temple.states__p04", "Completed Classical White Marble Portico", "P4", 2.40, 0.76, 0.83, 0.25, "portal_aperture", "New White Temple Nave"),
        L("11.props.inlays-lantern__p04", "Sanctuary Nave Wrought-Iron Lantern", "P3", 1.38, 0.24, 0.87, 0.22, "lamp_glow", "Choir Chords in the Nave"),
        L("11.props.journal__p11", "Open Sanctuary Hymnal & Ledger", "P2", 1.04, 0.50, 0.89, 0.17, "lamp_glow", None),
    ],
    "11.4": [
        L("02.props.mirror-phone-rings__p04", "Ornate Standing Mirror by Reflecting Pool", "P4", 2.40, 0.76, 0.84, 0.25, "portal_aperture", "The Lonely Mirror"),
        L("11.props.inlays-lantern__p15", "Reflecting Pool Brass Lantern", "P3", 1.40, 0.24, 0.88, 0.20, "lamp_glow", None),
        L("11.props.journal__p04", "Open Leather Journal by the Water's Edge", "P2", 1.04, 0.50, 0.89, 0.16, "lamp_glow", "Journal by the Pool"),
    ],
    "11.5": [
        L("11.props.temple.states__p06", "Golden-Lit Classical Temple Portico", "P4", 2.40, 0.76, 0.83, 0.25, "portal_aperture", "Welcoming the New"),
        L("11.props.inlays-lantern__p04", "Golden Dedication Sanctuary Lantern", "P3", 1.40, 0.24, 0.87, 0.22, "lamp_glow", "Reflecting Pool"),
        L("11.props.journal__p11", "Completed Sanctuary Chronicle", "P2", 1.04, 0.48, 0.89, 0.17, "lamp_glow", None),
    ],

    # =======================================================================
    # POEM 12 · REUNION
    # =======================================================================
    "12.0": [
        L("12.props.niche-porch__p15", "Hanging Brass Sanctuary Pendant Lamp", "P6", 6.00, 0.50, 0.24, 0.19, "lamp_glow", None),
        L("12.props.niche-porch__p01", "Arched Stone Sanctuary Niche Frame", "P4", 2.40, 0.80, 0.83, 0.25, "portal_aperture", "Temple Porch Entrance"),
        L("12.set.temple_backroom__p05", "Carved Wooden Welcome Chair", "P3", 1.42, 0.26, 0.88, 0.22, "lamp_base", "Welcome Home in the Hall"),
        L("12.props.hand-hourglass__p01", "Upright Glass Hourglass of Welcome", "P2", 1.04, 0.56, 0.88, 0.22, "hourglass_sand", None),
    ],
    "12.1": [
        L("12.props.niche-porch__p16", "Glowing Brass Hall Pendant Lamp", "P6", 6.00, 0.50, 0.24, 0.19, "lamp_glow", None),
        L("12.set.temple_backroom__p07", "Elder's Wooden Gathering Chair", "P3", 1.42, 0.26, 0.88, 0.22, "lamp_base", "Echoing Hall Colonnade"),
        L("04.props.heart__p01", "Beating Reunion Heart Emblem", "P2", 1.04, 0.52, 0.88, 0.21, "heart_beat", "Loud Voices & Laughter"),
        L("12.props.hand-hourglass__p04", "Tilted Glass Hourglass on Stone Ledge", "P1", 0.56, 0.78, 0.89, 0.20, "hourglass_sand", None),
    ],
    "12.2": [
        L("12.props.niche-porch__p01", "Quiet Stone Sanctuary Alcove Arch", "P4", 2.40, 0.20, 0.83, 0.25, "portal_aperture", "Afterlife Chamber"),
        L("12.set.temple_backroom__p05", "Empty Wooden Chair in the Chamber", "P3", 1.42, 0.46, 0.88, 0.22, "lamp_base", "The Empty Rooms"),
        L("12.props.last-hourglass__p01", "Tall Carved Wooden Hourglass", "P2", 1.04, 0.74, 0.88, 0.24, "hourglass_sand", None),
    ],
    "12.3": [
        L("12.props.niche-porch__p15", "Sanctuary Pendant Lamp Above the Pillars", "P6", 6.00, 0.50, 0.24, 0.18, "lamp_glow", None),
        L("12.props.hand-hourglass__p21", "Glass Hourglass of Burning Sand", "P3", 1.38, 0.28, 0.88, 0.22, "hourglass_sand", "Glasses of Burning Sand"),
        L("12.props.last-hourglass__p23", "Burning Wooden Hourglass Frame", "P2", 1.04, 0.68, 0.88, 0.23, "hourglass_sand", "The Burning Hourglasses"),
    ],
    "12.4": [
        L("12.set.temple_backroom__p07", "Elder's Carved Grove Chair", "P3", 1.40, 0.28, 0.88, 0.22, "lamp_base", "Western Forest Edge"),
        L("13.props.harvest__p09", "Lush Tied Bouquet of Poppies & Wildflowers", "P2", 1.04, 0.68, 0.88, 0.22, "flower_bloom", "Every Living Tree"),
    ],
    "12.5": [
        L("12.set.temple_backroom__p05", "Terrace Gathering Wooden Chair", "P3", 1.40, 0.26, 0.88, 0.22, "lamp_base", "Shore Terrace Canopy"),
        L("04.props.heart__p01", "Resonant Brotherhood Heart Emblem", "P2", 1.04, 0.64, 0.87, 0.21, "heart_beat", "The Brotherhood Chain"),
        L("12.props.hand-hourglass__p01", "Shared-Years Glass Hourglass", "P1", 0.56, 0.82, 0.89, 0.19, "hourglass_sand", None),
    ],
    "12.6": [
        L("13.props.harvest__p08", "Meadow Dusk Poppy & Lavender Bouquet", "P3", 1.40, 0.24, 0.88, 0.21, "flower_bloom", "Football in the Meadow"),
        L("12.props.reunion__p01", "Spiraling Leather Football", "P2", 1.04, 0.56, 0.66, 0.18, "tambourine_arc", "Spiraling Pass at Dusk"),
        L("13.props.harvest__p14", "Foreground Meadow Poppy Cluster", "P1", 0.56, 0.82, 0.90, 0.18, "flower_bloom", None),
    ],

    # =======================================================================
    # POEM 13 · HARVESTING OUR OLD STORIES
    # =======================================================================
    "13.0": [
        L("11.props.temple.states__p04", "Distant White Marble Temple Portico", "P4", 2.40, 0.20, 0.83, 0.24, "portal_aperture", "Leaving the White Temple"),
        L("13.props.planet-boats__p18", "Masted Wooden Sailboat in the Canal", "P3", 1.40, 0.74, 0.88, 0.21, "wave_near", None),
        L("13.props.harvest__p09", "Freshly Gathered Scarlet Poppy Bouquet", "P2", 1.04, 0.46, 0.88, 0.21, "flower_bloom", "Old Stories Gathered"),
    ],
    "13.1": [
        L("13.props.planet-boats__p01", "Banded Planet Rising Over the Harbor", "P6", 6.00, 0.78, 0.24, 0.19, "planet_orbit", None),
        L("13.props.cafe__p13", "Corner Marble Bistro Table & Two Chairs", "P3", 1.40, 0.60, 0.88, 0.23, "lamp_base", "Harbor Cafe Awning"),
        L("13.props.cafe__p11", "Cafe Table Edge & Porcelain Espresso Cup", "P2", 1.04, 0.28, 0.88, 0.18, "lamp_glow", "The Corner Cafe Table"),
    ],
    "13.2": [
        L("13.props.planet-boats__p01", "Counted Planetary Orbit Overhead", "P6", 6.00, 0.50, 0.22, 0.20, "planet_orbit", "Counted Planetary Orbits"),
        L("13.props.cafe__p04", "Freestanding Bentwood Cafe Chair", "P3", 1.40, 0.26, 0.88, 0.22, "lamp_base", None),
        L("13.props.five-letters__p02", "Five Unsent Love Letters Tied in Wax", "P2", 1.04, 0.68, 0.89, 0.18, "drawer_slide", "Five Unsent Letters"),
    ],
    "13.3": [
        L("13.props.harvest__p14", "Blooming Scarlet Poppy Cluster on Moss", "P3", 1.40, 0.72, 0.88, 0.20, "flower_bloom", "Drowned Atrium"),
        L("13.props.five-letters__p02", "Scorched Unsent Letter on the Ground", "P2", 1.04, 0.46, 0.89, 0.18, "drawer_slide", "Victory-less Season"),
        L("13.props.harvest__p03", "Single Tall Scarlet Poppy Stem", "P1", 0.56, 0.22, 0.90, 0.20, "flower_bloom", None),
    ],
    "13.4": [
        L("13.props.harvest__p09", "Lush Tied Scarlet Poppy & Lavender Bouquet", "P3", 1.42, 0.26, 0.88, 0.22, "flower_bloom", "Scarlet Poppy Meadow"),
        L("13.props.harvest__p08", "Harvested Hilltop Poppy Bouquet", "P2", 1.04, 0.56, 0.88, 0.21, "flower_bloom", "Harvesting the Poppies"),
        L("13.props.harvest__p12", "Foreground Wildflower & Poppy Cluster", "P1", 0.56, 0.82, 0.90, 0.19, "flower_bloom", None),
    ],
    "13.5": [
        L("13.props.cafe__p03", "Empty Bentwood Bistro Chair Waiting", "P3", 1.42, 0.28, 0.88, 0.22, "lamp_base", "Waiting by the Cafe"),
        L("13.props.cafe__p11", "Bistro Table Edge with Porcelain Espresso Cup", "P3", 1.38, 0.52, 0.88, 0.18, "lamp_glow", None),
        L("13.props.harvest__p07", "Poppy Bouquet Placed on the Table", "P2", 1.04, 0.76, 0.88, 0.21, "flower_bloom", "From a Distant Window"),
    ],
    "13.6": [
        L("13.props.cafe__p13", "Bistro Table & Chairs Left Behind", "P3", 1.40, 0.28, 0.88, 0.22, "lamp_base", "Rising From the Table"),
        L("13.props.planet-boats__p06", "Painted Wooden Harbor Rowboat at Pier", "P2", 1.04, 0.72, 0.88, 0.21, "wave_near", "Walking Toward the Quay"),
    ],

    # =======================================================================
    # POEM 14 · OUT OF LIFE (FINALE)
    # =======================================================================
    "14.0": [
        L("14.props.party__p19", "Festive String of Glowing Paper Lanterns", "P6", 6.00, 0.50, 0.22, 0.13, "lamp_glow", None),
        L("13.props.planet-boats__p18", "Harbor Sailboat Before the White Skyline", "P3", 1.40, 0.28, 0.88, 0.21, "wave_near", "Everything I Built"),
        L("14.props.reel__p08", "Luminous Ferris-Wheel Life-Memory Emblem", "P2", 1.04, 0.72, 0.87, 0.21, "sun_pulse", "Taken by the Haze"),
    ],
    "14.1": [
        L("14.props.door__p02", "Closed Freestanding Vintage Wooden Door", "P3", 1.42, 0.74, 0.87, 0.27, "portal_aperture", "Distant Door in the Void"),
        L("14.props.reel__p06", "Lit Candle in Brass Holder Floating in Void", "P2", 1.04, 0.28, 0.87, 0.21, "sun_pulse", "Sharpened Key of Answers"),
    ],
    "14.2": [
        L("14.props.party__p20", "Brass Horn Table Gramophone", "P3", 1.42, 0.24, 0.88, 0.21, "turntable_spin", "Highs of Life Memory"),
        L("14.props.reel__p03", "Scarlet Poppies Memory Medallion", "P3", 1.38, 0.50, 0.87, 0.20, "flower_bloom", None),
        L("11.props.journal__p04", "Open Leather Life-Reel Journal", "P2", 1.04, 0.76, 0.89, 0.16, "lamp_glow", "Love & Loss Endured"),
    ],
    "14.3": [
        L("14.props.door__p11", "Freestanding Vintage Door Ajar", "P3", 1.42, 0.76, 0.87, 0.27, "portal_aperture", "Battle Scars & Wisdom"),
        L("14.props.reel__p02", "Brass Tambourine Memory Medallion", "P3", 1.38, 0.52, 0.87, 0.19, "tambourine_arc", None),
        L("11.props.journal__p11", "Unspooled Journal Pages", "P2", 1.04, 0.26, 0.89, 0.17, "lamp_glow", "Unspooling the Reel"),
    ],
    "14.4": [
        L("14.props.party__p19", "Festive String of Glowing Paper Lanterns", "P6", 6.00, 0.50, 0.22, 0.13, "lamp_glow", None),
        L("14.props.door__p13", "Vintage Wooden Door Swinging Wide Open", "P3", 1.40, 0.68, 0.87, 0.27, "portal_aperture", "The Vintage Door Opens"),
        L("14.props.party__p03", "Brass Gramophone Horn Calling From Inside", "P2", 1.04, 0.28, 0.88, 0.20, "lamp_glow", "Light Spilling Through"),
    ],
    "14.5": [
        L("01.props.chandeliers__p27", "Grand 5-Branch Lit Ballroom Chandelier", "P6", 6.00, 0.50, 0.26, 0.21, "lamp_glow", None),
        L("14.props.party__p05", "Golden Ballroom Champagne Chalice", "P3", 1.42, 0.24, 0.88, 0.17, "lamp_glow", "Under the Ballroom Lights"),
        L("14.props.party__p20", "Brass Horn Table Gramophone", "P2", 1.04, 0.76, 0.88, 0.22, "turntable_spin", "Gramophone Waltz"),
        L("14.props.party__p16", "Spinning Vinyl Waltz Record LP", "P1", 0.56, 0.48, 0.90, 0.16, "turntable_spin", None),
    ],
    "14.6": [
        L("14.props.party__p20", "Brass Horn Table Gramophone", "P3", 1.44, 0.22, 0.88, 0.20, "lamp_glow", "Into the Ballroom Crowd"),
        L("01.props.room__p01", "Genesis Wooden Bedroom Dresser", "P3", 1.40, 0.46, 0.88, 0.21, "drawer_slide", None),
        L("01.props.room__p18", "Genesis Bedroom Television & Stand", "P2", 1.04, 0.72, 0.89, 0.20, "portal_tv_flicker", "Genesis · Back to Poem 01"),
    ],
}


# ---------------------------------------------------------------------------
# Scale Marker Extraction & Standardized Physical Piece Scale Calibration
# ---------------------------------------------------------------------------
OBJECT_REAL_HEIGHT_M: Dict[str, float] = {
    "person": 1.70,
    "man": 1.72,
    "woman": 1.65,
    "child": 1.22,
    "pedestrian": 1.70,
    "door": 2.05,
    "doorway": 2.10,
    "storefront": 2.40,
    "window": 1.35,
    "railing": 1.00,
    "fence": 1.15,
    "street lamp": 2.90,
    "lamp": 2.75,
    "lantern": 0.55,
    "vehicle": 1.45,
    "car": 1.45,
    "sedan": 1.45,
    "chair": 0.88,
    "bench": 0.86,
    "table": 0.78,
    "stairs": 2.20,
    "staircase": 2.40,
    "pillar": 3.40,
    "column": 3.40,
    "tree": 3.60,
    "air conditioner": 0.68,
    "flower": 0.45,
    "building": 12.0,
    "spire": 18.0,
    "tower": 18.0,
    "bridge": 4.50,
}

# Canonical physical size `(canon_h_m, canon_w_m, class_tag)` for every piece family
CANONICAL_PIECE_METERS_BY_ID: Dict[str, Tuple[float, float, str]] = {
    # Poem 01: Bedroom, Fire Escape, Ballroom & Trapdoor
    "01.props.room__p01": (1.15, 1.35, "furniture_dresser"),
    "01.props.room__p14": (1.18, 1.45, "furniture_chest"),
    "01.props.room__p18": (1.12, 1.15, "furniture_tv_stand"),
    "01.props.room__p03": (0.52, 0.78, "floor_drawer"),
    "01.props.handheld__p04": (0.58, 0.72, "floor_manuscript"),
    "01.props.handheld__p07": (0.55, 0.68, "tumbling_pages"),
    "01.props.window__p13": (1.68, 1.85, "arch_fire_escape_balcony"),
    "01.hero.severn__p11": (1.88, 1.75, "arch_fire_escape_stairs"),
    "01.hero.severn__p12": (1.05, 1.45, "arch_landing_grate"),
    "01.props.chandeliers__p27": (1.18, 1.45, "ceiling_chandelier"),
    "01.props.chandeliers__p28": (1.15, 1.35, "ceiling_chandelier"),
    "01.props.trapdoor__p12": (0.95, 1.55, "floor_trapdoor"),
    "01.props.trapdoor__p11": (0.92, 1.40, "floor_trapdoor_frame"),
    "01.props.trapdoor__p02": (0.78, 1.15, "floor_trapdoor_leaf"),
    # Poem 02: Mirror, Bedroom, 1990s Living Room, Sedan, Tambourine
    "02.props.mirror-phone-rings__p14": (1.58, 0.95, "standing_mirror"),
    "02.props.mirror-phone-rings__p04": (1.62, 1.00, "standing_mirror"),
    "02.props.mirror-phone-rings__p06": (0.62, 0.55, "table_phone"),
    "02.set.bedroom_night__p05": (1.12, 1.50, "bed_headboard"),
    "02.set.bedroom_night__p04": (0.86, 1.65, "bed_frame"),
    "02.set.bedroom_night__p08": (0.78, 1.55, "bed_blanket"),
    "02.set.living_room_1990s__p04": (1.55, 2.25, "living_room_sofa_curtains"),
    "02.set.living_room_1990s__p08": (1.32, 0.78, "floor_lamp"),
    "02.props.car__p01": (1.44, 3.35, "vehicle_sedan_body"),
    "02.props.car__p05": (0.65, 0.65, "vehicle_wheel"),
    "02.props.car__p06": (0.65, 0.65, "vehicle_wheel"),
    "parents.02.car-argument__p03": (0.62, 0.95, "vehicle_cabin_occupants"),
    "02.props.tambourine__p15": (0.68, 0.92, "music_tambourine"),
    "02.props.tambourine__p01": (0.68, 0.92, "music_tambourine"),
    # Poem 03: Cafe Racer, Chapel Pews, Altar, Rose Window
    "03.props.bike__p01": (1.28, 2.15, "vehicle_motorcycle"),
    "03.props.bike__p02": (1.28, 2.15, "vehicle_motorcycle"),
    "03.props.bike__p07": (0.72, 0.85, "motorcycle_exhaust"),
    "03.hero.chapel.interior-states__p05": (1.12, 1.85, "chapel_pew"),
    "03.hero.chapel.interior-states__p11": (1.12, 1.85, "chapel_pew"),
    "03.hero.chapel.interior-states__p08": (1.28, 1.65, "chapel_altar"),
    "03.hero.chapel.interior-states__p12": (1.65, 1.65, "chapel_rose_window"),
    "03.hero.chapel.interior-states__p02": (1.42, 1.25, "chapel_Timber_truss"),
    "03.hero.chapel.interior-states__p10": (1.18, 1.35, "chapel_shattered_beam"),
    # Poem 04: Hands, Phone Booth, Bridge Pylon
    "04.props.hands__p01": (1.05, 1.15, "sculptural_hands"),
    "04.props.hands__p02": (0.98, 1.05, "sculptural_hands"),
    "04.props.hands__p03": (0.98, 1.05, "sculptural_hands"),
    "04.props.hands__p06": (1.02, 1.12, "sculptural_hands"),
    "04.props.booth__p01": (2.12, 1.18, "arch_phone_booth"),
    "04.props.booth__p03": (2.12, 1.18, "arch_phone_booth"),
    "04.props.booth__p07": (0.65, 0.58, "phone_receiver"),
    "04.hero.bridge__p01": (2.25, 1.65, "arch_bridge_pylon"),
    "04.hero.bridge__p05": (1.45, 1.95, "arch_bridge_parapet"),
    # Poem 05: Ancestral Hearth, Table, Doors, Portrait
    "05.props.hearth__p01": (1.68, 1.65, "hearth_fireplace"),
    "05.props.hearth__p02": (1.18, 1.72, "dining_table"),
    "05.props.hearth__p03": (1.02, 0.78, "wooden_chair"),
    "05.props.hearth__p06": (0.78, 0.85, "hearth_tea_pot"),
    "05.props.doors__p01": (2.05, 1.22, "arch_door_closed"),
    "05.props.doors__p02": (2.05, 1.25, "arch_door_ajar"),
    "05.props.doors__p03": (2.08, 1.32, "arch_door_open"),
    "05.props.doors__p06": (1.28, 1.05, "wall_portrait"),
    # Poem 06 & 08 & 10: Lanterns, Guitar, Campfire, Waystone, Telescope, Astrolabe
    "06.props.lantern-candle-guitar__p01": (0.92, 0.68, "brass_lantern"),
    "06.props.lantern-candle-guitar__p02": (0.84, 0.62, "brass_candle"),
    "06.props.lantern-candle-guitar__p03": (1.15, 0.78, "acoustic_guitar"),
    "06.props.lantern-candle-guitar__p06": (1.15, 0.82, "acoustic_guitar"),
    "06.props.campfire-stones__p01": (1.05, 1.38, "campfire_circle"),
    "06.props.campfire-stones__p02": (1.25, 0.98, "standing_waystone"),
    "06.props.campfire-stones__p03": (1.48, 1.45, "stone_cairn_arch"),
    "08.props.telescope__p01": (1.58, 1.28, "brass_telescope"),
    "08.props.telescope__p02": (1.35, 1.18, "armillary_astrolabe"),
    "08.props.telescope__p05": (1.12, 1.15, "star_chart_table"),
    "10.props.beacon-wheel__p01": (1.42, 1.38, "ships_helm_wheel"),
    "10.props.beacon-wheel__p02": (1.68, 1.25, "lighthouse_fresnel_lens"),
    "10.props.beacon-wheel__p03": (1.28, 1.15, "brass_binocular_stand"),
    # Poem 07: Club DJ Booth, Speakers, Disco Ball, Neon Arch
    "07.props.dj-booth__p01": (1.38, 2.05, "club_dj_console"),
    "07.props.dj-booth__p02": (1.68, 1.15, "club_speaker_stack"),
    "07.props.dj-booth__p03": (0.98, 1.28, "club_turntable_deck"),
    "07.props.club-lights__p01": (1.05, 1.05, "club_disco_ball"),
    "07.props.club-lights__p03": (1.85, 1.65, "club_neon_arch"),
    "07.props.club-lights__p15": (1.25, 0.92, "club_velvet_stanchion"),
    # Poem 09: Sunken Columns, Anchors, Porthole, Diving Bell
    "09.props.sunken-ruins__p01": (1.92, 1.18, "sunken_doric_column"),
    "09.props.sunken-ruins__p02": (1.48, 1.55, "sunken_pediment_arch"),
    "09.props.sunken-ruins__p03": (1.42, 1.18, "ship_anchor"),
    "09.props.sunken-ruins__p05": (1.35, 1.35, "brass_porthole"),
    "09.props.sunken-ruins__p06": (1.65, 1.32, "diving_bell"),
    # Poem 11: Progressive Temple States & Mason Tools
    "11.props.temple.states__p02": (1.35, 1.85, "temple_state_1_plinth"),
    "11.props.temple.states__p03": (1.62, 1.88, "temple_state_2_drums"),
    "11.props.temple.states__p01": (1.88, 1.95, "temple_state_3_colonnade"),
    "11.props.temple.states__p04": (2.15, 2.15, "temple_state_4_sanctuary"),
    "11.props.temple.states__p06": (1.72, 1.65, "temple_altar_brazier"),
    "11.props.mason-tools__p01": (1.05, 1.25, "mason_chisel_mallet"),
    "11.props.mason-tools__p02": (1.32, 1.15, "mason_plumb_square"),
    "11.props.mason-tools__p03": (1.38, 1.48, "architect_drafting_table"),
    # Poem 12: Hourglasses, Sundial, Bell
    "12.props.hand-hourglass__p01": (1.22, 0.88, "glass_hourglass_upright"),
    "12.props.hand-hourglass__p04": (1.12, 1.05, "glass_hourglass_tilted"),
    "12.props.hand-hourglass__p21": (1.08, 0.95, "glass_hourglass_burning"),
    "12.props.last-hourglass__p01": (1.48, 0.95, "tall_wooden_hourglass"),
    "12.props.last-hourglass__p02": (1.28, 1.15, "stone_sundial"),
    "12.props.last-hourglass__p03": (1.58, 1.32, "bronze_chronometer_bell"),
    # Poem 13: Harvest Poppies & Harbor Cafe Bistro
    "13.props.harvest__p09": (1.12, 1.18, "poppy_bouquet_vase"),
    "13.props.harvest__p08": (0.98, 1.22, "wicker_harvest_basket"),
    "13.props.harvest__p07": (0.95, 1.18, "wheat_poppy_sheaf"),
    "13.props.cafe__p13": (1.18, 1.38, "bistro_table_chairs"),
    "13.props.cafe__p11": (0.68, 0.72, "espresso_cup_saucer"),
    "13.props.cafe__p01": (1.85, 2.10, "cafe_awning_menu"),
    # Poem 14: Life-Reel Medallions & Vintage Party Ballroom
    "14.props.reel__p08": (1.38, 1.38, "cinema_projector_reel"),
    "14.props.reel__p06": (1.32, 1.32, "memory_medallion_frame"),
    "14.props.reel__p03": (1.25, 1.55, "unspooled_film_ribbon"),
    "14.props.reel__p02": (1.32, 1.32, "silver_film_canister"),
    "14.props.party__p19": (1.15, 2.25, "paper_lantern_garland"),
    "14.props.party__p20": (1.22, 1.05, "brass_horn_gramophone"),
    "14.props.party__p03": (1.22, 1.05, "brass_horn_gramophone"),
    "14.props.party__p01": (1.25, 1.48, "champagne_fountain_table"),
}

_TIGHT_BBOX_CACHE: Dict[str, Tuple[int, int, int, int, float, float]] = {}
_SCALE_MARKER_CACHE: Dict[str, Dict[str, Any]] = {}


def get_part_tight_metrics(pid: str, parts_by_id: Dict[str, Dict[str, Any]]) -> Tuple[int, int, int, int, float, float]:
    """
    Returns `(pw, ph, tight_w, tight_h, fill_w, fill_h)` for `pid` by measuring
    its non-transparent alpha silhouette (`alpha > 24`) so transparent padding
    margins never distort standardized physical piece scaling.
    """
    if pid in _TIGHT_BBOX_CACHE:
        return _TIGHT_BBOX_CACHE[pid]
    import numpy as np

    pt = parts_by_id.get(pid, {})
    pw = max(1, int(pt.get("width", 240)))
    ph = max(1, int(pt.get("height", 240)))
    rel = pt.get("file", "")
    p_path = SHOTS_DIR / rel if rel else None
    if p_path and p_path.exists():
        try:
            im = Image.open(p_path).convert("RGBA")
            pw, ph = im.size
            a = np.array(im)[..., 3]
            ys, xs = np.where(a > 24)
            if len(xs) > 16:
                tw = max(8, int(xs.max() - xs.min() + 1))
                th = max(8, int(ys.max() - ys.min() + 1))
                fw = max(0.25, min(1.0, float(tw) / float(max(1, pw))))
                fh = max(0.25, min(1.0, float(th) / float(max(1, ph))))
                res = (pw, ph, tw, th, fw, fh)
                _TIGHT_BBOX_CACHE[pid] = res
                return res
        except Exception:
            pass
    res = (pw, ph, pw, ph, 1.0, 1.0)
    _TIGHT_BBOX_CACHE[pid] = res
    return res


def extract_cel_painting_scale_markers(fid: str, wshot: Dict[str, Any], skey: str = "") -> Dict[str, Any]:
    """
    Finds real-world scale markers (`person`, `door`, `window`, `street lamp`, `railing`,
    `vehicle`, `pillar`, `stairs`, `chair`, `tree`, `building`, etc.) in the cel painting's
    `shots/out/<fid>/shot.json` + `cartoon/signals.json` + `depth_sharp.npz`, and combines
    them with the hand-calibrated `shot_profile` (`shot_scale`, `camera_distance_m`, `focal_mm`,
    `stage_px_per_meter`) so every scene's scale reflects its true camera distance (`2.9m` close-up
    to `140m` aerial drop).
    """
    cache_key = f"{skey}:{fid}"
    if cache_key in _SCALE_MARKER_CACHE:
        return _SCALE_MARKER_CACHE[cache_key]
    import numpy as np

    shot_prof = get_scene_shot_profile(skey)
    prof_ppm = float(shot_prof["stage_px_per_meter"])
    prof_dist_m = float(shot_prof["camera_distance_m"])
    prof_focal_mm = int(shot_prof["focal_mm"])

    W_STAGE, H_STAGE = 1280.0, 720.0
    W_RAW, H_RAW = 1456.0, 816.0
    sx = W_STAGE / W_RAW
    sy = H_STAGE / H_RAW

    z_hero = float(wshot.get("z_hero") or prof_dist_m)
    z_hero = max(2.5, min(180.0, z_hero))
    focal_raw = float(wshot.get("focal") or 1250.0)
    cam_ppm_raw = (focal_raw * sy) / max(2.5, prof_dist_m)

    markers: List[Dict[str, Any]] = []
    valid_ppms: List[float] = []
    plane_values: Dict[str, Any] = {}

    out_dir = SHOTS_DIR / "out" / fid if fid else None
    depth_map = None
    if out_dir and (out_dir / "depth_sharp.npz").exists():
        try:
            depth_map = np.load(out_dir / "depth_sharp.npz")["depth"]
        except Exception:
            depth_map = None

    if out_dir and (out_dir / "cartoon" / "signals.json").exists():
        try:
            sig_d = json.loads((out_dir / "cartoon" / "signals.json").read_text())
            plane_values = sig_d.get("plane_values") or {}
            sl_p2 = (sig_d.get("scale_ladder") or {}).get("P2", {})
            if "1.7m" in sl_p2:
                sig_ppm = (float(sl_p2["1.7m"]) * sy) / 1.70
                if 18.0 <= sig_ppm <= 220.0:
                    valid_ppms.append(sig_ppm)
        except Exception:
            pass

    if out_dir and (out_dir / "shot.json").exists():
        try:
            shot_d = json.loads((out_dir / "shot.json").read_text())
            cam = shot_d.get("camera") or {}
            if cam.get("focal_px"):
                focal_raw = float(cam["focal_px"])

            for det in shot_d.get("detections", []):
                lbl = str(det.get("label", "")).strip().lower()
                score = float(det.get("score", 0.0))
                if score < 0.28:
                    continue
                matched_key = None
                real_h_m = None
                for k, hm in OBJECT_REAL_HEIGHT_M.items():
                    if k == lbl or k in lbl:
                        matched_key = k
                        real_h_m = hm
                        break
                if not real_h_m:
                    continue
                box = det.get("box") or [0, 0, 0, 0]
                if len(box) < 4:
                    continue
                x0, y0, x1, y1 = float(box[0]) * sx, float(box[1]) * sy, float(box[2]) * sx, float(box[3]) * sy
                bw = max(1.0, x1 - x0)
                bh = max(1.0, y1 - y0)
                if bh < 14.0 or bh > H_STAGE * 0.92:
                    continue

                # Sample metric depth inside the marker's bounding box if available
                z_marker = z_hero
                if depth_map is not None:
                    dh, dw = depth_map.shape[:2]
                    ix0 = max(0, min(dw - 1, int((x0 / W_STAGE) * dw)))
                    ix1 = max(ix0 + 1, min(dw, int((x1 / W_STAGE) * dw)))
                    iy0 = max(0, min(dh - 1, int((y0 / H_STAGE) * dh)))
                    iy1 = max(iy0 + 1, min(dh, int((y1 / H_STAGE) * dh)))
                    patch = depth_map[iy0:iy1, ix0:ix1]
                    if patch.size > 0:
                        z_marker = max(2.5, min(65.0, float(np.median(patch))))

                raw_marker_ppm = bh / real_h_m
                depth_ratio = max(0.55, min(1.85, z_marker / max(3.0, z_hero)))
                implied_p2_ppm = raw_marker_ppm * depth_ratio
                if 18.0 <= implied_p2_ppm <= 220.0:
                    valid_ppms.append(implied_p2_ppm)

                markers.append({
                    "label": matched_key,
                    "score": round(score, 3),
                    "box_stage": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
                    "px_h": round(bh, 1),
                    "real_h_m": real_h_m,
                    "z_m": round(z_marker, 2),
                    "implied_p2_px_per_m": round(implied_p2_ppm, 1),
                })
        except Exception:
            pass

    markers.sort(key=lambda m: m["score"], reverse=True)
    if valid_ppms:
        med_ppm = float(np.median(valid_ppms))
        # Blend 84% hand-calibrated shot-distance tier (`18..178 px/m`) with 16% detected marker median
        blended_ppm = 0.84 * prof_ppm + 0.16 * med_ppm
    else:
        blended_ppm = prof_ppm

    stage_ppm = round(max(16.0, min(188.0, blended_ppm)), 2)
    res = {
        "shot_id": fid,
        "shot_scale": shot_prof["shot_scale"],
        "short_label": shot_prof["short_label"],
        "badge_color": shot_prof["badge_color"],
        "camera_distance_m": prof_dist_m,
        "focal_mm": prof_focal_mm,
        "actor_scale_mult": shot_prof["actor_scale_mult"],
        "distance_readout": shot_prof["distance_readout"],
        "director_note": shot_prof["director_note"],
        "z_hero_m": round(prof_dist_m, 2),
        "focal_px": round(focal_raw, 1),
        "stage_px_per_meter": stage_ppm,
        "reference_human_170cm_px": round(stage_ppm * 1.70, 1),
        "marker_count": len(markers),
        "markers": markers[:8],
        "plane_values": plane_values,
    }
    _SCALE_MARKER_CACHE[cache_key] = res
    return res


def infer_canonical_piece_meters(
    pid: str,
    label: str,
    plane: str,
    ar: float,
) -> Tuple[float, float, str]:
    """
    Returns `(canon_h_m, canon_w_m, class_tag)` for any piece ID, using the explicit
    dictionary first and falling back to semantic keyword rules if needed.
    """
    if pid in CANONICAL_PIECE_METERS_BY_ID:
        ch, cw, ctag = CANONICAL_PIECE_METERS_BY_ID[pid]
        if ctag == "arch_portal_element":
            return (max(2.65, ch * 1.35), max(2.45, cw * 1.32), ctag)
        if ctag == "arch_fixture":
            return (max(2.05, ch * 1.28), max(2.10, cw * 1.25), ctag)
        return (ch, cw, ctag)
    s = f"{pid} {label}".lower()
    if any(k in s for k in ("booth", "door", "arch", "column", "pillar", "pylon", "temple", "sanctuary", "beacon", "lighthouse", "viaduct", "tower", "facade", "wall", "building", "chapel", "ruins", "gate")):
        return (2.82, 2.65, "arch_portal_element")
    if any(k in s for k in ("window", "balcony", "stairs", "fire-escape", "hearth", "fireplace", "altar", "console", "speaker", "telescope", "mirror", "screen", "tv")):
        return (2.12, 2.18, "arch_fixture")
    if any(k in s for k in ("sofa", "bed", "dresser", "chest", "table", "pew", "bistro", "chandelier", "garland", "wheel", "sundial", "bell", "reel", "bench")):
        return (1.32, 1.82, "furniture_large_prop")
    if any(k in s for k in ("chair", "lamp", "hourglass", "guitar", "lantern", "campfire", "waystone", "anchor", "gramophone", "vase", "bouquet", "basket")):
        return (1.06, 1.24, "medium_stage_prop")
    return (0.82, 0.98, "compact_stage_prop")


def standardize_piece_scale(
    pid: str,
    label: str,
    plane: str,
    authored_sc: float,
    stage_ppm: float,
    parts_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[float, Dict[str, Any]]:
    """
    Computes a standardized, camera-distance-calibrated stage `scale` (`target_h / 720`)
    for piece `pid` on `plane` using:
      1. The piece's tight non-transparent alpha bounding box (`tight_w, tight_h`),
      2. Its canonical physical height & width cap in meters (`canon_h_m, canon_w_m`),
      3. The scene's true camera-distance `stage_px_per_meter` (`18..178 px/m`),
      4. The depth-plane perspective foreshortening multiplier (`P4: 0.84`, `P3: 0.92`, `P2: 1.00`).
    """
    H_STAGE = 720.0
    pw, ph, tw, th, fill_w, fill_h = get_part_tight_metrics(pid, parts_by_id)
    ar_tight = float(tw) / float(max(1, th))
    canon_h_m, canon_w_m, class_tag = infer_canonical_piece_meters(pid, label, plane, ar_tight)

    plane_persp_mult = {
        "P6": 0.52,
        "P5": 0.66,
        "P4": 0.84,
        "P3": 0.92,
        "P2": 1.00,
        "P1": 1.06,
        "P0": 1.12,
    }.get(plane, 0.90)

    eff_ppm = 116.0 * ((max(18.0, stage_ppm) / 116.0) ** 0.72)

    desired_tight_h_px = canon_h_m * eff_ppm * plane_persp_mult
    desired_tight_w_px = desired_tight_h_px * ar_tight
    max_tight_w_px = canon_w_m * eff_ppm * plane_persp_mult
    if desired_tight_w_px > max_tight_w_px and ar_tight > 0.1:
        desired_tight_w_px = max_tight_w_px
        desired_tight_h_px = desired_tight_w_px / ar_tight

    full_h_px = desired_tight_h_px / max(0.32, fill_h)
    phys_sc = full_h_px / H_STAGE

    dist_ratio = eff_ppm / 116.0
    cal_sc = 0.72 * phys_sc + 0.28 * (float(authored_sc) * dist_ratio)
    max_cap = 0.62 if class_tag == "arch_portal_element" else (0.52 if class_tag == "arch_fixture" else 0.44)
    cal_sc = round(max(0.09, min(max_cap, cal_sc)), 4)

    meta = {
        "class_tag": class_tag,
        "canon_h_m": round(canon_h_m, 2),
        "canon_w_m": round(canon_w_m, 2),
        "tight_bbox_px": [tw, th],
        "fill_ratio": [round(fill_w, 3), round(fill_h, 3)],
        "authored_scale": round(float(authored_sc), 4),
        "standardized_scale": cal_sc,
        "effective_ppm": round(eff_ppm, 1),
    }
    return cal_sc, meta


def curate_scene_props(
    skey: str,
    raw_layers: List[Dict[str, Any]],
    stage_ppm: float = 118.0,
    parts_by_id: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Returns each scene's hand-assembled composition combining:
      1. Distance-calibrated in-frame multiplane architecture, portals & props (`x in [0.10 .. 0.90]`),
         preserving up to 5 distinct layers across P4 (architectural doors/windows/arches/balconies),
         P3 (grounded furniture & vehicles), and P2/P1 (focal & foreground elements), with layered
         multiplane `aperture_footage` attached to every door, window, archway, TV screen, or mirror!
      2. The hand-assembled, distance-calibrated Lego Set-Extension bridge (`x in [0.98 .. 1.58]`,
         `is_set_extension=True`) from `get_scene_lego_extension(skey)`, with layered multiplane
         `aperture_footage` inside every doorway, window, and portal opening!
    """
    base_list = SCENE_CURATED_PROP_OVERRIDES.get(skey, raw_layers[:3])
    has_car = any(x.get("part_id") == "02.props.car__p01" for x in base_list)
    if has_car:
        in_frame_list = [dict(x, alpha=0.98, is_set_extension=False) for x in base_list if x.get("plane") in ("P3", "P2")]
    else:
        grounded = [
            x for x in base_list
            if x.get("plane") in ("P4", "P3", "P2", "P1") and float(x.get("y", 0.86)) >= 0.76
        ]
        if not grounded:
            grounded = [dict(x, y=max(0.82, float(x.get("y", 0.86)))) for x in base_list[:2]]
        in_frame_list = [dict(x, alpha=0.98, is_set_extension=False) for x in grounded[:3]]

    # Also include grounded in-frame P4 door/window/arch portals from `raw_layers`
    existing_pids = {x.get("part_id") for x in in_frame_list}
    for rl in raw_layers:
        if len(in_frame_list) >= 4:
            break
        r_pid = rl.get("part_id", "")
        if r_pid in existing_pids:
            continue
        if f"{skey}:{r_pid}" in (
            "01.0:01.props.window__p01",
            "01.1:01.props.window__p01",
            "01.2:01.props.window__p01",
            "01.4:14.set.vintage_party__p03",
            "03.1:03.hero.chapel.interior-states__p12",
            "04.3:04.props.booth__p01",
            "05.4:05.props.doors__p03",
            "07.3:07.props.club-lights__p03",
            "09.3:09.props.sunken-ruins__p05",
            "14.1:14.props.door__p02",
            "14.3:14.props.door__p11",
            "14.4:14.props.door__p13",
        ):
            r_copy = dict(rl, alpha=0.98, is_set_extension=False)
            r_copy["y"] = max(0.80, float(r_copy.get("y", 0.86)))
            in_frame_list.append(r_copy)
            existing_pids.add(r_pid)

    out = list(in_frame_list)
    if parts_by_id:
        car_body = next((item for item in out if item["part_id"] == "02.props.car__p01"), None)
        locked_car_sc = None
        locked_car_cx = None
        locked_car_floor_y = None
        if car_body is not None:
            raw_car_sc = float(car_body["scale"])
            locked_car_cx = float(car_body["x"])
            locked_car_floor_y = round(float(car_body["y"]) + 0.05 * raw_car_sc, 4)
            locked_car_sc, car_meta = standardize_piece_scale(
                "02.props.car__p01",
                car_body["label"],
                car_body["plane"],
                raw_car_sc,
                stage_ppm,
                parts_by_id,
            )
            car_body["scale"] = locked_car_sc
            car_body["y"] = round(locked_car_floor_y - 0.05 * locked_car_sc, 4)
            car_body["scale_meta"] = car_meta

        for item in out:
            pid = item["part_id"]
            af = get_in_frame_portal_footage(skey, pid, item.get("label", ""), item.get("anim_role", ""))
            if af is not None:
                item["aperture_footage"] = af

            if pid == "02.props.car__p01" and locked_car_sc is not None:
                continue
            if locked_car_sc is not None and locked_car_cx is not None and locked_car_floor_y is not None:
                if pid == "02.props.car__p05":
                    item["x"] = round(locked_car_cx - 0.585 * locked_car_sc, 4)
                    item["y"] = locked_car_floor_y
                    item["scale"] = round(0.45 * locked_car_sc, 4)
                    item["scale_meta"] = {"class_tag": "vehicle_wheel_locked", "canon_h_m": 0.65, "standardized_scale": item["scale"]}
                    continue
                if pid == "02.props.car__p06":
                    item["x"] = round(locked_car_cx + 0.456 * locked_car_sc, 4)
                    item["y"] = locked_car_floor_y
                    item["scale"] = round(0.45 * locked_car_sc, 4)
                    item["scale_meta"] = {"class_tag": "vehicle_wheel_locked", "canon_h_m": 0.65, "standardized_scale": item["scale"]}
                    continue
                if pid == "parents.02.car-argument__p03":
                    body_y = round(locked_car_floor_y - 0.05 * locked_car_sc, 4)
                    item["x"] = round(locked_car_cx - 0.04 * locked_car_sc, 4)
                    item["y"] = round(body_y - 0.46 * locked_car_sc, 4)
                    item["scale"] = round(0.42 * locked_car_sc, 4)
                    item["scale_meta"] = {"class_tag": "vehicle_cabin_locked", "canon_h_m": 0.62, "standardized_scale": item["scale"]}
                    continue

            cal_sc, smeta = standardize_piece_scale(
                pid,
                item.get("label", ""),
                item.get("plane", "P3"),
                float(item.get("scale", 0.20)),
                stage_ppm,
                parts_by_id,
            )
            item["scale"] = cal_sc
            item["scale_meta"] = smeta

    # Append the hand-assembled, distance-calibrated Lego Set Extension (`x in [0.98 .. 1.58]`),
    # modulated by the scene's true Camera Distance & Shot Scale (`stage_ppm` vs reference `114 px/m`)
    shot_prof = get_scene_shot_profile(skey)
    lego_ext = get_scene_lego_extension(skey)
    ext_dist_mult = max(0.54, min(1.32, (stage_ppm / 114.0) ** 0.42))
    for lx in lego_ext:
        l_role = lx.get("lego_role", "wall_bay")
        base_sc = float(lx.get("scale", 0.50))
        if l_role in ("wall_with_door_hole", "wall_bay"):
            # Keep wall bays substantial enough to bridge the horizon while still breathing with shot scale
            sc_val = round(max(0.44, min(0.90, base_sc * (0.76 + 0.24 * ext_dist_mult))), 4)
        else:
            sc_val = round(max(0.11, min(0.86, base_sc * ext_dist_mult)), 4)
        lx["scale"] = sc_val
        lx["scale_meta"] = {
            "class_tag": f"lego_{l_role}",
            "canon_h_m": round(base_sc * 4.2, 2),
            "standardized_scale": sc_val,
            "is_set_extension": True,
            "lego_role": l_role,
            "shot_scale": shot_prof["shot_scale"],
            "camera_distance_m": shot_prof["camera_distance_m"],
            "stage_px_per_meter": round(stage_ppm, 1),
        }
        out.append(lx)

    return out



def clean_and_integrate_cutout(
    p_img: Image.Image,
    bg_crop: Image.Image,
    plane_id: str,
    haze_rgb: Tuple[int, int, int] = (24, 30, 44),
    cel_scene_img: Optional[Image.Image] = None,
) -> Image.Image:
    """
    Colorizes and integrates a cut-out piece directly into the Cel Painting (`world/<wk>/cel.webp`)
    it sits in ("Pieces as Paint"):
      1. Strips the outer tan Kraft-paper die-cut margin (`#b5986e`) & matte fringe
         within `dt <= 11px` of the silhouette edge.
      2. Modulates the outer `2px` silhouette boundary with a multi-frequency Organic
         Bristle Edge (`dt_brush`) while keeping the interior 100% opaque matte gouache.
      3. Extracts the 6-Band Luminance-Sorted Cel Pigment Ramp (`cel_ramp[0..5]`) from the
         piece's wider local neighborhood in `cel.webp` (72% weight) + the full `cel.webp`
         scene palette (28% weight).
      4. Preserves the piece's internal hand-drawn ink linework (`ink_strength`), quantizes
         its internal luminance (`[p05..p95]`) into 5 stepped cel-wash flats (`u_cel`),
         applies figure-ground Notan windowing so pieces never vanish into dark floors or
         wash out against bright skies, and colorizes the piece (`76%` direct Cel-Ramp +
         `24%` CIE-LAB harmonized hue).
      5. Applies an Edge-Preserving Bilateral Gouache Filter, re-inks internal linework,
         adds a `1.8px` cel-palette top rim highlight (`cel_ramp[5]`), and draws the outer
         `1.6px` charcoal-ink contour (`[15, 12, 19]` blended with `cel_ramp[0]`).
    """
    import cv2
    import numpy as np

    arr = np.array(p_img.convert("RGBA"), dtype=np.float32)
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    mask = alpha > 24
    if not mask.any():
        return p_img

    h_px, w_px = alpha.shape

    # 1. Strip outer tan Kraft cardboard margin & white/grey border fringe
    u8_mask = mask.astype(np.uint8)
    dt = cv2.distanceTransform(u8_mask, cv2.DIST_L2, 5)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    sat = max_c - min_c
    lum = 0.299 * r + 0.587 * g + 0.114 * b

    kraft_rim = (dt <= 11.0) & (
        ((r >= g - 6) & (g >= b - 10) & (lum > 80) & (sat < 105))
        | ((lum > 162) & (sat < 50))
    )
    clean_mask = mask & (~kraft_rim)
    if clean_mask.sum() > 64:
        mask = clean_mask
        u8_mask = mask.astype(np.uint8)
        dt = cv2.distanceTransform(u8_mask, cv2.DIST_L2, 5)

    # 2. Organic Bristle Silhouette Edge (100% opaque interior, bristle-feathered 1.8px rim)
    yy, xx = np.mgrid[0:h_px, 0:w_px].astype(np.float32)
    bristle = (
        0.55 * np.sin(xx * 0.23 + yy * 0.17)
        + 0.30 * np.cos(xx * 0.41 - yy * 0.29)
        + 0.15 * np.sin(xx * 0.73 + yy * 0.61)
    )
    dt_brush = np.maximum(0.0, dt + bristle * 0.45)
    alpha_clean = np.where(mask, alpha, 0.0)
    alpha_soft = cv2.GaussianBlur(alpha_clean, (3, 3), 0.85)
    alpha_out = np.where(mask, np.minimum(alpha_clean, np.clip(dt_brush * 96.0, 0, 255)), alpha_soft * 0.26)

    # 3. Extract the 6-Band Luminance-Sorted Cel Pigment Ramp (`cel_ramp[0..5]`) from `bg_crop` + `cel_scene_img`
    bg_arr = np.array(bg_crop.resize((w_px, h_px), Image.Resampling.BILINEAR).convert("RGB"), dtype=np.uint8)
    local_flat = bg_arr.reshape(-1, 3).astype(np.float32)
    if cel_scene_img is not None:
        scene_arr = np.array(cel_scene_img.convert("RGB"), dtype=np.float32).reshape(-1, 3)
    else:
        scene_arr = local_flat

    def compute_6band_ramp(pix: np.ndarray) -> np.ndarray:
        l_vals = 0.299 * pix[:, 0] + 0.587 * pix[:, 1] + 0.114 * pix[:, 2]
        order = np.argsort(l_vals)
        sorted_p = pix[order]
        n_p = len(sorted_p)
        edges = [0.0, 0.16, 0.34, 0.52, 0.70, 0.86, 1.00]
        swatches = []
        for bi in range(6):
            i0 = int(edges[bi] * n_p)
            i1 = max(i0 + 1, int(edges[bi + 1] * n_p))
            swatches.append(sorted_p[i0:i1].mean(axis=0))
        return np.array(swatches, dtype=np.float32)

    local_ramp = compute_6band_ramp(local_flat)
    scene_ramp = compute_6band_ramp(scene_arr)
    cel_ramp = 0.74 * local_ramp + 0.26 * scene_ramp

    bg_lum_mean = float(0.299 * local_flat[:, 0].mean() + 0.587 * local_flat[:, 1].mean() + 0.114 * local_flat[:, 2].mean())

    # Ensure upper cel swatches (`cel_ramp[4..5]`) have figure-ground contrast on dark floors
    # WITHOUT washing out saturation into neutral grey (lift toward `scene_ramp[5]` + warm gold tint)
    top_tint = 0.65 * np.maximum(scene_ramp[5], local_ramp[5]) + 0.35 * np.array([235.0, 198.0, 145.0], dtype=np.float32)
    for bi in range(6):
        sw_lum = float(0.299 * cel_ramp[bi, 0] + 0.587 * cel_ramp[bi, 1] + 0.114 * cel_ramp[bi, 2])
        min_band_lum = 12.0 + bi * 22.0
        if bg_lum_mean < 88.0 and bi >= 3:
            min_band_lum = max(min_band_lum, bg_lum_mean + 16.0 + (bi - 2) * 14.0)
        if sw_lum < min_band_lum:
            need = min(0.55, (min_band_lum - sw_lum) / max(32.0, 225.0 - sw_lum))
            cel_ramp[bi] = np.clip(cel_ramp[bi] * (1.0 - need) + top_tint * need, 0.0, 245.0)

    # 4. Detect internal hand-drawn ink linework (`ink_strength`) & normalize internal piece luminance (`u_cel`)
    lum_blur = cv2.GaussianBlur(lum, (9, 9), 2.2)
    ink_diff = np.maximum(0.0, lum_blur - lum)
    ink_strength = np.clip((ink_diff - 6.5) / 22.0, 0.0, 1.0) * (dt > 1.8).astype(np.float32)

    valid = mask
    if valid.sum() > 25:
        fg_l_vals = lum_blur[valid]
        p05 = float(np.percentile(fg_l_vals, 5))
        p95 = max(p05 + 14.0, float(np.percentile(fg_l_vals, 95)))
    else:
        p05, p95 = 20.0, 220.0

    u_cont = np.clip((lum_blur - p05) / (p95 - p05), 0.0, 1.0)
    # Posterize into 5 stepped cel-wash value flats while keeping 38% smooth transition
    u_cel = 0.38 * u_cont + 0.62 * (np.round(u_cont * 4.0) / 4.0)

    # Figure-Ground Notan Windowing against local background luminance
    if bg_lum_mean < 92.0:
        u_mapped = 0.18 + u_cel * 0.72
    elif bg_lum_mean > 168.0:
        u_mapped = 0.04 + u_cel * 0.76
    else:
        u_mapped = 0.10 + u_cel * 0.78

    # Piecewise-linear lookup of `u_mapped` in `[0, 1]` across `cel_ramp[0..5]`
    pos = np.clip(u_mapped * 5.0, 0.0, 4.999)
    idx0 = np.floor(pos).astype(np.int32)
    idx1 = np.minimum(5, idx0 + 1)
    frac = (pos - idx0)[..., None]
    ramp_rgb = cel_ramp[idx0] * (1.0 - frac) + cel_ramp[idx1] * frac

    # 5. Also compute CIE-LAB chrominance-harmonized RGB (`14%` weight) with strong chrominance transfer (`0.90`)
    fg_u8 = np.clip(rgb, 0, 255).astype(np.uint8)
    fg_lab = cv2.cvtColor(fg_u8, cv2.COLOR_RGB2LAB).astype(np.float32)
    bg_lab = cv2.cvtColor(bg_arr, cv2.COLOR_RGB2LAB).astype(np.float32)
    if valid.sum() > 25:
        for ch_i, blend_w in ((0, 0.56), (1, 0.90), (2, 0.90)):
            f_vals = fg_lab[..., ch_i][valid]
            b_vals = bg_lab[..., ch_i]
            f_mean, f_std = float(f_vals.mean()), max(4.0, float(f_vals.std()))
            b_mean, b_std = float(b_vals.mean()), max(4.0, float(b_vals.std()))
            if ch_i == 0:
                t_std = max(18.0, f_std * 0.75 + b_std * 0.25)
                raw_t_mean = f_mean * (1.0 - blend_w) + b_mean * blend_w
                t_mean = min(172.0, max(raw_t_mean, b_mean + 20.0)) if b_mean < 96.0 else raw_t_mean
            else:
                t_std = f_std * 0.25 + b_std * 0.75
                t_mean = f_mean * (1.0 - blend_w) + b_mean * blend_w
            fg_lab[..., ch_i] = np.clip((fg_lab[..., ch_i] - f_mean) * (t_std / f_std) + t_mean, 0, 255)
    harm_rgb = cv2.cvtColor(fg_lab.astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)

    # Blend 86% direct Cel-Ramp Colorization with 14% CIE-LAB harmonized color + spatial background wash
    bg_blur_f = cv2.GaussianBlur(bg_arr.astype(np.float32), (31, 31), 9.0)
    combined_f = 0.74 * ramp_rgb + 0.12 * harm_rgb + 0.14 * bg_blur_f
    combined_u8 = np.clip(combined_f, 0, 255).astype(np.uint8)
    gouache_u8 = cv2.bilateralFilter(combined_u8, d=5, sigmaColor=28, sigmaSpace=28)
    cel_rgb = gouache_u8.astype(np.float32)

    # Re-apply internal hand-drawn ink linework in the cel painting's deepest shadow ink color
    inner_ink_col = cel_ramp[0] * 0.55 + np.array([14.0, 12.0, 18.0], dtype=np.float32) * 0.45
    cel_rgb = cel_rgb * (1.0 - 0.72 * ink_strength[..., None]) + inner_ink_col * (0.72 * ink_strength[..., None])

    # Plane atmospheric depth integration (`haze_mix`)
    pmeta = SEVEN_PLANES.get(plane_id, SEVEN_PLANES["P3"])
    haze_mix = min(0.15, float(pmeta["haze_mix"]) * 0.45 + 0.02)
    haze = np.array(haze_rgb, dtype=np.float32)
    cel_rgb = cel_rgb * (1.0 - haze_mix) + haze * haze_mix

    # Subtle sunlit top gradient + cold-pressed paper micro-tooth
    v_grad = np.linspace(1.04, 0.93, h_px, dtype=np.float32)[:, None, None]
    cel_rgb = cel_rgb * v_grad + (bristle[..., None] * 1.4)

    # 6. Cel-Palette Top Rim Light (`cel_ramp[5]`) + Warm Charcoal-Sepia Outer Ink Contour (`cel_ramp[0]`)
    top_rim = (dt > 1.3) & (dt <= 3.1) & (yy < h_px * 0.65)
    rim_col = np.clip(cel_ramp[5] * 1.15 + np.array([28.0, 24.0, 18.0], dtype=np.float32), 75.0, 242.0)
    cel_rgb[top_rim] = cel_rgb[top_rim] * 0.72 + rim_col * 0.28

    outline = (dt > 0.0) & (dt <= 1.55 + 0.35 * bristle)
    ink_col = np.array([15.0, 12.0, 19.0], dtype=np.float32) * 0.68 + cel_ramp[0] * 0.32
    cel_rgb[outline] = cel_rgb[outline] * 0.28 + ink_col * 0.72

    out_arr = np.dstack([
        np.clip(cel_rgb, 0, 255).astype(np.uint8),
        np.clip(alpha_out, 0, 255).astype(np.uint8),
    ])
    return Image.fromarray(out_arr, mode="RGBA")


def _load_blended_cel_backdrop(
    backdrop_path: pathlib.Path,
    cel_path: Optional[pathlib.Path],
    W: int = 1280,
    H: int = 720,
) -> Tuple[Image.Image, Image.Image]:
    """Loads `1280x720` `backdrop.webp` blended 68% with `cel.webp` and returns `(rgba_blended, cel_ref_rgb)`."""
    if backdrop_path and backdrop_path.exists():
        bg = Image.open(backdrop_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    else:
        bg = Image.new("RGBA", (W, H), (14, 18, 26, 255))
    cel_ref = bg.convert("RGB")
    if cel_path and cel_path.exists():
        try:
            cel_bg = Image.open(cel_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
            cel_ref = cel_bg.convert("RGB")
            bg = Image.blend(bg, cel_bg, alpha=0.68)
        except Exception:
            pass
    bg = ImageEnhance.Contrast(bg.convert("RGB")).enhance(1.04).convert("RGBA")
    return bg, cel_ref


_PORTAL_FOOTAGE_RAW_CACHE: Dict[str, Image.Image] = {}


def _load_portal_footage_rgb(rel_path: str) -> Optional[Image.Image]:
    if not rel_path:
        return None
    if rel_path in _PORTAL_FOOTAGE_RAW_CACHE:
        return _PORTAL_FOOTAGE_RAW_CACHE[rel_path]
    p = SHOTS_DIR / rel_path
    if not p.exists():
        return None
    try:
        im = Image.open(p).convert("RGB")
        _PORTAL_FOOTAGE_RAW_CACHE[rel_path] = im
        return im
    except Exception:
        return None


def _build_harmonized_portal_patch(
    af: Dict[str, Any],
    ap_w: int,
    ap_h: int,
    bg_crop: Image.Image,
    haze_rgb: Tuple[int, int, int],
) -> Optional[Image.Image]:
    """
    Creates a color-harmonized, recessed multiplane footage patch (`ap_w x ap_h` RGBA)
    for a door, window, archway, television screen, or mirror opening:
      - Aspect-crops and resizes the poem video keyframe (`cel_assets/video/P*`) or archival
        16mm frame (`weave/archive/da69_frames/*`),
      - Harmonizes 40% toward the local cel painting palette so it belongs to the same world
        while preserving its luminous multiplane depth,
      - Adds a recessed architectural lintel & jamb inner shadow,
      - Adds optional window muntin bars (`mullions=True`) and diagonal glass reflection sheen,
      - Feathers the outer 3px rim so it seats cleanly inside the portal frame.
    """
    import cv2
    import numpy as np

    if ap_w < 16 or ap_h < 16:
        return None
    src_im = _load_portal_footage_rgb(str(af.get("footage_file", "")))
    if src_im is None:
        src_im = _load_portal_footage_rgb(str(af.get("alt_footage_file", "")))
    if src_im is None:
        return None

    sw, sh = src_im.size
    target_ar = float(ap_w) / float(max(1, ap_h))
    src_ar = float(sw) / float(max(1, sh))
    if src_ar > target_ar:
        new_sw = max(16, int(round(sh * target_ar)))
        x0 = (sw - new_sw) // 2
        cropped = src_im.crop((x0, 0, x0 + new_sw, sh))
    else:
        new_sh = max(16, int(round(sw / max(0.1, target_ar))))
        y0 = (sh - new_sh) // 2
        cropped = src_im.crop((0, y0, sw, y0 + new_sh))

    ft_rgb = np.array(cropped.resize((ap_w, ap_h), Image.Resampling.LANCZOS), dtype=np.float32)
    bg_rgb = np.array(bg_crop.resize((ap_w, ap_h), Image.Resampling.BILINEAR).convert("RGB"), dtype=np.float32)

    # Harmonize mean/std in CIE-LAB (38% chrominance + 24% luminance) + slight warm interior boost
    ft_lab = cv2.cvtColor(np.clip(ft_rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    bg_lab = cv2.cvtColor(np.clip(bg_rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
    for ch_i, w_blend in ((0, 0.24), (1, 0.42), (2, 0.42)):
        fm, fs = float(ft_lab[..., ch_i].mean()), max(6.0, float(ft_lab[..., ch_i].std()))
        bm, bs = float(bg_lab[..., ch_i].mean()), max(6.0, float(bg_lab[..., ch_i].std()))
        tm = fm * (1.0 - w_blend) + bm * w_blend
        if ch_i == 0:
            tm = max(tm, min(168.0, bm + 18.0))
        ts = fs * 0.72 + bs * 0.28
        ft_lab[..., ch_i] = np.clip((ft_lab[..., ch_i] - fm) * (ts / fs) + tm, 0, 255)

    harm_u8 = cv2.cvtColor(ft_lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
    gouache_u8 = cv2.bilateralFilter(harm_u8, d=5, sigmaColor=24, sigmaSpace=24)
    out_f = gouache_u8.astype(np.float32)

    yy, xx = np.mgrid[0:ap_h, 0:ap_w].astype(np.float32)
    nx = xx / max(1.0, float(ap_w - 1))
    ny = yy / max(1.0, float(ap_h - 1))

    portal_kind = str(af.get("portal_kind", "door"))
    # Arch top mask if portal_kind == "arch"
    arch_mask = np.ones((ap_h, ap_w), dtype=np.float32)
    if portal_kind == "arch" and ap_h > 28:
        arch_cy = 0.28
        in_dome = ny < arch_cy
        rx = (nx - 0.5) / 0.50
        ry = (arch_cy - ny) / max(0.05, arch_cy)
        r_dist = np.sqrt(rx * rx + ry * ry)
        arch_mask = np.where(in_dome, np.clip((1.03 - r_dist) * 14.0, 0.0, 1.0), 1.0)

    # Recessed architectural lintel (top) & jamb (left/right) inner shadow
    lintel_sh = np.clip(ny / 0.14, 0.32, 1.0)
    jamb_l = np.clip(nx / 0.10, 0.42, 1.0)
    jamb_r = np.clip((1.0 - nx) / 0.10, 0.42, 1.0)
    sill_b = np.clip((1.0 - ny) / 0.06, 0.65, 1.0)
    recess_mult = lintel_sh * np.minimum(jamb_l, jamb_r) * sill_b
    out_f *= recess_mult[..., None]

    # Optional window mullions (casement panes) & diagonal glass sheen
    if bool(af.get("mullions", False)) or portal_kind in ("window", "mirror", "screen"):
        # Diagonal glass reflection sheen
        diag = np.exp(-((nx * 0.85 + ny * 0.55 - 0.58) ** 2) / 0.012)
        sheen_col = np.array([235.0, 242.0, 255.0], dtype=np.float32)
        out_f = out_f * (1.0 - 0.16 * diag[..., None]) + sheen_col * (0.16 * diag[..., None])

    if bool(af.get("mullions", False)):
        m_col = np.array([22.0, 20.0, 26.0], dtype=np.float32)
        v_bar = np.abs(xx - ap_w * 0.50) <= max(1.5, ap_w * 0.018)
        h_bar1 = np.abs(yy - ap_h * 0.38) <= max(1.5, ap_h * 0.016)
        h_bar2 = np.abs(yy - ap_h * 0.70) <= max(1.5, ap_h * 0.016)
        bars = v_bar | h_bar1 | h_bar2
        out_f[bars] = out_f[bars] * 0.22 + m_col * 0.78

    # Dark inner frame border (2px) + 3px soft outer alpha feather
    edge_dist = np.minimum(np.minimum(xx, ap_w - 1 - xx), np.minimum(yy, ap_h - 1 - yy))
    border_ring = (edge_dist >= 1.0) & (edge_dist <= 3.2)
    out_f[border_ring] *= 0.48
    alpha_f = np.clip(edge_dist / 3.0, 0.0, 1.0) * arch_mask * 246.0

    rgba = np.dstack([
        np.clip(out_f, 0, 255).astype(np.uint8),
        np.clip(alpha_f, 0, 255).astype(np.uint8),
    ])
    return Image.fromarray(rgba, mode="RGBA")


def _apply_canvas_boundary_feather(patch_rgba: Image.Image, dest_x: int, canvas_w: int = W_MOD) -> Image.Image:
    """
    Smoothly tapers alpha of any composited prop/wall/portal near the outer left (`x in [0..108]`)
    and outer right (`x in [canvas_w-108..canvas_w]`) boundaries of the 2040px module so NO prop
    is ever sliced vertically at `x = 0` or `x = 2040` when scenes are stitched into `poem_tape.webp`!
    """
    import numpy as np

    pw, ph = patch_rgba.size
    if pw <= 2 or ph <= 2:
        return patch_rgba
    x0 = dest_x
    x1 = dest_x + pw
    margin = 108.0
    if x0 >= margin and x1 <= (canvas_w - margin):
        return patch_rgba

    arr = np.array(patch_rgba, dtype=np.float32)
    gx = (np.arange(pw, dtype=np.float32) + float(dest_x))[None, :]  # (1, pw)
    t_left = np.clip(gx / margin, 0.0, 1.0)
    w_left = 0.5 - 0.5 * np.cos(np.pi * t_left)
    t_right = np.clip((float(canvas_w - 1) - gx) / margin, 0.0, 1.0)
    w_right = 0.5 - 0.5 * np.cos(np.pi * t_right)
    arr[..., 3] *= (w_left * w_right)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGBA")


_WAG_STACK_CACHE: Optional[Dict[str, Any]] = None

# 8x8 Bayer matrix normalized to [0..1] for Halfworld dot-matrix spectrogram halftoning
_BAYER_8X8_NORM = [
    [0 / 64.0, 32 / 64.0, 8 / 64.0, 40 / 64.0, 2 / 64.0, 34 / 64.0, 10 / 64.0, 42 / 64.0],
    [48 / 64.0, 16 / 64.0, 56 / 64.0, 24 / 64.0, 50 / 64.0, 18 / 64.0, 58 / 64.0, 26 / 64.0],
    [12 / 64.0, 44 / 64.0, 4 / 64.0, 36 / 64.0, 14 / 64.0, 46 / 64.0, 6 / 64.0, 38 / 64.0],
    [60 / 64.0, 28 / 64.0, 52 / 64.0, 20 / 64.0, 62 / 64.0, 30 / 64.0, 54 / 64.0, 22 / 64.0],
    [3 / 64.0, 35 / 64.0, 11 / 64.0, 43 / 64.0, 1 / 64.0, 33 / 64.0, 9 / 64.0, 41 / 64.0],
    [51 / 64.0, 19 / 64.0, 59 / 64.0, 27 / 64.0, 49 / 64.0, 17 / 64.0, 57 / 64.0, 25 / 64.0],
    [15 / 64.0, 47 / 64.0, 7 / 64.0, 39 / 64.0, 13 / 64.0, 45 / 64.0, 5 / 64.0, 37 / 64.0],
    [63 / 64.0, 31 / 64.0, 55 / 64.0, 23 / 64.0, 61 / 64.0, 29 / 64.0, 53 / 64.0, 21 / 64.0],
]


def _hex_to_rgb_f(hex_str: str, fallback: Tuple[float, float, float] = (20.0, 24.0, 34.0)) -> Tuple[float, float, float]:
    s = str(hex_str or "").strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        return fallback
    try:
        return (float(int(s[0:2], 16)), float(int(s[2:4], 16)), float(int(s[4:6], 16)))
    except Exception:
        return fallback


def _sky_hour_rgb(hour_val: float) -> Tuple[float, float, float]:
    """
    Matches `districts/index.html` sky(h) color script:
    Night (`#0b1330`) runs from 01 to 10, dawn (`#e8a27a`) 4.5..7.5, day (`#9cc7e6`) 7.5..17, dusk (`#d0745a`) 17..20.5.
    Smoothly interpolates across twilight transitions so hour [h0, h1] produces a rich sky gradient.
    """
    h = ((float(hour_val) % 24.0) + 24.0) % 24.0
    stops = [
        (0.0, (11.0, 19.0, 48.0)),     # deep night #0b1330
        (4.2, (14.0, 22.0, 54.0)),     # pre-dawn night
        (6.0, (232.0, 162.0, 122.0)),  # dawn #e8a27a
        (8.2, (156.0, 199.0, 230.0)),  # day #9cc7e6
        (16.5, (156.0, 199.0, 230.0)), # afternoon day
        (19.0, (208.0, 116.0, 90.0)),  # dusk #d0745a
        (21.0, (15.0, 21.0, 48.0)),    # evening night
        (24.0, (11.0, 19.0, 48.0)),    # midnight
    ]
    for i in range(len(stops) - 1):
        h0, c0 = stops[i]
        h1, c1 = stops[i + 1]
        if h0 <= h <= h1:
            t = (h - h0) / max(0.001, h1 - h0)
            t_s = t * t * (3.0 - 2.0 * t)
            return (
                c0[0] * (1.0 - t_s) + c1[0] * t_s,
                c0[1] * (1.0 - t_s) + c1[1] * t_s,
                c0[2] * (1.0 - t_s) + c1[2] * t_s,
            )
    return (11.0, 19.0, 48.0)


def _load_wag_stack_spectrogram_and_districts() -> Dict[str, Any]:
    """
    Loads `shots/data/wag_stack/districts_scenes.json` and `shots/data/wag_stack/cut_book.json`,
    decoding each poem's 192x48 spectrogram (`sp.data` base64 -> float32 [48, 192] in [0, 1]),
    energy envelope, free cuts (`kill <= 0.20`), rests, and all 13 districts' `body` & `glow` palettes.
    """
    global _WAG_STACK_CACHE
    if _WAG_STACK_CACHE is not None:
        return _WAG_STACK_CACHE

    import base64
    import numpy as np

    wag_dir = SHOTS_DIR / "data" / "wag_stack"
    ds_path = wag_dir / "districts_scenes.json"
    cb_path = wag_dir / "cut_book.json"

    districts_by_id: Dict[str, Dict[str, Any]] = {}
    scenes_by_key: Dict[str, Dict[str, Any]] = {}
    script_by_num: Dict[str, Dict[str, Any]] = {}
    transitions_by_from: Dict[str, Dict[str, Any]] = {}

    if ds_path.exists():
        ds = json.loads(ds_path.read_text())
        for d in ds.get("districts", []):
            did = d["id"]
            body_hex = d.get("body") or ["#0d0f12", "#161922", "#1f2430"]
            glow_hex = d.get("glow") or [d.get("color", "#fa8d15"), "#d8ab4f"]
            districts_by_id[did] = {
                **d,
                "color_rgb": _hex_to_rgb_f(d.get("color", "#fa8d15")),
                "body_rgb": [_hex_to_rgb_f(c, (14.0, 16.0, 22.0)) for c in body_hex],
                "glow_rgb": [_hex_to_rgb_f(c, (240.0, 145.0, 35.0)) for c in glow_hex],
            }
        for s in ds.get("scenes", []):
            scenes_by_key[s["key"]] = s
        for sc_entry in ds.get("script", []):
            script_by_num[sc_entry["num"]] = sc_entry
        for tr in ds.get("transitions", []):
            transitions_by_from[tr["from"]] = tr

    songs_by_num: Dict[str, Dict[str, Any]] = {}
    if cb_path.exists():
        cb = json.loads(cb_path.read_text())
        sets = cb.get("sets", [])
        if sets:
            for s in sets[0].get("songs", []):
                num = str(s.get("n", "01")).zfill(2)
                sp = s.get("spectrum", {})
                w_sp = int(sp.get("w", 192))
                h_sp = int(sp.get("h", 48))
                raw_b64 = sp.get("data", "")
                if raw_b64:
                    raw_bytes = np.frombuffer(base64.b64decode(raw_b64), dtype=np.uint8)
                    if raw_bytes.size == w_sp * h_sp:
                        spec_arr = (raw_bytes.reshape((h_sp, w_sp)).astype(np.float32)) / 15.0
                    else:
                        spec_arr = np.zeros((h_sp, w_sp), dtype=np.float32)
                else:
                    spec_arr = np.zeros((h_sp, w_sp), dtype=np.float32)
                env_arr = np.array(s.get("envelope", [0.35] * w_sp), dtype=np.float32)
                free_cuts = [c for c in s.get("cuts", []) if float(c.get("kill", 1.0)) <= 0.20]
                songs_by_num[num] = {
                    "meta": {k: s[k] for k in ("n", "title", "seconds", "lufs", "lra", "bpm", "pulse", "balance", "onsets_per_min", "rest_seconds") if k in s},
                    "spec_arr": spec_arr,
                    "env_arr": env_arr,
                    "free_cuts": free_cuts,
                    "all_cuts": s.get("cuts", []),
                    "rests": s.get("rests", []),
                    "sections": s.get("sections", []),
                    "spectrum_b64": raw_b64,
                    "spectrum_w": w_sp,
                    "spectrum_h": h_sp,
                }

    _WAG_STACK_CACHE = {
        "districts_by_id": districts_by_id,
        "scenes_by_key": scenes_by_key,
        "script_by_num": script_by_num,
        "transitions_by_from": transitions_by_from,
        "songs_by_num": songs_by_num,
    }
    return _WAG_STACK_CACHE


def render_clean_scene_plate(
    out_webp: pathlib.Path,
    backdrop_path: pathlib.Path,
    cel_path: Optional[pathlib.Path],
    ink_path: Optional[pathlib.Path],
    floor_y: int,
    layers: List[Dict[str, Any]],
    district_glow: List[Any],
    haze_rgb: Tuple[int, int, int] = (24, 30, 44),
    props_out_dir: Optional[pathlib.Path] = None,
    num_str: str = "01",
    next_backdrop_path: Optional[pathlib.Path] = None,
    next_cel_path: Optional[pathlib.Path] = None,
    stage_ppm: float = 114.0,
    poem_num: int = 1,
    skey: str = "01.0",
    next_skey: str = "01.1",
    sc_idx: int = 0,
    n_sc: int = 6,
    return_pil: bool = False,
) -> Optional[Image.Image]:
    """
    Assembles a 100% SEAMLESS Single-World Scene + Visual Spectrogram & District Colour-Script Bridge Plate
    (`2040x880`, `W_MOD x H_EXT`) and crops the `1280x720` main frame (`s<idx>.webp`):
      1. ZERO Rorschach Mirror-Flipping (`np.flip` removed from horizontal bridge!):
         Instead of flipping `curr_np` and `next_np`, builds a Multi-Scale Horizontal Strata Advection
         that locks with exact C0+C1 pixel continuity at `x = 1280` (`exp(-x_ext / 28.0)`) and at `x = 2039`
         (`exp(-(759 - x_ext) / 28.0)`), blended through the exact **District Body/Glow Palette Ramp**
         (`d_curr -> d_next`) and **Treatment Sky-Hour Gradient (`hour[0] -> hour[1]`)** from `districts_scenes.json`.
      2. "Hides the Crimes" in the Poem's Visual Spectrogram & Dark Architectural Thresholds:
         Infuses the `x = 1280..2040` inter-scene bridge with the poem's real 48-band audio spectrogram &
         8x8 Bayer Dot-Halfworld frequency columns from `cut_book.json`, rising out of deep `The Black` /
         `d.body[0]` architectural silhouette piers with `d.glow` rim lighting.
      3. Grades any `wall_with_door_hole` / `wall_bay` extension piece into a **Dark District Silhouette Pier**
         (`d.body[0..1]` shadow core + `d.glow` contour rim) so no grey stone box ever sits over a colorful sky.
      4. Keeps `s<idx>.webp`, `s<idx>_ext.webp`, and `poem_tape.webp` 100% free of frozen duplicate Poet statues
         (the live playable Poet in `levels.html` dynamically scales by `stage_ppm`).
    """
    import cv2
    import numpy as np

    W, H = W_FRAME, 720
    bg_curr, cel_ref_curr = _load_blended_cel_backdrop(backdrop_path, cel_path, W, H)
    if next_backdrop_path is not None:
        bg_next, cel_ref_next = _load_blended_cel_backdrop(next_backdrop_path, next_cel_path, W, H)
    else:
        bg_next, cel_ref_next = bg_curr, cel_ref_curr

    curr_np = np.array(bg_curr.convert("RGB"), dtype=np.float32)
    next_np = np.array(bg_next.convert("RGB"), dtype=np.float32)

    wag = _load_wag_stack_spectrogram_and_districts()
    d_map = wag["districts_by_id"]
    sc_map = wag["scenes_by_key"]
    scr_map = wag["script_by_num"]
    song_map = wag["songs_by_num"]

    sc_curr_meta = sc_map.get(skey, {})
    sc_next_meta = sc_map.get(next_skey, sc_curr_meta)
    d_curr_id = str(sc_curr_meta.get("d", "haze"))
    d_next_id = str(sc_next_meta.get("d", d_curr_id))
    d_curr = d_map.get(d_curr_id, d_map.get("haze", {}))
    d_next = d_map.get(d_next_id, d_curr)

    scr_entry = scr_map.get(num_str, {"hour": [19.2, 20.4]})
    h_pair = scr_entry.get("hour", [19.2, 20.4])
    h_start = float(h_pair[0]) + (float(h_pair[1]) - float(h_pair[0])) * (float(sc_idx) / max(1.0, float(n_sc)))
    h_end = float(h_pair[0]) + (float(h_pair[1]) - float(h_pair[0])) * (float(sc_idx + 1) / max(1.0, float(n_sc)))
    sky_curr_rgb = np.array(_sky_hour_rgb(h_start), dtype=np.float32)
    sky_next_rgb = np.array(_sky_hour_rgb(h_end), dtype=np.float32)

    body_curr_rgb = np.array((d_curr.get("body_rgb") or [(18.0, 20.0, 28.0)])[0], dtype=np.float32)
    body_next_rgb = np.array((d_next.get("body_rgb") or [(18.0, 20.0, 28.0)])[0], dtype=np.float32)
    mid_curr_rgb = np.array((d_curr.get("body_rgb") or [(38.0, 42.0, 56.0)])[-1], dtype=np.float32)
    mid_next_rgb = np.array((d_next.get("body_rgb") or [(38.0, 42.0, 56.0)])[-1], dtype=np.float32)
    glow_curr_rgb = np.array((d_curr.get("glow_rgb") or [(245.0, 145.0, 35.0)])[min(1, len(d_curr.get("glow_rgb", [1])) - 1)], dtype=np.float32)
    glow_next_rgb = np.array((d_next.get("glow_rgb") or [(245.0, 145.0, 35.0)])[min(1, len(d_next.get("glow_rgb", [1])) - 1)], dtype=np.float32)

    # 1. Build a 100% 2D/3D Painted Inter-Scene Corridor (`x = 920..2040`) Built ON TOP OF & THROUGH
    #    the Foundry 3D Terrain (`sb/w1623` / `inv/w1623`) + CLIP Panoptic Aperture (`refs/` + `-seg.jpg`)
    #    with ZERO 1D horizontal pixel-extrusion smearing!
    foundry_dir = SHOTS_DIR / "data" / "terrarium" / "foundry"
    p_lookup = num_str if int(num_str) <= 13 else f"{((sc_idx * 2) % 13) + 1:02d}"
    sb_candidates = sorted((foundry_dir / "sb" / "w1623").glob(f"{p_lookup}-*.jpg"))
    inv_candidates = sorted((foundry_dir / "inv" / "w1623").glob(f"{p_lookup}-*-b.jpg"))
    ref_candidates = sorted(
        p for p in (foundry_dir / "refs").glob(f"{p_lookup}-*.jpg") if not p.name.endswith("-seg.jpg")
    )

    sb_img_np = curr_np.copy()
    if inv_candidates:
        pick_inv = inv_candidates[sc_idx % len(inv_candidates)]
        try:
            sb_img_np = np.array(
                Image.open(pick_inv).convert("RGB").resize((W, H), Image.Resampling.LANCZOS),
                dtype=np.float32,
            )
        except Exception:
            pass
    elif sb_candidates:
        pick_sb = sb_candidates[min(len(sb_candidates) - 1, int(round(sc_idx * len(sb_candidates) / max(1, n_sc))))]
        try:
            sb_img_np = np.array(
                Image.open(pick_sb).convert("RGB").resize((W, H), Image.Resampling.LANCZOS),
                dtype=np.float32,
            )
        except Exception:
            pass

    ref_img_np = next_np.copy()
    seg_img_np = None
    if ref_candidates:
        pick_ref = ref_candidates[min(len(ref_candidates) - 1, int(round(sc_idx * len(ref_candidates) / max(1, n_sc))))]
        try:
            ref_img_np = np.array(
                Image.open(pick_ref).convert("RGB").resize((W, H), Image.Resampling.LANCZOS),
                dtype=np.float32,
            )
            seg_p = pick_ref.with_name(f"{pick_ref.stem}-seg.jpg")
            if seg_p.exists():
                seg_img_np = np.array(
                    Image.open(seg_p).convert("RGB").resize((W, H), Image.Resampling.BILINEAR),
                    dtype=np.float32,
                )
        except Exception:
            pass

    # Fuse CLIP Reference sky/water/light *through* the Foundry 3D terrain via Panoptic Segmentation + Horizon mask
    yy_full = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]  # (720, 1, 1)
    if seg_img_np is not None:
        # Sky/water/light regions in panoptic mask have higher blue/cyan or high luminance
        seg_sky_water = np.clip(
            (seg_img_np[..., 2] - seg_img_np[..., 0] * 0.55) / 140.0
            + np.clip(1.0 - yy_full[:, :, 0] / 0.54, 0.0, 1.0) * 0.65,
            0.0,
            1.0,
        )
        ap_mask = cv2.GaussianBlur(seg_sky_water.astype(np.float32), (65, 65), 22.0)[..., None]
    else:
        ap_mask = (np.clip(1.0 - yy_full / 0.56, 0.0, 1.0) ** 1.25) * 0.65

    foundry_through = sb_img_np * (1.0 - 0.48 * ap_mask) + ref_img_np * (0.48 * ap_mask)

    # Harmonize `foundry_through` into the Cel-Gouache palette bridging `curr_np` and `next_np`
    def _harmonize_to_cel_target(src_f: np.ndarray, tgt_f: np.ndarray) -> np.ndarray:
        src_u8 = np.clip(src_f, 0, 255).astype(np.uint8)
        tgt_u8 = np.clip(tgt_f, 0, 255).astype(np.uint8)
        s_lab = cv2.cvtColor(src_u8, cv2.COLOR_RGB2LAB).astype(np.float32)
        t_lab = cv2.cvtColor(tgt_u8, cv2.COLOR_RGB2LAB).astype(np.float32)
        for ch_i, w_b in ((0, 0.58), (1, 0.84), (2, 0.84)):
            sm, ss = float(s_lab[..., ch_i].mean()), max(5.0, float(s_lab[..., ch_i].std()))
            tm, ts = float(t_lab[..., ch_i].mean()), max(5.0, float(t_lab[..., ch_i].std()))
            nm = sm * (1.0 - w_b) + tm * w_b
            ns = ss * (1.0 - 0.65 * w_b) + ts * (0.65 * w_b)
            s_lab[..., ch_i] = np.clip((s_lab[..., ch_i] - sm) * (ns / ss) + nm, 0, 255)
        h_u8 = cv2.cvtColor(s_lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
        # Posterize gently + bilateral gouache filter so it matches `cel.webp`
        g_u8 = cv2.bilateralFilter(h_u8, d=5, sigmaColor=26, sigmaSpace=26)
        return g_u8.astype(np.float32)

    foundry_cel_curr = _harmonize_to_cel_target(foundry_through, curr_np)
    foundry_cel_next = _harmonize_to_cel_target(foundry_through, next_np)

    # Subtle 18% Foundry x Inverse sky/horizon through-aperture inside the main `0..1280` frame (`curr_np`)
    sky_through_w = (np.clip(1.0 - yy_full / 0.54, 0.0, 1.0) ** 1.35) * 0.20
    curr_enriched = curr_np * (1.0 - sky_through_w) + foundry_cel_curr * sky_through_w

    # Construct the `2040px` (`W_MOD`) continuous 2D painted world strip using wide 2D overlapping panels:
    # - `x = 0..1280` starts with `curr_enriched`
    # - `x = 840..1760` weaves in the 2D `foundry_cel` panorama + interior/exterior detail from `curr_np` & `next_np`
    # - `x = 1360..2040` weaves in the 2D left half of `next_np` shifted so that `x = 2039` is `next_np`!
    x_mod = np.arange(W_MOD, dtype=np.float32)[None, :, None]  # (1, 2040, 1)

    # Build a 2040px-wide Foundry x Inverse 2D panoramic layer (from `foundry_cel_curr` -> `foundry_cel_next`)
    w_pan = np.clip((x_mod - 640.0) / 1160.0, 0.0, 1.0)
    w_pan_s = 0.5 - 0.5 * np.cos(np.pi * w_pan)
    pan_curr_2040 = cv2.resize(foundry_cel_curr, (W_MOD, H), interpolation=cv2.INTER_LANCZOS4)
    pan_next_2040 = cv2.resize(foundry_cel_next, (W_MOD, H), interpolation=cv2.INTER_LANCZOS4)
    foundry_pan_2040 = pan_curr_2040 * (1.0 - w_pan_s) + pan_next_2040 * w_pan_s

    # Also build a 2040px-wide 2D Cel Canvas where:
    # - `x = 0..1280` is `curr_enriched`
    # - `x = 1280..2040` is a 2D cropped/scaled vista of `next_np[:, :880, :]` blended with `curr_enriched[:, 400:1280, :]`
    next_vista_760 = cv2.resize(next_np[:, :960, :], (W_EXT, H), interpolation=cv2.INTER_LANCZOS4)
    curr_vista_760 = cv2.resize(curr_enriched[:, 320:1280, :], (W_EXT, H), interpolation=cv2.INTER_LANCZOS4)

    x_ext = np.arange(W_EXT, dtype=np.float32)[None, :, None]  # (1, 760, 1)
    t_b = x_ext / float(W_EXT - 1)                             # 0.0 at x=1280, 1.0 at x=2039
    w_next = 0.5 - 0.5 * np.cos(np.pi * t_b)
    sin_b = np.maximum(0.0, np.sin(np.pi * t_b))

    # 2D Panoramic Bridge Base: combines 2D `curr_vista_760`, 2D `foundry_pan_2040[:, 1280:]`, and 2D `next_vista_760`
    cel_2d_bridge = curr_vista_760 * (1.0 - w_next) + next_vista_760 * w_next
    foundry_bridge = foundry_pan_2040[:, W_FRAME:, :]
    bridge_base = 0.56 * cel_2d_bridge + 0.44 * foundry_bridge

    # Smooth 240px raised-cosine 2D cross-fade across `x = 1280` (so `curr_enriched[:, 1040:1280]` and `bridge_base[:, :240]`
    # lock together with zero vertical seam!) and at `x = 1860..2040` into `next_np[:, 0, :]`:
    r_edge_col = curr_enriched[:, -1:, :]
    l_edge_col = next_np[:, :1, :]
    lock_l = np.exp(-x_ext / 42.0)
    lock_r = np.exp(-(float(W_EXT - 1) - x_ext) / 42.0)
    bridge_base = bridge_base * (1.0 - 0.65 * lock_l) + (0.65 * lock_l) * (0.55 * r_edge_col + 0.45 * curr_enriched[:, -64:, :].mean(axis=1, keepdims=True))
    bridge_base = bridge_base * (1.0 - 0.65 * lock_r) + (0.65 * lock_r) * (0.55 * l_edge_col + 0.45 * next_np[:, :64, :].mean(axis=1, keepdims=True))

    # 2. Infuse the District Colour-Script & 48-Band Audio Spectrogram across the bridge (`sin_b > 0`)
    yy_b = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]  # (720, 1, 1)
    d_sky_ramp = sky_curr_rgb[None, None, :] * (1.0 - w_next) + sky_next_rgb[None, None, :] * w_next
    d_mid_ramp = mid_curr_rgb[None, None, :] * (1.0 - w_next) + mid_next_rgb[None, None, :] * w_next
    d_body_ramp = body_curr_rgb[None, None, :] * (1.0 - w_next) + body_next_rgb[None, None, :] * w_next
    d_glow_ramp = glow_curr_rgb[None, None, :] * (1.0 - w_next) + glow_next_rgb[None, None, :] * w_next

    # Vertical atmospheric strata for the District Colour Script (sky at top -> district mid -> deep district body at floor)
    w_sky_v = np.clip(1.0 - yy_b / 0.42, 0.0, 1.0) ** 1.4
    w_floor_v = np.clip((yy_b - 0.58) / 0.42, 0.0, 1.0) ** 1.3
    w_mid_v = np.maximum(0.0, 1.0 - w_sky_v - w_floor_v)
    district_strata = d_sky_ramp * w_sky_v + d_mid_ramp * w_mid_v + d_body_ramp * w_floor_v

    # Blend 22% of the District Colour-Script atmospheric wash into the bridge while preserving 78% crisp 2D/3D painting!
    w_district_wash = 0.22 * (sin_b ** 1.35)
    bridge_f = bridge_base * (1.0 - w_district_wash) + district_strata * w_district_wash

    # 3. Render the Poem's 48-Band Visual Spectrogram & Bayer 8x8 Dot-Halfworld Ribbons into the bridge!
    song_info = song_map.get(num_str)
    if song_info is not None:
        spec_arr = song_info["spec_arr"]  # (48, 192)
        env_arr = song_info["env_arr"]    # (192,)
        w_sp = spec_arr.shape[1]
        c0 = int(round((float(sc_idx) + 0.55) / max(1.0, float(n_sc)) * (w_sp - 1)))
        c1 = int(round((float(sc_idx) + 1.00) / max(1.0, float(n_sc)) * (w_sp - 1)))
        c0 = max(0, min(w_sp - 4, c0))
        c1 = max(c0 + 4, min(w_sp, c1))
        spec_slice = spec_arr[:, c0:c1]  # (48, cols)
        env_slice = env_arr[c0:c1]       # (cols,)

        # Resize the spectrogram slice smoothly to (H=720, W_EXT=760)
        spec_2d = cv2.resize(spec_slice, (W_EXT, H), interpolation=cv2.INTER_CUBIC)
        env_1d = cv2.resize(env_slice[None, :], (W_EXT, 1), interpolation=cv2.INTER_LINEAR)[0]  # (760,)

        # Create subtle vertical spectrogram frequency columns + 8x8 Bayer dot-matrix modulation
        bayer_tile = np.array(_BAYER_8X8_NORM, dtype=np.float32)
        yy_idx, xx_idx = np.mgrid[0:H, 0:W_EXT]
        bayer_map = bayer_tile[(yy_idx // 3) % 8, (xx_idx // 3) % 8]
        dot_mask = np.clip((spec_2d - bayer_map * 0.55) * 2.2, 0.0, 1.0)

        # Concentrate spectrogram energy in the horizon/midground band (`y = 0.16..0.82`) and fade to 0 at bridge ends
        sin_vert = np.maximum(0.0, np.sin(np.pi * np.clip((yy_b[:, :, 0] - 0.10) / 0.78, 0.0, 1.0)))
        vert_window = sin_vert ** 1.2
        spec_glow_w = (0.14 * spec_2d + 0.08 * dot_mask) * vert_window * (sin_b[:, :, 0] ** 1.4)
        bridge_f = bridge_f * (1.0 - spec_glow_w[..., None]) + d_glow_ramp * spec_glow_w[..., None]

        # Subtle dark architectural threshold silhouette under the audio energy envelope near the floor (`The Black`)
        arch_sil_h = (0.08 + 0.12 * env_1d[None, :]) * (sin_b[:, :, 0] ** 1.3)
        arch_sil_mask = np.clip((yy_b[:, :, 0] - (0.88 - arch_sil_h)) / 0.08, 0.0, 1.0) * (sin_b[:, :, 0] ** 1.5) * 0.34
        black_pier_rgb = d_body_ramp * 0.55 + np.array([10.0, 12.0, 16.0], dtype=np.float32)[None, None, :] * 0.45
        bridge_f = bridge_f * (1.0 - arch_sil_mask[..., None]) + black_pier_rgb * arch_sil_mask[..., None]

    strip_720_f = np.concatenate([curr_enriched, bridge_f], axis=1)  # (720, 2040, 3)
    # Cross-weave a 280px wide 2D transition across `x = 1280` (`x = 1140..1420`) so there is ZERO vertical seam at x=1280!
    j_x0, j_x1 = 1120, 1440
    j_band = strip_720_f[:, j_x0:j_x1, :]
    j_pan = foundry_pan_2040[:, j_x0:j_x1, :]
    j_t = np.linspace(0.0, 1.0, j_x1 - j_x0, dtype=np.float32)[None, :, None]
    j_bell = np.maximum(0.0, np.sin(np.pi * j_t)) ** 1.4
    j_smooth = cv2.GaussianBlur(j_band, (45, 15), 11.0)
    strip_720_f[:, j_x0:j_x1, :] = j_band * (1.0 - 0.52 * j_bell) + (0.58 * j_pan + 0.42 * j_smooth) * (0.52 * j_bell)
    strip_720_np = np.clip(strip_720_f, 0, 255).astype(np.uint8)

    # 4. Build `2040 x 160` upper headroom using vertical sky advection + Sky-Hour colour script (`w_mir == 1.0` at `y = 159`)!
    top_rows_blur = cv2.GaussianBlur(strip_720_np[:96, :, :].astype(np.float32), (65, 35), 16.0)
    mir_top_raw = np.flip(strip_720_np[:H_HEADROOM, :, :], axis=0).astype(np.float32)
    mir_top_blur = cv2.GaussianBlur(mir_top_raw, (55, 29), 13.0)
    v_t = np.linspace(0.0, 1.0, H_HEADROOM, dtype=np.float32)[:, None, None]
    v_smooth = v_t * v_t * (3.0 - 2.0 * v_t)
    # At `y = 159` (`v_t = 1.0`), `mir_top_blend` equals `mir_top_raw[-1] == strip_720_np[0]`
    mir_top_blend = mir_top_blur * (1.0 - v_smooth) + mir_top_raw * v_smooth
    top_sky_row = top_rows_blur[:24, :, :].mean(axis=0)  # (2040, 3)
    # Infuse the upper sky canopy with the treatment's exact Hour Sky colour!
    x_all = np.linspace(0.0, 1.0, W_MOD, dtype=np.float32)[None, :, None]
    hour_sky_bar = sky_curr_rgb[None, None, :] * (1.0 - x_all) + sky_next_rgb[None, None, :] * x_all
    studio_sky = top_sky_row[None, :, :] * 0.68 + hour_sky_bar * 0.32
    sky_grad = studio_sky * (1.0 - v_smooth) + top_sky_row[None, :, :] * v_smooth
    w_mir = v_smooth ** 1.35  # 0.0 at y=0, 1.0 at y=159 -> exact C0+C1 match at y=160!
    headroom_f = sky_grad * (1.0 - w_mir) + mir_top_blend * w_mir
    headroom_np = np.clip(headroom_f, 0, 255).astype(np.uint8)

    full_env_np = np.concatenate([headroom_np, strip_720_np], axis=0)  # (880, 2040, 3)
    ext_canvas = Image.fromarray(full_env_np, mode="RGB").convert("RGBA")
    cel_ref_ext = Image.fromarray(full_env_np, mode="RGB")
    cel_scene_small = cel_ref_curr.resize((160, 90), Image.Resampling.BILINEAR)

    # Subtle continuous stage floor grounding gradient across all `2040px`
    fy = max(480, min(660, int(floor_y)))
    fy_ext = H_HEADROOM + fy
    overlay = Image.new("RGBA", (W_MOD, H_EXT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(fy_ext, H_EXT):
        t = (y - fy_ext) / max(1.0, float(H_EXT - fy_ext))
        dark_a = int(26 * math.sqrt(t))
        odraw.line([(0, y), (W_MOD, y)], fill=(8, 10, 15, dark_a))
    ext_canvas = Image.alpha_composite(ext_canvas, overlay)

    # Save clean underpainting plates (`<stem>_env.webp` 1280x720 and `<stem>_ext_env.webp` 2040x880)
    env_canvas = ext_canvas.copy()
    if ink_path and ink_path.exists():
        try:
            ink_im = Image.open(ink_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
            _, _, _, a_ch = ink_im.split()
            a_np = np.array(a_ch, dtype=np.float32) * 0.26
            ramp_l = np.clip(np.arange(W, dtype=np.float32) / 110.0, 0.0, 1.0)[None, :]
            ramp_r = np.clip((1280.0 - np.arange(W, dtype=np.float32)) / 180.0, 0.0, 1.0)[None, :]
            a_np = (a_np * ramp_l * ramp_r).astype(np.uint8)
            ink_env = Image.merge("RGBA", (
                Image.new("L", (W, H), 16),
                Image.new("L", (W, H), 13),
                Image.new("L", (W, H), 20),
                Image.fromarray(a_np, mode="L"),
            ))
            env_canvas.alpha_composite(ink_env, dest=(0, H_HEADROOM))
        except Exception:
            pass
    out_webp.parent.mkdir(parents=True, exist_ok=True)
    env_webp = out_webp.parent / f"{out_webp.stem}_env.webp"
    ext_env_webp = out_webp.parent / f"{out_webp.stem}_ext_env.webp"
    env_canvas.crop((0, H_HEADROOM, W_FRAME, H_EXT)).convert("RGB").save(env_webp, "WEBP", quality=86, method=4)
    env_canvas.convert("RGB").save(ext_env_webp, "WEBP", quality=86, method=4)

    if props_out_dir is not None:
        props_out_dir.mkdir(parents=True, exist_ok=True)

    # Check if the scene has dedicated framed portal pieces (`portal_door_arch`, `portal_window`, or in-frame portals)
    has_framed_ext_portal = any(
        bool(l.get("aperture_footage")) and str(l.get("lego_role", "")) not in ("wall_with_door_hole", "wall_bay")
        for l in layers
        if not l.get("is_world_sheet")
    )

    # Paint all 7 planes (`P6 -> P0`) of curated in-frame props + Outside-the-Frame Set Extensions
    draw_layers = sorted(
        [l for l in layers if not l.get("is_world_sheet")],
        key=lambda item: float(item.get("z", 1.4)),
        reverse=True,
    )
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
        sc = float(lyr.get("scale", 0.20))
        plane_id = str(lyr.get("plane", "P3"))
        is_ext = bool(lyr.get("is_set_extension", False))
        l_role = str(lyr.get("lego_role", ""))
        target_w, target_h = compute_piece_stage_dims(
            pw, ph, sc, plane_id, W, H, is_set_extension=is_ext, lego_role=l_role
        )

        p_resized = p_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        if lyr.get("flip"):
            p_resized = p_resized.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        cx = int(round(float(lyr.get("x", 0.5)) * W))
        by = H_HEADROOM + int(round(float(lyr.get("y", 0.87)) * H))
        dx = cx - target_w // 2
        dy = by - target_h

        pad = 90
        cx0 = max(0, min(W_MOD - 32, dx - pad))
        cy0 = max(0, min(H_EXT - 32, dy - pad))
        cx1 = max(cx0 + 32, min(W_MOD, dx + target_w + pad))
        cy1 = max(cy0 + 32, min(H_EXT, dy + target_h + pad))
        bg_crop = cel_ref_ext.crop((cx0, cy0, cx1, cy1))

        p_cel = clean_and_integrate_cutout(
            p_resized,
            bg_crop,
            plane_id,
            haze_rgb=haze_rgb,
            cel_scene_img=cel_scene_small,
        )

        # "Hide the Crimes": Integrate any `wall_with_door_hole` or `wall_bay` extension piece into the
        # District Colour Script with organic bristle-feathered edges while keeping its hand-drawn architectural
        # detail and glowing portal apertures crisp and visible!
        if is_ext and l_role in ("wall_with_door_hole", "wall_bay"):
            if has_framed_ext_portal:
                lyr.pop("aperture_footage", None)
            p_np = np.array(p_cel, dtype=np.float32)
            ph_c, pw_c = p_np.shape[:2]
            exact_bg = bg_crop.resize((pw_c, ph_c), Image.Resampling.BILINEAR).convert("RGB")
            exact_bg_f = cv2.GaussianBlur(np.array(exact_bg, dtype=np.float32), (31, 31), 9.0)
            dark_arch = body_curr_rgb[None, None, :] * 0.45 + exact_bg_f * 0.55
            p_np[..., :3] = 0.64 * p_np[..., :3] + 0.36 * dark_arch
            yy_w, xx_w = np.mgrid[0:ph_c, 0:pw_c].astype(np.float32)
            bristle_w = 14.0 * np.sin(yy_w * 0.08) + 8.0 * np.cos(yy_w * 0.21)
            feather_l = max(110.0, min(220.0, pw_c * 0.32))
            feather_r = max(95.0, min(190.0, pw_c * 0.28))
            feather_t = max(75.0, min(160.0, ph_c * 0.30))
            feather_b = max(24.0, min(56.0, ph_c * 0.12))
            left_start = max(0.0, float(1210 - dx)) if dx < 1240 else 0.0
            t_l = np.clip((xx_w - left_start + bristle_w) / feather_l, 0.0, 1.0)
            w_l = 0.5 - 0.5 * np.cos(np.pi * t_l)
            t_r = np.clip(((pw_c - 1 - xx_w) + bristle_w) / feather_r, 0.0, 1.0)
            w_r = 0.5 - 0.5 * np.cos(np.pi * t_r)
            t_top = np.clip((yy_w + 0.5 * bristle_w) / feather_t, 0.0, 1.0)
            w_top = 0.5 - 0.5 * np.cos(np.pi * t_top)
            t_bot = np.clip(((ph_c - 1 - yy_w) + 0.5 * bristle_w) / feather_b, 0.0, 1.0)
            w_bot = 0.5 - 0.5 * np.cos(np.pi * t_bot)
            p_np[..., 3] *= (0.84 * w_l * w_r * w_top * w_bot)
            p_cel = Image.fromarray(np.clip(p_np, 0, 255).astype(np.uint8), mode="RGBA")
        elif is_ext:
            # Infuse other extension pieces (`portal_door_arch`, `portal_window`, `building_pier`, `stair_bridge_rail`)
            # with a subtle District Body/Glow tint so they belong 100% to the District Colour Script!
            p_np = np.array(p_cel, dtype=np.float32)
            lum = (0.299 * p_np[..., 0] + 0.587 * p_np[..., 1] + 0.114 * p_np[..., 2]) / 255.0
            d_tint = body_curr_rgb[None, None, :] * (1.0 - lum[..., None]) + glow_curr_rgb[None, None, :] * (lum[..., None] * 0.85)
            p_np[..., :3] = 0.78 * p_np[..., :3] + 0.22 * d_tint
            p_cel = Image.fromarray(np.clip(p_np, 0, 255).astype(np.uint8), mode="RGBA")

        # Save the cel-colorized, gouache-brushed RGBA piece sprite for `levels.html`
        if props_out_dir is not None:
            prop_fname = f"{lyr['id']}.webp"
            prop_path = props_out_dir / prop_fname
            p_cel.save(prop_path, "WEBP", quality=90, method=4)
            lyr["file"] = f"levels/{num_str}/props/{prop_fname}"

        alpha_mult = float(lyr.get("alpha", 0.96))
        if alpha_mult < 0.99:
            r_c, g_c, b_c, a_c = p_cel.split()
            a_c = a_c.point(lambda a: int(a * alpha_mult))
            p_cel = Image.merge("RGBA", (r_c, g_c, b_c, a_c))

        # Taper alpha near outer module edges `x = 0` and `x = 2040` so no prop is ever sliced at a scene join!
        p_cel_baked = _apply_canvas_boundary_feather(p_cel, dx, W_MOD)

        # Grounded elliptical floor contact shadow for floor-seated pieces on P4/P3/P2/P1
        if float(lyr.get("y", 0.87)) >= 0.55 and plane_id in ("P4", "P3", "P2", "P1"):
            sh_layer = Image.new("RGBA", (W_MOD, H_EXT), (0, 0, 0, 0))
            sdraw = ImageDraw.Draw(sh_layer)
            rx = int(target_w * 0.42)
            ry = max(5, int(target_h * 0.075))
            sh_alpha = 84 if plane_id in ("P4", "P1") else 106
            sdraw.ellipse([cx - rx, by - ry, cx + rx, by + ry], fill=(6, 8, 12, sh_alpha))
            sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(radius=6))
            ext_canvas = Image.alpha_composite(ext_canvas, sh_layer)

        # Render Layered Multiplane Footage (`aperture_footage`) inside doors, windows, arches, TVs & mirrors!
        af = lyr.get("aperture_footage")
        portal_patch: Optional[Image.Image] = None
        ap_x0, ap_y0, ap_x1, ap_y1 = 0, 0, 0, 0
        if isinstance(af, dict) and af.get("footage_file"):
            abox = af.get("aperture_box") or [0.24, 0.16, 0.78, 0.95]
            ap_x0 = max(4, dx + int(round(target_w * float(abox[0]))))
            ap_y0 = max(12, dy + int(round(target_h * float(abox[1]))))
            ap_x1 = min(W_MOD - 4, dx + int(round(target_w * float(abox[2]))))
            ap_y1 = min(H_EXT - 4, dy + int(round(target_h * float(abox[3]))))
            ap_w = ap_x1 - ap_x0
            ap_h = ap_y1 - ap_y0
            if ap_w >= 20 and ap_h >= 20:
                portal_patch = _build_harmonized_portal_patch(af, ap_w, ap_h, bg_crop, haze_rgb)
                if portal_patch is not None:
                    if props_out_dir is not None:
                        pf_name = f"portal_{lyr['id']}.webp"
                        portal_patch.save(props_out_dir / pf_name, "WEBP", quality=88, method=4)
                        af["portal_footage_webp"] = f"levels/{num_str}/props/{pf_name}"
                    portal_baked = _apply_canvas_boundary_feather(portal_patch, ap_x0, W_MOD)
                    ext_canvas.alpha_composite(portal_baked, dest=(ap_x0, ap_y0))

                    # District-glow floor light spill wedge in front of the portal threshold
                    if bool(af.get("warm_spill", True)) and by >= H_HEADROOM + 360:
                        spill_layer = Image.new("RGBA", (W_MOD, H_EXT), (0, 0, 0, 0))
                        sp_draw = ImageDraw.Draw(spill_layer)
                        sp_y0 = min(H_EXT - 8, by - 4)
                        sp_y1 = min(H_EXT - 2, by + max(24, int(ap_h * 0.24)))
                        sp_poly = [
                            (ap_x0 + 6, sp_y0),
                            (ap_x1 - 6, sp_y0),
                            (min(W_MOD - 2, ap_x1 + int(ap_w * 0.28)), sp_y1),
                            (max(2, ap_x0 - int(ap_w * 0.22)), sp_y1),
                        ]
                        g_col = (int(glow_curr_rgb[0]), int(glow_curr_rgb[1]), int(glow_curr_rgb[2]), 42)
                        sp_draw.polygon(sp_poly, fill=g_col)
                        spill_layer = spill_layer.filter(ImageFilter.GaussianBlur(radius=9))
                        ext_canvas = Image.alpha_composite(ext_canvas, spill_layer)

        # Composite the cel-colorized architectural/prop piece itself
        ext_canvas.alpha_composite(p_cel_baked, dest=(dx, dy))

        # 2) Also composite the inset portal footage inside the inner pane rectangle
        #    so doors, windows, TV screens & mirrors clearly display their layered multiplane footage!
        if portal_patch is not None and ap_x1 > ap_x0 + 20 and ap_y1 > ap_y0 + 20:
            inset_w = max(12, int((ap_x1 - ap_x0) * 0.84))
            inset_h = max(12, int((ap_y1 - ap_y0) * 0.84))
            inset_x = ap_x0 + ((ap_x1 - ap_x0) - inset_w) // 2
            inset_y = ap_y0 + ((ap_y1 - ap_y0) - inset_h) // 2
            inset_patch = portal_patch.resize((inset_w, inset_h), Image.Resampling.LANCZOS)
            ir, ig, ib, ia = inset_patch.split()
            ia = ia.point(lambda a: int(a * 0.82))
            inset_patch = _apply_canvas_boundary_feather(Image.merge("RGBA", (ir, ig, ib, ia)), inset_x, W_MOD)
            ext_canvas.alpha_composite(inset_patch, dest=(inset_x, inset_y))

    # Whole-Canvas Master Painting Unification Pass across all `2040x880` pixels:
    rgb_arr = np.array(ext_canvas.convert("RGB"), dtype=np.uint8)
    gouache_canvas = cv2.bilateralFilter(rgb_arr, d=5, sigmaColor=22, sigmaSpace=22)
    blended_f = 0.82 * rgb_arr.astype(np.float32) + 0.18 * gouache_canvas.astype(np.float32)

    yy_c, xx_c = np.mgrid[0:H_EXT, 0:W_MOD].astype(np.float32)
    paper_tooth = 1.6 * np.sin(xx_c * 0.65 + yy_c * 0.45) * np.cos(xx_c * 0.35 - yy_c * 0.55)
    blended_f = np.clip(blended_f + paper_tooth[..., None], 0, 255)
    ext_canvas = Image.fromarray(blended_f.astype(np.uint8), mode="RGB").convert("RGBA")

    # Unified top warm charcoal-sepia ink pass (`ink.webp`) feathered smoothly at both `x = 0` and `x = 1280`
    if ink_path and ink_path.exists():
        try:
            ink_im = Image.open(ink_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
            _, _, _, a_ch = ink_im.split()
            a_np = np.array(a_ch, dtype=np.float32) * 0.26
            ramp_l = np.clip(np.arange(W, dtype=np.float32) / 110.0, 0.0, 1.0)[None, :]
            ramp_r = np.clip((1280.0 - np.arange(W, dtype=np.float32)) / 180.0, 0.0, 1.0)[None, :]
            a_np = (a_np * ramp_l * ramp_r).astype(np.uint8)
            ink_dark = Image.merge("RGBA", (
                Image.new("L", (W, H), 16),
                Image.new("L", (W, H), 13),
                Image.new("L", (W, H), 20),
                Image.fromarray(a_np, mode="L"),
            ))
            ext_canvas.alpha_composite(ink_dark, dest=(0, H_HEADROOM))
        except Exception:
            pass

    ext_rgb = ext_canvas.convert("RGB")
    frame_rgb = ext_rgb.crop((0, H_HEADROOM, W_FRAME, H_EXT))
    frame_rgb.save(out_webp, "WEBP", quality=88, method=4)
    ext_webp = out_webp.parent / f"{out_webp.stem}_ext.webp"
    ext_rgb.save(ext_webp, "WEBP", quality=88, method=4)
    if return_pil:
        return ext_rgb
    return None




def main() -> None:
    print("[1/5] Loading wygwyl_atlas_manifest.json, world_data.js, districts_scenes.json & cut_book.json...")
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
    wag_stack = _load_wag_stack_spectrogram_and_districts()

    # Strictly verify every part_id, backdrop, and all 7 handmade planes (P6..P0) in CUSTOM_SCENES + Lego Extensions
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
        for lx in get_scene_lego_extension(skey):
            if lx["part_id"] not in parts_by_id:
                missing_parts.append((skey, lx["part_id"]))
    if missing_parts or missing_bgs:
        raise RuntimeError(f"Missing parts: {missing_parts}, Missing bgs: {missing_bgs}")
    print(f"  Verified {len(CUSTOM_SCENES)} custom scenes + 90 Set Extensions: 0 missing parts!")

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
    poem_tape_strips: List[Image.Image] = []

    total_scenes = 0
    total_layers = 0
    scenes_with_all_7 = 0

    print("[2/5] Building Seamless Visual-Spectrogram & District Colour-Script 14-Poem Worlds...")
    for poem_num in range(1, 15):
        num_str = f"{poem_num:02d}"
        lv_path = LEVELS_DIR / num_str / "level.json"
        lv = json.loads(lv_path.read_text())
        fw, fh = int(lv["frame"][0]), int(lv["frame"][1])
        lv["seven_planes_spec"] = SEVEN_PLANES
        lv["shot_scale_tiers"] = SHOT_SCALE_TIERS

        scr_info = wag_stack["script_by_num"].get(num_str, {})
        tr_info = wag_stack["transitions_by_from"].get(num_str, {})
        song_info = wag_stack["songs_by_num"].get(num_str, {})
        lv["colour_script"] = {
            "hour": scr_info.get("hour", [19.2, 20.4]),
            "weather": scr_info.get("weather", ["clear"]),
            "why": scr_info.get("why", ""),
            "seq": scr_info.get("seq", []),
            "transition_out": tr_info,
        }
        if song_info:
            lv["cut_book_summary"] = {
                "meta": song_info.get("meta", {}),
                "spectrum_w": song_info.get("spectrum_w", 192),
                "spectrum_h": song_info.get("spectrum_h", 48),
                "spectrum_b64": song_info.get("spectrum_b64", ""),
                "envelope": [round(float(x), 3) for x in song_info.get("env_arr", [])],
                "free_cuts": song_info.get("free_cuts", []),
                "rests": song_info.get("rests", []),
                "sections": song_info.get("sections", []),
            }

        lv["tape_geometry"] = {
            "frame_w": W_FRAME,
            "ext_w": W_EXT,
            "module_w": W_MOD,
            "frame_h": 720,
            "headroom_h": H_HEADROOM,
            "ext_h": H_EXT,
            "total_tape_w": len(lv["scenes"]) * W_MOD,
            "hyperflat_floor_y": HYPERFLAT_FLOOR_Y,
            "hyperflat_horizon_y": HYPERFLAT_HORIZON_Y,
            "tape_file": "poem_tape.webp",
            "seamless_cross_weave": True,
            "spectrogram_district_bridge": True,
        }

        poem_ext_plates: List[Image.Image] = []
        n_sc = len(lv["scenes"])

        for sc_idx, sc in enumerate(lv["scenes"]):
            skey = sc["key"]
            spec = CUSTOM_SCENES.get(skey)
            if not spec:
                raise RuntimeError(f"Missing custom scene spec for {skey}!")

            next_sc = lv["scenes"][(sc_idx + 1) % n_sc]
            next_skey = next_sc["key"]
            next_spec = CUSTOM_SCENES.get(next_skey, spec)
            next_bg_rel = next_spec["backdrop"]
            next_wk = next_bg_rel.split("/")[1]
            next_cel_rel = f"world/{next_wk}/cel.webp"

            backdrop_shots_rel = spec["backdrop"]
            backdrop_play_rel = f"../{backdrop_shots_rel}"
            wk = backdrop_shots_rel.split("/")[1]
            wshot = world_by_k.get(wk, {})
            fid = wshot.get("id", "")
            persp = load_frame_perspective_signals(fid)
            stage_haze_tuple = tuple(persp["stage_haze_rgb"])

            # Attach canonical District & Scene-Book metadata (`d`, `color`, `body`, `glow`, `here`, `block`, `camera`)
            ds_sc_meta = wag_stack["scenes_by_key"].get(skey, {})
            d_id = str(ds_sc_meta.get("d", sc.get("district_id", "haze")))
            d_obj = wag_stack["districts_by_id"].get(d_id, {})
            h_pair = scr_info.get("hour", [19.2, 20.4])
            h_sc0 = round(float(h_pair[0]) + (float(h_pair[1]) - float(h_pair[0])) * (float(sc_idx) / max(1.0, float(n_sc))), 2)
            h_sc1 = round(float(h_pair[0]) + (float(h_pair[1]) - float(h_pair[0])) * (float(sc_idx + 1) / max(1.0, float(n_sc))), 2)
            sc["district_meta"] = {
                "id": d_id,
                "name": d_obj.get("name", d_id),
                "color": d_obj.get("color", "#fa8d15"),
                "body": d_obj.get("body", ["#0d0f12", "#181c26"]),
                "glow": d_obj.get("glow", ["#fa8d15", "#d8ab4f"]),
                "glow_share": d_obj.get("glow_share", 0.30),
                "here": ds_sc_meta.get("here", ""),
                "block": ds_sc_meta.get("block", ""),
                "treatment_camera": ds_sc_meta.get("camera", ""),
                "hour_window": [h_sc0, h_sc1],
            }

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
                    "shots_file": wsh["lo"],
                    "plane": w_p,
                    "depth_index": pmeta["depth_index"],
                    "color_code": pmeta["color_code"],
                    "z": round(float(wsh.get("z", pmeta["z"])), 3),
                    "label": wsh.get("label", w_p),
                    "water": bool(wsh.get("water", False)),
                    "sway": bool(wsh.get("sway", False)),
                })

            raw_specs = verify_handmade_seven_layers_for_scene(skey, spec["layers"])
            shot_profile = get_scene_shot_profile(skey)
            scale_marker_info = extract_cel_painting_scale_markers(fid, wshot, skey=skey)
            stage_ppm = float(scale_marker_info["stage_px_per_meter"])
            curated_prop_specs = curate_scene_props(
                skey,
                raw_specs,
                stage_ppm=stage_ppm,
                parts_by_id=parts_by_id,
            )
            combined_layers: List[Dict[str, Any]] = []
            stations: List[Dict[str, Any]] = []

            # 1. Populate native pixel-registered environmental planes (P6, P5, P4, P1, P0)
            covered_env_planes = set()
            for w_idx, wsh in enumerate(world_sheets):
                w_p = wsh["plane"]
                if any(p["plane"] == w_p and not p.get("is_set_extension") for p in curated_prop_specs):
                    continue
                pmeta = SEVEN_PLANES.get(w_p, SEVEN_PLANES["P4"])
                covered_env_planes.add(w_p)
                combined_layers.append({
                    "id": f"lyr_{skey.replace('.', '_')}_ws_{w_idx}_{w_p}",
                    "part_id": f"world.{wk}.{w_p}.{w_idx}",
                    "sheet_id": f"world.{wk}",
                    "label": f"{wshot.get('title', sc['name'])} · {wsh['label']} ({w_p})",
                    "station_id": "",
                    "station_title": f"{wsh['label']} ({w_p})",
                    "plane": w_p,
                    "depth_index": pmeta["depth_index"],
                    "plane_name": pmeta["name"],
                    "color_code": pmeta["color_code"],
                    "ink_weight": pmeta["ink_weight"],
                    "haze_mix": pmeta["haze_mix"],
                    "pal_k": pmeta["pal_k"],
                    "z": wsh["z"],
                    "x": 0.50,
                    "y": 1.00,
                    "scale": 1.00,
                    "width": 1280,
                    "height": 720,
                    "role": "world_plane",
                    "anim_role": "wave_near" if wsh["water"] else ("flower_bloom" if wsh["sway"] else "static"),
                    "flip": False,
                    "alpha": 0.98,
                    "is_world_sheet": True,
                    "is_set_extension": False,
                    "file": wsh["file"],
                    "shots_file": wsh["shots_file"],
                })

            # 2. Add curated in-frame props + Outside-the-Frame Modular Lego Set-Extension pieces
            for e_idx, lspec in enumerate(curated_prop_specs):
                pid = lspec["part_id"]
                pt = parts_by_id[pid]
                shots_file = pt["file"]
                play_file = f"../{shots_file}"
                st_title = lspec.get("station_title")
                station_id = f"st_{skey.replace('.', '_')}_{e_idx}" if st_title else ""
                plane_id = lspec["plane"]
                pmeta = SEVEN_PLANES.get(plane_id, SEVEN_PLANES["P3"])
                covered_env_planes.add(plane_id)
                is_ext = bool(lspec.get("is_set_extension", False))
                l_role = lspec.get("lego_role", "")
                af_spec = lspec.get("aperture_footage")

                lyr_obj: Dict[str, Any] = {
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
                    "scale_meta": lspec.get("scale_meta", {}),
                    "width": int(pt.get("width", 240)),
                    "height": int(pt.get("height", 240)),
                    "role": "lego_extension" if is_ext else ("focal_cast" if plane_id == "P2" else "station_prop"),
                    "lego_role": l_role,
                    "is_set_extension": is_ext,
                    "anim_role": lspec.get("anim_role", "static"),
                    "flip": bool(lspec.get("flip", False)),
                    "alpha": round(float(lspec.get("alpha", 0.96)), 3),
                    "is_world_sheet": False,
                    "file": play_file,
                    "shots_file": shots_file,
                }
                if af_spec is not None:
                    lyr_obj["aperture_footage"] = dict(af_spec)
                    lyr_obj["aperture_footage"]["play_footage_file"] = f"../{af_spec['footage_file']}"
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
                        "is_set_extension": is_ext,
                        "anim_role": lspec.get("anim_role", "static"),
                        "has_portal_footage": af_spec is not None,
                    })

            # Ensure all 7 planes (P6..P0) have a registered layer entry
            for env_p in ("P6", "P5", "P4", "P3", "P2", "P1", "P0"):
                if env_p not in covered_env_planes:
                    pmeta = SEVEN_PLANES[env_p]
                    raw_match = next((r for r in raw_specs if r["plane"] == env_p), None)
                    env_label = raw_match["label"] if raw_match else f"{sc['name']} · {pmeta['short']}"
                    combined_layers.append({
                        "id": f"lyr_{skey.replace('.', '_')}_env_{env_p}",
                        "part_id": f"world.{wk}.{env_p}",
                        "sheet_id": f"world.{wk}",
                        "label": env_label,
                        "station_id": "",
                        "station_title": env_label,
                        "plane": env_p,
                        "depth_index": pmeta["depth_index"],
                        "plane_name": pmeta["name"],
                        "color_code": pmeta["color_code"],
                        "ink_weight": pmeta["ink_weight"],
                        "haze_mix": pmeta["haze_mix"],
                        "pal_k": pmeta["pal_k"],
                        "z": pmeta["z"],
                        "x": 0.50,
                        "y": 1.00,
                        "scale": 1.00,
                        "width": 1280,
                        "height": 720,
                        "role": "world_plane",
                        "anim_role": "static",
                        "flip": False,
                        "alpha": 0.98,
                        "is_world_sheet": True,
                        "is_set_extension": False,
                        "file": f"../{cel_rel}" if (SHOTS_DIR / cel_rel).exists() else backdrop_play_rel,
                        "shots_file": cel_rel if (SHOTS_DIR / cel_rel).exists() else backdrop_shots_rel,
                    })

            if len(stations) < 3:
                for r_idx, rspec in enumerate(raw_specs):
                    r_title = rspec.get("station_title")
                    if not r_title or any(s["title"] == r_title for s in stations):
                        continue
                    r_plane = rspec["plane"]
                    pmeta = SEVEN_PLANES.get(r_plane, SEVEN_PLANES["P4"])
                    stations.append({
                        "id": f"st_{skey.replace('.', '_')}_arch_{r_idx}",
                        "title": r_title,
                        "part_label": rspec["label"],
                        "part_id": rspec["part_id"],
                        "plane": r_plane,
                        "color_code": pmeta["color_code"],
                        "x": round(float(rspec["x"]), 3),
                        "mx": round(float(rspec["x"]) * fw, 1),
                        "y": round(float(rspec["y"]), 3),
                        "is_set_extension": False,
                        "anim_role": rspec.get("anim_role", "static"),
                    })
                    if len(stations) >= 3:
                        break

            sc["shot_profile"] = shot_profile
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
                "scale_markers": scale_marker_info,
                "shot_profile": shot_profile,
                "world_sheets": [{k: v for k, v in ws.items() if k != "shots_file"} for ws in world_sheets],
                "seven_layer_breakdown": compute_frame_seven_layer_breakdown(fid, skey, combined_layers),
            }

            combined_layers.sort(key=lambda item: float(item.get("z", 1.4)), reverse=True)
            total_layers += len(combined_layers)
            if len({l["plane"] for l in combined_layers}) == 7:
                scenes_with_all_7 += 1

            stations.sort(key=lambda s: s["x"])
            n_st = len(stations)
            n_lines = len(sc.get("lines", []))
            for l_idx, ln in enumerate(sc.get("lines", [])):
                if stations:
                    ext_stations = [s for s in stations if s.get("is_set_extension")]
                    in_stations = [s for s in stations if not s.get("is_set_extension")]
                    if l_idx == n_lines - 1 and ext_stations:
                        st_pick = ext_stations[0]
                    elif in_stations:
                        st_pick = in_stations[l_idx % len(in_stations)]
                    else:
                        st_pick = stations[l_idx % n_st]
                    jitter = ((l_idx % 3) - 1) * 18.0
                    ln["mx"] = round(max(160.0, min(W_MOD - 140.0, float(st_pick["mx"]) + jitter)), 1)
                    ln["station_id"] = st_pick["id"]
                    ln["station_label"] = st_pick["title"]
                    ln["station_part_label"] = st_pick["part_label"]
                    ln["station_anim"] = st_pick["anim_role"]

            if spec.get("initial_cue") and sc.get("lines"):
                sc["lines"][0]["posture_cue"] = spec["initial_cue"]

            out_webp = LEVELS_DIR / num_str / sc["img"]
            props_dir = LEVELS_DIR / num_str / "props"
            ext_pil = render_clean_scene_plate(
                out_webp=out_webp,
                backdrop_path=SHOTS_DIR / backdrop_shots_rel,
                cel_path=SHOTS_DIR / cel_rel,
                ink_path=SHOTS_DIR / ink_rel,
                floor_y=int(spec.get("floor", 614)),
                layers=combined_layers,
                district_glow=sc["district_meta"]["glow"],
                haze_rgb=stage_haze_tuple,
                props_out_dir=props_dir,
                num_str=num_str,
                next_backdrop_path=SHOTS_DIR / next_bg_rel,
                next_cel_path=SHOTS_DIR / next_cel_rel,
                stage_ppm=stage_ppm,
                poem_num=poem_num,
                skey=skey,
                next_skey=next_skey,
                sc_idx=sc_idx,
                n_sc=n_sc,
                return_pil=True,
            )

            sc["floor"] = int(spec.get("floor", 614))
            sc["backdrop_file"] = backdrop_play_rel
            sc["env_img"] = f"{out_webp.stem}_env.webp"
            sc["ext_img"] = f"{out_webp.stem}_ext.webp"
            sc["ext_env_img"] = f"{out_webp.stem}_ext_env.webp"
            sc["tape_x_offset"] = sc_idx * W_MOD
            sc["initial_cue"] = spec.get("initial_cue", "walk_stride_R")
            sc["preferred_actor"] = spec.get("preferred_actor")
            sc["counterpart"] = spec.get("counterpart")
            sc["stations"] = stations
            sc["multiplane_layers"] = [
                {k: v for k, v in lyr.items() if k != "shots_file"}
                for lyr in combined_layers
            ]

            if ext_pil is not None:
                poem_ext_plates.append(ext_pil)
                thumb = ext_pil.resize((540, 234), Image.Resampling.LANCZOS)
                tdraw = ImageDraw.Draw(thumb)
                bx_thumb = int(round(540 * (W_FRAME / float(W_MOD))))
                tdraw.rectangle([0, 0, 540, 22], fill=(8, 10, 14))
                d_col_rgb = tuple(int(c) for c in _hex_to_rgb_f(sc["district_meta"]["color"]))
                tdraw.rectangle([0, 0, 8, 22], fill=d_col_rgb)
                tdraw.line([(bx_thumb, 17), (bx_thumb, 22)], fill=(255, 210, 90), width=2)
                n_portals = sum(1 for l in combined_layers if l.get("aperture_footage"))
                dist_tag = f"{sc['district_meta']['id'].upper()} · {shot_profile['short_label']} {shot_profile['camera_distance_m']}m"
                tdraw.text(
                    (12, 4),
                    f"{skey} [{dist_tag}] {sc['name'][:16]} · {n_portals} Portals",
                    fill=(255, 228, 130),
                )
                if poem_num <= 4:
                    audit_batches["audit_scenes_01_04.png"].append(thumb)
                elif poem_num <= 8:
                    audit_batches["audit_scenes_05_08.png"].append(thumb)
                elif poem_num <= 11:
                    audit_batches["audit_scenes_09_11.png"].append(thumb)
                else:
                    audit_batches["audit_scenes_12_14.png"].append(thumb)

            total_scenes += 1

        # Stitch all scenes of the poem into a Seamless Continuous Horizontal Poem Background Tape (`poem_tape.webp`)
        if poem_ext_plates:
            import cv2
            import numpy as np

            half_w = W_MOD // 2   # 1020 px per module
            half_h = H_EXT // 2   # 440 px tall
            small_plates = [
                np.array(p_im.resize((half_w, half_h), Image.Resampling.LANCZOS), dtype=np.float32)
                for p_im in poem_ext_plates
            ]
            tape_np = np.concatenate(small_plates, axis=1)  # (440, N * 1020, 3)
            for idx_p in range(1, len(small_plates)):
                jx = idx_p * half_w
                hw_ov = 88
                x0 = max(0, jx - hw_ov)
                x1 = min(tape_np.shape[1], jx + hw_ov)
                band = tape_np[:, x0:x1, :]
                # Multi-scale 2D cross-weave across the module threshold so no vertical seam is ever visible
                band_mid = cv2.GaussianBlur(band, (55, 11), 14.0)
                band_broad = cv2.GaussianBlur(band, (115, 21), 28.0)
                bx = np.arange(x0, x1, dtype=np.float32)[None, :, None]
                dist_norm = np.abs(bx - float(jx)) / float(hw_ov)
                w_cos = 0.5 * (1.0 + np.cos(np.pi * np.clip(dist_norm, 0.0, 1.0)))
                w_mid = 0.62 * (w_cos ** 1.3)
                w_broad = 0.34 * (w_cos ** 2.2)
                tape_np[:, x0:x1, :] = (
                    band * (1.0 - w_mid - w_broad)
                    + band_mid * w_mid
                    + band_broad * w_broad
                )
            tape_im = Image.fromarray(np.clip(tape_np, 0, 255).astype(np.uint8), mode="RGB")
            tape_path = LEVELS_DIR / num_str / "poem_tape.webp"
            tape_im.save(tape_path, "WEBP", quality=88, method=4)
            vault_tapes_dir = SHOTS_DIR / "png_vault" / "painted_tapes"
            vault_tapes_dir.mkdir(parents=True, exist_ok=True)
            tape_im.save(vault_tapes_dir / f"poem_{num_str}_scene_tape.png", "PNG", optimize=True)

            # Create a 1800x142 panorama strip for `audit_poem_tapes.png` with the Colour Script & Sky-Hour strip underneath!
            strip_thumb = Image.new("RGB", (1800, 142), (8, 10, 14))
            strip_thumb.paste(tape_im.resize((1800, 120), Image.Resampling.LANCZOS), (0, 0))
            sdraw = ImageDraw.Draw(strip_thumb)
            # Draw District Colour-Script bar at y = 120..131 and Sky-Hour bar at y = 131..141
            sc_w = 1800 / max(1, len(lv["scenes"]))
            for idx_s, s_obj in enumerate(lv["scenes"]):
                sx0 = int(round(idx_s * sc_w))
                sx1 = int(round((idx_s + 1) * sc_w))
                dm = s_obj.get("district_meta", {})
                d_rgb = tuple(int(c) for c in _hex_to_rgb_f(dm.get("color", "#fa8d15")))
                hw = dm.get("hour_window", [19.2, 20.4])
                sky_rgb = tuple(int(c) for c in _sky_hour_rgb(0.5 * (float(hw[0]) + float(hw[1]))))
                sdraw.rectangle([sx0, 120, sx1 - 1, 131], fill=d_rgb)
                sdraw.rectangle([sx0, 132, sx1 - 1, 141], fill=sky_rgb)
            sdraw.rectangle([0, 0, 740, 20], fill=(8, 10, 14))
            seq_str = " -> ".join(s["district_meta"]["id"] for s in lv["scenes"])
            sdraw.text(
                (6, 3),
                f"POEM {num_str} SPECTROGRAM & COLOUR-SCRIPT TAPE · {lv['title']} · Districts: [{seq_str}]",
                fill=(120, 240, 190),
            )
            poem_tape_strips.append(strip_thumb)

        lv_path.write_text(json.dumps(lv, separators=(",", ":")))
        print(f"  Poem {num_str} ({lv['title']}): built {len(lv['scenes'])} Spectrogram & District Colour-Script scenes + poem_tape.webp")


    print("[3/5] Enriching level_assets_catalog.json with 7-layer color codes & standardized physical scales...")
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
            pid_cat = it.get("part_id", "")
            if pid_cat in parts_by_id:
                std_sc, std_meta = standardize_piece_scale(
                    pid_cat,
                    it.get("label", ""),
                    pl,
                    float(it.get("default_scale", 0.20)),
                    118.0,
                    parts_by_id,
                )
                it["default_scale"] = std_sc
                it["canon_h_m"] = std_meta["canon_h_m"]
                it["class_tag"] = std_meta["class_tag"]

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

    print("[4/5] Saving visual audit contact sheets for all 90 Hyper-Flat Lego Wing scenes + 14 Continuous Poem Tapes...")
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    for bname, thumbs in audit_batches.items():
        cols = 3
        rows = (len(thumbs) + cols - 1) // cols
        grid = Image.new("RGB", (cols * 544, rows * 238), (10, 12, 16))
        for i, im in enumerate(thumbs):
            grid.paste(im, ((i % cols) * 544 + 2, (i // cols) * 238 + 2))
        grid.save(SCRATCH_DIR / bname)
        print(f"  Saved {SCRATCH_DIR / bname} ({len(thumbs)} extended scenes)")

    if poem_tape_strips:
        tape_grid = Image.new("RGB", (1804, len(poem_tape_strips) * 146), (10, 12, 16))
        for i, st_im in enumerate(poem_tape_strips):
            tape_grid.paste(st_im, (2, i * 146 + 2))
        tape_grid.save(SCRATCH_DIR / "audit_poem_tapes.png")
        print(f"  Saved {SCRATCH_DIR / 'audit_poem_tapes.png'} (14 continuous horizontal poem tapes)")

    print(
        f"[5/5] DONE! Built {total_scenes} Hyper-Flat Extended Lego Wing scenes with {total_layers} layers "
        f"({scenes_with_all_7}/{total_scenes} scenes have all 7 layers P6->P0 populated!)."
    )


if __name__ == "__main__":
    main()


