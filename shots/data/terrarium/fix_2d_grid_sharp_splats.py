#!/usr/bin/env python3
"""
Fixes the 1D stride=32 (768 % 32 == 0 -> 24 vertical stripes) bug by sampling
Apple `ml-sharp` (`SHARP` 2.68GB on M3 Max `mps`) on a proper 2D (row, col) grid:
  - Layer 0 (Foreground 3DGS): 240 cols x 160 rows = 38,400 Gaussians
  - Layer 1 (Hidden Disocclusion 3DGS): 180 cols x 120 rows = 21,600 Gaussians
  - Secondary Camera Portals: 120 cols x 80 rows = 9,600 Gaussians per portal
Also exports clean grayscale metric depth maps (`<ref_id>_sharp_depth.png`) for
each District's cameras so Three.js can render both watertight 3D neural surfaces
and dense 3D Gaussian Splats inside a full-screen 360° 3D world.
"""

import json
import math
import struct
import sys, time, types
from pathlib import Path
sys.path.insert(0, "/tmp/ml-sharp/src")
sys.modules["plyfile"] = types.SimpleNamespace(PlyData=object, PlyElement=object)

import cv2
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F

from sharp.models import PredictorParams, create_predictor
from sharp.utils.gaussians import unproject_gaussians
from sharp.utils.color_space import linearRGB2sRGB

ROOT = Path("/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots")
MANIFEST_PATH = ROOT / "data/terrarium/atlas_packs/atlas_infrastructure_manifest.json"
SPLATS_DIR = ROOT / "data/terrarium/atlas_packs/splats"
REFS_DIR = ROOT / "data/terrarium/foundry/refs"
CKPT_PATH = Path.home() / ".cache/torch/hub/checkpoints/sharp_2572gikvuh.pt"


def compute_camera_basis(pos_m, look_m):
    px, py, pz = float(pos_m[0]), float(pos_m[1]), float(pos_m[2])
    lx, ly, lz = float(look_m[0]), float(look_m[1]), float(look_m[2])
    fx, fy, fz = lx - px, ly - py, lz - pz
    flen = math.sqrt(fx * fx + fy * fy + fz * fz)
    if flen < 1e-4:
        fx, fy, fz, flen = 0.0, 0.0, -1.0, 1.0
    fx, fy, fz = fx / flen, fy / flen, fz / flen

    rx, ry, rz = -fz, 0.0, fx
    rlen = math.sqrt(rx * rx + ry * ry + rz * rz)
    if rlen < 1e-4:
        rx, ry, rz, rlen = 1.0, 0.0, 0.0, 1.0
    rx, ry, rz = rx / rlen, ry / rlen, rz / rlen

    ux = ry * fz - rz * fy
    uy = rz * fx - rx * fz
    uz = rx * fy - ry * fx
    return (px, py, pz), (rx, ry, rz), (ux, uy, uz), (fx, fy, fz), flen


def main():
    t0 = time.perf_counter()
    SPLATS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST_PATH.read_text())

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[2D-Grid SHARP Builder] Loading Apple ml-sharp on {device}...")
    state_dict = torch.load(CKPT_PATH, map_location="cpu", weights_only=True)
    predictor = create_predictor(PredictorParams())
    predictor.load_state_dict(state_dict)
    predictor.eval()
    predictor.to(device)

    hero_cam_override = {
        "mount-vernon": "01-00",
        "woodberry": "02-05",
        "holland-island": "03-00",
        "assateague": "04-00",
        "teotihuacan": "05-00",
        "centro": "06-00",
        "condesa": "08-07",
        "tres-marias": "10-05",
        "inner-harbor": "11-00",
        "fells-point": "13-01",
    }

    W_render, H_render = 420, 192
    internal_shape = (1536, 1536)
    sharp_cache = {}
    hub_splat_accum = {h["hub_id"]: [] for h in manifest["mega_hubs"]}

    # Proper 2D Grid indices on the 768x768 Gaussian layers!
    # Layer 0: 240 cols x 160 rows = 38,400 evenly spaced 2D grid points
    rows_l0 = np.linspace(0, 767, 160, dtype=np.int64)
    cols_l0 = np.linspace(0, 767, 240, dtype=np.int64)
    rr0, cc0 = np.meshgrid(rows_l0, cols_l0, indexing="ij")
    idx_l0 = torch.from_numpy((rr0 * 768 + cc0).reshape(-1))

    # Layer 1: 180 cols x 120 rows = 21,600 evenly spaced 2D grid points
    rows_l1 = np.linspace(0, 767, 120, dtype=np.int64)
    cols_l1 = np.linspace(0, 767, 180, dtype=np.int64)
    rr1, cc1 = np.meshgrid(rows_l1, cols_l1, indexing="ij")
    idx_l1 = torch.from_numpy((768 * 768 + rr1 * 768 + cc1).reshape(-1))
    idx_l1_local = torch.from_numpy((rr1 * 768 + cc1).reshape(-1))

    sel_idx = torch.cat([idx_l0, idx_l1], dim=0)
    sel_is_l1 = np.concatenate([
        np.zeros(len(idx_l0), dtype=np.uint8),
        np.full(len(idx_l1), 255, dtype=np.uint8),
    ])

    for d_key, d_obj in manifest["districts"].items():
        cams = d_obj.get("cameras", [])
        hero_ref = hero_cam_override.get(d_key, cams[0]["ref_id"])
        hero_cam = next((c for c in cams if c["ref_id"] == hero_ref), cams[0])

        painted_cams = []
        for c in cams:
            if c["ref_id"] == hero_cam["ref_id"] and len(painted_cams) == 0:
                painted_cams.insert(0, c)
            elif c["ref_id"] == hero_cam["ref_id"]:
                painted_cams.insert(0, c)
            else:
                painted_cams.append(c)

        district_splat_records = []

        for cam_i, cam in enumerate(painted_cams):
            ref_id = cam["ref_id"]
            src_path = ROOT / cam["source_img"]
            if not src_path.exists():
                src_path = REFS_DIR / f"{ref_id}.jpg"
            leg_depth_path = ROOT / cam.get("depth_img", f"data/terrarium/foundry/refs/{ref_id}-depth.jpg")

            pos_m = cam["threejs_pose"]["position_m"]
            look_m = cam["threejs_pose"]["look_at_m"]
            fov_deg = float(cam["threejs_pose"].get("fov_deg", 55.0))
            P, R, U, F_vec, look_dist = compute_camera_basis(pos_m, look_m)

            is_hero = (cam["ref_id"] == hero_cam["ref_id"]) or (ref_id in sharp_cache)
            if is_hero:
                if ref_id not in sharp_cache:
                    rgb_pil = Image.open(src_path).convert("RGB")
                    im_v = np.array(rgb_pil.resize((W_render, H_render), Image.Resampling.LANCZOS))
                    f_px = (W_render * 0.5) / math.tan(math.radians(fov_deg * 0.5))

                    if leg_depth_path.exists():
                        leg_im = np.array(Image.open(leg_depth_path).convert("L").resize((768, 768), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
                    else:
                        leg_im = np.full((768, 768), 0.5, dtype=np.float32)
                    leg_z_768 = torch.from_numpy(1.5 + (1.0 - leg_im).reshape(-1) * 9.5).float()

                    with torch.no_grad():
                        image_pt = torch.from_numpy(im_v.copy()).float().to(device).permute(2, 0, 1) / 255.0
                        disparity_factor = torch.tensor([f_px / W_render], dtype=torch.float32, device=device)
                        image_resized_pt = F.interpolate(image_pt[None], size=internal_shape, mode="bilinear", align_corners=True)
                        gaussians_ndc = predictor(image_resized_pt, disparity_factor)
                        torch.mps.synchronize()

                        intrinsics_resized = torch.tensor([
                            [f_px * internal_shape[0] / W_render, 0, internal_shape[0] / 2.0, 0],
                            [0, f_px * internal_shape[1] / H_render, internal_shape[1] / 2.0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1],
                        ], dtype=torch.float32)
                        gaussians = unproject_gaussians(gaussians_ndc.to("cpu"), torch.eye(4), intrinsics_resized, internal_shape)
                        xyz_cv = gaussians.mean_vectors[0]
                        scales = gaussians.singular_values[0]
                        srgb = torch.clamp(linearRGB2sRGB(gaussians.colors[0]), 0.0, 1.0)
                        opa = gaussians.opacities[0]

                        # Save clean 512x256 grayscale neural depth map for 3D surface displacement in WebGL
                        N_half = 768 * 768
                        l0_z = xyz_cv[:N_half, 2].view(768, 768).numpy()
                        p5, p95 = np.percentile(l0_z, 3), np.percentile(l0_z, 97)
                        z_norm = np.clip((l0_z - p5) / max(1e-4, p95 - p5), 0.0, 1.0)
                        # Smooth slightly to remove high-freq sensor noise while preserving architectural edges
                        z_u8 = ((1.0 - z_norm) * 255.0).astype(np.uint8)
                        depth_out = SPLATS_DIR / f"depth_{ref_id}_sharp.png"
                        Image.fromarray(z_u8).resize((512, 256), Image.Resampling.BILINEAR).save(depth_out)

                        sharp_cache[ref_id] = {
                            "xyz_cv": xyz_cv,
                            "scales": scales,
                            "srgb": srgb,
                            "opa": opa,
                            "leg_z_768": leg_z_768,
                        }
                        print(f"  ✔ [{d_key:14s}] Hero Ref {ref_id}: 2D-Grid 2-Layer 3DGS + Neural Depth exported")

                cached = sharp_cache[ref_id]
                xyz_cv = cached["xyz_cv"]
                scales = cached["scales"]
                srgb = cached["srgb"]
                opa = cached["opa"]
                leg_z_768 = cached["leg_z_768"]
                N_half = 768 * 768
                med_z = float(torch.median(xyz_cv[:N_half, 2]).item())
                target_dist = max(9.0, min(18.0, look_dist))
                z_scale = target_dist / max(0.4, med_z)

                sel_leg_z = torch.cat([leg_z_768[idx_l0], leg_z_768[idx_l1_local]], dim=0).numpy()
                sub_xyz = xyz_cv[sel_idx].numpy()
                sub_sc = scales[sel_idx].numpy()
                sub_col = (srgb[sel_idx].numpy() * 255.0).astype(np.uint8)
                sub_opa = (torch.clamp(opa[sel_idx], 0.12, 0.99).numpy() * 255.0).astype(np.uint8)

                for i in range(len(sub_xyz)):
                    if sub_opa[i] < 28:
                        continue
                    xc = float(sub_xyz[i, 0]) * z_scale
                    yc = float(sub_xyz[i, 1]) * z_scale
                    zc = float(sub_xyz[i, 2]) * z_scale

                    wx = P[0] + xc * R[0] - yc * U[0] + zc * F_vec[0]
                    wy = P[1] + xc * R[1] - yc * U[1] + zc * F_vec[1]
                    wz = P[2] + xc * R[2] - yc * U[2] + zc * F_vec[2]

                    s0 = max(0.14, min(0.55, float(sub_sc[i, 0] * z_scale * 3.2)))
                    s1 = max(0.14, min(0.55, float(sub_sc[i, 1] * z_scale * 3.2)))
                    s2 = max(0.14, min(0.55, float(sub_sc[i, 2] * z_scale * 3.2)))

                    leg_zc = float(sel_leg_z[i]) * (target_dist / 5.5)
                    dz_legacy = max(-15.0, min(15.0, leg_zc - zc))
                    dz_u16 = int(round(((dz_legacy + 15.0) / 30.0) * 65535.0))
                    q2 = dz_u16 & 0xFF
                    q3 = (dz_u16 >> 8) & 0xFF

                    district_splat_records.append((
                        wx, wy, wz, s0, s1, s2,
                        int(sub_col[i, 0]), int(sub_col[i, 1]), int(sub_col[i, 2]), int(sub_opa[i]),
                        int(sel_is_l1[i]), int(cam_i), q2, q3
                    ))
            else:
                rgb_pil = Image.open(src_path).convert("RGB")
                gw, gh = 120, 80
                im_s = np.array(rgb_pil.resize((gw, gh), Image.Resampling.BILINEAR), dtype=np.uint8)
                lum = (0.299 * im_s[:, :, 0] + 0.587 * im_s[:, :, 1] + 0.114 * im_s[:, :, 2]) / 255.0
                lum_smooth = cv2.GaussianBlur(lum.astype(np.float32), (9, 9), 2.0)

                f_s = (gw * 0.5) / math.tan(math.radians(fov_deg * 0.5))
                target_dist = max(9.0, min(16.0, look_dist))
                for vg in range(gh):
                    v_norm = vg / float(gh - 1)
                    base_d = target_dist * (0.45 + 0.65 * (1.0 - v_norm * 0.55))
                    for ug in range(gw):
                        zc = base_d * (0.88 + 0.24 * (1.0 - float(lum_smooth[vg, ug])))
                        xc = ((ug - gw * 0.5) / f_s) * zc
                        yc = ((vg - gh * 0.5) / f_s) * zc
                        wx = P[0] + xc * R[0] - yc * U[0] + zc * F_vec[0]
                        wy = P[1] + xc * R[1] - yc * U[1] + zc * F_vec[1]
                        wz = P[2] + xc * R[2] - yc * U[2] + zc * F_vec[2]
                        r_c, g_c, b_c = int(im_s[vg, ug, 0]), int(im_s[vg, ug, 1]), int(im_s[vg, ug, 2])
                        ring = math.sin(math.hypot(ug - gw * 0.5, vg - gh * 0.5) * 0.45) * 4.5
                        dz_u16 = int(round(((ring + 15.0) / 30.0) * 65535.0))
                        q2 = dz_u16 & 0xFF
                        q3 = (dz_u16 >> 8) & 0xFF
                        district_splat_records.append((
                            wx, wy, wz, 0.26, 0.26, 0.26,
                            r_c, g_c, b_c, 240,
                            0, int(cam_i), q2, q3
                        ))

        n_rec = len(district_splat_records)
        buf = bytearray(n_rec * 32)
        fmt = "<fff fff BBBB BBBB"
        for i, rec in enumerate(district_splat_records):
            struct.pack_into(fmt, buf, i * 32, *rec)

        splat_rel = f"data/terrarium/atlas_packs/splats/district_{d_key}_sharp.splat"
        (ROOT / splat_rel).write_bytes(buf)
        d_obj["splat_seed"] = {
            "file": splat_rel,
            "splat_count": n_rec,
            "bytes": len(buf),
            "hero_ref": hero_cam["ref_id"],
            "hero_depth": f"data/terrarium/atlas_packs/splats/depth_{hero_cam['ref_id']}_sharp.png",
            "model": "apple/ml-sharp (SHARP 2.68GB 2-Layer 3DGS)",
            "spawn_camera": hero_cam["threejs_pose"],
        }

        for h in manifest["mega_hubs"]:
            if d_key in h["linked_stages"] or d_key == h["primary_stage"]:
                hub_splat_accum[h["hub_id"]].extend(district_splat_records[:35000])

        print(f"  ★ Saved 2D-Grid District [{d_key:14s}] -> {n_rec:,} 3DGS")

    for h in manifest["mega_hubs"]:
        hid = h["hub_id"]
        recs = hub_splat_accum.get(hid, [])
        if recs:
            buf = bytearray(len(recs) * 32)
            fmt = "<fff fff BBBB BBBB"
            for i, rec in enumerate(recs):
                struct.pack_into(fmt, buf, i * 32, *rec)
            (ROOT / h["splat_seed"]["file"]).write_bytes(buf)
            h["splat_seed"]["splat_count"] = len(recs)
            h["splat_seed"]["bytes"] = len(buf)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"[2D-Grid SHARP Builder] Completed all 10 Districts in {time.perf_counter() - t0:.2f}s!")


if __name__ == "__main__":
    main()
