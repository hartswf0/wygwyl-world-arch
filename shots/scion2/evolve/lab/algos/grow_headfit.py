"""grow_headfit (round 03). Hypothesis (critic: head wrong 10/12): the forced head is chosen by coverage anywhere, so
it lands as a fragment or a side face; scoring the forced head only on the uncovered cells within 13 cm of the
reference's head marker puts one head where the head is. Also: if the grown body already holds a head piece that
covers less than half the head region, it is still forced. Plus extremity ends and search as grow_extremity."""
from . import grow_clean as _c


def assemble(target, library, seed):
    return _c.run(target, seed, 'grower_headfit', {'ends_extremity': .7, 'head_fit': True}, search=60)
