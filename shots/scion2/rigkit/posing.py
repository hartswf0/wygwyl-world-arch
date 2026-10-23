"""pose_from_markers(char, target) -> pose dict;  render(pose) -> RGBA.

A pose dict is plain data (json-able except numpy arrays, which are lists here):
  {char, target, view, mirror, P:{param: value}, G:[[...],[...]], size:[w,h],
   opts:{head, hands:{R,L}, props:[[pid, layer]], ...}, sources:{body, head, handR, handL, props}, flags:[...]}

Choices made automatically (each can be overridden by keys, see chars/<char>.py KEYS):
  view  : from the catalog hint of the target painting (front / 3qR / 3qL / profile / back /
          kneel / sit / lie) mapped to the character's rigs (VIEW_RIGS), else from the marker
          shoulder width vs torso length.  3/4 and profile to screen-left render the 3/4-right
          rig mirrored.
  head  : the target painting's own head if it cut cleanly, else the head whose catalog gaze
          and view match best.
  hands : the target painting's own hands where they cut cleanly, else the rig's painted hand.
  props : costume details named in chars/<char>.py COSTUME_PROPS for the painting's costume.
"""
import json, math, os
import numpy as np, cv2

from . import core, parts as parts_mod

_RIG, _PARTS, _CAT = {}, {}, {}


def rig(char, view):
    if (char, view) not in _RIG:
        _RIG[(char, view)] = core.Rig(char, view)
    return _RIG[(char, view)]


def parts(char):
    if char not in _PARTS:
        _PARTS[char] = parts_mod.Parts(char)
    return _PARTS[char]


def catalog(char):
    if char not in _CAT:
        spec = core.char_module(char)
        _CAT[char] = spec.catalog() if hasattr(spec, 'catalog') else {}
    return _CAT[char]


def P2(m, k):
    return np.array(m[k][:2], float)


def ang(v):
    return math.atan2(v[1], v[0])


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


SIDES = ('R', 'L')
CHAINS = {'shoulder': 'sh', 'elbow': 'el', 'wrist': 'wr', 'hip': 'hip', 'knee': 'kn', 'ankle': 'an', 'toe': 'to'}


def mirror_markers(m, W):
    """mirror x and swap anatomical labels (a mirrored person's right arm is his left)"""
    out = {}
    for k, v in m.items():
        k2 = k[:-1] + ('L' if k[-1] == 'R' else 'R') if k[-1] in 'RL' and k[:-1] in CHAINS else k
        out[k2] = [W - v[0]] + list(v[1:])
    return out


def side_map(R, mk_master):
    """rig side -> marker label side, by which marker shoulder sits nearest the rig's shR"""
    dR = np.linalg.norm(P2(mk_master, 'shoulderR') - R.J['shR'])
    dL = np.linalg.norm(P2(mk_master, 'shoulderL') - R.J['shR'])
    return {'R': 'R', 'L': 'L'} if dR <= dL else {'R': 'L', 'L': 'R'}


def choose_view(char, tid, t, keys):
    spec = core.char_module(char)
    if 'view' in keys:
        v = keys['view']
        return (v[:-2], True) if v.endswith('_m') else (v, False)
    c = catalog(char).get(tid, {})
    hint = c.get('view') or ''
    cls = c.get('cls') or ''
    VR = spec.VIEW_RIGS
    if cls in VR:                   # a posture rig (kneel / sit / lie) wins over the view
        return VR[cls]
    if hint in VR:
        return VR[hint]
    m = t['markers']
    mid = (P2(m, 'hipR') + P2(m, 'hipL')) / 2
    T = np.linalg.norm(P2(m, 'neck') - mid) + 1e-6
    sw = np.linalg.norm(P2(m, 'shoulderR') - P2(m, 'shoulderL')) / T
    if sw > 0.62:
        return VR['front']
    face_right = m['chin'][0] > m['neck'][0]
    return VR['3qR'] if face_right else VR['3qL']


def solve_body(R, mk_master, m, keys):
    """bone parameters from target markers m measured against the rig master's markers"""
    r = mk_master
    sm = side_map(R, r)
    mid_t = (P2(m, 'hipR') + P2(m, 'hipL')) / 2
    mid_r = (P2(r, 'hipR') + P2(r, 'hipL')) / 2
    L = lambda mm, a, b: np.linalg.norm(P2(mm, a) - P2(mm, b))
    rat = {
        'torso': np.linalg.norm(P2(m, 'neck') - mid_t) / np.linalg.norm(P2(r, 'neck') - mid_r),
        'legs': max(L(m, 'hipR', 'kneeR') + L(m, 'kneeR', 'ankleR'), L(m, 'hipL', 'kneeL') + L(m, 'kneeL', 'ankleL')) /
                ((L(r, 'hipR', 'kneeR') + L(r, 'kneeR', 'ankleR') + L(r, 'hipL', 'kneeL') + L(r, 'kneeL', 'ankleL')) / 2),
        'arms': max(L(m, 'shoulderR', 'elbowR') + L(m, 'elbowR', 'wristR'), L(m, 'shoulderL', 'elbowL') + L(m, 'elbowL', 'wristL')) /
                ((L(r, 'shoulderR', 'elbowR') + L(r, 'elbowR', 'wristR') + L(r, 'shoulderL', 'elbowL') + L(r, 'elbowL', 'wristL')) / 2),
    }
    s = float(np.median(list(rat.values()))) * keys.get('scale', 1.0)
    sp_t = P2(m, 'neck') - mid_t; sp_r = P2(r, 'neck') - mid_r
    spine = wrap(ang(sp_t) - ang(sp_r))
    rr = spine - clamp(spine, math.radians(-35), math.radians(35))
    over = keys.get('bones', {})

    def d_ang(a, b, bone):
        if bone in over:
            return math.radians(over[bone])
        return wrap(ang(P2(m, b) - P2(m, a)) - ang(P2(r, b) - P2(r, a)) - rr)

    def d_len(a, b, lo, hi):
        return clamp(L(m, a, b) / (s * L(r, a, b) + 1e-6), lo, hi)

    P = {}
    P['pelvis'] = clamp(d_ang('hipR', 'hipL', 'pelvis'), math.radians(-15), math.radians(15))
    P['hipw'] = clamp(L(m, 'hipR', 'hipL') / (s * L(r, 'hipR', 'hipL') + 1e-6), 0.75, 1.12)
    P['chest'] = clamp(spine - rr, math.radians(-35), math.radians(35))
    P['torso_len'] = clamp(np.linalg.norm(sp_t) / (s * np.linalg.norm(sp_r)), 0.8, 1.1)
    P['shw'] = clamp(L(m, 'shoulderR', 'shoulderL') / (s * L(r, 'shoulderR', 'shoulderL') + 1e-6), 0.72, 1.08)
    P['head'] = math.radians(keys.get('head_tilt', 0.0))
    for S in SIDES:
        X = sm[S]
        P['uarm' + S] = d_ang('shoulder' + X, 'elbow' + X, 'uarm' + S)
        P['luarm' + S] = d_len('shoulder' + X, 'elbow' + X, 0.62, 1.15)
        P['farm' + S] = d_ang('elbow' + X, 'wrist' + X, 'farm' + S)
        P['lfarm' + S] = d_len('elbow' + X, 'wrist' + X, 0.62, 1.25)
        P['thigh' + S] = d_ang('hip' + X, 'knee' + X, 'thigh' + S)
        P['lthigh' + S] = d_len('hip' + X, 'knee' + X, 0.7, 1.12)
        P['shin' + S] = d_ang('knee' + X, 'ankle' + X, 'shin' + S)
        P['lshin' + S] = d_len('knee' + X, 'ankle' + X, 0.7, 1.12)
        toe, toe_r = m.get('toe' + X), r.get('toe' + X)
        if toe and toe_r and toe[4] >= 0.5 and toe_r[4] >= 0.5:
            P['foot' + S] = clamp(d_ang('ankle' + X, 'toe' + X, 'foot' + S), math.radians(-35), math.radians(35))
        else:
            P['foot' + S] = 0.0
    for k, v in keys.get('add', {}).items():
        P[k] += math.radians(v)
    for k, v in keys.get('set', {}).items():
        P[k] = math.radians(v)
    for k, v in keys.get('len', {}).items():
        P[k] = v
    for S in SIDES:
        if 'hand' + S not in keys.get('set', {}):
            P['hand' + S] = P['farm' + S] + math.radians(keys.get('wrist' + S, 0.0))
    c_, s_ = math.cos(rr), math.sin(rr)
    G = np.array([[s * c_, -s * s_, 0], [s * s_, s * c_, 0]], float)
    G[:, 2] = mid_t + np.array(keys.get('offset', (0, 0))) - G[:, :2] @ R.J['midhip']
    return P, G, sm, {'scale': s, 'turn_deg': math.degrees(rr)}


def choose_head(char, tid, keys, mirror):
    if 'head' in keys:
        return keys['head']
    pt = parts(char)
    own = tid + '#head'
    if pt.has(own) and pt.index[own]['ok']:
        return [own, mirror]
    # nearest by catalog view and gaze
    c = catalog(char).get(tid, {})
    best, bs = None, -1
    for pid, p in pt.index.items():
        if p['kind'] != 'head' or not p['ok']:
            continue
        a = p.get('attrs', {})
        sc = 2 * (a.get('gaze') == c.get('gaze')) + 2 * (a.get('view') == c.get('view')) + (a.get('costume') == c.get('costume'))
        if sc > bs:
            best, bs = pid, sc
    if best is None:
        return None
    flip = mirror
    return [best, flip]


def choose_hands(char, tid, sm, keys, mirror):
    if 'hands' in keys:
        return keys['hands']
    pt = parts(char)
    out = {}
    for S in SIDES:
        X = sm[S]
        if mirror:
            X = 'L' if X == 'R' else 'R'
        own = tid + '#hand' + X
        if pt.has(own) and pt.index[own]['ok']:
            out[S] = [own, mirror]
    return out


def pose_from_markers(char, tid, keys=None, markers=None):
    spec = core.char_module(char)
    keys = dict(getattr(spec, 'KEYS', {}).get(tid, {}), **(keys or {}))
    MK = core.load_markers(char)
    t = MK[tid]
    view, mirror = choose_view(char, tid, t, keys)
    R = rig(char, view)
    mk_master = MK[R.meta['master']]['markers']
    m = markers or t['markers']
    if mirror:
        m = mirror_markers(m, t['w'])
    P, G, sm, info = solve_body(R, mk_master, m, keys)
    head = choose_head(char, tid, keys, mirror)
    hands = choose_hands(char, tid, sm, keys, mirror)
    props = []
    c = catalog(char).get(tid, {})
    for pid, after in getattr(spec, 'COSTUME_PROPS', {}).get(c.get('costume'), []):
        props.append([pid, after])
    props += keys.get('props', [])
    flags = list(spec.painting_flags(tid, catalog(char))) if hasattr(spec, 'painting_flags') else []
    if c.get('cls') in getattr(spec, 'UNREACHED', {}) and c.get('cls') not in spec.VIEW_RIGS:
        flags.append('posture %s: no %s rig, rendered on the %s rig' % (c['cls'], c['cls'], view))
    if c.get('view', '').startswith('back'):
        flags.append('back view: rendered as a front/3-4 figure')
    if c.get('use') == 'crop':
        flags.append('target painting is cropped by the sheet edge; markers partial')
    if head is None:
        flags.append('no usable head')
    elif head[0] != tid + '#head':
        flags.append('head from %s (own head unusable)' % head[0].split('#')[0])
    for S in SIDES:
        if S not in hands:
            flags.append('hand %s: rig master hand (own hand hidden or unusable)' % S)
    opts = {'head': head, 'hands': hands, 'props': props, 'head_scale': keys.get('head_scale', 1.0),
            'hand_scale': keys.get('hand_scale', 1.0), 'head_off': keys.get('head_off', (0, 0))}
    pt = parts(char)
    src = {'body': R.meta['master'] + (' (mirrored)' if mirror else ''),
           'head': pt.index[head[0]]['painting'] if head else R.meta['master'],
           'handR': pt.index[hands['R'][0]]['painting'] if 'R' in hands else R.meta['master'],
           'handL': pt.index[hands['L'][0]]['painting'] if 'L' in hands else R.meta['master'],
           'props': [pt.index[p[0]]['painting'] for p in props]}
    return {'char': char, 'target': tid, 'view': view, 'mirror': mirror, 'P': {k: float(v) for k, v in P.items()},
            'G': G.tolist(), 'size': [t['w'], t['h']], 'opts': opts, 'sources': src, 'flags': flags, 'info': info}


def render(pose, ss=2, size=None, G=None):
    R = rig(pose['char'], pose['view'])
    W, H = size or pose['size']
    G = np.array(G if G is not None else pose['G'], float)
    if pose['mirror'] and size is None:
        pass
    img, _ = R.render(pose['P'], G, (W, H), ss=ss, opts=pose['opts'], lib=parts(pose['char']))
    if pose['mirror']:
        img = img[:, ::-1].copy()
    return img
