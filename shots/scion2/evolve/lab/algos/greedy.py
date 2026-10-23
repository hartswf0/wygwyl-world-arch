"""greedy (seed population): the blind greedy fill. Largest-gain shape first, no overflow at work resolution,
prune / re-place / merge local search, full-resolution refine. No joints: every piece is its own component."""
from evolve.puzzle import fill as FL

BUDGET = 60
MODE = 'blind'


def assemble(target, library, seed):
    ctx = target
    if 'V_fill' not in ctx:
        ctx['V_fill'] = FL.build_variants(library, ctx['t'])
    zones = None
    if MODE == 'prior':
        from evolve.puzzle import zones as ZN
        zones = ZN.load()
    r = FL.fill(ctx['char'], ctx['costume'], ctx['id'], mode=MODE, zones=zones, budget_s=BUDGET, seed=seed, ctx=ctx)
    t = ctx['t']
    return {'pieces': [{'pi': p['pi'], 'M': FL.full_M(p, library[p['pi']], t).tolist()} for p in r['_P']], 'edges': [],
            'info': {'mode': MODE}}
