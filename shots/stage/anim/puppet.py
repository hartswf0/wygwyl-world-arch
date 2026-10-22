"""Keyframed cut-out puppets: a pose in, a list of brad-chained cards out (shots/stage/anim/puppet.py).

The retarget (retarget.py) re-solves recorded Bolas acts. Sequences need actions the bank never recorded
(lift a handset, ride, throw, scratch a record), so this solver takes a POSE per frame instead and chains
the same cards the same way: torso (waist brad -> neck brad) is the root, head and arms hang on the torso
card's own brads, legs reach from the hips to the foot card's ankle brad, every card is scaled from cm.

Angles (degrees) are measured from straight DOWN, positive toward the actor's FRONT in profile
(D(a) below). In front/back views the same numbers mean outward (lateral) for each arm and leg, so one
keyframe language serves every view.

POSE keys (all optional):
  x, y        pelvis (hip centre) in world cm; y=None stands the pelvis as high as both feet allow
  face        +1 faces screen-right, -1 screen-left (profile)
  view        'profile' | 'front' | 'back'
  lean        torso lean from vertical (+ forward);  tilt: head nod (+ down/forward); htilt: extra head roll
  hview       head card view override: front|threequarter|profile|threequarter_back|back;  hface: head facing
  set         stand | sit | kneel | crouch | lie_side | lie_back | fall   (poet replacement sheets)
  rot         whole-body roll about the pelvis (deg, + forward) for lying/falling
  aL, aR      arm: {sh, el, wr} FK, or {ik:(x,y) world cm, at:'grip'|'tip'|'wrist'|'palm', ha: hand angle, elbow: 'down'|'up'|'back'|'front'}
  hL, hR      hand shape (relaxed, open, fist, grip, pinch, point, flat, cup, wave, thumb, peace, claw, ...)
  hvL, hvR    hand view 'back'|'palm' (default: near hand back, far hand palm in profile)
  fL, fR      foot: {x, y, p (pitch, + toe up), c: 'heel'|'ball'|'sole'} placed, or {th, kn, p} FK (thigh, knee)
  eyes, brows, mouth   face patch states (cards.faces)
  stub        set of sides whose hands are OFF (wrist stub only: poem 04)
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigs, cards
from retarget import card_matrix, apply, mlist, unit, Body, K as K0, BALL_FRAC
from PIL import Image

DEG = math.pi / 180


def D(a, f=1.0):
    r = a * DEG
    return np.array([f * math.sin(r), math.cos(r)])


def ang(v, f=1.0):
    return math.degrees(math.atan2(f * v[0], v[1]))


def two_bone(A, B, l1, l2):
    """Both elbow/knee solutions for joints A->B with bone lengths l1, l2. Returns (sol1, sol2, reached, ratio)."""
    d = B - A; L = float(np.linalg.norm(d)); u = unit(d) if L > 1e-9 else np.array([0.0, 1.0])
    ratio = L / (l1 + l2)
    if L >= l1 + l2 - 1e-6:
        j = A + u * l1 * (L / (l1 + l2)) if L <= (l1 + l2) * 1.03 else A + u * l1
        reached = A + u * min(L, (l1 + l2) * 1.03)
        return j, j, reached, ratio
    L = max(L, abs(l1 - l2) + 1e-3)
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    n = np.array([-u[1], u[0]])
    return A + u * a + n * h, A + u * a - n * h, B, ratio


# ------------------------------------------------------------------ cast: which rig, hands, faces per character
CAST = {
    'poet_tracksuit': dict(rig='poet_tracksuit', hands='poet_tracksuit', faces='poet_tracksuit', sets=True, owner='poet_tracksuit'),
    'poet_tshirt': dict(rig='poet_tshirt', hands='poet_tshirt', faces='poet_tshirt', owner='poet_tshirt'),
    'young_poet': dict(rig='young_poet', hands='young_poet', owner='young_poet'),
    'woman': dict(rig='woman', hands='woman', faces='woman', owner='woman'),
    'ex': dict(rig='ex', owner='ex'),
    'party_guest': dict(rig='party_guest', hands='party_guest', owner='party_guest'),
}


def register(name, **kw):
    CAST[name] = kw


_HAND = {}


def hand_card(pid, tab):
    """Resolve a hand card: wrist (tab eyelet), axis (wrist -> hand centroid), tip length along the axis,
       grip point (palm centroid) and fingertip. Pixel units of the card."""
    key = (pid, tab)
    if key in _HAND: return _HAND[key]
    rel, ab = rigs._img_path(pid)
    if not pid.startswith(('pack:', 'crop:')):
        rel, ab = rigs._cleaned(pid, rel, ab)
    A = rigs._alpha(ab); h, w = A.shape
    ys, xs = np.nonzero(A)
    P = np.stack([xs, ys], 1).astype(float)
    ext = max(xs.max() - xs.min(), ys.max() - ys.min())
    inward = {'left': (1, 0), 'right': (-1, 0), 'top': (0, 1), 'bottom': (0, -1)}[tab]
    inward = np.array(inward, float)
    proj = P @ inward
    pend = proj.min()
    near = P[proj < pend + 0.10 * ext]
    end = near.mean(0)
    guess = end + inward * 0.075 * ext
    B = rigs._brads(pid, A)
    wrist = guess
    if B:
        b = min(B, key=lambda b: np.linalg.norm(np.array(b) - guess))
        if np.linalg.norm(np.array(b) - guess) < 0.10 * ext:
            wrist = np.array(b, float)
    beyond = P[(P - wrist) @ inward > 0.18 * ext]
    cen = beyond.mean(0) if len(beyond) else P.mean(0)
    axis = unit(cen - wrist)
    pr = (P - wrist) @ axis
    tip = P[int(np.argmax(pr))]
    out = {'id': pid, 'img': rel.replace(os.sep, '/'), 'w': w, 'h': h, 'wrist': wrist, 'axis': axis,
           'len': float(pr.max()), 'grip': cen, 'tip': tip}
    _HAND[key] = out
    return out


class Puppet:
    def __init__(self, name, actor=None):
        self.name = name; self.actor = actor or name
        c = CAST[name]; self.c = c
        self.rig = rigs.build(c['rig'])
        self.body = Body(self.rig)
        self.hsheets = cards.hands(c.get('hands', '')) if c.get('hands') else []
        self.faces = cards.faces(c['faces']) if c.get('faces') else {}
        self.sets = cards.sets() if c.get('sets') else {}
        self._cards = {}
        self.owner = c.get('owner', name)
        # register base cards for the checker
        for v, parts in self.rig['views'].items():
            for key, p in parts.items():
                role = key.split('_')[0]
                side = key.split('_')[1] if '_' in key and key.split('_')[1] in 'LR' else None
                if role in ('foot', 'heelup', 'toeup') or key.startswith('foot'):
                    role = 'foot'
                cards.reg(p['id'], role=role, side=side, view=v, faces=p['faces'] if v == 'profile' else 0, owner=self.owner)
        for v, p in self.rig['heads'].items():
            cards.reg(p['id'], role='head', view=v, faces=p['faces'], owner=self.owner)
        for v, p in self.rig['glasses'].items():
            cards.reg(p['id'], role='glasses', view=v, owner=self.owner)
        for s in self.hsheets:
            for (shape, view, side), pid in s['cards'].items():
                cards.reg(pid, owner=self.owner)
        # hand scale per sheet: the reference card's wrist->tip is the character's hand length
        for s in self.hsheets:
            ref = hand_card(s['ref'], s.get('tabs', {}).get(s['ref'], s['tab']))
            s['px'] = ref['len']

    # ---------------------------------------------------------------- card helpers
    def card(self, pid, kind, hints=None):
        key = (pid, kind)
        if key not in self._cards:
            self._cards[key] = rigs.resolve(pid, kind, hints or {})
        return self._cards[key]

    def set_card(self, setname, role, side=None):
        S = self.sets.get(setname)
        if not S: return None
        pid = S.get(role + ('_' + side if side else ''))
        if pid is None: return None
        kind = {'torso': 'torso', 'bridge': 'bridge', 'seat': 'seat', 'hand': 'hand', 'foot': 'foot'}.get(role, 'limb')
        hints = {}
        if kind == 'seat': hints = {'waist': (0.5, 0.1)}
        if kind == 'limb':
            return self.limb2(pid)
        return self.card(pid, kind, hints)

    def limb2(self, pid):
        """A limb card whose two brads may sit on a diagonal (kneeling thighs): pivot = upper brad, socket =
           the brad farthest from it."""
        key = (pid, 'limb2')
        if key in self._cards: return self._cards[key]
        c = rigs.resolve(pid, 'limb', {})
        B = rigs._brads(pid, None)
        if len(B) >= 2:
            pairs = [(np.linalg.norm(np.array(a) - np.array(b)), a, b) for i, a in enumerate(B) for b in B[i + 1:]]
            d, a, b = max(pairs)
            if d > 0.5 * max(c['w'], c['h']):
                top, bot = (a, b) if a[1] <= b[1] else (b, a)
                c = dict(c); c['pts'] = {'pivot': list(top), 'socket': list(bot)}
        self._cards[key] = c
        return c

    def hand_pick(self, shape, view, side):
        """(sheet, pid, mirror) for a wanted hand shape: exact side first, else the other side mirrored,
           else an alias shape. None when the character has no hand sheet."""
        for want in [shape] + [a for a in cards.SHAPE_ALIAS.get(shape, []) if a != shape] + ['relaxed']:
            for s in self.hsheets:
                C = s['cards']
                for v in ([view, 'any'] if view != 'any' else ['any', 'back', 'palm']):
                    if (want, v, side) in C: return s, C[(want, v, side)], False, want, v
                for v in ([view, 'any'] if view != 'any' else ['any', 'back', 'palm']):
                    o = 'L' if side == 'R' else 'R'
                    if (want, v, o) in C: return s, C[(want, v, o)], True, want, v
                # the opposite view row of the same side (palm<->back) before giving up on this shape
                for (sh, v, sd), pid in C.items():
                    if sh == want:
                        return s, pid, sd != side, want, v
        return None

    # ---------------------------------------------------------------- solve one pose
    def solve(self, P, k, O):
        """P: pose dict. k: px per cm. O: (x, y) screen of the world origin (x=0 on the floor).
           Returns (ops, pts, info): ops = [(z, op)], pts = named screen points, info = what was drawn."""
        b = self.body
        f = float(P.get('face', 1)); view = P.get('view', 'profile')
        if self.rig.get('force_view'): view = self.rig['force_view']
        if view not in self.rig['views']:
            view = 'profile' if 'profile' in self.rig['views'] else next(iter(self.rig['views']))
        V = self.rig['views'][view]
        prof = view == 'profile' and not self.rig.get('front_for_profile')
        setn = P.get('set', 'stand')
        O = np.asarray(O, float)
        W = lambda x, y: O + np.array([x * k, -y * k])
        rot = P.get('rot', 0.0)
        info = {'view': view, 'face': f, 'set': setn, 'cards': {}}
        ops = []; pts = {}
        g = lambda part: part

        def put(z, part, M, t, role, side=None, shade=0.0, extra=None):
            op = {'t': 'img', 'id': part['id'], 'm': mlist(M, t), 'tag': {'a': self.actor, 'r': role}}
            if side: op['tag']['s'] = side
            if shade: op['shade'] = round(shade, 2)
            if extra: op['tag'].update(extra)
            op['_img'] = part['img']
            ops.append((z, op))
            return op

        # sides: near / far (profile), lateral sign per side (front/back)
        near = 'R' if f > 0 else 'L'
        far = 'L' if near == 'R' else 'R'
        if prof:
            sgn = {'L': f, 'R': f}
        elif view == 'front':
            sgn = {'L': 1.0, 'R': -1.0}
        else:
            sgn = {'L': -1.0, 'R': 1.0}

        # ---- the set (replacement sheet) swaps
        use_set = setn in self.sets
        swap = {}
        if use_set:
            if view in ('front', 'back') or not prof:
                roles = ['torso', 'bridge', 'seat', 'uarm', 'farm', 'thigh', 'shin', 'foot']
            else:
                roles = ['thigh', 'shin', 'foot', 'uarm', 'farm']
            for r in roles:
                for s in ('L', 'R'):
                    c = self.set_card(setn, r, s if r not in ('torso', 'bridge', 'seat') else None)
                    if c is not None: swap[(r, s if r not in ('torso', 'bridge', 'seat') else None)] = c
            # in profile one card serves both sides, as in the base profile kit: take the near side's card
            if prof:
                for r in roles:
                    if (r, near) in swap: swap[(r, far)] = swap[(r, near)]

        def part(role, side=None):
            if (role, side) in swap: return swap[(role, side)]
            if (role, None) in swap and side is None: return swap[(role, None)]
            key = role + '_' + side if side and (role + '_' + side) in V else role
            return V.get(key)

        # ---- root and torso
        pel = W(P.get('x', 0.0), P['y']) if P.get('y') is not None else None
        lean = P.get('lean', 0.0) + rot
        if prof:
            up = D(180 - lean, f)
        else:
            up = D(180 - P.get('lean', 0.0), 1.0) if view == 'front' else D(180 + P.get('lean', 0.0), 1.0)
            if rot: up = D(180 - rot, 1.0)

        # pelvis auto-height from the feet (standing): highest pelvis both legs reach at 98.5%
        feet = {}
        for s in ('L', 'R'):
            fd = P.get('f' + s)
            if fd and 'x' in fd: feet[s] = fd
        hip_off = {}
        for s in ('L', 'R'):
            if prof:
                hip_off[s] = (0.012 if s == near else -0.012) * b.H * k * np.array([f, 0.0]) * 0.0
            else:
                hip_off[s] = np.array([sgn[s] * b.hipw / 2 * k, 0.0])

        # foot cards first (their ankle brad is where the leg must reach)
        foot = {}
        for s in ('L', 'R'):
            fd = P.get('f' + s) or {}
            foot[s] = self._foot(s, fd, V, view, prof, f, k, W, part, use_set and ('foot', s) in swap)

        if pel is None:
            ys = []
            for s, fd in feet.items():
                A = foot[s]['ankle']
                L = (b.thigh + b.shin) * k * P.get('reach', 0.985)
                hx = (P.get('x', 0.0) * k + O[0]) + hip_off[s][0]
                dx = abs(A[0] - hx)
                ys.append(A[1] - math.sqrt(max(0.0, L * L - dx * dx)))
            py = max(ys) if ys else W(0, b.hip * 0.98)[1]
            pel = np.array([O[0] + P.get('x', 0.0) * k, py])
        pts['pelvis'] = pel

        tc = part('torso')
        kt = b.torso * k / max(1e-6, np.linalg.norm(np.array(tc['pts']['neck']) - np.array(tc['pts']['waist'])))
        waist = pel + up * b.bridge * k
        neck = waist + up * b.torso * k
        mir_t = prof and tc['faces'] != 0 and tc['faces'] != f
        Mt, tt = card_matrix(tc['pts']['waist'], tc['pts']['neck'], waist, neck, kt, mirror=mir_t)
        pts['waist'] = waist; pts['neck'] = apply(Mt, tt, tc['pts']['neck'])
        if prof:
            shp = apply(Mt, tt, tc['pts']['shVL'])
            sh = {'L': shp, 'R': shp}
        else:
            Lright = view == 'front'
            sh = {'L': apply(Mt, tt, tc['pts']['shVR' if Lright else 'shVL']),
                  'R': apply(Mt, tt, tc['pts']['shVL' if Lright else 'shVR'])}
        info['cards']['torso'] = tc['id']

        # hips
        hip = {}
        bc = part('bridge')
        bridge_op = None
        if not prof and bc is not None and not bc.get('virtual'):
            hm = (np.array(bc['pts']['hipVL']) + np.array(bc['pts']['hipVR'])) / 2
            kb = b.bridge * k / max(1.0, np.linalg.norm(hm - np.array(bc['pts']['waist'])))
            Mb, tb = card_matrix(bc['pts']['waist'], hm, waist, waist - up * 100, kb, axial=kb)
            Lr = view == 'front'
            hip = {'L': apply(Mb, tb, bc['pts']['hipVR' if Lr else 'hipVL']),
                   'R': apply(Mb, tb, bc['pts']['hipVL' if Lr else 'hipVR'])}
            bridge_op = (Mb, tb, bc)
        else:
            for s in ('L', 'R'):
                hip[s] = pel + (hip_off[s] if not prof else np.zeros(2))

        # ---- head
        tilt = P.get('tilt', 0.0)
        hv = P.get('hview') or {'profile': 'profile', 'front': 'front', 'back': 'back'}[view]
        if hv not in self.rig['heads']:
            order = ['profile', 'threequarter', 'front', 'threequarter_back', 'back']
            hv = min(self.rig['heads'], key=lambda x: abs(order.index(x) - order.index(hv)) if x in order else 9)
        hc = self.rig['heads'][hv]
        hf = float(P.get('hface', f))
        if prof or hv in ('profile', 'threequarter', 'threequarter_back'):
            hdir = D(180 - lean - tilt, f) if prof else D(180 - tilt * hf, 1.0)
        else:
            hdir = D(180 - P.get('htilt', 0.0), 1.0) if view == 'front' else up
        if P.get('htilt'): hdir = D(ang(hdir) + P['htilt'], 1.0)
        kh = b.head * k / max(1e-6, np.linalg.norm(np.array(hc['pts']['top']) - np.array(hc['pts']['neck'])))
        mir_h = hc['faces'] != 0 and hc['faces'] != hf
        Mh, th = card_matrix(hc['pts']['neck'], hc['pts']['top'], pts['neck'], pts['neck'] + hdir * 100, kh, mirror=mir_h, axial=kh)
        head_ops = []
        HZ = 4.0
        head_ops.append(put(HZ - 0.3, hc, Mh, th, 'head', extra={'v': hv, 'hf': int(hf)}))
        info['cards']['head'] = hc['id']; info['head_view'] = hv
        pts['head_top'] = apply(Mh, th, hc['pts']['top'])
        hw, hh = hc['w'], hc['h']
        fdict = self.faces.get(hv if hv in self.faces else ('profile' if hv in ('profile',) else None), None) if self.faces else None
        if hv == 'profile':
            pts['mouth'] = apply(Mh, th, (0.80 * hw, 0.735 * hh)); pts['ear'] = apply(Mh, th, (0.42 * hw, 0.50 * hh))
            pts['eye'] = apply(Mh, th, (0.75 * hw, 0.43 * hh))
        else:
            pts['mouth'] = apply(Mh, th, (0.5 * hw, 0.70 * hh)); pts['ear'] = apply(Mh, th, (0.12 * hw, 0.50 * hh))
            pts['eye'] = apply(Mh, th, (0.5 * hw, 0.45 * hh))
        if fdict:
            for part_, st_key in (('eyes', 'eyes'), ('brows', 'brows'), ('mouth', 'mouth')):
                if part_ == 'eyes' and self.faces.get('glasses_hide_eyes') and not P.get('no_glasses'):
                    continue
                st = P.get(st_key) or {'eyes': 'open', 'brows': 'rest', 'mouth': 'rest'}[part_]
                pid = fdict[part_].get(st) or next(iter(fdict[part_].values()))
                fx, fy, fwf = fdict['at'][part_]
                fc = self.card(pid, 'glasses', {})
                s_ = fwf * hw / fc['w']
                Mf = Mh @ (np.eye(2) * s_)
                tf = Mh @ (np.array([fx * hw, fy * hh]) - s_ * np.array([fc['w'] / 2, fc['h'] / 2])) + th
                head_ops.append(put(HZ - 0.2 + 0.01 * len(head_ops), fc, Mf, tf, part_, extra={'st': st, 'v': hv}))
                info['cards'][part_] = (pid, st)
        gl = self.rig['glasses'].get(hv)
        if gl is not None and not P.get('no_glasses'):
            kg = kh * hc['w'] * gl['width_frac'] / gl['w']
            at = np.array([gl['at'][0] * hc['w'], gl['at'][1] * hc['h']])
            ctr = apply(Mh, th, at)
            hax = unit(Mh @ np.array([0, -1.0]))
            Mg, tg = card_matrix(gl['pts']['anchor'], np.array(gl['pts']['anchor']) + [0, -10], ctr, ctr + hax * 10, kg, mirror=mir_h, axial=kg)
            head_ops.append(put(HZ - 0.1, gl, Mg, tg, 'glasses'))
            pts['glasses'] = ctr

        # ---- arms
        z_arm = {}
        for s in ('L', 'R'):
            if prof:
                z_arm[s] = 5.0 if s == near else 1.0
            else:
                z_arm[s] = 5.0
        stub = set(P.get('stub', ()))
        for s in ('L', 'R'):
            a = P.get('a' + s) or {}
            sg = sgn[s]
            ua, fa = part('uarm', s), part('farm', s)
            l1, l2 = b.uarm * k, b.farm * k
            S = sh[s]
            # the hand card decides where the grip point is relative to the wrist
            hshape = P.get('h' + s, 'relaxed')
            hview = P.get('hv' + s) or (('back' if s == near else 'palm') if prof else 'back')
            hsel = self.hand_pick(hshape, hview, s) if self.hsheets else None
            hdcard = None
            if hsel is None:
                hdcard = part('hand', s)
            if 'ik' in a:
                T = W(*a['ik'])
                ha = a.get('ha', 90.0)
                hdir = D(ha, sg)
                if hsel is not None:
                    sheet, pid, mir, got, gv = hsel
                    tab = sheet.get('tabs', {}).get(pid, sheet['tab'])
                    hc_ = hand_card(pid, tab)
                    ks = b.hand * k / sheet['px']
                    Mh_, th_ = card_matrix(hc_['wrist'], hc_['wrist'] + hc_['axis'] * 100, np.zeros(2), hdir * 100, ks, mirror=mir, axial=ks)
                    ref = {'grip': hc_['grip'], 'tip': hc_['tip'], 'wrist': hc_['wrist'], 'palm': hc_['grip']}[a.get('at', 'grip')]
                    off = apply(Mh_, th_, ref)
                else:
                    off = hdir * b.hand * k * {'grip': 0.45, 'tip': 1.0, 'wrist': 0.0, 'palm': 0.4}[a.get('at', 'grip')]
                Wr = T - off
                e1, e2, reached, ratio = two_bone(S, Wr, l1, l2)
                pref = a.get('elbow', 'down')
                if 'pole' in a:          # the elbow aims at a direction from the shoulder (deg, D convention)
                    pp = S + D(a['pole'], sg) * l1
                    El = e1 if np.linalg.norm(e1 - pp) <= np.linalg.norm(e2 - pp) else e2
                elif pref == 'down': El = e1 if e1[1] >= e2[1] else e2
                elif pref == 'up': El = e1 if e1[1] < e2[1] else e2
                elif pref == 'back': El = e1 if sg * e1[0] < sg * e2[0] else e2
                elif pref == 'front': El = e1 if sg * e1[0] >= sg * e2[0] else e2
                else: El = e1
                Wr2 = El + unit(reached - El) * l2 if np.linalg.norm(reached - El) > 1e-6 else reached
                info.setdefault('reach', {})[s] = round(ratio, 3)
                info.setdefault('miss', {})[s] = round(float(np.linalg.norm(Wr2 - Wr)) / k, 2)
                Wr = Wr2
            else:
                shA = a.get('sh', 8.0 if prof else 6.0); el = a.get('el', 12.0)
                El = S + D(shA, sg) * l1
                Wr = El + D(shA + el, sg) * l2
                hdir = D(shA + el + a.get('wr', 0.0), sg)
                if 'ha' in a: hdir = D(a['ha'], sg)
            ku = b.uarm * k / max(1e-6, np.linalg.norm(np.array(ua['pts']['socket']) - np.array(ua['pts']['pivot'])))
            kf = b.farm * k / max(1e-6, np.linalg.norm(np.array(fa['pts']['socket']) - np.array(fa['pts']['pivot'])))
            mir_l = prof and f < 0
            Mu, tu = card_matrix(ua['pts']['pivot'], ua['pts']['socket'], S, El, ku, mirror=mir_l)
            Mf, tf = card_matrix(fa['pts']['pivot'], fa['pts']['socket'], El, Wr, kf, mirror=mir_l)
            shade = 0.35 if (prof and s == far and P.get('shade', True)) else 0.0
            zA = z_arm[s]
            role_extra = {}
            if s not in stub:
                if hsel is not None:
                    sheet, pid, mir, got, gv = hsel
                    tab = sheet.get('tabs', {}).get(pid, sheet['tab'])
                    hc_ = hand_card(pid, tab)
                    ks = b.hand * k / sheet['px']
                    Mhd, thd = card_matrix(hc_['wrist'], hc_['wrist'] + hc_['axis'] * 100, Wr, Wr + hdir * 100, ks, mirror=mir, axial=ks)
                    hpart = {'id': pid, 'img': hc_['img']}
                    put(zA - 0.02, hpart, Mhd, thd, 'hand', s, shade, {'sh': got, 'hv': gv, 'mir': int(mir)})
                    pts['grip_' + s] = apply(Mhd, thd, hc_['grip']); pts['tip_' + s] = apply(Mhd, thd, hc_['tip'])
                    info['cards']['hand_' + s] = (pid, got, gv, mir)
                else:
                    hd = hdcard
                    khd = b.hand * k / max(1e-6, np.linalg.norm(np.array(hd['pts']['tip']) - np.array(hd['pts']['wrist'])))
                    mir_hd = (hd['faces'] != 0 and hd['faces'] != f) if prof else False
                    Mhd, thd = card_matrix(hd['pts']['wrist'], hd['pts']['tip'], Wr, Wr + hdir * 100, khd, mirror=mir_hd, axial=khd)
                    put(zA - 0.02, hd, Mhd, thd, 'hand', s, shade, {'sh': 'relaxed', 'hv': 'kit'})
                    pts['grip_' + s] = apply(Mhd, thd, (np.array(hd['pts']['wrist']) + np.array(hd['pts']['tip'])) / 2)
                    pts['tip_' + s] = apply(Mhd, thd, hd['pts']['tip'])
                    info['cards']['hand_' + s] = (hd['id'], 'relaxed', 'kit', mir_hd)
            put(zA - 0.01, fa, Mf, tf, 'farm', s, shade)
            put(zA, ua, Mu, tu, 'uarm', s, shade)
            pts['sh_' + s] = S; pts['el_' + s] = El; pts['wr_' + s] = Wr; pts['hdir_' + s] = hdir
            pts['wrist_card_' + s] = apply(Mf, tf, fa['pts']['socket'])

        # ---- legs
        for s in ('L', 'R'):
            fd = P.get('f' + s) or {}
            th_, sn = part('thigh', s), part('shin', s)
            l1, l2 = b.thigh * k, b.shin * k
            Hp = hip[s]
            sg = sgn[s]
            fc = foot[s]
            if 'th' in fd and 'x' not in fd:
                Kn = Hp + D(fd['th'], sg) * l1
                A = Kn + D(fd['th'] - fd.get('kn', 0.0), sg) * l2
                fc = self._foot(s, dict(fd, ankle=A), V, view, prof, f, k, W, part, use_set and ('foot', s) in swap)
                foot[s] = fc
                reached = A
            else:
                A = fc['ankle']
                e1, e2, reached, ratio = two_bone(Hp, A, l1, l2)
                kpref = fd.get('knee', 'front')
                if prof or kpref in ('front', 'back'):
                    Kn = e1 if sg * e1[0] >= sg * e2[0] else e2
                    if kpref == 'back': Kn = e2 if Kn is e1 else e1
                else:
                    Kn = e1 if sg * e1[0] >= sg * e2[0] else e2
                info.setdefault('leg_reach', {})[s] = round(ratio, 3)
                if np.linalg.norm(reached - A) > 0.5:
                    info.setdefault('foot_miss', {})[s] = round(float(np.linalg.norm(reached - A)) / k, 2)
            kth = b.thigh * k / max(1e-6, np.linalg.norm(np.array(th_['pts']['socket']) - np.array(th_['pts']['pivot'])))
            ksn = b.shin * k / max(1e-6, np.linalg.norm(np.array(sn['pts']['socket']) - np.array(sn['pts']['pivot'])))
            mir_l = prof and f < 0
            Mth, tth = card_matrix(th_['pts']['pivot'], th_['pts']['socket'], Hp, Kn, kth, mirror=mir_l)
            Msn, tsn = card_matrix(sn['pts']['pivot'], sn['pts']['socket'], Kn, reached, ksn, mirror=mir_l)
            shade = 0.35 if (prof and s == far and P.get('shade', True)) else 0.0
            zL = (3.0 if s == near else 2.0) if prof else 2.0
            Mft, tft = fc['M'], fc['t']
            if np.linalg.norm(reached - fc['ankle']) > 1e-6:
                tft = tft + (reached - fc['ankle'])
            put(zL - 0.02, fc['card'], Mft, tft, 'foot', s, shade, {'fs': fc['state']})
            put(zL - 0.01, sn, Msn, tsn, 'shin', s, shade)
            put(zL, th_, Mth, tth, 'thigh', s, shade)
            info['cards']['foot_' + s] = fc['card']['id']
            pts['hip_' + s] = Hp; pts['knee_' + s] = Kn; pts['ank_' + s] = reached
            card = fc['card']
            if card['faces'] != 0:
                hpt = apply(Mft, tft, card['pts']['heel']); tpt = apply(Mft, tft, card['pts']['toe'])
                pts['heel_' + s] = hpt; pts['toe_' + s] = tpt; pts['ball_' + s] = hpt + (tpt - hpt) * BALL_FRAC
            else:
                so = apply(Mft, tft, card['pts']['sole'])
                pts['heel_' + s] = so; pts['ball_' + s] = so; pts['toe_' + s] = so
            pts['sole_' + s] = apply(Mft, tft, card['pts']['sole'])

        # ---- torso group: seat / skirt / head / torso
        TZ = 4.0
        if not prof and bridge_op is not None:
            Mb, tb, bc = bridge_op
            put(1.5, bc, Mb, tb, 'bridge')
        if 'seat' in V or ('seat', None) in swap:
            sc = part('seat')
            if sc is not None and (not prof or ('seat', None) in swap and False):
                hm = (hip['L'] + hip['R']) / 2
                ks = (b.bridge + 0.35 * b.thigh) * k / max(1.0, sc['pts']['hem'][1] - sc['pts']['waist'][1])
                Ms, ts = card_matrix(sc['pts']['waist'], sc['pts']['hem'], waist, waist + unit(hm - waist) * 100, ks, axial=ks)
                put(TZ - 0.5 if view == 'back' else 1.6, sc, Ms, ts, 'seat')
        if 'skirt' in V:
            sk = V['skirt']
            kk = (b.bridge + 0.95 * b.thigh) * k / max(1.0, sk['pts']['hem'][1] - sk['pts']['waist'][1])
            kmid = (pts['knee_L'] + pts['knee_R']) / 2
            spread = abs(pts['knee_L'][0] - pts['knee_R'][0]) / (b.thigh * k)
            girth = kk * (0.62 if prof else 1.0) * (1 + 0.35 * min(1.0, spread))
            Mk, tk = card_matrix(sk['pts']['waist'], sk['pts']['hem'], waist, kmid, girth, axial=kk)
            put(TZ - 0.4, sk, Mk, tk, 'skirt')
        put(TZ, tc, Mt, tt, 'torso')
        if view == 'back':
            # from behind the head sits over the collar
            for z, op in ops:
                pass
        # depth adjustments: back view draws the head over the torso
        if view == 'back':
            ops = [((TZ + 0.3 if op['tag']['r'] in ('head', 'glasses', 'eyes', 'brows', 'mouth') else z), op) for z, op in ops]
        info['pts'] = {kk_: [round(float(v[0]), 1), round(float(v[1]), 1)] for kk_, v in pts.items() if isinstance(v, np.ndarray) and v.shape == (2,)}
        return ops, pts, info

    def _foot(self, s, fd, V, view, prof, f, k, W, part, from_set):
        b = self.body
        card = part('foot', s)
        p = fd.get('p', 0.0)
        state = 'flat'
        if prof and not from_set:
            if p < -14 and 'foot_heelup' in V: card = V['foot_heelup']; state = 'heelup'
            elif p > 14 and 'foot_toeup' in V: card = V['foot_toeup']; state = 'toeup'
        if card['faces'] == 0:
            kf = b.ank_up * k / max(1e-6, card['pts']['sole'][1] - card['pts']['ankle'][1])
            if 'ankle' in fd:
                A = fd['ankle']
                M, t = card_matrix(card['pts']['ankle'], card['pts']['sole'], A, A + np.array([0, 1.0]), kf, axial=kf)
            else:
                C = W(fd.get('x', 0.0), fd.get('y', 0.0))
                M, t = card_matrix(card['pts']['ankle'], card['pts']['sole'], np.zeros(2), np.array([0, 1.0]), kf, axial=kf)
                t = t + (C - apply(M, t, card['pts']['sole']))
            return {'card': card, 'M': M, 't': t, 'ankle': apply(M, t, card['pts']['ankle']), 'state': state}
        kf = b.foot * k / max(1e-6, np.linalg.norm(np.array(card['pts']['toe']) - np.array(card['pts']['heel'])))
        # the state cards are drawn already pitched: subtract their drawn pitch so `p` stays the world pitch
        hv = np.array(card['pts']['toe']) - np.array(card['pts']['heel'])
        drawn = math.degrees(math.atan2(-hv[1], abs(hv[0])))
        sdir = f if prof else (1.0 if s == 'L' else -1.0)
        pp = p - (drawn if state != 'flat' else 0.0)
        sv = np.array([sdir * math.cos(pp * DEG), -math.sin(pp * DEG)])
        mirror = (card['faces'] != sdir)
        M, t = card_matrix(card['pts']['heel'], card['pts']['toe'], np.zeros(2), sv * 100, kf, mirror=mirror, axial=kf)
        if 'ankle' in fd:
            t = t + (fd['ankle'] - apply(M, t, card['pts']['ankle']))
        else:
            C = W(fd.get('x', 0.0), fd.get('y', 0.0))
            c = fd.get('c', 'heel')
            hp = apply(M, t, card['pts']['heel']); tp = apply(M, t, card['pts']['toe'])
            cp = {'heel': hp, 'ball': hp + (tp - hp) * BALL_FRAC, 'toe': tp, 'sole': (hp + tp) / 2}[c]
            t = t + (C - cp)
        return {'card': card, 'M': M, 't': t, 'ankle': apply(M, t, card['pts']['ankle']), 'state': state}


# ------------------------------------------------------------------ keyframe tracks
def ease(u, kind='io'):
    u = min(1.0, max(0.0, u))
    if kind == 'l': return u
    if kind == 'i': return u * u
    if kind == 'o': return 1 - (1 - u) * (1 - u)
    if kind == 's': return 0.0
    return u * u * (3 - 2 * u)


def lerp(a, b, u):
    if isinstance(a, dict) and isinstance(b, dict):
        out = {}
        for kk in set(a) | set(b):
            if kk in a and kk in b: out[kk] = lerp(a[kk], b[kk], u)
            else: out[kk] = (a if kk in a else b)[kk] if (u < 0.5 or kk not in a) and kk in b else a.get(kk, b.get(kk))
        return out
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * u
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)) and len(a) == len(b) and all(isinstance(x, (int, float)) for x in a + b if not isinstance(x, (tuple, list))):
        return tuple(lerp(x, y, u) for x, y in zip(a, b))
    return a if u < 1.0 else b


class Track:
    """Per-channel keys: key(f, **channels) with optional ease=... ; value(f) interpolates each channel
       between its own neighbouring keys. Non-numeric channels (view, hand shapes, mouth) step."""

    def __init__(self):
        self.k = {}

    def key(self, f, ease_='io', **ch):
        for c, v in ch.items():
            self.k.setdefault(c, []).append((f, v, ease_))
            self.k[c].sort(key=lambda x: x[0])
        return self

    def value(self, f):
        out = {}
        for c, ks in self.k.items():
            if f <= ks[0][0]: out[c] = ks[0][1]; continue
            if f >= ks[-1][0]: out[c] = ks[-1][1]; continue
            for (f0, v0, _), (f1, v1, e1) in zip(ks, ks[1:]):
                if f0 <= f <= f1:
                    u = (f - f0) / max(1e-9, f1 - f0)
                    if isinstance(v0, (str, bool, set, frozenset)) or v0 is None or v1 is None or isinstance(v1, (str, bool, set, frozenset)):
                        out[c] = v0 if f < f1 else v1
                    else:
                        out[c] = lerp(v0, v1, ease(u, e1))
                    break
        return out
