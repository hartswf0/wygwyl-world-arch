#!/usr/bin/env python3
"""
build_scene_collage_scales.py
=============================
Multiplane Set Architecture, Archive/World Layer Collage & Scene Scale Solver
for the WYGWYL Cut-Out Animation Suite (Poems 01–14, 80 Scenes, 252 Shots).

Generates:
  shots/arena/parts/kit3/release_v2/scene_collage_plans.json

Key responsibilities:
  1. Classify all 6,265 cut pieces in `release_catalog.json` into 15 physical
     semantic classes (`sky_canopy`, `horizon_vista`, `building_facade`,
     `room_wall`, `door_window_arch`, `stair_bridge_viaduct`, `large_furniture`,
     `medium_prop`, `handheld_prop`, `full_figure_adult`, `full_figure_child`,
     `crouched_or_prone_figure`, `limb_or_head_detail`, `atmospheric_fx`,
     `typography_banner`) with ground-truth `scale_cm` from `poems/dossier/01..14.json`.
  2. Solve true scene scale & camera framing (`extreme_wide`, `wide`,
     `medium_wide`, `medium`, `close`) for all 80 scenes (`P01-S01`..`P14-S06`).
  3. Compute physically grounded stage scales (`scale` = fraction of stage height `sh`,
     `y` = bottom anchor `0..1`, `x` = horizontal center `0..1`) across multiplane
     depths `P6 (Z=6.0)`, `P5 (Z=3.8)`, `P4 (Z=2.4)`, `P3 (Z=1.4)`, `P2 (Z=1.0)`,
     and `P1/P0 (Z=0.45)`:
       - Handheld props (`vape_pen`, `tambourine`, `coin`, `coffee_cup`, `heart`,
         `phone`, `letters`, `rings`) are strictly scaled to `0.09–0.14` (9–14% of
         stage height) and pinned near the active actor's hand (`actor_x ± 0.06`,
         `y: 0.64`), never 34% on the floor.
       - Supporting & hero cast on `P2 (Z=1.0)` strictly use full-figure pose cards
         or complete multi-part rigs (`full_figure_adult`: `0.52–0.60`,
         `full_figure_child`: `0.36–0.40`, `crouched_or_prone_figure`: `0.26–0.38`
         with aspect-ratio compensation), eliminating detached headless torso vests.
       - Segmented architecture on `P4 (Z=2.4)` (`0.58–0.78`, `y: 0.86–0.92`) is
         distributed across left/center/right (`x: 0.18, 0.50, 0.82`) to frame the
         center acting lane rather than burying it.
  4. Integrate World & Weave Multiplane Backdrops (`world_backdrop`), Prelinger /
     Archive Found-Footage Plates (`archive_plate`), and 24-minute master audio
     windows (`audio_window` within `[0, 1440.072]`) into every scene.
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
        "scale_range": [0.72, 0.90],
        "default_scale": 0.82,
        "y_range": [0.78, 0.84],
        "default_y": 0.81,
        "scale_cm": 800,
        "description": "Skyline strips, distant ridges, sea horizons, city void tower vistas",
    },
    "building_facade": {
        "plane": "P4",
        "z": 2.4,
        "scale_range": [0.58, 0.78],
        "default_scale": 0.68,
        "y_range": [0.86, 0.92],
        "default_y": 0.88,
        "scale_cm": 450,
        "description": "Exterior walls, market stalls, church naves, tower slabs, plaza colonnades",
    },
    "room_wall": {
        "plane": "P4",
        "z": 2.4,
        "scale_range": [0.60, 0.78],
        "default_scale": 0.70,
        "y_range": [0.86, 0.92],
        "default_y": 0.89,
        "scale_cm": 320,
        "description": "Bedroom walls, hallways, apartment interiors, elevator shafts, temple halls",
    },
    "door_window_arch": {
        "plane": "P4",
        "z": 2.4,
        "scale_range": [0.58, 0.74],
        "default_scale": 0.62,
        "y_range": [0.86, 0.92],
        "default_y": 0.88,
        "scale_cm": 210,
        "description": "Sash windows, fire-escape frames, arches, gates, doorways, large wall mirrors",
    },
    "stair_bridge_viaduct": {
        "plane": "P4",
        "z": 2.4,
        "scale_range": [0.58, 0.76],
        "default_scale": 0.64,
        "y_range": [0.86, 0.92],
        "default_y": 0.90,
        "scale_cm": 380,
        "description": "Fire escapes, spiral stairs, stone steps, aqueduct bridges, escalators, catwalks",
    },
    "large_furniture": {
        "plane": "P3",
        "z": 1.4,
        "scale_range": [0.34, 0.44],
        "default_scale": 0.38,
        "y_range": [0.87, 0.90],
        "default_y": 0.88,
        "scale_cm": 180,
        "description": "Beds, dressers, pews, consoles, DJ booths, tables, benches, cars, motorcycles, phone booths",
    },
    "medium_prop": {
        "plane": "P3",
        "z": 1.4,
        "scale_range": [0.18, 0.26],
        "default_scale": 0.22,
        "y_range": [0.84, 0.88],
        "default_y": 0.86,
        "scale_cm": 75,
        "description": "Suitcases, TVs, chairs, lamps, flower pots, crates, screens, ice basins, hourglasses",
    },
    "handheld_prop": {
        "plane": "P3",
        "z": 1.4,
        "scale_range": [0.09, 0.14],
        "default_scale": 0.11,
        "y_range": [0.60, 0.68],
        "default_y": 0.64,
        "scale_cm": 18,
        "description": "Vape pens, ember dots, phones, tambourines, coffee cups, coins, letters/poems, rings, keys, bread/fruit",
    },
    "full_figure_adult": {
        "plane": "P2",
        "z": 1.0,
        "scale_range": [0.52, 0.60],
        "default_scale": 0.55,
        "y_range": [0.89, 0.93],
        "default_y": 0.91,
        "scale_cm": 175,
        "description": "Standing, walking, or dancing full-body adult characters",
    },
    "full_figure_child": {
        "plane": "P2",
        "z": 1.0,
        "scale_range": [0.36, 0.40],
        "default_scale": 0.38,
        "y_range": [0.89, 0.93],
        "default_y": 0.91,
        "scale_cm": 120,
        "description": "Young Poet, Ghost Child, Child Traveler (~0.68x adult height)",
    },
    "crouched_or_prone_figure": {
        "plane": "P2",
        "z": 1.0,
        "scale_range": [0.26, 0.38],
        "default_scale": 0.32,
        "y_range": [0.88, 0.93],
        "default_y": 0.91,
        "scale_cm": 105,
        "description": "Crouching, sitting, kneeling, or horizontally falling figures (height compensated by w/h aspect ratio)",
    },
    "limb_or_head_detail": {
        "plane": "P2",
        "z": 1.0,
        "scale_range": [0.11, 0.24],
        "default_scale": 0.16,
        "y_range": [0.58, 0.78],
        "default_y": 0.66,
        "scale_cm": 28,
        "description": "Detached hands, arms, heads, eyes, torso parts (only used in close-ups or inside assembled multi-part rigs)",
    },
    "atmospheric_fx": {
        "plane": "P1",
        "z": 0.45,
        "scale_range": [0.24, 0.38],
        "default_scale": 0.30,
        "y_range": [0.32, 0.92],
        "default_y": 0.68,
        "scale_cm": 140,
        "description": "Smoke plumes, light leaks, rain streaks, ink floods, embers, water ripples, shadow pools",
    },
    "typography_banner": {
        "plane": "P1",
        "z": 0.45,
        "scale_range": [0.24, 0.36],
        "default_scale": 0.28,
        "y_range": [0.28, 0.76],
        "default_y": 0.44,
        "scale_cm": 90,
        "description": "Falling word dashes, neon signs, street banners, star nameplates, film-frame apertures",
    },
}

CAMERA_FRAMING_SPECS: Dict[str, Dict[str, Any]] = {
    "extreme_wide": {
        "actor_mult": 0.96,
        "prop_mult": 0.92,
        "arch_mult": 0.94,
        "focal_length_mm": 21,
        "description": "Architectural / landscape dominance; full vista and multiplane set breathe around figures",
    },
    "wide": {
        "actor_mult": 0.98,
        "prop_mult": 0.96,
        "arch_mult": 0.98,
        "focal_length_mm": 28,
        "description": "Full room or street proscenium; head-to-toe figures grounded in 6-plane set",
    },
    "medium_wide": {
        "actor_mult": 1.00,
        "prop_mult": 1.00,
        "arch_mult": 1.00,
        "focal_length_mm": 35,
        "description": "Canonical stage framing; balanced dialogue between full-body performance and architecture",
    },
    "medium": {
        "actor_mult": 1.04,
        "prop_mult": 1.05,
        "arch_mult": 1.04,
        "focal_length_mm": 50,
        "description": "Intimate two-shot or gesture focus; closer presence while preserving full-figure grounding",
    },
    "close": {
        "actor_mult": 1.08,
        "prop_mult": 1.12,
        "arch_mult": 1.06,
        "focal_length_mm": 75,
        "description": "Tactile/emotional focus; foreground hands, props, and faces read clearly against deeper planes",
    },
}


# ---------------------------------------------------------------------------
# 2. Explicit Sheet-Level & Character Full-Figure Curations
# ---------------------------------------------------------------------------

HANDHELD_PROP_SHEETS: Dict[str, Tuple[int, float]] = {
    "01.props.handheld": (16, 0.11),
    "02.props.tambourine": (25, 0.12),
    "03.props.tambourine-broken": (15, 0.10),
    "03.props.gifts-bread-cups": (18, 0.12),
    "04.props.heart": (12, 0.11),
    "04.props.faith-blooms": (16, 0.12),
    "06.props.lantern-candle-guitar": (28, 0.13),
    "07.props.mic-daisy-rings": (18, 0.11),
    "11.props.inlays-lantern": (22, 0.12),
    "11.props.journal": (24, 0.12),
    "12.props.hand-hourglass": (20, 0.12),
    "12.props.snapshot": (15, 0.10),
    "13.props.five-letters": (22, 0.12),
    "13.props.personal": (14, 0.11),
    "14.props.reel": (20, 0.12),
}

LARGE_FURNITURE_PROP_SHEETS: Dict[str, Tuple[int, float]] = {
    "02.props.car": (480, 0.40),
    "07.props.dj-decks": (125, 0.36),
    "09.props.phonebooth": (220, 0.43),
    "10.props.bike-ride-views": (210, 0.38),
    "10.props.bike-skeleton": (210, 0.38),
    "10.props.tree-dawn-sign": (240, 0.42),
    "11.props.parked-motorcycle": (210, 0.38),
    "13.props.cafe": (130, 0.36),
    "13.props.rail-tide-awning": (140, 0.40),
    "07.hero.house.furniture": (160, 0.38),
    "13.set.church_pews": (300, 0.40),
}

DOOR_WINDOW_PROP_SHEETS: Dict[str, Tuple[int, float]] = {
    "01.props.window": (150, 0.62),
    "02.props.window": (150, 0.62),
    "03.props.rose-window": (180, 0.60),
    "12.props.niche-porch": (200, 0.60),
    "13.props.distant-window": (150, 0.58),
    "14.props.door": (210, 0.62),
    "03.set.chapel_side_doors": (220, 0.64),
    "05.set.winged_marble_gate": (320, 0.68),
    "06.set.atlantis_gate": (350, 0.70),
}

BUILDING_PROP_SHEETS: Dict[str, Tuple[int, float]] = {
    "11.props.ruin": (280, 0.62),
    "11.props.temple.arrival.beams": (300, 0.62),
    "11.props.temple.arrival.courses-columns": (300, 0.64),
    "11.props.temple.arrival.roof-finial": (300, 0.60),
    "11.props.temple.states": (320, 0.66),
    "11.props.temple.whole": (320, 0.66),
}

LIMB_DETAIL_PROP_SHEETS: Dict[str, Tuple[int, float]] = {
    "02.props.poet-eye-aperture": (24, 0.22),
    "04.props.poet-jointed-hands": (22, 0.15),
    "05.props.fingerprint": (35, 0.24),
}

TYPOGRAPHY_SHEETS: Dict[str, Tuple[int, float]] = {
    "01.fx.haze-words": (75, 0.28),
    "04.props.word-shore": (85, 0.26),
    "05.props.star-names": (60, 0.25),
    "12.fx.words-wind": (80, 0.28),
    "14.fx.filmframe": (110, 0.32),
}

# Verified full-figure pose cards for every character across all 14 poems.
# Each entry maps to (part_id, semantic_class, rig_id, posture_label).
CURATED_CHARACTER_POSES: Dict[str, List[Tuple[str, str, str, str]]] = {
    "POET_TSHIRT": [
        ("poet.01.main-poses__p01", "full_figure_adult", "poet_black_tshirt", "Poet (Black T-Shirt · P01) · Reading Poem Stand"),
        ("poet.01.main-poses__p02", "full_figure_adult", "poet_black_tshirt", "Poet (Black T-Shirt · P01) · Stepping Toward Window"),
        ("poet.01.main-poses__p03", "full_figure_adult", "poet_black_tshirt", "Poet (Black T-Shirt · P01) · Fire Escape Witness"),
        ("poet.01.main-poses__p04", "crouched_or_prone_figure", "poet_black_tshirt", "Poet (Black T-Shirt · P01) · Falling in City Void"),
        ("poet.02.main-poses__p01", "full_figure_adult", "poet_black_tshirt", "Poet (Poem 02) · Standing Witness"),
        ("poet.02.main-poses__p02", "full_figure_adult", "poet_black_tshirt", "Poet (Poem 02) · Stepping Through Memory"),
        ("poet.02.main-poses__p03", "crouched_or_prone_figure", "poet_black_tshirt", "Poet (Poem 02) · Kneeling by Broken Window"),
        ("poet.03.main-poses__p01", "full_figure_adult", "poet_black_tshirt", "Poet (Poem 03) · Chapel Nave Stand"),
        ("poet.03.main-poses__p02", "full_figure_adult", "poet_black_tshirt", "Poet (Poem 03) · Altar Reach"),
        ("poet.03.main-poses__p03", "crouched_or_prone_figure", "poet_black_tshirt", "Poet (Poem 03) · Kneeling Among Tambourine Shards"),
    ],
    "POET_TRACKSUIT": [
        ("poet.04.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit · P04) · Shore Stand"),
        ("poet.04.main-poses__p02", "crouched_or_prone_figure", "poet_tracksuit_31", "Poet (Tracksuit · P04) · Kneeling Offering Heart"),
        ("poet.05.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit · P05) · Procession Stride"),
        ("poet.06.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit · P06) · Atlantis Plaza Stand"),
        ("poet.07.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit · P07) · Club Crowd Witness"),
        ("poet.08.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit · P08) · Newly Single Stand"),
        ("poet.09.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit · P09) · Phone Booth Stand"),
        ("poet.10.main-poses__p01", "crouched_or_prone_figure", "poet_tracksuit_31", "Poet (Tracksuit · P10) · Motorcycle Rider Pose"),
        ("poet.10.main-poses__p02", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit · P10) · Highway Stand"),
        ("poet.11.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit · P11) · Temple Steps Ascent"),
        ("poet.12.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit · P12) · Temple Hall Stand"),
        ("poet.13.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet (Tracksuit · P13) · Harbor Cafe Stand"),
        ("poet.14.muse-dance__p01", "full_figure_adult", "poet_tracksuit_31", "Poet & Muse (P14) · Waltz Frame A"),
        ("poet.14.exit__p08", "full_figure_adult", "poet_tracksuit_31", "Poet (P14) · Final Doorway Exit"),
        ("poet.red_black_sunglasses.replacements.deep_crouch__p01", "crouched_or_prone_figure", "poet_tracksuit_31", "Poet (Tracksuit) · Deep Crouch Replacement"),
        ("poet.red_black_sunglasses.replacements.falling__p01", "crouched_or_prone_figure", "poet_tracksuit_31", "Poet (Tracksuit) · Falling Replacement"),
    ],
    "EX": [
        ("ex.ex_jacket.master__p01", "full_figure_adult", "ex_jacket_back", "Ex (Dark Jacket) · Standing Back View"),
        ("ex.ex_jacket.master__p29", "full_figure_adult", "ex_jacket_back", "Ex (Dark Jacket) · Back Stand at Window"),
        ("ex.ex_jacket.master__p30", "crouched_or_prone_figure", "ex_jacket_back", "Ex (Dark Jacket) · Leaning on Fire-Escape Rail"),
        ("ex.ex_jacket.master__p31", "crouched_or_prone_figure", "ex_jacket_back", "Ex (Dark Jacket) · Falling Back in Void"),
        ("ex.ex_jacket.master__p32", "crouched_or_prone_figure", "ex_jacket_back", "Ex (Dark Jacket) · Crouched Over Suitcase"),
    ],
    "WOMAN": [
        ("woman.13.window-action__p13", "full_figure_adult", "woman_muse_costumes", "Woman (Poem 13) · Standing by Distant Window"),
        ("woman.13.window-action__p14", "full_figure_adult", "woman_muse_costumes", "Woman (Poem 13) · Turning at Window"),
        ("woman.13.window-action__p15", "full_figure_adult", "woman_muse_costumes", "Woman (Poem 13) · Window Wave / Farewell"),
        ("poet.14.muse-dance__p02", "full_figure_adult", "woman_muse_costumes", "Muse (Poem 14) · Waltz Turn"),
        ("poet.14.muse-dance__p03", "full_figure_adult", "woman_muse_costumes", "Muse (Poem 14) · Dip & Spin"),
        ("poet.14.muse-dance__p04", "full_figure_adult", "woman_muse_costumes", "Muse (Poem 14) · Slow Dance Embrace"),
        ("party.vintage_party.main-poses__p01", "full_figure_adult", "woman_muse_costumes", "Woman in Gold Gown · Ballroom Stand"),
        ("08.cast.club.main-poses__p03", "full_figure_adult", "woman_muse_costumes", "Woman in Club Dress · Rooftop Stand"),
    ],
    "PARTY": [
        ("party.01.vintage-waltz-instances__p01", "full_figure_adult", "vintage_party_couple", "Vintage Party Couple · Waltz Instance A"),
        ("party.01.vintage-waltz-instances__p02", "full_figure_adult", "vintage_party_couple", "Vintage Party Couple · Waltz Instance B"),
        ("party.01.vintage-waltz-instances__p03", "full_figure_adult", "vintage_party_couple", "Vintage Party Couple · Waltz Instance C"),
        ("party.vintage_party.main-poses__p01", "full_figure_adult", "vintage_party_couple", "Vintage Party Guest · Standing Toast"),
        ("party.vintage_party.main-poses__p02", "full_figure_adult", "vintage_party_couple", "Vintage Party Guest · Gown Turn"),
        ("party.vintage_party.paired-choreography__p01", "full_figure_adult", "vintage_party_couple", "Vintage Party · Paired Choreography A"),
        ("party.vintage_party.paired-choreography__p02", "full_figure_adult", "vintage_party_couple", "Vintage Party · Paired Choreography B"),
    ],
    "YOUNG_POET": [
        ("young_ghost.02.main-poses__p01", "full_figure_child", "child_traveler_ghost", "Young Poet (Child) · Hallway Stand"),
        ("young_ghost.02.main-poses__p02", "full_figure_child", "child_traveler_ghost", "Young Poet (Child) · Holding Tambourine"),
        ("young_ghost.02.main-poses__p03", "full_figure_child", "child_traveler_ghost", "Young Poet (Child) · Looking Up"),
        ("young_ghost.02.main-poses__p04", "full_figure_child", "child_traveler_ghost", "Ghost Child · Doorway Silhouette"),
        ("young_poet.13.main-poses__p01", "full_figure_child", "child_traveler_ghost", "Young Poet (Poem 13) · Shore Stand"),
        ("young_poet.13.main-poses__p02", "full_figure_child", "child_traveler_ghost", "Young Poet (Poem 13) · Paper Boat Launch"),
        ("young_poet.13.main-poses__p03", "full_figure_child", "child_traveler_ghost", "Young Poet (Poem 13) · Watching Horizon"),
    ],
    "CHILD_TRAVELER": [
        ("atlantis.06.plaza-twelve__p03", "full_figure_child", "child_traveler_ghost", "Child Traveler · Atlantis Plaza Witness"),
        ("atlantis.06.source-actions__p05", "full_figure_child", "child_traveler_ghost", "Child Traveler · Run Cycle Contact"),
        ("atlantis.06.source-actions__p06", "full_figure_child", "child_traveler_ghost", "Child Traveler · Run Cycle Passing"),
        ("atlantis.06.source-actions__p07", "full_figure_child", "child_traveler_ghost", "Child Traveler · Pointing to Comet"),
    ],
    "PARENTS_02": [
        ("parents.02.car-argument__p01", "crouched_or_prone_figure", "mother_ancestors_family", "Father & Mother · Seated Car Argument A"),
        ("parents.02.car-argument__p02", "crouched_or_prone_figure", "mother_ancestors_family", "Father · Driver Profile Turning"),
        ("parents.02.car-argument__p03", "crouched_or_prone_figure", "mother_ancestors_family", "Mother · Passenger Profile Gesturing"),
        ("parents.02.car-argument__p04", "full_figure_adult", "mother_ancestors_family", "Parents · Driveway Silhouette Pair"),
    ],
    "ANCESTORS": [
        ("ancestors.05.procession-gifts-gate__p01", "full_figure_adult", "mother_ancestors_family", "Ancestor Procession · Lantern Bearer"),
        ("ancestors.05.procession-gifts-gate__p02", "full_figure_adult", "mother_ancestors_family", "Ancestor Procession · Gift Bearer"),
        ("ancestors.05.procession-gifts-gate__p03", "full_figure_adult", "mother_ancestors_family", "Ancestor Procession · Elder Stride"),
        ("ancestors.05.procession-gifts-gate__p04", "full_figure_adult", "mother_ancestors_family", "Ancestor Procession · Gate Keeper"),
        ("ancestors.05.identities.01__p09", "full_figure_adult", "mother_ancestors_family", "Ancestor Identity · Amos Full Figure"),
        ("ancestors.05.identities.01__p18", "full_figure_adult", "mother_ancestors_family", "Ancestor Identity · Matriarch Full Figure"),
    ],
    "ATLANTIS_CAST": [
        ("atlantis.06.plaza-twelve__p01", "full_figure_adult", "dj_club_citizens", "Atlantis Elder · Robed Witness"),
        ("atlantis.06.plaza-twelve__p02", "full_figure_adult", "dj_club_citizens", "Atlantis Traveler · Cloak & Staff"),
        ("atlantis.06.plaza-twelve__p04", "full_figure_adult", "dj_club_citizens", "Atlantis Gatekeeper · Standing Guard"),
        ("atlantis.06.plaza-twelve__p05", "full_figure_adult", "dj_club_citizens", "Atlantis Citizen · Forum Listener"),
        ("atlantis.06.plaza-twelve__p06", "full_figure_adult", "dj_club_citizens", "Atlantis Citizen · Waterfront Watcher"),
        ("atlantis.06.source-actions__p01", "full_figure_adult", "dj_club_citizens", "Atlantis Traveler · Walking Causeway"),
        ("atlantis.06.source-actions__p02", "full_figure_adult", "dj_club_citizens", "Atlantis Elder · Raising Lantern"),
    ],
    "DJ_AND_CLUB": [
        ("party.07.dj_cyber.main-poses__p01", "full_figure_adult", "dj_club_citizens", "DJ Cyber · At the Decks"),
        ("party.07.dj_cyber.main-poses__p02", "full_figure_adult", "dj_club_citizens", "DJ Cyber · One-Ear Headphone Cue"),
        ("party.07.dj_cyber.main-poses__p03", "full_figure_adult", "dj_club_citizens", "DJ Cyber · Raising Hand on Drop"),
        ("party.07.party_guest.main-poses__p01", "full_figure_adult", "dj_club_citizens", "Party Guest · Club Groove A"),
        ("party.07.party_guest.main-poses__p02", "full_figure_adult", "dj_club_citizens", "Party Guest · Club Groove B"),
        ("08.cast.club.main-poses__p01", "full_figure_adult", "dj_club_citizens", "Club Citizen · Rooftop Stand"),
        ("08.cast.club.main-poses__p02", "full_figure_adult", "dj_club_citizens", "Club Citizen · Leaning on Rail"),
    ],
    "ANGELS_AND_SOUL": [
        ("08.cast.angel.main-poses__p01", "full_figure_adult", "dj_club_citizens", "Angel · White Robe Standing Guard"),
        ("08.cast.angel.main-poses__p02", "full_figure_adult", "dj_club_citizens", "Angel · Wings Spread Hover"),
        ("08.cast.angel.main-poses__p03", "full_figure_adult", "dj_club_citizens", "Angel · Basin Attendant"),
        ("poet_soul.08.main-poses__p01", "full_figure_adult", "poet_tracksuit_31", "Poet Soul · Luminous Double Stand"),
        ("poet_soul.08.main-poses__p02", "full_figure_adult", "poet_tracksuit_31", "Poet Soul · Ascending Drift"),
    ],
    "PARENTS_09": [
        ("parents.09.phone-prayer-walk__p01", "full_figure_adult", "mother_ancestors_family", "Mother (Poem 09) · Leaning by Wall Phone"),
        ("parents.09.phone-prayer-walk__p02", "crouched_or_prone_figure", "mother_ancestors_family", "Mother (Poem 09) · Seated Prayer"),
        ("parents.09.phone-prayer-walk__p03", "full_figure_adult", "mother_ancestors_family", "Father Elder & Poet · Walking East Harbor"),
        ("parents.09.phone-prayer-walk__p04", "full_figure_adult", "mother_ancestors_family", "Father Elder · Steadying Poet's Shoulder"),
    ],
    "FAMILY_AND_ELDERS": [
        ("family.11.optional.action__p10", "full_figure_adult", "mother_ancestors_family", "Family Watcher · Raising Hand in Greeting"),
        ("family.11.optional.action__p11", "full_figure_adult", "mother_ancestors_family", "Family Watcher · Walking In Along Shore"),
        ("family.11.optional.action__p12", "full_figure_adult", "mother_ancestors_family", "Family Watcher · Open-Arm Welcome"),
        ("family.12.hug-restage__p01", "full_figure_adult", "mother_ancestors_family", "Brother & Poet · Porch Embrace"),
        ("family.12.hug-restage__p02", "full_figure_adult", "mother_ancestors_family", "Friend & Family · Temple Gathering"),
        ("family.12.hug-restage__p03", "full_figure_adult", "mother_ancestors_family", "Family · Two-Figure Reunion Stand"),
        ("12.elders.memory-drop__p01", "full_figure_adult", "mother_ancestors_family", "Temple Elder · Holding Hourglass"),
        ("12.elders.memory-drop__p02", "full_figure_adult", "mother_ancestors_family", "Temple Elder · Memory Drop Witness"),
        ("family.13.couple-orbits__p03", "full_figure_adult", "mother_ancestors_family", "Harbor Couple · Walking Orbit"),
        ("family.13.elder-prayer__p01", "full_figure_adult", "mother_ancestors_family", "Harbor Elder · Quay Prayer"),
        ("family.14.mainposes__p01", "full_figure_adult", "mother_ancestors_family", "Family Ensemble · Final Curtain Stand A"),
        ("family.14.mainposes__p02", "full_figure_adult", "mother_ancestors_family", "Family Ensemble · Final Curtain Stand B"),
    ],
}


# Sheets that contain ONLY detached body parts / headless torso vests and must
# NEVER be selected as a standalone character layer on P2.
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
    "08.cast.angel.wings",
    "08.cast.club_1.body",
    "08.cast.club_2.body",
    "party.07.action.dj_cyber.torso-parts",
    "party.dj_cyber.compact-core",
    "party.party_guest.compact-core",
    "poet.black_tshirt.body",
    "poet.tracksuit.body",
    "poet.tracksuit.hips-waist",
    "woman.black_dress.body",
    "woman.burgundy_dress.body",
    "woman.cream_coat.body",
    "woman.gold_gown.body",
    "woman.teal_gown.body",
    "woman.white_shift.body",
}


# ---------------------------------------------------------------------------
# 3. Aspect Ratio & Physical Scale Solver
# ---------------------------------------------------------------------------

def aspect_compensation_multiplier(width: int, height: int, sem_class: str) -> float:
    """
    Compensate height scale (`targetH = sh * scale`) when a cut part is wider
    than a standard vertical standing figure (`w/h > 0.75`), preventing wide
    crouched/falling poses or horizontal props from blowing up to giant size.
    """
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
    if sem_class == "handheld_prop":
        if ar > 1.8:
            return 0.86
        return 1.0
    return 1.0


def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def classify_part(
    sheet: Dict[str, Any],
    part: Dict[str, Any],
    dossier_props_by_poem: Dict[int, List[Dict[str, Any]]],
    ocr_labels_by_part: Dict[str, str],
) -> Dict[str, Any]:
    """
    Classify a single cut part into one of the 15 Semantic Physical Classes and
    compute its calibrated physical scale, plane, Z-depth, Y-anchor, and `scale_cm`.
    """
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

    # --- A. 05_PAINTED_EFFECTS ---
    if subfolder == "05_PAINTED_EFFECTS" or kind in ("fx", "painted_fx"):
        if sid in TYPOGRAPHY_SHEETS or any(k in low_lbl for k in ("word", "letter", "frame", "aperture")):
            sem_class = "typography_banner"
            scale_cm, base_scale = TYPOGRAPHY_SHEETS.get(sid, (85, 0.28))
        elif any(k in low_sid for k in ("sky", "clouds", "light")) and rel_w > 0.45 and ar > 2.2:
            sem_class = "sky_canopy"
            scale_cm, base_scale = 1200, 0.96
        else:
            sem_class = "atmospheric_fx"
            scale_cm, base_scale = 140, 0.30

    # --- B. 03_PROPS ---
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
            # Sheet has bar counter (large_furniture) and lighter/phone (handheld_prop)
            if max(w, h) < 260:
                sem_class = "handheld_prop"
                scale_cm, base_scale = 14, 0.11
            else:
                sem_class = "large_furniture"
                scale_cm, base_scale = 110, 0.36
        elif sid == "02.props.mirror-phone-rings":
            if max(w, h) < 220:
                sem_class = "handheld_prop"
                scale_cm, base_scale = 12, 0.10
            else:
                sem_class = "medium_prop"
                scale_cm, base_scale = 95, 0.24
        elif sid == "06.props.coin-booth":
            if max(w, h) < 240:
                sem_class = "handheld_prop"
                scale_cm, base_scale = 4, 0.10
            else:
                sem_class = "large_furniture"
                scale_cm, base_scale = 200, 0.38
        else:
            sem_class = "medium_prop"
            scale_cm, base_scale = 75, 0.22

    # --- C. 04_SETS_AND_BUILDINGS ---
    elif subfolder == "04_SETS_AND_BUILDINGS" or kind in ("set", "hero", "hero-continuation"):
        if sid in LARGE_FURNITURE_PROP_SHEETS:
            sem_class = "large_furniture"
            scale_cm, base_scale = LARGE_FURNITURE_PROP_SHEETS[sid]
        elif sid in DOOR_WINDOW_PROP_SHEETS:
            sem_class = "door_window_arch"
            scale_cm, base_scale = DOOR_WINDOW_PROP_SHEETS[sid]
        elif any(k in low_sid for k in ("black_void", "calm_sea")):
            sem_class = "sky_canopy"
            scale_cm, base_scale = 1200, 0.98
        elif any(k in low_sid for k in ("skyline", "aerial", "equator_plain", "harbor_atlantis_wide", "broll_life")):
            if rel_y < 0.35 and ar > 1.8:
                sem_class = "sky_canopy"
                scale_cm, base_scale = 1200, 0.96
            else:
                sem_class = "horizon_vista"
                scale_cm, base_scale = 850, 0.82
        elif any(k in low_sid for k in (
            "catwalk", "severnescape", "viaduct", "steps", "shore_steps",
            "causeway_road", "mountain_road", "incline_trail", "harbor_path_east", "perimeter"
        )):
            sem_class = "stair_bridge_viaduct"
            scale_cm, base_scale = 380, 0.65
        elif any(k in low_sid for k in (
            "bedroom_night", "living_room_1990s", "humid_basement", "mother_living_room",
            "mirror_hall", "temple_backroom", "temple_hall", "marquee.interior",
            "chapel.interior-states", "drowned_atrium", "atrium", "crystal_tree_hall"
        )):
            sem_class = "room_wall"
            scale_cm, base_scale = 320, 0.70
        else:
            # Check if an individual card on a building sheet is a wide sky backdrop or horizon vista
            if rel_w > 0.55 and rel_y < 0.38 and ar > 1.9:
                sem_class = "sky_canopy"
                scale_cm, base_scale = 1100, 0.96
            elif rel_w > 0.48 and ar > 2.1:
                sem_class = "horizon_vista"
                scale_cm, base_scale = 750, 0.80
            else:
                sem_class = "building_facade"
                scale_cm, base_scale = 450, 0.68

    # --- D. 01_CHARACTER_CORE & 02_ACTIONS_AND_POSES ---
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
            "compact-core", "wings", "expressions"
        )):
            sem_class = "limb_or_head_detail"
            scale_cm, base_scale = 30, 0.16
        elif is_child:
            if ar > 0.95 or is_crouched_sheet:
                sem_class = "crouched_or_prone_figure"
                scale_cm, base_scale = 85, 0.28
            else:
                sem_class = "full_figure_child"
                scale_cm, base_scale = 120, 0.38
        elif is_crouched_sheet:
            sem_class = "crouched_or_prone_figure"
            scale_cm, base_scale = 105, 0.32
        elif is_pose_sheet:
            if ar > 0.92:
                sem_class = "crouched_or_prone_figure"
                scale_cm, base_scale = 105, 0.32
            else:
                sem_class = "full_figure_adult"
                scale_cm, base_scale = 175, 0.55
        else:
            # Mixed character sheets (e.g. master, window-action, muse-dance, exit, reserve, optional.action)
            if rel_h >= 0.24 and h >= 210 and ar <= 0.90:
                sem_class = "full_figure_adult"
                scale_cm, base_scale = 175, 0.55
            elif rel_h >= 0.22 and h >= 190 and ar <= 1.25:
                sem_class = "crouched_or_prone_figure"
                scale_cm, base_scale = 105, 0.32
            else:
                sem_class = "limb_or_head_detail"
                scale_cm, base_scale = 30, 0.16

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


# ---------------------------------------------------------------------------
# 4. Camera Framing & Scene Audio/World/Archive Resolver
# ---------------------------------------------------------------------------

def infer_camera_framing(scene: Dict[str, Any], atlas_scenes: List[Dict[str, Any]]) -> str:
    """
    Determine the canonical `camera_framing` (`extreme_wide`, `wide`,
    `medium_wide`, `medium`, `close`) from the scene's beat tags, treatment,
    and atlas camera notes.
    """
    beats_text = " ".join(scene.get("beats", [])).upper()
    treatment_text = (scene.get("treatment", "") or "").upper()
    title_text = (scene.get("title", "") or "").upper()
    combined = f"{beats_text} {treatment_text} {title_text}"

    # Count explicit beat framing tags `[01.1a · WIDE / EYE]`
    tag_counts = {
        "extreme_wide": len(re.findall(r"\b(EXTREME[ _-]?WIDE|AERIAL|HORIZON|PANORAMA)\b", combined)),
        "wide": len(re.findall(r"\bWIDE\b", combined)),
        "medium_wide": len(re.findall(r"\b(MEDIUM[ _-]?WIDE|TWO[ _-]?SHOT|FULL[ _-]?SHOT)\b", combined)),
        "medium": len(re.findall(r"\bMEDIUM\b", combined)),
        "close": len(re.findall(r"\b(CLOSE|MACRO|INSERT|TIGHT|DETAIL)\b", combined)),
    }

    if tag_counts["extreme_wide"] >= 1 and ("SKYLINE" in combined or "VOID" in combined or "AERIAL" in combined or "HORIZON" in combined):
        return "extreme_wide"
    if tag_counts["close"] >= 2 and tag_counts["wide"] == 0:
        return "close"
    if tag_counts["medium"] > tag_counts["wide"] and tag_counts["medium"] >= 2:
        return "medium"
    if tag_counts["wide"] >= 2:
        return "wide"
    if tag_counts["close"] >= 1 and ("EYE" in combined or "HAND" in combined or "HOURGLASS" in combined):
        return "medium"
    return "medium_wide"


def scale_for_framing(base_scale: float, sem_class: str, framing: str) -> float:
    """
    Modulate `base_scale` by `camera_framing` while clamping strictly inside
    the physical class's valid stage scale bounds so no prop or figure ever
    violates physical scale rules.
    """
    spec = SEMANTIC_CLASS_SPECS[sem_class]
    f_spec = CAMERA_FRAMING_SPECS[framing]
    lo, hi = spec["scale_range"]

    if sem_class in ("full_figure_adult", "full_figure_child", "crouched_or_prone_figure"):
        mult = f_spec["actor_mult"]
    elif sem_class in ("handheld_prop", "medium_prop", "large_furniture", "limb_or_head_detail"):
        mult = f_spec["prop_mult"]
    elif sem_class in ("building_facade", "room_wall", "door_window_arch", "stair_bridge_viaduct"):
        mult = f_spec["arch_mult"]
    else:
        mult = 1.0

    return round(clamp(base_scale * mult, lo, hi), 4)


# ---------------------------------------------------------------------------
# 5. Main Builder
# ---------------------------------------------------------------------------

def main() -> None:
    print("[1/5] Loading release_catalog.json, wygwyl_atlas_manifest.json, suite_scion_timeline.json, character_rigs_library.json...")
    catalog = json.loads((RELEASE_DIR / "release_catalog.json").read_text())
    manifest = json.loads((RELEASE_DIR / "wygwyl_atlas_manifest.json").read_text())
    timeline = json.loads((RELEASE_DIR / "suite_scion_timeline.json").read_text())
    rigs_lib = json.loads((RELEASE_DIR / "character_rigs_library.json").read_text())
    weave_lib = json.loads((SHOTS_DIR / "weave" / "cast" / "man" / "library_manifest.json").read_text())

    # Load world_data.js
    wd_text = (SHOTS_DIR / "world_data.js").read_text()
    wd_match = re.search(r"window\.WORLD\s*=\s*(\{.*\})\s*;?\s*$", wd_text, re.S)
    world_data = json.loads(wd_match.group(1)) if wd_match else {"districts": [], "shots": [], "reels": []}
    world_shots_by_id = {s["id"]: s for s in world_data.get("shots", [])}
    world_reels_by_poem = {int(r["num"]): r for r in world_data.get("reels", [])}
    districts_by_id = {d["id"]: d for d in world_data.get("districts", [])}

    # Load poem dossiers, breakdowns, and atlases
    dossiers: Dict[int, Dict[str, Any]] = {}
    breakdowns: Dict[int, Dict[str, Any]] = {}
    atlases: Dict[int, Dict[str, Any]] = {}
    dossier_props_by_poem: Dict[int, List[Dict[str, Any]]] = {}
    dossier_sets_by_poem: Dict[int, Dict[str, Dict[str, Any]]] = {}

    for p in range(1, 15):
        d_path = SHOTS_DIR / "poems" / "dossier" / f"{p:02d}.json"
        b_path = SHOTS_DIR / "poems" / "breakdown" / f"{p:02d}.json"
        a_path = SHOTS_DIR / "poems" / "atlas" / f"{p:02d}.json"
        dossiers[p] = json.loads(d_path.read_text()) if d_path.exists() else {}
        breakdowns[p] = json.loads(b_path.read_text()) if b_path.exists() else {}
        atlases[p] = json.loads(a_path.read_text()) if a_path.exists() else {}
        dossier_props_by_poem[p] = dossiers[p].get("props", [])
        dossier_sets_by_poem[p] = {s["id"]: s for s in dossiers[p].get("sets", [])}

    # Index sheets and parts from release_catalog.json
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

    # Also index the 31 standalone tracksuit rig components (6,234 + 31 = 6,265 total cut parts)
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

    print(f"[2/5] Classifying all {len(parts_by_id)} cut parts across {len(sheets_by_id)} sheets + 31 tracksuit components into 15 Semantic Physical Classes...")
    part_classifications: Dict[str, Dict[str, Any]] = {}
    class_counts: Dict[str, int] = {k: 0 for k in SEMANTIC_CLASS_SPECS}

    for pid, pt in parts_by_id.items():
        sh = sheet_of_part[pid]
        info = classify_part(sh, pt, dossier_props_by_poem, ocr_labels_by_part)
        part_classifications[pid] = info
        class_counts[info["semantic_class"]] = class_counts.get(info["semantic_class"], 0) + 1

    print("  Semantic class distribution across 6,265 cut parts:")
    for k, cnt in sorted(class_counts.items(), key=lambda item: -item[1]):
        print(f"    - {k:26s}: {cnt:4d} parts (plane={SEMANTIC_CLASS_SPECS[k]['plane']}, scale={SEMANTIC_CLASS_SPECS[k]['scale_range']})")

    # Index timeline films and scion shots
    films_by_poem = {int(f["n"]): f for f in timeline.get("films", [])}
    scion_shots_by_poem: Dict[int, List[Dict[str, Any]]] = {}
    for s in timeline.get("shots", []):
        scion_shots_by_poem.setdefault(int(s["poem"]), []).append(s)

    # Group manifest scenes by poem to compute exact monotonic audio windows
    scenes_by_poem: Dict[int, List[Dict[str, Any]]] = {}
    for sc in manifest["scenes"]:
        scenes_by_poem.setdefault(int(sc["book"]), []).append(sc)

    scene_audio_windows: Dict[str, Dict[str, Any]] = {}
    for p, p_scenes in scenes_by_poem.items():
        film = films_by_poem[p]
        c0, c1 = float(film["container"][0]), float(film["container"][1])
        w0, w1 = float(film["poem"][0]), float(film["poem"][1])
        total_local_sec = sum(max(1.0, float(s.get("seconds", 10))) for s in p_scenes)
        cur_c = c0
        cur_w = w0
        p_scion = scion_shots_by_poem.get(p, [])

        for idx, s in enumerate(p_scenes):
            frac = max(1.0, float(s.get("seconds", 10))) / total_local_sec
            next_c = c1 if idx == len(p_scenes) - 1 else cur_c + (c1 - c0) * frac
            next_w = w1 if idx == len(p_scenes) - 1 else cur_w + (w1 - w0) * frac
            # Match scion shots overlapping [cur_w, next_w] or [cur_c, next_c]
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
            cur_c = next_c
            cur_w = next_w

    # Helper to build a valid stage layer dictionary from a part_id
    def make_cut_layer(
        instance: str,
        pid: str,
        role: str,
        framing: str,
        x: float,
        y_override: Optional[float] = None,
        plane_override: Optional[str] = None,
        z_override: Optional[float] = None,
        alpha: float = 0.98,
        blend: str = "source-over",
        label_override: Optional[str] = None,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pt = parts_by_id[pid]
        sh = sheet_of_part[pid]
        cls_info = part_classifications[pid]
        sem_class = cls_info["semantic_class"]
        spec = SEMANTIC_CLASS_SPECS[sem_class]

        plane = plane_override or cls_info["plane"]
        z_val = z_override if z_override is not None else cls_info["z"]
        scale_val = scale_for_framing(cls_info["scale"], sem_class, framing)
        y_val = round(y_override if y_override is not None else cls_info["y"], 3)

        layer: Dict[str, Any] = {
            "instance": instance,
            "plane": plane,
            "z": round(float(z_val), 2),
            "semantic_class": sem_class,
            "scale_cm": cls_info["scale_cm"],
            "sheet_id": sh["id"],
            "part_id": pid,
            "label": label_override or pt.get("label") or f"{sh['id']} · {pid}",
            "file": pt["file"],
            "width": int(pt["width"]),
            "height": int(pt["height"]),
            "x": round(float(x), 3),
            "y": y_val,
            "scale": scale_val,
            "alpha": round(float(alpha), 3),
            "blend": blend,
            "role": role,
            "sheet_file": sh.get("sheet_rel", ""),
            "bbox_sheet": pt.get("bbox_sheet", [0, 0, int(pt["width"]), int(pt["height"])]),
            "pivots": pt.get("pivots", []),
        }
        if extra_meta:
            layer.update(extra_meta)
        return layer

    # Helper to pick curated full-figure character poses for a scene
    def select_scene_actors(scene: Dict[str, Any], poem_num: int, sc_idx: int) -> List[Tuple[str, str, str, str, str]]:
        """
        Return a list of (slot_role, part_id, sem_class, rig_id, label) for the
        active characters in `scene`, guaranteeing 100% full-figure poses and
        zero detached headless torso vests.
        """
        text = " ".join([
            scene.get("title", ""),
            scene.get("treatment", ""),
            " ".join(scene.get("beats", [])),
        ]).upper()

        selected: List[Tuple[str, str, str, str, str]] = []

        # 1. Hero Poet (prioritize poem-specific full-figure main poses)
        base_poet_pool = CURATED_CHARACTER_POSES["POET_TSHIRT"] if poem_num in (1, 2, 3) else CURATED_CHARACTER_POSES["POET_TRACKSUIT"]
        poem_poet_pool = [p for p in base_poet_pool if f"poet.{poem_num:02d}." in p[0]]
        poet_pool = poem_poet_pool if poem_poet_pool else base_poet_pool

        if poem_num == 10 and any(k in text for k in ("BIKE", "MOTORCYCLE", "RIDE", "HIGHWAY")):
            bike_poses = [p for p in poet_pool if p[1] == "crouched_or_prone_figure"]
            p_choice = bike_poses[sc_idx % len(bike_poses)] if bike_poses else poet_pool[sc_idx % len(poet_pool)]
        elif any(k in text for k in ("FALL", "VOID", "PLUNGE", "DROP")):
            fall_poses = [p for p in base_poet_pool if p[1] == "crouched_or_prone_figure"]
            p_choice = fall_poses[sc_idx % len(fall_poses)] if fall_poses else poet_pool[sc_idx % len(poet_pool)]
        elif any(k in text for k in ("KNEEL", "CROUCH", "SHORE", "FLOOR")):
            crouch_poses = [p for p in base_poet_pool if p[1] == "crouched_or_prone_figure"]
            p_choice = crouch_poses[sc_idx % len(crouch_poses)] if crouch_poses else poet_pool[sc_idx % len(poet_pool)]
        elif poem_num == 14 and "DANCE" in text:
            dance_poses = [p for p in poet_pool if "muse-dance" in p[0]]
            p_choice = dance_poses[0] if dance_poses else poet_pool[sc_idx % len(poet_pool)]
        else:
            stand_poses = [p for p in poet_pool if p[1] == "full_figure_adult"]
            if not stand_poses:
                stand_poses = [p for p in base_poet_pool if p[1] == "full_figure_adult"]
            p_choice = stand_poses[sc_idx % len(stand_poses)]
        selected.append(("hero_poet", p_choice[0], p_choice[1], p_choice[2], p_choice[3]))

        # 2. Supporting Cast matched to poem & scene text
        if "EX" in re.findall(r"\bEX\b", text) or (poem_num in (1, 3) and sc_idx <= 2):
            ex_pool = CURATED_CHARACTER_POSES["EX"]
            if "FALL" in text:
                c = ex_pool[3]
            elif "RAIL" in text or "FIRE ESCAPE" in text or "WINDOW" in text:
                c = ex_pool[2] if sc_idx % 2 == 1 else ex_pool[0]
            else:
                c = ex_pool[sc_idx % len(ex_pool)]
            selected.append(("support_ex", c[0], c[1], c[2], c[3]))

        if poem_num == 2 and any(k in text for k in ("CHILD", "YOUNG", "GHOST", "BOY", "TAMBOURINE", "HALLWAY")):
            yp_pool = CURATED_CHARACTER_POSES["YOUNG_POET"][:4]
            c = yp_pool[sc_idx % len(yp_pool)]
            selected.append(("support_child", c[0], c[1], c[2], c[3]))

        if poem_num == 2 and any(k in text for k in ("FATHER", "MOTHER", "PARENTS", "CAR", "SEDAN", "DRIVEWAY", "LIVING ROOM")):
            par_pool = CURATED_CHARACTER_POSES["PARENTS_02"]
            c = par_pool[sc_idx % len(par_pool)]
            selected.append(("support_parents", c[0], c[1], c[2], c[3]))

        if poem_num in (1, 14) and any(k in text for k in ("PARTY", "WALTZ", "BALLROOM", "COUPLE", "DANCE", "GUEST")):
            pt_pool = CURATED_CHARACTER_POSES["PARTY"]
            c = pt_pool[sc_idx % len(pt_pool)]
            selected.append(("support_party", c[0], c[1], c[2], c[3]))

        if poem_num == 5:
            anc_pool = CURATED_CHARACTER_POSES["ANCESTORS"]
            c = anc_pool[sc_idx % len(anc_pool)]
            selected.append(("support_ancestor", c[0], c[1], c[2], c[3]))

        if poem_num == 6:
            atl_pool = CURATED_CHARACTER_POSES["ATLANTIS_CAST"]
            c1 = atl_pool[sc_idx % len(atl_pool)]
            selected.append(("support_atlantis", c1[0], c1[1], c1[2], c1[3]))
            if any(k in text for k in ("CHILD", "PLAZA", "TWELVE", "FORUM", "COMET")):
                ch_pool = CURATED_CHARACTER_POSES["CHILD_TRAVELER"]
                c2 = ch_pool[sc_idx % len(ch_pool)]
                selected.append(("support_child_traveler", c2[0], c2[1], c2[2], c2[3]))

        if poem_num == 7:
            dj_pool = CURATED_CHARACTER_POSES["DJ_AND_CLUB"]
            c = dj_pool[sc_idx % len(dj_pool)]
            selected.append(("support_dj_club", c[0], c[1], c[2], c[3]))

        if poem_num == 8:
            ang_pool = CURATED_CHARACTER_POSES["ANGELS_AND_SOUL"]
            c = ang_pool[sc_idx % len(ang_pool)]
            selected.append(("support_angel_soul", c[0], c[1], c[2], c[3]))

        if poem_num == 9:
            p9_pool = CURATED_CHARACTER_POSES["PARENTS_09"]
            c = p9_pool[sc_idx % len(p9_pool)]
            selected.append(("support_parents_09", c[0], c[1], c[2], c[3]))

        if poem_num in (10, 11, 12):
            fam_pool = CURATED_CHARACTER_POSES["FAMILY_AND_ELDERS"]
            if poem_num == 12:
                sub = [p for p in fam_pool if "12" in p[0]]
            else:
                sub = [p for p in fam_pool if "11" in p[0]]
            if not sub:
                sub = fam_pool
            c = sub[sc_idx % len(sub)]
            selected.append(("support_family", c[0], c[1], c[2], c[3]))

        if poem_num == 13:
            w13 = [p for p in CURATED_CHARACTER_POSES["WOMAN"] if "13" in p[0]]
            c = w13[sc_idx % len(w13)]
            selected.append(("support_woman_13", c[0], c[1], c[2], c[3]))
            if any(k in text for k in ("YOUNG", "CHILD", "BOAT", "SHORE", "HARVEST")):
                yp13 = [p for p in CURATED_CHARACTER_POSES["YOUNG_POET"] if "13" in p[0]]
                c2 = yp13[sc_idx % len(yp13)]
                selected.append(("support_young_poet_13", c2[0], c2[1], c2[2], c2[3]))

        if poem_num == 14 or (poem_num in (5, 6, 7, 12) and "WOMAN" in text):
            w_pool = [p for p in CURATED_CHARACTER_POSES["WOMAN"] if f".{poem_num:02d}." in p[0]]
            if not w_pool:
                w_pool = CURATED_CHARACTER_POSES["WOMAN"]
            c = w_pool[sc_idx % len(w_pool)]
            if all(s[1] != c[0] for s in selected):
                selected.append(("support_woman_muse", c[0], c[1], c[2], c[3]))

        return selected[:3]

    # Pre-index sheets by poem and semantic class for fast, clean architectural & prop assembly
    parts_by_poem_and_class: Dict[Tuple[int, str], List[str]] = {}
    for pid, info in part_classifications.items():
        sh = sheet_of_part[pid]
        pt = parts_by_id[pid]
        if pt.get("role") == "reference_only":
            continue
        for p_num in sh.get("poems", []):
            parts_by_poem_and_class.setdefault((int(p_num), info["semantic_class"]), []).append(pid)

    # Sort each bucket by area descending so clean primary structural cards come first
    for key, pids in parts_by_poem_and_class.items():
        pids.sort(key=lambda x: parts_by_id[x].get("area_px", 0), reverse=True)

    # Pre-index weave walking / stairs / contact assets
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

    print("[3/5] Building 80 scale-calibrated Multiplane Mosaic Collage Plans (P01-S01 .. P14-S06)...")
    scenes_out: List[Dict[str, Any]] = []

    for sc in manifest["scenes"]:
        sc_id = sc["id"]
        poem_num = int(sc["book"])
        sc_idx = int(sc_id.split("-S")[-1]) - 1
        set_id = sc.get("set_id", "")
        dossier = dossiers.get(poem_num, {})
        atlas = atlases.get(poem_num, {})
        dossier_set = dossier_sets_by_poem.get(poem_num, {}).get(set_id, {})

        # 1. Camera Framing
        framing = infer_camera_framing(sc, atlas.get("scenes", []))
        framing_spec = CAMERA_FRAMING_SPECS[framing]

        # 2. Audio Window & Scion Shots
        audio_info = scene_audio_windows[sc_id]
        scion_shots = audio_info["scion_shots"]
        primary_scion = scion_shots[0] if scion_shots else (
            scion_shots_by_poem[poem_num][0] if scion_shots_by_poem.get(poem_num) else {}
        )

        # 3. World Backdrop Resolution (World Diorama + Multiplane S00_P6..S11_P1 + Stills + Atlas Views)
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

        # Match atlas views for this scene
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

        # Check if a weave clean plate applies (e.g. Poem 04 shore/hands or Poem 07 club/canopy)
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

        # 4. Archive / Found-Footage Plate Resolution
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

        # Select compositing mode based on set architecture (sky aperture, window/TV screen quad, or split wipe)
        combined_text = f"{sc.get('title', '')} {sc.get('treatment', '')}".upper()
        if any(k in combined_text for k in ("TV", "SCREEN", "WINDOW", "PROJECTION", "MIRROR")):
            comp_mode = "window_screen_quad"
            aperture_quad = [[0.58, 0.18], [0.88, 0.18], [0.88, 0.56], [0.58, 0.56]]
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

        # 5. Assemble Multiplane Stage Layers (`P6` -> `P1/P0`)
        stage_layers: List[Dict[str, Any]] = []

        # --- PLANE P6 (Z=6.0): World Vista / Sky Canopy + Archive Torn-Paper Sky Plate ---
        # Layer 1a: World Multiplane Sky/Backdrop Plate (guaranteed to exist in shots/world/<k>/backdrop.webp)
        stage_layers.append({
            "instance": "world_sky_backdrop",
            "plane": "P6",
            "z": 6.0,
            "semantic_class": "sky_canopy",
            "scale_cm": 1200,
            "sheet_id": f"world.{world_shot['k']}",
            "part_id": f"world.{world_shot['k']}__backdrop",
            "label": f"World Vista Plate · {district_info.get('name', district_id.title())}",
            "file": world_shot["backdrop"],
            "width": 1456,
            "height": 816,
            "x": 0.50,
            "y": 0.98,
            "scale": 1.00,
            "alpha": 0.96,
            "blend": "source-over",
            "role": "world_backdrop_plate",
            "sheet_file": world_shot["backdrop"],
            "bbox_sheet": [0, 0, 1456, 816],
            "pivots": [],
        })

        # Layer 1b: Cut-out Sky Canopy card if poem has one, or Archive Sky Wipe Plate
        sky_pids = parts_by_poem_and_class.get((poem_num, "sky_canopy"), [])
        if sky_pids:
            sky_pid = sky_pids[sc_idx % len(sky_pids)]
            stage_layers.append(
                make_cut_layer(
                    instance="cut_sky_canopy",
                    pid=sky_pid,
                    role="sky_canopy",
                    framing=framing,
                    x=0.50,
                    y_override=0.96,
                    plane_override="P6",
                    z_override=5.8,
                    alpha=0.92,
                )
            )

        # --- PLANE P5 (Z=3.8): Distant Architecture / Horizon Vista / Archive Window Plate ---
        # Include the Archive Found-Footage Plate at P5 so the collage blends Prelinger/archive film + world + cut-out kits
        archive_img_file = archive_ref_files[0] if archive_ref_files else poster_file
        stage_layers.append({
            "instance": "archive_found_footage_plate",
            "plane": "P5",
            "z": 3.9,
            "semantic_class": "horizon_vista",
            "scale_cm": 800,
            "sheet_id": f"archive.{primary_scion.get('id', f'P{poem_num:02d}-001')}",
            "part_id": f"archive.{primary_scion.get('id', f'P{poem_num:02d}-001')}__plate",
            "label": f"Archive Plate · {primary_scion.get('archive_title', 'Found Footage')} ({primary_scion.get('archive_year', 1959)})",
            "file": archive_img_file,
            "width": 1280,
            "height": 720,
            "x": 0.52,
            "y": 0.80,
            "scale": 0.78,
            "alpha": 0.86,
            "blend": "source-over",
            "role": "archive_plate",
            "sheet_file": archive_img_file,
            "bbox_sheet": [0, 0, 1280, 720],
            "pivots": [],
            "compositing_mode": comp_mode,
            "aperture_quad": aperture_quad,
        })

        vista_pids = parts_by_poem_and_class.get((poem_num, "horizon_vista"), [])
        if not vista_pids:
            vista_pids = parts_by_poem_and_class.get((poem_num, "building_facade"), [])
        if vista_pids:
            v_pid = vista_pids[sc_idx % len(vista_pids)]
            stage_layers.append(
                make_cut_layer(
                    instance="set_horizon_vista",
                    pid=v_pid,
                    role="set_backdrop",
                    framing=framing,
                    x=0.48,
                    y_override=0.82,
                    plane_override="P5",
                    z_override=3.8,
                    alpha=0.95,
                )
            )
            # adjust scale into P5 [0.72, 0.90] range if needed
            stage_layers[-1]["scale"] = round(clamp(stage_layers[-1]["scale"], 0.72, 0.90), 4)
            stage_layers[-1]["semantic_class"] = "horizon_vista"

        # --- PLANE P4 (Z=2.4): Segmented Architectural Elements (Left / Center / Right Framing) ---
        # Gather architectural parts matching this scene's set_id first, then poem's architectural pool
        arch_classes = ("room_wall", "building_facade", "stair_bridge_viaduct", "door_window_arch")
        scene_arch_pids: List[str] = []

        # Check original manifest layers for set sheets matched to this scene
        for orig_l in sc.get("stage_layers", []):
            opid = orig_l.get("part_id", "")
            if opid in part_classifications and part_classifications[opid]["semantic_class"] in arch_classes:
                if opid not in scene_arch_pids:
                    scene_arch_pids.append(opid)

        for a_cls in arch_classes:
            for pid in parts_by_poem_and_class.get((poem_num, a_cls), []):
                if set_id and set_id.lower() in sheet_of_part[pid]["id"].lower():
                    if pid not in scene_arch_pids:
                        scene_arch_pids.append(pid)

        for a_cls in arch_classes:
            for pid in parts_by_poem_and_class.get((poem_num, a_cls), []):
                if pid not in scene_arch_pids:
                    scene_arch_pids.append(pid)

        # Pick 3 distinct architectural cards and spread them across Left (x=0.18), Center-Back (x=0.50), Right (x=0.82)
        arch_x_slots = [0.18, 0.82, 0.50]
        arch_y_slots = [0.88, 0.89, 0.87]
        arch_roles = ["set_arch_left", "set_arch_right", "set_arch_center"]
        used_arch_pids = set()
        for slot_i in range(min(3, len(scene_arch_pids))):
            pick_idx = (sc_idx * 2 + slot_i) % len(scene_arch_pids)
            a_pid = scene_arch_pids[pick_idx]
            while a_pid in used_arch_pids and len(used_arch_pids) < len(scene_arch_pids):
                pick_idx = (pick_idx + 1) % len(scene_arch_pids)
                a_pid = scene_arch_pids[pick_idx]
            used_arch_pids.add(a_pid)
            stage_layers.append(
                make_cut_layer(
                    instance=f"arch_mid_{slot_i + 1}",
                    pid=a_pid,
                    role=arch_roles[slot_i],
                    framing=framing,
                    x=arch_x_slots[slot_i],
                    y_override=arch_y_slots[slot_i],
                    plane_override="P4",
                    z_override=round(2.45 - slot_i * 0.05, 2),
                    alpha=0.97,
                )
            )

        # --- PLANE P2 (Z=1.0): Hero & Supporting Cast Full Figures (resolved before P3 so handheld props can anchor to hands!) ---
        actors = select_scene_actors(sc, poem_num, sc_idx)
        actor_x_positions = (
            [0.44] if len(actors) == 1
            else [0.36, 0.64] if len(actors) == 2
            else [0.34, 0.62, 0.78]
        )
        actor_layers: List[Dict[str, Any]] = []
        primary_actor_x = actor_x_positions[0]

        for act_i, (slot_role, act_pid, act_sem_class, rig_id, act_label) in enumerate(actors):
            ax = actor_x_positions[act_i]
            ay = 0.91
            rig_obj = rigs_lib.get("rigs", {}).get(rig_id, {})
            loco_keys = list(rig_obj.get("locomotion_cycles", {}).keys())
            active_cycle = loco_keys[sc_idx % len(loco_keys)] if loco_keys else "idle_breathe"

            act_layer = make_cut_layer(
                instance=f"{slot_role}_{act_i + 1}",
                pid=act_pid,
                role="hero_character" if act_i == 0 else "support_character",
                framing=framing,
                x=ax,
                y_override=ay,
                plane_override="P2",
                z_override=round(1.02 - act_i * 0.02, 2),
                alpha=1.0,
                label_override=act_label,
                extra_meta={
                    "rig_id": rig_id,
                    "locomotion_cycle": active_cycle,
                    "posture_class": act_sem_class,
                },
            )
            actor_layers.append(act_layer)

        # --- PLANE P3 (Z=1.4): Grounded Set Furnishings (`large_furniture`, `medium_prop`) & Hand-Anchored `handheld_prop` ---
        furn_pids = parts_by_poem_and_class.get((poem_num, "large_furniture"), [])
        med_prop_pids = parts_by_poem_and_class.get((poem_num, "medium_prop"), [])
        hand_prop_pids = parts_by_poem_and_class.get((poem_num, "handheld_prop"), [])

        # 1. Large furniture or medium prop grounded on floor at P3
        if furn_pids:
            f_pid = furn_pids[sc_idx % len(furn_pids)]
            stage_layers.append(
                make_cut_layer(
                    instance="prop_furniture_1",
                    pid=f_pid,
                    role="large_furniture",
                    framing=framing,
                    x=0.26 if primary_actor_x > 0.40 else 0.72,
                    y_override=0.88,
                    plane_override="P3",
                    z_override=1.45,
                    alpha=0.98,
                )
            )
        if med_prop_pids:
            m_pid = med_prop_pids[(sc_idx * 2) % len(med_prop_pids)]
            m_sheet_id = sheet_of_part[m_pid]["id"]
            # Ceiling chandeliers or moons hang higher in the frame
            m_y = 0.28 if "chandelier" in m_sheet_id else (0.32 if "moon" in m_sheet_id else 0.86)
            stage_layers.append(
                make_cut_layer(
                    instance="prop_medium_1",
                    pid=m_pid,
                    role="medium_prop",
                    framing=framing,
                    x=0.74 if primary_actor_x <= 0.50 else 0.28,
                    y_override=m_y,
                    plane_override="P3",
                    z_override=1.38,
                    alpha=0.98,
                )
            )

        # 2. Handheld prop (`scale: 0.09–0.14`, pinned near active actor's hand at `actor_x ± 0.06, y: 0.64`)
        if hand_prop_pids:
            h_pid = hand_prop_pids[sc_idx % len(hand_prop_pids)]
            # If Ex is vaping in Poem 01, pin the vape pen near Ex's hand if Ex is present
            hand_owner_x = primary_actor_x
            if poem_num == 1 and len(actor_layers) > 1 and "vape" in parts_by_id[h_pid].get("label", "").lower():
                hand_owner_x = actor_layers[1]["x"]
            hand_x = round(clamp(hand_owner_x + 0.06, 0.12, 0.88), 3)
            hand_layer = make_cut_layer(
                instance="prop_handheld_1",
                pid=h_pid,
                role="handheld_prop",
                framing=framing,
                x=hand_x,
                y_override=0.64,
                plane_override="P3",
                z_override=1.32,
                alpha=0.99,
                extra_meta={
                    "attached_to_actor_x": hand_owner_x,
                    "hand_offset": [0.06, -0.27],
                },
            )
            # Strictly enforce handheld_prop scale in [0.09, 0.14]
            hand_layer["scale"] = round(clamp(hand_layer["scale"], 0.09, 0.14), 4)
            stage_layers.append(hand_layer)

        # Now append the P2 Actor layers after P3 layers
        stage_layers.extend(actor_layers)

        # --- PLANE P1 / P0 (Z=0.45): Torn-Paper Foreground Wipes, Repoussoir & Painted FX / Typography ---
        fx_pids = parts_by_poem_and_class.get((poem_num, "atmospheric_fx"), [])
        typo_pids = parts_by_poem_and_class.get((poem_num, "typography_banner"), [])

        if fx_pids:
            fx_pid = fx_pids[sc_idx % len(fx_pids)]
            fx_layer = make_cut_layer(
                instance="fx_foreground_1",
                pid=fx_pid,
                role="foreground_fx",
                framing=framing,
                x=0.52,
                y_override=0.72,
                plane_override="P1",
                z_override=0.45,
                alpha=0.80,
                blend="screen",
            )
            fx_layer["scale"] = round(clamp(fx_layer["scale"], 0.24, 0.38), 4)
            stage_layers.append(fx_layer)

        if typo_pids:
            ty_pid = typo_pids[sc_idx % len(typo_pids)]
            ty_layer = make_cut_layer(
                instance="fx_typography_1",
                pid=ty_pid,
                role="typography_overlay",
                framing=framing,
                x=0.46,
                y_override=0.42,
                plane_override="P1",
                z_override=0.42,
                alpha=0.84,
                blend="source-over",
            )
            ty_layer["scale"] = round(clamp(ty_layer["scale"], 0.24, 0.36), 4)
            stage_layers.append(ty_layer)

        # 6. Walking, Stairs, and Contact Assets from `weave/cast/man/` & `character_rigs_library.json`
        is_stairs_or_climb = any(k in combined_text for k in ("STAIR", "STEP", "CLIMB", "ASCENT", "LADDER", "FIRE ESCAPE", "VIADUCT", "HILL"))
        is_crouch_or_fall = any(k in combined_text for k in ("CROUCH", "KNEEL", "FALL", "FLOOR", "PRONE"))
        walking_and_action_assets = {
            "primary_rig_id": actor_layers[0]["rig_id"] if actor_layers else "poet_tracksuit_31",
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
            "stage_layers": stage_layers,
        }
        scenes_out.append(scene_plan)

    # Build compact part scale lookup table by sheet so downstream tools can also query any of the 6,265 cut pieces
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
        "version": "2.0.0",
        "generated_by": "shots/arena/parts/kit3/build_scene_collage_scales.py",
        "title": "WYGWYL Multiplane Set Architecture, World/Archive Layer Collage & Calibrated Scene Scale Plans",
        "audio_master": {
            "file": "film/suite_audio.mp3",
            "duration_sec": 1440.072,
        },
        "plane_architecture": {
            "P6": {"z": 6.0, "role": "Sky Canopy / World Vista Plate / Archive Torn-Paper Sky Wipe", "scale_range": [0.95, 1.05], "y_range": [0.95, 1.00]},
            "P5": {"z": 3.8, "role": "Distant Architecture / Horizon Vista / Archive Window & Screen Plate", "scale_range": [0.72, 0.90], "y_range": [0.78, 0.84]},
            "P4": {"z": 2.4, "role": "Segmented Architectural Elements (Left x=0.18 / Center x=0.50 / Right x=0.82)", "scale_range": [0.58, 0.78], "y_range": [0.86, 0.92]},
            "P3": {"z": 1.4, "role": "Grounded Set Furnishings (0.34–0.44), Medium Props (0.18–0.26) & Hand-Pinned Props (0.09–0.14)", "scale_range": [0.09, 0.44], "y_range": [0.64, 0.88]},
            "P2": {"z": 1.0, "role": "Hero & Supporting Cast Full Figures (Adult 0.52–0.60, Child 0.36–0.40, Crouched/Prone 0.26–0.38)", "scale_range": [0.26, 0.60], "y_range": [0.89, 0.93]},
            "P1": {"z": 0.45, "role": "Torn-Paper Foreground Wipes, Repoussoir & Painted FX / Typography", "scale_range": [0.24, 0.38], "y_range": [0.28, 0.92]},
        },
        "semantic_classes": SEMANTIC_CLASS_SPECS,
        "camera_framing_specs": CAMERA_FRAMING_SPECS,
        "stats": {
            "poem_count": 14,
            "scene_count": len(scenes_out),
            "total_catalog_sheets": len(sheets_by_id),
            "total_catalog_cut_parts": len(parts_by_id),
            "semantic_class_counts": class_counts,
        },
        "scenes": scenes_out,
        "scenes_by_id": {s["id"]: s for s in scenes_out},
        "catalog_scale_index": sheets_scale_index,
    }

    print(f"[4/5] Writing {OUTPUT_PATH} ...")
    OUTPUT_PATH.write_text(json.dumps(output_payload, indent=2))
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"  Wrote {OUTPUT_PATH} ({size_mb:.2f} MB)")

    print("[5/5] Running strict verification checks across all 80 scenes...")
    missing_files: List[str] = []
    scale_violations: List[str] = []
    headless_torso_actors: List[str] = []

    for sc in scenes_out:
        sid = sc["id"]
        aw = sc["audio_window"]
        if not (0.0 <= aw[0] < aw[1] <= 1440.1):
            scale_violations.append(f"{sid}: invalid audio_window {aw}")
        wb_file = sc["world_backdrop"]["backdrop_file"]
        if not (SHOTS_DIR / wb_file).exists():
            missing_files.append(f"{sid} world_backdrop: {wb_file}")
        ap_file = sc["archive_plate"]["poster_file"]
        if not (SHOTS_DIR / ap_file).exists():
            missing_files.append(f"{sid} archive_plate: {ap_file}")

        for lyr in sc["stage_layers"]:
            lf = lyr["file"]
            if not (SHOTS_DIR / lf).exists():
                missing_files.append(f"{sid} layer {lyr['instance']}: {lf}")
            s_cls = lyr["semantic_class"]
            sc_val = lyr["scale"]
            lo, hi = SEMANTIC_CLASS_SPECS[s_cls]["scale_range"]
            if not (lo - 1e-4 <= sc_val <= hi + 1e-4):
                scale_violations.append(f"{sid} {lyr['instance']} ({s_cls}): scale {sc_val} outside [{lo}, {hi}]")
            if lyr["plane"] == "P2" and lyr["sheet_id"] in BODY_PART_ONLY_SHEETS:
                headless_torso_actors.append(f"{sid} {lyr['instance']}: {lyr['part_id']}")

    print(f"  Scenes verified: {len(scenes_out)}/80")
    print(f"  Missing image files: {len(missing_files)}")
    print(f"  Physical scale violations: {len(scale_violations)}")
    print(f"  Headless torso vests on P2: {len(headless_torso_actors)}")

    if missing_files or scale_violations or headless_torso_actors:
        for err in (missing_files + scale_violations + headless_torso_actors)[:20]:
            print("   ERROR:", err)
        raise SystemExit(1)

    print("SUCCESS: All 80 scenes passed multiplane scale, world/archive collage, and full-figure verification!")


if __name__ == "__main__":
    main()
