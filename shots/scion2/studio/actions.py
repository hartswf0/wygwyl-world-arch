"""Actor-independent action clips (lists of frames, see core.py for the frame format).

Every clip is authored once, facing right, in absolute screen angles. Nothing here knows which
actor will play it; props and other actors enter only as world targets (ik) and events.
"""
import math

FPS = 24

STAND = {
    'front': {'chest': -90, 'uarmR': 100, 'farmR': 96, 'uarmL': 80, 'farmL': 84,
              'thighR': 93, 'shinR': 92, 'thighL': 87, 'shinL': 88},
    'q3r': {'chest': -87, 'uarmR': 96, 'farmR': 84, 'uarmL': 92, 'farmL': 82,
            'thighR': 92, 'shinR': 92, 'thighL': 88, 'shinL': 89},
}


def ease(u):
    u = min(1., max(0., u))
    return u * u * (3 - 2 * u)


def frame(view, bones, anchor='ground', rel=None, body=0., contact=None, **kw):
    f = {'view': view, 'bones': dict(bones), 'anchor': anchor, 'rel': dict(rel or {}), 'body': body,
         'contact': dict(contact or {})}
    f.update(kw)
    return f


def stand(view='front', n=12, anchor='footR'):
    out = []
    for i in range(n):
        b = dict(STAND[view])
        b['chest'] += 0.8 * math.sin(2 * math.pi * i / 48)        # breathing
        out.append(frame(view, b, anchor, contact={'footR': True, 'footL': True}))
    return out


STEP = 0.42          # step length in leg lengths
SWING = 0.4          # share of a cycle each foot spends in the air (the rest is stance)


def foot_track(t, land_phase):
    """(u, lift, planted) of one foot at time t (in cycles). The foot lands at land_phase of each
    cycle, a little ahead of the pelvis, and swings for SWING of a cycle before that."""
    plant = lambda n: 2 * STEP * (n + land_phase) + 0.45 * STEP
    n = math.floor(t - land_phase)               # the last landing was in cycle n
    t_land = n + land_phase
    since = t - t_land
    if since < 1 - SWING:                        # stance
        return plant(n), 0., True
    u = (since - (1 - SWING)) / SWING            # swing toward the next landing
    return plant(n) + (plant(n + 1) - plant(n)) * ease(u), 0.11 * math.sin(math.pi * u), False


def walk(cycles=2, T=24, view='q3r'):
    """a straight walk. The pelvis travels at a steady rate and the feet are placed by IK, all in
    units of the actor's own leg length, so a taller actor takes longer strides with the same timing,
    and a planted foot never slides. Upper body by angles."""
    out = []
    for i in range(int(cycles * T)):
        t = i / T
        p = 2 * math.pi * t
        s = math.sin(p)
        uR, hR, pR = foot_track(t, 0.4)
        uL, hL, pL = foot_track(t, 0.9)
        b = dict(STAND[view])
        b['chest'] = -86 + 1.2 * math.sin(2 * p)
        b['uarmR'] = 92 - 20 * math.sin(2 * math.pi * (t - 0.15)); b['farmR'] = b['uarmR'] - 14
        b['uarmL'] = 92 + 20 * math.sin(2 * math.pi * (t - 0.15)); b['farmL'] = b['uarmL'] - 14
        rel = {'head': 1.5 * math.sin(2 * p), 'footR': -10 * hR / 0.11, 'footL': -10 * hL / 0.11}
        f = frame(view, b, 'gait', rel, contact={'footR': pR, 'footL': pL})
        f['gait'] = {'root': [2 * STEP * t, 0.012 * (1 + math.cos(4 * math.pi * (t - 0.4)))],
                     'feet': {'R': [uR, hR], 'L': [uL, hL]}}
        out.append(f)
    return out


def turn(n_front=12, n_after=16):
    """front -> 3/4 right. A turn in painted art is a drawing swap on a held frame, with a small
    anticipation dip before it and a settle after. The stance centre (midpoint of the ankles) stays
    put; on the swap frame the feet are re-set (a small step), so they count as lifted there."""
    out = [dict(f, anchor='feet') for f in stand('front', n_front - 3)]
    for i in range(3):              # anticipation: the chest dips, the head leads
        b = dict(STAND['front']); d = 4 * math.sin(math.pi * (i + 1) / 4)
        b['chest'] += d
        out.append(frame('front', b, 'feet', {'head': -2 * d}, contact={'footR': True, 'footL': True}, event='turn_prep'))
    for i in range(n_after):
        b = dict(STAND['q3r']); k = math.exp(-i / 3.) * math.cos(i / 1.6)
        b['chest'] += 3 * k
        out.append(frame('q3r', b, 'feet', {'head': 2 * k}, contact={'footR': i > 0, 'footL': i > 0},
                         event='swap' if i == 0 else 'settle'))
    return out


def grasp_release(grasp_pt, lift_pt, place_pt, S='L'):
    """reach to the prop, take it, lift it, set it down at place_pt, let go, return.
    The hand targets are world points (scene data); the arm angles are solved per actor."""
    out = stand('q3r', 6)
    seq = [('reach', 14, 'rest', grasp_pt, None), ('take', 5, grasp_pt, grasp_pt, 'take'),
           ('lift', 14, grasp_pt, lift_pt, 'hold'), ('hold', 6, lift_pt, lift_pt, 'hold'),
           ('place', 14, lift_pt, place_pt, 'hold'), ('release', 5, place_pt, place_pt, 'release'),
           ('return', 14, place_pt, 'rest', None)]
    for name, n, a, b_, held in seq:
        for i in range(n):
            u = ease((i + 1) / n)
            b = dict(STAND['q3r']); b['chest'] += -3 * (name in ('reach', 'take', 'place', 'release'))
            f = frame('q3r', b, 'footR', {},
                      contact={'footR': True, 'footL': True, 'hand' + S: 'prop' if held in ('take', 'hold') else None},
                      event=name)
            f['ik'] = {S: {'from': a, 'to': b_, 'u': u}}
            out.append(f)
    out += stand('q3r', 6)
    return out


def blend_in(clip, n=5):
    """the first n frames of clip ease in from whatever pose the actor held before (mixing)"""
    out = [dict(f) for f in clip]
    for i in range(min(n, len(out))):
        out[i]['blend'] = {'u': ease((i + 1) / (n + 1)), 'start': i == 0}
    return out


def mirror_sides(clip):
    """swap R and L in a clip (the same action led by the other foot or hand)"""
    sw = lambda k: k[:-1] + ('L' if k[-1] == 'R' else 'R') if k[-1:] in ('R', 'L') else k
    out = []
    for f in clip:
        g = dict(f)
        g['bones'] = {sw(k): v for k, v in f['bones'].items()}
        g['rel'] = {sw(k): v for k, v in f.get('rel', {}).items()}
        g['contact'] = {sw(k): v for k, v in f.get('contact', {}).items()}
        if f.get('anchor', '').startswith('foot'):
            g['anchor'] = sw(f['anchor'])
        out.append(g)
    return out


def fall_recover(view='q3r', n_fall=12, n_down=10, n_up=22):
    """knocked backward: rotate about the planted feet, land on the back, lie, roll up to sitting,
    stand. The ground holds the body: while down, the lowest painted pixel sits on the floor."""
    out = []
    for i in range(n_fall):
        u = ((i + 1) / n_fall) ** 2                       # accelerating fall
        b = dict(STAND[view]); b['uarmR'] -= 50 * u; b['uarmL'] -= 60 * u; b['farmR'] -= 40 * u; b['farmL'] -= 40 * u
        b['shinR'] += 10 * u; b['shinL'] += 10 * u
        planted = u < 0.85
        rel = {'footR': 82 * u, 'footL': 82 * u} if planted else {}
        out.append(frame(view, b, 'footR' if planted else 'ground', rel, body=-82 * u, event='fall',
                         contact={'footR': planted}))
    for i in range(n_down):
        b = dict(STAND[view]); b['uarmR'] -= 50; b['uarmL'] -= 60; b['farmR'] -= 40; b['farmL'] -= 40
        b['shinR'] += 10 + 3 * math.exp(-i / 2) * math.cos(i); b['shinL'] += 10
        out.append(frame(view, b, 'ground', body=-82 + 3 * math.exp(-i / 2.) * math.sin(i), event='down'))
    for i in range(n_up):
        u = ease((i + 1) / n_up)
        k = math.sin(math.pi * u)                         # knees fold through the middle of the rise
        b = dict(STAND[view])
        b['thighR'] -= 70 * k; b['thighL'] -= 60 * k; b['shinR'] += 40 * k; b['shinL'] += 50 * k
        b['uarmR'] -= 30 * k; b['uarmL'] -= 30 * k
        planted = u >= 0.75
        rel = {'footR': 82 * (1 - u), 'footL': 82 * (1 - u)} if planted else {}
        out.append(frame(view, b, 'ground' if not planted else 'footR', rel, body=-82 * (1 - u), event='recover',
                         contact={'footR': planted}))
    out += stand(view, 8)
    return out
