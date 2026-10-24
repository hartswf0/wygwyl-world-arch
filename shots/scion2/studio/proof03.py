"""Proof 03: the simple swarm method. Whole paintings on an exposure sheet; nothing is bent.

    python3 -m studio.proof03         (run from shots/scion2; writes studio/proof03/)

Shot 1, the couple's spin: one sheet written in views (q3 -> prof -> back3q -> back -> mirrored far
side), resolved per actor from their own dance drawings, played by both dancers side by side; then
recast (positions swapped). Shot 2, the poet acts: walks in, points, recoils, turns to us, opens his
arms, each beat one of his own paintings.
"""
import json, os, shutil, subprocess
import numpy as np, cv2

from studio import exposure as ex, proof as P1
from studio.core import PX_PER_CM

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'proof03')
STAGE = P1.STAGE
F = cv2.FONT_HERSHEY_SIMPLEX


def spin_sheet(cast):
    """intro hold, one slow spin on threes, a held landing, one fast spin on twos, a held end"""
    ring = cast.ring('q3', 1.0, cls='dance')
    sheet = [{'d': ring[0], 'hold': 16, 'name': 'hold'}]
    sheet += [{'d': k, 'hold': 3, 'name': 'spin 1'} for k in ring[1:]] + [{'d': ring[0], 'hold': 14, 'name': 'land'}]
    sheet += [{'d': k, 'hold': 2, 'name': 'spin 2', 'settle': False} for k in ring[1:]] + [{'d': ring[0], 'hold': 20, 'name': 'end'}]
    return sheet


POET = [{'d': 'walk-the-room', 'hold': 36, 'move_cm': 150, 'bob': 5, 'bob_period': 9, 'settle': False, 'name': 'walk in'},
        {'d': 'o06-point-at', 'hold': 22, 'name': 'point'},
        {'d': 'falter-at-shoulder-contact', 'hold': 14, 'move_cm': -12, 'name': 'recoil'},
        {'d': 'wince-standing-still-on-with-the-shoulders-beat-', 'hold': 16, 'name': 'turn to us'},
        {'d': 'welcome-new-day', 'hold': 28, 'name': 'open arms'}]


def encode(d, mp4):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '24', '-i', os.path.join(d, '%04d.jpg'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', mp4], check=True)


def shoot(name, players, labels=None):
    d = os.path.join(OUT, '_f', name); os.makedirs(d)
    n = max(len(p) for p in players)
    recs = [[] for _ in players]
    for f in range(n):
        img = P1.backdrop(False)
        for k, p in enumerate(players):
            recs[k].append(p.draw(img, f))
        if labels:
            for k, p in enumerate(players):
                r = recs[k][-1]
                cv2.putText(img, labels[k], (int(r.get('centre_px', 0)) - 60, 40), F, 0.6, (80, 80, 80), 1, cv2.LINE_AA)
        cv2.imwrite(os.path.join(d, '%04d.jpg' % f), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    encode(d, os.path.join(OUT, name + '.mp4'))
    # strip on twos for viewing and for the critic
    ims = [cv2.imread(os.path.join(d, '%04d.jpg' % f)) for f in range(0, n, 2)]
    th = [cv2.resize(i[160:690], (320, 132)) for i in ims]
    rows = [np.hstack(th[i:i + 6] + [np.full((132, 320, 3), 255, np.uint8)] * (6 - len(th[i:i + 6]))) for i in range(0, len(th), 6)]
    cv2.imwrite(os.path.join(OUT, name + '_strip.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    cv2.imwrite(os.path.join(OUT, name + '.jpg'), ims[len(ims) // 2], [cv2.IMWRITE_JPEG_QUALITY, 88])
    return recs


def checks(recs, travel_beats=('walk in', 'recoil')):
    """per actor: one size (height of standing drawings within a band), floor contact, no jump at a swap"""
    out = {}
    for name, rs in recs.items():
        rs = [r for r in rs if not r.get('gap')]
        lows = [abs(r['low_px'] - STAGE['floor'] - r['dip'] + r['bob']) for r in rs]
        jumps = []
        for a, b in zip(rs, rs[1:]):
            if b['swap'] and b['beat'] not in travel_beats:
                jumps.append(abs(b['centre_px'] - a['centre_px']) / PX_PER_CM)
        sc = [r['scale'] for r in rs]
        out[name] = {'frames': len(rs), 'gaps': sum(1 for r in recs[name] if r.get('gap')),
                     'floor_err_px_max': round(max(lows), 2), 'swap_jump_cm_max': round(max(jumps or [0]), 2),
                     'drawings_used': len({(r['drawing'], r['mirror']) for r in rs}),
                     'scale_spread_pct': round(100 * (max(sc) - min(sc)) / np.median(sc), 1)}
        out[name]['pass'] = out[name]['gaps'] == 0 and out[name]['floor_err_px_max'] < 1.5 and out[name]['swap_jump_cm_max'] < 1.0
    return out


def run():
    shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
    man = ex.Cast('vintage_man__suit', 'suit', 177, 'vintage man')
    woman = ex.Cast('vintage_woman__gown', 'gown', 166, 'vintage woman')
    poet = ex.Cast('poet__red_black_sunglasses', 'track', 183, 'poet')
    res = {'rings': {c.name: c.ring('q3', 1.0, cls='dance') for c in (man, woman)}}
    A = shoot('spin_A', [ex.Player(man, STAGE, 200, spin_sheet(man)), ex.Player(woman, STAGE, 330, spin_sheet(woman))],
              ['vintage man', 'vintage woman'])
    B = shoot('spin_B', [ex.Player(woman, STAGE, 200, spin_sheet(woman)), ex.Player(man, STAGE, 330, spin_sheet(man))],
              ['vintage woman', 'vintage man'])
    C = shoot('poet_beats', [ex.Player(poet, STAGE, 90, POET)])
    res['checks'] = {'spin_A': checks({'vintage man': A[0], 'vintage woman': A[1]}),
                     'spin_B': checks({'vintage woman': B[0], 'vintage man': B[1]}),
                     'poet': checks({'poet': C[0]})}
    # recast: the same beats land on the same frames whoever dances
    beats = lambda rs: [(r['beat'], r['swap']) for r in rs]
    res['recast'] = {'beats_identical': beats(A[0]) == beats(B[1]) == beats(A[1]) == beats(B[0]),
                     'frames': [len(A[0]), len(A[1]), len(B[0]), len(B[1])]}
    res['sheets'] = {'poet': [(b['name'], b['d'], b['hold']) for b in POET], 'spin': [(b['name'], b['d'], b['hold']) for b in spin_sheet(man)]}
    json.dump(res, open(os.path.join(OUT, 'report.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    shutil.rmtree(os.path.join(OUT, '_f'))
    print(json.dumps({k: res[k] for k in ('rings', 'checks', 'recast')}, indent=1))


if __name__ == '__main__':
    run()
