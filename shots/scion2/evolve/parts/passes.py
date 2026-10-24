"""Quick part passes: heads only, hands only, shoes only.

For each benchmark target, crop the REFERENCE around the part (from its Pose Lab markers), embed it with CLIP, and rank
the library's cards of that part (same character; hygiene-excluded and target-sourced cards removed) by CLIP similarity.
Each candidate is shown turned and scaled the way it would sit on that joint, beside the reference crop. Minutes, not
hours: an early test of whether the library can supply the right head / hand / shoe before any assembly.

    python3 -m evolve.parts.passes head|hand|foot [n_targets]      (run from shots/scion2)
"""
import json, math, os, sys
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..'))
SK = os.path.join(ROOT, 'shots/skinlab')
CLIP = '/tmp/claude-0/clip'
MEAN, STD = np.array([0.48145466, 0.4578275, 0.40821073]), np.array([0.26862954, 0.26130258, 0.27577711])
BG = (236, 233, 228)
sys.path.insert(0, os.path.join(ROOT, 'shots/scion2'))
from rigkit import core  # noqa: E402

F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)

L = json.load(open(os.path.join(SK, 'library.json')))
E = np.load(os.path.join(CLIP, 'emb.npy')).astype(np.float32)
E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
from evolve.puzzle.hygiene import junk as _junk  # noqa: E402
_H = json.load(open(os.path.join(ROOT, 'shots/scion2/evolve/lab/hygiene.json')))
HY = {k for k, r in _H.items() if _junk(r)}   # the lab's own junk rule (hygiene.json holds scores for every card)
LAB = json.load(open(os.path.join(SK, 'labels.json'))).get('cards', {}) if os.path.exists(os.path.join(SK, 'labels.json')) else {}
VIS = ort.InferenceSession(os.path.join(CLIP, 'visual.onnx'), providers=['CPUExecutionProvider'])


def prep(im):
    im = im.convert('RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    s = 224 / max(im.size)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))))
    c = Image.new('RGB', (224, 224), BG)
    c.paste(im, ((224 - im.width) // 2, (224 - im.height) // 2), im)
    return ((np.asarray(c) / 255.0 - MEAN) / STD).transpose(2, 0, 1).astype(np.float32)


def embed(im):
    x = prep(im)[None]
    v = VIS.run(None, {VIS.get_inputs()[0].name: x})[0][0]
    return v / (np.linalg.norm(v) + 1e-9)


def P(m, k):
    v = m.get(k)
    return np.array(v[:2], float) if v and (len(v) < 5 or not isinstance(v[4], (int, float)) or v[4] >= .25) else None


def region(part, m, side):
    """(centre, axis angle deg (direction the part points), size px) from the markers"""
    sh = [P(m, 'shoulderL'), P(m, 'shoulderR')]
    span = np.linalg.norm(sh[0] - sh[1]) if sh[0] is not None and sh[1] is not None else 60
    if part == 'head':
        h, n = P(m, 'head'), P(m, 'neck')
        if h is None or n is None:
            return None
        c = h + (h - n) * .1
        return c, math.degrees(math.atan2(*(h - n)[::-1])), max(np.linalg.norm(h - n) * 2.4, span * .9)
    if part == 'hand':
        e, w = P(m, 'elbow' + side), P(m, 'wrist' + side)
        if e is None or w is None:
            return None
        d = (w - e) / (np.linalg.norm(w - e) + 1e-6)
        return w + d * span * .22, math.degrees(math.atan2(d[1], d[0])), span * .75
    if part == 'foot':
        a, t, k = P(m, 'ankle' + side), P(m, 'toe' + side), P(m, 'knee' + side)
        if a is None:
            return None
        d = (t - a) if t is not None else (a - k if k is not None else np.array([0, 1.]))
        d = d / (np.linalg.norm(d) + 1e-6)
        return a + d * span * .2, math.degrees(math.atan2(d[1], d[0])), span * .8


def ref_crop(img, c, size):
    x0, y0 = int(c[0] - size / 2), int(c[1] - size / 2)
    return img.crop((x0, y0, x0 + int(size), y0 + int(size)))


def card_img(c):
    p = os.path.normpath(os.path.join(SK, c['img']))
    return Image.open(p).convert('RGBA') if os.path.exists(p) else None


def placed(c, angle, size):
    """the card turned so its A->B axis points along the part's axis, scaled to fit the crop"""
    im = card_img(c)
    if im is None:
        return None
    A, B = np.array(c['A'], float), np.array(c['B'], float)
    a_card = math.degrees(math.atan2(*(B - A)[::-1]))
    im = im.rotate(-(angle - a_card), resample=Image.BICUBIC, expand=True)
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    s = size * .92 / max(im.size)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))))


def tile(im, size, label, sub, color):
    t = Image.new('RGB', (size, size + 44), (255, 255, 255))
    bg = Image.new('RGB', (size, size), BG)
    if im is not None:
        bg.paste(im, ((size - im.width) // 2, (size - im.height) // 2), im if im.mode == 'RGBA' else None)
    t.paste(bg, (0, 0))
    d = ImageDraw.Draw(t)
    d.rectangle([0, 0, size - 1, size - 1], outline=color, width=3)
    d.text((4, size + 3), label, fill=color, font=FB)
    d.text((4, size + 24), sub[:46], fill=(80, 80, 80), font=F)
    return t


def main(part, n=None):
    B = json.load(open(os.path.join(ROOT, 'shots/scion2/evolve/lab/benchmark.json')))['train']
    out = os.path.join(ROOT, 'shots/scion2/evolve/parts', part)
    os.makedirs(out, exist_ok=True)
    rows, log = [], []
    for t in B[:n] if n else B:
        char = '%s__%s' % (t['char'], t['costume'])
        try:
            MK = core.load_markers(char)
        except Exception:
            continue
        if t['id'] not in MK:
            continue
        tg = MK[t['id']]
        src = next((os.path.join(ROOT, 'shots/kits/cut', t['id'] + e) for e in ('.webp', '.png') if os.path.exists(os.path.join(ROOT, 'shots/kits/cut', t['id'] + e))), None)
        if not src:
            continue
        img = Image.open(src).convert('RGBA')
        if tg.get('w') and img.size != (tg['w'], tg['h']):
            img = img.resize((tg['w'], tg['h']))
        pool = [i for i, c in enumerate(L) if c.get('character') == t['char'] and (LAB.get(c['id'], {}).get('slot') or c.get('slot')) == part
                and c['id'] not in HY and not LAB.get(c['id'], {}).get('bad') and t['id'] not in c['id'] and t['id'] not in c.get('img', '')]
        for side in (['L', 'R'] if part != 'head' else ['']):
            r = region(part, tg['markers'], side)
            if r is None or not pool:
                continue
            c, ang, size = r
            crop = ref_crop(img, c, size)
            q = embed(crop)
            sims = E[pool] @ q
            order = np.argsort(-sims)[:6]
            S = 200
            cells = [tile(crop.convert('RGBA').resize((S, S)), S, 'REFERENCE', '%s %s' % (part, side), (30, 110, 200))]
            for rank, j in enumerate(order):
                cc = L[pool[j]]
                cells.append(tile(placed(cc, ang, S), S, 'C%d  clip %.3f' % (rank + 1, sims[j]), cc['id'].split('/')[-1], (200, 60, 40)))
            row = Image.new('RGB', (len(cells) * (S + 8) + 8, S + 44 + 30), (225, 228, 232))
            ImageDraw.Draw(row).text((8, 6), '%s   %s %s   (%d library %s cards for %s)' % (t['id'], part, side, len(pool), part, t['char']), fill=(20, 20, 20), font=FB)
            for i, ce in enumerate(cells):
                row.paste(ce, (8 + i * (S + 8), 30))
            rows.append(row)
            log.append({'target': t['id'], 'side': side, 'pool': len(pool), 'top': [[L[pool[j]]['id'], round(float(sims[j]), 4)] for j in order]})
        print(t['id'], part, 'done', flush=True)
    per = 6
    for p in range(0, len(rows), per):
        ch = rows[p:p + per]
        W = max(r.width for r in ch)
        sheet = Image.new('RGB', (W, sum(r.height for r in ch) + 50), (210, 214, 220))
        ImageDraw.Draw(sheet).text((8, 12), '%s pass, sheet %d: REFERENCE crop (blue) | top 6 library %s cards by CLIP, turned onto the joint (red)' % (part.upper(), p // per + 1, part), fill=(20, 20, 20), font=FB)
        y = 50
        for r in ch:
            sheet.paste(r, (0, y)); y += r.height
        sheet.save(os.path.join(out, '%s_%02d.jpg' % (part, p // per + 1)), quality=85)
    json.dump(log, open(os.path.join(out, 'ranking.json'), 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
