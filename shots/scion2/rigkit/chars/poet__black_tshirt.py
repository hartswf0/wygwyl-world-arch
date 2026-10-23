"""The poet in the black t-shirt and black jeans (poems 01-03): bare brown arms, brass brads.

Masters (cut automatically from their Pose Lab markers, rigkit/auto.py):
  front : poet.01.main-poses/read-the                (front, standing, a page in both hands)
  q3r   : poet.03.main-poses/poet-follows-the        (3/4 to screen right, walking)
  back  : poet.03.main-poses/two-backs-out-of-step-1 (back, walking; his only back view)
  sit   : poet.02.main-poses/sit-up-awake-2          (front, on the bed edge, head in hand; bed cut away)
  lie   : poet.02.main-poses/turn-threequarter       (reclined on an elbow, to screen left)
Markers: shots/rig/poses/poet__black_tshirt.json (solve.py) + .supplement.json (MoveNet, two cards
from poet.01.action.black_tshirt.parts.02).  Five EX paintings that solve.py keyed to this poet
(they sit on poet.0x sheets) are excluded here: they live in ex__ex_jacket.json.
"""
import numpy as np, cv2

from .. import auto, core

CHAR = 'poet__black_tshirt'
MARKER_FILES = ['shots/rig/poses/poet__black_tshirt.json', 'shots/rig/poses/poet__black_tshirt.supplement.json']
EXCLUDE_TARGETS = {
    'poet.01.main-poses/fall-reach-back-2': 'the EX (olive bomber), see cast/ex__ex_jacket',
    'poet.02.main-poses/ex-writhes': 'the EX (olive bomber), see cast/ex__ex_jacket',
    'poet.03.main-poses/two-backs-out-of-step-2': 'the EX (olive bomber), see cast/ex__ex_jacket',
    'poet.03.main-poses/ex-keeps-going': 'the EX (olive bomber), see cast/ex__ex_jacket',
    'poet.03.main-poses/part-2': 'the EX (olive bomber), see cast/ex__ex_jacket',
    'poet.03.main-poses/part': 'not a figure: a fragment of ruled lines (catalog "frag"); its markers are noise',
}

# marker corrections (card px) where solve.py's markers are off the painting
MARKER_FIX = {
    # hips were put on the jeans' waistband and the far shoulder on the neck
    'poet.01.main-poses/trip-at-parquet-hole-2': {'hipR': (218, 88), 'hipL': (212, 86), 'groin': (214, 92),
                                                  'shoulderL': (300, 40)},
}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


def _cut(a, polys):
    a = a.copy()
    m = np.zeros(a.shape, np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    a[m > 0] = 0
    return a


def build_sit(rgb, a):
    """sit-up-awake-2: the bed (white mattress, wooden frame and legs) is cut away, then auto."""
    H, W = a.shape
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    light = (mn > 125) & (mx - mn < 50)
    light = cv2.dilate(light.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    skin = (r > g + 12) & (g > b + 15) & (r > 70) & (r < 230)
    yy, xx = np.mgrid[0:H, 0:W]
    hand = (xx > 200) & (xx < 262) & (yy > 195) & (yy < 285)
    mid = (xx > 150) & (xx < 315) & (yy > 200) & (yy < 300)     # the mattress showing between his legs
    a = a.copy()
    a[light & mid & ~(skin & hand)] = 0
    a = _cut(a, BED_POLYS)
    S = auto.build_auto(rgb, a, _mk(MASTERS['sit'][0]), **AUTO_OPTS)
    return S


# card px of sit-up-awake-2: mattress blocks either side of his legs, the frame between them, the bed legs
BED_POLYS = [
    [(0, 195), (113, 195), (113, 338), (0, 338)],
    [(361, 195), (450, 195), (450, 338), (361, 338)],
    [(163, 296), (307, 296), (307, 342), (163, 342)],
    [(0, 338), (74, 338), (74, 410), (0, 410)],
    [(409, 338), (450, 338), (450, 410), (409, 410)],
]

def auto_view(view, **extra):
    """the auto cut with this character's options plus per-view extras (split_legs for 3/4 strides)"""
    return lambda rgb, a: auto.build_auto(rgb, a, _mk(MASTERS[view][0]), **dict(AUTO_OPTS, **extra))


def build_front(rgb, a):
    """read-the: his hands hold a page over his chest, so hands are not grown by skin here"""
    return auto.build_auto(rgb, a, _mk(MASTERS['front'][0]), **dict(AUTO_OPTS, hand_skin=False))


# bare hands with long fingers; clean the torso of skin scraps and sleeve slivers
AUTO_OPTS = {'tip_len': 0.36, 'open_torso': 0.12, 'hand_skin': True, 'torso_over_legs': False}

MASTERS = {
    'front': ('poet.01.main-poses/read-the', build_front),
    'q3r': ('poet.03.main-poses/poet-follows-the', auto_view('q3r', split_legs=True)),
    'back': ('poet.03.main-poses/two-backs-out-of-step-1', 'auto'),
    'sit': ('poet.02.main-poses/sit-up-awake-2', build_sit),
    'lie': ('poet.02.main-poses/turn-threequarter', auto_view('lie', split_legs=True)),
}
MASTER_FACING = {'front': None, 'q3r': 'R', 'back': None, 'sit': None, 'lie': 'L'}
BACK_RIGS = ('back',)
# a clean brass brad: read-the's right knee (painting, cx, cy, brass r, sprite r)
BRAD_SOURCE = ('poet.01.main-poses/read-the', 59.0, 292.4, 6.0, 7.5)


def catalog():
    """H2's hand reading of the poet.01-03 sheets (../h2/tools/catalog_src.py) plus the two
    supplement cards it never saw."""
    import importlib.util, os
    p = os.path.join(os.path.dirname(__file__), '..', '..', 'h2', 'tools', 'catalog_src.py')
    spec = importlib.util.spec_from_file_location('h2catalog', p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    keys = ('costume', 'use', 'view', 'cls', 'props', 'hands', 'gaze', 'note')
    out = {k: dict(zip(keys, v)) for k, v in m.C.items() if k.startswith(('poet.01.', 'poet.02.', 'poet.03.'))}
    out.update({k: dict(zip(keys, v)) for k, v in SUPPLEMENT.items()})
    return out


SUPPLEMENT = {
    'poet.01.action.black_tshirt.parts.02/run-threequarter': ('tshirt', 'ok', '3qR', 'run', [], 'fists', 'side', 'running'),
    'poet.01.action.black_tshirt.parts.02/noet': ('tshirt', 'ok', '3qR', 'fall', [], 'open-up', 'up', 'falling back, arms up'),
}


def is_character_painting(tid, cat):
    c = cat.get(tid)
    return c is not None and c['costume'] == 'tshirt' and c['use'] in ('ok', 'crop', 'label')


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return []
    out = []
    if c['use'] in ('frag', 'empty', 'multi', 'ghost'):
        out.append('painting is a %s (%s), markers unreliable' % (c['use'], c.get('note', '')))
    if c['use'] == 'label':
        out.append('painting carries a printed label (%s); props (%s) not in the rig' % (c.get('note', ''), ', '.join(c['props'])))
    elif c['props']:
        out.append('props not in the rig: ' + ', '.join(c['props']))
    return out + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {
    'poet.01.main-poses/trip-at-parquet-hole-2': ['near-profile pose on the 3/4 rig: shoulders stay too wide, so the near arm '
                                                  'rises over his face; the back foot is oversized'],
    'poet.02.main-poses/silent-scream': ['near thigh lifted far from the master: a notch shows between the shirt hem and the thigh'],
    'poet.02.main-poses/poet-02-main-poses-every-working-body-part-and-p': ['palms on the mirror come out as the rig\'s loose fists '
                                                                          '(the own hand cuts carry mirror glass)'],
    'poet.03.main-poses/poet-turns-back': ['torso turn is not reachable (a swap, not a turn): seams show at the near thigh'],
    'poet.02.main-poses/turn-threequarter': ['two stray skin specks below the right hand (auto cut leftovers)'],
    'poet.02.main-poses/sit-up-awake': ['under the sheet in the painting: legs are guessed by the markers, no sheet in the rig'],
}
CURATED_PARTS = {}
POSTURE_RIGS = {'sit': 'sit', 'lie': 'lie'}
VIEW_RIGS = {'front': ('front', False), '3qR': ('q3r', False), '3qL': ('q3r', True), 'profR': ('q3r', False),
             'profL': ('q3r', True), 'back': ('back', False), 'back3qR': ('back', False), 'back3qL': ('back', False)}
# these cards are cut flush with the head, so the automatic head check (cut by the sheet edge)
# refuses them; the heads are whole, use them
_OWN_HEAD = ['poet.03.main-poses/poet-follows-the', 'poet.01.action.black_tshirt.parts.02/run-threequarter',
             'poet.01.action.black_tshirt.parts.02/noet', 'poet.01.main-poses/search-drawer-hall']
KEYS = {t: {'head': [t + '#head', False]} for t in _OWN_HEAD}
# the master's own painted hands hold the page; the skin-only hand cut would tear it
KEYS['poet.01.main-poses/read-the'] = {'hands': {}}
# own hand cuts that take a piece of the prop with them (window frame, mirror): the rig's hand instead
# (its own head cut also takes a sliver of the reaching arm under the chin: shoulder-2's profile head)
KEYS['poet.01.main-poses/reach-window'] = {'hands': {'R': ['poet.01.main-poses/reach-window#handR', False]},
                                           'head': ['poet.01.main-poses/shoulder-2#head', False]}
KEYS['poet.02.main-poses/poet-02-main-poses-every-working-body-part-and-p'] = {'hands': {}}
# its own head cut takes a corner of the pillow and his shoulder brad: the lie master's head
KEYS['poet.02.main-poses/sit-up-awake'] = {'head': ['poet.02.main-poses/turn-threequarter#head', False]}
KEYS['poet.01.main-poses/trip-at-parquet-hole-2'] = {'scale': 0.9}
# reclined in the air: the reclined (lie) master, mirrored, fits it better than the walking 3/4
KEYS['poet.01.action.black_tshirt.parts.02/noet'] = dict(KEYS['poet.01.action.black_tshirt.parts.02/noet'], view='lie_m')
