"""Kit 3: one skeleton per character, and from it every cut chart, sprite-sheet template and socket.

    python3 shots/arena/parts/kit3/kit.py          # writes kit3/out/*.png and kit3/registry.json

The old parts were generated first and registered after: a model drew a card, then we guessed
where its brads were, and the guesses were off by up to 30px (the "hallucinated connection
points"). Kit 3 runs the other way. Each character has a rest skeleton in cm (x to its left,
y up, z forward). The cut chart (a butcher's diagram of the body), the exploded sprite-sheet
templates and the registry all come from that one skeleton, so a sketch, a template and the
rig cannot disagree about where a joint is. A generator, or an artist, paints INTO a template
whose brads are already placed: socket A and B are fixed by the template, never detected.

A part is plug and play: everything with the same slot (say man.hand.R) and the same sockets
can stand in for anything else in that slot, whether it is a generated card, a coded drawing
or a fusion of the two (a generated face plate with coded eyes that follow the bank's gaze).
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
SERIF = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
INK = (24, 22, 20)
PAPER = (252, 250, 245)
GHOST = (232, 227, 216)
ACCENT = {'man': (205, 48, 38), 'poet': (22, 104, 112), 'dot': (196, 150, 30)}


def font(path, n):
    return ImageFont.truetype(path, n)


# ------------------------------------------------------------------ characters
# joints in cm, rest pose (arms 12 degrees out so every piece shows in the front view)
def humanoid(H, sh, hip, head_r, neck=7.0, arm=(0.165, 0.145, 0.105), leg=(0.25, 0.235), foot=0.145, z=None):
    """A rest skeleton scaled to height H: shoulder half-width sh, hip half-width hip."""
    crown = H
    chin = H - 2 * head_r * 1.1
    neckb = chin - neck
    shy = neckb - 5
    hipy = H * 0.515
    knee = hipy - H * leg[0]
    ankle = max(6.0, knee - H * leg[1])
    ua, fa, hd = (H * a for a in arm)
    J = {'crown': (0, crown, 1), 'head': (0, crown - head_r * 1.1, 1), 'chin': (0, chin, 4), 'neck': (0, neckb, 0)}
    a = math.radians(12)
    for s, sg in (('L', 1), ('R', -1)):
        S = np.array([sg * sh, shy, -1.0])
        E = S + np.array([sg * math.sin(a) * ua, -math.cos(a) * ua, -2])
        W = E + np.array([sg * math.sin(a * .6) * fa, -math.cos(a * .6) * fa, 4])
        T = W + np.array([sg * math.sin(a * .4) * hd, -math.cos(a * .4) * hd, 2])
        P = np.array([sg * hip, hipy, 0.0])
        K = np.array([sg * (hip + 1), knee, 2.0])
        A = np.array([sg * (hip + 1.5), ankle, -2.0])
        J.update({'shoulder' + s: tuple(S), 'elbow' + s: tuple(E), 'wrist' + s: tuple(W), 'tip' + s: tuple(T),
                  'hip' + s: tuple(P), 'knee' + s: tuple(K), 'ankle' + s: tuple(A),
                  'heel' + s: (A[0], 0, -6), 'toe' + s: (A[0], 0, H * foot)})
    return J


CHARS = {
    'man': {
        'label': 'The man', 'plays': 'Shim', 'height': 186,
        'look': 'black track jacket with red piping running from the shoulder seam down the chest, stand-up collar, zip, elastic cuffs and hem; black track trousers with an elastic waist and drawstring; black Chelsea boots; black sunglasses; short faded haircut and full beard; dark brown skin',
        'J': humanoid(186, 21, 9.5, 12.0),
        'w': {'uarm': (13, 11), 'farm': (11, 9), 'hand': (9, 8), 'thigh': (20, 14), 'shin': (14, 10)},
        'torso_front': [(-7, 0), (-19, -3), (-24, -8), (-23, -22), (-19, -30), (-18, -50), (-20, -60), (20, -60), (18, -50), (19, -30), (23, -22), (24, -8), (19, -3), (7, 0)],
        'torso_profile': [(-4, 0), (-11, -4), (-13, -20), (-12, -45), (-13, -60), (13, -60), (12, -45), (14, -22), (11, -6), (6, 0)],
        'pelvis': None,
        'face': ['eyes', 'brows', 'mouth', 'glasses'],
        'hair': None,
        'feet': 'boot',
    },
    'poet': {
        'label': 'The poet', 'plays': 'Bola', 'height': 172,
        'look': 'teal dress with a gold floral print, fitted sleeveless bodice and an A-line skirt to the knee; brown arms with a slim gold bangle; full rounded afro; dark brown skin; flat dark teal shoes',
        'J': humanoid(172, 18, 9.0, 11.0),
        'w': {'uarm': (9.5, 8), 'farm': (8, 6.5), 'hand': (7.5, 6.5), 'thigh': (16, 11), 'shin': (11, 7.5)},
        'torso_front': [(-6, 0), (-15, -3), (-19, -8), (-17, -22), (-15, -34), (-14, -46), (14, -46), (15, -34), (17, -22), (19, -8), (15, -3), (6, 0)],
        'torso_profile': [(-4, 0), (-10, -5), (-11, -22), (-9, -46), (11, -46), (13, -24), (11, -10), (6, 0)],
        'pelvis': 'skirt',
        'face': ['eyes', 'brows', 'mouth'],
        'hair': 'afro',
        'feet': 'flat',
    },
    'dot': {
        'label': 'Dot, the little one', 'plays': 'Dot', 'height': 105,
        'look': 'a crash-test dummy in mustard-yellow painted cardboard: round head with black-and-yellow crash targets on both sides and a small red bow on top, segmented body with brass brads, red stripe down the chest, mitten hands, flat little feet',
        'J': humanoid(105, 12.5, 6.0, 12.5, neck=3.0, arm=(0.15, 0.135, 0.09), leg=(0.2, 0.2), foot=0.15),
        'w': {'uarm': (7, 6), 'farm': (6, 5.5), 'hand': (6.5, 6), 'thigh': (10, 8), 'shin': (8, 7)},
        'torso_front': [(-4, 0), (-10, -2), (-13, -6), (-12, -18), (-11, -26), (11, -26), (12, -18), (13, -6), (10, -2), (4, 0)],
        'torso_profile': [(-3, 0), (-8, -4), (-8, -26), (8, -26), (9, -6), (4, 0)],
        'pelvis': None,
        'face': ['eyes', 'brows', 'mouth'],
        'hair': 'bow',
        'feet': 'dummy',
    },
}

# the cut list, numbered like a butcher's chart; slot names are what the rig plugs by
PIECES = [
    (1, 'head', 'head plate, blank: no eyes, brows or mouth painted on (they plug in)'),
    (2, 'torso', 'torso: jacket / bodice / dummy chest, neck tab tucked under the head'),
    (3, 'pelvis', 'skirt (the poet only): hangs from the waist, thighs hidden under it'),
    (4, 'uarm.L', 'upper arm, left'), (5, 'uarm.R', 'upper arm, right'),
    (6, 'farm.L', 'forearm with cuff, left'), (7, 'farm.R', 'forearm with cuff, right'),
    (8, 'hand.L', 'hand, left: plug-in, 12 shapes x back/palm'), (9, 'hand.R', 'hand, right: plug-in'),
    (10, 'thigh.L', 'thigh, left: rounded seat end tucks under the hem'), (11, 'thigh.R', 'thigh, right'),
    (12, 'shin.L', 'shin, left'), (13, 'shin.R', 'shin, right'),
    (14, 'foot.L', 'boot / shoe, left: plug-in'), (15, 'foot.R', 'boot / shoe, right: plug-in'),
    (16, 'eyes', 'eyes: plug-in on the eye line (pair, gaze moves the pupils)'),
    (17, 'brows', 'brows: plug-in above the eye line'),
    (18, 'mouth', 'mouth: plug-in at the mouth anchor (expressions and mouth shapes)'),
    (19, 'glasses', 'sunglasses (the man): plug-in over the eyes, on or off'),
    (20, 'hair', 'hair or mark behind the head: the poet\'s afro back, Dot\'s bow'),
]
NUM = {k: n for n, k, _ in PIECES}
LIMBS = [('uarm', 'shoulder', 'elbow'), ('farm', 'elbow', 'wrist'), ('hand', 'wrist', 'tip'), ('thigh', 'hip', 'knee'), ('shin', 'knee', 'ankle')]


# ------------------------------------------------------------------ geometry
def capsule(a, b, wa, wb, n=14):
    """A tapered card between two joints, round at both ends: the overlap disc at each brad."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    L = np.linalg.norm(d)
    u = d / L if L > 1e-6 else np.array([0, -1.0])
    p = np.array([-u[1], u[0]])
    ang0 = math.atan2(p[1], p[0])
    pts = []
    for t in np.linspace(0, math.pi, n):
        pts.append(b + (p * math.cos(t) - u * math.sin(t) * -1) * 0 + np.array([math.cos(ang0 + math.pi + t), math.sin(ang0 + math.pi + t)]) * wb / 2)
    for t in np.linspace(0, math.pi, n):
        pts.append(a + np.array([math.cos(ang0 + t), math.sin(ang0 + t)]) * wa / 2)
    return pts


def ellipse(c, rx, ry, n=48):
    return [(c[0] + rx * math.cos(t), c[1] + ry * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def view_xy(p, view):
    """front: x across (the character's left on screen right, as a puppet faces you), y up.
    profile: z across (facing screen right), y up."""
    x, y, z = p
    return (x, y) if view == 'front' else (z, y)


def shapes(cid, view):
    """Every piece as a 2D polygon in cm for one view, in drawing order (far to near)."""
    C = CHARS[cid]
    J = {k: np.array(view_xy(v, view), float) for k, v in C['J'].items()}
    W = C['w']
    out = []
    sides = ('R', 'L') if view == 'front' else ('R', 'L')     # profile: the right side is the far side
    for s in sides:
        for kind, a, b in LIMBS[3:]:
            if C['pelvis'] == 'skirt' and kind == 'thigh':
                continue
            out.append((f'{kind}.{s}', capsule(J[a + s], J[b + s], *W[kind]), (a + s, b + s)))
        out.append((f'foot.{s}', foot(J, s, C, view), ('ankle' + s, 'toe' + s)))
    if C['pelvis'] == 'skirt':
        hy = C['J']['hipL'][1] + 6
        hem = C['J']['kneeL'][1] + 4
        if view == 'front':
            sk = [(-15, hy), (15, hy), (24, hem), (-24, hem)]
        else:
            sk = [(-10, hy), (11, hy), (16, hem), (-15, hem)]
        out.append(('pelvis', sk, ('hipL', 'hipR')))
    top = np.array(view_xy(C['J']['neck'], view))
    tor = C['torso_front'] if view == 'front' else C['torso_profile']
    far_arm = [s for s in sides][:1] if view == 'profile' else []
    for s in far_arm:
        for kind, a, b in LIMBS[:3]:
            out.append((f'{kind}.{s}', capsule(J[a + s], J[b + s], *W[kind]), (a + s, b + s)))
    out.append(('torso', [(top[0] + x, top[1] + y) for x, y in tor], ('neck', 'hipL')))
    for s in ([x for x in sides if x not in far_arm]):
        for kind, a, b in LIMBS[:3]:
            out.append((f'{kind}.{s}', capsule(J[a + s], J[b + s], *W[kind]), (a + s, b + s)))
    hc = J['head']
    r = (C['J']['crown'][1] - C['J']['head'][1])
    nw = {'man': 9.0, 'poet': 7.0, 'dot': 5.0}[cid]
    nk = J['neck']
    out.append(('neck', [(nk[0] - nw / 2, nk[1] - 3), (nk[0] + nw / 2, nk[1] - 3), (hc[0] + nw / 2, hc[1]), (hc[0] - nw / 2, hc[1])], ('neck', 'head')))
    if C['hair'] == 'afro':
        out.append(('hair', ellipse(hc + np.array([-2 if view == 'profile' else 0, 3]), r * 1.45, r * 1.3), ('head', 'crown')))
    out.append(('head', ellipse(hc, r * (0.78 if cid != 'dot' else 1.0) * (1.05 if view == 'profile' else 1), r * 1.08), ('neck', 'crown')))
    return out, J


def foot(J, s, C, view):
    a = J['ankle' + s]
    L = C['height'] * 0.145
    h = max(7.0, C['height'] * 0.05)
    if view == 'front':
        return [(a[0] - h * .6, a[1] + 3), (a[0] + h * .6, a[1] + 3), (a[0] + h * .7, 0), (a[0] - h * .7, 0)]
    return [(a[0] - 6, a[1] + 4), (a[0] + 3, a[1] + 4), (a[0] + 6, 4), (a[0] + L - 6, 4), (a[0] + L - 4, 0), (a[0] - 7, 0)]


# ------------------------------------------------------------------ drawing
def dashed(d, p, q, col, w, dash=9, gap=6):
    p, q = np.asarray(p, float), np.asarray(q, float)
    L = np.linalg.norm(q - p)
    if L < 1:
        return
    u = (q - p) / L
    t = 0
    while t < L:
        a, b = p + u * t, p + u * min(L, t + dash)
        d.line([tuple(a), tuple(b)], fill=col, width=w)
        t += dash + gap


def brad(d, c, r, col=(184, 144, 47)):
    d.ellipse([c[0] - r - 1.5, c[1] - r - 1.5, c[0] + r + 1.5, c[1] + r + 1.5], fill=INK)
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=col)


def cut_chart(cid, s=None):
    """The butcher's chart: one outline per view, dashed cuts where cards meet, every piece
    numbered, brads at the joints, face plug-ins dotted on the head."""
    C = CHARS[cid]
    acc = ACCENT[cid]
    H = C['height']
    s = s or (3.2 if cid != 'dot' else 5.4)
    pad = 60
    vw = int(80 * s) if cid != 'dot' else int(60 * s)
    views = ('front', 'profile')
    Wd = pad * 2 + len(views) * (vw + int(40 * s)) + 760
    Hd = max(int(H * s + pad * 2 + 120), 820)
    im = Image.new('RGB', (Wd, Hd), PAPER)
    d = ImageDraw.Draw(im)
    f_num, f_lab, f_title = font(FONTB, 22), font(FONT, 17), font(SERIF, 34)
    d.text((pad, 24), f"{C['label'].upper()}  ·  CUT CHART", font=f_title, fill=INK)
    d.text((pad, 66), f"plays {C['plays']} · {H} cm · every piece is one cardboard card, brads at the joints", font=f_lab, fill=(110, 100, 90))
    x0 = pad
    for view in views:
        sh, J = shapes(cid, view)
        org = np.array([x0 + vw / 2 + int(20 * s), pad + 110 + H * s])
        P = lambda p: tuple(org + np.array([p[0] * s, -p[1] * s]))
        # union silhouette, then its outline
        mask = Image.new('L', im.size, 0)
        md = ImageDraw.Draw(mask)
        for name, poly, _ in sh:
            md.polygon([P(p) for p in poly], fill=255)
        m = np.asarray(mask) > 0
        edge = m & ~nd.binary_erosion(m, iterations=3)
        a = np.asarray(im).copy()
        a[edge] = INK
        im.paste(Image.fromarray(a))
        d = ImageDraw.Draw(im)
        # dashed cuts: each card's own outline where it lies over the body (the cow's dashed lines)
        for name, poly, _ in sh:
            pts = [P(p) for p in poly]
            for i in range(len(pts)):
                p, q = pts[i], pts[(i + 1) % len(pts)]
                mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                inside = all(0 <= int(v) < lim and m[int(min(max(mid[1] + dy, 0), lim2 - 1)), int(min(max(mid[0] + dx, 0), lim - 1))]
                             for v, lim, lim2 in ((mid[0], im.size[0], im.size[1]),) for dx, dy in ((4, 4), (-4, -4), (4, -4), (-4, 4)))
                if inside:
                    dashed(d, p, q, INK, 2, dash=7, gap=6)
        # character lines in the accent: the man's piping, the poet's hem, Dot's stripe
        top = np.array(view_xy(C['J']['neck'], view))
        if cid == 'man':
            for sx in ((-14, 14) if view == 'front' else (6,)):
                d.line([P(top + np.array([sx * 1.2, -4])), P(top + np.array([sx * .8, -30])), P(top + np.array([sx * .9, -50]))], fill=acc, width=4)
        if cid == 'dot':
            d.line([P(top + np.array([4 if view == 'front' else 3, -4])), P(top + np.array([4 if view == 'front' else 3, -22]))], fill=(180, 40, 30), width=5)
        # brads
        for k in ('shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'wristL', 'wristR', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR', 'neck'):
            if view == 'profile' and k.endswith('R'):
                continue
            brad(d, P(J[k]), 5)
        # face plug-in zones
        hc = J['head']
        r = C['J']['crown'][1] - C['J']['head'][1]
        fx = 0 if view == 'front' else r * 0.45
        eye = hc + np.array([fx, r * .15])
        if view == 'front':
            for ex in (-r * .32, r * .32):
                d.ellipse([P(eye + np.array([ex - 2.5, 1.8])), P(eye + np.array([ex + 2.5, -1.8]))], outline=acc, width=3)
        else:
            d.ellipse([P(eye + np.array([-2.5, 1.8])), P(eye + np.array([2.5, -1.8]))], outline=acc, width=3)
        dashed(d, P(eye + np.array([-r * .6 if view == 'front' else -3, 4])), P(eye + np.array([r * .6 if view == 'front' else 5, 4])), acc, 3, 5, 4)
        mo = hc + np.array([fx + (1.5 if view == 'profile' else 0), -r * .45])
        dashed(d, P(mo + np.array([-4, 0])), P(mo + np.array([4, 0])), acc, 3, 5, 4)
        if cid == 'man':
            d.rectangle([P(eye + np.array([-r * .62 if view == 'front' else -2, 2.6])), P(eye + np.array([r * .62 if view == 'front' else 6, -2.6]))], outline=INK, width=2)
        # numbers
        seen = set()
        for name, poly, (ja, jb) in sh:
            if view == 'profile' and name.endswith('.R'):
                continue
            n = NUM.get(name)
            if not n or n in seen:
                continue
            seen.add(n)
            c = np.mean(np.array(poly), axis=0)
            if name == 'head':
                c = hc + np.array([-r * .45 if view == 'front' else -r * .3, r * .55])
            if name == 'hair':
                c = hc + np.array([-r * 1.05 if view == 'profile' else r * 1.05, r * .9])
            q = P(c)
            d.text(q, str(n), font=f_num, fill=INK, anchor='mm')
        for n, c in ((16, eye + np.array([r * (.95 if view == 'front' else .9), r * .25])), (18, mo + np.array([r * .8, -r * .1]))):
            d.text(P(c), str(n), font=font(FONTB, 18), fill=acc, anchor='mm')
        d.text((org[0], org[1] + 40), view.upper(), font=font(FONTB, 18), fill=(110, 100, 90), anchor='mm')
        x0 += vw + int(40 * s)
    # legend
    lx = x0 + 20
    y = 120
    d.text((lx, y - 34), 'THE CUTS', font=font(FONTB, 20), fill=INK)
    for n, k, txt in PIECES:
        if k == 'pelvis' and C['pelvis'] != 'skirt':
            txt = 'no pelvis card: the thighs\' seat ends tuck under the hem'
        if k == 'glasses' and cid != 'man':
            continue
        if k == 'hair' and not C['hair']:
            continue
        if k == 'thigh.L' and C['pelvis'] == 'skirt':
            txt = 'thigh, left: drawn, but only shows in a kick or a sit'
        col = acc if n >= 16 else INK
        d.text((lx, y), f'{n:>2}', font=font(FONTB, 17), fill=col)
        d.text((lx + 36, y), txt, font=f_lab, fill=INK)
        y += 26
    y += 14
    d.text((lx, y), 'brass dot = brad (socket A on the nearer card, B on the farther)', font=font(FONT, 15), fill=(110, 100, 90))
    d.text((lx, y + 22), 'dashed = the cut: where one card tucks under another', font=font(FONT, 15), fill=(110, 100, 90))
    d.text((lx, y + 44), 'coloured = plug-ins: generated, coded or both', font=font(FONT, 15), fill=acc)
    return im


# ------------------------------------------------------------------ templates
SHEET_W, SHEET_H = 2048, 1152


def sheet_frame(title, sub, pxcm):
    im = Image.new('RGB', (SHEET_W, SHEET_H), PAPER)
    d = ImageDraw.Draw(im)
    d.text((36, 26), title, font=font(FONTB, 26), fill=INK)
    d.text((36, 62), sub, font=font(FONT, 16), fill=(110, 100, 90))
    # a 10 cm ruler and registration marks: the sheet's scale is part of the template
    rx = SHEET_W - 36 - 10 * pxcm
    d.line([(rx, 44), (rx + 10 * pxcm, 44)], fill=INK, width=3)
    for t in range(11):
        h = 10 if t % 5 == 0 else 5
        d.line([(rx + t * pxcm, 44 - h), (rx + t * pxcm, 44)], fill=INK, width=2)
    d.text((rx + 5 * pxcm, 58), f'10 cm = {10 * pxcm:g} px', font=font(MONO, 14), fill=INK, anchor='ma')
    for cx, cy in ((18, 18), (SHEET_W - 18, 18), (18, SHEET_H - 18), (SHEET_W - 18, SHEET_H - 18)):
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], outline=INK, width=2)
        d.line([(cx - 14, cy), (cx + 14, cy)], fill=INK, width=1)
        d.line([(cx, cy - 14), (cx, cy + 14)], fill=INK, width=1)
    return im, d


def cross(d, c, col, label=None, r=11):
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=col, width=3)
    d.line([(c[0] - r - 6, c[1]), (c[0] + r + 6, c[1])], fill=col, width=2)
    d.line([(c[0], c[1] - r - 6), (c[0], c[1] + r + 6)], fill=col, width=2)
    if label:
        d.text((c[0] + r + 8, c[1] - 9), label, font=font(MONO, 14), fill=col)


SOCK_A, SOCK_B = (34, 139, 70), (200, 52, 40)


def body_template(cid, view, registry, label=None):
    """One view's body pieces, exploded and upright, at one scale: ghost shapes to paint in,
    brads fixed. Limbs hang A (top) to B (bottom), as the rig expects."""
    C = CHARS[cid]
    sh, J = shapes(cid, view)
    pxcm = 6.0 if cid != 'dot' else 9.0
    label = label or view
    im, d = sheet_frame(f'{cid}.body.{label}', f"{C['label']} · body cards, {label} view · paint inside each ghost; keep every brad on its cross; one card per cell; transparent or white ground", pxcm)
    cells = [n for n, _, _ in sh if n not in ('head', 'hair', 'neck') and not (view == 'profile' and n.endswith('.R'))]
    order = ['torso', 'pelvis', 'uarm.L', 'farm.L', 'hand.L', 'uarm.R', 'farm.R', 'hand.R', 'thigh.L', 'shin.L', 'foot.L', 'thigh.R', 'shin.R', 'foot.R']
    cells = [c for c in order if c in cells]
    x, y, rowh = 60, 120, 0
    by = {n: (p, js) for n, p, js in sh}
    for name in cells:
        poly, (ja, jb) = by[name]
        P = np.array(poly)
        A = np.array(J[ja]) if ja in J else P.mean(0)
        B = np.array(J[jb]) if jb in J else P.mean(0)
        if name == 'torso':
            A, B = np.array(J['neck']), np.array([J['neck'][0], J['hipL'][1]])
        if name == 'pelvis':
            A = np.array([0.0, CHARS[cid]['J']['hipL'][1] + 6])
            B = np.array([0.0, CHARS[cid]['J']['kneeL'][1] + 4])
        # turn the card so A->B points straight down
        v = B - A
        th = -math.atan2(v[0], -v[1]) if name not in ('foot.L', 'foot.R', 'torso', 'pelvis') else 0
        R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
        Q = (P - A) @ R.T
        Bq = (B - A) @ R.T
        mn, mx = Q.min(0), Q.max(0)
        w, h = (mx[0] - mn[0]) * pxcm, (mx[1] - mn[1]) * pxcm
        if x + w + 60 > SHEET_W:
            x, y, rowh = 60, y + rowh + 70, 0
        org = np.array([x - mn[0] * pxcm, y + mx[1] * pxcm])
        T = lambda q: (org[0] + q[0] * pxcm, org[1] - q[1] * pxcm)
        pts = [T(q) for q in Q]
        d.polygon(pts, fill=GHOST)
        for i in range(len(pts)):
            dashed(d, pts[i], pts[(i + 1) % len(pts)], (150, 140, 128), 2, 6, 5)
        a_px, b_px = T((0, 0)), T(Bq)
        if name not in ('foot.L', 'foot.R'):
            d.ellipse([a_px[0] - (C['w'].get(name.split('.')[0], (8, 8))[0] / 2) * pxcm, a_px[1] - (C['w'].get(name.split('.')[0], (8, 8))[0] / 2) * pxcm,
                       a_px[0] + (C['w'].get(name.split('.')[0], (8, 8))[0] / 2) * pxcm, a_px[1] + (C['w'].get(name.split('.')[0], (8, 8))[0] / 2) * pxcm],
                      outline=(150, 140, 128), width=1)
        extra = {}
        if name in ('torso', 'pelvis'):
            # the torso carries the sockets the arms and thighs pin to: placed, never guessed
            for k in (('shoulderL', 'shoulderR', 'hipL', 'hipR') if name == 'torso' else ('hipL', 'hipR')):
                if view == 'profile' and k.endswith('R'):
                    continue
                if C['pelvis'] == 'skirt' and name == 'torso' and k.startswith('hip'):
                    continue
                q = T((np.array(J[k]) - A) @ R.T)
                cross(d, q, (60, 90, 170), k.replace('shoulder', 'sh.'), r=8)
                extra[k] = [round(q[0], 1), round(q[1], 1)]
        cross(d, a_px, SOCK_A, 'A')
        if name not in ('torso', 'pelvis', 'foot.L', 'foot.R'):
            cross(d, b_px, SOCK_B, 'B')
        d.text((x, y + h + 14), f"{NUM.get(name, '')}  {name}", font=font(FONTB, 16), fill=INK)
        d.text((x, y + h + 34), f"{np.linalg.norm(B - A):.0f} cm A-B", font=font(MONO, 13), fill=(110, 100, 90))
        registry.setdefault(cid, {}).setdefault(f'body.{label}', {})[name] = {
            'A': [round(a_px[0], 1), round(a_px[1], 1)], 'B': [round(b_px[0], 1), round(b_px[1], 1)],
            'cm': round(float(np.linalg.norm(B - A)), 1), 'px_per_cm': pxcm,
            'cell': [int(x), int(y), int(w), int(h)], **({'sockets': extra} if extra else {})}
        x += w + 70
        rowh = max(rowh, h + 40)
    return im


HAND_SHAPES = ['relaxed', 'open', 'fist', 'grip', 'pinch', 'point', 'thumb', 'peace', 'wave', 'claw', 'cup', 'flat_push']


def hands_template(cid, registry):
    """Twelve shapes, back and palm, one hand per cell: wrist eyelet on the green cross, the
    hand's axis along the dashed line to the red cross (the knuckle line). Right hand only:
    the left is the mirror."""
    C = CHARS[cid]
    pxcm = 11.0 if cid != 'dot' else 16.0
    L = np.linalg.norm(np.array(C['J']['tipL']) - np.array(C['J']['wristL']))
    im, d = sheet_frame(f'{cid}.hands.R', f"{C['label']} · right hand, 12 shapes x back / palm · eyelet on the green cross, fingers toward the red; {L:.0f} cm wrist to fingertip", pxcm)
    cw, ch = (SHEET_W - 120) / 6, (SHEET_H - 150) / 4
    for i, shape in enumerate(HAND_SHAPES):
        for k, face in enumerate(('back', 'palm')):
            col, row = i % 6, (i // 6) * 2 + k
            x0, y0 = 60 + col * cw, 120 + row * ch
            d.rectangle([x0 + 4, y0 + 4, x0 + cw - 4, y0 + ch - 4], outline=(220, 214, 204), width=1)
            a = (x0 + 34, y0 + ch / 2)
            b = (a[0] + L * 0.55 * pxcm, a[1])
            dashed(d, a, (a[0] + L * pxcm, a[1]), (170, 160, 148), 2, 6, 6)
            d.ellipse([a[0] - 4.5 * pxcm / 2, a[1] - 4.5 * pxcm / 2, a[0] + 4.5 * pxcm / 2, a[1] + 4.5 * pxcm / 2], fill=GHOST)
            cross(d, a, SOCK_A)
            cross(d, b, SOCK_B, r=7)
            d.text((x0 + 12, y0 + 10), f'{shape} · {face}', font=font(FONTB, 14), fill=INK)
            registry.setdefault(cid, {}).setdefault('hands.R', {})[f'{shape}.{face}'] = {
                'A': [round(a[0], 1), round(a[1], 1)], 'B': [round(b[0], 1), round(b[1], 1)], 'px_per_cm': pxcm}
    return im


EYES = ['open', 'wide', 'half', 'closed', 'squint', 'happy_arc', 'sad', 'glance_side']
BROWS = ['rest', 'raised', 'knit', 'sad', 'one_up', 'angry']
MOUTHS = ['rest', 'smile', 'grin_teeth', 'open_O', 'open_A', 'E', 'U', 'M_B_P', 'F_V', 'frown', 'strain_teeth', 'wavy']


def face_template(cid, view, registry):
    """The face plug-ins for one view: a blank head plate with its anchors, and grids of eyes,
    brows and mouths, each centred on its anchor cross so any one drops onto any plate."""
    C = CHARS[cid]
    r = C['J']['crown'][1] - C['J']['head'][1]
    pxcm = 14.0 if cid != 'dot' else 12.0
    im, d = sheet_frame(f'{cid}.face.{view}', f"{C['label']} · face plug-ins, {view} · the plate is painted with NO eyes, brows or mouth; every feature centred on its cross", pxcm)
    # the plate
    hc = (60 + r * 1.2 * pxcm, 140 + r * 1.25 * pxcm)
    rx, ry = r * (0.78 if cid != 'dot' else 1) * pxcm, r * 1.08 * pxcm
    if view == 'profile':
        rx *= 1.05
    d.ellipse([hc[0] - rx, hc[1] - ry, hc[0] + rx, hc[1] + ry], fill=GHOST)
    fx = 0 if view == 'front' else r * .45 * pxcm
    anchors = {'eyes': (hc[0] + fx, hc[1] - r * .15 * pxcm), 'brows': (hc[0] + fx, hc[1] - r * .38 * pxcm), 'mouth': (hc[0] + fx, hc[1] + r * .45 * pxcm),
               'neck': (hc[0], hc[1] + ry), 'crown': (hc[0], hc[1] - ry)}
    for k, c in anchors.items():
        cross(d, c, SOCK_A if k in ('neck', 'crown') else ACCENT[cid], k, r=8)
    d.text((hc[0] - rx, hc[1] + ry + 50), '1  head plate (blank)', font=font(FONTB, 16), fill=INK)
    reg = registry.setdefault(cid, {}).setdefault(f'face.{view}', {})
    reg['plate'] = {k: [round(v[0], 1), round(v[1], 1)] for k, v in anchors.items()}
    reg['px_per_cm'] = pxcm
    # feature grids
    gx0 = hc[0] + rx + 80
    rows = [('eyes', EYES, 8, 2 * r * .32 * pxcm + 6 * pxcm), ('brows', BROWS, 6, 2 * r * .32 * pxcm + 6 * pxcm), ('mouth', MOUTHS, 12, 9 * pxcm)]
    y = 130
    for slot, names, n, cwmin in rows:
        cols = 6 if n > 6 else n
        cw = (SHEET_W - gx0 - 40) / cols
        chh = 120 if slot != 'mouth' else 110
        d.text((gx0, y - 6), f"{NUM[slot]}  {slot}", font=font(FONTB, 16), fill=ACCENT[cid])
        y += 18
        for i, nm in enumerate(names):
            cx, cy = gx0 + (i % cols) * cw + cw / 2, y + (i // cols) * chh + chh / 2
            d.rectangle([cx - cw / 2 + 4, cy - chh / 2 + 4, cx + cw / 2 - 4, cy + chh / 2 - 4], outline=(220, 214, 204), width=1)
            if slot == 'eyes' and view == 'front':
                for ex in (-r * .32 * pxcm, r * .32 * pxcm):
                    d.ellipse([cx + ex - 2.4 * pxcm, cy - 1.6 * pxcm, cx + ex + 2.4 * pxcm, cy + 1.6 * pxcm], fill=GHOST)
            cross(d, (cx, cy), ACCENT[cid], r=6)
            d.text((cx - cw / 2 + 10, cy - chh / 2 + 8), nm, font=font(MONO, 13), fill=INK)
            reg.setdefault(slot, {})[nm] = [round(cx, 1), round(cy, 1)]
        y += chh * math.ceil(n / cols) + 16
    return im


HEAD_VIEWS = ['front', 'threequarter', 'profile', 'threequarter_back', 'back']


def heads_template(cid, registry):
    """Blank head plates in five views (screen-right facing; the rig mirrors for screen-left):
    neck tab on the green cross, crown on the red, the eye line and mouth anchors marked
    where the face plug-ins land. Eyes, brows and mouth are NOT painted: they plug in."""
    C = CHARS[cid]
    r = C['J']['crown'][1] - C['J']['head'][1]
    pxcm = 12.0 if cid != 'dot' else 11.0
    im, d = sheet_frame(f'{cid}.heads.blank', f"{C['label']} · head plates, five views, NO eyes / brows / mouth (they plug in) · neck tab on green, crown on red", pxcm)
    cw = (SHEET_W - 120) / 5
    reg = registry.setdefault(cid, {}).setdefault('heads.blank', {})
    for i, v in enumerate(HEAD_VIEWS):
        cx, cy = 60 + cw * i + cw / 2, 560
        rx, ry = r * (0.8 if cid != 'dot' else 1) * pxcm * (1.05 if 'profile' in v else 1), r * 1.08 * pxcm
        if C['hair'] == 'afro':
            d.ellipse([cx - rx * 1.42, cy - ry * 1.3 - 10, cx + rx * 1.42, cy + ry * .95 - 10], fill=(240, 236, 228))
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=GHOST)
        neck = (cx, cy + ry + 6 * pxcm)
        d.rectangle([cx - 4 * pxcm, cy + ry * .6, cx + 4 * pxcm, neck[1]], fill=GHOST)
        crown = (cx, cy - ry)
        turn = {'front': 0, 'threequarter': .3, 'profile': .5, 'threequarter_back': .6, 'back': None}[v]
        cross(d, neck, SOCK_A, 'neck')
        cross(d, crown, SOCK_B, 'crown', r=8)
        a = {'neck': neck, 'crown': crown}
        if turn is not None:
            ex = cx + turn * rx * 1.2
            a['eyes'] = (ex, cy - r * .15 * pxcm)
            a['mouth'] = (ex + (turn * 6 if turn else 0), cy + r * .45 * pxcm)
            if v != 'threequarter_back':
                for k in ('eyes', 'mouth'):
                    cross(d, a[k], ACCENT[cid], k, r=6)
        d.text((cx - cw / 2 + 16, 230), v, font=font(FONTB, 18), fill=INK)
        reg[v] = {k: [round(p[0], 1), round(p[1], 1)] for k, p in a.items()}
    reg['px_per_cm'] = pxcm
    return im


FEET = ['flat', 'heel_up', 'toe_up', 'front', 'back', 'threequarter']


def feet_template(cid, registry):
    """The right boot or shoe in six states: ankle brad on green, toe and heel on the floor line."""
    C = CHARS[cid]
    L = C['height'] * 0.145
    pxcm = 11.0 if cid != 'dot' else 16.0
    im, d = sheet_frame(f'{cid}.feet.R', f"{C['label']} · right foot, six states · ankle brad on green; toe (red) and heel (blue) where the sole meets the floor line", pxcm)
    cw = (SHEET_W - 120) / 3
    reg = registry.setdefault(cid, {}).setdefault('feet.R', {})
    for i, v in enumerate(FEET):
        x0, y0 = 60 + cw * (i % 3), 160 + (i // 3) * 470
        floor = y0 + 380
        d.line([(x0 + 20, floor), (x0 + cw - 20, floor)], fill=(200, 192, 180), width=2)
        ank = (x0 + 80 + 6 * pxcm, floor - 9 * pxcm)
        heel, toe = (ank[0] - 6 * pxcm, floor), (ank[0] + (L - 6) * pxcm, floor)
        if v == 'heel_up':
            heel = (heel[0] + 2 * pxcm, floor - 7 * pxcm)
        if v == 'toe_up':
            toe = (toe[0] - 2 * pxcm, floor - 8 * pxcm)
        if v in ('front', 'back'):
            ank = (x0 + cw / 2, floor - 10 * pxcm)
            heel, toe = (ank[0] - 4.5 * pxcm, floor), (ank[0] + 4.5 * pxcm, floor)
        # a ghost of the shoe, so the orientation is never in doubt
        if v in ('front', 'back'):
            g = [(ank[0] - 3.5 * pxcm, ank[1] - 4 * pxcm), (ank[0] + 3.5 * pxcm, ank[1] - 4 * pxcm), (toe[0] + 1 * pxcm, floor), (heel[0] - 1 * pxcm, floor)]
        else:
            g = [(ank[0] - 4 * pxcm, ank[1] - 5 * pxcm), (ank[0] + 4 * pxcm, ank[1] - 5 * pxcm), (ank[0] + 5 * pxcm, ank[1] + 3 * pxcm),
                 (toe[0], toe[1] - 4 * pxcm), (toe[0] + 1 * pxcm, toe[1]), (heel[0] - 1 * pxcm, heel[1]), (heel[0] - 1.5 * pxcm, heel[1] - 6 * pxcm)]
        d.polygon(g, fill=GHOST)
        cross(d, ank, SOCK_A, 'ankle')
        cross(d, toe, SOCK_B, 'toe' if v not in ('front', 'back') else 'sole R', r=7)
        cross(d, heel, (60, 90, 170), 'heel' if v not in ('front', 'back') else 'sole L', r=7)
        d.text((x0 + 20, y0), v.replace('_', ' '), font=font(FONTB, 18), fill=INK)
        reg[v] = {'A': [round(ank[0], 1), round(ank[1], 1)], 'toe': [round(toe[0], 1), round(toe[1], 1)], 'heel': [round(heel[0], 1), round(heel[1], 1)], 'px_per_cm': pxcm}
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    registry = {'about': 'Kit 3 sockets, written by kit.py from each character\'s rest skeleton: px in each template sheet. A part painted into a template keeps these sockets.',
                'sheet_px': [SHEET_W, SHEET_H], 'pieces': [{'n': n, 'slot': k, 'what': t} for n, k, t in PIECES],
                'characters': {k: {'label': v['label'], 'plays': v['plays'], 'height_cm': v['height'], 'look': v['look']} for k, v in CHARS.items()}}
    files = []
    for cid in CHARS:
        p = os.path.join(OUT, f'{cid}.cutchart.png')
        cut_chart(cid).save(p)
        files.append(p)
        # 3/4 and back cards share the front's sockets (a cut-out turns by swapping cards, not joints)
        for view, label in (('front', 'front'), ('front', 'threequarter'), ('front', 'back'), ('profile', 'profile')):
            p = os.path.join(OUT, f'{cid}.body.{label}.template.png')
            body_template(cid, view, registry, label).save(p)
            files.append(p)
        for view in ('front', 'profile'):
            p = os.path.join(OUT, f'{cid}.face.{view}.template.png')
            face_template(cid, view, registry).save(p)
            files.append(p)
        for nm, fn in (('heads', heads_template), ('feet', feet_template)):
            p = os.path.join(OUT, f'{cid}.{nm}.template.png')
            fn(cid, registry).save(p)
            files.append(p)
        p = os.path.join(OUT, f'{cid}.hands.template.png')
        hands_template(cid, registry).save(p)
        files.append(p)
    json.dump(registry, open(os.path.join(HERE, 'registry.json'), 'w'), indent=1)
    for f in files:
        print(os.path.relpath(f, HERE))


if __name__ == '__main__':
    main()
