#!/usr/bin/env python3
"""
Render 4 high-impact 2400x1350 visual simulation plates showing EXACTLY WHAT HAPPENS:
1. what_happens_01_naive_vs_infrastructure.png
   - Left: Naive Unfiltered District Splat Chaos (Macro Eyeball 02-04 & Spine 05-04 hallucinated as 40m walls,
     baked-in flat wax-statue ghost duplicates of the Poet frozen into the splat floor next to our live 2.5D puppet,
     and Z-fighting / broken occlusion without a .GLB collider).
   - Right: .GLB Chisel + Actor-Cleaned 2:1 Pano + Z-Buffer Phantom Infrastructure (clean volumetric 3D Gaussian
     splat locked to the cyan .GLB wireframe, with true R3 archway depth-occlusion over our live 2.5D actors).
2. what_happens_02_4step_glb_splat_pipeline_in_action.png
   - A continuous 4-zone horizontal peel across Club Atlantis showing:
     Zone 1: Raw Binary .GLB Chisel & Raycast Collider (3D perspective wireframe + ground raycast vectors gYw)
     Zone 2: 3D Gaussian Splat Cloud (.splat/.spz) Growing on the .GLB Skeleton
     Zone 3: .GLB Z-Buffer Occlusion Phantom + Live 2.5D Cut-Out Cast Walking Inside (archway occluding actor!)
     Zone 4: Final 16:9 Virtual Camera Reshoot Backplate
3. what_happens_03_twin_state_harbor_morph.png
   - 3-panel live morph across the shared hub_02_harbor_temple_chisel.glb shoreline collider:
     Panel A (t=0.0): Poem 03 Turquoise Storm Flood & Ruined Pier .splat
     Panel B (t=0.5): Mid-Morph 3D Gaussian Splat Cloud in flight over the rock-solid cyan .GLB collider
     Panel C (t=1.0): Poem 11 Rebuilt Gold & White Temple by the Bay .splat
4. what_happens_04_all_4_megahubs_live_3d_views.png
   - 2x2 full-frame 3D perspective renders of all 4 Bang-for-Buck Mega-Hubs projecting the real .splat 3D Gaussians,
     real .glb building wireframes, posed camera frustums A..F, and 2.5D cut-out actors on the street.
"""

import json
import math
import os
import struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch")
SHOTS = ROOT / "shots"
PACKS_DIR = SHOTS / "data" / "terrarium" / "atlas_packs"
VAULT_DIR = SHOTS / "png_vault" / "atlas_splats"
BRAIN_DIR = Path("/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584")


def get_font(size=18, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def load_splat_binary(splat_path: Path):
    """Unpack 32-byte .splat binary into (pos Nx3, scale Nx3, rgba Nx4)."""
    raw = splat_path.read_bytes()
    n = len(raw) // 32
    dt = np.dtype([
        ("pos", "<f4", (3,)),
        ("scale", "<f4", (3,)),
        ("rgba", "u1", (4,)),
        ("rot", "u1", (4,)),
    ])
    arr = np.frombuffer(raw[: n * 32], dtype=dt)
    return arr["pos"].copy(), arr["scale"].copy(), arr["rgba"].copy()


def parse_glb_lines(glb_path: Path):
    """Extract vertex positions and triangle edges from our binary .glb for 3D wireframe projection."""
    data = glb_path.read_bytes()
    if len(data) < 28 or data[:4] != b"glTF":
        return []
    json_len = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20 : 20 + json_len].decode("utf-8").strip())
    bin_offset = 20 + json_len + 8
    bin_chunk = data[bin_offset:]

    meshes_out = []
    for node in gltf.get("nodes", []):
        m_idx = node.get("mesh", 0)
        mesh = gltf["meshes"][m_idx]
        prim = mesh["primitives"][0]
        pos_acc = gltf["accessors"][prim["attributes"]["POSITION"]]
        idx_acc = gltf["accessors"][prim["indices"]]

        pos_bv = gltf["bufferViews"][pos_acc["bufferView"]]
        idx_bv = gltf["bufferViews"][idx_acc["bufferView"]]

        v_bytes = bin_chunk[pos_bv["byteOffset"] : pos_bv["byteOffset"] + pos_bv["byteLength"]]
        i_bytes = bin_chunk[idx_bv["byteOffset"] : idx_bv["byteOffset"] + idx_bv["byteLength"]]

        verts = np.frombuffer(v_bytes, dtype="<f4").reshape(-1, 3)
        tris = np.frombuffer(i_bytes, dtype="<u4").reshape(-1, 3)
        meshes_out.append((node.get("name", "MESH"), verts, tris))
    return meshes_out


def project_3d_points(pts, cam_pos, cam_target, fov_deg, w, h):
    """Project Nx3 world points into (u, v, depth_z) using a pinhole camera."""
    fwd = np.array(cam_target, dtype=np.float64) - np.array(cam_pos, dtype=np.float64)
    fwd /= np.linalg.norm(fwd) + 1e-9
    up_world = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    right = np.cross(fwd, up_world)
    right /= np.linalg.norm(right) + 1e-9
    up = np.cross(right, fwd)

    rel = pts.astype(np.float64) - np.array(cam_pos, dtype=np.float64)
    x_cam = rel @ right
    y_cam = rel @ up
    z_cam = rel @ fwd

    f = (h * 0.5) / math.tan(math.radians(fov_deg * 0.5))
    valid = z_cam > 1.5
    z_safe = np.where(valid, z_cam, 1.5)
    u = (w * 0.5) + (x_cam / z_safe) * f
    v = (h * 0.5) - (y_cam / z_safe) * f
    return u, v, z_cam, valid


def render_3d_splat_and_glb_viewport(
    w,
    h,
    splat_pos,
    splat_rgba,
    glb_meshes,
    cam_pos=(0.0, 18.0, 72.0),
    cam_target=(0.0, 4.0, -10.0),
    fov_deg=54.0,
    backdrop_img=None,
    backdrop_alpha=0.58,
    show_glb_wire=True,
    show_splat_ellipsoids=True,
    splat_stride=2,
    wire_color_buildings=(72, 232, 255, 195),
    wire_color_terrain=(74, 222, 128, 120),
    wire_color_portals=(255, 210, 63, 235),
):
    """Render a genuine 3D perspective viewport combining backdrop, .glb wireframe, and 3D Gaussian splats."""
    canvas = Image.new("RGBA", (w, h), (7, 10, 16, 255))

    if backdrop_img is not None:
        bg = backdrop_img.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
        bg = ImageEnhance.Brightness(bg).enhance(backdrop_alpha)
        canvas = Image.alpha_composite(canvas, bg)

    # 1. Project & draw 3D Gaussian Splats back-to-front
    if show_splat_ellipsoids and splat_pos is not None and len(splat_pos) > 0:
        pts = splat_pos[::splat_stride]
        cols = splat_rgba[::splat_stride]
        u, v, z, valid = project_3d_points(pts, cam_pos, cam_target, fov_deg, w, h)
        mask = valid & (u >= -20) & (u < w + 20) & (v >= -20) & (v < h + 20) & (z < 260.0)
        idxs = np.where(mask)[0]
        # Sort back-to-front (largest z first)
        order = idxs[np.argsort(-z[idxs])]

        splat_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(splat_layer)
        for i in order:
            px, py, pz = float(u[i]), float(v[i]), float(z[i])
            r, g, b, a = int(cols[i, 0]), int(cols[i, 1]), int(cols[i, 2]), int(cols[i, 3])
            # Ellipsoid size in pixels inversely proportional to depth
            rx = max(2.0, min(18.0, 260.0 / (pz + 8.0)))
            ry = max(1.5, rx * 0.62)
            alpha = int(min(210, max(55, a * 0.72)))
            sdraw.ellipse([px - rx, py - ry, px + rx, py + ry], fill=(r, g, b, alpha))
        # Slight Gaussian bloom for authentic Gaussian splat look
        splat_soft = splat_layer.filter(ImageFilter.GaussianBlur(radius=1.2))
        canvas = Image.alpha_composite(canvas, splat_soft)
        canvas = Image.alpha_composite(canvas, splat_layer)

    # 2. Project & draw .GLB Chisel & Collider wireframe meshes
    if show_glb_wire and glb_meshes:
        wire_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        wdraw = ImageDraw.Draw(wire_layer)
        for name, verts, tris in glb_meshes:
            u, v, z, valid = project_3d_points(verts, cam_pos, cam_target, fov_deg, w, h)
            if "TERRAIN" in name:
                col = wire_color_terrain
                step = 6  # subsample terrain triangles so grid is clean
                width = 1
            elif "PORTAL" in name:
                col = wire_color_portals
                step = 1
                width = 2
            else:
                col = wire_color_buildings
                step = 2
                width = 1

            for t in tris[::step]:
                i0, i1, i2 = int(t[0]), int(t[1]), int(t[2])
                if not (valid[i0] and valid[i1] and valid[i2]):
                    continue
                if max(z[i0], z[i1], z[i2]) > 220.0:
                    continue
                p0 = (float(u[i0]), float(v[i0]))
                p1 = (float(u[i1]), float(v[i1]))
                p2 = (float(u[i2]), float(v[i2]))
                if all(-100 <= p[0] <= w + 100 and -100 <= p[1] <= h + 100 for p in (p0, p1, p2)):
                    wdraw.line([p0, p1, p2, p0], fill=col, width=width)
        canvas = Image.alpha_composite(canvas, wire_layer)

    return canvas


def load_poet_cutout(target_h=340):
    """Assemble or load a clean full-body 2.5D cutout of the Poet / Cast for street placement."""
    candidates = [
        SHOTS / "arena" / "bodies" / "ACT-001_p0.png",
        SHOTS / "kits" / "packs" / "poet_tracksuit_v1" / "01_COMPONENTS" / "01_torso_front.png",
    ]
    # Better yet, let's check if we have a full figure cutout in release_v2 or weave/cast/man
    weave_man = SHOTS / "weave" / "cast" / "man"
    full_candidates = list((SHOTS / "arena" / "parts" / "kit3" / "v2" / "parts").glob("*/body.front.png"))
    for p in [
        SHOTS / "kits" / "packs" / "poem_01" / "01.cast.poet.png",
        SHOTS / "kits" / "packs" / "poem_06" / "06.cast.poet.png",
    ] + full_candidates + candidates:
        if p.exists():
            try:
                im = Image.open(p).convert("RGBA")
                # Crop to non-transparent bbox
                bbox = im.getbbox()
                if bbox:
                    im = im.crop(bbox)
                aspect = im.width / max(1, im.height)
                return im.resize((max(1, int(target_h * aspect)), target_h), Image.Resampling.LANCZOS)
            except Exception:
                pass
    return None


def assemble_tracksuit_poet(target_h=380):
    """Assemble the calibrated Poet Tracksuit 2.5D puppet from 01_COMPONENTS with cuff-tuck."""
    comp_dir = SHOTS / "kits" / "packs" / "poet_tracksuit_v1" / "01_COMPONENTS"
    if not (comp_dir / "01_torso_front.png").exists():
        return load_poet_cutout(target_h)

    canvas = Image.new("RGBA", (600, 950), (0, 0, 0, 0))

    def paste_part(fname, scale, cx, cy, rot=0):
        p = comp_dir / fname
        if not p.exists():
            return
        im = Image.open(p).convert("RGBA")
        bbox = im.getbbox()
        if bbox:
            im = im.crop(bbox)
        nw = max(1, int(im.width * scale))
        nh = max(1, int(im.height * scale))
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        if rot:
            im = im.rotate(rot, expand=True, resample=Image.Resampling.BICUBIC)
        canvas.alpha_composite(im, (int(cx - im.width // 2), int(cy - im.height // 2)))

    # Legs & boots (boots tucked behind shins)
    paste_part("19_boot_front_L.png", 0.14, 255, 845)
    paste_part("20_boot_front_R.png", 0.14, 345, 845)
    paste_part("12_shin_L.png", 0.22, 260, 700, rot=4)
    paste_part("14_shin_R.png", 0.22, 340, 700, rot=-4)
    paste_part("11_thigh_L.png", 0.24, 265, 535, rot=3)
    paste_part("13_thigh_R.png", 0.24, 335, 535, rot=-3)
    paste_part("05_pelvis_front.png", 0.25, 300, 430)
    # Hands & arms (true wide shoulder sockets)
    paste_part("15_hand_relaxed_L.png", 0.11, 148, 520, rot=14)
    paste_part("16_hand_relaxed_R.png", 0.11, 452, 520, rot=-14)
    paste_part("08_forearm_L.png", 0.20, 165, 420, rot=12)
    paste_part("10_forearm_R.png", 0.20, 435, 420, rot=-12)
    paste_part("07_upper_arm_L.png", 0.22, 192, 295, rot=10)
    paste_part("09_upper_arm_R.png", 0.22, 408, 295, rot=-10)
    # Head & torso
    paste_part("21_head_front_blank.png", 0.21, 300, 145)
    paste_part("01_torso_front.png", 0.28, 300, 310)
    paste_part("31_sunglasses_front.png", 0.12, 300, 140)
    paste_part("28_mouth_neutral.png", 0.06, 300, 176)

    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)
    aspect = canvas.width / max(1, canvas.height)
    return canvas.resize((max(1, int(target_h * aspect)), target_h), Image.Resampling.LANCZOS)


def draw_badge(draw, x, y, text, bg=(18, 26, 38, 235), fg=(255, 210, 63, 255), border=(255, 210, 63, 180), font_size=15):
    f = get_font(font_size, bold=True)
    tb = draw.textbbox((0, 0), text, font=f)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    pad_x, pad_y = 12, 6
    box = [x, y, x + tw + pad_x * 2, y + th + pad_y * 2]
    draw.rounded_rectangle(box, radius=6, fill=bg, outline=border, width=2)
    draw.text((x + pad_x, y + pad_y - 1), text, font=f, fill=fg)
    return box[2], box[3]


def draw_camera_frustum_2d(draw, cx, cy, yaw_deg, label, color=(255, 210, 63, 230), length=65):
    rad = math.radians(yaw_deg)
    spread = math.radians(26)
    p1 = (cx + math.cos(rad - spread) * length, cy + math.sin(rad - spread) * length * 0.55)
    p2 = (cx + math.cos(rad + spread) * length, cy + math.sin(rad + spread) * length * 0.55)
    draw.polygon([ (cx, cy), p1, p2 ], fill=(color[0], color[1], color[2], 55), outline=color)
    draw.line([ (cx, cy), p1 ], fill=color, width=2)
    draw.line([ (cx, cy), p2 ], fill=color, width=2)
    draw.line([ p1, p2 ], fill=color, width=2)
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=color)
    draw.text((cx + 8, cy - 14), label, font=get_font(12, bold=True), fill=color)


# ==============================================================================
# PLATE 1: NAIVE 10-DISTRICT CHAOS vs. .GLB + CLEANED SPLAT INFRASTRUCTURE
# ==============================================================================
def build_plate_01_naive_vs_infrastructure(poet_img):
    W, H = 2400, 1350
    img = Image.new("RGBA", (W, H), (8, 11, 16, 255))
    draw = ImageDraw.Draw(img)

    # Top Title Banner
    draw.rectangle([0, 0, W, 88], fill=(12, 17, 25, 255))
    draw.line([(0, 88), (W, 88)], fill=(50, 65, 90, 255), width=2)
    draw.text((28, 16), "WHAT HAPPENS WHEN WE BUILD CITY SPLATS IN MARBLE / ATLAS: NAIVE vs. INFRASTRUCTURE", font=get_font(26, bold=True), fill=(255, 210, 63, 255))
    draw.text((28, 52), "Left: Feeding unfiltered per-district references (macro close-ups, unmasked actors, no .GLB chisel)  |  Right: Our 4-Layer .GLB Collider + Cleaned 2:1 Pano + Z-Buffer Phantom Pipeline", font=get_font(16), fill=(185, 200, 222, 255))

    panel_w = 1164
    panel_h = 1140
    top_y = 104

    # Load Hub 01 assets
    pano_clean = Image.open(PACKS_DIR / "hub_01_atlantis" / "pano_2560x1280_clean.jpg").convert("RGBA")
    shot_06 = Image.open(SHOTS / "png_vault" / "painted_shots" / "inverse_painted_06_00_w1623.png").convert("RGBA")
    splat_pos, _, splat_rgba = load_splat_binary(PACKS_DIR / "splats" / "hub_01_atlantis.splat")
    glb_meshes = parse_glb_lines(PACKS_DIR / "glb" / "hub_01_atlantis_chisel.glb")

    # ------------------------------------------------------------------
    # LEFT PANEL: NAIVE UNFILTERED DISTRICT SPLAT CHAOS
    # ------------------------------------------------------------------
    lx = 24
    left_vp = render_3d_splat_and_glb_viewport(
        panel_w, panel_h,
        splat_pos=splat_pos,
        splat_rgba=splat_rgba,
        glb_meshes=None,
        cam_pos=(12.0, 22.0, 82.0),
        cam_target=(-8.0, 6.0, -15.0),
        fov_deg=58.0,
        backdrop_img=shot_06,
        backdrop_alpha=0.52,
        show_glb_wire=False,
        show_splat_ellipsoids=True,
        splat_stride=3,
    )

    # Inject the 3 real visual failure modes into the Left Panel:
    # Failure 1: Macro Eyeball (02-04) & Spine X-Ray (05-04) hallucinated as 40m walls in the splat sky/buildings!
    ref_eye_path = SHOTS / "data" / "terrarium" / "foundry" / "refs" / "02-04.jpg"
    ref_spine_path = SHOTS / "data" / "terrarium" / "foundry" / "refs" / "05-04.jpg"
    ref_tamb_path = SHOTS / "data" / "terrarium" / "foundry" / "refs" / "03-01.jpg"
    for rpath, box, tint, label_txt in [
        (ref_eye_path, (36, 92, 436, 372), (255, 80, 110), "HALLUCINATION #1: Macro Eyeball (02-04) -> 40m Building Wall!"),
        (ref_spine_path, (715, 92, 1125, 372), (255, 110, 80), "HALLUCINATION #2: Spine X-Ray (05-04) -> Giant Sky Ribcage!"),
        (ref_tamb_path, (452, 130, 698, 355), (255, 165, 60), "Markov Duplicate Clash (02-07=04-06)"),
    ]:
        if rpath.exists():
            rim = Image.open(rpath).convert("RGBA").resize((box[2] - box[0], box[3] - box[1]), Image.Resampling.LANCZOS)
            mask = Image.new("L", rim.size, 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.rounded_rectangle([6, 6, rim.width - 6, rim.height - 6], radius=22, fill=215)
            mask = mask.filter(ImageFilter.GaussianBlur(10))
            left_vp.paste(rim, (box[0], box[1]), mask)
            ld = ImageDraw.Draw(left_vp)
            ld.rounded_rectangle(box, radius=14, outline=(255, 77, 109, 240), width=3)
            draw_badge(ld, box[0] + 8, box[1] + 8, label_txt, bg=(45, 10, 18, 240), fg=(255, 145, 165, 255), border=(255, 77, 109, 230), font_size=12)

    # Failure 2: Baked-In Flat "Wax Statue" Ghost Actor frozen in the splat floor right next to our live 2.5D puppet!
    if poet_img is not None:
        ghost = poet_img.resize((int(poet_img.width * 0.92), int(poet_img.height * 0.92)), Image.Resampling.LANCZOS)
        ghost = ghost.filter(ImageFilter.GaussianBlur(4.5))
        g_arr = np.array(ghost, dtype=np.float32)
        g_arr[..., 0] *= 0.65
        g_arr[..., 1] *= 0.85
        g_arr[..., 2] *= 1.05
        g_arr[..., 3] *= 0.78
        ghost = Image.fromarray(np.clip(g_arr, 0, 255).astype(np.uint8), "RGBA")
        left_vp.alpha_composite(ghost, (125, 555))

        # Live 2.5D Poet right next to his frozen splat ghost
        left_vp.alpha_composite(poet_img, (305, 540))

        ld = ImageDraw.Draw(left_vp)
        ld.rounded_rectangle([95, 525, 535, 955], radius=12, outline=(255, 77, 109, 240), width=3)
        draw_badge(ld, 65, 482, "HALLUCINATION #3: Baked-In Splat Ghost Clone Collides with Live 2.5D Actor!", bg=(50, 12, 20, 240), fg=(255, 150, 165, 255), border=(255, 77, 109, 230), font_size=13)
        ld.text((118, 925), "Frozen R1 Splat Blob", font=get_font(13, bold=True), fill=(255, 130, 150, 255))
        ld.text((322, 925), "Live 2.5D Puppet", font=get_font(13, bold=True), fill=(92, 225, 230, 255))

    # Failure 3: No .GLB Depth Occlusion (2.5D Actor floats ON TOP of a foreground wall instead of behind it)
    if poet_img is not None:
        ld = ImageDraw.Draw(left_vp)
        ld.rectangle([770, 440, 945, 955], fill=(42, 34, 52, 215), outline=(255, 159, 28, 230), width=3)
        ld.text((782, 455), "Foreground R3 Wall\n(18m Depth)", font=get_font(13, bold=True), fill=(255, 210, 63, 255))
        small_poet = poet_img.resize((int(poet_img.width * 0.78), int(poet_img.height * 0.78)), Image.Resampling.LANCZOS)
        left_vp.alpha_composite(small_poet, (765, 565))
        ld = ImageDraw.Draw(left_vp)
        draw_badge(ld, 595, 968, "HALLUCINATION #4: No .GLB Z-Buffer -> Actor Floats Over Foreground Wall!", bg=(50, 24, 10, 240), fg=(255, 190, 90, 255), border=(255, 159, 28, 230), font_size=13)

    # Left Header Banner
    ld = ImageDraw.Draw(left_vp)
    ld.rectangle([0, 0, panel_w, 64], fill=(42, 11, 20, 240))
    ld.text((18, 10), "[BROKEN] WHAT HAPPENS IF WE DUMP UNFILTERED REFS PER DISTRICT", font=get_font(20, bold=True), fill=(255, 105, 130, 255))
    ld.text((18, 38), "10 Fragmented Splats · Macro Shots Turned Into Giant Walls · Frozen Wax-Statue Actors · Broken Z-Occlusion", font=get_font(13), fill=(240, 190, 200, 255))
    img.alpha_composite(left_vp, (lx, top_y))
    draw.rounded_rectangle([lx, top_y, lx + panel_w, top_y + panel_h], radius=10, outline=(255, 77, 109, 220), width=3)

    # ------------------------------------------------------------------
    # RIGHT PANEL: .GLB CHISEL + ACTOR-CLEANED PANO + Z-PHANTOM INFRASTRUCTURE
    # ------------------------------------------------------------------
    rx = W - panel_w - 24
    right_vp = render_3d_splat_and_glb_viewport(
        panel_w, panel_h,
        splat_pos=splat_pos,
        splat_rgba=splat_rgba,
        glb_meshes=glb_meshes,
        cam_pos=(0.0, 16.0, 68.0),
        cam_target=(0.0, 4.0, -18.0),
        fov_deg=52.0,
        backdrop_img=pano_clean.crop((320, 120, 2240, 1160)),
        backdrop_alpha=0.74,
        show_glb_wire=True,
        show_splat_ellipsoids=True,
        splat_stride=2,
    )
    rd = ImageDraw.Draw(right_vp)

    # Show 1: Actor-Cleaned R1/R0 Inpainted Pano Sky & Street (Zero Ghost Actors!)
    draw_badge(rd, 24, 84, "[STEP 1] Actor-Cleaned 2560x1280 (2:1) Pano + Metric Depth: Zero Baked-In Ghost Actors!", bg=(10, 38, 28, 235), fg=(110, 245, 175, 255), border=(46, 196, 182, 230), font_size=14)
    draw_badge(rd, 24, 126, "[STEP 2] Binary .GLB Chisel Mesh (Cyan Wireframe) Locks Street Grid, Heights & Ground Collider gYw(x,z)", bg=(12, 28, 46, 235), fg=(92, 225, 230, 255), border=(92, 225, 230, 220), font_size=14)

    # Show 2: Live 2.5D Cut-Out Cast Walking Inside the Splat with TRUE .GLB Depth-Occlusion!
    if poet_img is not None:
        px, py = 310, 520
        rd.ellipse([px + 20, py + poet_img.height - 18, px + poet_img.width - 20, py + poet_img.height + 14], fill=(0, 0, 0, 150), outline=(74, 222, 128, 240), width=2)
        rd.line([(px + poet_img.width // 2, py + poet_img.height - 4), (px + poet_img.width // 2, py + poet_img.height + 45)], fill=(74, 222, 128, 240), width=3)
        right_vp.alpha_composite(poet_img, (px, py))
        rd = ImageDraw.Draw(right_vp)
        draw_badge(rd, px - 25, py + poet_img.height + 18, "Live 2.5D Actor (R1 = 3.2m) Raycast-Locked to .GLB Floor", bg=(10, 32, 24, 240), fg=(74, 222, 128, 255), border=(74, 222, 128, 220), font_size=13)

        # Center-right Actor walking BEHIND an R3 .GLB Archway Column (Depth-Occlusion Phantom Prepass!)
        arch_x1, arch_y1, arch_x2, arch_y2 = 790, 350, 935, 930
        actor_behind = poet_img.resize((int(poet_img.width * 0.86), int(poet_img.height * 0.86)), Image.Resampling.LANCZOS)
        right_vp.alpha_composite(actor_behind, (715, 535))

        pillar_bg = pano_clean.crop((320, 120, 2240, 1160)).resize((panel_w, panel_h), Image.Resampling.LANCZOS)
        pillar_patch = pillar_bg.crop((arch_x1, arch_y1, arch_x2, arch_y2))
        pillar_patch = ImageEnhance.Brightness(pillar_patch).enhance(0.88)
        right_vp.paste(pillar_patch, (arch_x1, arch_y1))
        rd = ImageDraw.Draw(right_vp)
        rd.rectangle([arch_x1, arch_y1, arch_x2, arch_y2], fill=(92, 225, 230, 38), outline=(255, 210, 63, 245), width=3)
        for hy in range(arch_y1 + 20, arch_y2 - 10, 28):
            rd.line([(arch_x1 + 6, hy), (arch_x2 - 6, hy - 18)], fill=(255, 210, 63, 120), width=1)
        draw_badge(rd, arch_x1 - 75, arch_y1 - 42, "[STEP 3] .GLB Depth-Occlusion Phantom (R3 = 18m)", bg=(38, 30, 10, 245), fg=(255, 210, 63, 255), border=(255, 210, 63, 235), font_size=13)
        rd.text((arch_x1 + 10, arch_y1 + 14), ".GLB Z-Prepass\ncolorWrite: false\ndepthWrite: true\n\nOccludes R1 Actor\nWalking Behind\nSplat Archway!", font=get_font(13, bold=True), fill=(255, 230, 140, 255))

    # Draw Posed Camera Frustums A, B, C on the street
    draw_camera_frustum_2d(rd, 165, 845, -35, "Cam A (06-00)", color=(255, 210, 63, 240))
    draw_camera_frustum_2d(rd, 565, 885, -75, "Cam B (08-00)", color=(92, 225, 230, 240))
    draw_camera_frustum_2d(rd, 980, 850, -125, "Cam C (10-01)", color=(196, 181, 253, 240))

    # Right Header Banner
    rd.rectangle([0, 0, panel_w, 64], fill=(10, 36, 28, 240))
    rd.text((18, 10), "[SOLVED] WHAT HAPPENS WITH OUR 4-MEGA-HUB .GLB + .SPLAT INFRASTRUCTURE", font=get_font(20, bold=True), fill=(74, 222, 128, 255))
    rd.text((18, 38), "4 Cohesive Mega-Hubs · Binary .GLB Chisel & Floor Collider · Actor-Cleaned 2:1 Panos · True Z-Buffer Occlusion", font=get_font(13), fill=(195, 245, 215, 255))

    img.alpha_composite(right_vp, (rx, top_y))
    draw.rounded_rectangle([rx, top_y, rx + panel_w, top_y + panel_h], radius=10, outline=(46, 196, 182, 235), width=3)

    # Bottom Summary Footer
    draw.rectangle([24, H - 86, W - 24, H - 16], fill=(14, 20, 30, 245), outline=(60, 80, 110, 220), width=2)
    draw.text((44, H - 72), "WHY THIS MATTERS:", font=get_font(16, bold=True), fill=(255, 210, 63, 255))
    draw.text((220, H - 72), "World Labs Marble / Atlas turns every pixel in your input into static 3D Gaussian particles. If actors or macro close-ups are in the input, they become permanent", font=get_font(15), fill=(225, 232, 242, 255))
    draw.text((44, H - 46), "3D statues and 40m walls. By feeding Marble our .GLB Chisel + Actor-Cleaned 2:1 Pano + Depth Map, the .SPLAT becomes pure architectural infrastructure that our 2.5D puppets walk inside!", font=get_font(15), fill=(155, 235, 210, 255))

    out_path = VAULT_DIR / "what_happens_01_naive_vs_infrastructure.png"
    img.convert("RGB").save(out_path, quality=95)
    img.convert("RGB").save(BRAIN_DIR / out_path.name, quality=95)
    print("Saved", out_path)


# ==============================================================================
# PLATE 2: THE 4 STAGES OF .GLB + .SPLAT INFRASTRUCTURE IN A SINGLE CONTINUOUS FRAME
# ==============================================================================
def build_plate_02_4step_pipeline(poet_img):
    W, H = 2400, 1350
    img = Image.new("RGBA", (W, H), (8, 11, 16, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 88], fill=(12, 17, 25, 255))
    draw.line([(0, 88), (W, 88)], fill=(50, 65, 90, 255), width=2)
    draw.text((28, 16), "HOW .GLB & .SPLAT WORK TOGETHER AS LIVE 3D INFRASTRUCTURE (4-STAGE CUTAWAY PEEL)", font=get_font(26, bold=True), fill=(92, 225, 230, 255))
    draw.text((28, 52), "One continuous 3D camera across Hub 01 (Club Atlantis / Centro) peeling from (1) Binary .GLB Collider -> (2) 3D Gaussian Splat Cloud -> (3) Z-Buffer Phantom + 2.5D Actors -> (4) Final 16:9 Cinema Frame", font=get_font(16), fill=(185, 200, 222, 255))

    pano_clean = Image.open(PACKS_DIR / "hub_01_atlantis" / "pano_2560x1280_clean.jpg").convert("RGBA")
    depth_map = Image.open(PACKS_DIR / "hub_01_atlantis" / "depth_2560x1280.jpg").convert("RGBA")
    splat_pos, _, splat_rgba = load_splat_binary(PACKS_DIR / "splats" / "hub_01_atlantis.splat")
    glb_meshes = parse_glb_lines(PACKS_DIR / "glb" / "hub_01_atlantis_chisel.glb")

    vw, vh = W - 48, 1080
    vx, vy = 24, 104
    cam_pos = (0.0, 15.5, 64.0)
    cam_target = (0.0, 4.5, -20.0)
    fov = 52.0

    # Render 4 aligned full-viewport layers from the EXACT same 3D camera so we can slice them into 4 vertical cutaway strips!
    # Strip 1: Pure .GLB Chisel & Collider Wireframe over dark blueprint grid
    vp_stage1 = render_3d_splat_and_glb_viewport(
        vw, vh,
        splat_pos=None,
        splat_rgba=None,
        glb_meshes=glb_meshes,
        cam_pos=cam_pos,
        cam_target=cam_target,
        fov_deg=fov,
        backdrop_img=depth_map.crop((280, 120, 2280, 1160)),
        backdrop_alpha=0.22,
        show_glb_wire=True,
        show_splat_ellipsoids=False,
        wire_color_buildings=(72, 232, 255, 240),
        wire_color_terrain=(74, 222, 128, 200),
        wire_color_portals=(255, 210, 63, 255),
    )

    # Strip 2: .GLB Chisel + 3D Gaussian Splat Cloud (.splat ellipsoids locking onto the .GLB walls)
    vp_stage2 = render_3d_splat_and_glb_viewport(
        vw, vh,
        splat_pos=splat_pos,
        splat_rgba=splat_rgba,
        glb_meshes=glb_meshes,
        cam_pos=cam_pos,
        cam_target=cam_target,
        fov_deg=fov,
        backdrop_img=pano_clean.crop((280, 120, 2280, 1160)),
        backdrop_alpha=0.45,
        show_glb_wire=True,
        show_splat_ellipsoids=True,
        splat_stride=1,
    )

    # Strip 3: .GLB Z-Buffer Depth-Occlusion Prepass + Live 2.5D Cut-Out Cast & Camera Frustums
    vp_stage3 = render_3d_splat_and_glb_viewport(
        vw, vh,
        splat_pos=splat_pos,
        splat_rgba=splat_rgba,
        glb_meshes=glb_meshes,
        cam_pos=cam_pos,
        cam_target=cam_target,
        fov_deg=fov,
        backdrop_img=pano_clean.crop((280, 120, 2280, 1160)),
        backdrop_alpha=0.68,
        show_glb_wire=True,
        show_splat_ellipsoids=True,
        splat_stride=2,
        wire_color_buildings=(196, 181, 253, 130),
    )

    # Strip 4: Final Composited 16:9 Cinema Frame (Pure Splat + 2.5D Cast + Volumetric Lighting, Wireframe Hidden)
    shot_final = Image.open(SHOTS / "png_vault" / "painted_shots" / "inverse_painted_01_00_w1623.png").convert("RGBA").resize((vw, vh), Image.Resampling.LANCZOS)
    vp_stage4 = render_3d_splat_and_glb_viewport(
        vw, vh,
        splat_pos=splat_pos,
        splat_rgba=splat_rgba,
        glb_meshes=None,
        cam_pos=cam_pos,
        cam_target=cam_target,
        fov_deg=fov,
        backdrop_img=shot_final,
        backdrop_alpha=0.88,
        show_glb_wire=False,
        show_splat_ellipsoids=True,
        splat_stride=3,
    )

    # Assemble the 4 strips into one composite viewport
    comp = Image.new("RGBA", (vw, vh), (0, 0, 0, 255))
    sw = vw // 4
    for idx, stage_vp in enumerate([vp_stage1, vp_stage2, vp_stage3, vp_stage4]):
        x0 = idx * sw
        x1 = vw if idx == 3 else (idx + 1) * sw
        strip = stage_vp.crop((x0, 0, x1, vh))
        comp.paste(strip, (x0, 0))

    cd = ImageDraw.Draw(comp)

    # Place 2.5D Actors & Technical Callouts in each strip
    if poet_img is not None:
        # In Strip 3 (x = 2*sw .. 3*sw): show actor with Z-occlusion phantom mask & raycast vector
        s3_x = 2 * sw + 130
        s3_y = 480
        comp.alpha_composite(poet_img, (s3_x, s3_y))
        # Draw an R3 .GLB occlusion wall overlapping the right edge of the actor in Strip 3
        occ_box = [s3_x + int(poet_img.width * 0.58), s3_y - 40, s3_x + poet_img.width + 65, s3_y + poet_img.height + 10]
        occ_patch = vp_stage3.crop(occ_box)
        comp.paste(occ_patch, (occ_box[0], occ_box[1]))
        cd = ImageDraw.Draw(comp)
        cd.rectangle(occ_box, fill=(167, 139, 250, 48), outline=(255, 210, 63, 240), width=3)
        cd.text((occ_box[0] + 8, occ_box[1] + 12), "R3 .GLB Wall\nZ-Occludes\nR1 Puppet!", font=get_font(13, bold=True), fill=(255, 210, 63, 255))

        # In Strip 4 (x = 3*sw .. vw): show final lit 2.5D actor in the completed scene
        s4_x = 3 * sw + 175
        s4_y = 490
        comp.alpha_composite(poet_img, (s4_x, s4_y))
        cd = ImageDraw.Draw(comp)

    # Draw vertical divider lines and top headers for the 4 stages
    stage_meta = [
        ("STAGE 1 · BINARY .GLB CHISEL & COLLIDER", "Unpacked from 12-bit landpack hf + OSM buildings.\nProvides exact street walls for Marble & gYw(x,z) floor physics.", (72, 232, 255, 255)),
        ("STAGE 2 · 3D GAUSSIAN SPLAT (.SPLAT / .SPZ)", "28,000+ 3D Gaussians generated from Actor-Cleaned\n2560×1280 2:1 Pano + Depth locked to the .GLB skeleton.", (196, 181, 253, 255)),
        ("STAGE 3 · Z-PHANTOM + 2.5D ACTORS (R1)", ".GLB switches to Depth-Only Prepass (colorWrite: false)\nso splat walls occlude 2.5D actors walking inside!", (255, 210, 63, 255)),
        ("STAGE 4 · VIRTUAL CAMERA 16:9 RESHOOT", "Orbit or fly between posed cameras A..F and bake\nnew parallax-accurate backplates for the 183-shot tape!", (74, 222, 128, 255)),
    ]

    for idx, (title, sub, col) in enumerate(stage_meta):
        x0 = idx * sw
        x1 = vw if idx == 3 else (idx + 1) * sw
        if idx > 0:
            cd.line([(x0, 0), (x0, vh)], fill=col, width=4)
        cd.rectangle([x0 + 8, 12, x1 - 8, 108], fill=(10, 15, 24, 235), outline=col, width=2)
        cd.text((x0 + 20, 22), title, font=get_font(17, bold=True), fill=col)
        lines = sub.split("\n")
        cd.text((x0 + 20, 50), lines[0], font=get_font(13), fill=(225, 232, 242, 255))
        if len(lines) > 1:
            cd.text((x0 + 20, 70), lines[1], font=get_font(13), fill=(185, 200, 222, 255))

    # Add ground raycast arrows in Stage 1
    for gx in range(80, sw - 60, 110):
        cd.line([(gx, 620), (gx, 790)], fill=(74, 222, 128, 230), width=2)
        cd.ellipse([gx - 14, 782, gx + 14, 798], outline=(74, 222, 128, 255), width=2)
    draw_badge(cd, 28, 815, "Floor Raycast gYw(x,z) on TERRAIN_COLLIDER", bg=(10, 34, 22, 235), fg=(74, 222, 128, 255), border=(74, 222, 128, 220), font_size=13)

    img.alpha_composite(comp, (vx, vy))
    draw.rounded_rectangle([vx, vy, vx + vw, vy + vh], radius=10, outline=(92, 225, 230, 220), width=3)

    # Bottom Legend
    draw.rectangle([24, H - 142, W - 24, H - 18], fill=(13, 19, 28, 245), outline=(55, 75, 105, 220), width=2)
    draw.text((44, H - 126), "COORDINATE & OCCLUSION HANDSHAKE (OpenCV Splat <-> Three.js Terrarium):", font=get_font(16, bold=True), fill=(255, 210, 63, 255))
    draw.text((44, H - 96), "1. Coordinate Bridge: Marble exports .spz/.ply in OpenCV (+X right, +Y down, +Z fwd). Our studio applies diag(1, -1, -1, 1) + spawn datum so the splat snaps onto the .GLB collider.", font=get_font(15), fill=(220, 230, 242, 255))
    draw.text((44, H - 68), "2. Why .GLB + .SPLAT Need Each Other: The .GLB has crisp triangles for floor raycasting & Z-occlusion but no painterly surface; the .SPLAT has lush volumetric brush/neon", font=get_font(15), fill=(220, 230, 242, 255))
    draw.text((44, H - 42), "   texture but fuzzy point alpha. Together, the .GLB acts as the invisible physical skeleton and Z-buffer shield while the .SPLAT provides the 360° volumetric world!", font=get_font(15), fill=(120, 240, 190, 255))

    out_path = VAULT_DIR / "what_happens_02_4step_glb_splat_pipeline_in_action.png"
    img.convert("RGB").save(out_path, quality=95)
    img.convert("RGB").save(BRAIN_DIR / out_path.name, quality=95)
    print("Saved", out_path)


# ==============================================================================
# PLATE 3: TWIN-STATE HARBOR SPLAT MORPH (P03 STORM RUIN <-> P11 WHITE TEMPLE)
# ==============================================================================
def build_plate_03_twin_state_morph(poet_img):
    W, H = 2400, 1350
    img = Image.new("RGBA", (W, H), (8, 11, 16, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 88], fill=(12, 17, 25, 255))
    draw.line([(0, 88), (W, 88)], fill=(50, 65, 90, 255), width=2)
    draw.text((28, 16), "WHAT HAPPENS IN HUB 02: TWIN-STATE SPLAT MORPH ON ONE SHARED .GLB SHORELINE", font=get_font(26, bold=True), fill=(196, 181, 253, 255))
    draw.text((28, 52), "Poem 03 (Turquoise Storm Ruin Pier) and Poem 11 (Rebuilt Gold & White Temple) share hub_02_harbor_temple_chisel.glb — morphing 28,000 Gaussians live in 3D!", font=get_font(16), fill=(185, 200, 222, 255))

    pos_a, _, rgba_a = load_splat_binary(PACKS_DIR / "splats" / "hub_02_harbor_storm_ruin.splat")
    pos_b, _, rgba_b = load_splat_binary(PACKS_DIR / "splats" / "hub_02_harbor_temple.splat")
    n = min(len(pos_a), len(pos_b))
    pos_a, rgba_a = pos_a[:n], rgba_a[:n]
    pos_b, rgba_b = pos_b[:n], rgba_b[:n]

    # Mid-morph t = 0.50
    pos_mid = 0.5 * pos_a + 0.5 * pos_b
    # Add a slight upward arc to morphing particles so you visually see the temple rising out of the storm!
    pos_mid[:, 1] += 3.5 * np.sin(np.linspace(0, math.pi, n))
    rgba_mid = np.clip(0.5 * rgba_a.astype(np.float32) + 0.5 * rgba_b.astype(np.float32), 0, 255).astype(np.uint8)

    glb_meshes = parse_glb_lines(PACKS_DIR / "glb" / "hub_02_harbor_temple_chisel.glb")
    pano_storm = Image.open(PACKS_DIR / "hub_02_harbor_temple" / "pano_2560x1280_storm_ruin.jpg").convert("RGBA")
    pano_temple = Image.open(PACKS_DIR / "hub_02_harbor_temple" / "pano_2560x1280_clean.jpg").convert("RGBA")
    pano_mid = Image.blend(pano_storm, pano_temple, 0.5)

    pw = 768
    ph = 1080
    top_y = 104
    cam_pos = (0.0, 16.5, 66.0)
    cam_target = (0.0, 5.0, -18.0)

    panels = [
        (
            24,
            "STATE A (Morph = 0%) · POEM 03 STORM RUIN SPLAT",
            "hub_02_harbor_storm_ruin.splat + hub_02_harbor_temple_chisel.glb",
            pos_a,
            rgba_a,
            pano_storm.crop((350, 100, 2210, 1180)),
            (56, 189, 248, 255),
            "Turquoise floodwater, dark storm sky & shattered pier pilings.\nThe cyan .GLB collider defines the exact pier deck & shoreline.",
        ),
        (
            24 + pw + 24,
            "LIVE MID-MORPH (Morph = 50%) · SPLAT CLOUD TRANSFORMING",
            "28,000 3D Gaussians Lerping Position & SH Color Over Shared .GLB",
            pos_mid,
            rgba_mid,
            pano_mid.crop((350, 100, 2210, 1180)),
            (196, 181, 253, 255),
            "As you drag the Twin-State Slider in atlas_splat_studio.html,\nthe storm splat rises and crystallizes into white marble columns!",
        ),
        (
            24 + (pw + 24) * 2,
            "STATE B (Morph = 100%) · POEM 11 REBUILT WHITE TEMPLE",
            "hub_02_harbor_temple.splat + hub_02_harbor_temple_chisel.glb",
            pos_b,
            rgba_b,
            pano_temple.crop((350, 100, 2210, 1180)),
            (255, 210, 63, 255),
            "Radiant gold-and-white temple on the exact same .GLB shoreline.\nOur 2.5D actors keep walking without a single frame of physics glitch!",
        ),
    ]

    for px, title, sub, p_pos, p_rgba, bg_crop, col, desc in panels:
        vp = render_3d_splat_and_glb_viewport(
            pw, ph,
            splat_pos=p_pos,
            splat_rgba=p_rgba,
            glb_meshes=glb_meshes,
            cam_pos=cam_pos,
            cam_target=cam_target,
            fov_deg=54.0,
            backdrop_img=bg_crop,
            backdrop_alpha=0.72,
            show_glb_wire=True,
            show_splat_ellipsoids=True,
            splat_stride=2,
            wire_color_buildings=(col[0], col[1], col[2], 185),
        )
        vd = ImageDraw.Draw(vp)
        vd.rectangle([0, 0, pw, 72], fill=(10, 15, 24, 240))
        vd.text((16, 12), title, font=get_font(17, bold=True), fill=col)
        vd.text((16, 40), sub, font=get_font(13), fill=(195, 210, 230, 255))

        if poet_img is not None:
            actor_h = 310
            ac = poet_img.resize((int(poet_img.width * (actor_h / poet_img.height)), actor_h), Image.Resampling.LANCZOS)
            ax, ay = pw // 2 - ac.width // 2, 575
            vd.ellipse([ax + 15, ay + ac.height - 14, ax + ac.width - 15, ay + ac.height + 12], fill=(0, 0, 0, 155), outline=(74, 222, 128, 235), width=2)
            vp.alpha_composite(ac, (ax, ay))
            vd = ImageDraw.Draw(vp)

        # Bottom description card inside panel
        vd.rectangle([14, ph - 112, pw - 14, ph - 14], fill=(10, 15, 24, 235), outline=col, width=2)
        for li, line in enumerate(desc.split("\n")):
            vd.text((28, ph - 98 + li * 24), line, font=get_font(14), fill=(230, 236, 245, 255))
        draw_badge(vd, 28, ph - 44, "SHARED .GLB COLLIDER: 100% LOCKED ACROSS MORPH", bg=(12, 34, 26, 240), fg=(74, 222, 128, 255), border=(74, 222, 128, 210), font_size=12)

        img.alpha_composite(vp, (px, top_y))
        draw.rounded_rectangle([px, top_y, px + pw, top_y + ph], radius=10, outline=col, width=3)

    # Bottom Morph Progress Bar visual
    draw.rectangle([24, H - 140, W - 24, H - 18], fill=(13, 19, 28, 245), outline=(196, 181, 253, 200), width=2)
    draw.text((44, H - 122), "TWIN-STATE SPLAT MORPH SLIDER (LIVE IN shots/atlas_splat_studio.html):", font=get_font(16, bold=True), fill=(196, 181, 253, 255))
    bar_x1, bar_y1, bar_x2, bar_y2 = 44, H - 84, W - 44, H - 52
    draw.rounded_rectangle([bar_x1, bar_y1, bar_x2, bar_y2], radius=14, fill=(22, 30, 44, 255), outline=(92, 225, 230, 220), width=2)
    # Gradient fill
    for bx in range(bar_x1 + 4, bar_x2 - 4, 4):
        t = (bx - bar_x1) / max(1, (bar_x2 - bar_x1))
        r = int(56 * (1 - t) + 255 * t)
        g = int(189 * (1 - t) + 210 * t)
        b = int(248 * (1 - t) + 63 * t)
        draw.line([(bx, bar_y1 + 4), (bx, bar_y2 - 4)], fill=(r, g, b, 210), width=4)
    draw.text((bar_x1 + 18, bar_y1 + 6), "0.00 · Poem 03 Storm Ruin (Fells Point / Inner Harbor Flood)", font=get_font(14, bold=True), fill=(10, 15, 24, 255))
    draw.text(((bar_x1 + bar_x2) // 2 - 140, bar_y1 + 6), "0.50 · Real-Time Gaussian Lerp", font=get_font(14, bold=True), fill=(10, 15, 24, 255))
    draw.text((bar_x2 - 470, bar_y1 + 6), "1.00 · Poem 11 Rebuilt White Temple by the Bay", font=get_font(14, bold=True), fill=(10, 15, 24, 255))

    out_path = VAULT_DIR / "what_happens_03_twin_state_harbor_morph.png"
    img.convert("RGB").save(out_path, quality=95)
    img.convert("RGB").save(BRAIN_DIR / out_path.name, quality=95)
    print("Saved", out_path)


# ==============================================================================
# PLATE 4: ALL 4 BANG-FOR-BUCK MEGA-HUBS LIVE 3D PERSPECTIVE VIEWS
# ==============================================================================
def build_plate_04_all_4_megahubs_3d(poet_img):
    W, H = 2400, 1350
    img = Image.new("RGBA", (W, H), (8, 11, 16, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 88], fill=(12, 17, 25, 255))
    draw.line([(0, 88), (W, 88)], fill=(50, 65, 90, 255), width=2)
    draw.text((28, 16), "ALL 4 BANG-FOR-BUCK MEGA-HUBS: LIVE 3D .GLB + .SPLAT + 2.5D CAST VIEWPORTS", font=get_font(26, bold=True), fill=(255, 210, 63, 255))
    draw.text((28, 52), "Instead of 10 fragmented districts, these 4 Mega-Hubs cover 100% of all 14 Poems, 10 City Stages & 6 Foundry Worlds with pre-built .GLB colliders & .SPLAT clouds", font=get_font(16), fill=(185, 200, 222, 255))

    manifest = json.loads((PACKS_DIR / "atlas_infrastructure_manifest.json").read_text())
    hubs = manifest["mega_hubs"]

    quad_w = 1164
    quad_h = 596
    positions = [
        (24, 104),
        (W - quad_w - 24, 104),
        (24, 104 + quad_h + 24),
        (W - quad_w - 24, 104 + quad_h + 24),
    ]
    accent_cols = [
        (92, 225, 230, 255),
        (255, 210, 63, 255),
        (255, 120, 150, 255),
        (74, 222, 128, 255),
    ]

    for idx, hub in enumerate(hubs[:4]):
        qx, qy = positions[idx]
        col = accent_cols[idx]
        hid = hub["hub_id"]
        splat_url = hub["splat_seed"]["file"]
        glb_url = hub["chisel_glb"]["file"]
        pano_url = hub["pano_2560x1280"]
        splat_pos, _, splat_rgba = load_splat_binary(SHOTS / splat_url)
        glb_meshes = parse_glb_lines(SHOTS / glb_url)
        pano_img = Image.open(SHOTS / pano_url).convert("RGBA")

        vp = render_3d_splat_and_glb_viewport(
            quad_w, quad_h,
            splat_pos=splat_pos,
            splat_rgba=splat_rgba,
            glb_meshes=glb_meshes,
            cam_pos=(0.0, 17.5, 66.0),
            cam_target=(0.0, 4.0, -18.0),
            fov_deg=54.0,
            backdrop_img=pano_img.crop((320, 140, 2240, 1140)),
            backdrop_alpha=0.72,
            show_glb_wire=True,
            show_splat_ellipsoids=True,
            splat_stride=2,
            wire_color_buildings=(col[0], col[1], col[2], 195),
        )
        vd = ImageDraw.Draw(vp)

        # Place 2.5D actor on the street
        if poet_img is not None:
            ah = 225
            ac = poet_img.resize((int(poet_img.width * (ah / poet_img.height)), ah), Image.Resampling.LANCZOS)
            ax, ay = 520, 315
            vd.ellipse([ax + 12, ay + ac.height - 10, ax + ac.width - 12, ay + ac.height + 10], fill=(0, 0, 0, 160), outline=(74, 222, 128, 240), width=2)
            vp.alpha_composite(ac, (ax, ay))
            vd = ImageDraw.Draw(vp)

        # Draw 3 posed camera frustums
        for ci, anc in enumerate(hub.get("anchor_files", [])[:3]):
            fx = 220 + ci * 310
            fy = 505
            draw_camera_frustum_2d(vd, fx, fy, -65 - ci * 20, f"Cam {chr(65+ci)} ({anc['ref_id']})", color=col, length=52)

        # Top overlay bar
        vd.rectangle([0, 0, quad_w, 64], fill=(10, 15, 24, 238))
        vd.text((16, 10), f"{hub['title']}  ·  Poems {', '.join(hub['poems'])}", font=get_font(18, bold=True), fill=col)
        vd.text((16, 36), f"Districts: {', '.join(hub['linked_stages'])}  |  Splat: {hub['splat_seed']['splat_count']:,} Gaussians  |  Collider: {Path(glb_url).name} ({hub['chisel_glb']['buildings_extruded']} bldgs)", font=get_font(13), fill=(200, 215, 235, 255))

        # Inset Anchor Thumbnails on the right side of each quadrant
        anchors = sorted((PACKS_DIR / hid).glob("anchor_*.jpg"))
        for ai, apath in enumerate(anchors[:3]):
            if Path(apath).exists():
                aim = Image.open(apath).convert("RGBA").resize((152, 86), Image.Resampling.LANCZOS)
                tx = quad_w - 166
                ty = 78 + ai * 96
                vp.alpha_composite(aim, (tx, ty))
                vd = ImageDraw.Draw(vp)
                vd.rectangle([tx, ty, tx + 152, ty + 86], outline=col, width=2)
                vd.rectangle([tx, ty + 66, tx + 152, ty + 86], fill=(8, 12, 18, 215))
                vd.text((tx + 6, ty + 68), Path(apath).stem.replace("anchor_0", "#").replace("_clean", ""), font=get_font(11, bold=True), fill=col)

        img.alpha_composite(vp, (qx, qy))
        draw.rounded_rectangle([qx, qy, qx + quad_w, qy + quad_h], radius=10, outline=col, width=3)

    out_path = VAULT_DIR / "what_happens_04_all_4_megahubs_live_3d_views.png"
    img.convert("RGB").save(out_path, quality=95)
    img.convert("RGB").save(BRAIN_DIR / out_path.name, quality=95)
    print("Saved", out_path)


def update_png_catalog():
    cat_path = SHOTS / "png_vault" / "png_catalog.json"
    if not cat_path.exists():
        return
    cat = json.loads(cat_path.read_text())
    items = [it for it in cat.get("items", []) if not str(it.get("filename", "")).startswith("what_happens_")]

    new_entries = [
        {
            "id": "atlas_splat_what_happens_01",
            "title": "What Happens #1: Naive 10-District Splat Chaos vs. .GLB + Cleaned Splat Infrastructure",
            "filename": "what_happens_01_naive_vs_infrastructure.png",
            "file": "png_vault/atlas_splats/what_happens_01_naive_vs_infrastructure.png",
            "category": "atlas_splats",
            "subcategory": "master_atlas_splat_sheet",
            "poem": "01",
            "width": 2400,
            "height": 1350,
            "desc": "Side-by-side visual simulation: Left shows the 4 hallucinations when dumping unfiltered district refs into Marble/Atlas (macro eyeball/spine turned into 40m walls, frozen wax-statue actor ghosts, broken Z-occlusion); Right shows our .GLB Chisel + Actor-Cleaned 2:1 Pano + Z-Buffer Phantom pipeline.",
        },
        {
            "id": "atlas_splat_what_happens_02",
            "title": "What Happens #2: 4-Stage .GLB + .SPLAT Infrastructure Cutaway Peel in Action",
            "filename": "what_happens_02_4step_glb_splat_pipeline_in_action.png",
            "file": "png_vault/atlas_splats/what_happens_02_4step_glb_splat_pipeline_in_action.png",
            "category": "atlas_splats",
            "subcategory": "master_atlas_splat_sheet",
            "poem": "06",
            "width": 2400,
            "height": 1350,
            "desc": "Continuous 4-zone cutaway across Club Atlantis peeling from (1) Binary .GLB Chisel & Raycast Collider -> (2) 3D Gaussian Splat Cloud -> (3) .GLB Z-Buffer Occlusion Phantom + 2.5D Actors -> (4) Final 16:9 Virtual Camera Reshoot.",
        },
        {
            "id": "atlas_splat_what_happens_03",
            "title": "What Happens #3: Twin-State Harbor Splat Morph (Poem 03 Storm Ruin <-> Poem 11 Rebuilt White Temple)",
            "filename": "what_happens_03_twin_state_harbor_morph.png",
            "file": "png_vault/atlas_splats/what_happens_03_twin_state_harbor_morph.png",
            "category": "atlas_splats",
            "subcategory": "megahub_splat_pack",
            "poem": "11",
            "width": 2400,
            "height": 1350,
            "desc": "3-panel live morph across the shared hub_02_harbor_temple_chisel.glb shoreline collider from Poem 03 Storm Ruin (0%) through 50% Mid-Morph Gaussian flight to Poem 11 Rebuilt White Temple (100%).",
        },
        {
            "id": "atlas_splat_what_happens_04",
            "title": "What Happens #4: All 4 Bang-for-Buck Mega-Hubs Live 3D Viewports (.GLB + .SPLAT + 2.5D Cast)",
            "filename": "what_happens_04_all_4_megahubs_live_3d_views.png",
            "file": "png_vault/atlas_splats/what_happens_04_all_4_megahubs_live_3d_views.png",
            "category": "atlas_splats",
            "subcategory": "megahub_splat_pack",
            "poem": "01",
            "width": 2400,
            "height": 1350,
            "desc": "2x2 full-frame 3D perspective viewports of all 4 Bang-for-Buck Mega-Hubs projecting the real .splat 3D Gaussians, .glb building wireframes, posed camera frustums A..F, and 2.5D actors.",
        },
    ]

    cat["items"] = new_entries + items
    cat["total_count"] = len(cat["items"])
    cat["atlas_splats_count"] = sum(1 for x in cat["items"] if x.get("category") == "atlas_splats")
    if isinstance(cat.get("categories"), dict):
        cat["categories"]["atlas_splats"] = cat["atlas_splats_count"]
    cat_path.write_text(json.dumps(cat, indent=2))
    print("Updated png_catalog.json -> total:", cat["total_count"], "atlas_splats:", cat["atlas_splats_count"])


def main():
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    poet_img = assemble_tracksuit_poet(360)
    build_plate_01_naive_vs_infrastructure(poet_img)
    build_plate_02_4step_pipeline(poet_img)
    build_plate_03_twin_state_morph(poet_img)
    build_plate_04_all_4_megahubs_3d(poet_img)
    update_png_catalog()


if __name__ == "__main__":
    main()
