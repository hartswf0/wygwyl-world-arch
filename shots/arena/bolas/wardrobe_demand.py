"""Wardrobe demand: what a cut-out skin must contain to wear the Bolas motion bank, and how much of it a given
wardrobe already covers.

    python3 shots/arena/bolas/wardrobe_demand.py            (needs bank/ from export_bank.mjs)

For every frame, actor and body segment of every baked vignette, seen through that vignette's own Crash Lab
camera, it records:
  view     which side of the part faces the camera: front, 3q (three-quarter), profile, 3q_back, back
           (torso from the chest frame, head from the head frame, limbs inherit the torso's view)
  fore     foreshortening = projected length / true length: full >= .85, mid .6-.85, short .35-.6, end <.35
  mirror   whether the part faces screen-left (a flipped piece can serve; it is counted, not required)
plus hand shapes, faces (mouth / eyes) and leg poses (knee angle, foot off the floor, lying).

A cut-out piece serves one (segment, view, fore) cell. Squashing a 'full' piece to stand in for 'mid' is the
usual cheat; it is reported separately as 'squash', not as coverage.

Writes demand.json and demand.md next to this file.
"""
import json, math, os, glob
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(HERE, 'bank')
WARD = os.path.join(HERE, 'wardrobe')

SEGS = {  # segment: (joint a, joint b, true-length key in R2, view source)
    'torso': ('pelvis', 'neckBase', 'spine', 'torso'),
    'head': ('headBase', 'headTop', None, 'head'),
    'thighL': ('hipL', 'kneeL', 'thigh', 'torso'), 'thighR': ('hipR', 'kneeR', 'thigh', 'torso'),
    'shinL': ('kneeL', 'ankleL', 'shin', 'torso'), 'shinR': ('kneeR', 'ankleR', 'shin', 'torso'),
    'footL': ('heelL', 'toeL', None, 'torso'), 'footR': ('heelR', 'toeR', None, 'torso'),
    'uarmL': ('shoulderL', 'elbowL', 'upper', 'torso'), 'uarmR': ('shoulderR', 'elbowR', 'upper', 'torso'),
    'farmL': ('elbowL', 'wristL', 'fore', 'torso'), 'farmR': ('elbowR', 'wristR', 'fore', 'torso'),
}
R2 = dict(thigh=44, shin=43, upper=28, fore=26, spine=46)
FOOT_LEN = 17 + 5 + 12  # heelB + toeF + ankleB, roughly heel to toe
HEAD_LEN = 20 * 1.8 + 0  # headBase to headTop
VIEWS = ['front', '3q', 'profile', '3q_back', 'back']
FORES = ['full', 'mid', 'short', 'end']


def cam(view):
    yaw, elev = math.radians(view.get('yaw', -22)), math.radians(view.get('elev', 7))
    cy, sy, ce, se = math.cos(yaw), math.sin(yaw), math.cos(elev), math.sin(elev)

    def P(p):  # world -> (screen x, screen y up, depth toward the viewer)
        x, y, z = p
        x1, z1 = x * cy - z * sy, x * sy + z * cy
        return (x1, y * ce - z1 * se, y * se + z1 * ce)
    return P


def view_of(Pv):
    """Pv: a forward vector in camera space. 0 deg = facing the viewer."""
    th = math.degrees(math.atan2(Pv[0], Pv[2]))
    a = abs(th)
    v = VIEWS[min(4, int((a + 22.5) // 45))]
    return v, th < 0


def fore_of(r):
    return 'full' if r >= .85 else 'mid' if r >= .6 else 'short' if r >= .35 else 'end'


def angle(a, b, c):
    u = [a[i] - b[i] for i in range(3)]; v = [c[i] - b[i] for i in range(3)]
    nu, nv = math.hypot(*u), math.hypot(*v)
    if nu < 1e-6 or nv < 1e-6:
        return 180.0
    return math.degrees(math.acos(max(-1, min(1, sum(u[i] * v[i] for i in range(3)) / (nu * nv)))))


def load_wardrobes():
    W = {}
    for p in sorted(glob.glob(os.path.join(WARD, '*.json'))):
        w = json.load(open(p))
        W[w['name']] = w
    return W


def has(w, seg, v, f):
    base = seg.rstrip('LR') if seg not in ('head', 'torso') else seg
    for c in w['cells']:
        if c['seg'] == base and v in c['views'] and f in c['fores']:
            return True
    return False


def main():
    idx = json.load(open(os.path.join(BANK, 'index.json')))
    J = {k: i for i, k in enumerate(idx['joints'])}
    wards = load_wardrobes()
    cells = defaultdict(Counter)  # character -> (seg, view, fore) -> frames
    mirror = Counter(); hands = defaultdict(Counter); faces = defaultdict(Counter); legs = defaultdict(Counter)
    frames_by_char = Counter()
    cover = {n: defaultdict(lambda: [0, 0, 0]) for n in wards}  # wardrobe -> char -> [frames, fully covered, covered with squash]
    gaps = {n: defaultdict(lambda: {'frames': 0, 'examples': []}) for n in wards}
    per_vig = []
    for vmeta in idx['vignettes']:
        V = json.load(open(os.path.join(BANK, vmeta['id'] + '.json')))
        P = cam(V['view'] or {})
        names = {a['id']: a['name'] for a in V['actors']}
        scale = {a['id']: a['scale'] for a in V['actors']}
        vig_need = Counter()
        for fi, fr in enumerate(V['frames']):
            for aid, A in fr['a'].items():
                ch = names.get(aid, aid)
                if ch.startswith('Extra'):
                    ch = 'Extra'
                jj = A['j']
                if jj[J['pelvis']] is None:
                    continue
                frames_by_char[ch] += 1
                sc = scale.get(aid, 1)
                tv, tm = view_of(P(A['fwd']) if False else _dirc(P, A['fwd']))
                hv, hm = view_of(_dirc(P, A['hfwd']))
                need = []
                for seg, (ja, jb, lk, vs) in SEGS.items():
                    a, b = jj[J[ja]], jj[J[jb]]
                    if a is None or b is None:
                        continue
                    L3 = math.dist(a, b)
                    pa, pb = P(a), P(b)
                    L2 = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
                    f = fore_of(L2 / L3 if L3 > 1e-6 else 1)
                    if seg == 'torso':
                        f = 'full' if f in ('full', 'mid') else f  # a torso leaning toward camera: bow pieces
                    v = hv if vs == 'head' else tv
                    m = hm if vs == 'head' else tm
                    if seg == 'head' or seg.startswith('foot'):
                        f = 'full'  # heads and feet are drawn per view; their projected length follows the view
                    base = seg.rstrip('LR') if seg not in ('head', 'torso') else seg
                    cells[ch][(base, v, f)] += 1
                    mirror[m] += 1
                    need.append((seg, v, f))
                for S in 'LR':
                    hands[ch][A['hand'][S] or 'relaxed'] += 1
                    kn = angle(jj[J['hip' + S]], jj[J['knee' + S]], jj[J['ankle' + S]])
                    off = min(jj[J['heel' + S]][1], jj[J['ball' + S]][1]) > 3
                    legs[ch]['knee ' + ('straight' if kn > 160 else 'bent' if kn > 110 else 'deep')] += 1
                    if off:
                        legs[ch]['foot off the floor'] += 1
                if A['up'][1] < .5:
                    legs[ch]['torso tipped > 60 deg (lying, falling, bowing low)'] += 1
                if A.get('face'):
                    faces[ch]['mouth ' + str(A['face']['mouth'])] += 1
                    faces[ch]['eyes ' + str(A['face']['eyes'])] += 1
                    if A['face']['open'] > .3:
                        faces[ch]['mouth open > .3'] += 1
                for wn, w in wards.items():
                    if w.get('body') not in (None, ch) and ch != 'Extra':
                        continue
                    c = cover[wn][ch]; c[0] += 1
                    miss = [(s, v, f) for (s, v, f) in need if not has(w, s, v, f)]
                    if not miss:
                        c[1] += 1
                    elif all(f == 'mid' and has(w, s, v, 'full') for (s, v, f) in miss):
                        c[2] += 1
                    for (s, v, f) in miss:
                        base = s.rstrip('LR') if s not in ('head', 'torso') else s
                        g = gaps[wn][(base, v, f)]; g['frames'] += 1
                        if len(g['examples']) < 4 and fi % 12 == 0:
                            g['examples'].append([V['id'], fi, names.get(aid, aid)])
                vig_need.update(set((s.rstrip('LR') if s not in ('head', 'torso') else s, v, f) for (s, v, f) in need))
        per_vig.append({'id': V['id'], 'title': V['title'], 'cells': len(vig_need), 'view': V['view']})
    out = {
        'about': 'Cut-out cells the Bolas motion bank asks for, per character, seen through each vignette\'s camera.',
        'frames_by_character': dict(frames_by_char),
        'cells': {ch: sorted([[s, v, f, n] for (s, v, f), n in c.items()], key=lambda r: -r[3]) for ch, c in cells.items()},
        'mirror_frames_pct': round(100 * mirror[True] / max(1, sum(mirror.values())), 1),
        'hands': {k: dict(v.most_common()) for k, v in hands.items()},
        'faces': {k: dict(v.most_common()) for k, v in faces.items()},
        'legs': {k: dict(v.most_common()) for k, v in legs.items()},
        'coverage': {wn: {ch: {'frames': c[0], 'fully_covered_pct': round(100 * c[1] / max(1, c[0]), 1),
                               'with_squash_pct': round(100 * (c[1] + c[2]) / max(1, c[0]), 1)} for ch, c in d.items()} for wn, d in cover.items()},
        'gaps': {wn: sorted([{'cell': list(k), 'frames': g['frames'], 'examples': g['examples']} for k, g in d.items()], key=lambda r: -r['frames'])[:40] for wn, d in gaps.items()},
        'vignettes': per_vig,
    }
    out['reshoot'] = reshoot(idx, J, wards)
    json.dump(out, open(os.path.join(HERE, 'demand.json'), 'w'), indent=1)
    open(os.path.join(HERE, 'demand.md'), 'w').write(to_md(out))
    print(json.dumps(out['coverage'], indent=1))


def frame_needs(P, A, J):
    jj = A['j']
    tv, _ = view_of(_dirc(P, A['fwd'])); hv, _ = view_of(_dirc(P, A['hfwd']))
    need = []
    for seg, (ja, jb, lk, vs) in SEGS.items():
        a, b = jj[J[ja]], jj[J[jb]]
        if a is None or b is None:
            continue
        L3 = math.dist(a, b); pa, pb = P(a), P(b)
        f = fore_of(math.hypot(pa[0] - pb[0], pa[1] - pb[1]) / L3 if L3 > 1e-6 else 1)
        if seg == 'torso':
            f = 'full' if f in ('full', 'mid') else f
        if seg == 'head' or seg.startswith('foot'):
            f = 'full'
        need.append((seg, hv if vs == 'head' else tv, f))
    return need


def reshoot(idx, J, wards, step=15):
    """Per vignette, the camera yaw (same elevation) that lets each wardrobe cover the most actor-frames.
    The motion is 3D, so the camera is a free choice: this is re-shooting instead of re-skinning."""
    res = {wn: {'native': [0, 0], 'best': [0, 0], 'per_vignette': {}} for wn in wards}
    for vmeta in idx['vignettes']:
        V = json.load(open(os.path.join(BANK, vmeta['id'] + '.json')))
        view = V['view'] or {}
        frames = [(A) for fr in V['frames'][::2] for A in fr['a'].values() if A['j'][J['pelvis']] is not None]
        for wn, w in wards.items():
            best = None
            for yaw in [view.get('yaw', -22)] + list(range(-180, 180, step)):
                P = cam(dict(view, yaw=yaw))
                ok = sum(1 for A in frames if all(has(w, sg, v, f) for (sg, v, f) in frame_needs(P, A, J)))
                if best is None:
                    native = ok
                if best is None or ok > best[1]:
                    best = (yaw, ok)
            r = res[wn]; r['native'][0] += native; r['native'][1] += len(frames); r['best'][0] += best[1]; r['best'][1] += len(frames)
            r['per_vignette'][V['id']] = {'native_pct': round(100 * native / max(1, len(frames)), 1), 'best_yaw': best[0], 'best_pct': round(100 * best[1] / max(1, len(frames)), 1)}
    for wn, r in res.items():
        r['native_pct'] = round(100 * r['native'][0] / max(1, r['native'][1]), 1)
        r['best_pct'] = round(100 * r['best'][0] / max(1, r['best'][1]), 1)
    return res


def _dirc(P, d):
    o = P((0, 0, 0)); q = P(d)
    return (q[0] - o[0], q[1] - o[1], q[2] - o[2])


def to_md(o):
    L = ['# Wardrobe demand: what a skin needs to wear the Bolas motion bank', '',
         'Generated by [wardrobe_demand.py](wardrobe_demand.py) from the baked Crash Lab vignettes in `bank/` (export with [export_bank.mjs](export_bank.mjs)). '
         'A *cell* is one cut-out piece: segment x view x foreshortening. Counts are actor-frames seen through each vignette\'s own camera.', '',
         'Frames per character: ' + ', '.join('%s %d' % kv for kv in sorted(o['frames_by_character'].items(), key=lambda kv: -kv[1])) + '.',
         'Parts facing screen-left (a flipped piece can serve): %s%% of part-frames.' % o['mirror_frames_pct'], '',
         '## Coverage of the wardrobes declared in `wardrobe/`', '',
         '| Wardrobe | Character | Actor-frames | Every part has a piece | Allowing squash of full pieces |', '| :-- | :-- | --: | --: | --: |']
    for wn, d in o['coverage'].items():
        for ch, c in sorted(d.items(), key=lambda kv: -kv[1]['frames']):
            L.append('| %s | %s | %d | %s%% | %s%% |' % (wn, ch, c['frames'], c['fully_covered_pct'], c['with_squash_pct']))
    L += ['', '## Re-shoot instead of re-skin', '',
          'The motions are 3D, so the camera can be chosen per vignette. For each wardrobe: coverage through the Crash Lab camera, and through the best yaw (15 deg steps, same elevation, every second frame, all characters).', '',
          '| Wardrobe | Crash Lab camera | Best camera per vignette |', '| :-- | --: | --: |']
    for wn, r in o['reshoot'].items():
        L.append('| %s | %s%% | %s%% |' % (wn, r['native_pct'], r['best_pct']))
    for wn, g in o['gaps'].items():
        L += ['', '### Missing cells for `%s`, by frames' % wn, '', '| Cell (segment, view, fore) | Actor-frames | Example frames (vignette, frame, who) |', '| :-- | --: | :-- |']
        for r in g[:20]:
            L.append('| %s | %d | %s |' % (' / '.join(r['cell']), r['frames'], '; '.join('%s f%d %s' % tuple(e) for e in r['examples'])))
    for ch in ('Bola', 'Shim', 'Dot'):
        if ch not in o['cells']:
            continue
        tot = sum(r[3] for r in o['cells'][ch] if r[0] == 'torso')
        L += ['', '## %s: cells asked for' % ch, '', 'Torso view across %d frames: ' % tot + ', '.join(
            '%s %d%%' % (v, round(100 * sum(r[3] for r in o['cells'][ch] if r[0] == 'torso' and r[1] == v) / max(1, tot))) for v in VIEWS) + '.', '',
              '| Segment | ' + ' | '.join(VIEWS) + ' |', '| :-- |' + ' --: |' * len(VIEWS)]
        for seg in ['head', 'torso', 'thigh', 'shin', 'foot', 'uarm', 'farm']:
            row = []
            for v in VIEWS:
                fs = {r[2]: r[3] for r in o['cells'][ch] if r[0] == seg and r[1] == v}
                row.append(' '.join('%s:%d' % (f[0], fs[f]) for f in FORES if f in fs) or '')
            L.append('| %s | %s |' % (seg, ' | '.join(row)))
        L += ['', 'Hands: ' + ', '.join('%s %d' % kv for kv in list(o['hands'][ch].items())[:10]) + '.',
              'Legs: ' + ', '.join('%s %d' % kv for kv in o['legs'][ch].items()) + '.',
              'Faces: ' + ', '.join('%s %d' % kv for kv in list(o['faces'].get(ch, {}).items())[:10]) + '.']
    L += ['', 'Fore codes in the tables: f = full, m = mid, s = short, e = end-on.']
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    main()
