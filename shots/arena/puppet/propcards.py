"""Props drawn the Crash Lab's way, in the cast's cardboard.

The geometry follows Bolas's own drawProp() (lab/crash-lab/index.html) exactly:
the same pivots (a table's pos is the floor under its centre, a door's is its
hinge, a clock's is the middle of its pole), the same rotation (rot = [yaw, pitch,
roll] as rY . rX . rZ; the old cuboids read the yaw from rot[1], so every turned
chair, mirror and door faced the wrong way) and the same states (a door's open
angle, a clock's hand, a candle blown out, a book open). The look is the cast's:
the man's prop sheets (parts/cut/props, cut by parts/cut_props.py) are mapped
onto the prop's plane where it has one. Under an orthographic camera a plane maps
to the screen by an affine transform, so a card on a door swings with the door.
Volumes (tables, benches, crates, stairs) are flat-shaded cardboard with an ink
line. Glass, water and mirrors are see-through.

    items = prop_items(cam, frame_props, loader)   # [{id, held, z, type, draw(pt)}]
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(HERE, '..', 'parts', 'cut', 'props')
INK = (34, 26, 20, 255)
WOOD, WOOD_D, KRAFT = '#6f5b49', '#4a3b2f', '#c39a6b'
GREY_WOOD = '#7d7468'


def _rgb(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def _shade(h, f, a=255):
    r, g, b, _ = _rgb(h)
    return (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)), a)


def rY(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rX(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rZ(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


_CARD = {}


def card(name):
    if name not in _CARD:
        p = os.path.join(CARDS, name + '.png')
        _CARD[name] = Image.open(p).convert('RGBA') if os.path.exists(p) else None
    return _CARD[name]


class Pen:
    """Draws one prop: T(v) is the prop's local cm -> world, P(w) world -> screen."""

    def __init__(self, cam, pt, q):
        self.cam, self.pt = cam, pt
        r = q.get('rot') or [0, 0, 0]
        self.R = rY(r[0]) @ rX(r[1]) @ rZ(r[2])
        self.c = np.array(q['pos'], float)
        self.s = cam.s

    def T(self, v, R=None):
        return self.c + (self.R if R is None else R) @ np.asarray(v, float)

    def P(self, w):
        return self.cam.P(w)[:2]

    def poly(self, pts3, fill, ink=1.5, R=None):
        self.poly2([self.P(self.T(v, R)) for v in pts3], fill, ink)

    def poly2(self, pts, fill, ink=1.5):
        pt = self.pt
        if fill is not None and fill[3] < 255:
            self.alpha_poly(pts, fill)
        elif fill is not None:
            pt.poly_raw(pts, fill)
        if ink:
            pt.d.line([pt._xy(p) for p in list(pts) + [pts[0]]], fill=INK, width=max(1, int(ink * 2)), joint='curve')

    def alpha_poly(self, pts, fill):
        pt = self.pt
        P = [pt._xy(p) for p in pts]
        xs, ys = [p[0] for p in P], [p[1] for p in P]
        x0, y0 = int(max(0, min(xs))), int(max(0, min(ys)))
        x1, y1 = int(min(pt.im.size[0], max(xs) + 1)), int(min(pt.im.size[1], max(ys) + 1))
        if x1 <= x0 or y1 <= y0:
            return
        L = Image.new('RGBA', (x1 - x0, y1 - y0), (0, 0, 0, 0))
        ImageDraw.Draw(L).polygon([(x - x0, y - y0) for x, y in P], fill=fill)
        pt.im.alpha_composite(L, (x0, y0))

    def line(self, a, b, w_cm, col=INK, R=None):
        pa, pb = self.P(self.T(a, R)), self.P(self.T(b, R))
        self.pt.d.line([self.pt._xy(pa), self.pt._xy(pb)], fill=INK, width=max(2, int((w_cm * self.s + 2) * 2)))
        if col != INK:
            self.pt.d.line([self.pt._xy(pa), self.pt._xy(pb)], fill=col, width=max(1, int(w_cm * self.s * 2)))

    def circle2(self, c, r_px, fill, ink=1.5):
        n = max(16, int(r_px))
        self.poly2([(c[0] + r_px * math.cos(t), c[1] + r_px * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)], fill, ink)

    def box(self, centre, size, col, ink=1.4, R=None):
        """A cuboid about a local centre, faces shaded and only the ones facing the camera."""
        R = self.R if R is None else R
        sx, sy, sz = [v / 2 for v in size]
        V = lambda i, k, l: self.c + R @ (np.asarray(centre, float) + np.array([i * sx, k * sy, l * sz]))
        faces = [((0, 1, 0), [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)], 1.12),
                 ((0, -1, 0), [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], .6),
                 ((0, 0, 1), [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], .95),
                 ((0, 0, -1), [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)], .9),
                 ((1, 0, 0), [(1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)], .8),
                 ((-1, 0, 0), [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)], .8)]
        for n, idx, f in faces:
            if self.cam.dir(R @ np.array(n, float))[2] < 0:
                self.poly2([self.P(V(*i)) for i in idx], _shade(col, f, _rgb(col)[3] if isinstance(col, str) else 255), ink)

    def plane_card(self, img, tl, tr, bl, R=None, min_det=0.12):
        """Map a card onto the local plane through tl, tr, bl (local cm). False if edge-on."""
        if img is None:
            return False
        a, b, c = (self.P(self.T(v, R)) for v in (tl, tr, bl))
        w, h = img.size
        M = np.column_stack([(b - a) / w, (c - a) / h])
        area = abs(np.linalg.det(M)) * w * h
        full = np.linalg.norm(b - a) * np.linalg.norm(c - a) + 1e-9
        if area / full < min_det:
            return False
        self.pt.paste(img, M, a)
        return True

    def standee(self, img, base, height_cm, width_cm=None):
        """A card standing upright facing the camera, its base centre on a world point."""
        if img is None:
            return
        b = self.P(base)
        h = height_cm * self.s
        w = (width_cm * self.s) if width_cm else h * img.size[0] / img.size[1]
        M = np.array([[w / img.size[0], 0], [0, h / img.size[1]]])
        self.pt.paste(img, M, b - np.array([w / 2, h]))

    def glow(self, w, r_cm, col=(255, 214, 120, 60)):
        c = self.P(w)
        self.circle2(c, r_cm * self.s, col, ink=0)


def draw(pen, q, f=0):
    t, s, st = q.get('type'), q.get('size'), q.get('state') or {}
    s = s if isinstance(s, list) else ([s] if s else None)
    T, P = pen.T, pen.P
    if st.get('hide'):
        return
    if t == 'box':
        sz = s if s and len(s) == 3 else [30, 24, 24]
        pen.box([0, 0, 0], sz, KRAFT)
        if min(sz) > 25:          # packing tape across the lid
            pen.line([-sz[0] / 2, sz[1] / 2, 0], [sz[0] / 2, sz[1] / 2, 0], 1.6, (214, 190, 140, 255))
    elif t == 'table':
        w, h, d = (s + [110, 72, 60][len(s):]) if s else [110, 72, 60]
        legs = [(-w / 2 + 5, -d / 2 + 5), (w / 2 - 5, -d / 2 + 5), (-w / 2 + 5, d / 2 - 5), (w / 2 - 5, d / 2 - 5)]
        far = sorted(legs, key=lambda xz: -pen.cam.P(T([xz[0], 0, xz[1]]))[2])
        for x, z in far[:2]:
            pen.line([x, 0, z], [x, h - 2, z], 3.2, _rgb(WOOD_D))
        pen.box([0, h - 2, 0], [w, 4, d], WOOD)
        for x, z in far[2:]:
            pen.line([x, 0, z], [x, h - 2, z], 3.2, _rgb(WOOD_D))
    elif t == 'bench':
        w = s[0] if s else 140
        far = sorted([(x, z) for x in (-w / 2 + 8, w / 2 - 8) for z in (-14, 14)], key=lambda xz: -pen.cam.P(T([xz[0], 0, xz[1]]))[2])
        for x, z in far[:2]:
            pen.line([x, 0, z], [x, 42, z], 3.6, _rgb(WOOD_D))
        pen.box([0, 44, 0], [w, 5, 36], GREY_WOOD)
        for x, z in far[2:]:
            pen.line([x, 0, z], [x, 42, z], 3.6, _rgb(WOOD_D))
    elif t == 'chair':
        back_far = pen.cam.P(T([0, 66, -19]))[2] > pen.cam.P(T([0, 44, 0]))[2]
        if back_far:
            pen.box([0, 66, -19], [40, 40, 3], WOOD)
        for x, z in ((-17, -17), (17, -17), (-17, 17), (17, 17)):
            pen.line([x, 0, z], [x, 42, z], 2.8, _rgb(WOOD_D))
        pen.box([0, 44, 0], [40, 4, 40], WOOD)
        if not back_far:
            pen.box([0, 66, -19], [40, 40, 3], WOOD)
    elif t == 'door':
        w, h = (s[0], s[1]) if s and len(s) > 1 else (60, 200)
        a = st.get('open', 0) or 0
        Rd = pen.R @ rY(-a)
        if not pen.plane_card(card('doorframe'), [-6, h + 8, 0], [w + 6, h + 8, 0], [-6, 0, 0]):
            pen.line([0, 0, 0], [0, h + 6, 0], 5, _rgb(GREY_WOOD))
            pen.line([w, 0, 0], [w, h + 6, 0], 5, _rgb(GREY_WOOD))
        if not pen.plane_card(card('door'), [0, h, 0], [w, h, 0], [0, 0, 0], R=Rd):
            pen.line([0, 0, 0], [w, 0, 0], 4, _rgb(WOOD), R=Rd)
            pen.poly([[0, 0, 0], [w, 0, 0], [w, h, 0], [0, h, 0]], _rgb(WOOD), R=Rd)
    elif t == 'fence':
        w = s[0] if s else 160
        h = s[1] if s and len(s) > 1 else 105
        n = max(1, round(w / 190))
        for i in range(n):
            x0 = -w / 2 + w * i / n
            if not pen.plane_card(card('railing'), [x0, h, 0], [x0 + w / n, h, 0], [x0, 0, 0]):
                pen.line([x0, h, 0], [x0 + w / n, h, 0], 3, _rgb('#6e737a'))
    elif t == 'window':
        w, h = (s[0], s[1]) if s and len(s) > 1 else (80, 90)
        pen.poly([[-w / 2, 0, 0], [w / 2, 0, 0], [w / 2, h, 0], [-w / 2, h, 0]], (200, 222, 236, 120), ink=0)
        for a, b in (([-w / 2, 0, 0], [w / 2, 0, 0]), ([w / 2, 0, 0], [w / 2, h, 0]), ([w / 2, h, 0], [-w / 2, h, 0]),
                     ([-w / 2, h, 0], [-w / 2, 0, 0]), ([0, 0, 0], [0, h, 0]), ([-w / 2, h / 2, 0], [w / 2, h / 2, 0])):
            pen.line(a, b, 4 if a[1] == b[1] == 0 or abs(a[0]) == abs(b[0]) == w / 2 else 2.5, _rgb(GREY_WOOD))
    elif t == 'mirror':
        w, h = (s[0], s[1]) if s and len(s) > 1 else (70, 180)
        pen.poly([[-w / 2, 0, 0], [w / 2, 0, 0], [w / 2, h, 0], [-w / 2, h, 0]], (196, 210, 222, 70 if st.get('reflect') else 110), ink=0)
        pen.line([-w / 2 + 8, h * .7, 0], [-w / 2 + 26, h * .9, 0], 1.6, (240, 246, 250, 255))
        pen.line([-w / 2 + 14, h * .58, 0], [-w / 2 + 36, h * .84, 0], 1.0, (240, 246, 250, 255))
        for a, b in (([-w / 2, 0, 0], [w / 2, 0, 0]), ([w / 2, 0, 0], [w / 2, h, 0]), ([w / 2, h, 0], [-w / 2, h, 0]), ([-w / 2, h, 0], [-w / 2, 0, 0])):
            pen.line(a, b, 4, _rgb(WOOD_D))
    elif t == 'screen':
        w, h = (s[0], s[1]) if s and len(s) > 1 else (80, 56)
        y0 = s[2] if s and len(s) > 2 else 90
        pen.line([0, 0, -6], [0, y0, -6], 3, _rgb('#3a3d42'))
        pen.box([0, 1, -6], [30, 2, 20], '#55595f')
        pen.poly([[-w / 2 - 6, y0 - 6, 0], [w / 2 + 6, y0 - 6, 0], [w / 2 + 6, y0 + h + 6, 0], [-w / 2 - 6, y0 + h + 6, 0]], _rgb('#2a2d31'))
        pen.poly([[-w / 2, y0, 1], [w / 2, y0, 1], [w / 2, y0 + h, 1], [-w / 2, y0 + h, 1]], _rgb('#0e1318' if st.get('off') else '#2d4152'), ink=1)
    elif t == 'stairs':
        n = int(st.get('n', 4))
        rise, run, w = (s[1], s[2], s[0]) if s and len(s) == 3 else (20, 28, 80)
        order = sorted(range(n), key=lambda i: -pen.cam.P(T([0, rise * (i + 1) / 2, run * i + run / 2]))[2])
        for i in order:
            pen.box([0, rise * (i + 1) / 2, run * i + run / 2], [w, rise * (i + 1), run], '#8a7a68')
    elif t == 'lamp':
        pen.line([0, 0, 0], [0, 190, 0], 2.6, _rgb('#2c2a28'))
        pen.line([0, 190, 0], [18, 196, 0], 2, _rgb('#2c2a28'))
        pen.glow(T([22, 180, 0]), 34, (255, 214, 120, 40))
        pen.standee(card('lantern'), T([22, 166, 0]), 30)
    elif t == 'clock':
        pen.line([0, -40, 0], [0, 14, 0], 2.6, _rgb('#2c2a28'))
        pts = [P(T([math.sin(b) * 26, 40 + math.cos(b) * 26, 0])) for b in np.linspace(0, 2 * math.pi, 36, endpoint=False)]
        pen.poly2(pts, _rgb('#5a4636'), ink=1.5)
        pts = [P(T([math.sin(b) * 22, 40 + math.cos(b) * 22, .5])) for b in np.linspace(0, 2 * math.pi, 36, endpoint=False)]
        pen.poly2(pts, _rgb('#efe7d4'), ink=1)
        for i in range(12):
            b = i / 12 * 2 * math.pi
            pen.line([math.sin(b) * 18, 40 + math.cos(b) * 18, 1], [math.sin(b) * 21, 40 + math.cos(b) * 21, 1], .7)
        a = math.radians(st.get('hand', 0) or 0)
        pen.line([0, 40, 1], [math.sin(a) * 17, 40 + math.cos(a) * 17, 1], 1.2)
        pen.line([0, 40, 1], [math.sin(a + 2.1) * 10, 40 + math.cos(a + 2.1) * 10, 1], 1.6)
    elif t == 'cup':
        if st.get('broken'):
            for dx, dz, k in ((-6, 2, 1), (5, -3, -1), (1, 6, 1)):
                pen.poly([[dx - 3, .5, dz], [dx + 3, .5, dz + k], [dx, .5, dz + 3]], _rgb('#e9e4da'), ink=1)
            return
        img = card('papercup')
        if st.get('floor'):
            pen.plane_card(img, [-5, 0.5, -6], [5, 0.5, -6], [-5, 0.5, 6], min_det=0.0) or pen.standee(img, T([0, 0, 0]), 8, 12)
        else:
            pen.standee(img, T([0, -6, 0]), 12)
    elif t == 'ball':
        r = s[0] if s else 10
        img = card('basketball' if r >= 12 else 'soccer')
        c = P(pen.c)
        k = 2 * r * pen.s / img.size[1]
        pen.pt.paste(img, np.eye(2) * k, c - np.array(img.size) * k / 2)
    elif t == 'letter':
        if not pen.plane_card(card('letter'), [-9, 6, 0], [9, 6, 0], [-9, -6, 0]):
            pen.line([-9, 0, 0], [9, 0, 0], .8, _rgb('#f1ead8'))
    elif t == 'book':
        if st.get('open'):
            pen.plane_card(card('book'), [-15, 11, 2], [15, 11, 2], [-15, -11, 2]) or pen.line([-15, 0, 0], [15, 0, 0], 1.5, _rgb('#efe6d2'))
        else:
            pen.box([0, 0, 0], [16, 22, 4], '#7a2f2f')
            pen.plane_card(card('notebook'), [-8, 11, 2.2], [8, 11, 2.2], [-8, -11, 2.2])
    elif t == 'coin':
        c = P(pen.c)
        pen.circle2(c, max(2.0, 2.6 * pen.s), _rgb('#d8b04a'), ink=1)
    elif t == 'key':
        pen.line([-5, 0, 0], [5, 0, 0], .9, _rgb('#b08a2e'))
        pen.circle2(P(T([-7, 0, 0])), max(2, 2.4 * pen.s), _rgb('#b08a2e'), ink=1)
    elif t == 'hat':
        pen.poly([[-17, 0, 0], [17, 0, 0], [17, 2, 0], [-17, 2, 0]], _rgb('#2b2622'))
        pen.poly([[-11, 2, 0], [11, 2, 0], [10, 18, 0], [-10, 18, 0]], _rgb('#2b2622'))
        pen.line([-11, 5, .2], [11, 5, .2], 1.2, _rgb('#8a2a22'))
    elif t == 'candle':
        pen.box([0, 0, 0], [4, 16, 4], '#efe6cf', ink=1)
        if not st.get('out'):
            pen.glow(T([0, 12, 0]), 12)
            c = P(T([0, 11, 0]))
            pen.pt.ellipse_raw(c, 2.2 * pen.s, 4 * pen.s, (255, 200, 80, 255))
    elif t == 'skull':
        c = P(T([0, 2, 0]))
        front = pen.cam.dir(pen.R @ np.array([0, 0, 1.0]))[2] < 0.3
        pen.poly([[-4.5, -4, 4], [4.5, -4, 4], [4, -9, 3], [-4, -9, 3]], _rgb('#d9d0b8'), ink=1.2)
        pen.circle2(c, 8.5 * pen.s, _rgb('#ece4cf'), ink=1.5)
        if front:
            for x in (-3.2, 3.2):
                e = P(T([x, 1.5, 7.5]))
                pen.pt.ellipse_raw(e, 2.1 * pen.s, 2.5 * pen.s, INK)
            pen.poly([[-1, -2, 8], [1, -2, 8], [0, 0.2, 8]], INK, ink=0)
            for x in (-2.5, -.8, .8, 2.5):
                pen.line([x, -5.5, 6.6], [x, -7.5, 6.2], .25)
    elif t == 'globe':
        r = (s[0] / 2) if s else 22
        pen.box([0, 3, 0], [r * 1.6, 6, r * 1.6], '#6b4a33')
        c = P(T([0, 6 + r, 0]))
        pen.circle2(c, r * pen.s, (214, 232, 242, 70 if not st.get('empty') else 110), ink=1.6)
        pen.pt.d.arc([pen.pt._xy((c[0] - r * .7 * pen.s, c[1] - r * .7 * pen.s)), pen.pt._xy((c[0] + r * .3 * pen.s, c[1] + r * .3 * pen.s))],
                     200, 260, fill=(250, 252, 255, 230), width=max(2, int(1.2 * pen.s * 2)))
    elif t == 'kite':
        pen.poly([[0, 18, 0], [12, 0, 0], [0, -18, 0], [-12, 0, 0]], _rgb('#c84a3a'))
        pen.line([0, 18, .3], [0, -18, .3], .5, _rgb('#e8d9b0'))
        pen.line([-12, 0, .3], [12, 0, .3], .5, _rgb('#e8d9b0'))
        tail = [[math.sin(f * .2 + i) * 4, -18 - i * 7, 0] for i in range(6)]
        for a, b in zip(tail, tail[1:]):
            pen.line(a, b, .3)
    elif t == 'bell':
        pen.line([0, -60, 0], [0, 60, 0], 1.2, _rgb('#8a5a2b'))
        pen.poly([[-14, 60, 0], [14, 60, 0], [9, 80, 0], [-9, 80, 0]], _rgb('#d8b04a'))
    elif t == 'pie':
        pen.poly([[-9, 0, -3], [9, 0, -3], [8, 5, 0], [-8, 5, 0]], _rgb('#e8cf9e'))
    elif t == 'plate':
        pen.poly([[-11, 0, -4], [11, 0, -4], [11, 1, 4], [-11, 1, 4]], _rgb('#efe9dc'))
    elif t == 'suitcase':
        pen.box([0, 0, 0], [40, 30, 14], '#7a4a2a')
        pen.line([-6, 15, 0], [-6, 21, 0], 1.2)
        pen.line([6, 15, 0], [6, 21, 0], 1.2)
        pen.line([-6, 21, 0], [6, 21, 0], 1.2)
    elif t == 'stick':
        L = s[1] if s and len(s) > 1 else 60
        pen.line([0, -L / 2, 0], [0, L / 2, 0], 1.4, _rgb('#9b7b52'))
    elif t == 'broom':
        pen.line([0, -40, 0], [0, 50, 0], 1.4, _rgb('#8a5a2b'))
        pen.poly([[-10, -40, 0], [10, -40, 0], [13, -56, 0], [-13, -56, 0]], _rgb('#d9b45a'))
    elif t == 'puddle':
        r = s[0] if s else 40
        pen.poly([[math.cos(a) * r * (1 + .08 * math.sin(a * 3)), .2, math.sin(a) * r * .55] for a in np.linspace(0, 2 * math.pi, 18, endpoint=False)],
                 (90, 140, 180, 120), ink=1)
    elif t == 'water':
        w, dp, d = (s + [200, 80, 120][len(s):]) if s else [200, 80, 120]
        pen.box([0, -dp / 2, 0], [w, dp, d], '#4f86b0', ink=1)
        pen.poly([[-w / 2, 0, -d / 2], [w / 2, 0, -d / 2], [w / 2, 0, d / 2], [-w / 2, 0, d / 2]], (90, 150, 200, 150), ink=1)
    elif t == 'hoop':
        pen.box([0, 22, -14], [56, 40, 3], '#efe9dc')
        pen.line([0, -180, -16], [0, 22, -16], 2)
    elif t in ('wall',):
        w, h = (s[0], s[1]) if s and len(s) > 1 else (120, 200)
        pen.poly([[-w / 2, 0, 0], [w / 2, 0, 0], [w / 2, h, 0], [-w / 2, h, 0]], (160, 200, 230, 60) if st.get('glass') or st.get('mime') else _rgb('#5a5048'))
    else:
        pen.box([0, 0, 0], s if s and len(s) == 3 else [20, 20, 20], '#9a8a70')


def centre(q):
    """A local point for depth: the middle of the prop's body, not its pivot."""
    t, s = q.get('type'), q.get('size')
    s = s if isinstance(s, list) else ([s] if s else None)
    if t == 'table':
        return [0, (s[1] if s and len(s) > 1 else 72) / 2, 0]
    if t == 'door':
        return [(s[0] if s else 60) / 2, 100, 0]
    if t in ('fence', 'window', 'mirror', 'wall'):
        return [0, (s[1] if s and len(s) > 1 else 100) / 2, 0]
    if t in ('chair', 'bench'):
        return [0, 30, 0]
    if t == 'lamp':
        return [0, 95, 0]
    return [0, 0, 0]


def prop_items(cam, props, f=0):
    out = []
    for pid, q in props.items():
        if not q.get('pos') or (q.get('state') or {}).get('hide'):
            continue
        r = q.get('rot') or [0, 0, 0]
        R = rY(r[0]) @ rX(r[1]) @ rZ(r[2])
        z = cam.P(np.array(q['pos'], float) + R @ np.array(centre(q), float))[2]
        out.append({'id': pid, 'held': q.get('held'), 'z': z, 'type': q.get('type'),
                    'draw': (lambda pt, q=q: draw(Pen(cam, pt, q), q, f))})
    return out
