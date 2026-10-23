"""Pose the H3 rig toward a target painting's Pose Lab markers.

Directions and lengths are measured marker-to-marker on the target and on the master
(the same detector made both), so each bone gets: absolute rotation from the master's
bone direction to the target's, and a squash along its axis for foreshortening (clamped).
Hand angle, wrist bend and head yaw are not in the markers; they are animator keys in
keys.json (per target, written by eye, documented there).
"""
import json, math, os, sys
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig

HERE = rig.HERE
ROOT = rig.ROOT
MK = rig.load_markers()
MASTER = MK[rig.MASTER_ID]['markers']
MASTER_FAMILY = rig.MASTER_ID.split('/')[0]
KEYS = json.load(open(os.path.join(HERE, 'keys.json'))) if os.path.exists(os.path.join(HERE, 'keys.json')) else {}


def P2(m, k):
    return np.array(m[k][:2], float)


def mid(m, a, b):
    return (P2(m, a) + P2(m, b)) / 2


def ang(v):
    return math.atan2(v[1], v[0])


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def solve(tid, keys=None):
    t = MK[tid]
    m = t['markers']; r = MASTER
    keys = dict(KEYS.get(tid, {}), **(keys or {}))
    log = []
    hip_t, hip_r = mid(m, 'hipR', 'hipL'), mid(r, 'hipR', 'hipL')
    L = lambda mm, a, b: np.linalg.norm(P2(mm, a) - P2(mm, b))
    rat = {
        'torso': np.linalg.norm(P2(m, 'neck') - hip_t) / np.linalg.norm(P2(r, 'neck') - hip_r),
        'head': L(m, 'head', 'neck') / L(r, 'head', 'neck'),
        'legs': max(L(m, 'hipR', 'kneeR') + L(m, 'kneeR', 'ankleR'), L(m, 'hipL', 'kneeL') + L(m, 'kneeL', 'ankleL')) /
                ((L(r, 'hipR', 'kneeR') + L(r, 'kneeR', 'ankleR') + L(r, 'hipL', 'kneeL') + L(r, 'kneeL', 'ankleL')) / 2),
        'shoulders': L(m, 'shoulderR', 'shoulderL') / L(r, 'shoulderR', 'shoulderL'),
        'arms': max(L(m, 'shoulderR', 'elbowR') + L(m, 'elbowR', 'wristR'), L(m, 'shoulderL', 'elbowL') + L(m, 'elbowL', 'wristL')) /
                ((L(r, 'shoulderR', 'elbowR') + L(r, 'elbowR', 'wristR') + L(r, 'shoulderL', 'elbowL') + L(r, 'elbowL', 'wristL')) / 2),
    }
    s = float(np.median(list(rat.values()))) * keys.get('scale', 1.0)

    sp_t = P2(m, 'neck') - hip_t; sp_r = P2(r, 'neck') - hip_r
    spine = wrap(ang(sp_t) - ang(sp_r))
    # beyond 35 deg the whole figure turns (lying, falling); the rest is the chest's lean
    rr = spine - clamp(spine, math.radians(-35), math.radians(35)) if keys.get('root_turn', True) else 0.0

    def d_ang(a, b):  # absolute rotation that takes master bone a->b to target bone a->b
        return wrap(ang(P2(m, b) - P2(m, a)) - ang(P2(r, b) - P2(r, a)) - rr)

    def d_len(a, b, lo=0.62, hi=1.15):
        return clamp(L(m, a, b) / (s * L(r, a, b)), lo, hi)

    P = {}
    P['pelvis'] = clamp(d_ang('hipR', 'hipL'), math.radians(-15), math.radians(15))
    P['hipw'] = clamp(L(m, 'hipR', 'hipL') / (s * L(r, 'hipR', 'hipL')), 0.75, 1.12)
    P['chest'] = clamp(spine - rr, math.radians(-35), math.radians(35))
    P['torso_len'] = clamp(np.linalg.norm(sp_t) / (s * np.linalg.norm(sp_r)), 0.8, 1.1)
    P['shw'] = clamp(rat['shoulders'] / s, 0.72, 1.08)
    # The 'head' marker sits on the face side in 3/4 views, so it cannot give the tilt;
    # the head follows the chest, plus an animator key (degrees) set by eye.
    P['head'] = math.radians(keys.get('head', 0.0))
    for S in 'RL':
        P['uarm' + S] = d_ang('shoulder' + S, 'elbow' + S)
        P['luarm' + S] = d_len('shoulder' + S, 'elbow' + S)
        P['farm' + S] = d_ang('elbow' + S, 'wrist' + S)
        P['lfarm' + S] = d_len('elbow' + S, 'wrist' + S)
        P['hand' + S] = P['farm' + S] + math.radians(keys.get('wrist' + S, 0.0))
        P['thigh' + S] = d_ang('hip' + S, 'knee' + S)
        P['lthigh' + S] = d_len('hip' + S, 'knee' + S, 0.7, 1.12)
        P['shin' + S] = d_ang('knee' + S, 'ankle' + S)
        P['lshin' + S] = d_len('knee' + S, 'ankle' + S, 0.7, 1.12)
        toe = m.get('toe' + S)
        if toe and toe[4] >= 0.5 and keys.get('foot_from_toe', True):
            P['foot' + S] = clamp(d_ang('ankle' + S, 'toe' + S), math.radians(-35), math.radians(35))
        else:
            P['foot' + S] = 0.0
        P['foot' + S] += math.radians(keys.get('foot' + S, 0.0))
        for b in ('uarm', 'farm', 'thigh', 'shin'):
            pass
    # elbow / knee bend amounts (for the record)
    bends = {S: (math.degrees(wrap(P['farm' + S] - P['uarm' + S])), math.degrees(wrap(P['shin' + S] - P['thigh' + S]))) for S in 'RL'}
    c_, s_ = math.cos(rr), math.sin(rr)
    G = np.array([[s * c_, -s * s_, 0], [s * s_, s * c_, 0]], float)
    G[:, 2] = hip_t - G[:, :2] @ rig.J['midhip']
    if rr:
        log.append(f'whole figure turned {math.degrees(rr):.0f} deg')
    return P, G, (t['w'], t['h']), {'scale': s, 'ratios': rat, 'bends_deg': bends, 'log': log,
                                     'head_yaw': keys.get('yaw', 0.0), 'hands': keys.get('hands', {})}


_R = None


def get_rig():
    global _R
    if _R is None:
        _R = rig.Rig()
    return _R


def render_target(tid, keys=None, pad=0):
    P, G, size, info = solve(tid, keys)
    R = get_rig()
    W, H = size
    G2 = G.copy(); G2[:, 2] += pad
    img, jp = R.render(P, G2, (W + 2 * pad, H + 2 * pad), head_yaw=info['head_yaw'], hands=info['hands'])
    return img, info, P


def painting(tid):
    im = cv2.imread(os.path.join(ROOT, 'shots/kits/cut', tid + '.webp'), cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


def on_bg(rgba, bg=(236, 236, 236)):
    a = rgba[..., 3:] / 255.
    return (rgba[..., :3] * a + np.array(bg) * (1 - a)).astype(np.uint8)


def sheet(rows, path, H=520, label=True):
    """rows: list of (title, painting rgba, ours rgba) -> side by side at the same height."""
    tiles = []
    for title, a, b in rows:
        pair = []
        for im in (a, b):
            ys, xs = np.nonzero(im[..., 3] > 10)
            # same height: both crops are scaled so the canvas height maps to H
            c = on_bg(im)
            s = H / im.shape[0]
            pair.append(cv2.resize(c, (max(1, int(im.shape[1] * s)), H), interpolation=cv2.INTER_AREA))
        t = np.hstack([pair[0], np.full((H, 6, 3), 255, np.uint8), pair[1]])
        t = cv2.copyMakeBorder(t, 26, 0, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        if label:
            cv2.putText(t, title[:60], (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(t)
    rows_img = []; row = []; w = 0; MAXW = 2400
    for t in tiles:
        if row and w + t.shape[1] > MAXW:
            rows_img.append(row); row = []; w = 0
        row.append(t); w += t.shape[1] + 12
    rows_img.append(row)
    out = []
    for rr in rows_img:
        im = np.hstack(sum([[t, np.full((t.shape[0], 12, 3), 255, np.uint8)] for t in rr], []))
        im = cv2.copyMakeBorder(im, 0, 12, 0, MAXW + 200 - im.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255))
        out.append(im)
    W = max(o.shape[1] for o in out)
    out = [cv2.copyMakeBorder(o, 0, 0, 0, W - o.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for o in out]
    img = np.vstack(out)
    ys, xs = np.nonzero(img.min(2) < 250)
    img = img[:ys.max() + 14, :xs.max() + 14]
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 88])


def fam(tid):
    return tid.split('/')[0]


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'kill'
    TS = json.load(open(os.path.join(ROOT, 'shots/scion2/test_set.json')))
    if mode == 'kill':
        ids = ['poet.07.main-poses/push-two-sides-apart', 'poet.04.main-poses/04-6-rise-flex-reflect',
               'poet.08.main-poses/03-gentle-slow-bent-knee-dance-alone']
        od = os.path.join(HERE, 'kill')
    else:
        ids = sys.argv[2:] or [p['id'] for p in TS['poses']]
        od = os.path.join(HERE, 'out')
    os.makedirs(od, exist_ok=True)
    rows = []; infos = {}
    for tid in ids:
        assert fam(tid) != MASTER_FAMILY, 'leave-one-family-out violated'
        img, info, P = render_target(tid)
        name = tid.replace('/', '__')
        cv2.imwrite(os.path.join(od, name + '.png'), img)
        rows.append((tid, painting(tid), img))
        infos[tid] = {'scale': info['scale'], 'bends_deg': info['bends_deg'], 'log': info['log'],
                      'params_deg': {k: (round(math.degrees(v), 1) if k[0] not in 'l' and k not in ('hipw', 'shw', 'torso_len') else round(v, 3)) for k, v in P.items()}}
        print(tid, info['bends_deg'], info['log'])
    sheet(rows, os.path.join(od, 'sheet.jpg' if len(sys.argv) <= 2 else 'sheet_partial.jpg'), H=420)
    json.dump(infos, open(os.path.join(od, 'poses.json'), 'w'), indent=1)
