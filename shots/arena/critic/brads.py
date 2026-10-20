"""Read the brads that are drawn on each card, instead of typing pivots by hand.

TSU-01: "Pivots go on the visible joint connectors." Every card in the man's
library has its connectors drawn on it: brass discs, or punched holes. On a
whole figure brass is lost among the skin and cardboard (REGISTRATION.md).
On a single cut card it separates cleanly, because nothing else on a limb is
brass-yellow.

    read(path, kind) -> {'sockets': {name: [x, y]}, 'guessed': [names], 'brads': [[x, y, area]]}

`kind` is the card's role (uarm, farm, thigh, shin, hand, boot, pelvis, torso,
head). A socket the card does not draw is placed by a rule and listed in
`guessed`, so the critic can see which joints are read and which are invented.
"""
import numpy as np
from PIL import Image
from scipy import ndimage as nd

_cache = {}


def _components(mask, amin, amax, max_aspect=2.0, min_fill=0.45):
    lab, n = nd.label(mask)
    out = []
    for i, sl in enumerate(nd.find_objects(lab), 1):
        if sl is None:
            continue
        m = lab[sl] == i
        a = int(m.sum())
        if not (amin <= a <= amax):
            continue
        h, w = m.shape
        if max(h, w) > max_aspect * min(h, w) or a / (h * w) < min_fill:
            continue
        ys, xs = np.nonzero(m)
        out.append([float(xs.mean() + sl[1].start), float(ys.mean() + sl[0].start), a])
    return out


def brads(path):
    im = Image.open(path).convert('RGBA')
    A = np.asarray(im)[:, :, 3] > 128
    hsv = np.asarray(im.convert('RGB').convert('HSV')).astype(float)
    H, S, V = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    brass = nd.binary_opening(A & (H > 30) & (H < 65) & (S > 0.3) & (V > 0.35))
    found = _components(brass, 30, 400)
    holes = nd.binary_fill_holes(A) & ~A
    found += _components(holes, 20, 600, max_aspect=2.5, min_fill=0.35)
    return im, A, found


def _ink(A):
    ys = np.nonzero(A.any(1))[0]
    xs = np.nonzero(A.any(0))[0]
    return xs[0], xs[-1], ys[0], ys[-1]


def _row_centre(A, y):
    y = int(np.clip(round(y), 0, A.shape[0] - 1))
    xs = np.nonzero(A[y])[0]
    return float((xs[0] + xs[-1]) / 2) if len(xs) else A.shape[1] / 2


def read(path, kind):
    if (path, kind) in _cache:
        return _cache[(path, kind)]
    im, A, found = brads(path)
    h, w = A.shape
    x0, x1, y0, y1 = _ink(A)
    by_y = sorted(found, key=lambda b: b[1])
    s, guessed = {}, []

    def guess(name, p):
        s[name] = [float(p[0]), float(p[1])]
        guessed.append(name)

    if kind in ('uarm', 'farm', 'thigh', 'shin'):
        top = [b for b in by_y if b[1] < y0 + 0.35 * (y1 - y0)]
        bot = [b for b in by_y if b[1] > y0 + 0.65 * (y1 - y0)]
        if top:
            s['A'] = top[0][:2]
        else:
            guess('A', (_row_centre(A, y0 + 0.06 * (y1 - y0)), y0 + 0.06 * (y1 - y0)))
        if bot:
            s['B'] = bot[-1][:2]
        else:
            guess('B', (_row_centre(A, y1 - 0.06 * (y1 - y0)), y1 - 0.06 * (y1 - y0)))
    elif kind == 'hand':
        # The wrist is the brad nearest the cuff end (left edge; cards face +x).
        if found:
            s['wrist'] = min(found, key=lambda b: b[0])[:2]
        else:
            guess('wrist', (x0 + 0.15 * (x1 - x0), _col_centre(A, x0 + 0.15 * (x1 - x0))))
    elif kind == 'boot':
        if found:
            s['ankle'] = min(found, key=lambda b: b[1])[:2]
        else:
            guess('ankle', (x0 + 0.3 * (x1 - x0), y0 + 0.2 * (y1 - y0)))
        s['sole'] = [float(x0 + x1) / 2, float(y1)]
    elif kind == 'pelvis':
        top = [b for b in found if b[1] < h / 2]
        bot = [b for b in found if b[1] >= h / 2]
        if top:
            s['waist'] = [float(np.mean([b[0] for b in top])), float(np.mean([b[1] for b in top]))]
        else:
            guess('waist', (_row_centre(A, y0 + 0.1 * h), y0 + 0.1 * h))
        if len(bot) >= 2:
            l, r = sorted(bot, key=lambda b: b[0])[0], sorted(bot, key=lambda b: b[0])[-1]
            s['hip_L'], s['hip_R'] = l[:2], r[:2]
        else:
            guess('hip_L', (x0 + 0.25 * (x1 - x0), y0 + 0.85 * (y1 - y0)))
            guess('hip_R', (x0 + 0.75 * (x1 - x0), y0 + 0.85 * (y1 - y0)))
    elif kind == 'torso':
        low = [b for b in found if b[1] > y0 + 0.7 * (y1 - y0)]
        high = [b for b in found if b[1] < y0 + 0.3 * (y1 - y0)]
        if low:
            s['hip'] = [float(np.mean([b[0] for b in low])), float(np.mean([b[1] for b in low]))]
        else:
            guess('hip', (_row_centre(A, y1 - 0.08 * (y1 - y0)), y1 - 0.08 * (y1 - y0)))
        if high:
            s['shoulder'] = [float(np.mean([b[0] for b in high])), float(np.mean([b[1] for b in high]))]
        else:
            guess('shoulder', (_row_centre(A, y0 + 0.12 * (y1 - y0)), y0 + 0.12 * (y1 - y0)))
        guess('neck', (_row_centre(A, y0 + 0.02 * (y1 - y0)), y0 + 0.02 * (y1 - y0)))
    elif kind == 'head':
        low = [b for b in found if b[1] > y0 + 0.5 * (y1 - y0)]
        if low:
            s['neck'] = max(low, key=lambda b: b[1])[:2]
        else:
            guess('neck', (_row_centre(A, y1 - 0.1 * (y1 - y0)), y1 - 0.1 * (y1 - y0)))
        s['crown'] = [_row_centre(A, y0), float(y0)]
    r = {'sockets': {k: [float(v[0]), float(v[1])] for k, v in s.items()}, 'guessed': guessed,
         'brads': [[round(b[0], 1), round(b[1], 1), b[2]] for b in found], 'size': [w, h]}
    _cache[(path, kind)] = r
    return r


def _col_centre(A, x):
    x = int(np.clip(round(x), 0, A.shape[1] - 1))
    ys = np.nonzero(A[:, x])[0]
    return float((ys[0] + ys[-1]) / 2) if len(ys) else A.shape[0] / 2
