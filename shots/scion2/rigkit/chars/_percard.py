"""Helpers for per-card-master characters (each whole-figure card is its own master, painted brads kept,
painted head and hands kept, master scale pinned to 1).  Used by the father (02, 09), the poem-13 cafe
couples and their pair cards, the poem-13 elders, the woman in red and the street-clothes man.

A card can hold two figures: `keep` (a polygon round one figure) cuts the partner away before the layer
cut, so a two-figure card can serve as one figure's master (its target in that character's marker
supplement carries only that figure's markers).

builder(char, pid, ...) returns a master builder fn(rgb, alpha) -> spec:
  cut   : polygons removed from the card (a caption, a chair, the partner's overlapping hand)
  keep  : polygon; everything outside it is removed (the partner on a two-figure card)
  head  : polygon of the hand-cut head (down to the collar); `seat` is the polyline of its bottom cut
          (no paper edge drawn there; the torso keeps a few px under it)
  give  : [(layer name, polygon)] painted pixels inside the polygon move to that layer (a hand the
          automatic cut split, a skirt the legs took, ...)
  far_empty : the far arm is hidden in the painting: its layer keeps only `far_keep` (or nothing but a
          speck), the visible arm takes the rest
"""
import json, os
import numpy as np, cv2

from .. import auto, core

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}
VIEWS = ('front', '3qR', '3qL', 'profR', 'profL', 'back', 'back3qR', 'back3qL')


def poly_mask(shape, poly):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.array(poly, np.int32)], 1)
    return m > 0


def raw_markers(files, fix, pid):
    """a card's markers from the raw marker files with the module's fixes (no load_markers at import)"""
    out = None
    for f in files:
        for t in json.load(open(os.path.join(core.ROOT, f)))['targets']:
            if t['id'] == pid:
                out = dict(t['markers'])
    for k, (x, y) in fix.get(pid, {}).items():
        out[k] = [float(x), float(y)] + list(out.get(k, [0, 0, 1.0, 'fix', 1.0])[2:4]) + [1.0]
    return out


def self_scale(m):
    """the solver's scale for a card posed on itself (posing.solve_body): median of torso (1), legs and
    arms ratios, each the longer side over the mean of both"""
    L = lambda a, b: float(np.hypot(m[a][0] - m[b][0], m[a][1] - m[b][1]))
    legs = [L('hip' + s, 'knee' + s) + L('knee' + s, 'ankle' + s) for s in 'RL']
    arms = [L('shoulder' + s, 'elbow' + s) + L('elbow' + s, 'wrist' + s) for s in 'RL']
    return float(np.median([1.0, max(legs) / (sum(legs) / 2), max(arms) / (sum(arms) / 2)]))


def own_paint(S, rgb):
    """the torso and legs keep the painted pixels wherever the figure is painted (each card is its own
    master); painted pixels no layer took go to the torso"""
    fig = S['fig']
    for L in S['layers']:
        if L['bones'] == 'torso' or L['name'] == 'legs':
            L['rgb'] = np.where(fig[..., None], rgb, L['rgb'])
    return lost_to_torso(S)


def lost_to_torso(S):
    fig = S['fig']
    owned = np.zeros(fig.shape, bool)
    for L in S['layers']:
        owned |= L['alpha'] > 0.5
    for L in S['layers']:
        if L['bones'] == 'torso':
            L['alpha'] = np.where(fig & ~owned, 1.0, L['alpha']).astype(np.float32)
    return S


def torso_scraps(S, rgb):
    """small torso pieces detached from its main body (a sliver of sleeve beyond the arm's width, a gap
    between the knees) go to the layer that surrounds them most, so they do not ride the chest"""
    tor = [L for L in S['layers'] if L['bones'] == 'torso'][0]
    n, lab, st, _ = cv2.connectedComponentsWithStats((tor['alpha'] > 0.5).astype(np.uint8))
    if n <= 2:
        return S
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    for i in range(1, n):
        if i == big or st[i, cv2.CC_STAT_AREA] > 0.05 * st[big, cv2.CC_STAT_AREA]:
            continue
        comp = lab == i
        ring = (cv2.dilate(comp.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0) & ~comp
        best, bv = None, 0
        for L in S['layers']:
            if L is tor or L.get('is_head'):
                continue
            v = float((L['alpha'][ring] > 0.5).sum())
            if v > bv:
                best, bv = L, v
        if best is not None:
            best['alpha'] = np.where(comp, 1.0, best['alpha']).astype(np.float32)
            best['rgb'] = np.where(comp[..., None], rgb, best['rgb'])
            tor['alpha'] = np.where(comp, 0, tor['alpha']).astype(np.float32)
    return S


def warm(rgb):
    """a wooden cane, a brass handle: warm saturated pixels"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    return (r - b > 35) & (r > 60)


def give(S, rgb, name, poly, pred=None, fill=None):
    """painted pixels inside poly (and pred(rgb), if given) belong to layer `name` only.  fill: the name
    of a layer that lay under them (a coat under a cane): it keeps them, inpainted from its own pixels
    around, where they are inside its closed outline"""
    m = poly_mask(S['fig'].shape, poly) & S['fig']
    if pred is not None:
        m &= pred(rgb)
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
        m = (cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & poly_mask(S['fig'].shape, poly) & S['fig']
    if fill:
        for L in S['layers']:
            if L['name'] == fill:
                own = (L['alpha'] > 0.5) & ~m
                hull = cv2.morphologyEx(own.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)) > 0
                under = m & hull
                L['rgb'] = auto.inpaint(np.asarray(L['rgb'], np.float32), under, own & S['fig'])
                L['alpha'] = np.where(under, 1.0, np.where(m, 0, L['alpha'])).astype(np.float32)
                L['edgeok'] = np.where(under, 0.0, L['edgeok']).astype(np.float32)
                L['_keep'] = under
    for L in S['layers']:
        if L['name'] == name:
            L['alpha'] = np.maximum(L['alpha'], m.astype(np.float32))
            L['rgb'] = np.where(m[..., None], rgb, L['rgb'])
            L['edgeok'] = np.where(m, 1.0, L['edgeok']).astype(np.float32)
        elif L['name'] != fill:
            L['alpha'] = np.where(m, 0, L['alpha']).astype(np.float32)
        L.pop('_keep', None)
    return S


def seg_dist_map(shape, pts):
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    d = np.full(shape, 1e9, np.float32)
    for a, b in zip(pts[:-1], pts[1:]):
        d = np.minimum(d, auto.seg_d(xx, yy, np.array(a, float), np.array(b, float)))
    return d


def hand_head(S, rgb, poly, seat, band=5):
    """the head layer is the hand-cut head; the other layers lose it, except a band of `band` px above
    the seat line kept by the torso (under the head, so a turned head shows cloth, not a hole).  No paper
    edge along the seat."""
    fig = S['fig']
    hm = poly_mask(fig.shape, poly) & fig
    ds = seg_dist_map(fig.shape, seat)
    for L in S['layers']:
        if L.get('is_head'):
            L['rgb'] = rgb.copy()
            L['alpha'] = hm.astype(np.float32)
            L['edgeok'] = (ds > 3).astype(np.float32)
        elif L['bones'] == 'torso':
            L['alpha'] = np.where(hm & (ds > band), 0, L['alpha']).astype(np.float32)
            L['alpha'] = np.where(hm & (ds <= band), 1.0, L['alpha']).astype(np.float32)
            L['rgb'] = np.where(hm[..., None], rgb, L['rgb'])
        else:
            L['alpha'] = np.where(hm, 0, L['alpha']).astype(np.float32)
    return S


def far_arm_hidden(S, rgb, far, keep=None):
    """the far arm is hidden behind the body or the near arm: its layer keeps only `keep` (a polygon of
    what is truly visible of it, or nothing); the pixels it took go back to the torso / near arm"""
    fig = S['fig']
    km = poly_mask(fig.shape, keep) if keep else np.zeros(fig.shape, bool)
    near = 'L' if far == 'R' else 'R'
    J, T = S['joints'], S['T']
    yy, xx = np.mgrid[0:fig.shape[0], 0:fig.shape[1]].astype(np.float32)
    dN = np.minimum.reduce([auto.seg_d(xx, yy, np.array(J[a + near]), np.array(J[b + near]))
                            for a, b in (('sh', 'el'), ('el', 'wr'), ('wr', 'tip'))])
    dS = np.hypot(xx - J['sh' + near][0], yy - J['sh' + near][1])
    gone = np.zeros(fig.shape, bool)
    for L in S['layers']:
        if L['name'] == 'arm' + far:
            gone = (L['alpha'] > 0.5) & ~km
            L['alpha'] = np.where(km & fig, 1.0, 0.0).astype(np.float32)
    # what it took along the visible arm (beyond the shoulder) goes to the near arm, the rest to the torso
    to_near = gone & (dN < 0.3 * T) & (dS > 0.15 * T)
    for L in S['layers']:
        if L['name'] == 'arm' + near:
            L['alpha'] = np.where(to_near, 1.0, L['alpha']).astype(np.float32)
            L['rgb'] = np.where(to_near[..., None], rgb, L['rgb'])
    return lost_to_torso(S)


def fill_under_arms(S, rgb, k=0.2):
    """arm pixels lying inside the torso's closed outline: the torso keeps them too, inpainted from its
    own cloth round them (an arm moved off the coat shows coat, not a hole)"""
    tor = [L for L in S['layers'] if L['bones'] == 'torso'][0]
    own = tor['alpha'] > 0.5
    if k == 'hull':     # the torso's convex hull (an arm hanging beside a coat: the coat's side runs behind it)
        ys, xs = np.nonzero(own)
        hull = np.zeros(own.shape, np.uint8)
        cv2.fillConvexPoly(hull, cv2.convexHull(np.stack([xs, ys], 1).astype(np.int32)), 1)
        hull = hull > 0
    else:
        r = int(k * S['T']) | 1
        hull = cv2.morphologyEx(own.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (r, r))) > 0
    under = np.zeros(own.shape, bool)
    for L in S['layers']:
        if L['name'].startswith('arm'):
            under |= (L['alpha'] > 0.5) & hull & ~own
    if under.any():
        tor['rgb'] = auto.inpaint(np.asarray(tor['rgb'], np.float32), under, own & S['fig'])
        tor['alpha'] = np.where(under, 1.0, tor['alpha']).astype(np.float32)
    return S


def prop_bone(S, side, end):
    """a long prop held in the hand (a cane): its far end is a joint on the hand bone, so the whole prop is
    skinned rigidly to the hand instead of half to the forearm"""
    S['joints'] = dict(S['joints'], **{'prop' + side: tuple(float(v) for v in end)})
    for L in S['layers']:
        if L['name'] == 'arm' + side:
            L['bones'] = dict(L['bones'])
            L['bones']['hand' + side] = list(L['bones']['hand' + side]) + [('wr' + side, 'prop' + side)]
    return S


def builder(char, pid, cut=(), keep=None, head=None, seat=None, give_=(), far_hidden=None, far_keep=None, plain=None,
            opts=None, border=None, post=None, prop_ends=None, fill_arms=None):
    def fn(rgb, a):
        a = a.copy()
        if keep is not None:
            a[~poly_mask(a.shape, keep)] = 0
        for p in cut:
            a[poly_mask(a.shape, p)] = 0
        m = core.load_markers(char)[pid]['markers']
        S = auto.build_auto(rgb, a, m, plain_fn=plain, erase_emblem=False, **(opts or {}))
        S['brads'] = []                 # painted brads stay painted (each card is its own master)
        if border is not None:
            S['border'] = border
        S = own_paint(S, rgb)
        if far_hidden:
            S = far_arm_hidden(S, rgb, far_hidden, far_keep)
        for g in give_:
            S = give(S, rgb, *g)
        for side, end in (prop_ends or {}).items():
            S = prop_bone(S, side, end)
        if fill_arms:
            S = fill_under_arms(S, rgb, fill_arms)
        if head is not None:
            S = hand_head(S, rgb, head, seat)
        if post:
            S = post(S, rgb, a, m)
        return torso_scraps(lost_to_torso(S), rgb)
    return fn


def finish(mod, masters, notes, costume, gaze=None, extra_flags=None):
    """fill a per-card module's catalog, flags, rigs and KEYS.  masters: {view: (pid, builder, facing,
    catalog view, posture)}"""
    mod.MASTERS = {v: (pid, fn) for v, (pid, fn, _, _, _) in masters.items()}
    mod.MASTER_FACING = {v: f for v, (_, _, f, _, _) in masters.items()}
    first = next(iter(masters))
    mod.VIEW_RIGS = {v: (first, False) for v in VIEWS}
    mod.POSTURE_RIGS = {}
    mod.BACK_RIGS = ()
    mod.DEPTH = DEPTH
    mod.CURATED_PARTS = {}
    mod.SCALE_PRIOR = False
    files = mod.MARKER_FILES
    fix = getattr(mod, 'MARKER_FIX', {})
    mod.KEYS = {}
    cat = {}
    for v, (pid, _, _, cv, cls) in masters.items():
        s = self_scale(raw_markers(files, fix, pid))
        # 'scale' pins each master onto its own painting (the solver's median limb ratio on a card
        # against itself is s, not 1)
        mod.KEYS[pid] = {'view': v, 'head': None, 'hands': {}, 'scale': 1 / s}
        cat[pid] = dict(costume=costume, use='ok', view=cv, cls=cls, props=[], hands='', gaze=(gaze or {}).get(v, ''),
                        note=notes[v])
    mod.catalog = lambda: cat
    mod.is_character_painting = lambda tid, c: tid in c
    ef = extra_flags or {}

    def painting_flags(tid, c):
        if tid not in c:
            return ['painting not in this character\'s catalog']
        return [c[tid]['note'], '("no usable head" / "hand ...: rig master hand" below: none is swapped in; each card is '
                'its own master and keeps its own painted head and hands)'] + ef.get(tid, [])
    mod.painting_flags = painting_flags
