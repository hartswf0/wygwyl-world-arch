"""Dot's head drawn the Crash Lab's way: a port of Bolas drawHead() (lab/crash-lab/index.html).

Dot is a crash dummy, so her head is a round painted disc that carries the bank's whole
face, not a drawn card: eyes (open with gaze, lids, closed, heart), brows (angle and lift),
nose, mouth (line with smile, O, open, teeth, wavy), the crash-test targets on the sides of
the skull and her bow. Every feature sits on the head's sphere in the head's own frame
(hfwd from the bank, up from head to headTop) and shows only while it faces the camera, so
the face turns with the head. Dot's head cards were a black hair blob with two specks for
eyes: her face never read (critics, scion T133-T144).

Sizes are Bolas's, in cm on a 20cm head radius, scaled to this head.
"""
import math
import numpy as np

INK = (11, 13, 16, 255)
RED = (227, 38, 31, 255)
AMB = (255, 210, 63, 255)
PINK = (255, 158, 176, 255)
WHITE = (255, 255, 255, 255)


def nrm(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def _ell(cx, cy, rx, ry, rot=0.0, a0=0.0, a1=2 * math.pi, n=28):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for t in np.linspace(a0, a1, n):
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out


def _quad(p0, p1, p2, n=12):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, n)]


def _heart(x, y, s):
    pts = []
    for t in np.linspace(0, 2 * math.pi, 40):
        hx = 16 * math.sin(t) ** 3
        hy = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((x + hx * s / 16, y + hy * s / 16))
    return pts


def draw(pt, cam, j, a, colour, f=0, bow=True):
    """Paint the head on Painter pt. j: joints (np arrays), a: the bank actor record."""
    fc = a.get('face') or {}
    c3 = j['head']
    up = nrm(j['headTop'] - j['head'])
    fw = nrm(np.asarray(a.get('hfwd') or [0, 0, 1], float))
    fw = nrm(fw - up * np.dot(fw, up))
    # cheat to camera: a face side-on or a little away turns some way toward the lens, the
    # cut-out animator's habit, so a profile still shows an eye and the mouth
    toward = -nrm(np.array([cam.dir(e)[2] for e in np.eye(3)]))       # world direction to the viewer
    toward_h = nrm(toward - up * np.dot(toward, up))
    if np.dot(fw, toward_h) > -0.6:
        # turn until the face is clearly on the head, not squashed on its edge (critic, round 2)
        for _ in range(12):
            if np.dot(fw, toward_h) >= 0.4:
                break
            fw = nrm(fw + 0.25 * toward_h)
    x = nrm(np.cross(up, fw))
    Rh = np.column_stack([x, up, fw])
    Rcm = float(np.linalg.norm(j['headTop'] - j['head'])) * 1.05     # head radius, cm
    k = Rcm / 20.0                                                   # Bolas sizes are on a 20cm head
    sc = cam.s * k
    c = cam.P(c3)
    R = Rcm * cam.s
    d = pt.d
    X = lambda p: pt._xy(p)
    upv = cam.P(c3 + up)
    roll = math.atan2(upv[0] - c[0], -(upv[1] - c[1]))

    def feat(local, r=1.0):
        w = c3 + nrm(Rh @ np.asarray(local, float)) * Rcm * r
        q = cam.P(w)
        return (q[0], q[1]), float(np.clip((c[2] - q[2]) / Rcm, 0, 1))      # z is away: facing = nearer

    def poly(pts, fill=None, ink=None, w=2.2):
        P = [X(p) for p in pts]
        if fill:
            d.polygon(P, fill=fill)
        if ink:
            d.line(P + ([P[0]] if fill else []), fill=ink, width=max(1, int(w * 2)), joint='curve')

    # the bow sits behind the head's top edge, Dot's mark in the Crash Lab
    marks = []
    if bow:
        for sd in (-1, 1):
            q, _ = feat([sd * 8 / 20, 0.95, -2 / 20])
            marks.append(_ell(q[0] + sd * 5 * sc, q[1], 6 * sc, 4 * sc, sd * .4))
    for m in marks:
        poly(m, RED, INK, 1.6)
    poly(_ell(c[0], c[1], R, R, n=48), colour, INK, 2.4)
    for sd in (-1, 1):
        q, fa = feat([sd, .15, -.1])
        if fa > .25:
            rr = 4.2 * sc * fa
            for i in range(4):
                wedge = [(q[0], q[1])] + _ell(q[0], q[1], rr, rr, 0, i * math.pi / 2, (i + 1) * math.pi / 2, 8)
                poly(wedge, INK if i % 2 else AMB)
    if feat([0, 0, 1])[1] < .06:
        return
    blink = ((f + 67 * 13) % 113) < 3
    for side, lx in (('L', .36), ('R', -.36)):
        q, fa = feat([lx, .22, .9])
        if fa < .05:
            continue
        ew, eh = 6.2 * sc * max(.35, fa), 9 * sc
        shape = fc.get('eyes', 'o')
        lid = float(np.clip((fc.get('lid') or 0) + (1 if blink else 0), 0, 1))
        cr, sr = math.cos(roll), math.sin(roll)
        L = lambda px, py: (q[0] + px * cr - py * sr, q[1] + px * sr + py * cr)
        if shape == 'heart':
            poly(_heart(q[0], q[1], eh * 1.1), RED, INK, 1.5)
        elif shape == 'closed' or lid >= .97:
            yo = eh * .2 if shape == 'closed' else 0
            arc = [L(px, py + yo) for px, py in _ell(0, 0, ew, ew, 0, math.pi * 1.1, math.pi * 1.9, 12)]
            poly(arc, None, INK, 2.2)
        else:
            poly(_ell(q[0], q[1], ew, eh, roll), WHITE, INK, 1.8)
            gx = float(np.clip(fc.get('gx') or 0, -1, 1)) * ew * .5
            gy = -float(np.clip(fc.get('gy') or 0, -1, 1)) * eh * .45
            pc = L(gx, gy + eh * .12)
            poly(_ell(pc[0], pc[1], ew * .5, eh * .5, roll), INK)
            hl = L(gx - ew * .15, gy - eh * .05)
            poly(_ell(hl[0], hl[1], ew * .16, ew * .16), WHITE)
            if lid > .02:
                # the lid comes down in the head's colour, with its edge inked
                yl = -eh + 2 * eh * lid
                top = [L(px, py) for px, py in _ell(0, 0, ew, eh, 0, math.pi, 2 * math.pi, 14)]
                lid_poly = [L(-ew, yl)] + [p for p in top] + [L(ew, yl)]
                poly(lid_poly, colour)
                poly([L(-ew, yl), L(ew, yl)], None, INK, 1.8)
        by = -eh * 1.02 - 1.6 * sc - (fc.get('brow') or 0) * 0      # bank brow is an angle (browA)
        ba = (fc.get('brow') or 0) * .5 * (-1 if side == 'L' else 1)
        poly([L(-ew * 1.1 * math.cos(ba), by - ew * 1.1 * math.sin(ba)), L(ew * 1.1 * math.cos(ba), by + ew * 1.1 * math.sin(ba))], None, INK, 2.6)
    nz, _ = feat([0, -.02, 1], 1.04)
    poly(_ell(nz[0], nz[1], 3.2 * sc, 3.2 * sc, n=12), INK)
    mq, mf = feat([0, -.45, .88])
    if mf > .05:
        mw = 10 * sc * max(.4, mf) * (1 + (fc.get('open') or 0) * .25)
        op = (fc.get('open') or 0) * 10 * sc
        sm = (fc.get('smile') or 0) * 5.5 * sc
        cr, sr = math.cos(roll), math.sin(roll)
        L = lambda px, py: (mq[0] + px * cr - py * sr, mq[1] + px * sr + py * cr)
        m = fc.get('mouth', 'line')
        if m == 'wavy' and op < 3:
            poly([L(-mw + i * mw / 4, (-2 if i % 2 else 2) * sc) for i in range(9)], None, INK, 2.2)
        elif op < 1.2 and m != 'O':
            poly([L(*p) for p in _quad((-mw, -sm * .4), (0, sm * 1.3), (mw, -sm * .4))], None, INK, 2.2)
        else:
            if m == 'O':
                shape = [L(px, py) for px, py in _ell(0, op * .35, max(3 * sc, mw * .55), max(3 * sc, op * .7))]
            else:
                upper = _quad((-mw, -sm * .4), (0, sm * .6), (mw, -sm * .4))
                lower = _quad((mw, -sm * .4), (mw * .6, op + sm), (0, op + sm * 1.2)) + _quad((0, op + sm * 1.2), (-mw * .6, op + sm), (-mw, -sm * .4))
                shape = [L(*p) for p in upper + lower]
            poly(shape, (74, 13, 13, 255))
            if m == 'teeth':
                th = max(3, op * .45)
                poly([L(-mw * .8, -sm * .4), L(mw * .8, -sm * .4), L(mw * .7, -sm * .4 + th), L(-mw * .7, -sm * .4 + th)], WHITE)
            poly(shape, None, INK, 2.2)
