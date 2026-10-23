#!/usr/bin/env python3
"""
1. Detects and fixes any sideways (90-deg horizontal) head cutouts in swapper_bank & expressive_heads.
2. Classifies every head by true view_dir ('front', 'threequarter', 'profile', 'back'),
   head_type ('complete_painted', 'blank_canvas', 'slot_canvas'), compatible_torso_views, and skin_rgb.
3. Builds grommet-free, border-eroded organic facial feature assets in
   shots/arena/parts/kit3/v2/seamless_faces/ and populates `seamless_face_pool` in crash_lab_catalog.json.
"""

import json
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps
import numpy as np

ROOT = Path(__file__).resolve().parents[3]  # shots/
CAT_PATH = ROOT / "arena/parts/kit3/release_v2/crash_lab_catalog.json"
RC_PATH = ROOT / "arena/parts/kit3/release_v2/release_catalog.json"
OUT_DIR = ROOT / "arena/parts/kit3/v2/seamless_faces"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def analyze_front_blank_head(im: Image.Image):
    arr = np.array(im.convert("RGBA"), dtype=np.float32)
    h, w, _ = arr.shape
    rgb = arr[:, :, :3]
    a = arr[:, :, 3]
    mask_im = Image.fromarray(a.astype(np.uint8), mode="L")
    for _ in range(max(2, int(min(w, h) * 0.04))):
        mask_im = mask_im.filter(ImageFilter.MinFilter(3))
    inner_a = np.array(mask_im, dtype=np.float32)
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    yy, xx = np.mgrid[0:h, 0:w]
    is_skin = (inner_a > 200) & (lum > 95) & (lum < 235) & (yy > h * 0.16) & (yy < h * 0.77) & (xx > w * 0.18) & (xx < w * 0.82)
    if np.sum(is_skin) < 150:
        is_skin = (inner_a > 200) & (lum > 75) & (yy > h * 0.16) & (yy < h * 0.77)
    ys, xs = np.where(is_skin)
    y_top = float(np.percentile(ys, 5)) / h
    y_chin = float(np.percentile(ys, 95)) / h
    x_left = float(np.percentile(xs, 5)) / w
    x_right = float(np.percentile(xs, 95)) / w
    # Check dark beard pixels below y_chin * 0.88 and above neck (0.78*h)
    beard_band = (inner_a > 200) & (lum < 75) & (yy > h * (y_chin - 0.04)) & (yy < h * 0.79) & (xx > w * 0.28) & (xx < w * 0.72)
    has_beard = bool(np.sum(beard_band) > (w * h * 0.012))
    return {
        "face_cx": round((x_left + x_right) * 0.5, 4),
        "face_w": round(x_right - x_left, 4),
        "face_top": round(y_top, 4),
        "face_chin": round(y_chin, 4),
        "face_h": round(y_chin - y_top, 4),
        "has_beard": has_beard,
        "skin_rgb": [round(float(x), 1) for x in np.median(rgb[is_skin], axis=0)]
    }


def normalize_and_analyze_profile_head(im: Image.Image):
    im = im.convert("RGBA")
    arr = np.array(im, dtype=np.float32)
    h, w, _ = arr.shape
    rgb = arr[:, :, :3]
    a = arr[:, :, 3]
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    yy, xx = np.mgrid[0:h, 0:w]
    band = (a > 200) & (lum > 95) & (lum < 235) & (yy > h * 0.25) & (yy < h * 0.68)
    left_skin = np.sum(band & (xx < w * 0.45))
    right_skin = np.sum(band & (xx > w * 0.55))
    mirrored = False
    if left_skin > right_skin * 1.25:
        im = ImageOps.mirror(im)
        arr = np.array(im, dtype=np.float32)
        mirrored = True
    rgb = arr[:, :, :3]
    a = arr[:, :, 3]
    mask_im = Image.fromarray(a.astype(np.uint8), mode="L")
    for _ in range(max(2, int(min(w, h) * 0.035))):
        mask_im = mask_im.filter(ImageFilter.MinFilter(3))
    inner_a = np.array(mask_im, dtype=np.float32)
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    is_skin = (inner_a > 200) & (lum > 90) & (lum < 235) & (yy > h * 0.16) & (yy < h * 0.77) & (xx > w * 0.42)
    if np.sum(is_skin) < 100:
        is_skin = (inner_a > 200) & (lum > 70) & (yy > h * 0.16) & (yy < h * 0.77) & (xx > w * 0.40)
    ys, xs = np.where(is_skin)
    y_top = float(np.percentile(ys, 5)) / h
    y_chin = float(np.percentile(ys, 95)) / h
    x_right = float(np.percentile(xs, 99)) / w
    x_left = float(np.percentile(xs, 10)) / w
    beard_band = (inner_a > 200) & (lum < 75) & (yy > h * 0.52) & (yy < h * 0.79) & (xx > w * 0.48)
    has_beard = bool(np.sum(beard_band) > (w * h * 0.015))
    return im, mirrored, {
        "face_x_right": round(x_right, 4),
        "face_w": round(x_right - x_left, 4),
        "face_top": round(y_top, 4),
        "face_chin": round(y_chin, 4),
        "face_h": round(y_chin - y_top, 4),
        "has_beard": has_beard,
        "skin_rgb": [round(float(x), 1) for x in np.median(rgb[is_skin], axis=0)]
    }


def make_clean_feathered_feature(im: Image.Image, view="front", crop_top=0.0, crop_left=0.0, erode_ratio=0.06, blur_ratio=0.045):
    im = im.convert("RGBA")
    w0, h0 = im.size
    x0 = int(w0 * crop_left)
    y0 = int(h0 * crop_top)
    y1 = int(h0 * (0.95 if view == "profile_R" else 0.98))
    x1 = int(w0 * (0.98 if view != "profile_R" else 1.0))
    im = im.crop((x0, y0, x1, y1))
    arr = np.array(im, dtype=np.float32)
    h, w, _ = arr.shape
    alpha = arr[:, :, 3] / 255.0

    erode_px = max(2, int(min(w, h) * erode_ratio))
    blur_px = max(2, int(min(w, h) * blur_ratio))
    mask_im = Image.fromarray((alpha * 255).astype(np.uint8), mode="L")
    for _ in range(max(1, erode_px // 2)):
        mask_im = mask_im.filter(ImageFilter.MinFilter(3))
    mask_im = mask_im.filter(ImageFilter.GaussianBlur(radius=blur_px))
    eroded_a = np.array(mask_im, dtype=np.float32) / 255.0

    yy, xx = np.mgrid[0:h, 0:w]
    ny = (yy - h * 0.5) / (h * 0.44)
    if view == "profile_R":
        nx = np.where(xx < w * 0.65, (xx - w * 0.65) / (w * 0.58), (xx - w * 0.65) / (w * 0.35))
    else:
        nx = (xx - w * 0.5) / (w * 0.45)
    r2 = nx * nx + ny * ny
    ell = np.clip(1.0 - np.power(np.clip(r2, 0, 1.5), 1.85), 0.0, 1.0)
    new_a = eroded_a * ell

    # Measure median skin midtone RGB & check if feature contains dark beard
    rgb = arr[:, :, :3]
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    mid_mask = (new_a > 0.2) & (lum > 75) & (lum < 225)
    if np.any(mid_mask):
        skin_rgb = [round(float(x), 1) for x in np.median(rgb[mid_mask], axis=0)]
    else:
        skin_rgb = [178.0, 124.0, 78.0]
    dark_bottom = (new_a > 0.25) & (lum < 65) & (yy > h * 0.55)
    is_bearded = bool(np.sum(dark_bottom) > (w * h * 0.08))

    arr[:, :, 3] = np.clip(new_a * 255.0, 0, 255)
    out_im = Image.fromarray(arr.astype(np.uint8), mode="RGBA")
    return out_im, skin_rgb, is_bearded


def classify_head_orientation_and_type(im: Image.Image, file_str: str, cur_view: str):
    """Detects sideways-cropped (90-deg) heads, true gaze direction, and painted vs blank face."""
    arr = np.array(im.convert("RGBA"), dtype=np.float32)
    h, w, _ = arr.shape
    fl = file_str.lower()

    # Check if literally rotated 90 degrees (like bola.head.*.png 226x190)
    is_sideways_crop = (w > h * 1.12) and ("bola.head" in fl or "dummy" in fl)

    # Determine true view direction
    view_dir = "front"
    if "threequarter_back" in fl or "3q_back" in fl:
        view_dir = "back"
    elif "back" in fl:
        view_dir = "back"
    elif "threequarter" in fl or "3q" in fl:
        view_dir = "threequarter"
    elif "profile" in fl or ".side." in fl:
        view_dir = "profile"
    elif any(k in fl for k in ["head_01", "head_06", "head_11", "head_16", "head_21"]):
        view_dir = "front"
    elif any(k in fl for k in ["head_02", "head_07", "head_12", "head_17", "head_22"]):
        view_dir = "threequarter"
    elif any(k in fl for k in ["head_03", "head_08", "head_13", "head_18", "head_23"]):
        view_dir = "profile"
    elif any(k in fl for k in ["head_04", "head_05", "head_09", "head_10", "head_14", "head_15", "head_19", "head_20", "head_24"]):
        view_dir = "back"
    elif cur_view in ("front", "threequarter", "profile", "back"):
        view_dir = cur_view

    # Also check if head is actually back-of-head by checking dark hair coverage in center face
    rgb = arr[:, :, :3]
    a = arr[:, :, 3]
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    center_patch = a[int(h*0.25):int(h*0.62), int(w*0.28):int(w*0.72)] > 200
    center_lum = lum[int(h*0.25):int(h*0.62), int(w*0.28):int(w*0.72)]
    if np.sum(center_patch) > 100:
        dark_frac = float(np.sum(center_patch & (center_lum < 72))) / float(np.sum(center_patch))
        if dark_frac > 0.76 and "dj" not in fl and "bola" not in fl:
            view_dir = "back"

    # Determine head_type
    if view_dir == "back":
        head_type = "back_of_head"
    elif "blank" in fl or any(k in fl for k in ["mother_head_", "father_head_", "party_head_", "ancestors_head_", "elder_head_"]):
        head_type = "blank_canvas"
    elif "body.front.head" in fl or "body.threequarter.head" in fl or "body.profile.head" in fl:
        # Check if it's weave/cast/man/library/head (which is complete painted)
        if "weave/cast/man" in fl:
            head_type = "complete_painted"
        else:
            head_type = "slot_canvas"
    else:
        head_type = "complete_painted"

    compat_map = {
        "front": ["front", "threequarter"],
        "threequarter": ["front", "threequarter", "profile"],
        "profile": ["profile", "threequarter"],
        "back": ["back", "threequarter"]
    }
    return is_sideways_crop, view_dir, head_type, compat_map.get(view_dir, ["front"])


def main():
    cat = json.loads(CAT_PATH.read_text())
    rc = json.loads(RC_PATH.read_text())
    sheet_map = {}
    for s in rc["sheets"]:
        nm = s.get("name", "") or s.get("id", "") or Path(s.get("file", "")).stem
        sheet_map[nm] = s

    # 1. Fix sideways heads in swapper_bank['heads'] and classify all heads
    fixed_sideways = 0
    clean_sb_heads = []
    for h in cat["swapper_bank"]["heads"]:
        p = ROOT / h["file"]
        if not p.exists():
            continue
        im = Image.open(p).convert("RGBA")
        is_sw, view_dir, head_type, compat_views = classify_head_orientation_and_type(im, h["file"], h.get("view", "front"))
        if is_sw:
            # Rotate -90 deg CW (270 CCW) so neck is at bottom and crown is at top!
            up_im = im.rotate(-90, expand=True)
            up_rel = h["file"].replace(".png", ".upright.png")
            up_im.save(ROOT / up_rel)
            h["file"] = up_rel
            h["width"], h["height"] = up_im.size
            h["pivot_A"] = [0.50, 0.88]
            h["socket_B"] = [0.50, 0.08]
            fixed_sideways += 1
        h["view"] = view_dir
        h["view_dir"] = view_dir
        h["head_type"] = head_type
        h["is_sideways_profile"] = (view_dir == "profile")
        h["compatible_torso_views"] = compat_views
        clean_sb_heads.append(h)
    cat["swapper_bank"]["heads"] = clean_sb_heads

    # 2. Purify and classify expressive_heads in face_and_body_gene_pool
    pool = cat.get("face_and_body_gene_pool", {})
    raw_exp = pool.get("expressive_heads", [])
    clean_exp = []
    # Excluded indices from our visual audit of scratch_all_147_heads.png:
    # 96..98 (hands), 99, 105, 106 (full bodies), 134..141 (eyes, mouths, gloved hands)
    bad_substrings = [
        "father_head_06", "father_head_07", "father_head_08", "father_head_09",
        "mother_head_06", "mother_head_07",
        "ghost_head_06", "ghost_head_07", "ghost_head_14", "ghost_head_15",
        "ghost_head_16", "ghost_head_17", "ghost_head_18", "ghost_head_19"
    ]
    for h in raw_exp:
        fl = h["file"]
        if any(bs in fl for bs in bad_substrings):
            continue
        p = ROOT / fl
        if not p.exists():
            continue
        im = Image.open(p).convert("RGBA")
        is_sw, view_dir, head_type, compat_views = classify_head_orientation_and_type(im, fl, h.get("view", "front"))
        if is_sw:
            up_rel = fl.replace(".png", ".upright.png")
            if not (ROOT / up_rel).exists():
                im.rotate(-90, expand=True).save(ROOT / up_rel)
            h["file"] = up_rel
            im = Image.open(ROOT / up_rel).convert("RGBA")
            fixed_sideways += 1
        w0, h0 = im.size
        # Reject any wide non-head item
        if w0 > h0 * 1.15:
            continue
        h["w"], h["h"] = w0, h0
        h["view"] = view_dir
        h["view_dir"] = view_dir
        h["head_type"] = head_type
        h["is_sideways_profile"] = (view_dir == "profile")
        h["compatible_torso_views"] = compat_views
        clean_exp.append(h)
    pool["expressive_heads"] = clean_exp

    # Also filter vinyl record & empty frame out of headgear
    if "headgear" in pool:
        pool["headgear"] = [
            g for g in pool["headgear"]
            if not any(bad in g["file"] for bad in ["dj_acc_11", "dj_acc_13"])
        ]

    # 3. Build `seamless_face_pool` with calibrated Front & Profile Blank Heads + Pre-Feathered Organic Features
    front_blank_specs = [
        ("poet_front", "Poet", "arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.face.front/poet.red_black_sunglasses.face.front__p01.png"),
        ("young_poet_front", "Young Poet", "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.face.front/young_poet.child_clothes.face.front__p01.png"),
        ("mother_afro_front", "Mother", "arena/parts/body_lab/heads/the_mother_teal_dress/mother_head_01.png"),
        ("club_dress_front", "Woman Muse", "arena/parts/kit3/release_v2/cuts/08.cast.club_dress.faces-hands/08.cast.club_dress.faces-hands__p01.png"),
        ("club_jacket_front", "Club Jacket", "arena/parts/kit3/release_v2/cuts/08.cast.club_jacket.faces-hands/08.cast.club_jacket.faces-hands__p01.png"),
        ("club_shirt_front", "Club Shirt", "arena/parts/kit3/release_v2/cuts/08.cast.club_shirt.faces-hands/08.cast.club_shirt.faces-hands__p01.png"),
        ("angel_front", "Angel", "arena/parts/kit3/release_v2/cuts/08.cast.angel.faces-hands/08.cast.angel.faces-hands__p01.png"),
        ("father_cap_front", "Father", "arena/parts/body_lab/heads/the_father_long_coat/father_head_01.png"),
        ("vintage_woman_front", "Vintage Woman", "arena/parts/body_lab/heads/party_guests/party_head_01.png"),
        ("ghost_child_front", "Ghost Child", "arena/parts/kit3/release_v2/cuts/ghost_child.02.faces-hands/ghost_child.02.faces-hands__p01.png"),
        ("poet_12_front", "Poet Reunion", "arena/parts/kit3/release_v2/cuts/poet.12.faces/poet.12.faces__p01.png"),
        ("ancestor_crown_front", "Ancestor", "arena/parts/body_lab/heads/atlantis_ancestors/ancestors_head_15.png"),
    ]
    front_heads = []
    for hid, label, rel in front_blank_specs:
        p = ROOT / rel
        if not p.exists():
            continue
        im = Image.open(p).convert("RGBA")
        info = analyze_front_blank_head(im)
        front_heads.append({
            "id": hid,
            "name": label,
            "view": "front",
            "file": rel,
            "w": im.width,
            "h": im.height,
            **info
        })

    profile_blank_specs = [
        ("poet_profile", "Poet Profile", "arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.face.profile/poet.red_black_sunglasses.face.profile__p01.png"),
        ("young_poet_profile", "Young Poet Profile", "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.face.profile/young_poet.child_clothes.face.profile__p01.png"),
        ("club_dress_profile", "Woman Profile", "arena/parts/kit3/release_v2/cuts/08.cast.club_dress.faces-hands/08.cast.club_dress.faces-hands__p03.png"),
        ("club_jacket_profile", "Club Jacket Profile", "arena/parts/kit3/release_v2/cuts/08.cast.club_jacket.faces-hands/08.cast.club_jacket.faces-hands__p03.png"),
        ("club_shirt_profile", "Club Shirt Profile", "arena/parts/kit3/release_v2/cuts/08.cast.club_shirt.faces-hands/08.cast.club_shirt.faces-hands__p03.png"),
        ("angel_profile", "Angel Profile", "arena/parts/kit3/release_v2/cuts/08.cast.angel.faces-hands/08.cast.angel.faces-hands__p03.png"),
        ("ghost_child_profile", "Ghost Child Profile", "arena/parts/kit3/release_v2/cuts/ghost_child.02.faces-hands/ghost_child.02.faces-hands__p02.png"),
        ("father_cap_profile", "Father Profile", "arena/parts/body_lab/heads/the_father_long_coat/father_head_03.png"),
    ]
    profile_heads = []
    for hid, label, rel in profile_blank_specs:
        p = ROOT / rel
        if not p.exists():
            continue
        im, mirrored, info = normalize_and_analyze_profile_head(Image.open(p))
        if mirrored:
            out_rel = f"arena/parts/kit3/v2/seamless_faces/{hid}_R.png"
            im.save(ROOT / out_rel)
            rel = out_rel
        profile_heads.append({
            "id": hid,
            "name": label,
            "view": "profile_R",
            "file": rel,
            "w": im.width,
            "h": im.height,
            **info
        })

    # Collect and pre-feather Front Brows, Front Eyes, Front Noses, Front Mouths
    front_brows = []
    front_eyes = []
    front_noses = []
    front_mouths = []

    def add_feathered(src_rel, fid, group_name, kind, view="front", crop_top=0.0, crop_left=0.0):
        p = ROOT / src_rel
        if not p.exists():
            return None
        im = Image.open(p)
        f_im, skin_rgb, is_bearded = make_clean_feathered_feature(im, view=view, crop_top=crop_top, crop_left=crop_left)
        out_name = f"{kind}_{view}_{fid}.png"
        out_rel = f"arena/parts/kit3/v2/seamless_faces/{out_name}"
        f_im.save(ROOT / out_rel)
        return {
            "id": fid,
            "group": group_name,
            "kind": kind,
            "view": view,
            "file": out_rel,
            "raw_file": src_rel,
            "w": f_im.width,
            "h": f_im.height,
            "skin_rgb": skin_rgb,
            "is_bearded": is_bearded
        }

    # 1. Poet Front (p02..p09 eyes, p10..p15 brows, p16..p27 mouths)
    for i in range(2, 10):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.face.front/poet.red_black_sunglasses.face.front__p{i:02d}.png", f"poet_e{i:02d}", "Poet", "eye", "front")
        if it: front_eyes.append(it)
    for i in range(10, 16):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.face.front/poet.red_black_sunglasses.face.front__p{i:02d}.png", f"poet_b{i:02d}", "Poet", "brow", "front")
        if it: front_brows.append(it)
    for i in range(16, 28):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.face.front/poet.red_black_sunglasses.face.front__p{i:02d}.png", f"poet_m{i:02d}", "Poet", "mouth", "front")
        if it: front_mouths.append(it)

    # 2. Young Poet Front (p02..p09 eyes, p10..p15 brows, p16..p27 mouths)
    for i in range(2, 10):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.face.front/young_poet.child_clothes.face.front__p{i:02d}.png", f"ypoet_e{i:02d}", "Young Poet", "eye", "front")
        if it: front_eyes.append(it)
    for i in range(10, 16):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.face.front/young_poet.child_clothes.face.front__p{i:02d}.png", f"ypoet_b{i:02d}", "Young Poet", "brow", "front")
        if it: front_brows.append(it)
    for i in range(16, 28):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.face.front/young_poet.child_clothes.face.front__p{i:02d}.png", f"ypoet_m{i:02d}", "Young Poet", "mouth", "front")
        if it: front_mouths.append(it)

    # 3. Family Street Clothes (p01..p08 eyes, p09..p14 brows, p15..p20 & p23..p28 mouths, p21 front nose)
    for i in range(1, 9):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/family.street_clothes.face-feet/family.street_clothes.face-feet__p{i:02d}.png", f"street_e{i:02d}", "Street", "eye", "front")
        if it: front_eyes.append(it)
    for i in range(9, 15):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/family.street_clothes.face-feet/family.street_clothes.face-feet__p{i:02d}.png", f"street_b{i:02d}", "Street", "brow", "front")
        if it: front_brows.append(it)
    for i in list(range(15, 21)) + list(range(23, 29)):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/family.street_clothes.face-feet/family.street_clothes.face-feet__p{i:02d}.png", f"street_m{i:02d}", "Street", "mouth", "front")
        if it: front_mouths.append(it)

    # 4. DJ Cyber & Party Guest (p01..p08 eyes, p09..p14 brows, p15..p26 mouths)
    for pref, sh_name, grp in [("dj", "party.dj_cyber.face-feet", "DJ Cyber"), ("guest", "party.party_guest.face-feet", "Party Guest")]:
        for i in range(1, 9):
            it = add_feathered(f"arena/parts/kit3/release_v2/cuts/{sh_name}/{sh_name}__p{i:02d}.png", f"{pref}_e{i:02d}", grp, "eye", "front")
            if it: front_eyes.append(it)
        for i in range(9, 15):
            it = add_feathered(f"arena/parts/kit3/release_v2/cuts/{sh_name}/{sh_name}__p{i:02d}.png", f"{pref}_b{i:02d}", grp, "brow", "front")
            if it: front_brows.append(it)
        for i in range(15, 27):
            it = add_feathered(f"arena/parts/kit3/release_v2/cuts/{sh_name}/{sh_name}__p{i:02d}.png", f"{pref}_m{i:02d}", grp, "mouth", "front")
            if it: front_mouths.append(it)

    # 5. Vintage Party Female (grommet cropped!)
    vf_sh = "party.vintage_party.face-feet.female"
    for i in [1, 4, 6, 9, 19, 20, 21, 22]:
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/{vf_sh}/{vf_sh}__p{i:02d}.png", f"vfemale_e{i:02d}", "Vintage Woman", "eye", "front", crop_top=0.25)
        if it: front_eyes.append(it)
    for i in [12, 16, 18, 23, 24, 25]:
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/{vf_sh}/{vf_sh}__p{i:02d}.png", f"vfemale_b{i:02d}", "Vintage Woman", "brow", "front", crop_top=0.28)
        if it: front_brows.append(it)
    for i in [30, 31, 32, 33, 34, 35, 39, 40, 41, 42, 43, 44]:
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/{vf_sh}/{vf_sh}__p{i:02d}.png", f"vfemale_m{i:02d}", "Vintage Woman", "mouth", "front", crop_top=0.24)
        if it: front_mouths.append(it)

    # 6. Ghost Child Front (p04..p05 eyes, p08..p09 brows, p12..p13 mouths)
    for i in [4, 5]:
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/ghost_child.02.faces-hands/ghost_child.02.faces-hands__p{i:02d}.png", f"ghost_e{i:02d}", "Ghost Child", "eye", "front")
        if it: front_eyes.append(it)
    for i in [8, 9]:
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/ghost_child.02.faces-hands/ghost_child.02.faces-hands__p{i:02d}.png", f"ghost_b{i:02d}", "Ghost Child", "brow", "front")
        if it: front_brows.append(it)
    for i in [12, 13]:
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/ghost_child.02.faces-hands/ghost_child.02.faces-hands__p{i:02d}.png", f"ghost_m{i:02d}", "Ghost Child", "mouth", "front")
        if it: front_mouths.append(it)

    # 7. Front Noses (Street p21 + Tracksuit 26 + sculptural front noses [4, 9, 13, 16, 19, 21])
    n_specs = [
        ("street_n01", "Street", "arena/parts/kit3/release_v2/cuts/family.street_clothes.face-feet/family.street_clothes.face-feet__p21.png"),
        ("tracksuit_n01", "Poet", "kits/packs/poet_tracksuit_v1/01_COMPONENTS/26_nose_front.png"),
        ("shared_n04", "Sculptural", "arena/parts/body_lab/noses/cast_shared_features/shared_nose_04.png"),
        ("shared_n09", "Sculptural", "arena/parts/body_lab/noses/cast_shared_features/shared_nose_09.png"),
        ("shared_n13", "Sculptural", "arena/parts/body_lab/noses/cast_shared_features/shared_nose_13.png"),
        ("shared_n16", "Sculptural", "arena/parts/body_lab/noses/cast_shared_features/shared_nose_16.png"),
        ("shared_n19", "Sculptural", "arena/parts/body_lab/noses/cast_shared_features/shared_nose_19.png"),
        ("shared_n21", "Sculptural", "arena/parts/body_lab/noses/cast_shared_features/shared_nose_21.png"),
    ]
    for nid, grp, nrel in n_specs:
        it = add_feathered(nrel, nid, grp, "nose", "front")
        if it: front_noses.append(it)

    # 8. Profile Features (profile_R): Poet Profile, Young Poet Profile, Ghost Child Profile
    profile_brows = []
    profile_eyes = []
    profile_mouths = []

    for i in range(2, 10):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.face.profile/poet.red_black_sunglasses.face.profile__p{i:02d}.png", f"poet_prof_e{i:02d}", "Poet", "eye", "profile_R", crop_left=0.25)
        if it: profile_eyes.append(it)
    for i in range(10, 16):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.face.profile/poet.red_black_sunglasses.face.profile__p{i:02d}.png", f"poet_prof_b{i:02d}", "Poet", "brow", "profile_R", crop_left=0.25)
        if it: profile_brows.append(it)
    for i in range(16, 28):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.face.profile/poet.red_black_sunglasses.face.profile__p{i:02d}.png", f"poet_prof_m{i:02d}", "Poet", "mouth", "profile_R", crop_left=0.25)
        if it: profile_mouths.append(it)

    for i in range(2, 10):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.face.profile/young_poet.child_clothes.face.profile__p{i:02d}.png", f"ypoet_prof_e{i:02d}", "Young Poet", "eye", "profile_R", crop_left=0.12)
        if it: profile_eyes.append(it)
    for i in range(10, 16):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.face.profile/young_poet.child_clothes.face.profile__p{i:02d}.png", f"ypoet_prof_b{i:02d}", "Young Poet", "brow", "profile_R", crop_left=0.12)
        if it: profile_brows.append(it)
    for i in range(16, 28):
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.face.profile/young_poet.child_clothes.face.profile__p{i:02d}.png", f"ypoet_prof_m{i:02d}", "Young Poet", "mouth", "profile_R", crop_left=0.12)
        if it: profile_mouths.append(it)

    for i in [6, 7]:
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/ghost_child.02.faces-hands/ghost_child.02.faces-hands__p{i:02d}.png", f"ghost_prof_e{i:02d}", "Ghost Child", "eye", "profile_R", crop_left=0.12)
        if it: profile_eyes.append(it)
    for i in [10, 11]:
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/ghost_child.02.faces-hands/ghost_child.02.faces-hands__p{i:02d}.png", f"ghost_prof_b{i:02d}", "Ghost Child", "brow", "profile_R", crop_left=0.12)
        if it: profile_brows.append(it)
    for i in [14, 15]:
        it = add_feathered(f"arena/parts/kit3/release_v2/cuts/ghost_child.02.faces-hands/ghost_child.02.faces-hands__p{i:02d}.png", f"ghost_prof_m{i:02d}", "Ghost Child", "mouth", "profile_R", crop_left=0.12)
        if it: profile_mouths.append(it)

    # Also tag 3-strip flipbook items with true view & palette so front never mixes with profile!
    for s_key in ["strip_1_brows_eyes", "strip_2_noses_cheeks", "strip_3_mouths_jaws"]:
        for st in pool.get(s_key, []):
            fl = st["file"].lower()
            # In face.front.mouth.08..12, those 4 were profile mouths on the right column of the sheet
            if "face.front.mouth.08" in fl or "face.front.mouth.09" in fl or "face.front.mouth.10" in fl or "face.front.mouth.12" in fl:
                st["view"] = "profile"
            elif ".profile." in fl:
                st["view"] = "profile"
            else:
                st["view"] = "front"
            # Tag color palette by character directory
            if any(k in fl for k in ["father", "ancestors"]):
                st["palette"] = "cool_slate"
            elif "dj_cyber" in fl or "child_traveler" in fl:
                st["palette"] = "neon_accent"
            elif "vintage_party" in fl:
                st["palette"] = "gold_amber"
            else:
                st["palette"] = "warm_tan"

    pool["seamless_face_pool"] = {
        "front_heads": front_heads,
        "profile_heads": profile_heads,
        "front_brows": front_brows,
        "front_eyes": front_eyes,
        "front_noses": front_noses,
        "front_mouths": front_mouths,
        "profile_brows": profile_brows,
        "profile_eyes": profile_eyes,
        "profile_mouths": profile_mouths
    }
    cat["face_and_body_gene_pool"] = pool
    CAT_PATH.write_text(json.dumps(cat, indent=2))

    print(f"Fixed sideways heads: {fixed_sideways}")
    print(f"Purified expressive_heads: {len(clean_exp)} | swapper_bank heads: {len(clean_sb_heads)}")
    print(f"Seamless Front: {len(front_heads)} heads, {len(front_brows)} brows, {len(front_eyes)} eyes, {len(front_noses)} noses, {len(front_mouths)} mouths")
    print(f"Seamless Profile: {len(profile_heads)} heads, {len(profile_brows)} brows, {len(profile_eyes)} eyes, {len(profile_mouths)} mouths")


if __name__ == "__main__":
    main()
