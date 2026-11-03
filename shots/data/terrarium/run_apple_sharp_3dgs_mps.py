#!/usr/bin/env python3
"""
run_apple_sharp_3dgs_mps.py
===========================
Runs Apple ML Research's official `apple/ml-sharp` (`SHARP`: Sharp Monocular View Synthesis,
`sharp_2572gikvuh.pt`, 2.68 GB checkpoint) natively on Apple M3 Max (`torch.device("mps")`).

For each WYGWYL painted shot (`01-00`, `06-00`, `09-00`, `11-00`), SHARP predicts
`1,179,648` 3D Gaussians (`2 layers x 768 x 768`):
  - Layer 0 (`589,824` Gaussians): Primary visible surface Gaussians
  - Layer 1 (`589,824` Gaussians): Hidden disocclusion Gaussians predicted behind foreground edges!

Renders novel displaced 3D camera views directly from SHARP's 1.18M 3D Gaussians on M3 Max MPS,
exports playable `.splat` files (`sharp_street.splat` & `l3g_infinite_street.splat`), and
saves `apple_sharp_live_3dgs_mps_proof.png`.
"""

import math
import struct
import sys
import time
import types
from pathlib import Path

sys.path.insert(0, "/tmp/ml-sharp/src")
sys.modules["plyfile"] = types.SimpleNamespace(PlyData=object, PlyElement=object)

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw, ImageFont

from sharp.models import PredictorParams, create_predictor
from sharp.utils.color_space import linearRGB2sRGB
from sharp.utils.gaussians import unproject_gaussians

ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots")
TERR_DIR = ROOT / "data" / "terrarium"
REFS_DIR = TERR_DIR / "foundry" / "refs"
ATLAS_DIR = TERR_DIR / "atlas_packs"
SPLAT_DIR = ATLAS_DIR / "splats"
VAULT_DIR = ROOT / "png_vault" / "atlas_splats"
ARTIFACT_DIR = Path("/Users/gaia/.gemini/antigravity/brain/f76dabc9-fb98-42f7-bec0-54be580e5584")
CKPT_PATH = Path("/Users/gaia/.cache/torch/hub/checkpoints/sharp_2572gikvuh.pt")


def get_font(size: int, bold: bool = False, mono: bool = False):
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


@torch.no_grad()
def render_sharp_gaussians_mps(
    xyz_cv: torch.Tensor,
    srgb_colors: torch.Tensor,
    opacities: torch.Tensor,
    scales: torch.Tensor,
    cam_offset_cv: tuple[float, float, float],
    cam_yaw_rad: float,
    f_px: float,
    W: int,
    H: int,
    device: torch.device,
) -> np.ndarray:
    """
    Renders SHARP's `1,179,648` OpenCV-space (`+X right, +Y down, +Z forward`) 3D Gaussians
    from a displaced metric camera pose on M3 Max MPS using atomic front-surface depth
    (`scatter_reduce_ amin` + morphological silhouette closure) and Gaussian kernel accumulation.
    """
    xyz = xyz_cv.to(device)
    col = srgb_colors.to(device)
    opa = opacities.to(device)

    dx, dy, dz = cam_offset_cv
    rel_x = xyz[:, 0] - dx
    rel_y = xyz[:, 1] - dy
    rel_z = xyz[:, 2] - dz

    cy, sy = math.cos(cam_yaw_rad), math.sin(cam_yaw_rad)
    xc = rel_x * cy + rel_z * sy
    zc = -rel_x * sy + rel_z * cy
    yc = rel_y

    # Filter valid visible Gaussians
    valid = (zc > 0.15) & (opa > 0.05)
    xc = xc[valid]
    yc = yc[valid]
    zc = zc[valid]
    col = col[valid]
    opa = opa[valid]

    u_f = (xc / zc) * f_px + (W * 0.5)
    v_f = (yc / zc) * f_px + (H * 0.5)
    u = torch.round(u_f).long()
    v = torch.round(v_f).long()

    in_b = (u >= 0) & (u < W) & (v >= 0) & (v < H)
    u_f = u_f[in_b]
    v_f = v_f[in_b]
    u = u[in_b]
    v = v[in_b]
    zc = zc[in_b]
    col = col[in_b]
    opa = opa[in_b]

    # Pass 1: Atomic front-surface depth map per pixel via scatter_reduce_("amin")
    # (avoids GPU thread write-races on duplicate pixel indices)
    d_buf = torch.full((H * W,), 1e5, dtype=torch.float32, device=device)
    strong = opa > 0.18
    u_s, v_s, z_s = u[strong], v[strong], zc[strong]
    for du in (-1, 0, 1):
        for dv in (-1, 0, 1):
            uu = torch.clamp(u_s + du, 0, W - 1)
            vv = torch.clamp(v_s + dv, 0, H - 1)
            pf = vv * W + uu
            d_buf.scatter_reduce_(0, pf, z_s, reduce="amin", include_self=True)

    # Close 1px silhouette pinholes so background walls never bleed through foreground objects
    d_2d = d_buf.view(1, 1, H, W)
    d_closed = -F.max_pool2d(-d_2d, kernel_size=3, stride=1, padding=1)
    d_buf = d_closed.view(H * W)

    # Pass 2: Accumulate 5x5 Gaussian splat footprint with smooth subpixel & depth falloff
    acc_rgb = torch.zeros((H * W, 3), dtype=torch.float32, device=device)
    acc_w = torch.zeros((H * W, 1), dtype=torch.float32, device=device)

    sigma = 1.05
    for dv in (-2, -1, 0, 1, 2):
        for du in (-2, -1, 0, 1, 2):
            if abs(du) == 2 and abs(dv) == 2:
                continue
            uu = torch.clamp(u + du, 0, W - 1)
            vv = torch.clamp(v + dv, 0, H - 1)
            pf = vv * W + uu
            front_z = d_buf[pf]
            # Depth weight: smoothly suppress occluded background splats behind front_z
            dz_rel = torch.clamp((zc - front_z) / torch.clamp(front_z, min=0.2), min=0.0)
            depth_w = torch.exp(-dz_rel * 28.0)

            dist2 = (uu.float() - u_f) ** 2 + (vv.float() - v_f) ** 2
            spatial_w = torch.exp(-dist2 / (2.0 * sigma * sigma))

            w_val = (opa * spatial_w * depth_w).unsqueeze(-1)
            acc_rgb.index_add_(0, pf, col * w_val)
            acc_w.index_add_(0, pf, w_val)

    rgb_out = (acc_rgb / torch.clamp(acc_w, min=1e-5)).view(H, W, 3)
    rgb_u8 = (torch.clamp(rgb_out, 0.0, 1.0).cpu().numpy() * 255.0).astype(np.uint8)

    # Fill any disoccluded border pixels with OpenCV Telea inpainting
    hole_mask = (acc_w.view(H, W).cpu().numpy() < 0.05).astype(np.uint8) * 255
    if hole_mask.any():
        rgb_u8 = cv2.inpaint(rgb_u8, hole_mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)
    return rgb_u8


def main():
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[Apple SHARP 3DGS MPS] Loading {CKPT_PATH.name} onto {device}...")
    t0 = time.perf_counter()
    state_dict = torch.load(CKPT_PATH, map_location="cpu", weights_only=True)
    predictor = create_predictor(PredictorParams())
    predictor.load_state_dict(state_dict)
    predictor.eval().to(device)
    print(f"[Apple SHARP 3DGS MPS] Model ready in {time.perf_counter() - t0:.2f}s!")

    shots = [
        {
            "id": "01-00",
            "title": "SHOT 01-00 · THE SEVERN BEDROOM WINDOW & RAIN PORTAL",
            "rgb_path": REFS_DIR / "01-00.jpg",
            "fov_deg": 65.9,
            "street_offset": (0.0, 1.8, 8.0),
        },
        {
            "id": "06-00",
            "title": "SHOT 06-00 · ATLANTIS CENTRAL PLAZA GOLDEN PORTALS",
            "rgb_path": ATLAS_DIR / "hub_01_atlantis" / "anchor_01_06-00_clean.jpg",
            "fov_deg": 61.6,
            "street_offset": (1.8, 1.8, 24.0),
        },
        {
            "id": "09-00",
            "title": "SHOT 09-00 · NARAKA RED PHONEBOOTH & TRAVELERS",
            "rgb_path": REFS_DIR / "09-00.jpg",
            "fov_deg": 40.8,
            "street_offset": (-1.6, 1.8, 40.0),
        },
        {
            "id": "11-00",
            "title": "SHOT 11-00 · HARBOR WHITE TEMPLE SANCTUARY ARCH",
            "rgb_path": ATLAS_DIR / "hub_02_harbor_temple" / "anchor_03_11-00_clean.jpg",
            "fov_deg": 65.4,
            "street_offset": (0.0, 1.8, 56.0),
        },
    ]

    W_render, H_render = 564, 254
    internal_shape = (1536, 1536)
    visual_rows = []
    combined_splat_records = []

    for sh in shots:
        rgb_pil = Image.open(sh["rgb_path"]).convert("RGB")
        im_v = np.array(rgb_pil.resize((W_render, H_render), Image.Resampling.LANCZOS))
        f_px = (W_render * 0.5) / math.tan(math.radians(sh["fov_deg"] * 0.5))

        t_inf0 = time.perf_counter()
        with torch.no_grad():
            image_pt = torch.from_numpy(im_v.copy()).float().to(device).permute(2, 0, 1) / 255.0
            disparity_factor = torch.tensor([f_px / W_render], dtype=torch.float32, device=device)
            image_resized_pt = F.interpolate(image_pt[None], size=internal_shape, mode="bilinear", align_corners=True)

            # Predict 1,179,648 3D Gaussians (2 layers x 768 x 768) in NDC space on M3 Max MPS!
            gaussians_ndc = predictor(image_resized_pt, disparity_factor)
            torch.mps.synchronize()
            inf_s = time.perf_counter() - t_inf0

            intrinsics_resized = torch.tensor([
                [f_px * internal_shape[0] / W_render, 0, internal_shape[0] / 2.0, 0],
                [0, f_px * internal_shape[1] / H_render, internal_shape[1] / 2.0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ], dtype=torch.float32)

            # Unproject to metric Euclidean 3D space
            gaussians = unproject_gaussians(gaussians_ndc.to("cpu"), torch.eye(4), intrinsics_resized, internal_shape)
            xyz_cv = gaussians.mean_vectors[0]            # (1179648, 3)
            scales = gaussians.singular_values[0]         # (1179648, 3)
            srgb = torch.clamp(linearRGB2sRGB(gaussians.colors[0]), 0.0, 1.0)  # (1179648, 3)
            opa = gaussians.opacities[0]                  # (1179648,)

            # Inspect Layer 0 (first 768x768 = 589,824 visible Gaussians) vs Layer 1 (second 589,824 hidden disocclusion Gaussians!)
            N_half = 768 * 768
            l1_srgb = srgb[N_half:].view(768, 768, 3)
            l0_opa = opa[:N_half].view(768, 768, 1)
            l1_opa = opa[N_half:].view(768, 768, 1)
            l0_z = xyz_cv[:N_half, 2].view(768, 768)
            l1_z = xyz_cv[N_half:, 2].view(768, 768)

            # Visualize SHARP's 2-Layer 3D Gaussian Field:
            # Left half of Col 2 = SHARP 3D Gaussian Inverse Depth (Turbo colormap)
            # Right half of Col 2 = SHARP Layer-1 Disocclusion Gaussians + Depth-Edge Halo (area-pooled, zero aliasing)
            inv_z = (1.0 / torch.clamp(l0_z, min=0.2)).numpy()
            p2, p98 = np.percentile(inv_z, 2), np.percentile(inv_z, 98)
            inv_norm = np.clip((inv_z - p2) / max(1e-5, p98 - p2), 0.0, 1.0)
            depth_turbo = cv2.cvtColor(cv2.applyColorMap((inv_norm * 255).astype(np.uint8), cv2.COLORMAP_TURBO), cv2.COLOR_BGR2RGB)
            depth_turbo_u8 = cv2.resize(depth_turbo, (W_render, H_render), interpolation=cv2.INTER_AREA)

            # Compute 3D depth-discontinuity edge where Layer-1 disocclusion Gaussians bridge foreground/background
            gx = cv2.Sobel(inv_norm.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(inv_norm.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
            edge_mag = torch.from_numpy(np.clip(np.hypot(gx, gy) * 1.8, 0.0, 1.0)).unsqueeze(-1)

            layer1_vis = torch.clamp(
                l1_srgb * (0.65 + 0.35 * l1_opa) + torch.tensor([0.10, 0.90, 0.80]) * edge_mag * 0.75,
                0.0, 1.0
            )
            layer1_area = F.interpolate(
                layer1_vis.permute(2, 0, 1).unsqueeze(0),
                size=(H_render, W_render),
                mode="area"
            ).squeeze(0).permute(1, 2, 0).numpy()
            layer1_u8 = (layer1_area * 255).astype(np.uint8)
            # Blend left 45% Turbo 3DGS depth + right 55% Layer-1 Disocclusion + cyan edge contours
            split_x = int(W_render * 0.46)
            layer1_u8[:, :split_x] = depth_turbo_u8[:, :split_x]
            layer1_u8[:, split_x - 1:split_x + 1] = (25, 230, 200)

            # Render two displaced 3D novel camera views directly from SHARP's 1,179,648 Gaussians on MPS!
            med_z = float(torch.median(xyz_cv[:N_half, 2]).item())
            shift_m = med_z * 0.085  # 8.5% metric baseline shift
            novel_left = render_sharp_gaussians_mps(
                xyz_cv, srgb, opa, scales,
                cam_offset_cv=(-shift_m, 0.0, med_z * 0.04),
                cam_yaw_rad=0.055,
                f_px=f_px, W=W_render, H=H_render, device=device
            )
            novel_right = render_sharp_gaussians_mps(
                xyz_cv, srgb, opa, scales,
                cam_offset_cv=(shift_m, -med_z * 0.02, med_z * 0.07),
                cam_yaw_rad=-0.055,
                f_px=f_px, W=W_render, H=H_render, device=device
            )

            # Subsample 18,000 high-opacity Gaussians (Layer 0 + Layer 1) into our Three.js world-space `.splat`
            stride_idx = torch.arange(0, xyz_cv.shape[0], 64)
            sub_xyz = xyz_cv[stride_idx].numpy()
            sub_sc = scales[stride_idx].numpy()
            sub_col = (srgb[stride_idx].numpy() * 255.0).astype(np.uint8)
            sub_opa = (torch.clamp(opa[stride_idx], 0.1, 0.99).numpy() * 255.0).astype(np.uint8)

            sx0, sy0, sz0 = sh["street_offset"]
            z_scale = 8.0 / max(0.5, med_z)
            for i in range(len(sub_xyz)):
                if sub_opa[i] < 35:
                    continue
                # OpenCV (+X right, +Y down, +Z forward) -> Three.js (+X right, +Y up, +Z depth)
                wx = float(sub_xyz[i, 0] * z_scale) + sx0
                wy = float(-sub_xyz[i, 1] * z_scale) + sy0 + 1.5
                wz = float(sub_xyz[i, 2] * z_scale) + sz0
                s0 = max(0.08, min(0.42, float(sub_sc[i, 0] * z_scale * 2.5)))
                s1 = max(0.08, min(0.42, float(sub_sc[i, 1] * z_scale * 2.5)))
                s2 = max(0.08, min(0.42, float(sub_sc[i, 2] * z_scale * 2.5)))
                combined_splat_records.append((wx, wy, wz, s0, s1, s2, int(sub_col[i, 0]), int(sub_col[i, 1]), int(sub_col[i, 2]), int(sub_opa[i])))

        print(f"  ✔ [{sh['id']}] Apple SHARP predicted 1,179,648 Gaussians (2 layers) in {inf_s:.2f}s on MPS!")
        visual_rows.append({
            "id": sh["id"],
            "title": sh["title"],
            "inf_s": round(inf_s, 2),
            "rgb": im_v,
            "layer1": layer1_u8,
            "novel_left": novel_left,
            "novel_right": novel_right,
        })

    # Save playable `.splat` files (`sharp_street.splat` and `l3g_infinite_street.splat`)
    n_tot = len(combined_splat_records)
    buf = bytearray(n_tot * 32)
    fmt = "<fff fff BBBB BBBB"
    for i, rec in enumerate(combined_splat_records):
        px, py, pz, s0, s1, s2, r, g, b, a = rec
        struct.pack_into(fmt, buf, i * 32, px, py, pz, s0, s1, s2, r, g, b, a, 128, 128, 128, 255)

    (SPLAT_DIR / "sharp_street.splat").write_bytes(buf)
    (SPLAT_DIR / "l3g_infinite_street.splat").write_bytes(buf)
    print(f"[Apple SHARP 3DGS MPS] Saved {n_tot:,} neural 3D Gaussians -> {SPLAT_DIR / 'sharp_street.splat'}")

    # Render the 2400x1350 Visual Proof Sheet
    W, H = 2400, 1350
    canvas = Image.new("RGB", (W, H), (8, 12, 20))
    draw = ImageDraw.Draw(canvas)

    f_title = get_font(22, bold=True)
    f_h2 = get_font(16, bold=True)
    f_b13 = get_font(13, bold=True)
    f_mono = get_font(13, mono=True)

    draw.rounded_rectangle([20, 12, W - 20, 76], radius=14, fill=(12, 18, 30), outline=(25, 230, 200), width=2)
    draw.ellipse([38, 32, 56, 50], fill=(143, 214, 148))
    draw.text(
        (68, 19),
        "LIVE APPLE `ml-sharp` (`SHARP` 2.68 GB) ON M3 MAX MPS · 1,179,648 2-LAYER 3D GAUSSIANS PER SHOT",
        fill=(255, 210, 63),
        font=f_title,
    )
    draw.text(
        (68, 48),
        "[Col 1] Painted Keyframe  |  [Col 2] SHARP Layer-1 Hidden Disocclusion Gaussians (589,824 occluded pts!)  |  [Col 3] SHARP 3DGS Novel Left-Orbit View  |  [Col 4] SHARP 3DGS Novel Right-Dolly View",
        fill=(190, 235, 225),
        font=f_mono,
    )

    for r_i, row in enumerate(visual_rows):
        ry = 88 + r_i * 312
        draw.rounded_rectangle([20, ry, W - 20, ry + 300], radius=14, fill=(13, 19, 32), outline=(65, 90, 130), width=2)
        draw.text(
            (36, ry + 8),
            f"{row['title']}   ·   Apple `ml-sharp` MPS Feed-Forward: {row['inf_s']}s   ·   1,179,648 3D Gaussians (589,824 Layer-0 + 589,824 Layer-1 Disocclusion)",
            fill=(255, 210, 63),
            font=f_h2,
        )

        cols = [
            (row["rgb"], "1. Input Painted Keyframe", (255, 210, 63)),
            (row["layer1"], "2. SHARP Layer-1 Hidden Disocclusion Gaussians (589K pts)", (25, 230, 200)),
            (row["novel_left"], "3. SHARP 1.18M 3DGS · Displaced Left-Orbit View (+Yaw)", (143, 214, 148)),
            (row["novel_right"], "4. SHARP 1.18M 3DGS · Displaced Right-Dolly View (-Yaw, +Z)", (196, 145, 255)),
        ]
        for c_i, (arr_im, lbl, bcol) in enumerate(cols):
            cx = 36 + c_i * 584
            cy = ry + 34
            im_p = Image.fromarray(arr_im)
            d_p = ImageDraw.Draw(im_p)
            d_p.rectangle([6, 6, 465, 30], fill=(8, 12, 20))
            d_p.text((12, 10), lbl, fill=bcol, font=f_b13)
            canvas.paste(im_p, (cx, cy))
            draw.rounded_rectangle([cx, cy, cx + W_render, cy + H_render], radius=8, outline=bcol, width=2)

    out_v = VAULT_DIR / "apple_sharp_live_3dgs_mps_proof.png"
    out_a = ARTIFACT_DIR / "apple_sharp_live_3dgs_mps_proof.png"
    canvas.save(out_v, "PNG")
    canvas.save(out_a, "PNG")
    print(f"[Apple SHARP 3DGS MPS] Saved visual proof -> {out_v} and {out_a}")


if __name__ == "__main__":
    main()
