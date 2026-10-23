"""The VINTAGE PARTY MAN (poems 01.4-01.5, 14.5-14.6): brown pinstripe three-piece suit, white
shirt, rust paisley tie, pocket square, black oxfords, brass brads ringed in gold; trimmed beard.
One painted man for the 1930s couples (many crowd instances).

Masters (cut automatically from their Pose Lab markers, rigkit/auto.py):
  front  : party.vintage_party.master/main-poses        (front, standing, arms down; face turned to screen
           right; both sleeves touch the card's side edges)
  q3r    : party.vintage_party.main-poses/dance-threequarter       (3/4 to screen right, dancing step)
  prof   : party.vintage_party.main-poses/dance-profile            (profile to screen right, dancing step)
  back   : party.vintage_party.paired-choreography/4-rear-pair-2 (straight back, standing, one arm reaching
           to his partner, who is on her own card): the neutral back
  backdance : party.vintage_party.main-poses/dance-back            (straight back, both arms up and out:
           on the neutral back rig the arms swing ~90 deg and the sleeves smear, so it keeps its own rig)
  back3q : party.vintage_party.main-poses/dance-threequarter-back  (3/4 from behind, to screen right)
separate-prop (paired choreography, front, a coupe in hand, card clipped at the lower left) is posed on
the front rig with its own head and the coupe cut with its hand.  party.14...suit_man.parts/dance-
threequarter-back is a larger repaint of the 3/4-back dance (ringed brads, head clipped by the card top):
on the back3q rig with that master's head.
Every card carries a white glow outside its tan card edge and, under some arms, white paper: cut away.
His brass brads sit inside painted gold rings; they are found with joint_brads below.
Couple holds exist only on 2-figure cards (waltz instances): not rigged here.
Markers: shots/rig/poses/vintage_man__suit.json (MoveNet).
"""
import numpy as np, cv2

from .. import auto, core

CHAR = 'vintage_man__suit'
MP = 'party.vintage_party.main-poses/'
PC = 'party.vintage_party.paired-choreography/'
FRONT = 'party.vintage_party.master/main-poses'
P14 = 'party.14.action.vintage_party.suit_man.parts/dance-threequarter-back'
MARKER_FILES = ['shots/rig/poses/vintage_man__suit.json']

MARKER_FIX = {
    # the card is clipped through his right shin (straight cut at y 307): MoveNet piled that ankle and toe
    # on the other foot; the shin is continued straight down the card edge (guessed), toe out
    PC + 'separate-prop': {'ankleR': (35, 350), 'toeR': (10, 368)},
    # the far elbow marker sat 17 px off its brad, below the sleeve: the cut lost the forearm
    MP + 'dance-threequarter-back': {'elbowL': (78, 141), 'wristL': (38, 172)},
}

DEPTH = {'pelvis': 0, 'chest': 0, 'thighR': 1, 'thighL': 1, 'shinR': 2, 'shinL': 2, 'footR': 3, 'footL': 3,
         'uarmR': 1, 'farmR': 2, 'handR': 3, 'uarmL': 1, 'farmL': 2, 'handL': 3, 'head': 0}


def PLAIN_FABRIC(rgb, fig, er=7):
    """the pinstripe wool: dark pixels well inside the figure, away from the brass brads and their
    gold rings (the pale pinstripes come along: they are the cloth)"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    dark = (r < 110) & (g < 95) & (b < 90)
    gold = (r > 110) & (r - b > 40) & (r > g)
    e = cv2.erode(fig.astype(np.uint8), np.ones((er, er), np.uint8)) > 0
    near_gold = cv2.dilate(gold.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
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


AUTO_OPTS = {'tip_len': 0.3, 'hand_skin': True, 'torso_over_legs': False}


def paper(rgb, a, min_area=30):
    """white card paper inside the cut-out: the glow outside the tan card edge and the paper left in
    gaps (under an arm): bright unsaturated patches whose surroundings are mostly tan card edge or
    empty (his white cuffs, collar and pocket square sit in skin and wool: kept)"""
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    white = ((mn > 195) & (mx - mn < 30) & (a > 0.5)).astype(np.uint8)
    out_ = (a <= 0.5) | ((r > 170) & (r - b > 35) & (r - b < 120) & (g > 130))
    n, lab, st, _ = cv2.connectedComponentsWithStats(white)
    keep = np.zeros(a.shape, bool)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < min_area:
            continue
        x, y, w, h = st[i, :4]
        x0, y0, x1, y1 = max(0, x - 4), max(0, y - 4), x + w + 4, y + h + 4
        comp = lab[y0:y1, x0:x1] == i
        ring = (cv2.dilate(comp.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~comp
        if out_[y0:y1, x0:x1][ring].mean() > 0.6:
            keep[y0:y1, x0:x1] |= comp
    return cv2.dilate(keep.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0


def auto_view(view, cut=None, **extra):
    def fn(rgb, a):
        a = np.where(paper(rgb, a), 0, a)
        if cut:
            a = _cut(a, cut)
        S = auto.build_auto(rgb, a, _mk(MASTERS[view][0]), plain_fn=PLAIN_FABRIC, **dict(AUTO_OPTS, **extra))
        S['brads'] = joint_brads(S, rgb, _mk(MASTERS[view][0]))
        return own_head(S, rgb, a, MASTERS[view][0])
    return fn


_JB = {'sh': ('shoulder', 'uarm'), 'el': ('elbow', 'farm'), 'hip': ('hip', 'thigh'), 'kn': ('knee', 'shin')}


def joint_brads(S, rgb, m, rad=4.5, thr=0.65, reach=0.25, sat=None):
    """his brass brads sit inside painted gold rings: auto.find_brads sees ring and brad as one blob
    too big for a brad and misses most of them (they would stay painted and smear as the joint bends).
    Here solid brass discs are found as peaks of brass density in a brad-sized disc (a thin ring, the
    rust tie or a lapel edge cannot fill one), then each joint marker takes the best peak within 0.25
    torso lengths, ranked by density and distance.  The rings stay painted.
    sat: also require (r - b) / r above it (warm ivory satin passes the plain brass test)"""
    T, fig = S['T'], S['fig']
    b, g, r = [rgb[..., i].astype(np.float32) for i in range(3)]
    gold = (r > 120) & (r - b > 45) & (r >= g) & (g > 0.6 * r) & fig
    if sat is not None:
        gold &= (r - b) > sat * r
    gold = gold.astype(np.float32)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * rad) | 1,) * 2).astype(np.float32)
    dens = cv2.filter2D(gold, -1, k / k.sum())
    peak = (dens >= thr) & (dens >= cv2.dilate(dens, np.ones((int(2 * rad) | 1,) * 2, np.uint8)) - 1e-6)
    n, lab, st, c = cv2.connectedComponentsWithStats(peak.astype(np.uint8))
    pairs = []
    for i in range(1, n):
        x, y = c[i]
        dv = float(dens[int(round(y)), int(round(x))])
        for j, (mk, _) in _JB.items():
            for sd in 'RL':
                p = m[mk + sd][:2]
                d = float(np.hypot(x - p[0], y - p[1]))
                if d < reach * T:
                    pairs.append((d / T - dv, j, sd, float(x), float(y)))
    pairs.sort()
    far = S['layers'][0]['name'][-1]          # auto draws the far arm first
    br = float(np.clip(0.045 * T, 5.0, 6.5))
    used_j, used_c, out = set(), set(), []
    for _, j, sd, x, y in pairs:
        if j + sd in used_j or (round(x), round(y)) in used_c:
            continue
        used_j.add(j + sd); used_c.add((round(x), round(y)))
        lay = 'arm' + sd if j in ('sh', 'el') else 'legs'
        bn = _JB[j][1] + sd
        if j == 'sh' and sd == far:
            lay, bn = 'torso', 'chest'
        out.append((j + sd, lay, bn, x, y, br, max(1.5 * br, 0.07 * T)))
    return out


# his heads, cut by hand down to the collar (card px).  The automatic window chops every one of
# them obliquely (the back of the skull in profile, the far cheek in 3/4) and the cards are cut flush
# with the top of his hair, so the automatic check refuses them all.
_HEADS = {
    FRONT: [(54, 70), (60, 56), (72, 49), (90, 48), (104, 54), (112, 64), (116, 78), (119, 90), (117, 100), (112, 108),
            (106, 116), (98, 119), (88, 118), (80, 112), (72, 104), (62, 98), (56, 88)],
    MP + 'dance-profile': [(87, 30), (92, 16), (104, 8), (120, 5), (140, 8), (152, 16), (158, 26), (163, 36), (160, 44), (158, 52),
                           (154, 60), (146, 66), (134, 68), (118, 68), (104, 66), (95, 62), (89, 48)],
    MP + 'dance-threequarter': [(76, 20), (84, 8), (98, 2), (115, 3), (128, 10), (135, 22), (139, 36), (137, 46), (134, 56),
                                (128, 64), (118, 68), (104, 70), (92, 68), (84, 58), (78, 44)],
    MP + 'dance-threequarter-back': [(118, 26), (124, 12), (138, 4), (156, 3), (170, 10), (180, 22), (185, 36), (183, 48), (178, 58),
                                     (168, 62), (150, 60), (136, 60), (126, 58), (119, 44)],
    MP + 'dance-back': [(124, 24), (128, 12), (138, 5), (152, 3), (166, 6), (176, 14), (180, 26), (178, 40), (172, 48), (166, 56),
                        (152, 58), (138, 57), (132, 50), (126, 40)],
    PC + 'separate-prop': [(43, 26), (48, 12), (60, 3), (78, 1), (92, 8), (99, 18), (104, 30), (102, 40), (99, 50), (94, 58),
                           (86, 62), (72, 62), (60, 60), (52, 56), (46, 44)],
    PC + '4-rear-pair-2': [(101, 28), (106, 14), (116, 5), (130, 3), (142, 8), (148, 20), (150, 34), (148, 46), (142, 54),
                           (130, 52), (118, 50), (108, 48), (103, 40)],
}


def _poly_mask(shape, poly):
    hm = np.zeros(shape, np.uint8)
    cv2.fillPoly(hm, [np.array(poly, np.int32)], 1)
    return hm > 0


def own_head(S, rgb, a, pid):
    """the rig's head layer is the hand-cut head; the torso and arms lose those pixels (the torso
    keeps the lowest few rows, under the collar seat)"""
    hm = _poly_mask(a.shape, _HEADS[pid]) & S['fig']
    ys = np.nonzero(hm)[0]
    yy = np.mgrid[0:a.shape[0], 0:a.shape[1]][0]
    for L in S['layers']:
        if L.get('is_head'):
            L['rgb'] = rgb.copy()
            L['alpha'] = hm.astype(np.float32)
            L['edgeok'] = np.ones(a.shape, np.float32)
        elif L['bones'] == 'torso':
            L['alpha'] = np.where(hm & (yy < ys.max() - 6), 0, L['alpha']).astype(np.float32)
        else:
            L['alpha'] = np.where(hm, 0, L['alpha']).astype(np.float32)
    return S


def _axis(pid):
    """parts.torso_axis of a card, from the raw marker file (no import-time load_markers)"""
    import json, math, os
    for f in MARKER_FILES:
        for t in json.load(open(os.path.join(core.ROOT, f)))['targets']:
            if t['id'] == pid:
                m = dict(t['markers'], **{k: list(v) for k, v in MARKER_FIX.get(pid, {}).items()})
                mid = (np.array(m['hipR'][:2]) + np.array(m['hipL'][:2])) / 2
                v = np.array(m['neck'][:2]) - mid
                return math.atan2(v[1], v[0]), list(m['neck'][:2])


MASTERS = {
    'front': (FRONT, auto_view('front')),
    'q3r': (MP + 'dance-threequarter', auto_view('q3r')),
    'prof': (MP + 'dance-profile', auto_view('prof')),
    'back': (PC + '4-rear-pair-2', auto_view('back')),
    'backdance': (MP + 'dance-back', auto_view('backdance')),
    'back3q': (MP + 'dance-threequarter-back', auto_view('back3q')),
}
MASTER_FACING = {'front': None, 'q3r': 'R', 'prof': 'R', 'back': None, 'backdance': None, 'back3q': 'R'}
BACK_RIGS = ('back', 'backdance', 'back3q')
# a clean brass brad: the 3/4 master's left shoulder (painting, cx, cy, brass r, sprite r)
BRAD_SOURCE = (MP + 'dance-threequarter', 152.5, 88.3, 5.5, 7.0)

# hand-read hints: (view, posture, use, gaze, note)
_C = {
    FRONT: ('front', 'stand', 'ok', 'side', 'standing, arms down'),
    MP + 'dance-threequarter': ('3qR', 'dance', 'ok', 'side', 'dancing step'),
    MP + 'dance-profile': ('profR', 'dance', 'ok', 'side', 'dancing step'),
    MP + 'dance-back': ('back', 'dance', 'ok', 'away', 'arms out'),
    MP + 'dance-threequarter-back': ('back3qR', 'dance', 'ok', 'side', 'dancing step, from behind'),
    PC + 'separate-prop': ('front', 'stand', 'crop', 'side', 'a coupe in his hand'),
    PC + '4-rear-pair-2': ('back', 'stand', 'ok', 'away', 'reaching for his partner (not in the rig)'),
    P14: ('back3qR', 'dance', 'crop', 'side', 'larger repaint of the 3/4-back dance; head clipped by the card top'),
}


def catalog():
    return {k: dict(costume='suit', use=u, view=v, cls=c, props=[], hands='', gaze=g, note=n) for k, (v, c, u, g, n) in _C.items()}


def is_character_painting(tid, cat):
    return tid in cat


def painting_flags(tid, cat):
    c = cat.get(tid)
    if not c:
        return ['painting not in the vintage man catalog']
    out = [c['note']] if 'not in the rig' in c['note'] else []
    return out + EXTRA_FLAGS.get(tid, [])


EXTRA_FLAGS = {
    PC + 'separate-prop': ['clipped card: his right shin below y 307 is off the card; the rig continues it straight down (guessed foot)',
                           'his body is turned a little toward the glass in the painting; the front rig keeps it square-on'],
    P14: ['head from the 3/4-back master (this card clips his own at the top)',
          'a repaint in another style (ringed brads with dark centres, a deeper lean, bigger head): on the 3/4-back rig his '
          'torso leans less than painted and the brads are the rig\'s plain brass'],
    PC + '4-rear-pair-2': ['his partner\'s hand is on her own card: the reaching hand is empty'],
}
_OWN = '("no usable head" below: none is swapped in; the rig draws its own hand-cut painted head)'
CURATED_PARTS = {}
for _pid, _poly in _HEADS.items():
    _ax, _nk = _axis(_pid)
    CURATED_PARTS['head:' + _pid.split('/')[-1]] = dict(kind='head', src=_pid, poly=_poly, neck=_nk, axis=_ax, no_edge=False,
                                                       attrs={'gaze': _C[_pid][3]})
POSTURE_RIGS = {}
VIEW_RIGS = {'front': ('front', False), '3qR': ('q3r', False), '3qL': ('q3r', True), 'profR': ('prof', False),
             'profL': ('prof', True), 'back': ('back', False), 'back3qR': ('back3q', False), 'back3qL': ('back3q', True)}
KEYS = {MASTERS[v][0]: {'head': None} for v in MASTERS}
for _pid in MASTERS.values():
    EXTRA_FLAGS.setdefault(_pid[0], []).append(_OWN)
# the coupe in his right hand, cut with the hand (a skin-only hand cut drops the glass)
CURATED_PARTS['coupeR'] = dict(kind='hand', side='R', src=PC + 'separate-prop',
                               poly=[(95, 104), (100, 92), (104, 84), (104, 67), (142, 66), (142, 90), (133, 100), (136, 113),
                                     (126, 117), (110, 114), (100, 112)], wr=(96, 106), el=(41, 136), seat_r=5,
                               attrs={'shape': 'coupe'})
# solved at 0.81 against a 0.70 torso (the guessed shin and his long arms): the head came out 1.16x its
# painted size; scaled to his torso
KEYS[PC + 'separate-prop'] = {'head': ['head:separate-prop', False], 'scale': 0.88, 'set': {'footR': 0},
                              'hands': {'R': ['coupeR', False], 'L': [PC + 'separate-prop#handL', False]}}
KEYS[MP + 'dance-back']['view'] = 'backdance'
# the solver's scale is the median of the torso, leg and arm ratios; on the dance masters the longer
# leg or arm (foreshortening differs side to side) pushes it to 1.07-1.09, so a master would not land
# on its own painting: pinned to 1 (scale multiplies the solved value)
KEYS[MP + 'dance-profile']['scale'] = 1 / 1.09
KEYS[MP + 'dance-threequarter']['scale'] = 1 / 1.07
KEYS[MP + 'dance-back']['scale'] = 1 / 1.01
KEYS[FRONT]['scale'] = 1 / 1.01
KEYS[P14] = {'head': ['head:dance-threequarter-back', False]}
SCALE_PRIOR = False
