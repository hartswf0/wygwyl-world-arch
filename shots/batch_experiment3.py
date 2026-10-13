#!/usr/bin/env python3
"""
batch_experiment3.py — Parallel Execution of Experiment 3 across all 81 Shots.

Experiment 3: Semantic Edge-Snapping & Bilateral Shock Filtering.
Hypothesis:
  Monocular depth networks blur depth boundaries across a 3-8 pixel band.
  By coupling the Canny/Sobel RGB edge prior with a non-linear shock filter in disparity space,
  we snap intermediate boundary pixels to their true foreground/background step,
  eliminating the root cause of low-poly mesh tearing and sliver faces.

Executes across all reconstructed shots using multiprocessing.Pool.
"""
import glob, json, math, multiprocessing, os, sys, time
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "shots", "out")
EXP_DIR = os.path.join(OUT_DIR, "experiments", "exp3_parallel")


def guided_filter(guidance, src, r=4, eps=1e-4):
    I = guidance.astype(np.float32)
    P = src.astype(np.float32)

    mean_I = cv2.boxFilter(I, cv2.CV_32F, (r, r))
    mean_P = cv2.boxFilter(P, cv2.CV_32F, (r, r))

    corr_I = cv2.boxFilter(I * I, cv2.CV_32F, (r, r))
    corr_IP = cv2.boxFilter(I * P, cv2.CV_32F, (r, r))

    var_I = corr_I - mean_I * mean_I
    cov_IP = corr_IP - mean_I * mean_P

    a = cov_IP / (var_I + eps)
    b = mean_P - a * mean_I

    mean_a = cv2.boxFilter(a, cv2.CV_32F, (r, r))
    mean_b = cv2.boxFilter(b, cv2.CV_32F, (r, r))

    return mean_a * I + mean_b


def semantic_shock_filter(depth, rgb_gray, edge_canny):
    """
    Snaps intermediate ramp pixels near RGB edges to binary step edges.
    """
    disp = 1.0 / np.maximum(depth, 0.1)
    
    # Linear guided filter pass
    disp_gf = guided_filter(rgb_gray, disp, r=4, eps=1e-4)
    
    # Morphological min/max in disparity space
    kernel = np.ones((3, 3), np.uint8)
    disp_min = cv2.erode(disp_gf, kernel)
    disp_max = cv2.dilate(disp_gf, kernel)
    
    # Boundary zone near visual edges
    edge_zone = cv2.dilate(edge_canny, np.ones((5, 5), np.uint8)) > 0
    step_jump = (disp_max - disp_min) > 0.04 # Disparity jump > ~1m
    
    # Decision: snap to closer extreme
    shock_disp = disp_gf.copy()
    midpoint = (disp_min + disp_max) * 0.5
    snap_mask = edge_zone & step_jump
    
    shock_disp[snap_mask & (disp_gf >= midpoint)] = disp_max[snap_mask & (disp_gf >= midpoint)]
    shock_disp[snap_mask & (disp_gf < midpoint)] = disp_min[snap_mask & (disp_gf < midpoint)]
    
    return 1.0 / np.maximum(shock_disp, 1e-4)


def process_single_shot(shot_dir):
    sid = os.path.basename(shot_dir)
    npz_p = os.path.join(shot_dir, "arrays.npz")
    img_p = os.path.join(shot_dir, "image.jpg")

    if not os.path.exists(npz_p) or not os.path.exists(img_p):
        return None

    try:
        data = np.load(npz_p)
        depth = data["depth"].astype(np.float32)
        H, W = depth.shape

        img_bgr = cv2.imread(img_p)
        if img_bgr is None:
            return None
        if img_bgr.shape[:2] != (H, W):
            img_bgr = cv2.resize(img_bgr, (W, H), interpolation=cv2.INTER_LINEAR)

        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        gray_u8 = (gray * 255).astype(np.uint8)
        canny = cv2.Canny(gray_u8, 50, 150)

        # Apply semantic shock filter
        depth_sharp = semantic_shock_filter(depth, gray, canny)

        # Metrics:
        # 1. Edge Gradient Magnitude along RGB edges
        edge_mask = cv2.dilate(canny, np.ones((3, 3), np.uint8)) > 0
        gx_raw = cv2.Sobel(depth, cv2.CV_32F, 1, 0, ksize=3)
        gy_raw = cv2.Sobel(depth, cv2.CV_32F, 0, 1, ksize=3)
        grad_raw = np.sqrt(gx_raw**2 + gy_raw**2)

        gx_sharp = cv2.Sobel(depth_sharp, cv2.CV_32F, 1, 0, ksize=3)
        gy_sharp = cv2.Sobel(depth_sharp, cv2.CV_32F, 0, 1, ksize=3)
        grad_sharp = np.sqrt(gx_sharp**2 + gy_sharp**2)

        raw_edge_grad = float(grad_raw[edge_mask].mean()) if np.sum(edge_mask) else 1.0
        sharp_edge_grad = float(grad_sharp[edge_mask].mean()) if np.sum(edge_mask) else 1.0
        sharp_ratio = sharp_edge_grad / max(raw_edge_grad, 1e-4)

        # 2. Degenerate mesh sliver triangles
        step = 4
        def count_slivers(d):
            sub = d[::step, ::step]
            dz = np.abs(sub[:-1, :-1] - sub[:-1, 1:]) + np.abs(sub[:-1, :-1] - sub[1:, :-1])
            return int(np.sum((dz > 0.4) & (dz < 3.0)))

        slivers_raw = count_slivers(depth)
        slivers_sharp = count_slivers(depth_sharp)
        sliver_reduction = max(0.0, (slivers_raw - slivers_sharp) / max(slivers_raw, 1) * 100.0)

        # Save edge-sharpened depth map
        save_npz = os.path.join(shot_dir, "depth_sharp.npz")
        np.savez_compressed(save_npz, depth=depth_sharp.astype(np.float16))

        return {
            "id": sid,
            "raw_edge_grad": round(raw_edge_grad, 2),
            "sharp_edge_grad": round(sharp_edge_grad, 2),
            "sharp_ratio": round(sharp_ratio, 2),
            "raw_slivers": slivers_raw,
            "sharp_slivers": slivers_sharp,
            "sliver_reduction_pct": round(sliver_reduction, 1)
        }
    except Exception as e:
        return {"id": sid, "error": str(e)}


def main():
    t0 = time.time()
    os.makedirs(EXP_DIR, exist_ok=True)

    # Gather all shot directories
    all_shots = sorted(glob.glob(os.path.join(OUT_DIR, "*_*")))
    all_shots = [s for s in all_shots if os.path.isdir(s) and os.path.exists(os.path.join(s, "arrays.npz"))]

    print("=" * 75)
    print(f"EXPERIMENT 3 (PARALLEL): RUNNING SEMANTIC SHOCK-FILTER ACROSS {len(all_shots)} SHOTS")
    print(f"Workers: {multiprocessing.cpu_count()} CPU cores")
    print("=" * 75)

    with multiprocessing.Pool() as pool:
        results = pool.map(process_single_shot, all_shots)

    valid_results = [r for r in results if r and "error" not in r]

    # Aggregate statistics
    mean_sharp_ratio = float(np.mean([r["sharp_ratio"] for r in valid_results]))
    mean_sliver_red = float(np.mean([r["sliver_reduction_pct"] for r in valid_results]))
    total_slivers_eliminated = sum(r["raw_slivers"] - r["sharp_slivers"] for r in valid_results)

    report = {
        "experiment": "Experiment 3: Parallel Semantic Shock Filtering & Edge Snapping",
        "shots_processed": len(valid_results),
        "total_time_seconds": round(time.time() - t0, 2),
        "mean_sharpness_boost": round(mean_sharp_ratio, 2),
        "mean_sliver_reduction_percent": round(mean_sliver_red, 1),
        "total_ragged_slivers_eliminated": total_slivers_eliminated,
        "shots": valid_results
    }

    report_p = os.path.join(EXP_DIR, "experiment3_benchmark.json")
    with open(report_p, "w") as f:
        json.dump(report, f, indent=2)

    print("-" * 75)
    print(f"EXPERIMENT 3 COMPLETE in {time.time() - t0:.1f}s:")
    print(f"   Shots Processed:             {len(valid_results)} / {len(all_shots)}")
    print(f"   Mean Silhouette Sharpness:   +{mean_sharp_ratio:.2f}x")
    print(f"   Mean Sliver Reduction:       {mean_sliver_red:.1f}%")
    print(f"   Total Torn Slivers Removed:  {total_slivers_eliminated:,} faces across dataset")
    print(f"   Benchmark Report:            {report_p}")
    print("=" * 75)


if __name__ == "__main__":
    main()
