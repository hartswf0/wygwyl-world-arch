#!/usr/bin/env python3
import glob
import os
import cv2
import numpy as np
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)


def clean_v2_composited(abs_path):
    try:
        rel_file = os.path.relpath(abs_path, SHOTS)
        bname = os.path.basename(abs_path)
        is_head = ("head." in bname) or ("/head" in rel_file)
        im = cv2.imread(abs_path, cv2.IMREAD_UNCHANGED)
        if im is None or im.ndim != 3 or im.shape[2] != 4:
            return False
        rgba = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
        h, w = rgba.shape[:2]
        rgb = rgba[:, :, :3].copy()
        alpha = rgba[:, :, 3].copy()

        # 1. Remove small disconnected floating islands (registration dots outside torso/limbs)
        fg = (alpha > 20).astype(np.uint8)
        if fg.sum() < 20:
            return False
        num_l, labels, stats, _ = cv2.connectedComponentsWithStats(fg)
        if num_l > 2:
            main_i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            main_area = stats[main_i, cv2.CC_STAT_AREA]
            for i in range(1, num_l):
                if i != main_i and stats[i, cv2.CC_STAT_AREA] < main_area * 0.14:
                    alpha[labels == i] = 0
                    fg[labels == i] = 0

        dist_out = cv2.distanceTransform(fg, cv2.DIST_L2, 5)
        r = rgb[:, :, 0].astype(np.float32)
        g = rgb[:, :, 1].astype(np.float32)
        b = rgb[:, :, 2].astype(np.float32)
        lum = 0.299 * r + 0.587 * g + 0.114 * b

        # 2. High-res cardboard bevel & brass grommet removal on non-head body cards:
        # On high-res sheets (e.g. poet.red_black_sunglasses profile, child_clothes, street_clothes),
        # the cardboard bevel can be up to 16px wide (and around interior armholes), and collar grommets up to 68px wide.
        if not is_head:
            max_bevel_d = max(11.0, min(h, w) * 0.095)
            deep_core = (dist_out > max_bevel_d * 1.15)
            is_tan_kraft = (
                (r > 85) & (g > 60) & (r >= g * 1.02) & (g >= b * 1.08) &
                (r - b > 20) & (g / np.maximum(r, 1.0) > 0.54) & (g / np.maximum(r, 1.0) < 0.94)
            )
            # Check if the deep core of the garment is NOT itself a tan/brown garment
            tan_frac_deep = float(is_tan_kraft[deep_core].mean()) if deep_core.sum() > 40 else 1.0
            if tan_frac_deep < 0.32:
                # Any tan/kraft/brass pixel on this non-tan garment (perimeter bevel, armhole ring, or large grommet)
                # is cardboard/brass artifact and should be replaced by nearest valid garment pixel!
                bad_tan = is_tan_kraft & (fg > 0)
                # Also dilate bad_tan slightly to catch anti-aliased edge of brass grommets & cardboard bevels
                bad_tan_u8 = cv2.dilate(bad_tan.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
                valid_garment = (fg > 0) & (~bad_tan_u8) & (dist_out > 3.5)
                if valid_garment.sum() > 30:
                    inv_v = (~valid_garment).astype(np.uint8)
                    _, labels_near = cv2.distanceTransformWithLabels(inv_v, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
                    vy, vx = np.where(inv_v == 0)
                    idx = np.clip(labels_near - 1, 0, len(vy) - 1)
                    nearest_rgb = rgb[vy[idx], vx[idx]]
                    rgb[bad_tan_u8] = nearest_rgb[bad_tan_u8]
            else:
                # Even on tan/brown garments, strip the outer bevel (dist_out <= max_bevel_d * 0.75) using deep_core
                if deep_core.sum() > 30:
                    # Also mask any bright gold grommet in top/bottom 28%
                    ys_f, xs_f = np.where(fg > 0)
                    y0, y1 = ys_f.min(), ys_f.max()
                    bh = max(1, y1 - y0)
                    end_zone = ((np.arange(h)[:, None] <= y0 + bh * 0.28) | (np.arange(h)[:, None] >= y1 - bh * 0.25))
                    bright_brass = end_zone & (r > 165) & (g > 125) & (r - b > 45) & (g / np.maximum(r, 1.0) > 0.60)
                    bad_edge = ((dist_out <= max_bevel_d * 0.72) | bright_brass) & (fg > 0)
                    valid_g = deep_core & (~bright_brass)
                    if valid_g.sum() > 25:
                        inv_v = (~valid_g).astype(np.uint8)
                        _, labels_near = cv2.distanceTransformWithLabels(inv_v, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
                        vy, vx = np.where(inv_v == 0)
                        idx = np.clip(labels_near - 1, 0, len(vy) - 1)
                        nearest_rgb = rgb[vy[idx], vx[idx]]
                        rgb[bad_edge] = nearest_rgb[bad_edge]

        # 3. On limb cards (thigh, shin, uarm, farm), remove any vertical template bone line down the center (|x - w/2| <= 13)
        if any(k in bname for k in ("thigh", "shin", "uarm", "farm")) and w >= 36:
            ys, xs = np.where(fg > 0)
            if len(xs) > 0:
                y0, y1 = ys.min(), ys.max()
                for y in list(range(y0, min(h, y0 + 18))) + list(range(max(0, y1 - 18), y1 + 1)):
                    row_xs = np.where(fg[y] > 0)[0]
                    if len(row_xs) > 0 and (row_xs.max() - row_xs.min()) < w * 0.27:
                        alpha[y, :] = 0
                        fg[y, :] = 0

                cx = int(round(np.median(xs)))
                xL0, xL1 = max(0, cx - 24), max(0, cx - 13)
                xR0, xR1 = min(w, cx + 14), min(w, cx + 25)
                if xL1 > xL0 and xR1 > xR0:
                    flank_mask = np.zeros((h, w), dtype=bool)
                    flank_mask[:, xL0:xL1] = True
                    flank_mask[:, xR0:xR1] = True
                    flank_fg = flank_mask & (fg > 0)
                    if flank_fg.sum() > 30:
                        med_flank = np.median(rgb[flank_fg], axis=0)
                        c_x0, c_x1 = max(0, cx - 13), min(w, cx + 14)
                        center_strip = np.zeros((h, w), dtype=bool)
                        center_strip[:, c_x0:c_x1] = True
                        diff = np.linalg.norm(rgb.astype(np.float32) - med_flank[None, None, :], axis=2)
                        if (center_strip & (fg > 0) & (diff > 18.0)).sum() > 20:
                            span = float(max(1, c_x1 - c_x0))
                            for y in range(h):
                                if fg[y, cx] == 0:
                                    continue
                                col_L = np.median(rgb[y, max(0, c_x0 - 6):max(1, c_x0)], axis=0) if c_x0 > 2 else med_flank
                                col_R = np.median(rgb[y, min(w - 1, c_x1):min(w, c_x1 + 6)], axis=0) if c_x1 < w - 2 else med_flank
                                for x in range(c_x0, c_x1):
                                    if fg[y, x] > 0:
                                        u = (x - c_x0) / span
                                        rgb[y, x] = np.clip((1.0 - u) * col_L + u * col_R, 0, 255).astype(np.uint8)

        # 4. On torso cards, clean any remaining hip corner socket badges
        if "torso" in bname:
            ys, xs = np.where(fg > 0)
            if len(xs) > 0:
                x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
                bw, bh = max(1, x1 - x0), max(1, y1 - y0)
                hip_zones = np.zeros((h, w), dtype=bool)
                hip_zones[int(y0 + bh * 0.76):y1 + 1, x0:int(x0 + bw * 0.34)] = True
                hip_zones[int(y0 + bh * 0.76):y1 + 1, int(x1 - bw * 0.34):x1 + 1] = True
                chest_zone = np.zeros((h, w), dtype=bool)
                chest_zone[int(y0 + bh * 0.35):int(y0 + bh * 0.65), int(x0 + bw * 0.30):int(x0 + bw * 0.70)] = True
                chest_fg = chest_zone & (fg > 0)
                if chest_fg.sum() > 40:
                    med_chest = np.median(rgb[chest_fg], axis=0)
                    diff = np.linalg.norm(rgb.astype(np.float32) - med_chest[None, None, :], axis=2)
                    hip_badge = (hip_zones & (fg > 0) & (diff > 28.0)).astype(np.uint8) * 255
                    if hip_badge.sum() > 255 * 12:
                        dil = cv2.dilate(hip_badge, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
                        dil = cv2.bitwise_and(dil, fg * 255)
                        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                        rgb = cv2.cvtColor(cv2.inpaint(bgr, dil, 7, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB)

        out = np.dstack([rgb, alpha])
        cv2.imwrite(abs_path, cv2.cvtColor(out, cv2.COLOR_RGBA2BGRA))
        return True
    except Exception:
        return False


def main():
    files = sorted(glob.glob(os.path.join(SHOTS, "arena/parts/kit3/v2/parts/*/*.png")))
    with Pool(10) as p:
        res = p.map(clean_v2_composited, files, chunksize=64)
    print("Cleaned", sum(1 for r in res if r), "/", len(files), "v2 part files")


if __name__ == "__main__":
    main()
