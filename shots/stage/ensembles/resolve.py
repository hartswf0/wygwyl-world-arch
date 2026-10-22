"""Resolve a scene recipe (ensembles + cast + props + one archive still) into flat stage layers through the
scene's camera (scale.py). Every layer keeps `ens` (the ensemble it came from) and `role` so the stage and
the timeline can find the poet's pose, the hidden action and the archive still.

Depth: an ensemble is placed with its anchor at depth factor k (1 = the subject's distance; 2 = twice as far).
A layer z_cm behind the anchor sits at k + z_cm / d, d = the subject's distance from the camera
(visible_cm / 0.73: a ~40 degree vertical field). Things at depth k stand on the floor line
y = horizon + (foot - horizon) / k and are drawn at ppc / k pixels per cm.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import part, size, aspect, hole, load_ensembles, PARTS

W, H = 1600, 900
FOV = .73


def rnd(v):
    return int(round(v))


class Cam:
    def __init__(self, cam):
        self.c = cam
        self.Hy, self.foot, self.ppc = cam['horizon_y'], cam['foot_y'], cam['ppc']
        self.d = cam['visible_cm'] / FOV

    def at(self, k):
        k = max(.22, k)
        return self.Hy + (self.foot - self.Hy) / k, self.ppc / k

    def k_of(self, k0, z):
        return max(.22, k0 + z / self.d)


def card_rect(L):
    h = L.get('h') or (L['w'] * aspect(L['part']) if L.get('part') else L['w'] * L.get('ar', .5625))
    return (L['x'] - L['w'] / 2, L['y'] - h / 2, L['x'] + L['w'] / 2, L['y'] + h / 2)


def resolve_ensemble(E, place, cam, items, seq):
    """Append (sortkey, seq, layer) for ensemble E placed at place={k, x, flip, skip, swap, op, only}."""
    k0, xa = place.get('k', 1.0), place.get('x', 800)
    flip = place.get('flip', False)
    sgn = -1 if flip else 1
    _, ppc0 = cam.at(k0)
    X0 = (xa - 800) / ppc0
    skip, swap = set(place.get('skip', [])), place.get('swap', {})
    only = place.get('only')
    named = {}
    tag = {'ens': E['id']}

    def screen_x(x_cm, k):
        return 800 + (X0 + sgn * x_cm) * cam.at(k)[1]

    def src_of(L):
        nm = L.get('name')
        if nm in swap:
            r = swap[nm]
            return ({'kind': 'plane', 'src': r} if r.startswith(('sets/', '../')) else {'part': part(r)})
        return {'kind': 'plane', 'src': L['src']} if L.get('src') else {'part': L['part']}

    def ar_of(S):
        if 'part' in S:
            return aspect(S['part'])
        from PIL import Image
        im = Image.open(os.path.join(os.path.dirname(HERE), S['src']))
        return im.size[1] / im.size[0]

    out = []
    for i, L in enumerate(E['layers']):
        nm = L.get('name')
        if (nm and nm in skip) or (only and nm not in only and not L.get('fill')):
            continue
        if L.get('in_hole') or L.get('on'):
            continue
        S = src_of(L)
        ex = {k: L[k] for k in ('op', 'blend', 'rot') if k in L}
        if 'op' in place and L.get('fill') in (None, 'strip'):
            ex['op'] = place['op'] * ex.get('op', 1)
        f = L.get('fill')
        if f == 'sky':
            lay = S | {'x': 800, 'y': rnd((cam.Hy + 40 - 12) / 2), 'w': 1760, 'h': rnd(cam.Hy + 40 + 12)}
            key = 1e9
        elif f == 'band':
            h = L['h_px']
            x = L['x_px'] if not flip else 1600 - L['x_px']
            lay = S | {'x': rnd(x), 'y': rnd(cam.Hy + L['y_px'] - h / 2), 'w': rnd(L['w_px']), 'h': rnd(h)}
            key = 1e7 - i
        elif f == 'far':
            h = L['h_px']
            w = L.get('w_px') or h / ar_of(S)
            x = L['x_px'] if not flip else 1600 - L['x_px']
            lay = S | {'x': rnd(x), 'y': rnd(cam.Hy + L['y_px']), 'w': rnd(w), 'h': rnd(h)}
            if L.get('flip_v'):
                lay |= {'rot': 180, 'flip': True}
            key = (1e6 - 1 - i) if L.get('order') == 'water' else (1e8 - i)
        elif f == 'water':
            top = cam.Hy - 3
            bot = 910 if L.get('z_near') is None else cam.at(cam.k_of(k0, L['z_near']))[0] + 4
            lay = S | {'x': 800, 'y': rnd((top + bot) / 2), 'w': 1760, 'h': rnd(bot - top)}
            key = 1e6
        elif f == 'floor':
            kf = cam.k_of(k0, L['z_far'])
            top = cam.at(kf)[0] - 6
            bot = 912 if L.get('z_near') is None else cam.at(cam.k_of(k0, L['z_near']))[0] + 6
            if bot <= top:
                continue
            lay = S | {'x': 800, 'y': rnd((top + bot) / 2), 'w': 1780, 'h': rnd(bot - top)}
            key = kf - 1e-4
        elif f == 'strip':
            k = cam.k_of(k0, L['z_cm'])
            fy, pk = cam.at(k)
            bot = fy - L.get('y_cm', 0) * pk
            top = -14 if L.get('to_top') else bot - L['h_cm'] * pk
            w = L['w_px'] if L.get('w_px') else L['w_cm'] * pk
            x = screen_x(L.get('x_cm', 0), k)
            lay = S | {'x': rnd(x), 'y': rnd((top + bot) / 2), 'w': rnd(w), 'h': rnd(bot - top)}
            if L.get('to_top') and L.get('h_cm'):   # keep the card's own bottom band (skirting, window) where it belongs
                full = L['h_cm'] * pk
                if full > bot - top:
                    lay['y'], lay['h'] = rnd(bot - full / 2), rnd(full)
            key = k
        else:   # a standing card
            k = cam.k_of(k0, L['z_cm'])
            fy, pk = cam.at(k)
            w, h = L['w_cm'] * pk, L['h_cm'] * pk
            bot = fy - L['y_cm'] * pk
            x = screen_x(L['x_cm'], k)
            lay = S | {'x': rnd(x), 'y': rnd(bot - h / 2), 'w': rnd(w)}
            if L.get('stretch') or 'part' not in S or ('part' in S and S['part'] != L.get('part')):
                lay['h'] = rnd(h)
            if L.get('flip', False) != flip:
                lay['flip'] = True
            key = k
            if L.get('reflect'):
                R = dict(lay, h=rnd(h), y=rnd(fy - L['y_cm'] * pk + h / 2 + 2), rot=180, flip=not lay.get('flip', False),
                         op=L['reflect'].get('op', .3), label='reflection', role='reflection') | tag
                R.pop('blend', None)
                out.append((key + 1e-4, R))
        lay.update(ex)
        lay.update(tag)
        if nm:
            lay['label'] = nm
            named[nm] = (key, lay)
        if L.get('hole'):
            lay['_hole'] = L['hole']
        out.append((key, lay))
    # portal content behind a holed card, paint on a card
    for L in E['layers']:
        hn = L.get('in_hole') or L.get('on')
        if not hn or hn not in named:
            continue
        key, holder = named[hn]
        if not holder.get('h'):
            holder['h'] = rnd(holder['w'] * aspect(holder['part'])) if 'part' in holder else holder['w']
        x0, y0, x1, y1 = card_rect(holder)
        if L.get('in_hole'):
            hx = holder.get('_hole') or [.3, .2, .7, .7]
            if holder.get('flip'):
                hx = [1 - hx[2], hx[1], 1 - hx[0], hx[3]]
            x0, y0, x1, y1 = x0 + hx[0] * (x1 - x0), y0 + hx[1] * (y1 - y0), x0 + hx[2] * (x1 - x0), y0 + hx[3] * (y1 - y0)
        rx = L['rect']
        if holder.get('flip'):
            rx = [1 - rx[2], rx[1], 1 - rx[0], rx[3]]
        a, b, c, d = x0 + rx[0] * (x1 - x0), y0 + rx[1] * (y1 - y0), x0 + rx[2] * (x1 - x0), y0 + rx[3] * (y1 - y0)
        S = src_of(L)
        lay = S | {'x': rnd((a + c) / 2), 'y': rnd((b + d) / 2), 'w': rnd(c - a), 'h': rnd(d - b)} | tag
        lay.update({k: L[k] for k in ('op', 'blend', 'rot') if k in L})
        lay['label'] = ('portal: ' if L.get('in_hole') else 'on ') + hn + (' · ' + L['name'] if L.get('name') else '')
        out.append(((key + 2e-3) if L.get('in_hole') else (key - 2e-3), lay))
    for key, lay in out:
        seq[0] += 1
        items.append((key, seq[0], lay))
    return named


def slot_pos(E, place, slot, cam):
    S = next(s for s in E['slots'] if s['name'] == slot)
    k0, xa = place.get('k', 1.0), place.get('x', 800)
    sgn = -1 if place.get('flip') else 1
    X0 = (xa - 800) / cam.at(k0)[1]
    k = cam.k_of(k0, S['z_cm'])
    fy, pk = cam.at(k)
    return S, k, 800 + (X0 + sgn * S['x_cm']) * pk, fy - S['y_cm'] * pk, pk


def overlap(a, b):
    ax0, ay0, ax1, ay1 = card_rect(a)
    bx0, by0, bx1, by1 = card_rect(b)
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


_clipbox = {}


def clip_box(path):
    """What the stage engine (engine.js autoBox / frameBox) computes for a clip: its box (every n/50-th frame, the
    parts' corners transformed, +20 px), its floor line, cm_px and the actor's feet x at frame 0. An action layer is
    then sized at the scene's px/cm at its depth and stood on the floor line where the still pose stood."""
    if path in _clipbox:
        return _clipbox[path]
    import json
    from PIL import Image
    j = json.load(open(path))
    here = os.path.dirname(path)
    arena = os.path.dirname(here) if os.path.basename(here) == 'clips' and 'arena' in path else here
    sizes = {}
    for k, f in j['images'].items():
        for base in (here, arena):
            q = os.path.normpath(os.path.join(base, f))
            if os.path.exists(q):
                sizes[k] = Image.open(q).size
                break
    def bounds(draw, acc):
        for o in draw:
            if o.get('t') == 'img' and o['id'] in sizes:
                a, b, c, d, e, g = o['m']
                w, h = sizes[o['id']]
                for u, v in ((0, 0), (w, 0), (0, h), (w, h)):
                    acc.append((a * u + c * v + e, b * u + d * v + g))
            elif o.get('t') == 'shadow':
                acc += [(o['x'] - o['rx'], o['y']), (o['x'] + o['rx'], o['y'])]
    pts = []
    n = len(j['frames'])
    for fi in range(0, n, max(1, n // 50)):
        bounds(j['frames'][fi]['draw'], pts)
    f0 = []
    bounds([o for o in j['frames'][0]['draw'] if o.get('t') == 'img'], f0)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    fx = [p[0] for p in f0]
    fy1 = max(p[1] for p in f0)
    fl = j.get('floor_y', j.get('floor'))
    feet = min(fl, fy1) if fl is not None and abs(fl - fy1) < 60 else fy1
    cm_px = j.get('cm_px') or (j.get('cast') or [{}])[0].get('cm_px', 2.35)
    _clipbox[path] = {'box': [min(xs) - 20, min(ys) - 20, max(xs) + 20, max(ys) + 20], 'floor': feet, 'cm_px': cm_px,
                      'x_start': (min(fx) + max(fx)) / 2, 'top0': min(p[1] for p in f0)}
    return _clipbox[path]
