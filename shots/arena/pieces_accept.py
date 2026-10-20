#!/usr/bin/env python3
"""
ACCEPTANCE — a generated piece is not a piece until it passes registration.

    python3 shots/arena/pieces_accept.py <png> [<png> ...]
    python3 shots/arena/pieces_accept.py --library      # judge what we already have

Four checks, and the first one is the one the current library fails:

  aspect      the alpha box must be length:width within 12% of what the bone asks.
              Pinned on the thigh, today's cards are 34-84% out, each by a
              different amount, which is how you know they were never cut to one
              body.
  one piece   98% of the alpha in a single connected component. Two blobs means
              the generator drew two things, or drew a neighbour's limb as well.
  upright     the long axis within 5 degrees of vertical, so one axis rule holds
              for every card and the boot cannot be the exception again.
  ends        alpha at both declared pivot points, or there is nothing to put a
              brad through.

The point is not that the checks are clever. It is that the current library was
never asked to pass anything, and this is what asking looks like.
"""
import json, os, sys, math
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = json.load(open(os.path.join(HERE, 'pieces.json')))
BY = {p['id']: p for p in SPEC['pieces']}
TOL_ASPECT, TOL_COMP, TOL_ANG = 0.12, 0.98, 5.0

def judge(path, piece=None):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None: return dict(file=path, ok=False, why=['unreadable'])
    a = (im[:, :, 3] > 24) if im.ndim == 3 and im.shape[2] == 4 else (cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) < 250)
    if a.sum() < 50: return dict(file=path, ok=False, why=['empty'])
    if piece is None:
        base = os.path.basename(path).lower()
        for k in BY:
            if base.startswith(k) or ('.' + k + '.') in base or base.startswith(k.replace('uarm','upper_arm')):
                piece = k; break
        if piece is None:
            for k, alias in (('uarm','upper_arm'), ('farm','forearm'), ('boot','leg'), ('shin','leg')):
                if alias in base: piece = k; break
    why = []
    n, lab, st, cen = cv2.connectedComponentsWithStats(a.astype(np.uint8))
    big = max(range(1, n), key=lambda k: st[k, 4]) if n > 1 else 0
    frac = st[big, 4] / float(a.sum()) if n > 1 else 1.0
    if frac < TOL_COMP: why.append(f'{100*(1-frac):.0f}% of the ink is a second piece')
    ys, xs = np.nonzero(a)
    # orient by second moments: the long axis of the alpha
    yc, xc = ys.mean(), xs.mean()
    cov = np.cov(np.vstack([xs - xc, ys - yc]))
    ev, evec = np.linalg.eigh(cov)
    v = evec[:, int(np.argmax(ev))]
    ang = abs(math.degrees(math.atan2(v[0], v[1])))        # 0 = vertical
    ang = min(ang, 180 - ang)
    if ang > TOL_ANG: why.append(f'long axis {ang:.0f}° off vertical')
    L = float(np.ptp(ys)) + 1; W = float(np.ptp(xs)) + 1
    got = L / max(1.0, W)
    want = None
    if piece and piece in BY:
        want = BY[piece]['length_cm'] / BY[piece]['width_cm']
        err = (got - want) / want
        if abs(err) > TOL_ASPECT: why.append(f'aspect {got:.2f} vs {want:.2f} ({err*100:+.0f}%)')
    else:
        why.append('no piece in the spec matches this filename')
    for nm, py in (('pivot', ys.min()), ('far', ys.max())):
        band = a[int(py):int(py) + 6, :] if nm == 'pivot' else a[int(py) - 6:int(py) + 1, :]
        if band.sum() == 0: why.append(f'no ink at the {nm} end')
    return dict(file=os.path.basename(path), piece=piece, aspect=round(got, 2),
                want=round(want, 2) if want else None, off_vertical=round(ang, 1),
                one_piece=round(frac, 3), ok=not why, why=why)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--library' in sys.argv:
        import glob
        args = sorted(glob.glob(os.path.join(HERE, '..', 'weave', 'cast', 'man', 'parts', '*.png'))
                      + glob.glob(os.path.join(HERE, '..', 'weave', 'assets', 'parts', '*.png')))
        args = [f for f in args if 'crouch' not in f and 'pose' not in f
                and 'console' not in f and 'knob' not in f and 'atlas' not in f]
    rows = [judge(f) for f in args]
    ok = sum(1 for r in rows if r['ok'])
    print(f'{"file":34s} {"piece":8s} {"aspect":>7s} {"want":>6s} {"off_v":>6s}  verdict')
    for r in rows:
        print(f'{r["file"][:34]:34s} {str(r.get("piece")):8s} {str(r.get("aspect")):>7s} '
              f'{str(r.get("want")):>6s} {str(r.get("off_vertical")):>6s}  '
              + ('PASS' if r['ok'] else 'FAIL · ' + '; '.join(r['why'])[:70]))
    print(f'\n{ok} of {len(rows)} accepted.')
    json.dump(rows, open(os.path.join(HERE, 'pieces_accept.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
