"""Automatic layer cut of any painting that has Pose Lab markers (no hand-drawn polygons).

Used for posture masters (kneel, sit, lie) and as the first rig of a new character.
Returns the same spec dict as a hand-made builder in chars/<char>.py:
  joints, layers (back -> front), border, fig, brads

How:
  * joints from the markers (hand tip and toe extrapolated when missing);
  * every figure pixel is given to the nearest body part (arm, leg, head, torso) by distance
    to the marker bone segments, arms only within an arm's width of their bones;
  * the arm that covers more of the torso is the near arm (drawn in front); the other is
    drawn behind the torso;
  * the torso is completed under the arms (a quad between shoulders and hips, inpainted from
    the painting's own plain fabric), the trousers under the jacket hem the same way;
  * brads are found as round brass blobs and assigned to the nearest joint.
"""
import math
import numpy as np, cv2

from . import core


def _P(m, k):
    return np.array(m[k][:2], float)


def seg_d(xx, yy, a, b):
    ab = b - a
    L2 = float(ab @ ab) + 1e-9
    t = np.clip(((xx - a[0]) * ab[0] + (yy - a[1]) * ab[1]) / L2, 0, 1)
    return np.hypot(xx - (a[0] + t * ab[0]), yy - (a[1] + t * ab[1]))


def plain_fabric(rgb, fig, er=7):
    b, g, r = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    dark = (r < 70) & (g < 70) & (b < 70) & (r < g + 25)
    return dark & (cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0)


def inpaint(rgb, fill, known, r=7):
    img = rgb.copy()
    m = (~known).astype(np.uint8) * 255
    src = np.clip(img, 0, 255).astype(np.uint8)
    src[~known] = 0
    out = cv2.inpaint(src, m, r, cv2.INPAINT_TELEA).astype(np.float32)
    img[fill] = out[fill]
    return img


def find_brads(rgb, fig, T):
    b, g, r = [rgb[..., i].astype(int) for i in range(3)]
    gold = (r > 140) & (g > 95) & (b < 130) & (r - b > 60) & fig
    gold = cv2.morphologyEx(gold.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    ff = gold.copy(); m = np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8)
    cv2.floodFill(ff, m, (0, 0), 1)
    filled = gold | (1 - ff)
    n, lab, st, c = cv2.connectedComponentsWithStats(filled)
    out = []
    for i in range(1, n):
        x, y, w, h, A = st[i]
        if A < 0.002 * T * T or max(w, h) > 0.2 * T or min(w, h) < 0.4 * max(w, h):
            continue
        if A / (w * h) < 0.45:
            continue
        out.append((float(c[i][0]), float(c[i][1]), 0.5 * (w + h) / 2))
    return out


def build_auto(rgb, a, markers, cls=None, plain_fn=None, torso_over_legs=True):
    """plain_fn(rgb, fig) -> mask of plain cloth to fill hidden areas from (default: the poet's black fabric)"""
    H, W = a.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    fig = a > 0.5
    n, lab, st, _ = cv2.connectedComponentsWithStats(fig.astype(np.uint8))
    fig = lab == (1 + np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = markers
    # a costume emblem painted on the master (the poet.04 chest disc) is erased: it is a part
    b_, g_, r_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    blue = (b_ > 140) & (b_ > r_ + 60) & fig
    if blue.sum() > 20:
        ys, xs = np.nonzero(blue)
        cx, cy = xs.mean(), ys.mean()
        rr = 1.9 * math.sqrt(blue.sum() / math.pi) + 3
        disc = (xx - cx) ** 2 + (yy - cy) ** 2 <= rr * rr
        ring = ((xx - cx) ** 2 + (yy - cy) ** 2 <= (rr + 8) ** 2) & ~disc & plain_fabric(rgb, fig, 3)
        rgb = inpaint(rgb, disc, ring, 6)
    J = {}
    for S in 'RL':
        J['sh' + S] = _P(m, 'shoulder' + S); J['el' + S] = _P(m, 'elbow' + S); J['wr' + S] = _P(m, 'wrist' + S)
        J['hip' + S] = _P(m, 'hip' + S); J['kn' + S] = _P(m, 'knee' + S); J['an' + S] = _P(m, 'ankle' + S)
    J['neck'] = _P(m, 'neck'); J['midhip'] = (J['hipR'] + J['hipL']) / 2
    T = float(np.linalg.norm(J['neck'] - J['midhip']))
    up = (J['neck'] - J['midhip']) / T
    J['waist'] = J['midhip'] + 0.35 * T * up
    J['crotch'] = _P(m, 'groin') if 'groin' in m else J['midhip'] - 0.15 * T * up
    if np.linalg.norm(J['crotch'] - J['midhip']) < 0.08 * T:
        J['crotch'] = J['midhip'] - 0.15 * T * up
    ch = _P(m, 'chin'); hd = _P(m, 'head')
    J['headpiv'] = J['neck'] + 0.55 * (ch - J['neck'])
    J['collar'] = J['headpiv'].copy()
    J['headtop'] = hd if np.linalg.norm(hd - J['headpiv']) > 0.2 * T else J['headpiv'] + 0.5 * T * up
    for S in 'RL':
        f = J['wr' + S] - J['el' + S]
        f = f / (np.linalg.norm(f) + 1e-6)
        J['tip' + S] = J['wr' + S] + 0.22 * T * f
        toe = m.get('toe' + S)
        if toe and toe[4] >= 0.35 and np.linalg.norm(np.array(toe[:2]) - J['an' + S]) > 0.1 * T:
            J['to' + S] = np.array(toe[:2], float)
        else:
            sh = J['an' + S] - J['kn' + S]; sh /= np.linalg.norm(sh) + 1e-6
            facing = 1.0 if ch[0] >= J['neck'][0] else -1.0
            J['to' + S] = J['an' + S] + 0.3 * T * np.array([facing, 0.0]) + 0.05 * T * sh
    # ---------------------------------------------------------------- part masks
    rA, rL = 0.16 * T, 0.17 * T
    dArm = {S: np.minimum.reduce([seg_d(xx, yy, J['sh' + S], J['el' + S]), seg_d(xx, yy, J['el' + S], J['wr' + S]),
                                  seg_d(xx, yy, J['wr' + S], J['tip' + S])]) for S in 'RL'}
    dLeg = {S: np.minimum.reduce([seg_d(xx, yy, J['hip' + S], J['kn' + S]), seg_d(xx, yy, J['kn' + S], J['an' + S]),
                                  seg_d(xx, yy, J['an' + S], J['to' + S])]) for S in 'RL'}
    quad = np.array([J['shR'], J['shL'], J['hipL'], J['hipR']], np.float32)
    cq = quad.mean(0)
    quad_e = (cq + (quad - cq) * 1.12).astype(np.int32)
    torso_q = np.zeros((H, W), np.uint8); cv2.fillPoly(torso_q, [quad_e], 1); torso_q = torso_q > 0
    dTor = seg_d(xx, yy, J['midhip'], J['neck'])
    # head window (as in parts.cut_auto)
    a_ = ch - J['neck']
    ax = up * 0.5 + (a_ / (np.linalg.norm(a_) + 1e-6)) * 0.5; ax /= np.linalg.norm(ax)
    rel_h = (xx - J['neck'][0]) * ax[0] + (yy - J['neck'][1]) * ax[1]
    nrm = np.array([-ax[1], ax[0]])
    perp = (xx - J['neck'][0]) * nrm[0] + (yy - J['neck'][1]) * nrm[1] - float((ch - J['neck']) @ nrm)
    s0 = 0.20 * T
    half = np.clip(0.18 * T + (rel_h - s0) * 0.9, 0.18 * T, 0.42 * T)
    head = fig & (rel_h > s0) & (rel_h < s0 + 0.85 * T) & (np.abs(perp) < half)
    arm = {}
    for S in 'RL':
        other = 'L' if S == 'R' else 'R'
        arm[S] = fig & ~head & (dArm[S] < rA) & (dArm[S] <= dArm[other]) & ((dArm[S] < 0.6 * dTor) | ~torso_q | (dArm[S] < 0.1 * T))
        # do not take the shoulder top: within 0.12T of the shoulder joint and inward of it is jacket
        inward = ((xx - J['sh' + S][0]) * (J['neck'][0] - J['sh' + S][0]) + (yy - J['sh' + S][1]) * (J['neck'][1] - J['sh' + S][1])) > 0
        arm[S] &= ~(inward & (np.hypot(xx - J['sh' + S][0], yy - J['sh' + S][1]) < 0.14 * T))
        n_, lab_, st_, _ = cv2.connectedComponentsWithStats(arm[S].astype(np.uint8))
        if n_ > 1:
            # keep the components touching the arm bones closely
            keep = np.zeros_like(arm[S])
            for i in range(1, n_):
                comp = lab_ == i
                if dArm[S][comp].min() < 0.05 * T:
                    keep |= comp
            arm[S] = keep
    legs_vis = fig & ~head & ~arm['R'] & ~arm['L'] & ((np.minimum(dLeg['R'], dLeg['L']) < rL) |
                                                       (((xx - J['midhip'][0]) * up[0] + (yy - J['midhip'][1]) * up[1]) < -0.05 * T))
    torso_vis = fig & ~head & ~arm['R'] & ~arm['L'] & ~legs_vis
    n_, lab_, st_, _ = cv2.connectedComponentsWithStats(torso_vis.astype(np.uint8))
    if n_ > 1:      # stray bits (a prop, a far hand) are not jacket
        torso_vis = lab_ == (1 + np.argmax(st_[1:, cv2.CC_STAT_AREA]))
    # near / far arm: the one that overlaps the torso quad more is in front
    cover = {S: float((arm[S] & torso_q).sum()) for S in 'RL'}
    near = 'R' if cover['R'] >= cover['L'] else 'L'
    far = 'L' if near == 'R' else 'R'
    # completion
    plain = (plain_fn or plain_fabric)(rgb, fig)
    below = ((xx - J['midhip'][0]) * up[0] + (yy - J['midhip'][1]) * up[1]) < 0.02 * T
    torso_m = (torso_vis | torso_q) & ~(legs_vis & below) & ~(head & (rel_h > s0 + 3))
    if not torso_over_legs:     # the filled torso stops at the jacket hem: no fill over the trousers' waist
        torso_m &= ~legs_vis
    torso_rgb = inpaint(rgb, torso_m & ~torso_vis, torso_vis & plain)
    waist_q = np.array([J['hipR'] + 0.25 * T * up, J['hipL'] + 0.25 * T * up, J['hipL'], J['hipR']], np.float32)
    cw = waist_q.mean(0)
    wq = np.zeros((H, W), np.uint8); cv2.fillPoly(wq, [(cw + (waist_q - cw) * 1.1).astype(np.int32)], 1)
    legs_m = legs_vis | (wq > 0)
    legs_rgb = inpaint(rgb, legs_m & ~legs_vis, legs_vis & plain)

    def fade_root(al, S):
        d = np.hypot(xx - J['sh' + S][0], yy - J['sh' + S][1])
        inward = ((xx - J['sh' + S][0]) * (J['neck'][0] - J['sh' + S][0]) + (yy - J['sh' + S][1]) * (J['neck'][1] - J['sh' + S][1])) > 0
        f = np.clip((d - 0.08 * T) / (0.08 * T), 0, 1)
        seam = inward & (d < 0.16 * T) & (al > 0)
        return np.where(seam, al * f, al), seam

    aN, seamN = fade_root(arm[near].astype(np.float32), near)
    aF = arm[far].astype(np.float32)
    seat_line = rel_h < s0 + 4
    head_a = head.astype(np.float32) * np.clip((rel_h - s0) / 3, 0, 1)
    ones = np.ones((H, W), np.float32)
    legs_top = ((xx - J['midhip'][0]) * up[0] + (yy - J['midhip'][1]) * up[1]) > 0.05 * T

    def arm_layer(S, al, seam):
        hx, hy = J['wr' + S]
        f = J['wr' + S] - J['el' + S]; f = f / (np.linalg.norm(f) + 1e-6)
        return dict(name='arm' + S, rgb=rgb.copy(), alpha=al, edgeok=(~seam).astype(np.float32) if seam is not None else ones,
                    bones={'chest': [('neck', 'sh' + S)], 'uarm' + S: [('sh' + S, 'el' + S)], 'farm' + S: [('el' + S, 'wr' + S)],
                           'hand' + S: [('wr' + S, 'tip' + S)]},
                    tau=0.025 * T, hand={S: (float(hx), float(hy), float(-f[0]), float(-f[1]))}, side=S)

    layers = [
        arm_layer(far, aF, None),
        dict(name='legs', rgb=legs_rgb, alpha=legs_m.astype(np.float32), edgeok=(~((wq > 0) & ~legs_vis)).astype(np.float32),
             bones={'pelvis': [('waist', 'crotch'), ('hipR', 'hipL')], 'thighR': [('hipR', 'knR')], 'shinR': [('knR', 'anR')],
                    'footR': [('anR', 'toR')], 'thighL': [('hipL', 'knL')], 'shinL': [('knL', 'anL')], 'footL': [('anL', 'toL')]},
             tau=0.03 * T),
        dict(name='torso', rgb=torso_rgb, alpha=torso_m.astype(np.float32), edgeok=ones, bones='torso',
             torso=dict(p1=(J['midhip'] + 0.6 * T * up).tolist(), p0=(J['midhip'] + 0.1 * T * up).tolist(),
                        caps=[('sh' + near, 'uarm' + near)], cx=float(J['neck'][0]))),
        dict(name='head', rgb=rgb.copy(), alpha=head_a, edgeok=(~seat_line).astype(np.float32), bones={'head': [('headpiv', 'headtop')]},
             tau=1.0, is_head=True),
        arm_layer(near, aN, seamN),
    ]
    # brads
    brads = []
    jl = {'sh': ('uarm', 'arm'), 'el': ('farm', 'arm'), 'hip': ('thigh', 'legs'), 'kn': ('shin', 'legs'), 'an': ('foot', 'legs')}
    for (bx, by, br) in find_brads(rgb, fig, T):
        best, bd = None, 0.13 * T
        for j, (bone, lay) in jl.items():
            for S in 'RL':
                d = np.hypot(bx - J[j + S][0], by - J[j + S][1])
                if d < bd:
                    best, bd = (j + S, bone + S, lay + S if lay == 'arm' else lay), d
        if best:
            jn, bone, lay = best
            if jn.startswith('sh') and lay == 'arm' + far:
                lay, bone = 'torso', 'chest'
            brads.append((jn, lay, bone, bx, by, max(br, 0.04 * T), max(br * 1.5, 0.07 * T)))
    J = {k: tuple(float(x) for x in v) for k, v in J.items()}
    return dict(joints=J, layers=layers, border=3.5, fig=fig, brads=brads, T=T)
