"""pair.py OUT_DIR RENDER_DIR — side-by-sides painting | puppet (PuppetCore.renderPose), one per pose, plus a contact sheet.
RENDER_DIR holds <name>.png (renders on #505060) and results.json from core_check.html; paintings come from shots/kits/cut."""
import sys, json, os, numpy as np
from PIL import Image, ImageDraw
out, rd = sys.argv[1], sys.argv[2]
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))   # shots/
res = json.load(open(os.path.join(rd, 'results.json'))); H = 520; tiles = []
def crop_fig(im, painted):
    a = np.asarray(im.convert('RGBA'))
    m = a[..., 3] > 40 if painted else (np.abs(a[..., :3].astype(int) - [0x50, 0x50, 0x60]).sum(2) > 12)
    ys, xs = np.nonzero(m)
    if not len(xs): return im
    im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)).convert('RGBA')
    s = H / im.height; im = im.resize((max(1, int(im.width * s)), H)); bg = Image.new('RGBA', im.size, (80, 80, 96, 255)); bg.alpha_composite(im); return bg.convert('RGB')
for tid, r in res.items():
    name = tid.split('/')[-1]
    a = crop_fig(Image.open(os.path.join(root, 'kits/cut', tid + '.webp')), True)
    b = crop_fig(Image.open(os.path.join(rd, name + '.png')), False)
    W = a.width + b.width + 30; C = Image.new('RGB', (max(W, 420), H + 92), (28, 28, 34)); d = ImageDraw.Draw(C)
    C.paste(a, (10, 10)); C.paste(b, (a.width + 20, 10))
    for k in range(1, 8): d.line([(10, 10 + H * k // 8), (a.width + b.width + 20, 10 + H * k // 8)], fill=(120, 120, 60), width=1)
    sv = r.get('solve', {}); w = r.get('warnings', [])
    d.text((10, H + 16), f"{name[:48]}", fill='white')
    d.text((10, H + 32), f"painting | puppet   solve: {sv.get('view')} (psi {sv.get('psi')}, score {sv.get('score')})   cards: {r.get('view')}", fill=(200, 200, 200))
    d.text((10, H + 48), f"{len(w)} warnings: " + ('; '.join(x.split(' - ')[0] for x in w))[:150], fill=(230, 190, 90))
    d.text((10, H + 64), ('; '.join(x.split(' - ')[0] for x in w))[150:300], fill=(230, 190, 90))
    C.save(os.path.join(out, name + '.jpg'), quality=88); tiles.append(C)
cols = 4; rows = (len(tiles) + cols - 1) // cols; tw = max(t.width for t in tiles); th = max(t.height for t in tiles)
S = Image.new('RGB', (cols * tw, rows * th), (20, 20, 24))
for i, t in enumerate(tiles): S.paste(t, ((i % cols) * tw, (i // cols) * th))
S = S.resize((S.width // 2, S.height // 2)); S.save(os.path.join(out, 'contact.jpg'), quality=85)
