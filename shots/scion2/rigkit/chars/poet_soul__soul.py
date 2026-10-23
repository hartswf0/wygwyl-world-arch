"""The POET'S SOUL (poem 08): a pale-blue acetate double of the poet in a zip jacket and boots,
with a RING for a head -- no face is painted and none is invented.  His joints are pale rivets
(not brass brads): they stay painted on the layers, so no brad sprite is drawn (BRAD_SOURCE is
set only because the rig builder needs one).

Masters (cut automatically from their Pose Lab markers, rigkit/auto.py):
  front : part-10            (front, standing, arms down)
  q3r   : stand-front        (3/4 to screen right, floating step, arms out)
  sit   : 05-ledge-sit-2     (seated on a ledge, seen from behind, legs to screen right; ledge cut away)
  kneel : part-4             (one knee down, an arm over the ring, shielding; markers re-placed by hand)
Markers: shots/rig/poses/poet_soul__soul.json (MoveNet).  Faceless, so MoveNet's L/R is by screen
side: L is screen-left on every card (part-4 was swapped; its markers are re-placed below).
06-return and part-9 on the soul's sheet are clipped halves of the POET (black tracksuit), not
the soul: excluded.
"""
import numpy as np, cv2

from .. import auto, core

CHAR = 'poet_soul__soul'
SHEET = 'poet_soul.08.main-poses/'
MARKER_FILES = ['shots/rig/poses/poet_soul__soul.json']
EXCLUDE_TARGETS = {
    SHEET + '06-return': 'not the soul: a clipped half of the POET (black tracksuit, red piping); see cast/poet__red_black_sunglasses',
    SHEET + 'part-9': 'not the soul: a 63 px clipped sliver of the POET (black tracksuit); markers are noise',
}

# marker corrections (card px)
_K = lambda **kw: {k: v for k, v in kw.items()}
MARKER_FIX = {
    # kneeling, one arm over the ring: MoveNet put the wrists on the ring and the head on an elbow
    # (all re-placed on the rivets and limbs; L = screen-left as on his other cards)
    SHEET + 'part-4': _K(shoulderL=(100, 76), elbowL=(77, 100), wristL=(148, 100), shoulderR=(190, 90), elbowR=(282, 75),
                         wristR=(214, 45), neck=(140, 82), chin=(150, 72), head=(160, 4), hipL=(86, 198), hipR=(150, 196),
                         groin=(118, 205), kneeL=(125, 303), ankleL=(50, 273), toeL=(8, 305), kneeR=(228, 182), ankleR=(204, 277),
                         toeR=(266, 330)),
    # seated from behind: MoveNet put both knees and both ankles on the near (screen-right) leg
    SHEET + '05-ledge-sit-2': _K(kneeL=(205, 262), ankleL=(221, 338), toeL=(228, 402), kneeR=(268, 238), ankleR=(293, 331),
                                 toeR=(345, 392), wristR=(213, 262)),
}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=7):
    """the pale-blue acetate: mid-tone blue pixels well inside the figure, not the white rivet
    highlights nor the dark-blue outlines"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    blue = (b > r + 25) & (b > 150) & (r > 120) & (b < 250)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    return blue & e


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


def _cut(a, polys):
    a = a.copy()
    m = np.zeros(a.shape, np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    a[m > 0] = 0
    return a


AUTO_OPTS = {'tip_len': 0.3, 'torso_over_legs': False, 'erase_emblem': False}   # he is blue all over: no emblem to erase


def auto_view(view, cut=None, **extra):
    def fn(rgb, a):
        if cut:
            a = _cut(a, cut)
        S = auto.build_auto(rgb, a, _mk(MASTERS[view][0]), plain_fn=PLAIN_FABRIC, **dict(AUTO_OPTS, **extra))
        S['border'] = BORDER
        return S
    return fn


# his cards have no brown paper edge: the acetate runs to a thin, slightly deeper blue rim.  Strip
# only that rim (the thin ring head would lose half its width to the usual 3.5 px) and redraw it
# blue, not brown
BORDER = 1.0
PART_BORDER = 1.0
EDGE = ((196, 160, 118), (226, 200, 168), (1.0, 0.7))


# the ledge slab under 05-ledge-sit-2 (card px); his left hand rests on it and is kept
LEDGE = [[(0, 263), (200, 263), (204, 276), (0, 276)]]

MASTERS = {
    'front': (SHEET + 'part-10', auto_view('front')),
    'q3r': (SHEET + 'stand-front', auto_view('q3r', split_legs=True)),
    'sit': (SHEET + '05-ledge-sit-2', auto_view('sit', LEDGE)),
    'kneel': (SHEET + 'part-4', auto_view('kneel')),
}
MASTER_FACING = {'front': None, 'q3r': 'R', 'sit': 'R', 'kneel': 'R'}
BACK_RIGS = ('sit',)
# required by the rig builder; never drawn (no brads are found on the pale rivets)
BRAD_SOURCE = (SHEET + 'part-10', 128.0, 307.0, 5.0, 6.0)

# hand-read hints: (view, posture, use, note)
_C = {
    'part-10': ('front', 'stand', 'ok', ''),
    '03-crouch-shield': ('front', 'stand', 'ok', 'standing front, arms down (the card name says crouch; the painting stands)'),
    'stand-front': ('3qR', 'stand', 'ok', 'floating step, arms out'),
    '05-ledge-sit': ('front', 'stand', 'ok', 'perched on a ledge, legs hanging, arms out; no ledge in the rig'),
    '05-ledge-sit-2': ('back3qR', 'sit', 'ok', 'seated on a ledge, seen from behind; no ledge in the rig'),
    'part-4': ('3qR', 'kneel', 'ok', 'kneeling, an arm over the ring (shielding)'),
}


def catalog():
    return {SHEET + k: dict(costume='soul', use=u, view=v, cls=c, props=[], hands='', gaze='none', note=n)
            for k, (v, c, u, n) in _C.items()}


def is_character_painting(tid, cat):
    c = cat.get(tid)
    return c is not None and c['use'] == 'ok'


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the soul catalog']
    out = [c['note']] if 'no ' in c['note'] else []
    return out + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {}
CURATED_PARTS = {}
POSTURE_RIGS = {'sit': 'sit', 'kneel': 'kneel'}
VIEW_RIGS = {'front': ('front', False), '3qR': ('q3r', False), '3qL': ('q3r', True), 'profR': ('q3r', False),
             'profL': ('q3r', True), 'back': ('front', False), 'back3qR': ('sit', False), 'back3qL': ('sit', True)}
# his cards are cut flush with the top of the ring, so the automatic head check (cut by the sheet
# edge) refuses every ring; the rings are whole: each card keeps its own
KEYS = {SHEET + k: {'head': [SHEET + k + '#head', False]} for k in ('part-10', '03-crouch-shield', 'stand-front', '05-ledge-sit',
                                                                  '05-ledge-sit-2')}
# the sheet's scale prior (2.10 px/cm) makes his ~119 px torsos 57 cm: trust the markers
SCALE_PRIOR = False
