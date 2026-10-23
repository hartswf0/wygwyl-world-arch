"""The ANCESTORS of poem 05 (IDA, RUTH, MAE, CORA and one unnamed man): indigo robes woven with
gold, copper shoulder plates, gold neck rings, cowrie cuffs, head wraps; copper disc ornaments all
over the robe (they are not joint brads).

Five whole-figure paintings, all labelled "REFERENCE ONLY" (assembled references, not cut parts) and
all the same pose: standing front, arms down.  Each is a different person (her head and wrap make the
identity), so each card is its own master and keeps its own head; no head is swapped between them and
no face is invented.
  ida  : ancestors.05.identities.01/ida-reference-only
  ruth : ancestors.05.identities.02/ruth-reference-only
  mae  : ancestors.05.identities.02/mae-reference-only   (a gold sun-ray halo round her wrap: part of her head)
  cora : ancestors.05.identities.03/reference-only       (captioned CORA)
  man  : ancestors.05.identities.03/reference-only-2     (bearded man, unnamed)
The robes hide the legs: knee markers are guesses; the robe skirt is one piece on the legs.  No 3/4,
profile, walking or back painting exists (cast_plan gap: 05.1 "pan past" in profile); the orb hand-off
is a 2-figure card only.  The elder AMOS is chars/ancestor_elder__white_silver.py.
Markers: shots/rig/poses/ancestor_robe__indigo_gold.json (MoveNet).
"""
import numpy as np, cv2

from .. import auto, core

CHAR = 'ancestor_robe__indigo_gold'
S1, S2, S3 = 'ancestors.05.identities.01/', 'ancestors.05.identities.02/', 'ancestors.05.identities.03/'
MARKER_FILES = ['shots/rig/poses/ancestor_robe__indigo_gold.json']
MARKER_FIX = {}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=5):
    """the indigo robe: dark blue pixels well inside the figure"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    indigo = (b > r + 15) & (b < 140) & (r < 80)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    return indigo & e


def _mk(pid):
    return core.load_markers(CHAR)[pid]['markers']


AUTO_OPTS = {'tip_len': 0.35, 'hand_skin': True, 'torso_over_legs': False, 'limb_r': (0.2, 0.2)}
BORDER = 2.5
PART_BORDER = 2.5


def whole_head(S, rgb, m, below=0.0):
    """her head wrap (and MAE's halo) is wider and taller than the head window: every painted pixel
    above the shoulder plates' top, within 0.9 torso lengths of the chin and on no arm, joins the head
    layer; the gold neck rings stay on the torso"""
    fig, T = S['fig'], S['T']
    yy, xx = np.mgrid[0:fig.shape[0], 0:fig.shape[1]]
    cut_y = m['neck'][1] - below * T
    arms = np.zeros(fig.shape, bool)
    for L in S['layers']:
        if L['name'].startswith('arm'):
            arms |= L['alpha'] > 0.5
    top = fig & (yy < cut_y) & (np.hypot(xx - m['chin'][0], yy - m['chin'][1]) < 0.9 * T) & ~arms
    n, lab, st, _ = cv2.connectedComponentsWithStats(top.astype(np.uint8))
    if n > 1:
        top = lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    for L in S['layers']:
        if L.get('is_head'):
            L['alpha'] = top.astype(np.float32)
            L['rgb'] = rgb.copy()
            L['edgeok'] = (yy < cut_y - 3).astype(np.float32)
        elif L['bones'] == 'torso':
            L['alpha'] = np.where(top, 0, L['alpha']).astype(np.float32)
        else:
            L['alpha'] = np.where(top, 0, L['alpha']).astype(np.float32)
    return S


def robe_split(S, rgb, m):
    """a long robe is one piece of cloth from the shoulders to the boots: the auto cut tears it between
    the torso (filled quad) and the legs (limb widths), leaving a hole at the hips.  Here every painted
    pixel on no arm and not the head is the torso above the hip line and the robe skirt (legs layer)
    below it; the join carries no paper edge"""
    fig, T = S['fig'], S['T']
    yy, xx = np.mgrid[0:fig.shape[0], 0:fig.shape[1]]
    painted = lambda L: (L['alpha'] > 0.5) & fig & (np.abs(L['rgb'] - rgb).sum(-1) < 1)
    taken = np.zeros(fig.shape, bool)
    for L in S['layers']:
        if L['name'].startswith('arm') or L.get('is_head'):
            taken |= painted(L)
    mid = (np.array(m['hipR'][:2]) + np.array(m['hipL'][:2])) / 2
    up = np.array(m['neck'][:2]) - mid
    up /= np.linalg.norm(up)
    h = (xx - mid[0]) * up[0] + (yy - mid[1]) * up[1]
    rest = fig & ~taken
    for L in S['layers']:
        if L['bones'] == 'torso':
            L['rgb'] = rgb.copy()
            L['alpha'] = (rest & (h >= 0)).astype(np.float32)
            L['edgeok'] = (h > 3).astype(np.float32)
        elif L['name'] == 'legs':
            L['rgb'] = rgb.copy()
            L['alpha'] = (rest & (h < 2)).astype(np.float32)
            L['edgeok'] = (h < -3).astype(np.float32)
    return S


def own_paint(S, rgb):
    """each card is its own master: the torso and robe keep the painted pixels wherever the figure is
    painted; painted pixels no layer took go to the torso"""
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


def auto_view(view, border=BORDER, **extra):
    def fn(rgb, a):
        m = _mk(MASTERS[view][0])
        a = a.copy()
        a[:, :4] = 0          # reference-only-2 carries a thin grey frame line down its left edge
        # the pale floor shadow painted between the boots is opaque on the card: cut (their boots and
        # robes are dark, nothing else down there is that pale)
        b_, g_, r_ = [rgb[..., i] for i in range(3)]
        mx, mn = np.maximum(np.maximum(r_, g_), b_), np.minimum(np.minimum(r_, g_), b_)
        yy = np.mgrid[0:a.shape[0], 0:a.shape[1]][0]
        a[(mn > 195) & (mx - mn < 35) & (yy > min(m['ankleR'][1], m['ankleL'][1]) - 10)] = 0
        S = auto.build_auto(rgb, a, m, plain_fn=PLAIN_FABRIC, erase_emblem=False, **dict(AUTO_OPTS, **extra))
        S['border'] = border
        # the robe's copper disc ornaments would pass for brads: all stay painted
        S['brads'] = []
        return robe_split(whole_head(own_paint(S, rgb), rgb, m), rgb, m)
    return fn


_IDS = {'ida': S1 + 'ida-reference-only', 'ruth': S2 + 'ruth-reference-only', 'mae': S2 + 'mae-reference-only',
        'cora': S3 + 'reference-only', 'man': S3 + 'reference-only-2'}
MASTERS = {k: (pid, auto_view(k)) for k, pid in _IDS.items()}
# MAE's halo rays are 1-2 px wide and painted without a paper edge: the usual 2.5 px edge strip erases
# them, so her card's strip is thin
def build_mae(rgb, a):
    """MAE: thin edge strip; her halo (sun rays) and the top of her wrap get no paper edge, and the
    white glow painted round them is dropped"""
    S = auto_view('mae', border=0.6)(rgb, a)
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    glow = (mn > 180) & (mx - mn < 60)
    m = _mk(_IDS['mae'])
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    T = S['T']
    off_face = np.hypot(xx - m['chin'][0], yy - (m['chin'][1] - 0.2 * T)) > 0.3 * T
    above = S['fig'] & (yy < m['chin'][1] - 0.15 * T)     # the outer rays, beyond the head radius
    for L in S['layers']:
        if L['bones'] == 'torso':
            L['alpha'] = np.where(above, 0, L['alpha']).astype(np.float32)
        elif L.get('is_head'):
            L['alpha'] = np.where(above, 1.0, L['alpha']).astype(np.float32)
            L['rgb'] = np.where(above[..., None], rgb, L['rgb'])
    for L in S['layers']:
        if L.get('is_head'):
            L['alpha'] = np.where(glow & off_face, 0, L['alpha']).astype(np.float32)
            # the halo and the wrap's top carry no paper edge in the painting: none drawn there
            L['edgeok'] = np.where(yy < m['chin'][1] - 0.15 * T, 0, L['edgeok']).astype(np.float32)
    return S


MASTERS['mae'] = (_IDS['mae'], build_mae)
MASTER_FACING = {k: None for k in _IDS}
BACK_RIGS = ()
# required by the rig builder; never drawn (see auto_view)
BRAD_SOURCE = (S1 + 'ida-reference-only', 78.0, 150.0, 4.0, 5.0)

_NAMES = {'ida': 'IDA', 'ruth': 'RUTH', 'mae': 'MAE', 'cora': 'CORA', 'man': 'an unnamed bearded man'}


def catalog():
    return {pid: dict(costume='robe', use='label', view='front', cls='stand', props=[], hands='', gaze='front',
                      note='%s, standing front, arms down' % _NAMES[k]) for k, pid in _IDS.items()}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    if tid not in cat:
        return ['painting not in the ancestors catalog']
    return ['card carries a printed caption (not in the rig); labelled REFERENCE ONLY',
            '("no usable head" below: none is swapped in; each card is its own master and keeps its own head: '
            'each head is a different ancestor)',
            'robe hides the legs: knees are guesses; front only (no 3/4, profile, walk or back painting)'] + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {}
CURATED_PARTS = {}
POSTURE_RIGS = {}
VIEW_RIGS = {v: ('ida', False) for v in ('front', '3qR', '3qL', 'profR', 'profL', 'back', 'back3qR', 'back3qL')}
# 'scale' pins each master onto its own painting (the solver's median limb ratio is 1.00-1.04 on a card
# against itself)
_SELF = {'ida': 1.002, 'ruth': 1.035, 'mae': 1.018, 'cora': 1.005, 'man': 1.01}
KEYS = {pid: {'view': k, 'head': None, 'hands': {}, 'scale': 1 / _SELF[k]} for k, pid in _IDS.items()}
SCALE_PRIOR = False
