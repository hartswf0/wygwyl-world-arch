"""The performance layer over rigkit: actors, clips, retargeting, ground contact.

A MotionClip is actor-independent data (see clip()). A frame holds:
  view     which painted rig to use ('front', 'q3r', ...); a change of view is a drawing swap
  bones    absolute screen angles in degrees for chest, uarmR/L, farmR/L, thighR/L, shinR/L
           (0 = pointing screen-right, 90 = straight down; clips are authored facing right)
  rel      offsets in degrees from the painted rest angle for head (on top of the chest),
           handR/L (on top of the forearm) and footR/L; markers for these are unreliable, so they
           stay relative to the drawing
  body     whole-figure rotation in degrees (a fall), applied about the anchor
  anchor   'footR' / 'footL' (that ankle is locked where it lands), or 'ground' (the figure is
           dropped onto the floor by its lowest painted pixel)
  contact  {'footR': bool, 'footL': bool, 'handR': prop id or None, ...}
  ik       {'handR': [x, y]} world target for the hand tip, solved per actor (props are scene data)
  x        optional root x override in stage px (used once to place an actor)

An Actor is a cast member: a rigkit character plus a height. Retargeting turns a clip frame into
rigkit bone parameters: P[bone] = absolute angle - the actor's painted rest angle for that bone.
The choreography (angles, timing, contacts) is identical for every actor; only the drawings and
the proportions change.
"""
import math
import numpy as np

from rigkit import posing

BONES = {'chest': ('midhip', 'neck'),
         'uarmR': ('shR', 'elR'), 'farmR': ('elR', 'wrR'), 'uarmL': ('shL', 'elL'), 'farmL': ('elL', 'wrL'),
         'thighR': ('hipR', 'knR'), 'shinR': ('knR', 'anR'), 'thighL': ('hipL', 'knL'), 'shinL': ('knL', 'anL')}
REL = ('head', 'handR', 'handL', 'footR', 'footL')
PX_PER_CM = 2.4


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def ang(v):
    return math.atan2(v[1], v[0])


class Actor:
    """a cast member: rigkit character + height in cm. Every view is scaled so its painted legs and
    torso match the front view's, so a view swap does not change the actor's size."""

    def __init__(self, char, height_cm, name=None, views=('front', 'q3r')):
        self.char, self.name = char, name or char.split('__')[0]
        self.height_cm = height_cm
        self.rigs = {v: posing.rig(char, v) for v in views}
        self.lib = posing.parts(char)
        F = self.rigs['front'].J
        H = np.linalg.norm(F['headtop'] - (F['anR'] + F['anL']) / 2)
        self.ref_cm = height_cm * self.body_len(F) / H
        self.scale = {v: self.ref_cm * PX_PER_CM / self.body_len(R.J) for v, R in self.rigs.items()}
        self.rest = {v: {b: ang(R.J[q] - R.J[p]) for b, (p, q) in BONES.items()} for v, R in self.rigs.items()}

    @staticmethod
    def body_len(J):
        L = lambda a, b: np.linalg.norm(J[a] - J[b])
        legs = (L('hipR', 'knR') + L('knR', 'anR') + L('hipL', 'knL') + L('knL', 'anL')) / 2
        return legs + L('midhip', 'neck')

    def proportions(self):
        """bone lengths in cm in the front view, the actor's identity numbers"""
        J, s = self.rigs['front'].J, self.scale['front'] / PX_PER_CM
        L = lambda a, b: float(np.linalg.norm(J[a] - J[b]) * s)
        return {'height': self.height_cm, 'torso': L('midhip', 'neck'), 'thigh': (L('hipR', 'knR') + L('hipL', 'knL')) / 2,
                'shin': (L('knR', 'anR') + L('knL', 'anL')) / 2, 'upper_arm': (L('shR', 'elR') + L('shL', 'elL')) / 2,
                'forearm': (L('elR', 'wrR') + L('elL', 'wrL')) / 2, 'shoulders': L('shR', 'shL'),
                'head': L('headpiv', 'headtop')}

    # ---------------------------------------------------------------- retarget
    def params(self, fr):
        v = fr['view']
        rest = self.rest[v]
        rel = fr.get('rel', {})
        P = {}
        for b in BONES:
            P[b] = wrap(math.radians(fr['bones'][b]) - rest[b])
        P['head'] = math.radians(rel.get('head', 0.))
        for S in 'RL':
            P['hand' + S] = P['farm' + S] + math.radians(rel.get('hand' + S, 0.))
            P['foot' + S] = math.radians(rel.get('foot' + S, 0.))
        return P

    def G(self, view, root, body_deg=0.):
        """affine rig -> stage: scale, rotate by the body angle, rig midhip onto root"""
        s = self.scale[view]
        c, sn = math.cos(math.radians(body_deg)), math.sin(math.radians(body_deg))
        G = np.array([[s * c, -s * sn, 0.], [s * sn, s * c, 0.]])
        G[:, 2] = np.asarray(root, float) - G[:, :2] @ self.rigs[view].J['midhip']
        return G

    def fk(self, view, P, G):
        """world joints and the world silhouette points (every mesh vertex)"""
        R = self.rigs[view]
        A = R.transforms(P)
        jp = {k: G[:, :2] @ p + G[:, 2] for k, p in R.joint_pos(A).items()}
        pts = np.vstack([R.deform(n, A) for n in R.order]) @ G[:, :2].T + G[:, 2]
        return jp, pts

    def legs(self, view):
        """world leg geometry for a view: thigh and shin lengths per side, the mean leg length Lg, and
        how far each foot's lowest painted pixel sits below its ankle (measured on the rest drawing)"""
        if not hasattr(self, '_legs'):
            self._legs = {}
        if view not in self._legs:
            J, s = self.rigs[view].J, self.scale[view]
            out = {S: {'thigh': np.linalg.norm(J['kn' + S] - J['hip' + S]) * s,
                       'shin': np.linalg.norm(J['an' + S] - J['kn' + S]) * s} for S in 'RL'}
            Lg = np.mean([out[S]['thigh'] + out[S]['shin'] for S in 'RL'])
            jp, pts = self.fk(view, {}, self.G(view, (0., 0.)))
            for S in 'RL':
                near = pts[np.linalg.norm(pts - jp['an' + S], axis=1) < 0.3 * Lg]
                out[S]['foot_h'] = float(near[:, 1].max() - jp['an' + S][1]) if len(near) else 0.
            out['Lg'] = float(Lg)
            self._legs[view] = out
        return self._legs[view]

    def stand_ankle(self, view):
        """ankle heights relative to the floor (px, negative = above) when this actor stands in this
        view with its lowest painted pixel on the floor: the depth of each foot in the drawing"""
        if not hasattr(self, '_stand'):
            self._stand = {}
        if view not in self._stand:
            from studio.actions import STAND
            fr = {'view': view, 'bones': STAND[view]}
            jp, pts = self.fk(view, self.params(fr), self.G(view, (0., 0.)))
            low = pts[:, 1].max()
            self._stand[view] = {S: float(jp['an' + S][1] - low) for S in 'RL'}
        return self._stand[view]

    def arm_ik(self, fr, S, target):
        """two-bone IK in world space: set uarmS / farmS so the hand tip reaches target (elbow down)"""
        v = fr['view']
        J, s = self.rigs[v].J, self.scale[v]
        L1 = np.linalg.norm(J['el' + S] - J['sh' + S]) * s
        L2 = np.linalg.norm(J['tip' + S] - J['el' + S]) * s
        return L1, L2


def two_bone(root, target, L1, L2, bend=1.0):
    d = np.asarray(target, float) - root
    D = max(1e-6, min(np.linalg.norm(d), (L1 + L2) * 0.999))
    a0 = ang(d)
    c1 = np.clip((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D), -1, 1)
    a1 = a0 + bend * math.acos(c1)
    elbow = root + L1 * np.array([math.cos(a1), math.sin(a1)])
    a2 = ang(np.asarray(target, float) - elbow)
    return a1, a2


class Performer:
    """plays clips on one actor on a stage, keeping state (root, locked feet) between frames"""

    def __init__(self, actor, stage, x, facing='R'):
        self.a, self.stage, self.facing = actor, stage, facing
        self.root = np.array([x if facing == 'R' else stage['W'] - x, stage['floor'] - 100.], float)
        self.lock = {}
        self.first = True

    def solve(self, fr):
        """-> dict with view, P, G, world joints (stage coords, facing applied), silhouette, contacts"""
        a, v = self.a, fr['view']
        fr = dict(fr)
        if 'blend' in fr and getattr(self, 'last_abs', None) is not None:
            # animation mixing: ease from the pose this actor actually held (measured) into the clip
            if fr['blend'].get('start'):
                self.blend_src = dict(self.last_abs)
            u = fr['blend']['u']
            src = getattr(self, 'blend_src', self.last_abs)
            fr['bones'] = {b: math.degrees(math.radians(src[b]) + u * wrap(math.radians(fr['bones'][b]) - math.radians(src[b])))
                           for b in fr['bones']}
        P = a.params(fr)
        body = fr.get('body', 0.)
        if 'x' in fr:
            self.root[0] = fr['x'] if self.facing == 'R' else self.stage['W'] - fr['x']
            self.lock = {}
        anchor = fr.get('anchor', 'ground')
        if 'gait' in fr:
            self.gait(fr, P, body)
        else:
            self.gait_x0 = None
            G = a.G(v, self.root, body)
            jp, pts = a.fk(v, P, G)
            shift = np.zeros(2)
            c0 = fr.get('contact', {})
            if c0.get('footR') and c0.get('footL') and not fr.get('body'):
                self.handoff = None             # standing on both feet again
            if anchor.startswith('foot') and getattr(self, 'handoff', None):
                anchor = self.handoff           # the weight already moved to the other foot
                fr['anchor'] = anchor
                fr['contact'] = {k: v for k, v in fr.get('contact', {}).items() if not k.startswith('foot')}
                fr['contact'][anchor] = True
            elif not anchor.startswith('foot'):
                self.handoff = None
            if anchor.startswith('foot'):
                # a planted foot is locked in x and y where it planted (in a 3/4 drawing the far foot
                # stands higher on screen than the near one: that offset is depth, so the floor line
                # only places the figure when the foot first plants)
                k = 'an' + anchor[-1]
                if anchor not in self.lock or self.first:
                    # x where it is now; y at the depth this foot has when the actor stands in this view
                    self.lock = {anchor: np.array([jp[k][0], self.stage['floor'] + a.stand_ankle(v)[anchor[-1]]])}
                shift = self.lock[anchor] - jp[k]
                c = fr.get('contact', {})
                if c.get('footR') and c.get('footL') and not fr.get('body'):
                    # standing on both feet: the lowest painted pixel is on the floor (settles any
                    # depth left over from a single-foot phase); the planted ankle keeps its x
                    shift[1] = self.stage['floor'] - pts[:, 1].max()
                    self.lock[anchor] = jp[k] + shift
                low = pts[:, 1].max() + shift[1] - self.stage['floor']
                if low > 0.5:
                    # another part reached the floor first. If it is the other foot, the weight moves
                    # onto it (a step): that foot plants where it touches and the first one is released.
                    o = 'R' if anchor[-1] == 'L' else 'L'
                    lowest = pts[np.argmax(pts[:, 1])] + shift
                    if np.linalg.norm(lowest - (jp['an' + o] + shift)) < 0.35 * a.legs(v)['Lg']:
                        shift[1] -= low
                        self.handoff = 'foot' + o
                        self.lock = {'foot' + o: jp['an' + o] + shift}
                        fr['anchor'] = 'foot' + o
                        fr['contact'] = {k: c for k, c in fr.get('contact', {}).items() if not k.startswith('foot')}
                        fr['contact']['foot' + o] = True
                    else:               # never through the floor, even if that moves the planted foot
                        shift[1] -= low
            else:
                # the lowest painted pixel sits on the floor; 'feet' also keeps the ankles' midpoint x
                # (a turn in place: the drawing swap moves each foot, the stance centre stays)
                shift[1] = self.stage['floor'] - pts[:, 1].max()
                if anchor == 'feet':
                    ax = (jp['anR'][0] + jp['anL'][0]) / 2
                    if anchor not in self.lock or self.first:
                        self.lock = {anchor: ax}
                    shift[0] = self.lock[anchor] - ax
                else:
                    self.lock = {}
            self.root = self.root + shift
        self.first = False
        # hand IK on the clip's world targets, after the body is placed (targets in stage coords)
        for S, tgt in fr.get('ik', {}).items():
            jp, _ = a.fk(v, P, a.G(v, self.root, body))
            if isinstance(tgt, dict):       # {'from', 'to', 'u'}: either end may be 'rest' (the clip's own hand)
                end = []
                for e in (tgt['from'], tgt['to']):
                    if isinstance(e, str):
                        end.append(jp['tip' + S])
                    else:
                        e = np.array(e, float)
                        if self.facing == 'L':
                            e[0] = self.stage['W'] - e[0]
                        end.append(e)
                tgt = end[0] + (end[1] - end[0]) * tgt['u']
            else:
                tgt = np.array(tgt, float)
                if self.facing == 'L':
                    tgt[0] = self.stage['W'] - tgt[0]
            L1, L2 = a.arm_ik(fr, S, tgt)
            J = a.rigs[v].J
            a1, a2 = two_bone(jp['sh' + S], tgt, L1, L2, bend=1.0)
            P['uarm' + S] = wrap(a1 - ang(J['el' + S] - J['sh' + S]))
            P['farm' + S] = wrap(a2 - ang(J['tip' + S] - J['el' + S]))
            P['hand' + S] = P['farm' + S] + math.radians(fr.get('rel', {}).get('hand' + S, 0.))
        G = a.G(v, self.root, body)
        jp, pts = a.fk(v, P, G)
        # what the actor actually held this frame (internal coords, body rotation removed): a later
        # clip blends from it
        self.last_abs = {b: math.degrees(wrap(ang(jp[q] - jp[p_]) - math.radians(body))) for b, (p_, q) in BONES.items()}
        gait_err = None
        if 'gait' in fr:      # how far each ankle is from its foot target, in leg lengths
            gait_err = max(float(np.linalg.norm(jp['an' + S] - self.gait_tgt[S])) for S in 'RL') / a.legs(v)['Lg']
        if self.facing == 'L':
            W = self.stage['W']
            jp = {k: np.array([W - p[0], p[1]]) for k, p in jp.items()}
            pts = pts.copy(); pts[:, 0] = W - pts[:, 0]
        return {'view': v, 'P': P, 'G': G, 'jp': jp, 'pts': pts, 'fr': fr, 'facing': self.facing, 'gait_err': gait_err}

    def gait(self, fr, P, body):
        """legs by IK from normalised foot targets. fr['gait'] = {'root': [u, drop], 'feet': {S: [u, lift]}}
        with every length in units of this actor's leg length Lg, measured from where the gait began.
        A planted foot is a fixed target, so it cannot slide; the pelvis rides at (0.93 - drop) Lg."""
        a, v = self.a, fr['view']
        g = fr['gait']
        Lgs = a.legs(v)
        Lg = Lgs['Lg']
        if getattr(self, 'gait_x0', None) is None:
            self.gait_x0 = self.root[0] - g['root'][0] * Lg
        fl = self.stage['floor']
        dep = a.stand_ankle(v)                       # each foot walks at its standing depth
        base = fl + max(dep[S] for S in 'RL')       # pelvis height from the nearer (lower) foot, so both reach
        self.root = np.array([self.gait_x0 + g['root'][0] * Lg, base - (0.95 - g["root"][1]) * Lg])
        jp, _ = a.fk(v, P, a.G(v, self.root, body))
        # hips sit a little apart from midhip; keep the pelvis height measured from the hips
        hip_y = np.mean([jp['hipR'][1], jp['hipL'][1]])
        self.root[1] += (base - (0.95 - g["root"][1]) * Lg) - hip_y
        jp, _ = a.fk(v, P, a.G(v, self.root, body))
        J = a.rigs[v].J
        self.gait_tgt = {}
        for S in 'RL':
            u, lift = g['feet'][S]
            tgt = np.array([self.gait_x0 + u * Lg, fl + dep[S] - lift * Lg])
            best = None
            for bend in (1., -1.):      # the knee points forward (toward +x, the way the figure faces)
                a1, a2 = two_bone(jp['hip' + S], tgt, Lgs[S]['thigh'], Lgs[S]['shin'], bend)
                kx = jp['hip' + S][0] + Lgs[S]['thigh'] * math.cos(a1)
                if best is None or kx > best[0]:
                    best = (kx, a1, a2)
            _, a1, a2 = best
            self.gait_tgt[S] = tgt
            P['thigh' + S] = wrap(a1 - ang(J['kn' + S] - J['hip' + S]))
            P['shin' + S] = wrap(a2 - ang(J['an' + S] - J['kn' + S]))

    def render(self, st, ss=1):
        R = self.a.rigs[st['view']]
        W, H = self.stage['W'], self.stage['H']
        img, _ = R.render(st['P'], st['G'], (W, H), ss=ss, opts={}, lib=self.a.lib)
        if self.facing == 'L':
            img = img[:, ::-1].copy()
        return img
