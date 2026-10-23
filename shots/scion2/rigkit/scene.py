"""Compose a poem as scenes:  python3 -m rigkit.scene shots/scion2/poems/<NN>/plan.json [--frames t,t,...] [--out name]
(run from shots/scion2).

A poem is a list of SHOTS, normally one per timeline scene (shots/stage/timeline/NN.json), cut on the scene
boundaries; a scene whose plan text names a cut (09.3: booth -> mother's room) may hold several shots.
Per shot:
  * BACKDROP: the stage's own composed scene (shots/stage/plans/NN.json scenes[].layers: the ensembles placed
    by depth through the scene camera, true scale, op/blend/rot/flip exactly as the stage draws them), minus the
    stand-in figure cards (roles poet/ex/father/woman, the hidden solved action clip, the cue-driven archive still).
    A shot may borrow another scene's set ("set": "09.5") when the plan text asks for that place.
  * CHARACTERS: each one a rigkit character driven by animate.plan (pose-to-pose on word cues, planted feet,
    settle, swaps on held frames, head never with the hands), standing on the stage floor line at its depth:
    px/cm = camera ppc / k, the torso = torso_frac x height_cm.  Placed where the stage's own card of that
    role stood ({"role": "poet"}), in an ensemble slot ({"slot": "ens.phone_booth.quay:caller"}), or at
    {"x", "k"} / {"x", "foot_y"}.  A character is drawn at the depth of the card it replaces, or just under
    a named set layer ("under": "booth frame"), so set planes in front of it cross it.
  * CAMERA: a deliberate framing per shot: zoom so the framed figures fill "fill" of the frame height with the
    feet at "foot" of the frame, an optional slow push over the shot.  Cuts are hard.
Per frame: the set groups (pre-rendered once per shot in stage space at the shot's largest zoom) are warped
through the camera; each character is rendered straight from its rig masters through the same camera (never
an upscaled frame), with a soft contact shadow on the floor line.
Writes <out>.mp4 (1600x900, 24 fps, audio muxed), <out>_strip.jpg (every second + every cut), <out>.json.
"""
import json, math, os, re, subprocess, sys
import numpy as np, cv2

from . import core, posing, animate

STAGE = os.path.join(core.ROOT, 'shots/stage')
sys.path.insert(0, os.path.join(STAGE, 'ensembles'))
from lib import PARTS, CUT, load_ensembles          # noqa: E402  (the stage's own catalogue / ensembles, read only)
from resolve import Cam, slot_pos                    # noqa: E402

W, H = 1600, 900
FPS = animate.FPS
BG = np.array([3, 4, 5], np.float32)                 # BGR of the stage's #050403
STANDIN_ROLES = ('poet', 'ex', 'father', 'woman', 'action', 'archive')
TORSO_FRAC = 0.29                                    # neck->mid-hip over standing height, measured on the rigs


# ------------------------------------------------------------------ poem data
def load_poem(n):
    tl = json.load(open(os.path.join(STAGE, 'timeline/%s.json' % n)))
    pl = json.load(open(os.path.join(STAGE, 'plans/%s.json' % n)))
    return tl, {s['key']: s for s in pl['scenes']}


def norm(w):
    return re.sub(r'[^a-z0-9]', '', w.lower())


def word_t(tl, word, near):
    c = [w for w in tl['words'] if norm(w['w']) == norm(word)]
    if not c:
        raise ValueError('word not found: %s' % word)
    return min(c, key=lambda w: abs(w['s'] - near))['s']


def when(tl, v, scene=None, edge='t0'):
    """a time: number, 'scene' (the scene's own edge), or {word, near}"""
    if v is None or v == 'scene':
        return next(s for s in tl['scenes'] if s['key'] == scene)[edge]
    if isinstance(v, (int, float)):
        return float(v)
    return word_t(tl, v['word'], v['near'])


# ------------------------------------------------------------------ set cards
_IMG = {}


def card_img(L):
    key = L.get('part') or L.get('src')
    if key not in _IMG:
        f = os.path.join(CUT, PARTS[key]['file']) if L.get('part') else os.path.normpath(os.path.join(STAGE, L['src']))
        im = cv2.imread(f, cv2.IMREAD_UNCHANGED)
        if im is None:
            raise FileNotFoundError(f)
        if im.ndim == 2:
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
        if im.shape[2] == 3:
            im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
        _IMG[key] = im
    return _IMG[key]


def card_size(L):
    if L.get('h'):
        return L['w'], L['h']
    if L.get('part'):
        b = PARTS[L['part']]['bbox']
        return L['w'], L['w'] * b[3] / b[2]
    return L['w'], L['w'] * L.get('ar', 9 / 16)


def foot_of(L):
    """where a stage figure card stood: stage_scene.figure puts y = foot - h/2 + .01 h"""
    w, h = card_size(L)
    return L['x'], L['y'] + 0.49 * h


def draw_card(acc, L, S):
    """draw one stage layer into a premultiplied float RGBA canvas in stage space x S, the way index.html does:
    an image stretched to w x h about its centre, CSS transform rotate(rot) scaleX(flip), opacity, blend."""
    im = card_img(L).astype(np.float32)
    w, h = card_size(L)
    ih, iw = im.shape[:2]
    r = math.radians(L.get('rot', 0))
    fl = -1.0 if L.get('flip') else 1.0
    M = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]]) @ np.diag([fl, 1.0]) @ np.diag([w / iw, h / ih]) * S
    c = np.array([L['x'], L['y']]) * S
    T = np.hstack([M, (c - M @ np.array([iw / 2, ih / 2]))[:, None]])
    Hc, Wc = acc.shape[:2]
    pts = (T[:, :2] @ np.array([[0, 0], [iw, 0], [0, ih], [iw, ih]]).T).T + T[:, 2]
    x0, y0 = max(0, int(pts[:, 0].min()) - 2), max(0, int(pts[:, 1].min()) - 2)
    x1, y1 = min(Wc, int(pts[:, 0].max()) + 3), min(Hc, int(pts[:, 1].max()) + 3)
    if x1 <= x0 or y1 <= y0:
        return acc
    T2 = T.copy(); T2[:, 2] -= (x0, y0)
    shrink = math.sqrt(abs(np.linalg.det(M)))
    pm = im.copy(); pm[..., :3] *= pm[..., 3:] / 255.
    if shrink < 0.7:                       # strong minification: pre-shrink so the warp does not alias
        k = max(shrink * 1.4, 1e-3)
        pm = cv2.resize(pm, (max(1, int(iw * k)), max(1, int(ih * k))), interpolation=cv2.INTER_AREA)
        T2 = np.hstack([T2[:, :2] / k, T2[:, 2:]])          # p' = k p
    src = cv2.warpAffine(pm, T2, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    src *= L.get('op', 1.0)
    d = acc[y0:y1, x0:x1]
    a = src[..., 3:] / 255.
    mode = L.get('blend', 'normal')
    if mode == 'screen':                   # premultiplied screen: s + d - s*d
        d[..., :3] = src[..., :3] + d[..., :3] - src[..., :3] * d[..., :3] / 255.
        d[..., 3:] = src[..., 3:] + d[..., 3:] * (1 - a)
    elif mode in ('lighter', 'plus-lighter'):
        d[..., :3] = np.minimum(255, d[..., :3] + src[..., :3]); d[..., 3:] = np.minimum(255, d[..., 3:] + src[..., 3:])
    elif mode == 'multiply':
        d[..., :3] = src[..., :3] * d[..., :3] / 255. + src[..., :3] * (1 - d[..., 3:] / 255.) + d[..., :3] * (1 - a)
        d[..., 3:] = src[..., 3:] + d[..., 3:] * (1 - a)
    else:
        d[...] = src + d * (1 - a)
    acc[y0:y1, x0:x1] = d
    return acc


# ------------------------------------------------------------------ shot set-up
def shot_layers(shot, scenes):
    """the backdrop layers of a shot and the stand-in cards it removed, in stage draw order"""
    sc = scenes[shot.get('set', shot['scene'])]
    drop_roles = set(shot.get('drop_roles', STANDIN_ROLES))
    drop_labels = set(shot.get('drop', []))
    out, removed = [], []
    for i, L in enumerate(sc['layers']):
        k = L.get('kind')
        role = L.get('role')
        arch = k == 'image' and str(L.get('label', '')).startswith('archive')
        if k in ('clip', 'action', 'video', 'sfx', 'ensemble') or arch or role in drop_roles or L.get('label') in drop_labels:
            removed.append((len(out), L))
            continue
        out.append(L)
    return sc, out, removed


def place_char(C, sc, layers, removed, cast):
    """-> dict(x, foot, ppc_k, k, index) in stage space for the character entry C of a shot"""
    cam = sc['camera']
    at = C.get('at', {'role': C['who']})
    if 'role' in at:
        hits = [(i, L) for i, L in removed if L.get('role') == at['role'] and L.get('part')]
        if not hits:
            raise ValueError('no %s card in scene %s' % (at['role'], sc['key']))
        idx, L = hits[at.get('n', 0)]
        x, fy = foot_of(L)
    elif 'slot' in at:
        eid, sname = at['slot'].split(':')
        place = next(e for e in sc['ensembles'] if e['id'] == eid)
        _, k, x, fy, pk = slot_pos(load_ensembles()[eid], place, sname, Cam(cam))
        idx = len(layers)
    else:
        x = at['x']
        fy = at['foot_y'] if 'foot_y' in at else Cam(cam).at(at['k'])[0]
        idx = len(layers)
    x += at.get('dx', 0); fy += at.get('dy', 0)
    if C.get('under'):
        idx = next(i for i, L in enumerate(layers) if L.get('label') == C['under'])
    if C.get('over'):
        idx = max(i for i, L in enumerate(layers) if L.get('label') == C['over']) + 1
    k = max(.22, (cam['foot_y'] - cam['horizon_y']) / max(1e-3, fy - cam['horizon_y']))
    ppc = cam['ppc'] / k * at.get('scale', 1.0)
    return {'x': float(x), 'foot': float(fy), 'k': round(k, 3), 'ppc': ppc, 'index': idx}


def camera_track(cam, n):
    """per-frame (z, cx, cy): the framing eases over the shot by `push` (1 = locked off), the anchor point
    (the framed feet) stays put on the screen"""
    out = []
    for f in range(n):
        u = animate.smooth(f / max(1, n - 1))
        z = cam['z'] * (1 + (cam.get('push', 1.0) - 1) * u)
        ax, ay = cam['anchor']
        sx, sy = cam['anchor_out']
        cx = ax - (sx - W / 2) / z + cam.get('pan', 0) * u
        cy = ay - (sy - H / 2) / z
        hw, hh = W / 2 / z, H / 2 / z
        cx = min(max(cx, hw + cam.get('xmin', 0)), cam.get('xmax', W) - hw)
        cy = min(max(cy, hh), H - hh)
        out.append((z, cx, cy))
    return out


def frame_camera(shot, placed, cast):
    C = dict(shot.get('camera', {}))
    fit = C.get('fit') or [c['who'] for c in shot['chars'] if c.get('char')]
    fit = [placed[w] for w in fit if w in placed]
    if 'zoom' in C:
        z = C['zoom']
    elif fit:
        hpx = max(p['height_cm'] * p['ppc'] * p.get('posture', 1.0) for p in fit)
        z = C.get('fill', 0.62) * H / hpx
        if len(fit) > 1:                  # two figures: both must be in the frame with air around them
            span = max(p['x'] for p in fit) - min(p['x'] for p in fit) + 0.7 * hpx
            z = min(z, 0.92 * W / span)
    else:
        z = 1.0
    z = min(max(z, 1.0), C.get('zmax', 3.2))
    if fit:
        ax = C.get('x', sum(p['x'] for p in fit) / len(fit))
        ay = max(p['foot'] for p in fit)
    else:
        ax, ay = C.get('x', W / 2), C.get('y', H * .8)
    sx = W / 2 + C.get('screen_dx', 0) * W
    sy = C.get('foot', 0.88) * H
    return dict(C, z=z, anchor=(ax, ay), anchor_out=(sx, sy))


# ------------------------------------------------------------------ build a poem
def build(plan_path):
    plan = json.load(open(plan_path))
    n = plan['poem']
    tl, scenes = load_poem(n)
    cast = plan['cast']
    shots = []
    for si, sh in enumerate(plan['shots']):
        t0 = when(tl, sh.get('t0'), sh['scene'], 't0')
        t1 = when(tl, sh.get('t1'), sh['scene'], 't1')
        sc, layers, removed = shot_layers(sh, scenes)
        placed, chars = {}, []
        for C in sh.get('chars', []):
            info = cast[C['who']]
            if not info.get('char'):        # TODO: not built yet, never substituted -- a labelled grey box
                try:
                    p = place_char(C, sc, layers, removed, cast)
                except (ValueError, StopIteration, KeyError):
                    continue
                p['height_cm'] = info.get('height_cm', 175)
                chars.append({'who': C['who'], 'char': None, 'todo': info.get('todo', 'not rigged yet'), 'place': p,
                              'torso_px': TORSO_FRAC * p['height_cm'] * p['ppc'], 'keys': [], 'fades': [], 'shadow': False,
                              'posture': C.get('posture', 1.0), 'why': C.get('why', '')})
                continue
            p = place_char(C, sc, layers, removed, cast)
            p['height_cm'] = info.get('height_cm', 175)
            p['posture'] = C.get('posture', 1.0)
            placed[C['who']] = p
            torso_px = info.get('torso_frac', TORSO_FRAC) * p['height_cm'] * p['ppc']
            keys = []
            for K in C['keys']:
                t = when(tl, K.get('t', {'word': K['word'], 'near': K['near']}) if 'word' in K else K['t'])
                kk = dict(K.get('keys', {}))
                kk['no_costume_props'] = not plan.get('costume_props', False)
                keys.append({'t': round(max(0.0, t - t0), 3), 'abs_t': round(t, 3), 'word': K.get('word'), 'target': K['target'],
                             'x': (p['x'] + K.get('dx_cm', 0) * p['ppc']) / W, 'keys': kk, 'why': K.get('why', '')})
            keys.sort(key=lambda k: k['t'])
            fades = sorted([(when(tl, {'word': F['word'], 'near': F['near']}) if 'word' in F else F['t']) - t0, F['op']]
                           for F in C.get('fade', []))
            chars.append({'who': C['who'], 'char': info['char'], 'place': p, 'torso_px': torso_px, 'keys': keys,
                          'fades': fades, 'tint': C.get('tint', sh.get('tint')), 'shadow': C.get('shadow', True),
                          'why': C.get('why', '')})
        cam = frame_camera(sh, placed, cast)
        f0, f1 = int(round(t0 * FPS)), int(round(t1 * FPS))
        shots.append({'i': si, 'scene': sh['scene'], 'set': sc['key'], 't0': t0, 't1': t1, 'f0': f0, 'f1': f1,
                      'layers': layers, 'chars': chars, 'cam': cam, 'why': sh.get('why', ''),
                      'track': camera_track(cam, f1 - f0)})
    # cuts land exactly on the next shot's first frame
    for a, b in zip(shots, shots[1:]):
        a['f1'] = b['f0']; a['track'] = camera_track(a['cam'], a['f1'] - a['f0'])
    return plan, tl, shots


def plan_frames(shot):
    """animate.plan for every character of a shot (shot-local frames)"""
    n = shot['f1'] - shot['f0']
    for c in shot['chars']:
        if not c['char']:
            c['frames'], c['events'], c['solved'] = None, [], []
            continue
        st = animate.Stage(c['char'], (W, H), torso_px=c['torso_px'], floor_px=c['place']['foot'])
        frames, events, solved = animate.plan(c['char'], c['keys'], n / FPS + 1e-6, (W, H), stage=st)
        c['frames'], c['events'] = frames[:n], events
        c['solved'] = [{'t': k['abs_t'], 'word': k['word'], 'target': k['target'], 'why': k['why'], 'rig': s[0]['view'],
                        'mirrored': s[0]['mirror'], 'sources': s[0]['sources'], 'flags': s[0]['flags']}
                       for k, s in zip(c['keys'], solved)]


# ------------------------------------------------------------------ rendering
_SET = {}


def set_groups(shot):
    """split the backdrop at the characters' insertion points; pre-render each group in stage space at the
    shot's largest zoom.  Group 0 is opaque (on the stage black)."""
    key = shot['i']
    if key in _SET:
        return _SET[key]
    S = max(z for z, _, _ in shot['track'])
    S = min(3.0, max(1.0, S))
    cuts = sorted(set(c['place']['index'] for c in shot['chars']))
    bounds = [0] + cuts + [len(shot['layers'])]
    groups = []
    for gi in range(len(bounds) - 1):
        acc = np.zeros((int(H * S), int(W * S), 4), np.float32)
        if gi == 0:
            acc[..., :3] = BG; acc[..., 3] = 255
        for L in shot['layers'][bounds[gi]:bounds[gi + 1]]:
            acc = draw_card(acc, L, S)
        groups.append(np.clip(acc, 0, 255).astype(np.uint8))
    _SET.clear()
    _SET[key] = (S, cuts, groups)
    return _SET[key]


def cam_affine(z, cx, cy, S=1.0, mirror=False):
    """stage px (x S) -> output px"""
    if mirror:
        cx = W - cx
    k = z / S
    return np.array([[k, 0, W / 2 - z * cx], [0, k, H / 2 - z * cy]], np.float64)


def over(dst, src):
    return src + dst * (1 - src[..., 3:] / 255.)


def char_layer(c, f, z, cx, cy):
    """one character at shot frame f through the camera: premultiplied RGBA float (+ its contact shadow)"""
    if not c['char']:
        return todo_box(c, z, cx, cy), None
    fr = c['frames'][f]
    R = posing.rig(c['char'], fr['view'])
    Gs = np.vstack([np.array(fr['G']), [0, 0, 1]])
    Gc = cam_affine(z, cx, cy, mirror=fr['mirror']) @ Gs
    img, J = R.render(fr['P'], Gc, (W, H), ss=2, opts=fr['opts'], lib=posing.parts(c['char']))
    if fr['mirror']:
        img = img[:, ::-1]
    lay = img.astype(np.float32)
    if c.get('tint'):
        lay[..., :3] *= np.array(c['tint'], np.float32)[None, None, ::-1]   # tint is given as RGB
    lay[..., :3] *= lay[..., 3:] / 255.
    op = 1.0
    for t, o in c['fades']:
        if f / FPS >= t:
            op = o
    lay *= op
    sh = None
    if c['shadow'] and op > 0:
        a = lay[..., 3]
        ys = np.nonzero(a.max(1) > 30)[0]
        if len(ys):
            fy = z * (c['place']['foot'] - cy) + H / 2
            row = a[max(0, int(fy) - int(0.05 * c['torso_px'] * z) - 2):int(fy) + 1]
            xs = np.nonzero(row.max(0) > 30)[0] if row.size else []
            if len(xs):
                x0, x1 = xs.min(), xs.max()
                rx = (x1 - x0) / 2 + 0.18 * c['torso_px'] * z
                ry = max(3, 0.07 * c['torso_px'] * z)
                m = np.zeros((H, W), np.float32)
                cv2.ellipse(m, (int((x0 + x1) / 2), int(fy)), (int(rx), int(ry)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
                m = cv2.GaussianBlur(m, (0, 0), max(2, ry * 0.6)) * 0.42 * op
                sh = m
    return lay, sh


def todo_box(c, z, cx, cy):
    """a character not rigged yet: a grey silhouette box at its true size on its floor line, labelled TODO"""
    p = c['place']
    h = p['height_cm'] * p['ppc'] * c.get('posture', 1.0) * z
    w = 0.3 * h
    x = z * (p['x'] - cx) + W / 2
    y1 = z * (p['foot'] - cy) + H / 2
    m = np.zeros((H, W), np.uint8)
    hx, hr = int(x), int(0.075 * h)
    cv2.circle(m, (hx, int(y1 - h + hr)), hr, 255, -1, cv2.LINE_AA)
    cv2.rectangle(m, (int(x - w / 2), int(y1 - h + 2.1 * hr)), (int(x + w / 2), int(y1)), 255, -1)
    t = np.zeros((H, W), np.uint8)
    for i, txt in enumerate(['TODO', c['who'], 'not rigged']):
        cv2.putText(t, txt, (int(x - w / 2) + 4, int(y1 - h / 2) + 22 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 255, 1, cv2.LINE_AA)
    a = m.astype(np.float32) * 0.55 / 255.
    tt = t.astype(np.float32) / 255.
    lay = np.zeros((H, W, 4), np.float32)
    lay[..., :3] = (128 * a * (1 - tt) + 255 * tt)[..., None]          # premultiplied
    lay[..., 3] = 255 * np.maximum(a, tt)
    return lay


def render_frame(args):
    shot, f = args
    z, cx, cy = shot['track'][f]
    S, cuts, groups = set_groups(shot)
    out = None
    for gi, g in enumerate(groups):
        M = cam_affine(z, cx, cy, S)
        warped = cv2.warpAffine(g, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                borderValue=(3, 4, 5, 255) if gi == 0 else 0).astype(np.float32)
        out = warped if out is None else over(out, warped)
        if gi < len(cuts):
            here = [c for c in shot['chars'] if c['place']['index'] == cuts[gi]]
            here.sort(key=lambda c: -c['place']['k'])          # far first
            for c in here:
                lay, sh = char_layer(c, f, z, cx, cy)
                if sh is not None:
                    out[..., :3] *= (1 - sh[..., None])
                out = over(out, lay)
    return np.clip(out[..., :3], 0, 255).astype(np.uint8)


def render_jobs(shots, frames_abs=None):
    jobs = []
    for sh in shots:
        for f in range(sh['f1'] - sh['f0']):
            if frames_abs is None or (sh['f0'] + f) in frames_abs:
                jobs.append((sh['f0'] + f, sh['i'], f))
    return jobs


_SHOTS = None


def _job(a):
    fa, si, f = a
    return fa, render_frame((_SHOTS[si], f))


def _init(shots):
    global _SHOTS
    _SHOTS = shots


def main(plan_path, frames_t=None, out=None, workers=4):
    plan, tl, shots = build(plan_path)
    for sh in shots:
        plan_frames(sh)
    od = os.path.dirname(os.path.abspath(plan_path))
    name = out or plan.get('out', 'poem%s' % plan['poem'])
    import multiprocessing as mp
    if frames_t is not None:
        want = {int(round(t * FPS)) for t in frames_t}
        jobs = render_jobs(shots, want)
        os.makedirs(os.path.join(od, 'check'), exist_ok=True)
        with mp.Pool(workers, initializer=_init, initargs=(shots,)) as pool:
            for fa, img in pool.imap(_job, jobs):
                cv2.imwrite(os.path.join(od, 'check', '%s_%06.2fs.jpg' % (name, fa / FPS)), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return
    n = shots[-1]['f1']
    tmp = os.path.join(od, name + '.noaudio.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', '%dx%d' % (W, H),
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', '-preset', 'medium',
                           '-tune', 'animation', tmp], stdin=subprocess.PIPE)
    cut_frames = {sh['f0'] for sh in shots}
    thumbs = []
    jobs = render_jobs(shots)
    with mp.Pool(workers, initializer=_init, initargs=(shots,)) as pool:
        for fa, img in pool.imap(_job, jobs, chunksize=2):
            ff.stdin.write(img.tobytes())
            if fa % FPS == 0 or fa in cut_frames:
                t = cv2.resize(img, (320, 180), interpolation=cv2.INTER_AREA)
                cv2.putText(t, '%.1fs%s' % (fa / FPS, ' CUT' if fa in cut_frames else ''), (4, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                            (255, 255, 255), 1, cv2.LINE_AA)
                thumbs.append(t)
            if fa % 240 == 0:
                print('frame', fa, '/', n, flush=True)
    ff.stdin.close(); ff.wait()
    audio = os.path.join(STAGE, tl['audio'])
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-i', audio, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k',
                    '-shortest', os.path.join(od, name + '.mp4')], check=True)
    os.remove(tmp)
    per = 12
    rows = [np.hstack(thumbs[i:i + per] + [np.full((180, 320, 3), 255, np.uint8)] * (per - len(thumbs[i:i + per])))
            for i in range(0, len(thumbs), per)]
    cv2.imwrite(os.path.join(od, name + '_strip.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])
    rep = {'poem': plan['poem'], 'title': tl['title'], 'duration': tl['duration'], 'fps': FPS, 'size': [W, H], 'shots': []}
    for sh in shots:
        rep['shots'].append({
            'scene': sh['scene'], 'set': sh['set'], 't0': round(sh['f0'] / FPS, 3), 't1': round(sh['f1'] / FPS, 3), 'why': sh['why'],
            'camera': {'zoom': round(sh['cam']['z'], 3), 'push': sh['cam'].get('push', 1.0), 'anchor': [round(v) for v in sh['cam']['anchor']],
                       'why': sh['cam'].get('why', '')},
            'chars': [{'who': c['who'], 'char': c['char'], 'stage_x': round(c['place']['x']), 'foot_y': round(c['place']['foot']),
                       'depth_k': c['place']['k'], 'px_per_cm': round(c['place']['ppc'], 3),
                       'on_screen_height_px': round(c['place']['height_cm'] * c['place']['ppc'] * sh['cam']['z']),
                       'drawn_after_layer': c['place']['index'], 'keys': c['solved'], 'rig_changes': c['events'], 'why': c['why']}
                      for c in sh['chars']]})
    rep['todo'] = {w: v.get('todo') for w, v in plan['cast'].items() if not v.get('char')}
    json.dump(rep, open(os.path.join(od, name + '.json'), 'w'), indent=1)


if __name__ == '__main__':
    a = sys.argv[1:]
    ft = None; out = None
    if '--frames' in a:
        i = a.index('--frames'); ft = [float(v) for v in a[i + 1].split(',')]; del a[i:i + 2]
    if '--out' in a:
        i = a.index('--out'); out = a[i + 1]; del a[i:i + 2]
    main(a[0], ft, out)
