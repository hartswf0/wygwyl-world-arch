"""Shared helper for the per-card-master characters of the 8th production batch (the angel, the DJ,
the three club dancers, the ghost child, the Atlantis child and elder).  Not a character module.

Every whole-figure card of such a character is its own master (as chars/citizen_1__atlantis.py and
chars/traveler_1__atlantis.py do): a card is only ever posed on its own rig, so its painted head, hands
and brads stay as painted and nothing is swapped between cards.  On top of the automatic cut
(rigkit/auto.py) a card may take:
  head   : a hand-cut head polygon (card px), down to the collar; the rig's head layer is exactly it
  wings  : seed points on painted wings; each wing is found as the region bounded by the painted tan
           outline that holds a seed (feathers and robe are both white: only the outline tells them
           apart).  The wings are one layer behind everything, riding the chest
  prop   : a polygon round a held object (and the hand(s) holding it), cut out of the body and kept as
           that side's hand part, so it rides the wrist instead of the torso
  fill   : seed points in holes the background removal punched into the figure (the painting's own
           colours are intact under them: only the alpha is restored)
  cut    : polygons of non-figure paint removed from the card (a floor shadow, a caption)
setup(globals(), ...) fills a character module's MASTERS, KEYS, catalog and the rest from a table.
"""
import json, math, os
import numpy as np, cv2

from .. import auto, core
from .ancestor_robe__indigo_gold import own_paint

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def poly_mask(shape, polys):
    m = np.zeros(shape, np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    return m > 0


def raw_markers(files, fix):
    """{id: markers} straight from the marker files with the module's MARKER_FIX applied (usable at
    import time, before core.load_markers can import the module)"""
    out = {}
    for f in files:
        for t in json.load(open(os.path.join(core.ROOT, f)))['targets']:
            m = dict(t['markers'])
            for k, (x, y) in fix.get(t['id'], {}).items():
                m[k] = [float(x), float(y)] + list(m.get(k, [0, 0, 1.0, 'fix', 1.0])[2:4]) + [1.0]
            out[t['id']] = m
    return out


def self_scale(m):
    """the solver's median limb ratio of a card measured against itself (posing.solve_body): its
    inverse pins a master to scale 1 on its own painting"""
    P = lambda k: np.array(m[k][:2], float)
    L = lambda a, b: np.linalg.norm(P(a) - P(b))
    legs = max(L('hipR', 'kneeR') + L('kneeR', 'ankleR'), L('hipL', 'kneeL') + L('kneeL', 'ankleL')) / \
        ((L('hipR', 'kneeR') + L('kneeR', 'ankleR') + L('hipL', 'kneeL') + L('kneeL', 'ankleL')) / 2)
    arms = max(L('shoulderR', 'elbowR') + L('elbowR', 'wristR'), L('shoulderL', 'elbowL') + L('elbowL', 'wristL')) / \
        ((L('shoulderR', 'elbowR') + L('elbowR', 'wristR') + L('shoulderL', 'elbowL') + L('elbowL', 'wristL')) / 2)
    return float(np.median([1.0, legs, arms]))


def fill_holes_at(a, seeds):
    """restore the alpha of enclosed holes holding a seed point"""
    if not seeds:
        return a
    fig = np.pad((a > 0.5).astype(np.uint8), 1)
    ff = fig.copy()
    cv2.floodFill(ff, np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8), (0, 0), 1)
    holes = (ff == 0)[1:-1, 1:-1]
    n, lab = cv2.connectedComponents(holes.astype(np.uint8))
    a = a.copy()
    for (x, y) in seeds:
        i = lab[int(y), int(x)]
        if i:
            a[lab == i] = 1.0
    return a


def outline_regions(rgb, fig, tan_d=35):
    """regions of the figure bounded by its painted tan/brown outline"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    tan = cv2.dilate(((r - b > tan_d) & fig).astype(np.uint8), np.ones((2, 2), np.uint8)) > 0
    reg = fig & ~tan
    n, lab = cv2.connectedComponents(reg.astype(np.uint8), connectivity=4)
    return reg, lab


def wing_mask(rgb, fig, seeds, reach=1e9, not_=None):
    """the wings: outline regions holding a seed, their own outline (outline pixels nearer to them
    than to any other region, and not in not_: the arms' and hands' own pixels) and any small region
    they enclose"""
    reg, lab = outline_regions(rgb, fig)
    ids = {int(lab[int(y), int(x)]) for (x, y) in seeds} - {0}
    W = np.isin(lab, list(ids))
    other = reg & ~W
    dW = cv2.distanceTransform((~W).astype(np.uint8), cv2.DIST_L2, 5)
    dO = cv2.distanceTransform((~other).astype(np.uint8), cv2.DIST_L2, 5)
    wing = W | (fig & ~reg & (dW <= reach) & (dW <= dO) & (True if not_ is None else ~not_))
    # enclosed bits (feather spots, a speck of shading) belong to the wing
    ff = np.pad(wing.astype(np.uint8), 1)
    cv2.floodFill(ff, np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8), (0, 0), 1)
    wing |= ((ff == 0)[1:-1, 1:-1] & fig)
    return wing


def water(rgba_or_rgb, alpha, polys):
    """painted water inside the polygons: blue strokes and the pale highlights they enclose (drawn
    without a paper edge)"""
    b, r = rgba_or_rgb[..., 0].astype(np.float32), rgba_or_rgb[..., 2].astype(np.float32)
    blue = cv2.dilate(((b - r > 20) & (alpha > 0.05)).astype(np.uint8), np.ones((9, 9), np.uint8))
    ff = np.pad(blue, 1)
    cv2.floodFill(ff, np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8), (0, 0), 1)
    blue = (blue > 0) | (ff == 0)[1:-1, 1:-1]
    return blue & (alpha > 0.05) & poly_mask(alpha.shape, polys)


def lost_to_torso(S):
    fig = S['fig']
    owned = np.zeros(fig.shape, bool)
    for L in S['layers']:
        owned |= L['alpha'] > 0.5
    for L in S['layers']:
        if L['bones'] == 'torso':
            L['alpha'] = np.where(fig & ~owned, 1.0, L['alpha']).astype(np.float32)
    return S


def build_card(rgb, a, m, card, plain_fn, auto_opts, border):
    a = fill_holes_at(a, card.get('fill'))
    if card.get('cut'):
        a = np.where(poly_mask(a.shape, card['cut']), 0, a)
    pr = card.get('prop')
    opts = dict(auto_opts, **card.get('auto', {}))
    if card.get('head'):
        opts['head_win'] = (0.01, 0.01, 0.0, 9.0)     # no automatic head window: the polygon is the head
    S = auto.build_auto(rgb, a, m, plain_fn=plain_fn, erase_emblem=False, **opts)
    S['border'] = border
    S['brads'] = []          # brads stay painted: each card is its own master
    S = own_paint(S, rgb)
    fig = S['fig']
    if card.get('head'):
        hm = poly_mask(a.shape, [card['head']]) & fig
        for L in S['layers']:
            if L.get('is_head'):
                L['rgb'] = rgb.copy()
                L['alpha'] = hm.astype(np.float32)
                L['edgeok'] = np.ones(a.shape, np.float32)
            else:
                L['alpha'] = np.where(hm, 0, L['alpha']).astype(np.float32)
    if card.get('wings'):
        armpix = np.zeros(fig.shape, bool)
        for L in S['layers']:
            if L['name'].startswith('arm'):
                armpix |= L['alpha'] > 0.5
        wm = wing_mask(rgb, fig, card['wings'], not_=armpix)
        if card.get('head'):
            wm &= ~poly_mask(a.shape, [card['head']])
        for L in S['layers']:
            L['alpha'] = np.where(wm, 0, L['alpha']).astype(np.float32)
        S['layers'].insert(0, dict(name='wings', rgb=rgb.copy(), alpha=wm.astype(np.float32), edgeok=np.ones(a.shape, np.float32),
                                   bones={'chest': [('neck', 'midhip')]}, tau=1.0))
    S = lost_to_torso(S)
    if pr:
        # the held object leaves the body layers (it is that hand's part); the torso is filled in under
        # it from its own plain cloth, so the robe shows when the object moves away
        pm = poly_mask(a.shape, [pr['poly']]) & (a > 0.05)
        J = S['joints']
        q = np.array([J['shR'], J['shL'], J['hipL'], J['hipR']], np.float32)
        quad = poly_mask(a.shape, [q.mean(0) + (q - q.mean(0)) * 1.12])
        for L in S['layers']:
            if L['bones'] == 'torso':
                L['alpha'] = np.where(pm & ~quad, 0, L['alpha']).astype(np.float32)
                hole = pm & (L['alpha'] > 0.5)
                known = (L['alpha'] > 0.5) & ~pm & plain_fn(rgb, fig)
                L['rgb'] = auto.inpaint(L['rgb'], hole, known)
            L['alpha'] = np.where(pm & ~((L['bones'] == 'torso') & (L['alpha'] > 0.5)), 0, L['alpha']).astype(np.float32)
        S['prop_hole'] = pm
        a = np.where(pm, 0, a)
    # separate painted pieces off the main figure (drops of water; the robe below a basin that was cut
    # out) go to the legs layer when they lie below the hips, else to the torso
    bits = (a > 0.5) & ~fig
    if bits.any():
        n, lab = cv2.connectedComponents(bits.astype(np.uint8))
        hip_y = S['joints']['midhip'][1]
        for i in range(1, n):
            comp = lab == i
            to = 'legs' if np.nonzero(comp)[0].mean() > hip_y else 'torso'
            for L in S['layers']:
                if L['name'] == to:
                    L['alpha'] = np.where(comp, 1.0, L['alpha']).astype(np.float32)
                    L['rgb'] = np.where(comp[..., None], rgb, L['rgb'])
        S['fig'] = fig | bits
    if card.get('water'):
        # water painted over the body: its own alpha, no paper edge (the strip and the edge classes
        # read S['fig'], widened round it)
        wt = water(rgb, a, card['water'])
        for L in S['layers']:
            L['edgeok'] = np.where(cv2.dilate(wt.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0, 0, L['edgeok']).astype(np.float32)
        S['fig'] = S['fig'] | (cv2.dilate(wt.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0)
    if pr:
        # no paper edge where the body was cut round the held object (the object covers it)
        near = cv2.dilate(poly_mask(a.shape, [pr['poly']]).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        for L in S['layers']:
            L['edgeok'] = np.where(near, 0, L['edgeok']).astype(np.float32)
    if pr and pr.get('front'):
        # the arm carrying the prop is drawn last (the prop is placed just under it), so the object
        # held out in front of the body stays in front of it
        k = [i for i, L in enumerate(S['layers']) if L['name'] == 'arm' + pr['side']][0]
        S['layers'].append(S['layers'].pop(k))
    return S


def setup(ns, cards, plain_fn, auto_opts, view_rigs=None, border=2.5, posture_rigs=None):
    """fill a character module's namespace.  cards: {rig name: dict(id, view, cls, note, head, wings,
    prop, fill, cut, flags, keys, auto)}"""
    CHAR, files, fix = ns['CHAR'], ns['MARKER_FILES'], ns.setdefault('MARKER_FIX', {})
    RAW = raw_markers(files, fix)
    ns['DEPTH'] = DEPTH
    ns['PLAIN_FABRIC'] = plain_fn
    ns['BORDER'] = border
    ns['PART_BORDER'] = border

    def builder(k):
        def fn(rgb, a):
            m = core.load_markers(CHAR)[cards[k]['id']]['markers']
            return build_card(rgb, a, m, cards[k], plain_fn, auto_opts, border)
        return fn
    ns['MASTERS'] = {k: (c['id'], builder(k)) for k, c in cards.items()}
    ns['MASTER_FACING'] = {k: (c['view'][-1] if c['view'][-1:] in ('R', 'L') else None) for k, c in cards.items()}
    ns['BACK_RIGS'] = tuple(k for k, c in cards.items() if c['view'].startswith('back'))
    k0 = next(iter(cards))
    ns['BRAD_SOURCE'] = (cards[k0]['id'], 50.0, 50.0, 4.0, 5.0)     # required by the rig builder; never drawn
    ids = {c['id']: k for k, c in cards.items()}

    def catalog():
        return {c['id']: dict(costume=c.get('costume', ''), use='label', view=c['view'], cls=c.get('cls', 'stand'), props=[],
                              hands='', gaze=c.get('gaze', ''), note=c['note']) for c in cards.values()}

    def is_character_painting(tid, cat):
        return tid in cat

    def painting_flags(tid, cat):
        if tid not in cat:
            return ['painting not in this character\'s catalog']
        c = cards[ids[tid]]
        return [c['note'], '("no usable head" below: none is swapped in; each card is its own master and keeps its own '
                'painted head and hands)'] + list(c.get('flags', []))
    ns['catalog'], ns['is_character_painting'], ns['painting_flags'] = catalog, is_character_painting, painting_flags
    ns['CURATED_PARTS'] = {}
    ns['KEYS'] = {}
    for k, c in cards.items():
        keys = {'view': k, 'head': None, 'hands': {}, 'scale': 1 / self_scale(RAW[c['id']])}
        pr = c.get('prop')
        if pr:
            pid = 'prop:' + k
            ns['CURATED_PARTS'][pid] = dict(kind='hand', side=pr['side'], src=c['id'], poly=pr['poly'],
                                            wr=tuple(RAW[c['id']]['wrist' + pr['side']][:2]),
                                            el=tuple(RAW[c['id']]['elbow' + pr['side']][:2]), seat_r=pr.get('seat_r', 6),
                                            attrs={'shape': pr.get('what', 'prop')})
            if pr.get('water'):
                ns['CURATED_PARTS'][pid]['raw_fn'] = (lambda polys: lambda im: water(im, im[..., 3] / 255., polys))(pr['water'])
            if pr.get('raw_all'):
                # the whole object keeps its painted alpha and edge (it was painted without a paper edge
                # of its own where it lies over the body)
                ns['CURATED_PARTS'][pid]['raw_fn'] = lambda im: im[..., 3] > 0
            keys['hands'] = {pr['side']: [pid, False]}
        keys.update(c.get('keys', {}))
        ns['KEYS'][c['id']] = keys
    ns['POSTURE_RIGS'] = posture_rigs or {}
    ns['VIEW_RIGS'] = view_rigs or {v: (k0, False) for v in ('front', '3qR', '3qL', 'profR', 'profL', 'back', 'back3qR', 'back3qL')}
    ns['SCALE_PRIOR'] = False
    ns['EXTRA_FLAGS'] = {}
