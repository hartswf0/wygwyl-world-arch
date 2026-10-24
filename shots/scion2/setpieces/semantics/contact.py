"""Contact sheets of the doubtful cases in semantics.json, for a person (and for me) to audit.
Writes contact_<group>.jpg in this folder. Each tile: the cut-out on paper grey, then
  final category (confidence) / name / L: label class  C: CLIP top-3 / sheet.
Groups: conflict (label vs CLIP disagree, lowest confidence first), nolabel (no label class), charfrag (called a
person/body part), text (called text/graphic), lowconf (overall lowest confidence), byclass_<c> (random sample per class)."""
import json, os, sys, random
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
CUT = os.path.join(ROOT, 'shots/kits/cut')
D = json.load(open(os.path.join(ROOT, 'shots/scion2/setpieces/semantics.json')))
P = {k: v for k, v in D['parts'].items() if v['kind'] == 'card'}
TW, TH, IMG = 300, 330, 220
try:
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
except Exception:
    F = ImageFont.load_default()


def tile(pid):
    r = P[pid]
    t = Image.new('RGB', (TW, TH), (235, 232, 226))
    try:
        im = Image.open(os.path.join(CUT, pid + '.webp')).convert('RGBA')
    except Exception:
        im = Image.open(os.path.join(CUT, r['sheet'], pid.split('/', 1)[1] + '.webp')).convert('RGBA')
    im.thumbnail((TW - 10, IMG))
    t.paste(im, ((TW - im.width) // 2, 5 + (IMG - im.height) // 2), im)
    f = r['final']
    d = ImageDraw.Draw(t)
    lines = [f"{f['category']} ({f['confidence']:.2f}){' CONFLICT' if f['conflict'] else ''}",
             f"name: {f['name'][:44]}",
             f"L: {f['label_class']}  lbl: {(r['label'] or '')[:30]}",
             "C: " + ' '.join(f"{c[:10]}{p:.2f}" for c, p in r['clip_top3']),
             pid[:48]]
    for i, s in enumerate(lines):
        d.text((4, IMG + 10 + i * 15), s, fill=(200, 0, 0) if i == 0 and f['conflict'] else (20, 20, 20), font=F)
    return t


def sheet(name, ids, cols=6, maxn=48):
    ids = ids[:maxn]
    if not ids:
        return
    rows = (len(ids) + cols - 1) // cols
    S = Image.new('RGB', (cols * TW, rows * TH), (255, 255, 255))
    for i, pid in enumerate(ids):
        S.paste(tile(pid), ((i % cols) * TW, (i // cols) * TH))
    out = os.path.join(HERE, f'contact_{name}.jpg')
    S.save(out, quality=82)
    print(out, len(ids))


if __name__ == '__main__':
    random.seed(1)
    conf = lambda k: P[k]['final']['confidence']
    sheet('conflict', sorted([k for k in P if P[k]['final']['conflict']], key=conf))
    sheet('nolabel', sorted([k for k in P if not P[k]['final']['label_class']], key=conf))
    sheet('charfrag', sorted([k for k in P if P[k]['final']['category'] == 'character-fragment'], key=conf))
    sheet('text', sorted([k for k in P if P[k]['final']['category'] == 'text-graphic'], key=conf))
    sheet('lowconf', sorted(P, key=conf))
    for c in D['taxonomy']:
        ids = [k for k in P if P[k]['final']['category'] == c]
        random.shuffle(ids)
        sheet('byclass_' + c, ids, maxn=24)
