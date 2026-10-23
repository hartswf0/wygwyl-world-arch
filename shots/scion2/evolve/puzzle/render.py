"""Frames for the puzzle: REFERENCE | PUZZLE RENDER | PIECE MAP | COVERAGE, ~1600 px wide."""
import colorsys, glob, os, textwrap
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

from . import fill as FL

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.join(HERE, 'live')
LATEST = os.path.abspath(os.path.join(HERE, '..', 'live', 'latest.jpg'))
FRAME_W, PANEL_H = 1600, 330
BG = (238, 236, 232)


def font(sz, bold=False):
    p = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else '')
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()


F, FB, FS = font(13), font(15, True), font(10)


def piece_render(P, masks, pieces, t):
    W, H = t['size']
    acc = np.zeros((H, W, 4), np.float32)
    for p in P:
        pc = pieces[p['pi']]
        lay = cv2.warpAffine(pc['px'], FL.full_M(p, pc, t), (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        a = lay[..., 3:] / 255.
        acc[..., :3] = lay[..., :3] * a + acc[..., :3] * (1 - a)
        acc[..., 3:] = 255 * a + acc[..., 3:] * (1 - a)
    return acc


def colours(n):
    return [tuple(int(255 * c) for c in colorsys.hsv_to_rgb((i * .61803) % 1, .75, .85)) for i in range(n)]


def to_pil_bgra(a, bg=BG):
    rgb = a[..., [2, 1, 0]]
    al = a[..., 3:] / 255.
    o = rgb * al + np.array(bg, np.float32) * (1 - al)
    return Image.fromarray(np.clip(o, 0, 255).astype(np.uint8))


def panels(P, masks, pieces, t):
    W, H = t['size']
    if masks is None:
        masks = [FL.full_mask(p, pieces[p['pi']], t) for p in P]
    ref = to_pil_bgra(t['ref'].astype(np.float32))
    ren = to_pil_bgra(piece_render(P, masks, pieces, t))
    # piece map
    pm = np.full((H, W, 3), 255, np.uint8)
    pm[t['fig_t']] = (225, 225, 225)
    cols = colours(len(P))
    cents = []
    for i, m in enumerate(masks):
        cnts, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(pm, cnts, -1, cols[i], 1)
        ys, xs = np.nonzero(m)
        cents.append((xs.mean(), ys.mean()) if len(xs) else (0, 0))
    # coverage
    U = np.zeros((H, W), bool)
    for m in masks:
        U |= m
    fig, fd, ign = t['fig_t'], t['fig_dil'], t['ignore']
    cv_ = np.full((H, W, 3), 255, np.uint8)
    cv_[fig & U] = (170, 170, 170)
    cv_[fig & ~U] = (30, 110, 220)
    cv_[U & ~fd & ~ign] = (220, 30, 30)
    cv_[U & ~fig & fd] = (230, 170, 170)
    cv_[ign] = (255, 225, 120)
    st = FL.stats(masks, t)
    return ref, ren, Image.fromarray(pm), cents, Image.fromarray(cv_), st


def frame(tid, step, tag, P, masks, pieces, t, mode):
    ref, ren, pm, cents, cv_, st = panels(P, masks, pieces, t)
    W, H = t['size']
    pw = (FRAME_W - 50) // 4
    k = min(PANEL_H / H, pw / W)
    sz = (max(1, int(W * k)), max(1, int(H * k)))
    head = 44
    ids = ', '.join('%d %s' % (i + 1, pieces[p['pi']]['id'].replace('poet.red_black_sunglasses.', 'rb.').replace('harvest.poet.', 'H.')
                                     .replace('ex.ex_jacket.', 'ex.')) for i, p in enumerate(P))
    lines = textwrap.wrap('pieces: ' + ids, 260)[:4]
    out = Image.new('RGB', (FRAME_W, head + PANEL_H + 26 + 13 * len(lines) + 6), (255, 255, 255))
    d = ImageDraw.Draw(out)
    d.text((10, 6), '%s  [%s]  step %d: %s' % (tid, mode, step, tag[:70]), fill=(28, 32, 38), font=FB)
    d.text((10, 25), 'coverage %.1f%%   overflow %.2f%% (%d px beyond the 2 px band)   pieces %d' %
           (100 * st['coverage'], 100 * st['overflow'], st['overflow_px'], len(P)), fill=(180, 30, 30) if st['overflow_px'] else (28, 32, 38), font=FB)
    for i, (im, lab) in enumerate(((ref, 'REFERENCE (target shape only)'), (ren, 'PUZZLE RENDER (painted pieces)'),
                                   (pm, 'PIECE MAP'), (cv_, 'COVERAGE: grey filled, blue empty, red overflow'))):
        im = im.resize(sz, Image.LANCZOS if i < 2 else Image.NEAREST)
        x = 10 + i * (pw + 10)
        out.paste(im, (x, head))
        if i == 2:
            for j, (cx, cy) in enumerate(cents):
                d.text((x + cx * k - 4, head + cy * k - 6), str(j + 1), fill=(0, 0, 0), font=FS)
        d.text((x, head + PANEL_H + 4), lab, fill=(95, 101, 112), font=F)
    y = head + PANEL_H + 22
    for l in lines:
        d.text((10, y), l, fill=(60, 60, 60), font=FS)
        y += 13
    return out, st


def safe(tid):
    return tid.replace('/', '__')


def save(im, path, q=80):
    tmp = path + '.tmp.jpg'
    im.save(tmp, quality=q)
    os.replace(tmp, path)


def montage(rows_first, maxrows=6):
    """latest.jpg: the kill targets' current rows first, then the most recently updated others"""
    rows = sorted(glob.glob(os.path.join(LIVE, '_row_*.jpg')), key=os.path.getmtime, reverse=True)
    first = [r for r in rows if any(safe(t) in r for t in rows_first)]
    rest = [r for r in rows if r not in first]
    pick = sorted(first, key=lambda r: [i for i, t in enumerate(rows_first) if safe(t) in r][0]) + rest[:max(0, maxrows - len(first))]
    ims = []
    for r in pick[:maxrows]:
        try:
            ims.append(Image.open(r).convert('RGB'))
        except Exception:
            pass
    if not ims:
        return
    H = sum(i.height for i in ims)
    out = Image.new('RGB', (FRAME_W, H), (255, 255, 255))
    y = 0
    for i in ims:
        out.paste(i, (0, y)); y += i.height
    os.makedirs(os.path.dirname(LATEST), exist_ok=True)
    save(out, LATEST, 78)
