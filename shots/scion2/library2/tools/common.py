"""Shared plumbing for the regularized parts library (library2).

Card source: shots/skinlab/library.json (images under shots/kits/cut/). Every canonical part is the source card's
painted pixels, cleaned (components / regions cut away, never repainted) and re-rendered with a similarity
transform (rotation + uniform scale + translation) onto a fixed canvas per part type. See ../README.md.
"""
import json, math, os, re
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
LIB2 = os.path.dirname(HERE)                                  # shots/scion2/library2
SHOTS = os.path.dirname(os.path.dirname(LIB2))                # shots
REPO = os.path.dirname(SHOTS)
CUT = os.path.join(SHOTS, 'kits', 'cut')

CANON_PPC = 10.0          # canonical pixels per centimetre, every character, every part
# canvas (w, h), pivot position on the canvas, primary-axis direction on the canvas (unit vector, image coords y down)
GRID = {
    'head':      {'canvas': (512, 512), 'pivot': (256, 448), 'axis': (0, -1), 'pivot_name': 'neck',     'tip_name': 'crown'},
    'hand':      {'canvas': (384, 384), 'pivot': (192, 72),  'axis': (0, 1),  'pivot_name': 'wrist',    'tip_name': 'knuckles'},
    'foot':      {'canvas': (512, 384), 'pivot': (256, 96),  'axis': None,    'pivot_name': 'ankle',    'tip_name': 'toe'},
    'upper_arm': {'canvas': (256, 512), 'pivot': (128, 64),  'axis': (0, 1),  'pivot_name': 'shoulder', 'tip_name': 'elbow'},
    'forearm':   {'canvas': (256, 512), 'pivot': (128, 64),  'axis': (0, 1),  'pivot_name': 'elbow',    'tip_name': 'wrist'},
    'thigh':     {'canvas': (320, 640), 'pivot': (160, 80),  'axis': (0, 1),  'pivot_name': 'hip',      'tip_name': 'knee'},
    'shin':      {'canvas': (320, 640), 'pivot': (160, 80),  'axis': (0, 1),  'pivot_name': 'knee',     'tip_name': 'ankle'},
    'torso':     {'canvas': (768, 768), 'pivot': (384, 640), 'axis': (0, -1), 'pivot_name': 'waist',    'tip_name': 'neck'},
    'pelvis':    {'canvas': (640, 512), 'pivot': (320, 128), 'axis': (0, 1),  'pivot_name': 'waist',    'tip_name': 'hip_mid'},
    'feature':   {'canvas': (256, 256), 'pivot': (128, 128), 'axis': (1, 0),  'pivot_name': 'centre',   'tip_name': 'right'},
}

_cache = {}


def load_json(p):
    with open(p) as f:
        return json.load(f)


def cards():
    if 'cards' not in _cache:
        _cache['cards'] = load_json(os.path.join(SHOTS, 'skinlab', 'library.json'))
    return _cache['cards']


def labels():
    if 'labels' not in _cache:
        _cache['labels'] = load_json(os.path.join(SHOTS, 'skinlab', 'labels.json'))['cards']
    return _cache['labels']


def hygiene():
    if 'hyg' not in _cache:
        _cache['hyg'] = load_json(os.path.join(SHOTS, 'scion2', 'evolve', 'lab', 'hygiene.json'))
    return _cache['hyg']


def fixes():
    p = os.path.join(LIB2, 'fixes.json')
    return load_json(p) if os.path.exists(p) else {}


def height_cm(character):
    p = os.path.join(SHOTS, 'skinlab', 'contracts', character + '.json')
    if os.path.exists(p):
        h = load_json(p).get('height_cm')
        if h:
            return float(h)
    return {'young_poet': 120.0, 'ghost_child': 120.0, 'child_traveler': 125.0}.get(character, 175.0)


def card_path(c):
    return os.path.join(CUT, c['img'].split('kits/cut/')[1])


def load_rgba(c):
    return np.array(Image.open(card_path(c)).convert('RGBA'))


def slug(card_id):
    return re.sub(r'[^A-Za-z0-9._-]+', '__', card_id)


# ---------------------------------------------------------------- cleaning

def components(alpha, thr=40):
    n, lab, st, cen = cv2.connectedComponentsWithStats((alpha > thr).astype(np.uint8), 8)
    comps = [dict(i=i, x=int(st[i, 0]), y=int(st[i, 1]), w=int(st[i, 2]), h=int(st[i, 3]), area=int(st[i, 4])) for i in range(1, n)]
    comps.sort(key=lambda d: -d['area'])
    return lab, comps


def keep_main(rgba, extra_keep=0.15):
    """Keep the largest alpha component (and any other component >= extra_keep of it that overlaps its bbox).
    Returns (cleaned rgba, list of removed component descriptions). Soft edge alpha of the kept part is preserved."""
    a = rgba[..., 3]
    lab, comps = components(a)
    if not comps:
        return rgba.copy(), []
    main = comps[0]
    keep = {main['i']}
    removed = []
    for d in comps[1:]:
        inside = (d['x'] >= main['x'] - 2 and d['y'] >= main['y'] - 2 and d['x'] + d['w'] <= main['x'] + main['w'] + 2
                  and d['y'] + d['h'] <= main['y'] + main['h'] + 2)
        if d['area'] >= extra_keep * main['area'] and inside:
            keep.add(d['i'])
        else:
            kind = 'caption' if (d['h'] < 0.12 * main['h'] and d['y'] > main['y'] + 0.8 * main['h']) else 'fragment'
            removed.append(dict(kind=kind, bbox=[d['x'], d['y'], d['w'], d['h']], area=d['area']))
    m = np.isin(lab, list(keep)).astype(np.uint8)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))          # keep the soft fringe around the kept component
    out = rgba.copy()
    out[..., 3] = (out[..., 3] * m).astype(np.uint8)
    return out, removed


def mask_of(rgba, thr=40):
    return rgba[..., 3] > thr


# ---------------------------------------------------------------- transforms

def similarity(pivot_src, pivot_dst, rot_deg, scale):
    """2x3 matrix: card px -> canonical px. rot_deg is counter-clockwise on screen (image y down)."""
    t = math.radians(rot_deg)
    c, s = math.cos(t) * scale, math.sin(t) * scale
    # screen-ccw with y down: x' = c x + s y ; y' = -s x + c y
    M = np.array([[c, s, 0.0], [-s, c, 0.0]])
    p = M[:, :2] @ np.array(pivot_src, float)
    M[:, 2] = np.array(pivot_dst, float) - p
    return M


def rot_to(axis_vec, target_vec):
    """screen-ccw degrees that rotate axis_vec onto target_vec (image coords)."""
    a = math.atan2(-axis_vec[1], axis_vec[0])
    b = math.atan2(-target_vec[1], target_vec[0])
    d = math.degrees(b - a)
    return (d + 180) % 360 - 180


def apply(M, pt):
    if pt is None:
        return None
    p = M[:, :2] @ np.array(pt[:2], float) + M[:, 2]
    return [round(float(p[0]), 1), round(float(p[1]), 1)]


def apply_vec(M, v):
    p = M[:, :2] @ np.array(v, float)
    n = np.linalg.norm(p) or 1
    return [round(float(p[0] / n), 3), round(float(p[1] / n), 3)]


def warp(rgba, M, size):
    """premultiplied warp so edges do not pick up dark fringes"""
    f = rgba.astype(np.float32)
    a = f[..., 3:4] / 255.0
    pm = np.concatenate([f[..., :3] * a, f[..., 3:4]], -1)
    big = max(1.0, 1.0 / math.sqrt(abs(np.linalg.det(M[:, :2]))))
    interp = cv2.INTER_AREA if big > 1.2 else cv2.INTER_LINEAR
    if big > 1.2:     # downscale: pre-blur via pyramid-free resize first for quality
        sc = 1.0 / big
        small = cv2.resize(pm, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
        S = np.array([[1 / sc, 0, 0], [0, 1 / sc, 0], [0, 0, 1]])
        M = (np.vstack([M, [0, 0, 1]]) @ S)[:2]
        pm = small
        interp = cv2.INTER_LINEAR
    out = cv2.warpAffine(pm, M, size, flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a2 = out[..., 3:4] / 255.0
    rgb = np.where(a2 > 1e-3, out[..., :3] / np.maximum(a2, 1e-3), 0)
    return np.clip(np.concatenate([rgb, out[..., 3:4]], -1), 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- sheets

def font(sz):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def grid_bg(size, pivot, step=50):
    w, h = size
    im = Image.new('RGB', size, (246, 244, 238))
    d = ImageDraw.Draw(im)
    for x in range(pivot[0] % step, w, step):
        d.line([(x, 0), (x, h)], fill=(226, 224, 216))
    for y in range(pivot[1] % step, h, step):
        d.line([(0, y), (w, y)], fill=(226, 224, 216))
    d.line([(pivot[0], 0), (pivot[0], h)], fill=(200, 205, 225))
    d.line([(0, pivot[1]), (w, pivot[1])], fill=(200, 205, 225))
    return im


COL = {'pivot': (220, 0, 0), 'kp': (0, 140, 60), 'bone': (0, 120, 220), 'dir': (230, 120, 0)}


def draw_tile(rgba, part_type, kps, bones, label_lines, tile=256, dirs=(), bad=False, size=None):
    """render one sheet tile: canonical image on its grid, keypoints/bones, text"""
    g = GRID[part_type]
    size = size or g['canvas']
    bg = grid_bg(size, g['pivot']).convert('RGBA')
    if rgba is not None:
        bg.alpha_composite(Image.fromarray(rgba))
    s = tile / max(size)
    im = bg.convert('RGB').resize((round(size[0] * s), round(size[1] * s)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    P = lambda p: (p[0] * s, p[1] * s)
    for a, b in bones:
        if kps.get(a) and kps.get(b):
            d.line([P(kps[a]), P(kps[b])], fill=COL['bone'], width=2)
    for k, p in kps.items():
        if p is None or not isinstance(p, (list, tuple)) or len(p) != 2:
            continue
        x, y = P(p)
        if k == 'pivot':
            d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=COL['pivot'], width=3)
            d.line([(x - 9, y), (x + 9, y)], fill=COL['pivot'], width=1)
            d.line([(x, y - 9), (x, y + 9)], fill=COL['pivot'], width=1)
        else:
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=COL['kp'])
    for (p, v) in dirs:
        x, y = P(p)
        d.line([(x, y), (x + v[0] * 40, y + v[1] * 40)], fill=COL['dir'], width=3)
        d.ellipse([x + v[0] * 40 - 3, y + v[1] * 40 - 3, x + v[0] * 40 + 3, y + v[1] * 40 + 3], fill=COL['dir'])
    T = Image.new('RGB', (tile, tile + 15 * len(label_lines) + 6), (255, 255, 255) if not bad else (255, 236, 236))
    T.paste(im, ((tile - im.width) // 2, 0))
    dd = ImageDraw.Draw(T)
    f = font(11)
    for i, line in enumerate(label_lines):
        dd.text((4, tile + 3 + 15 * i), line[:44], fill=(0, 0, 0) if i else (40, 40, 140), font=f)
    return T


def sheet(tiles, out, cols=6, title=None):
    if not tiles:
        return []
    th = max(t.height for t in tiles)
    tw = max(t.width for t in tiles)
    per = cols * 5
    paths = []
    for k in range(0, len(tiles), per):
        chunk = tiles[k:k + per]
        rows = math.ceil(len(chunk) / cols)
        top = 34 if title else 0
        S = Image.new('RGB', (cols * (tw + 6) + 6, rows * (th + 6) + 6 + top), (120, 120, 120))
        if title:
            ImageDraw.Draw(S).text((8, 8), title + ('  (page %d)' % (k // per + 1)), fill=(255, 255, 255), font=font(18))
        for i, t in enumerate(chunk):
            S.paste(t, (6 + (i % cols) * (tw + 6), top + 6 + (i // cols) * (th + 6)))
        p = out % (k // per + 1)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        S.save(p, quality=88)
        paths.append(p)
    return paths
