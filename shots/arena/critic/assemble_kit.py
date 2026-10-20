"""Assemble the man from the part library (shots/arena/parts): code-drawn pelvis,
limbs, boots and hands; registered image head and torso.

Same skeleton angles as the clip, same chain as assemble.py (child socket on parent
socket, rigid parts, sole on the floor), but every socket comes from a part
contract: constructed for code parts, registered by eye for image parts. Nothing
is read off pixels and nothing is guessed.

Hands are chosen per frame from what the Bolas bank asks for: shape, grip and palm
facing, on the true side (L/R), never mirrored from the other hand.
"""
import math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'parts'))
import library as LIBR
from frame import kind_of, apply, M_of, skeleton, px_per_cm

PARTS = None

# cm along each IMAGE part's A->far socket, so a registered card is printed at body size
IMAGE_CM = {'torso': ('hip', 'neck', 50.0), 'head': ('neck', 'crown', 27.0)}


def lib():
    global PARTS
    if PARTS is None:
        PARTS = LIBR.load()
    return PARTS


def _scale(part, px_cm):
    if part['source'] == 'code':
        return px_cm / part['ppc']
    a, b, cm = IMAGE_CM[part['kind']]
    s = part['sockets']
    return cm * px_cm / math.dist(s[a], s[b])


def _mat(part, sock, target, direction, axis, px_cm, flip):
    """Uniform-scale matrix: part socket `sock` on `target`, the part's `axis` (two sockets) along `direction`."""
    s = part['sockets']
    a, b = np.array(s[axis[0]], float), np.array(s[axis[1]], float)
    u = b - a
    k = _scale(part, px_cm)
    F = np.diag([-1.0, 1.0]) if flip else np.eye(2)
    fu = F @ u
    th = math.atan2(direction[1], direction[0]) - math.atan2(fu[1], fu[0])
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    M = k * R @ F
    t = np.asarray(target, float) - M @ np.array(s[sock], float)
    return [float(M[0, 0]), float(M[1, 0]), float(M[0, 1]), float(M[1, 1]), float(t[0]), float(t[1])]


def face_to_expression(fc, effort):
    """Crash Lab FACE0 fields -> one of the cut expression heads (heads_intent_effort)."""
    m, brow, lid, smile = fc.get('mouth'), fc.get('brow', 0), fc.get('lid', 0), fc.get('smile', 0)
    if fc.get('eyes') == 'closed':
        return 'tired'
    if m == 'teeth':
        return 'strain' if brow < -0.3 or effort > 0.5 else 'forced_grin'
    if m in ('O', 'open'):
        return 'surprised' if brow >= -0.1 else 'panting'
    if m == 'wavy':
        return 'afraid'
    if brow < -0.4:
        return 'reluctant'
    if lid > 0.4:
        return 'tired'
    if smile > 0.45:
        return 'recognition'
    if smile < -0.25:
        return 'sad'
    return 'listening'


def _dir(p, q):
    v = np.asarray(q, float) - np.asarray(p, float)
    return v / max(np.linalg.norm(v), 1e-6)


def _card(part, role, actor, m):
    return {'t': 'img', 'id': part['id'], 'role': role, 'actor': actor, 'm': m,
            'path': os.path.join(SHOTS, part['file']), 'part': part}


def _at(card, sock):
    return apply(card['m'], card['part']['sockets'][sock])


def assemble(clip, f, cards, bank=None, actor=0, prefer=None):
    """prefer: {kind: source} e.g. {'torso': 'traced'} to swap a part family by source."""
    prefer = prefer or {}
    """-> (cards, notes). notes lists every request the library could not meet."""
    P = lib()
    px_cm = px_per_cm(clip)
    J = skeleton(cards)
    by = {c['role']: c for c in cards}
    flip = np.linalg.det(M_of(by['torso']['m'])[0]) < 0
    spine = _dir(J['pelvis'], J['neck'])
    notes = []
    torso_view = 'front' if 'front' in by['torso']['id'] else 'profile'
    head_view = by['head']['id'].split('.')[-1]

    def get(kind, **want):
        if kind in prefer:
            want = dict(want, source=prefer[kind])
        p, miss = LIBR.pick(P, kind, **want)
        if miss:
            notes.append(f'{kind}: no part for {", ".join(f"{k}={want[k]}" for k in miss)}; used {p["id"] if p else None}')
        return p

    out = {}
    pel = get('pelvis', view=torso_view)
    out['pelvis'] = _card(pel, 'pelvis', actor, _mat(pel, 'A', J['pelvis'] + spine * 0, -spine, ('A', 'B'), px_cm, flip))
    tor = get('torso', view=torso_view)
    out['torso'] = _card(tor, 'torso', actor, _mat(tor, 'hip', _at(out['pelvis'], 'A') + spine * 2 * px_cm, spine, ('hip', 'neck'), px_cm, flip))
    fc = bank.face(f, actor) if bank else None
    if fc and head_view != 'back':
        # an expression head chosen by what Bolas's face is doing; these are 3/4, one
        # step from profile, and have no sunglasses so the eyes can act
        expr = face_to_expression(fc, bank.effort(f, actor))
        hd = get('head', view='threequarter_R', expression=expr)
    else:
        hd = get('head', view=head_view)
    hm, _ = M_of(by['head']['m'])
    head_up = _dir([0, 0], hm @ np.array([0.0, -1.0]))
    out['head'] = _card(hd, 'head', actor, _mat(hd, 'neck', _at(out['torso'], 'neck'), head_up, ('neck', 'crown'), px_cm, flip))

    near = bank.near_side(f, actor) if bank else 'R'
    sides = {'near': near, 'far': 'L' if near == 'R' else 'R'}
    hands = bank.hands(f, actor) if bank else {s: {'shape': 'relaxed', 'grip': .25, 'palm': 'in'} for s in 'LR'}
    for side in ('far', 'near'):
        hip_sock = 'hip' if torso_view == 'profile' else ('hip_L' if sides[side] == 'L' else 'hip_R')
        th = get('thigh')
        out[f'thigh.{side}'] = _card(th, f'thigh.{side}', actor, _mat(th, 'A', _at(out['pelvis'], hip_sock), _dir(J[f'hip.{side}'], J[f'knee.{side}']), ('A', 'B'), px_cm, flip))
        sh = get('shin')
        out[f'shin.{side}'] = _card(sh, f'shin.{side}', actor, _mat(sh, 'A', _at(out[f'thigh.{side}'], 'B'), _dir(J[f'knee.{side}'], J[f'ankle.{side}']), ('A', 'B'), px_cm, flip))
        bt = get('boot', view='profile' if torso_view == 'profile' else 'front', roll=0)
        # Foot angle from the bank's own heel and toe (critic, kit turn 1: the compiler's
        # boot rotation pointed planted feet toes-down). Fallback: the compiler's.
        bm, _ = M_of(by[f'boot.{side}']['m'])
        M = bm / math.sqrt(abs(np.linalg.det(bm))) * _scale(bt, px_cm)
        if bank is not None:
            heel, toe = bank.foot(f, actor, sides[side])
            d = _dir(heel, toe)
            if flip:
                d = np.array([-d[0], d[1]])
            th = math.atan2(d[1], d[0])
            R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
            M = _scale(bt, px_cm) * R @ (np.diag([-1.0, 1.0]) if flip else np.eye(2))
        t = _at(out[f'shin.{side}'], 'B') - M @ np.array(bt['sockets']['A'])
        out[f'boot.{side}'] = _card(bt, f'boot.{side}', actor, [float(M[0, 0]), float(M[1, 0]), float(M[0, 1]), float(M[1, 1]), float(t[0]), float(t[1])])
        ua = get('uarm')
        out[f'uarm.{side}'] = _card(ua, f'uarm.{side}', actor, _mat(ua, 'A', _at(out['torso'], 'shoulder'), _dir(J[f'shoulder.{side}'], J[f'elbow.{side}']), ('A', 'B'), px_cm, flip))
        fa = get('farm')
        out[f'farm.{side}'] = _card(fa, f'farm.{side}', actor, _mat(fa, 'A', _at(out[f'uarm.{side}'], 'B'), _dir(J[f'elbow.{side}'], J[f'wrist.{side}']), ('A', 'B'), px_cm, flip))
        h = hands[sides[side]]
        # palm 'in' (toward the body): the near hand shows its back, the far hand its palm; 'out' the reverse
        shows = ('back' if side == 'near' else 'palm') if h['palm'] != 'out' else ('palm' if side == 'near' else 'back')
        shape = h['shape'] if h['shape'] in LIBR.HAND_SHAPES else 'relaxed'
        hp = get('hand', side=sides[side], shows=shows, shape=shape)
        # never mirror a hand: handedness is in the drawing
        out[f'hand.{side}'] = _card(hp, f'hand.{side}', actor, _mat(hp, 'A', _at(out[f'farm.{side}'], 'B'), _dir(J[f'elbow.{side}'], J[f'wrist.{side}']), ('A', 'B'), px_cm, False))
        out[f'hand.{side}']['asked'] = dict(h, side=sides[side], shows=shows)

    order = [c['role'] for c in cards]
    return [out[r] for r in order], notes
