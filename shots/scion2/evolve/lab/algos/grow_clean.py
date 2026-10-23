"""grow_clean (round 02). Hypotheses (critic round 01: junk content 8/12, head wrong 10/12):
  * a hygiene filter (puzzle/hygiene.py: CLIP zero-shot + pixel tests; captions, whole-figure thumbnails, single
    features, props, blank plates out) removes the junk the blind picker grabbed;
  * head rule: at most one head piece (a card the library files as a head), kept within 40 deg of upright, with a
    painted face (dark eye band) when the reference faces the camera and a back-of-head card for a back view; if growth
    ends with no head, the best-fitting head is attached at a free brad anyway (a body has one head).
    (CLIP's painted-face prompt was tried first and misread most painted heads as backs of heads: 26 of 84 at p<.05.)
Otherwise grow_ends (multi-joins, ends phase) + settle."""
import time
from evolve.puzzle import grow as GR, hygiene as HY
from . import grow as _g

BASE = {'max_joins': 3, 'ends': .3, 'max_heads': 1, 'head_rot': 40}
KEY = 'grower_clean'


def opts_for(ctx, extra=None):
    """hygiene (CLIP + pixel tests) for every piece; heads = cards the library or its learnt CLIP classifier calls a head;
    a front / side target takes only heads with a painted face (dark eye band, cards.py eyes_dark >= .06) not filed as a
    back view; a back target only heads filed as back views"""
    from evolve import cards as CD, library as LB
    C = HY.classify(ctx['pieces'])
    back = bool(ctx['t'].get('back'))
    lib = {c['id']: c for c in LB.cards(ctx['char'], ctx['costume'])}
    allowed, heads = set(), set()
    for i, p in enumerate(ctx['pieces']):
        r = C[p['id']]
        if HY.junk(r):
            continue
        c = lib.get(p['id'], {})
        if p['label'] == 'head':
            view = c.get('view')
            try:
                face = (CD.prep(c).eyes_dark or 0) >= .06
            except Exception:
                face = False
            isback = view in ('back', 'threequarter_back')
            if (back and not isback) or (not back and (isback or not face)):
                continue
            heads.add(i)
        allowed.add(i)
    o = dict(BASE, allowed=allowed, heads=heads)
    o.update(extra or {})
    if o.get('identity'):
        o['identity'] = identity(ctx, allowed)
    if o.get('parts_last'):
        pools = {c: {i for i in allowed if o['identity'].get(i) == c} for c in ('head', 'hand', 'foot')}
        pools['head'] = pools['head'] & heads if heads & pools['head'] else pools['head']
        o['pools'] = pools
        o['allowed'] = allowed - pools['head'] - pools['hand'] - pools['foot']
    return o


CONF = .6
CLASS = {'head': 'head', 'hand': 'hand', 'foot': 'foot', 'torso': 'cloth', 'pelvis': 'cloth', 'thigh': 'cloth', 'shin': 'cloth',
         'upper_arm': 'cloth', 'forearm': 'cloth'}


def identity(ctx, allowed):
    """piece -> head / hand / foot / cloth from the Skin Lab's learnt part classifier (clip_label.py: CLIP embedding +
    logistic regression; library.json clip.part, kept when part_p >= 0.6: at that confidence it agrees with the card's
    filing on 93% of 731 cards). Cards it is unsure of, and harvest cards (never classified), are 'cloth'."""
    from evolve import library as LB
    import json, os
    L = {c['id']: c for c in json.load(open(os.path.join(LB.SKIN, 'library.json')))}
    out = {}
    for i, p in enumerate(ctx['pieces']):
        cl = (L.get(p['id']) or {}).get('clip') or {}
        out[i] = CLASS.get(cl.get('part'), 'cloth') if cl.get('part_p', 0) >= CONF else 'cloth'
    return out


def run(target, seed, key, extra=None, search=0):
    if key not in target:
        target[key] = GR.Grower(target['char'], target['costume'], target['id'], seed=seed, ctx=target, opts=opts_for(target, extra))
    g = target[key]
    best = None
    isl = []
    for s in g.seeds(_g.SEEDS):
        st, prog = g.decode((s[1], s[2]), [])
        f = g.fitness(st)[0]
        isl.append([f, (s[1], s[2]), prog, st])
        if best is None or f > best[0]:
            best = (f, st, prog)
    if search and isl:                                  # (1+1) evolution of the growth program, as grow_search
        import random
        rng, t0, tries = random.Random(seed), time.time(), 0
        while time.time() - t0 < search:
            I = isl[tries % len(isl)]
            tries += 1
            if not I[2]:
                continue
            k = rng.randrange(len(I[2]))
            st, used = g.decode(I[1], I[2][:k] + [rng.choice([1, 1, 2, 3, 4])])
            f = g.fitness(st)[0]
            if f > I[0]:
                I[0], I[2], I[3] = f, used, st
        b = max(isl, key=lambda x: x[0])
        best = (b[0], b[3], b[2])
    if best is None:
        return {'pieces': [], 'edges': [], 'info': {'error': 'no seed fits'}}
    st = best[1]
    forced = None
    ends_missing = []
    if g.opts.get('parts_last'):
        # one head, a hand at each wrist end, a boot at each ankle end: each the best (by appearance when on) of its
        # class pool, snapped at a free brad, scored only on its own region
        a0 = g.allowed
        for reg, pool in (('head', 'head'), ('handL', 'hand'), ('handR', 'hand'), ('footL', 'foot'), ('footR', 'foot')):
            P_ = g.opts['pools'][pool]
            st2, ch = g.force(st, P_, g.end_regions[reg]) if P_ else (st, None)
            if ch is None:
                ends_missing.append(reg)
            else:
                st = st2
        g.allowed = a0

    def head_cover(st):
        import numpy as np
        c = np.zeros(g.shape, bool)
        for p in st.placed:
            v = g.V[p['vi']]
            if v['pi'] in g.heads:
                h_, w_ = v['m'].shape
                c[p['loc'][1]:p['loc'][1] + h_, p['loc'][0]:p['loc'][0] + w_] |= v['m'] > 0
        return (c & g.head_region).sum() / max(g.head_region.sum(), 1)
    need = not any(g.V[p['vi']]['pi'] in g.heads for p in st.placed)
    if g.opts.get('head_fit') and not need:
        need = head_cover(st) < .5
    if g.heads and need and not g.opts.get('parts_last'):
        if g.opts.get('head_fit'):            # the head slot is free again: other head pieces are not removed (a known gap)
            g.opts['max_heads'] = 2
        st2, ch = g.force(st, g.heads, g.head_region if g.opts.get('head_fit') else None)   # one head, even if it does not pay
        g.opts['max_heads'] = BASE['max_heads']
        if ch is not None:
            st, forced = st2, g.pieces[g.V[ch[1]]['pi']]['id']
    Ms, masks, alive = GR.settle(g, st, time.time() + 60)
    asm = _g.to_asm(g, st, Ms, alive)
    asm['info'] = {'program': best[2], 'allowed': len(g.allowed), 'heads': len(g.heads), 'forced_head': forced,
                   'ends_missing': ends_missing, 'valid': not ends_missing}
    return asm


def assemble(target, library, seed):
    return run(target, seed, KEY)
