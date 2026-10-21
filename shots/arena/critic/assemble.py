"""Assemble the man the way a cut-out puppet is built: brad on brad.

The compiler places every card on the skeleton independently: limbs are
stretched from joint to joint, the torso and head hang from hand-typed pivots,
the pelvis never rotates. Nothing makes a card meet its neighbour, and nothing
makes a boot meet the floor.

This assembler keeps the skeleton's ANGLES and throws away its lengths:

  * each card keeps one uniform scale for the whole clip (cards are rigid; no
    per-frame stretch, so the art is never smeared);
  * each child's drawn brad is put exactly on its parent's drawn brad, read
    from the card by brads.py (a guessed socket is flagged, not hidden);
  * the chain hangs from the pelvis; on grounded frames the whole figure is
    dropped so the lowest sole touches the floor.

    from assemble import assemble
    new_cards = assemble(clip, f, cards)     # same roles/ids, new matrices
"""
import math
import numpy as np

import brads
from frame import kind_of, apply, M_of, skeleton, px_per_cm

# Model-sheet lengths, cm, along each card's axis (proximal brad -> distal brad).
LEN_CM = {'uarm': 28.0, 'farm': 26.0, 'thigh': 44.0, 'shin': 43.0,
          'torso': 50.0,   # hip brad -> top of the collar
          'head': 30.0,    # neck brad -> crown
          'pelvis': 14.0,  # waist -> hem brads
          'hand': 17.0,    # wrist -> fingertip
          'boot': 14.0}    # ankle brad -> sole


def _axis(kind, r, size):
    s = r['sockets']
    w, h = size
    if kind in ('uarm', 'farm', 'thigh', 'shin'):
        return np.array(s['A']), np.array(s['B'])
    if kind == 'torso':
        return np.array(s['hip']), np.array(s['neck'])
    if kind == 'head':
        return np.array(s['neck']), np.array(s['crown'])
    if kind == 'pelvis':
        return np.array(s['waist']), (np.array(s['hip_L']) + np.array(s['hip_R'])) / 2
    if kind == 'hand':
        return np.array(s['wrist']), np.array([w * 0.95, s['wrist'][1]])
    if kind == 'boot':
        return np.array(s['ankle']), np.array(s['sole'])
    raise KeyError(kind)


def _place(card, kind, target, direction, px_cm, flip, socket_from=None):
    """Matrix putting the card's proximal socket on `target`, its axis along `direction`."""
    r = brads.read(card['path'], kind)
    a, b = _axis(kind, r, r['size'])
    if socket_from is not None:
        a = np.array(r['sockets'][socket_from])
    u = b - _axis(kind, r, r['size'])[0]
    span = np.linalg.norm(u)
    if kind == 'hand':
        # A hand card's wrist may be guessed and some are cropped (the fist is half a
        # hand), so wrist->edge is not its length. Its longest drawn extent is.
        # Critic turn 3: scaling by wrist->edge made the fists the size of a head.
        span = _ink_extent(card['path'])
    k = LEN_CM[kind] * px_cm / max(span, 1e-6)
    F = np.diag([-1.0, 1.0]) if flip else np.eye(2)
    fu = F @ u
    th = math.atan2(direction[1], direction[0]) - math.atan2(fu[1], fu[0])
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    M = k * R @ F
    t = np.asarray(target, float) - M @ a
    return [float(M[0, 0]), float(M[1, 0]), float(M[0, 1]), float(M[1, 1]), float(t[0]), float(t[1])], r


def _ink_extent(path):
    A = brads.brads(path)[1]
    ys, xs = np.nonzero(A)
    return float(max(np.ptp(xs), np.ptp(ys)))


def _dir(p, q):
    v = np.asarray(q, float) - np.asarray(p, float)
    return v / max(np.linalg.norm(v), 1e-6)


def _socket(card, name):
    r = brads.read(card['path'], kind_of(card['role']))
    return apply(card['m'], r['sockets'][name])


def assemble(clip, f, cards, grounded=None):
    px_cm = px_per_cm(clip)
    J = skeleton(cards)
    by = {c['role']: dict(c) for c in cards}
    flip = np.linalg.det(M_of(by['torso']['m'])[0]) < 0
    if 'pelvis' not in J or 'neck' not in J:
        return cards
    spine = _dir(J['pelvis'], J['neck'])

    def put(role, target, direction, socket_from=None):
        c = by[role]
        c['m'], _ = _place(c, kind_of(role), target, direction, px_cm, flip, socket_from)
        return c

    # Head direction: keep the compiler's head tilt (its card's up vector).
    hm, _ = M_of(by['head']['m'])
    head_up = _dir([0, 0], hm @ np.array([0.0, -1.0]))

    put('pelvis', J['pelvis'], -spine)
    put('torso', _socket(by['pelvis'], 'waist'), spine)
    put('head', _socket(by['torso'], 'neck'), head_up)
    hips = (_socket(by['pelvis'], 'hip_L') + _socket(by['pelvis'], 'hip_R')) / 2
    for side in ('far', 'near'):
        put(f'thigh.{side}', hips, _dir(J[f'hip.{side}'], J[f'knee.{side}']))
        put(f'shin.{side}', _socket(by[f'thigh.{side}'], 'B'), _dir(J[f'knee.{side}'], J[f'ankle.{side}']))
        # Keep the compiler's boot rotation (its feet were flat on the floor; a
        # direction derived here stood him on his toes in every frame, critic turn 1),
        # rescale it to the model sheet, and pin the drawn ankle brad to the shin.
        boot = by[f'boot.{side}']
        bm, _ = M_of(boot['m'])
        r = brads.read(boot['path'], 'boot')
        a, b = _axis('boot', r, r['size'])
        k = LEN_CM['boot'] * px_cm / max(np.linalg.norm(b - a), 1e-6)
        M = bm / math.sqrt(abs(np.linalg.det(bm))) * k
        t = _socket(by[f'shin.{side}'], 'B') - M @ a
        boot['m'] = [float(M[0, 0]), float(M[1, 0]), float(M[0, 1]), float(M[1, 1]), float(t[0]), float(t[1])]
        put(f'uarm.{side}', _socket(by['torso'], 'shoulder'), _dir(J[f'shoulder.{side}'], J[f'elbow.{side}']))
        put(f'farm.{side}', _socket(by[f'uarm.{side}'], 'B'), _dir(J[f'elbow.{side}'], J[f'wrist.{side}']))
        fd = _dir(J[f'elbow.{side}'], J[f'wrist.{side}'])
        put(f'hand.{side}', _socket(by[f'farm.{side}'], 'B'), fd)

    floor = next((o['y'] for o in clip['frames'][f]['draw'] if o['t'] == 'floor'), None)
    if grounded is None:
        grounded = bool(clip['frames'][f].get('dbg', {}).get('sup'))
    if floor is not None and grounded:
        soles = [_socket(by[f'boot.{s}'], 'sole')[1] for s in ('near', 'far')]
        dy = floor - max(soles)
        for c in by.values():
            c['m'][5] += dy
    return [by[c['role']] for c in cards]
