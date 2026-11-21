#!/usr/bin/env python3
"""Cut every named thing out of every analysed shot, with where it stood and how big it was,
and bake the fourteen readings beside them, for grid.html.  Run from shots/.
Needs the butterfly-halfworld checkout beside this repo for the readings."""
import json, glob, os, numpy as np
from PIL import Image
OUT = 'gridcuts'; os.makedirs(OUT, exist_ok=True)
FLAT = {'floor', 'ground', 'sky', 'wall', 'ceiling', 'road', 'street', 'sidewalk', 'water', 'sea', 'pavement', 'path', 'horizon'}
cuts = []
for f in sorted(glob.glob('out/*/shot.json')):
    d = os.path.dirname(f); s = json.load(open(f)); a = np.load(d + '/arrays.npz')
    masks, depth, focal = a['masks'], a['depth'].astype(np.float32), float(a['focal_px'])
    H, W = depth.shape; im = np.asarray(Image.open(d + '/image.jpg').convert('RGB')); n = s['bible_no']; camh = s['camera']['height_m'] or 1.5
    keep = []
    for k, det in enumerate(s['detections']):
        lab = det['label'].lower(); m = masks[k]; area = m.mean()
        if lab in FLAT or det['score'] < .28 or not (.002 < area < .4): continue
        keep.append((det['score'], k))
    for score, k in sorted(keep, reverse=True)[:14]:
        m = masks[k]; ys, xs = np.where(m); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        z = float(np.median(depth[m])); z = min(z, 400.0)
        rgba = np.dstack([im[y0:y1, x0:x1], (m[y0:y1, x0:x1] * 255).astype(np.uint8)])
        pic = Image.fromarray(rgba, 'RGBA'); sc = 220 / max(pic.size)
        if sc < 1: pic = pic.resize((max(1, round(pic.width * sc)), max(1, round(pic.height * sc))), Image.LANCZOS)
        name = f'{n:03d}_{k:02d}.webp'; pic.save(f'{OUT}/{name}', quality=78, method=4)
        hm = (y1 - y0) / focal * z; bot = camh - (y1 - H / 2) / focal * z
        cuts.append(dict(f=name, n=n, label=s['detections'][k]['label'].lower(), x=round(((x0 + x1) / 2 - W / 2) / focal * z, 2), z=round(z, 2),
                         h=round(hm, 2), y=round(max(0, bot) if bot > .6 else 0, 2), ar=round((x1 - x0) / (y1 - y0), 3), district=s['district']))
T = json.load(open('../../butterfly-halfworld/wygwyl/world/tide/tide.json'))
have = {c['n'] for c in cuts}
poems = [dict(num=p['num'], title=p['title'], audio='/butterfly-halfworld/wygwyl/' + p['audio'], dur=p['dur'],
              scenes=[dict(name=s['name'], what=s['what'], d=T['districts'][s['d']]['name'], glow=T['districts'][s['d']]['glow'][0], views=[v for v in s['views'] if v in have]) for s in p['scenes']],
              lines=[dict(t0=l['t0'], t1=l['t1'], text=l['text'], scene=l['scene'], words=l['words']) for l in p['lines']]) for p in T['poems']]
json.dump(dict(cuts=cuts, poems=poems), open(f'{OUT}/index.json', 'w'), ensure_ascii=False, separators=(',', ':'))
import collections
print(len(cuts), 'cutouts from', len(have), 'shots;', collections.Counter(c['label'] for c in cuts).most_common(14))
for p in poems: print(p['num'], [len(s['views']) for s in p['scenes']])
