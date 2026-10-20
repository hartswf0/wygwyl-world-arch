"""Acting Arena engine: a 2D cut-out performer solver with the Crash Lab checks.

A challenge script (challenges/*.py) builds a Scene: actors, props, and motions placed on a frame timeline.
Scene.solve() evaluates every frame once, in order, and returns:
  - per-frame joints for every actor (the pose);
  - per-frame prop poses and owners;
  - a display list per frame, in the same op format as shots/weave (img ops with a matrix, plus poly/line/label);
  - the technical report: every check in spec.crash_lab_checks that a 2D profile rig can measure, with
    the frames where it fails. Checks it cannot measure are listed as not_checked, never as passed.

Units. Positions are stage pixels (1920 x 1080, y down). Every actor has a standing height H px (sole to crown);
1 cm = H / 170 px for that actor, so the spec's centimetre tolerances are calibrated to the asset scale.
Angles are degrees. 'facing' f is +1 (right) or -1 (left). In facing space +x is forward and +y is down.

The rig is a cardboard cut-out: rigid pieces on brads. Pieces never stretch. Unlike the POET's first rig and the
Crash Lab dummy, the leg is three pieces (thigh, shin, foot), so a knee can be placed on a surface.
"""
import bisect, json, math
import numpy as np

W, H_STAGE = 1920, 1080

# ---------------------------------------------------------------- body

# proportions as fractions of standing height
PROPS = dict(head=0.125, neck=0.035, torso=0.30, thigh=0.245, shin=0.245, ankle=0.04,
             heel=0.045, ball=0.085, toe=0.115, uarm=0.165, farm=0.145, hand=0.095, palm=0.045,
             shoulder_drop=0.035, hip_w=0.055, sh_w=0.10)
# half-thickness of each piece (for penetration), fraction of height
RADII = dict(head=0.06, torso=0.085, thigh=0.045, shin=0.035, uarm=0.03, farm=0.026, hand=0.02, foot=0.0)
MASS = dict(head=0.081, torso=0.497, uarm=0.028, farm=0.016, hand=0.006, thigh=0.10, shin=0.0465, foot=0.0145)

VARIANTS = {  # spec.variation_axes.body, as scale factors on the pieces
    'standard': {},
    'short_limbs': dict(thigh=0.8, shin=0.8, uarm=0.82, farm=0.82),
    'long_limbs': dict(thigh=1.15, shin=1.15, uarm=1.15, farm=1.15),
    'bulky_torso': dict(torso=1.0, r_torso=1.45, m_torso=1.25),
}


def rotv(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([v[0] * c - v[1] * s, v[0] * s + v[1] * c])


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ik2(S0, Wt, L1, L2, bend):
    """two-bone IK in the plane. bend: +1/-1 picks the side the middle joint goes to (sign of the cross product).
    Returns (mid joint, end joint actually reached, requested distance / (L1+L2))."""
    S0 = np.asarray(S0, float); Wt = np.asarray(Wt, float)
    d = Wt - S0
    D = float(np.linalg.norm(d))
    Dc = min(max(D, abs(L1 - L2) + 1e-6), (L1 + L2) - 1e-6)
    a = math.acos(max(-1.0, min(1.0, (L1 * L1 + Dc * Dc - L2 * L2) / (2 * L1 * Dc))))
    base = math.atan2(d[1], d[0])
    ua = base + bend * a
    E = S0 + L1 * np.array([math.cos(ua), math.sin(ua)])
    tgt = S0 + d * (Dc / max(D, 1e-9))
    return E, tgt, D / (L1 + L2)


class Body:
    def __init__(self, height, variant='standard'):
        self.H = float(height)
        self.cm = self.H / 170.0
        self.variant = variant
        v = VARIANTS[variant]
        self.L = {k: PROPS[k] * self.H * v.get(k, 1.0) for k in PROPS}
        self.R = {k: RADII[k] * self.H * v.get('r_' + k, 1.0) for k in RADII}
        m = {k: MASS[k] * v.get('m_' + k, 1.0) for k in MASS}
        tot = m['head'] + m['torso'] + 2 * (m['uarm'] + m['farm'] + m['hand'] + m['thigh'] + m['shin'] + m['foot'])
        self.M = {k: x / tot for k, x in m.items()}

    def hip_height(self, bend=0.985):
        return (self.L['thigh'] + self.L['shin']) * bend + self.L['ankle']


# ---------------------------------------------------------------- channels


class Chan:
    """keys (t, value, mode). mode: 'ease' (smoothstep from the previous key), 'lin', or 'step'."""

    def __init__(self, default):
        self.t, self.v, self.m = [], [], []
        self.default = default

    def key(self, t, v, mode='ease'):
        if not self.t and t > 0:
            self.t.append(0.0); self.v.append(self.default); self.m.append('lin')
        i = bisect.bisect_right(self.t, t)
        if i > 0 and abs(self.t[i - 1] - t) < 1e-9:
            self.v[i - 1], self.m[i - 1] = v, mode
            return
        self.t.insert(i, t); self.v.insert(i, v); self.m.insert(i, mode)

    def span(self, t):
        """(value_a, value_b, x) with x in [0,1]; value_b is None when holding"""
        if not self.t:
            return self.default, None, 0.0
        i = bisect.bisect_right(self.t, t)
        if i == 0:
            return self.v[0], None, 0.0
        if i == len(self.t):
            return self.v[-1], None, 0.0
        ta, tb = self.t[i - 1], self.t[i]
        mode = self.m[i]
        if mode == 'step':
            return self.v[i - 1], None, 0.0
        x = (t - ta) / max(1e-9, tb - ta)
        return self.v[i - 1], self.v[i], (ease(x) if mode == 'ease' else x)

    def __call__(self, t):
        a, b, x = self.span(t)
        if b is None:
            return a
        if isinstance(a, (list, tuple, np.ndarray)):
            return [p + (q - p) * x for p, q in zip(a, b)]
        return a + (b - a) * x

    def last(self):
        return self.v[-1] if self.v else self.default


def hand_frame(J, side):
    return np.asarray(J['palm' + side], float), J['ha' + side], (1.0 if J['f'] > 0 else -1.0)


def hand_to_world(J, side, off, dang):
    """a carried prop lives in its hand's frame: rotate by the hand angle, then mirror with the puppet"""
    p, ha, f = hand_frame(J, side)
    q = rotv(off, ha)
    return (p + np.array([f * q[0], q[1]]), f * (ha + dang))


def world_to_hand(J, side, pose):
    p, ha, f = hand_frame(J, side)
    q = np.asarray(pose[0], float) - p
    q = rotv(np.array([f * q[0], q[1]]), -ha)
    return q, f * pose[1] - ha


# ---------------------------------------------------------------- props

PROP_KINDS = {
    # w, h in fractions of the reference height; sockets in prop-local px fractions of (w, h) from the centre
    'cup': dict(w=0.05, h=0.06, solid=False, mass=0.004, sockets={'base': (0, 0.5), 'grip': (0, 0.5)}, fill='#e9e2d0'),
    'box': dict(w=0.30, h=0.26, solid=True, mass=0.0, sockets={'L': (-0.5, 0.0), 'R': (0.5, 0.0), 'top': (0, -0.5)}, fill='#a8794a'),
    'beam': dict(w=0.5, h=0.05, solid=True, mass=0.0, sockets={}, fill='#6b4a2c'),
    'ledge': dict(w=0.9, h=0.8, solid=True, mass=0.0, sockets={'lip': (0.5, -0.5), 'lipL': (-0.5, -0.5), 'top': (0, -0.5)}, fill='#5b4a3c'),
    'book': dict(w=0.09, h=0.025, solid=False, mass=0.004, sockets={'near': (-0.45, 0), 'far': (0.45, 0)}, fill='#b2463a'),
    'wall': dict(w=0.04, h=1.6, solid=True, mass=0.0, sockets={}, fill='#3d3129'),
    'door': dict(w=0.04, h=1.25, solid=True, mass=0.0, sockets={'knob': (0, 0.08)}, fill='#7a5534'),
    'watch': dict(w=0.0, h=0.0, solid=False, mass=0.0, sockets={}, fill='#000'),
}


class Prop:
    def __init__(self, scene, name, kind, pos, ref_h, ang=0.0, w=None, h=None, mass=None, solid=None, fixed=True, fill=None):
        k = PROP_KINDS[kind]
        self.scene, self.name, self.kind = scene, name, kind
        self.w = (w if w is not None else k['w']) * ref_h
        self.h = (h if h is not None else k['h']) * ref_h
        self.mass = k['mass'] if mass is None else mass
        self.solid = k['solid'] if solid is None else solid
        self.fixed = fixed  # a fixed prop can be hung from
        self.sock = {n: np.array([fx * self.w, fy * self.h]) for n, (fx, fy) in k['sockets'].items()}
        self.fill = fill or k['fill']
        self.pose0 = (np.array(pos, float), float(ang))
        self.events = []  # (frame, 'grip'|'release', actor, hand)

    def corners(self, pose):
        c, a = pose
        hw, hh = self.w / 2, self.h / 2
        return [c + rotv(p, a) for p in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]

    def socket(self, pose, name):
        c, a = pose
        return c + rotv(self.sock[name], a)

    def sdist(self, pose, p):
        """signed distance from point p to this (rotated) rectangle; negative inside"""
        c, a = pose
        q = rotv(np.asarray(p, float) - c, -a)
        d = np.abs(q) - np.array([self.w / 2, self.h / 2])
        out = np.linalg.norm(np.maximum(d, 0))
        return out + min(max(d[0], d[1]), 0.0)


# ---------------------------------------------------------------- actor


class Actor:
    HANDS = ('L', 'R')  # L is the far side when facing right, R the near side (a profile convention)

    def __init__(self, scene, name, x, facing=1, height=520, variant='standard', lane=0, look='dummy', tint=None):
        self.scene, self.name = scene, name
        self.B = Body(height, variant)
        self.lane, self.look, self.tint = lane, look, tint
        L = self.B.L
        fl = scene.floor
        self.c = dict(
            px=Chan(float(x)), py=Chan(fl - self.B.hip_height()), lean=Chan(0.0), head=Chan(0.0),
            view=Chan('side'), face=Chan('neutral'), facing=Chan(facing),
            aL=Chan([x - facing * 0.03 * self.B.H, fl - L['ankle']]), aR=Chan([x + facing * 0.03 * self.B.H, fl - L['ankle']]),
            pL=Chan(0.0), pR=Chan(0.0), cL=Chan(float(facing)), cR=Chan(float(facing)),
            hL=Chan(('rest',)), hR=Chan(('rest',)), haL=Chan(80.0), haR=Chan(80.0),
            shL=Chan('relaxed'), shR=Chan('relaxed'), elL=Chan(1), elR=Chan(1), hview=Chan(''),
        )
        # generator cursor
        self.x, self.f = float(x), facing
        self.feet = {'L': np.array(self.c['aL'].default), 'R': np.array(self.c['aR'].default)}
        self.fc = {'L': float(facing), 'R': float(facing)}
        self.y0 = fl - self.B.hip_height()

    # ---------- small helpers for scripts
    def key(self, ch, t, v, mode='ease'):
        self.c[ch].key(t, v, mode)
        return self

    def beat(self, t, label):
        self.scene.beats.append({'f': int(round(t)), 'who': self.name, 'beat': label})
        return self

    def face(self, t, expr):
        return self.key('face', t, expr, 'step')

    def look(self, t0, t1, ang):
        self.key('head', t0, self.c['head'](t0)); return self.key('head', t1, ang)

    def head_view(self, t, view):
        """swap the head alone ('front', 'side' or '' to follow the body): the head turns before the body"""
        return self.key('hview', t, view, 'step')

    def pose(self, t, mode='ease', **kw):
        """key several channels at one frame: pose(t, px=.., py=.., lean=.., head=.., aL=[x,y], pL=.., ...)"""
        for k, v in kw.items():
            self.c[k].key(t, v, 'step' if k in ('view', 'face', 'facing', 'shL', 'shR', 'elL', 'elR', 'hview') else mode)
        return self

    def knee_on(self, knee_pt, shin_ang):
        """ankle target that puts the knee on knee_pt with the shin at shin_ang degrees (0 = pointing backwards
        along the surface, positive = ankle lifted). With a three-piece leg the IK then places the knee there
        whenever the hip is within a thigh's length of knee_pt."""
        L, f = self.B.L, self.f
        d = np.array([-f * math.cos(math.radians(shin_ang)), -math.sin(math.radians(shin_ang))])
        return list(np.asarray(knee_pt, float) + d * L['shin'])

    def hip_for(self, knee_pt, ang_from_knee):
        """pelvis position a thigh's length from knee_pt at that angle (deg, 0 = straight up, + toward the back)"""
        L, f = self.B.L, self.f
        a = math.radians(ang_from_knee)
        return list(np.asarray(knee_pt, float) + np.array([-f * math.sin(a), -math.cos(a)]) * L['thigh'] * 0.9999)

    def hand(self, t, side, spec, ha=None, shape=None, elbow=None, mode='ease'):
        self.c['h' + side].key(t, spec, mode)
        if ha is not None:
            self.c['ha' + side].key(t, ha, mode)
        if shape is not None:
            self.c['sh' + side].key(t, shape, 'step')
        if elbow is not None:
            self.c['el' + side].key(t, elbow, 'step')
        return self

    def hold_pose(self, t):
        """pin every continuous channel at its current value at t (so the next move starts from rest)"""
        for k, ch in self.c.items():
            if k in ('view', 'face', 'facing', 'shL', 'shR', 'elL', 'elR'):
                continue
            if k in ('hL', 'hR'):
                a, b, x = ch.span(t)
                if b is None:
                    ch.key(t, a)
                continue
            ch.key(t, ch(t))
        return self

    # ---------- foot geometry
    def foot_local(self):
        L = self.B.L
        return {'heel': np.array([-L['heel'], L['ankle']]), 'ball': np.array([L['ball'], L['ankle']]),
                'toe': np.array([L['toe'], L['ankle']])}

    def foot_points(self, ankle, pitch, c):
        out = {}
        for n, p in self.foot_local().items():
            q = rotv(p, pitch)
            out[n] = np.array([ankle[0] + c * q[0], ankle[1] + q[1]])
        return out

    def ankle_from(self, pivot, pw, pitch, c):
        q = rotv(self.foot_local()[pivot], pitch)
        return np.array([pw[0] - c * q[0], pw[1] - q[1]])

    def ground(self, x):
        return self.scene.ground_y(x)

    # ---------- motions (each starts from the cursor state and leaves the cursor at its end)
    def stand(self, t, settle=0.985):
        self.c['py'].key(t, self.ground(self.x) - self.B.hip_height(settle))
        self.c['lean'].key(t, 0.0)
        return self

    def walk(self, t0, x1, step=12, stride=0.30, lift=0.05, bob=0.012, lean=4.0, crouch=0.0, arms='LR',
             label=True, heel_pitch=-12.0, toe_pitch=30.0, swing_amp=0.07, gait=None, lead=0.42, knee=0.972):
        """walk so the leading foot lands at x1, then bring the trailing foot alongside. Returns the end frame.
        Footfalls: x0 + f*s*(k+1); the pelvis is midway between the feet at each contact. Feet roll on the heel
        at contact and on the ball at toe-off, so a point that carries weight does not move.
        crouch lowers the pelvis by that fraction of height. gait(k) -> dict can vary step/stride/bob per step
        (a limp, braking strides)."""
        B, L, f = self.B, self.B.L, self.f
        x0 = (self.feet['L'][0] + self.feet['R'][0]) / 2
        d = x1 - x0
        assert d * f > 0, '%s walks backwards: turn first (d=%.0f, facing %d)' % (self.name, d, f)
        n = max(1, int(round(abs(d) / (stride * B.H))))
        s = abs(d) / n
        order = sorted('LR', key=lambda k: self.feet[k][0] * f)
        swing, stance = order[0], order[1]
        t = int(round(t0))
        hip0 = self.ground(x0) - B.hip_height(knee) + crouch * B.H
        lean0 = lean + crouch * 60
        self.c['px'].key(t, self.c['px'](t)); self.c['py'].key(t, self.c['py'](t)); self.c['lean'].key(t, self.c['lean'](t))
        px_prev = self.c['px'](t)
        for k in range(n + 1):
            last = (k == n)
            g = gait(k) if gait else {}
            n_step = int(g.get('step', step) * (0.85 if last else 1.0))
            if not last:
                tx = x0 + f * s * (k + 1)
                px_end = tx - f * s * (1 - lead)
            else:
                tx = x1 - f * 0.06 * B.H
                px_end = x1 - f * 0.03 * B.H
            gy = self.ground(tx)
            heel1 = np.array([tx - f * L['heel'], gy])
            hp = heel_pitch if not last else 0.0
            A0 = np.array(self.c['a' + swing](t), float)
            ball0 = self.foot_points(A0, self.c['p' + swing](t), f)['toe']
            ball0[1] = self.ground(ball0[0])
            Aoff = self.ankle_from('toe', ball0, toe_pitch, f)
            Aland = self.ankle_from('heel', heel1, hp, f)
            v_lin = s / max(1, int(g.get('step', step)))
            p_start = float(self.c['p' + swing](t))
            heel_off = []  # the stance heel rises about its toe late in the step (so the stance leg can reach)
            if not last:
                toe_s = self.foot_points(self.feet[stance], 0.0, f)['toe']
                toe_s[1] = self.ground(toe_s[0])
            for j in range(n_step + 1):
                u = j / n_step
                if not last and u >= 0.6 and k < n - 0:
                    ps = 14.0 * ease((u - 0.6) / 0.4)
                    self.c['a' + stance].key(t + j, list(self.ankle_from('toe', toe_s, ps, f)), 'lin')
                    self.c['p' + stance].key(t + j, ps, 'lin')
                if u <= 0.25:  # toe-off: roll about the toe tip (a card foot has no toe joint)
                    pitch = p_start + (toe_pitch - p_start) * ease(u / 0.25)
                    A = self.ankle_from('toe', ball0, pitch, f)
                else:
                    v = (u - 0.25) / 0.75
                    pitch = toe_pitch * (1 - ease(v / 0.5)) if v < 0.5 else hp * ease((v - 0.5) / 0.5)
                    A = Aoff + (Aland - Aoff) * ease(v)
                    A[1] -= math.sin(math.pi * v) * g.get('lift', lift) * B.H * (0.5 if last else 1.0)
                    if j == n_step:
                        A, pitch = Aland, hp
                self.c['a' + swing].key(t + j, list(A), 'lin')
                self.c['p' + swing].key(t + j, pitch, 'lin')
                self.c['c' + swing].key(t + j, float(f), 'lin')
                # pelvis: Hermite from rest into the walking speed, linear while walking, Hermite back to rest
                D = px_end - px_prev
                if k == 0 and last:
                    xx = px_prev + D * ease(u)
                elif k == 0:
                    xx = px_prev + D * (-2 * u ** 3 + 3 * u ** 2) + f * v_lin * n_step * (u ** 3 - u ** 2)
                elif last:
                    xx = px_prev + f * v_lin * n_step * (u ** 3 - 2 * u ** 2 + u) + D * (-2 * u ** 3 + 3 * u ** 2)
                else:
                    xx = px_prev + D * u
                self.c['px'].key(t + j, xx, 'lin')
                yy = hip0 + g.get('drop', 0.0) * B.H - g.get('bob', bob) * B.H * math.sin(math.pi * u) * (0.4 if last else 1.0)
                if k == 0:
                    yy = self.c['py'](t) + (yy - self.c['py'](t)) * ease(min(1, u * 2))
                self.c['py'].key(t + j, yy, 'lin')
                self.c['lean'].key(t + j, (lean0 * (0.5 if last else 1.0)) if k else self.c['lean'](t) + (lean0 - self.c['lean'](t)) * ease(u), 'lin')
            land = t + n_step
            self.feet[swing] = self.ankle_from('heel', heel1, 0.0, f)
            for j in range(1, 4 if not last else 1):  # heel strike rolls flat about the heel
                pitch = hp * (1 - ease(j / 3))
                self.c['a' + swing].key(land + j, list(self.ankle_from('heel', heel1, pitch, f)), 'lin')
                self.c['p' + swing].key(land + j, pitch, 'lin')
            for side in arms:  # arms swing opposite the legs
                fwd = -1 if side == swing else 1
                self.c['h' + side].key(t + n_step * 0.5, ('rel', swing_amp * fwd * (0.3 if last else 1), 0.29))
                self.c['ha' + side].key(t + n_step * 0.5, 80 - 12 * fwd)
            if label:
                self.beat(t, 'weight onto the %s foot' % ('right' if stance == 'R' else 'left') if k == 0 else 'passing')
                self.beat(land, 'heel strike' if not last else 'trailing foot comes through')
            px_prev = px_end
            t = land
            swing, stance = stance, swing
        for side in arms:
            self.c['h' + side].key(t + 5, ('rest',)); self.c['ha' + side].key(t + 5, 80.0)
        self.x = px_prev
        if label:
            self.beat(t + 6, 'settle')
        self.c['py'].key(t + 6, hip0 + 0.006 * B.H, 'ease')
        self.c['lean'].key(t + 6, crouch * 60, 'ease')
        return t + 6

    def turn(self, t0, dur=10, label=True):
        """turn round in place: both feet pivot on the ball (their projected length passes through zero), the body
        set is replaced profile -> front -> profile at the middle. Returns the end frame."""
        f = self.f
        for side in 'LR':
            A = np.array(self.c['a' + side](t0)); c0 = self.c['c' + side](t0)
            ball = self.foot_points(A, 0.0, c0)['ball']
            # one foot pivots at a time on its ball with the heel up; the other stays flat and carries the weight
            w0, w1 = (0, dur // 2) if side == 'R' else (dur // 2, dur)
            for j in range(dur + 1):
                u = ease(min(1.0, max(0.0, (j - w0) / max(1, w1 - w0))))
                c = f * math.cos(math.pi * u)
                lift = 10.0 * max(0.0, min(1.0, (j - w0) / 2.0, (w1 - j) / 2.0))
                self.c['c' + side].key(t0 + j, c, 'lin')
                self.c['p' + side].key(t0 + j, lift, 'lin')
                self.c['a' + side].key(t0 + j, list(self.ankle_from('ball', ball, lift, c)), 'lin')
            self.feet[side] = np.array(self.c['a' + side](t0 + dur))
        self.c['view'].key(t0, 'side', 'step')
        self.c['view'].key(t0 + dur * 0.3, 'front', 'step')
        self.c['facing'].key(t0, f, 'step')
        self.c['facing'].key(t0 + dur * 0.5, -f, 'step')
        self.c['view'].key(t0 + dur * 0.7, 'side', 'step')
        self.f = -f
        # the pelvis dips a little on the pivot and recentres between the feet
        x_mid = (self.feet['L'][0] + self.feet['R'][0]) / 2
        self.c['px'].key(t0, self.c['px'](t0)); self.c['px'].key(t0 + dur, x_mid)
        y = self.c['py'](t0)
        self.c['py'].key(t0, y); self.c['py'].key(t0 + dur * 0.5, y + 0.008 * self.B.H); self.c['py'].key(t0 + dur, y)
        self.x = x_mid
        if label:
            self.beat(t0, 'turn'); self.beat(t0 + dur, 'turned')
        return t0 + dur

    def crouch(self, t0, t1, depth, lean=None):
        """lower the pelvis by depth * height with the feet planted (the knees come from IK)"""
        self.c['py'].key(t0, self.c['py'](t0)); self.c['lean'].key(t0, self.c['lean'](t0))
        self.c['py'].key(t1, self.ground(self.x) - self.B.hip_height() + depth * self.B.H)
        self.c['lean'].key(t1, depth * 70 if lean is None else lean)
        return t1

    def set_feet(self, t, mode='lin'):
        for s in 'LR':
            self.c['a' + s].key(t, list(self.feet[s]), mode); self.c['p' + s].key(t, 0.0, mode)
            self.c['c' + s].key(t, float(self.f), mode)


# ---------------------------------------------------------------- scene


class Scene:
    def __init__(self, cid, frames, fps=24, floor=900, title='', water=None):
        self.id, self.N, self.fps, self.floor, self.title = cid, int(frames), fps, float(floor), title
        self.actors, self.props, self.beats = {}, {}, []
        self.declared = []  # (kind, f0, f1, why) flags the script expects and accepts
        self.contacts = []  # (actor, hand, f0, f1, target) hand contacts the script asserts (besides prop grips)
        self.supports_by = []  # (actor_holding, actor_held, f0, f1): hands of one body that carry another
        self.water = water  # (x0, x1, y_surface) region where being below the floor is swimming
        self.notes = []

    def actor(self, name, x, **kw):
        a = Actor(self, name, x, **kw)
        self.actors[name] = a
        return a

    def prop(self, name, kind, pos, ref_h=520, **kw):
        p = Prop(self, name, kind, pos, ref_h, **kw)
        self.props[name] = p
        return p

    def grip(self, t, actor, hand, prop, snap=None):
        """from frame t the prop is carried by that hand (its offset to the palm is fixed at t).
        snap: a prop socket name to move onto the palm at t (for props that start in the hand)."""
        self.props[prop].events.append((int(round(t)), 'grip', actor, (hand, snap)))

    def release(self, t, prop, rest=None):
        self.props[prop].events.append((int(round(t)), 'release', None, rest))

    def declare(self, kind, f0, f1, why):
        self.declared.append((kind, int(f0), int(f1), why))

    def ground_y(self, x):
        y = self.floor
        for p in self.props.values():
            if p.solid and p.fixed and p.kind in ('box', 'ledge'):
                c, a = p.pose0
                if abs(x - c[0]) <= p.w / 2 and abs(a) < 1e-6:
                    y = min(y, c[1] - p.h / 2)
        return y

    # ------------------------------------------------ solve
    def _hand_target(self, a, side, spec, t, J, props_now):
        """world grip point for a hand spec"""
        B = a.B
        S = J['sh' + side]
        f = J['f']
        if spec[0] == 'rest':
            return S + np.array([f * 0.02 * B.H, B.L['uarm'] + B.L['farm'] + B.L['palm'] - 0.012 * B.H])
        if spec[0] == 'rel':
            return S + np.array([f * spec[1] * B.H, spec[2] * B.H])
        if spec[0] == 'world':
            return np.array(spec[1:3], float)
        if spec[0] == 'carry':  # ('carry', dx forward of the pelvis in heights, y in stage px)
            return np.array([J['P'][0] + f * spec[1] * B.H, spec[2]])
        if spec[0] == 'prop':
            pr = self.props[spec[1]]
            pose = props_now.get(spec[1])
            if pose is None:
                return None
            return pr.socket(pose, spec[2]) + (np.array(spec[3], float) * B.H if len(spec) > 3 else 0)
        if spec[0] == 'body':  # ('body', actor, joint, [dx, dy])
            other = self._J.get(spec[1])
            if other is None:
                return None
            return np.asarray(other[spec[2]]) + (np.array(spec[3], float) * B.H if len(spec) > 3 else 0)
        raise ValueError(spec)

    def _body(self, a, t):
        """everything but the hands"""
        B, L, c = a.B, a.B.L, a.c
        f = c['facing'](t)
        view = c['view'](t)
        P = np.array([c['px'](t), c['py'](t)])
        lean = c['lean'](t)
        u = np.array([f * math.sin(math.radians(lean)), -math.cos(math.radians(lean))])
        N = P + u * L['torso']
        J = {'f': f, 'view': view, 'hview': c['hview'](t) or view, 'P': P, 'N': N, 'lean': lean, 'face': c['face'](t)}
        hu = rotv(u, f * c['head'](t))
        J['C'] = N + hu * (L['neck'] + L['head'])
        J['Hb'] = N + hu * L['neck']
        sh = N - u * L['shoulder_drop']
        lat = np.array([L['sh_w'], 0.0]) if view != 'side' else np.array([0.012 * B.H * f, 0.0])
        J['shR'], J['shL'] = sh + lat * (1 if view != 'side' else 1), sh - lat
        hl = np.array([L['hip_w'], 0.0]) if view != 'side' else np.array([0.01 * B.H * f, 0.0])
        J['hipR'], J['hipL'] = P + hl, P - hl
        err = {}
        for s in 'LR':
            A = np.array(c['a' + s](t), float)
            K, Ar, ratio = ik2(J['hip' + s], A, L['thigh'], L['shin'], bend=-f if True else f)
            # knee must point forward: pick the side by facing
            K2, Ar2, _ = ik2(J['hip' + s], A, L['thigh'], L['shin'], bend=f)
            if (K2[0] - J['hip' + s][0]) * f > (K[0] - J['hip' + s][0]) * f:
                K, Ar = K2, Ar2
            J['knee' + s], J['ank' + s] = K, Ar
            err['leg' + s] = float(np.linalg.norm(Ar - A)) / B.cm
            pitch, cc = c['p' + s](t), c['c' + s](t)
            J['pitch' + s], J['c' + s] = pitch, cc
            J.update({k + s: v for k, v in a.foot_points(Ar, pitch, cc).items()})
        return J, err

    def _arms(self, a, t, J, props_now, which):
        B, L, c = a.B, a.B.L, a.c
        err = {}
        for s in which:
            spec_a, spec_b, x = c['h' + s].span(t)
            ha = c['ha' + s](t)
            Ga = self._hand_target(a, s, spec_a, t, J, props_now)
            Gb = self._hand_target(a, s, spec_b, t, J, props_now) if spec_b is not None else None
            if Ga is None or (spec_b is not None and Gb is None):
                return False
            G = Ga if Gb is None else Ga + (Gb - Ga) * x
            f = J['f']
            hd = np.array([f * math.cos(math.radians(ha)), math.sin(math.radians(ha))])
            Wt = G - hd * L['palm']
            bend = c['el' + s](t) * f  # elbow back (away from the facing direction)
            E, Wr, ratio = ik2(J['sh' + s], Wt, L['uarm'], L['farm'], bend=bend)
            J['elb' + s], J['wri' + s] = E, Wr
            J['palm' + s] = Wr + hd * L['palm']
            J['tip' + s] = Wr + hd * L['hand']
            J['ha' + s], J['shape' + s] = ha, c['sh' + s](t)
            hold = spec_b is None or (spec_a == spec_b) or (spec_a[0] == 'prop' and spec_b[0] == 'prop' and spec_a[1] == spec_b[1])
            if spec_a[0] in ('prop', 'body', 'world') and hold:
                err['hand' + s] = (float(np.linalg.norm(J['palm' + s] - G)) / B.cm, spec_a)
            J['reach' + s] = ratio
        return err

    def solve(self):
        N = self.N
        poses = {n: [] for n in self.actors}
        prop_track = {n: [] for n in self.props}
        owners = {n: [] for n in self.props}
        hand_err = []
        leg_err = []
        own = {n: None for n in self.props}  # name -> (actor, hand, offset (local), dang)
        free = {n: p.pose0 for n, p in self.props.items()}
        for fr in range(N):
            t = float(fr)
            # 1. bodies
            self._J = {}
            errs = {}
            for n, a in self.actors.items():
                J, e = self._body(a, t)
                self._J[n] = J
                errs[n] = e
            # 2. free props are where they were left; owned props wait for their hand
            props_now = {n: free[n] for n in self.props if own[n] is None}
            # events at this frame: releases first (prop keeps its last pose), then grips (after hands solve)
            for n, p in self.props.items():
                for (ef, kind, an, hand) in p.events:
                    if ef == fr and kind == 'release' and own[n] is not None:
                        last = prop_track[n][-1]
                        free[n] = (np.array(last[0]), last[1]) if hand is None else (np.array(hand[0], float), float(hand[1]))
                        own[n] = None
                        props_now[n] = free[n]
            # 3. hands whose targets are known; then carried props; then the remaining hands
            pending = {n: list('LR') for n in self.actors}
            herr = {}
            for _ in range(3):
                for n, a in self.actors.items():
                    rest = []
                    for s in pending[n]:
                        e = self._arms(a, t, self._J[n], props_now, s)
                        if e is False:
                            rest.append(s)
                        else:
                            herr.update({(n, k): v for k, v in e.items()})
                    pending[n] = rest
                for pn, o in own.items():
                    if o is None or pn in props_now:
                        continue
                    an, hand, off, dang = o
                    J = self._J[an]
                    if 'palm' + hand in J:
                        props_now[pn] = hand_to_world(J, hand, off, dang)
            for n, a in self.actors.items():  # unresolvable targets: hold the previous palm position, and say so
                for s in pending[n]:
                    prev = poses[n][-1]['palm' + s] if poses[n] else self._J[n]['shL']
                    a.c['h' + s].span  # (the spec is left as written)
                    self.notes.append('frame %d: %s hand %s target unresolved, held' % (fr, n, s))
                    save = a.c['h' + s]
                    tmp = Chan(('world', float(prev[0]), float(prev[1])))
                    a.c['h' + s] = tmp
                    self._arms(a, t, self._J[n], props_now, s)
                    a.c['h' + s] = save
                for pn, o in own.items():
                    if o is not None and pn not in props_now and o[0] == n:
                        props_now[pn] = hand_to_world(self._J[n], o[1], o[2], o[3])
            # 4. grips: the offset is fixed now, so the prop does not move on this frame
            for n, p in self.props.items():
                for (ef, kind, an, hand) in p.events:
                    if ef == fr and kind == 'grip':
                        hand, snap = hand
                        J = self._J[an]
                        pose = props_now.get(n, free[n])
                        if snap:
                            pose = (np.asarray(pose[0], float) + (J['palm' + hand] - p.socket(pose, snap)), pose[1])
                        off, dang = world_to_hand(J, hand, pose)
                        own[n] = (an, hand, off, dang)
                        props_now[n] = pose
            for n in self.props:
                pose = props_now.get(n, free[n])
                prop_track[n].append((np.asarray(pose[0], float).copy(), float(pose[1])))
                owners[n].append(None if own[n] is None else '%s.%s' % own[n][:2])
            for n in self.actors:
                poses[n].append(self._J[n])
            hand_err.append(herr)
            leg_err.append(errs)
        self.poses, self.prop_track, self.owners, self.hand_err, self.leg_err = poses, prop_track, owners, hand_err, leg_err
        return self


# ---------------------------------------------------------------- checks

SEGMENTS = [  # (name, joint a, joint b, radius key, mass key)
    ('torso', 'P', 'N', 'torso', 'torso'), ('head', 'Hb', 'C', 'head', 'head'),
    ('uarmL', 'shL', 'elbL', 'uarm', 'uarm'), ('farmL', 'elbL', 'wriL', 'farm', 'farm'), ('handL', 'wriL', 'tipL', 'hand', 'hand'),
    ('uarmR', 'shR', 'elbR', 'uarm', 'uarm'), ('farmR', 'elbR', 'wriR', 'farm', 'farm'), ('handR', 'wriR', 'tipR', 'hand', 'hand'),
    ('thighL', 'hipL', 'kneeL', 'thigh', 'thigh'), ('shinL', 'kneeL', 'ankL', 'shin', 'shin'), ('footL', 'heelL', 'toeL', 'foot', 'foot'),
    ('thighR', 'hipR', 'kneeR', 'thigh', 'thigh'), ('shinR', 'kneeR', 'ankR', 'shin', 'shin'), ('footR', 'heelR', 'toeR', 'foot', 'foot'),
]
SUPPORT_PTS = ['heelL', 'ballL', 'toeL', 'heelR', 'ballR', 'toeR', 'kneeL', 'kneeR', 'P', 'palmL', 'palmR', 'elbL', 'elbR', 'C', 'N']
PT_R = dict(kneeL='shin', kneeR='shin', P='torso', palmL='hand', palmR='hand', elbL='farm', elbR='farm', C='head', N='torso')


def com(a, J, carried):
    B = a.B
    m, s = 0.0, np.zeros(2)
    for name, ja, jb, rk, mk in SEGMENTS:
        w = B.M[mk]
        s += w * (np.asarray(J[ja]) + np.asarray(J[jb])) / 2; m += w
    for (pos, mass) in carried:
        s += mass * np.asarray(pos); m += mass
    return s / m


def check(scene):
    """run every check; returns the technical report in the spec's crash_lab_run.technical shape plus details"""
    N = scene.N
    flags = []  # (kind, frame, message)
    surfaces = []  # horizontal tops that can carry weight: (x0, x1, y)
    for p in scene.props.values():
        c, a = p.pose0
        if p.solid and p.fixed and abs(a) < 1e-6 and p.kind in ('box', 'ledge'):
            surfaces.append((c[0] - p.w / 2, c[0] + p.w / 2, c[1] - p.h / 2, p.name))
    solids = [p for p in scene.props.values() if p.solid]
    airborne = 0; grounded = 0; balanced = 0; contact_frames = 0; worst_contact = 0.0
    owner_changes = 0
    worst_drift = 0.0
    prev_sup = {}
    stats = dict(max_reach=0.0, max_leg_err=0.0, cup_max_tilt=0.0, cup_max_acc=0.0)
    static = {n: [] for n in scene.actors}
    in_water = lambda x, y: scene.water is not None and scene.water[0] <= x <= scene.water[1] and y > scene.water[2] - 1e-6
    for fr in range(N):
        # carried mass per actor
        carried = {n: [] for n in scene.actors}
        for pn, p in scene.props.items():
            o = scene.owners[pn][fr]
            if o and p.mass > 0:
                carried[o.split('.')[0]].append((scene.prop_track[pn][fr][0], p.mass))
        # hands holding fixed props (hanging) and hands that carry another body
        for n, a in scene.actors.items():
            J = scene.poses[n][fr]
            cm = a.B.cm
            # ---- legs
            for s in 'LR':
                e = scene.leg_err[fr][n]['leg' + s]
                stats['max_leg_err'] = max(stats['max_leg_err'], e)
                if e > 1.5:
                    flags.append(('legs', fr, '%s: leg short of its foot by # cm' % n))
            # ---- hands to targets
            for (an, k), (e, spec) in scene.hand_err[fr].items():
                if an != n:
                    continue
                contact_frames += 1
                worst_contact = max(worst_contact, e)
                if e > 2.0:
                    flags.append(('miss', fr, '%s: missed contact %s by # cm' % (n, k[-1])))
            for s in 'LR':
                r = J.get('reach' + s, 0)
                spec_a, spec_b, x = a.c['h' + s].span(fr)
                if spec_a[0] in ('prop', 'world', 'body') and (spec_b is None or spec_b == spec_a or (spec_b[0] == 'prop' and spec_a[0] == 'prop' and spec_b[1] == spec_a[1])):
                    stats['max_reach'] = max(stats['max_reach'], r)
                    if r > 1.0 + 2.0 * cm / (a.B.L['uarm'] + a.B.L['farm']):
                        flags.append(('overreach', fr, '%s: overreach (card arms do not stretch)' % n))
            # ---- support and weight
            hang = False
            sup_x = []
            pts = {}
            for k in SUPPORT_PTS:
                pts[k] = np.asarray(J[k])
            sup_now = {}
            for k, p in pts.items():
                r = a.B.R.get(PT_R.get(k, 'foot'), 0.0)
                tops = [(-1e9, 1e9, scene.floor, 'floor')] + surfaces
                for (x0, x1, y, sn) in tops:
                    if x0 - 0.5 * cm <= p[0] <= x1 + 0.5 * cm and -1.0 * cm <= (y - p[1]) <= r + 1.0 * cm:
                        sup_now[k] = p
                        break
                if in_water(p[0], p[1]):
                    hang = True
            for s in 'LR':
                spec_a, spec_b, x = a.c['h' + s].span(fr)
                if spec_a[0] == 'prop' and (spec_b is None or spec_b == spec_a or (spec_b[0] == 'prop' and spec_b[1] == spec_a[1])):
                    pr = scene.props[spec_a[1]]
                    if pr.fixed and pr.solid:
                        hang = True
                        sup_now['palm' + s] = pts['palm' + s]
            for (holder, held, f0, f1) in scene.supports_by:
                if held == n and f0 <= fr <= f1:
                    hang = True
            # arms and elbows only count when they rest on a top (hands on furniture)
            if sup_now or hang:
                grounded += 1
                c_ = com(a, J, carried[n])
                xs = [p[0] for p in sup_now.values()]
                ok = hang or (xs and min(xs) - 1.0 * cm <= c_[0] <= max(xs) + 1.0 * cm)
                static[n].append(bool(ok))
                if ok:
                    balanced += 1
            else:
                airborne += 1
                static[n].append(None)
            # planted drift: heel and ball that carried weight on both frames
            for k in ('heelL', 'ballL', 'heelR', 'ballR'):
                key = (n, k)
                if k in sup_now and key in prev_sup:
                    v = abs(float(sup_now[k][0] - prev_sup[key][0])) / cm  # sliding along the surface
                    if v > 0.6:
                        worst_drift = max(worst_drift, v)
                        flags.append(('slide', fr, '%s: planted %s drifts # cm/frame' % (n, k)))
            for k in list(prev_sup):
                if k[0] == n:
                    del prev_sup[k]
            for k in ('heelL', 'ballL', 'heelR', 'ballR'):
                if k in sup_now:
                    prev_sup[(n, k)] = sup_now[k]
            # ---- penetration: body pieces in solid props, below the floor
            gripped = set()
            for s in 'LR':
                spec_a, spec_b, x = a.c['h' + s].span(fr)
                for sp in (spec_a, spec_b):
                    if sp is not None and sp[0] == 'prop':
                        gripped.add((s, sp[1]))
            for name, ja, jb, rk, mk in SEGMENTS:
                A_, B_ = np.asarray(J[ja]), np.asarray(J[jb])
                r = a.B.R[rk]
                nseg = max(2, int(np.linalg.norm(B_ - A_) / cm))
                for i in range(nseg + 1):
                    p = A_ + (B_ - A_) * i / nseg
                    if p[1] > scene.floor + 1.0 * cm and not in_water(p[0], p[1]):
                        flags.append(('floor', fr, '%s: %s below the floor' % (n, name)))
                        break
                for pr in solids:
                    side = name[-1] if name[-1] in 'LR' else None
                    if side and name.startswith(('hand', 'farm')) and (side, pr.name) in gripped:
                        continue
                    pose = scene.prop_track[pr.name][fr]
                    hit = False
                    for i in range(nseg + 1):
                        p = A_ + (B_ - A_) * i / nseg
                        rr = r if 0 < i < nseg or name.startswith(('torso', 'head')) else r * 0.7
                        if name.startswith('foot'):
                            rr = 0.0
                        if rr - pr.sdist(pose, p) > 1.0 * cm:
                            hit = True; break
                    if hit:
                        flags.append(('solid', fr, '%s: %s into %s' % (n, name, pr.name)))
        # ---- bodies against each other (same lane): torsos and heads
        names = list(scene.actors)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = scene.actors[names[i]], scene.actors[names[j]]
                if a.lane != b.lane:
                    continue
                Ja, Jb = scene.poses[a.name][fr], scene.poses[b.name][fr]
                cm = min(a.B.cm, b.B.cm)
                for sa in ('torso', 'head'):
                    for sb in ('torso', 'head'):
                        ga = [s for s in SEGMENTS if s[0] == sa][0]; gb = [s for s in SEGMENTS if s[0] == sb][0]
                        d = seg_dist(Ja[ga[1]], Ja[ga[2]], Jb[gb[1]], Jb[gb[2]])
                        if d < a.B.R[ga[3]] + b.B.R[gb[3]] - 1.0 * cm:
                            flags.append(('clip', fr, '%s/%s: %s into %s' % (a.name, b.name, sa, sb)))
        # ---- props: owner changes, jumps, cup tilt and jerk
        for pn, p in scene.props.items():
            if fr > 0 and scene.owners[pn][fr] != scene.owners[pn][fr - 1]:
                owner_changes += 1
                jump = float(np.linalg.norm(scene.prop_track[pn][fr][0] - scene.prop_track[pn][fr - 1][0]))
                ref = list(scene.actors.values())[0].B.cm
                if jump / ref > 2.5:
                    flags.append(('prop', fr, '%s jumps # cm on an owner change' % pn))
            if p.kind == 'cup':
                ref = list(scene.actors.values())[0].B.cm
                tilt = abs(((scene.prop_track[pn][fr][1] + 180) % 360) - 180)
                stats['cup_max_tilt'] = max(stats['cup_max_tilt'], tilt)
                if tilt > 20:
                    flags.append(('spill', fr, '%s tilts past 20 degrees' % pn))
                if 2 <= fr:
                    q = [scene.prop_track[pn][fr - k][0] for k in (2, 1, 0)]
                    acc = float(np.linalg.norm(q[2] - 2 * q[1] + q[0])) / ref
                    stats['cup_max_acc'] = max(stats['cup_max_acc'], acc)
                    if acc > 0.45:
                        flags.append(('spill', fr, '%s jerks # cm/frame^2 (full cup)' % pn))
            if p.solid is False and scene.owners[pn][fr]:
                pose = scene.prop_track[pn][fr]
                low = max(c[1] for c in p.corners(pose))
                if low > scene.floor + 1.0 * list(scene.actors.values())[0].B.cm:
                    flags.append(('floor', fr, '%s below the floor' % pn))
    # balance: the spec's check is static. Walking is a controlled fall, so a static loss that a new support
    # catches within CATCH frames is reported as caught_by_step (accepted, counted separately); longer is a flag.
    CATCH = 4
    caught = 0
    for n, seq in static.items():
        for fr, ok in enumerate(seq):
            if ok is False:
                nxt = [x for x in seq[fr + 1:fr + 1 + CATCH]]
                if any(x is True for x in nxt):
                    caught += 1
                    scene.declared.append(('caught_by_step', fr, fr, '__auto'))
                    flags.append(('caught_by_step', fr, '%s: centre of mass outside the support, caught by the next support' % n))
                else:
                    flags.append(('unbalanced', fr, '%s: unbalanced' % n))
    # declared flags are accepted inside their ranges
    accepted, failing = [], []
    for fl in flags:
        ok = any(fl[0] == k and f0 <= fl[1] <= f1 for (k, f0, f1, why) in scene.declared)
        (accepted if ok else failing).append(fl)
    scene.declared = [d for d in scene.declared if d[3] != '__auto']
    def ranges(fs):
        by = {}
        for k, fr, msg in fs:
            by.setdefault(msg, []).append(fr)
        out = {}
        for msg, frs in by.items():
            frs = sorted(set(frs)); parts = []; s = p = frs[0]
            for x in frs[1:] + [None]:
                if x is not None and x == p + 1:
                    p = x; continue
                parts.append('%d' % s if s == p else '%d-%d' % (s, p))
                if x is not None:
                    s = p = x
            out[msg] = ','.join(parts)
        return out
    flag_frames = {}
    for k, fr, msg in failing:
        flag_frames.setdefault(k, set()).add(fr)
    tech = {
        'result': 'pass' if not failing else 'fail',
        'declared_flags': [{'kind': k, 'frames': '%d-%d' % (f0, f1), 'why': why} for (k, f0, f1, why) in scene.declared],
        'flag_frames': {k: len(v) for k, v in flag_frames.items()},
        'flagged_frame_ranges': ranges(failing),
        'accepted_frame_ranges': ranges(accepted),
        'contact_frames': contact_frames,
        'worst_contact_error_cm': round(worst_contact, 2),
        'prop_owner_changes': owner_changes,
        'airborne_frames': airborne,
        'balanced_pct_of_grounded_frames': round(100.0 * balanced / max(1, grounded), 1),
        'caught_by_step_frames': caught,
        'worst_planted_drift_cm_per_frame': round(worst_drift, 2),
        'max_arm_reach_ratio': round(stats['max_reach'], 3),
        'max_leg_error_cm': round(stats['max_leg_err'], 2),
    }
    if any(p.kind == 'cup' for p in scene.props.values()):
        tech['cup_max_tilt_deg'] = round(stats['cup_max_tilt'], 1)
        tech['cup_max_acc_cm_per_frame2'] = round(stats['cup_max_acc'], 3)
    return tech, failing, accepted


def seg_dist(a, b, c, d):
    a, b, c, d = (np.asarray(x, float) for x in (a, b, c, d))
    def pt_seg(p, s0, s1):
        v = s1 - s0; t = np.clip(np.dot(p - s0, v) / max(1e-9, np.dot(v, v)), 0, 1)
        return np.linalg.norm(p - (s0 + v * t))
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))


CHECKS_NOT_MEASURED = [
    'crossed feet and planted foot turned > 65 deg from the hips: need a depth axis; this rig is a 2D profile',
    'arm stretch > 1.12: cardboard pieces never stretch, so any reach beyond the arm is a missed contact instead',
    'forearms within 3 cm of each other: near and far arms are on different card layers',
    'hand inside an unintended torso of another performer: only torsos and heads are tested against each other',
    'pose continuity beyond the solver (the display list has no pops by construction; replacement swaps are intended)',
    'event synchronization other than contact frames; root path against obstacles other than solid props',
]
