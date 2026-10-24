"""SPACE step 1: pixel measurements for every set-piece card (kind 'card' on .props./.set./.hero./.fx. sheets).

Everything here is MEASURED from the cut webp alpha + colour. Cached to cache/measure.json (re-run only adds missing ids).

Per part:
  W,H            image size (== catalog bbox w,h)
  fill           opaque px / (W*H)
  soft           share of non-zero alpha px that are partly transparent (painted haze / glow cards)
  y_low          lowest opaque row (>= 3 opaque px, so a stray pixel does not count)
  base_x0/x1     opaque x extent inside the bottom band (y_low - band .. y_low), band = max(3, 2% H)
  base_runs      separate opaque runs in that band (legs / feet / wheels count)
  top_x0/x1       opaque x extent in the top band (the hanging point for a hung piece)
  base_frac      (base_x1-base_x0)/W
  top_slope, bot_slope    least-squares slope (px/px) of the top / bottom silhouette over the central 80% of columns
  left_slope, right_slope slope (dx/dy) of the left / right silhouette over the central 80% of rows
  conv_tb        bot_slope - top_slope: >0 means top and bottom edges diverge to the right (receding wall drawn in
                 perspective whose near end is on the right), <0 near end on the left
  conv_lr        right_slope - left_slope: >0 widens downward (trapezoid floor seen in perspective)
  straight_l/r   share of rows (in the opaque y range) whose silhouette sits within 3 px (or 1% W) of the edge column:
                 1.0 = a cut-straight vertical edge
  seam           mean |Lab| difference between the left 6 px and right 6 px strips (rows both opaque), and luma
                 profile correlation (seam_corr). Small diff + straight edges = tileable sideways.
  border_l/r     mean |Lab| between the outer 6 px strip and the 6 px strip 14 px further in (painted frame test)
  edge_touch     share of each border (t,b,l,r) of the image that is opaque (a full-bleed rectangle touches all)
  sym, sym_luma  silhouette mirror IoU, and mean |luma - mirrored luma| on the overlap (paint symmetry)
  L, sat         mean Lab L and HSV saturation over opaque px
"""
import json, os, sys
import numpy as np, cv2
cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')
TAGS = ('.props.', '.set.', '.hero.', '.fx.')


def setpieces():
    cat = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
    return cat, [(sid, p) for sid, s in cat.items() if any(t in sid for t in TAGS) for p in s['parts']]


def fit_slope(xs, ys):
    if len(xs) < 5:
        return 0.0, 0.0
    A = np.vstack([xs, np.ones_like(xs)]).T.astype(np.float64)
    sol, res, *_ = np.linalg.lstsq(A, ys.astype(np.float64), rcond=None)
    pred = A @ sol
    return float(sol[0]), float(np.sqrt(np.mean((ys - pred) ** 2)))


def measure(path):
    px = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if px is None:
        return None
    if px.ndim == 2:
        px = cv2.cvtColor(px, cv2.COLOR_GRAY2BGRA)
    if px.shape[2] == 3:
        px = np.dstack([px, np.full(px.shape[:2], 255, np.uint8)])
    a = px[:, :, 3]
    H, W = a.shape
    m = a > 127
    n = int(m.sum())
    r = {'W': W, 'H': H, 'fill': round(n / (W * H), 4)}
    nz = a > 8
    r['soft'] = round(float(((a > 8) & (a < 230)).sum() / max(1, nz.sum())), 4)
    if n < 20:
        r['empty'] = True
        return r
    rows = m.sum(1)
    cols = m.sum(0)
    ys = np.where(rows >= 3)[0]
    if len(ys) == 0:
        ys = np.where(rows > 0)[0]
    xs_any = np.where(cols >= 3)[0]
    if len(xs_any) == 0:
        xs_any = np.where(cols > 0)[0]
    y0, y1 = int(ys[0]), int(ys[-1])
    x0, x1 = int(xs_any[0]), int(xs_any[-1])
    r.update(y_top=y0, y_low=y1, x_min=x0, x_max=x1)
    band = max(3, int(round(0.02 * H)))
    bb = m[max(0, y1 - band + 1):y1 + 1].any(0)
    bx = np.where(bb)[0]
    r['base_x0'], r['base_x1'] = int(bx[0]), int(bx[-1])
    r['base_frac'] = round((bx[-1] - bx[0] + 1) / W, 4)
    r['base_fill'] = round(float(bb.sum()) / W, 4)
    # runs in the bottom band, ignoring gaps < 1% W
    runs, prev, gap = 0, False, 0
    mingap = max(3, int(0.01 * W))
    for v in bb:
        if v:
            if not prev and (runs == 0 or gap >= mingap):
                runs += 1
            prev, gap = True, 0
        else:
            prev = False
            gap += 1
    r['base_runs'] = runs
    tb = m[y0:y0 + band].any(0)
    tx = np.where(tb)[0]
    r['top_x0'], r['top_x1'] = int(tx[0]), int(tx[-1])
    # silhouettes
    colhas = m.any(0)
    cx = np.where(colhas)[0]
    top = m.argmax(0)
    bot = H - 1 - m[::-1].argmax(0)
    lo, hi = np.percentile(cx, [10, 90])
    sel = cx[(cx >= lo) & (cx <= hi)]
    r['top_slope'], r['top_rms'] = [round(v, 4) for v in fit_slope(sel, top[sel])]
    r['bot_slope'], r['bot_rms'] = [round(v, 4) for v in fit_slope(sel, bot[sel])]
    rowhas = m.any(1)
    ry = np.where(rowhas)[0]
    left = m.argmax(1)
    right = W - 1 - m[:, ::-1].argmax(1)
    lo, hi = np.percentile(ry, [10, 90])
    sely = ry[(ry >= lo) & (ry <= hi)]
    r['left_slope'], r['left_rms'] = [round(v, 4) for v in fit_slope(sely, left[sely])]
    r['right_slope'], r['right_rms'] = [round(v, 4) for v in fit_slope(sely, right[sely])]
    r['conv_tb'] = round(r['bot_slope'] - r['top_slope'], 4)
    r['conv_lr'] = round(r['right_slope'] - r['left_slope'], 4)
    tol = max(3, int(0.01 * W))
    r['straight_l'] = round(float((left[ry] <= x0 + tol).mean()), 4)
    r['straight_r'] = round(float((right[ry] >= x1 - tol).mean()), 4)
    tolh = max(3, int(0.01 * H))
    r['straight_b'] = round(float((bot[cx] >= y1 - tolh).mean()), 4)
    r['straight_t'] = round(float((top[cx] <= y0 + tolh).mean()), 4)
    r['edge_touch'] = [round(float(m[0].mean()), 3), round(float(m[-1].mean()), 3),
                       round(float(m[:, 0].mean()), 3), round(float(m[:, -1].mean()), 3)]
    # seam: compare the 6 px just inside the left / right silhouette, row by row
    lab = cv2.cvtColor(px[:, :, :3], cv2.COLOR_BGR2LAB).astype(np.float32)
    k = 6
    li = np.clip(left[:, None] + 2 + np.arange(k)[None], 0, W - 1)
    rj = np.clip(right[:, None] - 2 - np.arange(k)[None], 0, W - 1)
    rr = np.arange(H)[:, None]
    okrow = rowhas & (right - left > 4 * k)
    if okrow.sum() >= 10:
        Ls = lab[rr, li][okrow].mean(1)
        Rs = lab[rr, rj][okrow].mean(1)
        r['seam'] = round(float(np.abs(Ls - Rs).mean()), 2)
        a1, b1 = Ls[:, 0], Rs[:, 0]
        if a1.std() > 1 and b1.std() > 1:
            r['seam_corr'] = round(float(np.corrcoef(a1, b1)[0, 1]), 3)
        else:
            r['seam_corr'] = None
        # painted border test: the outer 6 px vs the 6 px starting 14 px further in. A frame / card border
        # changes colour there; a texture that runs off the edge does not.
        li2 = np.clip(left[:, None] + 14 + np.arange(k)[None], 0, W - 1)
        rj2 = np.clip(right[:, None] - 14 - np.arange(k)[None], 0, W - 1)
        Li = lab[rr, li2][okrow].mean(1)
        Ri = lab[rr, rj2][okrow].mean(1)
        r['border_l'] = round(float(np.abs(Ls - Li).mean()), 2)
        r['border_r'] = round(float(np.abs(Rs - Ri).mean()), 2)
    else:
        r['seam'], r['seam_corr'] = None, None
        r['border_l'] = r['border_r'] = None
    hsv = cv2.cvtColor(px[:, :, :3], cv2.COLOR_BGR2HSV)
    r['L'] = round(float(lab[:, :, 0][m].mean() * 100 / 255), 1)
    r['sat'] = round(float(hsv[:, :, 1][m].mean() / 255), 3)
    # mirror symmetry of the silhouette inside its x range (front views of furniture/doors are near-symmetric;
    # 3/4 and side views are not): IoU(mask, mask flipped about the opaque x-centre)
    crop = m[y0:y1 + 1, x0:x1 + 1]
    fl = crop[:, ::-1]
    r['sym'] = round(float((crop & fl).sum() / max(1, (crop | fl).sum())), 4)
    g = lab[y0:y1 + 1, x0:x1 + 1, 0]
    both = crop & fl
    r['sym_luma'] = round(float(np.abs(g - g[:, ::-1])[both].mean()), 2) if both.sum() > 50 else None
    # components (opaque, 8-conn) above 1% of the opaque area
    nc, lbl, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    areas = st[1:, cv2.CC_STAT_AREA]
    r['comps'] = int((areas > 0.01 * n).sum())
    return r


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'cache'), exist_ok=True)
    out_p = os.path.join(HERE, 'cache', 'measure.json')
    have = json.load(open(out_p)) if os.path.exists(out_p) else {}
    cat, parts = setpieces()
    todo = [p for _, p in parts if p['kind'] == 'card' and p['id'] not in have]
    print(len(parts), 'parts;', len(todo), 'to measure', flush=True)
    for i, p in enumerate(todo):
        have[p['id']] = measure(os.path.join(CUT, p['file']))
        if i % 300 == 299:
            json.dump(have, open(out_p, 'w'))
            print(i + 1, flush=True)
    json.dump(have, open(out_p, 'w'))
    print('done', len(have))
