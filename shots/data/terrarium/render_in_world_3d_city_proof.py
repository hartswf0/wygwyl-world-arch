#!/usr/bin/env python3
"""
Render a true 3D In-World Perspective Scene (2400x1350):
  shots/png_vault/atlas_splats/in_world_3d_agent_worktree_city.png
Everything is physically inside the painted 3D WYGWYL Halfworld / Atlantis street:
  - Full-bleed painted Atlantis Central Plaza & Naraka Twilight sky/city horizon
  - True 3D perspective wet-asphalt street + glowing gold Poem Tape highway
  - Real 32-byte 3D Gaussian Splat cloud (hub_01_atlantis.splat) projected in 3D
  - Multiplane 3D Stage Prosceniums + painted cutout props (DJ-Decks, Phonebooth, Coin-Booth, Atlantis Forum Arch)
  - Distinct painted character cutouts (Ancestor Maestro, The Poet, The EX, The Muse, Child Traveler) standing on glowing 3D worktree pedestals
"""
import math
import struct
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch")
SHOTS_DIR = REPO_ROOT / "shots"
OUT_PATH = SHOTS_DIR / "png_vault" / "atlas_splats" / "in_world_3d_agent_worktree_city.png"
ARTIFACT_PATH = Path("/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584/in_world_3d_agent_worktree_city.png")


def load_font(size: int, bold: bool = False, mono: bool = False):
    candidates = []
    if mono:
        candidates = ["/System/Library/Fonts/SFNSMono.ttf", "/System/Library/Fonts/Menlo.ttc"]
    elif bold:
        candidates = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"]
    else:
        candidates = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def project_3d(x: float, y: float, z: float, W: int = 2400, H: int = 1350):
    cam_x, cam_y, cam_z = 0.0, 4.3, -6.5
    pitch = -0.095
    dx = x - cam_x
    dy = y - cam_y
    dz = z - cam_z
    ry = dy * math.cos(pitch) - dz * math.sin(pitch)
    rz = dy * math.sin(pitch) + dz * math.cos(pitch)
    if rz <= 0.4:
        return None
    f = 1380.0
    u = W * 0.5 + (dx / rz) * f
    v = H * 0.46 - (ry / rz) * f
    return (u, v, rz)


def warp_quad_onto_canvas(canvas_rgba: np.ndarray, src_img: Image.Image, quad_pts_2d, border_col=None, border_w=2, alpha_mul=1.0):
    H, W = canvas_rgba.shape[:2]
    src_rgba = np.array(src_img.convert("RGBA"), dtype=np.uint8)
    sh, sw = src_rgba.shape[:2]
    src_corners = np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]])
    dst_corners = np.float32(quad_pts_2d)

    M = cv2.getPerspectiveTransform(src_corners, dst_corners)
    warped = cv2.warpPerspective(src_rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    if alpha_mul < 1.0:
        warped[:, :, 3] = (warped[:, :, 3].astype(np.float32) * alpha_mul).astype(np.uint8)

    a = warped[:, :, 3:4].astype(np.float32) / 255.0
    canvas_rgba[:, :, :3] = (canvas_rgba[:, :, :3].astype(np.float32) * (1.0 - a) + warped[:, :, :3].astype(np.float32) * a).astype(np.uint8)

    if border_col is not None:
        pts_int = dst_corners.astype(np.int32).reshape((-1, 1, 2))
        cv2.polylines(canvas_rgba, [pts_int], isClosed=True, color=(border_col[0], border_col[1], border_col[2], 255), thickness=border_w, lineType=cv2.LINE_AA)


def make_terminal_texture() -> Image.Image:
    im = Image.new("RGBA", (680, 360), (5, 10, 16, 236))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, 677, 357], radius=18, outline=(25, 230, 200, 255), width=4)
    f_h = load_font(20, bold=True, mono=True)
    f_m = load_font(15, mono=True)
    d.text((20, 16), "IN-WORLD GIT WORKTREE SHELL (:8788)", fill=(255, 210, 63), font=f_h)
    lines = [
        "$ git worktree list  [exit=0 · 16ms]",
        ". [main]",
        ".worktrees/wt-103-glb-z-phantom [MOUNTED]",
        ".worktrees/wt-104-twin-state-harbor-morph [MOUNTED]",
        ".worktrees/wt-105-cache-compactor-vault [MOUNTED]",
        ".worktrees/wt-106-terrarium-splat-mounter [MOUNTED]",
        "",
        "$ POST /api/worktree/audit (WT-104)",
        "[PASS] 27,818 32-byte Gaussian splats + .glb verified",
        "$ POST /api/cache/compact -> HANDOFF_55M.md written!",
    ]
    y = 50
    for ln in lines:
        col = (255, 210, 63) if ln.startswith("$") else (143, 214, 148) if "MOUNTED" in ln or "PASS" in ln else (185, 235, 245)
        d.text((20, y), ln, fill=col, font=f_m)
        y += 28
    return im


def main():
    W, H = 2400, 1350
    canvas = np.zeros((H, W, 4), dtype=np.uint8)
    canvas[:, :, 3] = 255

    # 1. FULL-BLEED PAINTED ATLANTIS / NARAKA TWILIGHT SKY & HORIZON + WET STREET REFLECTION
    sky1_path = REPO_ROOT / "coolradio_Atlantis_City_central_plaza_vibrant_manifestation_o_fd7ea369-8f63-4dce-b893-3d539424bca0_0.png"
    sky2_path = REPO_ROOT / "coolradio_Afrofuturist_twilight_market_Naraka_Market_district_b631fc80-d330-458d-8442-3be219b56b74_0.png"
    horizon_y = int(H * 0.47)

    if sky1_path.exists():
        s1 = Image.open(sky1_path).convert("RGB").resize((W, horizon_y + 110), Image.Resampling.LANCZOS)
        if sky2_path.exists():
            s2 = Image.open(sky2_path).convert("RGB").resize((W, horizon_y + 110), Image.Resampling.LANCZOS)
            s1 = Image.blend(s1, s2, 0.42)
        canvas[: horizon_y + 110, :, :3] = np.array(s1)

        # Wet-asphalt reflection on the street ground
        refl = s1.transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((W, H - horizon_y), Image.Resampling.LANCZOS)
        refl = refl.filter(ImageFilter.GaussianBlur(radius=6))
        refl_arr = (np.array(refl, dtype=np.float32) * np.array([0.42, 0.46, 0.56])).astype(np.uint8)
        canvas[horizon_y:, :, :3] = refl_arr

    # Smooth horizon blend band
    for y in range(horizon_y - 35, horizon_y + 45):
        if 0 <= y < H:
            t = (y - (horizon_y - 35)) / 80.0
            glow = np.array([28, 38, 56], dtype=np.float32) * math.sin(t * math.pi)
            canvas[y, :, :3] = np.clip(canvas[y, :, :3].astype(np.float32) * 0.85 + glow, 0, 255).astype(np.uint8)

    # 2. TRUE 3D PERSPECTIVE FOUNDRY TERRAIN GRID ON THE STREET
    for gx in range(-48, 52, 4):
        p0 = project_3d(gx, 0.0, 1.0, W, H)
        p1 = project_3d(gx, 0.0, 75.0, W, H)
        if p0 and p1:
            col = (255, 210, 63, 255) if abs(gx) <= 4 else (38, 86, 118, 255)
            cv2.line(canvas, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), col, 1, cv2.LINE_AA)

    for gz in range(2, 76, 3):
        p0 = project_3d(-48.0, 0.0, gz, W, H)
        p1 = project_3d(48.0, 0.0, gz, W, H)
        if p0 and p1:
            cv2.line(canvas, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (32, 72, 102, 255), 1, cv2.LINE_AA)

    # 3. PROJECT REAL 32-BYTE 3D GAUSSIAN SPLAT CLOUD (`hub_01_atlantis.splat`) INTO THE 3D WORLD
    splat_path = SHOTS_DIR / "data" / "terrarium" / "atlas_packs" / "splats" / "hub_01_atlantis.splat"
    if splat_path.exists():
        raw = splat_path.read_bytes()
        n_splats = len(raw) // 32
        for i in range(0, n_splats, 3):
            off = i * 32
            sx, sy, sz = struct.unpack_from("<fff", raw, off)
            r, g, b, a = struct.unpack_from("<BBBB", raw, off + 24)
            wx = sx * 0.88
            wy = max(0.3, sy * 0.72 + 1.8)
            wz = sz * 0.85 + 36.0
            if wz < 8.0 or abs(wx) < 6.5:
                continue
            pr = project_3d(wx, wy, wz, W, H)
            if pr:
                u, v, rz = int(pr[0]), int(pr[1]), pr[2]
                if 0 <= u < W and 110 <= v < H:
                    rad = max(1, min(3, int(24.0 / rz)))
                    cv2.circle(canvas, (u, v), rad, (min(255, int(r * 1.15)), min(255, int(g * 1.15)), min(255, int(b * 1.15)), 255), -1, cv2.LINE_AA)

    # 4. CONTINUOUS GOLD POEM TAPE HIGHWAY (`play/levels/01/poem_tape.webp`) SNAKING THROUGH THE 3D STREET
    tape_path = SHOTS_DIR / "play" / "levels" / "01" / "poem_tape.webp"
    tape_im = Image.open(tape_path).convert("RGBA") if tape_path.exists() else Image.new("RGBA", (512, 128), (255, 210, 63, 220))

    def road_center_x(z_val: float) -> float:
        return math.sin(z_val * 0.095) * 4.2

    z_steps = np.linspace(68.0, 0.5, 42)
    for i in range(len(z_steps) - 1):
        z_far = float(z_steps[i])
        z_near = float(z_steps[i + 1])
        xf = road_center_x(z_far)
        xn = road_center_x(z_near)
        hw = 3.2
        p_tl = project_3d(xf - hw, 0.05, z_far, W, H)
        p_tr = project_3d(xf + hw, 0.05, z_far, W, H)
        p_br = project_3d(xn + hw, 0.05, z_near, W, H)
        p_bl = project_3d(xn - hw, 0.05, z_near, W, H)
        if p_tl and p_tr and p_br and p_bl:
            tw, th = tape_im.size
            u0 = int((i % 7) * (tw / 7))
            u1 = int(((i % 7) + 1) * (tw / 7))
            seg_crop = tape_im.crop((u0, 0, max(u0 + 4, u1), th))
            warp_quad_onto_canvas(
                canvas,
                seg_crop,
                [[p_tl[0], p_tl[1]], [p_tr[0], p_tr[1]], [p_br[0], p_br[1]], [p_bl[0], p_bl[1]]],
                border_col=None,
                alpha_mul=0.94,
            )
            cv2.line(canvas, (int(p_tl[0]), int(p_tl[1])), (int(p_bl[0]), int(p_bl[1])), (255, 210, 63, 255), 3, cv2.LINE_AA)
            cv2.line(canvas, (int(p_tr[0]), int(p_tr[1])), (int(p_br[0]), int(p_br[1])), (255, 210, 63, 255), 3, cv2.LINE_AA)

    def draw_3d_billboard(img_path_or_pil, cx: float, y0: float, cz: float, w_m: float, h_m: float, yaw: float = 0.0, border_col=(255, 210, 63), border_w=3, alpha_mul=1.0):
        if isinstance(img_path_or_pil, (str, Path)):
            p = Path(img_path_or_pil)
            if not p.exists():
                return None
            im = Image.open(p).convert("RGBA")
        else:
            im = img_path_or_pil.convert("RGBA")
        hw = w_m * 0.5
        dx = math.cos(yaw) * hw
        dz = math.sin(yaw) * hw
        p_tl = project_3d(cx - dx, y0 + h_m, cz - dz, W, H)
        p_tr = project_3d(cx + dx, y0 + h_m, cz + dz, W, H)
        p_br = project_3d(cx + dx, y0, cz + dz, W, H)
        p_bl = project_3d(cx - dx, y0, cz - dz, W, H)
        if not (p_tl and p_tr and p_br and p_bl):
            return None
        warp_quad_onto_canvas(
            canvas,
            im,
            [[p_tl[0], p_tl[1]], [p_tr[0], p_tr[1]], [p_br[0], p_br[1]], [p_bl[0], p_bl[1]]],
            border_col=border_col,
            border_w=border_w,
            alpha_mul=alpha_mul,
        )
        return (p_tl, p_tr, p_br, p_bl)

    def draw_3d_ground_ring(cx: float, cz: float, r_m: float, col=(255, 210, 63), thickness=3):
        pts = []
        for k in range(40):
            ang = (k / 40.0) * math.tau
            px = cx + math.cos(ang) * r_m
            pz = cz + math.sin(ang) * r_m
            pr = project_3d(px, 0.06, pz, W, H)
            if pr:
                pts.append([int(pr[0]), int(pr[1])])
        if len(pts) > 3:
            arr = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(canvas, [arr], isClosed=True, color=(col[0], col[1], col[2], 255), thickness=thickness, lineType=cv2.LINE_AA)

    # 5. ERECT THE IN-WORLD 3D STATIONS FROM FAR DEPTH TO NEAR FOREGROUND (USING REAL PAINTED WORLD ASSETS)

    # --- STATION E (FAR CENTER, z=42m): ATLANTIS FORUM GOLDEN FIFO MERGE ARCHWAY (`WT-105`) ---
    arch_x = road_center_x(42.0)
    arch_z = 42.0
    draw_3d_ground_ring(arch_x, arch_z, 4.4, col=(143, 214, 148), thickness=3)
    draw_3d_billboard(SHOTS_DIR / "play/levels/06/s0_ext.webp", arch_x, 0.2, 46.0, 17.5, 7.6, yaw=0.0, border_col=(143, 214, 148), border_w=3)
    draw_3d_billboard(SHOTS_DIR / "kits/packs/poem_06/cut/06.hero.forum/card_01.png", arch_x, 0.0, 42.5, 11.0, 7.2, yaw=0.0, border_col=None)
    draw_3d_billboard(SHOTS_DIR / "kits/packs/poem_01/cut/party.vintage_party.main-poses/card_01.png", arch_x, 0.0, 40.5, 3.8, 5.2, yaw=0.0, border_col=None)
    for side in (-4.8, 4.8):
        p_bot = project_3d(arch_x + side, 0.0, arch_z, W, H)
        p_top = project_3d(arch_x + side, 8.4, arch_z, W, H)
        if p_bot and p_top:
            cv2.line(canvas, (int(p_bot[0]), int(p_bot[1])), (int(p_top[0]), int(p_top[1])), (255, 210, 63, 255), 9, cv2.LINE_AA)
    p_ltop = project_3d(arch_x - 5.2, 8.4, arch_z, W, H)
    p_rtop = project_3d(arch_x + 5.2, 8.4, arch_z, W, H)
    if p_ltop and p_rtop:
        cv2.line(canvas, (int(p_ltop[0]), int(p_ltop[1])), (int(p_rtop[0]), int(p_rtop[1])), (255, 210, 63, 255), 11, cv2.LINE_AA)

    # --- STATION D (MID-FAR RIGHT, z=25m, elevated terrace y=1.8m): 55-MINUTE PROMPT-CACHE PHONEBOOTH SHRINE (`HANDOFF_55M.md`) ---
    shrine_x, shrine_z = 16.5, 25.0
    draw_3d_ground_ring(shrine_x, shrine_z, 3.0, col=(168, 85, 247), thickness=3)
    draw_3d_billboard(SHOTS_DIR / "play/levels/09/s2_ext.webp", shrine_x + 1.2, 1.8, 28.0, 12.5, 5.6, yaw=-0.28, border_col=(168, 85, 247), border_w=3)
    draw_3d_billboard(SHOTS_DIR / "kits/packs/poem_09/cut/09.props.phonebooth/card_01.png", shrine_x - 2.0, 1.6, 24.5, 3.6, 5.4, yaw=-0.15, border_col=None)
    draw_3d_billboard(SHOTS_DIR / "kits/packs/poem_08/cut/08.cast.angel.main-poses/card_02.png", shrine_x + 1.5, 1.6, 24.0, 3.5, 5.0, yaw=-0.15, border_col=None)

    # --- STATION C (MID-LEFT, z=23m, elevated terrace y=1.4m): CROSS-MODEL AUDIT GATE (`WT-104`) + THE EX ---
    ex_x, ex_z = -14.2, 23.0
    draw_3d_ground_ring(ex_x, ex_z, 2.9, col=(255, 61, 110), thickness=4)
    draw_3d_billboard(SHOTS_DIR / "play/levels/11/s2_ext.webp", ex_x - 1.6, 1.4, 26.0, 12.2, 5.5, yaw=0.26, border_col=(255, 61, 110), border_w=3)
    draw_3d_billboard(SHOTS_DIR / "play/levels/03/s1_ext.webp", ex_x - 4.2, 2.2, 22.2, 4.4, 2.5, yaw=0.35, border_col=(92, 225, 230), border_w=2)
    draw_3d_billboard(SHOTS_DIR / "play/levels/11/s1_ext.webp", ex_x + 2.8, 2.2, 22.2, 4.4, 2.5, yaw=-0.22, border_col=(143, 214, 148), border_w=2)
    draw_3d_billboard(SHOTS_DIR / "kits/packs/poem_09/cut/poet.09.main-poses/card_03.png", ex_x - 0.4, 1.2, 21.0, 2.9, 5.0, yaw=0.15, border_col=None)

    # --- STATION B (FOREGROUND LEFT, z=12.2m): DOING DJ-DECK DESK (`WT-103`) + THE POET + 3D TERMINAL SLAB ---
    poet_x, poet_z = -5.8, 12.2
    draw_3d_ground_ring(poet_x, poet_z, 2.6, col=(25, 230, 200), thickness=4)
    draw_3d_ground_ring(poet_x, poet_z, 1.9, col=(255, 210, 63), thickness=2)
    term_tex = make_terminal_texture()
    draw_3d_billboard(term_tex, poet_x - 4.1, 1.1, 12.8, 5.2, 2.9, yaw=0.34, border_col=(25, 230, 200), border_w=3)
    draw_3d_billboard(SHOTS_DIR / "kits/packs/poem_07/cut/07.props.dj-decks/card_01.png", poet_x + 1.8, 0.0, 12.4, 3.8, 2.8, yaw=-0.15, border_col=None)
    draw_3d_billboard(SHOTS_DIR / "arena/bodies/ACT-001_p0.png", poet_x, 0.0, 11.5, 2.8, 4.3, yaw=0.14, border_col=None)

    # --- STATION A & F (FOREGROUND RIGHT & CENTER, z=11.4m): PLANNING PLAZA (`WT-101`) + ANCESTOR MAESTRO + THE MUSE ---
    mama_x, mama_z = 6.2, 11.6
    draw_3d_ground_ring(mama_x, mama_z, 2.7, col=(255, 210, 63), thickness=4)
    draw_3d_billboard(SHOTS_DIR / "play/levels/01/s0_ext.webp", mama_x + 3.8, 0.3, 14.6, 9.6, 4.4, yaw=-0.34, border_col=(255, 210, 63), border_w=3)
    draw_3d_billboard(SHOTS_DIR / "kits/packs/poem_01/cut/01.hero.severn/card_01.png", mama_x - 2.2, 0.0, 12.5, 3.4, 4.8, yaw=0.18, border_col=None)
    draw_3d_billboard(SHOTS_DIR / "kits/packs/poem_08/cut/08.cast.angel.main-poses/card_01.png", mama_x + 0.4, 0.0, 10.9, 3.2, 4.5, yaw=-0.16, border_col=None)

    # The Muse in White Satin Gown & Brass Pivots Walking the Center Poem Tape Road (z=9.6m)
    draw_3d_ground_ring(0.7, 9.6, 1.8, col=(255, 159, 28), thickness=3)
    draw_3d_billboard(SHOTS_DIR / "kits/packs/poem_01/cut/party.vintage_party.main-poses/card_05.png", 0.7, 0.0, 9.5, 2.5, 4.1, yaw=0.0, border_col=None)

    # Convert to PIL to draw non-overlapping diegetic 3D world banners & translucent glass HUD pills
    pil_im = Image.fromarray(canvas[:, :, :3], mode="RGB")
    draw = ImageDraw.Draw(pil_im, "RGBA")

    f_b16 = load_font(16, bold=True)
    f_b14 = load_font(14, bold=True)
    f_mono = load_font(12, mono=True)
    f_11 = load_font(11)

    def draw_world_banner_fixed(box_x: int, box_y: int, target_3d, line1: str, line2: str, line3: str, border_col=(255, 210, 63)):
        bw, bh = 386, 74
        g_pr = project_3d(target_3d[0], target_3d[1], target_3d[2], W, H)
        if g_pr:
            draw.line([(box_x + bw // 2, box_y + bh), (int(g_pr[0]), int(g_pr[1]))], fill=(border_col[0], border_col[1], border_col[2], 210), width=2)
            draw.ellipse([int(g_pr[0]) - 5, int(g_pr[1]) - 5, int(g_pr[0]) + 5, int(g_pr[1]) + 5], fill=(border_col[0], border_col[1], border_col[2], 255))
        draw.rounded_rectangle([box_x, box_y, box_x + bw, box_y + bh], radius=12, fill=(7, 11, 18, 228), outline=(border_col[0], border_col[1], border_col[2], 255), width=2)
        draw.text((box_x + 12, box_y + 8), line1, fill=border_col, font=f_b14)
        draw.text((box_x + 12, box_y + 29), line2, fill=(92, 225, 230), font=f_mono)
        draw.text((box_x + 12, box_y + 49), line3, fill=(235, 228, 210), font=f_11)

    # Non-overlapping world-space banners with leader lines to each 3D monument
    draw_world_banner_fixed(420, 130, (ex_x, 5.2, ex_z), "STOP C · CROSS-MODEL AUDIT GATE (WT-104)", "The EX (Codex o3-pro) · .worktrees/wt-104", "PASS: Twin-State Storm <-> White Temple (27,818 splats)", (255, 61, 110))
    draw_world_banner_fixed(980, 110, (arch_x, 7.8, arch_z), "STOP E · ATLANTIS FORUM FIFO MERGE ARCH", "feat/wt-105-cache-compactor-vault [#1 IN QUEUE]", "Single-file merge gate · 0 overlapping files -> main", (143, 214, 148))
    draw_world_banner_fixed(1580, 130, (shrine_x, 5.8, shrine_z), "STOP D · 55-MIN PROMPT-CACHE PHONEBOOTH", ".worktrees/wt-103.../HANDOFF_55M.md", "The Muse compacts context at 55/60m before cache expiry", (196, 145, 255))
    draw_world_banner_fixed(460, 340, (poet_x, 3.8, poet_z), "STOP B · DOING DJ-DECK DESK (WT-103)", "The Poet · .worktrees/wt-103-glb-z-phantom", "Coding Chisel .glb Z-buffer phantom + 3D Splat in-world", (25, 230, 200))
    draw_world_banner_fixed(1420, 340, (mama_x, 4.0, mama_z), "STOP A · PLANNING PLAZA (ANCESTOR MAESTRO)", "Claude Opus 4.6 · .worktrees/wt-101-onion-peel", "Spawns isolated Git worktrees & stages multiplane plates", (255, 210, 63))
    draw_world_banner_fixed(960, 820, (0.7, 1.4, 9.5), "STOP F · THE MUSE & HOUND TRANSCRIPT BEACON", "Live transcript.jsonl tail: 9,335 steps", "Walk or tap any 3D character in the street to interact!", (255, 159, 28))

    # 6. TRANSLUCENT DIEGETIC TOP & BOTTOM GLASS HUD PILLS
    draw.rounded_rectangle([18, 14, 1160, 56], radius=21, fill=(8, 12, 18, 214), outline=(255, 210, 63, 195), width=2)
    draw.ellipse([34, 29, 46, 41], fill=(143, 214, 148, 255))
    draw.text((56, 25), "WYGWYL IN-WORLD 3D AGENT-OFFICE & GIT WORKTREE CITY · 5 WORKTREES MOUNTED ON STREET · LIVE :8788", fill=(255, 210, 63), font=f_b16)

    draw.rounded_rectangle([1680, 14, 2382, 56], radius=21, fill=(8, 12, 18, 214), outline=(25, 230, 200, 195), width=2)
    draw.text((1702, 26), "Sky: Atlantis Twilight + Hub 01 Splat (28,000 pts)  |  Terrarium III  |  Splat Studio", fill=(243, 234, 210), font=f_b14)

    by = H - 72
    draw.rounded_rectangle([18, by, W - 18, H - 14], radius=18, fill=(8, 12, 18, 224), outline=(255, 210, 63, 200), width=2)
    stops_ui = [
        ("3D World Overview", "All 6 Street Monuments", True),
        ("Stop A · Planning Plaza", "Ancestor Maestro · WT-101", False),
        ("Stop B · DJ-Deck Desk", "The Poet · WT-103 .GLB", False),
        ("Stop C · Audit Gate", "The EX · WT-104 Splat QA", False),
        ("Stop D · 55m Phonebooth", "HANDOFF_55M.md Shrine", False),
        ("Stop E · Forum Merge Arch", "Single-File Merge · WT-105", False),
        ("Stop F · Traveler Beacon", "9,335 Transcript Steps", False),
        ("+ Spawn Worktree", "git worktree add", False),
    ]
    sw = (W - 60) // len(stops_ui)
    for idx, (st_t, st_s, is_on) in enumerate(stops_ui):
        sx = 30 + idx * sw
        draw.rounded_rectangle(
            [sx, by + 7, sx + sw - 8, H - 21],
            radius=12,
            fill=(46, 38, 16, 235) if is_on else (18, 26, 38, 205),
            outline=(255, 210, 63, 255) if is_on else (92, 225, 230, 120),
            width=2 if is_on else 1,
        )
        draw.text((sx + 12, by + 13), st_t, fill=(255, 210, 63) if is_on else (243, 234, 210), font=f_b14)
        draw.text((sx + 12, by + 32), st_s, fill=(92, 225, 230) if is_on else (168, 178, 196), font=f_11)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pil_im.save(OUT_PATH, "PNG")
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pil_im.save(ARTIFACT_PATH, "PNG")
    print(f"Saved {OUT_PATH} ({OUT_PATH.stat().st_size} bytes) and copied to {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
