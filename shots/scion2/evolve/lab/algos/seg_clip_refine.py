"""seg_clip_refine (round 03). seg_clip, then appearance-only local refinement: for each region, the 5 best cards are
each tried in the assembled body, and the one whose render over the region's box is closest by CLIP to the reference
region is kept."""
from . import seg_clip as _s


def assemble(target, library, seed):
    return _s.assemble(target, library, seed, refine=True)
