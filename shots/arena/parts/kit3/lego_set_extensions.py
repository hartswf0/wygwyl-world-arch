#!/usr/bin/env python3
"""
lego_set_extensions.py
======================
Hand-Assembled 14-Poem Continuous World, True Shot-Distance Calibration &
Layered Door/Window Multiplane Footage Specification (`01.0` .. `14.6`).

Solves the three core visual pillars directed by the user:
  1. SEAMLESS SINGLE WORLD (Zero Fragmented Seams):
     - Every poem (`01` .. `14`) is hand-assembled as one continuous horizontal world
       where architectural & landscape joiners straddle the frame boundary (`x = 0.90..1.10`)
       and bridge smoothly into the next scene (`x = 1.45..1.60`) with soft feathered joins.
  2. TRUE SHOT SCALE & CAMERA DISTANCE (`shot_scale`, `camera_distance_m`, `focal_mm`, `stage_px_per_meter`):
     - Every scene (`01.0` .. `14.6`) is explicitly calibrated into one of 5 cinematic
       distance tiers so you immediately see how close or far each shot is:
         * `CLOSE_INTIMATE`        (2.6..4.2m,  50..85mm, 152..188 px/m)
         * `MEDIUM_STAGE`          (5.5..9.0m,  35..50mm, 104..134 px/m)
         * `WIDE_BOULEVARD`        (13.5..24m,  24..32mm,  62..88 px/m)
         * `EXTREME_WIDE_VISTA`    (36.0..72m,  18..24mm,  30..48 px/m)
         * `VERTIGO_AERIAL_COSMIC` (85.0..180m, 14..18mm,  14..26 px/m)
     - Piece scales in both the main frame and the inter-scene bridge match the shot's
       true distance (no giant close-up bedroom walls on 55m ocean/bay vistas!).
  3. LAYERED MULTIPLANE FOOTAGE INSIDE DOORS, WINDOWS & PORTALS (`aperture_footage`):
     - Every door, window, archway, rose window, television screen, standing mirror,
       and film-frame portal layers real poem video keyframes (`cel_assets/video/P01-001`..`P14-*`)
       and archival 16mm plates (`weave/archive/da69_frames/*.jpg`) BEHIND the opening
       with recessed jamb shadows, window mullions, glass sheen, and warm floor light spill.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


W_FRAME = 1280
W_EXT = 760
W_MOD = W_FRAME + W_EXT  # 2040 px per scene + side extension module
H_STAGE = 720
HYPERFLAT_FLOOR_Y = 614
HYPERFLAT_HORIZON_Y = 420


# ---------------------------------------------------------------------------
# 5 Canonical Camera Distance & Shot Scale Tiers
# ---------------------------------------------------------------------------
SHOT_SCALE_TIERS: Dict[str, Dict[str, Any]] = {
    "CLOSE_INTIMATE": {
        "tier_id": "CLOSE_INTIMATE",
        "short_label": "CLOSE-UP",
        "badge_color": "#f48fb1",
        "default_distance_m": 3.2,
        "default_focal_mm": 65,
        "default_ppm": 168.0,
        "actor_scale_mult": 1.28,
        "bridge_scale_mult": 1.00,
        "description": "Intimate close interior / threshold / table / window framing (2.6–4.2m)",
    },
    "MEDIUM_STAGE": {
        "tier_id": "MEDIUM_STAGE",
        "short_label": "MEDIUM STAGE",
        "badge_color": "#ffd54f",
        "default_distance_m": 6.8,
        "default_focal_mm": 40,
        "default_ppm": 116.0,
        "actor_scale_mult": 1.02,
        "bridge_scale_mult": 0.88,
        "description": "Full human-stage room / courtyard / catwalk / nave framing (5.5–9.0m)",
    },
    "WIDE_BOULEVARD": {
        "tier_id": "WIDE_BOULEVARD",
        "short_label": "WIDE BOULEVARD",
        "badge_color": "#64b5f6",
        "default_distance_m": 17.5,
        "default_focal_mm": 28,
        "default_ppm": 74.0,
        "actor_scale_mult": 0.78,
        "bridge_scale_mult": 0.68,
        "description": "Wide boulevard / viaduct / harbor promenade / colonnade framing (13.5–24m)",
    },
    "EXTREME_WIDE_VISTA": {
        "tier_id": "EXTREME_WIDE_VISTA",
        "short_label": "FAR VISTA",
        "badge_color": "#4dd0e1",
        "default_distance_m": 48.0,
        "default_focal_mm": 20,
        "default_ppm": 38.0,
        "actor_scale_mult": 0.52,
        "bridge_scale_mult": 0.46,
        "description": "Distant ocean shore / bay skyline / causeway / mountain horizon vista (36–72m)",
    },
    "VERTIGO_AERIAL_COSMIC": {
        "tier_id": "VERTIGO_AERIAL_COSMIC",
        "short_label": "AERIAL / ABYSS",
        "badge_color": "#ce93d8",
        "default_distance_m": 125.0,
        "default_focal_mm": 15,
        "default_ppm": 20.0,
        "actor_scale_mult": 0.40,
        "bridge_scale_mult": 0.38,
        "description": "Vertigo skyscraper drop / cosmic star-map / aerial city / void (85–180m)",
    },
}


def _vid(poem: int, shot: int, kf: int = 0) -> str:
    """Returns verified poem video keyframe path in `shots/cel_assets/video/`."""
    p_up = f"P{poem:02d}-{shot:03d}"
    p_lo = f"vid-p{poem:02d}-{shot:03d}-kf{kf:05d}_0"
    return f"cel_assets/video/{p_up}/out/{p_lo}/image.jpg"


def _da69(frame_num: int) -> str:
    """Returns verified archival 16mm frame path in `shots/weave/archive/da69_frames/`."""
    return f"weave/archive/da69_frames/{frame_num:04d}.jpg"


def _portal(
    footage_file: str,
    portal_kind: str = "door",
    aperture_box: Tuple[float, float, float, float] = (0.24, 0.16, 0.78, 0.96),
    mullions: bool = False,
    warm_spill: bool = True,
    alt_footage_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a structured `aperture_footage` spec for a door, window, arch, screen, or mirror."""
    return {
        "footage_file": footage_file,
        "alt_footage_file": alt_footage_file or _da69(211),
        "portal_kind": portal_kind,
        "aperture_box": [round(float(v), 3) for v in aperture_box],
        "mullions": bool(mullions),
        "warm_spill": bool(warm_spill),
    }


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
    aperture_footage: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Defines a Modular Set-Extension Piece placed across the seamless inter-scene bridge
    (`x in [0.90 .. 1.58]`, straddling or extending out of the `1280x720` frame into the
    `2040px` continuous poem tape).
    """
    is_portal = (
        aperture_footage is not None
        or "portal" in lego_role
        or "door" in lego_role
        or "window" in lego_role
    )
    d: Dict[str, Any] = {
        "part_id": part_id,
        "label": label,
        "plane": plane,
        "z": z,
        "x": x,
        "y": y,
        "scale": scale,
        "lego_role": lego_role,
        "anim_role": "portal_aperture" if is_portal else "static",
        "station_title": station_title,
        "flip": flip,
        "alpha": alpha,
        "is_set_extension": True,
        "preserve_raw_scale": preserve_raw_scale,
    }
    if aperture_footage is not None:
        d["aperture_footage"] = aperture_footage
    return d


# ---------------------------------------------------------------------------
# Hand-Calibrated Shot Distance & Scale Profiles for All 90 Scenes (`01.0`..`14.6`)
# ---------------------------------------------------------------------------
def _sp(
    tier: str,
    dist_m: float,
    focal_mm: int,
    ppm: float,
    hor_y: float = 0.58,
    note: str = "",
) -> Dict[str, Any]:
    tmeta = SHOT_SCALE_TIERS[tier]
    # Compute smooth actor & prop scale multiplier relative to standard 116 px/m medium stage
    actor_mult = round(max(0.36, min(1.36, (ppm / 116.0) ** 0.72)), 3)
    return {
        "shot_scale": tier,
        "short_label": tmeta["short_label"],
        "badge_color": tmeta["badge_color"],
        "camera_distance_m": round(float(dist_m), 1),
        "focal_mm": int(focal_mm),
        "stage_px_per_meter": round(float(ppm), 1),
        "horizon_y_norm": round(float(hor_y), 3),
        "actor_scale_mult": actor_mult,
        "distance_readout": f"{tmeta['short_label']} · {dist_m:.1f}m ({focal_mm}mm · {int(round(ppm))} px/m)",
        "director_note": note,
    }


SCENE_SHOT_PROFILES: Dict[str, Dict[str, Any]] = {
    # POEM 01 · OUT OF LIFE (Intimate Bedroom -> Hallway -> Medium Fire-Escape -> Vertigo 140m Drop -> Ballroom -> Trapdoor)
    "01.0": _sp("CLOSE_INTIMATE", 3.2, 65, 168.0, 0.56, "Close bedroom interior with flickering TV & sash window"),
    "01.1": _sp("CLOSE_INTIMATE", 3.8, 55, 154.0, 0.56, "Close apartment corridor & open drawers to fire-escape window"),
    "01.2": _sp("MEDIUM_STAGE", 6.8, 40, 118.0, 0.58, "Medium exterior fire-escape catwalk bridging to stone gable door"),
    "01.3": _sp("VERTIGO_AERIAL_COSMIC", 140.0, 14, 18.0, 0.50, "Vertigo 140m vertical freefall down skyscraper canyon"),
    "01.4": _sp("MEDIUM_STAGE", 7.4, 38, 112.0, 0.58, "Medium 1940s chandelier ballroom waltz floor"),
    "01.5": _sp("MEDIUM_STAGE", 6.2, 42, 122.0, 0.60, "Medium-close ballroom trapdoor opening into the abyss"),

    # POEM 02 · FLASHING LIGHTS (Distant Void -> Close 1:08 AM Bedroom -> Medium Driveway -> Close Living Room -> Rain Window -> Wide Overseer Bridge)
    "02.0": _sp("EXTREME_WIDE_VISTA", 46.0, 20, 38.0, 0.54, "Far submerged void corridor with sweeping headlights"),
    "02.1": _sp("CLOSE_INTIMATE", 3.1, 65, 170.0, 0.56, "Intimate 1:08 AM bedside & standing mirror"),
    "02.2": _sp("MEDIUM_STAGE", 7.8, 35, 108.0, 0.58, "Medium 1990s family sedan on rain-slicked driveway"),
    "02.3": _sp("CLOSE_INTIMATE", 3.5, 58, 160.0, 0.57, "Close 1990s floral living room & pencil-marked doorpost"),
    "02.4": _sp("CLOSE_INTIMATE", 3.4, 60, 162.0, 0.56, "Close rain-streaked window looking out to nocturnal skyline"),
    "02.5": _sp("WIDE_BOULEVARD", 18.5, 28, 70.0, 0.58, "Wide nocturnal Overseer highway bridge & distant towers"),

    # POEM 03 · HOW TO BREAK OFF AN ENGAGEMENT (Medium Chapel -> Nave -> Close Side Doors -> Wide Storm Exterior -> Far Ruined Shore)
    "03.0": _sp("MEDIUM_STAGE", 7.5, 38, 110.0, 0.58, "Medium Gothic chapel facade & cafe-racer arrival"),
    "03.1": _sp("MEDIUM_STAGE", 6.6, 42, 118.0, 0.58, "Medium chapel nave arcade, pews & rose window"),
    "03.2": _sp("CLOSE_INTIMATE", 3.6, 55, 156.0, 0.58, "Close rusticated stone chapel side doors & threshold"),
    "03.3": _sp("WIDE_BOULEVARD", 16.0, 28, 76.0, 0.58, "Wide storm-lashed chapel exterior & cracked gable"),
    "03.4": _sp("EXTREME_WIDE_VISTA", 42.0, 21, 42.0, 0.56, "Distant collapsed chapel ruins along the tidal shore"),
    "03.5": _sp("EXTREME_WIDE_VISTA", 52.0, 19, 34.0, 0.55, "Extreme wide salt-shore causeway & distant viaduct horizon"),

    # POEM 04 · NEVERMORE (Far Ash Shore -> Wide Viaduct Canal -> Close Incline Hands -> Medium Bridge Booth -> Wide Garden Boulevard -> Far Starfield -> Wide Perimeter)
    "04.0": _sp("EXTREME_WIDE_VISTA", 48.0, 20, 36.0, 0.55, "Distant ash shore & three-arch stone viaduct across bay"),
    "04.1": _sp("WIDE_BOULEVARD", 15.5, 28, 78.0, 0.58, "Wide stone viaduct pier (+4m datum) & canal arches"),
    "04.2": _sp("CLOSE_INTIMATE", 3.4, 60, 162.0, 0.58, "Close incline trail ledge where Poet puts on his hands"),
    "04.3": _sp("MEDIUM_STAGE", 6.5, 40, 118.0, 0.58, "Medium viaduct bridge deck & illuminated glass phone booth"),
    "04.4": _sp("WIDE_BOULEVARD", 17.0, 28, 74.0, 0.58, "Wide moonlit night-garden boulevard with trees & lamps"),
    "04.5": _sp("EXTREME_WIDE_VISTA", 44.0, 20, 40.0, 0.54, "Far starfield ridge & stone archway under the cosmos"),
    "04.6": _sp("WIDE_BOULEVARD", 16.5, 28, 75.0, 0.58, "Wide perimeter chain-link boulevard bridging into Poem 05"),

    # POEM 05 · BLOODLINES (Wide Perimeter Boulevard -> Cosmic Star Field -> Medium Basement -> Far Globe Parade -> Close Hearth Door -> Far Causeway)
    "05.0": _sp("WIDE_BOULEVARD", 16.0, 28, 76.0, 0.58, "Wide perimeter fence, palm trees & red-halo street lamps"),
    "05.1": _sp("VERTIGO_AERIAL_COSMIC", 95.0, 16, 24.0, 0.52, "Cosmic star-naming field under vast wheeling constellations"),
    "05.2": _sp("MEDIUM_STAGE", 5.8, 45, 126.0, 0.58, "Medium-close humid cinderblock basement & high window"),
    "05.3": _sp("EXTREME_WIDE_VISTA", 45.0, 20, 38.0, 0.55, "Far curved-globe parade lawn & monumental winged marble gate"),
    "05.4": _sp("CLOSE_INTIMATE", 3.5, 58, 158.0, 0.58, "Close ancestral hearth fireplace, table & open doorway"),
    "05.5": _sp("EXTREME_WIDE_VISTA", 50.0, 19, 35.0, 0.55, "Extreme wide golden-brick causeway approaching Atlantis Gate"),

    # POEM 06 · RESURRECTING ATLANTIS (Far Bay Skyline -> Far Causeway -> Far Waterfront -> Medium Crystal Hall -> Wide Forum -> Medium Alley -> Wide Teahouse)
    "06.0": _sp("EXTREME_WIDE_VISTA", 58.0, 18, 32.0, 0.54, "Extreme wide Atlantis citadel bay skyline & Light Gate"),
    "06.1": _sp("EXTREME_WIDE_VISTA", 42.0, 21, 42.0, 0.56, "Distant yellow-brick causeway & Venetian-Atlantis colonnade"),
    "06.2": _sp("EXTREME_WIDE_VISTA", 46.0, 20, 38.0, 0.55, "Far terraced Atlantis hillside skyline & waterfront steps"),
    "06.3": _sp("MEDIUM_STAGE", 6.8, 40, 116.0, 0.58, "Medium Crystal Tree Hall & twin-arched colonnade"),
    "06.4": _sp("WIDE_BOULEVARD", 18.0, 26, 72.0, 0.58, "Wide circular Atlantis forum & terracotta arched wings"),
    "06.5": _sp("MEDIUM_STAGE", 6.4, 42, 120.0, 0.58, "Medium-close narrow cobblestone street & warm alley bulbs"),
    "06.6": _sp("WIDE_BOULEVARD", 15.0, 30, 80.0, 0.58, "Wide harbor teahouse veranda & waterfront boathouse"),

    # POEM 07 · DJ TURN ME UP (Medium Container Club -> Close DJ Booth -> Close Red Shaft -> Wide Club Plaza -> Wide Three-Roads -> Medium Alley -> Wide Canal)
    "07.0": _sp("MEDIUM_STAGE", 7.2, 38, 114.0, 0.58, "Medium industrial container club stage & speaker stacks"),
    "07.1": _sp("CLOSE_INTIMATE", 3.3, 62, 165.0, 0.57, "Close DJ turntable console, VU meters & neon booth"),
    "07.2": _sp("CLOSE_INTIMATE", 3.6, 56, 156.0, 0.58, "Close red-lit bass shaft & octagonal bulkhead portal"),
    "07.3": _sp("WIDE_BOULEVARD", 15.5, 28, 78.0, 0.58, "Wide brick club facade with three glowing portal doorways"),
    "07.4": _sp("WIDE_BOULEVARD", 21.0, 24, 64.0, 0.56, "Wide Three-Roads perspective highway & curved street lamps"),
    "07.5": _sp("MEDIUM_STAGE", 6.5, 40, 118.0, 0.58, "Medium after-hours alley & glowing NEW SINGLE marquee"),
    "07.6": _sp("WIDE_BOULEVARD", 17.5, 28, 72.0, 0.58, "Wide rain-soaked canal promenade with palms & street lamps"),

    # POEM 08 · NEWLY SINGLE (Aerial Rooftop -> Medium Marquee -> Aerial Soul Over Atlantis -> Close Ice Basins -> Wide Harbor Mist -> Far Equator Horizon)
    "08.0": _sp("VERTIGO_AERIAL_COSMIC", 88.0, 16, 26.0, 0.52, "High rooftop club terrace & broadcast towers over city abyss"),
    "08.1": _sp("MEDIUM_STAGE", 6.8, 40, 116.0, 0.58, "Medium NEW SINGLE brick theater facade & glowing lobby doors"),
    "08.2": _sp("VERTIGO_AERIAL_COSMIC", 115.0, 15, 21.0, 0.48, "Aerial soul floating above moonlit clouds & cinema roof"),
    "08.3": _sp("CLOSE_INTIMATE", 3.5, 58, 158.0, 0.58, "Close salted ice-water stone basins & reflecting channel"),
    "08.4": _sp("WIDE_BOULEVARD", 17.0, 28, 74.0, 0.58, "Wide harbor mist promenade with warehouse row & palms"),
    "08.5": _sp("EXTREME_WIDE_VISTA", 54.0, 19, 34.0, 0.54, "Far equator plain & distant Atlantis spire horizon"),

    # POEM 09 · YET, HEARD (Medium Club Sidewalk -> Wide Harbor Boulevard -> Close Mother's Room -> Close Phone Booth Call -> Wide Inner Harbor -> Wide Quay)
    "09.0": _sp("MEDIUM_STAGE", 6.6, 40, 118.0, 0.58, "Medium neon club sidewalk portals & wet reflections"),
    "09.1": _sp("WIDE_BOULEVARD", 18.0, 26, 72.0, 0.58, "Wide harborfront building row, palms & pier lamps"),
    "09.2": _sp("CLOSE_INTIMATE", 3.4, 60, 162.0, 0.57, "Close Mother's living room, suitcases & window portal"),
    "09.3": _sp("CLOSE_INTIMATE", 3.0, 68, 174.0, 0.57, "Intimate close-up of glass phone booth & Mother's window"),
    "09.4": _sp("WIDE_BOULEVARD", 19.5, 25, 68.0, 0.57, "Wide inner-harbor warehouses, iron crane & stone quay"),
    "09.5": _sp("WIDE_BOULEVARD", 16.0, 28, 76.0, 0.58, "Wide neon street facade & mosaic Shadowpool archway"),

    # POEM 10 · MAGIC RIDE (Medium Shadowpool -> Wide Neon Overpass -> Far Mountain Road -> Wide Solar Avenue -> Wide Viaduct -> Far Dawn Tree)
    "10.0": _sp("MEDIUM_STAGE", 6.8, 40, 116.0, 0.58, "Medium mosaic Shadowpool archways & golden pool reflections"),
    "10.1": _sp("WIDE_BOULEVARD", 16.5, 28, 75.0, 0.58, "Wide Atlantis avenue overpass & cafe-racer motorcycle"),
    "10.2": _sp("EXTREME_WIDE_VISTA", 48.0, 20, 36.0, 0.55, "Far canyon rock pillars & mountain highway ridge"),
    "10.3": _sp("WIDE_BOULEVARD", 15.0, 30, 80.0, 0.58, "Wide sunlit stone avenue archway & motorcycle in full stride"),
    "10.4": _sp("WIDE_BOULEVARD", 18.0, 26, 72.0, 0.58, "Wide Out-of-Atlantis viaduct railing, dawn trees & lamps"),
    "10.5": _sp("EXTREME_WIDE_VISTA", 44.0, 20, 40.0, 0.55, "Distant spreading Dawn Tree on mountain horizon & temple plinth"),

    # POEM 11 · NEW DAY (Wide Ruined Steps -> Wide Rising Colonnade -> Medium Mirror Hall -> Medium Completed Temple -> Close Infinity Pool -> Medium Portico)
    "11.0": _sp("WIDE_BOULEVARD", 17.0, 28, 74.0, 0.58, "Wide ancient ruined stone steps & first marble foundation course"),
    "11.1": _sp("WIDE_BOULEVARD", 15.5, 28, 78.0, 0.58, "Wide rising marble temple colonnade & turquoise pool"),
    "11.2": _sp("MEDIUM_STAGE", 7.0, 38, 114.0, 0.58, "Medium five-arch marble Mirror Hall arcade"),
    "11.3": _sp("MEDIUM_STAGE", 7.4, 38, 112.0, 0.58, "Medium completed marble temple pediment & New Day clocktower"),
    "11.4": _sp("CLOSE_INTIMATE", 3.8, 55, 152.0, 0.58, "Close reflecting infinity pool, columns & architect journal"),
    "11.5": _sp("MEDIUM_STAGE", 6.8, 40, 116.0, 0.58, "Medium sunlit temple portico & sanctuary arch into Poem 12"),

    # POEM 12 · REUNION (Medium Temple Backroom -> Wide Olive Grove -> Far Afterlife Threshold -> Medium Hourglass Hall -> Wide Forest -> Wide Terrace -> Wide Cafe)
    "12.0": _sp("MEDIUM_STAGE", 6.5, 40, 118.0, 0.58, "Medium temple hall colonnade & backroom doorway threshold"),
    "12.1": _sp("WIDE_BOULEVARD", 17.5, 28, 72.0, 0.58, "Wide Mediterranean olive grove balustrade & fluted columns"),
    "12.2": _sp("EXTREME_WIDE_VISTA", 40.0, 22, 44.0, 0.56, "Distant afterlife sanctuary horizon & vaulted threshold"),
    "12.3": _sp("MEDIUM_STAGE", 6.2, 42, 122.0, 0.58, "Medium sanctuary arcade & monumental burning hourglass"),
    "12.4": _sp("WIDE_BOULEVARD", 16.0, 28, 76.0, 0.58, "Wide western olive & cypress forest canopy"),
    "12.5": _sp("WIDE_BOULEVARD", 18.5, 26, 70.0, 0.58, "Wide stone shore-terrace staircase & wet flagstone landing"),
    "12.6": _sp("WIDE_BOULEVARD", 15.0, 30, 80.0, 0.58, "Wide harbor promenade approaching the Corner Cafe"),

    # POEM 13 · HOW TO WIN MY HEART (Wide Cafe Exterior -> Close Bistro Table -> Medium Sleepdam -> Far Drowned Atrium -> Wide Poppy Meadow -> Medium Window -> Wide Quay)
    "13.0": _sp("WIDE_BOULEVARD", 14.5, 30, 82.0, 0.58, "Wide teal Corner Cafe storefront & brick gable house"),
    "13.1": _sp("CLOSE_INTIMATE", 2.9, 70, 178.0, 0.57, "Intimate close-up of marble bistro table, espresso cup & cafe window"),
    "13.2": _sp("MEDIUM_STAGE", 7.6, 36, 110.0, 0.58, "Medium concrete Sleepdam spillway, steel catwalk & five letters"),
    "13.3": _sp("EXTREME_WIDE_VISTA", 42.0, 21, 42.0, 0.56, "Distant drowned atrium mullioned wall & flooded horizon"),
    "13.4": _sp("WIDE_BOULEVARD", 16.5, 28, 75.0, 0.58, "Wide scarlet poppy & lavender meadow under garden chapel arch"),
    "13.5": _sp("MEDIUM_STAGE", 6.0, 42, 124.0, 0.58, "Medium brick gabled window & waiting bistro table"),
    "13.6": _sp("WIDE_BOULEVARD", 18.0, 26, 72.0, 0.58, "Wide harbor quay stone seawall, gas lamps & rowboat"),

    # POEM 14 · OUT OF LIFE FINALE (Far Harbor Citadel -> Cosmic Void Reel -> Medium Memory Gallery -> Cosmic Graytone -> Close Vintage Door -> Medium Ballroom -> Close Genesis Room)
    "14.0": _sp("EXTREME_WIDE_VISTA", 56.0, 18, 33.0, 0.54, "Extreme wide island citadel of Atlantis, breakwater & sailboat"),
    "14.1": _sp("VERTIGO_AERIAL_COSMIC", 92.0, 16, 25.0, 0.52, "Cosmic black void with floating 35mm filmstrip portals & distant door"),
    "14.2": _sp("MEDIUM_STAGE", 6.6, 40, 118.0, 0.58, "Medium Life-Reel gallery wall, gramophone & vintage door #2"),
    "14.3": _sp("VERTIGO_AERIAL_COSMIC", 98.0, 16, 24.0, 0.52, "Cosmic graytone 35mm sprocket memory void & sanctuary portal"),
    "14.4": _sp("CLOSE_INTIMATE", 3.2, 65, 168.0, 0.57, "Intimate close-up of the Vintage Wooden Door swinging wide open with light"),
    "14.5": _sp("MEDIUM_STAGE", 7.0, 38, 114.0, 0.58, "Medium 1940s Grand Ballroom chandelier waltz & timber archway"),
    "14.6": _sp("CLOSE_INTIMATE", 3.3, 62, 166.0, 0.56, "Intimate Genesis bedroom return — dresser, flickering TV & dawn sash window"),
}


# ---------------------------------------------------------------------------
# In-Frame Door, Window, Arch, TV & Mirror Layered Footage Overrides
# Keyed by `(scene_key, part_id)` or `part_id` so in-frame doors/windows also
# display real multiplane footage inside their openings!
# ---------------------------------------------------------------------------
IN_FRAME_PORTAL_FOOTAGE: Dict[str, Dict[str, Any]] = {
    # Poem 01 in-frame windows, TV & trapdoor
    "01.0:01.props.window__p01": _portal(_vid(1, 2, 0), "window", (0.18, 0.14, 0.82, 0.86), mullions=True, warm_spill=True, alt_footage_file=_vid(1, 3, 12)),
    "01.0:01.props.room__p18": _portal(_vid(1, 1, 12), "screen", (0.16, 0.12, 0.84, 0.62), mullions=False, warm_spill=True, alt_footage_file=_da69(271)),
    "01.1:01.props.window__p01": _portal(_vid(1, 4, 0), "window", (0.18, 0.14, 0.82, 0.86), mullions=True, warm_spill=True),
    "01.2:01.props.window__p01": _portal(_vid(1, 5, 0), "window", (0.18, 0.14, 0.82, 0.86), mullions=True, warm_spill=True),
    "01.4:14.set.vintage_party__p03": _portal(_vid(1, 9, 0), "arch", (0.22, 0.18, 0.78, 0.96), mullions=False, warm_spill=True),
    "01.5:01.props.trapdoor__p12": _portal(_vid(1, 11, 0), "door", (0.18, 0.20, 0.82, 0.84), mullions=False, warm_spill=False),
    # Poem 02 mirrors & windows
    "02.0:02.props.mirror-phone-rings__p14": _portal(_vid(2, 1, 0), "mirror", (0.20, 0.14, 0.80, 0.86), mullions=False, warm_spill=True),
    "02.1:02.props.mirror-phone-rings__p04": _portal(_vid(2, 3, 0), "mirror", (0.20, 0.14, 0.80, 0.86), mullions=False, warm_spill=True),
    # Poem 03 rose window
    "03.1:03.hero.chapel.interior-states__p12": _portal(_vid(3, 3, 0), "window", (0.18, 0.18, 0.82, 0.82), mullions=True, warm_spill=True),
    # Poem 04 phone booth
    "04.3:04.props.booth__p01": _portal(_vid(4, 7, 0), "window", (0.20, 0.14, 0.80, 0.88), mullions=True, warm_spill=True),
    # Poem 05 ancestral doors
    "05.4:05.props.doors__p01": _portal(_vid(5, 7, 0), "door", (0.20, 0.12, 0.80, 0.95), mullions=False, warm_spill=True),
    "05.4:05.props.doors__p02": _portal(_vid(5, 8, 0), "door", (0.20, 0.12, 0.80, 0.95), mullions=False, warm_spill=True),
    "05.4:05.props.doors__p03": _portal(_vid(5, 9, 0), "door", (0.20, 0.12, 0.80, 0.95), mullions=False, warm_spill=True),
    # Poem 07 club neon arch
    "07.3:07.props.club-lights__p03": _portal(_vid(7, 6, 0), "arch", (0.22, 0.18, 0.78, 0.95), mullions=False, warm_spill=True),
    # Poem 09 porthole
    "09.3:09.props.sunken-ruins__p05": _portal(_vid(9, 7, 0), "window", (0.20, 0.20, 0.80, 0.80), mullions=True, warm_spill=True),
    # Poem 14 freestanding vintage doors & Genesis TV
    "14.1:14.props.door__p02": _portal(_vid(14, 2, 0), "door", (0.20, 0.10, 0.80, 0.95), mullions=False, warm_spill=True),
    "14.3:14.props.door__p11": _portal(_vid(14, 5, 0), "door", (0.20, 0.10, 0.80, 0.95), mullions=False, warm_spill=True),
    "14.4:14.props.door__p13": _portal(_vid(14, 7, 0), "door", (0.18, 0.10, 0.82, 0.96), mullions=False, warm_spill=True, alt_footage_file=_vid(1, 9, 0)),
    "14.6:01.props.room__p18": _portal(_vid(1, 1, 0), "screen", (0.16, 0.12, 0.84, 0.62), mullions=False, warm_spill=True),
}


# ---------------------------------------------------------------------------
# Reusable Distance-Calibrated Bridge Builders
# ---------------------------------------------------------------------------
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
    floor_y: float = 0.89,
    dist_mult: float = 0.82,
    portal_id: Optional[str] = None,
    portal_label: Optional[str] = None,
    portal_footage: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Builds a seamless, distance-calibrated Wide Boulevard Tape bridge (`14..24m` camera distance):
      - Straddling fence/wall joiner at `x = 0.98` + repeating bays at `x = 1.24, 1.48`
        so there is NEVER a vertical gap or cut at `x = 1.00` (`1280px`) or `x = 1.59` (`2040px`)!
      - Rhythmically spaced trees (`x = 1.03, 1.19, 1.36, 1.52`) scaled by `dist_mult`
      - Alternating street lamps (`x = 1.11, 1.28, 1.45`)
      - Optional window/door portal with layered video footage
      - Continuous foreground curb/hedge strip along `floor_y`
    """
    t0 = tree_ids[0]
    t1 = tree_ids[1 % len(tree_ids)]
    t2 = tree_ids[2 % len(tree_ids)]
    t3 = tree_ids[3 % len(tree_ids)]
    f_sc = round(0.42 * dist_mult, 3)
    t_sc1 = round(0.68 * dist_mult, 3)
    t_sc2 = round(0.62 * dist_mult, 3)
    l_sc = round(0.54 * dist_mult, 3)
    c_sc = round(0.20 * dist_mult, 3)

    items = [
        # Straddling fence/wall bays across `x = 0.98 .. 1.50` for seamless continuity
        X(fence_id, f"{fence_label} (Frame Join)", "P4", 2.48, 1.02, floor_y, f_sc, "boulevard_fence", station_title),
        X(fence_id, f"{fence_label} (Mid Span)", "P4", 2.46, 1.26, floor_y, f_sc, "boulevard_fence", None),
        X(fence_id, f"{fence_label} (Next Frame Join)", "P4", 2.46, 1.49, floor_y, f_sc, "boulevard_fence", None),
        # Rhythmically spaced boulevard trees scaled to wide-shot distance
        X(t0, f"{tree_label} #1", "P4", 2.38, 1.04, floor_y, t_sc1, "boulevard_tree", None),
        X(t1, f"{tree_label} #2", "P4", 2.36, 1.20, floor_y, t_sc2, "boulevard_tree", None),
        X(t2, f"{tree_label} #3", "P4", 2.38, 1.37, floor_y, t_sc1, "boulevard_tree", None),
        X(t3, f"{tree_label} #4", "P4", 2.36, 1.53, floor_y, t_sc2, "boulevard_tree", None),
        # Alternating street lamps
        X(lamp_id, f"{lamp_label} West", "P3", 1.48, 1.12, floor_y, l_sc, "boulevard_lamp", None),
        X(lamp_id, f"{lamp_label} Center", "P3", 1.48, 1.29, floor_y, l_sc, "boulevard_lamp", None),
        X(lamp_id, f"{lamp_label} East", "P3", 1.48, 1.46, floor_y, l_sc, "boulevard_lamp", None),
        # Continuous ground curb / hedge strip tying the boulevard base together
        X(curb_id, curb_label, "P2", 1.06, 1.15, floor_y + 0.02, c_sc, "ground_curb", None),
        X(curb_id, f"{curb_label} East", "P2", 1.06, 1.44, floor_y + 0.02, c_sc, "ground_curb", None),
    ]
    if portal_id and portal_footage:
        items.insert(
            3,
            X(
                portal_id,
                portal_label or "Boulevard Window Portal",
                "P4",
                2.40,
                1.33,
                floor_y,
                round(0.44 * dist_mult, 3),
                "gable_portal_cap",
                portal_label,
                aperture_footage=_portal(portal_footage, "window", (0.22, 0.18, 0.78, 0.88), mullions=True, warm_spill=True),
            ),
        )
    return items


def catwalk_gable_wall_extension(
    catwalk_deck_id: str,
    catwalk_truss_id: str,
    wall_hole_id: str,
    wall_label: str,
    gable_portal_id: str,
    gable_label: str,
    station_title: str,
    door_footage: str,
    window_footage: Optional[str] = None,
    floor_y: float = 0.90,
) -> List[Dict[str, Any]]:
    """
    Builds the Medium-Stage "Catwalk -> Wall with Doorway Hole (with layered video footage!) -> Stone Gable Portal"
    outside-the-frame Lego assembly (`media_1793295948484_14eeb0d8.png`), with straddling catwalk joiners at `x = 1.01`
    so the transition out of the frame is 100% seamless.
    """
    return [
        X(
            wall_hole_id,
            wall_label,
            "P4",
            2.42,
            1.28,
            floor_y,
            0.94,
            "wall_with_door_hole",
            station_title,
            aperture_footage=_portal(
                door_footage,
                "door",
                (0.34, 0.18, 0.80, 0.96),
                mullions=False,
                warm_spill=True,
                alt_footage_file=window_footage or _da69(331),
            ),
        ),
        X(
            gable_portal_id,
            gable_label,
            "P3",
            1.36,
            1.40,
            floor_y,
            1.18,
            "gable_portal_cap",
            f"Enter {gable_label}",
            aperture_footage=_portal(
                window_footage or door_footage,
                "arch",
                (0.28, 0.26, 0.72, 0.95),
                mullions=False,
                warm_spill=True,
            ),
        ),
        X(catwalk_truss_id, "Straddling Catwalk Support Truss", "P3", 1.48, 1.02, floor_y + 0.01, 0.34, "span_truss", None),
        X(catwalk_deck_id, "Straddling Iron Catwalk Span", "P2", 1.08, 1.05, floor_y - 0.02, 0.22, "span_deck", None),
    ]


# ---------------------------------------------------------------------------
# Hand-Assembled 14-Poem Continuous World & Layered Door/Window Extensions (`01.0`..`14.6`)
# Every scene's bridge is scaled to its exact `SCENE_SHOT_PROFILES[skey]` distance
# and layers real video footage inside its doors, windows, and portals!
# ---------------------------------------------------------------------------
SCENE_LEGO_EXTENSIONS: Dict[str, List[Dict[str, Any]]] = {
    # =======================================================================
    # POEM 01 · OUT OF LIFE
    # Hand Assembly: Close Bedroom (3.2m) -> Close Corridor (3.8m) -> Medium Catwalk & Stone Gable (6.8m)
    #                -> Vertigo 140m Skyscraper Canyon -> Medium Ballroom (7.4m) -> Medium Trapdoor Abyss (6.2m)
    # =======================================================================
    "01.0": [
        X("01.hero.severn__p07", "Straddling Bedroom Baseboard Moulding", "P3", 1.50, 1.02, 0.91, 0.16, "ground_curb", None),
        X(
            "12.set.temple_backroom__p01",
            "Close Bedroom Plaster Wall & Open Doorway to Hall",
            "P4",
            2.44,
            1.24,
            0.90,
            0.88,
            "wall_with_door_hole",
            "Bedroom Doorway Threshold",
            aperture_footage=_portal(_vid(1, 3, 0), "door", (0.34, 0.18, 0.80, 0.96), mullions=False, warm_spill=True),
        ),
        X(
            "01.props.window__p13",
            "Close Sash Window & Fire-Escape Balcony",
            "P3",
            1.42,
            1.47,
            0.78,
            0.46,
            "gable_portal_cap",
            "Window to the Night Alley",
            aperture_footage=_portal(_vid(1, 4, 12), "window", (0.20, 0.14, 0.80, 0.84), mullions=True, warm_spill=True),
        ),
        X("01.props.room__p01", "Hallway Wooden Dresser by Threshold", "P3", 1.38, 1.08, 0.89, 0.28, "furniture_anchor", None),
    ],
    "01.1": [
        X("01.hero.catwalk__p03", "Straddling Iron Fire-Escape Landing", "P3", 1.44, 1.03, 0.88, 0.20, "span_deck", None),
        X(
            "01.hero.severn__p02",
            "Close Tenement Wall with Lit Window & Door Holes",
            "P4",
            2.44,
            1.24,
            0.90,
            0.84,
            "wall_with_door_hole",
            "Tenement Corridor Wall",
            aperture_footage=_portal(_vid(1, 5, 0), "window", (0.26, 0.18, 0.76, 0.90), mullions=True, warm_spill=True),
        ),
        X(
            "01.hero.severn__p03",
            "Recessed Red Corridor Doorway Portal",
            "P3",
            1.40,
            1.47,
            0.90,
            0.68,
            "gable_portal_cap",
            "Corridor Exit Portal",
            aperture_footage=_portal(_vid(1, 6, 0), "door", (0.22, 0.14, 0.78, 0.95), mullions=False, warm_spill=True),
        ),
        X("01.hero.severnescape__p04", "Iron Fire-Escape Balcony Grate", "P2", 1.08, 1.36, 0.87, 0.26, "span_deck", None),
    ],
    "01.2": catwalk_gable_wall_extension(
        catwalk_deck_id="01.hero.catwalk__p03",
        catwalk_truss_id="01.hero.catwalk__p05",
        wall_hole_id="12.set.temple_backroom__p01",
        wall_label="Extended Plaster Wall with Open Doorway Hole",
        gable_portal_id="03.hero.chapel__p01",
        gable_label="Stone Gabled Roof & Doorway Portal",
        station_title="Catwalk to the Stone Gable Door",
        door_footage=_vid(1, 7, 0),
        window_footage=_vid(1, 8, 12),
        floor_y=0.90,
    ),
    # 01.3 is a 140m VERTIGO AERIAL DROP: use distant vertical skyscraper canyon spires & skylight portal below (NOT a room wall!)
    "01.3": [
        X("01.fx.haze-words__p05", "High-Altitude Nocturnal Cloud Layer", "P5", 3.84, 1.24, 0.36, 0.22, "vista_backing", None),
        X("01.set.city_fall_void__p03", "Distant Skyscraper Canyon Spire West (140m Drop)", "P5", 3.80, 1.08, 0.84, 0.36, "vista_backing", "Spire Canyon Abyss"),
        X("01.set.city_fall_void__p04", "Distant Skyscraper Canyon Shaft East (140m Drop)", "P4", 2.46, 1.28, 0.88, 0.38, "span_deck", None),
        X(
            "14.set.vintage_party__p03",
            "Distant Illuminated Ballroom Skylight Below the Drop",
            "P4",
            2.38,
            1.48,
            0.90,
            0.42,
            "gable_portal_cap",
            "Skylight Into the Ballroom",
            aperture_footage=_portal(_vid(1, 9, 0), "arch", (0.24, 0.20, 0.76, 0.94), mullions=True, warm_spill=True),
        ),
        X("01.props.chandeliers__p27", "Miniature Ballroom Chandelier Glimpsed Below", "P3", 1.40, 1.48, 0.56, 0.16, "ceiling_fixture", None),
    ],
    "01.4": [
        X("14.set.vintage_party__p04", "Straddling Polished Parquet Waltz Floor", "P3", 1.48, 1.06, 0.92, 0.22, "span_deck", None),
        X(
            "14.set.vintage_party__p02",
            "1940s Wood-Panelled Ballroom Wall & Illuminated Window",
            "P4",
            2.44,
            1.25,
            0.90,
            0.78,
            "wall_with_door_hole",
            "Ballroom Side Gallery",
            aperture_footage=_portal(_vid(1, 10, 0), "window", (0.24, 0.16, 0.78, 0.88), mullions=True, warm_spill=True),
        ),
        X("14.set.vintage_party__p01", "Ballroom Coffered Ceiling Cornice", "P4", 2.40, 1.26, 0.32, 0.20, "roof_cornice", None),
        X(
            "14.set.vintage_party__p03",
            "Timber Ballroom Threshold Portal",
            "P3",
            1.38,
            1.47,
            0.90,
            0.76,
            "gable_portal_cap",
            "Archway to the Trapdoor",
            aperture_footage=_portal(_vid(1, 11, 0), "arch", (0.24, 0.18, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
    ],
    "01.5": [
        X("01.hero.catwalk__p04", "Straddling Iron Railing Along the Abyss Rim", "P2", 1.08, 1.03, 0.89, 0.20, "span_deck", None),
        X(
            "01.props.trapdoor__p01",
            "Parquet Floor Slab with Open Abyss Portal",
            "P3",
            1.46,
            1.20,
            0.91,
            0.48,
            "wall_with_door_hole",
            "The Abyss Threshold",
            aperture_footage=_portal(_vid(1, 12, 0), "door", (0.22, 0.20, 0.78, 0.86), mullions=False, warm_spill=False),
        ),
        X("02.set.black_void__p01", "Receding Nocturnal Void Wall West", "P4", 2.44, 1.36, 0.90, 0.56, "wall_bay", None),
        X(
            "02.hero.drowned-light__p07",
            "Submerged Portal Arch Into Poem 02",
            "P3",
            1.38,
            1.50,
            0.90,
            0.62,
            "gable_portal_cap",
            "Into Poem 02 · Flashing Lights",
            aperture_footage=_portal(_vid(2, 1, 0), "arch", (0.24, 0.18, 0.76, 0.94), mullions=False, warm_spill=True),
        ),
    ],

    # =======================================================================
    # POEM 02 · FLASHING LIGHTS
    # Hand Assembly: Far Submerged Void (46m) -> Close 1:08 AM Bedroom (3.1m) -> Medium Driveway (7.8m)
    #                -> Close 1990s Living Room (3.5m) -> Close Rain Window (3.4m) -> Wide Overseer Bridge (18.5m)
    # =======================================================================
    # 02.0 is a 46m EXTREME WIDE VISTA: use distant skyline & low submerged causeway arches
    "02.0": [
        X("02.set.overseer_skyline__p06", "Distant Nocturnal Horizon Skyline (46m Vista)", "P5", 3.82, 1.24, 0.74, 0.22, "vista_backing", None),
        X("02.set.driveway_road_night__p03", "Straddling Submerged Roadway Causeway", "P3", 1.48, 1.06, 0.92, 0.18, "span_deck", None),
        X(
            "02.hero.drowned-light__p07",
            "Distant Submerged Corridor Arch",
            "P4",
            2.44,
            1.26,
            0.88,
            0.40,
            "gable_portal_cap",
            "Submerged Corridor Arch",
            aperture_footage=_portal(_vid(2, 2, 0), "arch", (0.24, 0.20, 0.76, 0.92), mullions=False, warm_spill=True),
        ),
        X(
            "02.set.bedroom_night__p02",
            "Glowing 1:08 AM Bedroom Threshold in the Distance",
            "P3",
            1.40,
            1.48,
            0.89,
            0.44,
            "gable_portal_cap",
            "1:08 AM Bedroom Threshold",
            aperture_footage=_portal(_vid(2, 3, 0), "door", (0.22, 0.14, 0.78, 0.94), mullions=False, warm_spill=True),
        ),
    ],
    "02.1": [
        X("02.set.bedroom_night__p09", "Straddling Dark Bedroom Floorboard Strip", "P3", 1.48, 1.04, 0.92, 0.18, "span_deck", None),
        X(
            "02.set.bedroom_night__p01",
            "Close Midnight Bedroom Wall with Lit Window Portal",
            "P4",
            2.44,
            1.24,
            0.90,
            0.88,
            "wall_with_door_hole",
            "Midnight Bedroom Window",
            aperture_footage=_portal(_vid(2, 4, 0), "window", (0.24, 0.16, 0.78, 0.88), mullions=True, warm_spill=True),
        ),
        X(
            "02.hero.childhouse__p01",
            "Childhood House Porch Doorway Portal",
            "P3",
            1.40,
            1.47,
            0.90,
            0.78,
            "gable_portal_cap",
            "1990s Childhood House",
            aperture_footage=_portal(_vid(2, 5, 0), "door", (0.24, 0.18, 0.76, 0.95), mullions=True, warm_spill=True),
        ),
        X("02.hero.childhouse__p10", "Carved Wooden Eaves Cornice", "P4", 2.36, 1.34, 0.30, 0.18, "roof_cornice", None),
    ],
    "02.2": [
        X("02.set.driveway_road_night__p03", "Straddling Wet Asphalt Driveway Curb", "P3", 1.48, 1.05, 0.92, 0.20, "span_deck", None),
        X(
            "02.set.living_room_1990s__p02",
            "1990s Floral Living Room Wall with Open Doorway",
            "P4",
            2.44,
            1.24,
            0.90,
            0.78,
            "wall_with_door_hole",
            "Living Room Doorway",
            aperture_footage=_portal(_vid(2, 6, 0), "door", (0.30, 0.16, 0.78, 0.96), mullions=False, warm_spill=True),
        ),
        X(
            "02.hero.childhouse__p07",
            "Red-Brick Driveway House Wing & Lit Window",
            "P3",
            1.40,
            1.47,
            0.90,
            0.76,
            "gable_portal_cap",
            "Driveway Porch Wing",
            aperture_footage=_portal(_vid(2, 7, 0), "window", (0.24, 0.20, 0.76, 0.88), mullions=True, warm_spill=True),
        ),
        X("02.set.living_room_1990s__p04", "1990s Floral Living Room Sofa", "P3", 1.36, 1.12, 0.89, 0.26, "furniture_anchor", None),
    ],
    "02.3": [
        X("02.set.living_room_1990s__p10", "Straddling Dark Wainscot Baseboard Runner", "P3", 1.46, 1.04, 0.92, 0.18, "ground_curb", None),
        X(
            "02.set.living_room_1990s__p01",
            "Close Floral Wall with Picture-Window Footage of Driveway",
            "P4",
            2.42,
            1.28,
            0.90,
            0.88,
            "wall_with_door_hole",
            "Picture Window to Driveway",
            aperture_footage=_portal(_vid(2, 8, 0), "window", (0.22, 0.16, 0.80, 0.86), mullions=True, warm_spill=True),
        ),
        X(
            "02.set.living_room_1990s__p03",
            "Pencil-Marked Childhood Doorpost Portal",
            "P3",
            1.42,
            1.08,
            0.90,
            0.66,
            "gable_portal_cap",
            "Doorpost Height Marks",
            aperture_footage=_portal(_vid(2, 9, 0), "door", (0.24, 0.14, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
        X("02.props.window__p21", "1990s Floral Draped Window Curtains", "P3", 1.36, 1.34, 0.74, 0.34, "window_dressing", None),
    ],
    "02.4": [
        X("02.set.driveway_road_night__p05", "Straddling Rain-Slicked Sill & Curb", "P3", 1.46, 1.04, 0.92, 0.18, "span_deck", None),
        X(
            "02.hero.childhouse__p15",
            "Close Shattered Glass Window Opening to the Storm",
            "P4",
            2.44,
            1.20,
            0.84,
            0.68,
            "wall_with_door_hole",
            "Shattered Driveway Window",
            aperture_footage=_portal(_vid(2, 10, 0), "window", (0.20, 0.16, 0.80, 0.88), mullions=True, warm_spill=True),
        ),
        X("02.set.overseer_skyline__p06", "Distant Nocturnal City Skyline Seen Through Rain", "P5", 3.82, 1.38, 0.74, 0.22, "vista_backing", None),
        X(
            "02.set.overseer_skyline__p02",
            "Nocturnal Overseer Bridge Tower",
            "P4",
            2.40,
            1.46,
            0.90,
            0.52,
            "wall_bay",
            "Overseer Skyline Bridge",
        ),
    ],
    # 02.5 is a 18.5m WIDE BOULEVARD / BRIDGE shot:
    "02.5": [
        X("02.set.overseer_skyline__p07", "Straddling Steel Highway Bridge Parapet West", "P3", 1.46, 1.06, 0.90, 0.18, "span_deck", "Bridge Toward the Chapel"),
        X("02.set.overseer_skyline__p07", "Extended Steel Highway Bridge Parapet East", "P3", 1.46, 1.36, 0.90, 0.18, "span_deck", None),
        X("02.set.overseer_skyline__p03", "Distant Nocturnal Overseer Tower", "P4", 2.44, 1.20, 0.88, 0.38, "wall_bay", None),
        X(
            "03.hero.chapel__p01",
            "Stone Chapel Gable & Lit Rose-Window Portal Across Bridge",
            "P4",
            2.38,
            1.46,
            0.89,
            0.58,
            "gable_portal_cap",
            "Chapel Threshold · Poem 03",
            aperture_footage=_portal(_vid(3, 1, 0), "arch", (0.26, 0.22, 0.74, 0.95), mullions=True, warm_spill=True),
        ),
    ],

    # =======================================================================
    # POEM 03 · HOW TO BREAK OFF AN ENGAGEMENT
    # Hand Assembly: Medium Chapel Facade (7.5m) -> Medium Nave (6.6m) -> Close Side Doors (3.6m)
    #                -> Wide Storm Exterior (16m) -> Far Ruined Shore (42m) -> Extreme Wide Salt Causeway (52m)
    # =======================================================================
    "03.0": [
        X("03.set.chapel_side_doors__p04", "Straddling Chapel Flagstone Approach", "P2", 1.08, 1.04, 0.92, 0.16, "ground_curb", None),
        X("03.hero.chapel__p06", "Gothic Stone Buttress Arcade Wall", "P4", 2.44, 1.22, 0.90, 0.64, "wall_bay", "Chapel Nave Buttress Wall"),
        X("03.hero.chapel__p02", "Pitched Slate Chapel Roof Slope", "P4", 2.40, 1.22, 0.48, 0.30, "roof_cornice", None),
        X(
            "03.hero.chapel__p01",
            "Stone Gabled Chapel Portal & Stained-Glass Oculus",
            "P3",
            1.40,
            1.45,
            0.90,
            0.88,
            "gable_portal_cap",
            "Chapel West Portal",
            aperture_footage=_portal(_vid(3, 2, 0), "arch", (0.26, 0.22, 0.74, 0.95), mullions=True, warm_spill=True),
        ),
        X("03.props.rose-window__p01", "Carved Gothic Rose Window Tracery", "P3", 1.36, 1.45, 0.50, 0.24, "window_dressing", None),
    ],
    "03.1": [
        X("03.hero.chapel.interior-states__p05", "Straddling Carved Wooden Chapel Pew", "P3", 1.42, 1.06, 0.90, 0.26, "furniture_anchor", "Empty Wedding Pew"),
        X(
            "03.hero.chapel.interior-states__p01",
            "Triple Lancet Stone Nave Window Wall with Stained-Glass Footage",
            "P4",
            2.44,
            1.26,
            0.90,
            0.82,
            "wall_with_door_hole",
            "Nave Lancet Arcade",
            aperture_footage=_portal(_vid(3, 4, 0), "window", (0.20, 0.16, 0.80, 0.88), mullions=True, warm_spill=True),
        ),
        X(
            "03.set.chapel_side_doors__p01",
            "Carved Stone Side-Door Portal",
            "P3",
            1.38,
            1.48,
            0.90,
            0.76,
            "gable_portal_cap",
            "Side Doors Threshold",
            aperture_footage=_portal(_vid(3, 5, 0), "door", (0.26, 0.18, 0.74, 0.95), mullions=False, warm_spill=True),
        ),
    ],
    "03.2": [
        X("03.set.chapel_side_doors__p04", "Straddling Weathered Stone Threshold Step", "P2", 1.08, 1.04, 0.92, 0.18, "ground_curb", None),
        X(
            "03.set.chapel_side_doors__p01",
            "Close Rusticated Stone Archway with Storm Footage Beyond",
            "P4",
            2.42,
            1.28,
            0.90,
            0.92,
            "wall_with_door_hole",
            "Chapel Stone Side Arch",
            aperture_footage=_portal(_vid(3, 6, 0), "door", (0.26, 0.16, 0.74, 0.96), mullions=False, warm_spill=True),
        ),
        X("03.set.chapel_side_doors__p02", "Heavy Timber Left Chapel Door Leaf", "P3", 1.44, 1.13, 0.90, 0.64, "gable_portal_cap", None),
        X("03.set.chapel_side_doors__p03", "Heavy Timber Right Chapel Door Leaf", "P3", 1.44, 1.43, 0.90, 0.64, "gable_portal_cap", None),
    ],
    # 03.3 is a 16m WIDE STORM EXTERIOR:
    "03.3": [
        X("03.set.remnants_shore__p03", "Straddling Storm-Swept Shingle Ground", "P2", 1.08, 1.06, 0.92, 0.16, "ground_curb", None),
        X("03.hero.chapel.decay__p06", "Weathered Stone Chapel Wall in Storm (16m Wide)", "P4", 2.44, 1.22, 0.90, 0.56, "wall_bay", "Storm-Struck Nave Wall"),
        X("03.hero.chapel.decay__p02", "Moss-Patched Slate Roof Slope", "P4", 2.40, 1.22, 0.54, 0.26, "roof_cornice", None),
        X(
            "03.hero.chapel.decay__p01",
            "Cracked Stone Gable Portal in Lightning",
            "P3",
            1.40,
            1.46,
            0.90,
            0.66,
            "gable_portal_cap",
            "Shattered Nave Threshold",
            aperture_footage=_portal(_vid(3, 7, 0), "arch", (0.26, 0.22, 0.74, 0.94), mullions=True, warm_spill=True),
        ),
    ],
    # 03.4 & 03.5 are 42m–52m EXTREME WIDE SHORE VISTAS: low horizon ruins, tidewater bands & distant viaduct arches!
    "03.4": [
        X("03.set.remnants_shore__p01", "Distant Tidewater Horizon Band (42m Vista)", "P5", 3.82, 1.26, 0.76, 0.18, "vista_backing", None),
        X("03.set.remnants_shore__p03", "Straddling Driftwood & Wet Shingle Shore", "P2", 1.08, 1.08, 0.92, 0.14, "ground_curb", None),
        X("03.hero.chapel.ruin__p06", "Distant Collapsed Stone Arcade Ruin", "P4", 2.44, 1.22, 0.89, 0.34, "span_deck", "Collapsed Nave Arcade"),
        X(
            "03.hero.chapel.ruin__p01",
            "Distant Ruined Shore Archway on the Spit",
            "P3",
            1.40,
            1.46,
            0.89,
            0.42,
            "gable_portal_cap",
            "Ruined Shore Arch",
            aperture_footage=_portal(_vid(3, 8, 0), "arch", (0.26, 0.24, 0.74, 0.94), mullions=False, warm_spill=True),
        ),
    ],
    "03.5": [
        X("03.set.remnants_shore__p01", "Continuous Sea Horizon Strip (52m Vista)", "P5", 3.82, 1.28, 0.76, 0.18, "vista_backing", None),
        X("03.set.remnants_shore__p04", "Straddling Salt-Line Shore Causeway", "P2", 1.08, 1.08, 0.92, 0.14, "ground_curb", None),
        X(
            "03.hero.chapel.ruin__p12",
            "Distant Broken Rose-Window Sea Ruin",
            "P4",
            2.42,
            1.20,
            0.88,
            0.34,
            "gable_portal_cap",
            "Ruined Shore Wall",
            aperture_footage=_portal(_vid(3, 9, 0), "window", (0.24, 0.22, 0.76, 0.88), mullions=True, warm_spill=True),
        ),
        X(
            "04.hero.viaduct__p01",
            "Distant Three-Arch Stone Viaduct Across the Bay",
            "P4",
            2.38,
            1.46,
            0.88,
            0.32,
            "span_deck",
            "Viaduct Toward Poem 04",
        ),
    ],

    # =======================================================================
    # POEM 04 · NEVERMORE
    # Hand Assembly: Far Ash Shore (48m) -> Wide Viaduct Pier (15.5m) -> Close Incline Ledge (3.4m)
    #                -> Medium Bridge Booth (6.5m) -> Wide Night Garden Boulevard (17m) -> Far Starfield (44m) -> Wide Perimeter (16.5m)
    # =======================================================================
    # 04.0 is a 48m EXTREME WIDE SHORE VISTA:
    "04.0": [
        X("04.set.shore_night__p01", "Continuous Nocturnal Sea Horizon (48m Vista)", "P5", 3.82, 1.26, 0.76, 0.18, "vista_backing", None),
        X("04.set.shore_night__p03", "Straddling Cresting Night-Shore Wave Strip", "P2", 1.08, 1.06, 0.92, 0.14, "ground_curb", None),
        X("04.hero.viaduct__p01", "Distant Three-Arch Stone Viaduct Span", "P4", 2.44, 1.26, 0.88, 0.34, "span_deck", "Stone Viaduct Bridge"),
        X("04.set.shore_night__p08", "Distant Wind-Bent Shore Tree", "P3", 1.38, 1.48, 0.89, 0.36, "boulevard_tree", None),
    ],
    "04.1": [
        X("04.set.shore_night__p03", "Straddling Night-Canal Wave Strip", "P2", 1.08, 1.05, 0.92, 0.14, "ground_curb", None),
        X(
            "04.hero.viaduct__p02",
            "Stone Viaduct Pier & Half-Arch (+4m Datum)",
            "P4",
            2.44,
            1.18,
            0.90,
            0.58,
            "gable_portal_cap",
            "Viaduct Pier (+4m Line)",
            aperture_footage=_portal(_vid(4, 3, 0), "arch", (0.24, 0.24, 0.76, 0.94), mullions=False, warm_spill=True),
        ),
        X(
            "04.hero.viaduct__p04",
            "Wide Stone Viaduct Canal Archway",
            "P4",
            2.40,
            1.45,
            0.90,
            0.58,
            "gable_portal_cap",
            "Viaduct Canal Arch",
            aperture_footage=_portal(_vid(4, 4, 0), "arch", (0.24, 0.24, 0.76, 0.94), mullions=False, warm_spill=True),
        ),
        X("04.hero.viaduct__p07", "Iron Viaduct Bridge Railing", "P3", 1.44, 1.30, 0.56, 0.16, "span_deck", None),
    ],
    "04.2": [
        X("04.set.incline_trail__p05", "Straddling Stepped Stone Trail Curb", "P2", 1.08, 1.04, 0.92, 0.18, "ground_curb", None),
        X("04.set.incline_trail__p03", "Close Rising Stone & Earth Incline Ramp", "P4", 2.44, 1.24, 0.90, 0.38, "span_deck", "Incline Trail Ramp"),
        X(
            "04.hero.viaduct__p03",
            "Close Stone Viaduct Overpass Arch with Light Beyond",
            "P3",
            1.40,
            1.46,
            0.90,
            0.78,
            "gable_portal_cap",
            "Viaduct Overpass Portal",
            aperture_footage=_portal(_vid(4, 6, 0), "arch", (0.24, 0.20, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
        X("04.set.shore_night__p09", "Twisted Shore Tree Silhouette", "P3", 1.42, 1.14, 0.89, 0.44, "boulevard_tree", None),
    ],
    "04.3": [
        X("04.hero.viaduct__p09", "Straddling Stone Viaduct Roadway Coping", "P2", 1.08, 1.05, 0.92, 0.16, "ground_curb", None),
        X("04.hero.viaduct__p01", "Extended Three-Arch Stone Viaduct", "P4", 2.44, 1.26, 0.89, 0.46, "span_deck", "Viaduct Archway Span"),
        X(
            "09.props.phonebooth__p01",
            "Illuminated Glass Telephone Booth on the Bridge",
            "P3",
            1.38,
            1.46,
            0.90,
            0.66,
            "gable_portal_cap",
            "Glass Phone Booth",
            aperture_footage=_portal(_vid(4, 8, 0), "window", (0.22, 0.14, 0.78, 0.88), mullions=True, warm_spill=True),
        ),
        X("04.hero.viaduct__p07", "Upper Viaduct Iron Balustrade", "P4", 2.38, 1.26, 0.56, 0.16, "span_deck", None),
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
        dist_mult=0.84,
        portal_id="04.hero.viaduct__p03",
        portal_label="Moonlit Garden Archway",
        portal_footage=_vid(4, 11, 0),
    ),
    # 04.5 is a 44m EXTREME WIDE STARFIELD VISTA:
    "04.5": [
        X("04.set.night_garden_field__p01", "Distant Horizon Tree-Line Strip (44m Vista)", "P5", 3.80, 1.26, 0.84, 0.20, "vista_backing", "Starfield Ridge"),
        X("04.set.night_garden_field__p07", "Straddling Wildflower & Reed Meadow", "P2", 1.08, 1.08, 0.92, 0.16, "ground_curb", None),
        X(
            "04.hero.viaduct__p03",
            "Distant Stone Archway Under the Stars",
            "P4",
            2.40,
            1.44,
            0.89,
            0.40,
            "gable_portal_cap",
            "Starlight Arch",
            aperture_footage=_portal(_vid(4, 14, 0), "arch", (0.26, 0.22, 0.74, 0.94), mullions=False, warm_spill=True),
        ),
        X("04.props.heart__p01", "Carved Stone Heart Reliquary on the Ridge", "P3", 1.40, 1.18, 0.89, 0.22, "story_prop", None),
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
        dist_mult=0.85,
    ),

    # =======================================================================
    # POEM 05 · BLOODLINES
    # Hand Assembly: Wide Perimeter Boulevard (16m) -> Cosmic Star-Naming Field (95m) -> Medium Basement (5.8m)
    #                -> Far Globe Parade (45m) -> Close Ancestral Hearth & Door (3.5m) -> Far Causeway to Atlantis (50m)
    # =======================================================================
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
        dist_mult=0.88,
    ),
    # 05.1 is a 95m COSMIC STAR-NAMING FIELD: low horizon silhouettes under vast constellations!
    "05.1": [
        X("05.set.night_field_parade__p05", "Straddling Low Horizon Grass Verge (95m Cosmic Field)", "P2", 1.08, 1.08, 0.92, 0.14, "ground_curb", None),
        X("05.hero.perimeter__p05", "Distant Horizon Fence Line", "P4", 2.46, 1.26, 0.89, 0.24, "boulevard_fence", "Star-Naming Horizon"),
        X("09.hero.canopy__p04", "Distant Silhouette Cypress Under the Stars #1", "P4", 2.40, 1.14, 0.89, 0.36, "boulevard_tree", None),
        X("09.hero.canopy__p07", "Distant Silhouette Cypress Under the Stars #2", "P4", 2.38, 1.44, 0.89, 0.34, "boulevard_tree", None),
        X("13.set.harbor_quay_night_fire__p02", "Distant Beacon Lamp on the Plain", "P3", 1.44, 1.30, 0.89, 0.32, "boulevard_lamp", None),
    ],
    "05.2": [
        X("05.set.humid_basement__p04", "Straddling Rough-Sawn Southern-Pine Ceiling Joist", "P4", 2.38, 1.12, 0.30, 0.18, "roof_cornice", "Southern-Pine Joist"),
        X(
            "05.set.humid_basement__p01",
            "Humid Cinderblock Basement Wall with High Window Footage",
            "P4",
            2.44,
            1.25,
            0.90,
            0.84,
            "wall_with_door_hole",
            "Humid Basement Window Wall",
            aperture_footage=_portal(_vid(5, 4, 0), "window", (0.26, 0.16, 0.76, 0.78), mullions=True, warm_spill=True),
        ),
        X("12.set.temple_backroom__p02", "Basement Stone Staircase Flight Upward", "P3", 1.42, 1.47, 0.90, 0.38, "span_deck", "Stairs Up to the Gate"),
        X("05.props.staff-mattress-emblem__p03", "Basement Floor Mattress", "P3", 1.38, 1.14, 0.90, 0.24, "furniture_anchor", None),
    ],
    # 05.3 is a 45m EXTREME WIDE GLOBE PARADE VISTA:
    "05.3": [
        X("05.set.night_field_parade__p07", "Straddling Curved Globe Horizon Lawn (45m Vista)", "P4", 2.46, 1.18, 0.90, 0.28, "span_deck", "Parade Field Extension"),
        X(
            "05.set.winged_marble_gate__p03",
            "Distant Monumental Winged Marble Gate on the Horizon",
            "P4",
            2.40,
            1.38,
            0.89,
            0.46,
            "gable_portal_cap",
            "Winged Marble Gate",
            aperture_footage=_portal(_vid(5, 6, 0), "arch", (0.26, 0.22, 0.74, 0.94), mullions=False, warm_spill=True),
        ),
        X("05.set.winged_marble_gate__p01", "Carved Marble Left Wing", "P3", 1.44, 1.24, 0.86, 0.34, "gable_portal_cap", None),
        X("05.set.winged_marble_gate__p05", "Carved Marble Right Wing", "P3", 1.44, 1.50, 0.86, 0.34, "gable_portal_cap", None),
    ],
    "05.4": [
        X("05.set.winged_marble_gate__p06", "Straddling Inscribed Marble Plinth Step", "P2", 1.08, 1.05, 0.92, 0.18, "ground_curb", None),
        X(
            "12.set.temple_backroom__p01",
            "Close Ancestral Hearth Wall & Open Doorway to Causeway",
            "P4",
            2.44,
            1.24,
            0.90,
            0.88,
            "wall_with_door_hole",
            "Ancestral Doorway Threshold",
            aperture_footage=_portal(_vid(5, 8, 0), "door", (0.32, 0.18, 0.78, 0.96), mullions=False, warm_spill=True),
        ),
        X(
            "05.set.winged_marble_gate__p03",
            "Close Marble Sanctuary Archway Portal",
            "P3",
            1.40,
            1.46,
            0.90,
            0.84,
            "gable_portal_cap",
            "Sanctuary Threshold",
            aperture_footage=_portal(_vid(5, 9, 0), "arch", (0.26, 0.20, 0.74, 0.95), mullions=False, warm_spill=True),
        ),
    ],
    # 05.5 is a 50m EXTREME WIDE CAUSEWAY VISTA:
    "05.5": [
        X("06.set.atlantis_waterfront.skyline__p01", "Distant Atlantis Citadel on the Horizon (50m Vista)", "P5", 3.82, 1.28, 0.76, 0.24, "vista_backing", None),
        X("06.set.causeway_road__p03", "Straddling Golden-Brick Causeway Perspective Span", "P3", 1.46, 1.16, 0.91, 0.24, "span_deck", "Yellow-Brick Causeway"),
        X(
            "06.set.atlantis_gate__p01",
            "Distant Light Gate of Atlantis Across the Bay",
            "P4",
            2.40,
            1.46,
            0.89,
            0.44,
            "gable_portal_cap",
            "The Light Gate of Atlantis",
            aperture_footage=_portal(_vid(6, 1, 0), "arch", (0.26, 0.24, 0.74, 0.94), mullions=False, warm_spill=True),
        ),
        X("06.props.lantern-candle-guitar__p01", "Brass Wayfinder Lantern on Causeway Post", "P2", 1.08, 1.06, 0.89, 0.16, "story_prop", None),
    ],

    # =======================================================================
    # POEM 06 · RESURRECTING ATLANTIS
    # Hand Assembly: Far Bay Skyline (58m) -> Far Causeway (42m) -> Far Waterfront (46m)
    #                -> Medium Crystal Hall (6.8m) -> Wide Forum (18m) -> Medium Narrow Street (6.4m) -> Wide Harbor Teahouse (15m)
    # =======================================================================
    # 06.0, 06.1, 06.2 are 42–58m EXTREME WIDE BAY VISTAS: horizon-scale citadels, causeways & colonnades!
    "06.0": [
        X("06.set.atlantis_waterfront.skyline__p01", "Distant Domed Atlantis Citadel Across Bay (58m Vista)", "P5", 3.82, 1.18, 0.76, 0.26, "vista_backing", None),
        X("06.set.atlantis_waterfront.skyline__p06", "Distant Twin-Spired Atlantis Palace", "P5", 3.78, 1.44, 0.76, 0.24, "vista_backing", None),
        X("06.set.atlantis_gate__p02", "Straddling Stone Gate Causeway Embankment", "P4", 2.42, 1.14, 0.91, 0.28, "span_deck", "Light Gate Embankment"),
        X("06.set.atlantis_waterfront__p04", "Distant Waterfront Quay Steps", "P3", 1.42, 1.42, 0.90, 0.22, "span_deck", "Waterfront Landing Stairs"),
    ],
    "06.1": [
        X("06.set.atlantis_waterfront.skyline__p12", "Distant Terraced Atlantis Citadel (42m Vista)", "P5", 3.80, 1.28, 0.76, 0.26, "vista_backing", None),
        X("06.set.causeway_road__p03", "Straddling Yellow-Brick Causeway Deck", "P3", 1.46, 1.14, 0.91, 0.24, "span_deck", "Yellow-Brick Causeway Extension"),
        X(
            "06.set.atlantis_plaza__p02",
            "Distant Three-Arch Venetian-Atlantis Colonnade",
            "P4",
            2.40,
            1.44,
            0.89,
            0.40,
            "gable_portal_cap",
            "Waterfront Colonnade",
            aperture_footage=_portal(_vid(6, 3, 0), "arch", (0.24, 0.22, 0.76, 0.94), mullions=False, warm_spill=True),
        ),
    ],
    "06.2": [
        X("06.set.atlantis_waterfront.skyline__p12", "Terraced Atlantis Hillside Skyline (46m Vista)", "P5", 3.80, 1.24, 0.76, 0.26, "vista_backing", None),
        X("06.set.atlantis_waterfront__p04", "Straddling Waterfront Balustrade & Quay Steps", "P4", 2.42, 1.10, 0.90, 0.24, "span_deck", "Waterfront Quay Steps"),
        X(
            "06.set.atlantis_plaza__p02",
            "Distant Atlantis Palace Arcade on the Water",
            "P3",
            1.40,
            1.42,
            0.89,
            0.42,
            "gable_portal_cap",
            "Palace Arcade",
            aperture_footage=_portal(_vid(6, 5, 0), "arch", (0.24, 0.22, 0.76, 0.94), mullions=False, warm_spill=True),
        ),
    ],
    "06.3": [
        X("06.set.crystal_tree_hall__p01", "Straddling Golden-Root Crystal Tree West", "P3", 1.44, 1.06, 0.89, 0.42, "boulevard_tree", None),
        X(
            "06.set.crystal_tree_hall__p13",
            "Twin-Arched Crystal Colonnade Portal with Sanctuary Footage",
            "P4",
            2.44,
            1.28,
            0.90,
            0.78,
            "gable_portal_cap",
            "Crystal Tree Colonnade",
            aperture_footage=_portal(_vid(6, 7, 0), "arch", (0.22, 0.18, 0.78, 0.95), mullions=True, warm_spill=True),
        ),
        X("06.set.crystal_tree_hall__p02", "Golden-Root Crystal Tree East", "P3", 1.42, 1.48, 0.89, 0.40, "boulevard_tree", None),
        X("06.set.crystal_tree_hall__p07", "Faceted Blue Crystal Canopy Cluster", "P4", 2.36, 1.28, 0.36, 0.26, "roof_cornice", None),
    ],
    "06.4": [
        X("06.hero.forum__p02", "Straddling Circular Stone Forum Ring", "P3", 1.44, 1.12, 0.91, 0.26, "span_deck", None),
        X(
            "06.set.atlantis_plaza__p01",
            "Wide Terracotta Arched Plaza Wing with Lit Windows",
            "P4",
            2.44,
            1.24,
            0.90,
            0.62,
            "wall_with_door_hole",
            "West Plaza Arcade",
            aperture_footage=_portal(_vid(6, 9, 0), "arch", (0.24, 0.20, 0.76, 0.94), mullions=True, warm_spill=True),
        ),
        X(
            "06.set.narrow_streets__p06",
            "Carved Stone Street Archway Into the Alleys",
            "P3",
            1.38,
            1.47,
            0.90,
            0.60,
            "gable_portal_cap",
            "Into the Narrow Streets",
            aperture_footage=_portal(_vid(6, 10, 0), "arch", (0.26, 0.22, 0.74, 0.95), mullions=False, warm_spill=True),
        ),
    ],
    "06.5": [
        X("06.set.narrow_streets__p10", "Straddling Perspective Cobblestone Street Deck", "P3", 1.48, 1.12, 0.92, 0.24, "span_deck", None),
        X("06.set.narrow_streets__p01", "Tall Narrow-Street Tenement Facade West", "P4", 2.46, 1.16, 0.90, 0.74, "wall_bay", "Narrow Cobble Alley"),
        X(
            "06.set.narrow_streets__p06",
            "Masonry Alleyway Arch Portal with Harbor Footage",
            "P3",
            1.42,
            1.36,
            0.90,
            0.72,
            "gable_portal_cap",
            "Alleyway Portal",
            aperture_footage=_portal(_vid(6, 11, 0), "arch", (0.26, 0.20, 0.74, 0.95), mullions=False, warm_spill=True),
        ),
        X("06.set.narrow_streets__p04", "Overhead String of Warm Alley Bulbs", "P2", 1.08, 1.28, 0.36, 0.18, "ceiling_fixture", None),
    ],
    "06.6": [
        X("06.hero.teahouse__p07", "Straddling Flagstone Harbor Quay Walk", "P3", 1.46, 1.08, 0.92, 0.18, "span_deck", None),
        X(
            "06.hero.teahouse__p01",
            "Weathered Teal Teahouse Wall with Glowing Window Footage",
            "P4",
            2.44,
            1.24,
            0.90,
            0.66,
            "wall_with_door_hole",
            "Harbor Teahouse Veranda",
            aperture_footage=_portal(_vid(6, 12, 0), "window", (0.24, 0.18, 0.78, 0.88), mullions=True, warm_spill=True),
        ),
        X("06.hero.teahouse__p02", "Corrugated Teahouse Overhang Roof", "P4", 2.40, 1.24, 0.50, 0.24, "roof_cornice", None),
        X(
            "06.hero.house__p01",
            "Red Waterfront Boathouse Portal Toward Poem 07",
            "P3",
            1.38,
            1.48,
            0.90,
            0.58,
            "gable_portal_cap",
            "Boathouse Wing",
            aperture_footage=_portal(_vid(7, 1, 0), "door", (0.24, 0.20, 0.76, 0.94), mullions=True, warm_spill=True),
        ),
    ],

    # =======================================================================
    # POEM 07 · DJ TURN ME UP
    # Hand Assembly: Medium Club Stage (7.2m) -> Close DJ Console (3.3m) -> Close Red Shaft (3.6m)
    #                -> Wide Club Plaza (15.5m) -> Wide Three-Roads Highway (21m) -> Medium Alley (6.5m) -> Wide Canal Boulevard (17.5m)
    # =======================================================================
    "07.0": [
        X("07.hero.house.furniture__p18", "Straddling Steel Grate Dancefloor Deck", "P3", 1.48, 1.06, 0.92, 0.20, "span_deck", None),
        X(
            "07.hero.house__p01",
            "Teal Industrial Club Wall with Neon Window Footage",
            "P4",
            2.44,
            1.22,
            0.90,
            0.76,
            "wall_with_door_hole",
            "Industrial Club Wing",
            aperture_footage=_portal(_vid(7, 2, 0), "window", (0.22, 0.18, 0.78, 0.88), mullions=True, warm_spill=True),
        ),
        X(
            "07.hero.house__p03",
            "Open-Sided DJ Stage Box Portal",
            "P3",
            1.40,
            1.46,
            0.90,
            0.74,
            "gable_portal_cap",
            "DJ Stage Box",
            aperture_footage=_portal(_vid(7, 3, 0), "arch", (0.20, 0.16, 0.80, 0.94), mullions=False, warm_spill=True),
        ),
    ],
    "07.1": [
        X("07.hero.house.furniture__p14", "Straddling Cyan Neon Floor Strip", "P2", 1.08, 1.05, 0.92, 0.14, "ground_curb", None),
        X(
            "07.hero.house__p04",
            "Close Corrugated Club Gallery Wall & VIP Window",
            "P4",
            2.44,
            1.24,
            0.90,
            0.86,
            "wall_with_door_hole",
            "Club Gallery Extension",
            aperture_footage=_portal(_vid(7, 4, 0), "window", (0.24, 0.18, 0.78, 0.88), mullions=True, warm_spill=True),
        ),
        X("07.hero.house__p09", "Industrial Steel Club Mezzanine Stairs", "P3", 1.44, 1.46, 0.90, 0.36, "span_deck", "Mezzanine Stairs"),
        X("07.hero.house.furniture__p17", "U-Shaped Neon VIP Lounge Booth", "P3", 1.38, 1.18, 0.90, 0.26, "furniture_anchor", None),
    ],
    "07.2": [
        X("07.hero.house.furniture__p14", "Straddling Neon Conduit Runner", "P2", 1.08, 1.05, 0.92, 0.14, "ground_curb", None),
        X(
            "07.hero.shaft__p16",
            "Close Red-Lit Industrial Bass Corridor Bay",
            "P4",
            2.44,
            1.24,
            0.90,
            0.86,
            "wall_with_door_hole",
            "Red Bass Corridor",
            aperture_footage=_portal(_vid(7, 5, 0), "door", (0.26, 0.16, 0.76, 0.94), mullions=False, warm_spill=True),
        ),
        X(
            "07.hero.shaft__p01",
            "Octagonal Red Steel Bulkhead Portal",
            "P3",
            1.40,
            1.46,
            0.90,
            0.82,
            "gable_portal_cap",
            "Bulkhead Portal",
            aperture_footage=_portal(_vid(7, 7, 0), "arch", (0.24, 0.20, 0.76, 0.86), mullions=False, warm_spill=True),
        ),
    ],
    "07.3": [
        X("07.hero.house.furniture__p18", "Straddling Club Plaza Grate Walk", "P3", 1.48, 1.08, 0.92, 0.20, "span_deck", None),
        X(
            "08.hero.marquee__p01",
            "Wide Brick Club Facade with Three Glowing Portal Doors",
            "P4",
            2.44,
            1.26,
            0.90,
            0.66,
            "wall_with_door_hole",
            "Club Plaza Portals",
            aperture_footage=_portal(_vid(7, 8, 0), "door", (0.20, 0.22, 0.80, 0.95), mullions=True, warm_spill=True),
        ),
        X(
            "07.hero.shaft__p15",
            "Red Elevator Shaft Portal",
            "P3",
            1.40,
            1.48,
            0.90,
            0.58,
            "gable_portal_cap",
            "Elevator Shaft Portal",
            aperture_footage=_portal(_vid(7, 9, 0), "door", (0.24, 0.16, 0.76, 0.94), mullions=False, warm_spill=True),
        ),
    ],
    # 07.4 is a 21m WIDE THREE-ROADS HIGHWAY:
    "07.4": [
        X("07.set.projection_vineyard__p05", "Distant Vineyard Horizon Trellis Row (21m Wide)", "P5", 3.80, 1.28, 0.84, 0.18, "vista_backing", "Vineyard Horizon"),
        X("07.set.projection_three_roads__p01", "Straddling Two-Lane Perspective Highway Deck", "P3", 1.46, 1.18, 0.91, 0.26, "span_deck", "Three Roads Highway"),
        X("07.set.projection_three_roads__p13", "Curved Highway Street Lamp West", "P3", 1.40, 1.12, 0.89, 0.44, "boulevard_lamp", None),
        X("07.set.projection_three_roads__p14", "Curved Highway Street Lamp East", "P3", 1.40, 1.42, 0.89, 0.42, "boulevard_lamp", None),
    ],
    "07.5": [
        X("07.hero.house.furniture__p05", "Straddling Wet Alleyway Curb Slab", "P2", 1.08, 1.06, 0.92, 0.16, "ground_curb", None),
        X("07.hero.house__p05", "Rusted Corrugated After-Hours Club Wall", "P4", 2.44, 1.22, 0.90, 0.72, "wall_bay", "After-Hours Alley Wall"),
        X(
            "08.hero.marquee__p16",
            "Illuminated 'NEW SINGLE' Theater Entrance Portal",
            "P3",
            1.40,
            1.46,
            0.90,
            0.76,
            "gable_portal_cap",
            "NEW SINGLE Marquee",
            aperture_footage=_portal(_vid(7, 12, 0), "door", (0.24, 0.20, 0.76, 0.95), mullions=True, warm_spill=True),
        ),
        X("07.set.projection_three_roads__p13", "Alleyway Sodium Street Lamp", "P3", 1.42, 1.08, 0.89, 0.48, "boulevard_lamp", None),
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
        dist_mult=0.84,
    ),

    # =======================================================================
    # POEM 08 · NEWLY SINGLE
    # Hand Assembly: Aerial Rooftop Skyline (88m) -> Medium NEW SINGLE Marquee (6.8m) -> Aerial Soul Over Clouds (115m)
    #                -> Close Ice-Water Basins (3.5m) -> Wide Harbor Mist Promenade (17m) -> Far Equator Horizon (54m)
    # =======================================================================
    # 08.0 is an 88m AERIAL ROOFTOP VISTA:
    "08.0": [
        X("08.set.rooftop_club__p07", "Distant Nocturnal Atlantis Spire Horizon (88m Aerial)", "P5", 3.82, 1.28, 0.78, 0.22, "vista_backing", None),
        X("08.set.rooftop_club__p09", "Straddling Rooftop Terrace Guardrail", "P3", 1.44, 1.12, 0.90, 0.16, "span_deck", None),
        X("08.set.rooftop_club__p02", "Rooftop Tesla-Coil Skyline Stage", "P4", 2.44, 1.24, 0.89, 0.36, "span_deck", "Rooftop Tesla Stage"),
        X("08.set.rooftop_club__p04", "Distant Lattice Broadcast Tower", "P4", 2.40, 1.48, 0.89, 0.42, "boulevard_lamp", None),
    ],
    "08.1": [
        X("08.hero.marquee__p14", "Straddling Rain-Slicked Sidewalk Reflections", "P3", 1.48, 1.08, 0.92, 0.18, "span_deck", None),
        X(
            "08.hero.marquee__p01",
            "Brick Theater Facade with Three Glowing Portal Doors",
            "P4",
            2.44,
            1.25,
            0.90,
            0.78,
            "wall_with_door_hole",
            "NEW SINGLE Marquee Portals",
            aperture_footage=_portal(_vid(8, 2, 0), "door", (0.20, 0.22, 0.80, 0.95), mullions=True, warm_spill=True),
        ),
        X("08.hero.marquee__p02", "Retro 'NEW SINGLE' Marquee Signboard", "P4", 2.38, 1.25, 0.42, 0.24, "roof_cornice", None),
        X(
            "08.hero.marquee.interior__p02",
            "Crimson Theater Lobby Twin Doors",
            "P3",
            1.40,
            1.48,
            0.90,
            0.72,
            "gable_portal_cap",
            "Theater Lobby Doors",
            aperture_footage=_portal(_vid(8, 3, 0), "door", (0.22, 0.18, 0.78, 0.95), mullions=False, warm_spill=True),
        ),
    ],
    # 08.2 is a 115m AERIAL SOUL FLIGHT OVER CLOUDS:
    "08.2": [
        X("08.set.atlantis_aerial__p03", "Continuous Moonlit Cumulus Cloud Bank West (115m Aerial)", "P5", 3.82, 1.14, 0.56, 0.26, "vista_backing", "Cloud Layer"),
        X("08.set.atlantis_aerial__p03", "Continuous Moonlit Cumulus Cloud Bank East", "P5", 3.80, 1.44, 0.62, 0.24, "vista_backing", None),
        X("08.set.rooftop_club__p07", "Distant Atlantis Aerial City Grid Below Clouds", "P4", 2.44, 1.28, 0.89, 0.24, "span_deck", "Aerial Atlantis Grid"),
        X(
            "08.hero.marquee.interior__p09",
            "Floating Crimson Cinema Portal in the Sky",
            "P3",
            1.40,
            1.46,
            0.88,
            0.44,
            "gable_portal_cap",
            "Crimson Auditorium Portal",
            aperture_footage=_portal(_vid(8, 5, 0), "door", (0.24, 0.18, 0.76, 0.94), mullions=False, warm_spill=True),
        ),
    ],
    "08.3": [
        X("11.hero.pools__p01", "Straddling Turquoise Reflecting Pool Channel", "P3", 1.48, 1.08, 0.92, 0.18, "span_deck", None),
        X("08.props.basins__p01", "Close Carved Stone Ice-Water Basin West", "P3", 1.44, 1.18, 0.90, 0.34, "furniture_anchor", "Salted Ice-Water Basin"),
        X("08.props.basins__p02", "Close Carved Stone Ice-Water Basin East", "P3", 1.42, 1.44, 0.90, 0.34, "furniture_anchor", None),
        X("12.set.temple_grove__p07", "Overhanging Willow & Cypress Canopy", "P4", 2.40, 1.30, 0.38, 0.28, "roof_cornice", None),
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
        dist_mult=0.84,
    ),
    # 08.5 is a 54m EXTREME WIDE EQUATOR HORIZON VISTA:
    "08.5": [
        X("08.set.rooftop_club__p07", "Distant Equator Spire Horizon Strip (54m Vista)", "P5", 3.82, 1.26, 0.78, 0.20, "vista_backing", None),
        X("09.set.harbor_path_east__p07", "Straddling Flagstone Harbor Causeway", "P2", 1.08, 1.08, 0.92, 0.16, "ground_curb", None),
        X("09.hero.canopy__p08", "Distant Illuminated Harbor Pergola Colonnade", "P4", 2.42, 1.24, 0.89, 0.34, "span_deck", "Harbor Pergola Colonnade"),
        X(
            "09.set.atlantis_club_sidewalk__p04",
            "Distant Neon Club Entrance Portal Toward Poem 09",
            "P3",
            1.40,
            1.46,
            0.89,
            0.44,
            "gable_portal_cap",
            "Into Poem 09 · Yet, Heard",
            aperture_footage=_portal(_vid(9, 1, 0), "door", (0.24, 0.18, 0.76, 0.94), mullions=True, warm_spill=True),
        ),
    ],

    # =======================================================================
    # POEM 09 · YET, HEARD
    # Hand Assembly: Medium Club Sidewalk (6.6m) -> Wide Harbor Pier (18m) -> Close Mother's Room (3.4m)
    #                -> Close Phone Booth Call (3.0m) -> Wide Inner Harbor (19.5m) -> Wide Shadowpool Approach (16m)
    # =======================================================================
    "09.0": [
        X("09.set.atlantis_club_sidewalk__p13", "Straddling Wet Neon-Reflected Sidewalk Slab", "P3", 1.48, 1.08, 0.92, 0.18, "span_deck", None),
        X(
            "09.set.atlantis_club_sidewalk__p05",
            "Crimson Neon Club Doorway Wall with Live Footage",
            "P4",
            2.44,
            1.22,
            0.90,
            0.76,
            "wall_with_door_hole",
            "Crimson Club Portal",
            aperture_footage=_portal(_vid(9, 2, 0), "door", (0.24, 0.18, 0.78, 0.95), mullions=True, warm_spill=True),
        ),
        X(
            "09.set.atlantis_club_sidewalk__p06",
            "Cyan-Lit Sidewalk Storefront Window Portal",
            "P3",
            1.40,
            1.47,
            0.90,
            0.74,
            "gable_portal_cap",
            "Sidewalk Storefront",
            aperture_footage=_portal(_vid(9, 3, 0), "window", (0.22, 0.18, 0.78, 0.90), mullions=True, warm_spill=True),
        ),
        X("09.hero.canopy__p02", "Palm & Neon Canopy Boulevard Row", "P4", 2.36, 1.32, 0.48, 0.26, "roof_cornice", None),
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
        dist_mult=0.82,
    ),
    "09.2": [
        X("09.set.mother_living_room__p15", "Straddling Patterned Living Room Rug", "P3", 1.46, 1.06, 0.92, 0.18, "span_deck", None),
        X(
            "09.set.mother_living_room__p01",
            "Close Mother's Living Room Wall with Framed Window Footage",
            "P4",
            2.44,
            1.25,
            0.90,
            0.88,
            "wall_with_door_hole",
            "Mother's Living Room Wall",
            aperture_footage=_portal(_vid(9, 6, 0), "window", (0.24, 0.16, 0.78, 0.86), mullions=True, warm_spill=True),
        ),
        X(
            "09.set.atlantis_club_sidewalk__p04",
            "Teal Hallway Threshold Archway",
            "P3",
            1.40,
            1.48,
            0.90,
            0.78,
            "gable_portal_cap",
            "Lobby Threshold",
            aperture_footage=_portal(_vid(9, 8, 0), "door", (0.24, 0.16, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
        X("09.props.suitcases-notice__p04", "Stacked Vintage Travel Suitcases", "P3", 1.42, 1.12, 0.90, 0.28, "story_prop", None),
    ],
    "09.3": [
        X("09.set.mother_living_room__p15", "Straddling Living Room Baseboard & Rug", "P3", 1.46, 1.05, 0.92, 0.18, "span_deck", None),
        X(
            "09.set.mother_living_room__p01",
            "Intimate Living Room Window Wall with Harbor Memory Footage",
            "P4",
            2.44,
            1.24,
            0.90,
            0.90,
            "wall_with_door_hole",
            "Mother's Window Wall",
            aperture_footage=_portal(_vid(9, 10, 0), "window", (0.24, 0.16, 0.78, 0.86), mullions=True, warm_spill=True),
        ),
        X("09.set.mother_living_room__p02", "Mullioned Wooden Window Casement", "P3", 1.44, 1.24, 0.72, 0.34, "window_dressing", None),
        X(
            "09.props.phonebooth__p02",
            "Close Illuminated Glass Telephone Booth",
            "P3",
            1.38,
            1.47,
            0.90,
            0.78,
            "gable_portal_cap",
            "The Call to Mother",
            aperture_footage=_portal(_vid(9, 11, 0), "window", (0.22, 0.14, 0.78, 0.88), mullions=True, warm_spill=True),
        ),
    ],
    "09.4": [
        X("09.set.harbor_path_east__p07", "Straddling Stone Quay Apron", "P2", 1.08, 1.08, 0.92, 0.18, "ground_curb", None),
        X("09.set.atlantis_harbor_street__p05", "Wide Waterfront Gables & Harbor Warehouses (19.5m)", "P4", 2.44, 1.26, 0.89, 0.36, "boulevard_fence", "Inner Harbor Warehouses"),
        X("09.set.atlantis_harbor_street__p09", "Iron Harbor Quay Loading Crane", "P4", 2.40, 1.14, 0.89, 0.44, "boulevard_lamp", "Harbor Crane Quay"),
        X(
            "09.hero.canopy__p09",
            "Illuminated Waterfront Pergola Portal",
            "P3",
            1.42,
            1.45,
            0.89,
            0.54,
            "gable_portal_cap",
            "Waterfront Pergola",
            aperture_footage=_portal(_vid(9, 13, 0), "arch", (0.24, 0.22, 0.76, 0.94), mullions=False, warm_spill=True),
        ),
    ],
    "09.5": [
        X("09.set.harbor_path_east__p07", "Straddling Harbor Quay Stone Walk", "P2", 1.08, 1.08, 0.92, 0.18, "ground_curb", None),
        X("10.set.atlantis_streets__p04", "Wide Neon Atlantis Street Facade Block", "P4", 2.44, 1.22, 0.89, 0.56, "wall_bay", "Neon Street Facade"),
        X(
            "10.hero.shadowpool__p01",
            "Mosaic Shadowpool Archway Portal Toward Poem 10",
            "P3",
            1.40,
            1.46,
            0.90,
            0.66,
            "gable_portal_cap",
            "Shadowpool Archway",
            aperture_footage=_portal(_vid(10, 1, 0), "arch", (0.24, 0.20, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
    ],

    # =======================================================================
    # POEM 10 · MAGIC RIDE
    # Hand Assembly: Medium Shadowpool Arch (6.8m) -> Wide Neon Overpass (16.5m) -> Far Mountain Road (48m)
    #                -> Wide Solar Avenue (15m) -> Wide Causeway Viaduct (18m) -> Far Dawn Tree Horizon (44m)
    # =======================================================================
    "10.0": [
        X("10.hero.shadowpool__p05", "Straddling Rippling Golden Pool Reflection Strip", "P3", 1.46, 1.08, 0.92, 0.20, "span_deck", None),
        X(
            "10.hero.shadowpool__p01",
            "Outer Mosaic Shadowpool Archway with Street Footage",
            "P4",
            2.44,
            1.22,
            0.90,
            0.78,
            "gable_portal_cap",
            "Shadowpool Outer Arch",
            aperture_footage=_portal(_vid(10, 2, 0), "arch", (0.24, 0.20, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
        X(
            "10.hero.shadowpool__p02",
            "Inner Mosaic Shadowpool Archway",
            "P3",
            1.40,
            1.46,
            0.90,
            0.74,
            "gable_portal_cap",
            "Shadowpool Inner Arch",
            aperture_footage=_portal(_vid(10, 3, 0), "arch", (0.24, 0.20, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
    ],
    "10.1": [
        X("04.hero.viaduct__p07", "Straddling Steel Overpass Guardrail Span", "P3", 1.44, 1.12, 0.90, 0.18, "span_deck", "Overpass Guardrail"),
        X("10.set.atlantis_streets__p05", "Wide Illuminated Atlantis Avenue Block (16.5m)", "P4", 2.44, 1.24, 0.89, 0.54, "wall_bay", "Atlantis Avenue Block"),
        X("10.set.atlantis_streets__p08", "Stepped Neon Spire Tower", "P4", 2.40, 1.46, 0.89, 0.56, "wall_bay", None),
        X("11.props.parked-motorcycle__p01", "Parked Cafe-Racer Motorcycle at Overpass", "P2", 1.08, 1.22, 0.90, 0.24, "story_prop", None),
    ],
    # 10.2 is a 48m EXTREME WIDE MOUNTAIN ROAD VISTA:
    "10.2": [
        X("10.set.mountain_road__p04", "Continuous Mountain Ridge Horizon (48m Vista)", "P5", 3.82, 1.28, 0.78, 0.22, "vista_backing", None),
        X("10.set.mountain_road__p06", "Straddling Asphalt Mountain Highway Deck", "P3", 1.46, 1.16, 0.92, 0.24, "span_deck", "Mountain Highway Tape"),
        X("10.set.mountain_road__p09", "Distant Weathered Canyon Rock Pillar West", "P4", 2.42, 1.18, 0.89, 0.36, "boulevard_tree", "Canyon Rock Pillar"),
        X("10.set.mountain_road__p10", "Distant Weathered Canyon Rock Pillar East", "P4", 2.40, 1.46, 0.89, 0.34, "boulevard_tree", None),
    ],
    "10.3": [
        X("10.set.atlantis_streets__p11", "Straddling Glowing Solar Highway Lane", "P3", 1.48, 1.10, 0.92, 0.16, "span_deck", None),
        X(
            "06.set.narrow_streets__p06",
            "Wide Sunlit Stone Avenue Archway with Causeway Footage",
            "P4",
            2.44,
            1.24,
            0.90,
            0.66,
            "gable_portal_cap",
            "Solar Avenue Archway",
            aperture_footage=_portal(_vid(10, 8, 0), "arch", (0.24, 0.20, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
        X("10.set.atlantis_streets__p06", "Golden-Lit Avenue Facade", "P4", 2.40, 1.46, 0.89, 0.56, "wall_bay", None),
        X("10.props.bike-skeleton__p01", "Cafe-Racer Motorcycle in Full Stride", "P2", 1.08, 1.22, 0.90, 0.24, "story_prop", None),
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
        dist_mult=0.82,
    ),
    # 10.5 is a 44m EXTREME WIDE DAWN TREE HORIZON VISTA:
    "10.5": [
        X("10.set.mountain_road__p05", "Continuous Mountain Ridge Horizon (44m Vista)", "P5", 3.82, 1.28, 0.78, 0.22, "vista_backing", None),
        X("11.hero.steps__p09", "Straddling Broad Stone Temple Approach Steps", "P2", 1.08, 1.08, 0.92, 0.16, "ground_curb", None),
        X("10.props.tree-dawn-sign__p01", "Distant Spreading Dawn Tree on the Ridge", "P4", 2.42, 1.20, 0.89, 0.44, "boulevard_tree", "The Dawn Tree"),
        X("11.props.temple.states__p02", "First Marble Temple Stylobate Plinth · Poem 11", "P3", 1.42, 1.46, 0.90, 0.24, "span_deck", "Temple Site · Poem 11"),
    ],

    # =======================================================================
    # POEM 11 · NEW DAY
    # Hand Assembly: Progressive Lego Temple Construction —
    #   Wide Ruined Steps (17m) -> Wide Rising Colonnade (15.5m) -> Medium Mirror Hall (7m)
    #   -> Medium Completed Temple (7.4m) -> Close Infinity Pool (3.8m) -> Medium Sunlit Portico (6.8m)
    # =======================================================================
    "11.0": [
        X("11.hero.steps__p01", "Straddling Weathered Stone Approach Step", "P2", 1.08, 1.06, 0.92, 0.16, "ground_curb", None),
        X("11.props.ruin__p01", "Wide Ancient Ruined Stone Wall Course (17m)", "P4", 2.44, 1.20, 0.90, 0.52, "wall_bay", "Ruined Stone Wall"),
        X(
            "11.props.ruin__p02",
            "Ancient Ruined Stone Archway Portal",
            "P3",
            1.40,
            1.45,
            0.90,
            0.62,
            "gable_portal_cap",
            "Ruined Sanctuary Arch",
            aperture_footage=_portal(_vid(11, 2, 0), "arch", (0.24, 0.22, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
        X("11.props.temple.arrival.courses-columns__p01", "Marble Stylobate Foundation Course #1", "P3", 1.44, 1.28, 0.91, 0.16, "span_deck", None),
    ],
    "11.1": [
        X("11.hero.pools__p01", "Straddling Turquoise Reflecting Pool Extension", "P3", 1.48, 1.10, 0.92, 0.18, "span_deck", None),
        X(
            "11.props.temple.states__p01",
            "Half-Erected Marble Temple Colonnade Portal",
            "P4",
            2.42,
            1.22,
            0.90,
            0.66,
            "gable_portal_cap",
            "Rising Marble Colonnade",
            aperture_footage=_portal(_vid(11, 4, 0), "arch", (0.22, 0.20, 0.78, 0.94), mullions=False, warm_spill=True),
        ),
        X("11.props.temple.whole__p04", "Fluted Marble Column Shaft #1", "P4", 2.38, 1.42, 0.89, 0.52, "wall_bay", None),
        X("11.props.temple.whole__p05", "Fluted Marble Column Shaft #2", "P4", 2.38, 1.52, 0.89, 0.52, "wall_bay", None),
        X("11.props.temple.arrival.beams__p01", "Carved Marble Architrave Beam", "P4", 2.34, 1.46, 0.48, 0.18, "roof_cornice", None),
    ],
    "11.2": [
        X("11.set.mirror_hall__p04", "Straddling Fluted Mirror-Hall Pier West", "P3", 1.44, 1.04, 0.90, 0.52, "wall_bay", None),
        X(
            "11.set.mirror_hall__p02",
            "Five-Arch Marble Mirror-Hall Arcade with Reflected Footage",
            "P4",
            2.44,
            1.28,
            0.90,
            0.78,
            "wall_with_door_hole",
            "Mirror-Hall Arcade",
            aperture_footage=_portal(_vid(11, 6, 0), "mirror", (0.20, 0.18, 0.80, 0.92), mullions=True, warm_spill=True),
        ),
        X("11.set.mirror_hall__p01", "Vaulted Marble Arch Span", "P4", 2.40, 1.28, 0.44, 0.28, "roof_cornice", None),
        X("11.set.mirror_hall__p05", "Fluted Mirror-Hall Pier East", "P3", 1.44, 1.48, 0.90, 0.52, "wall_bay", None),
    ],
    "11.3": [
        X("11.props.temple.arrival.courses-columns__p02", "Straddling Polished Marble Stylobate Course", "P3", 1.46, 1.12, 0.92, 0.18, "span_deck", None),
        X(
            "11.props.temple.states__p04",
            "Completed Marble Temple Sanctuary & Pediment Portal",
            "P4",
            2.42,
            1.25,
            0.90,
            0.78,
            "gable_portal_cap",
            "Completed Marble Temple",
            aperture_footage=_portal(_vid(11, 9, 0), "arch", (0.24, 0.24, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
        X("11.hero.clocktower__p01", "Tall Brick & Stone Clocktower Spire", "P4", 2.38, 1.48, 0.90, 0.62, "boulevard_lamp", "The New Day Clocktower"),
    ],
    "11.4": [
        X("11.hero.pools__p02", "Straddling Calm Reflecting Water Channel", "P3", 1.48, 1.08, 0.92, 0.18, "span_deck", None),
        X(
            "11.set.temple_infinity_pool__p04",
            "Close Classical Stone Aqueduct Arcade with Pool Footage",
            "P4",
            2.44,
            1.28,
            0.90,
            0.84,
            "wall_with_door_hole",
            "Infinity Pool Arcade",
            aperture_footage=_portal(_vid(11, 11, 0), "arch", (0.22, 0.20, 0.78, 0.94), mullions=True, warm_spill=True),
        ),
        X("12.hero.pools__p04", "Close Marble Pool Column West", "P3", 1.44, 1.10, 0.90, 0.58, "wall_bay", None),
        X("12.hero.pools__p05", "Close Marble Pool Column East", "P3", 1.44, 1.48, 0.90, 0.58, "wall_bay", None),
    ],
    "11.5": [
        X("11.hero.steps__p10", "Straddling Sunlit Stone Stylobate Step", "P2", 1.08, 1.08, 0.92, 0.16, "ground_curb", None),
        X(
            "11.props.temple.whole__p20",
            "Crowned Marble Temple Pediment & Sanctuary Portal",
            "P4",
            2.42,
            1.24,
            0.90,
            0.78,
            "gable_portal_cap",
            "Sunlit Temple Portico",
            aperture_footage=_portal(_vid(12, 1, 0), "arch", (0.24, 0.22, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
        X("12.set.temple_hall__p02", "Broad Marble Sanctuary Arch", "P4", 2.38, 1.46, 0.48, 0.26, "roof_cornice", None),
        X("12.set.temple_hall__p04", "Sanctuary Marble Pillar Into Poem 12", "P3", 1.42, 1.48, 0.90, 0.56, "wall_bay", "Into Poem 12 · Reunion"),
    ],

    # =======================================================================
    # POEM 12 · REUNION
    # Hand Assembly: Medium Temple Backroom (6.5m) -> Wide Olive Grove Tape (17.5m) -> Far Afterlife Threshold (40m)
    #                -> Medium Hourglass Hall (6.2m) -> Wide Western Forest (16m) -> Wide Shore Terrace (18.5m) -> Wide Cafe Approach (15m)
    # =======================================================================
    "12.0": [
        X("12.set.temple_backroom__p08", "Straddling Timber Floorboard Runner", "P3", 1.48, 1.08, 0.92, 0.18, "span_deck", None),
        X(
            "12.set.temple_backroom__p01",
            "Temple Backroom Wall with Open Doorway & Reunion Footage",
            "P4",
            2.42,
            1.26,
            0.90,
            0.86,
            "wall_with_door_hole",
            "Backroom Doorway Threshold",
            aperture_footage=_portal(_vid(12, 2, 0), "door", (0.32, 0.18, 0.78, 0.96), mullions=False, warm_spill=True),
        ),
        X("12.set.temple_backroom__p02", "Stone Staircase Inside the Threshold", "P3", 1.42, 1.48, 0.90, 0.36, "span_deck", None),
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
        dist_mult=0.84,
    ),
    # 12.2 is a 40m EXTREME WIDE AFTERLIFE THRESHOLD VISTA:
    "12.2": [
        X("12.set.temple_hall__p03", "Distant Classical Colonnade Horizon (40m Vista)", "P4", 2.44, 1.24, 0.88, 0.28, "boulevard_fence", "Afterlife Colonnade"),
        X(
            "12.set.temple_hall__p02",
            "Distant Vaulted Marble Sanctuary Arch on Horizon",
            "P3",
            1.40,
            1.44,
            0.88,
            0.42,
            "gable_portal_cap",
            "Afterlife Threshold Arch",
            aperture_footage=_portal(_vid(12, 5, 0), "arch", (0.26, 0.22, 0.74, 0.94), mullions=False, warm_spill=True),
        ),
        X("12.set.temple_backroom__p04", "Distant Empty Wooden Chair West", "P3", 1.42, 1.14, 0.89, 0.20, "furniture_anchor", None),
        X("12.set.temple_backroom__p05", "Distant Empty Wooden Chair East", "P3", 1.40, 1.36, 0.89, 0.20, "furniture_anchor", None),
    ],
    "12.3": [
        X("12.hero.pools__p06", "Straddling Sanctuary Column West", "P3", 1.44, 1.04, 0.90, 0.56, "wall_bay", None),
        X(
            "12.set.temple_hall__p03",
            "Illuminated Hourglass Sanctuary Arcade with Memory Footage",
            "P4",
            2.44,
            1.28,
            0.90,
            0.78,
            "wall_with_door_hole",
            "Hourglass Sanctuary Arcade",
            aperture_footage=_portal(_vid(12, 7, 0), "arch", (0.22, 0.20, 0.78, 0.94), mullions=True, warm_spill=True),
        ),
        X("12.hero.pools__p07", "Sanctuary Column East", "P3", 1.44, 1.48, 0.90, 0.56, "wall_bay", None),
        X("12.props.last-hourglass__p01", "Monumental Wooden Hourglass", "P2", 1.08, 1.28, 0.90, 0.26, "story_prop", "The Last Hourglass"),
    ],
    "12.4": [
        X("12.set.temple_grove__p09", "Straddling Forest Moss & Fern Floor Strip", "P2", 1.08, 1.08, 0.92, 0.16, "ground_curb", None),
        X("12.set.temple_grove__p07", "Interlocking Olive & Cypress Canopy Arch", "P4", 2.42, 1.28, 0.42, 0.30, "roof_cornice", "Western Forest Canopy"),
        X("12.set.temple_grove__p03", "Gnarled Olive Tree Trunk #1", "P3", 1.44, 1.10, 0.90, 0.56, "boulevard_tree", None),
        X("12.set.temple_grove__p04", "Gnarled Olive Tree Trunk #2", "P3", 1.42, 1.29, 0.90, 0.54, "boulevard_tree", None),
        X("12.set.temple_grove__p05", "Gnarled Olive Tree Trunk #3", "P3", 1.44, 1.48, 0.90, 0.56, "boulevard_tree", None),
    ],
    "12.5": [
        X("12.set.temple_shore_terrace__p06", "Straddling Wet Flagstone Shore Landing", "P2", 1.08, 1.08, 0.92, 0.18, "ground_curb", None),
        X("12.set.temple_shore_terrace__p05", "Broad Stone Shore-Terrace Staircase (18.5m Wide)", "P3", 1.44, 1.22, 0.91, 0.32, "span_deck", "Shore Terrace Stairs"),
        X("12.hero.pools__p01", "Terrace Stone Balustrade", "P4", 2.40, 1.42, 0.89, 0.22, "boulevard_fence", None),
        X("12.hero.pools__p02", "Terrace Cypress Tree", "P4", 2.36, 1.48, 0.89, 0.54, "boulevard_tree", None),
    ],
    "12.6": [
        X("13.set.harbor_quay_night_fire__p03", "Straddling Harbor Quay Stone Promenade", "P3", 1.48, 1.10, 0.92, 0.18, "span_deck", None),
        X(
            "13.hero.cafe__p01",
            "Corner Cafe Storefront with Warm Bistro Footage Inside",
            "P4",
            2.42,
            1.25,
            0.90,
            0.68,
            "wall_with_door_hole",
            "The Corner Cafe · Poem 13",
            aperture_footage=_portal(_vid(13, 1, 0), "window", (0.20, 0.20, 0.80, 0.92), mullions=True, warm_spill=True),
        ),
        X("13.hero.cafe__p02", "Shingled Cafe Awning Roof", "P4", 2.38, 1.25, 0.48, 0.24, "roof_cornice", None),
        X(
            "13.props.distant-window__p01",
            "Brick Gabled House with Lit Window Footage",
            "P3",
            1.40,
            1.48,
            0.90,
            0.66,
            "gable_portal_cap",
            "Brick Gable House",
            aperture_footage=_portal(_vid(13, 2, 0), "window", (0.28, 0.24, 0.72, 0.86), mullions=True, warm_spill=True),
        ),
    ],

    # =======================================================================
    # POEM 13 · HOW TO WIN MY HEART
    # Hand Assembly: Wide Cafe Exterior (14.5m) -> Intimate Close Bistro Table (2.9m) -> Medium Sleepdam (7.6m)
    #                -> Far Drowned Atrium (42m) -> Wide Poppy Meadow (16.5m) -> Medium Distant Window (6.0m) -> Wide Harbor Quay (18m)
    # =======================================================================
    "13.0": [
        X("13.props.cafe__p01", "Straddling Round Bistro Table on Sidewalk", "P2", 1.08, 1.05, 0.91, 0.22, "furniture_anchor", None),
        X(
            "13.hero.cafe__p01",
            "Teal Timber Cafe Facade with Door & Window Footage",
            "P4",
            2.44,
            1.24,
            0.90,
            0.70,
            "wall_with_door_hole",
            "Corner Cafe Entrance",
            aperture_footage=_portal(_vid(13, 3, 0), "door", (0.22, 0.18, 0.78, 0.94), mullions=True, warm_spill=True),
        ),
        X("13.hero.cafe__p02", "Slate Cafe Eaves Roof", "P4", 2.40, 1.24, 0.48, 0.24, "roof_cornice", None),
        X(
            "13.props.distant-window__p01",
            "Neighboring Brick Gable House with Lit Window",
            "P3",
            1.40,
            1.48,
            0.90,
            0.68,
            "gable_portal_cap",
            "Distant Window Gable",
            aperture_footage=_portal(_vid(13, 4, 0), "window", (0.28, 0.24, 0.72, 0.86), mullions=True, warm_spill=True),
        ),
    ],
    # 13.1 is a 2.9m INTIMATE CLOSE-UP of the Cafe Table & Window:
    "13.1": [
        X("13.hero.catwalk__p01", "Straddling Harbor Terrace Rail", "P3", 1.44, 1.06, 0.90, 0.18, "span_deck", "Harbor Steel Catwalk"),
        X(
            "13.set.harbor_cafe__p10",
            "Intimate Close Harbor Cafe Mullioned Window with Quay Footage",
            "P4",
            2.44,
            1.24,
            0.90,
            0.92,
            "wall_with_door_hole",
            "Harbor Cafe Terrace Window",
            aperture_footage=_portal(_vid(13, 5, 0), "window", (0.20, 0.16, 0.80, 0.88), mullions=True, warm_spill=True),
        ),
        X("13.set.harbor_quay_night_fire__p02", "Close Cast-Iron Harbor Quay Lamp", "P3", 1.40, 1.46, 0.90, 0.58, "boulevard_lamp", None),
    ],
    "13.2": [
        X("13.hero.sleepdam__p02", "Straddling Turbulent Dam Tailrace Water Strip", "P2", 1.08, 1.08, 0.92, 0.18, "ground_curb", None),
        X("13.hero.sleepdam__p01", "Monumental Concrete Sleepdam Spillway Wall", "P4", 2.44, 1.26, 0.90, 0.56, "wall_bay", "Sleepdam Spillway Wall"),
        X("13.hero.catwalk__p01", "Upper Dam Steel Walkway Bridge", "P3", 1.44, 1.26, 0.62, 0.18, "span_deck", None),
        X(
            "13.props.distant-window__p09",
            "Brick Gabled Cottage with Warm Window Footage Above Dam",
            "P3",
            1.40,
            1.48,
            0.90,
            0.66,
            "gable_portal_cap",
            "Cottage Above the Dam",
            aperture_footage=_portal(_vid(13, 7, 0), "window", (0.26, 0.24, 0.74, 0.86), mullions=True, warm_spill=True),
        ),
    ],
    # 13.3 is a 42m EXTREME WIDE DROWNED ATRIUM VISTA:
    "13.3": [
        X("13.set.drowned_atrium__p05", "Straddling Stone Planter Box with Ferns", "P3", 1.42, 1.08, 0.90, 0.20, "ground_curb", None),
        X(
            "13.set.drowned_atrium__p01",
            "Distant Drowned Atrium Mullioned Window Wall (42m Vista)",
            "P4",
            2.44,
            1.26,
            0.89,
            0.42,
            "gable_portal_cap",
            "Drowned Atrium Window Wall",
            aperture_footage=_portal(_vid(13, 8, 0), "window", (0.20, 0.18, 0.80, 0.88), mullions=True, warm_spill=True),
        ),
        X("13.set.drowned_atrium__p03", "Distant Spreading Atrium Shade Tree", "P4", 2.38, 1.46, 0.89, 0.42, "boulevard_tree", None),
    ],
    "13.4": [
        X("13.set.flower_field__p05", "Straddling Scarlet Poppy Meadow Bank West", "P3", 1.42, 1.08, 0.91, 0.26, "ground_curb", "Scarlet Poppy Meadow"),
        X(
            "13.set.church_pews__p02",
            "Garden Chapel Double-Lancet Window Arch with Meadow Footage",
            "P4",
            2.44,
            1.24,
            0.90,
            0.66,
            "gable_portal_cap",
            "Garden Chapel Arch",
            aperture_footage=_portal(_vid(13, 10, 0), "window", (0.24, 0.18, 0.76, 0.90), mullions=True, warm_spill=True),
        ),
        X("13.set.drowned_atrium__p03", "Spreading Meadow Shade Tree", "P4", 2.38, 1.46, 0.89, 0.56, "boulevard_tree", None),
        X("13.set.flower_field__p06", "Lavender & Wildflower Bank East", "P3", 1.40, 1.42, 0.91, 0.26, "ground_curb", None),
    ],
    "13.5": [
        X("13.set.church_pews__p09", "Straddling Checkered Stone Nave Floor", "P2", 1.08, 1.06, 0.92, 0.16, "ground_curb", None),
        X(
            "13.props.distant-window__p01",
            "Brick Gabled House with Open Window & Harbor Footage",
            "P4",
            2.44,
            1.22,
            0.90,
            0.82,
            "wall_with_door_hole",
            "Brick Gable Window",
            aperture_footage=_portal(_vid(13, 11, 0), "window", (0.28, 0.22, 0.72, 0.88), mullions=True, warm_spill=True),
        ),
        X(
            "13.set.church_pews__p02",
            "Carved Stone Gothic Window Portal",
            "P3",
            1.40,
            1.46,
            0.90,
            0.78,
            "gable_portal_cap",
            "Gothic Window Portal",
            aperture_footage=_portal(_vid(13, 12, 0), "window", (0.24, 0.18, 0.76, 0.92), mullions=True, warm_spill=True),
        ),
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
        dist_mult=0.84,
    ),

    # =======================================================================
    # POEM 14 · OUT OF LIFE (FINALE)
    # Hand Assembly: Far Atlantis Harbor Citadel (56m) -> Cosmic Void Film-Reels (92m) -> Medium Memory Gallery (6.6m)
    #                -> Cosmic Graytone Sprocket Void (98m) -> Close Vintage Door Opening (3.2m)
    #                -> Medium 1940s Ballroom Waltz (7.0m) -> Close Genesis Bedroom Return (3.3m)
    # =======================================================================
    # 14.0 is a 56m EXTREME WIDE HARBOR CITADEL VISTA:
    "14.0": [
        X("14.set.harbor_atlantis_wide__p04", "Distant Island Citadel of Atlantis (56m Vista)", "P5", 3.82, 1.24, 0.78, 0.24, "vista_backing", None),
        X("14.set.harbor_atlantis_wide__p07", "Straddling Long Stone Harbor Breakwater", "P2", 1.08, 1.10, 0.92, 0.14, "ground_curb", None),
        X("14.set.harbor_atlantis_wide__p05", "Distant Waterfront Colonnade Pier", "P4", 2.44, 1.44, 0.88, 0.26, "span_deck", "Atlantis Harbor Pier"),
        X("14.set.harbor_atlantis_wide__p06", "Miniature Gaff-Rigged Harbor Sailboat", "P3", 1.42, 1.18, 0.89, 0.20, "story_prop", None),
    ],
    # 14.1 is a 92m COSMIC VOID WITH FLOATING 35MM FILM REELS:
    "14.1": [
        X("14.set.black_void__p03", "Straddling Film-Stage Threshold Plinth", "P2", 1.08, 1.08, 0.92, 0.14, "ground_curb", None),
        X(
            "14.set.broll_life__p03",
            "Floating 35mm Cinema Filmstrip Portal with Life-Reel Footage",
            "P4",
            2.44,
            1.20,
            0.86,
            0.52,
            "gable_portal_cap",
            "Memory Filmstrip Portal",
            aperture_footage=_portal(_vid(14, 3, 0), "screen", (0.18, 0.16, 0.82, 0.86), mullions=False, warm_spill=True, alt_footage_file=_da69(391)),
        ),
        X(
            "14.props.door__p01",
            "Distant Standing Timber Door #1 in the Void",
            "P3",
            1.40,
            1.44,
            0.89,
            0.52,
            "gable_portal_cap",
            "First Memory Door",
            aperture_footage=_portal(_vid(14, 4, 0), "door", (0.22, 0.12, 0.78, 0.94), mullions=False, warm_spill=True),
        ),
    ],
    "14.2": [
        X("13.set.flower_field__p05", "Straddling Scarlet Poppies Along Baseboard", "P2", 1.08, 1.06, 0.92, 0.22, "ground_curb", None),
        X(
            "12.set.temple_backroom__p01",
            "Life-Reel Gallery Wall with Open Doorway & Archival Footage",
            "P4",
            2.44,
            1.24,
            0.90,
            0.84,
            "wall_with_door_hole",
            "Life-Reel Gallery Wall",
            aperture_footage=_portal(_vid(14, 5, 0), "door", (0.32, 0.18, 0.78, 0.96), mullions=False, warm_spill=True, alt_footage_file=_da69(451)),
        ),
        X(
            "14.props.door__p02",
            "Carved Vintage Wooden Door #2 with Warm Light",
            "P3",
            1.40,
            1.46,
            0.90,
            0.76,
            "gable_portal_cap",
            "Second Memory Door",
            aperture_footage=_portal(_vid(14, 6, 0), "door", (0.22, 0.12, 0.78, 0.95), mullions=False, warm_spill=True),
        ),
        X("14.props.party__p19", "Festive Paper Lantern Garland", "P3", 1.36, 1.28, 0.36, 0.22, "ceiling_fixture", None),
    ],
    # 14.3 is a 98m COSMIC GRAYTONE 35MM SPROCKET VOID:
    "14.3": [
        X("01.hero.catwalk__p03", "Straddling Graytone Iron Catwalk Deck", "P3", 1.46, 1.06, 0.90, 0.16, "span_deck", None),
        X(
            "14.fx.filmframe__p01",
            "Floating 35mm Sprocket Portal with Archival Memory Footage",
            "P4",
            2.44,
            1.22,
            0.86,
            0.52,
            "gable_portal_cap",
            "35mm Sprocket Portal",
            aperture_footage=_portal(_da69(511), "screen", (0.18, 0.16, 0.82, 0.84), mullions=False, warm_spill=True, alt_footage_file=_vid(14, 7, 0)),
        ),
        X(
            "14.props.door__p03",
            "Half-Open Vintage Wooden Door #3 in the Void",
            "P3",
            1.40,
            1.45,
            0.89,
            0.56,
            "gable_portal_cap",
            "Third Memory Door",
            aperture_footage=_portal(_vid(14, 8, 0), "door", (0.22, 0.12, 0.78, 0.95), mullions=False, warm_spill=True),
        ),
    ],
    # 14.4 is a 3.2m CLOSE-UP of the Vintage Door swinging wide open into the Ballroom:
    "14.4": [
        X("14.set.vintage_party__p04", "Straddling Polished Ballroom Parquet Threshold", "P3", 1.48, 1.06, 0.92, 0.22, "span_deck", None),
        X(
            "14.set.vintage_party__p02",
            "Close Wood-Panelled Ballroom Wall & Illuminated Window",
            "P4",
            2.44,
            1.24,
            0.90,
            0.90,
            "wall_with_door_hole",
            "Ballroom Wall Extension",
            aperture_footage=_portal(_vid(14, 8, 12), "window", (0.24, 0.16, 0.78, 0.88), mullions=True, warm_spill=True),
        ),
        X(
            "14.set.vintage_party__p03",
            "Close Grand Timber Ballroom Doorway Arch with Waltz Footage",
            "P3",
            1.40,
            1.46,
            0.90,
            0.88,
            "gable_portal_cap",
            "The Vintage Doorway",
            aperture_footage=_portal(_vid(1, 9, 0), "arch", (0.24, 0.18, 0.76, 0.96), mullions=False, warm_spill=True),
        ),
    ],
    "14.5": [
        X("14.set.vintage_party__p04", "Straddling Polished Parquet Waltz Floor", "P3", 1.48, 1.08, 0.92, 0.22, "span_deck", None),
        X(
            "14.set.vintage_party__p03",
            "Grand Ballroom Timber Archway Portal",
            "P4",
            2.42,
            1.24,
            0.90,
            0.80,
            "gable_portal_cap",
            "Ballroom Waltz Arch",
            aperture_footage=_portal(_vid(14, 9, 0), "arch", (0.24, 0.18, 0.76, 0.95), mullions=False, warm_spill=True),
        ),
        X(
            "12.set.temple_backroom__p01",
            "Transition Threshold Wall Back to the Genesis Bedroom",
            "P4",
            2.38,
            1.46,
            0.90,
            0.82,
            "wall_with_door_hole",
            "Doorway to Genesis Bedroom",
            aperture_footage=_portal(_vid(1, 1, 0), "door", (0.32, 0.18, 0.78, 0.96), mullions=False, warm_spill=True),
        ),
    ],
    # 14.6 is a 3.3m CLOSE-UP return to the Genesis Bedroom (`01.0`):
    "14.6": [
        X("01.hero.severn__p07", "Straddling Genesis Bedroom Baseboard Beam", "P3", 1.48, 1.05, 0.92, 0.16, "ground_curb", None),
        X(
            "12.set.temple_backroom__p01",
            "Close Genesis Bedroom Wall with Open Doorway Looping to Poem 01",
            "P4",
            2.44,
            1.24,
            0.90,
            0.88,
            "wall_with_door_hole",
            "Genesis Loop Doorway · Poem 01",
            aperture_footage=_portal(_vid(1, 1, 0), "door", (0.34, 0.18, 0.80, 0.96), mullions=False, warm_spill=True),
        ),
        X(
            "01.props.window__p01",
            "Close Dawn Bedroom Sash Window with Morning Footage",
            "P3",
            1.40,
            1.47,
            0.86,
            0.68,
            "gable_portal_cap",
            "Dawn Sash Window",
            aperture_footage=_portal(_vid(1, 2, 12), "window", (0.18, 0.14, 0.82, 0.86), mullions=True, warm_spill=True),
        ),
    ],
}


def get_scene_shot_profile(skey: str) -> Dict[str, Any]:
    """Returns a copy of the hand-calibrated Shot Scale & Camera Distance profile for `skey`."""
    prof = SCENE_SHOT_PROFILES.get(skey)
    if not prof:
        return _sp("MEDIUM_STAGE", 6.8, 40, 116.0, 0.58, "Standard medium stage")
    return dict(prof)


def get_in_frame_portal_footage(skey: str, part_id: str, label: str = "", anim_role: str = "") -> Optional[Dict[str, Any]]:
    """
    Returns layered multiplane `aperture_footage` for any in-frame door, window, arch,
    television screen, mirror, or film-frame piece in `skey`.
    """
    exact = IN_FRAME_PORTAL_FOOTAGE.get(f"{skey}:{part_id}")
    if exact:
        return dict(exact)
    by_part = IN_FRAME_PORTAL_FOOTAGE.get(part_id)
    if by_part:
        return dict(by_part)

    # Automatic fallback for any in-frame door/window/arch/screen/mirror piece
    s = f"{part_id} {label} {anim_role}".lower()
    poem_num = int(skey.split(".")[0]) if "." in skey else 1
    sc_idx = int(skey.split(".")[1]) if "." in skey else 0
    shot_idx = max(1, (sc_idx * 2) % 9 + 1)

    if any(k in s for k in ("window", "rose-window", "porthole", "booth")):
        return _portal(_vid(poem_num, shot_idx, 0), "window", (0.20, 0.16, 0.80, 0.86), mullions=True, warm_spill=True)
    if any(k in s for k in ("door", "trapdoor")):
        return _portal(_vid(poem_num, shot_idx, 0), "door", (0.22, 0.14, 0.78, 0.95), mullions=False, warm_spill=True)
    if any(k in s for k in ("tv", "television", "filmframe", "reel__p01")):
        return _portal(_vid(poem_num, shot_idx, 0), "screen", (0.16, 0.14, 0.84, 0.76), mullions=False, warm_spill=True)
    if "mirror" in s:
        return _portal(_vid(poem_num, shot_idx, 0), "mirror", (0.20, 0.14, 0.80, 0.86), mullions=False, warm_spill=True)
    if any(k in s for k in ("portal_aperture", "portal_other_world")) and any(k in s for k in ("arch", "gate", "colonnade", "marquee")):
        return _portal(_vid(poem_num, shot_idx, 0), "arch", (0.24, 0.20, 0.76, 0.94), mullions=False, warm_spill=True)
    return None


def get_scene_lego_extension(skey: str) -> List[Dict[str, Any]]:
    """Returns a deep copy of the hand-assembled outside-the-frame Lego set extension layers for `skey`."""
    raw = SCENE_LEGO_EXTENSIONS.get(skey, [])
    out = []
    for item in raw:
        d = dict(item)
        if "aperture_footage" in d and d["aperture_footage"] is not None:
            d["aperture_footage"] = dict(d["aperture_footage"])
        out.append(d)
    return out
