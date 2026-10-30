#!/usr/bin/env python3
"""Stage 2 (poems 08-14): write the staged scene JSONs from the authored blocking in tools/stage2_specs.py.

  /Users/gaia/anaconda3/bin/python3 shots/suite/tools/stage2_stage.py [scene_id ...]      (default: every scene in the specs)

For each scene it
  * takes the scene's window on the reading (tools/stage2_windows.py -> data/scenes/stage2_windows.json), cuts the reading
    (data/audio/<id>.m4a) and the word times (data/scenes/<id>.words.json) with tools/prep.py's cutter;
  * resolves every beat's word ('word' or 'word#2' = the 2nd time it is read) to its time, so beats are snapped to words;
  * picks each join's archive clip with lib/archive_grab.py (CLIP text search over the 15,149 clip thumbnails, kept to
    clips cached on this machine, never one already used in the same poem) and cuts its frame strip (prep.archive);
  * places each puppet by its foot point on the set's ground (the set's horizon and px/cm do the scaling);
  * writes data/scenes/<id>.json and adds the scene to data/scenes/index.json.
Then render and measure with:  node shots/suite/render.mjs <id ...>
Nothing here reads private photography (prep.safe refuses those paths).
"""
import os, re, sys, json, importlib.util
H = os.path.dirname(os.path.abspath(__file__)); SUITE = os.path.dirname(H); SHOTS = os.path.dirname(SUITE)
sys.path.insert(0, H); sys.path.insert(0, os.path.join(SUITE, 'lib'))
import prep                                   # the lane D cutter (audio, words, archive strips)
from stage2_specs import SPECS
DATA = os.path.join(SUITE, 'data')
WIN = json.load(open(os.path.join(DATA, 'scenes/stage2_windows.json')))
LOCAL = {f[:-4] for f in os.listdir(os.path.join(prep.LAB, 'clips')) if f.endswith('.mp4')}
norm = lambda w: re.sub(r"[^a-z0-9']", '', w.lower())
_grab = None

def grab():
    global _grab
    if _grab is None:
        from archive_grab import Grab
        _grab = Grab()
    return _grab

def window(sid):
    for p in WIN.values():
        for s in p['scenes']:
            if s['id'] == sid: return s
    raise SystemExit('no window for ' + sid)

def word_t(words, spec):
    """'pulsing' | 'pulsing#2' | 3.2 -> (t, anchor word as read)"""
    if isinstance(spec, (int, float)): return float(spec), None
    w, n = (spec.split('#') + ['1'])[:2]
    hits = [x for x in words if norm(x[0]) == norm(w)] or [x for x in words if norm(x[0]).startswith(norm(w))]
    if len(hits) < int(n): raise SystemExit(f'word {spec!r} not in the window: ' + ' '.join(x[0] for x in words))
    x = hits[int(n) - 1]
    return max(0.0, x[1]), x[0]

def pick_clip(query, poem, used, years=None):
    """the best CLIP match that is cached locally, unused in this poem, and not a dark or blank strip"""
    import cv2
    rs = grab().clips(query, k=400, years=years)
    for r in rs:
        if r['clip'] not in LOCAL or r['clip'][:8] in used: continue
        key = prep.archive(r['clip'], 0.0, 6.0)
        im = cv2.imread(os.path.join(DATA, 'archive', key + '.jpg'), 0)
        if im is None or im.mean() < 45 or im.std() < 25: continue
        m = json.load(open(os.path.join(DATA, 'archive', key + '.json')))      # and few black frames (a pane must not go dark)
        cells = [im[i // m['cols'] * m['h']:(i // m['cols'] + 1) * m['h'], i % m['cols'] * m['w']:(i % m['cols'] + 1) * m['w']].mean() for i in range(m['n'])]
        if sum(c < 35 for c in cells) > 0.15 * m['n']: continue
        return r
    raise SystemExit('no local clip for ' + query)

def pane_depth(st, poly, set_layers):
    """The ground line a pane must stand at to show in the plate: just in front of the nearest plate layer or set occluder
    that covers it, so it sits in the surface it was cut from (and puppets nearer than that still pass in front of it)."""
    import numpy as np, cv2
    from PIL import Image
    yh = st['ground'].get('horizon_y_px') or 1080 * 0.45; yg = st['ground']['y_px']; hc = (yg - yh) / st['scale']['px_per_cm_at_ground_line']
    f = st['scale'].get('focal_px_stage') or 960 / np.tan(np.radians(25))
    m = np.zeros((360, 640), np.uint8); cv2.fillPoly(m, [np.int32(np.array(poly) / 3)], 1); area = max(1, m.sum())
    z = 1e9
    rule = {'P3': 'back'}; rule.update(set_layers or {})
    for l in st['layers']:
        if l.get('depth_m') is None or not l.get('file') or rule.get(l.get('plane')) == 'back': continue
        a = np.array(Image.open(os.path.join(SUITE, l['file'])).convert('RGBA').resize((640, 360)))[..., 3] > 40
        if (a & (m > 0)).sum() / area > 0.05: z = min(z, l['depth_m'] * 100 - 4)
    for o in st.get('occluders', []):
        base = max(p[1] for p in o['polygon'])
        if base <= yh: continue
        zo = f * hc / max(base - yh, 0.5)
        mo = np.zeros((360, 640), np.uint8); cv2.fillPoly(mo, [np.int32(np.array(o['polygon']) / 3)], 1)
        if ((mo > 0) & (m > 0)).sum() / area > 0.05: z = min(z, zo - 2)
    if z >= 1e9: return None
    return round(yh + f * hc / z, 1)

def build(sid):
    sp = SPECS[sid]; w = window(sid); poem = sid[:2]
    bd = json.load(open(os.path.join(SHOTS, f'poems/breakdown/{poem}.json')))
    bs = next(s for s in bd['scenes'] if s['id'] == sid)
    st = json.load(open(os.path.join(DATA, f'sets/{sid}.json')))
    prep.audio(sid, {'in': w['in'], 'out': w['out']})
    words = json.load(open(os.path.join(DATA, f'scenes/{sid}.words.json')))['words']
    dur = round(w['out'] - w['in'], 3)
    scene = {'scene_id': sid, 'poem': poem, 'movement': bs['movement'], 'title_card': f"{poem} · {bs['movement']}", 'set': bs['shots'][0]['set'],
             'fps': 24, 'duration': dur, 'lines': bs['lines'], 'read': w['text'], 'shots_from_breakdown': [s['id'] for s in bs['shots']],
             'extensions': ['lib/stage2_extra.js'],
             'audio': {'file': f'suite/data/audio/{sid}.m4a', 'source': 'WYGWYL_Suite_Audio.mp3 (the reading), cut by tools/prep.py; window from tools/stage2_windows.py',
                       'suite_in': w['in'], 'suite_out': w['out'], 'words': words},
             'cast': [], 'beats': [], 'goals': [], 'joins': [], 'fx': [], 'camera': json.loads(json.dumps(sp.get('camera', {'keys': []}))),
             'notes': sp.get('notes', []), 'staged_by': 'stage 2 (tools/stage2_specs.py)'}
    if sp.get('title_card') is False: scene.pop('title_card')
    if sp.get('set_layers'): scene['set_layers'] = sp['set_layers']
    for c in sp['cast']:
        c = dict(c); c.setdefault('side', 'R'); c.setdefault('view', 'front')
        scene['cast'].append(c)
    for b in sp.get('beats', []):
        spec, who, action = b[0], b[1], b[2]
        args = b[3] if len(b) > 3 else None; label = b[4] if len(b) > 4 else None
        t, anchor = word_t(words, spec)
        o = {'t': round(t, 3), 'who': who, 'action': action}
        if anchor: o['word_anchor'] = anchor
        if args:
            args = dict(args)
            if 'arrive_word' in args and '#' in str(args['arrive_word']): args['arrive_word'] = word_t(words, args['arrive_word'])[1]
            o['args'] = args
        if label: o['label'] = label
        scene['beats'].append(o)
    for k in scene['camera'].get('keys', []):
        if isinstance(k['t'], str): k['t'] = round(word_t(words, k['t'])[0], 3)
        elif k['t'] < 0: k['t'] = dur
    for g in sp.get('goals', []):
        g = dict(g)
        for k in ('t0', 't1'):
            if isinstance(g.get(k), str): g[k] = round(word_t(words, g[k])[0], 3)
        scene['goals'].append(g)
    used = set()                                   # clips already opened by the poem's other scenes
    for f in os.listdir(os.path.join(DATA, 'scenes')):
        if f.startswith(poem + '.') and f.endswith('.json') and f.count('.') == 2 and f[:-5] != sid:
            used |= {j.get('clip') for j in json.load(open(os.path.join(DATA, 'scenes', f))).get('joins', [])}
    for j in sp.get('joins', []):
        j = dict(j)
        if 'clip' not in j:
            r = pick_clip(j.pop('query'), poem, used, j.pop('years', None))
            j['clip'] = prep.archive(r['clip'], j.pop('clip_t0', 0.0), j.pop('clip_dur', 6.0))
            j['why'] = (j.get('why', '') + f" · found by archive_grab: {r['title']} ({r['year']}), CLIP {r['score']}").strip(' ·')
        else: j.pop('query', None)
        used.add(j['clip'])
        t, anchor = word_t(words, j.pop('word', 0.0)); j['t'] = round(t, 3)
        if anchor: j['word_anchor'] = anchor
        if 'end_word' in j:
            te, ae = word_t(words, j.pop('end_word'))
            hit = next(x for x in words if x[0] == ae and abs(x[1] - te) < 1e-6) if ae else None
            j['t_end'] = round(hit[2] if hit else te, 3)
        if j.get('surface') and not any(s['id'] == j['surface'] for s in st['surfaces']): raise SystemExit(f"{sid}: no surface {j['surface']}")
        if j['kind'] == 'pane':
            gy = pane_depth(st, j['polygon'], sp.get('set_layers'))
            if gy is not None: j['ground_y'] = gy
        scene['joins'].append(j)
    for fx in sp.get('fx', []):
        fx = dict(fx)
        for k in ('t0', 't1'):
            if isinstance(fx.get(k), str): fx[k] = round(word_t(words, fx[k])[0], 3)
        if fx.get('kind') == 'card' and 'ground_y' not in fx: fx['ground_y'] = fx['at'][1]
        scene['fx'].append(fx)
    out = os.path.join(DATA, f'scenes/{sid}.json')
    old = json.load(open(out)) if os.path.exists(out) else {}
    if old.get('checks'): scene['checks_before_restage'] = {'pass': old['checks'].get('pass'), 'note': 'checks of the previous staging (stand-in set)'} if 'staged_by' not in old else None
    if scene.get('checks_before_restage') is None: scene.pop('checks_before_restage', None)
    json.dump(scene, open(out, 'w'), indent=1)
    idx_p = os.path.join(DATA, 'scenes/index.json'); idx = json.load(open(idx_p))
    idx['scenes'] = [s for s in idx['scenes'] if s['id'] != sid] + [{'id': sid, 'title': f"{poem} · {bs['movement']}", 'set': scene['set'], 'duration': dur}]
    idx['scenes'].sort(key=lambda s: tuple(int(x) for x in s['id'].split('.')))
    json.dump(idx, open(idx_p, 'w'), indent=1)
    print(sid, 'written', dur, 's', len(scene['cast']), 'cast', len(scene['beats']), 'beats', len(scene['joins']), 'joins')

if __name__ == '__main__':
    ids = sys.argv[1:] or list(SPECS)
    for sid in ids: build(sid)
    idx = {f[:-5]: json.load(open(os.path.join(DATA, 'archive', f))) for f in sorted(os.listdir(os.path.join(DATA, 'archive'))) if f.endswith('.json') and f != 'index.json'}
    json.dump(idx, open(os.path.join(DATA, 'archive/index.json'), 'w'), indent=1)
