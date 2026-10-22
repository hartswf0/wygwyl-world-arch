#!/usr/bin/env python3
"""
WYGWYL v2.0-poem-kits Release Extractor, CV Cardboard Cutter & Brass Pivot Detector.
Processes all 16 zip archives from the v2.0-poem-kits release:
  - Poem_01_Out_of_Life_All_Kits.zip .. Poem_14_Hot_Minute_All_Kits.zip (661 sheet entries / 365 unique sheets)
  - Poet_Black_Red_Tracksuit_Individual_Parts_v1.zip (31 pre-cut RGBA components + pose/source sheets)
  - Poet-GEMINI.zip (44 reference renders)

Outputs:
  - shots/arena/parts/kit3/release_v2/sheets/<sheet_id>.png
  - shots/arena/parts/kit3/release_v2/cuts/<sheet_id>/<part_id>.png
  - shots/arena/parts/kit3/release_v2/tracksuit/<comp_id>.png
  - shots/arena/parts/kit3/release_v2/release_catalog.json
"""

import os
import re
import json
import zipfile
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
import cv2
import numpy as np

ZIP_DIR = "/Users/gaia/Downloads/WYGWYL-WORLD-ARCH/POEM-KITS"
OUT_ROOT = "/Users/gaia/WORLDBUILDING-TERMS/wygwyl-world-arch/shots/arena/parts/kit3/release_v2"
SHEETS_DIR = os.path.join(OUT_ROOT, "sheets")
CUTS_DIR = os.path.join(OUT_ROOT, "cuts")
TRACKSUIT_DIR = os.path.join(OUT_ROOT, "tracksuit")
GEMINI_DIR = os.path.join(OUT_ROOT, "poet_gemini")


def detect_brass_pivots(rgba):
    """Detect brass grommet pivot eyelets (both open white-hole and dark-backed rings)."""
    b = rgba[:, :, 0].astype(int)
    g = rgba[:, :, 1].astype(int)
    r = rgba[:, :, 2].astype(int)
    a = rgba[:, :, 3].astype(int)
    brass = (a > 128) & (r > 165) & (g > 125) & ((r - b) > 52) & ((g - b) > 22)
    brass_u8 = cv2.morphologyEx(brass.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    num, labels, stats, cent = cv2.connectedComponentsWithStats(brass_u8, connectivity=8)
    pivots = []
    for i in range(1, num):
        x, y, w, h, area = stats[i]
        if 8 <= w <= 56 and 8 <= h <= 56 and 0.60 <= (w / max(1.0, float(h))) <= 1.55 and 40 <= area <= 1800:
            cx, cy = round(float(cent[i][0]), 1), round(float(cent[i][1]), 1)
            rad = round(float(w + h) / 4.0, 1)
            pivots.append({"x": cx, "y": cy, "r": rad})
    # Sort top-to-bottom, left-to-right
    pivots.sort(key=lambda p: (round(p["y"] / 24.0), p["x"]))
    return pivots


def parse_labels_from_prompt(prompt_text):
    """Extract likely component names from generation_prompt / final_revision_prompt."""
    if not prompt_text:
        return []
    labels = []
    # Match patterns like '01 torso - front', 'DECK.CURVE', 'A: ...', numbered items, etc.
    for m in re.finditer(r"\b(\d{2}\s+[A-Za-z0-9_.\- /]+?)(?=[,;.\n]|$)", prompt_text):
        val = m.group(1).strip()
        if 3 <= len(val) <= 42:
            labels.append(val)
    if not labels:
        for m in re.finditer(r"\b([A-Z][A-Z0-9_]+(?:\.[A-Z0-9_]+)+)\b", prompt_text):
            val = m.group(1).strip()
            if val not in labels:
                labels.append(val)
    return labels


def cut_single_sheet(task):
    """Worker function: cut a single sheet PNG into transparent RGBA component PNGs."""
    sheet_id = task["id"]
    sheet_path = task["sheet_path"]
    sheet_cuts_dir = os.path.join(CUTS_DIR, sheet_id)
    os.makedirs(sheet_cuts_dir, exist_ok=True)

    bgr = cv2.imread(sheet_path, cv2.IMREAD_COLOR)
    if bgr is None:
        return {"id": sheet_id, "error": "failed to read image", "parts": []}

    H, W = bgr.shape[:2]
    b = bgr[:, :, 0].astype(int)
    g = bgr[:, :, 1].astype(int)
    r = bgr[:, :, 2].astype(int)
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    lum = (r * 299 + g * 587 + b * 114) // 1000

    white = (lum >= 242) & (sat <= 14)
    non_white = ~white
    # Clear 4px outer border to prevent edge-frame merging
    non_white[:4, :] = False
    non_white[-4:, :] = False
    non_white[:, :4] = False
    non_white[:, -4:] = False

    # Detect thin 1-5px monochrome black layout / panel divider lines
    thin_h = np.zeros_like(non_white)
    thin_h[5:-5, :] = non_white[5:-5, :] & white[:-10, :] & white[10:, :] & (sat[5:-5, :] < 25)
    thin_v = np.zeros_like(non_white)
    thin_v[:, 5:-5] = non_white[:, 5:-5] & white[:, :-10] & white[:, 10:] & (sat[:, 5:-5] < 25)

    h_lines = cv2.morphologyEx(thin_h.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((1, int(W * 0.10)), np.uint8))
    v_lines = cv2.morphologyEx(thin_v.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((int(H * 0.10), 1), np.uint8))
    grid = cv2.dilate(cv2.bitwise_or(h_lines, v_lines), np.ones((5, 5), np.uint8)) > 0

    # Check if there is a horizontal REFERENCE ONLY divider in the bottom 36% of the sheet
    ref_y = None
    is_main_poses = ("main-poses" in sheet_id) or ("main_pose" in task.get("kind", ""))
    if not is_main_poses:
        for y_scan in range(int(H * 0.64), int(H * 0.86)):
            if np.sum(h_lines[y_scan, :] > 0) > W * 0.42:
                ref_y = y_scan
                break

    fg = (non_white & (~grid)).astype(np.uint8) * 255
    fg_closed = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    num, labels, stats, centroids = cv2.connectedComponentsWithStats(fg_closed, connectivity=8)

    raw_parts = []
    for i in range(1, num):
        x, y, w, h, area = stats[i]
        if area < 850:
            continue
        cm = (labels == i) & non_white
        ta = int(np.sum(cm))
        if ta < 650:
            continue
        wr = float(np.sum(cm & ((sat > 16) | ((r - b) > 12)))) / ta
        # Filter out monochrome black text labels & headers
        if wr < 0.06 and (h < 72 or ta / float(w * h) < 0.35):
            continue

        pad = 6
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(W, x + w + pad), min(H, y + h + pad)
        roi_bgr = bgr[y0:y1, x0:x1]
        roi_cm = cm[y0:y1, x0:x1]
        roi_r = r[y0:y1, x0:x1]
        roi_b = b[y0:y1, x0:x1]
        rh, rw = roi_cm.shape

        # Flood-fill exterior white background from ROI perimeter
        inv = (~roi_cm).astype(np.uint8) * 255
        ff = inv.copy()
        mask_ff = np.zeros((rh + 2, rw + 2), np.uint8)
        for bx in range(rw):
            if ff[0, bx] == 255:
                cv2.floodFill(ff, mask_ff, (bx, 0), 128)
            if ff[rh - 1, bx] == 255:
                cv2.floodFill(ff, mask_ff, (bx, rh - 1), 128)
        for by in range(rh):
            if ff[by, 0] == 255:
                cv2.floodFill(ff, mask_ff, (0, by), 128)
            if ff[by, rw - 1] == 255:
                cv2.floodFill(ff, mask_ff, (rw - 1, by), 128)

        ext_white = (ff == 128)
        int_holes = (ff == 255)

        nh, h_labels, h_stats, _ = cv2.connectedComponentsWithStats(int_holes.astype(np.uint8) * 255, connectivity=8)
        alpha = np.where(ext_white, 0, 255).astype(np.uint8)
        for hi in range(1, nh):
            hx, hy, hw, hh, harea = h_stats[hi]
            hmask = (h_labels == hi)
            dil = cv2.dilate(hmask.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
            ring = dil & (~hmask) & roi_cm
            ring_warm = 0.0
            if np.sum(ring) > 0:
                ring_warm = float(np.sum((roi_r[ring] - roi_b[ring]) > 28)) / float(np.sum(ring))
            aspect = float(min(hw, hh)) / max(1.0, float(max(hw, hh)))
            if (12 <= harea <= 950 and aspect > 0.45 and ring_warm > 0.40) or harea >= 480:
                alpha[hmask] = 0
            else:
                alpha[hmask] = 255

        # Soften 1px outer alpha edge to remove any white halo
        rgba = np.dstack([roi_bgr, alpha])
        pivots = detect_brass_pivots(rgba)
        role = "reference_composite" if (ref_y is not None and centroids[i][1] > ref_y) else "working_part"
        raw_parts.append({
            "sort_key": (0 if role == "working_part" else 1, int(y // 125), int(x)),
            "role": role,
            "bbox_sheet": [int(x), int(y), int(w), int(h)],
            "width": int(rw),
            "height": int(rh),
            "area_px": ta,
            "warm_ratio": round(wr, 3),
            "pivots": pivots,
            "rgba": rgba,
        })

    # If a sheet is a full-bleed painted sky/backdrop with 0 separated parts, keep the full sheet as 1 part
    if not raw_parts:
        rgba = np.dstack([bgr, np.full((H, W), 255, dtype=np.uint8)])
        raw_parts.append({
            "sort_key": (0, 0, 0),
            "role": "working_part",
            "bbox_sheet": [0, 0, int(W), int(H)],
            "width": int(W),
            "height": int(H),
            "area_px": int(W * H),
            "warm_ratio": 1.0,
            "pivots": [],
            "rgba": rgba,
        })

    raw_parts.sort(key=lambda item: item["sort_key"])
    hint_labels = parse_labels_from_prompt(task.get("prompt", ""))

    out_parts = []
    for idx, p in enumerate(raw_parts):
        part_num = idx + 1
        part_id = f"{sheet_id}__p{part_num:02d}"
        rel_png = f"arena/parts/kit3/release_v2/cuts/{sheet_id}/{part_id}.png"
        abs_png = os.path.join(sheet_cuts_dir, f"{part_id}.png")
        cv2.imwrite(abs_png, p["rgba"])
        label = hint_labels[idx] if idx < len(hint_labels) else f"{sheet_id} · Part {part_num:02d}"
        out_parts.append({
            "id": part_id,
            "part_index": part_num,
            "label": label,
            "role": p["role"],
            "file": rel_png,
            "bbox_sheet": p["bbox_sheet"],
            "width": p["width"],
            "height": p["height"],
            "area_px": p["area_px"],
            "pivots": p["pivots"],
        })

    return {
        "id": sheet_id,
        "width": int(W),
        "height": int(H),
        "part_count": len(out_parts),
        "working_part_count": sum(1 for p in out_parts if p["role"] == "working_part"),
        "reference_part_count": sum(1 for p in out_parts if p["role"] == "reference_composite"),
        "parts": out_parts,
    }


def main():
    os.makedirs(SHEETS_DIR, exist_ok=True)
    os.makedirs(CUTS_DIR, exist_ok=True)
    os.makedirs(TRACKSUIT_DIR, exist_ok=True)
    os.makedirs(GEMINI_DIR, exist_ok=True)

    # 1. Extract & catalog all 14 Poem zips
    poem_zips = sorted([f for f in os.listdir(ZIP_DIR) if f.startswith("Poem_") and f.endswith(".zip")])
    unique_sheets = {}
    poem_summaries = []

    for zname in poem_zips:
        zpath = os.path.join(ZIP_DIR, zname)
        with zipfile.ZipFile(zpath, "r") as zf:
            m_name = [n for n in zf.namelist() if n.endswith("manifest.json")][0]
            p_name = [n for n in zf.namelist() if n.endswith("prompts.json")][0]
            m = json.loads(zf.read(m_name))
            prompts = {p["id"]: p for p in json.loads(zf.read(p_name))}
            poem_num = int(m["poem"])
            poem_summaries.append({
                "poem": poem_num,
                "poem_str": m["poem"],
                "title": m["title"],
                "zip": zname,
                "sheet_count": len(m["sheets"]),
                "sheet_ids": [s["id"] for s in m["sheets"]],
            })
            root_prefix = zname.replace(".zip", "") + "/"
            for s in m["sheets"]:
                sha = s["sha256"]
                sid = s["id"]
                subfolder = s["file"].split("/")[0]
                k = s.get("category") or s.get("kind") or "other"
                p_obj = prompts.get(sid, {})
                prompt_txt = p_obj.get("final_revision_prompt") or p_obj.get("generation_prompt") or ""
                if sha not in unique_sheets:
                    sheet_out_path = os.path.join(SHEETS_DIR, f"{sid}.png")
                    if not os.path.exists(sheet_out_path):
                        zf_member = root_prefix + s["file"]
                        open(sheet_out_path, "wb").write(zf.read(zf_member))
                    unique_sheets[sha] = {
                        "id": sid,
                        "aliases": [sid],
                        "sha256": sha,
                        "subfolder": subfolder,
                        "kind": k,
                        "poems": [poem_num],
                        "original_file": s["file"],
                        "sheet_rel": f"arena/parts/kit3/release_v2/sheets/{sid}.png",
                        "sheet_path": sheet_out_path,
                        "separated_card_count": s.get("separated_card_count"),
                        "qa_notes": s.get("qa_notes", []),
                        "covered_source_ids": s.get("covered_source_ids", []),
                        "prompt": prompt_txt,
                    }
                else:
                    if poem_num not in unique_sheets[sha]["poems"]:
                        unique_sheets[sha]["poems"].append(poem_num)
                    if sid not in unique_sheets[sha]["aliases"]:
                        unique_sheets[sha]["aliases"].append(sid)

    print(f"Extracted {len(unique_sheets)} unique sheets from 14 poem archives.")

    # 2. Extract Poet_Black_Red_Tracksuit_Individual_Parts_v1.zip (31 pre-cut RGBA components)
    tracksuit_components = []
    ts_zip = os.path.join(ZIP_DIR, "Poet_Black_Red_Tracksuit_Individual_Parts_v1.zip")
    if os.path.exists(ts_zip):
        with zipfile.ZipFile(ts_zip, "r") as zf:
            ts_man = json.loads(zf.read("Poet_Black_Red_Tracksuit_Individual_Parts_v1/manifest.json"))
            ts_prompts = {
                p["id"]: p
                for p in json.loads(zf.read("Poet_Black_Red_Tracksuit_Individual_Parts_v1/prompts.json"))
            }
            for comp in ts_man["components"]:
                cid = comp["id"]
                c_out = os.path.join(TRACKSUIT_DIR, f"{cid}.png")
                if not os.path.exists(c_out):
                    zf_member = "Poet_Black_Red_Tracksuit_Individual_Parts_v1/" + comp["file"]
                    open(c_out, "wb").write(zf.read(zf_member))
                rgba = cv2.imread(c_out, cv2.IMREAD_UNCHANGED)
                pivots = detect_brass_pivots(rgba) if rgba is not None else []
                # Crop tight visible alpha bounding box so tracksuit cutouts don't have huge empty margins
                bx, by, bw, bh = comp.get("visible_bbox_alpha128_px", [0, 0, comp["dimensions_px"][0], comp["dimensions_px"][1]])
                tracksuit_components.append({
                    "id": f"poet.tracksuit.{cid}",
                    "comp_id": cid,
                    "label": comp["label"],
                    "group": comp["group"],
                    "file": f"arena/parts/kit3/release_v2/tracksuit/{cid}.png",
                    "width": comp["dimensions_px"][0],
                    "height": comp["dimensions_px"][1],
                    "visible_bbox": [bx, by, bw, bh],
                    "expected_pivots": comp.get("expected_pivot_marker_count", 0),
                    "pivots": pivots,
                    "poems": list(range(4, 15)),
                    "prompt": ts_prompts.get(cid, {}).get("prompt", ""),
                })
    print(f"Processed {len(tracksuit_components)} pre-cut Poet tracksuit components.")

    # 3. Cut all 365 unique sheets in parallel
    tasks = list(unique_sheets.values())
    results_by_id = {}
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(cut_single_sheet, t): t["id"] for t in tasks}
        done_cnt = 0
        for fut in as_completed(futs):
            res = fut.result()
            results_by_id[res["id"]] = res
            done_cnt += 1
            if done_cnt % 50 == 0 or done_cnt == len(tasks):
                print(f"  Cut progress: {done_cnt}/{len(tasks)} sheets...")

    # Merge results into catalog
    sheets_catalog = []
    total_parts = 0
    total_working = 0
    total_pivots = 0
    for sha, sdata in sorted(unique_sheets.items(), key=lambda kv: kv[1]["id"]):
        res = results_by_id.get(sdata["id"], {})
        sdata_out = {k: v for k, v in sdata.items() if k != "sheet_path"}
        sdata_out["width"] = res.get("width", 1536)
        sdata_out["height"] = res.get("height", 1024)
        sdata_out["part_count"] = res.get("part_count", 0)
        sdata_out["working_part_count"] = res.get("working_part_count", 0)
        sdata_out["reference_part_count"] = res.get("reference_part_count", 0)
        sdata_out["parts"] = res.get("parts", [])
        total_parts += sdata_out["part_count"]
        total_working += sdata_out["working_part_count"]
        for p in sdata_out["parts"]:
            total_pivots += len(p.get("pivots", []))
        sheets_catalog.append(sdata_out)

    catalog = {
        "release": "v2.0-poem-kits",
        "poem_count": len(poem_summaries),
        "total_sheet_entries": 661,
        "unique_sheet_count": len(sheets_catalog),
        "tracksuit_component_count": len(tracksuit_components),
        "total_cut_parts": total_parts + len(tracksuit_components),
        "total_working_parts": total_working + len(tracksuit_components),
        "total_detected_brass_pivots": total_pivots + sum(len(c["pivots"]) for c in tracksuit_components),
        "poems": poem_summaries,
        "tracksuit_components": tracksuit_components,
        "sheets": sheets_catalog,
    }

    cat_path = os.path.join(OUT_ROOT, "release_catalog.json")
    with open(cat_path, "w") as f:
        json.dump(catalog, f, indent=2)

    print("\n=== COMPLETE v2.0-poem-kits CUTTER SUMMARY ===")
    print(f"Unique sheets cut:           {len(sheets_catalog)}")
    print(f"Pre-cut tracksuit parts:     {len(tracksuit_components)}")
    print(f"Total cut RGBA pieces:       {catalog['total_cut_parts']}")
    print(f"Total working parts:         {catalog['total_working_parts']}")
    print(f"Total brass pivots detected: {catalog['total_detected_brass_pivots']}")
    print(f"Saved catalog to:            {cat_path}")


if __name__ == "__main__":
    main()
