"""grow_extremity (round 03). Hypothesis: the clutter of hands and wrist tabs over the joints (about 32 pieces per body
in grow_search / grow_clean) comes from the cheap ends phase filling interior pockets; restricting the ends phase to
free brads at the body's extremities (geodesic distance from the figure's deepest cell in the top 30%: hands, feet,
head) keeps the fill of fingers and toes and drops the clutter. Plus the program search (60 s)."""
from . import grow_clean as _c


def assemble(target, library, seed):
    return _c.run(target, seed, 'grower_extremity', {'ends_extremity': .7}, search=60)
