"""The ATLANTIS CITIZENS (poem 06.2, 06.4, 06.5): cream wrap suits with coral-and-teal trim, a sash
belt, black lace-up boots, brass brads.  One costume, several people (the head makes the identity).

Seven whole-figure paintings, each its own master (each is a separately painted card, and each head is
a different citizen: no head is swapped between them, no face invented):
  ref4   : atlantis.06.crowd-head-variants/reference-only-4  (CITIZEN_3, grey bob, standing FRONT, arms
           down; labelled REFERENCE ONLY, no brads painted)
  c1..c5 : atlantis.06.plaza-twelve/citizen-1 ... citizen-5   (from BEHIND, both arms raised to the light;
           c1 bearded man, c2 braided bun, c3 grey bob, c4 curls, c5 braids and bun; heads turned up in
           profile)
  guitar : atlantis.06.source-actions/part  (the guitar player, seated on a wooden crate, 3/4 to screen
           right; the card is captioned TRAVELER_1 but wears the citizen suit; the crate is cut away, the
           guitar stays in his arms)
No 3/4 or profile standing painting exists.  Markers: shots/rig/poses/citizen_1__atlantis.json (MoveNet).
The back cards' R/L are by screen side as MoveNet read them; each card is only ever posed on its own rig.
"""
import numpy as np, cv2

from .. import auto, core
from .ancestor_robe__indigo_gold import whole_head, own_paint

CHAR = 'citizen_1__atlantis'
PZ = 'atlantis.06.plaza-twelve/'
REF4 = 'atlantis.06.crowd-head-variants/reference-only-4'
GUIT = 'atlantis.06.source-actions/part'
MARKER_FILES = ['shots/rig/poses/citizen_1__atlantis.json']
_IDS = {'ref4': REF4, 'c1': PZ + 'citizen-1-twelve-crowd-instances', 'c2': PZ + 'citizen-2-working-body-shared-and-cores',
        'c3': PZ + 'citizen-3-supplied-and-separate-heads-on', 'c4': PZ + 'citizen-4-companion-sheets-on', 'c5': PZ + 'citizen-5',
        'guitar': GUIT}

MARKER_FIX = {}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=7):
    """the cream suit: light warm pixels well inside the figure, not the trim, not brass"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    cream = (r > 180) & (g > 165) & (b > 130) & (r - b < 70)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    return cream & e


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


def _cut(a, polys):
    a = a.copy()
    m = np.zeros(a.shape, np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    a[m > 0] = 0
    return a


AUTO_OPTS = {'tip_len': 0.4, 'hand_skin': True, 'torso_over_legs': False, 'limb_r': (0.2, 0.2)}


def lost_to_torso(S):
    """painted pixels no layer owns go to the torso (as own_paint does); called last"""
    fig = S['fig']
    owned = np.zeros(fig.shape, bool)
    for L in S['layers']:
        owned |= L['alpha'] > 0.5
    for L in S['layers']:
        if L['bones'] == 'torso':
            L['alpha'] = np.where(fig & ~owned, 1.0, L['alpha']).astype(np.float32)
    return S


def auto_view(view, cut=None, **extra):
    def fn(rgb, a):
        if cut:
            a = _cut(a, cut)
        m = _mk(MASTERS[view][0])
        S = auto.build_auto(rgb, a, m, plain_fn=PLAIN_FABRIC, erase_emblem=False, **dict(AUTO_OPTS, **extra))
        S['brads'] = []      # brads stay painted: each card is its own master
        return lost_to_torso(whole_head(own_paint(S, rgb), rgb, m))
    return fn


# the wooden crate under the guitar player (card px), less his near shin and boot in front of it
CRATE = [(34, 220), (182, 220), (182, 326), (34, 326)]
NEAR_LEG = [(104, 200), (162, 196), (164, 232), (152, 276), (160, 296), (162, 322), (96, 324), (97, 296), (106, 278), (104, 240)]


def build_ref4(rgb, a):
    """reference-only-4 is a reference figure without the cards' paper edge: its alpha is stair-stepped
    and its thin dark outline is the edge.  The alpha is smoothed and only 1 px is stripped."""
    sm = cv2.GaussianBlur((a > 0.5).astype(np.float32), (0, 0), 2.5)
    a = (sm > 0.5).astype(np.float32)
    # her wide sleeves: arm masks wide enough to take the whole sleeve (else its outer edge alternates
    # between the arm and the torso layer and the paper edge comes out wavy)
    S = auto_view('ref4', limb_r=(0.32, 0.2))(rgb, a)
    S['border'] = 1.0
    return S


def build_guitar(rgb, a):
    m = np.zeros(a.shape, np.uint8)
    cv2.fillPoly(m, [np.array(CRATE, np.int32)], 1)
    cv2.fillPoly(m, [np.array(NEAR_LEG, np.int32)], 0)
    a = np.where(m > 0, 0, a)
    return auto_view('guitar')(rgb, a)


MASTERS = {k: (pid, auto_view(k)) for k, pid in _IDS.items()}
MASTERS['guitar'] = (GUIT, build_guitar)
MASTERS['ref4'] = (REF4, build_ref4)
MASTER_FACING = {'ref4': None, 'c1': None, 'c2': None, 'c3': None, 'c4': None, 'c5': None, 'guitar': 'R'}
BACK_RIGS = ('c1', 'c2', 'c3', 'c4', 'c5')
# required by the rig builder; never drawn (see auto_view)
BRAD_SOURCE = (PZ + 'citizen-5', 120.0, 200.0, 5.0, 6.5)

_C = {
    'ref4': ('front', 'stand', 'CITIZEN_3 (grey bob), standing front, arms down; labelled REFERENCE ONLY'),
    'c1': ('back', 'stand', 'CITIZEN_1 (bearded man), from behind, arms raised'),
    'c2': ('back', 'stand', 'CITIZEN_2 (braided bun), from behind, arms raised'),
    'c3': ('back', 'stand', 'CITIZEN_3 (grey bob), from behind, arms raised'),
    'c4': ('back', 'stand', 'CITIZEN_4 (curls), from behind, arms raised'),
    'c5': ('back', 'stand', 'CITIZEN_5 (braids and bun), from behind, arms raised'),
    'guitar': ('3qR', 'sit', 'the guitar player, seated, playing; no crate in the rig (card captioned TRAVELER_1)'),
}


def catalog():
    return {_IDS[k]: dict(costume='wrap_suit', use='label', view=v, cls=c, props=[], hands='', gaze='up', note=n)
            for k, (v, c, n) in _C.items()}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the citizens catalog']
    return [c['note'], 'card carries a printed caption (not in the rig)',
            '("no usable head" below: none is swapped in; each card is its own master and keeps its own head: '
            'each head is a different citizen)'] + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {REF4: ['a small reference figure with no paper edge: the rig\'s paper edge along her sleeves is slightly wavy at full zoom'],
               GUIT: ['the guitar is painted across his body: it rides the torso and his hands stay on it only near this pose']}
CURATED_PARTS = {}
POSTURE_RIGS = {'sit': 'guitar'}
VIEW_RIGS = {'front': ('ref4', False), '3qR': ('ref4', False), '3qL': ('ref4', False), 'profR': ('ref4', False),
             'profL': ('ref4', False), 'back': ('c1', False), 'back3qR': ('c1', False), 'back3qL': ('c1', False)}
# 'scale' pins each master onto its own painting (the solver's median limb ratio on a card against itself)
_SELF = {'ref4': 1.01, 'c1': 1.049, 'c2': 1.007, 'c3': 1.016, 'c4': 1.029, 'c5': 1.017, 'guitar': 1.008}
KEYS = {pid: {'view': k, 'head': None, 'hands': {}, 'scale': 1 / _SELF[k]} for k, pid in _IDS.items()}
SCALE_PRIOR = False
