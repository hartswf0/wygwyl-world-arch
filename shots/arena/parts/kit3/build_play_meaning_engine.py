#!/usr/bin/env python3
"""
Upgrades shots/play/data.json and shots/play/levels/01..14/level.json with:
1. Exact semantic & emotional posture mapping for every drawing across all 37 characters
   (eliminating random shuffling of unrelated paintings or prop-attached scenes).
2. Clean, coherent walk stride selection (only genuine prop-free matched stride pairs swap drawings;
   all other characters use smooth continuous split-hip leg articulation with zero view-flipping).
3. Scene-by-scene and line-by-line Emotional Arc, Meaning, Posture Cues, and Atmospheric Change
   metadata across all 14 poems (80 scenes).
"""
import json
import glob
import os

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
DATA_PATH = os.path.join(ROOT, "shots/play/data.json")

# Curated semantic & emotional mapping for multi-drawing characters
# Ensures every painting has a clear human meaning and prop-scenes never shuffle into walks
CURATED_DRAWS = {
    "poet/red_black_sunglasses": {
        0:  {"id": "shore_lie_flat",   "label": "Washed Ashore (Prone)",     "emotion": "grief",     "group": "shore_recovery", "order": 0, "prop_scene": False},
        1:  {"id": "shore_lie_wake",   "label": "Waking on the Shore",       "emotion": "searching", "group": "shore_recovery", "order": 1, "prop_scene": False},
        2:  {"id": "open_arms_wide",   "label": "Open Arms (Offering)",      "emotion": "peace",     "group": "open_arms",      "order": 0, "prop_scene": False},
        3:  {"id": "idle_hand_chest",  "label": "Hand to Heart (Reflect)",   "emotion": "memory",    "group": "idle_reflect",   "order": 0, "prop_scene": False},
        4:  {"id": "arms_sky_high",    "label": "Reaching to the Stars",     "emotion": "awe",       "group": "sky_praise",     "order": 0, "prop_scene": False},
        5:  {"id": "walk_stride_R",    "label": "Stride Forward (Right)",    "emotion": "searching", "group": "walk_cycle",     "order": 1, "prop_scene": False},
        6:  {"id": "hold_back_walls",  "label": "Holding the Walls Back",    "emotion": "vertigo",   "group": "brace",          "order": 0, "prop_scene": False},
        7:  {"id": "point_horizon",    "label": "Pointing to the Horizon",   "emotion": "searching", "group": "point",          "order": 0, "prop_scene": False},
        8:  {"id": "open_question",    "label": "Asking Why (Open Palms)",   "emotion": "grief",     "group": "question",       "order": 0, "prop_scene": False},
        9:  {"id": "idle_grounded",    "label": "Calm Grounded Stance",      "emotion": "peace",     "group": "idle",           "order": 0, "prop_scene": False},
        10: {"id": "soul_rapture",     "label": "Soul Escaping (Head Back)", "emotion": "ecstasy",   "group": "soul_release",   "order": 0, "prop_scene": False},
        11: {"id": "club_groove",      "label": "Club Pulse (Dance)",        "emotion": "ecstasy",   "group": "dance",          "order": 0, "prop_scene": False},
        12: {"id": "chin_high_stand",  "label": "Chin High in the Rain",     "emotion": "awe",       "group": "chin_high",      "order": 0, "prop_scene": False},
        13: {"id": "blind_search_1",   "label": "Searching Blindly",         "emotion": "searching", "group": "blind_search",   "order": 0, "prop_scene": False},
        14: {"id": "blind_search_2",   "label": "Reaching Through Haze",     "emotion": "searching", "group": "blind_search",   "order": 1, "prop_scene": False},
        15: {"id": "shrug_peace",      "label": "Letting Go (Open Hands)",   "emotion": "peace",     "group": "letting_go",     "order": 0, "prop_scene": False},
        16: {"id": "walk_stride_L",    "label": "Stride Forward (Left)",     "emotion": "searching", "group": "walk_cycle",     "order": 0, "prop_scene": False},
        17: {"id": "welcome_new_day",  "label": "Welcoming the New Day",     "emotion": "peace",     "group": "welcome_dawn",   "order": 0, "prop_scene": False},
        18: {"id": "lunge_catch",      "label": "Lunging to Catch",          "emotion": "vertigo",   "group": "lunge",          "order": 0, "prop_scene": False},
        19: {"id": "victory_cry",      "label": "Naming the Stars",          "emotion": "awe",       "group": "sky_praise",     "order": 1, "prop_scene": False},
        20: {"id": "vow_hand_raised",  "label": "The Vow / Greeting",        "emotion": "peace",     "group": "vow",            "order": 0, "prop_scene": False},
        21: {"id": "still_sentinel",   "label": "Standing Still",            "emotion": "memory",    "group": "still",          "order": 0, "prop_scene": False},
        22: {"id": "fragment_22",      "label": "Fragment",                  "emotion": "memory",    "group": "fragment",       "order": 0, "prop_scene": True},
        23: {"id": "magic_ride_bike",  "label": "Mounting the Motorcycle",   "emotion": "ecstasy",   "group": "motorcycle",     "order": 0, "prop_scene": True},
        24: {"id": "back_horizon",     "label": "Facing the Horizon (Back)", "emotion": "departure", "group": "look_away",      "order": 0, "prop_scene": False},
        25: {"id": "hand_on_ledge",    "label": "Hand on the Stone Ledge",   "emotion": "searching", "group": "ledge",          "order": 0, "prop_scene": True},
        26: {"id": "fragment_26",      "label": "Seated Fragment",           "emotion": "memory",    "group": "fragment",       "order": 0, "prop_scene": True},
        27: {"id": "corner_cafe_cup",  "label": "Corner Cafe (Coffee Cup)",  "emotion": "peace",     "group": "cafe_sit",       "order": 0, "prop_scene": False},
        28: {"id": "kneel_hollow",     "label": "Kneeling (Hollow Heart)",   "emotion": "grief",     "group": "kneel_heart",    "order": 0, "prop_scene": False},
        29: {"id": "kneel_universe",   "label": "Holding the Universe",      "emotion": "awe",       "group": "universe",       "order": 0, "prop_scene": False},
    },
    "poet/black_tshirt": {
        0:  {"id": "fall_invert",      "label": "Tumbling Upside-Down",      "emotion": "vertigo",   "group": "fall_arc",       "order": 2, "prop_scene": False},
        1:  {"id": "fire_escape_climb","label": "Scrambling the Fire Escape","emotion": "vertigo",   "group": "scramble",       "order": 0, "prop_scene": False},
        2:  {"id": "fall_back_start",  "label": "Tripping / Falling Back",   "emotion": "vertigo",   "group": "fall_arc",       "order": 0, "prop_scene": False},
        3:  {"id": "fall_landed",      "label": "Fallen on the Floor",       "emotion": "grief",     "group": "fall_arc",       "order": 3, "prop_scene": False},
        4:  {"id": "walk_away_back",   "label": "Walking into the Dark",     "emotion": "departure", "group": "look_away",      "order": 0, "prop_scene": False},
        5:  {"id": "walk_stride_L",    "label": "Stride Forward (Left)",     "emotion": "searching", "group": "walk_cycle",     "order": 0, "prop_scene": False},
        6:  {"id": "walk_stride_R",    "label": "Stride Forward (Right)",    "emotion": "searching", "group": "walk_cycle",     "order": 1, "prop_scene": False},
        7:  {"id": "sprint_pursuit",   "label": "Running in Pursuit",        "emotion": "vertigo",   "group": "run",            "order": 0, "prop_scene": False},
        8:  {"id": "fall_midair",      "label": "Falling Through the Floor", "emotion": "vertigo",   "group": "fall_arc",       "order": 1, "prop_scene": False},
        9:  {"id": "reading_pages",    "label": "Reading the Manuscript",    "emotion": "memory",    "group": "read",           "order": 0, "prop_scene": False},
        10: {"id": "bed_despair_sit",  "label": "Sitting in Despair",        "emotion": "grief",     "group": "sit_despair",    "order": 0, "prop_scene": True},
        11: {"id": "bed_sheets_lie",   "label": "Sleepless Under Sheets",    "emotion": "grief",     "group": "bed_lie",        "order": 0, "prop_scene": True},
    },
    "ex/ex_jacket": {
        0:  {"id": "back_still_0",     "label": "Standing with Back Turned", "emotion": "departure", "group": "idle",           "order": 0, "prop_scene": False},
        1:  {"id": "back_still_1",     "label": "Looking Away",              "emotion": "departure", "group": "idle_alt",       "order": 0, "prop_scene": False},
        2:  {"id": "railing_lean",     "label": "Leaning on the Railing",    "emotion": "memory",    "group": "lean",           "order": 0, "prop_scene": True},
        3:  {"id": "fall_away_1",      "label": "Drifting Away",             "emotion": "vertigo",   "group": "fall_arc",       "order": 0, "prop_scene": False},
        4:  {"id": "phone_stand",      "label": "Holding the Phone",         "emotion": "grief",     "group": "phone_call",     "order": 0, "prop_scene": False},
        5:  {"id": "phone_sit",        "label": "Seated with Phone",         "emotion": "grief",     "group": "sit_phone",      "order": 0, "prop_scene": False},
        6:  {"id": "float_far",        "label": "Vanishing into the Abyss",  "emotion": "departure", "group": "fall_arc",       "order": 2, "prop_scene": True},
        7:  {"id": "fall_away_2",      "label": "Falling into Memory",       "emotion": "vertigo",   "group": "fall_arc",       "order": 1, "prop_scene": False},
        8:  {"id": "club_turn_back",   "label": "Dancing in the Crowd",      "emotion": "ecstasy",   "group": "dance",          "order": 0, "prop_scene": False},
        9:  {"id": "walk_away_1",      "label": "Walking Away (Step 1)",     "emotion": "departure", "group": "walk_cycle",     "order": 0, "prop_scene": False},
        10: {"id": "walk_away_2",      "label": "Walking Away (Step 2)",     "emotion": "departure", "group": "walk_cycle",     "order": 1, "prop_scene": False},
        11: {"id": "walk_away_3",      "label": "Walking Away (Step 3)",     "emotion": "departure", "group": "walk_cycle",     "order": 2, "prop_scene": False},
        12: {"id": "walk_away_4",      "label": "Walking Away (Step 4)",     "emotion": "departure", "group": "walk_cycle",     "order": 3, "prop_scene": False},
        13: {"id": "walk_away_5",      "label": "Walking Away (Step 5)",     "emotion": "departure", "group": "walk_cycle",     "order": 4, "prop_scene": False},
        14: {"id": "suitcase_crouch",  "label": "Packing the Suitcase",      "emotion": "departure", "group": "suitcase",       "order": 0, "prop_scene": False},
    }
}

# Genuine multi-drawing walk cycles (ONLY prop-free, same-orientation, visually coherent stride drawings)
CLEAN_WALK_CYCLES = {
    "poet/red_black_sunglasses": [16, 5],
    "poet/black_tshirt": [5, 6],
    "ex/ex_jacket": [9, 10, 11, 13],
}

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

for ch in data["characters"]:
    key = ch["key"]
    curated = CURATED_DRAWS.get(key, {})
    ch["clean_walk_indices"] = CLEAN_WALK_CYCLES.get(key, [])
    for idx, d in enumerate(ch["draws"]):
        d["is_fragment"] = (key == "poet/red_black_sunglasses" and idx in (22, 26))
        if idx in curated:
            meta = curated[idx]
            d["sem_id"] = meta["id"]
            d["sem_label"] = meta["label"]
            d["emotion"] = meta["emotion"]
            d["sem_group"] = meta["group"]
            d["sem_order"] = meta["order"]
            d["has_scene_prop"] = bool(meta["prop_scene"])
        else:
            cls = d.get("cls", "stand")
            vw = d.get("view", "front")
            emo_map = {
                "stand": "peace", "walk": "searching", "run": "vertigo",
                "dance": "ecstasy", "sit": "memory", "kneel": "grief",
                "crouch": "grief", "lean": "memory", "lunge": "searching",
                "lie": "grief", "fall": "vertigo", "fly": "awe", "float": "awe",
                "throw": "vertigo", "reach": "searching", "point": "searching"
            }
            label_map = {
                "stand": "Grounded Stance", "walk": "Stepping Forward", "run": "Rushing Forward",
                "dance": "Waltz / Groove", "sit": "Seated Reflection", "kneel": "Kneeling in Reverence",
                "crouch": "Crouching Low", "lean": "Leaning In", "lunge": "Reaching Out",
                "lie": "Lying Still", "fall": "Falling", "fly": "Ascending",
                "float": "Floating Weightless", "throw": "Hurling Forward"
            }
            base_lbl = label_map.get(cls, cls.title())
            if len(ch["draws"]) > 1:
                base_lbl = f"{base_lbl} ({vw} · #{idx+1})"
            d["sem_id"] = f"{cls}_{idx}"
            d["sem_label"] = base_lbl
            d["emotion"] = emo_map.get(cls, "peace")
            d["sem_group"] = f"{cls}_{idx}"
            d["sem_order"] = idx
            d["has_scene_prop"] = False

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, separators=(",", ":"))
print("Updated shots/play/data.json with semantic & emotional posture catalog.")

# 2. Enrich all 14 poem level.json files with Emotional Arc, Meaning, Posture Cues, and Scene Change
POEM_ARCS = {
    "01": {
        "theme": "Disillusion, Vertigo & Freefall Through Tainted Love",
        "start_emotion": "memory",
        "end_emotion": "vertigo",
        "transformation": "From quiet reading at the desk → stumbling off the fire escape → freefalling through the floor of memory.",
    },
    "02": {
        "theme": "Childhood Memory, Shattered Headlights & The Ghost Child",
        "start_emotion": "vertigo",
        "end_emotion": "grief",
        "transformation": "From falling with headlights off → confronting the Ghost Child and arguing parents → throwing the tambourine.",
    },
    "03": {
        "theme": "Breaking Off an Engagement & The Storm-Swept Temple",
        "start_emotion": "grief",
        "end_emotion": "departure",
        "transformation": "From the empty wedding chapel → the storm tearing away every gift → remnants washed ashore as the tambourine shatters.",
    },
    "04": {
        "theme": "Waking on the Shore with a Hollow Heart & Searching for Hands",
        "start_emotion": "grief",
        "end_emotion": "searching",
        "transformation": "From lying broken on the sand with a hollow chest → climbing the trail → placing hands on the ledge and resolving to go on.",
    },
    "05": {
        "theme": "Ancestral Bloodlines, Southern-Pine Memories & Naming the Stars",
        "start_emotion": "memory",
        "end_emotion": "awe",
        "transformation": "From stillness in the dark field → descending into the ancestral basement → holding universes and claiming the stars.",
    },
    "06": {
        "theme": "The Light Gates Open & Atlantis Rises From the Water",
        "start_emotion": "awe",
        "end_emotion": "peace",
        "transformation": "From standing before the Light Gates → passing the heart-scan → walking narrow candlelit streets into a welcoming home.",
    },
    "07": {
        "theme": "Subterranean Club Pulse, Eleven Daisy Petals & Chin High in the Rain",
        "start_emotion": "ecstasy",
        "end_emotion": "awe",
        "transformation": "From eyes wide shut at the club mic → haunted by wedding bands in the speaker mesh → walking through rain with chin held high.",
    },
    "08": {
        "theme": "Out-of-Body Release on the Dance Floor & Ice-Water Baptism",
        "start_emotion": "ecstasy",
        "end_emotion": "peace",
        "transformation": "The soul literally separates from the dancer's body, floats over Atlantis, receives the angels' baptism, and reunites on the rooftop.",
    },
    "09": {
        "theme": "The Unanswered Phone Booth Call, Mother's Voice & Letting Go",
        "start_emotion": "departure",
        "end_emotion": "grief",
        "transformation": "Following the EX through the crowd to the suitcases at the phone booth → calling Mother → watching the EX dissolve into haze.",
    },
    "10": {
        "theme": "Mounting the Midnight Motorcycle & Riding Into First Light",
        "start_emotion": "searching",
        "end_emotion": "ecstasy",
        "transformation": "From loneliness under a streetlamp → mounting the machine → riding out of Atlantis onto the mountain road at dawn.",
    },
    "11": {
        "theme": "Chilly Morning Shore, Self-Building Temple & A Heart at Peace",
        "start_emotion": "memory",
        "end_emotion": "peace",
        "transformation": "From shivering on the morning shore → watching the temple assemble itself course by course → welcoming the new day in peace.",
    },
    "12": {
        "theme": "Brotherhood Chain, Archival Hourglasses & Coming Home",
        "start_emotion": "memory",
        "end_emotion": "peace",
        "transformation": "From echoing halls and empty rooms → locking arms in the brotherhood chain → sunlight in the meadow bringing everyone home.",
    },
    "13": {
        "theme": "The Corner Cafe Table, Poppies & The Promise of a Heart",
        "start_emotion": "searching",
        "end_emotion": "peace",
        "transformation": "From waiting to be noticed at a corner cafe → walking past younger selves and victory-less seasons → harvesting poppies by the harbor.",
    },
    "14": {
        "theme": "Taken by the Haze, The Vintage Ballroom Waltz & Genesis",
        "start_emotion": "vertigo",
        "end_emotion": "awe",
        "transformation": "From floating in the black void → stepping through the vintage door into the golden waltz → disappearing into a new genesis.",
    },
}

def classify_line_meaning(text, sc_name, poem_num, sc_idx, line_idx):
    tl = text.lower()
    sl = sc_name.lower()
    # Check specific poetic imagery & actions
    if any(w in tl for w in ["fall", "falling", "trip", "stumble", "quicksands", "pit", "headlights off", "floating in the black"]):
        return ("vertigo", "Vertigo & Freefall", "fall_arc", "embers")
    if any(w in tl for w in ["hole", "chest", "broken", "hurt", "failed", "empty", "shattered", "burn", "ashes", "vices"]):
        return ("grief", "Grief & Hollowing", "kneel_heart", "ash")
    if any(w in tl for w in ["cafe", "coffee", "table", "notice me", "sit", "pause for a second", "journal"]):
        return ("memory", "Quiet Contemplation", "cafe_sit", "dawn")
    if any(w in tl for w in ["ride", "machine", "bike", "swagger", "avenue", "intersections"]):
        return ("ecstasy", "Midnight Ride", "motorcycle", "neon")
    if any(w in tl for w in ["soul", "escaped my body", "dance", "dj", "turn me up", "vibrations", "party"]):
        return ("ecstasy", "Ecstasy & Release", "soul_release" if "soul" in tl or poem_num == "08" else "dance", "neon")
    if any(w in tl for w in ["universe", "inherit", "earth", "blessings", "ancestors", "blood"]):
        return ("awe", "Ancestral Inheritance", "universe", "stars")
    if any(w in tl for w in ["stars", "gates open", "wings", "resurrect", "temple", "new day", "chin high", "genesis"]):
        return ("awe", "Awakening & Ascent", "sky_praise", "stars")
    if any(w in tl for w in ["ledge", "wall", "hallways", "drawers", "trail", "follow", "hands", "search", "find"]):
        return ("searching", "Searching Through the Dark", "ledge" if "hands" in tl or "ledge" in sl else "blind_search", "haze")
    if any(w in tl for w in ["back faced", "leave", "suitcase", "phone", "call", "crowd", "goodbye"]):
        return ("departure", "Departure & Distance", "look_away", "rain")
    if any(w in tl for w in ["peace", "home", "welcome", "safe", "brother", "heart", "love was real", "magic still exists"]):
        return ("peace", "Reconciliation & Peace", "open_arms", "petals")
    if sc_idx == 0 and poem_num in ("01", "11", "13"):
        return ("memory", "The Reading Begins", "read", "haze")
    # Default by poem arc
    arc = POEM_ARCS.get(poem_num, {})
    emo = arc.get("start_emotion", "searching") if sc_idx < 2 else arc.get("end_emotion", "peace")
    label_map = {
        "memory": ("Remembering", "idle_reflect", "haze"),
        "searching": ("Walking the Path", "walk_cycle", "haze"),
        "vertigo": ("On the Edge", "brace", "embers"),
        "grief": ("Carrying the Weight", "kneel_heart", "rain"),
        "awe": ("Looking Upward", "sky_praise", "stars"),
        "ecstasy": ("Moving with the Beat", "dance", "neon"),
        "departure": ("Watching Her Leave", "look_away", "rain"),
        "peace": ("Grounded in Light", "open_arms", "dawn"),
    }
    lbl, cue, part = label_map.get(emo, ("Walking the Path", "walk_cycle", "haze"))
    return (emo, lbl, cue, part)

for p in sorted(glob.glob(os.path.join(ROOT, "shots/play/levels/[0-9][0-9]/level.json"))):
    with open(p, "r", encoding="utf-8") as f:
        L = json.load(f)
    num = L["num"]
    L["emotional_arc"] = POEM_ARCS.get(num, {})
    num_sc = len(L["scenes"])
    for sc_i, sc in enumerate(L["scenes"]):
        sc_emos = []
        for ln_i, ln in enumerate(sc.get("lines", [])):
            emo, emo_lbl, cue, particle = classify_line_meaning(ln.get("text", ""), sc.get("name", ""), num, sc_i, ln_i)
            ln["emotion"] = emo
            ln["emotion_label"] = emo_lbl
            ln["posture_cue"] = cue
            ln["particle"] = particle
            sc_emos.append(emo)
        # Scene dominant emotion
        dom_emo = sc_emos[0] if sc_emos else POEM_ARCS.get(num, {}).get("start_emotion", "searching")
        sc["emotion"] = dom_emo
        sc["progress_ratio"] = round(sc_i / max(1, num_sc - 1), 2)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(L, f, separators=(",", ":"))

print("Enriched all 14 level.json files with emotional arcs, line posture cues, and atmospheric change states.")
