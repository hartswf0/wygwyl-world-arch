"""Pass 1: measure every set piece from its pixels (no decisions here). Writes cache/measure.json and
cache/clip_img.npy (+ cache/clip_ids.json). Run: python3 measure.py   (single thread, ~5 min)."""
import json, os, sys, time
import numpy as np, cv2
from scipy import ndimage as ndi
from common import setpieces, load_rgba, comp, CACHE, HERE

sys.path.insert(0, os.path.join(HERE, '..', '..', 'evolve', 'puzzle'))


def pale_mask(rgb):
    rgb = rgb.astype(int)
    return (rgb.min(2) > 200) & (rgb.max(2) - rgb.min(2) < 24)        # light + low saturation (paper white / grey)


def phash(gray):
    g = cv2.resize(gray.astype(np.float32), (32, 32), interpolation=cv2.INTER_AREA)
    d = cv2.dct(g)[:8, :8].ravel()[1:]
    return ''.join('1' if v > np.median(d) else '0' for v in d)       # 63 bits


def measure(p):
    px = load_rgba(p)
    h, w = px.shape[:2]
    A = px[..., 3]
    a = A > 128
    n = int(a.sum())
    r = {'w': w, 'h': h, 'area': n, 'fill': round(n / max(1, w * h), 3),
         'soft_alpha': round(float(((A > 8) & (A < 247)).sum()) / max(1, n), 3)}
    if n < 30:
        r['empty'] = True
        return r, px
    rgb = px[..., :3]
    # components (8-connected) and their share of the alpha
    k, lab, st, _ = cv2.connectedComponentsWithStats(a.astype(np.uint8), connectivity=8)
    areas = sorted((int(x) for x in st[1:, cv2.CC_STAT_AREA]), reverse=True)
    r['comp_fracs'] = [round(x / n, 4) for x in areas[:12]]
    r['n_comp'] = len(areas)
    r['n_comp_1pct'] = sum(x >= .01 * n for x in areas)
    r['n_comp_5pct'] = sum(x >= .05 * n for x in areas)
    # ink in satellite components (printed numbers / labels next to the object)
    if len(areas) > 1:
        main = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        sat = a & (lab != main)
        g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        r['sat_ink'] = round(float(((g < 90) & sat).sum()) / max(1, sat.sum()), 3)
        r['sat_pale'] = round(float((pale_mask(rgb) & sat).sum()) / max(1, sat.sum()), 3)
        # where the satellites sit relative to the main body (gap in px)
        mx, my, mw, mh = st[main, :4]
        r['main_bbox'] = [int(mx), int(my), int(mw), int(mh)]
    # thinness: share of alpha surviving an erosion (5 px and 11 px)
    r['erode5'] = round(float(cv2.erode(a.astype(np.uint8), np.ones((5, 5), np.uint8)).sum()) / n, 3)
    r['erode11'] = round(float(cv2.erode(a.astype(np.uint8), np.ones((11, 11), np.uint8)).sum()) / n, 3)
    # holes
    filled = ndi.binary_fill_holes(a)
    hl, hn = ndi.label(filled & ~a)
    hs = np.bincount(hl.ravel())[1:] if hn else np.array([])
    fa = int(filled.sum())
    r['hole_frac'] = round(float(hs.sum()) / fa, 4) if hn else 0.
    r['n_holes_big'] = int((hs >= .005 * fa).sum()) if hn else 0
    r['largest_hole'] = round(float(hs.max()) / fa, 4) if hn else 0.
    # fringe: outer 2 px band vs a band 6..12 px inside
    er2 = cv2.erode(a.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)      # 2 px in
    ring = a & ~er2
    e6 = cv2.erode(a.astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool)
    e12 = cv2.erode(a.astype(np.uint8), np.ones((25, 25), np.uint8)).astype(bool)
    inner = e6 & ~e12
    if inner.sum() < 50:
        inner = er2
    pm = pale_mask(rgb)
    r['ring_px'] = int(ring.sum())
    r['fringe_frac'] = round(float(pm[ring].mean()), 3) if ring.sum() else 0.
    r['inner_pale'] = round(float(pm[inner].mean()), 3) if inner.sum() else 0.
    r['body_pale'] = round(float(pm[a].mean()), 3)
    # band 2..4 px in (a wider halo is a paper border, not a matte edge)
    er4 = cv2.erode(a.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    b24 = er2 & ~er4
    r['fringe_2_4'] = round(float(pm[b24].mean()), 3) if b24.sum() else 0.
    # straight sides on the crop box: coverage of the boundary rows/cols, longest opaque run, and whether the paint
    # continues across the edge (low contrast between the edge row and rows 3..6 px in => the cut went through paint)
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    sides = {}
    for name, edge, inside in [('top', (slice(0, 2), slice(None)), (slice(3, 7), slice(None))),
                               ('bottom', (slice(h - 2, h), slice(None)), (slice(h - 7, h - 3), slice(None))),
                               ('left', (slice(None), slice(0, 2)), (slice(None), slice(3, 7))),
                               ('right', (slice(None), slice(w - 2, w)), (slice(None), slice(w - 7, w - 3)))]:
        ax = 0 if name in ('top', 'bottom') else 1
        cov = a[edge].any(axis=ax)
        L = len(cov)
        runs, best, cur = 0, 0, 0
        for v in cov:
            cur = cur + 1 if v else 0
            best = max(best, cur)
        sd = {'cov': round(float(cov.mean()), 3), 'run': round(best / L, 3), 'len': L}
        if cov.sum() > 10 and min(h, w) > 12:
            m = cov.astype(bool)
            e = g[edge].mean(axis=ax)[m]
            i_ = g[inside].mean(axis=ax)[m]
            sd['dE_in'] = round(float(np.abs(e - i_).sum(1).mean()), 1)
            sd['edge_pale'] = round(float(pm[edge].any(axis=ax)[m].mean()), 3)
            sd['edge_dark'] = round(float((g[edge][..., 0].mean(axis=ax)[m] < 70).mean()), 3)
        sides[name] = sd
    r['sides'] = sides
    bx, by, bw, bh = p['bbox']
    S = p.get('sheet_size') or [0, 0]
    r['touch_sheet'] = [s for s, t in [('left', bx <= 2), ('top', by <= 2), ('right', S[0] and bx + bw >= S[0] - 2),
                                         ('bottom', S[1] and by + bh >= S[1] - 2)] if t]
    r['sheet_frac'] = round(bw * bh / max(1, S[0] * S[1]), 3) if S[0] else None
    # ink: printed lettering = near-black or flat white, little colour
    gl = g[..., 0]
    chroma = np.hypot(g[..., 1] - 128, g[..., 2] - 128)
    r['ink_dark'] = round(float(((gl < 60) & a).sum()) / n, 3)
    r['low_chroma'] = round(float(((chroma < 8) & a).sum()) / n, 3)
    r['mean_chroma'] = round(float(chroma[a].mean()), 1)
    # perceptual hashes: RGB on paper, and the alpha silhouette
    c = comp(px)
    r['phash'] = phash(cv2.cvtColor(c, cv2.COLOR_RGB2GRAY))
    m16 = cv2.resize(A.astype(np.float32), (16, 16), interpolation=cv2.INTER_AREA) > 128
    r['ahash'] = ''.join('1' if v else '0' for v in m16.ravel())
    r['mean_rgb'] = [round(float(x)) for x in rgb[a].mean(0)]
    return r, px


def main():
    P = setpieces()
    out_p = os.path.join(CACHE, 'measure.json')
    M = json.load(open(out_p)) if os.path.exists(out_p) and '--fresh' not in sys.argv else {}
    ids_p, emb_p = os.path.join(CACHE, 'clip_ids.json'), os.path.join(CACHE, 'clip_img.npy')
    cids = json.load(open(ids_p)) if os.path.exists(ids_p) else []
    cemb = list(np.load(emb_p)) if os.path.exists(emb_p) else []
    have = set(cids)
    import hygiene as H                       # shots/scion2/evolve/puzzle/hygiene.py: CLIP image embedding (1 thread)
    t0 = time.time()
    for i, p in enumerate(P):
        need_m, need_c = p['id'] not in M, p['id'] not in have
        if not (need_m or need_c):
            continue
        r, px = measure(p)
        if need_m:
            M[p['id']] = r
        if need_c and px[..., 3].max() > 0:
            cemb.append(H._img(px[..., [2, 1, 0, 3]]).astype(np.float32))  # _img expects BGRA
            cids.append(p['id']); have.add(p['id'])
        if i % 200 == 0:
            print(i, len(P), round(time.time() - t0), flush=True)
    json.dump(M, open(out_p, 'w'))
    np.save(emb_p, np.array(cemb, np.float32)); json.dump(cids, open(ids_p, 'w'))
    print('measured', len(M), 'clip', len(cids))


if __name__ == '__main__':
    main()
