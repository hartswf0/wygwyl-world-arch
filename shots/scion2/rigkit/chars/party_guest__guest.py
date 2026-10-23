"""The PARTY GUEST: black studded denim jacket and cargo jeans, cream tee, gold chain, tan-soled
black boots, brass brads.  Poems 06.6 and 07 (one painted guest, many crowd instances).

All of his whole-figure paintings are on party.07.party_guest.main-poses.  Read by eye, the
sheet has front-facing standing cards, one back card, one seated card and two clipped slivers;
cast_plan's "3/4" (02-mouth-words-we-love) and "profile" (03-mouth-words-we-not) are both
front-facing bodies (heads turned a little), so there is no 3/4 or profile rig to build.

Masters (all cut automatically from their Pose Lab markers, rigkit/auto.py):
  front : 02-mouth-words-we-love   (front, arms out, palms up: the most open arms on the sheet)
  back  : walk-into                (back, walking through a door; the door frame is cut away)
  sit   : 01-couch-lean-hand-to-chest (perched on a couch arm, 3/4 to screen right; couch cut away)
cast_plan's front, 04-lighter-up-2, holds a lit lighter overhead in a raised hand: as a master
it would carry the lighter into every front pose.  It is rendered on the front rig instead, and
keeps its lighter as a curated hand part.
"""
import numpy as np, cv2

from .. import auto, core

CHAR = 'party_guest__guest'
SHEET = 'party.07.party_guest.main-poses/'
MARKER_FILES = ['shots/rig/poses/party_guest__guest.json']
EXCLUDE_TARGETS = {
    SHEET + 'part-11': 'not a figure to pose: a 63 px sliver of his clipped right side (arm and boot); MoveNet markers are noise '
                       '(confidence < 0.3, joints piled on each other)',
}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=7):
    """black denim: dark pixels well inside the silhouette, away from brass brads and the orange
    piping"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    dark = (r < 80) & (g < 80) & (b < 85)
    gold = (r > 110) & (r - b > 40)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    near_gold = cv2.dilate(gold.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    return dark & e & ~near_gold


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


def _cut(a, polys):
    a = a.copy()
    m = np.zeros(a.shape, np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    a[m > 0] = 0
    return a


def tee(S, rgb):
    """his cream tee belongs to the torso: arm layers that took tee pixels (a forearm across his
    chest) lose them, and the torso shows the painted tee there instead of the filled-in denim"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    cream = (mn > 95) & (mx - mn < 60) & S['fig']           # lit and shadowed tee
    cream = cv2.morphologyEx(cream.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(cream)  # the tee, not the brads' highlights
    cream = np.isin(lab, 1 + np.nonzero(st[1:, cv2.CC_STAT_AREA] > 0.03 * S['T'] ** 2)[0])
    for L in S['layers']:
        if L['name'].startswith('arm'):
            L['alpha'] = np.where(cream, 0, L['alpha']).astype(np.float32)
        elif L['bones'] == 'torso':
            L['rgb'] = np.where(cream[..., None], rgb, L['rgb'])
            L['alpha'] = np.where(cream, 1.0, L['alpha']).astype(np.float32)
    return hip_brads(S)


def hip_brads(S):
    """his hip brads sit over the jacket hem: draw them after the torso (still riding the thighs)"""
    S['brads'] = [(b[0], 'torso', b[2]) + tuple(b[3:]) if b[0].startswith('hip') else b for b in S['brads']]
    return S


def build_back(rgb, a):
    """walk-into: the tan door frame (posts at x 1-7 and 169-173, lintel y 1-19) is cut away"""
    a = _cut(a, [[(0, 0), (9, 0), (9, 400), (0, 400)], [(167, 0), (180, 0), (180, 400), (167, 400)],
                 [(0, 0), (180, 0), (180, 21), (0, 21)]])
    return hip_brads(auto.build_auto(rgb, a, _mk(MASTERS['back'][0]), plain_fn=PLAIN_FABRIC, **AUTO_OPTS))


def build_sit(rgb, a):
    """01-couch: the beige couch (light, unsaturated pixels left of his tee) and its wooden leg
    are cut away, then auto"""
    H, W = a.shape
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    light = (mn > 120) & (mx - mn < 70)
    yy, xx = np.mgrid[0:H, 0:W]
    couch = (light & (xx < 158) & (yy > 120)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(couch)     # the couch is big; brad highlights are specks
    couch = np.isin(lab, 1 + np.nonzero(st[1:, cv2.CC_STAT_AREA] > 400)[0])
    couch = cv2.dilate(couch.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    a = a.copy()
    a[couch] = 0
    a = _cut(a, COUCH_POLYS)
    S = tee(auto.build_auto(rgb, a, _mk(MASTERS['sit'][0]), plain_fn=PLAIN_FABRIC, **AUTO_OPTS), rgb)
    # both arms lie in front of his body here (one hand on his chest, the other forearm across the
    # jacket hem to his thigh): the auto cut's "far" arm goes in front of the torso too, so the
    # torso's filled-in denim does not paint over it
    arms = [L for L in S['layers'] if L['name'].startswith('arm')]
    S['layers'] = [L for L in S['layers'] if not L['name'].startswith('arm')] + arms
    # the shoulder brad the cut gave to the torso (as a far-arm brad) now rides on its arm
    S['brads'] = [(j, 'arm' + j[-1], 'uarm' + j[-1]) + tuple(b[3:]) if j.startswith('sh') and lay == 'torso' else b
                  for b in S['brads'] for (j, lay) in [(b[0], b[1])]]
    return S


# card px of 01-couch-lean-hand-to-chest: the couch's wooden leg and the couch body below his hand
COUCH_POLYS = [[(0, 300), (150, 300), (150, 398), (0, 398)]]

AUTO_OPTS = {'tip_len': 0.3, 'hand_skin': True, 'open_torso': 0.1, 'torso_over_legs': False}


def auto_view(view, **extra):
    return lambda rgb, a: tee(auto.build_auto(rgb, a, _mk(MASTERS[view][0]), plain_fn=PLAIN_FABRIC, **dict(AUTO_OPTS, **extra)), rgb)


MASTERS = {
    'front': (SHEET + '02-mouth-words-we-love', auto_view('front')),
    'back': (SHEET + 'walk-into', build_back),
    'sit': (SHEET + '01-couch-lean-hand-to-chest', build_sit),
}
MASTER_FACING = {'front': None, 'back': None, 'sit': 'R'}
BACK_RIGS = ('back',)
# a clean brass brad: the front master's right knee (painting, cx, cy, brass r, sprite r)
BRAD_SOURCE = (SHEET + '02-mouth-words-we-love', 112.9, 299.5, 5.5, 7.0)

# hand-read hints: (view, posture, use, gaze, note)
_C = {
    '01-couch-lean-hand-to-chest': ('3qR', 'sit', 'ok', 'side', 'perched on a couch arm, hand to chest; no couch in the rig'),
    '02-mouth-words-we-love': ('front', 'stand', 'ok', 'side', 'arms out, palms up, mouthing'),
    '03-mouth-words-we-not': ('front', 'stand', 'ok', 'front', 'both palms raised, mouthing'),
    '04-lighter-up-2': ('front', 'stand', 'ok', 'up', 'lit lighter held overhead, looking up at it'),
    'part-9': ('front', 'stand', 'crop', 'side', 'selfie: phone held up; card clipped down the left (his right side)'),
    'walk-into': ('back', 'walk', 'ok', 'away', 'walking away through a door; no door in the rig'),
}


def catalog():
    return {SHEET + k: dict(costume='guest', use=u, view=v, cls=c, props=[], hands='', gaze=g, note=n)
            for k, (v, c, u, g, n) in _C.items()}


def is_character_painting(tid, cat):
    c = cat.get(tid)
    return c is not None and c['use'] in ('ok', 'crop')


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the party guest catalog']
    out = []
    if c['cls'] in ('sit',) or 'no ' in c['note']:
        out.append(c['note'])
    return out + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {
    SHEET + '01-couch-lean-hand-to-chest': ['jacket front panel right of the tee, under his chest hand, is plain filled denim '
                                            '(no piping); a few edge specks at the seat where the couch was cut away'],
    SHEET + '03-mouth-words-we-not': ['raised palms land a little lower and smaller than painted (forearms foreshortened toward '
                                      'the camera, clamped)'],
    SHEET + 'part-9': ['clipped card: his right arm is off the card, the rig hangs it at his side (guessed); right leg too (guessed down '
                       'the card edge); head is the lighter card\'s, mirrored (the own face is cut in half)'],
}

# props held in a hand: a skin-only hand cut would drop them (card px, wrist and elbow points)
CURATED_PARTS = {
    'lighterR': dict(kind='hand', side='R', src=SHEET + '04-lighter-up-2',
                     poly=[(0, 0), (31, 0), (31, 63), (24, 67), (4, 67), (0, 63)], wr=(16, 69), el=(50, 110), seat_r=5,
                     attrs={'shape': 'lighter'}),
    'phoneL': dict(kind='hand', side='L', src=SHEET + 'part-9',
                   poly=[(126, 0), (161, 0), (161, 57), (150, 60), (135, 58), (126, 48)], wr=(147, 61), el=(119, 106), seat_r=5,
                   attrs={'shape': 'phone'}),
    # 03's raised right palm without the shoulder brad its own cut took over the thumb
    'palmR03': dict(kind='hand', side='R', src=SHEET + '03-mouth-words-we-not',
                    poly=[(26, 52), (64, 52), (66, 100), (60, 112), (54, 117), (34, 118), (28, 105), (24, 80)],
                    wr=(46, 121), el=(34, 154), seat_r=5, attrs={'shape': 'palm'}),
    # (axis: the card's torso axis, parts.torso_axis)
    # bearded heads the automatic window chops at the jaw (it narrows to the neck): whole head and
    # neck down to the collar, cut by hand; no edge along the collar seat
    'head04': dict(kind='head', src=SHEET + '04-lighter-up-2',
                   poly=[(108, 40), (130, 30), (160, 32), (170, 50), (168, 80), (162, 93), (150, 97), (125, 97), (112, 92), (104, 80),
                         (100, 60)], neck=(140, 102), axis=-1.5173, seat_line=[(110, 93), (165, 93)], attrs={'gaze': 'up'}),
    'head03': dict(kind='head', src=SHEET + '03-mouth-words-we-not',
                   poly=[(98, 0), (150, 0), (155, 30), (150, 55), (140, 70), (130, 78), (108, 80), (100, 72), (96, 50), (94, 25)],
                   neck=(113, 84), axis=-1.5669, seat_line=[(98, 76), (140, 76)], attrs={'gaze': 'front'}),
    'head01': dict(kind='head', src=SHEET + '01-couch-lean-hand-to-chest',
                   poly=[(140, 15), (160, 0), (205, 0), (215, 30), (214, 55), (208, 72), (200, 80), (180, 83), (166, 81), (158, 72),
                         (150, 62), (140, 50)], neck=(182, 86), axis=-1.9691, seat_line=[(150, 79), (210, 79)], attrs={'gaze': 'side'}),
}
POSTURE_RIGS = {'sit': 'sit'}
VIEW_RIGS = {'front': ('front', False), '3qR': ('front', False), '3qL': ('front', False), 'profR': ('front', False),
             'profL': ('front', False), 'back': ('back', False), 'back3qR': ('back', False), 'back3qL': ('back', False)}
KEYS = {
    # the sit master: his own painted hands (one on his chest over the tee) and his own head (the
    # card is cut flush with the top of his hair, so the automatic head check refuses it)
    SHEET + '01-couch-lean-hand-to-chest': {'hands': {}, 'head': ['head01', False]},
    SHEET + '03-mouth-words-we-not': {'hands': {'R': ['palmR03', False], 'L': [SHEET + '03-mouth-words-we-not#handL', False]},
                                      'head': ['head03', False]},
}
KEYS[SHEET + '04-lighter-up-2'] = {'hands': {'R': ['lighterR', False], 'L': [SHEET + '04-lighter-up-2#handL', False]},
                                   'head': ['head04', False]}
# the selfie card is clipped through his face: the lighter card's upturned head, mirrored to look up at the phone;
# the phone hand is a curated part
KEYS[SHEET + 'part-9'] = {'hands': {'L': ['phoneL', False]}, 'head': ['head04', True]}

# marker corrections (card px): part-9's right arm is off the clipped card (MoveNet put the elbow at
# x = -17 with confidence 0.04); hang it at his side, at the card edge
# 02's neck marker sits on the chain pendant, below the shoulder line (chin-neck 0.31 torso lengths
# against 0.14-0.19 on every other card): put it at the base of the neck like the others, so heads
# seat at the same collar height on the front rig
# its right leg is clipped too (MoveNet piled both legs on the visible left one): down the card edge
MARKER_FIX = {SHEET + 'part-9': {'elbowR': (2, 160), 'wristR': (0, 214), 'kneeR': (4, 310), 'ankleR': (0, 394), 'toeR': (-30, 424)},
              SHEET + '02-mouth-words-we-love': {'neck': (162, 79)}}

# the cards' scale prior (2.36 px/cm, "tallest standing figure on the sheet") puts his standing
# torsos above 54 cm, so parts.torso_len would swap in 45 cm and his own heads and hands would be
# placed 1.23x too big: trust the marker torso
SCALE_PRIOR = False
