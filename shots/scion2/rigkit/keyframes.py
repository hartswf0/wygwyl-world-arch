"""Keyframe stills for review before any full render:  python3 -m rigkit.keyframes shots/scion2/poems/<NN>/plan.json
(run from shots/scion2).

One still per key, rendered through scene.py exactly as the final frame would look (stage set, every character
in its pose at that moment, layered with the set planes, the shot's camera, 1600x900), taken a few frames after
the key lands so the overshoot has settled and the head/hand swaps are in.  Keys of different characters that
land on the same frame share a still.  Where a pose is held for more than HOLD_S seconds a "hold" still is added
in the middle of the hold, so the board shows what the viewer sees for most of the time.  A shot with no
character gets one still.

Writes poems/NN/keys/kNN.jpg, poems/NN/keys/index.json and poems/NN/board.jpg (board_1.jpg, board_2.jpg, ...
when there are more than PER_BOARD stills): thumbnails 400 px wide, each labelled with the key number, the time,
the WORD it lands on, the full line, each character with the painting its pose comes from, and the one-line why.
"""
import json, os, sys, textwrap
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

from . import scene

FPS = scene.FPS
SETTLE = 6            # frames after landing (overshoot + head swap at +3 are done)
HOLD_S = 4.0
PER_BOARD = 24
TW, TH = 400, 225
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def line_of(tl, t):
    best = None
    for s in tl['scenes']:
        for L in s['lines']:
            if L['t'] - 0.05 <= t <= L['e'] + 0.05:
                return L['text']
            if L['t'] <= t:
                best = L['text']
    return best or ''


def stills_for(shot):
    n = shot['f1'] - shot['f0']
    land = {}
    for c in shot['chars']:
        for i, k in enumerate(c['keys']):
            f = min(n - 1, int(round(k['t'] * FPS)) + SETTLE)
            land.setdefault(f, []).append((c, i))
    out = []
    for f in sorted(land):                  # keys landing within 6 frames of each other share a still
        if out and f - out[-1]['f'] <= 6:
            out[-1]['f'] = f; out[-1]['land'] += land[f]
        else:
            out.append({'f': f, 'land': list(land[f]), 'hold': False})
    if not out:
        out = [{'f': min(n - 1, SETTLE), 'land': [], 'hold': False}]
    edges = [s['f'] for s in out] + [n]
    holds = []
    for a, b in zip(edges, edges[1:]):
        if (b - a) / FPS > HOLD_S:
            holds.append({'f': (a + b) // 2, 'land': [], 'hold': True})
    return sorted(out + holds, key=lambda s: s['f'])


def describe(shot, st, tl):
    f = st['f']
    t = (shot['f0'] + f) / FPS
    who = []
    for c in shot['chars']:
        if not c['char']:
            who.append('%s: TODO (not rigged)' % c['who'])
            continue
        ki = c['frames'][f]['key']
        k = c['keys'][ki]
        nm = k['target'].split('/', 1)
        who.append('%s: %s' % (c['who'], k['target']))
    if st['land']:
        c, i = st['land'][0]
        k = c['keys'][i]
        word = ' / '.join(sorted({(cc['keys'][ii]['word'] or '(t=%.2f)' % cc['keys'][ii]['abs_t']) for cc, ii in st['land']}))
        why = k['why']
        tw = k['abs_t']
    else:
        word = '(hold)' if st['hold'] else '(shot)'
        why = ('held: ' + '; '.join(w for w in who)) if st['hold'] else shot['why']
        if st['hold']:
            prev = [cc['keys'][cc['frames'][f]['key']] for cc in shot['chars'] if cc['char']]
            why = 'held pose: ' + (prev[0]['why'] if prev else shot['why'])
        tw = t
    return {'t': round(t, 2), 'scene': shot['scene'], 'set': shot['set'], 'word': word, 'line': line_of(tl, tw),
            'chars': who, 'why': why, 'hold': st['hold'], 'zoom': round(shot['track'][f][0], 2)}


def board(items, path, title):
    cols = 4
    pad = 14
    f_b = ImageFont.truetype(FONTB, 15)
    f_r = ImageFont.truetype(FONT, 12)
    f_t = ImageFont.truetype(FONTB, 20)

    def lines_for(it):
        L = [('b', 'k%02d  %.2fs  %s  %s' % (it['n'], it['t'], it['scene'], it['word'].upper()))]
        for s in textwrap.wrap('"%s"' % it['line'], 58)[:3]:
            L.append(('r', s))
        for s in it['chars']:
            for q in textwrap.wrap(s, 62)[:2]:
                L.append(('g', q))
        for s in textwrap.wrap('why: ' + it['why'], 62)[:3]:
            L.append(('i', s))
        return L
    blocks = [lines_for(it) for it in items]
    lh = 15
    cell_h = TH + 8 + max(len(b) for b in blocks) * lh + 10
    rows = (len(items) + cols - 1) // cols
    Wb = cols * TW + (cols + 1) * pad
    Hb = 44 + rows * (cell_h + pad)
    im = Image.new('RGB', (Wb, Hb), (244, 240, 232))
    d = ImageDraw.Draw(im)
    d.text((pad, 12), title, font=f_t, fill=(20, 16, 12))
    for j, (it, bl) in enumerate(zip(items, blocks)):
        x = pad + (j % cols) * (TW + pad)
        y = 44 + (j // cols) * (cell_h + pad)
        th = Image.open(it['file']).convert('RGB').resize((TW, TH), Image.LANCZOS)
        im.paste(th, (x, y))
        if it['hold']:
            d.rectangle([x, y, x + TW - 1, y + TH - 1], outline=(150, 150, 150), width=3)
        yy = y + TH + 6
        for kind, s in bl:
            col = {'b': (20, 16, 12), 'r': (40, 40, 40), 'g': (30, 70, 110), 'i': (110, 60, 30)}[kind]
            d.text((x, yy), s, font=f_b if kind == 'b' else f_r, fill=col)
            yy += lh + (3 if kind == 'b' else 0)
    im.save(path, quality=88)


def main(plan_path):
    plan, tl, shots = scene.build(plan_path)
    od = os.path.dirname(os.path.abspath(plan_path))
    kd = os.path.join(od, 'keys')
    os.makedirs(kd, exist_ok=True)
    for f in os.listdir(kd):
        if f.endswith('.jpg'):
            os.remove(os.path.join(kd, f))
    items = []
    for sh in shots:
        scene.plan_frames(sh)
        for st in stills_for(sh):
            it = describe(sh, st, tl)
            it['n'] = len(items) + 1
            img = scene.render_frame((sh, st['f']))
            it['file'] = os.path.join(kd, 'k%02d.jpg' % it['n'])
            cv2.imwrite(it['file'], img, [cv2.IMWRITE_JPEG_QUALITY, 90])
            items.append(it)
            print('k%02d %.2fs %s %s' % (it['n'], it['t'], it['scene'], it['word']), flush=True)
    for f in os.listdir(od):
        if f.startswith('board') and f.endswith('.jpg'):
            os.remove(os.path.join(od, f))
    title = 'Poem %s  %s  -- keyframes (%d stills; grey frame = hold)' % (plan['poem'], tl['title'], len(items))
    if len(items) <= PER_BOARD + 4:
        board(items, os.path.join(od, 'board.jpg'), title)
        boards = ['board.jpg']
    else:
        nb = (len(items) + PER_BOARD - 1) // PER_BOARD
        per = (len(items) + nb - 1) // nb
        boards = []
        for b in range(nb):
            nm = 'board_%d.jpg' % (b + 1)
            board(items[b * per:(b + 1) * per], os.path.join(od, nm), title + '  [%d/%d]' % (b + 1, nb))
            boards.append(nm)
    json.dump({'poem': plan['poem'], 'title': tl['title'], 'boards': boards,
               'keys': [{k: v for k, v in it.items() if k != 'file'} | {'file': 'keys/' + os.path.basename(it['file'])} for it in items]},
              open(os.path.join(kd, 'index.json'), 'w'), indent=1)
    return items


if __name__ == '__main__':
    main(sys.argv[1])
