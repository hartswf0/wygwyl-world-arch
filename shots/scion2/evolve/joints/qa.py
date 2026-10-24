"""Seam tests for one connected pair (built to the definitions the coordinator relayed for library2/qa, which did not
exist yet when this was written: gap, width step, exposed cut edge, covered features, colour jump, wrong facing).
All are measured in a band round the joint (radius = max(4 cm, 0.8 x the joint width)). A pair-angle is CLEAN when
every test passes; amber = one test fails; red = two or more.

  gap       paper missing inside the joint: band pixels inside the convex hull of the union (in the band) that
            neither part covers, as a share of that hull; fail > 4%
  width     width step across the joint, cloth-to-cloth joints of the same limb (elbow, knee): union width across
            the child's axis 2.5 cm past the joint vs across the parent's axis 2.5 cm before it; fail > 30%
  exposed   cut ends left showing: the child's end behind the joint (towards the parent) that is not under / inside
            the parent's outline (+0.5 cm), and, when the parent is on top, the parent's end beyond the joint that is
            outside the child; share of that end's area; fail > 30%
  covered   (neck) the torso drawn over the face: share of the head's face box (eye line to chin, ear to ear)
            hidden by the torso; fail > 15%
  colour    (cloth joints) dE (CIE-Lab) between the mean colour of each part within 1.5 cm of the seam; fail > 25
  facing    child and parent facing screen-left vs screen-right (when both are known); fail if opposite
"""
import numpy as np, cv2

from . import connect as CN

TH = {'gap': .04, 'width': .30, 'exposed': .30, 'covered': .15, 'colour': 25., 'facing': .5}


def lab(bgr):
    return cv2.cvtColor(np.clip(bgr, 0, 255).astype(np.uint8).reshape(-1, 1, 3), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32) * [100 / 255., 1, 1] - [0, 128, 128]


def run(r, parent, child, joint, genes):
    RS = CN.RS
    pm, cm, J, uc, up = r['pm'], r['cm'], r['pivot'], r['axis_c'], r['axis_p']
    H, W = pm.shape
    yy, xx = np.mgrid[0:H, 0:W]
    jw = max(CN.width_across(pm.astype(np.uint8) * 255, J - 1.0 * RS * up, up), 1.)
    rad = max(4 * RS, .8 * jw)
    band = (xx - J[0]) ** 2 + (yy - J[1]) ** 2 <= rad ** 2
    U = pm | cm
    out = {}
    # gap
    ub = (U & band).astype(np.uint8)
    cnts, _ = cv2.findContours(ub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts:
        hull = np.zeros_like(ub)
        cv2.fillPoly(hull, [cv2.convexHull(np.vstack(cnts))], 1)
        h = hull > 0
        out['gap'] = float((h & ~U).sum() / max(h.sum(), 1))
        # more than one piece of paper in the band = the parts do not touch
        if len(cnts) > 1 and sorted(cv2.contourArea(c) for c in cnts)[-2] > .05 * ub.sum():
            out['gap'] = max(out['gap'], 1.)
    else:
        out['gap'] = 1.
    # width step (same-limb cloth joints)
    if joint in ('elbow', 'knee'):
        wc = CN.width_across(U.astype(np.uint8) * 255, J + 2.5 * RS * uc, uc)
        wp = CN.width_across(U.astype(np.uint8) * 255, J - 2.5 * RS * up, up)
        out['width'] = float(abs(wc - wp) / max(wc, wp, 1))
    # exposed cut ends
    pd = cv2.dilate(pm.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(RS) | 1,) * 2)) > 0
    behind = ((xx - J[0]) * uc[0] + (yy - J[1]) * uc[1]) < 0
    cend = cm & behind
    e1 = float((cend & ~pd).sum() / max(cend.sum(), 1)) if cend.sum() > 10 else 0.
    e2 = 0.
    if genes.get('on_top') == 'parent':
        beyond = ((xx - J[0]) * up[0] + (yy - J[1]) * up[1]) > 0
        pend = pm & beyond & band
        cd = cv2.dilate(cm.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(RS) | 1,) * 2)) > 0
        e2 = float((pend & ~cd).sum() / max(pend.sum(), 1)) if pend.sum() > 10 else 0.
    out['exposed'] = max(e1, e2)
    # covered features (neck: torso over the face)
    if joint == 'neck' and genes.get('on_top') == 'parent':
        kp = child['kp']
        if 'eye_line' in kp and 'chin' in kp:
            M = r['Mc']
            pts = [kp['eye_line'], kp['chin']] + [kp[k] for k in ('ear_l', 'ear_r') if k in kp]
            P = np.array([M[:, :2] @ np.asarray(p, float) + M[:, 2] for p in pts])
            x0, x1 = P[:, 0].min(), P[:, 0].max()
            if x1 - x0 < 2 * RS:
                x0, x1 = P[0, 0] - 4 * RS, P[0, 0] + 4 * RS
            y0, y1 = min(P[0, 1], P[1, 1]), max(P[0, 1], P[1, 1])
            box = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1) & cm
            out['covered'] = float((box & pm).sum() / max(box.sum(), 1))
    # colour jump (cloth joints)
    if joint in CN.CLOTH:
        dd = (xx - J[0]) ** 2 + (yy - J[1]) ** 2
        near = (dd <= (2.5 * RS) ** 2) & (dd > (1.4 * RS) ** 2)      # the brad itself (1.1 cm) is not cloth
        img = r['img']
        a_ = pm & near & ~cm if genes.get('on_top') == 'child' else pm & near
        b_ = cm & near & ~pm if genes.get('on_top') != 'child' else cm & near
        if a_.sum() > 10 and b_.sum() > 10:
            out['colour'] = float(np.linalg.norm(np.median(lab(img[..., :3][a_]), 0) - np.median(lab(img[..., :3][b_]), 0)))
    # facing
    fc, fp = child.get('facing'), parent.get('facing')
    if fc in ('screen-left', 'screen-right') and fp in ('screen-left', 'screen-right'):
        out['facing'] = float((fc != fp) != bool(r.get('mirror')))
    fails = [k for k, v in out.items() if v > TH[k]]
    return {'tests': {k: round(v, 3) for k, v in out.items()}, 'fails': fails,
            'grade': 'green' if not fails else 'amber' if len(fails) == 1 else 'red', 'band_r': rad}
