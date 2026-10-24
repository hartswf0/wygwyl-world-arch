"""Seam detectors that measure the DRAWN result (round 04 of the QA): visible tab, light rim, brad/grommet
registration and crescents, colour mismatch. Validated against the blind critic's named defects on the joint lab's
48 judged renders (qa/validation/report.json, qa/validation/validate_critic.py).

All take the final composite and the two parts as placed:
    comp      HxWx3 uint8, the composite over its background (what a viewer sees)
    mP, mC    bool silhouettes of parent and child as placed (whatever is on top)
    J         joint pivot (x, y)
    axP, axC  unit vectors from the joint INTO the parent / INTO the child
    over      'parent' or 'child' (which is drawn on top at the joint)
    ppc       pixels per cm of the composite
    layerP, layerC  each part's own RGBA as placed (for the painted rings)
    brad      bool mask of a brad sprite drawn at the joint (None if the method draws none)
"""
import numpy as np
import cv2


def _hsv(rgb):
    return cv2.cvtColor(np.ascontiguousarray(rgb[..., :3]), cv2.COLOR_RGB2HSV).astype(int)


def brass(rgb, alpha=None):
    h = _hsv(rgb)
    m = (h[..., 0] >= 15) & (h[..., 0] <= 34) & (h[..., 1] >= 80) & (h[..., 2] >= 100)
    if alpha is not None:
        m &= alpha > 128
    return m


def _disk(shape, J, r):
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    return (xx - J[0]) ** 2 + (yy - J[1]) ** 2 <= r * r


def visible(mP, mC, over):
    """what each part shows in the composite"""
    vP = mP & (~mC if over == 'child' else np.ones_like(mP))
    vC = mC & (~mP if over == 'parent' else np.ones_like(mC))
    return vP, vC


def tab_visible(comp, mP, mC, J, axP, axC, over, ppc, brad=None, depth_cm=0.3, reach_cm=6.0):
    """area (cm^2) of each part's VISIBLE pixels lying beyond the joint on the other part's side (an overlap tab,
    tongue, lobe or cuff end that shows), within reach_cm of the joint"""
    H, W = mP.shape
    yy, xx = np.mgrid[0:H, 0:W]
    dx, dy = xx - J[0], yy - J[1]
    near = dx * dx + dy * dy <= (reach_cm * ppc) ** 2
    beyondC = mC & ((dx * axC[0] + dy * axC[1]) < -depth_cm * ppc)      # child pixels on the parent side
    beyondP = mP & ((dx * axP[0] + dy * axP[1]) < -depth_cm * ppc)      # parent pixels on the child side
    vP, vC = visible(mP, mC, over)
    t = ((beyondC & vC) | (beyondP & vP)) & near
    if brad is not None:
        t &= ~cv2.dilate(brad.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    t = cv2.morphologyEx(t.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(bool)
    ys, xs = np.nonzero(t)
    spot = [float(xs.mean()), float(ys.mean())] if len(xs) else None
    return float(t.sum() / ppc ** 2), spot


def light_rim(comp, mP, mC, J, over, ppc, band=(0.2, 0.5), reach_cm=8.0):
    """fraction of light, low-saturation pixels in a 0.2-0.5 cm band on BOTH sides of the seam contour (the over
    part's outline inside the under part), kept inside the figure, within reach_cm of the joint"""
    U = mP | mC
    om = mC if over == 'child' else mP
    um = mP if over == 'child' else mC
    near = _disk(mP.shape, J, reach_cm * ppc)
    edge = om & ~cv2.erode(om.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    seam = edge & um & near          # the over part's outline where it lies ON the under part
    if seam.sum() < 5:
        return 0.0, None
    dist = cv2.distanceTransform((~seam).astype(np.uint8), cv2.DIST_L2, 3)
    k = max(3, int(0.25 * ppc) * 2 + 1)        # keep 0.25 cm away from the figure's own outer silhouette
    inner = cv2.erode(U.astype(np.uint8), np.ones((k, k), np.uint8)).astype(bool)
    bandm = (dist <= band[1] * ppc) & inner & near
    h = _hsv(comp)
    light = (h[..., 2] > 170) & (h[..., 1] < 60)
    if bandm.sum() < 10:
        return 0.0, None
    f = light & bandm
    ys, xs = np.nonzero(f)
    return float(f.sum() / bandm.sum()), ([float(xs.mean()), float(ys.mean())] if len(xs) else None)


def _components(m, min_px=3, round_only=False):
    n, lab, st, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    out = []
    for i in range(1, n):
        if round_only and min(st[i, 2], st[i, 3]) < 0.6 * max(st[i, 2], st[i, 3]):
            continue
        if st[i, 4] >= min_px:
            fill = st[i, 4] / max(1, st[i, 2] * st[i, 3])
            # centre = bbox centre: a lit brass ring's colour mask is lopsided (shading), its extent is not
            out.append(dict(c=np.array([st[i, 0] + st[i, 2] / 2.0, st[i, 1] + st[i, 3] / 2.0]), r=0.5 * max(st[i, 2], st[i, 3]), area=int(st[i, 4]), fill=float(fill), mask=lab == i))
    return out


def grommet(comp, layerP, layerC, J, ppc, brad=None, reach_cm=2.5):
    """registration of the drawn brad on the painted ring, measured on the composite.
    Returns dict(registration_cm, bare_brad, crescent_cm, peek_frac, spot):
    - rings: painted brass rings of either part near the joint (from the layers);
    - brad: the drawn brad sprite (brad mask) or, without one, the top part's brass nearest the joint;
    - registration_cm: brad centre to the nearest ring centre;
    - bare_brad: a brad with no ring under it (no ring centre within 1 cm);
    - crescent_cm: the thickest band of a ring still visible as brass in the composite outside the brad;
    - peek_frac: visible fraction of the ring's brass area (a half grommet peeking when 0.15-0.85, no brad over it)."""
    near = _disk(comp.shape[:2], J, reach_cm * ppc)
    rings = []
    for li, L in enumerate((layerP, layerC)):
        if L is None:
            continue
        for c in _components(brass(L[..., :3], L[..., 3]) & near, max(4, int(0.25 * ppc * ppc)), round_only=True):
            c['layer'] = li
            rings.append(c)
    bc = None
    if brad is not None and brad.any():
        bb = _components(brad & near, 3)
        if bb:
            bc = max(bb, key=lambda c: c['area'])
    res = dict(registration_cm=None, bare_brad=False, crescent_cm=0.0, peek_frac=None, spot=None)
    vis_brass = brass(comp) & near
    if bc is None and layerP is not None and layerC is not None:
        # no brad sprite: the joint is the two parts' own painted brads/grommets; take each part's brass nearest J
        def nearest(L):
            cs = _components(brass(L[..., :3], L[..., 3]) & near, max(4, int(0.25 * ppc * ppc)), round_only=True)
            return min(cs, key=lambda c: np.hypot(c['c'][0] - J[0], c['c'][1] - J[1])) if cs else None
        a, b = nearest(layerP), nearest(layerC)
        if a is not None and b is not None:
            res['registration_cm'] = round(float(np.hypot(*(a['c'] - b['c'])) / ppc), 3)
            # crescent: brass of either ring still visible outside the other ring's disc
            for x, y in ((a, b), (b, a)):
                disc = np.zeros(comp.shape[:2], np.uint8)
                cv2.circle(disc, (int(round(y['c'][0])), int(round(y['c'][1]))), int(round(y['r'])), 1, -1)
                cres = x['mask'] & vis_brass & ~disc.astype(bool)
                if cres.sum() > 2:
                    dt = cv2.distanceTransform(cres.astype(np.uint8), cv2.DIST_L2, 3)
                    res['crescent_cm'] = max(res['crescent_cm'], round(float(2 * dt.max() / ppc), 3))
                    ys, xs = np.nonzero(cres)
                    res['spot'] = [float(xs.mean()), float(ys.mean())]
    if bc is not None:
        if rings:
            d = [np.hypot(*(r['c'] - bc['c'])) for r in rings]
            i = int(np.argmin(d))
            res['registration_cm'] = round(float(d[i] / ppc), 3)
            res['bare_brad'] = bool(d[i] > 1.0 * ppc)
            ring = rings[i]
            cres = ring['mask'] & vis_brass & ~cv2.dilate(brad.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
            if cres.any():
                dt = cv2.distanceTransform(cres.astype(np.uint8), cv2.DIST_L2, 3)
                res['crescent_cm'] = round(float(2 * dt.max() / ppc), 3)
                ys, xs = np.nonzero(cres)
                res['spot'] = [float(xs.mean()), float(ys.mean())]
        else:
            res['bare_brad'] = True
            res['spot'] = [float(bc['c'][0]), float(bc['c'][1])]
    for ring in rings:     # a ring partly hidden by the other part with no brad on it: a half grommet peeking
        if bc is not None and np.hypot(*(ring['c'] - bc['c'])) < 1.0 * ppc:
            continue
        # concentric with the other part's ring (a brad seen through an eyelet): registered, not peeking
        if any(o['layer'] != ring['layer'] and np.hypot(*(o['c'] - ring['c'])) < 0.8 * max(o['r'], ring['r']) for o in rings):
            continue
        vis = float((ring['mask'] & vis_brass).sum() / max(1, ring['area']))
        if 0.15 < vis < 0.85:
            res['peek_frac'] = round(vis, 3)
            ys, xs = np.nonzero(ring['mask'])
            res['spot'] = res['spot'] or [float(xs.mean()), float(ys.mean())]
            break
    return res


def _materials(lab, hsv, m):
    """split a part's pixels into skin (warm, saturated, mid-light) and cloth/leather (the rest, brass excluded)"""
    hh, ss, vv = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    skin = m & (hh >= 4) & (hh <= 25) & (ss >= 60) & (vv >= 70)
    cloth = m & ~skin
    return skin, cloth


def colour_mismatch(comp, mP, mC, J, over, ppc, reach_cm=7.0):
    """CIE76 delta-E between the two parts' VISIBLE pixels near the joint, compared MATERIAL TO MATERIAL: skin
    against skin, cloth/leather against cloth/leather (a black sleeve next to a brown hand is not a mismatch; a grey
    boot under a black trouser leg, or a pale hand next to a brown one, is). Returns the larger matched delta-E, or
    None when the two parts share no material near the joint."""
    near = _disk(mP.shape, J, reach_cm * ppc)
    vP, vC = visible(mP, mC, over)
    lab = cv2.cvtColor(np.ascontiguousarray(comp[..., :3]), cv2.COLOR_RGB2LAB).astype(float)
    lab[..., 0] *= 100 / 255.0
    lab[..., 1:] -= 128
    h = _hsv(comp)
    ok = ~brass(comp)
    sP, cP = _materials(lab, h, vP & near & ok)
    sC, cC = _materials(lab, h, vC & near & ok)
    best = None
    for a, b in ((sP, sC), (cP, cC)):
        if a.sum() >= 30 and b.sum() >= 30 and a.sum() >= 0.2 * (sP.sum() + cP.sum()) and b.sum() >= 0.2 * (sC.sum() + cC.sum()):
            d = float(np.linalg.norm(np.median(lab[a], 0) - np.median(lab[b], 0)))
            best = d if best is None else max(best, d)
    return best
