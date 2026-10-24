"""Connection methods: connect(parent, child, joint, angle, genes) -> a rendered pair + the geometry the seam tests need.

Joint types: parent part, child part, the parent keypoint the child's pivot goes to, and the child's rest direction.
  neck      torso -> head        torso 'neck'                     head points up
  shoulder  torso -> upper_arm   torso 'shoulder_l' / 'shoulder_r' arm hangs down
  elbow     upper_arm -> forearm upper_arm 'tip'                  down
  wrist     forearm -> hand      forearm 'tip'                    down
  hip       pelvis -> thigh      pelvis 'hip_l' / 'hip_r'         down
  knee      thigh -> shin        thigh 'tip'                      down
  ankle     shin -> foot         shin 'tip'                       foot upright (sole down)
Parts are on library2's canonical grid (10 px/cm); the pair is rendered at RS px/cm. The parent stays in its canonical
pose; the child is turned by `angle` degrees about the joint (its rest direction = the parent's axis continued).

Genes (a method is a dict of them):
  pivot      'kp' (the part's canonical pivot) | 'brad' (the child's brad nearest its pivot, if within 3 cm) |
             'register' (the child's brad placed exactly on the parent's grommet at the joint, when both exist) |
             'midline' (the pivot moved onto the alpha's centre line, across the axis)
  overlap    cm the child's pivot is pushed back past the joint into the parent (0 = pivot on the joint point)
  on_top     'child' | 'parent'
  trim       'none' | 'contour' (the child's end behind the joint is cut away where it leaves the parent's outline)
  width      'none' | 'uniform' (child uniformly scaled 0.85-1.15 so its width at the pivot matches the parent's at
             the joint)
  seam       'none' | 'brad' (a brass brad drawn on top at the joint; brad_r its radius in cm, default 1.1)
  facing     True = mirror the child when its facing (screen-left / right) is the opposite of the parent's
  parent_tab None | cm: the parent's tab / collar / cuff beyond the joint line (towards the child) is cut that far
             past the joint (library2 QA: the torso's neck tab over the chin is the main neck failure)
  tab_shape  'line' (straight cut) | 'round' (keep a rounded lip as wide as the child's neck: no straight collar edge)
"""
import math
import numpy as np, cv2

RS = 4.0                   # render px per cm
J = {'neck': ('torso', 'head', 'neck', 'up'), 'shoulder': ('torso', 'upper_arm', 'shoulder', 'down'),
     'elbow': ('upper_arm', 'forearm', 'elbow', 'down'), 'wrist': ('forearm', 'hand', 'wrist', 'down'),
     'hip': ('pelvis', 'thigh', 'hip', 'down'), 'knee': ('thigh', 'shin', 'knee', 'down'), 'ankle': ('shin', 'foot', 'ankle', 'foot'),
     'waist': ('pelvis', 'torso', 'pivot', 'up')}
CLOTH = {'shoulder', 'elbow', 'hip', 'knee'}


def anchor(parent, joint, side):
    kp = parent['kp']
    name = J[joint][2]
    if name in ('shoulder', 'hip'):
        s = (side or 'R').upper()[0]
        for k in ((name + '_' + s.lower()), name + '_r', name + '_l', name):
            if k in kp:
                return np.asarray(kp[k], float)
        if name == 'hip' and 'pivot' in kp:            # no hip points: 9 cm below the waist, 10 cm to the side
            return kp['pivot'] + [(-1 if s == 'L' else 1) * 100., 90.]
        return None
    for k in (name, 'tip'):                 # library2 names the distal joint (wrist, ankle, ...); on-the-fly parts 'tip'
        if k in kp:
            return np.asarray(kp[k], float)
    return None


def width_across(alpha, p, u, max_px=400):
    """alpha extent (px) across direction u (unit) through p"""
    n = np.array([-u[1], u[0]])
    H, W = alpha.shape
    ext = []
    for sg in (1, -1):
        k = 0
        while k < max_px:
            q = p + sg * (k + 1) * n
            x, y = int(round(q[0])), int(round(q[1]))
            if not (0 <= x < W and 0 <= y < H) or alpha[y, x] < 128:
                break
            k += 1
        ext.append(k)
    return float(sum(ext))


def child_pivot(child, genes):
    piv = np.asarray(child['pivot'], float)
    if genes.get('pivot') == 'brad' and len(child['brads']):
        d = np.linalg.norm(child['brads'] - piv, axis=1)
        if d.min() < 30:
            piv = child['brads'][int(np.argmin(d))]
    elif genes.get('pivot') == 'midline':
        a = child['img'][..., 3]
        row = a[int(np.clip(piv[1] + 20, 0, a.shape[0] - 1))]
        xs = np.nonzero(row > 128)[0]
        if len(xs):
            piv = np.array([(xs.min() + xs.max()) / 2., piv[1]])
    return piv


def brad_sprite(r):
    d = int(2 * r + 3)
    yy, xx = np.mgrid[0:d, 0:d] - (d - 1) / 2.
    rr = np.hypot(xx, yy)
    a = np.clip(r + .5 - rr, 0, 1)
    col = np.zeros((d, d, 3), np.float32)
    col[:] = (40, 150, 205)
    col[rr < r * .55] = (90, 200, 240)
    col[(rr > r * .8)] = (20, 90, 140)
    return np.dstack([col, a * 255]).astype(np.float32)


def over(dst, src):
    a = src[..., 3:] / 255.
    b = dst[..., 3:] / 255.
    oa = a + b * (1 - a)
    rgb = (src[..., :3] * a + dst[..., :3] * b * (1 - a)) / np.maximum(oa, 1e-6)
    return np.dstack([rgb, oa * 255])


def connect(parent, child, joint, angle, genes, side=None):
    """returns a dict: img (BGRA float), pm / cm (alpha masks), pivot (render px), axis_c / axis_p (unit), info"""
    k = RS / 10.
    pa = anchor(parent, joint, side or child.get('side'))
    if pa is None:
        return None
    # parent: canonical pose, scaled to RS
    pimg = parent['img'].astype(np.float32)
    pax = {'torso': (0, -1), 'pelvis': (0, 1), 'upper_arm': (0, 1), 'forearm': (0, 1), 'thigh': (0, 1), 'shin': (0, 1)}[parent['part']]
    rest = J[joint][3]
    base = np.array(pax, float) if rest in ('down',) and parent['part'] not in ('torso', 'pelvis') else \
        (np.array([0, -1.]) if rest == 'up' else np.array([0, 1.]))
    if rest == 'foot':
        base = None
    # child transform: rotate its primary axis onto base, then by angle, about its pivot
    piv_c = child_pivot(child, genes)
    caxis = {'head': (0, -1), 'torso': (0, -1), 'hand': (0, 1), 'upper_arm': (0, 1), 'forearm': (0, 1), 'thigh': (0, 1), 'shin': (0, 1), 'foot': (0, 1)}[child['part']]
    if base is None:
        rot = math.radians(angle) * .5                  # a foot only tilts (half the sweep) about the ankle
        cdir = np.array([0, 1.])
    else:
        rot = math.atan2(base[1], base[0]) - math.atan2(caxis[1], caxis[0]) + math.radians(angle)
        cdir = np.array([math.cos(math.atan2(base[1], base[0]) + math.radians(angle)), math.sin(math.atan2(base[1], base[0]) + math.radians(angle))])
    sc = 1.0
    if genes.get('width') == 'uniform':
        wc = width_across(child['img'][..., 3], piv_c + 20 * np.array(caxis), np.array(caxis, float))
        wp = width_across(parent['img'][..., 3], pa - 20 * np.array(pax, float), np.array(pax, float))
        if wc > 5 and wp > 5 and joint in CLOTH | {'wrist', 'ankle'}:
            sc = float(np.clip(wp / wc, .85, 1.15))
        elif wc > 5 and wp > 5 and joint == 'neck':     # the neck fills the collar opening (collar ~1.3x the neck)
            sc = float(np.clip(wp / (1.3 * wc), .85, 1.15))
    mir = False
    if genes.get('facing') and child.get('facing') in ('screen-left', 'screen-right') and parent.get('facing') in ('screen-left', 'screen-right'):
        mir = child['facing'] != parent['facing']
    # canvas: parent centred
    Hc, Wc = int(parent['img'].shape[0] * k + 260 * k * 2), int(parent['img'].shape[1] * k + 260 * k * 2)
    off = np.array([260 * k, 260 * k])
    Mp = np.array([[k, 0, off[0]], [0, k, off[1]]])
    P = cv2.warpAffine(pimg, Mp, (Wc, Hc), flags=cv2.INTER_AREA, borderValue=0)
    J_r = pa * k + off
    target = J_r - genes.get('overlap', 0.) * RS * cdir      # pushed back into the parent along the child's direction
    # the parent's grommet at this joint (its brad nearest the joint, within 3 cm), in render px
    grom = None
    if len(parent['brads']):
        d = np.linalg.norm(parent['brads'] - pa, axis=1)
        if d.min() < 30:
            grom = parent['brads'][int(np.argmin(d))] * k + off
    cbrad = None
    if len(child['brads']):
        d = np.linalg.norm(child['brads'] - child['pivot'], axis=1)
        if d.min() < 30:
            cbrad = child['brads'][int(np.argmin(d))]
    if genes.get('pivot') == 'register' and grom is not None and cbrad is not None:
        piv_c, target = cbrad, grom              # the child's brad goes exactly onto the parent's grommet
    c, s_ = math.cos(rot), math.sin(rot)
    R = np.array([[c, -s_], [s_, c]]) * k * sc
    if mir:
        R = R @ np.array([[-1, 0], [0, 1.]])
    Mc = np.hstack([R, (target - R @ piv_c)[:, None]])
    C = cv2.warpAffine(child['img'].astype(np.float32), Mc, (Wc, Hc), flags=cv2.INTER_LINEAR, borderValue=0)
    if genes.get('parent_tab') is not None:
        # the parent's tab / collar beyond the joint (towards the child) is cut tab cm past the joint line
        yy, xx = np.mgrid[0:Hc, 0:Wc]
        beyond = ((xx - J_r[0]) * cdir[0] + (yy - J_r[1]) * cdir[1]) > genes['parent_tab'] * RS
        # never beyond the joint region (round 01 critic: a diagonal cut took the torso's shoulder off)
        wcn = width_across(child['img'][..., 3], piv_c, np.array(caxis, float)) * k * sc
        beyond &= (xx - J_r[0]) ** 2 + (yy - J_r[1]) ** 2 <= (max(wcn, 3 * RS) * 1.0) ** 2
        if genes.get('tab_shape') == 'round':
            # a rounded collar lip instead of a straight cut: keep the parent's tab inside a half-disc as wide as the
            # child's neck at the pivot
            wn = width_across(child['img'][..., 3], piv_c, np.array(caxis, float)) * k * sc
            lip = (xx - J_r[0]) ** 2 + (yy - J_r[1]) ** 2 <= (max(wn, 2 * RS) * .55) ** 2
            beyond &= ~lip
        P[..., 3][beyond] = 0
    pm, cm = P[..., 3] > 128, C[..., 3] > 128
    trim_cut = None
    if genes.get('trim') == 'contour':
        yy, xx = np.mgrid[0:Hc, 0:Wc]
        behind = ((xx - J_r[0]) * cdir[0] + (yy - J_r[1]) * cdir[1]) < 0
        behind &= (xx - J_r[0]) ** 2 + (yy - J_r[1]) ** 2 <= (8 * RS) ** 2     # the child's own joint end only
        pd = cv2.dilate(pm.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(RS) | 1, int(RS) | 1))) > 0
        cut = behind & ~pd & (C[..., 3] > 128)
        C[..., 3][cut] = 0
        cm = C[..., 3] > 128
        trim_cut = cut
    else:
        trim_cut = None
    if genes.get('on_top', 'child') == 'child':
        img = over(P, C)
    else:
        img = over(C, P)
    if genes.get('seam') == 'brad':
        r = genes.get('brad_r', 1.1) * RS
        spr = brad_sprite(r)
        if genes.get('pivot') == 'register' and grom is not None:
            J_r = grom                            # the brad is drawn on the registered grommet
        d = spr.shape[0]
        x0, y0 = int(round(J_r[0] - d / 2)), int(round(J_r[1] - d / 2))
        if 0 <= x0 and 0 <= y0 and x0 + d <= Wc and y0 + d <= Hc:
            img[y0:y0 + d, x0:x0 + d] = over(img[y0:y0 + d, x0:x0 + d], spr)
    return {'img': img, 'pm': pm, 'cm': cm, 'pivot': J_r, 'axis_c': cdir, 'axis_p': np.array(pax, float),
            'Mc': Mc, 'Mp': Mp, 'scale': sc, 'mirror': mir, 'trim_cut': trim_cut, 'grommet': grom, 'P': P, 'C': C,
            'child_brad': (Mc[:, :2] @ cbrad + Mc[:, 2]) if cbrad is not None else None}
