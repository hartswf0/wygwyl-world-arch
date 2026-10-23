"""greedy_prior (seed population): the greedy fill with the learned zone prior (puzzle/zones.json): uncovered cells
of a zone are worth +35% to pieces that have learned that zone. No joints."""
from . import greedy as _g
from .greedy import FL  # noqa: F401


def assemble(target, library, seed):
    _g.MODE = 'prior'
    try:
        return _g.assemble(target, library, seed)
    finally:
        _g.MODE = 'blind'
