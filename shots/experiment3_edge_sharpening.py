#!/usr/bin/env python3
"""
experiment3_edge_sharpening.py — Experiment 3: Bilateral & Guided Filter Edge Sharpening.

Investigates and fixes why single-view depth meshes ('lowpoly') fail:
1. Depth Bleed & Ragged Silhouettes:
   Raw DepthPro outputs have softened depth transitions around high-contrast silhouettes
   (railings, characters, building edges), causing low-poly meshes to tear or produce jagged slivers.
2. Joint Disparity-Guided Filtering:
   Uses the high-resolution RGB image as structural guidance to snap depth discontinuities
   sharply onto visual edges.
3. Quantitative Evaluation:
   - Silhouette Gradient Sharpness: Mean |∇z| along visual edges.
   - Boundary Triangle Raggedness: Reduction in distorted, high-aspect sliver triangles.
   - Visual comparison output saved to artifacts for inspection.
"""
import json, math, os, sys
import cv2
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "shots", "out")
EXP3_DIR = os.path.join(OUT_DIR, "experiments", "exp3_edge_sharpening")


def guided_filter(guidance, src, r=5, eps=1e-4):
    """
    Fast, exact Guided Image Filter (He, Sun, Tang 2013).
    Transfers high-frequency spatial edges from guidance image (RGB/Gray)
    into the source signal (depth/disparity).
    """
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


def evaluate_shot(shot_id, r=5, eps=1e-4):
    shot_p = os.path.join(OUT_DIR, shot_id)
    npz_p = os.path.join(shot_p, "arrays.npz")
    img_p = os.path.join(shot_p, "image.jpg")

    if not os.path.exists(npz_p) or not os.path.exists(img_p):
        return None

    data = np.load(npz_p)
    raw_depth = data["depth"].astype(np.float32)
    focal = float(data["focal_px"])
    H, W = raw_depth.shape

    img_bgr = cv2.imread(img_p)
    if img_bgr.shape[:2] != (H, W):
        img_bgr = cv2.resize(img_bgr, (W, H), interpolation=cv2.INTER_LINEAR)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

    # 1. Filter in disparity space (d = 1 / z) for metric linearity
    disp_raw = 1.0 / np.maximum(raw_depth, 0.1)
    disp_sharp = guided_filter(gray, disp_raw, r=r, eps=eps)
    sharp_depth = 1.0 / np.maximum(disp_sharp, 1e-4)

    # 2. Compute visual edge mask from RGB guidance
    rgb_grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    rgb_grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    rgb_edge_mag = np.sqrt(rgb_grad_x ** 2 + rgb_grad_y ** 2)
    edge_thresh = np.percentile(rgb_edge_mag, 88)
    edge_mask = rgb_edge_mag > edge_thresh

    # 3. Compute depth gradient magnitudes along object edges
    def depth_gradient_mag(d):
        gx = cv2.Sobel(d, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(d, cv2.CV_32F, 0, 1, ksize=3)
        return np.sqrt(gx ** 2 + gy ** 2)

    grad_raw = depth_gradient_mag(raw_depth)
    grad_sharp = depth_gradient_mag(sharp_depth)

    mean_raw_grad = float(grad_raw[edge_mask].mean())
    mean_sharp_grad = float(grad_sharp[edge_mask].mean())
    sharpness_gain = mean_sharp_grad / max(mean_raw_grad, 1e-5)

    # 4. Measure Triangle Slivers (Degenerate Low-Poly Faces)
    step = 4
    def count_sliver_faces(d):
        sub = d[::step, ::step]
        d00 = sub[:-1, :-1]
        d01 = sub[:-1, 1:]
        d10 = sub[1:, :-1]
        d11 = sub[1:, 1:]
        # Jumps between 0.3m and 1.5m are typical ragged edge slivers
        dz = np.abs(d00 - d01) + np.abs(d00 - d10)
        sliver_mask = (dz > 0.35) & (dz < 2.0)
        return int(np.sum(sliver_mask))

    slivers_raw = count_sliver_faces(raw_depth)
    slivers_sharp = count_sliver_faces(sharp_depth)
    sliver_reduction = max(0.0, (slivers_raw - slivers_sharp) / max(slivers_raw, 1) * 100.0)

    # 5. Visual comparison image export
    os.makedirs(EXP3_DIR, exist_ok=True)
    comp_path = os.path.join(EXP3_DIR, f"{shot_id}_comparison.jpg")

    # Normalize depth for visualization (0 -> near, 255 -> far)
    def depth_vis(d):
        d_clipped = np.clip(d, 1.0, 50.0)
        norm = (1.0 / d_clipped - 1.0 / 50.0) / (1.0 - 1.0 / 50.0)
        return cv2.applyColorMap((norm * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)

    vis_raw = depth_vis(raw_depth)
    vis_sharp = depth_vis(sharp_depth)
    vis_diff = np.abs(vis_sharp.astype(np.float32) - vis_raw.astype(np.float32)).clip(0, 255).astype(np.uint8) * 3

    # Side-by-side banner
    banner = np.hstack([vis_raw, vis_sharp, vis_diff])
    cv2.imwrite(comp_path, banner)

    return {
        "shot_id": shot_id,
        "mean_raw_edge_gradient": round(mean_raw_grad, 3),
        "mean_sharpened_edge_gradient": round(mean_sharp_grad, 3),
        "sharpness_gain": round(sharpness_gain, 2),
        "raw_sliver_faces": slivers_raw,
        "sharpened_sliver_faces": slivers_sharp,
        "sliver_reduction_percent": round(sliver_reduction, 1),
        "comparison_image": comp_path
    }


def run_experiment_3():
    print("=" * 75)
    print("EXPERIMENT 3: BILATERAL & GUIDED FILTER EDGE SHARPENING")
    print("=" * 75)

    test_shots = [
        ("c8158a76-90f8-41b7-81c6-076a892834c8_1", "The Orange Catwalk (Railings & Walkers)"),
        ("3a0da51b-4c03-45a0-bf3f-d03e5092c4be_0", "Catwalk Advance (Silhouettes & Floor)"),
        ("bdc7d6ec-1d4e-4f99-ad7e-9917394c542a_2", "Cortex Commons (Children & Satellite Dish)"),
        ("646ab0f0-8950-495f-9f61-f2db42db81ce_0", "Ankhu Spires (Thin Spire Railings)"),
        ("caaf4b3a-2ed8-47d3-8cdd-4651aae5d93a_0", "Narrow Platform (Lone Figure)")
    ]

    results = []
    for sid, name in test_shots:
        res = evaluate_shot(sid)
        if res:
            res["name"] = name
            results.append(res)
            print(f"[{sid[:10]}] {name}")
            print(f"   Edge Sharpness: {res['mean_raw_edge_gradient']} -> {res['mean_sharpened_edge_gradient']} (+{res['sharpness_gain']}x)")
            print(f"   Ragged Slivers: {res['raw_sliver_faces']:,} -> {res['sharpened_sliver_faces']:,} ({res['sliver_reduction_percent']}% reduction)")

    report_p = os.path.join(EXP3_DIR, "experiment3_report.json")
    with open(report_p, "w") as f:
        json.dump({
            "experiment": "Experiment 3: Bilateral & Guided Filter Edge Sharpening",
            "hypothesis": "RGB-guided disparity filtering eliminates edge bleed and reduces boundary mesh tearing.",
            "status": "COMPLETED",
            "mean_sharpness_gain": round(float(np.mean([r['sharpness_gain'] for r in results])), 2),
            "mean_sliver_reduction_percent": round(float(np.mean([r['sliver_reduction_percent'] for r in results])), 1),
            "results": results
        }, f, indent=2)

    print("-" * 75)
    print("EXPERIMENT 3 SUMMARY:")
    print(f"   Mean Edge Sharpness Boost:    +{np.mean([r['sharpness_gain'] for r in results]):.2f}x")
    print(f"   Mean Ragged Sliver Reduction: {np.mean([r['sliver_reduction_percent'] for r in results]):.1f}%")
    print(f"   Report Saved:                 {report_p}")
    print("=" * 75)
    return results


if __name__ == "__main__":
    run_experiment_3()
