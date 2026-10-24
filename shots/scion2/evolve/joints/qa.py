"""Seam tests for one connected pair. run() calls library2/qa/seam.score (the shared definition, ready in round 01);
run_local() is the first version (built to the definitions the coordinator relayed for library2/qa, which did not
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


def run(r, parent, child, joint, genes, angle=None):
    """library2/qa/seam.score (the shared definition); the old local tests stay as run_local"""
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'library2', 'qa')))
    import seam
    feats = []
    if child['part'] == 'head' and 'eye_line' in child['kp'] and 'chin' in child['kp']:
        M = r['Mc']
        kp = child['kp']
        pts = [kp['eye_line'], kp['chin']] + [kp[k] for k in ('ear_l', 'ear_r') if k in kp]
        P = np.array([M[:, :2] @ np.asarray(p, float) + M[:, 2] for p in pts])
        H, W = r['cm'].shape
        yy, xx = np.mgrid[0:H, 0:W]
        x0, x1 = P[:, 0].min(), P[:, 0].max()
        if x1 - x0 < 2 * CN.RS:
            x0, x1 = P[0, 0] - 4 * CN.RS, P[0, 0] + 4 * CN.RS
        y0, y1 = min(P[0, 1], P[1, 1]), max(P[0, 1], P[1, 1])
        feats = [(xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1) & r['cm']]
    img = r['img']
    rgba = np.dstack([img[..., [2, 1, 0]], img[..., 3]]).astype(np.uint8)
    lay = lambda L: np.dstack([L[..., [2, 1, 0]], L[..., 3]]).astype(np.uint8)
    jn = joint if joint in seam.ROM else 'generic'
    # library2 QA round 02: ROM, layers, brad registration, grommet peek, visible tab, trim cut are all seam.py terms now
    overA = r.get('on_top', genes.get('on_top')) == 'parent'
    mA, mB = r['pm'].copy(), r['cm'].copy()
    if r.get('brad_mask') is not None:           # seam.py (87f70e4): the brad sprite belongs to the over part's mask
        if overA:
            mA |= r['brad_mask']
        else:
            mB |= r['brad_mask']
    s = seam.score(rgba, mA, mB, r['pivot'], -r['axis_p'], r['axis_c'], over='A' if overA else 'B', origA=r.get('origP'), origB=r.get('origC'),
                   featuresA=None, featuresB=feats,
                   facingA=(parent.get('view'), parent.get('facing')) if parent.get('view') and parent.get('facing') else None,
                   facingB=(child.get('view'), child.get('facing')) if child.get('view') and child.get('facing') else None,
                   joint=jn, angle=angle, layerA=lay(r['P']), layerB=lay(r['C']),
                   bradA=None if r.get('grommet') is None else [float(v) for v in r['grommet']],
                   bradB=None if r.get('child_brad') is None else [float(v) for v in r['child_brad']], px_per_cm=CN.RS)
    if s['verdict'] == 'N/A':
        return None
    grade = {'CLEAN': 'green', 'WARN': 'amber', 'MUTILATED': 'red'}[s['verdict']]
    tests = {k: (round(float(v), 3) if isinstance(v, (int, float, np.floating)) else v) for k, v in s.items() if k in
             ('gap_frac', 'width_ratio', 'exposed_A_frac', 'exposed_B_frac', 'covered', 'colour_dE', 'facing_ok',
              'registration_cm', 'grommet_peek', 'tab_visible_frac', 'trim_cut')}
    why = s.get('why') or []
    if isinstance(why, str):
        why = [why]
    seam_w = float(s.get('seam_w', 40))
    return {'tests': tests, 'fails': [str(w).split(' ')[0].split(':')[0] for w in why] if grade != 'green' else [],
            'grade': grade, 'band_r': max(.9 * seam_w, 3 * CN.RS), 'verdict': s['verdict'], 'spot': s.get('spot')}


def run_local(r, parent, child, joint, genes):
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
