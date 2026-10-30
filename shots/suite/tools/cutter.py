"""Cut one painted sheet into cards, reusing the release cutter (arena/parts/kit3/cut_release_kits.py).

The release cutter assumes a pure-white ground. The v2 renders and the weave sheets sit on an
off-white, vignetted paper, so the ground is flattened first: a paper model (max filter of the
sheet, i.e. the brightest paper near each pixel) is subtracted, and any low-saturation pixel
within 12 levels of its local paper becomes pure white. Then cut_single_sheet does the rest
(alpha from the card vs the ground, connected components, interior holes, brass brad detection).
"""
import os, sys, tempfile
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(SHOTS, 'arena', 'parts', 'kit3'))
import cut_release_kits as CRK  # noqa: E402

detect_brass_pivots = CRK.detect_brass_pivots


def flatten_ground(bgr, tol=12):
    h, w = bgr.shape[:2]
    lum = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    k = 4
    small = cv2.resize(lum, (w // k, h // k), interpolation=cv2.INTER_AREA)
    paper = cv2.dilate(small, np.ones((41, 41), np.uint8))
    paper = cv2.GaussianBlur(paper, (0, 0), 6)
    paper = cv2.resize(paper, (w, h), interpolation=cv2.INTER_LINEAR).astype(int)
    mx = bgr.max(2).astype(int)
    mn = bgr.min(2).astype(int)
    sat = mx - mn
    ground = (lum.astype(int) >= paper - tol) & (sat <= 18) & (paper >= 200)
    out = bgr.copy()
    out[ground] = 255
    return out, ground


def cut(sheet_path, sheet_id, out_dir, flatten=True, prompt=''):
    """Returns the release cutter's result dict; part PNGs land in out_dir/<sheet_id>/."""
    bgr = cv2.imread(sheet_path, cv2.IMREAD_COLOR)
    if bgr is None:
        return {'id': sheet_id, 'error': 'unreadable', 'parts': []}
    src = sheet_path
    tmp = None
    if flatten:
        flat, _ = flatten_ground(bgr)
        fd, tmp = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        cv2.imwrite(tmp, flat)
        src = tmp
    CRK.CUTS_DIR = out_dir
    try:
        res = CRK.cut_single_sheet({'id': sheet_id, 'sheet_path': src, 'prompt': '', 'kind': ''})
    finally:
        if tmp:
            os.remove(tmp)
    # restore true colour inside each cut (flattening only decided the ground)
    for p in res.get('parts', []):
        f = os.path.join(out_dir, sheet_id, os.path.basename(p['file']))
        rgba = cv2.imread(f, cv2.IMREAD_UNCHANGED)
        x, y, w, h = p['bbox_sheet']
        pad = 6
        x0, y0 = max(0, x - pad), max(0, y - pad)
        roi = bgr[y0:y0 + rgba.shape[0], x0:x0 + rgba.shape[1]]
        if roi.shape[:2] == rgba.shape[:2]:
            rgba[:, :, :3] = roi
            cv2.imwrite(f, rgba)
        p['abs'] = f
        p['origin'] = [x0, y0]
    return res


def brads(rgba, min_r=4, max_r=30):
    """Brass brads/eyelets on one cut card (stricter than the release detector, which also fires on
    the kraft cut edge and warm skin): brass-coloured blobs that are round once holes are filled,
    roughly square, and sit inside the card rather than on its rim."""
    b = rgba[:, :, 0].astype(int); g = rgba[:, :, 1].astype(int); r = rgba[:, :, 2].astype(int)
    a = rgba[:, :, 3]
    hsv = cv2.cvtColor(np.ascontiguousarray(rgba[:, :, :3]), cv2.COLOR_BGR2HSV)
    H, S, V = hsv[:, :, 0].astype(int), hsv[:, :, 1].astype(int), hsv[:, :, 2].astype(int)
    # brass is yellower (hue 19-34 of 180) and brighter than kraft (hue ~15-17) or dark skin
    brass = (a > 128) & (H >= 19) & (H <= 34) & (S >= 45) & (V >= 95)
    m = cv2.morphologyEx(brass.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # fill eyelet holes so a ring reads as a disc
    ff = m.copy(); hh, ww = ff.shape
    mask = np.zeros((hh + 2, ww + 2), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 255)
    m = m | cv2.bitwise_not(ff)
    inside = cv2.distanceTransform((a > 128).astype(np.uint8), cv2.DIST_L2, 3)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        rr = (w + h) / 4.0
        if not (min_r <= rr <= max_r) or not (0.72 <= w / max(1, h) <= 1.38):
            continue
        comp = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
        filled = comp.copy()
        cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not cnts:
            continue
        c = max(cnts, key=cv2.contourArea)
        A = cv2.contourArea(c)
        P = cv2.arcLength(c, True)
        if P <= 0 or A <= 0:
            continue
        circ = 4 * np.pi * A / (P * P)
        fill = A / float(w * h)
        cx, cy = float(cen[i][0]), float(cen[i][1])
        depth = inside[int(round(cy)), int(round(cx))] if 0 <= int(cy) < a.shape[0] and 0 <= int(cx) < a.shape[1] else 0
        if circ < 0.58 or not (0.52 <= fill <= 0.92) or depth < 0.5 * rr:
            continue
        out.append({'x': round(cx, 1), 'y': round(cy, 1), 'r': round(rr, 1), 'circ': round(circ, 2)})
    # merge duplicates (ring split in two)
    keep = []
    for p in sorted(out, key=lambda q: -q['r']):
        if all(np.hypot(p['x'] - k['x'], p['y'] - k['y']) > max(p['r'], k['r']) for k in keep):
            keep.append(p)
    return keep
