"""grow_settle (seed population): grow, then the swarm settle at full resolution: each piece rotated (+-3/6 deg) and
scaled (+-4%) about its joint to its parent, carrying its subtree, kept when coverage rises with no new overflow; a
piece still overflowing has its subtree cut (the body stays one component)."""
import time
from evolve.puzzle import grow as GR
from . import grow as _g


def assemble(target, library, seed):
    g, best = _g.best_body(target, seed)
    if best is None:
        return {'pieces': [], 'edges': [], 'info': {'error': 'no seed fits'}}
    st = best[1]
    Ms, masks, alive = GR.settle(g, st, time.time() + 60)
    asm = _g.to_asm(g, st, Ms, alive)
    asm['info'] = {'program': best[3]}
    return asm
