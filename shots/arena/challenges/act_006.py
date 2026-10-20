"""ACT-006 Overshoot the ledge: run, jump too far, catch an edge, hang and pull up.

The Crash Lab take failed in the mantle: 'the rig cannot place knees directly', so knee, pelvis and feet passed
through the ledge corner and the arms over-stretched. This take uses the arena rig's separate thigh, shin and
foot: the near knee is put on the ledge top with knee_on() while the pelvis travels on a circle of thigh
length round that knee (hip_for), so the knee stays planted as the body comes up over it.

Physics used: the flight is ballistic (g = 9.81 m/s^2 with H px = 1.7 m, 24 fps). The feet push off the floor
until the legs are straight, the jump peaks above the lip and the catch happens on the way down ('too far').
The approach is a fast walk, not a run with a flight phase.
"""
import math
import numpy as np
from arena_lib import Scene

TIER = 'complete acted situation'
PERFORMANCE_NOTE = {'standard': 'Walk-up, crouch, jump, catch and hang read. The pull and the hips-back knee mantle read as a climb from the sheet. Still fails: the near thigh rests across the ledge corner (counted as penetration, not contact), the hands miss their marks while walking forward on the top, the far-knee phase swings the hip forward and back, and two feet touch the ledge on the step-up. Same weak point as the Crash Lab take (the mantle), with fewer and smaller faults.'}


def build(variant='standard'):
    H = 400.0
    sc = Scene('ACT-006', 340, floor=960, title='Overshoot the ledge')
    b = sc.actor('Bola', 160, facing=1, height=H, variant=variant, look='bola')
    L, R = b.B.L, b.B.R
    face, top = 1150.0, 960 - 1.3 * H
    sc.prop('ledge', 'ledge', (face + 0.4 * H, (top + 960) / 2), ref_h=H, w=0.8, h=1.3, fixed=True)
    g = 9.81 * (H / 1.7) / 24 ** 2  # px / frame^2
    leglen = L['thigh'] + L['shin']
    hipoff = 0.01 * H  # the near hip sits this far forward of the pelvis point in profile
    # ---- approach: a fast walk, arms pumping
    t = b.walk(6, 800, step=9, stride=0.32, lift=0.07, bob=0.014, lean=8, swing_amp=0.10, knee=0.95)
    feet = {k: list(v) for k, v in b.feet.items()}
    # ---- plant and crouch, arms swing back
    tp = t - 4
    yc = 960 - b.B.hip_height() + 0.14 * H
    b.pose(tp, py=b.c['py'](tp), lean=b.c['lean'](tp), px=b.c['px'](tp))
    b.pose(tp + 8, py=yc, lean=24, px=b.c['px'](tp) + 0.02 * H)
    for s in 'LR':
        b.pose(tp, **{'a' + s: feet[s], 'p' + s: 0.0}); b.pose(tp + 8, **{'a' + s: feet[s], 'p' + s: 0.0})
    b.hand(tp + 8, 'L', ('rel', -0.12, 0.22), ha=120).hand(tp + 8, 'R', ('rel', -0.14, 0.2), ha=120)
    b.face(tp, 'strain').beat(tp, 'plant').beat(tp + 8, 'crouch, arms back')
    # ---- flight: push off until the legs are straight, then tuck; ballistic to the catch on the way down
    tj = tp + 10
    for s in 'LR':
        b.pose(tj, **{'a' + s: feet[s], 'p' + s: 0.0})
    T = 17
    P0 = np.array([b.c['px'](tj), b.c['py'](tj)])
    arm = (L['uarm'] + L['farm']) * 0.95 + L['palm'] * 0.5
    grip_y = top + 0.012 * H
    Phang = np.array([face - R['torso'] - 0.035 * H, grip_y + arm + L['torso'] - L['shoulder_drop']])
    v = (Phang - P0 - 0.5 * np.array([0, g]) * T * T) / T
    toes = {s: b.foot_points(np.array(feet[s]), 0.0, 1)['toe'] for s in 'LR'}
    off = None
    for j in range(T + 1):
        P = P0 + v * j + 0.5 * np.array([0, g]) * j * j
        b.pose(tj + j, mode='lin', px=float(P[0]), py=float(P[1]), lean=24 - 24 * min(1, j / 6))
        hip = P + np.array([hipoff, 0])
        planted = all(np.linalg.norm(hip - b.ankle_from('toe', toes[s], 0.0, 1)) < 0.985 * leglen for s in 'LR')
        if off is None and planted:
            for s in 'LR':  # push: the heel rises about the toe as the leg straightens
                pitch = 0.0
                for pt in range(0, 50, 2):
                    if np.linalg.norm(hip - b.ankle_from('toe', toes[s], pt, 1)) < 0.985 * leglen:
                        pitch = pt; break
                else:
                    pitch = 48
                b.pose(tj + j, mode='lin', **{'a' + s: list(b.ankle_from('toe', toes[s], pitch, 1)), 'p' + s: float(pitch)})
            continue
        if off is None:
            off = j
            b.beat(tj + j, 'feet leave the floor')
        k = min(1.0, (j - off) / 5.0)
        kd = max(0.0, (j - (T - 5)) / 5.0)  # the legs reach down again before the catch
        tuck = np.array([[-0.07 * H, 0.40 * H], [0.03 * H, 0.37 * H]])
        reach = np.array([[-0.07 * H, 0.47 * H], [-0.04 * H, 0.47 * H]])
        for i, s in enumerate('LR'):
            A_last = np.array(b.c['a' + s](tj + off - 1))
            dv = A_last - hip
            A0 = hip + dv / np.linalg.norm(dv) * min(np.linalg.norm(dv), 0.97 * leglen)
            A_t = P + tuck[i] + (reach[i] - tuck[i]) * (kd * kd * (3 - 2 * kd))
            A = A0 + (A_t - A0) * (k * k * (3 - 2 * k))
            b.pose(tj + j, mode='lin', **{'a' + s: list(A), 'p' + s: 30.0 * k})
    b.beat(tj, 'take-off').beat(tj + 9, 'over the top of the arc')
    b.hand(tj + 5, 'L', ('rel', 0.10, -0.25), ha=-70, elbow=-1).hand(tj + 5, 'R', ('rel', 0.12, -0.27), ha=-70, elbow=-1)
    tc = tj + T
    lip = ('prop', 'ledge', 'lipL')
    b.hand(tc, 'L', lip + ([-0.004, 0.012],), ha=-60, shape='grip', elbow=-1).hand(tc, 'R', lip + ([0.0, 0.012],), ha=-60, shape='grip', elbow=-1)
    b.beat(tc, 'hands on the edge')
    # ---- hang: legs reach down, the body swings in once and settles below the grip
    hx, hy = Phang
    for j, dx in enumerate([0.0, 0.025, 0.008, -0.004, 0.0]):
        b.pose(tc + 4 * j + 1, px=hx + dx * H, py=hy, lean=-4.0 * (j == 1))
    th = tc + 22
    hang_feet = {'L': [hx - 0.07 * H, hy + 0.47 * H], 'R': [hx - 0.04 * H, hy + 0.47 * H]}
    b.pose(tc, aL=hang_feet['L'], aR=hang_feet['R'], pL=30.0, pR=25.0)
    b.pose(th, aL=hang_feet['L'], aR=hang_feet['R'], pL=30.0, pR=25.0)
    b.face(tc + 2, 'pain').face(th, 'strain').beat(th, 'hangs below the grip')
    # ---- pull: chest up to the edge; the torso stays outside the wall
    t1 = th + 40
    b.pose(t1 - 6, px=hx, py=hy, lean=0.0)
    for s in 'LR':
        b.pose(t1 - 6, **{'a' + s: hang_feet[s]})
    P1 = [face - R['torso'] - 0.025 * H, top + L['torso'] - 0.06 * H]
    b.pose(t1 + 14, px=P1[0], py=P1[1], lean=0.0)
    b.pose(t1 + 14, aL=[P1[0] - 0.07 * H, P1[1] + 0.482 * H], aR=[P1[0] - 0.04 * H, P1[1] + 0.482 * H])
    b.hand(t1 + 14, 'L', lip + ([-0.004, 0.012],), ha=-30, elbow=-1).hand(t1 + 14, 'R', lip + ([0.0, 0.012],), ha=-30, elbow=-1)
    b.beat(t1 + 14, 'pulls: chest to the edge')
    # ---- knee mantle with the hips back. The knee is the target: it slides up the wall face to the corner while
    # the hips go back (arms straighten toward the lip), rolls over the corner onto the top, and the body then
    # rotates forward over it. The hip is always a thigh's length from the knee, so the IK puts the knee exactly
    # where it is asked to be: this is what a fused thigh-shin piece cannot do.
    rth, rsh = R['thigh'], R['shin']
    arm_max = L['uarm'] + L['farm']
    lipxy = np.array([face, grip_y])

    def body_for(knee, alpha, sa):
        hip = np.array(b.hip_for(knee, alpha))
        P = hip - np.array([hipoff, 0])
        best = None
        for lean in range(-10, 75):  # lean so the near wrist can reach the lip with a little slack
            u = np.array([math.sin(math.radians(lean)), -math.cos(math.radians(lean))])
            sh = P + u * L['torso'] - u * L['shoulder_drop'] + np.array([0.012 * H, 0])
            d = np.linalg.norm(lipxy - np.array([L['palm'] * 0.5, 0]) - sh) / arm_max
            sc_ = abs(d - 0.93) + 0.002 * abs(lean - 20)
            if best is None or sc_ < best[0]:
                best = (sc_, lean)
        return [float(P[0]), float(P[1])], float(best[1]), b.knee_on(knee, sa)

    tk0 = t1 + 20
    path = []  # (frame offset, knee, alpha, shin angle)
    k_lo = [face - rth - 0.012 * H, top + 0.30 * H]
    k_corner = [face - rth * 0.2, top - rth - 0.02 * H]
    knee = [face + 0.10 * H, top - rsh - 0.6]
    n1, n2 = 26, 16
    for j in range(n1 + 1):  # up the face
        u = 0.5 - 0.5 * math.cos(math.pi * j / n1)
        kk = [k_lo[0], k_lo[1] + (top - rth - 0.03 * H - k_lo[1]) * u]
        path.append((j, kk, 20 + 58 * u, -90 + 40 * u))
    for j in range(1, n2 + 1):  # over the corner onto the top, on an arc that stays above it
        u = 0.5 - 0.5 * math.cos(math.pi * j / n2)
        x = k_lo[0] + (knee[0] - k_lo[0]) * u
        y = (top - rth - 0.03 * H) + (knee[1] - (top - rth - 0.03 * H)) * u - 0.05 * H * math.sin(math.pi * u)
        path.append((n1 + j, [x, y], 78 - 14 * u, -50 + 54 * u))
    for j, kk, al, sa in path:
        P, lean, aR = body_for(kk, al, sa)
        b.pose(tk0 + j, mode='lin', px=P[0], py=P[1], lean=lean, aR=aR, pR=80.0 if j <= n1 else 70.0)
        b.pose(tk0 + j, mode='lin', aL=[P[0] - 0.05 * H, P[1] + 0.47 * H], pL=40.0)
    t3 = tk0 + n1 + n2
    b.beat(tk0, 'right knee comes up the wall, hips back').beat(tk0 + n1, 'knee at the corner')
    b.beat(t3, 'right knee onto the top')
    # ---- the far knee follows: up the face, over the corner, onto the same point as the near knee.
    # Two planted knees at different points would pin the hip, so the far knee ends where the near one is
    # (side by side in depth). Meanwhile the hip is a thigh's length from both knees (circle intersection).
    last_hip = [None]
    def hip_from_two(kR, kL):
        cR = np.array(kR, float) - np.array([hipoff, 0]); cL = np.array(kL, float) + np.array([hipoff, 0])
        d = np.linalg.norm(cR - cL)
        th_ = L['thigh'] * 0.9999
        if d < 1e-6:
            return None
        a_ = d / 2; hh = math.sqrt(max(0.0, th_ * th_ - a_ * a_))
        m = (cR + cL) / 2; n = np.array([-(cR - cL)[1], (cR - cL)[0]]) / d
        c1, c2 = m + n * hh, m - n * hh
        rad = R['torso'] * 0.5
        outside = [c for c in (c1, c2) if not (c[0] > face - rad and c[1] > top - rad)]
        if not outside:
            return min((c1, c2), key=lambda c: c[0])  # the hip behind the knees
        prev = last_hip[0]
        if prev is None:
            return min(outside, key=lambda c: c[1])  # above the knees, never inside the ledge
        return min(outside, key=lambda c: np.linalg.norm(c - prev))  # continuity: no flip between the two solutions
    def lean_for(P, hand):
        best = None
        for lean in range(-10, 100):
            u = np.array([math.sin(math.radians(lean)), -math.cos(math.radians(lean))])
            sh = P + u * (L['torso'] - L['shoulder_drop']) + np.array([0.012 * H, 0])
            d = np.linalg.norm(np.asarray(hand) - sh) / arm_max
            sc_ = abs(d - 0.9) + 0.003 * abs(lean - 25)
            if best is None or sc_ < best[0]:
                best = (sc_, lean)
        return float(best[1])
    b.hand(t3, 'L', lip + ([-0.004, 0.012],), ha=-30).hand(t3, 'R', lip + ([0.0, 0.012],), ha=-30)
    on_top = {'L': ('prop', 'ledge', 'lipL', [0.07, -(R['hand'] + 1) / H - 0.012]), 'R': ('prop', 'ledge', 'lipL', [0.09, -(R['hand'] + 1) / H - 0.012])}
    b.hand(t3 + 6, 'L', on_top['L'], ha=0.0, shape='open', elbow=1).hand(t3 + 6, 'R', on_top['R'], ha=0.0, shape='open', elbow=1)
    hands_top = np.array([face + 0.08 * H, top])
    # as the far knee arrives the hands walk forward on the top, one then the other, so the shoulders stay over them
    on_top2 = {'L': ('prop', 'ledge', 'lipL', [0.30, -(R['hand'] + 1) / H - 0.012]), 'R': ('prop', 'ledge', 'lipL', [0.33, -(R['hand'] + 1) / H - 0.012])}
    hands_top2 = np.array([face + 0.31 * H, top])
    kL0 = np.array(b.c['aL'](t3))  # start the far knee from where the hanging leg's knee is
    kL_lo = [face - rth - 0.012 * H, top + 0.22 * H]
    m1, m2 = 18, 16
    kpath = []
    for j in range(m1 + 1):
        u = 0.5 - 0.5 * math.cos(math.pi * j / m1)
        kpath.append(([kL_lo[0], kL_lo[1] + (top - rth - 0.03 * H - kL_lo[1]) * u], -90 + 40 * u))
    for j in range(1, m2 + 1):
        u = 0.5 - 0.5 * math.cos(math.pi * j / m2)
        x = kL_lo[0] + (knee[0] - kL_lo[0]) * u
        y = (top - rth - 0.03 * H) + (knee[1] - (top - rth - 0.03 * H)) * u - 0.05 * H * math.sin(math.pi * u)
        kpath.append(([x, y], -50 + 56 * u))
    tb = t3 + 2
    last_hip[0] = np.array([b.c['px'](t3), b.c['py'](t3)])
    for j, (kL, saL) in enumerate(kpath):
        hip = hip_from_two(knee, kL)
        if hip is None:
            hip = np.array(b.hip_for(knee, 40)) - np.array([hipoff, 0])
        last_hip[0] = np.asarray(hip)
        P = hip
        w = max(0.0, (j - m1 + 4) / (m2 + 4))
        b.pose(tb + j, mode='lin', px=float(P[0]), py=float(P[1]), lean=lean_for(P, hands_top + (hands_top2 - hands_top) * w), aR=b.knee_on(knee, 4), pR=70.0,
               aL=b.knee_on(kL, saL), pL=80.0 if j < m1 else 70.0)
    t4 = tb + m1 + m2
    b.hand(tb + m1 - 4, 'L', on_top['L'], ha=0.0).hand(tb + m1 + 4, 'R', on_top['R'], ha=0.0)
    b.hand(tb + m1 + 6, 'L', on_top2['L'], ha=0.0).hand(t4, 'R', on_top2['R'], ha=0.0)
    b.beat(tb, 'left knee comes up the wall').beat(t4, 'kneeling on the top')
    # ---- kneel up over both knees (they share a point), then the near foot steps forward
    hip_now = np.array([b.c['px'](t4), b.c['py'](t4)]) + np.array([hipoff, 0])
    v0 = hip_now - np.array(knee)
    a0 = math.degrees(math.atan2(-v0[0], -v0[1]))
    t5 = t4 + 18
    for j in range(1, 19):
        a = a0 + (8 - a0) * (0.5 - 0.5 * math.cos(math.pi * j / 18))
        hip = np.array(b.hip_for(knee, a))
        P = hip - np.array([hipoff, 0])
        b.pose(t4 + j, mode='lin', px=float(P[0]), py=float(P[1]), lean=lean_for(P, hands_top2) * (1 - j / 18) + 10 * j / 18,
               aR=b.knee_on(knee, 4), pR=70.0, aL=b.knee_on(knee, 6), pL=70.0)
    b.hand(t5 - 10, 'L', on_top2['L'], ha=0.0).hand(t5 - 6, 'R', on_top2['R'], ha=0.0)  # hands stay on the top until the hips are over the knees
    b.hand(t5 - 4, 'L', ('rest',), ha=80.0, shape='relaxed').hand(t5, 'R', ('rest',), ha=80.0, shape='relaxed')
    b.beat(t5, 'kneeling up, hands off')
    # half-kneel: the near foot forward and down, the hip rides forward on the far knee
    t6 = t5 + 18
    ftR = [knee[0] + 0.22 * H, top - L['ankle']]
    b.pose(t5 + 8, aR=[knee[0] + 0.12 * H, top - 0.10 * H], pR=0.0)
    b.pose(t6, aR=ftR, pR=0.0)
    for j in range(1, 19):
        a = 8 + (-12 - 8) * (0.5 - 0.5 * math.cos(math.pi * j / 18))
        hip = np.array(b.hip_for(knee, a))
        b.pose(t5 + j, mode='lin', px=float(hip[0] + hipoff), py=float(hip[1]), lean=10.0, aL=b.knee_on(knee, 6), pL=70.0)
    b.beat(t6, 'right foot planted in front')
    # ---- stand up over the front foot; the back foot comes through
    t7 = t6 + 26
    ftL = [ftR[0] + 0.06 * H, top - L['ankle']]
    b.pose(t6 + 12, px=ftR[0] - 0.02 * H, py=top - b.B.hip_height() + 0.08 * H, lean=18, aL=[knee[0] + 0.02 * H, top - 0.10 * H], pL=20.0)
    b.pose(t7 - 4, aL=ftL, pL=0.0)
    b.pose(t7, px=(ftR[0] + ftL[0]) / 2, py=top - b.B.hip_height(), lean=0.0)
    t6 = t7
    b.face(t6, 'neutral').beat(t6, 'standing on top')
    b.face(t6 + 20, 'smile').beat(sc.N - 1, 'hold')
    return sc
