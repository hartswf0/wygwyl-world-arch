"""The exposure sheet: which drawing is on screen on every frame, and why.

The bank is Bolas's motion on ones: a new pose 24 times a second, smoothly eased.
That is how a 3D rig moves, not how a cut-out does. This Side Up's rule (TSU-00,
the gust test): key the poses, add breakdowns, hold on twos like stop-motion, and
switch to ones only for the fastest moments; never pass off a dissolve or a warp
as an in-between. So:

  K  key         an authored acting beat (beats.json), plus the first and last frame
  B  breakdown   in each key interval, the frame that strays furthest from a straight
                 move between its keys (if it strays more than BREAK_CM): the arc
  1  on ones     a frame whose fastest joint moves more than FAST_CM per frame and is in
                 the take's fastest 8%
  2  on twos     every other frame; the frame after it repeats the drawing
  H  hold        nothing moves more than STILL_CM: the last drawing stays up

Every drawing is a real pose from the bank, never a blend of two.

    xs = xsheet(V, beats)      # list of {f, src, mark}
"""
import numpy as np

FAST_CM = 5.0        # cm per frame: ones need at least this AND the take's top 8% (FAST_PCT)
FAST_PCT = 92
STILL_CM = 0.25      # cm per frame: slower than this holds
BREAK_CM = 6.0       # a breakdown must stray this far from the straight key-to-key move
WATCH = ['wristL', 'wristR', 'ankleL', 'ankleR', 'head', 'pelvis', 'elbowL', 'elbowR', 'kneeL', 'kneeR']
JN = ['pelvis', 'hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR', 'heelL', 'heelR', 'ballL', 'ballR', 'toeL', 'toeR',
      'spineMid', 'neckBase', 'chest', 'shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'wristL', 'wristR', 'headBase', 'head', 'headTop', 'nose']
IDX = [JN.index(k) for k in WATCH]


def joints(V):
    """(frames, actors*watched, 3) array of the watched joints."""
    F = []
    for fr in V['frames']:
        row = []
        for a in fr['a'].values():
            for i in IDX:
                row.append(a['j'][i] or [0, 0, 0])
        F.append(row)
    n = max(len(r) for r in F)
    F = [r + [r[-1]] * (n - len(r)) for r in F]
    return np.array(F, float)


DRIFT_CM = 1.0       # a hold ends once the pose has drifted this far from the drawing on screen


def acting(V):
    """Per frame, what the faces and hands show: a change is a new drawing even when the body
    holds still (critic: T136 is a seated face changing its mind; it was cut to one second)."""
    import p3d
    out = []
    for fr in V['frames']:
        k = []
        for a in fr['a'].values():
            fc = a.get('face') or {}
            k.append((p3d.face_to_expression(fc, a.get('effort', 0)), fc.get('eyes'), fc.get('mouth'),
                      round(float(fc.get('smile') or 0), 1), round(float(fc.get('open') or 0), 1), round(float(fc.get('lid') or 0), 1),
                      round(float(fc.get('gx') or 0), 1), round(float(fc.get('gy') or 0), 1), a['hand']['L'], a['hand']['R']))
        out.append(tuple(k))
    return out


def xsheet(V, beat_frames):
    P = joints(V)
    n = len(P)
    speed = np.zeros(n)
    speed[1:] = np.linalg.norm(P[1:] - P[:-1], axis=2).max(axis=1)
    # ones only for the fastest moments of THIS take (a walk at 3-4 cm/frame stays on
    # twos; at a flat 3.2 cm/frame the whole walk went on ones: critic, xsheet turn 1)
    fast = max(FAST_CM, float(np.percentile(speed, FAST_PCT)))
    keys = sorted({0, n - 1} | {f for f in beat_frames if 0 <= f < n})
    breaks = []
    for a, b in zip(keys, keys[1:]):
        if b - a < 4:
            continue
        t = np.linspace(0, 1, b - a + 1)[:, None, None]
        straight = P[a] * (1 - t) + P[b] * t
        dev = np.linalg.norm(P[a:b + 1] - straight, axis=2).max(axis=1)
        k = int(np.argmax(dev))
        if dev[k] > BREAK_CM and 1 < k < b - a - 1:
            breaks.append(a + k)
    sig = acting(V)
    out = []
    shown = 0
    for f in range(n):
        # how far the pose has drifted since the drawing on screen: a slow drift is still a move
        drift = float(np.linalg.norm(P[f] - P[shown], axis=1).max()) if out else 0.0
        if f in keys:
            mark = 'K'
        elif f in breaks:
            mark = 'B'
        elif out and sig[f] != sig[shown]:
            mark = 'F'               # the face or a hand changes: a new drawing, as a cut-out swaps its card
        elif speed[f] > fast:
            mark = '1'
        elif speed[f] < STILL_CM and out and drift < DRIFT_CM:
            mark = 'H'
        elif f % 2 == 0:
            mark = '2'
        else:
            mark = None              # the second exposure of a drawing on twos
        if mark in ('K', 'B', 'F', '1', '2'):
            shown = f
        out.append({'f': f, 'src': shown, 'mark': mark or '-', 'speed': round(float(speed[f]), 2)})
    return out


def summary(xs):
    marks = [x['mark'] for x in xs]
    drawings = len({x['src'] for x in xs})
    return {'frames': len(xs), 'drawings': drawings, 'keys': marks.count('K'), 'breakdowns': marks.count('B'),
            'faces': marks.count('F'), 'ones': marks.count('1'), 'twos': marks.count('2'), 'held_frames': marks.count('H') + marks.count('-'),
            'saving': round(1 - drawings / max(1, len(xs)), 2)}


def chart(xs, beats, width=1800, title=''):
    """A dope sheet: one column per frame; K/B/ones/twos/holds coloured; speed curve over it."""
    from PIL import Image, ImageDraw, ImageFont
    n = len(xs)
    h = 150
    im = Image.new('RGB', (width, h), (23, 25, 31))
    d = ImageDraw.Draw(im)
    col = {'K': (255, 200, 80), 'B': (120, 200, 255), '1': (240, 110, 90), '2': (110, 120, 135), 'H': (50, 54, 62), '-': (35, 38, 45)}
    w = width / n
    top, bot = 34, 100
    for x in xs:
        x0 = x['f'] * w
        d.rectangle([x0, top, x0 + max(1, w - 0.5), bot], fill=col[x['mark']])
    sp = np.array([x['speed'] for x in xs])
    m = max(sp.max(), FAST_CM * 1.5)
    pts = [(x['f'] * w, bot - (x['speed'] / m) * (bot - top)) for x in xs]
    d.line(pts, fill=(235, 235, 235), width=1)
    fast = max(FAST_CM, float(np.percentile(sp, FAST_PCT)))
    yf = bot - fast / m * (bot - top)
    d.line([(0, yf), (width, yf)], fill=(240, 110, 90), width=1)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    except OSError:
        font = ImageFont.load_default()
    for f, label in beats:
        d.text((f * w + 2, bot + 4), label[:22], fill=(255, 200, 80), font=font)
    s = summary(xs)
    d.text((6, 8), f"{title}   {s['frames']} frames, {s['drawings']} drawings: {s['keys']} keys, {s['breakdowns']} breakdowns, "
                   f"{s['ones']} on ones, {s['twos']} on twos, {s['held_frames']} held      "
                   f"K amber  B blue  ones red  twos grey  white = fastest joint, cm/frame; red line = ones", fill=(220, 220, 220), font=font)
    return im
