"""One page to study the whole arena: every challenge, both characters, stills only.

    python3 shots/arena/puppet/study.py            # all 32, 4 processes
    open shots/arena/puppet/study.html             # (serve the repo)

Per challenge, the authored acting beats (up to 8), on the vignette's own camera,
drawn by cardrig.py with each skin:
  one actor:   a row with the man, a row with the poet
  two or more: a row cast man/poet..., a row with the cast swapped
Writes study/<ACT>__<cast>.jpg (key beats), .mp4 (the take, timed on the
exposure sheet from xsheet.py), .poster.jpg, and study/study.json.
"""
import json, os, sys
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import subprocess
import p3d, board, cardrig, xsheet
from batch import window

VIDEO_H = 360

OUT = os.path.join(HERE, 'study')
SPEC = json.load(open(os.path.join(p3d.ARENA, 'spec', 'acting_arena_v0.2.json')))
BEATS = json.load(open(os.path.join(p3d.ARENA, 'bolas', 'bank', 'beats.json')))


def casts(ids):
    if len(ids) == 1:
        return [{ids[0]: 'man'}, {ids[0]: 'poet'}]
    a = {aid: ('man', 'poet')[i % 2] for i, aid in enumerate(ids)}
    b = {aid: ('poet', 'man')[i % 2] for i, aid in enumerate(ids)}
    return [a, b]


def run(act):
    R = cardrig.CardRig(act)
    ch = next(c for c in SPEC['challenges'] if c['id'] == act)
    bf = [f for f in board.beats(R.tid) if f < len(R.V['frames'])]
    if len(bf) > 8:
        bf = [bf[int(round(i))] for i in np.linspace(0, len(bf) - 1, 8)]
    if not bf:
        bf = [0, len(R.V['frames']) // 2, len(R.V['frames']) - 1]
    labels = {b['f']: b['beat'] for b in BEATS.get(R.tid, [])}
    cam = p3d.Camera(R.V['view'])
    win = window(R, cam)
    ids = [a['id'] for a in R.V['actors']]
    names = {a['id']: a['name'] for a in R.V['actors']}
    xs = xsheet.xsheet(R.V, board.beats(R.tid))
    rows = []
    for cast in casts(ids):
        R.cast = cast
        ims, faces = [], []
        for f in bf:
            img, nt = R.render(f, window=win)
            ims.append(img)
            faces.append(max([n.get('face_covered', 0) for n in nt] or [0]))
        tag = '-'.join(cast[i] for i in ids)
        video(R, win, xs, os.path.join(OUT, f'{act}__{tag}'))
        path = os.path.join(OUT, f'{act}__{tag}.jpg')
        board.strip(ims, h=300, pad=6).convert('RGB').save(path, quality=82)
        rows.append({'cast': {names[i]: cast[i] for i in ids}, 'file': os.path.basename(path),
                     'video': f'{act}__{tag}.mp4', 'poster': f'{act}__{tag}.poster.jpg',
                     'face_covered': [round(x, 2) for x in faces]})
    return {'id': act, 'title': ch['title'], 'xsheet': xsheet.summary(xs), 'family': ch['family'], 'situation': ch['situation'],
            'beats': [[f, labels.get(f, '')] for f in bf], 'rows': rows}


def video(R, win, xs, stem):
    """The take as the exposure sheet shows it: each drawing rendered once, held as long
    as the sheet says (keys, breakdowns, twos, ones for the fastest moments)."""
    W, H = win[2] - win[0], win[3] - win[1]
    oh = VIDEO_H
    ow = 2 * int(W * oh / H / 2)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{ow}x{oh}',
                           '-r', '24', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '27', '-preset', 'veryfast',
                           '-movflags', '+faststart', stem + '.mp4'], stdin=subprocess.PIPE)
    last, frame = None, None
    for n, x in enumerate(xs):
        if x['src'] != last:
            frame = R.render(x['src'], window=win)[0].resize((ow, oh))
            last = x['src']
            if n == 0:
                frame.save(stem + '.poster.jpg', quality=80)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    ff.wait()


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    acts = sys.argv[1:] or [c['id'] for c in SPEC['challenges']]
    with Pool(4) as p:
        recs = p.map(run, acts)
    path = os.path.join(OUT, 'study.json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update({r['id']: r for r in recs})
    json.dump(dict(sorted(old.items())), open(path, 'w'), indent=1)
    print(len(old), 'challenges in', path)
