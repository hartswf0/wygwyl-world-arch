"""pair.py OUT RUN_DIR: painting | puppet on the old solve | puppet on the re-solve, one jpg per pose + contact.jpg + table.md.
RUN_DIR holds resolve.json and <id with / as __>.{before,after}.png from run.mjs (PICS=1)."""
import sys, json, os, numpy as np
from PIL import Image, ImageDraw
out, rd = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
shots = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
R = json.load(open(os.path.join(rd, 'resolve.json'))); H = 420; tiles = []
def onbg(im):
    im = im.convert('RGBA'); bg = Image.new('RGBA', im.size, (80, 80, 96, 255)); bg.alpha_composite(im); return bg.convert('RGB')
rows = ['| pose | IoU before | IoU after | marker err cm before | after | priors before | after | seed |', '|---|---|---|---|---|---|---|---|']
for tid, r in R.items():
    if r.get('error'): continue
    base = os.path.join(rd, tid.replace('/', '__'))
    if not os.path.exists(base + '.after.png'): continue
    pt = Image.open(os.path.join(shots, 'kits/cut', tid + '.webp')); pt = onbg(pt.resize((max(1, int(pt.width * H / pt.height)), H)))
    b, a = onbg(Image.open(base + '.before.png')), onbg(Image.open(base + '.after.png'))
    W = pt.width + b.width + a.width + 40; C = Image.new('RGB', (W, H + 60), (28, 28, 34)); d = ImageDraw.Draw(C); x = 10
    for im, lab in ((pt, 'painting'), (b, 'puppet, old solve'), (a, 'puppet, re-solve')): C.paste(im, (x, 0)); d.text((x + 4, 4), lab, fill='white'); x += im.width + 10
    bf, af = r['before'], r['after']
    d.text((10, H + 8), tid.split('/')[-1][:60], fill='white')
    d.text((10, H + 24), f"IoU {bf['iou']} -> {af['iou']}   marker err {bf['marker_err_cm']} -> {af['marker_err_cm']} cm   priors {bf['priors']} -> {af['priors']}   psi {bf['psi']} -> {af['psi']}", fill=(220, 210, 160))
    d.text((10, H + 40), f"seed: {af['from']}", fill=(180, 180, 180))
    C.save(os.path.join(out, tid.split('/')[-1] + '.jpg'), quality=85); tiles.append(C)
    rows.append(f"| {tid} | {bf['iou']} | {af['iou']} | {bf['marker_err_cm']} | {af['marker_err_cm']} | {bf['priors']} | {af['priors']} | {af['from']} |")
open(os.path.join(out, 'table.md'), 'w').write('\n'.join(rows) + '\n')
if tiles:
    cols = 4; tw = max(t.width for t in tiles); th = max(t.height for t in tiles); n = len(tiles)
    for page in range(0, n, 16):
        sub = tiles[page:page + 16]; rws = (len(sub) + cols - 1) // cols; S = Image.new('RGB', (cols * tw, rws * th), (20, 20, 24))
        for i, t in enumerate(sub): S.paste(t, ((i % cols) * tw, (i // cols) * th))
        S.resize((S.width // 2, S.height // 2)).save(os.path.join(out, f'contact_{page // 16 + 1}.jpg'), quality=80)
