"""Harvest replacement cards from the painted poses: every limb the painter already drew foreshortened, cut into its own card.

    python3 shots/skinlab/production/recognition/harvest.py [character]      (default poet)

For each painted pose of the character (Pose Lab targets, shots/rig/poses/<character>__*.json), excluding paintings that
show another man, paintings the cutter cropped, and costumes other than the contract's: the joints on the painting come
from the Pose Lab solve projected into the painting (its own FK, view and scale), each replaced by the painting's labelled
marker when that marker is confident (>= .5) and within 10 cm of the solve. Every opaque pixel of the figure is given to
the nearest bone segment (within a width cap per part), so limbs split at the joints along the bisector between bones;
each card also keeps an overlap lobe of its parent's pixels around its own root joint, so the brad hides the seam.

Writes (source cuts are never touched):
  shots/kits/cut_harvest/<sheet>/<pose>/<part>.webp        one card per segment
  shots/skinlab/library_harvest.json                        library.json fields + source, view, facing, dir_cam (the bone's
                                                            unit direction in camera space: screen x, screen y down, toward
                                                            the camera), ratio (projected / true length: foreshortening),
                                                            flex (the hinge angle at its root, degrees), bad / why
  shots/skinlab/production/recognition/harvest_contact.jpg  every card with A (green) and B (red), bad ones crossed
"""
import json, math, os, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SKIN = os.path.abspath(os.path.join(HERE, '..', '..'))
SHOTS = os.path.dirname(SKIN)
sys.path.insert(0, os.path.join(SHOTS, 'rig'))
import solve as SV  # noqa: E402

CH = (sys.argv[1:] or ['poet'])[0]
C = json.load(open(os.path.join(SKIN, 'contracts', CH + '.json')))
NOTES = json.load(open(os.path.join(HERE, 'notes.json')))
OUTC = os.path.join(SHOTS, 'kits', 'cut_harvest')
# part, side, from, to, width cap (cm, distance from the bone), t range along the bone, parent part (for the lobe)
SEGS = [('torso', None, 'w7', 'neck', 26, (-.05, 1.05), None), ('head', None, 'neck', 'top', 15, (-.05, 1.2), 'torso')]
for s in 'LR':
    SEGS += [('upper_arm', s, 'sh' + s, 'el' + s, 9, (-.08, 1.0), 'torso'), ('forearm', s, 'el' + s, 'wr' + s, 8, (0, 1.0), 'upper_arm'),
             ('hand', s, 'wr' + s, 'tip' + s, 8, (0, 1.15), 'forearm'), ('thigh', s, 'hip' + s, 'kn' + s, 12, (-.1, 1.0), 'torso'),
             ('shin', s, 'kn' + s, 'an' + s, 10, (0, 1.0), 'thigh'), ('foot', s, 'an' + s, 'toe' + s, 10, (-.45, 1.15), 'shin')]
MK = {'shL': 'shoulderL', 'shR': 'shoulderR', 'elL': 'elbowL', 'elR': 'elbowR', 'wrL': 'wristL', 'wrR': 'wristR', 'hipL': 'hipL', 'hipR': 'hipR',
      'knL': 'kneeL', 'knR': 'kneeR', 'anL': 'ankleL', 'anR': 'ankleR', 'toeL': 'toeL', 'toeR': 'toeR', 'neck': 'neck'}
VIEW = lambda psi: SV.view_key(psi)

def cropped(img):
    a = np.asarray(Image.open(os.path.join(SHOTS, img)).convert('RGBA'))[..., 3] > 128
    return a[:, 0].mean() > .25 or a[:, -1].mean() > .25 or a[0, :].mean() > .25

def lab_mean(rgb, m):
    if m.sum() < 5: return None
    L = cv2.cvtColor(rgb[None, m].astype(np.uint8), cv2.COLOR_RGB2LAB)[0].astype(float).mean(0)
    return [round(L[0] * 100 / 255, 1), round(L[1] - 128, 1), round(L[2] - 128, 1)]

def harvest():
    files = [f for f in os.listdir(os.path.join(SHOTS, 'rig', 'poses')) if f.startswith(CH + '__') and f.endswith('.json')]
    lib, skipped, sets = [], [], []
    for fn in sorted(files):
        D = json.load(open(os.path.join(SHOTS, 'rig', 'poses', fn))); costume = fn.split('__', 1)[1][:-5]
        if costume != C.get('costume'): skipped.append({'file': fn, 'why': f'costume {costume} is not the contract costume'}); continue
        Sk = D['skeleton']
        for t in D['targets']:
            if not t.get('solves'): skipped.append({'id': t['id'], 'why': 'no Pose Lab solve'}); continue
            if any(t['id'].startswith(o) for o in NOTES['other_man']): skipped.append({'id': t['id'], 'why': 'another man is painted'}); continue
            if cropped(t['img']): skipped.append({'id': t['id'], 'why': 'the painting card is cropped'}); continue
            sol = t['solves'][0]; psi = sol['psi']; s_px = sol['scale_px_per_cm']; ox, oy = sol['params']['ox'], sol['params']['oy']
            X = np.array([[sol['params'][n] for n in SV.PN]]); J = SV.fk(Sk, X)
            p, w = J['pelvis'][0], J['waist'][0]; u = (w - p) / (np.linalg.norm(w - p) or 1); J['w7'] = (p + 7 * u)[None]
            pt, dep = {}, {}
            for n, v in J.items():
                if n == '_F': continue
                xy, d = SV.project(v[0], psi, ox, oy); pt[n] = np.array([xy[0] * s_px + t['cx'], xy[1] * s_px + t['floor']]); dep[n] = float(d)
            for n, m in MK.items():   # the painting's own labelled marker, when it is confident and agrees with the solve
                mm = (t.get('markers') or {}).get(m)
                if mm and mm[2] >= .5 and np.hypot(mm[0] - pt[n][0], mm[1] - pt[n][1]) < 10 * s_px:
                    sh = np.array(mm[:2]) - pt[n]; pt[n] = np.array(mm[:2], float)
                    if n.startswith('wr'): pt['tip' + n[-1]] = pt['tip' + n[-1]] + sh   # the hand moves with its wrist
            im = np.asarray(Image.open(os.path.join(SHOTS, t['img'])).convert('RGBA')); Hh, Ww = im.shape[:2]
            mask = im[..., 3] > 100
            ys, xs = np.nonzero(mask); P2 = np.stack([xs, ys], 1).astype(float)
            dist = np.full((len(SEGS), len(P2)), np.inf); draw = np.full(len(P2), np.inf)
            for i, (part, sd, a, b, cap, (t0, t1), par) in enumerate(SEGS):
                A, B = pt[a], pt[b]; v = B - A; L2 = float(v @ v) or 1.0
                tt = ((P2 - A) @ v) / L2; tc = np.clip(tt, t0, t1)
                d = np.linalg.norm(P2 - (A + tc[:, None] * v), axis=1)
                draw = np.minimum(draw, d)
                d[(tt < t0 - .15) | (tt > t1 + .15)] = np.inf; d[d > cap * s_px] = np.inf
                dist[i] = d
            owner = np.argmin(dist, 0); owner[np.isinf(dist.min(0))] = -1
            sheet, pose = t['id'].split('/', 1)
            os.makedirs(os.path.join(OUTC, sheet, pose), exist_ok=True)
            # the set piece: painted pixels no bone claims (a bike, a chair, a cup, a mirror), as one silhouette card
            rest = np.zeros(mask.shape, np.uint8); rr = owner == -1; rest[P2[rr, 1].astype(int), P2[rr, 0].astype(int)] = 1
            n_, lab_, st_, _ = cv2.connectedComponentsWithStats(rest, connectivity=8)
            rawd = np.zeros(mask.shape, np.float32); rawd[P2[:, 1].astype(int), P2[:, 0].astype(int)] = draw / s_px
            # a prop, not a stray edge of the figure: a sizeable piece whose pixels lie on average > 14 cm from every bone
            keep = [i for i in range(1, n_) if st_[i, cv2.CC_STAT_AREA] > .015 * mask.sum() and rawd[lab_ == i].mean() > 14]
            if keep:
                km = np.isin(lab_, keep); yy, xx = np.nonzero(km)
                sx0, sx1, sy0, sy1 = xx.min(), xx.max() + 1, yy.min(), yy.max() + 1
                card = np.zeros((sy1 - sy0, sx1 - sx0, 4), np.uint8); card[yy - sy0, xx - sx0] = im[yy, xx]
                spath = os.path.join(OUTC, sheet, pose, '_set.webp'); Image.fromarray(card).save(spath, lossless=True)
                sets.append({'source': t['id'], 'img': os.path.relpath(spath, SKIN), 'x0': int(sx0), 'y0': int(sy0), 'w': int(sx1 - sx0), 'h': int(sy1 - sy0),
                             'area': int(km.sum()), 'share_of_figure': round(float(km.sum() / mask.sum()), 3)})
            idx = {(sg[0], sg[1]): i for i, sg in enumerate(SEGS)}
            for i, (part, sd, a, b, cap, tr, par) in enumerate(SEGS):
                sel = owner == i
                if par:   # the overlap lobe: the parent's pixels around this segment's root joint
                    pi = idx.get((par, sd if par not in ('torso',) else None)) if par != 'torso' else idx[('torso', None)]
                    lobe = (owner == pi) & (np.linalg.norm(P2 - pt[a], axis=1) < .55 * cap * s_px)
                    sel = sel | lobe
                card_id = f'harvest.{sheet}/{pose}/{part}' + (f'-{sd.lower()}' if sd else '')
                L3 = float(np.linalg.norm(J[b][0] - J[a][0])); d2 = pt[b] - pt[a]; L2 = float(np.linalg.norm(d2)) / s_px
                ddep = dep[b] - dep[a]; dir_cam = [round(float(d2[0] / s_px / L3), 3), round(float(d2[1] / s_px / L3), 3), round(float(ddep / L3), 3)] if L3 else [0, 0, 0]
                why = []
                if sel.sum() < 40: why.append('too few pixels')
                exp = max(L2, 4) * cap * s_px * s_px * .5
                if part not in ('torso', 'head') and sel.sum() < .3 * exp: why.append(f'thin: {int(sel.sum())} px of ~{int(exp)} expected (hidden or overlapped in the painting)')
                for q, nm in ((pt[a], 'root'), (pt[b], 'end')):
                    qi = (int(round(q[1])), int(round(q[0])))
                    if not (0 <= qi[0] < Hh and 0 <= qi[1] < Ww): why.append(f'{nm} joint off the painting')
                if not sel.any(): continue
                xs_, ys_ = P2[sel, 0].astype(int), P2[sel, 1].astype(int)
                x0, x1, y0, y1 = max(0, xs_.min() - 2), min(Ww, xs_.max() + 3), max(0, ys_.min() - 2), min(Hh, ys_.max() + 3)
                card = np.zeros((y1 - y0, x1 - x0, 4), np.uint8); card[ys_ - y0, xs_ - x0] = im[ys_, xs_]
                al = (card[..., 3] > 100).astype(np.uint8); n_, lab_, st_, _ = cv2.connectedComponentsWithStats(al, connectivity=8)
                if n_ > 1 and st_[1:, cv2.CC_STAT_AREA].max() < .85 * al.sum(): why.append('broken into pieces (another part crosses it in the painting)')
                dil = cv2.dilate(al, np.ones((9, 9), np.uint8))
                for q, nm in ((pt[a], 'root'), (pt[b], 'end')):
                    qx, qy = int(round(q[0] - x0)), int(round(q[1] - y0))
                    if not (0 <= qy < dil.shape[0] and 0 <= qx < dil.shape[1] and dil[qy, qx]) and part not in ('hand', 'head'): why.append(f'{nm} joint is not on the painted limb')
                if part == 'foot' and dep[b] - dep[a] < -12 and VIEW(psi) == 'front': why.append('boot seen from behind in a front view')
                fpath = os.path.join(OUTC, sheet, pose, part + (f'-{sd.lower()}' if sd else '') + '.webp')
                Image.fromarray(card).save(fpath, lossless=True)
                rgb = im[..., :3]; m2 = np.zeros(mask.shape, bool); m2[ys_, xs_] = True
                r_, g_, b_ = (rgb[..., i].astype(int) for i in range(3))
                skinm = m2 & (r_ - b_ > 25) & (r_ - b_ < 120) & (g_ - b_ < 70) & (r_ > 70) & (r_ >= g_) & (g_ >= b_)   # painted brown skin, not brass or gold
                skin_share = float(skinm.sum() / max(1, m2.sum()))
                if part == 'hand' and skin_share < .4: why.append(f'not a hand: only {skin_share:.0%} skin (a sleeve, a prop or a held object)')
                pl = lab_mean(rgb, m2)
                if part == 'hand' and pl and pl[0] > 62: why.append(f'too light for a hand (L {pl[0]}): paper, stone or a cup')
                if part == 'head' and skin_share < .2: why.append(f'not a face: only {skin_share:.0%} skin')
                if part in ('upper_arm', 'forearm', 'thigh', 'shin', 'torso') and skin_share > .45: why.append(f'mostly skin ({skin_share:.0%}): a hand or face, not cloth')
                flex = None
                if part in ('forearm', 'shin', 'hand', 'foot'):
                    up = {'forearm': ('sh', 'el'), 'shin': ('hip', 'kn'), 'hand': ('el', 'wr'), 'foot': ('kn', 'an')}[part]
                    u1 = J[up[1] + sd][0] - J[up[0] + sd][0]; u2 = J[b][0] - J[a][0]
                    flex = round(math.degrees(math.acos(max(-1, min(1, float(u1 @ u2) / (np.linalg.norm(u1) * np.linalg.norm(u2) or 1))))), 1)
                vk = VIEW(psi)
                lib.append({'id': card_id, 'img': os.path.relpath(fpath, SKIN), 'w': int(x1 - x0), 'h': int(y1 - y0), 'slot': part, 'side': sd,
                            'view': vk, 'state': 'harvest', 'character': CH, 'costume': costume, 'px_per_cm': round(s_px, 4),
                            'A': [round(float(pt[a][0] - x0), 1), round(float(pt[a][1] - y0), 1)], 'B': [round(float(pt[b][0] - x0), 1), round(float(pt[b][1] - y0), 1)],
                            'pts': 'harvest', 'q': 'C' if why else 'A', 'label': f'{part} {sd or ""} from {t["id"]}', 'brads': [],
                            'pal': lab_mean(rgb, m2), 'tone': lab_mean(rgb, skinm), 'skin': round(float(skinm.sum() / max(1, m2.sum())), 2), 'area': int(sel.sum()),
                            'source': t['id'], 'source_img': t['img'], 'psi': psi, 'facing': 'right' if 0 < psi % 360 < 180 else 'left' if psi % 180 else ('camera' if psi % 360 == 0 else 'away'),
                            'dir_cam': dir_cam, 'ratio': round(L2 / L3, 3) if L3 else 1.0, 'flex': flex, 'solve_iou': sol.get('iou'),
                            'bad': bool(why), 'why': why})
    json.dump({'about': __doc__.split('\n\n')[0] + ' See shots/skinlab/production/recognition/harvest.py. Cards marked bad stay listed (never deleted).',
               'skipped': skipped, 'sets': sets, 'cards': lib}, open(os.path.join(SKIN, 'library_harvest.json'), 'w'), indent=1)
    return lib, skipped

def contact(lib):
    good = sorted(lib, key=lambda c: (c['slot'], c['ratio']))
    cw, ch, cols = 96, 132, 20
    S = Image.new('RGB', (cols * cw, ((len(good) + cols - 1) // cols) * ch), (233, 226, 212)); d = ImageDraw.Draw(S)
    for i, c in enumerate(good):
        im = Image.open(os.path.join(SKIN, c['img'])).convert('RGBA'); k = min((cw - 8) / im.width, (ch - 26) / im.height, 3)
        im2 = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k)))); x0, y0 = (i % cols) * cw + 4, (i // cols) * ch + 18
        S.paste(im2, (x0, y0), im2)
        for q, col in ((c['A'], (0, 160, 0)), (c['B'], (210, 0, 0))): d.ellipse([x0 + q[0] * k - 3, y0 + q[1] * k - 3, x0 + q[0] * k + 3, y0 + q[1] * k + 3], fill=col)
        d.text((x0, y0 - 16), f"{c['slot'][:5]}{c['side'] or ''} {c['ratio']:.2f}", fill=(40, 30, 20))
        if c['bad']: d.line([x0, y0, x0 + cw - 8, y0 + ch - 26], fill=(220, 0, 0), width=2)
    S.save(os.path.join(HERE, 'harvest_contact.jpg'), quality=80)

if __name__ == '__main__':
    lib, sk = harvest(); contact(lib)
    from collections import Counter
    print(len(lib), 'cards,', sum(not c['bad'] for c in lib), 'usable; skipped', len(sk))
    print(Counter((c['slot'], c['view']) for c in lib if not c['bad']))
