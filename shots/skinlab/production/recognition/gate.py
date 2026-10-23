"""Regression gate (Builder A's side): every pose a blind critic has recognised, its painting | the render it was recognised
from | the current render, on one sheet; look at it before pushing. python3 gate.py [out.jpg]"""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SHOTS = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
# every pose a blind critic has ever recognised (tests 1-6), shown beside its latest recognised render: the 19 of test 6,
# falter-at-shoulder-contact-2 (test 3) and falter-at-shoulder-contact (test 1)
T6 = ['poet.04.main-poses/04-2-heart-seated', 'poet.04.main-poses/04-4-empty-cuffs', 'poet.04.main-poses/04-5-left-then-right-1', 'poet.04.main-poses/04-6-rise-flex-reflect',
      'poet.05.main-poses/06-walk-to-the-gate-2', 'poet.05.main-poses/q2-star-overhead', 'poet.05.main-poses/q3-restless-lying-2', 'poet.07.main-poses/pluck-the-daisy',
      'poet.07.main-poses/push-two-sides-apart', 'poet.08.main-poses/03-gentle-slow-bent-knee-dance-alone', 'poet.09.main-poses/phone-palm', 'poet.10.main-poses/03-coil-to-mount',
      'poet.10.main-poses/in-wind', 'poet.11.main-poses/welcome-new-day', 'poet.12.main-poses/02', 'poet.12.main-poses/03', 'poet.13.main-poses/01-cafe-sit',
      'poet.13.main-poses/06-refocus', 'poet.13.main-poses/part-2']
GATE = {**{i: 6 for i in T6}, 'poet.09.main-poses/falter-at-shoulder-contact-2': 3, 'poet.09.main-poses/falter-at-shoulder-contact': 1}
def main(out):
    k3 = {v['id']: f for f, v in json.load(open(os.path.join(HERE, 'poet', 'blind3_key.json')))['files'].items()}
    k4 = {v['id']: f for f, v in json.load(open(os.path.join(HERE, 'results', 'blind4_key.json')))['files'].items()}
    k5 = {v['id']: f for f, v in json.load(open(os.path.join(HERE, 'results', 'blind5_key.json')))['files'].items()}
    k6 = {v['id']: f for f, v in json.load(open(os.path.join(HERE, 'results', 'blind6_key.json')))['files'].items()}
    k1 = {v['id']: f for f, v in json.load(open(os.path.join(HERE, 'results', 'blind1_key.json'))).items()}
    R = {r['id']: r for r in json.load(open(os.path.join(HERE, 'poet', 'renders', 'reports.json')))['reports']}
    h = 300; rows = []
    for pid, test in GATE.items():
        r = R[pid]; cells = [('painting', Image.open(os.path.join(SHOTS, r['img'])).convert('RGBA'))]
        old = {3: lambda: os.path.join(HERE, 'poet', 'blind3', k3[pid]), 4: lambda: os.path.join('/tmp/claude-0/blind4', k4[pid]),
               5: lambda: os.path.join('/tmp/claude-0/blind5', k5[pid]), 6: lambda: os.path.join('/tmp/claude-0/blind6', k6[pid]),
               1: lambda: os.path.join('/tmp/claude-0/blind1', k1[pid])}[test]()
        cells.append((f'recognised (test {test})', Image.open(old).convert('RGBA') if os.path.exists(old) else None))
        cells.append(('now', Image.open(os.path.join(HERE, 'poet', 'renders', r['safe'] + '.png')).convert('RGBA')))
        rows.append((pid + ('   CROPPED_HARD' if r.get('cropped_hard') else ''), cells))
    W = 1200; S = Image.new('RGB', (W * 2, (len(rows) + 1) // 2 * (h + 24)), (233, 226, 212)); d = ImageDraw.Draw(S)
    for i, (pid, cells) in enumerate(rows):
        x0, y0 = (i % 2) * W, (i // 2) * (h + 24); d.text((x0 + 6, y0 + 4), pid, fill=(30, 20, 10)); x = x0 + 6
        # wide cells (lying, bikes) shrink together so all three fit in the row's half of the sheet
        tw = sum(im.width * h / im.height for _, im in cells if im is not None) + 8 * len(cells) + (200 if any(im is None for _, im in cells) else 0)
        hh = min(h, int(h * (W - 12 - 8 * len(cells)) / max(1, tw - 8 * len(cells))))
        for lab, im in cells:
            if im is None: d.text((x, y0 + 40), lab + ': missing', fill=(200, 0, 0)); x += 200; continue
            im = im.resize((max(1, int(im.width * hh / im.height)), hh)); bg = Image.new('RGB', im.size, (233, 226, 212)); bg.paste(im, (0, 0), im)
            S.paste(bg, (x, y0 + 22)); d.text((x + 2, y0 + 22), lab, fill=(120, 0, 0)); x += im.width + 8
    S.save(out, quality=80); print(out)
if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'poet', 'gate_A.jpg'))
