"""grow (seed population): growth from a seed with brad snapping (puzzle/grow.py). Seed = the largest piece with
>= 2 brads that fits the figure core; every later piece snaps one of its brads onto a free brad of the body. Greedy
growth program (rank 0 at every step) from the 3 best seeds; the fittest body is kept. One component by construction."""
import time
from evolve.puzzle import grow as GR

SEEDS = 3
BUDGET = 90


def grower(ctx, seed):
    if 'grower' not in ctx:
        ctx['grower'] = GR.Grower(ctx['char'], ctx['costume'], ctx['id'], seed=seed, ctx=ctx)
    return ctx['grower']


def best_body(ctx, seed, budget=BUDGET):
    g = grower(ctx, seed)
    t0 = time.time()
    best = None
    for s in g.seeds(SEEDS):
        if best is not None and time.time() - t0 > budget:
            break
        st, prog = g.decode((s[1], s[2]), [])
        f = g.fitness(st)[0]
        if best is None or f > best[0]:
            best = (f, st, (s[1], s[2]), prog)
    return g, best


def to_asm(g, st, Ms=None, alive=None):
    Ms = Ms if Ms is not None else GR.full_affines(g, st)
    alive = sorted(alive) if alive is not None else list(range(len(st.placed)))
    idx = {o: i for i, o in enumerate(alive)}
    pieces = [{'pi': g.V[st.placed[o]['vi']]['pi'], 'M': Ms[o].tolist()} for o in alive]
    edges = []
    for a, ab, b, bb in st.snaps:
        if a in idx and b in idx:
            edges.append([idx[a], int(ab), idx[b], int(bb)])
    return {'pieces': pieces, 'edges': edges}


def assemble(target, library, seed):
    g, best = best_body(target, seed)
    if best is None:
        return {'pieces': [], 'edges': [], 'info': {'error': 'no seed fits'}}
    asm = to_asm(g, best[1])
    asm['info'] = {'program': best[3], 'seed_vi': best[2][0]}
    return asm
