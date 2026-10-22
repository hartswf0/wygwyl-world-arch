"""Data for the Skin Lab: the Crash Lab trials and the card library per bone.

    python3 shots/skinlab/build.py      # -> shots/skinlab/trials.json, shots/skinlab/library.json

bank/T*.json  a compact copy of the bank for the page (the bank itself is not committed): per frame per actor
              the 26 joints as one flat list of integers in half-centimetres, and the three facing vectors.
trials.json   the Bolas Crash Lab bank (shots/arena/bolas/bank/T*.json: 3D joints in cm, y up, per frame,
              per actor), listed with title, category, length and actors; the page loads a trial on demand.
library.json  every body card that can skin a bone: its slot (torso, head, upper_arm, forearm, hand, thigh,
              shin, foot), side, view, character/costume, true scale (shots/kits/cut/normalized.json, else the
              Body Lab) and two points in card px: A where it attaches to its parent joint and B where its
              child joint sits. Limbs: the two brads farthest apart, A the upper one (cards are drawn hanging);
              torso: A the lower brad (pelvis), B the upper (neck); hand: A the wrist eyelet, B the fingertip;
              foot: A the ankle brad, B the toe end; head: A the neck end, B the crown. Points are guesses
              where a card has fewer brads; the page lets you drag them, and saves the fix.
              Also the hip bridges (pelvis connectors: one waist hole over two thigh holes), which the
              normaliser has no slot for: scaled by the median px/cm of the body cards on the same sheet,
              A the waist (top brad), B the crotch (bottom centre). Every card carries its brads, so the
              page can snap a child's socket onto a real hole.
              Read from the pixels of every card (labels are often wrong): its costume colour (median Lab of the
              painted, non-skin pixels) for kitbashing across kits; for heads, the angle: front (symmetric, face
              skin in the middle), back (symmetric, hair where the face would be), profile/three-quarter (lopsided),
              and which way it faces (skin on one side, dark hair on the other).
"""
import glob, json, os, re, statistics
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)


def compact(j):
    """Per actor one flat list of integers: per frame the 26 joints (x,y,z in half-cm) then fwd, hfwd, pfwd (x100),
    each frame stored as the difference from the frame before (small numbers, small file)."""
    out = {'id': j['id'], 'title': j.get('title'), 'view': j.get('view'), 'after': j.get('after'), 'actors': j.get('actors'), 'n': len(j['frames']),
           'per_frame': 87, 'units': 'joints half-cm, facing x100, delta-coded over frames', 'a': {}}
    for a in j['actors']:
        prev, flat = None, []
        for fr in j['frames']:
            x = fr['a'][a['id']]
            cur = [int(round(c * 2)) for q in x['j'] for c in q] + [int(round(c * 100)) for k in ('fwd', 'hfwd', 'pfwd') for c in (x.get(k) or x['fwd'])]
            flat += cur if prev is None else [c - p for c, p in zip(cur, prev)]
            prev = cur
        out['a'][a['id']] = flat
    return out


def trials():
    out = []
    os.makedirs(os.path.join(HERE, 'bank'), exist_ok=True)
    for f in sorted(glob.glob(os.path.join(SHOTS, 'arena', 'bolas', 'bank', 'T*.json'))):
        j = json.load(open(f))
        out.append({'id': j['id'], 'title': j.get('title'), 'cat': j.get('cat'), 'len': j.get('len') or len(j.get('frames', [])),
                    'actors': [a.get('name') for a in j.get('actors', [])], 'note': (j.get('note') or '')[:200],
                    'file': 'bank/' + os.path.basename(f)})
        json.dump(compact(j), open(os.path.join(HERE, 'bank', os.path.basename(f)), 'w'), separators=(',', ':'))
    return out


def points(path, slot, brads, view):
    im = np.array(Image.open(path).convert('RGBA'))
    a = im[..., 3] > 128
    ys, xs = np.nonzero(a)
    if not len(xs):
        return None, None, 'empty'
    pts = np.stack([xs, ys], 1).astype(float)
    B = [np.array(b, float) for b in brads]
    if slot in ('upper_arm', 'forearm', 'thigh', 'shin', 'torso') and len(B) >= 2:
        i, j = max(((i, j) for i in range(len(B)) for j in range(i + 1, len(B))), key=lambda ij: np.linalg.norm(B[ij[0]] - B[ij[1]]))
        top, bot = sorted([B[i], B[j]], key=lambda p: p[1])
        return (bot, top, 'brads') if slot == 'torso' else (top, bot, 'brads')
    if slot == 'hand' and B:
        A = B[0]
        return A, pts[np.argmax(np.linalg.norm(pts - A, axis=1))], 'eyelet+tip'
    if slot == 'foot':
        A = B[0] if B else np.array([xs.min() + .25 * (xs.max() - xs.min()), ys.min() + .2 * (ys.max() - ys.min())])
        far = pts[np.argmax(np.linalg.norm(pts - A, axis=1))]
        return A, np.array([far[0], ys.max()]) if view not in ('front', 'back') else np.array([A[0], ys.max()]), 'ankle+toe' if B else 'guess'
    if slot == 'head':
        cx = (xs.min() + xs.max()) / 2
        A = max(B, key=lambda p: p[1]) if B else np.array([cx, ys.max()])
        return A, np.array([cx, ys.min()]), 'neck+crown' if B else 'guess'
    # one brad or none: along the long axis
    c = pts.mean(0); u, s, vt = np.linalg.svd(pts[::max(1, len(pts) // 3000)] - c, full_matrices=False)
    d = vt[0] if vt[0][1] > 0 else -vt[0]
    proj = (pts - c) @ d
    top, bot = c + d * proj.min() * .9, c + d * proj.max() * .9
    return ((bot, top) if slot == 'torso' else (top, bot)) + ('axis',)


PELVIS = re.compile(r'hip-bridge|bridge-hip|pelvis-conn|hip-conn|^hip-(profile|back|front)|waist-link|pelvis-\d*-?connector')


def view_of(name):
    for v, pat in (('threequarter_back', r'three-?quarter-back'), ('threequarter', r'three-?quarter|3-4'), ('profile', r'profile'), ('back', r'back'), ('front', r'front')):
        if re.search(pat, name):
            return v
    return None


def pelvis_cards(cat, N, R):
    sheet_ppc = {}
    for pid, n in N.items():
        if n.get('px_per_cm'):
            sheet_ppc.setdefault(pid.split('/')[0], []).append(n['px_per_cm'])
    char = {pid.split('/')[0]: (n.get('character'), n.get('costume')) for pid, n in N.items()}
    out = []
    for sid, sh in cat.items():
        if sid not in sheet_ppc or re.search(r'prop|set\.|fx\.|ref', sid):
            continue
        for p in sh['parts']:
            n = p['id'].split('/')[-1].lower()
            if not PELVIS.search(n) or R.get(p['id'], {}).get('q') == 'C':
                continue
            path = os.path.join(SHOTS, 'kits', 'cut', p['file'])
            a = np.array(Image.open(path).convert('RGBA'))[..., 3] > 128
            ys, xs = np.nonzero(a)
            if not len(xs):
                continue
            B = sorted((p.get('brads') or []), key=lambda b: b[1])
            cx = (xs.min() + xs.max()) / 2
            top = B[0] if B else [cx, ys.min() + .08 * (ys.max() - ys.min())]
            w, h = Image.open(path).size
            ch, co = char.get(sid, (None, None))
            out.append({'id': p['id'], 'img': '../kits/cut/' + p['file'], 'w': w, 'h': h, 'slot': 'pelvis', 'side': None, 'view': view_of(n),
                        'state': None, 'character': ch, 'costume': co, 'px_per_cm': round(statistics.median(sheet_ppc[sid]), 3),
                        'A': [round(float(top[0]), 1), round(float(top[1]), 1)], 'B': [round(float(cx), 1), round(float(ys.max()), 1)],
                        'pts': 'waist+crotch' if B else 'guess', 'q': R.get(p['id'], {}).get('q'), 'label': p.get('name') or p.get('label') or '',
                        'brads': [[round(float(x), 1), round(float(y), 1)] for x, y in (p.get('brads') or [])]})
    return out


def rgb2lab(rgb):
    c = rgb / 255.0
    c = np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
    X = c @ np.array([.4124, .3576, .1805]) / .9505; Y = c @ np.array([.2126, .7152, .0722]); Z = c @ np.array([.0193, .1192, .9505]) / 1.089
    f = lambda t: np.where(t > .008856, np.cbrt(t), 7.787 * t + 16 / 116)
    return np.stack([116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))], -1)


def analyse(path, slot):
    im = np.array(Image.open(path).convert('RGBA')).astype(float)
    a = im[..., 3] > 128
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    skin = a & (r > g) & (g > b) & (r - b > 30) & (r > 80)
    cloth = a & ~skin
    px = im[..., :3][cloth] if cloth.sum() > 50 else im[..., :3][a]
    out = {'pal': [round(float(v), 1) for v in np.median(rgb2lab(px[::max(1, len(px) // 4000)]), 0)], 'skin': round(float(skin.sum() / max(1, a.sum())), 2),
           'area': int(a.sum())}   # painted pixels: with px_per_cm, the card's true area, hence its mass
    if skin.sum() > 50:   # skin tone, so a borrowed hand or head matches the body it goes on
        sp = im[..., :3][skin]; out['tone'] = [round(float(v), 1) for v in np.median(rgb2lab(sp[::max(1, len(sp) // 3000)]), 0)]
    if slot != 'head':
        return out
    ys, xs = np.nonzero(a); y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    cx, w = xs.mean(), max(1, x1 - x0)
    m = a[:, max(0, int(cx - w / 2)):int(cx + w / 2)]
    sym = float((m & m[:, ::-1]).sum() / max(1, (m | m[:, ::-1]).sum()))
    band, cb = slice(int(y0 + .25 * (y1 - y0)), int(y0 + .6 * (y1 - y0))), slice(int(x0 + .3 * w), int(x0 + .7 * w))
    faceskin = float(skin[band, cb].sum() / max(1, a[band, cb].sum()))
    dark = a & ((r + g + b) / 3 < 60)
    side = ((np.nonzero(skin)[1].mean() - cx) / w if skin.sum() > 30 else 0) - ((np.nonzero(dark)[1].mean() - cx) / w if dark.sum() > 30 else 0)
    if sym > .88 and faceskin < .35: v = 'back'
    elif sym > .88 and faceskin > .55 and abs(side) < .06: v = 'front'
    elif abs(side) > .1 or sym < .82: v = 'profile'
    else: v = 'threequarter' if faceskin > .4 else 'threequarter_back'
    out.update({'est_view': v, 'faces': 'L' if side < -.03 else 'R' if side > .03 else None, 'sym': round(sym, 2), 'faceskin': round(faceskin, 2)})
    return out


FEATURE = [('eye', r'\beyes?\b|eye-|-eye|eyelid'), ('brow', r'brow'), ('mouth', r'mouth|\blips?\b|smile|grin|teeth|phoneme'), ('nose', r'\bnose')]


def feature_cards(cat, N, R):
    """Face features cut as their own cards (eyes, brows, mouths, noses) from the face and head sheets."""
    sheet_ppc = {}
    for pid, n in N.items():
        if n.get('px_per_cm'):
            sheet_ppc.setdefault(pid.split('/')[0], []).append(n['px_per_cm'])
    char = {pid.split('/')[0]: (n.get('character'), n.get('costume')) for pid, n in N.items()}
    out = []
    for sid, sh in cat.items():
        if not re.search(r'face|head|identit|nose', sid) or re.search(r'set\.|props?\.', sid):
            continue
        for p in sh['parts']:
            n = p['id'].split('/')[-1].lower()
            slot = next((k for k, pat in FEATURE if re.search(pat, n)), None)
            if not slot or R.get(p['id'], {}).get('q') == 'C':
                continue
            path = os.path.join(SHOTS, 'kits', 'cut', p['file'])
            w, h = Image.open(path).size
            side = 'L' if re.search(r'(^|-)l(-|$)|left', n) else 'R' if re.search(r'(^|-)r(-|$)|right', n) else None
            ch, co = char.get(sid, (re.split(r'[._]', sid)[0], None))
            out.append({'id': p['id'], 'img': '../kits/cut/' + p['file'], 'w': w, 'h': h, 'slot': slot, 'side': side, 'view': view_of(n), 'state': None,
                        'character': ch, 'costume': co, 'px_per_cm': round(statistics.median(sheet_ppc[sid]), 3) if sid in sheet_ppc else None,
                        'A': [w / 2, h / 2], 'B': [w / 2, h / 2], 'pts': 'centre', 'q': R.get(p['id'], {}).get('q'), 'label': p.get('name') or '',
                        'pair': slot in ('eye', 'brow') and side is None and w / max(1, h) > 2.2, 'brads': []})
    return out


def library():
    N = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'normalized.json')))['parts']
    cat = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'catalog.json')))['sheets']
    R = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'registry.json')))['parts']
    info = {p['id']: (p, sid) for sid, s in cat.items() for p in s['parts']}
    out = []
    for pid, n in N.items():
        if pid not in info or not n.get('px_per_cm') or R.get(pid, {}).get('q') == 'C':
            continue
        p, sid = info[pid]
        path = os.path.join(SHOTS, 'kits', 'cut', p['file'])
        A, B, how = points(path, n['slot'], p.get('brads') or [], n.get('view'))
        if A is None:
            continue
        w, h = Image.open(path).size
        out.append({'id': pid, 'img': '../kits/cut/' + p['file'], 'w': w, 'h': h, 'slot': n['slot'], 'side': n.get('side'), 'view': n.get('view'),
                    'state': n.get('state'), 'character': n.get('character'), 'costume': n.get('costume'), 'px_per_cm': n['px_per_cm'],
                    'A': [round(float(A[0]), 1), round(float(A[1]), 1)], 'B': [round(float(B[0]), 1), round(float(B[1]), 1)], 'pts': how,
                    'q': R.get(pid, {}).get('q'), 'label': p.get('name') or p.get('label') or '',
                    'brads': [[round(float(x), 1), round(float(y), 1)] for x, y in (p.get('brads') or [])]})
    out += pelvis_cards(cat, N, R) + feature_cards(cat, N, R)
    for c in out:
        c.update(analyse(os.path.join(SHOTS, 'kits', 'cut', c['img'][len('../kits/cut/'):]), c['slot']))
    # what CLIP learnt from the labelled cards (clip_label.py), and what people settled in the Skin Lab (labels.json,
    # exported from the page: view, painted face, facing, misfiled); a person's answer wins over everything else
    CL = json.load(open(os.path.join(HERE, 'clip.json'))) if os.path.exists(os.path.join(HERE, 'clip.json')) else {}
    HL = json.load(open(os.path.join(HERE, 'labels.json'))).get('cards', {}) if os.path.exists(os.path.join(HERE, 'labels.json')) else {}
    for c in out:
        r = CL.get(c['id'], {})
        c['clip'] = {k: r[k] for k in ('view_l', 'view_l_p', 'part', 'part_p', 'flags', 'kind', 'kind_p', 'pose', 'face', 'face_p') if k in r}
        h = HL.get(c['id'])
        if h:
            c['human'] = {k: h[k] for k in ('view', 'painted', 'left', 'bad', 'slot') if k in h}
    return out


def main():
    T, L = trials(), library()
    json.dump(T, open(os.path.join(HERE, 'trials.json'), 'w'))
    json.dump(L, open(os.path.join(HERE, 'library.json'), 'w'))
    from collections import Counter
    print(len(T), 'trials;', len(L), 'cards', Counter(c['slot'] for c in L), Counter(c['pts'] for c in L))
    H = [c for c in L if c['slot'] == 'head']
    G = lambda v: {'profile': 'side', 'front': 'front', 'threequarter': 'front', 'back': 'back', 'threequarter_back': 'back'}.get(v)
    print('heads: angle read from pixels', Counter(c['est_view'] for c in H), '| label vs pixels agree', sum(G(c['view']) == G(c['est_view']) for c in H if c['view']), 'of', sum(1 for c in H if c['view']))


if __name__ == '__main__':
    main()
