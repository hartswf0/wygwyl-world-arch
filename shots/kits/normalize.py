"""Normalise the cut body parts as one set: a slot and a true scale for every card, from the character's skeleton.

    python3 shots/kits/normalize.py      # -> shots/kits/cut/normalized.json + a before/after report

Why: the sheets were painted from our Kit v2 templates (shots/arena/parts/kit3/kit.py). The generator kept each
template's slots, names and order but redrew the layout and drew every card large to fill its cell, so a
sheet has no single drawing scale (hands on the hands sheet ≠ hands on the body sheet). Treating one px/cm per
sheet gave the same character's hand anywhere from 16 to 58 cm.
Here each card is scaled by WHAT IT IS: its slot's true length comes from the character's rest skeleton in
kit.CHARS (poet 184 cm: upper arm shoulder→elbow, forearm elbow→wrist, hand wrist→fingertip, thigh, shin,
foot heel→toe, head crown→chin, torso neck→hips), and the card's px/cm = its own measured length / that.
Slots come from the printed label matched against the closed list of slot words for the sheet type (not open
OCR), falling back to the Body Lab's class.
Validation uses what the scaling does not force: card WIDTH. If per-card scaling is right, a character's
hands (feet, forearms...) come out the same width on every sheet; the report gives the spread before and after.
"""
import collections, json, os, re, statistics as st, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SHOTS, 'arena', 'parts', 'kit3'))
import kit as K   # noqa: E402
import v2         # noqa: E402,F401  (registers the v2 builds into K.CHARS)

BUILD = [(r'^poet\.', 'poetm'), (r'^ex\.', 'ex'), (r'^young_poet\.', 'boy'), (r'^ghost', 'ghost'), (r'^woman\.', 'woman'),
         (r'^ancestors?\.', 'robed'), (r'mother|elder_woman|vintage_gown|gown|club_dress|female|woman', 'woman')]
SLOT_WORDS = [('upper_arm', r'upper ?arm|\buarm|\barm a\b'), ('forearm', r'fore ?arm|\bfarm\b'), ('hand', r'\bhand|palm|fist|grip|point|pinch|relaxed|open|thumb|peace|wave|claw|cup|flat'),
              ('thigh', r'thigh'), ('shin', r'\bshin|calf'), ('foot', r'foot|shoe|boot|sneaker|heel|toe'), ('head', r'\bhead|face'),
              ('torso', r'torso|bodice|chest|jacket|vest')]


def build_of(sheet, character=''):
    for pat, b in BUILD:
        if re.search(pat, sheet) or re.search(pat, character or ''):
            return b
    return 'manx'


def lengths(b):
    """True slot lengths in cm from the rest skeleton."""
    J = {k: np.array(v[:2], float) for k, v in K.CHARS[b]['J'].items()}
    d = lambda a, c: float(np.linalg.norm(J[a] - J[c]))
    toe = K.CHARS[b]['J'].get('toeL'); heel = K.CHARS[b]['J'].get('heelL')
    foot = abs(toe[2] - heel[2]) if toe is not None and heel is not None else 0.15 * K.CHARS[b]['height']
    return {'upper_arm': d('shoulderL', 'elbowL'), 'forearm': d('elbowL', 'wristL'), 'hand': d('wristL', 'tipL'),
            'thigh': d('hipL', 'kneeL'), 'shin': d('kneeL', 'ankleL'), 'foot': foot,
            'head': d('crown', 'chin') if 'crown' in J else .13 * K.CHARS[b]['height'], 'torso': d('neck', 'hipL')}


def slot_of(label, cls):
    t = (label or '').lower()
    for s, pat in SLOT_WORDS:
        if re.search(pat, t):
            return s, 'label'
    m = {'shoe': 'foot', 'foot': 'foot', 'hand': 'hand', 'head': 'head', 'torso': 'torso', 'upper_arm': 'upper_arm',
         'forearm': 'forearm', 'thigh': 'thigh', 'shin': 'shin'}.get(cls)
    return (m, 'bodylab') if m else (None, None)


def measure(path, slot, brads, view):
    """The card's own length along what its slot length means, in px."""
    a = np.array(Image.open(path).convert('RGBA'))[..., 3] > 128
    ys, xs = np.nonzero(a)
    if not len(xs):
        return None, 'empty'
    pts = np.stack([xs, ys], 1).astype(float)
    if slot in ('upper_arm', 'forearm', 'thigh', 'shin', 'torso') and len(brads) >= 2:
        B = np.array(brads, float)
        i, j = max(((i, j) for i in range(len(B)) for j in range(i + 1, len(B))), key=lambda ij: np.linalg.norm(B[ij[0]] - B[ij[1]]))
        return float(np.linalg.norm(B[i] - B[j])), 'brad→brad'
    if slot == 'hand' and len(brads) >= 1:
        b = np.array(brads[0], float)
        return float(np.max(np.linalg.norm(pts - b, axis=1))) * .92, 'eyelet→fingertip'
    if slot == 'foot':
        return (float(xs.max() - xs.min()) if view != 'front' and view != 'back' else None), 'heel→toe'
    if slot == 'head':
        return float(ys.max() - ys.min()) * .86, 'crown→chin'
    # limbs with fewer than two brads: the long axis, less the rounded ends
    c = pts - pts.mean(0)
    _, _, vt = np.linalg.svd(c[::max(1, len(c) // 4000)], full_matrices=False)
    proj = c @ vt[0]
    return float(proj.max() - proj.min()) * .86, 'long axis'


def width(path, slot):
    a = np.array(Image.open(path).convert('RGBA'))[..., 3] > 128
    ys, xs = np.nonzero(a)
    if not len(xs):
        return None
    pts = np.stack([xs, ys], 1).astype(float); c = pts - pts.mean(0)
    _, _, vt = np.linalg.svd(c[::max(1, len(c) // 4000)], full_matrices=False)
    return float((c @ vt[1]).max() - (c @ vt[1]).min())


def main():
    body = json.load(open(os.path.join(SHOTS, 'bodylab', 'body.json')))
    cat = json.load(open(os.path.join(HERE, 'cut', 'catalog.json')))['sheets']
    brads = {p['id']: p.get('brads') or [] for s in cat.values() for p in s['parts']}
    out, groups_before, groups_after = {}, collections.defaultdict(list), collections.defaultdict(list)
    L = {}
    for p in body['parts']:
        if p.get('gen') != 'cut':
            continue
        slot, src = slot_of(p.get('label'), p.get('class'))
        if not slot:
            continue
        b = build_of(p['sheet'], p.get('character'))
        L.setdefault(b, lengths(b))
        path = os.path.join(SHOTS, p['img'])
        m, how = measure(path, slot, brads.get(p['id'], []), p.get('view'))
        w = width(path, slot)
        rec = {'slot': slot, 'slot_src': src, 'side': p.get('side'), 'view': p.get('view'), 'state': p.get('state'),
               'character': p.get('character'), 'costume': p.get('costume'), 'build': b, 'slot_cm': round(L[b][slot], 1),
               'measure': how, 'px': round(m, 1) if m else None, 'px_per_cm': round(m / L[b][slot], 3) if m else None, 'flags': []}
        if src == 'label' and p.get('class') and slot_of('', p['class'])[0] not in (None, slot):
            rec['flags'].append(f"label says {slot}, Body Lab said {p['class']}")
        out[p['id']] = rec
        key = (p.get('character'), p.get('costume'), slot)
        if w and p.get('scale_px_per_cm'):
            groups_before[key].append((w / p['scale_px_per_cm'], p['sheet']))
        if w and rec['px_per_cm']:
            groups_after[key].append((w / rec['px_per_cm'], p['sheet']))
    # outliers: a card whose true-scale width is far from its group's median is probably mislabelled
    for key, v in groups_after.items():
        if len(v) >= 4:
            med = st.median(x for x, _ in v)
            for pid, rec in out.items():
                if (rec['character'], rec['costume'], rec['slot']) == key and rec['px_per_cm']:
                    pass
    def spread(G):
        r = []
        for key, v in G.items():
            sheets = {s for _, s in v}
            xs = sorted(x for x, _ in v)
            if len(sheets) >= 3 and len(xs) >= 4:
                lo, hi = xs[len(xs) // 10], xs[-1 - len(xs) // 10]          # 10th-90th percentile
                r.append((hi / max(.1, lo), key, len(xs)))
        return sorted(r, reverse=True)
    sb, sa = spread(groups_before), spread(groups_after)
    rep = {'parts': len(out), 'by_slot': collections.Counter(r['slot'] for r in out.values()),
           'slot_src': collections.Counter(r['slot_src'] for r in out.values()),
           'measure': collections.Counter(r['measure'] for r in out.values()),
           'flags': sum(1 for r in out.values() if r['flags']),
           'width_spread_before': {'median': round(st.median(x for x, *_ in sb), 2), 'groups_over_2x': sum(1 for x, *_ in sb if x > 2), 'groups': len(sb)},
           'width_spread_after': {'median': round(st.median(x for x, *_ in sa), 2), 'groups_over_2x': sum(1 for x, *_ in sa if x > 2), 'groups': len(sa)},
           'worst_after': [[round(x, 2), '/'.join(str(k) for k in key), n] for x, key, n in sa[:10]]}
    json.dump({'about': __doc__.strip().split('\n')[0], 'report': rep, 'lengths_cm': {b: {k: round(v, 1) for k, v in d.items()} for b, d in L.items()},
               'parts': out}, open(os.path.join(HERE, 'cut', 'normalized.json'), 'w'), indent=0)
    print(json.dumps(rep, indent=1, default=str))


if __name__ == '__main__':
    main()
