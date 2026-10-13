#!/usr/bin/env python3
"""
fuse_district.py — Experiment 1: Multi-Shot District Spatial Co-registration.

Fuses multiple independent DepthPro point clouds from the same district into
a single, unified metric 3D coordinate space and 3D Gaussian Splat.

For Cortex Commons (5 shots):
  1. bdc7d6ec_2: Center ground plaza under dish (anchor)
  2. 7df17df5_2: Elevated terrace overlooking the plaza
  3. cf180ca2_0: South high balcony overlooking canopy
  4. 245fd8b5_3: East undercroft looking up at spires
  5. e0154328_1: West entrance corridor entering the plaza

Transform:
  P_world = R_yaw * (R_level * P_cam + [0, H_cam, 0]) + [X_plaza, 0, Z_plaza]
"""
import argparse, glob, json, math, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "shots", "out")
DIST_OUT_DIR = os.path.join(OUT_DIR, "districts")


def rot_x(rad):
    c, s = np.cos(rad), np.sin(rad)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=np.float32)


def rot_y(rad):
    c, s = np.cos(rad), np.sin(rad)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=np.float32)


def rot_z(rad):
    c, s = np.cos(rad), np.sin(rad)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float32)


def load_ply(path):
    with open(path, "rb") as f:
        header = ""
        while True:
            line = f.readline().decode("ascii", errors="ignore")
            header += line
            if "end_header" in line:
                break
        n_verts = int([l.split()[-1] for l in header.split("\n") if l.startswith("element vertex")][0])
        data = np.frombuffer(f.read(), dtype=[("p", "<f4", 3), ("c", "u1", 3)], count=n_verts)
        return data["p"].copy(), data["c"].copy()


def save_ply(path, pts, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = (
        "ply\nformat binary_little_endian 1.0\n"
        f"element vertex {len(pts)}\n"
        "property float x\nproperty float y\nproperty float z\n"
        "property uchar red\nproperty uchar green\nproperty uchar blue\n"
        "end_header\n"
    )
    rec = np.empty(len(pts), dtype=[("p", "<f4", 3), ("c", "u1", 3)])
    rec["p"] = pts
    rec["c"] = cols
    with open(path, "wb") as f:
        f.write(header.encode("ascii"))
        f.write(rec.tobytes())


def save_splat(path, pts, cols, base_r=0.08):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = len(pts)
    # Adaptive footprint
    z_dist = np.maximum(np.linalg.norm(pts, axis=1), 1.0)
    r = np.clip(z_dist * 0.015, 0.04, 0.45).astype(np.float32)
    scales = np.column_stack([r, r, r])

    rgba = np.column_stack([cols, np.full((n, 1), 255, dtype=np.uint8)])
    rots = np.full((n, 4), [255, 128, 128, 128], dtype=np.uint8)

    splat_dtype = np.dtype([
        ("pos", "<f4", 3),
        ("scale", "<f4", 3),
        ("rgba", "u1", 4),
        ("rot", "u1", 4)
    ])
    buf = np.empty(n, dtype=splat_dtype)
    buf["pos"] = pts
    buf["scale"] = scales
    buf["rgba"] = rgba
    buf["rot"] = rots
    with open(path, "wb") as f:
        f.write(buf.tobytes())
    return os.path.getsize(path)


def fuse_commons():
    """
    Co-registers the 5 Cortex Commons viewpoints into a unified 3D plaza.
    """
    # Spatial layout definitions for Cortex Commons (offsets in meters relative to plaza center)
    layout = {
        "bdc7d6ec-1d4e-4f99-ad7e-9917394c542a_2": {
            "name": "Center Plaza (Children & Dish)",
            "yaw_deg": 0.0,
            "offset": np.array([0.0, 0.0, 0.0], dtype=np.float32),
            "weight": 1.0
        },
        "7df17df5-790f-44ba-8cb8-8c76b480e7e3_2": {
            "name": "Terrace View (Looking Over Plaza)",
            "yaw_deg": 32.0,
            "offset": np.array([-14.0, 0.0, -18.0], dtype=np.float32),
            "weight": 1.0
        },
        "cf180ca2-ab87-4fb4-972f-469d447d68d4_0": {
            "name": "South Balcony Overlook",
            "yaw_deg": -38.0,
            "offset": np.array([16.0, 0.0, 12.0], dtype=np.float32),
            "weight": 1.0
        },
        "245fd8b5-27bb-402d-8f8d-458257e5535b_3": {
            "name": "East Undercroft (Looking Up)",
            "yaw_deg": 75.0,
            "offset": np.array([12.0, 0.0, -10.0], dtype=np.float32),
            "weight": 0.9
        },
        "e0154328-09c4-4751-8b89-de495884ce64_1": {
            "name": "West Alleyway Entrance",
            "yaw_deg": -18.0,
            "offset": np.array([-20.0, 0.0, 8.0], dtype=np.float32),
            "weight": 0.9
        }
    }

    fused_pts = []
    fused_cols = []
    shot_reports = []

    print("=" * 70)
    print("EXPERIMENT 1: CORTEX COMMONS 3D DISTRICT FUSION")
    print("=" * 70)

    for sid, cfg in layout.items():
        ply_p = os.path.join(OUT_DIR, sid, "points.ply")
        sj_p = os.path.join(OUT_DIR, sid, "shot.json")
        if not os.path.exists(ply_p) or not os.path.exists(sj_p):
            print(f"Skipping {sid} (missing files)")
            continue

        sj = json.load(open(sj_p))
        cam = sj.get("camera", {})
        h_cam = float(cam.get("height_m") or 1.6)
        pitch_deg = float(cam.get("pitch_deg") or 0.0)
        roll_deg = float(cam.get("roll_deg") or 0.0)

        pts, cols = load_ply(ply_p)
        n_pts = len(pts)

        # 1. Leveling Rotation (cancel pitch and roll)
        # In OpenGL coords, pitch is around X axis, roll is around Z axis
        # Level so ground normal becomes [0, 1, 0]
        R_pitch = rot_x(-math.radians(pitch_deg))
        R_roll = rot_z(-math.radians(roll_deg))
        R_level = R_pitch @ R_roll

        # Rotate points to level
        pts_leveled = (R_level @ pts.T).T

        # 2. Translate vertically so ground sits at Y = 0
        # In leveled camera space, camera is at Y = +h_cam
        pts_leveled[:, 1] += h_cam

        # 3. Apply Plaza Yaw rotation and Spatial Offset
        R_yaw = rot_y(math.radians(cfg["yaw_deg"]))
        pts_world = (R_yaw @ pts_leveled.T).T + cfg["offset"]

        # Filter out extreme outliers / stray points beyond 120m
        valid = (np.linalg.norm(pts_world - cfg["offset"], axis=1) < 110.0) & (pts_world[:, 1] > -3.0)
        pts_world = pts_world[valid]
        cols = cols[valid]

        fused_pts.append(pts_world)
        fused_cols.append(cols)

        # Ground plane alignment verification
        # Check median Y of ground-level points (points with Y near 0)
        ground_pts = pts_world[(pts_world[:, 1] > -0.5) & (pts_world[:, 1] < 0.5)]
        mean_ground_y = float(ground_pts[:, 1].mean()) if len(ground_pts) else 0.0

        report = {
            "id": sid,
            "name": cfg["name"],
            "raw_points": n_pts,
            "fused_points": len(pts_world),
            "camera_height_m": h_cam,
            "pitch_deg": pitch_deg,
            "roll_deg": roll_deg,
            "yaw_deg": cfg["yaw_deg"],
            "offset_m": [float(v) for v in cfg["offset"]],
            "ground_y_residual_m": round(mean_ground_y, 3)
        }
        shot_reports.append(report)
        print(f"[{sid[:12]}] {cfg['name']}")
        print(f"   Points: {len(pts_world):,} | H: {h_cam:.2f}m | Pitch: {pitch_deg:.1f}° | Offset: {cfg['offset'].tolist()} | Ground residual: {mean_ground_y:+.3f}m")

    # Combine all points into one master plaza
    all_pts = np.vstack(fused_pts)
    all_cols = np.vstack(fused_cols)

    # Compute Plaza Global Bounds
    min_b = all_pts.min(axis=0)
    max_b = all_pts.max(axis=0)
    dim_b = max_b - min_b

    print("-" * 70)
    print(f"FUSED DISTRICT STATS:")
    print(f"   Total Fused Points: {len(all_pts):,} ({all_pts.nbytes / 1024 / 1024:.1f} MB)")
    print(f"   Plaza Dimensions:   {dim_b[0]:.1f}m (W) × {dim_b[1]:.1f}m (H) × {dim_b[2]:.1f}m (D)")
    print(f"   Plaza Footprint:    X: [{min_b[0]:.1f}, {max_b[0]:.1f}], Z: [{min_b[2]:.1f}, {max_b[2]:.1f}]")
    print("-" * 70)

    # Output directory
    fused_dir = os.path.join(DIST_OUT_DIR, "commons_fused")
    os.makedirs(fused_dir, exist_ok=True)

    ply_path = os.path.join(fused_dir, "points.ply")
    splat_path = os.path.join(fused_dir, "scene.splat")
    meta_path = os.path.join(fused_dir, "fusion_report.json")

    save_ply(ply_path, all_pts, all_cols)
    splat_sz = save_splat(splat_path, all_pts, all_cols)

    report_data = {
        "district": "commons",
        "district_name": "Cortex Commons",
        "total_points": len(all_pts),
        "splat_bytes": splat_sz,
        "splat_mb": round(splat_sz / 1024 / 1024, 2),
        "bounds_m": {
            "min": [round(float(v), 2) for v in min_b],
            "max": [round(float(v), 2) for v in max_b],
            "extent": [round(float(v), 2) for v in dim_b]
        },
        "shots": shot_reports
    }
    with open(meta_path, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"Saved Fused PLY:   {ply_path} ({os.path.getsize(ply_path) / 1024 / 1024:.2f} MB)")
    print(f"Saved Fused SPLAT: {splat_path} ({splat_sz / 1024 / 1024:.2f} MB)")
    print(f"Saved Report:      {meta_path}")
    print("=" * 70)
    return report_data


def fuse_district_auto(dist_id, max_total_points=450000):
    """
    Automated spatial co-registration for any district.
    Selects anchor shot, levels all views, distributes around central plaza / street corridor.
    """
    shots_data_js = os.path.join(ROOT, "shots", "shots_data.js")
    with open(shots_data_js) as f:
        txt = f.read()
    all_shots = json.loads(txt[txt.find("["):txt.rfind("]") + 1])
    d_shots = [s for s in all_shots if s.get("district") == dist_id]

    if not d_shots:
        print(f"No shots found for district: {dist_id}")
        return None

    # Load district meta if available
    dist_meta = {}
    dists_json = os.path.join(ROOT, "_city", "districts.json")
    if os.path.exists(dists_json):
        try:
            d_raw = json.load(open(dists_json)).get("districts", [])
            for d in d_raw:
                if d.get("id") == dist_id:
                    dist_meta = d
                    break
        except Exception:
            pass

    district_name = dist_meta.get("name", dist_id.capitalize())

    print("=" * 70)
    print(f"EXPERIMENT 1: {district_name.upper()} 3D DISTRICT CO-REGISTRATION")
    print(f"Candidate Views: {len(d_shots)}")
    print("=" * 70)

    fused_pts = []
    fused_cols = []
    shot_reports = []

    # Sort shots by presence of reliable ground / camera height (1.0m - 3.0m preferred as anchor)
    def anchor_score(s):
        cam = s.get("camera", {})
        h = cam.get("height_m")
        p = cam.get("pitch_deg")
        if h is None or p is None: return -100
        return -abs(h - 1.6) - abs(p) * 0.1

    d_shots.sort(key=anchor_score, reverse=True)

    # Compute radial / corridor distribution
    n_shots = len(d_shots)
    per_shot_budget = max(20000, max_total_points // max(1, n_shots))

    for idx, s in enumerate(d_shots):
        sid = s["id"]
        ply_p = os.path.join(OUT_DIR, sid, "points.ply")
        if not os.path.exists(ply_p):
            continue

        cam = s.get("camera", {})
        h_cam = float(cam.get("height_m") or 1.6)
        pitch_deg = float(cam.get("pitch_deg") or 0.0)
        roll_deg = float(cam.get("roll_deg") or 0.0)

        # Sanitize roll and pitch (DepthPro inversion guard)
        if abs(roll_deg) > 35.0:
            roll_deg = 0.0
        if abs(pitch_deg) > 40.0:
            pitch_deg = np.clip(pitch_deg, -35.0, 35.0)
        h_cam = np.clip(h_cam, 0.4, 6.0)

        pts, cols = load_ply(ply_p)
        if len(pts) == 0:
            continue

        # Subsample if too dense
        if len(pts) > per_shot_budget:
            step = max(1, len(pts) // per_shot_budget)
            pts = pts[::step]
            cols = cols[::step]

        # 1. Leveling Rotation
        R_pitch = rot_x(-math.radians(pitch_deg))
        R_roll = rot_z(-math.radians(roll_deg))
        R_level = R_pitch @ R_roll
        pts_leveled = (R_level @ pts.T).T

        # 2. Elevation Ground Reference
        pts_leveled[:, 1] += h_cam

        # 3. Spatial Arrangement:
        # Anchor (idx=0) at center (0, 0, 0).
        # Subsequent views distributed along street corridor / ring
        if idx == 0:
            yaw = 0.0
            offset = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        else:
            angle = (2.0 * math.pi * (idx - 1)) / max(1, n_shots - 1)
            dist_radius = 16.0 + 4.0 * (idx % 3)
            offset = np.array([dist_radius * math.cos(angle), 0.0, dist_radius * math.sin(angle)], dtype=np.float32)
            yaw = math.degrees(angle) + 180.0 # Point back inwards towards district center

        R_yaw = rot_y(math.radians(yaw))
        pts_world = (R_yaw @ pts_leveled.T).T + offset

        # Filter stray noise
        valid = (np.linalg.norm(pts_world - offset, axis=1) < 110.0) & (pts_world[:, 1] > -4.0)
        pts_world = pts_world[valid]
        cols = cols[valid]

        fused_pts.append(pts_world)
        fused_cols.append(cols)

        ground_pts = pts_world[(pts_world[:, 1] > -0.5) & (pts_world[:, 1] < 0.5)]
        mean_ground_y = float(ground_pts[:, 1].mean()) if len(ground_pts) else 0.0

        shot_name = (s.get("prompt") or sid)[:36]
        report = {
            "id": sid,
            "name": shot_name,
            "raw_points": len(pts),
            "fused_points": len(pts_world),
            "camera_height_m": round(h_cam, 2),
            "pitch_deg": round(pitch_deg, 1),
            "roll_deg": round(roll_deg, 1),
            "yaw_deg": round(yaw, 1),
            "offset_m": [round(float(v), 2) for v in offset],
            "ground_y_residual_m": round(mean_ground_y, 3)
        }
        shot_reports.append(report)
        print(f"[{sid[:10]}] {shot_name}")
        print(f"   Pts: {len(pts_world):,} | H: {h_cam:.2f}m | Pitch: {pitch_deg:.1f}° | Offset: {offset.round(1).tolist()} | Residual: {mean_ground_y:+.3f}m")

    if not fused_pts:
        print("No valid points fused.")
        return None

    all_pts = np.vstack(fused_pts)
    all_cols = np.vstack(fused_cols)

    min_b = all_pts.min(axis=0)
    max_b = all_pts.max(axis=0)
    dim_b = max_b - min_b

    fused_dir = os.path.join(DIST_OUT_DIR, f"{dist_id}_fused")
    os.makedirs(fused_dir, exist_ok=True)

    ply_path = os.path.join(fused_dir, "points.ply")
    splat_path = os.path.join(fused_dir, "scene.splat")
    meta_path = os.path.join(fused_dir, "fusion_report.json")

    save_ply(ply_path, all_pts, all_cols)
    splat_sz = save_splat(splat_path, all_pts, all_cols)

    report_data = {
        "district": dist_id,
        "district_name": district_name,
        "total_points": len(all_pts),
        "splat_bytes": splat_sz,
        "splat_mb": round(splat_sz / 1024 / 1024, 2),
        "bounds_m": {
            "min": [round(float(v), 2) for v in min_b],
            "max": [round(float(v), 2) for v in max_b],
            "extent": [round(float(v), 2) for v in dim_b]
        },
        "shots": shot_reports
    }
    with open(meta_path, "w") as f:
        json.dump(report_data, f, indent=2)

    print("-" * 70)
    print(f"FUSED DISTRICT: {district_name.upper()}")
    print(f"   Total Fused Points: {len(all_pts):,} ({all_pts.nbytes / 1024 / 1024:.1f} MB)")
    print(f"   Bounds:             {dim_b[0]:.1f}m × {dim_b[1]:.1f}m × {dim_b[2]:.1f}m")
    print(f"   Saved PLY:          {ply_path} ({os.path.getsize(ply_path) / 1024 / 1024:.2f} MB)")
    print(f"   Saved SPLAT:        {splat_path} ({splat_sz / 1024 / 1024:.2f} MB)")
    print("=" * 70)
    return report_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Shot District Spatial Co-registration")
    parser.add_argument("--district", "-d", type=str, default="commons", help="District ID (e.g. commons, ankhu, naraka, haze)")
    parser.add_argument("--all", "-a", action="store_true", help="Fuse all top districts")
    args = parser.parse_args()

    if args.all:
        fuse_commons()
        for d in ["ankhu", "naraka", "haze"]:
            fuse_district_auto(d)
    elif args.district == "commons":
        fuse_commons()
    else:
        fuse_district_auto(args.district)
