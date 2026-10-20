"""The part library: one contract for every part, drawn in code or cut from an image.

    python3 shots/arena/parts/library.py          # build lib/, library.json, sheet.png

A part is a file plus a contract:

  id            man.hand.R.palm.fist, kit.boot.profile.roll20, man.head.profile_R
  kind          head torso pelvis uarm farm hand thigh shin boot
  view/side/shows/state   what it is, for selection and swapping
  source        "code"   drawn by kit/*.py from its joints
                "image"  a generated or photographed card, sockets REGISTERED by eye
                "traced" code shapes cut to an image card's outline (trace.py),
                         carrying that card's registered sockets
  file          PNG, card px (and an SVG for code parts, resolution-free)
  ppc           px per cm of the file
  sockets       {name: [x, y]} in file px. A at the pivot, B straight down.
  socket_source "constructed" (code: exact) | "registered" (image: placed by a
                person, verified by the critic). Never "inferred".

The assembler only ever asks: library.pick(kind, view=, side=, shows=, state=)
and gets a part with sockets it can trust, or a named MISSING it can report.
"""
import json, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.normpath(os.path.join(HERE, '..', '..'))
LIB = os.path.join(HERE, 'lib')
sys.path.insert(0, HERE)
from kit import vec, hand as H, body as B

HAND_SHAPES = ['flat', 'open', 'relaxed', 'point', 'fist', 'thumb', 'pinch', 'peace', 'grip', 'cup']


def _write_code(pid, part, meta):
    im, (ox, oy) = vec.render(part['shapes'])
    im.save(os.path.join(LIB, pid + '.png'))
    open(os.path.join(LIB, pid + '.svg'), 'w').write(vec.svg(part['shapes']))
    ppc = vec.PX_PER_CM
    rec = dict(meta, id=pid, kind=part['kind'], source='code', file=f'arena/parts/lib/{pid}.png',
               svg=f'arena/parts/lib/{pid}.svg', ppc=ppc, size=list(im.size),
               sockets={k: [round(ox + v[0] * ppc, 2), round(oy + v[1] * ppc, 2)] for k, v in part['sockets'].items()},
               socket_source='constructed')
    for k in ('view', 'side', 'shows', 'state', 'length_cm'):
        if k in part and k not in rec:
            rec[k] = part[k]
    return rec


def build():
    os.makedirs(LIB, exist_ok=True)
    parts = []
    for side in ('R', 'L'):
        for shows in ('palm', 'back'):
            for shape in HAND_SHAPES:
                p = H.hand(side, shows, shape, 0.3)
                parts.append(_write_code(f'kit.hand.{side}.{shows}.{shape}', p, {'view': 'flat'}))
    for k in B.LIMBS:
        parts.append(_write_code(f'kit.{k}', B.limb(k), {'view': 'any'}))
    for v in ('profile', 'front'):
        parts.append(_write_code(f'kit.pelvis.{v}', B.pelvis(v), {'view': v}))
    for roll in (0, 20, 40):
        parts.append(_write_code(f'kit.boot.profile.roll{roll}', B.boot('profile', roll), {'view': 'profile', 'state': {'roll': roll}}))
    parts.append(_write_code('kit.boot.front', B.boot('front'), {'view': 'front'}))

    reg = json.load(open(os.path.join(HERE, 'registered.json')))['parts']
    for pid, r in reg.items():
        path = os.path.join(SHOTS, r['file'])
        size = list(Image.open(path).size)
        rec = {'id': pid, 'kind': r['kind'], 'view': r['view'], 'source': 'image', 'file': r['file'],
               'size': size, 'sockets': r['sockets'], 'socket_source': 'registered', 'note': r.get('note', '')}
        if r.get('state'):
            rec['state'] = r['state']
        if size != r['size']:
            rec['refused'] = f"file is {size}, sockets were placed on {r['size']}: re-register"
        parts.append(rec)
    # traced parts (trace.py): code shapes cut to a generated card's outline
    for fn in sorted(os.listdir(LIB)):
        if fn.endswith('.traced.json'):
            rec = json.load(open(os.path.join(LIB, fn))).get('record')
            if rec:
                parts.append(rec)
    json.dump({'about': __doc__.strip().split('\n')[0], 'parts': parts}, open(os.path.join(HERE, 'library.json'), 'w'), indent=1)
    sheet(parts)
    return parts


def load():
    return json.load(open(os.path.join(HERE, 'library.json')))['parts']


def pick(parts, kind, **want):
    """Best part for a request; exact match on every given key, else drop keys right to left.
    Returns (part, missing_keys)."""
    pool = [p for p in parts if p['kind'] == kind and 'refused' not in p]
    keys = [k for k in ('source', 'view', 'side', 'shows', 'shape', 'roll', 'expression') if k in want]

    def val(p, k):
        if k == 'expression':
            return (p.get('state') or {}).get('expression')
        if k == 'shape':
            return (p.get('state') or {}).get('shape')
        if k == 'roll':
            return (p.get('state') or {}).get('roll')
        return p.get(k)
    for n in range(len(keys), -1, -1):
        ks = keys[:n]
        hit = [p for p in pool if all(val(p, k) == want[k] for k in ks)]
        if hit:
            if k_roll := want.get('roll_near'):
                hit.sort(key=lambda p: abs((p.get('state') or {}).get('roll', 0) - k_roll))
            return hit[0], keys[n:]
    return None, keys


def sheet(parts):
    cell = 170
    cols = 12
    rows = (len(parts) + cols - 1) // cols
    S = Image.new('RGB', (cols * cell, rows * (cell + 16)), (128, 128, 128))
    d = ImageDraw.Draw(S)
    for i, p in enumerate(parts):
        im = Image.open(os.path.join(SHOTS, p['file'])).convert('RGBA')
        k = min((cell - 20) / im.size[0], (cell - 20) / im.size[1])
        t = im.resize((max(1, int(im.size[0] * k)), max(1, int(im.size[1] * k))))
        x, y = (i % cols) * cell, (i // cols) * (cell + 16)
        ox, oy = x + (cell - t.size[0]) // 2, y + 16 + (cell - 20 - t.size[1]) // 2
        S.paste(t, (ox, oy), t)
        for name, q in p['sockets'].items():
            if name in ('A', 'B'):
                cx, cy = ox + q[0] * k, oy + q[1] * k
                col = (0, 255, 0) if name == 'A' else (255, 40, 40)
                d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], outline=col, width=2)
        d.text((x + 3, y + 2), p['id'].replace('kit.', '').replace('man.', 'img:')[:28],
               fill=(255, 255, 255) if p['source'] == 'code' else (255, 230, 120))
    S.save(os.path.join(HERE, 'sheet.png'))


if __name__ == '__main__':
    ps = build()
    print(len(ps), 'parts;', sum(p['source'] == 'code' for p in ps), 'code,', sum(p['source'] == 'image' for p in ps), 'image')
