#!/usr/bin/env python3
"""
lego_set_extensions.py
======================
Defines the Hyper-Flat Camera Datum and Modular "Lego" Set-Extension Assemblies
built OUTSIDE the `1280x720` frame (`x in [0.92 .. 1.58]`, spanning `x_px = 1180 .. 2040`)
to fill the inter-scene holes and connect every poem (`01` .. `14`) into a
Continuous Horizontal Background Tape (`N_scenes * 2040 x 720`).

Inspired directly by the director's two reference compositions:
  1. Building outside the frame with modular walls that have doorway holes
     (`12.set.temple_backroom__p01`, `01.hero.severn__p02`, `02.set.living_room_1990s__p02`,
     `13.hero.cafe__p01`) capped/paired with stone gables & portal arches (`03.hero.chapel__p01`,
     `14.set.vintage_party__p03`, `05.set.winged_marble_gate__p03`) and connected by horizontal
     catwalks/viaducts (`01.hero.catwalk__p03`, `04.hero.viaduct__p01`).
  2. Continuous horizontal boulevard tapes (`05.hero.perimeter`, `09.hero.canopy`,
     `12.hero.pools`, `13.set.harbor_quay_night_fire`) where repeating fence/wall strips,
     rhythmically spaced palm/street trees, and glowing street lamps bridge seamlessly
     into the next cel frame on the tape.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# Standard geometry of a Scene + Outside-the-Frame Set Extension Module on the Poem Tape:
#   - Main Cel Frame width:     W_FRAME = 1280 px  (normalized x: 0.0000 .. 1.0000)
#   - Side Extension ("Hole"):  W_EXT   =  760 px  (normalized x: 1.0000 .. 1.5938)
#   - Total Module Span:        W_MOD   = 2040 px  (normalized x: 0.0000 .. 1.5938)
#   - Hyper-Flat Camera Datum:  H_STAGE =  720 px, FLOOR_Y = 614 px (y = 0.880), HORIZON_Y = 420 px (y = 0.583)
W_FRAME = 1280
W_EXT = 760
W_MOD = W_FRAME + W_EXT  # 2040 px per scene + side extension module
H_STAGE = 720
HYPERFLAT_FLOOR_Y = 614
HYPERFLAT_HORIZON_Y = 420


def X(
    part_id: str,
    label: str,
    plane: str,
    z: float,
    x: float,
    y: float,
    scale: float,
    lego_role: str = "wall_bay",
    station_title: Optional[str] = None,
    flip: bool = False,
    alpha: float = 0.98,
    preserve_raw_scale: bool = True,
) -> Dict[str, Any]:
    """
    Defines a single Modular Lego Set-Extension Piece placed outside (or bridging out of)
    the `1280x720` frame (`x in [0.90 .. 1.58]`, where `x = 1.00` is the right frame edge `1280px`
    and `x = 1.59375` is `2040px` where the next scene's frame begins on the continuous tape).
    """
    return {
        "part_id": part_id,
        "label": label,
        "plane": plane,
        "z": z,
        "x": x,
        "y": y,
        "scale": scale,
        "lego_role": lego_role,
        "anim_role": "portal_aperture" if "portal" in lego_role or "door" in lego_role else "static",
        "station_title": station_title,
        "flip": flip,
        "alpha": alpha,
        "is_set_extension": True,
        "preserve_raw_scale": preserve_raw_scale,
    }


def boulevard_tape_bridge(
    fence_id: str,
    fence_label: str,
    tree_ids: List[str],
    tree_label: str,
    lamp_id: str,
    lamp_label: str,
    curb_id: str,
    curb_label: str,
    station_title: str,
    floor_y: float = 0.99,
) -> List[Dict[str, Any]]:
    """
    Builds a repeating horizontal Boulevard Tape extension (matching the director's
    second reference image `media_1793295991132_6f4cd1fc.png`):
      - Continuous horizontal fence/wall bays along the hyper-flat horizon/floor line
      - Rhythmically spaced trees (`x = 1.07, 1.22, 1.38, 1.53`)
      - Alternating street lamps (`x = 1.14, 1.30, 1.46`)
      - Continuous foreground curb/hedge strip along `floor_y`
    """
    t0 = tree_ids[0]
    t1 = tree_ids[1 % len(tree_ids)]
    t2 = tree_ids[2 % len(tree_ids)]
    t3 = tree_ids[3 % len(tree_ids)]
    return [
        # Continuous fence / wall strip across the 760px extension gap
        X(fence_id, f"{fence_label} (Bay West)", "P4", 2.46, 1.15, floor_y, 0.50, "boulevard_fence", station_title),
        X(fence_id, f"{fence_label} (Bay East)", "P4", 2.46, 1.44, floor_y, 0.50, "boulevard_fence", None),
        # Rhythmically spaced boulevard trees rising to/above frame top
        X(t0, f"{tree_label} #1", "P4", 2.38, 1.07, floor_y, 0.82, "boulevard_tree", None),
        X(t1, f"{tree_label} #2", "P4", 2.36, 1.22, floor_y, 0.76, "boulevard_tree", None),
        X(t2, f"{tree_label} #3", "P4", 2.38, 1.38, floor_y, 0.85, "boulevard_tree", None),
        X(t3, f"{tree_label} #4", "P4", 2.36, 1.53, floor_y, 0.78, "boulevard_tree", None),
        # Alternating tall street lamps
        X(lamp_id, f"{lamp_label} West", "P3", 1.48, 1.14, floor_y, 0.68, "boulevard_lamp", None),
        X(lamp_id, f"{lamp_label} Center", "P3", 1.48, 1.30, floor_y, 0.68, "boulevard_lamp", None),
        X(lamp_id, f"{lamp_label} East", "P3", 1.48, 1.46, floor_y, 0.68, "boulevard_lamp", None),
        # Continuous ground curb / hedge strip tying the boulevard base together
        X(curb_id, curb_label, "P2", 1.06, 1.297, 1.00, 0.24, "ground_curb", None),
    ]


def catwalk_gable_wall_extension(
    catwalk_deck_id: str,
    catwalk_truss_id: str,
    wall_hole_id: str,
    wall_label: str,
    gable_portal_id: str,
    gable_label: str,
    station_title: str,
    floor_y: float = 0.995,
) -> List[Dict[str, Any]]:
    """
    Builds the exact "Catwalk -> Wall with Doorway Hole -> Stone Gable Portal"
    outside-the-frame Lego assembly from the director's first reference image
    (`media_1793295948484_14eeb0d8.png`):
      1. Horizontal catwalk deck & support truss extending out of the right edge of the frame (`x = 0.94..1.14`)
      2. Full-height plaster/wood-trimmed wall module with an open doorway hole (`x = 1.297`, `y = 0.995`, `scale = 0.98`)
         whose top and bottom align flush with the `1280x720` cel frame!
      3. Stone gabled roof & doorway arch (`x = 1.39`, `y = 0.995`, `scale = 1.22`) seated over the doorway hole,
         with its gabled stone roof rising into the upper architectural headroom above the frame top!
    """
    return [
        X(wall_hole_id, wall_label, "P4", 2.40, 1.297, floor_y, 0.98, "wall_with_door_hole", station_title),
        X(gable_portal_id, gable_label, "P3", 1.36, 1.395, floor_y, 1.22, "gable_portal_cap", f"Enter {gable_label}"),
        X(catwalk_truss_id, "Extended Catwalk Support Truss", "P3", 1.48, 1.05, 0.995, 0.34, "span_truss", None),
        X(catwalk_deck_id, "Extended Iron Catwalk Span", "P2", 1.08, 1.08, 0.91, 0.22, "span_deck", None),
    ]


# ---------------------------------------------------------------------------
# Bespoke Outside-the-Frame Lego Set Extensions for All 90 Scenes (`01.0`..`14.6`)
# ---------------------------------------------------------------------------
SCENE_LEGO_EXTENSIONS: Dict[str, List[Dict[str, Any]]] = {
    # =======================================================================
    # POEM 01 · OUT OF LIFE (Continuous Tape: Bedroom -> Hallway -> Fire Escape -> Gable Portal -> Spire Canyon -> Ballroom -> Trapdoor)
    # =======================================================================
    "01.0": [
        X("12.set.temple_backroom__p01", "Extended Bedroom Plaster Wall & Doorway Hole", "P4", 2.44, 1.28, 0.90, 0.52, "wall_with_door_hole", "Bedroom Doorway Threshold"),
        X("01.hero.severn__p07", "Extended Bedroom Wooden Baseboard Beam", "P3", 1.50, 1.28, 0.92, 0.14, "ground_curb", None),
        X("01.props.window__p13", "Exterior Sash Window & Fire-Escape Balcony", "P3", 1.42, 1.46, 0.76, 0.34, "gable_portal_cap", "Window to the Alley"),
        X("01.props.room__p01", "Hallway Wooden Dresser by the Door", "P3", 1.38, 1.12, 0.89, 0.24, "furniture_anchor", None),
    ],
    "01.1": [
        X("01.hero.severn__p02", "Severn Tenement Wall with Door & Window Holes", "P4", 2.44, 1.26, 0.90, 0.52, "wall_with_door_hole", "Tenement Corridor Wall"),
        X("01.hero.severn__p03", "Recessed Red Corridor Doorway Portal", "P4", 2.38, 1.48, 0.89, 0.42, "gable_portal_cap", "Corridor Exit Portal"),
        X("01.hero.catwalk__p03", "Connecting Iron Fire-Escape Deck", "P3", 1.44, 1.12, 0.88, 0.16, "span_deck", None),
        X("01.hero.severnescape__p04", "Curved Iron Fire-Escape Balcony Grate", "P3", 1.38, 1.38, 0.86, 0.26, "span_deck", None),
    ],
    # Exact match to Director's Uploaded Image 1 (`media_1793295948484_14eeb0d8.png`)!
    "01.2": catwalk_gable_wall_extension(
        catwalk_deck_id="01.hero.catwalk__p03",
        catwalk_truss_id="01.hero.catwalk__p05",
        wall_hole_id="12.set.temple_backroom__p01",
        wall_label="Extended Plaster Wall with Open Doorway Hole",
        gable_portal_id="03.hero.chapel__p01",
        gable_label="Stone Gabled Roof & Doorway Portal",
        station_title="Catwalk to the Stone Gable Door",
        floor_y=0.90,
    ),
    "01.3": [
        X("01.set.city_fall_void__p01", "Vertical Skyscraper Canyon Wall West", "P4", 2.48, 1.14, 0.92, 0.62, "wall_bay", "Spire Canyon Bridge"),
        X("01.set.city_fall_void__p02", "Vertical Skyscraper Spire East", "P4", 2.44, 1.34, 0.92, 0.62, "wall_bay", None),
        X("14.set.vintage_party__p03", "Ballroom Timber Archway Below the Drop", "P3", 1.42, 1.48, 0.90, 0.46, "gable_portal_cap", "Skylight Into the Ballroom"),
        X("01.props.chandeliers__p27", "Suspended Ballroom Crystal Chandelier", "P3", 1.38, 1.48, 0.44, 0.22, "ceiling_fixture", None),
    ],
    "01.4": [
        X("14.set.vintage_party__p02", "1940s Wood-Panelled Ballroom Wall & Window", "P4", 2.44, 1.28, 0.90, 0.52, "wall_with_door_hole", "Ballroom Side Gallery"),
        X("14.set.vintage_party__p01", "Ballroom Coffered Ceiling Cornice Strip", "P4", 2.40, 1.28, 0.36, 0.18, "roof_cornice", None),
        X("14.set.vintage_party__p04", "Polished Parquet Waltz Floor Extension", "P3", 1.48, 1.28, 0.93, 0.20, "span_deck", None),
        X("14.set.vintage_party__p03", "Timber Ballroom Threshold Portal", "P3", 1.38, 1.48, 0.90, 0.46, "gable_portal_cap", "Archway to the Trapdoor"),
    ],
    "01.5": [
        X("01.props.trapdoor__p01", "Parquet Floor Slab with Open Abyss Hole", "P3", 1.46, 1.22, 0.91, 0.38, "wall_with_door_hole", "The Abyss Threshold"),
        X("02.set.black_void__p01", "Inward-Slanting Dark Void Wall West", "P4", 2.44, 1.38, 0.90, 0.58, "wall_bay", None),
        X("02.set.black_void__p02", "Inward-Slanting Dark Void Wall East", "P4", 2.42, 1.52, 0.90, 0.58, "wall_bay", "Into Poem 02 · Flashing Lights"),
        X("01.hero.catwalk__p04", "Safety Iron Railing Along the Rim", "P2", 1.08, 1.12, 0.89, 0.20, "span_deck", None),
    ],

    # =======================================================================
    # POEM 02 · FLASHING LIGHTS (Continuous Tape: Void -> Midnight Bedroom -> 1990s Living Room & Driveway -> Rain Window -> Overseer Bridge)
    # =======================================================================
    "02.0": [
        X("02.hero.drowned-light__p07", "Submerged Stone Archway Span", "P4", 2.46, 1.24, 0.88, 0.44, "gable_portal_cap", "Submerged Corridor Arch"),
        X("02.set.bedroom_night__p01", "Midnight Bedroom Wall with Window Hole", "P4", 2.40, 1.42, 0.90, 0.52, "wall_with_door_hole", "1:08 AM Bedroom Threshold"),
        X("02.set.bedroom_night__p09", "Dark Wooden Bedroom Floorboard Strip", "P3", 1.48, 1.30, 0.93, 0.16, "span_deck", None),
        X("02.set.bedroom_night__p02", "Standing Mirror Frame in the Hall", "P3", 1.38, 1.48, 0.89, 0.38, "gable_portal_cap", None),
    ],
    "02.1": [
        X("02.hero.childhouse__p01", "Blue Clapboard Childhood House Facade", "P4", 2.46, 1.16, 0.90, 0.56, "wall_with_door_hole", "1990s Childhood House"),
        X("02.set.living_room_1990s__p01", "1990s Floral Wallpaper Wall with Window Hole", "P4", 2.40, 1.42, 0.90, 0.50, "wall_with_door_hole", "Living Room Window Wall"),
        X("02.hero.childhouse__p10", "Carved Wooden Eaves Cornice", "P4", 2.36, 1.30, 0.36, 0.16, "roof_cornice", None),
        X("02.set.living_room_1990s__p10", "Dark Wainscot Baseboard Runner", "P3", 1.46, 1.30, 0.92, 0.18, "ground_curb", None),
    ],
    "02.2": [
        X("02.set.living_room_1990s__p02", "1990s Floral Wall with Open Doorway Hole", "P4", 2.44, 1.22, 0.90, 0.52, "wall_with_door_hole", "Living Room Doorway"),
        X("02.hero.childhouse__p07", "Red-Brick Driveway House Wing", "P4", 2.40, 1.48, 0.90, 0.56, "wall_with_door_hole", "Driveway Porch Wing"),
        X("02.set.driveway_road_night__p03", "Wet Asphalt Driveway Extension Strip", "P3", 1.48, 1.32, 0.93, 0.18, "span_deck", None),
        X("02.set.living_room_1990s__p04", "1990s Floral Living Room Sofa", "P3", 1.38, 1.14, 0.89, 0.24, "furniture_anchor", None),
    ],
    "02.3": [
        X("02.set.living_room_1990s__p11", "Suburban Driveway Picture-Window Backing", "P5", 3.80, 1.34, 0.74, 0.32, "vista_backing", None),
        X("02.set.living_room_1990s__p01", "Floral Wall with Picture-Window Hole", "P4", 2.42, 1.34, 0.90, 0.52, "wall_with_door_hole", "Picture Window to Driveway"),
        X("02.set.living_room_1990s__p03", "Pencil-Marked Childhood Doorpost Jamb", "P3", 1.44, 1.08, 0.90, 0.44, "gable_portal_cap", "Doorpost Height Marks"),
        X("02.props.window__p21", "1990s Floral Draped Window Curtains", "P3", 1.38, 1.34, 0.72, 0.28, "window_dressing", None),
    ],
    "02.4": [
        X("02.hero.childhouse__p15", "Shattered Glass Window Aperture", "P4", 2.44, 1.18, 0.76, 0.36, "wall_with_door_hole", "Shattered Driveway Window"),
        X("02.set.overseer_skyline__p06", "Distant Nocturnal City Skyline Strip", "P5", 3.82, 1.36, 0.72, 0.20, "vista_backing", None),
        X("02.set.overseer_skyline__p02", "Nocturnal Overseer Tower West", "P4", 2.40, 1.38, 0.90, 0.48, "wall_bay", "Overseer Skyline Bridge"),
        X("02.set.driveway_road_night__p05", "Rain-Slicked Highway Curb Strip", "P3", 1.46, 1.30, 0.93, 0.18, "span_deck", None),
    ],
    "02.5": [
        X("02.set.overseer_skyline__p07", "Long Steel Highway Bridge Parapet", "P3", 1.46, 1.28, 0.90, 0.16, "span_deck", "Bridge Toward the Chapel"),
        X("02.set.overseer_skyline__p03", "Nocturnal Overseer Tower East", "P4", 2.44, 1.20, 0.90, 0.48, "wall_bay", None),
        X("03.hero.chapel__p01", "Distant Stone Chapel Gable & Doorway", "P4", 2.38, 1.46, 0.89, 0.46, "gable_portal_cap", "Chapel Threshold"),
        X("02.props.tambourine__p15", "Thrown Wooden Tambourine Over the Rail", "P2", 1.06, 1.32, 0.68, 0.18, "story_prop", None),
    ],

    # =======================================================================
    # POEM 03 · HOW TO BREAK OFF AN ENGAGEMENT (Continuous Tape: Gothic Chapel Facade -> Nave Arcade -> Side Doors -> Storm Roof -> Ruined Shore)
    # =======================================================================
    "03.0": [
        X("03.hero.chapel__p06", "Gothic Stone Buttress Arcade Wall", "P4", 2.44, 1.24, 0.90, 0.42, "wall_bay", "Chapel Nave Buttress Wall"),
        X("03.hero.chapel__p02", "Pitched Slate Chapel Roof Slope", "P4", 2.40, 1.24, 0.56, 0.30, "roof_cornice", None),
        X("03.hero.chapel__p01", "Stone Gabled Chapel Portal & Oculus", "P3", 1.40, 1.46, 0.90, 0.48, "gable_portal_cap", "Chapel West Portal"),
        X("03.props.rose-window__p01", "Carved Gothic Rose Window Tracery", "P3", 1.36, 1.46, 0.54, 0.24, "window_dressing", None),
    ],
    "03.1": [
        X("03.hero.chapel.interior-states__p01", "Triple Lancet Stone Nave Window Wall", "P4", 2.44, 1.22, 0.88, 0.48, "wall_with_door_hole", "Nave Lancet Arcade"),
        X("03.hero.chapel__p07", "Exterior Stone Arcade Wall Extension", "P4", 2.40, 1.46, 0.90, 0.42, "wall_bay", None),
        X("03.hero.chapel.interior-states__p05", "Carved Wooden Chapel Pew Row", "P3", 1.42, 1.20, 0.90, 0.26, "furniture_anchor", "Empty Wedding Pew"),
        X("03.hero.chapel.interior-states__p06", "Carved Oak Altar Screen", "P3", 1.38, 1.46, 0.89, 0.28, "furniture_anchor", None),
    ],
    "03.2": [
        X("03.set.chapel_side_doors__p01", "Rusticated Stone Archway with Open Portal Hole", "P4", 2.42, 1.28, 0.90, 0.56, "wall_with_door_hole", "Chapel Stone Side Arch"),
        X("03.set.chapel_side_doors__p02", "Heavy Timber Left Chapel Door Leaf", "P3", 1.44, 1.15, 0.89, 0.42, "gable_portal_cap", None),
        X("03.set.chapel_side_doors__p03", "Heavy Timber Right Chapel Door Leaf", "P3", 1.44, 1.41, 0.89, 0.42, "gable_portal_cap", None),
        X("03.set.chapel_side_doors__p04", "Weathered Stone Threshold Step Slab", "P2", 1.08, 1.28, 0.93, 0.16, "ground_curb", None),
    ],
    "03.3": [
        X("03.hero.chapel.decay__p06", "Weathered Stone Chapel Wall in Storm", "P4", 2.44, 1.24, 0.90, 0.42, "wall_bay", "Storm-Struck Nave Wall"),
        X("03.hero.chapel.decay__p02", "Moss-Patched Slate Roof Slope", "P4", 2.40, 1.24, 0.56, 0.30, "roof_cornice", None),
        X("03.hero.chapel.decay__p01", "Cracked Stone Gable Portal", "P3", 1.40, 1.46, 0.90, 0.48, "gable_portal_cap", "Shattered Nave Threshold"),
        X("03.hero.chapel.interior-states__p11", "Rain-Soaked Wooden Pew", "P3", 1.36, 1.22, 0.90, 0.25, "furniture_anchor", None),
    ],
    "03.4": [
        X("03.hero.chapel.ruin__p06", "Collapsed Stone Arcade Wall", "P4", 2.44, 1.22, 0.90, 0.36, "wall_bay", "Collapsed Nave Arcade"),
        X("03.hero.chapel.ruin__p02", "Broken Timber & Slate Roof Truss", "P4", 2.40, 1.22, 0.62, 0.28, "roof_cornice", None),
        X("03.hero.chapel.ruin__p01", "Ruined Stone Gable Archway", "P3", 1.40, 1.46, 0.90, 0.44, "gable_portal_cap", "Ruined Shore Arch"),
        X("03.set.remnants_shore__p03", "Driftwood & Wet Shingle Shore Strip", "P2", 1.08, 1.30, 0.93, 0.14, "ground_curb", None),
    ],
    "03.5": [
        X("03.set.remnants_shore__p01", "Tidewater Horizon Band", "P5", 3.80, 1.30, 0.78, 0.18, "vista_backing", None),
        X("03.hero.chapel.ruin__p12", "Broken Stone Rose-Window Ruin", "P4", 2.42, 1.18, 0.89, 0.38, "wall_with_door_hole", "Ruined Shore Wall"),
        X("04.hero.viaduct__p03", "First Stone Viaduct Arch (+4m Datum)", "P3", 1.42, 1.44, 0.90, 0.46, "gable_portal_cap", "Viaduct Toward Poem 04"),
        X("03.set.remnants_shore__p04", "Salt-Line Shore Causeway Strip", "P2", 1.08, 1.30, 0.93, 0.14, "ground_curb", None),
    ],

    # =======================================================================
    # POEM 04 · NEVERMORE (Continuous Tape: Ash Shore -> Stone Viaduct Arches -> Incline Trail -> Night Garden Boulevard -> Western Bloom)
    # =======================================================================
    "04.0": [
        X("04.set.shore_night__p01", "Nocturnal Sea Horizon Strip", "P5", 3.80, 1.30, 0.76, 0.18, "vista_backing", None),
        X("04.hero.viaduct__p01", "Three-Arch Stone Viaduct Bridge Span", "P4", 2.44, 1.28, 0.89, 0.44, "span_deck", "Stone Viaduct Bridge"),
        X("04.set.shore_night__p06", "Gnarled Driftwood Stump on Shore", "P3", 1.42, 1.12, 0.90, 0.28, "boulevard_tree", None),
        X("04.set.shore_night__p08", " Leafless Night-Shore Tree", "P3", 1.38, 1.48, 0.89, 0.36, "boulevard_tree", None),
    ],
    "04.1": [
        X("04.hero.viaduct__p02", "Stone Viaduct Pier & Half-Arch (+4m Line)", "P4", 2.44, 1.16, 0.90, 0.48, "gable_portal_cap", "Viaduct Pier (+4m Line)"),
        X("04.hero.viaduct__p04", "Wide Stone Viaduct Archway", "P4", 2.40, 1.44, 0.90, 0.48, "gable_portal_cap", "Viaduct Canal Arch"),
        X("04.hero.viaduct__p07", "Iron Viaduct Bridge Railing", "P3", 1.44, 1.30, 0.56, 0.16, "span_deck", None),
        X("04.set.shore_night__p03", "Cresting Night-Canal Wave Strip", "P2", 1.08, 1.30, 0.93, 0.14, "ground_curb", None),
    ],
    "04.2": [
        X("04.set.incline_trail__p03", "Rising Stone & Earth Incline Ramp", "P4", 2.44, 1.26, 0.90, 0.34, "span_deck", "Incline Trail Ramp"),
        X("04.hero.viaduct__p03", "Stone Viaduct Arch Portal", "P4", 2.38, 1.46, 0.90, 0.46, "gable_portal_cap", "Viaduct Overpass"),
        X("04.set.shore_night__p09", "Twisted Shore Tree Silhouette", "P3", 1.40, 1.16, 0.88, 0.34, "boulevard_tree", None),
        X("04.set.incline_trail__p05", "Stepped Stone Trail Curb", "P2", 1.08, 1.30, 0.93, 0.16, "ground_curb", None),
    ],
    "04.3": [
        X("04.hero.viaduct__p01", "Extended Three-Arch Stone Viaduct", "P4", 2.44, 1.28, 0.89, 0.44, "span_deck", "Viaduct Archway Span"),
        X("04.hero.viaduct__p07", "Upper Viaduct Iron Balustrade", "P4", 2.38, 1.28, 0.55, 0.16, "span_deck", None),
        X("09.props.phonebooth__p01", "Illuminated Glass Telephone Booth", "P3", 1.38, 1.46, 0.89, 0.38, "gable_portal_cap", "Glass Phone Booth"),
        X("04.hero.viaduct__p09", "Stone Viaduct Roadway Coping", "P2", 1.08, 1.28, 0.93, 0.14, "ground_curb", None),
    ],
    "04.4": boulevard_tape_bridge(
        fence_id="04.set.night_garden_field__p01",
        fence_label="Night Garden Hedgerow",
        tree_ids=["04.set.shore_night__p08", "04.set.shore_night__p09", "12.hero.pools__p02", "12.hero.pools__p03"],
        tree_label="Moonlit Garden Tree",
        lamp_id="07.set.projection_three_roads__p13",
        lamp_label="Garden Path Lamp",
        curb_id="04.set.night_garden_field__p06",
        curb_label="Blooming Night-Garden Grass Strip",
        station_title="Moonlit Garden Boulevard",
        floor_y=0.89,
    ),
    "04.5": [
        X("04.set.night_garden_field__p01", "Distant Tree-Line Silhouette Strip", "P4", 2.46, 1.28, 0.88, 0.24, "boulevard_fence", "Starfield Ridge"),
        X("04.hero.viaduct__p03", "Stone Archway Under the Stars", "P4", 2.40, 1.44, 0.90, 0.46, "gable_portal_cap", "Starlight Arch"),
        X("04.props.heart__p01", "Carved Stone Heart Reliquary", "P3", 1.40, 1.18, 0.88, 0.26, "story_prop", None),
        X("04.set.night_garden_field__p07", "Wildflower & Reed Foreground Strip", "P2", 1.08, 1.30, 0.93, 0.18, "ground_curb", None),
    ],
    "04.6": boulevard_tape_bridge(
        fence_id="05.hero.perimeter__p04",
        fence_label="Perimeter Chain-Link Fence",
        tree_ids=["12.hero.pools__p02", "12.hero.pools__p03", "12.hero.pools__p11", "12.hero.pools__p12"],
        tree_label="Perimeter Tree",
        lamp_id="13.set.harbor_quay_night_fire__p02",
        lamp_label="Perimeter Street Lamp",
        curb_id="04.set.night_garden_field__p02",
        curb_label="Perimeter Hedge Curb",
        station_title="Perimeter Boulevard Toward Poem 05",
        floor_y=0.89,
    ),

    # =======================================================================
    # POEM 05 · BLOODLINES (Continuous Tape: Perimeter Boulevard [Uploaded Image 2!] -> Star Field -> Humid Basement -> Winged Marble Gate)
    # =======================================================================
    # Exact match to Director's Uploaded Image 2 (`media_1793295991132_6f4cd1fc.png`)!
    "05.0": boulevard_tape_bridge(
        fence_id="05.hero.perimeter__p04",
        fence_label="Perimeter Fence Mesh",
        tree_ids=["09.hero.canopy__p05", "12.hero.pools__p02", "09.hero.canopy__p06", "12.hero.pools__p03"],
        tree_label="Boulevard Palm & Canopy Tree",
        lamp_id="07.set.projection_three_roads__p13",
        lamp_label="Red-Halo Boulevard Lamp",
        curb_id="04.set.night_garden_field__p02",
        curb_label="Clipped Boulevard Hedge Strip",
        station_title="Perimeter Boulevard Tape",
        floor_y=0.89,
    ),
    "05.1": boulevard_tape_bridge(
        fence_id="05.hero.perimeter__p05",
        fence_label="Perimeter Fence Section",
        tree_ids=["12.hero.pools__p11", "09.hero.canopy__p04", "12.hero.pools__p12", "09.hero.canopy__p07"],
        tree_label="Star-Field Boulevard Tree",
        lamp_id="13.set.harbor_quay_night_fire__p02",
        lamp_label="Star-Field Street Lamp",
        curb_id="05.set.night_field_parade__p05",
        curb_label="Night Field Grass Verge",
        station_title="Star-Naming Boulevard",
        floor_y=0.89,
    ),
    "05.2": [
        X("05.set.humid_basement__p01", "Cinderblock Basement Wall with Window Hole", "P4", 2.44, 1.28, 0.90, 0.52, "wall_with_door_hole", "Humid Basement Window Wall"),
        X("05.set.humid_basement__p04", "Rough-Sawn Southern-Pine Ceiling Joist", "P4", 2.38, 1.28, 0.34, 0.16, "roof_cornice", "Southern-Pine Joist"),
        X("12.set.temple_backroom__p02", "Basement Stone Staircase Flight", "P3", 1.42, 1.48, 0.90, 0.38, "span_deck", "Stairs Up to the Gate"),
        X("05.props.staff-mattress-emblem__p03", "Basement Floor Mattress", "P3", 1.38, 1.18, 0.90, 0.24, "furniture_anchor", None),
    ],
    "05.3": [
        X("05.set.night_field_parade__p07", "Curved Globe Horizon Lawn", "P4", 2.46, 1.28, 0.90, 0.32, "span_deck", "Parade Field Extension"),
        X("05.set.winged_marble_gate__p03", "Monumental Winged Marble Gate Arch", "P4", 2.40, 1.38, 0.89, 0.52, "gable_portal_cap", "Winged Marble Gate"),
        X("05.set.winged_marble_gate__p01", "Carved Marble Left Wing", "P3", 1.44, 1.22, 0.84, 0.44, "gable_portal_cap", None),
        X("05.set.winged_marble_gate__p05", "Carved Marble Right Wing", "P3", 1.44, 1.52, 0.84, 0.44, "gable_portal_cap", None),
    ],
    "05.4": [
        X("05.set.winged_marble_gate__p03", "Marble Sanctuary Archway", "P4", 2.44, 1.22, 0.89, 0.50, "gable_portal_cap", "Sanctuary Threshold"),
        X("05.set.night_field_parade__p04", "Wildflower Hillock Left", "P3", 1.44, 1.12, 0.90, 0.32, "ground_curb", None),
        X("05.set.night_field_parade__p06", "Wildflower Hillock Right", "P3", 1.42, 1.46, 0.90, 0.32, "ground_curb", None),
        X("05.set.winged_marble_gate__p06", "Inscribed Marble Plinth Step", "P2", 1.08, 1.28, 0.93, 0.16, "ground_curb", None),
    ],
    "05.5": [
        X("06.set.atlantis_gate__p01", "Tall Atlantis Stone Portal Tower", "P4", 2.44, 1.44, 0.90, 0.52, "gable_portal_cap", "The Light Gate of Atlantis"),
        X("06.set.causeway_road__p03", "Golden-Brick Causeway Perspective Span", "P3", 1.46, 1.24, 0.92, 0.28, "span_deck", "Yellow-Brick Causeway"),
        X("05.hero.perimeter__p01", "Causeway Guardrail Beam", "P3", 1.40, 1.20, 0.84, 0.14, "span_deck", None),
        X("06.props.lantern-candle-guitar__p01", "Brass Hurricane Wayfinder Lantern", "P2", 1.08, 1.12, 0.89, 0.20, "story_prop", None),
    ],

    # =======================================================================
    # POEM 06 · RESURRECTING ATLANTIS (Continuous Tape: Light Gate -> Causeway -> Waterfront Skyline -> Crystal Hall -> Narrow Streets -> Harbor Teahouse)
    # =======================================================================
    "06.0": [
        X("06.set.atlantis_waterfront.skyline__p01", "Domed Atlantis Citadel on the Bay", "P5", 3.82, 1.22, 0.78, 0.36, "vista_backing", None),
        X("06.set.atlantis_waterfront.skyline__p06", "Twin-Spired Atlantis Palace", "P5", 3.78, 1.46, 0.78, 0.34, "vista_backing", None),
        X("06.set.atlantis_gate__p02", "Stepped Stone Gate Causeway Embankment", "P4", 2.42, 1.28, 0.91, 0.38, "span_deck", "Light Gate Embankment"),
        X("06.set.atlantis_waterfront__p04", "Carved Stone Waterfront Staircase", "P3", 1.42, 1.44, 0.90, 0.26, "span_deck", "Waterfront Landing Stairs"),
    ],
    "06.1": [
        X("06.set.causeway_road__p03", "Yellow-Brick Causeway Deck", "P3", 1.46, 1.24, 0.92, 0.30, "span_deck", "Yellow-Brick Causeway Extension"),
        X("06.set.atlantis_plaza__p01", "Arched Venetian-Atlantis Arcade Wall", "P4", 2.42, 1.42, 0.89, 0.46, "wall_with_door_hole", "Waterfront Colonnade"),
        X("06.set.atlantis_waterfront__p06", "Hanging Ivy Seawall Garland", "P3", 1.38, 1.18, 0.74, 0.24, "boulevard_fence", None),
        X("06.props.lantern-candle-guitar__p01", "Brass Causeway Lantern", "P2", 1.08, 1.12, 0.89, 0.20, "story_prop", None),
    ],
    "06.2": [
        X("06.set.atlantis_waterfront.skyline__p12", "Terraced Atlantis Hillside Citadel", "P5", 3.80, 1.28, 0.76, 0.34, "vista_backing", None),
        X("06.set.atlantis_waterfront__p04", "Waterfront Balustrade & Quay Steps West", "P4", 2.42, 1.16, 0.90, 0.26, "span_deck", "Waterfront Quay Steps"),
        X("06.set.atlantis_waterfront__p05", "Waterfront Balustrade & Quay Steps East", "P4", 2.40, 1.44, 0.90, 0.26, "span_deck", None),
        X("06.set.atlantis_plaza__p02", "Three-Arch Atlantis Palace Facade", "P3", 1.40, 1.34, 0.88, 0.44, "gable_portal_cap", "Palace Arcade"),
    ],
    "06.3": [
        X("06.set.crystal_tree_hall__p13", "Twin-Arched Crystal Colonnade Portal", "P4", 2.44, 1.28, 0.89, 0.44, "gable_portal_cap", "Crystal Tree Colonnade"),
        X("06.set.crystal_tree_hall__p01", "Luminous Golden-Root Crystal Tree West", "P3", 1.44, 1.12, 0.89, 0.38, "boulevard_tree", None),
        X("06.set.crystal_tree_hall__p02", "Luminous Golden-Root Crystal Tree East", "P3", 1.42, 1.46, 0.89, 0.36, "boulevard_tree", None),
        X("06.set.crystal_tree_hall__p07", "Faceted Blue Crystal Canopy Cluster", "P4", 2.36, 1.28, 0.44, 0.26, "roof_cornice", None),
    ],
    "06.4": [
        X("06.set.atlantis_plaza__p01", "Terracotta Arched Plaza Wing West", "P4", 2.44, 1.16, 0.89, 0.46, "wall_with_door_hole", "West Plaza Arcade"),
        X("06.set.atlantis_plaza__p03", "Terracotta Arched Plaza Wing East", "P4", 2.42, 1.44, 0.89, 0.46, "wall_with_door_hole", "East Plaza Arcade"),
        X("06.hero.forum__p02", "Circular Stone Forum Amphitheater Ring", "P3", 1.44, 1.30, 0.92, 0.28, "span_deck", None),
        X("06.set.narrow_streets__p06", "Carved Stone Street Archway", "P3", 1.36, 1.30, 0.89, 0.36, "gable_portal_cap", "Into the Narrow Streets"),
    ],
    "06.5": [
        X("06.set.narrow_streets__p01", "Tall Narrow-Street Tenement Facade Left", "P4", 2.46, 1.12, 0.90, 0.56, "wall_bay", "Narrow Cobble Alley"),
        X("06.set.narrow_streets__p03", "Tall Narrow-Street Tenement Facade Right", "P4", 2.44, 1.48, 0.90, 0.56, "wall_bay", None),
        X("06.set.narrow_streets__p06", "Masonry Alleyway Arch Portal", "P3", 1.42, 1.30, 0.89, 0.38, "gable_portal_cap", "Alleyway Portal"),
        X("06.set.narrow_streets__p10", "Perspective Cobblestone Street Deck", "P3", 1.48, 1.30, 0.93, 0.24, "span_deck", None),
        X("06.set.narrow_streets__p04", "Overhead String of Warm Alley Bulbs", "P2", 1.08, 1.30, 0.42, 0.16, "ceiling_fixture", None),
    ],
    "06.6": [
        X("06.hero.teahouse__p01", "Weathered Teal Teahouse Wall with Window Holes", "P4", 2.44, 1.24, 0.90, 0.46, "wall_with_door_hole", "Harbor Teahouse Veranda"),
        X("06.hero.teahouse__p02", "Corrugated Teahouse Overhang Roof", "P4", 2.40, 1.24, 0.56, 0.26, "roof_cornice", None),
        X("06.hero.house__p01", "Red Waterfront Boathouse Wing", "P4", 2.38, 1.48, 0.90, 0.36, "wall_with_door_hole", "Boathouse Wing"),
        X("06.hero.teahouse__p07", "Flagstone Harbor Quay Walk", "P3", 1.46, 1.30, 0.93, 0.18, "span_deck", None),
    ],

    # =======================================================================
    # POEM 07 · DJ TURN ME UP (Continuous Tape: Club Container House -> DJ Decks -> Crowd -> Three-Roads Boulevard)
    # =======================================================================
    "07.0": [
        X("07.hero.house__p01", "Teal Industrial Club Wall with Window Holes", "P4", 2.44, 1.22, 0.90, 0.42, "wall_with_door_hole", "Industrial Club Wing"),
        X("07.hero.house__p03", "Open-Sided Club Stage Room Box", "P4", 2.40, 1.46, 0.90, 0.44, "wall_with_door_hole", "DJ Stage Box"),
        X("07.props.dj-decks__p01", "Illuminated Club DJ Console", "P3", 1.42, 1.24, 0.90, 0.28, "furniture_anchor", None),
        X("07.props.speakers-vu__p01", "Tall Bass Speaker Stack", "P3", 1.38, 1.48, 0.90, 0.32, "furniture_anchor", None),
    ],
    "07.1": [
        X("07.hero.house__p04", "Corrugated Club Gallery Wall", "P4", 2.44, 1.24, 0.90, 0.42, "wall_with_door_hole", "Club Gallery Extension"),
        X("07.hero.house__p09", "Industrial Steel Club Staircase", "P3", 1.44, 1.46, 0.90, 0.32, "span_deck", "Mezzanine Stairs"),
        X("07.hero.house.furniture__p17", "U-Shaped Neon VIP Lounge Booth", "P3", 1.40, 1.22, 0.90, 0.24, "furniture_anchor", None),
        X("07.hero.house.furniture__p15", "Magenta Neon Bar Counter", "P3", 1.36, 1.44, 0.90, 0.20, "furniture_anchor", None),
    ],
    "07.2": [
        X("07.hero.shaft__p16", "Red-Lit Industrial Corridor Bay", "P4", 2.44, 1.24, 0.90, 0.44, "wall_with_door_hole", "Red Bass Corridor"),
        X("07.hero.shaft__p01", "Octagonal Red Steel Bulkhead Portal", "P3", 1.42, 1.46, 0.89, 0.44, "gable_portal_cap", "Bulkhead Portal"),
        X("07.props.speakers-vu__p02", "Subwoofer Tower East", "P3", 1.38, 1.12, 0.90, 0.32, "furniture_anchor", None),
        X("07.hero.house.furniture__p14", "Cyan Neon Floor Strip", "P2", 1.08, 1.30, 0.93, 0.12, "ground_curb", None),
    ],
    "07.3": [
        X("08.hero.marquee__p01", "Brick Club Facade with Three Portal Holes", "P4", 2.44, 1.28, 0.90, 0.48, "wall_with_door_hole", "Club Plaza Portals"),
        X("07.props.bar-handheld__p01", "Illuminated Club Bar Counter", "P3", 1.42, 1.22, 0.90, 0.28, "furniture_anchor", None),
        X("07.hero.shaft__p15", "Deep Red Elevator Shaft Aperture", "P4", 2.38, 1.48, 0.89, 0.38, "wall_with_door_hole", "Elevator Shaft Portal"),
        X("07.hero.house.furniture__p18", "Steel Grate Dancefloor Deck", "P3", 1.48, 1.28, 0.93, 0.20, "span_deck", None),
    ],
    "07.4": [
        X("07.set.projection_vineyard__p05", "Distant Vineyard Trellis Row", "P4", 2.46, 1.28, 0.86, 0.20, "boulevard_fence", "Vineyard Horizon"),
        X("07.set.projection_three_roads__p01", "Perspective Two-Lane Highway Deck", "P3", 1.46, 1.26, 0.92, 0.28, "span_deck", "Three Roads Highway"),
        X("07.set.projection_three_roads__p13", "Curved Highway Street Lamp West", "P3", 1.40, 1.14, 0.89, 0.36, "boulevard_lamp", None),
        X("07.set.projection_three_roads__p14", "Curved Highway Street Lamp East", "P3", 1.40, 1.44, 0.89, 0.36, "boulevard_lamp", None),
    ],
    "07.5": [
        X("07.hero.house__p05", "Rusted Corrugated After-Hours Club Wall", "P4", 2.44, 1.22, 0.90, 0.42, "wall_bay", "After-Hours Alley Wall"),
        X("08.hero.marquee__p16", "Illuminated 'NEW SINGLE' Theater Entrance", "P4", 2.40, 1.46, 0.90, 0.44, "gable_portal_cap", "NEW SINGLE Marquee"),
        X("07.set.projection_three_roads__p13", "Alleyway Sodium Street Lamp", "P3", 1.42, 1.10, 0.89, 0.36, "boulevard_lamp", None),
        X("07.hero.house.furniture__p05", "Wet Alleyway Curb Slab", "P2", 1.08, 1.30, 0.93, 0.16, "ground_curb", None),
    ],
    "07.6": boulevard_tape_bridge(
        fence_id="08.set.rooftop_club__p09",
        fence_label="Flooded Canal Guardrail",
        tree_ids=["09.hero.canopy__p04", "09.hero.canopy__p05", "09.hero.canopy__p06", "09.hero.canopy__p07"],
        tree_label="Rain-Soaked Canal Palm",
        lamp_id="07.set.projection_three_roads__p13",
        lamp_label="Rain-Halo Street Lamp",
        curb_id="08.set.rooftop_club__p10",
        curb_label="Wet Stone Canal Promenade",
        station_title="Three Roads Canal Boulevard",
        floor_y=0.89,
    ),

    # =======================================================================
    # POEM 08 · NEWLY SINGLE (Continuous Tape: Rooftop Club -> NEW SINGLE Marquee -> Red Velvet Theater -> Equator Plain -> Mountain Ridge)
    # =======================================================================
    "08.0": [
        X("08.set.rooftop_club__p02", "Rooftop Tesla-Coil Skyline Stage", "P4", 2.44, 1.24, 0.88, 0.42, "wall_with_door_hole", "Rooftop Tesla Stage"),
        X("08.set.rooftop_club__p04", "Lattice Broadcast Tower East", "P4", 2.40, 1.48, 0.89, 0.46, "boulevard_lamp", None),
        X("08.set.rooftop_club__p09", "Rooftop Terrace Guardrail", "P3", 1.44, 1.26, 0.90, 0.18, "span_deck", None),
        X("08.set.rooftop_club__p10", "Rooftop Terrace Deck Slab", "P3", 1.48, 1.28, 0.93, 0.18, "span_deck", None),
    ],
    "08.1": [
        X("08.hero.marquee__p01", "Brick Theater Facade with Three Portal Holes", "P4", 2.44, 1.26, 0.90, 0.48, "wall_with_door_hole", "NEW SINGLE Marquee Portals"),
        X("08.hero.marquee__p02", "Retro 'NEW SINGLE' Marquee Signboard", "P4", 2.38, 1.26, 0.46, 0.22, "roof_cornice", None),
        X("08.hero.marquee.interior__p02", "Theater Lobby Wall with Twin Door Holes", "P4", 2.40, 1.48, 0.90, 0.42, "wall_with_door_hole", "Theater Lobby Doors"),
        X("08.hero.marquee__p14", "Rain-Slicked Sidewalk Reflections", "P3", 1.48, 1.30, 0.93, 0.16, "span_deck", None),
    ],
    "08.2": [
        X("08.hero.marquee.interior__p09", "Crimson Theater Wall with Open Doorway Hole", "P4", 2.44, 1.20, 0.90, 0.46, "wall_with_door_hole", "Crimson Auditorium Door"),
        X("08.hero.marquee.interior__p15", "Raked Red-Velvet Cinema Seating Bank", "P3", 1.44, 1.44, 0.90, 0.36, "furniture_anchor", "Empty Cinema Auditorium"),
        X("08.set.atlantis_aerial__p03", "Drifting Moonlit Cumulus Cloud Bank", "P5", 3.80, 1.32, 0.48, 0.26, "vista_backing", None),
        X("08.hero.marquee.interior__p12", "Red Carpeted Theater Aisle Runner", "P2", 1.08, 1.28, 0.93, 0.16, "ground_curb", None),
    ],
    "08.3": [
        X("08.props.basins__p01", "Carved Stone Ice-Water Basin West", "P3", 1.44, 1.18, 0.90, 0.28, "furniture_anchor", "Salted Ice-Water Basin"),
        X("08.props.basins__p02", "Carved Stone Ice-Water Basin East", "P3", 1.42, 1.44, 0.90, 0.28, "furniture_anchor", None),
        X("12.set.temple_grove__p07", "Overhanging Willow & Cypress Canopy Strip", "P4", 2.40, 1.30, 0.44, 0.28, "roof_cornice", None),
        X("11.hero.pools__p01", "Turquoise Reflecting Pool Channel", "P3", 1.48, 1.30, 0.93, 0.18, "span_deck", None),
    ],
    "08.4": boulevard_tape_bridge(
        fence_id="09.set.atlantis_harbor_street__p05",
        fence_label="Harbor Warehouse Facade Row",
        tree_ids=["09.hero.canopy__p04", "09.hero.canopy__p05", "09.hero.canopy__p06", "09.hero.canopy__p07"],
        tree_label="Harbor Mist Palm",
        lamp_id="13.set.harbor_quay_night_fire__p02",
        lamp_label="Harbor Quay Lamp",
        curb_id="09.set.harbor_path_east__p07",
        curb_label="Cobblestone Harbor Quay Walk",
        station_title="Harbor Mist Promenade",
        floor_y=0.89,
    ),
    "08.5": [
        X("08.set.rooftop_club__p07", "Distant Atlantis Spire Horizon Strip", "P5", 3.80, 1.30, 0.78, 0.22, "vista_backing", None),
        X("09.hero.canopy__p08", "Illuminated Harbor Pergola Colonnade", "P4", 2.42, 1.26, 0.89, 0.38, "gable_portal_cap", "Harbor Pergola Colonnade"),
        X("09.set.atlantis_club_sidewalk__p04", "Neon Club Entrance Portal", "P3", 1.40, 1.48, 0.90, 0.44, "wall_with_door_hole", "Into Poem 09 · Yet, Heard"),
        X("09.set.harbor_path_east__p07", "Flagstone Harbor Promenade", "P2", 1.08, 1.30, 0.93, 0.18, "ground_curb", None),
    ],

    # =======================================================================
    # POEM 09 · YET, HEARD (Continuous Tape: Club Sidewalk Portals -> Harbor Quay -> Escalator/Mother's Room -> Inner Harbor)
    # =======================================================================
    "09.0": [
        X("09.set.atlantis_club_sidewalk__p05", "Crimson Neon Club Doorway Wall", "P4", 2.44, 1.20, 0.90, 0.44, "wall_with_door_hole", "Crimson Club Portal"),
        X("09.set.atlantis_club_sidewalk__p06", "Cyan-Lit Sidewalk Storefront Portal", "P4", 2.40, 1.46, 0.90, 0.44, "wall_with_door_hole", "Sidewalk Storefront"),
        X("09.hero.canopy__p02", "Palm & Neon Canopy Boulevard Row", "P4", 2.36, 1.32, 0.56, 0.28, "roof_cornice", None),
        X("09.set.atlantis_club_sidewalk__p13", "Wet Neon-Reflected Sidewalk Slab", "P3", 1.48, 1.30, 0.93, 0.18, "span_deck", None),
    ],
    "09.1": boulevard_tape_bridge(
        fence_id="09.set.atlantis_harbor_street__p06",
        fence_label="Harborfront Building Row",
        tree_ids=["09.hero.canopy__p04", "09.hero.canopy__p05", "09.hero.canopy__p06", "09.hero.canopy__p07"],
        tree_label="Harbor Boulevard Palm",
        lamp_id="13.set.harbor_quay_night_fire__p02",
        lamp_label="Harbor Pier Lamp",
        curb_id="09.set.harbor_path_east__p07",
        curb_label="Harbor Pier Stone Walk",
        station_title="Harbor Pier Boulevard",
        floor_y=0.89,
    ),
    "09.2": [
        X("09.set.mother_living_room__p01", "Mother's Living Room Wall with Window Hole", "P4", 2.44, 1.24, 0.90, 0.48, "wall_with_door_hole", "Mother's Living Room Wall"),
        X("09.set.atlantis_club_sidewalk__p04", "Teal Lobby Portal Archway", "P4", 2.40, 1.48, 0.90, 0.44, "gable_portal_cap", "Lobby Threshold"),
        X("09.props.suitcases-notice__p04", "Stacked Vintage Travel Suitcases", "P3", 1.42, 1.14, 0.90, 0.26, "story_prop", None),
        X("09.set.mother_living_room__p15", "Patterned Living Room Rug", "P3", 1.46, 1.28, 0.93, 0.18, "span_deck", None),
    ],
    "09.3": [
        X("09.set.mother_living_room__p01", "Living Room Wall with Framed Window Hole", "P4", 2.44, 1.26, 0.90, 0.48, "wall_with_door_hole", "Mother's Window Wall"),
        X("09.set.mother_living_room__p02", "Mullioned Wooden Window Casement", "P3", 1.44, 1.26, 0.72, 0.30, "window_dressing", None),
        X("09.props.phonebooth__p02", "Standing Glass Telephone Booth", "P3", 1.40, 1.48, 0.90, 0.40, "gable_portal_cap", "The Call to Mother"),
        X("09.props.phones-chair__p07", "Upholstered Living Room Armchair", "P3", 1.38, 1.12, 0.90, 0.26, "furniture_anchor", None),
    ],
    "09.4": [
        X("09.set.atlantis_harbor_street__p05", "Waterfront gables & Harbor Warehouses", "P4", 2.44, 1.28, 0.88, 0.24, "wall_bay", "Inner Harbor Warehouses"),
        X("09.set.atlantis_harbor_street__p09", "Iron Harbor Quay Loading Crane", "P4", 2.40, 1.16, 0.88, 0.34, "boulevard_lamp", "Harbor Crane Quay"),
        X("09.hero.canopy__p09", "Illuminated Waterfront Pergola", "P3", 1.42, 1.44, 0.89, 0.38, "gable_portal_cap", None),
        X("09.set.harbor_path_east__p07", "Stone Quay Apron", "P2", 1.08, 1.30, 0.93, 0.18, "ground_curb", None),
    ],
    "09.5": [
        X("10.set.atlantis_streets__p04", "Neon Atlantis Street Facade Block", "P4", 2.44, 1.22, 0.89, 0.38, "wall_bay", "Neon Street Facade"),
        X("10.hero.shadowpool__p01", "Mosaic Shadowpool Archway Portal", "P3", 1.42, 1.46, 0.90, 0.48, "gable_portal_cap", "Shadowpool Archway"),
        X("09.props.phonebooth__p01", "Harbor Quay Telephone Booth", "P3", 1.38, 1.10, 0.90, 0.38, "gable_portal_cap", None),
        X("09.set.harbor_path_east__p07", "Harbor Quay Stone Walk", "P2", 1.08, 1.30, 0.93, 0.18, "ground_curb", None),
    ],

    # =======================================================================
    # POEM 10 · MAGIC RIDE (Continuous Tape: Shadowpool Archways -> Neon Streets -> Mountain Road & Cafe Racer -> Dawn Tree)
    # =======================================================================
    "10.0": [
        X("10.hero.shadowpool__p01", "Outer Mosaic Shadowpool Archway", "P4", 2.44, 1.22, 0.90, 0.48, "gable_portal_cap", "Shadowpool Outer Arch"),
        X("10.hero.shadowpool__p02", "Inner Mosaic Shadowpool Archway", "P4", 2.40, 1.46, 0.90, 0.44, "gable_portal_cap", "Shadowpool Inner Arch"),
        X("10.hero.shadowpool__p05", "Rippling Golden-Lit Pool Reflection Strip", "P3", 1.46, 1.30, 0.93, 0.20, "span_deck", None),
        X("10.set.atlantis_streets__p07", "Brass & Brick Steam Clocktower", "P4", 2.36, 1.34, 0.88, 0.38, "boulevard_lamp", None),
    ],
    "10.1": [
        X("10.set.atlantis_streets__p05", "Illuminated Atlantis Avenue Building Block", "P4", 2.44, 1.24, 0.89, 0.36, "wall_bay", "Atlantis Avenue Block"),
        X("10.set.atlantis_streets__p08", "Stepped Neon Spire Tower", "P4", 2.40, 1.46, 0.89, 0.40, "wall_bay", None),
        X("04.hero.viaduct__p07", "Steel Overpass Guardrail Span", "P3", 1.44, 1.28, 0.90, 0.16, "span_deck", "Overpass Guardrail"),
        X("11.props.parked-motorcycle__p01", "Parked Cafe-Racer Motorcycle at Overpass", "P2", 1.08, 1.24, 0.90, 0.26, "story_prop", None),
    ],
    "10.2": [
        X("10.set.mountain_road__p04", "Distant Mountain Ridge Horizon Strip", "P5", 3.80, 1.30, 0.78, 0.22, "vista_backing", None),
        X("10.set.mountain_road__p09", "Weathered Canyon Rock Pillar West", "P4", 2.42, 1.16, 0.90, 0.44, "wall_bay", "Canyon Rock Pillar"),
        X("10.set.mountain_road__p10", "Weathered Canyon Rock Pillar East", "P4", 2.40, 1.46, 0.90, 0.44, "wall_bay", None),
        X("10.set.mountain_road__p06", "Asphalt Mountain Highway Deck", "P3", 1.46, 1.30, 0.93, 0.28, "span_deck", "Mountain Highway Tape"),
    ],
    "10.3": [
        X("06.set.narrow_streets__p06", "Sunlit Stone Avenue Archway", "P4", 2.44, 1.22, 0.90, 0.42, "gable_portal_cap", "Solar Avenue Archway"),
        X("10.set.atlantis_streets__p06", "Golden-Lit Avenue Facade", "P4", 2.40, 1.46, 0.89, 0.38, "wall_bay", None),
        X("10.props.bike-skeleton__p01", "Cafe-Racer Motorcycle in Full Stride", "P3", 1.40, 1.24, 0.90, 0.26, "story_prop", None),
        X("10.set.atlantis_streets__p11", "Glowing Solar Highway Lane Strip", "P3", 1.48, 1.30, 0.93, 0.14, "span_deck", None),
    ],
    "10.4": boulevard_tape_bridge(
        fence_id="04.hero.viaduct__p07",
        fence_label="Causeway Viaduct Railing",
        tree_ids=["10.props.tree-dawn-sign__p01", "12.hero.pools__p02", "12.hero.pools__p03", "10.props.tree-dawn-sign__p01"],
        tree_label="Dawn Causeway Tree",
        lamp_id="07.set.projection_three_roads__p13",
        lamp_label="Causeway Lamp",
        curb_id="04.hero.viaduct__p09",
        curb_label="Stone Viaduct Curb",
        station_title="Out of Atlantis Viaduct Tape",
        floor_y=0.89,
    ),
    "10.5": [
        X("10.set.mountain_road__p05", "Mountain Ridge Horizon", "P5", 3.80, 1.30, 0.78, 0.22, "vista_backing", None),
        X("10.props.tree-dawn-sign__p01", "Great Spreading Dawn Tree", "P4", 2.42, 1.18, 0.90, 0.48, "boulevard_tree", "The Dawn Tree"),
        X("11.props.temple.states__p02", "First Marble Temple Stylobate Plinth", "P3", 1.42, 1.46, 0.90, 0.26, "span_deck", "Temple Site · Poem 11"),
        X("11.hero.steps__p09", "Broad Stone Temple Approach Steps", "P2", 1.08, 1.30, 0.93, 0.18, "ground_curb", None),
    ],

    # =======================================================================
    # POEM 11 · NEW DAY (Continuous Tape: Progressive Lego Temple Construction — Steps -> Plinth -> Columns -> Beams -> Roof -> Mirror Hall)
    # =======================================================================
    "11.0": [
        X("11.props.ruin__p01", "Ancient Ruined Stone Wall Course", "P4", 2.44, 1.18, 0.90, 0.36, "wall_bay", "Ruined Stone Wall"),
        X("11.props.ruin__p02", "Ancient Ruined Stone Archway Portal", "P4", 2.40, 1.44, 0.90, 0.42, "gable_portal_cap", "Ruined Sanctuary Arch"),
        X("11.props.temple.arrival.courses-columns__p01", "Marble Stylobate Foundation Course #1", "P3", 1.44, 1.28, 0.91, 0.16, "span_deck", None),
        X("11.hero.steps__p01", "Weathered Stone Approach Step", "P2", 1.08, 1.28, 0.93, 0.14, "ground_curb", None),
    ],
    "11.1": [
        X("11.props.temple.states__p01", "Half-Erected Marble Temple Colonnade", "P4", 2.42, 1.22, 0.90, 0.44, "gable_portal_cap", "Rising Marble Colonnade"),
        X("11.props.temple.whole__p04", "Fluted Marble Column Shaft #1", "P4", 2.38, 1.42, 0.89, 0.38, "wall_bay", None),
        X("11.props.temple.whole__p05", "Fluted Marble Column Shaft #2", "P4", 2.38, 1.52, 0.89, 0.38, "wall_bay", None),
        X("11.props.temple.arrival.beams__p01", "Carved Marble Architrave Beam", "P4", 2.34, 1.46, 0.56, 0.16, "roof_cornice", None),
        X("11.hero.pools__p01", "Turquoise Reflecting Pool Extension", "P3", 1.48, 1.30, 0.93, 0.18, "span_deck", None),
    ],
    "11.2": [
        X("11.set.mirror_hall__p02", "Five-Arch Marble Mirror-Hall Arcade", "P4", 2.44, 1.28, 0.88, 0.32, "wall_with_door_hole", "Mirror-Hall Arcade"),
        X("11.set.mirror_hall__p01", "Vaulted Marble Arch Span", "P4", 2.40, 1.28, 0.52, 0.28, "roof_cornice", None),
        X("11.set.mirror_hall__p04", "Fluted Mirror-Hall Pier West", "P3", 1.44, 1.10, 0.90, 0.38, "wall_bay", None),
        X("11.set.mirror_hall__p05", "Fluted Mirror-Hall Pier East", "P3", 1.44, 1.48, 0.90, 0.38, "wall_bay", None),
    ],
    "11.3": [
        X("11.props.temple.states__p04", "Completed Marble Temple Sanctuary & Pediment", "P4", 2.42, 1.24, 0.90, 0.48, "gable_portal_cap", "Completed Marble Temple"),
        X("11.hero.clocktower__p01", "Tall Brick & Stone Clocktower Spire", "P4", 2.38, 1.48, 0.90, 0.54, "boulevard_lamp", "The New Day Clocktower"),
        X("11.props.temple.arrival.courses-columns__p02", "Polished Marble Stylobate Course", "P3", 1.46, 1.28, 0.92, 0.16, "span_deck", None),
        X("11.props.inlays-lantern__p04", "Tall Brass Sanctuary Lantern", "P2", 1.08, 1.08, 0.90, 0.24, "story_prop", None),
    ],
    "11.4": [
        X("11.set.temple_infinity_pool__p04", "Classical Stone Aqueduct Arcade", "P4", 2.44, 1.28, 0.88, 0.28, "wall_with_door_hole", "Infinity Pool Arcade"),
        X("12.hero.pools__p04", "Marble Pool Column West", "P3", 1.44, 1.12, 0.90, 0.38, "wall_bay", None),
        X("12.hero.pools__p05", "Marble Pool Column East", "P3", 1.44, 1.46, 0.90, 0.38, "wall_bay", None),
        X("11.hero.pools__p02", "Calm Reflecting Water Channel", "P3", 1.48, 1.30, 0.93, 0.18, "span_deck", None),
    ],
    "11.5": [
        X("11.props.temple.whole__p20", "Crowned Marble Temple Pediment", "P4", 2.42, 1.24, 0.90, 0.46, "gable_portal_cap", "Sunlit Temple Portico"),
        X("12.set.temple_hall__p02", "Broad Marble Sanctuary Arch", "P4", 2.38, 1.48, 0.56, 0.26, "roof_cornice", None),
        X("12.set.temple_hall__p04", "Sanctuary Marble Pillar", "P3", 1.42, 1.48, 0.90, 0.38, "wall_bay", "Into Poem 12 · Reunion"),
        X("11.hero.steps__p10", "Sunlit Stone Stylobate Step", "P2", 1.08, 1.30, 0.93, 0.14, "ground_curb", None),
    ],

    # =======================================================================
    # POEM 12 · REUNION (Continuous Tape: Temple Hall -> Temple Backroom Wall -> Mediterranean Grove Boulevard -> Shore Terrace Stairs)
    # =======================================================================
    "12.0": [
        X("12.set.temple_hall__p03", "Long Classical Colonnade Arcade", "P4", 2.44, 1.28, 0.88, 0.28, "wall_with_door_hole", "Temple Hall Colonnade"),
        X("12.set.temple_backroom__p01", "Temple Backroom Wall with Open Doorway Hole", "P4", 2.40, 1.34, 0.90, 0.52, "wall_with_door_hole", "Backroom Doorway Threshold"),
        X("12.set.temple_backroom__p02", "Stone Staircase Inside the Threshold", "P3", 1.42, 1.50, 0.90, 0.36, "span_deck", None),
        X("12.set.temple_backroom__p08", "Timber Floorboard Runner", "P3", 1.48, 1.28, 0.93, 0.18, "span_deck", None),
    ],
    "12.1": boulevard_tape_bridge(
        fence_id="12.hero.pools__p01",
        fence_label="Carved Marble Pool Balustrade",
        tree_ids=["12.hero.pools__p02", "12.hero.pools__p03", "12.hero.pools__p11", "12.hero.pools__p12"],
        tree_label="Temple Grove Olive Tree",
        lamp_id="12.hero.pools__p04",
        lamp_label="Fluted Marble Grove Column",
        curb_id="12.set.temple_grove__p09",
        curb_label="Mossy Grove Ground Strip",
        station_title="Temple Grove Colonnade Tape",
        floor_y=0.89,
    ),
    "12.2": [
        X("12.set.temple_backroom__p01", "Afterlife Chamber Wall with Open Doorway Hole", "P4", 2.44, 1.26, 0.90, 0.52, "wall_with_door_hole", "Afterlife Chamber Doorway"),
        X("12.set.temple_hall__p02", "Marble Vaulted Arch Over the Threshold", "P4", 2.38, 1.44, 0.54, 0.28, "gable_portal_cap", None),
        X("12.set.temple_backroom__p04", "Empty Wooden Folding Chair West", "P3", 1.42, 1.14, 0.90, 0.28, "furniture_anchor", None),
        X("12.set.temple_backroom__p05", "Empty Wooden Folding Chair East", "P3", 1.40, 1.38, 0.90, 0.28, "furniture_anchor", None),
    ],
    "12.3": [
        X("12.set.temple_hall__p03", "Illuminated Sanctuary Arcade", "P4", 2.44, 1.28, 0.88, 0.28, "wall_with_door_hole", "Hourglass Sanctuary Arcade"),
        X("12.hero.pools__p06", "Sanctuary Column West", "P3", 1.44, 1.12, 0.90, 0.38, "wall_bay", None),
        X("12.hero.pools__p07", "Sanctuary Column East", "P3", 1.44, 1.48, 0.90, 0.38, "wall_bay", None),
        X("12.props.last-hourglass__p01", "Monumental Wooden Hourglass", "P2", 1.08, 1.30, 0.90, 0.28, "story_prop", "The Last Hourglass"),
    ],
    "12.4": [
        X("12.set.temple_grove__p07", "Interlocking Olive & Cypress Canopy Arch", "P4", 2.42, 1.28, 0.48, 0.30, "roof_cornice", "Western Forest Canopy"),
        X("12.set.temple_grove__p03", "Gnarled Olive Tree Trunk #1", "P3", 1.44, 1.12, 0.90, 0.38, "boulevard_tree", None),
        X("12.set.temple_grove__p04", "Gnarled Olive Tree Trunk #2", "P3", 1.42, 1.30, 0.90, 0.38, "boulevard_tree", None),
        X("12.set.temple_grove__p05", "Gnarled Olive Tree Trunk #3", "P3", 1.44, 1.48, 0.90, 0.38, "boulevard_tree", None),
        X("12.set.temple_grove__p09", "Forest Moss & Fern Floor Strip", "P2", 1.08, 1.30, 0.93, 0.16, "ground_curb", None),
    ],
    "12.5": [
        X("12.set.temple_shore_terrace__p05", "Broad Stone Shore-Terrace Staircase", "P3", 1.44, 1.24, 0.91, 0.32, "span_deck", "Shore Terrace Stairs"),
        X("12.hero.pools__p01", "Terrace Stone Balustrade", "P4", 2.40, 1.44, 0.89, 0.18, "boulevard_fence", None),
        X("12.hero.pools__p02", "Terrace Cypress Tree", "P4", 2.36, 1.48, 0.89, 0.36, "boulevard_tree", None),
        X("12.set.temple_shore_terrace__p06", "Wet Flagstone Shore Landing", "P2", 1.08, 1.30, 0.93, 0.18, "ground_curb", None),
    ],
    "12.6": [
        X("13.hero.cafe__p01", "Corner Cafe Storefront with Door & Window Holes", "P4", 2.42, 1.26, 0.90, 0.48, "wall_with_door_hole", "The Corner Cafe · Poem 13"),
        X("13.hero.cafe__p02", "Shingled Cafe Awning Roof", "P4", 2.38, 1.26, 0.54, 0.22, "roof_cornice", None),
        X("13.props.distant-window__p01", "Brick Gabled House with Central Window Hole", "P4", 2.40, 1.50, 0.90, 0.46, "gable_portal_cap", "Brick Gable House"),
        X("13.set.harbor_quay_night_fire__p03", "Harbor Quay Stone Promenade", "P3", 1.48, 1.30, 0.93, 0.18, "span_deck", None),
    ],

    # =======================================================================
    # POEM 13 · HOW TO WIN MY HEART (Continuous Tape: Corner Cafe -> Harbor Promenade -> Steel Catwalk -> Drowned Atrium -> Poppy Field -> Harbor Quay)
    # =======================================================================
    "13.0": [
        X("13.hero.cafe__p01", "Teal Timber Cafe Facade with Door & Window Holes", "P4", 2.44, 1.24, 0.90, 0.48, "wall_with_door_hole", "Corner Cafe Entrance"),
        X("13.hero.cafe__p02", "Slate Cafe Eaves Roof", "P4", 2.40, 1.24, 0.54, 0.22, "roof_cornice", None),
        X("13.props.cafe__p06", "Arched Wrought-Iron Cafe Sign Bracket", "P3", 1.44, 1.24, 0.48, 0.20, "roof_cornice", None),
        X("13.props.distant-window__p01", "Neighboring Brick Gable House with Window Hole", "P4", 2.38, 1.48, 0.90, 0.46, "gable_portal_cap", "Distant Window Gable"),
        X("13.props.cafe__p01", "Round Bistro Table on the Sidewalk", "P2", 1.08, 1.12, 0.91, 0.22, "furniture_anchor", None),
    ],
    "13.1": [
        X("13.set.harbor_cafe__p10", "Harbor Cafe Window Wall", "P4", 2.44, 1.20, 0.90, 0.44, "wall_with_door_hole", "Harbor Cafe Terrace"),
        X("13.hero.catwalk__p01", "Long Riveted Steel Harbor Catwalk Span", "P3", 1.44, 1.38, 0.89, 0.18, "span_deck", "Harbor Steel Catwalk"),
        X("13.set.harbor_quay_night_fire__p02", "Cast-Iron Harbor Quay Lamp West", "P3", 1.40, 1.12, 0.90, 0.36, "boulevard_lamp", None),
        X("13.set.harbor_quay_night_fire__p04", "Cast-Iron Harbor Quay Lamp East", "P3", 1.40, 1.48, 0.90, 0.36, "boulevard_lamp", None),
    ],
    "13.2": [
        X("13.hero.sleepdam__p01", "Monumental Concrete Sleepdam Wall & Spillway", "P4", 2.44, 1.28, 0.90, 0.34, "wall_bay", "Sleepdam Spillway Wall"),
        X("13.hero.catwalk__p01", "Upper Dam Steel Walkway Bridge", "P3", 1.44, 1.28, 0.64, 0.16, "span_deck", None),
        X("13.props.distant-window__p09", "Brick Gabled Cottage with Lit Window", "P4", 2.38, 1.48, 0.90, 0.36, "gable_portal_cap", "Cottage Above the Dam"),
        X("13.hero.sleepdam__p02", "Turbulent Dam Tailrace Water Strip", "P2", 1.08, 1.28, 0.93, 0.18, "ground_curb", None),
    ],
    "13.3": [
        X("13.set.drowned_atrium__p01", "Drowned Atrium Mullioned Window Wall", "P4", 2.44, 1.24, 0.90, 0.44, "wall_with_door_hole", "Drowned Atrium Window Wall"),
        X("13.set.drowned_atrium__p02", "Weathered Concrete Atrium Panel", "P4", 2.40, 1.48, 0.90, 0.42, "wall_bay", None),
        X("13.set.drowned_atrium__p05", "Stone Planter Box with Ferns West", "P3", 1.42, 1.16, 0.90, 0.24, "ground_curb", None),
        X("13.set.drowned_atrium__p06", "Stone Planter Box with Ferns East", "P3", 1.42, 1.44, 0.90, 0.24, "ground_curb", None),
    ],
    "13.4": [
        X("13.set.church_pews__p02", "Gothic Stone Double-Lancet Window Arch", "P4", 2.44, 1.22, 0.90, 0.48, "wall_with_door_hole", "Garden Chapel Arch"),
        X("13.set.drowned_atrium__p03", "Spreading Atrium Shade Tree", "P4", 2.38, 1.46, 0.89, 0.36, "boulevard_tree", None),
        X("13.set.flower_field__p05", "Lush Scarlet Poppy Meadow Bank West", "P3", 1.42, 1.18, 0.91, 0.28, "ground_curb", "Scarlet Poppy Meadow"),
        X("13.set.flower_field__p06", "Lavender & Wildflower Bank East", "P3", 1.40, 1.44, 0.91, 0.28, "ground_curb", None),
    ],
    "13.5": [
        X("13.props.distant-window__p01", "Brick Gabled House with Open Window Hole", "P4", 2.44, 1.20, 0.90, 0.48, "wall_with_door_hole", "Brick Gable Window"),
        X("13.set.church_pews__p02", "Carved Stone Gothic Window Portal", "P4", 2.40, 1.46, 0.90, 0.46, "gable_portal_cap", "Gothic Window Portal"),
        X("13.set.church_pews__p07", "Carved Wooden Church Pew", "P3", 1.42, 1.22, 0.91, 0.26, "furniture_anchor", None),
        X("13.set.church_pews__p09", "Checkered Stone Nave Floor Strip", "P2", 1.08, 1.30, 0.93, 0.16, "ground_curb", None),
    ],
    "13.6": boulevard_tape_bridge(
        fence_id="13.set.harbor_quay_night_fire__p03",
        fence_label="Harbor Quay Stone Seawall",
        tree_ids=["13.set.drowned_atrium__p03", "13.set.drowned_atrium__p04", "12.hero.pools__p02", "12.hero.pools__p03"],
        tree_label="Harbor Promenade Tree",
        lamp_id="13.set.harbor_quay_night_fire__p02",
        lamp_label="Harbor Quay Gas Lamp",
        curb_id="13.set.harbor_quay_night_fire__p07",
        curb_label="Harbor Quay Flagstone Walk",
        station_title="Harbor Quay Toward Poem 14",
        floor_y=0.89,
    ),

    # =======================================================================
    # POEM 14 · HOT MINUTE (Continuous Tape: Wide Atlantis Harbor -> Film-Frame Portals -> Vintage Doors -> Ballroom Arch -> Genesis Room Return)
    # =======================================================================
    "14.0": [
        X("14.set.harbor_atlantis_wide__p04", "Island Citadel of Atlantis", "P5", 3.80, 1.22, 0.78, 0.28, "vista_backing", None),
        X("14.set.harbor_atlantis_wide__p05", "Waterfront Colonnade Pier", "P4", 2.44, 1.44, 0.88, 0.28, "span_deck", "Atlantis Harbor Pier"),
        X("14.set.harbor_atlantis_wide__p06", "Gaff-Rigged Harbor Sailboat", "P3", 1.42, 1.16, 0.90, 0.28, "story_prop", None),
        X("14.set.harbor_atlantis_wide__p07", "Long Stone Harbor Breakwater", "P2", 1.08, 1.30, 0.93, 0.14, "ground_curb", None),
    ],
    "14.1": [
        X("14.set.broll_life__p03", "Cinema Filmstrip Frame Portal #1", "P4", 2.44, 1.20, 0.88, 0.36, "wall_with_door_hole", "Memory Filmstrip Portal"),
        X("14.fx.filmframe__p01", " Sprocketed 35mm Film Aperture", "P4", 2.40, 1.44, 0.88, 0.38, "wall_with_door_hole", None),
        X("14.props.door__p01", "Standing Weathered Timber Door #1", "P3", 1.40, 1.32, 0.90, 0.44, "gable_portal_cap", "First Memory Door"),
        X("14.set.black_void__p03", "Film-Stage Threshold Plinth", "P2", 1.08, 1.30, 0.93, 0.16, "ground_curb", None),
    ],
    "14.2": [
        X("12.set.temple_backroom__p01", "Gallery Wall with Open Doorway Hole", "P4", 2.44, 1.24, 0.90, 0.52, "wall_with_door_hole", "Life-Reel Gallery Wall"),
        X("14.props.door__p02", "Carved Vintage Wooden Door #2", "P3", 1.42, 1.46, 0.90, 0.44, "gable_portal_cap", "Second Memory Door"),
        X("14.props.party__p19", "Festive Paper Lantern Garland", "P3", 1.38, 1.28, 0.42, 0.22, "ceiling_fixture", None),
        X("13.set.flower_field__p05", "Scarlet Poppies Along the Baseboard", "P2", 1.08, 1.16, 0.92, 0.24, "ground_curb", None),
    ],
    "14.3": [
        X("01.set.city_fall_void__p01", "Graytone Skyscraper Canyon Wall", "P4", 2.44, 1.16, 0.90, 0.56, "wall_bay", "Graytone Canyon Wall"),
        X("03.hero.chapel__p01", "Stone Gabled Sanctuary Portal", "P4", 2.40, 1.42, 0.90, 0.46, "gable_portal_cap", "Sanctuary Gable Portal"),
        X("14.props.door__p03", "Half-Open Vintage Wooden Door #3", "P3", 1.40, 1.28, 0.90, 0.44, "gable_portal_cap", "Third Memory Door"),
        X("01.hero.catwalk__p03", "Connecting Iron Catwalk Deck", "P3", 1.46, 1.12, 0.89, 0.16, "span_deck", None),
    ],
    "14.4": [
        X("14.set.vintage_party__p02", "Warm Wood-Panelled Ballroom Wall & Window", "P4", 2.44, 1.24, 0.90, 0.52, "wall_with_door_hole", "Ballroom Wall Extension"),
        X("14.set.vintage_party__p03", "Grand Timber Ballroom Doorway Arch", "P3", 1.42, 1.46, 0.90, 0.46, "gable_portal_cap", "The Vintage Doorway"),
        X("14.props.door__p01", "Open Vintage Wooden Door Leaf", "P3", 1.38, 1.36, 0.90, 0.44, "gable_portal_cap", None),
        X("14.set.vintage_party__p04", "Golden Parquet Ballroom Floor", "P3", 1.48, 1.30, 0.93, 0.20, "span_deck", None),
    ],
    "14.5": [
        X("14.set.vintage_party__p02", "1940s Ballroom Wainscot & Window Wall", "P4", 2.44, 1.24, 0.90, 0.52, "wall_with_door_hole", "Waltz Hall Gallery"),
        X("14.set.vintage_party__p01", "Ballroom Ceiling Beam Cornice", "P4", 2.40, 1.28, 0.36, 0.18, "roof_cornice", None),
        X("14.set.vintage_party__p03", "Timber Archway Back to Poem 01", "P3", 1.42, 1.46, 0.90, 0.46, "gable_portal_cap", "Archway to the Genesis Room"),
        X("14.props.party__p19", "Glowing Paper Lantern String", "P3", 1.38, 1.28, 0.42, 0.22, "ceiling_fixture", None),
    ],
    "14.6": catwalk_gable_wall_extension(
        catwalk_deck_id="01.hero.catwalk__p03",
        catwalk_truss_id="01.hero.catwalk__p05",
        wall_hole_id="12.set.temple_backroom__p01",
        wall_label="Genesis Bedroom Wall with Doorway Hole",
        gable_portal_id="03.hero.chapel__p01",
        gable_label="Stone Gable Portal Loop to Poem 01",
        station_title="Full Circle · Back to Poem 01",
        floor_y=0.90,
    ),
}


def get_scene_lego_extension(skey: str) -> List[Dict[str, Any]]:
    """
    Returns a deep copy of the Outside-the-Frame Lego Set Extension for `skey`,
    calibrated to the Hyper-Flat Architectural Datum:
      - `wall_with_door_hole` / `wall_bay`: Full-frame height (`y = 0.995, scale = 0.96..0.98`),
        spanning the `760px` side extension (`x in [1.00 .. 1.59]`) flush with the `1280x720` frame.
      - `gable_portal_cap`: Seated over the doorway hole (`y = 0.995, scale = 1.18..1.24`),
        with its gabled stone/timber roof protruding into the upper headroom (`y < 0`) above the frame top.
      - `boulevard_fence` / `boulevard_tree` / `boulevard_lamp` / `ground_curb`: Continuous
        horizontal boulevard tape bridging into the next scene on the poem tape.
    """
    raw = SCENE_LEGO_EXTENSIONS.get(skey, [])
    out: List[Dict[str, Any]] = []
    for item in raw:
        d = dict(item)
        role = d.get("lego_role", "wall_bay")
        sc = float(d.get("scale", 0.50))
        y = float(d.get("y", 0.96))
        if role in ("wall_with_door_hole", "wall_bay"):
            d["y"] = 0.995
            d["scale"] = round(max(0.92, min(1.00, sc * 1.78 if sc < 0.75 else sc)), 3)
        elif role == "gable_portal_cap":
            d["y"] = 0.995
            d["scale"] = round(max(1.14, min(1.26, sc * 2.65 if sc < 0.75 else sc)), 3)
        elif role == "boulevard_tree":
            d["y"] = 0.99
            d["scale"] = round(max(0.74, min(0.88, sc * 2.25 if sc < 0.55 else sc)), 3)
        elif role == "boulevard_lamp":
            d["y"] = 0.99
            d["scale"] = round(max(0.64, min(0.74, sc * 1.85 if sc < 0.50 else sc)), 3)
        elif role == "boulevard_fence":
            d["y"] = 0.99
            d["scale"] = round(max(0.46, min(0.56, sc * 2.00 if sc < 0.38 else sc)), 3)
        elif role in ("span_deck", "span_truss"):
            d["y"] = round(max(0.88, min(0.995, y)), 3)
            d["scale"] = round(max(0.22, min(0.38, sc * 1.35 if sc < 0.22 else sc)), 3)
        elif role == "ground_curb":
            d["y"] = 1.00
            d["scale"] = round(max(0.20, min(0.28, sc * 1.45 if sc < 0.18 else sc)), 3)
        out.append(d)
    return out

