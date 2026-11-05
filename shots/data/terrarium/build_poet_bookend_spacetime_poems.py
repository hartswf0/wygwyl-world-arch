#!/usr/bin/env python3
"""
PLANE-SYNCHRONIZED SEGMENTED BOOKEND ENGINE (POEMS 01–14 & AGENT K 1:49 PARALLEL)
=================================================================================
Replaces flat/muddy mist overlays with TRUE MULTIPLANE SEGMENTED DECOMPOSITIONS &
PLANE-BY-PLANE TRANSITIONS across:
  - All 8 Poet Lectern production shots (`shots/out/poet_01..08/`)
  - All 8 Agent K / Toy Wooden Horse keyframes (`shots/out/k_01..08/`)
  - All 14 Poems' Hero & Echo Common Place shots (`shots/out/<uuid>/`)

Every shot has 6 pixel-registered segmented representations:
  1. `raw`      (`image.jpg`): Photographic / live-action plate
  2. `overlay`  (`overlay.jpg`): Mask2Former + OwlViT + SAM semantic/instance masks + horizon
  3. `layout`   (`cartoon/layout_sheet.png`): Classical animation layout sheet (P0..P6 contours + 3D perspective grid + VP)
  4. `cel`      (`cartoon/cel.png`): Painted animation cel (atmospheric flats + variable-width ink + glow)
  5. `angular`  (`program/frame0.png`): Angular polygon vector scene program (2-stop linear gradients per plane)
  6. `exploded` (`multiplane/exploded.jpg` + `planes.npz`): 7-plane (`P0..P6`) RGBA sheets with parallax

How Plane-Synchronized Transitions Work (Why Every Transition Matters):
  - ACT I   (0.0s – 3.8s) · OPENING LECTERN BOOKEND (`poet_01` -> `poet_02` -> `poet_03`):
      Live-action salon -> plane-by-plane structural lock (`P5` mural -> `P3` listeners/lamps ->
      `P1` acrylic lectern -> `P2` Poet) stepping through `layout_sheet` -> `cel` -> `angular program`
      with real multiplane depth parallax (`1/Z`).
  - ACT II  (3.8s – 7.0s) · THE THRESHOLD: CROSS-WORLD PLANE REPLACEMENT (`poet_04` -> `poet_05` -> `poet_06`):
      Using exact `planes.npz` (`L` in 0..6) for both the Poet shot and the incoming Poem shot:
        * First, `P5 & P4` (background wall behind the Poet) peel open along segmented polygon boundaries
          to reveal the Poem's `layout_sheet.png` perspective blueprint and `cel.png` architecture.
        * Second, inside the segmented mask of the Clear Acrylic Lectern (`P1` in `poet_05`/`poet_06`),
          the Poem's `angular program` (`frame0.png`) & live motion (`shot.mp4`) ignite like an optical prism.
        * Third, the Poet's segmented figure & open hands (`P2` in `poet_06`) morph via optical flow and
          distance-transform contour hand-off into the Poem's Hero (`P2/P3`).
  - ACT III (7.0s – 11.2s) · INSIDE THE POEM'S SEGMENTED WORLD:
      Multiplane parallax traversal across the Poem's `layout_sheet.png` -> `cartoon/cel.png` ->
      `program/frame0.png` -> live `shot.mp4` + `spacetime_worm.mp4`.
  - ACT IV  (11.2s – 14.6s) · THE "WOODEN HORSE" EMOTIONAL ANCHOR (`P2 / P3` ISOLATION):
      Environment planes (`P4, P5, P6`) drop into the quiet `layout_sheet.png` / `notan.png` blueprint,
      while `P2 & P3` (the Poem's segmented Hero / Emotional Anchor + painted cel patch `PNN-001.mp4` +
      `glow_pass.png`) blaze at 100% full-color clarity with heavy ink contours.
  - ACT V   (14.6s – 18.0s) · CLOSING BOOKEND: RETURN TO THE CIRCLE OF LISTENERS (`poet_07` -> `poet_08`):
      Plane-by-plane reassembly: first the Poet's foreground silhouette (`P2` in `poet_08`) locks in over
      the receding poem planes, then `P3` (the segmented Circle of Listeners in the dark) transitions from
      `layout_sheet` -> `cel` -> `angular program` -> warm live-action reality.
"""

import os
import sys
import json
import math
import glob
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import cv2
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots"
OUT_DIR = os.path.join(ROOT, "out")
TERR_DIR = os.path.join(ROOT, "data/terrarium")
FILM_OUT_DIR = os.path.join(TERR_DIR, "seeing_spacetime_films")
POET_DIR = os.path.join(TERR_DIR, "poet_lectern")
BOOKEND_VID_DIR = os.path.join(ROOT, "videos/poet_bookends")
ARTIFACT_DIR = "/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584"

os.makedirs(POET_DIR, exist_ok=True)
os.makedirs(BOOKEND_VID_DIR, exist_ok=True)

sys.path.insert(0, TERR_DIR)
from build_stelline_wooden_horse_spacetime import get_font, MEMORY_SEGMENTS


def load_font(size, mono=False, serif=False):
    if mono:
        return get_font("mono", size)
    if serif:
        return get_font("serif", size)
    return get_font("sans", size)


def ease(t):
    t = float(np.clip(t, 0.0, 1.0))
    return t * t * (3.0 - 2.0 * t)


# ==============================================================================
# 1. THE 8 POET LECTERN STAGES & 8 AGENT K STAGES (WITH ALL 6 SEGMENTED MODES)
# ==============================================================================
POET_LECTERN_STAGES = [
    {
        "id": "poet_01",
        "sid": "poet_01_warm_salon_circle_wide",
        "k_sid": "k_01_office_interview",
        "act": "ACT I · OPENING BOOKEND (SALON WIDE)",
        "file": "data/terrarium/poet_lectern/poet_01_warm_salon_circle_wide.jpg",
        "mist_file": "data/terrarium/poet_lectern/poet_01_dope_composite.jpg",
        "angular_file": "out/poet_01_warm_salon_circle_wide/program/frame0.png",
        "cel_file": "out/poet_01_warm_salon_circle_wide/cartoon/cel.png",
        "layout_file": "out/poet_01_warm_salon_circle_wide/cartoon/layout_sheet.png",
        "overlay_file": "out/poet_01_warm_salon_circle_wide/overlay.jpg",
        "exploded_file": "out/poet_01_warm_salon_circle_wide/multiplane/exploded.jpg",
        "title": "The Warm Graffiti Salon & Circle of Listeners",
        "k_parallel": "1:49.00 – 1:54.50 (k_01) · Joshi & K across the office table",
        "claim": "Segmented 7-plane salon: P1 Clear Acrylic Lectern, P2 Seated Poet, P3 Circle of Listeners & Twin Warm Lamps, P4/P5 Graffiti Mural.",
    },
    {
        "id": "poet_02",
        "sid": "poet_02_warm_lectern_medium",
        "k_sid": "k_01_office_interview",
        "act": "ACT I · OPENING BOOKEND (LECTERN MEDIUM)",
        "file": "data/terrarium/poet_lectern/poet_02_warm_lectern_medium.jpg",
        "mist_file": "data/terrarium/poet_lectern/poet_02_dope_composite.jpg",
        "angular_file": "out/poet_02_warm_lectern_medium/program/frame0.png",
        "cel_file": "out/poet_02_warm_lectern_medium/cartoon/cel.png",
        "layout_file": "out/poet_02_warm_lectern_medium/cartoon/layout_sheet.png",
        "overlay_file": "out/poet_02_warm_lectern_medium/overlay.jpg",
        "exploded_file": "out/poet_02_warm_lectern_medium/multiplane/exploded.jpg",
        "title": "At the Clear Acrylic Lectern — Plane Deconstruction Begins",
        "k_parallel": "1:54.50 – 2:00.29 (k_01) · 'Tell me a memory from when you were a kid'",
        "claim": "P1 Acrylic Stand in foreground (Z=2.2m), P2 Poet Hero Cutout (Z=2.9m), P3 Lamp & Listener (Z=1.55m), P5 Mural (Z=20.3m).",
    },
    {
        "id": "poet_03",
        "sid": "poet_03_standing_graffiti_gesture",
        "k_sid": "k_02_k_eyes_threshold",
        "act": "ACT I · OPENING BOOKEND (INCITING GESTURE)",
        "file": "data/terrarium/poet_lectern/poet_03_standing_graffiti_gesture.jpg",
        "mist_file": "data/terrarium/poet_lectern/poet_03_dope_composite.jpg",
        "angular_file": "out/poet_03_standing_graffiti_gesture/program/frame0.png",
        "cel_file": "out/poet_03_standing_graffiti_gesture/cartoon/cel.png",
        "layout_file": "out/poet_03_standing_graffiti_gesture/cartoon/layout_sheet.png",
        "overlay_file": "out/poet_03_standing_graffiti_gesture/overlay.jpg",
        "exploded_file": "out/poet_03_standing_graffiti_gesture/multiplane/exploded.jpg",
        "title": "Standing Before the Mural — P0 Framing Silhouettes & P2 Gesture",
        "k_parallel": "2:00.29 – 2:03.40 (k_02) · 'I had a little toy horse...'",
        "claim": "Foreground audience silhouettes lock into P0 camera mask while P2 (The Poet) raises his index finger and P4/P5 steps into Angular Vector planes.",
    },
    {
        "id": "poet_04",
        "sid": "poet_04_standing_hands_heart",
        "k_sid": "k_02_k_eyes_threshold",
        "act": "ACT II · THE THRESHOLD (HANDS TO HEART)",
        "file": "data/terrarium/poet_lectern/poet_04_standing_hands_heart.jpg",
        "mist_file": "data/terrarium/poet_lectern/poet_04_dope_composite.jpg",
        "angular_file": "out/poet_04_standing_hands_heart/program/frame0.png",
        "cel_file": "out/poet_04_standing_hands_heart/cartoon/cel.png",
        "layout_file": "out/poet_04_standing_hands_heart/cartoon/layout_sheet.png",
        "overlay_file": "out/poet_04_standing_hands_heart/overlay.jpg",
        "exploded_file": "out/poet_04_standing_hands_heart/multiplane/exploded.jpg",
        "title": "Recall Tied to Feeling — Background Planes Peel Into Poem Blueprint",
        "k_parallel": "2:03.40 – 2:06.86 (k_02) · 'Wait — I remember lots of kids. Everything's grey.'",
        "claim": "While P2 (The Poet with hands to chest) stays razor-sharp, P4/P5 behind him peels open to reveal the Poem's layout blueprint.",
    },
    {
        "id": "poet_05",
        "sid": "poet_05_close_pages_threshold",
        "k_sid": "k_03_orphanage_catwalks",
        "act": "ACT II · THE THRESHOLD (THROUGH THE GLASS PAGES)",
        "file": "data/terrarium/poet_lectern/poet_05_close_pages_threshold.jpg",
        "mist_file": "data/terrarium/poet_lectern/poet_05_dope_composite.jpg",
        "angular_file": "out/poet_05_close_pages_threshold/program/frame0.png",
        "cel_file": "out/poet_05_close_pages_threshold/cartoon/cel.png",
        "layout_file": "out/poet_05_close_pages_threshold/cartoon/layout_sheet.png",
        "overlay_file": "out/poet_05_close_pages_threshold/overlay.jpg",
        "exploded_file": "out/poet_05_close_pages_threshold/multiplane/exploded.jpg",
        "title": "The Acrylic Lectern Prism — Poem Planes Refract Through Glass",
        "k_parallel": "2:06.86 (k_03) · Office walls swap into Orphanage Catwalks",
        "claim": "Inside the segmented mask of the translucent acrylic stand, the Poem's Angular Vector Program and perspective grid ignite.",
    },
    {
        "id": "poet_06",
        "sid": "poet_06_chiaroscuro_open_hands",
        "k_sid": "k_06_wooden_horse_palm",
        "act": "ACT II → III · CHIAROSCURO HAND-OFF",
        "file": "data/terrarium/poet_lectern/poet_06_chiaroscuro_open_hands.jpg",
        "mist_file": "data/terrarium/poet_lectern/poet_06_dope_composite.jpg",
        "angular_file": "out/poet_06_chiaroscuro_open_hands/program/frame0.png",
        "cel_file": "out/poet_06_chiaroscuro_open_hands/cartoon/cel.png",
        "layout_file": "out/poet_06_chiaroscuro_open_hands/cartoon/layout_sheet.png",
        "overlay_file": "out/poet_06_chiaroscuro_open_hands/overlay.jpg",
        "exploded_file": "out/poet_06_chiaroscuro_open_hands/multiplane/exploded.jpg",
        "title": "Chiaroscuro Open Hands — P2 Hero-to-Hero Morph Into the Poem",
        "k_parallel": "2:24 – 2:28 (k_05/k_06) · Hands holding the Carved Wooden Horse (6·10·21)",
        "claim": "The Poet's segmented face, 5 open fingers, and acrylic rim step into Angular Vector & Cel ink, handing off directly to the Poem's P2 Hero.",
    },
    {
        "id": "poet_07",
        "sid": "poet_07_chiaroscuro_wide_circle",
        "k_sid": "k_07_burying_horse_ash",
        "act": "ACT V · CLOSING BOOKEND (RETURN TO DARKENED CIRCLE)",
        "file": "data/terrarium/poet_lectern/poet_07_chiaroscuro_wide_circle.jpg",
        "mist_file": "data/terrarium/poet_lectern/poet_07_dope_composite.jpg",
        "angular_file": "out/poet_07_chiaroscuro_wide_circle/program/frame0.png",
        "cel_file": "out/poet_07_chiaroscuro_wide_circle/cartoon/cel.png",
        "layout_file": "out/poet_07_chiaroscuro_wide_circle/cartoon/layout_sheet.png",
        "overlay_file": "out/poet_07_chiaroscuro_wide_circle/overlay.jpg",
        "exploded_file": "out/poet_07_chiaroscuro_wide_circle/multiplane/exploded.jpg",
        "title": "Reassembling the Room — P0 Circle Silhouettes & P2 Spotlight",
        "k_parallel": "2:36 – 3:06 (k_07) · Burying the horse in ash & returning to the room",
        "claim": "The Poem's midground planes recede behind the segmented P0 silhouettes of the circle and P2 spotlight on the Poet.",
    },
    {
        "id": "poet_08",
        "sid": "poet_08_ots_circle_listeners",
        "k_sid": "k_08_stelline_scanner_return",
        "act": "ACT V · CLOSING BOOKEND (THE CIRCLE OF LISTENERS)",
        "file": "data/terrarium/poet_lectern/poet_08_ots_circle_listeners.jpg",
        "mist_file": "data/terrarium/poet_lectern/poet_08_dope_composite.jpg",
        "angular_file": "out/poet_08_ots_circle_listeners/program/frame0.png",
        "cel_file": "out/poet_08_ots_circle_listeners/cartoon/cel.png",
        "layout_file": "out/poet_08_ots_circle_listeners/cartoon/layout_sheet.png",
        "overlay_file": "out/poet_08_ots_circle_listeners/overlay.jpg",
        "exploded_file": "out/poet_08_ots_circle_listeners/multiplane/exploded.jpg",
        "title": "Over-the-Shoulder Reverse Shot — Segmented Listeners Receive the Memory",
        "k_parallel": "3:06 – 3:25 (k_08) · 'Someone lived this. Yes... this happened.'",
        "claim": "Past the Poet's segmented back silhouette (P2), the 8 segmented listeners (P3) resolve from Angular Vector & Cel back into warm reality.",
    },
]

from build_segmented_poet_and_k_pipeline import K_SHOT_SPECS

POEM_BOOKEND_SPECS = [
    {
        "num": 1, "title": "Out of Life",
        "wooden_horse_anchor": "The Blue Vape Ember on the Fire Escape (P2/P3 Isolated Hero)",
        "anchor_detail": "Environment planes P4–P6 drop into classical layout blueprint & angular polygons while P2/P3 (the figure on the fire escape & blue ember glow) burns at 100% clarity.",
        "opening_cue": "What we've made we don't want, what we've sold to the world, to ourselves, doesn't exist.",
        "peak_cue": "I look for a way out through the hallways, within the drawers and fire escapes, trip on my own words, falling out of life...",
        "closing_cue": "...following the full distance between us almost having it all and starting anew, to rediscover when love was real.",
    },
    {
        "num": 2, "title": "Flashing Lights",
        "wooden_horse_anchor": "Red Tail-Lights & Strobe Reflections on Wet Asphalt (P2/P3)",
        "anchor_detail": "The avenue planes P4–P5 step into blue-pencil layout grid while the crimson/amber strobe planes P2–P3 blaze with full cel ink & glow.",
        "opening_cue": "Blinded by the glare of what we thought was arrival, standing in the middle of the avenue.",
        "peak_cue": "Every red and amber flash across the wet windshield holds the face I was trying not to remember.",
        "closing_cue": "When the sirens pass, the dark returns to the circle — and we are still standing here.",
    },
    {
        "num": 3, "title": "How to break off an engagement",
        "wooden_horse_anchor": "The Warm Bathroom Threshold & Ring on Porcelain (P2/P3)",
        "anchor_detail": "Apartment walls peel into Notan & Layout blueprint lines; only the warm tungsten doorway plane P2/P3 holds full living color.",
        "opening_cue": "There is a choreography to un-promising a life while both people are still in the same room.",
        "peak_cue": "The light under the bathroom door is the only honest line left in the house.",
        "closing_cue": "You open your hands at the lectern, and the ring stays on the counter.",
    },
    {
        "num": 4, "title": "Nevermore",
        "wooden_horse_anchor": "The Single Sodium Streetlamp Over the Viaduct (P2/P3)",
        "anchor_detail": "Concrete viaduct arches step into angular vector planes while the amber sodium pool on the wetstone curb anchors P2.",
        "opening_cue": "Some doors don't slam — they just turn into blueprint lines behind your shoulder.",
        "peak_cue": "Under the viaduct, the amber lamp carves one circle out of the gray night.",
        "closing_cue": "Say the word once into the dark room, and let the listeners keep watch.",
    },
    {
        "num": 5, "title": "Bloodlines",
        "wooden_horse_anchor": "Inherited Hands & Amber Arcade CRT Glow (P2/P3)",
        "anchor_detail": "Generational corridors separate into 7 multiplane sheets while the warm pulse of phosphor light on two hands holds P2.",
        "opening_cue": "We carry rooms we never walked into, voices that started speaking before we were born.",
        "peak_cue": "Look at the knuckles in the light — the same gesture my father made when the words ran out.",
        "closing_cue": "The circle in the studio breathes together; the bloodline crosses from speaker to listener.",
    },
    {
        "num": 6, "title": "Resurrecting Atlantis",
        "wooden_horse_anchor": "Submerged Gold Lantern Beneath the Green Tide (P2/P3)",
        "anchor_detail": "Sunken colonnades and flooded transit halls lock into blue-pencil perspective grid while the submerged lantern glows in P2.",
        "opening_cue": "How do you raise a city that drowned inside your own chest?",
        "peak_cue": "Through the green water, one window is still lit from the inside.",
        "closing_cue": "The water recedes into the dark floor of the studio, leaving the listeners on dry land.",
    },
    {
        "num": 7, "title": "DJ Turn Me Up",
        "wooden_horse_anchor": "Spinning Vinyl Label & VU Meter Needle in Red (P2/P3)",
        "anchor_detail": "The club architecture steps into angular vector facets while the glowing turntable and needle stay locked in P2.",
        "opening_cue": "Turn the booth up until the walls of the room forget our names.",
        "peak_cue": "In the center of the room, the needle holds the only heartbeat that matters.",
        "closing_cue": "When the track cuts out, the quiet of the circle is louder than the speakers.",
    },
    {
        "num": 8, "title": "Newly Single",
        "wooden_horse_anchor": "One Unoccupied Chair & Morning Light Across the Floor (P2/P3)",
        "anchor_detail": "The half-empty room deconstructs into layout lines; the single chair in the sunbeam holds the exact weight of solitude in P2.",
        "opening_cue": "The first morning alone isn't loud — it's just wider than the room used to be.",
        "peak_cue": "Sunlight hits the second cup that nobody reached for.",
        "closing_cue": "Across the dark studio, eight pairs of eyes share the weight of that empty chair.",
    },
    {
        "num": 9, "title": "Yet, Heard",
        "wooden_horse_anchor": "The Open Receiver & Acoustic Ripple in the Dark (P2/P3)",
        "anchor_detail": "Long hallways separate into multiplane sheets while the warm acoustic halo around the speaking mouth crystallizes in P2.",
        "opening_cue": "Even when the line went dead, the voice kept traveling through the wall.",
        "peak_cue": "To be heard after you stopped shouting — that is the whole miracle.",
        "closing_cue": "Here at the acrylic lectern, every syllable lands in the circle across the dark.",
    },
    {
        "num": 10, "title": "Magic Ride",
        "wooden_horse_anchor": "Carousel Gold Horse & Fairground Lights (P2/P3)",
        "anchor_detail": "Direct cousin to K's carved wooden horse: the fairground spins into angular vector planes while the painted horse head stays sharp in P2.",
        "opening_cue": "We bought the ticket knowing the track only ever goes in a circle.",
        "peak_cue": "Hold onto the painted wooden neck while the whole city steps into cel & vector planes.",
        "closing_cue": "The ride slows down into the circle of chairs; the Poet lowers his hands.",
    },
    {
        "num": 11, "title": "New Day",
        "wooden_horse_anchor": "First Amber Horizon Line Over the Rooftop Water Tank (P2/P3)",
        "anchor_detail": "Night-time scaffolding steps into layout blueprint lines as the first gold horizon line cuts cleanly across P2/P3.",
        "opening_cue": "Night doesn't end all at once; it thins out at the edges like breath on glass.",
        "peak_cue": "One strip of gold across the parapet says we survived the dark.",
        "closing_cue": "The lamp beside the lectern warms the faces in the front row.",
    },
    {
        "num": 12, "title": "Reunion",
        "wooden_horse_anchor": "Two Silhouettes Converging Under the Station Clock (P2/P3)",
        "anchor_detail": "The transit concourse separates into blueprint planes P4–P5, leaving only the two figures meeting beneath the warm clock face in P2.",
        "opening_cue": "Years are just distance between two platforms until you see the coat you recognize.",
        "peak_cue": "Everything else in the station disappears the second your hands close.",
        "closing_cue": "In the darkened studio, the circle leans in as the distance closes.",
    },
    {
        "num": 13, "title": "How to Win My Heart",
        "wooden_horse_anchor": "Unfurling Paper Note & Warm Table Candle (P2/P3)",
        "anchor_detail": "Architectural walls soften into painted cel flats around a single small gesture of honesty isolated in P2.",
        "opening_cue": "It was never a fortress — it just needed someone to knock without armor.",
        "peak_cue": "Not grand detail, not spectacle — just one small truth held in the palm.",
        "closing_cue": "The Poet's open hands mirror the offering; the circle holds the silence.",
    },
    {
        "num": 14, "title": "Hot Minute",
        "wooden_horse_anchor": "The Final Match-Flare & Single Gold Ember in the Dark (P2/P3)",
        "anchor_detail": "All 14 poems condense into a sharp angular-vector & cel flare of amber firelight before resolving into the circle of listeners.",
        "opening_cue": "A whole era of our lives lasted sixty seconds in the light of a single match.",
        "peak_cue": "Feel the heat on your fingers before the room returns.",
        "closing_cue": "The ember fades into the clear acrylic lectern — and the circle of listeners remains.",
    },
]


# ==============================================================================
# 2. SEGMENTED SHOT BUNDLE LOADER (LOADS ALL 5 DOPE VERSIONS + PLANES L 0..6)
# ==============================================================================
_SHOT_BUNDLE_CACHE = {}

def load_shot_segmented_bundle(sid, target_size=(960, 540)):
    """
    Loads a shot's complete segmented multiplane & cartoon stack from `shots/out/<sid>/`:
      - `raw`:     photographic RGB
      - `overlay`: Mask2Former + SAM + OwlViT semantic/instance overlay
      - `layout`:  cartoon/layout_sheet.png (blue-pencil perspective grid + P0..P6 colored contours)
      - `cel`:     cartoon/cel.png (flats + variable-width ink + glow)
      - `angular`: program/frame0.png (angular polygon vector scene program)
      - `notan`:   cartoon/notan.png
      - `glow`:    multiplane/glow_pass.png
      - `L`:       plane index map (0..6) at target_size
      - `P2`:      hero boolean mask
      - `P3`:      secondary/FX boolean mask
    """
    key = (sid, target_size)
    if key in _SHOT_BUNDLE_CACHE:
        return _SHOT_BUNDLE_CACHE[key]

    w, h = target_size
    od = os.path.join(OUT_DIR, sid)

    def _read_rgb(rel_p, fallback=None):
        p = os.path.join(od, rel_p)
        if os.path.exists(p):
            return np.asarray(Image.open(p).convert("RGB").resize((w, h), Image.Resampling.LANCZOS), dtype=np.uint8)
        return fallback.copy() if fallback is not None else np.zeros((h, w, 3), dtype=np.uint8)

    raw = _read_rgb("image.jpg")
    overlay = _read_rgb("overlay.jpg", raw)
    layout = _read_rgb("cartoon/layout_sheet.png", raw)
    cel = _read_rgb("cartoon/cel.png", raw)
    angular = _read_rgb("program/frame0.png", cel)
    notan = _read_rgb("cartoon/notan.png", layout)
    glow = _read_rgb("multiplane/glow_pass.png", np.zeros_like(raw))

    pl_path = os.path.join(od, "multiplane/planes.npz")
    if os.path.exists(pl_path):
        PL = np.load(pl_path)
        L_full = PL["L"].astype(np.uint8)
        P2_full = PL["P2"].astype(np.uint8)
        P3_full = PL["P3"].astype(np.uint8) if "P3" in PL else (L_full == 3).astype(np.uint8)
        L = cv2.resize(L_full, (w, h), interpolation=cv2.INTER_NEAREST)
        P2 = cv2.resize(P2_full, (w, h), interpolation=cv2.INTER_NEAREST) > 0
        P3 = cv2.resize(P3_full, (w, h), interpolation=cv2.INTER_NEAREST) > 0
    else:
        L = np.full((h, w), 4, dtype=np.uint8)
        P2 = np.zeros((h, w), dtype=bool)
        P3 = np.zeros((h, w), dtype=bool)

    # Precompute anti-aliased plane masks and colored contour lines for P0..P6
    p_cols = {
        0: (70, 75, 90),     # P0 camera mask
        1: (185, 130, 80),   # P1 foreground (lectern / floor)
        2: (235, 55, 60),    # P2 HERO (Poet / Wooden Horse / Poem Hero)
        3: (255, 175, 55),   # P3 Secondary / FX (Listeners / Lamps / Fire)
        4: (65, 145, 245),   # P4 Midground
        5: (125, 185, 245),  # P5 Distant background
        6: (155, 220, 245),  # P6 Sky
    }
    plane_masks = {}
    plane_edges = np.zeros((h, w, 3), dtype=np.float32)
    for p in range(7):
        m = (L == p).astype(np.uint8)
        plane_masks[p] = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2)[..., None]
        edge = cv2.dilate(m, np.ones((3, 3), np.uint8)) - cv2.erode(m, np.ones((3, 3), np.uint8))
        if edge.any():
            col = np.array(p_cols[p], dtype=np.float32)
            plane_edges[edge > 0] = col

    bundle = dict(
        sid=sid,
        raw=raw,
        overlay=overlay,
        layout=layout,
        cel=cel,
        angular=angular,
        notan=notan,
        glow=glow,
        L=L,
        P2=P2,
        P3=P3,
        plane_masks=plane_masks,
        plane_edges=plane_edges,
    )
    _SHOT_BUNDLE_CACHE[key] = bundle
    return bundle


# ==============================================================================
# 3. PLANE-SYNCHRONIZED COMPOSITING & CROSS-WORLD MORPH OPERATORS
# ==============================================================================
def render_multiplane_style_peel(bundle, u_peel, mode="raw_to_angular", parallax_shift=0.0):
    """
    Peels a single shot across its 7 segmented planes (P6/P5 background first ->
    P4 midground -> P3 listeners/FX -> P1 foreground lectern -> P2 Hero last),
    while applying real multiplane depth parallax (`1/Z` shift per plane)!
    """
    h, w = bundle["raw"].shape[:2]
    # Order of plane conversion: background planes convert first, hero P2 stays anchor longest
    plane_order = [6, 5, 4, 0, 1, 3, 2]
    parallax_factors = {6: 0.05, 5: 0.18, 4: 0.42, 3: 0.78, 2: 1.00, 1: 1.32, 0: 1.65}

    if mode == "raw_to_angular":
        src_A, src_B, src_mid = bundle["raw"], bundle["angular"], bundle["cel"]
    elif mode == "angular_to_raw":
        src_A, src_B, src_mid = bundle["angular"], bundle["raw"], bundle["cel"]
    elif mode == "layout_to_cel":
        src_A, src_B, src_mid = bundle["layout"], bundle["cel"], bundle["angular"]
    elif mode == "cel_to_angular":
        src_A, src_B, src_mid = bundle["cel"], bundle["angular"], bundle["layout"]
    else:
        src_A, src_B, src_mid = bundle["raw"], bundle["cel"], bundle["layout"]

    canvas = np.zeros((h, w, 3), dtype=np.float32)
    weight_sum = np.zeros((h, w, 1), dtype=np.float32)

    for rank_idx, p in enumerate(plane_order):
        # Local progress for plane `p`
        t_start = rank_idx * 0.09
        t_span = 0.46
        lu = float(np.clip((u_peel - t_start) / t_span, 0.0, 1.0))
        lu_e = ease(lu)

        # Blend A -> mid -> B with crisp contour flash right at the transition wavefront (0.2 < lu < 0.8)
        if lu_e < 0.5:
            k = lu_e * 2.0
            plane_img = src_A.astype(np.float32) * (1.0 - k) + src_mid.astype(np.float32) * k
        else:
            k = (lu_e - 0.5) * 2.0
            plane_img = src_mid.astype(np.float32) * (1.0 - k) + src_B.astype(np.float32) * k

        # Highlight plane boundary contour at the active peeling wavefront
        wave_flash = math.sin(lu * math.pi) ** 1.6
        if wave_flash > 0.05:
            plane_img = np.clip(plane_img + bundle["plane_edges"] * (0.65 * wave_flash), 0, 255)

        # Apply multiplane parallax shift/zoom for plane `p`
        pf = parallax_factors[p]
        scale = 1.0 + 0.045 * parallax_shift * pf
        dx = -10.0 * parallax_shift * pf
        M = np.float32([[scale, 0, (w * 0.5) * (1 - scale) + dx], [0, scale, (h * 0.5) * (1 - scale)]])
        warped_img = cv2.warpAffine(plane_img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        warped_m = cv2.warpAffine(bundle["plane_masks"][p], M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[..., None]

        canvas = canvas * (1.0 - warped_m) + warped_img * warped_m
        weight_sum = np.maximum(weight_sum, warped_m)

    # Add subtle glow pass
    canvas = np.clip(canvas + bundle["glow"].astype(np.float32) * 0.22, 0, 255)
    return canvas.astype(np.uint8)


def render_cross_world_plane_transition(poet_bundle, poem_bundle, poem_motion_frame, u_trans, reverse=False):
    """
    Plane-by-Plane Cross-World Transition between the Poet at the Lectern (`poet_bundle`)
    and the Poem's Segmented World (`poem_bundle` + `poem_motion_frame`):
      - Stage 1 (u in 0.0..0.40): Behind the Poet's segmented figure (P2) and foreground
        listeners (P0), the studio wall (P4/P5/P6) peels away into the Poem's `layout_sheet`
        and `angular` background planes! Meanwhile, inside the Clear Acrylic Lectern (P1),
        the Poem's `angular` & `cel` world refracts like an optical prism!
      - Stage 2 (u in 0.40..0.75): Midground & secondary planes (P3/P4) lock into the Poem's
        `cel.png` and `angular` polygons while the Poet's P2 Hero (open hands / lectern)
        hands off with inked contour flashes to the Poem's P2/P3 Hero!
      - Stage 3 (u in 0.75..1.00): Full arrival inside the Poem's segmented multiplane world.
    If `reverse=True`, runs the exact plane-by-plane reassembly from the Poem back into
    the Poet's silhouette (P2) and the Circle of Listeners (P3)!
    """
    u = 1.0 - float(np.clip(u_trans, 0.0, 1.0)) if reverse else float(np.clip(u_trans, 0.0, 1.0))
    h, w = poet_bundle["raw"].shape[:2]

    # Poet representation shifts from live-action -> cel -> angular vector as u increases
    u_poet_style = ease(min(1.0, u * 1.4))
    poet_img = (
        poet_bundle["raw"].astype(np.float32) * (1.0 - u_poet_style)
        + (0.45 * poet_bundle["cel"].astype(np.float32) + 0.55 * poet_bundle["angular"].astype(np.float32)) * u_poet_style
    )

    # Poem representation shifts from layout blueprint -> angular vector -> painted cel / live motion
    if u < 0.45:
        k = ease(u / 0.45)
        poem_img = poem_bundle["layout"].astype(np.float32) * (1.0 - k) + poem_bundle["angular"].astype(np.float32) * k
    else:
        k = ease((u - 0.45) / 0.55)
        poem_target = 0.55 * poem_bundle["cel"].astype(np.float32) + 0.45 * poem_motion_frame.astype(np.float32)
        poem_img = poem_bundle["angular"].astype(np.float32) * (1.0 - k) + poem_target * k

    # Plane-by-plane takeover weights based on Poet's planes `L`
    L_poet = poet_bundle["L"]
    # Background mural (P4, P5, P6) swaps to Poem FIRST (u: 0.05 -> 0.48)
    w_bg = ease((u - 0.05) / 0.43)
    # Acrylic lectern / foreground floor (P1) acts as an optical prism early (u: 0.12 -> 0.55)
    w_p1 = ease((u - 0.12) / 0.43)
    # Secondary listeners / lamps (P3) & framing (P0) swap mid-transition (u: 0.32 -> 0.78)
    w_p3 = ease((u - 0.32) / 0.46)
    # The Poet himself (P2 Hero: face & open hands) holds the frame longest and hands off last (u: 0.48 -> 0.92)
    w_p2 = ease((u - 0.48) / 0.44)

    takeover = np.zeros((h, w), dtype=np.float32)
    takeover[np.isin(L_poet, [4, 5, 6])] = w_bg
    takeover[L_poet == 1] = w_p1
    takeover[np.isin(L_poet, [0, 3])] = w_p3
    takeover[L_poet == 2] = w_p2
    takeover = cv2.GaussianBlur(takeover, (0, 0), 2.2)[..., None]

    comp = poet_img * (1.0 - takeover) + poem_img * takeover

    # Draw crisp segmented plane contours along the active hand-off boundary (zero muddy blur!)
    active_seam = 4.0 * takeover[..., 0] * (1.0 - takeover[..., 0])
    seam_contours = (
        poet_bundle["plane_edges"] * (1.0 - u) + poem_bundle["plane_edges"] * u
    ) * active_seam[..., None]
    comp = np.clip(comp + seam_contours * 0.95 + poem_bundle["glow"].astype(np.float32) * (0.25 * u), 0, 255)
    return comp.astype(np.uint8)


def render_wooden_horse_anchor_isolation(poem_bundle, live_frame, patch_frame, u_act4):
    """
    ACT IV: The Poem's "Wooden Horse" Emotional Anchor (`P2 / P3` Isolation).
    Just as K's memory isolates the carved wooden horse (`6·10·21`) and furnace flame in `P2/P3`
    while the industrial orphanage recedes, here:
      - The surrounding environment planes (`P4, P5, P6`) step into the quiet
        Classical Layout Blueprint (`layout_sheet.png`) & Angular Vector (`program/frame0.png`),
      - While the Hero & Emotional Anchor planes (`P2 | P3`) blaze in full living color
        (`live_frame` + painted cel `patch_frame` + `glow_pass.png`) framed by heavy `P2` red/amber ink contours!
    """
    h, w = poem_bundle["raw"].shape[:2]
    # Surround (P4, P5, P6): blend of layout blueprint + angular vector program
    u_e = ease(math.sin(u_act4 * math.pi))
    surround = (
        0.55 * poem_bundle["layout"].astype(np.float32)
        + 0.45 * poem_bundle["angular"].astype(np.float32)
    ) * 0.78

    # Hero / Emotional Anchor (P2 | P3): vibrant living motion + painted cel patch + glow
    hero_live = (
        0.50 * live_frame.astype(np.float32)
        + 0.30 * patch_frame.astype(np.float32)
        + 0.20 * poem_bundle["cel"].astype(np.float32)
        + poem_bundle["glow"].astype(np.float32) * 0.45
    )
    hero_live = np.clip(hero_live * 1.12, 0, 255)

    hero_mask = (poem_bundle["P2"] | poem_bundle["P3"]).astype(np.float32)
    if hero_mask.mean() < 0.03:
        # Fallback central focal mask if P2/P3 is tiny
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        hero_mask = np.clip(1.0 - np.sqrt(((xx - w * 0.5) / (w * 0.30)) ** 2 + ((yy - h * 0.48) / (h * 0.30)) ** 2), 0.0, 1.0)
    else:
        hero_mask = cv2.GaussianBlur(hero_mask, (0, 0), 2.5)

    blend_m = np.clip(hero_mask * (0.35 + 0.65 * u_e), 0.0, 1.0)[..., None]
    base = live_frame.astype(np.float32) * (1.0 - 0.75 * u_e) + surround * (0.75 * u_e)
    out = base * (1.0 - blend_m) + hero_live * blend_m

    # Add crisp P2/P3 ink contour around the isolated emotional anchor
    out = np.clip(out + poem_bundle["plane_edges"] * (0.55 * u_e), 0, 255)
    return out.astype(np.uint8)


def load_video_frames(video_path, num_frames, target_size=(960, 540)):
    w, h = target_size
    if not os.path.exists(video_path):
        return [np.zeros((h, w, 3), dtype=np.uint8) for _ in range(num_frames)]
    cmd = [
        "ffmpeg", "-v", "error",
        "-i", video_path,
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps=12",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"
    ]
    raw = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    frame_bytes = w * h * 3
    total = len(raw) // frame_bytes
    if total == 0:
        return [np.zeros((h, w, 3), dtype=np.uint8) for _ in range(num_frames)]
    arr = np.frombuffer(raw[:total * frame_bytes], dtype=np.uint8).reshape((total, h, w, 3))
    idxs = np.linspace(0, total - 1, num_frames).astype(int)
    return [arr[i].copy() for i in idxs]


def stamp_bookend_hud(frame_rgb, act_label, title_text, quote_text, k_parallel_text, pip_rgb=None, pip_label=None):
    im = Image.fromarray(frame_rgb)
    draw = ImageDraw.Draw(im, "RGBA")
    h, w = frame_rgb.shape[:2]
    f_hud = load_font(12, mono=True)
    f_sub = load_font(16, serif=True)
    f_k = load_font(11, mono=True)

    draw.rectangle((0, 0, w, 34), fill=(5, 7, 10, 175))
    draw.text((18, 9), act_label, font=f_hud, fill=(255, 198, 105, 245))
    draw.text((w - 430, 10), k_parallel_text[:62], font=f_k, fill=(115, 215, 255, 230))

    if pip_rgb is not None:
        pw, ph = 184, 104
        px, py = w - pw - 16, 44
        pip_im = Image.fromarray(pip_rgb).resize((pw, ph), Image.Resampling.LANCZOS)
        draw.rectangle((px - 2, py - 2, px + pw + 2, py + ph + 2), fill=(8, 10, 14, 225), outline=(255, 195, 95, 210), width=2)
        im.paste(pip_im, (px, py))
        if pip_label:
            draw.rectangle((px, py + ph - 18, px + pw, py + ph), fill=(5, 7, 10, 195))
            draw.text((px + 6, py + ph - 16), pip_label[:26], font=load_font(10, mono=True), fill=(255, 205, 115, 240))

    draw.rectangle((0, h - 64, w, h), fill=(5, 7, 10, 190))
    draw.text((22, h - 54), title_text, font=f_hud, fill=(255, 198, 105, 240))
    q_trim = quote_text if len(quote_text) <= 108 else quote_text[:105] + "..."
    draw.text((22, h - 34), f"“{q_trim}”", font=f_sub, fill=(244, 238, 226, 252))
    return np.asarray(im, dtype=np.uint8)


# ==============================================================================
# STEP 1: BUILD THE "DOPE SEGMENTED COMPOSITES" FOR ALL 8 POET & 8 K STAGES
# ==============================================================================
def build_poet_and_k_dope_composites():
    print("Step 1: Building Segmented Multiplane + Angular Vector + Painted Cel Composites for all 8 Poet & 8 K shots...")
    W, H = 1280, 720
    for idx, st in enumerate(POET_LECTERN_STAGES):
        b = load_shot_segmented_bundle(st["sid"], (W, H))
        k_b = load_shot_segmented_bundle(st["k_sid"], (W, H))
        # Create a razor-sharp Plane-Split Composite (no muddy stain!):
        # Background (P4, P5, P6) in Angular Vector + Layout Blueprint contours;
        # Secondary Listeners & Lamps (P3) in Painted Cel;
        # Poet (P2) & Acrylic Lectern (P1) in high-contrast Angular Vector + Cel Ink + Live-Action detail!
        comp = np.zeros((H, W, 3), dtype=np.float32)
        L = b["L"]
        bg_m = np.isin(L, [4, 5, 6])[..., None]
        p3_m = np.isin(L, [0, 3])[..., None]
        hero_m = np.isin(L, [1, 2])[..., None]

        bg_layer = 0.62 * b["angular"].astype(np.float32) + 0.38 * b["layout"].astype(np.float32)
        p3_layer = 0.55 * b["cel"].astype(np.float32) + 0.45 * b["angular"].astype(np.float32)
        hero_layer = 0.52 * b["angular"].astype(np.float32) + 0.28 * b["cel"].astype(np.float32) + 0.20 * b["raw"].astype(np.float32)

        comp = bg_layer * bg_m + p3_layer * p3_m + hero_layer * hero_m
        comp = np.clip(comp + b["plane_edges"] * 0.75 + b["glow"].astype(np.float32) * 0.30, 0, 255).astype(np.uint8)

        stamped = stamp_bookend_hud(
            comp,
            act_label=f"{st['act']} · 7-PLANE SEGMENTED (ANGULAR + CEL + LAYOUT)",
            title_text=st["title"],
            quote_text=st["claim"],
            k_parallel_text=st["k_parallel"],
            pip_rgb=k_b["angular"],
            pip_label=f"K PARALLEL: {st['k_sid'][:14]}",
        )
        out_p = os.path.join(ROOT, st["mist_file"])
        Image.fromarray(stamped).save(out_p, quality=94)
        # Also overwrite poet_0X_mist.jpg so any legacy link shows the new crisp segmented version!
        legacy_p = os.path.join(POET_DIR, f"{st['id']}_mist.jpg")
        Image.fromarray(stamped).save(legacy_p, quality=94)
    print("  -> Saved 8 crisp Segmented Poet Composites in", POET_DIR)


# ==============================================================================
# STEP 2: RENDER 14 BOOKENDED POEM FILMS WITH PLANE-BY-PLANE TRANSITIONS
# ==============================================================================
def build_single_poem_bookend_film(poem_dict, spec):
    n = spec["num"]
    ns = f"{n:02d}"
    out_mp4 = os.path.join(BOOKEND_VID_DIR, f"poem_{ns}_bookend_spacetime.mp4")

    W, H = 960, 540
    # Load the 8 Poet segmented bundles
    poet_bundles = [load_shot_segmented_bundle(st["sid"], (W, H)) for st in POET_LECTERN_STAGES]

    # Load the Poem's Hero & Echo segmented bundles from `shots/out/<uuid>/`
    views = poem_dict.get("views", [])
    v_hero_dir = (views[0].get("dir") or views[0].get("shot_dir")) if views else "62b9740c-d0be-4b4a-a311-d653a2580907_1"
    v_echo_dir = (views[1].get("dir") or views[1].get("shot_dir")) if len(views) > 1 else v_hero_dir
    poem_hero_b = load_shot_segmented_bundle(v_hero_dir, (W, H))
    poem_echo_b = load_shot_segmented_bundle(v_echo_dir, (W, H))

    # Load real motion clips for the poem
    v0_shot = os.path.join(ROOT, views[0]["live_shot_video"]) if views and views[0].get("live_shot_video") else ""
    worm_vid = os.path.join(ROOT, f"videos/poems/poem_{ns}_spacetime_worm.mp4")
    patches = sorted(glob.glob(os.path.join(ROOT, f"cel_assets/patches/P{ns}-*.mp4")))
    patch_vid = patches[0] if patches else worm_vid

    shot_frames = load_video_frames(v0_shot, 60, (W, H))
    worm_frames = load_video_frames(worm_vid, 60, (W, H))
    patch_frames = load_video_frames(patch_vid, 60, (W, H))

    frames_out = []
    strip_keyframes = []

    # --- ACT I (0.0s – 3.8s, 45 frames): OPENING BOOKEND — LIVE-ACTION -> 7-PLANE SEGMENTED SALON ---
    for f in range(45):
        if f < 15:
            st_idx, lu = 0, f / 14.0
        elif f < 30:
            st_idx, lu = 1, (f - 15) / 14.0
        else:
            st_idx, lu = 2, (f - 30) / 14.0
        pb = poet_bundles[st_idx]
        # Peel plane-by-plane from Live-Action into Cel & Angular Vector Scene Program
        frame = render_multiplane_style_peel(pb, u_peel=lu * 0.92, mode="raw_to_angular", parallax_shift=(lu - 0.5))
        stamped = stamp_bookend_hud(
            frame,
            act_label=f"P{ns} · {spec['title'].upper()} · ACT I: OPENING LECTERN BOOKEND (P0–P6 PEEL)",
            title_text=POET_LECTERN_STAGES[st_idx]["title"],
            quote_text=spec["opening_cue"],
            k_parallel_text="K PARALLEL (1:49–2:00): Officer K & Joshi in the interview room",
            pip_rgb=pb["layout"],
            pip_label=f"P0–P6 LAYOUT: {POET_LECTERN_STAGES[st_idx]['id'].upper()}",
        )
        frames_out.append(stamped)
        if f == 22:
            strip_keyframes.append(stamped.copy())

    # --- ACT II (3.8s – 7.0s, 39 frames): THE THRESHOLD — CROSS-WORLD PLANE SWAP (POET <-> POEM) ---
    for f in range(39):
        u = f / 38.0
        st_idx = 3 if f < 13 else (4 if f < 26 else 5)
        pb = poet_bundles[st_idx]
        frame = render_cross_world_plane_transition(
            poet_bundle=pb,
            poem_bundle=poem_hero_b,
            poem_motion_frame=shot_frames[min(len(shot_frames) - 1, f)],
            u_trans=u,
            reverse=False,
        )
        stamped = stamp_bookend_hud(
            frame,
            act_label=f"P{ns} · ACT II: CROSS-WORLD PLANE HAND-OFF (POET P0–P6 → POEM P0–P6)",
            title_text="P4/P5 Mural Peels Into Poem Blueprint · P1 Acrylic Stand Ignites · P2 Hands Release",
            quote_text=spec["opening_cue"],
            k_parallel_text="K PARALLEL (2:00–2:06): 'I had a little toy horse... Everything's grey'",
            pip_rgb=pb["angular"],
            pip_label=f"POET ANGULAR: {POET_LECTERN_STAGES[st_idx]['id'].upper()}",
        )
        frames_out.append(stamped)
        if f == 24:
            strip_keyframes.append(stamped.copy())

    # --- ACT III (7.0s – 11.2s, 50 frames): RECALLED MEMORY — MULTIPLANE PARALLAX & SEGMENTED STACK ---
    for f in range(50):
        u = f / 49.0
        if f < 18:
            # Layout Blueprint -> Painted Cel with multiplane parallax
            lu = f / 17.0
            frame = render_multiplane_style_peel(poem_hero_b, u_peel=lu, mode="layout_to_cel", parallax_shift=(lu - 0.5) * 1.4)
            pip_im, pip_lbl = poem_hero_b["overlay"], "SAM + ADE SEGMENTATION"
        elif f < 35:
            # Painted Cel -> Angular Vector Scene Program
            lu = (f - 18) / 16.0
            frame = render_multiplane_style_peel(poem_hero_b, u_peel=lu, mode="cel_to_angular", parallax_shift=(lu - 0.5) * 1.4)
            pip_im, pip_lbl = poem_hero_b["layout"], "3D PERSPECTIVE LAYOUT"
        else:
            # Angular Vector Program blended with live multiplane motion + spacetime worm
            lu = ease((f - 35) / 14.0)
            live_mix = 0.65 * shot_frames[f].astype(np.float32) + 0.35 * worm_frames[f].astype(np.float32)
            frame = np.clip(
                poem_hero_b["angular"].astype(np.float32) * (1.0 - lu)
                + live_mix * lu
                + poem_hero_b["plane_edges"] * (0.45 * (1.0 - lu)),
                0, 255
            ).astype(np.uint8)
            pip_im, pip_lbl = poem_hero_b["cel"], "PAINTED CEL (FLATS+INK)"

        stamped = stamp_bookend_hud(
            frame,
            act_label=f"P{ns} · ACT III: SEGMENTED MEMORY WORLD (LAYOUT → CEL → ANGULAR → MOTION)",
            title_text=f"Multiplane Memory Architecture · {spec['title']}",
            quote_text=spec["peak_cue"],
            k_parallel_text="K PARALLEL (2:06–2:24): Orphanage catwalks & turning clockwork gears",
            pip_rgb=pip_im,
            pip_label=pip_lbl,
        )
        frames_out.append(stamped)
        if f == 24:
            strip_keyframes.append(stamped.copy())

    # --- ACT IV (11.2s – 14.6s, 41 frames): THE "WOODEN HORSE" EMOTIONAL ANCHOR (P2/P3 ISOLATION) ---
    k06_b = load_shot_segmented_bundle("k_06_wooden_horse_palm", (W, H))
    for f in range(41):
        u = f / 40.0
        active_b = poem_hero_b if f < 22 else poem_echo_b
        frame = render_wooden_horse_anchor_isolation(
            poem_bundle=active_b,
            live_frame=shot_frames[min(len(shot_frames) - 1, f + 10)],
            patch_frame=patch_frames[min(len(patch_frames) - 1, f)],
            u_act4=u,
        )
        stamped = stamp_bookend_hud(
            frame,
            act_label=f"P{ns} · ACT IV: ISOLATED HERO ANCHOR (P2/P3) — {spec['wooden_horse_anchor'][:38].upper()}",
            title_text=f"Wooden Horse Equivalent: {spec['wooden_horse_anchor']}",
            quote_text=spec["anchor_detail"],
            k_parallel_text="K PARALLEL (2:27): Carved Wooden Horse (6·10·21) isolated in P2",
            pip_rgb=k06_b["angular"] if f % 2 == 0 else patch_frames[min(len(patch_frames) - 1, f)],
            pip_label="K WOODEN HORSE (P2) ↔ CEL PATCH",
        )
        frames_out.append(stamped)
        if f == 20:
            strip_keyframes.append(stamped.copy())

    # --- ACT V (14.6s – 18.0s, 41 frames): CLOSING BOOKEND — PLANE REASSEMBLY INTO CIRCLE OF LISTENERS ---
    for f in range(41):
        u = f / 40.0
        if f < 22:
            # Reverse Cross-World Plane Swap: Poem P0–P6 reassembles into Poet P07/P08
            lu = f / 21.0
            pb = poet_bundles[6] if f < 11 else poet_bundles[7]
            frame = render_cross_world_plane_transition(
                poet_bundle=pb,
                poem_bundle=poem_echo_b,
                poem_motion_frame=shot_frames[-1],
                u_trans=lu,
                reverse=True,
            )
            pip_im, pip_lbl = pb["layout"], "P08 CIRCLE LAYOUT SHEET"
            st_title = POET_LECTERN_STAGES[6 if f < 11 else 7]["title"]
        else:
            # Final peel from Angular Vector (`poet_08/program/frame0.png`) back to warm live-action circle of listeners
            lu = (f - 22) / 18.0
            pb = poet_bundles[7]
            frame = render_multiplane_style_peel(pb, u_peel=lu, mode="angular_to_raw", parallax_shift=(1.0 - lu) * 0.5)
            pip_im, pip_lbl = pb["angular"], "P08 ANGULAR VECTOR"
            st_title = POET_LECTERN_STAGES[7]["title"]

        stamped = stamp_bookend_hud(
            frame,
            act_label=f"P{ns} · ACT V: CLOSING BOOKEND — PLANE REASSEMBLY INTO CIRCLE OF LISTENERS",
            title_text=st_title,
            quote_text=spec["closing_cue"],
            k_parallel_text="K PARALLEL (3:06–3:25): Return to office & listener ('Someone lived this')",
            pip_rgb=pip_im,
            pip_label=pip_lbl,
        )
        frames_out.append(stamped)
        if f == 28:
            strip_keyframes.append(stamped.copy())

    # Encode 18.0s H.264 + AAC film with the Poet's real spoken reading (`play/levels/NN/reading.mp3`)
    reading_mp3 = os.path.join(ROOT, f"play/levels/{ns}/reading.mp3")
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", "24",
        "-i", "pipe:0",
    ]
    if os.path.exists(reading_mp3):
        cmd += [
            "-i", reading_mp3,
            "-filter_complex", "[1:a]atrim=0:18.0,afade=t=in:st=0:d=0.5,afade=t=out:st=16.5:d=1.5[a]",
            "-map", "0:v:0", "-map", "[a]",
            "-c:a", "aac", "-b:a", "160k",
        ]
    cmd += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "19",
        "-movflags", "+faststart", "-t", "18.0",
        out_mp4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in frames_out:
        proc.stdin.write(fr.tobytes())
        proc.stdin.write(fr.tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"  -> Rendered P{ns} Plane-Synchronized Bookend Film: {out_mp4}")
    return out_mp4, strip_keyframes


def _render_poem_worker(args):
    p, spec = args
    return build_single_poem_bookend_film(p, spec)


# ==============================================================================
# STEP 3: BUILD THE 2 4K ARCHITECTURAL CONTACT SHEETS & MASTER ANTHOLOGY FILM
# ==============================================================================
def build_bookend_contact_sheets_and_master_film(all_poem_strips, poem_mp4s):
    print("Step 3: Building 4K Segmented Architecture Sheet (Agent K 1:49 vs The Poet's Lectern Bookend)...")
    SW, SH = 3840, 2160
    sheet1 = Image.new("RGB", (SW, SH), (7, 9, 13))
    draw1 = ImageDraw.Draw(sheet1)
    f_h1 = load_font(34, serif=True)
    f_h2 = load_font(20, mono=True)
    f_lbl = load_font(15, mono=True)
    f_body = load_font(16, serif=True)

    draw1.text((48, 24), "PLANE-SYNCHRONIZED BOOKEND ARCHITECTURE · AGENT K (1:49 – 3:25) ↔ THE POET AT THE LECTERN (POEMS 01–14)", font=f_h1, fill=(246, 238, 222))
    draw1.text((48, 68), "Every shot decomposed into 7 Multiplane Sheets (P0..P6), SAM/Mask2Former Semantic Masks, Classical Layout Blueprints (HORIZON+VP), Painted Cels, and Angular Vector Scene Programs.", font=f_body, fill=(255, 198, 102))

    # Row 1: All 8 Agent K / Toy Wooden Horse Segmented Shots (Raw vs Angular Vector + Layout Blueprint)
    draw1.text((48, 108), "ROW I · BLADE RUNNER 2049 PROTOTYPE: AGENT K & THE TOY WOODEN HORSE (1:49 – 3:25) — 8 SEGMENTED STAGES (ANGULAR VECTOR + CEL + LAYOUT)", font=f_h2, fill=(120, 210, 250))
    kw = (SW - 96 - 7 * 16) // 8
    kh = 360
    for i, kspec in enumerate(K_SHOT_SPECS):
        x0 = 48 + i * (kw + 16)
        y0 = 142
        kb = load_shot_segmented_bundle(kspec["sid"], (kw, kh - 84))
        # Top half of card: Angular Vector Program; Bottom strip: Layout Sheet + Raw PIP
        card_im = Image.fromarray(kb["angular"])
        lay_strip = Image.fromarray(kb["layout"]).resize((kw // 2, 76), Image.Resampling.LANCZOS)
        raw_strip = Image.fromarray(kb["raw"]).resize((kw // 2, 76), Image.Resampling.LANCZOS)
        sheet1.paste(card_im, (x0, y0))
        sheet1.paste(raw_strip, (x0, y0 + kh - 160))
        sheet1.paste(lay_strip, (x0 + kw // 2, y0 + kh - 160))
        draw1.rectangle((x0, y0, x0 + kw, y0 + kh - 84), outline=(120, 210, 250), width=2)
        draw1.text((x0 + 4, y0 + kh - 78), kspec["sid"].upper()[:26], font=f_lbl, fill=(120, 210, 250))
        draw1.text((x0 + 4, y0 + kh - 56), kspec["act"][:32], font=load_font(12, mono=True), fill=(255, 198, 102))
        draw1.text((x0 + 4, y0 + kh - 36), kspec["title"][:38], font=f_body, fill=(230, 224, 210))

    # Rows 2 & 3: All 8 Poet Lectern Shots showing 4 Dope Segmented Versions per Shot (2x2 quad inside each card: Raw | SAM Overlay | Layout Blueprint | Angular Vector Program)
    draw1.text((48, 522), "ROWS II–III · THE POET'S LIVE RETELLING AT THE ACRYLIC LECTERN — ALL 8 STAGES × 4 DOPE SEGMENTED VERSIONS (RAW · SAM OVERLAY · LAYOUT BLUEPRINT · ANGULAR VECTOR)", font=f_h2, fill=(255, 198, 102))
    pw = (SW - 96 - 3 * 24) // 4
    ph = 760
    for idx, st in enumerate(POET_LECTERN_STAGES):
        col = idx % 4
        row = idx // 4
        x0 = 48 + col * (pw + 24)
        y0 = 560 + row * (ph + 24)
        qw = (pw - 6) // 2
        qh = (ph - 104 - 6) // 2
        pb = load_shot_segmented_bundle(st["sid"], (qw, qh))

        # 2x2 Quad: TL=Raw, TR=SAM Overlay, BL=Layout Sheet (P0..P6 + Grid), BR=Angular Vector Scene Program
        quads = [
            (pb["raw"], "1·RAW LIVE-ACTION", (255, 198, 102), x0, y0),
            (pb["overlay"], "2·SAM/MASK2FORMER", (120, 210, 250), x0 + qw + 6, y0),
            (pb["layout"], "3·P0–P6 LAYOUT GRID", (130, 240, 175), x0, y0 + qh + 6),
            (pb["angular"], "4·ANGULAR VECTOR", (255, 140, 195), x0 + qw + 6, y0 + qh + 6),
        ]
        for q_arr, q_tag, q_col, qx, qy in quads:
            sheet1.paste(Image.fromarray(q_arr), (qx, qy))
            draw1.rectangle((qx, qy, qx + qw, qy + qh), outline=q_col, width=2)
            draw1.rectangle((qx + 4, qy + 4, qx + 178, qy + 24), fill=(5, 7, 10))
            draw1.text((qx + 8, qy + 6), q_tag, font=load_font(11, mono=True), fill=q_col)

        ty = y0 + 2 * qh + 14
        draw1.text((x0 + 4, ty), f"{st['id'].upper()} · {st['act']}", font=f_lbl, fill=(255, 198, 102))
        draw1.text((x0 + 4, ty + 24), f"{st['title']}  |  {st['k_parallel']}", font=load_font(13, mono=True), fill=(120, 210, 250))
        draw1.text((x0 + 4, ty + 46), st["claim"][:96], font=f_body, fill=(230, 224, 210))

    sheet1_path = os.path.join(FILM_OUT_DIR, "poet_bookend_vs_k_interview_sheet.png")
    sheet1.save(sheet1_path)
    shutil.copy2(sheet1_path, os.path.join(ARTIFACT_DIR, "poet_bookend_vs_k_interview_sheet.png"))
    print("  -> Saved 4K Segmented Architecture Comparison Sheet:", sheet1_path)

    # 2. 4K 14-Poem Bookended Retelling Matrix Sheet (All 14 Poems × 5 Plane-Synchronized Acts)
    print("Step 4: Building 4K 14-Poem Plane-Synchronized Bookend Matrix Sheet...")
    MW, MH = 3840, 2660
    sheet2 = Image.new("RGB", (MW, MH), (7, 9, 13))
    draw2 = ImageDraw.Draw(sheet2)
    draw2.text((40, 24), "WHERE YOU GO WHEN YOU LEAVE — ALL 14 POEMS BOOKENDED BY PLANE-SYNCHRONIZED POET RETELLING (P0–P6)", font=f_h1, fill=(246, 238, 222))
    draw2.text((40, 70), "5-Act Segmented Transition Grammar: [ACT I] P0–P6 Salon Peel → [ACT II] Cross-World Plane Swap (Mural/Lectern/Hands) → [ACT III] Segmented Memory (Layout/Cel/Angular) → [ACT IV] Isolated P2/P3 Anchor → [ACT V] Circle Reassembly", font=f_body, fill=(255, 198, 102))

    col_w = (MW - 80 - 32) // 2
    row_h = (MH - 120 - 6 * 14) // 7
    thumb_w = (col_w - 20 - 4 * 8) // 5
    thumb_h = row_h - 62

    for idx, (spec, strip) in enumerate(zip(POEM_BOOKEND_SPECS, all_poem_strips)):
        col = idx // 7
        row = idx % 7
        x0 = 40 + col * (col_w + 32)
        y0 = 112 + row * (row_h + 14)
        draw2.rectangle((x0, y0, x0 + col_w, y0 + row_h), fill=(12, 15, 22), outline=(48, 58, 74), width=1)
        ns = f"{spec['num']:02d}"
        draw2.text(
            (x0 + 10, y0 + 6),
            f"POEM {ns} · {spec['title'].upper()}   |   ISOLATED P2/P3 ANCHOR: {spec['wooden_horse_anchor']}",
            font=f_lbl,
            fill=(255, 198, 102),
        )
        act_short = ["I·P0-P6 SALON PEEL", "II·PLANE HAND-OFF", "III·LAYOUT/CEL/VEC", "IV·P2/P3 ANCHOR", "V·LISTENERS"]
        for k in range(min(5, len(strip))):
            tx = x0 + 10 + k * (thumb_w + 8)
            ty = y0 + 30
            im_t = Image.fromarray(strip[k]).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet2.paste(im_t, (tx, ty))
            draw2.rectangle((tx, ty, tx + thumb_w, ty + thumb_h), outline=(120, 210, 250) if k in (1, 2, 3) else (255, 198, 102), width=1)
            draw2.text((tx + 4, ty + thumb_h + 4), act_short[k], font=load_font(12, mono=True), fill=(210, 218, 228))

    sheet2_path = os.path.join(FILM_OUT_DIR, "poet_retelling_bookend_14poems_sheet.png")
    sheet2.save(sheet2_path)
    shutil.copy2(sheet2_path, os.path.join(ARTIFACT_DIR, "poet_retelling_bookend_14poems_sheet.png"))
    print("  -> Saved 4K 14-Poem Plane-Synchronized Bookend Matrix Sheet:", sheet2_path)

    # 3. Master Anthology Film
    master_out = os.path.join(ROOT, "videos/wygwyl_poet_retelling_bookend_spacetime.mp4")
    concat_list_path = "/tmp/poet_bookend_concat.txt"
    featured_indices = [0, 1, 4, 7, 9, 13]
    with open(concat_list_path, "w") as f:
        for i in featured_indices:
            f.write(f"file '{poem_mp4s[i]}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-c", "copy", "-movflags", "+faststart",
        master_out
    ], check=True)
    shutil.copy2(master_out, os.path.join(ARTIFACT_DIR, "wygwyl_poet_retelling_bookend_spacetime.mp4"))
    shutil.copy2(poem_mp4s[0], os.path.join(ARTIFACT_DIR, "poem_01_bookend_spacetime.mp4"))
    print("  -> Saved Master Poet Bookend Anthology Film:", master_out)


# ==============================================================================
# STEP 4: UPDATE DATA BUNDLES WITH ALL 6 SEGMENTED MODES PER SHOT
# ==============================================================================
def update_bundles_with_poet_bookends():
    print("Step 5: Updating vesper_world_bundle.json and stelline_spacetime_data.js...")
    bundle_path = os.path.join(FILM_OUT_DIR, "vesper_world_bundle.json")
    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    bundle["poet_lectern_stages"] = POET_LECTERN_STAGES
    bundle["k_segmented_stages"] = [
        {
            "sid": ks["sid"],
            "title": ks["title"],
            "act": ks["act"],
            "raw_file": f"out/{ks['sid']}/image.jpg",
            "overlay_file": f"out/{ks['sid']}/overlay.jpg",
            "layout_file": f"out/{ks['sid']}/cartoon/layout_sheet.png",
            "cel_file": f"out/{ks['sid']}/cartoon/cel.png",
            "angular_file": f"out/{ks['sid']}/program/frame0.png",
            "exploded_file": f"out/{ks['sid']}/multiplane/exploded.jpg",
        }
        for ks in K_SHOT_SPECS
    ]
    bundle["poet_bookend_master_video"] = "videos/wygwyl_poet_retelling_bookend_spacetime.mp4"
    bundle["poet_bookend_architecture_sheet"] = "data/terrarium/seeing_spacetime_films/poet_bookend_vs_k_interview_sheet.png"
    bundle["poet_bookend_14poems_sheet"] = "data/terrarium/seeing_spacetime_films/poet_retelling_bookend_14poems_sheet.png"

    for p, spec in zip(bundle["poems"], POEM_BOOKEND_SPECS):
        ns = f"{spec['num']:02d}"
        views = p.get("views", [])
        v_hero_dir = (views[0].get("dir") or views[0].get("shot_dir")) if views else "62b9740c-d0be-4b4a-a311-d653a2580907_1"
        p["poet_bookend"] = {
            "bookend_video": f"videos/poet_bookends/poem_{ns}_bookend_spacetime.mp4",
            "spoken_reading_audio": f"play/levels/{ns}/reading.mp3",
            "wooden_horse_anchor": spec["wooden_horse_anchor"],
            "anchor_detail": spec["anchor_detail"],
            "opening_cue": spec["opening_cue"],
            "peak_cue": spec["peak_cue"],
            "closing_cue": spec["closing_cue"],
            "hero_segmented_versions": {
                "raw": f"out/{v_hero_dir}/image.jpg",
                "overlay": f"out/{v_hero_dir}/overlay.jpg",
                "layout": f"out/{v_hero_dir}/cartoon/layout_sheet.png",
                "cel": f"out/{v_hero_dir}/cartoon/cel.png",
                "angular": f"out/{v_hero_dir}/program/frame0.png",
                "exploded": f"out/{v_hero_dir}/multiplane/exploded.jpg",
            },
            "acts": [
                {
                    "act": "ACT I · P0–P6 SALON DECONSTRUCTION (0:00 – 0:03.8)",
                    "t0": 0.0, "t1": 3.8,
                    "title": "Warm Graffiti Salon → 7-Plane Segmented Peel (Layout → Cel → Angular)",
                    "k_parallel": "1:49 – 2:00 (k_01) · K & Joshi across the interview table",
                    "cue": spec["opening_cue"],
                },
                {
                    "act": "ACT II · CROSS-WORLD PLANE HAND-OFF (0:03.8 – 0:07.0)",
                    "t0": 3.8, "t1": 7.0,
                    "title": "P4/P5 Mural Swaps First · P1 Acrylic Stand Refracts · P2 Hands Release",
                    "k_parallel": "2:00 – 2:06 (k_02) · 'I had a little toy horse... Everything's grey'",
                    "cue": "Behind the segmented Poet (P2), the studio wall peels into the Poem's layout blueprint while the acrylic lectern ignites.",
                },
                {
                    "act": "ACT III · SEGMENTED MEMORY WORLD (0:07.0 – 0:11.2)",
                    "t0": 7.0, "t1": 11.2,
                    "title": f"Multiplane Parallax: Layout Grid → Painted Cel → Angular Vector → Motion ({spec['title']})",
                    "k_parallel": "2:06 – 2:24 (k_03/k_04) · Orphanage catwalks & clockwork gears",
                    "cue": spec["peak_cue"],
                },
                {
                    "act": "ACT IV · ISOLATED P2/P3 EMOTIONAL ANCHOR (0:11.2 – 0:14.6)",
                    "t0": 11.2, "t1": 14.6,
                    "title": f"Wooden Horse Talisman: {spec['wooden_horse_anchor']}",
                    "k_parallel": "2:24 – 2:47 (k_05/k_06) · Carved Wooden Horse (6·10·21) isolated in P2",
                    "cue": spec["anchor_detail"],
                },
                {
                    "act": "ACT V · CLOSING BOOKEND — CIRCLE REASSEMBLY (0:14.6 – 0:18.0)",
                    "t0": 14.6, "t1": 18.0,
                    "title": "P2 Poet Silhouette & P3 Circle of Listeners Resolve Back Into Reality",
                    "k_parallel": "3:06 – 3:25 (k_08) · Return to room & listener ('Someone lived this')",
                    "cue": spec["closing_cue"],
                },
            ],
        }

    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False)

    stelline_js_path = os.path.join(TERR_DIR, "stelline_spacetime_data.js")
    with open(stelline_js_path, "r", encoding="utf-8") as f:
        txt = f.read()
    prefix = "window.STELLINE_SPACETIME_DATA = "
    payload = json.loads(txt[len(prefix):].rstrip(";\n ")) if txt.startswith(prefix) else {}

    payload["poet_lectern_stages"] = POET_LECTERN_STAGES
    payload["k_segmented_stages"] = bundle["k_segmented_stages"]
    payload["poet_bookend_specs"] = POEM_BOOKEND_SPECS
    payload["poet_bookend_master_video"] = "videos/wygwyl_poet_retelling_bookend_spacetime.mp4"
    payload["poet_bookend_architecture_sheet"] = "data/terrarium/seeing_spacetime_films/poet_bookend_vs_k_interview_sheet.png"
    payload["poet_bookend_14poems_sheet"] = "data/terrarium/seeing_spacetime_films/poet_retelling_bookend_14poems_sheet.png"
    payload["poems"] = bundle["poems"]

    with open(stelline_js_path, "w", encoding="utf-8") as f:
        f.write("window.STELLINE_SPACETIME_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    print("  -> Updated", stelline_js_path)


def main():
    build_poet_and_k_dope_composites()
    bundle_path = os.path.join(FILM_OUT_DIR, "vesper_world_bundle.json")
    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    tasks = list(zip(bundle["poems"], POEM_BOOKEND_SPECS))
    with ProcessPoolExecutor(max_workers=7) as ex:
        results = list(ex.map(_render_poem_worker, tasks))

    poem_mp4s = [r[0] for r in results]
    all_poem_strips = [r[1] for r in results]

    build_bookend_contact_sheets_and_master_film(all_poem_strips, poem_mp4s)
    update_bundles_with_poet_bookends()
    print("ALL DONE! 14 Plane-Synchronized Bookend Poem Films + 2 4K Sheets + Master Anthology Film built.")


if __name__ == "__main__":
    main()
