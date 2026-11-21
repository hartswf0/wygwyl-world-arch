#!/usr/bin/env python3
"""Pack every analysed shot for wordscan.html: a small colour picture, and one PNG whose
red channel is a noun index and whose green/blue channels are 16-bit log depth.
Nouns come from the shot's own detections and stuff classes; depth and focal from DepthPro.
Run from shots/.  Reads the butterfly-halfworld scene book if it is checked out beside this repo."""
import json, glob, os, math, numpy as np
from PIL import Image
GW, GH = 176, 99
OUT = 'wordscan'; os.makedirs(OUT, exist_ok=True)
SB = '../../butterfly-halfworld/wygwyl/world/districts/scenes.json'
by_view = {}
if os.path.exists(SB):
    sb = json.load(open(SB))
    for s in sb['scenes']:
        for n in s['clip_views']:
            by_view.setdefault(n, dict(poem=s['poem'], title=s['title'], scene=s['name'], lines=s['lines'], what=s['what']))
index = []
for f in sorted(glob.glob('out/*/shot.json')):
    d = os.path.dirname(f); s = json.load(open(f)); a = np.load(d + '/arrays.npz')
    seg, depth, sky, masks = a['seg'], a['depth'].astype(np.float32), a['sky'], a['masks']
    H, W = seg.shape
    # name the stuff ids by matching their area share to the shares recorded in shot.json
    ids, cnt = np.unique(seg, return_counts=True); stuff = dict(s['stuff']); names = {}
    for i, c in sorted(zip(ids, cnt), key=lambda x: -x[1]):
        if not stuff: break
        k = min(stuff, key=lambda k: abs(stuff[k] - c / seg.size)); names[int(i)] = k; del stuff[k]
    labels = []; lab = np.zeros((H, W), np.uint8)
    def ix(name):
        name = name.split(',')[0].strip().upper() or 'THING'
        if name not in labels: labels.append(name)
        return labels.index(name)
    for i in ids: lab[seg == i] = ix(names.get(int(i), 'thing'))
    order = sorted(range(len(masks)), key=lambda k: -masks[k].sum())      # small things on top
    for k in order: lab[masks[k]] = ix(s['detections'][k]['label'])
    lab[sky] = ix('sky')
    ys = ((np.arange(GH) + .5) * H / GH).astype(int); xs = ((np.arange(GW) + .5) * W / GW).astype(int)
    L = lab[ys][:, xs]; D = depth[ys][:, xs]; S = sky[ys][:, xs]
    q = np.clip(np.log(np.maximum(D, .3) / .3) / math.log(2000), 0, 1); q[S] = 1
    q = (q * 65535).astype(np.uint16)
    px = np.dstack([L, (q >> 8).astype(np.uint8), (q & 255).astype(np.uint8), np.full(L.shape, 255, np.uint8)])
    n = s['bible_no']
    Image.fromarray(px, 'RGBA').save(f'{OUT}/{n:03d}.png', optimize=True)
    Image.open(d + '/image.jpg').convert('RGB').resize((GW * 2, GH * 2), Image.LANCZOS).save(f'{OUT}/{n:03d}.jpg', quality=72)
    used = [labels[i] for i in np.unique(L)]
    index.append(dict(n=n, id=s['id'], district=s['district'], prompt=s['prompt'], labels=labels, seen=used,
                      f=round(float(a['focal_px']) * GW / W, 2), cam=s['camera']['shot_class'], h=s['camera']['height_m'], **by_view.get(n, {})))
index.sort(key=lambda x: (x.get('poem', 'zz'), x['n']))
json.dump(dict(gw=GW, gh=GH, shots=index), open(f'{OUT}/index.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(index), 'shots;', sum('poem' in x for x in index), 'tied to a scene of a poem')
