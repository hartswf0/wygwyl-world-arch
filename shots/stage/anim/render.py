"""Render stage clips to PNG with Pillow (verification; the browser viewer is index.html).

    python3 shots/stage/anim/render.py clips/poet_tracksuit/ACT-001.json 0 40 80 --out /tmp/x
    python3 shots/stage/anim/render.py --strip clips/poet_tracksuit/ACT-001.json 30 36 42 48 --out strip.png
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

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


def render(clip_path, f, scale=0.5, crop=None, dbg=False):
    c = json.load(open(clip_path)) if isinstance(clip_path, str) else clip_path
    base = os.path.dirname(os.path.abspath(clip_path)) if isinstance(clip_path, str) else HERE
    W, H = int(1920 * scale), int(1080 * scale)
    out = Image.new('RGBA', (W, H), (24, 20, 17, 255))
    d = ImageDraw.Draw(out)
    fr = c['frames'][f]
    for op in fr['draw']:
        t = op['t']
        if t == 'floor':
            y = op['y'] * scale; d.rectangle([0, y, W, H], fill=(44, 36, 30, 255)); d.line([0, y, W, y], fill=(120, 100, 80, 255), width=2)
        elif t == 'shadow':
            x, y, rx = op['x'] * scale, op['y'] * scale, op['rx'] * scale
            d.ellipse([x - rx, y - rx * 0.18, x + rx, y + rx * 0.18], fill=(10, 8, 6, 255))
        elif t == 'img':
            im = _img(os.path.normpath(os.path.join(base, c['images'][op['id']])), op.get('shade', 0))
            a, b, cc, dd, e, ff = op['m']
            M = np.array([[a, cc, e], [b, dd, ff], [0, 0, 1.0]])
            S = np.diag([scale, scale, 1.0]); Mi = np.linalg.inv(S @ M)
            layer = im.transform((W, H), Image.AFFINE, data=tuple(Mi[:2].reshape(-1)), resample=Image.BILINEAR)
            out.alpha_composite(layer)
    if dbg and 'dbg' in fr:
        for x, y in fr['dbg'].get('pelvis', []):
            d.ellipse([x * scale - 4, y * scale - 4, x * scale + 4, y * scale + 4], outline=(255, 0, 255))
    d.text((8, 8), '%s f%d %s/%s' % (c['id'], f, fr.get('view'), fr.get('head')), fill=(230, 220, 200, 255))
    if crop:
        out = out.crop(tuple(int(v * scale) for v in crop))
    return out.convert('RGB')


if __name__ == '__main__':
    a = sys.argv[1:]
    out = a[a.index('--out') + 1]; a = a[:a.index('--out')]
    strip = '--strip' in a; a = [x for x in a if x != '--strip']
    clip, frames = a[0], [int(x) for x in a[1:]]
    if strip:
        c = json.load(open(clip))
        sc = float(os.environ.get('SCALE', '0.5'))
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
