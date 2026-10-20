"""Slice cutout pieces from the 18 generated sheets for the Man (Male Poet) and register cast.json.

Usage:
    python3 shots/weave/cast/man/build_cast.py

Outputs:
    shots/weave/cast/man/parts/*.png
    shots/weave/cast/man/cast.json
"""
import json, os
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, 'sheets')
PARTS = os.path.join(HERE, 'parts')
os.makedirs(PARTS, exist_ok=True)


def extract_alpha(bgr, pad=4):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    bg = (hsv[..., 1] < 35) & (hsv[..., 2] > 185)
    fg = (~bg).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:
        k = 1 + int(np.argmax(st[1:, 4]))
        fg = (lab == k).astype(np.uint8)
    cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    solid = np.zeros_like(fg)
    cv2.drawContours(solid, cnts, -1, 1, -1)
    a = cv2.GaussianBlur(solid.astype(np.float32), (3, 3), 0.6)
    alpha = (a * 255).astype(np.uint8)

    # Crop to bounding box
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0 or len(ys) == 0:
        return np.dstack([bgr, alpha]), (0, 0)
    x0, x1 = max(0, xs.min() - pad), min(bgr.shape[1], xs.max() + 1 + pad)
    y0, y1 = max(0, ys.min() - pad), min(bgr.shape[0], ys.max() + 1 + pad)

    crop_bgr = bgr[y0:y1, x0:x1]
    crop_a = alpha[y0:y1, x0:x1]
    return np.dstack([crop_bgr, crop_a]), (x0, y0)


def cut(sheet_name, box, pid, pivot_rel, sockets_rel={}):
    sp = os.path.join(SHEETS, sheet_name)
    im = cv2.imread(sp)
    if im is None:
        raise FileNotFoundError(sp)
    x0, y0, x1, y1 = box
    patch = im[y0:y1, x0:x1]
    rgba, offset = extract_alpha(patch)
    out_name = f"{pid}.png"
    out_path = os.path.join(PARTS, out_name)
    cv2.imwrite(out_path, rgba)

    H, W = rgba.shape[:2]
    # adjust pivot & sockets by local cropped offset
    piv = [round(pivot_rel[0] * W, 1), round(pivot_rel[1] * H, 1)]
    socks = {}
    for k, v in sockets_rel.items():
        socks[k] = [round(v[0] * W, 1), round(v[1] * H, 1)]

    return {
        'id': pid,
        'file': f"cast/man/parts/{out_name}",
        'size': [W, H],
        'pivot': piv,
        'sockets': socks,
        'sheet': sheet_name,
        'box': box
    }


def main():
    reg = {'about': 'The Man (Male Poet) cardboard cutout library', 'parts': {}}

    # 1. From body_profile.jpg
    p = cut('body_profile.jpg', [467, 44, 687, 368], 'torso.profile', [0.5, 0.95],
            {'neck': [0.5, 0.05], 'shoulder_near': [0.65, 0.15], 'shoulder_far': [0.35, 0.15], 'hip': [0.5, 0.95]})
    reg['parts']['torso.profile'] = p

    p = cut('body_profile.jpg', [458, 373, 694, 620], 'pelvis.profile', [0.5, 0.1],
            {'hip': [0.5, 0.1], 'hip_near': [0.55, 0.5], 'hip_far': [0.45, 0.5]})
    reg['parts']['pelvis.profile'] = p

    p = cut('body_profile.jpg', [778, 55, 852, 276], 'uarm.profile', [0.5, 0.1],
            {'shoulder': [0.5, 0.1], 'elbow': [0.5, 0.9]})
    reg['parts']['uarm.profile'] = p

    p = cut('body_profile.jpg', [925, 188, 997, 380], 'farm.profile', [0.5, 0.1],
            {'elbow': [0.5, 0.1], 'wrist': [0.5, 0.9]})
    reg['parts']['farm.profile'] = p

    p = cut('body_profile.jpg', [1108, 456, 1276, 549], 'hand.profile.open', [0.15, 0.5],
            {'wrist': [0.15, 0.5], 'tip': [0.85, 0.5]})
    reg['parts']['hand.profile.open'] = p

    # 2. From body_front.jpg
    p = cut('body_front.jpg', [466, 46, 686, 373], 'torso.front', [0.5, 0.95],
            {'neck': [0.5, 0.05], 'shoulder_near': [0.8, 0.15], 'shoulder_far': [0.2, 0.15], 'hip': [0.5, 0.95]})
    reg['parts']['torso.front'] = p

    p = cut('body_front.jpg', [458, 383, 697, 630], 'pelvis.front', [0.5, 0.1],
            {'hip': [0.5, 0.1], 'hip_near': [0.75, 0.5], 'hip_far': [0.25, 0.5]})
    reg['parts']['pelvis.front'] = p

    # 3. Heads from heads.jpg (6 angles)
    angles = [
        ('profile_R', [50, 68, 265, 360]),
        ('threequarter_R', [291, 69, 468, 359]),
        ('front', [501, 68, 678, 361]),
        ('threequarter_L', [708, 69, 883, 359]),
        ('profile_L', [913, 68, 1123, 356]),
        ('back', [1149, 69, 1333, 365])
    ]
    for ang_name, box in angles:
        pid = f"head.{ang_name}"
        p = cut('heads.jpg', box, pid, [0.5, 0.88], {'neck': [0.5, 0.88], 'eye': [0.7, 0.45]})
        reg['parts'][pid] = p

    # 4. Segmented legs from legs_segmented.jpg (separate thigh, shin, boots)
    p = cut('legs_segmented.jpg', [391, 47, 499, 241], 'thigh.profile', [0.5, 0.1],
            {'hip': [0.5, 0.1], 'knee': [0.5, 0.9]})
    reg['parts']['thigh.profile'] = p

    p = cut('legs_segmented.jpg', [397, 297, 488, 551], 'shin.profile', [0.5, 0.1],
            {'knee': [0.5, 0.1], 'ankle': [0.5, 0.9]})
    reg['parts']['shin.profile'] = p

    p = cut('legs_segmented.jpg', [73, 593, 262, 734], 'boot.flat', [0.35, 0.25],
            {'ankle': [0.35, 0.25], 'toe': [0.85, 0.85], 'heel': [0.15, 0.85]})
    reg['parts']['boot.flat'] = p

    p = cut('legs_segmented.jpg', [305, 564, 481, 733], 'boot.toe', [0.4, 0.25],
            {'ankle': [0.4, 0.25], 'toe': [0.75, 0.85], 'heel': [0.2, 0.7]})
    reg['parts']['boot.toe'] = p

    # 5. Hands from hands.jpg
    p = cut('hands.jpg', [60, 50, 220, 220], 'hand.grip', [0.2, 0.5], {'wrist': [0.2, 0.5], 'palm': [0.6, 0.5]})
    reg['parts']['hand.grip'] = p

    p = cut('hands.jpg', [240, 50, 390, 220], 'hand.fist', [0.2, 0.5], {'wrist': [0.2, 0.5], 'palm': [0.6, 0.5]})
    reg['parts']['hand.fist'] = p

    p = cut('hands.jpg', [410, 50, 570, 220], 'hand.point', [0.2, 0.5], {'wrist': [0.2, 0.5], 'tip': [0.85, 0.5]})
    reg['parts']['hand.point'] = p

    out_json = os.path.join(HERE, 'cast.json')
    json.dump(reg, open(out_json, 'w'), indent=1)
    print(f"Wrote {len(reg['parts'])} sliced parts and {out_json}")


if __name__ == '__main__':
    main()
