"""Limbs, pelvis and boots drawn from their joints, in the man's colours.

Every part: cm, joint A at (0, 0), joint B straight down +y. Sockets are where
the part was built from, so they are exact.

Limbs have round ends centred on their joints, the oldest cut-out trick: a disc
turning on its own centre never opens a gap, whatever the angle, so a joint can
bend without the brad showing daylight.
"""
import math
from . import vec

CLOTH = '#202328'
CLOTH_HI = '#2c3037'
PIPING = '#d98a74'
SOLE = '#2a1d16'
LEATHER = '#16181c'
LEATHER_HI = '#4a4f58'
GUSSET = '#3a3d44'
LINE = '#0d0e10'

# cm: length A->B, radius at A, radius at B, piping?
LIMBS = {
    'uarm':  (28.0, 5.0, 4.2, True),
    'farm':  (26.0, 4.2, 3.4, True),
    'thigh': (44.0, 7.8, 5.9, True),
    'shin':  (43.0, 5.9, 4.4, True),
}


def limb(kind, length=None):
    L, ra, rb, pipe = LIMBS[kind]
    L = length or L
    a, b = [0.0, 0.0], [0.0, L]
    shapes = [{'capsule': [a, b], 'r': [ra, rb], 'fill': CLOTH, 'stroke': LINE, 'sw': 0.12}]
    shapes += vec.corrugate(a, b, ra, rb, col=CLOTH_HI)
    if pipe:
        shapes.append({'line': [[ra * 0.35, ra * 0.6], [rb * 0.35, L - rb * 0.6]], 'stroke': PIPING, 'w': 0.55, 'rim': False})
    if kind == 'farm':
        # sleeve cuff: the hand's tab tucks under it
        shapes.append({'line': [[-rb * 0.95, L - 1.6], [rb * 0.95, L - 1.6]], 'stroke': '#3a3e45', 'w': 0.3, 'rim': False})
    shapes += vec.brad(a) + vec.brad(b)
    return {'kind': kind, 'shapes': shapes, 'sockets': {'A': a, 'B': b}, 'socket_source': 'constructed',
            'length_cm': L}


def pelvis(view='profile'):
    """Hips and seat. Profile: the body faces +x. The thighs hang from 'hip'."""
    if view == 'profile':
        # waist 18 deep; seat bulges behind; the front drops to the crotch
        # critic, kit turn 3: a seat at x=-11 stood out behind the vest like a bustle
        outline = [[-7.5, 0], [7.0, 0], [8.2, 4.0], [8.0, 9.0], [5.8, 13.6], [1.5, 15.8],
                   [-3.0, 16.0], [-7.2, 14.8], [-8.9, 10.8], [-8.6, 5.0]]
        hip = [0.5, 9.5]
        shapes = [{'poly': outline, 'fill': CLOTH, 'stroke': LINE, 'sw': 0.12},
                  {'line': [[-7.6, 2.4], [7.6, 2.4]], 'stroke': '#111316', 'w': 0.5, 'rim': False},   # waistband
                  {'line': [[-0.5, 2.6], [0.2, 6.5], [0.5, 9.5]], 'stroke': PIPING, 'w': 0.55, 'rim': False},
                  {'line': [[-8.4, 11.2], [-5.0, 14.4]], 'stroke': '#33373e', 'w': 0.15, 'rim': False}]
        shapes += vec.brad([0, 0]) + vec.brad(hip)
        sockets = {'A': [0.0, 0.0], 'B': hip, 'hip': hip, 'hip_L': hip, 'hip_R': hip}
    else:
        outline = [[-16, 0], [16, 0], [17.5, 8], [16.5, 17], [10.5, 19.5], [1.5, 15.5],
                   [-1.5, 15.5], [-10.5, 19.5], [-16.5, 17], [-17.5, 8]]
        hl, hr = [-9.0, 10.0], [9.0, 10.0]
        shapes = [{'poly': outline, 'fill': CLOTH, 'stroke': LINE, 'sw': 0.12},
                  {'line': [[-16, 2.4], [16, 2.4]], 'stroke': '#111316', 'w': 0.5, 'rim': False},
                  {'line': [[0, 2.6], [0, 15]], 'stroke': '#33373e', 'w': 0.15, 'rim': False}]
        shapes += vec.brad([0, 0]) + vec.brad(hl) + vec.brad(hr)
        sockets = {'A': [0.0, 0.0], 'B': [0.0, 10.0], 'hip_L': hl, 'hip_R': hr}
    return {'kind': 'pelvis', 'view': view, 'shapes': shapes, 'sockets': sockets, 'socket_source': 'constructed'}


def boot(view='profile', roll=0.0):
    """A chelsea boot. Profile: toe toward +x, ankle (A) 8 cm above the ground, B on the
    ground under it. `roll` (deg) lifts the heel about the ball for toe-off; the forefoot
    stays on the ground, so the ball socket is where a rolling foot stays planted."""
    if view == 'profile':
        g = 8.0                 # ground
        ball = [13.5, g]
        # a real last: 27 cm long, toe box ~5 cm tall, instep rising to the ankle
        upper = [[-4.9, -10.0], [3.9, -10.0], [4.4, -3.0], [5.6, -0.6], [8.6, 1.2], [12.5, 2.4],
                 [16.5, 3.0], [19.6, 3.8], [21.2, 5.0], [21.5, 6.3], [21.0, 7.1], [13.5, 7.2],
                 [-1.0, 7.0], [-6.1, 6.8], [-6.4, 3.0], [-5.9, -2.5]]
        sole = [[-6.3, 6.6], [21.3, 6.7], [21.0, 7.4], [20.0, 7.9], [13.5, g], [-6.3, g]]
        heel = [[-6.4, 6.2], [-1.6, 6.2], [-1.6, g], [-6.4, g]]
        gusset = [[-0.6, -9.6], [2.6, -9.6], [3.1, -0.6], [1.0, 1.6], [-1.8, 0.8]]
        tab = [[-5.2, -12.2], [-3.4, -12.2], [-3.2, -9.4], [-5.2, -9.6]]
        welt = {'line': [[-6.0, 6.6], [21.0, 6.7]], 'stroke': '#5a4636', 'w': 0.18, 'rim': False}
        shine = {'line': [[9.5, 2.6], [14.5, 3.4], [18.8, 4.4]], 'stroke': LEATHER_HI, 'w': 0.45, 'rim': False}
        shapes = [{'poly': tab, 'fill': LEATHER, 'stroke': LINE, 'sw': 0.1, 'rim': False},
                  {'poly': upper, 'fill': LEATHER, 'stroke': LINE, 'sw': 0.12},
                  {'poly': gusset, 'fill': GUSSET, 'stroke': LINE, 'sw': 0.08, 'rim': False},
                  {'poly': heel, 'fill': SOLE, 'stroke': LINE, 'sw': 0.08},
                  {'poly': sole, 'fill': SOLE, 'stroke': LINE, 'sw': 0.08}, welt, shine]
        shapes += vec.brad([0, 0])
        sockets = {'A': [0.0, 0.0], 'B': [0.0, g], 'heel': [-6.3, g], 'ball': ball, 'toe': [20.0, g]}
        if roll:
            # rotate everything about the ball: heel rises, toes stay down
            def R(p):
                return vec.rot(p, roll, ball)
            for s in shapes:
                for k in ('poly', 'line'):
                    if k in s:
                        s[k] = [R(p) for p in s[k]]
                if 'circle' in s:
                    s['circle'] = R(s['circle'])
            sockets = {k: R(v) for k, v in sockets.items()}
            sockets['ball'] = ball
    else:
        shapes = [{'poly': [[-4.2, -9], [4.2, -9], [4.8, 3], [5.6, 6.6], [4.6, 7.6], [-4.6, 7.6], [-5.6, 6.6], [-4.8, 3]],
                   'fill': LEATHER, 'stroke': LINE, 'sw': 0.12},
                  {'poly': [[-5.8, 7.0], [5.8, 7.0], [5.8, 8.0], [-5.8, 8.0]], 'fill': SOLE, 'stroke': LINE, 'sw': 0.08},
                  {'poly': [[-4.6, -8.6], [-2.6, -8.6], [-2.8, 1.0], [-4.4, 1.0]], 'fill': GUSSET, 'rim': False},
                  {'poly': [[2.6, -8.6], [4.6, -8.6], [4.4, 1.0], [2.8, 1.0]], 'fill': GUSSET, 'rim': False}]
        shapes += vec.brad([0, 0])
        sockets = {'A': [0.0, 0.0], 'B': [0.0, 8.0], 'heel': [0.0, 8.0], 'ball': [0.0, 8.0], 'toe': [0.0, 8.0]}
    return {'kind': 'boot', 'view': view, 'state': {'roll': roll}, 'shapes': shapes, 'sockets': sockets,
            'socket_source': 'constructed'}
