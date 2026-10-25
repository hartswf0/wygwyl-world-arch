import os, json
import numpy as np
from PIL import Image, ImageDraw

BASE = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots"

def trim_white_sheet_border(rel_path):
    """Remove any bright white paper margin strips along the edges of a cut piece."""
    full = os.path.join(BASE, rel_path)
    if not os.path.exists(full):
        return
    im = Image.open(full).convert("RGBA")
    arr = np.array(im)
    r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]
    # Detect near-white paper margin pixels (r>215, g>215, b>210) near left/right/top/bottom edges
    h, w = a.shape
    edge_mask = np.zeros((h, w), dtype=bool)
    margin_x = max(18, int(w * 0.14))
    margin_y = max(18, int(h * 0.08))
    edge_mask[:, :margin_x] = True
    edge_mask[:, w - margin_x:] = True
    edge_mask[:margin_y, :] = True
    edge_mask[h - margin_y:, :] = True
    white_px = (r > 205) & (g > 205) & (b > 198) & edge_mask
    if np.any(white_px):
        arr[white_px, 3] = 0
        # Also feather 1px next to removed white border
        im_clean = Image.fromarray(arr)
        bbox = im_clean.getbbox()
        if bbox:
            im_clean = im_clean.crop(bbox)
        im_clean.save(full)
        print(f"Cleaned white border on {rel_path} -> {im_clean.size}")

def make_profile_crop(src_rel, dst_rel, width_ratio=0.56):
    src = os.path.join(BASE, src_rel)
    dst = os.path.join(BASE, dst_rel)
    im = Image.open(src).convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    nw = max(48, int(round(w * width_ratio)))
    # Take center-right slice to preserve garment texture & border without squishing grommets
    x0 = int((w - nw) * 0.45)
    cropped = im.crop((x0, 0, x0 + nw, h))
    # Softly round the cut left/right vertical edges by 4px so it looks like a natural cutout
    arr = np.array(cropped)
    for dx in range(4):
        factor = (dx + 1) / 5.0
        arr[:, dx, 3] = (arr[:, dx, 3].astype(float) * factor).astype(np.uint8)
        arr[:, nw - 1 - dx, 3] = (arr[:, nw - 1 - dx, 3].astype(float) * factor).astype(np.uint8)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    Image.fromarray(arr).save(dst)
    print(f"Created profile crop {dst_rel} ({nw}x{h}) from {src_rel} ({w}x{h})")

def make_shim_pelvis():
    """Create matte-black crash-test pelvis pieces matching shim.crash_teal thighs."""
    thigh_p = os.path.join(BASE, "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.thigh.L.png")
    im_t = Image.open(thigh_p).convert("RGBA")
    # Sample center texture from thigh
    tw, th = im_t.size
    patch = im_t.crop((int(tw*0.2), int(th*0.25), int(tw*0.8), int(th*0.75)))
    for name, (pw, ph) in [
        ("body.front.pelvis.png", (190, 145)),
        ("body.threequarter.pelvis.png", (175, 145)),
        ("body.profile.pelvis.png", (118, 145)),
        ("body.back.pelvis.png", (190, 145)),
    ]:
        tex = patch.resize((pw, ph), Image.Resampling.LANCZOS)
        mask = Image.new("L", (pw, ph), 0)
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle([4, 4, pw - 5, ph - 5], radius=24, fill=255)
        out = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        out.paste(tex, (0, 0), mask)
        # Subtle kraft/teal rim to match shim.crash_teal
        d_out = ImageDraw.Draw(out)
        d_out.rounded_rectangle([4, 4, pw - 5, ph - 5], radius=24, outline=(85, 82, 74, 220), width=2)
        dst = os.path.join(BASE, "arena/parts/kit3/v2/parts/shim.crash_teal", name)
        out.save(dst)
        print("Created shim pelvis:", name, (pw, ph))

# 1. Clean white borders on family.street_clothes profile pieces
for fn in ["body.profile.torso.png", "body.profile.uarm.L.png", "body.profile.farm.L.png", "body.profile.thigh.L.png", "body.profile.shin.L.png"]:
    trim_white_sheet_border(f"arena/parts/kit3/v2/parts/family.street_clothes/{fn}")

# 2. Generate non-squished profile pelvis/skirt crops
make_profile_crop(
    "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.hipcore/young_poet.child_clothes.hipcore__p04.png",
    "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.profile.pelvis.denim.true.png",
    width_ratio=0.52
)
make_profile_crop(
    "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.hipcore/ex.ex_jacket.hipcore__p03.png",
    "arena/parts/kit3/v2/parts/ex.ex_jacket/body.profile.pelvis.true.png",
    width_ratio=0.52
)
make_profile_crop(
    "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p14.png",
    "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.profile.skirt.brocade.png",
    width_ratio=0.62
)
make_profile_crop(
    "arena/parts/kit3/v2/parts/poet.black_tshirt/body.front.torso.png",
    "arena/parts/kit3/v2/parts/poet.black_tshirt/body.profile.torso.true.png",
    width_ratio=0.58
)
make_shim_pelvis()

# 3. Define verified slot overrides for all Problem Rigs
RIG_OVERRIDES = {
    "poet_tracksuit_31": {
        "head": {
            "file": "weave/cast/man/parts/head.front.png",
            "view_variants": {
                "front": "weave/cast/man/parts/head.front.png",
                "threequarter": "weave/cast/man/parts/head.threequarter_R.png",
                "profile": "weave/cast/man/parts/head.profile_R.png",
                "back": "weave/cast/man/parts/head.back.png"
            }
        },
        "torso": {
            "file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/01_torso_front.png",
            "view_variants": {
                "front": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/01_torso_front.png",
                "threequarter": "arena/parts/kit3/v2/parts/poet.red_black_sunglasses/body.threequarter.torso.png",
                "profile": "weave/cast/man/parts/torso.profile.png",
                "back": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/02_torso_back.png"
            }
        },
        "pelvis": {
            "file": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/06_pelvis_front_cover.png",
            "view_variants": {
                "front": "kits/packs/poet_tracksuit_v1/01_COMPONENTS/06_pelvis_front_cover.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.hipcore/poet.red_black_sunglasses.hipcore__p03.png",
                "profile": "arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.hipcore/poet.red_black_sunglasses.hipcore__p04.png",
                "back": "arena/parts/kit3/release_v2/cuts/poet.red_black_sunglasses.hipcore/poet.red_black_sunglasses.hipcore__p03.png"
            }
        }
    },
    "child_traveler_ghost": {
        "torso": {
            "file": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p01.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p01.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.threequarter/young_poet.child_clothes.body.threequarter__p01.png",
                "profile": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.hipcore/young_poet.child_clothes.hipcore__p03.png",
                "back": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.back/young_poet.child_clothes.body.back__p01.png"
            }
        },
        "pelvis": {
            "file": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.hipcore/young_poet.child_clothes.hipcore__p04.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.hipcore/young_poet.child_clothes.hipcore__p04.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.hipcore/young_poet.child_clothes.hipcore__p04.png",
                "profile": "arena/parts/kit3/v2/parts/young_poet.child_clothes/body.profile.pelvis.denim.true.png",
                "back": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.hipcore/young_poet.child_clothes.hipcore__p04.png"
            }
        },
        "uarm_L": {
            "file": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p02.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p02.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.threequarter/young_poet.child_clothes.body.threequarter__p02.png",
                "profile": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p02.png",
                "back": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.back/young_poet.child_clothes.body.back__p02.png"
            }
        },
        "uarm_R": {
            "file": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p04.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p04.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.threequarter/young_poet.child_clothes.body.threequarter__p03.png",
                "profile": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p02.png",
                "back": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.back/young_poet.child_clothes.body.back__p03.png"
            }
        },
        "farm_L": {
            "file": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p03.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p03.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.threequarter/young_poet.child_clothes.body.threequarter__p04.png",
                "profile": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p03.png",
                "back": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.back/young_poet.child_clothes.body.back__p04.png"
            }
        },
        "farm_R": {
            "file": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p05.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p05.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.threequarter/young_poet.child_clothes.body.threequarter__p05.png",
                "profile": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p03.png",
                "back": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.back/young_poet.child_clothes.body.back__p05.png"
            }
        },
        "thigh_L": {
            "file": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p08.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p08.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.threequarter/young_poet.child_clothes.body.threequarter__p08.png",
                "profile": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p05.png",
                "back": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.back/young_poet.child_clothes.body.back__p08.png"
            }
        },
        "thigh_R": {
            "file": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p10.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p10.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.threequarter/young_poet.child_clothes.body.threequarter__p10.png",
                "profile": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p05.png",
                "back": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.back/young_poet.child_clothes.body.back__p10.png"
            }
        },
        "shin_L": {
            "file": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p09.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p09.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.threequarter/young_poet.child_clothes.body.threequarter__p09.png",
                "profile": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p06.png",
                "back": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.back/young_poet.child_clothes.body.back__p09.png"
            }
        },
        "shin_R": {
            "file": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p11.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.front/young_poet.child_clothes.body.front__p11.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.threequarter/young_poet.child_clothes.body.threequarter__p11.png",
                "profile": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.profile/young_poet.child_clothes.body.profile__p06.png",
                "back": "arena/parts/kit3/release_v2/cuts/young_poet.child_clothes.body.back/young_poet.child_clothes.body.back__p11.png"
            }
        }
    },
    "ex_jacket_back": {
        "torso": {
            "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p01.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p01.png",
                "back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p01.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p01.png",
                "threequarter_back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p01.png",
                "profile": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.hipcore/ex.ex_jacket.hipcore__p02.png"
            }
        },
        "pelvis": {
            "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.hipcore/ex.ex_jacket.hipcore__p03.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.hipcore/ex.ex_jacket.hipcore__p03.png",
                "back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.hipcore/ex.ex_jacket.hipcore__p03.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.hipcore/ex.ex_jacket.hipcore__p03.png",
                "threequarter_back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.hipcore/ex.ex_jacket.hipcore__p03.png",
                "profile": "arena/parts/kit3/v2/parts/ex.ex_jacket/body.profile.pelvis.true.png"
            }
        },
        "uarm_L": {
            "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p02.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p02.png",
                "back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p02.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p04.png",
                "threequarter_back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p04.png",
                "profile": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p04.png"
            }
        },
        "uarm_R": {
            "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p03.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p03.png",
                "back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p03.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p05.png",
                "threequarter_back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p05.png",
                "profile": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p05.png"
            }
        },
        "farm_L": {
            "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p04.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p04.png",
                "back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p04.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p02.png",
                "threequarter_back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p02.png",
                "profile": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p02.png"
            }
        },
        "farm_R": {
            "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p05.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p05.png",
                "back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p05.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p03.png",
                "threequarter_back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p03.png",
                "profile": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p03.png"
            }
        },
        "thigh_L": {
            "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p08.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p08.png",
                "back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p08.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p09.png",
                "threequarter_back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p09.png",
                "profile": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p09.png"
            }
        },
        "thigh_R": {
            "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p10.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p10.png",
                "back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p10.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p10.png",
                "threequarter_back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p10.png",
                "profile": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p10.png"
            }
        },
        "shin_L": {
            "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p09.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p09.png",
                "back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p09.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p11.png",
                "threequarter_back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p11.png",
                "profile": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p11.png"
            }
        },
        "shin_R": {
            "file": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p11.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p11.png",
                "back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.back/ex.ex_jacket.body.back__p11.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p12.png",
                "threequarter_back": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p12.png",
                "profile": "arena/parts/kit3/release_v2/cuts/ex.ex_jacket.body.threequarter_back/ex.ex_jacket.body.threequarter_back__p12.png"
            }
        }
    },
    "woman_muse_costumes": {
        "head": {
            "file": "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p06.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p06.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p07.png",
                "profile": "arena/parts/kit3/v2/parts/woman.window_woman_dress/head.profile.png",
                "back": "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p05.png"
            }
        },
        "torso": {
            "file": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p01.png",
            "girth": 1.24,
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p01.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p01.png",
                "profile": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p03.png",
                "back": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p02.png"
            }
        },
        "pelvis": {
            "file": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.pelvis.png",
            "view_variants": {
                "front": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.pelvis.png",
                "profile": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.profile.pelvis.png",
                "back": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.pelvis.png"
            }
        },
        "uarm_L": {
            "file": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.uarm.L.png",
            "girth": 0.85,
            "view_variants": {
                "front": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.uarm.L.png",
                "threequarter": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.threequarter.uarm.L.png",
                "profile": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.profile.uarm.L.png",
                "back": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.back.uarm.L.png"
            }
        },
        "uarm_R": {
            "file": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.uarm.R.png",
            "girth": 0.85,
            "view_variants": {
                "front": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.uarm.R.png",
                "threequarter": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.threequarter.uarm.R.png",
                "profile": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.profile.uarm.L.png",
                "back": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.back.uarm.R.png"
            }
        },
        "farm_L": {
            "file": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.farm.L.png",
            "girth": 0.85,
            "view_variants": {
                "front": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.farm.L.png",
                "threequarter": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.threequarter.farm.L.png",
                "profile": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.profile.farm.L.png",
                "back": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.back.farm.L.png"
            }
        },
        "farm_R": {
            "file": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.farm.R.png",
            "girth": 0.85,
            "view_variants": {
                "front": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.front.farm.R.png",
                "threequarter": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.threequarter.farm.R.png",
                "profile": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.profile.farm.L.png",
                "back": "arena/parts/kit3/v2/parts/woman.window_woman_dress/body.back.farm.R.png"
            }
        },
        "foot_L": {
            "file": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p16.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p16.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p17.png",
                "profile": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p17.png",
                "back": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p16.png"
            }
        },
        "foot_R": {
            "file": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p16.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p16.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p17.png",
                "profile": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p17.png",
                "back": "arena/parts/kit3/release_v2/cuts/woman.13.body/woman.13.body__p16.png"
            }
        }
    },
    "weave_man": {
        "head": {
            "file": "weave/cast/man/library/head/head.front.small_smile.png",
            "view_variants": {
                "front": "weave/cast/man/library/head/head.front.small_smile.png",
                "threequarter": "weave/cast/man/library/head/head.intent.listening.png",
                "profile": "weave/cast/man/library/head/head.profile_R.neutral.png",
                "back": "weave/cast/man/library/head/head.back.neutral.png"
            }
        },
        "torso": {
            "file": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p01.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p01.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p01.png",
                "profile": "arena/parts/kit3/release_v2/cuts/family.street_clothes.hipcore/family.street_clothes.hipcore__p05.png",
                "back": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.back/family.street_clothes.body.back__p01.png"
            }
        },
        "pelvis": {
            "file": "arena/parts/kit3/release_v2/cuts/family.street_clothes.hipcore/family.street_clothes.hipcore__p03.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/family.street_clothes.hipcore/family.street_clothes.hipcore__p03.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/family.street_clothes.hipcore/family.street_clothes.hipcore__p03.png",
                "profile": "arena/parts/kit3/release_v2/cuts/family.street_clothes.hipcore/family.street_clothes.hipcore__p06.png",
                "back": "arena/parts/kit3/release_v2/cuts/family.street_clothes.hipcore/family.street_clothes.hipcore__p03.png"
            }
        },
        "uarm_L": {
            "file": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p02.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p02.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p02.png",
                "profile": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p02.png",
                "back": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.back/family.street_clothes.body.back__p02.png"
            }
        },
        "uarm_R": {
            "file": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p03.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p03.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p03.png",
                "profile": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p03.png",
                "back": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.back/family.street_clothes.body.back__p03.png"
            }
        },
        "farm_L": {
            "file": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p04.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p04.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p04.png",
                "profile": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p04.png",
                "back": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.back/family.street_clothes.body.back__p04.png"
            }
        },
        "farm_R": {
            "file": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p05.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p05.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p05.png",
                "profile": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p05.png",
                "back": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.back/family.street_clothes.body.back__p05.png"
            }
        },
        "thigh_L": {
            "file": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p08.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p08.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p08.png",
                "profile": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p08.png",
                "back": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.back/family.street_clothes.body.back__p08.png"
            }
        },
        "thigh_R": {
            "file": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p09.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p09.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p09.png",
                "profile": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p09.png",
                "back": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.back/family.street_clothes.body.back__p09.png"
            }
        },
        "shin_L": {
            "file": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p10.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p10.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p10.png",
                "profile": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p10.png",
                "back": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.back/family.street_clothes.body.back__p10.png"
            }
        },
        "shin_R": {
            "file": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p11.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p11.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p11.png",
                "profile": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.front/family.street_clothes.body.front__p11.png",
                "back": "arena/parts/kit3/release_v2/cuts/family.street_clothes.body.back/family.street_clothes.body.back__p11.png"
            }
        }
    },
    "mother_ancestors_family": {
        "head": {
            "file": "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p06.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p06.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/woman.13.heads-hands/woman.13.heads-hands__p07.png",
                "profile": "arena/parts/kit3/v2/parts/woman.window_woman_dress/head.profile.png",
                "back": "arena/parts/kit3/release_v2/cuts/woman.09.mother.heads-hands/woman.09.mother.heads-hands__p05.png"
            }
        },
        "torso": {
            "file": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p01.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p01.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p01.png",
                "profile": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p03.png",
                "back": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p02.png"
            }
        },
        "pelvis": {
            "file": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p14.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p14.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p14.png",
                "profile": "arena/parts/kit3/v2/parts/woman.mother_cardigan/body.profile.skirt.brocade.png",
                "back": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p15.png"
            }
        },
        "foot_L": {
            "file": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p16.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p16.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p18.png",
                "profile": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p20.png",
                "back": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p17.png"
            }
        },
        "foot_R": {
            "file": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p17.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p17.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p19.png",
                "profile": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p20.png",
                "back": "arena/parts/kit3/release_v2/cuts/woman.09.mother.body/woman.09.mother.body__p16.png"
            }
        }
    },
    "bolas_dummy": {
        "pelvis": {
            "file": "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.pelvis.png",
            "view_variants": {
                "front": "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.pelvis.png",
                "threequarter": "arena/parts/kit3/v2/parts/shim.crash_teal/body.threequarter.pelvis.png",
                "profile": "arena/parts/kit3/v2/parts/shim.crash_teal/body.profile.pelvis.png",
                "back": "arena/parts/kit3/v2/parts/shim.crash_teal/body.back.pelvis.png"
            }
        },
        "uarm_R": {
            "file": "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.uarm.R.png",
            "view_variants": {
                "front": "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.uarm.R.png",
                "threequarter": "arena/parts/kit3/v2/parts/shim.crash_teal/body.threequarter.uarm.R.png",
                "profile": "arena/parts/kit3/v2/parts/shim.crash_teal/body.profile.uarm.L.png",
                "back": "arena/parts/kit3/v2/parts/shim.crash_teal/body.back.uarm.R.png"
            }
        },
        "farm_R": {
            "file": "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.farm.R.png",
            "view_variants": {
                "front": "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.farm.R.png",
                "threequarter": "arena/parts/kit3/v2/parts/shim.crash_teal/body.threequarter.farm.R.png",
                "profile": "arena/parts/kit3/v2/parts/shim.crash_teal/body.profile.farm.L.png",
                "back": "arena/parts/kit3/v2/parts/shim.crash_teal/body.back.farm.R.png"
            }
        },
        "thigh_R": {
            "file": "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.thigh.R.png",
            "view_variants": {
                "front": "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.thigh.R.png",
                "threequarter": "arena/parts/kit3/v2/parts/shim.crash_teal/body.threequarter.thigh.R.png",
                "profile": "arena/parts/kit3/v2/parts/shim.crash_teal/body.profile.thigh.L.png",
                "back": "arena/parts/kit3/v2/parts/shim.crash_teal/body.back.thigh.R.png"
            }
        },
        "shin_R": {
            "file": "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.shin.R.png",
            "view_variants": {
                "front": "arena/parts/kit3/v2/parts/shim.crash_teal/body.front.shin.R.png",
                "threequarter": "arena/parts/kit3/v2/parts/shim.crash_teal/body.threequarter.shin.R.png",
                "profile": "arena/parts/kit3/v2/parts/shim.crash_teal/body.profile.shin.L.png",
                "back": "arena/parts/kit3/v2/parts/shim.crash_teal/body.back.shin.R.png"
            }
        }
    },
    "dj_club_citizens": {
        "head": {
            "file": "weave/cast/man/parts/head.front.png",
            "view_variants": {
                "front": "weave/cast/man/parts/head.front.png",
                "threequarter": "weave/cast/man/library/head/head.sunglasses_shades.png",
                "profile": "weave/cast/man/parts/head.profile_R.png",
                "back": "weave/cast/man/parts/head.back.png"
            }
        },
        "torso": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p01.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p01.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p01.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p01.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p02.png"
            }
        },
        "pelvis": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p03.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p03.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p03.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p08.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p03.png"
            }
        },
        "uarm_L": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p02.png",
            "girth": 0.90,
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p02.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p02.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p02.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p02.png"
            }
        },
        "uarm_R": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p02.png",
            "girth": 0.90,
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p02.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p02.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p02.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p02.png"
            }
        },
        "farm_L": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p03.png",
            "girth": 0.88,
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p03.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p03.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p03.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p03.png"
            }
        },
        "farm_R": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p03.png",
            "girth": 0.88,
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p03.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p03.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p03.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p03.png"
            }
        },
        "thigh_L": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p09.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p09.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p09.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p04.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p09.png"
            }
        },
        "thigh_R": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p11.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p11.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p11.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p04.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p11.png"
            }
        },
        "shin_L": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p10.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p10.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p10.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p05.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p10.png"
            }
        },
        "shin_R": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p12.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p12.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p12.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p05.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p12.png"
            }
        },
        "foot_L": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p13.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p13.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p13.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p07.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p13.png"
            }
        },
        "foot_R": {
            "file": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p14.png",
            "view_variants": {
                "front": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p14.png",
                "threequarter": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p14.png",
                "profile": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.body.profile/party.dj_cyber.body.profile__p07.png",
                "back": "arena/parts/kit3/release_v2/cuts/party.dj_cyber.compact-core/party.dj_cyber.compact-core__p14.png"
            }
        }
    }
}

# Also mirror uarm_L/R -> upper_arm_L/R and farm_L/R -> forearm_L/R
for rig_id, slots in list(RIG_OVERRIDES.items()):
    for s_from, s_to in [("uarm_L", "upper_arm_L"), ("uarm_R", "upper_arm_R"), ("farm_L", "forearm_L"), ("farm_R", "forearm_R")]:
        if s_from in slots:
            slots[s_to] = slots[s_from]

for cat_rel in ["arena/parts/kit3/release_v2/crash_lab_catalog.json", "arena/parts/kit3/release_v2/character_rigs_library.json"]:
    cat_p = os.path.join(BASE, cat_rel)
    with open(cat_p) as f:
        data = json.load(f)
    rigs_raw = data.get("rigs", [])
    rigs_list = list(rigs_raw.values()) if isinstance(rigs_raw, dict) else rigs_raw
    for r in rigs_list:
        rid = r["id"]
        if rid in RIG_OVERRIDES:
            ov = RIG_OVERRIDES[rid]
            slots_dict = r.get("slots") or r.get("resolved_parts") or {}
            for sk, sv in ov.items():
                if sk in slots_dict:
                    slots_dict[sk]["file"] = sv["file"]
                    slots_dict[sk]["view_variants"] = sv["view_variants"]
                    if "girth" in sv:
                        slots_dict[sk]["girth"] = sv["girth"]
                    # Update width & height from actual file
                    fp = os.path.join(BASE, sv["file"])
                    if os.path.exists(fp):
                        im = Image.open(fp)
                        slots_dict[sk]["width"], slots_dict[sk]["height"] = im.size
    with open(cat_p, "w") as f:
        json.dump(data, f, indent=2)
    print("Updated", cat_rel)
