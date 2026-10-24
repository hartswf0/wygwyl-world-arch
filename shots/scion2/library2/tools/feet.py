"""Feet: clean, classify, sub-skeleton (ankle pivot, heel, toe tip, sole line), regularize onto the foot grid.

    python3 shots/scion2/library2/tools/feet.py poet

Foot grid: a 768x448 canvas with the ankle pivot at (384,112). The rotation makes the sole line horizontal, with the
sole down, so a foot stands on the grid. The toe points screen-right or screen-left, and that direction is the
recorded facing. Scale is the median library px_per_cm of the cut sheet, the same rule as for hands.
"""
import math, os, re, sys
import numpy as np, cv2
from PIL import Image
import common as C
from brass import brass_blobs
import index as IX

PART = 'foot'
G = C.GRID[PART]
BONES = [('pivot', 'heel'), ('pivot', 'toe'), ('sole_heel', 'sole_toe')]


def bottom_envelope(m):
    xs = np.where(m.any(0))[0]
    pts = []
    for x in xs:
        ys = np.where(m[:, x])[0]
        pts.append((x, ys[-1]))
    return np.array(pts, float)


def sole_angle(m):
    """angle (deg, screen-ccw) of the sole: a robust line through the lowest 30 % of the bottom envelope"""
    env = bottom_envelope(m)
    if len(env) < 10:
        return 0.0
    thr = np.percentile(env[:, 1], 60)
    low = env[env[:, 1] >= thr]
    if len(low) < 5:
        return 0.0
    k, b = np.polyfit(low[:, 0], low[:, 1], 1)
    return -math.degrees(math.atan(k))


def side_from_name(n):
    n = n.lower()
    if re.search(r'(^|[-_ .])(l|left)($|[-_ .])|foot-?l\b|footl|left', n):
        return 'left'
    if re.search(r'(^|[-_ .])(r|right)($|[-_ .])|foot-?r\b|footr|right', n):
        return 'right'
    return None


def process(c, fx, s_sheet):
    rgba, removed = C.keep_main(C.load_rgba(c))
    m = C.mask_of(rgba)
    flags = ['cleaned'] if removed else []
    H, W = m.shape
    bl = brass_blobs(rgba)
    top = [b for b in bl if b['c'][1] < 0.6 * H]
    if fx.get('pivot'):
        pivot, psrc = list(map(float, fx['pivot'])), 'fixes.json'
    elif top:
        b = max(top, key=lambda b: b['r'])
        pivot, psrc = b['c'], 'brass eyelet on the ankle tab'
    else:
        pivot, psrc = list(map(float, c['A'])), 'library A point'
        flags.append('no_ankle_brad')
    ang = float(fx.get('rot', -sole_angle(m)))
    s, ssrc = s_sheet
    if 'scale' in fx:
        s, ssrc = float(fx['scale']), 'fixes.json'
    M = C.similarity(pivot, G['pivot'], ang, s)
    can = C.warp(rgba, M, G['canvas'])
    mc = can[..., 3] > 128
    P = np.array(G['pivot'], float)
    ys, xs = np.nonzero(mc)
    if not len(ys):
        return None
    bot = ys.max()
    low = mc.copy(); low[:int(P[1] + 0.6 * (bot - P[1]))] = False
    ly, lx = np.nonzero(low)
    ext_r, ext_l = lx.max() - P[0], P[0] - lx.min()
    asym = (ext_r - ext_l) / max(1, ext_r + ext_l)
    nm = c['id'].split('/')[-1].lower()
    lab = C.labels().get(c['id'], {})
    libv = {'profile': 'side', 'threequarter': 'three-quarter'}.get(c.get('view'), c.get('view'))
    cls = {}
    if fx.get('view'):
        cls['view'] = (fx['view'], 0.95, 'fixes.json (agent-vision, card looked at)')
    elif abs(asym) > 0.12:
        cls['view'] = ('side', 0.75, 'pixel: sole extends %.0f%% more on one side of the ankle' % (100 * abs(asym)))
    elif libv:
        cls['view'] = (libv, 0.7, 'library.view')
    else:
        cls['view'] = ('front' if 'toe' not in nm else 'front', 0.4, 'pixel: symmetric about the ankle (front or back)')
    toe_right = asym > 0
    if cls['view'][0] in ('side', 'three-quarter'):
        cls['facing'] = ('screen-right' if toe_right else 'screen-left', min(0.95, 0.5 + abs(asym)), 'pixel: the toe side extends further from the ankle (asym %.2f)' % asym)
    else:
        cls['facing'] = ('camera' if cls['view'][0] == 'front' else 'away', 0.5, 'follows view')
    sd = side_from_name(nm)
    cls['side'] = (sd, 0.75, 'card name') if sd else ('unknown', 0.2, 'not in the name')
    upper = mc.copy(); upper[int(P[1]):] = False
    hgt = (bot - ys.min()) / max(1, lx.max() - lx.min())
    lacey = 'sneaker' if hgt < 0.62 and cls['view'][0] == 'side' else 'chelsea_boot'
    hsv = cv2.cvtColor(can[..., :3], cv2.COLOR_RGB2HSV)
    white = float(((hsv[..., 1] < 40) & (hsv[..., 2] > 170) & mc).sum() / max(1, mc.sum()))
    st = lacey + ('_white' if white > 0.3 else '')
    if re.search(r'heel-up|toe-up', nm):
        st += '_' + re.search(r'heel-up|toe-up', nm).group(0).replace('-', '_')
        flags.append('sole_visible')
    cls['state'] = (st, 0.6, 'pixel: height/length %.2f (sneaker < 0.62), white %.0f%%; name' % (hgt, 100 * white))
    for k in ('facing', 'side', 'state'):
        if k in fx:
            cls[k] = (fx[k], 0.95, 'fixes.json (agent-vision, card looked at)')
    # keypoints in canonical frame
    sgn = 1 if cls['facing'][0] != 'screen-left' else -1
    lowpts = np.stack([lx, ly], 1).astype(float)
    if cls['view'][0] in ('side', 'three-quarter'):
        toe = lowpts[np.argmax(sgn * lowpts[:, 0] - 0.2 * (bot - lowpts[:, 1]))]
        heel = lowpts[np.argmax(-sgn * lowpts[:, 0] - 0.2 * (bot - lowpts[:, 1]))]
    else:
        toe = np.array([P[0], bot], float)
        heel = None
    env = bottom_envelope(mc)
    sole = env[env[:, 1] >= bot - 0.04 * (bot - P[1])]
    kc = {'pivot': P.tolist(), 'toe': toe.tolist(), 'sole_heel': [float(sole[:, 0].min()), float(bot)] if sgn > 0 else [float(sole[:, 0].max()), float(bot)],
          'sole_toe': [float(sole[:, 0].max()), float(bot)] if sgn > 0 else [float(sole[:, 0].min()), float(bot)]}
    if heel is not None:
        kc['heel'] = heel.tolist()
    for k, v in fx.get('kp_canonical', {}).items():
        kc[k] = v
    kc = {k: [round(v[0], 1), round(v[1], 1)] for k, v in kc.items()}
    Minv = cv2.invertAffineTransform(M)
    kp = {k: C.apply(Minv, v) for k, v in kc.items()}
    if max(H, W) < 180:
        flags.append('low_res')
    if 'white' in st:
        flags.append('off_palette_white')
    flags += fx.get('flags', [])
    row = mc[int(P[1])]
    widths = {'ankle_tab_at_pivot': float(np.ptp(np.where(row)[0]) + 1) if row.any() else None,
              'length': float(lx.max() - lx.min()), 'height_pivot_to_sole': float(bot - P[1])}
    return dict(rgba=can, M=M, kp=kp, kc=kc, cls=cls, px={'toe_asym': round(float(asym), 3), 'height_over_length': round(float(hgt), 3), 'white': round(white, 3)},
                flags=sorted(set(flags)), removed=removed, scale=s, rot=ang, psrc=psrc, ssrc=ssrc, widths=widths)


def candidates(ch):
    lab, fxs = C.labels(), C.fixes()
    out = []
    for c in C.cards():
        if c['character'] != ch:
            continue
        refile = fxs.get(c['id'], {}).get('part') or lab.get(c['id'], {}).get('slot')
        if (c['slot'] == PART and (not (refile and refile != PART) or fxs.get(c['id'], {}).get('reject'))) or refile == PART:
            out.append(c)
    return out


def auto_reject(c, fx):
    if fx.get('reject'):
        return fx['reject']
    lab = C.labels().get(c['id'], {})
    if lab.get('bad'):
        return 'labels.json: ' + lab.get('note', 'bad')
    if c.get('state') in ('uncut_pair',):
        return 'an uncut pair (two feet on one card)'
    bl = brass_blobs(C.load_rgba(c))
    if len(bl) >= 5:
        return 'whole figure or multi-part card (%d brads), not a single foot' % len(bl)
    return None


def run(ch):
    fxs = C.fixes()
    cands = candidates(ch)
    sheet_ppc = {}
    for c in cands:
        if c.get('px_per_cm') and not auto_reject(c, fxs.get(c['id'], {})):
            sheet_ppc.setdefault(c['id'].split('/')[0], []).append(c['px_per_cm'])
    recs, tiles, bad = [], [], []
    for c in cands:
        fx = fxs.get(c['id'], {})
        why = auto_reject(c, fx)
        if why:
            recs.append(IX.reject_record(c, PART, why, fx.get('refile')))
            bad.append(IX.reject_tile(C.load_rgba(c), c, why))
            continue
        sk = c['id'].split('/')[0]
        med = float(np.median(sheet_ppc[sk])) if sk in sheet_ppc else (c.get('px_per_cm') or 10)
        r = process(c, fx, (C.CANON_PPC / med, 'sheet %s: median library px_per_cm %.2f over %d feet' % (sk, med, len(sheet_ppc.get(sk, [])))))
        if r is None:
            continue
        rec = IX.part_record(c, PART, r, C.CANON_PPC)
        rec['widths_px'] = r['widths']
        recs.append(rec)
        path = os.path.join(C.LIB2, rec['image'])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(r['rgba']).save(path, optimize=True)
        cl = rec['classes']
        lines = [c['id'].split('/')[-1][:40] + '  ' + c['id'].split('.')[1],
                 '%s  %s  %s foot' % (cl['view']['value'], cl['facing']['value'], cl['side']['value']),
                 '%s  rot %+.0f  len %.0f px' % (cl['state']['value'], r['rot'], r['widths']['length']),
                 'pivot: ' + r['psrc'][:36],
                 ','.join(rec['flags'])[:44]]
        tiles.append((cl['view']['value'] + cl['facing']['value'], IX.tile(r['rgba'], PART, rec['keypoints']['canonical'], BONES, lines)))
    tiles.sort(key=lambda t: t[0])
    IX.merge(recs, ch, PART)
    sheets = C.sheet([t for _, t in tiles], os.path.join(C.LIB2, 'sheets', '%s_foot_%%02d.jpg' % ch), cols=6,
                     title='%s feet on the foot grid (768x448, ankle pivot red cross at 384,112, sole horizontal; grid 5 cm; %g px/cm)' % (ch, C.CANON_PPC))
    sheets += C.sheet(bad, os.path.join(C.LIB2, 'sheets', '%s_foot_rejected_%%02d.jpg' % ch), cols=6, title='%s foot cards rejected (reason under each)' % ch)
    print('\n'.join(sheets))


if __name__ == '__main__':
    for ch in sys.argv[1:]:
        run(ch)
