#!/usr/bin/env python3
"""Stage lane 1: build staged scene JSONs (shots/suite/data/scenes/<id>.json) from a compact spec.

A spec (see tools/stage_01_07.py) names, per scene: the cast and where each one stands on the lane-C set, beats keyed
to words of the reading ('look', 'the#2' = second "the" in the scene), goals, WEAVE joins with an archive query, fx,
camera, and the set_patch (walkable ground, marks, surface depths) that lib/set_patch.js merges into the lane-C set.
This module does the mechanical part:

  · scene window on the suite clock (tools/stage_windows.py: the poem's scenes tile its reading end to end)
  · the reading cut for the window (data/audio/<id>.m4a) and its words, scene-relative (data/scenes/<id>.words.json)
  · the walkable ground, if the spec gives none: lane C's P3 ground mask minus its P0 occluder silhouettes
  · archive strips for the joins: CLIP query (lib/archive_grab.py) -> first local clip -> tiled strip (tools/prep.py)
  · word anchors -> times, so every beat sits on its word

Figure size is never set here: the suite scales every puppet from lane C's horizon + px_per_cm_at_ground_line.
Nothing here reads private photography (prep.safe refuses CAT/EYE, cdmx, Thompson, wygwyl-private paths).
"""
import os, sys, json, re, subprocess
import numpy as np, cv2

H = os.path.dirname(os.path.abspath(__file__)); SUITE = os.path.dirname(H); DATA = os.path.join(SUITE, 'data')
sys.path.insert(0, H); sys.path.insert(0, os.path.join(SUITE, 'lib'))
import prep                                     # safe(), archive(), SUITE_AUDIO
from stage_windows import windows

norm = lambda w: re.sub(r"[^a-z0-9']", '', w.lower())
_grab = None
def grab():
    global _grab
    if _grab is None:
        from archive_grab import Grab
        _grab = Grab()
    return _grab

LOCAL = None
def local_ids():
    global LOCAL
    if LOCAL is None: LOCAL = {f[:-4] for f in os.listdir(os.path.join(prep.LAB, 'clips')) if f.endswith('.mp4')}
    return LOCAL

# ── reading ──
def cut_audio(sid, t_in, t_out):
    out = os.path.join(DATA, 'audio', sid + '.m4a'); wp = os.path.join(DATA, 'scenes', sid + '.words.json')
    same = False
    if os.path.exists(out) and os.path.exists(wp):
        w = json.load(open(wp)); same = abs(w.get('suite_in', -1) - t_in) < 1e-3 and abs(w.get('suite_out', -1) - t_out) < 1e-3
    if not same:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t_in:.3f}', '-to', f'{t_out:.3f}', '-i', prep.safe(prep.SUITE_AUDIO),
                        '-ac', '1', '-c:a', 'aac', '-b:a', '96k', out], check=True)
    return 'suite/data/audio/' + sid + '.m4a'

def scene_words(W, t_in, t_out):
    return [[w[0], round(w[1] - t_in, 3), round(w[2] - t_in, 3), w[3]] for w in W if w[2] > t_in and w[1] < t_out]

def word_time(words, spec, end=False):
    """'look' | 'the#2' (2nd occurrence) | number (seconds) -> (time, anchor text)"""
    if spec is None: return None, None
    if isinstance(spec, (int, float)): return float(spec), None
    m = re.match(r'^(.*?)(?:#(\d+))?$', spec); w, k = norm(m.group(1)), int(m.group(2) or 1)
    hits = [x for x in words if norm(x[0]) == w and x[1] >= -0.05]
    if len(hits) < k: raise SystemExit(f'word not found in scene: {spec!r}  (have: {" ".join(x[0] for x in words)})')
    x = hits[k - 1]
    return (x[2] if end else x[1]), x[0]

# ── ground ──
def auto_walkable(setj, min_frac=0.004):
    g = setj['ground']; hz = g.get('horizon_y_px') or 486
    ground = next((l for l in setj.get('layers', []) if l.get('name') == 'ground' and l.get('file')), None)
    if not ground:                                           # code set (black void): the lower frame
        return [[[0, round(hz + 60)], [1920, round(hz + 60)], [1920, 1078], [0, 1078]]]
    a = cv2.imread(os.path.join(SUITE, ground['file']), cv2.IMREAD_UNCHANGED)
    m = (cv2.resize(a[:, :, 3], (1920, 1080), interpolation=cv2.INTER_NEAREST) > 40).astype(np.uint8)
    for o in setj.get('occluders', []):
        cv2.fillPoly(m, [np.array(o['polygon'], np.int32)], 0)
    m[:int(hz + 12)] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    m = cv2.erode(m, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    polys = []
    for i in sorted(range(1, n), key=lambda i: -st[i, cv2.CC_STAT_AREA]):
        if st[i, cv2.CC_STAT_AREA] < min_frac * 1920 * 1080: continue
        cs, _ = cv2.findContours((lab == i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        c = max(cs, key=cv2.contourArea); c = cv2.approxPolyDP(c, 5, True)
        polys.append([[int(p[0][0]), int(p[0][1])] for p in c])
    return polys

def camera(setj):
    g, sc = setj['ground'], setj['scale']
    hy = g.get('horizon_y_px') or 1080 * 0.45
    hc = (g['y_px'] - hy) / sc['px_per_cm_at_ground_line']
    f = sc.get('focal_px_stage') or 960 / np.tan(np.radians(25))
    return hy, hc, f

def depth_cm(setj, y):
    hy, hc, f = camera(setj); return f * hc / max(0.5, y - hy)

def aim(sid, x, base_y, h_cm):
    """screen point h_cm above the ground row base_y (a point on a vertical surface standing on that row)"""
    setj = json.load(open(os.path.join(DATA, 'sets', sid + '.json'))); hy, hc, f = camera(setj)
    Z = depth_cm(setj, base_y); return [x, round(hy + f * (hc - h_cm) / Z)]

def surface_poly(sid, surf):
    setj = json.load(open(os.path.join(DATA, 'sets', sid + '.json')))
    return [[round(a), round(b)] for a, b in next(x for x in setj['surfaces'] if x['id'] == surf)['polygon']]

def seat_layers(setj, patch, spec):
    """Lane C gives each image plane one median depth. The ground plane (P3) is the floor itself: it lies under the feet,
    so it goes to the back. A mid plane (P4) shallower than the deepest ground a puppet can reach would paint over a
    puppet standing behind its median depth; unless the spec keeps it ('keep_mid'), it goes behind that ground."""
    grounds = patch['walkable'] if isinstance(patch['walkable'][0][0], list) else [patch['walkable']]
    ymin = min(p[1] for gp in grounds for p in gp); zmax = depth_cm(setj, ymin) / 100
    have = {l['id'] for l in patch.get('layers', [])}
    out = list(patch.get('layers', []))
    if spec.get('all_layers_back'):            # a fall / a void over a plate: every plane of the plate is below or behind the bodies
        for l in setj.get('layers', []):
            if l['id'] not in have and l.get('kind') == 'image' and l.get('depth_m') is not None:
                out.append({'id': l['id'], 'depth_m': 999, 'why': 'the bodies fall in front of the whole plate'})
        patch['occluders'] = patch.get('occluders', []) + [{'id': o['id'], 'remove': True} for o in setj.get('occluders', [])]
        patch['layers'] = out
        return
    for l in setj.get('layers', []):
        if l['id'] in have or l.get('kind') != 'image' or l.get('depth_m') is None: continue
        if l.get('name') == 'ground':
            out.append({'id': l['id'], 'depth_m': 999, 'why': 'the ground plane lies under the feet: drawn behind every puppet'})
        elif l.get('name') in ('mid', 'far') and l['depth_m'] < zmax and not spec.get('keep_mid'):
            out.append({'id': l['id'], 'depth_m': round(zmax + 0.5, 2), 'why': f"{l.get('name')} plane (median {l['depth_m']} m) sits behind the deepest walkable ground ({zmax:.1f} m)"})
    if out: patch['layers'] = out

# ── archive ──
USED = set(); BAD = set()
def pick_clip(query, title=None, years=None, negative=None):
    """CLIP query over the archive thumbnails, kept to clips that are on this machine; `title` keeps it to one film
    (a substring of its title), so the pick is the film the dossier names and the query only chooses the moment."""
    loc = local_ids(); G = grab(); G._load_clips()
    pool = None
    if title:
        t = title.lower()
        pool = {c for c in loc if t in str((G._corpus.get(c) or {}).get('sourceTitle', '')).lower()}
        if not pool: raise SystemExit('no local clip titled ' + title)
    for r in G.clips(query or title, k=20000 if pool else 600, years=years, negative=negative):
        if r['clip'] in loc and (pool is None or r['clip'] in pool) and r['clip'] not in USED and r['clip'] not in BAD:
            USED.add(r['clip']); return r
    if pool:                                                  # every clip of that film already used: reuse the best
        r = G.clips(query or title, k=20000); r = [x for x in r if x['clip'] in pool and x['clip'] not in BAD]
        if r: return r[0]
    raise SystemExit('no local clip for ' + str(query))

def strip(clip_id, dur, fps=6, w=320):
    key = prep.archive(clip_id, 0.0, min(dur, 6.0), fps=fps, w=w)
    idx = {f[:-5]: json.load(open(os.path.join(DATA, 'archive', f))) for f in sorted(os.listdir(os.path.join(DATA, 'archive'))) if f.endswith('.json') and f != 'index.json'}
    json.dump(idx, open(os.path.join(DATA, 'archive/index.json'), 'w'), indent=1)
    return key, idx[key]

OVER = {'prop', 'sweep', 'flash', 'rain', 'glow', 'iris', 'cracks', 'blinds', 'cobweb', 'scatter', 'darken', 'reticle', 'strobe', 'sunrise'}
def over(fx):
    """lib/fx_extra.js pieces sit in front of the set unless they name a depth (draw.js sorts fx with no depth to the back)"""
    fx = dict(fx)
    if fx['kind'] in OVER and fx.get('depth_m') is None and fx.get('ground_y') is None: fx.setdefault('over', True)
    return fx

# ── build one scene ──
def build(sid, spec, win, W, poem_meta):
    setj = json.load(open(os.path.join(DATA, 'sets', sid + '.json')))
    t_in, t_out = win['in'], win['out']
    dur = round(t_out - t_in, 3)
    words = scene_words(W, t_in, t_out)
    audio = cut_audio(sid, t_in, t_out)
    json.dump({'scene_id': sid, 'suite_in': t_in, 'suite_out': t_out, 'source': 'kernel-data.json (suite clock, faster-whisper word times)', 'words': words},
              open(os.path.join(DATA, 'scenes', sid + '.words.json'), 'w'), indent=0)
    patch = dict(spec.get('patch') or {})
    if 'walkable' not in patch: patch['walkable'] = auto_walkable(setj); patch['_walkable_from'] = 'lane C P3 ground mask minus P0 occluders (stage_build.auto_walkable)'
    seat_layers(setj, patch, spec)
    beats = []
    for b in spec.get('beats', []):
        who, action, wd, args = b[0], b[1], b[2], (b[3] if len(b) > 3 else None)
        t, anchor = word_time(words, wd)
        o = {'t': round(t, 3), 'who': who, 'action': action}
        if anchor: o['word_anchor'] = anchor
        if len(b) > 4 and b[4]: o['label'] = b[4]
        if action == 'hold_gesture' and args is not None and 'hand' not in args:    # the hand card that fits the gesture (lib/hands_extra.js)
            args = {**args, 'hand': {'palm_out': 'open', 'arms_up': 'open', 'reach_out': 'open', 'page_up': 'grip', 'hand_chest': 'relaxed', 'hand_low': 'relaxed'}.get(args.get('name'), 'relaxed')}
        if args is not None: o['args'] = args
        beats.append(o)
    joins = []
    for j in spec.get('joins', []):
        j = dict(j)
        t, anchor = word_time(words, j.pop('word', 0.0))
        t_end = None
        if 'end_word' in j: t_end, end_anchor = word_time(words, j.pop('end_word'), end=True); j['end_word'] = end_anchor
        if 't_end' in j: t_end = j['t_end']
        span = (t_end if t_end is not None else dur) - t
        if span <= 0.2: raise SystemExit(f'{sid}: join ends before it starts ({j}); use word#n for repeated words')
        if 'clip' in j and len(j['clip']) > 8: rec = grab().clip_record(j['clip']); USED.add(j['clip'])
        elif 'clip' in j: rec = {'clip': next(c for c in local_ids() if c.startswith(j['clip'])), 'title': None}
        else: rec = None
        q = {k: j.pop(k, None) for k in ('query', 'title', 'years', 'negative')}
        for attempt in range(6):
            if rec is None: rec = pick_clip(q['query'], title=q['title'], years=q['years'], negative=q['negative'])
            try: key, meta = strip(rec['clip'], span); break
            except (IndexError, SystemExit) as e: print('  unreadable clip', rec['clip'], '- next'); BAD.add(rec['clip']); rec = None
        else: raise SystemExit('no readable clip for ' + str(q))
        j['clip'] = key; j['t'] = round(t, 3)
        if anchor: j['word_anchor'] = anchor
        if t_end is not None: j['t_end'] = round(t_end, 3)
        j.setdefault('why', '')
        j['archive'] = f"{meta.get('title')} ({meta.get('year')}) · clip {meta['clip']}"
        joins.append(j)
    scene = {
        'scene_id': sid, 'poem': sid[:2], 'movement': win['movement'], 'title_card': f"{sid[:2]} · {win['movement']}",
        'set': setj.get('set'), 'fps': 24, 'duration': dur, 'lines': poem_meta['lines'],
        'shots_from_breakdown': poem_meta['shots'],
        'audio': {'file': audio, 'source': 'WYGWYL_Suite_Audio.mp3 (the reading), cut by tools/stage_build.py', 'suite_in': t_in, 'suite_out': t_out,
                  'words': words, 'window': 'tools/stage_windows.py: scenes tile the poem reading' + (' · UNREAD: no words of the reading fall in this scene' if win.get('unread') else '')},
        'set_patch': patch, 'cast': spec['cast'], 'beats': beats, 'goals': spec.get('goals', []), 'joins': joins, 'fx': [over(f) for f in spec.get('fx', [])],
        'camera': spec.get('camera') or {'keys': [{'t': 0, 'zoom': 1, 'x': 960, 'y': 540}, {'t': dur, 'zoom': 1.04, 'x': 960, 'y': 560}]},
        'notes': spec.get('notes', []), 'staged_by': 'stage lane 1 (poems 01-07), tools/stage_01_07.py',
    }
    if spec.get('title_card') is False: scene.pop('title_card')
    # keep any measured checks from a previous render out: they are re-measured on the next render
    json.dump(scene, open(os.path.join(DATA, 'scenes', sid + '.json'), 'w'), indent=1)
    idxp = os.path.join(DATA, 'scenes/index.json'); idx = json.load(open(idxp))
    idx['scenes'] = [s for s in idx['scenes'] if s['id'] != sid] + [{'id': sid, 'title': scene['title_card'] if 'title_card' in scene else sid, 'set': scene['set'], 'duration': dur}]
    idx['scenes'].sort(key=lambda s: [int(x) for x in s['id'].split('.')])
    json.dump(idx, open(idxp, 'w'), indent=1)
    return scene


def build_poems(SPECS, only=None):
    bd = {}
    for sid in SPECS:
        if only and sid not in only and sid[:2] not in only: continue
        p = sid[:2]
        if p not in bd:
            ws, W = windows(p); b = json.load(open(os.path.join(os.path.dirname(SUITE), 'poems/breakdown', p + '.json')))
            bd[p] = ({w['id']: w for w in ws}, W, {s['id']: s for s in b['scenes']})
        wins, W, scenes = bd[p]
        meta = {'lines': scenes[sid]['lines'], 'shots': [s['id'] for s in scenes[sid]['shots']]}
        sc = build(sid, SPECS[sid], wins[sid], W, meta)
        print(sid, f"{sc['duration']:.1f}s", len(sc['audio']['words']), 'words', len(sc['beats']), 'beats', len(sc['joins']), 'joins')
