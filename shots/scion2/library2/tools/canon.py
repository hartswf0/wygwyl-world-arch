"""Proportion canon per character/costume, measured from the painted whole-figure references with the Pose Lab
markers (shots/rig/poses/<char>__<costume>.json), and each regularized part's deviation from it.

    python3 shots/scion2/library2/tools/canon.py            # every pose file -> library2/canon.json, deviations -> index.json

Segment lengths (cm): the 2D distance between markers, converted with the solve's scale (best solve
scale_px_per_cm, else the sheet's scale prior). Foreshortening only shortens a segment in 2D, so the canon value is
the 75th percentile over the figures, not the median. The median and the inter-quartile spread are recorded next
to it.
- head: the Pose Lab skeleton's head length. The chin -> head markers stop short of the crown, so they are kept
  as head_markers.
- torso: neck -> groin.
- pelvis (width): hipL -> hipR.
- upper_arm: shoulder -> elbow.
- forearm: elbow -> wrist.
- thigh: hip -> knee.
- shin: knee -> ankle.
- foot: ankle -> toe.
- hand: there is no fingertip marker, so the Pose Lab skeleton's hand length is used.

Joint widths (cm): the silhouette width of the painted figure across the bone at the joint marker. Overlapping
limbs and the torso behind an arm only inflate it, so the canon is the 25th percentile; the median and the
inter-quartile range are recorded too. Only figures with a confident solve (score >= 0.5) count.
- neck: across chin->neck, half way.
- shoulder: across shoulder->elbow, 15 % down the bone.
- elbow and wrist: across elbow->wrist, at each end.
- waist: across neck->groin, at 75 % of the way down.
- hip: across hip->knee, 10 % down.
- knee: across hip->knee, at the knee.
- ankle: across knee->ankle, at the ankle.
"""
import json, math, os, sys
import numpy as np
from PIL import Image
import common as C

POSES = os.path.join(C.SHOTS, 'rig', 'poses')
SEG = {'head': ('chin', 'head'), 'torso': ('neck', 'groin'), 'pelvis_width': ('hipL', 'hipR'),
       'upper_arm': [('shoulderL', 'elbowL'), ('shoulderR', 'elbowR')], 'forearm': [('elbowL', 'wristL'), ('elbowR', 'wristR')],
       'thigh': [('hipL', 'kneeL'), ('hipR', 'kneeR')], 'shin': [('kneeL', 'ankleL'), ('kneeR', 'ankleR')], 'foot': [('ankleL', 'toeL'), ('ankleR', 'toeR')]}
# joint -> list of (point marker, bone a, bone b, t along bone where to measure)
JW = {'neck': [('neck', 'chin', 'neck', 0.5)],
      'shoulder': [('shoulderL', 'shoulderL', 'elbowL', 0.15), ('shoulderR', 'shoulderR', 'elbowR', 0.15)],
      'elbow': [('elbowL', 'elbowL', 'wristL', 0.0), ('elbowR', 'elbowR', 'wristR', 0.0)],
      'wrist': [('wristL', 'elbowL', 'wristL', 1.0), ('wristR', 'elbowR', 'wristR', 1.0)],
      'waist': [('neck', 'neck', 'groin', 0.75)],
      'hip': [('hipL', 'hipL', 'kneeL', 0.1), ('hipR', 'hipR', 'kneeR', 0.1)],
      'knee': [('kneeL', 'hipL', 'kneeL', 1.0), ('kneeR', 'hipR', 'kneeR', 1.0)],
      'ankle': [('ankleL', 'kneeL', 'ankleL', 1.0), ('ankleR', 'kneeR', 'ankleR', 1.0)]}


def best_scale(t, stature=None):
    sol = [s for s in t.get('solves') or [] if s.get('scale_px_per_cm')]
    if sol:
        s = max(sol, key=lambda s: s.get('score', 0))
        return s['scale_px_per_cm'], s.get('score', 0)
    sp = (t.get('scale_prior') or {}).get('px_per_cm')
    if sp:
        return sp, 0.0
    # no solve: the figure's painted height (floor - top) over the stature; only standing figures are this tall,
    # so this under-estimates the scale of bent poses (their segments come out long -> they drop out of the p75)
    if stature and t.get('bbox') and t.get('floor'):
        return (t['floor'] - t['bbox'][1]) / stature, 0.5
    return None, 0.0


def width_across(mask, a, b, t):
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    n = np.linalg.norm(d)
    if n < 1:
        return None
    u = d / n
    v = np.array([-u[1], u[0]])
    c = a + d * t
    H, W = mask.shape
    if not (0 <= int(c[0]) < W and 0 <= int(c[1]) < H) or not mask[int(c[1]), int(c[0])]:
        return None
    w = 0
    for sgn in (1, -1):
        k = 0
        while k < 4000:
            q = c + v * sgn * (k + 1)
            x, y = int(round(q[0])), int(round(q[1]))
            if not (0 <= x < W and 0 <= y < H) or not mask[y, x]:
                break
            k += 1
        w += k
    return float(w + 1)


def stats(vals, q=75):
    v = np.array([x for x in vals if x and np.isfinite(x)], float)
    if len(v) < 2:
        return None
    return {'canon': round(float(np.percentile(v, q)), 1), 'median': round(float(np.median(v)), 1),
            'iqr': [round(float(np.percentile(v, 25)), 1), round(float(np.percentile(v, 75)), 1)], 'n': int(len(v))}


def measure(path):
    D = C.load_json(path)
    segs = {k: [] for k in SEG}
    wid = {k: [] for k in JW}
    for t in D.get('targets', []):
        m = t.get('markers') or {}
        sc, score = best_scale(t, D.get('stature_cm') or C.height_cm((D.get('character') or '').split('/')[0] if isinstance(D.get('character'), str) else ''))
        if not sc or not m:
            continue
        P = {k: v[:2] for k, v in m.items() if isinstance(v, list) and len(v) >= 2}
        for k, spec in SEG.items():
            pairs = spec if isinstance(spec, list) else [spec]
            for a, b in pairs:
                if a in P and b in P:
                    segs[k].append(math.dist(P[a], P[b]) / sc)
        if score < 0.5:
            continue
        ip = os.path.join(C.SHOTS, t['img'])
        if not os.path.exists(ip):
            continue
        mask = np.array(Image.open(ip).convert('RGBA'))[..., 3] > 100
        for k, specs in JW.items():
            for pt, a, b, tt in specs:
                if a in P and b in P:
                    w = width_across(mask, P[a], P[b], tt)
                    if w:
                        wid[k].append(w / sc)
    out = {'segments_cm': {k: stats(v) for k, v in segs.items()},
           'joint_widths_cm': {k: stats(v, 25) for k, v in wid.items()},
           'stature_cm': D.get('stature_cm'), 'skeleton_hand_cm': (D.get('skeleton') or {}).get('handL'),
           'n_figures': len(D.get('targets', [])), 'source': os.path.relpath(path, C.REPO)}
    sk = D.get('skeleton') or {}
    if sk.get('head'):
        out['segments_cm']['head_markers'] = out['segments_cm']['head']
        out['segments_cm']['head'] = {'canon': round(sk['head'], 1), 'median': None, 'iqr': None, 'n': 0,
                                      'source': 'Pose Lab skeleton head (the chin->head markers stop short of the crown: see head_markers)'}
    if out['skeleton_hand_cm']:
        out['segments_cm']['hand'] = {'canon': round(out['skeleton_hand_cm'], 1), 'median': None, 'iqr': None, 'n': 0, 'source': 'Pose Lab skeleton handL'}
    return out


# part -> (canon segment, the part's own length in canonical px)
PART_SEG = {'head': 'head', 'torso': 'torso', 'upper_arm': 'upper_arm', 'forearm': 'forearm', 'thigh': 'thigh', 'shin': 'shin', 'hand': 'hand', 'foot': 'foot'}
PART_W = {'head': [('neck', 'neck_at_pivot')], 'torso': [('waist', 'waist'), ('neck', 'neck')], 'upper_arm': [('shoulder', 'shoulder'), ('elbow', 'elbow')],
          'forearm': [('elbow', 'elbow'), ('wrist', 'wrist')], 'thigh': [('hip', 'hip'), ('knee', 'knee')], 'shin': [('knee', 'knee'), ('ankle', 'ankle')],
          'hand': [('wrist', 'at_pivot')], 'foot': [('ankle', 'ankle_tab_at_pivot')]}


def part_length_cm(rec):
    k = rec['keypoints']['canonical']
    p = rec['part']
    if p == 'head' and k.get('crown') and k.get('chin'):
        return math.dist(k['crown'], k['chin']) / C.CANON_PPC
    if p == 'hand':
        return (rec.get('widths_px') or {}).get('length', 0) / C.CANON_PPC
    if p == 'foot':
        return (rec.get('widths_px') or {}).get('length', 0) / C.CANON_PPC
    tip = C.GRID[p]['tip_name'] if p != 'torso' else 'neck'
    if k.get(tip):
        return math.dist(k['pivot'], k[tip]) / C.CANON_PPC
    return None


def main():
    canon = {'about': __doc__.strip().split('\n\n')[0], 'method': 'see tools/canon.py docstring', 'characters': {}}
    for fn in sorted(os.listdir(POSES)):
        if not fn.endswith('.json') or '.' in fn[:-5] or '__' not in fn:
            continue
        key = fn[:-5].replace('__', '/')
        try:
            canon['characters'][key] = measure(os.path.join(POSES, fn))
        except Exception as e:
            canon['characters'][key] = {'error': str(e)}
    with open(os.path.join(C.LIB2, 'canon.json'), 'w') as f:
        json.dump(canon, f, indent=1)
    # deviations into index.json
    idx = C.load_json(os.path.join(C.LIB2, 'index.json'))
    n = 0
    for rec in idx['parts'].values():
        if rec.get('status') != 'ok':
            continue
        ck = '%s/%s' % (rec['character'], rec.get('costume'))
        cn = canon['characters'].get(ck) or next((v for k, v in canon['characters'].items() if k.startswith(rec['character'] + '/') and 'error' not in v), None)
        if not cn or 'error' in cn:
            rec['canon_deviation'] = None
            continue
        dev = {'canon': ck if ck in canon['characters'] else 'nearest costume of ' + rec['character']}
        seg = PART_SEG.get(rec['part'])
        L = part_length_cm(rec)
        cs = (cn['segments_cm'].get(seg) or {}) if seg else {}
        if L and cs.get('canon'):
            dev['length_cm'] = round(L, 1)
            dev['canon_length_cm'] = cs['canon']
            dev['length_ratio'] = round(L / cs['canon'], 3)
        wd = rec.get('widths_px') or {}
        for jn, wk in PART_W.get(rec['part'], []):
            cw = (cn['joint_widths_cm'].get(jn) or {})
            if wd.get(wk) and cw.get('canon'):
                dev['width_%s_ratio' % jn] = round(wd[wk] / C.CANON_PPC / cw['canon'], 3)
        rec['canon_deviation'] = dev
        n += 1
    with open(os.path.join(C.LIB2, 'index.json'), 'w') as f:
        json.dump(idx, f, indent=1)
    print('canon for', len(canon['characters']), 'character/costumes; deviations on', n, 'parts')


if __name__ == '__main__':
    main()
