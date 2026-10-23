"""grow_search (round 02). Hypothesis: greedy growth commits early (the first big piece at a free brad blocks a limb);
searching the growth program (a (1+1) evolution per seed island: change the rank at one step, regrow everything after
it, keep if fitter) finds bodies that reach all limbs. Multi-joins and the ends phase as grow_ends."""
import random, time
from evolve.puzzle import grow as GR
from . import grow as _g

OPTS = {'max_joins': 3, 'ends': .3}
BUDGET = 60


def assemble(target, library, seed):
    key = 'grower_ends'
    if key not in target:
        target[key] = GR.Grower(target['char'], target['costume'], target['id'], seed=seed, ctx=target, opts=OPTS)
    g = target[key]
    rng = random.Random(seed)
    isl = []
    for s in g.seeds(_g.SEEDS):
        st, prog = g.decode((s[1], s[2]), [])
        isl.append([g.fitness(st)[0], (s[1], s[2]), prog, st])
    if not isl:
        return {'pieces': [], 'edges': [], 'info': {'error': 'no seed fits'}}
    t0, tries, wins = time.time(), 0, 0
    while time.time() - t0 < BUDGET:
        I = isl[tries % len(isl)]
        tries += 1
        prog = list(I[2])
        if not prog:
            continue
        k = rng.randrange(len(prog))
        prog = prog[:k] + [rng.choice([1, 1, 2, 3, 4])]
        st, used = g.decode(I[1], prog)
        f = g.fitness(st)[0]
        if f > I[0]:
            I[0], I[2], I[3] = f, used, st
            wins += 1
    best = max(isl, key=lambda x: x[0])
    Ms, masks, alive = GR.settle(g, best[3], time.time() + 60)
    asm = _g.to_asm(g, best[3], Ms, alive)
    asm['info'] = {'program': best[2], 'opts': OPTS, 'tries': tries, 'wins': wins}
    return asm
