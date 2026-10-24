"""Pairwise joint tests: each part attached to the parts beside it, swept through the joint angle, seams scored.

    python3 shots/scion2/library2/qa/pairs.py poet head      # child part type: head (neck) | hand (wrist) | foot (ankle) ...

For every child part that passes its gates, the 3 best-matching neighbours are chosen. A neighbour must have the
same character, the same view family, and a compatible facing; the same costume and the same cut sheet rank
higher. The child is attached at its pivot to the neighbour's joint keypoint (both images are canonical, so the
neutral pose is zero rotation). It is then rotated through -60..+90 deg in 15 deg steps (positive = counter-clockwise
on screen), and every pose is scored with seam.score.

Writes:
- qa/results/<char>_<part>.json: the gates and every pair-angle score.
- qa/pairs.json: the compatibility matrix (child key -> neighbour key -> clean range, warn range, failures).
- qa/sheets/<char>_<part>_qa_NN.jpg: the review rows.
- qa/sheets/<char>_<part>_qa_worst.jpg: the worst offenders.
"""
import json, math, os, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))
sys.path.insert(0, HERE)
import common as C  # noqa: E402
import seam  # noqa: E402
import gates  # noqa: E402

ANGLES = list(range(-60, 91, 15))
SHOW = [-60, -30, -15, 0, 15, 45, 90]
# joint: child part, parent part, parent keypoint the child pivot goes on, which is drawn on top (stack order of the
# Skin Lab contract: torso over head; forearm over hand? the contract draws hands last, so hand over forearm;
# shin over foot? feet are drawn before shins in the front stack, so shin over foot)
JOINTS = {
    'head': dict(joint='neck', parent='torso', parent_kp='neck', over='parent', match='view'),
    'hand': dict(joint='wrist', parent='forearm', parent_kp='tip', over='child', match='side'),
    'foot': dict(joint='ankle', parent='shin', parent_kp='tip', over='parent', match='side'),
}
FAM = {'front': 'F', 'three-quarter': 'Q', 'side': 'S', 'three-quarter-back': 'QB', 'back': 'B', 'top': 'T'}
OUT = os.path.join(HERE, 'results')


def idx():
    return C.load_json(os.path.join(C.LIB2, 'index.json'))['parts']


def canon(rec):
    return np.array(Image.open(os.path.join(C.LIB2, rec['image'])).convert('RGBA'))


def neighbours(child, parents, k=3, match='view'):
    cv, cf = child['classes']['view']['value'], child['classes']['facing']['value']
    sk = child['source_card'].split('/')[0]
    out = []
    if match == 'side':
        csd = child['classes'].get('side', {}).get('value', 'unknown')
        for p in parents:
            psd = p['classes'].get('side', {}).get('value', 'unknown')
            if csd in ('left', 'right') and psd in ('left', 'right') and csd != psd:
                continue
            s = 2.0 if (csd == psd and csd != 'unknown') else 0.0
            s += 2 if p.get('costume') == child.get('costume') else 0
            s += 1 if p['source_card'].split('/')[0] == sk else 0
            s += 1 if 'estimated' not in ' '.join(p['flags']) else 0
            s -= 1 if p['classes']['state']['value'] in ('empty_sleeve', 'wrist_socket') else 0
            out.append((s, p))
        out.sort(key=lambda t: -t[0])
        return [p for s, p in out[:k]]
    for p in parents:
        pv, pf = p['classes']['view']['value'], p['classes']['facing']['value']
        ok = seam.facing_compatible((cv, cf), (pv, pf))
        if ok is False:
            continue
        s = 0.0
        s += 3 if FAM.get(pv) == FAM.get(cv) else 0
        s += 2 if (pf == cf and pf not in ('unknown',)) else 0
        s += 2 if p.get('costume') == child.get('costume') else 0
        s += 1 if p['source_card'].split('/')[0] == sk else 0
        s += 1 if 'brass' in (p.get('pivot_source') or '') and 'neck_pivot_estimated' not in p['flags'] else 0
        s -= 1 if any(w in p['source_card'] for w in ('lie', 'hollow', 'crouch', 'kneel', 'sitting', 'fall')) else 0
        s -= 0.5 if p['classes']['view']['conf'] < 0.5 else 0
        out.append((s, p))
    out.sort(key=lambda t: -t[0])
    return [p for s, p in out[:k]]


def compose(parent, child, theta, jcfg):
    """world frame = parent canonical canvas padded; child pivot on the parent's joint keypoint, rotated theta."""
    P = canon(parent)
    Cc = canon(child)
    pad = 320
    Hh, Ww = P.shape[0] + 2 * pad, P.shape[1] + 2 * pad
    kp = parent['keypoints']['canonical']
    jk = jcfg['parent_kp']
    J = np.array(kp[jk], float) + pad
    Mp = np.array([[1, 0, pad], [0, 1, pad]], float)
    Pw = cv2.warpAffine(P, Mp, (Ww, Hh), flags=cv2.INTER_NEAREST)
    gpiv = C.GRID[child['part']]['pivot']
    Mc = C.similarity(gpiv, J, theta, 1.0)
    Cw = C.warp(Cc, Mc, (Ww, Hh))
    mP, mC = Pw[..., 3] > 100, Cw[..., 3] > 100
    over_child = jcfg['over'] == 'child'
    under, overl = (Pw, Cw) if over_child else (Cw, Pw)
    comp = np.zeros((Hh, Ww, 4), np.float32)
    for L in (under, overl):
        a = L[..., 3:4].astype(np.float32) / 255
        comp[..., :3] = comp[..., :3] * (1 - a) + L[..., :3] * a
        comp[..., 3:4] = np.maximum(comp[..., 3:4], L[..., 3:4])
    comp = comp.astype(np.uint8)
    # axes at the joint: into the child = its primary axis rotated; into the parent = from joint toward parent pivot
    ax = np.array(C.GRID[child['part']]['axis'] or (0, 1), float)
    t = math.radians(theta)
    axc = np.array([ax[0] * math.cos(t) + ax[1] * math.sin(t), -ax[0] * math.sin(t) + ax[1] * math.cos(t)])
    pp = np.array(kp['pivot'], float) + pad
    axp = (pp - J) / (np.linalg.norm(pp - J) or 1)
    # features of the child that must stay visible (heads: the face oval between eye line and chin)
    feats = []
    ck = child['keypoints']['canonical']
    if child['part'] == 'head' and ck.get('eye_line') and ck.get('chin') and child['classes']['view']['value'] not in ('back', 'three-quarter-back'):
        f = np.zeros(Cc.shape[:2], np.uint8)
        e, ch = np.array(ck['eye_line']), np.array(ck['chin'])
        ctr = (e + ch) / 2
        ry = max(4, np.linalg.norm(ch - e) / 2)
        cv2.ellipse(f, (int(ctr[0]), int(ctr[1])), (int(0.75 * ry), int(ry)), 0, 0, 360, 1, -1)
        f = cv2.warpAffine(f, Mc, (Ww, Hh), flags=cv2.INTER_NEAREST).astype(bool) & mC
        feats.append(f)
    return comp, mC, mP, J, axc, axp, feats, over_child


VR = {'CLEAN': 0, 'WARN': 1, 'MUTILATED': 2}


def run_pair(child, parent, jcfg):
    """the z-order at the joint is not trusted from the stack alone: the neutral pose is scored both ways and the
    sweep runs with the better one (recorded as 'over')"""
    best = None
    for over in (jcfg['over'], 'child' if jcfg['over'] == 'parent' else 'parent'):
        j2 = dict(jcfg, over=over)
        r0 = _sweep(child, parent, j2, [0])[0][0]
        key = (VR[r0['verdict']], len(r0['why']), r0['covered'])
        if best is None or key < best[0]:
            best = (key, j2)
    res = _sweep(child, parent, best[1], ANGLES)
    for a in res:
        res[a][0]['over'] = best[1]['over']
    return res


def _sweep(child, parent, jcfg, angles):
    res = {}
    for th in angles:
        comp, mC, mP, J, axc, axp, feats, over_child = compose(parent, child, th, jcfg)
        # score inside a window around the joint (faster; the seam is local)
        x0, y0 = max(0, int(J[0]) - 360), max(0, int(J[1]) - 400)
        sl = (slice(y0, y0 + 760), slice(x0, x0 + 720))
        comp, mC, mP = comp[sl], mC[sl], mP[sl]
        feats = [f[sl] for f in feats]
        J = np.array(J) - [x0, y0]
        r = seam.score(comp, mC, mP, J, axc, axp, over='A' if over_child else 'B', featuresA=feats, featuresB=None,
                       facingA=(child['classes']['view']['value'], child['classes']['facing']['value']) if jcfg.get('match') == 'view' else None,
                       facingB=(parent['classes']['view']['value'], parent['classes']['facing']['value']) if jcfg.get('match') == 'view' else None,
                       joint=jcfg['joint'])
        # keep the composite only where a sheet needs it (memory)
        res[th] = (r, comp if th in SHOW else None, J)
    return res


def ranges(scores):
    """contiguous angle range around 0 where every step is CLEAN (and CLEAN-or-WARN)"""
    def span(okset):
        if 0 not in okset:
            return None
        lo = hi = 0
        while lo - 15 in okset:
            lo -= 15
        while hi + 15 in okset:
            hi += 15
        return [lo, hi]
    clean = {a for a, r in scores.items() if r['verdict'] == 'CLEAN'}
    usable = {a for a, r in scores.items() if r['verdict'] != 'MUTILATED'}
    return span(clean), span(usable)


COLV = {'CLEAN': (40, 170, 60), 'WARN': (235, 160, 0), 'MUTILATED': (215, 30, 30)}


TILE = {'up': 0.62}


def test_tile(comp, J, r, th, size=150, crop=520):
    x0, y0 = int(J[0] - crop / 2), int(J[1] - crop * TILE['up'])
    bg = Image.new('RGBA', (crop, crop), (246, 244, 238, 255))
    src = Image.fromarray(comp)
    bg.alpha_composite(src.crop((x0, y0, x0 + crop, y0 + crop)))
    im = bg.convert('RGB').resize((size, size), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    s = size / crop
    if r.get('spot') and r['verdict'] != 'CLEAN':
        sx, sy = (r['spot'][0] - x0) * s, (r['spot'][1] - y0) * s
        rr = max(10, r['seam_w'] * s * 0.6)
        d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], outline=COLV[r['verdict']], width=2)
    col = COLV[r['verdict']]
    d.rectangle([0, 0, size - 1, size - 1], outline=col, width=4)
    d.text((5, 4), '%+d' % th, fill=(0, 0, 0), font=C.font(11))
    if r['why']:
        d.text((5, size - 15), ','.join(w.replace('exposed_', 'exp') for w in r['why'])[:24], fill=col, font=C.font(10))
    return im


def run(ch, part):
    J = JOINTS[part]
    TILE['up'] = 0.62 if (C.GRID[part]['axis'] or (0, 1))[1] < 0 else 0.4
    P = idx()
    kids = [v for v in P.values() if v['character'] == ch and v['part'] == part and v['status'] == 'ok']
    pars = [v for v in P.values() if v['character'] == ch and v['part'] == J['parent'] and v['status'] == 'ok']
    jcfg = dict(J)
    if jcfg['parent_kp'] == 'tip':
        jcfg['parent_kp'] = C.GRID[J['parent']]['tip_name']
    # gate the parents too (when a gate exists for them) so failed parents are not used as neighbours
    pg = {p['key']: gates.gate(p) for p in pars}
    pars_ok = [p for p in pars if not pg[p['key']] or pg[p['key']]['verdict'] != 'fail']
    results, rows, worst = {}, [], []
    os.makedirs(OUT, exist_ok=True)
    pj_path = os.path.join(HERE, 'pairs.json')
    PJ = C.load_json(pj_path) if os.path.exists(pj_path) else {'about': 'compatibility matrix: child -> neighbour -> clean/usable angle ranges (deg, ccw +) and failures; produced by qa/pairs.py', 'pairs': {}}
    order = {'front': 0, 'three-quarter': 1, 'side': 2, 'three-quarter-back': 3, 'back': 4}
    kids.sort(key=lambda k: (order.get(k['classes']['view']['value'], 9), k['source_card']))
    counts = {'parts': {'pass': 0, 'warn': 0, 'fail': 0}, 'pair_angles': {'CLEAN': 0, 'WARN': 0, 'MUTILATED': 0}, 'kinds': {}}
    for kid in kids:
        g = gates.gate(kid)
        counts['parts'][g['verdict']] += 1
        entry = {'gates': g, 'pairs': {}}
        strip = []
        if g['verdict'] != 'fail':
            for nb in neighbours(kid, pars_ok, match=J.get('match', 'view')):
                res = run_pair(kid, nb, jcfg)
                sc = {a: r for a, (r, _, _) in res.items()}
                cl, us = ranges(sc)
                fails = {a: r['why'] for a, r in sc.items() if r['verdict'] != 'CLEAN'}
                entry['pairs'][nb['key']] = {'joint': J['joint'], 'over': sc[0]['over'], 'clean_range': cl, 'usable_range': us, 'scores': {str(a): r for a, r in sc.items()}}
                PJ['pairs'].setdefault(kid['key'], {})[nb['key']] = {'joint': J['joint'], 'clean_range': cl, 'usable_range': us,
                                                                    'failures': {str(a): w for a, w in fails.items()}}
                for a, r in sc.items():
                    counts['pair_angles'][r['verdict']] += 1
                    for w in r['why']:
                        counts['kinds'][w] = counts['kinds'].get(w, 0) + 1
                    sev = len(r['why']) + (5 if r['verdict'] == 'MUTILATED' else 0)
                    if sev and res[a][1] is not None:
                        worst.append((sev, kid, nb, a, r, test_tile(res[a][1], res[a][2], r, a, size=200)))
                worst.sort(key=lambda t: -t[0])
                del worst[24:]
                strip.append((nb, [test_tile(res[a][1], res[a][2], res[a][0], a) for a in SHOW], cl, us))
        else:
            for nb_key in list(PJ['pairs'].get(kid['key'], {})):
                PJ['pairs'][kid['key']].pop(nb_key)
        results[kid['key']] = entry
        rows.append(row_image(kid, g, strip, {k: ('head' if J['joint'] == 'neck' else part) if v.get('over') == 'child' else J['parent'] for k, v in entry['pairs'].items()}))
    worst.sort(key=lambda t: -t[0])
    with open(os.path.join(OUT, '%s_%s.json' % (ch, part)), 'w') as f:
        json.dump({'joint': J['joint'], 'angles': ANGLES, 'counts': counts, 'parts': results}, f, indent=1, default=str)
    rebuild_pairs()
    sheets = stack(rows, os.path.join(HERE, 'sheets', '%s_%s_qa_%%02d.jpg' % (ch, part)),
                   '%s %s QA: gates + %s joint sweep vs neighbour %ss (green CLEAN, amber WARN, red MUTILATED; circle = failing seam)' % (ch, part, J['joint'], J['parent']))
    sheets.append(worst_sheet(worst[:24], os.path.join(HERE, 'sheets', '%s_%s_qa_worst.jpg' % (ch, part)), ch, part, counts))
    print(json.dumps(counts))
    print('\n'.join(sheets))
    return counts, sheets


def rebuild_pairs():
    """pairs.json is derived from every results/<char>_<part>.json (so parallel runs never clobber each other)"""
    PJ = {'about': 'compatibility matrix: child part key -> neighbour key -> clean_range / usable_range (deg, ccw +, '
                   'contiguous around 0) and the non-CLEAN angles with their failing terms; derived from qa/results/*.json by qa/pairs.py',
          'gates': {}, 'pairs': {}}
    for fn in sorted(os.listdir(OUT)):
        if not fn.endswith('.json'):
            continue
        R = C.load_json(os.path.join(OUT, fn))
        for key, e in R['parts'].items():
            PJ['gates'][key] = e['gates']['verdict']
            for nb, p in e['pairs'].items():
                PJ['pairs'].setdefault(key, {})[nb] = {'joint': p['joint'], 'over': p.get('over'), 'clean_range': p['clean_range'], 'usable_range': p['usable_range'],
                                                       'failures': {a: r['why'] for a, r in p['scores'].items() if r['verdict'] != 'CLEAN'}}
    with open(os.path.join(HERE, 'pairs.json'), 'w') as f:
        json.dump(PJ, f, indent=1)


def row_image(kid, g, strip, strip_over=None):
    strip_over = strip_over or {}
    T = 150
    head = C.draw_tile(canon(kid), kid['part'], kid['keypoints']['canonical'], [], [], tile=T)
    head = head.crop((0, 0, T, T))
    nstrip = max(1, len(strip))
    W = 8 + T + 10 + 7 * (T + 4) + 8
    hrow = T + 26
    H = 22 + nstrip * hrow + 74
    im = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    f, fb = C.font(11), C.font(13)
    cl = kid['classes']
    d.text((8, 4), '%s   [%s %s %s]   gates: %s' % (kid['source_card'], cl['view']['value'], cl['facing']['value'], cl['state']['value'], g['verdict'].upper()),
           fill=COLV[{'pass': 'CLEAN', 'warn': 'WARN', 'fail': 'MUTILATED'}[g['verdict']]], font=fb)
    im.paste(head, (8, 22))
    for i, (nb, tiles, clr, us) in enumerate(strip):
        y = 22 + i * hrow
        for j, t in enumerate(tiles):
            im.paste(t, (8 + T + 10 + j * (T + 4), y))
        d.text((8 + T + 10, y + T + 3), 'with %s [%s %s]  %s on top  clean %s  usable %s' % (nb['source_card'][-44:], nb['classes']['view']['value'], nb['classes']['facing']['value'],
                                                                                 strip_over.get(nb['key'], '?'), clr, us), fill=(60, 60, 60), font=f)
    if not strip:
        d.text((8 + T + 10, 60), 'excluded from pairing (gate fail)' if g['verdict'] == 'fail' else 'no compatible neighbour', fill=(200, 0, 0), font=fb)
    y = 22 + nstrip * hrow + 4
    for k in ('cutoff', 'contamination', 'connection', 'view'):
        t = g[k]
        d.text((8, y), '%-13s %-4s %s' % (k, t['result'].upper(), (t['why'] or '')[:150]),
               fill=COLV[{'pass': 'CLEAN', 'warn': 'WARN', 'fail': 'MUTILATED'}[t['result']]] if t['result'] != 'pass' else (60, 60, 60), font=f)
        y += 16
    d.line([(0, H - 1), (W, H - 1)], fill=(150, 150, 150), width=2)
    return im


def stack(rows, pattern, title, per=6):
    out = []
    for k in range(0, len(rows), per):
        ch = rows[k:k + per]
        W = max(r.width for r in ch)
        H = 34 + sum(r.height for r in ch)
        S = Image.new('RGB', (W, H), (255, 255, 255))
        ImageDraw.Draw(S).text((8, 8), title + '  (page %d)' % (k // per + 1), fill=(0, 0, 0), font=C.font(16))
        y = 34
        for r in ch:
            S.paste(r, (0, y)); y += r.height
        p = pattern % (k // per + 1)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        S.save(p, quality=85)
        out.append(p)
    return out


def worst_sheet(worst, path, ch, part, counts):
    T = 200
    cols = 6
    rows = max(1, math.ceil(len(worst) / cols))
    S = Image.new('RGB', (cols * (T + 6) + 6, 70 + rows * (T + 40)), (255, 255, 255))
    d = ImageDraw.Draw(S)
    d.text((8, 6), '%s %s QA: worst pair-angles' % (ch, part), fill=(0, 0, 0), font=C.font(16))
    d.text((8, 28), 'parts: %s   pair-angles: %s' % (counts['parts'], counts['pair_angles']), fill=(0, 0, 0), font=C.font(12))
    d.text((8, 46), 'failure kinds: %s' % dict(sorted(counts['kinds'].items(), key=lambda kv: -kv[1])), fill=(0, 0, 0), font=C.font(12))
    for i, (sc, kid, nb, a, r, tile) in enumerate(worst):
        x, y = 6 + (i % cols) * (T + 6), 70 + (i // cols) * (T + 40)
        S.paste(tile, (x, y))
        d.text((x, y + T + 2), kid['source_card'].split('/')[-1][:30], fill=(0, 0, 0), font=C.font(10))
        d.text((x, y + T + 14), '+ ' + nb['source_card'].split('/')[-1][:28], fill=(80, 80, 80), font=C.font(10))
        d.text((x, y + T + 26), ','.join(r['why'])[:34], fill=COLV[r['verdict']], font=C.font(10))
    S.save(path, quality=85)
    return path


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
