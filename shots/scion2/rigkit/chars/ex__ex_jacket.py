"""The EX: olive bomber jacket, dark jeans, white sneakers.  Poems 01-03, 07-09.

He is designed to be seen only from BEHIND ("face never turned"): every rig is a back or
3/4-back view, and no front or profile head exists or is invented.  A target turned further
than 3/4-back still renders on a back rig and is flagged.

Masters (all cut automatically from their Pose Lab markers, rigkit/auto.py):
  back    : ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01  (straight back, standing)
  back3q  : ex.ex_jacket.hipcore/proofs                (3/4 back, turned to screen right, phone up)
  sit     : ex.ex_jacket.hipcore/part                  (seated, 3/4 back to screen right)
  crouch  : poet.09.main-poses/ex-zips                 (crouched over the suitcase; suitcase cut away)
  fall    : ex.ex_jacket.master/03-fall-back-04         (tipping back, to screen left)
Marker R/L are anatomical: in a back view R is on screen RIGHT.
"""
import numpy as np, cv2

from .. import auto, core

MARKER_FILES = ['shots/rig/poses/ex__ex_jacket.json']

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=7):
    """the cloth hidden areas are filled from: olive jacket and blue-black denim, i.e. any figure
    pixel well inside the silhouette that is not a brass brad, white sneaker or skin"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    gold = (r > 110) & (r - b > 40) & (r > g)
    white = (r > 150) & (g > 150) & (b > 140)
    skin = (r > g + 12) & (g > b + 15) & (r > 70)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    near_gold = cv2.dilate(gold.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    return e & ~near_gold & ~white & ~skin


def _mk(pid):
    return core.load_markers('ex__ex_jacket')[pid]['markers']


def build_crouch(rgb, a):
    """ex-zips: the suitcase is cut away (a polygon round the case, his hand on the zip kept),
    then the auto cut runs on what is left."""
    a = a.copy()
    H, W = a.shape
    case = np.zeros((H, W), np.uint8)
    cv2.fillPoly(case, [np.array(SUITCASE_POLY, np.int32)], 1)
    a[case > 0] = 0
    # leather left showing between his shoes and shin: brown-orange pixels near the case
    b, g, r = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    yy, xx = np.mgrid[0:H, 0:W]
    leather = (r > b + 18) & (r > g + 8) & (xx >= 125) & (yy >= 195) & ~((xx > 228) & (yy < 216))
    leather &= (yy < 272) | (xx >= 154)       # below that is his shoe's tan sole
    leather = cv2.morphologyEx(leather.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
    a[leather] = 0
    return tidy(auto.build_auto(rgb, a, _mk(MASTERS['crouch'][0]), plain_fn=PLAIN_FABRIC, **AUTO_OPTS), rgb, paper_gap=False)


def tidy(S, rgb, paper_gap=True):
    """clean an auto cut: the torso loses thin spikes (sleeve-hem slivers the arm masks left behind)
    and keeps its main piece; no layer keeps the card's beige paper showing between the legs"""
    T = S['T']
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    paper = (r > 165) & (r - b > 18) & (r - b < 75) & (g > 135)
    gold = cv2.dilate(((r > 110) & (r - b > 40) & (r > g + 10)).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    yy, xx = np.mgrid[0:rgb.shape[0], 0:rgb.shape[1]]
    mh = S['joints']['midhip']
    paper &= ~gold & (np.hypot(xx - mh[0], yy - mh[1]) < 0.7 * T) & paper_gap   # only the gap at the crotch
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(0.13 * T) | 1,) * 2)
    for L in S['layers']:
        if L.get('is_head'):
            continue
        al = L['alpha']
        if L['bones'] == 'torso':
            m = cv2.morphologyEx((al > 0.5).astype(np.uint8), cv2.MORPH_OPEN, k)
            n, lab, st, _ = cv2.connectedComponentsWithStats(m)
            if n > 1:
                m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
            al = al * m
        L['alpha'] = (np.where(paper, 0, al) if L['name'] == 'legs' else al).astype(np.float32)
    return S


def build_auto(view, cut=None):
    """auto cut + tidy; cut = polygon (master px) removed from the painting first (a prop)"""
    def fn(rgb, a):
        if cut:
            a = a.copy()
            m = np.zeros(a.shape, np.uint8)
            cv2.fillPoly(m, [np.array(cut, np.int32)], 1)
            a[m > 0] = 0
        return tidy(auto.build_auto(rgb, a, _mk(MASTERS[view][0]), plain_fn=PLAIN_FABRIC, **AUTO_OPTS), rgb)
    return fn


# the vape pen sticking out of the back master's left fist
VAPE_POLY = [(12, 231), (25, 228), (29, 254), (16, 256)]


# the suitcase on ex-zips (card px); his hand on the zip pull stays outside it
SUITCASE_POLY = [(169, 190), (246, 190), (249, 213), (261, 213), (263, 193), (311, 193), (311, 303), (153, 303), (153, 262),
                 (160, 232), (166, 205)]

# his jacket is olive over blue-black jeans: the filled torso must not paint over the jeans' waist
AUTO_OPTS = {'torso_over_legs': False}

MASTERS = {
    'back': ('ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01', build_auto('back', VAPE_POLY)),
    'back3q': ('ex.ex_jacket.hipcore/proofs', build_auto('back3q')),
    'sit': ('ex.ex_jacket.hipcore/part', build_auto('sit')),
    'crouch': ('poet.09.main-poses/ex-zips', build_crouch),
    'fall': ('ex.ex_jacket.master/03-fall-back-04', build_auto('fall')),
}
MASTER_FACING = {'back': None, 'back3q': 'R', 'sit': 'R', 'crouch': 'R', 'fall': 'L'}
BACK_RIGS = ('back', 'back3q', 'sit', 'crouch', 'fall')
# one clean painted brad (the master's left-hip brad): (painting, cx, cy, brass r, sprite r)
BRAD_SOURCE = ('ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01', 58.0, 199.1, 4.0, 5.0)

# hand-read hints for his paintings: view (back / back3qR / back3qL), posture, use, gaze
_C = {
    'ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01': ('back', 'stand', 'ok', 'vape in L hand'),
    'ex.ex_jacket.master/stand-front-back': ('back', 'stand', 'ok', 'vape in L hand'),
    'ex.ex_jacket.master/lean-back': ('back', 'lean', 'ok', 'leaning on a rail (rail not in the rig)'),
    'ex.ex_jacket.master/03-fall-back-04': ('back3qL', 'fall', 'ok', 'tipping backward'),
    'ex.ex_jacket.hipcore/proofs': ('back3qR', 'stand', 'ok', 'phone up in R hand'),
    'ex.ex_jacket.hipcore/part': ('back3qR', 'sit', 'ok', 'seated, phone; no seat in the rig'),
    'ex.02.action.ex_jacket.parts/head-back-view': ('back3qL', 'fly', 'ok', 'flying / thrown, horizontal'),
    'poet.01.main-poses/fall-reach-back-2': ('back', 'fall', 'ok', 'prone from behind, soles to camera (foreshortened)'),
    'poet.02.main-poses/ex-writhes': ('back', 'dance', 'ok', 'arms flung out, knees bent'),
    'poet.03.main-poses/two-backs-out-of-step-2': ('back', 'walk', 'ok', ''),
    'poet.03.main-poses/ex-keeps-going': ('back', 'walk', 'ok', ''),
    'poet.03.main-poses/part-2': ('back', 'walk', 'ok', ''),
    'poet.08.main-poses/08-ex-strictly-walks-back-away-with-both-hands-p': ('back', 'walk', 'ok', 'hands in pockets'),
    'poet.09.main-poses/part-2': ('back', 'walk', 'ok', ''),
    'poet.09.main-poses/ex-zips': ('back3qR', 'crouch', 'ok', 'crouched over the suitcase (no suitcase in the rig)'),
    'poet.07.main-poses/2': ('back', 'stand', 'ghost', 'translucent ghost card'),
}


def catalog():
    return {k: dict(costume='ex', use=u, view=v, cls=c, props=[], hands='', gaze='away', note=n) for k, (v, c, u, n) in _C.items()}


def is_character_painting(tid, cat):
    c = cat.get(tid)
    return c is not None and c['use'] == 'ok'


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the EX catalog']
    out = []
    if c['use'] == 'ghost':
        out.append('painting is a translucent ghost card: the rig renders him solid, its own parts are not used')
    if c['cls'] in ('lean', 'sit', 'crouch') and c['note']:
        out.append(c['note'])
    return out + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {
    'ex.ex_jacket.hipcore/proofs': ['the phone in his raised hand is mostly lost: the auto arm cut keeps only an arm width round the bones'],
    'ex.ex_jacket.hipcore/part': ['the phone in his raised hand is mostly lost: the auto arm cut keeps only an arm width round the bones'],
    'poet.03.main-poses/part-2': ['card clipped on the left: the left wrist marker is a guess, the rig hand lands behind his back'],
    'poet.01.main-poses/fall-reach-back-2': ['prone and foreshortened toward the camera (soles up): a flat rig cannot reach it; '
                                             'rendered as an upright back figure in the marker pose'],
    'ex.02.action.ex_jacket.parts/head-back-view': ['thrown/flying: rendered on the back rig at 0.8x the marker scale '
                                                    '(its limbs are drawn long against its torso)'],
}


CURATED_PARTS = {}
# catalog posture -> rig
POSTURE_RIGS = {'sit': 'sit', 'crouch': 'crouch', 'fall': 'fall', 'fly': 'fall'}
VIEW_RIGS = {'back': ('back', False), 'back3qR': ('back3q', False), 'back3qL': ('back3q', True),
             # never a front: anything else still lands on a back rig
             'front': ('back', False), '3qR': ('back3q', False), '3qL': ('back3q', True)}
KEYS = {
    'ex.02.action.ex_jacket.parts/head-back-view': {'view': 'back', 'scale': 0.8},
    # its own head is drawn foreshortened from above, collar and all: use the master's back head
    'poet.01.main-poses/fall-reach-back-2': {'view': 'back', 'scale': 1.15, 'offset': (0, 22),
                                             'head': ['ex.ex_jacket.master/back-view-neutral-stand-with-vape-pen-01#head', False]},
    # a master's own painted hand keeps its prop (phone, zip pull); a skin-only hand cut drops it
    'ex.ex_jacket.hipcore/proofs': {'hands': {}},
    'ex.ex_jacket.hipcore/part': {'hands': {}},
    # the own hand cut takes a piece of the suitcase with it
    'poet.09.main-poses/ex-zips': {'hands': {}},
    # hands in his pockets: no hand drawn, the sleeve ends at the cuff
    'poet.08.main-poses/08-ex-strictly-walks-back-away-with-both-hands-p': {'hands': {'R': 'none', 'L': 'none'}},
    # his hands are hidden in front of his body in the painting
    'poet.09.main-poses/part-2': {'hands': {'R': 'none', 'L': 'none'}},
}
