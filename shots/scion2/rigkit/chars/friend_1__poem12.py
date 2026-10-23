"""FRIEND 1 (poem 12): navy jacket with rolled sleeves, cream tee, khaki trousers, black shoes,
brass brads, short beard.

Only two whole-figure paintings exist, both on family.12.friend_1.heads-hands and both small
(torso ~50 px, figure ~190 px tall):
  front : part-25                     (front, pointing to screen right, the other hand raised in a pinch)
  laugh : 26-laugh-head-back-standing (front, arms down, head thrown back laughing; white paper
          left between his arms and his legs is cut away)
Each card is its own master.  The sheet also holds a 3/4, a 3/4-back, a back and a profile, but as
heads only (1-front, 2-threequarter, 4-threequarter-back, 5-back, profile-3) plus loose hands: there
is no 3/4, profile or back body, so the 12.5 profile chain is not reachable and nothing is invented.
Markers: shots/rig/poses/friend_1__poem12.json (MoveNet), corrected on the brads below.
"""
import numpy as np, cv2

from .. import auto, core

CHAR = 'friend_1__poem12'
SHEET = 'family.12.friend_1.heads-hands/'
MARKER_FILES = ['shots/rig/poses/friend_1__poem12.json']

# marker corrections (card px): joints on the painted brads
MARKER_FIX = {
    SHEET + 'part-25': {'shoulderR': (34, 47), 'shoulderL': (82, 44), 'elbowR': (17, 72), 'elbowL': (104, 58),
                        'wristR': (9, 47), 'wristL': (125, 46), 'hipR': (44, 97), 'hipL': (79, 93),
                        'kneeR': (43, 134), 'kneeL': (77, 134), 'ankleR': (36, 169), 'ankleL': (79, 169)},
    SHEET + '26-laugh-head-back-standing': {'shoulderR': (18, 49), 'shoulderL': (63, 46), 'hipR': (31, 97), 'hipL': (65, 93),
                                            'kneeR': (31, 135), 'kneeL': (63, 135), 'ankleR': (28, 170), 'ankleL': (63, 170),
                                            'wristR': (12, 100), 'wristL': (79, 96), 'chin': (44, 30)},
}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=3):
    """navy jacket and khaki twill: figure pixels inside, not brass, skin, the cream tee or paper"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    gold = (r > 150) & (g > 120) & (b < 120)
    skin = (r > g + 12) & (g > b + 15) & (r > 70) & (r < 200)
    light = mn > 150
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    near_gold = cv2.dilate(gold.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    return e & ~near_gold & ~skin & ~light


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


def paper(rgb, a):
    """opaque white card paper inside the cut-out (between arms and body, between the legs): bright,
    unsaturated (the cream tee is warmer: max-min ~ 55)"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    p = ((mn > 185) & (mx - mn < 30) & (a > 0.5)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(p)
    p = np.isin(lab, 1 + np.nonzero(st[1:, cv2.CC_STAT_AREA] >= 6)[0])
    return cv2.dilate(p.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0


# small cards: the painted paper edge is about 2 px, not the large cards' 3.5, and the rig's crisp
# edge is drawn at half the usual width (in master px it would be twice as heavy against his ~50 px
# torso as against the poet's)
AUTO_OPTS = {'tip_len': 0.35, 'hand_skin': True, 'torso_over_legs': False}
BORDER = 2.0
PART_BORDER = 2.0
EDGE = (core.EDGE_BROWN, core.EDGE_TAN, (0.8, 0.5))


def auto_view(view, cut_paper=False, **extra):
    def fn(rgb, a):
        if cut_paper:
            a = np.where(paper(rgb, a), 0, a)
        S = auto.build_auto(rgb, a, _mk(MASTERS[view][0]), plain_fn=PLAIN_FABRIC, **dict(AUTO_OPTS, **extra))
        S['border'] = BORDER
        # his brads are small pale highlights the brad finder mostly misses: all stay painted
        S['brads'] = []
        return own_head(tee(S, rgb), rgb, a, view)
    return fn


# his heads cut by hand down to the collar (card px; the seat row below which the torso keeps its
# pixels): the automatic window draws a paper edge across his collar and chops the thrown-back head
_HEADS = {
    'front': ([(39, 10), (44, 1), (56, -1), (68, 2), (72, 12), (71, 22), (67, 30), (62, 35), (54, 36), (48, 32), (42, 24),
               (39, 18)], 36),
    'laugh': ([(13, 10), (20, 1), (35, -1), (46, 3), (52, 12), (52, 24), (48, 31), (43, 35), (35, 37), (26, 34), (18, 28),
               (13, 20)], 36),
}


def own_head(S, rgb, a, view):
    poly, sy = _HEADS[view]
    hm = np.zeros(a.shape, np.uint8)
    cv2.fillPoly(hm, [np.array(poly, np.int32)], 1)
    hm = (hm > 0) & S['fig']
    yy = np.mgrid[0:a.shape[0], 0:a.shape[1]][0]
    for L in S['layers']:
        if L.get('is_head'):
            L['rgb'] = rgb.copy()
            L['alpha'] = hm.astype(np.float32)
            L['edgeok'] = np.ones(a.shape, np.float32)
        elif L['bones'] == 'torso':
            L['alpha'] = np.where(hm & (yy < sy - 6), 0, L['alpha']).astype(np.float32)
        else:
            L['alpha'] = np.where(hm, 0, L['alpha']).astype(np.float32)
    return S


def tee(S, rgb):
    """the cream tee belongs to the torso, never to an arm layer (as the party guest's)"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    cream = (mn > 150) & (mx - mn > 25) & (r > b + 25) & S['fig']
    n, lab, st, _ = cv2.connectedComponentsWithStats(cream.astype(np.uint8))
    cream = np.isin(lab, 1 + np.nonzero(st[1:, cv2.CC_STAT_AREA] > 0.08 * S['T'] ** 2)[0])
    for L in S['layers']:
        if L['name'].startswith('arm'):
            L['alpha'] = np.where(cream, 0, L['alpha']).astype(np.float32)
        elif L['bones'] == 'torso':
            L['rgb'] = np.where(cream[..., None], rgb, L['rgb'])
            L['alpha'] = np.where(cream, 1.0, L['alpha']).astype(np.float32)
    return S


MASTERS = {
    # the pointing finger reaches 0.66 torso lengths past the wrist
    'front': (SHEET + 'part-25', auto_view('front', tip_len=0.7)),
    'laugh': (SHEET + '26-laugh-head-back-standing', auto_view('laugh', cut_paper=True)),
}
MASTER_FACING = {'front': None, 'laugh': None}
BACK_RIGS = ()
# required by the rig builder; never drawn (his brads stay painted, see auto_view)
BRAD_SOURCE = (SHEET + 'part-25', 82.0, 44.0, 2.5, 3.5)

_C = {
    'part-25': ('front', 'stand', 'ok', 'front', 'pointing to screen right, the other hand raised in a pinch'),
    '26-laugh-head-back-standing': ('front', 'stand', 'label', 'up', 'arms down, head thrown back laughing'),
}


def catalog():
    return {SHEET + k: dict(costume='navy', use=u, view=v, cls=c, props=[], hands='', gaze=g, note=n)
            for k, (v, c, u, g, n) in _C.items()}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the friend 1 catalog']
    out = []
    if c['use'] == 'label':
        out.append('card carries a printed caption (not in the rig)')
    return out + EXTRA_FLAGS.get(tid, [])


_OWN = '("no usable head" below: none is swapped in; the rig draws its own painted head)'
EXTRA_FLAGS = {
    SHEET + 'part-25': [_OWN, 'his only two bodies are fronts: no 3/4, profile or back body exists (12.5 profile chain not reachable)',
                        'the small white chip pinched in his raised hand is mostly lost (pale, inside the thin edge strip)'],
    SHEET + '26-laugh-head-back-standing': [_OWN, 'white card paper between his arms and body and between his legs is cut away'],
}
CURATED_PARTS = {}
POSTURE_RIGS = {}
VIEW_RIGS = {'front': ('front', False), '3qR': ('front', False), '3qL': ('front', False), 'profR': ('front', False),
             'profL': ('front', False), 'back': ('front', False), 'back3qR': ('front', False), 'back3qL': ('front', False)}
# each card is its own master, with its rig's own painted head and hands (the automatic hand part,
# skin within 0.42 torso lengths of the wrist, drops the pointing finger)
KEYS = {SHEET + 'part-25': {'head': None, 'hands': {}},
        SHEET + '26-laugh-head-back-standing': {'view': 'laugh', 'head': None, 'hands': {}}}
SCALE_PRIOR = False
