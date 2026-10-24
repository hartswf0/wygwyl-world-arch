"""Seam tests for one joint between two attached parts: the reusable fitness for any joint method.

Stable interface (see qa/README.md):

    score(render_rgba, maskA, maskB, pivot, axisA, axisB, over='A', featuresA=None, featuresB=None,
          facingA=None, facingB=None, joint='generic') -> dict

All masks and points are in the render's pixel frame (y down).
- render_rgba: the composite, HxWx4 uint8.
- maskA, maskB: bool HxW, the full silhouette of each part as placed, whatever is on top.
- pivot: (x, y), the joint point where the two pivots coincide.
- axisA: unit vector at the pivot pointing from the joint INTO part A (along A's bone, away from B).
- axisB: the same for part B.
- over: 'A' or 'B', which part is drawn on top at this joint.
- featuresA / featuresB: lists of bool masks (or None) of painted features that must stay visible: a face, an
  off-joint brad, fingers. Only the under part's features can be covered.
- facingA / facingB: (view, facing) tags. The test fails when they are incompatible.

Returns the measurements, each named, plus 'verdict' (CLEAN / WARN / MUTILATED) and 'why' (the list of failing
terms):
- gap_px, gap_frac: background enclosed between the parts at the joint (the closing of the union minus the union,
  inside the joint disk), as a fraction of seam_w^2.
- width_A, width_B, width_ratio: each part's own cross-section width at the joint (measured across its axis at
  0.1 seam_w inside it); ratio = width_B / width_A. A width step is the ratio leaving the joint's tolerance (neck:
  the collar/neck end of the torso (B) may be 0.9-2.4x the head's neck (A)).
- gap ignores holes painted inside one part (eyelet holes, a hollow chest).
- exposed_A_frac, exposed_B_frac: pixels of a part lying beyond the joint (on the other part's side, i.e. its
  overlap tab or cut end) and outside the other part's silhouette. These are cut edges or tabs showing; fraction of
  seam_w^2. In the verdict the UNDER part's exposure counts fully. The over part's beyond-joint pixels are painted
  on top (a collar rim, a cuff), so they only warn when they pass 2x the fail level.
- covered: the largest fraction of an under-part feature hidden by the over part.
- colour_dE: CIE76 delta-E between the median colours on either side of the visible seam contour.
- facing_ok: bool or None.
- seam_w: the cross-section width used as the unit: the smaller of the two parts' widths at the pivot.
"""
import math
import numpy as np
import cv2

# per joint tolerances; the joint lab may override any of these
TOL = {
    'generic': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.08, cov_fail=0.25,
                    ratio=(0.6, 1.67), ratio_fail=(0.4, 2.5), dE_warn=None),
    # neck: a neck going into a collar is expected to step out (collar wider than neck)
    'neck': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.08, cov_fail=0.25,
                 ratio=(0.9, 2.4), ratio_fail=(0.7, 3.2), dE_warn=None),
    'wrist': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.1, cov_fail=0.3,
                  ratio=(0.5, 2.0), ratio_fail=(0.3, 3.0), dE_warn=None),
    'ankle': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.1, cov_fail=0.3,
                  ratio=(0.5, 2.5), ratio_fail=(0.3, 4.0), dE_warn=None),
    'elbow': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.1, cov_fail=0.3,
                  ratio=(0.7, 1.43), ratio_fail=(0.5, 2.0), dE_warn=18),
    'knee': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.1, cov_fail=0.3,
                 ratio=(0.7, 1.43), ratio_fail=(0.5, 2.0), dE_warn=18),
}


def _width(mask, p, u, dist):
    """outline width of mask across direction u (perpendicular), at p + u*dist"""
    H, W = mask.shape
    c = np.array(p, float) + np.array(u, float) * dist
    v = np.array([-u[1], u[0]], float)
    w = 0
    for sgn in (1, -1):
        k = 0
        while k < 2000:
            q = c + v * sgn * (k + 1)
            x, y = int(round(q[0])), int(round(q[1]))
            if not (0 <= x < W and 0 <= y < H) or not mask[y, x]:
                break
            k += 1
        w += k
    cx, cy = int(round(c[0])), int(round(c[1]))
    if not (0 <= cx < W and 0 <= cy < H) or not mask[cy, cx]:
        return 0.0
    return float(w + 1)


def _lab(rgb):
    return cv2.cvtColor(rgb.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(float) * [100 / 255, 1, 1] - [0, 128, 128]


def facing_compatible(fa, fb):
    """fa, fb = (view, facing). Views must be the same family; profile/3-4 facings must agree."""
    if not fa or not fb:
        return None
    va, sa = fa
    vb, sb = fb
    fam = lambda v: {'front': 'F', 'three-quarter': 'Q', 'side': 'S', 'three-quarter-back': 'QB', 'back': 'B'}.get(v, v)
    A, B = fam(va), fam(vb)
    near = {('F', 'Q'), ('Q', 'F'), ('Q', 'S'), ('S', 'Q'), ('B', 'QB'), ('QB', 'B')}
    if A != B and (A, B) not in near:
        return False
    if sa in ('screen-left', 'screen-right') and sb in ('screen-left', 'screen-right') and sa != sb:
        return False
    return True


def score(render_rgba, maskA, maskB, pivot, axisA, axisB, over='A', featuresA=None, featuresB=None,
          facingA=None, facingB=None, joint='generic', tol=None):
    T = dict(TOL.get(joint, TOL['generic']))
    if tol:
        T.update(tol)
    H, W = maskA.shape
    P = np.array(pivot, float)
    uA = np.array(axisA, float); uA /= (np.linalg.norm(uA) or 1)
    uB = np.array(axisB, float); uB /= (np.linalg.norm(uB) or 1)
    U = maskA | maskB
    wA0 = _width(maskA, P, uA, 0) or _width(maskA, P, uA, 4)
    wB0 = _width(maskB, P, uB, 0) or _width(maskB, P, uB, 4)
    seam_w = max(8.0, min([w for w in (wA0, wB0) if w > 0] or [40.0]))
    from scipy.ndimage import binary_fill_holes
    own_holes = (binary_fill_holes(maskA) & ~maskA) | (binary_fill_holes(maskB) & ~maskB)
    R = 0.9 * seam_w
    yy, xx = np.mgrid[0:H, 0:W]
    dx, dy = xx - P[0], yy - P[1]
    disk = dx * dx + dy * dy <= R * R
    # gap: background enclosed by the union near the joint
    k = max(3, int(0.15 * seam_w) | 1)
    closed = cv2.morphologyEx(U.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))).astype(bool)
    gap = closed & ~U & disk & ~own_holes      # painted holes (eyelets, a hollow chest) are not seams
    gap_px = int(gap.sum())
    # widths of the visible union just inside each part
    # cross-section of each part at the joint (just inside it): the two ends that meet
    wA = _width(maskA, P, uA, 0.1 * seam_w) or wA0
    wB = _width(maskB, P, uB, 0.1 * seam_w) or wB0
    ratio = (wB / wA) if wA > 0 else float('inf')
    # exposed: a part's pixels beyond the joint (on the other part's side) outside the other's silhouette
    m = 0.06 * seam_w
    beyondA = maskA & ((dx * uA[0] + dy * uA[1]) < -m) & (dx * dx + dy * dy <= (2.5 * seam_w) ** 2)
    beyondB = maskB & ((dx * uB[0] + dy * uB[1]) < -m) & (dx * dx + dy * dy <= (2.5 * seam_w) ** 2)
    expA = beyondA & ~maskB
    expB = beyondB & ~maskA
    # small erosion so 1-2 px antialias fringes do not count
    er = lambda x: cv2.erode(x.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    expA_px, expB_px = int(er(expA).sum()), int(er(expB).sum())
    # covered features of the under part
    under_feats = featuresB if over == 'A' else featuresA
    over_mask = maskA if over == 'A' else maskB
    covered = 0.0
    for f in under_feats or []:
        if f is not None and f.sum() > 0:
            covered = max(covered, float((f & over_mask).sum() / f.sum()))
    # colour jump across the visible seam contour inside the disk
    under_mask = maskB if over == 'A' else maskA
    edge_in = over_mask & ~cv2.erode(over_mask.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool) & disk
    ring_out = cv2.dilate(over_mask.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & ~over_mask & under_mask & disk
    dE = None
    if edge_in.sum() > 20 and ring_out.sum() > 20:
        rgb = render_rgba[..., :3]
        la = np.median(_lab(rgb[edge_in]), 0)
        lb = np.median(_lab(rgb[ring_out]), 0)
        dE = float(np.linalg.norm(la - lb))
    fok = facing_compatible(facingA, facingB)
    s2 = seam_w * seam_w
    r = dict(seam_w=round(seam_w, 1), gap_px=gap_px, gap_frac=round(gap_px / s2, 4), width_A=round(wA, 1), width_B=round(wB, 1),
             width_ratio=round(ratio, 3) if math.isfinite(ratio) else None,
             exposed_A_frac=round(expA_px / s2, 4), exposed_B_frac=round(expB_px / s2, 4), covered=round(covered, 3),
             colour_dE=None if dE is None else round(dE, 1), facing_ok=fok)
    why, bad = [], []
    if r['gap_frac'] > T['gap_fail']:
        bad.append('gap')
    elif r['gap_frac'] > T['gap_warn']:
        why.append('gap')
    # the under part's tab/cut end must stay inside the over part; the over part's own beyond-joint pixels are
    # painted on top (a collar rim, a cuff) and only warn when large
    for nm, v, is_under in (('exposed_A', r['exposed_A_frac'], over == 'B'), ('exposed_B', r['exposed_B_frac'], over == 'A')):
        if is_under and v > T['exp_fail']:
            bad.append(nm)
        elif (is_under and v > T['exp_warn']) or (not is_under and v > T['exp_fail'] * 2):
            why.append(nm)
    if covered > T['cov_fail']:
        bad.append('covered')
    elif covered > T['cov_warn']:
        why.append('covered')
    rt = r['width_ratio']
    if rt is None or not (T['ratio_fail'][0] <= rt <= T['ratio_fail'][1]):
        bad.append('width_step')
    elif not (T['ratio'][0] <= rt <= T['ratio'][1]):
        why.append('width_step')
    if T.get('dE_warn') and dE is not None and dE > T['dE_warn']:
        why.append('colour_jump')
    if fok is False:
        bad.append('facing')
    r['why'] = bad + why
    r['verdict'] = 'MUTILATED' if bad else 'WARN' if why else 'CLEAN'
    # where to circle on a sheet: centroid of the worst failing region
    spot = None
    for nm, msk in (('gap', gap), ('exposed_A', expA), ('exposed_B', expB)):
        if nm in r['why'] and msk.sum():
            ys_, xs_ = np.nonzero(msk)
            spot = [float(xs_.mean()), float(ys_.mean())]
            break
    r['spot'] = spot or ([float(P[0]), float(P[1])] if r['why'] else None)
    return r
