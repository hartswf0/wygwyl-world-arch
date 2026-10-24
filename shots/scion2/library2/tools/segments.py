"""Torso / pelvis / limb segments: clean, classify, joint pivots from the brass brads, regularize, sheet.

    python3 shots/scion2/library2/tools/segments.py poet torso [pelvis upper_arm ...]

Joint pivots are the brass brads/eyelets (tools/brass.py); the card's A/B points are the fallback. Scale is the
library's sheet px_per_cm (one value per cut sheet, so parts cut together keep their painted relative sizes).
"""
import math, os, sys
import numpy as np, cv2
from PIL import Image
import common as C
from brass import brass_blobs
import index as IX

VIEWMAP = {'threequarter': 'three-quarter', 'profile': 'side', 'threequarter_back': 'three-quarter-back'}
BONES = {
    'torso': [('pivot', 'neck'), ('shoulder_l', 'shoulder_r'), ('neck', 'shoulder_l'), ('neck', 'shoulder_r')],
    'upper_arm': [('pivot', 'elbow')], 'forearm': [('pivot', 'wrist')], 'thigh': [('pivot', 'knee')], 'shin': [('pivot', 'ankle')],
    'pelvis': [('pivot', 'hip_mid'), ('hip_l', 'hip_r')],
}


def widths_along(m, p0, p1, ts=(0.0, 0.5, 1.0)):
    """outline width perpendicular to p0->p1 at fractions ts (card px)"""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    n = np.linalg.norm(d) or 1
    u = d / n
    v = np.array([-u[1], u[0]])
    H, W = m.shape
    out = []
    for t in ts:
        c = p0 + d * t
        w = 0
        for sgn in (1, -1):
            k = 0
            while True:
                q = c + v * sgn * (k + 1)
                x, y = int(round(q[0])), int(round(q[1]))
                if not (0 <= x < W and 0 <= y < H) or not m[y, x]:
                    break
                k += 1
            w += k
        out.append(float(w + 1))
    return out


def zip_offset(rgba, m, waist, neck):
    """screen-x offset of the zip (a narrow grey run, row by row) from the outline's mid-line, as a fraction of width"""
    hsv = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2HSV)
    S, V = hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    lo, hi = sorted([waist[1], neck[1]])
    y0, y1 = int(lo + 0.2 * (hi - lo)), int(hi - 0.15 * (hi - lo))
    found, offs = 0, []
    for y in range(max(0, y0), min(m.shape[0], y1)):
        xs = np.where(m[y])[0]
        if len(xs) < 10:
            continue
        wd = xs[-1] - xs[0]
        g = m[y] & (S[y] < 45) & (V[y] > 85) & (V[y] < 215)
        gx = np.where(g[xs[0] + int(0.12 * wd): xs[-1] - int(0.12 * wd)])[0]
        if 0 < len(gx) <= max(3, 0.06 * wd):
            found += 1
            offs.append((xs[0] + int(0.12 * wd) + np.median(gx) - (xs[0] + xs[-1]) / 2) / wd)
    if found < 0.3 * max(1, y1 - y0):
        return None
    return float(np.median(offs))


def neck_offset(m, waist, neck):
    """neck pivot x against the outline mid-line at shoulder height (3/4 views turn the neck toward the facing side)"""
    y = int(neck[1] + 0.25 * (waist[1] - neck[1]))
    xs = np.where(m[min(max(y, 0), m.shape[0] - 1)])[0]
    if len(xs) < 5:
        return 0.0
    return float((neck[0] - (xs[0] + xs[-1]) / 2) / max(1, xs[-1] - xs[0]))


def torso_points(c, rgba, m, fx):
    H, W = m.shape
    bl = brass_blobs(rgba)
    ys = np.where(m.any(1))[0]
    xs = np.where(m.any(0))[0]
    top, bot = ys[0], ys[-1]
    hgt = bot - top
    src = {}
    lowb = [b for b in bl if b['c'][1] > top + 0.75 * hgt]
    if fx.get('pivot'):
        waist, src['pivot'] = fx['pivot'], 'fixes.json'
    elif lowb:
        b = min(lowb, key=lambda b: abs(b['c'][0] - (xs[0] + xs[-1]) / 2) - 0.1 * b['c'][1])
        if abs(b['c'][0] - (xs[0] + xs[-1]) / 2) > 0.25 * (xs[-1] - xs[0]):      # only a hem-corner brad: not the waist
            row = np.where(m[bot - 2])[0]
            waist, src['pivot'] = [float(row.mean()), float(bot - 0.04 * hgt)], 'bottom centre of the outline (the low brads are at the hem corners)'
        else:
            waist, src['pivot'] = b['c'], 'brass brad at the waist'
    else:
        row = np.where(m[bot - 2])[0]
        waist, src['pivot'] = [float(row.mean()), float(bot - 0.04 * hgt)], 'bottom centre of the outline'
    topb = [b for b in bl if b['c'][1] < top + 0.2 * hgt and abs(b['c'][0] - waist[0]) < 0.3 * (xs[-1] - xs[0])]
    if fx.get('neck'):
        neck, src['neck'] = fx['neck'], 'fixes.json'
    elif topb:
        b = min(topb, key=lambda b: b['c'][1])
        neck, src['neck'] = b['c'], 'brass brad at the neck'
    else:
        band = [y for y in range(top, top + max(3, int(0.03 * hgt)))]
        cx = float(np.mean([np.where(m[y])[0].mean() for y in band if m[y].any()]))
        neck, src['neck'] = [cx, float(top + 0.04 * hgt)], 'top centre of the collar'
    sh = [b for b in bl if top + 0.05 * hgt < b['c'][1] < top + 0.45 * hgt and b['c'] != neck]
    left = [b for b in sh if b['c'][0] < neck[0] - 0.12 * (xs[-1] - xs[0])]
    right = [b for b in sh if b['c'][0] > neck[0] + 0.12 * (xs[-1] - xs[0])]
    kp = {'pivot': list(map(float, waist)), 'neck': list(map(float, neck))}
    if left:
        kp['shoulder_l'] = min(left, key=lambda b: b['c'][0])['c']; src['shoulder_l'] = 'brass brad'
    if right:
        kp['shoulder_r'] = max(right, key=lambda b: b['c'][0])['c']; src['shoulder_r'] = 'brass brad'
    # side views: a single shoulder brad in the middle (the near arm socket)
    if not left and not right:
        mid = [b for b in sh if abs(b['c'][0] - neck[0]) <= 0.4 * (xs[-1] - xs[0])]
        if mid:
            kp['shoulder'] = max(mid, key=lambda b: b['r'])['c']; src['shoulder'] = 'brass brad (near shoulder)'
    for k in ('shoulder_l', 'shoulder_r', 'shoulder'):
        if k in fx:
            kp[k] = fx[k]; src[k] = 'fixes.json'
    return kp, src, bl


def classify_torso(c, rgba, m, kp):
    lab = C.labels().get(c['id'], {})
    out = {}
    libv = VIEWMAP.get(c.get('view'), c.get('view'))
    nm = c['id'].split('/')[-1]
    from_name = None
    for v, pat in (('three-quarter-back', 'threequarter-back|rear-3-4'), ('three-quarter', 'threequarter|three-quarter'),
                   ('side', 'profile'), ('back', 'back|rear'), ('front', 'front')):
        import re
        if re.search(pat, nm):
            from_name = v
            break
    zo = zip_offset(rgba, m, kp['pivot'], kp['neck'])
    if libv:
        out['view'] = (libv, 0.8, 'library.view (sheet caption)')
    elif lab.get('view'):
        out['view'] = (lab['view'], 0.75, 'labels.json (agent-vision)')
    elif from_name:
        out['view'] = (from_name, 0.7, 'card name')
    elif zo is not None:
        out['view'] = ('front' if abs(zo) < 0.08 else 'three-quarter' if abs(zo) < 0.3 else 'side', 0.5, 'pixel: zip offset %.2f' % zo)
    else:
        cv = c.get('clip', {}).get('view_l')
        out['view'] = ({'side': 'side'}.get(cv, cv) or 'front', 0.4, 'CLIP view (weak)')
    v = out['view'][0]
    if v == 'front':
        out['facing'] = ('camera', 0.8, 'follows view')
    elif v == 'back':
        out['facing'] = ('away', 0.8, 'follows view')
    elif 'left' in lab:
        out['facing'] = ('screen-left' if lab['left'] else 'screen-right', 0.85, 'labels.json (agent-vision)')
    elif zo is not None and abs(zo) > 0.04:
        out['facing'] = ('screen-right' if zo > 0 else 'screen-left', min(0.9, 0.5 + abs(zo)), 'pixel: zip line is %s of centre (%.2f)' % ('right' if zo > 0 else 'left', zo))
    elif abs(no := neck_offset(m, kp['pivot'], kp['neck'])) > 0.04:
        f = 'screen-right' if no > 0 else 'screen-left'
        if v == 'three-quarter-back':
            f = 'screen-left' if no > 0 else 'screen-right'
        out['facing'] = (f, min(0.8, 0.45 + abs(no)), 'pixel: neck sits %s of centre (%.2f)' % ('right' if no > 0 else 'left', no))
    else:
        out['facing'] = ('unknown', 0.2, 'no zip line found; needs a look')
    return out, zo


def limb_points(c, rgba, m, fx, part):
    """proximal pivot and distal tip: the brass brads nearest the card's A (proximal) and B (distal) points"""
    tipk = C.GRID[part]['tip_name']
    bl = brass_blobs(rgba)
    src = {}
    A, B = np.array(c['A'], float), np.array(c['B'], float)
    L = float(np.linalg.norm(B - A)) or 1.0
    kp = {}
    for k, ref in (('pivot', A), (tipk, B)):
        near = [b for b in bl if np.linalg.norm(np.array(b['c']) - ref) < 0.3 * L]
        if k in fx:
            kp[k], src[k] = list(map(float, fx[k])), 'fixes.json'
        elif near:
            b = min(near, key=lambda b: np.linalg.norm(np.array(b['c']) - ref))
            kp[k], src[k] = b['c'], 'brass brad nearest the library %s point' % ('A' if k == 'pivot' else 'B')
        else:
            kp[k], src[k] = list(map(float, ref)), 'library %s point' % ('A' if k == 'pivot' else 'B')
    if 'pivot' in fx and tipk in fx:
        pass
    return kp, src, bl


def pelvis_points(c, rgba, m, fx):
    """waist brad (the one nearest the outline's centre-line) + the two hip brads; hip_mid between them"""
    bl = brass_blobs(rgba)
    big = [b for b in bl if b['r'] >= 0.5 * max([x['r'] for x in bl] or [1])]
    ys, xs = np.nonzero(m)
    cx, cy = (xs.min() + xs.max()) / 2, ys.mean()
    hgt = ys.max() - ys.min()
    src, kp = {}, {}
    if len(big) >= 3:
        w = min(big, key=lambda b: abs(b['c'][0] - cx) - 0.01 * b['r'])
        rest = [b for b in big if b is not w]
        pair = max(((a, b) for i, a in enumerate(rest) for b in rest[i + 1:]), key=lambda ab: math.dist(ab[0]['c'], ab[1]['c']))
        hl, hr = sorted(pair, key=lambda b: b['c'][0])
        kp = {'pivot': w['c'], 'hip_l': hl['c'], 'hip_r': hr['c']}
        mid = [(hl['c'][0] + hr['c'][0]) / 2, (hl['c'][1] + hr['c'][1]) / 2]
        src = {'pivot': 'brass brad (waist, nearest the centre-line)', 'hip_l': 'brass brad', 'hip_r': 'brass brad'}
        if math.dist(mid, w['c']) < 0.15 * hgt:
            # three brads in a row (a waist strip): the bone runs from the waist toward the outline's mass
            d = np.array([cx, cy]) - np.array(w['c'])
            d = d / (np.linalg.norm(d) or 1)
            mid = list(np.array(w['c']) + d * 0.3 * hgt) if np.linalg.norm(d) else [w['c'][0], w['c'][1] + 0.3 * hgt]
            src['hip_mid'] = 'estimated: brads in a row'
        else:
            src['hip_mid'] = 'midpoint of the hip brads'
        kp['hip_mid'] = list(map(float, mid))
    elif len(big) == 2:
        a, b = sorted(big, key=lambda b: b['c'][1])
        kp = {'pivot': a['c'], 'hip_mid': b['c']}
        src = {'pivot': 'brass brad (upper)', 'hip_mid': 'brass brad (lower)'}
    else:
        kp = {'pivot': list(map(float, c['A'])), 'hip_mid': list(map(float, c['B']))}
        src = {'pivot': 'library A point', 'hip_mid': 'library B point'}
    for k in ('pivot', 'hip_mid', 'hip_l', 'hip_r'):
        if k in fx:
            kp[k], src[k] = list(map(float, fx[k])), 'fixes.json'
    return kp, src, bl


def classify_limb(c, rgba, m, kp, part):
    import re
    lab = C.labels().get(c['id'], {})
    nm = c['id'].split('/')[-1].lower()
    out = {}
    libv = VIEWMAP.get(c.get('view'), c.get('view'))
    if libv:
        out['view'] = (libv, 0.75, 'library.view (sheet caption)')
    elif lab.get('view'):
        out['view'] = (lab['view'], 0.75, 'labels.json (agent-vision)')
    elif (c.get('clip') or {}).get('view_l'):
        cv = c['clip']
        out['view'] = (cv['view_l'], round(0.7 * cv.get('view_l_p', 0.5), 2), 'CLIP view classifier learnt on the labelled cards (view_l p=%.2f)' % cv.get('view_l_p', 0))
    else:
        out['view'] = ('unknown', 0.2, 'limbs: not determined from pixels')
    if 'left' in lab:
        out['facing'] = ('screen-left' if lab['left'] else 'screen-right', 0.8, 'labels.json (agent-vision)')
    elif out['view'][0] == 'front':
        out['facing'] = ('camera', 0.6, 'follows view')
    elif out['view'][0] == 'back':
        out['facing'] = ('away', 0.6, 'follows view')
    else:
        out['facing'] = ('unknown', 0.2, 'side-view limb: screen direction not determined')
    if re.search(r'(^|[-_ .])(l|left)($|[-_ .])|-l-|left', nm):
        out['side'] = ('left', 0.75, 'card name')
    elif re.search(r'(^|[-_ .])(r|right)($|[-_ .])|-r-|right', nm):
        out['side'] = ('right', 0.75, 'card name')
    else:
        out['side'] = ('unknown', 0.2, 'not in the name')
    hsv = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2HSV)
    V, S = hsv[..., 2], hsv[..., 1]
    dark = float(((V < 60) & m).sum() / max(1, m.sum()))
    white = float(((S < 40) & (V > 170) & m).sum() / max(1, m.sum()))
    st = 'empty_sleeve' if 'empty' in nm else 'wrist_socket' if 'socket' in nm else 'sleeved' if dark > 0.35 else 'white_sleeve' if white > 0.35 else 'bare_skin'
    out['state'] = (st, 0.7, 'card name / pixel: %.0f%% dark cloth, %.0f%% white cloth' % (100 * dark, 100 * white))
    return out, None


def process(c, part, fx):
    rgba, removed = C.keep_main(C.load_rgba(c))
    m = C.mask_of(rgba)
    flags = ['cleaned'] if removed else []
    tipk = TIPK(part)
    if part == 'torso':
        kp, src, bl = torso_points(c, rgba, m, fx)
        rgba, cap = C.cut_bottom_caption(rgba, max(kp['pivot'][1], kp['neck'][1]) + 0.01 * m.shape[0], narrow_rule=True)
        if cap:
            removed.append(cap); flags += ['cleaned', 'caption_removed']; m = C.mask_of(rgba)
        cls, zo = classify_torso(c, rgba, m, kp)
    elif part == 'pelvis':
        kp, src, bl = pelvis_points(c, rgba, m, fx)
        cls, zo = classify_limb(c, rgba, m, kp, part)
        cls['state'] = ('connector_plate' if 'connector' in c['id'] else 'hip_bridge' if 'bridge' in c['id'] else 'waist_link' if 'link' in c['id'] else cls['state'][0],
                        0.7, 'card name')
        if 'estimated' in src.get('hip_mid', ''):
            flags.append('brads_in_a_row')
    else:
        kp, src, bl = limb_points(c, rgba, m, fx, part)
        rgba, cap = C.cut_bottom_caption(rgba, max(kp['pivot'][1], kp[tipk][1]) + 0.01 * m.shape[0], narrow_rule=True)
        if cap:
            removed.append(cap); flags += ['cleaned', 'caption_removed']; m = C.mask_of(rgba)
        cls, zo = classify_limb(c, rgba, m, kp, part)
    for k in ('view', 'facing', 'state', 'side'):
        if k in fx:
            cls[k] = (fx[k], 0.95, 'fixes.json (agent-vision, card looked at)')
    if 'state' not in cls:
        hsv = cv2.cvtColor(rgba[..., :3], cv2.COLOR_RGB2HSV)
        holes = 'hollow' in c['id']
        co = (c.get('costume') or '').lower()
        cls['state'] = ('hollow_chest' if holes else 'jacket' if (co == 'red_black_sunglasses' or 'jacket' in co or 'suit' in co) else 'tshirt' if 'tshirt' in co else co or 'unknown',
                        0.6, 'costume / card name')
    g = C.GRID[part]
    axis = np.array(kp[tipk]) - np.array(kp['pivot'])
    rot = float(fx.get('rot', C.rot_to(axis, g['axis'])))
    D = math.dist(kp['pivot'], kp[tipk])
    Lcm = KIT_LEN.get((c['character'], part))
    if Lcm:
        s = Lcm * C.CANON_PPC / max(5.0, D)
        ssrc = 'pivot->%s = %.1f cm (median kit length for %s %s)' % (tipk, Lcm, c['character'], part)
    else:
        ppc = c.get('px_per_cm') or 10.0
        s, ssrc = C.CANON_PPC / ppc, 'library sheet px_per_cm %.3f' % ppc
    if 'scale' in fx:
        s, ssrc = float(fx['scale']), 'fixes.json'
    M = C.similarity(kp['pivot'], g['pivot'], rot, s)
    can = C.warp(rgba, M, g['canvas'])
    kc = {k: C.apply(M, v) for k, v in kp.items()}
    wd = widths_along(m, kp['pivot'], kp[tipk], (0.02, 0.5, 0.97))
    widths = {G_NAMES(part)[0]: round(wd[0] * s, 1), 'mid': round(wd[1] * s, 1), G_NAMES(part)[1]: round(wd[2] * s, 1)}
    if 'shoulder_l' in kp and 'shoulder_r' in kp:
        widths['shoulder_span'] = round(math.dist(kp['shoulder_l'], kp['shoulder_r']) * s, 1)
    flags += fx.get('flags', [])
    if max(m.shape) < 180:
        flags.append('low_res')
    if part == 'torso' and 'brass' not in src.get('neck', ''):
        flags.append('neck_pivot_estimated')
    if part == 'pelvis' and 'hip_l' in kp and 'hip_r' in kp:
        widths['hip_span'] = round(math.dist(kp['hip_l'], kp['hip_r']) * s, 1)
    if part not in ('torso', 'pelvis'):
        for k in ('pivot', tipk):
            if 'brass' not in src.get(k, ''):
                flags.append('%s_pivot_estimated' % ('proximal' if k == 'pivot' else 'distal'))
        # contamination hint: more brass brads along the bone than its two ends (two segments on one card)
        mids = [b for b in bl if min(math.dist(b['c'], kp['pivot']), math.dist(b['c'], kp[tipk])) > 0.2 * D and b['r'] > 0.5 * max(x['r'] for x in bl)]
        if mids:
            flags.append('extra_brads_mid_segment')
    return dict(rgba=can, M=M, kp=kp, kc=kc, cls=cls, px={'zip_offset': None if zo is None else round(zo, 3), 'brads_found': len(bl)},
                flags=sorted(set(flags)), removed=removed, scale=s, rot=rot, psrc='; '.join('%s: %s' % kv for kv in src.items()),
                ssrc=ssrc, widths=widths)


def candidates(ch, part):
    lab, fxs = C.labels(), C.fixes()
    out = []
    for c in C.cards():
        if c['character'] != ch:
            continue
        refile = fxs.get(c['id'], {}).get('part') or lab.get(c['id'], {}).get('slot')
        if (c['slot'] == part and not (refile and refile != part)) or refile == part:
            out.append(c)
    return out


KIT_LEN = {}
TIPK = lambda part: 'neck' if part == 'torso' else C.GRID[part]['tip_name']
G_NAMES = lambda part: ('waist', 'neck') if part == 'torso' else (C.GRID[part]['pivot_name'], C.GRID[part]['tip_name'])


def kit_length(ch, part):
    """the kit's own pivot->tip length in cm: the library px_per_cm is a fit of A-B to a bone, so the median of
    (brad-to-brad length / px_per_cm) over cards with both brads found is the bone length the kit was cut for"""
    fxs = C.fixes()
    L = []
    for c in candidates(ch, part):
        fx = fxs.get(c['id'], {})
        if fx.get('reject') or not c.get('px_per_cm'):
            continue
        rgba, _ = C.keep_main(C.load_rgba(c))
        tipk = TIPK(part)
        if part == 'torso':
            kp, src, _ = torso_points(c, rgba, C.mask_of(rgba), fx)
        elif part == 'pelvis':
            kp, src, _ = pelvis_points(c, rgba, C.mask_of(rgba), fx)
            if 'midpoint' not in src.get('hip_mid', ''):
                continue
        else:
            kp, src, _ = limb_points(c, rgba, C.mask_of(rgba), fx, part)
        if 'brass' in src.get('pivot', '') and ('brass' in src.get(tipk, '') or 'midpoint' in src.get(tipk, '')):
            L.append(math.dist(kp['pivot'], kp[tipk]) / c['px_per_cm'])
    return float(np.median(L)) if len(L) >= 3 else None


def run(ch, part):
    fxs = C.fixes()
    KIT_LEN[(ch, part)] = kit_length(ch, part)
    print('kit length', ch, part, KIT_LEN[(ch, part)])
    recs, tiles, bad = [], [], []
    for c in candidates(ch, part):
        fx = fxs.get(c['id'], {})
        lab = C.labels().get(c['id'], {})
        nbr = len(brass_blobs(C.load_rgba(c))) if part not in ('torso', 'pelvis') else 0
        if fx.get('part') == part and c['slot'] != part:
            fx = {k: v for k, v in fx.items() if k != 'reject'}      # re-filed INTO this part type: the reject was for its old slot
        if fx.get('reject') or lab.get('bad') or nbr >= 5:
            why = fx.get('reject') or (lab.get('note', 'bad') if lab.get('bad') else 'whole figure or multi-part card (%d brads), not one %s' % (nbr, part))
            recs.append(IX.reject_record(c, part, why, fx.get('refile')))
            bad.append(IX.reject_tile(C.load_rgba(c), c, why))
            continue
        r = process(c, part, fx)
        rec = IX.part_record(c, part, r, C.CANON_PPC)
        rec['widths_px'] = r['widths']
        recs.append(rec)
        path = os.path.join(C.LIB2, rec['image'])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(r['rgba']).save(path, optimize=True)
        cl = rec['classes']
        lines = [c['id'].split('/')[-1][:40] + '  ' + c['id'].split('.')[1],
                 '%s  %s  (%.2f/%.2f)' % (cl['view']['value'], cl['facing']['value'], cl['view']['conf'], cl['facing']['conf']),
                 '%s %s rot %+.0f x%.2f' % (cl['state']['value'], cl.get('side', {}).get('value', ''), r['rot'], r['scale']),
                 '%s' % '  '.join('%s %.0f' % kv for kv in r['widths'].items() if kv[0] != 'shoulder_span'),
                 ','.join(rec['flags'])[:44]]
        tiles.append((cl['view']['value'], IX.tile(r['rgba'], part, rec['keypoints']['canonical'], BONES.get(part, []), lines)))
    order = {'front': 0, 'three-quarter': 1, 'side': 2, 'three-quarter-back': 3, 'back': 4}
    tiles.sort(key=lambda t: order.get(t[0], 9))
    IX.merge(recs, ch, part)
    g = C.GRID[part]
    sheets = C.sheet([t for _, t in tiles], os.path.join(C.LIB2, 'sheets', '%s_%s_%%02d.jpg' % (ch, part)), cols=6,
                     title='%s %s on the grid (%dx%d, %s pivot red cross; grid 5 cm; %g px/cm)' % (ch, part, g['canvas'][0], g['canvas'][1], g['pivot_name'], C.CANON_PPC))
    sheets += C.sheet(bad, os.path.join(C.LIB2, 'sheets', '%s_%s_rejected_%%02d.jpg' % (ch, part)), cols=6, title='%s %s cards rejected (reason under each)' % (ch, part))
    print('\n'.join(sheets))


if __name__ == '__main__':
    ch = sys.argv[1]
    for part in sys.argv[2:]:
        run(ch, part)
