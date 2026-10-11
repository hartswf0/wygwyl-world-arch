#!/usr/bin/env python3
"""
actors.py — turn a shot's angular cartoon into a cast.

The scene program (scene_program.py) leaves each shot as ~50-150 flat polygons sorted into
planes P1..P6. Nothing in that drawing knows that a polygon is a child, a lamp or the sea.
The analysis pass (analyze.py) already knows that — Grounding-DINO boxes + SAM masks — but
in pixels. This script binds the two:

    polygon  ──(how much of it lies inside each SAM mask)──▶  actor  ──(label)──▶  verb

and writes  shots/out/<sid>/program/actors.json , which animate.html plays.

Every actor gets:
  label    what the detector called it ("person", "street lamp", "satellite dish" ...)
  kind     one of person | vehicle | light | water | sky | sway | signal
  verb     the default action for that kind (run, walk, drive, flicker, ripple, drift, sway, pulse)
  box      bbox in drawing pixels, pivot (feet / base), plane, depth (m)
  shapes   the polygon ids that move with it
  behind   a flat colour sampled from the planes behind it, painted under it so it can move
           without opening a hole in the drawing (a poor man's clean plate)

Usage:
  python3 shots/actors.py <sid-or-prefix> [...]     # one or more shots
  python3 shots/actors.py --all                     # every shot with program/scene.json
"""
import glob, json, os, re, sys, zlib
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')

# label keyword → kind. Order matters: first match wins, specific before broad.
KINDS = [
    ('person',  r'\b(person|people|child|children|kid|man|woman|men|women|boy|girl|figure|crowd|'
                r'local|locals|pedestrian|silhouette|poet|vendor|dancer|runner|walker|elder|worker)'),
    ('vehicle', r'\b(vehicle|car|cars|bus|truck|van|taxi|train|tram|boat|ship|ferry|barge|bike|bicycle|'
                r'motorcycle|scooter|drone|airship|aircraft|plane|zeppelin|cart)'),
    ('light',   r'\b(lamp|light|lights|neon|sign|lantern|screen|billboard|led|beacon|glow|candle|fire|torch)'),
    ('water',   r'\b(water|sea|ocean|canal|lake|river|pool|pools|puddle|wave|waves|bay|harbou?r|fountain|waterfall)'),
    ('sky',     r'\b(sky|cloud|clouds|fog|mist|haze|smoke|steam|smog|vapou?r)'),
    ('sway',    r'\b(tree|trees|palm|plant|plants|flower|flowers|grass|fabric|laundry|banner|flag|curtain|vine|'
                r'leaves|bush|reed|cloth|hanging)'),
    ('signal',  r'\b(dish|antenna|mast|spire|spires|tower|pylon|lattice)'),
]
# what each kind does by default, and the menu offered for it in animate.html
VERBS = {
    'person':  ['run', 'walk', 'idle', 'still'],
    'vehicle': ['drive', 'hover', 'still'],
    'light':   ['flicker', 'pulse', 'still'],
    'water':   ['ripple', 'still'],
    'sky':     ['drift', 'still'],
    'sway':    ['sway', 'still'],
    'signal':  ['pulse', 'still'],
}
# fraction of a polygon that must fall inside a mask to belong to it
CLAIM = {'person': .45, 'vehicle': .45, 'light': .45, 'sway': .5, 'signal': .55, 'water': .6, 'sky': .6}
PRIORITY = {'person': 7, 'vehicle': 6, 'light': 5, 'sway': 4, 'signal': 3, 'water': 2, 'sky': 1}


def kind_of(label):
    l = label.lower()
    for k, rx in KINDS:
        if re.search(rx, l):
            return k
    return None


def parse_d(d):
    """'M x y L x y ... Z M ...' → list of int32 Nx2 arrays (one per subpath)."""
    polys, cur = [], []
    for tok in re.finditer(r'([MLZ])\s*(-?[\d.]+)?\s*(-?[\d.]+)?', d):
        c, x, y = tok.groups()
        if c == 'M':
            if len(cur) > 2: polys.append(cur)
            cur = [(float(x), float(y))]
        elif c == 'L':
            cur.append((float(x), float(y)))
        elif c == 'Z':
            if len(cur) > 2: polys.append(cur)
            cur = []
    if len(cur) > 2: polys.append(cur)
    return [np.round(np.array(p)).astype(np.int32) for p in polys]


def raster(polys, H, W):
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, polys, 1)
    return m.astype(bool)


def gradients(html):
    g = {}
    for m in re.finditer(r'<linearGradient id="g(\d+)"[^>]*x1="([-\d.]+)" y1="([-\d.]+)" x2="([-\d.]+)" y2="([-\d.]+)">'
                         r'<stop offset="0" stop-color="(#[0-9a-f]{6})"/><stop offset="1" stop-color="(#[0-9a-f]{6})"/>', html):
        i, x1, y1, x2, y2, c0, c1 = m.groups()
        g[int(i)] = [float(x1), float(y1), float(x2), float(y2), c0, c1]
    return g


def mix(c0, c1):
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple((x + y) // 2 for x, y in zip(a, b))


def build(sid):
    od = os.path.join(OUT, sid)
    scene = json.load(open(os.path.join(od, 'program', 'scene.json')))
    html = open(os.path.join(od, 'program', 'cartoon.html')).read()
    shot = json.load(open(os.path.join(od, 'shot.json')))
    arr = np.load(os.path.join(od, 'arrays.npz'), allow_pickle=True)
    W, H = scene['W'], scene['H']
    masks, depth = arr['masks'], arr['depth'].astype(np.float32)
    dets = shot['detections'][:len(masks)]
    grads = gradients(html)

    # stroke per shape (the scene program inks some shapes)
    strokes = {}
    for m in re.finditer(r'<path d="[^"]*" fill="url\(#g(\d+)\)" stroke="(#[0-9a-f]{6})" stroke-width="([\d.]+)"', html):
        strokes[int(m.group(1))] = [m.group(2), float(m.group(3))]

    # shapes, far → near (P6 first) so the painter's order is preserved
    order = ['P6', 'P5', 'P4', 'P3', 'P2', 'P1', 'P0']
    shapes, rast = [], {}
    for p in order:
        for s in scene['planes'].get(p, []):
            polys = parse_d(s['d'])
            if not polys: continue
            r = raster(polys, H, W)
            if not r.any(): continue
            sid_ = int(s['id'])
            rast[sid_] = r
            f = s.get('fill'); f = f if isinstance(f, dict) else {'c0': f or '#333333', 'c1': f or '#333333'}
            g = grads.get(sid_) or [0, 0, 0, H, f['c0'], f['c1']]
            shapes.append(dict(id=sid_, plane=p, d=s['d'], g=g, stroke=strokes.get(sid_, ['#000', 0]),
                               area=int(r.sum()), actor=None))

    # candidate actors from detections
    cands = []
    for i, det in enumerate(dets):
        k = kind_of(det['label'])
        if not k: continue
        m = masks[i]
        if m.sum() < 60: continue
        cands.append(dict(i=i, label=det['label'], kind=k, score=det['score'], mask=m, marea=int(m.sum())))

    # claim: each shape goes to the best candidate that covers enough of it
    for s in shapes:
        r = rast[s['id']]
        best, bv = None, 0
        for c in cands:
            inside = (r & c['mask']).sum() / s['area']
            if inside < CLAIM[c['kind']]: continue
            # a small actor cannot own a huge polygon (that polygon is scenery that happens to touch it)
            if c['kind'] in ('person', 'vehicle', 'light') and s['area'] > 3.0 * c['marea']: continue
            v = PRIORITY[c['kind']] * 10 + inside + c['score']
            if v > bv: best, bv = c, v
        if best is not None:
            s['actor'] = best['i']

    # colour behind every shape: the most-covering shape on a farther plane at its pixels
    plane_rank = {p: n for n, p in enumerate(order)}
    def behind_color(s):
        r = rast[s['id']]
        best, bv = None, 0
        for t in shapes:
            if plane_rank[t['plane']] >= plane_rank[s['plane']] or t['id'] == s['id']: continue
            v = (rast[t['id']] & r).sum()
            if v > bv: best, bv = t, v
        return mix(best['g'][4], best['g'][5]) if best else '#10141c'

    actors = []
    for c in cands:
        own = [s for s in shapes if s['actor'] == c['i']]
        if not own: continue
        u = np.zeros((H, W), bool)
        for s in own: u |= rast[s['id']]
        ys, xs = np.nonzero(u)
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
        z = float(np.median(depth[u])) if u.any() else None
        near_plane = max((s['plane'] for s in own), key=lambda p: plane_rank[p])
        actors.append(dict(
            id='a%d' % c['i'], label=c['label'], kind=c['kind'], verb=VERBS[c['kind']][0], verbs=VERBS[c['kind']],
            score=round(c['score'], 3), box=[x0, y0, x1, y1], pivot=[(x0 + x1) // 2, y1],
            plane=near_plane, depth_m=round(z, 2) if z else None,
            shapes=[s['id'] for s in own], behind={str(s['id']): behind_color(s) for s in own},
            area=int(u.sum())))

    # a deterministic phase per actor so a crowd does not move in lockstep
    for n, a in enumerate(actors):
        a['phase'] = round((zlib.crc32((a['id'] + sid).encode()) % 1000) / 1000.0, 3)
        # people facing: lean of the silhouette's centre of mass vs its base → travel direction
        if a['kind'] in ('person', 'vehicle'):
            cx = (a['box'][0] + a['box'][2]) / 2
            a['dir'] = 1 if cx < W / 2 else -1

    for s in shapes:
        s['actor'] = ('a%d' % s['actor']) if s['actor'] is not None else None
        s.pop('area', None)

    out = dict(id=sid, W=W, H=H, camera=scene.get('camera', {}), parallax=scene.get('parallax', {}),
               district=shot.get('district'), prompt=shot.get('prompt', '')[:240],
               shapes=shapes, actors=actors)
    fn = os.path.join(od, 'program', 'actors.json')
    json.dump(out, open(fn, 'w'), separators=(',', ':'))
    tally = {}
    for a in actors: tally[a['kind']] = tally.get(a['kind'], 0) + 1
    bound = sum(1 for s in shapes if s['actor'])
    print('%-12s %3d shapes  %3d bound  actors %s' % (sid[:12], len(shapes), bound, tally))
    return out


def resolve(arg):
    hits = sorted(glob.glob(os.path.join(OUT, arg + '*', 'program', 'scene.json')))
    return [h.split(os.sep)[-3] for h in hits]


if __name__ == '__main__':
    args = sys.argv[1:]
    sids = resolve('') if (not args or args == ['--all']) else [s for a in args for s in resolve(a)]
    idx = []
    for sid in sids:
        try:
            o = build(sid)
            idx.append(dict(id=sid, district=o['district'], actors=len(o['actors']),
                            kinds=sorted({a['kind'] for a in o['actors']})))
        except Exception as e:
            print('skip', sid[:12], type(e).__name__, e)
    if len(sids) > 1:
        json.dump(idx, open(os.path.join(OUT, 'actors_index.json'), 'w'), indent=0)
        print('wrote out/actors_index.json', len(idx))
