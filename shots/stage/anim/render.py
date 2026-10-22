"""Render stage clips to PNG with Pillow (verification; the browser viewers are anim/index.html and seq/index.html).

    python3 shots/stage/anim/render.py clips/poet_tracksuit/ACT-001.json 0 40 80 --out /tmp/x
    python3 shots/stage/anim/render.py --strip clips/poet_tracksuit/ACT-001.json 30 36 42 48 --out strip.png
    python3 shots/stage/anim/render.py --sheet ../seq/clips/seq.09.phone.profile.json 0 24 48 72 --out sheet.png [--cols 4] [--scale 0.5]

Handles the FORMATS.md ops: img (m, a, shade, blend=screen/lighter approximated), poly, line, glow, shadow, text.
"""
import json, os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
_IM = {}


def _img(path, shade=0.0):
    key = (path, shade)
    if key not in _IM:
        im = Image.open(path).convert('RGBA')
        if shade:
            a = im.getchannel('A'); im = ImageEnhance.Brightness(im.convert('RGB')).enhance(1 - shade).convert('RGBA'); im.putalpha(a)
        _IM[key] = im
    return _IM[key]


def _col(c, a=1.0):
    if isinstance(c, str):
        c = c.lstrip('#'); r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    else:
        r, g, b = c[:3]
    return (int(r), int(g), int(b), int(255 * a))


def render(clip_path, f, scale=0.5, crop=None, dbg=False, bg=(24, 20, 17)):
    c = json.load(open(clip_path)) if isinstance(clip_path, str) else clip_path
    base = os.path.dirname(os.path.abspath(clip_path)) if isinstance(clip_path, str) else c.get('_base', HERE)
    sz = c.get('size', {'w': 1920, 'h': 1080})
    W, H = int(sz['w'] * scale), int(sz['h'] * scale)
    out = Image.new('RGBA', (W, H), bg + (255,))
    d = ImageDraw.Draw(out)
    fr = c['frames'][f % len(c['frames'])]
    for op in fr['draw']:
        t = op['t']
        if t == 'floor':
            y = op['y'] * scale; d.rectangle([0, y, W, H], fill=(44, 36, 30, 255)); d.line([0, y, W, y], fill=(120, 100, 80, 255), width=2)
        elif t == 'shadow':
            x, y, rx = op['x'] * scale, op['y'] * scale, op['rx'] * scale
            ry = op.get('ry', op['rx'] * 0.18) * scale
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).ellipse([x - rx, y - ry, x + rx, y + ry], fill=(6, 5, 4, int(255 * op.get('a', 0.6))))
            out.alpha_composite(lay); d = ImageDraw.Draw(out)
        elif t == 'img':
            src = c['images'][op['id']]
            im = _img(os.path.normpath(os.path.join(base, src)), op.get('shade', 0))
            a, b, cc, dd, e, ff = op['m']
            M = np.array([[a, cc, e], [b, dd, ff], [0, 0, 1.0]])
            S = np.diag([scale, scale, 1.0]); Mi = np.linalg.inv(S @ M)
            layer = im.transform((W, H), Image.AFFINE, data=tuple(Mi[:2].reshape(-1)), resample=Image.BILINEAR)
            al = op.get('a', 1.0)
            if al < 1.0:
                A = layer.getchannel('A').point(lambda v: int(v * al)); layer.putalpha(A)
            if op.get('blend') in ('screen', 'lighter', 'add'):
                rgb = ImageChops.screen(out.convert('RGB'), Image.composite(layer.convert('RGB'), Image.new('RGB', (W, H)), layer.getchannel('A')))
                out = Image.merge('RGBA', (*rgb.split(), out.getchannel('A'))); d = ImageDraw.Draw(out)
            else:
                out.alpha_composite(layer)
        elif t == 'poly':
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            pts = [(x * scale, y * scale) for x, y in op['pts']]
            dl.polygon(pts, fill=_col(op.get('fill', '#000000'), op.get('a', 1.0)) if op.get('fill') else None,
                       outline=_col(op['stroke']) if op.get('stroke') else None)
            out.alpha_composite(lay); d = ImageDraw.Draw(out)
        elif t == 'line':
            pts = op.get('pts') or [[op['x1'], op['y1']], [op['x2'], op['y2']]]
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            dl.line([(x * scale, y * scale) for x, y in pts], fill=_col(op.get('stroke', '#000000'), op.get('a', 1.0)),
                    width=max(1, int(op.get('w', 2) * scale)), joint='curve')
            out.alpha_composite(lay); d = ImageDraw.Draw(out)
        elif t == 'glow':
            x, y, r = op['x'] * scale, op['y'] * scale, op['r'] * scale
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
            col = _col(op.get('color', '#ffd38a'))
            for i in range(12, 0, -1):
                rr = r * i / 12
                dl.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col[:3] + (int(255 * op.get('a', 0.5) * (1 - i / 12) * 0.35),))
            out.alpha_composite(lay); d = ImageDraw.Draw(out)
        elif t == 'text':
            d.text((op['x'] * scale, op['y'] * scale), op['txt'], fill=_col(op.get('color', '#ffffff')))
    if dbg:
        for nm, pt, x, y in (fr.get('dbg', {}).get('contacts', [])):
            d.ellipse([x * scale - 4, y * scale - 4, x * scale + 4, y * scale + 4], outline=(95, 208, 255, 255), width=2)
        for x, y in fr.get('dbg', {}).get('pelvis', []) if isinstance(fr.get('dbg', {}).get('pelvis'), list) else []:
            d.ellipse([x * scale - 4, y * scale - 4, x * scale + 4, y * scale + 4], outline=(255, 0, 255))
    lab = '%s f%d' % (c['id'], f)
    if 'view' in fr: lab += ' %s/%s' % (fr.get('view'), fr.get('head'))
    d.text((8, 8), lab, fill=(230, 220, 200, 255))
    if crop:
        out = out.crop(tuple(int(v * scale) for v in crop))
    return out.convert('RGB')


def sheet(clip, frames, out, cols=4, scale=0.5, crop=None, dbg=False):
    ims = [render(clip, f, scale=scale, crop=crop, dbg=dbg) for f in frames]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    S = Image.new('RGB', (cols * w, rows * h), (0, 0, 0))
    for i, im in enumerate(ims):
        S.paste(im, ((i % cols) * w, (i // cols) * h))
    S.save(out, quality=88)
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    out = a[a.index('--out') + 1]; del a[a.index('--out'):a.index('--out') + 2]
    cols = 4; sc = float(os.environ.get('SCALE', '0.5')); crop = None
    if '--cols' in a: cols = int(a[a.index('--cols') + 1]); del a[a.index('--cols'):a.index('--cols') + 2]
    if '--scale' in a: sc = float(a[a.index('--scale') + 1]); del a[a.index('--scale'):a.index('--scale') + 2]
    if '--crop' in a: crop = [float(v) for v in a[a.index('--crop') + 1].split(',')]; del a[a.index('--crop'):a.index('--crop') + 2]
    dbg = '--dbg' in a; a = [x for x in a if x != '--dbg']
    if '--sheet' in a:
        a.remove('--sheet')
        sheet(a[0], [int(x) for x in a[1:]], out, cols, sc, crop, dbg)
        sys.exit()
    strip = '--strip' in a; a = [x for x in a if x != '--strip']
    clip, frames = a[0], [int(x) for x in a[1:]]
    if strip:
        c = json.load(open(clip))
        ims = []
        for f in frames:
            im = render(clip, f, scale=sc)
            px = c['frames'][f]['dbg']['pelvis'][0]
            cx, cy = px[0] * sc, px[1] * sc
            hw = 0.24 * 1080 * sc
            ims.append(im.crop((int(cx - hw), int(max(0, cy - 2.2 * hw)), int(cx + hw), int(min(im.size[1], cy + 1.9 * hw)))))
        S = Image.new('RGB', (sum(i.size[0] for i in ims), ims[0].size[1]))
        x = 0
        for im in ims: S.paste(im, (x, 0)); x += im.size[0]
        S.save(out)
    else:
        os.makedirs(out, exist_ok=True)
        for f in frames:
            render(clip, f).save(os.path.join(out, '%s_f%03d.png' % (os.path.basename(clip)[:-5], f)))
