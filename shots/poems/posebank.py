"""A pose library from the Crash Lab bank: real poses, classified, so a shot breakdown can be
rendered with the card rig instead of a stick sketch.

    python3 shots/poems/posebank.py        # writes poems/poses.json

Every actor frame of every vignette (T101-T191) is measured: pelvis height, feet off the
floor, knee and hip bend, torso tilt, how fast it moves, where the hands are. Each frame
gets one class (stand, walk, run, sit, kneel, crouch, lie, fall, float, reach, lean, dance)
and per class the most typical frame is kept, centred on its pelvis and turned to face +z.
"""
import glob, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'arena', 'puppet'))
import p3d

BANK = os.path.join(p3d.ARENA, 'bolas', 'bank')
J = p3d.J


def nrm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def angle(a, b, c):
    u, v = nrm(a - b), nrm(c - b)
    return math.degrees(math.acos(float(np.clip(np.dot(u, v), -1, 1))))


def features(j, prev, scale):
    P = lambda k: np.array(j[J[k]], float)
    pel = P('pelvis')
    feet = min(P('heelL')[1], P('heelR')[1], P('toeL')[1], P('toeR')[1])
    knee = (angle(P('hipL'), P('kneeL'), P('ankleL')) + angle(P('hipR'), P('kneeR'), P('ankleR'))) / 2
    kneemin = min(P('kneeL')[1], P('kneeR')[1])
    spine = nrm(P('neckBase') - pel)
    tilt = math.degrees(math.acos(float(np.clip(spine[1], -1, 1))))
    sp = 0.0 if prev is None else float(np.linalg.norm(np.array(prev[J['pelvis']], float)[[0, 2]] - pel[[0, 2]]))
    vy = 0.0 if prev is None else float(pel[1] - prev[J['pelvis']][1])
    hand_up = max(P('wristL')[1], P('wristR')[1]) - P('shoulderL')[1]
    reach = max(np.linalg.norm((P('wristL') - P('shoulderL'))[[0, 2]]), np.linalg.norm((P('wristR') - P('shoulderR'))[[0, 2]]))
    return dict(pel=pel[1] / scale, feet=feet, knee=knee, kneemin=kneemin / scale, tilt=tilt, sp=sp, vy=vy, hand_up=hand_up, reach=reach / scale)


def classify(f):
    if f['tilt'] > 60 and f['pel'] < 40:
        return 'lie'
    if f['vy'] < -2.5 and f['feet'] > 8:
        return 'fall'
    if f['feet'] > 18 and abs(f['vy']) < 1.5:
        return 'float'
    if f['pel'] < 62 and f['kneemin'] < 12:
        return 'kneel'
    if 38 < f['pel'] < 66 and f['knee'] < 125 and f['tilt'] < 35 and f['feet'] < 4:
        return 'sit' if f['sp'] < 0.4 else 'crouch'
    if f['pel'] < 66 and f['knee'] < 115:
        return 'crouch'
    if f['sp'] > 4.0:
        return 'run'
    if f['sp'] > 0.9:
        return 'walk'
    if f['hand_up'] > 0 and f['reach'] > 30:
        return 'reach'
    if f['tilt'] > 20:
        return 'lean'
    if f['hand_up'] > 12:
        return 'dance'
    return 'stand'


def canonical(a):
    """Centre on the pelvis (feet stay on the floor) and turn so the pelvis faces +z."""
    j = np.array([q if q is not None else [0, 0, 0] for q in a['j']], float)
    c = np.array([j[J['pelvis']][0], 0, j[J['pelvis']][2]])
    pf = np.array(a['pfwd'], float)
    th = math.atan2(pf[0], pf[2])
    R = np.array([[math.cos(-th), 0, math.sin(-th)], [0, 1, 0], [-math.sin(-th), 0, math.cos(-th)]])
    rot = lambda v: (R @ np.asarray(v, float)).tolist()
    out = dict(a)
    out['j'] = [((R @ (q - c)).round(1).tolist() if a['j'][i] is not None else None) for i, q in enumerate(j)]
    for k in ('fwd', 'up', 'hfwd', 'pfwd'):
        out[k] = [round(x, 3) for x in rot(a[k])]
    return out


def main():
    pools = {}
    for f in sorted(glob.glob(os.path.join(BANK, 'T*.json'))):
        V = json.load(open(f))
        scale = {a['id']: a.get('scale', 1) for a in V['actors']}
        prev = {}
        for fi, fr in enumerate(V['frames']):
            if fi % 2:
                continue
            for aid, a in fr['a'].items():
                if any(a['j'][J[k]] is None for k in ('pelvis', 'heelL', 'heelR', 'neckBase', 'kneeL', 'kneeR')):
                    continue
                ft = features(a['j'], prev.get(aid), scale.get(aid, 1))
                prev[aid] = a['j']
                c = classify(ft)
                pools.setdefault(c, []).append((ft, os.path.basename(f)[:-5], fi, aid, scale.get(aid, 1), a))
    lib = {}
    for c, items in pools.items():
        F = np.array([[i[0]['pel'], i[0]['knee'], i[0]['tilt'], i[0]['reach']] for i in items])
        med = np.median(F, 0)
        k = int(np.argmin(((F - med) / (F.std(0) + 1e-6)) .__pow__(2).sum(1)))
        ft, tid, fi, aid, sc, a = items[k]
        lib[c] = {'from': f'{tid} f{fi} {aid}', 'scale': sc, 'count': len(items), 'actor': canonical(a)}
        print(f'{c:7s} {len(items):6d} frames  <- {tid} f{fi} {aid}')
    json.dump(lib, open(os.path.join(HERE, 'poses.json'), 'w'))


if __name__ == '__main__':
    main()
