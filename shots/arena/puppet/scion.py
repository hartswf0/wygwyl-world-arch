"""SCION, states 1 and 2 and the gates, for the Cineosis batch (T133-T182).

    python3 shots/arena/puppet/scion.py              # all 50, 4 processes
    python3 shots/arena/puppet/scion.py T140 T150

Per vignette, in scion/:
  T###.json         the report: beat chain, three stagings and their scores, X-sheet
                    summary, gates 1-5 with pass/fail
  T###.mp4          the take, 720p, timed on the exposure sheet, dead holds trimmed
  T###.jpg          the key beats on the chosen staging
  T###.stage.jpg    the three stagings tried, on the middle beat

State 1, the dramatic beats: the vignette's note is the situation; its authored
beats (beats.json, walk texture filtered) are the chain. Each beat names who drives
it (the actor moving most around that frame) and what it answers (the beat before).

State 2, staging and timing: three cameras (the authored one, and swung 40 degrees
either way about the vertical) are scored on what the gates measure: faces seen,
actors kept apart, the action filling the frame. The best one is shot. The take is
the X-sheet (xsheet.py) with the tail trimmed to the last movement and long holds
cut to one second: a held pose reads in a second and dies after three.

Gates:
  1 silhouette  actors' silhouettes do not merge (overlap of their bone masks)
  2 volume      cards are rarely squashed to the minimum (a bone end-on to camera)
  3 contact     planted feet do not slide (cm per frame, after retargeting)
  4 arcs        each key interval that bends has a breakdown on its arc
  5 vitality    no hold on screen longer than HOLD_MAX frames; faces readable on the beats
"""
import json, math, os, subprocess, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3d, board, cardrig, xsheet
from batch import window, face_score

OUT = os.path.join(HERE, 'scion')
BEATS = json.load(open(os.path.join(p3d.ARENA, 'bolas', 'bank', 'beats.json')))
VIDEO_H = 720
HOLD_MAX = 24        # frames a held drawing may stay on screen
TAIL = 18            # frames after the last beat or movement
MIN_FRAMES = 96      # no take shorter than four seconds
SWING = 40           # degrees each way for the alternative stagings
BONES = [('hipL', 'kneeL'), ('kneeL', 'ankleL'), ('hipR', 'kneeR'), ('kneeR', 'ankleR'), ('pelvis', 'neckBase'),
         ('shoulderL', 'elbowL'), ('elbowL', 'wristL'), ('shoulderR', 'elbowR'), ('elbowR', 'wristR'), ('neckBase', 'head')]
WIDTH = {'pelvis': 30, 'hipL': 14, 'hipR': 14, 'kneeL': 11, 'kneeR': 11, 'shoulderL': 10, 'shoulderR': 10,
         'elbowL': 8, 'elbowR': 8, 'neckBase': 20}


# ---------------------------------------------------------------- state 1
def beat_chain(R):
    labels = {b['f']: b['beat'] for b in BEATS.get(R.tid, [])}
    n = len(R.V['frames'])
    fs = [f for f in board.beats(R.tid) if f < n] or [0, n // 2, n - 1]
    names = {a['id']: a['name'] for a in R.V['actors']}
    chain, prev = [], None
    for f in fs:
        best, who = -1, None
        for aid in R.V['frames'][f]['a']:
            d = 0.0
            for g in range(max(0, f - 6), min(n - 1, f + 6)):
                a, b = R.V['frames'][g]['a'].get(aid), R.V['frames'][g + 1]['a'].get(aid)
                if a and b:
                    d += sum(np.linalg.norm(np.subtract(p, q)) for p, q in zip(a['j'], b['j']) if p and q)
            if d > best:
                best, who = d, aid
        lab = labels.get(f, '')
        chain.append({'f': f, 'beat': lab, 'driver': names.get(who, who), 'answers': prev})
        prev = lab or prev
    return chain


# ---------------------------------------------------------------- measures
def actor_joints(R, f):
    out = {}
    for aid, a in R.actors(f):
        b, _ = R.retarget(dict(a, _id=aid), R.cast.get(aid, 'man'))
        out[aid] = {k: np.array(b['j'][i], float) for k, i in p3d.J.items() if b['j'][i] is not None}
    return out


def masks(R, cam, f, win, scale=0.25):
    """Each actor as thick bones, a cheap silhouette at a quarter of the window."""
    W, H = int((win[2] - win[0]) * scale), int((win[3] - win[1]) * scale)
    out = {}
    for aid, J in actor_joints(R, f).items():
        im = Image.new('L', (W, H))
        d = ImageDraw.Draw(im)
        for a, b in BONES:
            if a in J and b in J:
                pa, pb = cam.P(J[a])[:2], cam.P(J[b])[:2]
                pa = ((pa[0] - win[0]) * scale, (pa[1] - win[1]) * scale)
                pb = ((pb[0] - win[0]) * scale, (pb[1] - win[1]) * scale)
                d.line([pa, pb], fill=255, width=max(1, int(WIDTH.get(a, 9) * cam.s * scale)))
        if 'head' in J:
            c = cam.P(J['head'])[:2]
            r = 11 * cam.s * scale
            c = ((c[0] - win[0]) * scale, (c[1] - win[1]) * scale)
            d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
        out[aid] = np.asarray(im) > 0
    return out


def overlap(M):
    """Worst share of one actor's silhouette covered by another's (0 apart, 1 merged)."""
    ids, worst = list(M), 0.0
    for i in range(len(ids)):
        for k in range(i + 1, len(ids)):
            a, b = M[ids[i]], M[ids[k]]
            m = min(a.sum(), b.sum())
            if m:
                worst = max(worst, float((a & b).sum() / m))
    return worst


def squashed(R, cam, f):
    """Share of limb bones seen end-on: their card would be squashed to the minimum."""
    n = s = 0
    for J in actor_joints(R, f).values():
        for a, b in BONES[:4] + BONES[5:9]:
            if a in J and b in J:
                L = np.linalg.norm(J[b] - J[a])
                if L > 1:
                    n += 1
                    s += np.linalg.norm(cam.P(J[b])[:2] - cam.P(J[a])[:2]) / (cam.s * L) < cardrig.SQUASH_MIN
    return s / max(1, n)


def foot_slide(R, f0, f1):
    """Planted feet: the ball of the foot on the floor (under 4cm) in two frames running.
    Returns the 95th percentile and the worst slide, cm per frame, after retargeting."""
    sl, prev = [], None
    for f in range(f0, f1 + 1):
        cur = actor_joints(R, f)
        if prev:
            for aid, J in cur.items():
                P = prev.get(aid)
                if not P:
                    continue
                for s in 'LR':
                    k = 'ball' + s
                    if k in J and k in P and J[k][1] < 4 and P[k][1] < 4:
                        sl.append(float(np.hypot(*(J[k] - P[k])[[0, 2]])))
        prev = cur
    if not sl:
        return 0.0, 0.0
    return round(float(np.percentile(sl, 95)), 2), round(max(sl), 2)


# ---------------------------------------------------------------- state 2
def stagings(R, keys):
    v = R.V['view']
    out = []
    for name, dy in (('authored', 0), ('swing left', -SWING), ('swing right', SWING)):
        cam = p3d.Camera(v, yaw=v.get('yaw', 0) + dy)
        win = window(R, cam)
        faces, over, fill = [], [], []
        for f in keys:
            _, nt = R.render(f, window=win, props=False, floor=False) if len(R.V['actors']) <= 4 else (None, [])
            faces.append(face_score(nt))
            M = masks(R, cam, f, win)
            over.append(overlap(M))
            fill.append(sum(m.mean() for m in M.values()))
        sc = {'face': round(float(np.mean(faces)), 3), 'overlap': round(float(np.mean(over)), 3),
              'fill': round(float(np.mean(fill)), 3)}
        sc['score'] = round(0.5 * sc['face'] + 0.4 * sc['overlap'] + 0.1 * (1 - min(1, sc['fill'] / 0.25))
                            - (0.03 if dy == 0 else 0), 3)
        out.append({'name': name, 'yaw': round(v.get('yaw', 0) + dy, 1), 'cam': cam, 'win': win, **sc})
    return out


def trimmed(V, beat_frames):
    """The X-sheet, cut to the action: start a second before the first movement, end TAIL
    frames after the last beat or movement, and cut every hold to HOLD_MAX frames."""
    xs = xsheet.xsheet(V, beat_frames)
    sp = np.array([x['speed'] for x in xs])
    moving = np.nonzero(sp > xsheet.STILL_CM * 4)[0]
    n = len(xs)
    if len(moving):
        start = max(0, int(moving[0]) - 24)
        end = min(n - 1, max(max(beat_frames or [0]) + TAIL, int(moving[-1]) + TAIL))
    else:
        start, end = 0, n - 1
    out, run = [], 0
    for x in xs[start:end + 1]:
        run = run + 1 if out and x['src'] == out[-1]['src'] else 0
        if run < HOLD_MAX or x['mark'] == 'K':
            out.append(x)
    if len(out) < MIN_FRAMES:
        # a near-still vignette (a face, a held breath) keeps its length: cutting every hold
        # left T136 one second long (critic)
        out = xs[start:end + 1]
    return out


# ---------------------------------------------------------------- the take
def video(R, cam, win, xs, stem):
    W, H = win[2] - win[0], win[3] - win[1]
    oh = VIDEO_H
    ow = 2 * int(W * oh / H / 2)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{ow}x{oh}',
                           '-r', '24', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-preset', 'veryfast',
                           '-movflags', '+faststart', stem + '.mp4'], stdin=subprocess.PIPE)
    last, frame, faces = None, None, []
    for n, x in enumerate(xs):
        if x['src'] != last:
            img, nt = R.render(x['src'], yaw=cam.yaw_deg, window=win)
            frame = img.convert('RGB').resize((ow, oh), Image.LANCZOS)
            last = x['src']
            if n == 0:
                frame.save(stem + '.poster.jpg', quality=82)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    ff.wait()


def run(tid):
    R = cardrig.CardRig(tid)
    V = R.V
    chain = beat_chain(R)
    keys = [b['f'] for b in chain]
    show = keys if len(keys) <= 8 else [keys[int(round(i))] for i in np.linspace(0, len(keys) - 1, 8)]
    S = stagings(R, show)
    best = min(S, key=lambda s: s['score'])
    cam, win = best['cam'], best['win']
    cam.yaw_deg = best['yaw']
    # the chosen staging on every beat
    ims, faces, over, sq = [], [], [], []
    for f in show:
        img, nt = R.render(f, yaw=best['yaw'], window=win)
        ims.append(img)
        faces.append(face_score(nt))
        over.append(overlap(masks(R, cam, f, win)))
        sq.append(squashed(R, cam, f))
    board.strip(ims, h=360, pad=6).convert('RGB').save(os.path.join(OUT, tid + '.jpg'), quality=84)
    mid = show[len(show) // 2]
    trip = [R.render(mid, yaw=s['yaw'], window=s['win'])[0] for s in S]
    board.strip(trip, h=300, pad=6, labels=[f"{s['name']} {s['score']:.2f}" for s in S]).convert('RGB').save(
        os.path.join(OUT, tid + '.stage.jpg'), quality=80)
    xs = trimmed(V, keys)
    video(R, cam, win, xs, os.path.join(OUT, tid))
    f0, f1 = xs[0]['f'], xs[-1]['f']
    slide95, slide_max = foot_slide(R, f0, f1)
    xsum = xsheet.summary(xs)
    runs, r = [], 0
    for a, b in zip(xs, xs[1:]):
        r = r + 1 if a['src'] == b['src'] else 0
        runs.append(r)
    bends = sum(1 for a, b in zip(keys, keys[1:]) if b - a >= 8)
    multi = len(V['actors']) > 1
    gates = {
        'G1 silhouette': {'worst_overlap': round(max(over), 2), 'pass': (not multi) or max(over) < 0.35},
        'G2 volume': {'squashed_share': round(float(np.mean(sq)), 3), 'pass': float(np.mean(sq)) < 0.15},
        'G3 contact': {'slide_p95_cm': slide95, 'slide_max_cm': slide_max, 'pass': slide95 < 1.0},
        'G4 arcs': {'breakdowns': xsum['breakdowns'], 'key_intervals': bends, 'pass': xsum['breakdowns'] >= min(bends, 1) or bends == 0},
        'G5 vitality': {'longest_hold': (max(runs) + 1) if runs else 0, 'face_unread': round(float(np.mean(faces)), 2),
                        'pass': ((max(runs) + 1) if runs else 0) <= HOLD_MAX + 1 and float(np.mean(faces)) < 0.5},
    }
    names = {a['id']: a['name'] for a in V['actors']}
    rec = {'id': tid, 'title': V.get('title', tid), 'situation': V.get('note', ''),
           'cast': {names[a]: s for a, s in R.cast.items()}, 'chain': chain, 'shown': show,
           'stagings': [{k: v for k, v in s.items() if k not in ('cam', 'win')} for s in S], 'chosen': best['name'],
           'xsheet': xsum, 'span': [f0, f1, len(V['frames'])], 'gates': gates,
           'passed': sum(g['pass'] for g in gates.values()),
           'video': tid + '.mp4', 'poster': tid + '.poster.jpg', 'strip': tid + '.jpg', 'stage': tid + '.stage.jpg'}
    json.dump(rec, open(os.path.join(OUT, tid + '.json'), 'w'), indent=1)
    print(tid, best['name'], rec['passed'], '/5', flush=True)
    return rec


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    ids = sys.argv[1:] or [f'T{n}' for n in range(133, 183)]
    with Pool(4) as p:
        recs = p.map(run, ids, chunksize=1)
    path = os.path.join(OUT, 'scion.json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update({r['id']: r for r in recs})
    json.dump(dict(sorted(old.items())), open(path, 'w'), indent=1)
    print(len(old), 'vignettes in', path)
