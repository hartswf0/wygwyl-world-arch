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
    return o


def run(target, seed, key, extra=None):
    if key not in target:
        target[key] = GR.Grower(target['char'], target['costume'], target['id'], seed=seed, ctx=target, opts=opts_for(target, extra))
    g = target[key]
    best = None
    for s in g.seeds(_g.SEEDS):
        st, prog = g.decode((s[1], s[2]), [])
        f = g.fitness(st)[0]
        if best is None or f > best[0]:
            best = (f, st, prog)
    if best is None:
        return {'pieces': [], 'edges': [], 'info': {'error': 'no seed fits'}}
    st = best[1]
    forced = None
    if g.heads and not any(g.V[p['vi']]['pi'] in g.heads for p in st.placed):
        st2, ch = g.force(st, g.heads)                 # one head, even if it does not pay for itself in coverage
        if ch is not None:
            st, forced = st2, g.pieces[g.V[ch[1]]['pi']]['id']
    Ms, masks, alive = GR.settle(g, st, time.time() + 60)
    asm = _g.to_asm(g, st, Ms, alive)
    asm['info'] = {'program': best[2], 'allowed': len(g.allowed), 'heads': len(g.heads), 'forced_head': forced}
    return asm


def assemble(target, library, seed):
    return run(target, seed, KEY)
