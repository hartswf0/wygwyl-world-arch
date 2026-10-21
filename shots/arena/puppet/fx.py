"""The Crash Lab's effects track, drawn over the take: a port of Bolas FX{} (lab/crash-lab/index.html).

The bank now carries each vignette's effects (export_bank.mjs: fx = [{k, a, b, who, txt, p}]):
rain, wind, glow, hearts, sweat, tear, dust, ?, !, Zzz, lines, steam, shiver, stars, a word.
Without them T176 and T181 asked for rain we never drew (critics, round 2). Positions follow
Bolas exactly (cm, around the actor's head or the view centre); the look is inked paper.

    draw(pt, cam, V, f, joints)      # joints: {actor id: {joint: np.array}} for frame f
"""
import math
import numpy as np

INK = (24, 20, 18, 255)
AMB = (255, 210, 63, 255)
RED = (205, 52, 42, 255)


def _line(pt, cam, a, b, col, w):
    pa, pb = cam.P(a)[:2], cam.P(b)[:2]
    pt.d.line([pt._xy(pa), pt._xy(pb)], fill=col, width=max(1, int(w * 2)))


def _text(pt, cam, at, txt, size, col):
    from PIL import ImageFont
    p = cam.P(at)[:2]
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', max(12, int(size * cam.s * 2)))
    x, y = pt._xy(p)
    pt.d.text((x, y), txt, font=f, fill=col, anchor='mm', stroke_width=max(2, int(size * cam.s * .18)), stroke_fill=(255, 255, 255, 255))


def _heart(cx, cy, s):
    pts = []
    for t in np.linspace(0, 2 * math.pi, 30):
        pts.append((cx + 16 * math.sin(t) ** 3 * s / 16, cy - (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) * s / 16))
    return pts


def _star(cx, cy, r, n=5, inner=.45):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(-math.pi / 2 + i * math.pi / n),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(-math.pi / 2 + i * math.pi / n)) for i in range(2 * n)]


def draw(pt, cam, V, f, joints):
    view = V.get('view') or {}
    vx, vz = (view.get('x') or 0), (view.get('z') or 0)
    first = next(iter(joints), None)
    for e in V.get('fx', []):
        if not (e['a'] <= f <= e['b']):
            continue
        t = (f - e['a']) / max(1, e['b'] - e['a'])
        J = joints.get(e.get('who') or first) or (joints.get(first) if first else None)
        k = e['k']
        if k == 'rain':
            # denser than the lab's 40 drops: the take is framed tighter and the drops are fine
            for i in range(140):
                x = vx - 320 + ((i * 53) % 640)
                z = vz - 90 + ((i * 29) % 180)
                y = 240 - ((f * 9 + i * 37) % 240)
                _line(pt, cam, [x, y, z], [x - 3, y - 14, z], (185, 212, 235, 235), 1.3)
        elif k == 'wind':
            for i in range(9):
                y = 20 + i * 22
                x = vx + 240 - ((f * 12 + i * 57) % 560)
                _line(pt, cam, [x, y, 30], [x + 40 + (i % 3) * 14, y, 30], (190, 196, 204, 220), 1.2)
        elif J is None:
            continue
        elif k == 'hearts':
            for i in range(3):
                ph = (f * .025 + i / 3) % 1
                p = cam.P(J['head'] + np.array([math.sin(i * 1.7 + ph * 6) * 24, 22 + ph * 70, 0]))
                c = pt._xy(p[:2])
                pts = _heart(c[0], c[1], (5 + ph * 4) * cam.s * 2)
                pt.d.polygon(pts, fill=(RED[0], RED[1], RED[2], int(255 * (1 - ph))), outline=INK)
        elif k == 'sweat':
            for i in range(3):
                ph = (f * .06 + i / 3) % 1
                side = 1 if i % 2 else -1
                p = cam.P(J['head'] + np.array([side * (18 + ph * 18), 8 + ph * 10 - ph * ph * 30, 6]))
                c = pt._xy(p[:2])
                r = 3.5 * cam.s * 2
                pt.d.ellipse([c[0] - r * .7, c[1] - r, c[0] + r * .7, c[1] + r], fill=(143, 208, 255, 255), outline=INK)
        elif k == 'tear':
            ph = (f * .035) % 1
            p = cam.P(J['head'] + np.array([4, 4 - ph * 36, 8]))
            c = pt._xy(p[:2])
            r = 2.6 * cam.s * 2
            pt.d.ellipse([c[0] - r * .7, c[1] - r, c[0] + r * .7, c[1] + r], fill=(143, 208, 255, 255), outline=INK)
        elif k == 'dust':
            base = (J['ankleL'] + J['ankleR']) / 2
            for i in range(6):
                a = i / 6 * math.pi * 2
                p = cam.P([base[0] + math.cos(a) * (8 + t * 36), 4 + t * 10, base[2] + math.sin(a) * (6 + t * 18)])
                c = pt._xy(p[:2])
                r = (4 + t * 8) * cam.s * 2
                pt.d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(243, 239, 230, int(255 * (1 - t))), outline=INK)
        elif k == 'q':
            _text(pt, cam, J['head'] + np.array([20, 42 + math.sin(f * .3) * 2, 0]), '?', 30, INK)
        elif k == 'bang':
            _text(pt, cam, J['head'] + np.array([0, 46 + t * 4, 0]), '!', 40, RED)
        elif k == 'zzz':
            for i in range(3):
                ph = (f * .02 + i / 3) % 1
                _text(pt, cam, J['head'] + np.array([16 + ph * 30, 26 + ph * 50, 0]), 'Z', 13 + ph * 13, INK)
        elif k == 'steam':
            for i in range(5):
                ph = (f * .07 + i / 5) % 1
                p = cam.P(J['headTop'] + np.array([math.sin(i * 2 + f * .2) * 8 * ph + (6 if i % 2 else -6), 10 + ph * 50, 0]))
                c = pt._xy(p[:2])
                r = (4 + ph * 10) * cam.s * 2
                pt.d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(255, 255, 255, int(230 * (1 - ph))), outline=INK)
        elif k == 'stars':
            cc = J['head'] + np.array([0, 30, 0])
            for i in range(4):
                a = f * .18 + i * math.pi / 2
                p = cam.P(cc + np.array([math.cos(a) * 22, math.sin(a * 2) * 3, math.sin(a) * 14]))
                c = pt._xy(p[:2])
                pt.d.polygon(_star(c[0], c[1], 5.5 * cam.s * 2), fill=AMB, outline=INK)
        elif k == 'lines':
            c = pt._xy(cam.P(J['head'])[:2])
            for i in range(14):
                a = i / 14 * math.pi * 2 + (f % 2) * .1
                r1 = 34 * cam.s * 2
                r2 = r1 + (12 + (i % 3) * 7) * cam.s * 2
                pt.d.line([(c[0] + math.cos(a) * r1, c[1] + math.sin(a) * r1), (c[0] + math.cos(a) * r2, c[1] + math.sin(a) * r2)], fill=INK, width=3)
        elif k == 'shiver':
            ch = J['chest']
            for s in (-1, 1):
                for i in range(3):
                    y = ch[1] - 20 + i * 22
                    x = ch[0] + s * (34 + (f % 2) * 3)
                    _line(pt, cam, [x, y, ch[2]], [x + s * 8, y + 4, ch[2]], INK, 1.4)
        elif k == 'bulb':
            c = pt._xy(cam.P(J['head'] + np.array([0, 46, 0]))[:2])
            r = 9 * cam.s * 2
            pt.d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(255, 242, 122, 255) if t > .15 else (255, 255, 255, 255), outline=INK, width=3)
        elif k == 'glow':
            at = np.array(e['p'], float) if e.get('p') else J['head']
            c = pt._xy(cam.P(at)[:2])
            r = (10 + math.sin(f * .5) * 3 + t * 6) * cam.s * 2 * 2.4
            from PIL import Image, ImageDraw, ImageFilter
            L = Image.new('RGBA', pt.im.size, (0, 0, 0, 0))
            ImageDraw.Draw(L).ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(255, 220, 90, 120))
            pt.im.alpha_composite(L.filter(ImageFilter.GaussianBlur(r * .35)))
        elif k == 'word' and e.get('txt'):
            at = np.array(e['p'], float) if e.get('p') else J[e.get('at') or 'head'] + np.array(e.get('off') or [0, 40, 0])
            c = pt._xy(cam.P(at)[:2])
            s = (26 * (0.6 + t / .15 * .6 if t < .15 else 1.2 - (t - .15) * .25)) * cam.s * 2
            pt.d.polygon(_star(c[0], c[1], s * 1.25, 12, .62), fill=AMB, outline=INK)
            _text(pt, cam, at, e['txt'], 26 * (1.0 if t >= .15 else 0.6 + t / .15 * .4), INK)
