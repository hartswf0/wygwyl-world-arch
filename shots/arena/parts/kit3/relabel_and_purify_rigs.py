#!/usr/bin/env python3
"""
SCION — Autonomous Rig Relabeler & Torso/Pelvis/Foot Purifier
Fixes all mislabeled torsos, mechanical triangle pelvises, child denim shorts/thighs,
white opera glove leaks, and backward-pointing profile shoes across crash_lab_catalog.json.
"""
import json
import os
import shutil
from PIL import Image, ImageOps

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
    # Crop central 76% horizontally (removing the two wide outer shoulder grommet tabs) and compress horizontally to side-profile depth
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
    # Top 54% of p08 is the blue denim shorts; mirror-join L+R to form a symmetric child denim shorts pelvis cover!
    top_shorts = im.crop((0, 0, w, int(h * 0.54)))
    sw, sh = top_shorts.size
    pel = Image.new("RGBA", (int(sw * 1.65), sh), (0, 0, 0, 0))
    pel.paste(top_shorts, (0, 0), top_shorts)
    flipped = ImageOps.mirror(top_shorts)
    pel.paste(flipped, (int(sw * 0.65), 0), flipped)
    pel.save(dst_p)
    return dst_rel


def main():
    with open(CATALOG_PATH, "r") as f:
        cat = json.load(f)

    # 1. Generate true narrow side-profile torsos for poet.black_tshirt and ex.ex_jacket
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

    # 2. Create child denim shorts pelvis cover from young_poet.child_clothes.body.front__p08.png
    child_pelvis_rel = make_child_denim_pelvis(
        "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p08.png",
        "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.front.pelvis.denim.png",
    )

    # 3. Also copy ancestor indigo/gold real pelvis & boots into v2/parts/ancestors.ancestor_robe_indigo_gold
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

    def update_slot_dims(slot_obj):
        rel = slot_obj.get("file")
        if not rel:
            return
        fp = os.path.join(ROOT, rel)
        if os.path.exists(fp):
            with Image.open(fp) as im:
                slot_obj["width"], slot_obj["height"] = im.size

    fixed_count = 0
    for rig in cat.get("rigs", []):
        rid = rig["id"]
        slots = rig.get("slots", {})

        if rid == "poet_black_tshirt":
            # Fix profile torso variant (was wide front tee) & back pelvis (was 3-grommet yoke strip)
            t = slots.get("torso", {})
            if "view_variants" in t:
                t["view_variants"]["profile"] = poet_prof_torso
            p = slots.get("pelvis", {})
            if "view_variants" in p:
                p["view_variants"]["back"] = "arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.pelvis.png"
            fixed_count += 1

        elif rid == "ex_jacket_back":
            # Fix profile torso variant & broken miniature-figure back pelvis
            t = slots.get("torso", {})
            if "view_variants" in t:
                t["view_variants"]["profile"] = ex_prof_torso
            p = slots.get("pelvis", {})
            p["file"] = "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.front.pelvis.png"
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.front.pelvis.png",
                "profile": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.front.pelvis.png",
                "back": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.front.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.front.pelvis.png",
            }
            update_slot_dims(p)
            fixed_count += 1

        elif rid == "vintage_party_couple":
            # Replace mechanical 3-grommet hip yoke strip (188x109) with actual pinstriped suit pelvis (162x126 / 189x222)
            p = slots.get("pelvis", {})
            p["file"] = "arena/parts/kit3/v2/parts/party.vintage_party/body.back.pelvis.png"
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/party.vintage_party/body.back.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/party.vintage_party/body.back.pelvis.png",
                "profile": "arena/parts/kit3/v2/parts/party.vintage_party/body.profile.pelvis.png",
                "back": "arena/parts/kit3/v2/parts/party.vintage_party/body.back.pelvis.png",
            }
            update_slot_dims(p)
            # Replace sleeve-attached hands (73x228) with clean hands
            for h_slot, sfx in [("hand_L", "L"), ("hand_R", "R")]:
                if h_slot in slots:
                    slots[h_slot]["file"] = f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.{sfx}.png"
                    slots[h_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.{sfx}.png",
                        "profile": f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.{sfx}.png",
                    }
                    update_slot_dims(slots[h_slot])
            # Use clean front dress shoes for front view and side oxford (198x160) for profile view
            for f_slot, sfx in [("foot_L", "L"), ("foot_R", "R")]:
                if f_slot in slots:
                    slots[f_slot]["file"] = f"arena/parts/kit3/v2/parts/family.street_clothes/body.front.foot.{sfx}.png"
                    slots[f_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/family.street_clothes/body.front.foot.{sfx}.png",
                        "threequarter": f"arena/parts/kit3/v2/parts/party.vintage_party/body.profile.foot.{sfx}.png",
                        "profile": f"arena/parts/kit3/v2/parts/party.vintage_party/body.profile.foot.{sfx}.png",
                        "back": f"arena/parts/kit3/v2/parts/family.street_clothes/body.back.foot.{sfx}.png",
                    }
                    update_slot_dims(slots[f_slot])
            fixed_count += 1

        elif rid == "woman_muse_costumes":
            # Replace cardboard triangle pelvis (185x184) with actual red floral pelvis/skirt cover (230x181 & 246x293)
            p = slots.get("pelvis", {})
            p["file"] = "arena/parts/kit3/v2/parts/woman.teal_dress/body.back.pelvis.png"
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/woman.teal_dress/body.back.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.pelvis.png",
                "profile": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.profile.pelvis.png",
                "back": "arena/parts/kit3/v2/parts/woman.teal_dress/body.back.pelvis.png",
            }
            update_slot_dims(p)
            # Replace misplaced white opera glove (70x219) with natural warm brown hands
            for h_slot, sfx in [("hand_L", "L"), ("hand_R", "R")]:
                if h_slot in slots:
                    slots[h_slot]["file"] = f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.{sfx}.png"
                    slots[h_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.{sfx}.png",
                        "profile": f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.{sfx}.png",
                    }
                    update_slot_dims(slots[h_slot])
            # Fix backward-pointing left Mary-Jane shoe (foot.L was pointing -X; foot.R points +X!)
            right_shoe = "arena/parts/kit3/v2/parts/woman.teal_dress/body.front.foot.R.png"
            for f_slot in ["foot_L", "foot_R"]:
                if f_slot in slots:
                    slots[f_slot]["file"] = right_shoe
                    slots[f_slot]["view_variants"] = {
                        "front": right_shoe,
                        "threequarter": right_shoe,
                        "profile": right_shoe,
                        "back": right_shoe,
                    }
                    update_slot_dims(slots[f_slot])
            fixed_count += 1

        elif rid == "child_traveler_ghost":
            # Fix giant hand in pelvis slot (180x229) -> real child denim shorts pelvis cover!
            p = slots.get("pelvis", {})
            if child_pelvis_rel:
                p["file"] = child_pelvis_rel
                p["view_variants"] = {
                    "front": child_pelvis_rel,
                    "threequarter": child_pelvis_rel,
                    "profile": child_pelvis_rel,
                    "back": child_pelvis_rel,
                }
                update_slot_dims(p)
            # Fix child thighs to use the actual denim shorts + thigh cuts (p08, p10, profile p05)!
            thL_front = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p08.png"
            thR_front = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p10.png"
            th_prof = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p05.png"
            if "thigh_L" in slots:
                slots["thigh_L"]["file"] = thL_front
                slots["thigh_L"]["view_variants"] = {"front": thL_front, "threequarter": thL_front, "profile": th_prof, "back": thL_front}
                update_slot_dims(slots["thigh_L"])
            if "thigh_R" in slots:
                slots["thigh_R"]["file"] = thR_front
                slots["thigh_R"]["view_variants"] = {"front": thR_front, "threequarter": thR_front, "profile": th_prof, "back": thR_front}
                update_slot_dims(slots["thigh_R"])
            # Fix child forearms to use bare forearms (p03, p05, profile p03) instead of repeating the striped upper arm!
            faL_front = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p03.png"
            faR_front = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p05.png"
            fa_prof = "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p03.png"
            if "farm_L" in slots:
                slots["farm_L"]["file"] = faL_front
                slots["farm_L"]["view_variants"] = {"front": faL_front, "threequarter": faL_front, "profile": fa_prof, "back": faL_front}
                update_slot_dims(slots["farm_L"])
            if "farm_R" in slots:
                slots["farm_R"]["file"] = faR_front
                slots["farm_R"]["view_variants"] = {"front": faR_front, "threequarter": faR_front, "profile": fa_prof, "back": faR_front}
                update_slot_dims(slots["farm_R"])
            fixed_count += 1

        elif rid == "mother_ancestors_family":
            # Replace cardboard triangle pelvis (188x164) with Mother's knit pelvis cover (body.back.pelvis.png 196x192)
            p = slots.get("pelvis", {})
            p["file"] = "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.pelvis.png"
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.pelvis.png",
                "profile": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.pelvis.png",
                "back": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.pelvis.png",
            }
            update_slot_dims(p)
            # Replace misplaced white opera glove (70x219) with natural warm hands
            for h_slot, sfx in [("hand_L", "L"), ("hand_R", "R")]:
                if h_slot in slots:
                    slots[h_slot]["file"] = f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.{sfx}.png"
                    slots[h_slot]["view_variants"] = {
                        "front": f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.{sfx}.png",
                        "profile": f"arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.hand.{sfx}.png",
                    }
                    update_slot_dims(slots[h_slot])
            # Add Mother's true side-profile slipper (woman.09.mother.body__p20.png 219x134)
            prof_slipper_L = "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p20.png"
            prof_slipper_R = "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p21.png"
            if "foot_L" in slots:
                slots["foot_L"]["view_variants"]["profile"] = prof_slipper_L
                slots["foot_L"]["view_variants"]["threequarter"] = prof_slipper_L
            if "foot_R" in slots:
                slots["foot_R"]["view_variants"]["profile"] = prof_slipper_R
                slots["foot_R"]["view_variants"]["threequarter"] = prof_slipper_R
            fixed_count += 1

        elif rid == "dj_club_citizens":
            # Replace black mechanical triangle pelvis (363x251) with actual black cargo shorts pelvis (body.back.pelvis.png 388x257)
            p = slots.get("pelvis", {})
            p["file"] = "arena/parts/kit3/v2/parts/party.dj_cyber/body.back.pelvis.png"
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/party.dj_cyber/body.back.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/party.dj_cyber/body.back.pelvis.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p09.png",
                "back": "arena/parts/kit3/v2/parts/party.dj_cyber/body.back.pelvis.png",
            }
            update_slot_dims(p)
            # Replace faceless beard silhouette head with expressive club/DJ head
            dj_head_front = "arena/parts/kit3/v2/parts/party.club_jacket/head.front.png"
            dj_head_prof = "arena/parts/kit3/v2/parts/party.club_jacket/head.profile.png"
            if "head" in slots and os.path.exists(os.path.join(ROOT, dj_head_front)):
                slots["head"]["file"] = dj_head_front
                slots["head"]["view_variants"]["front"] = dj_head_front
                if os.path.exists(os.path.join(ROOT, dj_head_prof)):
                    slots["head"]["view_variants"]["profile"] = dj_head_prof
                update_slot_dims(slots["head"])
            fixed_count += 1

        elif rid == "weave_man":
            # Fix family.street_clothes profile/back pelvis (which were mislabeled thighs 178x306)
            p = slots.get("pelvis", {})
            p["view_variants"] = {
                "front": "arena/parts/kit3/v2/parts/family.street_clothes/body.front.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/family.street_clothes/body.threequarter.pelvis.png",
                "profile": "arena/parts/kit3/v2/parts/family.street_clothes/body.front.pelvis.png",
                "back": "arena/parts/kit3/v2/parts/family.street_clothes/body.threequarter.pelvis.png",
            }
            fixed_count += 1

    # Also purify swapper_bank.torsos_pelvis so no mechanical triangle armatures or mislabeled hands appear
    sb = cat.get("swapper_bank", {})
    if "torsos_pelvis" in sb:
        cleaned_tp = []
        for item in sb["torsos_pelvis"]:
            fl = item.get("file", "")
            if "young_poet.child_clothes/body.front.pelvis.png" in fl:
                item["file"] = child_pelvis_rel or fl
                item["name"] = "Child Denim Shorts Pelvis"
            elif "woman.teal_dress/body.front.pelvis.png" in fl:
                item["file"] = "arena/parts/kit3/v2/parts/woman.teal_dress/body.back.pelvis.png"
                item["name"] = "Woman Red Floral Pelvis Cover"
            elif "woman.mother_cardigan/body.front.pelvis.png" in fl:
                item["file"] = "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.back.pelvis.png"
                item["name"] = "Mother Knit Skirt Pelvis"
            elif "party.dj_cyber/body.front.pelvis.png" in fl:
                item["file"] = "arena/parts/kit3/v2/parts/party.dj_cyber/body.back.pelvis.png"
                item["name"] = "DJ Cyber Cargo Shorts Pelvis"
            elif "party.vintage_party/body.front.pelvis.png" in fl:
                item["file"] = "arena/parts/kit3/v2/parts/party.vintage_party/body.back.pelvis.png"
                item["name"] = "Vintage Pinstripe Suit Pelvis"
            cleaned_tp.append(item)
        # Add the authentic Teal Dress torso & pelvis from v2/cut/woman.teal_dress.body.profile/
        cleaned_tp.append({
            "id": "teal_dress_true_torso",
            "name": "Woman True Teal Dress Torso",
            "character_group": "Woman / Muse",
            "clip_tag": "Torso / Dress",
            "file": "arena/parts/kit3/v2/cut/woman.teal_dress.body.profile/part_02.png",
            "width": 303,
            "height": 494,
            "normalized_cm_scale": 0.14,
            "pivot_A": [0.5, 0.88],
            "socket_B": [0.5, 0.12],
        })
        cleaned_tp.append({
            "id": "teal_dress_true_pelvis",
            "name": "Woman True Teal Pelvis Brief",
            "character_group": "Woman / Muse",
            "clip_tag": "Pelvis / Hip Bridge",
            "file": "arena/parts/kit3/v2/cut/woman.teal_dress.body.profile/part_09.png",
            "width": 272,
            "height": 201,
            "normalized_cm_scale": 0.12,
            "pivot_A": [0.5, 0.25],
            "socket_B": [0.5, 0.85],
        })
        sb["torsos_pelvis"] = cleaned_tp

    with open(CATALOG_PATH, "w") as f:
        json.dump(cat, f, indent=2)
    print(f"Purified and relabeled {fixed_count} rigs in {CATALOG_PATH}")


if __name__ == "__main__":
    main()
