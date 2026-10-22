"""Small helpers for building mechanism clips (FORMATS.md §1) from the cut kit.

A clip is assembled from cards: `card(key, x, y, ...)` places a cut part so that its pivot pixel lands
on (x, y) in clip px, rotated (deg, clockwise on screen) and scaled. Everything stays rigid cardboard:
rotation on a brad, replacement (swap the card), slide, squash for a swing seen edge-on.
"""
import json, math, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..'))
CUT = os.path.join(SHOTS, 'kits', 'cut')
_CAT = None


def catalog():
    """The cut catalog (another agent may be rewriting it: retry until it parses)."""
    global _CAT
    if _CAT is None:
        for _ in range(20):
            try:
                _CAT = json.load(open(os.path.join(CUT, 'catalog.json')))
                break
            except Exception:
                time.sleep(2)
    return _CAT


def part(pid):
    """catalog entry for 'sheet/name' (id) or None"""
    sheet = pid.split('/')[0]
    for p in catalog()['sheets'].get(sheet, {}).get('parts', []):
        if p['id'] == pid:
            return p
    return None


_SIZE = {}


def size(path):
    if path not in _SIZE:
        from PIL import Image
        _SIZE[path] = Image.open(path).size
    return _SIZE[path]


class Clip:
    def __init__(self, cid, title, poems, frames, fps=24, loop=True, kind='mech', cm_px=1.0, floor_y=None, view=None, notes=''):
        self.d = {'id': cid, 'title': title, 'kind': kind, 'poems': poems, 'clock': {'fps': fps, 'frames': frames}, 'loop': loop,
                  'image_root': '../../../', 'images': {}, 'cm_px': cm_px}
        if floor_y is not None:
            self.d['floor_y'] = floor_y
        if view:
            self.d['view'] = dict(zip(('x', 'y', 'w', 'h'), view))
        self.n = frames
        self.frames = [[] for _ in range(frames)]
        self.anchors, self.tracks, self.events, self.parts = {}, {}, [], {}
        self.notes = notes
        self.sfx = set()

    # --- images -------------------------------------------------------------------------------------
    def img(self, key, file):
        """register an image; file is relative to shots/ (kits/cut/... or stage/mech/parts/...)"""
        if file.startswith('kits/cut/') is False and not file.startswith('stage/') and not file.startswith('kits/'):
            file = 'kits/cut/' + file
        self.d['images'][key] = file
        self.parts[key] = file
        return key

    def wh(self, key):
        return size(os.path.join(SHOTS, self.d['images'][key]))

    # --- ops ----------------------------------------------------------------------------------------
    def M(self, key, x, y, rot=0.0, s=1.0, sx=1.0, sy=1.0, px=None, py=None, flip=False, skew=0.0):
        """matrix placing image pixel (px, py) (default centre) at (x, y)"""
        w, h = self.wh(key)
        px = w / 2 if px is None else px
        py = h / 2 if py is None else py
        fx = -1 if flip else 1
        r = math.radians(rot)
        cs, sn = math.cos(r), math.sin(r)
        a0, d0 = s * sx * fx, s * sy
        # M = R * [[a0, skew*d0],[0, d0]]
        a, c = cs * a0, cs * skew * d0 - sn * d0
        b, d = sn * a0, sn * skew * d0 + cs * d0
        e = x - (a * px + c * py)
        f = y - (b * px + d * py)
        return [round(v, 4) for v in (a, b, c, d, e, f)]

    def card(self, f, key, x, y, a=None, blend=None, **kw):
        op = {'t': 'img', 'id': key, 'm': self.M(key, x, y, **kw)}
        if a is not None:
            if a <= 0.003:
                return
            op['a'] = round(min(1, a), 3)
        if blend:
            op['blend'] = blend
        self.frames[f].append(op)

    def glow(self, f, x, y, r, color, a=1.0, blend=None):
        if a <= 0.003:
            return
        op = {'t': 'glow', 'x': round(x, 1), 'y': round(y, 1), 'r': round(r, 1), 'color': color, 'a': round(a, 3)}
        if blend:
            op['blend'] = blend
        self.frames[f].append(op)

    def poly(self, f, pts, fill=None, stroke=None, w=None, a=None, blend=None):
        op = {'t': 'poly', 'pts': [[round(x, 1), round(y, 1)] for x, y in pts]}
        if fill: op['fill'] = fill
        if stroke: op['stroke'] = stroke
        if w: op['w'] = w
        if a is not None: op['a'] = round(a, 3)
        if blend: op['blend'] = blend
        self.frames[f].append(op)

    def line(self, f, pts, stroke, w=2, a=None, dash=None, blend=None):
        op = {'t': 'line', 'pts': [[round(x, 1), round(y, 1)] for x, y in pts], 'stroke': stroke, 'w': w}
        if a is not None: op['a'] = round(a, 3)
        if dash: op['dash'] = dash
        if blend: op['blend'] = blend
        self.frames[f].append(op)

    def clip(self, f, pts):
        self.frames[f].append({'t': 'clip', 'pts': [[round(x, 1), round(y, 1)] for x, y in pts]})

    def unclip(self, f):
        self.frames[f].append({'t': 'unclip'})

    def plate(self, f, src, x, y, w, h, video=False, poster=None, a=None, sx=None, sy=None, sw=None, sh=None):
        op = {'t': 'plate', 'src': src, 'm': [1, 0, 0, 1, round(x, 2), round(y, 2)], 'w': round(w, 2), 'h': round(h, 2)}
        if video: op['video'] = True
        if poster: op['poster'] = poster
        if a is not None: op['a'] = round(a, 3)
        for k, v in (('sx', sx), ('sy', sy), ('sw', sw), ('sh', sh)):
            if v is not None: op[k] = round(v, 4)
        self.frames[f].append(op)

    def text(self, f, x, y, s, txt, color='#efe6da', a=None, rot=None):
        op = {'t': 'text', 'x': x, 'y': y, 's': s, 'color': color, 'txt': txt}
        if a is not None: op['a'] = round(a, 3)
        if rot: op['rot'] = rot
        self.frames[f].append(op)

    def shadow(self, f, x, y, rx, a=0.6, ry=None):
        op = {'t': 'shadow', 'x': round(x, 1), 'y': round(y, 1), 'rx': round(rx, 1), 'a': round(a, 3)}
        if ry: op['ry'] = round(ry, 1)
        self.frames[f].append(op)

    def bg(self, f, color):
        self.frames[f].append({'t': 'bg', 'color': color})

    # --- sockets & sound ----------------------------------------------------------------------------
    def anchor(self, name, track):
        """track: list of (x, y) per frame, or one (x, y)"""
        if isinstance(track[0], (int, float)):
            self.anchors[name] = [round(track[0], 1), round(track[1], 1)]
        else:
            self.anchors[name] = [round(track[0][0], 1), round(track[0][1], 1)]
            if any(abs(p[0] - track[0][0]) > .2 or abs(p[1] - track[0][1]) > .2 for p in track):
                self.tracks[name] = [[round(x, 1), round(y, 1)] for x, y in track]

    def event(self, f, sfx, label):
        self.events.append({'f': f, 'sfx': sfx, 'label': label})
        self.sfx.add(sfx)

    def size_cm(self, w, h):
        self.d['size_cm'] = {'w': w, 'h': h}

    # --- out ----------------------------------------------------------------------------------------
    def save(self, path):
        d = dict(self.d)
        d['anchors'] = self.anchors
        if self.tracks:
            d['anchor_tracks'] = self.tracks
        d['events'] = sorted(self.events, key=lambda e: e['f'])
        d['frames'] = [{'f': i, 'draw': ops} for i, ops in enumerate(self.frames)]
        d['notes'] = self.notes
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as fh:
            json.dump(d, fh, separators=(',', ':'))
        return d


def ease(p):
    p = max(0.0, min(1.0, p))
    return p * p * (3 - 2 * p)


def lerp(a, b, p):
    return a + (b - a) * p


def flick(seed, f, lo=0.75, hi=1.0, rate=1.0):
    """deterministic lamp flicker in [lo, hi]"""
    v = (math.sin(f * 1.7 * rate + seed * 3.1) * 0.5 + math.sin(f * 4.3 * rate + seed * 7.7) * 0.3 + math.sin(f * 0.6 * rate + seed) * 0.2)
    return lo + (hi - lo) * (0.5 + 0.5 * v)
