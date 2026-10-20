"""Look at the cards before trusting where the compiler pins them.

    python3 shots/arena/critic/cards.py            -> critic/out/cards_man.png + cards_man.json

Every card the man's rig is assembled from, on grey, with the pivot (green) and
far socket (red) that `draw_man()` in bolas/compile_vignette.py hard-codes for it.
The numbers are copied from that function; if they change there, change PINS.

Yellow rings are the brads drawn on the card, read by brads.py.

Checks per card, all on the card's own pixels:
  on_ink      - is the pivot / socket on an opaque pixel? A hinge in the air is a
                joint that cannot look joined however well the skeleton is solved.
  ink_span    - where the ink starts and ends along the card's long axis, as a
                fraction of the card. A pivot at 0.70 means 30% of the card hangs
                past the joint.
  stale       - the pin is outside the card, or the card's size differs from the
                size the pins were written for (cast.json `size`).
"""
import json, math, os, sys
import numpy as np
import brads
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'out')

# (image id, file, pivot, socket-or-None, what the pivot is)  -- from draw_man()
PINS = [
    ('man.uarm', 'weave/cast/man/parts/proc.uarm.png', (39, 10), (39, 158), 'shoulder -> elbow'),
    ('man.farm', 'weave/cast/man/parts/proc.farm.png', (35, 10), (35, 148), 'elbow -> wrist'),
    ('man.thigh', 'weave/cast/man/parts/proc.thigh.png', (52, 10), (52, 244), 'hip -> knee'),
    ('man.shin', 'weave/cast/man/parts/proc.shin.png', (43, 10), (43, 238), 'knee -> ankle'),
    ('man.hand.open', 'weave/cast/man/parts/hand.profile.open.png', (25, 46), None, 'wrist'),
    ('man.hand.grip', 'weave/cast/man/parts/hand.grip.png', (25, 46), None, 'wrist'),
    ('man.hand.fist', 'weave/cast/man/parts/hand.fist.png', (25, 46), None, 'wrist'),
    ('man.hand.point', 'weave/cast/man/parts/hand.point.png', (25, 46), None, 'wrist'),
    ('man.boot.flat', 'weave/cast/man/parts/boot.flat.png', (66, 35), None, 'ankle'),
    ('man.boot.toe', 'weave/cast/man/parts/boot.toe.png', (66, 35), None, 'ankle'),
    ('man.pelvis.profile', 'weave/cast/man/parts/pelvis.profile.png', (118, 25), None, 'pelvis'),
    ('man.pelvis.front', 'weave/cast/man/parts/pelvis.front.png', (118, 25), None, 'pelvis'),
    ('man.torso.profile', 'weave/cast/man/parts/torso.profile.png', (110, 308), None, 'pelvis (hip)'),
    ('man.torso.front', 'weave/cast/man/parts/torso.front.png', (110, 308), None, 'pelvis (hip)'),
    ('man.head.profile_R', 'weave/cast/man/parts/head.profile_R.png', (107, 257), None, 'neck'),
    ('man.head.front', 'weave/cast/man/parts/head.front.png', (107, 257), None, 'neck'),
    ('man.head.threequarter_R', 'weave/cast/man/parts/head.threequarter_R.png', (107, 257), None, 'neck'),
    ('man.head.profile_L', 'weave/cast/man/parts/head.profile_L.png', (107, 257), None, 'neck'),
]


def alpha(path):
    im = Image.open(os.path.join(SHOTS, path)).convert('RGBA')
    return im, np.asarray(im)[:, :, 3] > 40


def on_ink(a, p, r=3):
    x, y = int(round(p[0])), int(round(p[1]))
    h, w = a.shape
    if not (0 <= x < w and 0 <= y < h):
        return False
    return bool(a[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1].any())


def inspect():
    cast = json.load(open(os.path.join(SHOTS, 'weave/cast/man/cast.json')))['parts']
    rows = []
    for pid, path, piv, sock, what in PINS:
        im, a = alpha(path)
        h, w = a.shape
        ys = np.where(a.any(1))[0]
        xs = np.where(a.any(0))[0]
        row = {'id': pid, 'file': path, 'size': [w, h], 'pins_for': what,
               'pivot': list(piv), 'pivot_on_ink': on_ink(a, piv),
               'ink_y': [round(float(ys[0]) / h, 2), round(float(ys[-1]) / h, 2)],
               'ink_x': [round(float(xs[0]) / w, 2), round(float(xs[-1]) / w, 2)],
               'pivot_frac': [round(piv[0] / w, 2), round(piv[1] / h, 2)]}
        if sock:
            row['socket'] = list(sock)
            row['socket_on_ink'] = on_ink(a, sock)
            # Share of the card's height that lies outside pivot..socket: drawn limb
            # that will hang past the joint once the card is placed bone to bone.
            row['overhang_px'] = [int(piv[1] - ys[0]), int(ys[-1] - sock[1])]
        row['drawn_brads'] = [b[:2] for b in brads.brads(os.path.join(SHOTS, path))[2]]
        if row['drawn_brads']:
            row['pivot_to_nearest_drawn_brad_px'] = round(min(math.dist(piv, b) for b in row['drawn_brads']), 1)
        stem = os.path.basename(path)[:-4]
        if stem in cast and cast[stem]['size'] != [w, h]:
            row['stale_vs_cast_json'] = {'cast.json size': cast[stem]['size'], 'file size': [w, h]}
        row['pin_outside_card'] = not (0 <= piv[0] < w and 0 <= piv[1] < h)
        faults = []
        if not row['pivot_on_ink']:
            faults.append('pivot in the air')
        if sock and not row['socket_on_ink']:
            faults.append('socket in the air')
        if row['pin_outside_card']:
            faults.append('pivot outside the card')
        if abs(row['pivot_frac'][0] - (row['ink_x'][0] + row['ink_x'][1]) / 2) > 0.15 and 'hand' not in pid and 'boot' not in pid:
            faults.append('pivot off the card centreline')
        if row.get('pivot_to_nearest_drawn_brad_px', 0) > 8:
            faults.append(f"pin misses the drawn brad by {row['pivot_to_nearest_drawn_brad_px']:.0f}px")
        if 'stale_vs_cast_json' in row:
            faults.append('card replaced since its pins were written')
        row['faults'] = faults
        rows.append((row, im))
    return rows


def sheet(rows, out):
    cell = 300
    cols = 6
    n = len(rows)
    W = cols * cell
    H = ((n + cols - 1) // cols) * (cell + 40)
    S = Image.new('RGB', (W, H), (128, 128, 128))
    d = ImageDraw.Draw(S)
    for i, (row, im) in enumerate(rows):
        cx, cy = (i % cols) * cell, (i // cols) * (cell + 40)
        w, h = im.size
        k = min((cell - 40) / w, (cell - 40) / h)
        t = im.resize((max(1, int(w * k)), max(1, int(h * k))))
        ox, oy = cx + (cell - t.size[0]) // 2, cy + 20 + (cell - 40 - t.size[1]) // 2
        d.rectangle([ox, oy, ox + t.size[0], oy + t.size[1]], outline=(90, 90, 90))
        S.paste(t, (ox, oy), t)

        def dot(p, col):
            x, y = ox + p[0] * k, oy + p[1] * k
            d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=col, width=3)
            d.line([x - 9, y, x + 9, y], fill=col)
            d.line([x, y - 9, x, y + 9], fill=col)
        for b in row.get('drawn_brads', []):
            x, y = ox + b[0] * k, oy + b[1] * k
            d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(255, 210, 0), width=2)
        dot(row['pivot'], (0, 255, 0))
        if 'socket' in row:
            dot(row['socket'], (255, 40, 40))
        d.text((cx + 6, cy + 4), row['id'].replace('man.', ''), fill=(255, 255, 255))
        d.text((cx + 6, cy + cell - 16), ', '.join(row['faults']) or 'ok', fill=(255, 230, 0) if row['faults'] else (200, 255, 200))
    S.save(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = inspect()
    sheet(rows, os.path.join(OUT, 'cards_man.png'))
    json.dump([r for r, _ in rows], open(os.path.join(OUT, 'cards_man.json'), 'w'), indent=1)
    for r, _ in rows:
        print(f"{r['id']:26s} {str(r['size']):11s} pivot@{r['pivot_frac']} ink_y{r['ink_y']}  {'; '.join(r['faults']) or 'ok'}")


if __name__ == '__main__':
    main()
