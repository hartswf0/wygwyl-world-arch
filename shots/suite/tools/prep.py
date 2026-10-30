#!/usr/bin/env python3
"""Cut-Out Suite, lane D: prepare the material a staged scene needs, from sources already on this machine.

  /Users/gaia/anaconda3/bin/python3 shots/suite/tools/prep.py [scene_id ...]

For each scene in SCENES it writes, under shots/suite/data/:
  audio/<scene>.m4a           the reading for the scene window, cut from WYGWYL_Suite_Audio.mp3 (suite clock)
  scenes/<scene>.words.json   word timings for that window (kernel-data.json, suite clock), scene-relative
  archive/<clip8>.jpg/.json   a tiled frame strip of each archive clip a join opens (8 fps, 320 px), from lab/clips
  proxy/plates/<set>.jpg      a 1920x1080 plate for the set (stand-in until lane C's sets/<scene>.json exist)
and once: proxy/parts.json + proxy/characters.json, stand-ins for lanes A and B built from parts already in the repo
(weave/cast/man jointed parts, play/data.json replacement cards, character_rigs_library.json proportions).

Nothing here reads the private photography: every source path is checked against PRIVATE and refused.
"""
import os, re, sys, json, subprocess
import numpy as np, cv2

H = os.path.dirname(os.path.abspath(__file__)); SUITE = os.path.dirname(H); SHOTS = os.path.dirname(SUITE)
DATA = os.path.join(SUITE, 'data')
SUITE_AUDIO = '/Users/gaia/resurrecting atlantis/CINEOSIS_44/lab/wygwyl/WYGWYL_Suite_Audio.mp3'
KERNEL = '/Users/gaia/cineosis-lab-cels/lab/bets/kernel-data.json'
LAB = '/Users/gaia/resurrecting atlantis/CINEOSIS_44/lab'
DIST = '/Users/gaia/Downloads/butterfly-halfworld/.claude/worktrees/hungry-cori-d982c1/wygwyl/world/districts'
PRIVATE = re.compile(r'(/CAT/|/EYE/|cdmx|thompson|wygwyl-private)', re.I)

# scene windows on the suite clock (seconds), the plate each proxy set uses, and the archive clips its joins open
SCENES = {
    '01.2': {'in': 36.70, 'out': 42.90, 'set': 'bedroom_highrise',
             'plate': ('video', '/Users/gaia/resurrecting atlantis/BOY/WN_LEAVE/WGY001_DS__Mood_Environment_Stabilizer__A_dimly_lit_9b49bf11-2387-44a0-b00d-ad914c7c48a0_2.mp4', 2.6),
             'clips': {'147f497d-6457-5bcd-a1a1-ed98ff0f2505': (0.0, 6.0), '8b20a7e8-5587-5e18-8553-1c1ec0ff408f': (4.0, 4.0)}},
    '08.1': {'in': 751.80, 'out': 760.80, 'set': 'rooftop_club',
             'plate': ('image', os.path.join(DIST, 'v/073.webp'), None),
             'clips': {'9cb98c3d': (0.0, 8.0), '2c2401f2-cd39-5635-8be8-b6b754ea6095': (0.0, 6.0)}},
    '09.4': {'in': 935.60, 'out': 946.60, 'set': 'harbor_path_east',
             'plate': ('image', os.path.join(DIST, 'v/085.webp'), None),
             'clips': {'b1ec80f0': (2.0, 8.0), '27ef5094': (0.0, 6.0)}},
}

def safe(p):
    if PRIVATE.search(p): raise SystemExit('refused (private source): ' + p)
    return p

def run(*a): subprocess.run(a, check=True)

def local_clip(prefix):
    for f in os.listdir(os.path.join(LAB, 'clips')):
        if f.startswith(prefix) and f.endswith('.mp4'): return os.path.join(LAB, 'clips', f)
    raise SystemExit('no local clip ' + prefix)

def plate(sid, cfg):
    out = os.path.join(DATA, 'proxy/plates', cfg['set'] + '.jpg')
    if os.path.exists(out): return
    kind, src, t = cfg['plate']; safe(src)
    if kind == 'video':
        cap = cv2.VideoCapture(src); cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, im = cap.read(); assert ok, src
    else:
        im = cv2.imread(src); assert im is not None, src
    h, w = im.shape[:2]; s = max(1920 / w, 1080 / h)                       # cover-fit, centre crop
    im = cv2.resize(im, (round(w * s), round(h * s)), interpolation=cv2.INTER_CUBIC)
    y0 = (im.shape[0] - 1080) // 2; x0 = (im.shape[1] - 1920) // 2
    cv2.imwrite(out, im[y0:y0 + 1080, x0:x0 + 1920], [cv2.IMWRITE_JPEG_QUALITY, 86])
    print('plate', out)

def audio(sid, cfg):
    out = os.path.join(DATA, 'audio', sid + '.m4a')
    if not os.path.exists(out):
        run('ffmpeg', '-v', 'error', '-y', '-ss', f"{cfg['in']:.3f}", '-to', f"{cfg['out']:.3f}", '-i', safe(SUITE_AUDIO),
            '-ac', '1', '-c:a', 'aac', '-b:a', '96k', out)
        print('audio', out)
    K = json.load(open(KERNEL)); words = []
    for l in K['lines']:
        for w in l.get('words', []):
            if w['t1'] > cfg['in'] and w['t0'] < cfg['out']:
                words.append([w['w'], round(w['t0'] - cfg['in'], 3), round(w['t1'] - cfg['in'], 3), l['id']])
    json.dump({'scene_id': sid, 'suite_in': cfg['in'], 'suite_out': cfg['out'], 'source': 'kernel-data.json (suite clock, faster-whisper word times)',
               'words': words}, open(os.path.join(DATA, 'scenes', sid + '.words.json'), 'w'), indent=0)
    print('words', sid, len(words))

def archive(prefix, t0, dur, fps=8, w=320, cols=8):
    src = safe(local_clip(prefix)); cid = os.path.basename(src)[:-4]; key = cid[:8]
    out = os.path.join(DATA, 'archive', key + '.jpg')
    corp = json.load(open(os.path.join(LAB, 'cache/corpus.json'))).get(cid, {})
    if not os.path.exists(out):
        cap = cv2.VideoCapture(src); sfps = cap.get(cv2.CAP_PROP_FPS) or 24; n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames = []
        k = 0
        while len(frames) < int(dur * fps):
            fi = int((t0 + k / fps) * sfps)
            if fi >= n: break
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi); ok, im = cap.read()
            if not ok: break
            h0, w0 = im.shape[:2]; frames.append(cv2.resize(im, (w, round(h0 * w / w0)), interpolation=cv2.INTER_AREA)); k += 1
        fh = frames[0].shape[0]; rows = (len(frames) + cols - 1) // cols
        sheet = np.zeros((rows * fh, cols * w, 3), np.uint8)
        for i, f in enumerate(frames): sheet[(i // cols) * fh:(i // cols + 1) * fh, (i % cols) * w:(i % cols + 1) * w] = f[:fh]
        cv2.imwrite(out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 82])
        json.dump({'clip': cid, 'title': corp.get('sourceTitle'), 'year': corp.get('sourceYear'), 'fps': fps, 'n': len(frames), 'w': w, 'h': fh,
                   'cols': cols, 'file': key + '.jpg', 'clip_window_s': [t0, t0 + len(frames) / fps], 'ledger': 'OBSERVED (archive film)'},
                  open(os.path.join(DATA, 'archive', key + '.json'), 'w'), indent=1)
        print('archive', key, corp.get('sourceTitle'), len(frames))
    return key

# ── stand-ins for lanes A and B, in the contract's schema ──
VIEW = {'prof': 'profile', 'q3': 'threequarter', 'front': 'front', 'back': 'back', 'back3q': 'threequarter_back'}
CARD_CAST = {  # suite character id -> (play/data.json key, costume)
    'poet': [('poet/black_tshirt', 'black_tshirt'), ('poet/red_black_sunglasses', 'red_black_sunglasses')],
    'ex': [('ex/ex_jacket', 'ex_jacket')],
    'father_elder': [('father_elder/poem09', 'elder_father_coat')],
    'dancer_dress': [('club_dress/club', 'club_dress')],
    'dancer_shirt': [('club_shirt/club', 'club_shirt')],
    'dancer_jacket': [('club_jacket/club', 'club_jacket')],
}
# shoulder sockets read off the cards by eye (card px), for contact targets on replacement-card characters
CARD_SOCKETS = {('father_elder/poem09', '00.webp'): {'shoulder_L': [130, 96], 'shoulder_R': [36, 94], 'neck': [92, 70]},
                ('ex/ex_jacket', '02.webp'): {'hand_R': [212, 95]}}
# which way each card faces on screen, read off the cards by eye (R = toward screen right); front/back cards: R
CARD_FACING = {('father_elder/poem09', '00.webp'): 'L', ('father_elder/poem09', '01.webp'): 'R', ('ex/ex_jacket', '02.webp'): 'R',
               ('club_dress/club', '01.webp'): 'L', ('club_shirt/club', '01.webp'): 'R', ('club_jacket/club', '01.webp'): 'R'}
MAN_PART = {'torso': 'torso', 'pelvis': 'pelvis', 'uarm': 'upper_arm', 'farm': 'forearm', 'hand': 'hand', 'thigh': 'thigh',
            'shin': 'shin', 'boot': 'foot', 'head': 'head'}

def proxies():
    parts = []
    man = json.load(open(os.path.join(SHOTS, 'weave/cast/man/cast.json')))['parts']
    # weave/cast/man/cast.json is stale for 13 parts (the PNGs were re-cut at another size); sockets re-read off the PNGs
    FIX = {'boot.flat': {'ankle': [84.3, 294.5], 'toe': [480, 380], 'heel': [62, 418], 'toe_sole': [540, 402]},
           'boot.toe': {'ankle': [120, 220], 'toe': [420, 510]},
           'hand.grip': {'wrist': [137, 292]}, 'hand.fist': {'wrist': [131, 288]}, 'hand.point': {'wrist': [28, 111]},
           'pelvis.front': {'hip': [218, 20], 'hip_near': [330, 140], 'hip_far': [106, 140]}, 'pelvis.profile': {'hip': [119, 14], 'hip_near': [131, 126], 'hip_far': [110, 126]},
           'torso.front': {'hip': [118, 425], 'neck': [118, 18], 'shoulder_near': [200, 60], 'shoulder_far': [36, 60]}}
    from PIL import Image as _I
    for pid, p in man.items():
        sz = list(_I.open(os.path.join(SHOTS, 'weave', p['file'])).size)
        if sz != p['size']:
            p = dict(p, size=sz, stale_cast_json=True)
            if pid in FIX: p['sockets'] = FIX[pid]
            elif pid.startswith('head.'): p['sockets'] = {'neck': [round(sz[0] * (0.46 if 'profile' in pid else 0.48), 1), round(sz[1] * 0.82, 1)]}
            p['pivot'] = list(p['sockets'].values())[0]
            man[pid] = p
    for pid, p in man.items():
        kind = pid.split('.')[0]; rest = pid.split('.')[1:]
        if kind not in MAN_PART: continue
        view, state, side = '-', '-', '-'
        for r in rest:
            if r.startswith(('profile', 'front', 'threequarter', 'back')):
                view = {'profile_R': 'profile', 'profile_L': 'profile', 'threequarter_R': 'threequarter', 'threequarter_L': 'threequarter'}.get(r, r)
                if r.endswith('_R'): side = 'R'
                if r.endswith('_L'): side = 'L'
            else: state = r
        if kind == 'hand' and state == '-': state = 'open'
        if kind == 'boot' and view == '-': view = 'profile'
        if kind == 'hand' and view == '-': view = 'profile'
        parts.append({'id': 'man.' + pid, 'character': 'poet', 'costume': 'red_black_sunglasses', 'part': MAN_PART[kind], 'side': side,
                      'view': view if view != '-' else 'profile', 'state': state, 'file': 'weave/' + p['file'], 'w': p['size'][0], 'h': p['size'][1],
                      'pivot': p['pivot'], 'parent_part': None, 'sockets': p['sockets'], 'scale': {'px_per_cm': None, 'source': 'fit to bone length at solve time'},
                      'height_cm_real': None, 'sheet': p.get('sheet'), 'provenance': 'weave/cast/man (generated sheets, INVENTED)' + ('; sockets re-read by suite prep (cast.json stale for this PNG)' if p.get('stale_cast_json') else ''), 'painted': True})
    # man parts cut but never registered in cast.json: pivots estimated from the alpha box (marked as such)
    for pid, kind, view, side, state, piv in [
            ('torso.threequarter_R', 'torso', 'threequarter', 'R', '-', {'hip': (0.5, 0.95), 'neck': (0.5, 0.05)}),
            ('torso.threequarter_back', 'torso', 'threequarter_back', '-', '-', {'hip': (0.5, 0.95), 'neck': (0.5, 0.05)}),
            ('torso.back', 'torso', 'back', '-', '-', {'hip': (0.5, 0.95), 'neck': (0.5, 0.05)}),
            ('boot.front', 'foot', 'front', '-', 'flat', {'ankle': (0.5, 0.42), 'sole': (0.5, 0.99)}),
            ('boot.back', 'foot', 'back', '-', 'flat', {'ankle': (0.5, 0.36), 'sole': (0.5, 0.99)}),
            ('proc.hand.relaxed', 'hand', 'profile', '-', 'relaxed', {'wrist': (0.10, 0.42), 'tip': (0.90, 0.45)}),
            ('proc.hand.grip', 'hand', 'profile', '-', 'grip', {'wrist': (0.10, 0.45), 'tip': (0.62, 0.55)})]:
        f = os.path.join(SHOTS, 'weave/cast/man/parts', pid + '.png'); a = cv2.imread(f, cv2.IMREAD_UNCHANGED)
        ys, xs = np.nonzero(a[:, :, 3] > 24); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        sk = {k: [round(float(x0 + u * (x1 - x0)), 1), round(float(y0 + v * (y1 - y0)), 1)] for k, (u, v) in piv.items()}
        first = list(sk)[0]
        parts.append({'id': 'man.' + pid, 'character': 'poet', 'costume': 'red_black_sunglasses', 'part': MAN_PART[kind] if kind in MAN_PART else kind,
                      'side': side, 'view': view, 'state': state, 'file': 'weave/cast/man/parts/' + pid + '.png', 'w': int(a.shape[1]), 'h': int(a.shape[0]),
                      'pivot': sk[first], 'parent_part': None, 'sockets': sk, 'scale': {'px_per_cm': None, 'source': 'fit to bone length at solve time'},
                      'height_cm_real': None, 'sheet': None, 'provenance': 'weave/cast/man/parts (pivots estimated from alpha box by suite prep)', 'painted': True})
    # hands: the farthest inked point from the wrist is the fingertip line; record it so every hand card is sized
    # by the same thing (wrist to fingertips = hand length), whatever its sheet's scale
    for p in parts:
        if p['part'] != 'hand': continue
        a = cv2.imread(os.path.join(SHOTS, p['file']), cv2.IMREAD_UNCHANGED); ys, xs = np.nonzero(a[:, :, 3] > 24)
        w0 = p['sockets'].get('wrist', p['pivot']); d = np.hypot(xs - w0[0], ys - w0[1]); i = int(d.argmax())
        p['sockets']['fingertips'] = [int(xs[i]), int(ys[i])]
    play = {c['key']: c for c in json.load(open(os.path.join(SHOTS, 'play/data.json')))['characters']}
    chars = []
    for cid, keys in CARD_CAST.items():
        for key, costume in keys:
            c = play[key]
            for d in c['draws']:
                f = os.path.join(SHOTS, 'play/assets', key.replace('/', '__'), d['f'])
                a = cv2.imread(f, cv2.IMREAD_UNCHANGED); ys, xs = np.nonzero(a[:, :, 3] > 24) if a.shape[2] == 4 else (np.array([0, a.shape[0] - 1]), np.array([0]))
                top, bot = int(ys.min()), int(ys.max())
                parts.append({'id': f"card.{key.replace('/', '.')}.{d['f'][:-5]}", 'character': cid, 'costume': costume, 'part': 'body', 'side': '-',
                              'view': VIEW.get(d['view'], d['view']), 'state': d['cls'], 'file': os.path.relpath(f, SHOTS), 'w': d['w'], 'h': d['h'],
                              'pivot': [d['ax'], bot], 'parent_part': None, 'sockets': CARD_SOCKETS.get((key, d['f']), {}),
                              'scale': {'px_per_cm': round((bot - top) / c['height_cm'], 4) if d['cls'] in ('stand', 'walk') else round(d['body_px'] / c['height_cm'], 4),
                                        'source': 'alpha height / height_cm (stand, walk); play body_px / height_cm (bent poses)'},
                              'figure_px': (bot - top) if d['cls'] in ('stand', 'walk') else d['body_px'],
                              'height_cm_real': c['height_cm'], 'sheet': d.get('id'), 'provenance': 'play/data.json replacement card (generated, INVENTED)',
                              'painted': True, 'label': d.get('sem_label'), 'alpha_top': top, 'facing': CARD_FACING.get((key, d['f']), 'R')})
    rigs = json.load(open(os.path.join(SHOTS, 'arena/parts/kit3/release_v2/character_rigs_library.json')))['rigs']
    def entry(cid, name, h, heads, rig, stride, mode):
        ps = [p for p in parts if p['character'] == cid]
        views = {}
        for p in ps: views.setdefault(p['view'], {'parts': [], 'joints': {}})['parts'].append(p['id'])
        an = rigs[rig]['anatomy'] if rig else {}
        return {'id': cid, 'name': name, 'height_cm': h, 'head_heights': heads,
                'proportions': {'hip': an.get('hip_elevation_fraction', 0.53), 'torso': an.get('torso_to_body_fraction', 0.32),
                                'source': f'character_rigs_library.json:{rig}' if rig else 'default adult 7.5H'},
                'views': views, 'replacement': {'heads': [p['id'] for p in ps if p['part'] == 'head'], 'hands': [p['id'] for p in ps if p['part'] == 'hand']},
                'walk': {'source': 'suite footstep planner', 'cycle_frames': 26, 'stride_cm': stride}, 'suite_mode': mode,
                'solve_notes': [], 'arena': {}}
    chars = [entry('poet', 'POET', 184, 7.5, 'poet_tracksuit_31', 66, 'jointed'),
             entry('ex', 'EX', 188, 7.6, 'ex_jacket_back', 68, 'cards'),
             entry('father_elder', 'FATHER (elder guise)', 175, 7.4, 'mother_ancestors_family', 54, 'cards'),
             entry('dancer_dress', 'DANCER (club dress)', 168, 7.3, 'dj_club_citizens', 60, 'cards'),
             entry('dancer_shirt', 'DANCER (club shirt)', 178, 7.5, 'dj_club_citizens', 62, 'cards'),
             entry('dancer_jacket', 'DANCER (club jacket)', 180, 7.5, 'dj_club_citizens', 62, 'cards')]
    chars[1]['view_rule'] = {'allowed': ['back', 'threequarter_back'], 'why': "EX's face is never seen"}
    json.dump({'about': 'STAND-IN for lane A (shots/suite/data/parts.json): weave/cast/man jointed parts + play/data.json replacement cards',
               'parts': parts}, open(os.path.join(DATA, 'proxy/parts.json'), 'w'), indent=0)
    json.dump({'about': 'STAND-IN for lane B (shots/suite/data/characters.json)', 'characters': chars},
              open(os.path.join(DATA, 'proxy/characters.json'), 'w'), indent=1)
    print('proxy parts', len(parts), 'characters', len(chars))

if __name__ == '__main__':
    ids = sys.argv[1:] or list(SCENES)
    proxies()
    idx = {}
    for sid in ids:
        cfg = SCENES[sid]; plate(sid, cfg); audio(sid, cfg)
        for pre, (t0, d) in cfg['clips'].items(): archive(pre, t0, d)
    if os.path.exists(os.path.join(DATA, 'archive')):
        idx = {f[:-5]: json.load(open(os.path.join(DATA, 'archive', f))) for f in sorted(os.listdir(os.path.join(DATA, 'archive'))) if f.endswith('.json') and f != 'index.json'}
        json.dump(idx, open(os.path.join(DATA, 'archive/index.json'), 'w'), indent=1)
