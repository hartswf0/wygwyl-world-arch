"""One page to study the whole arena: every challenge, both characters, stills only.

    python3 shots/arena/puppet/study.py            # all 32, 4 processes
    open shots/arena/puppet/study.html             # (serve the repo)

Per challenge, the authored acting beats (up to 8), on the vignette's own camera,
drawn by cardrig.py with each skin:
  one actor:   a row with the man, a row with the poet
  two or more: a row cast man/poet..., a row with the cast swapped
Writes study/<ACT>__<cast>.jpg and study/study.json.
"""
import json, os, sys
from multiprocessing import Pool
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3d, board, cardrig
from batch import window

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
    rows = []
    for cast in casts(ids):
        R.cast = cast
        ims, faces = [], []
        for f in bf:
            img, nt = R.render(f, window=win)
            ims.append(img)
            faces.append(max([n.get('face_covered', 0) for n in nt] or [0]))
        tag = '-'.join(cast[i] for i in ids)
        path = os.path.join(OUT, f'{act}__{tag}.jpg')
        board.strip(ims, h=300, pad=6).convert('RGB').save(path, quality=82)
        rows.append({'cast': {names[i]: cast[i] for i in ids}, 'file': os.path.basename(path),
                     'face_covered': [round(x, 2) for x in faces]})
    return {'id': act, 'title': ch['title'], 'family': ch['family'], 'situation': ch['situation'],
            'beats': [[f, labels.get(f, '')] for f in bf], 'rows': rows}


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
