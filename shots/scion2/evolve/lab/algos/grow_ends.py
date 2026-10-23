"""grow_ends (round 02). Hypothesis: hands, feet and the head outline stay blue because a small piece cannot pay the
piece cost (0.5% of the figure); after the main growth, a second phase at 0.3x the piece cost lets small pieces
attach to free brads at the extremities. Multi-joins as grow_multijoin."""
import time
from evolve.puzzle import grow as GR
from . import grow as _g

OPTS = {'max_joins': 3, 'ends': .3}


def assemble(target, library, seed):
    key = 'grower_ends'
    if key not in target:
        target[key] = GR.Grower(target['char'], target['costume'], target['id'], seed=seed, ctx=target, opts=OPTS)
    g = target[key]
    best = None
    for s in g.seeds(_g.SEEDS):
        st, prog = g.decode((s[1], s[2]), [])
        f = g.fitness(st)[0]
        if best is None or f > best[0]:
            best = (f, st, prog)
    if best is None:
        return {'pieces': [], 'edges': [], 'info': {'error': 'no seed fits'}}
    Ms, masks, alive = GR.settle(g, best[1], time.time() + 60)
    asm = _g.to_asm(g, best[1], Ms, alive)
    asm['info'] = {'program': best[2], 'opts': OPTS}
    return asm
