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
  0.1 seam_w inside it); width_ratio = width_B / width_A. The step test is ORDER-FREE: width_step_ratio =
  larger / smaller is compared with TOL[joint]['ratio'] (warn) and ['ratio_fail'] (fail), given as (1, max). Neck:
  a collar may be up to 2.4x the neck before it warns, 3.2x before it fails.
- gap ignores holes painted inside one part (eyelet holes, a hollow chest).
- exposed_A_frac, exposed_B_frac: pixels of a part lying beyond the joint (on the other part's side, i.e. its
  overlap tab or cut end) and outside the other part's silhouette. These are cut edges or tabs showing; fraction of
  seam_w^2. In the verdict the UNDER part's exposure counts fully. The over part's beyond-joint pixels are painted
  on top (a collar rim, a cuff), so they only warn when they pass 2x the fail level.
- covered: the largest fraction of an under-part feature hidden by the over part.
- colour_dE: CIE76 delta-E between the median colours on either side of the visible seam contour.
- facing_ok: bool or None.
- seam_w: the cross-section width used as the unit: the smaller of the two parts' widths at the pivot.
- trim_cut: the longest NEW straight run on the visible outline near the joint, / seam_w. It warns above 0.6 and
  fails above 1.0. A run counts when:
  - it is straight within 0.6 px;
  - its midpoint lies within 1 seam_w of the joint along the bone;
  - less than 70 % of it lies on either part's own untrimmed outline (origA/origB, default = the masks). An edge
    that was already on the painted card is never a trim cut.
- light_rim: the fraction of the over part's soft edge, inside the joint disk, that is near-white (L* > 85) and more
  than 60 L* lighter than the under part beneath it (a card-background halo; the kit's painted brown card edge does
  not count). It warns above 0.25. Library images are defringed, so
  this should stay 0 for library parts.
- registration_cm: the distance between the child's brad and the parent's grommet. It needs bradA/bradB, and
  warns above 0.3 cm and fails above 0.6 cm.
- grommet_peek: the under part's grommet at this joint (its brass component nearest the pivot, as its painted
  ring) and the fraction of that ring still brass in the FINAL composite outside the over part. A brad drawn over
  it is part of the over part's mask and hides it. Between 8 % and 92 % visible (a half grommet) it warns. It needs
  the layers.
- tab_visible_frac: the over part's beyond-joint pixels that are tab material (light cardboard or skin, not dark
  cloth or brass) outside the under part, / seam_w^2. It uses the exposed thresholds.
- angle + ROM: outside ROM[joint] the verdict is 'N/A' (out_of_rom) and nothing is judged.
"""
import math, os, sys
import numpy as np
import cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import detect as DT  # noqa: E402

# per joint tolerances; the joint lab may override any of these
TOL = {
    'generic': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.08, cov_fail=0.25,
                    ratio=(1.0, 1.67), ratio_fail=(1.0, 2.5), dE_warn=None),
    # neck: a neck going into a collar is expected to step out (collar wider than neck)
    'neck': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.08, cov_fail=0.25,
                 ratio=(1.0, 2.4), ratio_fail=(1.0, 3.2), dE_warn=None),
    'wrist': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.1, cov_fail=0.3,
                  ratio=(1.0, 2.0), ratio_fail=(1.0, 3.0), dE_warn=None),
    'ankle': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.1, cov_fail=0.3,
                  ratio=(1.0, 2.5), ratio_fail=(1.0, 4.0), dE_warn=None),
    'elbow': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.1, cov_fail=0.3,
                  ratio=(1.0, 1.43), ratio_fail=(1.0, 2.0), dE_warn=18),
    'knee': dict(gap_warn=0.01, gap_fail=0.04, exp_warn=0.06, exp_fail=0.18, cov_warn=0.1, cov_fail=0.3,
                 ratio=(1.0, 1.43), ratio_fail=(1.0, 2.0), dE_warn=18),
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


# range of motion per joint, degrees of the child's rotation away from the neutral (straight) pose, + = ccw on
# screen. Angles outside it are not judged (verdict 'N/A'). Elbow/knee: 0..150 of flexion; flexion is taken as
# either rotation direction because a profile limb can face either way.
ROM = {'neck': (-35, 35), 'wrist': (-70, 70), 'ankle': (-30, 45), 'elbow': (0, 150), 'knee': (0, 150),
       'shoulder': (-60, 180), 'hip': (-30, 125), 'waist': (-30, 90), 'generic': (-180, 180)}


def in_rom(joint, angle):
    if angle is None:
        return True
    lo, hi = ROM.get(joint, ROM['generic'])
    if joint in ('elbow', 'knee'):
        return lo <= abs(angle) <= hi
    return lo <= angle <= hi


def brass_mask(rgba):
    """brass brads / grommets by colour (as tools/brass.py)"""
    hsv = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2HSV)
    h, s_, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    return (h >= 17) & (h <= 32) & (s_ >= 90) & (v >= 105) & (rgba[..., 3] > 128)


def _on_outline(a, b, outline, tol=1.5):
    """fraction of the segment a-b that lies on a given outline mask (within tol px)"""
    if outline is None:
        return 0.0
    n = max(2, int(np.linalg.norm(b - a)))
    H, W = outline.shape
    hit = 0
    for t in np.linspace(0, 1, n):
        x, y = (a + (b - a) * t).round().astype(int)
        if 0 <= x < W and 0 <= y < H and outline[y, x]:
            hit += 1
    return hit / n


def _straight_runs(mask, centre, radius, min_len, axis=None, along=None):
    """straight segments of the outline of mask within radius of centre (scissor cuts); with axis, only those whose
    midpoint lies within `along` of the centre measured along the bone axis"""
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cs:
        if len(c) < 20:
            continue
        poly = cv2.approxPolyDP(c, 0.6, True)[:, 0, :].astype(float)
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            L = float(np.linalg.norm(b - a))
            mid = (a + b) / 2
            if L < min_len or np.linalg.norm(mid - centre) > radius:
                continue
            if axis is not None and along is not None and abs(float(np.dot(mid - centre, axis))) > along:
                continue
            out.append((a, b, L))
    return out


def score(render_rgba, maskA, maskB, pivot, axisA, axisB, over='A', featuresA=None, featuresB=None,
          facingA=None, facingB=None, joint='generic', tol=None, angle=None, layerA=None, layerB=None,
          bradA=None, bradB=None, px_per_cm=10.0, origA=None, origB=None):
    """see the module docstring. New (round 02): angle (deg, for the ROM table), layerA/layerB (each part's own RGBA
    as placed, for brass and tab tests), bradA/bradB (the brad / grommet centre each part brings to this joint,
    render px; None if the part has none), px_per_cm (render scale), origA/origB (each part's UNTRIMMED silhouette
    as placed: pass them when a joint method trims a part; when omitted the masks are taken as untrimmed)."""
    T = dict(TOL.get(joint, TOL['generic']))
    if tol:
        T.update(tol)
    if not in_rom(joint, angle):
        return {'verdict': 'N/A', 'why': ['out_of_rom'], 'angle': angle, 'rom': ROM.get(joint), 'spot': None}
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
    # trim cuts: long straight runs on the VISIBLE outline (the union) near the seam
    # (a) only near the joint along the bone (a sleeve's long painted side well above the joint is not a cut);
    # (b) only edges NEW to the part: a straight run lying on a part's own untrimmed card outline was painted that way
    axis_mean = uA - uB
    axis_mean = axis_mean / (np.linalg.norm(axis_mean) or 1)
    runs = _straight_runs(U, P, 1.6 * seam_w, max(6.0, T.get('trim_min', 0.35) * seam_w), axis=axis_mean, along=1.0 * seam_w)
    k3 = np.ones((3, 3), np.uint8)
    edge = lambda m_: (m_ & ~cv2.erode(m_.astype(np.uint8), k3).astype(bool)) if m_ is not None else None
    oA = edge(origA if origA is not None else maskA)
    oB = edge(origB if origB is not None else maskB)
    oAB = cv2.dilate((oA | oB).astype(np.uint8), k3).astype(bool)
    runs = [(a, b, L) for a, b, L in runs if _on_outline(a, b, oAB) < 0.7]
    trim_len = max([L for _, _, L in runs] or [0.0])
    trim_spot = None
    if runs:
        a, b, L = max(runs, key=lambda t: t[2])
        trim_spot = [float((a[0] + b[0]) / 2), float((a[1] + b[1]) / 2)]
    # brad-on-grommet registration and half-grommet peeking
    reg_cm = None
    if bradA is not None and bradB is not None:
        reg_cm = float(np.linalg.norm(np.array(bradA, float) - np.array(bradB, float)) / px_per_cm)
    peek = None
    over_mask_ = maskA if over == 'A' else maskB
    under_layer = layerB if over == 'A' else layerA
    if under_layer is not None:
        # the under part's grommet AT this joint: the brass component of its layer nearest the pivot, as its own
        # painted ring (filled disc of the component's radius). Peek = brass still visible in the FINAL composite
        # inside that ring, outside the over part (a brad drawn over it is part of the over part's mask).
        bm = (brass_mask(under_layer) & disk).astype(np.uint8)
        n_, lab_, st_, cen_ = cv2.connectedComponentsWithStats(bm, 8)
        if n_ > 1:
            i_ = 1 + int(np.argmin([np.hypot(cen_[i][0] - P[0], cen_[i][1] - P[1]) for i in range(1, n_)]))
            if st_[i_, 4] > 15:
                rr = 0.5 * max(st_[i_, 2], st_[i_, 3])
                ring = np.zeros_like(bm)
                cv2.circle(ring, (int(round(cen_[i_][0])), int(round(cen_[i_][1]))), int(round(rr)), 1, -1)
                ring = ring.astype(bool) & (lab_ == i_)
                vis = ring & brass_mask(render_rgba) & ~over_mask_
                peek = round(float(vis.sum() / max(1, ring.sum())), 3)
    # visible connector tab: the over part's beyond-joint pixels outside the under part that are tab material
    # (light cardboard / skin, not dark cloth)
    over_layer = layerA if over == 'A' else layerB
    tab_vis = None
    if over_layer is not None:
        beyond_over = expA if over == 'A' else expB
        hsv = cv2.cvtColor(over_layer[..., :3], cv2.COLOR_RGB2HSV)
        tabby = beyond_over & (hsv[..., 2] > 80) & ~brass_mask(over_layer)
        tab_vis = round(float(er(tabby).sum() / s2), 4)
    # light rim: the over part's soft edge (semi-transparent pixels) inside the joint disk that is much lighter than
    # what lies under it (card-background fringe over a dark partner)
    rim = None
    if over_layer is not None and under_layer is not None:
        oa = over_layer[..., 3].astype(int)
        band = (oa > 15) & (oa < 240) & disk & under_mask
        if band.sum() > 20:
            Lo = cv2.cvtColor(over_layer[..., :3], cv2.COLOR_RGB2LAB)[..., 0].astype(int)
            Lu = cv2.cvtColor(under_layer[..., :3], cv2.COLOR_RGB2LAB)[..., 0].astype(int)
            rim = round(float((((Lo - Lu) > 60 * 255 / 100) & (Lo > 85 * 255 / 100))[band].mean()), 3)     # cv2 L is 0..255
    r = dict(seam_w=round(seam_w, 1), gap_px=gap_px, gap_frac=round(gap_px / s2, 4), width_A=round(wA, 1), width_B=round(wB, 1),
             width_ratio=round(ratio, 3) if math.isfinite(ratio) else None,
             exposed_A_frac=round(expA_px / s2, 4), exposed_B_frac=round(expB_px / s2, 4), covered=round(covered, 3),
             colour_dE=None if dE is None else round(dE, 1), facing_ok=fok,
             trim_cut=round(trim_len / seam_w, 3), registration_cm=None if reg_cm is None else round(reg_cm, 2),
             grommet_peek=peek, tab_visible_frac=tab_vis, light_rim=rim, angle=angle)
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
    # the step is order-free: the larger joint end over the smaller (callers pass child/parent in either order)
    rt = None if (r['width_ratio'] is None or r['width_ratio'] <= 0) else max(r['width_ratio'], 1.0 / r['width_ratio'])
    r['width_step_ratio'] = None if rt is None else round(rt, 3)
    if rt is None or not (T['ratio_fail'][0] <= rt <= T['ratio_fail'][1]):
        bad.append('width_step')
    elif not (T['ratio'][0] <= rt <= T['ratio'][1]):
        why.append('width_step')
    if T.get('dE_warn') and dE is not None and dE > T['dE_warn']:
        why.append('colour_jump')
    if fok is False:
        bad.append('facing')
    if r['trim_cut'] > T.get('trim_fail', 1.0):
        bad.append('trim_cut')
    elif r['trim_cut'] > T.get('trim_warn', 0.6):
        why.append('trim_cut')
    if reg_cm is not None and reg_cm > T.get('reg_fail', 0.6):
        bad.append('registration')
    elif reg_cm is not None and reg_cm > T.get('reg_warn', 0.3):
        why.append('registration')
    if peek is not None and 0.08 < peek < 0.92:
        why.append('grommet_peek')
    if rim is not None and rim > 0.25:
        why.append('light_rim')
    if tab_vis is not None and tab_vis > T['exp_fail']:
        bad.append('tab_visible')
    elif tab_vis is not None and tab_vis > T['exp_warn']:
        why.append('tab_visible')
    # ---- round 04: detectors that measure the DRAWN result (qa/detect.py), validated against the blind critic's
    # named defects (qa/validation/report.json). They replace the old tab_visible / light_rim / grommet_peek /
    # colour_jump verdict terms (still reported above, as diagnostics).
    for t in ('tab_visible', 'light_rim', 'grommet_peek', 'colour_jump', 'registration'):
        if t in why:
            why.remove(t)
        if t in bad:
            bad.remove(t)
    if layerA is not None and layerB is not None:
        comp = render_rgba[..., :3]
        if render_rgba.shape[-1] == 4:
            al = render_rgba[..., 3:] / 255.0
            comp = (render_rgba[..., :3] * al + 245 * (1 - al)).astype(np.uint8)
        overp = 'child' if over == 'A' else 'parent'     # convention here: A = child, B = parent (pairs.py)
        mC_, mP_ = maskA, maskB
        tab_cm2, tspot = DT.tab_visible(comp, mP_, mC_, P, uB, uA, overp, px_per_cm)
        rim2, rspot = DT.light_rim(comp, mP_, mC_, P, overp, px_per_cm)
        g = DT.grommet(comp, layerB, layerA, P, px_per_cm)
        col = DT.colour_mismatch(comp, mP_, mC_, P, overp, px_per_cm)
        r.update(tab_cm2=round(tab_cm2, 2), light_rim2=round(rim2, 3), registration2_cm=g['registration_cm'], crescent_cm=g['crescent_cm'],
                 bare_brad=g['bare_brad'], grommet_peek2=g['peek_frac'], colour_dE2=None if col is None else round(col, 1))
        if tab_cm2 > T.get('tab_cm2', 9.2):
            why.append('tab_visible')
        if rim2 > T.get('rim2', 0.055):
            why.append('light_rim')
        reg = g['registration_cm'] or 0.0
        if reg > T.get('reg2_fail', 1.0) or g['bare_brad']:
            bad.append('registration')
        elif g['crescent_cm'] > T.get('crescent', 0.74) or g['peek_frac'] is not None:
            why.append('grommet')
        if col is not None and col > T.get('colour2', 15.0):
            why.append('colour_jump')
        r['spot'] = None
        for nm, sp in (('tab_visible', tspot), ('light_rim', rspot), ('grommet', g['spot']), ('registration', g['spot'])):
            if nm in why + bad and sp:
                r['spot'] = sp
                break
    r['why'] = bad + why
    r['verdict'] = 'MUTILATED' if bad else 'WARN' if why else 'CLEAN'
    # where to circle on a sheet: centroid of the worst failing region
    spot = r.get('spot')
    for nm, msk in (('gap', gap), ('exposed_A', expA), ('exposed_B', expB)):
        if nm in r['why'] and msk.sum():
            ys_, xs_ = np.nonzero(msk)
            spot = [float(xs_.mean()), float(ys_.mean())]
            break
    if spot is None and 'trim_cut' in r['why']:
        spot = trim_spot
    r['spot'] = spot or ([float(P[0]), float(P[1])] if r['why'] else None)
    return r
