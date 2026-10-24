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
  on_top     'child' | 'parent' | 'view' (parent on top for back views, child otherwise)
  trim       'none' | 'contour' (the child's end behind the joint is cut away where it leaves the parent's outline)
  width      'none' | 'uniform' (child uniformly scaled 0.85-1.15 so its width at the pivot matches the parent's at
             the joint)
  seam       ignored from round 06: no brad sprite is drawn (the critic read it as a bare brad); the top piece's own
             painted grommet is the fastener (grommet_rule, side_trim: see the round 06 block in connect())
  rim_trim   True (default): the over part's paper-edge band inside the under part, near the joint, is removed
  facing     True = mirror the child when its facing (screen-left / right) is the opposite of the parent's
  align      True = align the parts' actual keypoint axes at 0 degrees (round 04), else the grid's nominal axes
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


def grommet_radius(img, c, max_r=40):
    """painted radius (canonical px) of the brass grommet ring round c: the farthest brass pixel connected to it"""
    x0, y0 = int(max(0, c[0] - max_r)), int(max(0, c[1] - max_r))
    patch = img[y0:int(c[1] + max_r), x0:int(c[0] + max_r)]
    if patch.size == 0:
        return None
    hsv = cv2.cvtColor(patch[..., :3].astype(np.uint8), cv2.COLOR_BGR2HSV)
    gold = ((hsv[..., 0] >= 12) & (hsv[..., 0] <= 34) & (hsv[..., 1] > 80) & (hsv[..., 2] > 110) & (patch[..., 3] > 128)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(gold)
    if n < 2:
        return None
    cx, cy = c[0] - x0, c[1] - y0
    yy, xx = np.mgrid[0:gold.shape[0], 0:gold.shape[1]]
    best = None
    for i in range(1, n):
        m = lab == i
        d = np.hypot(xx[m] - cx, yy[m] - cy)
        if d.min() < 12 and (best is None or d.max() > best):
            best = float(d.max())
    return best


def round_end(U, c, width, xx, yy, rng=None):
    """round 07 (critic r06: background wedges in the crook of large bends): complete the under piece U (render BGRA,
    in place) to a disc centred on the pivot c, radius half its width at the pivot, the way a cut-out puppet's limb end
    is cut round about its brad. The new paper is painted from U's own pixels: its cloth (sampled > 0.8 cm inside its
    outline, within 5 cm of the pivot) inside, its edge rim (sampled <= 0.45 cm from its outline) in the outer 0.45 cm"""
    if width < 4:
        return 0
    rng = rng or np.random.default_rng(0)
    r = width / 2.
    d2 = (xx - c[0]) ** 2 + (yy - c[1]) ** 2
    um = U[..., 3] > 128
    new = (d2 <= r * r) & ~um
    if not new.any():
        return 0
    dist_in = cv2.distanceTransform(um.astype(np.uint8), cv2.DIST_L2, 3)
    near = d2 <= (5 * RS) ** 2
    cloth = U[..., :3][um & near & (dist_in > .8 * RS)]
    rimpx = U[..., :3][um & near & (dist_in > 0) & (dist_in <= .45 * RS)]
    if len(cloth) < 10:
        return 0
    if len(rimpx) < 10:
        rimpx = cloth
    edge = new & (d2 >= (r - .45 * RS) ** 2)
    inner = new & ~edge
    U[..., :3][inner] = cloth[rng.integers(0, len(cloth), int(inner.sum()))]
    U[..., :3][edge] = rimpx[rng.integers(0, len(rimpx), int(edge.sum()))]
    # soften the sampled noise into a paint texture
    bl = cv2.GaussianBlur(U[..., :3], (5, 5), 0)
    U[..., :3][new] = bl[new]
    U[..., 3][new] = 255
    return int(new.sum())


def drop_islands(L, frac=.02):
    """removes the alpha islands of a render layer smaller than frac of its paper (in place)"""
    m = (L[..., 3] > 128).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n <= 2:
        return
    tot = st[1:, cv2.CC_STAT_AREA].sum()
    small = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] < frac * tot]
    if small:
        L[..., 3][np.isin(lab, small)] = 0
        L[..., 3][(L[..., 3] <= 128) & (cv2.dilate(np.isin(lab, small).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)] = 0


def tab_edge(part, g, axis, max_px=90):
    """canonical px from a grommet g along axis to the first sharp change of paint (|dlum| > 35 against the tab's
    own colour just past the grommet ring), at least 1 cm out; 1.5 cm if none"""
    img = part['img'].astype(np.float32)
    u = np.asarray(axis, float)
    n = np.array([-u[1], u[0]])
    lum = []
    for t in range(0, max_px):
        q = [np.asarray(g, float) + t * u + s * n for s in (-6, -3, 3, 6)]
        v = [img[int(y), int(x), :3].mean() for x, y in q if 0 <= int(x) < img.shape[1] and 0 <= int(y) < img.shape[0] and img[int(y), int(x), 3] > 128]
        lum.append(np.mean(v) if v else np.nan)
    lum = np.array(lum)
    ref = np.nanmedian(lum[9:13]) if np.isfinite(lum[9:13]).any() else np.nan
    for t in range(10, max_px - 3):
        if np.isfinite(ref) and abs(np.nanmean(lum[t:t + 3]) - ref) > 35:
            return float(t)
    return 15.


def cuff_reach(part, g, axis, max_px=120):
    """canonical px from a grommet g along axis to the end of the part's paper"""
    a = part['img'][..., 3]
    u = np.asarray(axis, float)
    for t in range(max_px):
        x, y = np.asarray(g, float) + t * u
        if not (0 <= int(x) < a.shape[1] and 0 <= int(y) < a.shape[0]) or a[int(y), int(x)] <= 128:
            return float(t)
    return float(max_px)


def tab_reach(part, g, axis, max_px=70):
    """how far (canonical px) a part's painted paper tab reaches from its grommet g towards the part's body (against
    axis): the first sharp darkening (tan paper -> skin / hair) at least 1.2 cm from the grommet, else 0.8 cm"""
    img = part['img'].astype(np.float32)
    u = np.asarray(axis, float)                 # the child axis points away from the joint, into the body
    n = np.array([-u[1], u[0]])
    lum = []
    for t in range(0, max_px):
        q = [np.asarray(g, float) + t * u + s * n for s in (-6, -3, 3, 6)]
        v = [img[int(y), int(x), :3].mean() for x, y in q if 0 <= int(x) < img.shape[1] and 0 <= int(y) < img.shape[0] and img[int(y), int(x), 3] > 128]
        lum.append(np.mean(v) if v else np.nan)
    lum = np.array(lum)
    ref = np.nanmedian(lum[12:24]) if np.isfinite(lum[12:24]).any() else np.nan
    for t in range(12, max_px - 3):
        if np.isfinite(ref) and np.nanmean(lum[t:t + 3]) < ref - 35:
            return float(t)
    return 8.


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
    if genes.get('align') and base is not None:
        # round 04 (critic: hands hung sideways): use each part's ACTUAL bone axis from its keypoints, not the grid's
        # nominal one -- the parent's pivot -> joint, the child's pivot -> distal keypoint -- aligned at 0 degrees
        pk, ck = parent['kp'], child['kp']
        if parent['part'] not in ('torso', 'pelvis'):
            v = pa - np.asarray(pk['pivot'], float)
            if np.linalg.norm(v) > 20:
                base = v / np.linalg.norm(v)
        dist = {'hand': ('knuckle_l', 'knuckle_r'), 'head': ('crown',), 'forearm': ('wrist', 'tip'), 'shin': ('ankle', 'tip'),
                'upper_arm': ('elbow', 'tip'), 'thigh': ('knee', 'tip'), 'torso': ('neck',)}.get(child['part'], ())
        q = [np.asarray(ck[k], float) for k in dist if k in ck]
        if child['part'] == 'hand' and len(q) == 2:
            q = [(q[0] + q[1]) / 2]
        elif q:
            q = q[:1]
        if q:
            v = q[0] - np.asarray(child['pivot'], float)
            if np.linalg.norm(v) > 20:
                caxis = tuple(v / np.linalg.norm(v))
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
    if genes.get('mirror'):                   # round 08: mirrored to carry the piping across (piping.py)
        mir = not mir
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
    # round 08 (critic r07 s02: the hand card's square dark tab sits between sleeve and hand): with the hand on top, the
    # hand's tab (from its grommet to the first sharp change of paint towards the fingers) is cut from the card, and
    # the hand moved back so its skin starts 0.3 cm inside the cuff's end; no fastener shows at this wrist
    hand_over = joint == 'wrist' and genes.get('on_top', 'child') == 'child' and genes.get('hand_tab_cut', True) and cbrad is not None
    hand_cut = None
    if hand_over:
        reach = tab_edge(child, cbrad, caxis)
        ys_, xs_ = np.mgrid[0:child['img'].shape[0], 0:child['img'].shape[1]]
        proj = (xs_ - cbrad[0]) * caxis[0] + (ys_ - cbrad[1]) * caxis[1]
        reach += 8.                            # past the tab's own painted rim (about 0.6 cm)
        hand_cut = proj < reach
        cuff = cuff_reach(parent, (grom - off) / k, pax) if grom is not None else 0.
        shift = reach * k * sc - cuff * k + .3 * RS
        if shift > 0:
            target = np.asarray(target, float) - shift * cdir
    neck_back = joint == 'neck' and (child.get('view') or '').startswith(('back', 'three-quarter-back')) and genes.get('side_trim', True)
    r_g = None
    torso_reach = 0.
    if neck_back:
        # round 06 (critic r05: tan neck tabs on back views): the torso's neck grommet sits on the collar edge, and the
        # head's painted nape tab reaches tab_reach above the head's grommet; the head is lowered by that much so its
        # tab and grommet go under the collar (the collar is on top in back views)
        gr0 = grommet_radius(parent['img'], (grom - off) / k) if grom is not None else None
        r_g = (gr0 * k if gr0 else .8 * RS) + .2 * RS
        # the torso's own neck tab: its tan paper runs from the grommet down to the collar edge (torso_reach); that tab
        # is cut (below) and the head lowered by both reaches
        torso_reach = tab_reach(parent, (grom - off) / k, (0, 1)) * k if grom is not None else 0.
        target = np.asarray(target, float) - torso_reach * cdir - (tab_reach(child, cbrad if cbrad is not None else piv_c, caxis) * k + .9 * RS) * cdir
    c, s_ = math.cos(rot), math.sin(rot)
    R = np.array([[c, -s_], [s_, c]]) * k * sc
    if mir:
        R = R @ np.array([[-1, 0], [0, 1.]])
    Mc = np.hstack([R, (target - R @ piv_c)[:, None]])
    cimg = child['img'].astype(np.float32)
    if hand_over:
        # (the cut and the shift were set before the child transform, below)
        cimg = cimg.copy()
        cimg[..., 3][hand_cut] = 0
    C = cv2.warpAffine(cimg, Mc, (Wc, Hc), flags=cv2.INTER_LINEAR, borderValue=0)
    P0m = P[..., 3] > 128
    C0m = C[..., 3] > 128
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
    top = genes.get('on_top', 'child')
    if joint == 'neck' and (child.get('view') or '').startswith(('back', 'three-quarter-back')):
        top = 'view'                           # round 05 (critic r04): back views always put the collar over the head's tab
    if top == 'view':                          # back views: the parent (collar) over the child's tab; else the child over
        top = 'parent' if (child.get('view') or '').startswith(('back', 'three-quarter-back')) else 'child'
    # ---- round 06 (critic r05) ------------------------------------------------------------------------------
    # 1. no drawn brad sprite, ever. The fastener is the TOP piece's own painted grommet, registered over the under
    #    piece's grommet. If the top piece has no grommet at this joint, flip the z-order when the other piece has
    #    one, else the pair is rejected for this method (None). The neck has no fastener in this art and is exempt.
    if genes.get('grommet_rule', True) and joint != 'neck' and not hand_over:
        has = {'child': cbrad is not None, 'parent': grom is not None}
        if not has[top]:
            other = 'parent' if top == 'child' else 'child'
            if not has[other]:
                return None
            top = other
    Ov, Un = (C, P) if top == 'child' else (P, C)
    yy2, xx2 = np.mgrid[0:Hc, 0:Wc]
    if genes.get('round_end') and joint in ('elbow', 'knee'):
        round_end(Un, target, (width_across(parent['img'][..., 3], pa, np.array(pax, float)) * k) if top == 'child' else
                  (width_across(child['img'][..., 3], piv_c, np.array(caxis, float)) * k * sc), xx2, yy2)
    side = (xx2 - target[0]) * cdir[0] + (yy2 - target[1]) * cdir[1]          # > 0: the child's side of the joint
    disk = (xx2 - target[0]) ** 2 + (yy2 - target[1]) ** 2 <= (8 * RS) ** 2
    if genes.get('side_trim', True):
        # 3a. connector tabs: each piece's paper on the OTHER piece's side of the joint line, near the joint, that is
        #     not inside the other piece's silhouette is a tab / ear and is removed (the under piece strictly; the over
        #     piece with 0.2 cm of tolerance so its own painted grommet ring stays whole)
        pm_, cm_ = P[..., 3] > 128, C[..., 3] > 128
        tol = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(.4 * RS) | 1, int(.4 * RS) | 1))
        cmd = cv2.dilate(cm_.astype(np.uint8), tol) > 0 if top == 'parent' else cm_
        pmd = cv2.dilate(pm_.astype(np.uint8), tol) > 0 if top == 'child' else pm_
        # the under piece is trimmed only at the extremity joints (hand ears, boot / collar tabs); at the cloth
        # joints its end is the paper showing inside the bend and trimming it leaves a background notch
        cut_under = joint in ('wrist', 'ankle', 'neck')
        # round 07 (critic r06: a notch at the top of the shoulder): only at the extremity joints; at cloth joints the
        # over piece's rounded end is part of the puppet and cutting it left notches
        if cut_under and not hand_over:         # the parent's paper beyond the joint, outside the child
            P[..., 3][(side > 0) & disk & pm_ & ~cmd] = 0
        if cut_under:                           # the child's paper behind the joint, outside the parent
            C[..., 3][(side < 0) & disk & cm_ & ~pmd] = 0
    if neck_back and top == 'parent' and grom is not None:
        # 3b. the torso's neck tab above the collar edge is cut (the tab and the neck stub round it, 0.75 x the neck width either side; not the shoulders)
        # in the torso's own frame (its up = screen up), not the tilted head's
        side0 = -(yy2 - grom[1])
        lat = np.abs(xx2 - grom[0])
        wcn = width_across(child['img'][..., 3], piv_c, np.array(caxis, float)) * k * sc
        band = lat <= max(.75 * wcn, 1.5 * RS)
        P[..., 3][(side0 > -torso_reach + .1 * RS) & (side0 < 4 * RS) & band] = 0
        # the torso card's notches round its old neck stub, now open below the new collar line, are closed and
        # painted from the collar round them
        zone = (side0 <= -torso_reach + .1 * RS) & (side0 > -torso_reach - 8 * RS) & (lat <= 1.3 * max(.75 * wcn, 1.5 * RS))
        pa_ = P[..., 3] > 128
        # a transparent pixel there with torso paper both to its left and to its right on its row is a notch
        cl = np.cumsum(pa_, axis=1)
        left = cl > 0
        right = (cl[:, -1:] - cl) > 0
        holes = zone & ~pa_ & left & right
        if holes.any():
            bgr = np.clip(P[..., :3], 0, 255).astype(np.uint8)
            P[..., :3] = cv2.inpaint(bgr, holes.astype(np.uint8), 5, cv2.INPAINT_TELEA).astype(np.float32)
            P[..., 3][holes] = 255
    if genes.get('rim_trim', True):
        # 3c. the over piece's painted rim (leopard / tan paper edge, 0.45 cm) wherever it lies over the under piece,
        #     along the whole overlap (round 05 trimmed only within 6 cm of the joint)
        ov_a = (Ov[..., 3] > 128).astype(np.uint8)
        dist = cv2.distanceTransform(ov_a, cv2.DIST_L2, 3)
        rim = (dist > 0) & (dist <= .45 * RS) & (Un[..., 3] > 128)
        # round 07 (critic r06: a dotted light halo along the over piece's edge): its soft fringe (alpha <= 128,
        # outside the mask the band is measured from) lying over the under piece goes too
        rim |= (Ov[..., 3] > 0) & (Ov[..., 3] <= 128) & (Un[..., 3] > 128)
        Ov[..., 3][rim] = 0
    # round 08 (critic r07: beard / ear slivers beside back necks): alpha islands under 2% of a piece are removed
    for L_ in (P, C):
        drop_islands(L_)
    pm, cm = P[..., 3] > 128, C[..., 3] > 128
    # 2. both pieces must be visible: the under piece's share of its own area left uncovered
    un, ov = (Un[..., 3] > 128), (Ov[..., 3] > 128)
    vis = float((un & ~ov).sum()) / max(1, un.sum())
    if top == 'child':
        img = over(P, C)
    else:
        img = over(C, P)
    brad_mask = None
    return {'img': img, 'pm': pm, 'cm': cm, 'pivot': J_r, 'axis_c': cdir, 'axis_p': np.array(pax, float),
            'Mc': Mc, 'Mp': Mp, 'scale': sc, 'mirror': mir, 'trim_cut': trim_cut, 'grommet': grom, 'P': P, 'C': C, 'on_top': top,
            'origP': P0m, 'origC': C0m, 'brad_mask': brad_mask, 'vis_under': vis, 'target': np.asarray(target, float),
            'joint_w': width_across(parent['img'][..., 3], pa - 20 * np.array(pax, float), np.array(pax, float)) * k,
            'child_brad': (Mc[:, :2] @ cbrad + Mc[:, 2]) if cbrad is not None else None}
