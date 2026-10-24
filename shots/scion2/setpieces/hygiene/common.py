"""Shared helpers for the set-piece hygiene swarm: which parts are set pieces, loading, contact sheets."""
import json, os, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

cv2.setNumThreads(1)
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
CUT = os.path.join(REPO, 'shots', 'kits', 'cut')
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
os.makedirs(CACHE, exist_ok=True)
SET_RE = re.compile(r'\.(props|set|hero|fx)\.')


def setpieces():
    cat = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
    out = []
    for sid, s in cat.items():
        if not SET_RE.search(sid):
            continue
        for p in s['parts']:
            q = dict(p); q.pop('cut', None); q['sheet'] = sid; q['sheet_size'] = s.get('size'); q['sheet_title'] = s.get('title')
            out.append(q)
    return out


def load_rgba(p):
    return np.array(Image.open(os.path.join(CUT, p['file'])).convert('RGBA'))


def comp(px, bg=(235, 232, 226)):
    a = px[..., 3:4] / 255.
    return (px[..., :3] * a + np.array(bg) * (1 - a)).astype(np.uint8)


def _font(sz=11):
    for f in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf']:
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def contact(items, path, cols=6, cell=220, title=None):
    """items: [(part, [caption lines])] -> jpg with checker background so fringes/holes show."""
    rows = (len(items) + cols - 1) // cols
    head = 26 if title else 0
    capn = max([len(c) for _, c in items] + [1])
    ch = cell + 13 * capn + 6
    W, H = cols * cell, rows * ch + head
    sheet = Image.new('RGB', (W, H), (40, 40, 40))
    d = ImageDraw.Draw(sheet); f = _font(11)
    if title:
        d.text((6, 6), title, fill=(255, 255, 255), font=_font(14))
    for i, (p, cap) in enumerate(items):
        x0, y0 = (i % cols) * cell, (i // cols) * ch + head
        px = load_rgba(p)
        h, w = px.shape[:2]
        k = (cell - 10) / max(h, w)
        im = Image.fromarray(px).resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
        # dark/teal checker shows pale fringe and holes
        bg = Image.new('RGB', (cell - 4, cell - 4), (30, 70, 80))
        bd = ImageDraw.Draw(bg)
        for yy in range(0, cell, 16):
            for xx in range(0, cell, 16):
                if (xx // 16 + yy // 16) % 2:
                    bd.rectangle([xx, yy, xx + 15, yy + 15], fill=(20, 50, 60))
        bg.paste(im, ((cell - 4 - im.width) // 2, (cell - 4 - im.height) // 2), im)
        sheet.paste(bg, (x0 + 2, y0 + 2))
        for j, line in enumerate(cap):
            d.text((x0 + 3, y0 + cell + 1 + 13 * j), line[:36], fill=(240, 240, 200) if j == 0 else (200, 220, 255), font=f)
    sheet.save(path, quality=85)
    return path
