"""Data for the Skin Lab: the Crash Lab trials and the card library per bone.

    python3 shots/skinlab/build.py      # -> shots/skinlab/trials.json, shots/skinlab/library.json

trials.json   the Bolas Crash Lab bank (shots/arena/bolas/bank/T*.json: 3D joints in cm, y up, per frame,
              per actor), listed with title, category, length and actors; the page loads a trial on demand.
library.json  every body card that can skin a bone: its slot (torso, head, upper_arm, forearm, hand, thigh,
              shin, foot), side, view, character/costume, true scale (shots/kits/cut/normalized.json, else the
              Body Lab) and two points in card px: A where it attaches to its parent joint and B where its
              child joint sits. Limbs: the two brads farthest apart, A the upper one (cards are drawn hanging);
              torso: A the lower brad (pelvis), B the upper (neck); hand: A the wrist eyelet, B the fingertip;
              foot: A the ankle brad, B the toe end; head: A the neck end, B the crown. Points are guesses
              where a card has fewer brads; the page lets you drag them, and saves the fix.
"""
import glob, json, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)


def trials():
    out = []
    for f in sorted(glob.glob(os.path.join(SHOTS, 'arena', 'bolas', 'bank', 'T*.json'))):
        j = json.load(open(f))
        out.append({'id': j['id'], 'title': j.get('title'), 'cat': j.get('cat'), 'len': j.get('len') or len(j.get('frames', [])),
                    'actors': [a.get('name') for a in j.get('actors', [])], 'note': (j.get('note') or '')[:200],
                    'file': '../arena/bolas/bank/' + os.path.basename(f)})
    return out


def points(path, slot, brads, view):
    im = np.array(Image.open(path).convert('RGBA'))
    a = im[..., 3] > 128
    ys, xs = np.nonzero(a)
    if not len(xs):
        return None, None, 'empty'
    pts = np.stack([xs, ys], 1).astype(float)
    B = [np.array(b, float) for b in brads]
    if slot in ('upper_arm', 'forearm', 'thigh', 'shin', 'torso') and len(B) >= 2:
        i, j = max(((i, j) for i in range(len(B)) for j in range(i + 1, len(B))), key=lambda ij: np.linalg.norm(B[ij[0]] - B[ij[1]]))
        top, bot = sorted([B[i], B[j]], key=lambda p: p[1])
        return (bot, top, 'brads') if slot == 'torso' else (top, bot, 'brads')
    if slot == 'hand' and B:
        A = B[0]
        return A, pts[np.argmax(np.linalg.norm(pts - A, axis=1))], 'eyelet+tip'
    if slot == 'foot':
        A = B[0] if B else np.array([xs.min() + .25 * (xs.max() - xs.min()), ys.min() + .2 * (ys.max() - ys.min())])
        far = pts[np.argmax(np.linalg.norm(pts - A, axis=1))]
        return A, np.array([far[0], ys.max()]) if view not in ('front', 'back') else np.array([A[0], ys.max()]), 'ankle+toe' if B else 'guess'
    if slot == 'head':
        cx = (xs.min() + xs.max()) / 2
        A = max(B, key=lambda p: p[1]) if B else np.array([cx, ys.max()])
        return A, np.array([cx, ys.min()]), 'neck+crown' if B else 'guess'
    # one brad or none: along the long axis
    c = pts.mean(0); u, s, vt = np.linalg.svd(pts[::max(1, len(pts) // 3000)] - c, full_matrices=False)
    d = vt[0] if vt[0][1] > 0 else -vt[0]
    proj = (pts - c) @ d
    top, bot = c + d * proj.min() * .9, c + d * proj.max() * .9
    return ((bot, top) if slot == 'torso' else (top, bot)) + ('axis',)


def library():
    N = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'normalized.json')))['parts']
    cat = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'catalog.json')))['sheets']
    R = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'registry.json')))['parts']
    info = {p['id']: (p, sid) for sid, s in cat.items() for p in s['parts']}
    out = []
    for pid, n in N.items():
        if pid not in info or not n.get('px_per_cm') or R.get(pid, {}).get('q') == 'C':
            continue
        p, sid = info[pid]
        path = os.path.join(SHOTS, 'kits', 'cut', p['file'])
        A, B, how = points(path, n['slot'], p.get('brads') or [], n.get('view'))
        if A is None:
            continue
        w, h = Image.open(path).size
        out.append({'id': pid, 'img': '../kits/cut/' + p['file'], 'w': w, 'h': h, 'slot': n['slot'], 'side': n.get('side'), 'view': n.get('view'),
                    'state': n.get('state'), 'character': n.get('character'), 'costume': n.get('costume'), 'px_per_cm': n['px_per_cm'],
                    'A': [round(float(A[0]), 1), round(float(A[1]), 1)], 'B': [round(float(B[0]), 1), round(float(B[1]), 1)], 'pts': how,
                    'q': R.get(pid, {}).get('q'), 'label': p.get('name') or p.get('label') or ''})
    return out


def main():
    T, L = trials(), library()
    json.dump(T, open(os.path.join(HERE, 'trials.json'), 'w'))
    json.dump(L, open(os.path.join(HERE, 'library.json'), 'w'))
    from collections import Counter
    print(len(T), 'trials;', len(L), 'cards', Counter(c['slot'] for c in L), Counter(c['pts'] for c in L))


if __name__ == '__main__':
    main()
