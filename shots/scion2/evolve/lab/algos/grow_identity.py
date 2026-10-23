"""grow_identity (round 03). Hypothesis (critic round 02: hands as feet or knees 11/12, head replaced 12/12): pure shape
lets the 207 hand cards fill any small pocket; gating by learnt identity -- a head / hand / foot card (Skin Lab part
classifier, confidence >= 0.6) pays -2 for every cell outside its skeleton zones, unsure cards are cloth and pay
outside the cloth zones -- stops hands landing on knees. With appearance (floor 0), multi-joins, extremity ends,
the head rule, search 60 s."""
from . import grow_clean as _c


def assemble(target, library, seed):
    return _c.run(target, seed, 'grower_identity', {'identity': True, 'appear': True, 'appear_floor': 0., 'ends_extremity': .7}, search=60)
