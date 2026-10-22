"""First-pass stage plans for every poem: shots/stage/plans/NN.json, one stage per scene-book scene.

    python3 shots/stage/plan_poems.py            # poems without a plan
    python3 shots/stage/plan_poems.py 07 13 -f   # these, replacing an existing auto plan (hand plans are kept unless -F)

For each scene of the poem (atlas scene book + the dossier's staging) it lays, back to front:
  set      the poem's cut set or hero sheet that best matches the staging's set id: a sky card on top,
           the long strips stacked far to near as bands, up to four free-standing pieces in the middle;
           when no cut sheet matches, the place's own footage as a depth-plane set (AI as set)
  cast     each character named in the scene, in the pose cut from its main-poses sheet whose scene number
           matches (else the nearest), standing on the floor line
  props    the props the staging names, from the poem's cut prop sheets
  action   the solved Arena action for the scene's movement (walk, crouch, fall, dance, wait), hidden
  archive  the scene's atlas references, hidden and tagged, ready to switch on
Everything is a first pass to rearrange on the stage; plans with "auto": false are never overwritten.
"""
import json, os, re, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
CAT = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'catalog.json')))['sheets']
ASSETS = json.load(open(os.path.join(HERE, 'assets.json')))
W, H, FLOOR = 1600, 900, 800
words = lambda s: {w for w in re.findall(r'[a-z]+', str(s).lower().replace('_', ' ')) if len(w) > 2} - {'the', 'and', 'set', 'hero', 'props', 'with', 'his', 'her'}


def num(code):
    return float(code) if code else None


REF = re.compile(r'reference|assembled|composite|not a cutout|overview|example|proof', re.I)


def sheets_of(n, folder):
    return {sid: dict(s, parts=[p for p in s['parts'] if not REF.search(p['label'] or '')]) for sid, s in CAT.items()
            if n in s['poems'] and s['folder'] == folder and s['parts']}


def best_sheet(n, set_id):
    """The cut set/hero sheet sharing most words with the set id; ties go to the poem's own sheets."""
    best, score = None, 0
    for sid, s in sheets_of(n, '04_SETS_AND_BUILDINGS').items():
        sc = len(words(set_id) & words(sid)) + (.5 if sid.startswith(n) else 0)
        if sc > score:
            best, score = sid, sc
    return best if score >= 1 else None


FAR = r'sky|sea|ocean|water|horizon|skyline|treeline|tree line|mountain|city|far|back|distant|smallest|cloud'
NEAR = r'\bfront\b|floor|ground|soil|sand|ash|grass|weed|foreground|near|rail|kerb|deck|street|pavement|grit'


def depth(p):
    """Far (low) to near (high): what the strip is, then how tall it is (a nearer strip is drawn taller)."""
    lab = p['label'].lower() + ' ' + p['id'].split('/')[1]
    return (-1 if re.search(FAR, lab) else 1 if re.search(NEAR, lab) else 0, p['bbox'][3] / p['bbox'][2])


def any_sky(n):
    for sid, s in sorted(sheets_of(n, '04_SETS_AND_BUILDINGS').items(), key=lambda kv: '.set.' not in kv[0]):
        for p in s['parts']:
            if re.search(r'\bsky\b', p['label'], re.I) and p['bbox'][2] / p['bbox'][3] >= 3:
                return p
    return None


def any_floor(n, not_sid):
    for sid, s in sorted(sheets_of(n, '04_SETS_AND_BUILDINGS').items(), key=lambda kv: '.set.' not in kv[0]):
        for p in s['parts']:
            if sid != not_sid and re.search(r'floor|ground|street|deck|quay', p['label'], re.I) and p['bbox'][2] / p['bbox'][3] >= 3:
                return p
    return None


def lay_set(sid, n):
    """A set sheet as layers: a sky on top (borrowed from the poem's other sheets if this one has none),
    strips as bands far to near, up to four free-standing pieces in the middle."""
    parts = CAT[sid]['parts']
    strips = [p for p in parts if p['bbox'][2] / p['bbox'][3] >= 3.5 and p['bbox'][2] > 380]
    pieces = [p for p in parts if p not in strips and p['bbox'][2] * p['bbox'][3] > 9000][:4]
    sky = [p for p in strips if re.search(r'\bsky\b|backdrop', p['label'], re.I)][:1] or ([any_sky(n)] if any_sky(n) else [])
    bands = sorted([p for p in strips if p not in sky and not re.search(r'\bsky\b', p['label'], re.I)], key=depth)   # one sky: day/dusk/night variants stay in the tray
    L = [{'part': p['id'], 'x': 800, 'y': 230, 'w': 1800, 'h': 480} for p in sky]
    ys = [380 + i * (480 / max(1, len(bands) - 1)) for i in range(len(bands))] if len(bands) > 1 else [700]
    for p, y in zip(bands, ys):
        L.append({'part': p['id'], 'x': 800, 'y': round(y), 'w': 1800, 'h': max(120, round(p['bbox'][3] * 1800 / p['bbox'][2]))})
    if not any(depth(b)[0] == 1 for b in bands):   # no floor on this sheet: borrow the poem's
        fl = any_floor(n, sid)
        if fl:
            L.append({'part': fl['id'], 'x': 800, 'y': 830, 'w': 1800, 'h': max(150, round(fl['bbox'][3] * 1800 / fl['bbox'][2]))})
    mid = [L.pop()] if bands and depth(bands[-1])[0] == 1 else []   # a near floor strip goes in front of the cast
    for p, x in zip(pieces, (260, 1340, 560, 1060)):
        w = min(420, p['bbox'][2])
        L.append({'part': p['id'], 'x': x, 'y': FLOOR - 40 - round(w * p['bbox'][3] / p['bbox'][2] / 2), 'w': w})
    return L, mid


def lay_planes(still):
    S = ASSETS['planes'].get(still)
    if not S:
        return []
    L = [{'kind': 'plane', 'src': S['backdrop'], 'x': 800, 'y': 450, 'w': 1600, 'h': 900, 'label': S['short'] + ' backdrop'}]
    L += [{'kind': 'plane', 'src': s['file'], 'x': 800, 'y': 450, 'w': 1600, 'h': 900, 'label': S['short'] + ' ' + (s.get('plane') or s['sheet'])} for s in S['sheets']]
    return L


def poses(n, who):
    """Cut pose figures for a character in this poem, with their scene numbers."""
    out = []
    for sid, s in sheets_of(n, '02_ACTIONS_AND_POSES').items():
        if (sid.split('.')[0] == who or (who == 'party' and sid.startswith(('party', '08.cast')))) and 'pose' in sid:
            # figures: the panel cut-outs, or (sheets without rules) the big cards
            out += [p for p in s['parts'] if p['kind'] == 'pose' or p['bbox'][2] * p['bbox'][3] > 40000]
    return out


def panel_no(p):
    m = re.match(r'\s*0?(\d{1,2})\b', p['label'] or '')
    return int(m.group(1)) if m else None


def pick_pose(ps, key, used, i):
    """The figure for scene `key` (the i-th scene): its scene number, else its panel number in order, else the nearest."""
    k = num(key)
    for test in (lambda p: p['scene'] == key, lambda p: panel_no(p) == i + 1):
        hit = [p for p in ps if test(p) and p['id'] not in used]
        if hit:
            return hit[0]
    ranked = sorted(ps, key=lambda p: (p['id'] in used, abs(num(p['scene']) - k) if p['scene'] else 99))
    return ranked[0] if ranked else None


def image_layer(rel_from_poems, label):
    p = os.path.join(SHOTS, 'poems', rel_from_poems)
    if not os.path.exists(p):
        return None
    w, h = Image.open(p).size
    src = rel_from_poems.split('/')[2] if rel_from_poems.count('/') > 2 else 'atlas'
    return {'kind': 'image', 'src': '../poems/' + rel_from_poems, 'x': 1250, 'y': 230, 'w': 480, 'ar': round(h / w, 4), 'label': label,
            'tag': f'ARCHIVE · {src} · {label}'[:70], 'blend': 'screen', 'op': .85, 'hide': True}


def plan(n):
    D = json.load(open(os.path.join(SHOTS, 'poems', 'dossier', f'{n}.json')))
    A = json.load(open(os.path.join(SHOTS, 'poems', 'atlas', f'{n}.json')))
    stg = {g['scene']: g for g in (D.get('atlas') or {}).get('staging') or []}
    sets = {s['id']: s for s in D.get('sets') or []}
    chars = [c['id'] for c in D.get('characters') or []]
    props = D.get('props') or []
    prop_parts = [p for s in sheets_of(n, '03_PROPS').values() for p in s['parts']]
    used, scenes = set(), []
    for si, sc in enumerate(A['scenes']):
        g = stg.get(sc['key'], {})
        text = ' '.join([sc.get('what', ''), g.get('shot', ''), sc.get('block') or ''])
        set_id = g.get('set') or next(iter(sets), '')
        layers, front, note = [], [], []
        sid = best_sheet(n, set_id)
        if sid:
            layers, front = lay_set(sid, n)
            note.append(f'set from {sid}')
        else:
            refs = [r for r in (sets.get(set_id, {}).get('refs') or []) if '/' not in r] + ASSETS['poems'][n]['planes']
            layers = lay_planes(refs[0]) if refs else []
            note.append(f'no cut set for {set_id}: footage depth planes {refs[0][:8] if refs else ""}')
        # cast: the poet always when named; others when the scene names them
        who = [c for c in chars if c == 'poet' or re.search(r'\b' + {'young_poet': 'young', 'ghost_child': 'child', 'woman': 'mother|she|woman'}.get(c, c) + r'\b', text, re.I)]
        xs = iter((800, 1120, 480, 1340))
        for c in who[:3]:
            p = pick_pose(poses(n, c), sc['key'], used, si)
            if not p:
                continue
            used.add(p['id'])
            hgt = 420 if c != 'young_poet' else 250
            w = round(hgt * p['bbox'][2] / p['bbox'][3])
            layers.append({'part': p['id'], 'x': next(xs), 'y': FLOOR - hgt // 2, 'w': w})
        # props the staging names (by the prop's own name), two at most, each part once
        placed = 0
        for pr in sorted(props, key=lambda pr: not pr.get('hero')):
            toks = words(pr.get('name', '')) | words(pr['id'])
            if placed >= 2 or not toks & words(text):
                continue
            cand = [p for p in prop_parts if p['id'] not in used and (words(p['label']) & toks or words(p['id'].split('/')[0]) & toks)]
            if cand:
                p = cand[0]
                used.add(p['id'])
                placed += 1
                w = min(260, p['bbox'][2])
                layers.append({'part': p['id'], 'x': 1050 if len(front) % 2 == 0 else 560, 'y': FLOOR - 30, 'w': w})
        layers += front
        # a solved action for the scene's movement, switched off, ready to swap in for the still pose
        for pat, act in ((r'\bwalk|stroll|climb|step|follow', 'ACT-001__man'), (r'kneel|crouch|search', 'ACT-003__man'),
                         (r'\bfall|falls|fell|drop', 'ACT-008__man'), (r'danc|spin', 'ACT-017__man'), (r'wait|stand|sits?\b|seated', 'ACT-024__man')):
            if re.search(pat, text, re.I):
                layers.append({'kind': 'action', 'action': act, 'x': 800, 'y': FLOOR - 200, 'w': 420, 'hide': True,
                               'label': 'solved action for this beat (switch on to replace the still pose)'})
                break
        for r in (g.get('refs') or [])[:2]:
            im = image_layer(r, sc['name'])
            if im:
                layers.append(im)
        scenes.append({'key': sc['key'], 'name': sc['name'], 'set': set_id, 'shot': g.get('shot') or sc.get('block') or '', 'note': '; '.join(note), 'layers': layers})
    return {'num': n, 'title': D.get('title'), 'auto': True,
            'note': 'First pass by plan_poems.py from the dossier staging and the cut kits; rearrange on the stage and export to keep.', 'scenes': scenes}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    force, hard = '-f' in sys.argv, '-F' in sys.argv
    os.makedirs(os.path.join(HERE, 'plans'), exist_ok=True)
    for n in args or [f'{i:02d}' for i in range(1, 15)]:
        out = os.path.join(HERE, 'plans', f'{n}.json')
        if os.path.exists(out):
            old = json.load(open(out))
            if not (hard or (force and old.get('auto'))):
                print(n, 'kept (exists' + ('' if old.get('auto') else ', hand plan') + ')')
                continue
        P = plan(n)
        json.dump(P, open(out, 'w'), indent=1)
        print(n, P['title'], len(P['scenes']), 'scenes,', sum(len(s['layers']) for s in P['scenes']), 'layers ·', '; '.join(s['note'] for s in P['scenes'])[:160])


if __name__ == '__main__':
    main()
