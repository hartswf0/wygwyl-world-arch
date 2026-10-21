"""Vector shapes in centimetres -> SVG and a PIL raster, in the cardboard cut-out look.

A part drawn in code is a list of shapes in its own frame: cm, joint A at (0, 0),
joint B straight down +y (the axis rule in pieces.json). Because the part is
built from its joints outward, its connection points are known exactly; nothing
has to be read off the pixels or guessed afterwards.

Shapes (dicts):
  {'poly': [[x, y], ...]}
  {'circle': [x, y], 'r': r}
  {'capsule': [[x0, y0], [x1, y1]], 'r': [r0, r1]}     tapered, round ends
  {'line': [[x, y], ...], 'w': cm}                     open stroke (piping, creases)
style keys: fill, stroke, sw (stroke width cm), rim (True: part of the cardboard
silhouette, drawn first with the card-edge colour), alpha.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

PX_PER_CM = 12          # pieces_brief.json: 12 px/cm
RIM = '#d8bf98'          # cut cardboard edge
RIM_CM = 0.35
INK = '#1b1612'


def circle_pts(c, r, n=40):
    return [[c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)] for k in range(n)]


def hull(pts):
    """Monotone-chain convex hull."""
    P = sorted(map(tuple, pts))
    if len(P) < 3:
        return [list(p) for p in P]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return [list(p) for p in lo[:-1] + hi[:-1]]


def capsule_pts(a, b, ra, rb):
    return hull(circle_pts(a, ra) + circle_pts(b, rb))


def outline(s):
    """Closed outline of a shape in cm, or None for open strokes."""
    if 'poly' in s:
        return s['poly']
    if 'circle' in s:
        return circle_pts(s['circle'], s['r'])
    if 'capsule' in s:
        (a, b), (ra, rb) = s['capsule'], s['r']
        return capsule_pts(a, b, ra, rb)
    return None


def offset(pts, d):
    """Grow a closed outline by d cm (vertex normals; fine for the convex-ish card shapes)."""
    P = np.asarray(pts, float)
    n = len(P)
    out = []
    area = 0.5 * sum(P[i, 0] * P[(i + 1) % n, 1] - P[(i + 1) % n, 0] * P[i, 1] for i in range(n))
    sgn = 1 if area > 0 else -1
    for i in range(n):
        p0, p1, p2 = P[i - 1], P[i], P[(i + 1) % n]
        t = (p2 - p0)
        t = t / (np.linalg.norm(t) or 1)
        nrm = np.array([t[1], -t[0]]) * sgn
        out.append(list(p1 + nrm * d))
    return out


def bounds(shapes, pad=1.0):
    pts = []
    for s in shapes:
        o = outline(s)
        if o:
            pts += o
        elif 'line' in s:
            pts += s['line']
    P = np.asarray(pts, float)
    return P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad


def _hex(c, a=1.0):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (int(255 * a),)


def render(shapes, ppc=PX_PER_CM, ss=4, pad=1.0, box=None):
    """-> (RGBA image, origin_px): the part's (0, 0) in cm lands on origin_px."""
    x0, y0, x1, y1 = box or bounds(shapes, pad)
    W, H = int(math.ceil((x1 - x0) * ppc)), int(math.ceil((y1 - y0) * ppc))
    k = ppc * ss
    im = Image.new('RGBA', (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = lambda pts: [((p[0] - x0) * k, (p[1] - y0) * k) for p in pts]
    # cardboard rim: every rim shape, grown, in the card-edge colour, under everything
    for s in shapes:
        o = outline(s)
        if o and s.get('rim', True):
            d.polygon(P(offset(o, RIM_CM)), fill=_hex(RIM))
    for s in shapes:
        o = outline(s)
        if o:
            d.polygon(P(o), fill=_hex(s.get('fill', '#000000'), s.get('alpha', 1.0)) if s.get('fill') else None)
            if s.get('stroke'):
                pts = P(o)
                d.line(pts + [pts[0]], fill=_hex(s['stroke']), width=max(1, int(s.get('sw', 0.12) * k)), joint='curve')
        elif 'line' in s:
            d.line(P(s['line']), fill=_hex(s.get('stroke', INK), s.get('alpha', 1.0)), width=max(1, int(s.get('w', 0.15) * k)), joint='curve')
    im = im.resize((W, H), Image.LANCZOS)
    return im, ((0 - x0) * ppc, (0 - y0) * ppc)


def svg(shapes, pad=1.0, box=None):
    x0, y0, x1, y1 = box or bounds(shapes, pad)
    f = lambda v: f'{v:.2f}'
    pts = lambda o: ' '.join(f'{f(p[0])},{f(p[1])}' for p in o)
    rim, body = [], []
    for s in shapes:
        o = outline(s)
        if o and s.get('rim', True):
            rim.append(f'<polygon points="{pts(offset(o, RIM_CM))}" fill="{RIM}"/>')
        if o:
            st = f' stroke="{s["stroke"]}" stroke-width="{s.get("sw", 0.12)}" stroke-linejoin="round"' if s.get('stroke') else ''
            body.append(f'<polygon points="{pts(o)}" fill="{s.get("fill", "none")}" fill-opacity="{s.get("alpha", 1.0)}"{st}/>')
        elif 'line' in s:
            body.append(f'<polyline points="{pts(s["line"])}" fill="none" stroke="{s.get("stroke", INK)}" stroke-width="{s.get("w", 0.15)}" stroke-linecap="round" stroke-linejoin="round" stroke-opacity="{s.get("alpha", 1.0)}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(x0)} {f(y0)} {f(x1 - x0)} {f(y1 - y0)}" '
            f'width="{f((x1 - x0) * PX_PER_CM)}" height="{f((y1 - y0) * PX_PER_CM)}">' + ''.join(rim + body) + '</svg>')


def brad(c, r=0.75):
    """A brass split-pin head at a joint: the connection point, drawn where it is."""
    return [{'circle': c, 'r': r, 'fill': '#b8902f', 'stroke': '#5a4314', 'sw': 0.1, 'rim': False},
            {'circle': [c[0] - r * 0.25, c[1] - r * 0.25], 'r': r * 0.35, 'fill': '#f1d27a', 'rim': False}]


def rot(p, deg, about=(0, 0)):
    a = math.radians(deg)
    x, y = p[0] - about[0], p[1] - about[1]
    return [about[0] + x * math.cos(a) - y * math.sin(a), about[1] + x * math.sin(a) + y * math.cos(a)]


def corrugate(a, b, ra, rb, step=0.7, col='#2f3238'):
    """Faint fluting across a limb, like the cardboard the cast is cut from."""
    out = []
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = np.linalg.norm(b - a)
    u = (b - a) / L
    n = np.array([-u[1], u[0]])
    t = step
    while t < L - step:
        r = (ra + (rb - ra) * t / L) * 0.82
        p = a + u * t
        out.append({'line': [list(p - n * r), list(p + n * r)], 'stroke': col, 'w': 0.08, 'alpha': 0.7})
        t += step
    return out
