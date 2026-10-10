#!/usr/bin/env python3
"""
build_film_suite.py
Generates the comprehensive data files for the WYGWYL Film, Atlantis Map, and Storyboard Suite:
  1. shots/film_data.js       - 14 poems, 4 cuts, beats, timestamps, Deleuze signs & readings
  2. shots/city_data.js       - 12 districts, palettes, altitude profiles, landmarks, shot coordinates
  3. shots/storyboard_data.js - Beat-by-beat storyboard panels with grounds, SAM cutouts, camera moves
"""
import glob, json, math, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS_DIR = os.path.join(ROOT, "shots")
OUT_DIR = os.path.join(SHOTS_DIR, "out")

# Deleuze's 44 Cinematic Signs after David Deamer (Edinburgh UP, 2016)
SIGNS = {
    # 1. Perception (zeroness)
    "So": {"name": "Solid perception", "cat": "perception", "col": "#e9d9a8", "code": "000",
           "gloss": "Anchored, normal human sensorimotor perception.", "test": "Is perception bound to a terrestrial body or object?"},
    "Li": {"name": "Liquid perception", "cat": "perception", "col": "#e9d9a8", "code": "001",
           "gloss": "Aqueous, flowing, reflective consciousness without fixed horizon.", "test": "Does perception flow like water, reflection, or current?"},
    "Gs": {"name": "Gas perception", "cat": "perception", "col": "#e9d9a8", "code": "002",
           "gloss": "Molecular, microscopic, cosmic or unanchored viewpoint.", "test": "Has perception escaped all human anchoring into the ether?"},
    
    # 2. Affect (Firstness: 111)
    "Ic": {"name": "Icon", "cat": "affect", "col": "#f0b9a4", "code": "111",
           "gloss": "The face or close-up expressing pure affect.", "test": "Does the shot hold an affective entity abstracted from space?"},
    "Ql": {"name": "Qualisign", "cat": "affect", "col": "#f0b9a4", "code": "112",
           "gloss": "Any-space-whatever, pure tonal or atmospheric hue.", "test": "Is space dissolved into a single atmospheric quality (fog, neon, rain)?"},
    "Pt": {"name": "Potisign", "cat": "affect", "col": "#f0b9a4", "code": "113",
           "gloss": "Virtual capacity or power gathering before action.", "test": "Does the shot hold tension that has not yet broken into action?"},
    "Df": {"name": "Diaisign", "cat": "affect", "col": "#f0b9a4", "code": "114",
           "gloss": "Threshold or transition where one affect turns into another.", "test": "Is a face or space in the exact instant of shifting affect?"},

    # 3. Impulse (211)
    "Sy": {"name": "Synsign", "cat": "action", "col": "#e7a37c", "code": "221",
           "gloss": "An action situation: an environment dictating behavior.", "test": "Does the setting impose a specific mode of survival or habit?"},
    "Il": {"name": "Impulse", "cat": "action", "col": "#e7a37c", "code": "211",
           "gloss": "Primal drive, raw appetite, predation or destructive energy.", "test": "Is behavior driven by elemental hunger, fury, or panic?"},
    "Mi": {"name": "Milieu", "cat": "action", "col": "#e7a37c", "code": "212",
           "gloss": "An originary world of ruins, mud, smoke, or wasteland.", "test": "Is this a world stripped of civil order down to bare matter?"},

    # 4. Action (Secondness: 222)
    "Du": {"name": "Duel", "cat": "action", "col": "#e7a37c", "code": "222",
           "gloss": "Direct physical confrontation: figure against obstacle or adversary.", "test": "Is there a direct head-on struggle between forces?"},
    "In": {"name": "Index", "cat": "action", "col": "#e7a37c", "code": "223",
           "gloss": "An equivocal clue, trace, or absence pointing to an action.", "test": "Does the shot read through an inference from a mark or footprint?"},
    "Im": {"name": "Immersion", "cat": "action", "col": "#e7a37c", "code": "224",
           "gloss": "Total submersion of the subject into the sensory medium.", "test": "Is the figure engulfed completely by the element?"},

    # 5. Reflection (311 / 321)
    "Pl": {"name": "Plastisign", "cat": "reflection", "col": "#b9cfa0", "code": "311",
           "gloss": "Architectural or geometric crystalline reflection.", "test": "Is the composition dominated by pure formal geometry or crystal lines?"},
    "Su": {"name": "Susign", "cat": "reflection", "col": "#b9cfa0", "code": "321",
           "gloss": "A question posed by the image; reflection upon choices.", "test": "Does the image pause action to weigh an ethical or spatial decision?"},
    "Ll": {"name": "Luminisign", "cat": "reflection", "col": "#b9cfa0", "code": "312",
           "gloss": "Light sculpting matter: chiaroscuro, beams cutting darkness.", "test": "Is light itself the subject cutting through obscurity?"},

    # 6. Mental / Relation (Thirdness: 333)
    "Mk": {"name": "Mark", "cat": "mental", "col": "#a9c9c9", "code": "331",
           "gloss": "A customary sign, natural relation, or established habit.", "test": "Does the sign evoke an established social or ritual custom?"},
    "Dm": {"name": "Demark", "cat": "mental", "col": "#a9c9c9", "code": "332",
           "gloss": "The sudden rupture or defamiliarization of a relation.", "test": "Does a familiar object suddenly become uncanny or estranged?"},
    "Rd": {"name": "Reduct", "cat": "mental", "col": "#a9c9c9", "code": "333",
           "gloss": "Symbolic relation: an idea connecting two disparate realities.", "test": "Does the image link two terms through intellectual relation?"},
    "Sd": {"name": "Schema", "cat": "mental", "col": "#a9c9c9", "code": "334",
           "gloss": "The web or nervous system connecting all parts of the city.", "test": "Does the shot reveal the unseen network or system?"},

    # 7. Break / Pure Sensation (0)
    "Op": {"name": "Opsign", "cat": "break", "col": "#d9d3c7", "code": "001",
           "gloss": "Pure optical situation: seeing without being able to act.", "test": "Does the spectator or character simply gaze into a vast stillness?"},
    "Sn": {"name": "Sonsign", "cat": "break", "col": "#d9d3c7", "code": "002",
           "gloss": "Pure sound situation: autonomous acoustic event or voice.", "test": "Is the audio/ambient hum independent of visible action?"},

    # 8. Time (1 / 2)
    "Hy": {"name": "Hyalosign", "cat": "time", "col": "#b8b3d8", "code": "101",
           "gloss": "The crystal of time: mutual reflection of actual and virtual.", "test": "Do the past memory and present reality form an indivisible mirror?"},
    "Mf": {"name": "Monstration", "cat": "time", "col": "#b8b3d8", "code": "102",
           "gloss": "Direct presentation of time: peaks of present coexisting.", "test": "Is time itself presented directly rather than inferred from movement?"},
    "Pp": {"name": "Chronosign: past", "cat": "time", "col": "#b8b3d8", "code": "201",
           "gloss": "Sheets of past: layers of historical and personal memory.", "test": "Are deep strata of former eras visible simultaneously?"},
    "Ba": {"name": "Chronosign: series", "cat": "time", "col": "#b8b3d8", "code": "202",
           "gloss": "Irreversible becoming, transformative series, cosmic threshold.", "test": "Is the figure or space crossing a point of no return?"},

    # 9. Reader
    "Le": {"name": "Lectosign", "cat": "read", "col": "#d9b8d2", "code": "301",
           "gloss": "The image that must be read like a glyph, chart, or text.", "test": "Must the viewer decipher written letters, numbers, or symbols?"}
}

POEMS_SPEC = [
    {
        "num": "01",
        "title": "Out of Life",
        "district": "naraka",
        "mood": "dusk into night · haze · cold descent",
        "quote": "His high-rise room in The Severn above the market, dusk into night.",
        "beats": [
            {"id": "01.1", "line": "Look from the high-rise window as the market drowns in teal.", "sign": "Op",
             "camera": "SLO PUSH IN", "duration": 6.5, "district": "naraka", "shot_hint": "dark_futuristic_cityscape_hive"},
            {"id": "01.2", "line": "A language made exact: towers of the New Boroughs darkened in the Fall.", "sign": "Pl",
             "camera": "TILT UP 45°", "duration": 7.0, "district": "hive", "shot_hint": "hive-walls_crusted"},
            {"id": "01.3", "line": "Engines tick beneath the catwalks; the air burns near-solid orange.", "sign": "Mi",
             "camera": "TRACK R", "duration": 6.0, "district": "haze", "shot_hint": "Air_burns_orange"}
        ]
    },
    {
        "num": "02",
        "title": "Flashing Lights",
        "district": "overseer",
        "mood": "black space · blinking beacons · the moon",
        "quote": "Black space with lights flashing: the beacons. Headlights raking a dark room.",
        "beats": [
            {"id": "02.1", "line": "The moon standing in the narrow slot between two indigo towers.", "sign": "Ll",
             "camera": "STATIC TELE", "duration": 6.0, "district": "overseer", "shot_hint": "The_Overseer_blue_cityscape"},
            {"id": "02.2", "line": "Lattice signal towers with red and blue beacons pulsing like a nervous system.", "sign": "Sd",
             "camera": "CRANE DOWN", "duration": 6.5, "district": "hive", "shot_hint": "indigo_hive_spires"},
            {"id": "02.3", "line": "Cold grandeur and signal lights across the sterile northern perimeter.", "sign": "Ic",
             "camera": "PAN L", "duration": 5.5, "district": "overseer", "shot_hint": "indigo_hive_spires"}
        ]
    },
    {
        "num": "03",
        "title": "How to Break off an Engagement",
        "district": "bay",
        "mood": "storm aftermath · flooded atria · handprints",
        "quote": "The storm and its aftermath: the flooded corridors.",
        "beats": [
            {"id": "03.1", "line": "Submerged corridors beneath reflective pools where daylight never reaches.", "sign": "Li",
             "camera": "PUSH IN", "duration": 7.0, "district": "bay", "shot_hint": "Mirror_Thread_Bay_submerged_corridors"},
            {"id": "03.2", "line": "Handprints on the glass of a drowned corridor: someone was here before the water.", "sign": "In",
             "camera": "CLOSE PUSH", "duration": 6.5, "district": "bay", "shot_hint": "submerged_corridors_beneath_refle"},
            {"id": "03.3", "line": "Saltwater graffiti beneath the sleep-dam wall: 'REMEMBER THE SHORE'.", "sign": "Le",
             "camera": "PAN R", "duration": 6.0, "district": "bay", "shot_hint": "saltwater_graffiti_beneath_sleep-dam"}
        ]
    },
    {
        "num": "04",
        "title": "Nevermore",
        "district": "bay",
        "mood": "twilight shore · calm waves · distant heights",
        "quote": "The shore at twilight, calm waves; looking across the water toward the spires.",
        "beats": [
            {"id": "04.1", "line": "A lone silhouette in the twilight haze beside calm water.", "sign": "Op",
             "camera": "STATIC WIDE", "duration": 7.0, "district": "bay", "shot_hint": "Panasonic_GH6"},
            {"id": "04.2", "line": "Looking up from the shore at open-air platforms suspended in periwinkle mist.", "sign": "Pl",
             "camera": "TILT UP", "duration": 6.5, "district": "ankhu", "shot_hint": "Ankhu_Spires_high-altitude_open-air"},
            {"id": "04.3", "line": "The boardwalk beneath the great bridge where the diaspora watches the tide.", "sign": "Sy",
             "camera": "TRACK R", "duration": 6.0, "district": "bay", "shot_hint": "Afrofuturist_waterfront_district_Mirror"}
        ]
    },
    {
        "num": "05",
        "title": "Bloodline",
        "district": "ascent",
        "mood": "ancestor communion · rooftops · heritage",
        "quote": "The POET entering the Ancestors' parade, receiving cosmic gifts.",
        "beats": [
            {"id": "05.1", "line": "The POET entering the Ancestors' parade, golden dust floating through the gate.", "sign": "Ba",
             "camera": "CRANE FWD", "duration": 8.0, "district": "ascent", "shot_hint": "POET_entering_Ancestors"},
            {"id": "05.2", "line": "Dark futuristic skyline with tall chrono-decayed spires under a violet sky.", "sign": "Pp",
             "camera": "PAN L", "duration": 7.0, "district": "hive", "shot_hint": "dark_futuristic_skyline_with_tall"},
            {"id": "05.3", "line": "Rooftop laundry drying in the metallic hum beneath Ankhu's hanging gardens.", "sign": "Ql",
             "camera": "SLOW ZOOM", "duration": 6.0, "district": "ankhu", "shot_hint": "rooftop_laundry_beneath_Ankhu"}
        ]
    },
    {
        "num": "06",
        "title": "Resurrecting Atlantis",
        "district": "plaza",
        "mood": "threshold · arrival · manifestation",
        "quote": "He sees the entrance, goes in through the gates.",
        "beats": [
            {"id": "06.1", "line": "The Overseer's Perimeter Gate: transparent high-frequency fence buzzing with white light.", "sign": "Pt",
             "camera": "DOLLY IN", "duration": 6.5, "district": "plaza", "shot_hint": "The_Overseers_Perimeter_Gate"},
            {"id": "06.2", "line": "Sweeping aerial over Atlantis Central Plaza: circular rose terraces and crystal courts.", "sign": "Pl",
             "camera": "CRANE DOWN", "duration": 7.5, "district": "plaza", "shot_hint": "Atlantis_City_central_plaza_sweeping"},
            {"id": "06.3", "line": "Vibrant manifestation of energy rising from the central reflection pool.", "sign": "Hy",
             "camera": "ORBIT R", "duration": 7.0, "district": "plaza", "shot_hint": "Atlantis_City_central_plaza_vibrant"}
        ]
    },
    {
        "num": "07",
        "title": "DJ Turn Me Up",
        "district": "naraka",
        "mood": "club haze · street crush · bass hum",
        "quote": "The club crowd dissolving in warm haze.",
        "beats": [
            {"id": "07.1", "line": "Neon reflections in the wet asphalt; the crowd dissolves into orange and turquoise vapor.", "sign": "Li",
             "camera": "HANDHELD", "duration": 5.5, "district": "naraka", "shot_hint": "Canon_A-1"},
            {"id": "07.2", "line": "Urban LED canyon crossroads: high-voltage billboards pulsating over the night market.", "sign": "Sy",
             "camera": "WHIP PAN", "duration": 5.0, "district": "naraka", "shot_hint": "urban_LED_canyon_crossroads"}
        ]
    },
    {
        "num": "08",
        "title": "Newly Single",
        "district": "ankhu",
        "mood": "altitude · solitude · breath",
        "quote": "High-altitude platforms connecting the mushroom-cap spires.",
        "beats": [
            {"id": "08.1", "line": "Standing on an open-air platform four hundred meters above the fog line.", "sign": "Op",
             "camera": "STATIC WIDE", "duration": 7.0, "district": "ankhu", "shot_hint": "Ankhu_Spires_high-altitude_open-air"},
            {"id": "08.2", "line": "Hanging gardens on slender stems sway in the mountain updraft.", "sign": "Ql",
             "camera": "SLOW PUSH", "duration": 6.5, "district": "ankhu", "shot_hint": "open-air_platforms_conne_cbb5e9c5"},
            {"id": "08.3", "line": "The terracotta souk at the base of the spire breathes cumin and roasted coffee.", "sign": "So",
             "camera": "PAN R", "duration": 6.0, "district": "ankhu", "shot_hint": "Afrofuturist_high-altitude_city_core"}
        ]
    },
    {
        "num": "09",
        "title": "Yet Heard",
        "district": "arcade",
        "mood": "someone else's rain · memory corridor",
        "quote": "You're soaked in someone else's rain. Neon hums beneath.",
        "beats": [
            {"id": "09.1", "line": "Soaked in someone else's rain; the neon arcade hums an abandoned broadcast.", "sign": "Sn",
             "camera": "SLOW TRACK", "duration": 6.5, "district": "arcade", "shot_hint": "soaked_in_someone_elses_rain"},
            {"id": "09.2", "line": "Rainy red-blue glow inside the memory corridor: signs for shops that vanished decades ago.", "sign": "Pp",
             "camera": "PUSH IN", "duration": 6.5, "district": "arcade", "shot_hint": "Neon_Alley_Rainy_RedBlue"},
            {"id": "09.3", "line": "The symmetrical moon canyon reflects across puddles of synthetic oil.", "sign": "Hy",
             "camera": "TILT DOWN", "duration": 5.5, "district": "overseer", "shot_hint": "The_Overseer_blue_cityscape_at_night"}
        ]
    },
    {
        "num": "10",
        "title": "Magic Ride",
        "district": "haze",
        "mood": "motorcycle through tunnel · sodium smog",
        "quote": "The motorcycle through tunnel light toward dawn: the undercroft and the skyway.",
        "beats": [
            {"id": "10.1", "line": "The Orange Haze: brutalist concrete undercrofts where sodium lamps burn continuously.", "sign": "Mi",
             "camera": "LOW TRACK", "duration": 6.0, "district": "haze", "shot_hint": "Orange-Hazed_Dystopia"},
            {"id": "10.2", "line": "Skyway through oppressive smog: a single runner steps across the expansion joints.", "sign": "Du",
             "camera": "TRACK FWD", "duration": 6.5, "district": "haze", "shot_hint": "orange_smog_skyway"},
            {"id": "10.3", "line": "Elevated concrete catwalk with glowing amber kerb strips winding toward the towers.", "sign": "Pl",
             "camera": "CRANE UP", "duration": 6.0, "district": "haze", "shot_hint": "The_Orange_Catwalk"}
        ]
    },
    {
        "num": "11",
        "title": "New Day",
        "district": "cenotaph",
        "mood": "wet stone · viaducts · mountain railway",
        "quote": "Wet stone steps beneath mountain in Cenotaph Rail district.",
        "beats": [
            {"id": "11.1", "line": "Wet stone steps climbing toward the mountain viaduct under a gray morning mist.", "sign": "Du",
             "camera": "TILT UP", "duration": 7.0, "district": "cenotaph", "shot_hint": "wet_stone_steps_beneath_mountain"},
            {"id": "11.2", "line": "Shadow play beneath solar bridges: sun-bleached asphalt and rusted steel trestles.", "sign": "Ll",
             "camera": "PAN R", "duration": 6.0, "district": "cenotaph", "shot_hint": "shadow_play_beneath_solar"},
            {"id": "11.3", "line": "Saltwater graffiti beneath the sleep-dam wall: words half-eaten by the tide.", "sign": "Le",
             "camera": "STATIC", "duration": 6.5, "district": "cenotaph", "shot_hint": "saltwater_graffiti"}
        ]
    },
    {
        "num": "12",
        "title": "Reunion",
        "district": "temple",
        "mood": "mirror pool · white stone · still water",
        "quote": "A perfect mirror pool with white colonnades meeting the shore.",
        "beats": [
            {"id": "12.1", "line": "Mirror-pool skyline inspired by ancient Federation symmetry: columns carved in white salt.", "sign": "Pl",
             "camera": "PUSH IN", "duration": 7.5, "district": "temple", "shot_hint": "mirror-pool_skyline"},
            {"id": "12.2", "line": "Night falls over the water: ripples die down until the sky is doubled without error.", "sign": "Li",
             "camera": "STATIC WIDE", "duration": 7.0, "district": "temple", "shot_hint": "futuristic_city_at_night_a_perfect_mirror"},
            {"id": "12.3", "line": "Reflecting Pool Mouth: looking across the threshold where temple meets bay.", "sign": "Hy",
             "camera": "SLOW PAN", "duration": 6.5, "district": "temple", "shot_hint": "Reflecting_Pool_Mouth"}
        ]
    },
    {
        "num": "13",
        "title": "How to Win My Heart",
        "district": "bay",
        "mood": "daylight harbor walk · turquoise lagoon",
        "quote": "The daylight harbor walk to the corner café.",
        "beats": [
            {"id": "13.1", "line": "Morning light strikes the turquoise lagoons: garden islands anchored by thick steel cables.", "sign": "So",
             "camera": "DOLLY R", "duration": 6.5, "district": "bay", "shot_hint": "Afrofuturist_waterfront_district_Mirror_Thread_Bay__22fcebea"},
            {"id": "13.2", "line": "Walk along the boardwalk beneath the suspension bridge: salt breeze and chatter from the souks.", "sign": "Sy",
             "camera": "TRACK FWD", "duration": 6.5, "district": "bay", "shot_hint": "Afrofuturist_waterfront_district_Mirror_Thread_Bay__932cb5b5"},
            {"id": "13.3", "line": "High-altitude view of the bay meeting the mountain terraces in golden daylight.", "sign": "Pl",
             "camera": "SLOW CRANE", "duration": 7.0, "district": "ankhu", "shot_hint": "Afrofuturist_city_district_Ankhu_Spires"}
        ]
    },
    {
        "num": "14",
        "title": "Hot Minute",
        "district": "ascent",
        "mood": "harbor party · the soul ascending",
        "quote": "The POET's soul ascending, observing Atlantis from above.",
        "beats": [
            {"id": "14.1", "line": "The POET's soul ascending, watching Atlantis fall away into concentric rings of blue and orange.", "sign": "Gs",
             "camera": "VERTICAL CRANE UP", "duration": 8.5, "district": "ascent", "shot_hint": "POETs_soul_ascending"},
            {"id": "14.2", "line": "The harbor party below dissolves into tiny points of orange and magenta light.", "sign": "Op",
             "camera": "SLOW ZOOM OUT", "duration": 7.0, "district": "ascent", "shot_hint": "Panasonic_GH6"},
            {"id": "14.3", "line": "The final cut: a camera shutter clicks; twilight returns to the Severn fire escape.", "sign": "Le",
             "camera": "STATIC HOLD", "duration": 7.5, "district": "naraka", "shot_hint": "Canon_A-1"}
        ]
    }
]


def match_shot_id(hint, available_shots):
    """Finds best matching shot in shots/out for a given hint."""
    for s in available_shots:
        if hint.lower() in s["prompt"].lower() or hint.lower() in s.get("file", "").lower() or hint.lower() in s["id"].lower():
            return s["id"]
    return available_shots[0]["id"] if available_shots else ""


def build_suite():
    # Load all available shots in shots/out
    available_shots = []
    for p in glob.glob(os.path.join(OUT_DIR, "*", "shot.json")):
        try:
            j = json.load(open(p))
            available_shots.append(j)
        except Exception: pass
    available_shots.sort(key=lambda s: s["id"])
    print(f"Loaded {len(available_shots)} analyzed shots from {OUT_DIR}")

    shot_map = {s["id"]: s for s in available_shots}

    # Load districts
    dist_file = os.path.join(ROOT, "_city", "districts.json")
    dist_data = json.load(open(dist_file)) if os.path.exists(dist_file) else {"districts": []}
    districts = dist_data.get("districts", [])

    # Map district coordinates on the city plan
    D_COORDS = {
        "naraka":   {"x": 166, "y": 152, "alt": 5, "zone": "Ground Harbor"},
        "haze":     {"x": 203, "y": 170, "alt": 18, "zone": "Industrial Undercroft"},
        "hive":     {"x": 122, "y": 148, "alt": 180, "zone": "New Borough Towers"},
        "overseer": {"x": 167, "y": 103, "alt": 95, "zone": "Northern Perimeter"},
        "bay":      {"x": 123, "y": 184, "alt": -3, "zone": "Submerged Bay & Shore"},
        "commons":  {"x": 93,  "y": 169, "alt": 12, "zone": "Civic Forum"},
        "arcade":   {"x": 102, "y": 214, "alt": 14, "zone": "Abandoned Consumer Sector"},
        "cenotaph": {"x": 167, "y": 244, "alt": 45, "zone": "Mountain Rail Viaduct"},
        "plaza":    {"x": 378, "y": 268, "alt": 110, "zone": "High Ground Light Gate"},
        "ankhu":    {"x": 390, "y": 282, "alt": 220, "zone": "Mountain Terraces & Souks"},
        "temple":   {"x": 260, "y": 313, "alt": 25, "zone": "White Salt Colonnade"},
        "ascent":   {"x": 490, "y": 80,  "alt": 450, "zone": "Cosmic Spire & Upper Ether"}
    }

    # Assign shot IDs to poem beats
    all_beats = []
    for p in POEMS_SPEC:
        for b in p["beats"]:
            sid = match_shot_id(b["shot_hint"], available_shots)
            b["shot_id"] = sid
            b["sign_meta"] = SIGNS.get(b["sign"], {"name": b["sign"], "cat": "unknown", "col": "#888"})
            all_beats.append(b)

    # 4 Cuts of WYGWYL
    # Cut 1: Narrative Cut (chronological through poems 01-14)
    cut1_beats = []
    t_acc = 0.0
    for b in all_beats:
        nb = dict(b)
        nb["t_start"] = round(t_acc, 2)
        t_acc += nb["duration"]
        nb["t_end"] = round(t_acc, 2)
        cut1_beats.append(nb)

    # Cut 2: Spatial Drift (organized by altitude: Harbor -> High Mountain -> Cosmic)
    cut2_sorted = sorted(all_beats, key=lambda b: D_COORDS.get(b["district"], {}).get("alt", 0))
    cut2_beats = []
    t_acc = 0.0
    for b in cut2_sorted:
        nb = dict(b)
        nb["duration"] = round(b["duration"] * 0.9, 1)
        nb["t_start"] = round(t_acc, 2)
        t_acc += nb["duration"]
        nb["t_end"] = round(t_acc, 2)
        cut2_beats.append(nb)

    # Cut 3: Emotional Resonance / Interiority (Memory, Time, Liquid perception first)
    cut3_sorted = sorted(all_beats, key=lambda b: (0 if b["sign"] in ("Hy", "Pp", "Li", "Op", "In") else 1, b["duration"]))
    cut3_beats = []
    t_acc = 0.0
    for b in cut3_sorted:
        nb = dict(b)
        nb["duration"] = round(b["duration"] * 0.95, 1)
        nb["t_start"] = round(t_acc, 2)
        t_acc += nb["duration"]
        nb["t_end"] = round(t_acc, 2)
        cut3_beats.append(nb)

    # Cut 4: Kinetic Beat Cut (Rapid montage: 3.6s per shot)
    cut4_beats = []
    t_acc = 0.0
    for b in all_beats:
        nb = dict(b)
        nb["duration"] = 3.6
        nb["t_start"] = round(t_acc, 2)
        t_acc += 3.6
        nb["t_end"] = round(t_acc, 2)
        cut4_beats.append(nb)

    film_data = {
        "signs": SIGNS,
        "poems": POEMS_SPEC,
        "cuts": {
            "A": {
                "id": "A",
                "name": "The Narrative Arc",
                "tagline": "The canonical sequence: dusk in The Severn, through the New Boroughs, arriving at the Light Gate and the Ascent.",
                "total_sec": cut1_beats[-1]["t_end"] if cut1_beats else 0,
                "beats": cut1_beats
            },
            "B": {
                "id": "B",
                "name": "The Spatial Drift",
                "tagline": "An architectural climb through Atlantis by elevation: submerged bay → street market → viaduct → sky platforms → cosmic ionosphere.",
                "total_sec": cut2_beats[-1]["t_end"] if cut2_beats else 0,
                "beats": cut2_beats
            },
            "C": {
                "id": "C",
                "name": "The Memory Corridors",
                "tagline": "Interiority and crystal time: drowned rooms, neon reflections, laundry under the stars, ancestral communion.",
                "total_sec": cut3_beats[-1]["t_end"] if cut3_beats else 0,
                "beats": cut3_beats
            },
            "D": {
                "id": "D",
                "name": "The Kinetic Beat",
                "tagline": "A rapid pulse cut on twos: sodium highways, signal towers, strobe fences, and club vapor.",
                "total_sec": cut4_beats[-1]["t_end"] if cut4_beats else 0,
                "beats": cut4_beats
            }
        }
    }

    # Write shots/film_data.js
    with open(os.path.join(SHOTS_DIR, "film_data.js"), "w") as fh:
        fh.write("window.FILM = " + json.dumps(film_data, indent=1) + ";\n")
    print(f"wrote shots/film_data.js ({len(POEMS_SPEC)} poems, 4 cuts)")

    # Build shots/city_data.js
    city_districts = []
    for d in districts:
        did = d["id"]
        coords = D_COORDS.get(did, {"x": 300, "y": 200, "alt": 50, "zone": "Sector"})
        d_shots = [s["id"] for s in available_shots if s.get("district") == did]
        d_rec = {
            "id": did,
            "name": d["name"],
            "realm": d["realm"],
            "where": d["where"],
            "eras": d["eras"],
            "mood": d["mood"],
            "arch": d["arch"],
            "materials": d["materials"],
            "signature": d["signature"],
            "color": d.get("color", "#01acd4"),
            "body": d.get("body", []),
            "glow": d.get("glow", []),
            "glow_share": d.get("glow_share", 0.05),
            "dark": d.get("dark", 0.2),
            "mean_lum": d.get("mean_lum", 60),
            "coords": coords,
            "shots": d_shots,
            "key": d.get("key", []),
            "moments": d.get("moments", []),
            "poems": d.get("poems", [])
        }
        city_districts.append(d_rec)

    city_data = {
        "districts": city_districts,
        "altitudes": [
            {"label": "Submerged Bay", "min_m": -15, "max_m": 0, "color": "#465fb1", "realm": "C · Harbor & Shore"},
            {"label": "Ground Market", "min_m": 0, "max_m": 25, "color": "#01acd4", "realm": "B · Old Harbor City"},
            {"label": "Mid Viaducts", "min_m": 25, "max_m": 70, "color": "#fa8d15", "realm": "B · Industrial Ring"},
            {"label": "High Terraces", "min_m": 70, "max_m": 150, "color": "#bb7362", "realm": "A · Atlantis High Ground"},
            {"label": "Spires & Souks", "min_m": 150, "max_m": 300, "color": "#d36f46", "realm": "A · Ankhu Peaks"},
            {"label": "Cosmic Ionosphere", "min_m": 300, "max_m": 600, "color": "#2560e1", "realm": "A · The Ascent"}
        ]
    }

    with open(os.path.join(SHOTS_DIR, "city_data.js"), "w") as fh:
        fh.write("window.CITY = " + json.dumps(city_data, indent=1) + ";\n")
    print(f"wrote shots/city_data.js ({len(city_districts)} districts)")

    # Build shots/storyboard_data.js
    sb_panels = []
    for p in POEMS_SPEC:
        for idx, b in enumerate(p["beats"]):
            sid = b["shot_id"]
            shot_rec = shot_map.get(sid, {})
            cam = shot_rec.get("camera", {})
            dets = shot_rec.get("detections", [])
            figures = []
            for d in dets[:4]:
                figures.append({
                    "label": d.get("label", "figure"),
                    "box": d.get("box", [0, 0, 100, 100]),
                    "area_pct": round(d.get("area_pct", 0.05), 3),
                    "conf": round(d.get("conf", 0.8), 2)
                })
            panel = {
                "id": f"p_{b['id']}",
                "poem_num": p["num"],
                "poem_title": p["title"],
                "beat_idx": idx + 1,
                "line": b["line"],
                "quote": p["quote"],
                "district": b["district"],
                "shot_id": sid,
                "camera_move": b["camera"],
                "camera_params": {
                    "height_m": cam.get("height_m"),
                    "pitch_deg": cam.get("pitch_deg"),
                    "fov_h_deg": cam.get("fov_h_deg"),
                    "shot_class": cam.get("shot_class")
                },
                "sign": b["sign"],
                "sign_meta": b["sign_meta"],
                "figures": figures,
                "director_note": f"Stage on {b['camera'].lower()} with {b['sign_meta']['name']} ({b['sign']}). Scale ladder keyed to camera h={cam.get('height_m') or '1.5'} m."
            }
            sb_panels.append(panel)

    storyboard_data = {
        "panels": sb_panels,
        "total_panels": len(sb_panels)
    }

    with open(os.path.join(SHOTS_DIR, "storyboard_data.js"), "w") as fh:
        fh.write("window.STORYBOARD = " + json.dumps(storyboard_data, indent=1) + ";\n")
    print(f"wrote shots/storyboard_data.js ({len(sb_panels)} storyboard panels)")


if __name__ == "__main__":
    build_suite()
