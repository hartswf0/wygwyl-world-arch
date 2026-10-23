"""Recognition test: pose the poet puppet (contracts/poet.json) into every painted pose of his kits, in the painting's
own view, and put puppet and painting side by side so a blind critic can say which painting each puppet is.

    python3 shots/skinlab/production/recognition/recognize.py [--all]

Source: shots/rig/poses/poet__red_black_sunglasses.json — 90 painted targets, each with the Pose Lab's 3D solve
(params in degrees on the Pose Lab skeleton, the view yaw psi, the painting's px/cm). FK and projection are the Pose
Lab's own (shots/rig/solve.py: fk, project). Default: the poem-relevant sheets poet.09 / poet.04 / poet.08.

Per-view mechanics (SCION_PUPPET_FOUNDRY.md 4b, the joint atlas): every segment's projected length over its 3D
length r decides the method —
  r >= .88        ROTATE   a rigid card turned in the picture plane (pinned at both joints, shortening <= 12%)
  .55 <= r < .88  OVERLAP  declared shortening capped at 12%; the card overruns its child joint and the child card
                           overlaps it (no replacement cards for limbs exist in the poet kits)
  r < .55         NEEDCARD a dedicated foreshortened card is needed and the kit has none: drawn squashed to r and
                           FLAGGED (a violation, counted, outlined red in the method panel)
  feet front/back DEDICATED the front/back boot cards (true size, upright on the ankle)
Side and three-quarter: cards drawn facing right, mirrored across their own axis when he faces left; the limb nearer
the camera (larger depth) is drawn over, the far one under and darkened. Facing screen-right the camera sees his
RIGHT side. Front: L/R cards as cut; hands and boots over the legs by the contract's front stack.

Writes shots/skinlab/production/recognition/poet/: pairs/<n>_<id>.jpg (painting | puppet | method panel, same height),
blind/<random>.jpg (puppet only), paintings_contact.jpg (numbered), key.json (the blind key: the critic must not read
it), methods.json (per pose, per segment: view, r, method), and ../index.html.
"""
import json, math, os, sys, random, hashlib
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SKIN = os.path.abspath(os.path.join(HERE, '..', '..'))
SHOTS = os.path.dirname(SKIN)
sys.path.insert(0, os.path.join(SHOTS, 'rig'))
import solve as SV  # noqa: E402  the Pose Lab's FK and projection

OUT = os.path.join(HERE, 'poet')
C = json.load(open(os.path.join(SKIN, 'contracts', 'poet.json')))
LIB = {c['id']: c for c in json.load(open(os.path.join(SKIN, 'library.json')))}
DOC = json.load(open(os.path.join(SHOTS, 'rig', 'poses', 'poet__red_black_sunglasses.json')))
SK = DOC['skeleton']
H_PANEL = 720                                   # every panel is drawn at this height
BG = (233, 226, 212)

# ---------------------------------------------------------------- cards
_IMG, _GEN, _PAD = {}, {}, {}
def card_img(cid):
    """RGBA of a card with the contract's erase / trim applied (fix[id].erase rectangles, fix[id].trim px)."""
    if cid in _IMG: return _IMG[cid]
    if cid.startswith('gen.') and 'built-seat' in cid:
        im, A, B, K = build_seat(cid); _IMG[cid] = im; _GEN[cid] = (A, B, K); return im
    c = LIB[cid]; im = np.array(Image.open(os.path.normpath(os.path.join(SKIN, c['img']))).convert('RGBA'))
    f = C['fix'].get(cid, {})
    if f.get('flare'):
        A, B = AB(cid); im, pad = flare(im, A, B, f['flare']); _PAD[cid] = pad
    for x0, y0, x1, y1 in f.get('erase', []): im[y0:y1, x0:x1, 3] = 0
    if f.get('trim'):
        r = int(f['trim']); k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        im[..., 3] = cv2.erode(im[..., 3], k)
    _IMG[cid] = im
    return im

def AB(cid, padded=False):
    if cid.startswith('gen.'):
        card_img(cid); A, B, _ = _GEN[cid]; return np.array(A, float), np.array(B, float)
    f = C['fix'].get(cid, {}); c = LIB[cid]
    A, B = np.array(f.get('A', c['A']), float), np.array(f.get('B', c['B']), float)
    if padded and cid in _PAD: A, B = A + [_PAD[cid], 0], B + [_PAD[cid], 0]
    return A, B

def ppc(cid):
    if cid.startswith('gen.'): card_img(cid); return _GEN[cid][2]
    return C['fix'].get(cid, {}).get('px_per_cm') or LIB[cid]['px_per_cm']

def left_drawn(cid):
    f = C['fix'].get(cid, {})
    if cid.startswith('gen.'): return f.get('left', False)
    c = LIB[cid]
    if 'left' in f: return f['left']
    h = (c.get('human') or {}).get('left')
    if h is not None: return h
    if c['slot'] == 'foot': A, B = AB(cid); return B[0] < A[0]
    return c.get('faces') == 'L'

# The contract's pelvis and torso cards are bound on the Skin Lab (Bolas) skeleton: waist 7 cm above the hip line,
# crotch 13 cm below it. The Pose Lab skeleton's 'waist' is 19.4 cm above the hips, so two virtual joints are made
# along the pelvis -> waist line: w7 (7 cm above the hip line) and crotch (13 cm below); the torso spans w7 -> neck
# and the pelvis card w7 -> crotch, exactly as in the Skin Lab. Declared in methods.json.
def virtual(J):
    p, w = J['pelvis'][0], J['waist'][0]; u = (w - p) / (np.linalg.norm(w - p) or 1)
    J['w7'] = (p + 7 * u)[None]; J['crotch'] = (p - 13 * u)[None]

# ---- cards built by code or reshaped by the contract (ports of puppet-core.js buildSeat / flared, Builder B's) ----
def smooth_outline(q, steps=8):
    n = len(q); mid = lambda i: (q[i % n] + q[(i + 1) % n]) / 2; out = []
    for i in range(n):
        a, c, b = mid(i), q[(i + 1) % n], mid(i + 1)
        for k in range(steps): t = k / steps; out.append((1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b)
    return np.array(out)

def build_seat(cid):
    o = C['fix'].get(cid, {}); K, m, hip = 8, 6, o.get('hip_cm', 7)
    out = np.array(o.get('outline') or [[5, -3], [-9, -3], [-11.5, 1], [-14.5, 6], [-17.5, 11], [-18, 15.5], [-16.5, 19.5], [-13, 23], [-9, 25.5], [-4, 24.5], [5, 20]], float)
    x0, y0 = out[:, 0].min(), out[:, 1].min()
    W = int(math.ceil((out[:, 0].max() - x0) * K + 2 * m)); Hp = int(math.ceil((out[:, 1].max() - y0) * K + 2 * m))
    Pt = lambda p: np.array([m + (p[0] - x0) * K, m + (p[1] - y0) * K])
    src = np.array(Image.open(os.path.join(SHOTS, 'kits', 'cut', o.get('from', 'poet.red_black_sunglasses.hipcore/5-rear-seat') + '.webp')).convert('RGBA'))
    ih, iw = src.shape[:2]; sx = o.get('src_rect') or [iw * .5, ih * .08, iw * .46, ih * .86]
    crop = Image.fromarray(src).crop((int(sx[0]), int(sx[1]), int(sx[0] + sx[2]), int(sx[1] + sx[3]))).transpose(Image.FLIP_LEFT_RIGHT).resize((W + 2 * m, Hp))
    fill = Image.new('RGBA', (W, Hp), (27, 26, 29, 255)); fill.paste(crop, (-m, 0), crop)
    poly = [tuple(Pt(p)) for p in smooth_outline(out)]
    mask = Image.new('L', (W, Hp), 0); ImageDraw.Draw(mask).polygon(poly, fill=255)
    yy, xx = np.mgrid[0:Hp, 0:W]; c0 = Pt([-6, 14]); rr = np.hypot(xx - c0[0], yy - c0[1]) / (16 * K)
    arr = np.array(fill).astype(np.float32); arr[..., :3] *= (1 - .38 * np.clip((rr - .55) / .45, 0, 1))[..., None]
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8)); img.putalpha(mask)
    d = ImageDraw.Draw(img); d.line(poly + [poly[0]], fill=(201, 162, 107, 255), width=5); d.line(poly + [poly[0]], fill=(107, 74, 42, 255), width=1)
    for b in ([0, 0], [0, hip]):
        q = Pt(b); d.ellipse([q[0] - 8, q[1] - 8, q[0] + 8, q[1] + 8], fill=(217, 166, 64, 255), outline=(122, 84, 16, 255), width=2)
        d.ellipse([q[0] - 3, q[1] - 4, q[0] + 1, q[1]], fill=(255, 243, 192, 255))
    return np.array(img), Pt([0, 0]), Pt([0, o.get('crotch_cm', 20)]), K

def flare(im, A, B, fl):
    h, w = im.shape[:2]; mx = max(fl[0], fl[1], 1); pad = int(math.ceil(w * (mx - 1) / 2)) + 2
    out = np.zeros((h, w + 2 * pad, 4), np.uint8)
    for y in range(h):
        t = max(0.0, min(1.0, (y - A[1]) / ((B[1] - A[1]) or 1))); k = fl[0] + (fl[1] - fl[0]) * t; ax = A[0] + (B[0] - A[0]) * t
        nw = max(1, int(round(w * k))); row = cv2.resize(im[y:y + 1], (nw, 1), interpolation=cv2.INTER_LINEAR)
        x0 = int(round(pad + ax - ax * k)); x0c = max(0, x0); x1 = min(out.shape[1], x0 + nw)
        out[y, x0c:x1] = row[0, x0c - x0:x1 - x0]
    return out, pad

SEGS = [  # name, from, to, contract limb
    ('pelvis', 'w7', 'crotch', 'pelvis'), ('torso', 'w7', 'neck', 'torso'), ('head', 'neck', 'top', 'head')]
for s in 'LR':
    SEGS += [('upper_arm_' + s, 'sh' + s, 'el' + s, 'upper_arm_' + s), ('forearm_' + s, 'el' + s, 'wr' + s, 'forearm_' + s),
             ('hand_' + s, 'wr' + s, 'tip' + s, 'hand_' + s), ('thigh_' + s, 'hip' + s, 'kn' + s, 'thigh_' + s),
             ('shin_' + s, 'kn' + s, 'an' + s, 'shin_' + s), ('foot_' + s, 'an' + s, 'toe' + s, 'foot_' + s)]

def view_of(psi):
    a = abs(((psi + 180) % 360) - 180)
    return 'front' if a < 22.5 else 'threequarter' if a < 67.5 else 'side' if a < 112.5 else 'back' if a > 157.5 else 'threequarter_back'

def cards_for(view):
    v = {'threequarter_back': 'back'}.get(view, view)
    out = {}
    for k, l in C['limbs'].items():
        cs = l['cards']
        out[k] = cs.get(v) or (cs.get('front') if v == 'threequarter' else None) or cs.get('side')
    return out

def stack_for(view):
    return C['stack']['side' if view in ('side', 'threequarter') else 'back' if view in ('back', 'threequarter_back') else 'front']

# ---------------------------------------------------------------- pose one painting
def pose(t, sol):
    psi = sol['psi']; view = view_of(psi); facing = 1 if ((psi + 360) % 360) < 180 else -1
    X = np.array([[sol['params'][n] for n in SV.PN]])
    J = SV.fk(SK, X); virtual(J)
    s_px = sol['scale_px_per_cm']; ox, oy = sol['params']['ox'], sol['params']['oy']
    P = {n: SV.project(v[0], psi, ox, oy) for n, v in J.items() if n != '_F'}
    scr = {n: np.array([p[0][0] * s_px + t['cx'], p[0][1] * s_px + t['floor']]) for n, p in P.items()}
    dep = {n: float(p[1]) for n, p in P.items()}
    cards = cards_for(view)
    near = {'arm': 'L' if dep['shL'] > dep['shR'] else 'R', 'leg': 'L' if dep['hipL'] > dep['hipR'] else 'R'}
    placed, report = [], {}
    for name, a, b, limb in SEGS:
        cid = cards.get(limb)
        if not cid: continue
        card_img(cid); A, B = AB(cid, padded=True)
        L3 = float(np.linalg.norm(J[b][0] - J[a][0])); d2 = scr[b] - scr[a]; L2 = float(np.linalg.norm(d2)) / s_px
        r = L2 / L3 if L3 > 1e-6 else 1.0
        lab = float(np.linalg.norm(B - A)) or 1.0
        foot = name.startswith('foot')
        side_cards = view in ('side', 'threequarter')
        if name == 'head':                            # the face must read: a head is never squashed or tucked away
            s = s_px * L3 / lab; along = 1.0
            up = scr['neck'] - scr['w7']; up = up / (np.linalg.norm(up) or 1)
            dd = d2 / (np.linalg.norm(d2) or 1)
            if r < .55: dd = up                       # looking at or away from the camera: stand the head on the neck line
            ang = math.atan2(dd[1], dd[0]); method = 'ROTATE' if r >= .55 else 'HEADUP'
        elif foot and not side_cards:                   # front/back boot: a dedicated card, upright on the ankle, true size
            method, ang, along, s = 'DEDICATED', math.pi / 2, 1.0, s_px / ppc(cid)
        else:
            s = s_px * L3 / lab                       # rigid at the bone's true 3D length
            if foot or C['fix'].get(cid, {}).get('rigid_ppc') or cid.startswith('gen.'): s = s_px / ppc(cid)   # boots and the seat at their claimed true size
            ang = math.atan2(d2[1], d2[0])
            if r >= .88: method, along = 'ROTATE', (r if not foot else 1.0)
            elif r >= .55: method, along = 'OVERLAP', .88
            else: method, along = 'NEEDCARD', max(r, .2)
        mir = side_cards and (facing < 0) != left_drawn(cid)
        ax = math.atan2(B[1] - A[1], B[0] - A[0])
        # card px -> screen px: P + R(ang) diag(along*s, s*m) R(-ax) (q - A)
        Rm = lambda th: np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
        L = Rm(ang) @ np.diag([along * s, s * (-1 if mir else 1)]) @ Rm(-ax)
        tvec = scr[a] - L @ A
        M = np.hstack([L, tvec[:, None]])
        sd = name[-1] if name[-2] == '_' else None
        part = name[:-2] if sd else name
        role = part if not sd else (('near_' if sd == near['arm' if part in ('upper_arm', 'forearm', 'hand') else 'leg'] else 'far_') + part)
        far = role.startswith('far_') and view != 'front'
        placed.append({'name': name, 'cid': cid, 'M': M, 'role': role, 'far': far, 'd': (dep[a] + dep[b]) / 2,
                       'P': scr[a], 'Q': scr[b], 'end': scr[a] + (L @ (B - A)), 'method': method})
        report[name] = {'card': cid, 'r': round(r, 3), 'method': method, 'role': role}
    st = stack_for(view)
    placed.sort(key=lambda x: (st.index(x['role']) if x['role'] in st else 99, x['d']))
    return {'view': view, 'psi': psi, 'facing': facing, 'placed': placed, 'report': report, 'near': near}

def render(t, ps, U):
    """the puppet on a canvas the size of the painting (U x), same px/cm, same floor and centre."""
    W, Hh = int(canvas_w(t) * U), int(t['h'] * U)
    canvas = np.zeros((Hh, W, 4), np.float32)
    S2 = np.array([[U, 0, U * (canvas_w(t) - t['w']) / 2], [0, U, 0]], float)
    for x in ps['placed']:
        im = card_img(x['cid'])
        M = S2[:, :2] @ x['M']; M[:, 2] += S2[:, 2]
        w = cv2.warpAffine(im, M, (W, Hh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)).astype(np.float32)
        if x['far']: w[..., :3] *= .62
        a = w[..., 3:4] / 255.0
        canvas[..., :3] = canvas[..., :3] * (1 - a) + w[..., :3] * a
        canvas[..., 3:4] = np.maximum(canvas[..., 3:4], w[..., 3:4])
    return Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), 'RGBA')

def canvas_w(t):   # wide enough for limbs that leave the painting's own box
    return max(t['w'], .75 * t['h'])

def padded_painting(t):
    im = Image.open(os.path.join(SHOTS, t['img'])).convert('RGBA'); W = int(canvas_w(t))
    out = Image.new('RGBA', (W, im.height), (0, 0, 0, 0)); out.paste(im, ((W - im.width) // 2, 0)); return out

def method_panel(puppet, ps, U):
    im = Image.new('RGBA', puppet.size, BG + (255,)); im.alpha_composite(Image.eval(puppet, lambda v: v).convert('RGBA'))
    fade = Image.new('RGBA', puppet.size, BG + (150,)); im.alpha_composite(fade)
    d = ImageDraw.Draw(im)
    col = {'ROTATE': (40, 150, 60), 'OVERLAP': (220, 140, 20), 'NEEDCARD': (210, 30, 30), 'DEDICATED': (40, 90, 200), 'HEADUP': (150, 60, 200)}
    for x in ps['placed']:
        off = np.array([U * ps['dx'], 0]); p, q = x['P'] * U + off, x['Q'] * U + off
        d.line([tuple(p), tuple(q)], fill=col[x['method']], width=max(3, int(2.2 * U)))
        d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=(30, 30, 30))
    return im

def panel(img, h, bg=BG):
    k = h / img.height; im = img.resize((max(1, int(img.width * k)), h), Image.LANCZOS)
    out = Image.new('RGB', im.size, bg); out.paste(im, (0, 0), im if im.mode == 'RGBA' else None); return out

def font(sz):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()

def main():
    allp = '--all' in sys.argv
    sheets = ('poet.09.main-poses', 'poet.04.main-poses', 'poet.08.main-poses')
    T = [t for t in DOC['targets'] if allp or t['sheet'] in sheets]
    for d in ('pairs', 'blind'):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
        for f in os.listdir(os.path.join(OUT, d)): os.remove(os.path.join(OUT, d, f))
    rng = random.Random(909)
    methods, key, skipped, rows = {}, {'blind': {}, 'paintings': {}}, [], []
    order = list(range(len(T))); rng.shuffle(order)
    paint_num = {T[i]['id']: n + 1 for n, i in enumerate(order)}    # painting numbers on the contact sheet (shuffled)
    F, Fs = font(22), font(16)
    for t in T:
        if not t.get('solves'):
            skipped.append({'id': t['id'], 'why': 'the Pose Lab has no solve for this painting'}); continue
        sol = t['solves'][0]
        ps = pose(t, sol)
        U = H_PANEL / t['h']
        pup = render(t, ps, U)
        paint = padded_painting(t); ps['dx'] = (canvas_w(t) - t['w']) / 2
        a, b, c = panel(paint, H_PANEL), panel(pup, H_PANEL), panel(method_panel(pup, ps, U), H_PANEL)
        gap = 24; top = 60; Wt = a.width + b.width + c.width + 4 * gap
        sheet = Image.new('RGB', (max(Wt, 760), H_PANEL + top + 70), BG); d = ImageDraw.Draw(sheet)
        x = gap
        for im, lab in ((a, 'painting'), (b, 'puppet'), (c, 'method')):
            sheet.paste(im, (x, top)); d.text((x, top - 26), lab, fill=(60, 50, 40), font=Fs); x += im.width + gap
        cnt = {}
        for v in ps['report'].values(): cnt[v['method']] = cnt.get(v['method'], 0) + 1
        d.text((gap, 12), f"{t['id']}   view {ps['view']} (psi {ps['psi']}, facing {'right' if ps['facing'] > 0 else 'left'})   solve IoU {sol.get('iou')}", fill=(30, 25, 20), font=Fs)
        d.text((gap, top + H_PANEL + 14), '  '.join(f'{k} {v}' for k, v in sorted(cnt.items())) + '   green rotate · amber 12% shortening + overlap · red needs a foreshortened card · blue dedicated boot card · violet head stood on the neck line', fill=(60, 50, 40), font=Fs)
        n = paint_num[t['id']]
        safe = t['id'].replace('/', '__')
        sheet.save(os.path.join(OUT, 'pairs', f'{n:02d}_{safe}.jpg'), quality=86)
        tok = hashlib.sha1((t['id'] + 'poet-blind-909').encode()).hexdigest()[:10]
        blind = Image.new('RGB', (b.width + 40, H_PANEL + 40), BG); blind.paste(b, (20, 20))
        blind.save(os.path.join(OUT, 'blind', tok + '.jpg'), quality=86)
        key['blind'][tok + '.jpg'] = {'painting_number': n, 'id': t['id']}
        key['paintings'][str(n)] = t['id']
        methods[t['id']] = {'number': n, 'view': ps['view'], 'psi': ps['psi'], 'facing': 'right' if ps['facing'] > 0 else 'left',
                            'near': ps['near'], 'solve_iou': sol.get('iou'), 'solve_err_cm': sol.get('mean_err_cm'), 'counts': cnt, 'segments': ps['report']}
        rows.append((n, safe, t['id'], ps['view'], cnt))
        print(f"{n:2d} {t['id'][:60]:60s} {ps['view']:12s} {cnt}")
    # numbered paintings contact sheet (in the shuffled numbering, so it does not give the blind key away)
    cells = sorted(((paint_num[t['id']], t) for t in T if t.get('solves')), key=lambda c: c[0])
    cw, ch, cols = 220, 330, 8
    cs = Image.new('RGB', (cols * cw, ((len(cells) + cols - 1) // cols) * ch), BG); d = ImageDraw.Draw(cs)
    for i, (n, t) in enumerate(cells):
        im = Image.open(os.path.join(SHOTS, t['img'])).convert('RGBA'); k = min((cw - 16) / im.width, (ch - 40) / im.height)
        im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
        x0, y0 = (i % cols) * cw, (i // cols) * ch
        cs.paste(im, (x0 + (cw - im.width) // 2, y0 + 34), im); d.text((x0 + 8, y0 + 6), str(n), fill=(20, 15, 10), font=F)
    cs.save(os.path.join(OUT, 'paintings_contact.jpg'), quality=86)
    json.dump(key, open(os.path.join(OUT, 'key.json'), 'w'), indent=1)
    json.dump({'about': 'per painting, per segment: the view, r = projected/3D length, and the method (ROTATE / OVERLAP / NEEDCARD / DEDICATED; see recognize.py)',
               'pelvis_mapping': 'the Pose Lab waist is 19.4 cm above the hip line; virtual w7 (7 cm above) and crotch (13 cm below) joints make the torso w7->neck and the pelvis w7->crotch, as on the Skin Lab skeleton the contract is bound on',
               'skipped': skipped, 'poses': methods}, open(os.path.join(OUT, 'methods.json'), 'w'), indent=1)
    # the page
    items = ''.join(f'<figure><img loading="lazy" src="poet/pairs/{n:02d}_{s}.jpg" alt="{i}"><figcaption>{n:02d} · {i} · {v} · ' +
                    ', '.join(f'{k} {c}' for k, c in sorted(cnt.items())) + '</figcaption></figure>' for n, s, i, v, cnt in sorted(rows))
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Poet recognition</title><style>
:root{{--bg:#efe7d8;--ink:#2a221c;--dim:#6b5d50}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#16120f;--ink:#efe6da;--dim:#9a8d7e}}}}
:root[data-theme="dark"]{{--bg:#16120f;--ink:#efe6da;--dim:#9a8d7e}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,sans-serif;padding:16px}}
h1{{font-size:20px;margin:0 0 6px}} p{{color:var(--dim);max-width:900px}}
figure{{margin:0 0 22px}} img{{max-width:100%;height:auto;display:block;border:1px solid #0002}}
figcaption{{color:var(--dim);font-size:12px;margin-top:4px}}
</style></head><body>
<h1>Poet recognition test: painting | puppet | method</h1>
<p>Each painted pose of the poet's kits (Pose Lab solve, the painting's own view and height) posed with the poet contract's cards. Method per segment from the joint atlas: green rotate a rigid card; amber declared 12% shortening plus overlap; red needs a foreshortened card the kit lacks (drawn squashed, flagged); blue dedicated front/back boot. Blind renders for the critic are in poet/blind/ with the numbered paintings in poet/paintings_contact.jpg; the key is poet/key.json (critics must not read it). Regenerate: python3 shots/skinlab/production/recognition/recognize.py</p>
{items}
<p>Skipped (no Pose Lab solve): {", ".join(s["id"] for s in skipped) or "none"}</p>
</body></html>'''
    open(os.path.join(HERE, 'index.html'), 'w').write(html)
    print('skipped', len(skipped), [s['id'] for s in skipped])

if __name__ == '__main__':
    main()
