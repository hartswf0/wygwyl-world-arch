#!/usr/bin/env python3
"""
build_multiplane_play_levels.py
===============================
Rebuilds all 14 playable poem levels (`shots/play/levels/01..14/level.json` and
`s*.webp` scene plates) + `shots/play/level_assets_catalog.json` using purified
die-cut multiplane architectural & prop silhouettes from `wygwyl_atlas_manifest.json`
and `scene_collage_plans.json`.

Key Quality Guarantees:
  1. Purifies every scene of flat rectangular backing-strip bars (`ar > 2.2` and
     `opaque_ratio > 0.80` like `11.set.calm_sea__p01` or `11.fx.light__p02`) and
     eliminates generic `06.set.atlantis_gate` repetition across unrelated poems.
  2. Stages 3 distinct, scene-specific die-cut Architectural & Prop Stations per
     scene (Left `x≈0.22`, Center `x≈0.52`, Right `x≈0.78`) plus co-located
     kinetic subparts (spinning car/motorcycle wheels, DJ vinyl platters,
     bistro table base/stem/cup/chair, hourglass bulbs/sand, jointed hands).
  3. Renders 90 clean, distinct `s*.webp` shelf/preview plates from the painted
     `shots/world/<id>/backdrop.webp` world backdrops + grounded proscenium floor
     + die-cut architectural/prop stations.
  4. Exports a purified `shots/play/level_assets_catalog.json` (only true die-cut
     silhouettes, zero rectangular strip bars) for the live `🛠️ Assemble Stage`
     workbench in `shots/play/levels.html`.
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
PLANS_PATH = RELEASE_DIR / "scene_collage_plans.json"
MANIFEST_PATH = RELEASE_DIR / "wygwyl_atlas_manifest.json"
CATALOG_OUT_PATH = PLAY_DIR / "level_assets_catalog.json"


# ---------------------------------------------------------------------------
# Curated Scene-Specific Die-Cut Architectural & Prop Stations (All 90 Scenes)
# ---------------------------------------------------------------------------
# Every part_id below has been alpha-verified to be a clean die-cut architectural
# or prop silhouette (zero rectangular backing-strip bars!).
SCENE_STATION_ENRICHMENTS: Dict[Tuple[int, int], List[Tuple[str, str, str, str, float, float, float, float, str]]] = {
    # POEM 01 · OUT OF LIFE
    (1, 0): [
        ("01.props.room__p01", "Wooden Bedroom Dresser", "Bedroom Dresser & TV Portal", "P3", 1.45, 0.22, 0.88, 0.34, "drawer_slide"),
        ("01.props.room__p05", "Flickering TV Screen Portal", "Bedroom Dresser & TV Portal", "P3", 1.42, 0.22, 0.66, 0.20, "portal_tv_flicker"),
        ("01.props.window__p01", "High-Rise Sash Window Frame", "High-Rise Sash Window", "P4", 2.42, 0.52, 0.84, 0.54, "portal_aperture"),
        ("01.props.window__p06", "Steel Fire-Escape Balcony Rail", "Fire-Escape Threshold", "P4", 2.34, 0.78, 0.86, 0.28, "fire_escape_landing"),
    ],
    (1, 1): [
        ("01.props.room__p13", "Bedroom Writing Chair & Desk", "Bedroom Reading Desk", "P3", 1.45, 0.22, 0.88, 0.26, "lamp_glow"),
        ("01.props.window__p01", "High-Rise Sash Window", "Haze at the Window", "P4", 2.42, 0.52, 0.84, 0.54, "portal_aperture"),
        ("01.fx.haze-words__p01", "Drifting Amber Haze Ribbon", "Fire-Escape Haze Rail", "P1", 0.48, 0.78, 0.68, 0.24, "cloud_drift_L"),
    ],
    (1, 2): [
        ("01.props.window__p01", "Open Apartment Sash Window", "Open Sash Window", "P4", 2.44, 0.22, 0.84, 0.52, "portal_aperture"),
        ("01.hero.catwalk__p01", "Steel Catwalk Platform", "Catwalk & Fire Escape", "P4", 2.36, 0.52, 0.87, 0.44, "fire_escape_landing"),
        ("01.hero.severn__p01", "Severn Brick Tower Facade", "Drop Off the Fire Escape", "P4", 2.50, 0.80, 0.86, 0.54, "portal_aperture"),
    ],
    (1, 3): [
        ("01.set.city_fall_void__p02", "Vertical City Tower Canyon", "High-Rise Canyon Wall", "P4", 2.52, 0.22, 0.85, 0.52, "portal_other_world"),
        ("01.fx.haze-words__p02", "Falling Stanza Word Banner", "The Vertical Freefall", "P3", 1.40, 0.52, 0.62, 0.24, "tambourine_arc"),
        ("01.props.chandeliers__p01", "Distant Ballroom Chandelier Below", "Skylight Above Ballroom", "P3", 1.44, 0.78, 0.44, 0.24, "chandelier_sway"),
    ],
    (1, 4): [
        ("01.props.chandeliers__p01", "Six-Arm Crystal Chandelier Left", "Crystal Chandelier Hall", "P3", 1.48, 0.24, 0.34, 0.24, "chandelier_sway"),
        ("14.set.vintage_party__p03", "Warm 1940s Ballroom Archway", "Vintage Waltz Floor", "P4", 2.46, 0.52, 0.85, 0.52, "portal_other_world"),
        ("01.props.chandeliers__p02", "Golden Ballroom Chandelier Right", "Ballroom Bandstand", "P3", 1.48, 0.78, 0.34, 0.24, "chandelier_sway"),
    ],
    (1, 5): [
        ("14.set.vintage_party__p03", "Ballroom Colonnade Arch", "Ballroom Colonnade", "P4", 2.46, 0.22, 0.85, 0.48, "portal_aperture"),
        ("01.props.trapdoor__p01", "Shattered Ballroom Floor Trapdoor", "Hole in the Floor", "P3", 1.36, 0.54, 0.90, 0.34, "portal_aperture"),
        ("01.props.trapdoor__p05", "Splintered Trapdoor Rim", "Edge of the Abyss", "P3", 1.34, 0.78, 0.88, 0.24, "drawer_slide"),
    ],

    # POEM 02 · FLASHING LIGHTS
    (2, 0): [
        ("02.set.overseer_skyline__p02", "Night Highway Overseer Tower", "Night Highway Tower", "P4", 2.48, 0.22, 0.85, 0.50, "portal_other_world"),
        ("02.props.car__p01", "Family Sedan (Headlights Off)", "Sedan in the Dark", "P3", 1.40, 0.54, 0.86, 0.28, "car_chassis"),
        ("02.set.overseer_skyline__p03", "Distant Overseer Skyline Spire", "Silent Scream Horizon", "P4", 2.46, 0.80, 0.85, 0.50, "portal_aperture"),
    ],
    (2, 1): [
        ("02.props.poet-eye-aperture__p01", "Dilating Poet Eye Aperture", "Dilating Eye Portal", "P4", 2.44, 0.24, 0.70, 0.32, "portal_aperture"),
        ("02.set.bedroom_night__p02", "Midnight Bedroom Mirror Glass", "The Midnight Mirror", "P4", 2.40, 0.52, 0.84, 0.48, "portal_aperture"),
        ("02.set.living_room_1990s__p05", "Bedside Ceramic Table Lamp", "Shadowed Bedside Lamp", "P3", 1.44, 0.78, 0.86, 0.22, "lamp_glow"),
    ],
    (2, 2): [
        ("02.set.living_room_1990s__p01", "1990s Window Looking Out", "Driveway Window View", "P4", 2.44, 0.24, 0.84, 0.50, "portal_aperture"),
        ("02.props.car__p01", "1990s Family Sedan Pulling Up", "Family Sedan Arriving", "P3", 1.40, 0.56, 0.86, 0.28, "car_chassis"),
        ("02.fx.lights-iris__p01", "Sweeping Headlight Beam Cone", "Flashing Headlight Glare", "P1", 0.46, 0.78, 0.84, 0.24, "headlight_beam"),
    ],
    (2, 3): [
        ("02.set.living_room_1990s__p05", "Ceramic Living Room Lamp", "Living Room Table Lamp", "P3", 1.45, 0.20, 0.86, 0.22, "lamp_glow"),
        ("02.set.living_room_1990s__p01", "1990s Living Room Window Frame", "Childhood Window Frame", "P4", 2.42, 0.52, 0.84, 0.52, "portal_aperture"),
        ("02.props.tambourine__p01", "Seven-Year-Old's Wooden Tambourine", "Ghost Child's Tambourine", "P3", 1.34, 0.78, 0.76, 0.14, "tambourine_arc"),
    ],
    (2, 4): [
        ("02.set.living_room_1990s__p03", "Drawn Living Room Window Drape", "Raised Window Blinds", "P4", 2.38, 0.22, 0.84, 0.46, "curtain_sway_L"),
        ("02.props.car__p01", "Family Sedan Cabin in Driveway", "Parents' Car Cabin", "P3", 1.40, 0.56, 0.86, 0.28, "car_chassis"),
        ("02.props.window__p01", "Driveway Side Sash Window", "Argument Behind Glass", "P4", 2.42, 0.82, 0.84, 0.48, "portal_aperture"),
    ],
    (2, 5): [
        ("02.props.window__p01", "Living Room Sash Window", "Living Room Window", "P4", 2.42, 0.24, 0.84, 0.50, "portal_aperture"),
        ("02.props.tambourine__p01", "Flying Wooden Tambourine", "Tambourine in Flight", "P3", 1.28, 0.52, 0.56, 0.14, "tambourine_arc"),
        ("03.props.rose-window__p01", "Shattering Chapel Rose Window", "Chapel Window Portal", "P4", 2.45, 0.78, 0.62, 0.44, "stained_glass_glow"),
    ],

    # POEM 03 · HOW TO BREAK OFF AN ENGAGEMENT
    (3, 0): [
        ("03.props.rose-window__p01", "Gothic Rose Window Tracery", "Chapel Rose Window", "P4", 2.45, 0.24, 0.60, 0.44, "portal_aperture"),
        ("02.props.tambourine__p01", "Tambourine Crossing Stained Glass", "Arc of the Tambourine", "P3", 1.28, 0.52, 0.54, 0.14, "tambourine_arc"),
        ("03.hero.chapel__p01", "Gothic Chapel Tower & Nave", "Chapel Altar Nave", "P4", 2.42, 0.78, 0.86, 0.52, "portal_aperture"),
    ],
    (3, 1): [
        ("03.hero.chapel.interior-states__p01", "Empty Chapel Stone Wall", "Empty Chapel Nave", "P4", 2.46, 0.22, 0.85, 0.52, "portal_aperture"),
        ("03.hero.chapel.interior-states__p03", "Abandoned Wooden Chapel Pew", "Empty Wedding Pews", "P3", 1.44, 0.52, 0.88, 0.36, "lamp_base"),
        ("03.props.cobwebs__p01", "Draped Altar Cobwebs", "Cobwebbed Sanctuary", "P3", 1.38, 0.78, 0.72, 0.22, "curtain_sway_L"),
    ],
    (3, 2): [
        ("03.set.chapel_side_doors__p01", "Left Chapel Side Door", "Left Chapel Doorway", "P4", 2.42, 0.22, 0.85, 0.50, "portal_aperture"),
        ("03.props.gifts-bread-cups__p01", "Unopened Wedding Gifts & Bread", "Table of Wedding Gifts", "P3", 1.40, 0.52, 0.86, 0.20, "lamp_glow"),
        ("03.set.chapel_side_doors__p02", "Right Chapel Exit Door", "Right Departure Door", "P4", 2.42, 0.80, 0.85, 0.50, "portal_aperture"),
    ],
    (3, 3): [
        ("03.hero.chapel.decay__p01", "Weathered Chapel Roof in Storm", "Storm Over the Chapel", "P4", 2.46, 0.24, 0.85, 0.52, "portal_aperture"),
        ("03.hero.chapel.decay__p03", "Buffeted Stone Bell Tower", "Buffeted Chapel Nave", "P4", 2.44, 0.52, 0.85, 0.50, "portal_aperture"),
        ("03.fx.storm-light__p01", "Diagonal Storm Lightning Shaft", "Lightning & Gale", "P1", 0.46, 0.78, 0.58, 0.28, "light_ray"),
    ],
    (3, 4): [
        ("03.hero.chapel.ruin__p01", "Ruined Chapel Timber Arch", "Collapsed Chapel Arch", "P4", 2.46, 0.22, 0.85, 0.50, "portal_aperture"),
        ("03.props.gifts-bread-cups__p03", "Washed-Ashore Chalice & Gifts", "Shore of Remnants", "P3", 1.40, 0.52, 0.87, 0.20, "wave_mid"),
        ("03.props.strings-footprints__p01", "Two Sets of Footsteps in Wet Sand", "Footsteps on the Shore", "P3", 1.36, 0.78, 0.88, 0.20, "drawer_slide"),
    ],
    (3, 5): [
        ("03.hero.chapel.ruin__p04", "Fallen Bell Tower Cap on Sand", "Ruined Shore Stone", "P4", 2.40, 0.22, 0.86, 0.44, "portal_aperture"),
        ("03.props.tambourine-broken__p01", "Shattered Tambourine Rim & Jingles", "Shattered Tambourine", "P3", 1.32, 0.52, 0.88, 0.16, "tambourine_arc"),
        ("04.set.shore_night__p03", "Breaking Night Shore Foam", "Dark Ocean Threshold", "P1", 0.50, 0.78, 0.90, 0.20, "wave_near"),
    ],

    # POEM 04 · NEVERMORE
    (4, 0): [
        ("04.props.word-shore__p02", "Washed-Up Iron Letters on Sand", "Shore of Broken Words", "P3", 1.42, 0.22, 0.88, 0.24, "wave_mid"),
        ("04.set.shore_night__p04", "Weathered Driftwood Stump", "Driftwood Wreckage", "P3", 1.40, 0.52, 0.87, 0.24, "boat_rock"),
        ("04.props.ravens-stumps__p01", "Perched Shore Raven", "Raven on the Stump", "P3", 1.38, 0.78, 0.84, 0.18, "wing_flap_L"),
    ],
    (4, 1): [
        ("04.set.shore_night__p06", "Wind-Bent Shore Tree", "Silent Night Shore", "P4", 2.44, 0.22, 0.85, 0.46, "curtain_sway_L"),
        ("04.hero.viaduct__p02", "Distant Stone Viaduct Arch Pier", "Viaduct in the Silence", "P4", 2.50, 0.52, 0.84, 0.52, "portal_aperture"),
        ("04.props.ravens-stumps__p03", "Watching Raven on Stone", "Stone Sentinel", "P3", 1.40, 0.78, 0.86, 0.22, "wing_flap_R"),
    ],
    (4, 2): [
        ("04.props.word-shore__p02", "Folded Whisper Script in Sand", "Folded Whispers", "P3", 1.42, 0.22, 0.88, 0.24, "drawer_slide"),
        ("04.props.heart__p01", "Beating Anatomical Poet Heart", "Beating Heart on the Sand", "P3", 1.32, 0.50, 0.82, 0.15, "heart_beat"),
        ("04.props.poet-jointed-hands__p01", "Articulated Weave Hands Cupping Heart", "Jointed Hands Reach", "P3", 1.30, 0.76, 0.78, 0.18, "weave_hand_articulation"),
    ],
    (4, 3): [
        ("04.hero.viaduct__p03", "Lower Viaduct Stone Arch", "Base of the Incline", "P4", 2.42, 0.22, 0.85, 0.50, "fire_escape_landing"),
        ("04.props.faith-blooms__p05", "Rooted Mustard-Seed Golden Bloom", "Mustard Seed Bloom", "P3", 1.34, 0.52, 0.86, 0.16, "flower_bloom"),
        ("04.hero.viaduct__p04", "Upper Viaduct Stone Pier", "Crest of the Trail", "P4", 2.46, 0.80, 0.84, 0.52, "portal_aperture"),
    ],
    (4, 4): [
        ("04.props.faith-blooms__p02", "Luminous Night Garden Bloom West", "Night Garden Entrance", "P3", 1.38, 0.24, 0.86, 0.18, "flower_bloom"),
        ("04.props.faith-blooms__p07", "Radiant Golden Flowerhead", "Center of the Bloom Field", "P3", 1.34, 0.52, 0.84, 0.15, "flower_bloom"),
        ("04.fx.moon-reach__p01", "Silver Moon Halo Over Field", "Moonlit Field Edge", "P5", 3.60, 0.78, 0.30, 0.24, "sun_pulse"),
    ],
    (4, 5): [
        ("04.props.poet-jointed-hands__p01", "Searching Left Jointed Hand", "Left Hand on the Stone Ledge", "P3", 1.34, 0.24, 0.78, 0.18, "weave_hand_articulation"),
        ("04.props.heart__p01", "Pulsing Heart Chambers", "The Hollow Chest Awakens", "P3", 1.32, 0.52, 0.76, 0.14, "heart_beat"),
        ("04.props.poet-jointed-hands__p02", "Searching Right Jointed Hand", "Putting the Hands Back On", "P3", 1.34, 0.78, 0.78, 0.18, "weave_hand_articulation"),
    ],
    (4, 6): [
        ("04.set.shore_night__p06", "Swaying Night Field Cypress", "Western Meadow", "P4", 2.38, 0.22, 0.86, 0.46, "curtain_sway_L"),
        ("04.hero.viaduct__p02", "Ancient Stone Archway", "Standing Whole in the Field", "P4", 2.44, 0.52, 0.84, 0.52, "portal_aperture"),
        ("04.props.faith-blooms__p01", "Tall Blooming Faith Stem", "Eastern Horizon Trail", "P3", 1.36, 0.78, 0.86, 0.18, "flower_bloom"),
    ],

    # POEM 05 · BLOODLINES
    (5, 0): [
        ("05.set.night_field_parade__p04", "Night Meadow Stone Cairn", "Still Night Meadow", "P4", 2.40, 0.22, 0.86, 0.46, "curtain_sway_L"),
        ("05.set.night_field_parade__p03", "Curved Celestial Globe Floor", "Celestial Globe Axis", "P3", 1.42, 0.52, 0.88, 0.26, "planet_orbit"),
        ("05.set.night_field_parade__p06", "Parade Lantern Archway", "Parade Perimeter Arch", "P4", 2.46, 0.78, 0.86, 0.46, "portal_aperture"),
    ],
    (5, 1): [
        ("05.props.star-names__p01", "Constellation Nameplate West", "First Star Constellation", "P5", 3.50, 0.24, 0.34, 0.22, "sun_pulse"),
        ("05.props.galaxy-universe__p01", "Swirling Spiral Galaxy Core", "Naming My Own Stars", "P5", 3.55, 0.52, 0.32, 0.24, "planet_orbit"),
        ("05.props.star-names__p02", "Constellation Nameplate East", "Eastern Star Canopy", "P5", 3.50, 0.78, 0.34, 0.22, "sun_pulse"),
    ],
    (5, 2): [
        ("05.set.humid_basement__p02", "Southern-Pine Basement Window Well", "Basement Window Well", "P4", 2.44, 0.24, 0.82, 0.46, "portal_aperture"),
        ("05.props.staff-mattress-emblem__p02", "Childhood Basement Emblem & Bed", "Southern-Pine Basement", "P3", 1.42, 0.52, 0.86, 0.28, "lamp_base"),
        ("05.props.staff-mattress-emblem__p01", "Carved Wooden Ancestor Staff", "Ancestor Staff Corner", "P3", 1.38, 0.78, 0.84, 0.28, "lamp_glow"),
    ],
    (5, 3): [
        ("05.props.fingerprint__p01", "Luminous Whorled Fingerprint", "Lines of the Palm", "P3", 1.38, 0.24, 0.74, 0.22, "sun_pulse"),
        ("05.props.galaxy-universe__p02", "New Universe Cupped in Palms", "A New Universe in Hands", "P3", 1.34, 0.52, 0.70, 0.22, "planet_orbit"),
        ("05.set.winged_marble_gate__p03", "Winged Marble Sanctuary Arch", "Altar of Blessings", "P4", 2.44, 0.78, 0.84, 0.52, "portal_aperture"),
    ],
    (5, 4): [
        ("05.props.fingerprint__p05", "Crimson Pulse Fingerprint", "Blood Through the Hands", "P3", 1.36, 0.24, 0.76, 0.22, "heart_beat"),
        ("04.props.poet-jointed-hands__p01", "Outstretched Jointed Poet Hands", "Living Palms", "P3", 1.32, 0.52, 0.78, 0.18, "weave_hand_articulation"),
        ("05.hero.perimeter__p03", "Carved Stone Watchtower Pillar", "The Watchtower Pillar", "P4", 2.46, 0.78, 0.85, 0.48, "portal_aperture"),
    ],
    (5, 5): [
        ("05.set.winged_marble_gate__p01", "Left Winged Marble Gate Pillar", "Left Winged Pillar", "P4", 2.42, 0.22, 0.84, 0.54, "portal_aperture"),
        ("05.set.winged_marble_gate__p03", "Central Winged Marble Gate Arch", "The Gates Open to Atlantis", "P4", 2.40, 0.52, 0.84, 0.54, "portal_aperture"),
        ("05.set.winged_marble_gate__p05", "Right Winged Marble Gate Pillar", "Right Winged Pillar", "P4", 2.42, 0.80, 0.84, 0.54, "portal_aperture"),
    ],

    # POEM 06 · RESURRECTING ATLANTIS (Every scene has completely distinct, clean architecture!)
    (6, 0): [
        ("05.set.winged_marble_gate__p02", "Outer Marble Gate Column", "Outer Light Gate", "P4", 2.46, 0.22, 0.85, 0.52, "portal_aperture"),
        ("06.set.atlantis_gate__p01", "Central Atlantis Light Gate Portal", "The Light Gates Open", "P4", 2.40, 0.52, 0.84, 0.58, "portal_aperture"),
        ("06.set.crystal_tree_hall__p01", "Crystal Tree Glowing Beyond Gate", "Crystal Sanctuary Vista", "P4", 2.58, 0.78, 0.82, 0.48, "portal_inner_world"),
    ],
    (6, 1): [
        ("06.fx.comet__p01", "Streaking Golden Comet West", "Yellow-Brick Causeway", "P5", 3.62, 0.24, 0.30, 0.24, "tambourine_arc"),
        ("06.set.atlantis_waterfront.skyline__p04", "Causeway Bridge Watchtower", "Following the Comets", "P4", 2.42, 0.52, 0.84, 0.50, "portal_aperture"),
        ("06.set.atlantis_waterfront.skyline__p01", "Rising Atlantis Domes & Spires", "Atlantis Horizon Ahead", "P4", 2.48, 0.78, 0.82, 0.56, "portal_aperture"),
    ],
    (6, 2): [
        ("06.set.atlantis_waterfront.skyline__p02", "Western Waterfront Spire", "Rising Waterfront Wall", "P4", 2.44, 0.22, 0.84, 0.52, "portal_aperture"),
        ("06.set.atlantis_waterfront.skyline__p01", "Grand Capital Dome of Atlantis", "The City Rises From the Sea", "P4", 2.48, 0.52, 0.82, 0.58, "portal_aperture"),
        ("06.hero.teahouse__p01", "Harbor Teahouse Pavilion", "Waterfront Sanctuary Pavilion", "P4", 2.40, 0.80, 0.85, 0.50, "lamp_glow"),
    ],
    (6, 3): [
        ("06.set.crystal_tree_hall__p02", "Jungle Interface Banyan Arch", "Jungle Interface Threshold", "P4", 2.44, 0.22, 0.84, 0.50, "flower_bloom"),
        ("06.props.coin-booth__p01", "Heart-Scan Admission Booth", "Heart-Scan Admission Booth", "P3", 1.42, 0.52, 0.86, 0.38, "lamp_glow"),
        ("06.props.coin-booth__p02", "Golden Heart-Scan Admission Coin", "Golden Admission Token", "P3", 1.36, 0.78, 0.76, 0.16, "sun_pulse"),
    ],
    (6, 4): [
        ("06.set.atlantis_plaza__p01", "Left Plaza Stained Glazing Arch", "West Plaza Colonnade", "P4", 2.44, 0.22, 0.85, 0.52, "portal_aperture"),
        ("06.set.crystal_tree_hall__p01", "Central Plaza Crystal Tree Hall", "City Center Sanctuary", "P4", 2.40, 0.52, 0.84, 0.52, "portal_inner_world"),
        ("06.set.atlantis_plaza__p03", "Right Plaza Stained Glazing Arch", "East Plaza Colonnade", "P4", 2.44, 0.80, 0.85, 0.52, "portal_aperture"),
    ],
    (6, 5): [
        ("06.set.narrow_streets__p01", "Lantern-Lit Cobblestone Wall Left", "West Cobblestone Arch", "P4", 2.42, 0.20, 0.86, 0.54, "portal_aperture"),
        ("06.props.lantern-candle-guitar__p01", "Glowing Street Lantern & Candle", "Candlelit Narrow Street", "P3", 1.40, 0.50, 0.74, 0.24, "lamp_glow"),
        ("06.set.narrow_streets__p03", "Far Cobblestone Street Archway", "Musician's Street Corner", "P4", 2.44, 0.80, 0.86, 0.54, "portal_aperture"),
    ],
    (6, 6): [
        ("06.hero.teahouse__p01", "Lantern Teahouse Veranda", "Teahouse Veranda", "P4", 2.44, 0.22, 0.85, 0.48, "lamp_glow"),
        ("06.hero.house__p05", "Teal Atlantis House Entry Arch", "The House at the Plaza Edge", "P4", 2.40, 0.54, 0.85, 0.52, "portal_aperture"),
        ("06.hero.house__p02", "Warm Overhead String Lights", "Glowing House Entrance", "P3", 1.46, 0.78, 0.42, 0.32, "lamp_glow"),
    ],

    # POEM 07 · DJ TURN ME UP
    (7, 0): [
        ("07.props.speakers-vu__p08", "Left Bass Speaker Cabinet", "Left Speaker Stack", "P3", 1.46, 0.22, 0.86, 0.34, "speaker_pulse"),
        ("07.props.dj-decks__p02", "DJ Booth Console & Mixer", "DJ Turn Me Up Console", "P3", 1.40, 0.50, 0.86, 0.34, "dj_console"),
        ("07.props.speakers-vu__p07", "Right Bass Speaker Cabinet", "Right Speaker Stack", "P3", 1.46, 0.78, 0.86, 0.34, "speaker_pulse"),
    ],
    (7, 1): [
        ("07.hero.house.furniture__p03", "House Party Lounge Sofa", "House Party Lounge", "P3", 1.45, 0.22, 0.87, 0.32, "lamp_base"),
        ("07.props.mic-daisy-rings__p01", "Chrome Vocal Microphone on Stand", "Eyes Wide Shut at the Mic", "P3", 1.36, 0.50, 0.86, 0.28, "speaker_pulse"),
        ("07.props.dj-decks__p04", "Spinning Turntable Platter", "Turntable Platter Deck", "P3", 1.38, 0.78, 0.80, 0.16, "turntable_spin"),
    ],
    (7, 2): [
        ("07.props.speakers-vu__p08", "Woven Speaker Mesh Grille", "Ghosts in the Speaker Mesh", "P3", 1.44, 0.24, 0.86, 0.34, "speaker_pulse"),
        ("07.set.projection_vineyard__p03", "Vineyard Ghosts Arch Projection", "Projected Vineyard Wall", "P4", 2.48, 0.52, 0.78, 0.48, "portal_other_world"),
        ("07.props.speakers-vu__p04", "Glowing VU Meter Dial", "Resonant Bass Column", "P3", 1.44, 0.78, 0.76, 0.18, "speaker_pulse"),
    ],
    (7, 3): [
        ("07.props.speakers-vu__p04", "Red-Lining VU Meter Dial Left", "Left VU Meter in the Red", "P3", 1.40, 0.24, 0.76, 0.18, "speaker_pulse"),
        ("07.props.dj-decks__p02", "Overdriven DJ Mixer Console", "A Thousand Light Years Deck", "P3", 1.38, 0.50, 0.86, 0.34, "dj_console"),
        ("07.props.speakers-vu__p05", "Red-Lining VU Meter Dial Right", "Right VU Meter Peak", "P3", 1.40, 0.78, 0.76, 0.18, "speaker_pulse"),
    ],
    (7, 4): [
        ("07.props.mic-daisy-rings__p03", "Diverging Golden Wedding Bands", "Diverging Wedding Rings", "P3", 1.36, 0.24, 0.76, 0.16, "sun_pulse"),
        ("07.props.projection__p01", "Projected Boxed Home Aperture", "The Boxed Home Projection", "P4", 2.46, 0.52, 0.78, 0.46, "portal_tv_flicker"),
        ("07.hero.house__p03", "Shadowed House Room Arch", "Threshold of the Room", "P4", 2.40, 0.78, 0.85, 0.48, "portal_aperture"),
    ],
    (7, 5): [
        ("07.props.bar-handheld__p06", "Club Bar Bottle & Glass", "Club Bar Counter", "P3", 1.44, 0.22, 0.84, 0.22, "lamp_glow"),
        ("07.props.mic-daisy-rings__p02", "Stem of Eleven Daisy Petals", "Eleven Years in Daisy Petals", "P3", 1.34, 0.52, 0.85, 0.26, "flower_bloom"),
        ("07.hero.shaft__p01", "Vertical Light Shaft Portal", "Exit Stairwell Shaft", "P4", 2.42, 0.78, 0.84, 0.50, "portal_aperture"),
    ],
    (7, 6): [
        ("07.set.projection_three_roads__p01", "Three Diverging Roads in Rain", "Three Roads Crossroads", "P4", 2.46, 0.24, 0.82, 0.46, "portal_other_world"),
        ("07.fx.party-haze__p01", "Dim Streetlamp Fog & Rain Bank", "Rain & Dim Streetlights", "P1", 0.48, 0.52, 0.72, 0.26, "cloud_drift_L"),
        ("07.hero.house__p03", "Open Night Doorway to the Street", "Walking Out Chin High", "P4", 2.40, 0.78, 0.85, 0.48, "portal_aperture"),
    ],

    # POEM 08 · NEWLY SINGLE
    (8, 0): [
        ("08.hero.marquee__p01", "Glowing Rooftop Club Marquee", "Rooftop Club Marquee", "P4", 2.44, 0.24, 0.84, 0.50, "lamp_glow"),
        ("08.set.rooftop_club__p04", "Pulsing Rooftop Light Tower", "Where the Soul Leaves the Body", "P4", 2.38, 0.52, 0.85, 0.48, "speaker_pulse"),
        ("08.fx.soul-weather__p01", "Rising Luminous Soul Vapor", "Ascending Soul Current", "P1", 0.46, 0.78, 0.64, 0.24, "sun_pulse"),
    ],
    (8, 1): [
        ("08.hero.marquee.interior__p01", "Club Interior Neon Arch", "Crowded Club Arch", "P4", 2.44, 0.22, 0.84, 0.48, "portal_aperture"),
        ("07.props.dj-decks__p02", "Late-Night Rooftop DJ Console", "Last One to Leave the Floor", "P3", 1.40, 0.52, 0.86, 0.34, "dj_console"),
        ("08.set.rooftop_club__p05", "Rooftop Corner Beacon Tower", "Rooftop Parapet Edge", "P4", 2.40, 0.78, 0.85, 0.48, "lamp_glow"),
    ],
    (8, 2): [
        ("08.set.atlantis_aerial__p02", "Aerial Atlantis Spire Below", "Floating Above Atlantis", "P4", 2.50, 0.24, 0.85, 0.48, "portal_other_world"),
        ("08.set.equator_plain__p01", "Open Field at the Equator", "The Equator Plain", "P4", 2.42, 0.52, 0.85, 0.50, "water_backing"),
        ("08.props.moons-laundry__p01", "Twin Equator Moons & Laundry Line", "Skyline Laundry & Moons", "P5", 3.55, 0.78, 0.36, 0.24, "planet_orbit"),
    ],
    (8, 3): [
        ("08.props.basins__p01", "Left Stone Ice-Water Basin", "First Ice-Water Basin", "P3", 1.42, 0.22, 0.87, 0.26, "wave_mid"),
        ("08.props.basins__p02", "Central Baptism Font of Ice Water", "Angels' Ice-Water Baptism", "P3", 1.38, 0.50, 0.87, 0.28, "wave_near"),
        ("08.cast.angel.wings__p03", "Feathered Angel Sanctuary Wings", "Winged Angel Choir", "P3", 1.36, 0.76, 0.74, 0.26, "wing_flap_L"),
    ],
    (8, 4): [
        ("08.fx.soul-weather__p02", "Parting Morning Haze Curtain", "Parting of the Haze", "P1", 0.48, 0.24, 0.66, 0.26, "cloud_drift_L"),
        ("08.set.rooftop_club__p04", "Quiet Dawn Rooftop Beacon", "Soul Re-Entering the Body", "P4", 2.40, 0.52, 0.85, 0.48, "portal_aperture"),
        ("08.props.basins__p03", "Cleansing Basin on the Terrace", "Terrace Recovery Basin", "P3", 1.42, 0.78, 0.87, 0.24, "wave_mid"),
    ],
    (8, 5): [
        ("08.set.rooftop_club__p05", "West Rooftop Balustrade Tower", "Rooftop Balustrade", "P4", 2.40, 0.22, 0.85, 0.48, "portal_aperture"),
        ("08.set.equator_plain__p03", "Distant Mountain Ridge at Dawn", "Mountains From the Rooftop", "P4", 2.48, 0.52, 0.82, 0.52, "water_backing"),
        ("09.props.moon-sun__p01", "Rising Morning Sun Over Ridge", "First Light on the Peaks", "P5", 3.60, 0.78, 0.28, 0.20, "sun_pulse"),
    ],

    # POEM 09 · YET, HEARD
    (9, 0): [
        ("09.set.atlantis_club_sidewalk__p04", "Club Sidewalk Colonnade West", "Outside the Club Sidewalk", "P4", 2.44, 0.22, 0.85, 0.50, "portal_aperture"),
        ("09.set.atlantis_club_sidewalk__p05", "Harbor Street Archway", "Spotting the EX in the Crowd", "P4", 2.40, 0.52, 0.85, 0.50, "portal_aperture"),
        ("09.props.moon-sun__p01", "Luminous Shared Moon Overhead", "Under the Shared Moon", "P5", 3.60, 0.78, 0.26, 0.20, "sun_pulse"),
    ],
    (9, 1): [
        ("09.set.atlantis_harbor_street__p07", "Harbor Street Lantern Post", "Harbor Street Facade", "P4", 2.44, 0.24, 0.85, 0.44, "lamp_glow"),
        ("09.set.atlantis_harbor_street__p09", "Moonlit Quay Stone Arch", "Walking Toward the Moon", "P4", 2.38, 0.52, 0.85, 0.46, "portal_aperture"),
        ("09.props.moon-sun__p01", "Reflected Moon Over Harbor", "Moonlight on the Water", "P5", 3.58, 0.78, 0.28, 0.22, "sun_pulse"),
    ],
    (9, 2): [
        ("09.props.suitcases-notice__p01", "Packed Leather Suitcases on Curb", "Suitcases on the Curb", "P3", 1.42, 0.24, 0.88, 0.22, "drawer_slide"),
        ("09.props.phonebooth__p01", "Modular Harbor Phone Booth", "The Harbor Phone Booth", "P3", 1.44, 0.54, 0.86, 0.42, "booth_frame"),
        ("09.props.suitcases-notice__p02", "Departure Notice on Booth Glass", "Unanswered Departure Note", "P3", 1.38, 0.78, 0.78, 0.18, "lamp_glow"),
    ],
    (9, 3): [
        ("09.props.phonebooth__p01", "Illuminated Harbor Phone Booth", "Calling From the Booth", "P3", 1.44, 0.24, 0.86, 0.42, "booth_frame"),
        ("09.fx.call-abyss__p01", "Acoustic Voice Wave Across the Abyss", "Voice Across the Abyss", "P1", 0.48, 0.52, 0.58, 0.24, "phone_ring"),
        ("09.set.mother_living_room__p01", "Mother's Warm Living Room Interior", "Mother's Living Room", "P4", 2.42, 0.78, 0.85, 0.50, "lamp_glow"),
    ],
    (9, 4): [
        ("09.set.harbor_path_east__p02", "Old Harbor Stone Watchhouse", "Inner Harbor Watchhouse", "P4", 2.44, 0.22, 0.85, 0.50, "portal_aperture"),
        ("09.set.atlantis_club_sidewalk__p06", "East Quay Stone Arch", "Father & Son Harbor Walk", "P4", 2.38, 0.52, 0.85, 0.48, "portal_aperture"),
        ("13.props.planet-boats__p06", "Moored Inner-Harbor Sailboat", "Inner Harbor Mooring", "P3", 1.46, 0.78, 0.82, 0.18, "boat_rock"),
    ],
    (9, 5): [
        ("09.set.harbor_path_east__p02", "Misty Quay Watchhouse", "Misty Quay Wall", "P4", 2.40, 0.24, 0.85, 0.48, "wave_far"),
        ("09.props.suitcases-notice__p03", "Abandoned Suitcase in Morning Mist", "Where Footsteps End", "P3", 1.40, 0.52, 0.88, 0.20, "drawer_slide"),
        ("01.fx.haze-words__p03", "Dissolving Morning Haze Plume", "The EX Dissolves Into Haze", "P1", 0.46, 0.78, 0.72, 0.26, "cloud_drift_L"),
    ],

    # POEM 10 · MAGIC RIDE
    (10, 0): [
        ("10.hero.shadowpool__p01", "Streetlamp Shadowpool Cone", "Under the Streetlamp Pool", "P4", 2.38, 0.24, 0.86, 0.48, "lamp_glow"),
        ("11.props.parked-motorcycle__p01", "Parked Cafe Motorcycle Under Lamp", "The Parked Motorcycle", "P3", 1.38, 0.52, 0.86, 0.30, "bike_chassis"),
        ("10.set.atlantis_streets__p07", "Midnight Atlantis Streetlamp Arch", "Empty Midnight Sidewalk", "P4", 2.46, 0.78, 0.85, 0.46, "portal_aperture"),
    ],
    (10, 1): [
        ("10.set.atlantis_streets__p08", "Brick Alleyway Arch", "Ignition Alleyway", "P4", 2.46, 0.22, 0.85, 0.46, "portal_aperture"),
        ("10.props.bike-skeleton__p01", "Running Cafe Motorcycle & Engine", "Mounting the Machine", "P3", 1.38, 0.52, 0.86, 0.28, "bike_chassis"),
        ("10.fx.ride-light__p02", "Ignited Headlight Beam Cone", "Headlight Cutting the Dark", "P1", 0.45, 0.76, 0.83, 0.22, "headlight_beam"),
    ],
    (10, 2): [
        ("10.set.atlantis_streets__p07", "West Intersection Signal Arch", "First Midnight Intersection", "P4", 2.44, 0.22, 0.85, 0.46, "portal_aperture"),
        ("10.props.bike-skeleton__p01", "Cruising Motorcycle at Speed", "Riding Through Loneliness", "P3", 1.38, 0.52, 0.86, 0.28, "bike_chassis"),
        ("10.hero.shadowpool__p02", "East Avenue Streetlamp Pool", "Streaming Streetlights", "P4", 2.44, 0.78, 0.86, 0.46, "lamp_glow"),
    ],
    (10, 3): [
        ("10.hero.shadowpool__p03", "Grand Boulevard Light Cone", "Boulevard Facade", "P4", 2.46, 0.24, 0.86, 0.46, "lamp_glow"),
        ("10.props.bike-skeleton__p01", "Leaning Cafe Racer on the Avenue", "Swagger Down the Avenue", "P3", 1.38, 0.52, 0.86, 0.28, "bike_chassis"),
        ("10.fx.ride-light__p03", "Amber Streetlight Halo", "Velocity Light Trail", "P1", 0.46, 0.78, 0.68, 0.22, "headlight_beam"),
    ],
    (10, 4): [
        ("05.set.winged_marble_gate__p02", "Outer Boundary Pillar of Atlantis", "Leaving the City Gates", "P4", 2.46, 0.22, 0.85, 0.50, "portal_aperture"),
        ("10.props.bike-skeleton__p01", "Highway Motorcycle Heading Out", "Out of Atlantis", "P3", 1.38, 0.52, 0.86, 0.28, "bike_chassis"),
        ("09.props.moon-sun__p01", "Setting Moon at the Horizon", "Where the Moon Settles", "P5", 3.60, 0.78, 0.32, 0.20, "sun_pulse"),
    ],
    (10, 5): [
        ("10.set.mountain_road__p06", "Winding Mountain Cliffside Ridge", "Mountain Switchback", "P4", 2.42, 0.24, 0.85, 0.50, "fire_escape_landing"),
        ("10.props.tree-dawn-sign__p05", "Highway Dawn Milepost Sign", "Mountain Road at First Light", "P3", 1.42, 0.52, 0.85, 0.22, "lamp_glow"),
        ("10.props.tree-dawn-sign__p01", "Solitary Dawn Pine Tree on Crest", "First Light Over the Ridge", "P4", 2.38, 0.78, 0.85, 0.52, "flower_bloom"),
    ],

    # POEM 11 · NEW DAY
    (11, 0): [
        ("11.props.parked-motorcycle__p01", "Parked Motorcycle on Chilly Shore", "Parked Bike by the Sea", "P3", 1.40, 0.22, 0.87, 0.28, "bike_chassis"),
        ("11.props.ruin__p02", "Weathered Shore Chapel Stones", "Arrival on the Chilly Shore", "P4", 2.40, 0.52, 0.86, 0.44, "portal_aperture"),
        ("11.hero.clocktower__p02", "Distant Shore Sanctuary Tower", "Ruined Shore Threshold", "P4", 2.48, 0.78, 0.85, 0.48, "portal_aperture"),
    ],
    (11, 1): [
        ("11.props.ruin__p03", "Sunlit Ruin Archway Stone", "Sunlit Ruin Stones", "P4", 2.44, 0.24, 0.86, 0.44, "portal_aperture"),
        ("11.props.temple.states__p01", "Rising White Marble Foundation", "First Courses of Stone", "P4", 2.38, 0.52, 0.86, 0.48, "drawer_slide"),
        ("11.fx.light__p01", "Morning Sun Breaking Through Fog", "Remnants in the Sunlight", "P5", 3.60, 0.78, 0.28, 0.22, "sun_pulse"),
    ],
    (11, 2): [
        ("11.props.temple.whole__p04", "Left Rising Fluted Marble Column", "Rising Temple Columns", "P4", 2.42, 0.24, 0.85, 0.48, "portal_aperture"),
        ("11.props.temple.states__p04", "Self-Building White Temple Nave", "The Temple Builds Itself", "P4", 2.40, 0.52, 0.85, 0.52, "portal_aperture"),
        ("11.props.temple.arrival.roof-finial__p05", "Crowning White Marble Finial", "Crowning the White Roof", "P4", 2.38, 0.78, 0.72, 0.34, "sun_pulse"),
    ],
    (11, 3): [
        ("11.props.temple.whole__p20", "Completed White Temple Colonnade", "Completed Temple Nave", "P4", 2.44, 0.24, 0.85, 0.50, "portal_aperture"),
        ("11.props.inlays-lantern__p04", "Hanging Sanctuary Brass Lantern", "Choir Chords in the Nave", "P3", 1.40, 0.52, 0.74, 0.28, "lamp_glow"),
        ("11.hero.clocktower__p01", "White Sanctuary Bell & Clocktower", "Sanctuary Bell Tower", "P4", 2.46, 0.78, 0.85, 0.54, "portal_aperture"),
    ],
    (11, 4): [
        ("11.set.mirror_hall__p03", "Tall Hall of Mirrors Arch", "The Lonely Mirror", "P4", 2.42, 0.24, 0.85, 0.48, "portal_aperture"),
        ("11.props.journal__p01", "Open Leather Journal on Lectern", "Open Journal Pages", "P3", 1.38, 0.52, 0.84, 0.24, "lamp_glow"),
        ("11.hero.pools__p04", "Glassy Temple Infinity Pool Arch", "Infinity Pool Reflection", "P4", 2.36, 0.78, 0.86, 0.48, "wave_far"),
    ],
    (11, 5): [
        ("11.hero.pools__p04", "Reflecting Pool Threshold", "Reflecting Pool Steps", "P4", 2.38, 0.24, 0.86, 0.48, "wave_mid"),
        ("11.props.temple.whole__p20", "White Temple Glowing by the Sea", "Walking on Calm Water", "P4", 2.42, 0.52, 0.85, 0.50, "portal_aperture"),
        ("11.fx.light__p05", "Golden Dawn Shaft Over the Sea", "Welcoming the New Day", "P1", 0.45, 0.78, 0.52, 0.28, "light_ray"),
    ],

    # POEM 12 · REUNION
    (12, 0): [
        ("12.props.niche-porch__p01", "Arched White Temple Porch", "Temple Porch Entrance", "P4", 2.44, 0.22, 0.85, 0.52, "portal_aperture"),
        ("12.set.temple_hall__p04", "Sunlit White Temple Hall Column", "Welcome Home in the Hall", "P4", 2.40, 0.52, 0.85, 0.48, "portal_aperture"),
        ("12.props.reunion__p01", "Gathering Table of Friends", "Table of Reunion", "P3", 1.42, 0.78, 0.86, 0.28, "lamp_glow"),
    ],
    (12, 1): [
        ("12.set.temple_hall__p05", "Echoing Marble Colonnade", "Echoing Hall Columns", "P4", 2.44, 0.24, 0.85, 0.48, "portal_aperture"),
        ("04.props.heart__p01", "Overheard Beating Hearts in Chorus", "Overheard Hearts", "P3", 1.36, 0.52, 0.76, 0.14, "heart_beat"),
        ("12.props.reunion__p02", "Warm Banquet Bench", "Hall Gathering Bench", "P3", 1.42, 0.78, 0.86, 0.28, "lamp_base"),
    ],
    (12, 2): [
        ("12.set.temple_backroom__p02", "Quiet Afterlife Backroom Arch", "Quiet Backroom Threshold", "P4", 2.44, 0.24, 0.85, 0.48, "portal_aperture"),
        ("12.set.temple_backroom__p04", "Sunlit Empty Afterlife Chamber", "Empty Rooms of the Afterlife", "P4", 2.40, 0.52, 0.85, 0.48, "portal_inner_world"),
        ("12.props.niche-porch__p02", "Carved Wall Sanctuary Niche", "Memory Wall Niche", "P4", 2.38, 0.78, 0.84, 0.48, "lamp_glow"),
    ],
    (12, 3): [
        ("12.props.hand-hourglass__p01", "Handheld Glass Hourglass", "Handheld Hourglass", "P3", 1.38, 0.24, 0.80, 0.20, "hourglass_sand"),
        ("12.props.last-hourglass__p01", "Burning Wooden Hourglass Stand", "The Burning Hourglasses", "P3", 1.36, 0.52, 0.85, 0.26, "hourglass_sand"),
        ("12.props.snapshot__p03", "Framed Archival Group Photograph", "The Group Photo Reenactment", "P3", 1.40, 0.78, 0.78, 0.24, "portal_tv_flicker"),
    ],
    (12, 4): [
        ("12.set.temple_grove__p03", "Western Grove Cypress Tree", "Western Forest Edge", "P4", 2.44, 0.22, 0.86, 0.50, "flower_bloom"),
        ("12.set.temple_grove__p05", "Central Sanctuary Grove Pine", "Trees at the Forest Edge", "P4", 2.40, 0.52, 0.86, 0.52, "curtain_sway_L"),
        ("12.fx.words-wind__p07", "Wind-Parting Poetic Script", "Where the Winds Part", "P1", 0.48, 0.78, 0.64, 0.24, "cloud_drift_L"),
    ],
    (12, 5): [
        ("12.set.temple_shore_terrace__p07", "West Shore Terrace Pillar", "Shore Terrace Balustrade", "P4", 2.42, 0.22, 0.86, 0.46, "portal_aperture"),
        ("12.props.reunion__p04", "Locked-Arms Brotherhood Arch", "The Brotherhood Chain", "P3", 1.40, 0.52, 0.86, 0.34, "heart_beat"),
        ("12.set.temple_shore_terrace__p10", "East Terrace Overlooking the Sea", "Terrace Overlooking Dusk", "P4", 2.42, 0.78, 0.86, 0.46, "wave_far"),
    ],
    (12, 6): [
        ("12.set.temple_grove__p06", "Open Dusk Meadow Grove", "Football in the Meadow", "P4", 2.38, 0.24, 0.86, 0.46, "curtain_sway_R"),
        ("12.props.niche-porch__p01", "Illuminated Temple Home Portal", "Recollections Bring Us Home", "P4", 2.42, 0.52, 0.85, 0.52, "portal_aperture"),
        ("12.props.last-hourglass__p02", "Stilled Glass Hourglass at Peace", "Time at Rest", "P3", 1.38, 0.78, 0.84, 0.22, "lamp_glow"),
    ],

    # POEM 13 · HOW TO WIN MY HEART
    (13, 0): [
        ("13.props.rail-tide-awning__p03", "Harbor Cafe Striped Pillar", "Harbor Cafe Awning", "P4", 2.42, 0.22, 0.85, 0.48, "curtain_sway_L"),
        ("13.props.cafe__p01", "Corner Marble Bistro Table & Cup", "The Corner Cafe Table", "P3", 1.42, 0.52, 0.86, 0.22, "coffee_steam"),
        ("13.hero.cafe__p01", "Harbor Cafe Facade & Windows", "Cafe Window Promenade", "P4", 2.46, 0.78, 0.85, 0.52, "portal_aperture"),
    ],
    (13, 1): [
        ("11.props.temple.whole__p20", "White Temple on the Point", "Leaving the White Temple", "P4", 2.48, 0.22, 0.85, 0.48, "portal_aperture"),
        ("13.hero.atrium__p01", "Curving Harbor Quay Colonnade", "Walk Around the Harbor", "P4", 2.38, 0.52, 0.85, 0.50, "fire_escape_landing"),
        ("13.props.planet-boats__p06", "Harbor Sailboat & Jupiter Orbit", "Sailboats on the Tide", "P3", 1.46, 0.78, 0.82, 0.18, "boat_rock"),
    ],
    (13, 2): [
        ("13.props.planet-boats__p01", "Jupiter & Counted Orbits in Sky", "Counted Planetary Orbits", "P5", 3.65, 0.24, 0.28, 0.22, "planet_orbit"),
        ("13.set.church_pews__p02", "Carved Wooden Pews of Elders", "Praying Elders in the Pews", "P3", 1.44, 0.52, 0.87, 0.36, "lamp_glow"),
        ("13.hero.atrium__p03", "Sunlit Harbor Atrium Arch", "Younger Selves Colonnade", "P4", 2.44, 0.78, 0.85, 0.46, "portal_aperture"),
    ],
    (13, 3): [
        ("13.set.drowned_atrium__p01", "Half-Submerged Atrium Columns", "Drowned Atrium of Seasons", "P4", 2.44, 0.24, 0.85, 0.50, "wave_far"),
        ("13.props.five-letters__p01", "Five Unsent Letters Drifting", "Burned Stories & Five Letters", "P3", 1.38, 0.52, 0.78, 0.16, "tambourine_arc"),
        ("13.set.drowned_atrium__p03", "Weathered Floodgate Arch", "The Floodgate Weir", "P4", 2.46, 0.78, 0.85, 0.46, "wave_mid"),
    ],
    (13, 4): [
        ("04.props.faith-blooms__p03", "Golden Poppy & Blossom Cluster West", "Western Poppy Meadow", "P3", 1.38, 0.24, 0.86, 0.20, "flower_bloom"),
        ("04.props.faith-blooms__p07", "Harvested Golden Poppy Flowerhead", "Harvesting the Poppies", "P3", 1.34, 0.52, 0.84, 0.16, "flower_bloom"),
        ("04.props.faith-blooms__p04", "Blossoming Hilltop Poppies East", "Harvested Power Ridge", "P3", 1.38, 0.78, 0.86, 0.20, "flower_bloom"),
    ],
    (13, 5): [
        ("13.props.cafe__p03", "Empty Bentwood Bistro Chair", "Empty Chair at Dusk", "P3", 1.44, 0.24, 0.88, 0.34, "cafe_chair"),
        ("13.props.distant-window__p01", "Upper Harbor Window & Curtains", "From a Distant Window", "P4", 2.42, 0.54, 0.80, 0.52, "portal_aperture"),
        ("13.props.distant-window__p02", "Warm Candlelit Sill Above Quay", "Watching From Upstairs", "P4", 2.38, 0.78, 0.80, 0.46, "curtain_sway_R"),
    ],
    (13, 6): [
        ("13.props.cafe__p01", "Bistro Table & Paid Check", "Rising From the Table", "P3", 1.42, 0.22, 0.86, 0.22, "coffee_steam"),
        ("13.set.harbor_quay_night_fire__p02", "Night Harbor Quay Watchfire Torch", "Walks the Night Harbor", "P3", 1.40, 0.52, 0.85, 0.28, "lamp_glow"),
        ("13.props.planet-boats__p06", "Night Sailboat Heading Out", "Harbor Lantern Horizon", "P3", 1.46, 0.78, 0.82, 0.18, "boat_rock"),
    ],

    # POEM 14 · HOT MINUTE
    (14, 0): [
        ("14.set.harbor_atlantis_wide__p06", "Panoramic Harbor Lighthouse", "Everything I Built", "P4", 2.46, 0.24, 0.85, 0.46, "water_backing"),
        ("01.fx.haze-words__p01", "Rising Golden Haze Column", "Taken by the Haze", "P1", 0.48, 0.52, 0.68, 0.26, "cloud_drift_L"),
        ("14.set.harbor_atlantis_wide__p04", "Distant Temple & Causeway", "The Whole Harbor Horizon", "P4", 2.44, 0.78, 0.85, 0.48, "portal_aperture"),
    ],
    (14, 1): [
        ("14.props.reel__p06", "Candle Memory in the Void", "The Weightless Black", "P3", 1.42, 0.24, 0.76, 0.22, "lamp_glow"),
        ("14.props.reel__p05", "Floating Star Memory Shard", "Floating in the Black", "P3", 1.40, 0.52, 0.66, 0.18, "sun_pulse"),
        ("14.props.door__p02", "Distant Freestanding Door Silhouette", "No Walls Around Us", "P4", 2.46, 0.78, 0.85, 0.50, "portal_aperture"),
    ],
    (14, 2): [
        ("14.props.reel__p02", "Memory Frame 01 · High-Rise Window", "High-Rise Window Memory", "P3", 1.42, 0.22, 0.74, 0.24, "portal_tv_flicker"),
        ("14.set.broll_life__p04", "Panoramic B-Roll Frame of Life", "Highs and Lows of Life", "P4", 2.42, 0.52, 0.80, 0.46, "portal_other_world"),
        ("14.props.reel__p03", "Memory Frame 02 · The Tambourine", "Tambourine & Shore Memory", "P3", 1.42, 0.78, 0.74, 0.24, "tambourine_arc"),
    ],
    (14, 3): [
        ("14.fx.filmframe__p01", "Perforated 35mm Graytone Film Frame", "Graytone Film Aperture", "P4", 2.42, 0.24, 0.78, 0.44, "portal_tv_flicker"),
        ("14.props.reel__p01", "Unspooling Nine-Frame Memory Reel", "Battle Scars & The Reel", "P3", 1.38, 0.52, 0.80, 0.28, "wheel_spin"),
        ("14.props.reel__p04", "Memory Frame 03 · Poppy Field", "Poppy Field Recollection", "P3", 1.42, 0.78, 0.76, 0.22, "flower_bloom"),
    ],
    (14, 4): [
        ("14.fx.filmframe__p02", "Dissolving Celluloid Frame", "Edge of the Reel", "P4", 2.44, 0.22, 0.80, 0.44, "portal_other_world"),
        ("14.props.door__p01", "Freestanding Panelled Vintage Door", "The Vintage Door Appears", "P4", 2.40, 0.54, 0.86, 0.56, "portal_aperture"),
        ("14.set.vintage_party__p03", "Warm 1940s Ballroom Beyond Door", "Golden Light Beyond the Threshold", "P4", 2.58, 0.78, 0.85, 0.50, "portal_other_world"),
    ],
    (14, 5): [
        ("01.props.chandeliers__p01", "Sparkling Ballroom Chandelier", "Under the Crystal Chandelier", "P3", 1.48, 0.24, 0.34, 0.24, "chandelier_sway"),
        ("14.set.vintage_party__p03", "1940s Grand Ballroom Archway", "The Dance at the Vintage Party", "P4", 2.44, 0.52, 0.85, 0.52, "portal_other_world"),
        ("14.props.party__p01", "Champagne Table & Ballroom Arch", "Two Entwined Muses", "P3", 1.42, 0.78, 0.86, 0.30, "lamp_glow"),
    ],
    (14, 6): [
        ("14.props.party__p03", "Warm Ballroom Crowd Table", "Into the Ballroom Crowd", "P3", 1.44, 0.24, 0.86, 0.28, "lamp_glow"),
        ("14.props.door__p01", "Closing Panelled Vintage Doorway", "The Vintage Door Closes", "P4", 2.40, 0.54, 0.86, 0.56, "portal_aperture"),
        ("01.props.window__p01", "Quiet Bedroom Window at Dawn", "Genesis · Back to the Beginning", "P4", 2.44, 0.80, 0.84, 0.52, "portal_aperture"),
    ],
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
) -> None:
    """
    Renders a clean, high-legibility 1280x720 WebP scene plate for the shelf
    thumbnail and preview:
      - Uses the painted Atlantis world backdrop (`shots/world/<id>/backdrop.webp`)
      - Adds a grounded architectural stage floor below `floor_y`
      - Composites the scene's die-cut `P5`, `P4`, and `P3` architectural/prop
        stations at their calibrated physical scales.
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

    odraw.line([(0, fy), (W, fy)], fill=(r_g, g_g, b_g, 96), width=2)
    for px_frac in (0.15, 0.32, 0.50, 0.68, 0.85):
        top_x = int(W * px_frac)
        bot_x = int(W * 0.5 + (top_x - W * 0.5) * 1.35)
        odraw.line([(top_x, fy), (bot_x, H)], fill=(255, 255, 255, 18), width=1)

    canvas = Image.alpha_composite(canvas, overlay)

    # Composite P5, P4, and P3 die-cut structures & station props
    draw_layers = [
        l for l in layers
        if l.get("plane") in ("P5", "P4", "P3") and not str(l.get("role", "")).startswith("character")
    ]
    draw_layers.sort(key=lambda item: float(item.get("z", 1.4)), reverse=True)

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
        sc = float(lyr.get("scale", 0.42))
        target_h = max(28, min(int(H * 0.72), int(round(H * sc))))
        target_w = max(28, int(round(target_h * (pw / float(ph)))))
        if target_w > int(W * 0.68):
            ratio = (W * 0.68) / float(target_w)
            target_w = int(W * 0.68)
            target_h = max(24, int(round(target_h * ratio)))

        p_resized = p_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
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
    canvas.convert("RGB").save(out_webp, "WEBP", quality=88, method=4)


def main() -> None:
    print("[1/4] Loading scene_collage_plans.json and wygwyl_atlas_manifest.json...")
    plans_data = json.loads(PLANS_PATH.read_text())
    manifest = json.loads(MANIFEST_PATH.read_text())

    plans_by_poem: Dict[int, List[Dict[str, Any]]] = {}
    for sc in plans_data["scenes"]:
        plans_by_poem.setdefault(int(sc["book"]), []).append(sc)

    parts_by_id: Dict[str, Dict[str, Any]] = {}
    sheet_by_part: Dict[str, Dict[str, Any]] = {}
    for asset in manifest["assets"]:
        for pt in asset.get("parts", []):
            parts_by_id[pt["id"]] = pt
            sheet_by_part[pt["id"]] = asset

    # Cache alpha opacity ratios so we can filter out rectangular strip bars
    alpha_cache: Dict[str, Tuple[float, float]] = {}
    def get_ar_op(pid: str) -> Tuple[float, float]:
        if pid not in alpha_cache:
            pt = parts_by_id.get(pid)
            alpha_cache[pid] = compute_opaque_ratio(SHOTS_DIR / pt["file"]) if pt else (1.0, 1.0)
        return alpha_cache[pid]

    total_scenes_updated = 0
    total_plates_rendered = 0
    total_layers_embedded = 0

    print("[2/4] Building purified multiplane architectural levels & re-rendering 90 clean scene plates...")
    for poem_num in range(1, 15):
        num_str = f"{poem_num:02d}"
        lv_path = LEVELS_DIR / num_str / "level.json"
        lv = json.loads(lv_path.read_text())
        p_plans = plans_by_poem.get(poem_num, [])
        fw, fh = int(lv["frame"][0]), int(lv["frame"][1])

        for sc_idx, sc in enumerate(lv["scenes"]):
            plan = p_plans[min(sc_idx, len(p_plans) - 1)]
            wb = plan["world_backdrop"]
            ap = plan["archive_plate"]

            backdrop_shots_rel = wb["backdrop_file"]
            backdrop_play_rel = f"../{backdrop_shots_rel}"
            poster_shots_rel = ap.get("poster_file", "cel_assets/posters/P01-001.jpg")
            poster_play_rel = f"../{poster_shots_rel}"

            combined_layers: List[Dict[str, Any]] = []
            seen_part_positions = set()
            active_sheet_prefixes = set()

            enrichments = SCENE_STATION_ENRICHMENTS.get((poem_num, sc_idx), [])
            stations: List[Dict[str, Any]] = []

            for e_idx, (pid, lbl, st_title, plane, z, x, y, scale, anim_role) in enumerate(enrichments):
                pt = parts_by_id.get(pid)
                if not pt:
                    continue
                shots_file = pt["file"]
                play_file = f"../{shots_file}"
                key_sig = (pid, round(x, 2))
                seen_part_positions.add(key_sig)
                active_sheet_prefixes.add(pid.split("__")[0])

                station_id = f"st_{num_str}_{sc_idx}_{e_idx}"
                lyr_obj = {
                    "id": f"lyr_{num_str}_{sc_idx}_{e_idx}_{pid.split('__')[-1]}",
                    "part_id": pid,
                    "sheet_id": sheet_by_part[pid]["id"],
                    "label": lbl,
                    "station_id": station_id,
                    "station_title": st_title,
                    "plane": plane,
                    "z": round(float(z), 2),
                    "x": round(float(x), 3),
                    "y": round(float(y), 3),
                    "scale": round(float(scale), 4),
                    "width": int(pt.get("width", 240)),
                    "height": int(pt.get("height", 240)),
                    "role": "station_arch" if plane == "P4" else ("station_horizon" if plane == "P5" else "station_prop"),
                    "anim_role": anim_role,
                    "alpha": 0.98,
                    "file": play_file,
                    "shots_file": shots_file,
                }
                combined_layers.append(lyr_obj)

                if 0.14 <= x <= 0.88:
                    stations.append({
                        "id": station_id,
                        "title": st_title,
                        "part_label": lbl,
                        "part_id": pid,
                        "plane": plane,
                        "x": round(float(x), 3),
                        "mx": round(float(x) * fw, 1),
                        "y": round(float(y), 3),
                        "anim_role": anim_role,
                    })

            # Add ONLY co-located kinetic subparts (wheels, platters, table stem/cup,hourglass bulbs/sand, shore foam)
            # that belong to the scene's active ensembles and are NOT rectangular backing bars or generic portals
            ALLOWED_SUBPART_SHEETS = {
                "02.props.car", "10.props.bike-skeleton", "07.props.dj-decks",
                "09.props.phonebooth", "09.props.phones-chair", "13.props.cafe",
                "13.props.personal", "12.props.last-hourglass", "04.props.heart",
                "04.set.shore_night"
            }
            for p_idx, pl in enumerate(plan.get("staged_placements", [])):
                role = str(pl.get("role", ""))
                if role.startswith("character") or pl.get("plane") == "P2":
                    continue
                pid = pl["part_id"]
                sh_prefix = pid.split("__")[0]
                if sh_prefix not in ALLOWED_SUBPART_SHEETS:
                    continue
                # Only include vehicle/table/booth/dj subparts if that ensemble is actually in this scene
                if sh_prefix != "04.set.shore_night" and sh_prefix not in active_sheet_prefixes:
                    continue
                ar, op = get_ar_op(pid)
                if ar > 2.2 and op > 0.78:
                    continue
                # Skip wide wave bars (WAVE.1/WAVE.2 are 1496x158 bars); keep WAVE.3 (`p03`, 478x79)
                if sh_prefix == "04.set.shore_night" and not pid.endswith("__p03"):
                    continue

                x = float(pl.get("x", 0.5))
                key_sig = (pid, round(x, 2))
                if key_sig in seen_part_positions:
                    continue
                seen_part_positions.add(key_sig)

                shots_file = pl["file"]
                play_file = f"../{shots_file}"
                combined_layers.append({
                    "id": f"sub_{num_str}_{sc_idx}_{p_idx}_{pid.split('__')[-1]}",
                    "part_id": pid,
                    "sheet_id": sh_prefix,
                    "label": pl.get("label", pid),
                    "station_id": stations[1]["id"] if len(stations) > 1 else (stations[0]["id"] if stations else ""),
                    "station_title": pl.get("label", pid),
                    "plane": pl.get("plane", "P3"),
                    "z": round(float(pl.get("z", 1.36)), 2),
                    "x": round(x, 3),
                    "y": round(float(pl.get("y", 0.86)), 3),
                    "scale": round(float(pl.get("scale", 0.16)), 4),
                    "width": int(pl.get("width", 240)),
                    "height": int(pl.get("height", 240)),
                    "role": role or "prop_subpart",
                    "anim_role": pl.get("anim_role", "static"),
                    "alpha": round(float(pl.get("alpha", 0.96)), 3),
                    "file": play_file,
                    "shots_file": shots_file,
                })

            combined_layers.sort(key=lambda item: float(item.get("z", 1.4)), reverse=True)
            total_layers_embedded += len(combined_layers)

            stations.sort(key=lambda s: s["x"])
            distinct_stations: List[Dict[str, Any]] = []
            for st in stations:
                if not distinct_stations or abs(st["x"] - distinct_stations[-1]["x"]) >= 0.14:
                    distinct_stations.append(st)

            n_st = len(distinct_stations)
            station_order = [0, 1, 2, 1] if n_st >= 3 else list(range(n_st))
            for l_idx, ln in enumerate(sc.get("lines", [])):
                st_pick = distinct_stations[station_order[l_idx % len(station_order)] % n_st]
                jitter = ((l_idx % 3) - 1) * 22.0
                ln["mx"] = round(max(160.0, min(fw - 160.0, float(st_pick["mx"]) + jitter)), 1)
                ln["station_id"] = st_pick["id"]
                ln["station_label"] = st_pick["title"]
                ln["station_part_label"] = st_pick["part_label"]
                ln["station_anim"] = st_pick["anim_role"]

            sc["floor"] = max(575, min(635, int(sc.get("floor", 610))))
            sc["plan_id"] = plan["id"]
            sc["set_name"] = plan.get("set_name", sc["name"])
            sc["camera_framing"] = plan.get("camera_framing", "medium_wide")
            sc["district_name"] = wb.get("district_name", "Atlantis")
            sc["palette_glow"] = wb.get("palette_glow", ["#d8ab4f"])
            sc["backdrop_file"] = backdrop_play_rel
            sc["archive_poster"] = poster_play_rel
            sc["world_planes"] = [
                {
                    "file": f"../{wp['file']}",
                    "plane": wp["plane"],
                    "z": wp["z"],
                    "label": wp["label"],
                }
                for wp in wb.get("multiplane_sheets", [])
            ]
            sc["stations"] = distinct_stations
            sc["multiplane_layers"] = [
                {k: v for k, v in lyr.items() if k != "shots_file"}
                for lyr in combined_layers
            ]

            out_webp = LEVELS_DIR / num_str / sc["img"]
            render_clean_scene_plate(
                out_webp=out_webp,
                backdrop_path=SHOTS_DIR / backdrop_shots_rel,
                floor_y=sc["floor"],
                layers=combined_layers,
                district_glow=sc["palette_glow"],
            )
            total_plates_rendered += 1
            total_scenes_updated += 1

        lv_path.write_text(json.dumps(lv, separators=(",", ":")))
        print(f"  Poem {num_str} ({lv['title']}): updated {len(lv['scenes'])} scenes with purified die-cut structures")

    # -----------------------------------------------------------------------
    # [3/4] Build Purified `shots/play/level_assets_catalog.json`
    # -----------------------------------------------------------------------
    print("[3/4] Building purified shots/play/level_assets_catalog.json (zero rectangular strip bars)...")
    catalog_items: List[Dict[str, Any]] = []
    for asset in manifest["assets"]:
        aid = asset["id"]
        akind = asset.get("kind", "")
        if not (
            akind in ("set", "hero", "hero-continuation", "props", "fx", "environment", "world", "other")
            or ".set." in aid or ".props." in aid or ".hero." in aid or ".fx." in aid
        ):
            continue
        if ".body" in aid or "compact-core" in aid or "torso-parts" in aid:
            continue

        poem_prefix = int(aid[:2]) if aid[:2].isdigit() else 0
        parts = asset.get("parts", [])
        sorted_parts = sorted(parts, key=lambda p: int(p.get("area_px", int(p.get("width", 1)) * int(p.get("height", 1)))), reverse=True)

        kept_for_sheet = 0
        for pt in sorted_parts:
            if kept_for_sheet >= 6:
                break
            pid = pt["id"]
            w = int(pt.get("width", 200))
            h = int(pt.get("height", 200))
            if w < 42 or h < 42:
                continue
            ar, op = get_ar_op(pid)
            # Filter out wide solid rectangular strip cards
            if (ar > 2.2 and op > 0.79) or op > 0.93:
                continue

            kept_for_sheet += 1
            if ".set." in aid or ".hero." in aid:
                plane = "P4"
                z = 2.40
                default_scale = 0.48
                cat = "architecture"
                anim_role = "portal_aperture"
            elif ".fx." in aid:
                plane = "P1"
                z = 0.48
                default_scale = 0.24
                cat = "atmosphere_fx"
                anim_role = "light_ray"
            else:
                plane = "P3"
                z = 1.40
                default_scale = 0.26 if max(w, h) >= 240 else 0.16
                cat = "props_furniture"
                anim_role = "lamp_glow"

            raw_lbl = pt.get("label", "") or f"{aid} · {pid.split('__')[-1]}"
            catalog_items.append({
                "part_id": pid,
                "sheet_id": aid,
                "poem": poem_prefix,
                "category": cat,
                "label": raw_lbl[:65],
                "file": f"../{pt['file']}",
                "width": w,
                "height": h,
                "plane": plane,
                "z": z,
                "default_scale": default_scale,
                "anim_role": anim_role,
            })

    CATALOG_OUT_PATH.write_text(json.dumps({
        "version": "2.1",
        "count": len(catalog_items),
        "items": catalog_items,
    }, separators=(",", ":")))
    print(f"  Wrote {CATALOG_OUT_PATH} ({len(catalog_items)} purified die-cut architectural & prop pieces)")
    print(f"[4/4] DONE! Updated {total_scenes_updated} scenes, embedded {total_layers_embedded} purified multiplane layers, and rendered {total_plates_rendered} clean WebP scene plates.")


if __name__ == "__main__":
    main()
