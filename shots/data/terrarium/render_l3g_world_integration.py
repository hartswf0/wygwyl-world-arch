#!/usr/bin/env python3
"""
Render a visual architecture & in-world demonstration showing how KAIST CVLab's
L3G-World (Latent 3D Gaussian Memory + Video DiT) integrates into the WYGWYL
painted world to solve:
1. Pre-Seeded Multi-Keyframe L3G-Mem (anchoring our 14 painted poems in 3D latent space)
2. Disocclusion & Alleyway Adaptive Spawning (filling behind Onion Depth L1/L2 arches)
3. Infinite Corridor Bridging + Loop-Closure Consistency -> Distilled to 60 FPS WebGL .splat
"""
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots")
OUT_PATH = ROOT / "png_vault" / "atlas_splats" / "l3g_world_wygwyl_integration.png"
ARTIFACT_PATH = Path("/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584/l3g_world_wygwyl_integration.png")

def load_font(size: int, bold: bool = False, mono: bool = False):
    candidates = []
    if mono:
        candidates = ["/System/Library/Fonts/SFNSMono.ttf", "/System/Library/Fonts/Menlo.ttc"]
    elif bold:
        candidates = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"]
    else:
        candidates = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

def crop_fill(im: Image.Image, w: int, h: int) -> Image.Image:
    iw, ih = im.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    im_r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x0 = (nw - w) // 2
    y0 = (nh - h) // 2
    return im_r.crop((x0, y0, x0 + w, y0 + h))

def main():
    W, H = 2400, 1350
    bg = Image.new("RGBA", (W, H), (8, 11, 18, 255))

    # Full-bleed darkened painted Atlantis/Naraka world backdrop
    sky_path = ROOT / "coolradio_Atlantis_City_central_plaza_vibrant_manifestation_o_fd7ea369-8f63-4dce-b893-3d539424bca0_0.png"
    if sky_path.exists():
        sky = crop_fill(Image.open(sky_path).convert("RGBA"), W, H)
        sky = sky.filter(ImageFilter.GaussianBlur(radius=3))
        dark = Image.new("RGBA", (W, H), (7, 10, 18, 195))
        bg = Image.alpha_composite(sky, dark)

    draw = ImageDraw.Draw(bg, "RGBA")
    f_title = load_font(24, bold=True)
    f_h2 = load_font(18, bold=True)
    f_b15 = load_font(15, bold=True)
    f_14 = load_font(14)
    f_13 = load_font(13)
    f_mono = load_font(13, mono=True)
    f_mono_sm = load_font(12, mono=True)

    # Top Header Bar
    draw.rounded_rectangle([24, 18, W - 24, 78], radius=16, fill=(10, 15, 26, 235), outline=(255, 210, 63, 220), width=2)
    draw.ellipse([44, 38, 62, 56], fill=(25, 230, 200, 255))
    draw.text((76, 26), "HOW WE USE KAIST L3G-WORLD IN WYGWYL · LATENT 3D GAUSSIAN MEMORY (L3G-Mem) + VIDEO DiT (L3G-Gen)", fill=(255, 210, 63), font=f_title)
    draw.text((76, 54), "Solving the 3 Core Bottlenecks: (1) Multi-Keyframe Anchor Injection  ·  (2) Disocclusion Alley Spawning  ·  (3) Latent-to-WebGL .splat Distillation", fill=(190, 215, 235), font=f_14)

    # ── LEFT PANEL: THE 3 CORE ISSUES WITH RAW L3G-WORLD & OUR WYGWYL FIXES (x=24..790, y=96..680) ──
    draw.rounded_rectangle([24, 96, 790, 680], radius=18, fill=(10, 15, 25, 230), outline=(255, 107, 139, 210), width=2)
    draw.text((44, 114), "1. THE 3 ISSUES WITH RAW L3G-WORLD (& OUR FIXES)", fill=(255, 107, 139), font=f_h2)

    issues = [
        (
            "ISSUE A · Single-Image Drift vs. Our 14 Painted Poems",
            "Raw L3G-World starts from 1 image and hallucinates forward.",
            "WYGWYL FIX: Pre-Seed L3G-Mem with All 62 Painted Keyframes",
            "We encode our 62 clean plates + Onion Depth masks via the VAE and unproject",
            "them into L3G-Mem along the Poem Tape spline BEFORE running L3G-Gen.",
            "L3G-Gen then bridges the interstitial streets directly into our real art!",
            (255, 210, 63),
        ),
        (
            "ISSUE B · VAE Latent Gaussians != 60 FPS Browser WebGL",
            "L3G-Mem stores heavy DiT VAE latents (9 FPS on A100/RTX GPU).",
            "WYGWYL FIX: Offline Corridor Baker -> 32-Byte RGB .splat",
            "We run L3G-World along the Poem Tape camera trajectory on the server,",
            "decode RGB + metric depth with loop-closure guarantees, and bake",
            "standard 32-byte .splat chunks for 60 FPS desktop/mobile WebGL.",
            (25, 230, 200),
        ),
        (
            "ISSUE C · 2D Cutout Cast Baking as Frozen Statues",
            "Feeding raw shots bakes The Poet & The Muse into static background Gaussians.",
            "WYGWYL FIX: Clean-Plate L3G-Mem + Live Brass-Pivot Foreground",
            "Only clean background plates (`s0_ext.webp`) enter L3G-Mem; our",
            "articulated 2.5D character rigs walk live inside the Three.js scene.",
            "Zero ghosting, full 360-degree loop-consistent streets.",
            (168, 130, 255),
        ),
    ]

    iy = 152
    for title, prob, fix_t, l1, l2, l3, col in issues:
        draw.rounded_rectangle([42, iy, 772, iy + 162], radius=12, fill=(16, 23, 38, 235), outline=(col[0], col[1], col[2], 190), width=2)
        draw.text((58, iy + 10), title, fill=(255, 130, 150), font=f_b15)
        draw.text((58, iy + 32), f"Problem: {prob}", fill=(210, 195, 195), font=f_13)
        draw.line([(58, iy + 56), (756, iy + 56)], fill=(col[0], col[1], col[2], 90), width=1)
        draw.text((58, iy + 64), fix_t, fill=col, font=f_b15)
        draw.text((58, iy + 88), l1, fill=(235, 240, 248), font=f_13)
        draw.text((58, iy + 108), l2, fill=(235, 240, 248), font=f_13)
        draw.text((58, iy + 128), l3, fill=(143, 214, 148), font=f_mono_sm)
        iy += 174

    # ── CENTER-RIGHT PANEL: IN-WORLD 3D DIAGRAM OF PRE-SEEDED L3G-MEM ALONG THE POEM TAPE (x=810..2376, y=96..680) ──
    draw.rounded_rectangle([810, 96, 2376, 680], radius=18, fill=(10, 15, 25, 225), outline=(25, 230, 200, 220), width=2)
    draw.text((832, 114), "2. IN-WORLD PIPELINE: PRE-SEEDED L3G-MEM BRIDGING POEM 01 (SEVERN) -> POEM 06 (ATLANTIS) -> POEM 09 (NARAKA)", fill=(25, 230, 200), font=f_h2)
    draw.text((832, 140), "Anchored Painted Keyframe Gaussians (Gold) + L3G-Mem Adaptively Spawned Corridor & Disocclusion Gaussians (Cyan/Violet) along the Poem Tape Trajectory", fill=(215, 225, 240), font=f_14)

    # Render a rich visual corridor canvas inside [830, 170, 2356, 660]
    cw, ch = 1526, 486
    corridor = Image.new("RGBA", (cw, ch), (9, 14, 24, 255))
    cdraw = ImageDraw.Draw(corridor, "RGBA")

    # Perspective grid on corridor floor
    for gx in range(-12, 13):
        x_top = cw // 2 + gx * 28
        x_bot = cw // 2 + gx * 115
        cdraw.line([(x_top, 160), (x_bot, ch)], fill=(35, 65, 95, 110), width=1)
    for gz in range(1, 10):
        t = (gz / 9.0) ** 1.6
        y_line = int(160 + t * (ch - 160))
        cdraw.line([(0, y_line), (cw, y_line)], fill=(35, 65, 95, 110), width=1)

    # Golden Poem Tape winding from Anchor 1 (Left) -> L3G-Gen Bridge (Center) -> Anchor 2 (Right-Mid) -> Anchor 3 (Far Right)
    pts_road = []
    for s in range(60):
        u = s / 59.0
        rx = int(120 + u * 1280)
        ry = int(380 - math.sin(u * math.pi * 1.6) * 85 - u * 110)
        pts_road.append((rx, ry))
    for i in range(len(pts_road) - 1):
        p0, p1 = pts_road[i], pts_road[i + 1]
        cdraw.line([p0, (p1[0], p1[1])], fill=(255, 210, 63, 220), width=18)
        cdraw.line([(p0[0], p0[1] - 9), (p1[0], p1[1] - 9)], fill=(25, 230, 200, 240), width=2)
        cdraw.line([(p0[0], p0[1] + 9), (p1[0], p1[1] + 9)], fill=(25, 230, 200, 240), width=2)

    # Draw Latent 3D Gaussian Ellipsoids along the trajectory:
    # - Gold/Warm Gaussians = Pre-seeded from our painted keyframes + Onion Depth
    # - Cyan/Purple Gaussians = Adaptively spawned by L3G-Mem in interstitial corridors & disoccluded alleys
    rng = np.random.default_rng(42)
    for i, (rx, ry) in enumerate(pts_road):
        is_anchor = (i < 12) or (25 <= i <= 36) or (i > 48)
        for _ in range(18):
            ox = int(rng.normal(0, 42))
            oy = int(rng.normal(-45, 38))
            ew = int(rng.integers(8, 22))
            eh = int(rng.integers(5, 14))
            if is_anchor:
                col = (255, int(rng.integers(180, 235)), int(rng.integers(50, 110)), 145)
            else:
                col = (int(rng.integers(25, 160)), int(rng.integers(160, 245)), 255, 150)
            cdraw.ellipse([rx + ox - ew, ry + oy - eh, rx + ox + ew, ry + oy + eh], fill=col, outline=(255, 255, 255, 70))

    # Place the 3 Painted Keyframe Cards + 2 Interstitial L3G-Gen Bridge Cards
    cards = [
        (40, 175, 290, 180, ROOT / "play/levels/01/s0_ext.webp", "ANCHOR 1 · POEM 01 SEVERN", "Pre-Seeded L3G-Mem Keyframe", "Onion Depth L0..L4 -> VAE Latents", (255, 210, 63)),
        (375, 52, 310, 185, ROOT / "play/levels/03/s1_ext.webp", "L3G-GEN CORRIDOR BRIDGE #1", "Adaptively Spawned Gaussians", "Fills 45m alley + behind-arch parallax", (25, 230, 200)),
        (730, 215, 300, 180, ROOT / "play/levels/06/s0_ext.webp", "ANCHOR 2 · POEM 06 FORUM", "Loop-Closure Verified Keyframe", "Zero drift when camera turns 180 deg", (255, 210, 63)),
        (1070, 42, 310, 185, ROOT / "play/levels/09/s2_ext.webp", "L3G-GEN CORRIDOR BRIDGE #2", "9 FPS DiT -> Baked .splat", "Distilled into 32-byte WebGL splats", (192, 132, 252)),
    ]
    for cx, cy, w_c, h_c, img_p, t1, t2, t3, bcol in cards:
        cdraw.rounded_rectangle([cx, cy, cx + w_c, cy + h_c], radius=12, fill=(10, 15, 26, 240), outline=(bcol[0], bcol[1], bcol[2], 255), width=3)
        if img_p.exists():
            im_c = crop_fill(Image.open(img_p).convert("RGBA"), w_c - 12, h_c - 68)
            corridor.paste(im_c, (cx + 6, cy + 6))
        cdraw.text((cx + 10, cy + h_c - 58), t1, fill=bcol, font=f_b15)
        cdraw.text((cx + 10, cy + h_c - 38), t2, fill=(240, 244, 250), font=f_13)
        cdraw.text((cx + 10, cy + h_c - 20), t3, fill=(143, 214, 148), font=f_mono_sm)

    # Paste live cutout characters walking the L3G-Mem corridor
    poet_p = ROOT / "arena/bodies/ACT-001_p0.png"
    if poet_p.exists():
        p_im = Image.open(poet_p).convert("RGBA")
        p_im.thumbnail((150, 210), Image.Resampling.LANCZOS)
        corridor.alpha_composite(p_im, (315, 255))

    muse_p = ROOT / "kits/packs/poem_01/cut/party.vintage_party.main-poses/card_05.png"
    if muse_p.exists():
        m_im = Image.open(muse_p).convert("RGBA")
        m_im.thumbnail((150, 210), Image.Resampling.LANCZOS)
        corridor.alpha_composite(m_im, (1035, 245))

    angel_p = ROOT / "kits/packs/poem_08/cut/08.cast.angel.main-poses/card_01.png"
    if angel_p.exists():
        a_im = Image.open(angel_p).convert("RGBA")
        a_im.thumbnail((165, 220), Image.Resampling.LANCZOS)
        corridor.alpha_composite(a_im, (1345, 195))

    # Legend pill at bottom of corridor
    cdraw.rounded_rectangle([18, ch - 46, cw - 18, ch - 10], radius=10, fill=(7, 11, 18, 230), outline=(255, 210, 63, 180), width=1)
    cdraw.ellipse([32, ch - 35, 46, ch - 21], fill=(255, 210, 63, 255))
    cdraw.text((54, ch - 36), "GOLD GAUSSIANS = Pre-Seeded from WYGWYL Painted Plates + Metric Depth", fill=(255, 210, 63), font=f_b15)
    cdraw.ellipse([650, ch - 35, 664, ch - 21], fill=(25, 230, 200, 255))
    cdraw.text((674, ch - 36), "CYAN / VIOLET GAUSSIANS = Spawned by L3G-Mem in Unseen Alleys & Disocclusions (O(Physical Area) Memory)", fill=(25, 230, 200), font=f_b15)

    bg.alpha_composite(corridor, (830, 174))

    # ── BOTTOM ROW: 4 HIGH-LEVERAGE WAYS WE USE L3G-WORLD + COMPARISON VS. WORLD LABS ATLAS (y=700..1328) ──
    draw.rounded_rectangle([24, 700, 2376, 1328], radius=18, fill=(10, 15, 25, 235), outline=(255, 210, 63, 210), width=2)
    draw.text((44, 718), "3. THE 4 CONCRETE WAYS WE USE L3G-WORLD ALONGSIDE WORLD LABS ATLAS & ONION DEPTH", fill=(255, 210, 63), font=f_h2)

    cols_data = [
        (
            "USE CASE 1 · INTER-HUB CORRIDOR BRIDGING",
            "Connects Our 4 Atlas Megahubs into 1 Continuous Walk",
            "play/levels/01/s1_ext.webp",
            [
                "• World Labs Atlas builds 4 bounded Megahubs (~45m radius).",
                "• L3G-World excels at long-horizon camera trajectories where",
                "  memory scales with physical street area, not frame count.",
                "• We feed the Catmull-Rom Poem Tape spline (`P01 -> P14`)",
                "  into L3G-World to generate the connecting alleyways",
                "  and bridges between Severn, Harbor, Atrium & Naraka.",
                "• Output: `shots/atlas_splats/corridor_01_to_02.splat`.",
            ],
            (255, 210, 63),
        ),
        (
            "USE CASE 2 · DISOCCLUSION POCKET SPAWNING",
            "Fills Behind-Pillar Shadows in Onion Depth Peels",
            "play/levels/06/s1_ext.webp",
            [
                "• In Onion Depth (`shots/onion_depth/`), moving the camera",
                "  more than +/-3m sideways exposes gaps behind L1/L2 arches.",
                "• L3G-Mem's adaptive updater spawns new 3D Gaussians ONLY",
                "  in newly disoccluded pixels while keeping L0..L4 locked!",
                "• A +/-25 deg orbital camera sweep around each of our 62",
                "  shots populates true 3D geometry behind every pillar.",
                "• Output: Full parallax look-around with zero stretched edges.",
            ],
            (25, 230, 200),
        ),
        (
            "USE CASE 3 · 360° LOOP-CLOSURE CONSISTENCY",
            "Eliminates Seam Drift When Turning Around in a Room",
            "play/levels/11/s1_ext.webp",
            [
                "• Standard video models forget the wall behind you as soon",
                "  as it leaves the sliding window.",
                "• Because L3G-Mem stores persistent 3D latent Gaussians in",
                "  world space, turning 360 deg or walking out & back into",
                "  The Severn projects the exact original latents into L3G-Gen.",
                "• Guarantees zero seam mismatch at the +/-180 deg wrap line",
                "  of our equirectangular horizons (`shots/equirec/`).",
            ],
            (143, 214, 148),
        ),
        (
            "USE CASE 4 · LIVE :8788 DREAM-WALK STREAMER",
            "Real-Time 9 FPS Infinite Street Exploration + Auto-Bake",
            "play/levels/09/s1_ext.webp",
            [
                "• When a GPU worker connects to `agent_office_server.py`",
                "  (`:8788`), walking off the edge of the baked street sends",
                "  your live Three.js 6-DoF camera pose to L3G-World.",
                "• L3G-Mem renders latent Gaussians directly (no RGB->VAE",
                "  re-encoding bottleneck!) and streams 9 FPS video + depth.",
                "• Visited L3G-Mem Gaussians are automatically distilled into",
                "  permanent `.splat` files inside the active Git worktree!",
            ],
            (192, 132, 252),
        ),
    ]

    card_w = 562
    for idx, (ctitle, csub, img_rel, bullets, bcol) in enumerate(cols_data):
        bx = 44 + idx * (card_w + 18)
        by = 758
        bh = 548
        draw.rounded_rectangle([bx, by, bx + card_w, by + bh], radius=14, fill=(15, 22, 36, 240), outline=(bcol[0], bcol[1], bcol[2], 215), width=2)
        draw.text((bx + 16, by + 14), ctitle, fill=bcol, font=f_b15)
        draw.text((bx + 16, by + 36), csub, fill=(235, 240, 248), font=f_13)

        im_path = ROOT / img_rel
        if im_path.exists():
            thumb = crop_fill(Image.open(im_path).convert("RGBA"), card_w - 32, 210)
            bg.paste(thumb, (bx + 16, by + 62))
            draw.rounded_rectangle([bx + 16, by + 62, bx + card_w - 16, by + 272], radius=8, outline=(bcol[0], bcol[1], bcol[2], 180), width=2)

        ty = by + 288
        for b_line in bullets:
            draw.text((bx + 16, ty), b_line, fill=(215, 225, 238) if not b_line.startswith("• Output:") else bcol, font=f_14 if not b_line.startswith("• Output:") else f_mono_sm)
            ty += 33

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(OUT_PATH, "PNG")
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(ARTIFACT_PATH, "PNG")
    print(f"Saved {OUT_PATH} and copied to {ARTIFACT_PATH}")

if __name__ == "__main__":
    main()
