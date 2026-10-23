"""grow_appear (round 02). Hypothesis (critic round 01: wrong body part substituted 11/12 -- pure shape cannot tell a
hand from a foot): score each attachment by appearance agreement as well as shape -- a covered cell counts fully when
the piece's paint there is within dE 30 (CIE-Lab, work resolution) of the reference's local colour, 25% otherwise.
Skin lands on skin, boot leather on boots, jacket on jacket. The reference is only a guide; no pixel is copied.
Otherwise grow_clean (hygiene, head rule, multi-joins, ends phase, settle)."""
from . import grow_clean as _c


def assemble(target, library, seed):
    return _c.run(target, seed, 'grower_appear', {'appear': True})
