"""Character rigs for the animation library, built from the cut poem-kit parts.

Every card is resolved to named points in its own pixel frame:

    limb   pivot (top brad)  socket (bottom brad)
    torso  waist (bottom brad)  neck (top brad)  shL / shR (shoulder brads, or a hint)
    bridge waist (top brad)  hipL / hipR (lower brads)
    head   neck (bottom brad on the neck tab)  top (highest opaque pixel above it)
    hand   wrist (tab brad)  tip (lowest opaque pixel centroid)
    foot   ankle (tab brad)  heel / toe (lowest opaque pixels at each end of the sole)
    skirt  waist (mid-point of the waistband brads)  hem (bottom centre)

Brads come from shots/kits/cut/catalog.json (brass circles detected by the
cutter, in part-local px). The detector also fires on knuckles, ears and
laces, so points are chosen by geometry (central band, top/bottom) instead of
trusting the catalog's own `pivot`, and fall back to a hint when no brad is
there. Sole and head-top points come from the alpha channel.

Scale is never taken from the card's pixel size: every card is scaled so the
segment it spans has the character's length in cm (see SPEC props), which is
what stops heads, hands and feet ballooning when sheets were drawn at
different resolutions.
"""
import json, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(os.path.dirname(HERE))
CUT = os.path.join(SHOTS, 'kits', 'cut')
PACK = os.path.join(SHOTS, 'kits', 'packs')
_CAT = None


def catalog():
    global _CAT
    if _CAT is None:
        d = json.load(open(os.path.join(CUT, 'catalog.json')))['sheets']
        _CAT = {p['id']: p for s in d.values() for p in s['parts']}
    return _CAT


def _img_path(pid):
    """Path relative to shots/ and absolute path for a part id."""
    if pid.startswith('pack:'):
        rel = os.path.join('kits', 'packs', pid[5:])
    else:
        rel = os.path.join('kits', 'cut', catalog()[pid]['file'])
    return rel, os.path.join(SHOTS, rel)


def _cleaned(pid, rel, ab):
    """Some cut images still carry the thin panel-frame lines of their sheet (the hipcore
       sheets especially). Keep only the largest opaque island, written as a copy under
       shots/stage/anim/parts/ (the cut/ folder is never modified)."""
    from scipy import ndimage
    im = Image.open(ab).convert('RGBA'); a = np.asarray(im)
    m = a[:, :, 3] > 40
    lab, n = ndimage.label(m)
    if n <= 1:
        return rel, ab
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    keep = lab == (1 + int(np.argmax(sizes)))
    keep = ndimage.binary_dilation(keep, iterations=2)
    if (m & ~keep).sum() < 30:
        return rel, ab
    b = a.copy(); b[:, :, 3] = np.where(keep, a[:, :, 3], 0)
    name = pid.replace('pack:', 'pack.').replace('/', '__') + '.png'
    out = os.path.join(HERE, 'parts', name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(ab):
        Image.fromarray(b).save(out, optimize=True)
    return os.path.relpath(out, SHOTS), out


def _alpha(abs_path):
    im = Image.open(abs_path).convert('RGBA')
    return np.asarray(im)[:, :, 3] > 100


def _brads(pid, A):
    if pid.startswith('pack:'):
        return _pack_brads(A)
    return [tuple(map(float, b)) for b in catalog()[pid].get('brads', [])]


def _pack_brads(A):
    return []          # pack PNGs carry no brad list; their pivots come from hints


def _central(brads, w, band=0.30):
    return [b for b in brads if abs(b[0] - w / 2) <= band * w]


def resolve(pid, kind, hints=None):
    """Return {'id','img','abs','w','h','pts':{...},'faces':+1/-1/0}."""
    hints = dict(hints or {})
    rel, ab = _img_path(pid)
    if not pid.startswith('pack:'):
        rel, ab = _cleaned(pid, rel, ab)
    A = _alpha(ab)
    h, w = A.shape
    ys, xs = np.nonzero(A)
    B = _brads(pid, A)
    pts = {}
    faces = 0

    def hint(name, default):
        v = hints.get(name, default)
        p = [v[0] * w, v[1] * h]
        # a hint snaps onto a detected brad when one is close: the hint says which
        # brad, the brad says exactly where
        if name in hints and B:
            b = min(B, key=lambda b: (b[0] - p[0]) ** 2 + (b[1] - p[1]) ** 2)
            if (b[0] - p[0]) ** 2 + (b[1] - p[1]) ** 2 < (0.07 * max(w, h)) ** 2:
                return list(b)
        return p

    if kind == 'limb':
        c = _central(B, w, 0.35)
        top = [b for b in c if b[1] < 0.35 * h]
        bot = [b for b in c if b[1] > 0.65 * h]
        near = lambda L, p: list(min(L, key=lambda b: (b[0] - p[0]) ** 2 + (b[1] - p[1]) ** 2))
        pts['pivot'] = near(top, (w / 2, 0.07 * h)) if top and 'pivot' not in hints else hint('pivot', (0.5, 0.07))
        pts['socket'] = near(bot, (w / 2, 0.93 * h)) if bot and 'socket' not in hints else hint('socket', (0.5, 0.93))
    elif kind == 'torso':
        c = _central(B, w, 0.2)
        top = [b for b in c if b[1] < 0.3 * h]
        bot = [b for b in c if b[1] > 0.7 * h]
        pts['neck'] = list(min(top, key=lambda b: b[1])) if top and 'neck' not in hints else hint('neck', (0.5, 0.04))
        pts['waist'] = list(max(bot, key=lambda b: b[1])) if bot and 'waist' not in hints else hint('waist', (0.5, 0.95))
        side = [b for b in B if b[1] < 0.35 * h and abs(b[0] - w / 2) > 0.28 * w]
        left = [b for b in side if b[0] < w / 2]
        right = [b for b in side if b[0] > w / 2]
        # viewer-left / viewer-right; which one is the actor's L is decided per view
        pts['shVL'] = list(min(left, key=lambda b: b[0])) if left and 'shVL' not in hints else hint('shVL', (0.12, 0.17))
        pts['shVR'] = list(max(right, key=lambda b: b[0])) if right and 'shVR' not in hints else hint('shVR', (0.88, 0.17))
    elif kind == 'bridge':
        if len(B) >= 3 and 'waist' not in hints:
            yb0, yb1 = ys.min(), ys.max(); xb0, xb1 = xs.min(), xs.max()
            wb = min(B, key=lambda b: (b[0] - (xb0 + xb1) / 2) ** 2 + (b[1] - yb0) ** 2)
            rest = [b for b in B if b is not wb and b[1] > wb[1] + 0.1 * (yb1 - yb0)]
            pts['waist'] = list(wb)
            pts['hipVL'] = list(min(rest, key=lambda b: b[0]))
            pts['hipVR'] = list(max(rest, key=lambda b: b[0]))
        else:
            pts['waist'] = hint('waist', (0.5, 0.15))
            pts['hipVL'] = hint('hipVL', (0.15, 0.8))
            pts['hipVR'] = hint('hipVR', (0.85, 0.8))
    elif kind == 'seat':
        pts['waist'] = hint('waist', (0.5, 0.08))
        pts['hem'] = hint('hem', (0.5, 0.95))
    elif kind == 'skirt':
        tb = sorted([b for b in B if b[1] < 0.25 * h], key=lambda b: b[0])
        if len(tb) >= 2 and 'waist' not in hints:
            pts['waist'] = [(tb[0][0] + tb[-1][0]) / 2, (tb[0][1] + tb[-1][1]) / 2]
        else:
            pts['waist'] = hint('waist', (0.5, 0.08))
        pts['hem'] = [w / 2, float(ys.max())]
    elif kind == 'head':
        c = _central(B, w, 0.30)
        bot = [b for b in c if b[1] > 0.75 * h]
        pts['neck'] = list(min(bot, key=lambda b: (b[0] - w / 2) ** 2 + (b[1] - 0.93 * h) ** 2)) \
            if bot and 'neck' not in hints else hint('neck', (0.5, 0.92))
        ytop = float(ys.min())
        pts['top'] = [pts['neck'][0], ytop]
        for k in ('eye',):
            if k in hints: pts[k] = hint(k, None)
    elif kind == 'hand':
        top = [b for b in B if b[1] < 0.3 * h]
        pts['wrist'] = list(min(top, key=lambda b: b[1])) if top and 'wrist' not in hints else hint('wrist', (0.5, 0.08))
        yb = ys.max()
        sel = ys > yb - 0.12 * h
        pts['tip'] = [float(xs[sel].mean()), float(yb)]
    elif kind == 'foot':
        # the tab: the upper 18% of the opaque rows
        tsel = ys < ys.min() + 0.18 * h
        tab_cx = float(xs[tsel].mean())
        tab_y = float(ys.min()) + 0.12 * h
        cand = [b for b in B if b[1] < 0.5 * h]
        if cand and 'ankle' not in hints:
            pts['ankle'] = list(min(cand, key=lambda b: (b[0] - tab_cx) ** 2 + (b[1] - tab_y) ** 2))
        else:
            pts['ankle'] = hint('ankle', (tab_cx / w, tab_y / h))
        x0, x1 = xs.min(), xs.max()
        span = x1 - x0
        lsel = xs < x0 + 0.25 * span
        rsel = xs > x1 - 0.25 * span
        # the extreme tip in x (the foot's real length), at the height of the lowest
        # sole pixel near that end (so heel->toe still runs along the sole)
        lpt = [float(x0), float(ys[lsel].max())]
        rpt = [float(x1), float(ys[rsel].max())]
        # the toe is the end farther from the ankle tab; front/back cards have no toe
        if hints.get('front'):
            faces = 0
            pts['heel'] = [float(x0), float(ys.max())]
            pts['toe'] = [float(x1), float(ys.max())]
        elif hints.get('faces', 1 if abs(x1 - tab_cx) > abs(tab_cx - x0) else -1) == 1:
            faces = 1; pts['heel'], pts['toe'] = lpt, rpt
        else:
            faces = -1; pts['heel'], pts['toe'] = rpt, lpt
        pts['sole'] = [(pts['heel'][0] + pts['toe'][0]) / 2, float(ys.max())]
    elif kind == 'glasses':
        pts['anchor'] = hint('anchor', (0.5, 0.5))
    else:
        raise ValueError(kind)
    if 'faces' in hints:
        faces = hints['faces']
    return {'id': pid, 'img': rel.replace(os.sep, '/'), 'w': w, 'h': h, 'pts': pts, 'faces': faces,
            'kind': kind}


# --------------------------------------------------------------------------------------
# Character specs.  props are fractions of standing height H (cm).
#   bridge= hip joint -> waist brad      torso = waist -> neck brad (derived so the total is H)
#   head  = neck brad -> top of skull    hand = wrist -> fingertip   foot = heel -> toe
# --------------------------------------------------------------------------------------
# hip = hip-joint height, knee = knee height (the shin card spans knee -> the foot card's ankle brad,
# however high the boot puts that brad), torso = 1 - hip - bridge - head so the total is exactly H.
ADULT_M = dict(hip=0.520, knee=0.285, bridge=0.075, head=0.175, uarm=0.170, farm=0.150, hand=0.105, foot=0.145)
ADULT_F = dict(hip=0.520, knee=0.280, bridge=0.080, head=0.180, uarm=0.165, farm=0.145, hand=0.100, foot=0.135)
CHILD = dict(hip=0.480, knee=0.265, bridge=0.065, head=0.225, uarm=0.160, farm=0.140, hand=0.100, foot=0.150)

P = 'poet.red_black_sunglasses'
TS = 'pack:poet_tracksuit_v1/01_COMPONENTS/'

SPEC = {
    'poet_tracksuit': dict(
        title='POET - black/red tracksuit + sunglasses (poems 04-14)', height_cm=180, props=dict(ADULT_M, bridge=0.035),
        views={
            'profile': dict(
                torso=(P + '.body.profile/torso', 'torso', {'faces': 1, 'neck': (0.58, 0.077), 'shVL': (0.42, 0.16), 'shVR': (0.42, 0.16)}),
                bridge=(P + '.hipcore/4-hip-bridge', 'bridge', {}),
                uarm=(P + '.body.profile/part-3', 'limb', {}), farm=(P + '.body.profile/part-4', 'limb', {}),
                thigh=(P + '.body.profile/thigh-l', 'limb', {}), shin=(P + '.body.profile/shin-l', 'limb', {}),
                hand=(P + '.body.profile/hand-l', 'hand', {'faces': 1}),
                foot=(P + '.feet/flat', 'foot', {}), foot_heelup=(P + '.feet/heel-up', 'foot', {}),
                foot_toeup=(P + '.feet/toe-up', 'foot', {})),
            'front': dict(
                torso=(P + '.body.front/1', 'torso', {}), bridge=(P + '.hipcore/4-hip-bridge', 'bridge', {}),
                uarm_L=(P + '.body.front/upper-arm-l', 'limb', {}), uarm_R=(P + '.body.front/5-upper-arm', 'limb', {}),
                farm_L=(P + '.body.front/3-forearm-l', 'limb', {}), farm_R=(P + '.body.front/forearm-r', 'limb', {}),
                hand_L=(P + '.body.front/4-hand-l', 'hand', {}), hand_R=(P + '.body.front/7-hand-r', 'hand', {}),
                thigh_L=(P + '.body.front/8-thigh-l', 'limb', {}), thigh_R=(P + '.body.front/11-thigh-r', 'limb', {}),
                shin_L=(P + '.body.front/shin-l', 'limb', {}), shin_R=(P + '.body.front/12-shin-r', 'limb', {}),
                foot_L=(TS + '19_boot_front_L.png', 'foot', {'front': True, 'ankle': (0.5, 0.17)}),
                foot_R=(TS + '20_boot_front_R.png', 'foot', {'front': True, 'ankle': (0.5, 0.17)})),
            'back': dict(
                torso=(P + '.hipcore/2-3', 'torso', {}), bridge=(P + '.hipcore/4-hip-bridge', 'bridge', {}),
                seat=(P + '.hipcore/5-rear-seat', 'seat', {'waist': (0.5, 0.1)}),
                uarm_L=(P + '.body.back/upper-arm-l', 'limb', {}), uarm_R=(P + '.body.back/upper-arm-r', 'limb', {}),
                farm_L=(P + '.body.back/for-l', 'limb', {}), farm_R=(P + '.body.back/forearm-r', 'limb', {}),
                hand_L=(P + '.body.back/l', 'hand', {}), hand_R=(P + '.body.back/hand-r', 'hand', {}),
                thigh_L=(P + '.body.back/l-2', 'limb', {}), thigh_R=(P + '.body.back/thigh-r', 'limb', {}),
                shin_L=(P + '.body.back/shin-r', 'limb', {}), shin_R=(P + '.body.back/shin-r', 'limb', {}),
                foot_L=(P + '.feet/threequarter', 'foot', {'front': True}), foot_R=(P + '.feet/threequarter', 'foot', {'front': True})),
        },
        heads=dict(front=(P + '.heads/front', {}), threequarter=(P + '.heads/threequarter', {'faces': 1}),
                   profile=(P + '.heads/profile', {'faces': 1}), threequarter_back=(P + '.heads/threequarter-back', {'faces': -1}),
                   back=(P + '.heads/back', {})),
        glasses=dict(front=(TS + '31_sunglasses_front.png', 0.95, (0.5, 0.40)),
                     threequarter=(P + '.master/front-2', 0.80, (0.62, 0.40)),
                     profile=(P + '.master/sunglasses-right', 0.50, (0.74, 0.385))),
    ),
    'poet_tshirt': dict(
        title='POET - black t-shirt (poems 01-03)', height_cm=180, props=ADULT_M,
        views={
            'front': dict(
                torso=('poet.black_tshirt.compact-core/01-torso-front', 'torso', {}),
                bridge=('poet.black_tshirt.compact-core/03-hip-bridge', 'bridge', {}),
                uarm_L=('poet.black_tshirt.compact-core/upperarm', 'limb', {}), uarm_R=('poet.black_tshirt.compact-core/upperarm-2', 'limb', {}),
                farm_L=('poet.black_tshirt.compact-core/06-forearm', 'limb', {}), farm_R=('poet.black_tshirt.compact-core/forearm', 'limb', {}),
                hand_L=(P + '.body.front/4-hand-l', 'hand', {}), hand_R=(P + '.body.front/7-hand-r', 'hand', {}),
                thigh_L=('poet.black_tshirt.compact-core/09-thigh-l', 'limb', {}), thigh_R=('poet.black_tshirt.compact-core/11-thighr', 'limb', {}),
                shin_L=('poet.black_tshirt.compact-core/10', 'limb', {}), shin_R=('poet.black_tshirt.compact-core/12', 'limb', {}),
                foot_L=('poet.black_tshirt.compact-core/13-foot-l-poet-black-tshirt-compact-core', 'foot', {}),
                foot_R=('poet.black_tshirt.compact-core/14-foot-r-for-poems01-02-03', 'foot', {})),
            'back': dict(
                torso=('poet.black_tshirt.compact-core/02-torso-back', 'torso', {}),
                bridge=('poet.black_tshirt.compact-core/03-hip-bridge', 'bridge', {}),
                seat=('poet.black_tshirt.compact-core/04-seat-rear', 'seat', {}),
                uarm_L=('poet.black_tshirt.compact-core/upperarm', 'limb', {}), uarm_R=('poet.black_tshirt.compact-core/upperarm-2', 'limb', {}),
                farm_L=('poet.black_tshirt.compact-core/06-forearm', 'limb', {}), farm_R=('poet.black_tshirt.compact-core/forearm', 'limb', {}),
                hand_L=(P + '.body.back/l', 'hand', {}), hand_R=(P + '.body.back/hand-r', 'hand', {}),
                thigh_L=('poet.black_tshirt.compact-core/09-thigh-l', 'limb', {}), thigh_R=('poet.black_tshirt.compact-core/11-thighr', 'limb', {}),
                shin_L=('poet.black_tshirt.compact-core/10', 'limb', {}), shin_R=('poet.black_tshirt.compact-core/12', 'limb', {}),
                foot_L=('poet.black_tshirt.compact-core/13-foot-l-poet-black-tshirt-compact-core', 'foot', {}),
                foot_R=('poet.black_tshirt.compact-core/14-foot-r-for-poems01-02-03', 'foot', {})),
        },
        # the t-shirt kit has no heads: same man, so the tracksuit heads without the sunglasses
        heads=dict(front=(P + '.heads/front', {}), threequarter=(P + '.heads/threequarter', {'faces': 1}),
                   profile=(P + '.heads/profile', {'faces': 1}), threequarter_back=(P + '.heads/threequarter-back', {'faces': -1}),
                   back=(P + '.heads/back', {})),
        front_for_profile=True,
    ),
    'young_poet': dict(
        title='YOUNG POET - child clothes', height_cm=122, props=CHILD,
        views={
            'profile': dict(
                torso=('young_poet.child_clothes.body.profile/01-torso-right-profile', 'torso', {'faces': 1, 'shVL': (0.42, 0.2), 'shVR': (0.42, 0.2)}),
                bridge=('young_poet.child_clothes.hipcore/part-1', 'bridge', {'waist': (0.5, 0.15), 'hipVL': (0.3, 0.8), 'hipVR': (0.7, 0.8), 'virtual': True}),
                uarm=('young_poet.child_clothes.body.profile/02-upper-arm-right-profile', 'limb', {}),
                farm=('young_poet.child_clothes.body.profile/03-forearm-right-profile', 'limb', {}),
                hand=('young_poet.child_clothes.body.profile/04-hand-l-right-profile', 'hand', {'faces': 1}),
                thigh=('young_poet.child_clothes.body.profile/05-thigh-l-right-profile', 'limb', {}),
                shin=('young_poet.child_clothes.body.profile/06-shin-l-right-profile', 'limb', {}),
                foot=('young_poet.child_clothes.feet/01-flat-profile', 'foot', {}),
                foot_heelup=('young_poet.child_clothes.feet/poet-child', 'foot', {'faces': 1}),
                foot_toeup=('young_poet.child_clothes.feet/03-toe-up', 'foot', {})),
        },
        heads=dict(front=('young_poet.child_clothes.heads/front', {}), threequarter=('young_poet.child_clothes.heads/threequarter-right', {'faces': 1}),
                   profile=('young_poet.child_clothes.heads/profile-right', {'faces': 1}),
                   threequarter_back=('young_poet.child_clothes.heads/threequarter-back', {'faces': -1}),
                   back=('young_poet.child_clothes.heads/back', {})),
    ),
    'woman': dict(
        title='WOMAN - red floral dress (poem 13)', height_cm=165, props=ADULT_F,
        views={
            'profile': dict(
                torso=('woman.13.body/18-bodice-profile', 'torso', {'faces': 1, 'neck': (0.72, 0.09), 'shVL': (0.2, 0.08), 'shVR': (0.2, 0.08)}),
                bridge=('woman.13.body/4-hip-bridge-1-upper-waist', 'bridge', {}),
                skirt=('woman.13.body/waist-to-knee', 'skirt', {}),
                uarm=('woman.13.body/8-upper-arm', 'limb', {}), farm=('woman.13.body/10-forearm', 'limb', {}),
                hand=('woman.13.heads-hands/17-hand-relaxed', 'hand', {'faces': 1}),
                thigh=('woman.13.body/12-thigh-l', 'limb', {}), shin=('woman.13.body/14-shin-l', 'limb', {}),
                foot=('woman.13.body/17-shoe-r', 'foot', {})),
        },
        # '4. HEAD RIGHT PROFILE' shows her right cheek, i.e. she faces screen-LEFT
        heads=dict(front=('woman.13.heads-hands/1-head-front', {}), threequarter=('woman.13.heads-hands/2-head-three-quarter', {'faces': -1}),
                   profile=('woman.13.heads-hands/4-head-right-profile', {'faces': -1}),
                   threequarter_back=('woman.13.heads-hands/5-head-back', {}),
                   back=('woman.13.heads-hands/5-head-back', {})),
    ),
    'ex': dict(
        title='EX - olive jacket, back views only (face never seen)', height_cm=183, props=ADULT_M,
        force_view='back',
        views={
            'back': dict(
                torso=('ex.ex_jacket.body.back/1-torso', 'torso', {}),
                bridge=('ex.ex_jacket.hipcore/4-hip-bridge', 'bridge', {}),
                seat=('ex.ex_jacket.hipcore/5-rear-seat', 'seat', {'waist': (0.5, 0.17)}),
                uarm_L=('ex.ex_jacket.body.back/2-upper-arm-l', 'limb', {}), uarm_R=('ex.ex_jacket.body.back/5-upper-armr', 'limb', {}),
                farm_L=('ex.ex_jacket.body.back/3-forearm-l', 'limb', {}), farm_R=('ex.ex_jacket.body.back/6-forearm-r', 'limb', {}),
                hand_L=('ex.ex_jacket.body.back/4-handl', 'hand', {}), hand_R=('ex.ex_jacket.body.back/7-handr', 'hand', {}),
                thigh_L=('ex.ex_jacket.body.back/8-thigh-l', 'limb', {}), thigh_R=('ex.ex_jacket.body.back/11-thigh-r', 'limb', {}),
                shin_L=('ex.ex_jacket.body.back/9-shinl', 'limb', {}), shin_R=('ex.ex_jacket.body.back/12-shinr', 'limb', {}),
                foot_L=('ex.ex_jacket.feet/back', 'foot', {'front': True}), foot_R=('ex.ex_jacket.feet/back', 'foot', {'front': True})),
        },
        heads=dict(back=('ex.ex_jacket.heads/back', {}), threequarter_back=('ex.ex_jacket.heads/right-three-quarter-rear', {'faces': 1}),
                   slight_back=('ex.ex_jacket.heads/slight-right-rear', {'faces': 1})),
    ),
    'party_guest': dict(
        title='PARTY GUEST - dancer in black (poem 07 party)', height_cm=178, props=ADULT_M,
        views={
            'profile': dict(
                torso=('party.party_guest.body.profile/2-torso', 'torso', {'faces': 1, 'shVL': (0.17, 0.19), 'shVR': (0.17, 0.19)}),
                bridge=('party.party_guest.body.profile/h-l-h-r-pelvis-16-connector', 'bridge', {}),
                uarm=('party.party_guest.body.profile/4-uarm-l', 'limb', {}), farm=('party.party_guest.body.profile/6', 'limb', {}),
                hand=('party.party_guest.body.profile/8-hand-l', 'hand', {'faces': 1}),
                thigh=('party.party_guest.body.profile/10', 'limb', {}), shin=('party.party_guest.body.profile/12', 'limb', {}),
                foot=('party.party_guest.body.profile/14', 'foot', {})),
        },
        heads=dict(front=('party.party_guest.heads/front', {}), threequarter=('party.party_guest.heads/threequarter', {'faces': 1}),
                   profile=('party.party_guest.heads/profile', {'faces': 1}),
                   threequarter_back=('party.party_guest.heads/threequarter-back', {'faces': -1}),
                   back=('party.party_guest.heads/back', {})),
    ),
}

_CACHE = {}


def build(name):
    """Resolve every card of a character. Returns the spec with resolved parts."""
    if name in _CACHE:
        return _CACHE[name]
    s = SPEC[name]
    out = {'name': name, 'title': s['title'], 'height_cm': s['height_cm'], 'props': dict(s['props']),
           'views': {}, 'heads': {}, 'glasses': {}, 'force_view': s.get('force_view'),
           'front_for_profile': s.get('front_for_profile', False)}
    for v, parts in s['views'].items():
        out['views'][v] = {}
        for key, (pid, kind, hints) in parts.items():
            r = resolve(pid, kind, hints)
            if hints.get('virtual'):
                r['virtual'] = True
            out['views'][v][key] = r
    for v, (pid, hints) in s['heads'].items():
        out['heads'][v] = resolve(pid, 'head', hints)
    for v, (pid, width_frac, at) in s.get('glasses', {}).items():
        g = resolve(pid, 'glasses', {})
        g['width_frac'] = width_frac      # glasses width as a fraction of the head card's width
        g['at'] = at                      # centre, as a fraction of the head card
        out['glasses'][v] = g
    _CACHE[name] = out
    return out


if __name__ == '__main__':
    import sys
    for n in (sys.argv[1:] or SPEC):
        r = build(n)
        for v, ps in r['views'].items():
            for k, p in ps.items():
                print(n, v, k, p['id'], p['faces'], {a: [round(x) for x in b] for a, b in p['pts'].items()})
