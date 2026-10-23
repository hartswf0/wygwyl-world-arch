"""The MOTHER (poems 02.4 and 09.3): big afro, gold drop earrings, grey cable-knit cardigan over a
teal floral dress, grey knit slippers, brass brads.  The same design on both sheets.

Only three whole-figure paintings exist, all SEATED and all different, so each is its own master:
  argue : parents.02.car-argument/part-2   (seated 3/4 to screen right, head turned to screen left,
          arguing, one hand raised; the printed caption "PASSENGER" under her is cut away)
  lap   : parents.02.car-argument/part-5   (seated profile to screen right, head bowed, hands clasped
          on her knee)
  phone : parents.09.phone-prayer-walk/2-mother-prayer-mother-prayer (seated front, eyes closed in
          tears, the phone at her ear, the other palm open; the phone stays in her hand)
No standing, front-standing or back painting exists (cast_plan: not needed by the plans).  Her legs are
under the skirt: knee markers are placed by eye on the skirt's shape.
Markers: shots/rig/poses/mother__poem09.json (MoveNet, "medium"): every joint re-placed below.
"""
import numpy as np, cv2

from .. import auto, core

CHAR = 'mother__poem09'
CA = 'parents.02.car-argument/'
PH = 'parents.09.phone-prayer-walk/2-mother-prayer-mother-prayer'
MARKER_FILES = ['shots/rig/poses/mother__poem09.json']

# marker corrections (card px): shoulders, elbows and hips on her brads; R = her right
MARKER_FIX = {
    CA + 'part-2': dict(shoulderR=(113, 113), elbowR=(93, 172), wristR=(62, 128), shoulderL=(195, 112), elbowL=(228, 172),
                        wristL=(255, 180), hipR=(145, 212), hipL=(190, 222), groin=(170, 225), kneeR=(275, 192),
                        kneeL=(292, 200), ankleR=(262, 272), ankleL=(308, 265), toeR=(300, 298), toeL=(365, 292),
                        neck=(155, 110), chin=(125, 88), head=(150, 15)),
    CA + 'part-5': dict(shoulderR=(40, 113), elbowR=(65, 180), wristR=(150, 182), shoulderL=(105, 105), elbowL=(128, 168),
                        wristL=(148, 176), hipR=(35, 215), hipL=(85, 218), groin=(60, 225), kneeR=(178, 196),
                        kneeL=(190, 202), ankleR=(185, 265), ankleL=(225, 262), toeR=(215, 292), toeL=(285, 288),
                        neck=(85, 100), chin=(110, 88), head=(100, 8)),
    PH: dict(shoulderR=(55, 218), elbowR=(55, 325), wristR=(185, 340), shoulderL=(180, 226), elbowL=(238, 268),
             wristL=(225, 215), hipR=(95, 410), hipL=(195, 405), groin=(145, 415), kneeR=(130, 505), kneeL=(220, 500),
             ankleR=(152, 578), ankleL=(225, 575), toeR=(150, 632), toeL=(245, 632), neck=(132, 212), chin=(150, 190),
             head=(150, 30)),
}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=7):
    """the cardigan's grey knit and the teal dress: figure pixels well inside, not brass, not skin,
    not her dark hair"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    gold = (r > 110) & (r - b > 40) & (r > g)
    skin = (r > g + 12) & (g > b + 15) & (r > 70)
    dark = (r < 60) & (g < 50) & (b < 45)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    near_gold = cv2.dilate(gold.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
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


# the "PASSENGER" caption under part-2 (card px)
CAPTION = [[(160, 304), (285, 304), (285, 326), (160, 326)]]
AUTO_OPTS = {'tip_len': 0.35, 'hand_skin': True, 'torso_over_legs': False}


def whole_head(S, rgb, m):
    """her afro is far wider than the head window: every painted pixel above the shoulder line, within
    0.9 torso lengths of the chin and on no arm, joins the head layer (the torso loses it)"""
    fig, T = S['fig'], S['T']
    yy, xx = np.mgrid[0:fig.shape[0], 0:fig.shape[1]]
    sh_y = min(m['shoulderR'][1], m['shoulderL'][1])
    arms = np.zeros(fig.shape, bool)
    for L in S['layers']:
        if L['name'].startswith('arm'):
            arms |= L['alpha'] > 0.5
    arms = cv2.dilate(arms.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    top = fig & (yy < sh_y - 4) & (np.hypot(xx - m['chin'][0], yy - m['chin'][1]) < 0.9 * T) & ~arms
    n, lab, st, _ = cv2.connectedComponentsWithStats(top.astype(np.uint8))
    if n > 1:
        top = lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    for L in S['layers']:
        if L.get('is_head'):
            L['alpha'] = np.maximum(L['alpha'], top.astype(np.float32))
            L['rgb'] = np.where(top[..., None], rgb, L['rgb'])
            L['edgeok'] = np.ones(fig.shape, np.float32)
        elif L['bones'] == 'torso':
            L['alpha'] = np.where(top, 0, L['alpha']).astype(np.float32)
    return S


def own_paint(S, rgb):
    """each card is its own master: the torso and legs keep the painted pixels wherever the figure is
    painted (the filled-in knit or floral would show through the arm-root fades); painted pixels no
    layer took go to the torso"""
    fig = S['fig']
    owned = np.zeros(fig.shape, bool)
    for L in S['layers']:
        owned |= L['alpha'] > 0.5
    for L in S['layers']:
        if L['bones'] == 'torso' or L['name'] == 'legs':
            L['rgb'] = np.where(fig[..., None], rgb, L['rgb'])
        if L['bones'] == 'torso':
            L['alpha'] = np.where(fig & ~owned, 1.0, L['alpha']).astype(np.float32)
    return S


def auto_view(view, cut=None, **extra):
    def fn(rgb, a):
        if cut:
            a = _cut(a, cut)
        m = _mk(MASTERS[view][0])
        S = auto.build_auto(rgb, a, m, plain_fn=PLAIN_FABRIC, **dict(AUTO_OPTS, **extra))
        # her brads stay painted: the brad finder also takes the gold flowers of her dress, and each
        # card is its own master, so nothing bends round them
        S['brads'] = []
        return whole_head(own_paint(S, rgb), rgb, m)
    return fn


MASTERS = {
    'argue': (CA + 'part-2', auto_view('argue', CAPTION)),
    'lap': (CA + 'part-5', auto_view('lap')),
    'phone': (PH, auto_view('phone')),
}
MASTER_FACING = {'argue': 'R', 'lap': 'R', 'phone': None}
BACK_RIGS = ()
# required by the rig builder; never drawn (her brads stay painted, see auto_view)
BRAD_SOURCE = (CA + 'part-5', 65.0, 180.0, 6.0, 7.5)

_C = {
    CA + 'part-2': ('3qR', 'sit', 'label', 'side', 'seated, arguing, one hand raised; no car seat in the rig'),
    CA + 'part-5': ('profR', 'sit', 'ok', 'down', 'seated, head bowed, hands clasped on her knee; no car seat in the rig'),
    PH: ('front', 'sit', 'ok', 'down', 'seated on the phone, in tears; no armchair in the rig'),
}


def catalog():
    return {k: dict(costume='cardigan', use=u, view=v, cls=c, props=[], hands='', gaze=g, note=n) for k, (v, c, u, g, n) in _C.items()}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the mother catalog']
    out = [c['note']]
    if c['use'] == 'label':
        out.append('card carries a printed caption (cut away, not in the rig)')
    return out + EXTRA_FLAGS.get(tid, [])


_OWN = '("no usable head" below: none is swapped in; each card is its own master and keeps its painted head and hands)'
EXTRA_FLAGS = {k: [_OWN, 'seated only: no standing, walking or back painting of her exists'] for k in _C}
CURATED_PARTS = {}
POSTURE_RIGS = {}
VIEW_RIGS = {'front': ('phone', False), '3qR': ('argue', False), '3qL': ('argue', True), 'profR': ('lap', False),
             'profL': ('lap', True), 'back': ('phone', False), 'back3qR': ('argue', False), 'back3qL': ('argue', True)}
# 'scale' pins each master onto its own painting: the solver's median ratio compares the longer limb
# with the mean of both and comes out 1.01-1.10 on a card against itself
KEYS = {CA + 'part-2': {'view': 'argue', 'head': None, 'hands': {}, 'scale': 1 / 1.09},
        CA + 'part-5': {'view': 'lap', 'head': None, 'hands': {}, 'scale': 1 / 1.10},
        PH: {'view': 'phone', 'head': None, 'hands': {}, 'scale': 1 / 1.01}}
SCALE_PRIOR = False
