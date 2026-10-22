"""Pose Lab solver: snap a character's rig onto every drawn pose figure (shots/rig/solve.py).

    python3 shots/rig/solve.py                       # every character that has pose targets
    python3 shots/rig/solve.py poet/red_black_sunglasses [--only <part id substring>] [--quick]

Writes shots/rig/poses/<character>__<costume>.json (targets, detected brads, solves + alternatives, scores)
and shots/rig/poses/<character>__<costume>.contact.webp (target | snapped rig | overlay, per pose), and prints
the score distribution and the worst ten with the reason.

TARGETS  the drawn pose figures: catalog parts of kind 'pose', plus tall cards (>= 300 px, grade A/B) on the
         *main-poses sheets, mapped to a Rig Builder character through body.json's character/costume.
BRADS    the painted brass brads are found by colour (brass: hue 15-27 of 180, saturated, with a bright
         highlight; skin is hue ~12 so faces and hands drop out), components merged and refined with a local
         Hough circle; the cutter's catalog brads are the fallback when fewer than four brass discs are found.
SKELETON one 3D skeleton per character, measured from the Rig Builder's front cards at true scale (data/*.json):
         pelvis, waist, neck, shoulders, elbows, wrists, hips, knees, ankles, heel/toe. Body frame: X = the actor's
         LEFT, Y = DOWN, Z = FORWARD. Joints are swing angles in degrees (flexion forward +, abduction outward +;
         elbows and knees are hinges), with limits from the range-test norms (bolas/lab/range-test).
VIEW     a pane is a yaw psi: 0 front, +90 profile facing screen-right, +-45 three-quarter, 180 back.
         screen_x = X cos psi + Z sin psi + 0.12 depth |sin psi|  (a small oblique offset so near and far limbs
         separate in profile), depth = -X sin psi + Z cos psi (toward the camera), screen_y = Y.
SOLVE    per view and seed pose: (A) robust least squares over the joint angles + figure scale: every target brad
         pulls the nearest rig joint, rig points must stay inside the target silhouette, the target silhouette must
         be covered by the rig's limbs, angles are lightly pulled to neutral; (B) one-to-one matching of rig joints
         to target brads (Hungarian, 9 cm gate) and re-solve; (C) refine by silhouette IoU of the rendered cards.
SCORE    IoU (rig card alpha vs target alpha), per-joint error in cm for matched joints, joints > 4 cm flagged,
         joints with no target brad listed.
The same skeleton, projection, card placement and solver run live in shots/rig/pose-core.js.
"""
import json, os, sys, math, time, glob
from collections import defaultdict, Counter
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from scipy.optimize import least_squares, linear_sum_assignment

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'poses')

# ------------------------------------------------------------------------------------------- parameters
PN = ['ox', 'oy', 'oz', 'pitch', 'roll', 'twist', 'tf', 'tb', 'hf', 'hb',
      'shLf', 'shLb', 'elL', 'wrL', 'shRf', 'shRb', 'elR', 'wrR',
      'hpLf', 'hpLb', 'knL', 'anL', 'hpRf', 'hpRb', 'knR', 'anR', 'shLt', 'shRt', 'hpLt', 'hpRt',
      'kT', 'kU', 'kF', 'kTh', 'kSh', 'kHd']
# kT..kHd: log stretch of torso / upper arms / forearms / thighs / shins / head, used only while MATCHING a
# drawing whose proportions differ from the rig; the reported keyframe is re-solved with every k = 0.
PI = {n: i for i, n in enumerate(PN)}
NP = len(PN)
# joint limits (deg) from the range-test norms: shoulder 180, elbow 150, hip 120, knee 135, neck 50, trunk 90
LIM = {'pitch': (-120, 120), 'roll': (-100, 100), 'twist': (-50, 50), 'tf': (-30, 90), 'tb': (-35, 35),
       'hf': (-50, 60), 'hb': (-45, 45), 'shLf': (-60, 180), 'shLb': (-30, 180), 'elL': (0, 150), 'wrL': (-70, 70),
       'shRf': (-60, 180), 'shRb': (-30, 180), 'elR': (0, 150), 'wrR': (-70, 70),
       'hpLf': (-30, 125), 'hpLb': (-25, 70), 'knL': (0, 140), 'anL': (-45, 30),
       'hpRf': (-30, 125), 'hpRb': (-25, 70), 'knR': (0, 140), 'anR': (-45, 30),
       'shLt': (-90, 90), 'shRt': (-90, 90), 'hpLt': (-45, 45), 'hpRt': (-45, 45),
       'kT': (-.7, .4), 'kU': (-.7, .4), 'kF': (-.7, .4), 'kTh': (-.7, .4), 'kSh': (-.7, .4), 'kHd': (-.7, .4)}
KN = ['kT', 'kU', 'kF', 'kTh', 'kSh', 'kHd']
ANG = [i for i, n in enumerate(PN) if i >= 6 and n not in KN]
STEP = np.r_[[.002 if n in KN else .05 for n in PN], .002]
XSC = np.r_[[.05 if n in KN else 10.0 for n in PN], .1]
# labelled target markers (Mixamo-style; MoveNet + brads + the user) and the rig point each one pins
MARKERS = [('head', 'top'), ('chin', 'chin'), ('neck', 'neck'), ('shoulderL', 'shL'), ('shoulderR', 'shR'), ('elbowL', 'elL'),
           ('elbowR', 'elR'), ('wristL', 'wrL'), ('wristR', 'wrR'), ('groin', 'pelvis'), ('hipL', 'hipL'), ('hipR', 'hipR'),
           ('kneeL', 'knL'), ('kneeR', 'knR'), ('ankleL', 'anL'), ('ankleR', 'anR'), ('toeL', 'toeL'), ('toeR', 'toeR')]
MARKER_J = dict(MARKERS)
# drawn heads are big and stylised, toes are found from the silhouette: they pull less
MW = {'head': .5, 'chin': .5, 'toeL': .6, 'toeR': .6}
JOINTS = ['neck', 'waist', 'shL', 'shR', 'elL', 'elR', 'wrL', 'wrR', 'hipL', 'hipR', 'knL', 'knR', 'anL', 'anR']
SEGS = [('waist', 'neck', 14), ('pelvis', 'waist', 13), ('neck', 'top', 9), ('shL', 'elL', 5.5), ('elL', 'wrL', 4.5),
        ('wrL', 'tipL', 4), ('shR', 'elR', 5.5), ('elR', 'wrR', 4.5), ('wrR', 'tipR', 4), ('hipL', 'knL', 7),
        ('knL', 'anL', 5.5), ('heelL', 'toeL', 4), ('hipR', 'knR', 7), ('knR', 'anR', 5.5), ('heelR', 'toeR', 4)]
FLAT = [('shL', 'elL'), ('elL', 'wrL'), ('shR', 'elR'), ('elR', 'wrR'), ('hipL', 'knL'), ('knL', 'anL'),
        ('hipR', 'knR'), ('knR', 'anR'), ('waist', 'neck')]
INSIDE = ['top', 'headC', 'tipL', 'tipR', 'toeL', 'toeR', 'heelL', 'heelR', 'mUaL', 'mUaR', 'mFaL', 'mFaR',
          'mThL', 'mThR', 'mShL', 'mShR', 'chest', 'pelvis'] + JOINTS
# segment mass fractions (Dempster via Winter) and COM position from the proximal joint
MASS = [('pelvis', 'waist', .142, .5), ('waist', 'neck', .355, .5), ('neck', 'top', .081, .55),
        ('shL', 'elL', .028, .436), ('elL', 'wrL', .016, .43), ('wrL', 'tipL', .006, .506),
        ('shR', 'elR', .028, .436), ('elR', 'wrR', .016, .43), ('wrR', 'tipR', .006, .506),
        ('hipL', 'knL', .100, .433), ('knL', 'anL', .0465, .433), ('heelL', 'toeL', .0145, .5),
        ('hipR', 'knR', .100, .433), ('knR', 'anR', .0465, .433), ('heelR', 'toeR', .0145, .5)]


def lims(sandbox=False, stretch=False):
    lo = np.full(NP, -1e4); hi = np.full(NP, 1e4)
    for n, (a, b) in LIM.items():
        lo[PI[n]], hi[PI[n]] = (-180, 180) if sandbox and n not in ('pitch', 'roll') and n not in KN else (a, b)
    if not stretch:
        for n in KN: lo[PI[n]], hi[PI[n]] = -1e-6, 1e-6
    lo[PI['oz']], hi[PI['oz']] = -1e-6, 1e-6
    return lo, hi


# ------------------------------------------------------------------------------------------- rig data
def load_rig(key):
    doc = json.load(open(os.path.join(HERE, 'data', key.replace('/', '__') + '.json')))
    doc['P'] = {p['id']: p for p in doc['parts']}
    pp = sorted(p['ppc'] for p in doc['parts'] if p.get('ppc'))
    doc['ppcMedian'] = pp[len(pp) // 2] if pp else 8.0
    return doc


KIND = {'torso': 'torso', 'hip': 'hip', 'head': 'head', 'hand': 'hand', 'shoe': 'shoe'}


def pt(p, name):
    q = p.get('pts') or {}
    if name in q: return q[name]
    w, h = p['w'], p['h']; k = KIND.get(p['cls'], 'limb')
    F = {'pivot': [w / 2, .07 * h], 'socket': [w / 2, .93 * h], 'neck': [w / 2, .92 * h] if k == 'head' else [w / 2, .05 * h],
         'waist': [w / 2, .15 * h] if k == 'hip' else [w / 2, .95 * h], 'shVL': [.12 * w, .17 * h], 'shVR': [.88 * w, .17 * h],
         'hipVL': [.2 * w, .8 * h], 'hipVR': [.8 * w, .8 * h], 'top': [w / 2, 0], 'wrist': [w / 2, .08 * h], 'tip': [w / 2, h],
         'ankle': [w / 2, .15 * h], 'heel': [0, h], 'toe': [w, h]}
    return F.get(name, [w / 2, h / 2])


SLOTS = [('hip', 'hip', None), ('torso', 'torso', None), ('head', 'head', None),
         ('upper_arm_L', 'upper_arm', 'L'), ('forearm_L', 'forearm', 'L'), ('hand_L', 'hand', 'L'),
         ('upper_arm_R', 'upper_arm', 'R'), ('forearm_R', 'forearm', 'R'), ('hand_R', 'hand', 'R'),
         ('thigh_L', 'thigh', 'L'), ('shin_L', 'shin', 'L'), ('shoe_L', 'shoe', 'L'),
         ('thigh_R', 'thigh', 'R'), ('shin_R', 'shin', 'R'), ('shoe_R', 'shoe', 'R')]
VIEWKEYS = ['front', 'threequarter', 'profile', 'threequarter_back', 'back']


def score(p, side, view):     # the Rig Builder's candidate ranking (index.html score())
    s = 0
    if side: s += 4 if p.get('side') == side else (-3 if p.get('side') else 1)
    if p.get('view'): s += 3 if p['view'] == view else -2
    s += {'A': 3, 'B': 1, 'C': -6}.get(p.get('q'), 0)
    if (p.get('nb') or 0) >= 2: s += 1
    names = {'torso': ['neck', 'waist', 'shVL', 'shVR'], 'hip': ['waist', 'hipVL', 'hipVR'], 'head': ['neck', 'top'],
             'hand': ['wrist', 'tip'], 'shoe': ['ankle', 'heel', 'toe']}.get(p['cls'], ['pivot', 'socket'])
    s += sum(.5 for n in names if (p.get('src') or {}).get(n) == 'brad')
    if p.get('ppc_src') == 'sheet': s += 1
    if p.get('not_costume'): s -= 10
    if p.get('state') and ('uncut' in p['state'] or 'pair' in p['state']): s -= 4
    if p['cls'] == 'hand' and p.get('shape') and p['shape'] != 'relaxed': s -= 1
    return s


def _cards_exact(doc, view):
    d = dict((doc.get('defaults') or {}).get(view) or {})
    out = {}
    for n, cls, side in SLOTS:
        pid = d.get(n)
        if not pid or pid not in doc['P']:
            L = [p for p in doc['parts'] if p['cls'] == cls]
            L.sort(key=lambda p: -score(p, side, view))
            pid = L[0]['id'] if L else None
        out[n] = pid
    return out


def cards_for(doc, view):
    c = _cards_for(doc, view)
    r = (doc.get('rest') or {}).get(view) or {}
    for slot, pid in (r.get('cards') or {}).items():
        if pid in doc['P']: c[slot] = pid
    return c


def _cards_for(doc, view):
    """slot -> part id for a view key: the character's defaults, else the best-scored part (as the Builder).
       Three-quarter views take torso / head from a card drawn for that view when the kit has one (grade A/B)
       and every limb from the nearest full view (front for 3/4, back for 3/4-back): the kits rarely draw
       3/4 limbs, and the cards the ranker would pick there are mostly mislabelled."""
    if view in ('front', 'profile', 'back'):
        return _cards_exact(doc, view)
    base = _cards_exact(doc, 'front' if view == 'threequarter' else 'back')
    for n, cls, side in SLOTS:
        if cls in ('torso', 'head'):
            L = [p for p in doc['parts'] if p['cls'] == cls and p.get('view') == view and p.get('q') in ('A', 'B')]
            if L:
                L.sort(key=lambda p: -score(p, side, view)); base[n] = L[0]['id']
    return base


NORM = {'upper_arm': .186, 'forearm': .145, 'hand': .108, 'thigh': .245, 'shin': .246}


def skeleton(doc, rig=None, autofix=True):
    """Segment lengths (cm) at true scale from the front cards (or a Builder rig {slot: {pid, s}})."""
    H = doc['stature_cm']
    front = cards_for(doc, 'front')
    if rig: front.update({k: v['pid'] for k, v in rig.items() if v.get('pid')})
    P = doc['P']

    fixes = S_fix = []

    def card(n):
        pid = front.get(n)
        if not pid: return None, 0
        p = P[pid]
        s = (rig or {}).get(n, {}).get('s') or p.get('user_scale') or 1
        return p, s / (p.get('ppc') or doc['ppcMedian'])

    def fixlen(slot, L_):
        """the Builder critic's automatic scale fix: a segment outside 0.85..1.18 of its norm is rescaled to it"""
        nr = NORM.get(slot.rsplit('_', 1)[0])
        if not autofix or not nr or rig: return L_
        r = L_ / (nr * H)
        if r < .85 or r > 1.18:
            S_fix.append(f'{slot} {r:.2f}x norm -> rescaled'); return nr * H
        return L_

    def L(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])
    S = {'H': H, 'cards': front}
    p, k = card('hip')
    if p:
        a, b = pt(p, 'hipVL'), pt(p, 'hipVR'); mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
        S['hipHalf'] = L(a, b) / 2 * k; S['waistUp'] = max(4.0, (mid[1] - pt(p, 'waist')[1]) * k)
    else:
        S['hipHalf'], S['waistUp'] = .05 * H, .06 * H
    p, k = card('torso')
    if p:
        n, w = pt(p, 'neck'), pt(p, 'waist'); S['torso'] = L(n, w) * k
        sl, sr = pt(p, 'shVR'), pt(p, 'shVL')         # front view: actor L is viewer right
        S['shL'] = [(sl[0] - n[0]) * k, (sl[1] - n[1]) * k]
        S['shR'] = [(sr[0] - n[0]) * k, (sr[1] - n[1]) * k]
    else:
        S['torso'] = .3 * H; S['shL'] = [.11 * H, .03 * H]; S['shR'] = [-.11 * H, .03 * H]
    p, k = card('head')
    S['head'] = L(pt(p, 'neck'), pt(p, 'top')) * k if p else .14 * H
    norm = {'upper_arm': .186, 'forearm': .145, 'hand': .108, 'thigh': .245, 'shin': .246}
    for side in 'LR':
        for slot, key, a, b in (('upper_arm', 'uarm', 'pivot', 'socket'), ('forearm', 'farm', 'pivot', 'socket'),
                                ('hand', 'hand', 'wrist', 'tip'), ('thigh', 'thigh', 'pivot', 'socket'), ('shin', 'shin', 'pivot', 'socket')):
            p, k = card(slot + '_' + side)
            S[key + side] = fixlen(slot + '_' + side, L(pt(p, a), pt(p, b)) * k) if p else norm[slot] * H
    # foot: from the profile foot card (ankle -> heel / toe), else proportions
    pf = cards_for(doc, 'profile').get('shoe_L')
    p = P.get(pf) if pf else None
    if p and p.get('pts', {}).get('heel') and p.get('view') == 'profile':
        k = (p.get('user_scale') or 1) / (p.get('ppc') or doc['ppcMedian'])
        an, he, to = pt(p, 'ankle'), pt(p, 'heel'), pt(p, 'toe')
        f = p.get('faces') or 1
        S['heel'] = [0, (he[1] - an[1]) * k, (he[0] - an[0]) * k * f]
        S['toe'] = [0, (to[1] - an[1]) * k, (to[0] - an[0]) * k * f]
        if S['heel'][2] > S['toe'][2]: S['heel'][2], S['toe'][2] = S['toe'][2], S['heel'][2]
        if not (.08 * H < S['toe'][2] - S['heel'][2] < .25 * H) or not (.02 * H < S['heel'][1] < .09 * H):
            p = None
    if 'heel' not in S or not p:
        S['heel'] = [0, .04 * H, -.03 * H]; S['toe'] = [0, .04 * H, .12 * H]
    S['fixes'] = fixes
    J = fk(S, np.zeros((1, NP)))
    S['standing_cm'] = float(max(J['heelL'][0][1], J['toeL'][0][1]) - J['top'][0][1])
    return S


# ------------------------------------------------------------------------------------------- FK (batched)
def _rx(a):
    c, s = np.cos(a), np.sin(a); o, z = np.ones_like(a), np.zeros_like(a)
    return np.stack([np.stack([o, z, z], -1), np.stack([z, c, -s], -1), np.stack([z, s, c], -1)], -2)


def _ry(a):
    c, s = np.cos(a), np.sin(a); o, z = np.ones_like(a), np.zeros_like(a)
    return np.stack([np.stack([c, z, s], -1), np.stack([z, o, z], -1), np.stack([-s, z, c], -1)], -2)


def _rz(a):
    c, s = np.cos(a), np.sin(a); o, z = np.ones_like(a), np.zeros_like(a)
    return np.stack([np.stack([c, -s, z], -1), np.stack([s, c, z], -1), np.stack([z, z, o], -1)], -2)


def _mv(R, v):
    return np.einsum('bij,bj->bi', R, v)


def fk(S, X):
    """X (B, NP) degrees -> dict of (B, 3) body-frame points (root = pelvis at the origin) and frames."""
    X = np.atleast_2d(X); B = X.shape[0]
    r = np.radians(X)
    g = lambda n: r[:, PI[n]]
    vec = lambda v: np.tile(np.asarray(v, float), (B, 1))
    mm = lambda A, C: np.einsum('bij,bjk->bik', A, C)
    R0 = mm(mm(_ry(g('twist')), _rx(-g('pitch'))), _rz(g('roll')))
    # proportions are relative: k is centred (mean 0), so the figure's overall size is the scale's job
    kmean = X[:, [PI[k] for k in KN]].mean(1)
    ek = lambda n: np.exp(X[:, PI[n]] - kmean)[:, None]
    J = {'pelvis': np.zeros((B, 3))}
    J['hipL'] = _mv(R0, vec([S['hipHalf'], 0, 0])); J['hipR'] = _mv(R0, vec([-S['hipHalf'], 0, 0]))
    J['waist'] = _mv(R0, vec([0, -S['waistUp'], 0]) * ek('kT'))
    Rt = mm(mm(R0, _rx(-g('tf'))), _rz(g('tb')))
    J['neck'] = J['waist'] + _mv(Rt, vec([0, -S['torso'], 0]) * ek('kT'))
    J['chest'] = J['waist'] + _mv(Rt, vec([0, -.6 * S['torso'], 0]) * ek('kT'))
    Rh = mm(mm(Rt, _rx(-g('hf'))), _rz(g('hb')))
    J['top'] = J['neck'] + _mv(Rh, vec([0, -S['head'], 0]) * ek('kHd'))
    J['headC'] = J['neck'] + _mv(Rh, vec([0, -.55 * S['head'], 0]) * ek('kHd'))
    J['chin'] = J['neck'] + _mv(Rh, vec([0, -.33 * S['head'], 0]) * ek('kHd'))
    F = {'R0': R0, 'Rt': Rt, 'Rh': Rh}
    for sd, sg in (('L', 1), ('R', -1)):
        sh = S['sh' + sd]
        J['sh' + sd] = J['neck'] + _mv(Rt, vec([sh[0], sh[1], 0]))
        Ru = mm(mm(mm(Rt, _rx(g('sh%sf' % sd))), _rz(-sg * g('sh%sb' % sd))), _ry(sg * g('sh%st' % sd)))
        J['el' + sd] = J['sh' + sd] + _mv(Ru, vec([0, S['uarm' + sd], 0]) * ek('kU'))
        Rf = mm(Ru, _rx(g('el' + sd)))
        J['wr' + sd] = J['el' + sd] + _mv(Rf, vec([0, S['farm' + sd], 0]) * ek('kF'))
        Rw = mm(Rf, _rx(g('wr' + sd)))
        J['tip' + sd] = J['wr' + sd] + _mv(Rw, vec([0, S['hand' + sd], 0]))
        Rth = mm(mm(mm(R0, _rx(g('hp%sf' % sd))), _rz(-sg * g('hp%sb' % sd))), _ry(sg * g('hp%st' % sd)))
        J['kn' + sd] = J['hip' + sd] + _mv(Rth, vec([0, S['thigh' + sd], 0]) * ek('kTh'))
        Rs = mm(Rth, _rx(-g('kn' + sd)))
        J['an' + sd] = J['kn' + sd] + _mv(Rs, vec([0, S['shin' + sd], 0]) * ek('kSh'))
        Rft = mm(Rs, _rx(g('an' + sd)))
        J['heel' + sd] = J['an' + sd] + _mv(Rft, vec(S['heel']))
        J['toe' + sd] = J['an' + sd] + _mv(Rft, vec(S['toe']))
        J['ball' + sd] = J['an' + sd] + _mv(Rft, vec([0, S['toe'][1], .72 * S['toe'][2]]))
        J['ankUp' + sd] = J['an' + sd] + _mv(Rft, vec([0, -10, 0]))
        J['mUa' + sd] = (J['sh' + sd] + J['el' + sd]) / 2; J['mFa' + sd] = (J['el' + sd] + J['wr' + sd]) / 2
        J['mTh' + sd] = (J['hip' + sd] + J['kn' + sd]) / 2; J['mSh' + sd] = (J['kn' + sd] + J['an' + sd]) / 2
        F['Ru' + sd], F['Rf' + sd], F['Rw' + sd], F['Rth' + sd], F['Rs' + sd], F['Rft' + sd] = Ru, Rf, Rw, Rth, Rs, Rft
    J['_F'] = F
    return J


def project(P3, psi, ox=0.0, oy=0.0):
    """(..., 3) body-frame points -> (..., 2) screen cm and (...) depth (toward the camera)."""
    c, s = math.cos(math.radians(psi)), math.sin(math.radians(psi))
    X, Y, Z = P3[..., 0], P3[..., 1], P3[..., 2]
    depth = -X * s + Z * c
    sx = X * c + Z * s + 0.12 * depth * abs(s)
    return np.stack([sx + ox, Y + oy], -1), depth


def view_key(psi):
    a = abs(((psi + 180) % 360) - 180)
    return VIEWKEYS[min(4, int((a + 22.5) // 45))]


# ------------------------------------------------------------------------------------------- targets
def brass(img_rgba):
    """Painted brass brads: [(x, y, r, src)] in card px."""
    a = img_rgba[:, :, 3] > 100
    hsv = cv2.cvtColor(np.ascontiguousarray(img_rgba[:, :, :3]), cv2.COLOR_RGB2HSV).astype(int)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    inner = cv2.erode(a.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    g = ((h >= 15) & (h <= 27) & (s >= 110) & (v >= 140) & inner).astype(np.uint8)
    g = cv2.morphologyEx(g, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    H = a.shape[0]
    n, lab, st, cen = cv2.connectedComponentsWithStats(g, 8)
    cand = []
    for i in range(1, n):
        x, y, w, hh, ar = st[i]
        d = max(w, hh)
        if ar < 6 or d < 4 or d > 0.08 * max(H, 200): continue
        if d / max(1, min(w, hh)) > 1.8: continue
        if np.percentile(v[lab == i], 90) < 205: continue
        cand.append([float(cen[i][0]), float(cen[i][1]), d / 2, int(ar)])
    # a hollow eyelet often splits into a highlight and a ring: merge components closer than their radii
    cand.sort(key=lambda c: -c[3]); out = []
    for c in cand:
        for o in out:
            if math.hypot(c[0] - o[0], c[1] - o[1]) < max(c[2], o[2]) * 1.2:
                w0, w1 = o[3], c[3]
                o[0] = (o[0] * w0 + c[0] * w1) / (w0 + w1); o[1] = (o[1] * w0 + c[1] * w1) / (w0 + w1)
                o[2] = max(o[2], c[2]); o[3] += c[3]; break
        else:
            out.append(list(c))
    # Hough refinement of each centre on a local crop
    gray = cv2.cvtColor(np.ascontiguousarray(img_rgba[:, :, :3]), cv2.COLOR_RGB2GRAY)
    res = []
    for x, y, r, ar in out:
        R = int(max(6, r * 2.2)); x0, y0 = int(max(0, x - R)), int(max(0, y - R))
        crop = gray[y0:int(y + R) + 1, x0:int(x + R) + 1]
        src = 'brass'
        if crop.shape[0] > 8 and crop.shape[1] > 8:
            c = cv2.HoughCircles(cv2.GaussianBlur(crop, (3, 3), 0), cv2.HOUGH_GRADIENT, dp=1, minDist=R,
                                 param1=80, param2=10, minRadius=max(2, int(r * .6)), maxRadius=int(r * 1.5) + 1)
            if c is not None:
                cx, cy, cr = c[0][0]
                if math.hypot(cx + x0 - x, cy + y0 - y) < r * .6:
                    x, y, r, src = float(cx + x0), float(cy + y0), float(cr), 'brass+hough'
        res.append([round(x, 1), round(y, 1), round(r, 1), src])
    return res


def target_list():
    """All pose targets mapped to a buildable character key."""
    c = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'catalog.json')))['sheets']
    body = json.load(open(os.path.join(SHOTS, 'bodylab', 'body.json')))
    reg = json.load(open(os.path.join(SHOTS, 'kits', 'cut', 'registry.json')))['parts']
    bp = {p['id']: p for p in body['parts']}
    keys = {x['key'] for x in json.load(open(os.path.join(HERE, 'data', 'index.json')))['characters']}
    ALIAS = {'young_ghost/ghost': 'young_poet/child_clothes', 'poet/tracksuit_v1': 'poet/red_black_sunglasses'}
    out, skipped = [], Counter()
    for sid, s in c.items():
        for p in s['parts']:
            q = bp.get(p['id']); r = reg.get(p['id'], {})
            if not q: continue
            if p['kind'] == 'pose': kind = 'pose'
            elif 'main-poses' in sid and q['h'] >= 300 and r.get('q') in ('A', 'B') and q['class'] == 'other': kind = 'card'
            else: continue
            key = q['character'] + '/' + q['costume']; key = ALIAS.get(key, key)
            if key not in keys:
                skipped[key] += 1; continue
            out.append({'id': p['id'], 'img': 'kits/cut/' + p['file'], 'label': p.get('label') or p.get('name') or '',
                        'sheet': sid, 'kind': kind, 'key': key, 'w': q['w'], 'h': q['h'], 'catalog_brads': p.get('brads', []),
                        'q': r.get('q')})
    return out, skipped


def prepare(t):
    im = np.asarray(Image.open(os.path.join(SHOTS, t['img'])).convert('RGBA'))
    a = im[:, :, 3] > 100
    lab, n = ndimage.label(a)
    if n > 1:                              # the figure is the largest island (labels, fx fragments drop out)
        sz = ndimage.sum(a, lab, range(1, n + 1)); a = lab == (1 + int(np.argmax(sz)))
    ys, xs = np.nonzero(a)
    t['bbox'] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    t['floor'] = int(ys.max()); t['cx'] = float((xs.min() + xs.max()) / 2)
    B = [b for b in brass(im) if a[int(min(a.shape[0] - 1, b[1])), int(min(a.shape[1] - 1, b[0]))]]
    if len(B) < 4:
        B += [[float(x), float(y), 4.0, 'catalog'] for x, y in t['catalog_brads']
              if all(math.hypot(x - b[0], y - b[1]) > 6 for b in B)][:20]
    if len(B) >= 5:
        rmed = float(np.median([b[2] for b in B]))
        t['dropped'] = [b for b in B if b[2] > 1.7 * rmed]
        B = [b for b in B if b[2] <= 1.7 * rmed]
    t['brads'] = B
    return im, a


# ------------------------------------------------------------------------------------------- solver
class Problem:
    def __init__(self, S, t, mask, psi, s0, s_sig, sandbox=False):
        self.S, self.t, self.psi = S, t, psi
        self.s0, self.s_sig = s0, s_sig
        self.mask = mask
        pad = 200
        m = np.pad(mask, pad)
        self.dt = ndimage.distance_transform_edt(~m).astype(np.float32)
        self.pad = pad
        self.B = np.array([[b[0], b[1]] for b in t['brads']], float) if t['brads'] else np.zeros((0, 2))
        cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cnt = max(cnts, key=len)[:, 0, :].astype(float)
        idx = np.linspace(0, len(cnt) - 1, 48).astype(int)
        self.C = cnt[idx]
        self.sandbox = sandbox
        self.set_stretch(True)
        self.match = None
        self.flat = 3.0
        self.Mk = [(n, m[:2], float(m[2]) * MW.get(n, 1.0)) for n, m in (t.get('markers') or {}).items() if m and m[2] > 0 and n in MARKER_J]

    # world cm <-> target px
    def to_px(self, xy, ls):
        s = self.s0 * np.exp(ls)
        return np.stack([xy[..., 0] * s[..., None] + self.t['cx'], xy[..., 1] * s[..., None] + self.t['floor']], -1)

    def residuals(self, Z, stage):
        Z = np.atleast_2d(Z); X = Z[:, :NP]; ls = Z[:, NP]
        J = fk(self.S, X)
        names = JOINTS + [n for n in INSIDE if n not in JOINTS] + [n for n in ('chin', 'top', 'toeL', 'toeR') if n not in JOINTS and n not in INSIDE]
        nm_ = {n: i for i, n in enumerate(names)}
        P3 = np.stack([J[n] for n in names], 1)
        xy, _ = project(P3, self.psi, X[:, PI['ox']][:, None], X[:, PI['oy']][:, None])
        px = self.to_px(xy, ls)                                    # (B, n, 2)
        s = self.s0 * np.exp(ls)
        out = []
        nj = len(JOINTS)
        jp = px[:, :nj]
        if stage == 'M':
            for n, xy, w in self.Mk:
                q = px[:, nm_[MARKER_J[n]]] if MARKER_J[n] in nm_ else None
                out.append(w * (q - np.asarray(xy)) / s[:, None])
        elif len(self.B):
            if stage == 'A':
                d = np.linalg.norm(self.B[None, :, None, :] - jp[:, None, :, :], axis=-1) / s[:, None, None]  # (B, nb, nj)
                out.append(d.min(-1))                          # every brad pulls its nearest joint
                out.append(.5 * np.minimum(d.min(1), 12.0))    # every joint wants a brad (capped: some have none)
            else:
                for (bi, ji) in self.match:
                    dd = (jp[:, ji] - self.B[bi]) / s[:, None]
                    out.append(1.5 * dd)
        # rig points inside the target silhouette
        q = np.clip(px + self.pad, 0, np.array(self.dt.shape[::-1]) - 1)
        dtv = ndimage.map_coordinates(self.dt, [q[..., 1].ravel(), q[..., 0].ravel()], order=1).reshape(q.shape[:2])
        wi, wc = (.3, .1) if stage == 'M' else (.7, .45)     # with labelled markers the silhouette only assists
        out.append(wi * dtv / s[:, None])
        # target silhouette covered by the rig's limbs (capsules)
        segd = []
        nm = {n: i for i, n in enumerate(names)}
        for a, b, rad in SEGS:
            A_ = px[:, nm[a]] if a in nm else self.to_px(project(J[a], self.psi, X[:, 0], X[:, 1])[0][:, None], ls)[:, 0]
            B_ = px[:, nm[b]] if b in nm else self.to_px(project(J[b], self.psi, X[:, 0], X[:, 1])[0][:, None], ls)[:, 0]
            ab = (B_ - A_)[:, None]; ap = self.C[None] - A_[:, None]
            tt = np.clip((ap * ab).sum(-1) / np.maximum((ab * ab).sum(-1), 1e-6), 0, 1)
            dd = np.linalg.norm(ap - tt[..., None] * ab, axis=-1) / s[:, None] - rad
            segd.append(dd)
        cov = np.maximum(0, np.min(np.stack(segd, 0), 0))
        out.append(wc * cov)
        # cut-out figures are flat: a drawn limb shows its full length, so foreshortening costs
        for a, b in FLAT:
            pa, pb = project(J[a], self.psi)[0], project(J[b], self.psi)[0]
            L3 = np.linalg.norm(J[b] - J[a], axis=-1)
            out.append((self.flat * (np.linalg.norm(pb - pa, axis=-1) / np.maximum(L3, 1e-6) - 1))[:, None])
        # priors: neutral angles, figure scale
        ang = X[:, ANG] / 90.0
        out.append(.35 * ang)
        out.append(1.2 * X[:, [PI['hf'], PI['hb']]] / 90.0)     # heads stay upright unless the drawing insists
        out.append(X[:, [PI[k] for k in KN]] / .25)
        out.append(.25 * X[:, 3:6] / 90.0)
        out.append(((ls - 0) / self.s_sig)[:, None])
        return np.concatenate([o.reshape(o.shape[0], -1) for o in out], 1)

    def set_stretch(self, on):
        lo, hi = lims(self.sandbox, on)
        # the figure's scale stays within ~2 sigma of the sheet prior (a robust loss would let it run away)
        # the figure's scale stays within ~2 sigma of the sheet prior; with the proportions free (k) their mean is
        # held at 1 (a residual below), so k says only how the drawing's proportions differ, scale how big it is
        w = min(math.log(1.8), 2.2 * self.s_sig)
        self.lo = np.append(lo, -w); self.hi = np.append(hi, w)

    def solve(self, z0, stage, nfev=120):
        f = lambda z: self.residuals(z, stage)[0]
        h = 1e-3

        def jac(z):
            Z = np.repeat(z[None], NP + 2, 0)
            Z[1:] += np.eye(NP + 1) * STEP
            R = self.residuals(Z, stage)
            return ((R[1:] - R[0]) / STEP[:, None]).T
        z0 = np.clip(z0, self.lo + 1e-8, self.hi - 1e-8)
        r = least_squares(f, z0, jac=jac, bounds=(self.lo, self.hi), loss='soft_l1', f_scale=3.0, max_nfev=nfev,
                          x_scale=XSC)
        return r.x, float(r.cost)

    def joints_px(self, z):
        X = z[None, :NP]; J = fk(self.S, X)
        P3 = np.stack([J[n] for n in JOINTS], 1)
        xy, depth = project(P3, self.psi, X[:, 0][:, None], X[:, 1][:, None])
        return self.to_px(xy, z[None, NP])[0]

    def do_match(self, z, gate_cm=9.0):
        if not len(self.B): self.match = []; return
        jp = self.joints_px(z); s = self.s0 * math.exp(z[NP])
        D = np.linalg.norm(self.B[:, None] - jp[None], axis=-1) / s
        Dg = np.where(D < gate_cm, D, 1e3)
        bi, ji = linear_sum_assignment(Dg)
        self.match = [(int(b), int(j)) for b, j in zip(bi, ji) if Dg[b, j] < 1e3]


SEEDS = {
    'stand': {},
    'step': {'hpLf': 25, 'hpRf': -15, 'knR': 15, 'shLf': -15, 'shRf': 15},
    'crouch': {'hpLf': 105, 'hpRf': 105, 'knL': 125, 'knR': 125, 'tf': 35, 'anL': 20, 'anR': 20, 'oy': 40, 'shLf': 40, 'shRf': 40},
    'kneel': {'hpLf': 90, 'knL': 90, 'hpRf': 0, 'knR': 95, 'tf': 15, 'oy': 30},
    'sit': {'hpLf': 90, 'hpRf': 90, 'knL': 90, 'knR': 90, 'oy': 40},
    'arms_up': {'shLf': 165, 'shRf': 165},
    'arms_out': {'shLb': 85, 'shRb': 85, 'elL': 20, 'elR': 20},
    'lie': {'pitch': 85, 'roll': 0, 'oy': 75},
}


def seed_vec(name, psi, S):
    z = np.zeros(NP + 1)
    for k, v in SEEDS[name].items(): z[PI[k]] = v
    z[PI['oy']] = -(S['thighL'] + S['shinL'] + S['heel'][1] + 1) + SEEDS[name].get('oy', 0)
    if name == 'lie':
        if view_key(psi) in ('front', 'back'): z[PI['pitch']], z[PI['roll']] = 0, 85
        z[PI['oy']] = -12
    return z


def swap_lr(z, what):
    z = z.copy()
    pairs = {'legs': [('hpLf', 'hpRf'), ('hpLb', 'hpRb'), ('knL', 'knR'), ('anL', 'anR'), ('hpLt', 'hpRt')],
             'arms': [('shLf', 'shRf'), ('shLb', 'shRb'), ('elL', 'elR'), ('wrL', 'wrR'), ('shLt', 'shRt')]}[what]
    for a, b in pairs: z[PI[a]], z[PI[b]] = z[PI[b]], z[PI[a]]
    return z


# ------------------------------------------------------------------------------------------- cards (render)
_ALPHA = {}


def part_img(p):
    if p['id'] not in _ALPHA:
        _ALPHA[p['id']] = np.asarray(Image.open(os.path.join(SHOTS, p['img'])).convert('RGBA'))
    return _ALPHA[p['id']]


CARD = {   # slot -> (card pivot, card axis point, skeleton A, skeleton B, stretch along the axis)
    'hip': ('waist', 'hips', 'waist', 'pelvis', True), 'torso': ('waist', 'neck', 'waist', 'neck', True),
    'head': ('neck', 'top', 'neck', 'top', False),
    'upper_arm': ('pivot', 'socket', 'sh', 'el', True), 'forearm': ('pivot', 'socket', 'el', 'wr', True),
    'hand': ('wrist', 'tip', 'wr', 'tip', 'shrink'), 'thigh': ('pivot', 'socket', 'hip', 'kn', True),
    'shin': ('pivot', 'socket', 'kn', 'an', True), 'shoe': ('ankle', None, 'an', None, False)}
BIAS = {'hip': -10, 'shoe': -6, 'shin': -5, 'thigh': -4, 'torso': 0, 'head': 2, 'upper_arm': 3, 'forearm': 4, 'hand': 5}


def place_cards(doc, S, J, psi, ox, oy, cards=None):
    """-> [(slot, part, M 2x3 card px -> screen cm, depth, far)] back to front; J is fk() for ONE pose (B=1)."""
    vk = view_key(psi)
    cards = cards or cards_for(doc, vk)
    face = 1 if ((psi + 360) % 360) < 180 else -1
    side_view = vk in ('profile', 'threequarter', 'threequarter_back')
    out = []
    P2 = lambda n: project(J[n][0], psi, ox, oy)[0]
    D = lambda n: float(project(J[n][0], psi)[1])
    tdep = D('chest')
    for slot, cls, side in SLOTS:
        pid = cards.get(slot)
        if not pid: continue
        p = doc['P'][pid]
        cp, ca, sa, sb, stretch = CARD[cls]
        sd = side or ''
        A = (sa + sd) if sa in ('sh', 'el', 'wr', 'hip', 'kn', 'an', 'tip') else sa
        k = (p.get('user_scale') or 1) / (p.get('ppc') or doc['ppcMedian'])
        flip = False
        if side_view: flip = (p.get('faces') or 1) * face < 0 if cls == 'shoe' else face < 0
        elif side and p.get('side') and p['side'] != side: flip = True
        w = p['w']
        fx = (lambda q: [w - q[0], q[1]]) if flip else (lambda q: list(q))
        if cp == 'waist' and cls == 'hip': pv = fx(pt(p, 'waist'))
        else: pv = fx(pt(p, cp))
        if ca == 'hips':
            a_, b_ = pt(p, 'hipVL'), pt(p, 'hipVR'); ax = fx([(a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2])
        elif ca: ax = fx(pt(p, ca))
        else: ax = None
        Aw = P2(A)
        if cls == 'shoe':
            if side_view and (p.get('pts') or {}).get('heel'):
                pa, pb = fx(pt(p, 'heel')), fx(pt(p, 'toe'))
                Bv = P2('toe' + sd) - P2('heel' + sd)
                uc = np.array(pb, float) - np.array(pa, float)
            else:
                Bv = P2('ankUp' + sd) - Aw; uc = np.array([0.0, -1.0])
            Lr, Ld = 1.0, None
        else:
            B = (sb + sd) if sb in ('el', 'wr', 'kn', 'an', 'tip') else sb
            Bv = P2(B) - Aw
            uc = np.array(ax, float) - np.array(pv, float)
        lc = float(np.linalg.norm(uc)) or 1.0; ld = float(np.linalg.norm(Bv))
        uh = uc / lc; dh = Bv / ld if ld > 1e-6 else np.array([0.0, 1.0])
        if cls == 'shoe' or stretch is False: along = k
        else:
            along = ld / lc
            if stretch == 'shrink': along = min(k, max(.5 * k, along))
            else: along = min(1.7 * k, max(.3 * k, along))
        nh_c = np.array([-uh[1], uh[0]]); nh_d = np.array([-dh[1], dh[0]])
        kx = k
        if cls in ('torso', 'hip') and p.get('view') != vk:     # foreshortened across its axis (pose-core.js too)
            yaw = {'front': 0, 'threequarter': 45, 'profile': 90, 'threequarter_back': 135, 'back': 180}.get(p.get('view') or 'front', 0)
            a = abs(((psi % 360) + 360) % 360); a = 360 - a if a > 180 else a
            kx = k * max(.3, abs(math.cos(math.radians(a - yaw))))
        L = along * np.outer(dh, uh) + kx * np.outer(nh_d, nh_c)
        if flip: L = L @ np.array([[-1.0, 0], [0, 1]])
        pv0 = np.array(pt(p, cp) if ca != 'hips' else pt(p, 'waist'), float)
        t = Aw - L @ pv0
        M = np.array([[L[0, 0], L[0, 1], t[0]], [L[1, 0], L[1, 1], t[1]]])
        if cls == 'shoe': dep = D('an' + sd)
        elif sb in ('neck', 'pelvis', 'top'): dep = D(A) * .5 + D(sb if sb != 'top' else 'top') * .5
        else: dep = (D(A) + D((sb + sd) if sb in ('el', 'wr', 'kn', 'an', 'tip') else sb)) / 2
        far = side_view and side is not None and dep < tdep - 4
        key = dep + BIAS[cls]
        rest = (doc.get('rest') or {}).get(vk) or {}
        if rest.get('order') and slot in rest['order']:     # the Rest rig's stack, re-sorted only by big depth changes
            swap = side_view and face != (rest.get('facing') or 1)
            rs = (slot[:-1] + ('R' if side == 'L' else 'L')) if swap and side else slot
            key = rest['order'].index(rs) * 10 + .25 * dep
            if side_view and rest.get('far') and side: far = bool(rest['far'].get(rs))
        out.append((slot, p, M, key, far))
    out.sort(key=lambda o: o[3])
    return out


def render(doc, S, z, psi, size, s_px, cx, floor, color=False, cards=None):
    """Rig cards in target px. Returns alpha (H, W) bool, or an RGBA image when color."""
    X = z[None, :NP]; J = fk(S, X)
    placed = place_cards(doc, S, J, psi, float(z[0]), float(z[1]), cards)
    Wd, Ht = size
    T = np.array([[s_px, 0, cx], [0, s_px, floor], [0, 0, 1]])
    if color: canvas = Image.new('RGBA', (Wd, Ht), (0, 0, 0, 0))
    else: acc = np.zeros((Ht, Wd), np.uint8)
    for slot, p, M, dep, far in placed:
        Mt = (T @ np.vstack([M, [0, 0, 1]]))[:2]
        src = part_img(p)
        if color:
            w = cv2.warpAffine(src, Mt, (Wd, Ht), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
            if far: w = w.copy(); w[..., :3] = (w[..., :3] * .62).astype(np.uint8)
            canvas.alpha_composite(Image.fromarray(w))
        else:
            w = cv2.warpAffine(src[:, :, 3], Mt, (Wd, Ht), flags=cv2.INTER_NEAREST, borderValue=0)
            acc = np.maximum(acc, w)
    return canvas if color else acc > 100


def head_diff(doc, S, z, psi, t, im, s_px):
    """How unlike the drawing the rig's HEAD card looks in this view (mean |RGB| difference over the pixels both
       cover, 0..255): front, back and the facing of a profile are told apart by the face, not by the brads."""
    X = z[None, :NP]; J = fk(S, X)
    placed = [c for c in place_cards(doc, S, J, psi, float(z[0]), float(z[1])) if c[0] == 'head']
    if not placed: return 60.0
    Ht, Wd = im.shape[:2]
    T = np.array([[s_px, 0, t['cx']], [0, s_px, t['floor']], [0, 0, 1]])
    _, p, M, _, _ = placed[0]
    w = cv2.warpAffine(part_img(p), (T @ np.vstack([M, [0, 0, 1]]))[:2], (Wd, Ht), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    reg = w[..., 3] > 100
    if reg.sum() < 50: return 1.0

    def skin(a):
        hsv = cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2HSV).astype(int)
        return (hsv[..., 0] >= 3) & (hsv[..., 0] <= 20) & (hsv[..., 1] >= 60) & (hsv[..., 2] >= 50) & (a[..., 3] > 100)
    # skin (face) share inside the rig head's outline, rig card vs drawing: a back-of-head card shows hair
    return float(abs(skin(w)[reg].mean() - skin(im)[reg].mean()))


def iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 0.0


# ------------------------------------------------------------------------------------------- one target
def sheet_scale_prior(targets, key_stature):
    """key_stature: the rig's own standing height (cm), floor to crown, per character."""
    """px per cm per sheet: the tallest standing figure on the sheet is ~0.98 of the stature."""
    by = defaultdict(list)
    for t in targets:
        hh = t['bbox'][3] - t['bbox'][1]; ww = t['bbox'][2] - t['bbox'][0]
        if hh / max(1, ww) > 1.7 and len(t['brads']) >= 5: by[t['sheet']].append(hh)
    out = {}
    for t in targets:
        H = key_stature[t['key']]
        L = by.get(t['sheet'])
        if L: out[t['id']] = (max(L) / (0.98 * H), 0.12, 'tallest standing figure on the sheet')
        else:
            hh = t['bbox'][3] - t['bbox'][1]
            out[t['id']] = (max(hh, t['bbox'][2] - t['bbox'][0]) / (0.9 * H), 0.35, 'own height (no standing figure on the sheet)')
    return out


PSIS = [0, 90, -90, 45, -45, 180]


def views_for(t):
    """Views to try: all six, unless the drawing's own label names its view."""
    lab = (t.get('label', '') + ' ' + t['id'].split('/')[-1]).lower().replace('-', ' ')
    if 'threequarter back' in lab or 'three quarter back' in lab or 'rear three' in lab: return [135, -135, 180]
    if 'threequarter' in lab or 'three quarter' in lab or '3/4' in lab: return [45, -45]
    if 'profile' in lab or 'side view' in lab: return [90, -90]
    if 'back view' in lab or 'rear view' in lab or 'from behind' in lab: return [180, 135, -135]
    if 'front' in lab: return [0, 45, -45]
    return PSIS


def solve_target(doc, S, t, mask, prior, quick=False, sandbox=False):
    s0, ssig, _ = prior
    hh = t['bbox'][3] - t['bbox'][1]; ww = t['bbox'][2] - t['bbox'][0]
    lying = ww > 1.6 * hh
    seeds = ['lie'] if lying else ['stand', 'step', 'crouch', 'kneel', 'sit', 'arms_up', 'arms_out']
    if quick: seeds = seeds[:3]
    if t.get('markers_use'):
        return solve_markers(doc, S, t, mask, prior, seeds, quick, sandbox)
    cands = []
    probs = {}
    for psi in views_for(t):
        pr = probs[psi] = Problem(S, t, mask, psi, s0, ssig, sandbox)
        for sd in seeds:
            z0 = seed_vec(sd, psi, S)
            z, cost = pr.solve(z0, 'A', nfev=60)
            cands.append((cost, psi, sd, z))
    cands.sort(key=lambda c: c[0])
    finals = []
    for cost, psi, sd, z in cands[:5 if quick else 8]:
        pr = probs[psi]
        for it in range(2):
            pr.do_match(z, 12.0 if it == 0 else 8.0)
            z, c2 = pr.solve(z, 'B', nfev=100)
        finals.append({'psi': psi, 'seed': sd, 'z': z, 'match': list(pr.match), 'costB': c2})
    Ht, Wd = mask.shape
    for f in finals:
        f['iou'] = iou(render(doc, S, f['z'], f['psi'], (Wd, Ht), s0 * math.exp(f['z'][NP]), t['cx'], t['floor']), mask)
    for f in finals: f['head'] = head_diff(doc, S, f['z'], f['psi'], t, t['_im'], s0 * math.exp(f['z'][NP]))
    best = min(finals, key=lambda f: rank(f, S, t) - 8.0 * f['iou'] + 10.0 * f['head'])
    # alternatives: swap legs (near/far), swap arms (which arm is which / elbows), and the next-best views
    pr = probs[best['psi']]
    for what in ('legs', 'arms'):
        z = swap_lr(best['z'], what)
        for it in range(2):
            pr.do_match(z, 8.0); z, c2 = pr.solve(z, 'B', nfev=100)
        finals.append({'psi': best['psi'], 'seed': 'swap ' + what + ' of best', 'z': z, 'match': list(pr.match), 'costB': c2})
    # drawings are stylised (big heads, short torsos): the match is made with the proportions free (k), and
    # the keyframe keeps those joint ANGLES on the rig as built (rigidify, after the IoU refinement)
    for f in finals:
        km = float(np.mean([f['z'][PI[n]] for n in KN])); f['k'] = {n: round(math.exp(float(f['z'][PI[n]]) - km), 3) for n in KN}
    Ht, Wd = mask.shape
    for f in finals:
        s = s0 * math.exp(f['z'][NP])
        f['iou'] = iou(render(doc, S, f['z'], f['psi'], (Wd, Ht), s, t['cx'], t['floor']), mask)
        f['head'] = head_diff(doc, S, f['z'], f['psi'], t, t['_im'], s)
        f['rank'] = rank(f, S, t) - 8.0 * f['iou'] + 10.0 * f['head']
    finals.sort(key=lambda f: f['rank'])
    return finals, probs


def swap_markers(M, what):
    """The marker set with the L/R labels of the legs (or arms) exchanged: MoveNet's side guess, reversed."""
    keys = {'legs': ['hip', 'knee', 'ankle', 'toe'], 'arms': ['shoulder', 'elbow', 'wrist']}[what]
    o = dict(M)
    for k in keys:
        a, b = M.get(k + 'L'), M.get(k + 'R')
        o.pop(k + 'L', None); o.pop(k + 'R', None)
        if b: o[k + 'L'] = b
        if a: o[k + 'R'] = a
    return o


def solve_markers(doc, S, t, mask, prior, seeds, quick=False, sandbox=False):
    """Solve against LABELLED markers (no matching): every view x seed, best six refined, then the same with the
       legs' or arms' L/R labels swapped as alternatives."""
    s0, ssig, _ = prior
    cands = []
    for psi in views_for(t):
        pr = Problem(S, t, mask, psi, s0, ssig, sandbox)
        for sd in seeds:
            z, cost = pr.solve(seed_vec(sd, psi, S), 'M', nfev=50)
            cands.append((cost, psi, sd, z, pr))
    cands.sort(key=lambda c: c[0])
    finals = []
    for cost, psi, sd, z, pr in cands[:4 if quick else 6]:
        z, c2 = pr.solve(z, 'M', nfev=150)
        finals.append({'psi': psi, 'seed': sd, 'z': z, 'match': [], 'costB': c2, 'markers': None})
    Ht, Wd = mask.shape

    def score_f(f):
        tt = t if not f['markers'] else dict(t, markers=f['markers'])
        s = s0 * math.exp(f['z'][NP])
        f['iou'] = iou(render(doc, S, f['z'], f['psi'], (Wd, Ht), s, t['cx'], t['floor']), mask)
        f['head'] = head_diff(doc, S, f['z'], f['psi'], t, t['_im'], s)
        f['rank'] = rank(f, S, tt) - 8.0 * f['iou'] + 10.0 * f['head']
    for f in finals: score_f(f)
    best = min(finals, key=lambda f: f['rank'])
    for what in ('legs', 'arms'):
        M2 = swap_markers(t['markers'], what)
        pr = Problem(S, dict(t, markers=M2), mask, best['psi'], s0, ssig, sandbox)
        z, c2 = pr.solve(swap_lr(best['z'], what), 'M', nfev=150)
        f = {'psi': best['psi'], 'seed': 'L/R ' + what + ' swapped', 'z': z, 'match': [], 'costB': c2, 'markers': M2}
        score_f(f); finals.append(f)
    for f in finals:
        km = float(np.mean([f['z'][PI[n]] for n in KN])); f['k'] = {n: round(math.exp(float(f['z'][PI[n]]) - km), 3) for n in KN}
    finals.sort(key=lambda f: f['rank'])
    return finals, {}


def rigidify(f, S, t, s0):
    """The same joint angles on the rig as built (k = 0), dropped onto the target's floor and centred on the
       matched joints horizontally."""
    z = f['z'].copy(); z[[PI[n] for n in KN]] = 0
    J = fk(S, z[None, :NP])
    low = max(float(J[n][0][1]) for n in ('heelL', 'heelR', 'toeL', 'toeR', 'knL', 'knR', 'pelvis', 'tipL', 'tipR', 'wrL', 'wrR', 'top'))
    z[PI['oy']] = -low
    g = dict(f); g['z'] = z
    if t.get('markers_use'):
        M = f.get('markers') or t['markers']; s = s0 * math.exp(z[NP])
        J = fk(S, z[None, :NP]); dx = []
        for n, m in M.items():
            if m and m[2] > 0 and n in MARKER_J:
                xy, _ = project(J[MARKER_J[n]][0], f['psi'], z[0], z[1]); dx.append((m[0] - (xy[0] * s + t['cx'])) / s)
        if dx: z[PI['ox']] += float(np.median(dx))
        return z
    e, jp, s = errors(g, S, t, s0)
    if f['match']:
        dx = np.mean([t['brads'][bi][0] - jp[ji][0] for bi, ji in f['match']]) / s
        z[PI['ox']] += dx
    return z


def marker_errors(z, psi, S, t, s0):
    s = s0 * math.exp(z[NP]); J = fk(S, z[None, :NP]); e = {}
    for n, m in (t.get('markers') or {}).items():
        if not m or m[2] <= 0 or n not in MARKER_J: continue
        xy, _ = project(J[MARKER_J[n]][0], psi, z[0], z[1])
        q = np.array([xy[0] * s + t['cx'], xy[1] * s + t['floor']])
        e[n] = float(np.linalg.norm(q - np.array(m[:2])) / s)
    return e


def errors(f, S, t, s0):
    if t.get('markers_use'):
        z = f['z']; s = s0 * math.exp(z[NP])
        return marker_errors(z, f['psi'], S, t, s0), None, s
    z = f['z']; s = s0 * math.exp(z[NP])
    pr = Problem.__new__(Problem); pr.S, pr.t, pr.psi, pr.s0 = S, t, f['psi'], s0
    jp = pr.joints_px(z)
    e = {}
    for bi, ji in f['match']:
        e[JOINTS[ji]] = float(np.linalg.norm(jp[ji] - np.array(t['brads'][bi][:2])) / s)
    return e, jp, s


def rank(f, S, t):
    s0 = t['_s0']
    e, _, _ = errors(f, S, t, s0)
    if t.get('markers_use'):
        w = {n: m[2] for n, m in t['markers'].items()}
        return sum(w[k] * v for k, v in e.items()) / max(1e-6, sum(w[k] for k in e))
    nb = len(t['brads'])
    mean = np.mean(list(e.values())) if e else 15.0
    miss = max(0, min(nb, 12) - len(e))
    return mean + 1.2 * miss + 2.0 * f.get('costB', 0) / max(1, nb) * .1


def refine_iou(doc, S, t, mask, f, s0, steps=(4.0, 2.0)):
    """Coordinate search on the main angles, position and scale to raise silhouette IoU (brad error kept)."""
    Ht, Wd = mask.shape
    keys = ['ox', 'oy', 'tf', 'tb', 'shLf', 'shLb', 'elL', 'shRf', 'shRb', 'elR', 'hpLf', 'knL', 'hpRf', 'knR', 'hf', 'pitch', 'roll']
    lo, hi = lims()
    z = f['z'].copy()   # k (proportion stretch) stays 0: refine the rig as built

    def obj(z):
        s = s0 * math.exp(z[NP])
        a = render(doc, S, z, f['psi'], (Wd, Ht), s, t['cx'], t['floor'])
        ff = dict(f); ff['z'] = z
        e, _, _ = errors(ff, S, t, s0)
        m = np.mean(list(e.values())) if e else 0
        return -iou(a, mask) + 0.02 * m, iou(a, mask)
    best, bi = obj(z)
    for st in steps:
        for k in keys + ['scale']:
            for d in (+1, -1):
                z2 = z.copy()
                if k == 'scale': z2[NP] = np.clip(z2[NP] + d * st * .01, math.log(.55), math.log(1.8))
                else:
                    i = PI[k]; z2[i] = np.clip(z2[i] + d * st * (0.5 if k in ('ox', 'oy') else 1), lo[i], hi[i])
                o, ii = obj(z2)
                if o < best - 1e-4: best, bi, z = o, ii, z2
    f['z'] = z; f['iou'] = bi
    return f


def describe(f, S, t, s0):
    e, jp, s = errors(f, S, t, s0)
    z = f['z']
    J = fk(S, z[None, :NP])
    proj = lambda n: project(J[n][0], f['psi'])
    lab = {}
    # elbows: out = the elbow sits away from the body midline (X) relative to the shoulder-wrist chord
    for sd, sg in (('L', 1), ('R', -1)):
        a, b, el = J['sh' + sd][0], J['wr' + sd][0], J['el' + sd][0]
        lab['elbow' + sd] = 'out' if (el[0] - (a[0] + b[0]) / 2) * sg > 0 else 'in'
    dl, dr = float(proj('knL')[1]), float(proj('knR')[1])
    lab['near_leg'] = 'L' if dl > dr else 'R'
    lab['view'] = view_key(f['psi']) + ('' if view_key(f['psi']) in ('front', 'back') else (' facing right' if f['psi'] > 0 else ' facing left'))
    return e, lab


# ------------------------------------------------------------------------------------------- batch
def run(keys=None, only=None, quick=False):
    t0 = time.time()
    targets, skipped = target_list()
    if keys: targets = [t for t in targets if t['key'] in keys]
    if only: targets = [t for t in targets if only in t['id']]
    idx = {c['key']: c for c in json.load(open(os.path.join(HERE, 'data', 'index.json')))['characters']}
    docs = {k: load_rig(k) for k in {t['key'] for t in targets}}
    for d in docs.values(): d['_S'] = skeleton(d)
    stature = {k: d['_S']['standing_cm'] for k, d in docs.items()}
    masks = {}
    for t in targets:
        im, m = prepare(t); masks[t['id']] = m; t['_im'] = im
    priors = sheet_scale_prior(targets, stature)
    attach_markers(targets)
    os.makedirs(OUT, exist_ok=True)
    results = defaultdict(list)
    G.update(targets=targets, docs=docs, masks=masks, priors=priors, quick=quick, t0=t0)
    import multiprocessing as mp
    n = len(targets)
    if n > 1 and (os.cpu_count() or 1) > 1:
        with mp.get_context('fork').Pool(min(4, os.cpu_count())) as pool:
            recs = pool.map(solve_one, range(n), chunksize=1)
    else:
        recs = [solve_one(i) for i in range(n)]
    for t, rec in zip(targets, recs): results[t['key']].append(rec)
    for key, recs in results.items():
        doc = docs[key]; S = doc['_S']
        out = {'about': 'Pose Lab batch solves (shots/rig/solve.py): each drawn pose figure, its brass brads, and the rig '
                        'snapped onto it (params in degrees, see PN; psi = view yaw). score = IoU x brad-fit, 0..1.',
               'built': time.strftime('%Y-%m-%d %H:%M'), 'character': key, 'stature_cm': doc['stature_cm'],
               'skeleton': {k: v for k, v in S.items() if k not in ('cards',)}, 'cards_front': S['cards'], 'PN': PN, 'LIM': LIM,
               'joints': JOINTS, 'targets': recs, 'walk': walk_keys(S)}
        fn = os.path.join(OUT, key.replace('/', '__') + '.json')
        if only and os.path.exists(fn):        # merge into an existing file
            old = json.load(open(fn)); have = {r['id'] for r in recs}
            out['targets'] = [r for r in old['targets'] if r['id'] not in have] + recs
        json.dump(out, open(fn, 'w'), separators=(',', ':'))
        contact(doc, S, out['targets'], os.path.join(OUT, key.replace('/', '__') + '.contact.webp'))
    write_index()
    report(results, skipped)
    print(f'{time.time() - t0:.0f}s')


G = {}


def attach_markers(targets, lab_dir=None):
    """Labelled markers per target: MoveNet + brads (poses/markers.json, markers.mjs) overridden by people's
       answers in shots/rig/labels/*.json (t 'marker': part = target id, point = marker name, xy | v 'none')."""
    fn = os.path.join(OUT, 'markers.json')
    mk = json.load(open(fn))['targets'] if os.path.exists(fn) else {}
    user = defaultdict(dict)
    for f in sorted(glob.glob(os.path.join(lab_dir or os.path.join(HERE, 'labels'), '*.json'))):
        try: L = json.load(open(f)).get('answers', [])
        except Exception: continue
        for a in L:
            if a.get('t') == 'marker' and a.get('part') and a.get('point'):
                user[a['part']][a['point']] = None if a.get('v') == 'none' else [a['xy'][0], a['xy'][1], 2.0, 'user', 1.0]
    for t in targets:
        M = dict((mk.get(t['id']) or {}).get('markers') or {})
        t['movenet_conf'] = (mk.get(t['id']) or {}).get('mean_conf')
        for n, v in user.get(t['id'], {}).items():
            if v is None: M.pop(n, None)
            else: M[n] = v
        t['markers'] = M
        t['markers_use'] = sum(1 for m in M.values() if m and m[2] > .35) >= 6


def solve_one(i):
    t = G['targets'][i]; doc = G['docs'][t['key']]; S = doc['_S']; quick = G['quick']
    s0, ssig, why = G['priors'][t['id']]; t['_s0'] = s0
    t['scale_prior'] = {'px_per_cm': round(s0, 4), 'sigma_log': ssig, 'why': why}
    m = G['masks'][t['id']]
    rec = {k: t[k] for k in ('id', 'img', 'label', 'sheet', 'kind', 'w', 'h', 'bbox', 'floor', 'cx', 'brads', 'scale_prior', 'q')}
    rec['markers'] = t.get('markers'); rec['markers_use'] = bool(t.get('markers_use')); rec['movenet_conf'] = t.get('movenet_conf')
    if len(t['brads']) < 3 and not t.get('markers_use'):
        rec['solves'] = []; rec['score'] = None; rec['fail'] = f'only {len(t["brads"])} brads found on the figure'
        print(f'[{i + 1}/{len(G["targets"])}] {t["id"]}: SKIP {rec["fail"]}', flush=True); return rec
    finals, probs = solve_target(doc, S, t, m, G['priors'][t['id']], quick)
    keep, seen = [], set()
    for f in finals:
        e, lab = describe(f, S, t, s0)
        sig = (lab['view'], lab['elbowL'], lab['elbowR'], lab['near_leg'])
        if sig in seen: continue
        seen.add(sig); f['lab'] = lab; keep.append(f)
        if len(keep) >= 4: break
    nref = 1 if quick else 4
    for f in keep[:nref]:
        refine_iou(doc, S, t, m, f, s0, steps=(3.0,) if quick else (4.0, 2.0))
    for f in keep[nref:]:
        s = s0 * math.exp(f['z'][NP]); f['iou'] = iou(render(doc, S, f['z'], f['psi'], (m.shape[1], m.shape[0]), s, t['cx'], t['floor']), m)
    sol = []
    Ht, Wd = m.shape
    names = [n for n, _ in MARKERS] if t.get('markers_use') else JOINTS
    for f in keep:
        tt = dict(t, markers=f['markers']) if f.get('markers') else t
        e_pose, lab = describe(f, S, tt, s0)
        pose_mean = float(np.mean(list(e_pose.values()))) if e_pose else None
        zr = rigidify(f, S, tt, s0)
        g = dict(f); g['z'] = zr
        e, _, _ = errors(g, S, tt, s0)
        mean = float(np.mean(list(e.values()))) if e else None
        iou_rig = iou(render(doc, S, zr, f['psi'], (Wd, Ht), s0 * math.exp(zr[NP]), t['cx'], t['floor']), m)
        s_ = {'psi': f['psi'], 'view': lab['view'], 'seed': f['seed'], 'labels': lab,
              'params': {k: round(float(v), 2) for k, v in zip(PN, zr[:NP])},
              'scale_px_per_cm': round(s0 * math.exp(float(zr[NP])), 4),
              'iou': round(iou_rig, 3), 'err_cm': {k: round(v, 2) for k, v in e.items()},
              'mean_err_cm': round(mean, 2) if mean is not None else None,
              'flagged': sorted(k for k, v in e.items() if v > 4.0),
              'unmatched_joints': [j for j in names if j not in e],
              'match': [[JOINTS[ji], bi] for bi, ji in f['match']],
              'against': 'markers' if t.get('markers_use') else 'brads',
              **({'markers': f['markers']} if f.get('markers') else {}),
              # the same pose with the drawing's own proportions (how well the POSE was read)
              'pose': {'iou': round(f['iou'], 3), 'mean_err_cm': round(pose_mean, 2) if pose_mean is not None else None,
                       'params': {k: round(float(v), 3) for k, v in zip(PN, f['z'][:NP])},
                       'err_cm': {k: round(v, 2) for k, v in e_pose.items()},
                       'proportions': {n[1:]: f['k'][n] for n in KN}}}
        s_['score'] = round(score_of(s_), 3)
        s_['pose']['score'] = round(score_of({'iou': f['iou'], 'mean_err_cm': pose_mean, 'unmatched_joints': s_['unmatched_joints'], 'against': s_['against']}), 3)
        sol.append(s_)
    sol.sort(key=lambda s_: -s_['pose']['score'])
    rec['solves'] = sol; rec['score'] = sol[0]['score'] if sol else None
    rec['pose_score'] = sol[0]['pose']['score'] if sol else None
    rec['why'] = why_bad(sol[0], t) if sol else 'no solve'
    b = sol[0]
    print(f'[{i + 1}/{len(G["targets"])}] {t["id"]}: score {b["score"]:.2f} (pose {b["pose"]["score"]:.2f}) IoU {b["iou"]:.2f} err {b["mean_err_cm"]} cm '
          f'{b["view"]} flagged {b["flagged"]} ({time.time() - G["t0"]:.0f}s)', flush=True)
    return rec


def score_of(s):
    e = s['mean_err_cm'] if s['mean_err_cm'] is not None else 12.0
    fit = 1.0 / (1.0 + (e / 4.0) ** 2)
    cover = 1 - len(s['unmatched_joints']) / (len(MARKERS) if s.get('against') == 'markers' else len(JOINTS))
    return s['iou'] * (.55 + .45 * fit) * (.7 + .3 * cover)


def why_bad(s, t):
    w = []
    if s.get('against') != 'markers' and len(t['brads']) < 8: w.append(f'only {len(t["brads"])} brass brads found')
    if s.get('against') == 'markers' and (t.get('movenet_conf') or 1) < .35: w.append(f'MoveNet unsure (confidence {t["movenet_conf"]:.2f})')
    if s['iou'] < .5: w.append(f'silhouette IoU {s["iou"]:.2f}')
    if s['mean_err_cm'] is not None and s['mean_err_cm'] > 4: w.append(f'mean {"marker" if s.get("against") == "markers" else "brad"} error {s["mean_err_cm"]:.1f} cm (rig as built)')
    if s.get('pose') and s['pose'].get('mean_err_cm') is not None and s['pose']['mean_err_cm'] > 4: w.append(f'pose read {s["pose"]["mean_err_cm"]:.1f} cm off the markers')
    if s['flagged']: w.append(f'{len(s["flagged"])} joints > 4 cm' + (': ' + ', '.join(s['flagged']) if len(s['flagged']) <= 5 else ''))
    if len(s['unmatched_joints']) > 6: w.append(f'{len(s["unmatched_joints"])} joints without a {"marker" if s.get("against") == "markers" else "target brad"}')
    pr_ = (s.get('pose') or {}).get('proportions') or {}
    off = [f'{k} x{v:.2f}' for k, v in pr_.items() if v < .8 or v > 1.25]
    if off: w.append('drawing vs rig proportions: ' + ', '.join(off))
    if t['kind'] == 'card': w.append('cut as a card, maybe not one clean figure')
    return '; '.join(w) or 'ok'


def write_index():
    out = []
    for fn in sorted(glob.glob(os.path.join(OUT, '*__*.json'))):
        d = json.load(open(fn))
        sc = [t['score'] for t in d['targets'] if t.get('score') is not None]
        out.append({'character': d['character'], 'file': 'poses/' + os.path.basename(fn), 'n': len(d['targets']),
                    'solved': len(sc), 'median_score': round(float(np.median(sc)), 3) if sc else None,
                    'contact': 'poses/' + os.path.basename(fn)[:-5] + '.contact.webp'})
    json.dump({'about': 'Pose Lab batch output index (shots/rig/solve.py)', 'characters': out},
              open(os.path.join(OUT, 'index.json'), 'w'), indent=1)


def report(results, skipped):
    allr = [(r['score'], r['id'], r.get('why') or r.get('fail'), k) for k, L in results.items() for r in L]
    sc = np.array([a[0] for a in allr if a[0] is not None])
    print('\n== score distribution (0..1: IoU x brad fit) ==')
    if len(sc):
        h, edges = np.histogram(sc, bins=[0, .2, .3, .4, .5, .6, .7, .8, 1.0])
        for c, a, b in zip(h, edges[:-1], edges[1:]): print(f'  {a:.1f}-{b:.1f} {"#" * c} {c}')
        print(f'  n={len(sc)} median {np.median(sc):.2f} mean {sc.mean():.2f}; unsolved {sum(1 for a in allr if a[0] is None)}')
    print('== worst 10 ==')
    for s, i, w, k in sorted(allr, key=lambda a: (a[0] if a[0] is not None else -1))[:10]:
        print(f'  {s if s is None else round(s, 2)}  {i}  — {w}')
    if skipped: print('no rig for:', dict(skipped))


def contact(doc, S, recs, path):
    tiles = []
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 13)
    except Exception: font = ImageFont.load_default()
    for r in recs:
        im = Image.open(os.path.join(SHOTS, r['img'])).convert('RGBA')
        W, H = im.size
        tile = Image.new('RGB', (W * 3 + 20, H + 40), (14, 11, 10))
        bg = Image.new('RGBA', im.size, (28, 22, 18, 255)); bg.alpha_composite(im)
        tile.paste(bg.convert('RGB'), (0, 0))
        d = ImageDraw.Draw(tile)
        if r.get('solves'):
            s = r['solves'][0]; z = np.array([s['params'][k] for k in PN] + [math.log(s['scale_px_per_cm'] / r['scale_prior']['px_per_cm'])])
            rig = render(doc, S, z, s['psi'], (W, H), s['scale_px_per_cm'], r['cx'], r['floor'], color=True)
            b2 = Image.new('RGBA', im.size, (28, 22, 18, 255)); b2.alpha_composite(rig); tile.paste(b2.convert('RGB'), (W + 10, 0))
            ov = Image.new('RGBA', im.size, (28, 22, 18, 255)); g = im.copy(); g.putalpha(Image.fromarray((np.asarray(im)[:, :, 3] * .45).astype(np.uint8)))
            ov.alpha_composite(g); rr = rig.copy(); rr.putalpha(Image.fromarray((np.asarray(rig)[:, :, 3] * .6).astype(np.uint8))); ov.alpha_composite(rr)
            tile.paste(ov.convert('RGB'), (2 * W + 20, 0))
            pr = Problem.__new__(Problem); pr.S, pr.t, pr.psi, pr.s0 = S, r, s['psi'], r['scale_prior']['px_per_cm']
            jp = pr.joints_px(z)
            for j, bi in s['match']:
                b = r['brads'][bi]; q = jp[JOINTS.index(j)]
                col = (255, 90, 80) if s['err_cm'].get(j, 0) > 4 else (120, 220, 140)
                d.line([(2 * W + 20 + b[0], b[1]), (2 * W + 20 + q[0], q[1])], fill=col, width=2)
                d.ellipse([2 * W + 20 + q[0] - 3, q[1] - 3, 2 * W + 20 + q[0] + 3, q[1] + 3], fill=col)
            for b in r['brads']:
                d.ellipse([2 * W + 20 + b[0] - 5, b[1] - 5, 2 * W + 20 + b[0] + 5, b[1] + 5], outline=(95, 208, 255), width=2)
            txt = f'{r["score"]:.2f}  IoU {s["iou"]:.2f}  err {s["mean_err_cm"]} cm  {s["view"]}'
        else:
            txt = 'unsolved: ' + (r.get('fail') or '')
        d.text((4, H + 4), (r['label'] or r['id'].split('/')[-1])[:40], fill=(239, 230, 218), font=font)
        d.text((4, H + 21), txt, fill=(231, 163, 90) if (r.get('score') or 0) >= .5 else (255, 107, 90), font=font)
        tiles.append(tile)
    if not tiles: return
    th = int(os.environ.get("TH", 230))
    tiles = [t.resize((int(t.width * th / t.height), th)) for t in tiles]
    cols, rows, x, y, rowh = [], [], 0, 0, th
    Wmax = 2400
    pos = []
    for t in tiles:
        if x + t.width > Wmax: x = 0; y += rowh + 8
        pos.append((x, y)); x += t.width + 8
    sheet = Image.new('RGB', (Wmax, y + rowh), (8, 6, 5))
    for t, p in zip(tiles, pos): sheet.paste(t, p)
    sheet.save(path, quality=80)


# ------------------------------------------------------------------------------------------- the anim walk
BOLAS = os.path.join(SHOTS, 'arena', 'bolas', 'bank')
BONES = [('pelvis', 'neck', 'pelvis', 'neckBase'), ('neck', 'top', 'neckBase', 'headTop'),
         ('shL', 'elL', 'shoulderL', 'elbowL'), ('elL', 'wrL', 'elbowL', 'wristL'),
         ('shR', 'elR', 'shoulderR', 'elbowR'), ('elR', 'wrR', 'elbowR', 'wristR'),
         ('hipL', 'knL', 'hipL', 'kneeL'), ('knL', 'anL', 'kneeL', 'ankleL'), ('heelL', 'toeL', 'heelL', 'toeL'),
         ('hipR', 'knR', 'hipR', 'kneeR'), ('knR', 'anR', 'kneeR', 'ankleR'), ('heelR', 'toeR', 'heelR', 'toeR'),
         ('hipR', 'hipL', 'hipR', 'hipL'), ('shR', 'shL', 'shoulderR', 'shoulderL')]


def bolas_frames(act='T001'):
    """Bolas bank act -> per frame {joint: [X, Y, Z]} in the Pose Lab body frame (X = actor's left, Y down,
       Z forward), using the act's own forward vector (Bolas: y up, the actor's left at -z when facing +x)."""
    d = json.load(open(os.path.join(BOLAS, act + '.json')))
    names = d['joints']
    out = []
    for fr in d['frames']:
        a = fr['a'][d['actors'][0]['id']]
        fw = np.array(a.get('fwd', [1, 0, 0]), float); fw[1] = 0; fw /= np.linalg.norm(fw) or 1
        up = np.array([0, 1.0, 0]); left = np.cross(fw, up) * -1      # facing +x: left = -z
        P = {n: np.array(p, float) for n, p in zip(names, a['j'])}
        out.append({n: [float(p @ left), float(-p[1]), float(p @ fw)] for n, p in P.items()})
    return d, out


def fit_bolas(S, Jb, z0=None):
    """Joint angles whose bone directions match one Bolas frame (proportions differ, so directions only)."""
    lo, hi = lims()
    free = [PI[n] for n in PN if n not in ('ox', 'oy', 'oz') and n not in KN]

    def f(v):
        z = np.zeros(NP); z[free] = v
        J = fk(S, z[None])
        r = []
        for a, b, A, B in BONES:
            u = J[b][0] - J[a][0]; w = np.array(Jb[B]) - np.array(Jb[A])
            r.extend(u / (np.linalg.norm(u) or 1) - w / (np.linalg.norm(w) or 1))
        r.extend(.02 * z[ANG] / 90)
        r.extend(.5 * z[3:6] / 90)          # the root stays upright; the trunk takes the lean
        return np.array(r)
    x0 = np.zeros(len(free)) if z0 is None else z0[free]
    x0 = np.clip(x0, lo[free] + 1e-6, hi[free] - 1e-6)
    r = least_squares(f, x0, bounds=(lo[free], hi[free]), max_nfev=200)
    z = np.zeros(NP); z[free] = r.x
    return z, float(np.sqrt(np.mean(r.fun ** 2)))


def walk_keys(S, act='T001'):
    """Contact / passing / contact / passing keys of one walk cycle from the Bolas bank (local extremes of the
       forward distance between the ankles), fitted to this skeleton."""
    d, F = bolas_frames(act)
    sep = np.array([f['ankleL'][2] - f['ankleR'][2] for f in F])
    n = len(F); keys = []
    for i in range(2, n - 2):
        w = sep[i - 2:i + 3]
        if sep[i] == w.max() and sep[i] > 15: keys.append((i, 'contact, L foot forward'))
        elif sep[i] == w.min() and sep[i] < -15: keys.append((i, 'contact, R foot forward'))
    # passing: the zero crossings between contacts
    cyc = []
    for (i, a), (j, b) in zip(keys, keys[1:]):
        if a != b:
            k = i + int(np.argmin(np.abs(sep[i:j]))); cyc += [(i, a), (k, 'passing')]
    cyc = cyc[:4] if len(cyc) >= 4 else cyc
    out = []; z = None
    for i, lab in cyc:
        z, err = fit_bolas(S, F[i], z)
        J = F[i]; ground = -min(J['heelL'][1], J['heelR'][1], J['toeL'][1], J['toeR'][1])
        out.append({'f': int(i), 'label': lab, 'fit_rms': round(err, 3), 'params': {k: round(float(v), 2) for k, v in zip(PN, z)},
                    'pelvis_cm': [round(v, 1) for v in J['pelvis']]})
    return {'source': f'Bolas bank {act} ({d["title"]}), {d.get("after", "")}', 'act': act, 'fps': 24, 'keys': out}


def add_walks():
    for fn in sorted(glob.glob(os.path.join(OUT, '*__*.json'))):
        d = json.load(open(fn)); key = d['character']
        doc = load_rig(key); S = skeleton(doc)
        d['walk'] = walk_keys(S)
        json.dump(d, open(fn, 'w'), separators=(',', ':'))
        print(key, [(k['f'], k['label'], k['fit_rms']) for k in d['walk']['keys']])


def export_targets():
    """poses/targets.json: every target with its brads, floor and scale prior (input to markers.mjs / MoveNet)."""
    targets, skipped = target_list()
    docs = {k: load_rig(k) for k in {t['key'] for t in targets}}
    for d in docs.values(): d['_S'] = skeleton(d)
    for t in targets: prepare(t)
    pri = sheet_scale_prior(targets, {k: d['_S']['standing_cm'] for k, d in docs.items()})
    out = [{k: t[k] for k in ('id', 'img', 'label', 'sheet', 'kind', 'key', 'w', 'h', 'bbox', 'floor', 'cx', 'brads')} |
           {'scale_prior': {'px_per_cm': round(pri[t['id']][0], 4), 'sigma_log': pri[t['id']][1], 'why': pri[t['id']][2]}} for t in targets]
    os.makedirs(OUT, exist_ok=True)
    json.dump({'about': 'Pose targets (shots/rig/solve.py --targets)', 'targets': out, 'no_rig': dict(skipped)},
              open(os.path.join(OUT, 'targets.json'), 'w'), separators=(',', ':'))
    print(len(out), 'targets ->', os.path.join(OUT, 'targets.json'))


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--targets' in a:
        export_targets(); sys.exit()
    if '--walks' in a:
        add_walks(); sys.exit()
    only = None; quick = '--quick' in a
    if '--only' in a: i = a.index('--only'); only = a[i + 1]; del a[i:i + 2]
    a = [x for x in a if not x.startswith('--')]
    run(set(a) or None, only, quick)
