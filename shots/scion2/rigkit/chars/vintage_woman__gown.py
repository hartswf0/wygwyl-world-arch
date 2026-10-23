"""The VINTAGE PARTY WOMAN (poems 01.4-01.5, 14.5-14.6): ivory satin gown with a thigh slit, long
ivory opera gloves, gold drop earrings, finger-waved black hair, ivory heels with ankle straps, brass
brads.  One painted woman for the 1930s couples (many crowd instances).

Her legs are under a full, flared gown in every painting (the Pose Lab knee and ankle markers are
MoveNet guesses through the satin).  The skirt is a rigid bell: skinned to the leg bones it would shear
as the legs move.  So every main card is its own master, and a card posed on another card's rig keeps
that master's legs, and so its skirt (KEYS 'set' below): only the torso, arms and head pose.
Masters (cut automatically from their Pose Lab markers, rigkit/auto.py):
  front  : party.vintage_party.paired-choreography/party-vintage-party-2 (front, a coupe raised in her
           right hand: the glass is part of the front rig's hand; card clipped at the bottom and right)
  q3r    : party.vintage_party.main-poses/dance-threequarter-2       (3/4 to screen right, dancing)
  prof   : party.vintage_party.main-poses/dance-profile-2            (profile to screen right, dancing)
  back3q : party.vintage_party.main-poses/dance-threequarter-back-party-vintage-party-main (3/4 from behind)
  back   : party.vintage_party.paired-choreography/open-a-gap-2      (from behind, one arm out to her partner)
  backdance : party.vintage_party.main-poses/dance-back-2            (from behind, both arms raised)
party.14...gown_woman.parts.02/a-dance-threequarter-back and /dance-back are smaller repaints of the
3/4-back and back dances: posed on those rigs (arms, torso, head), with the master's skirt.
Couple holds are 2-figure cards only (waltz instances): not rigged.  She is not the poet's muse.
Markers: shots/rig/poses/vintage_woman__gown.json (MoveNet).
"""
import math
import numpy as np, cv2

from .. import auto, core


CHAR = 'vintage_woman__gown'
MP = 'party.vintage_party.main-poses/'
PC = 'party.vintage_party.paired-choreography/'
P14 = 'party.14.action.vintage_party.gown_woman.parts.02/'
MARKER_FILES = ['shots/rig/poses/vintage_woman__gown.json']
MARKER_FIX = {}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=7):
    """ivory satin: light warm pixels well inside the figure, not brass, not skin, not hair"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    ivory = (r > 170) & (g > 150) & (b > 110) & (r - b < 80)
    gold = (r > 110) & (r - b > 40) & (r > g) & (g < 0.75 * r)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    near_gold = cv2.dilate(gold.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    return ivory & e & ~near_gold


def paper(rgb, a, min_area=30):
    """the white glow outside her tan card edge: bright unsaturated patches touching the outside of the
    card (her ivory satin is as pale, so a patch enclosed by the figure is never cut)"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    white = ((mn > 195) & (mx - mn < 30) & (a > 0.5)).astype(np.uint8)
    outside = a <= 0.5
    n, lab, st, _ = cv2.connectedComponentsWithStats(white)
    keep = np.zeros(a.shape, bool)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < min_area:
            continue
        x, y, w, h = st[i, :4]
        x0, y0, x1, y1 = max(0, x - 3), max(0, y - 3), x + w + 3, y + h + 3
        comp = lab[y0:y1, x0:x1] == i
        ring = (cv2.dilate(comp.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~comp
        if outside[y0:y1, x0:x1][ring].mean() > 0.25:
            keep[y0:y1, x0:x1] |= comp
    return cv2.dilate(keep.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0


def whole_head(S, rgb, m):
    """the head window (narrowing to the neck, centred on the chin) cuts the back of her finger-waved
    hair off in profile and 3/4: every painted pixel above the neck line, within 0.75 torso lengths of
    the chin and on no arm, joins the head layer.  The torso is then closed over pinholes its opening
    left (they showed the legs' paper edge through the satin)."""
    fig, T = S['fig'], S['T']
    H, W = fig.shape
    yy, xx = np.mgrid[0:H, 0:W]
    nk, ch = m['neck'][:2], m['chin'][:2]
    arms = np.zeros(fig.shape, bool)
    for L in S['layers']:
        if L['name'].startswith('arm'):
            arms |= L['alpha'] > 0.5
    arms = cv2.dilate(arms.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    top = fig & (yy < nk[1] - 0.12 * T) & (np.hypot(xx - ch[0], yy - ch[1]) < 0.75 * T) & ~arms
    n, lab, st, _ = cv2.connectedComponentsWithStats(top.astype(np.uint8))
    if n > 1:
        top = lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    for L in S['layers']:
        if L.get('is_head'):
            L['alpha'] = np.maximum(L['alpha'], top.astype(np.float32))
            L['rgb'] = np.where(top[..., None], rgb, L['rgb'])
        elif L['bones'] == 'torso':
            al = L['alpha'] > 0.5
            ff = al.astype(np.uint8).copy()
            mk = np.zeros((H + 2, W + 2), np.uint8)
            cv2.floodFill(ff, mk, (0, 0), 1)
            holes = (ff == 0) & fig
            L['alpha'] = np.where(holes, 1.0, np.where(top, 0, L['alpha'])).astype(np.float32)
            L['rgb'] = np.where(holes[..., None], rgb, L['rgb'])
    # painted pixels no layer owns (a stray piece the torso dropped as not its main component): to the
    # legs below the waist, to the torso above (only near the spine)
    owned = np.zeros(fig.shape, bool)
    for L in S['layers']:
        owned |= L['alpha'] > 0.5
    J = S['joints']
    nk_, mh_ = np.array(J['neck']), np.array(J['midhip'])
    ab = mh_ - nk_
    t = np.clip(((xx - nk_[0]) * ab[0] + (yy - nk_[1]) * ab[1]) / float(ab @ ab), 0, 1)
    spine_d = np.hypot(xx - (nk_[0] + t * ab[0]), yy - (nk_[1] + t * ab[1]))
    lost = fig & ~owned & (spine_d < 0.45 * T)       # not glove slivers out by the raised hands
    low = yy > J['waist'][1]
    for L in S['layers']:
        take = lost & (low if L['name'] == 'legs' else ~low if L['bones'] == 'torso' else np.zeros_like(lost))
        if take.any():
            L['alpha'] = np.where(take, 1.0, L['alpha']).astype(np.float32)
            L['rgb'] = np.where(take[..., None], rgb, L['rgb'])
    return S


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


# long opera gloves and spread gloved fingers: arm masks wider and longer than the default, and the
# torso opened so no glove sliver outside them stays on it (a ghost forearm once the arm moves)
AUTO_OPTS = {'tip_len': 0.5, 'torso_over_legs': False, 'limb_r': (0.2, 0.17), 'open_torso': 0.1}


def auto_view(view, **extra):
    def fn(rgb, a):
        a = np.where(paper(rgb, a), 0, a)
        S = auto.build_auto(rgb, a, _mk(MASTERS[view][0]), plain_fn=PLAIN_FABRIC, **dict(AUTO_OPTS, **extra))
        # her brads stay painted: brass-finding takes her warm skin and the satin highlights for brads
        # (and nearly every pose is its own master, so nothing bends round them)
        S['brads'] = []
        # her shoulders and back are bare skin: the torso's filled-in satin must not show there.  The
        # torso keeps the painted pixels wherever the figure is painted; only the area outside the
        # painted figure (under a raised arm) stays filled
        for L in S['layers']:
            if L['bones'] == 'torso':
                L['rgb'] = np.where(S['fig'][..., None], rgb, L['rgb'])
        return whole_head(S, rgb, _mk(MASTERS[view][0]))
    return fn


MASTERS = {
    'front': (PC + 'party-vintage-party-2', auto_view('front')),
    'q3r': (MP + 'dance-threequarter-2', auto_view('q3r')),
    'prof': (MP + 'dance-profile-2', auto_view('prof')),
    'back3q': (MP + 'dance-threequarter-back-party-vintage-party-main', auto_view('back3q')),
    'back': (PC + 'open-a-gap-2', auto_view('back')),
    'backdance': (MP + 'dance-back-2', auto_view('backdance')),
}
MASTER_FACING = {'front': None, 'q3r': 'R', 'prof': 'R', 'back3q': 'R', 'back': None, 'backdance': None}
BACK_RIGS = ('back3q', 'back', 'backdance')
# required by the rig builder; never drawn (her brads stay painted, see auto_view)
BRAD_SOURCE = (MP + 'dance-threequarter-2', 150.0, 93.0, 5.0, 6.5)

_C = {
    PC + 'party-vintage-party-2': ('front', 'stand', 'crop', 'side', 'a coupe raised in her right hand'),
    MP + 'dance-threequarter-2': ('3qR', 'dance', 'ok', 'side', 'dancing'),
    MP + 'dance-profile-2': ('profR', 'dance', 'ok', 'side', 'dancing'),
    MP + 'dance-threequarter-back-party-vintage-party-main': ('back3qR', 'dance', 'ok', 'side', 'dancing, from behind'),
    PC + 'open-a-gap-2': ('back', 'stand', 'ok', 'away', 'one arm out to her partner (not in the rig)'),
    MP + 'dance-back-2': ('back', 'dance', 'ok', 'away', 'both arms raised'),
    P14 + 'a-dance-threequarter-back': ('back3qR', 'dance', 'ok', 'side', 'smaller repaint of the 3/4-back dance'),
    P14 + 'dance-back': ('back', 'dance', 'ok', 'away', 'smaller repaint of the back dance'),
}


def catalog():
    return {k: dict(costume='gown', use=u, view=v, cls=c, props=[], hands='', gaze=g, note=n) for k, (v, c, u, g, n) in _C.items()}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the vintage woman catalog']
    out = [c['note']] if 'not in the rig' in c['note'] else []
    return out + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {}
CURATED_PARTS = {}
POSTURE_RIGS = {}
VIEW_RIGS = {'front': ('front', False), '3qR': ('q3r', False), '3qL': ('q3r', True), 'profR': ('prof', False),
             'profL': ('prof', True), 'back': ('back', False), 'back3qR': ('back3q', False), 'back3qL': ('back3q', True)}
# masters: their own painted head and gloved hands (a skin-only hand cut finds no glove)
KEYS = {MASTERS[v][0]: {'head': None, 'hands': {}} for v in MASTERS}
KEYS[MP + 'dance-back-2']['view'] = 'backdance'
# the coupe in her raised left hand, cut with the gloved hand (the rig's arm layer keeps only an arm's
# width round the bones and drops the glass)
CURATED_PARTS['coupeL'] = dict(kind='hand', side='L', src=PC + 'party-vintage-party-2',
                               poly=[(0, 36), (40, 36), (38, 52), (30, 58), (40, 64), (44, 74), (40, 82), (24, 84), (8, 80),
                                     (10, 70), (18, 66), (18, 56), (4, 50)], wr=(34, 80), el=(72, 109), seat_r=5,
                               attrs={'shape': 'coupe'})
KEYS[PC + 'party-vintage-party-2']['hands'] = {'L': ['coupeL', False]}
# a card posed on another card's rig keeps that master's legs, and so its rigid skirt bell
_SKIRT = {'set': {b + sd: 0 for b in ('thigh', 'shin', 'foot') for sd in 'RL'},
          'len': {b + sd: 1.0 for b in ('lthigh', 'lshin') for sd in 'RL'}}
# the two parts.02 repaints are straight backs with both arms raised: the dance-back-2 rig.  dance-back
# keeps that rig's painted head (its own is clipped by the card top); the 3/4 one turns her head to
# screen right in profile; no back-view head of hers does that on this rig, so it keeps the rig's
# painted back-of-head (her face is not invented)
KEYS[P14 + 'dance-back'] = dict(_SKIRT, view='backdance', head=None, hands={})
KEYS[P14 + 'a-dance-threequarter-back'] = dict(_SKIRT, view='backdance', head=None, hands={})
EXTRA_FLAGS[P14 + 'dance-back'] = ['on the dance-back-2 rig: its skirt and legs are that master\'s (her own skirt swings wider)']
EXTRA_FLAGS[P14 + 'a-dance-threequarter-back'] = ['on the dance-back-2 rig (her body is a straight back with both arms up): its skirt, '
                                                  'legs and head (back of her head) are that master\'s; her painted profile turn of the head is not reached']
SCALE_PRIOR = False
