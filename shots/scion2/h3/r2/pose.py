"""Pose an H3 rig toward a target painting's Pose Lab markers (round 2).

Per target, keys.json picks the view rig (front / q3r), the replacement head and hands,
and sets what the markers cannot give (wrist turn, head tilt).  Bone directions come from
marker-to-marker vectors measured on the target and on that rig's master, so each bone
gets: an absolute rotation and a clamped squash along its axis for foreshortening.
Leave-one-family-out is asserted for the master, the head and every hand.
"""
import json, math, os, sys
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig, lib, specs

HERE = rig.HERE
ROOT = rig.ROOT
MK = rig.load_markers()
KEYS = json.load(open(os.path.join(HERE, 'keys.json')))
TS = json.load(open(os.path.join(ROOT, 'shots/scion2/test_set.json')))


def fam(tid):
    return tid.split('/')[0]


def P2(m, k):
    return np.array(m[k][:2], float)


def ang(v):
    return math.atan2(v[1], v[0])


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


_RIGS, _LIB = {}, None


def get_rig(view):
    if view not in _RIGS:
        _RIGS[view] = rig.Rig(view)
    return _RIGS[view]


def get_lib():
    global _LIB
    if _LIB is None:
        _LIB = lib.Lib()
    return _LIB


def solve(tid, keys=None, markers=None):
    keys = dict(KEYS.get(tid, {}), **(keys or {}))
    view = keys.get('view', 'front')
    mid = specs.MASTERS[view][0]
    m = markers or MK[tid]['markers']
    r = MK[mid]['markers']
    mid_t = (P2(m, 'hipR') + P2(m, 'hipL')) / 2; mid_r = (P2(r, 'hipR') + P2(r, 'hipL')) / 2
    L = lambda mm, a, b: np.linalg.norm(P2(mm, a) - P2(mm, b))
    rat = {
        'torso': np.linalg.norm(P2(m, 'neck') - mid_t) / np.linalg.norm(P2(r, 'neck') - mid_r),
        'legs': max(L(m, 'hipR', 'kneeR') + L(m, 'kneeR', 'ankleR'), L(m, 'hipL', 'kneeL') + L(m, 'kneeL', 'ankleL')) /
                ((L(r, 'hipR', 'kneeR') + L(r, 'kneeR', 'ankleR') + L(r, 'hipL', 'kneeL') + L(r, 'kneeL', 'ankleL')) / 2),
        'shoulders': L(m, 'shoulderR', 'shoulderL') / L(r, 'shoulderR', 'shoulderL'),
        'arms': max(L(m, 'shoulderR', 'elbowR') + L(m, 'elbowR', 'wristR'), L(m, 'shoulderL', 'elbowL') + L(m, 'elbowL', 'wristL')) /
                ((L(r, 'shoulderR', 'elbowR') + L(r, 'elbowR', 'wristR') + L(r, 'shoulderL', 'elbowL') + L(r, 'elbowL', 'wristL')) / 2),
    }
    s = float(np.median(list(rat.values()))) * keys.get('scale', 1.0)
    sp_t = P2(m, 'neck') - mid_t; sp_r = P2(r, 'neck') - mid_r
    spine = wrap(ang(sp_t) - ang(sp_r))
    rr = spine - clamp(spine, math.radians(-35), math.radians(35))
    over = keys.get('bones', {})

    def d_ang(a, b, bone=None):
        if bone in over:
            return math.radians(over[bone])
        return wrap(ang(P2(m, b) - P2(m, a)) - ang(P2(r, b) - P2(r, a)) - rr)

    def d_len(a, b, lo=0.62, hi=1.15):
        return clamp(L(m, a, b) / (s * L(r, a, b)), lo, hi)

    P = {}
    P['pelvis'] = clamp(d_ang('hipR', 'hipL'), math.radians(-15), math.radians(15))
    P['hipw'] = clamp(L(m, 'hipR', 'hipL') / (s * L(r, 'hipR', 'hipL')), 0.75, 1.12)
    P['chest'] = clamp(spine - rr, math.radians(-35), math.radians(35))
    P['torso_len'] = clamp(np.linalg.norm(sp_t) / (s * np.linalg.norm(sp_r)), 0.8, 1.1)
    P['shw'] = clamp(rat['shoulders'] / s, 0.72, 1.08)
    P['head'] = math.radians(keys.get('head_tilt', 0.0))
    for S in 'RL':
        P['uarm' + S] = d_ang('shoulder' + S, 'elbow' + S, 'uarm' + S)
        P['luarm' + S] = d_len('shoulder' + S, 'elbow' + S)
        P['farm' + S] = d_ang('elbow' + S, 'wrist' + S, 'farm' + S)
        P['lfarm' + S] = d_len('elbow' + S, 'wrist' + S, 0.62, 1.25)
        P['hand' + S] = P['farm' + S] + math.radians(keys.get('wrist' + S, 0.0))
        P['thigh' + S] = d_ang('hip' + S, 'knee' + S, 'thigh' + S)
        P['lthigh' + S] = d_len('hip' + S, 'knee' + S, 0.7, 1.12)
        P['shin' + S] = d_ang('knee' + S, 'ankle' + S, 'shin' + S)
        P['lshin' + S] = d_len('knee' + S, 'ankle' + S, 0.7, 1.12)
        toe = m.get('toe' + S)
        if toe and toe[4] >= 0.5:
            P['foot' + S] = clamp(d_ang('ankle' + S, 'toe' + S), math.radians(-35), math.radians(35))
        else:
            P['foot' + S] = 0.0
        P['foot' + S] += math.radians(keys.get('foot' + S, 0.0))
    for k, v in keys.get('len', {}).items():
        P[k] = v
    for k, v in keys.get('add', {}).items():   # relative corrections (deg) set by eye
        P[k] += math.radians(v)
    for k, v in keys.get('set', {}).items():   # absolute params (deg) set by eye
        P[k] = math.radians(v)
    for S in 'RL':
        if 'hand' + S not in keys.get('set', {}):
            P['hand' + S] = P['farm' + S] + math.radians(keys.get('wrist' + S, 0.0))
    c_, s_ = math.cos(rr), math.sin(rr)
    G = np.array([[s * c_, -s * s_, 0], [s * s_, s * c_, 0]], float)
    Rg = get_rig(view)
    if 'place' in keys:   # [scale, x, y]: where the markers are unusable (cropped paintings)
        s = keys['place'][0]; G = np.array([[s, 0, 0], [0, s, 0]], float); mid_t = np.array(keys['place'][1:], float)
    G[:, 2] = mid_t + np.array(keys.get('offset', (0, 0))) - G[:, :2] @ Rg.J['midhip']
    opts = {'head': keys.get('head'), 'hands': keys.get('hands', {}), 'hand_rot': keys.get('hand_rot', {}),
            'head_scale': keys.get('head_scale', 1.0), 'hand_scale': keys.get('hand_scale', 1.0),
            'head_off': keys.get('head_off', (0, 0))}
    return P, G, view, opts, {'scale': s, 'ratios': {k: round(float(v), 3) for k, v in rat.items()}, 'turn_deg': math.degrees(rr)}


def check_families(tid, view, opts):
    f = fam(tid)
    used = [specs.MASTERS[view][0]]
    L = get_lib()
    h = opts.get('head')
    if h:
        used.append(L.meta['heads'][h if isinstance(h, str) else h[0]]['src'])
    for side, hs in opts.get('hands', {}).items():
        if hs and hs not in ('none', 'cuff'):
            used.append(L.meta['hands'][hs if isinstance(hs, str) else hs[0]]['src'])
    bad = [u for u in used if fam(u) == f]
    assert not bad, f'leave-one-family-out violated for {tid}: {bad}'
    return used


def render_target(tid, keys=None, ss=2):
    P, G, view, opts, info = solve(tid, keys)
    info['sources'] = check_families(tid, view, opts)
    t = MK[tid]
    img, jp = get_rig(view).render(P, G, (t['w'], t['h']), ss=ss, opts=opts, lib=get_lib())
    return img, info, P


def painting(tid):
    return rig.read_rgba(os.path.join(rig.CUT, tid + '.webp'))


def on_bg(rgba, bg=(236, 236, 236)):
    a = rgba[..., 3:] / 255.
    return (rgba[..., :3] * a + np.array(bg) * (1 - a)).astype(np.uint8)


def sheet(rows, path, H=440):
    tiles = []
    for title, a, b in rows:
        pair = [cv2.resize(on_bg(im), (max(1, int(im.shape[1] * H / im.shape[0])), H), interpolation=cv2.INTER_AREA) for im in (a, b)]
        t = np.hstack([pair[0], np.full((H, 6, 3), 255, np.uint8), pair[1]])
        if t.shape[1] > 2300:
            k = 2300 / t.shape[1]
            t = cv2.resize(t, (2300, int(H * k)), interpolation=cv2.INTER_AREA)
            t = cv2.copyMakeBorder(t, 0, H - t.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        t = cv2.copyMakeBorder(t, 26, 0, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        cv2.putText(t, title[:60], (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(t)
    rows_img, row, w = [], [], 0
    for t in tiles:
        if row and w + t.shape[1] > 2400:
            rows_img.append(row); row, w = [], 0
        row.append(t); w += t.shape[1] + 12
    rows_img.append(row)
    out = [cv2.copyMakeBorder(np.hstack(sum([[t, np.full((t.shape[0], 12, 3), 255, np.uint8)] for t in rr], [])), 0, 12, 0, 0,
                              cv2.BORDER_CONSTANT, value=(255, 255, 255)) for rr in rows_img]
    W = max(o.shape[1] for o in out)
    img = np.vstack([cv2.copyMakeBorder(o, 0, 0, 0, W - o.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for o in out])
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 88])


if __name__ == '__main__':
    ids = sys.argv[1:] or [p['id'] for p in TS['poses']]
    gaps = json.load(open(os.path.join(HERE, 'gaps.json')))['cannot_attempt'] if os.path.exists(os.path.join(HERE, 'gaps.json')) else {}
    od = os.path.join(HERE, 'out'); os.makedirs(od, exist_ok=True)
    rows, infos = [], {}
    for tid in ids:
        if tid in gaps:
            continue
        img, info, P = render_target(tid)
        cv2.imwrite(os.path.join(od, tid.replace('/', '__') + '.png'), img)
        rows.append((tid, painting(tid), img))
        infos[tid] = dict(info, keys=KEYS.get(tid, {}))
        print(tid, info['scale'], info['sources'])
    sheet(rows, os.path.join(od, 'sheet.jpg' if len(sys.argv) == 1 else 'sheet_partial.jpg'))
    if len(sys.argv) == 1:
        json.dump(infos, open(os.path.join(od, 'poses.json'), 'w'), indent=1)
