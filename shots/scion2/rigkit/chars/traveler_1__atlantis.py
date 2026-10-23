"""The ATLANTIS TRAVELLERS (poem 06.0, 06.2, 06.4): blue-grey distressed greatcoat with epaulettes,
cream shirt, brown trousers, black lace-up boots, brass brads.  One costume, several people (the head
makes the identity).

Eleven whole-figure paintings, each its own master (separately painted cards, and each head is a
different traveller: no head is swapped between them, no face invented):
  f1..f5 : atlantis.06.crowd-head-variants/reference-only, -2, -3, traveler-2-, traveler-4-reference-only
           (standing FRONT, arms down; labelled REFERENCE ONLY; f1 and f3 carry captions "TRAVELER" and
           "TRAVELER_5" under their boots, cut away)
  b1..b5 : atlantis.06.plaza-twelve/traveler-1 ... traveler-5 (from BEHIND, both arms raised, heads turned
           up in profile)
  open   : atlantis.06.source-actions/citizen-1 (front, arms spread palms up, satchel on a strap; the card
           is clipped through his knees: the shins are continued below the card, guessed and off-canvas)
No 3/4, profile or walking painting exists (cast_plan gap: 06.0 "file of traveller silhouettes" walking in).
Markers: shots/rig/poses/traveler_1__atlantis.json (MoveNet).  Each card is only ever posed on its own rig.
"""
import numpy as np, cv2

from .. import auto, core
from .ancestor_robe__indigo_gold import whole_head, own_paint

CHAR = 'traveler_1__atlantis'
PZ = 'atlantis.06.plaza-twelve/'
HV = 'atlantis.06.crowd-head-variants/'
OPEN = 'atlantis.06.source-actions/citizen-1'
MARKER_FILES = ['shots/rig/poses/traveler_1__atlantis.json']
_IDS = {'f1': HV + 'reference-only', 'f2': HV + 'reference-only-2', 'f3': HV + 'reference-only-3',
        'f4': HV + 'traveler-2-reference-only', 'f5': HV + 'traveler-4-reference-only',
        'b1': PZ + 'traveler-1', 'b2': PZ + 'traveler-2', 'b3': PZ + 'traveler-3', 'b4': PZ + 'traveler-4', 'b5': PZ + 'traveler-5',
        'open': OPEN}

# the clipped card's knees are its brads on the bottom edge; shins continued straight down (guessed)
MARKER_FIX = {OPEN: {'kneeR': (163, 318), 'kneeL': (283, 318), 'ankleR': (160, 410), 'ankleL': (290, 410),
                     'toeR': (130, 425), 'toeL': (320, 425)}}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=7):
    """the blue-grey greatcoat: cool mid-grey pixels well inside the figure"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    coat = (b >= r) & (r > 50) & (r < 150) & (b < 170)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    return coat & e


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


def build_ref(view, caption_y=None):
    """the small reference fronts have no paper edge and a stair-stepped alpha: smoothed, 1 px strip;
    a caption under the boots is cut away"""
    def fn(rgb, a):
        if caption_y:
            a = a.copy()
            a[caption_y:] = 0
        sm = cv2.GaussianBlur((a > 0.5).astype(np.float32), (0, 0), 2.5)
        S = auto_view(view)(rgb, (sm > 0.5).astype(np.float32))
        S['border'] = 1.0
        return S
    return fn


MASTERS = {k: (pid, auto_view(k)) for k, pid in _IDS.items()}
for _k in ('f1', 'f2', 'f3', 'f4', 'f5'):
    MASTERS[_k] = (_IDS[_k], build_ref(_k, {'f1': 301, 'f3': 292}.get(_k)))
MASTER_FACING = {k: None for k in _IDS}
BACK_RIGS = ('b1', 'b2', 'b3', 'b4', 'b5')
# required by the rig builder; never drawn (see auto_view)
BRAD_SOURCE = (PZ + 'traveler-2', 120.0, 200.0, 5.0, 6.5)

_C = {
    'f1': ('front', 'stand', 'curly hair, standing front, arms down; REFERENCE ONLY, caption TRAVELER'),
    'f2': ('front', 'stand', 'bald, bearded (TRAVELER_3), standing front, arms down; REFERENCE ONLY'),
    'f3': ('front', 'stand', 'short locs, standing front, arms down; REFERENCE ONLY, caption TRAVELER_5'),
    'f4': ('front', 'stand', 'afro (TRAVELER_2), standing front, arms down; REFERENCE ONLY'),
    'f5': ('front', 'stand', 'cream head wrap (TRAVELER_4), standing front, arms down; REFERENCE ONLY'),
    'b1': ('back', 'stand', 'TRAVELER_1 (bearded), from behind, arms raised'),
    'b2': ('back', 'stand', 'TRAVELER_2 (afro), from behind, arms raised'),
    'b3': ('back', 'stand', 'TRAVELER_3 (bald), from behind, arms raised'),
    'b4': ('back', 'stand', 'TRAVELER_4 (head wrap), from behind, arms raised'),
    'b5': ('back', 'stand', 'TRAVELER_5 (locs), from behind, arms raised'),
    'open': ('front', 'stand', 'bearded traveller, arms spread palms up, satchel (card captioned TRAVELER_1 on a citizen-1 cut)'),
}


def catalog():
    return {_IDS[k]: dict(costume='greatcoat', use='label', view=v, cls=c, props=[], hands='', gaze='up', note=n)
            for k, (v, c, n) in _C.items()}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the travellers catalog']
    return [c['note'], 'card carries a printed caption (not in the rig)',
            '("no usable head" below: none is swapped in; each card is its own master and keeps its own head: '
            'each head is a different traveller)'] + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {OPEN: ['card clipped through his knees: the shins below are guessed and fall off the canvas',
                      'the satchel and its strap are painted on the coat: they ride the torso'],
               **{_IDS[k]: ['a small reference figure with no paper edge: the rig\'s paper edge is slightly wavy at full zoom']
                  for k in ('f1', 'f2', 'f3', 'f4', 'f5')}}
CURATED_PARTS = {}
POSTURE_RIGS = {}
VIEW_RIGS = {'front': ('f2', False), '3qR': ('f2', False), '3qL': ('f2', False), 'profR': ('f2', False),
             'profL': ('f2', False), 'back': ('b1', False), 'back3qR': ('b1', False), 'back3qL': ('b1', False)}
# 'scale' pins each master onto its own painting (the solver's median limb ratio on a card against itself)
_SELF = {'f1': 1.014, 'f2': 1.002, 'f3': 1.002, 'f4': 1.011, 'f5': 1.001, 'b1': 1.001, 'b2': 1.006, 'b3': 1.025, 'b4': 1.008,
         'b5': 1.027, 'open': 1.003}
KEYS = {pid: {'view': k, 'head': None, 'hands': {}, 'scale': 1 / _SELF[k]} for k, pid in _IDS.items()}
SCALE_PRIOR = False
