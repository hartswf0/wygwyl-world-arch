"""Rig Builder data: every body part of every character, with resolved control points, at true scale.

    python3 shots/rig/build.py                 # all characters with a buildable body
    python3 shots/rig/build.py poet/red_black_sunglasses
    python3 shots/rig/build.py --labels DIR    # read label files from DIR instead of shots/rig/labels/

Writes shots/rig/data/index.json and shots/rig/data/<character>__<costume>.json.

Sources (read-only):
  shots/bodylab/body.json        class / side / view / state / px-per-cm for every body piece
  shots/kits/cut/registry.json   quality grade A/B/C (+ reasons) and px/cm per cut part
  shots/kits/cut/catalog.json    brads (via rigs.py)
  shots/stage/anim/rigs.py       the point resolver (pivot / socket / neck / waist / hips / ankle / heel / toe)
  shots/stage/anim/rigs.SPEC     the hand-picked default card per slot, where a character has one
  shots/stage/anim/cards.py      known hand shapes per card
  shots/rig/labels/*.json        human answers from the Builder's captchas and edits (applied last, so they win)

Control points are stored in the card's own pixel frame with VIEWER-left / VIEWER-right names
(shVL/shVR, hipVL/hipVR); the page decides which is the actor's L for the chosen view.
"""
import json, os, sys, glob, math, time
from collections import Counter, defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
ANIM = os.path.join(SHOTS, 'stage', 'anim')
sys.path.insert(0, ANIM)
import rigs  # noqa: E402

SLOT_CLASSES = ['torso', 'hip', 'head', 'upper_arm', 'forearm', 'hand', 'thigh', 'shin', 'shoe']
KIND = {'torso': 'torso', 'hip': 'bridge', 'head': 'head', 'upper_arm': 'limb', 'forearm': 'limb',
        'thigh': 'limb', 'shin': 'limb', 'hand': 'hand', 'shoe': 'foot'}
# costumes that are the same outfit drawn twice (the tracksuit pack is the poet's red/black tracksuit)
ALIAS = {'poet/tracksuit_v1': 'poet/red_black_sunglasses'}
# rigs.SPEC defaults: which body.json character/costume each stage rig belongs to
SPEC_OF = {'poet/red_black_sunglasses': 'poet_tracksuit', 'poet/black_tshirt': 'poet_tshirt',
           'young_poet/child_clothes': 'young_poet', 'woman/poem13': 'woman', 'ex/ex_jacket': 'ex',
           'party_guest/guest': 'party_guest'}
SLOT_OF_SPEC = {'torso': 'torso', 'bridge': 'hip', 'uarm': 'upper_arm', 'farm': 'forearm', 'hand': 'hand',
                'thigh': 'thigh', 'shin': 'shin', 'foot': 'shoe'}

# ------------------------------------------------------------------ part table + resolver hooks
_TABLE = {}          # pid -> (rel to shots, abs, brads)


def _img_path(pid):
    rel, ab, _ = _TABLE[pid]
    return rel, ab


def _brads(pid, A):
    return [tuple(map(float, b)) for b in _TABLE[pid][2]]


# rigs.resolve looks these up as module globals: point them at our table, and never write cleaned copies
# into shots/stage/anim/parts (not ours).
rigs._img_path = _img_path
rigs._brads = _brads
rigs._cleaned = lambda pid, rel, ab: (rel, ab)


def unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else np.array([0.0, 1.0])


def hand_points(pid):
    """puppet.hand_card's method (wrist at the tab eyelet, axis to the hand centroid, tip = farthest pixel
       along the axis), with the tab side guessed: the narrowest end of the card."""
    rel, ab = _img_path(pid)
    A = rigs._alpha(ab); h, w = A.shape
    ys, xs = np.nonzero(A)
    if len(xs) < 20:
        return None
    P = np.stack([xs, ys], 1).astype(float)
    ext = max(xs.max() - xs.min(), ys.max() - ys.min()) or 1
    best = None
    for tab, inward in (('top', (0, 1)), ('bottom', (0, -1)), ('left', (1, 0)), ('right', (-1, 0))):
        inward = np.array(inward, float)
        proj = P @ inward
        near = P[proj < proj.min() + 0.10 * ext]
        side = near @ np.array([inward[1], inward[0]])
        width = float(side.max() - side.min()) if len(side) else 1e9
        # wrist tabs are narrow; prefer top (most sheets) on ties
        score = width * (0.9 if tab == 'top' else 1.0)
        if best is None or score < best[0]:
            best = (score, tab, inward, near)
    _, tab, inward, near = best
    end = near.mean(0)
    guess = end + inward * 0.075 * ext
    B = _brads(pid, A)
    wrist, src = guess, 'alpha'
    if B:
        b = min(B, key=lambda b: np.linalg.norm(np.array(b) - guess))
        if np.linalg.norm(np.array(b) - guess) < 0.10 * ext:
            wrist, src = np.array(b, float), 'brad'
    beyond = P[(P - wrist) @ inward > 0.18 * ext]
    cen = beyond.mean(0) if len(beyond) else P.mean(0)
    axis = unit(cen - wrist)
    pr = (P - wrist) @ axis
    tip = P[int(np.argmax(pr))]
    return {'pts': {'wrist': wrist.tolist(), 'tip': tip.tolist(), 'grip': cen.tolist()},
            'src': {'wrist': src, 'tip': 'alpha', 'grip': 'alpha'}, 'tab': tab}


def resolve(pid, cls, hints=None):
    kind = KIND[cls]
    if kind == 'hand':
        return hand_points(pid)
    try:
        r = rigs.resolve(pid, kind, hints or {})
    except Exception as e:          # empty alpha, odd card
        return {'pts': {}, 'src': {}, 'err': str(e)[:80]}
    B = _TABLE[pid][2]
    src = {}
    for k, p in r['pts'].items():
        on = any((b[0] - p[0]) ** 2 + (b[1] - p[1]) ** 2 < 4 for b in B)
        src[k] = 'brad' if on else ('alpha' if k in ('top', 'heel', 'toe', 'sole', 'tip') else 'hint')
    out = {'pts': {k: [round(float(v[0]), 1), round(float(v[1]), 1)] for k, v in r['pts'].items()}, 'src': src}
    if kind == 'foot':
        out['faces'] = r['faces']
    return out


# ------------------------------------------------------------------ labels (human answers) -> overrides
def load_labels(d):
    """Every committed label file. Returns per-part lists of answers, plus a summary."""
    per = defaultdict(list)
    files = sorted(glob.glob(os.path.join(d, '*.json')))
    n = 0
    for f in files:
        try:
            j = json.load(open(f))
        except Exception as e:
            print('labels: skip', f, e); continue
        for a in j.get('answers', []):
            if a.get('part'):
                a = dict(a); a['_file'] = os.path.basename(f)
                per[a['part']].append(a); n += 1
    return per, {'files': [os.path.basename(f) for f in files], 'answers': n}


def vote(vals):
    """Majority of non-'unsure' answers; ties -> None."""
    c = Counter(v for v in vals if v not in (None, 'unsure', 'skip'))
    if not c: return None
    (top, k), *rest = c.most_common(2) + [(None, 0)]
    return top if k > rest[0][1] else None


def apply_labels(part, answers):
    """Fold a part's answers into it. Points: median of clicks; categorical: majority vote."""
    if not answers: return
    applied = {}
    pts = defaultdict(list)
    for a in answers:
        t = a.get('t')
        if t in ('pivot', 'edit-point', 'site') and a.get('point') and a.get('xy'):
            pts[a['point']].append(a['xy'])
    for k, L in pts.items():
        xy = np.median(np.array(L, float), 0).round(1).tolist()
        part['pts'][k] = xy; part['src'][k] = 'label'
        applied['pt.' + k] = len(L)
    for t, key in (('side', 'side'), ('shape', 'shape'), ('slot', 'cls'), ('view', 'view')):
        v = vote([a.get('v') for a in answers if a.get('t') == t])
        if v is None: continue
        if t == 'side' and v == 'pair':
            part.setdefault('flags', []).append('labelled: L and R cut together as one card')
            part['q'] = 'C'; part['why'] = part['why'] + ['labelled: two parts in one card']
        elif t == 'slot' and v == 'not_body':
            part['cls'] = 'other'
        elif t == 'slot' and '_' in v and v.split('_')[-1] in ('L', 'R'):
            part['cls'], part['side'] = v.rsplit('_', 1)
        else:
            part[key] = v
        applied[t] = v
    cost = vote([a.get('v') for a in answers if a.get('t') == 'costume'])
    if cost == 'no':
        part['not_costume'] = True; part['why'] = part['why'] + ['labelled: not this costume']
        applied['costume'] = 'no'
    cut = [a for a in answers if a.get('t') == 'cut']
    v = vote([a.get('v') for a in cut])
    if v == 'no':
        reasons = sorted({r for a in cut if a.get('v') == 'no' for r in a.get('why', [])})
        part['q'] = 'C'; part['why'] = part['why'] + ['labelled unclean: ' + (', '.join(reasons) or 'see marks')]
        part['marks'] = [a['xy'] for a in cut if a.get('xy')][:12]
        applied['cut'] = 'no'
    elif v == 'yes' and part['q'] == 'B':
        part['q'] = 'A'; applied['cut'] = 'yes'
    sc = [a.get('v') for a in answers if a.get('t') == 'scale' and isinstance(a.get('v'), (int, float))]
    if sc:
        part['user_scale'] = round(float(np.median(sc)), 4); applied['scale'] = part['user_scale']
    part['labels'] = applied


# ------------------------------------------------------------------ build
def main():
    args = [a for a in sys.argv[1:]]
    lab_dir = os.path.join(HERE, 'labels')
    if '--labels' in args:
        i = args.index('--labels'); lab_dir = args[i + 1]; del args[i:i + 2]
    only = set(args)
    t0 = time.time()
    body = json.load(open(os.path.join(SHOTS, 'bodylab', 'body.json')))
    reg = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'registry.json')))['parts']
    cat = rigs.catalog()
    labels, lsum = load_labels(lab_dir)
    choices = defaultdict(list)
    rests = defaultdict(dict)        # char -> view -> latest Rest-rig answer (cards, draw order, near/far)
    for L in labels.values():
        for a in L:
            if a.get('t') == 'choice' and a.get('char'):
                choices[a['char']].append(a)
    for f in sorted(glob.glob(os.path.join(lab_dir, '*.json'))):
        try: A = json.load(open(f)).get('answers', [])
        except Exception: continue
        for a in A:
            if a.get('t') == 'rest' and a.get('char') and a.get('view') and isinstance(a.get('v'), dict):
                old = rests[a['char']].get(a['view'])
                if not old or a.get('ts', '') >= old.get('ts', ''):
                    rests[a['char']][a['view']] = dict(a['v'], ts=a.get('ts', ''))
    try:
        import cards
        known_shape = {}
        for h in ('poet_tracksuit', 'poet_tshirt', 'young_poet', 'woman', 'party_guest'):
            try:
                for s in cards.hands(h):
                    for (shape, v, side), pid in s['cards'].items():
                        known_shape[pid] = shape
            except Exception:
                pass
    except Exception:
        known_shape = {}

    groups = defaultdict(list)
    for p in body['parts']:
        key = p['character'] + '/' + p['costume']
        key = ALIAS.get(key, key)
        if p['class'] in SLOT_CLASSES:
            groups[key].append(p)

    index = {'about': 'Rig Builder data (shots/rig/build.py). Parts per character with control points in card px '
                      '(viewer-left/right names), px/cm, grade and reasons. Labels from shots/rig/labels/ applied.',
             'built': time.strftime('%Y-%m-%d %H:%M'), 'labels': lsum, 'stature': body['stature'],
             'norms': NORMS, 'limits': LIMITS, 'characters': []}
    os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
    for key, ch in body['characters'].items():
        if key in ALIAS: continue
        ps = groups.get(key, [])
        have = {p['class'] for p in ps}
        if 'torso' not in have or len(have & set(SLOT_CLASSES)) < 6:
            continue
        if only and key not in only: continue
        out_parts = []
        for p in ps:
            pid = p['id']
            rel = p['img']
            brads = p.get('brads') or (cat.get(pid, {}).get('brads') or [])
            _TABLE[pid] = (rel, os.path.join(SHOTS, rel), brads)
            if not os.path.exists(os.path.join(SHOTS, rel)):
                continue
            r = reg.get(pid, {})
            q = r.get('q', 'A' if p['gen'] != 'cut' else 'B')
            why = list(r.get('why', []))
            res = resolve(pid, p['class']) or {'pts': {}, 'src': {}}
            part = {'id': pid, 'img': rel, 'w': p['w'], 'h': p['h'], 'cls': p['class'], 'side': p.get('side'),
                    'view': p.get('view'), 'state': p.get('state'), 'label': p.get('label', ''),
                    'sheet': p['sheet'], 'gen': p['gen'], 'costume': p['costume'],
                    'shape': known_shape.get(pid) or (p.get('state') if p['class'] == 'hand' else None),
                    'q': q, 'why': why, 'ppc': p.get('scale_px_per_cm'), 'ppc_src': p.get('scale_source'),
                    'own_ppc': p.get('own_ppc'), 'problems': p.get('problems', []),
                    'brads': [[round(b[0]), round(b[1])] for b in brads[:30]], 'nb': len(brads),
                    'pts': res['pts'], 'src': res['src']}
            if 'faces' in res: part['faces'] = res['faces']
            if 'tab' in res: part['tab'] = res['tab']
            if p.get('dups'): part['dups'] = p['dups']
            apply_labels(part, labels.get(pid))
            out_parts.append(part)
        defaults = spec_defaults(key, {p['id'] for p in out_parts})
        # a part someone picked for a slot in the Builder becomes that slot's default (latest pick wins)
        have = {p['id'] for p in out_parts}
        for a in sorted(choices.get(key, []), key=lambda a: a.get('ts', '')):
            if a['part'] in have and a.get('slot'):
                defaults.setdefault(a.get('view') or 'front', {})[a['slot']] = a['part']
        rest = {v: r for v, r in rests.get(key, {}).items()}
        for v, r in rest.items():          # the Rest rig's card picks are that view's defaults too
            for slot, pid in (r.get('cards') or {}).items():
                if pid in {p['id'] for p in out_parts}: defaults.setdefault(v, {})[slot] = pid
        doc = {'key': key, 'rest': rest, 'character': ch['character'], 'costume': ch['costume'], 'name': ch['name'],
               'body': ch['body'], 'stature_cm': ch['stature_cm'], 'ref_sheet': ch.get('ref_sheet'),
               'spec': SPEC_OF.get(key), 'defaults': defaults, 'parts': out_parts}
        fn = key.replace('/', '__') + '.json'
        json.dump(doc, open(os.path.join(HERE, 'data', fn), 'w'), separators=(',', ':'))
        cnt = Counter(p['cls'] for p in out_parts)
        index['characters'].append({'key': key, 'name': ch['name'], 'costume': ch['costume'], 'file': 'data/' + fn,
                                    'stature_cm': ch['stature_cm'], 'n': len(out_parts), 'classes': dict(cnt),
                                    'spec': SPEC_OF.get(key), 'labelled': sum(1 for p in out_parts if p.get('labels'))})
        print(f'{key:40s} {len(out_parts):4d} parts  {dict(cnt)}')
    index['characters'].sort(key=lambda c: (c['key'] != 'poet/red_black_sunglasses', -c['n']))
    if only:     # keep the other characters already built
        old = os.path.join(HERE, 'data', 'index.json')
        if os.path.exists(old):
            keep = [c for c in json.load(open(old))['characters'] if c['key'] not in only]
            index['characters'] = index['characters'] + keep
    json.dump(index, open(os.path.join(HERE, 'data', 'index.json'), 'w'), indent=1)
    print(f'labels: {lsum["answers"]} answers from {len(lsum["files"])} files; {time.time() - t0:.1f}s')


def spec_defaults(key, have):
    """Slot -> part id from rigs.SPEC (the stage's hand-picked front cards), when the character has a spec."""
    name = SPEC_OF.get(key)
    out = {}
    if not name: return out
    s = rigs.SPEC[name]
    for view, parts in s['views'].items():
        d = {}
        for k, (pid, kind, hints) in parts.items():
            if pid.startswith('pack:poet_tracksuit_v1/01_COMPONENTS/'):      # the pack's bodylab copy
                pid = 'tracksuit/' + pid.rsplit('/', 1)[1][:-4]
            base, _, side = k.partition('_')
            slot = SLOT_OF_SPEC.get(base)
            if not slot or pid not in have: continue
            if side and side not in ('L', 'R'): continue     # foot_heelup / foot_toeup are replacement cards
            if side in ('L', 'R'):
                d[slot + '_' + side] = pid
            elif slot in ('torso', 'hip'):
                d[slot] = pid
            else:
                d[slot + '_L'] = d[slot + '_R'] = pid
        hv = s.get('heads', {}).get(view)
        if hv and hv[0] in have: d['head'] = hv[0]
        out[view] = d
    return out


# Anthropometric segment lengths as a fraction of standing height (what the critic measures):
# joint-to-joint for limbs, wrist->fingertip, heel->toe, chin->crown.
NORMS = {'hand': 0.108, 'shoe': 0.15, 'head': 0.13, 'forearm': 0.145, 'upper_arm': 0.186,
         'thigh': 0.245, 'shin': 0.246, 'torso': 0.30}
# Joint limits (deg) from the range-test norms (bolas/lab/range-test: shoulder 180, elbow 150, hip 120,
# knee 135, neck 50, trunk 90 incl. lateral bend 35). Signed: + = away from the body midline (front/back
# view) or toward the facing direction (profile).
LIMITS = {'head': [-50, 50], 'torso': [-35, 35], 'upper_arm': [-40, 180], 'forearm': [-150, 150],
          'hand': [-80, 80], 'thigh': [-30, 120], 'shin': [-135, 135], 'shoe': [-30, 45]}

if __name__ == '__main__':
    main()
