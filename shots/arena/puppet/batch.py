"""The whole arena, drawn from 3D, timed on the exposure sheet.

    python3 shots/arena/puppet/batch.py              # all 32 challenges, 4 processes
    python3 shots/arena/puppet/batch.py ACT-010 ACT-016

Per challenge, in out/<ACT>/:
  take.mp4      the take as the X-sheet exposes it (keys, breakdowns, twos, ones, holds)
  keys.png      the authored acting beats only, no captions: the cold read
  xsheet.png    the dope sheet: which frames are new drawings and why
  take.json     X-sheet, summary, face checks per beat, the suggested camera
and out/arena.json, which gallery.html reads.

Face check: on every drawing, the share of the drawn head that ends up covered by
whatever is painted after it (a shoulder, an arm, a box, another actor), or the
head seen from behind. Where the authored camera hides a face on a beat, the
batch tries the camera around the vertical axis and suggests the yaw that shows
the most face over all the beats.
"""
import json, math, os, subprocess, sys
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3d, xsheet, board

OUT = os.path.join(HERE, 'out')
SPEC = json.load(open(os.path.join(p3d.ARENA, 'spec', 'acting_arena_v0.2.json')))
BEATS = json.load(open(os.path.join(p3d.ARENA, 'bolas', 'bank', 'beats.json')))
H_OUT = 540


def window(P, cam):
    pts = []
    for fr in P.V['frames'][::3]:
        for a in fr['a'].values():
            for q in a['j']:
                if q is not None:
                    pts.append(cam.P(q)[:2])
        for q in fr.get('p', {}).values():
            if q.get('pos') and q.get('size'):
                sz = q['size'] if isinstance(q['size'], list) else [q['size']]
                sx, sy = sz[0], sz[1] if len(sz) > 1 else sz[0]     # a ball's size is one number
                for dx in (-.5, .5):
                    for dy in (-.5, .5):
                        pts.append(cam.P([q['pos'][0] + dx * sx, q['pos'][1] + dy * sy, q['pos'][2]])[:2])
    pts = np.array(pts)
    m = 34 * cam.s
    x0, y0 = pts.min(0) - m
    x1, y1 = pts.max(0) + m
    y1 = max(y1, cam.P([cam.c[0], 0, cam.c[2]])[1] + 12 * cam.s)
    w, h = x1 - x0, y1 - y0
    # keep frames at least 4:3 so a turn does not get clipped, and even-sized for the encoder
    if w < h * 0.75:
        cx = (x0 + x1) / 2
        x0, x1 = cx - h * 0.375, cx + h * 0.375
    return (int(x0), int(y0), int(x0) + 2 * int((x1 - x0) / 2), int(y0) + 2 * int((y1 - y0) / 2))


def face_score(notes):
    """0 = every face fully visible; 1 = covered or seen from behind."""
    s = []
    for n in notes:
        if 'back' in n.get('head', ''):
            s.append(1.0)
        else:
            s.append(min(1.0, n.get('face_covered', 0.0)))
    return float(np.mean(s)) if s else 0.0


def run(act):
    P = p3d.Puppet(act)
    out = os.path.join(OUT, act)
    os.makedirs(out, exist_ok=True)
    ch = next(c for c in SPEC['challenges'] if c['id'] == act)
    bf = board.beats(P.tid)
    labels = [(b['f'], b['beat']) for b in BEATS.get(P.tid, []) if b['f'] in bf]
    xs = xsheet.xsheet(P.V, bf)
    keyframes = [x['f'] for x in xs if x['mark'] == 'K']

    # camera: the authored one, unless it hides faces on the beats; then search yaw
    base = P.V['view'].get('yaw', -22)
    cam = p3d.Camera(P.V['view'])
    win = window(P, cam)
    beat_notes = {}
    for f in keyframes:
        _, nt = P.render(f, window=win)
        beat_notes[f] = nt
    authored = float(np.mean([face_score(n) for n in beat_notes.values()]))
    yaw_used, tried = None, {}
    if authored > 0.08:
        for dy in (-60, -30, 30, 60, 90, -90):
            c2 = p3d.Camera(P.V['view'], yaw=base + dy)
            w2 = window(P, c2)
            sc = float(np.mean([face_score(P.render(f, yaw=base + dy, window=w2)[1]) for f in keyframes]))
            tried[base + dy] = round(sc, 3)
        best = min(tried, key=tried.get)
        if tried[best] < authored - 0.05:
            yaw_used = best
    if yaw_used is not None:
        cam = p3d.Camera(P.V['view'], yaw=yaw_used)
        win = window(P, cam)

    # render every drawing once, expose it as the X-sheet says
    W, H = win[2] - win[0], win[3] - win[1]
    k = H_OUT / H
    ow, oh = 2 * int(W * k / 2), H_OUT
    cache, faces = {}, {}
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{ow}x{oh}',
                           '-r', '24', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '26', '-preset', 'veryfast',
                           os.path.join(out, 'take.mp4')], stdin=subprocess.PIPE)
    for x in xs:
        s = x['src']
        if s not in cache:
            cache.clear() if len(cache) > 3 else None
            img, nt = P.render(s, yaw=yaw_used, window=win)
            cache[s] = img.resize((ow, oh))
            faces[s] = nt
        ff.stdin.write(cache[s].tobytes())
    ff.stdin.close()
    ff.wait()

    # the cold-read sheet and the dope sheet
    ims = [P.render(f, yaw=yaw_used, window=win)[0] for f in bf if f < len(P.V['frames'])]
    if ims:
        board.strip(ims, h=420).save(os.path.join(out, 'keys.png'))
    xsheet.chart(xs, labels, title=act).save(os.path.join(out, 'xsheet.png'))

    covered = {s: [(n['actor'], n.get('face_covered', 0), n.get('head', '')) for n in nt] for s, nt in faces.items()}
    hidden = sorted(s for s, nt in faces.items() if any(n.get('face_hidden_by') for n in nt))
    rec = {'id': act, 'tid': P.tid, 'title': ch['title'], 'family': ch['family'], 'situation': ch['situation'],
           'success': ch.get('success_observation'), 'cast': [a['name'] for a in P.V['actors']],
           'beats': labels, 'xsheet_summary': xsheet.summary(xs),
           'camera': {'authored_yaw': base, 'used_yaw': yaw_used if yaw_used is not None else base,
                      'authored_face_score': round(authored, 3), 'tried': tried},
           'face_hidden_drawings': hidden, 'face_hidden_share': round(len(hidden) / max(1, len(faces)), 3),
           'beat_heads': {f: [n.get('head', '') + ' / ' + n.get('expression', '') for n in nt] for f, nt in beat_notes.items()}}
    json.dump(dict(rec, xsheet=xs, faces=covered), open(os.path.join(out, 'take.json'), 'w'), default=float)
    return rec


def main(acts):
    with Pool(4) as pool:
        recs = pool.map(run, acts)
    path = os.path.join(OUT, 'arena.json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update({r['id']: r for r in recs})
    json.dump(dict(sorted(old.items())), open(path, 'w'), indent=1, default=float)
    for r in recs:
        s = r['xsheet_summary']
        print(f"{r['id']} {r['title'][:28]:28s} {s['drawings']:4d}/{s['frames']:<4d} drawings  K{s['keys']} B{s['breakdowns']} "
              f"ones {s['ones']}  face hidden {r['face_hidden_share']:.0%}  yaw {r['camera']['authored_yaw']}->{r['camera']['used_yaw']}")


if __name__ == '__main__':
    acts = sys.argv[1:] or [c['id'] for c in SPEC['challenges']]
    main(acts)
