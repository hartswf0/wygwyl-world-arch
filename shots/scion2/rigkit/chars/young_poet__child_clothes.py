"""The YOUNG POET in his summer clothes (poem 13): striped tee, denim shorts, white socks, blue
canvas sneakers, bronze brads.

Only two whole-figure paintings exist, both on young_poet.13.main-poses and both leaning on a rail
with his chin in his hands; each is its own master (the rail is cut away):
  q3r  : strict-rail-lean  (profile to screen right, leaning on the rail)
  lean : lean              (3/4 to screen right, leaning on the rail, face to the viewer)
No standing, front or back painting of him exists (young_poet.child_clothes.body.* sheets are parts
only); nothing is invented.

Markers: shots/rig/poses/young_poet__child_clothes.json.  solve.py also keyed every card of
young_ghost.02.main-poses here by sheet alias; those are the PAJAMA boy (chars/young_poet__pajamas_
winter.py), the GHOST CHILD (ghost_child__ghost_nightclothes) and two cards with both children: all
excluded.  awe-face-proof is a head-and-shoulders face card (MoveNet's body markers are noise,
confidence < 0.1): excluded as a pose.
"""
import numpy as np, cv2

from .. import auto, core

CHAR = 'young_poet__child_clothes'
SHEET = 'young_poet.13.main-poses/'
G = 'young_ghost.02.main-poses/'
MARKER_FILES = ['shots/rig/poses/young_poet__child_clothes.json']
_PAJ = 'not this costume: the young poet in plaid winter PAJAMAS (poem 02), see cast/young_poet__pajamas_winter'
_GHO = 'not the young poet: the GHOST CHILD (pale nightgown, poem 02)'
_TWO = 'two figures on one card (the pajama boy and the ghost child): needs splitting before it can be rigged'
EXCLUDE_TARGETS = {
    G + '04-side-hug': _PAJ, G + '02-ghost-assembles-2': _PAJ, G + '06-wind-up-ghost-thins': _PAJ,
    G + '06-wind-up-ghost-thins-2': _PAJ,
    G + '02-ghost-assembles-1': _GHO, G + '06-wind-up-ghost-thins-1': _GHO,
    G + '04-side-hug-2': _TWO, G + '05-offer-take-tambourine': _TWO,
    SHEET + 'awe-face-proof': 'a face close-up (head and collar only), not a figure: its body markers are noise (confidence < 0.1)',
}

# marker corrections (card px): the forearms stand up from the rail to the hands under his chin
MARKER_FIX = {
    SHEET + 'strict-rail-lean': {'elbowR': (228, 290), 'wristR': (245, 205), 'wristL': (292, 205)},
    SHEET + 'lean': {'elbowR': (247, 296), 'wristR': (240, 205), 'wristL': (330, 205)},
}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=7):
    """denim and tee: figure pixels well inside, not skin, not bronze"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    gold = (r > 110) & (r - b > 40) & (r > g + 10) & (g > 70)
    skin = (r > g + 12) & (g > b + 15) & (r > 70)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    near_gold = cv2.dilate(gold.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    return e & ~near_gold & ~skin


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


def _cut(a, polys):
    a = a.copy()
    m = np.zeros(a.shape, np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    a[m > 0] = 0
    return a


# a child: big head and thick limbs against a short torso (see young_poet__pajamas_winter)
AUTO_OPTS = {'tip_len': 0.3, 'torso_over_legs': False, 'head_win': (0.63, 1.3, 1.6, 0.20), 'limb_r': (0.2, 0.22)}


def auto_view(view, cut=None, **extra):
    def fn(rgb, a):
        a = _cut(a, cut or [])
        S = auto.build_auto(rgb, a, _mk(MASTERS[view][0]), plain_fn=PLAIN_FABRIC, **dict(AUTO_OPTS, **extra))
        # his bronze brads are bigger than the brad sprite's 25 px source window: they stay painted
        S['brads'] = []
        return own_torso(S, rgb)
    return fn


def own_torso(S, rgb):
    """every painted pixel the auto cut gave to no layer, or only to the torso's fill (his neck under
    his chin, the back of his big head outside the head window), is the torso's own painting; pixels
    the legs or the far arm (drawn under the torso) paint stay theirs"""
    fig = S['fig']
    painted = lambda L: (L['alpha'] > 0.5) & fig & (np.abs(L['rgb'] - rgb).sum(-1) < 1)
    names = [L['name'] for L in S['layers']]
    ti = next(i for i, L in enumerate(S['layers']) if L['bones'] == 'torso')
    under = np.zeros(fig.shape, bool)
    over = np.zeros(fig.shape, bool)
    for i, L in enumerate(S['layers']):
        if i < ti:
            under |= painted(L)
        elif i > ti:
            over |= painted(L)
    T = S['layers'][ti]
    own = fig & ~under & ~over
    T['rgb'] = np.where(own[..., None], rgb, T['rgb'])
    T['alpha'] = np.where(own, 1.0, np.where(under, 0.0, T['alpha'])).astype(np.float32)
    return S


# the rail: its top bar and its leg (card px)
RAIL_STRICT = [[(178, 317), (361, 317), (361, 349), (178, 349)], [(290, 345), (337, 345), (337, 741), (290, 741)]]
RAIL_LEAN = [[(192, 317), (469, 317), (469, 353), (192, 353)], [(393, 349), (447, 349), (447, 746), (393, 746)]]

MASTERS = {
    'q3r': (SHEET + 'strict-rail-lean', auto_view('q3r', RAIL_STRICT)),
    'lean': (SHEET + 'lean', auto_view('lean', RAIL_LEAN)),
}
MASTER_FACING = {'q3r': 'R', 'lean': 'R'}
BACK_RIGS = ()
# required by the rig builder; never drawn (his brads stay painted, see auto_view)
BRAD_SOURCE = (SHEET + 'lean', 175.1, 212.9, 6.0, 8.0)
SCALE_PRIOR = False

_C = {
    'strict-rail-lean': ('profR', 'lean', 'ok', 'leaning on a rail, chin in his hands; no rail in the rig'),
    'lean': ('3qR', 'lean', 'ok', 'leaning on a rail, chin in his hands; no rail in the rig'),
}


def catalog():
    return {SHEET + k: dict(costume='child', use=u, view=v, cls=c, props=[], hands='', gaze='side', note=n)
            for k, (v, c, u, n) in _C.items()}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the catalog']
    return [c['note']] + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {SHEET + k: ['("no usable head" below: none is swapped in; the rig draws its own painted head)'] for k in _C}
CURATED_PARTS = {}
POSTURE_RIGS = {}
VIEW_RIGS = {'front': ('lean', False), '3qR': ('lean', False), '3qL': ('lean', True), 'profR': ('q3r', False),
             'profL': ('q3r', True), 'back': ('lean', False), 'back3qR': ('lean', False), 'back3qL': ('lean', True)}
# each card is its own master: its rig's painted head and hands (the hands are under his chin, so a
# skin-only hand cut would take his face and the head cut his fingers)
KEYS = {SHEET + k: {'head': None, 'hands': {}} for k in _C}
