"""Hands: clean, classify, sub-skeleton (wrist pivot, palm centre, knuckle line, fingertips, thumb tip, palm normal),
regularize onto the hand grid (384x384, wrist pivot at (192,72), wrist->hand axis pointing DOWN), review sheet.

    python3 shots/scion2/library2/tools/hands.py poet

Scale: the library's px_per_cm for hands is a per-card fit of A-B to 21 cm, which would stretch fists to the length
of open hands. So each cut sheet gets ONE scale, the median of its cards' px_per_cm. Hands cut together keep
their painted relative sizes.
"""
import math, os, re, sys
import numpy as np, cv2
from PIL import Image
import common as C
from brass import brass_blobs
import index as IX

PART = 'hand'
G = C.GRID[PART]
BONES = [('pivot', 'palm_centre'), ('knuckle_l', 'knuckle_r'), ('palm_centre', 'thumb_tip')]
PROPS = r'daisy|mic\b|mic-|pen\b|coin|cup\b|coffee|letter|page|stem|orb|sphere|star|phone|sunglasses|flower|blossom|journal|drawer|poppy|knob|door|table|hourglass|armful'
STATES = [('point', r'point'), ('fist', r'fist'), ('pinch', r'pinch'), ('grip', r'grip|grasp|hold'), ('cupped', r'cup|support|guiding'),
          ('peace', r'peace'), ('wave', r'wave'), ('claw', r'claw'), ('flat_push', r'flat|push'), ('palm_up', r'palm-up'),
          ('open', r'open|celebration|embrace|release|spread'), ('relaxed', r'relax|hand-only|^\d+$|hand-[lr]$|^[lr]$|part')]


def side_from_name(n):
    n = n.lower()
    if re.search(r'(^|[-_ .])(l|left)($|[-_ .])|left', n):
        return 'left'
    if re.search(r'(^|[-_ .])(r|right)($|[-_ .])|right', n):
        return 'right'
    return None


def tips_on_contour(mc, centre, L, knuckle_y):
    cs, _ = cv2.findContours(mc.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        return []
    c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
    d = np.linalg.norm(c - centre, axis=1)
    n = len(c)
    w = max(5, n // 40)
    tips = []
    for i in range(n):
        lo, hi = i - w, i + w
        idx = np.arange(lo, hi + 1) % n
        if d[i] < d[idx].max() or d[i] < 0.45 * L:
            continue
        p = c[i]
        if p[1] < knuckle_y - 0.25 * L and abs(p[0] - centre[0]) < 0.3 * L:
            continue          # the tab / wrist end, not a finger
        if all(np.linalg.norm(p - q) > 0.12 * L for q in tips):
            tips.append(p)
    return [list(map(float, t)) for t in tips]


def process(c, fx, s_sheet):
    rgba, removed = C.keep_main(C.load_rgba(c))
    m = C.mask_of(rgba)
    flags = ['cleaned'] if removed else []
    bl = brass_blobs(rgba)
    H, W = m.shape
    if fx.get('pivot'):
        pivot, psrc = list(map(float, fx['pivot'])), 'fixes.json'
    elif bl:
        b = max(bl, key=lambda b: b['r'])
        pivot, psrc = b['c'], 'brass eyelet on the wrist tab'
    else:
        pivot, psrc = list(map(float, c['A'])), 'library A point'
        flags.append('no_wrist_brad')
    ys, xs = np.nonzero(m)
    d = np.hypot(xs - pivot[0], ys - pivot[1])
    far = d > 0.3 * d.max()
    cen = np.array([xs[far].mean(), ys[far].mean()])
    axis = cen - np.array(pivot)
    rot = float(fx.get('rot', C.rot_to(axis, G['axis'])))
    s, ssrc = s_sheet
    if 'scale' in fx:
        s, ssrc = float(fx['scale']), 'fixes.json'
    M = C.similarity(pivot, G['pivot'], rot, s)
    can = C.warp(rgba, M, G['canvas'])
    mc = can[..., 3] > 128
    P = np.array(G['pivot'], float)
    cy, cx = np.nonzero(mc)
    if len(cy) == 0:
        return None
    L = float(cy.max() - P[1])
    # knuckle line: first row past 30 % of the length where the fingers separate (3+ runs); fists: 70 %
    knuckle_y, sep = None, False
    for y in range(int(P[1] + 0.3 * L), int(cy.max())):
        row = mc[y]
        runs = np.count_nonzero(np.diff(row.astype(np.int8)) == 1) + int(row[0])
        if runs >= 3:
            knuckle_y, sep = y - 0.06 * L, True
            break
    if knuckle_y is None:
        knuckle_y = P[1] + 0.7 * L
    band = (cy > P[1] + 0.25 * (knuckle_y - P[1])) & (cy < knuckle_y)
    palm = [float(cx[band].mean()), float(cy[band].mean())] if band.sum() > 20 else [float(P[0]), float(P[1] + 0.45 * L)]
    kr = np.where(mc[int(min(knuckle_y, mc.shape[0] - 1))])[0]
    kn_l = [float(kr[0] + 0.08 * np.ptp(kr)), float(knuckle_y)] if len(kr) else None
    kn_r = [float(kr[-1] - 0.08 * np.ptp(kr)), float(knuckle_y)] if len(kr) else None
    tips = tips_on_contour(mc, np.array(palm), L, knuckle_y)
    thumb = None
    if tips:
        ang = [abs(math.degrees(math.atan2(t[0] - palm[0], t[1] - palm[1]))) for t in tips]
        i = int(np.argmax(ang))
        if ang[i] > 35:
            thumb = tips[i]
    fingers = [t for t in tips if t is not thumb]
    kc = {'pivot': list(map(float, P)), 'palm_centre': palm, 'knuckle_l': kn_l, 'knuckle_r': kn_r}
    if thumb:
        kc['thumb_tip'] = thumb
    for i, t in enumerate(sorted(fingers, key=lambda t: t[0])[:5]):
        kc['tip_%d' % i] = t
    for k, v in fx.get('kp_canonical', {}).items():
        kc[k] = v
    Minv = cv2.invertAffineTransform(M)
    kp = {k: C.apply(Minv, v) for k, v in kc.items() if v}
    kc = {k: [round(v[0], 1), round(v[1], 1)] for k, v in kc.items() if v}
    # classification
    nm = c['id'].split('/')[-1].lower()
    lab = C.labels().get(c['id'], {})
    cls = {}
    st = next((k for k, pat in STATES if re.search(pat, nm)), None)
    cpose = c.get('clip', {}).get('pose')
    cls['state'] = (st, 0.75, 'card name') if st else (cpose or 'unknown', 0.4, 'CLIP pose (zero-shot)')
    # a prop actually painted on the card: large non-skin regions (white petals, black mic, green stem) past the tab
    hsv = cv2.cvtColor(can[..., :3], cv2.COLOR_RGB2HSV)
    body = mc.copy(); body[:int(P[1] + 0.15 * L)] = False
    hh, ss, vv = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    nonskin = body & (((ss < 45) & (vv > 150)) | (vv < 45) | ((hh > 35) & (hh < 100) & (ss > 60)))
    prop_frac = float(nonskin.sum() / max(1, body.sum()))
    pm = re.search(PROPS, nm)
    if prop_frac > 0.12:
        cls['state'] = ('holding_' + (pm.group(0).strip('-') if pm else 'prop'), 0.7, 'pixel: %.0f%% non-skin pixels in the hand (a painted prop); name: %s' % (100 * prop_frac, pm.group(0) if pm else '-'))
    elif pm:
        cls['grip_for'] = (pm.group(0).strip('-'), 0.7, 'card name; the prop is NOT on the card (%.0f%% non-skin)' % (100 * prop_frac))
    sd = side_from_name(nm)
    pn = 'palm' if re.search(r'palm', nm) else 'back' if re.search(r'back', nm) else None
    if pn:
        cls['palm_normal'] = (pn, 0.6, 'card name (the kit names are not always right)')
    else:
        cls['palm_normal'] = ('unknown', 0.2, 'not determined')
    wd = float(max(np.ptp(np.where(mc[y])[0]) for y in range(int(P[1] + 0.2 * L), int(cy.max())) if mc[y].any()))
    ratio = wd / max(1, L)
    if sd:
        cls['side'] = (sd, 0.8, 'card name')
    elif thumb and cls['palm_normal'][0] in ('palm', 'back'):
        thumb_left = thumb[0] < palm[0]
        right = thumb_left == (cls['palm_normal'][0] == 'palm')
        cls['side'] = ('right' if right else 'left', 0.5, 'derived: thumb on screen-%s with %s to camera, fingers down' % ('left' if thumb_left else 'right', cls['palm_normal'][0]))
    else:
        cls['side'] = ('unknown', 0.2, 'not determined')
    cls['view'] = ('edge' if ratio < 0.42 else 'front', 0.55, 'pixel: width/length %.2f (edge-on < 0.42)' % ratio)
    cls['facing'] = ('n/a', 1.0, 'hands: see palm_normal and side')
    for k in ('view', 'state', 'side', 'palm_normal', 'facing'):
        if k in fx:
            cls[k] = (fx[k], 0.95, 'fixes.json (agent-vision, card looked at)')
    if lab.get('bad'):
        flags.append('labels_bad')
    if str(cls['state'][0]).startswith('holding'):
        flags.append('prop')
    if max(H, W) < 180:
        flags.append('low_res')
    flags += fx.get('flags', [])
    tab_w = None
    row = mc[int(P[1])]
    if row.any():
        tab_w = float(np.ptp(np.where(row)[0]) + 1)
    widths = {'at_pivot': tab_w, 'max_hand': round(wd, 1), 'length': round(L, 1)}
    return dict(rgba=can, M=M, kp=kp, kc=kc, cls=cls, px={'width_over_length': round(ratio, 3), 'fingers_separate': sep, 'prop_frac': round(prop_frac, 3)},
                flags=sorted(set(flags)), removed=removed, scale=s, rot=rot, psrc=psrc, ssrc=ssrc, widths=widths)


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
    if 'jointed-hands' in c['id']:
        return 'jointed-hand sub-piece (palm plate / finger fan / thumb), not a whole hand: belongs to a hand-kit'
    rgba = C.load_rgba(c)
    bl = brass_blobs(rgba)
    if len(bl) >= 5:
        return 'whole figure or multi-part card (%d brads), not a single hand' % len(bl)
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
        r = process(c, fx, (C.CANON_PPC / med, 'sheet %s: median library px_per_cm %.2f over %d hands' % (sk, med, len(sheet_ppc.get(sk, [])))))
        if r is None:
            continue
        rec = IX.part_record(c, PART, r, C.CANON_PPC)
        rec['widths_px'] = r['widths']
        recs.append(rec)
        path = os.path.join(C.LIB2, rec['image'])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(r['rgba']).save(path, optimize=True)
        cl = rec['classes']
        bones = BONES + [('palm_centre', k) for k in rec['keypoints']['canonical'] if k.startswith('tip_')]
        lines = [c['id'].split('/')[-1][:40] + '  ' + c['id'].split('.')[1],
                 '%s  %s hand  %s' % (cl['state']['value'], cl['side']['value'], cl['palm_normal']['value']),
                 'view %s  L %.0f px  rot %+.0f' % (cl['view']['value'], r['widths']['length'], r['rot']),
                 'pivot: ' + r['psrc'][:36],
                 ','.join(rec['flags'])[:44]]
        tiles.append((cl['state']['value'], IX.tile(r['rgba'], PART, rec['keypoints']['canonical'], bones, lines)))
    tiles.sort(key=lambda t: str(t[0]))
    IX.merge(recs, ch, PART)
    sheets = C.sheet([t for _, t in tiles], os.path.join(C.LIB2, 'sheets', '%s_hand_%%02d.jpg' % ch), cols=6,
                     title='%s hands on the hand grid (384x384, wrist pivot red cross at 192,72, hand points down; grid 5 cm; %g px/cm)' % (ch, C.CANON_PPC))
    sheets += C.sheet(bad, os.path.join(C.LIB2, 'sheets', '%s_hand_rejected_%%02d.jpg' % ch), cols=6, title='%s hand cards rejected (reason under each)' % ch)
    print('\n'.join(sheets))


if __name__ == '__main__':
    for ch in sys.argv[1:]:
        run(ch)
