"""Blind bake-off sheets: painting | reproduction at the same height, all methods shuffled together.

    python3 shots/scion2/judge/sheets.py <out dir> <key.json>
A method with no output for a pose (a declared gap) gets no sheet and counts as FAIL.
"""
import json, os, random, sys
from PIL import Image, ImageDraw
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../..'))
out, keyf = sys.argv[1:3]
ONLY = sys.argv[3].split(',') if len(sys.argv) > 3 else None
T = json.load(open(os.path.join(ROOT, 'shots/scion2/test_set.json')))['poses']
M = {'h1': 'shots/scion2/h1/out', 'h2': 'shots/scion2/h2/out', 'h3': 'shots/scion2/h3/out', 'control': 'shots/scion2/control/out'}
def crop(im):
    im = im.convert('RGBA')
    if im.getextrema()[3][0] < 250: return im.crop(im.getbbox())
    g = im.convert('L').point(lambda x: 255 if x < 225 else 0); return im.crop(g.getbbox())
items, missing = [], []
for m, d in M.items():
    if ONLY and m not in ONLY: continue
    for p in T:
        b = p['id'].replace('/', '__'); f = next((os.path.join(ROOT, d, b + e) for e in ('.png', '.jpg') if os.path.exists(os.path.join(ROOT, d, b + e))), None)
        (items if f else missing).append((m, p, f))
random.Random(20261023 + len(items)).shuffle(items); os.makedirs(out, exist_ok=True); key = {}; H = 900
for i, (m, p, f) in enumerate(items, 1):
    pa = crop(Image.open(os.path.join(ROOT, p['painting']))); pu = crop(Image.open(f))
    def flat(x):
        bg = Image.new('RGBA', x.size, (236, 228, 214, 255)); bg.alpha_composite(x); return bg.convert('RGB')
    pa, pu = flat(pa), flat(pu)
    pa = pa.resize((round(pa.width * H / pa.height), H)); pu = pu.resize((max(1, round(pu.width * H / pu.height)), H))
    sh = Image.new('RGB', (pa.width + pu.width + 60, H + 50), 'white'); dr = ImageDraw.Draw(sh)
    sh.paste(pa, (20, 40)); sh.paste(pu, (pa.width + 40, 40)); dr.text((20, 12), 'PAINTING', fill='black'); dr.text((pa.width + 40, 12), 'PUPPET', fill='black')
    n = f's{i:02d}.jpg'; sh.save(os.path.join(out, n), quality=85); key[n] = {'method': m, 'id': p['id']}
json.dump({'about': 'BAKE-OFF KEY: not for critics', 'files': key, 'no_output': [[m, p['id']] for m, p, _ in missing]}, open(keyf, 'w'), indent=1)
print(len(items), 'sheets;', len(missing), 'declared gaps with no output:', [(m, p['kind']) for m, p, _ in missing])
