#!/usr/bin/env python3
"""SETS, STEP 2: screen every candidate frame for figures, choose each scene's plate, and measure the chosen plates.

  screen   Grounding DINO 'person' on every candidate frame (the people a generated plate already has fight the puppet).
  choose   per scene: score = CLIP(set text) - figure penalty (+ small bonus for the dossier's own pick / an analysed view).
  measure  for each chosen plate: OneFormer ADE20K (stuff), Depth Pro (metric depth + focal), Grounding DINO + SAM 2.1
           masks for people, doors, windows, screens, cars, steps (known sizes) -> ground plane (RANSAC), horizon, camera
           height. Atlantis views that shots/analyze.py already measured (shots/out/<id>/) are reused, not re-run.
The models are the ones shots/analyze.py uses (imported from it).
  .venv-shots/bin/python sets_analyze.py <work_dir> [screen|choose|measure|all]"""
import os, sys, json, math, time
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1'); os.environ.setdefault('HF_HUB_OFFLINE', '1')
import numpy as np, cv2, torch
from PIL import Image
SUITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SH = os.path.dirname(SUITE)
sys.path.insert(0, SH)
import analyze as AN

WORK = sys.argv[1]; STEP = sys.argv[2] if len(sys.argv) > 2 else 'all'
C = json.load(open(os.path.join(WORK, 'candidates.json')))
SCREEN = os.path.join(WORK, 'screen.json'); CHOICE = os.path.join(WORK, 'choice.json'); MDIR = os.path.join(WORK, 'measure')
os.makedirs(MDIR, exist_ok=True)
_M = None
def models():
    global _M
    if _M is None: _M = AN.Models()
    return _M

KNOWN = ['person', 'door', 'window', 'car', 'stairs', 'chair', 'bench', 'television screen', 'screen', 'mirror', 'street lamp']
KNOWN_H = {'person': 1.70, 'door': 2.05, 'car': 1.45, 'chair': 0.85, 'bench': 0.45, 'street lamp': 4.5}

def screen():
    S = json.load(open(SCREEN)) if os.path.exists(SCREEN) else {}
    frames = sorted({f for s in C['scenes'] for c in s['candidates'] for f in c['frames']})
    todo = [f for f in frames if f not in S]; print(len(frames), 'frames,', len(todo), 'to screen')
    M = models()
    for i, f in enumerate(todo):
        img = Image.open(f).convert('RGB'); W, H = img.size
        dets = [d for d in M.detect(img, ['person', 'human figure'], box_thr=0.30) if d['score'] >= 0.30]
        area = 0.0; tall = 0.0
        for d in dets:
            x0, y0, x1, y1 = d['box']; area += (x1 - x0) * (y1 - y0) / (W * H); tall = max(tall, (y1 - y0) / H)
        S[f] = dict(n=len(dets), area=round(min(area, 1.0), 4), tallest=round(tall, 3), boxes=[d['box'] for d in dets][:12])
        if i % 20 == 0:
            print(i, os.path.basename(f), S[f]['n'], S[f]['area'], flush=True); json.dump(S, open(SCREEN, 'w'))
    json.dump(S, open(SCREEN, 'w'))

def choose():
    S = json.load(open(SCREEN)); out = {}
    for s in C['scenes']:
        best = None
        for c in s['candidates']:
            for f, cl in zip(c['frames'], c['clip_frames']):
                sc = S[f]
                pen = 0.9 * sc['area'] + (0.02 if sc['n'] else 0) + 0.25 * max(0, sc['tallest'] - 0.15)
                bonus = (0.012 if 'dossier_plate' in c['origin'] else 0) + (0.006 if c['kind'] == 'world' else 0)
                score = cl - pen + bonus
                row = dict(cand=c['id'], kind=c['kind'], frame=f, clip=cl, people=sc, score=round(score, 4), origin=c['origin'],
                           out_id=c.get('out_id'), provenance=c['provenance'])
                if best is None or score > best['score']: best = row
        alts = []
        for c in s['candidates']:
            k = int(np.argmin([S[f]['area'] for f in c['frames']])); f = c['frames'][k]
            alts.append(dict(cand=c['id'], frame=f, clip=c['clip_frames'][k], people=S[f]['n'], people_area=S[f]['area'], origin=c['origin']))
        out[s['scene_id']] = dict(best=best, alternatives=alts)
    json.dump(out, open(CHOICE, 'w'), indent=1)
    for k, v in out.items():
        b = v['best']; print(k, b and (b['cand'], round(b['clip'], 3), b['people']['n'], b['people']['area'], b['score']))

def measure_one(key, frame, out_id):
    od = os.path.join(MDIR, key)
    if os.path.exists(os.path.join(od, 'm.json')): return
    os.makedirs(od, exist_ok=True)
    img = Image.open(frame).convert('RGB'); W, H = img.size; rgb = np.array(img)
    M = models()
    vocab = KNOWN
    if out_id:  # reuse the analysed Atlantis view
        A = np.load(os.path.join(SH, 'out', out_id, 'arrays.npz')); shot = json.load(open(os.path.join(SH, 'out', out_id, 'shot.json')))
        seg = A['seg']; depth = A['depth'].astype(np.float32) / max(1e-6, shot['camera'].get('scale_factor', 1.0))  # raw (unscaled) depth
        focal = float(A['focal_px']); sky = A['sky']; ground = A['ground']; id2label = {i: str(l) for i, l in enumerate(A['id2label'])}
        reused = True
    else:
        seg, id2label = M.stuff(img); depth, focal, _ = M.depth(img)
        sky = np.isin(seg, [k for k, v in id2label.items() if 'sky' in v.split(', ')])
        ground = np.isin(seg, [k for k, v in id2label.items() if AN.ADE_GROUND & set(v.split(', '))]) & ~sky
        reused = False
    dets = M.detect(img, vocab, box_thr=0.30)
    masks = M.segment(img, dets) if dets else np.zeros((0, H, W), bool)
    for d, m in zip(dets, masks): d['area_frac'] = round(float(m.mean()), 4)
    plane = AN.fit_ground(depth, focal, ground) if ground.mean() > 0.01 else None
    refs = []
    for i, (d, m) in enumerate(zip(dets, masks)):
        if d['label'] in KNOWN_H and d['score'] >= 0.35 and m.sum() > 60:
            h = AN.object_metric_height(m, depth, focal)
            ys, xs = np.where(m)
            if h and h > 0: refs.append(dict(i=i, label=d['label'], score=d['score'], h_m_raw=round(float(h), 3), known_m=KNOWN_H[d['label']],
                                             foot=[float(np.median(xs)), float(ys.max())], top=float(ys.min()),
                                             touches_edge=bool(ys.max() >= H - 2 or ys.min() <= 1)))
    np.savez_compressed(os.path.join(od, 'a.npz'), seg=seg.astype(np.uint8), depth=depth.astype(np.float16), sky=sky, ground=ground,
                        masks=np.asarray(masks, bool), focal=np.float32(focal),
                        id2label=np.array([id2label[i] for i in range(len(id2label))]))
    rec = dict(key=key, frame=frame, size=[W, H], focal_px=float(focal), reused_out=out_id if reused else None,
               plane=dict(n=[float(x) for x in plane['n']], d=plane['d'], inlier_frac=plane['inlier_frac']) if plane else None,
               dets=dets, refs=refs, ground_frac=float(ground.mean()), sky_frac=float(sky.mean()),
               stuff={id2label[int(k)]: round(float((seg == k).mean()), 4) for k in np.unique(seg)})
    json.dump(rec, open(os.path.join(od, 'm.json'), 'w'), indent=1, default=float)

def measure():
    CH = json.load(open(CHOICE)); seen = set()
    for sid, v in CH.items():
        b = v['best']
        if not b: continue
        key = os.path.splitext(os.path.basename(b['frame']))[0] if b['kind'] != 'world' else b['cand']
        b['key'] = key
        if key in seen: continue
        seen.add(key); t = time.time()
        measure_one(key, b['frame'], b.get('out_id'))
        print(sid, key, round(time.time() - t, 1), 's', flush=True)
    json.dump(CH, open(CHOICE, 'w'), indent=1)

def measure_overrides():
    O = json.load(open(os.path.join(SUITE, 'tools', 'sets_overrides.json'))); CH = json.load(open(CHOICE))
    for sid, o in O.items():
        if sid.startswith('_') or not o.get('cand'): continue
        a = next(a for a in CH[sid]['alternatives'] if a['cand'] == o['cand'])
        c = next(c for s in C['scenes'] if s['scene_id'] == sid for c in s['candidates'] if c['id'] == o['cand'])
        key = o['cand'] if c['kind'] == 'world' else os.path.splitext(os.path.basename(a['frame']))[0]
        measure_one(key, a['frame'], c.get('out_id')); print('override', sid, key, flush=True)

if STEP in ('screen', 'all'): screen()
if STEP in ('choose', 'all'): choose()
if STEP in ('measure', 'all'): measure()
if STEP in ('overrides', 'all'): measure_overrides()
