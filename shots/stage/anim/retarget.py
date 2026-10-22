"""Retarget Acting Arena acts onto poem-kit cut-out characters.

    python3 shots/stage/anim/retarget.py                       # the default library
    python3 shots/stage/anim/retarget.py poet_tracksuit ACT-001 ACT-003

Source: the Bolas Crash Lab 3D joint bank (shots/arena/bolas/bank/T1NN.json,
cm, y up, floor y=0) that every solved act ACT-NNN__<cast>.json was compiled
from. Re-solving from the 3D joints (rather than the 2D frames) is what lets
a child, a woman and a man each get their own limb lengths.

Per frame:
  1. 3D retarget.  The source is scaled by r = target hip height / Bola hip
     height about the camera's ground point, so a planted source foot stays
     planted.  Bone DIRECTIONS come from the source, LENGTHS from the target
     (props in rigs.py).  Legs are two-bone IK from the hip to the foot card's
     ankle-brad point; the pelvis drops (smoothed) if a leg cannot reach.
  2. Projection through the act's camera (yaw/elev) at ONE fixed scale for
     every clip (K px per cm), so clips compare at true relative size.
  3. Card solve in 2D, as a chain of brads: torso (waist->neck) is the root;
     head, shoulders and the hip bridge hang on the torso card's own brads;
     arms are FK from the shoulder brad; legs are 2D IK from the bridge's hip
     brad to the ankle target.  Each card is scaled from cm (not from its
     sheet's pixel size): limbs may shorten along their axis for
     foreshortening (clamped), heads/hands/feet are rigid.
  4. Contact pass: while the source foot is down, the drawn sole contact point
     is pinned in screen space (the ankle target is shifted, the IK absorbs
     it), so the foot cannot slide.
  5. Checks are measured on the drawn cards: brad gap (distance between the
     two brads that should coincide), planted drift of the drawn sole,
     drawn height, axial squash.

Output clips: shots/stage/anim/clips/<character>/<ACT-id>.json in the arena
display-list format.  Image paths in `images` are RELATIVE TO THE CLIP FILE
(e.g. ../../../../kits/cut/...); `image_root` documents the same path from
shots/.
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigs

SHOTS = rigs.SHOTS
BANK = os.path.join(SHOTS, 'arena', 'bolas', 'bank')
ARENA_CLIPS = os.path.join(SHOTS, 'arena', 'clips')
OUT = os.path.join(HERE, 'clips')

W, H = 1920, 1080
K = H * 0.86 / 230          # px per cm, the same for every clip (arena zoom = 1)
CAM_Y = 92.0                # camera target height (cm), fixed so floors line up
DEG = math.pi / 180
J = ['pelvis', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR', 'heelL', 'heelR', 'ballL', 'ballR',
     'toeL', 'toeR', 'spineMid', 'neckBase', 'chest', 'shoulderL', 'shoulderR', 'elbowL', 'elbowR',
     'wristL', 'wristR', 'headBase', 'head', 'headTop', 'nose']
JI = {n: i for i, n in enumerate(J)}
SRC_HIP = 95.0              # Bola: thigh 44 + shin 43 + ankle 8
TOL_DRIFT = 0.6             # cm/frame (arena spec)
TOL_BRAD = 2.0              # cm (arena spec)


def _ranges(frs):
    frs = sorted(frs); out = []; a = b = frs[0]
    for x in frs[1:] + [None]:
        if x is not None and x == b + 1: b = x; continue
        out.append('%d' % a if a == b else '%d-%d' % (a, b))
        if x is not None: a = b = x
    return ','.join(out)


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v * 0


# ------------------------------------------------------------------ geometry helpers
def card_matrix(pivot, socket, A, B, girth, mirror=False, axial=None):
    """Affine m=[a,b,c,d,e,f] putting card point `pivot` on A with the card's
       pivot->socket axis along A->B. Scales `axial` along that axis (default:
       exactly |B-A|) and `girth` across it. mirror flips the card about its axis."""
    c0 = np.asarray(pivot, float); c1 = np.asarray(socket, float)
    A = np.asarray(A, float); B = np.asarray(B, float)
    cv = c1 - c0; Lc = np.linalg.norm(cv); v = B - A; Lw = np.linalg.norm(v)
    if Lc < 1e-6:
        cv = np.array([0.0, 1.0]); Lc = 1.0
    if Lw < 1e-6:
        v = cv; Lw = Lc
    u = cv / Lc; n = np.array([-u[1], u[0]])
    sa = (Lw / Lc) if axial is None else axial
    S = np.outer(u, u) * sa + np.outer(n, n) * girth * (-1 if mirror else 1)
    ac = math.atan2(u[1], u[0]); aw = math.atan2(v[1], v[0]); th = aw - ac
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    M = R @ S
    t = A - M @ c0
    return M, t


def apply(M, t, p):
    return M @ np.asarray(p, float) + t


def mlist(M, t):
    return [round(float(M[0, 0]), 5), round(float(M[1, 0]), 5), round(float(M[0, 1]), 5),
            round(float(M[1, 1]), 5), round(float(t[0]), 2), round(float(t[1]), 2)]


def ik2(Hp, A, l1, l2, bend_sign, stretch=1.04):
    """2D two-bone IK. Returns knee, ankle_reached, factor (>1 means stretched)."""
    d = A - Hp; L = np.linalg.norm(d)
    f = 1.0
    if L > (l1 + l2) * 0.9999:
        f = min(stretch, L / (l1 + l2) / 0.9999)
        l1 *= f; l2 *= f
    if L > l1 + l2:
        u = unit(d)
        return Hp + u * l1, Hp + u * (l1 + l2), f
    L = max(L, abs(l1 - l2) + 1e-3)
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    hh = math.sqrt(max(0.0, l1 * l1 - a * a))
    u = unit(d); n = np.array([-u[1], u[0]]) * bend_sign
    return Hp + u * a + n * hh, A, f


def ik3(Hp, A, l1, l2, pole):
    """3D two-bone IK with a pole direction for the knee."""
    d = A - Hp; L = np.linalg.norm(d); u = unit(d)
    L = min(max(L, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-4)
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    hh = math.sqrt(max(0.0, l1 * l1 - a * a))
    p = pole - u * np.dot(pole, u)
    if np.linalg.norm(p) < 1e-6:
        p = np.array([0.0, 0.0, 1.0]) - u * u[2]
    return Hp + u * a + unit(p) * hh


# ------------------------------------------------------------------ source + camera
def act_to_t(act):
    n = int(act.split('-')[1])
    return 'T%d' % (100 + n)


def load_source(act, actor='A'):
    V = json.load(open(os.path.join(BANK, act_to_t(act) + '.json')))
    frames = []
    for fr in V['frames']:
        a = fr['a'].get(actor)
        if a is None or a['j'][0] is None:
            frames.append(None); continue
        frames.append({'j': np.array(a['j'], float), 'fwd': np.array(a.get('fwd', [0, 0, 1]), float),
                       'hfwd': np.array(a.get('hfwd') or a.get('fwd', [0, 0, 1]), float),
                       'pfwd': np.array(a.get('pfwd') or a.get('fwd', [0, 0, 1]), float)})
    # carry over gaps
    last = None
    for i, f in enumerate(frames):
        if f is None: frames[i] = last
        else: last = f
    first = next(f for f in frames if f is not None)
    frames = [f or first for f in frames]
    arena = None
    for cast in ('poet', 'man', 'bolas'):
        p = os.path.join(ARENA_CLIPS, '%s__%s.json' % (act, cast))
        if os.path.exists(p):
            arena = json.load(open(p)); break
    return V, frames, arena


class Camera:
    def __init__(self, view):
        self.yaw = view.get('yaw', -22) * DEG; self.elev = view.get('elev', 12) * DEG
        self.cy, self.sy = math.cos(self.yaw), math.sin(self.yaw)
        self.ce, self.se = math.cos(self.elev), math.sin(self.elev)
        self.c = np.array([view.get('x', 0.0), CAM_Y, view.get('z', 0.0)])

    def p(self, P):
        x, y, z = P[0] - self.c[0], P[1] - self.c[1], P[2] - self.c[2]
        x1, z1 = x * self.cy - z * self.sy, x * self.sy + z * self.cy
        y2, z2 = y * self.ce - z1 * self.se, y * self.se + z1 * self.ce
        return np.array([W / 2 + x1 * K, H * 0.52 - y2 * K]), -z2     # (screen xy, depth: larger = farther)

    def yawrel(self, d):
        """0 = facing the camera, +90 = facing screen-right, 180 = facing away."""
        sx = d[0] * self.cy - d[2] * self.sy
        tc = d[0] * self.sy + d[2] * self.cy
        return math.degrees(math.atan2(sx, tc))


# ------------------------------------------------------------------ the target body
class Body:
    def __init__(self, rig):
        self.rig = rig
        Hc = rig['height_cm']; pr = rig['props']
        self.H = Hc
        self.hip = pr['hip'] * Hc; self.knee = pr['knee'] * Hc
        self.thigh = self.hip - self.knee
        self.bridge = pr['bridge'] * Hc; self.head = pr['head'] * Hc
        self.torso = Hc - self.hip - self.bridge - self.head
        self.uarm = pr['uarm'] * Hc; self.farm = pr['farm'] * Hc
        self.hand = pr['hand'] * Hc; self.foot = pr['foot'] * Hc
        # the ankle brad sits wherever the foot card puts it: measure it on the flat foot card
        fv = next(v for v in rig['views'].values() if 'foot' in v or 'foot_L' in v)
        fc = fv.get('foot') or fv.get('foot_L')
        pts = fc['pts']
        if fc['faces'] == 0:          # front/back boot: the sole has no heel->toe axis
            span = abs(pts['toe'][0] - pts['heel'][0]) or 1
            kf = (self.foot * 0.6) / span         # a front/back shoe is ~60% as wide as the foot is long
            self.ank_up = (pts['sole'][1] - pts['ankle'][1]) * kf
            self.ank_along = 0.3 * self.foot
        else:
            hv = np.array(pts['toe']) - np.array(pts['heel']); Lh = np.linalg.norm(hv); u = hv / Lh
            av = np.array(pts['ankle']) - np.array(pts['heel'])
            kf = self.foot / Lh
            self.ank_along = abs(float(np.dot(av, u))) * kf
            self.ank_up = abs(float(u[0] * av[1] - u[1] * av[0])) * kf
        self.shin = self.knee - self.ank_up
        if self.shin < 0.08 * Hc:
            raise ValueError('foot card ankle brad too high for %s' % rig['name'])
        self.r = self.hip / SRC_HIP
        # widths come from the cards so the 3D skeleton matches the drawn brads
        bv = next((v['bridge'] for v in rig['views'].values() if 'bridge' in v and not v['bridge'].get('virtual')), None)
        if bv is not None:
            p = bv['pts']; hm = (np.array(p['hipVL']) + np.array(p['hipVR'])) / 2
            kb = self.bridge / max(1.0, abs(hm[1] - p['waist'][1]))
            self.hipw = abs(p['hipVR'][0] - p['hipVL'][0]) * kb
        else:
            self.hipw = 0.10 * Hc
        tv = next((v['torso'] for v in rig['views'].values() if v['torso']['faces'] == 0), None)
        if tv is not None:
            p = tv['pts']; kt = self.torso / max(1.0, abs(p['waist'][1] - p['neck'][1]))
            self.shw = abs(p['shVR'][0] - p['shVL'][0]) * kt
        else:
            self.shw = 0.21 * Hc


BALL_FRAC = 17.0 / 22.0     # Bola: heel -> ball is 17 of the 22 cm heel -> toe


def contact_spans(frames, side, n_hold=3):
    """Frames where the source foot is down (heel or ball within 2.5cm of the floor and slow),
       and per frame which point carries it: 'heel' (heel down, incl. flat) or 'ball'."""
    hi, bi = JI['heel' + side], JI['ball' + side]
    N = len(frames); down = np.zeros(N, bool); ctype = [None] * N; kinds = [set() for _ in range(N)]
    for i in range(N):
        j = frames[i]['j']; jp = frames[max(0, i - 1)]['j']; jn = frames[min(N - 1, i + 1)]['j']
        for k, nm in ((bi, 'ball'), (hi, 'heel')):
            sp = 0.5 * np.linalg.norm((jn[k] - jp[k])[[0, 2]])
            if j[k][1] < 2.5 and sp < 1.2:
                down[i] = True; ctype[i] = nm; kinds[i].add(nm)
        if len(kinds[i]) == 2:
            # both down: the load is on whichever is lower (a rising heel hands it to the ball early)
            ctype[i] = 'heel' if j[hi][1] <= j[bi][1] + 1.0 else 'ball'
    spans = []; i = 0
    while i < N:
        if down[i]:
            k = i
            while k + 1 < N and down[k + 1]: k += 1
            if k - i + 1 >= n_hold: spans.append((i, k))
            i = k + 1
        else:
            i += 1
    return spans, ctype, kinds


def card_contact(card, M, t, kind, P=None, s=None):
    h = apply(M, t, card['pts']['heel']); to = apply(M, t, card['pts']['toe'])
    if card['faces'] == 0:
        # a front/back boot cannot show the roll, so the contact is carried by the
        # projected 3D contact point, kept relative to the card's ankle brad
        if P is None: return apply(M, t, card['pts']['sole'])
        return apply(M, t, card['pts']['ankle']) + (P[kind + s][0] - P['ank' + s][0])
    return h if kind == 'heel' else h + (to - h) * BALL_FRAC


def retarget3d(body, frames, origin, rot=0.0):
    """Per frame dict of 3D target joints (cm)."""
    r = body.r
    cr, sr = math.cos(rot), math.sin(rot)

    def X(p):            # rotate about origin (EX faces away), then scale about the ground point
        q = p - origin
        q = np.array([q[0] * cr + q[2] * sr, q[1], -q[0] * sr + q[2] * cr])
        return origin + q * r

    def Xd(d):
        return np.array([d[0] * cr + d[2] * sr, d[1], -d[0] * sr + d[2] * cr])

    out = []
    for fr in frames:
        S = fr['j']; T = {}
        g = lambda n: S[JI[n]]
        T['pelvis'] = X(g('pelvis'))
        T['fwd'] = Xd(fr['fwd']); T['hfwd'] = Xd(fr['hfwd']); T['pfwd'] = Xd(fr['pfwd'])
        hax = unit(Xd(g('hipL') - g('hipR')))
        T['hipL'] = T['pelvis'] + hax * body.hipw / 2; T['hipR'] = T['pelvis'] - hax * body.hipw / 2
        for s in 'LR':
            heel = X(g('heel' + s)); ball = X(g('ball' + s)); toe = X(g('toe' + s))
            u = unit(toe - heel)
            up = np.array([0.0, 1.0, 0.0]); nrm = unit(up - u * np.dot(up, u))
            T['heel' + s] = heel
            T['toe' + s] = heel + u * body.foot
            T['ball' + s] = heel + u * body.foot * BALL_FRAC
            T['ank' + s] = heel + u * body.ank_along + nrm * body.ank_up       # the ankle BRAD
            T['pole' + s] = Xd(g('knee' + s) - (g('hip' + s) + g('ankle' + s)) / 2)
        out.append(T)
    # pelvis drop so both legs reach their ankle brads (then smoothed so it never pops)
    reach = 0.975 * (body.thigh + body.shin)
    need = np.zeros(len(out))
    for i, T in enumerate(out):
        for s in 'LR':
            h = T['hip' + s]; a = T['ank' + s]
            dxz = np.linalg.norm((h - a)[[0, 2]])
            if dxz < reach:
                need[i] = max(need[i], (h[1] - a[1]) - math.sqrt(reach ** 2 - dxz ** 2))
    need = np.maximum(need, 0)
    win = np.array([max(need[max(0, i - 3):i + 4]) for i in range(len(need))])
    ker = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2); ker /= ker.sum()
    sm = np.convolve(np.pad(win, 6, mode='edge'), ker, mode='valid')
    drop = np.maximum(need, sm)
    for i, T in enumerate(out):
        dv = np.array([0, -drop[i], 0])
        S = frames[i]['j']; g = lambda n: S[JI[n]]
        for k in ('pelvis', 'hipL', 'hipR'): T[k] = T[k] + dv
        T['drop'] = float(drop[i])
        spine = unit(Xd(g('spineMid') - g('pelvis')))
        T['waist'] = T['pelvis'] + spine * body.bridge
        T['neck'] = T['waist'] + unit(Xd(g('neckBase') - g('spineMid'))) * body.torso
        T['top'] = T['neck'] + unit(Xd(g('headTop') - g('neckBase'))) * body.head
        shax = unit(Xd(g('shoulderL') - g('shoulderR')))
        tdir = unit(T['neck'] - T['waist'])
        for s in 'LR':
            sg = 1 if s == 'L' else -1
            sh = T['neck'] - tdir * 0.12 * body.torso + shax * sg * body.shw / 2
            el = sh + unit(Xd(g('elbow' + s) - g('shoulder' + s))) * body.uarm
            wr = el + unit(Xd(g('wrist' + s) - g('elbow' + s))) * body.farm
            T['sh' + s], T['el' + s], T['wr' + s] = sh, el, wr
            T['tip' + s] = wr + unit(wr - el) * body.hand
            T['knee' + s] = ik3(T['hip' + s], T['ank' + s], body.thigh, body.shin, T['pole' + s])
    return out


# ------------------------------------------------------------------ the 2D card solve
def view_for(yr, avail, prev, force=None):
    if force: return force
    a = abs(yr)
    want = 'front' if a < 40 else ('back' if a > 140 else 'profile')
    if prev is not None and prev != want and prev in avail:      # hysteresis
        if prev == 'profile' and (32 < a < 148): want = 'profile'
        if prev == 'front' and a < 48: want = 'front'
        if prev == 'back' and a > 132: want = 'back'
    order = {'profile': ['profile', 'front', 'back'], 'front': ['front', 'profile', 'back'],
             'back': ['back', 'profile', 'front']}[want]
    return next(v for v in order if v in avail)


def head_view(yr, avail):
    a = abs(yr)
    seq = ['front', 'threequarter', 'profile', 'threequarter_back', 'back']
    i = min(4, int((a + 22.5) // 45))
    want = seq[i]
    # nearest available, preferring the more-turned-away neighbour on ties
    for d in (0, 1, -1, 2, -2, 3, -3, 4, -4):
        k = i + d
        if 0 <= k < 5 and seq[k] in avail: return seq[k]
    return next(iter(avail))


class Solver:
    def __init__(self, name):
        self.rig = rigs.build(name); self.name = name
        self.body = Body(self.rig)

    def k(self, part, a, b, cm):
        """Card scale (screen px per card px) so the a->b span is `cm` long."""
        L = np.linalg.norm(np.array(part['pts'][b]) - np.array(part['pts'][a]))
        return cm * K / max(L, 1e-6)

    def solve(self, act, max_frames=None):
        V, frames, arena = load_source(act)
        if max_frames: frames = frames[:max_frames]
        cam = Camera(V['view'] or {})
        origin = np.array([cam.c[0], 0.0, cam.c[2]])
        rot = 0.0
        if self.rig.get('force_view') == 'back':
            # EX is only ever seen from behind: turn the whole act so his mean heading
            # points away from the camera (150 deg: away and a little to screen-right)
            f0 = np.mean([f['fwd'] for f in frames], axis=0); f0[1] = 0
            def turned(r_):
                return np.array([f0[0] * math.cos(r_) + f0[2] * math.sin(r_), 0, -f0[0] * math.sin(r_) + f0[2] * math.cos(r_)])
            rot = min((d * DEG for d in range(-180, 180)), key=lambda r_: abs(((cam.yawrel(turned(r_)) - 150) + 180) % 360 - 180))
        T3 = retarget3d(self.body, frames, origin, rot)
        b = self.body
        cs = {s: contact_spans(frames, s) for s in 'LR'}
        spans = {s: cs[s][0] for s in 'LR'}; ctype = {s: cs[s][1] for s in 'LR'}; kinds = {s: cs[s][2] for s in 'LR'}
        N = len(T3)

        # ---- pass 1: everything but the legs, plus ankle targets and foot cards
        F = []
        prev_view = None
        for i, T in enumerate(T3):
            P = {k: cam.p(v) for k, v in T.items() if isinstance(v, np.ndarray) and v.shape == (3,) and k not in ('fwd', 'hfwd', 'pfwd')}
            yr = cam.yawrel(T['pfwd']); hyr = cam.yawrel(T['hfwd'])
            vname = view_for(yr, self.rig['views'], prev_view, self.rig.get('force_view'))
            prev_view = vname
            # side: the body is seen side-on, whichever card set the kit could offer for it
            side = (not self.rig.get('force_view')) and 35 < abs(yr) < 145
            F.append({'P': P, 'yr': yr, 'hyr': hyr, 'view': vname, 'T': T, 'side': side})

        # foot placement (rigid card, pivot on the ankle brad, sole along heel->toe)
        def foot_card(fr, s):
            V_ = self.rig['views'][fr['view']]
            T = fr['T']; P = fr['P']
            heel3, toe3 = T['heel' + s], T['toe' + s]
            pitch = math.degrees(math.atan2(toe3[1] - heel3[1], np.linalg.norm((toe3 - heel3)[[0, 2]])))
            key = 'foot_' + s if ('foot_' + s) in V_ else 'foot'
            card = V_[key]
            if key == 'foot':
                if pitch < -18 and 'foot_heelup' in V_: card = V_['foot_heelup']
                elif pitch > 14 and 'foot_toeup' in V_: card = V_['foot_toeup']
            h2, t2 = P['heel' + s][0], P['toe' + s][0]
            kf = (b.foot * K) / max(1e-6, np.linalg.norm(np.array(card['pts']['toe']) - np.array(card['pts']['heel'])))
            if card['faces'] == 0:
                # a front/back boot is scaled by its ankle-brad height, which must equal the
                # height the 3D ankle brad is carried at, or the boot floats or sinks
                kf = (b.ank_up * K) / max(1e-6, card['pts']['sole'][1] - card['pts']['ankle'][1])
                M, t = card_matrix(card['pts']['ankle'], card['pts']['sole'], P['ank' + s][0],
                                   P['ank' + s][0] + np.array([0, 1.0]), kf, axial=kf)
                return card, M, t
            sdir = 1 if (t2[0] - h2[0]) >= 0 else -1
            if abs(t2[0] - h2[0]) < 0.25 * b.foot * K:          # foot pointing at/away from camera
                sdir = 1 if fr['yr'] >= 0 else -1
            mirror = card['faces'] != sdir
            hv = t2 - h2
            # the sole foreshortens like a limb (clamped), so the card's heel and ball land on the
            # projected heel and ball and a pinned contact does not drag the ankle
            fsf = min(1.0, max(0.45, np.linalg.norm(hv) / (b.foot * K)))
            if np.linalg.norm(hv) < 0.3 * b.foot * K:            # pointing at the camera: keep it level
                hv = np.array([sdir * 1.0, 0.0])
            ch = np.array(card['pts']['heel']); ct = np.array(card['pts']['toe'])
            M, t = card_matrix(ch, ct, np.zeros(2), unit(hv), kf, mirror=mirror, axial=kf * fsf)
            # then translate so the card's ankle brad is on the target
            t = t + (P['ank' + s][0] - apply(M, t, card['pts']['ankle']))
            return card, M, t

        for fr in F:
            fr['foot'] = {s: foot_card(fr, s) for s in 'LR'}

        # ---- contact pass: pin the drawn sole during source contact
        off = {s: np.zeros((N, 2)) for s in 'LR'}
        swaps = {s: set() for s in 'LR'}
        floor_y = {}
        for s in 'LR':
            for (a, z) in spans[s]:
                def contact_pt(i):
                    card, M, t = F[i]['foot'][s]
                    return card_contact(card, M, t, ctype[s][i] or 'heel', F[i]['P'], s)
                # anchor: x where the foot first lands, y on the floor line at that depth.
                # When the load moves heel -> ball the anchor is handed over continuously.
                c0 = contact_pt(a)
                g3 = F[a]['T']['heel' + s].copy(); g3[1] = 0.0
                fy = cam.p(g3)[0][1]
                anchor = np.array([c0[0], fy])
                def cardkey(i):
                    card, M, t = F[i]['foot'][s]
                    return (card['id'], np.linalg.det(M) < 0)
                for i in range(a, z + 1):
                    # hand the anchor over (keeping the ankle continuous) when the load moves heel->ball,
                    # or when the foot swaps to another state card or flips: a different card has a
                    # different contact point and pinning the old one would drag the ankle
                    # a load hand-over (heel -> ball) re-anchors with the ankle continuous; a card swap
                    # (flat -> heel-up, or a mirror flip) keeps the contact point where it is and lets
                    # the leg IK absorb the ankle shift, so the sole does not pop
                    if i > a and ctype[s][i] != ctype[s][i - 1]:
                        anchor = contact_pt(i) + off[s][i - 1]
                    if i > a and cardkey(i) != cardkey(i - 1):
                        swaps[s].add(i)
                    off[s][i] = anchor - contact_pt(i)
            # ease the offset in/out over 4 frames outside each span
            o = off[s]; inspan = np.zeros(N, bool)
            for a, z in spans[s]: inspan[a:z + 1] = True
            res = o.copy()
            for i in range(N):
                if inspan[i]: continue
                prv = [k for k in range(max(0, i - 4), i) if inspan[k]]
                nxt = [k for k in range(i + 1, min(N, i + 5)) if inspan[k]]
                acc = np.zeros(2); wsum = 0
                if prv:
                    k = prv[-1]; w_ = 1 - (i - k) / 5.0; acc += o[k] * w_; wsum += 1
                if nxt:
                    k = nxt[0]; w_ = 1 - (k - i) / 5.0; acc += o[k] * w_; wsum += 1
                if wsum: res[i] = acc / wsum
            off[s] = res
        for i, fr in enumerate(F):
            for s in 'LR':
                card, M, t = fr['foot'][s]
                fr['foot'][s] = (card, M, t + off[s][i])
                fr['ankT' + s] = fr['P']['ank' + s][0] + off[s][i]

        # ---- pass 2: build every card
        need = np.zeros(N); dyv = np.zeros(N)
        for attempt in (0, 1):
            clip_frames = []; images = {}; worst_gap = 0.0; gap_frames = []; squash = []
            stretch_max = 1.0; miss_max = 0.0; heights = []
            drift = {s: [] for s in 'LR'}; prev_contact = {s: None for s in 'LR'}; swap_jump = []
            spanset = {s: set(i for a, z in spans[s] for i in range(a, z + 1)) for s in 'LR'}
            problems = set()
            for i, fr in enumerate(F):
                V_ = self.rig['views'][fr['view']]; T = fr['T']
                sh_ = np.array([0.0, dyv[i]])
                P = {k: ((v[0] + sh_, v[1]) if not k.startswith(('heel', 'toe', 'ank', 'ball')) else v) for k, v in fr['P'].items()}
                ops = []; links = []
                yr = fr['yr']; s_face = 1 if yr >= 0 else -1
                prof = fr['view'] == 'profile' and not self.rig.get('front_for_profile')
                g = lambda part: images.setdefault(part['id'], part['img'])

                def img(part, M, t, shade=0.0, z=0.0):
                    g(part)
                    op = {'t': 'img', 'id': part['id'], 'm': mlist(M, t)}
                    if shade: op['shade'] = round(shade, 2)
                    return op

                # torso
                tc = V_['torso']
                kt = self.k(tc, 'waist', 'neck', b.torso)
                w2, n2 = P['waist'][0], P['neck'][0]
                ax = np.linalg.norm(n2 - w2) / max(1e-6, np.linalg.norm(np.array(tc['pts']['neck']) - np.array(tc['pts']['waist'])))
                ax = min(max(ax, 0.80 * kt), 1.02 * kt)
                mir_t = (tc['faces'] != 0 and tc['faces'] != s_face)
                Mt, tt = card_matrix(tc['pts']['waist'], tc['pts']['neck'], w2, n2, kt, mirror=mir_t, axial=ax)
                neckC = apply(Mt, tt, tc['pts']['neck']); waistC = apply(Mt, tt, tc['pts']['waist'])
                # which viewer side is the actor's L (front: viewer right; back: viewer left)
                Lright = P['shL'][0][0] > P['shR'][0][0]
                if tc['faces'] == 0:
                    if fr['view'] == 'front' and not self.rig.get('front_for_profile'): Lright = True
                    if fr['view'] == 'back': Lright = False
                shC = {'L': apply(Mt, tt, tc['pts']['shVR' if Lright else 'shVL']),
                       'R': apply(Mt, tt, tc['pts']['shVL' if Lright else 'shVR'])}
                # bridge: hangs on the torso's waist brad, squashed edge-on in profile
                bc = V_.get('bridge')
                hipC = {}
                bridge_op = None
                if bc is not None and not bc.get('virtual'):
                    kb = b.bridge * K / max(1.0, abs((bc['pts']['hipVL'][1] + bc['pts']['hipVR'][1]) / 2 - bc['pts']['waist'][1]))
                    hm3 = (P['hipL'][0] + P['hipR'][0]) / 2
                    sep = abs(P['hipL'][0][0] - P['hipR'][0][0]) / max(1e-6, b.hipw * K)
                    sq = min(1.0, max(0.45 if self.rig.get('front_for_profile') else 0.18, sep)) if fr['side'] else 1.0
                    hmC = (np.array(bc['pts']['hipVL']) + np.array(bc['pts']['hipVR'])) / 2
                    LrB = P['hipL'][0][0] > P['hipR'][0][0] if fr['side'] else Lright
                    Mb, tb = card_matrix(bc['pts']['waist'], hmC, waistC, waistC + unit(hm3 - P['waist'][0]) * 100, kb * sq,
                                         axial=kb)
                    hipC = {'L': apply(Mb, tb, bc['pts']['hipVR' if LrB else 'hipVL']),
                            'R': apply(Mb, tb, bc['pts']['hipVL' if LrB else 'hipVR'])}
                    if sq > 0.5 or self.rig.get('front_for_profile'):          # edge-on it is a sliver: it still carries the hip brads, but is not drawn
                        bridge_op = img(bc, Mb, tb)
                else:
                    for s in 'LR':
                        hipC[s] = waistC + (P['hip' + s][0] - P['waist'][0])
                # head
                hv = head_view(fr['hyr'], self.rig['heads'])
                hc = self.rig['heads'][hv]
                kh = self.k(hc, 'neck', 'top', b.head)
                hs = 1 if fr['hyr'] >= 0 else -1
                mir_h = hc['faces'] != 0 and hc['faces'] != hs
                Mh, th = card_matrix(hc['pts']['neck'], hc['pts']['top'], neckC, neckC + unit(P['top'][0] - P['neck'][0]) * 100,
                                     kh, mirror=mir_h, axial=kh)
                head_ops = [img(hc, Mh, th)]
                gl = self.rig['glasses'].get(hv)
                if gl is not None:
                    kg = kh * hc['w'] * gl['width_frac'] / gl['w']
                    at = np.array([gl['at'][0] * hc['w'], gl['at'][1] * hc['h']])
                    ctr = apply(Mh, th, at)
                    hax = (Mh @ np.array([0, -1.0])); hax = unit(hax)
                    Mg, tg = card_matrix(gl['pts']['anchor'], np.array(gl['pts']['anchor']) + [0, -10], ctr, ctr + hax * 10,
                                         kg, mirror=mir_h, axial=kg)
                    head_ops.append(img(gl, Mg, tg))
                links.append(('neck', neckC, apply(Mh, th, hc['pts']['neck'])))

                # arms
                arm_ops = {}
                for s in 'LR':
                    key = (lambda n: n + '_' + s if (n + '_' + s) in V_ else n)
                    ua, fa, hd = V_[key('uarm')], V_[key('farm')], V_[key('hand')]
                    sh = shC[s]
                    fs1 = np.linalg.norm(P['el' + s][0] - P['sh' + s][0]) / (b.uarm * K)
                    fs2 = np.linalg.norm(P['wr' + s][0] - P['el' + s][0]) / (b.farm * K)
                    fs1c, fs2c = max(0.55, min(1.0, fs1)), max(0.55, min(1.0, fs2))
                    squash.append(min(fs1c, fs2c))
                    el = sh + unit(P['el' + s][0] - P['sh' + s][0]) * b.uarm * K * fs1c
                    wr = el + unit(P['wr' + s][0] - P['el' + s][0]) * b.farm * K * fs2c
                    mir = prof and s_face < 0
                    ku = self.k(ua, 'pivot', 'socket', b.uarm); kfa = self.k(fa, 'pivot', 'socket', b.farm)
                    Mu, tu = card_matrix(ua['pts']['pivot'], ua['pts']['socket'], sh, el, ku, mirror=mir)
                    Mf, tf = card_matrix(fa['pts']['pivot'], fa['pts']['socket'], el, wr, kfa, mirror=mir)
                    khd = self.k(hd, 'wrist', 'tip', b.hand)
                    hdir = unit(wr - el) if np.linalg.norm(wr - el) > 1 else unit(P['tip' + s][0] - P['wr' + s][0])
                    mir_hd = (hd['faces'] != 0 and hd['faces'] != s_face) if prof else False
                    Mhd, thd = card_matrix(hd['pts']['wrist'], hd['pts']['tip'], wr, wr + hdir * 100, khd, mirror=mir_hd, axial=khd)
                    links += [('shoulder' + s, sh, apply(Mu, tu, ua['pts']['pivot'])),
                              ('elbow' + s, apply(Mu, tu, ua['pts']['socket']), apply(Mf, tf, fa['pts']['pivot'])),
                              ('wrist' + s, apply(Mf, tf, fa['pts']['socket']), apply(Mhd, thd, hd['pts']['wrist']))]
                    z = (fr['P']['el' + s][1] + fr['P']['wr' + s][1]) / 2
                    arm_ops[s] = (z, [img(hd, Mhd, thd), img(fa, Mf, tf), img(ua, Mu, tu)])

                # legs: IK from the bridge's hip brad to the (pinned) ankle brad
                fdrift = {'L': 0.0, 'R': 0.0}; fmiss = {'L': 0.0, 'R': 0.0}
                leg_ops = {}
                for s in 'LR':
                    key = (lambda n: n + '_' + s if (n + '_' + s) in V_ else n)
                    th_, sn = V_[key('thigh')], V_[key('shin')]
                    Hp = hipC[s]; A = fr['ankT' + s]
                    fs1 = np.linalg.norm(P['knee' + s][0] - P['hip' + s][0]) / (b.thigh * K)
                    fs2 = np.linalg.norm(P['ank' + s][0] - P['knee' + s][0]) / (b.shin * K)
                    fs1c, fs2c = max(0.5, min(1.0, fs1)), max(0.5, min(1.0, fs2))
                    squash.append(min(fs1c, fs2c))
                    l1, l2 = b.thigh * K * fs1c, b.shin * K * fs2c
                    d3 = P['knee' + s][0] - P['hip' + s][0]; e3 = P['ank' + s][0] - P['hip' + s][0]
                    bend = 1 if (e3[0] * d3[1] - e3[1] * d3[0]) < 0 else -1
                    Lm = (l1 + l2) * 0.995; dxx = abs(A[0] - Hp[0])
                    if dxx < Lm:
                        need[i] = max(need[i], (A[1] - Hp[1]) - math.sqrt(Lm * Lm - dxx * dxx)) if attempt == 0 else need[i]
                    # foreshortening is an estimate from the 3D skeleton; if the brads it must join are
                    # farther apart, give the cards back their length (up to full) before any stretch
                    dd = float(np.linalg.norm(A - Hp))
                    for _ in range(3):
                        if dd > (l1 + l2) * 0.999:
                            g_ = dd / (l1 + l2)
                            l1, l2 = min(b.thigh * K, l1 * g_), min(b.shin * K, l2 * g_)
                    knee, reached, fst = ik2(Hp, A, l1, l2, bend)
                    stretch_max = max(stretch_max, fst)
                    miss = np.linalg.norm(reached - A) / K
                    miss_max = max(miss_max, miss); fmiss[s] = miss
                    mir = prof and s_face < 0
                    kth = self.k(th_, 'pivot', 'socket', b.thigh); ksn = self.k(sn, 'pivot', 'socket', b.shin)
                    Mth, tth = card_matrix(th_['pts']['pivot'], th_['pts']['socket'], Hp, knee, kth, mirror=mir)
                    Msn, tsn = card_matrix(sn['pts']['pivot'], sn['pts']['socket'], knee, reached, ksn, mirror=mir)
                    fcard, Mft, tft = fr['foot'][s]
                    if np.linalg.norm(reached - A) > 1e-6:
                        # out of reach: the foot follows the leg (brad stays closed); the slip
                        # this causes is caught by the planted-drift check below
                        tft = tft + (reached - A)
                    links += [('hip' + s, Hp, apply(Mth, tth, th_['pts']['pivot'])),
                              ('knee' + s, apply(Mth, tth, th_['pts']['socket']), apply(Msn, tsn, sn['pts']['pivot'])),
                              ('ankle' + s, apply(Msn, tsn, sn['pts']['socket']), apply(Mft, tft, fcard['pts']['ankle']))]
                    z = (fr['P']['knee' + s][1] + fr['P']['ank' + s][1]) / 2
                    leg_ops[s] = (z, [img(fcard, Mft, tft), img(sn, Msn, tsn), img(th_, Mth, tth)])
                    # drift of the drawn sole while the source foot is down
                    # the SAME contact point (this frame's load point) measured on this frame's card and
                    # on last frame's card: its motion is the slide the audience sees
                    kind_ = ctype[s][i] or 'heel'
                    cp = card_contact(fcard, Mft, tft, kind_, fr['P'], s)
                    if i in spanset[s] and (i - 1) in spanset[s] and prev_contact[s] is not None \
                            and kind_ in kinds[s][i - 1]:
                        pc, pM, pt_, pP = prev_contact[s]
                        mv = np.linalg.norm(cp - card_contact(pc, pM, pt_, kind_, pP, s)) / K
                        if (pc['id'], np.linalg.det(pM) < 0) != (fcard['id'], np.linalg.det(Mft) < 0):
                            swap_jump.append(mv)
                        else:
                            drift[s].append(mv); fdrift[s] = mv
                    prev_contact[s] = (fcard, Mft, tft, P)

                # torso group (bridge, seat/skirt, torso, head)
                tz = (P['waist'][1] + P['neck'][1]) / 2
                torso_ops = []
                bridge_ops = [bridge_op] if bridge_op else []      # the bridge always sits under the thigh tabs
                if 'seat' in V_:
                    sc = V_['seat']
                    ks = (b.bridge + 0.35 * b.thigh) * K / max(1.0, sc['pts']['hem'][1] - sc['pts']['waist'][1])
                    hm = (hipC['L'] + hipC['R']) / 2
                    Ms, ts = card_matrix(sc['pts']['waist'], sc['pts']['hem'], waistC, waistC + unit(hm - waistC) * 100, ks, axial=ks)
                    torso_ops.append(img(sc, Ms, ts))
                if 'skirt' in V_:
                    sk = V_['skirt']
                    kk = (b.bridge + 0.95 * b.thigh) * K / max(1.0, sk['pts']['hem'][1] - sk['pts']['waist'][1])
                    # hang the skirt toward the mean of the two knees
                    kL = links[[l[0] for l in links].index('kneeL')][1]; kR = links[[l[0] for l in links].index('kneeR')][1]
                    kmid = (kL + kR) / 2
                    spread = abs(kL[0] - kR[0]) / (b.thigh * K)
                    girth = kk * (0.62 if prof else 1.0) * (1 + 0.35 * min(1.0, spread))
                    Mk, tk = card_matrix(sk['pts']['waist'], sk['pts']['hem'], waistC, kmid, girth, axial=kk)
                    torso_ops.append(img(sk, Mk, tk))
                torso_ops += head_ops          # under the torso, so the collar hides the neck tab
                torso_ops.append(img(tc, Mt, tt))

                # depth order: legs pushed back (jacket hem over the trouser tops), arms forward in front/back views
                if prof:
                    # a side-on puppet has a fixed stack: far arm, far leg, near leg, body, near arm
                    fa_ = 'L' if arm_ops['L'][0] > arm_ops['R'][0] else 'R'; na_ = 'R' if fa_ == 'L' else 'L'
                    fl_ = 'L' if leg_ops['L'][0] > leg_ops['R'][0] else 'R'; nl_ = 'R' if fl_ == 'L' else 'L'
                    groups = [(5, 0, arm_ops[fa_][1]), (4.5, 0, bridge_ops), (4, 0, leg_ops[fl_][1]), (3, 0, leg_ops[nl_][1]),
                              (2, 0, torso_ops), (1, 0, arm_ops[na_][1])]
                else:
                    groups = [(tz, 1, torso_ops), (1e6, 1, bridge_ops)]
                    for s in 'LR':
                        groups.append((leg_ops[s][0] + 14.0, 0, leg_ops[s][1]))
                        groups.append((arm_ops[s][0] - 6.0, 2, arm_ops[s][1]))
                groups.sort(key=lambda g_: -g_[0])
                far_shade = {}
                if prof:            # the far limbs of a profile puppet sit in shadow
                    for s in 'LR':
                        far_shade['leg' + s] = leg_ops[s][0] > leg_ops['R' if s == 'L' else 'L'][0]
                        far_shade['arm' + s] = arm_ops[s][0] > arm_ops['R' if s == 'L' else 'L'][0]
                    for s in 'LR':
                        for op in leg_ops[s][1] if far_shade['leg' + s] else []: op['shade'] = 0.35
                        for op in arm_ops[s][1] if far_shade['arm' + s] else []: op['shade'] = 0.35
                fl = cam.p(np.array([cam.c[0], 0, cam.c[2]]))[0][1]
                draw = [{'t': 'bg'}, {'t': 'floor', 'y': round(float(fl), 1)},
                        {'t': 'shadow', 'x': round(float(P['pelvis'][0][0]), 1),
                         'y': round(float(cam.p(np.array([T['pelvis'][0], 0, T['pelvis'][2]]))[0][1]), 1),
                         'rx': round(b.H * 0.28 * K / 2, 1), 'a': 0.6}]
                for g_ in groups: draw += g_[2]

                gaps = [(nm, float(np.linalg.norm(a_ - b_) / K)) for nm, a_, b_ in links]
                fg = max(gaps, key=lambda x: x[1])
                if fg[1] > worst_gap: worst_gap = fg[1]
                if fg[1] > TOL_BRAD: gap_frames.append(i)
                # drawn height: floor under the feet to the top of the head card
                top_pt = apply(Mh, th, hc['pts']['top'])
                sole_y = max(max(apply(fr['foot'][s][1], fr['foot'][s][2], fr['foot'][s][0]['pts'][k])[1] for k in ('heel', 'toe', 'sole')) for s in 'LR')
                heights.append((sole_y - top_pt[1]) / K)
                clip_frames.append({'f': i, 'draw': draw, 'view': fr['view'], 'head': hv,
                                    'dbg': {'pelvis': [[round(float(P['pelvis'][0][0]), 1), round(float(P['pelvis'][0][1]), 1)]],
                                            'gap': [fg[0], round(fg[1], 2)],
                                            'drift': [round(fdrift['L'], 2), round(fdrift['R'], 2)],
                                            'miss': [round(fmiss['L'], 2), round(fmiss['R'], 2)]}})

            if attempt == 0:
                nd = np.maximum(need, 0)
                win = np.array([max(nd[max(0, k - 4):k + 5]) for k in range(N)])
                ker = np.exp(-0.5 * (np.arange(-6, 7) / 2.5) ** 2); ker /= ker.sum()
                smv = np.convolve(np.pad(win, 6, mode='edge'), ker, mode='valid')
                dyv = np.maximum(nd, smv)
                if not dyv.any(): break
        # the source's own slide on the same contact frames (cm/frame, at the target's scale r)
        src_slide = 0.0
        for s_ in 'LR':
            for a, z in spans[s_]:
                for i in range(a + 1, z + 1):
                    if ctype[s_][i] != ctype[s_][i - 1]: continue
                    k_ = JI[(ctype[s_][i] or 'heel') + s_]
                    src_slide = max(src_slide, b.r * float(np.linalg.norm((frames[i]['j'][k_] - frames[i - 1]['j'][k_])[[0, 2]])))
        nswap = len(swap_jump)
        all_drift = drift['L'] + drift['R']
        worst_drift = max(all_drift) if all_drift else 0.0
        clip_problems = []
        if worst_drift > TOL_DRIFT:
            clip_problems.append('planted drift %.2f cm/frame > %.1f (source foot itself slides up to %.2f cm/frame on its contact frames)'
                                 % (worst_drift, TOL_DRIFT, src_slide))
        if worst_gap > TOL_BRAD: clip_problems.append('brad gap %.2f cm > %.1f on %d frames' % (worst_gap, TOL_BRAD, len(gap_frames)))
        if stretch_max > 1.005: clip_problems.append('leg cards stretched to %.0f%% on some frames to reach a planted foot' % (stretch_max * 100))
        if miss_max > 0.5: clip_problems.append('a pinned foot was out of reach by up to %.1f cm; the foot follows the leg there' % miss_max)
        sj = max(swap_jump) if swap_jump else 0.0
        if nswap and sj > TOL_DRIFT:
            clip_problems.append('%d planted-foot card swaps/flips (heel-up/toe-up state or mirror); drift is not counted on those '
                                 'frames, the sole jumps there by up to %.1f cm' % (nswap, sj))
        sq = min(squash) if squash else 1
        if sq < 0.6: clip_problems.append('limb card squashed to %.0f%% for foreshortening' % (sq * 100))
        views = sorted(set(f['view'] for f in clip_frames))
        lying = [i for i, fr in enumerate(F) if unit(fr['T']['neck'] - fr['T']['waist'])[1] < 0.55]
        if lying:
            clip_problems.append('%d frames with the torso >57deg from upright (on the floor): standing cards are rotated, '
                                 'the kit\'s lying/kneeling replacement cards are not used yet (frames %s)' % (len(lying), _ranges(lying)))
        if self.rig.get('force_view') == 'back':
            facing = sum(1 for fr in F if abs(fr['yr']) < 90)
            if facing: clip_problems.append('%d frames turn toward camera; back cards forced (face never shown)' % facing)
        if self.rig.get('front_for_profile') and any(f['side'] for f in F):
            clip_problems.append('no side-view body in this kit: front torso/limbs walk sideways with profile shoes and head')
        if V['actors'] and len(V['actors']) > 1:
            clip_problems.append('source has %d actors; only the lead (%s) is retargeted' % (len(V['actors']), V['actors'][0]['name']))
        stand_h = float(np.median(heights[:max(1, min(12, len(heights)))]))
        beats = arena.get('beats', []) if arena else []
        title = V['title']
        rel_root = os.path.relpath(SHOTS, os.path.join(OUT, self.name)).replace(os.sep, '/')
        clip = {
            'id': '%s__%s' % (act, self.name), 'act': act, 'character': self.name, 'variant': 'stage_anim',
            'title': title, 'family': arena.get('family') if arena else None,
            'situation': arena.get('situation') if arena else V.get('note'),
            'clock': {'fps': 24, 'frames': len(clip_frames)},
            'cm_px': round(K, 4),
            'image_root': 'shots/', 'image_paths': 'relative to this clip file (%s/ == shots/)' % rel_root,
            'images': {k: rel_root + '/' + v for k, v in images.items()},
            'floor': clip_frames[0]['draw'][1]['y'],
            'cast': [{'name': self.rig['title'], 'height_cm': b.H, 'cm_px': round(K, 4)}],
            'beats': beats,
            'technical': {
                'worst_planted_drift_cm_per_frame': round(worst_drift, 3), 'tolerance_planted_drift_cm_per_frame': TOL_DRIFT,
                'source_contact_slide_cm_per_frame': round(src_slide, 3),
                'worst_brad_gap_cm': round(worst_gap, 3), 'tolerance_brad_gap_cm': TOL_BRAD,
                'brad_gap_frames': len(gap_frames), 'max_leg_stretch': round(stretch_max, 3),
                'max_ankle_miss_cm': round(miss_max, 2), 'min_limb_axial': round(sq, 3),
                'drawn_height_cm': round(stand_h, 1), 'target_height_cm': b.H,
                'contact_frames': len(spanset['L']) + len(spanset['R']),
                'planted_card_swaps': nswap, 'swap_jump_max_cm': round(sj, 2),
                'views': views, 'pelvis_drop_max_cm': round(max(T['drop'] for T in T3), 1), 'screen_drop_max_cm': round(float(dyv.max()) / K, 1),
                'retarget_scale_r': round(b.r, 4),
                'segments_cm': {k: round(getattr(b, k), 1) for k in ('hip', 'knee', 'thigh', 'shin', 'ank_up', 'bridge', 'torso', 'head', 'uarm', 'farm', 'hand', 'foot', 'hipw', 'shw')},
                'result': 'pass' if not any(p.startswith(('planted', 'brad')) for p in clip_problems) else 'fail',
            },
            'problems': clip_problems,
            'ledger': [['source', 'Bolas bank %s (%s), actor A' % (act_to_t(act), title)],
                       ['retarget', 'shots/stage/anim/retarget.py'], ['rig', 'shots/stage/anim/rigs.py:%s' % self.name],
                       ['camera', 'yaw=%s elev=%s, K=%.3f px/cm (fixed for every stage clip)' % (V['view'].get('yaw'), V['view'].get('elev'), K)]],
            'frames': clip_frames,
        }
        return clip


DEFAULT = {
    'poet_tracksuit': ['ACT-001', 'ACT-003', 'ACT-008', 'ACT-017', 'ACT-024', 'ACT-002', 'ACT-007', 'ACT-013', 'ACT-019', 'ACT-023'],
    'poet_tshirt': ['ACT-001', 'ACT-003', 'ACT-008', 'ACT-017', 'ACT-024'],
    'young_poet': ['ACT-001', 'ACT-003', 'ACT-008', 'ACT-017', 'ACT-024'],
    'woman': ['ACT-001', 'ACT-003', 'ACT-017', 'ACT-024'],
    'ex': ['ACT-001', 'ACT-003', 'ACT-024'],
    'party_guest': ['ACT-001', 'ACT-017', 'ACT-019', 'ACT-024'],
}


def write_index():
    idx = []
    for ch in sorted(os.listdir(OUT)):
        d = os.path.join(OUT, ch)
        if not os.path.isdir(d): continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.json'): continue
            c = json.load(open(os.path.join(d, fn)))
            t = c['technical']
            idx.append({'id': c['id'], 'character': ch, 'act': c['act'], 'title': c['title'],
                        'frames': c['clock']['frames'], 'fps': c['clock']['fps'],
                        'path': 'clips/%s/%s' % (ch, fn), 'cm_px': c['cm_px'],
                        'result': t['result'], 'views': t['views'],
                        'problems': c['problems'],
                        'checks': {'planted_drift': t['worst_planted_drift_cm_per_frame'],
                                   'source_slide': t.get('source_contact_slide_cm_per_frame'),
                                   'swap_jump': t.get('swap_jump_max_cm'),
                                   'brad_gap': t['worst_brad_gap_cm'],
                                   'height_cm': t['drawn_height_cm'], 'target_height_cm': t['target_height_cm'],
                                   'leg_stretch': t['max_leg_stretch'], 'min_limb_axial': t['min_limb_axial']}})
    json.dump({'about': 'Acting Arena acts retargeted onto poem-kit cut-out characters (shots/stage/anim/retarget.py). '
                        'Image paths inside each clip are relative to the clip file. cm_px is the same for every clip, '
                        'so clips can be shown side by side at true relative scale.',
               'cm_px': round(K, 4), 'tolerances': {'planted_drift_cm_per_frame': TOL_DRIFT, 'brad_gap_cm': TOL_BRAD},
               'characters': {n: {'title': rigs.SPEC[n]['title'], 'height_cm': rigs.SPEC[n]['height_cm']} for n in rigs.SPEC},
               'clips': idx}, open(os.path.join(HERE, 'index.json'), 'w'), indent=1)
    return idx


def run(name, acts, max_frames=None):
    s = Solver(name)
    os.makedirs(os.path.join(OUT, name), exist_ok=True)
    for a in acts:
        c = s.solve(a, max_frames)
        json.dump(c, open(os.path.join(OUT, name, a + '.json'), 'w'), separators=(',', ':'))
        t = c['technical']
        print('%-15s %s %-28s drift %.2f gap %.2f h %.1f/%d stretch %.2f axial %.2f views %s  %s' % (
            name, a, c['title'][:28], t['worst_planted_drift_cm_per_frame'], t['worst_brad_gap_cm'],
            t['drawn_height_cm'], t['target_height_cm'], t['max_leg_stretch'], t['min_limb_axial'],
            ','.join(t['views']), '; '.join(c['problems'])))


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        for n, acts in DEFAULT.items(): run(n, acts)
    else:
        n = args[0]; acts = args[1:] or DEFAULT.get(n, ['ACT-001'])
        run(n, acts)
    write_index()
