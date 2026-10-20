"""ACT-001 Walk without spilling: carry a brim-full cup through a turn, stop, then resume.

Acting choices (authored): the cup hand is carried with its height held in the world, so the arm (not the cup)
takes the walk's bob. The turn is slow on purpose: a cup on a 30 cm radius turned in half a second would spill
(about 1.2 g sideways), so the turn is about 1.7 s with the cup swung round in front of the body. The stop
rocks back over the heels before settling, which is where the weight shows.
"""
import math
import numpy as np
from arena_lib import Scene

TIER = 'complete acted situation'
PERFORMANCE_NOTE = {'standard': 'Cup held at chest height reads; the forearm stays level and the cup does not tilt. The stop settles back over the heels. The turn is slow and careful, which suits a brim-full cup but costs pace. Gait is stiff and the arms barely swing; no secondary action in the free hand.'}


def build(variant='standard'):
    sc = Scene('ACT-001', 330, title='Walk without spilling')
    b = sc.actor('Bola', 260, facing=1, variant=variant, look='bola')
    H, L = b.B.H, b.B.L
    sc.prop('cup', 'cup', (300, 600))
    y_cup = b.c['py'](0) - L['torso'] + L['shoulder_drop'] + L['uarm'] * 0.95
    dx = 0.17
    b.hand(0, 'R', ('carry', dx, y_cup), ha=0.0, shape='open')
    sc.grip(0, 'Bola', 'R', 'cup', snap='base')
    b.face(0, 'neutral').beat(0, 'cup brim-full')
    b.face(8, 'strain')  # concentration
    t = b.walk(14, 1040, step=13, stride=0.27, arms='L', bob=0.010)
    # the stop: weight rocks back over the heels, then forward to rest
    b.key('lean', t, b.c['lean'](t)).key('lean', t + 5, -4.0).key('lean', t + 14, 0.5).key('lean', t + 22, 0.0)
    y0 = b.c['py'](t)
    b.key('py', t, y0).key('py', t + 5, y0 + 0.010 * H).key('py', t + 18, y0)
    b.beat(t + 5, 'weight back over the heels').beat(t + 18, 'stopped, nothing spilt')
    b.face(t + 18, 'neutral')
    # slow turn: the cup is swung round in front of the body on a half circle
    t0 = t + 30
    dur = 40
    b.hand(t0, 'R', ('carry', dx, y_cup))
    t1 = b.turn(t0, dur=dur)
    px0 = b.c['px'](t0)
    for j in range(1, dur):
        u = j / dur
        uu = 0.5 - 0.5 * math.cos(math.pi * u)
        px = b.c['px'](t0 + j)
        b.hand(t0 + j, 'R', ('world', px + dx * H * math.cos(math.pi * uu), y_cup - 0.02 * H * math.sin(math.pi * uu)), mode='lin')
    b.hand(t1, 'R', ('carry', dx, y_cup), mode='lin')
    b.beat(t0 + dur // 2, 'cup swung round in front')
    b.face(t1 + 6, 'strain')
    t2 = b.walk(t1 + 14, 380, step=13, stride=0.27, arms='L', bob=0.010)
    b.key('lean', t2, b.c['lean'](t2)).key('lean', t2 + 5, -4.0).key('lean', t2 + 14, 0.5).key('lean', t2 + 22, 0.0)
    y0 = b.c['py'](t2)
    b.key('py', t2, y0).key('py', t2 + 5, y0 + 0.010 * H).key('py', t2 + 18, y0)
    b.beat(t2 + 18, 'stopped again').face(t2 + 20, 'smile')
    b.beat(sc.N - 1, 'hold')
    return sc
