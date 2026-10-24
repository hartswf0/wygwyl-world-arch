"""Pose selection: animate an actor by choosing among its own paintings (the swarm approach).

The swarms (Pose2Pose casting, Dynamic Pose Selection, Multiview Drawing Substitution, Reiniger,
Cartoon Saloon, Harmony) agree on one rule for painted characters: when a pose is not in the
drawing, swap to a drawing that has it; do not bend one drawing into every pose. So:

  library   every clean painting of the actor in one costume, with its pose read from its markers
            (bone angles, mirrored to face right), its view, and its anchor points
  target    a performance (studio clips, solved on a reference rig) gives the wanted pose per frame
  decode    Viterbi over the library on twos (12 drawings a second): match cost (pose distance) +
            switch cost (a change of drawing must earn its keep), views must agree
  place     each chosen painting is placed whole: scaled to the actor's height, its planted ankle on
            the performance's planted ankle (so a held drawing never slides), its lowest pixel on the floor
  report    the decoder path, per-beat match error, and the poses the library cannot cover (the
            drawings to commission)
"""
import math, os
import numpy as np, cv2

from rigkit import core

ROOT = core.ROOT
BONES = {'chest': ('groin', 'neck'), 'uarmA': ('shoulderR', 'elbowR'), 'farmA': ('elbowR', 'wristR'),
         'uarmB': ('shoulderL', 'elbowL'), 'farmB': ('elbowL', 'wristL'),
         'thighA': ('hipR', 'kneeR'), 'shinA': ('kneeR', 'ankleR'), 'thighB': ('hipL', 'kneeL'), 'shinB': ('kneeL', 'ankleL')}
RIG_BONES = {'chest': ('midhip', 'neck'), 'uarmA': ('shR', 'elR'), 'farmA': ('elR', 'wrR'), 'uarmB': ('shL', 'elL'),
             'farmB': ('elL', 'wrL'), 'thighA': ('hipR', 'knR'), 'shinA': ('knR', 'anR'), 'thighB': ('hipL', 'knL'),
             'shinB': ('knL', 'anL')}
VIEW_OF = {'front': 'front', '3qR': 'q3', '3qL': 'q3', 'profR': 'prof', 'profL': 'prof', 'back': 'back',
           'back3qR': 'back', 'back3qL': 'back'}
FACING = {'3qR': 'R', 'profR': 'R', '3qL': 'L', 'profL': 'L', 'back3qR': 'R', 'back3qL': 'L'}


def deg(v):
    return math.degrees(math.atan2(v[1], v[0]))


def adiff(a, b):
    return abs((a - b + 180) % 360 - 180)


class Drawing:
    """one painting, its pose and its anchors (all in its own pixels, mirrored to face right if needed)"""

    def __init__(self, t, cat):
        self.id = t['id']
        self.cat = cat
        self.view = VIEW_OF.get(cat.get('view') or '', None)
        self.mirror = FACING.get(cat.get('view') or '') == 'L'
        self.cls = cat.get('cls') or ''
        self.w, self.h = t['w'], t['h']
        m = {}
        for k, v in t['markers'].items():
            if v and (len(v) < 5 or not isinstance(v[4], (int, float)) or v[4] >= 0.2):
                x, y = float(v[0]), float(v[1])
                m[k] = np.array([self.w - x if self.mirror else x, y])
        if 'groin' not in m and 'hipR' in m and 'hipL' in m:
            m['groin'] = (m['hipR'] + m['hipL']) / 2
        self.m = m
        self.ang = {b: deg(m[q] - m[p]) for b, (p, q) in BONES.items() if p in m and q in m}
        L = lambda a, b: np.linalg.norm(m[a] - m[b]) if a in m and b in m else None
        legs = [x for x in (L('hipR', 'kneeR'), L('kneeR', 'ankleR'), L('hipL', 'kneeL'), L('kneeL', 'ankleL')) if x]
        self.body_px = (np.mean(legs) * 2 if len(legs) >= 2 else None, L('groin', 'neck'))
        self._img = None

    def ok(self):
        return self.view is not None and len(self.ang) >= 7 and all(self.body_px)

    def image(self):
        if self._img is None:
            src = next(os.path.join(ROOT, 'shots/kits/cut', self.id + e) for e in ('.webp', '.png')
                       if os.path.exists(os.path.join(ROOT, 'shots/kits/cut', self.id + e)))
            im = cv2.imread(src, cv2.IMREAD_UNCHANGED)
            if im.shape[2] == 3:
                im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
            if (im.shape[1], im.shape[0]) != (self.w, self.h):
                im = cv2.resize(im, (self.w, self.h), interpolation=cv2.INTER_AREA)
            self._img = im[:, ::-1].copy() if self.mirror else im
        return self._img


def library(char, costume=None, uses=('ok',), props_ok=()):
    """clean drawings of the actor: one costume, a usable full figure, and no props or scenery baked
    into the cutout unless the scene asks for that prop (a table or a motorbike in a walk is an odd piece)"""
    spec = core.char_module(char)
    cat = spec.catalog() if hasattr(spec, 'catalog') else {}
    out = []
    for tid, t in core.load_markers(char).items():
        c = cat.get(tid, {}) or {}
        if c.get('use', 'ok') not in uses or (costume and c.get('costume') != costume):
            continue
        if any(pr not in props_ok for pr in (c.get('props') or [])):
            continue
        # painting flags are mostly rig notes; only a different character or a multi-figure card disqualifies
        if hasattr(spec, 'painting_flags') and any(f.startswith('not the') or 'multi' in f for f in spec.painting_flags(tid, cat)):
            continue
        d = Drawing(t, c)
        if d.ok():
            out.append(d)
    return out


def pose_dist(a, b, w=None):
    """mean weighted angle difference; A/B limb labels may be swapped (marker sides are unreliable),
    so the better of the two pairings counts. Returns (degrees, swapped?)"""
    w = w or {}
    best = None
    for sw in (False, True):
        tot = n = 0.
        for k, va in a.items():
            kb = k if not sw or k == 'chest' else k[:-1] + ('B' if k[-1] == 'A' else 'A')
            if kb in b:
                wt = w.get(k[:-1] if k != 'chest' else k, 1.0)
                tot += wt * adiff(va, b[kb]); n += wt
        d = tot / max(n, 1e-6)
        if best is None or d < best[0]:
            best = (d, sw)
    return best


def target_from(st):
    """target pose (bone angles, rig R side = A) and view class from a solved studio frame (facing right)"""
    jp = st['jp']
    ang = {b: deg(jp[q] - jp[p]) for b, (p, q) in RIG_BONES.items()}
    view = {'front': 'front', 'q3r': 'q3'}.get(st['view'], st['view'])
    return ang, view


GAP_DEG = 14.0      # a beat whose best drawing is further than this is a gap: commission, don't substitute


def decode(lib, targets, weights, switch=9.0, view_pen=200.0, step=2):
    """Viterbi on every `step`-th frame. targets: list of (angles, view). Returns per-frame
    [(drawing index, match error, swapped)] and the beat path."""
    beats = list(range(0, len(targets), step))
    S = len(lib)
    INF = 1e18
    pair = np.zeros((S, S))
    for i in range(S):
        for j in range(S):
            if i != j:
                pair[i, j] = switch + 0.25 * pose_dist(lib[i].ang, lib[j].ang)[0]
    cost = np.full(S, 0.)
    back = []
    unary = []
    for bi, f in enumerate(beats):
        ang, view = targets[f]
        w = weights[f]
        u = np.array([pose_dist(ang, d.ang, w)[0] + (0 if d.view == view else view_pen) for d in lib])
        unary.append(u)
        if bi == 0:
            cost = u.copy(); back.append(np.arange(S)); continue
        tot = cost[:, None] + pair
        arg = tot.argmin(0)
        cost = tot[arg, np.arange(S)] + u
        back.append(arg)
    path = [int(cost.argmin())]
    for bi in range(len(beats) - 1, 0, -1):
        path.append(int(back[bi][path[-1]]))
    path = path[::-1]
    per_frame = []
    for f in range(len(targets)):
        bi = min(f // step, len(path) - 1)
        k = path[bi]
        d, sw = pose_dist(targets[f][0], lib[k].ang, weights[f])
        per_frame.append((k, d, sw))
    return per_frame, [(beats[i], path[i], float(unary[i][path[i]])) for i in range(len(path))]


def place(d, sw, st, actor_cm, px_per_cm, floor, facing='R', W=1280):
    """affine placement of drawing d: uniform scale to the actor's size; the anchor ankle (the
    performance's planted foot, else the pelvis) goes onto the performance's; lowest pixel to floor"""
    legs_cm, torso_cm = actor_cm
    s = 0.5 * ((legs_cm * px_per_cm) / d.body_px[0] + (torso_cm * px_per_cm) / d.body_px[1])
    jp = st['jp']
    planted = [k for k in ('footR', 'footL') if st['fr'].get('contact', {}).get(k)]
    side_rig = planted[0][-1] if planted else None
    if side_rig:
        # rig side R/L -> drawing marker side (A = marker R); facing L mirrors which foot is which
        mk = 'ankle' + (side_rig if not sw else ('L' if side_rig == 'R' else 'R'))
        src = d.m.get(mk, d.m['groin'])
        dst = jp['an' + side_rig]
    else:
        src, dst = d.m['groin'], jp['midhip']
    img = d.image()
    if facing == 'L':
        img = img[:, ::-1]
        src = np.array([d.w - src[0], src[1]])
    a = img[..., 3] > 40
    low = np.nonzero(a.any(1))[0].max()
    tx = dst[0] - s * src[0]
    ty = floor - s * low
    return img, s, tx, ty


def paste(canvas, img, s, tx, ty):
    H, W = canvas.shape[:2]
    M = np.array([[s, 0, tx], [0, s, ty]], np.float32)
    lay = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
    a = lay[..., 3:4].astype(np.float32) / 255.
    canvas[:] = (lay[..., :3] * a + canvas * (1 - a)).astype(np.uint8)
    return lay
