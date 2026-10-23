#!/usr/bin/env python3
"""
SCION — Autonomous Rig Relabeler, Hand/Foot View Normalizer & Torso/Pelvis Purifier
Fixes:
1. Mislabeled torsos (true side-profile torsos for poet_black_tshirt and ex_jacket_back)
2. Mechanical triangle pelvises & hand-in-pelvis bugs across all 10 rigs
3. Upside-down child hands (young_poet.child_clothes) & authentic slender female hands for Woman/Mother
4. Front-view vs. 3/4-view vs. Side-profile shoes (ensuring all front shoes face 0° front and all profile/3Q shoes point +X right with calibrated ankle pivot_A)
5. Synchronizes `variant_meta` with `view_variants` across all 15 slots of all 10 rigs so stale pivots never override relabeled assets.
"""
import json
import os
import shutil
from PIL import Image, ImageOps, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
CATALOG_PATH = os.path.join(ROOT, "arena/parts/kit3/release_v2/crash_lab_catalog.json")


def make_true_profile_torso(src_rel, dst_rel, aspect_target=0.58):
    """Creates a true narrow side-profile torso from a front/back vest when a distinct side cut is missing."""
    src_p = os.path.join(ROOT, src_rel)
    dst_p = os.path.join(ROOT, dst_rel)
    if not os.path.exists(src_p):
        return src_rel
    im = Image.open(src_p).convert("RGBA")
    w, h = im.size
    x0 = int(w * 0.12)
    x1 = int(w * 0.88)
    cropped = im.crop((x0, 0, x1, h))
    new_w = max(80, int(h * aspect_target))
    prof = cropped.resize((new_w, h), Image.Resampling.LANCZOS)
    prof.save(dst_p)
    return dst_rel


def make_child_denim_pelvis(src_rel, dst_rel):
    """Extracts a clean denim shorts pelvis cover from young_poet.child_clothes.body.front__p08.png."""
    src_p = os.path.join(ROOT, src_rel)
    dst_p = os.path.join(ROOT, dst_rel)
    if not os.path.exists(src_p):
        return None
    im = Image.open(src_p).convert("RGBA")
    w, h = im.size
    top_shorts = im.crop((0, 0, w, int(h * 0.54)))
    sw, sh = top_shorts.size
    pel = Image.new("RGBA", (int(sw * 1.65), sh), (0, 0, 0, 0))
    pel.paste(top_shorts, (0, 0), top_shorts)
    flipped = ImageOps.mirror(top_shorts)
    pel.paste(flipped, (int(sw * 0.65), 0), flipped)
    pel.save(dst_p)
    return dst_rel


def make_upright_hand(src_rel, dst_rel, rotate_180=True, mirror_x=False):
    """Copies a hand asset, optionally rotating 180 deg if its wrist grommet was at the bottom."""
    src_p = os.path.join(ROOT, src_rel)
    dst_p = os.path.join(ROOT, dst_rel)
    if not os.path.exists(src_p):
        return src_rel
    im = Image.open(src_p).convert("RGBA")
    if rotate_180:
        im = im.rotate(180, expand=True)
    if mirror_x:
        im = ImageOps.mirror(im)
    im.save(dst_p)
    return dst_rel


def make_red_front_shoe(src_rel, dst_rel):
    """Tints woman.teal_dress/foot.R.front.png (174x329) to match her crimson/gold Mary-Jane palette."""
    src_p = os.path.join(ROOT, src_rel)
    dst_p = os.path.join(ROOT, dst_rel)
    if not os.path.exists(src_p):
        return src_rel
    im = Image.open(src_p).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 15:
                continue
            # Preserve tan kraft border and top grommet tab (y < 0.25) and sole (y > 0.86)
            if y > h * 0.24 and y < h * 0.86 and r < 110 and g < 110 and b < 115:
                nr = min(235, int(r * 2.1 + 95))
                ng = max(18, int(g * 0.65))
                nb = max(18, int(b * 0.60))
                px[x, y] = (nr, ng, nb, a)
    im.save(dst_p)
    return dst_rel


def sync_slot_and_variant_meta(slot_obj, slot_key):
    """Synchronizes slot_obj dimensions and rebuilds variant_meta so every view_variant has accurate pivots and dimensions."""
    vv = slot_obj.get("view_variants", {})
    if not vv and slot_obj.get("file"):
        vv = {"front": slot_obj["file"]}
        slot_obj["view_variants"] = vv

    is_foot = slot_key.startswith("foot_")
    is_hand = slot_key.startswith("hand_")
    is_head = slot_key == "head"
    is_torso = slot_key == "torso"
    is_pelvis = slot_key == "pelvis"

    new_vm = {}
    for vk, rel_path in list(vv.items()):
        if not rel_path:
            continue
        fp = os.path.join(ROOT, rel_path)
        w, h = slot_obj.get("width", 200), slot_obj.get("height", 200)
        if os.path.exists(fp):
            with Image.open(fp) as im:
                w, h = im.size

        # Calibrate view-specific pivot_A and socket_B
        if is_foot:
            if vk in ("profile", "threequarter") or (w > h * 1.05):
                # Right-pointing (+X) profile/3Q shoe: ankle shaft is on upper-left [0.30, 0.22], sole directly below ankle [0.30, 0.86] so thetaCard = +90 deg!
                if "19_boot" in rel_path or "20_boot" in rel_path:
                    pA, sB = [0.32, 0.25], [0.32, 0.86]
                elif "foot.R.threequarter" in rel_path or "foot.L.threequarter" in rel_path:
                    pA, sB = [0.28, 0.22], [0.28, 0.86]
                else:
                    pA, sB = [0.30, 0.22], [0.30, 0.86]
                top_clip = 0.18
            else:
                # Front / Back vertical shoe: centered [0.50, 0.22] -> [0.50, 0.88]
                pA, sB = [0.50, 0.22], [0.50, 0.88]
                top_clip = 0.18
        elif is_hand:
            if w > h * 1.15:
                # Horizontal hand (e.g. 74x43)
                pA, sB = [0.22, 0.48], [0.88, 0.48]
                top_clip = 0.0
            elif "young_poet.child_clothes/body.profile.hand" in rel_path:
                # Child profile hand curves slightly right toward bottom
                pA, sB = [0.38, 0.20], [0.58, 0.86]
                top_clip = 0.18
            else:
                # Vertical upright hand: wrist crease at y=0.22 (clipping top grommet tab y<0.18), fingertips at y=0.88
                pA, sB = [0.50, 0.22], [0.50, 0.88]
                top_clip = 0.18
        elif is_head:
            pA, sB = [0.50, 0.86], [0.50, 0.14]
            top_clip = 0.0
        elif is_torso:
            pA, sB = [0.50, 0.10], [0.50, 0.88]
            top_clip = 0.0
        elif is_pelvis:
            pA, sB = [0.50, 0.20], [0.50, 0.84]
            top_clip = 0.0
        elif slot_key.startswith("thigh_") or slot_key.startswith("uarm_"):
            pA = slot_obj.get("pivot_A", [0.50, 0.16])
            sB = slot_obj.get("socket_B", [0.50, 0.84])
            top_clip = 0.10
        else:
            pA = slot_obj.get("pivot_A", [0.50, 0.16])
            sB = slot_obj.get("socket_B", [0.50, 0.84])
            top_clip = 0.0

        new_vm[vk] = {
            "file": rel_path,
            "width": w,
            "height": h,
            "pivot_A": pA,
            "socket_B": sB,
            "rot_offset_deg": 0.0,
            "cuff_clip_ratio": slot_obj.get("cuff_clip_ratio", 1.0),
            "top_clip_ratio": top_clip,
        }

    slot_obj["variant_meta"] = new_vm
    # Set primary slot file & metadata from 'front' (or first available)
    prim_vk = "front" if "front" in new_vm else (next(iter(new_vm.keys()), None))
    if prim_vk and prim_vk in new_vm:
        pm = new_vm[prim_vk]
        slot_obj["file"] = pm["file"]
        slot_obj["width"] = pm["width"]
        slot_obj["height"] = pm["height"]
        slot_obj["pivot_A"] = pm["pivot_A"]
        slot_obj["socket_B"] = pm["socket_B"]
        slot_obj["rot_offset_deg"] = 0.0
        slot_obj["top_clip_ratio"] = pm["top_clip_ratio"]


def main():
    with open(CATALOG_PATH, "r") as f:
        cat = json.load(f)

    # 1. Generate true narrow side-profile torsos for poet.black_tshirt and ex.ex_jacket, plus narrow pelvises for weave_man
    poet_prof_torso = make_true_profile_torso(
        "arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.torso.png",
        "arena/parts/kit3/v2/parts/poet.black_tshirt/body.profile.torso.true.png",
        aspect_target=0.58,
    )
    ex_prof_torso = make_true_profile_torso(
        "arena/parts/kit3/v2/parts/ex.ex_jacket/body.back.torso.png",
        "arena/parts/kit3/v2/parts/ex.ex_jacket/body.profile.torso.true.png",
        aspect_target=0.60,
    )
    weave_prof_pelvis = make_true_profile_torso(
        "arena/parts/kit3/v2/parts/family.street_clothes/body.front.pelvis.png",
        "arena/parts/kit3/v2/parts/family.street_clothes/body.profile.pelvis.true.png",
        aspect_target=0.88,
    )
    weave_3q_pelvis = make_true_profile_torso(
        "arena/parts/kit3/v2/parts/family.street_clothes/body.front.pelvis.png",
        "arena/parts/kit3/v2/parts/family.street_clothes/body.threequarter.pelvis.true.png",
        aspect_target=1.18,
    )
    poet_bt_prof_pelvis = make_true_profile_torso(
        "arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.pelvis.png",
        "arena/parts/kit3/v2/parts/poet.black_tshirt/body.profile.pelvis.true.png",
        aspect_target=0.88,
    )
    ex_prof_pelvis = make_true_profile_torso(
        "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.front.pelvis.png",
        "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.profile.pelvis.true.png",
        aspect_target=0.95,
    )

    # 2. Create child denim shorts pelvis cover from young_poet.child_clothes.body.front__p08.png
    child_pelvis_rel = make_child_denim_pelvis(
        "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p08.png",
        "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.front.pelvis.denim.png",
    )

    # 3. Create upright Child hands (rotating upside-down p06/p07 180 deg so wrist grommet is at top y=0.18!)
    child_hand_front_L = make_upright_hand(
        "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p06.png",
        "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.front.hand.up.L.png",
        rotate_180=True,
        mirror_x=False,
    )
    child_hand_front_R = make_upright_hand(
        "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p07.png",
        "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.front.hand.up.R.png",
        rotate_180=True,
        mirror_x=False,
    )
    # Also overwrite body.front.hand.L.png and R.png directly so any direct loader gets the upright hand!
    shutil.copyfile(
        os.path.join(ROOT, child_hand_front_L),
        os.path.join(ROOT, "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.front.hand.L.png"),
    )
    shutil.copyfile(
        os.path.join(ROOT, child_hand_front_R),
        os.path.join(ROOT, "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.front.hand.R.png"),
    )

    # 4. Create upright Woman / Mother graceful hands from woman.13.heads-hands__p18.png (front open) and p20.png (profile/3Q)
    woman_hand_front_L = make_upright_hand(
        "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p18.png",
        "arena/parts/kit3/v2/parts/woman.teal_dress/body.front.hand.true.L.png",
        rotate_180=False,
        mirror_x=False,
    )
    woman_hand_front_R = make_upright_hand(
        "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p18.png",
        "arena/parts/kit3/v2/parts/woman.teal_dress/body.front.hand.true.R.png",
        rotate_180=False,
        mirror_x=True,
    )
    woman_hand_prof_L = make_upright_hand(
        "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p20.png",
        "arena/parts/kit3/v2/parts/woman.teal_dress/body.profile.hand.true.L.png",
        rotate_180=False,
        mirror_x=False,
    )
    woman_hand_prof_R = make_upright_hand(
        "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p20.png",
        "arena/parts/kit3/v2/parts/woman.teal_dress/body.profile.hand.true.R.png",
        rotate_180=False,
        mirror_x=True,
    )

    # 5. Create Woman front-view red shoe to match her red Mary-Jane profile shoes
    woman_front_shoe = make_red_front_shoe(
        "arena/parts/kit3/v2/parts/woman.teal_dress/foot.R.front.png",
        "arena/parts/kit3/v2/parts/woman.teal_dress/body.front.foot.true.png",
    )

    # 5b. Create Child expressive slot-free heads (front, threequarter, profile, back) from atlantis.06.child_traveler.heads-hands
    cut_ct = os.path.join(ROOT, "arena/parts/kit3/release_v2/cuts/atlantis.06.child_traveler.heads-hands")
    yp_dst = os.path.join(ROOT, "arena/parts/kit3/v2/parts/young_poet.child_clothes")
    child_head_front = "arena/parts/kit3/v2/parts/young_poet.child_clothes/head.front.true.png"
    child_head_3q = "arena/parts/kit3/v2/parts/young_poet.child_clothes/head.threequarter.true.png"
    child_head_prof = "arena/parts/kit3/v2/parts/young_poet.child_clothes/head.profile.true.png"
    child_head_back = "arena/parts/kit3/release_v2/cuts/atlantis.06.child_traveler.heads-hands/atlantis.06.child_traveler.heads-hands__p05.png"
    if os.path.exists(cut_ct) and os.path.exists(yp_dst):
        p01 = Image.open(os.path.join(cut_ct, "atlantis.06.child_traveler.heads-hands__p01.png")).convert("RGBA")
        p02 = Image.open(os.path.join(cut_ct, "atlantis.06.child_traveler.heads-hands__p02.png")).convert("RGBA")
        p03 = Image.open(os.path.join(cut_ct, "atlantis.06.child_traveler.heads-hands__p03.png")).convert("RGBA")
        eyeL = Image.open(os.path.join(cut_ct, "atlantis.06.child_traveler.heads-hands__p08.png")).convert("RGBA").resize((36, 23), Image.Resampling.LANCZOS)
        eyeR = Image.open(os.path.join(cut_ct, "atlantis.06.child_traveler.heads-hands__p09.png")).convert("RGBA").resize((36, 23), Image.Resampling.LANCZOS)
        browL = Image.open(os.path.join(cut_ct, "atlantis.06.child_traveler.heads-hands__p10.png")).convert("RGBA").resize((38, 16), Image.Resampling.LANCZOS)
        browR = Image.open(os.path.join(cut_ct, "atlantis.06.child_traveler.heads-hands__p11.png")).convert("RGBA").resize((38, 16), Image.Resampling.LANCZOS)
        mouth = Image.open(os.path.join(cut_ct, "atlantis.06.child_traveler.heads-hands__p17.png")).convert("RGBA").resize((42, 19), Image.Resampling.LANCZOS)

        f_im = p01.copy()
        f_im.paste(browL, (62, 102), browL)
        f_im.paste(browR, (110, 102), browR)
        f_im.paste(eyeL, (63, 117), eyeL)
        f_im.paste(eyeR, (110, 117), eyeR)
        f_im.paste(mouth, (84, 164), mouth)
        f_im.save(os.path.join(ROOT, child_head_front))

        tq_im = p02.copy()
        tq_im.paste(browL, (95, 100), browL)
        tq_im.paste(browR.resize((28, 15), Image.Resampling.LANCZOS), (144, 102), browR.resize((28, 15), Image.Resampling.LANCZOS))
        tq_im.paste(eyeL, (96, 115), eyeL)
        tq_im.paste(eyeR.resize((28, 21), Image.Resampling.LANCZOS), (145, 116), eyeR.resize((28, 21), Image.Resampling.LANCZOS))
        tq_im.paste(mouth.resize((34, 17), Image.Resampling.LANCZOS), (125, 164), mouth.resize((34, 17), Image.Resampling.LANCZOS))
        tq_im.save(os.path.join(ROOT, child_head_3q))

        pr_im = p03.copy()
        pr_im.paste(browL.resize((34, 15), Image.Resampling.LANCZOS), (118, 102), browL.resize((34, 15), Image.Resampling.LANCZOS))
        pr_im.paste(eyeL.resize((32, 21), Image.Resampling.LANCZOS), (120, 117), eyeL.resize((32, 21), Image.Resampling.LANCZOS))
        pr_im.paste(mouth.resize((22, 14), Image.Resampling.LANCZOS), (146, 164), mouth.resize((22, 14), Image.Resampling.LANCZOS))
        pr_im.save(os.path.join(ROOT, child_head_prof))

    # 6. Copy ancestor indigo/gold real pelvis & boots into v2/parts/ancestors.ancestor_robe_indigo_gold
    anc_cut = os.path.join(ROOT, "arena/parts/kit3/release_v2/cuts/ancestors.05.ancestor_robe_indigo_gold.body")
    anc_dst = os.path.join(ROOT, "arena/parts/kit3/v2/parts/ancestors.ancestor_robe_indigo_gold")
    if os.path.exists(anc_cut) and os.path.exists(anc_dst):
        shutil.copyfile(
            os.path.join(anc_cut, "ancestors.05.ancestor_robe_indigo_gold.body__p09.png"),
            os.path.join(anc_dst, "body.front.pelvis.png"),
        )
        shutil.copyfile(
            os.path.join(anc_cut, "ancestors.05.ancestor_robe_indigo_gold.body__p18.png"),
            os.path.join(anc_dst, "body.front.foot.L.png"),
        )
        shutil.copyfile(
            os.path.join(anc_cut, "ancestors.05.ancestor_robe_indigo_gold.body__p19.png"),
            os.path.join(anc_dst, "body.front.foot.R.png"),
        )
        shutil.copyfile(
            os.path.join(anc_cut, "ancestors.05.ancestor_robe_indigo_gold.body__p20.png"),
            os.path.join(anc_dst, "body.profile.foot.L.png"),
        )
        shutil.copyfile(
            os.path.join(anc_cut, "ancestors.05.ancestor_robe_indigo_gold.body__p21.png"),
            os.path.join(anc_dst, "body.profile.foot.R.png"),
        )

    fixed_count = 0
    for rig in cat.get("rigs", []):
        rid = rig["id"]
        slots = rig.get("slots", {})

        if rid == "poet_tracksuit_31":
            if "head" in slots:
                slots["head"]["view_variants"]["front"] = "weave/cast/man/library/head/head.front.sunglasses.png"
                slots["head"]["view_variants"]["profile"] = "weave/cast/man/library/misc/body_profile_01.png"
                slots["head"]["view_variants"]["threequarter"] = "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/head.threequarter.png"
            # Ensure both foot_L and foot_R point +X in profile/3Q and face 0 deg front in front/back
            for f_slot, f_front in [
                ("foot_L", "kits/packs/poet_tracksuit_v1/01_COMPONENTS/19_boot_front_L.png"),
                ("foot_R", "kits/packs/poet_tracksuit_v1/01_COMPONENTS/20_boot_front_R.png"),
            ]:
                if f_slot in slots:
                    slots[f_slot]["view_variants"] = {
                        "front": f_front,
                        "threequarter": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.threequarter.foot.L.png",
                        "profile": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.profile.foot.L.png",
                        "back": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.back.foot.L.png",
                    }
            fixed_count += 1

        elif rid == "poet_black_tshirt":
            if "head" in slots:
                slots["head"]["view_variants"]["front"] = "weave/cast/man/library/head/head.front.neutral.png"
                slots["head"]["view_variants"]["threequarter"] = "weave/cast/man/library/head/head.threequarter_R.neutral.png"
                slots["head"]["view_variants"]["profile"] = "weave/cast/man/library/head/head.profile_R.neutral.png"
            t = slots.get("torso", {})
            if "view_variants" in t:
                t["view_variants"]["profile"] = poet_prof_torso
            p = slots.get("pelvis", {})
            if "view_variants" in p:
                p["view_variants"]["profile"] = poet_bt_prof_pelvis
                p["view_variants"]["back"] = "arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.pelvis.png"
            # True front-view sneakers (`foot.R.front.png` 174x329) for front/back, and right-pointing (`+X`) `body.profile.foot.L.png` (199x125) for BOTH foot_L and foot_R in profile!
            for f_slot in ["foot_L", "foot_R"]:
                if f_slot in slots:
                    slots[f_slot]["view_variants"] = {
                        "front": "arena/parts/kit3/v2/parts/poet.black_tshirt/foot.R.front.png",
                        "threequarter": "arena/parts/kit3/v2/parts/poet.black_tshirt/foot.R.threequarter.png",
                        "profile": "arena/parts/kit3/v2/parts/poet.black_tshirt/body.profile.foot.L.png",
                        "back": "arena/parts/kit3/v2/parts/poet.black_tshirt/foot.R.back.png",
                    }
            fixed_count += 1

        elif rid == "ex_jacket_back":
            t = slots.get("torso", {})
            if "view_variants" in t:
                t["view_variants"]["profile"] = ex_prof_torso
            p = slots.get("pelvis", {})
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.front.pelvis.png",
                "profile": ex_prof_pelvis,
                "back": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.front.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.front.pelvis.png",
                "threequarter_back": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.front.pelvis.png",
            }
            # True front/back white sneakers (`foot.R.front.png` / `foot.R.back.png` 174x329) for front/back, and right-pointing (`+X`) `body.profile.foot.L.png` (203x158) for BOTH foot_L and foot_R in profile!
            for f_slot in ["foot_L", "foot_R"]:
                if f_slot in slots:
                    slots[f_slot]["view_variants"] = {
                        "front": "arena/parts/kit3/v2/parts/ex.ex_jacket/foot.R.front.png",
                        "back": "arena/parts/kit3/v2/parts/ex.ex_jacket/foot.R.back.png",
                        "threequarter": "arena/parts/kit3/v2/parts/ex.ex_jacket/body.profile.foot.L.png",
                        "threequarter_back": "arena/parts/kit3/v2/parts/ex.ex_jacket/body.profile.foot.L.png",
                        "profile": "arena/parts/kit3/v2/parts/ex.ex_jacket/body.profile.foot.L.png",
                    }
            fixed_count += 1

        elif rid == "vintage_party_couple":
            if "head" in slots:
                slots["head"]["view_variants"]["front"] = "weave/cast/man/library/head/head.front.small_smile.png"
                slots["head"]["view_variants"]["threequarter"] = "weave/cast/man/library/head/head.3q.recognition.png"
                slots["head"]["view_variants"]["profile"] = "weave/cast/man/library/head/head.profile_R.neutral.png"
            p = slots.get("pelvis", {})
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/party.vintage_party/body.back.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/party.vintage_party/body.back.pelvis.png",
                "profile": "arena/parts/kit3/v2/parts/party.vintage_party/body.profile.pelvis.png",
                "back": "arena/parts/kit3/v2/parts/party.vintage_party/body.back.pelvis.png",
            }
            for h_slot, sfx in [("hand_L", "L"), ("hand_R", "R")]:
                if h_slot in slots:
                    slots[h_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.{sfx}.png",
                        "threequarter": f"arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.profile.hand.{sfx}.png",
                        "profile": f"arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.profile.hand.{sfx}.png",
                        "back": f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.back.hand.{sfx}.png",
                    }
            for f_slot, sfx in [("foot_L", "L"), ("foot_R", "R")]:
                if f_slot in slots:
                    slots[f_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/family.street_clothes/body.front.foot.{sfx}.png",
                        "threequarter": "arena/parts/kit3/v2/parts/party.vintage_party/body.profile.foot.L.png",
                        "profile": "arena/parts/kit3/v2/parts/party.vintage_party/body.profile.foot.L.png",
                        "back": f"arena/parts/kit3/v2/parts/family.street_clothes/body.back.foot.{sfx}.png",
                    }
            fixed_count += 1

        elif rid == "woman_muse_costumes":
            if "head" in slots:
                slots["head"]["view_variants"]["profile"] = "arena/parts/kit3/v2/parts/woman.window_woman_dress/head.profile.png"
                slots["head"]["view_variants"]["threequarter"] = "arena/parts/kit3/v2/parts/woman.window_woman_dress/head.threequarter.png"
            p = slots.get("pelvis", {})
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/woman.teal_dress/body.back.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.pelvis.png",
                "profile": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.profile.pelvis.png",
                "back": "arena/parts/kit3/v2/parts/woman.teal_dress/body.back.pelvis.png",
            }
            if "hand_L" in slots:
                slots["hand_L"]["view_variants"] = {
                    "front": woman_hand_front_L,
                    "threequarter": woman_hand_prof_L,
                    "profile": woman_hand_prof_L,
                    "back": woman_hand_front_L,
                }
            if "hand_R" in slots:
                slots["hand_R"]["view_variants"] = {
                    "front": woman_hand_front_R,
                    "threequarter": woman_hand_prof_R,
                    "profile": woman_hand_prof_R,
                    "back": woman_hand_front_R,
                }
            right_mary_jane = "arena/parts/kit3/v2/parts/woman.teal_dress/body.front.foot.R.png"
            for f_slot in ["foot_L", "foot_R"]:
                if f_slot in slots:
                    slots[f_slot]["view_variants"] = {
                        "front": woman_front_shoe,
                        "threequarter": right_mary_jane,
                        "profile": right_mary_jane,
                        "back": woman_front_shoe,
                    }
            fixed_count += 1

        elif rid == "child_traveler_ghost":
            if "head" in slots:
                slots["head"]["view_variants"] = {
                    "front": child_head_front,
                    "threequarter": child_head_3q,
                    "profile": child_head_prof,
                    "back": child_head_back,
                }
            p = slots.get("pelvis", {})
            if child_pelvis_rel:
                p["view_variants"] = {
                    "front": child_pelvis_rel,
                    "threequarter": child_pelvis_rel,
                    "profile": child_pelvis_rel,
                    "back": child_pelvis_rel,
                }
            thL_front = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p08.png"
            thR_front = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p10.png"
            th_prof = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p05.png"
            if "thigh_L" in slots:
                slots["thigh_L"]["view_variants"] = {"front": thL_front, "threequarter": thL_front, "profile": th_prof, "back": thL_front}
            if "thigh_R" in slots:
                slots["thigh_R"]["view_variants"] = {"front": thR_front, "threequarter": thR_front, "profile": th_prof, "back": thR_front}
            faL_front = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p03.png"
            faR_front = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p05.png"
            fa_prof = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p03.png"
            if "farm_L" in slots:
                slots["farm_L"]["view_variants"] = {"front": faL_front, "threequarter": faL_front, "profile": fa_prof, "back": faL_front}
            if "farm_R" in slots:
                slots["farm_R"]["view_variants"] = {"front": faR_front, "threequarter": faR_front, "profile": fa_prof, "back": faR_front}
            # Fix upside-down front/back hands on child_traveler_ghost!
            if "hand_L" in slots:
                slots["hand_L"]["view_variants"] = {
                    "front": child_hand_front_L,
                    "threequarter": "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.threequarter.hand.L.png",
                    "profile": "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.profile.hand.L.png",
                    "back": child_hand_front_L,
                }
            if "hand_R" in slots:
                slots["hand_R"]["view_variants"] = {
                    "front": child_hand_front_R,
                    "threequarter": "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.threequarter.hand.R.png",
                    "profile": "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.profile.hand.R.png",
                    "back": child_hand_front_R,
                }
            for f_slot, sfx in [("foot_L", "L"), ("foot_R", "R")]:
                if f_slot in slots:
                    slots[f_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/young_poet.child_clothes/body.front.foot.{sfx}.png",
                        "threequarter": "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.threequarter.foot.L.png",
                        "profile": "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.profile.foot.L.png",
                        "back": f"arena/parts/kit3/v2/parts/young_poet.child_clothes/body.back.foot.{sfx}.png",
                    }
            fixed_count += 1

        elif rid == "mother_ancestors_family":
            if "head" in slots:
                slots["head"]["view_variants"]["front"] = "arena/parts/kit3/v2/parts/woman.teal_dress/head.front.png"
                slots["head"]["view_variants"]["profile"] = "arena/parts/kit3/v2/parts/party.club_dress/head.profile.png"
                slots["head"]["view_variants"]["threequarter"] = "arena/parts/kit3/v2/parts/party.club_dress/head.threequarter.png"
            p = slots.get("pelvis", {})
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.pelvis.png",
                "profile": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.pelvis.png",
                "back": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.pelvis.png",
            }
            if "hand_L" in slots:
                slots["hand_L"]["view_variants"] = {
                    "front": woman_hand_front_L,
                    "threequarter": woman_hand_prof_L,
                    "profile": woman_hand_prof_L,
                    "back": woman_hand_front_L,
                }
            if "hand_R" in slots:
                slots["hand_R"]["view_variants"] = {
                    "front": woman_hand_front_R,
                    "threequarter": woman_hand_prof_R,
                    "profile": woman_hand_prof_R,
                    "back": woman_hand_front_R,
                }
            # Both foot_L and foot_R in profile/3Q must point +X (p20 is side profile +X, p18 is 3Q +X; p21/p19 point -X!)
            prof_slipper_right = "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p20.png"
            tq_slipper_right = "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p18.png"
            for f_slot, sfx in [("foot_L", "L"), ("foot_R", "R")]:
                if f_slot in slots:
                    slots[f_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/woman.mother_cardigan/body.front.foot.{sfx}.png",
                        "threequarter": tq_slipper_right,
                        "profile": prof_slipper_right,
                        "back": f"arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.foot.{sfx}.png",
                    }
            fixed_count += 1

        elif rid == "dj_club_citizens":
            p = slots.get("pelvis", {})
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/party.dj_cyber/body.back.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/party.dj_cyber/body.back.pelvis.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p09.png",
                "back": "arena/parts/kit3/v2/parts/party.dj_cyber/body.back.pelvis.png",
            }
            if "head" in slots:
                slots["head"]["view_variants"]["front"] = "weave/cast/man/library/head/head.front.sunglasses.png"
                slots["head"]["view_variants"]["threequarter"] = "weave/cast/man/library/head/head.sunglasses_shades.png"
                slots["head"]["view_variants"]["profile"] = "weave/cast/man/library/head/head.profile_R.neutral.png"
            # Fix DJ Cyber shoes: use true front-facing boots in front/back, and right-pointing (+X) neon sneakers in profile & 3Q!
            for f_slot, sfx in [("foot_L", "L"), ("foot_R", "R")]:
                if f_slot in slots:
                    slots[f_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/family.street_clothes/body.front.foot.{sfx}.png",
                        "threequarter": "arena/parts/kit3/v2/parts/party.dj_cyber/body.profile.foot.L.png",
                        "profile": "arena/parts/kit3/v2/parts/party.dj_cyber/body.profile.foot.L.png",
                        "back": f"arena/parts/kit3/v2/parts/family.street_clothes/body.back.foot.{sfx}.png",
                    }
            fixed_count += 1

        elif rid == "bolas_dummy":
            # Fix bolas_dummy profile hand & profile foot (was mismatched poet leather boot on R and heel-pinned boot on L!)
            if "hand_R" in slots:
                slots["hand_R"]["view_variants"]["profile"] = "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.hand.R.png"
            for f_slot, sfx in [("foot_L", "L"), ("foot_R", "R")]:
                if f_slot in slots:
                    slots[f_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/shim.crash_teal/body.front.foot.{sfx}.png",
                        "threequarter": f"arena/parts/kit3/v2/parts/shim.crash_teal/body.threequarter.foot.{sfx}.png",
                        "profile": f"arena/parts/kit3/v2/parts/shim.crash_teal/body.threequarter.foot.{sfx}.png",
                        "back": f"arena/parts/kit3/v2/parts/shim.crash_teal/body.back.foot.{sfx}.png",
                    }
            fixed_count += 1

        elif rid == "weave_man":
            if "head" in slots:
                slots["head"]["view_variants"]["front"] = "weave/cast/man/library/head/head.front.neutral.png"
                slots["head"]["view_variants"]["profile"] = "weave/cast/man/library/head/head.profile_R.neutral.png"
                slots["head"]["view_variants"]["threequarter"] = "weave/cast/man/library/head/head.threequarter_R.neutral.png"
            p = slots.get("pelvis", {})
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/family.street_clothes/body.front.pelvis.png",
                "threequarter": weave_3q_pelvis,
                "profile": weave_prof_pelvis,
                "back": weave_3q_pelvis,
            }
            for f_slot, sfx in [("foot_L", "L"), ("foot_R", "R")]:
                if f_slot in slots:
                    slots[f_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/family.street_clothes/body.front.foot.{sfx}.png",
                        "threequarter": "arena/parts/kit3/v2/parts/family.street_clothes/body.profile.foot.L.png",
                        "profile": "arena/parts/kit3/v2/parts/family.street_clothes/body.profile.foot.L.png",
                        "back": f"arena/parts/kit3/v2/parts/family.street_clothes/body.back.foot.{sfx}.png",
                    }
            fixed_count += 1

        # Synchronize variant_meta across all slots of this rig!
        for sk, slot_obj in slots.items():
            sync_slot_and_variant_meta(slot_obj, sk)

    with open(CATALOG_PATH, "w") as f:
        json.dump(cat, f, indent=2)
    print(f"Purified, view-normalized, and synced variant_meta across {fixed_count} rigs in {CATALOG_PATH}")


if __name__ == "__main__":
    main()
