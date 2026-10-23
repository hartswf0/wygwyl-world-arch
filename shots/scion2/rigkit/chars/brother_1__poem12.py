"""BROTHER 1 (poem 12): grey hoodie, blue jeans, black-and-white sneakers, brass brads, beard.

Only two whole-figure paintings exist, both on family.12.brother_1.heads-hands:
  front  : welcome  (front, arms wide; the card carries a printed header bar "ASSEMBLED REFERENCES
           -- NOT CUT PARTS" across its top 26 rows, cut away)
  back3q : back     (3/4 from behind, turned to screen right, right arm reaching; his face shows in
           profile past his shoulder)
Both are small (torso ~80 px).  No profile and no straight back painting exists (cast_plan gap: the
12.5 brotherhood chain in profile), and the hugs are poet+brother 2-figure cards
(family.12.hug-restage): none is invented.  family.12.brother_1.body holds loose limb parts only.
Markers: shots/rig/poses/brother_1__poem12.json (MoveNet), corrected below.
"""
import numpy as np, cv2

from .. import auto, core

CHAR = 'brother_1__poem12'
SHEET = 'family.12.brother_1.heads-hands/'
MARKER_FILES = ['shots/rig/poses/brother_1__poem12.json']

# marker corrections (card px)
MARKER_FIX = {
    # MoveNet put both knees on the hips; his short, spread legs: ankles on the brads above the
    # sneakers, knees halfway down; chin on the beard's tip
    SHEET + 'welcome': {'kneeR': (262, 190), 'kneeL': (339, 187), 'ankleR': (256, 203), 'ankleL': (347, 200),
                        'toeR': (223, 217), 'toeL': (387, 217), 'hipR': (268, 175), 'hipL': (330, 172),
                        'neck': (296, 92), 'chin': (301, 83), 'shoulderR': (256, 103), 'shoulderL': (329, 100),
                        'elbowL': (365, 112), 'groin': (299, 180)},
    # from behind: the far (left) forearm is hidden in front of his body (MoveNet's wrist, conf 0.1,
    # sat on the elbow); a short stub past the elbow bulge (a longer one takes painted hoodie off his
    # back into the arm layer), its hand is not drawn
    SHEET + 'back': {'shoulderR': (106, 79), 'shoulderL': (41, 73), 'elbowL': (21, 92), 'wristL': (30, 103),
                     'hipL': (39, 141), 'hipR': (84, 145), 'kneeL': (23, 185), 'kneeR': (100, 172),
                     'ankleR': (91, 199), 'ankleL': (18, 198), 'toeR': (132, 215), 'toeL': (6, 212),
                     'neck': (80, 64), 'chin': (110, 57), 'head': (95, 3)},
}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=5):
    """grey fleece and denim: figure pixels well inside, not brass, skin, white (drawstrings,
    sneaker soles) or the black outline"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    gold = (r > 110) & (r - b > 40) & (r > g)
    skin = (r > g + 12) & (g > b + 15) & (r > 70)
    white = (r > 160) & (g > 160) & (b > 160)
    dark = (r < 30) & (g < 30) & (b < 35)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    near_gold = cv2.dilate(gold.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    return e & ~near_gold & ~skin & ~white & ~dark


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


def _cut(a, polys):
    a = a.copy()
    m = np.zeros(a.shape, np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    a[m > 0] = 0
    return a


# the printed header bar on the welcome card (rows 0-25, full width)
HEADER = [[(0, 0), (473, 0), (473, 25), (0, 25)]]

# his head is big against his short torso (chin only 0.1 torso lengths above the neck marker): a
# head window seated lower and taller than the adults' default
HEAD_WIN = (0.5, 1.0, 1.2, 0.08)
AUTO_OPTS = {'tip_len': 0.3, 'hand_skin': True, 'torso_over_legs': False, 'head_win': HEAD_WIN, 'limb_r': (0.2, 0.2)}


def auto_view(view, cut=None, **extra):
    def fn(rgb, a):
        if cut:
            a = _cut(a, cut)
        return auto.build_auto(rgb, a, _mk(MASTERS[view][0]), plain_fn=PLAIN_FABRIC, **dict(AUTO_OPTS, **extra))
    return fn


def own_head(S, rgb, a, key):
    """the head layer is the hand-cut head (_HEADS) instead of the automatic window: on these small
    cards the window either leaves the back of his skull on the torso (its axis leans toward his
    chin) or cuts across his hood, leaving a paper edge over the jaw.  The torso loses the skull
    above the hood line."""
    poly, _, _, sy = _HEADS[key]
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
            L['alpha'] = np.where(hm & (yy < sy - 10), 0, L['alpha']).astype(np.float32)
    return S


def build_front(rgb, a):
    return own_head(auto_view('front', HEADER)(rgb, a), rgb, a, 'welcome')


def build_back(rgb, a):
    """back: the auto cut calls the hidden left arm 'near' (its elbow bulge overlaps the torso quad
    more than the reaching right arm does).  From behind, turned to screen right, his right arm is
    the near one: it is drawn last, over the torso, with its shoulder brad.  Painted hoodie the left
    arm's mask took off his back (inside the shoulder-hip quad) goes back to the torso."""
    # the head window is centred on the chin, here at the face's edge (his head is in profile): wide
    # enough to reach the back of his skull
    S = auto_view('back3q', head_win=(0.75, 1.0, 1.2, 0.08))(rgb, a)
    J = S['joints']
    names = [L['name'] for L in S['layers']]
    if names[-1] == 'armL':
        L_arm, R_arm = S['layers'][-1], S['layers'][0]
        # the fade-into-the-torso seam belongs to the near arm's root: swap them
        L_arm['alpha'] = (L_arm['alpha'] > 0).astype(np.float32)
        L_arm['edgeok'] = np.ones_like(L_arm['alpha'])
        S['layers'] = [L_arm] + S['layers'][1:-1] + [R_arm]
        S['brads'] = [('shR', 'armR', 'uarmR') + tuple(b[3:]) if b[0] == 'shR' else b for b in S['brads']]
    S = own_head(S, rgb, a, 'back')
    quad = np.zeros(a.shape, np.uint8)
    cv2.fillPoly(quad, [np.array([J['shR'], J['shL'], J['hipL'], J['hipR']], np.int32)], 1)
    far = S['layers'][0]
    took = (quad > 0) & (far['alpha'] > 0.5) & S['fig']
    for L in S['layers']:
        if L['bones'] == 'torso':
            L['rgb'] = np.where(took[..., None], rgb, L['rgb'])
            L['alpha'] = np.where(took, 1.0, L['alpha']).astype(np.float32)
    return S


MASTERS = {
    'front': (SHEET + 'welcome', build_front),
    'back3q': (SHEET + 'back', build_back),
}
MASTER_FACING = {'front': None, 'back3q': 'R'}
BACK_RIGS = ('back3q',)
# a clean brass brad: the front master's left shoulder (painting, cx, cy, brass r, sprite r)
BRAD_SOURCE = (SHEET + 'welcome', 329.0, 100.0, 3.5, 4.5)

# hand-read hints: (view, posture, use, gaze, note)
_C = {
    'welcome': ('front', 'stand', 'label', 'front', 'arms wide in welcome'),
    'back': ('back3qR', 'stand', 'ok', 'side', 'from behind, reaching to screen right; face in profile past the shoulder'),
}


def catalog():
    return {SHEET + k: dict(costume='hoodie', use=u, view=v, cls=c, props=[], hands='', gaze=g, note=n)
            for k, (v, c, u, g, n) in _C.items()}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the brother catalog']
    out = []
    if c['use'] == 'label':
        out.append('card carries a printed header bar (cut away, not in the rig)')
    return out + EXTRA_FLAGS.get(tid, [])


_OWN = '("no usable head" below: none is swapped in; the rig draws its own hand-cut painted head)'
EXTRA_FLAGS = {
    SHEET + 'welcome': [_OWN, 'his only front; no profile or straight-back painting exists (12.5 profile chain not reachable); '
                              'hugs are poet+brother 2-figure cards only'],
    SHEET + 'back': ['far (left) forearm and hand are hidden in front of his body in the painting: not drawn', _OWN,
                     'the soft white glow under the reaching sleeve stays inside the paper edge (a pale band above the brown line)'],
}
# his heads, cut by hand down to the hoodie collar (card px; axis = parts.torso_axis of the fixed markers)
_HEADS = {
    'welcome': ([(268, 50), (272, 34), (285, 25), (305, 25), (316, 36), (318, 52), (316, 68), (312, 78), (305, 86), (295, 89),
                 (286, 86), (280, 80), (276, 72), (270, 66)], (296, 92), -1.6076, 88),
    'back': ([(66, 30), (72, 10), (92, 0), (110, 2), (118, 14), (120, 40), (116, 56), (110, 63), (104, 63), (92, 58),
              (78, 52), (68, 46)], (80, 64), -1.3405, 60),
}
CURATED_PARTS = {}
POSTURE_RIGS = {}
VIEW_RIGS = {'front': ('front', False), '3qR': ('front', False), '3qL': ('front', False), 'profR': ('front', False),
             'profL': ('front', False), 'back': ('back3q', False), 'back3qR': ('back3q', False), 'back3qL': ('back3q', True)}
KEYS = {}
# the cards' scale prior is not his (a small figure on a heads-and-hands sheet): trust the markers
SCALE_PRIOR = False


def _heads():
    for k, (poly, nk, ax, sy) in _HEADS.items():
        CURATED_PARTS['head:' + k] = dict(kind='head', src=SHEET + k, poly=poly, neck=nk, axis=ax,
                                          seat_line=[(0, sy), (500, sy)], attrs={'gaze': _C[k][3]})
        # each card is its own master: it keeps its rig's painted head (the hand cut above leaves out
        # hood pixels the rig's head window holds); the cut heads are there for other poses
        KEYS[SHEET + k] = {'head': None}


_heads()
KEYS[SHEET + 'back']['hands'] = {'L': 'none'}
