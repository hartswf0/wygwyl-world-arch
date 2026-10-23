"""The YOUNG POET, age 6, in plaid winter pajamas and knit socks (poem 02), brass brads.

His cards are on young_ghost.02.main-poses, which solve.py aliased to young_poet/child_clothes (the
striped-tee boy of poem 13, a different costume: see chars/young_poet__child_clothes.py).  Two other
cards on that sheet are the GHOST CHILD (pale nightgown: 02-ghost-assembles-1, 06-wind-up-ghost-thins-1)
and two show both children (04-side-hug-2, 05-offer-take-tambourine); none of those is used here.
Markers: shots/rig/poses/young_poet__pajamas_winter.json (his 4 cards only).

Masters (cut automatically from their Pose Lab markers, rigkit/auto.py):
  q3r     : 06-wind-up-ghost-thins-2 (3/4 to screen right, throwing; the tambourine is cut away and
            kept as a curated hand part)
  profL   : 02-ghost-assembles-2     (strict profile facing screen left, standing)
  back3q  : 04-side-hug              (from behind, turned to screen right, a hand on the curtain;
            curtain cut away)
There is no front painting of him: a front target would land on the 3/4 rig.  No face is invented.
"""
import numpy as np, cv2

from .. import auto, core

CHAR = 'young_poet__pajamas_winter'
SHEET = 'young_ghost.02.main-poses/'
MARKER_FILES = ['shots/rig/poses/young_poet__pajamas_winter.json']

# marker corrections (card px)
MARKER_FIX = {
    # hauling the blind cord with both hands, from behind: MoveNet swapped his sides (R on screen left,
    # against 04-side-hug's R on screen right, the same back view) and put both wrists on the upper hand;
    # every limb marker re-placed, R = screen right as on the back master
    SHEET + '06-wind-up-ghost-thins': {'shoulderR': (236, 150), 'elbowR': (277, 137), 'wristR': (300, 108),
                                       'shoulderL': (210, 149), 'elbowL': (265, 186), 'wristL': (298, 184),
                                       'hipR': (230, 251), 'kneeR': (242, 330), 'ankleR': (235, 406), 'toeR': (283, 435),
                                       'hipL': (182, 266), 'kneeL': (162, 326), 'ankleL': (127, 392), 'toeL': (133, 443)},
    # the raised wrist is at the cuff brad under the tambourine, not on the tambourine's rim
    SHEET + '06-wind-up-ghost-thins-2': {'wristR': (50, 88)},
}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=7):
    """the plaid flannel: any figure pixel well inside the silhouette that is not brass, skin or the
    dark outline"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    gold = (r > 110) & (r - b > 40) & (r > g)
    skin = (r > g + 12) & (g > b + 15) & (r > 70)
    dark = (r < 50) & (g < 50) & (b < 60)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    near_gold = cv2.dilate(gold.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    return e & ~near_gold & ~skin & ~dark


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


def _cut(a, polys):
    a = a.copy()
    m = np.zeros(a.shape, np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    a[m > 0] = 0
    return a


# a six-year-old's head is big against his torso: a wider, taller head window than the adults' (it
# decides which pixels the rigs' head layers take; the head parts themselves are cut by hand below)
HEAD_WIN = (0.63, 1.3, 1.6, 0.20)
# ...and his sleeves and trouser legs are thick against his short torso
AUTO_OPTS = {'tip_len': 0.3, 'hand_skin': True, 'torso_over_legs': False, 'head_win': HEAD_WIN, 'limb_r': (0.23, 0.24)}


def auto_view(view, cut=None, **extra):
    def fn(rgb, a):
        if cut:
            a = _cut(a, cut)
        return auto.build_auto(rgb, a, _mk(MASTERS[view][0]), plain_fn=PLAIN_FABRIC, **dict(AUTO_OPTS, **extra))
    return fn


def build_prof(rgb, a):
    """02-ghost-assembles-2, strict profile: both sleeves lie over his side, so the auto cut leaves
    the torso nothing but filled-in plaid.  Here the torso is the painted figure minus the near arm
    and the legs (no fill), and the far arm, hidden behind him, is dropped."""
    S = auto_view('prof', limb_r=(0.16, 0.24))(rgb, a)
    fig = S['fig']
    painted = lambda L: (L['alpha'] > 0.5) & fig & (np.abs(L['rgb'] - rgb).sum(-1) < 1)
    names = [L['name'] for L in S['layers']]
    near = names[-1]                       # auto draws the near arm last
    taken = np.zeros(fig.shape, bool)
    for L in S['layers']:
        if L['name'] in ('legs', near):
            taken |= painted(L)
    for L in S['layers']:
        if L['bones'] == 'torso':
            L['rgb'] = rgb.copy()
            L['alpha'] = (fig & ~taken & ~painted(S['layers'][names.index('head')])).astype(np.float32)
        elif L['name'].startswith('arm') and L['name'] != near:
            L['alpha'] = np.zeros(fig.shape, np.float32)
    return S


# card px: the tambourine in his raised hand (06-wind-up-ghost-thins-2), the curtain beside him
# (04-side-hug: everything right of his sleeve and the hand that holds it), the blind cord and tassel
# (06-wind-up-ghost-thins, between and below his two hands)
TAMBOURINE = [(6, 0), (94, 0), (94, 70), (72, 80), (40, 83), (6, 72)]
CURTAIN = [[(318, 0), (487, 0), (487, 452), (298, 452), (306, 400), (318, 320), (330, 240), (336, 190), (346, 170), (357, 142),
            (360, 136), (366, 128), (367, 110), (362, 100), (352, 96), (345, 104), (340, 104), (336, 96), (330, 80), (322, 0)]]
CORD = [[(305, 0), (332, 0), (332, 68), (305, 68)], [(308, 101), (330, 101), (330, 154), (308, 154)],
        [(298, 197), (334, 197), (334, 300), (298, 300)]]

MASTERS = {
    'q3r': (SHEET + '06-wind-up-ghost-thins-2', auto_view('q3r', [TAMBOURINE])),
    'prof': (SHEET + '02-ghost-assembles-2', build_prof),
    'back3q': (SHEET + '04-side-hug', auto_view('back3q', CURTAIN)),
}
MASTER_FACING = {'q3r': 'R', 'prof': 'L', 'back3q': 'R'}
BACK_RIGS = ('back3q',)
# a clean brad: the 3/4 master's left hip (painting, cx, cy, brass r, sprite r)
BRAD_SOURCE = (SHEET + '06-wind-up-ghost-thins-2', 168.9, 207.9, 6.0, 7.5)

# hand-read hints: (view, posture, use, note)
_C = {
    '04-side-hug': ('back3qR', 'stand', 'label', 'at the window, a hand on the curtain; no curtain in the rig'),
    '02-ghost-assembles-2': ('profL', 'stand', 'ok', ''),
    '06-wind-up-ghost-thins': ('back3qR', 'stand', 'label', 'hauling the blind cord; no cord in the rig'),
    '06-wind-up-ghost-thins-2': ('3qR', 'throw', 'ok', 'throwing the tambourine (kept as his hand part)'),
}


def catalog():
    return {SHEET + k: dict(costume='pajamas', use=u, view=v, cls=c, props=[], hands='', gaze='side', note=n)
            for k, (v, c, u, n) in _C.items()}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the pajama-boy catalog']
    out = [c['note']] if 'no ' in c['note'] else []
    if c['use'] == 'label':
        out.append('card carries a printed caption (not in the rig)')
    return out + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {
    SHEET + '06-wind-up-ghost-thins': ['on the back rig (square-on shoulders): both arms reach forward round a narrowed back and the '
                                       'shoulder rivets bunch; the cut-away cord leaves short stubs in his fists; a tuft of the back master\'s hair pokes above his head'],
    SHEET + '04-side-hug': ['a few curtain threads stay between the fingers of his raised hand'],
    SHEET + '02-ghost-assembles-2': ['profile rig: the far arm is hidden (dropped); a small soft patch of filled plaid at the hip'],
}
# his heads, cut by hand down to the collar: the automatic window (narrowing to the neck, seated on
# the head axis) chops a child's big round head at the nape.  (card px; axis = parts.torso_axis)
_HEADS = {
    '04-side-hug': ([(205, 70), (225, 48), (250, 44), (275, 55), (288, 80), (288, 110), (278, 125), (262, 133), (262, 140),
                     (222, 140), (222, 132), (205, 122), (200, 100)], (243, 157), -1.5832, 145),
    '02-ghost-assembles-2': ([(5, 40), (15, 15), (35, 0), (80, 0), (100, 15), (104, 40), (100, 65), (88, 80), (70, 92), (62, 98),
                              (40, 98), (18, 86), (5, 70)], (48, 109), -1.6082, 103),
    '06-wind-up-ghost-thins': ([(152, 95), (165, 70), (190, 58), (220, 60), (238, 80), (246, 100), (245, 125), (235, 135), (215, 138),
                                (190, 140), (170, 135), (155, 120)], (220, 147), -1.4402, 143),
    '06-wind-up-ghost-thins-2': ([(96, 65), (110, 42), (135, 31), (158, 35), (170, 50), (172, 70), (178, 78), (176, 92), (165, 98),
                                  (150, 100), (140, 104), (118, 100), (105, 90), (96, 80)], (140, 118), -1.4923, 108),
}
CURATED_PARTS = {
    'head:' + k: dict(kind='head', src=SHEET + k, poly=poly, neck=nk, axis=ax, seat_line=[(0, sy), (500, sy)], attrs={'gaze': 'side'})
    for k, (poly, nk, ax, sy) in _HEADS.items()}
CURATED_PARTS.update({
    'tambR': dict(kind='hand', side='R', src=SHEET + '06-wind-up-ghost-thins-2', poly=TAMBOURINE, wr=(50, 88), el=(63, 116), seat_r=4,
                  attrs={'shape': 'tambourine'}),
})
POSTURE_RIGS = {}
VIEW_RIGS = {'front': ('q3r', False), '3qR': ('q3r', False), '3qL': ('q3r', True), 'profL': ('prof', False),
             'profR': ('prof', True), 'back': ('back3q', False), 'back3qR': ('back3q', False), 'back3qL': ('back3q', True)}
KEYS = {SHEET + k: {'head': ['head:' + k, False]} for k in _HEADS}
KEYS[SHEET + '06-wind-up-ghost-thins-2']['hands'] = {'R': ['tambR', False]}
# the profile master keeps its own painted hand (the skin-only cut leaves a hole at the cuff and hip)
KEYS[SHEET + '02-ghost-assembles-2']['hands'] = {}
# the back master's own painted hand on the curtain edge (its skin-only cut carries curtain scraps)
KEYS[SHEET + '04-side-hug']['hands'] = {}
