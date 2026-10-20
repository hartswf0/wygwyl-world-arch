"""Shared code for every weave passage.

A passage is: a registry of parts (assets.json), a set (plate + masks), a clip script that evaluates every frame once,
and a display list per frame that shots/weave.html draws without knowing anything about the passage.

The display list (frames[f]['draw']) is a list of ops. Every op has 't' (type) and 'k' (camera parallax plane, 0..1).
  img    {id, m:[a,b,c,d,e,f] | box:[x,y,w,h], a, op, sh, dust, mask, wipe}
  warp   {id, quad:[[x,y]*4], mask, grade:[r,g,b,a], tex, texa, a}          (an image mapped onto a quad)
  tint   {color, mask, op, a}
  rect   {color, a, op}                                                       (full-frame fill on its plane)
  glow   {x, y, r, color, a, op}
  dots   {pts:[[x,y,r,a]...], color}                                          (dust, debris)
  line   {pts:[[x,y]...], w, color, boil}                                     (drawn grease-pencil line)
  label  {txt, x, y, size, rot, fill, back, a}                                (hand-lettered tape)
  proc   {name, ...}                                                          (a named drawn element: floor, box, ground)
  inset  {id, x, y, w, h, rot, cap, sub, a}                                   (screen space)
Images are named in clip['images'] (id -> url relative to shots/weave/); masks listed in clip['masks'] are converted
from greyscale to alpha by the renderer. Sequences (archive frames) are ids of the form 'seq:<name>:<n>'.
"""
import json, math, os, wave
import numpy as np
import cv2

WEAVE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(WEAVE))
W, H = 1920, 1080


# ---------------- time ----------------
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def key(t, ks):
    """piecewise smoothstep over [(t, v), ...]; v may be a number or a sequence"""
    if t <= ks[0][0]:
        return ks[0][1]
    for (ta, va), (tb, vb) in zip(ks, ks[1:]):
        if t <= tb:
            x = ease((t - ta) / max(1e-9, tb - ta))
            if isinstance(va, (list, tuple, np.ndarray)):
                return [a + (b - a) * x for a, b in zip(va, vb)]
            return va + (vb - va) * x
    return ks[-1][1]


def words(path, t0):
    W_ = json.load(open(path))['words']

    def w(word, k=0, end=False):
        hits = [x for x in W_ if x['w'].lower().strip('.,!?') == word]
        x = hits[k]
        return (x['t1'] if end else x['t0']) - t0
    return W_, w


# ---------------- 2D rig ----------------
def rot(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s], [s, c]])


class Rig:
    """Parts with pivots and sockets (in their own image pixels), drawn at a scale."""

    def __init__(self, parts, scale):
        self.P = parts
        self.S = scale

    def mat(self, part, pos, ang, scale=None):
        s = self.S if scale is None else scale
        p = np.array(self.P[part]['pivot'], float)
        R = rot(ang) * s
        t = np.array(pos, float) - R @ p
        return [R[0, 0], R[1, 0], R[0, 1], R[1, 1], t[0], t[1]]

    def sock(self, part, name, pos, ang, scale=None):
        s = self.S if scale is None else scale
        p = np.array(self.P[part]['pivot'], float)
        q = np.array(self.P[part]['sockets'][name], float) if isinstance(name, str) else np.array(name, float)
        return np.array(pos, float) + rot(ang) @ ((q - p) * s)

    def bone_ang(self, part, a, b):
        s = self.P[part]['sockets']
        v = np.array(s[b], float) - np.array(s[a], float)
        return math.degrees(math.atan2(v[1], v[0]))

    def blen(self, part, a, b):
        s = self.P[part]['sockets']
        return float(np.linalg.norm(np.array(s[b], float) - np.array(s[a], float))) * self.S

    def pos_for_socket(self, part, name, world, ang):
        """pivot position that puts socket `name` at `world` with rotation ang"""
        return np.array(world, float) - (self.sock(part, name, (0, 0), ang))


def ik2(S0, Wt, L1, L2, elbow='down'):
    """two-bone IK. Returns (upper angle, fore angle, reach ratio, clamped?) in degrees, world space, y down."""
    d = np.asarray(Wt, float) - np.asarray(S0, float)
    D = float(np.linalg.norm(d))
    Dc = min(max(D, abs(L1 - L2) * 1.001 + 1e-6), (L1 + L2) * 0.9995)
    a = math.acos(max(-1, min(1, (L1 * L1 + Dc * Dc - L2 * L2) / (2 * L1 * Dc))))
    base = math.atan2(d[1], d[0])
    sols = []
    for sgn in (1, -1):
        ua = base + sgn * a
        E = np.asarray(S0, float) + L1 * np.array([math.cos(ua), math.sin(ua)])
        sols.append((E, ua))
    if elbow == 'down':
        E, ua = max(sols, key=lambda s: s[0][1])
    elif elbow == 'up':
        E, ua = min(sols, key=lambda s: s[0][1])
    elif elbow == 'back':
        E, ua = min(sols, key=lambda s: s[0][0])
    else:  # 'front'
        E, ua = max(sols, key=lambda s: s[0][0])
    tgt = np.asarray(S0, float) + d * (Dc / max(D, 1e-9))
    fa = math.atan2(tgt[1] - E[1], tgt[0] - E[0])
    return math.degrees(ua), math.degrees(fa), D / (L1 + L2), D > (L1 + L2) * 0.9995


# ---------------- display-list ops ----------------
def r(v, n=2):
    return [round(float(x), n) for x in v]


def op_img(id_, m=None, box=None, k=1.0, a=1.0, op=None, sh=0, dust=0.0, mask=None, wipe=None):
    o = {'t': 'img', 'id': id_, 'k': k}
    if m is not None:
        o['m'] = [round(float(m[0]), 5), round(float(m[1]), 5), round(float(m[2]), 5), round(float(m[3]), 5),
                  round(float(m[4]), 2), round(float(m[5]), 2)]
    if box is not None:
        o['box'] = r(box)
    if a != 1.0:
        o['a'] = round(float(a), 4)
    if op:
        o['op'] = op
    if sh:
        o['sh'] = sh
    if dust > 0.001:
        o['dust'] = round(float(dust), 3)
    if mask:
        o['mask'] = mask
    if wipe:
        o['wipe'] = wipe
    return o


def op_label(txt, x, y, size=24, rot_=0.0, fill='#fff3e0', back='#2a1608', a=1.0, k=1.0):
    return {'t': 'label', 'txt': txt, 'x': round(x, 1), 'y': round(y, 1), 'size': size, 'rot': round(rot_, 4),
            'fill': fill, 'back': back, 'a': round(float(a), 3), 'k': k}


def cam_t(z, c, k):
    """the renderer's camT: plane k zooms 1+(z-1)k about a centre that moves k of the way. returns (s, tx, ty)"""
    zz = 1 + (z - 1) * k
    kk = min(1.0, k)
    ox, oy = 960 + (c[0] - 960) * kk, 540 + (c[1] - 540) * kk
    return zz, 960 - ox * zz, 540 - oy * zz


def label_box(txt, x, y, size):
    """world bbox of a label as letter() draws it (Permanent Marker caps measured at about 0.66 em per glyph)"""
    w = 0.66 * size * len(txt)
    return x - 10, y - size * 1.02, x + w + 12, y + size * 0.38


def label_fit(txt, x, y, size, k, z, c, margin=28):
    """move a label (in its plane) so that its whole box is on screen under camera (z, c)"""
    s, tx, ty = cam_t(z, c, k)
    x0, y0, x1, y1 = label_box(txt, x, y, size)
    sx0, sx1, sy0, sy1 = x0 * s + tx, x1 * s + tx, y0 * s + ty, y1 * s + ty
    dx = dy = 0.0
    if sx1 > W - margin: dx = (W - margin - sx1)
    if sx0 + dx < margin: dx = margin - sx0
    if sy0 < margin: dy = margin - sy0
    if sy1 + dy > H - margin: dy = H - margin - sy1
    return x + dx / s, y + dy / s


def label_onscreen(txt, x, y, size, k, z, c):
    s, tx, ty = cam_t(z, c, k)
    x0, y0, x1, y1 = label_box(txt, x, y, size)
    sx0, sx1, sy0, sy1 = x0 * s + tx, x1 * s + tx, y0 * s + ty, y1 * s + ty
    return sx0 >= 0 and sy0 >= 0 and sx1 <= W and sy1 <= H


# ---------------- measuring what the critic sees ----------------
_alpha_cache = {}


def part_alpha(path):
    if path not in _alpha_cache:
        _alpha_cache[path] = cv2.imread(path, cv2.IMREAD_UNCHANGED)[..., 3]
    return _alpha_cache[path]


def raster_ops(ops, files, ids=None):
    """binary mask (1080x1920) of the listed img ops with a matrix, as the renderer would place them (stage plane)"""
    m = np.zeros((H, W), np.uint8)
    for o in ops:
        if o.get('t') != 'img' or 'm' not in o or (ids is not None and o['id'] not in ids):
            continue
        a = part_alpha(files[o['id']])
        M = np.array([[o['m'][0], o['m'][2], o['m'][4]], [o['m'][1], o['m'][3], o['m'][5]]], np.float32)
        m |= (cv2.warpAffine(a, M, (W, H)) > 128).astype(np.uint8)
    return m


# ---------------- assets ----------------
def alpha_from_white(bgr, extra_bg=None, max_hole=None, sat=28, val=200):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    bg = (hsv[..., 1] < sat) & (hsv[..., 2] > val)
    if extra_bg is not None:
        bg |= extra_bg
    fg = (~bg).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:
        k = 1 + int(np.argmax(st[1:, 4]))
        fg = (lab == k).astype(np.uint8)
    if max_hole is None:
        cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        solid = np.zeros_like(fg)
        cv2.drawContours(solid, cnts, -1, 1, -1)
    else:
        solid = fg.copy()
        n2, l2, s2, _ = cv2.connectedComponentsWithStats(1 - fg)
        for i in range(1, n2):
            x, y, w, h, a = s2[i]
            if a < max_hole and x > 0 and y > 0 and x + w < fg.shape[1] and y + h < fg.shape[0]:
                solid[l2 == i] = 1
    a = cv2.GaussianBlur(solid.astype(np.float32), (3, 3), 0.6)
    return (a * 255).astype(np.uint8)


def paper_cut(rgba, rng, border=7, jag=(3, 10)):
    """trim an image's alpha with scissors: an irregular outline and a thin white paper border"""
    a = rgba[..., 3]
    m = (a > 128).astype(np.uint8)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cnts:
        return rgba
    c = max(cnts, key=cv2.contourArea)
    approx = cv2.approxPolyDP(c, 2.5, True)[:, 0, :].astype(np.float32)
    # push every vertex out a little, irregularly: scissors do not follow the edge exactly
    M = cv2.moments(c)
    cx, cy = M['m10'] / max(1, M['m00']), M['m01'] / max(1, M['m00'])
    out = []
    for x, y in approx:
        v = np.array([x - cx, y - cy]); n = np.linalg.norm(v) + 1e-6
        out.append([x, y] + v / n * rng.uniform(*jag))
    h, w = a.shape
    outer = np.zeros((h, w), np.uint8)
    cv2.fillPoly(outer, [np.array(out, np.int32)], 255)
    inner = cv2.erode(outer, np.ones((border, border), np.uint8))
    res = rgba.copy()
    res[..., 3] = outer
    edge = (outer > 0) & ((inner == 0) | (a < 128))
    res[edge, :3] = (226, 232, 236)
    return res


def pack_atlas(items, out_png, width=2048, pad=4):
    """items: list of (id, rgba). Returns {id: [x,y,w,h]}; every packed rect is checked against its source."""
    order = sorted(range(len(items)), key=lambda i: -items[i][1].shape[0])
    x = y = rowh = 0
    rects = {}
    for i in order:
        h, w = items[i][1].shape[:2]
        if x + w + pad > width:
            x, y, rowh = 0, y + rowh + pad, 0
        rects[i] = (x, y, w, h)
        x += w + pad
        rowh = max(rowh, h)
    Hh = y + rowh
    atlas = np.zeros((Hh, width, 4), np.uint8)
    for i, (x, y, w, h) in rects.items():
        atlas[y:y + h, x:x + w] = items[i][1]
    cv2.imwrite(out_png, atlas)
    worst = 0
    res = {}
    for i, (x, y, w, h) in rects.items():
        worst = max(worst, int(np.abs(atlas[y:y + h, x:x + w].astype(int) - items[i][1].astype(int)).max()))
        res[items[i][0]] = [x, y, w, h]
    assert worst == 0, 'atlas mismatch %d' % worst
    return res, [width, Hh]


def jdump(obj, path, compact=False):
    d = lambda o: o.item() if hasattr(o, 'item') else (o.tolist() if hasattr(o, 'tolist') else str(o))
    with open(path, 'w') as f:
        if compact:
            json.dump(obj, f, separators=(',', ':'), default=d)
        else:
            json.dump(obj, f, indent=1, default=d)


# ---------------- sound ----------------
SR = 48000


def wav_read(path):
    with wave.open(path) as w:
        ch, sr, n = w.getnchannels(), w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
    assert sr == SR, (path, sr)
    return x.reshape(-1, ch).mean(1) if ch > 1 else x


def wav_write(path, st):
    st = np.asarray(st, np.float32)
    st = st / max(1.0, np.abs(st).max() / 0.95)
    with wave.open(path, 'w') as w:
        w.setnchannels(st.shape[1] if st.ndim > 1 else 1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def movavg(x, n):
    """cumulative-sum moving average (never an O(N x kernel) convolution over full-length audio)"""
    n = max(1, int(n))
    c = np.cumsum(np.concatenate([[0.0], x]))
    y = (c[n:] - c[:-n]) / n
    return np.concatenate([np.full(n // 2, y[0]), y, np.full(len(x) - len(y) - n // 2, y[-1])])


def reverb(x, rng, secs=1.9, wet=0.45):
    n = int(secs * SR)
    ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.linspace(0, 7, n)).astype(np.float32)
    ir /= np.sqrt((ir ** 2).sum())
    m = 1 << int(np.ceil(np.log2(len(x) + n)))
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:len(x)]
    return (1 - wet) * x + wet * y.astype(np.float32)
