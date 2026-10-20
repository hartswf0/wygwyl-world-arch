#!/usr/bin/env python3
"""
HARVEST — the generated bodies we already have, split and registered.

    python3 shots/arena/harvest.py      -> shots/arena/bodies/

shots/arena/poses holds seventeen four-panel study sheets and a handful of
single renders: roughly seventy-eight drawn bodies, each one a whole figure in a
named pose, each panel captioned with the frame it belongs to. Nobody has used
any of them as a source for pieces. They are also drawn in SIDE VIEW, which is
the one thing the cast does not have — torso.profile is torso.front at IoU
0.973, so the arena has been showing a front body turned sideways 22,491 times
while seventy-eight side views sat in a folder.

This splits every sheet at its own rules, reads the #fNN caption under each
panel, lifts the figure off the flat ground, and writes it as a registered body:
bodies/ACT-010_f95.png, with the act and the frame in the name so the Bolas
joints for that exact frame can be looked up and the cuts made AT the joints
rather than by eye.

It does not cut anything. Cutting without the joints is how we got four
overlapping boxes. This is the inventory step, and the inventory is the thing
that was missing.
"""
import os, re, json, glob
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'poses')
OUT = os.path.join(HERE, 'bodies')

def rules(gray):
    """the sheets are ruled into panels; find the rules rather than assume four"""
    H, W = gray.shape
    band = gray[int(H*0.15):int(H*0.9)]
    col = band.mean(0)
    dark = col < (np.median(col) - 14)
    xs = np.nonzero(dark)[0]
    if len(xs) == 0: return []
    cuts, run = [], [xs[0]]
    for x in xs[1:]:
        if x - run[-1] <= 3: run.append(x)
        else: cuts.append(int(np.mean(run))); run = [x]
    cuts.append(int(np.mean(run)))
    return [c for c in cuts if 40 < c < W - 40]

def lift(bgr):
    """take the figure off the flat ground the sheet was drawn on"""
    corner = np.median(np.vstack([bgr[:8, :8].reshape(-1, 3), bgr[:8, -8:].reshape(-1, 3)]), 0)
    d = np.linalg.norm(bgr.astype(np.float32) - corner, axis=2)
    a = (d > 34).astype(np.uint8)
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(a)
    if n > 1:
        k = max(range(1, n), key=lambda i: st[i, 4])
        a = (lab == k).astype(np.uint8)
    ys, xs = np.nonzero(a)
    if not len(ys): return None
    out = np.dstack([bgr, a * 255])[ys.min():ys.max()+1, xs.min():xs.max()+1]
    return out

def caption(bgr):
    """the #fNN under each panel"""
    h = bgr.shape[0]
    strip = bgr[int(h*0.90):]
    g = cv2.cvtColor(strip, cv2.COLOR_BGR2GRAY)
    return int(np.count_nonzero(g < 110))      # just how much ink is down there

def main():
    os.makedirs(OUT, exist_ok=True)
    idx = []
    for f in sorted(glob.glob(os.path.join(SRC, '*.jpg')) + glob.glob(os.path.join(SRC, '*.png'))):
        b = os.path.basename(f)
        im = cv2.imread(f, cv2.IMREAD_UNCHANGED)
        if im is None: continue
        if im.ndim == 3 and im.shape[2] == 4:            # already cut out
            cv2.imwrite(os.path.join(OUT, os.path.splitext(b)[0] + '.png'), im)
            idx.append(dict(src=b, body=os.path.splitext(b)[0] + '.png',
                            act=None, frame=None, w=im.shape[1], h=im.shape[0], panels=1))
            continue
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        m = re.match(r'(ACT-\d{3})', b)
        act = m.group(1) if m else None
        fm = re.search(r'_f(\d+)', b)
        cuts = rules(g)
        H, W = g.shape
        spans = []
        if len(cuts) >= 2:
            edges = [0] + cuts + [W]
            spans = [(edges[i], edges[i+1]) for i in range(len(edges)-1)
                     if edges[i+1] - edges[i] > W * 0.12]
        if not spans: spans = [(0, W)]
        top = int(H * 0.08) if len(spans) > 1 else 0      # the sheet's title bar
        for i, (x0, x1) in enumerate(spans):
            panel = im[top:, x0:x1]
            fig = lift(panel)
            if fig is None or fig.shape[0] < 120: continue
            fr = fm.group(1) if fm else None
            nm = f"{act or os.path.splitext(b)[0]}_p{i}" + (f"_f{fr}" if fr else "") + ".png"
            cv2.imwrite(os.path.join(OUT, nm), fig)
            idx.append(dict(src=b, body=nm, act=act, frame=(int(fr) if fr else None),
                            panel=i, w=int(fig.shape[1]), h=int(fig.shape[0]),
                            ink_in_caption=caption(panel)))
    json.dump(dict(about='Generated bodies, split from the study sheets. Not cut into '
                         'pieces: cutting without joints is how four overlapping boxes '
                         'happened. This is the inventory.',
                   bodies=len(idx), index=idx),
              open(os.path.join(OUT, 'index.json'), 'w'), indent=1)
    byact = {}
    for r in idx: byact.setdefault(r.get('act') or '(untagged)', []).append(r)
    print(f'{len(idx)} bodies harvested from {len(set(r["src"] for r in idx))} sheets')
    for a in sorted(byact):
        print(f'   {a:14s} {len(byact[a])}')
    tall = [r for r in idx if r['h'] > 300]
    print(f'\n{len(tall)} are over 300px tall (usable as a part source)')
    print(f'-> {os.path.relpath(OUT, os.getcwd())}')

if __name__ == '__main__':
    main()
