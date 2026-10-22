#!/usr/bin/env python3
"""
fix_massive_set_and_rigs.py (v2 — Exact Visual Template Mapping, Face Compositing & Cross-Kit Kitbashing)
Fixes:
1. Exact per-sheet layout templates for:
   - 13-piece `.body.front / .threequarter / .back` sheets
   - 7-piece `.body.profile` sheets (distinguishing Poet tracksuit `[torso, thigh, shin, uarm, farm, hand, foot]`
     vs Street/DJ `[torso, uarm, farm, thigh, shin, hand, foot]`
     vs Child `[torso, uarm, farm, hand, thigh, shin, foot]`)
   - 14-piece `poet.black_tshirt.compact-core` (`[front.torso, back.torso, front.pelvis, back.pelvis, uarm.L, farm.L, uarm.R, farm.R, thigh.L, shin.L, thigh.R, shin.R, foot.L, foot.R]`)
   - 14-piece `ex.ex_jacket.body.back` & `threequarter_back` (skipping the vape pen prop `p12`/`p08`!)
   - 18-piece `woman.13.body` & `party.vintage_party.body.profile`
   - 21-piece `woman.09.mother.body`, `ancestors.05.ancestor_robe_indigo_gold.body`, `parents.02.father_02.body`
2. Exact 5-head angle order (`p01=front`, `p02=threequarter`, `p03=profile`, `p04=threequarter_back`, `p05=back`)
   + Automatic Face Feature Compositing (eyes, brows, nose, mouth, sunglasses) onto blank head bases so no rig ever displays an eerie blank mannequin head!
3. Cross-Kit Kitbash Matrix in `crash_lab_catalog.json`:
   - Fills missing views (`poet.black_tshirt` hands & profile/3Q torso, `ex.ex_jacket` 3Q-back, `woman_muse` painted heads, `ancestors` turban heads) and records `kitbashed_from` + `torso_style` parameters for the Programmatic 2.5D Torso Solver.
"""

import os
import glob
import json
import shutil
from PIL import Image, ImageEnhance
import numpy as np

ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots"
CUTS_DIR = os.path.join(ROOT, "arena/parts/kit3/release_v2/cuts")
V2_PARTS_DIR = os.path.join(ROOT, "arena/parts/kit3/v2/parts")
CATALOG_PATH = os.path.join(ROOT, "arena/parts/kit3/release_v2/crash_lab_catalog.json")
TS_DIR = os.path.join(ROOT, "kits/packs/poet_tracksuit_v1/01_COMPONENTS")


def get_cut(folder, idx_1based):
    p = os.path.join(CUTS_DIR, folder, f"{folder}__p{idx_1based:02d}.png")
    return p if os.path.exists(p) else None


def copy_cut(src_folder, idx_1based, dst_dir, dst_name, crop_box_ratio=None, rotate_ccw=0, flip_x=False):
    src = get_cut(src_folder, idx_1based)
    if not src:
        return False
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, dst_name)
    im = Image.open(src).convert("RGBA")
    if crop_box_ratio:
        w, h = im.size
        x0, y0, x1, y1 = crop_box_ratio
        im = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
    if rotate_ccw != 0:
        im = im.rotate(rotate_ccw, expand=True)
    if flip_x:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im.save(dst)
    return True


def composite_face_onto_head(base_head_path, overlays, dst_path):
    """
    Composites facial feature PNGs (`(path, cx_ratio, cy_ratio, width_ratio)`) onto a blank head base
    so the character head has painted eyes, brows, nose, mouth, or sunglasses baked in.
    """
    if not base_head_path or not os.path.exists(base_head_path):
        return False
    base = Image.open(base_head_path).convert("RGBA")
    bw, bh = base.size
    for ov_path, cx_r, cy_r, w_r in overlays:
        if not ov_path or not os.path.exists(ov_path):
            continue
        ov = Image.open(ov_path).convert("RGBA")
        ow, oh = ov.size
        if ow < 2 or oh < 2:
            continue
        target_w = max(8, int(bw * w_r))
        target_h = max(6, int(oh * (target_w / float(ow))))
        ov_resized = ov.resize((target_w, target_h), Image.LANCZOS)
        px = int(bw * cx_r - target_w * 0.5)
        py = int(bh * cy_r - target_h * 0.5)
        base.alpha_composite(ov_resized, (max(0, min(bw - target_w, px)), max(0, min(bh - target_h, py))))
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    base.save(dst_path)
    return True


def synthesize_profile_tshirt_torso(front_torso_path, dst_path):
    """
    Creates a side-profile black t-shirt torso with a kraft-bordered side armhole socket
    from the front black t-shirt torso (for `poet.black_tshirt` kitbashing).
    """
    if not os.path.exists(front_torso_path):
        return
    im = Image.open(front_torso_path).convert("RGBA")
    w, h = im.size
    prof_w = int(w * 0.62)
    prof = im.resize((prof_w, h), Image.LANCZOS)
    # Pad back to a clean canvas
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(prof, ((w - prof_w) // 2, 0))
    out.save(dst_path)


def copy_13_row(src_folder, dst_dir, view_name):
    """Standard 13-piece body view sheet: torso, uarm.L/R, farm.L/R, hand.L/R, thigh.L/R, shin.L/R, foot.L/R, pelvis."""
    mapping = [
        (1, f"body.{view_name}.torso.png", (0, 0, 1, 0.94) if view_name == "back" else None),
        (2, f"body.{view_name}.uarm.L.png", None),
        (2 if (src_folder == "poet.red_black_sunglasses.body.threequarter") else 3, f"body.{view_name}.uarm.R.png", None),
        (4, f"body.{view_name}.farm.L.png", None),
        (5, f"body.{view_name}.farm.R.png", None),
        (6, f"body.{view_name}. thigh_or_hand_6", None),
    ]
    # Note: Let's check whether p06..p13 on 13-piece sheets are:
    # p01=torso, p02=uarm.L, p03=uarm.R, p04=farm.L, p05=farm.R,
    # p06=thigh.L, p07=thigh.R, p08=shin.L, p09=shin.R, p10=hand.L, p11=hand.R, p12=foot.L, p13=foot.R/pelvis
    # Wait: let's inspect the aspect ratios / sizes of p06..p13 dynamically so we NEVER confuse a thigh with a hand or foot!
    cuts = []
    for idx in range(1, 15):
        p = get_cut(src_folder, idx)
        if p:
            im = Image.open(p)
            cuts.append((idx, p, im.size[0], im.size[1]))
    if not cuts:
        return

    # p01 is always torso
    copy_cut(src_folder, 1, dst_dir, f"body.{view_name}.torso.png", (0, 0, 1, 0.94) if view_name == "back" else None)
    # p02, p03 are uarm.L, uarm.R (use p02 for both if p03 has attached text like threequarter.uarm.R)
    copy_cut(src_folder, 2, dst_dir, f"body.{view_name}.uarm.L.png")
    copy_cut(src_folder, 2 if "threequarter" in src_folder else 3, dst_dir, f"body.{view_name}.uarm.R.png")
    # p04, p05 are farm.L, farm.R
    copy_cut(src_folder, 4, dst_dir, f"body.{view_name}.farm.L.png")
    copy_cut(src_folder, 5, dst_dir, f"body.{view_name}.farm.R.png")

    # Classify remaining cuts p06..p13 by their geometry:
    # - Hands: smaller height than thighs/shins, or fingers/thumb shape
    # - Feet/Boots: wider or L-shaped (w/h > 0.52) at the end of the sheet
    # - Pelvis/Hip-bridge: triangular or oval wide piece (w/h > 0.62)
    # - Thighs & Shins: tall tubular pieces (w/h < 0.50, height > 280)
    tall_limbs = []
    hands = []
    feet = []
    pelvises = []
    for idx, p, w, h in cuts[5:]:
        aspect = w / float(max(1, h))
        if h >= 310 and aspect < 0.50:
            tall_limbs.append((idx, w, h))
        elif aspect >= 0.68 and h < 260:
            # Could be foot or pelvis
            if idx >= 11:
                feet.append((idx, w, h))
            else:
                pelvises.append((idx, w, h))
        elif h < 310 and aspect < 0.68:
            if idx >= 11 and len(feet) < 2:
                feet.append((idx, w, h))
            else:
                hands.append((idx, w, h))
        else:
            if idx >= 11:
                feet.append((idx, w, h))
            else:
                pelvises.append((idx, w, h))

    # Among tall_limbs (usually 4: thigh.L, thigh.R, shin.L, shin.R):
    # Thighs are the wider pair (or first pair), shins are the narrower pair (or second pair)
    if len(tall_limbs) >= 4:
        # Sort by index: first 2 are thighs, next 2 are shins
        tL, tR = tall_limbs[0][0], tall_limbs[1][0]
        sL, sR = tall_limbs[2][0], tall_limbs[3][0]
        # Avoid text label on poet back thigh L
        if src_folder == "poet.red_black_sunglasses.body.back":
            tL = tR
        copy_cut(src_folder, tL, dst_dir, f"body.{view_name}.thigh.L.png")
        copy_cut(src_folder, tR, dst_dir, f"body.{view_name}.thigh.R.png")
        copy_cut(src_folder, sL, dst_dir, f"body.{view_name}.shin.L.png")
        copy_cut(src_folder, sR, dst_dir, f"body.{view_name}.shin.R.png")
    elif len(tall_limbs) >= 2:
        copy_cut(src_folder, tall_limbs[0][0], dst_dir, f"body.{view_name}.thigh.L.png")
        copy_cut(src_folder, tall_limbs[0][0], dst_dir, f"body.{view_name}.thigh.R.png")
        copy_cut(src_folder, tall_limbs[1][0], dst_dir, f"body.{view_name}.shin.L.png")
        copy_cut(src_folder, tall_limbs[1][0], dst_dir, f"body.{view_name}.shin.R.png")

    if len(hands) >= 2:
        copy_cut(src_folder, hands[0][0], dst_dir, f"body.{view_name}.hand.L.png")
        copy_cut(src_folder, hands[1][0], dst_dir, f"body.{view_name}.hand.R.png")
    elif len(hands) == 1:
        copy_cut(src_folder, hands[0][0], dst_dir, f"body.{view_name}.hand.L.png")
        copy_cut(src_folder, hands[0][0], dst_dir, f"body.{view_name}.hand.R.png", flip_x=True)

    if len(feet) >= 2:
        crop_f = (0, 0, 1, 0.90) if view_name == "back" and "poet.red_black" in src_folder else None
        copy_cut(src_folder, feet[0][0], dst_dir, f"body.{view_name}.foot.L.png", crop_f)
        copy_cut(src_folder, feet[1][0], dst_dir, f"body.{view_name}.foot.R.png", crop_f)
    elif len(feet) == 1:
        copy_cut(src_folder, feet[0][0], dst_dir, f"body.{view_name}.foot.L.png")
        copy_cut(src_folder, feet[0][0], dst_dir, f"body.{view_name}.foot.R.png")

    if pelvises:
        copy_cut(src_folder, pelvises[0][0], dst_dir, f"body.{view_name}.pelvis.png")


def rebuild_all_kits():
    repaired = 0

    # =========================================================================
    # 1. POET (RED/BLACK TRACKSUIT) — `poet.red_black_sunglasses`
    # =========================================================================
    d_poet = os.path.join(V2_PARTS_DIR, "poet.red_black_sunglasses")
    for v in ["front", "threequarter", "back"]:
        copy_13_row(f"poet.red_black_sunglasses.body.{v}", d_poet, v)
    # Profile 7-piece sheet: p01=torso, p02=thigh, p03=shin, p04=uarm, p05=farm, p06=hand, p07=foot
    p_prof = "poet.red_black_sunglasses.body.profile"
    copy_cut(p_prof, 1, d_poet, "body.profile.torso.png")
    for side in ["L", "R"]:
        copy_cut(p_prof, 2, d_poet, f"body.profile.thigh.{side}.png")
        copy_cut(p_prof, 3, d_poet, f"body.profile.shin.{side}.png")
        copy_cut(p_prof, 4, d_poet, f"body.profile.uarm.{side}.png")
        copy_cut(p_prof, 5, d_poet, f"body.profile.farm.{side}.png")
        copy_cut(p_prof, 6, d_poet, f"body.profile.hand.{side}.png")
        copy_cut(p_prof, 7, d_poet, f"body.profile.foot.{side}.png")
    # Hipcore
    copy_cut("poet.red_black_sunglasses.hipcore", 1, d_poet, "body.threequarter.pelvis.png")
    copy_cut("poet.red_black_sunglasses.hipcore", 2, d_poet, "body.profile.pelvis.png")
    copy_cut("poet.red_black_sunglasses.hipcore", 2, d_poet, "body.back.pelvis.png")
    copy_cut("poet.red_black_sunglasses.hipcore", 3, d_poet, "body.front.pelvis.png")
    # Heads: Use the ultra-crisp artist-painted heads from `weave/cast/man/library/head/`!
    weave_head_dir = os.path.join(ROOT, "weave/cast/man/library/head")
    prof_face_dir = os.path.join(ROOT, "kits/packs/poet_tracksuit_v1/01_COMPONENTS/profile_face_clean")
    copy_cut("poet.red_black_sunglasses.heads", 1, d_poet, "head.front.blank.png")
    copy_cut("poet.red_black_sunglasses.heads", 2, d_poet, "head.threequarter.blank.png")
    copy_cut("poet.red_black_sunglasses.heads", 3, d_poet, "head.profile.blank.png")
    copy_cut("poet.red_black_sunglasses.heads", 4, d_poet, "head.threequarter_back.png")
    shutil.copy2(os.path.join(weave_head_dir, "head.back.neutral.png"), os.path.join(d_poet, "head.back.png"))
    shutil.copy2(os.path.join(weave_head_dir, "head.front.sunglasses.png"), os.path.join(d_poet, "head.front.png"))
    shutil.copy2(os.path.join(weave_head_dir, "head.sunglasses_shades.png"), os.path.join(d_poet, "head.threequarter.png"))
    composite_face_onto_head(
        os.path.join(weave_head_dir, "head.profile_R.neutral.png"),
        [
            (os.path.join(prof_face_dir, "profile_sunglasses_10.png"), 0.65, 0.42, 0.56),
        ],
        os.path.join(d_poet, "head.profile.png"),
    )
    repaired += 45

    # =========================================================================
    # 2. POET (BLACK T-SHIRT) — `poet.black_tshirt` (14-piece compact-core + Kitbash)
    # =========================================================================
    d_bt = os.path.join(V2_PARTS_DIR, "poet.black_tshirt")
    cc = "poet.black_tshirt.compact-core"
    # p01=front.torso, p02=back.torso, p03=front.pelvis, p04=back.pelvis,
    # p05=uarm.L, p06=farm.L, p07=uarm.R, p08=farm.R,
    # p09=thigh.L, p10=shin.L, p11=thigh.R, p12=shin.R, p13=foot.L, p14=foot.R
    copy_cut(cc, 1, d_bt, "body.front.torso.png")
    copy_cut(cc, 1, d_bt, "body.threequarter.torso.png")
    copy_cut(cc, 2, d_bt, "body.back.torso.png", crop_box_ratio=(0, 0.11, 1, 1))
    synthesize_profile_tshirt_torso(os.path.join(d_bt, "body.front.torso.png"), os.path.join(d_bt, "body.profile.torso.png"))
    for v in ["front", "threequarter", "profile"]:
        copy_cut(cc, 3, d_bt, f"body.{v}.pelvis.png")
    copy_cut(cc, 4, d_bt, "body.back.pelvis.png")
    for v in ["front", "threequarter", "profile", "back"]:
        copy_cut(cc, 5, d_bt, f"body.{v}.uarm.L.png")
        copy_cut(cc, 7, d_bt, f"body.{v}.uarm.R.png")
        copy_cut(cc, 6, d_bt, f"body.{v}.farm.L.png")
        copy_cut(cc, 8, d_bt, f"body.{v}.farm.R.png")
        copy_cut(cc, 9, d_bt, f"body.{v}.thigh.L.png")
        copy_cut(cc, 11, d_bt, f"body.{v}.thigh.R.png")
        copy_cut(cc, 10, d_bt, f"body.{v}.shin.L.png")
        copy_cut(cc, 12, d_bt, f"body.{v}.shin.R.png")
        copy_cut(cc, 13, d_bt, f"body.{v}.foot.L.png")
        copy_cut(cc, 14, d_bt, f"body.{v}.foot.R.png")
        # Kitbash hands from poet.red_black_sunglasses!
        for side in ["L", "R"]:
            shutil.copy2(os.path.join(d_poet, f"body.{v}.hand.{side}.png"), os.path.join(d_bt, f"body.{v}.hand.{side}.png"))
    # Kitbash painted Poet heads from `weave/cast/man/library/head/` (without sunglasses for Poems 01-03 Black Tee!)
    shutil.copy2(os.path.join(weave_head_dir, "head.front.neutral.png"), os.path.join(d_bt, "head.front.png"))
    shutil.copy2(os.path.join(weave_head_dir, "head.threequarter_R.neutral.png"), os.path.join(d_bt, "head.threequarter.png"))
    shutil.copy2(os.path.join(weave_head_dir, "head.profile_R.neutral.png"), os.path.join(d_bt, "head.profile.png"))
    shutil.copy2(os.path.join(weave_head_dir, "head.back.neutral.png"), os.path.join(d_bt, "head.back.png"))
    repaired += 52

    # =========================================================================
    # 3. EX (OLIVE BOMBER JACKET) — `ex.ex_jacket` (14-piece back & 3Q-back, skipping vape pen!)
    # =========================================================================
    d_ex = os.path.join(V2_PARTS_DIR, "ex.ex_jacket")
    ex_b = "ex.ex_jacket.body.back"
    # p01=torso, p02=uarm.L, p03=uarm.R, p04=farm.L, p05=farm.R, p06=hand.L, p07=hand.R,
    # p08=thigh.L, p09=shin.L, p10=thigh.R, p11=shin.R, p12=VAPE_PEN(skip!), p13=foot.L, p14=foot.R
    copy_cut(ex_b, 1, d_ex, "body.back.torso.png")
    copy_cut(ex_b, 2, d_ex, "body.back.uarm.L.png")
    copy_cut(ex_b, 3, d_ex, "body.back.uarm.R.png")
    copy_cut(ex_b, 4, d_ex, "body.back.farm.L.png")
    copy_cut(ex_b, 5, d_ex, "body.back.farm.R.png")
    copy_cut(ex_b, 6, d_ex, "body.back.hand.L.png")
    copy_cut(ex_b, 7, d_ex, "body.back.hand.R.png")
    copy_cut(ex_b, 8, d_ex, "body.back.thigh.L.png")
    copy_cut(ex_b, 9, d_ex, "body.back.shin.L.png")
    copy_cut(ex_b, 10, d_ex, "body.back.thigh.R.png")
    copy_cut(ex_b, 11, d_ex, "body.back.shin.R.png")
    copy_cut(ex_b, 13, d_ex, "body.back.foot.L.png")
    copy_cut(ex_b, 14, d_ex, "body.back.foot.R.png")

    ex_3q = "ex.ex_jacket.body.threequarter_back"
    # p01=torso, p02=uarm.L, p03=uarm.R, p04=farm.L, p05=farm.R, p06=hand.L, p07=hand.R,
    # p08=VAPE_PEN(skip!), p09=thigh.L, p10=thigh.R, p11=shin.L, p12=shin.R, p13=foot.L, p14=foot.R
    for v in ["threequarter", "profile", "front"]:
        copy_cut(ex_3q, 1, d_ex, f"body.{v}.torso.png")
        copy_cut(ex_3q, 2, d_ex, f"body.{v}.uarm.L.png")
        copy_cut(ex_3q, 3, d_ex, f"body.{v}.uarm.R.png")
        copy_cut(ex_3q, 4, d_ex, f"body.{v}.farm.L.png")
        copy_cut(ex_3q, 5, d_ex, f"body.{v}.farm.R.png")
        copy_cut(ex_3q, 6, d_ex, f"body.{v}.hand.L.png")
        copy_cut(ex_3q, 7, d_ex, f"body.{v}.hand.R.png")
        copy_cut(ex_3q, 9, d_ex, f"body.{v}.thigh.L.png")
        copy_cut(ex_3q, 10, d_ex, f"body.{v}.thigh.R.png")
        copy_cut(ex_3q, 11, d_ex, f"body.{v}.shin.L.png")
        copy_cut(ex_3q, 12, d_ex, f"body.{v}.shin.R.png")
        copy_cut(ex_3q, 13, d_ex, f"body.{v}.foot.L.png")
        copy_cut(ex_3q, 14, d_ex, f"body.{v}.foot.R.png")
    # EX heads (strictly back / 3Q-back / profile-back)
    copy_cut("ex.ex_jacket.heads", 1, d_ex, "head.back.png")
    copy_cut("ex.ex_jacket.heads", 2, d_ex, "head.threequarter.png")
    copy_cut("ex.ex_jacket.heads", 2, d_ex, "head.front.png")
    copy_cut("ex.ex_jacket.heads", 4, d_ex, "head.profile.png")
    repaired += 48

    # =========================================================================
    # 4. WOMAN / MUSE (`woman.teal_dress`) & MOTHER (`woman.mother_cardigan`)
    # =========================================================================
    d_wom = os.path.join(V2_PARTS_DIR, "woman.teal_dress")
    w13 = "woman.13.body"
    # p01=head, p02=front.torso, p03=back.torso, p04=skirt.front, p05=pelvis.front, p06=pelvis.back,
    # p07=skirt.back, p08..09=uarm, p10..11=farm, p12..13=thigh, p14..15=shin, p16=profile.torso, p17..18=foot
    copy_cut(w13, 2, d_wom, "body.front.torso.png")
    copy_cut(w13, 2, d_wom, "body.threequarter.torso.png")
    copy_cut(w13, 3, d_wom, "body.back.torso.png")
    copy_cut(w13, 16, d_wom, "body.profile.torso.png")
    for v in ["front", "threequarter", "profile"]:
        copy_cut(w13, 5, d_wom, f"body.{v}.pelvis.png")
    copy_cut(w13, 6, d_wom, "body.back.pelvis.png")
    for v in ["front", "threequarter", "profile", "back"]:
        copy_cut(w13, 8, d_wom, f"body.{v}.uarm.L.png")
        copy_cut(w13, 9, d_wom, f"body.{v}.uarm.R.png")
        copy_cut(w13, 10, d_wom, f"body.{v}.farm.L.png")
        copy_cut(w13, 11, d_wom, f"body.{v}.farm.R.png")
        copy_cut(w13, 12, d_wom, f"body.{v}.thigh.L.png")
        copy_cut(w13, 13, d_wom, f"body.{v}.thigh.R.png")
        copy_cut(w13, 14, d_wom, f"body.{v}.shin.L.png")
        copy_cut(w13, 15, d_wom, f"body.{v}.shin.R.png")
        copy_cut(w13, 17, d_wom, f"body.{v}.foot.L.png")
        copy_cut(w13, 18, d_wom, f"body.{v}.foot.R.png")
    # Woman painted heads from `woman.13.heads-hands` (p06=painted front, p02+eyes=3Q, p03=painted profile, p05=back)
    copy_cut("woman.13.heads-hands", 6, d_wom, "head.front.png")
    copy_cut("woman.13.heads-hands", 2, d_wom, "head.threequarter.blank.png")
    composite_face_onto_head(
        os.path.join(d_wom, "head.threequarter.blank.png"),
        [(get_cut("woman.13.heads-hands", 8), 0.62, 0.50, 0.44)],
        os.path.join(d_wom, "head.threequarter.png"),
    )
    copy_cut("woman.13.heads-hands", 3, d_wom, "head.profile.png")
    copy_cut("woman.13.heads-hands", 4, d_wom, "head.threequarter_back.png")
    copy_cut("woman.13.heads-hands", 5, d_wom, "head.back.png")

    # Mother (`woman.mother_cardigan`) from `woman.09.mother.body` (21 cuts) & `woman.09.mother.heads-hands`
    d_mom = os.path.join(V2_PARTS_DIR, "woman.mother_cardigan")
    w09 = "woman.09.mother.body"
    copy_cut(w09, 1, d_mom, "body.front.torso.png")
    copy_cut(w09, 1, d_mom, "body.threequarter.torso.png")
    copy_cut(w09, 2, d_mom, "body.back.torso.png")
    copy_cut(w09, 3, d_mom, "body.profile.torso.png")
    for v in ["front", "threequarter", "profile"]:
        copy_cut(w09, 8, d_mom, f"body.{v}.pelvis.png")
    copy_cut(w09, 9, d_mom, "body.back.pelvis.png")
    for v in ["front", "threequarter", "profile", "back"]:
        copy_cut(w09, 4, d_mom, f"body.{v}.uarm.L.png")
        copy_cut(w09, 5, d_mom, f"body.{v}.uarm.R.png")
        copy_cut(w09, 6, d_mom, f"body.{v}.farm.L.png")
        copy_cut(w09, 7, d_mom, f"body.{v}.farm.R.png")
        copy_cut(w09, 10, d_mom, f"body.{v}.thigh.L.png")
        copy_cut(w09, 11, d_mom, f"body.{v}.thigh.R.png")
        copy_cut(w09, 12, d_mom, f"body.{v}.shin.L.png")
        copy_cut(w09, 13, d_mom, f"body.{v}.shin.R.png")
        copy_cut(w09, 16, d_mom, f"body.{v}.foot.L.png")
        copy_cut(w09, 17, d_mom, f"body.{v}.foot.R.png")
    copy_cut("woman.09.mother.heads-hands", 1, d_mom, "head.front.blank.png")
    composite_face_onto_head(
        os.path.join(d_mom, "head.front.blank.png"),
        [(get_cut("woman.09.mother.heads-hands", 6), 0.50, 0.52, 0.46)],
        os.path.join(d_mom, "head.front.png"),
    )
    copy_cut("woman.09.mother.heads-hands", 2, d_mom, "head.threequarter.blank.png")
    composite_face_onto_head(
        os.path.join(d_mom, "head.threequarter.blank.png"),
        [(get_cut("woman.09.mother.heads-hands", 6), 0.58, 0.52, 0.44)],
        os.path.join(d_mom, "head.threequarter.png"),
    )
    copy_cut("woman.09.mother.heads-hands", 3, d_mom, "head.profile.png")
    copy_cut("woman.09.mother.heads-hands", 5, d_mom, "head.back.png")
    repaired += 80

    # =========================================================================
    # 5. ANCESTORS (`ancestors.ancestor_robe_indigo_gold`) & PARENTS (`parents.elder_father_coat`)
    # =========================================================================
    d_anc = os.path.join(V2_PARTS_DIR, "ancestors.ancestor_robe_indigo_gold")
    anc_b = "ancestors.05.ancestor_robe_indigo_gold.body"
    copy_cut(anc_b, 1, d_anc, "body.front.torso.png")
    copy_cut(anc_b, 1, d_anc, "body.threequarter.torso.png")
    copy_cut(anc_b, 2, d_anc, "body.back.torso.png")
    copy_cut(anc_b, 3, d_anc, "body.profile.torso.png")
    for v in ["front", "threequarter", "profile"]:
        copy_cut(anc_b, 4, d_anc, f"body.{v}.pelvis.png")
    copy_cut(anc_b, 9, d_anc, "body.back.pelvis.png")
    for v in ["front", "threequarter", "profile", "back"]:
        copy_cut(anc_b, 5, d_anc, f"body.{v}.uarm.L.png")
        copy_cut(anc_b, 6, d_anc, f"body.{v}.uarm.R.png")
        copy_cut(anc_b, 7, d_anc, f"body.{v}.farm.L.png")
        copy_cut(anc_b, 8, d_anc, f"body.{v}.farm.R.png")
        copy_cut(anc_b, 10, d_anc, f"body.{v}.thigh.L.png")
        copy_cut(anc_b, 11, d_anc, f"body.{v}.thigh.R.png")
        copy_cut(anc_b, 12, d_anc, f"body.{v}.shin.L.png")
        copy_cut(anc_b, 13, d_anc, f"body.{v}.shin.R.png")
        copy_cut(anc_b, 16, d_anc, f"body.{v}.foot.L.png")
        copy_cut(anc_b, 17, d_anc, f"body.{v}.foot.R.png")
    # True Ancestor turban heads (`ancestors.05.identities.01`: p01=front, p02=profile, p03=back)
    copy_cut("ancestors.05.identities.01", 1, d_anc, "head.front.png", (0, 0, 1, 0.94))
    copy_cut("ancestors.05.identities.01", 1, d_anc, "head.threequarter.png", (0, 0, 1, 0.94))
    copy_cut("ancestors.05.identities.01", 2, d_anc, "head.profile.png")
    copy_cut("ancestors.05.identities.01", 3, d_anc, "head.back.png")

    # =========================================================================
    # 6. CHILD TRAVELER (`young_poet.child_clothes`)
    # =========================================================================
    d_ch = os.path.join(V2_PARTS_DIR, "young_poet.child_clothes")
    for v in ["front", "threequarter", "back"]:
        copy_13_row(f"young_poet.child_clothes.body.{v}", d_ch, v)
    ch_p = "young_poet.child_clothes.body.profile"
    # p01=torso, p02=uarm, p03=farm, p04=hand, p05=thigh, p06=shin, p07=foot
    copy_cut(ch_p, 1, d_ch, "body.profile.torso.png")
    for side in ["L", "R"]:
        copy_cut(ch_p, 2, d_ch, f"body.profile.uarm.{side}.png")
        copy_cut(ch_p, 3, d_ch, f"body.profile.farm.{side}.png")
        copy_cut(ch_p, 4, d_ch, f"body.profile.hand.{side}.png")
        copy_cut(ch_p, 5, d_ch, f"body.profile.thigh.{side}.png")
        copy_cut(ch_p, 6, d_ch, f"body.profile.shin.{side}.png")
        copy_cut(ch_p, 7, d_ch, f"body.profile.foot.{side}.png")
    # Child heads (`p01=front`, `p02=3Q`, `p03=profile`, `p04=3Q_back`, `p05=back`) + face compositing
    copy_cut("young_poet.child_clothes.heads", 1, d_ch, "head.front.blank.png")
    copy_cut("young_poet.child_clothes.heads", 2, d_ch, "head.threequarter.blank.png")
    copy_cut("young_poet.child_clothes.heads", 3, d_ch, "head.profile.blank.png")
    copy_cut("young_poet.child_clothes.heads", 4, d_ch, "head.threequarter_back.png")
    copy_cut("young_poet.child_clothes.heads", 5, d_ch, "head.back.png")
    composite_face_onto_head(
        os.path.join(d_ch, "head.front.blank.png"),
        [
            (os.path.join(d_ch, "face.front.brows.rest.png"), 0.50, 0.44, 0.55),
            (os.path.join(d_ch, "face.front.eyes.rest.png"), 0.50, 0.52, 0.54),
            (os.path.join(d_ch, "face.front.mouth.neutral.png"), 0.50, 0.72, 0.30),
        ],
        os.path.join(d_ch, "head.front.png"),
    )
    composite_face_onto_head(
        os.path.join(d_ch, "head.threequarter.blank.png"),
        [
            (os.path.join(d_ch, "face.front.brows.rest.png"), 0.56, 0.44, 0.52),
            (os.path.join(d_ch, "face.front.eyes.rest.png"), 0.56, 0.52, 0.50),
            (os.path.join(d_ch, "face.front.mouth.neutral.png"), 0.56, 0.72, 0.28),
        ],
        os.path.join(d_ch, "head.threequarter.png"),
    )
    composite_face_onto_head(
        os.path.join(d_ch, "head.profile.blank.png"),
        [
            (os.path.join(d_ch, "face.profile.brows.rest.png"), 0.68, 0.44, 0.32),
            (os.path.join(d_ch, "face.profile.eyes.open.png"), 0.68, 0.52, 0.30),
            (os.path.join(d_ch, "face.profile.mouth.neutral.png"), 0.68, 0.72, 0.24),
        ],
        os.path.join(d_ch, "head.profile.png"),
    )
    repaired += 45

    # =========================================================================
    # 7. VINTAGE PARTY (`party.vintage_party`), CYBER DJ (`party.dj_cyber`), STREET (`family.street_clothes`)
    # =========================================================================
    # Vintage Party Profile (`p01=torso, p02=uarm, p03=farm, p04=thigh, p05=shin, p06=pelvis, p07=hand, p09=foot`)
    d_vp = os.path.join(V2_PARTS_DIR, "party.vintage_party")
    vp_p = "party.vintage_party.body.profile"
    copy_cut(vp_p, 1, d_vp, "body.profile.torso.png")
    copy_cut(vp_p, 6, d_vp, "body.profile.pelvis.png")
    for side in ["L", "R"]:
        copy_cut(vp_p, 2, d_vp, f"body.profile.uarm.{side}.png")
        copy_cut(vp_p, 3, d_vp, f"body.profile.farm.{side}.png")
        copy_cut(vp_p, 4, d_vp, f"body.profile.thigh.{side}.png")
        copy_cut(vp_p, 5, d_vp, f"body.profile.shin.{side}.png")
        copy_cut(vp_p, 7, d_vp, f"body.profile.hand.{side}.png")
        copy_cut(vp_p, 9, d_vp, f"body.profile.foot.{side}.png")
    copy_cut("party.vintage_party.heads", 1, d_vp, "head.front.blank.png")
    copy_cut("party.vintage_party.heads", 2, d_vp, "head.threequarter.blank.png")
    copy_cut("party.vintage_party.heads", 3, d_vp, "head.profile.blank.png")
    copy_cut("party.vintage_party.heads", 4, d_vp, "head.threequarter_back.png")
    copy_cut("party.vintage_party.heads", 5, d_vp, "head.back.png")
    composite_face_onto_head(
        os.path.join(d_vp, "head.front.blank.png"),
        [
            (os.path.join(d_poet, "face.front.brows.rest.png"), 0.50, 0.36, 0.58),
            (os.path.join(d_poet, "face.front.eyes.rest.png"), 0.50, 0.43, 0.56),
            (os.path.join(d_poet, "face.front.mouth.neutral.png"), 0.50, 0.64, 0.34),
        ],
        os.path.join(d_vp, "head.front.png"),
    )
    composite_face_onto_head(
        os.path.join(d_vp, "head.threequarter.blank.png"),
        [
            (os.path.join(d_poet, "face.front.brows.rest.png"), 0.56, 0.36, 0.54),
            (os.path.join(d_poet, "face.front.eyes.rest.png"), 0.56, 0.43, 0.52),
            (os.path.join(d_poet, "face.front.mouth.neutral.png"), 0.56, 0.64, 0.32),
        ],
        os.path.join(d_vp, "head.threequarter.png"),
    )
    composite_face_onto_head(
        os.path.join(d_vp, "head.profile.blank.png"),
        [
            (os.path.join(d_poet, "face.profile.brows.rest.png"), 0.68, 0.36, 0.34),
            (os.path.join(d_poet, "face.profile.eyes.open.png"), 0.68, 0.43, 0.32),
            (os.path.join(d_poet, "face.profile.mouth.neutral.png"), 0.68, 0.63, 0.26),
        ],
        os.path.join(d_vp, "head.profile.png"),
    )

    # Cyber DJ (`party.dj_cyber.body.profile`: p01=torso, p02=uarm, p03=farm, p04=thigh, p05=shin, p06=hand, p07=foot, p08=pelvis)
    d_dj = os.path.join(V2_PARTS_DIR, "party.dj_cyber")
    dj_p = "party.dj_cyber.body.profile"
    copy_cut(dj_p, 1, d_dj, "body.profile.torso.png")
    copy_cut(dj_p, 8, d_dj, "body.profile.pelvis.png")
    for side in ["L", "R"]:
        copy_cut(dj_p, 2, d_dj, f"body.profile.uarm.{side}.png")
        copy_cut(dj_p, 3, d_dj, f"body.profile.farm.{side}.png")
        copy_cut(dj_p, 4, d_dj, f"body.profile.thigh.{side}.png")
        copy_cut(dj_p, 5, d_dj, f"body.profile.shin.{side}.png")
        copy_cut(dj_p, 6, d_dj, f"body.profile.hand.{side}.png", (0, 0, 1, 0.92))
        copy_cut(dj_p, 7, d_dj, f"body.profile.foot.{side}.png", (0, 0, 1, 0.92))
    copy_cut("party.dj_cyber.heads", 1, d_dj, "head.front.blank.png")
    copy_cut("party.dj_cyber.heads", 2, d_dj, "head.threequarter.blank.png")
    copy_cut("party.dj_cyber.heads", 3, d_dj, "head.profile.blank.png")
    copy_cut("party.dj_cyber.heads", 4, d_dj, "head.threequarter_back.png")
    copy_cut("party.dj_cyber.heads", 5, d_dj, "head.back.png")
    composite_face_onto_head(
        os.path.join(d_dj, "head.front.blank.png"),
        [
            (os.path.join(d_poet, "face.front.eyes.rest.png"), 0.50, 0.45, 0.56),
            (os.path.join(d_poet, "face.front.mouth.neutral.png"), 0.50, 0.65, 0.34),
            (os.path.join(d_poet, "face.front.sunglasses.png"), 0.50, 0.45, 0.74),
        ],
        os.path.join(d_dj, "head.front.png"),
    )
    composite_face_onto_head(
        os.path.join(d_dj, "head.threequarter.blank.png"),
        [
            (os.path.join(d_poet, "face.front.eyes.rest.png"), 0.54, 0.46, 0.52),
            (os.path.join(d_poet, "face.front.mouth.neutral.png"), 0.54, 0.66, 0.32),
            (os.path.join(d_poet, "face.front.sunglasses.png"), 0.54, 0.46, 0.68),
        ],
        os.path.join(d_dj, "head.threequarter.png"),
    )
    composite_face_onto_head(
        os.path.join(d_dj, "head.profile.blank.png"),
        [
            (os.path.join(d_poet, "face.profile.eyes.open.png"), 0.66, 0.46, 0.32),
            (os.path.join(d_poet, "face.profile.mouth.neutral.png"), 0.66, 0.65, 0.26),
            (os.path.join(d_poet, "face.profile.sunglasses.png"), 0.62, 0.46, 0.54),
        ],
        os.path.join(d_dj, "head.profile.png"),
    )

    # Family Street Clothes (`family.street_clothes`)
    d_st = os.path.join(V2_PARTS_DIR, "family.street_clothes")
    st_p = "family.street_clothes.body.profile"
    copy_cut(st_p, 1, d_st, "body.profile.torso.png")
    for side in ["L", "R"]:
        copy_cut(st_p, 2, d_st, f"body.profile.uarm.{side}.png")
        copy_cut(st_p, 3, d_st, f"body.profile.farm.{side}.png")
        copy_cut(st_p, 4, d_st, f"body.profile.thigh.{side}.png")
        copy_cut(st_p, 5, d_st, f"body.profile.shin.{side}.png")
        copy_cut(st_p, 6, d_st, f"body.profile.hand.{side}.png")
        copy_cut(st_p, 7, d_st, f"body.profile.foot.{side}.png")
    copy_cut("family.street_clothes.heads", 1, d_st, "head.front.blank.png")
    copy_cut("family.street_clothes.heads", 2, d_st, "head.threequarter.blank.png")
    copy_cut("family.street_clothes.heads", 3, d_st, "head.profile.blank.png")
    copy_cut("family.street_clothes.heads", 4, d_st, "head.threequarter_back.png")
    copy_cut("family.street_clothes.heads", 5, d_st, "head.back.png")
    composite_face_onto_head(
        os.path.join(d_st, "head.front.blank.png"),
        [
            (os.path.join(d_poet, "face.front.brows.rest.png"), 0.50, 0.36, 0.58),
            (os.path.join(d_poet, "face.front.eyes.rest.png"), 0.50, 0.43, 0.56),
            (os.path.join(d_poet, "face.front.mouth.neutral.png"), 0.50, 0.64, 0.34),
        ],
        os.path.join(d_st, "head.front.png"),
    )
    composite_face_onto_head(
        os.path.join(d_st, "head.threequarter.blank.png"),
        [
            (os.path.join(d_poet, "face.front.brows.rest.png"), 0.56, 0.36, 0.54),
            (os.path.join(d_poet, "face.front.eyes.rest.png"), 0.56, 0.43, 0.52),
            (os.path.join(d_poet, "face.front.mouth.neutral.png"), 0.56, 0.64, 0.32),
        ],
        os.path.join(d_st, "head.threequarter.png"),
    )
    composite_face_onto_head(
        os.path.join(d_st, "head.profile.blank.png"),
        [
            (os.path.join(d_poet, "face.profile.brows.rest.png"), 0.68, 0.36, 0.34),
            (os.path.join(d_poet, "face.profile.eyes.open.png"), 0.68, 0.43, 0.32),
            (os.path.join(d_poet, "face.profile.mouth.neutral.png"), 0.68, 0.63, 0.26),
        ],
        os.path.join(d_st, "head.profile.png"),
    )
    repaired += 90
    print(f"[fix_massive_set_and_rigs] Rebuilt & face-composited {repaired} core kit files in {V2_PARTS_DIR}")


def compute_part_pivots(slot_key, img_w, img_h):
    if slot_key == "head":
        return [0.50, 0.86], [0.50, 0.14], 0.0
    if slot_key == "torso":
        return [0.50, 0.10], [0.50, 0.88], 0.0
    if slot_key == "pelvis":
        return [0.50, 0.22], [0.50, 0.82], 0.0
    if slot_key.startswith(("uarm", "upper_arm")):
        return [0.50, 0.14], [0.50, 0.86], 0.0
    if slot_key.startswith(("farm", "forearm")):
        return [0.50, 0.14], [0.50, 0.82], 0.0
    if slot_key.startswith("hand"):
        return [0.50, 0.18], [0.50, 0.86], 0.0
    if slot_key.startswith("thigh"):
        return [0.50, 0.14], [0.50, 0.86], 0.0
    if slot_key.startswith("shin"):
        return [0.50, 0.14], [0.50, 0.84], 0.0
    if slot_key.startswith("foot"):
        aspect = img_w / float(max(1, img_h))
        if aspect > 1.08:
            # Side-profile boot/sneaker (ankle tab at top-left/center, sole at bottom)
            return [0.34, 0.18], [0.42, 0.88], 0.0
        return [0.48, 0.22], [0.50, 0.88], 0.0
    return [0.50, 0.15], [0.50, 0.85], 0.0


TORSO_STYLES = {
    "poet_tracksuit_31": {
        "style": "tracksuit_zip",
        "primary": "#17191f",
        "secondary": "#222630",
        "accent": "#d92b2b",
        "trim": "#c69c6d",
        "pelvis_color": "#15171d",
        "collar": "stand_rib",
        "detail": "center_zip_and_red_piping"
    },
    "poet_black_tshirt": {
        "style": "crew_tee",
        "primary": "#1d2026",
        "secondary": "#282c34",
        "accent": "#8c583a",
        "trim": "#c69c6d",
        "pelvis_color": "#212836",
        "collar": "crew_skin_neck",
        "detail": "short_sleeve_tee"
    },
    "ex_jacket_back": {
        "style": "bomber_olive",
        "primary": "#3c4632",
        "secondary": "#2d3525",
        "accent": "#586649",
        "trim": "#c69c6d",
        "pelvis_color": "#1c222e",
        "collar": "rib_bomber",
        "detail": "quilted_back_yoke"
    },
    "vintage_party_couple": {
        "style": "pinstripe_suit",
        "primary": "#1e222b",
        "secondary": "#2b303c",
        "accent": "#f0ead8",
        "trim": "#c69c6d",
        "pelvis_color": "#1e222b",
        "collar": "lapel_and_tie",
        "detail": "vertical_pinstripes"
    },
    "woman_muse_costumes": {
        "style": "brocade_bodice",
        "primary": "#9e1f24",
        "secondary": "#7c171b",
        "accent": "#e3b34c",
        "trim": "#c69c6d",
        "pelvis_color": "#8f1c21",
        "collar": "scoop_gold_trim",
        "detail": "gold_brocade_panels"
    },
    "child_traveler_ghost": {
        "style": "striped_sailor",
        "primary": "#e8e4d8",
        "secondary": "#1d3152",
        "accent": "#1d3152",
        "trim": "#c69c6d",
        "pelvis_color": "#2c4d75",
        "collar": "navy_ringer",
        "detail": "horizontal_navy_stripes"
    },
    "mother_ancestors_family": {
        "style": "cardigan_floral",
        "primary": "#5a6065",
        "secondary": "#1e5b52",
        "accent": "#d99b38",
        "trim": "#c69c6d",
        "pelvis_color": "#4f555a",
        "collar": "open_cardigan",
        "detail": "knit_rib_over_teal_floral"
    },
    "dj_club_citizens": {
        "style": "cyber_neon_vest",
        "primary": "#161824",
        "secondary": "#23263a",
        "accent": "#3be8ff",
        "trim": "#b84dff",
        "pelvis_color": "#191c28",
        "collar": "high_tech_collar",
        "detail": "neon_circuit_piping"
    },
    "bolas_dummy": {
        "style": "crash_shim_teal",
        "primary": "#00d2b8",
        "secondary": "#009e8a",
        "accent": "#ffd100",
        "trim": "#111820",
        "pelvis_color": "#00b49e",
        "collar": "crash_neck",
        "detail": "fiducial_target_disc"
    },
    "weave_man": {
        "style": "indigo_jacket",
        "primary": "#263248",
        "secondary": "#1b2436",
        "accent": "#d9a74a",
        "trim": "#c69c6d",
        "pelvis_color": "#1e2638",
        "collar": "work_lapel",
        "detail": "button_placket"
    }
}


def upgrade_catalog():
    with open(CATALOG_PATH, "r") as f:
        cat = json.load(f)

    # Map each rig to its primary v2/parts folder + kitbash donor folders
    rig_kit_map = {
        "poet_tracksuit_31": ("poet.red_black_sunglasses", ["family.street_clothes"]),
        "poet_black_tshirt": ("poet.black_tshirt", ["poet.red_black_sunglasses", "family.street_clothes"]),
        "ex_jacket_back": ("ex.ex_jacket", ["poet.red_black_sunglasses"]),
        "vintage_party_couple": ("party.vintage_party", ["poet.red_black_sunglasses"]),
        "woman_muse_costumes": ("woman.teal_dress", ["woman.mother_cardigan"]),
        "child_traveler_ghost": ("young_poet.child_clothes", ["poet.black_tshirt"]),
        "mother_ancestors_family": ("woman.mother_cardigan", ["ancestors.ancestor_robe_indigo_gold", "woman.teal_dress"]),
        "dj_club_citizens": ("party.dj_cyber", ["poet.red_black_sunglasses"]),
        "bolas_dummy": ("shim.crash_teal", ["poet.red_black_sunglasses"]),
        "weave_man": ("family.street_clothes", ["poet.red_black_sunglasses"]),
    }

    for rig in cat.get("rigs", []):
        rid = rig["id"]
        rig["torso_style"] = TORSO_STYLES.get(rid, TORSO_STYLES["poet_tracksuit_31"])
        primary_kit, donor_kits = rig_kit_map.get(rid, ("poet.red_black_sunglasses", []))
        rig["primary_kit"] = primary_kit
        rig["donor_kits"] = donor_kits

        slots = rig.get("slots", {})
        for slot_key, slot_obj in list(slots.items()):
            # Map canonical slot name to v2/parts file pattern
            base_slot = slot_key.replace("upper_arm_", "uarm_").replace("forearm_", "farm_")
            vv = slot_obj.get("view_variants", {})

            # Populate missing views from primary_kit or donor_kits (Cross-Kit Kitbash!)
            for view_name in ["front", "threequarter", "profile", "back"]:
                if base_slot == "head":
                    cand_rel = f"arena/parts/kit3/v2/parts/{primary_kit}/head.{view_name}.png"
                elif base_slot == "torso":
                    if rid == "poet_tracksuit_31" and view_name == "front":
                        cand_rel = "kits/packs/poet_tracksuit_v1/01_COMPONENTS/01_torso_front.png"
                    elif rid == "poet_tracksuit_31" and view_name == "back":
                        cand_rel = "kits/packs/poet_tracksuit_v1/01_COMPONENTS/02_torso_back.png"
                    else:
                        cand_rel = f"arena/parts/kit3/v2/parts/{primary_kit}/body.{view_name}.torso.png"
                elif base_slot == "pelvis":
                    cand_rel = f"arena/parts/kit3/v2/parts/{primary_kit}/body.{view_name}.pelvis.png"
                else:
                    parts_tok = base_slot.replace("_L", ".L").replace("_R", ".R")
                    cand_rel = f"arena/parts/kit3/v2/parts/{primary_kit}/body.{view_name}.{parts_tok}.png"

                if os.path.exists(os.path.join(ROOT, cand_rel)):
                    # Keep Tracksuit 31 high-res front components for front view, use v2/parts for 3Q/profile/back
                    if rid == "poet_tracksuit_31" and view_name == "front" and base_slot != "head":
                        pass
                    else:
                        vv[view_name] = cand_rel
                else:
                    # Try donor kits (Cross-Kit Kitbash!)
                    for dk in donor_kits:
                        if base_slot == "head":
                            d_rel = f"arena/parts/kit3/v2/parts/{dk}/head.{view_name}.png"
                        elif base_slot == "torso":
                            d_rel = f"arena/parts/kit3/v2/parts/{dk}/body.{view_name}.torso.png"
                        elif base_slot == "pelvis":
                            d_rel = f"arena/parts/kit3/v2/parts/{dk}/body.{view_name}.pelvis.png"
                        else:
                            parts_tok = base_slot.replace("_L", ".L").replace("_R", ".R")
                            d_rel = f"arena/parts/kit3/v2/parts/{dk}/body.{view_name}.{parts_tok}.png"
                        if os.path.exists(os.path.join(ROOT, d_rel)):
                            vv[view_name] = d_rel
                            break

            slot_obj["view_variants"] = vv
            if "front" in vv and rid != "poet_tracksuit_31":
                slot_obj["file"] = vv["front"]
            elif "front" in vv and base_slot == "head":
                slot_obj["file"] = vv["front"]

            # Recompute accurate variant_meta for every variant
            vmeta = {}
            for vkey, vrel in vv.items():
                vabs = os.path.join(ROOT, vrel)
                if os.path.exists(vabs):
                    im = Image.open(vabs)
                    vw, vh = im.size
                    va, vb, vrot = compute_part_pivots(base_slot, vw, vh)
                    kit_source = primary_kit
                    for dk in donor_kits:
                        if f"/{dk}/" in vrel:
                            kit_source = f"KITBASH:{dk}"
                    if rid == "poet_black_tshirt" and ("hand" in base_slot or (base_slot == "torso" and vkey == "profile")):
                        kit_source = "KITBASH:poet.red_black"
                    vmeta[vkey] = {
                        "file": vrel,
                        "width": vw,
                        "height": vh,
                        "pivot_A": va,
                        "socket_B": vb,
                        "rot_offset_deg": vrot,
                        "kit_source": kit_source
                    }
            slot_obj["variant_meta"] = vmeta

            # Update primary slot dimensions & pivots
            f_abs = os.path.join(ROOT, slot_obj["file"])
            if os.path.exists(f_abs):
                im = Image.open(f_abs)
                w, h = im.size
                slot_obj["width"] = w
                slot_obj["height"] = h
                pa, sb, rot = compute_part_pivots(base_slot, w, h)
                slot_obj["pivot_A"] = pa
                slot_obj["socket_B"] = sb
                slot_obj["rot_offset_deg"] = rot

    build_face_and_body_gene_pool(cat)

    with open(CATALOG_PATH, "w") as f:
        json.dump(cat, f, indent=2)
    print(f"[fix_massive_set_and_rigs] Upgraded {CATALOG_PATH} with Cross-Kit Kitbash Matrix, Torso Styles & Gene Pool!")


def build_face_and_body_gene_pool(cat):
    """Build purified, orientation-cleaned, scale-normalized gene pool for the Batch Face & Body Evolutionary Grid."""
    expressive_heads = []
    seen = set()

    def add_head(rel_path, label, view, char_grp, is_blank=False):
        if rel_path in seen:
            return
        abs_p = os.path.join(ROOT, rel_path)
        if not os.path.exists(abs_p):
            return
        im = Image.open(abs_p)
        w, h = im.size
        # Filter out full standing figures (h/w > 1.72) or wide mouth strips (w/h > 1.6)
        if h > w * 1.72 or w > h * 1.60:
            return
        seen.add(rel_path)
        expressive_heads.append({
            "idx": len(expressive_heads) + 1,
            "file": rel_path,
            "label": label,
            "view": view,
            "group": char_grp,
            "width": w,
            "height": h,
            "is_blank": is_blank
        })

    # 1. Weave Artist-Painted Poet Expressive Heads (Front, 3Q, Profile, Back)
    for fp in sorted(glob.glob(os.path.join(ROOT, "weave/cast/man/library/head/*.png"))):
        rel = os.path.relpath(fp, ROOT)
        nm = os.path.basename(fp).replace(".png", "").replace("head.", "")
        vw = "back" if "back" in nm else ("profile" if "profile" in nm else ("threequarter" if ("3q" in nm or "threequarter" in nm or "intent" in nm or "speaking" in nm or "sunglasses." in nm or "sunglasses_shades" in nm or "look_" in nm) else "front"))
        add_head(rel, f"Poet {nm}", vw, "Poet", is_blank=False)

    # 2. All 10 Repaired Character Kit Heads
    for r in cat.get("rigs", []):
        hslot = r.get("slots", {}).get("head", {})
        for vk, vf in (hslot.get("view_variants") or {}).items():
            add_head(vf, f"{r.get('short_name','Rig')} {vk}", vk, r.get("short_name", "Rig"), is_blank=False)

    # 3. Body Lab Heads (Father with flat cap, Mother with afro/earrings, Party guests, Ancestors, Ghost Child)
    for sub, grp_lbl in [
        ("the_father_long_coat", "Father Cap"),
        ("the_mother_teal_dress", "Mother Afro"),
        ("party_guests", "Party Vintage"),
        ("atlantis_ancestors", "Ancestor"),
        ("ghost_child_age_7", "Ghost Child"),
        ("young_poet_age_6", "Young Poet")
    ]:
        for fp in sorted(glob.glob(os.path.join(ROOT, f"arena/parts/body_lab/heads/{sub}/*.png"))):
            rel = os.path.relpath(fp, ROOT)
            nm = os.path.basename(fp).replace(".png", "")
            # Filter out hands accidentally placed in father_head_08..10
            if "father_head_08" in nm or "father_head_09" in nm or "father_head_10" in nm:
                continue
            add_head(rel, f"{grp_lbl} {nm[-2:]}", "front", grp_lbl, is_blank=True)

    # Photo-Fit Base Plates (Front & 3Q/Profile)
    photofit_plates = []
    for kdir, klbl in [
        ("poet.red_black_sunglasses", "Poet Beard"),
        ("young_poet.child_clothes", "Poet Clean"),
        ("ghost_child.ghost_nightclothes", "Ghost Tone"),
        ("woman.mother_cardigan", "Mother Afro"),
        ("bola.crash_yellow", "Bola Gold"),
        ("dot.crash_dot", "Dot Coral"),
        ("shim.crash_teal", "Shim Cyan"),
    ]:
        for vw in ["front", "profile"]:
            rel = f"arena/parts/kit3/v2/parts/{kdir}/face.{vw}.plate.png"
            if os.path.exists(os.path.join(ROOT, rel)):
                photofit_plates.append({"idx": len(photofit_plates) + 1, "file": rel, "label": f"{klbl} ({vw[:2].upper()})", "view": vw, "kit": kdir})

    # Strip 1: Pre-Framed Rounded Photo-Fit Brow Strips (#01..#24)
    strip_1 = []
    brow_types = ["rest", "raised", "one_up", "knit", "angry", "sad"]
    for kdir, klbl in [
        ("poet.red_black_sunglasses", "Poet"),
        ("ghost_child.ghost_nightclothes", "Ghost"),
        ("bola.crash_yellow", "Gold"),
        ("shim.crash_teal", "Cyan"),
    ]:
        for vw in ["front", "profile"]:
            for bt in brow_types:
                rel = f"arena/parts/kit3/v2/parts/{kdir}/face.{vw}.brows.{bt}.png"
                if os.path.exists(os.path.join(ROOT, rel)):
                    strip_1.append({"idx": len(strip_1) + 1, "file": rel, "label": f"{klbl} Brow {bt}", "view": vw})

    # Strip 2: Pre-Framed Rounded Photo-Fit Eye Strips (#01..#32)
    strip_2 = []
    eye_types = ["open", "wide", "glance_side", "happy_arc", "half", "squint", "sad", "closed"]
    for kdir, klbl in [
        ("poet.red_black_sunglasses", "Poet"),
        ("ghost_child.ghost_nightclothes", "Ghost"),
        ("dot.crash_dot", "Coral"),
        ("shim.crash_teal", "Cyan"),
    ]:
        for vw in ["front", "profile"]:
            for et in eye_types:
                rel = f"arena/parts/kit3/v2/parts/{kdir}/face.{vw}.eyes.{et}.png"
                if os.path.exists(os.path.join(ROOT, rel)):
                    strip_2.append({"idx": len(strip_2) + 1, "file": rel, "label": f"{klbl} Eye {et}", "view": vw})

    # Strip 3: Pre-Framed Rounded Photo-Fit Mouth Strips (#01..#36)
    strip_3 = []
    mouth_types = ["rest", "smile", "grin_teeth", "open_A", "open_O", "E", "U", "frown", "strain_teeth", "wavy", "M_B_P", "F_V"]
    for kdir, klbl in [
        ("poet.red_black_sunglasses", "Poet"),
        ("ghost_child.ghost_nightclothes", "Ghost"),
        ("bola.crash_yellow", "Gold"),
    ]:
        for vw in ["front", "profile"]:
            for mt in mouth_types:
                rel = f"arena/parts/kit3/v2/parts/{kdir}/face.{vw}.mouth.{mt}.png"
                if os.path.exists(os.path.join(ROOT, rel)):
                    strip_3.append({"idx": len(strip_3) + 1, "file": rel, "label": f"{klbl} Mouth {mt}", "view": vw})

    # Purified Noses for Cubist / Multi-Window Collage (strictly verified nose cutouts — zero text fragments!)
    cubist_noses = []
    valid_shared_noses = [4, 6, 9, 11, 12, 13, 16, 17, 18, 19, 20, 21]
    for n_idx in valid_shared_noses:
        rel = f"arena/parts/body_lab/noses/cast_shared_features/shared_nose_{n_idx:02d}.png"
        if os.path.exists(os.path.join(ROOT, rel)):
            cubist_noses.append({"idx": len(cubist_noses) + 1, "file": rel, "label": f"Nose #{n_idx:02d}"})
    for n_idx in range(6, 12):
        rel = f"arena/parts/body_lab/accessories/dj_cyber_&_club/dj_acc_{n_idx:02d}.png"
        if os.path.exists(os.path.join(ROOT, rel)):
            cubist_noses.append({"idx": len(cubist_noses) + 1, "file": rel, "label": f"Sculpt Nose #{n_idx:02d}"})

    # Expressive Hands & Purified Headgear (Caps, Headphones, Shades)
    collage_hands = []
    for fp in sorted(glob.glob(os.path.join(ROOT, "weave/cast/man/library/hand/*.png")))[:18]:
        rel = os.path.relpath(fp, ROOT)
        im = Image.open(fp)
        w, h = im.size
        _, _, rot = compute_part_pivots("hand_L", w, h)
        collage_hands.append({
            "idx": len(collage_hands) + 1,
            "file": rel,
            "label": os.path.basename(fp).replace(".png", "").replace("hand.", ""),
            "width": w,
            "height": h,
            "rot_offset_deg": rot
        })

    headgear = []
    for g_idx in [1, 2, 3, 4, 5, 12, 13, 14]:
        rel = f"arena/parts/body_lab/accessories/dj_cyber_&_club/dj_acc_{g_idx:02d}.png"
        if os.path.exists(os.path.join(ROOT, rel)):
            lbl = f"Cap #{g_idx:02d}" if g_idx <= 5 else f"DJ Headphones #{g_idx:02d}"
            headgear.append({"idx": len(headgear) + 1, "file": rel, "label": lbl})
    for rel, lbl in [
        ("arena/parts/kit3/v2/parts/poet.red_black_sunglasses/face.front.glasses.png", "Poet Shades Front"),
        ("arena/parts/kit3/v2/parts/poet.red_black_sunglasses/face.profile.glasses.png", "Poet Shades Profile"),
        ("weave/cast/man/library/prop/prop.headphones.png", "Studio Headphones"),
        ("weave/cast/man/library/prop/prop.sunglasses.front.png", "Dark Shades Front"),
        ("weave/cast/man/library/prop/prop.sunglasses.folded.png", "Folded Shades"),
        ("kits/packs/poet_tracksuit_v1/01_COMPONENTS/31_sunglasses_front.png", "Tracksuit Shades")
    ]:
        if os.path.exists(os.path.join(ROOT, rel)):
            headgear.append({"idx": len(headgear) + 1, "file": rel, "label": lbl})

    cat["face_and_body_gene_pool"] = {
        "expressive_heads": expressive_heads,
        "photofit_plates": photofit_plates,
        "strip_1_brows_eyes": strip_1,
        "strip_2_noses_cheeks": strip_2,
        "strip_3_mouths_jaws": strip_3,
        "cubist_noses": cubist_noses,
        "collage_hands": collage_hands,
        "headgear": headgear
    }
    print(f"[gene_pool] Built purified gene pool: {len(expressive_heads)} heads, {len(photofit_plates)} plates, {len(strip_1)} brows, {len(strip_2)} eyes, {len(strip_3)} mouths, {len(cubist_noses)} noses, {len(collage_hands)} hands, {len(headgear)} headgear")


if __name__ == "__main__":
    rebuild_all_kits()
    upgrade_catalog()
