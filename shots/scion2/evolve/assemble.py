"""Genome -> placed library cards on the target skeleton -> pixels.

Target  (target(char, tid)):  the Pose Lab markers of one painting; s (px per card-cm) fitted from the least-foreshortened
         bones; the painting itself is loaded only as REFERENCE (its alpha for silhouette overlap, its pixels for the
         copy check) and is never drawn.
Genome  {'view': v, 'parts': {key: {'id', 'k', 'rot', 'mir'}}}; keys = KEYS (pelvis may be None = no hip piece).
Placing (place):  forward kinematics on the target's markers, card joint to joint:
    torso   card neck -> neck marker, aimed at the mid-hip; length = card cm * s * k, stretched toward the marker
            length by at most +-12%
    head    card neck -> neck marker, aimed 60% along the spine / 40% at the head marker (which sits toward the
            face, not the crown), natural length
    pelvis  the card's two hip points on the two hip markers: natural height, width squeezed to the hips (0.55-1.15)
    arm     upper arm A -> shoulder marker aimed at the elbow marker; forearm A -> where the upper arm's B landed
            (no gap by construction), aimed at the wrist marker; hand A -> forearm's B, continuing the forearm
    leg     thigh A -> hip marker aimed at the knee; shin A -> thigh's B aimed at the ankle; foot A -> shin's B,
            drawn upright as painted (feet are not aimed), flipped so its toe points the way the toe marker does
    every aimed part: stretch along its own axis clamped to [0.88, 1.12]; what the clamp leaves is joint error.
Rendering:
    fast (evolution): each card rigidly warped onto the target canvas, no edge, no brads.
    full (sheets): each limb card is a triangle mesh bent inside the part near its joints (the end of the thigh
            turns half-way toward the shin, the top of the shin half-way back: one continuous trouser leg), each
            card's painted paper border stripped and one crisp edge drawn back (brown line + tan hairline, rigkit's
            colours) except where a card overlaps its chain neighbour; one clean brad (cut from a kit card of the
            same character, never the target) drawn at shoulders, elbows, wrists, hips, knees and ankles.
"""
import json, math, os
import numpy as np, cv2

from . import library, cards as C

ROOT = library.ROOT
KEYS = ['torso', 'pelvis', 'head', 'uarmL', 'uarmR', 'farmL', 'farmR', 'handL', 'handR',
        'thighL', 'thighR', 'shinL', 'shinR', 'footL', 'footR']
SLOT = {'torso': 'torso', 'pelvis': 'pelvis', 'head': 'head'}
for _s in 'LR':
    SLOT.update({'uarm' + _s: 'upper_arm', 'farm' + _s: 'forearm', 'hand' + _s: 'hand', 'thigh' + _s: 'thigh',
                 'shin' + _s: 'shin', 'foot' + _s: 'foot'})
CHAINS = {'armL': ['uarmL', 'farmL', 'handL'], 'armR': ['uarmR', 'farmR', 'handR'],
          'legL': ['thighL', 'shinL', 'footL'], 'legR': ['thighR', 'shinR', 'footR'], 'core': ['torso', 'pelvis', 'head']}
CANON_CM = {'upper_arm': 30.4, 'forearm': 26.7, 'thigh': 46.0, 'shin': 42.8}   # the library's own normalised lengths
STRETCH = (0.88, 1.12)
BRAD_CARD = {'poet': ('poet.red_black_sunglasses.body.front/1', (151.0, 31.0)),
             'ex': ('ex.ex_jacket.body.back/1-torso', (154.0, 49.0))}
EDGE_BROWN = np.array([30, 52, 104], np.float32)   # BGR, rigkit core.py
EDGE_TAN = np.array([96, 122, 146], np.float32)

MARKER_FILES = {'poet': ['shots/rig/poses_v2/poet__red_black_sunglasses.json', 'shots/rig/poses/poet__red_black_sunglasses.json'],
                'ex': ['shots/rig/poses/ex__ex_jacket.json']}


def P2(m, k):
    return np.array(m[k][:2], float)


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def all_targets(char, costume=None):
    """{painting id: Pose Lab target} for a character (+ costume: shots/rig/poses_v2 then poses/<char>__<costume>.json)"""
    out = {}
    files = MARKER_FILES[char] if (costume is None or (char, costume) in (('poet', 'red_black_sunglasses'), ('ex', 'ex_jacket'))) \
        else ['shots/rig/poses_v2/%s__%s.json' % (char, costume), 'shots/rig/poses/%s__%s.json' % (char, costume)]
    for f in reversed(files):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            out.update({t['id']: t for t in json.load(open(p))['targets']})
    return out


def target(char, costume, tid):
    T = all_targets(char, costume)[tid]
    m = T['markers']
    pts = {k: P2(m, k) for k in m if isinstance(m[k], list)}
    pts['midhip'] = (pts['hipL'] + pts['hipR']) / 2
    L = lambda a, b: np.linalg.norm(pts[a] - pts[b])
    ratios = []
    for a, b, slot in (('shoulder', 'elbow', 'upper_arm'), ('elbow', 'wrist', 'forearm'), ('hip', 'knee', 'thigh'), ('knee', 'ankle', 'shin')):
        ratios.append(max(L(a + 'L', b + 'L'), L(a + 'R', b + 'R')) / CANON_CM[slot])
    s = float(np.median(ratios))
    img = os.path.join(ROOT, 'shots/kits/cut', tid + '.webp')
    ref = C.read_bgra(img)
    if (ref.shape[1], ref.shape[0]) != (T['w'], T['h']):
        ref = cv2.resize(ref, (T['w'], T['h']))
    sw = L('shoulderL', 'shoulderR') / (L('neck', 'midhip') + 1e-6)
    back = pts['shoulderL'][0] < pts['shoulderR'][0]
    face = pts['chin'][0] - pts['neck'][0]
    facing = None if abs(face) < .12 * L('neck', 'midhip') else ('R' if face > 0 else 'L')
    if back:
        facing = None
    torso = L('neck', 'midhip')
    if back:
        head_view = ['back', 'threequarter_back']
    elif abs(face) > .25 * torso:
        head_view = ['side', 'threequarter']
    elif facing:
        head_view = ['threequarter', 'front']
    else:
        head_view = ['front']
    fv = {}
    for S in 'LR':
        d = pts['toe' + S] - pts['ankle' + S]
        side_on = abs(d[0]) > .9 * abs(d[1]) and abs(d[0]) > .12 * torso
        fv['foot_view_' + S] = (['side', 'threequarter_back'] if back else ['side']) if side_on else (['back', 'threequarter_back'] if back else ['front', 'threequarter'])
    markers = {k: v.copy() for k, v in pts.items()}
    # the reference's own figure: its alpha, minus props / labels listed in REF_IGNORE
    fig = ref[..., 3] > 128
    ign = np.zeros_like(fig)
    for x0, y0, x1, y1 in REF_IGNORE.get(tid, []):
        ign[y0:y1, x0:x1] = True
    # painted brads -> joint targets: each joint takes the nearest brad within 22% of the torso; else its marker
    rb = ref_brads(ref)
    bj = {}
    used = set()
    for j in BRAD_JOINTS:
        if j not in pts or not len(rb):
            continue
        d = np.linalg.norm(rb - pts[j], axis=1)
        for i in np.argsort(d):
            if d[i] > .22 * torso:
                break
            if i not in used:
                bj[j] = rb[i]; used.add(i)
                break
    for j, p in bj.items():
        pts[j] = p.copy()
    pts['midhip'] = (pts['hipL'] + pts['hipR']) / 2
    # the hip region the candidate must fill: from 15% of the spine above the hip line down to the crotch,
    # across the two hip joints (+ 25%), inside the reference figure
    sp = pts['neck'] - pts['midhip']
    down = -sp / (np.linalg.norm(sp) + 1e-9)
    hl, hr = pts['hipL'], pts['hipR']
    ex = .25 * (hr - hl)
    poly = np.array([hl - ex + .15 * sp, hr + ex + .15 * sp, hr + ex + down * .06 * torso, (hl + hr) / 2 + down * .14 * torso,
                     hl - ex + down * .06 * torso])
    hm = np.zeros(fig.shape, np.uint8)
    cv2.fillPoly(hm, [np.round(poly).astype(np.int32)], 1)
    hip_region = (hm > 0) & fig & ~ign
    return {'char': char, 'costume': costume, 'id': tid, 'pts': pts, 's': s, 'size': (T['w'], T['h']), 'ref': ref,
            'markers': markers, 'ref_brads': rb, 'brad_joints': bj, 'fig': fig, 'ignore': ign, 'hip_region': hip_region,
            'hip_poly': poly, 'head_view': head_view, **fv,
            'sw': sw, 'back': back, 'facing': facing, 'label': T.get('label'), 'scale_prior': (T.get('scale_prior') or {}).get('px_per_cm')}


BRAD_JOINTS = ['shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'wristL', 'wristR', 'hipL', 'hipR', 'kneeL', 'kneeR',
               'ankleL', 'ankleR']
REF_IGNORE = {'ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01': [(10, 222, 32, 262)]}   # the vape pen


def ref_brads(ref):
    """centres of the painted gold brads on a reference painting (hue 16-32, saturated, bright, round, 15-400 px,
    at least 5 px inside the figure)"""
    hsv = cv2.cvtColor(ref[..., :3], cv2.COLOR_BGR2HSV)
    h, s_, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    inner = cv2.erode((ref[..., 3] > 128).astype(np.uint8), np.ones((11, 11), np.uint8)) > 0
    gold = ((h >= 16) & (h <= 32) & (s_ > 100) & (v > 150) & inner).astype(np.uint8)
    gold = cv2.morphologyEx(gold, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    n, lab, st, cen = cv2.connectedComponentsWithStats(gold)
    out = [cen[i] for i in range(1, n) if 15 <= st[i, 4] <= 400 and .5 < st[i, 2] / max(st[i, 3], 1) < 2 and max(st[i, 2], st[i, 3]) <= 26]
    return np.array(out, float).reshape(-1, 2)


def fig_width(t, P, Q):
    """the reference figure's width (px) across the bone P->Q: median over 35/50/65%, None if ambiguous"""
    fig = t['fig']
    u = (Q - P) / (np.linalg.norm(Q - P) + 1e-9)
    n = np.array([-u[1], u[0]])
    H, W = fig.shape
    ws = []
    for f in (.35, .5, .65):
        c = P + f * (Q - P)
        if not (0 <= c[0] < W and 0 <= c[1] < H) or not fig[int(c[1]), int(c[0])]:
            continue
        ext = []
        for sgn in (1, -1):
            k = 0
            while k < 200:
                q = c + sgn * (k + 1) * n
                if not (0 <= q[0] < W and 0 <= q[1] < H) or not fig[int(q[1]), int(q[0])]:
                    break
                k += 1
            ext.append(k)
        ws.append(sum(ext))
    return float(np.median(ws)) if ws else None


WIDTH_FIT = (.8, 1.25)


def width_fit(t, card, P, Q, k):
    """across-bone scale that makes the card as wide as the reference limb there; 1 when the reference width is
    ambiguous (the limb crosses the body, or is over 1.7x the card)"""
    rw = fig_width(t, P, Q)
    cw = (card.wmid or 0) * t['s'] * k
    if not rw or cw < 1:
        return 1.0
    r = rw / cw
    if r > 1.7 or r < .5:
        return 1.0
    return float(np.clip(r, *WIDTH_FIT))


# ------------------------------------------------------------------ placing
class Placed(dict):
    __getattr__ = dict.get


def _aff(card, P, theta, s_ax, s_perp, mir, flipx=False):
    """card px -> canvas px: A -> P, card axis A->B -> angle theta, scales along/across the axis, mirror across the axis"""
    A, B = card.A, card.B
    phi = math.atan2(B[1] - A[1], B[0] - A[0])
    if flipx:      # feet and heads: keep the card upright, flip left-right about A, then turn by theta (a trim)
        S = np.diag([-s_ax if mir else s_ax, s_ax])
        c, s_ = math.cos(theta), math.sin(theta)
        M = np.array([[c, -s_], [s_, c]]) @ S
    else:
        c, s_ = math.cos(-phi), math.sin(-phi)
        Rm = np.array([[c, -s_], [s_, c]])
        D = np.diag([s_ax, -s_perp if mir else s_perp])
        c2, s2 = math.cos(theta), math.sin(theta)
        R2 = np.array([[c2, -s2], [s2, c2]])
        M = R2 @ D @ Rm
    t = P - M @ A
    return np.hstack([M, t[:, None]])


def app(M, p):
    return M[:, :2] @ np.asarray(p, float) + M[:, 2]


def _aimed(card, P, Q, s, k, rot, mir, stretch=True, wf=1.0):
    nat = card.len_cm * s * k
    want = np.linalg.norm(Q - P)
    st = float(np.clip(want / nat, *STRETCH)) if stretch else 1.0
    th = math.atan2(Q[1] - P[1], Q[0] - P[0]) + math.radians(rot)
    sc = s * k * card.ppc ** -1
    M = _aff(card, P, th, sc * st, sc * wf, mir)
    return M, th, st, want / nat


def near_side(t, view):
    """which arm / leg is nearer the camera (drawn over the torso) in a turned view"""
    if view in ('front', 'back', 'threequarter_back'):
        return None
    return 'R' if (t['facing'] or 'R') == 'R' else 'L'


def place(G, t, lib):
    """G genome, t target, lib {id: library card}. Returns {key: Placed} in canvas px at factor 1."""
    pts, s = t['pts'], t['s']
    out = {}

    def card(key):
        g = G['parts'].get(key)
        if not g:
            return None, None
        return C.prep(lib[g['id']]), g

    # torso: neck -> toward mid-hip (card B = neck, A = hem)
    c, g = card('torso')
    nat = c.len_cm * s * g['k']
    want = np.linalg.norm(pts['midhip'] - pts['neck'])
    st = float(np.clip(want / nat, *STRETCH))
    th = math.atan2(pts['midhip'][1] - pts['neck'][1], pts['midhip'][0] - pts['neck'][0]) + math.radians(g['rot'])
    sc = s * g['k'] / c.ppc
    # build with the card's B as the proximal end
    rev = C.Card(c); rev['A'], rev['B'] = c.B, c.A
    wf = width_fit(t, c, pts['neck'], pts['midhip'], g['k'])
    M = _aff(rev, pts['neck'], th, sc * st, sc * wf, g['mir'])
    out['torso'] = Placed(key='torso', card=c, g=g, M=M, P=app(M, c.B), Q=app(M, c.A), th=th, st=st, want=want / nat, wf=wf)
    spine = pts['neck'] - pts['midhip']
    # pelvis
    c, g = card('pelvis')
    if c is not None and c.hip1 is None:
        print('pelvis card without hip points:', g['id'], c.slot)
        c = None
    if c is not None:
        # the card's two hip points onto the two hip markers: natural height, width squeezed to the hips (0.55-1.15),
        # so a turned body's narrow hips do not leave the connector's lobes sticking out
        h1, h2 = np.asarray(c.hip1), np.asarray(c.hip2)
        tl, tr = (pts['hipR'], pts['hipL']) if pts['hipR'][0] < pts['hipL'][0] else (pts['hipL'], pts['hipR'])
        sc = s * g['k'] / c.ppc
        sx = float(np.clip(np.linalg.norm(tr - tl) / (sc * np.linalg.norm(h2 - h1) + 1e-6), .55, 1.25))
        th = math.atan2(tr[1] - tl[1], tr[0] - tl[0]) + math.radians(g['rot'])
        u = (h2 - h1) / (np.linalg.norm(h2 - h1) + 1e-9)
        Rc = np.array([[u[0], u[1]], [-u[1], u[0]]])            # card hip axis -> +x
        Rt = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
        Mx = Rt @ np.diag([sc * sx, sc]) @ Rc
        if g['mir']:
            Mx = Mx @ np.array([[-1, 0], [0, 1]])
        mid_c = (h1 + h2) / 2
        tvec = (tl + tr) / 2 - Mx @ mid_c
        M = np.hstack([Mx, tvec[:, None]])
        # the hip piece shows only between the thighs, below the hem: clipped to hips -> crotch (no band, no lobes)
        down = -spine / (np.linalg.norm(spine) + 1e-9)
        hw = np.linalg.norm(tr - tl)
        clip = np.array([tl - .3 * spine, tr - .3 * spine, tr, (tl + tr) / 2 + down * max(.55 * hw, 6 * s), tl])
        out['pelvis'] = Placed(key='pelvis', card=c, g=g, M=M, P=app(M, c.A), Q=app(M, c.B), th=th, st=sx, want=1.0, clip=clip)
    # head
    c, g = card('head')
    # the head marker sits toward the face, not on the crown: aim the head between the spine and the marker
    u1 = spine / (np.linalg.norm(spine) + 1e-9)
    u2 = (pts['head'] - pts['neck']) / (np.linalg.norm(pts['head'] - pts['neck']) + 1e-9)
    aim = pts['neck'] + (.6 * u1 + .4 * u2) * 50
    M, th, st, w = _aimed(c, pts['neck'], aim, s, g['k'], g['rot'], g['mir'], stretch=False)
    out['head'] = Placed(key='head', card=c, g=g, M=M, P=app(M, c.A), Q=app(M, c.B), th=th, st=st, want=w)
    for S in 'LR':
        prev = None
        for key, a, b in (('uarm' + S, 'shoulder' + S, 'elbow' + S), ('farm' + S, None, 'wrist' + S), ('hand' + S, None, None),
                          ('thigh' + S, 'hip' + S, 'knee' + S), ('shin' + S, None, 'ankle' + S), ('foot' + S, None, None)):
            c, g = card(key)
            if key.startswith('thigh'):
                prev = None
            P = pts[a] if a else prev.Q
            if key.startswith('hand'):
                Q = P + (prev.Q - prev.P)
                M, th, st, w = _aimed(c, P, Q, s, g['k'], g['rot'], g['mir'], stretch=False)
            elif key.startswith('foot'):
                M = _aff(c, P, math.radians(g['rot']), s * g['k'] / c.ppc, s * g['k'] / c.ppc, g['mir'], flipx=True)
                th, st, w = math.radians(g['rot']), 1.0, 1.0
            else:
                wf = width_fit(t, c, P, pts[b], g['k'])
                M, th, st, w = _aimed(c, P, pts[b], s, g['k'], g['rot'], g['mir'], wf=wf)
            pl = Placed(key=key, card=c, g=g, M=M, P=app(M, c.A), Q=app(M, c.B), th=th, st=st, want=w,
                        wf=wf if not key.startswith(('hand', 'foot')) else 1.0)
            out[key] = pl
            prev = pl
    return out


def card_brads(PL):
    """every placed card's own painted brads, canvas px: {key: array (n, 2)}"""
    out = {}
    for k, p in PL.items():
        cb = p.card.cbrads
        b = np.asarray(cb if cb is not None else [], float).reshape(-1, 2)
        out[k] = b @ p.M[:, :2].T + p.M[:, 2] if len(b) else b
    return out


def foot_mirror(c, t, S):
    """flip a foot card so its toe points the way the target's toe marker does (front-on boots: no flip)"""
    dx_card = c.B[0] - c.A[0]
    dx_t = t['pts']['toe' + S][0] - t['pts']['ankle' + S][0]
    if abs(dx_card) < .25 * np.linalg.norm(np.subtract(c.B, c.A)) or abs(dx_t) < 4:
        return 0
    return int((dx_card > 0) != (dx_t > 0))


def head_mirror(c, t, libcard):
    f = None
    if libcard.get('left') is not None:
        f = 'L' if libcard['left'] else 'R'
    elif libcard.get('faces') in ('L', 'R'):
        f = libcard['faces']
    elif libcard.get('facing') in ('left', 'right'):
        f = libcard['facing'][0].upper()
    if f is None or t['facing'] is None:
        return 0
    return int(f != t['facing'])


def order(PL, view, t):
    """draw order, back to front"""
    near = near_side(t, view)
    far = None if near is None else ('L' if near == 'R' else 'R')
    seq = []
    # proximal over distal: the tabs at the top of a shin / forearm card slide under the thigh / sleeve above
    arm = lambda S: ['hand' + S, 'farm' + S, 'uarm' + S]
    leg = lambda S: ['foot' + S, 'shin' + S, 'thigh' + S]
    if far:
        seq += arm(far) + ['pelvis'] + leg(far) + leg(near) + ['head', 'torso'] + arm(near)
    else:
        seq += ['pelvis'] + leg('L') + leg('R') + ['head', 'torso'] + arm('L') + arm('R')
    return [k for k in seq if k in PL]


# chain neighbours: (key, end) -> neighbour key; end 'P' = proximal, 'Q' = distal
NEIGH = {}
for _s in 'LR':
    NEIGH.update({('uarm' + _s, 'Q'): 'farm' + _s, ('farm' + _s, 'P'): 'uarm' + _s, ('farm' + _s, 'Q'): 'hand' + _s,
                  ('hand' + _s, 'P'): 'farm' + _s, ('thigh' + _s, 'Q'): 'shin' + _s, ('shin' + _s, 'P'): 'thigh' + _s,
                  ('shin' + _s, 'Q'): 'foot' + _s, ('foot' + _s, 'P'): 'shin' + _s})
BEND = {'uarm', 'farm', 'thigh', 'shin'}     # parts bent at their joint ends (hands, feet, head, torso stay rigid)


def clip_mask(poly, W, H):
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.round(poly * 4).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=2)
    return m.astype(np.float32) / 255.


# ------------------------------------------------------------------ fast render
def render_fast(PL, view, t, F=1.0):
    W, H = int(t['size'][0] * F), int(t['size'][1] * F)
    acc = np.zeros((H, W, 4), np.float32)
    masks = {}
    Sm = np.diag([F, F])
    for k in order(PL, view, t):
        p = PL[k]
        M = Sm @ p.M
        lay = cv2.warpAffine(p.card.bgra, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if p.clip is not None:
            lay[..., 3] *= clip_mask(p.clip * F, W, H)
        a = lay[..., 3:] / 255.
        masks[k] = a[..., 0]
        acc[..., :3] = lay[..., :3] * a + acc[..., :3] * (1 - a)
        acc[..., 3:] = a * 255 + acc[..., 3:] * (1 - a)
    return acc, masks


# ------------------------------------------------------------------ full render
def raster_fast(Vo, UV, T, W, H, alpha):
    """triangle rasteriser (after rigkit core.raster_fast, one depth group): per output pixel, the card texel it shows"""
    mx = np.full((H, W), -10, np.float32); my = np.full((H, W), -10, np.float32)
    cov = np.zeros((H, W), np.float32)
    P = Vo[T]; Q = UV[T]
    X = np.concatenate([P, np.ones(P.shape[:2] + (1,))], 2)
    det = np.linalg.det(X)
    good = np.abs(det) > 1e-9
    Minv = np.zeros_like(X); Minv[good] = np.linalg.inv(X[good])
    Mu = np.einsum('nij,njk->nik', Minv, Q)
    SH = 4
    idx = np.nonzero(good)[0]
    ids = np.zeros((H, W), np.int32)
    pts = np.round(P[idx] * (1 << SH) - (1 << (SH - 1))).astype(np.int32)
    for k, i in enumerate(idx):
        cv2.fillConvexPoly(ids, pts[k], int(i) + 1, lineType=cv2.LINE_8, shift=SH)
    ys, xs = np.nonzero(ids)
    t = ids[ys, xs] - 1
    px = xs + 0.5; py = ys + 0.5
    u = px * Mu[t, 0, 0] + py * Mu[t, 1, 0] + Mu[t, 2, 0]
    v = px * Mu[t, 0, 1] + py * Mu[t, 1, 1] + Mu[t, 2, 1]
    mx[ys, xs] = u; my[ys, xs] = v; cov[ys, xs] = 1
    return mx, my, cov


def _smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def bend_part(p, PL, F, W, H, step=3.0, later=()):
    """mesh-deform one card: rigid placement, then the ends near a chain joint turned toward the neighbour"""
    c = p.card
    M = np.diag([F, F]) @ p.M
    sc = math.sqrt(abs(np.linalg.det(M[:, :2])))
    # resample the card to about output resolution first (UV space = resampled card px)
    r = min(1.0, sc * 1.5)
    tex = cv2.resize(c.bgra, None, fx=r, fy=r, interpolation=cv2.INTER_AREA if r < 1 else cv2.INTER_LINEAR)
    al = tex[..., 3]
    h, w = al.shape
    xs = np.arange(0, w + step, step); ys = np.arange(0, h + step, step)
    gx, gy = np.meshgrid(xs, ys)
    V = np.stack([gx.ravel(), gy.ravel()], 1).astype(np.float64)
    nx = len(xs)
    md = cv2.dilate((al > 8).astype(np.uint8), np.ones((5, 5), np.uint8))
    cs = cv2.resize(md, (len(xs) - 1, len(ys) - 1), interpolation=cv2.INTER_AREA) if len(xs) > 1 and len(ys) > 1 else md
    cell = cv2.resize(md.astype(np.float32), (len(xs) - 1, len(ys) - 1), interpolation=cv2.INTER_AREA) > 0
    jj, ii = np.nonzero(cell)
    a = jj * nx + ii; b = a + 1; cc = a + nx; d = cc + 1
    tris = np.concatenate([np.stack([a, b, d], 1), np.stack([a, d, cc], 1)])
    Vc = V / r                       # card px
    Vo = (Vc @ M[:, :2].T + M[:, 2])
    base = p.key.rstrip('LR')
    if base in BEND:
        A, B = np.asarray(c.A), np.asarray(c.B)
        L = np.linalg.norm(B - A)
        tt = ((Vc - A) @ (B - A)) / (L * L)
        rr = .18
        for end, w_fn in (('Q', lambda t_: .5 * _smooth((t_ - (1 - rr)) / rr) + .5 * _smooth((t_ - 1) / rr)),
                          ('P', lambda t_: .5 * _smooth((rr - t_) / rr) + .5 * _smooth(-t_ / rr))):
            nb = NEIGH.get((p.key, end))
            if not nb or nb not in PL or nb.rstrip('LR') == 'foot':
                continue
            q = PL[nb]
            dth = wrap(q.th - p.th)
            if abs(dth) > math.radians(150):
                continue
            J = (p.Q if end == 'Q' else p.P) * F
            wv = w_fn(tt)
            ang = wv * dth
            ca, sa = np.cos(ang), np.sin(ang)
            dvec = Vo - J
            Vo = J + np.stack([ca * dvec[:, 0] - sa * dvec[:, 1], sa * dvec[:, 0] + ca * dvec[:, 1]], 1)
    mx, my, cov = raster_fast(Vo, V, tris, W, H, al)
    lay = cv2.remap(tex, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) * cov[..., None]
    # edge class in card space: 1 = the card's own outline (always edged), .5 = near a chain joint (edged only over empty paper)
    E = np.ones((h, w), np.float32)
    A, B = np.asarray(c.A) * r, np.asarray(c.B) * r
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rad = max(c.w0 or 0, c.w1 or 0) * c.ppc * r * .75 + 4
    for end, pt in (('P', A), ('Q', B)):
        nb = NEIGH.get((p.key, end))
        if nb in PL or (p.key.startswith(('uarm', 'thigh')) and end == 'P'):
            # a neighbour still to come draws the outline at this joint; one already down: edge only over paper
            E[(xx - pt[0]) ** 2 + (yy - pt[1]) ** 2 < rad ** 2] = 0. if nb in later else .5
    if p.key in ('head', 'pelvis'):
        E[:] = .5 if p.key == 'pelvis' else E
    Eo = cv2.remap(E, mx, my, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=1) * cov
    # fade: the lower cap of a thigh / upper arm (drawn over the shin / forearm) dissolves into the cloth below the
    # joint, so the two read as one sleeve / one trouser leg (kept where nothing is under it)
    fade = np.ones((h, w), np.float32)
    if base in ('uarm', 'thigh') and NEIGH.get((p.key, 'Q')) in PL:
        A_, B_ = np.asarray(c.A) * r, np.asarray(c.B) * r
        L_ = np.linalg.norm(B_ - A_)
        tt_ = ((xx - A_[0]) * (B_[0] - A_[0]) + (yy - A_[1]) * (B_[1] - A_[1])) / (L_ * L_)
        fade = _smooth((1.02 - tt_) / .12).astype(np.float32)
    Fo = cv2.remap(fade, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=1)
    return lay, Eo, Fo


def strip_border(lay, bw_px):
    if bw_px < 1:
        return lay
    a = lay[..., 3]
    hard = (a > 20).astype(np.uint8)
    d = cv2.distanceTransform(np.pad(hard, 1), cv2.DIST_L2, 3)[1:-1, 1:-1]
    out = lay.copy()
    out[..., 3] = a * np.clip(d - bw_px + .5, 0, 1)
    return out


def ring(lay, E, bg_a, sc_o):
    al = lay[..., 3] / 255.
    hard = (al > .5).astype(np.uint8)
    if not hard.any():
        return None
    wb, wt = 1.6 * sc_o, 1.0 * sc_o
    d = cv2.distanceTransform(1 - hard, cv2.DIST_L2, 5)
    r = int(math.ceil(wb + wt)) + 1
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    e1 = cv2.dilate(((E > .75) * hard).astype(np.float32), k)
    e2 = cv2.dilate((((E > .25) & (E <= .75)) * hard).astype(np.float32), k)
    Eo = np.clip(e1 + e2 * (1 - bg_a), 0, 1)
    a_out = np.clip(wb + wt - d + .5, 0, 1) * (d > 0) * Eo
    tmix = np.clip(d - wb + .5, 0, 1)[..., None]
    col = EDGE_BROWN * (1 - tmix) + EDGE_TAN * tmix
    return np.dstack([col, a_out * 255]).astype(np.float32)


def over(dst, src):
    """straight-alpha 'over'"""
    a = src[..., 3:] / 255.
    b = dst[..., 3:] / 255.
    oa = a + b * (1 - a)
    rgb = (src[..., :3] * a + dst[..., :3] * b * (1 - a)) / np.maximum(oa, 1e-6)
    return np.dstack([rgb, oa * 255])


_BRAD = {}


def brad_sprite(char):
    if char not in _BRAD:
        cid, (cx, cy) = BRAD_CARD[char]
        lc = next(c for c in library.cards(char, {'poet': 'red_black_sunglasses', 'ex': 'ex_jacket'}[char]) if c['id'] == cid)
        im = C.read_bgra(lc['img']).astype(np.float32)
        R = 18
        patch = im[int(cy) - R:int(cy) + R + 1, int(cx) - R:int(cx) + R + 1].copy()
        b, g, r_ = patch[..., 0], patch[..., 1], patch[..., 2]
        gold = (r_ > 120) & (r_ - b > 40)
        yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
        dd = np.hypot(xx, yy)
        rad = float(np.percentile(dd[gold], 92)) if gold.sum() > 20 else 10.
        patch[..., 3] = 255 * np.clip((rad + 1.0 - dd) * 1.5, 0, 1)
        _BRAD[char] = (patch, rad, lc['ppc'])
    return _BRAD[char]


def draw_brad(acc, char, p, r_out):
    spr, rad, _ = brad_sprite(char)
    k = r_out / rad
    R = spr.shape[0] // 2
    half = int(math.ceil(k * R)) + 2
    x0, y0 = int(p[0]) - half, int(p[1]) - half
    x1, y1 = x0 + 2 * half + 1, y0 + 2 * half + 1
    H, W = acc.shape[:2]
    if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
        return acc
    Mx = np.float32([[k, 0, p[0] - k * R - x0], [0, k, p[1] - k * R - y0]])
    so = cv2.warpAffine(spr, Mx, (x1 - x0, y1 - y0), flags=cv2.INTER_AREA)
    acc[y0:y1, x0:x1] = over(acc[y0:y1, x0:x1], so)
    return acc


JOINT_BRADS = [('uarm', 'P'), ('uarm', 'Q'), ('farm', 'Q'), ('thigh', 'P'), ('thigh', 'Q'), ('shin', 'Q')]


def render_full(PL, view, t, F=2.0):
    W, H = int(t['size'][0] * F), int(t['size'][1] * F)
    pad = int(60 * F)
    W2, H2 = W + 2 * pad, H + 2 * pad
    acc = np.zeros((H2, W2, 4), np.float32)
    PLs = {}
    for k, p in PL.items():          # shift into the padded canvas
        q = Placed(p)
        q['M'] = p.M.copy(); q['M'][:, 2] += pad / F
        q['P'] = p.P + pad / F; q['Q'] = p.Q + pad / F
        if p.clip is not None:
            q['clip'] = p.clip + pad / F
        PLs[k] = q
    sc_o = F * 0.9
    drawn = []
    seq = order(PLs, view, t)
    for i, k in enumerate(seq):
        p = PLs[k]
        lay, E, Fo = bend_part(p, PLs, F, W2, H2, later=set(seq[i + 1:]))
        if p.clip is not None:
            lay[..., 3] *= clip_mask(p.clip * F, W2, H2)
        bw = p.card.border * math.sqrt(abs(np.linalg.det(p.M[:, :2]))) * F
        lay = strip_border(lay, min(bw, 4 * F))
        bg_a = acc[..., 3] / 255.
        lay[..., 3] *= Fo + (1 - Fo) * (1 - bg_a)
        rg = ring(lay, E, bg_a, sc_o)
        if rg is not None:
            acc = over(acc, rg)
        acc = over(acc, lay)
        drawn.append(k)
        # a brad rides each joint, drawn as soon as every part meeting there is down
        for jb, end in JOINT_BRADS:
            for S in 'LR':
                owner = PLs.get(jb + S)
                nb = NEIGH.get((jb + S, end))
                need = [x for x in (jb + S, nb) if x and x in PLs]
                if owner is None or k not in need or not all(x in drawn for x in need):
                    continue
                pt = (owner.P if end == 'P' else owner.Q) * F
                acc = draw_brad(acc, t['char'], pt, 2.1 * t['s'] * F)
    a = acc[..., 3]
    out = acc[pad:pad + H, pad:pad + W]
    return np.clip(out, 0, 255).astype(np.uint8), pad



def joints_out(PL):
    """the skeleton the candidate was posed on (its own placed joints), canvas px at factor 1"""
    J = {'neck': PL['torso'].P, 'waist': PL['torso'].Q, 'headtop': PL['head'].Q}
    for S in 'LR':
        J['sh' + S] = PL['uarm' + S].P; J['el' + S] = PL['uarm' + S].Q; J['wr' + S] = PL['farm' + S].Q
        J['tip' + S] = PL['hand' + S].Q; J['hip' + S] = PL['thigh' + S].P; J['kn' + S] = PL['thigh' + S].Q
        J['an' + S] = PL['shin' + S].Q; J['to' + S] = PL['foot' + S].Q
    return J


SKEL = [('neck', 'headtop'), ('neck', 'waist'), ('shL', 'shR'), ('shL', 'elL'), ('elL', 'wrL'), ('wrL', 'tipL'),
        ('shR', 'elR'), ('elR', 'wrR'), ('wrR', 'tipR'), ('hipL', 'hipR'), ('hipL', 'knL'), ('knL', 'anL'), ('anL', 'toL'),
        ('hipR', 'knR'), ('knR', 'anR'), ('anR', 'toR'), ('neck', 'shL'), ('neck', 'shR')]
