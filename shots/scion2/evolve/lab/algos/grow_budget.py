"""grow_budget (round 03). Hypothesis: Q rose while the critic did not because more pieces = more tabs and hands piled
on joints; doubling the piece cost (each piece must fill 1% of the figure) and dropping the ends phase gives 15-20
pieces, with appearance (floor 0) keeping grow_appear's colour coherence. Identity-gated, parts placed last."""
from . import grow_clean as _c


def assemble(target, library, seed):
    return _c.run(target, seed, 'grower_budget', {'identity': True, 'parts_last': True, 'appear': True, 'appear_floor': 0.,
                                                  'ends': None, 'lam_scale': 2.}, search=60)
