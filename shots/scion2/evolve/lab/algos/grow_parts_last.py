"""grow_parts_last (round 03). Hypothesis: heads and hands go wrong because they compete with cloth during growth;
grow the body from cloth cards only (identity-gated), then place exactly one head (head region), one hand at each
wrist end and one boot at each ankle end, each the appearance-best card of its class snapped at a free brad.
A body missing any of the five is marked invalid (info.valid). No ends phase (the ends are the parts)."""
from . import grow_clean as _c


def assemble(target, library, seed):
    return _c.run(target, seed, 'grower_parts_last', {'identity': True, 'parts_last': True, 'appear': True, 'appear_floor': 0.,
                                                      'ends': None}, search=60)
