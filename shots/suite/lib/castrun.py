"""Run one character (or the whole cast) through the standard Acting Arena battery and measure each take on the render.

    python3 shots/suite/lib/castrun.py --bank <dir with Bolas T###.json>  [ids...]  [--jobs 12]

Battery (Bolas Crash Lab motion bank, hartswf0/bolas):
  walk      T001 Heel, flat, ball, toe          locomotion, planted feet
  turn      T014 Quarter, half, whole turn      every view of the body in one take
  sit       T006 Sitting down, standing up      a chair sized to the actor
  reach     T080 Hanging a picture              two hands to sockets the SET owns (a frame at 140 cm)
  handoff   T046 The letter changes hands       hand meets hand with a partner
  fall      T108 Stand after a fall             down to the floor and up again

Pipeline per frame (one module, no hidden steps):
  1. retarget   the bank's 3D joints onto the character's own rest skeleton (its build, scaled to height_cm):
                bone directions from the motion, bone lengths from the character; root travel scaled by leg length.
  2. pin        planted feet (bank contact: heel or ball at y <= 1 cm) are pinned to where they landed; the leg is
                re-solved by two-bone IK, the pelvis lowered if the pin is out of reach.
  3. sockets    hands that the motion puts on a socket (the frame, the letter) are IK'd to it in 3D.
  4. project    orthographic camera of the bank vignette (yaw, elevation); S px per cm, the floor at a fixed line.
  5. cut-out    rigid cards chained brad to brad: torso first, limbs hung from the TORSO CARD's own sockets, legs and
                arms re-solved by 2D two-bone IK on the card lengths, a skirt/robe card carrying the knees in a slot.
  6. render     every card is warped once, composited; one alpha buffer per actor is kept for measuring.
  7. measure    on the render: foot slide, brad gap and brad holes, contact error, height drift, floor error,
                view-swap pop, balance. Thresholds are the Arena spec's (drift 0.6 cm/frame, brad 2 cm, balance 95 %).
"""
import argparse, json, math, os, subprocess, sys, time
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.dirname(HERE)
SHOTS = os.path.dirname(SUITE)
sys.path.insert(0, HERE)
import castkit as CK  # noqa: E402

OUT = os.path.join(SUITE, 'cast')
PARTS = json.load(open(os.path.join(SUITE, 'data', 'cast_parts.json')))['characters']

N = ['pelvis', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR', 'heelL', 'heelR', 'ballL', 'ballR', 'toeL', 'toeR',
     'spineMid', 'neckBase', 'chest', 'shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'wristL', 'wristR', 'headBase', 'head',
     'headTop', 'nose']
I = {n: i for i, n in enumerate(N)}
PARENT = {'hipL': 'pelvis', 'hipR': 'pelvis', 'spineMid': 'pelvis', 'chest': 'spineMid', 'neckBase': 'chest',
          'headBase': 'neckBase', 'head': 'headBase', 'headTop': 'head', 'nose': 'head', 'shoulderL': 'neckBase',
          'shoulderR': 'neckBase', 'elbowL': 'shoulderL', 'elbowR': 'shoulderR', 'wristL': 'elbowL', 'wristR': 'elbowR',
          'kneeL': 'hipL', 'kneeR': 'hipR', 'ankleL': 'kneeL', 'ankleR': 'kneeR', 'heelL': 'ankleL', 'heelR': 'ankleR',
          'ballL': 'ankleL', 'ballR': 'ankleR', 'toeL': 'ballL', 'toeR': 'ballR'}
ORDER = ['hipL', 'hipR', 'spineMid', 'chest', 'neckBase', 'headBase', 'head', 'headTop', 'nose', 'shoulderL', 'shoulderR',
         'elbowL', 'elbowR', 'wristL', 'wristR', 'kneeL', 'kneeR', 'ankleL', 'ankleR', 'heelL', 'heelR', 'ballL', 'ballR',
         'toeL', 'toeR']

BATTERY = [('walk', 'T001'), ('turn', 'T014'), ('sit', 'T006'), ('reach', 'T080'), ('handoff', 'T046'), ('fall', 'T108')]
TOL = dict(foot_slide=0.6, brad_gap=2.0, contact=3.0, height_drift=3.0, floor=2.0, balance=95.0)
W, H = 640, 360
FPS = 24


# ====================================================================== 1-3. retarget, pin, sockets (3D, cm)
def target_lengths(c, src0):
    """Bone lengths of the character (from its build's rest skeleton, scaled to its height) and of the source."""
    k = c['height_cm'] / CK.K.CHARS[c['build']]['height']
    J = {n: np.array(p, float) * k for n, p in CK.K.CHARS[c['build']]['J'].items()}
    d = lambda a, b: float(np.linalg.norm(J[a] - J[b]))
    S = {n: np.array(src0[I[n]], float) for n in N}
    ds = lambda a, b: float(np.linalg.norm(S[a] - S[b]))
    t = dict(thigh=d('hipL', 'kneeL'), shin=d('kneeL', 'ankleL'), ua=d('shoulderL', 'elbowL'), fa=d('elbowL', 'wristL'),
             ank_h=J['ankleL'][1], foot=J['toeL'][2] - J['heelL'][2], hip_w=abs(J['hipL'][0]), sh_w=d('shoulderL', 'neck'),
             torso=J['neck'][1] - J['hipL'][1], headneck=J['crown'][1] - J['neck'][1], hand=d('wristL', 'tipL'))
    s = dict(thigh=ds('hipL', 'kneeL'), shin=ds('kneeL', 'ankleL'), ua=ds('shoulderL', 'elbowL'), fa=ds('elbowL', 'wristL'),
             ank_h=S['ankleL'][1], foot=ds('heelL', 'toeL'), hip_w=ds('hipL', 'hipR') / 2, sh_w=ds('shoulderL', 'neckBase'),
             torso=S['neckBase'][1] - S['pelvis'][1], headneck=S['headTop'][1] - S['neckBase'][1])
    return t, s, k


def bone_scale(bone, t, s):
    p = PARENT[bone]
    if bone in ('kneeL', 'kneeR'): return t['thigh'] / s['thigh']
    if bone in ('ankleL', 'ankleR'): return t['shin'] / s['shin']
    if bone in ('elbowL', 'elbowR'): return t['ua'] / s['ua']
    if bone in ('wristL', 'wristR'): return t['fa'] / s['fa']
    if bone in ('hipL', 'hipR'): return t['hip_w'] / s['hip_w']
    if bone in ('shoulderL', 'shoulderR'): return t['sh_w'] / s['sh_w']
    if bone in ('spineMid', 'chest', 'neckBase'): return t['torso'] / s['torso']
    if bone in ('headBase', 'head', 'headTop', 'nose'): return t['headneck'] / s['headneck']
    if p.startswith(('ankle', 'ball')): return None     # feet: handled in the foot frame
    return 1.0


def two_bone(a, target, l1, l2, pole):
    """3D two-bone IK: returns (mid, end, reached)."""
    v = target - a
    d = float(np.linalg.norm(v))
    reach = d <= (l1 + l2) * 0.9995
    d = min(max(d, abs(l1 - l2) + 1e-3), (l1 + l2) * 0.9995)
    u = v / (np.linalg.norm(v) + 1e-9)
    end = a + u * d
    x = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - x * x))
    pv = pole - a
    pv = pv - u * float(pv @ u)
    if np.linalg.norm(pv) < 1e-6:
        pv = np.array([0.0, 0.0, 1.0]) - u * u[2]
    pv /= np.linalg.norm(pv) + 1e-9
    return a + u * x + pv * h, end, reach


def retarget(V, ai, c, origin=None, sockets=None):
    """The bank actor ai, re-proportioned to character c. Returns per-frame joints (F,26,3), contacts, facing."""
    frames = [list(fr['a'].values())[ai] for fr in V['frames']]
    src0 = frames[0]['j']
    t, s, k = target_lengths(c, src0)
    s_leg = (t['thigh'] + t['shin'] + t['ank_h']) / (s['thigh'] + s['shin'] + s['ank_h'])
    r_len, r_h = t['foot'] / s['foot'], t['ank_h'] / s['ank_h']
    if origin is None:
        p0 = np.array(src0[0], float)
        origin = np.array([p0[0], 0.0, p0[2]])
    out, cont, fwds, srcs = [], [], [], []
    for A in frames:
        S = {n: np.array(A['j'][I[n]], float) for n in N}
        T = {}
        T['pelvis'] = np.array([origin[0] + (S['pelvis'][0] - origin[0]) * s_leg, S['pelvis'][1] * s_leg,
                                origin[2] + (S['pelvis'][2] - origin[2]) * s_leg])
        for b in ORDER:
            p = PARENT[b]
            sc = bone_scale(b, t, s)
            if sc is None:
                # foot points: along the foot by the foot-length ratio, across it by the ankle-height ratio
                side = b[-1]
                f = S['toe' + side] - S['heel' + side]
                f[1] = 0
                f /= np.linalg.norm(f) + 1e-9
                v = S[b] - S[p]
                along = float(v @ f)
                T[b] = T[p] + f * along * r_len + (v - f * along) * r_h
            else:
                T[b] = T[p] + (S[b] - S[p]) * sc
        out.append(T)
        cont.append({sd: bool(S['heel' + sd][1] <= 1.0 or S['ball' + sd][1] <= 1.0) for sd in 'LR'})
        fwds.append(np.array(A.get('fwd', [0, 0, 1]), float))
        srcs.append(S)
    # 2. pin planted feet
    pins = {'L': None, 'R': None}
    resid = np.zeros(len(out))
    drop = np.zeros(len(out))
    for side in 'LR':
        pass
    for f, T in enumerate(out):
        S = srcs[f]
        targets = {}
        for side in 'LR':
            if not cont[f][side]:
                pins[side] = None
                continue
            kind = 'ball' if S['ball' + side][1] <= 1.0 else 'heel'
            pt = T[kind + side]
            if pins[side] is None or pins[side][0] != kind:
                pins[side] = (kind, np.array([pt[0], 0.0, pt[2]]))
            pin = pins[side][1]
            targets[side] = pin - (pt - T['ankle' + side])
            targets[side][1] = T['ankle' + side][1] - pt[1]          # the contact point exactly on the floor
        # pelvis drop if a pinned ankle is out of reach
        need = 0.0
        for side, at in targets.items():
            hip = T['hip' + side]
            L = (t['thigh'] + t['shin']) * 0.999
            hz = math.hypot(at[0] - hip[0], at[2] - hip[2])
            if hz < L:
                y_ok = at[1] + math.sqrt(L * L - hz * hz)
                need = max(need, hip[1] - y_ok)
        drop[f] = max(0.0, need)
    # smooth the drop so the body does not jitter (max-filter then a short blur keeps every pin reachable)
    if drop.any():
        mx = np.array([drop[max(0, i - 2):i + 3].max() for i in range(len(drop))])
        drop = np.convolve(np.pad(mx, 2, mode='edge'), np.ones(5) / 5, mode='valid')
        drop = np.maximum(drop, mx * 0.98)
    pins = {'L': None, 'R': None}
    for f, T in enumerate(out):
        S = srcs[f]
        if drop[f] > 0:
            for n in N:
                if not n.startswith(('knee', 'ankle', 'heel', 'ball', 'toe')):
                    T[n] = T[n] - np.array([0, drop[f], 0])
        for side in 'LR':
            hip = T['hip' + side]
            if cont[f][side]:
                kind = 'ball' if S['ball' + side][1] <= 1.0 else 'heel'
                pt = T[kind + side] - np.array([0, 0 if drop[f] == 0 else 0, 0])
                if pins[side] is None or pins[side][0] != kind:
                    pins[side] = (kind, np.array([pt[0], 0.0, pt[2]]))
                pin = pins[side][1]
                foot_off = {n: T[n + side] - T['ankle' + side] for n in ('heel', 'ball', 'toe')}
                at = pin - foot_off[kind]
                at[1] = -foot_off[kind][1]
            else:
                pins[side] = None
                foot_off = {n: T[n + side] - T['ankle' + side] for n in ('heel', 'ball', 'toe')}
                at = T['ankle' + side] - np.array([0, drop[f], 0])
                low = min(at[1] + foot_off[n][1] for n in foot_off)
                if low < 0:
                    at[1] -= low                     # a swinging foot never goes through the floor
            pole = hip + (T['knee' + side] - hip) * 2 + np.array(fwds[f]) * 10
            kn, an, ok = two_bone(hip, at, t['thigh'], t['shin'], pole)
            if not ok:
                resid[f] = max(resid[f], float(np.linalg.norm(an - at)))
            T['knee' + side], T['ankle' + side] = kn, an
            for n in ('heel', 'ball', 'toe'):
                T[n + side] = an + foot_off[n]
    # 3. hands to sockets
    reach_miss = np.zeros(len(out))
    if sockets:
        for f, T in enumerate(out):
            for side, P in (sockets.get(f) or {}).items():
                sh = T['shoulder' + side]
                pole = sh + (T['elbow' + side] - sh) * 2 + np.array([0, -10.0, 0])
                el, wr, ok = two_bone(sh, np.asarray(P, float), t['ua'], t['fa'], pole)
                T['elbow' + side], T['wrist' + side] = el, wr
                reach_miss[f] = max(reach_miss[f], float(np.linalg.norm(wr - np.asarray(P, float))))
    J = np.array([[T[n] for n in N] for T in out])
    return dict(J=J, contact=cont, fwd=fwds, src=srcs, k=k, s_leg=s_leg, t=t, drop=drop, pin_resid=resid,
                reach_miss=reach_miss, origin=origin)


# ====================================================================== 4. camera
class Cam:
    def __init__(self, view, yaw=None, zoom_mul=1.0):
        self.yaw = (view.get('yaw', -22) if yaw is None else yaw)
        y, e = math.radians(self.yaw), math.radians(view.get('elev', 8))
        self.cy, self.sy, self.ce, self.se = math.cos(y), math.sin(y), math.cos(e), math.sin(e)
        self.c = [view.get('x', 0), 92.0, view.get('z', 0)]
        self.S = H * 0.80 / 230 * view.get('zoom', 1.0) * zoom_mul      # px per cm
        self.floor = self.proj(np.array([self.c[0], 0, self.c[2]]))[1]

    def proj(self, p):
        x, y, z = p[0] - self.c[0], p[1] - self.c[1], p[2] - self.c[2]
        x1, z1 = x * self.cy - z * self.sy, x * self.sy + z * self.cy
        y2, z2 = y * self.ce - z1 * self.se, y * self.se + z1 * self.ce
        return np.array([W / 2 + x1 * self.S, H * 0.50 - y2 * self.S, z2])

    def facing(self, fwd):
        fx = fwd[0] * self.cy + fwd[2] * self.sy
        fz = -fwd[0] * self.sy + fwd[2] * self.cy
        return math.degrees(math.atan2(fx, fz)), fx      # 0 = toward camera; |180| = away


# ====================================================================== 5. cut-out solve (2D)
def rot(th):
    return np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])


def place(card_a, card_b, world_a, world_dir, s, flip=False):
    """Uniform-scale card matrix: card point card_a on world_a, the card's a->b axis along world_dir."""
    F = np.diag([-1.0, 1.0]) if flip else np.eye(2)
    cv_ = F @ (np.asarray(card_b, float) - np.asarray(card_a, float))
    th = math.atan2(world_dir[1], world_dir[0]) - math.atan2(cv_[1], cv_[0])
    M = s * rot(th) @ F
    t = np.asarray(world_a, float) - M @ np.asarray(card_a, float)
    return np.hstack([M, t[:, None]])


def apply(M, p):
    return M[:, :2] @ np.asarray(p, float) + M[:, 2]


def ik2d(a, target, l1, l2, bend_hint):
    v = np.asarray(target, float) - a
    d0 = float(np.linalg.norm(v))
    d = min(max(d0, abs(l1 - l2) + 1e-3), (l1 + l2) * 0.9999)
    u = v / (d0 + 1e-9)
    x = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - x * x))
    n = np.array([-u[1], u[0]])
    sgn = 1.0 if float(n @ (np.asarray(bend_hint, float) - a)) >= 0 else -1.0
    mid = a + u * x + n * h * sgn
    end = a + u * d
    return mid, end, d0 - d


VIEW_BANDS = [('front', 25), ('threequarter', 65), ('profile', 115), ('threequarter_back', 155), ('back', 181)]


def pick_view(ang, have, prev=None, back_only=False):
    a = abs(ang)
    if back_only:
        v = 'back' if a > 150 else 'threequarter_back'
        return v if v in have else 'back'
    want = next(v for v, lim in VIEW_BANDS if a <= lim)
    if prev and prev in have:
        # hysteresis: keep the previous view while within 8 deg of its band
        lo = {'front': 0, 'threequarter': 25, 'profile': 65, 'threequarter_back': 115, 'back': 155}[prev]
        hi = dict(VIEW_BANDS)[prev]
        if lo - 8 <= a <= hi + 8:
            return prev
    if want in have:
        return want
    fall = {'threequarter': ['front', 'profile'] if a < 45 else ['profile', 'front'],
            'threequarter_back': ['back', 'profile'] if a > 135 else ['profile', 'back'],
            'front': ['threequarter', 'profile'], 'back': ['threequarter_back', 'profile'], 'profile': ['threequarter', 'front']}[want]
    for v in fall:
        if v in have:
            return v
    return 'profile'


class Puppet:
    """One character's cards and the cut-out solve."""

    def __init__(self, cid, S):
        self.c = CK.BY_ID[cid]
        self.P = PARTS[cid]
        self.S = S
        self.k = self.P['k']
        self.skirt = self.P.get('rig') == 'skirt'
        self.pitch = {}
        self.views = [v for v in self.P['views'] if v in self.P['heads'] or self.c.get('code_head')]
        if self.c.get('back_only'):
            self.views = [v for v in self.views if v in ('back', 'threequarter_back')]

    def scale(self, part):
        return self.S * self.k / part['px_per_cm']

    def solve(self, P2, view, flip, plant, sockets2=None):
        """P2: dict joint -> projected (x, y). Returns ordered draw ops [(file, M, far, role)] and measure points."""
        V = self.P['views'][view]
        ops, pts, gaps = [], {}, []
        far_side = None
        # which side is far: the larger camera z
        zs = {s: (P2['shoulder' + s][2] + P2['hip' + s][2]) for s in 'LR'}
        far_side = 'L' if zs['L'] > zs['R'] else 'R'
        near_side = 'R' if far_side == 'L' else 'L'
        xy = lambda n: np.asarray(P2[n][:2], float)
        hipmid = (xy('hipL') + xy('hipR')) / 2
        neck = xy('neckBase')
        T = V['torso']
        s_t = self.scale(T)
        hip_c = T['sockets'].get('hipL') if not self.skirt else T['B']
        if view != 'profile' and not self.skirt and 'hipR' in T['sockets']:
            hip_c = list((np.array(T['sockets']['hipL']) + np.array(T['sockets']['hipR'])) / 2)
        Mt = place(hip_c, T['A'], hipmid, neck - hipmid, s_t, flip)
        neck_top = apply(Mt, T['A'])
        # collar tuck: the head's neck tab is pinned 0.8 cm INSIDE the collar (and the brad 4 % up the tab), so the brad goes through both cards
        tuck = (apply(Mt, T['B']) - neck_top)
        neck_w = neck_top + tuck / (np.linalg.norm(tuck) + 1e-9) * 0.8 * self.k * self.S
        socks = {k: apply(Mt, v) for k, v in T['sockets'].items()}
        if view == 'profile':
            socks['shoulderR'] = socks['shoulderL']
            socks['hipR'] = socks.get('hipL', apply(Mt, T['B']))
        if self.skirt:
            socks['hipL'] = socks['hipR'] = apply(Mt, T['B'])
        if view in ('profile', 'threequarter', 'threequarter_back'):
            # one card, two shoulders: the far one sits behind the card by the skeleton's own projected width
            for kind in ('shoulder', 'hip'):
                if kind + 'L' in socks and np.allclose(socks[kind + 'L'], socks[kind + 'R']):
                    mid = (xy(kind + 'L') + xy(kind + 'R')) / 2
                    base = socks[kind + 'L'].copy()
                    for s_ in 'LR':
                        socks[kind + s_] = base + (xy(kind + s_) - mid)
                    socks['_' + kind] = True
        # front/back: give each limb the torso socket nearest its joint
        def sock_for(kind, side):
            if socks.get('_' + kind):
                return socks[kind + side]
            cands = [socks[kind + s] for s in 'LR' if kind + s in socks]
            j = xy(kind + side)
            return min(cands, key=lambda q: np.linalg.norm(q - j))

        def limb_card(name, side):
            nm = f'{name}.{side}'
            if view == 'profile':
                return V.get(nm) or V.get(f'{name}.L')
            return V.get(nm) or V.get(f'{name}.{"L" if side == "R" else "R"}')

        def arm(side, far):
            ua, fa, hd = limb_card('uarm', side), limb_card('farm', side), limb_card('hand', side)
            sh = sock_for('shoulder', side)
            l1 = ua['len_cm'] * self.k * self.S
            l2 = fa['len_cm'] * self.k * self.S
            tgt = xy('wrist' + side)
            if sockets2 and side in sockets2:
                # the hand's middle on the socket: wrist target pulled back along the hand
                hl = hd['len_cm'] * self.k * self.S
                d = tgt - xy('elbow' + side)
                d /= np.linalg.norm(d) + 1e-9
                tgt = np.asarray(sockets2[side], float) - d * hl * 0.5
            el, wr, miss = ik2d(sh, tgt, l1, l2, xy('elbow' + side))
            hand_dir = wr - el
            m_ua = place(ua['A'], ua['B'], sh, el - sh, self.scale(ua), flip)
            m_fa = place(fa['A'], fa['B'], el, wr - el, self.scale(fa), flip)
            m_hd = place(hd['A'], hd['B'], wr, hand_dir, self.scale(hd), flip)
            gaps.append(np.linalg.norm(apply(m_ua, ua['B']) - apply(m_fa, fa['A'])))
            gaps.append(np.linalg.norm(apply(m_fa, fa['B']) - apply(m_hd, hd['A'])))
            gaps.append(np.linalg.norm(apply(m_ua, ua['A']) - sh))
            pts['hand' + side] = apply(m_hd, np.array(hd['A']) + 0.55 * (np.array(hd['B']) - np.array(hd['A'])))
            pts['hseg' + side] = (apply(m_hd, hd['A']), apply(m_hd, hd['B']))
            pts['brads'] += [('shoulder' + side, sh), ('elbow' + side, el), ('wrist' + side, wr)]
            pts['ikmiss'] = max(pts.get('ikmiss', 0), miss); pts.setdefault('ikd', {})['arm' + side] = round(miss, 1)
            return [(hd['file'], m_hd, far, 'hand'), (fa['file'], m_fa, far, 'farm'), (ua['file'], m_ua, far, 'uarm')]

        def leg(side, far, skirt_m=None, skirt_card=None):
            sn, ft = limb_card('shin', side), limb_card('foot', side)
            l2 = sn['len_cm'] * self.k * self.S
            s_ft = self.scale(ft)
            side_on = view == 'profile'      # 3/4 cards were painted into the FRONT ghosts: their feet stand upright
            if side_on:
                # a card does not foreshorten: orient the foot by its TRUE pitch (3D), and only take the
                # left/right sense from the screen, so a foot pointing at the camera is not driven through the floor
                fd2 = xy('toe' + side) - xy('ankle' + side)
                sgn = (-1.0 if flip else 1.0)
                if abs(fd2[0]) > 0.3 * (np.linalg.norm(fd2) + 1e-9):
                    sgn = 1.0 if fd2[0] > 0 else -1.0
                pitch = self.pitch.get(side, 0.0)
                fd = np.array([sgn * math.cos(pitch), math.sin(pitch)])
                ff = sgn < 0          # the shoe is mirrored by where IT points, or a mirrored card turned 180 deg lands upside down
            else:
                fd, ff = np.array([0.0, 1.0]), False
            heel, toe, A_ = (np.array(ft[k_], float) for k_ in ('heel', 'toe', 'A'))
            cpt = {'heel': heel, 'ball': heel + 0.72 * (toe - heel), 'toe': toe} if side_on else \
                  {k_: (heel + toe) / 2 for k_ in ('heel', 'ball', 'toe')}
            planted = plant.get(side)
            if planted:
                # the planted foot is the root of the leg: its contact point stays on the floor where it landed
                m_ft = place(cpt[planted], cpt[planted] + (toe - A_), xy(planted + side), fd, s_ft, ff)
                at = apply(m_ft, A_)
            else:
                at = xy('ankle' + side)
            out = []
            if self.skirt:
                # the knee rides in a slot along the hem: pick the slot point the shin can best reach the ankle from
                # the knee brad sits 4 cm above the hem (the template's knee + 4 cm), inside the cloth
                hc = np.array(skirt_card['B'], float) + (np.array(skirt_card['A'], float) - np.array(skirt_card['B'], float)) * \
                    (4.0 / max(1e-6, skirt_card['len_cm']))
                half = 0.42 * (skirt_card['ink'][2] - skirt_card['ink'][0])
                best = None
                for u in np.linspace(-1, 1, 21):
                    p = apply(skirt_m, hc + np.array([u * half, 0]))
                    e = abs(np.linalg.norm(at - p) - l2)
                    if best is None or e < best[0]:
                        best = (e, p)
                kn = best[1]
                if planted:
                    pts['skirt_need'] = max(pts.get('skirt_need', 0.0), float(np.linalg.norm(at - kn)) - l2)
                d = at - kn
                an = kn + d / (np.linalg.norm(d) + 1e-9) * l2
                miss = best[0]
            else:
                th = limb_card('thigh', side)
                hp = sock_for('hip', side)
                l1 = th['len_cm'] * self.k * self.S
                kn, an, miss = ik2d(hp, at, l1, l2, xy('knee' + side))
                m_th = place(th['A'], th['B'], hp, kn - hp, self.scale(th), flip)
                out.append((th['file'], m_th, far, 'thigh'))
                gaps.append(np.linalg.norm(apply(m_th, th['B']) - kn))
                gaps.append(np.linalg.norm(apply(m_th, th['A']) - hp))
                pts['brads'].append(('hip' + side, hp))
            m_sn = place(sn['A'], sn['B'], kn, an - kn, self.scale(sn), flip)
            if not planted:
                m_ft = place(A_, toe, an, fd, s_ft, ff)
            g = float(np.linalg.norm(apply(m_sn, sn['B']) - apply(m_ft, A_)))
            gaps.append(g)
            pts.setdefault('gapd', {})['ankle' + side] = g
            pts['brads'] += [('knee' + side, kn), ('ankle' + side, apply(m_ft, A_))]
            pts['ikmiss'] = max(pts.get('ikmiss', 0), miss); pts.setdefault('ikd', {})['leg' + side] = round(float(miss), 1)
            pts['foot' + side] = {k_: apply(m_ft, v_) for k_, v_ in cpt.items()}
            pts['foot' + side]['sole'] = [apply(m_ft, heel), apply(m_ft, toe)]
            return [(ft['file'], m_ft, far, 'foot'), (sn['file'], m_sn, far, 'shin')] + out[::-1]

        pts['brads'] = [('neck', neck_w)]
        skirt_ops = []
        skirt_m = skirt_card = None
        if self.skirt:
            skirt_card = V['pelvis']
            waist = apply(Mt, T['B']) + (neck_w - apply(Mt, T['B'])) / (np.linalg.norm(neck_w - apply(Mt, T['B'])) + 1e-9) * 6 * self.k * self.S
            down = -(neck_w - waist)
            th_dirs = [xy('knee' + s) - xy('hip' + s) for s in 'LR']
            mean = th_dirs[0] / (np.linalg.norm(th_dirs[0]) + 1e-9) + th_dirs[1] / (np.linalg.norm(th_dirs[1]) + 1e-9)
            a_down = math.atan2(down[1], down[0])
            a_mean = math.atan2(mean[1], mean[0])
            dlt = (a_mean - a_down + math.pi) % (2 * math.pi) - math.pi
            dlt = max(-math.radians(100), min(math.radians(100), dlt))
            sd = np.array([math.cos(a_down + dlt), math.sin(a_down + dlt)])
            skirt_m = place(skirt_card['A'], skirt_card['B'], waist, sd, self.scale(skirt_card), flip)
            skirt_ops = [(skirt_card['file'], skirt_m, False, 'skirt')]
            pts['skirt_turn_deg'] = math.degrees(dlt)
        bridge_ops = []
        hipc = apply(Mt, T['B'])
        waist2 = hipc + (neck_w - hipc) / (np.linalg.norm(neck_w - hipc) + 1e-9) * 6 * self.k * self.S
        if not self.skirt and 'bridge' in V:
            bc = V['bridge']
            bridge_ops = [(bc['file'], place(bc['A'], bc['B'], waist2, hipc - neck_w, self.scale(bc), flip), False, 'bridge')]
        if 'overlay_skirt' in V:
            # a skirt that does not carry the knees: it hangs from the waist and follows the mean thigh, clamped
            oc = V['overlay_skirt']
            down = hipc - neck_w
            th_dirs = [xy('knee' + s_) - xy('hip' + s_) for s_ in 'LR']
            mean = sum(d_ / (np.linalg.norm(d_) + 1e-9) for d_ in th_dirs)
            a_down, a_mean = math.atan2(down[1], down[0]), math.atan2(mean[1], mean[0])
            dlt = (a_mean - a_down + math.pi) % (2 * math.pi) - math.pi
            dlt = max(-math.radians(25), min(math.radians(25), dlt))
            a_sk = a_down + dlt
            sd = np.array([math.cos(a_sk), math.sin(a_sk)])
            skirt_ops = [(oc['file'], place(oc['A'], oc['B'], waist2, sd, self.scale(oc), flip), False, 'skirt')]
            exits = [abs((math.atan2(d_[1], d_[0]) - a_sk + math.pi) % (2 * math.pi) - math.pi) for d_ in th_dirs]
            pts['thigh_exit_deg'] = max(0.0, math.degrees(max(exits)) - 14.0)
        # head
        hd = self.P['heads'].get(view) if not self.c.get('code_head') else None
        top = xy('headTop')
        hdir = top - neck
        if hd:
            m_h = place(hd['neck'], hd['crown'], neck_w, hdir, self.S * self.k / hd['px_per_cm'], flip)
            head_op = (hd['file'], m_h, False, 'head')
            pts['head_top'] = apply(m_h, hd['crown'])
        else:
            ch = code_head(self.c, view)
            s_h = self.S * self.k / ch['px_per_cm']
            m_h = place(ch['neck'], ch['crown'], neck_w, hdir, s_h, flip)
            head_op = (ch['key'], m_h, False, 'head')
            pts['head_top'] = apply(m_h, ch['crown'])
        torso_op = (T['file'], Mt, False, 'torso')
        wings = []
        if self.c.get('wings'):
            wings = wing_ops(self, Mt, T, view, flip, neck_w, apply(Mt, T['B']))
        # z-order per view
        if view in ('profile', 'threequarter', 'threequarter_back'):
            seq = [w for w in wings if w[2]] + arm(far_side, True) + bridge_ops + leg(far_side, True, skirt_m, skirt_card) + \
                  leg(near_side, False, skirt_m, skirt_card) + skirt_ops
            seq += ([head_op, torso_op] if view != 'threequarter_back' else [torso_op, head_op])
            seq += [w for w in wings if not w[2]] + arm(near_side, False)
        elif view == 'front':
            seq = wings + bridge_ops + leg('L', False, skirt_m, skirt_card) + leg('R', False, skirt_m, skirt_card) + skirt_ops + \
                  [head_op, torso_op] + arm('L', False) + arm('R', False)
        else:   # back: the head covers the collar, the arms hang behind the shoulders' outline
            seq = bridge_ops + leg('L', False, skirt_m, skirt_card) + leg('R', False, skirt_m, skirt_card) + skirt_ops + \
                  arm('L', False) + arm('R', False) + [torso_op, head_op] + wings
        pts['gap_px'] = max(gaps) if gaps else 0.0
        return seq, pts


# ---------------------------------------------------------------- code-drawn parts (dummy heads; nothing painted is faked)
_CODE = {}


def code_head(c, view):
    key = f"code:{c['id']}:{view}"
    if key in _CODE:
        return _CODE[key]
    build = c['build']
    J = CK.K.CHARS[build]['J']
    r = J['crown'][1] - J['head'][1]
    ppc = 10.0
    R = r * 1.05 * ppc
    w, h = int(R * 2.6), int(R * 3.0 + 6 * ppc)
    im = np.zeros((h, w, 4), np.uint8)
    cx, cy = w // 2, int(R * 0.9 + R)
    col = c['code_head']['color'][::-1]
    cv2.ellipse(im, (cx, cy), (int(R * 0.95), int(R)), 0, 0, 360, (*col, 255), -1, cv2.LINE_AA)
    cv2.ellipse(im, (cx, cy), (int(R * 0.95), int(R)), 0, 0, 360, (20, 18, 26, 255), 3, cv2.LINE_AA)
    cv2.rectangle(im, (cx - int(R * .25), cy + int(R * .8)), (cx + int(R * .25), h - 2), (40, 40, 40, 255), -1)
    if view != 'back':
        ex = cx + (int(R * .45) if view in ('profile', 'threequarter') else 0)
        for dx in ((0,) if view == 'profile' else (-int(R * .3), int(R * .3))):
            cv2.circle(im, (ex + dx, cy - int(R * .1)), max(3, int(R * .09)), (20, 18, 26, 255), -1, cv2.LINE_AA)
        cv2.line(im, (ex - int(R * .2), cy + int(R * .4)), (ex + int(R * .15), cy + int(R * .42)), (20, 18, 26, 255), 3, cv2.LINE_AA)
    # crash target on the side
    if view in ('profile', 'threequarter'):
        tc = (cx - int(R * .25), cy)
        cv2.circle(im, tc, int(R * .28), (20, 18, 26, 255), -1)
        cv2.ellipse(im, tc, (int(R * .28), int(R * .28)), 0, 0, 90, (*col, 255), -1)
        cv2.ellipse(im, tc, (int(R * .28), int(R * .28)), 0, 180, 270, (*col, 255), -1)
    topk = c['code_head']['top']
    if topk == 'antenna':
        cv2.line(im, (cx, cy - int(R)), (cx, cy - int(R * 1.7)), (20, 18, 26, 255), 4)
        cv2.circle(im, (cx, cy - int(R * 1.75)), int(R * .14), (60, 60, 230, 255), -1, cv2.LINE_AA)
    elif topk == 'fin':
        pts = np.array([[cx - int(R * .3), cy - int(R * .92)], [cx + int(R * .1), cy - int(R * 1.5)], [cx + int(R * .3), cy - int(R * .9)]])
        cv2.fillPoly(im, [pts], (200, 120, 40, 255), cv2.LINE_AA)
    elif topk == 'bow':
        cv2.ellipse(im, (cx - int(R * .2), cy - int(R * 1.05)), (int(R * .2), int(R * .12)), 0, 0, 360, (60, 40, 220, 255), -1)
        cv2.ellipse(im, (cx + int(R * .2), cy - int(R * 1.05)), (int(R * .2), int(R * .12)), 0, 0, 360, (60, 40, 220, 255), -1)
    rgba = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
    ys = np.where(rgba[:, :, 3] > 0)[0]
    crown_y = cy - int(R)
    ppc_ = (h - 3 - crown_y) / (2 * r * 1.08 + 6)
    tab_needed = (J['head'][1] - r * 1.08) - J['neck'][1]
    rec = {'key': key, 'img': rgba, 'neck': [cx, h - 3 - max(0.0, 6 - tab_needed) * ppc_], 'crown': [cx, crown_y], 'px_per_cm': ppc_}
    _CODE[key] = rec
    return rec


def wing_ops(pup, Mt, T, view, flip, neck_w, hip_w):
    """Wings: their own cards, pinned at the shoulder blade (25 % down the torso), scaled to 1.35 x torso length
    (the rig library's canonical table), drawn behind the body except in the back view."""
    W_ = pup.P.get('wings', {})
    torso_len = np.linalg.norm(hip_w - neck_w)
    blade = neck_w + (hip_w - neck_w) * 0.25
    down = (hip_w - neck_w) / (torso_len + 1e-9)
    ops = []
    for s in ('L', 'R'):
        rec = W_.get(f'back.{s}') or W_.get(f'front.{s}')
        if not rec:
            continue
        x0, y0, x1, y1 = rec['ink']
        hgt = y1 - y0
        sc = 1.35 * torso_len / max(1, hgt)
        a = [x0 + (x1 - x0) * (0.85 if s == 'L' else 0.15), y0 + hgt * 0.15]
        b = [a[0], y1]
        if view == 'profile':
            if s == 'R':
                continue
            m = place(a, b, blade + np.array([(-6 if not flip else 6), 0]), down, sc, flip)
            ops.append((rec['file'], m, True, 'wing'))
        else:
            off = np.array([(1 if s == 'L' else -1) * 0.15 * torso_len, 0])
            m = place(a, b, blade + off, down, sc, False)
            ops.append((rec['file'], m, view != 'back', 'wing'))
    return ops


# ====================================================================== 6. render
class Canvas:
    def __init__(self):
        self.cache = {}

    def card(self, key, s, far, tint, alpha):
        ck = (key, round(s, 4), far, tint, alpha)
        if ck in self.cache:
            return self.cache[ck]
        if key.startswith('code:'):
            img = _CODE[key]['img']
        else:
            img = cv2.cvtColor(cv2.imread(os.path.join(SHOTS, key), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)
        pre = min(1.0, max(0.05, s * 3.0))
        if pre < 1.0:
            img = cv2.resize(img, (max(1, int(img.shape[1] * pre)), max(1, int(img.shape[0] * pre))), interpolation=cv2.INTER_AREA)
        f = img.astype(np.float32) / 255.0
        rgb, a = f[:, :, :3], f[:, :, 3:4]
        if tint:
            g = rgb.mean(2, keepdims=True)
            rgb = 0.35 * rgb + 0.65 * g * (np.array(tint, np.float32) / 200.0)
        if far:
            rgb = rgb * 0.72
        a = a * alpha
        prem = np.concatenate([rgb * a, a], 2)
        prem = cv2.copyMakeBorder(prem, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=0)
        self.cache[ck] = (prem, pre)
        return self.cache[ck]

    def draw(self, buf, abuf, key, M, far=False, tint=None, alpha=1.0):
        s = float(math.sqrt(abs(np.linalg.det(M[:, :2]))))
        prem, pre = self.card(key, s, far, tint, alpha)
        Mi = M.copy()
        Mi[:, :2] = M[:, :2] / pre
        Mi[:, 2] = M[:, 2] - Mi[:, :2] @ np.array([2.0, 2.0])
        h, w = prem.shape[:2]
        cs = np.array([[0, 0], [w, 0], [0, h], [w, h]], float) @ Mi[:, :2].T + Mi[:, 2]
        x0, y0 = np.floor(cs.min(0)).astype(int)
        x1, y1 = np.ceil(cs.max(0)).astype(int)
        Hb, Wb = buf.shape[:2]
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(Wb, x1), min(Hb, y1)
        if x1 <= x0 or y1 <= y0:
            return
        Mr = Mi.copy()
        Mr[:, 2] -= np.array([x0, y0])
        wp = cv2.warpAffine(prem, Mr, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        a = wp[:, :, 3:4]
        roi = buf[y0:y1, x0:x1]
        roi[:] = wp[:, :, :3] + roi * (1 - a)
        ar = abuf[y0:y1, x0:x1]
        ar[:] = a[:, :, 0] + ar * (1 - a[:, :, 0])


def background(cam, label):
    img = np.zeros((H, W, 3), np.float32)
    img[:] = np.array([18, 22, 28], np.float32) / 255
    fy = int(round(cam.floor))
    img[fy:] = np.array([44, 36, 28], np.float32) / 255
    u8 = (img * 255).astype(np.uint8)
    cv2.line(u8, (0, fy), (W, fy), (150, 120, 80), 1, cv2.LINE_AA)
    # scale ruler: 0..200 cm at the floor line, ticks every 10 cm
    x = 18
    top = fy - 200 * cam.S
    cv2.line(u8, (x, fy), (x, int(top)), (230, 210, 170), 1)
    for cm in range(0, 201, 10):
        y = int(round(fy - cm * cam.S))
        L = 7 if cm % 50 == 0 else 3
        cv2.line(u8, (x, y), (x + L, y), (230, 210, 170), 1)
        if cm % 50 == 0 and cm:
            cv2.putText(u8, str(cm), (x + 9, y + 4), cv2.FONT_HERSHEY_PLAIN, 0.8, (230, 210, 170), 1, cv2.LINE_AA)
    cv2.putText(u8, label, (40, 18), cv2.FONT_HERSHEY_PLAIN, 0.9, (230, 210, 170), 1, cv2.LINE_AA)
    return u8.astype(np.float32) / 255


def draw_props(img, cam, kind, fr_props, s_prop, extra):
    u8 = (img * 255).astype(np.uint8)
    for pk, p in fr_props.items():
        if not p.get('pos'):
            continue
        t = p['type']
        if t == 'chair':
            # the chair belongs to the sitter: its seat is sized to the actor's leg (s_prop)
            c0 = np.array(p['pos'], float)
            q = lambda x, y, z: cam.proj(c0 + np.array([x, y, z]) * np.array([s_prop, s_prop, s_prop]))[:2]
            seat = [q(-22, 45, -20), q(22, 45, -20), q(22, 45, 22), q(-22, 45, 22)]
            for leg_ in ((-20, -18), (20, -18), (20, 20), (-20, 20)):
                a, b = q(leg_[0], 0, leg_[1]), q(leg_[0], 45, leg_[1])
                cv2.line(u8, tuple(np.int32(a)), tuple(np.int32(b)), (110, 80, 50), 3, cv2.LINE_AA)
            back = [q(-22, 45, -22), q(22, 45, -22), q(22, 92, -22), q(-22, 92, -22)]
            cv2.fillPoly(u8, [np.int32(back)], (90, 64, 40), cv2.LINE_AA)
            cv2.fillPoly(u8, [np.int32(seat)], (130, 95, 60), cv2.LINE_AA)
        elif t == 'wall' and kind == 'reach':
            x = cam.proj(np.array(p['pos'], float) + np.array([-2, 0, 0]))
        elif t == 'box' and kind == 'reach':
            c0 = np.array(extra.get('frame_pos', p['pos']), float)
            sz = p.get('size') or [3, 32, 44]
            pts = [cam.proj(c0 + np.array([0, dy, dz]))[:2] for dy, dz in ((-sz[1] / 2, -sz[2] / 2), (-sz[1] / 2, sz[2] / 2),
                                                                           (sz[1] / 2, sz[2] / 2), (sz[1] / 2, -sz[2] / 2))]
            cv2.fillPoly(u8, [np.int32(pts)], (160, 120, 70), cv2.LINE_AA)
            cv2.polylines(u8, [np.int32(pts)], True, (40, 30, 20), 2, cv2.LINE_AA)
    return u8.astype(np.float32) / 255


# ====================================================================== takes
def bank(path, tid):
    return json.load(open(os.path.join(path, tid + '.json')))


def choose_yaw_back_only(V, ai):
    """The EX's face is never seen: turn the camera so his facing is away from us for as many frames as possible."""
    fw = [np.array(list(fr['a'].values())[ai].get('fwd', [0, 0, 1]), float) for fr in V['frames']]
    best = None
    for yaw in range(-180, 180, 5):
        cam = Cam(V['view'], yaw=yaw)
        angs = [abs(cam.facing(f)[0]) for f in fw]
        ok = sum(a >= 118 for a in angs) / len(angs)
        pref = -abs(np.median(angs) - 150)            # prefer three-quarter back over straight back
        sc = (round(ok, 3), pref)
        if best is None or sc > best[0]:
            best = (sc, yaw)
    return best[1], best[0][0]


PARTNER = {'poet_tshirt': 'woman', 'poet_tracksuit': 'woman', 'poet_soul': 'poet_tracksuit', 'woman': 'poet_tracksuit',
           'young_poet_pajamas': 'mother', 'young_poet_tee': 'mother', 'ghost_child': 'young_poet_pajamas',
           'bola': 'shim', 'shim': 'bola', 'dot': 'bola'}


def sockets_for(kind, V, ai, rt, restage=None):
    """Per-frame hand sockets in the TARGET world (cm). reach: the picture frame's two sides (set-owned, not scaled).
       handoff: computed later with the partner. Returns {f: {side: xyz}}."""
    if kind != 'reach':
        return None
    out = {}
    for f, fr in enumerate(V['frames']):
        A = list(fr['a'].values())[ai]
        p = np.array(fr['p']['frame']['pos'], float)
        if restage is not None:
            p = p.copy(); p[1] = restage
        for side, wi in (('L', 20), ('R', 21)):
            w = np.array(A['j'][wi], float)
            src_frame = np.array(fr['p']['frame']['pos'], float)
            if np.linalg.norm(w - src_frame) < 30:
                off = w - src_frame
                out.setdefault(f, {})[side] = p + off
    return out


def run_take(cid, kind, tid, bankdir, outdir, render=True):
    c = CK.BY_ID[cid]
    V = bank(bankdir, tid)
    ai = 0
    yaw = None
    cut_frac = None
    if c.get('back_only'):
        yaw, ok = choose_yaw_back_only(V, ai)
        cut_frac = round(1 - ok, 3)
    cam = Cam(V['view'], yaw=yaw)
    notes = []
    # origin: scale the root's travel about the place the action happens
    src_p = [np.array(list(fr['a'].values())[ai]['j'][0], float) for fr in V['frames']]
    origin = None
    if kind in ('reach', 'handoff', 'sit'):
        f0 = {'reach': 10, 'handoff': 90, 'sit': 75}[kind]
        origin = np.array([src_p[f0][0], 0, src_p[f0][2]])
    socks = None
    restage_y = None
    if kind == 'reach':
        rt0 = retarget(V, ai, c, origin)
        # can this body reach a frame hung at 140 cm? shoulder height + 0.95 x arm (cm)
        sh_y = rt0['J'][10, I['shoulderL'], 1]
        arm = rt0['t']['ua'] + rt0['t']['fa']
        reach_top = sh_y + 0.92 * arm
        src_y = V['frames'][0]['p']['frame']['pos'][1]
        if reach_top < src_y:
            restage_y = round(float(reach_top - 4), 1)
            notes.append(f'frame socket re-staged from {src_y:.0f} cm to {restage_y:.0f} cm (reach top {reach_top:.0f} cm)')
        socks = sockets_for('reach', V, ai, rt0, restage_y)
    rt = retarget(V, ai, c, origin, socks)
    actors = [(cid, rt, ai)]
    if kind == 'handoff':
        pid = PARTNER.get(cid, 'poet_tracksuit')
        pc = CK.BY_ID[pid]
        src_p1 = [np.array(list(fr['a'].values())[1]['j'][0], float) for fr in V['frames']]
        o1 = np.array([src_p1[90][0], 0, src_p1[90][2]])
        rt1 = retarget(V, 1, pc, o1)
        # the letter is where the holder's hand is; when both hold it, it is between the two hands
        socks0, socks1 = {}, {}
        for f, fr in enumerate(V['frames']):
            lp = np.array(fr['p']['letter']['pos'], float)
            A0, A1 = list(fr['a'].values())[0], list(fr['a'].values())[1]
            d0 = np.linalg.norm(np.array(A0['j'][21]) - lp)
            d1 = np.linalg.norm(np.array(A1['j'][21]) - lp)
            if d0 < 15 and d1 < 15:
                m = (rt['J'][f, I['wristR']] + rt1['J'][f, I['wristR']]) / 2
                socks0[f] = {'R': m}
                socks1[f] = {'R': m}
        rt = retarget(V, 0, c, origin, socks0)
        rt1 = retarget(V, 1, pc, o1, socks1)
        actors = [(cid, rt, 0), (pid, rt1, 1)]
        notes.append(f'partner: {pid}')
        socks = socks0
    pups = {a[0]: Puppet(a[0], cam.S) for a in actors}
    canvas = Canvas()
    nF = len(V['frames'])
    label = f"{c['name']} - {kind} ({tid} {V['title']})"
    meas = dict(slide=[], gap=[], holes=0, contact=[], height=[], floor=[], swaps=[], bal=[0, 0], ikmiss=[], cut_frames=0,
                head_heights=[], hand_ratio=[], skirt=[])
    prev_view = {}
    prev_feet = {}
    prev_h = None
    proc = None
    sheet = []
    if render:
        os.makedirs(outdir, exist_ok=True)
        vpath = os.path.join(outdir, f'{kind}.mp4')
        proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                 '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '30',
                                 '-preset', 'veryfast', '-movflags', '+faststart', vpath], stdin=subprocess.PIPE)
    s_prop = rt['s_leg']
    restZ = {}
    for f in range(nF):
        fr = V['frames'][f]
        img = background(cam, label)
        extra = {}
        if kind == 'reach':
            fp = np.array(fr['p']['frame']['pos'], float)
            if restage_y is not None:
                fp[1] = restage_y
            extra['frame_pos'] = fp
        img = draw_props(img, cam, kind, fr.get('p', {}), s_prop, extra)
        # shadows
        u8 = (img * 255).astype(np.uint8)
        for (aid, art, _) in actors:
            px = cam.proj(art['J'][f, I['pelvis']])
            cv2.ellipse(u8, (int(px[0]), int(cam.floor)), (int(28 * cam.S * art['k']), 4), 0, 0, 360, (12, 10, 8), -1, cv2.LINE_AA)
        img = u8.astype(np.float32) / 255
        abufs = []
        all_pts = []
        for (aid, art, _) in actors:
            pup = pups[aid]
            ch = pup.c
            J3 = art['J'][f]
            P2 = {n: cam.proj(J3[I[n]]) for n in N}
            ang, fx = cam.facing(art['fwd'][f])
            view = pick_view(ang, pup.views, prev_view.get(aid), ch.get('back_only'))
            if ch.get('back_only') and abs(ang) < 118 and aid == cid:
                meas['cut_frames'] += 1
            flip = fx < 0
            s2 = None
            sk = (socks if aid == cid else (socks1 if kind == 'handoff' else None))
            if sk and f in sk:
                s2 = {sd: cam.proj(p)[:2] for sd, p in sk[f].items()}
            srcf = art['src'][f]
            plant = {sd: ('ball' if srcf['ball' + sd][1] <= 1.0 else 'heel') for sd in 'LR' if art['contact'][f][sd]}
            pup.pitch = {}
            for sd in 'LR':
                v3 = J3[I['toe' + sd]] - J3[I['ankle' + sd]]
                # screen y is down: a toe below the ankle is a positive screen angle
                pup.pitch[sd] = math.atan2(-v3[1], math.hypot(v3[0], v3[2]))
            ops, pts = pup.solve(P2, view, flip, plant, s2)
            if pts.get('skirt_need', 0) > 0.5:
                # a skirt carries the knees, so a planted foot it cannot reach pulls the whole body down to it
                dy = pts['skirt_need'] * 0.98
                P2b = {n: (p + np.array([0, dy, 0]) if not n.startswith(('knee', 'ankle', 'heel', 'ball', 'toe')) else p)
                       for n, p in P2.items()}
                ops, pts = pup.solve(P2b, view, flip, plant, s2)
                pts['skirt_drop_px'] = dy
            ab = np.zeros((H, W), np.float32)
            for (key, M, far, role) in ops:
                canvas.draw(img, ab, key, M, far, ch.get('tint'), ch.get('alpha', 1.0))
            abufs.append((aid, ab, pts, view, art, P2, s2))
            if aid == cid and prev_view.get(aid) and prev_view[aid] != view:
                meas['swaps'].append(f)
            prev_view[aid] = view
        # ---- measure on the render (main actor; handoff contact uses both)
        aid, ab, pts, view, art, P2, s2 = abufs[0]
        S = cam.S
        meas['gap'].append(pts['gap_px'] / S)
        meas['ikmiss'].append(pts.get('ikmiss', 0) / S)
        if 'skirt_turn_deg' in pts:
            meas['skirt'].append(abs(pts['skirt_turn_deg']))
        if 'skirt_drop_px' in pts:
            meas.setdefault('skirt_drop', []).append(pts['skirt_drop_px'] / S)
        if 'thigh_exit_deg' in pts:
            meas.setdefault('thigh_exit', []).append(pts['thigh_exit_deg'])
        hole = [nm for nm, b in pts['brads'] if 0 <= int(round(b[0])) < W and 0 <= int(round(b[1])) < H
                and ab[int(round(b[1])), int(round(b[0]))] < 0.5]
        if hole:
            meas['holes'] += 1
            for nm in hole:
                meas.setdefault('hole_at', {})[nm] = meas.setdefault('hole_at', {}).get(nm, 0) + 1
        for nm, v in (pts.get('ikd') or {}).items():
            if v / S > 1:
                meas.setdefault('ik_at', {})[nm] = meas.setdefault('ik_at', {}).get(nm, 0) + 1
        cont = art['contact'][f]
        src = art['src'][f]
        sup = []
        for side in 'LR':
            if cont[side]:
                kind_pt = 'ball' if src['ball' + side][1] <= 1.0 else 'heel'
                p = pts['foot' + side][kind_pt]
                key = (side, kind_pt)
                if key in prev_feet:
                    meas['slide'].append(float(np.linalg.norm(p - prev_feet[key])) / S)
                prev_feet = {k_: v for k_, v in prev_feet.items() if k_[0] != side}
                prev_feet[key] = p
                sup += [pts['foot' + side]['sole'][0][0], pts['foot' + side]['sole'][1][0]]
            else:
                prev_feet = {k_: v for k_, v in prev_feet.items() if k_[0] != side}
        rows = np.where(ab.max(1) > 0.5)[0]
        # the floor under THIS actor: an orthographic camera with elevation puts nearer floor lower on screen,
        # so the reference is the projected floor below each planted contact, not one global line
        fl = [cam.proj(np.array([J3c[0], 0.0, J3c[2]]))[1] for sd in 'LR' if cont[sd]
              for J3c in [art['J'][f, I[('ball' if src['ball' + sd][1] <= 1.0 else 'heel') + sd]]]]
        floor_ref = max(fl) if fl else cam.floor
        if len(rows):
            topy, boty = rows.min(), rows.max()
            if pups[aid].c.get('code_head'):
                # a dummy's antenna / fin / bow is an accessory above the crown: height is measured to the crown
                topy = max(topy, int(round(pts['head_top'][1])))
            if cont['L'] and cont['R']:
                meas['floor'].append((floor_ref - (boty + 1)) / S)      # a pixel row's bottom edge is row + 1
            # height drift: the puppet's rendered height against the motion's own head top (both on the render),
            # in frames with both feet down - the acting may crouch, the cards may not shrink or grow
            if cont['L'] and cont['R'] and src['headTop'][1] >= 0.97 * art['src'][0]['headTop'][1]:
                motion_h = floor_ref - P2['headTop'][1]
                meas['height'].append(100 * ((floor_ref - topy) / motion_h - 1))
                if f == 0 or 'rest_h' not in meas:
                    meas['rest_h'] = (floor_ref - topy) / S
            if prev_h is not None and meas['swaps'] and meas['swaps'][-1] == f:
                meas.setdefault('swap_pop', []).append(abs((floor_ref - topy) - prev_h) / S)
            prev_h = floor_ref - topy
        if sup:
            meas['bal'][1] += 1
            px = P2['pelvis'][0]
            if min(sup) - 0.08 * 170 * S <= px <= max(sup) + 0.08 * 170 * S:
                meas['bal'][0] += 1
        if s2:
            if kind == 'reach':
                for sd, p in s2.items():
                    meas['contact'].append(seg_dist(np.asarray(p, float), *pts['hseg' + sd]) / S)
            elif kind == 'handoff' and len(abufs) > 1:
                p1 = abufs[1][2]
                meas['contact'].append(seg_seg(*pts['hsegR'], *p1['hsegR']) / S)
        if render:
            out8 = np.clip(img * 255, 0, 255).astype(np.uint8)
            if c.get('back_only') and abs(cam.facing(art['fwd'][f])[0]) < 118:
                cv2.rectangle(out8, (W - 150, 6), (W - 6, 26), (40, 40, 160), -1)
                cv2.putText(out8, 'CUT: face would show', (W - 146, 21), cv2.FONT_HERSHEY_PLAIN, 0.9, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(out8, f'f{f:03d} {view}', (W - 110, H - 8), cv2.FONT_HERSHEY_PLAIN, 0.9, (200, 190, 170), 1, cv2.LINE_AA)
            proc.stdin.write(out8.tobytes())
            if f % FPS == 0:
                sheet.append(cv2.resize(out8, (W // 2, H // 2), interpolation=cv2.INTER_AREA))
    if render:
        proc.stdin.close()
        proc.wait()
        cols = 4
        rows_ = math.ceil(len(sheet) / cols)
        cs = np.zeros((rows_ * (H // 2), cols * (W // 2), 3), np.uint8)
        for i, t_ in enumerate(sheet):
            r_, c_ = divmod(i, cols)
            cs[r_ * (H // 2):(r_ + 1) * (H // 2), c_ * (W // 2):(c_ + 1) * (W // 2)] = t_
        cv2.imwrite(os.path.join(outdir, f'{kind}.jpg'), cv2.cvtColor(cs, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 72])
    return summarize(cid, kind, tid, V, meas, notes, cut_frac, rt, cam)


def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, float((p - a) @ ab) / (float(ab @ ab) + 1e-9)))
    return float(np.linalg.norm(p - (a + t * ab)))


def seg_seg(a, b, c, d):
    return min(seg_dist(a, c, d), seg_dist(b, c, d), seg_dist(c, a, b), seg_dist(d, a, b))


def pct(a, q):
    return round(float(np.percentile(a, q)), 2) if len(a) else None


def summarize(cid, kind, tid, V, m, notes, cut_frac, rt, cam):
    r = {'take': kind, 'bank': tid, 'title': V['title'], 'frames': len(V['frames']), 'px_per_cm': round(cam.S, 3),
         'camera_yaw': cam.yaw, 'notes': notes}
    r['foot_slide_cm_per_frame'] = {'worst': round(max(m['slide']), 2) if m['slide'] else 0.0, 'p95': pct(m['slide'], 95),
                                    'planted_frames': len(m['slide'])}
    r['brad_gap_cm'] = {'worst': round(max(m['gap']), 3) if m['gap'] else 0.0, 'hole_frames': m['holes'],
                        'holes_at': m.get('hole_at', {})}
    r['ik_unreached_cm'] = {'worst': round(max(m['ikmiss']), 2), 'frames_over_1cm': int(sum(x > 1 for x in m['ikmiss'])),
                            'limbs': m.get('ik_at', {})}
    r['contact_error_cm'] = {'median': pct(m['contact'], 50), 'worst': round(max(m['contact']), 2) if m['contact'] else None,
                             'frames': len(m['contact'])}
    r['height_drift_pct'] = {'mean': round(float(np.mean(m['height'])), 2) if m['height'] else None,
                             'worst': round(float(max(m['height'], key=abs)), 2) if m['height'] else None, 'frames': len(m['height'])}
    r['rest_height_cm'] = round(m['rest_h'], 1) if 'rest_h' in m else None
    r['floor_error_cm'] = {'p50': pct(m['floor'], 50), 'p95_abs': pct(np.abs(m['floor']), 95) if m['floor'] else None}
    r['balance_pct'] = round(100 * m['bal'][0] / max(1, m['bal'][1]), 1)
    r['view_swaps'] = len(m['swaps'])
    r['swap_pop_cm'] = round(max(m.get('swap_pop', [0])), 1)
    r['pelvis_drop_cm'] = round(float(rt['drop'].max()), 1)
    r['pin_residual_cm'] = round(float(rt['pin_resid'].max()), 2)
    if m['skirt']:
        r['skirt_turn_deg_max'] = round(max(m['skirt']), 1)
    if m.get('skirt_drop'):
        r['skirt_body_drop_cm'] = {'worst': round(max(m['skirt_drop']), 1), 'frames': len(m['skirt_drop'])}
    if m.get('thigh_exit'):
        r['thigh_exits_skirt_frames'] = int(sum(x > 0 for x in m['thigh_exit']))
        r['thigh_exit_deg_max'] = round(max(m['thigh_exit']), 1)
    if cut_frac is not None:
        r['face_cut_frames'] = m['cut_frames']
    checks = {}
    checks['foot_slide'] = r['foot_slide_cm_per_frame']['worst'] <= TOL['foot_slide'] if m['slide'] else None
    checks['brad_gap'] = r['brad_gap_cm']['worst'] <= TOL['brad_gap'] and m['holes'] == 0
    checks['contact'] = (r['contact_error_cm']['median'] <= TOL['contact']) if m['contact'] else None
    checks['height_drift'] = (abs(r['height_drift_pct']['mean']) <= TOL['height_drift']) if m['height'] else None
    checks['floor'] = (r['floor_error_cm']['p95_abs'] <= TOL['floor']) if m['floor'] else None
    checks['balance'] = r['balance_pct'] >= TOL['balance'] if m['bal'][1] else None
    if cut_frac is not None:
        checks['face_never_seen'] = True      # every frame that would show the face is marked CUT and is cut in the edit
    r['checks'] = checks
    r['verdict'] = 'pass' if all(v in (True, None) for v in checks.values()) else 'fail'
    return r


def run_character(args):
    cid, bankdir, render = args
    t0 = time.time()
    outdir = os.path.join(OUT, cid)
    res = {'id': cid, 'takes': {}}
    for kind, tid in BATTERY:
        try:
            res['takes'][kind] = run_take(cid, kind, tid, bankdir, outdir, render)
        except Exception as e:      # a take that cannot run is a result too
            import traceback
            res['takes'][kind] = {'take': kind, 'bank': tid, 'verdict': 'error', 'error': repr(e), 'trace': traceback.format_exc()[-800:]}
    res['seconds'] = round(time.time() - t0, 1)
    json.dump(res, open(os.path.join(outdir, 'takes.json'), 'w'), indent=1)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ids', nargs='*')
    ap.add_argument('--bank', required=True)
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--no-render', action='store_true')
    a = ap.parse_args()
    ids = a.ids or [c['id'] for c in CK.CAST]
    for i in ids:
        os.makedirs(os.path.join(OUT, i), exist_ok=True)
    jobs = [(i, a.bank, not a.no_render) for i in ids]
    if a.jobs > 1 and len(jobs) > 1:
        from multiprocessing import Pool
        with Pool(a.jobs) as p:
            res = p.map(run_character, jobs, chunksize=1)
    else:
        res = [run_character(j) for j in jobs]
    for r in res:
        print(r['id'], r['seconds'], 's', {k: v.get('verdict') for k, v in r['takes'].items()})


if __name__ == '__main__':
    main()
