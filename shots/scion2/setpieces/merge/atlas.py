"""Atlases of registry.json for a person to audit.
  atlas/cat_<category>.jpg   every usable piece of that category, best first (registry rank); dup copies dimmed tag
  atlas/unusable.jpg         every unusable card (refs excluded: they are all catalog kind=ref) with its reason
  atlas/unusable_refs.jpg    the 152 reference panels (small tiles)
  atlas/merge_rules.jpg      every part a MERGE rule changed (P1/P2/C1/U7/U8/F3)
Tiles: cut-out on paper grey, then grade|plane|size, name, flags/affordances, id.
Usage: python3 atlas.py [category ...]   (no args = all)
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(SP, '../../..'))
OUT = os.path.join(SP, 'atlas'); os.makedirs(OUT, exist_ok=True)
R = json.load(open(os.path.join(SP, 'registry.json')))['parts']
try:
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
    FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 12)
except Exception:
    F = FB = ImageFont.load_default()


def tile(r, lines, TW=230, IMG=170, red=False):
    TH = IMG + 8 + 14 * len(lines)
    t = Image.new('RGB', (TW, TH), (232, 229, 222) if not red else (245, 222, 218))
    im = Image.open(os.path.join(ROOT, r['file'])).convert('RGBA')
    im.thumbnail((TW - 8, IMG - 4))
    t.paste(im, ((TW - im.width) // 2, 3 + (IMG - im.height) // 2), im)
    d = ImageDraw.Draw(t)
    for i, s in enumerate(lines):
        d.text((3, IMG + 4 + i * 14), s[:40], fill=(150, 0, 0) if (i == 0 and red) else (20, 20, 20), font=FB if i == 0 else F)
    return t


def sz(r):
    s = r.get('size_cm')
    return f"{max(s.get('h') or 0, s.get('w') or 0):.0f}cm" if s else '?cm'


def std_lines(r):
    affs = ','.join(f"{a['kind']}{a['confidence']:.1f}" for a in r['affordances'])
    return [f"{r['grade']} {r['plane']} {sz(r)} {'DUP' if r['duplicate_of'] else ''}",
            (r['name'] or '')[:40],
            ('!' + ','.join(r['flags']) if r['flags'] else '') + (' ' + affs if affs else ''),
            r['id'][:40]]


def sheet(name, items, cols=8, **kw):
    if not items:
        return
    tiles = [tile(r, l, red=red, **kw) for r, l, red in items]
    TW, TH = tiles[0].width, max(t.height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    S = Image.new('RGB', (cols * TW, rows * TH), (255, 255, 255))
    for i, t in enumerate(tiles):
        S.paste(t, ((i % cols) * TW, (i // cols) * TH))
    p = os.path.join(OUT, name + '.jpg'); S.save(p, quality=80); print(p, len(tiles), S.size)


def main(cats=None):
    U = [r for r in R.values() if r['usable']]
    allcats = sorted(set(r['category'] for r in U))
    for c in (cats or allcats):
        items = sorted([r for r in U if r['category'] == c], key=lambda r: -r['rank'])
        sheet('cat_' + c, [(r, std_lines(r), bool(r['flags'])) for r in items])
    if cats:
        return
    bad = sorted([r for r in R.values() if not r['usable'] and r['kind'] != 'ref'],
                 key=lambda r: (r['unusable_reasons'][0]['rule'], r['id']))
    sheet('unusable', [(r, [' '.join(w['rule'] + ':' + w['by'] for w in r['unusable_reasons']),
                            ', '.join(str(x) for w in r['unusable_reasons'] for x in w['reason'])[:40],
                            f"sem:{r['category']} lbl:{r['label'][:28]}", r['id'][:40]], True) for r in bad])
    refs = sorted([r for r in R.values() if r['kind'] == 'ref'], key=lambda r: r['id'])
    sheet('unusable_refs', [(r, ['ref (catalog kind=ref)', r['id'][:40]], True) for r in refs], cols=12, TW=150, IMG=110)
    mr = [r for r in R.values() if set(r['merge_rules']) & {'P1', 'P2', 'C1', 'U7', 'U8', 'F3'}]
    mr.sort(key=lambda r: (sorted(set(r['merge_rules']) & {'P1', 'P2', 'C1', 'U7', 'U8', 'F3'}), r['id']))
    sheet('merge_rules', [(r, [' '.join(sorted(set(r['merge_rules']) & {'P1', 'P2', 'C1', 'U7', 'U8', 'F3'})) + f" {r['category']} {r['plane']}",
                               (r['label'] or '')[:40], ','.join(f"{a['kind']}{a['confidence']:.2f}" for a in r['affordances'] + r['affordances_dropped']),
                               r['id'][:40]], False) for r in mr])


if __name__ == '__main__':
    main(sys.argv[1:] or None)
