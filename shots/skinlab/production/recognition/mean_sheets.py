"""Side-by-side sheets for the mean critic (MEAN_CRITIC.md): painting | puppet at the same height, one file per pose.

    python3 mean_sheets.py <blind dir> <blind key.json> <out dir> <out key.json>

Renders come from the blind folder (exactly what the recognition critic saw). Poses are reshuffled and renamed m01..m30,
and the key (m -> pose id) goes outside the out dir, so the mean critic cannot learn the recognition test's mapping.
"""
import json, os, random, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '../../../..'))
bdir, bkey, out, okey = sys.argv[1:5]
K = json.load(open(bkey)); K = K.get('files', K)
items = sorted(K.items()); random.Random(len(items) * 7919 + sum(map(ord, bdir))).shuffle(items)
os.makedirs(out, exist_ok=True); key = {}
H = 900
for i, (f, v) in enumerate(items, 1):
    src = None
    for ext in ('.webp', '.png', '.jpg'):
        p = os.path.join(ROOT, 'shots/kits/cut', v['id'] + ext)
        if os.path.exists(p): src = p; break
    pa = Image.open(src).convert('RGBA'); bb = pa.getbbox(); pa = pa.crop(bb)
    bg = Image.new('RGBA', pa.size, (236, 228, 214, 255)); bg.alpha_composite(pa); pa = bg.convert('RGB')
    pu = Image.open(os.path.join(bdir, f)).convert('RGB')
    # trim the render's empty margin, then scale both to the same height
    g = pu.convert('L').point(lambda x: 255 if x < 225 else 0); bb = g.getbbox() or (0, 0) + pu.size
    pu = pu.crop((max(0, bb[0] - 10), max(0, bb[1] - 10), min(pu.width, bb[2] + 10), min(pu.height, bb[3] + 10)))
    pa = pa.resize((round(pa.width * H / pa.height), H)); pu = pu.resize((round(pu.width * H / pu.height), H))
    sh = Image.new('RGB', (pa.width + pu.width + 60, H + 50), 'white'); d = ImageDraw.Draw(sh)
    sh.paste(pa, (20, 40)); sh.paste(pu, (pa.width + 40, 40))
    d.text((20, 12), 'PAINTING', fill='black'); d.text((pa.width + 40, 12), 'PUPPET', fill='black')
    n = f'm{i:02d}.jpg'; sh.save(os.path.join(out, n), quality=85); key[n] = v
json.dump({'about': 'MEAN CRITIC KEY: not for critics', 'files': key}, open(okey, 'w'), indent=1)
print(len(key), 'sheets ->', out)
