import os, json, math
from PIL import Image
import numpy as np

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch"
PLAY_DIR = os.path.join(ROOT, "shots/play")
DATA_PATH = os.path.join(PLAY_DIR, "data.json")
CRASH_PATH = os.path.join(ROOT, "shots/arena/parts/kit3/release_v2/crash_lab_catalog.json")

data = json.load(open(DATA_PATH))
crash = json.load(open(CRASH_PATH))

# Map bolas 37 character keys to our 9 canonical 15-bone rigs in crash_lab_catalog.json
RIG_MAP = {
    "poet/red_black_sunglasses": "poet_tracksuit_31",
    "poet/black_tshirt": "poet_black_tshirt",
    "poet_soul/soul": "poet_black_tshirt",
    "ex/ex_jacket": "ex_jacket_back",
    "vintage_man/suit": "vintage_party_couple",
    "vintage_woman/gown": "woman_muse_costumes",
    "young_poet/pajamas_winter": "child_traveler_ghost",
    "young_poet/child_clothes": "child_traveler_ghost",
    "ghost_child/ghost_nightclothes": "child_traveler_ghost",
}

def map_char_to_rig(key):
    if key in RIG_MAP:
        return RIG_MAP[key]
    k = key.lower()
    if "poet" in k and "young" not in k:
        return "poet_tracksuit_31" if "red" in k or "track" in k else "poet_black_tshirt"
    if "young" in k or "child" in k or "ghost" in k:
        return "child_traveler_ghost"
    if "ex/" in k or "ex_" in k:
        return "ex_jacket_back"
    if "mother" in k or "parent" in k or "ancestor" in k or "family" in k:
        return "mother_ancestors_family"
    if "woman" in k or "girl" in k or "bride" in k or "muse" in k:
        return "woman_muse_costumes"
    if "vintage" in k or "suit" in k or "gentleman" in k:
        return "vintage_party_couple"
    return "dj_club_citizens"

# Analyze each drawing's bottom 28% silhouette to determine left/right foot positions, lead_leg (+1 or -1), and stride_cm
for ch in data["characters"]:
    h_cm = float(ch.get("height_cm", 170.0))
    cdir = os.path.join(PLAY_DIR, "assets", ch["dir"])
    ch["rig_id"] = map_char_to_rig(ch["key"])
    for idx, d in enumerate(ch["draws"]):
        img_path = os.path.join(cdir, d["f"])
        is_frag = (".hipcore/" in d.get("id", "")) or (d.get("body_px", 400) < 220 and d.get("h", 400) < 260 and h_cm > 140)
        d["is_fragment"] = bool(is_frag)
        d["hip_y_ratio"] = 0.54

        # Compute physical cm per pixel for this drawing
        body_px = max(120.0, float(d.get("body_px", d.get("h", 400))))
        cm_per_px = (0.70 * h_cm) / body_px

        lead_leg = 1 if (idx % 2 == 0) else -1
        stride_cm = max(14.0, float(d.get("spread", 20.0)) * 0.72)

        if os.path.exists(img_path):
            try:
                im = Image.open(img_path).convert("RGBA")
                arr = np.array(im)
                alpha = arr[:, :, 3]
                H, W = alpha.shape
                # Inspect bottom 22% (feet / ankles region)
                y_start = int(H * 0.78)
                sub = alpha[y_start:, :]
                ys, xs = np.where(sub > 40)
                if len(xs) > 20:
                    x_min, x_max = float(np.percentile(xs, 4)), float(np.percentile(xs, 96))
                    span_px = max(8.0, x_max - x_min)
                    measured_stride = span_px * cm_per_px
                    # Blend with spread metadata
                    if d.get("spread", 0) > 10:
                        stride_cm = float(np.clip(0.55 * measured_stride + 0.45 * (d["spread"] * 0.72), 18.0, 58.0))
                    else:
                        stride_cm = float(np.clip(measured_stride, 16.0, 42.0))

                    # Determine which foot is lower/planted vs reaching forward
                    ax = float(d.get("ax", W * 0.5))
                    left_mask = xs < ax
                    right_mask = xs >= ax
                    if np.any(left_mask) and np.any(right_mask):
                        y_left_max = float(np.percentile(ys[left_mask], 95))
                        y_right_max = float(np.percentile(ys[right_mask], 95))
                        x_left_ext = abs(ax - float(np.percentile(xs[left_mask], 10)))
                        x_right_ext = abs(float(np.percentile(xs[right_mask], 90)) - ax)
                        # Combine forward extension and vertical plant difference
                        asym = (x_right_ext - x_left_ext) + (y_right_max - y_left_max) * 1.5
                        lead_leg = 1 if asym >= 0 else -1
            except Exception as e:
                pass

        d["stride_cm"] = round(float(stride_cm), 1)
        d["lead_leg"] = int(lead_leg)

# Ensure that if a character has >= 2 walk/stride candidates, at least one has lead_leg=+1 and one has lead_leg=-1
for ch in data["characters"]:
    valid = [d for d in ch["draws"] if not d.get("is_fragment") and d["cls"] not in ("lie", "fall", "sit", "kneel", "crouch")]
    strides = [d for d in valid if d.get("spread", 0) >= 18 or d["cls"] == "walk"]
    if len(strides) >= 2:
        # Sort by view preference (prof/q3 first) and spread
        strides_sorted = sorted(strides, key=lambda x: (0 if x["view"] in ("prof", "q3") else 1, -x.get("spread", 0)))
        if all(s["lead_leg"] == strides_sorted[0]["lead_leg"] for s in strides_sorted):
            strides_sorted[1]["lead_leg"] = -strides_sorted[0]["lead_leg"]

json.dump(data, open(DATA_PATH, "w"), indent=2)
print(f"Enriched {len(data['characters'])} characters in shots/play/data.json with stride_cm, lead_leg, is_fragment, and rig_id!")
