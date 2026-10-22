"""One scale and one quality grade for every cut part: shots/kits/cut/registry.json.

    python3 shots/kits/registry.py            # all parts
    python3 shots/kits/registry.py --sheet 09.props.phones-chair

Why: every planner sized parts its own way (a 60 cm moon card placed like a prop at the camera, a
22 cm handset blown up to a set piece), and a bad cut was as likely to be placed as a good one.
Per part this writes:
  place      how a size is meant: body (on a character), held, worn, floor (furniture, props on the
             ground), arch (doors, walls, buildings), land (trees, rocks, far set pieces), band (a strip that
             spans the frame), sky (moon, sun, clouds, stars: sized as a share of the frame, never in cm), fx
  cm         [w, h] real size, and px_per_cm, from the best source available:
             body parts  -> the Body Lab's per-sheet scale (shots/bodylab/body.json)
             props       -> the dossier's scale_cm (longest side) for the part it names, then the same sheet
                            scale for the sheet's other parts
             set pieces  -> a size table by kind (door 215 cm, tree 650 …)
  scale_src  where the size came from (bodylab | dossier | sheet | table | none)
  q          A (use), B (usable, check), C (do not place) and the reasons, from the cut image itself:
             fragments, a sheet chunk (mostly paper), clipped at a panel edge, holes, printed text, tiny,
             a pale fringe around the edge, a reference panel
"""
import glob, json, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
CUT = os.path.join(HERE, 'cut')

SKY = r'\b(moon|sun|cloud|clouds|star|stars|sky|comet|jupiter|planet|galaxy|constellation|aurora)\b'
FX = r'\b(haze|smoke|glow|light|beam|rain|ripple|spark|flare|dust|ash|fleck|mist|fog|shimmer|shadow|reflection|leak)\b'
ARCH = r'\b(door|wall|window|arch|facade|façade|building|tower|booth|gate|column|pillar|stair|steps|tread|landing|rail|railing|fence|frame|roof|porch|chapel|temple|house|shop|cafe|kiosk|awning|bridge|viaduct|lamp ?post|pole|sign)\b'
LAND = r'\b(tree|trees|stump|rock|rocks|bush|hill|mountain|dune|reef|boat|ship|wreck|car|motorcycle|bike)\b'
FLOOR = r'\b(chair|table|sofa|couch|bed|armchair|desk|bench|crate|box|suitcase|suitcases|basin|pot|planter|speaker|decks?|turntable|piano|tv|television|drawer|chest|lantern|lamp|hourglass)\b'
HELD = r'\b(phone|handset|receiver|cup|glass|mic|microphone|pen|paper|page|letter|letters|book|journal|vape|coin|key|ring|flower|daisy|poppy|petal|tambourine|heart|hand ?held|card|knife|cigarette|lighter|record|vinyl|photo|snapshot|rose)\b'
WORN = r'\b(sunglasses|glasses|hat|cap|earcup|headphones|jacket|scarf|bag|watch)\b'
BODY_SHEET = re.compile(r'\.(body|hands|feet|heads|face|faces|hipcore|replacements|torso|limbs|heads-hands|face-feet|faces-hands|main-?poses|action|chest)')

# real sizes for set pieces without a dossier size (longest side, cm)
TABLE = {'door': 215, 'window': 140, 'wall': 300, 'arch': 320, 'booth': 230, 'gate': 400, 'column': 450, 'pillar': 450,
         'stair': 200, 'steps': 200, 'tread': 120, 'landing': 300, 'rail': 300, 'railing': 300, 'fence': 300, 'frame': 220,
         'building': 1200, 'tower': 4500, 'facade': 900, 'house': 900, 'shop': 600, 'cafe': 600, 'awning': 300, 'bridge': 3000,
         'viaduct': 4000, 'chapel': 1400, 'temple': 1600, 'porch': 400, 'tree': 650, 'stump': 120, 'rock': 120, 'bush': 120,
         'boat': 600, 'ship': 3000, 'car': 450, 'motorcycle': 210, 'bike': 200, 'chair': 90, 'table': 120, 'sofa': 200,
         'couch': 200, 'bed': 200, 'armchair': 95, 'desk': 140, 'bench': 180, 'crate': 60, 'box': 50, 'suitcase': 70,
         'basin': 60, 'speaker': 110, 'decks': 100, 'turntable': 50, 'tv': 70, 'television': 70, 'lantern': 45, 'lamp': 160,
         'hourglass': 45, 'phone': 22, 'handset': 22, 'receiver': 21, 'cup': 10, 'mic': 22, 'microphone': 22, 'paper': 30,
         'letter': 25, 'book': 25, 'journal': 22, 'vape': 12, 'coin': 3, 'flower': 40, 'daisy': 30, 'poppy': 40,
         'tambourine': 25, 'heart': 14, 'sunglasses': 15, 'glasses': 14, 'hat': 30, 'photo': 15, 'snapshot': 12, 'sign': 120}


def place_of(sheet, text):
    t = text.lower()
    if BODY_SHEET.search(sheet) and not re.search(r'\bprops?\b', sheet):
        return 'body'
    folder_fx = '.fx.' in sheet
    if re.search(SKY, t):
        return 'sky'
    if folder_fx or re.search(FX, t):
        return 'fx'
    if re.search(WORN, t):
        return 'worn'
    if re.search(HELD, t):
        return 'held'
    if re.search(FLOOR, t):
        return 'floor'
    if re.search(ARCH, t):
        return 'arch'
    if re.search(LAND, t):
        return 'land'
    return 'floor' if '.props.' in sheet else 'land' if ('.set.' in sheet or '.hero.' in sheet) else 'floor'


def grade(path, part, sheet_size):
    """Cut quality from the image alone."""
    try:
        im = np.array(Image.open(path).convert('RGBA'))
    except Exception:
        return 'C', ['unreadable']
    a = im[..., 3] > 128
    h, w = a.shape
    why = []
    rr = str(part.get('ref_reason', ''))
    if part.get('kind') == 'ref' and re.search(r'label fragment|section box', rr):
        return 'C', ['reference panel: ' + rr]          # printed words, or a box of several cards
    assembled = part.get('kind') == 'ref'               # an assembled figure or object: a usable whole
    if a.sum() < 400 or min(w, h) < 14:
        return 'C', ['tiny']
    lab, n = ndi.label(a)
    sizes = np.bincount(lab.ravel())[1:]
    big = (sizes > .03 * a.sum()).sum()
    if big > 3 and not re.search(r'fleck|ash|dust|seed|shard|petal|star|rain|spark|letters?', part.get('label', ''), re.I):
        why.append(f'fragments ({big})')
    rgb = im[..., :3].astype(int)
    pale = (rgb.min(2) > 225) & a
    if pale.sum() > .45 * a.sum():
        why.append('mostly paper (sheet chunk)')
    filled = ndi.binary_fill_holes(a)
    holes = filled.sum() - a.sum()
    if holes > .25 * filled.sum():
        why.append('big holes')
    # clipped: long straight alpha edges along the crop box
    edge = [a[0].mean(), a[-1].mean(), a[:, 0].mean(), a[:, -1].mean()]
    if sum(e > .6 for e in edge) >= 2 and not re.search(r'sky|sea|strip|band|floor|ground|wall|water|road|street', part.get('label', ''), re.I) and w * h < .5 * sheet_size[0] * sheet_size[1]:
        why.append('clipped at a panel edge')
    # pale fringe: paper left round the edge = near-white, colourless outer ring (the kraft edge is tan, not this)
    ring = a & ~ndi.binary_erosion(a, iterations=2)
    if ring.sum() > 50:
        white = (rgb.min(2) > 215) & (rgb.max(2) - rgb.min(2) < 18)
        if white[ring].mean() > .35:
            why.append('pale fringe')
    # printed lettering: near-black or white strokes in several pieces, little colour
    ink = (rgb.max(2) < 70) | ((rgb.min(2) > 215) & (rgb.max(2) - rgb.min(2) < 18))
    if a.sum() and ink[a].mean() > .85 and (sizes > 30).sum() >= 3:
        why.append('printed lettering')
        return 'C', why
    if assembled:
        why.append('assembled whole (' + rr[:40] + ')')
    if not part.get('label'):
        why.append('no label')
    serious = [x for x in why if not x.startswith(('no label', 'pale fringe', 'assembled'))]
    return ('C' if len(serious) >= 2 or 'mostly paper (sheet chunk)' in serious else 'B' if why else 'A'), why


def words(s):
    return {w for w in re.findall(r'[a-z]+', s.lower()) if len(w) > 2}


def main():
    cat = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
    body = json.load(open(os.path.join(SHOTS, 'bodylab', 'body.json')))
    bscale = {p['id']: p.get('scale_px_per_cm') for p in body['parts'] if p.get('gen') == 'cut'}
    props = {}
    for f in glob.glob(os.path.join(SHOTS, 'poems', 'dossier', '[0-9][0-9].json')):
        D = json.load(open(f))
        for p in D.get('props') or []:
            if p.get('scale_cm'):
                props[(D['num'], p['id'])] = (p['scale_cm'], words(p.get('name', '') + ' ' + p['id'].replace('_', ' ')))
    only = sys.argv[sys.argv.index('--sheet') + 1] if '--sheet' in sys.argv else None
    out = {}
    for sid, s in cat.items():
        if only and sid != only:
            continue
        poem = sid[:2] if sid[:2].isdigit() else None
        rows = []
        for p in s['parts']:
            text = ' '.join([p.get('name') or '', p.get('label') or '', p['id'].split('/')[1].replace('-', ' ')])
            place = place_of(sid, text)
            q, why = grade(os.path.join(CUT, p['file']), p, s.get('size') or [1536, 1024])
            r = {'place': place, 'q': q, 'why': why, 'px': p['bbox'][2:], 'px_per_cm': None, 'scale_src': 'none'}
            if place == 'body' and bscale.get(p['id']):
                r['px_per_cm'], r['scale_src'] = bscale[p['id']], 'bodylab'
            elif poem and place in ('held', 'worn', 'floor', 'arch', 'land'):
                best = max(((words(text) & ws, cm) for (n, _), (cm, ws) in props.items() if n == poem), key=lambda x: len(x[0]), default=(set(), None))
                if best[0]:
                    r['px_per_cm'], r['scale_src'] = max(p['bbox'][2:]) / best[1], 'dossier'
            if r['px_per_cm'] is None and place not in ('sky', 'band', 'fx', 'body'):
                k = next((k for k in TABLE if re.search(r'\b' + k + r's?\b', text.lower())), None)
                if k:
                    r['px_per_cm'], r['scale_src'] = max(p['bbox'][2:]) / TABLE[k], 'table'
            if p['bbox'][2] / max(1, p['bbox'][3]) >= 3.5 and p['bbox'][2] > 380 and place in ('land', 'floor', 'arch', 'fx', 'sky'):
                r['place'] = 'band' if place != 'sky' else 'sky'
            rows.append((p['id'], r))
        # the sheet's other parts share its scale (one sheet, one drawing scale) unless they have their own
        known = [r['px_per_cm'] for _, r in rows if r['scale_src'] in ('dossier', 'bodylab')]
        if known:
            med = float(np.median(known))
            for _, r in rows:
                if r['px_per_cm'] is None and r['place'] not in ('sky', 'band', 'fx'):
                    r['px_per_cm'], r['scale_src'] = med, 'sheet'
        for pid, r in rows:
            if r['px_per_cm']:
                r['px_per_cm'] = round(r['px_per_cm'], 3)
                r['cm'] = [round(r['px'][0] / r['px_per_cm'], 1), round(r['px'][1] / r['px_per_cm'], 1)]
            out[pid] = r
    path = os.path.join(CUT, 'registry.json')
    if only and os.path.exists(path):
        old = json.load(open(path))
        old['parts'].update(out)
        out = old['parts']
    from collections import Counter
    summary = {'parts': len(out), 'q': Counter(r['q'] for r in out.values()), 'place': Counter(r['place'] for r in out.values()),
               'scale_src': Counter(r['scale_src'] for r in out.values()), 'why': Counter(w.split(' (')[0] for r in out.values() for w in r['why'])}
    json.dump({'about': __doc__.strip().split('\n')[0], 'summary': summary, 'parts': out}, open(path, 'w'))
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
