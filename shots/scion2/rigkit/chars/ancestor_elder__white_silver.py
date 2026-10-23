"""AMOS, the elder ancestor of poem 05: white and silver layered robe with star and moon panels, white
turban, grey beard, white boots, brass brads; a carved wooden staff with a lantern head in his left hand.

One whole-figure painting exists, ancestors.05.identities.01/amos-reference-only (standing front, the
right arm down, the staff held upright in the left hand; labelled REFERENCE ONLY): it is his only
master.  The staff is cut out of the body layers and kept as his left hand part with the fist, so it
rides the wrist instead of the robe.  No 3/4, profile, walking or back painting exists.
Markers: shots/rig/poses/ancestor_elder__white_silver.json (MoveNet), corrected below.
"""
import numpy as np, cv2

from .. import auto, core
from .ancestor_robe__indigo_gold import whole_head, own_paint, robe_split

CHAR = 'ancestor_elder__white_silver'
AMOS = 'ancestors.05.identities.01/amos-reference-only'
MARKER_FILES = ['shots/rig/poses/ancestor_elder__white_silver.json']
# joints on his brads; the robe hides his legs (knees guessed on the robe's folds)
MARKER_FIX = {AMOS: {'shoulderR': (34, 83), 'shoulderL': (106, 83), 'elbowR': (17, 130), 'elbowL': (111, 131),
                     'wristR': (18, 172), 'wristL': (127, 120), 'hipR': (48, 180), 'hipL': (90, 180),
                     'kneeR': (45, 240), 'kneeL': (95, 240), 'ankleR': (47, 301), 'ankleL': (91, 301),
                     'toeR': (25, 312), 'toeL': (110, 312)}}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=5):
    """white and silver robe: light unsaturated pixels well inside the figure"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    return (mn > 140) & (mx - mn < 40) & e


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


# card px: the staff from its lantern head to its foot, and his fist round it
STAFF_HAND = [(122, 18), (152, 18), (152, 321), (128, 321), (129, 134), (125, 132), (124, 110), (128, 106), (128, 60), (122, 40)]
AUTO_OPTS = {'tip_len': 0.35, 'hand_skin': True, 'torso_over_legs': False, 'limb_r': (0.22, 0.2)}


def build_front(rgb, a):
    m = _mk(AMOS)
    a = a.copy()
    st = np.zeros(a.shape, np.uint8)
    cv2.fillPoly(st, [np.array(STAFF_HAND, np.int32)], 1)
    a[st > 0] = 0                           # staff and fist are the hand part (CURATED_PARTS)
    S = auto.build_auto(rgb, a, m, plain_fn=PLAIN_FABRIC, erase_emblem=False, **AUTO_OPTS)
    S['border'] = 2.5
    S['brads'] = []                         # his brads stay painted (one master, nothing bends round them)
    return robe_split(whole_head(own_paint(S, rgb), rgb, m), rgb, m)


MASTERS = {'front': (AMOS, build_front)}
MASTER_FACING = {'front': None}
BACK_RIGS = ()
# required by the rig builder; never drawn (see build_front)
BRAD_SOURCE = (AMOS, 111.0, 131.0, 4.0, 5.0)
BORDER = 2.5
PART_BORDER = 2.5


def catalog():
    return {AMOS: dict(costume='white_silver', use='label', view='front', cls='stand', props=['staff'], hands='', gaze='front',
                       note='standing front, staff in his left hand')}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    if tid not in cat:
        return ['painting not in the AMOS catalog']
    return ['card carries a printed caption (not in the rig); labelled REFERENCE ONLY',
            '("no usable head" below: none is swapped in; his only card is his master and keeps its painted head)',
            'robe hides the legs: knees are guesses; front only (no 3/4, profile, walk or back painting)',
            'the staff is his left hand part (cut with the fist): it rides the wrist']


CURATED_PARTS = {
    'staffL': dict(kind='hand', side='L', src=AMOS, poly=STAFF_HAND, wr=(127, 120), el=(111, 131), seat_r=6, attrs={'shape': 'staff'}),
}
POSTURE_RIGS = {}
VIEW_RIGS = {v: ('front', False) for v in ('front', '3qR', '3qL', 'profR', 'profL', 'back', 'back3qR', 'back3qL')}
KEYS = {AMOS: {'head': None, 'hands': {'L': ['staffL', False]}}}
SCALE_PRIOR = False
