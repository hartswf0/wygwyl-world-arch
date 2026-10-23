"""grow_appear_search (round 03). Hypothesis: appearance agreement made the most coherent bodies (best CLIP, fewest
stray hands) but lost coverage (79%) because the -0.3 floor rejects any cloth that differs from the reference;
a floor of 0 (disagreeing paint simply earns nothing) plus the program search (60 s) regains coverage while keeping
the coherence. Otherwise grow_clean (hygiene, head rule, multi-joins, ends phase, settle)."""
from . import grow_clean as _c


def assemble(target, library, seed):
    return _c.run(target, seed, 'grower_appear0', {'appear': True, 'appear_floor': 0.}, search=60)
