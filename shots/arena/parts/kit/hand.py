"""A hand drawn from its joints: palm, four three-segment fingers, a two-segment thumb.

The parameters are the Crash Lab's own (bolas lab/crash-lab gloveDraw): a shape
name, a grip amount 0-1, which way the palm faces, and the side. So any frame of
the Bolas bank can ask for exactly the hand Bolas drew, instead of the nearest of
four cards.

Frame: cm, wrist (A) at (0, 0), fingers pointing +y. Seen flat, as a cut-out hand
is: palm or back toward the camera. Curl foreshortens each segment by the cosine
of its accumulated bend, so past 90 degrees a finger folds back over the palm
(in front of it when the palm faces us, behind it when the back does). A fist
falls out of the geometry; nothing is drawn as a special case.

Handedness: with fingers down, a RIGHT hand showing its PALM has the thumb on -x.
Mirror swaps side and keeps what is shown, so L palm = mirror(R palm).
"""
import math
from . import vec

SKIN = '#8a644e'
SKIN_PALM = '#a47c64'
SKIN_SHADE = '#6e4c3a'
LINE = '#3b2a20'

# finger order: index, middle, ring, pinky
LEN = [7.9, 8.6, 8.1, 6.6]
WID = [1.85, 1.95, 1.85, 1.6]
SEG = [0.46, 0.31, 0.23]
BEND = [85, 100, 70]          # degrees at full curl, per joint

# shape -> (finger curls, thumb curl, thumb angle deg: + is away from the palm)
SHAPES = {
    'flat':    ([0, 0, 0, 0], 0.2, 38),
    'open':    ([0, 0, 0, 0], 0.0, 55),
    'relaxed': (None, None, 22),           # every curl = grip (the Crash Lab default)
    'point':   ([0, .95, .95, .95], .6, 5),
    'fist':    ([1, 1, 1, 1], .9, -18),
    'thumb':   ([1, 1, 1, 1], 0.0, 160),      # thumb back past the wrist: thumbs-up
    'pinch':   ([.45, .7, .85, .9], .45, 8),
    'peace':   ([0, 0, 1, 1], .8, -8),
    'grip':    ([.68, .7, .72, .75], .5, 10),   # round a bar or a box edge
    'cup':     ([.35, .35, .38, .4], .25, 30),
}


def thumb_side(side, shows):
    return -1 if (side == 'R') == (shows == 'palm') else 1


def _finger(base, length, width, curl, splay, front):
    """-> (segments drawn in front of the palm, segments behind) as capsules."""
    pts, cum = [base], 0.0
    p = list(base)
    for k, frac in enumerate(SEG):
        cum += BEND[k] * curl
        seg = length * frac
        dy = seg * math.cos(math.radians(cum))
        d = vec.rot([0, dy], splay)
        p = [p[0] + d[0], p[1] + d[1]]
        pts.append(p)
    caps = []
    for k in range(3):
        r0 = width / 2 * (1 - 0.08 * k)
        r1 = width / 2 * (1 - 0.08 * (k + 1))
        folded = sum(BEND[:k + 1]) * curl > 90
        caps.append(({'capsule': [pts[k], pts[k + 1]], 'r': [r0, r1], 'fill': SKIN, 'stroke': LINE, 'sw': 0.09}, folded))
    infront = [c for c, folded in caps if not folded or front]
    behind = [c for c, folded in caps if folded and not front]
    return infront, behind, pts


def hand(side='R', shows='palm', shape='relaxed', grip=0.25, wrist_tab=True):
    curls, th_curl, th_ang = SHAPES.get(shape or 'relaxed', SHAPES['relaxed'])
    if curls is None:
        curls, th_curl = [grip] * 4, grip
    ts = thumb_side(side, shows)
    palm_front = shows == 'palm'
    palm_col = SKIN_PALM if palm_front else SKIN
    # palm: wrist 6.2 wide, knuckles 8.4 wide, 9.4 long; heel pad bulges on the thumb side
    palm = [[-3.1, 0.4], [3.1, 0.4], [4.2, 4.5], [4.3, 9.0], [2.6, 9.9], [-2.6, 9.9], [-4.3, 9.0], [-4.0, 4.5]]
    palm = [[p[0], p[1]] for p in palm]
    palm_shape = {'poly': palm, 'fill': palm_col, 'stroke': LINE, 'sw': 0.1}
    behind, front, tips = [], [], []
    for i in range(4):
        x = ts * (3.0 - i * 2.0)
        splay = ts * (-6 + i * 4.5) * (1 - curls[i])
        f, b, pts = _finger([x, 9.2], LEN[i], WID[i], curls[i], splay, palm_front)
        front += f
        behind += b
        tips.append(pts[-1])
    # thumb: from the heel of the palm, two segments, rotating outward by th_ang
    tb = [ts * 3.6, 3.0]
    ang = ts * -th_ang                       # rotate +y toward the thumb side
    if shape == 'pinch':
        # aim the thumb at the index fingertip so the two tips meet
        dx, dy = tips[0][0] - tb[0], tips[0][1] - tb[1]
        ang = math.degrees(math.atan2(-dx, dy))
        th_curl = 0.0
        L = math.hypot(dx, dy)
    L1, L2 = 3.8, 3.3
    if shape == 'pinch':
        L1, L2 = L * 0.55, L * 0.45
    d1 = vec.rot([0, L1], ang)
    j1 = [tb[0] + d1[0], tb[1] + d1[1]]
    bend = th_curl * 70
    d2 = vec.rot([0, L2 * math.cos(math.radians(bend * 0.6))], ang - ts * bend * 0.9)
    tip = [j1[0] + d2[0], j1[1] + d2[1]]
    thumb = [{'capsule': [tb, j1], 'r': [1.35, 1.15], 'fill': SKIN, 'stroke': LINE, 'sw': 0.09},
             {'capsule': [j1, tip], 'r': [1.15, 0.95], 'fill': SKIN, 'stroke': LINE, 'sw': 0.09}]
    marks = []
    if palm_front:
        marks += [{'line': [[ts * 3.6, 4.5], [0, 6.2], [-ts * 3.8, 7.0]], 'stroke': SKIN_SHADE, 'w': 0.1, 'rim': False},
                  {'line': [[ts * 2.4, 2.2], [ts * 0.6, 5.5], [-ts * 1.2, 8.4]], 'stroke': SKIN_SHADE, 'w': 0.1, 'rim': False}]
    else:
        for i in range(4):
            x = ts * (3.0 - i * 2.0)
            marks.append({'circle': [x, 9.1], 'r': 0.32, 'fill': SKIN_SHADE, 'rim': False})
    shapes = []
    if wrist_tab:
        # the cardboard tab the wrist brad goes through, under the hand
        shapes += [{'capsule': [[0, -1.2], [0, 1.4]], 'r': [1.9, 2.3], 'fill': '#c9a57a', 'stroke': LINE, 'sw': 0.08}]
    shapes += behind
    if palm_front:
        shapes += [palm_shape] + marks + front + thumb
    else:
        shapes += thumb + [palm_shape] + marks + front
    if wrist_tab:
        shapes += vec.brad([0, 0], 0.7)
    sockets = {'A': [0.0, 0.0], 'B': [0.0, 9.9], 'palm': [0.0, 5.5],
               'index_tip': tips[0], 'thumb_tip': tip}
    return {'kind': 'hand', 'side': side, 'shows': shows, 'state': {'shape': shape, 'grip': grip},
            'shapes': shapes, 'sockets': sockets, 'socket_source': 'constructed'}


def mirror(part):
    """Left from right: flip x, swap side, keep what is shown."""
    def fx(p):
        return [-p[0], p[1]]
    out = dict(part)
    out['side'] = {'L': 'R', 'R': 'L'}.get(part['side'], part['side'])
    sh = []
    for s in part['shapes']:
        s = dict(s)
        for k in ('poly', 'line'):
            if k in s:
                s[k] = [fx(p) for p in s[k]]
        if 'circle' in s:
            s['circle'] = fx(s['circle'])
        if 'capsule' in s:
            s['capsule'] = [fx(p) for p in s['capsule']]
        sh.append(s)
    out['shapes'] = sh
    out['sockets'] = {k: fx(v) for k, v in part['sockets'].items()}
    return out
